#!/usr/bin/env python3
"""
Generate a neofetch-style terminal info card SVG with explicit absolute coordinates
so GitHub's image proxy renders every line crisply without stacking.
"""
import os

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "info-card.svg")

def main():
    CANVAS_W = 490
    CANVAS_H = 430

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" width="{CANVAS_W}" height="{CANVAS_H}">
  <style>
    .bg {{ fill: #0d1117; stroke: #30363d; stroke-width: 1; rx: 8px; }}
    .title-bar {{ fill: #161b22; rx: 8px 8px 0 0; }}
    .dot-red {{ fill: #ff5f56; }}
    .dot-yellow {{ fill: #ffbd2e; }}
    .dot-green {{ fill: #27c93f; }}
    .term-title {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 11px; fill: #8b949e; text-anchor: middle; }}
    
    .font-mono {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; }}
    .cmd {{ font-size: 12.5px; font-weight: 600; fill: #58a6ff; }}
    .prompt-sym {{ fill: #7ee787; }}
    .divider {{ stroke: #30363d; stroke-width: 1; stroke-dasharray: 4 2; }}
    
    .key {{ font-size: 11.5px; font-weight: 700; fill: #79c0ff; }}
    .val {{ font-size: 11.5px; fill: #c9d1d9; }}
    .val-highlight {{ font-size: 11.5px; fill: #58a6ff; font-weight: 600; }}
    .bullet {{ font-size: 11px; fill: #d2a8ff; font-weight: bold; }}
    .highlight-name {{ font-size: 11px; font-weight: 700; fill: #ffa657; }}
    .highlight-desc {{ font-size: 11px; fill: #c9d1d9; }}

    @keyframes fadeIn {{
      from {{ opacity: 0; }}
      to {{ opacity: 1; }}
    }}
    .anim {{
      animation: fadeIn 0.4s ease forwards;
    }}
  </style>

  <!-- Container -->
  <rect class="bg" x="0.5" y="0.5" width="{CANVAS_W - 1}" height="{CANVAS_H - 1}" />
  
  <!-- Titlebar -->
  <path d="M 0.5 8.5 A 8 8 0 0 1 8.5 0.5 L {CANVAS_W - 8.5} 0.5 A 8 8 0 0 1 {CANVAS_W - 0.5} 8.5 L {CANVAS_W - 0.5} 28.5 L 0.5 28.5 Z" class="title-bar" />
  <circle class="dot-red" cx="18" cy="14.5" r="4.5" />
  <circle class="dot-yellow" cx="32" cy="14.5" r="4.5" />
  <circle class="dot-green" cx="46" cy="14.5" r="4.5" />
  <text class="term-title" x="{CANVAS_W / 2}" y="18">talha@terminal:~ (neofetch)</text>

  <!-- Command Prompt -->
  <text class="font-mono cmd anim" x="22" y="52"><tspan class="prompt-sym">talha@github</tspan> ~ $ neofetch</text>
  <line class="divider" x1="22" y1="62" x2="468" y2="62" />

  <!-- Info Rows with explicit absolute Y coordinates -->
  <text class="font-mono anim" x="22" y="84">
    <tspan class="key">Role</tspan>
    <tspan class="val" x="110">: Software Developer &amp; Product Builder</tspan>
  </text>

  <text class="font-mono anim" x="22" y="104">
    <tspan class="key">Now</tspan>
    <tspan class="val-highlight" x="110">: Logistics Tech &amp; AI-Augmented Systems</tspan>
  </text>

  <text class="font-mono anim" x="22" y="124">
    <tspan class="key">Focus</tspan>
    <tspan class="val" x="110">: Full-Stack · UI/UX · AI Integration · 3D</tspan>
  </text>

  <text class="font-mono anim" x="22" y="144">
    <tspan class="key">Edu</tspan>
    <tspan class="val" x="110">: IKU (Visual Comm. &amp; Comp. Programming)</tspan>
  </text>

  <!-- Stack Rows -->
  <line class="divider" x1="22" y1="158" x2="468" y2="158" />

  <text class="font-mono anim" x="22" y="178">
    <tspan class="key">Frontend</tspan>
    <tspan class="val" x="110">: Next.js, React, TypeScript, Tailwind, Motion</tspan>
  </text>

  <text class="font-mono anim" x="22" y="198">
    <tspan class="key">Backend</tspan>
    <tspan class="val" x="110">: Node.js, Python (FastAPI), Supabase, SQL</tspan>
  </text>

  <text class="font-mono anim" x="22" y="218">
    <tspan class="key">AI / ML</tspan>
    <tspan class="val" x="110">: Gemini API, Claude API, Multi-Agent, RAG</tspan>
  </text>

  <text class="font-mono anim" x="22" y="238">
    <tspan class="key">Design/3D</tspan>
    <tspan class="val" x="110">: Figma, Fusion 360, Blender, UE5 (GAS)</tspan>
  </text>

  <!-- Highlights -->
  <line class="divider" x1="22" y1="252" x2="468" y2="252" />

  <text class="font-mono anim" x="22" y="272">
    <tspan class="bullet">•</tspan>
    <tspan class="highlight-name" x="38">Bioos:</tspan>
    <tspan class="highlight-desc" x="90">7-Stage Medical AI Analysis (Full-Stack)</tspan>
  </text>

  <text class="font-mono anim" x="22" y="292">
    <tspan class="bullet">•</tspan>
    <tspan class="highlight-name" x="38">Feron:</tspan>
    <tspan class="highlight-desc" x="90">AI Digital Wardrobe (Next.js + Gemini + WASM)</tspan>
  </text>

  <text class="font-mono anim" x="22" y="312">
    <tspan class="bullet">•</tspan>
    <tspan class="highlight-name" x="38">Robotoy:</tspan>
    <tspan class="highlight-desc" x="100">AI Robot (ANTSPARK 3rd · TÜBİTAK Supported)</tspan>
  </text>

  <text class="font-mono anim" x="22" y="332">
    <tspan class="bullet">•</tspan>
    <tspan class="highlight-name" x="38">Asset:</tspan>
    <tspan class="highlight-desc" x="85">Teknofest Smart Tour (Top 14 in 4,250)</tspan>
  </text>

  <!-- Terminal Color Palette Blocks -->
  <rect x="22" y="365" width="26" height="14" rx="3" fill="#ff5f56" />
  <rect x="54" y="365" width="26" height="14" rx="3" fill="#ffbd2e" />
  <rect x="86" y="365" width="26" height="14" rx="3" fill="#27c93f" />
  <rect x="118" y="365" width="26" height="14" rx="3" fill="#58a6ff" />
  <rect x="150" y="365" width="26" height="14" rx="3" fill="#bc8cff" />
  <rect x="182" y="365" width="26" height="14" rx="3" fill="#7ee787" />
  <rect x="214" y="365" width="26" height="14" rx="3" fill="#c9d1d9" />
  <rect x="246" y="365" width="26" height="14" rx="3" fill="#30363d" />
</svg>
'''
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg.strip())
    print(f"generated {OUT_PATH}")

if __name__ == "__main__":
    main()
