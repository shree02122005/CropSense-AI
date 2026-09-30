# OPENWEATHER API INTEGRATION - ROOT CAUSE & SOLUTION

## Problem Statement

**Identical predictions across all locations** → Investigation traced to **OpenWeather API always returning fallback values** instead of live weather data.

---

## Root Cause (ONE SENTENCE)

**The `OPENWEATHER_API_KEY` environment variable is NOT SET**, so the API key is `None`, causing HTTP 401 errors and silent fallback to hardcoded values.

---

## Evidence Trail

### Step 1: API Key Loading
```python
# backend/predict_api.py, Line 24
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") or os.getenv("OPENWEATHER_KEY")

# Audit Result:
# ❌ OPENWEATHER_API_KEY: None
# ❌ OPENWEATHER_KEY: None
# ❌ Final value: None
```

### Step 2: URL Generation
```python
# backend/predict_api.py, Lines 66-71
url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"

# Generated URL:
# https://api.openweathermap.org/data/2.5/weather?lat=13.0041&lon=77.6366&appid=None&units=metric
#                                                                                      ^^^^ Wrong!
```

### Step 3: API Response
```python
# API rejects invalid key:
Status: 401 Unauthorized
Response:
{
  "cod": 401,
  "message": "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."
}
```

### Step 4: Exception Handling
```python
# backend/predict_api.py, Lines 74-79
if r.status_code != 200:
    raise ValueError(f"HTTP {r.status_code}")  # ← Raises here

except Exception:  # ← Catches the exception
    return _weather_fallback(lat, lon)  # ← Returns hardcoded values
```

### Step 5: Fallback Values Used
```python
# For any latitude in tropical zone (abs(lat) <= 23):
temp = 28.0°C
humidity = 75.0%
rainfall = 110.0mm
location = "Fallback location (...)"
```

---

## Why Direct API Calls Work

When you manually test with a valid key:
```bash
curl "https://api.openweathermap.org/data/2.5/weather?lat=13.0041&lon=77.6366&appid=YOUR_VALID_KEY&units=metric"

# Response:
{
  "main": {
    "temp": 29.86,
    "humidity": 56,
    ...
  },
  "name": "Bengaluru"
}
```

✅ **The API works fine when a valid key is provided.**

---

## Why the Application Fails

```
Environment Variable NOT SET
         ↓
OPENWEATHER_API_KEY = None
         ↓
URL has appid=None (string "None")
         ↓
OpenWeather rejects with HTTP 401
         ↓
Exception raised
         ↓
Exception caught silently
         ↓
Fallback values returned
         ↓
Identical predictions across locations
```

---

## Proof: Audit Script Results

```
[1] API KEY LOADING
  OPENWEATHER_API_KEY: None  ← NOT SET
  OPENWEATHER_KEY:     None  ← NOT SET
  Final Value Used: None     ← PROBLEM HERE

[3] API REQUEST TEST
  Generated URL: ...&appid=None&units=metric
  HTTP Status: 401 Unauthorized
  Error: "Invalid API key"

[5] FALLBACK TRIGGER ANALYSIS
  Fallback Reason: API key is None → URL will have 'appid=None' → HTTP 401 error

[7] EXCEPTION HANDLING
  ⚠️ ANY exception will trigger fallback without logging!
```

---

## Solution

### 1. Get an OpenWeather API Key

Go to: https://openweathermap.org/api
- Sign up for free (limited requests allowed)
- Generate an API key from account settings
- You'll receive a key like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

### 2. Set Environment Variable (BEFORE starting backend)

**Option A: Windows PowerShell**
```powershell
$env:OPENWEATHER_API_KEY = "your_api_key_here"
cd C:\Users\priya\Downloads\cropsense-ai\crop-full
python backend\main.py
```

**Option B: Windows Command Prompt**
```cmd
set OPENWEATHER_API_KEY=your_api_key_here
cd C:\Users\priya\Downloads\cropsense-ai\crop-full
python backend\main.py
```

**Option C: Create .env file (if using python-dotenv)**
```
# .env file in backend/ directory
OPENWEATHER_API_KEY=your_api_key_here
```

**Option D: Modify code (NOT recommended - for testing only)**
```python
# backend/predict_api.py, Line 24
# OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") or os.getenv("OPENWEATHER_KEY")
OPENWEATHER_API_KEY = "your_api_key_here"  # HARD-CODED (NOT for production!)
```

### 3. Verify the Fix

Run the audit script again:
```bash
python backend\audit_openweather.py
```

Expected output after setting API key:
```
[1] API KEY LOADING
  ✓ API key found: a1b2c3d...

[3] API REQUEST TEST
  ✓ HTTP Status Code: 200
  ✓ Response received

[4] RESPONSE PARSING
  ✓ Temperature: 29.86°C
  ✓ Humidity: 56%
  ✓ Location: Bengaluru

[DIAGNOSIS & ROOT CAUSE]
✅ OPENWEATHER API IS WORKING CORRECTLY
```

### 4. Restart Backend

After setting the environment variable, restart the FastAPI backend:
```bash
python backend\main.py
```

---

## Expected Results After Fix

### Before (with missing API key)
```
Location: Bengaluru (13.0041°N)
Temperature: 28.0°C (fallback)
Humidity: 75.0% (fallback)
Rainfall: 110.0mm (fallback)
Crops: [Rice, Wheat, Corn]

Location: Hyderabad (17.3850°N)
Temperature: 28.0°C (fallback - same!)
Humidity: 75.0% (fallback - same!)
Rainfall: 110.0mm (fallback - same!)
Crops: [Rice, Wheat, Corn] ← IDENTICAL!
```

### After (with valid API key)
```
Location: Bengaluru (13.0041°N)
Temperature: 29.86°C (live API)
Humidity: 56% (live API)
Rainfall: 2mm (live API)
Crops: [Rice, Corn, Sugarcane]

Location: Hyderabad (17.3850°N)
Temperature: 33.5°C (live API)
Humidity: 45% (live API)
Rainfall: 0mm (live API)
Crops: [Cotton, Sugarcane, Groundnut] ← DIFFERENT!
```

---

## Files Involved

| File | Lines | Issue |
|------|-------|-------|
| `backend/predict_api.py` | 24 | API key loading |
| `backend/predict_api.py` | 64-79 | _fetch_weather() function |
| `backend/predict_api.py` | 74 | HTTP status check |
| `backend/predict_api.py` | 79 | Silent exception handling |
| `backend/audit_openweather.py` | N/A | Audit script (created) |

---

## Summary

| Item | Status | Details |
|------|--------|---------|
| **Is the API working?** | ❌ NO | API key not configured |
| **Root cause** | Missing API key | Environment variable not set |
| **Current behavior** | Fallback values | Always returns hardcoded data |
| **Identical predictions** | YES | Because all locations use same fallback values |
| **Solution** | Simple | Set OPENWEATHER_API_KEY environment variable |
| **Time to fix** | 2 minutes | Get API key + set environment variable |

---

## Quick Fix Summary

```bash
# 1. Get API key from https://openweathermap.org/api (free account)
# 2. Set environment variable:
$env:OPENWEATHER_API_KEY = "YOUR_API_KEY_HERE"

# 3. Restart backend:
python backend\main.py

# 4. Test:
python backend\audit_openweather.py
```

✅ **Done!** Predictions will now vary by location with live weather data.

---

**Full Audit Report:** See [OPENWEATHER_AUDIT_REPORT.md](OPENWEATHER_AUDIT_REPORT.md)
