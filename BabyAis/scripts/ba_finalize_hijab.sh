#!/bin/bash
# Build the hijab variant from BabyAis_Final.blend and produce its deliverables. Run from BabyAis/.
set -e
# hijab shape settings (refinement round 2, batch 29: cloth-simulated drape, ears hidden, head 0.88)
export OFF_TOP=0.023 OFF_SIDE=0.022 OFF_EDGE=0.003 COWL=0.024 THICK=0.0042 FOLD_AMP=0.0015 TIER_AMP=0.0045 DRAPE_AMP=0.0 HEM_WAVE=0.0 HEM_FRONT=0.296 HEM_BACK=0.258 HEM_SIDE_ADD=-0.015 BELL_W=0.0 R_SMOOTH=12 AW=64 TH_UP=32 TH_DN=33 THC=105 CHIN_ROLL=0.011 CHIN_T=139 CHIN_NARROW=0.46 CAP_BAND=12 NECK_T=126 BIB_POW=3 SIM_FRAMES=40 PIN_T=114 BEND=3 HEAD_SCALE=0.88
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
