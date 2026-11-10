# Baby Mo Sports: tennis poses

20 transparent PNG poses of Baby Mo playing tennis, for the Baby Mo sports games app and motion graphics.

- **PNGs:** `renders/tennis/BabyMo_Tennis_NN_name.png`, 1200 × 1200, transparent background. All are shot from one camera at the same scale and ground line, so you can swap poses in place for animation without re-aligning.
- **Overview:** `renders/BabyMo_Tennis_Sheet.png`. All PNGs zipped: `renders/BabyMo_Tennis_20_Poses_PNG.zip`.
- **Titles:** `renders/tennis/poses.csv` gives each pose's title in Indonesian and English.
- **Editable file:** `BabyMo_Tennis_Poses.blend`. Frame N holds pose N, and the racket and ball are keyed with each pose. Open it, go to a frame, adjust, and render.

| # | Pose | Use in a game |
|---|---|---|
| 01 | Ready position | idle |
| 02 | Split step (hop) | waiting for the ball |
| 03 | Run to the ball | moving |
| 04–06 | Forehand: backswing → contact → follow-through | forehand hit animation |
| 07–09 | Backhand: backswing → contact → follow-through | backhand hit animation |
| 10 | Bounce the ball | before serve |
| 11–14 | Serve: toss → trophy → contact → follow-through | serve animation |
| 15 / 16 | Forehand / backhand volley | net play |
| 17 | Overhead smash (jump) | power shot |
| 18 | Lunge for a wide ball | stretch save |
| 19 | Jump for joy | point won |
| 20 | Oops, missed | point lost |

## How they're made
- `scripts/mo_pose_kit.py` poses Mo's Rigify rig. It switches the limbs to FK, aims each arm and leg bone along a world direction, turns and leans the body, keeps the feet flat, turns the fist to follow the racket, borrows Mo's own face expressions, and grounds the feet automatically.
- `scripts/tennis_props.py` builds the toy racket and the tennis ball (with the real seam curve) and sets up the fixed orthographic sprite camera.
- `scripts/tennis_poses.py` holds the 20 poses; each is a short, readable function.

To re-render (needs Blender 5.2's Python with `bpy`, and the original `BABY_MO_v008.blend`):
```bash
SAVE_LIB=$PWD/BabyMo_Tennis_Poses.blend RES=1200 SAMPLES=48 python scripts/tennis_poses.py BABY_MO_v008.blend renders/tennis scripts
ONLY=05,13 RES=400 SAMPLES=8 python scripts/tennis_poses.py BABY_MO_v008.blend /tmp/test scripts   # quick drafts of chosen poses
```
The same kit works for other sports: add a props file and a poses file.
