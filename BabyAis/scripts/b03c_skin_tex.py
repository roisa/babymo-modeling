"""BATCH 03c - Ais-owned skin colour texture (Mo's painted orange blush removed; Ais blush is the
soft pink procedural mask) + eye gloss fix (no clear-coat: it mirrored the dark studio as grey)."""
import bpy, sys
root = sys.argv[1]
bpy.ops.wm.open_mainfile(filepath=root + "/BabyAis_Working.blend")
img = bpy.data.images.load(root + "/textures/T_Ais_Skin_BaseColor.1001.png")
img.source = 'TILED'; img.name = "T_Ais_Skin_BaseColor.<UDIM>"
img.filepath = "//textures/T_Ais_Skin_BaseColor.<UDIM>.png"; img.reload()
print("tiles", [t.number for t in img.tiles])
m = bpy.data.materials["M_Ais_Skin"]
tex = m.node_tree.nodes["Image Texture.002"]; tex.image = img
img.pack()
e = bpy.data.materials["M_Ais_Eye"]; bs = next(n for n in e.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
bs.inputs["Coat Weight"].default_value = 0.0; bs.inputs["Roughness"].default_value = 0.35
bs.inputs["Specular IOR Level"].default_value = 0.35
# blush: softer & a touch more saturated rose, reads like the reference
m.node_tree.nodes["Blush Strength"].inputs[1].default_value = 0.78
bpy.ops.wm.save_mainfile(compress=True)
bpy.ops.wm.save_as_mainfile(filepath=root + "/checkpoints/BabyAis_v003_face.blend", compress=True, copy=True)
print("SAVED v003")
