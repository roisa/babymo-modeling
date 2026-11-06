import bpy, sys
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
sc=bpy.context.scene
print("scene",sc.name,"engine",sc.render.engine,"res",sc.render.resolution_x,sc.render.resolution_y,"units",sc.unit_settings.system,sc.unit_settings.scale_length,"view",sc.view_settings.view_transform,sc.view_settings.look,"cam",sc.camera and sc.camera.name)
def walk(c,d=0):
    print("  "*d+"[C]",c.name,len(c.objects))
    for ch in c.children: walk(ch,d+1)
walk(sc.collection)
for o in sorted([o for o in bpy.data.objects if not o.name.startswith("WGT")],key=lambda o:o.name):
    extra=""
    if o.type=="MESH":
        me=o.data
        bb=[o.matrix_world@Vector(v) for v in o.bound_box]
        mn=Vector((min(v.x for v in bb),min(v.y for v in bb),min(v.z for v in bb)));mx=Vector((max(v.x for v in bb),max(v.y for v in bb),max(v.z for v in bb)))
        extra=f"v={len(me.vertices)} f={len(me.polygons)} min={tuple(round(x,3) for x in mn)} max={tuple(round(x,3) for x in mx)} mats={[m.name if m else None for m in me.materials]} mods={[(m.type,m.name) for m in o.modifiers]} sk={len(me.shape_keys.key_blocks) if me.shape_keys else 0} vg={len(o.vertex_groups)}"
    elif o.type=="LIGHT": extra=f"{o.data.type} E={o.data.energy} col={tuple(round(c,2) for c in o.data.color)} size={getattr(o.data,'size',None)} loc={tuple(round(x,2) for x in o.location)}"
    elif o.type=="CAMERA": extra=f"lens={o.data.lens} type={o.data.type} loc={tuple(round(x,2) for x in o.location)} rot={tuple(round(x,2) for x in o.rotation_euler)}"
    elif o.type=="ARMATURE": extra=f"bones={len(o.data.bones)} {[b.name for b in o.data.bones][:80]}"
    print(o.type,o.name,"parent=",o.parent and o.parent.name,"coll=",[c.name for c in o.users_collection],extra)
print("MATERIALS")
for m in bpy.data.materials:
    if not m.node_tree: print(m.name,"no nodes");continue
    print("--",m.name,"users",m.users)
    for n in m.node_tree.nodes:
        vals={i.name:(tuple(round(x,3) for x in i.default_value) if hasattr(i.default_value,'__len__') else round(i.default_value,3)) for i in n.inputs if hasattr(i,'default_value') and not i.is_linked and i.enabled and i.name in("Base Color","Roughness","Metallic","Subsurface Weight","Subsurface Radius","Subsurface Scale","Coat Weight","Sheen Weight","Specular IOR Level","Emission Strength","Color","Strength","Fac","Scale","Melanin","Transmission Weight","IOR")}
        print("   ",n.type,n.name,getattr(n,'image',None) and n.image.name,vals)
print("IMAGES",[(i.name,i.size[:],i.filepath,i.packed_file is not None) for i in bpy.data.images])
w=sc.world
if w and w.node_tree:
    for n in w.node_tree.nodes: print("WORLD",n.type,[(i.name,getattr(i,'default_value',None) if not hasattr(getattr(i,'default_value',0),'__len__') else tuple(i.default_value)) for i in n.inputs])
print("eevee/cycles", sc.cycles.samples if sc.render.engine=="CYCLES" else sc.eevee.taa_render_samples)
print("actions",[a.name for a in bpy.data.actions])
