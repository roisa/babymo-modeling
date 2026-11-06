import sys, numpy as np
from PIL import Image, ImageFilter
for t in (1001, 1002):
    im = Image.open(f"renders/tex/skin.{t}.png").convert("RGB"); a = np.asarray(im).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mask = ((r - g) > 75) & ((g - b) > 25) | ((r - b) > 125)
    print(t, "blush px", int(mask.sum()))
    m = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(21)).filter(ImageFilter.GaussianBlur(4))
    mm = np.asarray(m).astype(np.float32)[..., None] / 255
    # fill: heavy blur of the image with blush pixels replaced by the global skin median
    med = np.median(a[~mask], axis=0)
    fill = a.copy(); fill[np.asarray(m) > 10] = med
    fill = np.asarray(Image.fromarray(fill.astype(np.uint8)).filter(ImageFilter.GaussianBlur(40))).astype(np.float32)
    out = a * (1 - mm) + fill * mm
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(f"textures/T_Ais_Skin_BaseColor.{t}.png")
