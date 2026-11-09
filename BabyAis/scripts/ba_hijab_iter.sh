#!/bin/bash
# usage: ba_hijab_iter.sh TAG   (shape params from the environment) -> build, preview, side-by-side with reference
set -e
P=/opt/bpyenv/bin/python
$P -I scripts/b11_hijab.py $PWD $PWD/scripts > /tmp/claude-0/-home-user/d08b9ecf-1286-5930-a76a-70e1a14fc8e0/scratchpad/hb_$1.log 2>&1 || { echo BUILD FAILED; tail -5 /tmp/claude-0/-home-user/d08b9ecf-1286-5930-a76a-70e1a14fc8e0/scratchpad/hb_$1.log; exit 1; }
grep -q "HIJAB SAVED" /tmp/claude-0/-home-user/d08b9ecf-1286-5930-a76a-70e1a14fc8e0/scratchpad/hb_$1.log || { echo NOT SAVED; exit 1; }
./scripts/ba_hijab_preview.sh BabyAis_Hijab_Working.blend $1 > /dev/null
$P -I -c "
from PIL import Image
r=Image.open('reference/BabyAis_Hijab_reference_v2.jpg').convert('RGB'); s=Image.open('renders/$1_sheet.png').convert('RGB')
r=r.resize((int(r.width*450/r.height),450)); s=s.resize((int(s.width*450/s.height),450))
o=Image.new('RGB',(r.width+s.width,450),'white'); o.paste(r,(0,0)); o.paste(s,(r.width,0)); o.save('/tmp/claude-0/-home-user/d08b9ecf-1286-5930-a76a-70e1a14fc8e0/scratchpad/cmp_$1.png')"
echo OK $1
