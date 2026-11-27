"""BoneCraft — control-picker layout core (pure, no ``bpy``).

The headlessly-testable heart of the rig-UI / control-picker layer (R7):
auto-generate a clickable layout from a rig's bone collections, round-trip it
as BoneCraft-native JSON, build selection sets, and mirror a selection by the
BoneCraft bone-naming convention (``-L`` <-> ``-R``).

Clean-room: original BoneCraft layout schema and grouping; no third-party
picker format or asset is referenced.
"""
import json

LAYOUT_VERSION = 1

# Collections that hold animator controls (Deform/MCH are not pickable).
PICKER_GROUPS = ("Root", "Controls", "FK", "IK", "Fingers", "Tail",
                 "Spline", "Face")

# Per-group control colour (RGB 0..1) — BoneForge-native conventions.
GROUP_COLORS = {
    "Root": [0.95, 0.95, 0.95],
    "Controls": [0.85, 0.80, 0.30],
    "FK": [0.30, 0.60, 0.90],
    "IK": [0.90, 0.50, 0.20],
    "Fingers": [0.60, 0.50, 0.90],
    "Tail": [0.70, 0.60, 0.40],
    "Spline": [0.50, 0.70, 0.70],
    "Face": [0.20, 0.80, 0.55],
}


def mirror_bone_name(name):
    """Swap the BoneCraft side suffix (``upperarm.fk-L`` <-> ``upperarm.fk-R``)."""
    if name.endswith("-L"):
        return name[:-2] + "-R"
    if name.endswith("-R"):
        return name[:-2] + "-L"
    return name


def mirror_selection(names):
    """Mirror a list of control/bone names; central names map to themselves."""
    return [mirror_bone_name(n) for n in names]


def auto_generate_layout(collections):
    """Build a picker layout from ``{collection_name: [bone_names]}``.

    Lays controls out in a grid: one row per picker group, one column per bone
    (sorted), coloured by group. Deform/MCH collections are ignored.
    """
    controls = []
    row = 0
    for group in PICKER_GROUPS:
        bones = sorted(collections.get(group, []))
        if not bones:
            continue
        for col, bone in enumerate(bones):
            controls.append({
                "id": bone,
                "bone": bone,
                "group": group,
                "color": list(GROUP_COLORS.get(group, [0.5, 0.5, 0.5])),
                "rect": [float(col), float(row), 0.9, 0.9],
            })
        row += 1
    return {"version": LAYOUT_VERSION, "controls": controls}


def validate_layout(layout):
    """Return a list of structural problems ([] == valid)."""
    problems = []
    if not isinstance(layout, dict):
        return ["layout is not an object"]
    if layout.get("version") != LAYOUT_VERSION:
        problems.append("unexpected version: %r" % layout.get("version"))
    controls = layout.get("controls")
    if not isinstance(controls, list):
        return problems + ["'controls' must be a list"]
    seen = set()
    for c in controls:
        cid = c.get("id")
        if cid in seen:
            problems.append("duplicate control id: %r" % cid)
        seen.add(cid)
        if "bone" not in c:
            problems.append("control %r missing 'bone'" % cid)
        rect = c.get("rect")
        if not (isinstance(rect, list) and len(rect) == 4):
            problems.append("control %r has a bad rect" % cid)
    return problems


def find_control(layout, control_id):
    """Return the control dict for ``control_id``, or None."""
    for control in layout.get("controls", []):
        if control.get("id") == control_id:
            return control
    return None


def _copy_layout(layout):
    return layout_from_json(layout_to_json(layout))


def _snap_value(value, grid):
    grid = float(grid) if grid else 0.0
    if grid <= 0.0:
        return float(value)
    return round(float(value) / grid) * grid


def _snap_rect(rect, grid):
    return [_snap_value(v, grid) for v in rect]


def edit_control_rect(layout, control_id, dx=0.0, dy=0.0, dw=0.0, dh=0.0,
                      snap=False, grid=1.0, min_size=0.1):
    """Return a copy with one control rect moved/resized."""
    data = _copy_layout(layout)
    control = find_control(data, control_id)
    if control is None:
        raise KeyError(control_id)
    rect = list(control.get("rect", [0.0, 0.0, 0.9, 0.9]))
    if len(rect) != 4:
        raise ValueError("control %r has a bad rect" % control_id)
    rect = [float(v) for v in rect]
    rect[0] += float(dx)
    rect[1] += float(dy)
    rect[2] = max(float(min_size), rect[2] + float(dw))
    rect[3] = max(float(min_size), rect[3] + float(dh))
    if snap:
        rect = _snap_rect(rect, grid)
        rect[2] = max(float(min_size), rect[2])
        rect[3] = max(float(min_size), rect[3])
    control["rect"] = rect
    return data


def move_control(layout, control_id, dx=0.0, dy=0.0, snap=False, grid=1.0):
    return edit_control_rect(layout, control_id, dx=dx, dy=dy,
                             snap=snap, grid=grid)


def resize_control(layout, control_id, dw=0.0, dh=0.0, snap=False, grid=1.0,
                   min_size=0.1):
    return edit_control_rect(layout, control_id, dw=dw, dh=dh, snap=snap,
                             grid=grid, min_size=min_size)


def relabel_control(layout, control_id, label):
    """Return a copy with a display label stored on the control."""
    data = _copy_layout(layout)
    control = find_control(data, control_id)
    if control is None:
        raise KeyError(control_id)
    control["label"] = str(label)
    return data


def layout_to_json(layout):
    return json.dumps(layout, indent=2, sort_keys=True)


def layout_from_json(text):
    return json.loads(text)


def control_bones(layout):
    """The pose-bone names a layout drives, in order."""
    return [c["bone"] for c in layout.get("controls", [])]


def bones_in_group(layout, group):
    return [c["bone"] for c in layout.get("controls", []) if c.get("group") == group]
