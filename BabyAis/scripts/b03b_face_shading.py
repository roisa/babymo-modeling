"""BATCH 03b - face identity shading: dark-brown glossy eyes, brown brows (own material), pink blush."""
import bpy, sys
sys.path.insert(0, sys.argv[-1]); import ba_common as C
root = sys.argv[1]
bpy.ops.wm.open_mainfile(filepath=root + "/BabyAis_Working.blend")
# eyes
m = bpy.data.materials["M_Ais_Eye"]; nt = m.node_tree
hsv = next(n for n in nt.nodes if n.type == "HUE_SAT")
hsv.inputs["Hue"].default_value, hsv.inputs["Saturation"].default_value, hsv.inputs["Value"].default_value = 1.0, 1.0, 0.85
bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
bs.inputs["Roughness"].default_value = 0.45
bs.inputs["Coat Weight"].default_value = 1.0; bs.inputs["Coat Roughness"].default_value = 0.03; bs.inputs["Coat IOR"].default_value = 1.38
# brows: own dark-chocolate material
dark = bpy.data.materials["M_Ais_FaceHairDark"]
brow = dark.copy(); brow.name = "M_Ais_Brow"
b = next(n for n in brow.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (0.045, 0.022, 0.014, 1); b.inputs["Metallic"].default_value = 0.0
b.inputs["Roughness"].default_value = 0.6; b.inputs["Sheen Weight"].default_value = 0.2
bpy.data.objects["Ais_Brows"].material_slots[0].material = brow
dark.name = "M_Ais_Lash"
l = next(n for n in dark.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
l.inputs["Base Color"].default_value = (0.012, 0.008, 0.007, 1); l.inputs["Metallic"].default_value = 0.0; l.inputs["Roughness"].default_value = 0.45
# skin: pink blush from the Ais_Blush attribute, mixed over the base colour texture
m = bpy.data.materials["M_Ais_Skin"]; nt = m.node_tree
bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
link = bs.inputs["Base Color"].links[0]; src = link.from_socket
att = nt.nodes.new("ShaderNodeAttribute"); att.attribute_name = "Ais_Blush"; att.attribute_type = 'GEOMETRY'; att.name = "Blush Mask"; att.location = (-500, 500)
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.55; mul.name = "Blush Strength"; mul.location = (-300, 500)
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MIX'; mix.name = "Blush Mix"; mix.location = (-100, 400)
mix.inputs[7].default_value = (0.93, 0.36, 0.40, 1)   # B colour: soft rose
nt.links.new(att.outputs["Fac"], mul.inputs[0]); nt.links.new(mul.outputs[0], mix.inputs[0])
nt.links.new(src, mix.inputs[6]); nt.links.new(mix.outputs[2], bs.inputs["Base Color"])
bpy.ops.wm.save_mainfile(compress=True)
print("shading done")
