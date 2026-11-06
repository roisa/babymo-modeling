import sys
from PIL import Image
out=sys.argv[1]; ims=[Image.open(p).convert("RGB") for p in sys.argv[2:]]
h=max(i.height for i in ims); w=sum(i.width for i in ims)
s=Image.new("RGB",(w,h),"white"); x=0
for i in ims: s.paste(i,(x,0)); x+=i.width
s.save(out)
