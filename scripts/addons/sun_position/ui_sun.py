# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Operator, Menu
from bl_operators.presets import AddPresetBase
from bl_ui.utils import PresetPanel
import os
from math import degrees

from .sun_calc import format_lat_long, format_time, format_hms, sun


# -------------------------------------------------------------------
# Choice list of places, month and day at 12:00 noon
# -------------------------------------------------------------------


class SUNPOS_PT_Presets(PresetPanel, bpy.types.Panel):
    bl_label = "Sun Position Presets"
    preset_subdir = "operator/sun_position"
    preset_operator = "script.execute_preset"
    preset_add_operator = "world.sunpos_add_preset"


class SUNPOS_OT_AddPreset(AddPresetBase, Operator):
    '''Add Sun Position preset'''
    bl_idname = "world.sunpos_add_preset"
    bl_label = "Add Sun Position preset"
    preset_menu = "SUNPOS_PT_Presets"

    # variable used for all preset values
    preset_defines = [
        "sun_props = bpy.context.scene.sun_pos_properties"
    ]

    # properties to store in the preset
    preset_values = [
        "sun_props.day",
        "sun_props.month",
        "sun_props.time",
        "sun_props.year",
        "sun_props.UTC_zone",
        "sun_props.use_daylight_savings",
        "sun_props.latitude",
        "sun_props.longitude",
    ]

    # where to store the preset
    preset_subdir = "operator/sun_position"


# -------------------------------------------------------------------
#
#   Draw the Sun Panel, sliders, et. al.
#
# -------------------------------------------------------------------

class SUNPOS_PT_Panel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"
    bl_label = "Sun Position"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header_preset(self, _context):
        SUNPOS_PT_Presets.draw_panel_header(self.layout)

    def draw(self, context):
        sun_props = context.scene.sun_pos_properties
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(sun_props, "usage_mode", expand=True)
        layout.separator()

        if sun_props.usage_mode == "HDR":
            self.draw_environment_mode_panel(context)
        else:
            self.draw_normal_mode_panel(context)

    def draw_environment_mode_panel(self, context):
        sun_props = context.scene.sun_pos_properties
        layout = self.layout

        col = layout.column(align=True)
        col.prop_search(sun_props, "sun_object",
                        context.view_layer, "objects")
        if context.scene.world is not None:
            if context.scene.world.node_tree is not None:
                col.prop_search(sun_props, "hdr_texture",
                                context.scene.world.node_tree, "nodes")
            else:
                col.label(text="Please activate Use Nodes in the World panel.",
                          icon="ERROR")
        else:
            col.label(text="Please select World in the World panel.",
                      icon="ERROR")

        layout.use_property_decorate = True

        col = layout.column(align=True)
        col.prop(sun_props, "bind_to_sun", text="Bind Texture to Sun")
        col.prop(sun_props, "hdr_azimuth")
        row = col.row(align=True)
        row.active = not sun_props.bind_to_sun
        row.prop(sun_props, "hdr_elevation")
        col.prop(sun_props, "sun_distance")
        col.separator()

        col = layout.column(align=True)
        row = col.row(align=True)
        row.enabled = not sun_props.bind_to_sun
        row.operator("world.sunpos_show_hdr", icon='LIGHT_SUN')

    def draw_normal_mode_panel(self, context):
        sun_props = context.scene.sun_pos_properties
        addon_prefs = context.preferences.addons[__package__].preferences
        layout = self.layout

        col = layout.column(align=True)
        col.prop(sun_props, "sun_object")
        col.separator()

        col.prop(sun_props, "object_collection")
        if sun_props.object_collection:
            col.prop(sun_props, "object_collection_type")
            if sun_props.object_collection_type == 'DIURNAL':
                col.prop(sun_props, "time_spread")
        col.separator()

        if context.scene.world is not None:
            if context.scene.world.node_tree is not None:
                col.prop_search(sun_props, "sky_texture",
                                context.scene.world.node_tree, "nodes")
            else:
                col.label(text="Please activate Use Nodes in the World panel.",
                          icon="ERROR")
        else:
            col.label(text="Please select World in the World panel.",
                      icon="ERROR")

        if addon_prefs.show_overlays:
            col = layout.column(align=True, heading="Show")
            col.prop(sun_props, "show_north", text="North")
            col.prop(sun_props, "show_analemmas", text="Analemmas")
            col.prop(sun_props, "show_surface", text="Surface")

        if addon_prefs.show_refraction:
            col = layout.column(align=True, heading="Use")
            col.prop(sun_props, "use_refraction", text="Refraction")


class SUNPOS_PT_Location(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"
    bl_label = "Location"
    bl_parent_id = "SUNPOS_PT_Panel"

    @classmethod
    def poll(self, context):
        sun_props = context.scene.sun_pos_properties
        return sun_props.usage_mode != "HDR"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        sun_props = context.scene.sun_pos_properties
        addon_prefs = context.preferences.addons[__package__].preferences

        col = layout.column(align=True)
        col.prop(sun_props, "coordinates", icon='URL')
        col.prop(sun_props, "latitude")
        col.prop(sun_props, "longitude")

        col.separator()

        col = layout.column(align=True)
        col.prop(sun_props, "north_offset", text="North Offset")

        if addon_prefs.show_az_el:
            col = layout.column(align=True)
            col.prop(sun_props, "sun_elevation", text="Elevation")
            col.prop(sun_props, "sun_azimuth", text="Azimuth")
            col.separator()

        col = layout.column()
        col.prop(sun_props, "sun_distance")
        col.separator()


class SUNPOS_PT_Time(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"
    bl_label = "Time"
    bl_parent_id = "SUNPOS_PT_Panel"

    @classmethod
    def poll(self, context):
        sun_props = context.scene.sun_pos_properties
        return sun_props.usage_mode != "HDR"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        sun_props = context.scene.sun_pos_properties
        addon_prefs = context.preferences.addons[__package__].preferences

        col = layout.column(align=True)
        col.prop(sun_props, "use_day_of_year")
        if sun_props.use_day_of_year:
            col.prop(sun_props, "day_of_year")
        else:
            col.prop(sun_props, "day")
            col.prop(sun_props, "month")
        col.prop(sun_props, "year")
        col.separator()

        col = layout.column(align=True)
        col.prop(sun_props, "time", text="Time", text_ctxt="Hour")
        col.prop(sun_props, "UTC_zone")
        col.prop(sun_props, "use_daylight_savings")
        col.separator()

        local_time = format_time(sun_props.time,
                                 sun_props.use_daylight_savings)
        utc_time = format_time(sun_props.time,
                               sun_props.use_daylight_savings,
                               sun_props.UTC_zone)

        col = layout.column(align=True)
        col.alignment = 'CENTER'

        split = col.split(factor=0.5, align=True)
        sub = split.column(align=True)
        sub.alignment = 'RIGHT'
        sub.label(text="Time Local:")
        sub.label(text="UTC:")

        sub = split.column(align=True)
        sub.label(text=local_time)
        sub.label(text=utc_time)
        col.separator()

        if addon_prefs.show_rise_set:
            sunrise = format_hms(sun.sunrise)
            sunset = format_hms(sun.sunset)

            col = layout.column(align=True)
            col.alignment = 'CENTER'

            split = col.split(factor=0.5, align=True)
            sub = split.column(align=True)
            sub.alignment = 'RIGHT'
            sub.label(text="Sunrise:")
            sub.label(text="Sunset:")

            sub = split.column(align=True)
            sub.label(text=sunrise)
            sub.label(text=sunset)

        col.separator()
