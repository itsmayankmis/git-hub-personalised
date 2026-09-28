#!/usr/bin/env python3
"""
render_heatmap_svg.py
Renders data/contributions.json into contrib-heatmap.svg with:
- 53 weeks x 7 days grid
- GitHub-ish green ramp with neon level 5
- Diagonal CSS slide-down animation (freezes on load, no looping)
- Less -> More legend & stats footer
- Support for STATIC=1 environment variable
"""

import sys
import os
import json
from datetime import datetime

PALETTE = [
    "#161b22", # 0: None / Background
    "#0e4429", # 1: Low
    "#006d32", # 2: Medium-Low
    "#26a641", # 3: Medium-High
    "#39d353", # 4: High
    "#69f0a0", # 5: Top-decile / Neon
]

def render_heatmap(data_path="data/contributions.json", out_path="contrib-heatmap.svg"):
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run fetch_contributions.py first.", file=sys.stderr)
        sys.exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    days = data.get("days", [])
    if not days:
        print(f"Error: No days found in {data_path}", file=sys.stderr)
        sys.exit(1)

    is_static = os.environ.get("STATIC", "0") == "1"

    total = data.get("total", 0)
    current_streak = data.get("stats", {}).get("current_streak", 0)
    longest_streak = data.get("stats", {}).get("longest_streak", 0)

    # Determine 90th percentile threshold for Level 5
    active_counts = [d["count"] for d in days if d["count"] > 0]
    top_threshold = 999999
    if active_counts:
        active_counts.sort()
        idx_90 = int(len(active_counts) * 0.90)
        top_threshold = max(active_counts[idx_90], 5)

    # Calculate grid coordinates
    grid = []
    week_idx = 0
    month_markers = []
    last_month = None

    for i, d in enumerate(days):
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        # Sunday is 0, Saturday is 6
        dow = (dt.weekday() + 1) % 7
        if i > 0 and dow == 0:
            week_idx += 1

        # Month label calculation
        if dt.month != last_month:
            if not month_markers or (week_idx - month_markers[-1][0] >= 3):
                month_markers.append((week_idx, dt.strftime("%b")))
            last_month = dt.month

        # Map to level 0..5
        lvl = d.get("level", 0)
        cnt = d.get("count", 0)
        if cnt >= top_threshold and lvl >= 4:
            color_idx = 5
        elif lvl > 4:
            color_idx = 4
        elif lvl < 0:
            color_idx = 0
        else:
            color_idx = lvl

        fill_color = PALETTE[color_idx]
        grid.append({
            "date": d["date"],
            "count": cnt,
            "level": color_idx,
            "fill": fill_color,
            "week": week_idx,
            "dow": dow
        })

    # Dimensions
    svg_width = 860
    svg_height = 200
    start_x = 42
    start_y = 48
    cell_size = 11.5
    cell_gap = 3.3
    step_x = cell_size + cell_gap # 14.8 px
    step_y = cell_size + cell_gap # 14.8 px

    # CSS styles
    css_lines = [
        "svg { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Courier New', monospace; }",
        ".label { font-size: 10px; fill: #7d8590; }",
        ".footer { font-size: 11px; fill: #8b949e; }",
        ".legend-text { font-size: 10px; fill: #7d8590; }",
    ]

    if not is_static:
        css_lines.extend([
            "@keyframes cellDrop {",
            "  0% { opacity: 0; transform: translateY(-7px); }",
            "  100% { opacity: 1; transform: translateY(0); }",
            "}",
            ".cell {",
            "  opacity: 0;",
            "  animation: cellDrop 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;",
            "  transform-box: fill-box;",
            "  transform-origin: center;",
            "}",
            "@media (prefers-reduced-motion: reduce) {",
            "  .cell { opacity: 1 !important; transform: none !important; animation: none !important; }",
            "}"
        ])
    else:
        css_lines.append(".cell { opacity: 1; }")

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">')
    svg_parts.append('  <style>')
    for line in css_lines:
        svg_parts.append(f'    {line}')
    svg_parts.append('  </style>')

    # Background card
    svg_parts.append(f'  <rect width="{svg_width}" height="{svg_height}" rx="8" fill="#0d1117" stroke="#30363d" stroke-width="1"/>')

    # Month Labels
    for w_idx, m_name in month_markers:
        mx = start_x + (w_idx * step_x)
        my = start_y - 12
        if mx < svg_width - 50:
            svg_parts.append(f'  <text x="{mx:.1f}" y="{my:.1f}" class="label">{m_name}</text>')

    # Day of week labels (Mon=1, Wed=3, Fri=5)
    dow_labels = [
        (1, "Mon"),
        (3, "Wed"),
        (5, "Fri")
    ]
    for dow, name in dow_labels:
        dy = start_y + (dow * step_y) + (cell_size * 0.82)
        svg_parts.append(f'  <text x="16" y="{dy:.1f}" class="label">{name}</text>')

    # Grid Cells
    for item in grid:
        x = start_x + (item["week"] * step_x)
        y = start_y + (item["dow"] * step_y)
        delay_ms = (item["week"] + item["dow"]) * 12
        style_attr = f' style="animation-delay: {delay_ms}ms;"' if not is_static else ''
        svg_parts.append(
            f'  <rect class="cell" x="{x:.1f}" y="{y:.1f}" width="{cell_size:.1f}" height="{cell_size:.1f}" '
            f'rx="2.2" fill="{item["fill"]}"{style_attr}>'
            f'<title>{item["count"]} contribution{"s" if item["count"] != 1 else ""} on {item["date"]}</title>'
            f'</rect>'
        )

    # Stats Footer (left side)
    curr_unit = "day" if current_streak == 1 else "days"
    long_unit = "day" if longest_streak == 1 else "days"
    footer_text = f"{total:,} contributions in the last year  ·  Current streak: {current_streak} {curr_unit}  ·  Longest streak: {longest_streak} {long_unit}"
    svg_parts.append(f'  <text x="{start_x}" y="176" class="footer">{footer_text}</text>')

    # Legend (right side)
    legend_start_x = 690
    legend_y = 168
    svg_parts.append(f'  <text x="{legend_start_x - 30}" y="{legend_y + 8}" class="legend-text">Less</text>')
    
    # 5 sample boxes for legend
    legend_colors = [PALETTE[0], PALETTE[1], PALETTE[2], PALETTE[3], PALETTE[4], PALETTE[5]]
    for idx, col in enumerate(legend_colors):
        bx = legend_start_x + (idx * 14)
        svg_parts.append(f'  <rect x="{bx}" y="{legend_y}" width="10" height="10" rx="2" fill="{col}"/>')
        
    svg_parts.append(f'  <text x="{legend_start_x + len(legend_colors) * 14 + 6}" y="{legend_y + 8}" class="legend-text">More</text>')

    svg_parts.append('</svg>')

    content = "\n".join(svg_parts) + "\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully generated {out_path} ({len(content)} bytes, static={is_static}).")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "contrib-heatmap.svg"
    render_heatmap(out_path=out_file)
