"""Usage: ba_render_views.py BLEND OUTDIR SCRIPTSDIR -- tag:az:tz:dist:elev:w:h[:samples] ...  (hides named objects via HIDE=a,b)"""
import bpy, sys, os
argv=sys.argv; i=argv.index('--')
blend,out,sd=argv[i-3:i] if False else (argv[1],argv[2],argv[3])
sys.path.insert(0,sd); import ba_common as C
bpy.ops.wm.open_mainfile(filepath=blend)
sc=bpy.context.scene; sc.frame_set(sc.frame_current)
for o in bpy.data.objects:
    if o.name.startswith(("WGT", "cs_")): o.hide_render = True
    if o.name in ("Safezone",) or o.name in os.environ.get("HIDE","").split(","): o.hide_render=True
os.makedirs(out,exist_ok=True)
for spec in argv[i+1:]:
    p=spec.split(':'); tag=p[0]; az,tz,dist,elev=map(float,p[1:5]); w,h=int(p[5]),int(p[6]); s=int(p[7]) if len(p)>7 else 24
    tx=float(os.environ.get("TX","0"))
    C.render_view(f"{out}/{tag}.png",az,target=(tx,0,tz),dist=dist,elev_deg=elev,res=(w,h),samples=s)
    print("RENDERED",tag)
