#!/usr/bin/env python3
"""
Streak / stats / top-languages cards, rendered from data/profile.json.

Same layout language as streak-stats + github-readme-stats (so the README reads
exactly like the reference), but generated in-repo: no public instance, no
"API rate limit exceeded", no token. Rank is intentionally absent: it is
stars/followers weighted and says nothing about how much you ship.

    python scripts/profile/cards.py [outdir]
"""
import sys

from common import SANS, THEMES, esc, fmt_date, lang_color, load_data, write

ICONS = {  # octicons 16px
    "star": "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Zm0 2.445L6.615 5.5a.75.75 0 0 1-.564.41l-3.097.45 2.24 2.184a.75.75 0 0 1 .216.664l-.528 3.084 2.769-1.456a.75.75 0 0 1 .698 0l2.77 1.456-.53-3.084a.75.75 0 0 1 .216-.664l2.24-2.183-3.096-.45a.75.75 0 0 1-.564-.41L8 2.694Z",
    "history": "m.427 1.927 1.215 1.215a8.002 8.002 0 1 1-1.6 5.685.75.75 0 1 1 1.493-.154 6.5 6.5 0 1 0 1.18-4.458l1.358 1.358A.25.25 0 0 1 3.896 6H.25A.25.25 0 0 1 0 5.75V2.104a.25.25 0 0 1 .427-.177ZM7.75 4a.75.75 0 0 1 .75.75v2.992l2.028.812a.75.75 0 0 1-.557 1.392l-2.5-1A.751.751 0 0 1 7 8.25v-3.5A.75.75 0 0 1 7.75 4Z",
    "pr": "M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Z",
    "issue": "M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z",
    "repo": "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z",
    "code": "m11.28 3.22 4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.749.749 0 0 1-1.275-.326.749.749 0 0 1 .215-.734L13.94 8l-3.72-3.72a.749.749 0 0 1 .326-1.275.749.749 0 0 1 .734.215Zm-6.56 0a.751.751 0 0 1 1.042.018.751.751 0 0 1 .018 1.042L2.06 8l3.72 3.72a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215L.47 8.53a.75.75 0 0 1 0-1.06Z",
    "rocket": "M14.064 0h.186C15.216 0 16 .784 16 1.75v.186a8.752 8.752 0 0 1-2.564 6.186l-.458.459c-.314.314-.641.616-.979.904v3.207c0 .608-.315 1.172-.833 1.49l-2.774 1.707a.749.749 0 0 1-1.11-.418l-.954-3.102a1.214 1.214 0 0 1-.145-.125L3.754 9.816a1.218 1.218 0 0 1-.124-.145L.528 8.717a.749.749 0 0 1-.418-1.11l1.71-2.774A1.748 1.748 0 0 1 3.31 4h3.204c.288-.338.59-.665.904-.979l.459-.458A8.749 8.749 0 0 1 14.064 0ZM8.938 3.623h-.002l-.458.458c-.76.76-1.437 1.598-2.02 2.5l-1.5 2.317 2.143 2.143 2.317-1.5c.902-.583 1.74-1.26 2.499-2.02l.459-.458a7.25 7.25 0 0 0 2.123-5.127V1.75a.25.25 0 0 0-.25-.25h-.186a7.249 7.249 0 0 0-5.125 2.123ZM3.56 14.56c-.732.732-2.334 1.045-3.005 1.148a.234.234 0 0 1-.201-.064.234.234 0 0 1-.064-.201c.103-.671.416-2.273 1.15-3.003a1.502 1.502 0 1 1 2.12 2.12Zm6.94-3.935c-.088.06-.177.118-.266.175l-2.35 1.521.548 1.783 1.949-1.2a.25.25 0 0 0 .119-.213ZM3.678 8.116 5.2 5.766c.058-.09.117-.178.176-.266H3.309a.25.25 0 0 0-.213.119l-1.2 1.95ZM12 5a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z",
    "flame": "M9.533.753V.752c.217 2.385 1.463 3.626 2.653 4.81C13.37 6.74 14.498 7.863 14.498 10c0 3.5-3 6-6.5 6S1.5 13.512 1.5 10c0-1.298.536-2.56 1.425-3.286.376-.308.862 0 1.035.454C4.46 8.487 5.581 8.419 6 8c.282-.282.341-.811-.003-1.5C4.34 3.187 7.035.75 8.77.146c.39-.137.726.194.763.607Z",
}

FADE = ("@keyframes fadein{from{opacity:0}to{opacity:1}}"
        "@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
        "@keyframes pop{0%{font-size:3px;opacity:.2}80%{font-size:34px;opacity:1}100%{font-size:28px;opacity:1}}"
        "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
        "@keyframes ring{from{stroke-dashoffset:252}to{stroke-dashoffset:0}}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important;opacity:1!important}}")


def anim(name, delay, dur=0.5, ease="cubic-bezier(.2,.7,.3,1)"):
    return f'style="opacity:0;animation:{name} {dur}s {ease} forwards {delay:.2f}s"'


# ---------------------------------------------------------------- streak
STREAK = {
    "dark": dict(bg="#0A101F", stroke="#22D3EE", ring="#A78BFA", fire="#10B981", label="#22D3EE",
                 side="#94A3B8", num="#F8FAFC", dates="#64748B"),
    "light": dict(bg="#FFFFFF", stroke="#0891B2", ring="#7C3AED", fire="#059669", label="#0891B2",
                  side="#475569", num="#0F172A", dates="#94A3B8"),
}


def streak_card(d, theme, W=1180, H=195):
    c, s = STREAK[theme], d["streak"]
    cx = [W / 6, W / 2, 5 * W / 6]
    cur = s["current_range"]
    cur_txt = fmt_date(cur[0]) if cur[0] == cur[1] else f"{fmt_date(cur[0])} - {fmt_date(cur[1])}"
    lng = s["longest_range"]
    lng_txt = fmt_date(lng[0]) if lng[0] == lng[1] else f"{fmt_date(lng[0])} - {fmt_date(lng[1])}"
    t = lambda x, y, txt, fill, size, weight, a: (
        f'<text x="{x:.1f}" y="{y}" text-anchor="middle" fill="{fill}" font-size="{size}" '
        f'font-weight="{weight}" {a}>{esc(txt)}</text>')
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="{SANS}" role="img" aria-label="Contribution streak">',
         f'<style>{FADE}</style>',
         f'<defs><mask id="m"><rect x="-50" y="-40" width="100" height="100" fill="#fff"/>'
         f'<ellipse cx="0" cy="-40" rx="20" ry="15" fill="#000"/></mask></defs>',
         f'<rect width="{W}" height="{H}" rx="4.5" fill="{c["bg"]}"/>',
         f'<line x1="{W / 3:.1f}" y1="28" x2="{W / 3:.1f}" y2="170" stroke="{c["stroke"]}" stroke-width="1"/>',
         f'<line x1="{2 * W / 3:.1f}" y1="28" x2="{2 * W / 3:.1f}" y2="170" stroke="{c["stroke"]}" stroke-width="1"/>']
    # total
    o += [t(cx[0], 80, f'{s["total"]:,}', c["num"], 28, 700, anim("rise", 0.6)),
          t(cx[0], 116, "Total Contributions", c["side"], 14, 400, anim("fadein", 0.7)),
          t(cx[0], 146, f'{fmt_date(s["first_day"], True)} - Present', c["dates"], 12, 400, anim("fadein", 0.8))]
    # current (ring + flame)
    o += [f'<g transform="translate({cx[1]:.1f},71)" mask="url(#m)"><circle r="40" fill="none" stroke="{c["ring"]}" '
          f'stroke-width="5" stroke-dasharray="252" transform="rotate(-90)" '
          f'style="animation:ring 1.1s cubic-bezier(.4,0,.2,1) forwards .3s;stroke-dashoffset:252"/></g>',
          f'<g transform="translate({cx[1] - 12:.1f},7) scale(1.5)" {anim("fadein", 0.6)}>'
          f'<path d="{ICONS["flame"]}" fill="{c["fire"]}"/></g>',
          f'<text x="{cx[1]:.1f}" y="80" text-anchor="middle" fill="{c["num"]}" font-size="28" font-weight="700" '
          f'style="animation:pop .6s linear forwards">{s["current"]}</text>',
          t(cx[1], 140, "Current Streak", c["label"], 14, 700, anim("fadein", 0.9)),
          t(cx[1], 166, cur_txt, c["dates"], 12, 400, anim("fadein", 0.9))]
    # longest
    o += [t(cx[2], 80, f'{s["longest"]:,}', c["num"], 28, 700, anim("rise", 1.2)),
          t(cx[2], 116, "Longest Streak", c["side"], 14, 400, anim("fadein", 1.3)),
          t(cx[2], 146, lng_txt, c["dates"], 12, 400, anim("fadein", 1.4)), "</svg>"]
    return "\n".join(o)


# ---------------------------------------------------------------- stats
STATS = {
    "dark": dict(bg="#0A101F", title="#22D3EE", icon="#A78BFA", text="#94A3B8"),
    "light": dict(bg="#FFFFFF", title="#0891B2", icon="#7C3AED", text="#0F172A"),
}


def stats_card(d, theme, W=500, H=195):
    c, st = STATS[theme], d["stats"]
    first = st["name"].split()[0] if st["name"] else d["user"]
    # Rows chosen to describe the work, not popularity: stars/PR counts stay low on a
    # mostly-private portfolio and would undersell it.
    rows = [("history", "Total Commits:", st["commits"]),
            ("repo", "Public Repositories:", st["public_repos"]),
            ("code", "Languages Used:", st["languages_used"]),
            ("rocket", "Top Language:", st["top_language"]),
            ("star", "Contributed to (last year):", st["contributed_to"])]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="{SANS}" role="img" aria-label="{esc(first)} GitHub stats">',
         f'<style>{FADE}</style>',
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="4.5" fill="{c["bg"]}"/>',
         f'<text x="25" y="35" font-size="18" font-weight="600" fill="{c["title"]}" {anim("fadein", 0, 0.8)}>'
         f'{esc(st["name"])}\'s GitHub Stats</text>']
    for i, (icon, label, val) in enumerate(rows):
        y = 55 + i * 25
        shown = f"{val:,}" if isinstance(val, int) else esc(val)
        o.append(f'<g transform="translate(25,{y})"><g {anim("rise", 0.45 + 0.15 * i, 0.4)}>'
                 f'<path d="{ICONS[icon]}" fill="{c["icon"]}"/>'
                 f'<text x="25" y="12.5" font-size="14" font-weight="600" fill="{c["text"]}">{label}</text>'
                 f'<text x="230" y="12.5" font-size="14" font-weight="600" fill="{c["text"]}">{shown}</text></g></g>')
    o.append("</svg>")
    return "\n".join(o)


# ---------------------------------------------------------------- languages
def langs_card(d, theme, W=500, H=195, n=8):
    c = STATS[theme]
    items = sorted(d["languages"].items(), key=lambda kv: -kv[1])[:n]
    total = sum(v for _, v in items) or 1
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="{SANS}" role="img" aria-label="Most used languages">',
         f'<style>{FADE}</style>',
         f'<defs><clipPath id="bar"><rect x="25" y="55" width="450" height="8" rx="5"/></clipPath></defs>',
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="4.5" fill="{c["bg"]}"/>',
         f'<text x="25" y="35" font-size="18" font-weight="600" fill="{c["title"]}" {anim("fadein", 0, 0.8)}>'
         f'Most Used Languages</text>',
         f'<g clip-path="url(#bar)"><g style="transform-origin:25px 0;animation:grow 1s cubic-bezier(.4,0,.2,1) both .3s">']
    x = 25.0
    for name, v in items:
        w = 450 * v / total
        o.append(f'<rect x="{x:.2f}" y="55" width="{w + 0.5:.2f}" height="8" fill="{lang_color(name)}"/>')
        x += w
    o.append("</g></g>")
    for i, (name, v) in enumerate(items):
        col, row = i % 2, i // 2
        o.append(f'<g transform="translate({25 + col * 230},{80 + row * 25})"><g {anim("rise", 0.45 + 0.1 * i, 0.4)}>'
                 f'<circle cx="5" cy="6" r="5" fill="{lang_color(name)}"/>'
                 f'<text x="15" y="10" font-size="11" fill="{c["text"]}">{esc(name)} {100 * v / total:.2f}%</text></g></g>')
    o.append("</svg>")
    return "\n".join(o)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "dist"
    d = load_data()
    for theme in ("dark", "light"):
        write(out, f"streak-{theme}.svg", streak_card(d, theme))
        write(out, f"stats-{theme}.svg", stats_card(d, theme))
        write(out, f"langs-{theme}.svg", langs_card(d, theme))


if __name__ == "__main__":
    main()
