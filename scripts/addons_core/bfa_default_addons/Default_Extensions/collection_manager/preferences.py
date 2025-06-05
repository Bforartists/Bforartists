# SPDX-FileCopyrightText: 2011 Ryan Inch
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import AddonPreferences
from bpy.props import (
    BoolProperty,
    FloatProperty,
    FloatVectorProperty,
    )

from . import cm_init
from . import qcd_init

def update_disable_objects_hotkeys_status(self, context):
    if self.enable_disable_objects_override:
        cm_init.register_disable_objects_hotkeys()

    else:
        cm_init.unregister_disable_objects_hotkeys()

def update_qcd_status(self, context):
    if self.enable_qcd:
        qcd_init.register_qcd()

    else:
        qcd_init.unregister_qcd()

def update_qcd_view_hotkeys_status(self, context):
    if self.enable_qcd_view_hotkeys:
        qcd_init.register_qcd_view_hotkeys()
    else:
        qcd_init.unregister_qcd_view_hotkeys()

def update_qcd_view_edit_mode_hotkeys_status(self, context):
    if self.enable_qcd_view_edit_mode_hotkeys:
        qcd_init.register_qcd_view_edit_mode_hotkeys()
    else:
        qcd_init.unregister_qcd_view_edit_mode_hotkeys()

def update_qcd_3dview_header_widget_status(self, context):
    if self.enable_qcd_3dview_header_widget:
        qcd_init.register_qcd_3dview_header_widget()
    else:
        qcd_init.unregister_qcd_3dview_header_widget()

def get_tool_text(self):
    if self.tool_text_override:
        return self["tool_text_color"]
    else:
        color = bpy.context.preferences.themes[0].user_interface.wcol_tool.text
        self["tool_text_color"] = color[0], color[1], color[2]
        return self["tool_text_color"]

def set_tool_text(self, values):
    self["tool_text_color"] = values[0], values[1], values[2]


def get_tool_text_sel(self):
    if self.tool_text_sel_override:
        return self["tool_text_sel_color"]
    else:
        color = bpy.context.preferences.themes[0].user_interface.wcol_tool.text_sel
        self["tool_text_sel_color"] = color[0], color[1], color[2]
        return self["tool_text_sel_color"]

def set_tool_text_sel(self, values):
    self["tool_text_sel_color"] = values[0], values[1], values[2]


def get_tool_inner(self):
    if self.tool_inner_override:
        return self["tool_inner_color"]
    else:
        color = bpy.context.preferences.themes[0].user_interface.wcol_tool.inner
        self["tool_inner_color"] = color[0], color[1], color[2], color[3]
        return self["tool_inner_color"]

def set_tool_inner(self, values):
    self["tool_inner_color"] = values[0], values[1], values[2], values[3]


def get_tool_inner_sel(self):
    if self.tool_inner_sel_override:
        return self["tool_inner_sel_color"]
    else:
        color = bpy.context.preferences.themes[0].user_interface.wcol_tool.inner_sel
        self["tool_inner_sel_color"] = color[0], color[1], color[2], color[3]
        return self["tool_inner_sel_color"]

def set_tool_inner_sel(self, values):
    self["tool_inner_sel_color"] = values[0], values[1], values[2], values[3]


def get_tool_outline(self):
    if self.tool_outline_override:
        return self["tool_outline_color"]
    else:
        color = bpy.context.preferences.themes[0].user_interface.wcol_tool.outline
        self["tool_outline_color"] = color[0], color[1], color[2], color[3]
        return self["tool_outline_color"]

def set_tool_outline(self, values):
    self["tool_outline_color"] = values[0], values[1], values[2], values[3]


def get_menu_back_text(self):
    if self.menu_back_text_override:
        return self["menu_back_text_color"]
    else:
        color = bpy.context.preferences.themes[0].user_interface.wcol_menu_back.text
        self["menu_back_text_color"] = color[0], color[1], color[2]
        return self["menu_back_text_color"]

def set_menu_back_text(self, values):
    self["menu_back_text_color"] = values[0], values[1], values[2]


def get_menu_back_inner(self):
    if self.menu_back_inner_override:
        return self["menu_back_inner_color"]
    else:
        color = bpy.context.preferences.themes[0].user_interface.wcol_menu_back.inner
        self["menu_back_inner_color"] = color[0], color[1], color[2], color[3]
        return self["menu_back_inner_color"]

def set_menu_back_inner(self, values):
    self["menu_back_inner_color"] = values[0], values[1], values[2], values[3]


def get_menu_back_outline(self):
    if self.menu_back_outline_override:
        return self["menu_back_outline_color"]
    else:
        color = bpy.context.preferences.themes[0].user_interface.wcol_menu_back.outline
        self["menu_back_outline_color"] = color[0], color[1], color[2], color[3]
        return self["menu_back_outline_color"]

def set_menu_back_outline(self, values):
    self["menu_back_outline_color"] = values[0], values[1], values[2], values[3]


def get_tooltip_text(self):
    if self.tooltip_text_override:
        return self["tooltip_text_color"]
    else:
        color = bpy.context.preferences.themes[0].user_interface.wcol_tooltip.text
        self["tooltip_text_color"] = color[0], color[1], color[2]
        return self["tooltip_text_color"]

def set_tooltip_text(self, values):
    self["tooltip_text_color"] = values[0], values[1], values[2]


def get_tooltip_inner(self):
    if self.tooltip_inner_override:
        return self["tooltip_inner_color"]
    else:
        color = bpy.context.preferences.themes[0].user_interface.wcol_tooltip.inner
        self["tooltip_inner_color"] = color[0], color[1], color[2], color[3]
        return self["tooltip_inner_color"]

def set_tooltip_inner(self, values):
    self["tooltip_inner_color"] = values[0], values[1], values[2], values[3]


def get_tooltip_outline(self):
    if self.tooltip_outline_override:
        return self["tooltip_outline_color"]
    else:
        color = bpy.context.preferences.themes[0].user_interface.wcol_tooltip.outline
        self["tooltip_outline_color"] = color[0], color[1], color[2], color[3]
        return self["tooltip_outline_color"]

def set_tooltip_outline(self, values):
    self["tooltip_outline_color"] = values[0], values[1], values[2], values[3]


class CMPreferences(AddonPreferences):
    bl_idname = __package__

    # ENABLE DISABLE OBJECTS OVERRIDE
    enable_disable_objects_override: BoolProperty(
        name="Disable objects instead of Hiding",
        description=(
            "Replace the object hiding hotkeys with object disabling hotkeys and add them to the Object->Show/Hide menu.\n"
            "Disabling objects prevents them from being automatically shown again when collections are unexcluded"
            ),
        default=False,
        update=update_disable_objects_hotkeys_status,
        )

    # ENABLE QCD BOOLS
    enable_qcd: BoolProperty(
        name="QCD",
        description="Enable/Disable QCD System.\nThe Quick Content Display system allows you to specify collections as QCD \"slots\" up to a maximum of 20. You can then interact with them through numerical hotkeys, a popup move widget, and a 3D Viewport header widget",
        default=True,
        update=update_qcd_status,
        )

    enable_qcd_view_hotkeys: BoolProperty(
        name="QCD Hotkeys",
        description="Enable/Disable the numerical hotkeys to view QCD slots",
        default=True,
        update=update_qcd_view_hotkeys_status,
        )

    enable_qcd_view_edit_mode_hotkeys: BoolProperty(
        name="QCD Edit Mode Hotkeys",
        description="Enable/Disable the numerical hotkeys to view QCD slots in Edit Mode",
        default=False,
        update=update_qcd_view_edit_mode_hotkeys_status,
        )

    enable_qcd_3dview_header_widget: BoolProperty(
        name="QCD 3D Viewport Header Widget",
        description="Enable/Disable the 3D Viewport header widget.  This widget graphically represents the 20 QCD slots and allows you to interact with them through the GUI",
        default=True,
        update=update_qcd_3dview_header_widget_status,
        )


    # OVERRIDE BOOLS
    tool_text_override: BoolProperty(
        name="Text",
        description="Override Theme Text Color",
        default=False,
        )

    tool_text_sel_override: BoolProperty(
        name="Selection",
        description="Override Theme Text Selection Color",
        default=False,
        )

    tool_inner_override: BoolProperty(
        name="Inner",
        description="Override Theme Inner Color",
        default=False,
        )

    tool_inner_sel_override: BoolProperty(
        name="Selection",
        description="Override Theme Inner Selection Color",
        default=False,
        )

    tool_outline_override: BoolProperty(
        name="Outline",
        description="Override Theme Outline Color",
        default=False,
        )

    menu_back_text_override: BoolProperty(
        name="Text",
        description="Override Theme Text Color",
        default=False,
        )

    menu_back_inner_override: BoolProperty(
        name="Inner",
        description="Override Theme Inner Color",
        default=False,
        )

    menu_back_outline_override: BoolProperty(
        name="Outline",
        description="Override Theme Outline Color",
        default=False,
        )

    tooltip_text_override: BoolProperty(
        name="Text",
        description="Override Theme Text Color",
        default=False,
        )

    tooltip_inner_override: BoolProperty(
        name="Inner",
        description="Override Theme Inner Color",
        default=False,
        )

    tooltip_outline_override: BoolProperty(
        name="Outline",
        description="Override Theme Outline Color",
        default=False,
        )


    # OVERRIDE COLORS
    qcd_ogl_widget_tool_text: FloatVectorProperty(
        name="",
        description="QCD Move Widget Tool Text Color",
        default=bpy.context.preferences.themes[0].user_interface.wcol_tool.text,
        subtype='COLOR_GAMMA',
        min=0.0,
        max=1.0,
        get=get_tool_text,
        set=set_tool_text,
        )

    qcd_ogl_widget_tool_text_sel: FloatVectorProperty(
        name="",
        description="QCD Move Widget Tool Text Selection Color",
        default=bpy.context.preferences.themes[0].user_interface.wcol_tool.text_sel,
        subtype='COLOR_GAMMA',
        min=0.0,
        max=1.0,
        get=get_tool_text_sel,
        set=set_tool_text_sel,
        )

    qcd_ogl_widget_tool_inner: FloatVectorProperty(
        name="",
        description="QCD Move Widget Tool Inner Color",
        default=bpy.context.preferences.themes[0].user_interface.wcol_tool.inner,
        subtype='COLOR_GAMMA',
        min=0.0,
        max=1.0,
        size=4,
        get=get_tool_inner,
        set=set_tool_inner,
        )

    qcd_ogl_widget_tool_inner_sel: FloatVectorProperty(
        name="",
        description="QCD Move Widget Tool Inner Selection Color",
        default=bpy.context.preferences.themes[0].user_interface.wcol_tool.inner_sel,
        subtype='COLOR_GAMMA',
        min=0.0,
        max=1.0,
        size=4,
        get=get_tool_inner_sel,
        set=set_tool_inner_sel,
        )

    qcd_ogl_widget_tool_outline: FloatVectorProperty(
        name="",
        description="QCD Move Widget Tool Outline Color",
        default=bpy.context.preferences.themes[0].user_interface.wcol_tool.outline,
        subtype='COLOR_GAMMA',
        min=0.0,
        max=1.0,
        size=4,
        get=get_tool_outline,
        set=set_tool_outline,
        )

    qcd_ogl_widget_menu_back_text: FloatVectorProperty(
        name="",
        description="QCD Move Widget Menu Back Text Color",
        default=bpy.context.preferences.themes[0].user_interface.wcol_menu_back.text,
        subtype='COLOR_GAMMA',
        min=0.0,
        max=1.0,
        get=get_menu_back_text,
        set=set_menu_back_text,
        )

    qcd_ogl_widget_menu_back_inner: FloatVectorProperty(
        name="",
        description="QCD Move Widget Menu Back Inner Color",
        default=bpy.context.preferences.themes[0].user_interface.wcol_menu_back.inner,
        subtype='COLOR_GAMMA',
        min=0.0,
        max=1.0,
        size=4,
        get=get_menu_back_inner,
        set=set_menu_back_inner,
        )

    qcd_ogl_widget_menu_back_outline: FloatVectorProperty(
        name="",
        description="QCD Move Widget Menu Back Outline Color",
        default=bpy.context.preferences.themes[0].user_interface.wcol_menu_back.outline,
        subtype='COLOR_GAMMA',
        min=0.0,
        max=1.0,
        size=4,
        get=get_menu_back_outline,
        set=set_menu_back_outline,
        )

    qcd_ogl_widget_tooltip_text: FloatVectorProperty(
        name="",
        description="QCD Move Widget Tooltip Text Color",
        default=bpy.context.preferences.themes[0].user_interface.wcol_tooltip.text,
        subtype='COLOR_GAMMA',
        min=0.0,
        max=1.0,
        get=get_tooltip_text,
        set=set_tooltip_text,
        )

    qcd_ogl_widget_tooltip_inner: FloatVectorProperty(
        name="",
        description="QCD Move Widget Tooltip Inner Color",
        default=bpy.context.preferences.themes[0].user_interface.wcol_tooltip.inner,
        subtype='COLOR_GAMMA',
        min=0.0,
        max=1.0,
        size=4,
        get=get_tooltip_inner,
        set=set_tooltip_inner,
        )

    qcd_ogl_widget_tooltip_outline: FloatVectorProperty(
        name="",
        description="QCD Move Widget Tooltip Outline Color",
        default=bpy.context.preferences.themes[0].user_interface.wcol_tooltip.outline,
        subtype='COLOR_GAMMA',
        min=0.0,
        max=1.0,
        size=4,
        get=get_tooltip_outline,
        set=set_tooltip_outline,
        )

    # NON ACTIVE ICON ALPHA
    qcd_ogl_selected_icon_alpha: FloatProperty(
        name="Selected Icon Alpha",
        description="Set the 'Selected' icon's alpha value",
        default=0.9,
        min=0.0,
        max=1.0,
        )

    qcd_ogl_objects_icon_alpha: FloatProperty(
        name="Objects Icon Alpha",
        description="Set the 'Objects' icon's alpha value",
        default=0.5,
        min=0.0,
        max=1.0,
        )

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        box.row().prop(self, "enable_disable_objects_override")
        box.row().prop(self, "enable_qcd")

        if not self.enable_qcd:
            return

        box.row().prop(self, "enable_qcd_view_hotkeys")
        box.row().prop(self, "enable_qcd_view_edit_mode_hotkeys")
        box.row().prop(self, "enable_qcd_3dview_header_widget")

        box.row().label(text="QCD Move Widget")

        # TOOL OVERRIDES
        tool_box = box.box()
        tool_box.row().label(text="Tool Theme Overrides:")

        overrides = tool_box.split(align=True)

        # Column 1
        col = overrides.column()
        col.alignment = 'RIGHT'

        # Text
        override = col.row(align=True)
        override.alignment = 'RIGHT'
        checkbox = override.row(align=True)
        checkbox.alignment = 'RIGHT'
        checkbox.label(text="Text")
        checkbox.prop(self, "tool_text_override", text="")
        color_picker = override.row(align=True)
        color_picker.alignment = 'RIGHT'
        color_picker.enabled = self.tool_text_override
        color_picker.prop(self, "qcd_ogl_widget_tool_text")

        # Text Selection
        override = col.row(align=True)
        override.alignment = 'RIGHT'
        checkbox = override.row(align=True)
        checkbox.alignment = 'RIGHT'
        checkbox.label(text="Selection")
        checkbox.prop(self, "tool_text_sel_override", text="")
        color_picker = override.row(align=True)
        color_picker.alignment = 'RIGHT'
        color_picker.enabled = self.tool_text_sel_override
        color_picker.prop(self, "qcd_ogl_widget_tool_text_sel")

        # Column 2
        col = overrides.column()
        col.alignment = 'RIGHT'

        # Inner
        override = col.row(align=True)
        override.alignment = 'RIGHT'
        checkbox = override.row(align=True)
        checkbox.alignment = 'RIGHT'
        checkbox.label(text="Inner")
        checkbox.prop(self, "tool_inner_override", text="")
        color_picker = override.row(align=True)
        color_picker.alignment = 'RIGHT'
        color_picker.enabled = self.tool_inner_override
        color_picker.prop(self, "qcd_ogl_widget_tool_inner")

        # Inner Selection
        override = col.row(align=True)
        override.alignment = 'RIGHT'
        checkbox = override.row(align=True)
        checkbox.alignment = 'RIGHT'
        checkbox.label(text="Selection")
        checkbox.prop(self, "tool_inner_sel_override", text="")
        color_picker = override.row(align=True)
        color_picker.alignment = 'RIGHT'
        color_picker.enabled = self.tool_inner_sel_override
        color_picker.prop(self, "qcd_ogl_widget_tool_inner_sel")

        # Outline
        override = col.row(align=True)
        override.alignment = 'RIGHT'
        checkbox = override.row(align=True)
        checkbox.alignment = 'RIGHT'
        checkbox.label(text="Outline")
        checkbox.prop(self, "tool_outline_override", text="")
        color_picker = override.row(align=True)
        color_picker.alignment = 'RIGHT'
        color_picker.enabled = self.tool_outline_override
        color_picker.prop(self, "qcd_ogl_widget_tool_outline")

        # Icon Alpha
        tool_box.row().label(text="Icon Alpha:")
        icon_fade_row = tool_box.row()
        icon_fade_row.alignment = 'EXPAND'
        icon_fade_row.prop(self, "qcd_ogl_selected_icon_alpha", text="Selected")
        icon_fade_row.prop(self, "qcd_ogl_objects_icon_alpha", text="Objects")


        # MENU BACK OVERRIDES
        menu_back_box = box.box()
        menu_back_box.row().label(text="Menu Back Theme Overrides:")

        overrides = menu_back_box.split(align=True)

        # Column 1
        col = overrides.column()
        col.alignment = 'RIGHT'

        # Text
        override = col.row(align=True)
        override.alignment = 'RIGHT'
        checkbox = override.row(align=True)
        checkbox.alignment = 'RIGHT'
        checkbox.label(text="Text")
        checkbox.prop(self, "menu_back_text_override", text="")
        color_picker = override.row(align=True)
        color_picker.alignment = 'RIGHT'
        color_picker.enabled = self.menu_back_text_override
        color_picker.prop(self, "qcd_ogl_widget_menu_back_text")

        # Column 2
        col = overrides.column()
        col.alignment = 'RIGHT'

        # Inner
        override = col.row(align=True)
        override.alignment = 'RIGHT'
        checkbox = override.row(align=True)
        checkbox.alignment = 'RIGHT'
        checkbox.label(text="Inner")
        checkbox.prop(self, "menu_back_inner_override", text="")
        color_picker = override.row(align=True)
        color_picker.alignment = 'RIGHT'
        color_picker.enabled = self.menu_back_inner_override
        color_picker.prop(self, "qcd_ogl_widget_menu_back_inner")

        # Outline
        override = col.row(align=True)
        override.alignment = 'RIGHT'
        checkbox = override.row(align=True)
        checkbox.alignment = 'RIGHT'
        checkbox.label(text="Outline")
        checkbox.prop(self, "menu_back_outline_override", text="")
        color_picker = override.row(align=True)
        color_picker.alignment = 'RIGHT'
        color_picker.enabled = self.menu_back_outline_override
        color_picker.prop(self, "qcd_ogl_widget_menu_back_outline")


        # TOOLTIP OVERRIDES
        tooltip_box = box.box()
        tooltip_box.row().label(text="Tooltip Theme Overrides:")

        overrides = tooltip_box.split(align=True)

        # Column 1
        col = overrides.column()
        col.alignment = 'RIGHT'

        # Text
        override = col.row(align=True)
        override.alignment = 'RIGHT'
        checkbox = override.row(align=True)
        checkbox.alignment = 'RIGHT'
        checkbox.label(text="Text")
        checkbox.prop(self, "tooltip_text_override", text="")
        color_picker = override.row(align=True)
        color_picker.alignment = 'RIGHT'
        color_picker.enabled = self.tooltip_text_override
        color_picker.prop(self, "qcd_ogl_widget_tooltip_text")

        # Column 2
        col = overrides.column()
        col.alignment = 'RIGHT'

        # Inner
        override = col.row(align=True)
        override.alignment = 'RIGHT'
        checkbox = override.row(align=True)
        checkbox.alignment = 'RIGHT'
        checkbox.label(text="Inner")
        checkbox.prop(self, "tooltip_inner_override", text="")
        color_picker = override.row(align=True)
        color_picker.alignment = 'RIGHT'
        color_picker.enabled = self.tooltip_inner_override
        color_picker.prop(self, "qcd_ogl_widget_tooltip_inner")

        # Outline
        override = col.row(align=True)
        override.alignment = 'RIGHT'
        checkbox = override.row(align=True)
        checkbox.alignment = 'RIGHT'
        checkbox.label(text="Outline")
        checkbox.prop(self, "tooltip_outline_override", text="")
        color_picker = override.row(align=True)
        color_picker.alignment = 'RIGHT'
        color_picker.enabled = self.tooltip_outline_override
        color_picker.prop(self, "qcd_ogl_widget_tooltip_outline")
