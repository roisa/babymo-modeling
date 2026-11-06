import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
m=bpy.data.materials["M_Ais_Eye"]
for l in m.node_tree.links: print(l.from_node.name,l.from_socket.name,"->",l.to_node.name,l.to_socket.name)
for n in m.node_tree.nodes:
    if n.type=="HUE_SAT": print("HSV",[ (i.name, i.default_value) for i in n.inputs if not hasattr(i.default_value,'__len__')])
    if n.type=="MAPPING": print("MAP",[tuple(i.default_value) for i in n.inputs[1:]])
img=bpy.data.images["7ca75d4d2bf3009e0b559af838005d47.jpg"]
img.filepath_raw=sys.argv[2]; img.file_format='PNG'; img.save()
e=bpy.data.objects["Ais_Eyes"]; print("eye uv", [u.name for u in e.data.uv_layers])
m=bpy.data.materials["M_Ais_Skin"]
for l in m.node_tree.links: print("SKIN",l.from_node.name,l.from_socket.name,"->",l.to_node.name,l.to_socket.name)
