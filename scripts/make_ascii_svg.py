#!/usr/bin/env python3
"""
make_ascii_svg.py
Converts source-prepped.png into an animated, terminal-styled ascii-portrait.svg:
- Fixed width = 370px, matching info-card.svg height (~344px)
- Downsampled grid with aspect ratio compensation
- Sparse-to-dense brightness ramp: " .`:-=+*cs#%@"
- Pure monochrome fill (#c9d1d9) on #0d1117 dark terminal background
- Mac/Linux terminal title bar with dots and "<username>@github ~ $ cat portrait.asc"
- SMIL clipPath wipe per row + traveling block cursor (█) that hides after each row
- Rows staggered top-to-bottom for ~3.2s total print time
- STATIC=1 support for non-animated / static freeze-frame preview
"""

import sys
import os
import json
import xml.sax.saxutils as saxutils
from PIL import Image
import numpy as np

RAMP = " .`:-=+*cs#%@"

def escape(text: str) -> str:
    return saxutils.escape(text)

def generate_ascii_svg(
    img_path="source-prepped.png",
    config_path="data/profile_config.json",
    out_path="ascii-portrait.svg"
):
    if not os.path.exists(img_path):
        print(f"Error: {img_path} not found. Run prep_photo.py first.", file=sys.stderr)
        sys.exit(1)

    username = "itsmayankmis"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                username = cfg.get("github_username", username)
        except Exception:
            pass

    is_static = os.environ.get("STATIC", "0") == "1"

    img = Image.open(img_path).convert("L")
    arr = np.array(img)

    # Detect subject bounding box to eliminate blank border
    mask = arr < 252
    y_indices, x_indices = np.where(mask)
    if len(y_indices) > 0:
        min_y, max_y = y_indices.min(), y_indices.max()
        min_x, max_x = x_indices.min(), x_indices.max()
        margin = 12
        crop_box = (
            max(0, min_x - margin),
            max(0, min_y - margin),
            min(img.width, max_x + margin),
            min(img.height, max_y + margin)
        )
        img = img.crop(crop_box)

    # Desired visual dimensions: 370px wide, 344px tall (matching info-card.svg)
    svg_width = 370
    svg_height = 344
    title_bar_height = 36

    content_top = title_bar_height + 12
    content_bottom = svg_height - 10
    content_height = content_bottom - content_top # 298px

    content_left = 16
    content_right = svg_width - 16
    content_width = content_right - content_left # 338px

    # Rows & Columns
    # Monospace characters in standard fonts have aspect ratio approx width/height = 0.55
    # To preserve subject proportions:
    # (cols * 0.55) / rows ≈ img.width / img.height
    rows = 48
    char_aspect = 0.55
    target_cols = int(rows * (img.width / img.height) / char_aspect)
    # Clamp cols to around 72 - 82
    cols = max(70, min(84, target_cols))

    resized = img.resize((cols, rows), Image.Resampling.LANCZOS)
    grid_data = np.array(resized)

    # Calculate exact character spacing
    char_w = content_width / cols
    row_h = content_height / rows
    font_size = row_h * 1.18

    # Generate ASCII lines
    ascii_rows = []
    ramp_len = len(RAMP)
    for r in range(rows):
        chars = []
        for c in range(cols):
            val = grid_data[r, c]
            # 255 = background -> RAMP[0] = ' '
            # 0 = darkest -> RAMP[-1] = '@'
            idx = int((255 - val) / 255.0 * (ramp_len - 1))
            chars.append(RAMP[idx])
        ascii_rows.append("".join(chars))

    # Timing configuration
    total_print_time = 3.2 # seconds
    stagger = total_print_time / rows # ~0.066s per row
    row_duration = 0.16 # duration for each row to wipe across

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">')

    # Styles
    css_lines = [
        "svg { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Courier New', monospace; }",
        ".window-title { font-size: 11.5px; fill: #8b949e; font-weight: 500; }",
        ".ascii-row { font-size: " + f"{font_size:.2f}px" + "; fill: #c9d1d9; font-weight: normal; }",
        ".cursor { font-size: " + f"{font_size:.2f}px" + "; fill: #58a6ff; font-weight: bold; }",
    ]
    svg_parts.append('  <style>')
    for l in css_lines:
        svg_parts.append(f'    {l}')
    svg_parts.append('  </style>')

    # Defs: Clip paths and cursor animations for each row
    if not is_static:
        svg_parts.append('  <defs>')
        for r in range(rows):
            start_t = r * stagger
            y_pos = content_top + (r * row_h)
            # Clip path expanding from width 0 to content_width
            svg_parts.append(f'    <clipPath id="rowclip_{r}">')
            svg_parts.append(f'      <rect x="{content_left}" y="{y_pos:.2f}" width="0" height="{row_h + 1:.2f}">')
            svg_parts.append(f'        <animate attributeName="width" from="0" to="{content_width:.2f}" dur="{row_duration:.3f}s" begin="{start_t:.3f}s" fill="freeze"/>')
            svg_parts.append('      </rect>')
            svg_parts.append('    </clipPath>')
        svg_parts.append('  </defs>')

    # Window container
    svg_parts.append(f'  <rect width="{svg_width}" height="{svg_height}" rx="8" fill="#0d1117" stroke="#30363d" stroke-width="1"/>')

    # Window Title Bar
    svg_parts.append(f'  <path d="M 0 8 A 8 8 0 0 1 8 0 L {svg_width-8} 0 A 8 8 0 0 1 {svg_width} 8 L {svg_width} {title_bar_height} L 0 {title_bar_height} Z" fill="#161b22"/>')
    svg_parts.append(f'  <line x1="0" y1="{title_bar_height}" x2="{svg_width}" y2="{title_bar_height}" stroke="#30363d" stroke-width="1"/>')

    # Window control dots (macOS style)
    svg_parts.append('  <circle cx="18" cy="18" r="5.5" fill="#ff5f56"/>')
    svg_parts.append('  <circle cx="36" cy="18" r="5.5" fill="#ffbd2e"/>')
    svg_parts.append('  <circle cx="54" cy="18" r="5.5" fill="#27c93f"/>')

    # Title text
    title_text = f"{username}@github ~ $ cat portrait.asc"
    svg_parts.append(f'  <text x="74" y="22" class="window-title">{escape(title_text)}</text>')

    # Content rows
    for r in range(rows):
        y_text = content_top + (r * row_h) + (row_h * 0.82)
        escaped_row = escape(ascii_rows[r])

        clip_attr = f' clip-path="url(#rowclip_{r})"' if not is_static else ''
        svg_parts.append(
            f'  <text x="{content_left}" y="{y_text:.2f}" class="ascii-row" xml:space="preserve" '
            f'textLength="{content_width:.2f}" lengthAdjust="spacingAndGlyphs"{clip_attr}>{escaped_row}</text>'
        )

        # Traveling cursor block riding the wipe edge
        if not is_static:
            start_t = r * stagger
            end_t = start_t + row_duration
            cursor_y = content_top + (r * row_h) + (row_h * 0.82)
            svg_parts.append(f'  <text x="{content_left}" y="{cursor_y:.2f}" class="cursor" opacity="0">█')
            svg_parts.append(f'    <animate attributeName="x" from="{content_left}" to="{content_right}" dur="{row_duration:.3f}s" begin="{start_t:.3f}s" fill="freeze"/>')
            svg_parts.append(f'    <set attributeName="opacity" to="1" begin="{start_t:.3f}s"/>')
            svg_parts.append(f'    <set attributeName="opacity" to="0" begin="{end_t:.3f}s"/>')
            svg_parts.append('  </text>')

    svg_parts.append('</svg>')

    content = "\n".join(svg_parts) + "\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully generated {out_path} ({len(content)} bytes, {cols}x{rows} grid, static={is_static}).")

if __name__ == "__main__":
    in_img = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    out_svg = sys.argv[2] if len(sys.argv) > 2 else "ascii-portrait.svg"
    generate_ascii_svg(in_img, out_path=out_svg)
