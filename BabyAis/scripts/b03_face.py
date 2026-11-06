"""BATCH 03 - Baby Ais face: fuller round cheeks, softer smaller chin, thin arched brown brows,
outer-corner lash flicks (joined into the lash mesh so blink shape keys + lid bones still drive them),
and a painted blush colour attribute that the skin shader reads (batch 06)."""
import bpy, bmesh, sys, math, numpy as np
from mathutils import Vector
sys.path.insert(0, sys.argv[-1]); import ba_common as C
root = sys.argv[1]
bpy.ops.wm.open_mainfile(filepath=root + "/checkpoints/BabyAis_v002_body.blend")
k = C.k_scale()
body = bpy.data.objects["Ais_Body"]
P = C.world_coords(body); N = C.vertex_normals_world(body)
d = np.zeros_like(P)
for sx in (-1, 1):
    # round apple cheeks (main identity cue of the reference)
    w = C.falloff(P, C.mo2w((sx * 0.066, -0.08, 0.383)), 0.045 * k, scale=(1, 0.8, 1))
    d += N * (w * 0.0048 * k)[:, None]
    # soft lower-cheek fullness toward the jaw -> rounder face outline
    w = C.falloff(P, C.mo2w((sx * 0.075, -0.05, 0.36)), 0.04 * k)
    d += N * (w * 0.0025 * k)[:, None]
# smaller softer chin
w = C.falloff(P, C.mo2w((0, -0.095, 0.343)), 0.026 * k)
d += N * (w * -0.0018 * k)[:, None]
C.apply_world_delta(body, d)
print("face verts moved", int((np.linalg.norm(d, axis=1) > 1e-5).sum()))

# ---- blush attribute (pink, soft, round - painted procedurally, editable in Vertex Paint)
P = C.world_coords(body)
bl = np.zeros(len(P))
for sx in (-1, 1):
    bl = np.maximum(bl, C.falloff(P, C.mo2w((sx * 0.07, -0.085, 0.39)), 0.032 * k, scale=(1.05, 0.6, 0.85)))
me = body.data
if "Ais_Blush" in me.attributes: me.attributes.remove(me.attributes["Ais_Blush"])
at = me.attributes.new("Ais_Blush", 'FLOAT', 'POINT'); at.data.foreach_set("value", bl.astype(np.float32))
print("blush verts", int((bl > 0.01).sum()))

# ---- brows: thinner, higher, more arched (girlish), keep mirror modifier
br = bpy.data.objects["Ais_Brows"]
Pb = C.world_coords(br)
print("brow verts", len(Pb), "x range", Pb[:, 0].min().round(4), Pb[:, 0].max().round(4))
xs = np.abs(Pb[:, 0])
# centre line per x-bin
bins = np.linspace(xs.min(), xs.max(), 9)
idx = np.clip(np.digitize(xs, bins) - 1, 0, 7)
zc = np.array([Pb[idx == i, 2].mean() if (idx == i).any() else 0 for i in range(8)])
zc_v = zc[idx]
t = (xs - xs.min()) / (xs.max() - xs.min())           # 0 inner .. 1 outer
db = np.zeros_like(Pb)
db[:, 2] = (Pb[:, 2] - zc_v) * (0.62 - 1.0)            # thinner stroke
db[:, 2] += (0.0022 + 0.0022 * np.sin(np.pi * np.clip(t * 1.1, 0, 1))) * k   # lift + arch peak at 1/2..2/3
db[:, 2] -= 0.0012 * np.clip((t - 0.75) / 0.25, 0, 1) * k                      # tail drops slightly
db[:, 1] -= 0.0004 * k                                                         # stays on the skin after lift
C.apply_world_delta(br, db)

# ---- lash flicks: 3 tapered curved lashes at each outer corner, joined into Ais_Lashes
la = bpy.data.objects["Ais_Lashes"]
Pl = C.world_coords(la)
me = la.data
bm = bmesh.new(); bm.from_mesh(me)
nv0 = len(bm.verts)
inv = la.matrix_world.inverted()
anchors = []  # (new vert index range, anchor vert index)
deform = me.vertices
for sx in (-1, 1):
    side = np.where(Pl[:, 0] * sx > 0.01 * k)[0]
    # top edge of the lash strip: the highest verts, ordered along x
    xs_ = Pl[side, 0] * sx
    outer = side[np.argsort(-xs_)][:40]
    upper = outer[np.argsort(-Pl[outer, 2])][:14]       # upper outer-corner region
    upper = upper[np.argsort(-Pl[upper, 0] * sx)]
    picks = [upper[0], upper[min(4, len(upper)-1)], upper[min(9, len(upper)-1)]]
    for j, ai in enumerate(picks):
        base = Vector(Pl[ai])
        L = (0.0105 - 0.0022 * j) * k
        out = Vector((sx * 0.75, -0.25, 0.55)).normalized()
        up = Vector((sx * 0.35, -0.15, 1.0)).normalized()
        rings = []
        for s in range(7):
            u = s / 6
            c = base + (out * (1 - u) + up * u).normalized() * (L * u) + out * (L * 0.35 * u)
            r = (0.00145 * (1 - u) ** 0.8 + 0.00012) * k
            ring = []
            for q in range(5):
                a = 2 * math.pi * q / 5
                off = Vector((math.cos(a), 0, math.sin(a))) * r
                ring.append(bm.verts.new(inv @ (c + Vector((off.x * 0.5, off.y + math.cos(a) * r * 0.6, off.z)))))
            rings.append(ring)
        for s in range(6):
            for q in range(5):
                a, b2 = rings[s][q], rings[s][(q + 1) % 5]; c2, d2 = rings[s + 1][(q + 1) % 5], rings[s + 1][q]
                bm.faces.new((a, b2, c2, d2))
        bm.faces.new(list(reversed(rings[0])))
        tip = bm.verts.new(inv @ (base + (out * 0.3 + up).normalized() * L * 1.05 + out * L * 0.4))
        for q in range(5): bm.faces.new((rings[6][q], rings[6][(q + 1) % 5], tip))
        anchors.append((ai, 7 * 5 + 1))
bm.to_mesh(me); bm.free()
# weights + shape keys follow the anchor vertex rigidly
vi = nv0
for ai, n in anchors:
    for g in me.vertices[ai].groups:
        la.vertex_groups[g.group].add(list(range(vi, vi + n)), g.weight, 'REPLACE')
    if me.shape_keys:
        base_co = me.shape_keys.key_blocks[0].data[ai].co.copy()
        for kb in me.shape_keys.key_blocks[1:]:
            dv = kb.data[ai].co - base_co
            for i in range(vi, vi + n): kb.data[i].co = me.vertices[i].co + dv
        for i in range(vi, vi + n): me.shape_keys.key_blocks[0].data[i].co = me.vertices[i].co
    vi += n
me.update()
print("lash flicks added verts", vi - nv0)
bpy.ops.wm.save_as_mainfile(filepath=root + "/BabyAis_Working.blend", compress=True)
print("SAVED working (face pass)")
