#!/usr/bin/env python3
"""
make_info_card.py
Generates info-card.svg:
- 490px width terminal window with macOS/Linux style window dots
- Title prompt: <username>@github ~ $ neofetch
- Key/Value rows: Now, Prev, Stack, Highlights
- Staggered line-by-line fade and slide-up animation (CSS keyframes, plays once, freezes)
- Supports STATIC=1 env var for static preview
"""

import sys
import os
import json
import xml.sax.saxutils as saxutils

def escape(text: str) -> str:
    return saxutils.escape(text)

def wrap_text(text: str, max_width: int = 42) -> list[str]:
    """Wraps text into chunks of at most max_width chars on word boundaries."""
    words = text.split()
    lines = []
    current_line = []
    current_len = 0

    for w in words:
        if current_len + len(w) + (1 if current_line else 0) <= max_width:
            current_line.append(w)
            current_len += len(w) + (1 if len(current_line) > 1 else 0)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [w]
            current_len = len(w)

    if current_line:
        lines.append(" ".join(current_line))

    return lines or [""]

def generate_info_card(config_path="data/profile_config.json", out_path="info-card.svg"):
    config = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

    username = config.get("github_username", "itsmayankmis")
    info = config.get("info_card", {})
    title = info.get("title", f"{username}@github ~ $ neofetch")
    now_val = info.get("now", "Building autonomous AI agents & interactive developer tools")
    prev_val = info.get("prev", "Software Engineering & Computer Science")
    stack_val = info.get("stack", "Python, TypeScript, React, Next.js, Docker, Linux, Git")
    highlights = info.get("highlights", [
        "Engineered automated terminal-first SVG pipelines",
        "Specialized in LLM agent orchestration & tooling",
        "Passionate about modern UX and open source"
    ])

    is_static = os.environ.get("STATIC", "0") == "1"

    width = 490
    title_bar_height = 36

    # We will build structured lines for the terminal output
    # Each entry: { "key": str, "value": str, "is_header": bool, "is_bullet": bool }
    raw_sections = [
        {"type": "banner", "text": f"{username}@github"},
        {"type": "separator", "text": "─" * 38},
        {"type": "kv", "key": "Now", "value": now_val},
        {"type": "kv", "key": "Prev", "value": prev_val},
        {"type": "kv", "key": "Stack", "value": stack_val},
        {"type": "header", "text": "Highlights:"},
    ]
    for h in highlights:
        raw_sections.append({"type": "bullet", "value": h})

    # Layout into renderable lines with wrapping
    render_lines = []
    key_width = 8 # characters for key label

    for item in raw_sections:
        itype = item["type"]
        if itype == "banner":
            render_lines.append({
                "type": "banner",
                "text": item["text"]
            })
        elif itype == "separator":
            render_lines.append({
                "type": "separator",
                "text": item["text"]
            })
        elif itype == "header":
            render_lines.append({
                "type": "header",
                "text": item["text"]
            })
        elif itype == "kv":
            k = item["key"]
            val_wrapped = wrap_text(item["value"], max_width=40)
            for idx, line_text in enumerate(val_wrapped):
                if idx == 0:
                    render_lines.append({
                        "type": "kv_first",
                        "key": f"{k}:".ljust(key_width),
                        "value": line_text
                    })
                else:
                    render_lines.append({
                        "type": "kv_cont",
                        "indent": " " * key_width,
                        "value": line_text
                    })
        elif itype == "bullet":
            b_wrapped = wrap_text(item["value"], max_width=42)
            for idx, line_text in enumerate(b_wrapped):
                if idx == 0:
                    render_lines.append({
                        "type": "bullet_first",
                        "bullet": "• ",
                        "value": line_text
                    })
                else:
                    render_lines.append({
                        "type": "bullet_cont",
                        "indent": "  ",
                        "value": line_text
                    })

    # Calculate height
    line_height = 20.5
    content_start_y = title_bar_height + 26
    height = int(content_start_y + (len(render_lines) * line_height) + 16)

    # CSS styles
    css_lines = [
        "svg { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Courier New', monospace; }",
        ".window-title { font-size: 11.5px; fill: #8b949e; font-weight: 500; }",
        ".banner-text { font-size: 13.5px; font-weight: bold; fill: #58a6ff; }",
        ".sep-text { font-size: 11px; fill: #30363d; }",
        ".key-text { font-size: 12.5px; font-weight: 600; fill: #79c0ff; }",
        ".val-text { font-size: 12.5px; fill: #c9d1d9; }",
        ".header-text { font-size: 12.5px; font-weight: 600; fill: #d2a8ff; }",
        ".bullet-symbol { font-size: 12.5px; fill: #7ee787; font-weight: bold; }",
    ]

    if not is_static:
        css_lines.extend([
            "@keyframes lineSlideUp {",
            "  0% { opacity: 0; transform: translateY(6px); }",
            "  100% { opacity: 1; transform: translateY(0); }",
            "}",
            ".term-line {",
            "  opacity: 0;",
            "  animation: lineSlideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;",
            "}"
        ])
    else:
        css_lines.append(".term-line { opacity: 1; }")

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    svg_parts.append('  <style>')
    for l in css_lines:
        svg_parts.append(f'    {l}')
    svg_parts.append('  </style>')

    # Window container
    svg_parts.append(f'  <rect width="{width}" height="{height}" rx="8" fill="#0d1117" stroke="#30363d" stroke-width="1"/>')

    # Window Title Bar
    svg_parts.append(f'  <path d="M 0 8 A 8 8 0 0 1 8 0 L {width-8} 0 A 8 8 0 0 1 {width} 8 L {width} {title_bar_height} L 0 {title_bar_height} Z" fill="#161b22"/>')
    svg_parts.append(f'  <line x1="0" y1="{title_bar_height}" x2="{width}" y2="{title_bar_height}" stroke="#30363d" stroke-width="1"/>')

    # Window control dots (mac style)
    svg_parts.append('  <circle cx="18" cy="18" r="5.5" fill="#ff5f56"/>')
    svg_parts.append('  <circle cx="36" cy="18" r="5.5" fill="#ffbd2e"/>')
    svg_parts.append('  <circle cx="54" cy="18" r="5.5" fill="#27c93f"/>')

    # Title
    svg_parts.append(f'  <text x="74" y="22" class="window-title">{escape(title)}</text>')

    # Render lines
    base_delay = 0.15
    stagger = 0.12 # seconds per line

    for idx, line in enumerate(render_lines):
        y = content_start_y + (idx * line_height)
        delay_s = base_delay + (idx * stagger)
        style_attr = f' style="animation-delay: {delay_s:.2f}s;"' if not is_static else ''

        ltype = line["type"]
        if ltype == "banner":
            svg_parts.append(f'  <g class="term-line"{style_attr}>')
            svg_parts.append(f'    <text x="24" y="{y:.1f}" class="banner-text">{escape(line["text"])}</text>')
            svg_parts.append('  </g>')
        elif ltype == "separator":
            svg_parts.append(f'  <g class="term-line"{style_attr}>')
            svg_parts.append(f'    <text x="24" y="{y:.1f}" class="sep-text">{escape(line["text"])}</text>')
            svg_parts.append('  </g>')
        elif ltype == "header":
            svg_parts.append(f'  <g class="term-line"{style_attr}>')
            svg_parts.append(f'    <text x="24" y="{y:.1f}" class="header-text">{escape(line["text"])}</text>')
            svg_parts.append('  </g>')
        elif ltype == "kv_first":
            svg_parts.append(f'  <g class="term-line"{style_attr}>')
            svg_parts.append(f'    <text x="24" y="{y:.1f}" xml:space="preserve"><tspan class="key-text">{escape(line["key"])}</tspan><tspan class="val-text">{escape(line["value"])}</tspan></text>')
            svg_parts.append('  </g>')
        elif ltype == "kv_cont":
            svg_parts.append(f'  <g class="term-line"{style_attr}>')
            svg_parts.append(f'    <text x="24" y="{y:.1f}" xml:space="preserve"><tspan class="val-text">{escape(line["indent"])}{escape(line["value"])}</tspan></text>')
            svg_parts.append('  </g>')
        elif ltype == "bullet_first":
            svg_parts.append(f'  <g class="term-line"{style_attr}>')
            svg_parts.append(f'    <text x="24" y="{y:.1f}" xml:space="preserve"><tspan class="bullet-symbol">{escape(line["bullet"])}</tspan><tspan class="val-text">{escape(line["value"])}</tspan></text>')
            svg_parts.append('  </g>')
        elif ltype == "bullet_cont":
            svg_parts.append(f'  <g class="term-line"{style_attr}>')
            svg_parts.append(f'    <text x="24" y="{y:.1f}" xml:space="preserve"><tspan class="val-text">{escape(line["indent"])}{escape(line["value"])}</tspan></text>')
            svg_parts.append('  </g>')

    svg_parts.append('</svg>')

    content = "\n".join(svg_parts) + "\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully generated {out_path} ({len(content)} bytes, {width}x{height}px, static={is_static}).")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "info-card.svg"
    generate_info_card(out_path=out_file)
