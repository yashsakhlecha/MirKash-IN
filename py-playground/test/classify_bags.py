#!/usr/bin/env python3
"""
one_shot_sort.py
----------------
Sorts handbag (or any fashion-item) photos into SKU-named sub-folders by
finding the nearest *reference* image in FashionCLIP embedding space.

Folder layout (all paths are relative to where you run the script):

  references/     HB123.jpg, HB456.jpg, …   ← ONE clean image per SKU
  unsorted/       raw images to be filed
  sorted/         will be created automatically:
      ├─ HB123/
      ├─ HB456/
      └─ _check_manually/   ← low-confidence matches land here

Usage:

  1.  pip install torch torchvision transformers pillow tqdm
  2.  python one_shot_sort.py
  3.  Inspect "sorted/", tweak THR if needed, then automate via cron/Task Scheduler.

Tunable parameters
------------------
THR  – similarity margin (0 = strict, 1 = loose).  Start at 0.35.
"""

import shutil
from pathlib import Path
import sys

import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
from tqdm.auto import tqdm

# ────────────────────────────────────────────────────────────────────────────
# 1️⃣  Paths
# ────────────────────────────────────────────────────────────────────────────
REFS   = Path("references")
INBOX  = Path("unsorted")
OUT    = Path("sorted")
UNK    = OUT / "_check_manually"
UNK.mkdir(parents=True, exist_ok=True)

# ────────────────────────────────────────────────────────────────────────────
# 2️⃣  FashionCLIP model
# ────────────────────────────────────────────────────────────────────────────
# Use MPS (Metal Performance Shaders) for M1 Mac GPU acceleration
if torch.backends.mps.is_available():
    device = "mps"
elif torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

MODEL_ID  = "patrickjohncyh/fashion-clip"   # HF repo

print(f"Loading FashionCLIP ({MODEL_ID}) on {device} ...", file=sys.stderr)
processor = CLIPProcessor.from_pretrained(MODEL_ID)
model     = CLIPModel.from_pretrained(MODEL_ID).eval().to(device)
EMB_DIM   = model.config.projection_dim     # 512

@torch.inference_mode()
def embed(img_path: Path) -> torch.Tensor:
    """Return an L2-normalised FashionCLIP embedding for one image."""
    inputs   = processor(images=Image.open(img_path).convert("RGB"),
                         return_tensors="pt")
    features = model.get_image_features(
        **{k: v.to(device) for k, v in inputs.items()}
    )[0]
    return features / features.norm()       # cosine-friendly

# ────────────────────────────────────────────────────────────────────────────
# 3️⃣  Build reference index
# ────────────────────────────────────────────────────────────────────────────
print("Building reference index...", file=sys.stderr)
valid_ext  = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
ref_vecs, skus = [], []

for ref in sorted(REFS.iterdir()):
    if ref.suffix.lower() not in valid_ext or ref.name.startswith("."):
        continue
    try:
        sku = ref.stem.upper()          # "HB123.jpg" → "HB123"
        ref_vecs.append(embed(ref))
        skus.append(sku)
        print(f"  Loaded: {ref.name}  →  {sku}", file=sys.stderr)
    except Exception as exc:
        print(f"  Skipping {ref.name}: {exc}", file=sys.stderr)

if not ref_vecs:
    sys.exit("No valid reference images found! Aborting.")

ref_mat = torch.stack(ref_vecs)          # shape: [N_refs, 512]
print(f"Loaded {len(skus)} reference SKUs.", file=sys.stderr)

# ────────────────────────────────────────────────────────────────────────────
# 4️⃣  Sort incoming images
# ────────────────────────────────────────────────────────────────────────────
THR = 0.5                               # tune on a validation set
print(f"Sorting images in {INBOX} ...", file=sys.stderr)

for img in tqdm(list(INBOX.iterdir()), file=sys.stderr):
    if (not img.is_file()
        or img.suffix.lower() not in valid_ext
        or img.name.startswith(".")):
        continue
    try:
        vec        = embed(img)
        sims       = (ref_mat @ vec).cpu().numpy()   # cosine similarities
        best_idx   = int(sims.argmax())
        best_score = float(sims[best_idx])

        dest_dir = OUT / skus[best_idx] if best_score >= 1 - THR else UNK
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(img, dest_dir / img.name)

        print(f"{img.name:30} → {dest_dir.name:<18} (score={best_score:.3f})")
    except Exception as exc:
        print(f"Error processing {img.name}: {exc}", file=sys.stderr)

print("Sorting complete.") 