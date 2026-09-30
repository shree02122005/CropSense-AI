"""
Enhanced soil classifier audit with detailed weight tracking
"""
import sys
sys.path.insert(0, '.')

from cnn.predict_soil import predict_soil_from_bytes, SOIL_CLASSES, InvalidSoilImage

print("="*80)
print(" "*20 + "SOIL CLASSIFIER PIPELINE AUDIT")
print("="*80)
print()
print("Testing: clay_001.jpg from training dataset")
print()

# Load image
with open('cnn/dataset/train/clay/clay_001.jpg', 'rb') as f:
    image_bytes = f.read()

print("RUNNING FULL PREDICTION PIPELINE:")
print("-" * 80)

try:
    # Run prediction with full verbose output
    soil_type, confidence = predict_soil_from_bytes(image_bytes, verbose=True)
    
    print()
    print("="*80)
    print("PIPELINE SUMMARY & HYBRID WEIGHTS")
    print("="*80)
    print()
    print("COMPONENTS IN CLASSIFICATION:")
    print("  1. CNN Model (TensorFlow):         60% weight (0.60)")
    print("  2. Histogram Features:              30% weight (0.30) [if sklearn model available]")
    print("  3. Color & Texture Analysis:       Applied as post-combination boost")
    print()
    print("COLOR HEURISTIC BOOSTING RULES:")
    print("  • Black soil:   boost 1.15x if (R > 0.35 AND G > 0.30 AND B < 0.25)")
    print("  • Red soil:     boost 1.15x if (R > 0.40 AND G < 0.35 AND B < 0.25)")
    print("  • Sandy soil:   boost 1.15x if (R > 0.45 AND G > 0.45 AND B > 0.35)")
    print("  • Clay soil:    boost 1.10x if (texture Laplacian variance > 150)")
    print("  • Loamy soil:   boost 1.05x if (color uniformity > 0.70)")
    print()
    print("IMAGE VALIDATION THRESHOLDS:")
    print("  • Blur score:        < 100.0 required")
    print("  • Darkness:          brightness > 30 required")
    print("  • Brightness:        brightness < 225 required")
    print()
    print("PREDICTION CONFIDENCE THRESHOLD: >= 30% required")
    print()
    print("="*80)
    print(f"✓ FINAL CLASSIFICATION: {soil_type} ({confidence:.1%} confidence)")
    print("="*80)
    
except InvalidSoilImage as e:
    print(f"[VALIDATION FAILED] {e}")
except Exception as e:
    print(f"[ERROR] {e}")
