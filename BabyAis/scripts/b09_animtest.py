"""BATCH 08/09 - rig check + animation tests on Baby Ais.  Re-imports Mo's standing presentation pose,
adds a head-rotation test action, stores every test as a muted NLA track on Ais_Rig (kept in the file),
and renders one review frame per test."""
import bpy, sys, os, math
from mathutils import Quaternion, Vector
sys.path.insert(0, sys.argv[-1]); import ba_common as C
root = sys.argv[1]; SRC = root + "/" + sys.argv[2]; OUT = root + "/renders/" + sys.argv[3]
bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene; rig = bpy.data.objects["Ais_Rig"]
if "Ais_Pose_Presentation" not in bpy.data.actions:
    with bpy.data.libraries.load(root + "/reference/BABY_MO_v008_ORIGINAL.blend", link=False) as (src, dst):
        dst.actions = ["rigAction"]
    a = dst.actions[0]; a.name = "Ais_Pose_Presentation"
a = bpy.data.actions["Ais_Pose_Presentation"]; a.use_fake_user = True
# ---- custom head-rotation test (turn L/R, nod, tilt) on the Rigify 'head' control
ht = bpy.data.actions.get("AisTest_HeadTurn") or bpy.data.actions.new("AisTest_HeadTurn"); ht.use_fake_user = True
rig.animation_data_create()
rig.animation_data.action = ht
pb = rig.pose.bones["head"]
for f, axis, ang in ((1, (0, 1, 0), 0), (12, (0, 1, 0), 50), (24, (0, 1, 0), -50), (36, (1, 0, 0), 22), (48, (0, 0, 1), 20), (60, (0, 1, 0), 0)):
    pb.rotation_quaternion = Quaternion(axis, math.radians(ang)); pb.keyframe_insert("rotation_quaternion", frame=f)
pb.rotation_quaternion = (1, 0, 0, 0)
rig.animation_data.action = None
TESTS = [("01_Idle", "Idle_breathing", 0.5), ("02_Walk_A", "Locomotion_Walk", 0.25), ("02_Walk_B", "Locomotion_Walk", 0.75),
         ("03_Run", "Locomotion_Run", 0.3), ("04_Jump", "Locomotion_Jumping", 0.5), ("05_Wave", "Idle_Wave", 0.35),
         ("06_Sit", "Locomotion_Sit", 0.85), ("07_HeadTurnL", "AisTest_HeadTurn", 12), ("07_HeadTurnR", "AisTest_HeadTurn", 24),
         ("07_HeadNod", "AisTest_HeadTurn", 36), ("08_Happy", "Face_Happy_1", 1), ("08_Surprised", "Face_Surprised_1", 1),
         ("08_Sad", "Face_Sad_1", 1), ("08_Cheeky", "Face_Cheeky_1", 1)]
ad = rig.animation_data
for tr in list(ad.nla_tracks):
    if tr.name.startswith("TEST_"): ad.nla_tracks.remove(tr)
for name, act, _ in TESTS:
    tr = ad.nla_tracks.new(); tr.name = "TEST_" + name; tr.mute = True
    acto = bpy.data.actions[act]
    st = tr.strips.new(name, int(acto.frame_range[0]), acto); st.action_slot = acto.slots[0] if acto.slots else None
only = os.environ.get("ONLY")
os.makedirs(OUT, exist_ok=True)
for name, act, fr in TESTS:
    if only and only not in name: continue
    acto = bpy.data.actions[act]
    ad.action = acto
    if acto.slots: ad.action_slot = acto.slots[0]
    f0, f1 = acto.frame_range
    f = int(round(f0 + (f1 - f0) * fr)) if fr < 1 else int(fr)
    sc.frame_set(f)
    bpy.context.view_layer.update()
    tgt = rig.matrix_world @ rig.pose.bones["torso"].head
    face = name.startswith("08") or name.startswith("07")
    az = 30 if not name.startswith("06") else 60
    if face:
        h = rig.matrix_world @ rig.pose.bones["head"].head
        C.render_view(f"{OUT}/{name}.png", 15, target=(h.x, h.y, h.z + 0.04), dist=0.8, elev_deg=0, res=(320, 360), samples=12)
    else:
        C.render_view(f"{OUT}/{name}.png", az, target=(tgt.x, tgt.y, tgt.z + 0.07), dist=1.9, elev_deg=4, res=(320, 420), samples=12)
    print("TEST", name, act, "frame", f)
ad.action = a
if a.slots: ad.action_slot = a.slots[0]
sc.frame_set(1)
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=root + "/BabyAis_Working.blend", compress=True)
    print("SAVED working with tests")
