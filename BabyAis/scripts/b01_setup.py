"""BATCH 01 - project setup. Opens the ORIGINAL Baby Mo file read-only, saves a separate Baby Ais
working project, builds the Baby Ais collection layout, renames the reusable assets with the Ais_
prefix, makes Ais-owned copies of every reused material and removes Baby-Mo-only geometry."""
import bpy, sys, os
src, root = sys.argv[1], sys.argv[2]
bpy.ops.wm.open_mainfile(filepath=src)
sc = bpy.context.scene
rig = bpy.data.objects['rig']
print("rig action:", rig.animation_data and rig.animation_data.action and rig.animation_data.action.name)
print("frame", sc.frame_current, sc.frame_start, sc.frame_end)
# ---- rest the rig: no action, identity pose (actions stay in the file as the shared motion library)
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
# ---- broken drivers (modifiers mask_legs / mask_arms no longer exist on any mesh)
removed = 0
for o in bpy.data.objects:
    ad = o.animation_data
    if not ad: continue
    for fc in list(ad.drivers):
        if fc.data_path.startswith('modifiers["mask_'):
            ad.drivers.remove(fc); removed += 1
print("removed broken drivers:", removed)
# ---- collections
def coll(name, parent):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in parent.children: parent.children.link(c)
    return c
geo = coll("GEO Baby Ais", sc.collection)
cb, cf, ch, cc = (coll(n, geo) for n in ("AIS_Body", "AIS_Face", "AIS_Hair", "AIS_Clothing"))
def move(o, c):
    for u in list(o.users_collection): u.objects.unlink(o)
    c.objects.link(o)
rename = {"Body": ("Ais_Body", cb), "Mata": ("Ais_Eyes", cf), "Alis": ("Ais_Brows", cf), "Bulu mata": ("Ais_Lashes", cf),
          "Gigi Atas": ("Ais_TeethUpper", cf), "Gigi bawah": ("Ais_TeethLower", cf), "Lidah": ("Ais_Tongue", cf)}
for old, (new, c) in rename.items():
    o = bpy.data.objects[old]; o.name = new; o.data.name = new; move(o, c)
# Baby Mo's own hair and outfit are NOT reused: Ais gets new geometry for both
for n in ["Rambut", "Baju", "Lengan Panjang", "Saku", "Bintang", "Alas Kaki"]:
    o = bpy.data.objects[n]; me = o.data; bpy.data.objects.remove(o); 
    if me.users == 0: bpy.data.meshes.remove(me)
old = bpy.data.collections.get("GEO Baby Mo")
for c in list(old.children_recursive): bpy.data.collections.remove(c)
bpy.data.collections.remove(old)
rig.name = "Ais_Rig"; rig.data.name = "Ais_Rig"
bpy.data.collections["RIG"].name = "RIG_Ais"
bpy.data.objects["metarig"].name = "Ais_metarig"
bpy.data.objects["Safezone"].hide_render = True; bpy.data.objects["Safezone"].hide_viewport = True
# ---- Ais-owned materials (copies, so Baby Mo's library materials are never edited)
newmat = {}
for o in [o for o in bpy.data.objects if o.name.startswith("Ais_") and o.type == 'MESH']:
    for slot in o.material_slots:
        m = slot.material
        if not m: continue
        if m.name not in newmat:
            base = {"BABY.001": "M_Ais_Skin", "Material": "M_Ais_FaceHairDark", "Material.001": "M_Ais_Tongue",
                    "Material.002": "M_Ais_Teeth", "Material.003": "M_Ais_Eye"}.get(m.name, "M_Ais_" + m.name)
            c = m.copy(); c.name = base; newmat[m.name] = c
        slot.material = newmat[m.name]
print("materials:", {k: v.name for k, v in newmat.items()})
for m in list(bpy.data.materials):
    if m.users == 0: bpy.data.materials.remove(m)
bpy.ops.outliner.orphans_purge(do_recursive=True) if False else None
sc.frame_set(1)
os.makedirs(root + "/checkpoints", exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=root + "/BabyAis_Working.blend", compress=True)
bpy.ops.wm.save_as_mainfile(filepath=root + "/checkpoints/BabyAis_v001_base.blend", compress=True, copy=True)
print("objects:", sorted(o.name for o in bpy.data.objects if not o.name.startswith("WGT")))
print("SAVED v001")
