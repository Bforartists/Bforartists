# -*- coding: utf-8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
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
# ***** END GPL LICENCE BLOCK *****
#

# System imports
#-----------------------------------------------------------------------------
import datetime, math, time
today = datetime.datetime.now()

# Blender imports
#----------------------------------------------------------------------------- 
import bpy
from extensions_framework import Addon, declarative_property_group
from extensions_framework.ui import property_group_renderer

# Addon setup
#----------------------------------------------------------------------------- 
bl_info = {
    "name": "Geographical Sun",
    "author": "Doug Hammond (dougal2)",
    "version": (0, 0, 1),
    "blender": (2, 56, 0),
    "category": "Object",
    "location": "Lamp data > Geographical Sun",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "description": "Set SUN Lamp rotation according to geographical time and location."
}
GeoSunAddon = Addon(bl_info)

# Sun rotation calculator implementation
#----------------------------------------------------------------------------- 
class sun_calculator(object):
    """
    Based on SunLight v1.0 by Miguel Kabantsov (miguelkab@gmail.com)
    Replaces the faulty sun position calculation algorythm with a precise calculation (Source for algorythm: http://de.wikipedia.org/wiki/Sonnenstand),
    Co-Ordinates: http://www.bcca.org/misc/qiblih/latlong.html
    Author: Nils-Peter Fischer (Nils-Peter.Fischer@web.de)
    """
    
    location_list = [
        ("EUROPE",[
            ("Antwerp, Belgium",            67),
            ("Berlin, Germany",             1),
            ("Bratislava, Slovak Republic", 70),
            ("Brno, Czech Republic",        72),
            ("Brussles, Belgium",           68),
            ("Geneva, Switzerland",         65),
            ("Helsinki, Finland",           7),
            ("Innsbruck, Austria",          62),
            ("Kyiv, Ukraine",               64),
            ("London, England",             10),
            ("Lyon, France",                66),
            ("Nitra, Slovak Republic",      69),
            ("Oslo, Norway",                58),
            ("Paris, France",               15),
            ("Praha, Czech Republic",       71),
            ("Rome, Italy",                 18),
            ("Telfs, Austria",              63),
            ("Warsaw, Poland",              74),
            ("Wroclaw, Poland",             73),
            ("Zurich, Switzerland",         21),
        ]),
        
        ("WORLD CITIES", [
            ("Beijing, China",              0),
            ("Bombay, India",               2),
            ("Buenos Aires, Argentina",     3),
            ("Cairo, Egypt",                4),
            ("Cape Town, South Africa",     5),
            ("Caracas, Venezuela",          6),
            ("Curitiba, Brazil",            60),
            ("Hong Kong, China",            8),
            ("Jerusalem, Israel",           9),
            ("Joinville, Brazil",           61),
            ("Mexico City, Mexico",         11),
            ("Moscow, Russia",              12),
            ("New Delhi, India",            13),
            ("Ottawa, Canada",              14),
            ("Rio de Janeiro, Brazil",      16),
            ("Riyadh, Saudi Arabia",        17),
            ("Sao Paulo, Brazil",           59),
            ("Sydney, Australia",           19),
            ("Tokyo, Japan",                20),
        ]),
        
        ("US CITIES", [
            ("Albuquerque, NM",             22),
            ("Anchorage, AK",               23),
            ("Atlanta, GA",                 24),
            ("Austin, TX",                  25),
            ("Birmingham, AL",              26),
            ("Bismarck, ND",                27),
            ("Boston, MA",                  28),
            ("Boulder, CO",                 29),
            ("Chicago, IL",                 30),
            ("Dallas, TX",                  31),
            ("Denver, CO",                  32),
            ("Detroit, MI",                 33),
            ("Honolulu, HI",                34),
            ("Houston, TX",                 35),
            ("Indianapolis, IN",            36),
            ("Jackson, MS",                 37),
            ("Kansas City, MO",             38),
            ("Los Angeles, CA",             39),
            ("Menomonee Falls, WI",         40),
            ("Miami, FL",                   41),
            ("Minneapolis, MN",             42),
            ("New Orleans, LA",             43),
            ("New York City, NY",           44),
            ("Oklahoma City, OK",           45),
            ("Philadelphia, PA",            46),
            ("Phoenix, AZ",                 47),
            ("Pittsburgh, PA",              48),
            ("Portland, ME",                49),
            ("Portland, OR",                50),
            ("Raleigh, NC",                 51),
            ("Richmond, VA",                52),
            ("Saint Louis, MO",             53),
            ("San Diego, CA",               54),
            ("San Francisco, CA",           55),
            ("Seattle, WA",                 56),
            ("Washington DC",               57),
        ])
    ]
    
    location_data = {
        # Europe
        67: ( 51.2167, -4.4, 1),
        1:  ( 52.33, -13.30, 1),
        70: ( 48.17, -17.17, 1),
        72: ( 49.2, -16.63, 1),
        68: ( 58.8467, -4.3525, 1),
        65: ( 46.217, -6.150, 1),
        7:  ( 60.1667, -24.9667,2),
        62: ( 47.2672, -11.3928, 1),
        64: ( 50.75, -30.0833, 2),
        10: ( 51.50, 0.0, 0),
        66: ( 45.767, -4.833, 1),
        69: ( 48.32, -18.07, 1),
        58: ( 59.56, -10.41, 1),
        15: ( 48.8667, -2.667, 1),
        71: ( 50.08, -14.46, 1),
        18: ( 41.90, -12.4833, 1),
        63: ( 47.3, -11.0667, 1),
        74: ( 52.232, -21.008, 1),
        73: ( 51.108, -17.038, 1),
        21: ( 47.3833, -8.5333, 1),
        
        # World Cities
        0:  ( 39.9167, -116.4167, 8),
        2:  ( 18.9333, -72.8333, 5.5),
        3:  (-34.60, 58.45, -3),
        4:  ( 30.10, -31.3667, 2),
        5:  (-33.9167, -18.3667, 2),
        6:  ( 10.50, 66.9333, -4),
        60: (-25.4278, 49.2731, -3),
        8:  ( 22.25, -114.1667, 8),
        9:  ( 31.7833, -35.2333, 2),
        61: (-29.3044, 48.8456, -3),
        11: ( 19.4, 99.15, -6),
        12: ( 55.75, -37.5833, 3),
        13: ( 28.6, -77.2, 5.5),
        14: ( 45.41667, 75.7, -5),
        16: (-22.90, 43.2333, -3),
        17: ( 24.633, -46.71667, 3),
        59: ( -23.5475, 46.6361, -3),
        19: (-33.8667, -151.2167,10),
        20: ( 35.70, -139.7667, 9), 
        
        # US Cities
        22: ( 35.0833, 106.65, -7),
        23: ( 61.217, 149.90, -9),
        24: ( 33.733, 84.383, -5),
        25: ( 30.283, 97.733, -6),
        26: ( 33.521, 86.8025, -6),
        27: ( 46.817, 100.783, -6),
        28: ( 42.35, 71.05, -5),
        29: ( 40.125, 105.237, -7),
        30: ( 41.85, 87.65, -6),
        31: ( 32.46, 96.47, -6),
        32: ( 39.733, 104.983, -7),
        33: ( 42.333, 83.05, -5),
        34: ( 21.30, 157.85, -10),
        35: ( 29.75, 95.35, -6),
        36: ( 39.767, 86.15, -5),
        37: ( 32.283, 90.183, -6),
        38: ( 39.083, 94.567, -6),
        39: ( 34.05, 118.233, -8),
        40: ( 43.11, 88.10, -6),
        41: ( 25.767, 80.183, -5),
        42: ( 44.967, 93.25, -6),
        43: ( 29.95, 90.067, -6),
        44: ( 40.7167, 74.0167, -5),
        45: ( 35.483, 97.533, -6),
        46: ( 39.95, 75.15, -5),
        47: ( 33.433, 112.067,-7),
        48: ( 40.433, 79.9833, -5),
        49: ( 43.666, 70.283, -5),
        50: ( 45.517, 122.65, -8),
        51: ( 35.783, 78.65, -5),
        52: ( 37.5667, 77.450, -5),
        53: ( 38.6167, 90.1833, -6),
        54: ( 32.7667, 117.2167, -8),
        55: ( 37.7667, 122.4167, -8),
        56: ( 47.60, 122.3167, -8),
        57: ( 38.8833, 77.0333, -5),
    }
    
    # mathematical helpers
    @staticmethod
    def sind(deg):
        return math.sin(math.radians(deg))
    
    @staticmethod
    def cosd(deg):
        return math.cos(math.radians(deg))
    
    @staticmethod
    def tand(deg):
        return math.tan(math.radians(deg))
    
    @staticmethod
    def asind(deg):
        return math.degrees(math.asin(deg))
    
    @staticmethod
    def atand(deg):
        return math.degrees(math.atan(deg))
    
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
        A = int(Y/100.0)
        
        JD = math.floor(365.25*(Y+4716.0)) + math.floor(30.6001*(M+1.0)) + Day + hour - 1524.4
        
        # The following section is adopted from netCDF4 netcdftime implementation.
        # Copyright: 2008 by Jeffrey Whitaker
        # License: http://www.opensource.org/licenses/mit-license.php
        if JD >= 2299170.5:
            # 1582 October 15 (Gregorian Calendar)
            B = 2.0 - A + int(A/4.0)
        elif JD < 2299160.5:
            # 1582 October 5 (Julian Calendar)
            B = 0
        else:
            raise Exception('ERROR: Date falls in the gap between Julian and Gregorian calendars.')
            B = 0
        
        return JD+B
    
    @staticmethod
    def geoSunData(Latitude, Longitude, Year, Month, Day, LocalTime, Timezone):
        JD = sun_calculator.geo_sun_astronomicJulianDate(Year, Month, Day, LocalTime, Timezone)
        
        phi = Latitude
        llambda = Longitude
                
        n = JD - 2451545.0
        LDeg = (280.460 + 0.9856474*n) - (math.floor((280.460 + 0.9856474*n)/360.0) * 360.0)
        gDeg = (357.528 + 0.9856003*n) - (math.floor((357.528 + 0.9856003*n)/360.0) * 360.0)
        LambdaDeg = LDeg + 1.915 * sun_calculator.sind(gDeg) + 0.02 * sun_calculator.sind(2.0*gDeg)
        
        epsilonDeg = 23.439 - 0.0000004*n
        
        alphaDeg = sun_calculator.atand( (sun_calculator.cosd(epsilonDeg) * sun_calculator.sind(LambdaDeg)) / sun_calculator.cosd(LambdaDeg) )
        if sun_calculator.cosd(LambdaDeg) < 0.0:
            alphaDeg += 180.0
            
        deltaDeg = sun_calculator.asind( sun_calculator.sind(epsilonDeg) * sun_calculator.sind(LambdaDeg) )
        
        JDNull = sun_calculator.geo_sun_astronomicJulianDate(Year, Month, Day, 0.0, 0.0)
        
        TNull = (JDNull - 2451545.0) / 36525.0
        T = LocalTime - Timezone
        
        thetaGh = 6.697376 + 2400.05134*TNull + 1.002738*T
        thetaGh -= math.floor(thetaGh/24.0) * 24.0
        
        thetaG = thetaGh * 15.0
        theta = thetaG + llambda
        
        tau = theta - alphaDeg
        
        a = sun_calculator.atand( sun_calculator.sind(tau) / ( sun_calculator.cosd(tau)*sun_calculator.sind(phi) - sun_calculator.tand(deltaDeg)*sun_calculator.cosd(phi)) )
        if sun_calculator.cosd(tau)*sun_calculator.sind(phi) - sun_calculator.tand(deltaDeg)*sun_calculator.cosd(phi) < 0.0:
            a += 180.0
        
        h = sun_calculator.asind( sun_calculator.cosd(deltaDeg)*sun_calculator.cosd(tau)*sun_calculator.cosd(phi) + sun_calculator.sind(deltaDeg)*sun_calculator.sind(phi) )
        
        R = 1.02 / (sun_calculator.tand (h+(10.3/(h+5.11))))
        hR = h + R/60.0
        
        azimuth = a
        elevation = hR
        
        return azimuth, elevation

# Addon classes
#----------------------------------------------------------------------------- 
@GeoSunAddon.addon_register_class
class OBJECT_OT_set_geographical_sun_now(bpy.types.Operator):
    bl_idname = 'object.set_geographical_sun_now'
    bl_label = 'Set time to NOW'
    
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

@GeoSunAddon.addon_register_class
class OBJECT_OT_set_geographical_sun_pos(bpy.types.Operator):
    bl_idname = 'object.set_geographical_sun_pos'
    bl_label = 'Set SUN position'
    
    @classmethod
    def poll(cls, context):
        cl = context.lamp
        return cl and cl.type == 'SUN'
    
    def execute(self, context):
        try:
            GSP = context.lamp.GeoSunProperties
            
            dst = 1 if GSP.dst else 0
            
            az,el = sun_calculator.geoSunData(
                GSP.lat,
                GSP.long,
                GSP.year,
                GSP.month,
                GSP.day,
                GSP.hour + GSP.minute/60.0,
                -GSP.tz + dst
            )
            
            context.object.rotation_euler = ( math.radians(90-el), 0, math.radians(-az) )
            return {'FINISHED'}
        except Exception as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}

@GeoSunAddon.addon_register_class
class OBJECT_OT_set_geographical_location_preset(bpy.types.Operator):
    bl_idname = 'object.set_geographical_location_preset'
    bl_label = 'Apply location preset'
    
    index = bpy.props.IntProperty()
    
    @classmethod
    def poll(cls, context):
        cl = context.lamp
        return cl and cl.type == 'SUN'
    
    def execute(self, context):
        GSP = context.lamp.GeoSunProperties
        GSP.lat, GSP.long, GSP.tz = sun_calculator.location_data[self.properties.index]
        return {'FINISHED'}

# Dynamic submenu magic !

def draw_generator(locations):
    def draw(self, context):
        sl = self.layout
        for location in locations:
            location_name, location_index = location
            sl.operator('OBJECT_OT_set_geographical_location_preset', text=location_name).index = location_index
    return draw

submenus = []
for label, locations in sun_calculator.location_list:
    submenu_idname = 'OBJECT_MT_geo_sun_location_cat%d'%len(submenus)
    submenu = type(
        submenu_idname,
        (bpy.types.Menu,),
        {
            'bl_idname': submenu_idname,
            'bl_label': label,
            'draw': draw_generator(locations)
        }
    )
    GeoSunAddon.addon_register_class(submenu)
    submenus.append(submenu)

@GeoSunAddon.addon_register_class
class OBJECT_MT_geo_sun_location(bpy.types.Menu):
    bl_label = 'Location preset'
    
    def draw(self, context):
        sl = self.layout
        for sm in submenus:
            sl.menu(sm.bl_idname)

@GeoSunAddon.addon_register_class
class GeoSunProperties(declarative_property_group):
    ef_attach_to = ['Lamp']
    
    controls = [
        ['hour', 'minute'],
        ['day', 'month', 'year'],
        ['tz', 'dst'],
        'location_menu',
        ['lat', 'long'],
        ['set_time', 'set_posn'],
    ]
    
    properties = [
        {
            'type': 'int',
            'attr': 'minute',
            'name': 'Minute',
            'min': 0,
            'soft_min': 0,
            'max': 59,
            'soft_max': 59,
            'default': today.minute
        },
        {
            'type': 'int',
            'attr': 'hour',
            'name': 'Hour',
            'min': 0,
            'soft_min': 0,
            'max': 24,
            'soft_max': 24,
            'default': today.hour
        },
        {
            'type': 'int',
            'attr': 'day',
            'name': 'Day',
            'min': 1,
            'soft_min': 1,
            'max': 31,
            'soft_max': 31,
            'default': today.day
        },
        {
            'type': 'int',
            'attr': 'month',
            'name': 'Month',
            'min': 1,
            'soft_min': 1,
            'max': 12,
            'soft_max': 12,
            'default': today.month
        },
        {
            'type': 'int',
            'attr': 'year',
            'name': 'Year',
            'min': datetime.MINYEAR,
            'soft_min': datetime.MINYEAR,
            'max': datetime.MAXYEAR,
            'soft_max': datetime.MAXYEAR,
            'default': today.year
        },
        {
            'type': 'int',
            'attr': 'tz',
            'name': 'Time zone',
            'min': -13,
            'soft_min': -13,
            'max': 13,
            'soft_max': 13,
            'default': time.timezone
        },
        {
            'type': 'bool',
            'attr': 'dst',
            'name': 'DST',
            'default': False
        },
        {
            'type': 'float',
            'attr': 'lat',
            'name': 'Lat.',
            'min': -180.0,
            'soft_min': -180.0,
            'max': 180.0,
            'soft_max': 180.0,
            'default': 0.0
        },
        {
            'type': 'float',
            'attr': 'long',
            'name': 'Long.',
            'min': -90.0,
            'soft_min': -90.0,
            'max': 90.0,
            'soft_max': 90.0,
            'default': 0.0
        },
        
        # draw operators and menus
        {
            'attr': 'location_menu',
            'type': 'menu',
            'menu': 'OBJECT_MT_geo_sun_location'
        },
        {
            'attr': 'set_time',
            'type': 'operator',
            'operator': 'object.set_geographical_sun_now',
            'icon': 'PREVIEW_RANGE'
        },
        {
            'attr': 'set_posn',
            'type': 'operator',
            'operator': 'object.set_geographical_sun_pos',
            'icon': 'WORLD_DATA'
        },
    ]

@GeoSunAddon.addon_register_class
class GeoSunPanel(property_group_renderer):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'
    bl_label = 'Geographical Sun'
    
    display_property_groups = [
        ( ('lamp',), 'GeoSunProperties' )
    ]
    
    @classmethod
    def poll(cls, context):
        cl = context.lamp
        return cl and cl.type == 'SUN'

# Bootstrap the Addon
#----------------------------------------------------------------------------- 
register, unregister = GeoSunAddon.init_functions()
