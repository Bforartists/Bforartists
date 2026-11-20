"""Drivers-only actions with explicit visible, selected-channel scope."""
from __future__ import annotations

import json

import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import Operator

from ..core.driver_context import active_driver, driver_curves, driver_issues, in_driver_editor


class _ActiveDriver:
    @classmethod
    def poll(cls, context):
        if not in_driver_editor(context):
            cls.poll_message_set("Switch to the Drivers editor")
            return False
        if active_driver(context) is None:
            cls.poll_message_set("Select an active visible driver channel")
            return False
        return True


class ANIMASSIST_OT_driver_settings(_ActiveDriver, Operator):
    """Open the native Drivers tab for the active driver's variables and expression"""
    bl_idname = "animassist.driver_settings"
    bl_label = "Open Driver Settings"

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False
        if getattr(context, "active_editable_fcurve", None) is None:
            cls.poll_message_set("Click an unlocked driver channel to make it active")
            return False
        return True

    panel: EnumProperty(name="Settings", description="Native settings to open for the active driver",
        items=(("DRIVER", "Driver", "Variables and expression"),
               ("MODIFIERS", "Modifiers", "Response curve modifiers")),
        default="DRIVER", options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def description(cls, context, properties):
        if properties.panel == "MODIFIERS":
            return "Open the native Modifiers tab for the active driver's response curve"
        return cls.__doc__

    def execute(self, context):
        # C sidebar panels are not wm.call_panel popovers in this host. Navigate
        # to their native category instead of duplicating or reimplementing them.
        context.space_data.show_region_ui = True
        sidebar = next((r for r in context.area.regions if r.type == "UI"), None)
        if sidebar is None:
            self.report({"WARNING"}, "Open the editor sidebar and try again")
            return {"CANCELLED"}
        category = "Modifiers" if self.panel == "MODIFIERS" else "Drivers"
        area = context.area
        try:
            sidebar.active_panel_category = category
        except AttributeError:
            # A closed sidebar has no runtime categories until its first draw.
            # Use the same one-shot deferral as Open Anim Assist Home.
            def select_tab():
                try:
                    if area.type == "GRAPH_EDITOR" and area.spaces.active.mode == "DRIVERS":
                        ui = next((r for r in area.regions if r.type == "UI"), None)
                        if ui:
                            ui.active_panel_category = category
                            area.tag_redraw()
                except (AttributeError, ReferenceError):
                    pass  # The editor was closed or its categories are not ready.
                return None
            bpy.app.timers.register(select_tab, first_interval=.1)
        area.tag_redraw()
        return {"FINISHED"}


_MODIFIER_TYPES = tuple((item.identifier, item.name, item.description)
    for item in bpy.ops.graph.fmodifier_add.get_rna_type().properties["type"].enum_items
    if item.identifier != "NULL")


class ANIMASSIST_OT_driver_modifier_add(_ActiveDriver, Operator):
    """Add a response modifier to the active editable driver only"""
    bl_idname = "animassist.driver_modifier_add"
    bl_label = "Add Driver Modifier"
    bl_options = {"REGISTER", "UNDO"}

    type: EnumProperty(name="Modifier", description="Response modifier for the active driver",
                       items=_MODIFIER_TYPES, default="LIMITS")

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False
        fc = active_driver(context)
        if fc.lock or not fc.id_data.is_editable:
            cls.poll_message_set("Unlock the active driver and use an editable owner")
            return False
        return True

    def execute(self, context):
        fc = active_driver(context)
        fc.modifiers.new(type=self.type)
        fc.id_data.update_tag()
        context.view_layer.update()
        context.area.tag_redraw()
        return {"FINISHED"}


class ANIMASSIST_OT_driver_select_owner(_ActiveDriver, Operator):
    """Select the object that owns the active driver, preserving other selected objects"""
    bl_idname = "animassist.driver_select_owner"
    bl_label = "Select Owner"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False
        owner = active_driver(context).id_data
        if not isinstance(owner, bpy.types.Object) or context.view_layer.objects.get(owner.name) != owner:
            cls.poll_message_set("The active driver must belong to an object in this view layer")
            return False
        if owner.hide_get() or owner.hide_select:
            cls.poll_message_set("Unhide the owner and enable object selection first")
            return False
        return True

    def execute(self, context):
        owner = active_driver(context).id_data
        owner.select_set(True)
        context.view_layer.objects.active = owner
        return {"FINISHED"}


class _SelectedDrivers:
    @classmethod
    def poll(cls, context):
        if not in_driver_editor(context):
            cls.poll_message_set("Switch to the Drivers editor")
            return False
        if not driver_curves(context, selected=True):
            cls.poll_message_set("Select at least one visible driver channel")
            return False
        return True


def _selected_key(key):
    return key.select_control_point or key.select_left_handle or key.select_right_handle


def _updated(curves, context):
    for fc in curves:
        fc.update()
    for owner in {fc.id_data for fc in curves}:
        owner.update_tag()
    context.view_layer.update()
    context.area.tag_redraw()


class _EditableDrivers(_SelectedDrivers):
    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False
        if not driver_curves(context, selected=True, editable=True):
            cls.poll_message_set("Select an unlocked driver channel with an editable owner")
            return False
        return True


class _DriverKeys(_EditableDrivers):
    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False
        if not any(_selected_key(k) for fc in driver_curves(context, selected=True, editable=True)
                   for k in fc.keyframe_points):
            cls.poll_message_set("Select response points in an unlocked driver channel")
            return False
        return True


class ANIMASSIST_OT_driver_interpolation(_DriverKeys, Operator):
    """Set interpolation on selected response points in selected editable driver channels only"""
    bl_idname = "animassist.driver_interpolation"
    bl_label = "Driver Interpolation"
    bl_options = {"REGISTER", "UNDO"}
    type: EnumProperty(name="Interpolation", description="How driver output changes between response points",
        items=(("CONSTANT", "Constant", "Hold the previous output"),
               ("LINEAR", "Linear", "Straight response between points"),
               ("BEZIER", "Bezier", "Shape the response with handles")), default="BEZIER")

    def execute(self, context):
        curves = [fc for fc in driver_curves(context, selected=True, editable=True)
                  if any(_selected_key(k) for k in fc.keyframe_points)]
        for fc in curves:
            for key in fc.keyframe_points:
                if _selected_key(key):
                    key.interpolation = self.type
        _updated(curves, context)
        return {"FINISHED"}


class ANIMASSIST_OT_driver_handles(_DriverKeys, Operator):
    """Set selected handles in selected editable driver channels; selecting a point sets both handles"""
    bl_idname = "animassist.driver_handles"
    bl_label = "Driver Handles"
    bl_options = {"REGISTER", "UNDO"}
    type: EnumProperty(name="Handles", description="Handle behavior for selected driver response points",
        items=tuple((item.identifier, item.name, item.description)
            for item in bpy.ops.graph.handle_type.get_rna_type().properties["type"].enum_items),
        default="AUTO_CLAMPED")

    def execute(self, context):
        curves = [fc for fc in driver_curves(context, selected=True, editable=True)
                  if any(_selected_key(k) for k in fc.keyframe_points)]
        for fc in curves:
            for key in fc.keyframe_points:
                if key.select_control_point or key.select_left_handle:
                    key.handle_left_type = self.type
                if key.select_control_point or key.select_right_handle:
                    key.handle_right_type = self.type
        _updated(curves, context)
        return {"FINISHED"}


class ANIMASSIST_OT_driver_extrapolation(_EditableDrivers, Operator):
    """Set the response outside the endpoints of selected editable driver channels only"""
    bl_idname = "animassist.driver_extrapolation"
    bl_label = "Driver Extrapolation"
    bl_options = {"REGISTER", "UNDO"}
    type: EnumProperty(name="Extrapolation", description="Driver response outside its first and last points",
        items=(("CONSTANT", "Constant", "Hold endpoint output"),
               ("LINEAR", "Linear", "Continue the endpoint slope")), default="CONSTANT")

    def execute(self, context):
        curves = driver_curves(context, selected=True, editable=True)
        for fc in curves:
            fc.extrapolation = self.type
        _updated(curves, context)
        return {"FINISHED"}


class ANIMASSIST_OT_driver_refresh(_SelectedDrivers, Operator):
    """Refresh dependencies for selected visible driver owners without changing expressions or keys"""
    bl_idname = "animassist.driver_refresh"
    bl_label = "Update Dependencies"

    def execute(self, context):
        owners = {fc.id_data for fc in driver_curves(context, selected=True)}
        for owner in owners:
            owner.update_tag()
        context.view_layer.update()
        context.area.tag_redraw()
        self.report({"INFO"}, f"Refreshed {len(owners)} selected driver owner(s)")
        return {"FINISHED"}


class ANIMASSIST_OT_driver_check(_SelectedDrivers, Operator):
    """Inspect selected visible drivers for evaluation errors, missing targets, paths and bones; make no repairs"""
    bl_idname = "animassist.driver_check"
    bl_label = "Check Selected Drivers"

    results: StringProperty(options={"HIDDEN", "SKIP_SAVE"})

    def execute(self, context):
        rows = []
        curves = driver_curves(context, selected=True)
        for fc in curves:
            for issue in driver_issues(fc, context):
                rows.append(f"{fc.id_data.name}: {fc.data_path}[{fc.array_index}] — {issue}")
        self.results = json.dumps(rows)
        if rows:
            self.report({"WARNING"}, f"{len(rows)} issue(s) in {len(curves)} selected driver(s)")
        else:
            self.report({"INFO"}, f"No issues found in {len(curves)} selected driver(s)")
        return {"FINISHED"}

    def invoke(self, context, event):
        self.execute(context)
        return context.window_manager.invoke_popup(self, width=360)

    def draw(self, context):
        from ..ui.ui_helpers import wrapped_label
        rows = json.loads(self.results or "[]")
        self.layout.label(text="Selected Driver Diagnostics")
        for row in rows:
            wrapped_label(self.layout, context, row, icon="INFO")
        if not rows:
            self.layout.label(text="No issues found", icon="CHECKMARK")


CLASSES = (ANIMASSIST_OT_driver_settings, ANIMASSIST_OT_driver_select_owner,
           ANIMASSIST_OT_driver_modifier_add, ANIMASSIST_OT_driver_interpolation,
           ANIMASSIST_OT_driver_handles, ANIMASSIST_OT_driver_extrapolation,
           ANIMASSIST_OT_driver_refresh, ANIMASSIST_OT_driver_check)
