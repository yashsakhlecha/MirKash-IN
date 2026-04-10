#!/usr/bin/env python3
"""classify_fruits.py – EXPLAINED IN DETAIL
================================================
This script uses **CLIP** (Contrastive Language–Image Pre‑training) in a **zero‑shot** fashion to
sort a bunch of fruit photos into class‑named folders (``apple``, ``mango``, etc.).

🛠  HOW IT WORKS – HIGH LEVEL
----------------------------
1. **Argument parsing** – You specify the *input folder* (messy pile of images),
   *output folder* (where tidy class sub‑folders will be created) and a list of
   *categories* (fruit names).
2. **Model loading** – Pulls the CLIP **ViT‑B/32** model that has been pre‑trained
   on 2 billion image‑caption pairs (LAION‑2B). The heavy lifting is done once
   here and reused for all images.
3. **Text embeddings** – Turns prompts like
   *"a photo of a mango"* into fixed‑length vectors that live in CLIP's joint
   image–text space.
4. **Image loop** – Processes your images in mini‑batches:
      • Load → preprocess (resize / center‑crop / normalise)
      • Embed with CLIP
      • Cosine‑compare each image vector to all text vectors
      • Pick the highest‑scoring class and copy the file into the matching folder
5. **Done** – Open `--output_dir` and you'll see neatly sorted sub‑folders.

WHY ZERO‑SHOT CLIP?
-------------------
Because the model has *already* linked the concept *"a photo of an apple"* to
countless real apple pictures during pre‑training, we can leverage that general
knowledge without custom training. It's a pragmatic balance of **setup speed vs.
accuracy**. For production‑grade precision you'd still fine‑tune on a
labelled fruit dataset (e.g. Fruit‑360).

CLI EXAMPLE
-----------
::
    python classify_fruits.py \
        --input_dir ./input_images \
        --output_dir ./sorted_images \
        --categories apple mango banana orange grape

Dependencies (install once):
::
    pip install open_clip_torch torch pillow tqdm
"""

# ────────────────────────────────────────────────────────────────────────────────
# Standard library
# ────────────────────────────────────────────────────────────────────────────────
import argparse       # handles command‑line flags
import os             # filesystem operations (listdir, path joins, etc.)
import shutil         # used to copy files into their new folders
from typing import List

# ────────────────────────────────────────────────────────────────────────────────
# Third‑party libs
# ────────────────────────────────────────────────────────────────────────────────
import torch                  # PyTorch tensor core + CUDA acceleration
from PIL import Image         # lightweight image IO (reads JPEG/PNG/WebP/…)
from tqdm import tqdm         # pretty progress bars
import open_clip              # OpenCLIP wrapper for CLIP models

# ────────────────────────────────────────────────────────────────────────────────
# 1. Argument parsing helper
# ────────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """Collect CLI arguments and return them as a Namespace."""
    parser = argparse.ArgumentParser(
        description="Sort fruit images into folders using zero‑shot CLIP",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Required flags
    parser.add_argument("--input_dir", required=True,
                        help="Folder that holds the unsorted images")
    parser.add_argument("--output_dir", required=True,
                        help="Destination root – class sub‑folders are created here")
    parser.add_argument(
        "--categories", nargs="+", required=True,
        help="Space‑separated list of fruit classes (e.g. apple mango banana)",
    )

    # Optional flag
    parser.add_argument("--batch_size", type=int, default=32,
                        help="Number of images processed simultaneously")

    return parser.parse_args()

# ────────────────────────────────────────────────────────────────────────────────
# 2. Model and transform loader
# ────────────────────────────────────────────────────────────────────────────────

def load_model(device: torch.device):
    """Load the CLIP **ViT‑B/32** model plus **inference** transform and tokenizer.

    open_clip returns **two** preprocessing pipelines (train / val). We grab the
    *validation* one for deterministic inference.
    """
    # create_model_and_transforms returns: model, preprocess_train, preprocess_val
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k"
    )

    # Text tokenizer must be fetched separately ➜ otherwise our earlier code was
    # passing an *image* transform where a tokenizer was expected, causing the
    # TypeError you hit.
    tokenizer = open_clip.get_tokenizer("ViT-B-32")

    model.to(device)
    model.eval()  # inference‑only mode
    return model, preprocess, tokenizer

# ────────────────────────────────────────────────────────────────────────────────
# 3. Build text feature matrix (one row per class)
# ────────────────────────────────────────────────────────────────────────────────

def build_text_features(categories: List[str], tokenizer, model, device):
    """Create *ℓ2‑normalised* text embeddings for prompts like
    "a photo of a <fruit>". Normalisation lets us later use a simple dot product
    as *cosine similarity*.
    """
    prompts = [f"a photo of a {c}" for c in categories]
    
    # Print the prompts being used
    print("\n📝 Generated prompts for classification:")
    for i, prompt in enumerate(prompts):
        print(f"  {i+1}. {prompt}")
    print()

    with torch.no_grad():  # inference‑only block (saves VRAM & compute)
        text_tokens = tokenizer(prompts).to(device)
        text_features = model.encode_text(text_tokens)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)

    return text_features  # shape: (num_classes, embed_dim)

# ────────────────────────────────────────────────────────────────────────────────
# 4. Ensure output/<class_name> directories exist
# ────────────────────────────────────────────────────────────────────────────────

def ensure_dirs(root: str, classes: List[str]):
    """Create the root output folder and one sub‑folder per class (idempotent)."""
    os.makedirs(root, exist_ok=True)       # safe even if already present
    for cls in classes:
        os.makedirs(os.path.join(root, cls), exist_ok=True)

# ────────────────────────────────────────────────────────────────────────────────
# 5. Main entry point
# ────────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    # Choose CUDA ↔ CPU automatically
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load CLIP + preprocessing + tokenizer → GPU/CPU
    model, preprocess, tokenizer = load_model(device)

    # Pre‑compute text embeddings once – re‑used for every image batch
    text_features = build_text_features(args.categories, tokenizer, model, device)

    # Make sure destination sub‑folders exist
    ensure_dirs(args.output_dir, args.categories)

    # --------------------------------------------------------------------
    # Gather all image file paths (simple glob on common extensions)
    # --------------------------------------------------------------------
    valid_ext = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    img_paths = [
        os.path.join(args.input_dir, f)
        for f in os.listdir(args.input_dir)
        if f.lower().endswith(valid_ext)
    ]

    # --------------------------------------------------------------------
    # Loop over image paths in mini‑batches for speed/GPU utilisation
    # --------------------------------------------------------------------
    for i in tqdm(range(0, len(img_paths), args.batch_size), desc="Classifying"):
        batch_paths = img_paths[i : i + args.batch_size]
        images = []  # holds *pre‑processed* tensors (or None if failed)

        # ~~~~~~~~~~~~~
        # 5a. LOAD STEP
        # ~~~~~~~~~~~~~
        for p in batch_paths:
            try:
                img = Image.open(p).convert("RGB")
                images.append(preprocess(img))  # ⇢ tensor (3×224×224)
            except Exception as e:
                # Corrupt file, unsupported format, etc.
                print(f"[WARN] Skipping {p}: {e}")
                images.append(None)

        # Keep only successfully‑loaded indices to stay in‑sync later
        valid_indices = [idx for idx, im in enumerate(images) if im is not None]
        if not valid_indices:
            continue  # entire batch failed – highly unlikely but safe

        images_tensor = torch.stack([images[idx] for idx in valid_indices]).to(device)

        # ~~~~~~~~~~~~~~~~~~
        # 5b. INFERENCE STEP
        # ~~~~~~~~~~~~~~~~~~
        with torch.no_grad():
            img_features = model.encode_image(images_tensor)
            img_features = img_features / img_features.norm(dim=-1, keepdim=True)

            # Dot product between each image and all class prompts ⇒ similarity
            logits = img_features @ text_features.T  # shape (B, num_classes)
            preds = logits.argmax(dim=-1).cpu().tolist()  # index of max class

        # ~~~~~~~~~~~~~~~~~
        # 5c. SAVE/COPYING
        # ~~~~~~~~~~~~~~~~~
        for local_idx, img_idx in enumerate(valid_indices):
            pred_label = args.categories[preds[local_idx]]  # class name string
            src = batch_paths[img_idx]                      # original file path
            dst = os.path.join(args.output_dir, pred_label,
                               os.path.basename(src))      # target folder
            # Print a description for each image being sorted
            prompt = f"a photo of a {pred_label}"
            print(f"Sorting image: {os.path.basename(src)} | Predicted: {pred_label} | Prompt: '{prompt}'")
            try:
                shutil.copy2(src, dst)  # metadata‑preserving copy
            except Exception as e:
                print(f"[ERR] Failed to copy {src} → {dst}: {e}")

    # All batches processed
    print("\n✔ Done! Classified images are now in:", os.path.abspath(args.output_dir))

# ────────────────────────────────────────────────────────────────────────────────
# 6. Module guard – allows *python classify_fruits.py* to act as script or import
# ────────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
