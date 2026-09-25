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


def lock(col, s=1.0):
    return (f'<g transform="scale({s})" fill="{col}"><rect x="0" y="4.6" width="9" height="6.8" rx="1.4"/>'
            f'<path d="M2 4.6V3.2a2.5 2.5 0 0 1 5 0v1.4" fill="none" stroke="{col}" stroke-width="1.4"/></g>')


def gear_path(cx=20, cy=20, teeth=8, r_out=11.5, r_in=8.6, hole=3.6):
    n, pts = teeth * 4, []
    for k in range(n):
        a = 2 * math.pi * k / n - math.pi / 2
        r = r_out if k % 4 in (1, 2) else r_in
        pts.append(f"{cx + r * math.cos(a):.2f} {cy + r * math.sin(a):.2f}")
    return (f'M{"L".join(pts)}Z M{cx + hole} {cy}a{hole} {hole} 0 1 0 {-2 * hole} 0'
            f'a{hole} {hole} 0 1 0 {2 * hole} 0Z')


STROKE = 'fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"'
SPIN = '<animateTransform attributeName="transform" type="rotate" from="0 20 20" to="360 20 20" dur="{d}s" repeatCount="indefinite"/>'
ICONS = {  # 40x40 tile glyphs: (gradient from, to, markup)
    "gear": ("#234D9C", "#0E92DD",
             f'<path d="{gear_path()}" fill="#fff" fill-rule="evenodd">{SPIN.format(d=14)}</path>'),
    "pulse": ("#059669", "#22D3EE",
              f'<path d="M6 21h6.5l2.6-6.5 4.6 13 3-9 2.2 2.5H34" {STROKE} opacity=".35"/>'
              f'<path d="M6 21h6.5l2.6-6.5 4.6 13 3-9 2.2 2.5H34" {STROKE} stroke-dasharray="62" stroke-dashoffset="62">'
              f'<animate attributeName="stroke-dashoffset" values="62;0;0;-62" keyTimes="0;.45;.7;1" dur="2.6s" repeatCount="indefinite"/></path>'),
    "hanger": ("#7C3AED", "#EC4899",
               f'<g><animateTransform attributeName="transform" type="rotate" values="-6 20 10;6 20 10;-6 20 10" dur="3.2s" '
               f'repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/>'
               f'<path d="M20 14.2c0-1.9 2.7-2.3 2.7-4.2a2.7 2.7 0 0 0-5.4 0" {STROKE}/>'
               f'<path d="M20 14.6 8.6 23a1.5 1.5 0 0 0 .9 2.7h21a1.5 1.5 0 0 0 .9-2.7Z" {STROKE}/></g>'),
    "robot": ("#F59E0B", "#F97316",
              f'<path d="M20 13V10" {STROKE}/><circle cx="20" cy="8.6" r="1.9" fill="#fff">'
              f'<animate attributeName="fill" values="#fff;#FEF08A;#fff" dur="1.6s" repeatCount="indefinite"/></circle>'
              f'<rect x="10.5" y="13" width="19" height="15" rx="5" {STROKE}/><path d="M8 19v4M32 19v4M17 24.6h6" {STROKE}/>'
              + "".join(f'<ellipse cx="{ex}" cy="20.3" rx="2" ry="2" fill="#fff"><animate attributeName="ry" '
                        f'values="2;2;.3;2" keyTimes="0;.9;.95;1" dur="3.4s" repeatCount="indefinite"/></ellipse>'
                        for ex in (16.2, 23.8))),
    "android": ("#0EA5E9", "#6366F1",
                f'<circle cx="20" cy="20" r="9.5" {STROKE} stroke-dasharray="11.5 3.4">{SPIN.format(d=8)}</circle>'
                f'<circle cx="20" cy="20" r="3.6" fill="#fff"><animate attributeName="fill" '
                f'values="#fff;#7DD3FC;#FDE047;#fff" dur="4s" repeatCount="indefinite"/></circle>'),
    "card": ("#10B981", "#84CC16",
             f'<path d="M13 8.5h14l3.6 4.2v12.5L20 31.6 9.4 25.2V12.7Z" {STROKE}/>'
             f'<path d="m20 14.2 1.7 3.5 3.8.5-2.8 2.6.7 3.8-3.4-1.8-3.4 1.8.7-3.8-2.8-2.6 3.8-.5Z" fill="#fff">'
             f'<animate attributeName="opacity" values="1;.45;1" dur="2.2s" repeatCount="indefinite"/></path>'),
}


def icon(kind, i):
    a, b, glyph = ICONS[kind]
    gid = f"ic_{i}"
    return (f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a}"/>'
            f'<stop offset="1" stop-color="{b}"/></linearGradient></defs>'
            f'<rect width="40" height="40" rx="11" fill="url(#{gid})"/>'
            f'<rect x=".5" y=".5" width="39" height="39" rx="10.5" fill="none" stroke="#fff" stroke-opacity=".22"/>'
            f'{glyph}')


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
         f'<line x1="0" y1="30" x2="{CARD_W}" y2="30" stroke="{c["BARLINE"]}"/>']
    if repo:
        o.append(f'<text x="16" y="19" font-size="10" fill="{c["MUTED"]}"><tspan fill="{c["CYAN"]}">&#8226;</tspan> {esc(head)}</text>')
    else:
        o.append(f'<g transform="translate(15,9.5)">{lock(c["VIOLET"], 0.9)}</g>'
                 f'<text x="27" y="19" font-size="10" fill="{c["MUTED"]}">{esc(head)}</text>')

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
    if p.get("icon") in ICONS:
        o.append(f'<g>{bob}<g transform="translate(16,44)">{icon(p["icon"], i)}</g></g>')
    elif uri:
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
        o.append(f'<g transform="translate(68,146)">{lock(c["CYAN"], 0.85)}</g>'
                 f'<text x="80" y="155" font-size="11" fill="{c["DIM"]}">{esc(p.get("footer") or "private repo")}</text>')

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
    elif p.get("highlights"):   # private repo: no language data, so show what it achieved instead
        circ = 2 * math.pi * r
        o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c["RING_BG"]}" stroke-width="9"/>'
                 f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#hl_{i})" stroke-width="9" '
                 f'stroke-linecap="round" stroke-dasharray="0 {circ:.2f}" transform="rotate(-90 {cx} {cy})">'
                 f'<animate attributeName="stroke-dasharray" from="0 {circ:.2f}" to="{circ:.2f} 0" dur="1.1s" '
                 f'begin="{b + 0.3:.2f}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".3 0 .2 1"/></circle>'
                 f'<defs><linearGradient id="hl_{i}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["VIOLET"]}"/>'
                 f'<stop offset="1" stop-color="{c["CYAN"]}"/></linearGradient></defs>'
                 f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" font-size="12" font-weight="700" '
                 f'fill="{c["TEXT"]}">{esc(p.get("badge", "★"))}</text>')
        dot_x, ly = cx - r - 96, cy - 22
        for name, col in zip(p["highlights"][:3], (c["VIOLET"], c["CYAN"], c["EMERALD"])):
            o.append(f'<circle cx="{dot_x}" cy="{ly}" r="3.5" fill="{col}"/>'
                     f'<text x="{dot_x + 9}" y="{ly + 4}" font-size="10" fill="{c["MUTED"]}">{esc(name)}</text>')
            ly += 18
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
