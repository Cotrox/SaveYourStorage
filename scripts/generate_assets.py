"""
Asset Generator for Ctrx SaveStorage
Generates PNG, ICO, and Favicon assets from the header SVG icon.
Developed by Giuseppe Antonino Cotroneo (https://ko-fi.com/cotrox)
"""

import os
import sys
from pathlib import Path
from PIL import Image
import resvg_py

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
WEB_DIR = BASE_DIR / "web"

ASSETS_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR.mkdir(parents=True, exist_ok=True)

# Master SVG definition matching header app icon
SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="fluentGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0078d4"/>
      <stop offset="100%" stop-color="#00b4d8"/>
    </linearGradient>
    <filter id="fluentShadow" x="-10%" y="-10%" width="130%" height="130%">
      <feDropShadow dx="0" dy="16" stdDeviation="20" flood-color="#0078d4" flood-opacity="0.4"/>
    </filter>
  </defs>
  <!-- Rounded Squircle Base -->
  <rect x="44" y="44" width="424" height="424" rx="100" fill="url(#fluentGrad)" filter="url(#fluentShadow)"/>
  
  <!-- Cloud Download / Save Storage Icon from Header -->
  <g transform="translate(120, 120) scale(11.333)" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none">
    <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/>
    <path d="M12 12v9"/>
    <path d="m8 17 4 4 4-4"/>
  </g>
</svg>"""

def generate_all():
    print("==================================================")
    print(" Generazione Asset Icona & Favicon Ctrx SaveStorage")
    print("==================================================")

    # 1. Save master SVG
    svg_path = ASSETS_DIR / "icon.svg"
    svg_path.write_text(SVG_TEMPLATE, encoding="utf-8")
    print(f"✓ Salvato SVG: {svg_path.name}")

    # 2. Render 512x512 Master PNG with resvg
    png_bytes = resvg_py.svg_to_bytes(SVG_TEMPLATE)
    master_png = ASSETS_DIR / "icon-512.png"
    with open(master_png, "wb") as f:
        f.write(png_bytes)
    print(f"✓ Renderizzato PNG 512x512: {master_png.name}")

    # Copy to assets/icon.png and web/icon.png
    master_img = Image.open(master_png).convert("RGBA")
    master_img.save(ASSETS_DIR / "icon.png", format="PNG")
    master_img.save(WEB_DIR / "icon.png", format="PNG")

    # 3. Generate icon sizes for favicon and multi-res ICO
    sizes = [256, 128, 64, 48, 32, 16]
    ico_images = []

    for sz in sizes:
        resized = master_img.resize((sz, sz), Image.Resampling.LANCZOS)
        resized.save(ASSETS_DIR / f"icon-{sz}.png", format="PNG")
        ico_images.append(resized)
        if sz == 32:
            resized.save(WEB_DIR / "favicon.png", format="PNG")
        elif sz == 192 or sz == 256:
            resized.save(WEB_DIR / "favicon-192.png", format="PNG")
        print(f"✓ Generato PNG {sz}x{sz}")

    # 4. Generate multi-resolution .ICO for Windows and Web
    ico_path_assets = ASSETS_DIR / "icon.ico"
    ico_path_web = WEB_DIR / "favicon.ico"

    # Pillow can save all resolutions in a single .ico file
    master_img.save(
        ico_path_assets,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    )
    master_img.save(
        ico_path_web,
        format="ICO",
        sizes=[(64, 64), (48, 48), (32, 32), (16, 16)]
    )
    print(f"✓ Generato Windows App Icon: {ico_path_assets.name}")
    print(f"✓ Generato Favicon Web: {ico_path_web.name}")

    print("\nTutti gli asset sono stati creati con successo!")

if __name__ == "__main__":
    generate_all()
