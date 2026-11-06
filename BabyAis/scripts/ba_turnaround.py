"""Turnaround sheet like the reference: row 1 full body front/3-4/left/right/back, row 2 face + hair close-ups."""
import sys
from PIL import Image, ImageDraw, ImageFont
d = sys.argv[1]; out = sys.argv[2]
body = [Image.open(f"{d}/{v}_w.png") for v in ("front", "34", "left", "right", "back")]
close = [Image.open(f"{d}/{v}_w.png") for v in ("face", "hair")]
W = 600; H = 800
body = [im.crop((90, 120, 810, 1080)).resize((W, H)) for im in body]
CW = 1500 // 2
close = [im.resize((CW, CW)) for im in close]
sheet = Image.new("RGB", (W * 5, H + CW + 60), "white")
for i, im in enumerate(body): sheet.paste(im, (i * W, 0))
x0 = (W * 5 - 2 * CW - 40) // 2
for i, im in enumerate(close): sheet.paste(im, (x0 + i * (CW + 40), H + 30))
dr = ImageDraw.Draw(sheet)
try: f = ImageFont.truetype("DejaVuSans.ttf", 26)
except Exception: f = ImageFont.load_default()
for i, t in enumerate(("FRONT", "THREE-QUARTER", "LEFT", "RIGHT", "BACK")): dr.text((i * W + 20, H - 40), t, fill=(150, 150, 160), font=f)
dr.text((20, H + 40), "BABY AIS  -  " + (sys.argv[3] if len(sys.argv) > 3 else "no hijab edition"), fill=(120, 120, 135), font=f)
sheet.save(out); print(sheet.size)
