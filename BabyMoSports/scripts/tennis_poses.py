"""Baby Mo - 20 tennis poses rendered as transparent PNG sprites (same camera, scale and ground line for all).
Usage: python tennis_poses.py BABY_MO.blend OUTDIR SCRIPTS_DIR
Env: ONLY=03,05  RES=1200  SAMPLES=48  KEEP=1 (also save each posed .blend)
Each pose sets FK limb directions (world), body turn/lean, the racket direction + string-face direction,
the ball position, Mo's face expression and an optional hop height."""
import bpy, sys, os, math
sys.path.insert(0, sys.argv[3])
from mathutils import Vector
from mo_pose_kit import Kit, v, FWD, BACK, UP, DOWN, RIGHT, LEFT
import tennis_props as TP

BLEND, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
RACKET_SCALE = 1.3
HC = 0.20 * RACKET_SCALE                          # racket head centre along the shaft (world)
CAM = v(-0.47, -0.88, 0.1)                       # toward the camera: strings turned this way read best

def stance(K, width=0.2, bend=0.35, stagger=0.0, heel_up=0.0):
    """Athletic stance: feet apart, knees bent; stagger > 0 puts Mo's left foot forward."""
    for s, sx in (("L", 1), ("R", -1)):
        fwd = bend + (stagger if s == "L" else -stagger)
        K.leg(s, v(sx * width, -fwd, -1), v(sx * width * 0.35, bend * 0.6, -1), heel_up=heel_up)

# ---------------------------------------------------------------- the 20 poses
# Each returns: rk=(shaft dir, string-face dir), ball=None | ("strings", gap) | ("world", xyz) | ("handL", up), face, lift
def p01(K):   # ready position
    stance(K, 0.2, 0.42); K.body(lean=14, head_nod=-8)
    K.arm("R", v(-0.2, -0.45, -1), v(0.4, -1, 0.0))
    K.arm("L", v(0.3, -0.45, -1), v(-0.1, -1, 0.15), v(0.2, -0.9, 0.4))
    return dict(rk=(v(0.85, -0.3, 0.42), CAM), face="Face_Happy_1")
def p02(K):   # split step (little hop)
    stance(K, 0.3, 0.3, heel_up=12); K.body(lean=10)
    K.arm("R", v(-0.25, -0.45, -1), v(0.4, -1, 0.05))
    K.arm("L", v(0.35, -0.45, -1), v(-0.1, -1, 0.2), v(0.2, -0.9, 0.4))
    return dict(rk=(v(0.85, -0.3, 0.45), CAM), face="Face_Determined_1", lift=0.035)
def p03(K):   # run to the ball
    K.leg("L", v(0.05, -0.9, -0.55), v(0, 0.15, -1), foot=v(0, -1, -0.25)); K.leg("R", v(-0.05, 0.45, -1), v(0, 0.95, -0.35), foot=v(0, 0.3, -1))
    K.body(twist=-25, lean=16, head_turn=15)
    K.arm("R", v(-0.3, 0.55, -0.9), v(-0.15, -0.1, -1))
    K.arm("L", v(0.25, -0.75, -0.55), v(0.1, -0.95, 0.5), v(0, -0.9, 0.4))
    return dict(rk=(v(-0.25, -0.9, 0.2), v(-1, 0.1, 0.2)), face="Face_Determined_1", lift=0.03)
def p04(K):   # forehand backswing
    stance(K, 0.24, 0.32, stagger=0.1); K.body(twist=-40, lean=8, head_turn=35)
    K.arm("R", v(-0.75, 0.5, -0.3), v(-0.45, 0.75, 0.3))
    K.arm("L", v(0.25, -1, 0.05), v(0.15, -1, 0.2), v(0.15, -1, 0.25))
    return dict(rk=(v(-0.35, 0.45, 0.8), CAM), face="Face_Determined_1", ball=("world", (-0.32, -0.42, 0.34)))
def p05(K):   # forehand contact
    stance(K, 0.26, 0.3, stagger=0.08); K.body(twist=-8, lean=10, head_turn=-15)
    K.arm("R", v(-0.9, -0.35, -0.25), v(-0.75, -0.65, -0.05))
    K.arm("L", v(0.7, -0.25, -0.45), v(0.45, -0.55, 0.0), v(0.3, -0.7, 0.1))
    return dict(rk=(v(-0.9, -0.3, 0.3), v(-0.05, -1, 0.05)), face="Face_Determined_1", ball=("strings", 0.034))
def p06(K):   # forehand follow-through
    stance(K, 0.24, 0.25, stagger=0.08); K.body(twist=35, lean=4, head_turn=-25)
    K.arm("R", v(0.7, -0.6, 0.1), v(0.75, 0.2, 0.6))
    K.arm("L", v(0.45, -0.25, -0.85), v(0.3, -0.75, 0.15), v(0.0, -0.9, 0.2))
    return dict(rk=(v(0.55, 0.25, 0.8), CAM), face="Face_Happy_2")
def p07(K):   # backhand backswing (one-handed)
    stance(K, 0.24, 0.32, stagger=-0.1); K.body(twist=40, lean=8, head_turn=-40)
    K.arm("R", v(0.75, -0.05, -0.6), v(0.5, 0.55, -0.15))
    K.arm("L", v(0.45, -0.25, -0.6), v(0.0, -0.75, 0.2), v(-0.3, -0.9, 0.2))
    return dict(rk=(v(0.85, 0.3, 0.42), CAM), face="Face_Determined_1", ball=("world", (0.3, -0.45, 0.3)))
def p08(K):   # backhand contact
    stance(K, 0.26, 0.3, stagger=-0.08); K.body(twist=8, lean=10, head_turn=15)
    K.arm("R", v(0.85, -0.45, -0.25), v(0.75, -0.65, -0.05))
    K.arm("L", v(-0.65, 0.55, -0.45), v(-0.55, 0.65, 0.0), v(-0.5, 0.7, 0.1))
    return dict(rk=(v(0.9, -0.3, 0.3), v(0.05, -1, 0.05)), face="Face_Determined_1", ball=("strings", 0.034))
def p09(K):   # backhand follow-through
    stance(K, 0.24, 0.25, stagger=-0.08); K.body(twist=-25, lean=4, head_turn=20)
    K.arm("R", v(0.0, -0.6, 0.8), v(-0.4, -0.25, 0.9))
    K.arm("L", v(-0.65, 0.45, -0.6), v(-0.6, 0.65, -0.25), v(-0.5, 0.8, 0.0))
    return dict(rk=(v(-0.65, 0.2, 0.7), CAM), face="Face_Happy_2")
def p10(K):   # bounce the ball before serving
    stance(K, 0.15, 0.14); K.body(twist=-20, lean=14, head_nod=22)
    K.arm("L", v(0.15, -0.5, -1), v(0.05, -1, -0.45), v(0, -0.7, -0.9))
    K.arm("R", v(-0.25, 0.1, -1), v(-0.15, -0.45, -0.9))
    return dict(rk=(v(-0.45, -0.85, 0.0), v(-0.6, 0.2, 0.8)), face="Face_Happy_1", ball=("world", (0.06, -0.25, 0.024)))
def p11(K):   # serve: ball toss
    stance(K, 0.17, 0.2, stagger=0.12); K.body(twist=-15, lean=-4, head_nod=-16, head_turn=15)
    K.arm("L", v(0.5, -0.35, 0.8), v(0.4, -0.3, 0.85), v(0.35, -0.25, 0.9))
    K.arm("R", v(-0.45, 0.5, -0.75), v(-0.35, 0.8, -0.3))
    return dict(rk=(v(-0.3, 0.55, 0.75), CAM), face="Face_Determined_1", ball=("handL", 0.09))
def p12(K):   # serve: trophy position
    stance(K, 0.22, 0.48, stagger=0.12); K.body(twist=-18, lean=-8, head_nod=-14, head_turn=12)
    K.arm("L", v(0.55, -0.35, 0.75), v(0.45, -0.3, 0.85), v(0.4, -0.25, 0.9))
    K.arm("R", v(-1, 0.2, 0.15), v(-0.15, 0.2, 1))
    return dict(rk=(v(-0.25, 0.35, 0.9), CAM), face="Face_Determined_1", ball=("world", (0.3, -0.25, 0.88)))
def p13(K):   # serve: contact at full reach
    stance(K, 0.13, 0.06, heel_up=20); K.body(twist=-10, lean=-5, side=-8, head_nod=-14)
    K.arm("R", v(-0.5, -0.2, 0.85), v(-0.4, -0.3, 0.85))
    K.arm("L", v(0.45, -0.45, -0.5), v(-0.35, -0.85, 0.2), v(-0.55, -0.75, 0.2))
    return dict(rk=(v(-0.3, -0.35, 0.9), CAM), face="Face_Determined_1", ball=("strings", 0.034), lift=0.03)
def p14(K):   # serve: follow-through
    K.leg("L", v(0.15, -0.5, -1), v(0.05, 0.3, -1)); K.leg("R", v(-0.2, 0.6, -1), v(-0.1, 0.95, -0.45), foot=v(0, 0.25, -1))
    K.body(twist=30, lean=26, head_nod=-18)
    K.arm("R", v(0.35, -0.75, -0.55), v(0.8, -0.35, -0.3))
    K.arm("L", v(0.5, -0.3, -0.7), v(0.2, -0.85, 0.1), v(-0.2, -0.9, 0.1))
    return dict(rk=(v(0.8, 0.15, -0.5), CAM), face="Face_Happy_2")
def p15(K):   # forehand volley at the net
    K.leg("L", v(0.12, -0.7, -1), v(0.05, 0.3, -1)); K.leg("R", v(-0.25, 0.3, -1), v(-0.1, 0.6, -0.8))
    K.body(twist=-12, lean=16)
    K.arm("R", v(-0.85, -0.4, -0.25), v(-0.55, -0.8, 0.2))
    K.arm("L", v(0.6, -0.55, -0.35), v(0.3, -0.9, 0.2), v(0.2, -0.9, 0.3))
    return dict(rk=(v(-0.65, -0.35, 0.65), v(-0.15, -1, 0.1)), face="Face_Surprised_1", ball=("strings", 0.034))
def p16(K):   # backhand volley at the net
    K.leg("R", v(-0.12, -0.7, -1), v(-0.05, 0.3, -1)); K.leg("L", v(0.25, 0.3, -1), v(0.1, 0.6, -0.8))
    K.body(twist=14, lean=16)
    K.arm("R", v(0.65, -0.65, -0.25), v(0.55, -0.75, 0.25))
    K.arm("L", v(-0.6, 0.2, -0.6), v(-0.4, -0.6, 0.1), v(-0.3, -0.8, 0.2))
    return dict(rk=(v(0.65, -0.35, 0.65), v(0.15, -1, 0.1)), face="Face_Surprised_1", ball=("strings", 0.034))
def p17(K):   # overhead smash (jumping)
    K.leg("L", v(0.15, -0.65, -1), v(0.1, 0.6, -1), foot=v(0.1, -0.6, -1)); K.leg("R", v(-0.15, 0.25, -1), v(-0.05, 0.9, -0.45), foot=v(0, 0.3, -1))
    K.body(twist=-18, lean=-10, head_nod=-14, head_turn=10)
    K.arm("L", v(0.6, -0.5, 0.65), v(0.5, -0.5, 0.7), v(0.45, -0.5, 0.75))
    K.arm("R", v(-1, 0.1, 0.4), v(-0.3, 0.3, 1))
    return dict(rk=(v(-0.3, 0.45, 0.85), CAM), face="Face_Determined_1", ball=("world", (0.28, -0.45, 0.9)), lift=0.07)
def p18(K):   # lunge for a wide ball
    K.leg("R", v(-0.85, -0.25, -0.6), v(-0.15, 0.05, -1)); K.leg("L", v(0.55, 0.1, -0.85), v(0.6, 0.1, -0.8), foot=v(0.35, -0.55, -0.7))
    K.body(twist=-15, side=16, lean=12, head_turn=-15)
    K.arm("R", v(-0.9, -0.3, -0.4), v(-0.7, -0.6, -0.3))
    K.arm("L", v(0.8, 0.2, 0.15), v(0.6, 0.1, 0.5), v(0.5, 0.0, 0.6))
    return dict(rk=(v(-0.85, -0.3, -0.1), v(-0.05, -1, 0.15)), face="Face_Determined_1", ball=("strings", 0.034))
def p19(K):   # jump for joy - point won!
    K.leg("L", v(0.15, -0.55, -1), v(0.1, 0.8, -0.75), foot=v(0.1, 0.2, -1)); K.leg("R", v(-0.15, -0.3, -1), v(-0.1, 0.85, -0.65), foot=v(-0.1, 0.2, -1))
    K.body(lean=-6, head_nod=-12)
    K.arm("R", v(-0.6, -0.15, 0.8), v(-0.5, -0.2, 0.85))
    K.arm("L", v(0.7, -0.15, 0.7), v(0.6, -0.15, 0.8), v(0.45, -0.15, 0.9))
    K.fingers("L", curl=85, thumb=40)
    return dict(rk=(v(-0.45, -0.2, 0.9), CAM), face="Face_Happy_3", lift=0.09)
def p20(K):   # oops - missed it
    stance(K, 0.15, 0.1); K.body(lean=4, head_tilt=10, head_turn=25)
    K.arm("R", v(-0.35, -0.2, -1), v(-0.2, -0.45, -1))
    K.arm("L", v(0.55, -0.6, -0.1), v(-0.25, -0.15, 1), v(-0.4, 0.1, 0.8))
    return dict(rk=(v(-0.45, -0.85, -0.1), v(-0.6, 0.2, 0.8)), face="Face_Sad_1", ball=("world", (0.38, 0.35, 0.024)))

POSES = [
    ("01_ready", "Siap!", "Ready position", p01), ("02_split_step", "Lompat kecil", "Split step", p02),
    ("03_run", "Lari ke bola", "Run to the ball", p03), ("04_forehand_backswing", "Forehand: ayun ke belakang", "Forehand backswing", p04),
    ("05_forehand_contact", "Forehand: pukul!", "Forehand contact", p05), ("06_forehand_follow", "Forehand: ayunan lanjut", "Forehand follow-through", p06),
    ("07_backhand_backswing", "Backhand: ayun ke belakang", "Backhand backswing", p07), ("08_backhand_contact", "Backhand: pukul!", "Backhand contact", p08),
    ("09_backhand_follow", "Backhand: ayunan lanjut", "Backhand follow-through", p09), ("10_serve_bounce", "Pantulkan bola", "Bounce before serve", p10),
    ("11_serve_toss", "Servis: lempar bola", "Serve toss", p11), ("12_serve_trophy", "Servis: posisi piala", "Serve trophy position", p12),
    ("13_serve_contact", "Servis: pukul!", "Serve contact", p13), ("14_serve_follow", "Servis: ayunan lanjut", "Serve follow-through", p14),
    ("15_volley_forehand", "Voli forehand", "Forehand volley", p15), ("16_volley_backhand", "Voli backhand", "Backhand volley", p16),
    ("17_smash", "Smes!", "Overhead smash", p17), ("18_lunge", "Menjangkau bola", "Lunge for a wide ball", p18),
    ("19_celebrate", "Hore, menang poin!", "Jump for joy", p19), ("20_oops", "Yah, meleset", "Oops, missed", p20),
]

def main():
    only = [s for s in os.environ.get("ONLY", "").split(",") if s]
    res, samples = int(os.environ.get("RES", "1200")), int(os.environ.get("SAMPLES", "48"))
    K = Kit(BLEND)
    coll = bpy.data.collections.new("TennisProps"); K.sc.collection.children.link(coll)
    racket = TP.build_racket(coll); ball = TP.build_ball(coll)
    TP.setup_render(K.sc, res=res, samples=samples, ortho=float(os.environ.get("ORTHO", "1.12")), target=(0, 0, float(os.environ.get("TZ", "0.46"))))
    lines = []; snaps = []
    for name, id_title, en_title, fn in POSES:
        if only and name[:2] not in only: continue
        K.reset()
        spec = fn(K) or {}
        shaft, face = spec["rk"]
        K.hand_to("R", shaft)
        K.fingers("R", curl=75, thumb=35)
        if spec.get("face"): K.face(spec["face"])
        K.ground(lift=spec.get("lift", 0.0))
        hx, hy, hz = K.bone_axes("DEF-hand.R")
        L = K.rig.matrix_world.to_scale().x * K.rig.data.bones["DEF-hand.R"].length
        at = K.world_of("DEF-hand.R") + hy * L * 0.6
        TP.place(racket, at, shaft, face); racket.scale = (RACKET_SCALE,) * 3
        b = spec.get("ball"); show = b is not None
        ball.hide_render = not show
        for ch in ball.children: ch.hide_render = not show
        if show:
            kind, p = b
            if kind == "world": pos = Vector(p)
            elif kind == "handL": pos = K.world_of("DEF-hand.L") + K.bone_axes("DEF-hand.L")[1] * 0.04 + Vector((0, 0, p))
            else:
                f = Vector(face).normalized(); y = Vector(shaft).normalized(); f = (f - y * f.dot(y)).normalized()
                pos = at + y * HC + f * p
            TP.place(ball, pos, UP, LEFT)
        K.sc.render.filepath = f"{OUT}/BabyMo_Tennis_{name}.png"
        bpy.ops.render.render(write_still=True)
        if os.environ.get("KEEP"): bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/BabyMo_Tennis_{name}.blend", copy=True, compress=True)
        print("POSE", name, "|", id_title, "|", en_title); lines.append(f"{name},{id_title},{en_title}")
        snaps.append((int(name[:2]), {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(), pb.rotation_euler.copy(), pb.scale.copy()) for pb in K.P},
                      racket.matrix_world.copy(), ball.matrix_world.copy(), show))
    lib = os.environ.get("SAVE_LIB")
    if lib:   # one editable file: frame N = pose N (all bones + racket + ball keyed, constant interpolation)
        K.reset(); ad = K.rig.animation_data_create(); act = bpy.data.actions.new("Tennis_Poses"); act.use_fake_user = True; ad.action = act
        for f, bones, rm, bm_, show in snaps:
            for n, (l, q, e, sc_) in bones.items():
                pb = K.P[n]; pb.location, pb.rotation_quaternion, pb.rotation_euler, pb.scale = l, q, e, sc_
                for path in ("location", "rotation_quaternion", "rotation_euler", "scale"): pb.keyframe_insert(path, frame=f)
            racket.matrix_world = rm; ball.matrix_world = bm_
            for ob in (racket, ball): ob.keyframe_insert("location", frame=f); ob.keyframe_insert("rotation_euler", frame=f); ob.keyframe_insert("scale", frame=f)
            for ob in [ball] + list(ball.children): ob.hide_render = not show; ob.keyframe_insert("hide_render", frame=f)
        try:
            for ly in act.layers:
                for st in ly.strips:
                    for cb in st.channelbags:
                        for fc in cb.fcurves:
                            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
        except Exception as e: print("interp", e)
        K.sc.frame_start, K.sc.frame_end = 1, len(snaps); K.sc.frame_set(1)
        bpy.ops.wm.save_as_mainfile(filepath=lib, compress=True); print("SAVED LIB", lib)
    if not only:
        open(f"{OUT}/poses.csv", "w").write("file,judul_id,title_en\n" + "\n".join(f"BabyMo_Tennis_{l}" for l in lines) + "\n")

main()
