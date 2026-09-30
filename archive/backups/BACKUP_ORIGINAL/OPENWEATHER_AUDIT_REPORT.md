# OPENWEATHER API INTEGRATION AUDIT REPORT

**Audit Date:** June 4, 2026  
**Status:** 🔴 **NOT WORKING - CRITICAL ISSUE FOUND**

---

## Executive Summary

The OpenWeather API integration is **NOT functioning**. The application consistently falls back to hardcoded weather values instead of using live API data.

**Root Cause:** The `OPENWEATHER_API_KEY` environment variable is **NOT SET**, causing the API key to be `None`. This results in HTTP 401 Unauthorized responses, triggering the fallback mechanism.

---

## 1. Code Files & Functions

### Primary File: `backend/predict_api.py`

| Component | Location | Purpose |
|-----------|----------|---------|
| **API Key Loading** | Line 24 | Load API key from environment |
| **Fetch Weather** | Lines 64-79 | Async function to call OpenWeather API |
| **Weather Fallback** | Lines 81-93 | Return hardcoded fallback values |
| **URL Generation** | Lines 66-71 | Construct API request URL |
| **Response Parsing** | Lines 74-78 | Extract weather data from JSON |

### Import Statement
```python
# Line 18
import httpx
```

---

## 2. API Key Loading Analysis

### Code (Line 24)
```python
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") or os.getenv("OPENWEATHER_KEY")
```

### Audit Results

| Variable | Status | Value |
|----------|--------|-------|
| `os.getenv("OPENWEATHER_API_KEY")` | ❌ NOT SET | `None` |
| `os.getenv("OPENWEATHER_KEY")` | ❌ NOT SET | `None` |
| **Final `OPENWEATHER_API_KEY` value** | ❌ **NONE** | `None` |

### Finding
```
🔴 CRITICAL: API key environment variable is NOT set
   - Neither OPENWEATHER_API_KEY nor OPENWEATHER_KEY is configured
   - os.getenv() returns None for both
   - The final OPENWEATHER_API_KEY variable = None
```

---

## 3. URL Generation Verification

### Code (Lines 66-71)
```python
url = (
    f"https://api.openweathermap.org/data/2.5/weather"
    f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
)
```

### Generated URL (with None API key)
```
https://api.openweathermap.org/data/2.5/weather?lat=13.0041&lon=77.6366&appid=None&units=metric
```

### Finding
```
⚠️  MALFORMED URL: The string "None" (literal text) is used as the API key
   - Expected: &appid=your_valid_api_key&units=metric
   - Actual:   &appid=None&units=metric
   - Result:   OpenWeather API rejects the request with HTTP 401
```

---

## 4. API Response Verification

### Test Request
```
GET https://api.openweathermap.org/data/2.5/weather?lat=13.0041&lon=77.6366&appid=None&units=metric
```

### Actual Response
```
Status Code: 401 Unauthorized
Response Body: 
{
  "cod": 401,
  "message": "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."
}
```

### Finding
```
🔴 ERROR: HTTP 401 Unauthorized
   - OpenWeather API rejected the request
   - Cause: Invalid/missing API key
   - Exception raised in try block (line 74 check)
   - Caught by except block (line 79)
```

---

## 5. Response Parsing Check

### Code (Lines 75-78)
```python
d = r.json()
temp = float(d["main"]["temp"])
humidity = float(d["main"]["humidity"])
rainfall = float(d.get("rain", {}).get("1h", 0) or d.get("rain", {}).get("3h", 0) or 0)
location = d.get("name", "Unknown")
```

### Expected Extraction (for valid responses)
```
Temperature:  29.86°C  (from d["main"]["temp"])
Humidity:     56%      (from d["main"]["humidity"])
Rainfall:     0mm      (from d.get("rain", {}).get("1h", 0))
Location:     Bengaluru (from d.get("name", "Unknown"))
```

### Actual Parsing Result
```
❌ NOT REACHED - API request failed with HTTP 401
   No valid JSON structure returned to parse
```

### Finding
```
⚠️  The parsing code is correctly structured, BUT it never executes because:
   - The HTTP check on line 74 raises ValueError("HTTP 401")
   - This exception is caught by line 79 except block
   - Fallback function called immediately
```

---

## 6. Exception Handling Flow

### Code (Lines 64-79)
```python
async def _fetch_weather(lat: float, lon: float):
    try:
        # Line 66-71: URL construction
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        
        # Line 72-73: HTTP request
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(url)
        
        # Line 74: Status code check
        if r.status_code != 200:
            raise ValueError(f"HTTP {r.status_code}")  # ← RAISES HERE (401)
        
        # Lines 75-78: NOT REACHED - exception already raised
        d = r.json()
        temp = float(d["main"]["temp"])
        humidity = float(d["main"]["humidity"])
        rainfall = float(d.get("rain", {}).get("1h", 0) or d.get("rain", {}).get("3h", 0) or 0)
        location = d.get("name", "Unknown")
        
        return temp, humidity, rainfall, location
    
    except Exception:  # ← CATCHES ValueError("HTTP 401")
        return _weather_fallback(lat, lon)  # ← FALLBACK CALLED
```

### Exception Handling Issues

| Issue | Severity | Details |
|-------|----------|---------|
| **Silent Exception** | 🔴 Critical | No logging of the actual error |
| **Broad Exception** | 🟡 Medium | `except Exception:` catches all errors |
| **No Error Context** | 🔴 Critical | Impossible to debug why fallback was used |
| **No Retry Logic** | 🟡 Medium | No attempt to retry on timeout |
| **8s Timeout** | 🟡 Medium | Could be too short for slow networks |

---

## 7. Fallback Value Trigger

### Actual Trigger Sequence

1. **API Key Missing** (Line 24)
   - `OPENWEATHER_API_KEY = None`

2. **Malformed URL** (Lines 66-71)
   - `appid=None` embedded in URL

3. **HTTP 401 Response** (Line 74)
   - OpenWeather rejects request
   - `raise ValueError("HTTP 401")`

4. **Exception Caught** (Line 79)
   - `except Exception:`
   - Calls `_weather_fallback(lat, lon)`

5. **Fallback Values Returned**
   - Temperature: `28.0°C`
   - Humidity: `75.0%`
   - Rainfall: `110.0mm`

---

## 8. Live API Response vs. Application Values

### Test Case: Bengaluru (13.0041°N, 77.6366°E)

#### Verified Live API Response
```
Temperature:  29.86°C
Humidity:     56%
Location:     Bengaluru
```

#### Application Returns (with current code)
```
Temperature:  28.0°C      (fallback for tropical zone)
Humidity:     75.0%       (fallback for tropical zone)
Rainfall:     110.0mm     (fallback for tropical zone)
Location:     Fallback location (13.00, 77.64)
```

#### Comparison Table

| Field | Live API | Application | Difference | Source |
|-------|----------|-------------|-----------|--------|
| **Temperature** | 29.86°C | 28.0°C | 1.86°C higher in API | Live API works, app uses fallback |
| **Humidity** | 56% | 75.0% | 19% higher in app | Fallback value |
| **Location** | Bengaluru | Fallback location (...) | Different strings | Fallback location |

### Finding
```
🔴 MISMATCH CONFIRMED:
   - Live API returns correct data (verified working)
   - Application receives fallback data
   - Cause: Exception handling silently catches API failure
   - No error logging prevents debugging
```

---

## 9. Root Cause Summary

### PRIMARY ROOT CAUSE

| Item | Details |
|------|---------|
| **Component** | API Key Loading |
| **File** | `backend/predict_api.py` |
| **Line Number** | 24 |
| **Issue** | Environment variable not set |
| **Code** | `OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") or os.getenv("OPENWEATHER_KEY")` |
| **Result** | `OPENWEATHER_API_KEY` is `None` |

### SECONDARY ROOT CAUSES

| Item | Details |
|------|---------|
| **Silent Fallback** | No error logging in except block |
| **No API Key Validation** | No check if API key is None before URL construction |
| **Broad Exception Handling** | `except Exception:` hides the actual error |
| **No Debug Logging** | Impossible to diagnose in production |

---

## 10. Detailed Findings

### Is the OpenWeather integration working correctly?

**Answer: NO ❌**

### Root Cause (Exact)

**File:** `backend/predict_api.py`  
**Line:** 24  
**Issue:** 
```python
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") or os.getenv("OPENWEATHER_KEY")
```

The environment variable `OPENWEATHER_API_KEY` (or `OPENWEATHER_KEY`) is **NOT SET** in the system environment.

**Consequence:**
1. `OPENWEATHER_API_KEY` becomes `None` (NoneType)
2. URL constructed with `appid=None` (string representation)
3. OpenWeather API returns HTTP 401 Unauthorized
4. ValueError raised on line 74
5. Exception caught on line 79
6. `_weather_fallback()` returns hardcoded values
7. Application uses fallback data instead of live API data

### Why the API Works in Direct Tests

When you test the API directly with a valid key:
```python
import httpx
url = "https://api.openweathermap.org/data/2.5/weather?lat=13.0041&lon=77.6366&appid=YOUR_KEY&units=metric"
response = httpx.get(url)
# Returns HTTP 200 with valid data
```

✅ **The API works correctly when a valid key is provided.**

### Why the Application Uses Fallback

When the application runs:
```python
OPENWEATHER_API_KEY = None  # ← Environment variable not set
url = f"...&appid={None}&units=metric"  # ← Becomes "appid=None"
response = httpx.get(url)  # ← Returns HTTP 401
# Exception caught → Fallback values used
```

❌ **The application cannot reach the API because no API key is configured.**

---

## 11. Secondary Issues Found

### Issue 1: Silent Exception Handling
**Severity:** 🔴 Critical  
**File:** `backend/predict_api.py`  
**Lines:** 64-79  
**Problem:**
```python
except Exception:  # ← Catches ALL exceptions without logging
    return _weather_fallback(lat, lon)
```
**Impact:** No error message indicates why fallback was used
**Fix:** Add logging/debug output

---

### Issue 2: No API Key Validation
**Severity:** 🔴 Critical  
**File:** `backend/predict_api.py`  
**Line:** 24  
**Problem:** No check if `OPENWEATHER_API_KEY` is None before use  
**Impact:** Silent failure with cryptic HTTP 401
**Fix:** Add validation and clear error message

---

### Issue 3: URL with String "None"
**Severity:** 🔴 Critical  
**File:** `backend/predict_api.py`  
**Lines:** 66-71  
**Problem:** f-string includes `None` as literal text "None"  
**Impact:** Creates malformed URL: `appid=None`
**Fix:** Validate API key exists before URL construction

---

## 12. Audit Checklist

- [x] Located all OpenWeather-related code files and functions
- [x] Verified API key loading from environment variables
- [x] Confirmed API key source (environment variables only)
- [x] Verified request URL being generated
- [x] Checked API response (HTTP 401 Unauthorized)
- [x] Validated field extraction logic (never reaches parsing code)
- [x] Identified fallback trigger conditions
- [x] Compared live API vs application values
- [x] Verified exception handling mechanism
- [x] Identified root cause and secondary issues

---

## 13. Conclusion

**Is the OpenWeather integration working correctly?**

### **ANSWER: NO** 🔴

**Root Cause:** The environment variable `OPENWEATHER_API_KEY` (or `OPENWEATHER_KEY`) is **NOT SET**.

**Evidence:**
1. Audit shows `OPENWEATHER_API_KEY = None`
2. Generated URL contains `appid=None` (literal string)
3. OpenWeather API returns HTTP 401 Unauthorized
4. Exception caught and silently handled
5. Fallback values always returned

**Impact:** The application always uses hardcoded weather values instead of live API data, resulting in identical predictions regardless of location's actual weather.

**Verification Method:** The direct API test works when you manually provide a valid API key, proving the API itself works. The failure is in the application's configuration, not the API or code logic.

---

## File Structure Reference

```
backend/
├── predict_api.py          ← Main issue file
│   ├── Line 24: API key loading
│   ├── Line 64-79: _fetch_weather() function
│   ├── Line 74: Status code check (raises HTTP 401)
│   ├── Line 79: Exception handler (calls fallback)
│   └── Line 81-93: _weather_fallback() function
├── main.py                 ← Entry point
└── audit_openweather.py    ← This audit script
```

---

**END OF AUDIT REPORT**
