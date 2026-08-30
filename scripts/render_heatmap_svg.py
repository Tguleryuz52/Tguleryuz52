#!/usr/bin/env python3
"""
Render data/contributions.json as an animated, terminal-styled contribution heatmap SVG.
"""
import datetime
import json
import os
import sys

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "contrib-heatmap.svg")

# Palette matching GitHub dark mode green ramp
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

def get_color(count):
    if count == 0:
        return PALETTE[0]
    elif count <= 2:
        return PALETTE[1]
    elif count <= 5:
        return PALETTE[2]
    elif count <= 9:
        return PALETTE[3]
    elif count <= 15:
        return PALETTE[4]
    else:
        return PALETTE[5]

def main():
    if not os.path.exists(DATA_PATH):
        print(f"data file not found: {DATA_PATH}. Run fetch_contributions.py first.", file=sys.stderr)
        sys.exit(1)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    days = data.get("days", [])
    total = data.get("total_contributions", 0)
    current_streak = data.get("current_streak", 0)
    longest_streak = data.get("longest_streak", 0)

    # Grid constants
    CELL_SIZE = 11
    GAP = 3
    RADIUS = 2
    PAD_X = 25
    PAD_TOP = 40
    PAD_BOTTOM = 45

    # Group days into weeks (53 columns x 7 rows)
    weeks = []
    current_week = []
    
    # Pad first week if needed
    if days:
        first_date = datetime.date.fromisoformat(days[0]["date"])
        # Sunday=0, Monday=1, ..., Saturday=6
        weekday = (first_date.weekday() + 1) % 7
        for _ in range(weekday):
            current_week.append(None)

    for d in days:
        current_week.append(d)
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []

    if current_week:
        while len(current_week) < 7:
            current_week.append(None)
        weeks.append(current_week)

    # Trim or ensure 53 weeks
    weeks = weeks[-53:]

    grid_w = len(weeks) * (CELL_SIZE + GAP) - GAP
    grid_h = 7 * (CELL_SIZE + GAP) - GAP
    canvas_w = grid_w + PAD_X * 2
    canvas_h = grid_h + PAD_TOP + PAD_BOTTOM

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" width="{canvas_w}" height="{canvas_h}">')
    svg_parts.append('<style>')
    svg_parts.append('''
        .bg { fill: #0d1117; stroke: #30363d; stroke-width: 1; rx: 8px; }
        .text { font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 11px; fill: #8b949e; }
        .text-bold { font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 12px; font-weight: 600; fill: #c9d1d9; }
        .cell { rx: 2px; ry: 2px; transition: all 0.2s ease; }
        @keyframes reveal {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .anim-cell {
            animation: reveal 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            opacity: 0;
        }
    ''')
    svg_parts.append('</style>')

    # Background card
    svg_parts.append(f'<rect class="bg" x="0.5" y="0.5" width="{canvas_w - 1}" height="{canvas_h - 1}" />')

    # Title & Header
    svg_parts.append(f'<text class="text-bold" x="{PAD_X}" y="25">Contributions Calendar</text>')
    svg_parts.append(f'<text class="text" x="{canvas_w - PAD_X}" y="25" text-anchor="end">{total:,} contributions in the last year</text>')

    # Contribution Grid
    for w_idx, week in enumerate(weeks):
        for d_idx, day in enumerate(week):
            if day is None:
                continue
            x = PAD_X + w_idx * (CELL_SIZE + GAP)
            y = PAD_TOP + d_idx * (CELL_SIZE + GAP)
            color = get_color(day["count"])
            delay = (w_idx * 0.015) + (d_idx * 0.008)
            svg_parts.append(
                f'<rect class="cell anim-cell" x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
                f'fill="{color}" style="animation-delay: {delay:.3f}s;"><title>{day["date"]}: {day["count"]} contributions</title></rect>'
            )

    # Footer: Legend + Streaks
    foot_y = PAD_TOP + grid_h + 26
    svg_parts.append(f'<text class="text" x="{PAD_X}" y="{foot_y}">🔥 Current streak: <tspan class="text-bold">{current_streak} days</tspan> · Longest: <tspan class="text-bold">{longest_streak} days</tspan></text>')

    # Less -> More Legend
    legend_x = canvas_w - PAD_X - (6 * (CELL_SIZE + GAP)) - 35
    svg_parts.append(f'<text class="text" x="{legend_x - 6}" y="{foot_y}" text-anchor="end">Less</text>')
    for i, c in enumerate(PALETTE):
        lx = legend_x + i * (CELL_SIZE + GAP)
        ly = foot_y - 9
        svg_parts.append(f'<rect class="cell" x="{lx}" y="{ly}" width="{CELL_SIZE}" height="{CELL_SIZE}" fill="{c}" />')
    svg_parts.append(f'<text class="text" x="{legend_x + 6 * (CELL_SIZE + GAP) + 4}" y="{foot_y}">More</text>')

    svg_parts.append('</svg>')

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_parts))
    print(f"rendered {OUT_PATH} ({canvas_w}x{canvas_h})")

if __name__ == "__main__":
    main()
