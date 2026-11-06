# Baby Ais (No Hijab Edition): Production Completion Report

**Final file:** `BabyAis_Final.blend` (Blender 5.2.3 LTS, Cycles, all textures packed)
**Turnaround:** `renders/final/BabyAis_Turnaround.png`
**Animation tests:** `renders/anim_tests/AnimTests_Body.png`, `renders/anim_tests/AnimTests_HeadFace.png`

Baby Ais is Baby Mo's younger sister: a toddler girl with large dark-brown eyes, round blushing cheeks, a gentle smile, a short almost-black side-parted bob, and the pink-and-lavender romper outfit from the reference sheet. She is built on the Baby Mo production foundation (rig, skin shader, lights, conventions) and has her own head and face shaping, hair, proportions and clothing.

---

## Deliverables

| # | Deliverable | Where |
|---|---|---|
| 1 | Final project | `BabyAis_Final.blend` (also `checkpoints/BabyAis_v008_final.blend`) |
| 2 | Editable character geometry | collection `GEO Baby Ais` (all meshes, modifiers live and not applied) |
| 3 | Organized collections | `AIS_Body`, `AIS_Face`, `AIS_Hair`, `AIS_Clothing`, `RIG_Ais`, `Studio` |
| 4 | Editable materials | 14 `M_Ais_*` node materials, Ais-owned copies, so Baby Mo's materials are never edited |
| 5 | Short black bob | 5 hair objects, 54 sculpted locks plus a scalp cap |
| 6 | Pink and lavender outfit | romper, shirt/sleeves, cuffs, pockets, moon emblem, shoes, soles |
| 7 | Functional rig | `Ais_Rig`: Baby Mo's Rigify rig (966 bones, full face rig), scaled to Ais |
| 8 | Animation tests | 14 muted NLA tracks `TEST_*` on `Ais_Rig`, plus test renders |
| 9 | Renders | `renders/final/`: front, ¾, left, right, back, face close-up, hair close-up (`*_w.png` = on white) |
| 10 | This report | `PRODUCTION_REPORT.md` |

The checkpoints are `checkpoints/BabyAis_v001_base` through `v008_final`. The working file is `BabyAis_Working.blend`. The original Baby Mo file was never written to: the scripts open a read-only copy.

**Every batch is a re-runnable script** in `scripts/` (`b01_setup.py` … `b10_present.py`). Running them in order rebuilds every checkpoint from the original Baby Mo file. The run commands are at the end of this report.

---

## What was built, batch by batch

**01 Inspection and setup.** Inspected Baby Mo: Cycles/AgX, 3-point studio, orthographic camera, Rigify rig (966 bones, 173 deform), UDIM skin textures, shape-key blinks, and 100+ actions (locomotion, gestures, face poses, visemes). Created the Ais collection layout and `Ais_` naming. Made Ais-owned material copies. Removed Mo's own hair, outfit and star emblem. Removed 16 broken drivers that pointed at missing mask modifiers.

**02 Body.** Ais is 94% of Mo's size (0.557 m body, 0.567 m with hair), keeping the large toddler head. Gave her a rounder toddler belly (+7 mm) and softer hips. Edits are applied to the base mesh and every shape key together, so blinks and correctives still work.

**03 Face.** Fuller round apple cheeks with softer lower-cheek fullness, and a smaller, softer chin. Brows are thinner, higher and arched, in their own dark-brown material. There are 3 tapered lash flicks at each outer corner; they are joined into the lash mesh so lid bones and blink shape keys drive them. Eyes are dark chocolate brown with the warm iris ring visible. Blush is soft rose, from an editable `Ais_Blush` vertex attribute. Mo's painted orange blush ovals were removed in a new Ais-owned skin texture (`T_Ais_Skin_BaseColor`).

**04 Hair (6 review cycles).** Built in layers:
1. scalp cap
2. inner back fill layer (17 locks)
3. outer back layer (21 locks) radiating from the crown
4. side sections sweeping from an off-centre part over the tops of the ears and tucking behind them
5. a staggered side-swept fringe

Each lock is a tapered lens-section ribbon with UVs. A clearance pass keeps every lock at least 2.5 mm off the face, ears and neck. The shader is almost-black chocolate with strand bump, anisotropic sheen and darker roots. The hair is rigid to the head bone. Iterations fixed: a helmet look and layer steps (one shared volume profile), a narrow front view (side flare), the shelf above the ears, hook-like framing locks (removed), the mushroom back (gentler flare), and grey colour (darker base, lower specular). Iteration sheets are in `renders/progress/hair_*.png`.

**05 Clothing.** Each garment is a fitted shell offset from the body, with fabric thickness, and every opening cut with a clean plane:
- **Lavender shirt:** long sleeves plus a collar band that shows above the romper. The hidden torso is removed to prevent layer poke-through.
- **Hot-pink sleeveless romper:** scooped neckline, armholes at the shoulder joint, legs to the ankle.
- **Light-blue cuffs:** banded and measured around the wrist axis.
- **Purple shoes:** rounded toddler shoes (rounded-box uppers) with **light-blue soles**.
- **Two purple pockets** with rounded corners, and a **raised white crescent moon**, both projected onto the romper surface.

Body faces fully covered by clothes are hidden with a Mask modifier (vertex group `Hidden_Clothes`), keeping one ring at every opening.

**06 Materials and lighting.** Soft cotton fabrics (sheen, fine grain bump, subtle value breakup), satin shoes, gentle subsurface on the skin, and the hair look-dev. Baby Mo's own light rig is reused unchanged. The world is high-key white, with a shadow-catcher floor. View transform is AgX (as in Mo's file) at −0.4 exposure. Round 3 switches the look to Punchy.

**07 Refinement.** Reviewed every view against the reference and re-ran the whole scripted chain several times:
- back silhouette slimmed so the dome flows into the bob with inward-curving ends
- side "wings" at ear height evened out
- hair darkened to almost black
- iris ring brightened
- the clean back view confirmed
- QA warnings fixed: hair normals, missing UVs on cuffs, pockets and moon, empty UVs on shoes

**07b Refinement round 2 (after review feedback: "looks weird").** Compared again, strictly, against the reference sheet. These changes are scripted into batches 03–06 and the whole chain was rebuilt:
- **Eyes:** removed Mo's dark lower liner (it ringed the whole eye), leaving a thick upper lash line only, with short, thick, curled flicks at the outer corners. The warm-brown iris and the eye whites now read like the reference.
- **Skin:** graded to lighter, warmer peach (a `Skin Grade` node in `M_Ais_Skin`, editable), with a slightly stronger pink blush.
- **Hair:**
  - the pinstripe strand texture is replaced by fine, subtle strands, with glossier shading
  - locks are wider and flatter so they overlap into one smooth mass, without ridges
  - the crown is fuller and rounder
  - the bob is longer, about 2 cm below the chin like the sheet, and frames the face from the front
- **Shoes:** smaller, rounder toddler shoes with a thinner light-blue sole.

Before and after sheets: `renders/progress/refine2_*.png`. The final renders, turnaround, animation tests and QA (pass, 0 errors) were regenerated from the rebuilt file.

**07c Round 3: new hairstyle and refined clothes** (from the second reference sheet, `reference/BabyAis_reference_v2.png`).

*Hair.* The bob is redesigned as a longer, layered, softly voluminous cut to shoulder level:
- the crown is fuller and rounder
- a gentle outward curve runs through the length, with a soft S-wave in each lock
- tips are feathered and tapered, with varied lengths, instead of blunt
- a new shorter **top layer** (`Ais_Hair_TopLayer`) sits over the long back layer to give visible layering
- locks from the part fall down each side of the forehead and frame it in an arch, like the sheet, replacing the side-swept band
- ears stay visible in front of the hair

*Clothes.*
- The romper is smoothed from the hips down: no seat crease or knee bumps.
- Its legs are inflated into straight, rounded toddler trousers, with a guard keeping the fabric at least 6 mm outside the skin.
- The blotchy fabric breakup pattern is removed, leaving a clean, smooth fabric with a light sheen.
- The pink moves toward the sheet's hot magenta-pink.
- Pockets are bigger, U-shaped (straight top, round bottom) and lavender.
- The moon is bigger, the sleeves and cuffs a little puffier.
- The colour look changes to **AgX – Punchy** (exposure −0.4) for the saturated reference palette.

**08 Rigging.** Baby Mo's Rigify rig is reused and scaled to Ais. It provides pelvis, spine, chest, neck and head; shoulders; arms with IK/FK; hands with all fingers; legs and feet; and the Rigify face rig (brows, lids, eyes, jaw, lips, cheeks, tongue) for facial controls. Skinning:
- **Body and face:** keep Mo's weights.
- **Hair:** rigid to `DEF-spine.006` (head).
- **Shirt and romper:** each vertex copies the exact weights of the body vertex it was built from.
- **Cuffs and shoes:** weights come from same-side arm or foot vertices only.
- **Pockets and moon:** ride the romper surface with Surface Deform. They also carry skin weights for engine export.

**09 Animation tests** (14 tests, all stored in the file):
- **Body:** idle, walk (2 phases), run, jump, wave, sit
- **Head:** turn left 50°, turn right 50°, nod
- **Face:** happy, surprised, sad, cheeky wink

Bugs found and fixed during testing:
1. Cuffs stretched into straps because they had picked up pelvis weights.
2. Romper and shirt shredded because vertices created by the plane cuts got interpolated source indices.
3. Shirt poked through the romper chest during walk.
4. Moon and pockets sank into the romper, then were misplaced, because the subdivision level differed between viewport and render.

Final result: clean deformation in all 14 tests. Sheets are in `renders/progress/animtest_*.png` (before and after).

**10 Presentation.** Seven views at 900×1200 (close-ups 1000×1000), 64 samples, shadow catcher composited on pure white, plus the turnaround sheet. The file's scene camera is left at the front presentation framing (1500×2000, 128 samples).

---

## Technical summary

- **Meshes (base cage, editable):** body 7.3k verts (Mo topology), hair ~17k, outfit ~5.3k. At render subdivision the whole character is about 340k tris.
- **Real-time use:** apply or limit Subdivision to level 0–1, which gives roughly 60–90k tris. For the lowest mobile budgets, decimate the hair locks or use LODs (see the `blender-game-optimization` skill).
- **QA** (`blender-asset-qa`, render profile): **PASS, 0 errors.** The remaining warnings are inherited from Mo's face meshes (unapplied teeth and tongue scale, more than 4 bone influences on some body and lash vertices) or cosmetic (overlapping UVs on lock end caps, duplicate vertices where hair locks meet, 4 inconsistent edges on the moon patch).
- **Default pose:** `Ais_Pose_Presentation` (Mo's standing pose). The test animations are in the NLA editor: unmute one `TEST_*` track to play it.

## Known limitations and honest notes

1. **Body base topology comes from Baby Mo.** Ais's body is Mo's production body mesh, reshaped (size, belly, hips, cheeks, chin). That keeps the UVs, skin textures, blink shape keys and the entire rig and action library compatible, which is standard practice for sibling characters. Her hair, clothing, brows, lashes, blush and eye colour are new.
2. **Eyes in head-turn tests.** The Rigify eye target stays fixed in space, so the eyes hold focus when the head turns or nods. This is expected rig behaviour; parent the `eyes` control to the head if you prefer them to follow.
3. **Pockets and moon use Surface Deform** to follow the romper. Game engines don't export that modifier, so for export remove it and add an Armature modifier (the skin weights are already on the objects).
4. **White background.** The `.blend` renders on transparent film with a shadow catcher. The white sheets were composited afterwards (`scripts/ba_white.py`).
5. **Facial animation coverage.** The facial expression tests use Mo's face pose library. The lip-sync visemes (`MOUTH_*`) are in the file but weren't individually reviewed.
6. **Back silhouette.** A very slight step remains at ear height where the side sections meet the back locks.
7. **Reference image.** The reference sheet was supplied in chat and isn't stored in the repo. Hair and outfit proportions were matched to it visually.
8. **Blender version.** Blender was run headless (the `bpy` 5.2.3 module), because blender.org downloads were blocked in this environment. The file opens normally in Blender 5.2+.

## Rebuild

```bash
# needs the read-only copy of the original Baby Mo file at reference/BABY_MO_v008_ORIGINAL.blend
PY="python -I"          # Blender 5.2 python with bpy (here: /opt/bpyenv/bin/python)
R=$PWD; S=$PWD/scripts
$PY scripts/b01_setup.py $R/reference/BABY_MO_v008_ORIGINAL.blend $R
$PY scripts/b02_body.py $R $S
$PY scripts/b03_face.py $R $S && $PY scripts/b03b_face_shading.py $R $S && $PY scripts/b03c_skin_tex.py $R $S
$PY scripts/b04_hair.py $R $S
$PY scripts/b05_clothing.py $R $S
$PY scripts/b06_materials.py $R "AgX - Punchy" x $S
SAVE=1 $PY scripts/b09_animtest.py $R checkpoints/BabyAis_v006_materials.blend anim_tests $S
cp BabyAis_Working.blend checkpoints/BabyAis_v007_rigging.blend
SAVE=BabyAis_Final.blend $PY scripts/b10_present.py $R BabyAis_Working.blend final $S
```
