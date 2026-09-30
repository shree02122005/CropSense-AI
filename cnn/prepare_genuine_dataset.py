"""
prepare_genuine_dataset.py
--------------------------
Downloads genuine soil photographs for the 5 target soil classes:
- black (from Black_Soil)
- clay (from Laterite_Soil / Clay)
- loamy (from Alluvial_Soil / Loam)
- red (from Red_Soil)
- sandy (from Arid_Soil / Sand)

Splits into:
- cnn/dataset/train/ (40 images per class)
- cnn/dataset/test/  (10 images per class)

Also creates non-soil test images in cnn/dataset/test_non_soil/
"""

import os, io, sys, time
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import httpx
from PIL import Image, ImageDraw

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(ROOT_DIR, "cnn", "dataset")
TRAIN_DIR = os.path.join(DATASET_DIR, "train")
TEST_DIR = os.path.join(DATASET_DIR, "test")
NON_SOIL_DIR = os.path.join(DATASET_DIR, "test_non_soil")

CLASSES = {
    "black": "Black_Soil",
    "clay": "Laterite_Soil",
    "loamy": "Alluvial_Soil",
    "red": "Red_Soil",
    "sandy": "Arid_Soil",
}

def download_soil_images():
    print("=" * 60)
    print("  Downloading Genuine Soil Images for 5 Classes")
    print("=" * 60)
    
    headers = {"User-Agent": "CropSenseAI-Dataset-Builder/1.0"}
    
    for soil_class, github_folder in CLASSES.items():
        train_cls_dir = os.path.join(TRAIN_DIR, soil_class)
        test_cls_dir = os.path.join(TEST_DIR, soil_class)
        os.makedirs(train_cls_dir, exist_ok=True)
        os.makedirs(test_cls_dir, exist_ok=True)
        
        # Check existing real images to resume
        existing_train = len([f for f in os.listdir(train_cls_dir) if f.startswith("real_")])
        existing_test = len([f for f in os.listdir(test_cls_dir) if f.startswith("test_")])
        if existing_train >= 40 and existing_test >= 10:
            print(f"Class '{soil_class}' already has {existing_train} train + {existing_test} test genuine images. Skipping.")
            continue
        
        # Query directory listing from GitHub API
        api_url = f"https://api.github.com/repos/Phantom-fs/Soil-Classification-Dataset/contents/Orignal-Dataset/{github_folder}"
        try:
            r = httpx.get(api_url, headers=headers, timeout=15)
            if r.status_code != 200:
                print(f"Error fetching listing for {soil_class}: HTTP {r.status_code}")
                continue
            files_meta = [x for x in r.json() if x["type"] == "file" and x["name"].lower().endswith((".jpg", ".jpeg", ".png"))]
        except Exception as e:
            print(f"Failed to query {soil_class}: {e}")
            continue
            
        print(f"\nProcessing class '{soil_class}' ({len(files_meta)} images available)...")
        
        count = 0
        target_train = 40
        target_test = 10
        total_target = target_train + target_test
        
        for item in files_meta:
            if count >= total_target:
                break
                
            raw_url = item["download_url"]
            try:
                img_res = httpx.get(raw_url, headers=headers, timeout=12, follow_redirects=True)
                if img_res.status_code != 200:
                    continue
                im = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                
                # Check minimum valid dimensions
                if im.size[0] < 50 or im.size[1] < 50:
                    continue
                
                # Determine destination
                if count < target_train:
                    save_path = os.path.join(train_cls_dir, f"real_{soil_class}_{count:03d}.jpg")
                else:
                    test_idx = count - target_train
                    save_path = os.path.join(test_cls_dir, f"test_{soil_class}_{test_idx:03d}.jpg")
                    
                im.save(save_path, "JPEG", quality=92)
                count += 1
                if count % 10 == 0:
                    print(f"  Downloaded {count}/{total_target} for {soil_class}")
            except Exception as ex:
                continue
                
        print(f"  [OK] Completed {soil_class}: {count} genuine images saved.")


def create_non_soil_images():
    print("\n" + "=" * 60)
    print("  Generating Test Non-Soil Images (out-of-domain evaluation)")
    print("=" * 60)
    os.makedirs(NON_SOIL_DIR, exist_ok=True)
    
    # 1. Vibrant Green Leaves / Foliage
    im_green = Image.new("RGB", (224, 224), (20, 180, 45))
    draw = ImageDraw.Draw(im_green)
    draw.polygon([(20, 20), (200, 100), (50, 200)], fill=(10, 220, 60))
    im_green.save(os.path.join(NON_SOIL_DIR, "non_soil_foliage_green.jpg"), "JPEG")
    
    # 2. Deep Blue Sky / Ocean
    im_blue = Image.new("RGB", (224, 224), (30, 120, 240))
    draw = ImageDraw.Draw(im_blue)
    draw.ellipse([40, 40, 180, 180], fill=(70, 160, 255))
    im_blue.save(os.path.join(NON_SOIL_DIR, "non_soil_blue_sky.jpg"), "JPEG")
    
    # 3. Bright Solid Red Graphic (Not soil)
    im_solid = Image.new("RGB", (224, 224), (250, 10, 15))
    im_solid.save(os.path.join(NON_SOIL_DIR, "non_soil_solid_red_graphic.jpg"), "JPEG")
    
    # 4. White page with black text lines
    im_doc = Image.new("RGB", (224, 224), (245, 245, 245))
    draw = ImageDraw.Draw(im_doc)
    for y in range(30, 200, 20):
        draw.line([(25, y), (195, y)], fill=(30, 30, 30), width=3)
    im_doc.save(os.path.join(NON_SOIL_DIR, "non_soil_document_text.jpg"), "JPEG")
    
    # 5. Metallic / Gray grid
    im_metal = Image.new("RGB", (224, 224), (180, 180, 190))
    draw = ImageDraw.Draw(im_metal)
    for i in range(0, 224, 25):
        draw.line([(i, 0), (i, 224)], fill=(120, 120, 130), width=2)
        draw.line([(0, i), (224, i)], fill=(120, 120, 130), width=2)
    im_metal.save(os.path.join(NON_SOIL_DIR, "non_soil_metal_grid.jpg"), "JPEG")
    
    print(f"  [OK] Created 5 distinct non-soil evaluation images in {NON_SOIL_DIR}")

if __name__ == "__main__":
    download_soil_images()
    create_non_soil_images()
    print("\nDataset preparation completed successfully!")
