"""Try yellow/exposure variants on one vehicle. args: BLEND OUTDIR VEHICLE then variants name:r,g,b:exposure:world:coat"""
import bpy, sys, math, os
from mathutils import Vector
blend, out, veh = sys.argv[1:4]
bpy.ops.wm.open_mainfile(filepath=blend); sc = bpy.context.scene
cd = bpy.data.cameras.new("Cam"); cd.lens = 70; cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
for c in ["Excavator", "DumpTruck", "Bulldozer", "CraneTruck", "CementMixer", "WheelLoader"]: bpy.data.collections[c].hide_render = (c != veh)
pts = [o.matrix_world @ Vector(cn) for o in bpy.data.collections[veh].objects if o.type in ('MESH', 'CURVE') for cn in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)]); ctr = (lo + hi) / 2
a, e = math.radians(38), math.radians(16); cam.location = ctr + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * (hi - lo).length * 2.1
cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.cycles.samples = 16; sc.render.resolution_x, sc.render.resolution_y = 480, 336
try: sc.render.image_settings.media_type = 'IMAGE'
except Exception: pass
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
y = bpy.data.materials["M_Toy_Yellow"].node_tree.nodes["Principled BSDF"]; bg = sc.world.node_tree.nodes["Background"]
for spec in sys.argv[4:]:
    n, col, ex, wd, coat, sp = spec.split(":")
    y.inputs["Specular IOR Level"].default_value = float(sp)
    y.inputs["Base Color"].default_value = (*map(float, col.split(",")), 1)
    sc.view_settings.exposure = float(ex); bg.inputs["Strength"].default_value = float(wd); y.inputs["Coat Weight"].default_value = float(coat)
    sc.render.filepath = f"{out}/{n}.png"; bpy.ops.render.render(write_still=True); print("R", n)
