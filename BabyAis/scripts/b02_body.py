"""BATCH 02 - Baby Ais body: younger/smaller than Mo (94 %), rounder toddler belly, softer hips."""
import bpy, sys, numpy as np
sys.path.insert(0, sys.argv[-1]); import ba_common as C
root = sys.argv[1]
bpy.ops.wm.open_mainfile(filepath=root + "/BabyAis_Working.blend")
rig = bpy.data.objects["Ais_Rig"]
rig.scale = (C.MO_SCALE * 0.94,) * 3          # Ais is Mo's younger sister: 94 % of his height
bpy.context.view_layer.update()
body = bpy.data.objects["Ais_Body"]
P = C.world_coords(body); N = C.vertex_normals_world(body)
k = C.k_scale()
front = np.clip(-N[:, 1], 0, 1)               # only front-facing skin
d = np.zeros_like(P)
# toddler belly: round forward bulge below the chest
w = C.falloff(P, C.mo2w((0, -0.06, 0.215)), 0.085 * k, scale=(1.0, 1.0, 0.8)) * front
d += N * (w * 0.007 * k)[:, None]
# soft little hips / bum (side+back), kept subtle
for sx in (-1, 1):
    w = C.falloff(P, C.mo2w((sx * 0.06, 0.02, 0.15)), 0.06 * k)
    d += N * (w * 0.003 * k)[:, None]
C.apply_world_delta(body, d)
print("body verts moved:", int((np.linalg.norm(d, axis=1) > 1e-5).sum()), "max mm", round(np.linalg.norm(d, axis=1).max() * 1000, 2))
zs = C.world_coords(body)[:, 2]; print("height m", round(zs.max() - zs.min(), 4))
bpy.ops.wm.save_mainfile(compress=True)
bpy.ops.wm.save_as_mainfile(filepath=root + "/checkpoints/BabyAis_v002_body.blend", compress=True, copy=True)
print("SAVED v002")
