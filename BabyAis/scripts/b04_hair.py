"""BATCH 04 - Baby Ais short black bob: real editable mesh hair built in layers.
 1 scalp-following base cap   2 back bob (inner + outer lock layers, crown-rooted, inward-curving ends)
 3 side sections that sweep over the ears and tuck behind them   4 side-swept front fringe from an
 off-centre part   5 face-framing temple locks.   Every lock is a tapered lens-section ribbon with UVs
 (v = root->tip) for strand shading; a clearance pass keeps all hair off face, ears and neck.
Geometry is authored in Baby-Mo space (head centre (0,.012,.47), skull r~.122) and scaled to Ais (k)."""
import bpy, bmesh, sys, math, random
import numpy as np
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0, sys.argv[-1]); import ba_common as C
root = sys.argv[1]
SRC = sys.argv[2] if len(sys.argv) > 3 else root + "/checkpoints/BabyAis_v003_face.blend"
bpy.ops.wm.open_mainfile(filepath=SRC)
random.seed(7)
k = C.k_scale()
rig = bpy.data.objects["Ais_Rig"]; rig.data.pose_position = 'REST'
body = bpy.data.objects["Ais_Body"]
_sub = [m for m in body.modifiers if m.type == "SUBSURF"]
for m in _sub: m.show_viewport = False
dg = bpy.context.evaluated_depsgraph_get(); dg.update()
be = body.evaluated_get(dg); me = be.to_mesh()
P = np.array([body.matrix_world @ v.co for v in me.vertices]) / k        # Mo space
# ear verts (excluded from the skull surface so hair passes over/behind ears, not around them)
vgi = {g.index: g.name for g in body.vertex_groups}
ear = np.zeros(len(body.data.vertices), bool)
for v in body.data.vertices:
    for g in v.groups:
        if vgi[g.group].startswith("DEF-ear") and g.weight > 0.25: ear[v.index] = True
# evaluated mesh == base topology? (subsurf off in viewport for this probe)
polys = [p.vertices[:] for p in me.polygons]
if len(me.vertices) == len(ear):
    polys_skull = [p for p in polys if not any(ear[i] for i in p)]
else:
    polys_skull = polys
bvh_all = BVHTree.FromPolygons([Vector(p) for p in P], polys)
bvh_sk = BVHTree.FromPolygons([Vector(p) for p in P], polys_skull)
be.to_mesh_clear()
for m in _sub: m.show_viewport = True
print("skull polys", len(polys_skull), "of", len(polys))
Cc = Vector((0, 0.012, 0.47))

def sph(a, t):
    a, t = math.radians(a), math.radians(t)
    return Vector((math.sin(t) * math.sin(a), math.sin(t) * math.cos(a), math.cos(t)))

def skull(d):
    hit = bvh_sk.ray_cast(Cc + d * 0.4, -d)
    return (hit[0] - Cc).length if hit[0] else 0.12

XP = -0.017
FLARE_ADD = 0.0
WAVE_PH = 0.0
BULGE = 0.011                                    # part line x (her right of centre, as in the reference)
def part_dir(phi):
    """phi: +58 front hairline ... -30 crown (deg, in the y-z plane)."""
    ph = math.radians(phi)
    d = Vector((0, -math.sin(ph), math.cos(ph)))
    r = skull(d); p = Cc + d * r; p.x = XP
    return (p - Cc).normalized()

def slerp(a, b, t):
    return Quaternion(a.rotation_difference(b)).slerp(Quaternion(), 1 - t) @ a if False else a.slerp(b, t) if hasattr(a, "slerp") else (a * (1 - t) + b * t).normalized()

def catmull(pts, n):
    pts = [pts[0] + (pts[0] - pts[1])] + pts + [pts[-1] + (pts[-1] - pts[-2])]
    out = []
    seg = len(pts) - 3
    for i in range(n):
        u = i / (n - 1) * seg; j = min(int(u), seg - 1); t = u - j
        p0, p1, p2, p3 = pts[j:j + 4]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return out

def scalp_path(wps):
    """wps: list of (dir, off). Densify with direction slerp, project to skull + offset."""
    pts = []
    for (d0, o0), (d1, o1) in zip(wps[:-1], wps[1:]):
        for s in range(6):
            t = s / 6
            d = d0.slerp(d1, t).normalized() if hasattr(d0, 'slerp') else (d0 * (1 - t) + d1 * t).normalized()
            pts.append(Cc + d * (skull(d) + vol(d, o0 * (1 - t) + o1 * t)))
    d, o = wps[-1]; pts.append(Cc + d * (skull(d) + vol(d, o)))
    return pts

LAYER_D = 0.0
def vol(d, o):
    """Cohesive dome: volume grows from the part/crown to the widest point just above the ears.
    The waypoint offset only matters at the root (o < .006 -> root lift); LAYER_D separates layers."""
    th = math.degrees(math.acos(max(-1, min(1, d.z))))
    v = 0.011 + 0.011 * min(max((th - 5) / 55, 0), 1) ** 0.7 + 0.006 * min(max((th - 55) / 35, 0), 1)
    v *= 1 - 0.85 * max(0.0, -d.y - 0.25) / 0.75      # flatter at the forehead hairline
    if o < 0.0045: v = min(v, 0.0035)    # roots at the part sit close to the scalp
    return v + LAYER_D

def hang(p0, z_end, flare=0.006, tuck=0.012, curl=0.006):
    side = min(abs(math.degrees(math.atan2(p0.x - Cc.x, p0.y - Cc.y))) / 72, 1.2)
    flare = flare + FLARE_ADD + 0.010 * side ** 2; tuck = tuck + 0.001 * side
    """Bob drop from p0 straight down to z_end with a slight outward flare then an inward curl."""
    h = Vector((p0.x - Cc.x, p0.y - Cc.y, 0)); R0 = h.length; h.normalize()
    pts = []; n = 10
    for i in range(1, n + 1):
        s = i / n
        z = p0.z + (z_end - p0.z) * s
        peak = 0.62 - 0.27 * min(side, 1)
        R = R0 + flare * math.sin(min(s / peak, 1) * math.pi / 2)
        R += BULGE * math.sin(math.pi * min(s / 0.92, 1.0)) + 0.0018 * math.sin(s * math.pi * 1.6 + WAVE_PH)
        if s > 0.72:
            q = (s - 0.72) / 0.28
            R -= tuck * q * q
            z += curl * q * q
        pts.append(Vector((Cc.x, Cc.y, 0)) + h * R + Vector((0, 0, z)))
    return pts

locks = []   # (name, centreline pts (Mo space), width, thickness, layer)
def add_lock(name, pts, w, t, layer, tipw=0.16):
    locks.append((name, pts, w, t, layer, tipw))

S = lambda a, t, o: (sph(a, t), o)
# ---------------- 2a back bob: inner fill layer
LAYER_D = -0.0045
for i in range(17):
    a = -68 + 136 * i / 16
    wp = [S(a * 0.3, 18, 0.002), S(a * 0.8, 55, 0.008), S(a, 92, 0.011)]
    p = scalp_path(wp)
    WAVE_PH = random.uniform(0, 1.0)
    add_lock(f"BackInner_{i:02d}", p + hang(p[-1], 0.300 + random.uniform(0, 0.006), 0.010, 0.006, 0.004), 0.050, 0.010, "back_in", tipw=0.3)
# ---------------- 2b back bob: outer locks
LAYER_D = 0.0
for i in range(23):
    a = -74 + 148 * i / 22 + random.uniform(-1.5, 1.5)
    wp = [S(a * 0.35, 14, 0.004), S(a * 0.8, 52, 0.014), S(a, 92, 0.017)]
    p = scalp_path(wp)
    zend = 0.294 + random.uniform(-0.007, 0.007) + 0.004 * (abs(a) / 74); WAVE_PH = random.uniform(0, 1.2)
    add_lock(f"BackOuter_{i:02d}", p + hang(p[-1], zend, 0.004, random.uniform(0.003, 0.009), random.uniform(0.002, 0.006)), 0.044 + random.uniform(-0.004, 0.004), 0.0078, "back_out", tipw=0.34)
# ---------------- 2c top layer: shorter crown layer over the bob (visible layering like the reference)
LAYER_D = 0.0018
for i in range(15):
    a = -66 + 132 * i / 14 + random.uniform(-2, 2)
    wp = [S(a * 0.3, 12, 0.004), S(a * 0.8, 50, 0.014), S(a, 92, 0.017)]
    p = scalp_path(wp); WAVE_PH = random.uniform(0, 1.0)
    add_lock(f"TopLayer_{i:02d}", p + hang(p[-1], 0.318 + random.uniform(-0.006, 0.006), 0.004, 0.004, 0.004), 0.044 + random.uniform(-0.004, 0.004), 0.007, "layer", tipw=0.28)
LAYER_D = 0.0
LAYER_D = 0.0012
# ---------------- 3 side sections: from the part, over the top of the ear, tucked behind it
def side_lock(name, sgn, phi, a_mid, t_mid, a_land, t_land, zend, w=0.034, off=0.016):
    wp = [(part_dir(phi), 0.003), S(sgn * a_mid, t_mid, off * 0.85), S(sgn * a_land, t_land, off),
          S(sgn * 82, 90, off), S(sgn * 58, 93, off)]
    p = scalp_path(wp)
    add_lock(name, p + hang(p[-1], zend + random.uniform(-0.005, 0.005), 0.003, random.uniform(0.0, 0.006), 0.004), w, 0.008, "side", tipw=0.32)
# her left (long side of the part)
L = [(-26, 70, 40, 80, 82), (-14, 86, 46, 88, 84), (-2, 98, 50, 96, 84), (10, 108, 54, 104, 83), (22, 118, 57, 110, 82)]
for j, (phi, am, tm, al, tl) in enumerate(L):
    side_lock(f"SideL_{j}", 1, phi, am, tm, al, tl, 0.298 + 0.002 * j, w=0.040)
# her right (short side)
R = [(-26, 68, 40, 80, 83), (-14, 80, 44, 88, 85), (-2, 90, 47, 94, 85), (10, 100, 50, 100, 84), (22, 108, 53, 104, 83)]
for j, (phi, am, tm, al, tl) in enumerate(R):
    side_lock(f"SideR_{j}", -1, phi, am, tm, al, tl, 0.298 + 0.002 * j, w=0.040)
LAYER_D = 0.0008
# ---------------- 4 side-swept fringe: from the front of the part across the upper forehead
# locks from the front of the part that fall down each side of the forehead (reference: forehead framed in an arch)
FL = [(34, 158, 64, 132, 78, 0.040), (44, 166, 67, 138, 80, 0.036), (54, 174, 68, 144, 81, 0.032)]    # her left (long side)
FRt = [(30, -158, 62, -130, 78, 0.040), (40, -170, 66, -142, 80, 0.034), (52, -176, 68, -148, 81, 0.030)]                              # her right
for j, (phi, a1, t1, a2, t2, w) in enumerate(FL + FRt):
    sgn = 1 if j < len(FL) else -1
    wp = [(part_dir(phi), 0.003), S(a1, t1, 0.008), S(a2, t2, 0.010), S(sgn * 118, 86, 0.013), S(sgn * 86, 92, 0.016), S(sgn * 58, 93, 0.016)]
    p = scalp_path(wp); WAVE_PH = random.uniform(0, 1.0)
    add_lock(f"Fringe_{j}", p + hang(p[-1], 0.300 + 0.004 * j, 0.003, 0.004, 0.004), w * 1.1, 0.0055, "fringe", tipw=0.3)
LAYER_D = -0.004
# ---------------- 5 face-framing temple locks in front of the ears (short, inward curl)
for sgn, phi, w in ():   # face-frame locks removed (read as hooks); side mass frames the face
    wp = [(part_dir(phi), 0.004), S(sgn * 132, 60, 0.012), S(sgn * 118, 84, 0.012), S(sgn * 112, 95, 0.012)]
    p = scalp_path(wp)
    add_lock(f"Frame_{'R' if sgn < 0 else 'L'}", p + hang(p[-1], 0.412, 0.0, 0.004, 0.003), w, 0.009, "frame", tipw=0.4)

# ---------------- clearance: keep every centreline >= t/2 + 2.5 mm outside the skin (incl. ears)
def clear(pts, t):
    out = []
    for p in pts:
        q = p.copy()
        for _ in range(3):
            loc, nrm, _i, dist = bvh_all.find_nearest(q)
            if loc is None: break
            side = (q - loc).dot(nrm)
            need = t * 0.5 + 0.0025
            if side < need: q = loc + nrm * need
        out.append(q)
    return out

# ---------------- build meshes
def build(name, pts, w, t, tipw, mat):
    n = 34
    c = catmull(pts, n)
    c = clear(c, t)
    c = catmull(c[::2] + [c[-1]], n)   # re-smooth after clearance
    bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap")
    rings = []; seg = 10
    for i, p in enumerate(c):
        T = (c[min(i + 1, n - 1)] - c[max(i - 1, 0)]).normalized()
        base = Vector((Cc.x, Cc.y, min(p.z, Cc.z)))
        nr = (p - base).normalized()
        Np = (nr - T * nr.dot(T)).normalized(); B = T.cross(Np).normalized()
        u = i / (n - 1)
        wf = (0.6 + 0.4 * min(u / 0.12, 1)) * (1 - (1 - tipw) * max(0, (u - 0.75) / 0.25) ** 1.5)
        tf = (0.55 + 0.45 * min(u / 0.12, 1)) * (1 - 0.55 * max(0, (u - 0.8) / 0.2))
        ring = []
        for s in range(seg):
            ang = 2 * math.pi * s / seg
            cx, sy = math.cos(ang), math.sin(ang)
            lens = abs(cx) ** 0.15 * (1 if cx >= 0 else -1)
            off = B * (w * 0.5 * wf * cx) + Np * (t * 0.5 * tf * sy * (1.0 if sy > 0 else 0.55))
            ring.append(bm.verts.new((p + off) * k))
        rings.append(ring)
    faces = []
    for i in range(n - 1):
        for s in range(seg):
            f = bm.faces.new((rings[i][s], rings[i][(s + 1) % seg], rings[i + 1][(s + 1) % seg], rings[i + 1][s]))
            for lp, (uu, vv) in zip(f.loops, ((s / seg, i / (n - 1)), ((s + 1) / seg, i / (n - 1)), ((s + 1) / seg, (i + 1) / (n - 1)), (s / seg, (i + 1) / (n - 1)))):
                lp[uv].uv = (uu, vv)
    # caps
    for ring, rev in ((rings[0], True), (rings[-1], False)):
        ctr = bm.verts.new(sum((v.co for v in ring), Vector()) / len(ring))
        for s in range(seg):
            a, b = ring[s], ring[(s + 1) % seg]
            bm.faces.new((b, a, ctr) if rev else (a, b, ctr))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    return bm

coll = bpy.data.collections["AIS_Hair"]
for o in list(coll.objects): bpy.data.objects.remove(o)
mat = bpy.data.materials.get("M_Ais_Hair") or bpy.data.materials.new("M_Ais_Hair")
groups = {}
for name, pts, w, t, layer, tipw in locks:
    groups.setdefault(layer, []).append((name, pts, w, t, tipw))
objs = []
LAYER_NAME = {"back_in": "Ais_Hair_BackInner", "back_out": "Ais_Hair_BackOuter", "side": "Ais_Hair_Sides",
              "fringe": "Ais_Hair_Fringe", "layer": "Ais_Hair_TopLayer", "frame": "Ais_Hair_FaceFrame"}
for layer, items in groups.items():
    bm_all = bmesh.new()
    me_l = bpy.data.meshes.new(LAYER_NAME[layer])
    tmp = []
    for name, pts, w, t, tipw in items:
        bm = build(name, pts, w, t, tipw, mat)
        m = bpy.data.meshes.new("tmp"); bm.to_mesh(m); bm.free(); tmp.append(m)
    # merge via join
    ob = bpy.data.objects.new(LAYER_NAME[layer], tmp[0]); coll.objects.link(ob)
    others = []
    for m in tmp[1:]:
        o = bpy.data.objects.new("tmp", m); coll.objects.link(o); others.append(o)
    with bpy.context.temp_override(active_object=ob, selected_editable_objects=[ob] + others, object=ob):
        bpy.ops.object.join()
    ob.data.name = LAYER_NAME[layer]
    objs.append(ob)

# ---------------- 1 base cap: body faces of the hair region, offset 4.5 mm
bm = bmesh.new(); bm.from_mesh(body.data); bm.transform(body.matrix_world); bm.normal_update()
def in_hair(co):
    p = Vector(co) / k - Cc
    if p.length < 1e-6: return False
    d = p.normalized()
    th = math.degrees(math.acos(max(-1, min(1, d.z)))); a = math.degrees(math.atan2(d.x, d.y))
    aa = abs(a)
    lim = 104 if aa <= 70 else (104 - (aa - 70) * 0.5 if aa <= 125 else 76.5 - (aa - 125) * 0.25)
    return th < lim
earset = set(np.where(ear)[0])
drop = [f for f in bm.faces if not all(in_hair(v.co) and v.index not in earset for v in f.verts)]
bmesh.ops.delete(bm, geom=drop, context="FACES")
for v in bm.verts: v.co += v.normal * 0.0045 * k
cap_me = bpy.data.meshes.new("Ais_Hair_Base"); bm.to_mesh(cap_me); bm.free()
cap = bpy.data.objects.new("Ais_Hair_Base", cap_me); coll.objects.link(cap); objs.insert(0, cap)
print("cap faces", len(cap_me.polygons))

# ---------------- finishing: material, smooth, subdivision, rig binding (rigid to the head)
for ob in objs:
    ob.data.materials.clear(); ob.data.materials.append(mat)
    for p in ob.data.polygons: p.use_smooth = True
    vg = ob.vertex_groups.new(name="DEF-spine.006"); vg.add(range(len(ob.data.vertices)), 1.0, 'REPLACE')
    ob.parent = rig; ob.matrix_parent_inverse = rig.matrix_world.inverted()
    am = ob.modifiers.new("Armature", 'ARMATURE'); am.object = rig
    sd = ob.modifiers.new("Subdivision", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    print(ob.name, "verts", len(ob.data.vertices))
rig.data.pose_position = 'POSE'
# provisional hair shader (final look-dev in batch 06)
mat.use_nodes = True
import ba_hair_shader; ba_hair_shader.build(mat)
bs = None

bpy.ops.wm.save_as_mainfile(filepath=root + "/BabyAis_Working.blend", compress=True)
bpy.ops.wm.save_as_mainfile(filepath=root + "/checkpoints/BabyAis_v004_hair.blend", compress=True, copy=True)
print("HAIR BUILT", len(locks), "locks")
