"""
generate_sample_images.py
─────────────────────────
Generates 30 synthetic soil-like images per class using Pillow + NumPy.
No external image sources required.
"""

import os, sys
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

# Soil colour palettes (RGB base + variation)
SOIL_CONFIG = {
    "black":  {"base": (25,  20,  18),  "noise": 18,  "texture": "coarse"},
    "clay":   {"base": (140, 100, 70),  "noise": 22,  "texture": "smooth"},
    "loamy":  {"base": (105, 80,  55),  "noise": 30,  "texture": "mixed"},
    "red":    {"base": (160, 75,  50),  "noise": 25,  "texture": "coarse"},
    "sandy":  {"base": (200, 175, 130), "noise": 35,  "texture": "grain"},
}

IMG_SIZE    = 128
IMAGES_PER  = 30
BASE_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset", "train")

def make_texture(kind, size=IMG_SIZE):
    if kind == "grain":
        noise = np.random.randint(0, 255, (size, size), dtype=np.uint8)
        img = Image.fromarray(noise).convert("L")
        return np.stack([np.array(img)]*3, axis=-1)
    elif kind == "coarse":
        base = np.random.randint(0, 2, (size//4, size//4), dtype=np.uint8) * 200
        img  = Image.fromarray(base.astype(np.uint8)).resize((size,size), Image.NEAREST)
        arr  = np.stack([np.array(img)]*3, axis=-1)
        return arr
    elif kind == "smooth":
        x = np.linspace(0, 1, size)
        y = np.linspace(0, 1, size)
        xv, yv = np.meshgrid(x, y)
        wave = ((np.sin(xv*12) * np.cos(yv*8)) * 40 + 40).astype(np.uint8)
        return np.stack([wave]*3, axis=-1)
    else:  # mixed
        noise1 = np.random.randint(0, 60, (size, size, 3), dtype=np.uint8)
        noise2 = np.random.randint(0, 30, (size, size, 3), dtype=np.uint8)
        return (noise1.astype(int) + noise2.astype(int)).clip(0,255).astype(np.uint8)

def generate_soil_image(soil_class, idx, rng):
    cfg   = SOIL_CONFIG[soil_class]
    base  = np.array(cfg["base"], dtype=np.int32)
    noise = cfg["noise"]

    # Base colour canvas with per-channel noise
    canvas = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.int32)
    for c in range(3):
        canvas[:,:,c] = base[c]

    # Add random noise
    canvas += rng.integers(-noise, noise+1, (IMG_SIZE, IMG_SIZE, 3))

    # Add texture overlay
    tex = make_texture(cfg["texture"]).astype(np.int32)
    canvas += (tex - 128) // 6

    canvas = np.clip(canvas, 0, 255).astype(np.uint8)
    img    = Image.fromarray(canvas, "RGB")

    # Slight blur for realism
    img = img.filter(ImageFilter.GaussianBlur(radius=int(rng.integers(0, 2))))

    # Random pebble dots for coarse soils
    if cfg["texture"] in ("coarse", "mixed"):
        draw  = ImageDraw.Draw(img)
        n_peb = rng.integers(5, 20)
        for _ in range(n_peb):
            x, y  = rng.integers(0, IMG_SIZE, 2)
            r     = rng.integers(1, 5)
            shade = tuple(np.clip(np.array(cfg["base"]) + rng.integers(-30, 30, 3), 0, 255).tolist())
            draw.ellipse([x-r, y-r, x+r, y+r], fill=shade)

    return img

def main():
    rng = np.random.default_rng(seed=0)
    total = 0
    for soil_class in SOIL_CONFIG:
        out_dir = os.path.join(BASE_DIR, soil_class)
        os.makedirs(out_dir, exist_ok=True)
        for i in range(IMAGES_PER):
            img  = generate_soil_image(soil_class, i, rng)
            path = os.path.join(out_dir, f"{soil_class}_{i:03d}.jpg")
            img.save(path, "JPEG", quality=90)
            total += 1
        print(f"  {soil_class}: {IMAGES_PER} images → {out_dir}")
    print(f"\nTotal generated: {total} images")

if __name__ == "__main__":
    print("Generating synthetic soil images …")
    main()
    print("Done.")
