"""Shared Timeline action dispatch, menus and quick-selection settings."""

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from ..core.logging import get_logger
from .timeline_catalog import (
    ACTIONS as _ACTIONS, EXECUTE_ACTIONS, GROUPS, QUICK_GROUPS, FAMILY,
    command_description, command_metadata, QUICK_LABELS, search_actions, TIPS,
    DEFAULT_QUICK_ACTIONS, quick_property_name, selected_quick_actions, quick_clusters,
)

_log = get_logger(__name__)


def is_timeline(area):
    return bool(area and area.type == "DOPESHEET_EDITOR"
                and area.spaces.active.mode == "TIMELINE")


def is_strip(area):
    """Recognize legacy ownership only; never mark or create new editors."""
    return bool(area and area.type == "TEXT_EDITOR"
                and area.spaces.active.text is not None
                and area.spaces.active.text.get("animassist_timeline_toolbar") == 1)


def native_available():
    """Feature detection, including the host's safe native enable operation."""
    properties = bpy.types.SpaceDopeSheetEditor.bl_rna.properties
    if not all(name in properties for name in
               ("show_region_tool_header", "timeline_toolbar_hidden_by_user")):
        return False
    try:
        operation = bpy.ops.screen.timeline_toolbar_set.get_rna_type()
    except (RuntimeError, AttributeError):
        return False
    return all(name in operation.properties for name in ("enabled", "user_action"))


def native_visible(area):
    return (_enabled() and native_available() and is_timeline(area)
            and area.spaces.active.show_region_tool_header
            and any(r.type == "TOOL_HEADER" and r.height > 1 for r in area.regions))


def _enabled():
    from ..prefs import get_prefs
    prefs = get_prefs()
    return prefs is None or prefs.timeline_toolbar_row


def _target(context):
    return context.area if is_timeline(context.area) else None


def _window_region(area):
    return next(r for r in area.regions if r.type == "WINDOW")


def _operator(action):
    operator = getattr(bpy.ops.animassist, _ACTIONS[action][0])
    try:
        operator.get_rna_type()
    except (RuntimeError, AttributeError):
        return None
    return operator


def _switch_unavailable(context, action):
    from ..core.p8_properties import get_p8
    from ..operators.p8_switch_ops import _resolve_prop_owner, _get_prop_value
    settings = get_p8(context)
    obj = context.active_object
    if obj is None or settings is None or not settings.switch_prop_path:
        return "Configure an active object's rig property in Pose options"
    if obj.library and not obj.override_library:
        return "Use a local or overridden rig object"
    owner = _resolve_prop_owner(obj, settings.switch_bone_name)
    if owner is None:
        return "Choose an existing rig bone in Pose options"
    value = _get_prop_value(owner, settings.switch_prop_path)
    if not isinstance(value, (int, float)):
        return "Choose a writable numeric rig property; string enum properties are unsupported"
    if action == "SWITCH_BOOL" and value not in (0, 1):
        return "Choose a boolean rig property whose value is 0 or 1"
    if action == "SWITCH_INFLUENCE" and not 0 <= settings.switch_new_value <= 1:
        return "Set the rig influence target between 0 and 1 in Pose options"
    if action == "SWITCH_ENUM" and not float(settings.switch_new_value).is_integer():
        return "Set a whole-number rig target value in Pose options"
    path = settings.switch_prop_path
    if not (path.startswith('["') and path.endswith('"]')):
        try:
            if "." in path:
                parent_path, attribute = path.rsplit(".", 1)
                parent = owner.path_resolve(parent_path)
            else:
                parent, attribute = owner, path
            if parent.is_property_readonly(attribute):
                return "Choose a writable rig property in Pose options"
        except (AttributeError, ValueError, TypeError):
            return "Choose a supported rig property path in Pose options"
    return ""


def _module_reason(context,action):
    from ..prefs import get_prefs
    prefs=get_prefs(context)
    if not prefs: return ''
    suffix=_ACTIONS[action][0]
    family=FAMILY[action][0]
    module={'tween':'breakdown','curves':'transform','timing':'retime',
            'keys':'keys','pose':'matching','bake':'controls','motion':'trajectory'}[family]
    if suffix.startswith('anim_offset'): module='transform'
    elif suffix in {'set_handle_type','move_keys'}: module='keys'
    elif suffix=='p6_bake_timing': module='retime'
    elif suffix=='batch_interpolation': module='keys'
    elif action in {'ALL','RANGE','ENDS','GROW_LEFT','GROW_RIGHT','GROW_BOTH','SELECT_BREAKDOWNS'}: module='selection'
    flag='enable_'+module
    if not getattr(prefs,flag,True):
        return 'Enable '+prefs.bl_rna.properties[flag].name+' in add-on preferences'
    return ''


def _selection_requirement(action):
    if action in {"NEIGHBORS", "FRAME", "EASE", "AMPLIFY", "SMOOTH"}:
        from ..operators.curve_tool_ops import _editable_fcurves
        return _editable_fcurves, 2 if action == "EASE" else 1
    if action.startswith(("TYPE_", "NUDGE_")):
        from ..operators.keymanager_ops import _object_fcurves
        return _object_fcurves, 1
    if action in {"TO_SPLINE", "TO_STEPPED"} or action.startswith("HANDLE_"):
        from ..operators.keymanager_ops import _visible_fcurves
        return _visible_fcurves, 1
    return None, 0


def _has_selected_keys(context, action, checks):
    curves, count = _selection_requirement(action)
    if curves is None:
        return True
    key = (curves, count)
    if checks is not None and key in checks:
        return checks[key]
    has_selection = False
    for curve in curves(context):
        selected = (point for point in curve.keyframe_points if point.select_control_point)
        if next(selected, None) is None:
            continue
        has_selection = True
        if count == 1 or next(selected, None) is not None:
            if checks is not None:
                checks[key] = True
                checks[curves, 1] = True
            return True
    if checks is not None:
        checks[key] = False
        checks[curves, 1] = has_selection
    return False


def _unavailable(context, target, action, *, selection_checks=None):
    if target is None:
        return "Use an animation tool from a Timeline"
    reason=_module_reason(context,action)
    if reason: return reason
    operator = _operator(action)
    if operator is None:
        return "Enable the corresponding Anim Assist tool module"
    try:
        with context.temp_override(area=target, region=_window_region(target)):
            if not _has_selected_keys(context, action, selection_checks):
                if action == "EASE":
                    return "Select at least two editable keys on the same curve"
                return "Select editable keys on an animated object"
            if action == "COPY_KEYS":
                from ..core.context_utils import iter_selected_keys
                if next(iter_selected_keys(context), None) is None:
                    return "Select editable keys to copy"
            if action == "PASTE_KEYS":
                from ..core.key_utils import clipboard_size
                if not clipboard_size():
                    return "Copy keys into the Anim Assist clipboard first"
            if action in {"BOOKMARK_RECALL", "BOOKMARK_REMOVE"}:
                settings = context.scene.anim_assist
                if not 0 <= settings.active_bookmark_index < len(settings.bookmarks):
                    return "Choose an existing reference bookmark in Curves options"
            if action.startswith("SWITCH_"):
                reason = _switch_unavailable(context, action)
                if reason:
                    return reason
            if action == "MIRROR_RANGE":
                scene = context.scene
                start = scene.frame_preview_start if scene.use_preview_range else scene.frame_start
                if start < 0:
                    return "Use a nonnegative preview/playback range for Mirror Range"
            if action in {"INBETWEEN", "INBETWEENS"}:
                from ..operators.p3_inbetween_ops import _selected_frames
                obj = context.active_object
                if obj is None or len(_selected_frames(obj)) < 2:
                    return "Select two bounding keys with a gap"
            if action == "OFFSET":
                if context.scene.anim_assist.anim_offset_active:
                    return ""
                from ..operators.anim_offset_ops import _object_fcurves
                if not _object_fcurves(context):
                    return "Select an object with editable Action curves"
            if action in {'TRAIL_SHOW','TRAIL_REFRESH','TRAIL_DIAGNOSE'}:
                from ..operators.p5_overlay_ops import _resolve_targets
                from ..core.p5_properties import get_p5
                if not _resolve_targets(context,get_p5(context)):
                    return 'Select or configure an animated motion-trail target'
            if action in {'SCALE_DRAG','OFFSET_DRAG'}:
                from ..core.fcurve_compat import get_fcurves
                obj=context.active_object
                data=getattr(obj,'animation_data',None)
                if data and data.action and not any(not fc.lock and not fc.hide for fc in get_fcurves(data.action,anim_data=data)):
                    return 'Unlock and show editable Action curves'
            if not operator.poll():
                return command_metadata(action)[1]
    except (RuntimeError, ReferenceError, StopIteration) as exc:
        _log.debug("Timeline prerequisite unavailable: %s", exc)
        return "Open an editable Timeline and select the required animation"
    return ""


def _arguments(context, action):
    arguments = dict(_ACTIONS[action][1])
    settings = context.scene.anim_assist
    if action == "BOOKMARK_RECALL":
        arguments["index"] = settings.active_bookmark_index
    elif action == "BOOKMARK_ADD":
        arguments["name"] = f"Reference {settings.reference_frame}"
    elif action == "MIRROR_RANGE":
        scene = context.scene
        arguments.update(start_frame=scene.frame_preview_start if scene.use_preview_range else scene.frame_start,
                         end_frame=scene.frame_preview_end if scene.use_preview_range else scene.frame_end)
    elif action == "PASTE_KEYS":
        from ..prefs import get_prefs
        prefs = get_prefs(context)
        arguments["frame_offset"] = prefs.timeline_paste_offset if prefs else 0.0
    elif action in {"SWITCH_ENUM", "SWITCH_INFLUENCE"}:
        from ..core.p8_properties import get_p8
        value = get_p8(context).switch_new_value
        arguments["value" if action == "SWITCH_ENUM" else "influence"] = int(value) if action == "SWITCH_ENUM" else value
    return arguments


class ANIMASSIST_OT_timeline_tool(bpy.types.Operator):
    """Use an Anim Assist action in this Timeline"""
    bl_idname = "animassist.timeline_tool"
    bl_label = "Timeline Tool"
    bl_options = {"INTERNAL"}
    action: StringProperty(options={"HIDDEN", "SKIP_SAVE"})
    canvas_undo: BoolProperty(default=False, options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def poll(cls, context):
        if not is_timeline(context.area):
            cls.poll_message_set("Use this tool from a Timeline")
            return False
        return True

    @classmethod
    def description(cls, context, properties):
        action = properties.action
        if action not in _ACTIONS:
            return cls.__doc__
        from ..core import explainers
        operator = _operator(action)
        description = command_description(action, explainers.operator_text("animassist." + _ACTIONS[action][0])
                                          if operator else "Tool module unavailable")
        reason = _unavailable(context, _target(context), action)
        if action in {"OFFSET", "OFFSET_MASK", "OFFSET_SCENE_RANGE"}:
            from ..operators.anim_offset_ops import offset_session_status
            status = offset_session_status(context.scene)
            if status:
                description += f" Active session: {status}."
        return description + (f" Unavailable: {reason}." if reason else "")

    @classmethod
    def _aa_short(cls, context, properties):
        # Short explainer: the tool's purpose in one line, and why it is greyed.
        from ..core import explainers
        action = properties.action
        if action not in _ACTIONS:
            return ""
        operator = _operator(action)
        text = TIPS.get(action) or (explainers.operator_text("animassist." + _ACTIONS[action][0]) if operator else "")
        reason = _unavailable(context, _target(context), action)
        return explainers.short(text or _ACTIONS[action][2]) + (f". Unavailable: {reason}" if reason else "")

    def invoke(self, context, _event):
        return self.execute(context)

    def execute(self, context):
        target = _target(context)
        if target is None or self.action not in _ACTIONS:
            self.report({"WARNING"}, "Choose a known Timeline tool")
            return {"CANCELLED"}
        try:
            reason = _unavailable(context, target, self.action)
            if reason:
                self.report({"WARNING"}, reason)
                return {"CANCELLED"}
            with context.temp_override(area=target, region=_window_region(target)):
                operator = _operator(self.action)
                if (self.action == "OFFSET" and context.scene.anim_assist.anim_offset_active
                        and not operator.poll()):
                    context.scene.anim_assist.anim_offset_active = False
                    return {"FINISHED"}
                # Canvas calls need an explicit checkpoint; native UI buttons
                # already retain the nested operator's Undo entry. Asynchronous
                # modals own their completion history.
                mode = "EXEC_DEFAULT" if self.action in EXECUTE_ACTIONS else "INVOKE_DEFAULT"
                result = operator(mode, True, **_arguments(context, self.action))
                if self.canvas_undo and "FINISHED" in result:
                    bpy.ops.ed.undo_push(message=_ACTIONS[self.action][2])
            return {"CANCELLED"} if "CANCELLED" in result else {"FINISHED"}
        except (RuntimeError, ReferenceError, AttributeError) as exc:
            self.report({"WARNING"}, str(exc))
            return {"CANCELLED"}


def _button(layout, context, target, action, text="", icon="NONE", depress=False):
    row = layout.row(align=True)
    row.enabled = not _unavailable(context, target, action)
    row.operator_context = "INVOKE_DEFAULT"
    op = row.operator("animassist.timeline_tool", text=text, icon=icon, depress=depress)
    op.action = action


def _menu_id(key):
    return f"ANIMASSIST_MT_timeline_{key}"


def _build_menu(key, label, actions):
    def draw(self, context):
        for action in actions:
            if action is None:
                self.layout.separator()
            else:
                _button(self.layout, context, _target(context), action, _ACTIONS[action][2])
        self.layout.separator()
        options = self.layout.operator("wm.call_panel", text=f"{label} Options", icon="PREFERENCES")
        options.name = f"ANIMASSIST_PT_timeline_options_{key}"
        self.layout.operator("animassist.open_home", text="Open Anim Assist Panel", icon="PROPERTIES")
    name = _menu_id(key)
    return type(name, (bpy.types.Menu,), {"bl_idname": name, "bl_label": label, "draw": draw})


_menus = [_build_menu(*group) for group in GROUPS]


class ANIMASSIST_MT_timeline_tools(bpy.types.Menu):
    bl_label = "Anim Assist Tools"
    bl_description = "All seven animation families in their permanent order"

    def draw(self, context):
        for key, label, _actions in GROUPS:
            self.layout.menu(_menu_id(key), text=label)


class ANIMASSIST_MT_timeline_more(bpy.types.Menu):
    bl_label = "More Anim Assist Shortcuts"
    bl_description = "Original quick commands and all animation families"

    def draw(self, context):
        from . import timeline_config as model
        from ..prefs import timeline_record, get_prefs
        from .timeline_overlay import current_stage
        data=timeline_record(get_prefs(context))
        stage=current_stage(context)
        order,tools=model.stage_view(data['active'],stage)
        families={key:(label,set(a for a in actions if a)) for key,label,actions in GROUPS}
        for key in model.row_families(data['active'],stage):
            label,known=families[key]
            actions=[a for a in order if a in known and tools[a]['mode']!='HIDDEN']
            if not actions: continue
            self.layout.separator()
            self.layout.label(text=label)
            for action in actions:
                active = action == "OFFSET" and context.scene.anim_assist.anim_offset_active
                _button(self.layout, context, _target(context), action, _ACTIONS[action][2],
                        icon="PAUSE" if active else "NONE", depress=active)
                for value in data['active']['tools'][action].get('presets',[]):
                    op=self.layout.operator('animassist.timeline_slider',text=f'{_ACTIONS[action][2]}: {value:g}')
                    op.action=action; op.value=value; op.apply_value=True
        self.layout.separator()
        self.layout.menu("ANIMASSIST_MT_timeline_tools", text="All Tools")


_menus.extend([ANIMASSIST_MT_timeline_tools, ANIMASSIST_MT_timeline_more])


class ANIMASSIST_OT_reset_timeline_quick_defaults(bpy.types.Operator):
    bl_idname = "animassist.reset_timeline_quick_defaults"
    bl_label = "Reset All Quick Buttons to Defaults"
    bl_description = "Restore the recommended two-slider toolbar layout"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        from ..prefs import get_prefs
        prefs = get_prefs(context)
        if prefs is None:
            self.report({"WARNING"}, "Enable Anim Assist in add-on preferences first")
            return {"CANCELLED"}
        for action in _ACTIONS:
            setattr(prefs, quick_property_name(action), action in DEFAULT_QUICK_ACTIONS)
        from . import timeline_config as model
        from ..prefs import timeline_record
        data=timeline_record(prefs); model.load(data,'recommended',_ACTIONS)
        prefs.timeline_layouts_json=model.encode(data,_ACTIONS)
        return {"FINISHED"}


class ANIMASSIST_OT_timeline_pin(bpy.types.Operator):
    bl_idname = "animassist.timeline_pin"
    bl_label = "Toggle Quick Button"
    bl_description = "Add or remove this tool's one-click button beside its family"
    bl_options = {"INTERNAL"}
    action: StringProperty(options={"HIDDEN", "SKIP_SAVE"})

    def execute(self, context):
        from ..prefs import get_prefs
        prefs = get_prefs(context)
        if prefs is None or self.action not in _ACTIONS:
            self.report({"WARNING"}, "Enable Anim Assist and choose a known tool")
            return {"CANCELLED"}
        from . import timeline_config as model
        from ..prefs import timeline_record
        from .timeline_settings import write, editor, sync_editor
        from .timeline_overlay import current_stage
        data=timeline_record(prefs)
        stage=current_stage(context)
        target=model.pin_target(stage,self.action)
        visible=model.stage_view(data['active'],target)[1][self.action]['mode']!='HIDDEN'
        mode='HIDDEN' if visible else ('POPOUT' if self.action in model.SLIDERS else 'BUTTON')
        model.set_stage_tool(data,target,self.action,mode=mode)
        # An open Toolbar Settings shows the pin too, so its next edit cannot undo it.
        try:
            if editor(context): sync_editor(context,data)
            else: write(context,data)
        except ValueError as exc:
            self.report({'WARNING'},str(exc)); return {'CANCELLED'}
        if target=='ALL':
            setattr(prefs, quick_property_name(self.action),not visible)
        return {"FINISHED"}


class ANIMASSIST_OT_timeline_search(bpy.types.Operator):
    bl_idname = "animassist.timeline_search"
    bl_label = "Search Animation Tools"
    bl_description = ("Find any Anim Assist tool by name, family or idea; run it, or pin it to this row. "
                      "With nothing typed, browse every tool by family")
    bl_options = {"INTERNAL"}
    query: StringProperty(name="Search", description="Find tools by name, family or animation concept",
                          options={"TEXTEDIT_UPDATE", "SKIP_SAVE"})
    family: EnumProperty(name="Family", description="Browse this family's tools",
                         items=[(key, label, f"Browse the {label} tools") for key, label, _a in GROUPS],
                         options={"SKIP_SAVE"})

    @classmethod
    def poll(cls, context):
        if not is_timeline(context.area):
            cls.poll_message_set("Search these tools from a Timeline")
            return False
        return True

    def invoke(self, context, _event):
        # Browse opens on the first family of the row shown (Tween for All).
        from . import timeline_config as model
        from .timeline_overlay import current_stage
        from ..prefs import get_prefs, timeline_record
        try:
            self.family = model.row_families(timeline_record(get_prefs(context))['active'], current_stage(context))[0]
        except (ValueError, TypeError, AttributeError, IndexError):
            pass
        return context.window_manager.invoke_popup(self, width=620)

    def draw(self, context):
        from ..prefs import get_prefs
        self.layout.prop(self, "query", text="", icon="VIEWZOOM")
        from . import timeline_config as model
        from .timeline_overlay import current_stage
        from ..prefs import timeline_record
        prefs = get_prefs(context)
        selected = selected_quick_actions(prefs)
        stage = current_stage(context)
        if prefs is not None and stage in model.STAGE_KEYS:
            try:
                active = timeline_record(prefs)['active']
                views = {key: model.stage_view(active, key)[1] for key in ('ALL', stage)}
                selected = frozenset(a for a in _ACTIONS
                                     if views[model.pin_target(stage, a)][a]['mode'] != 'HIDDEN')
            except ValueError:
                pass
        matches = search_actions(self.query)
        limit = 16
        if not self.query.strip():
            # Nothing typed: browse every tool, one family at a time.
            self.layout.row().prop(self, "family", expand=True)
            matches = tuple(a for a in next(acts for key, _l, acts in GROUPS if key == self.family) if a)
            limit = len(matches)
            self.layout.label(text="Click a tool to run it; the pin adds it to this row or takes it off.")
        if not matches:
            self.layout.label(text="No matching animation tools", icon="INFO")
        for action in matches[:limit]:
            row = self.layout.row(align=True)
            _button(row, context, _target(context), action, _ACTIONS[action][2])
            pin = row.row(align=True)
            pin.enabled = prefs is not None
            op = pin.operator("animassist.timeline_pin", text="",
                              icon="PINNED" if action in selected else "UNPINNED",
                              depress=action in selected)
            op.action = action
        if len(matches) > limit:
            self.layout.label(text=f"{len(matches)} matches; refine the search to see more")

    def execute(self, context):
        return {"FINISHED"}


class ANIMASSIST_PT_timeline_quick_settings(bpy.types.Panel):
    bl_label = "Timeline Quick Tools"
    bl_space_type = "DOPESHEET_EDITOR"
    bl_region_type = "HEADER"
    bl_ui_units_x = 22

    def draw(self, context):
        from ..prefs import get_prefs, draw_timeline_quick_settings
        prefs = get_prefs(context)
        if prefs is None:
            self.layout.label(text="Enable Anim Assist in add-on preferences", icon="INFO")
        else:
            draw_timeline_quick_settings(self.layout, context, prefs)


# These secondary controls edit existing settings; the primary action remains
# immediate and each target's native Adjust Last Operation stays available.
_OPTION_FIELDS = {
    "tween": (("anim_assist_p3", ("mode", "mask_location", "mask_rotation", "mask_scale", "mask_custom", "inbetween_count")),),
    "curves": (("anim_assist", ("reference_frame",)),),
    "timing": (("anim_assist_p6", ("anchor_mode", "pivot_frame", "range_mode", "range_start", "range_end", "offset_frames", "ripple_delta", "insert_frames", "modal_snap", "modal_show_header")),),
    "keys": (),
    "pose": (("anim_assist_p9", ("mirror_axis", "mirror_space", "mirror_location", "mirror_rotation", "mirror_scale", "respect_locks", "respect_drivers", "auto_key_mirror")),
             ("anim_assist_p8", ("match_channels", "match_axis", "maintain_offset", "respect_locks", "respect_drivers", "auto_key_switch", "switch_bone_name", "switch_prop_path", "switch_new_value", "comp_range", "comp_range_start", "comp_range_end"))),
    "bake": (("anim_assist_p7", ("bake_range_mode", "bake_range_start", "bake_range_end", "bake_step", "bake_channels", "smart_bake_tolerance")),),
    "motion": (("anim_assist_p5", ("scope_mode", "custom_start", "custom_end", "sample_step", "space_mode")),),
}


def _build_options(key, label, _actions):
    def draw(self, context):
        layout = self.layout
        layout.label(text=f"{label} options")
        for attribute, names in _OPTION_FIELDS[key]:
            settings = getattr(context.scene, attribute, None)
            if settings is None:
                layout.label(text="Enable this tool module to edit its settings", icon="INFO")
                continue
            for name in names:
                layout.prop(settings, name)
            layout.separator()
        if key == "curves":
            settings = context.scene.anim_assist
            layout.template_list("UI_UL_list", "reference_bookmarks", settings, "bookmarks",
                                 settings, "active_bookmark_index", rows=3)
            index = settings.active_bookmark_index
            if 0 <= index < len(settings.bookmarks):
                layout.prop(settings.bookmarks[index], "name")
                layout.prop(settings.bookmarks[index], "frame")
            for action in ("BOOKMARK_ADD", "BOOKMARK_RECALL", "BOOKMARK_REMOVE"):
                _button(layout, context, _target(context), action, _ACTIONS[action][2])
            layout.label(text="Recall changes the reference; the playhead stays put.")
        elif key == "keys":
            from ..prefs import get_prefs
            prefs = get_prefs(context)
            if prefs:
                layout.prop(prefs, "timeline_paste_offset")
            layout.label(text="Paste matches Action names and curve paths.")
            layout.label(text="Paste uses copied times plus offset, not the playhead.")
        elif key == "pose":
            layout.label(text="Mirror Range uses the preview/playback range.")
        elif key == "motion":
            mask = context.scene.anim_assist.mask
            for name in ("enabled", "start_frame", "end_frame", "blend_left", "blend_right"):
                layout.prop(mask, name)
        layout.separator()
        layout.label(text="Drag feedback appears in the header or status bar.")
        layout.label(text="Use Adjust Last Operation for completed tool options.")
    name = f"ANIMASSIST_PT_timeline_options_{key}"
    return type(name, (bpy.types.Panel,), {"bl_label": f"{label} Options",
                "bl_space_type": "DOPESHEET_EDITOR", "bl_region_type": "HEADER",
                "bl_ui_units_x": 24, "draw": draw})


_settings_classes = [ANIMASSIST_OT_reset_timeline_quick_defaults, ANIMASSIST_OT_timeline_pin,
                     ANIMASSIST_OT_timeline_search, ANIMASSIST_PT_timeline_quick_settings]
_settings_classes.extend(_build_options(*group) for group in GROUPS)


def _draw_toolbar(self, context):
    layout = self.layout
    target = _target(context)
    if target is None:
        return
    from ..prefs import get_prefs
    layout.operator("animassist.timeline_search", text="Search", icon="VIEWZOOM")
    layout.popover(panel="ANIMASSIST_PT_timeline_quick_settings", text="", icon="PREFERENCES")
    for key, label, actions in quick_clusters(selected_quick_actions(get_prefs(context))):
        layout.separator()
        row = layout.row(align=True)
        row.menu(_menu_id(key), text=label)
        for action in actions:
            active = action == "OFFSET" and context.scene.anim_assist.anim_offset_active
            _button(row, context, target, action, QUICK_LABELS.get(action, _ACTIONS[action][2]),
                    icon="PAUSE" if active else "MOUSE_MOVE" if action == "DRAG" else "NONE",
                    depress=active)
        row.popover(panel=f"ANIMASSIST_PT_timeline_options_{key}", text="", icon="TRIA_DOWN")


# Pixel drawing and native keymaps own the canvas row. Menu registration
# creates no helper editor and starts no repeated geometry repair.
def reconcile_preferences():
    manager = getattr(bpy.context, 'window_manager', None)
    for window in getattr(manager, 'windows', ()):
        for area in window.screen.areas:
            if is_timeline(area):
                area.tag_redraw()


def register():
    from . import timeline_overlay, timeline_settings
    from ..core import explainers
    explainers.register_class(ANIMASSIST_OT_timeline_tool)
    for cls in _settings_classes + _menus:
        explainers.register_class(cls)
    timeline_settings.register()
    timeline_overlay.register()
    reconcile_preferences()


def unregister():
    from . import timeline_overlay, timeline_settings
    timeline_overlay.unregister()
    timeline_settings.unregister()
    for cls in reversed(_settings_classes + _menus + [ANIMASSIST_OT_timeline_tool]):
        if cls.is_registered:
            bpy.utils.unregister_class(cls)
    reconcile_preferences()
