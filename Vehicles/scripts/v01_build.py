"""Toy-style construction vehicles (excavator, dump truck, bulldozer, crane truck, cement mixer, wheel loader).
Every part is real editable geometry built from bevelled primitives; one collection + root empty per vehicle.
Vehicle space: front faces -Y, X lateral (+X = vehicle's left), Z up, ground at z=0, ~2 units long.
Usage: python v01_build.py OUT.blend"""
import bpy, bmesh, math, random, sys
from mathutils import Vector, Euler, Matrix, Quaternion

OUT = sys.argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
R = math.radians

# ------------------------------------------------------------------ materials
def principled(name, rgb, rough=0.35, coat=0.0, metal=0.0, spec=0.5):
    m = bpy.data.materials.new(name)
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*rgb, 1)
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metal
    bs.inputs["Coat Weight"].default_value = coat
    bs.inputs["Coat Roughness"].default_value = 0.15
    bs.inputs["Specular IOR Level"].default_value = spec
    return m
M = dict(
    yellow=principled("M_Toy_Yellow", (1.0, 0.51, 0.0), 0.3, coat=0.0, spec=0.08),   # matched to reference: mid rgb(253,187,2)
    dark=principled("M_Toy_DarkGrey", (0.035, 0.037, 0.04), 0.45, coat=0.2),
    rubber=principled("M_Toy_Rubber", (0.025, 0.026, 0.028), 0.62),
    grey=principled("M_Toy_SteelGrey", (0.22, 0.23, 0.25), 0.4, coat=0.25),
    lightgrey=principled("M_Toy_LightGrey", (0.55, 0.56, 0.58), 0.35, coat=0.25),
    chrome=principled("M_Toy_Chrome", (0.8, 0.8, 0.82), 0.18, metal=1.0),
    glass=principled("M_Toy_Glass", (0.04, 0.16, 0.36), 0.08, coat=1.0, spec=0.8),
    white=principled("M_Toy_White", (0.9, 0.9, 0.88), 0.3, coat=0.3),
    light=principled("M_Toy_Headlight", (1.0, 0.97, 0.9), 0.15, coat=1.0),
    orange=principled("M_Toy_Beacon", (1.0, 0.33, 0.0), 0.25, coat=0.5),
    rock=principled("M_Toy_Rock", (0.24, 0.11, 0.05), 0.55),
    red=principled("M_Toy_Red", (0.85, 0.02, 0.015), 0.3, coat=0.0, spec=0.12),
    green=principled("M_Toy_Green", (0.06, 0.45, 0.08), 0.32, coat=0.0, spec=0.12),
    wood=principled("M_Toy_Wood", (0.42, 0.22, 0.08), 0.6),
    card=principled("M_Toy_Cardboard", (0.62, 0.38, 0.16), 0.7),
    blue_light=principled("M_Toy_BlueLight", (0.05, 0.25, 1.0), 0.2, coat=0.6),
    red_light=principled("M_Toy_RedLight", (1.0, 0.05, 0.03), 0.2, coat=0.6),
)
# striped mixer drum: diagonal white/yellow bands
def stripe_mat(name, ca, cb, scale, spiral):
    m = bpy.data.materials.new(name); nt = m.node_tree; N = nt.nodes.new; L = nt.links.new
    bs = nt.nodes.get("Principled BSDF"); bs.inputs["Roughness"].default_value = 0.3; bs.inputs["Coat Weight"].default_value = 0.35
    tc = N("ShaderNodeTexCoord"); mp = N("ShaderNodeMapping"); L(tc.outputs["Object"], mp.inputs["Vector"])
    mp.inputs["Rotation"].default_value = (0, 0, 0)
    sep = N("ShaderNodeSeparateXYZ"); L(mp.outputs["Vector"], sep.inputs[0])
    # angle around the local Z axis + spiral along Z -> stripe parameter
    at = N("ShaderNodeMath"); at.operation = 'ARCTAN2'; L(sep.outputs["Y"], at.inputs[0]); L(sep.outputs["X"], at.inputs[1])
    mz = N("ShaderNodeMath"); mz.operation = 'MULTIPLY'; mz.inputs[1].default_value = spiral; L(sep.outputs["Z"], mz.inputs[0])
    ad = N("ShaderNodeMath"); ad.operation = 'ADD'; L(at.outputs[0], ad.inputs[0]); L(mz.outputs[0], ad.inputs[1])
    mu = N("ShaderNodeMath"); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = scale; L(ad.outputs[0], mu.inputs[0])
    sn = N("ShaderNodeMath"); sn.operation = 'SINE'; L(mu.outputs[0], sn.inputs[0])
    gt = N("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.0; L(sn.outputs[0], gt.inputs[0])
    mx = N("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (*ca, 1); mx.inputs[7].default_value = (*cb, 1)
    L(gt.outputs[0], mx.inputs[0]); L(mx.outputs[2], bs.inputs["Base Color"])
    return m
M["drum"] = stripe_mat("M_Toy_MixerDrum", (0.9, 0.88, 0.84), (1.0, 0.51, 0.0), 3.0, 2.2)
# hazard stripes for the crane hook block (diagonal black/yellow)
def hazard_mat(name):
    m = bpy.data.materials.new(name); nt = m.node_tree; N = nt.nodes.new; L = nt.links.new
    bs = nt.nodes.get("Principled BSDF"); bs.inputs["Roughness"].default_value = 0.35; bs.inputs["Coat Weight"].default_value = 0.3
    tc = N("ShaderNodeTexCoord"); sep = N("ShaderNodeSeparateXYZ"); L(tc.outputs["Object"], sep.inputs[0])
    ad = N("ShaderNodeMath"); ad.operation = 'ADD'; L(sep.outputs["X"], ad.inputs[0]); L(sep.outputs["Z"], ad.inputs[1])
    ad2 = N("ShaderNodeMath"); ad2.operation = 'ADD'; L(ad.outputs[0], ad2.inputs[0]); L(sep.outputs["Y"], ad2.inputs[1])
    mu = N("ShaderNodeMath"); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = 45.0; L(ad2.outputs[0], mu.inputs[0])
    sn = N("ShaderNodeMath"); sn.operation = 'SINE'; L(mu.outputs[0], sn.inputs[0])
    gt = N("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; L(sn.outputs[0], gt.inputs[0])
    mx = N("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (0.03, 0.03, 0.03, 1); mx.inputs[7].default_value = (1.0, 0.36, 0.0, 1)
    L(gt.outputs[0], mx.inputs[0]); L(mx.outputs[2], bs.inputs["Base Color"])
    return m
M["hazard"] = hazard_mat("M_Toy_Hazard")

# ------------------------------------------------------------------ primitive helpers
CUR = {}   # current vehicle: collection + root
def finish(name, bm, mat, bevel=0.0, seg=4, smooth=True, weights=False, extra_bevel=0.0):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); CUR["coll"].objects.link(ob); ob.parent = CUR["root"]
    me.materials.append(mat)
    for p in me.polygons: p.use_smooth = smooth
    if bevel:
        b = ob.modifiers.new("Bevel", 'BEVEL'); b.width = bevel; b.segments = seg
        b.limit_method = 'WEIGHT' if weights else 'ANGLE'
        if not weights: b.angle_limit = R(40)
        b.use_clamp_overlap = True
        if extra_bevel:
            b2 = ob.modifiers.new("BevelSoft", 'BEVEL'); b2.width = extra_bevel; b2.segments = 3; b2.limit_method = 'ANGLE'; b2.angle_limit = R(40)
        ob.modifiers.new("WeightedNormal", 'WEIGHTED_NORMAL').keep_sharp = True
    return ob

def place(ob, loc=(0, 0, 0), rot=(0, 0, 0), quat=None):
    ob.location = loc
    if quat is not None: ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = quat
    else: ob.rotation_euler = Euler(tuple(R(a) for a in rot))
    return ob

def box(name, size, loc, mat, bevel=0.04, rot=(0, 0, 0), seg=4, quat=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    return place(finish(name, bm, mat, bevel, seg), loc, rot, quat)

def cyl(name, r, d, loc, mat, rot=(0, 0, 0), bevel=0.02, segs=40, r2=None, quat=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=d)
    return place(finish(name, bm, mat, bevel, 3), loc, rot, quat)

def sphere(name, r, loc, mat, scale=(1, 1, 1)):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=r)
    ob = finish(name, bm, mat); ob.scale = scale; return place(ob, loc)

def beam(name, p0, p1, w, h, mat, bevel=0.03):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    q = d.to_track_quat('Y', 'Z')
    return box(name, (w, d.length, h), (p0 + p1) / 2, mat, bevel, quat=q)

def rod(name, p0, p1, r, mat, bevel=0.005):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    return cyl(name, r, d.length, (p0 + p1) / 2, mat, quat=d.to_track_quat('Z', 'Y'), bevel=bevel, segs=24)

def hydraulic(name, p0, p1, r=0.045, barrel_mat=None):
    p0, p1 = Vector(p0), Vector(p1); m = p0.lerp(p1, 0.58)
    rod(name + "_Barrel", p0, m, r, barrel_mat or M["dark"], bevel=0.01)
    rod(name + "_Rod", m - (m - p0).normalized() * 0.05, p1, r * 0.55, M["chrome"])
    for p in (p0, p1): cyl(name + "_Pin", r * 0.75, r * 2.6, p, M["dark"], rot=(0, 90, 0), bevel=0.006, segs=20)

def scoop(name, width, radius, loc, rot, mat, thick=0.035, open_dir=(0, 0, 1), arc_keep=0.0, keep_axis=(0, 0, 1), caps=True):
    """Half-cylinder scoop (bucket / blade): axis along X, open side toward +local Z after bisect."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=48, radius1=radius, radius2=radius, depth=width,
                          matrix=Matrix.Rotation(R(90), 4, 'Y'))
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5,
                           plane_co=Vector(keep_axis) * arc_keep * radius, plane_no=open_dir, clear_outer=True)
    ob = finish(name, bm, mat)
    so = ob.modifiers.new("Solidify", 'SOLIDIFY'); so.thickness = thick; so.offset = -1; so.use_rim = True
    b = ob.modifiers.new("Bevel", 'BEVEL'); b.width = thick * 0.35; b.segments = 3; b.limit_method = 'ANGLE'
    ob.modifiers.new("WeightedNormal", 'WEIGHTED_NORMAL').keep_sharp = True
    return place(ob, loc, rot)

def wheel(name, x, y, r, w, rim_mat, tread=True, side=1):
    z = r
    cyl(name + "_Tire", r, w, (x, y, z), M["rubber"], rot=(0, 90, 0), bevel=r * 0.28, segs=48)
    cyl(name + "_Rim", r * 0.56, w * 1.02, (x + side * 0.006, y, z), rim_mat, rot=(0, 90, 0), bevel=r * 0.08, segs=40)
    cyl(name + "_RimDish", r * 0.42, w * 1.04, (x + side * 0.01, y, z), rim_mat, rot=(0, 90, 0), bevel=r * 0.05, segs=40)
    cyl(name + "_Hub", r * 0.2, w * 1.1, (x + side * 0.02, y, z), M["dark"] if rim_mat is not M["dark"] else M["grey"], rot=(0, 90, 0), bevel=r * 0.05, segs=24)
    for i in range(6):
        a = 2 * math.pi * i / 6
        cyl(name + f"_Bolt{i}", r * 0.035, w * 1.14, (x + side * 0.02, y + math.cos(a) * r * 0.3, z + math.sin(a) * r * 0.3),
            M["grey"], rot=(0, 90, 0), bevel=0.003, segs=12)
    if tread:
        n = 18
        for i in range(n):
            a = 2 * math.pi * i / n
            for s in (-1, 1):
                box(name + f"_Lug{i}{'a' if s < 0 else 'b'}", (w * 0.42, r * 0.2, r * 0.13),
                    (x + s * w * 0.26, y + math.cos(a + s * 0.09) * r * 0.97, z + math.sin(a + s * 0.09) * r * 0.97), M["rubber"],
                    bevel=r * 0.04, rot=(math.degrees(a + s * 0.09) - 90 + s * 18, 0, 0))

def track(name, x, y0, y1, h, w, wheel_mat, n_wheels=5):
    L_ = y1 - y0; yc = (y0 + y1) / 2; rr = h / 2
    # stadium belt: rounded box, ends bevelled to a full radius
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * w, v.co.y * L_, v.co.z * h))
    bw = bm.edges.layers.float.new("bevel_weight_edge")
    for e in bm.edges:
        d = e.verts[0].co - e.verts[1].co
        e[bw] = 1.0 if abs(d.x) > 1e-6 else 0.0
    ob = finish(name + "_Belt", bm, M["dark"], bevel=rr * 0.98, seg=10, weights=True, extra_bevel=0.015)
    place(ob, (x, yc, rr))
    # pads around the belt
    per = 2 * (L_ - h) + math.pi * h; n = int(per / 0.085)
    for i in range(n):
        s = per * i / n; straight = L_ - h
        if s < straight:   p = (yc - straight / 2 + s, h); ang = 0
        elif s < straight + math.pi * rr:
            a = (s - straight) / rr; p = (yc + straight / 2 + math.sin(a) * rr, rr + math.cos(a) * rr); ang = -math.degrees(a)
        elif s < 2 * straight + math.pi * rr:
            p = (yc + straight / 2 - (s - straight - math.pi * rr), 0.0); ang = 180
        else:
            a = (s - 2 * straight - math.pi * rr) / rr; p = (yc - straight / 2 - math.sin(a) * rr, rr - math.cos(a) * rr); ang = 180 - math.degrees(a)
        box(name + f"_Pad{i:02d}", (w * 1.04, 0.05, 0.03), (x, p[0], p[1]), M["rubber"], bevel=0.008, seg=2, rot=(ang, 0, 0))
    # road wheels + sprocket/idler on the outer face
    side = 1 if x > 0 else -1
    for i in range(n_wheels):
        yy = y0 + rr * 0.9 + (L_ - rr * 1.8) * i / (n_wheels - 1)
        rad = rr * (0.62 if i in (0, n_wheels - 1) else 0.42)
        zz = rr if i in (0, n_wheels - 1) else rr * 0.62
        cyl(name + f"_RoadWheel{i}", rad, w * 0.3, (x + side * w * 0.42, yy, zz), wheel_mat, rot=(0, 90, 0), bevel=0.012, segs=32)
        cyl(name + f"_RoadHub{i}", rad * 0.4, w * 0.34, (x + side * w * 0.45, yy, zz), M["dark"] if wheel_mat is not M["dark"] else M["grey"],
            rot=(0, 90, 0), bevel=0.006, segs=20)
    box(name + "_Frame", (w * 0.3, L_ - h * 1.2, h * 0.22), (x + side * w * 0.42, yc, rr * 1.05), wheel_mat, bevel=0.02)

def cab_glass(name, x0, x1, y0, y1, z0, z1, frame_mat, roof_mat, panes=("front", "left", "right", "back"), roof_over=0.04):
    """Framed operator cab: dark frame box, glass panes on chosen faces, overhanging roof."""
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2; sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
    box(name + "_Frame", (sx, sy, sz), (cx, cy, cz), frame_mat, bevel=0.035)
    gz0, gz1 = z0 + sz * 0.2, z1 - 0.05
    gh = gz1 - gz0; gzc = (gz0 + gz1) / 2
    if "front" in panes: box(name + "_GlassFront", (sx - 0.08, 0.02, gh), (cx, y0 - 0.003, gzc), M["glass"], bevel=0.02)
    if "back" in panes: box(name + "_GlassBack", (sx - 0.08, 0.02, gh), (cx, y1 + 0.003, gzc), M["glass"], bevel=0.02)
    for s, tag in ((1, "left"), (-1, "right")):
        if tag in panes:
            xx = x1 + 0.003 if s > 0 else x0 - 0.003
            box(name + f"_Glass{tag}A", (0.02, sy * 0.48, gh), (xx, cy - sy * 0.23, gzc), M["glass"], bevel=0.02)
            box(name + f"_Glass{tag}B", (0.02, sy * 0.38, gh), (xx, cy + sy * 0.27, gzc), M["glass"], bevel=0.02)
    box(name + "_Roof", (sx + roof_over * 2, sy + roof_over * 2, 0.07), (cx, cy, z1 + 0.03), roof_mat, bevel=0.03)

def truck_cab(name, w, y0, y1, z0, z1, body=None):
    body = body or M["yellow"]
    """Cab-over truck cab with windshield, side windows, grille, headlights, bumper, mirrors."""
    sy, sz = y1 - y0, z1 - z0; cy, cz = (y0 + y1) / 2, (z0 + z1) / 2
    box(name + "_Body", (w, sy, sz), (0, cy, cz), body, bevel=0.09)
    box(name + "_Windshield", (w * 0.84, 0.03, sz * 0.36), (0, y0 - 0.005, z1 - sz * 0.27), M["glass"], bevel=0.03)
    for s in (1, -1):
        box(name + f"_SideWin{s}", (0.03, sy * 0.55, sz * 0.34), (s * (w / 2 + 0.005), cy - sy * 0.08, z1 - sz * 0.28), M["glass"], bevel=0.03)
        box(name + f"_Mirror{s}", (0.05, 0.05, 0.16), (s * (w / 2 + 0.07), y0 + 0.08, z1 - sz * 0.25), M["dark"], bevel=0.02)
        rod(name + f"_MirrorArm{s}", (s * w / 2, y0 + 0.1, z1 - sz * 0.15), (s * (w / 2 + 0.07), y0 + 0.08, z1 - sz * 0.2), 0.012, M["dark"])
        box(name + f"_Headlight{s}", (0.13, 0.03, 0.08), (s * w * 0.36, y0 - 0.008, z0 + sz * 0.3), M["light"], bevel=0.015)
    box(name + "_Grille", (w * 0.5, 0.03, sz * 0.22), (0, y0 - 0.008, z0 + sz * 0.36), M["dark"], bevel=0.02)
    for i in range(3):
        box(name + f"_Slat{i}", (w * 0.44, 0.03, 0.015), (0, y0 - 0.02, z0 + sz * (0.29 + 0.07 * i)), M["grey"], bevel=0.005)
    box(name + "_Bumper", (w * 1.02, 0.12, sz * 0.13), (0, y0 - 0.02, z0 + sz * 0.08), body, bevel=0.04)

def vehicle(name, origin):
    coll = bpy.data.collections.new(name); sc.collection.children.link(coll)
    root = bpy.data.objects.new(name + "_Root", None); coll.objects.link(root); root.location = origin
    root.empty_display_type = 'PLAIN_AXES'
    CUR["coll"], CUR["root"] = coll, root
    return root

# ================================================================== 1 EXCAVATOR
def excavator():
    vehicle("Excavator", (-3.6, 0, 0))
    for s in (1, -1): track(f"Exc_Track{'L' if s > 0 else 'R'}", s * 0.42, -0.78, 0.78, 0.36, 0.28, M["dark"])
    box("Exc_Undercarriage", (0.6, 1.1, 0.16), (0, 0, 0.27), M["dark"], bevel=0.03)
    cyl("Exc_Turntable", 0.42, 0.12, (0, 0.05, 0.42), M["dark"], bevel=0.02)
    box("Exc_House", (1.0, 1.15, 0.36), (0, 0.17, 0.66), M["yellow"], bevel=0.08)
    box("Exc_Counterweight", (1.02, 0.32, 0.4), (0, 0.66, 0.66), M["yellow"], bevel=0.12)
    box("Exc_EngineHood", (0.5, 0.45, 0.14), (-0.22, 0.42, 0.9), M["yellow"], bevel=0.05)
    box("Exc_EngineGrille", (0.02, 0.32, 0.12), (-0.51, 0.45, 0.68), M["dark"], bevel=0.01)
    rod("Exc_Exhaust", (-0.32, 0.6, 0.85), (-0.32, 0.6, 1.12), 0.03, M["dark"])
    cab_glass("Exc_Cab", 0.04, 0.48, -0.46, 0.06, 0.84, 1.42, M["dark"], M["yellow"])
    # arm: boom (two beams) -> stick -> bucket
    piv = Vector((-0.2, -0.28, 0.82)); knee = Vector((-0.2, -0.72, 1.82)); elbow = Vector((-0.2, -1.28, 1.6))
    wrist = Vector((-0.2, -1.62, 0.62))
    cyl("Exc_BoomPivot", 0.09, 0.3, piv, M["yellow"], rot=(0, 90, 0))
    beam("Exc_Boom1", piv, knee, 0.25, 0.32, M["yellow"], bevel=0.08)
    beam("Exc_Boom2", knee, elbow, 0.25, 0.3, M["yellow"], bevel=0.08)
    sphere("Exc_BoomKnee", 0.18, knee, M["yellow"], scale=(0.75, 1, 1))
    cyl("Exc_ElbowPin", 0.1, 0.27, elbow, M["yellow"], rot=(0, 90, 0))
    beam("Exc_Stick", elbow, wrist, 0.2, 0.25, M["yellow"], bevel=0.07)
    hydraulic("Exc_BoomCyl", (-0.2, -0.42, 0.66), knee + Vector((0, 0.1, -0.22)), 0.055)
    hydraulic("Exc_StickCyl", knee + Vector((0, -0.05, 0.16)), elbow + Vector((0, 0.05, 0.18)), 0.05)
    hydraulic("Exc_BucketCyl", elbow + Vector((0, -0.12, -0.05)), wrist + Vector((0, 0.02, 0.2)), 0.04)
    scoop("Exc_Bucket", 0.5, 0.3, wrist + Vector((0, -0.08, -0.12)), (35, 0, 0), M["grey"], thick=0.04, open_dir=(0, -0.3, 1))
    for i in range(5):
        box(f"Exc_Tooth{i}", (0.06, 0.1, 0.05), (wrist.x - 0.18 + 0.09 * i, wrist.y - 0.32, wrist.z - 0.37), M["grey"], bevel=0.015, rot=(-50, 0, 0))

# ================================================================== 2 DUMP TRUCK
def dump_truck():
    vehicle("DumpTruck", (0, 0, 0))
    box("Dump_Chassis", (0.76, 2.0, 0.18), (0, 0.05, 0.42), M["dark"], bevel=0.03)
    truck_cab("Dump_Cab", 1.12, -1.12, -0.4, 0.42, 1.28)
    for s in (1, -1):
        box(f"Dump_Step{s}", (0.08, 0.3, 0.08), (s * 0.58, -0.62, 0.36), M["dark"], bevel=0.02)
        box(f"Dump_FuelTank{s}", (0.12, 0.3, 0.2), (s * 0.43, -0.12, 0.5), M["dark"], bevel=0.05)
        box(f"Dump_Fender{s}", (0.36, 0.62, 0.06), (s * 0.55, 0.62, 0.86), M["dark"], bevel=0.02)
    # dump bed (open box + canopy over cab + side ribs)
    bx0, bx1, by0, by1, bz0, bz1 = -0.68, 0.68, -0.38, 1.16, 0.86, 1.46
    box("Dump_BedFloor", (bx1 - bx0, by1 - by0, 0.08), (0, (by0 + by1) / 2, bz0), M["yellow"], bevel=0.03)
    box("Dump_BedFront", (bx1 - bx0, 0.08, bz1 - bz0 + 0.1), (0, by0, (bz0 + bz1) / 2 + 0.05), M["yellow"], bevel=0.03)
    box("Dump_Canopy", (bx1 - bx0 - 0.08, 0.36, 0.06), (0, by0 - 0.16, bz1 + 0.06), M["yellow"], bevel=0.025, rot=(-6, 0, 0))
    for s in (1, -1):
        box(f"Dump_BedSide{s}", (0.08, by1 - by0, bz1 - bz0), (s * bx1, (by0 + by1) / 2, (bz0 + bz1) / 2), M["yellow"], bevel=0.03)
        box(f"Dump_BedRail{s}", (0.12, by1 - by0 + 0.04, 0.07), (s * bx1, (by0 + by1) / 2, bz1), M["yellow"], bevel=0.025)
        for i in range(4):
            box(f"Dump_Rib{s}{i}", (0.05, 0.07, bz1 - bz0 - 0.08), (s * (bx1 + 0.05), by0 + 0.25 + 0.3 * i, (bz0 + bz1) / 2 - 0.02), M["yellow"], bevel=0.02)
    box("Dump_BedTail", (bx1 - bx0, 0.08, bz1 - bz0 - 0.08), (0, by1, (bz0 + bz1) / 2 - 0.04), M["yellow"], bevel=0.03)
    rnd = random.Random(3)
    for i in range(16):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.14)
        for v in bm.verts: v.co *= 1 + rnd.uniform(-0.18, 0.18)
        ob = finish(f"Dump_Rock{i:02d}", bm, M["rock"], bevel=0.0)
        ob.modifiers.new("Subdivision", 'SUBSURF').levels = 1
        ob.location = (rnd.uniform(-0.48, 0.48), rnd.uniform(-0.2, 0.98), bz1 - 0.02 + rnd.uniform(0, 0.12) - 0.002 * (i % 3))
        ob.rotation_euler = (rnd.uniform(0, 6), rnd.uniform(0, 6), rnd.uniform(0, 6)); ob.scale = (1, 1, rnd.uniform(0.7, 0.95))
    for s in (1, -1):
        for j, yy in enumerate((-0.72, 0.44, 0.86)):
            wheel(f"Dump_Wheel{'L' if s > 0 else 'R'}{j}", s * 0.5, yy, 0.37, 0.32, M["yellow"], tread=True, side=s)

# ================================================================== 3 BULLDOZER
def bulldozer():
    vehicle("Bulldozer", (3.6, 0, 0))
    for s in (1, -1): track(f"Doz_Track{'L' if s > 0 else 'R'}", s * 0.48, -0.66, 0.84, 0.42, 0.3, M["yellow"])
    for s in (1, -1): box(f"Doz_Fender{s}", (0.34, 1.32, 0.05), (s * 0.48, 0.1, 0.45), M["yellow"], bevel=0.02)
    box("Doz_Body", (0.66, 1.15, 0.42), (0, 0.12, 0.66), M["yellow"], bevel=0.07)
    box("Doz_Hood", (0.6, 0.55, 0.22), (0, -0.2, 0.97), M["yellow"], bevel=0.07)
    box("Doz_Grille", (0.4, 0.03, 0.22), (0, -0.475, 0.86), M["dark"], bevel=0.02)
    for i in range(4): box(f"Doz_GrilleSlat{i}", (0.36, 0.03, 0.018), (0, -0.49, 0.78 + 0.055 * i), M["grey"], bevel=0.005)
    rod("Doz_Exhaust", (-0.12, -0.2, 1.05), (-0.12, -0.2, 1.38), 0.035, M["dark"])
    cyl("Doz_ExhaustCap", 0.045, 0.05, (-0.12, -0.2, 1.39), M["dark"], bevel=0.01)
    cab_glass("Doz_Cab", -0.33, 0.33, 0.12, 0.72, 0.87, 1.55, M["dark"], M["yellow"])
    box("Doz_CabBase", (0.74, 0.7, 0.06), (0, 0.42, 0.88), M["yellow"], bevel=0.02)
    # blade: curved, concave to the front, teeth along the lip
    # shallow arc, concave toward the front: keep the part of a cylinder (axis X) behind its centre line
    scoop("Doz_Blade", 1.5, 0.4, (0, -1.27, 0.4), (0, 0, 0), M["grey"], thick=0.055, open_dir=(0, -1, 0), arc_keep=0.33, keep_axis=(0, 1, 0))
    box("Doz_BladeTopRail", (1.5, 0.07, 0.06), (0, -0.9, 0.77), M["grey"], bevel=0.02)
    box("Doz_BladeBackRib", (1.3, 0.05, 0.08), (0, -0.88, 0.42), M["grey"], bevel=0.02)
    for i in range(6): box(f"Doz_Tooth{i}", (0.18, 0.12, 0.05), (-0.6 + 0.24 * i, -1.16, 0.035), M["grey"], bevel=0.02)
    for s in (1, -1):
        beam(f"Doz_PushArm{s}", (s * 0.56, -0.9, 0.3), (s * 0.56, 0.1, 0.4), 0.09, 0.12, M["yellow"], bevel=0.035)
        hydraulic(f"Doz_LiftCyl{s}", (s * 0.28, -0.42, 1.02), (s * 0.4, -0.9, 0.68), 0.045, barrel_mat=M["yellow"])

# ================================================================== 4 CRANE TRUCK
def crane_truck():
    vehicle("CraneTruck", (-3.6, 3.8, 0))
    box("Crane_Chassis", (0.8, 2.3, 0.2), (0, 0.15, 0.42), M["dark"], bevel=0.03)
    truck_cab("Crane_Cab", 1.05, -1.1, -0.45, 0.4, 1.12)
    box("Crane_Deck", (1.0, 1.45, 0.12), (0, 0.6, 0.58), M["grey"], bevel=0.03)
    for s in (1, -1):
        for j, yy in enumerate((-0.68, 0.55, 0.98)):
            wheel(f"Crane_Wheel{'L' if s > 0 else 'R'}{j}", s * 0.48, yy, 0.27, 0.22, M["lightgrey"], tread=False, side=s)
        for yy in (-0.2, 1.25):   # outriggers
            box(f"Crane_OutBeam{s}{yy}", (0.16, 0.12, 0.12), (s * 0.5, yy, 0.46), M["yellow"], bevel=0.03)
            rod(f"Crane_OutLeg{s}{yy}", (s * 0.56, yy, 0.46), (s * 0.56, yy, 0.07), 0.05, M["yellow"])
            cyl(f"Crane_OutPad{s}{yy}", 0.1, 0.05, (s * 0.56, yy, 0.03), M["dark"], bevel=0.012)
    cyl("Crane_Turntable", 0.35, 0.12, (0, 0.65, 0.7), M["dark"], bevel=0.02)
    box("Crane_Superstructure", (0.8, 0.8, 0.3), (0, 0.72, 0.9), M["yellow"], bevel=0.07)
    cab_glass("Crane_OpCab", 0.12, 0.5, 0.2, 0.62, 0.95, 1.45, M["yellow"], M["yellow"], panes=("front", "left"), roof_over=0.0)
    # telescopic boom up and over the cab
    b0 = Vector((-0.16, 0.95, 1.05)); b1 = Vector((-0.16, -0.25, 1.85)); b2 = Vector((-0.16, -1.15, 2.4))
    beam("Crane_Boom1", b0, b1 + (b1 - b0).normalized() * 0.1, 0.26, 0.26, M["yellow"], bevel=0.06)
    beam("Crane_Boom2", b1 - (b1 - b0).normalized() * 0.15, b2, 0.2, 0.2, M["yellow"], bevel=0.05)
    cyl("Crane_BoomFoot", 0.12, 0.34, b0, M["yellow"], rot=(0, 90, 0))
    hydraulic("Crane_LiftCyl", (-0.16, 0.45, 0.95), b0.lerp(b1, 0.62) + Vector((0, 0.04, -0.12)), 0.06)
    cyl("Crane_Sheave", 0.11, 0.12, b2 + Vector((0, -0.06, 0)), M["dark"], rot=(0, 90, 0), bevel=0.02)
    hook_top = b2 + Vector((0, -0.16, -0.05)); blk = hook_top + Vector((0, 0, -0.7))
    for s in (1, -1): rod(f"Crane_Cable{s}", hook_top + Vector((s * 0.03, 0, 0)), blk + Vector((s * 0.03, 0, 0.12)), 0.008, M["dark"])
    box("Crane_HookBlock", (0.2, 0.14, 0.26), blk, M["hazard"], bevel=0.05)
    # hook: curve with round bevel
    cu = bpy.data.curves.new("Crane_Hook", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.03; cu.bevel_resolution = 6
    sp = cu.splines.new('POLY'); pts = []
    for i in range(16):
        a = R(-90 + 290 * i / 15); pts.append((0, 0.11 * math.sin(a) - 0.0, -0.33 - 0.11 * math.cos(a) + 0.11))
    pts = [(0, 0, -0.13), (0, 0, -0.24)] + pts
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts): p.co = (*c, 1)
    ho = bpy.data.objects.new("Crane_Hook", cu); CUR["coll"].objects.link(ho); ho.parent = CUR["root"]; ho.location = blk
    cu.materials.append(M["dark"])

# ================================================================== 5 CEMENT MIXER
def cement_mixer():
    vehicle("CementMixer", (0, 3.8, 0))
    box("Mix_Chassis", (0.8, 2.3, 0.2), (0, 0.15, 0.42), M["dark"], bevel=0.03)
    truck_cab("Mix_Cab", 1.1, -1.1, -0.42, 0.4, 1.2)
    cyl("Mix_Beacon", 0.07, 0.1, (0, -0.8, 1.29), M["orange"], bevel=0.02, r2=0.05)
    for s in (1, -1):
        for j, yy in enumerate((-0.68, 0.55, 0.98)):
            wheel(f"Mix_Wheel{'L' if s > 0 else 'R'}{j}", s * 0.48, yy, 0.28, 0.23, M["lightgrey"], tread=False, side=s)
        box(f"Mix_SideRail{s}", (0.05, 1.4, 0.08), (s * 0.45, 0.6, 0.6), M["grey"], bevel=0.02)
    # drum: lathe profile (radius along the drum axis), tilted up at the back
    prof = [(0.0, 0.02), (0.0, 0.25), (0.08, 0.32), (0.35, 0.5), (0.7, 0.53), (1.0, 0.48), (1.25, 0.28), (1.32, 0.2), (1.32, 0.0)]
    bm = bmesh.new(); vs = [bm.verts.new((r, 0, z)) for z, r in prof]
    edges = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + edges, cent=(0, 0, 0), axis=(0, 0, 1), angle=R(360), steps=48, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    drum = finish("Mix_Drum", bm, M["drum"]); drum.modifiers.new("Subdivision", 'SUBSURF').levels = 1
    drum.location = (0, -0.25, 1.0); drum.rotation_euler = (R(-74), 0, 0)
    ax = Matrix.Rotation(R(-74), 3, 'X') @ Vector((0, 0, 1))
    c0 = Vector((0, -0.25, 1.0))
    for t, rr_, nm in ((0.05, 0.33, "Front"), (1.27, 0.25, "Back")):
        cyl(f"Mix_DrumRing{nm}", rr_, 0.06, c0 + ax * t, M["grey"], quat=ax.to_track_quat('Z', 'Y'), bevel=0.02)
    box("Mix_FrontStand", (0.55, 0.14, 0.42), (0, -0.33, 0.78), M["grey"], bevel=0.04)
    box("Mix_RearStand", (0.5, 0.14, 0.62), (0, 1.0, 0.88), M["grey"], bevel=0.04)
    cyl("Mix_Hopper", 0.16, 0.22, c0 + ax * 1.42 + Vector((0, 0.04, 0.05)), M["grey"], r2=0.24, quat=ax.to_track_quat('Z', 'Y'), bevel=0.02)
    beam("Mix_Chute", (0, 1.15, 0.92), (0, 1.38, 0.66), 0.16, 0.06, M["grey"], bevel=0.02)
    rod("Mix_Ladder1", (0.32, 1.12, 0.5), (0.32, 1.02, 1.5), 0.015, M["grey"])

# ================================================================== 6 WHEEL LOADER
def wheel_loader():
    vehicle("WheelLoader", (3.6, 3.8, 0))
    for s in (1, -1):
        for j, yy in enumerate((-0.52, 0.62)):
            wheel(f"Load_Wheel{'L' if s > 0 else 'R'}{j}", s * 0.56, yy, 0.42, 0.34, M["yellow"], tread=True, side=s)
            box(f"Load_Fender{s}{j}", (0.36, 0.55, 0.05), (s * 0.56, yy - 0.04, 0.9), M["yellow"], bevel=0.02, rot=(8 if j == 0 else -6, 0, 0))
    box("Load_FrontFrame", (0.6, 0.85, 0.36), (0, -0.5, 0.62), M["yellow"], bevel=0.07)
    box("Load_Articulation", (0.36, 0.3, 0.26), (0, 0.05, 0.62), M["dark"], bevel=0.04)
    box("Load_RearBody", (0.8, 0.95, 0.48), (0, 0.62, 0.74), M["yellow"], bevel=0.09)
    box("Load_EngineHood", (0.72, 0.62, 0.18), (0, 0.78, 1.05), M["yellow"], bevel=0.07)
    box("Load_RearGrille", (0.5, 0.03, 0.22), (0, 1.1, 0.78), M["dark"], bevel=0.02)
    box("Load_Counterweight", (0.84, 0.16, 0.26), (0, 1.12, 0.52), M["yellow"], bevel=0.07)
    rod("Load_Exhaust", (-0.24, 0.78, 1.1), (-0.24, 0.78, 1.42), 0.035, M["dark"])
    cab_glass("Load_Cab", -0.36, 0.36, -0.2, 0.42, 0.98, 1.72, M["dark"], M["yellow"])
    for s in (1, -1):
        p0 = Vector((s * 0.36, -0.2, 1.0)); p1 = Vector((s * 0.4, -1.2, 0.52))
        beam(f"Load_LiftArm{s}", p0, p1, 0.1, 0.18, M["yellow"], bevel=0.04)
        hydraulic(f"Load_LiftCyl{s}", (s * 0.34, -0.45, 0.48), p0.lerp(p1, 0.45) + Vector((0, 0, -0.08)), 0.05)
    beam("Load_CrossTube", (-0.4, -0.7, 0.82), (0.4, -0.7, 0.82), 0.12, 0.12, M["yellow"], bevel=0.04)
    hydraulic("Load_TiltCyl", (0, -0.42, 1.15), (0, -1.15, 0.86), 0.05)
    scoop("Load_Bucket", 1.4, 0.36, (0, -1.38, 0.38), (25, 0, 0), M["grey"], thick=0.045, open_dir=(0, -0.55, 1))
    for i in range(6): box(f"Load_Tooth{i}", (0.12, 0.1, 0.05), (-0.55 + 0.22 * i, -1.73, 0.1), M["grey"], bevel=0.02, rot=(10, 0, 0))

for f in (excavator, dump_truck, bulldozer, crane_truck, cement_mixer, wheel_loader): f()

# ================================================================== 7 ROAD ROLLER
def road_roller():
    vehicle("RoadRoller", (-3.6, 7.6, 0))
    cyl("Rol_Drum", 0.43, 1.2, (0, -0.72, 0.43), M["grey"], rot=(0, 90, 0), bevel=0.05, segs=56)
    for s in (1, -1):
        cyl(f"Rol_DrumCap{s}", 0.3, 0.04, (s * 0.61, -0.72, 0.43), M["yellow"], rot=(0, 90, 0), bevel=0.012)
        cyl(f"Rol_DrumHub{s}", 0.1, 0.08, (s * 0.64, -0.72, 0.43), M["dark"], rot=(0, 90, 0), bevel=0.01)
        box(f"Rol_YokeSide{s}", (0.08, 0.62, 0.55), (s * 0.7, -0.72, 0.62), M["yellow"], bevel=0.035)
        wheel(f"Rol_Wheel{'L' if s > 0 else 'R'}", s * 0.56, 0.62, 0.4, 0.32, M["yellow"], tread=False, side=s)
        box(f"Rol_RearFender{s}", (0.36, 0.7, 0.05), (s * 0.56, 0.62, 0.86), M["yellow"], bevel=0.02)
    box("Rol_YokeTop", (1.48, 0.62, 0.12), (0, -0.72, 0.95), M["yellow"], bevel=0.04)
    box("Rol_Body", (0.82, 1.15, 0.52), (0, 0.35, 0.72), M["yellow"], bevel=0.11)
    box("Rol_Grille", (0.5, 0.03, 0.2), (0, 0.93, 0.74), M["dark"], bevel=0.02)
    box("Rol_Step", (0.5, 0.25, 0.06), (0, -0.33, 0.5), M["dark"], bevel=0.02)
    rod("Rol_Exhaust", (0.28, 0.75, 0.95), (0.28, 0.75, 1.32), 0.032, M["dark"])
    box("Rol_Seat", (0.36, 0.3, 0.1), (0, 0.32, 1.05), M["dark"], bevel=0.04)
    box("Rol_SeatBack", (0.36, 0.08, 0.3), (0, 0.48, 1.2), M["dark"], bevel=0.04)
    rod("Rol_SteerCol", (0, 0.0, 0.98), (0, 0.1, 1.24), 0.02, M["dark"])
    cyl("Rol_SteerWheel", 0.11, 0.025, (0, 0.1, 1.25), M["dark"], rot=(-25, 0, 0), bevel=0.01)
    for x in (-0.38, 0.38):
        for y in (-0.08, 0.6): rod(f"Rol_Post{x}{y}", (x, y, 0.98), (x, y, 1.72), 0.025, M["dark"])
    box("Rol_Canopy", (0.95, 0.9, 0.07), (0, 0.26, 1.75), M["yellow"], bevel=0.03)
    cyl("Rol_Beacon", 0.06, 0.09, (0, 0.26, 1.83), M["orange"], bevel=0.02, r2=0.045)

# ================================================================== 8 TRACTOR
def tractor():
    vehicle("Tractor", (0, 7.6, 0))
    for s in (1, -1):
        wheel(f"Trac_RearWheel{'L' if s > 0 else 'R'}", s * 0.56, 0.42, 0.52, 0.34, M["yellow"], tread=True, side=s)
        wheel(f"Trac_FrontWheel{'L' if s > 0 else 'R'}", s * 0.44, -0.78, 0.27, 0.2, M["yellow"], tread=True, side=s)
        scoop(f"Trac_RearFender{s}", 0.4, 0.6, (s * 0.56, 0.42, 0.52), (0, 0, 0), M["yellow"], thick=0.035, open_dir=(0, 0, -1), arc_keep=-0.15, keep_axis=(0, 0, 1), caps=False)
        box(f"Trac_Headlight{s}", (0.08, 0.03, 0.07), (s * 0.18, -1.16, 0.8), M["light"], bevel=0.015)
    box("Trac_Hood", (0.52, 0.95, 0.42), (0, -0.66, 0.72), M["yellow"], bevel=0.1)
    box("Trac_HoodTop", (0.46, 0.85, 0.06), (0, -0.62, 0.95), M["yellow"], bevel=0.03)
    box("Trac_Grille", (0.34, 0.03, 0.3), (0, -1.14, 0.7), M["dark"], bevel=0.02)
    for i in range(4): box(f"Trac_Slat{i}", (0.3, 0.03, 0.015), (0, -1.155, 0.6 + 0.065 * i), M["grey"], bevel=0.005)
    box("Trac_FrontAxle", (0.75, 0.12, 0.1), (0, -0.78, 0.3), M["dark"], bevel=0.03)
    box("Trac_Weights", (0.5, 0.14, 0.2), (0, -1.2, 0.42), M["dark"], bevel=0.03)
    box("Trac_Body", (0.66, 0.65, 0.42), (0, 0.32, 0.78), M["yellow"], bevel=0.08)
    cab_glass("Trac_Cab", -0.38, 0.38, 0.06, 0.72, 0.98, 1.68, M["dark"], M["yellow"])
    rod("Trac_Exhaust", (-0.16, -0.5, 0.92), (-0.16, -0.5, 1.42), 0.032, M["dark"])
    cyl("Trac_ExhaustCap", 0.042, 0.05, (-0.16, -0.5, 1.44), M["dark"], bevel=0.01)
    box("Trac_Hitch", (0.3, 0.2, 0.1), (0, 0.85, 0.42), M["dark"], bevel=0.03)

# ================================================================== 9 FORKLIFT
def forklift():
    vehicle("Forklift", (3.6, 7.6, 0))
    for s in (1, -1):
        wheel(f"Fork_FrontWheel{'L' if s > 0 else 'R'}", s * 0.43, -0.35, 0.27, 0.24, M["dark"], tread=False, side=s)
        wheel(f"Fork_RearWheel{'L' if s > 0 else 'R'}", s * 0.4, 0.55, 0.22, 0.2, M["dark"], tread=False, side=s)
    box("Fork_Body", (0.78, 1.15, 0.38), (0, 0.1, 0.48), M["yellow"], bevel=0.08)
    box("Fork_Counterweight", (0.82, 0.32, 0.55), (0, 0.65, 0.58), M["yellow"], bevel=0.13)
    box("Fork_Seat", (0.34, 0.3, 0.1), (0, 0.22, 0.75), M["dark"], bevel=0.04)
    box("Fork_SeatBack", (0.34, 0.08, 0.3), (0, 0.38, 0.9), M["dark"], bevel=0.04)
    rod("Fork_SteerCol", (0, -0.2, 0.68), (0, -0.08, 0.98), 0.02, M["dark"])
    cyl("Fork_SteerWheel", 0.1, 0.025, (0, -0.08, 0.99), M["dark"], rot=(-25, 0, 0), bevel=0.01)
    for x in (-0.36, 0.36):
        for y in (-0.28, 0.45): rod(f"Fork_GuardPost{x}{y}", (x, y, 0.66), (x, y, 1.6), 0.03, M["dark"])
    box("Fork_GuardRoof", (0.84, 0.82, 0.05), (0, 0.09, 1.62), M["dark"], bevel=0.02)
    for i in range(4): box(f"Fork_GuardSlat{i}", (0.06, 0.75, 0.04), (-0.27 + 0.18 * i, 0.09, 1.66), M["dark"], bevel=0.01)
    for s in (1, -1):
        box(f"Fork_Mast{s}", (0.07, 0.09, 1.65), (s * 0.3, -0.62, 0.86), M["dark"], bevel=0.02)
        box(f"Fork_Upright{s}", (0.11, 0.05, 0.42), (s * 0.18, -0.72, 0.42), M["grey"], bevel=0.015)
        box(f"Fork_Tine{s}", (0.11, 0.62, 0.045), (s * 0.18, -1.02, 0.23), M["grey"], bevel=0.015)
        hydraulic(f"Fork_TiltCyl{s}", (s * 0.34, -0.2, 0.55), (s * 0.34, -0.6, 0.9), 0.035)
    for z in (0.12, 0.9, 1.65): box(f"Fork_MastBar{z}", (0.66, 0.06, 0.05), (0, -0.62, z), M["dark"], bevel=0.015)
    rod("Fork_LiftCyl", (0, -0.58, 0.15), (0, -0.58, 1.3), 0.04, M["chrome"])
    box("Fork_Carriage", (0.66, 0.05, 0.3), (0, -0.7, 0.4), M["grey"], bevel=0.02)
    # pallet + cardboard box on the forks
    for i in range(3): box(f"Fork_PalletTop{i}", (0.7, 0.16, 0.025), (0, -1.22 + 0.2 * i, 0.29), M["wood"], bevel=0.008)
    for x in (-0.3, 0, 0.3): box(f"Fork_PalletBlock{x}", (0.08, 0.56, 0.035), (x, -1.02, 0.26), M["wood"], bevel=0.008)
    box("Fork_Box", (0.56, 0.5, 0.42), (0, -1.02, 0.52), M["card"], bevel=0.02)
    box("Fork_BoxTape", (0.58, 0.08, 0.005), (0, -1.02, 0.73), M["lightgrey"], bevel=0.002)

# ================================================================== 10 GARBAGE TRUCK
def garbage_truck():
    vehicle("GarbageTruck", (-1.8, 11.6, 0))
    box("Gar_Chassis", (0.8, 2.3, 0.2), (0, 0.15, 0.42), M["dark"], bevel=0.03)
    truck_cab("Gar_Cab", 1.1, -1.12, -0.44, 0.4, 1.22, body=M["green"])
    cyl("Gar_Beacon", 0.07, 0.1, (0, -0.8, 1.31), M["orange"], bevel=0.02, r2=0.05)
    box("Gar_Body", (1.1, 1.38, 1.0), (0, 0.3, 1.0), M["green"], bevel=0.14)
    box("Gar_BodyStripe", (1.12, 1.25, 0.1), (0, 0.3, 0.86), M["yellow"], bevel=0.03)
    box("Gar_Tailgate", (1.06, 0.36, 0.95), (0, 1.12, 0.95), M["grey"], bevel=0.14)
    box("Gar_Hopper", (0.85, 0.06, 0.32), (0, 1.32, 0.62), M["dark"], bevel=0.03)
    for s in (1, -1):
        for j, yy in enumerate((-0.68, 0.45, 0.88)):
            wheel(f"Gar_Wheel{'L' if s > 0 else 'R'}{j}", s * 0.48, yy, 0.28, 0.23, M["lightgrey"], tread=False, side=s)
        box(f"Gar_LiftArm{s}", (0.06, 0.06, 0.55), (s * 0.45, 1.33, 0.6), M["grey"], bevel=0.015)
        box(f"Gar_Handrail{s}", (0.03, 0.03, 0.4), (s * 0.5, 1.3, 1.15), M["lightgrey"], bevel=0.008)
    box("Gar_RearStep", (0.9, 0.18, 0.05), (0, 1.36, 0.36), M["dark"], bevel=0.015)
    # wheelie bin on the lift
    box("Gar_Bin", (0.36, 0.34, 0.46), (0.0, 1.62, 0.42), M["green"], bevel=0.05)
    box("Gar_BinLid", (0.4, 0.38, 0.05), (0.0, 1.62, 0.68), M["green"], bevel=0.02)
    for s in (1, -1): cyl(f"Gar_BinWheel{s}", 0.06, 0.04, (s * 0.15, 1.78, 0.06), M["dark"], rot=(0, 90, 0), bevel=0.01)

# ================================================================== 11 FIRE TRUCK
def fire_truck():
    vehicle("FireTruck", (1.8, 11.6, 0))
    box("Fire_Chassis", (0.8, 2.4, 0.2), (0, 0.2, 0.42), M["dark"], bevel=0.03)
    truck_cab("Fire_Cab", 1.1, -1.12, -0.32, 0.4, 1.25, body=M["red"])
    box("Fire_CabStripe", (1.12, 0.82, 0.07), (0, -0.72, 0.68), M["white"], bevel=0.02)
    box("Fire_LightBar", (0.7, 0.14, 0.06), (0, -0.82, 1.3), M["white"], bevel=0.02)
    for s, mat in ((1, "blue_light"), (-1, "red_light")): box(f"Fire_Light{s}", (0.26, 0.15, 0.08), (s * 0.2, -0.82, 1.36), M[mat], bevel=0.03)
    box("Fire_Body", (1.08, 1.5, 0.82), (0, 0.48, 0.9), M["red"], bevel=0.1)
    box("Fire_BodyStripe", (1.1, 1.42, 0.07), (0, 0.48, 0.66), M["white"], bevel=0.02)
    for s in (1, -1):
        for i in range(3):
            box(f"Fire_Locker{s}{i}", (0.02, 0.4, 0.36), (s * 0.545, 0.0 + 0.48 * i, 1.0), M["lightgrey"], bevel=0.02)
            for k_ in range(4): box(f"Fire_LockerSlat{s}{i}{k_}", (0.025, 0.36, 0.012), (s * 0.552, 0.0 + 0.48 * i, 0.88 + 0.08 * k_), M["grey"], bevel=0.003)
        for j, yy in enumerate((-0.68, 0.55, 0.98)):
            wheel(f"Fire_Wheel{'L' if s > 0 else 'R'}{j}", s * 0.48, yy, 0.28, 0.23, M["lightgrey"], tread=False, side=s)
    cyl("Fire_HoseReel", 0.2, 0.3, (0, 1.28, 0.95), M["red"], rot=(0, 90, 0), bevel=0.02)
    cyl("Fire_Hose", 0.17, 0.26, (0, 1.28, 0.95), M["white"], rot=(0, 90, 0), bevel=0.04)
    # ladder on the roof
    cyl("Fire_LadderTurntable", 0.2, 0.08, (0, 0.95, 1.36), M["lightgrey"], bevel=0.02)
    for s in (1, -1): beam(f"Fire_LadderRail{s}", (s * 0.2, 1.0, 1.44), (s * 0.2, -1.05, 1.56), 0.05, 0.07, M["lightgrey"], bevel=0.015)
    for i in range(12):
        t = i / 11; y = 1.0 + (-1.05 - 1.0) * t; z = 1.44 + 0.12 * t
        rod(f"Fire_Rung{i}", (-0.2, y, z), (0.2, y, z), 0.014, M["white"])
    box("Fire_LadderRest", (0.5, 0.08, 0.08), (0, -0.62, 1.32), M["dark"], bevel=0.02)

for f in (road_roller, tractor, forklift, garbage_truck, fire_truck): f()


# ------------------------------------------------------------------ studio
w = bpy.data.worlds.new("Studio"); sc.world = w
bg = w.node_tree.nodes.get("Background"); bg.inputs["Color"].default_value = (1, 1, 1, 1); bg.inputs["Strength"].default_value = 0.15
st = bpy.data.collections.new("Studio"); sc.collection.children.link(st)
for nm, loc, e, sz in (("Key", (-5, -6, 7), 2400, 4), ("Fill", (7, -4, 4), 900, 5), ("Rim", (2, 8, 6), 1300, 4)):
    ld = bpy.data.lights.new(nm, 'AREA'); ld.energy = e; ld.size = sz
    lo = bpy.data.objects.new(nm, ld); st.objects.link(lo); lo.location = loc
    lo.rotation_euler = (Vector((0, 0, 0.6)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=24)
fm = bpy.data.meshes.new("Floor"); bm.to_mesh(fm); bm.free()
fl = bpy.data.objects.new("ShadowFloor", fm); st.objects.link(fl); fl.location = (0, 2, 0); fl.is_shadow_catcher = True
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = -1.2
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILT", {c.name: len(c.objects) for c in sc.collection.children})
