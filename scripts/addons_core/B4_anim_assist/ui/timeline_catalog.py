"""Existing actions exposed in the add-on Timeline toolbar, grouped by task.

Concept mapping: docs/anim_assist/releases/12.3.0/animbot-matches.md.
Names describe our actual scope; they do not promise animBot feature parity.
All entries are day-to-day actions (top tier). Bake/proxy settings remain in
their existing sidebar home (mid tier); setup and file procedures are excluded.
"""

from ..constants import BREAKDOWN_ANCHOR_HINT

# (existing operator suffix, fixed arguments, menu label). No scene overrides.
ACTIONS = {
    "B25": ("breakdown_percentage", {"percent": 25}, "25% Breakdown"),
    "B50": ("breakdown_percentage", {"percent": 50}, "50% Breakdown"),
    "B75": ("breakdown_percentage", {"percent": 75}, "75% Breakdown"),
    "DRAG": ("modal_drag_breakdown", {}, "Drag Breakdown"),
    "PUSH_PREV": ("breakdown_push_prev", {}, "Push Previous"),
    "PULL_PREV": ("breakdown_pull_prev", {}, "Pull Previous"),
    "PULL_NEXT": ("breakdown_pull_next", {}, "Pull Next"),
    "PUSH_NEXT": ("breakdown_push_next", {}, "Push Next"),
    "T80": ("p6_scale_keys", {"scale_factor": 0.8}, "Scale Key Spacing to 80%"),
    "T90": ("p6_scale_keys", {"scale_factor": 0.9}, "Scale Key Spacing to 90%"),
    "T110": ("p6_scale_keys", {"scale_factor": 1.1}, "Scale Key Spacing to 110%"),
    "T120": ("p6_scale_keys", {"scale_factor": 1.2}, "Scale Key Spacing to 120%"),
    "RIPPLE": ("p6_ripple_forward", {}, "Ripple Forward"),
    "RANGE": ("select_frame_range", {}, "Select Frame Range"),
    "ALL": ("select_all_visible", {}, "Select All Visible Keys"),
    "ENDS": ("select_first_last", {}, "Select First and Last Keys"),
    "OFFSET": ("anim_offset", {}, "Offset Active Action"),
    "INBETWEEN": ("inbetween_selected_gap", {}, "Add Inbetween in Selected Gap"),
    "INBETWEENS": ("inbetween_distribute", {}, "Distribute Inbetweens in Selected Gap"),
    "NEIGHBORS": ("blend_neighbor", {}, "Blend to Neighbors (Drag)"),
    "FRAME": ("blend_frame", {}, "Blend to Frame (Drag)"),
    "EASE": ("ease_to_ease", {}, "Blend to Ease (Drag)"),
    "AMPLIFY": ("push_pull", {}, "Scale Values from Reference (Drag)"),
    "SMOOTH": ("smooth_keys", {}, "Smooth Keys (Drag)"),
    "REFERENCE": ("set_reference_frame", {}, "Set Reference Frame from Playhead"),
    "HANDLE_AUTO": ("set_handle_type", {"handle_type": "AUTO"}, "Auto Handles"),
    "HANDLE_CLAMPED": ("set_handle_type", {"handle_type": "AUTO_CLAMPED"}, "Auto Clamped Handles"),
    "HANDLE_VECTOR": ("set_handle_type", {"handle_type": "VECTOR"}, "Vector Handles"),
    "HANDLE_ALIGNED": ("set_handle_type", {"handle_type": "ALIGNED"}, "Aligned Handles"),
    "HANDLE_FREE": ("set_handle_type", {"handle_type": "FREE"}, "Free Handles"),
    "TO_SPLINE": ("batch_interpolation", {"interp_type": "BEZIER"}, "Set Selected Keys to Spline (Bezier)"),
    "TO_STEPPED": ("batch_interpolation", {"interp_type": "CONSTANT"}, "Set Selected Keys to Stepped (Constant)"),
    "NUDGE_LEFT": ("move_keys", {"offset": -1}, "Nudge Selected Keys -1 Frame"),
    "NUDGE_RIGHT": ("move_keys", {"offset": 1}, "Nudge Selected Keys +1 Frame"),
    "SCALE_DRAG": ("p6_modal_scale", {}, "Scale Key Timing (Drag)"),
    "OFFSET_DRAG": ("p6_modal_offset", {}, "Offset Action Timing (Drag)"),
    "OFFSET_ACTION": ("p6_offset_keys", {}, "Offset Action Timing"),
    "INSERT_TIME": ("p6_insert_time", {}, "Insert Time at Playhead"),
    "REMOVE_TIME": ("p6_remove_time", {}, "Remove Time and Keys at Playhead"),
    "DISTRIBUTE_TIME": ("p6_distribute_keys", {}, "Distribute Key Timing in Range"),
    "REVERSE": ("p6_reverse_keys", {}, "Reverse Key Timing in Range"),
    "SNAP": ("p6_snap_to_frames", {}, "Round Key Times"),
    "GROW_LEFT": ("select_neighbors", {"direction": "LEFT"}, "Grow Key Selection Left"),
    "GROW_RIGHT": ("select_neighbors", {"direction": "RIGHT"}, "Grow Key Selection Right"),
    "GROW_BOTH": ("select_neighbors", {"direction": "BOTH"}, "Grow Key Selection Both Sides"),
    "TYPE_KEYFRAME": ("set_key_type", {"key_type": "KEYFRAME"}, "Mark as Keyframe"),
    "TYPE_BREAKDOWN": ("set_key_type", {"key_type": "BREAKDOWN"}, "Mark as Breakdown"),
    "TYPE_HOLD": ("set_key_type", {"key_type": "MOVING_HOLD"}, "Mark as Moving Hold"),
    "TYPE_EXTREME": ("set_key_type", {"key_type": "EXTREME"}, "Mark as Extreme"),
    "TYPE_JITTER": ("set_key_type", {"key_type": "JITTER"}, "Mark as Jitter"),
    "SELECT_BREAKDOWNS": ("select_by_key_type", {"key_type": "BREAKDOWN"}, "Select Breakdown Keys"),
    "MIRROR_ACTIVE": ("p9_mirror_pose", {}, "Mirror Active Bone to Opposite"),
    "MIRROR_SELECTED": ("p9_mirror_selected", {}, "Mirror Selected Bones"),
    "MIRROR_FRAME": ("p9_mirror_frame", {}, "Mirror and Key Current Frame"),
    "MIRROR_RANGE": ("p9_mirror_range", {}, "Mirror and Key Preview or Playback Range"),
    "OPPOSITE": ("p9_select_opposite", {}, "Select Opposite of Active Bone"),
    "SWAP": ("p9_swap_poses", {}, "Swap Left/Right Poses"),
    "ALIGN": ("p8_match_selected_to_active", {}, "Align Selected Objects to Active"),
    "BAKE_STEP": ("p7_bake_step", {}, "Bake Object Transforms"),
    "SMART_BAKE": ("p7_smart_bake", {}, "Bake Object Transforms and Reduce"),
    "REDUCE": ("p7_reduce_keys", {}, "Reduce Keys"),
    "PROXY_TRANSLATION": ("p7_create_proxy", {"proxy_type": "TRANSLATION"}, "Create Object Translation Proxy"),
    "PROXY_ORIENTATION": ("p7_create_proxy", {"proxy_type": "ORIENTATION"}, "Create Object Orientation Proxy"),
    "PROXY_WORLD": ("p7_create_proxy", {"proxy_type": "WORLD_SPACE"}, "Create Object World-Space Proxy"),
    "PROXY_PARENT": ("p7_create_proxy", {"proxy_type": "PARENT_SPACE"}, "Create Object Parent-Space Proxy"),
    "BAKE_CLEANUP": ("p7_one_click_cleanup", {}, "Bake Session and Remove Proxies"),
    "BAKE_PREVIEW": ("p7_bake_preview", {}, "Bake Object Transforms in Preview Range"),
    "BAKE_INTEGER": ("p6_bake_timing", {}, "Bake Keys to Integer Frames"),
    "PROXY_BAKE": ("p7_one_click_proxy_bake", {}, "One-Click Translation Proxy and Bake"),
    "CLEANUP_ALL": ("p7_cleanup_all", {}, "Remove All Proxy Sessions"),
    "TRAIL_SHOW": ("p5_enable_overlay", {}, "Show World Motion Trails"),
    "TRAIL_TOGGLE": ("timeline_trails_toggle", {}, "Show or Hide World Motion Trails"),
    "TRAIL_HIDE": ("p5_disable_overlay", {}, "Hide World Motion Trails"),
    "TRAIL_REFRESH": ("p5_refresh_overlay", {}, "Refresh World Motion Trails"),
    "TRAIL_DIAGNOSE": ("p5_run_diagnostics", {}, "Diagnose Motion Arcs"),
    "OFFSET_MASK": ("anim_offset_toggle_mask", {}, "Toggle Anim Offset Mask"),
    "OFFSET_SCENE_RANGE": ("anim_offset_range_from_scene", {}, "Set Offset Mask from Scene Range"),
    "COPY_KEYS": ("copy_selected_keys", {}, "Copy Selected Keys with Handles"),
    "PASTE_KEYS": ("paste_keys_at_frame", {}, "Paste Keys at Copied Times"),
    "BOOKMARK_ADD": ("add_bookmark", {}, "Save Reference Bookmark"),
    "BOOKMARK_REMOVE": ("remove_bookmark", {}, "Remove Active Reference Bookmark"),
    "BOOKMARK_RECALL": ("recall_bookmark", {}, "Set Reference from Active Bookmark"),
    "MATCH_WORLD": ("p8_match_to_world", {}, "Match Object to World Origin"),
    "MATCH_PARENT": ("p8_match_to_parent", {}, "Match Object to Parent"),
    "MATCH_TARGET": ("p8_match_to_target", {}, "Match Active Object to Selected Target"),
    "MATCH_LOCATION": ("p8_match_location", {}, "Match Object Location to Selected Target"),
    "MATCH_ROTATION": ("p8_match_rotation", {}, "Match Object Rotation to Selected Target"),
    "MATCH_SCALE": ("p8_match_scale", {}, "Match Object Scale to Selected Target"),
    "MATCH_TRS": ("p8_match_trs", {}, "Match Object Transforms to Selected Target"),
    "MATCH_VISUAL": ("p8_match_visual_matrix", {}, "Match Object Evaluated Matrix"),
    "MATCH_LOCAL": ("p8_match_local_matrix", {}, "Match Object Local Matrix"),
    "SWITCH_SINGLE": ("p8_compensate_single", {}, "Switch Configured Rig Property and Compensate"),
    "SWITCH_RANGE": ("p8_compensate_multi", {}, "Switch and Key Configured Rig Property in Range"),
    "SWITCH_BOOL": ("p8_switch_bool", {}, "Toggle Configured Rig Boolean and Compensate"),
    "SWITCH_ENUM": ("p8_switch_enum", {}, "Set Configured Rig Integer and Compensate"),
    "SWITCH_INFLUENCE": ("p8_switch_influence", {}, "Set Configured Rig Influence and Compensate"),
}

# Fixed nudge presets run immediately through the existing undoable execute path.
EXECUTE_ACTIONS = {"NUDGE_LEFT", "NUDGE_RIGHT", "MIRROR_RANGE", "BOOKMARK_ADD"}

TIPS = {
    "NEIGHBORS": "Drag to blend selected keys toward the line between bounding neighbors. Esc restores the keys",
    "FRAME": "Drag selected keys toward their reference-frame value. Set the reference from the playhead first; Esc cancels",
    "EASE": "Drag selected keys from linear spacing toward eased spacing. Esc restores the keys",
    "AMPLIFY": "Drag to scale selected key values around the reference-frame value. This changes curve amplitude, not timing",
    "SMOOTH": "Drag selected keys toward neighboring averages; negative factors roughen the curve",
    "TRAIL_TOGGLE": "Show world motion trails in the 3D Viewport, or hide them when they are shown. The eye is filled while trails are on",
    "TO_SPLINE": "Set selected keys to Bezier interpolation so blocked poses play as smooth curves. Handle types are kept",
    "TO_STEPPED": "Set selected keys to Constant interpolation so each pose holds until the next key, for reviewing poses",
    "T80": "Scale key spacing to 80% around the Timing pivot: keys sit closer together, so the action plays faster",
    "T90": "Scale key spacing to 90% around the Timing pivot: keys sit closer together, so the action plays faster",
    "T110": "Scale key spacing to 110% around the Timing pivot: keys spread apart, so the action plays slower",
    "T120": "Scale key spacing to 120% around the Timing pivot: keys spread apart, so the action plays slower",
    "SCALE_DRAG": "Drag to scale key spacing around the Timing pivot. Below 100% keys sit closer (faster); above 100% they spread apart (slower)",
    "NUDGE_LEFT": "Move selected keys one frame earlier, carrying their handles",
    "NUDGE_RIGHT": "Move selected keys one frame later, carrying their handles",
    "OFFSET_ACTION": "Move key times in the active object's Action using its timing offset and range settings. This is not limited to selected keys",
    "OFFSET_DRAG": "Drag to move all key times in the active object's Action. Esc restores them; this does not keep key positions fixed",
    "REMOVE_TIME": "Remove the configured playhead time window, delete keys inside it, and shift later keys backward",
    "SNAP": "Round key times in the active Action to whole frames. This does not resample values to preserve poses",
    "ALIGN": "Match other selected objects to the active object's evaluated transform using your matching channel, offset and lock settings",
    "BAKE_STEP": "Bake the active object's evaluated transform using the existing bake range and Frame Step settings",
    "SMART_BAKE": "Bake the active object's evaluated transform, then reduce keys using the existing reduction tolerance",
    "RIPPLE": "Drag to preview shifting every key after the playhead later or earlier; release to apply, Esc restores. Earlier stops one frame after the playhead",
    "REDUCE": "Drag to preview removing keys whose deletion changes the curve by less than the tolerance; release to apply, Esc restores. As a button it uses the Smart Bake tolerance",
    "PROXY_WORLD": "Create a temporary helper using the existing Copy Transforms proxy setup",
    "BAKE_CLEANUP": "Bake the active proxy session's constrained objects and remove that session's helpers. Uses existing bake settings",
    "BAKE_PREVIEW": "Bake the active object's evaluated transform within the preview range using the existing Frame Step and channel settings",
    "BAKE_INTEGER": "Round sub-frame keys in the active object's Action to whole frames and keep a timing snapshot that Reset Timing restores. Same rounding as Round Key Times",
    "PROXY_BAKE": "Bake the active object's world motion to keys through a temporary translation proxy, then remove that proxy. Uses the bake range, Frame Step, channel and reduction settings; other proxy sessions are left alone",
    "CLEANUP_ALL": "Remove every Anim Assist proxy, proxy constraint and helper collection in this file, from all sessions. Baked keys stay",
    "PASTE_KEYS": "Paste copied absolute key times plus the paste offset onto matching Action names and curve paths; the playhead does not set the paste time",
}

GROUPS = (
    ("tween", "Tween", (
        "B25", "B50", "B75", "DRAG", None, "INBETWEEN", "INBETWEENS", None,
        "PUSH_PREV", "PULL_PREV", "PULL_NEXT", "PUSH_NEXT")),
    ("curves", "Curves", (
        "TO_SPLINE", "TO_STEPPED", None, "NEIGHBORS", "FRAME", "EASE", "AMPLIFY", "SMOOTH", "REFERENCE", None,
        "HANDLE_AUTO", "HANDLE_CLAMPED", "HANDLE_VECTOR", "HANDLE_ALIGNED", "HANDLE_FREE", None,
        "BOOKMARK_ADD", "BOOKMARK_RECALL", "BOOKMARK_REMOVE")),
    ("timing", "Timing", (
        "NUDGE_LEFT", "NUDGE_RIGHT", None, "T80", "T90", "T110", "T120", "SCALE_DRAG",
        "OFFSET_DRAG", "OFFSET_ACTION", None, "RIPPLE", "INSERT_TIME", "REMOVE_TIME",
        "DISTRIBUTE_TIME", "REVERSE", "SNAP")),
    ("keys", "Keys", (
        "ALL", "RANGE", "ENDS", None, "GROW_LEFT", "GROW_RIGHT", "GROW_BOTH", None,
        "TYPE_KEYFRAME", "TYPE_BREAKDOWN", "TYPE_HOLD", "TYPE_EXTREME", "TYPE_JITTER",
        "SELECT_BREAKDOWNS", None, "COPY_KEYS", "PASTE_KEYS")),
    ("pose", "Pose", (
        "MIRROR_ACTIVE", "MIRROR_SELECTED", "MIRROR_FRAME", "MIRROR_RANGE", None,
        "OPPOSITE", "SWAP", "ALIGN", None,
        "MATCH_WORLD", "MATCH_PARENT", "MATCH_TARGET", "MATCH_LOCATION", "MATCH_ROTATION",
        "MATCH_SCALE", "MATCH_TRS", "MATCH_VISUAL", "MATCH_LOCAL", None,
        "SWITCH_SINGLE", "SWITCH_RANGE", "SWITCH_BOOL", "SWITCH_ENUM", "SWITCH_INFLUENCE")),
    ("bake", "Bake", (
        "BAKE_STEP", "BAKE_PREVIEW", "SMART_BAKE", "REDUCE", "BAKE_INTEGER", None, "PROXY_BAKE", "PROXY_TRANSLATION",
        "PROXY_ORIENTATION", "PROXY_WORLD", "PROXY_PARENT", "BAKE_CLEANUP", "CLEANUP_ALL")),
    ("motion", "Motion", (
        "TRAIL_TOGGLE", "TRAIL_SHOW", "TRAIL_HIDE", "TRAIL_REFRESH", "TRAIL_DIAGNOSE", None,
        "OFFSET", "OFFSET_MASK", "OFFSET_SCENE_RANGE")),
)

# Shared by inline buttons, family menus and More. Scene state never chooses
# positions. More deliberately contains all shortcuts, including inline ones.
QUICK_GROUPS = (
    ("tween", "Tween", ("B25", "B50", "B75", "DRAG")),
    ("curves", "Curves", ("PUSH_PREV", "PULL_PREV", "PULL_NEXT", "PUSH_NEXT")),
    ("timing", "Timing", ("T80", "T90", "T110", "T120", "RIPPLE")),
    ("keys", "Keys", ("RANGE", "ALL", "ENDS")),
    ("motion", "Motion", ("OFFSET",)),
)
FAMILY = {action: (key, label) for key, label, actions in GROUPS
          for action in actions if action is not None}

# Saved quick selection belongs to the add-on, not to a scene or screen width.
DEFAULT_QUICK_ACTIONS = (
    "B25", "B50", "B75", "DRAG", "SMOOTH", "NUDGE_LEFT", "NUDGE_RIGHT",
    "RIPPLE", "RANGE", "ENDS", "MIRROR_SELECTED", "BAKE_STEP", "TRAIL_SHOW",
)
QUICK_LABELS = {
    "B25": "25%", "B50": "50%", "B75": "75%", "DRAG": "Drag",
    "SMOOTH": "Smooth", "NUDGE_LEFT": "-1f", "NUDGE_RIGHT": "+1f",
    "RIPPLE": "Ripple", "RANGE": "Range", "ENDS": "Ends",
    "MIRROR_SELECTED": "Mirror Sel", "BAKE_STEP": "Bake Object",
    "TRAIL_SHOW": "Show Trails",
}


def quick_property_name(action):
    """Stable RNA name; never derive preference identity from a display label."""
    if action not in ACTIONS:
        raise KeyError(action)
    return "timeline_quick_" + action.lower()


def selected_quick_actions(prefs):
    """Missing preferences use defaults; an explicitly empty set stays empty."""
    defaults = frozenset(DEFAULT_QUICK_ACTIONS)
    if prefs is None:
        return defaults
    if getattr(prefs,'timeline_layouts_json',''):
        from .timeline_config import decode
        try:
            tools=decode(prefs.timeline_layouts_json,ACTIONS)['active']['tools']
            return frozenset(action for action in ACTIONS if tools[action]['mode']!='HIDDEN')
        except ValueError:
            pass
    return frozenset(action for action in ACTIONS
                     if getattr(prefs, quick_property_name(action), action in defaults))


def quick_clusters(selected_actions):
    """Every family, with selected known actions in permanent catalog order."""
    selected = set(selected_actions).intersection(ACTIONS)
    return tuple((key, label, tuple(action for action in actions
                                   if action is not None and action in selected))
                 for key, label, actions in GROUPS)

_SCOPES = {
    "tween": ("Active object's Action; selected/active pose bones when in Pose mode, using Breakdown mask/exclusions",
              "Select an object with an Action"),
    "curves": ("Selected keys on editable selected curves, or the active object's Action when no editor curves are supplied",
               "Select editable keys on an animated object"),
    "timing": ("Active object's Action using Timing range/anchor settings",
               "Select an object with an Action"),
    "keys": ("Editable, unhidden and unmuted curves across view-layer Actions",
             "Have editable animation curves in the view layer"),
    "pose": ("Active armature in Pose mode using bone-pair settings",
             "Select an armature and an active bone in Pose mode"),
    "bake": ("Active object using Object Bake range, step and reduction settings",
             "Select an object; session cleanup requires an existing proxy session"),
    "motion": ("World trajectories of configured object/bone targets using Motion Trail settings",
               "Use the Motion Trail target settings"),
}
_SELECTED_KEY_SCOPE = (
    "Selected keys on editor-selected curves, or the active object's Action",
    "Select keys on an animated object",
)


def command_metadata(action):
    """Return scope, prerequisite and gesture, independent of UI location."""
    family = FAMILY[action][0]
    scope, prerequisite = _SCOPES[family]
    gesture = ""
    if action == "EASE":
        prerequisite = "Select at least two keys on the same editable curve; include an interior key to reshape it"
    if action.startswith("HANDLE_") or action.startswith("TYPE_") or action.startswith("NUDGE_"):
        scope, prerequisite = _SELECTED_KEY_SCOPE
    if action in {"TO_SPLINE", "TO_STEPPED"}:
        scope, prerequisite = _SELECTED_KEY_SCOPE
    if action.startswith(("TYPE_", "NUDGE_")):
        scope = "Selected keys in the active object's Action"
        prerequisite = "Select keys in the active object's Action"
    if action == "SELECT_BREAKDOWNS":
        scope = "Editor-selected curves, or the active object's Action; selects keys by type"
        prerequisite = "Have curves on the active object's Action"
    if action in {"INBETWEEN", "INBETWEENS"}:
        scope = "Selected key gap in the active object's Action using Breakdown settings"
        prerequisite = "Select two bounding keys with a gap"
    if action in {"OFFSET_DRAG"}:
        scope = "All key times in the active object's Action"
    if action == "ALIGN":
        scope = "Other selected objects matched to the active object's evaluated transform"
        prerequisite = "Select a target object and make the reference object active"
    if action.startswith("PROXY_"):
        scope = "Active object; temporary constrained object helper"
        prerequisite = "Select the object to drive through a proxy"
    if action == "BAKE_CLEANUP":
        scope = "Constrained objects and helpers in the existing proxy session"
    if action == "BAKE_PREVIEW":
        prerequisite = "Select an object and turn on the scene preview range"
    if action == "BAKE_INTEGER":
        scope, prerequisite = "Key times in the active object's Action", "Select an object with an Action"
    if action == "PROXY_BAKE":
        scope = "Active object; temporary translation proxy, baked then removed"
        prerequisite = "Select the object to bake through a proxy"
    if action == "CLEANUP_ALL":
        scope, prerequisite = "Every Anim Assist proxy session in this file", "Have proxy helpers or sessions to remove"
    if action == "REDUCE":
        prerequisite = "Select an object with an Action to reduce"
    if action == "OFFSET":
        scope = "Captured active object's editable Action curves; live frame mask with blend margins"
        prerequisite = "Select an object with editable Action curves to start Offset"
    if action in {"OFFSET_MASK", "OFFSET_SCENE_RANGE"}:
        scope = "Scene's live Action Offset frame mask; affects an active session immediately"
        prerequisite = "Choose the frame range and blend margins in Offset settings"
    if action == "REFERENCE":
        scope, prerequisite = "Scene playhead; stores the reference frame", "Choose the desired reference frame"
    if action in {"COPY_KEYS", "PASTE_KEYS"}:
        scope = "Editable, unhidden, unmuted view-layer Action curves matched by Action name, path and array index"
        prerequisite = "Select editable keys to copy" if action == "COPY_KEYS" else "Copy keys into the Anim Assist clipboard first"
    if action.startswith("BOOKMARK_"):
        scope = "Scene reference-frame bookmarks; recall sets the reference without moving the playhead"
        prerequisite = "Set a reference frame" if action == "BOOKMARK_ADD" else "Choose an existing reference bookmark"
    if action.startswith("MATCH_"):
        scope = "Active object's transforms using matching filters, locks, offset and keying settings"
        prerequisite = "Select an active object in Object or Pose mode"
        if action == "MATCH_PARENT":
            prerequisite = "Select an object with a parent"
        elif action not in {"MATCH_WORLD"}:
            prerequisite = "Select a reference object and make the object to match active"
    if action.startswith("SWITCH_"):
        scope = "Configured object or pose-bone property; compensate its evaluated transform using rig switch settings"
        prerequisite = "Configure a writable numeric rig property and target value in Pose options"
    if action == "DRAG":
        gesture = "Release left mouse to apply; Esc/right mouse restores the pre-drag keys"
    elif action in {"NEIGHBORS", "FRAME", "EASE", "AMPLIFY", "SMOOTH", "SCALE_DRAG", "OFFSET_DRAG"}:
        gesture = "Left click or Enter applies; Esc/right click cancels"
    elif action == "OFFSET":
        gesture = "Click again to finish; Esc uses the existing Offset snapshot restore"
    return scope, prerequisite, gesture


def command_description(action, operation):
    scope, prerequisite, gesture = command_metadata(action)
    parts = [f"Scope: {scope}.", f"{ACTIONS[action][2]}: {TIPS.get(action) or operation}.",
             f"Requires: {prerequisite}."]
    if action in {"B25", "B50", "B75", "DRAG"}:
        parts.append(BREAKDOWN_ANCHOR_HINT)
    if gesture:
        parts.append(gesture + ".")
    parts.append(f"Also in {FAMILY[action][1]} > {ACTIONS[action][2]}.")
    return " ".join(parts)


# Bforartists' own commands that do the same job as a row tool, as (operator, settings).
# Hover text names one only when Bforartists has a key bound to it (owner request
# 2026-10-18: "native hints", labelled as Bforartists keys, never as Anim Assist ones).
_TIME_SCALE = (("transform.transform", {"mode": "TIME_SCALE"}),)
_TIME_MOVE = (("transform.transform", {"mode": "TIME_TRANSLATE"}),)
NATIVE_EQUIVALENTS = {
    "COPY_KEYS": (("action.copy", {}), ("graph.copy", {})),
    "PASTE_KEYS": (("action.paste", {"flipped": False}), ("graph.paste", {"flipped": False})),
    "ALL": (("action.select_all", {"action": "SELECT"}), ("graph.select_all", {"action": "SELECT"})),
    "GROW_BOTH": (("action.select_more", {}), ("graph.select_more", {})),
    "T80": _TIME_SCALE, "T90": _TIME_SCALE, "T110": _TIME_SCALE, "T120": _TIME_SCALE, "SCALE_DRAG": _TIME_SCALE,
    "OFFSET_DRAG": _TIME_MOVE, "OFFSET_ACTION": _TIME_MOVE, "NUDGE_LEFT": _TIME_MOVE, "NUDGE_RIGHT": _TIME_MOVE,
    "SNAP": (("action.snap", {"type": "NEAREST_FRAME"}), ("graph.snap", {"type": "NEAREST_FRAME"})),
    "TO_SPLINE": (("action.interpolation_type", {"type": "BEZIER"}), ("graph.interpolation_type", {"type": "BEZIER"})),
    "TO_STEPPED": (("action.interpolation_type", {"type": "CONSTANT"}), ("graph.interpolation_type", {"type": "CONSTANT"})),
    "TYPE_KEYFRAME": (("action.keyframe_type", {"type": "KEYFRAME"}),),
    "TYPE_BREAKDOWN": (("action.keyframe_type", {"type": "BREAKDOWN"}),),
    "TYPE_EXTREME": (("action.keyframe_type", {"type": "EXTREME"}),),
    "TYPE_HOLD": (("action.keyframe_type", {"type": "MOVING_HOLD"}),),
    "TYPE_JITTER": (("action.keyframe_type", {"type": "JITTER"}),),
    "SMOOTH": (("graph.smooth", {}),),
    "EASE": (("graph.ease", {}),),
    "NEIGHBORS": (("graph.blend_to_neighbor", {}),),
    "DRAG": (("pose.breakdown", {}), ("graph.breakdown", {})),
    "REDUCE": (("graph.decimate", {}),),
    "BAKE_STEP": (("nla.bake", {}),),
    "OPPOSITE": (("pose.select_mirror", {}),),
}
for _kind, _type in (("AUTO", "AUTO"), ("CLAMPED", "AUTO_CLAMPED"), ("VECTOR", "VECTOR"),
                     ("ALIGNED", "ALIGNED"), ("FREE", "FREE")):
    NATIVE_EQUIVALENTS["HANDLE_" + _kind] = (("action.handle_type", {"type": _type}), ("graph.handle_type", {"type": _type}))


def command_tooltip(action, operation, reason="", status=""):
    """Row hover text as (text, role) lines: name, what it does, then details.
    Roles: TITLE, BODY, DETAIL, WARNING. A greyed tool leads its details with why."""
    scope, prerequisite, gesture = command_metadata(action)
    lines = [(ACTIONS[action][2], "TITLE"), ((TIPS.get(action) or operation).rstrip(".") + ".", "BODY")]
    if reason:
        lines.append((f"Unavailable: {reason.rstrip('.')}.", "WARNING"))
    lines.append((f"Works on: {scope}.", "DETAIL"))
    if not reason:
        lines.append((f"Needs: {prerequisite}.", "DETAIL"))
    if action in {"B25", "B50", "B75", "DRAG"}:
        lines.append((BREAKDOWN_ANCHOR_HINT, "DETAIL"))
    if gesture:
        lines.append((gesture + ".", "DETAIL"))
    if status:
        lines.append((f"Active session: {status}.", "DETAIL"))
    lines.append((f"Also in {FAMILY[action][1]} > {ACTIONS[action][2]}.", "DETAIL"))
    return lines


# Original search terms describe concepts, not another application's guarantees.
SEARCH_TERMS = {
    "B25": "tween breakdown quarter", "B50": "tween breakdown halfway", "B75": "tween breakdown three quarters",
    "DRAG": "tween slider blend", "NEIGHBORS": "tween neighbors slider", "FRAME": "tween reference slider",
    "AMPLIFY": "scale amplitude push pull slider", "SMOOTH": "smooth roughen slider",
    "OFFSET_DRAG": "time offset offsetter timing slider", "OFFSET_ACTION": "time offset offsetter timing",
    "SCALE_DRAG": "retime scale timing spacing slider",
    "T80": "spacing faster", "T90": "spacing faster", "T110": "spacing slower", "T120": "spacing slower",
    "COPY_KEYS": "clipboard copy animation", "PASTE_KEYS": "clipboard paste animation",
    "BOOKMARK_ADD": "reference bookmark save", "BOOKMARK_RECALL": "reference bookmark load",
    "BOOKMARK_REMOVE": "reference bookmark delete",
    "TO_SPLINE": "spline bezier interpolation smooth convert from stepped",
    "TRAIL_TOGGLE": "trails motion path arcs show hide toggle eye",
    "TO_STEPPED": "stepped constant interpolation hold blocking review",
    "SWITCH_SINGLE": "space switch rig compensate", "SWITCH_RANGE": "space switch rig bake compensate",
    "SWITCH_BOOL": "space switch rig boolean", "SWITCH_ENUM": "space switch rig integer enum",
    "SWITCH_INFLUENCE": "space switch rig constraint influence",
    "BAKE_PREVIEW": "bake preview range playback", "BAKE_INTEGER": "bake integer whole frames snap round export",
    "PROXY_BAKE": "proxy bake one click world motion", "CLEANUP_ALL": "proxy session cleanup remove all",
}


def search_actions(query):
    """Stable token matching across the complete catalogue, including aliases."""
    terms = query.casefold().split()
    return tuple(action for action, (suffix, _arguments, label) in ACTIONS.items()
                 if all(term in f"{action} {label} {FAMILY[action][1]} {suffix} {SEARCH_TERMS.get(action, '')}".casefold()
                        for term in terms))


def toolbar_plan(logical_width):
    """Conservative native-size budgets; no selection or session dependency."""
    return {
        "compact": logical_width < 900,
        "tween": logical_width >= 360,
        "timing": logical_width >= 1120,
        "keys": logical_width >= 1260,
    }


# The pure layout model validates stage tools by family without importing this module.
from .timeline_config import register_families as _register_families  # noqa: E402
_register_families(GROUPS)
