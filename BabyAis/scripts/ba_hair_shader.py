"""Hair look-dev (used by batch 04 preview and finalised in batch 06): very dark chocolate-black,
soft anisotropic-looking strand sheen from a UV strand bump, darker roots, warm brown highlights."""
import bpy
def build(mat):
    nt = mat.node_tree; nt.nodes.clear()
    N = nt.nodes.new; L = nt.links.new
    out = N("ShaderNodeOutputMaterial"); out.location = (900, 0)
    bs = N("ShaderNodeBsdfPrincipled"); bs.location = (600, 0)
    uv = N("ShaderNodeTexCoord"); uv.location = (-1000, 0)
    sep = N("ShaderNodeSeparateXYZ"); sep.location = (-800, -200); L(uv.outputs["UV"], sep.inputs[0])
    # strands: fine bands across each lock (u), slightly wavy along its length (v)
    # fine strands: noise stretched along the lock (u across x40, v along x1.5) -> soft hair lines, not stripes
    stretch = N("ShaderNodeMapping"); stretch.location = (-800, 200); stretch.inputs["Scale"].default_value = (40.0, 1.5, 1.0)
    L(uv.outputs["UV"], stretch.inputs["Vector"])
    wave = N("ShaderNodeTexNoise"); wave.location = (-600, 200); wave.inputs["Scale"].default_value = 3.0
    wave.inputs["Detail"].default_value = 4.0; wave.inputs["Roughness"].default_value = 0.6
    L(stretch.outputs["Vector"], wave.inputs["Vector"])
    noise = N("ShaderNodeTexNoise"); noise.location = (-600, -50); noise.inputs["Scale"].default_value = 18.0
    L(uv.outputs["UV"], noise.inputs["Vector"])
    # colour: chocolate-black base, warm brown streaks, darker roots
    ramp = N("ShaderNodeValToRGB"); ramp.location = (-350, 250)
    e = ramp.color_ramp.elements; e[0].position = 0.25; e[0].color = (0.0035, 0.0023, 0.0019, 1); e[1].position = 0.9; e[1].color = (0.013, 0.0075, 0.005, 1)
    mixf = N("ShaderNodeMath"); mixf.operation = 'MULTIPLY'; mixf.location = (-450, 250)
    L(wave.outputs["Fac"], mixf.inputs[0]); L(noise.outputs["Fac"], mixf.inputs[1]); mixf.inputs[1].default_value = 1
    add = N("ShaderNodeMath"); add.operation = 'ADD'; add.location = (-450, 380); add.use_clamp = True
    L(mixf.outputs[0], add.inputs[0]); add.inputs[1].default_value = 0.15
    L(add.outputs[0], ramp.inputs["Fac"])
    root = N("ShaderNodeMapRange"); root.location = (-350, -250); root.inputs["From Min"].default_value = 0.0; root.inputs["From Max"].default_value = 0.18
    root.inputs["To Min"].default_value = 0.55; root.inputs["To Max"].default_value = 1.0; L(sep.outputs["Y"], root.inputs["Value"])
    dark = N("ShaderNodeMix"); dark.data_type = 'RGBA'; dark.blend_type = 'MULTIPLY'; dark.location = (-100, 200)
    dark.inputs[0].default_value = 1.0; L(ramp.outputs["Color"], dark.inputs[6])
    comb = N("ShaderNodeCombineColor"); comb.location = (-250, -250)
    for i in range(3): L(root.outputs[0], comb.inputs[i])
    L(comb.outputs[0], dark.inputs[7])
    L(dark.outputs[2], bs.inputs["Base Color"])
    bump = N("ShaderNodeBump"); bump.location = (300, -250); bump.inputs["Strength"].default_value = 0.12; bump.inputs["Distance"].default_value = 0.0004
    L(wave.outputs["Fac"], bump.inputs["Height"]); L(bump.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Roughness"].default_value = 0.62
    bs.inputs["Specular IOR Level"].default_value = 0.18
    tan = N("ShaderNodeTangent"); tan.location = (300, -450); tan.direction_type = 'UV_MAP'; tan.uv_map = "UVMap"
    bs.inputs["Anisotropic"].default_value = 0.5
    L(tan.outputs["Tangent"], bs.inputs["Tangent"])
    bs.inputs["Sheen Weight"].default_value = 0.08; bs.inputs["Sheen Tint"].default_value = (0.35, 0.22, 0.16, 1); bs.inputs["Sheen Roughness"].default_value = 0.4
    bs.inputs["Coat Weight"].default_value = 0.0
    L(bs.outputs[0], out.inputs["Surface"])
    return mat
