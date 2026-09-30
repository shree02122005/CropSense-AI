"""
predict_soil.py
───────────────
Predicts soil type from image bytes with improved reliability.
Automatically loads .h5 (TensorFlow CNN) if present, else .pkl (sklearn RF).

Features:
- Image quality validation (blur, brightness, darkness)
- Hybrid soil classification (CNN + color histogram + texture analysis)
- Detailed logging for debugging
- Consistent preprocessing between training and prediction
"""
import os, sys, io
import numpy as np
from PIL import Image
import tensorflow as tf
import cv2

ROOT_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H5_PATH   = os.path.join(ROOT_DIR, "models", "soil_cnn_model.h5")
PKL_PATH  = os.path.join(ROOT_DIR, "models", "soil_cnn_model.pkl")

SOIL_CLASSES = sorted(["black", "clay", "loamy", "red", "sandy"])

# Average RGB centroids for soil classes (normalized to 0-1)
COLOR_CENTROIDS = {
    "black": (0.085, 0.071, 0.065),
    "clay": (0.489, 0.332, 0.214),
    "loamy": (0.356, 0.258, 0.160),
    "red": (0.607, 0.274, 0.176),
    "sandy": (0.781, 0.683, 0.506),
}

# Configuration
IMG_SIZE = 224
BLUR_THRESHOLD = 100.0  # Laplacian variance threshold
DARKNESS_THRESHOLD = 30  # Min mean pixel intensity (0-255)
BRIGHTNESS_THRESHOLD = 225  # Max mean pixel intensity (0-255)
# Centralized soil confidence threshold used by training, prediction and API
SOIL_CONFIDENCE_THRESHOLD = 0.70
HISTOGRAM_CONFIDENCE_THRESHOLD = 0.70

_cache = {}


class InvalidSoilImage(Exception):
    """Raised when an uploaded image is not a valid soil image or prediction is uncertain."""


class SoilProcessingError(Exception):
    """Raised for unexpected processing errors during soil prediction."""

def _load():
    """Load model from cache or disk."""
    if "model" in _cache:
        return _cache["type"], _cache["model"]

    if os.path.exists(H5_PATH):
        try:
            m = tf.keras.models.load_model(H5_PATH)
            _cache["type"] = "tf"
            _cache["model"] = m
            return "tf", m
        except Exception as e:
            print(f"  [WARN] Failed to load .h5 model: {e}")

    if os.path.exists(PKL_PATH):
        import joblib
        bundle = joblib.load(PKL_PATH)
        _cache["type"] = "pkl"
        _cache["model"] = bundle
        return "pkl", bundle

    raise FileNotFoundError(
        "No soil model found. Run:  python cnn/train_cnn.py"
    )


def _validate_image_quality(img: Image.Image, image_name: str = "image") -> tuple[bool, str]:
    """
    Validate image quality before prediction.
    Returns: (is_valid: bool, reason: str)
    """
    arr = np.array(img)
    
    # Convert to grayscale for blur detection
    if len(arr.shape) == 3:
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    else:
        gray = arr
    
    # Check blur using Laplacian variance
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var < BLUR_THRESHOLD:
        return False, f"Image too blurry (blur score: {laplacian_var:.1f}). Please upload a clearer soil image."
    
    # Check brightness/darkness
    mean_intensity = np.mean(arr)
    if mean_intensity < DARKNESS_THRESHOLD:
        return False, f"Image too dark (brightness: {mean_intensity:.1f}). Please ensure adequate lighting."
    if mean_intensity > BRIGHTNESS_THRESHOLD:
        return False, f"Image too bright (brightness: {mean_intensity:.1f}). Please reduce glare/overexposure."
    
    return True, "OK"


def _preprocess_image(image_bytes: bytes) -> tuple[np.ndarray, Image.Image]:
    """
    Preprocess image for prediction.
    Returns: (normalized_array, PIL_image_224x224)
    Ensures consistent preprocessing between training and prediction.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # Center crop to square (same as training)
    width, height = img.size
    min_dim = min(width, height)
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim
    img = img.crop((left, top, right, bottom))
    
    # Resize (same as training)
    img = img.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.LANCZOS)
    
    # Normalize for MobileNetV2 (same preprocessing as training)
    arr = np.array(img, dtype=np.float32)
    arr = tf.keras.applications.mobilenet_v2.preprocess_input(arr)
    
    return arr, img


def _extract_color_features(img: Image.Image) -> dict:
    """
    Extract color histogram features for hybrid classification.
    Analyzes dominant colors to boost certain soil types.
    """
    arr = np.array(img, dtype=np.float32) / 255.0
    
    # Color channel analysis
    r_mean = np.mean(arr[:, :, 0])
    g_mean = np.mean(arr[:, :, 1])
    b_mean = np.mean(arr[:, :, 2])
    
    # Texture analysis: compute Laplacian for roughness/cracking (clay indicator)
    gray = cv2.cvtColor((arr * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    texture_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    return {
        "r_mean": float(r_mean),
        "g_mean": float(g_mean),
        "b_mean": float(b_mean),
        "texture_score": float(texture_score),
    }


def _extract_hist_features(img: Image.Image) -> np.ndarray:
    """Extract histogram features for sklearn model (from training)."""
    arr = np.array(img, dtype=np.float32) / 255.0
    feats = []
    for c in range(3):
        ch = (arr[:, :, c].flatten() * 255).astype(np.uint8)
        hist, _ = np.histogram(ch, bins=16, range=(0, 255))
        feats.extend(hist / (hist.sum() + 1e-9))
        feats.append(arr[:, :, c].mean())
        feats.append(arr[:, :, c].std())
    return np.array(feats)


def _compute_color_similarity(r: float, g: float, b: float) -> np.ndarray:
    """Compute a normalized color similarity probability vector against class centroids."""
    similarities = []
    max_dist = np.sqrt(3.0)
    for cls in SOIL_CLASSES:
        cr, cg, cb = COLOR_CENTROIDS[cls]
        dist = np.sqrt((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2)
        similarity = max(0.0, 1.0 - (dist / max_dist))
        similarities.append(similarity)
    similarities = np.array(similarities, dtype=np.float32)
    if similarities.sum() <= 0:
        return np.ones_like(similarities) / len(similarities)
    return similarities / similarities.sum()


def _hybrid_soil_classification(
    cnn_proba: np.ndarray = None,
    hist_proba: np.ndarray = None,
    color_features: dict = None,
    logging: bool = False
) -> tuple[str, float]:
    """
    Hybrid classification combining CNN, color similarity, and texture heuristics.
    """
    combined = np.zeros(len(SOIL_CLASSES), dtype=np.float32)
    
    # Primary signal: CNN
    if cnn_proba is not None:
        combined += 0.70 * cnn_proba
    else:
        combined += 0.70 * (np.ones(len(SOIL_CLASSES), dtype=np.float32) / len(SOIL_CLASSES))
    
    # Secondary signal: RGB color similarity
    color_similarity = np.ones(len(SOIL_CLASSES), dtype=np.float32) / len(SOIL_CLASSES)
    texture_vector = np.ones(len(SOIL_CLASSES), dtype=np.float32) / len(SOIL_CLASSES)
    debug_color = None
    debug_texture = None
    
    if color_features is not None:
        r = color_features["r_mean"]
        g = color_features["g_mean"]
        b = color_features["b_mean"]
        texture = color_features["texture_score"]
        
        debug_color = _compute_color_similarity(r, g, b)
        color_similarity = debug_color
        
        # Apply reduced texture-based heuristics only for ambiguous classes
        if texture > 150:
            texture_vector[SOIL_CLASSES.index("clay")] *= 1.10
        
        uniformity = 1.0 - np.std([r, g, b])
        if uniformity > 0.70:
            texture_vector[SOIL_CLASSES.index("loamy")] *= 1.05
        
        if r > 0.50 and g < 0.35 and b < 0.25:
            texture_vector[SOIL_CLASSES.index("red")] *= 1.10
        
        texture_vector = texture_vector / (texture_vector.sum() + 1e-9)
        debug_texture = texture_vector
        combined += 0.25 * color_similarity
        combined += 0.05 * texture_vector
    else:
        combined += 0.30 * (np.ones(len(SOIL_CLASSES), dtype=np.float32) / len(SOIL_CLASSES))
    
    # Final normalization and selection
    combined = combined / (combined.sum() + 1e-9)
    idx = int(np.argmax(combined))
    conf = float(combined[idx])
    
    if logging:
        print(f"\n  [Hybrid Classification]")
        if color_features is not None:
            print(f"    RGB: R={color_features['r_mean']:.3f}, G={color_features['g_mean']:.3f}, B={color_features['b_mean']:.3f}")
            print(f"    Color similarity:")
            for i, cls in enumerate(SOIL_CLASSES):
                print(f"      {cls:10s}: {debug_color[i]:.4f}")
            print(f"    Texture vector:")
            for i, cls in enumerate(SOIL_CLASSES):
                print(f"      {cls:10s}: {debug_texture[i]:.4f}")
        if cnn_proba is not None:
            print(f"    CNN probabilities:")
            for i, cls in enumerate(SOIL_CLASSES):
                print(f"      {cls:10s}: {cnn_proba[i]:.4f}")
        if hist_proba is not None:
            print(f"    Histogram probabilities (unused in final weights):")
            for i, cls in enumerate(SOIL_CLASSES):
                print(f"      {cls:10s}: {hist_proba[i]:.4f}")
        print(f"    Final combined probabilities:")
        for i, cls in enumerate(SOIL_CLASSES):
            print(f"      {cls:10s}: {combined[i]:.4f}")
        print(f"  Selected: {SOIL_CLASSES[idx]} (confidence: {conf:.4f})")
    
    return SOIL_CLASSES[idx], conf


def predict_soil_from_bytes(image_bytes: bytes, verbose: bool = False) -> tuple:
    """
    Predict soil type from image bytes with improved reliability.
    
    Returns:
        (soil_class: str, confidence: float)
        or ("Prediction uncertain. Please upload a clearer soil image.", 0.0)
    """
    try:
        # Load image and validate quality
        temp_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        is_valid, reason = _validate_image_quality(temp_img)
        if not is_valid:
            if verbose:
                print(f"  [Image Validation] {reason}")
            raise InvalidSoilImage(reason)
        
        # Preprocess
        arr_preprocessed, img_224 = _preprocess_image(image_bytes)
        
        # Get model
        kind, model = _load()
        
        cnn_proba = None
        hist_proba = None
        
        if kind == "tf":
            # CNN prediction
            arr_batch = np.expand_dims(arr_preprocessed, 0)
            cnn_proba = model.predict(arr_batch, verbose=0)[0]
            
            if verbose:
                print(f"\n  [CNN Prediction]")
                for i, cls in enumerate(SOIL_CLASSES):
                    print(f"    {cls:10s}: {cnn_proba[i]:.4f}")
        
        # Histogram-based prediction (always compute for hybrid)
        hist_feats = _extract_hist_features(img_224)
        
        if kind == "tf":
            # For TensorFlow models, still compute histogram for hybrid
            # We'll use it for confidence boost but won't have sklearn model
            pass
        elif kind == "pkl":
            # Sklearn model available
            clf = model["model"]
            hist_proba = clf.predict_proba(hist_feats.reshape(1, -1))[0]
            if verbose:
                print(f"\n  [Histogram Prediction]")
                for i, cls in enumerate(SOIL_CLASSES):
                    print(f"    {cls:10s}: {hist_proba[i]:.4f}")
        
        # Color and texture features
        color_features = _extract_color_features(img_224)
        if verbose:
            print(f"\n  [Color Features]")
            print(f"    R: {color_features['r_mean']:.3f}, G: {color_features['g_mean']:.3f}, B: {color_features['b_mean']:.3f}")
            print(f"    Texture (Laplacian variance): {color_features['texture_score']:.1f}")
        
        # Hybrid classification
        soil_type, confidence = _hybrid_soil_classification(
            cnn_proba=cnn_proba,
            hist_proba=hist_proba,
            color_features=color_features,
            logging=verbose
        )

        # Apply centralized confidence threshold
        if confidence < SOIL_CONFIDENCE_THRESHOLD:
            msg = f"Prediction uncertain. Please upload a clearer soil image. (confidence: {confidence:.1%})"
            if verbose:
                print(f"\n  [Confidence Check] {msg}")
            raise InvalidSoilImage(msg)
        
        if verbose:
            print(f"\n  ✓ Final Prediction: {soil_type} ({confidence:.1%})")
        
        return soil_type, confidence
    
    except InvalidSoilImage:
        raise
    except Exception as e:
        error_msg = f"Error processing image: {str(e)}"
        if verbose:
            print(f"  [ERROR] {error_msg}")
        raise SoilProcessingError(error_msg)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python predict_soil.py <image_path> [--verbose]")
        sys.exit(1)
    
    verbose = "--verbose" in sys.argv
    with open(sys.argv[1], "rb") as f:
        data = f.read()
    
    try:
        soil, conf = predict_soil_from_bytes(data, verbose=verbose)
        print(f"\nSoil type : {soil}")
        print(f"Confidence: {conf:.4f}" if conf > 0 else "")
    except InvalidSoilImage as e:
        print(f"Soil prediction failed: {e}")
        sys.exit(2)
    except SoilProcessingError as e:
        print(f"Processing error: {e}")
        sys.exit(3)
