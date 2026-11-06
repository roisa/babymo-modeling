import bpy, sys, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
rig=bpy.data.objects['rig']; rig.data.pose_position='REST'
dg=bpy.context.evaluated_depsgraph_get()
b=bpy.data.objects['Body']
for m in b.modifiers:
    if m.type=='SUBSURF': m.show_viewport=False
dg.update()
be=b.evaluated_get(dg); me=be.to_mesh()
mw=b.matrix_world
verts=[mw@v.co for v in me.vertices]
bvh=BVHTree.FromPolygons(verts,[p.vertices[:] for p in me.polygons])
vg={g.index:g.name for g in b.vertex_groups}
def grp(prefix):
    out=[]
    for v in b.data.vertices:
        for g in v.groups:
            if vg[g.group].startswith(prefix) and g.weight>0.5: out.append(mw@b.data.vertices[v.index].co); break
    return out
def bbx(pts): return [tuple(round(f(p[i] for p in pts),4) for i in range(3)) for f in (min,max)]
print("ear L",bbx(grp('DEF-ear.L')))
print("brow L",bbx(grp('DEF-brow.T.L')))
print("eye master L",bbx(grp('DEF-eye_master.L')))
print("jaw/chin",bbx(grp('DEF-chin')))
print("head(spine.006)",bbx(grp('DEF-spine.006')))
print("neck(spine.004/5)",bbx(grp('DEF-spine.005')),bbx(grp('DEF-spine.004')))
C=Vector((0,0.012,0.47))
for th in [0,20,40,60,80,90,100,110,120]:
    row=[]
    for a in [0,30,60,90,120,150,180]:
        # alpha: 0=back(+Y), 90=char left(+X), 180=front(-Y)
        d=Vector((math.sin(math.radians(th))*math.sin(math.radians(a)), math.sin(math.radians(th))*math.cos(math.radians(a)), math.cos(math.radians(th))))
        hit=bvh.ray_cast(C+d*0.4,-d)
        row.append(round((hit[0]-C).length,3) if hit[0] else None)
    print("theta",th,row)
for z in [0.30,0.32,0.34,0.36,0.38,0.40]:
    row=[]
    for a in [0,45,90,135,180]:
        d=Vector((math.sin(math.radians(a)),math.cos(math.radians(a)),0)); o=Vector((0,0.0,z))
        hit=bvh.ray_cast(o+d*0.3,-d); row.append(round((hit[0]-o).length,3) if hit[0] else None)
    print("z",z,"horiz r",row)
print("total bbox", bbx(verts))
