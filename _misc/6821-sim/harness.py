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
def shift_press(x, y):
    """Shift+press with the key first, as a person does it. event_simulate(shift=True) only sets
    modifier bits, and the key press is what makes WM_event_drag_threshold pick the keyboard value.
    Don't use dblclick() with this: the simulator refuses DOUBLE_CLICK."""
    move(x, y); yield W
    move(x, y); yield W
    win().event_simulate(type="LEFT_SHIFT", value="PRESS", x=int(x), y=int(y), shift=True)
    yield 0.05
    win().event_simulate(type="LEFTMOUSE", value="PRESS", x=int(x), y=int(y), shift=True)
    yield 0.05
def shift_release(x, y):
    win().event_simulate(type="LEFTMOUSE", value="RELEASE", x=int(x), y=int(y), shift=True)
    yield 0.05
    win().event_simulate(type="LEFT_SHIFT", value="RELEASE", x=int(x), y=int(y))
    yield 0.2

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
def tear_enum(t="VIEW_3D", rt="HEADER", idx=0, **kw):
    with bpy.context.temp_override(**override(t, rt, idx)):
        return bpy.ops.wm.enum_tear_off(**kw)

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

class SIM_PT_enum(bpy.types.Panel):
    bl_idname = "SIM_PT_enum"; bl_label = "Sim Enum"
    bl_space_type = "VIEW_3D"; bl_region_type = "UI"; bl_category = "Sim"
    def draw(self, context):
        sc = context.scene
        self.layout.prop(context.tool_settings, "transform_pivot_point", text="")
        self.layout.prop_with_menu(sc.sequencer_colorspace_settings, "name", text="Sequencer",
                                   menu="UI_MT_color_space_select")
        if hasattr(sc, "sim_enum"):
            self.layout.prop(sc, "sim_enum")

class SIM_OT_area_probe(bpy.types.Operator):
    bl_idname = "sim.area_probe"; bl_label = "Sim Area Probe"
    state = {"area": None, "runs": 0}
    def execute(self, context):
        st = SIM_OT_area_probe.state
        st["area"] = context.area.type if context.area else None
        st["runs"] += 1
        return {"FINISHED"}

class SIM_MT_ctx(bpy.types.Menu):
    bl_idname = "SIM_MT_ctx"; bl_label = "Sim Context"
    def draw(self, context):
        self.layout.operator("sim.area_probe", text="Probe")

class SIM_MT_cols(bpy.types.Menu):
    bl_idname = "SIM_MT_cols"; bl_label = "Sim Columns"
    def draw(self, context):
        split = self.layout.split()
        for side in ("Left", "Right"):
            col = split.column()
            for i in range(4):
                col.operator("sim.area_probe", text=f"{side} Column {i}")

# enum_op registers this one itself, because it tests what happens when it goes away.
class SIM_OT_enum(bpy.types.Operator):
    bl_idname = "sim.enum"; bl_label = "Sim Enum Operator"
    type: bpy.props.EnumProperty(name="Type", items=[
        ("FIRST", "First Item", ""), ("SECOND", "Second Item", ""), ("THIRD", "Third Item", "")])
    state = {"type": None}
    def execute(self, context):
        SIM_OT_enum.state["type"] = self.type
        return {"FINISHED"}

# ---------------------------------------------------------------- Phases 5 and 6
def sim_state(**kw):
    st = dict(show=False, poll=0, poll_popup=0, draw=0, draw_popup=0, bad_draw=0,
              popover=None, pin=None)
    st.update(kw)
    return st


class SimTearPanel:
    """A panel that reports what ran. It polls False until a scenario sets state["show"], so the
    other scenarios see the same regions as before. `context.region_popup` tells a tear-off's draw
    from the source region's, which draws the same panel and would hide a missing call."""
    bl_space_type = "VIEW_3D"; bl_region_type = "UI"; bl_category = "SimTear"
    state = None
    rows = 5

    @classmethod
    def poll(cls, context):
        st = cls.state
        st["poll"] += 1
        if context.region_popup:
            st["poll_popup"] += 1
        return st["show"]

    def draw(self, context):
        st = self.__class__.state
        st["draw"] += 1
        if not st["show"]:
            st["bad_draw"] += 1
        if context.region_popup:
            st["draw_popup"] += 1
            st["popover"] = self.is_popover
            st.setdefault("popover_first", self.is_popover)
        else:
            st["pin"] = self.use_pin
        self.draw_rows(context)

    def draw_rows(self, context):
        for i in range(self.rows):
            self.layout.label(text=f"Row {i}")


class SimColumnsPanel(SimTearPanel):
    """Records the column count both ways, and the active tool, on each draw."""
    rows = 3

    def draw_rows(self, context):
        from bl_ui.space_toolsystem_common import toolsystem_column_count
        layout = self.layout
        st = self.__class__.state
        rec = st["popup"] if context.region_popup else st["region"]
        tool = context.workspace.tools.from_space_view3d_mode(context.mode, create=False)
        rec.update(width=layout.tear_off_width,
                   count=toolsystem_column_count(context.region, layout),
                   region_count=toolsystem_column_count(context.region),
                   tool=tool.idname if tool else None,
                   draws=rec.get("draws", 0) + 1)
        SimTearPanel.draw_rows(self, context)


class SimSpacePollPanel(SimTearPanel):
    """Polls a property of its editor, which the scenario picks, as the real panels there do."""

    @classmethod
    def poll(cls, context):
        st = cls.state
        st["poll"] += 1
        if context.region_popup:
            st["poll_popup"] += 1
        return st["show"] and getattr(context.space_data, st["prop"]) == st["value"]


class SIM_PT_tear_anchor(SimTearPanel, bpy.types.Panel):
    """Stays above the panel under test, so its tab stays and its rect shows in a frame diff."""
    bl_idname = "SIM_PT_tear_anchor"; bl_label = "Sim Anchor"
    state = sim_state()
    rows = 1


class SIM_PT_tear(SimTearPanel, bpy.types.Panel):
    bl_idname = "SIM_PT_tear"; bl_label = "Sim Tear"
    state = sim_state()


class SIM_PT_tear_sub(bpy.types.Panel):
    """No poll of its own on purpose: it relies on the parent's, as many subpanels do."""
    bl_idname = "SIM_PT_tear_sub"; bl_label = "Sim Tear Sub"; bl_parent_id = "SIM_PT_tear"
    bl_space_type = "VIEW_3D"; bl_region_type = "UI"; bl_category = "SimTear"

    def draw(self, context):
        st = SIM_PT_tear.state
        if not st["show"]:
            st["bad_draw"] += 1
        if context.region_popup:
            st["draw_popup"] += 1
            st["sub_popover"] = self.is_popover
        # More than the gray row's one line, or a failed poll couldn't make its tear-off shorter.
        for i in range(4):
            self.layout.label(text=f"Sub Row {i}")


class SIM_PT_tear_sub2(SimTearPanel, bpy.types.Panel):
    """Can be hidden, unlike SIM_PT_tear_sub, so its rect shows in a frame diff."""
    bl_idname = "SIM_PT_tear_sub2"; bl_label = "Sim Tear Sub 2"; bl_parent_id = "SIM_PT_tear"
    state = sim_state()
    rows = 1


class SIM_PT_hdr(SimTearPanel, bpy.types.Panel):
    bl_idname = "SIM_PT_hdr"; bl_label = "Sim Header"
    state = sim_state(header_popup=0, preset_popup=0)

    def draw_header(self, context):
        if context.region_popup:
            self.__class__.state["header_popup"] += 1
        self.layout.prop(context.scene, "use_gravity", text="")

    def draw_header_preset(self, context):
        if context.region_popup:
            self.__class__.state["preset_popup"] += 1
        self.layout.operator("sim.area_probe", text="", icon="PRESET")

    def draw_rows(self, context):
        # Must stay on the panel's own column, or the header's checkbox and X would go dead too.
        self.layout.enabled = context.scene.use_gravity
        SimTearPanel.draw_rows(self, context)


class SIM_PT_once(SimTearPanel, bpy.types.Panel):
    """The checkbox spans the middle of the header, so the release of a grab lands on it."""
    bl_idname = "SIM_PT_once"; bl_label = "Sim Once"
    state = sim_state()

    def draw_header(self, context):
        self.layout.prop(context.scene, "use_gravity", text="Long Checkbox Label Here")


class SIM_PT_place(SimTearPanel, bpy.types.Panel):
    """A selected toggle far under the header, which a regular popover would open under."""
    bl_idname = "SIM_PT_place"; bl_label = "Sim Place"
    state = sim_state()
    rows = 7

    def draw_rows(self, context):
        SimTearPanel.draw_rows(self, context)
        self.layout.prop(context.scene, "use_gravity", toggle=True)


class SIM_PT_props(SimTearPanel, bpy.types.Panel):
    bl_idname = "SIM_PT_props"; bl_label = "Sim Props"
    bl_space_type = "PROPERTIES"; bl_region_type = "WINDOW"; bl_context = "scene"; bl_category = ""
    state = sim_state()


class SIM_PT_none(SimTearPanel, bpy.types.Panel):
    """Same context as STRIP_PT_color_tag_picker: only shown through a popover."""
    bl_idname = "SIM_PT_none"; bl_label = "Sim None"
    bl_space_type = "PROPERTIES"; bl_region_type = "WINDOW"; bl_context = "none"; bl_category = ""
    state = sim_state()


class SIM_PT_tool_tab(SimTearPanel, bpy.types.Panel):
    """The Properties Tool tab shows 3D View sidebar panels of this category."""
    bl_idname = "SIM_PT_tool_tab"; bl_label = "Sim Tool Tab"; bl_category = "Tool"
    state = sim_state()


class SIM_PT_cols_anchor(SimTearPanel, bpy.types.Panel):
    bl_idname = "SIM_PT_cols_anchor"; bl_label = "Sim Anchor"; bl_region_type = "TOOLS"
    state = sim_state()
    rows = 1


class SIM_PT_cols(SimColumnsPanel, bpy.types.Panel):
    bl_idname = "SIM_PT_cols"; bl_label = "Sim Columns"; bl_region_type = "TOOLS"
    state = sim_state(popup={}, region={})


class SIM_PT_clip_cols(SimColumnsPanel, bpy.types.Panel):
    bl_idname = "SIM_PT_clip_cols"; bl_label = "Sim Clip"
    bl_space_type = "CLIP_EDITOR"; bl_region_type = "TOOLS"
    state = sim_state(popup={}, region={})


class SIM_PT_ui_cols(SimColumnsPanel, bpy.types.Panel):
    bl_idname = "SIM_PT_ui_cols"; bl_label = "Sim UI Columns"
    state = sim_state(popup={}, region={})


class SIM_PT_seq_poll(SimSpacePollPanel, bpy.types.Panel):
    bl_idname = "SIM_PT_seq_poll"; bl_label = "Sim Sequencer Poll"
    bl_space_type = "SEQUENCE_EDITOR"
    state = sim_state(prop="", value="")


bpy.utils.register_class(SIM_PT_field)
bpy.utils.register_class(SIM_OT_dialog)
bpy.utils.register_class(SIM_PT_enum)
bpy.utils.register_class(SIM_OT_area_probe)
bpy.utils.register_class(SIM_MT_ctx)
bpy.utils.register_class(SIM_MT_cols)
# Parents first, and each anchor before the panel it sits above.
for sim_cls in (SIM_PT_tear_anchor, SIM_PT_tear, SIM_PT_tear_sub, SIM_PT_tear_sub2, SIM_PT_hdr,
                SIM_PT_once, SIM_PT_place, SIM_PT_props, SIM_PT_none, SIM_PT_tool_tab,
                SIM_PT_cols_anchor, SIM_PT_cols, SIM_PT_clip_cols, SIM_PT_ui_cols,
                SIM_PT_seq_poll):
    bpy.utils.register_class(sim_cls)

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
