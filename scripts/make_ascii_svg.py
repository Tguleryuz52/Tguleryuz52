#!/usr/bin/env python3
"""
Generate ultra-crisp monochrome ASCII portrait SVG with typewriter animation.
"""
import html
import os
import sys
from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "talha-ascii.svg")

COLS = 96
ROWS = 52
RAMP = " .`:-=+*cs#%@"

GAMMA = 1.12
WHITE_FLOOR = 0.72

CANVAS_W = 370
CANVAS_H = 430

BG = "#0d1117"
FRAME = "#30363d"
INK = "#c9d1d9"

ROW_DUR = 0.07
STAGGER = 0.05

def main():
    if not os.path.exists(SRC):
        print(f"Error: {SRC} not found.", file=sys.stderr)
        sys.exit(1)

    im = Image.open(SRC).convert("L")
    im = ImageEnhance.Contrast(im).enhance(1.25)
    im = im.resize((COLS, ROWS), Image.Resampling.LANCZOS)
    px = im.load()

    rows_txt = []
    for y in range(ROWS):
        chars = []
        for x in range(COLS):
            lum = px[x, y] / 255.0
            lum = pow(lum, GAMMA)
            if lum >= WHITE_FLOOR:
                chars.append(" ")
                continue
            idx = int((1.0 - lum) * (len(RAMP) - 1))
            idx = max(0, min(len(RAMP) - 1, idx))
            chars.append(RAMP[idx])
        rows_txt.append("".join(chars))

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" width="{CANVAS_W}" height="{CANVAS_H}">')
    svg_parts.append('<style>')
    svg_parts.append(f'''
        .bg {{ fill: {BG}; stroke: {FRAME}; stroke-width: 1; rx: 8px; }}
        .title-bar {{ fill: #161b22; rx: 8px 8px 0 0; }}
        .dot-red {{ fill: #ff5f56; }}
        .dot-yellow {{ fill: #ffbd2e; }}
        .dot-green {{ fill: #27c93f; }}
        .term-title {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace; font-size: 11px; fill: #8b949e; text-anchor: middle; }}
        .ascii-text {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 6.5px; fill: {INK}; letter-spacing: 0.2px; }}
    ''')
    svg_parts.append('</style>')

    # Window
    svg_parts.append(f'<rect class="bg" x="0.5" y="0.5" width="{CANVAS_W - 1}" height="{CANVAS_H - 1}" />')
    svg_parts.append(f'<path d="M 0.5 8.5 A 8 8 0 0 1 8.5 0.5 L {CANVAS_W - 8.5} 0.5 A 8 8 0 0 1 {CANVAS_W - 0.5} 8.5 L {CANVAS_W - 0.5} 28.5 L 0.5 28.5 Z" class="title-bar" />')
    svg_parts.append('<circle class="dot-red" cx="18" cy="14.5" r="4.5" />')
    svg_parts.append('<circle class="dot-yellow" cx="32" cy="14.5" r="4.5" />')
    svg_parts.append('<circle class="dot-green" cx="46" cy="14.5" r="4.5" />')
    svg_parts.append(f'<text class="term-title" x="{CANVAS_W / 2}" y="18">talha.ascii [view]</text>')

    start_y = 48
    line_h = 7.1
    for i, line in enumerate(rows_txt):
        y_pos = start_y + (i * line_h)
        escaped = html.escape(line).replace(" ", "&#160;")
        delay = i * STAGGER
        
        clip_id = f"cl-r-{i}"
        svg_parts.append(f'<clipPath id="{clip_id}">')
        svg_parts.append(f'  <rect x="14" y="{y_pos - 6.5}" width="0" height="{line_h + 1}">')
        svg_parts.append(f'    <animate attributeName="width" from="0" to="{CANVAS_W - 28}" dur="{ROW_DUR}s" begin="{delay:.2f}s" fill="freeze" />')
        svg_parts.append('  </rect>')
        svg_parts.append('</clipPath>')
        
        svg_parts.append(f'<text class="ascii-text" x="14" y="{y_pos}" clip-path="url(#{clip_id})">{escaped}</text>')

    svg_parts.append('</svg>')

    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_parts))
    print(f"Generated High-Res ASCII SVG: {OUT}")

if __name__ == "__main__":
    main()
