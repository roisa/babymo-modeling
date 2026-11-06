"""Shared helpers for Baby Ais production scripts (run with /opt/bpyenv python)."""
import bpy, math, os
from mathutils import Vector, Euler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def ensure_cam(name="BA_ReviewCam", ortho=False, lens=85):
    cam = bpy.data.objects.get(name)
    if not cam:
        cd = bpy.data.cameras.new(name)
        cam = bpy.data.objects.new(name, cd)
        bpy.context.scene.collection.objects.link(cam)
    cam.data.type = 'ORTHO' if ortho else 'PERSP'
    cam.data.lens = lens
    cam.data.clip_start = 0.01
    return cam

def render_view(path, azimuth_deg, target=(0, 0, 0.3), dist=2.2, elev_deg=4, res=(700, 900), samples=24, lens=85, ortho_scale=None):
    sc = bpy.context.scene
    cam = ensure_cam(ortho=ortho_scale is not None, lens=lens)
    if ortho_scale: cam.data.ortho_scale = ortho_scale
    a = math.radians(azimuth_deg); e = math.radians(elev_deg)
    t = Vector(target)
    # azimuth 0 = front (camera at -Y looking +Y), 90 = character's left side
    cam.location = t + Vector((math.sin(a) * math.cos(e) * dist, -math.cos(a) * math.cos(e) * dist, math.sin(e) * dist))
    look_at(cam, t)
    sc.camera = cam
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    try: sc.render.image_settings.media_type = 'IMAGE'
    except Exception: pass
    sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)

# ------------------------------------------------------------------ sculpt helpers
import numpy as np

MO_SCALE = 0.17312900722026825

def k_scale():
    """Ais/Mo size ratio (1.0 before batch 02 shrinks the rig)."""
    return bpy.data.objects["Ais_Rig"].scale.x / MO_SCALE

def mo2w(p):
    """Baby-Mo world landmark (measured on the original file) -> current Ais world position."""
    k = k_scale(); return Vector(p) * k

def world_coords(ob, key=None):
    me = ob.data
    src = key.data if key else me.vertices
    co = np.empty(len(src) * 3); src.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(ob.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]

def vertex_normals_world(ob):
    me = ob.data
    n = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("normal", n); n = n.reshape(-1, 3)
    N = np.array(ob.matrix_world.to_3x3().inverted().transposed())
    n = n @ N.T
    return n / np.linalg.norm(n, axis=1, keepdims=True)

def apply_world_delta(ob, delta):
    """Add a world-space per-vertex delta (N,3) to the mesh AND every shape key (keeps keys relative)."""
    me = ob.data
    Minv = np.array(ob.matrix_world.to_3x3().inverted())
    dl = delta @ Minv.T
    def add(coll):
        co = np.empty(len(coll) * 3); coll.foreach_get("co", co); co = co.reshape(-1, 3) + dl
        coll.foreach_set("co", co.ravel())
    add(me.vertices)
    if me.shape_keys:
        for kb in me.shape_keys.key_blocks: add(kb.data)
    me.update()

def falloff(P, center, radius, scale=(1, 1, 1)):
    d = (P - np.array(center)) / np.array(scale)
    r = np.linalg.norm(d, axis=1) / radius
    w = np.clip(1 - r * r, 0, 1)
    return w * w * (3 - 2 * w)  # smooth
