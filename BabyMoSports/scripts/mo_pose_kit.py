"""Pose toolkit for Baby Mo (Rigify rig 'rig'): FK limbs aimed by world direction, body turns, finger curls,
face expressions borrowed from Mo's own face actions, auto-grounding, sport props, fixed sprite camera.
World frame: Mo faces -Y, his right hand is on -X, Z is up, feet on z = 0."""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Quaternion

R = math.radians
FWD, BACK, UP, DOWN = Vector((0, -1, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), Vector((0, 0, -1))
RIGHT, LEFT = Vector((-1, 0, 0)), Vector((1, 0, 0))      # Mo's own right / left
def v(*a): return Vector(a).normalized()

class Kit:
    def __init__(self, blend):
        bpy.ops.wm.open_mainfile(filepath=blend)
        self.sc = bpy.context.scene
        self.rig = bpy.data.objects["rig"]; self.P = self.rig.pose.bones
        self.k = self.rig.scale.x
        for o in bpy.data.objects:
            if o.name.startswith(("WGT", "cs_")) or o.name == "Safezone": o.hide_render = True
        self.meshes = [o for o in bpy.data.collections["CHARACTER"].objects if o.type == 'MESH']
        if self.rig.animation_data:
            for tr in list(self.rig.animation_data.nla_tracks): self.rig.animation_data.nla_tracks.remove(tr)
        self.props = {}
        self.FACE_SKIP = None

    # ------------------------------------------------------------ basics
    def upd(self): bpy.context.view_layer.update()
    def reset(self):
        ad = self.rig.animation_data
        if ad: ad.action = None
        for pb in self.P:
            pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
        for s in "LR":
            self.P[f"upper_arm_parent.{s}"]["IK_FK"] = 1.0
            self.P[f"thigh_parent.{s}"]["IK_FK"] = 1.0
        self.P["torso"]["neck_follow"] = 1.0; self.P["torso"]["head_follow"] = 1.0
        self.upd()

    def _set(self, name, N):
        self.P[name].matrix = N; self.upd()

    def aim(self, name, d, twist=0.0):
        """Point the bone's length (local +Y) along world direction d, rotating about its head; optional twist."""
        pb = self.P[name]; M = pb.matrix.copy(); head = M.translation.copy()
        y = M.to_3x3().col[1].normalized(); q = y.rotation_difference(Vector(d).normalized())
        N = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ M
        if twist: N = N @ Matrix.Rotation(R(twist), 4, 'Y')
        self._set(name, N)

    def turn(self, name, axis, deg):
        """Rotate the bone about a world axis through its head."""
        pb = self.P[name]; M = pb.matrix.copy(); head = M.translation.copy()
        N = Matrix.Translation(head) @ Matrix.Rotation(R(deg), 4, Vector(axis)) @ Matrix.Translation(-head) @ M
        self._set(name, N)

    def twist(self, name, deg):
        pb = self.P[name]; self._set(name, pb.matrix.copy() @ Matrix.Rotation(R(deg), 4, 'Y'))

    def arm(self, side, upper, fore, hand=None, twist=0.0, htwist=0.0):
        self.aim(f"upper_arm_fk.{side}", upper, twist)
        self.aim(f"forearm_fk.{side}", fore)
        if hand is not None: self.aim(f"hand_fk.{side}", hand, htwist)

    def leg(self, side, thigh, shin, foot="flat", toe_out=8.0, heel_up=0.0):
        """foot='flat' keeps the sole level (rest orientation, turned out by toe_out deg, heel raised by heel_up deg)."""
        self.aim(f"thigh_fk.{side}", thigh); self.aim(f"shin_fk.{side}", shin)
        if foot == "flat":
            pb = self.P[f"foot_fk.{side}"]; head = pb.matrix.translation.copy()
            rest = self.rig.data.bones[f"foot_fk.{side}"].matrix_local.to_3x3()
            rot = Matrix.Rotation(R(toe_out if side == "L" else -toe_out), 3, 'Z') @ Matrix.Rotation(R(-heel_up), 3, 'X') @ rest
            N = rot.to_4x4(); N.translation = head; self._set(f"foot_fk.{side}", N)
        elif foot is not None:
            self.aim(f"foot_fk.{side}", foot)

    def hand_to(self, side, shaft):
        """Turn the fist so a held racket points along `shaft`: local Z = shaft, fingers (Y) stay close to the forearm."""
        fa = self.bone_axes(f"forearm_fk.{side}")[1]
        z = Vector(shaft).normalized(); y = (fa - z * fa.dot(z))
        if y.length < 1e-4: y = Vector((0, 0, 1)) - z * z.z
        y.normalize(); x = y.cross(z)
        pb = self.P[f"hand_fk.{side}"]; head = pb.matrix.translation.copy()
        N = Matrix(((x.x, y.x, z.x, 0), (x.y, y.y, z.y, 0), (x.z, y.z, z.z, 0), (0, 0, 0, 1))); N.translation = head
        self._set(f"hand_fk.{side}", N)

    def body(self, twist=0.0, lean=0.0, side=0.0, chest_twist=0.0, chest_lean=0.0, head_turn=0.0, head_tilt=0.0, head_nod=0.0):
        """twist: whole torso about Z (+ turns Mo toward his left); lean: forward(+)/back; side: bend toward his right(+).
        chest_*: extra on the upper body only; head_*: look left/right, tilt, nod down(+)."""
        if twist: self.turn("torso", UP, twist)
        if lean: self.turn("torso", LEFT, -lean)
        if side: self.turn("torso", FWD, side)
        if chest_twist: self.turn("chest", UP, chest_twist)
        if chest_lean: self.turn("chest", LEFT, -chest_lean)
        if head_turn: self.turn("head", UP, head_turn)
        if head_nod: self.turn("head", LEFT, -head_nod)
        if head_tilt: self.turn("head", FWD, head_tilt)

    def fingers(self, side, curl=0.0, thumb=0.0, spread=0.0):
        for f in ("f_index", "f_middle", "f_ring", "f_pinky"):
            for i in (1, 2, 3):
                pb = self.P.get(f"{f}.0{i}.{side}")
                if pb: pb.rotation_quaternion = Quaternion((1, 0, 0), R(curl * (0.8 if i == 1 else 1.0)))
        for i in (2, 3):
            pb = self.P.get(f"thumb.0{i}.{side}")
            if pb: pb.rotation_quaternion = Quaternion((1, 0, 0), R(thumb))
        self.upd()

    # ------------------------------------------------------------ face
    def face(self, action_name):
        """Copy the face-bone pose from one of Mo's face actions (body controls are left as posed)."""
        a = bpy.data.actions.get(action_name)
        if not a: return
        BODY = {"root", "torso", "hips", "chest", "neck", "head", "tweak_spine", "spine_fk", "spine_fk.001", "spine_fk.002", "spine_fk.003"}
        names = set()
        for ly in a.layers:
            for st in ly.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        if fc.data_path.startswith('pose.bones["'):
                            n = fc.data_path.split('"')[1]
                            if n not in BODY and "_fk" not in n and "_ik" not in n and "upper_arm" not in n and "thigh" not in n \
                               and not n.startswith(("f_", "thumb", "hand", "foot", "shoulder", "toe")): names.add(n)
        saved = {n: (self.P[n].location.copy(), self.P[n].rotation_quaternion.copy(), self.P[n].rotation_euler.copy(), self.P[n].scale.copy()) for n in self.P.keys()}
        ad = self.rig.animation_data_create(); ad.action = a
        if a.slots: ad.action_slot = a.slots[0]
        self.sc.frame_set(int(a.frame_range[0])); self.upd()
        face = {n: (self.P[n].location.copy(), self.P[n].rotation_quaternion.copy(), self.P[n].rotation_euler.copy(), self.P[n].scale.copy()) for n in names if n in self.P}
        ad.action = None
        for n, (l, q, e, s) in saved.items():
            pb = self.P[n]; pb.location, pb.rotation_quaternion, pb.rotation_euler, pb.scale = l, q, e, s
        for n, (l, q, e, s) in face.items():
            pb = self.P[n]; pb.location, pb.rotation_quaternion, pb.rotation_euler, pb.scale = l, q, e, s
        self.upd()

    # ------------------------------------------------------------ grounding
    def lowest(self):
        dg = bpy.context.evaluated_depsgraph_get(); z = 1e9
        for o in self.meshes:
            if o.hide_render: continue
            oe = o.evaluated_get(dg); me = oe.to_mesh(); M = o.matrix_world
            for vx in me.vertices: z = min(z, (M @ vx.co).z)
            oe.to_mesh_clear()
        return z

    def ground(self, lift=0.0, shift=(0, 0)):
        """Move the root so the lowest point of Mo touches z = lift (world); shift x/y in world units."""
        dz = lift - self.lowest()
        pb = self.P["root"]; M = pb.matrix.copy()
        M.translation += Vector((shift[0], shift[1], dz)) / self.k
        self._set("root", M)

    # ------------------------------------------------------------ props
    def world_of(self, bone, local=(0, 0, 0)):
        pb = self.P[bone]; return self.rig.matrix_world @ (pb.matrix @ Vector(local))

    def bone_axes(self, bone):
        M3 = (self.rig.matrix_world @ self.P[bone].matrix).to_3x3()
        return [M3.col[i].normalized() for i in range(3)]

    def attach(self, ob, bone):
        """Parent a prop to a deform bone keeping its current world transform."""
        mw = ob.matrix_world.copy()
        ob.parent = self.rig; ob.parent_type = 'BONE'; ob.parent_bone = bone
        self.upd(); ob.matrix_world = mw

    def detach(self, ob):
        mw = ob.matrix_world.copy(); ob.parent = None; ob.matrix_world = mw
