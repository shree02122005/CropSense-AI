"""
train_cnn.py
────────────
Trains the soil image classifier (black / clay / loamy / red / sandy).

• If TensorFlow is installed → MobileNetV2 transfer learning, saved to
  models/soil_cnn_model.keras (+ .h5)
• If TensorFlow is NOT installed → colour-histogram RandomForest fallback,
  saved to models/soil_cnn_model.pkl  (predict_soil.py handles both)

MobileNetV2 training pipeline:
  1. Images are loaded with EXACTLY the preprocessing used in predict_soil.py
     (square center crop → 224x224 LANCZOS → mobilenet_v2.preprocess_input),
     so the model sees the same input distribution at train and inference time.
  2. Any training image that is a byte-identical copy of a test image is
     dropped (prevents test-set leakage), and in-train duplicates are removed.
  3. Stratified train / validation split (seeded, reproducible).
  4. On-the-fly augmentation suited to soil texture photos
     (h+v flips, 90° rotations, small zoom, brightness/contrast jitter).
  5. Phase 1: frozen MobileNetV2 backbone, train the classification head.
  6. Phase 2: fine-tune the top MobileNetV2 blocks at a low learning rate
     (BatchNorm layers stay frozen so small batches don't wreck statistics).
  7. Final evaluation on the held-out cnn/dataset/test set: accuracy,
     per-class report and confusion matrix, written to
     models/soil_cnn_metrics.json.

Run from project root:
    python cnn/train_cnn.py
"""
import os, sys, json, hashlib, random
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from PIL import Image

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR     = os.path.dirname(BASE_DIR)
DATASET_DIR  = os.path.join(BASE_DIR, "dataset", "train")
TEST_DIR     = os.path.join(BASE_DIR, "dataset", "test")
H5_PATH      = os.path.join(ROOT_DIR, "models", "soil_cnn_model.h5")
KERAS_PATH   = os.path.join(ROOT_DIR, "models", "soil_cnn_model.keras")
PKL_PATH     = os.path.join(ROOT_DIR, "models", "soil_cnn_model.pkl")
METRICS_PATH = os.path.join(ROOT_DIR, "models", "soil_cnn_metrics.json")

IMG_SIZE        = 224
BATCH_SIZE      = 16
SEED            = 42
VAL_FRACTION    = 0.15
HEAD_EPOCHS     = 40
FINETUNE_EPOCHS = 40
FINETUNE_LAYERS = 40          # number of top MobileNetV2 layers to unfreeze
SOIL_CLASSES    = sorted(["black", "clay", "loamy", "red", "sandy"])
IMG_EXTS        = ('.jpg', '.jpeg', '.png')

os.makedirs(os.path.join(ROOT_DIR, "models"), exist_ok=True)
random.seed(SEED)
np.random.seed(SEED)

print("=" * 60)
print("  Soil Classifier - MobileNetV2 Training")
print("=" * 60)


# ── Shared preprocessing (MUST match predict_soil._preprocess_image) ─────────
def _load_rgb_224(img_path: str) -> np.ndarray:
    """Square center crop → 224x224 LANCZOS. Returns float32 RGB in [0, 255]."""
    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    m = min(w, h)
    left, top = (w - m) // 2, (h - m) // 2
    img = img.crop((left, top, left + m, top + m))
    img = img.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.LANCZOS)
    return np.array(img, dtype=np.float32)


def _md5(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _list_images(root: str):
    """Return [(path, class_idx), ...] for every image under root/<class>/."""
    items = []
    for idx, cls in enumerate(SOIL_CLASSES):
        d = os.path.join(root, cls)
        if not os.path.isdir(d):
            print(f"  WARNING: missing folder {d}")
            continue
        for f in sorted(os.listdir(d)):
            if f.lower().endswith(IMG_EXTS):
                items.append((os.path.join(d, f), idx))
    return items


def load_dataset(root: str, exclude_hashes=frozenset(), dedupe=True):
    """Load images (RGB 0-255) + labels, skipping duplicates / excluded hashes."""
    X, y, seen = [], [], set()
    skipped_leak = skipped_dup = 0
    for path, idx in _list_images(root):
        h = _md5(path)
        if h in exclude_hashes:
            skipped_leak += 1
            continue
        if dedupe and h in seen:
            skipped_dup += 1
            continue
        seen.add(h)
        try:
            X.append(_load_rgb_224(path))
            y.append(idx)
        except Exception as e:
            print(f"    Skip {path}: {e}")
    if skipped_leak:
        print(f"  Removed {skipped_leak} training image(s) duplicated in the test set (leakage)")
    if skipped_dup:
        print(f"  Removed {skipped_dup} duplicate image(s)")
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int64)


def stratified_split(y: np.ndarray, val_fraction: float, seed: int):
    rng = np.random.default_rng(seed)
    tr, va = [], []
    for c in np.unique(y):
        idx = np.where(y == c)[0]
        rng.shuffle(idx)
        n_val = max(1, int(round(len(idx) * val_fraction)))
        va.extend(idx[:n_val])
        tr.extend(idx[n_val:])
    return np.array(tr), np.array(va)


def extract_hist_features(X_imgs: np.ndarray) -> np.ndarray:
    """Histogram features for the sklearn fallback (X in 0-1, SAME as predict_soil.py)."""
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


def _confusion(y_true, y_pred, n):
    cm = np.zeros((n, n), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[t, p] += 1
    return cm


print("\n[1/5] Loading dataset (center-crop preprocessing identical to inference)...")
test_hashes = frozenset(_md5(p) for p, _ in _list_images(TEST_DIR))
X_all, y_all = load_dataset(DATASET_DIR, exclude_hashes=test_hashes)
X_test, y_test = load_dataset(TEST_DIR, dedupe=False)
if len(X_all) == 0:
    print("ERROR: No training images found. Run:  python cnn/prepare_genuine_dataset.py")
    sys.exit(1)
for i, cls in enumerate(SOIL_CLASSES):
    print(f"  {cls:6}: train {int((y_all == i).sum()):3d} | test {int((y_test == i).sum()):3d}")

try:
    import tensorflow as tf
    tf.keras.utils.set_random_seed(SEED)

    num_classes = len(SOIL_CLASSES)
    preprocess = tf.keras.applications.mobilenet_v2.preprocess_input

    tr_idx, va_idx = stratified_split(y_all, VAL_FRACTION, SEED)
    X_tr, y_tr = X_all[tr_idx], y_all[tr_idx]
    X_va, y_va = X_all[va_idx], y_all[va_idx]
    print(f"\n[2/5] Split: {len(X_tr)} train / {len(X_va)} validation / {len(X_test)} test")

    # Augmentation operates on raw 0-255 pixels, before MobileNetV2 scaling.
    augment = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal_and_vertical"),
        tf.keras.layers.RandomRotation(0.25, fill_mode="reflect"),
        tf.keras.layers.RandomZoom((-0.20, 0.0), fill_mode="reflect"),
        tf.keras.layers.RandomTranslation(0.10, 0.10, fill_mode="reflect"),
        tf.keras.layers.RandomBrightness(0.15, value_range=(0, 255)),
        tf.keras.layers.RandomContrast(0.15),
    ], name="augment")

    def make_ds(X, y, training):
        y_oh = tf.keras.utils.to_categorical(y, num_classes)
        ds = tf.data.Dataset.from_tensor_slices((X, y_oh))
        if training:
            ds = ds.shuffle(len(X), seed=SEED, reshuffle_each_iteration=True)
        ds = ds.batch(BATCH_SIZE)
        if training:
            ds = ds.map(lambda a, b: (tf.clip_by_value(augment(a, training=True), 0, 255), b),
                        num_parallel_calls=tf.data.AUTOTUNE)
        ds = ds.map(lambda a, b: (preprocess(a), b), num_parallel_calls=tf.data.AUTOTUNE)
        return ds.prefetch(tf.data.AUTOTUNE)

    train_ds = make_ds(X_tr, y_tr, True)
    val_ds   = make_ds(X_va, y_va, False)
    test_ds  = make_ds(X_test, y_test, False)

    # Architecture kept identical to predict_soil._build_mobilenet_model so the
    # .h5 weights fallback still loads.
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3), include_top=False, weights="imagenet"
    )
    base_model.trainable = False
    model = tf.keras.Sequential([
        tf.keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3)),
        base_model,
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dense(256, activation="relu"),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(num_classes, activation="softmax"),
    ])

    def callbacks(patience):
        return [
            tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=patience,
                                             restore_best_weights=True, verbose=1),
            tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5,
                                                 patience=3, min_lr=1e-7, verbose=1),
        ]

    # ── Phase 1: train head on frozen backbone ───────────────────────────────
    print("\n[3/5] Phase 1 - training classification head (backbone frozen)...")
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3),
                  loss="categorical_crossentropy", metrics=["accuracy"])
    h1 = model.fit(train_ds, validation_data=val_ds, epochs=HEAD_EPOCHS,
                   callbacks=callbacks(8), verbose=2)

    # ── Phase 2: fine-tune top of backbone ───────────────────────────────────
    print(f"\n[4/5] Phase 2 - fine-tuning top {FINETUNE_LAYERS} MobileNetV2 layers...")
    base_model.trainable = True
    for layer in base_model.layers[:-FINETUNE_LAYERS]:
        layer.trainable = False
    for layer in base_model.layers:
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False   # keep ImageNet BN statistics (inference mode)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-5),
                  loss="categorical_crossentropy", metrics=["accuracy"])
    h2 = model.fit(train_ds, validation_data=val_ds, epochs=FINETUNE_EPOCHS,
                   callbacks=callbacks(10), verbose=2)

    # ── Evaluation on held-out test set ──────────────────────────────────────
    print("\n[5/5] Evaluating on held-out test set...")
    test_proba = model.predict(test_ds, verbose=0)
    test_pred = test_proba.argmax(axis=1)
    test_acc = float((test_pred == y_test).mean())
    val_loss, val_acc = model.evaluate(val_ds, verbose=0)
    cm = _confusion(y_test, test_pred, num_classes)

    print(f"  Validation accuracy: {val_acc:.1%}")
    print(f"  TEST accuracy      : {test_acc:.1%}  ({int((test_pred == y_test).sum())}/{len(y_test)})")
    print(f"  Mean top-1 confidence on test: {test_proba.max(axis=1).mean():.1%}")
    print("\n  Confusion matrix (rows = true, cols = predicted):")
    print("          " + " ".join(f"{c[:5]:>6}" for c in SOIL_CLASSES))
    for i, cls in enumerate(SOIL_CLASSES):
        print(f"  {cls:7} " + " ".join(f"{v:6d}" for v in cm[i]))
    per_class = {}
    for i, cls in enumerate(SOIL_CLASSES):
        tp = cm[i, i]
        prec = tp / max(1, cm[:, i].sum())
        rec = tp / max(1, cm[i, :].sum())
        f1 = 2 * prec * rec / max(1e-9, prec + rec)
        per_class[cls] = {"precision": round(float(prec), 3), "recall": round(float(rec), 3),
                          "f1": round(float(f1), 3)}
        print(f"  {cls:7} precision {prec:.2f}  recall {rec:.2f}  f1 {f1:.2f}")

    print(f"\n  Saving model -> {KERAS_PATH} and {H5_PATH}")
    model.save(KERAS_PATH)
    try:
        model.save(H5_PATH)
    except Exception as e:
        print(f"  Note on H5 save: {e}; saving weights instead")
        model.save_weights(H5_PATH)

    with open(METRICS_PATH, "w") as f:
        json.dump({
            "architecture": "MobileNetV2 (ImageNet) + dense head, 2-phase fine-tuning",
            "classes": SOIL_CLASSES,
            "n_train": int(len(X_tr)), "n_val": int(len(X_va)), "n_test": int(len(X_test)),
            "head_epochs_run": len(h1.history["loss"]),
            "finetune_epochs_run": len(h2.history["loss"]),
            "val_accuracy": round(float(val_acc), 4),
            "test_accuracy": round(test_acc, 4),
            "test_mean_confidence": round(float(test_proba.max(axis=1).mean()), 4),
            "per_class": per_class,
            "confusion_matrix": cm.tolist(),
        }, f, indent=2)
    print(f"  Metrics -> {METRICS_PATH}")

except ImportError:
    print("\n[2/5] TensorFlow not found - using colour-histogram RandomForest fallback...")
    import joblib
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, classification_report

    clf = RandomForestClassifier(n_estimators=250, max_depth=30, min_samples_split=4,
                                 min_samples_leaf=2, random_state=SEED, n_jobs=-1)
    clf.fit(extract_hist_features(X_all / 255.0), y_all)
    y_hat = clf.predict(extract_hist_features(X_test / 255.0))
    print(f"  TEST accuracy: {accuracy_score(y_test, y_hat):.1%}")
    print(classification_report(y_test, y_hat, target_names=SOIL_CLASSES))
    joblib.dump({"model": clf, "classes": SOIL_CLASSES, "type": "sklearn_colour_hist"}, PKL_PATH)
    print(f"  Saved -> {PKL_PATH}")

print("=" * 60)
print("  Training complete!")
print("=" * 60)
