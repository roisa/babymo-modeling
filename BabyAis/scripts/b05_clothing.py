"""BATCH 05 - Baby Ais outfit, all editable geometry fitted to the body and skinned to the rig:
lavender long-sleeve shirt (collar visible), light-blue cuffs, pink sleeveless romper with legs,
purple shoes with light-blue soles, two purple rounded pockets, raised white crescent-moon emblem.
Body faces fully covered are masked (no poke-through); a 1-ring margin is kept at every opening."""
import bpy, bmesh, sys, math, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, sys.argv[-1]); import ba_common as C
root = sys.argv[1]
bpy.ops.wm.open_mainfile(filepath=root + "/checkpoints/BabyAis_v004_hair.blend")
k = C.k_scale()
rig = bpy.data.objects["Ais_Rig"]; rig.data.pose_position = 'REST'
body = bpy.data.objects["Ais_Body"]
coll = bpy.data.collections["AIS_Clothing"]
for o in list(coll.objects): bpy.data.objects.remove(o)
for m in list(body.modifiers):
    if m.type == 'MASK': body.modifiers.remove(m)
bpy.context.view_layer.update()
me = body.data
P = C.world_coords(body) / k            # Mo space
NV = len(P)
vgi = {g.index: g.name for g in body.vertex_groups}
W = {}  # bone-family weight sums
def fam(n):
    for key in ("upper_arm", "forearm", "hand", "f_", "thumb", "palm", "shoulder", "thigh", "shin", "foot", "toe", "spine", "pelvis"):
        if key in n: return key
    return "other"
F = {f: np.zeros(NV) for f in ("upper_arm", "forearm", "hand", "f_", "thumb", "palm", "shoulder", "thigh", "shin", "foot", "toe", "spine", "pelvis", "other")}
for v in me.vertices:
    for g in v.groups:
        n = vgi[g.group]
        if n.startswith("DEF-"): F[fam(n)][v.index] += g.weight
handw = F["hand"] + F["f_"] + F["thumb"] + F["palm"]
armw = F["upper_arm"] + F["forearm"]
legw = F["thigh"] + F["shin"]
footw = F["foot"] + F["toe"]
z, x, y = P[:, 2], P[:, 0], P[:, 1]
ax = np.abs(x)
print("hand verts", int((handw > 0.5).sum()), "arm", int((armw > 0.5).sum()), "foot", int((footw > 0.5).sum()))
# wrist position along each arm: lowest arm-dominant verts next to the hand
wrist_z = {}
for s in (-1, 1):
    m = (handw > 0.35) & (x * s > 0)
    wrist_z[s] = P[m, 2].max()
print("wrist top z", wrist_z)
bone = lambda n: (rig.matrix_world @ rig.data.bones[n].head_local, rig.matrix_world @ rig.data.bones[n].tail_local)
WR = {}
for s_, sfx in ((1, "L"), (-1, "R")):
    h, t = bone(f"DEF-forearm.{sfx}.001"); WR[s_] = (t.copy(), (t - h).normalized())     # wrist point + forearm axis
    ua_h, ua_t = bone(f"DEF-upper_arm.{sfx}"); WR[s_] += (ua_h.copy(), (ua_t - ua_h).normalized())
print("wrist", {s_: tuple(round(c, 3) for c in WR[s_][0]) for s_ in WR})
hand_dom = handw > 0.5
shirt = (z < 0.345) & (z > 0.16) & (legw < 0.5) & ~hand_dom
romper = (z < 0.33) & ~hand_dom & (z > 0.03) & (armw < 0.75)
for s_ in (1, -1):   # romper never needs the lower arm
    romper &= ~((x * s_ > 0) & (F["forearm"] > 0.3))
def V(*a): return Vector(a)
_bb = bmesh.new(); _bb.from_mesh(me); _bb.transform(body.matrix_world)
BODY_BVH = BVHTree.FromBMesh(_bb); _bb.free()

def shell(name, mask, offset, mat, cuts=(), min_faces=40):
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(body.matrix_world); bm.normal_update()
    for dl in list(bm.verts.layers.deform.values()): bm.verts.layers.deform.remove(dl)
    src = bm.verts.layers.int.new("src_vert")
    for v in bm.verts: v[src] = v.index + 1
    drop = [f for f in bm.faces if not all(mask[v.index] for v in f.verts)]
    bmesh.ops.delete(bm, geom=drop, context="FACES")
    for v in bm.verts:
        v.co += v.normal * offset * k
        loc, nrm, _i, dist = BODY_BVH.find_nearest(v.co)       # guard against stray normals
        if loc is not None and (dist > offset * k * 1.8 or (v.co - loc).dot(nrm) < 0):
            v.co = loc + nrm * offset * k
    for co, no in cuts:   # remove the side the normal points to
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no, clear_outer=True)
    bmesh.ops.dissolve_degenerate(bm, dist=0.0006 * k, edges=bm.edges[:])
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0004 * k)
    # drop tiny islands / loose bits
    bm.faces.ensure_lookup_table(); seen = set(); kill = []
    for f in bm.faces:
        if f in seen: continue
        isl = []; stack = [f]; seen.add(f)
        while stack:
            g = stack.pop(); isl.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h not in seen: seen.add(h); stack.append(h)
        if len(isl) < min_faces: kill += isl
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    m = bpy.data.meshes.new(name); bm.to_mesh(m); bm.free()
    ob = bpy.data.objects.new(name, m); coll.objects.link(ob)
    for p in m.polygons: p.use_smooth = True
    m.materials.append(mat)
    return ob

from mathutils.kdtree import KDTree
DEFW = [{body.vertex_groups[g.group].name: g.weight for g in v.groups if body.vertex_groups[g.group].name.startswith("DEF-") and g.weight > 0.001} for v in me.vertices]
def copy_weights(ob, src_of):
    """src_of: list (per garment vert) of body vertex index -> exact weight copy (limit 4, normalised)."""
    for i, bi in enumerate(src_of):
        w = sorted(DEFW[bi].items(), key=lambda t: -t[1])[:4]; tot = sum(x for _, x in w) or 1
        for n, x in w:
            vg = ob.vertex_groups.get(n) or ob.vertex_groups.new(name=n); vg.add([i], x / tot, 'REPLACE')
def weights_by_region(ob, allowed):
    """Nearest body vertex inside an allowed region (e.g. same-side arm) for every garment vertex."""
    idx = np.where(allowed)[0]; kd = KDTree(len(idx))
    Pw = P * k
    for j, bi in enumerate(idx): kd.insert(Pw[bi], j)
    kd.balance()
    copy_weights(ob, [int(idx[kd.find(ob.matrix_world @ v.co)[1]]) for v in ob.data.vertices])
def weights_from_source(ob):
    """Shells: exact copy from the body vertex each garment vertex was offset from; cut verts -> nearest tagged."""
    at = ob.data.attributes.get("src_vert")
    vals = np.zeros(len(ob.data.vertices), int); at.data.foreach_get("value", vals)
    Pw = P * k
    for i, v in enumerate(ob.data.vertices):      # cut verts carry interpolated (wrong) indices -> invalidate
        if vals[i] > 0 and (Vector(Pw[vals[i] - 1]) - ob.matrix_world @ v.co).length > 0.02 * k: vals[i] = 0
    print(ob.name, "re-mapped cut verts", int((vals == 0).sum()))
    tagged = np.where(vals > 0)[0]; kd = KDTree(len(tagged))
    for j, i in enumerate(tagged): kd.insert(ob.data.vertices[int(i)].co, j)
    kd.balance()
    src = [int(vals[i]) - 1 if vals[i] > 0 else int(vals[tagged[kd.find(v.co)[1]]]) - 1 for i, v in enumerate(ob.data.vertices)]
    copy_weights(ob, src)
REGION = {}
def finish(ob, thick, subd=1, cs=True):
    """Skin weights from the body (same bones -> layers move together), rig parent, fabric thickness."""
    if ob.get("weights_done") or "src_vert" in ob.data.attributes:
        if not ob.get("weights_done"): weights_from_source(ob)
        _parent_and_mods(ob, thick, subd, cs); return
    for vg in body.vertex_groups:
        if vg.name.startswith("DEF-") and vg.name not in ob.vertex_groups: ob.vertex_groups.new(name=vg.name)
    dt = ob.modifiers.new("Weights", "DATA_TRANSFER"); dt.object = body; dt.use_object_transform = True
    dt.use_vert_data = True; dt.data_types_verts = {"VGROUP_WEIGHTS"}; dt.vert_mapping = "POLYINTERP_NEAREST"
    dt.layers_vgroup_select_src = "ALL"; dt.layers_vgroup_select_dst = "NAME"
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.modifier_apply(modifier=dt.name)
        for vg in list(ob.vertex_groups):
            if not vg.name.startswith("DEF-"): ob.vertex_groups.remove(vg)
        bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
        bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
        bpy.ops.object.vertex_group_clean(group_select_mode="ALL", limit=0.001)
    _parent_and_mods(ob, thick, subd, cs)
def _parent_and_mods(ob, thick, subd, cs):
    ob.parent = rig; ob.matrix_parent_inverse = rig.matrix_world.inverted()
    am = ob.modifiers.new("Armature", 'ARMATURE'); am.object = rig
    if cs:
        c = ob.modifiers.new("CorrectiveSmooth", 'CORRECTIVE_SMOOTH'); c.smooth_type = 'LENGTH_WEIGHTED'; c.iterations = 4
    if thick:
        so = ob.modifiers.new("Solidify", 'SOLIDIFY'); so.thickness = thick * k; so.offset = 1.0; so.use_even_offset = False; so.use_quality_normals = True; so.use_rim = True
    if subd:
        sd = ob.modifiers.new("Subdivision", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2

def mat(name, rgb, rough=0.75, sheen=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*rgb, 1); bs.inputs["Roughness"].default_value = rough
    bs.inputs["Sheen Weight"].default_value = sheen; bs.inputs["Sheen Roughness"].default_value = 0.5
    return m
M_pink = mat("M_Ais_Fabric_Pink", (1.0, 0.07, 0.30))
M_lav = mat("M_Ais_Fabric_Lavender", (0.42, 0.24, 0.95))
M_blue = mat("M_Ais_Fabric_LightBlue", (0.30, 0.66, 1.0))
M_purp = mat("M_Ais_Pocket_Purple", (0.40, 0.22, 0.95))
M_shoe = mat("M_Ais_Shoe_Purple", (0.36, 0.18, 0.9), rough=0.45, sheen=0.2)
M_sole = mat("M_Ais_Shoe_Sole_Blue", (0.33, 0.68, 1.0), rough=0.5, sheen=0.1)
M_moon = mat("M_Ais_Moon_White", (0.92, 0.92, 0.92), rough=0.6, sheen=0.3)
K = lambda *a: Vector(a) * k
cuts_shirt = [(K(0, -0.06, 0.312), V(0, -0.15, 1))]
cuts_romper = [(K(0, -0.06, 0.304), V(0, -0.15, 1)), (K(0, 0, 0.043), V(0, 0, -1))]
cuts_cuff = []
for s_ in (1, -1):
    wp, wd, sp, sd = WR[s_]
    cuts_shirt.append((wp + wd * 0.001 * k, wd))
    cuts_romper.append((sp - V(s_, 0, 0) * 0.006 * k, V(s_, 0, 0.28).normalized()))
shirt_ob = shell("Ais_Shirt", shirt, 0.0046, M_lav, cuts_shirt)
# hidden shirt torso under the romper is removed (no layer poke-through in motion); keep sleeves + collar
bm = bmesh.new(); bm.from_mesh(shirt_ob.data)
def under_romper(co):
    p = co / k
    if -0.15 * (p.y + 0.06) + (p.z - 0.304) > -0.012: return False      # collar band stays
    for s_ in (1, -1):
        sp = WR[s_][2] / k; n = V(s_, 0, 0.28).normalized()
        if (p - (sp - V(s_, 0, 0) * 0.006)).dot(n) > -0.013: return False   # sleeve + 13 mm tuck under armhole
    return p.z > 0.075
kill = [f for f in bm.faces if all(under_romper(v.co) for v in f.verts)]
bmesh.ops.delete(bm, geom=kill, context="FACES"); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bm.to_mesh(shirt_ob.data); bm.free()
print("shirt torso faces removed", len(kill))
def planar_uv(ob, axes=(0, 2)):
    me_ = ob.data
    if not me_.uv_layers: me_.uv_layers.new(name="UVMap")
    uvl = me_.uv_layers.active.data
    co = np.array([v.co[:] for v in me_.vertices]); lo, hi = co.min(0), co.max(0); span = max((hi - lo)[list(axes)].max(), 1e-6)
    for poly in me_.polygons:
        for li in poly.loop_indices:
            c = co[me_.loops[li].vertex_index]; uvl[li].uv = ((c[axes[0]] - lo[axes[0]]) / span, (c[axes[1]] - lo[axes[1]]) / span)
def fix_normals(ob):
    bm_ = bmesh.new(); bm_.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm_, faces=bm_.faces); bm_.to_mesh(ob.data); bm_.free()
romper_ob = shell("Ais_Romper", romper, 0.0092, M_pink, cuts_romper)
def romper_shape(ob):
    """Toddler romper silhouette: no body detail (seat crease, knees), straight rounded pant legs."""
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    bnd = {v for e in bm.edges if e.is_boundary for v in e.verts}
    low = [v for v in bm.verts if v.co.z / k < 0.215 and v not in bnd]
    for _ in range(14):
        bmesh.ops.smooth_vert(bm, verts=low, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=False)
    # legs: radius around each leg axis at least Rmin (wide straight trousers)
    for s_, n in ((1, "L"), (-1, "R")):
        hp = rig.matrix_world @ rig.data.bones[f"DEF-thigh.{n}"].head_local
        ap = rig.matrix_world @ rig.data.bones[f"DEF-shin.{n}.001"].tail_local
        ax = (ap - hp).normalized()
        for v in bm.verts:
            if v.co.x * s_ <= 0 or v.co.z / k > 0.15: continue
            t = (v.co - hp).dot(ax); c = hp + ax * t; r = v.co - c; r.z = 0
            if r.length < 1e-6: continue
            # top of the leg blends into the body; full straight leg below z .13
            blend = min(max((0.15 - v.co.z / k) / 0.03, 0), 1)
            Rmin = (0.042 - 0.003 * min(max((0.13 - v.co.z / k) / 0.08, 0), 1)) * k
            inner = r.normalized().x * s_ < -0.3          # inner side: limited so legs never touch
            if inner: Rmin = min(Rmin, 0.043 * k)
            if r.length < Rmin:
                v.co += r.normalized() * (Rmin - r.length) * blend
            zz = v.co.z / k
            if zz < 0.09:   # hem flares over the shoe + soft fabric bunching above it
                bunch = 0.0035 * min(max((0.07 - zz) / 0.025, 0), 1) + 0.0007 * math.sin(zz / 0.0105 * 2 * math.pi + s_) * min(max((0.09 - zz) / 0.03, 0), 1)
                v.co += r.normalized() * bunch * k
    # hem ring: level height + smooth radius along the ring (clean hem edge)
    hem = [v for v in bnd if v.co.z / k < 0.06]
    for v in hem: v.co.z = 0.043 * k
    for _ in range(6):
        newp = {}
        for v in hem:
            ns = [e.other_vert(v) for e in v.link_edges if e.other_vert(v) in bnd]
            if len(ns) == 2: newp[v] = (v.co + ns[0].co + ns[1].co) / 3
        for v, c in newp.items(): v.co = Vector((c.x, c.y, 0.043 * k))
    # guard: >= 6 mm outside the skin everywhere
    for v in bm.verts:
        loc, nrm, _i, dist = BODY_BVH.find_nearest(v.co)
        if loc is not None and (v.co - loc).dot(nrm) < 0.006 * k: v.co = loc + nrm * 0.006 * k
    bm.to_mesh(ob.data); bm.free()
romper_shape(romper_ob)
cuff_parts = []
def cuff_band(name, wp, wd, length=0.018, off=0.0072, segs=24, rows=7):
    """Neat cuff band around the wrist axis: radius = measured sleeve radius + ease, per angle."""
    up = Vector((0, 0, 1)); a1 = wd.cross(up).normalized(); a2 = wd.cross(a1).normalized()
    bm = bmesh.new(); grid = []
    radii = []
    for r in range(rows + 1):
        t = -length + (length + 0.002) * r / rows
        c = wp + wd * t * k
        row_r = []
        for j in range(segs):
            ang = 2 * math.pi * j / segs; d = a1 * math.cos(ang) + a2 * math.sin(ang)
            hit = BODY_BVH.ray_cast(c + d * 0.06 * k, -d, 0.06 * k)
            row_r.append(((hit[0] - c).length if hit[0] else 0.02 * k))
        radii.append(row_r)
    R = np.array(radii); Rm = np.maximum.accumulate(R[::-1], axis=0)[::-1] * 0 + R.max(axis=0)[None, :]   # straight band
    Rm = 0.5 * Rm + 0.5 * np.convolve(np.r_[Rm[0, -2:], Rm[0], Rm[0, :2]], np.ones(5) / 5, 'valid')[None, :]
    for r in range(rows + 1):
        t = -length + (length + 0.002) * r / rows
        c = wp + wd * t * k
        row = []
        for j in range(segs):
            ang = 2 * math.pi * j / segs; d = a1 * math.cos(ang) + a2 * math.sin(ang)
            bulge = 0.0008 * k * math.sin(math.pi * r / rows)
            row.append(bm.verts.new(c + d * (Rm[0, j] + off * k + bulge)))
        grid.append(row)
    for r in range(rows):
        for j in range(segs):
            bm.faces.new((grid[r][j], grid[r][(j + 1) % segs], grid[r + 1][(j + 1) % segs], grid[r + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    m = bpy.data.meshes.new(name); bm.to_mesh(m); bm.free()
    ob = bpy.data.objects.new(name, m); coll.objects.link(ob); m.materials.append(M_blue)
    for p in m.polygons: p.use_smooth = True
    return ob
for s_ in (1, -1):
    wp, wd, sp, sd = WR[s_]
    cuff_parts.append(cuff_band(f"Ais_Cuff_{'L' if s_ > 0 else 'R'}", wp, wd))
def collar_band():
    """Ribbed lavender collar at the neckline (reference: a soft rounded rib shows all round)."""
    wd = Vector((0, -0.15, 1)).normalized(); wp = K(0, -0.004, 0.3075)
    up_ = Vector((0, 1, 0)); a1 = wd.cross(up_).normalized(); a2 = wd.cross(a1).normalized()
    segs, rows, length = 64, 6, 0.0085
    radii = []
    for j in range(segs):
        ang = 2 * math.pi * j / segs; d = a1 * math.cos(ang) + a2 * math.sin(ang); best = 0.0
        for r in range(rows + 1):
            c = wp + wd * (-length * 0.6 + length * r / rows) * k
            hit = BODY_BVH.ray_cast(c + d * 0.09 * k, -d, 0.09 * k)
            if hit[0]: best = max(best, (hit[0] - c).length)
        radii.append(best or 0.04 * k)
    radii = np.convolve(np.r_[radii[-3:], radii, radii[:3]], np.ones(7) / 7, 'valid')
    bm = bmesh.new(); grid = []
    for r in range(rows + 1):
        c = wp + wd * (-length * 0.6 + length * r / rows) * k
        roll = 0.0016 * k * math.sin(math.pi * r / rows)
        row = []
        for j in range(segs):
            ang = 2 * math.pi * j / segs; d = a1 * math.cos(ang) + a2 * math.sin(ang)
            rib = 0.00035 * k * math.cos(ang * 32)
            row.append(bm.verts.new(c + d * (radii[j] + 0.0068 * k + roll + rib)))
        grid.append(row)
    for r in range(rows):
        for j in range(segs):
            bm.faces.new((grid[r][j], grid[r][(j + 1) % segs], grid[r + 1][(j + 1) % segs], grid[r + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    m = bpy.data.meshes.new("Ais_Collar"); bm.to_mesh(m); bm.free()
    ob = bpy.data.objects.new("Ais_Collar", m); coll.objects.link(ob); m.materials.append(M_lav)
    for pl in m.polygons: pl.use_smooth = True
    return ob
collar_ob = collar_band()
cuff_ob = cuff_parts[0]
with bpy.context.temp_override(active_object=cuff_ob, selected_editable_objects=cuff_parts, object=cuff_ob):
    bpy.ops.object.join()
cuff_ob.name = cuff_ob.data.name = "Ais_Cuffs"

# ---- shoes: rounded toddler shoes fitted to each foot (superellipsoid upper + rounded sole slab)
def superellipsoid(name, c, a, b, h, e=2.6, flat=0.0, top_cut=None, rings=14, segs=28):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
    grid = []
    for i in range(rings + 1):
        th = math.pi * i / rings            # 0 top .. pi bottom
        row = []
        for j in range(segs):
            ph = 2 * math.pi * j / segs
            ct, st = math.cos(th), math.sin(th)
            sx = np.sign(math.cos(ph)) * abs(math.cos(ph)) ** (2 / e) * abs(st) ** (2 / e)
            sy = np.sign(math.sin(ph)) * abs(math.sin(ph)) ** (2 / e) * abs(st) ** (2 / e)
            sz = np.sign(ct) * abs(ct) ** (2 / e)
            # toe end (front, -y) a bit higher/rounder than the heel
            frontness = max(0.0, -sy)
            zz = c.z + sz * h * (1 + 0.12 * frontness)
            zz = max(zz, c.z - h + flat) if flat else zz
            row.append(bm.verts.new((c.x + sx * a, c.y + sy * b, zz)))
        grid.append(row)
    for i in range(rings):
        for j in range(segs):
            q = (grid[i][j], grid[i][(j + 1) % segs], grid[i + 1][(j + 1) % segs], grid[i + 1][j])
            if len(set(q)) == 4:
                try: bm.faces.new(q)
                except ValueError: pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    m = bpy.data.meshes.new(name); bm.to_mesh(m); bm.free()
    ob = bpy.data.objects.new(name, m); coll.objects.link(ob)
    for p in m.polygons: p.use_smooth = True
    return ob
def sneaker(tag, cx, cy, L, W):
    """Toddler sneaker: foot-shaped plan (wider toe), domed upper lower at the toe and higher at the
    heel/ankle collar, plus a rounded light-blue sole rim wrapping the bottom. Mo-space inputs."""
    segs, rows = 40, 12
    def outline(ph, grow=0.0):
        sp, cp = math.sin(ph), math.cos(ph)
        e = 2.6
        x = np.sign(sp) * abs(sp) ** (2 / e); y = -np.sign(cp) * abs(cp) ** (2 / e)
        front = max(0.0, -y)
        Wf = W * (0.88 + 0.16 * front) + grow
        return Vector((cx + x * Wf, cy - 0.003 + y * (L + grow), 0))
    Z0, SOLE_H = 0.0062, 0.0078
    # upper
    bm = bmesh.new(); grid = []
    top = Vector((cx, cy - 0.003 + 0.28 * L, 0))
    for r in range(rows + 1):
        t = r / rows
        rho = math.cos(t * math.pi / 2) ** 0.55
        row = []
        for j in range(segs):
            ph = 2 * math.pi * j / segs
            o = outline(ph)
            heel = max(0.0, (o.y - (cy - 0.003)) / L)          # 0 toe .. 1 heel
            H = 0.0255 + 0.0175 * heel ** 1.3
            q = top + (o - top) * rho
            row.append(bm.verts.new(Vector((q.x, q.y, Z0 + H * math.sin(t * math.pi / 2) ** 0.85)) * k))
        grid.append(row)
    for r in range(rows):
        for j in range(segs):
            q = (grid[r][j], grid[r][(j + 1) % segs], grid[r + 1][(j + 1) % segs], grid[r + 1][j])
            if len(set(q)) == 4: bm.faces.new(q)
    bot = bm.verts.new(Vector((cx, cy - 0.003, Z0)) * k)
    for j in range(segs): bm.faces.new((grid[0][(j + 1) % segs], grid[0][j], bot))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mu = bpy.data.meshes.new("Ais_Shoe_" + tag); bm.to_mesh(mu); bm.free()
    up = bpy.data.objects.new("Ais_Shoe_" + tag, mu); coll.objects.link(up)
    # sole rim: rounded band profile (inner bottom -> outer bulge -> inner top)
    prof = [(-0.004, 0.0), (0.0, 0.0006), (0.0022, 0.0030), (0.0016, SOLE_H - 0.0012), (-0.0004, SOLE_H), (-0.006, SOLE_H)]
    bm = bmesh.new(); grid = []
    for gr, z in prof:
        grid.append([bm.verts.new(Vector((outline(2 * math.pi * j / segs, gr).x, outline(2 * math.pi * j / segs, gr).y, z)) * k) for j in range(segs)])
    for r in range(len(prof) - 1):
        for j in range(segs):
            bm.faces.new((grid[r][j], grid[r][(j + 1) % segs], grid[r + 1][(j + 1) % segs], grid[r + 1][j]))
    for ring, z in ((grid[0], 0.0), (grid[-1], SOLE_H)):
        c = bm.verts.new(Vector((cx, cy - 0.003, z)) * k)
        for j in range(segs): bm.faces.new((ring[j], ring[(j + 1) % segs], c))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ms = bpy.data.meshes.new("Ais_Sole_" + tag); bm.to_mesh(ms); bm.free()
    so = bpy.data.objects.new("Ais_Sole_" + tag, ms); coll.objects.link(so)
    for ob in (up, so):
        for pl in ob.data.polygons: pl.use_smooth = True
    return up, so
shoe_parts, sole_parts = [], []
for s_ in (1, -1):
    fm = (footw > 0.4) & (x * s_ > 0) & (z < 0.08)
    Q = P[fm]
    lo, hi = Q.min(0), Q.max(0)
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    L2, W2 = (hi[1] - lo[1]) / 2 + 0.0045, (hi[0] - lo[0]) / 2 + 0.004
    print("foot", s_, "len", round(hi[1] - lo[1], 3), "w", round(hi[0] - lo[0], 3), "top", round(hi[2], 3))
    sh, so = sneaker('L' if s_ > 0 else 'R', cx, cy, (hi[1] - lo[1]) / 2 + 0.0065, (hi[0] - lo[0]) / 2 + 0.0035)
    shoe_parts.append(sh); sole_parts.append(so)
def joined(parts, name, mat):
    ob = parts[0]
    with bpy.context.temp_override(active_object=ob, selected_editable_objects=parts, object=ob):
        bpy.ops.object.join()
    ob.name = ob.data.name = name; ob.data.materials.clear(); ob.data.materials.append(mat); return ob
shoe_ob = joined(shoe_parts, "Ais_Shoes", M_shoe)
sole_ob = joined(sole_parts, "Ais_ShoeSoles", M_sole)
shoe = (z < 0.052) & (footw + F["shin"] > 0.2)

# ---- patches (pockets, moon) projected onto the romper front
rbm = bmesh.new(); rbm.from_mesh(romper_ob.data); rbm.normal_update()
rbvh = BVHTree.FromBMesh(rbm)
def poly_nearest(poly, q):
    best, bp = 1e9, None
    for i in range(len(poly)):
        a_, b_ = np.array(poly[i]), np.array(poly[(i + 1) % len(poly)]); d = b_ - a_
        t = np.clip(np.dot(q - a_, d) / max(np.dot(d, d), 1e-12), 0, 1); c = a_ + d * t
        dd = np.sum((q - c) ** 2)
        if dd < best: best, bp = dd, c
    return bp
def patch(name, outline2d, center, matx, lift=0.0030, thick=0.0018, grid=40, poly=None):
    """Smooth-edged appliqué: fine 2D grid inside the outline, boundary snapped onto the exact outline
    polyline, interior relaxed, then projected onto the romper front.  center=(x,z,sx,sz) Mo space."""
    cx, cz, sx, sz = center
    uv = {}; faces2d = []
    for i in range(grid):
        for j in range(grid):
            uc, vc = -1 + 2 * (i + 0.5) / grid, -1 + 2 * (j + 0.5) / grid
            if outline2d(uc, vc): faces2d.append([(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)])
    for f in faces2d:
        for (i, j) in f: uv[i, j] = np.array([-1 + 2 * i / grid, -1 + 2 * j / grid])
    edges = {}
    for f in faces2d:
        for e in zip(f, f[1:] + f[:1]):
            key = tuple(sorted(e)); edges[key] = edges.get(key, 0) + 1
    bnd = {v for e, c in edges.items() if c == 1 for v in e}
    if poly is not None:
        for v in bnd: uv[v] = poly_nearest(poly, uv[v])
    nb = {v: set() for v in uv}
    for (a_, b_) in edges: nb[a_].add(b_); nb[b_].add(a_)
    for _ in range(25):   # relax interior so cells near the edge stay even
        new_uv = dict(uv)
        for v in uv:
            if v in bnd: continue
            new_uv[v] = uv[v] * 0.5 + 0.5 * np.mean([uv[n] for n in nb[v]], axis=0)
        uv = new_uv
    bm = bmesh.new(); verts = {}
    for key, (u, v) in uv.items():
        p = Vector((cx + u * sx, -0.3, cz + v * sz)) * k
        hit = rbvh.ray_cast(p, Vector((0, 1, 0)))
        if hit[0] is not None: verts[key] = bm.verts.new(hit[0] + hit[1] * lift * k)
    n = 0
    for f in faces2d:
        if all(t in verts for t in f):
            try: bm.faces.new([verts[t] for t in f]); n += 1
            except ValueError: pass
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges[:])
    m = bpy.data.meshes.new(name); bm.to_mesh(m); bm.free()
    ob = bpy.data.objects.new(name, m); coll.objects.link(ob); m.materials.append(matx)
    for pl in m.polygons: pl.use_smooth = True
    print(name, "faces", n)
    return ob, thick
def outline_u_pocket(r=0.62, nseg=16):
    pts = [(-1.0, 1.0), (1.0, 1.0)]
    pts += [(1.0, 1.0 - t * (2.0 - r)) for t in np.linspace(0.1, 1.0, 6)]
    pts += [(1 - r + r * math.cos(-a), -1 + r + r * math.sin(-a)) for a in np.linspace(0, math.pi / 2, nseg)]
    pts += [(-1 + r - r * math.cos(-a), -1 + r + r * math.sin(-a)) for a in np.linspace(math.pi / 2, 0, nseg)]
    pts += [(-1.0, -1 + r + t * (2.0 - r)) for t in np.linspace(0.0, 0.9, 6)]
    return pts
def outline_crescent(n=360):
    outer = [(math.cos(t), math.sin(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)
             if (math.cos(t) - 0.42) ** 2 + (math.sin(t) + 0.12) ** 2 > 0.78 ** 2]
    inner = [(0.42 + 0.78 * math.cos(t), -0.12 + 0.78 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)
             if (0.42 + 0.78 * math.cos(t)) ** 2 + (-0.12 + 0.78 * math.sin(t)) ** 2 < 1.0]
    # order: outer arc (CCW, starting after the gap) then inner arc reversed
    ang = lambda p: math.atan2(p[1] - 0.0, p[0] - 0.0)
    gap = math.atan2(-0.12, 0.42)
    outer.sort(key=lambda p: (ang(p) - gap) % (2 * math.pi))
    inner.sort(key=lambda p: -((math.atan2(p[1] + 0.12, p[0] - 0.42) - gap) % (2 * math.pi)))
    return outer + inner
def u_pocket(u, v, r=0.62):
    """Straight top edge, straight sides, large rounded bottom corners (reference pockets)."""
    if abs(u) > 1 or v > 1 or v < -1: return False
    if v >= -1 + r or abs(u) <= 1 - r: return True
    return (abs(u) - (1 - r)) ** 2 + (v - (-1 + r)) ** 2 <= r * r
    if v > 0.0: return abs(u) <= 1.0 and v <= 1.0
    return (u * u) / 1.0 + (v * v) / 1.0 <= 1.0 or (abs(u) <= 1.0 and (abs(u) - 0.45) ** 2 + v * v <= 0.55 ** 2 and abs(u) > 0.45) or (abs(u) <= 0.45 and v >= -1.0)
def rounded_rect(r=0.35):
    def f(u, v):
        top = v > 0.75 and abs(u) < 1.0           # straight top edge
        du, dv = max(abs(u) - (1 - r), 0), max(-v - (1 - r), 0) if v < 0 else 0
        return (du * du + dv * dv) <= r * r and v <= 1.0
    return f
pockets = []
for s in (-1, 1):
    ob, t = patch(f"Ais_Pocket_{'L' if s > 0 else 'R'}", u_pocket, (s * 0.044, 0.158, 0.025, 0.023), M_purp, grid=36, poly=outline_u_pocket())
    pockets.append((ob, t))
def crescent(u, v):
    return (u * u + v * v) <= 1.0 and ((u - 0.42) ** 2 + (v + 0.12) ** 2) > 0.78 ** 2
moon, mt = patch("Ais_MoonEmblem", crescent, (0.0, 0.262, 0.030, 0.030), M_moon, grid=56, poly=outline_crescent())
rbm.free()
# pockets: join into one object (two separate islands), moon separate
pk = pockets[0][0]
with bpy.context.temp_override(active_object=pk, selected_editable_objects=[p for p, _ in pockets], object=pk):
    bpy.ops.object.join()
pk.name = "Ais_Pockets"; pk.data.name = "Ais_Pockets"

armside = lambda s_: ((armw + handw) > 0.3) & (x * s_ > 0)
footside = lambda s_: (footw > 0.3) & (x * s_ > 0)
def weights_two_sided(ob, region_fn):
    L = [i for i, v in enumerate(ob.data.vertices) if (ob.matrix_world @ v.co).x > 0]
    idxL, idxR = np.where(region_fn(1))[0], np.where(region_fn(-1))[0]
    kds = {}
    for s_, idx in ((1, idxL), (-1, idxR)):
        kd = KDTree(len(idx))
        for j, bi in enumerate(idx): kd.insert(P[bi] * k, j)
        kd.balance(); kds[s_] = (kd, idx)
    src = []
    for v in ob.data.vertices:
        w = ob.matrix_world @ v.co; kd, idx = kds[1 if w.x > 0 else -1]; src.append(int(idx[kd.find(w)[1]]))
    copy_weights(ob, src)
weights_two_sided(cuff_ob, armside); REGION["Ais_Cuffs"] = None
neckreg = lambda s_: (F["spine"] > 0.3) & (x * s_ > -0.01) & (z > 0.27)
weights_two_sided(collar_ob, neckreg); collar_ob["weights_done"] = True
weights_two_sided(shoe_ob, footside); weights_two_sided(sole_ob, footside)
for o in (cuff_ob, shoe_ob, sole_ob): o["weights_done"] = True
for ob, thick, cs in ((shirt_ob, 0.0018, True), (cuff_ob, 0.003, True), (romper_ob, 0.0024, True), (shoe_ob, 0, False),
                      (sole_ob, 0, False), (pk, 0.0026, True), (moon, 0.0022, True), (collar_ob, 0.0022, True)):
    finish(ob, thick, cs=cs)
    print(ob.name, "verts", len(ob.data.vertices))

for ob_, ax in ((cuff_ob, (1, 2)), (collar_ob, (0, 1)), (pk, (0, 2)), (moon, (0, 2)), (shoe_ob, (0, 1)), (sole_ob, (0, 1))):
    fix_normals(ob_); planar_uv(ob_, ax)
# ---- patches ride the romper surface exactly (Surface Deform bound in rest pose)
for m in romper_ob.modifiers:
    if m.type == 'SUBSURF': m.levels = m.render_levels = 2      # SD target must evaluate identically in viewport + render
bpy.context.view_layer.update()
for ob in (pk, moon):
    for m in list(ob.modifiers):
        if m.type in ('ARMATURE', 'CORRECTIVE_SMOOTH'): ob.modifiers.remove(m)
    sd = ob.modifiers.new("FollowRomper", 'SURFACE_DEFORM'); sd.target = romper_ob; sd.falloff = 4.0
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
        bpy.ops.object.modifier_move_to_index(modifier=sd.name, index=0)
        bpy.ops.object.surfacedeform_bind(modifier=sd.name)
    print(ob.name, "surface-deform bound", sd.is_bound)
# ---- hide body faces fully covered (keep one ring at every opening)
def inside_cuts(cuts):
    ok = np.ones(NV, bool); Pw = P * k
    for co, no in cuts: ok &= ((Pw - np.array(co)) @ np.array(no)) < -0.004 * k
    return ok
covered = (shirt & inside_cuts(cuts_shirt) & (z < 0.30)) | (romper & inside_cuts(cuts_romper) & (z > 0.06)) | shoe
keep = covered.copy()
for _ in range(1):
    border = set()
    for e in me.edges:
        a, b = e.vertices
        if keep[a] != keep[b]: border.update((a, b))
    for i in border: keep[i] = False
vg = body.vertex_groups.get("Hidden_Clothes") or body.vertex_groups.new(name="Hidden_Clothes")
vg.add([int(i) for i in np.where(keep)[0]], 1.0, 'REPLACE')
mk = body.modifiers.new("Hidden_Clothes", 'MASK'); mk.vertex_group = "Hidden_Clothes"; mk.invert_vertex_group = True
with bpy.context.temp_override(object=body, active_object=body):
    bpy.ops.object.modifier_move_to_index(modifier=mk.name, index=[m.type for m in body.modifiers].index('CORRECTIVE_SMOOTH') + 1)
print("body verts hidden", int(keep.sum()))
rig.data.pose_position = 'POSE'
bpy.ops.wm.save_as_mainfile(filepath=root + "/BabyAis_Working.blend", compress=True)
print("CLOTHING BUILT")
bpy.ops.wm.save_as_mainfile(filepath=root + "/checkpoints/BabyAis_v005_clothing.blend", compress=True, copy=True)
print("SAVED v005")
