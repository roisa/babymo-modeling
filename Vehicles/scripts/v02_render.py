"""Render each vehicle collection on its own in a 3/4 view (transparent + shadow) and composite a white sheet.
Usage: python v02_render.py BLEND OUTDIR [samples] [w h]"""
import bpy, sys, math, os
from mathutils import Vector
blend, out = sys.argv[1], sys.argv[2]
S = int(sys.argv[3]) if len(sys.argv) > 3 else 32
W, H = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (800, 560)
bpy.ops.wm.open_mainfile(filepath=blend); sc = bpy.context.scene
os.makedirs(out, exist_ok=True)
NAMES = ["Excavator", "DumpTruck", "Bulldozer", "CraneTruck", "CementMixer", "WheelLoader"]
cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
cd.lens = 70
sc.cycles.samples = S; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = W, H
try: sc.render.image_settings.media_type = 'IMAGE'
except Exception: pass
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
AZ = float(os.environ.get("AZ", "38"))
for n in NAMES:
    for c in NAMES: bpy.data.collections[c].hide_render = (c != n)
    root = bpy.data.objects[n + "_Root"]
    pts = [o.matrix_world @ Vector(cn) for o in bpy.data.collections[n].objects if o.type in ('MESH', 'CURVE') for cn in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    ctr = (lo + hi) / 2; size = (hi - lo).length
    a, e = math.radians(AZ), math.radians(16)
    d = size * float(os.environ.get('DIST', '2.1'))
    cam.location = ctr + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d
    cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"{out}/{n}.png"
    bpy.ops.render.render(write_still=True); print("RENDERED", n)
