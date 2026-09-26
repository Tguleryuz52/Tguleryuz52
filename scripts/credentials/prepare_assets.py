#!/usr/bin/env python3
"""
Turn the original certificate scans into build inputs (scripts/credentials/assets/).
The certificates themselves are NOT committed: the README only ever shows the dot
version, so the raw files stay on the author's machine.

    python scripts/credentials/prepare_assets.py "C:/Users/<you>/Documents"
"""
import os
import sys

import numpy as np
from PIL import Image, ImageEnhance

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def flat(path):
    im = Image.open(path)
    bg = Image.new("RGB", im.size, "white")
    bg.paste(im, mask=im.split()[3] if im.mode == "RGBA" else None)
    return bg


def fit(im, w=1400):
    return im.resize((w, round(w * im.height / im.width)), Image.LANCZOS) if im.width > w else im


def paint_out(im, circles, r=25):
    """Harmonic fill of small circles (e.g. gallery arrows), seeded from a ring around each."""
    t = np.asarray(im).astype(np.float32)
    h, w, _ = t.shape
    yy, xx = np.mgrid[0:h, 0:w]
    for cx, cy in circles:
        d2 = (xx - cx) ** 2 + (yy - cy) ** 2
        m = d2 <= r ** 2
        t[m] = t[(d2 > (r + 2) ** 2) & (d2 <= (r + 9) ** 2)].mean(0)
        for _ in range(3000):
            avg = (np.roll(t, 1, 0) + np.roll(t, -1, 0) + np.roll(t, 1, 1) + np.roll(t, -1, 1)) / 4
            t[m] = avg[m]
    return Image.fromarray(np.clip(t, 0, 255).astype(np.uint8))


def white_balance(im):
    a = np.asarray(im).astype(np.float32)
    a = np.clip(a * (244.0 / np.median(a.reshape(-1, 3), axis=0)), 0, 255)
    im = ImageEnhance.Contrast(Image.fromarray(a.astype(np.uint8))).enhance(1.12)
    return ImageEnhance.Sharpness(im).enhance(1.3)


def main(src):
    os.makedirs(OUT, exist_ok=True)
    fit(flat(os.path.join(src, "MicrosoftSertifika.png"))).save(os.path.join(OUT, "microsoft-cert.jpg"), quality=88)
    tek = paint_out(flat(os.path.join(src, "TekonofestSertifika.png")), [(35, 362), (995, 362)])
    tek.save(os.path.join(OUT, "teknofest-cert.jpg"), quality=88)
    iku = white_balance(flat(os.path.join(src, "okul_sertifika_mühendilik_günü_başarı_belgesi.png")))
    fit(iku).save(os.path.join(OUT, "iku-cert.jpg"), quality=88)
    logo = np.asarray(Image.open(os.path.join(src, "teknofest_logo.jpg")).convert("RGB")).astype(np.int16)
    alpha = (np.linalg.norm(255 - logo, axis=2) > 45).astype(np.uint8) * 255
    Image.fromarray(np.dstack([logo.astype(np.uint8), alpha])).save(os.path.join(OUT, "teknofest-logo.png"))
    print("assets ready in", OUT)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Documents"))
