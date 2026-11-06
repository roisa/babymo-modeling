#!/bin/bash
# Rebuild b04 -> final deliverables (hair, clothing, materials, rig tests, presentation, QA). Run from BabyAis/.
set -e
P=/opt/bpyenv/bin/python; R=$PWD; S=$PWD/scripts
$P -I scripts/b04_hair.py $R $S 2>&1 | grep -E "HAIR|rror"
$P -I scripts/b05_clothing.py $R $S 2>&1 | grep -E "SAVED|rror|Trace"
$P -I scripts/b06_materials.py $R "AgX - Punchy" x $S 2>&1 | grep -E "SAVED|rror"
SAVE=1 ONLY=zzz $P -I scripts/b09_animtest.py $R checkpoints/BabyAis_v006_materials.blend zz $S 2>&1 | grep -E "SAVED|rror"
cp BabyAis_Working.blend checkpoints/BabyAis_v007_rigging.blend
rm -rf renders/anim_tests renders/final renders/zz
$P -I scripts/b09_animtest.py $R BabyAis_Working.blend anim_tests $S 2>&1 | grep -cE "^TEST"
SAMPLES=64 SAVE=BabyAis_Final.blend $P -I scripts/b10_present.py $R BabyAis_Working.blend final $S 2>&1 | grep -E "SAVED|rror"
cp BabyAis_Final.blend checkpoints/BabyAis_v008_final.blend; rm -f *.blend1 checkpoints/*.blend1
(cd renders/final && for f in front 34 left right back face hair; do $P -I ../../scripts/ba_white.py $f.png; done && $P -I ../../scripts/ba_turnaround.py . BabyAis_Turnaround.png)
(cd renders/anim_tests && for f in *.png; do $P -I ../../scripts/ba_white.py $f && rm $f; done && $P -I ../../scripts/ba_sheet.py AnimTests_Body.png 01_Idle_w.png 02_Walk_A_w.png 02_Walk_B_w.png 03_Run_w.png 04_Jump_w.png 05_Wave_w.png 06_Sit_w.png && $P -I ../../scripts/ba_sheet.py AnimTests_HeadFace.png 07_HeadTurnL_w.png 07_HeadTurnR_w.png 07_HeadNod_w.png 08_Happy_w.png 08_Surprised_w.png 08_Sad_w.png 08_Cheeky_w.png)
$P -I scripts/ba_qa.py $R/BabyAis_Final.blend $R/../.claude/skills/blender-asset-qa/scripts 2>&1 | grep -E "^QA_|^ERRORS"
echo ALLDONE
