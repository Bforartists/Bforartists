"""Contextual Drivers sidebar and shared header-menu drawing."""
from __future__ import annotations

import bpy
from bpy.types import Menu, Panel

from .. import constants
from ..core.driver_context import active_driver, driver_curves, in_driver_editor
from .ui_helpers import wrapped_label


def draw_target(layout, context):
    fc = active_driver(context)
    layout.label(text=f"Selected drivers: {len(driver_curves(context, selected=True))}")
    if fc is None:
        wrapped_label(layout, context, "Select a driver channel to inspect its owner and driven property.")
    else:
        wrapped_label(layout, context, f"Owner: {fc.id_data.name}")
        wrapped_label(layout, context, f"Property: {fc.data_path}")
        try:
            value = fc.id_data.path_resolve(fc.data_path)
            if hasattr(value, "__len__") and not isinstance(value, str):
                layout.label(text=f"Array index: {fc.array_index}")
                value = value[fc.array_index]
            wrapped_label(layout, context, f"Current value: {value:.4g}" if isinstance(value, (int, float)) else f"Current value: {value}")
        except (ValueError, AttributeError, KeyError, IndexError, TypeError):
            wrapped_label(layout, context, "Driven property cannot be resolved", icon="ERROR")
    layout.operator_context = "EXEC_REGION_WIN"
    row = layout.row(align=True)
    row.operator("graph.view_selected", text="Frame Selected")
    row.operator("graph.view_all", text="Frame All")
    row = layout.row(align=True)
    row.operator("anim.channels_select_all", text="All Channels").action = "SELECT"
    row.operator("anim.channels_select_all", text="None").action = "DESELECT"
    layout.operator("animassist.driver_select_owner")
    if fc is not None:
        row = layout.row(align=True)
        row.enabled = fc.id_data.is_editable
        row.prop(fc, "mute", text="Muted")
        row.prop(fc, "lock", text="Locked")


def draw_variables(layout, context):
    layout.operator_context = "INVOKE_DEFAULT"
    layout.operator("animassist.driver_settings")
    fc = active_driver(context)
    if fc is None:
        wrapped_label(layout, context, "Select a driver to edit its variables and expression.")
        return
    driver = fc.driver
    layout.label(text=f"Variables: {len(driver.variables)}")
    if driver.type == "SCRIPTED":
        wrapped_label(layout, context, f"Expression: {driver.expression}")
    else:
        item = driver.bl_rna.properties["type"].enum_items[driver.type]
        layout.label(text=f"Type: {item.name}")


def draw_response(layout, context):
    wrapped_label(layout, context, "Horizontal: driver input. Vertical: driven output.")
    layout.operator_context = "EXEC_REGION_WIN"
    editable = driver_curves(context, selected=True, editable=True)
    if not editable:
        wrapped_label(layout, context, "Select an unlocked, editable driver channel.")
    keys = layout.column(align=True)
    keys.enabled = any(k.select_control_point or k.select_left_handle or k.select_right_handle
                       for fc in editable for k in fc.keyframe_points)
    keys.menu("ANIMASSIST_MT_driver_interpolation", text="Interpolation")
    keys.menu("ANIMASSIST_MT_driver_handles", text="Handles")
    curves = layout.column(align=True)
    curves.enabled = bool(editable)
    curves.menu("ANIMASSIST_MT_driver_extrapolation", text="Extrapolation")
    modifiers = layout.column()
    fc = active_driver(context)
    modifiers.enabled = bool(fc and not fc.lock and fc.id_data.is_editable)
    modifiers.menu("ANIMASSIST_MT_driver_modifier_add", text="Add Modifier (Active)")
    modifiers.operator("animassist.driver_settings", text="Open Modifier Settings").panel = "MODIFIERS"


def draw_diagnostics(layout, context):
    layout.operator_context = "INVOKE_DEFAULT"
    layout.operator("animassist.driver_check")
    layout.operator_context = "EXEC_DEFAULT"
    layout.operator("animassist.driver_refresh")
    wrapped_label(layout, context, "Checks selected visible drivers. No automatic repairs or deletion.")


DRIVER_SECTIONS = (
    ("target", "Driver & Target", draw_target),
    ("variables", "Variables & Expression", draw_variables),
    ("response", "Response Curve", draw_response),
    ("diagnostics", "Diagnostics", draw_diagnostics),
)


def _panel(key, label, draw_body, order):
    def draw(self, context):
        draw_body(self.layout, context)
    return type(f"ANIMASSIST_PT_driver_{key}", (Panel,), {
        "bl_idname": f"ANIMASSIST_PT_driver_{key}", "bl_label": label,
        "bl_space_type": "GRAPH_EDITOR", "bl_region_type": "UI",
        "bl_category": constants.ANIMASSIST_CATEGORY, "bl_order": order,
        "bl_options": {"DEFAULT_CLOSED"} if order > 1 else set(),
        "poll": classmethod(lambda cls, context: in_driver_editor(context)), "draw": draw,
    })


CLASSES = tuple(_panel(key, label, draw, index) for index, (key, label, draw)
                in enumerate(DRIVER_SECTIONS, start=1))


def _curve_menu(operation, label, description):
    def draw(self, context):
        self.layout.operator_context = "EXEC_REGION_WIN"
        op = getattr(bpy.ops.animassist, operation)
        for item in op.get_rna_type().properties["type"].enum_items:
            self.layout.operator(f"animassist.{operation}", text=item.name).type = item.identifier
    name = f"ANIMASSIST_MT_{operation}"
    return type(name, (Menu,), {"bl_idname": name, "bl_label": label,
                              "bl_description": description, "draw": draw})


CURVE_MENUS = (
    _curve_menu("driver_interpolation", "Interpolation", "Interpolation of selected points in selected editable drivers"),
    _curve_menu("driver_handles", "Handles", "Handle behavior of selected points in selected editable drivers"),
    _curve_menu("driver_extrapolation", "Extrapolation", "Response outside the endpoints of selected editable drivers"),
    _curve_menu("driver_modifier_add", "Add Driver Modifier", "Add a response modifier to the active editable driver only"),
)
