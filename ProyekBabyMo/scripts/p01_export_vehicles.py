"""Export every toy vehicle as its own game-ready GLB with real moving parts.
For each vehicle: build pivot empties (named PV_*) at the true hinge points, re-parent the parts that move,
bake modifiers to meshes, join static meshes per (pivot, material) to keep draw calls low, centre the
vehicle at the origin, export Draco-compressed GLB.  Wheels get one PV_Wheel_* pivot each (spin about X).
Usage: python p01_export_vehicles.py VEHICLES.blend OUTDIR"""
import bpy, sys, os, re, json, math
from mathutils import Vector, Matrix

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
V = Vector

# pivot spec per vehicle: (pivot name, parent pivot or None, location (vehicle-local), object-name regex, axis note)
SPECS = {
    "Excavator": [
        ("PV_Swing", None, (0, 0.05, 0.42), r"^Exc_(House|Counterweight|EngineHood|EngineGrille|Exhaust|Cab_.*|BoomCyl.*)$"),
        ("PV_Boom", "PV_Swing", (-0.2, -0.28, 0.82), r"^Exc_(BoomPivot|Boom1|Boom2|BoomKnee|StickCyl.*)$"),
        ("PV_Stick", "PV_Boom", (-0.2, -1.28, 1.6), r"^Exc_(ElbowPin|Stick|BucketCyl.*)$"),
        ("PV_Bucket", "PV_Stick", (-0.2, -1.62, 0.62), r"^Exc_(Bucket|Tooth\d+)$"),
    ],
    "DumpTruck": [
        ("PV_Bed", None, (0, 1.16, 0.86), r"^Dump_(Bed.*|Rib.*|Canopy|Rock\d+)$"),
    ],
    "Bulldozer": [
        ("PV_Blade", None, (0, 0.1, 0.4), r"^Doz_(Blade.*|Tooth\d+|PushArm.*|LiftCyl.*)$"),
    ],
    "CraneTruck": [
        ("PV_Swing", None, (0, 0.65, 0.7), r"^Crane_(Superstructure|OpCab_.*|LiftCyl.*)$"),
        ("PV_Boom", "PV_Swing", (-0.16, 0.95, 1.05), r"^Crane_(Boom1|Boom2|BoomFoot|Sheave)$"),
        ("PV_Hook", "PV_Boom", (-0.16, -1.31, 1.65), r"^Crane_(HookBlock|Hook)$"),
    ],
    "CementMixer": [
        ("PV_Drum", None, (0, -0.25, 1.0), r"^Mix_(Drum|DrumRing.*)$"),
    ],
    "WheelLoader": [
        ("PV_Arm", None, (0, -0.2, 1.0), r"^Load_(LiftArm.*|CrossTube|TiltCyl.*|Bucket|Tooth\d+)$"),
    ],
    "RoadRoller": [
        ("PV_Drum", None, (0, -0.72, 0.43), r"^Rol_(Drum|DrumCap.*|DrumHub.*)$"),
    ],
    "Tractor": [],
    "Forklift": [
        ("PV_Forks", None, (0, -0.7, 0.0), r"^Fork_(Upright.*|Tine.*|Carriage|Pallet.*|Box.*)$"),
    ],
    "GarbageTruck": [
        ("PV_Bin", None, (0, 1.4, 0.4), r"^Gar_(Bin.*)$"),
    ],
    "FireTruck": [
        ("PV_LadderSwing", None, (0, 0.95, 1.36), r"^Fire_(LadderTurntable)$"),
        ("PV_Ladder", "PV_LadderSwing", (0, 1.0, 1.44), r"^Fire_(LadderRail.*|Rung\d+)$"),
    ],
}
# extra per-vehicle metadata the game reads (axis + rest notes)
META = {
    "CementMixer": {"PV_Drum": {"axis_tilt_x_deg": -74}},
    "Excavator": {"note": "PV_Swing rotates Z; PV_Boom/PV_Stick/PV_Bucket rotate X"},
}

bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
report = {}
for veh in list(SPECS):
    bpy.ops.wm.open_mainfile(filepath=SRC); sc = bpy.context.scene
    coll = bpy.data.collections[veh]; root = bpy.data.objects[veh + "_Root"]
    origin = root.location.copy()
    # isolate: delete every other vehicle + studio
    for c in list(sc.collection.children):
        if c.name != veh:
            for o in list(c.objects): bpy.data.objects.remove(o)
            bpy.data.collections.remove(c)
    for o in list(sc.collection.objects): bpy.data.objects.remove(o)
    root.location = (0, 0, 0); bpy.context.view_layer.update()
    objs = [o for o in coll.objects if o.type in ('MESH', 'CURVE')]
    # 1) bake modifiers / curves to plain meshes
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        if o.type == 'CURVE':
            no = bpy.data.objects.new(o.name + "_m", me); coll.objects.link(no)
            no.parent = o.parent; no.matrix_world = o.matrix_world.copy()
            nm = o.name; bpy.data.objects.remove(o); no.name = nm
        else:
            o.modifiers.clear(); old = o.data; o.data = me
            if old.users == 0: bpy.data.meshes.remove(old)
    objs = [o for o in coll.objects if o.type == 'MESH']
    # 2) pivots
    piv = {}
    for name, parent, loc, rx in SPECS[veh]:
        e = bpy.data.objects.new(name, None); coll.objects.link(e); e.empty_display_size = 0.15
        e.parent = piv[parent][0] if parent else root
        e.matrix_world = Matrix.Translation(V(loc)); piv[name] = (e, re.compile(rx))
    piv = {k: v for k, v in piv.items()}
    # wheels: group parts named <Prefix>_Wheel<id>_<Part> -> PV_Wheel_<id>
    wheel_groups = {}
    for o in objs:
        m = re.match(r"^(.*?_(?:Rear|Front)?Wheel[A-Za-z]*\d*)_(Tire|Rim|RimDish|Hub|Bolt\d+|Lug\d+[ab])$", o.name)
        if m: wheel_groups.setdefault(m.group(1), []).append(o)
    for gname, parts in wheel_groups.items():
        tire = next(p for p in parts if p.name.endswith("_Tire"))
        e = bpy.data.objects.new("PV_Wheel_" + gname.split("_", 1)[1], None); coll.objects.link(e)
        e.parent = root; e.matrix_world = Matrix.Translation(tire.matrix_world.translation)
        for p in parts:
            mw = p.matrix_world.copy(); p.parent = e; p.matrix_world = mw
    for name, (e, rx) in piv.items():
        for o in objs:
            if rx.match(o.name):
                mw = o.matrix_world.copy(); o.parent = e; o.matrix_world = mw
    # mixer drum pivot tilted to the drum axis so the game spins local Z
    if veh == "CementMixer":
        e = bpy.data.objects["PV_Drum"]; kids = list(e.children); mws = [k.matrix_world.copy() for k in kids]
        e.matrix_world = Matrix.Translation(e.matrix_world.translation) @ Matrix.Rotation(math.radians(-74), 4, 'X')
        for k, mw in zip(kids, mws): k.matrix_world = mw
    bpy.context.view_layer.update()
    # 3) join meshes per (parent, material)
    groups = {}
    for o in [o for o in coll.objects if o.type == 'MESH']:
        mat = o.data.materials[0].name if o.data.materials else "none"
        groups.setdefault((o.parent.name if o.parent else "", mat), []).append(o)
    for (par, mat), lst in groups.items():
        if len(lst) < 2: continue
        act = lst[0]
        with bpy.context.temp_override(active_object=act, selected_editable_objects=lst, object=act):
            bpy.ops.object.join()
        act.name = f"{veh}_{(par or 'Body').replace('PV_', '')}_{mat.replace('M_Toy_', '')}"
    # 4) export
    for o in sc.objects: o.select_set(o.name in coll.all_objects)
    path = f"{OUT}/{veh}.glb"
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=False,
                              export_draco_mesh_compression_enable=False, export_draco_mesh_compression_level=7,
                              export_yup=True, export_materials='EXPORT', export_extras=True)
    tris = sum(len(p.vertices) - 2 for o in coll.objects if o.type == 'MESH' for p in o.data.polygons)
    report[veh] = {"kb": round(os.path.getsize(path) / 1024), "meshes": len([o for o in coll.objects if o.type == 'MESH']),
                   "tris": tris, "pivots": sorted(o.name for o in coll.objects if o.name.startswith("PV_")), "origin": list(origin)}
    print("EXPORTED", veh, report[veh]["kb"], "KB", report[veh]["meshes"], "meshes", tris, "tris")
json.dump(report, open(f"{OUT}/vehicles.json", "w"), indent=1)
