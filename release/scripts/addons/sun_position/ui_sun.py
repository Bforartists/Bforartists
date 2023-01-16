# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Operator, Menu
from bl_operators.presets import AddPresetBase
import os

from .sun_calc import (format_lat_long, format_time, format_hms, sun)


# -------------------------------------------------------------------
# Choice list of places, month and day at 12:00 noon
# -------------------------------------------------------------------


class SUNPOS_MT_Presets(Menu):
    bl_label = "Sun Position Presets"
    preset_subdir = "operator/sun_position"
    preset_operator = "script.execute_preset"
    draw = Menu.draw_preset


class SUNPOS_OT_AddPreset(AddPresetBase, Operator):
    '''Add Sun Position preset'''
    bl_idname = "world.sunpos_add_preset"
    bl_label = "Add Sun Position preset"
    preset_menu = "SUNPOS_MT_Presets"

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

    def draw(self, context):
        sp = context.scene.sun_pos_properties
        p = context.preferences.addons[__package__].preferences
        layout = self.layout
        self.draw_panel(context, sp, p, layout)

    def draw_panel(self, context, sp, p, layout):
        col = self.layout.column(align=True)
        col.label(text="Usage Mode")
        row = col.row()
        row.prop(sp, "usage_mode", expand=True)
        col.separator()
        if sp.usage_mode == "HDR":
            self.draw_environ_mode_panel(context, sp, p, layout)
        else:
            self.draw_normal_mode_panel(context, sp, p, layout)

    def draw_environ_mode_panel(self, context, sp, p, layout):
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True,
                             even_rows=False, align=False)

        col = flow.column(align=True)
        col.label(text="Environment Texture")

        if context.scene.world is not None:
            if context.scene.world.node_tree is not None:
                col.prop_search(sp, "hdr_texture",
                                context.scene.world.node_tree, "nodes", text="")
            else:
                col.label(text="Please activate Use Nodes in the World panel.",
                          icon="ERROR")
        else:
            col.label(text="Please select World in the World panel.",
                      icon="ERROR")

        col.separator()

        col = flow.column(align=True)
        col.label(text="Sun Object")
        col.prop_search(sp, "sun_object",
                        context.view_layer, "objects", text="")
        col.separator()

        col = flow.column(align=True)
        col.prop(sp, "sun_distance")
        if not sp.bind_to_sun:
            col.prop(sp, "hdr_elevation")
        col.prop(sp, "hdr_azimuth")
        col.separator()

        col = flow.column(align=True)
        if sp.bind_to_sun:
            col.prop(sp, "bind_to_sun", toggle=True, icon="CONSTRAINT",
                     text="Release binding")
        else:
            col.prop(sp, "bind_to_sun", toggle=True, icon="CONSTRAINT",
                     text="Bind Texture to Sun")

        row = col.row(align=True)
        row.enabled = not sp.bind_to_sun
        row.operator("world.sunpos_show_hdr", icon='LIGHT_SUN')

    def draw_normal_mode_panel(self, context, sp, p, layout):
        if p.show_time_place:
            row = layout.row(align=True)
            row.menu(SUNPOS_MT_Presets.__name__, text=SUNPOS_MT_Presets.bl_label)
            row.operator(SUNPOS_OT_AddPreset.bl_idname, text="", icon='ADD')
            row.operator(SUNPOS_OT_AddPreset.bl_idname, text="", icon='REMOVE').remove_active = True

        col = layout.column(align=True)
        col.use_property_split = True
        col.use_property_decorate = False
        col.prop(sp, "sun_object")
        col.separator()

        col.prop(sp, "object_collection")
        if sp.object_collection:
            col.prop(sp, "object_collection_type")
            if sp.object_collection_type == 'DIURNAL':
                col.prop(sp, "time_spread")
        col.separator()

        if context.scene.world is not None:
            if context.scene.world.node_tree is not None:
                col.prop_search(sp, "sky_texture",
                                context.scene.world.node_tree, "nodes")
            else:
                col.label(text="Please activate Use Nodes in the World panel.",
                          icon="ERROR")
        else:
            col.label(text="Please select World in the World panel.",
                      icon="ERROR")

class SUNPOS_PT_Location(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"
    bl_label = "Location"
    bl_parent_id = "SUNPOS_PT_Panel"

    @classmethod
    def poll(self, context):
        sp = context.scene.sun_pos_properties
        return sp.usage_mode != "HDR"

    def draw(self, context):
        layout = self.layout
        sp = context.scene.sun_pos_properties
        p = context.preferences.addons[__package__].preferences

        col = layout.column(align=True)
        col.label(text="Enter Coordinates")
        col.prop(sp, "co_parser", text='', icon='URL')

        layout.separator()

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)

        col = flow.column(align=True)
        col.prop(sp, "latitude")
        if p.show_dms:
            row = col.row()
            row.alignment = 'RIGHT'
            row.label(text=format_lat_long(sp.latitude, True))

        col = flow.column(align=True)
        col.prop(sp, "longitude")
        if p.show_dms:
            row = col.row()
            row.alignment = 'RIGHT'
            row.label(text=format_lat_long(sp.longitude, False))
        col.separator()

        if p.show_north:
            col = flow.column(align=True)
            col.prop(sp, "show_north", toggle=True)
            col.prop(sp, "north_offset")
            col.separator()

        if p.show_surface or p.show_analemmas:
            col = flow.column(align=True)
            if p.show_surface:
                col.prop(sp, "show_surface", toggle=True)
            if p.show_analemmas:
                col.prop(sp, "show_analemmas", toggle=True)
            col.separator()

        if p.show_az_el:
            col = flow.column(align=True)
            split = col.split(factor=0.4, align=True)
            split.label(text="Azimuth:")
            split.label(text=str(round(sun.azimuth, 3)) + "°")
            split = col.split(factor=0.4, align=True)
            split.label(text="Elevation:")
            split.label(text=str(round(sun.elevation, 3)) + "°")
            col.separator()

        if p.show_refraction:
            col = flow.column()
            col.prop(sp, "use_refraction")
            col.separator()

        col = flow.column()
        col.prop(sp, "sun_distance")
        col.separator()


class SUNPOS_PT_Time(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"
    bl_label = "Time"
    bl_parent_id = "SUNPOS_PT_Panel"

    @classmethod
    def poll(self, context):
        sp = context.scene.sun_pos_properties
        return sp.usage_mode != "HDR"

    def draw(self, context):
        layout = self.layout
        sp = context.scene.sun_pos_properties
        p = context.preferences.addons[__package__].preferences

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)

        col = flow.column(align=True)
        col.prop(sp, "use_day_of_year",
                 icon='SORTTIME')
        if sp.use_day_of_year:
            col.prop(sp, "day_of_year")
        else:
            col.prop(sp, "day")
            col.prop(sp, "month")
        col.prop(sp, "year")
        col.separator()

        col = flow.column(align=True)
        col.prop(sp, "time")
        col.prop(sp, "UTC_zone")
        if p.show_daylight_savings:
            col.prop(sp, "use_daylight_savings")
        col.separator()

        col = flow.column(align=True)
        lt = format_time(sp.time,
                         p.show_daylight_savings and sp.use_daylight_savings,
                         sp.longitude)
        ut = format_time(sp.time,
                         p.show_daylight_savings and sp.use_daylight_savings,
                         sp.longitude,
                         sp.UTC_zone)
        col.alignment = 'CENTER'

        split = col.split(factor=0.5, align=True)
        split.label(text="Local:", icon='TIME')
        split.label(text=lt)
        split = col.split(factor=0.5, align=True)
        split.label(text="UTC:", icon='PREVIEW_RANGE')
        split.label(text=ut)
        col.separator()


        col = flow.column(align=True)
        col.alignment = 'CENTER'
        if p.show_rise_set:
            sr = format_hms(sun.sunrise.time)
            ss = format_hms(sun.sunset.time)

            split = col.split(factor=0.5, align=True)
            split.label(text="Sunrise:", icon='LIGHT_SUN')
            split.label(text=sr)
            split = col.split(factor=0.5, align=True)
            split.label(text="Sunset:", icon='SOLO_ON')
            split.label(text=ss)

        col.separator()
