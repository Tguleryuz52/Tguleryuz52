#!/usr/bin/env python3
"""
Generate a neofetch-style terminal info card SVG with line-by-line animated reveal.
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
    .cmd {{ font-size: 13px; font-weight: 600; fill: #58a6ff; }}
    .prompt-sym {{ fill: #7ee787; }}
    .divider {{ stroke: #30363d; stroke-width: 1; stroke-dasharray: 4 2; }}
    
    .key {{ font-size: 12px; font-weight: 700; fill: #79c0ff; }}
    .val {{ font-size: 12px; fill: #c9d1d9; }}
    .val-dim {{ font-size: 11px; fill: #8b949e; }}
    .bullet {{ font-size: 11px; fill: #d2a8ff; font-weight: 600; }}
    .highlight-name {{ font-size: 11px; font-weight: 700; fill: #ffa657; }}
    .highlight-desc {{ font-size: 11px; fill: #c9d1d9; }}
    
    @keyframes lineFade {{
      from {{ opacity: 0; transform: translateX(-6px); }}
      to {{ opacity: 1; transform: translateX(0); }}
    }}
    .anim-line {{
      animation: lineFade 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      opacity: 0;
    }}
  </style>

  <!-- Window Container -->
  <rect class="bg" x="0.5" y="0.5" width="{CANVAS_W - 1}" height="{CANVAS_H - 1}" />
  
  <!-- Titlebar -->
  <path d="M 0.5 8.5 A 8 8 0 0 1 8.5 0.5 L {CANVAS_W - 8.5} 0.5 A 8 8 0 0 1 {CANVAS_W - 0.5} 8.5 L {CANVAS_W - 0.5} 28.5 L 0.5 28.5 Z" class="title-bar" />
  <circle class="dot-red" cx="18" cy="14.5" r="4.5" />
  <circle class="dot-yellow" cx="32" cy="14.5" r="4.5" />
  <circle class="dot-green" cx="46" cy="14.5" r="4.5" />
  <text class="term-title" x="{CANVAS_W / 2}" y="18">talha@terminal:~ (neofetch)</text>

  <g transform="translate(24, 52)">
    <!-- Command Prompt -->
    <g class="anim-line" style="animation-delay: 0.05s;">
      <text class="font-mono cmd" x="0" y="0"><tspan class="prompt-sym">talha@github</tspan> ~ $ neofetch</text>
      <line class="divider" x1="0" y1="12" x2="442" y2="12" />
    </g>

    <!-- Info Block -->
    <g class="anim-line font-mono" style="animation-delay: 0.15s;" transform="translate(0, 32)">
      <text class="key" x="0" y="0">Role</text>
      <text class="val" x="90" y="0">: Software Developer &amp; Product Builder</text>
    </g>
    <g class="anim-line font-mono" style="animation-delay: 0.22s;" transform="translate(0, 52)">
      <text class="key" x="0" y="0">Now</text>
      <text class="val" x="90" y="0">: Logistics Tech &amp; AI-Augmented Systems</text>
    </g>
    <g class="anim-line font-mono" style="animation-delay: 0.29s;" transform="translate(0, 72)">
      <text class="key" x="0" y="0">Focus</text>
      <text class="val" x="90" y="0">: Full-Stack, UI/UX, AI Integrations, 3D</text>
    </g>
    <g class="anim-line font-mono" style="animation-delay: 0.36s;" transform="translate(0, 92)">
      <text class="key" x="0" y="0">Edu</text>
      <text class="val" x="90" y="0">: IKU (Visual Comm. &amp; Comp. Programming)</text>
    </g>

    <!-- Stack Section -->
    <g class="anim-line font-mono" style="animation-delay: 0.45s;" transform="translate(0, 122)">
      <text class="key" x="0" y="0">Frontend</text>
      <text class="val" x="90" y="0">: Next.js, React, TypeScript, Tailwind, Motion</text>
    </g>
    <g class="anim-line font-mono" style="animation-delay: 0.52s;" transform="translate(0, 142)">
      <text class="key" x="0" y="0">Backend</text>
      <text class="val" x="90" y="0">: Node.js, Python (FastAPI), Supabase, SQL</text>
    </g>
    <g class="anim-line font-mono" style="animation-delay: 0.59s;" transform="translate(0, 162)">
      <text class="key" x="0" y="0">AI / ML</text>
      <text class="val" x="90" y="0">: Gemini API, Claude API, Multi-Agent, RAG</text>
    </g>
    <g class="anim-line font-mono" style="animation-delay: 0.66s;" transform="translate(0, 182)">
      <text class="key" x="0" y="0">Design/3D</text>
      <text class="val" x="90" y="0">: Figma, Fusion 360, Blender, UE5 (C++/GAS)</text>
    </g>

    <!-- Highlights Section -->
    <g class="anim-line font-mono" style="animation-delay: 0.75s;" transform="translate(0, 212)">
      <line class="divider" x1="0" y1="-8" x2="442" y2="-8" />
      <text class="key" x="0" y="6">&gt; Highlights</text>
    </g>

    <g class="anim-line font-mono" style="animation-delay: 0.82s;" transform="translate(0, 236)">
      <text class="bullet" x="4" y="0">•</text>
      <text class="highlight-name" x="18" y="0">Bioos:</text>
      <text class="highlight-desc" x="65" y="0">7-Stage Medical AI Analysis (Full-Stack)</text>
    </g>
    <g class="anim-line font-mono" style="animation-delay: 0.89s;" transform="translate(0, 254)">
      <text class="bullet" x="4" y="0">•</text>
      <text class="highlight-name" x="18" y="0">Feron:</text>
      <text class="highlight-desc" x="65" y="0">AI Wardrobe (Next.js + Gemini + WASM)</text>
    </g>
    <g class="anim-line font-mono" style="animation-delay: 0.96s;" transform="translate(0, 272)">
      <text class="bullet" x="4" y="0">•</text>
      <text class="highlight-name" x="18" y="0">Robotoy:</text>
      <text class="highlight-desc" x="78" y="0">AI Robot (ANTSPARK 3rd · TÜBİTAK Support)</text>
    </g>
    <g class="anim-line font-mono" style="animation-delay: 1.03s;" transform="translate(0, 290)">
      <text class="bullet" x="4" y="0">•</text>
      <text class="highlight-name" x="18" y="0">Asset:</text>
      <text class="highlight-desc" x="60" y="0">Teknofest Smart Tour (Top 14 / 4,250)</text>
    </g>

    <!-- Color Palette Blocks -->
    <g class="anim-line" style="animation-delay: 1.15s;" transform="translate(0, 320)">
      <rect x="0" y="0" width="22" height="12" rx="2" fill="#ff5f56" />
      <rect x="26" y="0" width="22" height="12" rx="2" fill="#ffbd2e" />
      <rect x="52" y="0" width="22" height="12" rx="2" fill="#27c93f" />
      <rect x="78" y="0" width="22" height="12" rx="2" fill="#58a6ff" />
      <rect x="104" y="0" width="22" height="12" rx="2" fill="#bc8cff" />
      <rect x="130" y="0" width="22" height="12" rx="2" fill="#7ee787" />
      <rect x="156" y="0" width="22" height="12" rx="2" fill="#c9d1d9" />
    </g>
  </g>
</svg>
'''
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg.strip())
    print(f"generated {OUT_PATH}")

if __name__ == "__main__":
    main()
