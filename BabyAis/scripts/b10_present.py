"""BATCH 10 - presentation renders: Mo's standing pose (+ optional smile layer), white studio, views."""
import bpy, sys, os
sys.path.insert(0, sys.argv[-1]); import ba_common as C
root = sys.argv[1]; SRC = root + "/" + sys.argv[2]; OUT = root + "/renders/" + sys.argv[3]
bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene; rig = bpy.data.objects["Ais_Rig"]; ad = rig.animation_data
pose = bpy.data.actions[os.environ.get("POSE", "Ais_Pose_Presentation")]
ad.action = pose; ad.action_slot = pose.slots[0]
smile = os.environ.get("SMILE")
if smile:
    tr = ad.nla_tracks.get("PRESENT_Smile") or ad.nla_tracks.new(); tr.name = "PRESENT_Smile"; tr.mute = False
    for st in list(tr.strips): tr.strips.remove(st)
    a = bpy.data.actions[smile]; st = tr.strips.new("smile", 1, a); st.action_slot = a.slots[0]; st.blend_type = 'COMBINE'
    ad.action_blend_type = 'COMBINE'
for o in bpy.data.objects:                 # rig widget / custom-shape meshes never render
    if o.name.startswith(("WGT", "cs_")): o.hide_render = True
sc.frame_set(1); bpy.context.view_layer.update()
S = int(os.environ.get("SAMPLES", "48"))
H = rig.matrix_world @ rig.pose.bones["head"].head
views = os.environ.get("VIEWS", "front,34,left,right,back,face,hair").split(",")
SPEC = {"front": (0, 0.285, 1.95, 4), "34": (38, 0.285, 1.95, 4), "left": (90, 0.285, 1.95, 4), "right": (-90, 0.285, 1.95, 4),
        "back": (180, 0.285, 1.95, 4), "face": (8, H.z + 0.045, 0.62, 2), "hair": (140, H.z + 0.06, 0.75, 10)}
os.makedirs(OUT, exist_ok=True)
for v in views:
    az, tz, d, el = SPEC[v]
    res = (900, 1200) if v not in ("face", "hair") else (1000, 1000)
    if os.environ.get("SMALL"): res = (res[0] // 2, res[1] // 2)
    C.render_view(f"{OUT}/{v}.png", az, target=(0, 0, tz), dist=d, elev_deg=el, res=res, samples=S)
    print("VIEW", v)
# leave the scene camera on the front presentation framing
cam = C.ensure_cam(); a = 0.0
import math
from mathutils import Vector
cam.location = Vector((0, -1.95, 0.285 + 1.95 * math.sin(math.radians(4)))); C.look_at(cam, (0, 0, 0.285)); sc.camera = cam; cam.name = "Ais_PresentCam"
sc.render.resolution_x, sc.render.resolution_y = 1500, 2000; sc.cycles.samples = 128
if os.environ.get("SAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=root + "/" + os.environ["SAVE"], compress=True); print("SAVED", os.environ["SAVE"])
