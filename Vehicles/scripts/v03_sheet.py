"""3x2 sheet on white from the per-vehicle renders."""
import sys
from PIL import Image
d, out = sys.argv[1], sys.argv[2]
import os
N = sys.argv[3].split(",") if len(sys.argv) > 3 else open(f"{d}/order.txt").read().split()
ims = []
for n in N:
    im = Image.open(f"{d}/{n}.png").convert("RGBA"); bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    bg.convert("RGB").save(f"{d}/{n}_w.png"); ims.append(bg.convert("RGB"))
w, h = ims[0].size; rows = (len(ims) + 2) // 3; sheet = Image.new("RGB", (w * 3, h * rows), "white")
for i, im in enumerate(ims): sheet.paste(im, ((i % 3) * w, (i // 3) * h))
sheet.save(out); print(sheet.size)
