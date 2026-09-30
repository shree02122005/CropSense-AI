# OPENWEATHER API INTEGRATION - TECHNICAL REFERENCE

## API Configuration Reference

### Environment Variables Required

```bash

# PRIMARY (preferred)

OPENWEATHER_API_KEY=your_32_character_api_key

# SECONDARY (fallback if primary not set)

OPENWEATHER_KEY=your_32_character_api_key

```

**How it works in code:**

```python

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") or os.getenv("OPENWEATHER_KEY")

# Returns first non-None value, or None if both missing

```

### Current Status

```

Environment Variable Status:

  OPENWEATHER_API_KEY: ❌ NOT SET (None)

  OPENWEATHER_KEY:     ❌ NOT SET (None)

  Final Value:         ❌ None

API Integration Status: ❌ NOT WORKING

  Reason: Invalid/missing API key

  HTTP Response: 401 Unauthorized

  Fallback Used: YES

  Result: Hardcoded values returned

```

---

## API Request Flow

### Normal Flow (With Valid API Key)

```

1. User submits image + coordinates

2. backend/predict_api.py:predict_crop() called

3. CNN classifies soil type

4. _fetch_weather(lat, lon) called

   → URL: https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid=YOUR_OPENWEATHER_API_KEY&units=metric

   → HTTP GET request sent

   → Response: HTTP 200 with weather JSON

   → Parse: {"main": {"temp": 29.86, "humidity": 56, ...}}

   → Return: (29.86, 56, 0, "Bengaluru")

5. _fetch_soil(lat, lon) called

   → Gets soil properties from SoilGrids API

6. Feature vector created: [N, P, K, temp, humidity, ph, rainfall, soil_encoded]

7. ML model predicts crops

```

### Current Broken Flow (Missing API Key)

```

1. User submits image + coordinates

2. backend/predict_api.py:predict_crop() called

3. CNN classifies soil type

4. _fetch_weather(lat, lon) called

   → URL: https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid=None&units=metric

   → HTTP GET request sent

   → Response: HTTP 401 Unauthorized (Invalid API key)

   → EXCEPTION RAISED: ValueError("HTTP 401")

   → Exception caught: except Exception:

   → Fallback called: _weather_fallback(lat, lon)

   → Return: (28.0, 75.0, 110.0, "Fallback location...")

5. _fetch_soil(lat, lon) called (same issue if key missing)

   → Returns fallback soil values

6. Feature vector: [90, 40, 40, 28.0, 75.0, 5.8, 110.0, 2]

7. ML model predicts crops (same as all tropical locations)

```

---

## Code Analysis by Line

### File: `backend/predict_api.py`

#### Line 24: API Key Loading

```python

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") or os.getenv("OPENWEATHER_KEY")

```

- **Status:** ❌ Loads None

- **Issue:** Environment variables not set

- **Expected:** Should be a 32-character alphanumeric string

- **Actual:** None

#### Lines 66-71: URL Construction

```python

url = (

    f"https://api.openweathermap.org/data/2.5/weather"

    f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"

)

```

- **Status:** ❌ Generates malformed URL

- **Issue:** API key is None

- **Expected URL:** `https://api.openweathermap.org/data/2.5/weather?lat=13.0041&lon=77.6366&appid=YOUR_OPENWEATHER_API_KEY&units=metric`

- **Actual URL:** `https://api.openweathermap.org/data/2.5/weather?lat=13.0041&lon=77.6366&appid=None&units=metric`

#### Lines 72-73: HTTP Request

```python

async with httpx.AsyncClient(timeout=8) as client:

    r = await client.get(url)

```

- **Status:** ⚠️  Executes but receives error

- **Issue:** Requests malformed URL

- **Timeout:** 8 seconds (reasonable)

- **Result:** HTTP 401 response

#### Line 74: Status Code Check

```python

if r.status_code != 200:

    raise ValueError(f"HTTP {r.status_code}")

```

- **Status:** ✓ Working as designed

- **Issue:** Raises exception (HTTP 401)

- **Exception Type:** ValueError

- **Message:** "HTTP 401"

#### Lines 75-78: Response Parsing

```python

d = r.json()

temp = float(d["main"]["temp"])

humidity = float(d["main"]["humidity"])

rainfall = float(d.get("rain", {}).get("1h", 0) or d.get("rain", {}).get("3h", 0) or 0)

location = d.get("name", "Unknown")

```

- **Status:** ⚠️  Never executed

- **Issue:** Exception raised before reaching this code

- **Would work:** If HTTP 200 received

- **Never returns:** Fallback triggered first

#### Line 79: Exception Handling

```python

except Exception:

    return _weather_fallback(lat, lon)

```

- **Status:** ❌ Problem here

- **Issue:** Silently catches ValueError("HTTP 401")

- **Problem:** No logging of error

- **Result:** Returns hardcoded values

#### Lines 81-93: Fallback Function

```python

def _weather_fallback(lat: float, lon: float):

    if abs(lat) <= 23:

        temp = 28.0 if lat >= 0 else 24.0

        humidity = 75.0

        rainfall = 110.0

    elif abs(lat) <= 35:

        temp = 24.0

        humidity = 65.0

        rainfall = 70.0

    # ... more zones ...

```

- **Status:** ✓ Working as designed

- **Issue:** Used when it shouldn't be

- **Behavior:** Returns same values for all locations in same latitude band

- **Result:** Identical predictions for nearby cities

---

## Test Results

### Audit Execution: `python backend/audit_openweather.py`

#### Section 1: API Key Loading

```

Environment Variables:

  OPENWEATHER_API_KEY: None ✗

  OPENWEATHER_KEY:     None ✗

Final Value: None ✗

```

#### Section 2: URL Generation

```

Generated URL:

https://api.openweathermap.org/data/2.5/weather?lat=13.0041&lon=77.6366&appid=None&units=metric

                                                                                   ^^^ MALFORMED

```

#### Section 3: API Request

```

HTTP Status: 401 Unauthorized ✗

Response:

{

  "cod": 401,

  "message": "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."

}

```

#### Section 5: Fallback Trigger

```

Reason: API key is None → URL will have 'appid=None' → HTTP 401 error ✗

```

---

## Expected Values Comparison

### Test Location: Bengaluru (13.0041°N, 77.6366°E)

#### From OpenWeather API (when working)

```json

{

  "main": {

    "temp": 29.86,

    "feels_like": 32.5,

    "humidity": 56

  },

  "rain": {

    "1h": 0

  },

  "name": "Bengaluru"

}

```

**Extracted Values:**

- Temperature: 29.86°C

- Humidity: 56%

- Rainfall: 0mm

- Location: Bengaluru

#### From Fallback (current)

```python

# abs(13.0041) <= 23, so:

temp = 28.0

humidity = 75.0

rainfall = 110.0

location = "Fallback location (13.00, 77.64)"

```

**Extracted Values:**

- Temperature: 28.0°C (differs by 1.86°C)

- Humidity: 75.0% (differs by 19%)

- Rainfall: 110.0mm (differs by 110mm!)

- Location: Fallback location... (clearly wrong)

---

## Debugging Steps

### 1. Check Current API Key

```python

import os

key = os.getenv("OPENWEATHER_API_KEY") or os.getenv("OPENWEATHER_KEY")

print(f"API Key: {key}")  # Should print key, not None

```

### 2. Check Environment Variables (PowerShell)

```powershell

Get-ChildItem env: | Where-Object {$_.Name -like "*WEATHER*"}

# or

$env:OPENWEATHER_API_KEY

```

### 3. Test URL Manually

```python

import httpx

url = "https://api.openweathermap.org/data/2.5/weather?lat=13.0041&lon=77.6366&appid=YOUR_KEY&units=metric"

response = httpx.get(url, timeout=8)

print(response.status_code)  # Should be 200

print(response.json())

```

### 4. Run Full Audit

```bash

python backend/audit_openweather.py

```

---

## Solution Implementation

### Step 1: Get API Key

- Go to https://openweathermap.org/api

- Create free account

- Generate API key (usually 32 characters)

### Step 2: Set Environment Variable

**PowerShell (recommended for testing):**

```powershell

$env:OPENWEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY"

```

**Command Prompt:**

```cmd

set OPENWEATHER_API_KEY=YOUR_OPENWEATHER_API_KEY

**Permanent (Windows):**

1. Open "Environment Variables" settings

2. Click "New" under User variables

3. Variable name: `OPENWEATHER_API_KEY`

4. Variable value: `your_api_key_here`

5. Click OK

6. Restart terminal/IDE

### Step 3: Verify in Code

```python

# backend/predict_api.py, line 24

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") or os.getenv("OPENWEATHER_KEY")

# Add after (for debugging only):

if OPENWEATHER_API_KEY is None:

    print("WARNING: OPENWEATHER_API_KEY not set!")

else:

    print(f"✓ API key loaded: {OPENWEATHER_API_KEY[:10]}...")

```

### Step 4: Test

```bash

python backend/audit_openweather.py

```

Should show:

```

✓ API key found: a1b2c3d...

✓ HTTP Status Code: 200

✓ JSON parsed successfully

✓ Temperature: 29.86°C

✓ Humidity: 56%

```

---

## Troubleshooting

### Problem: Still getting 401 error after setting variable

**Possible causes:**

1. Variable set in wrong terminal/IDE

2. IDE needs restart to pick up environment changes

3. Variable name misspelled (exact case-sensitivity not an issue but typos are)

4. API key invalid or expired

**Solution:**

- Verify key from https://openweathermap.org/account/api_keys

- Restart IDE completely

- Check with: `Get-ChildItem env: | grep WEATHER` (PowerShell)

### Problem: Getting different error (not 401)

**If 403 (Forbidden):**

- Key exists but not authorized for this endpoint

- Contact OpenWeather support

**If 429 (Too Many Requests):**

- Exceeded free tier limits

- Wait for rate limit reset or upgrade plan

**If timeout:**

- Network connectivity issue

- Try with longer timeout value

---

## OpenWeather API Reference

### Endpoint

```

https://api.openweathermap.org/data/2.5/weather

```

### Required Parameters

```

lat     - Latitude (-90 to 90)

lon     - Longitude (-180 to 180)

appid   - API key (your unique key)

units   - metric (for Celsius/percentage/mm)

```

### Response Fields Used

```json

{

  "main": {

    "temp": 29.86,          // Temperature in Celsius

    "humidity": 56          // Humidity percentage

  },

  "rain": {

    "1h": 0,                // Rainfall in last hour (mm)

    "3h": 0                 // Rainfall in last 3 hours (mm)

  },

  "name": "Bengaluru"       // City name

}

```

### API Documentation

- https://openweathermap.org/weather-conditions

- https://openweathermap.org/current

- Free tier: 60 calls/minute, 1000 calls/day

---

## Integration Points

### Files that depend on OpenWeather data

1. `backend/predict_api.py` - Calls API

2. `backend/main.py` - Passes coordinates to predict

3. Frontend - Shows temperature/humidity in results

### How it affects predictions

```

Weather Data → Feature Vector → ML Model → Crop Predictions

Good weather:   [N, P, K, 25°C, 60%, pH, rainfall, soil] → [Rice, Corn, Wheat]

Bad weather:    [N, P, K, 40°C, 20%, pH, rainfall, soil] → [Cotton, Sugarcane, Jowar]

Fallback (wrong):[N, P, K, 28°C, 75%, pH, rainfall, soil] → Always same crops

```

---

## Success Metrics

After fixing the API key issue:

| Metric | Before | After |

|--------|--------|-------|

| API Status | ❌ 401 errors | ✓ 200 OK |

| Temperature varies | ❌ Always 28°C | ✓ Varies (25-35°C) |

| Humidity varies | ❌ Always 75% | ✓ Varies (20-80%) |

| Location accuracy | ❌ Generic "Fallback location" | ✓ Actual city name |

| Prediction diversity | ❌ Identical for nearby cities | ✓ Different recommendations |

---

**Created:** June 4, 2026  

**Status:** Root cause identified and documented  

**Next Action:** Set OPENWEATHER_API_KEY environment variable and restart backend