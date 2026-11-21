"""Add-on-only Timeline tool band, using the supported pixel draw handler.

The fixed-height band sits above the native scrollbar. Hover help and tool
popouts have their own space above the band.
"""

import bpy
import blf
import gpu
import time
from math import ceil
from types import SimpleNamespace
from gpu_extras.batch import batch_for_shader
from bpy.props import EnumProperty, IntProperty, StringProperty
from .timeline_catalog import ACTIONS, GROUPS, FAMILY, QUICK_LABELS, command_metadata
from . import timeline_config as model
from ..core import explainers

# Short row labels; tooltips keep the full catalogue names. Distinct from the
# All tab, the Breakdown slider and the Reference popout they sit beside.
ROW_LABELS = {
    'COPY_KEYS': 'Copy', 'PASTE_KEYS': 'Paste', 'MIRROR_SELECTED': 'Mirror', 'BAKE_STEP': 'Bake Object',
    'TRAIL_SHOW': 'Show Trails', 'INBETWEEN': 'Inbetween', 'INBETWEENS': 'Distribute',
    'PUSH_PREV': 'Push Prev', 'PULL_PREV': 'Pull Prev', 'PULL_NEXT': 'Pull Next', 'PUSH_NEXT': 'Push Next',
    'ALL': 'All Keys', 'GROW_LEFT': 'Grow Left', 'GROW_RIGHT': 'Grow Right',
    'TYPE_KEYFRAME': 'Mark Key', 'TYPE_BREAKDOWN': 'Mark Breakdown', 'TYPE_EXTREME': 'Mark Extreme',
    'TYPE_HOLD': 'Mark Hold', 'REFERENCE': 'Set Reference', 'HANDLE_CLAMPED': 'Clamped',
    'HANDLE_VECTOR': 'Vector', 'HANDLE_FREE': 'Free', 'T80': '80%', 'T90': '90%', 'T110': '110%',
    'T120': '120%', 'SNAP': 'Snap', 'OPPOSITE': 'Opposite', 'MIRROR_ACTIVE': 'Mirror Active',
    'SWAP': 'Swap', 'SMART_BAKE': 'Smart Bake', 'REDUCE': 'Reduce', 'BAKE_CLEANUP': 'Bake Proxies',
    'PROXY_TRANSLATION': 'Location Proxy', 'PROXY_ORIENTATION': 'Rotation Proxy', 'PROXY_WORLD': 'Proxy World',
    'PROXY_PARENT': 'Proxy Parent', 'BAKE_PREVIEW': 'Bake Preview', 'BAKE_INTEGER': 'Whole Frames',
    'PROXY_BAKE': 'Proxy & Bake', 'TO_SPLINE': 'To Spline', 'TO_STEPPED': 'To Stepped', 'TRAIL_TOGGLE': 'Trails', 'CLEANUP_ALL': 'Clean All Proxies',
    'TRAIL_REFRESH': 'Refresh', 'TRAIL_DIAGNOSE': 'Diagnose', 'TRAIL_HIDE': 'Hide Trails',
}

# All keeps its 12.9 row width: Hide Trails is not beside Show Trails there.
ALL_ROW_LABELS = {'TRAIL_SHOW': 'Trails'}

# Logical px: room left under the row for the Timeline's horizontal scrollbar, and the
# inset that keeps the row's end buttons off Blender's area corner handles.
SCROLLBAR_LIFT = 14
CORNER_INSET = 16

# Per workspace, saved with the file. Maximized views and extra windows of the
# same workspace share it (a Screen property would be lost in those).
STAGE_PROPERTY = "animassist_timeline_stage"


def current_stage(context):
    workspace = getattr(context, "workspace", None)
    stage = getattr(workspace, STAGE_PROPERTY, "ALL") if workspace else "ALL"
    return stage if stage in model.STAGE_IDS else "ALL"


def draw_stage_controls(layout, context, family=None):
    """Row stage selector for settings surfaces, plus a hidden-family note."""
    from . import timeline_strip as tools
    workspace = getattr(context, "workspace", None)
    screen = context.screen
    if workspace is None or not hasattr(workspace, STAGE_PROPERTY):
        return
    if screen is None or not any(tools.is_timeline(area) for area in screen.areas):
        # Opened from Preferences or another window: no row to stage here.
        layout.label(text="Open from a Timeline to change its row stage", icon="INFO")
        return
    layout.prop(workspace, STAGE_PROPERTY, text="Row Stage")
    if family:
        labels = {key: label for key, label, _actions in GROUPS}
        from ..prefs import get_prefs, timeline_record
        stage = current_stage(context)
        try:
            shown = model.row_families(timeline_record(get_prefs(context))['active'], stage)
        except (ValueError, TypeError, AttributeError):
            shown = None
        note = model.hidden_family_note(stage, family, labels.get(family, family), shown)
        if note:
            layout.label(text=note, icon="INFO")


def _tool_action(kind, key):
    """Catalogue action for a tool control; '' for tabs, menus and utilities.

    Stage ids share the key space with actions (the All tab and Select All
    Visible are both 'ALL'), so only tool kinds may resolve to an action.
    """
    if kind not in {'ACTION', 'SLIDER', 'POPOUT', 'PRESET'}:
        return ''
    action = key.split(':', 1)[0]
    return action if action in ACTIONS else ''


def _family_labels(stage):
    labels = {key: label for key, label, _actions in GROUPS}
    return ", ".join(labels[family] for family in model.stage_families(stage))


def _stage_description(kind, stage):
    label = model.stage_label(stage)
    if kind == "STAGE_CYCLE":
        return (f"Stage: {label}. Click to choose a stage; Ctrl+Wheel cycles. "
                "Each stage has its own toolset, edited in Settings")
    if stage == "ALL":
        return "Show the All overview of every tool family. Ctrl+Wheel over the stage button cycles stages"
    return (f"{label} stage: its own {_family_labels(stage)} toolset, edited in Settings. "
            "Ctrl+Wheel over the stage button cycles stages")


def _tooltip_paragraphs(context, item, row, unavailable):
    """Hover text for a row control as (text, role) paragraphs."""
    from . import timeline_strip as tools
    from .timeline_catalog import command_tooltip
    kind, key = item[0], item[1]
    action = key.split(':', 1)[0]
    if kind == 'ACTION' and action in ACTIONS:
        operator = tools._operator(action)
        operation = explainers.operator_text('animassist.' + ACTIONS[action][0]) if operator else 'Tool module unavailable'
        reason = unavailable(action)
        status = ''
        if action in {'OFFSET', 'OFFSET_MASK', 'OFFSET_SCENE_RANGE'}:
            from ..operators.anim_offset_ops import offset_session_status
            status = offset_session_status(context.scene) or ''
        return command_tooltip(action, operation, reason or '', status)
    if kind in {'SLIDER', 'POPOUT', 'PRESET'} and action in ACTIONS:
        operator = tools._operator(action)
        text = (explainers.operator_text('animassist.' + ACTIONS[action][0]) if operator else '') or ACTIONS[action][2]
        from ..constants import BREAKDOWN_ANCHOR_HINT
        lines = [(ACTIONS[action][2], 'TITLE'), (text.rstrip('.') + '.', 'BODY'),
                 (f'Works on: {command_metadata(action)[0]}.', 'DETAIL'),
                 ('Drag to preview; release to apply; Esc cancels. Right-click for tool settings.', 'DETAIL')]
        try:
            shown = row.view[1][action]
            ticks = model.tick_values(shown)
        except (ValueError, KeyError, AttributeError):
            ticks = []
        if ticks and kind == 'SLIDER':
            unit = model.SLIDERS[action][1]
            lines.insert(2, ('Ticks: ' + ', '.join(f'{t:g}{unit}' for t in ticks) + '. Click a tick to apply it.', 'BODY'))
        if action == 'DRAG':
            lines.append((BREAKDOWN_ANCHOR_HINT, 'DETAIL'))
        return lines
    text = explainers.raw_description(ANIMASSIST_OT_overlay_control, context, SimpleNamespace(kind=kind, key=key))
    return [(text.rstrip('.') + '.', 'BODY')]


def _shape_tooltip(context, item, paragraphs):
    """Apply the explainer preference (Full, Short, Off) and add any shortcut that
    already exists for the tool. Nothing is invented: no binding, no shortcut line."""
    current = explainers.mode(context)
    if current == 'OFF':
        return []
    kind, key = item[0], item[1]
    action = key.split(':', 1)[0]
    extra = []
    if kind in {'ACTION', 'SLIDER', 'POPOUT', 'PRESET'} and action in ACTIONS:
        operator, properties, _label = ACTIONS[action]
        bindings = []
        for idname, props in (('animassist.' + operator, properties),
                              ('animassist.timeline_tool', {'action': action}),
                              ('animassist.timeline_slider', {'action': action})):
            bindings += [b for b in explainers.shortcuts(idname, props) if b not in bindings]
        extra = [(line, 'DETAIL') for line in explainers.shortcut_lines(bindings)]
        # Bforartists' own command for the same job, only when Bforartists binds a key to it.
        from .timeline_catalog import NATIVE_EQUIVALENTS
        extra += [(line, 'DETAIL') for line in explainers.native_lines(NATIVE_EQUIVALENTS.get(action, ()))]
    if current == 'SHORT':
        title = [p for p in paragraphs if p[1] == 'TITLE'][:1]
        body = [(explainers.short(text) + '.', 'BODY') for text, role in paragraphs if role == 'BODY'][:1]
        warning = [(explainers.short(text) + '.', 'WARNING') for text, role in paragraphs if role == 'WARNING'][:1]
        paragraphs = title + body + warning
    return list(paragraphs) + extra


def _theme(context):
    theme = context.preferences.themes[0]
    widgets = theme.user_interface.wcol_regular
    return tuple(theme.dopesheet_editor.space.header), widgets


def _quad(rect, color):
    x, y, w, h = rect
    shader = gpu.shader.from_builtin("UNIFORM_COLOR")
    batch = batch_for_shader(shader, "TRIS", {"pos": ((x, y), (x+w, y), (x+w, y+h),
                                                       (x, y), (x+w, y+h), (x, y+h))})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


class ANIMASSIST_OT_overlay_control(bpy.types.Operator):
    bl_idname = "animassist.overlay_control"
    bl_label = "Anim Assist Timeline Tools"
    bl_options = {"INTERNAL"}
    kind: StringProperty(options={"HIDDEN", "SKIP_SAVE"})
    key: StringProperty(options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def description(cls, context, properties):
        from . import timeline_strip as tools
        if properties.kind in {'STAGE','STAGE_CYCLE','STAGE_ITEM'}:
            shown = current_stage(context) if properties.kind == 'STAGE_CYCLE' else properties.key
            return _stage_description('STAGE' if properties.kind == 'STAGE_ITEM' else properties.kind, shown)
        action=properties.key.split(':',1)[0]
        if properties.kind in {'SLIDER','POPOUT','PRESET'} and action in ACTIONS:
            operator=tools._operator(action)
            text=(explainers.operator_text('animassist.'+ACTIONS[action][0]) if operator else '') or ACTIONS[action][2]
            scope=command_metadata(action)[0]
            from ..constants import BREAKDOWN_ANCHOR_HINT
            return text+'. '+scope+'. Drag to preview; release to apply; Esc cancels. Right-click for tool settings.'+((' '+BREAKDOWN_ANCHOR_HINT) if action=='DRAG' else '')
        if properties.kind == "ACTION" and properties.key in ACTIONS:
            return explainers.raw_description(tools.ANIMASSIST_OT_timeline_tool,
                context, SimpleNamespace(action=properties.key))
        return {"SEARCH": ("Find any Anim Assist tool by name, family or idea; run it, or pin it to this row. "
                           "With nothing typed, browse every tool by family"),
                "SETTINGS": "Choose visible tools, slider modes, order and named layouts",
                "MORE": "Tools on this row that did not fit at this width; click to use them",
                "MENU": "Open this animation family's tools",
                "BAND": "Anim Assist tools; the remaining Timeline keeps its normal controls"}.get(properties.kind, "Anim Assist")

    def invoke(self, context, _event):
        from . import timeline_strip as tools
        if not tools.is_timeline(context.area):
            return {"CANCELLED"}
        if self.kind == "ACTION":
            return bpy.ops.animassist.timeline_tool("INVOKE_DEFAULT", action=self.key, canvas_undo=True)
        if self.kind == "SEARCH":
            return bpy.ops.animassist.timeline_search("INVOKE_DEFAULT")
        if self.kind == "SETTINGS":
            return bpy.ops.animassist.toolbar_settings("INVOKE_DEFAULT")
        if self.kind == "MENU":
            return bpy.ops.wm.call_menu("INVOKE_DEFAULT", name=tools._menu_id(self.key))
        if self.kind == "MORE":
            return bpy.ops.wm.call_menu("INVOKE_DEFAULT", name="ANIMASSIST_MT_timeline_more")
        if self.kind == "STAGE":
            return bpy.ops.animassist.timeline_stage(stage=self.key)
        if self.kind == "STAGE_CYCLE":
            _stage_menu[context.window.as_pointer()] = context.area.as_pointer()
            context.area.tag_redraw()
            return {"FINISHED"}
        return {"FINISHED"}


class ANIMASSIST_MT_timeline_stage(bpy.types.Menu):
    bl_idname = "ANIMASSIST_MT_timeline_stage"
    bl_label = "Anim Assist Stage"
    bl_description = "Choose which stage toolset the Timeline row shows"

    def draw(self, context):
        workspace = getattr(context, "workspace", None)
        if workspace is not None and hasattr(workspace, STAGE_PROPERTY):
            self.layout.props_enum(workspace, STAGE_PROPERTY)


class ANIMASSIST_OT_timeline_stage(bpy.types.Operator):
    bl_idname = "animassist.timeline_stage"
    bl_label = "Anim Assist Stage"
    bl_description = "Show one animation stage's tool families in the Timeline band"
    bl_options = {"INTERNAL"}
    stage: StringProperty(options={"HIDDEN", "SKIP_SAVE"})
    step: IntProperty(options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def poll(cls, context):
        workspace = getattr(context, "workspace", None)
        return workspace is not None and hasattr(workspace, STAGE_PROPERTY)

    def execute(self, context):
        stage = model.next_stage(current_stage(context), self.step) if self.step else self.stage
        if stage not in model.STAGE_IDS:
            self.report({"WARNING"}, "Choose a known stage")
            return {"CANCELLED"}
        setattr(context.workspace, STAGE_PROPERTY, stage)  # update redraws Timelines
        return {"FINISHED"}


_handle = None
_epoch = object()
_keymaps = []
_resize_attempts = {}
_input_windows = set()
_hover = {}
# Window -> area pointer whose stage dropdown is open (drawn by this band, not a Blender menu,
# so it never opens over the stage button and a second click on the button closes it).
_stage_menu = {}
_hover_started = {}


def _row_geometry(area, system):
    scale = system.ui_scale
    header = next((r for r in area.regions if r.type == "HEADER"), None)
    base = max(28 * scale, header.height if header else 0)
    height = base + 8 * scale
    scrollbar = ceil(max(SCROLLBAR_LIFT * scale, 11 * scale + 4 * system.pixel_size))
    return base, height, scrollbar, 46 * scale


def _toolbar_row(context):
    from ..prefs import get_prefs, timeline_record
    region, area = context.region, context.area
    scale = context.preferences.system.ui_scale
    base, height, scrollbar, keys_at_top = _row_geometry(area, context.preferences.system)
    # The native scrub ruler and keyframe summary row are always drawn at the
    # top of the canvas, whichever side the header is on. Anchor the band at
    # the bottom so it never hides or intercepts clicks on keyframes. Markers
    # use a bottom strip; sit above it when the canvas has room for both.
    usable_height = region.height
    space = context.space_data
    markers = bool(context.scene.timeline_markers) and getattr(space, "show_markers", True)
    marker_strip = 42 * scale if markers else 0
    y = max(scrollbar, marker_strip if usable_height >= marker_strip + height + keys_at_top else 0)
    if usable_height < y + height + keys_at_top:
        return SimpleNamespace(items=[], band=(0, y, region.width, 0))
    blf.size(0, round(11 * scale))
    # Blender's area corner handles (drag to split or join) sit in the bottom corners.
    # When the row reaches the Timeline's left or right edge (channels or sidebar
    # closed), keep the end buttons clear of them so a click hits the button.
    left = CORNER_INSET * scale if region.x <= area.x + 1 else 0
    right = CORNER_INSET * scale if region.x + region.width >= area.x + area.width - 1 else 0
    try: record=timeline_record(get_prefs(context))
    except ValueError: record=model.recommended(ACTIONS)
    stage = current_stage(context)
    layout = record['active']
    view = model.stage_view(layout, stage)
    labels={**QUICK_LABELS,**ROW_LABELS,**(ALL_ROW_LABELS if stage == 'ALL' else {})}
    # Vertical space never changes the horizontal packing or button order.
    items = model.toolbar_layout(max(1, region.width - left - right), base, base, False,
                       record,GROUPS,labels,lambda text: blf.dimensions(0, text)[0],
                       stage, view=view)
    items = [
        (kind, key, label, (x + left, y + iy, w, ih + height - base))
        for kind, key, label, (x, iy, w, ih) in items
    ]
    band = (0, y, region.width, height)
    return SimpleNamespace(items=items, band=band, layout=layout, stage=stage, view=view)


def _items(context):
    row = _toolbar_row(context)
    return row.items, row.band


# Family and More lists drawn by the add-on (Blender's own popup menus picked an item on
# mouse release and closed when the pointer moved away). One click opens a list; it stays
# open until an item is clicked, the same button or anything else is clicked, or Esc.
_row_menu = {}


def _list_open(context):
    window, area = context.window, context.area
    state = _row_menu.get(window.as_pointer()) if window else None
    return state if state and area and state['area'] == area.as_pointer() else None


def _open_row_menu(context, kind, key):
    pointer = context.window.as_pointer()
    _stage_menu.pop(pointer, None)
    _row_menu[pointer] = dict(area=context.area.as_pointer(), opener=(kind, key),
                              view=('FAMILY', key) if kind == 'MENU' else ('MORE', ''), back=False)
    for area in context.window.screen.areas:
        area.tag_redraw()


def _close_row_menu(context):
    if context.window and _row_menu.pop(context.window.as_pointer(), None):
        for area in context.window.screen.areas:
            area.tag_redraw()


def _row_hidden_tools(row):
    """Visible tools of the shown setup that did not fit on the row."""
    order, tools = row.view
    families = set(model.row_families(row.layout, row.stage, view=row.view))
    shown = {item[1].split(':', 1)[0] for item in row.items if item[0] in {'ACTION', 'SLIDER', 'POPOUT'}}
    return [a for a in order if a in ACTIONS and tools.get(a, {}).get('mode', 'HIDDEN') != 'HIDDEN'
            and FAMILY[a][0] in families and a not in shown]


def _list_entries(row, state):
    """(kind, key, label) rows: HEAD, GAP, RUN, FAMILY, BACK, OPTIONS, HOME."""
    view, key = state['view']
    if view == 'FAMILY':
        label, actions = next((l, a) for k, l, a in GROUPS if k == key)
        rows = [('BACK', '', '\u2039 Back')] if state.get('back') else []
        rows.append(('HEAD', key, label))
        for action in actions:
            rows.append(('GAP', '', '') if action is None else ('RUN', action, ACTIONS[action][2]))
        return rows + [('GAP', '', ''), ('OPTIONS', key, f'{label} Options'), ('HOME', '', 'Open Anim Assist Panel')]
    # More has one job: the row's tools that did not fit (owner pick "C", 2026-10-18).
    # Every other tool is in Find.
    hidden = _row_hidden_tools(row)
    if not hidden:
        return [('HEAD', '', 'Every tool on this row fits')]
    return [('HEAD', '', 'Did Not Fit')] + [('RUN', a, ACTIONS[a][2]) for a in hidden]


def _list_layout(context, row):
    """Rects of the open family/More list, in columns above the row."""
    state = _list_open(context)
    if not state:
        return []
    items, band = row.items, row.band
    entries = _list_entries(row, state)
    scale = context.preferences.system.ui_scale
    row_h, gap_h, pad = 20 * scale, 7 * scale, 8 * scale
    blf.size(0, round(11 * scale))
    width = max([140 * scale] + [blf.dimensions(0, label)[0] + 2 * pad for _k, _key, label in entries])
    base = band[1] + band[3] + 4 * scale
    # Stay below the scrub strip at the top: Blender takes clicks there to change the frame.
    avail = max(row_h, context.region.height - base - 30 * scale)
    columns, column, used = [], [], 0.
    for entry in entries:
        h = gap_h if entry[0] == 'GAP' else row_h
        if column and used + h > avail:
            columns.append(column); column, used = [], 0.
        if entry[0] == 'GAP' and not column:
            continue
        column.append((entry, h)); used += h
    if column:
        columns.append(column)
    tallest = max(sum(h for _e, h in col) for col in columns)
    anchor = next((item for item in items if (item[0], item[1]) == state['opener']), None)
    x0 = anchor[3][0] if anchor else 0
    x0 = max(0, min(x0, context.region.width - len(columns) * (width + 2 * scale)))
    result = []
    for index, col in enumerate(columns):
        x, y = x0 + index * (width + 2 * scale), base + tallest
        for (kind, key, label), h in col:
            y -= h
            result.append((kind, key, label, (x, y, width, h)))
    return result


def popout_geometry(region_w, region_h, band, track_x, scale, extra=0.):
    """(box, track) of a popout slider, shared by drawing and the slider operator.
    *extra* adds a bottom line (the hint of a clicked popout)."""
    y = band[1] + band[3] + 4 * scale
    available = max(0, region_h - y)
    # In a short Timeline, omit the hint line. It is also in the status bar.
    extra = extra if available >= 44 * scale + extra else 0.
    width = min(280 * scale, region_w)
    height = min(44 * scale + extra, available)
    x = max(0, min(track_x, region_w - width))
    return (x, y, width, height), (x + 10 * scale, y + 5 * scale + extra, max(1, width - 70 * scale), 16 * scale)


def _menu_open(context):
    window, area = context.window, context.area
    return bool(window and area and _stage_menu.get(window.as_pointer()) == area.as_pointer())


def _close_stage_menu(context):
    if context.window and _stage_menu.pop(context.window.as_pointer(), None):
        for area in context.window.screen.areas:
            area.tag_redraw()


def _menu_items(context, items, band):
    """Rects of the open stage dropdown: a list above the stage button, or one
    row of the five stages when the Timeline is too short for the list."""
    button = next((item for item in items if item[0] == 'STAGE_CYCLE'), None)
    if button is None:
        return []
    scale = context.preferences.system.ui_scale
    bx, _by, bw, bh = button[3]
    gap, pad = 2 * scale, 8 * scale
    blf.size(0, round(11 * scale))
    stages = [(key, label) for key, label, _families in model.STAGES]
    top = band[1] + band[3] + gap
    region_w = context.region.width
    region_h = context.region.height - 23 * scale
    if region_h <= top:
        return []
    if top + len(stages) * (bh + gap) <= region_h:
        width = max(bw, max(blf.dimensions(0, label)[0] for _key, label in stages) + 2 * pad)
        x = max(0, min(bx, region_w - width))
        return [('STAGE_ITEM', key, label, (x, top + (len(stages) - 1 - index) * (bh + gap), width, bh))
                for index, (key, label) in enumerate(stages)]
    # Use one row when the full list cannot fit above the buttons.
    bh = min(bh, region_h - top)
    widths = [blf.dimensions(0, label)[0] + 2 * pad for _, label in stages]
    total = sum(widths) + (len(stages) - 1) * gap
    if total > region_w:
        stages = [(key, label[:3]) for key, label in stages]
        widths = [(region_w - (len(stages) - 1) * gap) / len(stages)] * len(stages)
        total = region_w
    x = min(bx, region_w - total)
    result = []
    for (key, label), width in zip(stages, widths):
        result.append(('STAGE_ITEM', key, label, (x, top, width, bh)))
        x += width + gap
    return result


def _fit_hover_help(paragraphs, region_w, region_h, band, measure, scale):
    """Fit hover help in the space above the band, leaving every button clear."""
    y = band[1] + band[3] + 4 * scale
    line_h, pad = 15 * scale, 7 * scale
    available = region_h - y
    count = int((available - 2 * pad) // line_h)
    if count < 1 or region_w <= 4 * pad:
        return [], y, 0, 0
    lines, width, height = model.fit_tooltip(
        paragraphs, region_w, available, measure, scale, line_h, pad, 420 * scale)
    if len(lines) > count:
        lines = lines[:count]
        text, role = lines[-1]
        while text and measure(text.rstrip() + '\u2026') > width - 2 * pad:
            text = text[:-1]
        lines[-1] = (text.rstrip() + '\u2026', role)
        height = len(lines) * line_h + 2 * pad
    return lines, y, width, height


def _inside(rect, location):
    x, y, w, h = rect
    return x <= location[0] < x+w and y <= location[1] < y+h


_COLORS={'tween':(.25,.8,.8,1),'timing':(1,.72,.25,1),'curves':(.4,.75,1,1),
         'keys':(1,.8,.35,1),'pose':(.8,.6,1,1),'bake':(1,.6,.3,1),'motion':(.5,.85,.5,1)}


def _text(rect,text,color,scale,font=11,left=False):
    x,y,w,h=rect
    blf.size(0,round(font*scale)); blf.color(0,*color)
    tw,th=blf.dimensions(0,text)
    blf.position(0,x+3*scale if left else x+(w-tw)/2,y+(h-th)/2+1,0)
    blf.draw(0,text)


def _glyph(rect,action,color):
    x,y,w,h=rect; cx=x+w/2; cy=y+h/2; r=min(w,h)*.28
    gpu.state.blend_set('ALPHA')
    shader=gpu.shader.from_builtin('UNIFORM_COLOR')
    if action in {'SEARCH','SETTINGS','MORE'}:
        if action=='MORE':
            for dx in (-r,0,r): _quad((cx+dx-1,cy-1,2,2),color)
        else:
            import math
            positions=[(cx+math.cos(i*math.pi/4)*r,cy+math.sin(i*math.pi/4)*r) for i in range(9)]
            if action=='SEARCH': positions.extend(((cx+r*.7,cy-r*.7),(cx+r*1.5,cy-r*1.5)))
            batch=batch_for_shader(shader,'LINE_STRIP',{'pos':positions})
            shader.bind(); shader.uniform_float('color',color); batch.draw(shader)
            if action=='SETTINGS':
                for i in range(4):
                    dx=math.cos(i*math.pi/2)*r; dy=math.sin(i*math.pi/2)*r
                    _quad((cx+dx-2,cy+dy-2,4,4),color)
        return
    positions=((cx,cy+r),(cx+r,cy),(cx,cy-r),(cx,cy+r),(cx,cy-r),(cx-r,cy))
    if action.startswith('NUDGE_'):
        sign=-1 if action=='NUDGE_LEFT' else 1
        positions=((cx+sign*r,cy),(cx-sign*r,cy+r),(cx-sign*r,cy-r))
    elif action in {'COPY_KEYS','PASTE_KEYS','BAKE_STEP'}:
        positions=((cx-r,cy-r),(cx+r,cy-r),(cx+r,cy+r),
                   (cx-r,cy-r),(cx+r,cy+r),(cx-r,cy+r))
    batch=batch_for_shader(shader,'TRIS',{'pos':positions})
    shader.bind(); shader.uniform_float('color',color); batch.draw(shader)
    if action=='COPY_KEYS': _quad((cx-r/2,cy-r/2,r,r),(.12,.12,.12,1))


# Key-type icons match the Dope Sheet: the theme's key colours (bright "selected"
# variants, readable on the row) and Blender's relative diamond sizes, so the type
# reads by shape and size as well as colour.
_KEY_ICONS = {
    'TYPE_KEYFRAME': ('keyframe_selected', 1.0, (1.0, .745, .196)),
    'TYPE_BREAKDOWN': ('keyframe_breakdown_selected', .85, (.353, .808, 1.0)),
    'TYPE_EXTREME': ('keyframe_extreme_selected', 1.2, (1.0, .631, .631)),
    'TYPE_HOLD': ('keyframe_moving_hold_selected', .925, (1.0, .937, .945)),
    'TYPE_JITTER': ('keyframe_jitter_selected', .8, (.529, 1.0, .361)),
}


def key_icon_style(context, action):
    """(fill RGB, border RGB, size factor) for a key-type icon, from the theme."""
    name, factor, fallback = _KEY_ICONS[action]
    try:
        anim = context.preferences.themes[0].common.anim
        fill = tuple(getattr(anim, name))[:3]
    except (AttributeError, IndexError, TypeError):
        fill = fallback
    try:
        border = tuple(context.preferences.themes[0].dopesheet_editor.keyframe_border)[:3]
    except (AttributeError, IndexError, TypeError):
        border = (0., 0., 0.)
    return fill, border, factor


def _key_icon(rect, context, action, alpha):
    fill, border, factor = key_icon_style(context, action)
    x, y, w, h = rect
    cx, cy = x + w / 2, y + h / 2
    r = min(w, h) * .30 * factor
    gpu.state.blend_set('ALPHA')  # text drawing can leave blending off; faded icons need it
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    for radius, color in ((r + 1.5, (*border, alpha)), (r, (*fill, alpha))):
        positions = ((cx, cy + radius), (cx + radius, cy), (cx, cy - radius),
                     (cx, cy + radius), (cx, cy - radius), (cx - radius, cy))
        batch = batch_for_shader(shader, 'TRIS', {'pos': positions})
        shader.bind(); shader.uniform_float('color', color); batch.draw(shader)


# Handle-type icons use the theme's Graph Editor handle colours (bright selected variants).
_HANDLE_COLORS = {
    'HANDLE_AUTO': ('handle_sel_auto', (.941, 1.0, .251)),
    'HANDLE_CLAMPED': ('handle_sel_auto_clamped', (.941, .686, .565)),
    'HANDLE_VECTOR': ('handle_sel_vect', (.251, .753, .188)),
    'HANDLE_ALIGNED': ('handle_sel_align', (.941, .565, .627)),
    'HANDLE_FREE': ('handle_sel_free', (1.0, .937, .945)),
}
_SHAPE_ICONS = frozenset({'INBETWEEN', 'INBETWEENS', 'REFERENCE', 'OPPOSITE', 'MIRROR_SELECTED', 'MIRROR_ACTIVE',
                          'SWAP', 'BAKE_STEP', 'PROXY_TRANSLATION', 'PROXY_ORIENTATION', 'PROXY_WORLD',
                          'PROXY_PARENT'})
_LINE_ICONS = frozenset(_HANDLE_COLORS) | {'GROW_LEFT', 'GROW_RIGHT', 'GROW_BOTH', 'TO_SPLINE', 'TO_STEPPED',
                                           'TRAIL_TOGGLE'} | _SHAPE_ICONS


def handle_icon_color(context, action):
    name, fallback = _HANDLE_COLORS[action]
    try:
        return tuple(getattr(context.preferences.themes[0].common.curves, name))[:3]
    except (AttributeError, IndexError, TypeError):
        return fallback


def _trails_shown():
    try:
        from ..operators.p5_overlay_ops import trails_shown
        return trails_shown()
    except Exception:
        return False


def _lines(points, color, mode='LINE_STRIP'):
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, mode, {'pos': points})
    shader.bind(); shader.uniform_float('color', color); batch.draw(shader)


def _tris(points, color):
    _lines(points, color, 'TRIS')


def _disc(cx, cy, radius, color, steps=12):
    import math
    ring = [(cx + math.cos(i * 2 * math.pi / steps) * radius, cy + math.sin(i * 2 * math.pi / steps) * radius)
            for i in range(steps + 1)]
    _tris([p for i in range(steps) for p in ((cx, cy), ring[i], ring[i + 1])], color)


def _ring(cx, cy, radius, color, steps=20, start=0., sweep=None):
    import math
    sweep = 2 * math.pi if sweep is None else sweep
    _lines([(cx + math.cos(start + sweep * i / steps) * radius, cy + math.sin(start + sweep * i / steps) * radius)
            for i in range(steps + 1)], color)


def _shape_icon(action, cx, cy, r, color, scale):
    """Compact-row icons for tween, reference, pose, bake and proxy tools."""
    import math

    def diamond(dx, size):
        _tris(((dx, cy + size), (dx + size, cy), (dx, cy - size), (dx, cy + size), (dx, cy - size), (dx - size, cy)),
              color)

    def triangle(tip, base, half, filled=True):
        points = ((tip, cy), (base, cy + half), (base, cy - half))
        if filled: _tris(points, color)
        else: _lines(points + (points[0],), color)

    if action in {'INBETWEEN', 'INBETWEENS'}:
        diamond(cx - r * 1.0, r * .55); diamond(cx + r * 1.0, r * .55)
        if action == 'INBETWEEN':
            _quad((cx - r * .4, cy - .9 * scale, r * .8, 1.8 * scale), color)
            _quad((cx - .9 * scale, cy - r * .4, 1.8 * scale, r * .8), color)
        else:
            for dx in (-.25, .25):
                _quad((cx + dx * r - 1.5 * scale, cy - 1.5 * scale, 3 * scale, 3 * scale), color)
    elif action == 'REFERENCE':
        _ring(cx, cy, r * .95, color); _ring(cx, cy, r * .5, color)
        _quad((cx - 1.2 * scale, cy - 1.2 * scale, 2.4 * scale, 2.4 * scale), color)
    elif action == 'OPPOSITE':
        from_x, to_x = cx - r * .65, cx + r * .65
        _disc(from_x, cy, r * .42, color); _ring(to_x, cy, r * .42, color)
        _lines(((from_x + r * .45, cy), (to_x - r * .45, cy)), color)
    elif action in {'MIRROR_SELECTED', 'MIRROR_ACTIVE'}:
        for y0 in (-1., -.2, .6):
            _lines(((cx, cy + y0 * r), (cx, cy + (y0 + .4) * r)), color)
        triangle(cx - r * 1.2, cx - r * .25, r * .6)
        triangle(cx + r * 1.2, cx + r * .25, r * .6, filled=action == 'MIRROR_SELECTED')
    elif action == 'SWAP':
        top, bottom = cy + r * .45, cy - r * .45
        _lines(((cx - r * 1.1, top), (cx + r * .7, top)), color)
        _tris(((cx + r * 1.2, top), (cx + r * .6, top + r * .35), (cx + r * .6, top - r * .35)), color)
        _lines(((cx + r * 1.1, bottom), (cx - r * .7, bottom)), color)
        _tris(((cx - r * 1.2, bottom), (cx - r * .6, bottom + r * .35), (cx - r * .6, bottom - r * .35)), color)
    elif action == 'BAKE_STEP':
        _lines(((cx - r * 1.2, cy - r * .85), (cx + r * 1.2, cy - r * .85)), color)
        for i, height in enumerate((.5, 1.1, 1.6, .9)):
            bx = cx - r * .9 + i * r * .6
            _quad((bx - scale, cy - r * .8, 2 * scale, r * height), color)
    elif action == 'PROXY_TRANSLATION':
        _lines(((cx - r, cy), (cx + r, cy)), color, 'LINES'); _lines(((cx, cy - r), (cx, cy + r)), color, 'LINES')
        a = r * .35
        _tris(((cx + r * 1.15, cy), (cx + r * .75, cy + a), (cx + r * .75, cy - a),
               (cx - r * 1.15, cy), (cx - r * .75, cy + a), (cx - r * .75, cy - a),
               (cx, cy + r * 1.15), (cx + a, cy + r * .75), (cx - a, cy + r * .75),
               (cx, cy - r * 1.15), (cx + a, cy - r * .75), (cx - a, cy - r * .75)), color)
    elif action == 'PROXY_ORIENTATION':
        _ring(cx, cy, r * .85, color, steps=18, start=math.radians(60), sweep=math.radians(290))
        ex, ey = cx + math.cos(math.radians(350)) * r * .85, cy + math.sin(math.radians(350)) * r * .85
        _tris(((ex + r * .35, ey + r * .1), (ex - r * .3, ey + r * .15), (ex, ey - r * .4)), color)
    elif action == 'PROXY_WORLD':
        _ring(cx, cy, r * .95, color)
        _lines(((cx - r * .95, cy), (cx + r * .95, cy)), color, 'LINES')
        _lines([(cx + math.sin(a) * r * .42, cy + math.cos(a) * r * .95)
                for a in [math.pi * i / 10 for i in range(21)]], color)
    elif action == 'PROXY_PARENT':
        _disc(cx - r * .7, cy + r * .7, r * .3, color)
        _lines(((cx - r * .7, cy + r * .4), (cx - r * .7, cy - r * .55), (cx + r * .15, cy - r * .55)), color)
        _quad((cx + r * .2, cy - r * .95, r * .8, r * .8), color)


def _tool_icon(rect, context, action, alpha, accent, ink):
    """Line icons for row tools (grow, interpolation, handle types, trails)."""
    import math
    x, y, w, h = rect
    cx, cy = x + w / 2, y + h / 2
    r = min(w, h) * .32
    scale = context.preferences.system.ui_scale
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(max(1., 1.5 * scale))
    try:
        if action in _SHAPE_ICONS:
            _shape_icon(action, cx, cy, r, (*accent[:3], alpha), scale)
        elif action in _HANDLE_COLORS:
            color = (*handle_icon_color(context, action), alpha)
            shape = {
                'HANDLE_CLAMPED': ((cx - r, cy), (cx + r, cy)),
                'HANDLE_AUTO': ((cx - r, cy - r * .5), (cx + r, cy + r * .5)),
                'HANDLE_ALIGNED': ((cx - r, cy - r * .85), (cx + r, cy + r * .85)),
                'HANDLE_VECTOR': ((cx - r, cy + r * .85), (cx, cy), (cx + r, cy + r * .85)),
                'HANDLE_FREE': ((cx - r, cy + r * .7), (cx, cy), (cx + r, cy - r * .25)),
            }[action]
            _lines(shape, color)
            for px, py in (shape[0], shape[-1]):
                _quad((px - 1.5 * scale, py - 1.5 * scale, 3 * scale, 3 * scale), color)
            _quad((cx - 2.5 * scale, cy - 2.5 * scale, 5 * scale, 5 * scale), (*ink[:3], alpha))
        elif action == 'TO_SPLINE':
            points = []
            for i in range(13):
                t = i / 12
                ease = t * t * (3 - 2 * t)
                points.append((cx - r + 2 * r * t, cy - r * .75 + 1.5 * r * ease))
            _lines([(cx - r * 1.3, cy - r * .75)] + points + [(cx + r * 1.3, cy + r * .75)], (*accent[:3], alpha))
        elif action == 'TO_STEPPED':
            s = r * .66
            _lines(((cx - r * 1.2, cy - r * .75), (cx - s, cy - r * .75), (cx - s, cy), (cx + s, cy),
                    (cx + s, cy + r * .75), (cx + r * 1.2, cy + r * .75)), (*accent[:3], alpha))
        elif action in {'GROW_LEFT', 'GROW_RIGHT', 'GROW_BOTH'}:
            color = (*accent[:3], alpha)
            # A selected key (diamond) with an arrow growing the selection outward.
            def key(kx):
                k = r * .45
                _lines(((kx, cy + k), (kx + k, cy), (kx, cy - k), (kx - k, cy), (kx, cy + k)), color)
            if action == 'GROW_BOTH':
                key(cx)
                _tris(((cx - r * 1.3, cy), (cx - r * .6, cy + r * .5), (cx - r * .6, cy - r * .5),
                       (cx + r * 1.3, cy), (cx + r * .6, cy + r * .5), (cx + r * .6, cy - r * .5)), color)
            else:
                sign = -1 if action == 'GROW_LEFT' else 1
                kx = cx - sign * r * .55
                key(kx)
                _tris(((cx + sign * r * 1.25, cy), (cx + sign * r * .2, cy + r * .6),
                       (cx + sign * r * .2, cy - r * .6)), color)
        elif action == 'TRAIL_TOGGLE':
            shown = _trails_shown()
            color = (*accent[:3], alpha)
            upper = [(cx + math.cos(a) * r * 1.25, cy + math.sin(a) * r * .75)
                     for a in [math.pi * i / 10 for i in range(11)]]
            lower = [(cx + math.cos(a) * r * 1.25, cy - math.sin(a) * r * .75)
                     for a in [math.pi * i / 10 for i in range(10, -1, -1)]]
            _lines(upper + lower, color)
            if shown:
                _disc(cx, cy, r * .45, color)
            else:
                _lines(((cx - r * 1.1, cy - r * .9), (cx + r * 1.1, cy + r * .9)), color, 'LINES')
    finally:
        gpu.state.line_width_set(1.)


def _parts(rect,label,scale):
    blf.size(0,round(11*scale))
    return model.slider_parts(rect,label,lambda s:blf.dimensions(0,s)[0],scale)


def _track(rect,value,tool,color):
    x,y,w,h=rect; cy=y+h/2
    low,high=model.track_range(tool)
    fraction=min(1,max(0,(value-low)/(high-low)))
    _quad((x,cy-2,w,4),(.15,.15,.15,1))
    _quad((x,cy-2,w*fraction,4),color)
    # Preset ticks: click one to apply it (the drag snaps onto it).
    for tick in model.tick_values(tool):
        tx=x+w*(tick-low)/(high-low)
        _quad((tx-.5,cy-5,1.5,10),(.85,.85,.85,color[3]))
    _quad((x+w*fraction-3,cy-5,6,10),color)


def _slider_controls(context,point,item,scale,stage_tools):
    from ..operators import timeline_slider_ops as sliders
    kind,action,label,rect=item
    tool=model.effective_tool(action,stage_tools[action])
    track,value_rect,reset_rect=_parts(rect,label,scale)
    if kind=='POPOUT': track=(rect[0],rect[1],120*scale,rect[3])
    value=sliders.last_value(context.window,context.area,action,tool['default'])
    if kind=='SLIDER' and _inside(value_rect,point):
        return bpy.ops.animassist.slider_value('INVOKE_DEFAULT',True,action=action,value=value)
    if kind=='SLIDER' and _inside(reset_rect,point):
        result=bpy.ops.animassist.timeline_slider('EXEC_DEFAULT',action=action,value=tool['default'])
        if 'FINISHED' in result: bpy.ops.ed.undo_push(message='Reset '+model.SLIDERS[action][0])
        return result
    return bpy.ops.animassist.timeline_slider('INVOKE_DEFAULT',True,action=action,
        mode='INLINE' if kind=='SLIDER' else 'POPOUT',track_x=track[0],track_y=track[1],track_width=track[2])


def _draw():
    context = bpy.context
    from . import timeline_strip as tools
    if not tools.is_timeline(context.area) or not tools._enabled():
        return
    if context.region.height < 8:
        return
    row = _toolbar_row(context)
    items, band = row.items, row.band
    if not items:
        return
    background, widgets = _theme(context)
    scale = context.preferences.system.ui_scale
    from ..operators import timeline_slider_ops as sliders
    active = sliders.feedback(context.window, context.area)
    stage = row.stage
    stage_tools = row.view[1]
    selection_checks = {}
    availability = {}

    def unavailable(action):
        if action not in availability:
            availability[action] = tools._unavailable(
                context, context.area, action, selection_checks=selection_checks)
        return availability[action]

    old_blend = gpu.state.blend_get()
    try:
        gpu.state.blend_set("ALPHA")
        _quad(band, (*background[:3], 1))
        pointer = context.window.as_pointer()
        hover = _hover.get(pointer)
        if hover and hover[0] != context.area.as_pointer():
            hover = None
        for kind, key, label, rect in items:
            action=_tool_action(kind,key)
            highlighted = hover == (context.area.as_pointer(), kind, key)
            reason = unavailable(action) if action else ""
            color = widgets.inner_sel if highlighted else widgets.inner
            _quad(rect,tuple(color) if kind!='MENU' else (*background[:3],1))
            text_color = widgets.text_sel if highlighted else widgets.text
            ink=(*text_color[:3],.45 if reason else 1)
            accent=_COLORS.get(FAMILY[action][0] if action in FAMILY else key,ink)
            if kind in {'STAGE','STAGE_CYCLE'}:
                shown = stage if kind=='STAGE_CYCLE' else key
                current = kind=='STAGE_CYCLE' or key==stage
                if current and kind=='STAGE' and not highlighted:
                    _quad(rect,tuple(widgets.inner_sel))
                if current and shown!='ALL':
                    # Underline in the colour of the stage's first family.
                    _quad((rect[0]+3*scale,rect[1]+2*scale,rect[2]-6*scale,2*scale),
                          _COLORS[model.stage_families(shown)[0]])
                text_rect=rect
                blf.size(0,round(11*scale))
                arrow=0
                if kind=='STAGE_CYCLE' and rect[2]>=blf.dimensions(0,label)[0]+(model.STAGE_ARROW+8)*scale:
                    arrow=model.STAGE_ARROW*scale
                    text_rect=(rect[0],rect[1],rect[2]-arrow,rect[3])
                ink_text=(*widgets.text_sel[:3],1) if current or highlighted else ink
                _text(text_rect,label,ink_text,scale)
                if arrow:
                    # Dropdown arrow: three stacked bars narrowing downward.
                    ax=rect[0]+rect[2]-arrow*.6; ay=rect[1]+rect[3]/2
                    for row,half in enumerate((3,2,1)):
                        _quad((ax-half*scale,ay+(1-row)*scale,2*half*scale,scale),ink_text)
                continue
            if kind=='SLIDER':
                tool=model.effective_tool(action,stage_tools[action])
                value=active.value if active and active.action==action else sliders.last_value(context.window,context.area,action,tool['default'])
                track,value_rect,reset_rect=_parts(rect,label,scale)
                if label: _text((rect[0],rect[1],track[0]-rect[0],rect[3]),label,ink,scale,left=True)
                _track(track,value,tool,(*accent[:3],ink[3]))
                unit=model.SLIDERS[action][1]
                number=f'{value:.{tool["precision"]}f}' if abs(value)<10000 else f'{value:.3g}'
                _text(value_rect,number+unit,ink,scale,font=9)
                _text(reset_rect,'R',ink,scale,font=9)
            elif not label and action in _KEY_ICONS:
                _key_icon(rect,context,action,ink[3])
            elif not label and action in _LINE_ICONS:
                _tool_icon(rect,context,action,ink[3],accent,ink)
            elif not label:
                _glyph(rect,action if action else kind,(*accent[:3],ink[3]))
            else:
                _text(rect,label,(*accent[:3],ink[3]) if kind=='MENU' else ink,scale)
                if kind=='POPOUT': _quad((rect[0]+3*scale,rect[1]+2*scale,rect[2]-6*scale,1*scale),accent)
        if _menu_open(context):
            menu = _menu_items(context, items, band)
            if menu:
                xs = [r[0] for *_k, r in menu]; ys = [r[1] for *_k, r in menu]
                x1 = max(r[0] + r[2] for *_k, r in menu); y1 = max(r[1] + r[3] for *_k, r in menu)
                _quad((min(xs) - 2 * scale, min(ys) - 2 * scale, x1 - min(xs) + 4 * scale, y1 - min(ys) + 4 * scale),
                      (.08, .08, .08, .97))
                for _kind, key, label, rect in menu:
                    lit = key == stage or hover == (context.area.as_pointer(), 'STAGE_ITEM', key)
                    _quad(rect, tuple(widgets.inner_sel) if lit else tuple(widgets.inner))
                    if key == stage and key != 'ALL':
                        _quad((rect[0] + 3 * scale, rect[1] + 2 * scale, rect[2] - 6 * scale, 2 * scale),
                              _COLORS[model.stage_families(key)[0]])
                    _text(rect, label, (*(widgets.text_sel if lit else widgets.text)[:3], 1), scale)
        rows = _list_layout(context, row)
        if rows:
            xs = [r[0] for *_k, r in rows]; ys = [r[1] for *_k, r in rows]
            x1 = max(r[0] + r[2] for *_k, r in rows); y1 = max(r[1] + r[3] for *_k, r in rows)
            _quad((min(xs) - 2 * scale, min(ys) - 2 * scale, x1 - min(xs) + 4 * scale, y1 - min(ys) + 4 * scale),
                  (.08, .08, .08, .97))
            for kind, key, label, rect in rows:
                if kind == 'GAP':
                    _quad((rect[0] + 6 * scale, rect[1] + rect[3] / 2, rect[2] - 12 * scale, 1), (.3, .3, .3, 1))
                    continue
                if kind == 'HEAD':
                    color = _COLORS.get(key, (*widgets.text[:3], .6))
                    _text(rect, label, (*color[:3], 1), scale, left=True)
                    continue
                lit = hover == (context.area.as_pointer(), 'LIST_' + kind, key)
                if lit:
                    _quad(rect, tuple(widgets.inner_sel))
                dim = kind == 'RUN' and unavailable(key)
                ink_row = (*(widgets.text_sel if lit else widgets.text)[:3], .45 if dim else 1)
                _text((rect[0] + 8 * scale, rect[1], rect[2] - 8 * scale, rect[3]), label, ink_row, scale, left=True)
        # Thin separator on the edge facing the animation canvas.
        _quad((band[0], band[1]+band[3]-1, band[2], 1), (*widgets.outline[:3], 1))
        if active and active.mode=='POPOUT' and active._moved:
            sticky=getattr(active,'_sticky',False); extra=14*scale if sticky else 0.
            (x,y,width,height),track=popout_geometry(context.region.width,context.region.height,band,active.track_x,scale,extra)
            extra = track[1] - y - 5 * scale
            accent=_COLORS[FAMILY[active.action][0]]
            _quad((x,y,width,height),(*background[:3],1))
            _quad((x,y,width,1),accent)
            _text((x+5*scale,y+23*scale+extra,width-10*scale,18*scale),model.SLIDERS[active.action][0],(*widgets.text[:3],1),scale,left=True)
            _track(track,active.value,active._tool,accent)
            if extra > 0:
                _text((x+5*scale,y+2*scale,width-10*scale,12*scale),'Drag to adjust \u00b7 double-click or click away to apply \u00b7 Esc cancels',
                      (*widgets.text[:3],.6),scale,font=9,left=True)
            _text((x+width-60*scale,y+3*scale+extra,55*scale,20*scale),f'{active.value:.{active._tool["precision"]}f}'+model.SLIDERS[active.action][1],(*widgets.text[:3],1),scale,font=10)
        if not active and hover and not _menu_open(context) and not _list_open(context) and time.monotonic() - _hover_started.get(pointer, float("inf")) > .6:
            item = next((item for item in items if (item[0], item[1]) == hover[1:]), None)
            if item:
                paragraphs = _shape_tooltip(context, item, _tooltip_paragraphs(context, item, row, unavailable))
                blf.size(0, round(11 * scale))
                line_h, pad = 15 * scale, 7 * scale
                lines, y, width, height = _fit_hover_help(
                    paragraphs, context.region.width, context.region.height, band,
                    lambda text: blf.dimensions(0, text)[0], scale)
                if lines:
                    x = max(0, min(item[3][0], context.region.width-width))
                    # The playhead is drawn over add-on drawing; keep the box clear of it.
                    try:
                        head = context.region.view2d.view_to_region(context.scene.frame_current, 0, clip=False)[0]
                    except (AttributeError, TypeError):
                        head = None
                    if head is not None and x - 3*scale <= head <= x + width + 3*scale:
                        right, left = head + 4*scale, head - 4*scale - width
                        if right + width <= context.region.width:
                            x = right
                        elif left >= 0:
                            x = left
                    _quad((x, y, width, height), (.06, .06, .06, .97))
                    colors = {'TITLE': (1, 1, 1, 1), 'BODY': (.92, .92, .92, 1),
                              'DETAIL': (.70, .70, .70, 1), 'WARNING': (1, .72, .35, 1)}
                    for index, (line, role) in enumerate(lines):
                        blf.color(0, *colors.get(role, colors['BODY']))
                        blf.position(0, x+pad, y+height-pad-(index+1)*line_h+4*scale, 0)
                        blf.draw(0, line)
    finally:
        gpu.state.blend_set(old_blend)


class ANIMASSIST_OT_timeline_overlay_events(bpy.types.Operator):
    bl_idname = "animassist.timeline_overlay_events"
    bl_label = "Anim Assist Timeline Row Input"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context):
        from . import timeline_strip as tools
        return tools.is_timeline(context.area) and bool(context.region) and context.region.type == "WINDOW" and tools._enabled()

    def invoke(self, context, event):
        return self.handle_event(context, event, _toolbar_row(context))

    def handle_event(self, context, event, row):
        items, band = row.items, row.band
        if not items:
            return {"PASS_THROUGH"}
        point = (event.mouse_x - context.region.x, event.mouse_y - context.region.y)
        hit = _inside(band, point)
        pointer = context.window.as_pointer()
        menu = _menu_items(context, items, band) if _menu_open(context) else []
        in_menu = next((item for item in menu if _inside(item[3], point)), None)
        found = in_menu or (next((item for item in items if _inside(item[3], point)), None) if hit else None)
        hover = (context.area.as_pointer(), found[0], found[1]) if found else None
        previous = _hover.get(pointer)
        if previous != hover:
            _hover[pointer] = hover
            _hover_started[pointer] = time.monotonic()
            context.area.tag_redraw()
            if previous and previous[0] != context.area.as_pointer():
                # Moving directly into another Timeline must erase the old box.
                for area in context.window.screen.areas:
                    if area.as_pointer() == previous[0]:
                        area.tag_redraw()
                        break
            if hover:
                epoch, window, expected = _epoch, context.window, hover
                def tooltip_redraw():
                    if epoch is _epoch:
                        try:
                            if _hover.get(window.as_pointer()) == expected:
                                for area in window.screen.areas:
                                    if area.as_pointer() == expected[0]:
                                        area.tag_redraw()
                        except ReferenceError:
                            pass
                    return None
                bpy.app.timers.register(tooltip_redraw, first_interval=.65)
        rows = _list_layout(context, row)
        if rows:
            in_row = next((r for r in rows if r[0] not in {'HEAD', 'GAP'} and _inside(r[3], point)), None)
            row_hover = (context.area.as_pointer(), 'LIST_' + in_row[0], in_row[1]) if in_row else None
            if _hover.get(pointer) != row_hover:
                _hover[pointer] = row_hover
                context.area.tag_redraw()
            if event.type == 'MOUSEMOVE':
                return {'FINISHED'}
            if event.type == 'ESC' or event.type == 'RIGHTMOUSE':
                _close_row_menu(context)
                return {'FINISHED'}
            if event.type == 'LEFTMOUSE':
                state = _list_open(context)
                if in_row is None:
                    box = (min(r[3][0] for r in rows), min(r[3][1] for r in rows),
                           max(r[3][0] + r[3][2] for r in rows) - min(r[3][0] for r in rows),
                           max(r[3][1] + r[3][3] for r in rows) - min(r[3][1] for r in rows))
                    if not _inside(box, point):
                        if found and found[0] in {'MENU', 'MORE'} and (found[0], found[1]) != state['opener']:
                            _open_row_menu(context, found[0], found[1])  # another family button switches lists
                        else:
                            _close_row_menu(context)  # click away (the opener included) closes
                    return {'FINISHED'}
                kind, key = in_row[0], in_row[1]
                if kind == 'FAMILY':
                    state.update(view=('FAMILY', key), back=True); context.area.tag_redraw()
                elif kind == 'BACK':
                    state.update(view=('MORE', ''), back=False); context.area.tag_redraw()
                elif kind == 'RUN':
                    from . import timeline_strip as tools
                    reason = tools._unavailable(context, context.area, key)
                    if reason:
                        self.report({'WARNING'}, reason)  # stays open so another tool can be chosen
                    else:
                        _close_row_menu(context)
                        bpy.ops.animassist.timeline_tool('INVOKE_DEFAULT', action=key, canvas_undo=True)
                elif kind == 'OPTIONS':
                    _close_row_menu(context)
                    bpy.ops.wm.call_panel('INVOKE_DEFAULT', name=f'ANIMASSIST_PT_timeline_options_{key}')
                elif kind == 'HOME':
                    _close_row_menu(context)
                    bpy.ops.animassist.open_home('INVOKE_DEFAULT')
                return {'FINISHED'}
            return {'FINISHED'}
        if menu and event.type == "ESC":
            _close_stage_menu(context)
            return {"FINISHED"}
        if menu and event.type in {"LEFTMOUSE", "RIGHTMOUSE"}:
            # While open: pick a stage, or close on any other click in this Timeline
            # (including the stage button itself) without acting on what is underneath.
            _close_stage_menu(context)
            if in_menu and event.type == "LEFTMOUSE":
                bpy.ops.animassist.timeline_stage(stage=in_menu[1])
            return {"FINISHED"}
        if event.type == "ESC":
            return {"CANCELLED", "PASS_THROUGH"}
        if event.type == "MOUSEMOVE":
            return {"FINISHED"} if hit else {"PASS_THROUGH"}
        if not hit:
            return {"CANCELLED", "PASS_THROUGH"}
        if (event.type in {'WHEELUPMOUSE','WHEELDOWNMOUSE'} and event.ctrl and found
                and found[0] in {'STAGE','STAGE_CYCLE'}):
            bpy.ops.animassist.timeline_stage(step=1 if event.type=='WHEELDOWNMOUSE' else -1)
            return {'FINISHED'}
        if event.type=='RIGHTMOUSE' and found:
            action=_tool_action(found[0],found[1])
            if action:
                bpy.ops.animassist.tool_settings('INVOKE_DEFAULT',action=action)
                return {'FINISHED'}
        if event.type == "LEFTMOUSE" and found and found[0] in {'MENU', 'MORE'}:
            _open_row_menu(context, found[0], found[1])  # one click opens; stays open
            return {"FINISHED"}
        if event.type == "LEFTMOUSE" and found and found[0] == 'STAGE_CYCLE':
            _close_row_menu(context)
            _stage_menu[pointer] = context.area.as_pointer()  # one click opens; stays open
            context.area.tag_redraw()
            return {"FINISHED"}
        if event.type == "LEFTMOUSE" and found:
            action=_tool_action(found[0],found[1])
            from . import timeline_strip as tools
            reason=tools._unavailable(context,context.area,action) if action else ''
            if reason:
                self.report({'WARNING'},reason)
            elif found[0] in {'SLIDER','POPOUT'}:
                _slider_controls(context,point,found,context.preferences.system.ui_scale,row.view[1])
            elif found[0]=='PRESET':
                value=float(found[1].split(':',1)[1])
                result=bpy.ops.animassist.timeline_slider('EXEC_DEFAULT',action=action,value=value,preset=True)
                if 'FINISHED' in result: bpy.ops.ed.undo_push(message='Preset '+model.SLIDERS[action][0])
            else:
                bpy.ops.animassist.overlay_control("INVOKE_DEFAULT", kind=found[0], key=found[1])
            context.area.tag_redraw()
        return {"FINISHED"}


def _open_settings_after_click(window, area, region):
    epoch = _epoch

    def open_settings():
        if epoch is _epoch:
            try:
                if (any(a == area for a in window.screen.areas)
                        and any(r == region for r in area.regions)):
                    with bpy.context.temp_override(window=window, area=area, region=region):
                        bpy.ops.animassist.toolbar_settings("INVOKE_DEFAULT")
            except ReferenceError:
                pass  # The window or editor closed before the callback.
        return None

    # Let the pointer handler finish before adding the native popup handler.
    bpy.app.timers.register(open_settings, first_interval=0)


class ANIMASSIST_OT_timeline_pointer(bpy.types.Operator):
    bl_idname = "animassist.timeline_pointer"
    bl_label = "Anim Assist Timeline Pointer Input"
    bl_options = {"INTERNAL"}

    def invoke(self, context, _event):
        self.epoch = _epoch
        self.settings_press = None
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if self.epoch is not _epoch:
            return {"CANCELLED", "PASS_THROUGH"}
        if event.type == "WINDOW_DEACTIVATE":
            self.settings_press = None
        moving = event.type in {"MOUSEMOVE", "INBETWEEN_MOUSEMOVE"}
        if not moving and (event.type != "LEFTMOUSE" or event.value not in {"PRESS", "RELEASE"}):
            return {"PASS_THROUGH"}
        settings_press = self.settings_press
        if not moving:
            self.settings_press = None
        if not moving and event.value == "RELEASE" and settings_press is None:
            return {"PASS_THROUGH"}
        from . import timeline_settings, timeline_strip as tools
        if not tools._enabled() or timeline_settings.editor(context) is not None:
            return {"PASS_THROUGH"}
        # Window modal handlers run before native scene strip gizmos can hover
        # or show tooltips through the toolbar's drawn overlay.
        # Resolve the editor under this event even immediately after resizing.
        window = context.window
        for area in window.screen.areas:
            if not tools.is_timeline(area):
                continue
            for region in area.regions:
                if region.type != "WINDOW" or not _inside(
                    (region.x, region.y, region.width, region.height),
                    (event.mouse_x, event.mouse_y),
                ):
                    continue
                with context.temp_override(window=window, area=area, region=region):
                    row = _toolbar_row(context)
                    point = (event.mouse_x - region.x, event.mouse_y - region.y)
                    if moving:
                        if event.type == "MOUSEMOVE":
                            result = ANIMASSIST_OT_timeline_overlay_events.handle_event(
                                self, context, event, row)
                            return {"PASS_THROUGH"} if "PASS_THROUGH" in result else {"RUNNING_MODAL"}
                        return {"RUNNING_MODAL"} if _inside(row.band, point) else {"PASS_THROUGH"}
                    if event.value == "RELEASE" or not (_menu_open(context) or _list_open(context)):
                        items = row.items
                        settings_hit = any(kind == "SETTINGS" and _inside(rect, point)
                                           for kind, _key, _label, rect in items)
                        if event.value == "RELEASE":
                            if settings_hit and settings_press == region.as_pointer():
                                _open_settings_after_click(window, area, region)
                            return {"RUNNING_MODAL"}
                        if settings_hit:
                            # Open on release so the native popup doesn't see
                            # the tail of the click that created it.
                            self.settings_press = region.as_pointer()
                            return {"RUNNING_MODAL"}
                    result = ANIMASSIST_OT_timeline_overlay_events.handle_event(self, context, event, row)
                if "PASS_THROUGH" not in result:
                    return {"RUNNING_MODAL"}
                return {"PASS_THROUGH"}
        return {"RUNNING_MODAL"} if event.value == "RELEASE" else {"PASS_THROUGH"}


class ANIMASSIST_OT_clear_timeline_hover(bpy.types.Operator):
    bl_idname = "animassist.clear_timeline_hover"
    bl_label = "Clear Timeline Tool Hover"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context):
        from . import timeline_strip as tools
        if not context.window:
            return False
        pointer = context.window.as_pointer()
        if not (_hover.get(pointer) or _stage_menu.get(pointer) or _row_menu.get(pointer)):
            return False
        return not (tools.is_timeline(context.area) and context.region
                    and context.region.type == "WINDOW")

    def invoke(self, context, event):
        _hover.pop(context.window.as_pointer(), None)
        if event.type == "LEFTMOUSE":
            _stage_menu.pop(context.window.as_pointer(), None)
            _row_menu.pop(context.window.as_pointer(), None)
        for area in context.window.screen.areas:
            area.tag_redraw()
        return {"CANCELLED", "PASS_THROUGH"}


class ANIMASSIST_OT_close_stage_menu(bpy.types.Operator):
    bl_idname = "animassist.close_stage_menu"
    bl_label = "Close Anim Assist Stage List"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context):
        return bool(context.window and (_stage_menu.get(context.window.as_pointer())
                                        or _row_menu.get(context.window.as_pointer())))

    def invoke(self, context, _event):
        _close_row_menu(context)
        _close_stage_menu(context)
        return {"FINISHED"}


def _restore_timeline_height(window, area):
    region = next((r for r in area.regions if r.type == "WINDOW"), None)
    if region is None or region.height <= 0:
        return
    _base, height, scrollbar, keys_at_top = _row_geometry(area, bpy.context.preferences.system)
    missing = ceil(height + scrollbar + keys_at_top - region.height)
    pointer = area.as_pointer()
    if missing <= 0:
        _resize_attempts.pop(pointer, None)
        return
    x, y = area.x + area.width // 2, area.y + area.height
    above = next((a for a in window.screen.areas if a != area and abs(a.y - y - 1) <= 3
                  and a.x <= x < a.x + a.width), None)
    if above is None:
        return
    # Don't keep nudging a divider whose other side has reached its native limit.
    size = (x, y, region.height, above.as_pointer(), above.height, missing)
    if _resize_attempts.get(pointer) == size:
        return
    with bpy.context.temp_override(window=window, area=area):
        if bpy.ops.screen.area_move.poll():
            _resize_attempts[pointer] = size
            bpy.ops.screen.area_move(x=x, y=y, delta=missing)


def _start_windows():
    if _handle is None:
        return None
    from . import timeline_strip as tools
    from ..prefs import get_prefs, timeline_record
    prefs = get_prefs()
    if prefs and not prefs.timeline_layouts_json:
        timeline_record(prefs, initialize=True)
    if prefs and not prefs.timeline_canvas_row_initialized:
        # Before 12.6.1, False meant "use the existing header", not hide tools.
        # Apply the new visible placement once; later explicit hiding persists.
        prefs.timeline_toolbar_row = True
        prefs.timeline_canvas_row_initialized = True
    for window in bpy.context.window_manager.windows:
        if tools._enabled():
            window_id = window.as_pointer()
            if window_id not in _input_windows and any(tools.is_timeline(area) for area in window.screen.areas):
                with bpy.context.temp_override(window=window):
                    if "RUNNING_MODAL" in bpy.ops.animassist.timeline_pointer("INVOKE_DEFAULT"):
                        _input_windows.add(window_id)
            # The native resize owns the divider until the mouse is released.
            if not any(op.bl_idname == "SCREEN_OT_area_move" for op in window.modal_operators):
                for area in window.screen.areas:
                    if tools.is_timeline(area):
                        _restore_timeline_height(window, area)
    return 1.0


def _view_menu(self, context):
    from . import timeline_strip as tools
    from ..prefs import get_prefs
    if tools.is_timeline(context.area):
        prefs = get_prefs(context)
        if prefs:
            self.layout.separator()
            self.layout.prop(prefs, "timeline_toolbar_row", text="Show Anim Assist Tool Row")
            row = self.layout.row()
            row.operator_context = "INVOKE_DEFAULT"
            row.operator("animassist.toolbar_settings", text="Anim Assist Toolbar Settings")
            if hasattr(context.workspace, STAGE_PROPERTY):
                self.layout.prop_menu_enum(context.workspace, STAGE_PROPERTY, text="Anim Assist Stage")
            self.layout.menu("ANIMASSIST_MT_timeline_tools", text="Anim Assist Tools")


@bpy.app.handlers.persistent
def _load_post(_unused):
    global _epoch
    _epoch = object()
    _hover.clear()
    _stage_menu.clear()
    _hover_started.clear()
    _resize_attempts.clear()
    _input_windows.clear()


_CLASSES = (ANIMASSIST_OT_overlay_control, ANIMASSIST_MT_timeline_stage, ANIMASSIST_OT_timeline_stage,
            ANIMASSIST_OT_close_stage_menu,
            ANIMASSIST_OT_timeline_overlay_events, ANIMASSIST_OT_timeline_pointer,
            ANIMASSIST_OT_clear_timeline_hover)


def _stage_update(workspace, _context):
    # Tabs, Toolbar Settings and the View menu all set the stage; redraw every
    # Timeline showing this workspace so the row follows immediately.
    from . import timeline_strip as tools, timeline_settings
    timeline_settings.on_stage_changed(workspace)
    manager = getattr(bpy.context, "window_manager", None)
    for window in getattr(manager, "windows", ()):
        if window.workspace == workspace:
            for area in window.screen.areas:
                if tools.is_timeline(area):
                    area.tag_redraw()


def _stage_items():
    # Explicit, permanent numbers: the .blend stores the number, so reordering
    # STAGES later must not change saved stages.
    return [(key, label, "The All overview of every tool family" if families is None
             else f"The {label} toolset: {_family_labels(key)}", model.STAGE_NUMBERS[key])
            for key, label, families in model.STAGES]


def register():
    global _handle, _epoch
    _epoch = object()
    from ..core import explainers
    for cls in _CLASSES:
        explainers.register_class(cls)
    setattr(bpy.types.WorkSpace, STAGE_PROPERTY, EnumProperty(
        name="Anim Assist Stage", description="Tool families the Timeline band shows in this workspace",
        items=_stage_items(), default="ALL", update=_stage_update))
    if not bpy.app.background:
        _handle = bpy.types.SpaceDopeSheetEditor.draw_handler_add(_draw, (), "WINDOW", "POST_PIXEL")
        bpy.types.DOPESHEET_MT_view.append(_view_menu)
        config = bpy.context.window_manager.keyconfigs.addon
        if config:
            screen = config.keymaps.new(name="Screen", space_type="EMPTY", region_type="WINDOW")
            item = screen.keymap_items.new(ANIMASSIST_OT_clear_timeline_hover.bl_idname,
                                           type="MOUSEMOVE", value="ANY")
            _keymaps.append((screen, item))
            item = screen.keymap_items.new(ANIMASSIST_OT_clear_timeline_hover.bl_idname,
                                           type="LEFTMOUSE", value="PRESS", any=True)
            _keymaps.append((screen, item))
            # Esc closes an open stage list from anywhere in the window.
            item = screen.keymap_items.new(ANIMASSIST_OT_close_stage_menu.bl_idname, type="ESC", value="PRESS")
            _keymaps.append((screen, item))
            for name in ("Dopesheet", "Dopesheet Generic"):
                keymap = config.keymaps.new(name=name, space_type="DOPESHEET_EDITOR", region_type="WINDOW")
                for event_type in ("LEFTMOUSE", "RIGHTMOUSE", "MIDDLEMOUSE", "WHEELUPMOUSE", "WHEELDOWNMOUSE"):
                    item = keymap.keymap_items.new(ANIMASSIST_OT_timeline_overlay_events.bl_idname,
                                                  type=event_type, value="PRESS", any=True)
                    _keymaps.append((keymap, item))
                item = keymap.keymap_items.new(ANIMASSIST_OT_timeline_overlay_events.bl_idname,
                                              type="ESC", value="PRESS")
                _keymaps.append((keymap, item))
        bpy.app.handlers.load_post.append(_load_post)
        from ..operators.timeline_slider_ops import cancel_active
        bpy.app.handlers.load_pre.append(cancel_active)
        bpy.app.handlers.undo_pre.append(cancel_active)
        bpy.app.timers.register(_start_windows, first_interval=.1, persistent=True)


def unregister():
    global _handle, _epoch
    _epoch = object()
    from ..operators.timeline_slider_ops import cancel_active
    cancel_active(finalize=True)
    for handlers in (bpy.app.handlers.load_pre,bpy.app.handlers.undo_pre):
        if cancel_active in handlers: handlers.remove(cancel_active)
    if _handle is not None:
        bpy.types.SpaceDopeSheetEditor.draw_handler_remove(_handle, "WINDOW")
        _handle = None
        bpy.types.DOPESHEET_MT_view.remove(_view_menu)
        if _load_post in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(_load_post)
        if bpy.app.timers.is_registered(_start_windows):
            bpy.app.timers.unregister(_start_windows)
    _resize_attempts.clear()
    _input_windows.clear()
    _hover.clear()
    _stage_menu.clear()
    _hover_started.clear()
    for keymap, item in _keymaps:
        keymap.keymap_items.remove(item)
    _keymaps.clear()
    if hasattr(bpy.types.WorkSpace, STAGE_PROPERTY):
        delattr(bpy.types.WorkSpace, STAGE_PROPERTY)
    for cls in reversed(_CLASSES):
        if "bl_rna" in cls.__dict__:
            bpy.utils.unregister_class(cls)
