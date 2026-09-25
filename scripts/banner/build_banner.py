#!/usr/bin/env python3
"""
Hero banner generator -> dark.svg + light.svg (1180x610 terminal window).

Left  (VISUAL.MAP): 1-bit Floyd-Steinberg portrait. Intro shimmers in, then on a
      loop the portrait dissolves into a swarm of travellers that morph through
      tech logos (optimal-transport matched) and fold back into the face.
Right (SYSTEM.INFO): readout rows that slide in one by one.

Two independent layers (see GitHub-Profile-Master-Prompt):
  * portrait  : full-density dots, intro = 60 random groups, loop = drift bands
  * travellers: ~900 dots hidden during the portrait, visible during logos

This script + config below are the source of truth. Never hand-edit the SVGs.

    python scripts/banner/build_banner.py                 # uses defaults below
    python scripts/banner/build_banner.py --photo new.jpg # new photo (flat bg)
"""
import argparse
import html
import os
import sys

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from scipy import ndimage as ndi
from scipy.cluster.vq import kmeans2
from scipy.optimize import linear_sum_assignment

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))

# ---------------------------------------------------------------- profile
HANDLE_MAIL = "guleryuztalha52@gmail.com"
ROWS = [
    ("Subject", "Talha Güleryüz"),
    ("Role", "Software Developer"),
    ("Education", "Software Engineering, IKU"),
    ("Focus", "AI Agents · Full-Stack · CRM Automation"),
    ("Awards", "TEKNOFEST Top 14 · ANTSPARK 3rd · TÜBİTAK"),
    None,
    ("Core.Lang", "TypeScript, Python, C++"),
    ("Core.Frontend", "Next.js 16, React 19, Tailwind v4"),
    ("Core.Backend", "Node.js, FastAPI, Supabase"),
    ("Core.AI", "Claude API, Gemini, Multi-Agent, RAG"),
    ("Core.Data", "Zoho CRM, Sanity CMS, PostgreSQL"),
    ("Core.Infra", "Vercel, GitHub Actions, CI/CD"),
    "Contact",
    ("Grid.Mail", HANDLE_MAIL),
    ("Grid.Portfolio", "talhaguleryuz.framer.website"),
    ("Grid.LinkedIn", "in/talha-güleryüz"),
    ("Grid.GitHub", "@Tguleryuz52"),
    ("Grid.Behance", "talhagleryz"),
]
LOGOS = ["nextdotjs", "react", "python", "claude", "cplusplus", "nodedotjs", "vercel"]
INVERT = {"nextdotjs", "cplusplus"}   # badge logos: draw rim + letters instead of the solid badge

# ---------------------------------------------------------------- photo
PHOTO = os.path.join(ROOT, "source-photo.jpg")
MASK = os.path.join(HERE, "portrait-mask.png")   # optional; white = subject
CROP = (610, 250, 1225)      # (center x, top y, bottom y) in photo pixels
CONTRAST = 1.3
TONE = {"dark": (0.62, 70), "light": (0.62, 45)}   # (gamma, local-contrast %); gamma<1 lifts mids

# ---------------------------------------------------------------- geometry
W, H = 1180, 610
FRAME = (36, 84, 400, 492)            # VISUAL.MAP box
GW, GH = 300, 340                     # dither grid
OX, OY = 50, 86                       # grid origin (px)
SX, SY = 1.24, 490 / 340              # grid -> px
LOGO_BOX = 270                        # max logo size (px)
N_TRAVEL = 900
N_INTRO, N_BANDS = 60, 94

# ---------------------------------------------------------------- timing
INTRO_END = 3.2
T_PORTRAIT, T_LOGO, T_MOVE = 3.0, 2.0, 1.3
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

THEMES = {
    "dark": dict(
        OUTER="#070B16", PANEL0="#0A101F", PANEL1="#0C1426", BAR="#0B1222",
        HAIR="rgba(255,255,255,0.10)", TITLE="#94A3B8", LABEL_DIM="#475569",
        GLOW="#22D3EE", FRAME_BG="#0A101F", FRAME_STROKE="rgba(34,211,238,0.35)",
        INK="#A78BFA", HEAD="#22D3EE", LIVE="#F87171", PILL="#4C1D95",
        PILL_TX="#E9D5FF", KEY="#22D3EE", LEAD="rgba(148,163,184,0.35)",
        VAL="#F8FAFC", MUTED="#94A3B8", ACC=("#7C3AED", "#22D3EE", "#10B981"),
    ),
    "light": dict(
        OUTER="#FFFFFF", PANEL0="#F8FAFC", PANEL1="#EEF2F7", BAR="#F1F5F9",
        HAIR="rgba(15,23,42,0.10)", TITLE="#475569", LABEL_DIM="#94A3B8",
        GLOW="#06B6D4", FRAME_BG="#F8FAFC", FRAME_STROKE="rgba(8,145,178,0.40)",
        INK="#7C3AED", HEAD="#0891B2", LIVE="#DC2626", PILL="#DBEAFE",
        PILL_TX="#1D4ED8", KEY="#0891B2", LEAD="rgba(15,23,42,0.25)",
        VAL="#0F172A", MUTED="#475569", ACC=("#2563EB", "#06B6D4", "#10B981"),
    ),
}

RNG = np.random.default_rng(52)


# ================================================================ portrait
def segment(img):
    """Flat-background segmentation: colour distance from the border colour."""
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bg = np.median(border, axis=0)
    dist = np.linalg.norm(a - bg, axis=2)
    m = dist > max(28.0, np.percentile(dist, 35))
    return clean_mask(m)


def clean_mask(m):
    m = ndi.binary_closing(m, iterations=4)
    m = ndi.binary_fill_holes(m)
    lab, n = ndi.label(m)
    if n > 1:
        sizes = ndi.sum(m, lab, range(1, n + 1))
        m = lab == (1 + int(np.argmax(sizes)))
    return m


def load_portrait(photo, mask_path):
    img = Image.open(photo).convert("RGB")
    if mask_path and os.path.exists(mask_path):
        mask = np.asarray(Image.open(mask_path).convert("L")) > 127
        mask = clean_mask(mask)
    else:
        mask = segment(img)

    cx, top, bottom = CROP
    ch = bottom - top
    cw = round(ch * (GW * SX) / (GH * SY))
    box = (cx - cw // 2, top, cx - cw // 2 + cw, bottom)
    gray = img.convert("L").crop(box).resize((GW, GH), Image.LANCZOS)
    m = Image.fromarray(mask.astype(np.uint8) * 255).crop(box).resize((GW, GH), Image.LANCZOS)
    m = np.asarray(m) > 127

    gray = ImageEnhance.Contrast(gray).enhance(CONTRAST)
    lum = np.asarray(gray, dtype=np.float32) / 255.0
    lo, hi = np.percentile(lum[m], [1, 99])          # autocontrast(cutoff=1) on subject only
    lum = np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1)
    return lum, m


def tone(lum, gamma, local):
    img = Image.fromarray((lum ** gamma * 255).astype(np.uint8))
    if local:   # large-radius unsharp = local contrast: face detail vs. bright shirt
        img = img.filter(ImageFilter.UnsharpMask(radius=24, percent=local, threshold=0))
    img = img.filter(ImageFilter.UnsharpMask(radius=3, percent=140, threshold=0))
    return np.asarray(img, dtype=np.float32) / 255.0


def dither(v):
    """1-bit Floyd-Steinberg, serpentine scan."""
    a = v.astype(np.float32).copy()
    h, w = a.shape
    out = np.zeros((h, w), bool)
    for y in range(h):
        rng = range(w) if y % 2 == 0 else range(w - 1, -1, -1)
        d = 1 if y % 2 == 0 else -1
        row, nxt = a[y], a[y + 1] if y + 1 < h else None
        for x in rng:
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
                    nxt[x + d] += e * 1 / 16
    return out


def portrait_dots(theme):
    lum, m = load_portrait(PHOTO, MASK)
    gamma, local = TONE[theme]
    lum = tone(lum, gamma, local)
    v = lum if theme == "dark" else 1.0 - lum     # dark: lit subject; light: ink the shadows
    v = np.where(m, v, 0.0)
    dots = dither(v)
    dots &= ndi.binary_erosion(m, iterations=1)   # hard-clear diffusion bleed at the edge
    return dots


def runs_of(dots):
    """Horizontal runs -> array of (y, x, n)."""
    out = []
    for y in range(dots.shape[0]):
        row = np.concatenate([[0], dots[y].astype(np.int8), [0]])
        d = np.diff(row)
        for s, e in zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]):
            out.append((y, s, e - s))
    return np.array(out, dtype=np.int32)


def path_d(runs):
    """Stroked 1-unit lines with relative moves (≈45% smaller than rect paths)."""
    runs = runs[np.lexsort((runs[:, 1], runs[:, 0]))]
    parts, cx, cy = [], None, None
    for y, x, n in runs:
        if cx is None:
            parts.append(f"M{x} {y}.5h{n}")
        else:
            dy = y - cy
            parts.append(f"m{x - cx}{'' if dy < 0 else ' '}{dy}h{n}")
        cx, cy = x + n, y
    return "".join(parts)


# ================================================================ logos
def invert_logo(a):
    """Badge logos (solid disc/hexagon with letters cut out) read poorly as dots:
    the letters are negative space. Swap to rim + solid letters."""
    from PIL import ImageDraw
    from scipy.spatial import ConvexHull
    ys, xs = np.nonzero(a)
    pts = np.stack([xs, ys], 1)
    hull_pts = pts[ConvexHull(pts).vertices]
    hull_img = Image.new("L", (a.shape[1], a.shape[0]), 0)
    ImageDraw.Draw(hull_img).polygon([tuple(p) for p in hull_pts], fill=255)
    hull = np.asarray(hull_img) > 127
    rim = hull & ~ndi.binary_erosion(hull, iterations=max(4, a.shape[0] // 40))
    letters = ndi.binary_erosion(hull, iterations=2) & ~a
    return rim | letters


def logo_points(name, n):
    import resvg_py
    svg = open(os.path.join(HERE, "logos", f"{name}.svg"), encoding="utf-8").read()
    size = LOGO_BOX * 2
    png = resvg_py.svg_to_bytes(svg_string=svg, width=size, height=size)
    from io import BytesIO
    a = np.asarray(Image.open(BytesIO(png)).convert("RGBA"))[:, :, 3] > 100
    if name in INVERT:
        a = invert_logo(a)
    ys, xs = np.nonzero(a)
    pts = np.stack([xs, ys], 1).astype(np.float64) / 2.0          # -> px in LOGO_BOX space
    # edge-weighted sampling: small cut-outs (the N, C++'s "++") keep a crisp rim
    depth = ndi.distance_transform_edt(a)[ys, xs]
    w = 1.0 + 3.0 * np.exp(-depth / 6.0)
    pts = pts[RNG.choice(len(pts), 12000, replace=True, p=w / w.sum())] + RNG.uniform(-.25, .25, (12000, 2))
    cent, _ = kmeans2(pts, n, minit="points", iter=15, seed=RNG)  # even stipple (CVT)
    cent += RNG.normal(0, 0.6, cent.shape)                       # break the lattice
    # centre in the frame, then px -> grid units
    fx, fy, fw, fh = FRAME
    span = cent.max(0) - cent.min(0)
    off = np.array([fx + fw / 2, fy + fh / 2]) - (cent.min(0) + span / 2)
    px = cent + off
    return np.stack([(px[:, 0] - OX) / SX, (px[:, 1] - OY) / SY], 1)


def keytimes():
    t = [0.0, T_PORTRAIT]
    for _ in LOGOS:
        t += [t[-1] + T_MOVE, t[-1] + T_MOVE + T_LOGO]
    total = t[-1] + T_MOVE
    return [x / total for x in t] + [1.0], total


# ================================================================ svg parts
def f(x):
    return f"{x:.3f}".rstrip("0").rstrip(".") if x else "0"


def build_visual(theme, dots, shapes):
    c = THEMES[theme]
    kt, total = keytimes()
    k1, k2, k_last = kt[1], kt[2], kt[-2]
    rep = f'dur="{total:.1f}s" begin="{INTRO_END}s" repeatCount="indefinite"'
    ease = ".45 0 .25 1"
    out = []
    g_open = f'<g transform="translate({OX},{OY}) scale({SX},{SY:.4f})"'
    ink = f'stroke="{c["INK"]}" stroke-width="1" fill="none" shape-rendering="crispEdges"'
    ys, xs = np.nonzero(dots)

    def group_path(labels, g):
        """Runs of the dots carrying label g (labels are per dot, never per run:
        grouping whole runs shows up as horizontal scanlines while fading)."""
        img = np.zeros_like(dots)
        sel = labels == g
        img[ys[sel], xs[sel]] = True
        return path_d(runs_of(img))

    # --- intro: 60 interleaved random groups (never spatial) shimmer in
    gid = RNG.integers(0, N_INTRO, len(xs))
    out.append(f'{g_open} {ink}>')
    out.append(f'<set attributeName="opacity" to="0" begin="{INTRO_END}s"/>')
    for g in range(N_INTRO):
        b = 0.20 + g * 0.03
        out.append(
            f'<g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.9s" begin="{b:.2f}s" '
            f'fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".4 0 .2 1"/>'
            f'<path d="{group_path(gid, g)}"/></g>')
    out.append("</g>")

    # --- loop layer: drift bands. Drift is linear in position, so add per-dot
    #     noise before clustering or the bands collapse into a square grid.
    target = shapes[0].mean(0)
    drift = 0.42 * (target - np.stack([xs + 0.5, ys + 0.5], 1))
    noisy = drift + RNG.normal(0, 4.0, drift.shape)
    band_c, band = kmeans2(noisy, N_BANDS, minit="points", iter=20, seed=RNG)
    kt5 = f"0;{k1:.3f};{k2:.3f};{k_last:.3f};1"
    spl5 = ";".join(["0 0 1 1", ease, "0 0 1 1", ease])
    out.append(f'{g_open} {ink} opacity="0">')
    out.append(f'<set attributeName="opacity" to="1" begin="{INTRO_END}s"/>')
    for b in range(N_BANDS):
        if not (band == b).any():
            continue
        dx, dy = band_c[b]
        kb = f"0;{k1 + RNG.uniform(0, 0.45) * (k2 - k1):.3f};{k2:.3f};{k_last:.3f};1"   # staggered release
        out.append(
            f'<g><animate attributeName="opacity" values="1;1;0;0;1" keyTimes="{kb}" '
            f'calcMode="spline" keySplines="{spl5}" {rep}/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 0;{dx:.0f} {dy:.0f};{dx:.0f} {dy:.0f};0 0" keyTimes="{kb}" '
            f'calcMode="spline" keySplines="{spl5}" {rep}/>'
            f'<path d="{group_path(band, b)}"/></g>')
    out.append("</g>")

    # --- travellers: start on portrait dots, OT-matched hop by hop
    ys, xs = np.nonzero(dots)
    pick = RNG.choice(len(xs), N_TRAVEL, replace=False)
    home = np.stack([xs[pick], ys[pick]], 1).astype(np.float64)
    chain, cur = [home], home
    for s in shapes:
        cost = ((cur[:, None, :] - s[None, :, :]) ** 2).sum(-1)
        _, col = linear_sum_assignment(cost)
        cur = s[col]
        chain.append(cur)
    kts = ";".join(f"{k:.3f}".rstrip("0").rstrip(".") if 0 < k < 1 else str(int(k)) for k in kt)
    n_seg = len(kt) - 1
    spl = ";".join((["0 0 1 1"] + [ease, "0 0 1 1"] * len(LOGOS) + [ease])[:n_seg])
    trav_op_kt = f"0;{k1:.3f};{k2:.3f};{k_last:.3f};1"
    out.append(f'<defs><rect id="tv{theme}" x="-1.2" y="-.85" width="2.4" height="1.7" fill="{c["INK"]}"/></defs>')
    out.append(f'{g_open} opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" '
               f'keyTimes="{trav_op_kt}" calcMode="spline" keySplines="{spl5}" {rep}/>')
    for i in range(N_TRAVEL):
        pts = [chain[0][i], chain[0][i]]
        for j in range(1, len(chain)):
            pts += [chain[j][i], chain[j][i]]
        pts.append(chain[0][i])
        vals = ";".join(f"{p[0]:.0f} {p[1]:.0f}" for p in pts)
        out.append(
            f'<use href="#tv{theme}"><animateTransform attributeName="transform" type="translate" '
            f'values="{vals}" keyTimes="{kts}" calcMode="spline" keySplines="{spl}" {rep}/></use>')
    out.append("</g>")
    return "\n".join(out)


def build_info(theme):
    c = THEMES[theme]
    x0, x1, N = 470, 1125, 79
    out = []
    corner = 14
    fx, fy, fw, fh = FRAME
    for (ax, ay, bx, by, cx_, cy_) in [
        (fx + corner, fy, fx, fy, fx, fy + corner), (fx + fw - corner, fy, fx + fw, fy, fx + fw, fy + corner),
        (fx + corner, fy + fh, fx, fy + fh, fx, fy + fh - corner),
        (fx + fw - corner, fy + fh, fx + fw, fy + fh, fx + fw, fy + fh - corner)]:
        out.append(f'<path d="M {ax} {ay} L {bx} {by} L {cx_} {cy_}" fill="none" stroke="{c["GLOW"]}" stroke-width="2" opacity="0.8"/>')
    out.append(f'<text x="{x0}" y="106" font-size="13" letter-spacing="2" fill="{c["HEAD"]}" filter="url(#txtGlow)">SYSTEM.INFO</text>')
    out.append(f'<line x1="566" y1="102" x2="1061" y2="102" stroke="{c["HAIR"]}"/>')
    out.append(f'<text x="{x1}" y="106" text-anchor="end" font-size="12" fill="{c["LIVE"]}" font-weight="700">'
               f'<tspan>&#9679;</tspan> LIVE<animate attributeName="opacity" values="1;0.25;1" dur="1.6s" repeatCount="indefinite"/></text>')
    pill_w = round(len(HANDLE_MAIL) * 8.4 + 18)
    out.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="0.6s" fill="freeze"/>')
    out.append(f'<rect x="{x0}" y="122" width="{pill_w}" height="20" rx="4" fill="{c["PILL"]}"/>')
    out.append(f'<text x="{x0 + 9}" y="136" font-size="14" font-weight="700" fill="{c["PILL_TX"]}">{html.escape(HANDLE_MAIL)}</text>')
    out.append(f'<line x1="{x0 + pill_w + 10}" y1="130" x2="{x1}" y2="130" stroke="{c["HAIR"]}"/></g>')

    y, t = 162, 0.90
    for row in ROWS:
        if row is None:                      # section gap
            y += 8
            t += 0.10
            continue
        if isinstance(row, str):             # divider
            y += 8
            t += 0.10
            head = f"- {row} "
            out.append(
                f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="{t:.2f}s" fill="freeze"/>'
                f'<text x="{x0}" y="{y}" font-size="14" textLength="{x1 - x0}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
                f'<tspan fill="{c["MUTED"]}">{head}</tspan><tspan fill="{c["LEAD"]}">{"-" * (N - len(head))}</tspan></text></g>')
            y += 23
            t += 0.12
            continue
        k, v = row
        lead = "." * max(3, N - len(k) - 1 - len(v) - 1)
        out.append(
            f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="{t:.2f}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" values="-8 0;0 0" dur="0.4s" begin="{t:.2f}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .7 .3 1"/>'
            f'<text x="{x0}" y="{y}" font-size="14" textLength="{x1 - x0}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
            f'<tspan fill="{c["KEY"]}">{html.escape(k)} </tspan><tspan fill="{c["LEAD"]}">{lead}</tspan>'
            f'<tspan fill="{c["VAL"]}" font-weight="600"> {html.escape(v)}</tspan></text></g>')
        y += 23
        t += 0.12
    t += 0.20
    y += 8
    out.append(
        f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{t:.2f}s" fill="freeze"/>'
        f'<text x="{x0}" y="{y}" font-size="14" fill="{c["MUTED"]}">&#9656; More about me &amp; projects below in README &#8595; '
        f'<tspan fill="{c["GLOW"]}">&#9608;<animate attributeName="fill-opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></tspan></text></g>')
    return "\n".join(out)


def build(theme, dots, shapes):
    c = THEMES[theme]
    a0, a1, a2 = c["ACC"]
    fx, fy, fw, fh = FRAME
    cyc = lambda *v: ";".join(v)
    head = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}" role="img" aria-label="Talha Güleryüz — profile.sh --live">
<defs>
<linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{a0}"><animate attributeName="stop-color" values="{cyc(a0, a1, a2, a0)}" dur="10s" repeatCount="indefinite"/></stop>
<stop offset="0.5" stop-color="{a1}"><animate attributeName="stop-color" values="{cyc(a1, a2, a0, a1)}" dur="10s" repeatCount="indefinite"/></stop>
<stop offset="1" stop-color="{a2}"><animate attributeName="stop-color" values="{cyc(a2, a0, a1, a2)}" dur="10s" repeatCount="indefinite"/></stop>
</linearGradient>
<linearGradient id="panelGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["PANEL0"]}"/><stop offset="1" stop-color="{c["PANEL1"]}"/></linearGradient>
<filter id="glow8" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="8"/></filter>
<filter id="glow3" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="3"/></filter>
<filter id="txtGlow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="0.9" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="winClip"><rect x="2" y="2" width="{W - 4}" height="{H - 4}" rx="18"/></clipPath>
</defs>
<rect x="2" y="2" width="{W - 4}" height="{H - 4}" rx="18" fill="{c["OUTER"]}"/>
<g clip-path="url(#winClip)">
<rect x="2" y="2" width="{W - 4}" height="{H - 4}" fill="url(#panelGrad)"/>
<rect x="2" y="2" width="{W - 4}" height="46" fill="{c["BAR"]}"/>
<line x1="2" y1="48" x2="{W - 2}" y2="48" stroke="{c["HAIR"]}"/>
<circle cx="30" cy="25" r="5.5" fill="#ff5f56"/>
<circle cx="50" cy="25" r="5.5" fill="#ffbd2e"/>
<circle cx="70" cy="25" r="5.5" fill="#27c93f"/>
<text x="{W / 2:.0f}" y="29" text-anchor="middle" font-size="12" fill="{c["TITLE"]}">{html.escape(HANDLE_MAIL)} - % ./profile.sh --live</text>
<text x="38" y="74" font-size="10" letter-spacing="3" fill="{c["LABEL_DIM"]}">VISUAL.MAP</text>
<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="10" fill="none" stroke="{c["GLOW"]}" stroke-width="2" opacity="0.45" filter="url(#glow3)"/>
<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="10" fill="{c["FRAME_BG"]}" stroke="{c["FRAME_STROKE"]}"/>'''
    tail = f'''</g>
<rect x="3" y="3" width="{W - 6}" height="{H - 6}" rx="17" fill="none" stroke="url(#accent)" stroke-width="3" opacity="0.55" filter="url(#glow8)"/>
<rect x="3" y="3" width="{W - 6}" height="{H - 6}" rx="17" fill="none" stroke="url(#accent)" stroke-width="1.6"/>
</svg>
'''
    return "\n".join([head, build_visual(theme, dots, shapes), build_info(theme), tail])


def main():
    global PHOTO, MASK
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", default=PHOTO)
    ap.add_argument("--mask", default=MASK, help="white=subject; pass '' to auto-segment")
    ap.add_argument("--out", default=ROOT)
    ap.add_argument("--preview", action="store_true", help="also write dither PNGs")
    args = ap.parse_args()
    PHOTO, MASK = args.photo, args.mask

    shapes = [logo_points(n, N_TRAVEL) for n in LOGOS]
    for theme in ("dark", "light"):
        dots = portrait_dots(theme)
        if args.preview:
            Image.fromarray((~dots * 255).astype(np.uint8)).resize((372, 490), Image.NEAREST).save(
                os.path.join(args.out, f"_preview-{theme}.png"))
        svg = build(theme, dots, shapes)
        path = os.path.join(args.out, f"{theme}.svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"{theme}.svg  {len(svg.encode()) / 1024:.0f} KB  dots={int(dots.sum())}")


if __name__ == "__main__":
    sys.exit(main())
