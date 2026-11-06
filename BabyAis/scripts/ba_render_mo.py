import bpy, sys, time
sys.path.insert(0, sys.argv[-1])
import ba_common as C
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
sc=bpy.context.scene
sc.frame_set(1)
for o in bpy.data.objects:
    if o.name=="Safezone": o.hide_render=True
out=sys.argv[2]
for az,tag in [(0,"front"),(90,"side"),(180,"back"),(35,"34")]:
    t=time.time(); C.render_view(f"{out}/mo_{tag}.png", az, target=(0,0,0.3), dist=2.0, samples=16, res=(500,640)); print("rendered",tag,round(time.time()-t,1))
