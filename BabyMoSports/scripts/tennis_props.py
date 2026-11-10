"""Toy tennis racket + tennis ball for Baby Mo, and the fixed sprite camera / render setup."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
R = math.radians

def _mat(name, rgb, rough=0.35, coat=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*rgb, 1); bs.inputs["Roughness"].default_value = rough
    bs.inputs["Coat Weight"].default_value = coat; bs.inputs["Specular IOR Level"].default_value = 0.35
    return m

def _obj(name, me, mat, coll, parent=None):
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob); me.materials.append(mat)
    if hasattr(me, "polygons"):
        for p in me.polygons: p.use_smooth = True
    if parent: ob.parent = parent
    return ob

def build_racket(coll):
    """Racket root empty: origin = where the hand grips, +Y = toward the head, +X = string-face normal."""
    root = bpy.data.objects.new("Racket", None); coll.objects.link(root); root.empty_display_size = 0.05
    frame_m = _mat("M_Racket_Frame", (0.95, 0.12, 0.08), 0.3, coat=0.4)
    grip_m = _mat("M_Racket_Grip", (0.05, 0.12, 0.42), 0.55)
    str_m = _mat("M_Racket_Strings", (0.95, 0.95, 0.92), 0.5)
    cap_m = _mat("M_Racket_Cap", (1.0, 0.78, 0.05), 0.35, coat=0.3)
    HW, HL, HC = 0.056, 0.072, 0.20          # head half-width (Z), half-length (Y), head centre (Y)
    # frame: oval tube
    cu = bpy.data.curves.new("RacketFrame", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0075; cu.bevel_resolution = 4
    sp = cu.splines.new('POLY'); n = 64; sp.points.add(n - 1)
    for i, p in enumerate(sp.points):
        a = 2 * math.pi * i / n; p.co = (0, HC + HL * math.cos(a), HW * math.sin(a), 1)
    sp.use_cyclic_u = True
    fr = bpy.data.objects.new("Racket_Frame", cu); coll.objects.link(fr); cu.materials.append(frame_m); fr.parent = root
    # throat: two arms from the shaft into the bottom of the oval
    for s in (-1, 1):
        c2 = bpy.data.curves.new("RacketThroat", 'CURVE'); c2.dimensions = '3D'; c2.bevel_depth = 0.0065; c2.bevel_resolution = 3
        sp2 = c2.splines.new('BEZIER'); sp2.bezier_points.add(1)
        b0, b1 = sp2.bezier_points
        b0.co = (0, 0.075, 0); b0.handle_left = (0, 0.06, 0); b0.handle_right = (0, 0.1, s * 0.012)
        y1 = HC - HL * math.cos(R(38)); z1 = s * HW * math.sin(R(38))
        b1.co = (0, y1, z1); b1.handle_left = (0, y1 - 0.02, z1 * 0.6); b1.handle_right = (0, y1 + 0.01, z1 * 1.1)
        th = bpy.data.objects.new(f"Racket_Throat{s}", c2); coll.objects.link(th); c2.materials.append(frame_m); th.parent = root
    # shaft + grip + butt cap
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.0075, radius2=0.0075, depth=0.04, matrix=Matrix.Translation((0, 0.06, 0)) @ Matrix.Rotation(R(-90), 4, 'X'))
    me = bpy.data.meshes.new("RacketShaft"); bm.to_mesh(me); bm.free(); _obj("Racket_Shaft", me, frame_m, coll, root)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.0115, radius2=0.0105, depth=0.095, matrix=Matrix.Translation((0, -0.002, 0)) @ Matrix.Rotation(R(-90), 4, 'X'))
    me = bpy.data.meshes.new("RacketGrip"); bm.to_mesh(me); bm.free(); g = _obj("Racket_Grip", me, grip_m, coll, root)
    b = g.modifiers.new("Bevel", 'BEVEL'); b.width = 0.002; b.segments = 2
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.013, radius2=0.012, depth=0.008, matrix=Matrix.Translation((0, -0.052, 0)) @ Matrix.Rotation(R(-90), 4, 'X'))
    me = bpy.data.meshes.new("RacketCap"); bm.to_mesh(me); bm.free(); _obj("Racket_Cap", me, cap_m, coll, root)
    # strings: thin cylinders clipped to the oval
    bm = bmesh.new()
    def string(p0, p1):
        d = p1 - p0; L = d.length
        if L < 0.004: return
        mtx = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=0.0011, radius2=0.0011, depth=L, matrix=mtx)
    for i in range(-5, 6):                      # mains (along Y)
        z = i * HW * 0.17; t = math.sqrt(max(0.0, 1 - (z / HW) ** 2)) * HL
        string(Vector((0, HC - t, z)), Vector((0, HC + t, z)))
    for j in range(-6, 7):                      # crosses (along Z)
        y = j * HL * 0.14; t = math.sqrt(max(0.0, 1 - (y / HL) ** 2)) * HW
        string(Vector((0, HC + y, -t)), Vector((0, HC + y, t)))
    me = bpy.data.meshes.new("RacketStrings"); bm.to_mesh(me); bm.free(); _obj("Racket_Strings", me, str_m, coll, root)
    return root

def build_ball(coll, r=0.024):
    root = bpy.data.objects.new("Ball", None); coll.objects.link(root); root.empty_display_size = 0.03
    felt = _mat("M_Ball_Felt", (0.78, 0.95, 0.08), 0.85); seam = _mat("M_Ball_Seam", (0.97, 0.97, 0.95), 0.6)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=r)
    me = bpy.data.meshes.new("BallFelt"); bm.to_mesh(me); bm.free(); ob = _obj("Ball_Felt", me, felt, coll, root)
    cu = bpy.data.curves.new("BallSeam", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r * 0.07; cu.bevel_resolution = 2
    sp = cu.splines.new('POLY'); n = 96; sp.points.add(n - 1); a_, b_ = 0.75, 0.25
    for i, p in enumerate(sp.points):
        t = 2 * math.pi * i / n
        q = Vector((a_ * math.cos(t) + b_ * math.cos(3 * t), a_ * math.sin(t) - b_ * math.sin(3 * t), 2 * math.sqrt(a_ * b_) * math.sin(2 * t))).normalized() * r * 1.005
        p.co = (*q, 1)
    sp.use_cyclic_u = True
    so = bpy.data.objects.new("Ball_Seam", cu); coll.objects.link(so); cu.materials.append(seam); so.parent = root
    return root

def place(ob, at, y_dir, x_hint):
    """Place a prop: origin at `at`, local +Y along y_dir, local +X as close as possible to x_hint (world)."""
    y = Vector(y_dir).normalized(); x = Vector(x_hint); x = (x - y * x.dot(y)).normalized(); z = x.cross(y)
    M = Matrix(((x.x, y.x, z.x, at[0]), (x.y, y.y, z.y, at[1]), (x.z, y.z, z.z, at[2]), (0, 0, 0, 1)))
    ob.matrix_world = M

def setup_render(sc, res=1200, samples=48, azimuth=-28.0, elev=6.0, ortho=1.32, target=(0.0, 0.0, 0.43)):
    """Fixed orthographic sprite camera: every pose shares the same scale and ground line."""
    cam = bpy.data.objects.get("SpriteCam")
    if not cam:
        cd = bpy.data.cameras.new("SpriteCam"); cam = bpy.data.objects.new("SpriteCam", cd); sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho; cam.data.clip_start = 0.01; cam.data.clip_end = 50
    a, e = math.radians(azimuth), math.radians(elev); t = Vector(target)
    cam.location = t + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 6
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples; sc.cycles.use_denoising = True
    sc.render.resolution_x = sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    try: sc.render.image_settings.media_type = 'IMAGE'
    except Exception: pass
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.compression = 40
    return cam
