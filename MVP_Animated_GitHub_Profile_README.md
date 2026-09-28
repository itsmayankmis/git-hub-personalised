# MVP: Animated Terminal-Style GitHub Profile README

> Paste this whole document into Antigravity as the task brief. Fill the `[FILL]` fields in Section 2 first.

---

## 1. Goal

Build a GitHub profile README that looks like a terminal. It has three animated SVGs and a daily auto-refresh:

1. **Contribution heatmap** (top): the real 53-week contribution calendar as rounded green boxes that slide in diagonally, with a Less→More legend and a stats footer.
2. **ASCII portrait** (left): my photo as clean, one-color ASCII art that "types" itself in row by row.
3. **Neofetch info card** (right): a terminal-style panel whose lines fade in one by one.
4. **Links row** (below): `./links.sh` heading, my name and role line, and badge buttons.
5. **GitHub Action** that re-scrapes and re-renders the heatmap every day and commits it.

**Hard constraints (GitHub README limits):**
- No JavaScript. No external CSS. Inline `style=""` is stripped.
- All motion lives inside self-contained SVG files (SMIL or CSS keyframes) embedded with `<img>`.
- No third-party stats services. No GitHub token. Only a public GitHub HTML endpoint.
- SVGs cannot load external fonts or images. Use a monospace fallback stack: `ui-monospace, SFMono-Regular, Menlo, Consolas, "Courier New", monospace`.

---

## 2. Inputs (fill these in)

| Field | Value |
|---|---|
| GitHub username | `[FILL]` |
| Display name | `[FILL]` |
| Role line (one line) | `[FILL]` e.g. "Mechanical Engineering Student · AI Builder" |
| Photo | `source-photo.jpg` in repo root (front-facing, good light) |
| Info card: Now | `[FILL]` |
| Info card: Prev | `[FILL]` |
| Info card: Stack | `[FILL]` |
| Info card: Highlights (2–3) | `[FILL]` |
| Links | Portfolio `[FILL]`, LinkedIn `[FILL]`, Instagram `[FILL]`, optional live link `[FILL]` |

---

## 3. Repo structure

```
<username>/                      # special repo: name must equal the GitHub username, public
├── README.md
├── source-photo.jpg
├── source-prepped.png           # generated
├── ascii-portrait.svg           # generated
├── info-card.svg                # generated
├── contrib-heatmap.svg          # generated, refreshed daily
├── links-row.svg                # optional, generated (else use shields.io badges in README)
├── data/contributions.json      # generated daily
├── scripts/
│   ├── requirements.txt
│   ├── prep_photo.py
│   ├── make_ascii_svg.py
│   ├── make_info_card.py
│   ├── fetch_contributions.py
│   └── render_heatmap_svg.py
└── .github/workflows/update-profile-art.yml
```

`scripts/requirements.txt`:
```
requests==2.32.3
beautifulsoup4==4.12.3
# portrait only (local, not needed by the daily workflow):
pillow
numpy
opencv-python
rembg
```

---

## 4. Component specs

### 4.1 `prep_photo.py` (run once per photo)
Input: `source-photo.jpg`. Output: grayscale `source-prepped.png`.
1. Remove the background with `rembg` to isolate the subject.
2. Convert to grayscale and apply OpenCV **CLAHE** (clipLimit ≈ 2.5–3.0, tileGridSize 8×8) to add highlights and shadows to a flat face.
3. Composite onto **pure white** so the background maps to the blank end of the ASCII ramp.
4. CLI: `python scripts/prep_photo.py source-photo.jpg`.

### 4.2 `make_ascii_svg.py` → `ascii-portrait.svg`
- Downsample `source-prepped.png` to about **100 columns × 53 rows**. Correct for character aspect ratio (glyphs are about 2× taller than wide).
- Brightness → glyph using this ramp, sparse to dense: `RAMP = " .`:-=+*cs#%@"`. The leading space clears the background.
- **Monochrome:** one light-gray fill (e.g. `#c9d1d9`) on a transparent or `#0d1117` background. No per-character colors.
- Render each row as an SVG `<text>` with `xml:space="preserve"`, monospace font, fixed `textLength` or character width so columns align.
- **Animation (SMIL, plays once, then freezes):**
  - Each row is wrapped in a `clipPath` whose `<rect>` width animates 0 → full width (`<animate attributeName="width" fill="freeze">`).
  - A small block cursor `█` rides the wipe edge and disappears at the end of the row.
  - Rows are staggered top to bottom (about 0.04–0.06 s per row via `begin`).
  - Total print time about 3–4 s. No looping.
- Env flag `STATIC=1` emits a frozen final frame for local preview.
- Escape `&`, `<`, `>` in glyphs (`&amp;`, `&lt;`, `&gt;`).

### 4.3 `make_info_card.py` → `info-card.svg`
- Size about 490×(auto) viewBox. Dark panel (`#0d1117`), 1px border `#30363d`, rounded corners.
- Title bar with three dots (red/yellow/green) and a title like `<username>@github ~ $ neofetch`.
- Colored key/value rows: **Now**, **Prev**, **Stack**, **Highlights**, taken from Section 2.
  - Keys in an accent color (e.g. `#58a6ff`), values in `#c9d1d9`, separators in gray.
- Word-wrap long values manually (SVG has no auto-wrap). Keep lines about 48 characters max.
- **Animation:** each line fades in and slides up about 6 px with a short stagger (about 0.25 s per line), using CSS `@keyframes` with `animation-fill-mode: forwards`. Play once.
- Do NOT duplicate GitHub stats here. The card is for the story the numbers can't tell.
- Support `STATIC=1`.

### 4.4 `fetch_contributions.py` → `data/contributions.json`
- GET `https://github.com/users/<username>/contributions` with a normal browser `User-Agent`. No auth.
- Parse with BeautifulSoup:
  - Day cells: `td.ContributionCalendar-day` with `data-date` and `data-level` (0–4).
  - Contribution counts come from the linked tooltip text (`"N contributions on …"` or `"No contributions on …"`). Match by cell `id` ↔ tooltip `for`.
  - Total from the header text ("N contributions in the last year").
- Write JSON: `{ "username", "generated_at", "total", "days": [{"date","count","level"}], "stats": { "current_streak", "longest_streak", "best_day": {"date","count"}, "monthly_totals": {...} } }`.
- Exit non-zero on empty or malformed results so the workflow doesn't commit a broken graph.

### 4.5 `render_heatmap_svg.py` → `contrib-heatmap.svg`
- Read `data/contributions.json`. Draw the classic **53 weeks × 7 days** grid: rounded rects (`rx≈2`), cell about 12 px, gap about 3 px.
- Palette (level 0→5; map GitHub levels 0–4 and use level 5 for top-decile days):
  `["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]`
- Add month labels on top and Mon/Wed/Fri labels on the left.
- **Animation:** CSS keyframes, plays once on load and freezes. Each cell fades and slides down, with delay = `(week + day) * ~12ms` for a diagonal wave. No looping glow.
- **Legend:** "Less [5 boxes] More" bottom right.
- **Stats footer:** `"<total> contributions in the last year"` plus current streak and longest streak.
- Total width about **860 px** (matches portrait 370 + card 490 below).
- Support `STATIC=1`.

### 4.6 Links row
Preferred: static shields.io badge images in the README (`<img src="https://img.shields.io/badge/...">`), since GitHub renders those. Under the heading show the display name and role line centered. Optional: a generated `links-row.svg` if a fully self-hosted look is wanted.

---

## 5. README.md layout

```html
<div align="center">

<h3><code>USERNAME@github ~ $ ./contributions.sh</code></h3>
<img src="./contrib-heatmap.svg" width="860" />
<br><br>

<h3><code>USERNAME@github ~ $ whoami</code></h3>
<table>
  <tr>
    <td valign="top"><img src="./ascii-portrait.svg" width="370" /></td>
    <td valign="top"><img src="./info-card.svg" width="490" /></td>
  </tr>
</table>
<br>

<h3><code>USERNAME@github ~ $ ./links.sh</code></h3>
<b>DISPLAY NAME</b><br>
ROLE LINE<br><br>
<!-- badge row: Portfolio | LinkedIn | GitHub | Instagram -->
<a href="..."><img src="https://img.shields.io/badge/..." /></a>

</div>
```

**GitHub gotchas to respect:**
- Use `<h3>` for section prompts (`<h1>`/`<h2>` draw an underline rule).
- Only `<br>` tags create vertical spacing (inline style is stripped).
- Two images side by side only work inside a `<table>` with `valign="top"`.
- Keep the widths aligned: heatmap 860 = portrait 370 + card 490.

---

## 6. GitHub Action: `.github/workflows/update-profile-art.yml`

```yaml
name: Update profile art
"on":
  schedule:
    - cron: "17 6 * * *"      # daily ~06:17 UTC
  workflow_dispatch: {}
  push:
    branches: [main]
permissions:
  contents: write
jobs:
  heatmap:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install requests==2.32.3 beautifulsoup4==4.12.3
      - run: python scripts/fetch_contributions.py
      - run: python scripts/render_heatmap_svg.py
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: refresh contribution graph [skip ci]"
          file_pattern: "data/contributions.json contrib-heatmap.svg"
```

Note: the daily job installs only `requests` and `beautifulsoup4`. The image libraries are for local portrait generation. The heatmap scripts must not import them.

---

## 7. Build order for the agent

1. Scaffold the folder structure and `requirements.txt`, and create a venv.
2. Build `fetch_contributions.py` and `render_heatmap_svg.py` first (no photo needed), then verify `contrib-heatmap.svg` visually.
3. Build `make_info_card.py` and verify.
4. Build `prep_photo.py` and `make_ascii_svg.py` and verify the portrait is recognizable.
5. Write `README.md` and add the workflow.
6. Provide `gh` commands to create the repo, push, and trigger the workflow once.

---

## 8. Acceptance criteria

- [ ] All SVGs open standalone in a browser and animate once, then freeze (no looping).
- [ ] Each SVG is under about 1 MB; no `<script>`, no external URLs, no `<foreignObject>`.
- [ ] Portrait is readable: the face is clear and the background is blank.
- [ ] Heatmap counts match my real GitHub profile (spot-check 3 days and the total).
- [ ] README renders correctly on the GitHub profile page in dark and light themes (SVGs use their own dark panel background so both look fine).
- [ ] Workflow runs via `workflow_dispatch` and commits a fresh `contrib-heatmap.svg`; the bot commit does not retrigger it.
- [ ] `STATIC=1` produces frozen previews of every animated SVG.
- [ ] README has no inline styles and no JavaScript.

---

## 9. Out of scope (MVP)

Visitor counters, WakaTime or language stats, music widgets, looping animations, light-theme variants, and pinned-repo customization (GitHub handles those natively).

---

## 10. Deliverables

Full source for all scripts, generated SVGs, `README.md`, the workflow file, and a short `docs/HOWTO.md` explaining how to swap the photo and edit the info card (which command to rerun).
