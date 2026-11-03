# Scripted GUI scenarios for tear-off menus/panels. Run with --enable-event-simulate.
import bpy, sys, os, traceback

args = sys.argv[sys.argv.index("--") + 1:]
SCEN, OUT = args[0], args[1]
SHOTS = os.path.join(OUT, "shots")
LOG = open(os.path.join(OUT, f"{SCEN}.log"), "w", buffering=1)

def log(*a):
    s = " ".join(str(x) for x in a)
    LOG.write(s + "\n"); LOG.flush(); print("SIM:", s, flush=True)

results = []
def check(name, ok, info=""):
    results.append((name, bool(ok)))
    log(("PASS " if ok else "FAIL ") + name, info)

win = lambda: bpy.context.window_manager.windows[0]
scr = lambda: win().screen

def area(t="VIEW_3D", idx=0):
    return [a for a in scr().areas if a.type == t][idx]
def region_of(a, t="WINDOW"):
    return [r for r in a.regions if r.type == t][0]
def override(t="VIEW_3D", rt="WINDOW", idx=0):
    a = area(t, idx)
    return dict(window=win(), screen=scr(), area=a, region=region_of(a, rt))

def move(x, y):
    win().event_simulate(type="MOUSEMOVE", value="NOTHING", x=int(x), y=int(y))
def press(x, y, t="LEFTMOUSE"):
    win().event_simulate(type=t, value="PRESS", x=int(x), y=int(y))
def release(x, y, t="LEFTMOUSE"):
    win().event_simulate(type=t, value="RELEASE", x=int(x), y=int(y))
def key(t, x, y, ch=None, val="PRESS"):
    kw = {"unicode": ch} if ch and val == "PRESS" else {}
    win().event_simulate(type=t, value=val, x=int(x), y=int(y), **kw)

W = 0.25
def click(x, y):
    move(x, y); yield W
    move(x, y); yield W
    press(x, y); yield 0.05
    release(x, y); yield W
def dblclick(x, y):
    move(x, y); yield W
    move(x, y); yield W
    press(x, y); yield 0.02
    release(x, y); yield 0.02
    win().event_simulate(type="LEFTMOUSE", value="DOUBLE_CLICK", x=int(x), y=int(y)); yield 0.02
    release(x, y); yield W
def type_key(t, x, y, ch=None):
    key(t, x, y, ch); yield 0.03
    key(t, x, y, None, "RELEASE"); yield 0.1

def shot(name):
    p = os.path.join(SHOTS, f"{SCEN}-{name}.png")
    with bpy.context.temp_override(window=win(), screen=scr()):
        bpy.ops.screen.screenshot(filepath=p)
    log("shot", p)
    yield 0.1

import numpy as np
FRAME = {}
def grab(name):
    """Screenshot into FRAME[name] as a height x width x 4 array, origin bottom-left (event coords)."""
    yield 0.35
    yield from shot(name)
    p = os.path.join(SHOTS, f"{SCEN}-{name}.png")
    img = bpy.data.images.load(p, check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(a)
    FRAME[name] = a.reshape(h, w, 4)[:, :, :3]
    bpy.data.images.remove(img)
    yield 0.02
def bbox(n1, n2, thresh=0.04):
    """(xmin, ymin, xmax, ymax) of what differs between two frames, or None."""
    d = np.abs(FRAME[n1] - FRAME[n2]).max(axis=2) > thresh
    if not d.any():
        return None
    ys, xs = np.where(d)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())

def center(t="VIEW_3D"):
    r = region_of(area(t))
    return r.x + r.width // 2, r.y + r.height // 2

def tear_menu(name="VIEW3D_MT_object", t="VIEW_3D", rt="HEADER", idx=0):
    with bpy.context.temp_override(**override(t, rt, idx)):
        bpy.ops.wm.menu_tear_off(menu_idname=name)
def tear_panel(name, t="VIEW_3D", rt="HEADER", idx=0):
    with bpy.context.temp_override(**override(t, rt, idx)):
        bpy.ops.wm.panel_tear_off(panel_idname=name)

class SIM_PT_field(bpy.types.Panel):
    bl_idname = "SIM_PT_field"; bl_label = "Sim Field"
    bl_space_type = "VIEW_3D"; bl_region_type = "UI"; bl_category = "Sim"
    def draw(self, context):
        ob = context.object
        self.layout.prop(ob, "name", text="") if ob else self.layout.label(text="none")
        self.layout.prop(context.scene, "frame_current")

class SIM_OT_dialog(bpy.types.Operator):
    bl_idname = "sim.dialog"; bl_label = "Sim Dialog"
    value: bpy.props.IntProperty(name="Value")
    state = {"exec": 0, "cancel": 0}
    def execute(self, context):
        SIM_OT_dialog.state["exec"] += 1; return {"FINISHED"}
    def cancel(self, context):
        SIM_OT_dialog.state["cancel"] += 1
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

bpy.utils.register_class(SIM_PT_field)
bpy.utils.register_class(SIM_OT_dialog)

# ---------------------------------------------------------------- scenarios
def s_calibrate():
    x, y = center(); move(x, y); yield 0.5
    log("window", win().width, win().height, "ui_scale", bpy.context.preferences.system.ui_scale)
    yield from grab("base")
    tear_menu(); yield 0.8
    yield from grab("menu")
    b = bbox("base", "menu"); check("menu tear-off visible", b is not None, b)
    x2, y2 = center(); move(x2 - 400, y2); yield 0.3
    tear_panel("SIM_PT_field"); yield 0.8
    yield from grab("two")
    log("panel bbox", bbox("menu", "two"))

SC = {"calibrate": s_calibrate}
exec(open(os.path.join(OUT, "scenarios.py"), encoding="utf-8").read()) if os.path.exists(os.path.join(OUT, "scenarios.py")) else None

gen = SC[SCEN]()
def tick():
    try:
        d = next(gen)
        return max(float(d or 0.05), 0.02)
    except StopIteration:
        ok = all(r[1] for r in results)
        log("DONE", "ALLPASS" if ok else "SOMEFAIL", f"{sum(r[1] for r in results)}/{len(results)}")
    except Exception:
        log("EXCEPTION", traceback.format_exc())
    LOG.flush()
    os._exit(0)
bpy.app.timers.register(tick, first_interval=2.0, persistent=True)
