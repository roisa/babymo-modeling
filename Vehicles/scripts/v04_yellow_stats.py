"""Median / bright / shadow colour of the yellow paint in an image (pixels that are clearly yellow-orange)."""
import sys, numpy as np, colorsys
from PIL import Image
for p in sys.argv[1:]:
    im = Image.open(p).convert("RGBA"); a = np.asarray(im).astype(float)
    rgb, al = a[..., :3], a[..., 3]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    m = (al > 200) & (r > 120) & (r > g) & (g > b + 40) & ((r - b) > 110)
    px = rgb[m]; lum = px.mean(1)
    def hsv(c): h, s, v = colorsys.rgb_to_hsv(*(c / 255)); return f"rgb{tuple(int(x) for x in c)} H{h*360:.0f} S{s:.2f} V{v:.2f}"
    q = np.percentile(lum, [20, 50, 85])
    sel = lambda lo, hi: np.median(px[(lum >= lo) & (lum <= hi)], 0)
    print(p.split('/')[-1], "n", len(px), "| shadow", hsv(sel(0, q[0])), "| mid", hsv(sel(q[0], q[2])), "| light", hsv(sel(q[2], 999)))
