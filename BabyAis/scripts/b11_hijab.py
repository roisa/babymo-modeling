"""BATCH 11 - Baby Ais WITH HIJAB (separate variant built from BabyAis_Final.blend).
Pink hijab: a parametric surface around the head (spherical grid from the head centre) with an oval face
opening, offset over skull/ears/clothes, bell-shaped drape below the chin (cloth never swings inward),
soft folds, rolled thick edge (solidify + subdivision).  Lavender inner cap shows as a forehead band.
Light-blue star pin.  Hair removed.  Skinned: head-rigid above the chin, blending into neck/chest/shoulder
weights over the drape.  All shape parameters are at the top for iteration."""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
sys.path.insert(0, sys.argv[-1]); import ba_common as C
root = sys.argv[1]
P_ = dict(
    OFF_TOP=0.026, OFF_SIDE=0.017, OFF_EDGE=0.004, COWL=0.017, NECK_T=122.0,      # volume over the head; snug at the face edge
    AW=58.0, THC=104.0, TH_UP=30.0, TH_DN=34.0,          # face opening oval (deg): half width, centre, up/down extent
    CHIN_NARROW=0.22,                                    # opening narrows toward the chin
    DRAPE_START=108.0,                                   # polar angle where the bell starts (cloth hangs, no inward)
    HEM_FRONT=0.298, HEM_BACK=0.255, HEM_SIDE=0.292,     # hem heights (Mo space)
    FOLD_AMP=0.0020, FOLD_N=7, CHIN_ROLL=0.0045, CHIN_T=141.0, CLEAR=0.005, TIER_AMP=0.0, DRAPE_AMP=0.0, HEM_WAVE=0.0,
    THICK=0.0055, CAP_THICK=0.002, CAP_BAND=6.0,        # cap band visible above the hijab edge (deg)
)
for kk in list(P_):
    if os.environ.get(kk): P_[kk] = float(os.environ[kk])
OUT = os.environ.get("OUT", "BabyAis_Hijab_Working.blend")
bpy.ops.wm.open_mainfile(filepath=root + "/BabyAis_Final.blend")
if bpy.data.objects.get("Ais_Collar"): bpy.data.objects.remove(bpy.data.objects["Ais_Collar"])   # hidden under the hijab
# ears are hidden under the hijab: mask them on the body so the cloth can wrap the skull smoothly
_bd = bpy.data.objects["Ais_Body"]; _gn = {g.index: g.name for g in _bd.vertex_groups}
_ear_ids = [v.index for v in _bd.data.vertices if any(_gn[g.group].startswith("DEF-ear") and g.weight > 0.15 for g in v.groups)]
_eg = _bd.vertex_groups.get("Hidden_Ears") or _bd.vertex_groups.new(name="Hidden_Ears"); _eg.add(_ear_ids, 1.0, 'REPLACE')
_mk = _bd.modifiers.new("Hidden_Ears", 'MASK'); _mk.vertex_group = "Hidden_Ears"; _mk.invert_vertex_group = True
with bpy.context.temp_override(object=_bd, active_object=_bd):
    bpy.ops.object.modifier_move_to_index(modifier=_mk.name, index=[m.name for m in _bd.modifiers].index("Hidden_Clothes") + 1)
print("ears hidden", len(_ear_ids))
k = C.k_scale()
rig = bpy.data.objects["Ais_Rig"]
HS = float(os.environ.get("HEAD_SCALE", "0.88"))
pbh = rig.pose.bones["MCH-ROT-head"]
tc = pbh.constraints.new('TRANSFORM'); tc.name = "Ais_HeadScale"
tc.target = rig; tc.subtarget = "root"; tc.owner_space = 'LOCAL'; tc.target_space = 'LOCAL'
tc.map_from = 'LOCATION'; tc.map_to = 'SCALE'; tc.mix_mode_scale = 'MULTIPLY'
for ax in "xyz":
    setattr(tc, f"to_min_{ax}_scale", HS); setattr(tc, f"to_max_{ax}_scale", HS)
# build pose = rest pose + smaller head (no action, identity pose bones)
_act = rig.animation_data.action if rig.animation_data else None
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
rig.data.pose_position = 'POSE'
_mods_off = []
for n in ("Ais_Body", "Ais_Shirt", "Ais_Romper", "Ais_Collar", "Ais_Cuffs"):
    o = bpy.data.objects.get(n)
    if o:
        for m in o.modifiers:
            if m.type in ('SUBSURF', 'SOLIDIFY', 'SURFACE_DEFORM') and m.show_viewport: m.show_viewport = False; _mods_off.append(m)
bpy.context.view_layer.update()
DG = bpy.context.evaluated_depsgraph_get()
# ---- remove hair (hidden under the hijab)
for o in list(bpy.data.collections["AIS_Hair"].objects): bpy.data.objects.remove(o)
for o in bpy.data.objects:
    if o.name.startswith(("WGT", "cs_")): o.hide_render = True
bpy.data.collections["AIS_Hair"].name = "AIS_Hijab"
coll = bpy.data.collections["AIS_Hijab"]
# ---- collision surface: body + garments (rest pose, base meshes) in Mo space
def full_eval_coords(ob):
    '''Evaluated (posed) vertex coords in ORIGINAL vertex order: masks disabled temporarily.'''
    ms = [m for m in ob.modifiers if m.type == 'MASK' and m.show_viewport]
    for m in ms: m.show_viewport = False
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    me_ = ob.evaluated_get(dg).to_mesh(); co = [v.co.copy() for v in me_.vertices]; ob.evaluated_get(dg).to_mesh_clear()
    for m in ms: m.show_viewport = True
    bpy.context.view_layer.update()
    return co
verts, polys = [], []
EAR_POLYS = set()
for n in ("Ais_Body", "Ais_Shirt", "Ais_Romper"):
    o = bpy.data.objects.get(n)
    if not o: continue
    M = o.matrix_world; base = len(verts)
    oe = o.evaluated_get(DG); me_e = oe.to_mesh()
    verts += [(M @ v.co) / k for v in me_e.vertices]
    if n == "Ais_Body":
        _vgb = {g.index: g.name for g in o.vertex_groups}
        _earv = {v.index for v in o.data.vertices if any(_vgb[g.group].startswith("DEF-ear") and g.weight > 0.05 for g in v.groups)}
        EAR_POLYS = set() if not os.environ.get('KEEP_EARS') else {len(polys) + pi for pi, p in enumerate(me_e.polygons) if any(i in _earv for i in p.vertices)}
    polys += [[base + i for i in p.vertices] for p in me_e.polygons]
    oe.to_mesh_clear()
bvh = BVHTree.FromPolygons(verts, polys)
_piv = (rig.matrix_world @ rig.data.bones["DEF-spine.006"].head_local) / k
Cc = _piv + (Vector((0, 0.012, 0.47)) - _piv) * HS
print("head scale", HS, "centre", tuple(round(c, 4) for c in Cc))
def sph(a, t):
    a, t = math.radians(a), math.radians(t)
    return Vector((math.sin(t) * math.sin(a), math.sin(t) * math.cos(a), math.cos(t)))
def surf(d, window=0.04):
    """Outermost surface along d within 4 cm of the first exit from the head centre (ears, clothes)."""
    o = Cc.copy(); first = None; far = None; travelled = 0.0
    for _ in range(8):
        hit = bvh.ray_cast(o, d, 0.6)
        if hit[0] is None: break
        dist = (hit[0] - Cc).length
        if first is None: first = dist
        if dist - first > window: break
        far = dist; o = hit[0] + d * 1e-4
    return far if far is not None else 0.12
NA, NT, TMAX = 128, 120, 168.0
_b = bpy.data.objects["Ais_Body"]; _vg = {g.index: g.name for g in _b.vertex_groups}
_bco = full_eval_coords(_b)
EAR = [(_b.matrix_world @ _bco[v.index]) / k for v in _b.data.vertices
       if any(_vg[g.group].startswith("DEF-ear") and g.weight > 0.2 for g in v.groups)]
print("ear verts", len(EAR))
BELL_K, BELL_W, BELL_T = float(os.environ.get('BELL_K', '0.90')), float(os.environ.get('BELL_W', '0.6')), float(os.environ.get('BELL_T', '96'))
A = np.array([360.0 * j / NA for j in range(NA)])           # azimuth: 0 back(+Y), 90 her left(+X), 180 front
T = np.array([0.6 + (TMAX - 0.6) * i / (NT - 1) for i in range(NT)])
def opening_q(a, t, up_shift=0.0):
    da = ((a - 180 + 180) % 360) - 180
    tc = P_["THC"]
    up = P_["TH_UP"] + up_shift
    dt = (t - tc) / (up if t < tc else P_["TH_DN"])
    w = P_["AW"] * (1 - P_["CHIN_NARROW"] * max(0.0, (t - tc) / P_["TH_DN"])) + (5.0 if up_shift < 0 else 0.0)
    return math.sqrt((da / max(w, 1e-3)) ** 2 + dt * dt)
def build_R(off_scale=1.0, edge=None, up_shift=0.0, minoff=0.0035):
    H = np.zeros((NT, NA)); R = np.zeros((NT, NA)); Rmin = np.zeros((NT, NA))
    for i, t in enumerate(T):
        for j, a in enumerate(A):
            H[i, j] = surf(sph(a, t), 0.04 if t < 125 else 0.14)
    # ears: every ear vertex raises the surface radius in its grid neighbourhood
    for e_ in (EAR if os.environ.get('KEEP_EARS') else []):
        dv = e_ - Cc; r_ = dv.length; dn = dv / r_
        t_ = math.degrees(math.acos(max(-1, min(1, dn.z)))); a_ = math.degrees(math.atan2(dn.x, dn.y)) % 360
        i0 = int(round((t_ - T[0]) / (T[1] - T[0]))); j0 = int(round(a_ / 360 * NA))
        for di in range(-10, 11):
            for dj in range(-10, 11):
                ii = i0 + di
                fall = max(0.0, 1 - (di * di + dj * dj) / 110.0)
                if 0 <= ii < NT and fall > 0:
                    jj = (j0 + dj) % NA
                    target = r_ + 0.002 - 0.012 * (1 - fall) ** 1.5
                    H[ii, jj] = max(H[ii, jj], target)
    # teardrop silhouette: at the sides and back the cloth falls from the widest point (ear level) onto the
    # shoulders - horizontal radius never shrinks going down (no ear bumps / neck waist)
    for j, a_ in enumerate(A):
        da = abs(((a_ - 180 + 180) % 360) - 180)
        w = min(max((da - 50) / 35, 0.0), 1.0); w = w * w * (3 - 2 * w)
        if w <= 0: continue
        rho = 0.0
        for i, t in enumerate(T):
            st = math.sin(math.radians(t))
            if t >= BELL_T:
                need = BELL_K * rho / max(st, 0.05)
                if need > H[i, j]: H[i, j] = H[i, j] + (need - H[i, j]) * w * BELL_W
            rho = max(rho, H[i, j] * st) if t >= 82 else H[i, j] * st
    # bib: below the chin the cloth hangs - horizontal radius may not shrink going down
    for j in range(NA):
        rho = 0.0
        for i, t in enumerate(T):
            st = math.sin(math.radians(t))
            if t >= P_["NECK_T"]:
                fw = ((1 - math.cos(math.radians(A[j]))) / 2) ** float(os.environ.get("BIB_POW", "0"))
                H[i, j] = max(H[i, j], H[i, j] + (0.96 * rho / max(st, 0.05) - H[i, j]) * fw)
            rho = H[i, j] * st
    Hs = H.copy()                         # smoothed head: volume absorbs the ears (no ear-muff bumps)
    for _ in range(40):
        Hs[1:-1] = 0.25 * Hs[:-2] + 0.5 * Hs[1:-1] + 0.25 * Hs[2:]
        Hs = 0.25 * np.roll(Hs, 1, 1) + 0.5 * Hs + 0.25 * np.roll(Hs, -1, 1)
        Hs = np.maximum(Hs, H - 0.006)
    e = P_["OFF_EDGE"] if edge is None else edge
    for i, t in enumerate(T):
        for j, a in enumerate(A):
            q = opening_q(a, t, up_shift)
            top = max(0.0, math.cos(math.radians(t)))
            back = (1 + math.cos(math.radians(a))) / 2
            base = P_["OFF_SIDE"] + (P_["OFF_TOP"] - P_["OFF_SIDE"]) * max(top, 0.7 * back * max(0.0, 1 - max(0.0, t - 100) / 30))
            neck = min(max((t - P_["NECK_T"] + 12) / 18, 0.0), 1.0)
            base = base * (1 - neck) + P_["COWL"] * neck
            base *= off_scale
            ramp = min(max((q - 1.0) / 0.8, 0.0), 1.0); ramp = ramp * ramp * (3 - 2 * ramp)
            R[i, j] = (H[i, j] * (1 - ramp) + max(Hs[i, j], H[i, j] - 0.004) * ramp) + e + (base - e) * ramp
            Rmin[i, j] = H[i, j] + (e if q < 1.6 else max(minoff, 0.006 * off_scale + minoff * (1 - off_scale)))
    Rm0 = Rmin.copy()                      # smooth the lower limit too (no steps where the surface search widens)
    for _ in range(25):
        Rs = Rmin.copy()
        Rs[1:-1] = 0.25 * Rmin[:-2] + 0.5 * Rmin[1:-1] + 0.25 * Rmin[2:]
        Rs = 0.25 * np.roll(Rs, 1, 1) + 0.5 * Rs + 0.25 * np.roll(Rs, -1, 1)
        Rmin = np.maximum(Rs, Rm0 - 0.0025)
    R = np.maximum(R, Rmin)
    for _ in range(int(os.environ.get("R_SMOOTH", "30"))):
        Rs = R.copy()
        Rs[1:-1] = 0.25 * R[:-2] + 0.5 * R[1:-1] + 0.25 * R[2:]
        Rs = 0.25 * np.roll(Rs, 1, 1) + 0.5 * Rs + 0.25 * np.roll(Rs, -1, 1)
        R = np.maximum(Rs, Rmin)
    return R, H
def interp(Rg, a, t):
    x = (a % 360.0) / 360.0 * NA; j0 = int(math.floor(x)) % NA; j1 = (j0 + 1) % NA; fx = x - math.floor(x)
    y = (t - T[0]) / (T[1] - T[0]); i0 = int(min(max(math.floor(y), 0), NT - 2)); fy = min(max(y - i0, 0.0), 1.0)
    return (Rg[i0, j0] * (1 - fx) + Rg[i0, j1] * fx) * (1 - fy) + (Rg[i0 + 1, j0] * (1 - fx) + Rg[i0 + 1, j1] * fx) * fy
def hem_z(a):
    back = (1 + math.cos(math.radians(a))) / 2; side = abs(math.sin(math.radians(a)))
    front = max(0.0, -math.cos(math.radians(a)))
    return P_["HEM_FRONT"] * (1 - back) + P_["HEM_BACK"] * back + 0.012 * side ** 2 - 0.016 * front ** 2 \
        + P_["HEM_WAVE"] * (math.sin(math.radians(a) * 7 + 0.4) * 0.7 + 0.3 * math.sin(math.radians(a) * 13))
def make_surface(name, Rg, cut_open_shift=0.0, tmax_keep=None, folds=True):
    def rad(a, t):
        r = interp(Rg, a, t)
        if folds and t > 112:
            g = min((t - 112) / 24, 1.0) * max(0.0, 1 - max(0.0, t - 150) / 20) * (1 - (1 + math.cos(math.radians(a))) / 2) ** 1.5
            da = math.radians(a)
            r += P_["FOLD_AMP"] * g * (math.sin(P_["FOLD_N"] * da + 0.8 * math.sin(2 * da)) + 0.45 * math.sin(2.3 * P_["FOLD_N"] * da + 1.3))
        if folds:
            da_ = math.radians(a)
            frontw = ((1 - math.cos(da_)) / 2) ** 2
            # tiers: soft horizontal folds where the cloth wraps under the chin / around the neck
            g1 = max(0.0, 1 - abs(t - 140) / 18)
            r += P_["TIER_AMP"] * g1 * frontw * math.sin((t - 128) / 7.5 * 2 * math.pi + 0.6 * math.sin(3 * da_))
            # drape: vertical folds falling from the neck over the shoulders and down the back
            g2 = min(max((t - 140) / 20, 0.0), 1.0) ** 1.5
            r += P_["DRAPE_AMP"] * g2 * (math.sin(6 * da_ + 1.2 * math.sin(2 * da_)) * 0.75 + 0.25 * math.sin(13 * da_ + 0.5))
            front = (1 - math.cos(math.radians(a))) / 2
            r += P_["CHIN_ROLL"] * front ** 2 * math.exp(-((t - P_["CHIN_T"]) / 6.0) ** 2)
        return r
    def pos(a, t): return Cc + sph(a, t) * rad(a, t)
    def keep_at(a, t):
        if opening_q(a, t, cut_open_shift) < 1.0: return False
        if tmax_keep is not None and t > tmax_keep: return False
        return pos(a, t).z >= hem_z(a)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap"); G = {}; AT = {}
    for i, t in enumerate(T):
        for j, a in enumerate(A):
            G[i, j] = bm.verts.new(pos(a, t) * k); AT[G[i, j]] = (a, t)
    pole = bm.verts.new((Cc + Vector((0, 0, Rg[0].mean()))) * k)
    keep = {(i, j): keep_at(A[j], T[i]) for i in range(NT) for j in range(NA)}
    # a face survives if >= 3 of its corners are kept (boundary verts get snapped below)
    for i in range(NT - 1):
        for j in range(NA):
            j2 = (j + 1) % NA
            q = [(i, j), (i, j2), (i + 1, j2), (i + 1, j)]
            if sum(keep[c] for c in q) >= 3:
                f = bm.faces.new([G[c] for c in q])
                for lp, c in zip(f.loops, q): lp[uvl].uv = (A[c[1]] / 360.0, T[c[0]] / TMAX)
    for j in range(NA):
        if keep[0, j] and keep[0, (j + 1) % NA]: bm.faces.new((G[0, (j + 1) % NA], G[0, j], pole))
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    # snap every border vertex exactly onto the opening oval / hem / tmax curve
    border = [v for v in bm.verts if v.is_boundary and v in AT]
    for v in border:
        a, t = AT[v]
        lo, hi = 0.0, 1.0
        if opening_q(a, t, cut_open_shift) < 1.15:            # opening edge: bisect along the ray to the oval centre
            c = (180.0, P_["THC"])
            da = ((a - 180 + 180) % 360) - 180
            f = lambda s_: opening_q(180 + da * s_, c[1] + (t - c[1]) * s_, cut_open_shift) - 1.0
            lo, hi = 0.3, 2.5
            for _ in range(40):
                m = (lo + hi) / 2
                (lo, hi) = (lo, m) if f(m) > 0 else (m, hi)
            a2, t2 = 180 + da * hi, c[1] + (t - c[1]) * hi
        elif tmax_keep is not None and t > tmax_keep - 3:
            a2, t2 = a, tmax_keep
        else:                                                 # hem: bisect t until z == hem_z
            lo, hi = t - 6, t + 6
            for _ in range(40):
                m = (lo + hi) / 2
                (lo, hi) = (m, hi) if pos(a, m).z > hem_z(a) else (lo, m)
            a2, t2 = a, lo
        v.co = pos(a2, t2) * k
    for _ in range(2):   # relax the ring next to the border to even out cells
        bmesh.ops.smooth_vert(bm, verts=list({e.other_vert(v) for v in border for e in v.link_edges if not e.other_vert(v).is_boundary}),
                              factor=0.3, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    clr = P_["CLEAR"] if folds else 0.0022
    moved = 0
    for _ in range(3):
        for v in bm.verts:
            p = v.co / k
            loc, nrm, _i, dist = bvh.find_nearest(p)
            if loc is None or _i in EAR_POLYS: continue
            need = clr if not v.is_boundary else min(clr, 0.003)
            if (p - loc).dot(nrm) < need:
                v.co = (loc + nrm * need) * k; moved += 1
        inner = [v for v in bm.verts if not v.is_boundary]
        bmesh.ops.smooth_vert(bm, verts=inner, factor=0.25, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    inner = [v for v in bm.verts if not v.is_boundary]
    for _ in range(int(os.environ.get("POST_SMOOTH", "2"))):
        bmesh.ops.smooth_vert(bm, verts=inner, factor=0.25, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    for it in range(int(os.environ.get("FINAL_CLR", "4"))):                     # final clearance, alternated with smoothing of only the pushed area
        pushed = []
        for v in bm.verts:
            p = v.co / k; loc, nrm, _i, dist = bvh.find_nearest(p)
            if _i in EAR_POLYS: continue
            need = (clr if not v.is_boundary else min(clr, 0.003)) * (1.0 + 0.4 * (it < 3))
            if loc is not None and (p - loc).dot(nrm) < need: v.co = (loc + nrm * need) * k; pushed.append(v)
        if it < 3 and pushed:
            ring = set(pushed)
            for _ in range(3): ring |= {e.other_vert(v) for v in list(ring) for e in v.link_edges}
            ring = [v for v in ring if not v.is_boundary]
            for _ in range(4):
                bmesh.ops.smooth_vert(bm, verts=ring, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    if folds:                               # dent-fill on the head part: radial max(v, mean(neighbours))
        head = [v for v in bm.verts if v in AT and AT[v][1] < 114 and not v.is_boundary]
        filled = 0
        for _ in range(int(os.environ.get("DENT_IT", "40"))):
            upd = {}
            for v in head:
                nb = [e.other_vert(v).co for e in v.link_edges]
                avg = sum(nb, Vector()) / len(nb)
                c = Cc * k; dv = v.co - c; r0 = dv.length; ra = (avg - c).length
                if ra > r0 + 1e-6: upd[v] = c + dv / r0 * (r0 + (ra - r0) * 0.8)
            for v, co in upd.items(): v.co = co
            filled = max(filled, len(upd))
        print(name, "dent-fill max verts", filled)
    print(name, "clearance moves", moved)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.faces:
        f0 = max(bm.faces, key=lambda f: f.calc_center_median().z)
        if f0.normal.z < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
    m = bpy.data.meshes.new(name); bm.to_mesh(m); bm.free()
    ob = bpy.data.objects.new(name, m); coll.objects.link(ob)
    for pl in m.polygons: pl.use_smooth = True
    return ob
R, H = build_R()
hijab = make_surface("Ais_Hijab", R)
Rc, _ = build_R(off_scale=0.0, edge=0.0020, minoff=0.002)
cap = make_surface("Ais_HijabInnerCap", Rc, cut_open_shift=-P_["CAP_BAND"], tmax_keep=78, folds=False)   # forehead band + crown only
print("hijab faces", len(hijab.data.polygons), "cap faces", len(cap.data.polygons))
# ---- star pin on her left temple, on the hijab surface
def star_mesh(name, Ro=0.0165, Ri=0.0075, h=0.0042, n=5):
    bm = bmesh.new(); top, bot = [], []
    for s in range(2 * n):
        r = Ro if s % 2 == 0 else Ri; a = math.pi / 2 + math.pi * s / n
        top.append(bm.verts.new((r * math.cos(a) * k, r * math.sin(a) * k, h * k)))
        bot.append(bm.verts.new((r * math.cos(a) * k, r * math.sin(a) * k, 0)))
    ct = bm.verts.new((0, 0, h * 1.35 * k)); cb = bm.verts.new((0, 0, 0))
    for s in range(2 * n):
        s2 = (s + 1) % (2 * n)
        bm.faces.new((top[s], top[s2], ct)); bm.faces.new((bot[s2], bot[s], cb)); bm.faces.new((bot[s], bot[s2], top[s2], top[s]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    m = bpy.data.meshes.new(name); bm.to_mesh(m); bm.free()
    ob = bpy.data.objects.new(name, m); coll.objects.link(ob)
    return ob
star = star_mesh("Ais_HijabStarPin")
SA, ST = float(os.environ.get("STAR_A", "128")), float(os.environ.get("STAR_T", "79"))
d = sph(SA, ST)
i_ = int(np.argmin(np.abs(T - ST))); j_ = int(np.argmin(np.abs(A - SA)))
pin_p = (Cc + d * (interp(R, SA, ST) + P_["THICK"] * 1.05)) * k
nrm = d.copy()
star.matrix_world = Matrix.Translation(pin_p) @ nrm.to_track_quat('Z', 'Y').to_matrix().to_4x4() @ Matrix.Rotation(math.radians(-15), 4, 'Z')
for pl in star.data.polygons: pl.use_smooth = False
# ---- materials
pink = bpy.data.materials["M_Ais_Fabric_Pink"].copy(); pink.name = "M_Ais_Hijab_Pink"
bsdf = next(n for n in pink.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
mixn = next((n for n in pink.node_tree.nodes if n.type == "MIX"), None)
col = (1.0, 0.09, 0.36, 1)
if mixn: mixn.inputs[6].default_value = col
else: bsdf.inputs["Base Color"].default_value = col
bsdf.inputs["Sheen Weight"].default_value = 0.45; bsdf.inputs["Roughness"].default_value = 0.6
hijab.data.materials.append(pink)
cap.data.materials.append(bpy.data.materials["M_Ais_Fabric_Lavender"])
sm = bpy.data.materials["M_Ais_Shoe_Sole_Blue"].copy(); sm.name = "M_Ais_HijabStar_Blue"
star.data.materials.append(sm)
# ---- skinning
body = bpy.data.objects["Ais_Body"]; me = body.data
vgn = {g.index: g.name for g in body.vertex_groups}
ALLOW = ("DEF-spine", "DEF-shoulder", "DEF-pelvis", "DEF-upper_arm")
idx, W = [], []
for v in me.vertices:
    w = {vgn[g.group]: g.weight for g in v.groups if vgn[g.group].startswith(ALLOW) and g.weight > 0.01}
    if w and v.co is not None:
        idx.append(v.index); W.append(w)
_bco2 = full_eval_coords(body)
Pw = [body.matrix_world @ _bco2[i] for i in idx]
kd = KDTree(len(Pw))
for n_, p in enumerate(Pw): kd.insert(p, n_)
kd.balance()
def skin(ob, rigid=False):
    groups = {}
    for v in ob.data.vertices:
        wp = ob.matrix_world @ v.co; z = wp.z / k
        f = 0.0 if rigid else min(max((0.39 - z) / 0.10, 0.0), 1.0); f = f * f * (3 - 2 * f)
        w = {"DEF-spine.006": 1.0 - f}
        if f > 0:
            cap_zone = abs(wp.x / k) > 0.07 and abs(wp.y / k) < 0.03   # top of the shoulder only
            bw = {n_: (x * (0.35 if cap_zone else 0.0) if 'upper_arm' in n_ else x) for n_, x in W[kd.find(wp)[1]].items()}
            if sum(bw.values()) <= 0: bw = {"DEF-spine.004": 1.0}
            tot = sum(bw.values())
            for n_, x in bw.items(): w[n_] = w.get(n_, 0) + f * x / tot
        w = dict(sorted(w.items(), key=lambda t: -t[1])[:4]); tot = sum(w.values())
        for n_, x in w.items():
            if x / tot > 0.001: groups.setdefault(n_, []).append((v.index, x / tot))
    for n_, lst in groups.items():
        g = ob.vertex_groups.new(name=n_)
        for vi, x in lst: g.add([vi], x, 'REPLACE')
    # built in the posed (small-head) state -> move every vertex back to rest space through the inverse of its
    # blended bone matrix (exact inverse of linear-blend skinning for this pose)
    RW = rig.matrix_world; RWi = RW.inverted()
    BM = {n_: RW @ rig.pose.bones[n_].matrix @ rig.data.bones[n_].matrix_local.inverted() @ RWi for n_ in groups}
    vw = {}
    for n_, lst in groups.items():
        for vi, x in lst: vw.setdefault(vi, []).append((n_, x))
    OM = ob.matrix_world; OMi = OM.inverted()
    for vi, lst in vw.items():
        Mb = Matrix(((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)))
        for n_, x in lst: Mb = Mb + BM[n_] * x
        ob.data.vertices[vi].co = OMi @ (Mb.inverted() @ (OM @ ob.data.vertices[vi].co))
    mw = ob.matrix_world.copy(); ob.parent = rig; ob.matrix_world = mw
    am = ob.modifiers.new("Armature", 'ARMATURE'); am.object = rig
skin(hijab); skin(cap, rigid=True); skin(star, rigid=True)
for ob, th, cs in ((hijab, P_["THICK"], True), (cap, P_["CAP_THICK"], False)):
    if cs:
        c = ob.modifiers.new("CorrectiveSmooth", 'CORRECTIVE_SMOOTH'); c.smooth_type = 'LENGTH_WEIGHTED'; c.iterations = 8; c.factor = 0.6
    so = ob.modifiers.new("Solidify", 'SOLIDIFY'); so.thickness = th * k; so.offset = 1.0; so.use_rim = True; so.use_quality_normals = True
    sd = ob.modifiers.new("Subdivision", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
bv = star.modifiers.new("Bevel", 'BEVEL'); bv.width = 0.0012 * k; bv.segments = 3
sd = star.modifiers.new("Subdivision", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
rig.data.pose_position = 'POSE'
for m in _mods_off: m.show_viewport = True
if rig.animation_data and _act: rig.animation_data.action = _act
bpy.data.collections["GEO Baby Ais"].name = "GEO Baby Ais Hijab"
bpy.ops.wm.save_as_mainfile(filepath=root + "/" + OUT, compress=True)
print("HIJAB SAVED", OUT, {kk: v for kk, v in P_.items()})
