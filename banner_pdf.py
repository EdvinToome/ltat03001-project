#!/usr/bin/env python
# banner_pdf.py ───────────────────────────────────────────────────────────────
# (Same logic as you provided, but all assets live under assets/.)

from PIL import Image, ImageFilter
import os
import zipfile
import tempfile
from pathlib import Path

# ============================
#  SETUP: INPUT/OUTPUT FOLDERS
# ============================
input_folder = "input"
output_folder = "output"
os.makedirs(output_folder, exist_ok=True)

# Clean up top-level files in the output folder.
for item in os.listdir(output_folder):
    item_path = os.path.join(output_folder, item)
    if os.path.isfile(item_path) or os.path.islink(item_path):
        os.unlink(item_path)

# ============================
#  ASSETS DIRECTORY
# ============================
ASSETS = Path("assets")

# ============================
#  WATERMARK PATHS DICTIONARY
# ============================
watermark_paths = {
    'd': ASSETS / 'dark.png',
    'l': ASSETS / 'bright.png',
    'dw': ASSETS / 'dark-wide.png',
    'lw': ASSETS / 'bright-wide.png'
}

dark_watermark      = Image.open(watermark_paths['d']).convert("RGBA")
dark_wide_watermark = Image.open(watermark_paths['dw']).convert("RGBA")

# ============================
#  USER INPUT: OUTPUT MODE
# ============================
output_type = input("Select single or multi output type (s/m): ").strip().lower()

# ============================
#  GLOBAL WATERMARK SELECTION (for non-multi mode)
# ============================
if output_type != "m":
    watermark_type   = input("Select dark or light watermark type (d/l/dw/lw): ").strip().lower()
    watermark_global = Image.open(watermark_paths.get(watermark_type, ASSETS / 'bright.png')).convert("RGBA")
else:
    watermark_global = None

# ============================
#  LOAD BANNER RESOURCES (COMMON)
# ============================
banner_template_path = ASSETS / "banner_template.png"
banner_template      = Image.open(banner_template_path).convert("RGBA")

banner_watermark_path = ASSETS / "watermark.png"
banner_watermark      = Image.open(banner_watermark_path).convert("RGBA")

# ============================
#  GLOBAL PROCESSING PARAMETERS
# ============================
shadow_offset = (5, 5)
blur_radius   = 15
shadow_opacity= 90
shadow_color  = (0, 0, 0, shadow_opacity)

# ============================
#  HELPER FUNCTION: PROCESS IMAGE
# ============================
def process_single_image(image_path, out_subfolder, rename_banner=False):
    image = Image.open(image_path).convert("RGBA")
    watermark_img = dark_watermark if image.height > image.width else dark_wide_watermark
    watermark_resized = watermark_img.resize(image.size, Image.LANCZOS)
    watermark_cropped = watermark_resized.crop((0, 0, image.size[0], image.size[1]))
    watermarked_image = Image.alpha_composite(image, watermark_cropped)
    watermarked_image_rgb = watermarked_image.convert("RGB")

    # Create the Banner Image
    banner = banner_template.copy()
    banner_width, banner_height = banner.size
    ratio = 884 / 1080
    max_width  = int(banner_width * ratio)
    max_height = int(banner_height * ratio)
    orig_w, orig_h = watermarked_image.width, watermarked_image.height
    scale_factor = min(max_width / orig_w, max_height / orig_h)
    target_w = int(orig_w * scale_factor)
    target_h = int(orig_h * scale_factor)
    resized_image = watermarked_image.resize((target_w, target_h), Image.LANCZOS)
    image_x = (banner_width - resized_image.width) // 2
    image_y = (banner_height - resized_image.height) // 2

    # Drop Shadow
    shadow_layer = Image.new("RGBA", banner.size, (0, 0, 0, 0))
    shadow_rect  = Image.new("RGBA", (resized_image.width, resized_image.height), shadow_color)
    shadow_layer.paste(shadow_rect, (image_x + shadow_offset[0], image_y + shadow_offset[1]))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur_radius))
    banner = Image.alpha_composite(banner, shadow_layer)

    # Paste image + overlay watermark
    banner.paste(resized_image, (image_x, image_y))
    temp_wm = Image.new("RGBA", banner.size, (0, 0, 0, 0))
    temp_wm.paste(banner_watermark, (0, 0), banner_watermark)
    banner = Image.alpha_composite(banner, temp_wm)

    # Save Banner
    if rename_banner:
        out_path = out_subfolder / 'Banner.jpg'
        banner.convert("RGB").save(out_path, "JPEG")
        print(f"Banner saved: {out_path}")
    else:
        stem = Path(image_path).stem
        if stem in ['1','2','3','4']:
            out_path = out_subfolder / f"{stem}_banner.jpg"
            banner.convert("RGB").save(out_path, "JPEG")
            print(f"Banner saved: {out_path}")

    return watermarked_image_rgb

# ============================
#  MAIN PROCESSING LOOP
# ============================
input_files = sorted(Path(input_folder).glob("*"), key=lambda x: x.name)

for file in input_files:
    out_subfolder = Path(output_folder) / file.stem
    os.makedirs(out_subfolder, exist_ok=True)

    if file.suffix.lower() == ".png":
        print(f"Processing PNG: {file}")
        img = process_single_image(file, out_subfolder, rename_banner=True)
        pdf_path = out_subfolder / "Worksheet.pdf"
        img.save(pdf_path, "PDF")
        print(f"PDF saved: {pdf_path}")

    elif file.suffix.lower() == ".zip":
        print(f"Processing ZIP: {file}")
        pages = []
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(file, 'r') as z:
                z.extractall(td)
            pngs = sorted(Path(td).rglob("*.png"), key=lambda x: x.name)
            for p in pngs:
                print(f"  Processing extracted PNG: {p.name}")
                pages.append(process_single_image(p, out_subfolder, rename_banner=False))
        if pages:
            out_pdf = out_subfolder / "Worksheet.pdf"
            pages[0].save(out_pdf, "PDF", save_all=True, append_images=pages[1:])
            print(f"Combined PDF saved: {out_pdf}")

    else:
        print(f"Skipping unsupported file type: {file}")

print("Processing complete. Files saved to the 'output' folder.")

if __name__ == "__main__":
    pass
