"""2D cartoon version of the tennis poses: flat cel shading (Toon BSDF, hard terminator, flat ambient fill),
bold dark Freestyle outline, transparent PNG. Reads BabyMo_Tennis_Poses.blend (frame N = pose N).
Usage: python toon2d.py POSES.blend OUTDIR   Env: ONLY=05,18  RES=1200  SAMPLES=24  LINE=3.2  SHADE=0.55"""
import bpy, os, sys, csv

BLEND, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
RES = int(os.environ.get("RES", "1200")); SAMPLES = int(os.environ.get("SAMPLES", "24"))
LINE = float(os.environ.get("LINE", "3.2")); AMB = float(os.environ.get("SHADE", "0.55"))
only = [s for s in os.environ.get("ONLY", "").split(",") if s]

bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene

def base_source(nt):
    """(socket feeding the base colour, or None) and the flat colour fallback."""
    bs = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bs is None: return None, (0.8, 0.8, 0.8, 1)
    inp = bs.inputs["Base Color"]
    return (inp.links[0].from_socket if inp.is_linked else None), tuple(inp.default_value)

def toonify(mat):
    if not mat or not mat.node_tree or mat.get("toon"): return
    nt = mat.node_tree; src, col = base_source(nt)
    out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
    if out is None: return
    for l in list(out.inputs["Displacement"].links): nt.links.remove(l)
    N = nt.nodes.new; L = nt.links.new
    toon = N("ShaderNodeBsdfToon"); toon.component = 'DIFFUSE'
    toon.inputs["Size"].default_value = float(os.environ.get("TSIZE", "0.85")); toon.inputs["Smooth"].default_value = 0.02
    emi = N("ShaderNodeEmission"); emi.inputs["Strength"].default_value = AMB
    add = N("ShaderNodeAddShader")
    if src is not None: L(src, toon.inputs["Color"]); L(src, emi.inputs["Color"])
    else: toon.inputs["Color"].default_value = col; emi.inputs["Color"].default_value = col
    L(toon.outputs[0], add.inputs[0]); L(emi.outputs[0], add.inputs[1]); L(add.outputs[0], out.inputs["Surface"])
    mat["toon"] = 1

for o in sc.objects:
    if o.type in ('MESH', 'CURVE') and not o.hide_render:
        for s in o.material_slots: toonify(s.material)

# lights: one key + soft fill keep the cel terminator crisp and readable
for o in list(sc.objects):
    if o.type == 'LIGHT': o.hide_render = True
key = bpy.data.lights.new("ToonKey", 'SUN'); key.energy = float(os.environ.get("KEY", "1.6")); key.angle = 0.02
ko = bpy.data.objects.new("ToonKey", key); sc.collection.objects.link(ko); ko.rotation_euler = (0.85, 0.0, -0.75)
if sc.world and sc.world.node_tree:
    bg = next((n for n in sc.world.node_tree.nodes if n.type == "BACKGROUND"), None)
    if bg: bg.inputs["Strength"].default_value = 0.0

# outline
sc.render.use_freestyle = True; sc.render.line_thickness_mode = 'ABSOLUTE'
vl = sc.view_layers[0]; fs = vl.freestyle_settings; fs.crease_angle = 2.2
ls = fs.linesets[0] if fs.linesets else fs.linesets.new("Outline")
ls.select_by_visibility = True; ls.visibility = 'VISIBLE'
ls.select_silhouette = True; ls.select_border = True; ls.select_crease = False; ls.select_contour = True; ls.select_external_contour = True
# no outline on the racket strings (they would turn the head grey)
nol = bpy.data.collections.new("NoOutline"); sc.collection.children.link(nol)
for o in sc.objects:
    if o.name.startswith("Racket_Strings"): nol.objects.link(o)
ls.select_by_collection = True; ls.collection = nol; ls.collection_negation = 'EXCLUSIVE'
st = ls.linestyle; st.color = (0.12, 0.07, 0.07); st.thickness = LINE * RES / 1200; st.thickness_position = 'CENTER'
st.caps = 'ROUND'; st.chaining = 'PLAIN'

sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
sc.render.resolution_x = sc.render.resolution_y = RES
sc.render.film_transparent = True
sc.view_settings.view_transform = os.environ.get('VT', 'AgX'); sc.view_settings.look = os.environ.get('LOOK', 'AgX - Punchy'); sc.view_settings.exposure = float(os.environ.get('EXPO', '0.15'))
cam = sc.camera; cam.data.ortho_scale = float(os.environ.get("ORTHO", "1.02"))

names = []
csvp = os.path.join(os.path.dirname(os.path.abspath(BLEND)), "renders", "tennis", "poses.csv")
if os.path.exists(csvp): names = [r[0].replace("BabyMo_Tennis_", "") for r in list(csv.reader(open(csvp)))[1:]]
for f in range(sc.frame_start, sc.frame_end + 1):
    tag = f"{f:02d}"
    if only and tag not in only: continue
    sc.frame_set(f)
    nm = next((n for n in names if n.startswith(tag)), tag)
    sc.render.filepath = f"{OUT}/BabyMo_Tennis2D_{nm}.png"
    bpy.ops.render.render(write_still=True); print("RENDERED", nm)
