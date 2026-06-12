from PIL import Image, ImageDraw, ImageFont
import os
import random

BASE = os.path.dirname(os.path.dirname(__file__))
IMAGES_DIR = os.path.join(BASE, "images")

spec = {
    "anime": {
        "gojo": ["school", "work", "street"],
        "urume": ["school", "work", "street"]
    },
    "goth": {
        "default": ["default"]
    },
    "serials": {
        "homelender": ["default"]
    }
}

os.makedirs(IMAGES_DIR, exist_ok=True)

for cat, chars in spec.items():
    cat_dir = os.path.join(IMAGES_DIR, cat)
    os.makedirs(cat_dir, exist_ok=True)
    for char, styles in chars.items():
        for style in styles:
            fn = f"{cat}_{char}_{style}.png"
            path = os.path.join(cat_dir, fn)
            # create simple placeholder image
            img = Image.new("RGB", (800, 600), color=(random.randint(50,230), random.randint(50,230), random.randint(50,230)))
            d = ImageDraw.Draw(img)
            try:
                fnt = ImageFont.truetype("arial.ttf", 40)
            except Exception:
                fnt = ImageFont.load_default()
            text = f"{char.capitalize()}\n{style.capitalize()}"
            w, h = d.multiline_textsize(text, font=fnt)
            d.multiline_text(((800-w)/2, (600-h)/2), text, font=fnt, fill=(255,255,255), align="center")
            img.save(path)
            print("Wrote", path)

print("All placeholders created.")
