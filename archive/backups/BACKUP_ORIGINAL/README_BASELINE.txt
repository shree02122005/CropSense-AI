================================================================================
CROPSENSE AI — ORIGINAL BASELINE DOCUMENTATION
================================================================================
Date: 2026-09-29
Directory: BACKUP_ORIGINAL/
Description: Complete, pristine copy of original CropSense AI project prior to improvements.

1. ORIGINAL MODELS
--------------------------------------------------------------------------------
a. Crop Recommendation Model:
   - File: models/crop_model.pkl (~11.88 MB)
   - Algorithm: RandomForestClassifier (n_estimators=200, random_state=42, n_jobs=-1)
   - Source code: backend/train_model.py
   - Classes: 22 crop types (rice, maize, chickpea, kidneybeans, pigeonpeas,
     mothbeans, mungbean, blackgram, lentil, pomegranate, banana, mango, grapes,
     watermelon, muskmelon, apple, orange, papaya, coconut, cotton, jute, coffee).

b. Soil CNN Classifier:
   - Primary: models/soil_cnn_model.h5 (~11.38 MB, TensorFlow / Keras MobileNetV2)
   - Secondary / Fallback: models/soil_cnn_model.pkl (~287 KB, scikit-learn RF on color histogram)
   - Source code: cnn/train_cnn.py
   - Classes: 5 classes (black, clay, loamy, red, sandy)

2. ORIGINAL DATASETS
--------------------------------------------------------------------------------
a. Crop Recommendation Dataset:
   - File: datasets/Crop_recommendation.csv (100,422 bytes, 1,152 rows)
   - Original columns: N, P, K, temperature, humidity, ph, rainfall, label
   - Note: The original dataset does NOT have a soil_type column!
   - Soil type was synthetically added during training by a hard-coded mapping:
     df['soil_type'] = df['label'].map(CROP_TO_SOIL_TYPE).fillna('loamy')
     Crucially, "red" soil was completely omitted from CROP_TO_SOIL_TYPE.

b. Soil Image Dataset:
   - Directory: cnn/dataset/train/ (black, clay, loamy, red, sandy)
   - Count: 30 images per class (total 150 images, 128x128 pixels).
   - Origin: Generated synthetically by cnn/generate_sample_images.py using
     per-channel uniform noise, linspace waves, and random pebble ellipses.
   - Ground truth: Zero genuine soil field photographs.

3. ORIGINAL CNN BEHAVIOR & PREDICTION PIPELINE
--------------------------------------------------------------------------------
- File: cnn/predict_soil.py
- Preprocessing: Center crop to square, resize to 224x224, MobileNetV2 preprocess_input.
- Hybrid ensemble:
    combined = 0.70 * cnn_proba + 0.25 * color_similarity + 0.05 * texture_vector
  where color_similarity is distance to centroids derived from synthetic images:
    COLOR_CENTROIDS = {
        "black": (0.085, 0.071, 0.065),
        "clay": (0.489, 0.332, 0.214),
        "loamy": (0.356, 0.258, 0.160),
        "red": (0.607, 0.274, 0.176),
        "sandy": (0.781, 0.683, 0.506),
    }
- Image validation:
    - Laplacian variance < 100 => rejected as blurry
    - Mean brightness < 30 => rejected as too dark
    - Mean brightness > 225 => rejected as too bright
    - Combined confidence < 0.70 (SOIL_CONFIDENCE_THRESHOLD) => raises InvalidSoilImage
- Limitation: Because centroids and training data were synthetic noise boxes,
  genuine outdoor soil photos often receive low confidence (< 0.70) or misclassification.

4. ORIGINAL FEATURE VECTOR & ORDER
--------------------------------------------------------------------------------
- Dimensions: 8 features
- Feature order:
    1. N (Nitrogen)
    2. P (Phosphorus)
    3. K (Potassium)
    4. temperature (°C)
    5. humidity (%)
    6. ph
    7. rainfall (mm)
    8. soil_type_encoded (black=0, clay=1, loamy=2, red=3, sandy=4)

5. ORIGINAL N/P/K BEHAVIOR
--------------------------------------------------------------------------------
- In backend/predict_api.py line 305:
    N, P, K = 90, 40, 40
  Every prediction across all geographic locations unconditionally used fixed
  values (N=90, P=40, K=40). N/P/K were never queried from SoilGrids or location data.

6. ORIGINAL EXTERNAL APIS & GEOGRAPHIC BEHAVIOR
--------------------------------------------------------------------------------
a. OpenWeatherMap:
   - Fetches live temperature, humidity, and rainfall (1h/3h rain, often 0 on dry days).
   - Fallback based on latitude bands (abs(lat) <= 23, <= 35, <= 50, etc.).

b. SoilGrids ISRIC REST API:
   - Fetches phh2o (pH) and soc (soil organic carbon) at 0-5cm depth.
   - Does NOT fetch N, P, or K.
   - Fallback: returns pH=5.8, SOC=2.5 for tropical latitude band.

c. Regional Weighting Hack:
   - backend/predict_api.py applied _tropical_weighting():
     Multiplies probabilities of coffee, pepper, cardamom, arecanut, banana by up to 1.45x
     for coordinates in 11.0 <= lat <= 13.0, 74.0 <= lon <= 77.0 (Kodagu/Coorg region).

7. ORIGINAL DEPENDENCIES
--------------------------------------------------------------------------------
- Backend requirements.txt:
    fastapi==0.111.0
    uvicorn[standard]==0.29.0
    python-multipart==0.0.9
    httpx==0.27.0
    Pillow==10.3.0
    numpy==1.26.4
    pandas==2.2.2
    scikit-learn==1.4.2
    joblib==1.4.2
    requests==2.32.3
    tensorflow==2.16.1
    opencv-python==4.10.0.84
- Frontend:
    React 18.3.1, react-scripts 5.0.1, lucide-react 0.383.0, framer-motion 11.2.10, axios 1.7.2.

8. KNOWN LIMITATIONS OF ORIGINAL VERSION
--------------------------------------------------------------------------------
1. Soil training dataset consists entirely of synthetic 128x128 noise images. Real field photos fail.
2. Soil CNN confidence on real soil images drops below the 70% threshold because of color centroid penalties.
3. Crop dataset lacked a soil_type column; soil_type was synthetically mapped from crop label in circular fashion.
4. "Red" soil was omitted from the crop-to-soil mapping and thus has zero representation in the trained model.
5. N/P/K values are hardcoded to 90/40/40 globally.
6. OpenWeather rainfall (1h/3h instant rain) is semantically mismatched with dataset seasonal rainfall (mm/year).
7. Location diversity was faked using an artificial hardcoded multiplier table (_tropical_weighting) rather than legitimate soil/climate data differences.
================================================================================
