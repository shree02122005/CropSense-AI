"""
Audit script to test predictions for different locations
Test locations:
  - Mahadevpura, Bengaluru: 13.0041°N, 77.6366°E
  - Bellandur, Bengaluru: 12.9352°N, 77.6245°E
"""
import asyncio
import sys
import os

# Add paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from backend.predict_api import (
    _fetch_weather, 
    _fetch_soil,
    _soil_type_to_encoded,
    _predict_crops,
    _tropical_weighting
)
import numpy as np

async def audit_location(name: str, latitude: float, longitude: float):
    """Audit prediction pipeline for a specific location"""
    print(f"\n{'='*70}")
    print(f"AUDITING: {name}")
    print(f"Coordinates: {latitude:.4f}°N, {longitude:.4f}°E")
    print(f"{'='*70}")
    
    # Fetch weather
    print(f"\n[1] WEATHER FETCH")
    print(f"    Calling _fetch_weather({latitude}, {longitude})")
    temp, humidity, rainfall, location = await _fetch_weather(latitude, longitude)
    print(f"    ✓ Temperature:  {temp}°C")
    print(f"    ✓ Humidity:     {humidity}%")
    print(f"    ✓ Rainfall:     {rainfall}mm")
    print(f"    ✓ Location:     {location}")
    
    # Check if fallback (location name contains "Fallback")
    if "Fallback" in location:
        print(f"    ⚠ USING FALLBACK VALUES (API failed)")
    
    # Fetch soil
    print(f"\n[2] SOIL FETCH")
    print(f"    Calling _fetch_soil({latitude}, {longitude})")
    ph, organic_carbon = await _fetch_soil(latitude, longitude)
    print(f"    ✓ pH:               {ph}")
    print(f"    ✓ Organic Carbon:   {organic_carbon}%")
    
    # Check if fallback
    print(f"    (Fallback for tropical zone (abs(lat) <= 23): pH=5.8, SOC=2.5)")
    if ph == 5.8 and organic_carbon == 2.5:
        print(f"    ⚠ USING FALLBACK VALUES (API failed or no valid data)")
    
    # Mock soil type for testing (using "loamy" as default)
    soil_type = "loamy"
    soil_type_encoded = _soil_type_to_encoded(soil_type)
    print(f"\n[3] SOIL TYPE")
    print(f"    Soil Type:          {soil_type}")
    print(f"    Soil Type Encoded:  {soil_type_encoded}")
    
    # Feature vector
    print(f"\n[4] FEATURE VECTOR FOR ML MODEL")
    N, P, K = 90, 40, 40
    print(f"    NPK (fixed):        N={N}, P={P}, K={K}")
    feature_vector = [N, P, K, temp, humidity, ph, rainfall, soil_type_encoded]
    print(f"    FEATURE VECTOR:     {feature_vector}")
    print(f"                        [N, P, K, temp, humidity, ph, rainfall, soil_encoded]")
    
    # Get regional weights
    print(f"\n[5] REGIONAL WEIGHTING")
    weights = _tropical_weighting(latitude, longitude, humidity, temp)
    print(f"    Weights dict:       {weights}")
    
    # Predict crops (need to mock the model prediction)
    print(f"\n[6] ML PREDICTION")
    print(f"    [Note: Actual crop probabilities require loaded ML model]")
    print(f"    Feature vector being sent to ML model: {feature_vector}")
    
    return {
        "name": name,
        "latitude": latitude,
        "longitude": longitude,
        "temperature": temp,
        "humidity": humidity,
        "rainfall": rainfall,
        "location": location,
        "ph": ph,
        "organic_carbon": organic_carbon,
        "feature_vector": feature_vector,
        "weights": weights,
    }


async def main():
    print("\n" + "="*70)
    print("CROPSENSE AI - PREDICTION AUDIT")
    print("Investigating why predictions remain identical after location change")
    print("="*70)
    
    # Test locations
    locations = [
        ("Mahadevpura, Bengaluru", 13.0041, 77.6366),
        ("Bellandur, Bengaluru", 12.9352, 77.6245),
    ]
    
    results = []
    for name, lat, lon in locations:
        result = await audit_location(name, lat, lon)
        results.append(result)
    
    # Compare results
    print("\n" + "="*70)
    print("COMPARISON")
    print("="*70)
    
    print("\nWeather Comparison:")
    print(f"  Location 1 (Mahadevpura):")
    print(f"    Temperature:  {results[0]['temperature']}°C")
    print(f"    Humidity:     {results[0]['humidity']}%")
    print(f"    Rainfall:     {results[0]['rainfall']}mm")
    print(f"  Location 2 (Bellandur):")
    print(f"    Temperature:  {results[1]['temperature']}°C")
    print(f"    Humidity:     {results[1]['humidity']}%")
    print(f"    Rainfall:     {results[1]['rainfall']}mm")
    print(f"  Weather identical? {results[0]['temperature'] == results[1]['temperature']}")
    
    print("\nSoil Comparison:")
    print(f"  Location 1 (Mahadevpura):")
    print(f"    pH:             {results[0]['ph']}")
    print(f"    Organic Carbon: {results[0]['organic_carbon']}%")
    print(f"  Location 2 (Bellandur):")
    print(f"    pH:             {results[1]['ph']}")
    print(f"    Organic Carbon: {results[1]['organic_carbon']}%")
    print(f"  Soil identical? {results[0]['ph'] == results[1]['ph']}")
    
    print("\nFeature Vectors:")
    print(f"  Location 1: {results[0]['feature_vector']}")
    print(f"  Location 2: {results[1]['feature_vector']}")
    print(f"  Vectors identical? {results[0]['feature_vector'] == results[1]['feature_vector']}")
    
    # Analysis
    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)
    
    if results[0]['feature_vector'] == results[1]['feature_vector']:
        print("\n🔴 ISSUE CONFIRMED: Feature vectors are identical!")
        print("\nROOT CAUSE:")
        
        if results[0]['location'] and "Fallback" in results[0]['location']:
            print("  ✓ Both locations are using FALLBACK values (API calls failed)")
            print(f"  ✓ Fallback function uses only LATITUDE, not longitude")
            print(f"  ✓ Both locations have latitude in same band (abs(lat) <= 23)")
            print(f"  ✓ Therefore: Same fallback values → Same predictions")
        else:
            print("  ? APIs succeeded but weather/soil data is identical")
            print("  ? This could indicate:")
            print("    - SoilGrids API returning same data for nearby locations")
            print("    - OpenWeather API grid resolution issues")
    else:
        print("\n✅ Feature vectors differ between locations")
        print("   Predictions should differ (if not, check crop model logic)")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(main())
