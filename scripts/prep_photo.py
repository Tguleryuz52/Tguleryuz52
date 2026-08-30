#!/usr/bin/env python3
"""
High-quality portrait background removal using u2net session and contrast enhancement for ASCII art.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

def main():
    if not os.path.exists(INP):
        print(f"Input file {INP} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {INP}...")
    orig = Image.open(INP).convert("RGB")

    try:
        from rembg import remove, new_session
        print("Removing background with u2net session...")
        session = new_session("u2net")
        cutout = remove(orig, session=session)
    except Exception as e:
        print(f"Rembg u2net session failed: {e}. Falling back to default.")
        from rembg import remove
        cutout = remove(orig)

    # Composite onto pure white background
    white_bg = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(white_bg, cutout)
    
    # Auto-crop based on non-white content
    bbox = cutout.getbbox()
    if bbox:
        comp = comp.crop(bbox)

    # Convert to grayscale
    gray = comp.convert("L")

    # Autocontrast
    gray = ImageOps.autocontrast(gray, cutoff=1)

    # Sharpen features
    gray = gray.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=2))

    # Increase contrast
    enh_c = ImageEnhance.Contrast(gray).enhance(1.4)
    enh_b = ImageEnhance.Brightness(enh_c).enhance(1.02)

    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    enh_b.save(OUT)
    print(f"Saved prepped image to: {OUT}")

if __name__ == "__main__":
    main()
