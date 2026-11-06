#!/bin/bash
# usage: ba_headviews.sh BLEND OUTDIR [samples]
S=${3:-16}
/opt/bpyenv/bin/python -I scripts/ba_render_views.py $1 $2 $PWD/scripts -- h_front:0:0.41:0.85:2:480:520:$S h_34:40:0.41:0.85:2:480:520:$S h_left:90:0.41:0.85:2:480:520:$S h_right:-90:0.41:0.85:2:480:520:$S h_back:180:0.41:0.85:2:480:520:$S 2>&1 | grep -c RENDER
/opt/bpyenv/bin/python -I scripts/ba_sheet.py $2/head_sheet.png $2/h_front.png $2/h_34.png $2/h_left.png $2/h_right.png $2/h_back.png
