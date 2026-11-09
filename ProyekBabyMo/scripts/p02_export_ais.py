"""Export Baby Ais (hijab edition) as a skinned, animated GLB for the game.
Keeps only the character meshes + rig; pockets/moon switched from Surface Deform to skin weights so they
ride along in the browser; deform bones only; a curated set of the Baby Mo animation clips, sampled.
Usage: python p02_export_ais.py BabyAis_Hijab_Final.blend OUT.glb"""
import bpy, sys, os

SRC, OUT = sys.argv[1], sys.argv[2]
CLIPS = {  # game clip name -> source action
    "Idle": "Idle_breathing", "Wave": "Idle_Wave", "Walk": "Locomotion_Walk", "Run": "Locomotion_Run",
    "Jump": "Locomotion_Jumping", "Cheer": "Gesture_Hore", "Clap": "Gesture_Clap", "Point": "Gesture_Pointing",
    "ThumbsUp": "Gesture_Thumbs_Up", "LetsGo": "Gesture_Lets_Go", "Nod": "Gesture_Nodding", "Stand": "Ais_Pose_Presentation",
}
bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
rig = bpy.data.objects["Ais_Rig"]
LOW = {"Ais_Hijab", "Ais_HijabInnerCap", "Ais_Pockets", "Ais_MoonEmblem", "Ais_Romper"}
DECIMATE = {"Ais_HijabInnerCap": 0.35, "Ais_Pockets": 0.5, "Ais_MoonEmblem": 0.5}
keep_meshes = [o for o in bpy.data.collections["GEO Baby Ais Hijab"].all_objects if o.type == 'MESH']
# pockets / moon: skin weights instead of Surface Deform
for o in keep_meshes:
    sd = [m for m in o.modifiers if m.type == 'SURFACE_DEFORM']
    for m in sd: o.modifiers.remove(m)
    if sd and not any(m.type == 'ARMATURE' for m in o.modifiers):
        am = o.modifiers.new("Armature", 'ARMATURE'); am.object = rig
        with bpy.context.temp_override(object=o, active_object=o):
            bpy.ops.object.modifier_move_to_index(modifier=am.name, index=0)
    for m in o.modifiers:
        if m.type == 'SUBSURF': m.levels = 0 if o.name in LOW else 1
    if o.name in DECIMATE:
        d = o.modifiers.new("GameDecimate", 'DECIMATE'); d.ratio = DECIMATE[o.name]
# shape keys block modifier application on export: bake the current mix away (blinks are not used in-game)
for o in keep_meshes:
    if o.data.shape_keys:
        o.shape_key_add(name="__mix", from_mix=True)
        for kb in list(o.data.shape_keys.key_blocks): o.shape_key_remove(kb) if kb.name != "__mix" else None
        o.shape_key_remove(o.data.shape_keys.key_blocks["__mix"])
# glTF has no UDIM tiles: skin base colour -> the 1001 tile image; drop height/metal/rough/normal/AO maps
TILE = bpy.data.images.load(os.path.join(os.path.dirname(SRC), "textures", "T_Ais_Skin_BaseColor.1001.png"))
for mat in bpy.data.materials:
    if not mat.node_tree: continue
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type != 'TEX_IMAGE' or not n.image: continue
        img = n.image
        usable = img.source != 'TILED' and (img.packed_file or os.path.exists(bpy.path.abspath(img.filepath)))
        feeds_base = any(l.to_socket.name in ("Color", "A", "B") or l.to_node.type in ("MIX", "HUE_SAT", "BSDF_PRINCIPLED") and l.to_socket.name == "Base Color" for l in n.outputs["Color"].links)
        if mat.name == "M_Ais_Skin" and n.name == "Image Texture.002":
            n.image = TILE; continue
        if not usable: nt.nodes.remove(n)
    bs = next((x for x in nt.nodes if x.type == "BSDF_PRINCIPLED"), None)
    if bs and mat.name == "M_Ais_Skin":
        for sock in ("Metallic", "Roughness", "Normal"):
            for l in list(bs.inputs[sock].links): nt.links.remove(l)
        bs.inputs["Metallic"].default_value = 0.0; bs.inputs["Roughness"].default_value = 0.55
        out = next(x for x in nt.nodes if x.type == "OUTPUT_MATERIAL")
        for l in list(out.inputs["Displacement"].links): nt.links.remove(l)
# procedural fabric colours (noise / mix nodes) don't survive glTF: flatten them to their main colour
for mat in bpy.data.materials:
    if not mat.node_tree or mat.name == "M_Ais_Skin": continue
    nt = mat.node_tree; bs = next((x for x in nt.nodes if x.type == "BSDF_PRINCIPLED"), None)
    if not bs or not bs.inputs["Base Color"].is_linked: continue
    src = bs.inputs["Base Color"].links[0].from_node
    if src.type == "TEX_IMAGE": continue
    if src.type == "HUE_SAT" and src.inputs["Color"].is_linked and src.inputs["Color"].links[0].from_node.type == "TEX_IMAGE":
        nt.links.new(src.inputs["Color"].links[0].from_node.outputs["Color"], bs.inputs["Base Color"]); print("eye texture direct", mat.name); continue
    col = None
    if src.type == "MIX" and not src.inputs[6].is_linked: col = tuple(src.inputs[6].default_value)
    elif src.type == "MIX" and src.inputs[6].is_linked and src.inputs[6].links[0].from_node.type == "VALTORGB":
        col = tuple(src.inputs[6].links[0].from_node.color_ramp.elements[-1].color)
    if col is None: col = (0.01, 0.007, 0.006, 1.0)
    for l in list(bs.inputs["Base Color"].links): nt.links.remove(l)
    bs.inputs["Base Color"].default_value = col
    for l in list(bs.inputs["Normal"].links): nt.links.remove(l)
    print("flattened", mat.name, tuple(round(c, 3) for c in col[:3]))
# curated actions only; renamed to the game clip names
keep = {}
for game, src in CLIPS.items():
    a = bpy.data.actions.get(src)
    if a: keep[a.name] = game
for a in list(bpy.data.actions):
    if a.name not in keep: bpy.data.actions.remove(a)
for a in list(bpy.data.actions):
    if a.name in keep: a.name = keep[a.name]; a.use_fake_user = True
ad = rig.animation_data
for tr in list(ad.nla_tracks): ad.nla_tracks.remove(tr)
ad.action = bpy.data.actions["Stand"]; ad.action_slot = ad.action.slots[0]
sc.frame_set(1)
for o in sc.objects: o.select_set(o in keep_meshes or o == rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_apply=True,
                          export_def_bones=True, export_animations=True, export_animation_mode='ACTIONS',
                          export_force_sampling=True, export_frame_step=2, export_optimize_animation_size=True,
                          export_anim_slide_to_zero=True, export_bake_animation=False,
                          export_draco_mesh_compression_enable=False, export_draco_mesh_compression_level=7,
                          export_yup=True, export_materials='EXPORT', export_image_format='WEBP')
print("EXPORTED", OUT, round(os.path.getsize(OUT) / 1024), "KB", "meshes", len(keep_meshes), "clips", sorted(keep.values()))
