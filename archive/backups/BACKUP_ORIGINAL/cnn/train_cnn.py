"""
train_cnn.py
────────────
Trains a soil image classifier with improved reliability.

• If TensorFlow is installed → trains a real CNN and saves .h5
• If TensorFlow is NOT installed → trains a colour-histogram RF classifier
  and saves to soil_cnn_model.pkl  (predict_soil.py handles both automatically)

Features:
- Consistent preprocessing (center crop + resize + normalize)
- Enhanced data augmentation (rotation, zoom, brightness, flip)
- Validation split for early stopping
- Transfer learning with MobileNetV2

Run from project root:
    python cnn/train_cnn.py
"""
import os, sys
import numpy as np
from PIL import Image
import cv2

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.dirname(BASE_DIR)
DATASET_DIR = os.path.join(BASE_DIR, "dataset", "train")
H5_PATH     = os.path.join(ROOT_DIR, "models", "soil_cnn_model.h5")
PKL_PATH    = os.path.join(ROOT_DIR, "models", "soil_cnn_model.pkl")

IMG_SIZE     = 224
BATCH_SIZE   = 16
EPOCHS       = 20
SOIL_CLASSES = sorted(["black", "clay", "loamy", "red", "sandy"])

os.makedirs(os.path.join(ROOT_DIR, "models"), exist_ok=True)

print("=" * 60)
print("  Soil Classifier - Training with Enhanced Reliability")
print("=" * 60)

def _preprocess_image_consistent(img_path: str, img_size: int) -> np.ndarray:
    """
    Preprocess image with center crop, resize, and normalization.
    MUST match the preprocessing in predict_soil.py
    """
    img = Image.open(img_path).convert("RGB")
    
    # Center crop to square (SAME as predict_soil.py)
    width, height = img.size
    min_dim = min(width, height)
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim
    img = img.crop((left, top, right, bottom))
    
    # Resize to target (SAME as predict_soil.py)
    img = img.resize((img_size, img_size), Image.Resampling.LANCZOS)
    
    # Convert to array
    arr = np.array(img, dtype=np.float32)
    
    return arr


def load_images(dataset_dir: str, img_size: int) -> tuple:
    """Load images with consistent preprocessing."""
    X, y = [], []
    
    for idx, cls in enumerate(SOIL_CLASSES):
        cls_dir = os.path.join(dataset_dir, cls)
        if not os.path.exists(cls_dir):
            print(f"  WARNING: missing folder {cls_dir}")
            continue
        
        files = [f for f in os.listdir(cls_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        print(f"  {cls}: {len(files)} images")
        
        for f in files:
            try:
                img_path = os.path.join(cls_dir, f)
                arr = _preprocess_image_consistent(img_path, img_size)
                
                # Normalize to [0, 1] for augmentation
                arr = arr / 255.0
                
                X.append(arr)
                y.append(idx)
            except Exception as e:
                print(f"    Skip {f}: {e}")
    
    return np.array(X), np.array(y)


def extract_hist_features(X_imgs: np.ndarray) -> np.ndarray:
    """Extract histogram features for sklearn fallback (SAME as predict_soil.py)."""
    feats = []
    for img in X_imgs:
        f = []
        for c in range(3):
            ch = (img[:, :, c].flatten() * 255).astype(np.uint8)
            hist, _ = np.histogram(ch, bins=16, range=(0, 255))
            f.extend(hist / (hist.sum() + 1e-9))
            f.append(img[:, :, c].mean())
            f.append(img[:, :, c].std())
        feats.append(f)
    return np.array(feats)


print("\n[1/4] Checking dataset...")

try:
    import tensorflow as tf
    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    print("\n[2/4] TensorFlow found - training CNN with enhanced augmentation...")
    num_classes = len(SOIL_CLASSES)

    # ENHANCED data augmentation (rotation, zoom, brightness, flip)
    train_datagen = ImageDataGenerator(
        rotation_range=15,              # ↑ from 10
        width_shift_range=0.10,         # ↑ from 0.05
        height_shift_range=0.10,        # ↑ from 0.05
        zoom_range=0.15,                # ↑ from 0.05
        brightness_range=[0.85, 1.15], # ↑ from [0.9, 1.1]
        horizontal_flip=True,
        fill_mode='reflect',            # Better than default
        validation_split=0.2,
        preprocessing_function=tf.keras.applications.mobilenet_v2.preprocess_input
    )

    val_datagen = ImageDataGenerator(
        validation_split=0.2,
        preprocessing_function=tf.keras.applications.mobilenet_v2.preprocess_input
    )

    train_generator = train_datagen.flow_from_directory(
        DATASET_DIR,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='training',
        classes=SOIL_CLASSES,
        interpolation='lanczos'  # Match preprocessing
    )

    val_generator = val_datagen.flow_from_directory(
        DATASET_DIR,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='validation',
        classes=SOIL_CLASSES,
        interpolation='lanczos'
    )

    if train_generator.samples == 0:
        print("ERROR: No images found. Run:  python cnn/generate_sample_images.py")
        sys.exit(1)

    print(f"  Training samples: {train_generator.samples}")
    print(f"  Validation samples: {val_generator.samples}")

    # Improved CNN architecture with transfer learning
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False  # Freeze the base model

    model = tf.keras.Sequential([
        base_model,
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dense(256, activation="relu"),     # ↑ from 128
        tf.keras.layers.BatchNormalization(),              # ✓ NEW
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(128, activation="relu"),     # ✓ NEW
        tf.keras.layers.Dropout(0.3),                      # ✓ NEW
        tf.keras.layers.Dense(num_classes, activation="softmax"),
    ])
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    model.summary()

    print("\n[3/4] Training with enhanced augmentation and validation...")
    history = model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=EPOCHS,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                monitor='val_accuracy',
                patience=5,
                restore_best_weights=True,
                verbose=1
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=2,
                min_lr=0.00001,
                verbose=1
            )
        ],
        verbose=1
    )
    
    best_val = max(history.history["val_accuracy"])
    print(f"\n  ✓ Best validation accuracy: {best_val:.4f} ({best_val*100:.2f}%)")

    print(f"\n[4/4] Saving CNN -> {H5_PATH}")
    model.save(H5_PATH)
    print("  ✓ CNN model saved (TensorFlow .h5)\n")

except ImportError:
    print("\n[2/4] TensorFlow not found - using colour-histogram + texture RF classifier...")
    X, y = load_images(DATASET_DIR, IMG_SIZE)
    
    if len(X) == 0:
        print("ERROR: No images found. Run:  python cnn/generate_sample_images.py")
        sys.exit(1)
    
    print(f"  ✓ Loaded {len(X)} images ({len(SOIL_CLASSES)} classes)")

    import joblib
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report

    # Extract features (histogram + texture)
    feats = extract_hist_features(X)
    print(f"  ✓ Extracted {feats.shape[1]} features per image")
    
    X_tr, X_te, y_tr, y_te = train_test_split(
        feats, y, test_size=0.2, random_state=42, stratify=y
    )

    print("\n[3/4] Training RandomForest with 250 trees...")
    clf = RandomForestClassifier(
        n_estimators=250,               # ↑ from 200
        max_depth=30,                   # ✓ NEW
        min_samples_split=4,            # ✓ NEW
        min_samples_leaf=2,             # ✓ NEW
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    clf.fit(X_tr, y_tr)
    
    train_acc = accuracy_score(y_tr, clf.predict(X_tr))
    test_acc = accuracy_score(y_te, clf.predict(X_te))
    
    print(f"\n  Training accuracy: {train_acc:.4f} ({train_acc*100:.2f}%)")
    print(f"  ✓ Test accuracy: {test_acc:.4f} ({test_acc*100:.2f}%)")
    
    print("\n[Classification Report]")
    print(classification_report(y_te, clf.predict(X_te), target_names=SOIL_CLASSES))

    bundle = {
        "model": clf,
        "classes": SOIL_CLASSES,
        "type": "sklearn_colour_hist"
    }
    
    print(f"\n[4/4] Saving -> {PKL_PATH}")
    joblib.dump(bundle, PKL_PATH)
    print("  ✓ Soil classifier saved (sklearn .pkl)\n")

print("=" * 60)
print("  Training complete!")
print("=" * 60)
