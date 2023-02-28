from typing import Callable, Iterable

import bpy

from .common import BrushPanelBase


def panel_factory(
        tools: Iterable[str],
        icon_prefix: str,
        tool_name_attr: str,
        use_paint_attr: str,
        tool_settings_attr: str,
        poll: Callable[[bpy.types.Panel, bpy.types.Context], bool],
        panel_class_name_suffix: str,
        space_type: str
):

    @staticmethod
    def tool_name_from_brush(brush: bpy.types.Brush):
        return getattr(brush, tool_name_attr)

    @staticmethod
    def filter_brush(brush: bpy.types.Brush):
        return getattr(brush, use_paint_attr)

    @staticmethod
    def icon_name_from_brush(brush: bpy.types.Brush):
        return icon_prefix + tool_name_from_brush(brush).lower()

    for tool_name in tools:
        yield type(
            f"BFA_PT_brush_{tool_name_attr}_{tool_name}_{panel_class_name_suffix}",
            (BrushPanelBase,),
            {
                "bl_label": tool_name.capitalize(),
                "bl_space_type": space_type,
                "poll": poll,
                "tool_name": tool_name,
                "tool_settings_attribute_name": tool_settings_attr,
                "filter_brush": filter_brush,
                "icon_name_from_brush": icon_name_from_brush,
                "tool_name_from_brush": tool_name_from_brush,
            },
        )


def panel_factory_view3d(
        tools: Iterable[str],
        icon_prefix: str,
        tool_name_attr: str,
        use_paint_attr: str,
        tool_settings_attr: str,
        mode: str
):

    @classmethod
    def poll(cls, context):
        return context.mode == mode

    yield from panel_factory(tools,
                             icon_prefix,
                             tool_name_attr,
                             use_paint_attr,
                             tool_settings_attr,
                             poll,
                             panel_class_name_suffix=mode,
                             space_type="VIEW_3D"
                             )


def panel_factory_image_editor(tools: Iterable[str],
                                icon_prefix: str,
                                tool_name_attr: str,
                                use_paint_attr: str,
                                tool_settings_attr: str):
    @classmethod
    def poll(cls, context):
        return context.space_data.ui_mode == "PAINT"

    yield from panel_factory(tools,
                             icon_prefix,
                             tool_name_attr,
                             use_paint_attr,
                             tool_settings_attr,
                             poll,
                             panel_class_name_suffix="image_editor",
                             space_type="IMAGE_EDITOR",
                             )
