import bpy, sys
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
rig=bpy.data.objects['rig']; print("rig",rig.location[:],rig.scale[:],rig.rotation_euler[:], "pose_position", rig.data.pose_position)
b=bpy.data.objects['Body']; print("body mw scale",b.matrix_world.to_scale()[:], "parent_type", b.parent_type)
me=b.data
print("shape keys",[ (k.name,k.value) for k in me.shape_keys.key_blocks])
print("uv",[u.name for u in me.uv_layers])
vg={g.index:g.name for g in b.vertex_groups}
from collections import defaultdict
best=defaultdict(list)
for v in me.vertices:
    if not v.groups: continue
    g=max(v.groups,key=lambda g:g.weight)
    best[vg[g.group]].append(v.co.copy())
def bb(pts):
    mn=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)));mx=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
    return tuple(round(x,3) for x in mn),tuple(round(x,3) for x in mx)
for k in sorted(best): 
    if len(best[k])>20: print(k,len(best[k]),bb(best[k]))
mw=b.matrix_world
print("body local->world sample", (mw@me.vertices[0].co)[:], me.vertices[0].co[:])
for n in ['Mata','Alis','Bulu mata','Rambut','Baju','Lengan Panjang','Saku','Alas Kaki']:
    o=bpy.data.objects[n]; print(n, [m.name for m in o.modifiers], [(m.type, getattr(m,'object',None) and m.object.name) for m in o.modifiers])
for bn in ['DEF-spine.006','DEF-spine.005','DEF-spine.004','ORG-eye.L','DEF-jaw','DEF-upper_arm.L','DEF-forearm.L','DEF-hand.L','DEF-thigh.L','DEF-shin.L','DEF-foot.L','DEF-toe.L','DEF-spine','DEF-spine.003','DEF-ear.L']:
    bo=rig.data.bones.get(bn)
    if bo: print(bn,"head",tuple(round(x,3) for x in rig.matrix_world@bo.head_local),"tail",tuple(round(x,3) for x in rig.matrix_world@bo.tail_local))
print("DEF bones",len([x for x in rig.data.bones if x.name.startswith('DEF')]))
print([x.name for x in rig.data.bones if x.use_deform][:400])
