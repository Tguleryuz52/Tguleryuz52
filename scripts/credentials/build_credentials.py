#!/usr/bin/env python3
"""
CREDENTIALS.LOG panel -> credentials-dark.svg / credentials-light.svg (committed, static).

Three cards side by side, same particle language as the hero portrait. Each loops:
  logo (travellers in the logo's real colours)
  -> travellers fly onto the certificate (optimal-transport matched, colours shift)
  -> the certificate shimmers in as a dense Floyd-Steinberg dot field in its own
     colours (lightness clamped per theme so the text stays readable), a scan light
     sweeps across it
  -> dots dissolve, travellers fly back to the logo.
No raster of the certificate is embedded: everything is dots.

    python scripts/credentials/build_credentials.py
"""
import base64
import colorsys
import html
import io
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.cluster.vq import kmeans2
from scipy.optimize import linear_sum_assignment

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "profile"))
from common import MONO, THEMES  # noqa: E402

A = lambda name: os.path.join(HERE, "assets", name)  # noqa: E731

MS_LOGO = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 21 21">'
           '<rect width="10" height="10" fill="#F25022"/><rect x="11" width="10" height="10" fill="#7FBA00"/>'
           '<rect y="11" width="10" height="10" fill="#00A4EF"/><rect x="11" y="11" width="10" height="10" fill="#FFB900"/></svg>')
CAP_LOGO = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path d="M6 10.6v4.6c0 1.8 2.7 3.3 6 3.3s6-1.5 6-3.3v-4.6L12 13.3Z" fill="#BE123C"/>'
            '<path d="M12 3 23 8 12 13 1 8Z" fill="#F43F5E"/>'
            '<rect x="20.3" y="8.3" width="1.3" height="6.6" fill="#FBBF24"/><circle cx="20.95" cy="15.5" r="1.5" fill="#FBBF24"/></svg>')

CARDS = [
    dict(key="microsoft", head="credentials/microsoft", title="Microsoft · AI Innovators",
         sub="Internship Program · Summer 2026", date="AUG 2026", logo=MS_LOGO, cert="microsoft-cert.jpg",
         palette=["#F25022", "#7FBA00", "#00A4EF", "#FFB900"]),
    dict(key="teknofest", head="credentials/teknofest", title="TEKNOFEST Finalist",
         sub="Tourism Technologies Competition", date="2024", logo=A("teknofest-logo.png"), cert="teknofest-cert.jpg"),
    dict(key="iku", head="credentials/iku", title="İKÜ Certificate of Achievement",
         sub="Faculty of Engineering · Oct 2024", date="OCT 2024", logo=CAP_LOGO, cert="iku-cert.jpg"),
]

W, MARGIN, GAP = 1180, 5, 15
CW, CH = 380, 352
BX, BY, BW, BH = 14, 42, CW - 28, 248          # visual box inside a card
LOGO_MAX = 150                                  # px
N = 400                                         # travellers per card
DOT = 2.6
PITCH = 1.3                                     # certificate dot grid (px)
N_SHIMMER = 6                                   # random groups for the dot field fade
N_COLORS = 7
INK_FLOOR = 0.14
T = 14.0
DELAY = [0.0, 1.2, 2.4]
KT = "0;.2;.3;.8;.9;1"                          # logo, depart, on cert, depart, logo, loop
SPL = ";".join(["0 0 1 1", ".45 0 .25 1", "0 0 1 1", ".45 0 .25 1", "0 0 1 1"])
RNG = np.random.default_rng(7)


# ---------------------------------------------------------------- sampling
def rgba_logo(src, px):
    if src.lstrip().startswith("<svg"):
        import resvg_py
        png = resvg_py.svg_to_bytes(svg_string=src, width=px, height=px)
        im = Image.open(io.BytesIO(bytes(png))).convert("RGBA")
    else:
        im = Image.open(src).convert("RGBA")
    im = im.crop(im.getbbox())
    s = px / max(im.size)
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)


def cvt(xy, w, n):
    pick = xy[RNG.choice(len(xy), 14000, replace=True, p=w / w.sum())] + RNG.uniform(-.4, .4, (14000, 2))
    cent, _ = kmeans2(pick, n, minit="points", iter=14, seed=RNG)
    return cent


def logo_particles(src):
    im = rgba_logo(src, LOGO_MAX * 2)
    a = np.asarray(im)
    mask = a[:, :, 3] > 110
    ys, xs = np.nonzero(mask)
    depth = ndi.distance_transform_edt(mask)[ys, xs]
    pts = cvt(np.stack([xs, ys], 1).astype(float), 1.0 + 2.0 * np.exp(-depth / 5.0), N)
    iy = np.clip(pts[:, 1].round().astype(int), 0, a.shape[0] - 1)
    ix = np.clip(pts[:, 0].round().astype(int), 0, a.shape[1] - 1)
    pts = pts / 2.0
    off = np.array([BX + BW / 2, BY + BH / 2]) - (pts.min(0) + pts.max(0)) / 2
    return pts + off, a[iy, ix, :3].astype(float)


def dither(v):
    """1-bit Floyd-Steinberg, serpentine (same as the hero portrait)."""
    a = v.astype(np.float32).copy()
    h, w = a.shape
    out = np.zeros((h, w), bool)
    for y in range(h):
        fwd = y % 2 == 0
        d = 1 if fwd else -1
        row, nxt = a[y], a[y + 1] if y + 1 < h else None
        for x in (range(w) if fwd else range(w - 1, -1, -1)):
            old = row[x]
            new = 1.0 if old >= 0.5 else 0.0
            out[y, x] = new > 0
            e = old - new
            if 0 <= x + d < w:
                row[x + d] += e * 7 / 16
            if nxt is not None:
                if 0 <= x - d < w:
                    nxt[x - d] += e * 3 / 16
                nxt[x] += e * 5 / 16
                if 0 <= x + d < w:
                    nxt[x + d] += e / 16
    return out


def cert_field(name):
    """Dot field of the certificate: where the 'ink' is (distance from the paper colour)."""
    im = Image.open(A(name)).convert("RGB")
    s = min(BW / im.width, BH / im.height)
    w, h = round(im.width * s), round(im.height * s)
    gw, gh = round(w / PITCH), round(h / PITCH)
    g = np.asarray(im.resize((gw, gh), Image.LANCZOS)).astype(float)
    paper = np.median(g.reshape(-1, 3), axis=0)
    ink = np.linalg.norm(g - paper, axis=2)
    ink = np.clip(ink / np.percentile(ink, 99), 0, 1)
    ink = np.clip((ink - INK_FLOOR) / (1 - INK_FLOOR), 0, 1) ** 0.85   # paper texture -> no dots
    dots = dither(ink)
    ys, xs = np.nonzero(dots)
    cols = g[ys, xs]
    pal, lab = kmeans2(cols, N_COLORS, minit="++", iter=30, seed=RNG)
    origin = (BX + (BW - w) / 2, BY + (BH - h) / 2)
    sx, sy = w / gw, h / gh
    return dict(xs=xs, ys=ys, lab=lab, pal=pal, origin=origin, scale=(sx, sy), box=(*origin, w, h), shape=(gh, gw))


# ---------------------------------------------------------------- colour
def hexc(c):
    return "#%02X%02X%02X" % tuple(int(max(0, min(255, v))) for v in c)


def for_theme(rgb, th):
    """Keep the certificate's hue, clamp lightness so it reads on the card."""
    h, l, s = colorsys.rgb_to_hls(*(np.asarray(rgb) / 255.0))
    l = max(l, 0.64) if th == "dark" else min(l, 0.42)
    return np.array(colorsys.hls_to_rgb(h, l, min(1.0, s * 1.1))) * 255


def quantize(cols, k, palette=None):
    if palette:
        cent = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in palette], float)
        return cent, np.argmin(((cols[:, None] - cent[None]) ** 2).sum(-1), 1)
    return kmeans2(cols, k, minit="++", iter=30, seed=RNG)


# ---------------------------------------------------------------- svg
def png_uri(rgba):
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def runs_path(mask):
    """Horizontal runs as stroked 1-unit lines with relative moves (grid units)."""
    parts, cx, cy = [], None, None
    for y in range(mask.shape[0]):
        row = np.concatenate([[0], mask[y].astype(np.int8), [0]])
        d = np.diff(row)
        for s, e in zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]):
            n = e - s
            if cx is None:
                parts.append(f"M{s} {y}.5h{n}")
            else:
                dy = y - cy
                parts.append(f"m{s - cx}{'' if dy < 0 else ' '}{dy}h{n}")
            cx, cy = s + n, y
    return "".join(parts)


def prepare():
    out = []
    for c in CARDS:
        lp, lc = logo_particles(c["logo"])
        f = cert_field(c["cert"])
        pick = RNG.choice(len(f["xs"]), N, replace=False)
        ox, oy = f["origin"]
        sx, sy = f["scale"]
        cp = np.stack([ox + (f["xs"][pick] + .5) * sx, oy + (f["ys"][pick] + .5) * sy], 1)
        clab = f["lab"][pick]
        _, col = linear_sum_assignment(((lp[:, None, :] - cp[None, :, :]) ** 2).sum(-1))
        cp, clab = cp[col], clab[col]
        lpal, llab = quantize(lc, 8, c.get("palette"))
        out.append(dict(c, lp=lp, lpal=lpal, llab=llab, cp=cp, clab=clab, field=f,
                        group=RNG.integers(0, N_SHIMMER, len(f["xs"]))))
    return out


def card_svg(d, i, x, th):
    c = THEMES[th]
    f = d["field"]
    rep = f'dur="{T}s" begin="{DELAY[i]}s" repeatCount="indefinite"'
    bx, by, bw, bh = f["box"]
    pal = [hexc(for_theme(p, th)) for p in f["pal"]]
    pid = f"{th[0]}{i}"
    o = [f'<g transform="translate({x},42)">',
         f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".6s" begin="{.2 + i * .15:.2f}s" fill="freeze"/>',
         f'<rect width="{CW}" height="{CH}" rx="12" fill="{c["PANEL"]}" stroke="{c["STROKE_LO"]}">'
         f'<animate attributeName="stroke" values="{c["STROKE_LO"]};{c["STROKE_HI"]};{c["STROKE_LO"]}" dur="4.5s" '
         f'begin="{i * .7:.1f}s" repeatCount="indefinite"/></rect>',
         f'<path d="M0 30V12A12 12 0 0 1 12 0H{CW - 12}A12 12 0 0 1 {CW} 12V30Z" fill="{c["PANEL_BAR"]}"/>',
         f'<line x1="0" y1="30" x2="{CW}" y2="30" stroke="{c["BARLINE"]}"/>',
         f'<text x="16" y="19" font-size="10" fill="{c["MUTED"]}"><tspan fill="{c["CYAN"]}">&#8226;</tspan> {html.escape(d["head"])}</text>',
         f'<circle cx="{CW - 16}" cy="15" r="3.5" fill="{c["EMERALD"]}"><animate attributeName="opacity" values="1;.25;1" dur="1.8s" repeatCount="indefinite"/></circle>',
         f'<rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" rx="8" fill="{c["BG"]}" opacity=".55"/>']

    # dense certificate dot field, one pixel per dot, scaled up with pixelated sampling:
    # looks identical to vector dots but costs one bitmap draw per layer per frame
    # (31k vector runs repainted every frame made the page stutter).
    gh, gw = f["shape"]
    rgb = np.array([[int(h[j:j + 2], 16) for j in (1, 3, 5)] for h in pal], np.uint8)
    for g in range(N_SHIMMER):
        a_in = .30 + g * (.07 / N_SHIMMER)
        a_out = .71 + g * (.06 / N_SHIMMER)
        sel = d["group"] == g
        layer = np.zeros((gh, gw, 4), np.uint8)
        layer[f["ys"][sel], f["xs"][sel], :3] = rgb[f["lab"][sel]]
        layer[f["ys"][sel], f["xs"][sel], 3] = 255
        o.append(f'<image x="{bx:.2f}" y="{by:.2f}" width="{bw}" height="{bh}" preserveAspectRatio="none" '
                 f'style="image-rendering:pixelated" opacity="0" href="{png_uri(layer)}">'
                 f'<animate attributeName="opacity" values="0;0;1;1;0;0" '
                 f'keyTimes="0;{a_in:.3f};{a_in + .03:.3f};{a_out:.3f};{a_out + .03:.3f};1" {rep}/></image>')

    # travellers: logo colours -> certificate colours via shared animated swatches
    pairs = sorted(set(zip(d["llab"].tolist(), d["clab"].tolist())))
    o.append("<defs>")
    for a, b in pairs:
        la, cb = hexc(d["lpal"][a]), pal[b]
        o.append(f'<rect id="p{pid}_{a}_{b}" x="{-DOT / 2}" y="{-DOT / 2}" width="{DOT}" height="{DOT}" rx=".6" fill="{la}">'
                 f'<animate attributeName="fill" values="{la};{la};{cb};{cb};{la};{la}" keyTimes="{KT}" calcMode="spline" '
                 f'keySplines="{SPL}" {rep}/></rect>')
    o.append("</defs>")
    o.append(f'<g><animate attributeName="opacity" values="1;1;0;0;1;1" keyTimes="0;.31;.38;.72;.79;1" {rep}/>')
    for k in range(N):
        (lx, ly), (cx, cy) = d["lp"][k], d["cp"][k]
        L, C = f"{lx:.0f} {ly:.0f}", f"{cx:.1f} {cy:.1f}"
        o.append(f'<use href="#p{pid}_{d["llab"][k]}_{d["clab"][k]}" transform="translate({L})">'
                 f'<animateTransform attributeName="transform" type="translate" values="{L};{L};{C};{C};{L};{L}" '
                 f'keyTimes="{KT}" calcMode="spline" keySplines="{SPL}" {rep}/></use>')
    o.append("</g>")

    # scan light + date pill while the certificate is up
    clip = f"cc{pid}"
    o.append(f'<defs><clipPath id="{clip}"><rect x="{bx:.1f}" y="{by:.1f}" width="{bw}" height="{bh}"/></clipPath>'
             f'<linearGradient id="sw{pid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{c["CYAN"]}" stop-opacity="0"/>'
             f'<stop offset=".5" stop-color="{c["CYAN"]}" stop-opacity=".30"/><stop offset="1" stop-color="{c["CYAN"]}" stop-opacity="0"/>'
             f'</linearGradient></defs>'
             f'<g clip-path="url(#{clip})"><rect x="{bx - 70:.1f}" y="{by:.1f}" width="70" height="{bh}" fill="url(#sw{pid})" '
             f'transform="skewX(-12)"><animateTransform attributeName="transform" type="translate" '
             f'values="0 0;0 0;{bw + 140} 0;{bw + 140} 0" keyTimes="0;.38;.49;1" {rep} additive="sum"/></rect></g>')
    pill_w = len(d["date"]) * 6.4 + 34
    px = bx + bw - pill_w - 4
    o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;.34;.40;.72;.78;1" {rep}/>'
             f'<rect x="{px:.1f}" y="{by + 4:.1f}" width="{pill_w:.1f}" height="18" rx="9" fill="#0A101F" fill-opacity=".85" stroke="{c["EMERALD"]}"/>'
             f'<text x="{px + 10:.1f}" y="{by + 17:.1f}" font-size="10" font-weight="700" fill="#34D399">&#10003; {html.escape(d["date"])}</text></g>')
    o.append(f'<text x="{CW / 2}" y="{CH - 32}" text-anchor="middle" font-size="14" font-weight="700" fill="{c["TEXT"]}">{html.escape(d["title"])}</text>'
             f'<text x="{CW / 2}" y="{CH - 13}" text-anchor="middle" font-size="10.5" fill="{c["MUTED"]}">{html.escape(d["sub"])}</text>')
    o.append("</g></g>")
    return "".join(o)


def build(cards, th):
    c = THEMES[th]
    H = 42 + CH + MARGIN
    g = f"acc_{th}"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="{MONO}" role="img" aria-label="Certificates: Microsoft AI Innovators, TEKNOFEST finalist, IKU certificate of achievement">',
         f'<rect width="{W}" height="{H}" fill="{c["BG"]}"/>',
         f'<defs><linearGradient id="{g}" x1="0" y1="0" x2="1" y2="0">'
         f'<stop offset="0" stop-color="{c["VIOLET2"]}"><animate attributeName="stop-color" '
         f'values="{c["VIOLET2"]};{c["CYAN"]};{c["EMERALD"]};{c["VIOLET2"]}" dur="10s" repeatCount="indefinite"/></stop>'
         f'<stop offset="1" stop-color="{c["EMERALD"]}"><animate attributeName="stop-color" '
         f'values="{c["EMERALD"]};{c["VIOLET2"]};{c["CYAN"]};{c["EMERALD"]}" dur="10s" repeatCount="indefinite"/></stop>'
         f'</linearGradient></defs>',
         f'<text x="{MARGIN + 2}" y="18" font-size="11" letter-spacing="2" fill="{c["CYAN"]}">CREDENTIALS.LOG</text>',
         f'<text x="{MARGIN + 148}" y="18" font-size="10" fill="{c["DIM"]}">./certs.sh --verify</text>',
         f'<line x1="{MARGIN}" y1="28" x2="{W - MARGIN}" y2="28" stroke="url(#{g})" stroke-width="1.5" opacity=".7"/>']
    for i, d in enumerate(cards):
        o.append(card_svg(d, i, MARGIN + i * (CW + GAP), th))
    o.append("</svg>")
    return "\n".join(o)


def main():
    cards = prepare()
    for th in ("dark", "light"):
        svg = build(cards, th)
        with open(os.path.join(ROOT, f"credentials-{th}.svg"), "w", encoding="utf-8") as fh:
            fh.write(svg)
        dots = sum(len(d["field"]["xs"]) for d in cards)
        print(f"credentials-{th}.svg  {len(svg.encode()) / 1024:.0f} KB  ({dots} certificate dots)")


if __name__ == "__main__":
    main()
