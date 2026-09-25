#!/usr/bin/env python3
"""
Animated PROJECTS.LIST panel: 2-column grid of mini terminal cards.

Curate projects.json (order = display order, logo = file in logos/); stars,
languages and "updated" come from data/profile.json. Private repos
("repo": null) render from config only, with a lock instead of stats.

    python scripts/profile/projects.py [outdir]
"""
import base64
import datetime as dt
import math
import os
import sys

from common import MONO, ROOT, THEMES, esc, lang_color, load_data, write

W, CARD_W, CARD_H, GAP, MARGIN = 1180, 578, 168, 14, 5


def rel_time(iso):
    if not iso:
        return "n/a"
    d = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if d.days >= 365:
        return f"{d.days // 365}y ago"
    if d.days >= 30:
        return f"{d.days // 30}mo ago"
    if d.days > 0:
        return f"{d.days}d ago"
    return f"{d.seconds // 3600}h ago" if d.seconds >= 3600 else "just now"


def logo_uri(name):
    if not name:
        return None
    p = os.path.join(ROOT, "logos", name)
    if not os.path.exists(p):
        return None
    mime = {"svg": "image/svg+xml", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(
        name.rsplit(".", 1)[-1].lower(), "image/png")
    with open(p, "rb") as fh:
        return f"data:{mime};base64,{base64.b64encode(fh.read()).decode()}"


def wrap(s, width, lines=2):
    out, cur = [], ""
    words = s.split()
    for i, w in enumerate(words):
        if len(cur) + len(w) + (1 if cur else 0) <= width:
            cur = f"{cur} {w}".strip()
            continue
        out.append(cur)
        cur = w
        if len(out) == lines:
            out[-1] = out[-1][: width - 1].rstrip(" ,.:") + "…"
            return out
    return out + [cur] if cur else out


def donut(langs, cx, cy, r, begin, c):
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:4]
    rest = total - sum(v for _, v in top)
    if rest > 0:
        top.append(("Other", rest))
    circ = 2 * math.pi * r
    palette = [c["VIOLET"], c["CYAN"], c["EMERALD"], "#6366F1", "#64748B"]
    o, legend, off, t = [], [], 0.0, begin
    for i, (name, v) in enumerate(top):
        seg, col = circ * v / total, palette[i % len(palette)]
        o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="9" '
                 f'stroke-dasharray="0 {circ:.2f}" stroke-dashoffset="{-off:.2f}" transform="rotate(-90 {cx} {cy})">'
                 f'<animate attributeName="stroke-dasharray" from="0 {circ:.2f}" to="{seg:.2f} {circ - seg:.2f}" '
                 f'dur="0.6s" begin="{t:.2f}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".3 0 .2 1"/></circle>')
        legend.append((name, v / total, col))
        off += seg
        t += 0.18
    return "".join(o), legend


def card(p, x, y, i, c):
    b = 0.25 + i * 0.15
    repo = p.get("repo") or ""
    head = repo or f'private/{p.get("slug") or p["name"].lower()}'
    link = f"https://github.com/{repo}" if repo else "https://github.com/Tguleryuz52"
    o = [f'<a href="{esc(link)}" target="_blank"><g opacity="0" transform="translate({x},{y})">'
         f'<animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{b:.2f}s" fill="freeze"/>',
         f'<rect width="{CARD_W}" height="{CARD_H}" rx="12" fill="{c["PANEL"]}" stroke="{c["STROKE_LO"]}">'
         f'<animate attributeName="stroke" values="{c["STROKE_LO"]};{c["STROKE_HI"]};{c["STROKE_LO"]}" dur="4.5s" '
         f'begin="{b + i * 0.7:.2f}s" repeatCount="indefinite"/></rect>',
         f'<path d="M0 30V12A12 12 0 0 1 12 0H{CARD_W - 12}A12 12 0 0 1 {CARD_W} 12V30Z" fill="{c["PANEL_BAR"]}"/>',
         f'<line x1="0" y1="30" x2="{CARD_W}" y2="30" stroke="{c["BARLINE"]}"/>',
         f'<text x="16" y="19" font-size="10" fill="{c["MUTED"]}"><tspan fill="{c["CYAN"]}">&#8226;</tspan> {esc(head)}</text>']

    days = 999
    if p.get("pushed_at"):
        days = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(p["pushed_at"].replace("Z", "+00:00"))).days
    if days <= 14:
        o.append(f'<circle cx="{CARD_W - 16}" cy="15" r="3.5" fill="{c["EMERALD"]}">'
                 f'<animate attributeName="opacity" values="1;.25;1" dur="1.8s" repeatCount="indefinite"/></circle>')
    else:
        o.append(f'<circle cx="{CARD_W - 16}" cy="15" r="3.5" fill="{c["DIM"]}"/>')

    bob = (f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -2.5;0 0" dur="5s" '
           f'begin="{b + i * 0.5:.2f}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" '
           f'keySplines=".4 0 .6 1;.4 0 .6 1"/>')
    uri = logo_uri(p.get("logo"))
    if uri:
        o.append(f'<g>{bob}<image x="16" y="44" width="40" height="40" href="{uri}" preserveAspectRatio="xMidYMid meet"/></g>')
    else:
        o.append(f'<g>{bob}<rect x="16" y="44" width="40" height="40" rx="9" fill="{c["VIOLET2"]}" opacity=".9"/>'
                 f'<text x="36" y="71" text-anchor="middle" font-size="20" font-weight="700" fill="{c["MONO_TX"]}">'
                 f'{esc(p["name"][0].upper())}</text></g>')

    o.append(f'<text x="68" y="61" font-size="17" font-weight="700" fill="{c["TEXT"]}">{esc(p["name"])}'
             f'<tspan fill="{c["CYAN"]}">_<animate attributeName="opacity" values="1;0;1" dur="1.2s" '
             f'begin="{b + 0.4:.2f}s" repeatCount="indefinite"/></tspan></text>')
    langs = p.get("languages") or {}
    for j, line in enumerate(wrap(p.get("description", ""), 50 if langs or not repo else 60)):
        o.append(f'<text x="68" y="{80 + j * 16}" font-size="11" fill="{c["MUTED"]}">{esc(line)}</text>')

    tx = 68
    for tag in (p.get("tags") or [])[:3]:
        tw = len(tag) * 6.6 + 14
        o.append(f'<rect x="{tx}" y="118" width="{tw:.0f}" height="17" rx="8.5" fill="{c["PILL_BG"]}" stroke="{c["PILL_STROKE"]}"/>'
                 f'<text x="{tx + tw / 2:.0f}" y="130" text-anchor="middle" font-size="9.5" fill="{c["VIOLET"]}">{esc(tag)}</text>')
        tx += tw + 7

    if repo:
        o.append(f'<text x="68" y="155" font-size="11" fill="{c["MUTED"]}"><tspan fill="{c["CYAN"]}">&#9733;</tspan> '
                 f'{p.get("stars", 0)}<tspan fill="{c["DIM"]}" dx="14">updated {rel_time(p.get("pushed_at"))}</tspan></text>')
    else:
        o.append(f'<text x="68" y="155" font-size="11" fill="{c["DIM"]}"><tspan fill="{c["CYAN"]}">&#9679;</tspan> private repo</text>')

    cx, cy, r = CARD_W - 58, CARD_H // 2 + 6, 27
    if langs:
        segs, legend = donut(langs, cx, cy, r, b + 0.3, c)
        o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c["RING_BG"]}" stroke-width="9"/>{segs}')
        o.append(f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" font-size="11" font-weight="700" '
                 f'fill="{c["TEXT"]}">{legend[0][1] * 100:.0f}%</text>')
        dot_x, ly = cx - r - 92, cy - 22
        for name, frac, col in legend[:3]:
            o.append(f'<circle cx="{dot_x}" cy="{ly}" r="3.5" fill="{col}"/>'
                     f'<text x="{dot_x + 9}" y="{ly + 4}" font-size="10" fill="{c["MUTED"]}">{esc(name)} {frac * 100:.0f}%</text>')
            ly += 18
    elif not repo:   # private: dashed ring + padlock where the donut would be
        o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c["RING_BG"]}" stroke-width="9"/>'
                 f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c["VIOLET"]}" stroke-width="2" '
                 f'stroke-dasharray="3 5" opacity=".7"><animateTransform attributeName="transform" type="rotate" '
                 f'from="0 {cx} {cy}" to="360 {cx} {cy}" dur="18s" repeatCount="indefinite"/></circle>'
                 f'<g transform="translate({cx - 8},{cy - 10})" fill="{c["VIOLET"]}"><rect x="1" y="8" width="14" height="11" rx="2"/>'
                 f'<path d="M4 8V5a4 4 0 0 1 8 0v3" fill="none" stroke="{c["VIOLET"]}" stroke-width="2"/></g>')
    o.append("</g></a>")
    return "".join(o)


def build(projects, theme):
    c = THEMES[theme]
    rows = math.ceil(len(projects) / 2)
    H = 42 + rows * (CARD_H + GAP) - GAP + MARGIN
    g = f"acc_{theme}"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="{MONO}" role="img" aria-label="Projects">',
         f'<rect width="{W}" height="{H}" fill="{c["BG"]}"/>',
         f'<defs><linearGradient id="{g}" x1="0" y1="0" x2="1" y2="0">'
         f'<stop offset="0" stop-color="{c["VIOLET2"]}"><animate attributeName="stop-color" '
         f'values="{c["VIOLET2"]};{c["CYAN"]};{c["EMERALD"]};{c["VIOLET2"]}" dur="10s" repeatCount="indefinite"/></stop>'
         f'<stop offset="1" stop-color="{c["EMERALD"]}"><animate attributeName="stop-color" '
         f'values="{c["EMERALD"]};{c["VIOLET2"]};{c["CYAN"]};{c["EMERALD"]}" dur="10s" repeatCount="indefinite"/></stop>'
         f'</linearGradient></defs>',
         f'<text x="{MARGIN + 2}" y="18" font-size="11" letter-spacing="2" fill="{c["CYAN"]}">PROJECTS.LIST</text>',
         f'<text x="{MARGIN + 130}" y="18" font-size="10" fill="{c["DIM"]}">./projects.sh --all</text>',
         f'<line x1="{MARGIN}" y1="28" x2="{W - MARGIN}" y2="28" stroke="url(#{g})" stroke-width="1.5" opacity=".7"/>']
    for i, p in enumerate(projects):
        o.append(card(p, MARGIN + (i % 2) * (CARD_W + GAP + 4), 42 + (i // 2) * (CARD_H + GAP), i, c))
    o.append("</svg>")
    return "".join(o)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "dist"
    projects = load_data()["projects"]
    for theme in ("dark", "light"):
        write(out, f"projects-{theme}.svg", build(projects, theme))


if __name__ == "__main__":
    main()
