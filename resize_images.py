#!/usr/bin/env python3
"""
Ecom Image Resizer
Resizes images to 1000x1500px (portrait) with center-zoom crop.
Saves to 'resized/' subfolder. Originals untouched.

Usage:
    python resize_images.py /path/to/folder
    python resize_images.py  (uses current directory)
"""

import sys
import os
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

TARGET_W = 1000
TARGET_H = 1500
TARGET_RATIO = TARGET_W / TARGET_H  # 0.6667

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"}


def resize_crop_center(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Scale to cover target, then center crop."""
    src_w, src_h = img.size
    src_ratio = src_w / src_h

    if src_ratio > TARGET_RATIO:
        # Image wider than target → fit height, crop width
        scale = target_h / src_h
    else:
        # Image taller than target → fit width, crop height
        scale = target_w / src_w

    new_w = round(src_w * scale)
    new_h = round(src_h * scale)

    img = img.resize((new_w, new_h), Image.LANCZOS)

    # Center crop
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    right = left + target_w
    bottom = top + target_h

    return img.crop((left, top, right, bottom))


def process_folder(folder: Path):
    out_dir = folder / "resized"
    out_dir.mkdir(exist_ok=True)

    images = [f for f in folder.iterdir() if f.suffix.lower() in SUPPORTED]

    if not images:
        print(f"No images found in {folder}")
        return

    print(f"Found {len(images)} image(s) → saving to {out_dir}\n")

    ok, fail = 0, 0
    for img_path in sorted(images):
        try:
            with Image.open(img_path) as img:
                # Convert to RGB (handles RGBA/P mode PNGs etc.)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                result = resize_crop_center(img, TARGET_W, TARGET_H)

                # Preserve original format where possible
                ext = img_path.suffix.lower()
                out_name = img_path.stem + ext
                out_path = out_dir / out_name

                save_kwargs = {}
                if ext in (".jpg", ".jpeg"):
                    save_kwargs = {"quality": 90, "optimize": True}
                elif ext == ".png":
                    save_kwargs = {"optimize": True}

                result.save(out_path, **save_kwargs)
                print(f"  ✓ {img_path.name}  →  {result.size}")
                ok += 1

        except Exception as e:
            print(f"  ✗ {img_path.name}  ERROR: {e}")
            fail += 1

    print(f"\nDone. {ok} resized, {fail} failed.")
    print(f"Output: {out_dir}")


if __name__ == "__main__":
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

    if not folder.exists():
        print(f"Folder not found: {folder}")
        sys.exit(1)

    if not folder.is_dir():
        print(f"Not a folder: {folder}")
        sys.exit(1)

    process_folder(folder)
