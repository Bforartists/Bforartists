# SPDX-FileCopyrightText: 2011-2012 Michael Martin
# SPDX-FileCopyrightText: 2019-2025 Damien Picard
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import AddonPreferences, PropertyGroup
from bpy.props import (
    StringProperty,
    EnumProperty,
    IntProperty,
    FloatProperty,
    BoolProperty,
    PointerProperty,
)
from bpy.app.translations import pgettext_rpt as rpt_

from .draw import north_update, analemmas_surface_update
from .geo import parse_position
from .sun_calc import format_lat_long, move_sun, move_sun_env

from math import pi
from datetime import date, timedelta

############################################################################
# Sun panel properties
############################################################################

parse_success = True


def lat_long_update(self, context):
    global parse_success
    parse_success = True
    sun_update(self, context)


def get_day(self):
    """Getter for the day property.

    Not all days are valid, depending on month.
    Invalid days are only at the end of the month so they
    can be checked by just decreasing the value until it is valid.
    """
    day = self.get("day", 1)
    found_date = False
    while not found_date:
        try:
            date(self.year, self.month, day)
            found_date = True
        except ValueError:
            day -= 1
    return day


def set_day(self, value):
    self["day"] = value


def get_day_of_year(self):
    """Getter for the day_of_year property.

    Not all days of year are valid, depending on leap years.
    Only the last day of the year can be invalid.
    """
    day_of_year = self.get("day_of_year", 1)
    dt = date(self.year, 1, 1) + timedelta(day_of_year - 1)
    if dt.year == self.year:
        return day_of_year
    else:
        return 365


def set_day_of_year(self, value):
    self["day_of_year"] = value


def get_coordinates(self):
    if parse_success:
        return format_lat_long(self.latitude, self.longitude)
    return rpt_("Error: could not parse coordinates")


def set_coordinates(self, value):
    parsed_co = parse_position(value)

    global parse_success
    if parsed_co is not None and len(parsed_co) == 2:
        latitude, longitude = parsed_co
        self.latitude, self.longitude = latitude, longitude
    else:
        parse_success = False


def mode_update(self, context):
    """Update both object and environment, but not in the same order depending on target mode.

    The Sun object is shared between the two, so the target mode needs to be updated last.
    """
    if self.usage_mode == 'ENVIRONMENT':
        sun_update(self, context)
        env_update(self, context)
    else:
        env_update(self, context)
        sun_update(self, context)


def sun_update(self, context):
    move_sun(context.scene)

    analemmas_surface_update(context.scene)
    north_update(context.scene)


def env_update(self, context):
    move_sun_env(context.scene)


class SunPosProperties(PropertyGroup):
    usage_mode: EnumProperty(
        name="Usage Mode",
        description="Operate in Normal mode or Environment Texture mode",
        items=(
            ('NORMAL', "Sun Object", "Animate the Sun using time and location on Earth"),
            ('ENVIRONMENT', "Environment", "Synchronize an environment texture and a sun light"),
        ),
        default='NORMAL',
        update=mode_update,
    )
    use_daylight_savings: BoolProperty(
        name="Daylight Savings",
        description=(
            "Daylight savings time adds 1 hour to the standard time. "
            "It is usually used between the spring and fall months"
        ),
        default=False,
        update=sun_update,
    )
    use_refraction: BoolProperty(
        name="Use Refraction",
        description="Show the apparent Sun position due to atmospheric refraction",
        default=True,
        update=sun_update,
    )
    show_north: BoolProperty(
        name="Show North",
        description="Draw a line pointing to the north",
        default=False,
        update=sun_update,
    )
    north_offset: FloatProperty(
        name="North Offset",
        description="Rotate the scene to choose the north direction",
        unit="ROTATION",
        soft_min=-pi,
        soft_max=pi,
        step=10.0,
        default=0.0,
        update=sun_update,
    )
    show_surface: BoolProperty(
        name="Show Surface",
        description="Draw the surface that the Sun occupies in the sky",
        default=False,
        update=sun_update,
    )
    show_analemmas: BoolProperty(
        name="Show Analemmas",
        description=(
            "Draw Sun analemmas. "
            "These help visualize the motion of the Sun in the sky during the year, for each hour of the day"
        ),
        default=False,
        update=sun_update,
    )
    coordinates: StringProperty(
        name="Coordinates",
        description="Latitude and longitude on Earth. Coordinates can be directly entered from an online map",
        get=get_coordinates,
        set=set_coordinates,
        update=sun_update,
        default="00°00′00.00″ 00°00′00.00″",
        options={'SKIP_SAVE'},
    )
    latitude: FloatProperty(
        name="Latitude",
        description="Latitude: (+) Northern (-) Southern",
        soft_min=-90.0,
        soft_max=90.0,
        step=5,
        precision=3,
        default=0.0,
        update=lat_long_update,
    )
    longitude: FloatProperty(
        name="Longitude",
        description="Longitude: (-) West of Greenwich (+) East of Greenwich",
        soft_min=-180.0,
        soft_max=180.0,
        step=5,
        precision=3,
        default=0.0,
        update=lat_long_update,
    )
    sunrise_time: FloatProperty(
        name="Sunrise Time",
        description="Time at which the Sun rises",
        soft_min=0.0,
        soft_max=24.0,
        default=0.0,
        get=lambda self: self.get("sunrise_time", 0.0),
    )
    sunset_time: FloatProperty(
        name="Sunset Time",
        description="Time at which the Sun sets",
        soft_min=0.0,
        soft_max=24.0,
        default=0.0,
        get=lambda self: self.get("sunset_time", 0.0),
    )
    sun_elevation: FloatProperty(
        name="Sun Elevation",
        description="Elevation angle of the Sun",
        soft_min=-pi / 2,
        soft_max=pi / 2,
        precision=3,
        default=0.0,
        unit="ROTATION",
        get=lambda self: self.get("elevation", 0.0),
    )
    sun_azimuth: FloatProperty(
        name="Sun Azimuth",
        description="Rotation angle of the Sun from the direction of the north",
        soft_min=-pi,
        soft_max=pi,
        precision=3,
        default=0.0,
        unit="ROTATION",
        get=lambda self: self.get("azimuth", 0.0) - self.north_offset,
    )
    month: IntProperty(
        name="Month",
        min=1,
        max=12,
        default=1,
        update=sun_update,
    )
    day: IntProperty(
        name="Day",
        min=1,
        max=31,
        default=1,
        get=get_day,
        set=set_day,
        update=sun_update,
    )
    year: IntProperty(
        name="Year",
        min=1,
        max=4000,
        default=2000,
        update=sun_update,
    )
    use_day_of_year: BoolProperty(
        description="Use a single value for the day of year",
        name="Use Day of Year",
        default=False,
        update=sun_update,
    )
    day_of_year: IntProperty(
        name="Day of Year",
        min=1,
        max=366,
        default=1,
        get=get_day_of_year,
        set=set_day_of_year,
        update=sun_update,
    )
    UTC_zone: FloatProperty(
        name="UTC Zone",
        description="Time difference between Coordinated Universal Time and local time",
        precision=1,
        soft_min=-12.0,
        soft_max=14.0,
        step=50,
        default=0.0,
        update=sun_update,
    )
    time: FloatProperty(
        name="Time",
        description="Time of the day",
        translation_context="Hour",
        precision=4,
        soft_min=0.0,
        soft_max=24.0,
        step=1.0,
        default=12.0,
        update=sun_update,
    )
    sun_distance: FloatProperty(
        name="Distance",
        description="Distance to the sun object from the origin",
        unit="LENGTH",
        min=0.0,
        soft_max=3000.0,
        step=10.0,
        default=50.0,
        update=sun_update,
    )
    sun_object: PointerProperty(
        name="Sun Object",
        type=bpy.types.Object,
        description="Sun object to use in the scene",
        poll=lambda self, obj: obj.type == 'LIGHT',
        update=mode_update,
    )
    object_collection: PointerProperty(
        name="Collection",
        type=bpy.types.Collection,
        description="Collection of objects used to visualize the motion of the Sun",
        update=sun_update,
    )
    object_collection_type: EnumProperty(
        name="Display Type",
        description="Type of Sun motion to visualize",
        items=(
            (
                'ANALEMMA',
                "Analemma",
                "Trajectory of the Sun in the sky during the year, for a given time of the day",
            ),
            ('DIURNAL', "Diurnal", "Trajectory of the Sun in the sky during a single day"),
        ),
        default='ANALEMMA',
        update=sun_update,
    )
    time_spread: FloatProperty(
        name="Time Spread",
        description="Time period around which to spread object collection",
        precision=4,
        soft_min=1.0,
        soft_max=24.0,
        step=1.0,
        default=23.0,
        update=sun_update,
    )
    sky_texture: StringProperty(
        name="Sky Texture",
        default="",
        description="Name of the sky texture to use",
        update=sun_update,
    )
    env_texture: StringProperty(
        default="Environment Texture",
        name="Environment Texture",
        description=(
            "Name of the environment texture to use. World nodes must be enabled "
            "and the color set to an environment texture"
        ),
        update=env_update,
    )
    env_azimuth: FloatProperty(
        name="Rotation",
        description="Rotation angle of the Sun and environment texture",
        unit="ROTATION",
        step=10.0,
        default=0.0,
        precision=3,
        update=env_update,
    )
    env_elevation: FloatProperty(
        name="Elevation",
        description="Elevation angle of the Sun",
        unit="ROTATION",
        step=10.0,
        default=0.0,
        precision=3,
        update=env_update,
    )
    env_distance: FloatProperty(
        name="Distance",
        description="Distance to the sun object from the origin",
        unit="LENGTH",
        min=0.0,
        soft_max=3000.0,
        step=10.0,
        default=50.0,
        update=env_update,
    )
    bind_to_sun: BoolProperty(
        name="Bind Texture to Sun",
        description="If enabled, the environment texture moves with the Sun",
        default=False,
        update=env_update,
    )


############################################################################
# Preference panel properties
############################################################################


class SunPosAddonPreferences(AddonPreferences):
    bl_idname = __package__

    show_overlays: BoolProperty(
        name="Show Overlays",
        description="Display overlays in the viewport: the direction of the north, analemmas and the Sun surface",
        default=True,
        update=sun_update,
    )
    show_refraction: BoolProperty(
        name="Refraction",
        description="Show Sun Refraction choice",
        default=True,
    )
    show_az_el: BoolProperty(
        name="Azimuth and Elevation Info",
        description="Show azimuth and solar elevation info",
        default=True,
    )
    show_rise_set: BoolProperty(
        name="Sunrise and Sunset Info",
        description="Show sunrise and sunset labels",
        default=True,
    )

    def draw(self, context):
        layout = self.layout

        col = layout.column()

        col.label(text="Show options and info")
        flow = col.grid_flow(columns=0, even_columns=True, even_rows=False, align=False)
        flow.prop(self, "show_refraction")
        flow.prop(self, "show_overlays")
        flow.prop(self, "show_az_el")
        flow.prop(self, "show_rise_set")
