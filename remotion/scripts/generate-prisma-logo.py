from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import shutil

width, height = 512, 512
img = Image.new("RGBA", (width, height), (0, 0, 0, 0))

# 1. Base dark card rounded rectangle
card = Image.new("RGBA", (width, height), (11, 15, 25, 255))
mask = Image.new("L", (width, height), 0)
mask_draw = ImageDraw.Draw(mask)
mask_draw.rounded_rectangle([(0, 0), (width, height)], radius=64, fill=255)
img.paste(card, (0, 0), mask)

# 2. Border
draw = ImageDraw.Draw(img)
draw.rounded_rectangle([(2, 2), (width-2, height-2)], radius=62, outline=(255, 255, 255, 36), width=2)

# 3. Ambient Glow behind prism
glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow)
glow_draw.ellipse([(140, 90), (372, 322)], fill=(20, 184, 166, 60))
glow = glow.filter(ImageFilter.GaussianBlur(32))
img = Image.alpha_composite(img, glow)
draw = ImageDraw.Draw(img)

# 4. Prisma Iconic Polygon Facets
# Top apex: (256, 80)
# Left apex: (110, 330)
# Right apex: (410, 290)
# Bottom base: (230, 380)
# Crest spine: (250, 310)

# Left Facet (Deep Teal)
draw.polygon([(256, 80), (110, 330), (230, 380), (250, 310)], fill=(13, 148, 136, 255))

# Right Facet (Luminous Cyan / Light Catcher)
draw.polygon([(256, 80), (250, 310), (230, 380), (410, 290)], fill=(45, 212, 191, 255))

# Sharp Spine Highlight
draw.line([(256, 80), (250, 310), (230, 380)], fill=(255, 255, 255, 240), width=4)
draw.line([(256, 80), (410, 290)], fill=(255, 255, 255, 200), width=3)
draw.line([(256, 80), (110, 330)], fill=(45, 212, 191, 200), width=2)

# 5. Typography: "PRISMA"
try:
    font_large = ImageFont.truetype("arial.ttf", 46)
    font_sub = ImageFont.truetype("arial.ttf", 16)
except Exception:
    font_large = ImageFont.load_default()
    font_sub = ImageFont.load_default()

draw.text((256, 415), "PRISMA", fill=(248, 250, 252, 255), font=font_large, anchor="mm")
draw.text((256, 455), "NEXT-GEN ORM", fill=(45, 212, 191, 255), font=font_sub, anchor="mm")

# Save to destination
out_path = os.path.abspath("jobs/sample-promo-prisma/assets/logo.png")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
img.save(out_path, "PNG")

pub_path = os.path.abspath("public/jobs/sample-promo-prisma/assets/logo.png")
os.makedirs(os.path.dirname(pub_path), exist_ok=True)
shutil.copyfile(out_path, pub_path)

print(f"Generated Prisma logo at: {out_path} and {pub_path}")
