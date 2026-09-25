#!/usr/bin/env python3
"""
ACHIEVEMENTS.LOG panel: earned GitHub achievements (scraped by fetch_data.py,
refreshed every 6h) next to real-world awards. Same card language as PROJECTS.LIST.

Badge images are downscaled and inlined (an SVG shown through <img> cannot load
external URLs), so Pillow is used when available.

    python scripts/profile/achievements.py [outdir]
"""
import base64
import io
import math
import sys
import urllib.request

from common import MONO, THEMES, esc, load_data, write

W, GAP, MARGIN, CARD_H, PER_ROW = 1180, 14, 5, 150, 6

# how each GitHub achievement is earned (short enough for one card line)
HOW = {
    "pull-shark": "Merged pull requests",
    "quickdraw": "Closed a PR within 5 min",
    "yolo": "Merged without a review",
    "starstruck": "A repo with 16+ stars",
    "pair-extraordinaire": "Co-authored merged PRs",
    "galaxy-brain": "Accepted answers",
    "public-sponsor": "Sponsors open source",
    "arctic-code-vault-contributor": "Code in the Arctic Vault",
}

# real-world awards (not on GitHub, so kept here)
AWARDS = [
    {"name": "TEKNOFEST", "sub": "Top 14 of 4,250 · Smart Tour", "glyph": "trophy", "grad": ("#F59E0B", "#EF4444")},
    {"name": "ANTSPARK", "sub": "3rd place · Robotoy", "glyph": "medal", "grad": ("#A78BFA", "#EC4899")},
    {"name": "TÜBİTAK", "sub": "Backed project · Robotoy", "glyph": "shield", "grad": ("#22D3EE", "#2563EB")},
]

STROKE = 'fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"'
GLYPHS = {  # drawn in a 72x72 box, centre 36,36
    "trophy": f'<path d="M26 21h20v9a10 10 0 0 1-20 0Z" {STROKE}/><path d="M26 24h-5a5 5 0 0 0 5 8M46 24h5a5 5 0 0 1-5 8" {STROKE}/>'
              f'<path d="M36 40v7M29 51h14" {STROKE}/>',
    "medal": f'<path d="M28 17l8 13 8-13" {STROKE}/><circle cx="36" cy="41" r="11" {STROKE}/>'
             f'<text x="36" y="46.5" text-anchor="middle" font-size="15" font-weight="800" fill="#fff" font-family="{MONO}">3</text>',
    "shield": f'<path d="M36 17l14 5v10c0 9-6 16-14 20-8-4-14-11-14-20V22Z" {STROKE}/>'
              f'<path d="m36 27 2.6 5.2 5.7.8-4.1 4 1 5.7-5.2-2.7-5.2 2.7 1-5.7-4.1-4 5.7-.8Z" fill="#fff"/>',
}


def badge_uri(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "profile"}), timeout=30) as r:
            data = r.read()
    except Exception as e:  # noqa: BLE001 - card still renders, just without the image
        print(f"warn: badge {url}: {e}", file=sys.stderr)
        return None
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data)).convert("RGBA").resize((144, 144), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        data = buf.getvalue()
    except ImportError:
        pass
    return "data:image/png;base64," + base64.b64encode(data).decode()


def card(item, x, y, w, i, c):
    b = 0.25 + i * 0.12
    cx = w / 2
    o = [f'<g opacity="0" transform="translate({x:.1f},{y})">'
         f'<animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{b:.2f}s" fill="freeze"/>',
         f'<rect width="{w:.1f}" height="{CARD_H}" rx="12" fill="{c["PANEL"]}" stroke="{c["STROKE_LO"]}">'
         f'<animate attributeName="stroke" values="{c["STROKE_LO"]};{c["STROKE_HI"]};{c["STROKE_LO"]}" dur="4.5s" '
         f'begin="{b + i * 0.6:.2f}s" repeatCount="indefinite"/></rect>',
         f'<text x="12" y="19" font-size="8" letter-spacing="1.5" fill="{c["DIM"]}">{item["kind"]}</text>']
    if item.get("tier"):
        o.append(f'<rect x="{w - 40:.1f}" y="9" width="30" height="16" rx="8" fill="{c["PILL_BG"]}" stroke="{c["PILL_STROKE"]}"/>'
                 f'<text x="{w - 25:.1f}" y="21" text-anchor="middle" font-size="10" font-weight="700" fill="{c["VIOLET"]}">{esc(item["tier"])}</text>')
    # glow + floating badge
    o.append(f'<circle cx="{cx:.1f}" cy="54" r="34" fill="url(#glow_{c["_t"]})"><animate attributeName="r" values="30;36;30" '
             f'dur="3.6s" begin="{i * 0.4:.1f}s" repeatCount="indefinite"/></circle>')
    bob = (f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -3;0 0" dur="4.8s" '
           f'begin="{b + i * 0.4:.2f}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" '
           f'keySplines=".4 0 .6 1;.4 0 .6 1"/>')
    if item.get("uri"):
        o.append(f'<g>{bob}<image x="{cx - 36:.1f}" y="18" width="72" height="72" href="{item["uri"]}"/></g>')
    else:
        g0, g1 = item.get("grad", (c["VIOLET2"], c["CYAN"]))
        o.append(f'<defs><linearGradient id="aw_{c["_t"]}_{i}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{g0}"/>'
                 f'<stop offset="1" stop-color="{g1}"/></linearGradient></defs>'
                 f'<g>{bob}<g transform="translate({cx - 36:.1f},18)"><circle cx="36" cy="36" r="34" fill="url(#aw_{c["_t"]}_{i})"/>'
                 f'<circle cx="36" cy="36" r="33" fill="none" stroke="#fff" stroke-opacity=".25"/>'
                 f'{GLYPHS.get(item.get("glyph"), "")}</g></g>')
    o.append(f'<text x="{cx:.1f}" y="114" text-anchor="middle" font-size="14" font-weight="700" fill="{c["TEXT"]}">{esc(item["name"])}</text>'
             f'<text x="{cx:.1f}" y="132" text-anchor="middle" font-size="10" fill="{c["MUTED"]}">{esc(item["sub"])}</text></g>')
    return "".join(o)


def build(items, theme):
    c = dict(THEMES[theme], _t=theme)
    rows = math.ceil(len(items) / PER_ROW)
    H = 42 + rows * (CARD_H + GAP) - GAP + MARGIN
    g = f"acc_{theme}"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="{MONO}" role="img" aria-label="Achievements and awards">',
         f'<rect width="{W}" height="{H}" fill="{c["BG"]}"/>',
         f'<defs><linearGradient id="{g}" x1="0" y1="0" x2="1" y2="0">'
         f'<stop offset="0" stop-color="{c["VIOLET2"]}"><animate attributeName="stop-color" '
         f'values="{c["VIOLET2"]};{c["CYAN"]};{c["EMERALD"]};{c["VIOLET2"]}" dur="10s" repeatCount="indefinite"/></stop>'
         f'<stop offset="1" stop-color="{c["EMERALD"]}"><animate attributeName="stop-color" '
         f'values="{c["EMERALD"]};{c["VIOLET2"]};{c["CYAN"]};{c["EMERALD"]}" dur="10s" repeatCount="indefinite"/></stop>'
         f'</linearGradient><radialGradient id="glow_{theme}"><stop offset="0" stop-color="{c["CYAN"]}" stop-opacity=".28"/>'
         f'<stop offset="1" stop-color="{c["CYAN"]}" stop-opacity="0"/></radialGradient></defs>',
         f'<text x="{MARGIN + 2}" y="18" font-size="11" letter-spacing="2" fill="{c["CYAN"]}">ACHIEVEMENTS.LOG</text>',
         f'<text x="{MARGIN + 156}" y="18" font-size="10" fill="{c["DIM"]}">./badges.sh --earned</text>',
         f'<line x1="{MARGIN}" y1="28" x2="{W - MARGIN}" y2="28" stroke="url(#{g})" stroke-width="1.5" opacity=".7"/>']
    for r in range(rows):
        row = items[r * PER_ROW:(r + 1) * PER_ROW]
        w = (W - 2 * MARGIN - GAP * (len(row) - 1)) / len(row)
        for j, it in enumerate(row):
            o.append(card(it, MARGIN + j * (w + GAP), 42 + r * (CARD_H + GAP), w, r * PER_ROW + j, c))
    o.append("</svg>")
    return "".join(o)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "dist"
    earned = load_data().get("achievements") or []
    items = [{"kind": "GITHUB", "name": a["name"], "sub": HOW.get(a["slug"], "GitHub achievement"),
              "tier": a.get("tier"), "uri": badge_uri(a["img"])} for a in earned]
    items += [dict(a, kind="AWARD") for a in AWARDS]
    for theme in ("dark", "light"):
        write(out, f"achievements-{theme}.svg", build(items, theme))


if __name__ == "__main__":
    main()
