import bpy, sys, json
sys.path.insert(0, sys.argv[2])
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
import qa_check
objs = sorted(o.name for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("Ais_") and o.name != "Ais_StudioFloor")
r = qa_check.run(objects=objs, profile="render")
print("QA_PASS", r["pass"]); print("ERRORS", json.dumps(r["errors"], indent=0)[:3000]); print("WARN", json.dumps(r["warnings"], indent=0)[:2500])
tot = 0
for n, m in r["objects"].items():
    t = m.get("tris") or m.get("triangles"); tot += t or 0
    print("OBJ", n, {k: v for k, v in m.items() if k in ("tris", "triangles", "materials", "islands")})
print("TOTAL_TRIS", tot)
