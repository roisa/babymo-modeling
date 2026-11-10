"""Contact sheet on white: python sheet.py OUT.png COLS TILE img1 img2 ... (labels = file stems)."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
out, cols, tile = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); fs = sys.argv[4:]
rows = (len(fs) + cols - 1) // cols; lab = 34
sheet = Image.new("RGB", (cols * tile, rows * (tile + lab)), "white"); d = ImageDraw.Draw(sheet)
try: font = ImageFont.truetype("DejaVuSans.ttf", 20)
except Exception: font = ImageFont.load_default()
for i, f in enumerate(fs):
    im = Image.open(f).convert("RGBA").resize((tile, tile)); bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    x, y = (i % cols) * tile, (i // cols) * (tile + lab); sheet.paste(bg.convert("RGB"), (x, y + lab))
    d.text((x + 8, y + 6), os.path.basename(f).replace("BabyMo_Tennis_", "").replace(".png", ""), fill=(90, 90, 110), font=font)
sheet.save(out); print(sheet.size)
