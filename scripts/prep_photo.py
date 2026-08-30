#!/usr/bin/env python3
"""
Prepare a portrait photo for clean ASCII conversion using Pillow & NumPy.
Performs contrast optimization, edge sharpening, and adaptive background washout.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "github-profile-setup-source-photo.jpg.jpeg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

def main():
    if not os.path.exists(INP):
        print(f"Error: input photo {INP} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Processing photo {INP}...")
    orig = Image.open(INP).convert("RGB")

    # Crop to focus nicely on the subject / head-and-shoulders if portrait
    w, h = orig.size
    # Center-crop to 4:5 ratio if taller
    target_aspect = 0.85
    cur_aspect = w / h
    if cur_aspect > target_aspect:
        new_w = int(h * target_aspect)
        left = (w - new_w) // 2
        orig = orig.crop((left, 0, left + new_w, h))
    elif cur_aspect < target_aspect:
        new_h = int(w / target_aspect)
        top = int(h * 0.05)
        orig = orig.crop((0, top, w, min(h, top + new_h)))

    # Convert to grayscale
    gray = orig.convert("L")

    # Autocontrast with cutoff
    gray = ImageOps.autocontrast(gray, cutoff=2)

    # Boost local contrast with unsharp mask
    gray = gray.filter(ImageFilter.UnsharpMask(radius=3, percent=160, threshold=3))

    # Enhance brightness & contrast
    enh_c = ImageEnhance.Contrast(gray).enhance(1.35)
    enh_b = ImageEnhance.Brightness(enh_c).enhance(1.05)

    # Gamma adjustment with numpy to push darks into distinct character bands
    arr = np.array(enh_b, dtype=np.float32) / 255.0
    arr = np.power(arr, 1.1)
    arr = (arr * 255.0).astype(np.uint8)

    out_img = Image.fromarray(arr)
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    out_img.save(OUT)
    print(f"Saved prepped image to: {OUT}")

if __name__ == "__main__":
    main()
