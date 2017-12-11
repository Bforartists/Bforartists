# -*- coding: utf-8 -*-
#
# ##### BEGIN GPL LICENSE BLOCK #####
#
# --------------------------------------------------------------------------
# Blender 2.5 Geographical Sun Add-On
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENCE BLOCK #####

# Note: Update to version 0.0.2 remove the dependency on modules\extensions_framework

bl_info = {
    "name": "Geographical Sun",
    "author": "Doug Hammond (dougal2)",
    "version": (0, 0, 2),
    "blender": (2, 7, 0),
    "category": "Lighting",
    "location": "Lamp data > Geographical Sun",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "description": "Set Sun Lamp rotation according to geographical time and location"
}

import bpy
import datetime
from math import (
        asin, sin, cos,
        tan, atan, radians,
        degrees, floor,
        )
import time

today = datetime.datetime.now()

from bpy.types import (
        Operator,
        Menu,
        Panel,
        PropertyGroup,
        )
from bpy.props import (
        BoolProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        )


# Sun rotation calculator implementation
class sun_calculator(object):
    """
    Based on SunLight v1.0 by Miguel Kabantsov (miguelkab@gmail.com)
    Replaces the faulty sun position calculation algorythm with a precise calculation
   (Source for algorythm: http://de.wikipedia.org/wiki/Sonnenstand),
    Co-Ordinates: http://www.bcca.org/misc/qiblih/latlong.html
    Author: Nils-Peter Fischer (Nils-Peter.Fischer@web.de)
    """

    location_list = {
        "EUROPE": [
            ("Antwerp, Belgium", 67),
            ("Berlin, Germany", 1),
            ("Bratislava, Slovak Republic", 70),
            ("Brno, Czech Republic", 72),
            ("Brussles, Belgium", 68),
            ("Geneva, Switzerland", 65),
            ("Helsinki, Finland", 7),
            ("Innsbruck, Austria", 62),
            ("Kyiv, Ukraine", 64),
            ("London, England", 10),
            ("Lyon, France", 66),
            ("Nitra, Slovak Republic", 69),
            ("Oslo, Norway", 58),
            ("Paris, France", 15),
            ("Praha, Czech Republic", 71),
            ("Rome, Italy", 18),
            ("Telfs, Austria", 63),
            ("Warsaw, Poland", 74),
            ("Wroclaw, Poland", 73),
            ("Zurich, Switzerland", 21),
        ],

        "WORLD_CITIES": [
            ("Beijing, China", 0),
            ("Bombay, India", 2),
            ("Buenos Aires, Argentina", 3),
            ("Cairo, Egypt", 4),
            ("Cape Town, South Africa", 5),
            ("Caracas, Venezuela", 6),
            ("Curitiba, Brazil", 60),
            ("Hong Kong, China", 8),
            ("Jerusalem, Israel", 9),
            ("Joinville, Brazil", 61),
            ("Mexico City, Mexico", 11),
            ("Moscow, Russia", 12),
            ("New Delhi, India", 13),
            ("Ottawa, Canada", 14),
            ("Rio de Janeiro, Brazil", 16),
            ("Riyadh, Saudi Arabia", 17),
            ("Sao Paulo, Brazil", 59),
            ("Sydney, Australia", 19),
            ("Tokyo, Japan", 20),
        ],

        "USA_CITIES": [
            ("Albuquerque, NM", 22),
            ("Anchorage, AK", 23),
            ("Atlanta, GA", 24),
            ("Austin, TX", 25),
            ("Birmingham, AL", 26),
            ("Bismarck, ND", 27),
            ("Boston, MA", 28),
            ("Boulder, CO", 29),
            ("Chicago, IL", 30),
            ("Dallas, TX", 31),
            ("Denver, CO", 32),
            ("Detroit, MI", 33),
            ("Honolulu, HI", 34),
            ("Houston, TX", 35),
            ("Indianapolis, IN", 36),
            ("Jackson, MS", 37),
            ("Kansas City, MO", 38),
            ("Los Angeles, CA", 39),
            ("Menomonee Falls, WI", 40),
            ("Miami, FL", 41),
            ("Minneapolis, MN", 42),
            ("New Orleans, LA", 43),
            ("New York City, NY", 44),
            ("Oklahoma City, OK", 45),
            ("Philadelphia, PA", 46),
            ("Phoenix, AZ", 47),
            ("Pittsburgh, PA", 48),
            ("Portland, ME", 49),
            ("Portland, OR", 50),
            ("Raleigh, NC", 51),
            ("Richmond, VA", 52),
            ("Saint Louis, MO", 53),
            ("San Diego, CA", 54),
            ("San Francisco, CA", 55),
            ("Seattle, WA", 56),
            ("Washington DC", 57),
        ]
    }

    location_data = {
        # Europe
        67: (51.2167, 4.4, 1),
        1: (52.33, 13.30, 1),
        70: (48.17, 17.17, 1),
        72: (49.2, 16.63, 1),
        68: (58.8467, 4.3525, 1),
        65: (46.217, 6.150, 1),
        7: (60.1667, 24.9667, 2),
        62: (47.2672, 11.3928, 1),
        64: (50.75, 30.0833, 2),
        10: (51.50, 0.0, 0),
        66: (45.767, 4.833, 1),
        69: (48.32, 18.07, 1),
        58: (59.56, 10.41, 1),
        15: (48.8667, 2.667, 1),
        71: (50.08, 14.46, 1),
        18: (41.90, 12.4833, 1),
        63: (47.3, 11.0667, 1),
        74: (52.232, 21.008, 1),
        73: (51.108, 17.038, 1),
        21: (47.3833, 8.5333, 1),

        # World Cities
        0: (39.9167, 116.4167, 8),
        2: (18.9333, 72.8333, 5.5),
        3: (-34.60, -58.45, -3),
        4: (30.10, 31.3667, 2),
        5: (-33.9167, 18.3667, 2),
        6: (10.50, -66.9333, -4),
        60: (-25.4278, -49.2731, -3),
        8: (22.25, 114.1667, 8),
        9: (31.7833, 35.2333, 2),
        61: (-29.3044, -48.8456, -3),
        11: (19.4, -99.15, -6),
        12: (55.75, 37.5833, 3),
        13: (28.6, 77.2, 5.5),
        14: (45.41667, -75.7, -5),
        16: (-22.90, -43.2333, -3),
        17: (24.633, 46.71667, 3),
        59: (-23.5475, -46.6361, -3),
        19: (-33.8667, 151.2167, 10),
        20: (35.70, 139.7667, 9),

        # US Cities
        22: (35.0833, -106.65, -7),
        23: (61.217, -149.90, -9),
        24: (33.733, -84.383, -5),
        25: (30.283, -97.733, -6),
        26: (33.521, -86.8025, -6),
        27: (46.817, -100.783, -6),
        28: (42.35, -71.05, -5),
        29: (40.125, -105.237, -7),
        30: (41.85, -87.65, -6),
        31: (32.46, -96.47, -6),
        32: (39.733, -104.983, -7),
        33: (42.333, -83.05, -5),
        34: (21.30, -157.85, -10),
        35: (29.75, -95.35, -6),
        36: (39.767, -86.15, -5),
        37: (32.283, -90.183, -6),
        38: (39.083, -94.567, -6),
        39: (34.05, -118.233, -8),
        40: (43.11, -88.10, -6),
        41: (25.767, -80.183, -5),
        42: (44.967, -93.25, -6),
        43: (29.95, -90.067, -6),
        44: (40.7167, -74.0167, -5),
        45: (35.483, -97.533, -6),
        46: (39.95, -75.15, -5),
        47: (33.433, -112.067, -7),
        48: (40.433, -79.9833, -5),
        49: (43.666, -70.283, -5),
        50: (45.517, -122.65, -8),
        51: (35.783, -78.65, -5),
        52: (37.5667, -77.450, -5),
        53: (38.6167, -90.1833, -6),
        54: (32.7667, -117.2167, -8),
        55: (37.7667, -122.4167, -8),
        56: (47.60, -122.3167, -8),
        57: (38.8833, -77.0333, -5),
    }

    # mathematical helpers
    @staticmethod
    def sind(deg):
        return sin(radians(deg))

    @staticmethod
    def cosd(deg):
        return cos(radians(deg))

    @staticmethod
    def tand(deg):
        return tan(radians(deg))

    @staticmethod
    def asind(deg):
        return degrees(asin(deg))

    @staticmethod
    def atand(deg):
        return degrees(atan(deg))

    @staticmethod
    def geo_sun_astronomicJulianDate(Year, Month, Day, LocalTime, Timezone):
        if Month > 2.0:
            Y = Year
            M = Month
        else:
            Y = Year - 1.0
            M = Month + 12.0

        UT = LocalTime - Timezone
        hour = UT / 24.0
        A = int(Y / 100.0)

        JD = floor(365.25 * (Y + 4716.0)) + floor(30.6001 * (M + 1.0)) + Day + hour - 1524.4

        # The following section is adopted from netCDF4 netcdftime implementation.
        # Copyright: 2008 by Jeffrey Whitaker
        # License: http://www.opensource.org/licenses/mit-license.php
        if JD >= 2299170.5:
            # 1582 October 15 (Gregorian Calendar)
            B = 2.0 - A + int(A / 4.0)
        elif JD < 2299160.5:
            # 1582 October 5 (Julian Calendar)
            B = 0
        else:
            raise Exception('ERROR: Date falls in the gap between Julian and Gregorian calendars.')
            B = 0

        return JD + B

    @staticmethod
    def geoSunData(Latitude, Longitude, Year, Month, Day, LocalTime, Timezone):
        JD = sun_calculator.geo_sun_astronomicJulianDate(Year, Month, Day, LocalTime, Timezone)

        phi = Latitude
        llambda = Longitude

        n = JD - 2451545.0
        LDeg = (280.460 + 0.9856474 * n) - (floor((280.460 + 0.9856474 * n) / 360.0) * 360.0)
        gDeg = (357.528 + 0.9856003 * n) - (floor((357.528 + 0.9856003 * n) / 360.0) * 360.0)
        LambdaDeg = LDeg + 1.915 * sun_calculator.sind(gDeg) + 0.02 * sun_calculator.sind(2.0 * gDeg)

        epsilonDeg = 23.439 - 0.0000004 * n

        alphaDeg = sun_calculator.atand(
                (sun_calculator.cosd(epsilonDeg) * sun_calculator.sind(LambdaDeg)) /
                sun_calculator.cosd(LambdaDeg)
                )

        if sun_calculator.cosd(LambdaDeg) < 0.0:
            alphaDeg += 180.0

        deltaDeg = sun_calculator.asind(sun_calculator.sind(epsilonDeg) * sun_calculator.sind(LambdaDeg))

        JDNull = sun_calculator.geo_sun_astronomicJulianDate(Year, Month, Day, 0.0, 0.0)

        TNull = (JDNull - 2451545.0) / 36525.0
        T = LocalTime - Timezone

        thetaGh = 6.697376 + 2400.05134 * TNull + 1.002738 * T
        thetaGh -= floor(thetaGh / 24.0) * 24.0

        thetaG = thetaGh * 15.0
        theta = thetaG + llambda

        tau = theta - alphaDeg

        a = sun_calculator.atand(
                sun_calculator.sind(tau) / (sun_calculator.cosd(tau) * sun_calculator.sind(phi) -
                sun_calculator.tand(deltaDeg) * sun_calculator.cosd(phi))
                )

        if (sun_calculator.cosd(tau) * sun_calculator.sind(phi) -
                sun_calculator.tand(deltaDeg) * sun_calculator.cosd(phi) < 0.0):
            a += 180.0

        h = sun_calculator.asind(
                sun_calculator.cosd(deltaDeg) * sun_calculator.cosd(tau) * sun_calculator.cosd(phi) +
                sun_calculator.sind(deltaDeg) * sun_calculator.sind(phi)
                )

        R = 1.02 / (sun_calculator.tand(h + (10.3 / (h + 5.11))))
        hR = h + R / 60.0

        azimuth = a
        elevation = hR

        return -azimuth, elevation


class OBJECT_OT_set_geographical_sun_now(Operator):
    bl_idname = "object.set_geographical_sun_now"
    bl_label = "Set time to Now"
    bl_description = "Update the time and date settings to the current one"

    @classmethod
    def poll(cls, context):
        cl = context.lamp
        return cl and cl.type == 'SUN'

    def execute(self, context):
        GSP = context.lamp.GeoSunProperties

        now = datetime.datetime.now()
        for p in ("hour", "minute", "day", "month", "year"):
            setattr(
                GSP,
                p,
                getattr(now, p)
            )
        GSP.tz = time.timezone
        GSP.dst = False

        return {'FINISHED'}


class OBJECT_OT_set_geographical_sun_pos(Operator):
    bl_idname = "object.set_geographical_sun_pos"
    bl_label = "Set Sun position"
    bl_description = "Set the Sun lamp rotation according to the given settings"

    @classmethod
    def poll(cls, context):
        cl = context.lamp
        return cl and cl.type == 'SUN'

    def execute(self, context):
        try:
            GSP = context.lamp.GeoSunProperties

            dst = 1 if GSP.dst else 0

            az, el = sun_calculator.geoSunData(
                GSP.lat,
                GSP.longt,
                GSP.year,
                GSP.month,
                GSP.day,
                GSP.hour + GSP.minute / 60.0,
                -GSP.tz + dst
            )

            context.object.rotation_euler = (radians(90 - el), 0, radians(az))
            return {'FINISHED'}

        except Exception as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}


class OBJECT_OT_set_geographical_location_preset(Operator):
    bl_idname = "object.set_geographical_location_preset"
    bl_label = "Apply location preset"
    bl_description = "Update the settings with the data from the chosen city location"

    index = IntProperty()

    @classmethod
    def poll(cls, context):
        cl = context.lamp
        return cl and cl.type == 'SUN'

    def execute(self, context):
        GSP = context.lamp.GeoSunProperties
        GSP.lat, GSP.longt, GSP.tz = sun_calculator.location_data[self.properties.index]
        return {'FINISHED'}


# Dynamic submenu magic !
def draw_locations(self, context, region):
    layout = self.layout
    regions = sun_calculator.location_list[region]

    for location in regions:
        location_name, location_index = location
        layout.operator('OBJECT_OT_set_geographical_location_preset',
                    text=location_name).index = location_index


class OBJECT_MT_geo_sun_location(Menu):
    bl_idname = "OBJECT_MT_geo_sun_location"
    bl_label = "Location preset"
    bl_description = "Choose the specific city location"

    def draw(self, context):
        layout = self.layout

        layout.menu(OBJECT_MT_geo_sun_location_europe_cities.bl_idname)
        layout.menu(OBJECT_MT_geo_sun_location_usa_cities.bl_idname)
        layout.menu(OBJECT_MT_geo_sun_location_world_cities.bl_idname)


class OBJECT_MT_geo_sun_location_europe_cities(Menu):
    bl_idname = "OBJECT_MT_geo_sun_location_europe_cities"
    bl_label = "Europe"

    def draw(self, context):
        draw_locations(self, context, "EUROPE")


class OBJECT_MT_geo_sun_location_usa_cities(Menu):
    bl_idname = "OBJECT_MT_geo_sun_location_usa_cities"
    bl_label = "United States"

    def draw(self, context):
        draw_locations(self, context, "USA_CITIES")


class OBJECT_MT_geo_sun_location_world_cities(Menu):
    bl_idname = "OBJECT_MT_geo_sun_location_world_cities"
    bl_label = "World"

    def draw(self, context):
        draw_locations(self, context, "WORLD_CITIES")


class SUNGEO_GeoSunProperties(PropertyGroup):
    minute = IntProperty(
            name="Minute",
            min=0,
            max=59,
            default=today.minute
            )
    hour = IntProperty(
            name="Hour",
            min=0,
            max=24,
            default=today.hour
            )
    day = IntProperty(
            name="Day",
            min=1,
            max=31,
            default=today.day
            )
    month = IntProperty(
            name="Month",
            min=1,
            max=12,
            default=today.month
            )
    year = IntProperty(
            name="Year",
            min=datetime.MINYEAR,
            max=datetime.MAXYEAR,
            default=today.year
            )
    tz = IntProperty(
            name="Time Zone",
            min=-13,
            max=13,
            default=time.timezone
            )
    dst = BoolProperty(
            name="Daylight saving time",
            default=False
            )
    lat = FloatProperty(
            name="Latitude",
            min=-180.0,
            max=180.0,
            default=0.0
            )
    longt = FloatProperty(
            name="Longitude",
            min=-90.0,
            max=90.0,
            default=0.0
            )


class SUNGEO_PT_lamp_settings(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'
    bl_label = 'Geographical Sun'

    @classmethod
    def poll(cls, context):
        cl = context.lamp
        return cl and cl.type == 'SUN'

    def draw(self, context):
        layout = self.layout

        cl = context.lamp
        if not (cl and cl.type == 'SUN'):
            layout.label("Sun lamp is not active", icon="INFO")
            return

        geosunproperties = cl.GeoSunProperties

        row = layout.row(align=True)
        row.prop(geosunproperties, "hour")
        row.prop(geosunproperties, "minute")

        row = layout.row(align=True)
        row.prop(geosunproperties, "day")
        row.prop(geosunproperties, "month")
        row.prop(geosunproperties, "year")

        row = layout.row(align=True)
        row.prop(geosunproperties, "dst")

        box = layout.box()
        row = box.row(align=True)
        row.menu(OBJECT_MT_geo_sun_location.bl_idname, icon="COLLAPSEMENU")
        row.prop(geosunproperties, "tz")

        row = box.row(align=True)
        row.prop(geosunproperties, "lat")
        row.prop(geosunproperties, "longt")

        row = layout.row(align=True)
        row.operator("object.set_geographical_sun_pos", icon="WORLD_DATA")
        row.operator("object.set_geographical_sun_now", icon="PREVIEW_RANGE")


classes = (
    SUNGEO_GeoSunProperties,
    OBJECT_OT_set_geographical_location_preset,
    OBJECT_OT_set_geographical_sun_now,
    OBJECT_OT_set_geographical_sun_pos,
    OBJECT_MT_geo_sun_location_europe_cities,
    OBJECT_MT_geo_sun_location_usa_cities,
    OBJECT_MT_geo_sun_location_world_cities,
    OBJECT_MT_geo_sun_location,
    SUNGEO_PT_lamp_settings,
    )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.SunLamp.GeoSunProperties = PointerProperty(
                                            type=SUNGEO_GeoSunProperties
                                            )


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.SunLamp.GeoSunProperties
