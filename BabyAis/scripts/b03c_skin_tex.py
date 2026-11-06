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
# lighter, warmer peach skin like the reference (texture kept, graded in the shader)
nt = m.node_tree; bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
hsv = nt.nodes.new("ShaderNodeHueSaturation"); hsv.name = "Skin Grade"; hsv.location = (-350, 300)
hsv.inputs["Hue"].default_value = 0.505; hsv.inputs["Saturation"].default_value = 0.82; hsv.inputs["Value"].default_value = 1.22
tex.location = (-650, 300)
targets = [l.to_socket for l in nt.links if l.from_node == tex and l.from_socket.name == "Color" and l.to_node.name == "Blush Mix"]
for l in [l for l in nt.links if l.from_node == tex and l.to_node.name == "Blush Mix"]: nt.links.remove(l)
nt.links.new(tex.outputs["Color"], hsv.inputs["Color"])
for sock in targets: nt.links.new(hsv.outputs["Color"], sock)
print("skin graded", len(targets))
# blush: softer & a touch more saturated rose, reads like the reference
m.node_tree.nodes["Blush Strength"].inputs[1].default_value = 0.92
bpy.ops.wm.save_mainfile(compress=True)
bpy.ops.wm.save_as_mainfile(filepath=root + "/checkpoints/BabyAis_v003_face.blend", compress=True, copy=True)
print("SAVED v003")
