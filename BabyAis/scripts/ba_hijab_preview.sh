#!/bin/bash
# usage: ba_hijab_preview.sh BLEND OUTDIR  -> front/side/back full body + face, on white, sheet
P=/opt/bpyenv/bin/python
SMALL=1 SAMPLES=${SAMPLES:-20} VIEWS=front,left,back,34,face $P -I scripts/b10_present.py $PWD $1 $2 $PWD/scripts 2>&1 | grep -cE "VIEW"
for f in renders/$2/*.png; do case $f in *_w.png) ;; *) $P -I scripts/ba_white.py $f;; esac; done
$P -I scripts/ba_sheet.py renders/$2_sheet.png renders/$2/front_w.png renders/$2/left_w.png renders/$2/back_w.png renders/$2/face_w.png
