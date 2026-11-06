import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
img=bpy.data.images["Baby_MOD_BABY_BaseColor_New.<UDIM>.jpg"]
print(img.source, [t.number for t in img.tiles] if img.source=='TILED' else None, img.size[:])
img2=img.copy(); img2.source='FILE' if img.source!='TILED' else 'TILED'
img.filepath_raw=sys.argv[2]; 
try:
    img.save_render(sys.argv[2])
except Exception as e: print("ERR",e)
