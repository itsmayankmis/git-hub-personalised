#!/usr/bin/env python3
"""
prep_photo.py
Prepares source-photo.jpg for ASCII conversion:
1. Removes background with rembg.
2. Converts to grayscale and enhances local contrast with CLAHE.
3. Composites onto pure white (so background = 255 = blank space in ASCII ramp).
4. Saves grayscale image to source-prepped.png.
"""

import sys
import os
from PIL import Image
import numpy as np
import cv2
from rembg import remove

def prep_photo(input_path="source-photo.jpg", output_path="source-prepped.png"):
    if not os.path.exists(input_path):
        print(f"Error: Input photo '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading '{input_path}' and removing background with rembg...")
    input_image = Image.open(input_path).convert("RGBA")
    
    # 1. Remove background
    bg_removed = remove(input_image)
    bg_np = np.array(bg_removed) # Shape: (H, W, 4) - RGBA

    r, g, b, alpha = bg_np[:, :, 0], bg_np[:, :, 1], bg_np[:, :, 2], bg_np[:, :, 3]

    # Convert RGB to grayscale (standard luminance weights)
    gray = cv2.cvtColor(bg_np[:, :, :3], cv2.COLOR_RGB2GRAY)

    # 2. Boost local contrast with CLAHE
    # clipLimit ≈ 2.5–3.0, tileGridSize 8×8
    clahe = cv2.createCLAHE(clipLimit=2.8, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)

    # 3. Composite onto pure white (255) using alpha mask
    # alpha mask normalized 0.0 to 1.0
    alpha_norm = (alpha.astype(np.float32) / 255.0)

    # Foreground is enhanced_gray, background is 255 (pure white)
    white_bg = np.full_like(enhanced_gray, 255, dtype=np.float32)
    composite = (enhanced_gray.astype(np.float32) * alpha_norm) + (white_bg * (1.0 - alpha_norm))
    composite = np.clip(composite, 0, 255).astype(np.uint8)

    # 4. Save output
    out_img = Image.fromarray(composite, mode="L")
    out_img.save(output_path)
    print(f"Successfully saved prepped image to '{output_path}' ({out_img.size[0]}x{out_img.size[1]}px).")

if __name__ == "__main__":
    in_file = sys.argv[1] if len(sys.argv) > 1 else "source-photo.jpg"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png"
    prep_photo(in_file, out_file)
