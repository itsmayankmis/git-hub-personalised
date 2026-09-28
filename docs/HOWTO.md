# Profile Maintenance & Customization Guide

This document explains how to update your photo, customize your terminal info card, re-render components, and publish changes to your public GitHub profile.

---

## 1. How It Appears to Visitors on GitHub

When you create a public repository named **`itsmayankmis`** under your account (`github.com/itsmayankmis/itsmayankmis`), GitHub automatically renders `README.md` at the very top of your public profile (`https://github.com/itsmayankmis`).

Anyone who visits your profile will see:
1. **Contribution Calendar (`contrib-heatmap.svg`)**: Smooth diagonal wave animation displaying your actual GitHub contributions.
2. **ASCII Portrait (`ascii-portrait.svg`)**: Your photo rendered as crisp ASCII art that types itself row-by-row with a terminal cursor.
3. **Info Card (`info-card.svg`)**: A macOS/Linux terminal window presenting your current focus, background, stack, and highlights fading in line-by-line.
4. **Links & Badges**: Clean badge links to your GitHub, LinkedIn, and Instagram.

---

## 2. Changing or Updating Your Photo

1. Place your new front-facing photo as `source-photo.jpg` in the root of the repository.
2. Run the photo preparation script:
   ```bash
   ./.venv/bin/python scripts/prep_photo.py source-photo.jpg source-prepped.png
   ```
   *This removes the background with AI (`rembg`) and applies CLAHE contrast optimization.*
3. Generate the animated ASCII SVG:
   ```bash
   ./.venv/bin/python scripts/make_ascii_svg.py source-prepped.png ascii-portrait.svg
   ```
4. Commit and push:
   ```bash
   git add source-photo.jpg source-prepped.png ascii-portrait.svg
   git commit -m "feat: update profile ASCII portrait"
   git push
   ```

---

## 3. Editing the Info Card (Neofetch Panel)

1. Open `data/profile_config.json` and edit any fields:
   - `now`: What you're currently building or learning.
   - `prev`: Previous experience or degree.
   - `stack`: Comma-separated list of technologies.
   - `highlights`: Bullet points showcasing recent wins or projects.
2. Regenerate the SVG:
   ```bash
   ./.venv/bin/python scripts/make_info_card.py
   ```
3. Commit and push:
   ```bash
   git add data/profile_config.json info-card.svg
   git commit -m "chore: update info card bio and highlights"
   git push
   ```

---

## 4. Manual Heatmap Refresh

The GitHub Action (`.github/workflows/update-profile-art.yml`) automatically refreshes the heatmap daily at `06:17 UTC`. To refresh manually at any time:
```bash
./.venv/bin/python scripts/fetch_contributions.py
./.venv/bin/python scripts/render_heatmap_svg.py
```

---

## 5. Previewing Static Frames

To preview or generate frozen frames without animations:
```bash
STATIC=1 ./.venv/bin/python scripts/render_heatmap_svg.py
STATIC=1 ./.venv/bin/python scripts/make_info_card.py
STATIC=1 ./.venv/bin/python scripts/make_ascii_svg.py
```
