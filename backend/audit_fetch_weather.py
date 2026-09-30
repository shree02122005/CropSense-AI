"""
audit_fetch_weather.py
────────────────────────
Test _fetch_weather() function with debug logging
"""
import os
import sys
import asyncio

# Add paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from backend.predict_api import _fetch_weather

# Test locations
locations = [
    ("Mahadevpura, Bengaluru", 13.0041, 77.6366),
    ("Bellandur, Bengaluru", 12.9352, 77.6245),
]

async def test_locations():
    print("="*80)
    print("_fetch_weather() AUDIT")
    print("="*80)
    
    all_results = []
    
    for name, lat, lon in locations:
        print(f"\n{'='*80}")
        print(f"TEST: {name}")
        print(f"Coordinates: {lat}°N, {lon}°E")
        print(f"{'='*80}")
        
        temp, humidity, rainfall, location = await _fetch_weather(lat, lon)
        
        print(f"\n[SUMMARY] {name}")
        print(f"  Temperature: {temp}°C")
        print(f"  Humidity: {humidity}%")
        print(f"  Rainfall: {rainfall}mm")
        print(f"  Location: {location}")
        
        all_results.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "temp": temp,
            "humidity": humidity,
            "rainfall": rainfall,
            "location": location,
        })
    
    # Comparison
    print(f"\n{'='*80}")
    print("COMPARISON OF RESULTS")
    print(f"{'='*80}")
    
    if len(all_results) >= 2:
        r1, r2 = all_results[0], all_results[1]
        
        print(f"\nLocation 1: {r1['name']}")
        print(f"  Temp: {r1['temp']}°C, Humidity: {r1['humidity']}%, Rainfall: {r1['rainfall']}mm")
        
        print(f"\nLocation 2: {r2['name']}")
        print(f"  Temp: {r2['temp']}°C, Humidity: {r2['humidity']}%, Rainfall: {r2['rainfall']}mm")
        
        print(f"\nDifferences:")
        temp_diff = abs(r1['temp'] - r2['temp'])
        humidity_diff = abs(r1['humidity'] - r2['humidity'])
        rainfall_diff = abs(r1['rainfall'] - r2['rainfall'])
        
        print(f"  Temperature difference: {temp_diff}°C")
        print(f"  Humidity difference: {humidity_diff}%")
        print(f"  Rainfall difference: {rainfall_diff}mm")
        
        if temp_diff == 0 and humidity_diff == 0 and rainfall_diff == 0:
            print(f"\n  🔴 IDENTICAL VALUES - Fallback values being used")
        else:
            print(f"\n  ✓ DIFFERENT VALUES - Live API data being used")

# Run async function
asyncio.run(test_locations())
