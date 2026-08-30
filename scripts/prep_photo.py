#!/usr/bin/env python3
"""
Tight crop and high-contrast portrait optimization for ultra-detailed ASCII face.
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
        print(f"Error: {INP} not found", file=sys.stderr)
        sys.exit(1)

    orig = Image.open(INP).convert("RGB")
    W, H = orig.size

    # Focus crop tightly on head, glasses, face, coffee cup (head & shoulders)
    # Coordinates tailored for his portrait:
    crop_box = (
        int(W * 0.15),  # left
        int(H * 0.08),  # top
        int(W * 0.88),  # right
        int(H * 0.78),  # bottom (chest level)
    )
    cropped = orig.crop(crop_box)

    try:
        from rembg import remove, new_session
        session = new_session("u2net")
        cutout = remove(cropped, session=session)
    except Exception as e:
        print(f"rembg error: {e}")
        cutout = cropped.convert("RGBA")

    # Composite onto pure white background
    white_bg = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(white_bg, cutout)

    # Convert to grayscale
    gray = comp.convert("L")

    # Enhance local contrast for facial features (eyes, glasses, jawline, hair)
    gray = ImageOps.autocontrast(gray, cutoff=2)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=2.5, percent=220, threshold=1))

    # Boost contrast & brightness balance
    enh_c = ImageEnhance.Contrast(gray).enhance(1.6)
    enh_b = ImageEnhance.Brightness(enh_c).enhance(1.08)

    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    enh_b.save(OUT)
    print(f"Saved optimized face-focused prepped image to {OUT}")

if __name__ == "__main__":
    main()
