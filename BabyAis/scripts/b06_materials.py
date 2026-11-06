"""BATCH 06 - premium stylized materials + white studio.  Fabrics: soft cotton (sheen, fine grain bump),
shoes satin, skin with gentle subsurface warmth, hair look-dev, white high-key world + shadow-catcher
floor (presentation composites on pure white)."""
import bpy, sys, math
sys.path.insert(0, sys.argv[-1]); import ba_common as C, ba_hair_shader
root = sys.argv[1]; LOOK = sys.argv[2] if len(sys.argv) > 4 else "None"
import os; SOFT = float(os.environ.get("SOFT", "0.25")); SUNA = float(os.environ.get("SUNA", "2"))
bpy.ops.wm.open_mainfile(filepath=root + "/checkpoints/BabyAis_v005_clothing.blend")
sc = bpy.context.scene
def fabric(name, rgb, rough=0.78, sheen=0.55, grain=0.06, coat=0.0, crough=0.3):
    m = bpy.data.materials[name]; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    out = N("ShaderNodeOutputMaterial"); out.location = (600, 0)
    bs = N("ShaderNodeBsdfPrincipled"); bs.location = (300, 0)
    bs.inputs["Base Color"].default_value = (*rgb, 1); bs.inputs["Roughness"].default_value = rough
    bs.inputs["Sheen Weight"].default_value = sheen; bs.inputs["Sheen Roughness"].default_value = 0.45
    bs.inputs["Sheen Tint"].default_value = (1, 1, 1, 1); bs.inputs["Specular IOR Level"].default_value = 0.35
    bs.inputs["Coat Weight"].default_value = coat; bs.inputs["Coat Roughness"].default_value = crough
    tc = N("ShaderNodeTexCoord"); tc.location = (-600, 0)
    no = N("ShaderNodeTexNoise"); no.location = (-350, -150); no.inputs["Scale"].default_value = 900.0; no.inputs["Detail"].default_value = 2.0
    L(tc.outputs["Object"], no.inputs["Vector"])
    vb = N("ShaderNodeTexNoise"); vb.location = (-350, 150); vb.inputs["Scale"].default_value = 40.0
    L(tc.outputs["Object"], vb.inputs["Vector"])
    # very subtle large-scale value breakup so flat fabric doesn't look plastic
    mix = N("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.location = (0, 200)
    mix.inputs[0].default_value = 0.08; mix.inputs[6].default_value = (*rgb, 1); L(vb.outputs["Color"], mix.inputs[7])
    L(mix.outputs[2], bs.inputs["Base Color"])
    bu = N("ShaderNodeBump"); bu.location = (0, -200); bu.inputs["Strength"].default_value = grain; L(no.outputs["Fac"], bu.inputs["Height"])
    L(bu.outputs["Normal"], bs.inputs["Normal"]); L(bs.outputs[0], out.inputs["Surface"])
fabric("M_Ais_Fabric_Pink", (1.0, 0.075, 0.30))
fabric("M_Ais_Fabric_Lavender", (0.40, 0.22, 0.95))
fabric("M_Ais_Fabric_LightBlue", (0.28, 0.64, 1.0))
fabric("M_Ais_Pocket_Purple", (0.33, 0.14, 0.86))
fabric("M_Ais_Moon_White", (0.93, 0.93, 0.92), rough=0.7, sheen=0.4)
fabric("M_Ais_Shoe_Purple", (0.33, 0.15, 0.88), rough=0.42, sheen=0.15, grain=0.02, coat=0.25, crough=0.25)
fabric("M_Ais_Shoe_Sole_Blue", (0.30, 0.66, 1.0), rough=0.5, sheen=0.1, grain=0.02)
ba_hair_shader.build(bpy.data.materials["M_Ais_Hair"])
# skin: gentle subsurface warmth (texture colours kept)
sk = bpy.data.materials["M_Ais_Skin"]; bs = next(n for n in sk.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
bs.inputs["Subsurface Weight"].default_value = 0.18; bs.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
bs.inputs["Subsurface Scale"].default_value = 0.008; bs.inputs["Specular IOR Level"].default_value = 0.4
# ---- studio
st = bpy.data.collections.get("Studio")
w = sc.world; bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (1, 1, 1, 1); bg.inputs["Strength"].default_value = 0.55
floor = bpy.data.objects.get("Ais_StudioFloor")
if not floor:
    me = bpy.data.meshes.new("Ais_StudioFloor")
    import bmesh; bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=3.0); bm.to_mesh(me); bm.free()
    floor = bpy.data.objects.new("Ais_StudioFloor", me); st.objects.link(floor)
floor.is_shadow_catcher = True; floor.location = (0, 0, -0.0005)
sc.render.film_transparent = True
VT = "Standard" if LOOK == "Standard" else "AgX"
sc.view_settings.view_transform = VT; sc.view_settings.look = "None" if VT == "Standard" else LOOK
if VT == "Standard": sc.view_settings.exposure = -0.35
sc.view_settings.exposure = float(os.environ.get('EXPO', '-0.4'))
bpy.ops.wm.save_as_mainfile(filepath=root + "/BabyAis_Working.blend", compress=True)
print("MATERIALS OK", LOOK)
bpy.ops.wm.save_as_mainfile(filepath=root + "/checkpoints/BabyAis_v006_materials.blend", compress=True, copy=True)
print("SAVED v006")
