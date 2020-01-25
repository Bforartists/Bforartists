### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

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


class SUNPOS_OT_DefaultPresets(Operator):
    '''Copy Sun Position default presets'''
    bl_idname = "world.sunpos_default_presets"
    bl_label = "Copy Sun Position default presets"

    def execute(self, context):
        preset_dirpath = bpy.utils.user_resource('SCRIPTS', path="presets/operator/sun_position", create=True)
        #                       [month, day, time, UTC, lat, lon, dst]
        presets = {"chongqing.py": [10, 1,  7.18,  8, 29.5583,  106.567, False],
                   "sao_paulo.py": [9,  7,  12.0, -3,  -23.55, -46.6333, False],
                   "kinshasa.py":  [6,  30, 12.0,  1,  -4.325,  15.3222, False],
                   "london.py":    [6,  11, 12.0,  0, 51.5072,  -0.1275, True],
                   "new_york.py":  [7,  4,  12.0, -5, 40.6611, -73.9439, True],
                   "sydney.py":    [1,  26, 17.6, 10, -33.865,  151.209, False]}

        script = '''import bpy
sun_props = bpy.context.scene.sun_pos_properties

sun_props.month = {:d}
sun_props.day = {:d}
sun_props.time = {:f}
sun_props.UTC_zone = {:d}
sun_props.latitude = {:f}
sun_props.longitude = {:f}
sun_props.use_daylight_savings = {}
'''

        for path, p in presets.items():
            print(p)
            with open(os.path.join(preset_dirpath, path), 'w') as f:
                f.write(script.format(*p))

        return {'FINISHED'}

# -------------------------------------------------------------------
#
#   Draw the Sun Panel, sliders, et. al.
#
# -------------------------------------------------------------------

class SUNPOS_PT_Panel(bpy.types.Panel):
    bl_idname = "SUNPOS_PT_world"
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
        self.layout.label(text="Usage mode:")
        self.layout.prop(sp, "usage_mode", expand=True)
        if sp.usage_mode == "HDR":
            self.draw_environ_mode_panel(context, sp, p, layout)
        else:
            self.draw_normal_mode_panel(context, sp, p, layout)

    def draw_environ_mode_panel(self, context, sp, p, layout):
        box = self.layout.box()
        flow = box.grid_flow(row_major=True, columns=0, even_columns=True,
                             even_rows=False, align=False)

        col = flow.column()
        col.label(text="Environment texture:")
        col.prop_search(sp, "hdr_texture",
                        context.scene.world.node_tree, "nodes", text="")
        col.separator()

        col = flow.column()
        col.label(text="Sun object:")
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
        row1 = col.row()
        if sp.bind_to_sun:
            prop_text="Release binding"
        else:
            prop_text="Bind Texture to Sun "
        row1.prop(sp, "bind_to_sun", toggle=True, icon="CONSTRAINT",
                  text=prop_text)

        row = col.row()
        row.enabled = not sp.bind_to_sun
        row.operator("world.sunpos_show_hdr", icon='LIGHT_SUN')

    def draw_normal_mode_panel(self, context, sp, p, layout):
        if p.show_time_place:
            row = layout.row(align=True)
            row.menu(SUNPOS_MT_Presets.__name__, text=SUNPOS_MT_Presets.bl_label)
            row.operator(SUNPOS_OT_AddPreset.bl_idname, text="", icon='ADD')
            row.operator(SUNPOS_OT_AddPreset.bl_idname, text="", icon='REMOVE').remove_active = True
            row.operator(SUNPOS_OT_DefaultPresets.bl_idname, text="", icon='FILE_REFRESH')

        box = self.layout.box()
        flow = box.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)

        col = flow.column()
        col.prop(sp, "use_sky_texture", text="Cycles sky")
        if sp.use_sky_texture:
            col.prop_search(sp, "sky_texture", context.scene.world.node_tree,
                            "nodes", text="")
        col.separator()

        col = flow.column()
        col.prop(sp, "use_sun_object", text="Use object")
        if sp.use_sun_object:
            col.prop(sp, "sun_object", text="")
        col.separator()

        col = flow.column()
        if p.show_object_collection:
            col.prop(sp, "use_object_collection", text="Use collection")
            if sp.use_object_collection:
                col.prop(sp, "object_collection", text="")
                if sp.object_collection:
                    col.prop(sp, "object_collection_type")
                    if sp.object_collection_type == 'ECLIPTIC':
                        col.prop(sp, "time_spread")

        box = self.layout.box()

        col = box.column(align=True)
        col.label(text="Enter coordinates:")
        col.prop(sp, "co_parser", text='', icon='URL')

        box.separator()

        flow = box.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)

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
            col.prop(sp, "show_north", text="Show North", toggle=True)
            col.prop(sp, "north_offset")
            col.separator()

        if p.show_az_el:
            col = flow.column(align=True)
            row = col.row()
            row.alignment = 'RIGHT'
            row.label(text="Azimuth: " +
                     str(round(sun.azimuth, 3)) + "°")
            row = col.row()
            row.alignment = 'RIGHT'
            row.label(text="Elevation: " +
                     str(round(sun.elevation, 3)) + "°")
            col.separator()

        if p.show_refraction:
            col = flow.column()
            col.prop(sp, "use_refraction", text="Show refraction")
            col.separator()

        col = flow.column()
        col.prop(sp, "sun_distance")


        box = self.layout.box()
        flow = box.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)

        col = flow.column(align=True)
        col.prop(sp, "use_day_of_year",
                 icon='SORTTIME')
        if sp.use_day_of_year:
            col.prop(sp, "day_of_year")
        else:
            col.prop(sp, "month")
            col.prop(sp, "day")
        col.prop(sp, "year")
        col.separator()

        col = flow.column(align=True)
        col.prop(sp, "time")
        col.prop(sp, "UTC_zone")
        if p.show_daylight_savings:
            col.prop(sp, "use_daylight_savings", text="Daylight Savings")
        col.separator()

        lt = format_time(sp.time,
                         p.show_daylight_savings and sp.use_daylight_savings,
                         sp.longitude)
        ut = format_time(sp.time,
                         p.show_daylight_savings and sp.use_daylight_savings,
                         sp.longitude,
                         sp.UTC_zone)
        col = flow.column(align=True)
        col.alignment = 'CENTER'
        col.label(text="Local: " + lt, icon='TIME')
        col.label(text="  UTC: " + ut, icon='PREVIEW_RANGE')
        col.separator()

        col = flow.column(align=True)
        col.alignment = 'CENTER'
        if p.show_rise_set:
            sr = format_hms(sun.sunrise.time)
            ss = format_hms(sun.sunset.time)
            tsr = "Sunrise: " + sr
            tss = " Sunset: " + ss
            col.label(text=tsr, icon='LIGHT_SUN')
            col.label(text=tss, icon='SOLO_ON')
