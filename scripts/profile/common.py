"""Shared palette + helpers for the generated README cards (matches the hero banner)."""
import datetime as dt
import html
import json
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "'Segoe UI',Ubuntu,'Helvetica Neue',Sans-Serif"

THEMES = {
    "dark": {
        "BG": "#0A101F", "PANEL": "#0C1426", "PANEL_BAR": "#0B1222",
        "CYAN": "#22D3EE", "VIOLET": "#A78BFA", "VIOLET2": "#7C3AED", "EMERALD": "#10B981",
        "TEXT": "#F8FAFC", "MUTED": "#94A3B8", "DIM": "#475569", "DATES": "#64748B",
        "STROKE_LO": "rgba(34,211,238,0.22)", "STROKE_HI": "rgba(34,211,238,0.5)",
        "BARLINE": "rgba(255,255,255,0.08)", "RING_BG": "rgba(148,163,184,0.15)",
        "PILL_BG": "rgba(124,58,237,0.28)", "PILL_STROKE": "rgba(167,139,250,0.5)", "MONO_TX": "#EDE9FE",
    },
    "light": {
        "BG": "#FFFFFF", "PANEL": "#FFFFFF", "PANEL_BAR": "#F1F5F9",
        "CYAN": "#0891B2", "VIOLET": "#7C3AED", "VIOLET2": "#7C3AED", "EMERALD": "#059669",
        "TEXT": "#0F172A", "MUTED": "#475569", "DIM": "#94A3B8", "DATES": "#94A3B8",
        "STROKE_LO": "rgba(8,145,178,0.20)", "STROKE_HI": "rgba(8,145,178,0.55)",
        "BARLINE": "rgba(0,0,0,0.08)", "RING_BG": "rgba(100,116,139,0.20)",
        "PILL_BG": "rgba(124,58,237,0.12)", "PILL_STROKE": "rgba(124,58,237,0.4)", "MONO_TX": "#FFFFFF",
    },
}

# github/linguist colours for the languages that realistically show up here
LANG_COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5", "C++": "#f34b7d",
    "C": "#555555", "C#": "#178600", "HTML": "#e34c26", "CSS": "#663399", "SCSS": "#c6538c",
    "MDX": "#fcb32c", "Dart": "#00B4AB", "Shell": "#89e051", "PowerShell": "#012456",
    "CMake": "#DA3434", "Java": "#b07219", "Kotlin": "#A97BFF", "Swift": "#F05138",
    "Go": "#00ADD8", "Rust": "#dea584", "Vue": "#41b883", "Svelte": "#ff3e00",
    "Jupyter Notebook": "#DA5B0B", "Dockerfile": "#384d54", "GLSL": "#5686a5", "HLSL": "#aace60",
    "Lua": "#000080", "PHP": "#4F5D95", "Ruby": "#701516", "Batchfile": "#C1F12E",
}


def lang_color(name):
    return LANG_COLORS.get(name, "#8b949e")


def esc(s):
    return html.escape(str(s), quote=True)


def load_data():
    with open(os.path.join(ROOT, "data", "profile.json"), encoding="utf-8") as fh:
        return json.load(fh)


def fmt_date(iso, with_year=None):
    d = dt.date.fromisoformat(iso)
    if with_year is None:
        with_year = d.year != dt.date.today().year
    return d.strftime("%b %-d, %Y" if with_year else "%b %-d") if os.name != "nt" else \
        d.strftime("%b %#d, %Y" if with_year else "%b %#d")


def write(outdir, name, svg):
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, name), "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {name} ({len(svg.encode()) // 1024} KB)")
