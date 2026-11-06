"""Composite transparent renders (with shadow-catcher alpha) over pure white."""
import sys
from PIL import Image
for p in sys.argv[1:]:
    im = Image.open(p).convert("RGBA"); bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im); bg.convert("RGB").save(p.replace(".png", "_w.png"))
