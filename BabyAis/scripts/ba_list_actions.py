import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
for a in bpy.data.actions:
    if any(t in a.name for t in ("Idle", "Locomotion", "Wave", "Nodding", "Turn", "Face_Happy_1", "Face_Surprised", "Face_Sad_1", "Blink", "Mouth_Idle", "Gesture_Lets", "Face_Cheeky_1")):
        print(a.name, tuple(round(f) for f in a.frame_range), "slots", [s.identifier for s in a.slots], "users", a.users)
