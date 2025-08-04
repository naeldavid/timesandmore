from flask import Flask, render_template
from datetime import datetime
import requests
import json
from hijri_converter import convert
import ephem 
import math

app = Flask(__name__)
now = datetime.now()
today = now.strftime("%Y%m%d%H%M")

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        return response.json()['ip']
    except Exception as e:
        return str(e)

def get_prayer_times(latitude, longitude, city, country, timezone):
    try:
        url = f"http://api.aladhan.com/v1/timings/{today}?latitude={latitude}&longitude={longitude}&timezone={timezone}&method=4"
        response = requests.get(url)
        data = response.json()
        
        if data['status'] == 'OK':
            return data['data']['timings']
    except Exception as e:
        return str(e)

def calculate_moon_phase():
    moon = ephem.Moon()
    moon.compute()
    
    # Get the illumination percentage (0-100)
    illumination = round(moon.phase)
    
    # Get the moon's age in days
    previous_new_moon = ephem.previous_new_moon(now)
    next_new_moon = ephem.next_new_moon(now)
    moon_age = (now - previous_new_moon.datetime()) / (next_new_moon.datetime() - previous_new_moon.datetime())
    moon_age = float(moon_age) * 29.530588853  # Synodic month length
    
    # Determine the phase more accurately
    if moon_age < 1.84566:
        phase = "New Moon"
    elif moon_age < 5.53699:
        phase = "Waxing Crescent"
    elif moon_age < 9.22831:
        phase = "First Quarter"
    elif moon_age < 12.91963:
        phase = "Waxing Gibbous"
    elif moon_age < 16.61096:
        phase = "Full Moon"
    elif moon_age < 20.30228:
        phase = "Waning Gibbous"
    elif moon_age < 23.99361:
        phase = "Last Quarter"
    elif moon_age < 27.68493:
        phase = "Waning Crescent"
    else:
        phase = "New Moon"
    
    return phase, illumination

def calculate_qibla(latitude, longitude):
    """Calculate Qibla direction from given coordinates"""
    # Coordinates of Kaaba
    kaaba_lat = math.radians(21.4225)
    kaaba_long = math.radians(39.8262)
    
    # Convert to radians
    lat = math.radians(latitude)
    long = math.radians(longitude)
    
    # Calculate Qibla direction
    y = math.sin(kaaba_long - long)
    x = (math.cos(lat) * math.tan(kaaba_lat)) - (math.sin(lat) * math.cos(kaaba_long - long))
    qibla = math.degrees(math.atan2(y, x))
    
    # Normalize to 0-360
    qibla = (qibla + 360) % 360
    
    return round(qibla, 2)

@app.route('/')
def index():
    ip = get_public_ip()
    response = requests.get('http://ipwho.is/' + ip)
    ipwhois = response.json()

    country = ipwhois['country']
    city = ipwhois['city']
    longitude = ipwhois['longitude']
    latitude = ipwhois['latitude']
    timezone = ipwhois['timezone']['abbr']

    prayer_times = get_prayer_times(latitude, longitude, city, country, timezone)
    
    now = datetime.now()
    hijri = convert.Gregorian(now.year, now.month, now.day).to_hijri()
    hijri_date = f"{hijri.day} {hijri.month_name()} {hijri.year} AH"
    gregorian_date = now.strftime('%b %d, %Y')
    

    current_phase, illumination = calculate_moon_phase()
    
    # Add Qibla calculation
    qibla_direction = calculate_qibla(latitude, longitude)
    
    return render_template('index.html', 
                         city=city,
                         country=country,
                         timezone=timezone,
                         prayer_times=prayer_times,
                         hijri_date=hijri_date,
                         gregorian_date=gregorian_date,
                         current_phase=current_phase,
                         illumination=illumination,
                         qibla_direction=qibla_direction)