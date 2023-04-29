from pathlib import Path
from PIL import Image

load_dest = Path("results")

for f_png in load_dest.glob("**/*.png"):
    f_jpg = f_png.with_suffix(".jpg")
    if f_jpg.exists():
        continue

    png_image = Image.open(f_png)

    # Convert the image to RGB mode (if it's not already in RGB mode)
    rgb_image = png_image.convert("RGB")

    # Save the image as a JPEG file with high quality
    rgb_image.save(f_jpg, quality=85)
    print(f_jpg)
