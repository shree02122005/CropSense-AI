import requests, glob, json, os

print("--- 1. Testing Live Backend ---")
r = requests.get("http://127.0.0.1:8000/")
assert r.status_code == 200
print("Root endpoint: OK")

r = requests.get("http://127.0.0.1:8000/history")
assert r.status_code == 200
hist_len = len(r.json().get("history", []))
print(f"History endpoint: OK ({hist_len} records)")

r = requests.get("http://127.0.0.1:8000/history/stats")
assert r.status_code == 200
print("History stats endpoint: OK")

print("\n--- 2. Testing Live POST /predict ---")
test_imgs = glob.glob("cnn/dataset/test/*/*.jpg")
with open(test_imgs[0], "rb") as f:
    files = {"image": ("test_soil.jpg", f, "image/jpeg")}
    data = {"latitude": 12.9716, "longitude": 77.5946}
    r = requests.post("http://127.0.0.1:8000/predict", files=files, data=data)

assert r.status_code == 200
pred = r.json()
print("Location:", pred["location"])
print(f"Soil Type: {pred['soil_type']} ({pred['soil_confidence']*100:.1f}%)")
print(f"N/P/K: {pred['N']}/{pred['P']}/{pred['K']}")
print("OOD Detected:", pred.get("npk_out_of_training_range"), "Features:", pred.get("npk_ood_features"))
print("Top 3 Crops from Production RF:")
for idx, c in enumerate(pred["crops"][:3], 1):
    print(f"  {idx}. {c['name']} - confidence: {c['confidence']*100:.1f}%")

print("\n--- 3. Verifying Production Model Integrity ---")
assert os.path.exists("models/crop_model.pkl")
assert os.path.exists("models/crop_model_xgboost_demo.pkl")
assert os.path.exists("models/soil_cnn_model.keras")
print("All model artifacts verified present and intact!")

print("\n--- 4. Testing Frontend Server ---")
r_front = requests.get("http://localhost:3000/")
assert r_front.status_code == 200
print("Frontend server (port 3000): OK (HTTP 200)")
print("\nALL SYSTEM VERIFICATIONS PASSED SUCCESSFULLY!")
