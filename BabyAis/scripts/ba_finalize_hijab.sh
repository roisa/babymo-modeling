#!/bin/bash
# Build the hijab variant from BabyAis_Final.blend and produce its deliverables. Run from BabyAis/.
set -e
# hijab shape settings (refinement round 2, batch 17)
export OFF_TOP=0.012 OFF_SIDE=0.014 OFF_EDGE=0.003 COWL=0.017 THICK=0.0038 FOLD_AMP=0.0018 TIER_AMP=0.0048 DRAPE_AMP=0.003 HEM_WAVE=0.002 HEM_FRONT=0.305 HEM_BACK=0.288 BELL_W=0.15 R_SMOOTH=70 AW=64 TH_UP=32 TH_DN=33 THC=105 CHIN_ROLL=0.009 CHIN_T=139 CHIN_NARROW=0.46 CAP_BAND=12 HEAD_SCALE=0.88
P=/opt/bpyenv/bin/python; R=$PWD; S=$PWD/scripts
OUT=BabyAis_Hijab_Final.blend $P -I scripts/b11_hijab.py $R $S 2>&1 | grep -E "SAVED|rror"
rm -rf renders/hijab_final renders/hijab_anim_tests
$P -I scripts/b09_animtest.py $R BabyAis_Hijab_Final.blend hijab_anim_tests $S 2>&1 | grep -cE "^TEST"
SAMPLES=64 SAVE=BabyAis_Hijab_Final.blend $P -I scripts/b10_present.py $R BabyAis_Hijab_Final.blend hijab_final $S 2>&1 | grep -E "SAVED|rror"
rm -f *.blend1
(cd renders/hijab_final && for f in front 34 left right back face hair; do $P -I ../../scripts/ba_white.py $f.png; done && $P -I ../../scripts/ba_turnaround.py . BabyAis_Hijab_Turnaround.png "hijab edition")
(cd renders/hijab_anim_tests && for f in *.png; do $P -I ../../scripts/ba_white.py $f && rm $f; done && $P -I ../../scripts/ba_sheet.py AnimTests_Body.png 01_Idle_w.png 02_Walk_A_w.png 02_Walk_B_w.png 03_Run_w.png 04_Jump_w.png 05_Wave_w.png 06_Sit_w.png && $P -I ../../scripts/ba_sheet.py AnimTests_HeadFace.png 07_HeadTurnL_w.png 07_HeadTurnR_w.png 07_HeadNod_w.png 08_Happy_w.png 08_Surprised_w.png 08_Sad_w.png 08_Cheeky_w.png)
$P -I scripts/ba_qa.py $R/BabyAis_Hijab_Final.blend $R/../.claude/skills/blender-asset-qa/scripts 2>&1 | grep -E "^QA_|^ERRORS"
echo ALLDONE
