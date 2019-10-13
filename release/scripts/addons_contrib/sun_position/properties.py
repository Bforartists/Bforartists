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
from bpy.types import AddonPreferences, PropertyGroup
from bpy.props import (StringProperty, EnumProperty, IntProperty,
                       FloatProperty, BoolProperty, PointerProperty)

from .sun_calc import sun_update, parse_coordinates
from .north import north_update


############################################################################
# Sun panel properties
############################################################################


class SunPosProperties(PropertyGroup):
    usage_mode: EnumProperty(
        name="Usage mode",
        description="Operate in normal mode or environment texture mode",
        items=(
            ('NORMAL', "Normal", ""),
            ('HDR', "Sun + HDR texture", ""),
        ),
        default='NORMAL',
        update=sun_update)

    show_map: BoolProperty(
        description="Show world map.",
        default=False,
        update=sun_update)

    use_daylight_savings: BoolProperty(
        description="Daylight savings time adds 1 hour to standard time.",
        default=0,
        update=sun_update)

    use_refraction: BoolProperty(
        description="Show apparent sun position due to refraction.",
        default=1,
        update=sun_update)

    show_north: BoolProperty(
        description="Draws line pointing north.",
        default=0,
        update=north_update)

    north_offset: FloatProperty(
        attr="",
        name="",
        description="North offset in degrees or radians "
                    "from scene's units settings",
        unit="ROTATION",
        soft_min=-3.14159265, soft_max=3.14159265, step=10.00, default=0.00,
        update=sun_update)

    latitude: FloatProperty(
        attr="",
        name="Latitude",
        description="Latitude: (+) Northern (-) Southern",
        soft_min=-90.000, soft_max=90.000,
        step=5, precision=3,
        default=0.000,
        update=sun_update)

    longitude: FloatProperty(
        attr="",
        name="Longitude",
        description="Longitude: (-) West of Greenwich  (+) East of Greenwich",
        soft_min=-180.000, soft_max=180.000,
        step=5, precision=3,
        default=0.000,
        update=sun_update)

    co_parser: StringProperty(
        attr="",
        name="Enter coordinates",
        description="Enter coordinates from an online map",
        update=parse_coordinates)

    month: IntProperty(
        attr="",
        name="Month",
        description="",
        min=1, max=12, default=6,
        update=sun_update)

    day: IntProperty(
        attr="",
        name="Day",
        description="",
        min=1, max=31, default=21,
        update=sun_update)

    year: IntProperty(
        attr="",
        name="Year",
        description="",
        min=1800, max=4000, default=2012,
        update=sun_update)

    use_day_of_year: BoolProperty(
        description="Use a single value for day of year",
        name="Use day of year",
        default=False,
        update=sun_update)

    day_of_year: IntProperty(
        attr="",
        name="Day of year",
        description="",
        min=1, max=366, default=1,
        update=sun_update)

    UTC_zone: IntProperty(
        attr="",
        name="UTC zone",
        description="Time zone: Difference from Greenwich England in hours.",
        min=-12, max=12, default=0,
        update=sun_update)

    time: FloatProperty(
        attr="",
        name="Time",
        description="",
        precision=4,
        soft_min=0.00, soft_max=23.9999, step=1.00, default=12.00,
        update=sun_update)

    sun_distance: FloatProperty(
        attr="",
        name="Distance",
        description="Distance to sun from XYZ axes intersection.",
        unit="LENGTH",
        soft_min=1, soft_max=3000.00, step=10.00, default=50.00,
        update=sun_update)

    use_sun_object: BoolProperty(
        description="Enable sun positioning of named lamp or mesh",
        default=False,
        update=sun_update)

    sun_object: PointerProperty(
        type=bpy.types.Object,
        # default="Sun",
        description="Sun object to set in the scene",
        poll=lambda self, obj: obj.type == 'LIGHT',
        update=sun_update)

    use_object_collection: BoolProperty(
        description="Allow a group of objects to be positioned.",
        default=False,
        update=sun_update)

    object_collection: PointerProperty(
        type=bpy.types.Collection,
        description="Collection of objects used for analemma",
        update=sun_update)

    object_collection_type: EnumProperty(
        name="Display type",
        description="Show object group on ecliptic or as analemma",
        items=(
            ('ECLIPTIC', "On the Ecliptic", ""),
            ('ANALEMMA', "As Analemma", ""),
        ),
        default='ECLIPTIC',
        update=sun_update)

    use_sky_texture: BoolProperty(
        description="Enable use of Cycles' "
                    "sky texture. World nodes must be enabled, "
                    "then set color to Sky Texture.",
        default=False,
        update=sun_update)

    sky_texture: StringProperty(
        default="Sky Texture",
        name="sunSky",
        description="Name of sky texture to be used",
        update=sun_update)

    hdr_texture: StringProperty(
        default="Environment Texture",
        name="envSky",
        description="Name of texture to use. World nodes must be enabled "
                    "and color set to Environment Texture",
        update=sun_update)

    hdr_azimuth: FloatProperty(
        attr="",
        name="Rotation",
        description="Rotation angle of sun and environment texture "
                    "in degrees or radians from scene's units settings",
        unit="ROTATION",
        step=10.0,
        default=0.0, precision=3,
        update=sun_update)

    hdr_elevation: FloatProperty(
        attr="",
        name="Elevation",
        description="Elevation angle of sun",
        unit="ROTATION",
        step=10.0,
        default=0.0, precision=3,
        update=sun_update)

    bind_to_sun: BoolProperty(
        description="If true, Environment texture moves with sun.",
        default=False,
        update=sun_update)

    time_spread: FloatProperty(
        attr="",
        name="Time Spread",
        description="Time period in which to spread object group",
        precision=4,
        soft_min=1.00, soft_max=24.00, step=1.00, default=23.00,
        update=sun_update)


############################################################################
# Preference panel properties
############################################################################


class SunPosAddonPreferences(AddonPreferences):
    bl_idname = __package__

    # map_location: EnumProperty(
    #     name="Map location",
    #     description="Display map in viewport or world panel",
    #     items=(
    #         ('VIEWPORT', "Viewport", ""),
    #         ('PANEL', "Panel", ""),
    #     ),
    #     default='VIEWPORT')

    show_time_place: BoolProperty(
        description="Show time/place presets",
        default=False)

    show_object_collection: BoolProperty(
        description="Use object collection",
        default=True,
        update=sun_update)

    show_dms: BoolProperty(
        description="Show lat/long degrees, minutes, seconds labels",
        default=True)

    show_north: BoolProperty(
        description="Show north offset choice and slider",
        default=True,
        update=sun_update)

    show_refraction: BoolProperty(
        description="Show sun refraction choice",
        default=True,
        update=sun_update)

    show_az_el: BoolProperty(
        description="Show azimuth and solar elevation info",
        default=True)

    show_daylight_savings: BoolProperty(
        description="Show daylight savings time choice",
        default=True,
        update=sun_update)

    show_rise_set: BoolProperty(
        description="Show sunrise and sunset",
        default=True)

    # Uncomment this if you add other map images
    # map_name: StringProperty(
    #     default="WorldMap.jpg",
    #     name="WorldMap",
    #     description="Name of world map")

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column()

        # Uncomment this if you add other map images
        # row = col.row()
        # row.label(text="World map options:")
        # row.operator_menu_enum('world.wmp_operator',
        #                        'map_presets', text=Sun.map_name)
        # col.separator()

        # col.prop(self, "map_location")
        # col.separator()

        col.label(text="Show or use:")
        flow = col.grid_flow(columns=0, even_columns=True, even_rows=False, align=False)
        flow.prop(self, "show_time_place", text="Time/place presets")
        flow.prop(self, "show_object_collection", text="Use collection")
        flow.prop(self, "show_dms", text="D° M' S\"")
        flow.prop(self, "show_north", text="North offset")
        flow.prop(self, "show_refraction", text="Refraction")
        flow.prop(self, "show_az_el", text="Azimuth, elevation")
        flow.prop(self, "show_daylight_savings", text="Daylight savings time")
        flow.prop(self, "show_rise_set", text="Sunrise, sunset")
