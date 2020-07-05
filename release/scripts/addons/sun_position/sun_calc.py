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
from bpy.app.handlers import persistent
from mathutils import Euler
import math
from math import degrees, radians, pi
import datetime
from .geo import parse_position


############################################################################
#
# SunClass is used for storing intermediate sun calculations.
#
############################################################################

class SunClass:

    class TazEl:
        time = 0.0
        azimuth = 0.0
        elevation = 0.0

    class CLAMP:
        elevation = 0.0
        azimuth = 0.0
        az_start_sun = 0.0
        az_start_env = 0.0

    sunrise = TazEl()
    sunset = TazEl()
    solar_noon = TazEl()
    rise_set_ok = False

    bind = CLAMP()
    bind_to_sun = False

    latitude = 0.0
    longitude = 0.0
    elevation = 0.0
    azimuth = 0.0

    month = 0
    day = 0
    year = 0
    day_of_year = 0
    time = 0.0

    UTC_zone = 0
    sun_distance = 0.0
    use_daylight_savings = False


sun = SunClass()


def sun_update(self, context):
    update_time(context)
    move_sun(context)

def parse_coordinates(self, context):
    error_message = "ERROR: Could not parse coordinates"
    sun_props = context.scene.sun_pos_properties

    if sun_props.co_parser:
        parsed_co = parse_position(sun_props.co_parser)

        if parsed_co is not None and len(parsed_co) == 2:
            sun_props.latitude, sun_props.longitude = parsed_co
        elif sun_props.co_parser != error_message:
            sun_props.co_parser = error_message

        # Clear prop
    if sun_props.co_parser not in {'', error_message}:
        sun_props.co_parser = ''

@persistent
def sun_handler(scene):
    update_time(bpy.context)
    move_sun(bpy.context)


############################################################################
#
# move_sun() will cycle through all the selected objects
# and call set_sun_position and set_sun_rotations
# to place them in the sky.
#
############################################################################


def move_sun(context):
    addon_prefs = context.preferences.addons[__package__].preferences
    sun_props = context.scene.sun_pos_properties

    if sun_props.usage_mode == "HDR":
        nt = context.scene.world.node_tree.nodes
        env_tex = nt.get(sun_props.hdr_texture)

        if sun.bind_to_sun != sun_props.bind_to_sun:
            # bind_to_sun was just toggled
            sun.bind_to_sun = sun_props.bind_to_sun
            sun.bind.az_start_sun = sun_props.hdr_azimuth
            if env_tex:
                sun.bind.az_start_env = env_tex.texture_mapping.rotation.z

        if env_tex and sun_props.bind_to_sun:
            az = sun_props.hdr_azimuth - sun.bind.az_start_sun + sun.bind.az_start_env
            env_tex.texture_mapping.rotation.z = az

        if sun_props.sun_object:
            sun.theta = math.pi / 2 - sun_props.hdr_elevation
            sun.phi = -sun_props.hdr_azimuth

            obj = sun_props.sun_object
            set_sun_position(obj, sun_props.sun_distance)
            rotation_euler = Euler((sun_props.hdr_elevation - pi/2,
                                    0, -sun_props.hdr_azimuth))

            set_sun_rotations(obj, rotation_euler)
        return

    local_time = sun_props.time
    zone = -sun_props.UTC_zone
    sun.use_daylight_savings = sun_props.use_daylight_savings
    if sun.use_daylight_savings:
        zone -= 1

    north_offset = degrees(sun_props.north_offset)

    if addon_prefs.show_rise_set:
        calc_sunrise_sunset(rise=True)
        calc_sunrise_sunset(rise=False)

    get_sun_position(local_time, sun_props.latitude, sun_props.longitude,
            north_offset, zone, sun_props.month, sun_props.day, sun_props.year,
            sun_props.sun_distance)

    if sun_props.sky_texture:
        sky_node = bpy.context.scene.world.node_tree.nodes.get(sun_props.sky_texture)
        if sky_node is not None and sky_node.type == "TEX_SKY":
            locX = math.sin(sun.phi) * math.sin(-sun.theta)
            locY = math.sin(sun.theta) * math.cos(sun.phi)
            locZ = math.cos(sun.theta)
            sky_node.texture_mapping.rotation.z = 0.0
            sky_node.sun_direction = locX, locY, locZ
            sky_node.sun_elevation = math.radians(sun.elevation)
            sky_node.sun_rotation = math.radians(sun.az_north)

    # Sun object
    if (sun_props.sun_object is not None
            and sun_props.sun_object.name in context.view_layer.objects):
        obj = sun_props.sun_object
        set_sun_position(obj, sun_props.sun_distance)
        rotation_euler = Euler((math.radians(sun.elevation - 90), 0,
                                math.radians(-sun.az_north)))
        set_sun_rotations(obj, rotation_euler)

    # Sun collection
    if sun_props.object_collection is not None:
        sun_objects = sun_props.object_collection.objects
        object_count = len(sun_objects)
        if sun_props.object_collection_type == 'DIURNAL':
            # Diurnal motion
            if object_count > 1:
                time_increment = sun_props.time_spread / (object_count - 1)
                local_time = local_time + time_increment * (object_count - 1)
            else:
                time_increment = sun_props.time_spread

            for obj in sun_objects:
                get_sun_position(local_time, sun_props.latitude,
                                 sun_props.longitude, north_offset, zone,
                                 sun_props.month, sun_props.day,
                                 sun_props.year, sun_props.sun_distance)
                set_sun_position(obj, sun_props.sun_distance)
                local_time -= time_increment
                obj.rotation_euler = (
                    (math.radians(sun.elevation - 90), 0,
                     math.radians(-sun.az_north)))
        else:
            # Analemma
            day_increment = 365 / object_count
            day = sun_props.day_of_year + day_increment * (object_count - 1)
            for obj in sun_objects:
                dt = (datetime.date(sun_props.year, 1, 1) +
                      datetime.timedelta(day - 1))
                get_sun_position(local_time, sun_props.latitude,
                                 sun_props.longitude, north_offset, zone,
                                 dt.month, dt.day, sun_props.year,
                                 sun_props.sun_distance)
                set_sun_position(obj, sun_props.sun_distance)
                day -= day_increment
                obj.rotation_euler = (
                    (math.radians(sun.elevation - 90), 0,
                     math.radians(-sun.az_north)))

def update_time(context):
    sun_props = context.scene.sun_pos_properties

    if sun_props.use_day_of_year:
        dt = (datetime.date(sun_props.year, 1, 1) +
              datetime.timedelta(sun_props.day_of_year - 1))
        sun.day = dt.day
        sun.month = dt.month
        sun.day_of_year = sun_props.day_of_year
        if sun_props.day != dt.day:
            sun_props.day = dt.day
        if sun_props.month != dt.month:
            sun_props.month = dt.month
    else:
        dt = datetime.date(sun_props.year, sun_props.month, sun_props.day)
        day_of_year = dt.timetuple().tm_yday
        if sun_props.day_of_year != day_of_year:
            sun_props.day_of_year = day_of_year
        sun.day = sun_props.day
        sun.month = sun_props.month
        sun.day_of_year = day_of_year
    sun.year = sun_props.year
    sun.longitude = sun_props.longitude
    sun.latitude = sun_props.latitude
    sun.UTC_zone = sun_props.UTC_zone


def format_time(the_time, daylight_savings, longitude, UTC_zone=None):
    if UTC_zone is not None:
        if daylight_savings:
            UTC_zone += 1
        the_time -= UTC_zone

    the_time %= 24

    hh = int(the_time)
    mm = (the_time - int(the_time)) * 60
    ss = int((mm - int(mm)) * 60)

    return ("%02i:%02i:%02i" % (hh, mm, ss))


def format_hms(the_time):
    hh = str(int(the_time))
    min = (the_time - int(the_time)) * 60
    sec = int((min - int(min)) * 60)
    mm = "0" + str(int(min)) if min < 10 else str(int(min))
    ss = "0" + str(sec) if sec < 10 else str(sec)

    return (hh + ":" + mm + ":" + ss)


def format_lat_long(lat_long, is_latitude):
    hh = str(abs(int(lat_long)))
    min = abs((lat_long - int(lat_long)) * 60)
    sec = abs(int((min - int(min)) * 60))
    mm = "0" + str(int(min)) if min < 10 else str(int(min))
    ss = "0" + str(sec) if sec < 10 else str(sec)
    if lat_long == 0:
        coord_tag = " "
    else:
        if is_latitude:
            coord_tag = " N" if lat_long > 0 else " S"
        else:
            coord_tag = " E" if lat_long > 0 else " W"

    return hh + "° " + mm + "' " + ss + '"' + coord_tag




############################################################################
#
# Calculate the actual position of the sun based on input parameters.
#
# The sun positioning algorithms below are based on the National Oceanic
# and Atmospheric Administration's (NOAA) Solar Position Calculator
# which rely on calculations of Jean Meeus' book "Astronomical Algorithms."
# Use of NOAA data and products are in the public domain and may be used
# freely by the public as outlined in their policies at
#               www.nws.noaa.gov/disclaimer.php
#
# The calculations of this script can be verified with those of NOAA's
# using the Azimuth and Solar Elevation displayed in the SunPos_Panel.
# NOAA's web site is:
#               http://www.esrl.noaa.gov/gmd/grad/solcalc
############################################################################


def get_sun_position(local_time, latitude, longitude, north_offset,
                   utc_zone, month, day, year, distance):

    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    sun_props = bpy.context.scene.sun_pos_properties

    longitude *= -1                 # for internal calculations
    utc_time = local_time + utc_zone   # Set Greenwich Meridian Time

    if latitude > 89.93:            # Latitude 90 and -90 gives
        latitude = radians(89.93)  # erroneous results so nudge it
    elif latitude < -89.93:
        latitude = radians(-89.93)
    else:
        latitude = radians(latitude)

    t = julian_time_from_y2k(utc_time, year, month, day)

    e = radians(obliquity_correction(t))
    L = apparent_longitude_of_sun(t)
    solar_dec = sun_declination(e, L)
    eqtime = calc_equation_of_time(t)

    time_correction = (eqtime - 4 * longitude) + 60 * utc_zone
    true_solar_time = ((utc_time - utc_zone) * 60.0 + time_correction) % 1440

    hour_angle = true_solar_time / 4.0 - 180.0
    if hour_angle < -180.0:
        hour_angle += 360.0

    csz = (math.sin(latitude) * math.sin(solar_dec) +
           math.cos(latitude) * math.cos(solar_dec) *
           math.cos(radians(hour_angle)))
    if csz > 1.0:
        csz = 1.0
    elif csz < -1.0:
        csz = -1.0

    zenith = math.acos(csz)

    az_denom = math.cos(latitude) * math.sin(zenith)

    if abs(az_denom) > 0.001:
        az_rad = ((math.sin(latitude) *
                  math.cos(zenith)) - math.sin(solar_dec)) / az_denom
        if abs(az_rad) > 1.0:
            az_rad = -1.0 if (az_rad < 0.0) else 1.0
        azimuth = 180.0 - degrees(math.acos(az_rad))
        if hour_angle > 0.0:
            azimuth = -azimuth
    else:
        azimuth = 180.0 if (latitude > 0.0) else 0.0

    if azimuth < 0.0:
        azimuth = azimuth + 360.0

    exoatm_elevation = 90.0 - degrees(zenith)

    if sun_props.use_refraction:
        if exoatm_elevation > 85.0:
            refraction_correction = 0.0
        else:
            te = math.tan(radians(exoatm_elevation))
            if exoatm_elevation > 5.0:
                refraction_correction = (
                    58.1 / te - 0.07 / (te ** 3) + 0.000086 / (te ** 5))
            elif (exoatm_elevation > -0.575):
                s1 = (-12.79 + exoatm_elevation * 0.711)
                s2 = (103.4 + exoatm_elevation * (s1))
                s3 = (-518.2 + exoatm_elevation * (s2))
                refraction_correction = 1735.0 + exoatm_elevation * (s3)
            else:
                refraction_correction = -20.774 / te

        refraction_correction = refraction_correction / 3600
        solar_elevation = 90.0 - (degrees(zenith) - refraction_correction)

    else:
        solar_elevation = 90.0 - degrees(zenith)

    solar_azimuth = azimuth
    solar_azimuth += north_offset

    sun.az_north = solar_azimuth

    sun.theta = math.pi / 2 - radians(solar_elevation)
    sun.phi = radians(solar_azimuth) * -1
    sun.azimuth = azimuth
    sun.elevation = solar_elevation


def set_sun_position(obj, distance):
    locX = math.sin(sun.phi) * math.sin(-sun.theta) * distance
    locY = math.sin(sun.theta) * math.cos(sun.phi) * distance
    locZ = math.cos(sun.theta) * distance

    #----------------------------------------------
    # Update selected object in viewport
    #----------------------------------------------
    obj.location = locX, locY, locZ


def set_sun_rotations(obj, rotation_euler):
    rotation_quaternion = rotation_euler.to_quaternion()
    obj.rotation_quaternion = rotation_quaternion

    if obj.rotation_mode in {'XZY', 'YXZ', 'YZX', 'ZXY','ZYX'}:
        obj.rotation_euler = rotation_quaternion.to_euler(obj.rotation_mode)
    else:
        obj.rotation_euler = rotation_euler

    rotation_axis_angle = obj.rotation_quaternion.to_axis_angle()
    obj.rotation_axis_angle = (rotation_axis_angle[1],
                               *rotation_axis_angle[0])


def calc_sunrise_set_UTC(rise, jd, latitude, longitude):
    t = calc_time_julian_cent(jd)
    eq_time = calc_equation_of_time(t)
    solar_dec = calc_sun_declination(t)
    hour_angle = calc_hour_angle_sunrise(latitude, solar_dec)
    if not rise:
        hour_angle = -hour_angle
    delta = longitude + degrees(hour_angle)
    time_UTC = 720 - (4.0 * delta) - eq_time
    return time_UTC


def calc_sun_declination(t):
    e = radians(obliquity_correction(t))
    L = apparent_longitude_of_sun(t)
    solar_dec = sun_declination(e, L)
    return solar_dec


def calc_hour_angle_sunrise(lat, solar_dec):
    lat_rad = radians(lat)
    HAarg = (math.cos(radians(90.833)) /
            (math.cos(lat_rad) * math.cos(solar_dec))
            - math.tan(lat_rad) * math.tan(solar_dec))
    if HAarg < -1.0:
        HAarg = -1.0
    elif HAarg > 1.0:
        HAarg = 1.0
    HA = math.acos(HAarg)
    return HA


def calc_solar_noon(jd, longitude, timezone, dst):
    t = calc_time_julian_cent(jd - longitude / 360.0)
    eq_time = calc_equation_of_time(t)
    noon_offset = 720.0 - (longitude * 4.0) - eq_time
    newt = calc_time_julian_cent(jd + noon_offset / 1440.0)
    eq_time = calc_equation_of_time(newt)

    nv = 780.0 if dst else 720.0
    noon_local = (nv- (longitude * 4.0) - eq_time + (timezone * 60.0)) % 1440
    sun.solar_noon.time = noon_local / 60.0


def calc_sunrise_sunset(rise):
    zone = -sun.UTC_zone

    jd = get_julian_day(sun.year, sun.month, sun.day)
    time_UTC = calc_sunrise_set_UTC(rise, jd, sun.latitude, sun.longitude)
    new_time_UTC = calc_sunrise_set_UTC(rise, jd + time_UTC / 1440.0,
                     sun.latitude, sun.longitude)
    time_local = new_time_UTC + (-zone * 60.0)
    tl = time_local / 60.0
    get_sun_position(tl, sun.latitude, sun.longitude, 0.0,
            zone, sun.month, sun.day, sun.year,
            sun.sun_distance)
    if sun.use_daylight_savings:
        time_local += 60.0
        tl = time_local / 60.0
    tl %= 24.0
    if rise:
        sun.sunrise.time = tl
        sun.sunrise.azimuth = sun.azimuth
        sun.sunrise.elevation = sun.elevation
        calc_solar_noon(jd, sun.longitude, -zone, sun.use_daylight_savings)
        get_sun_position(sun.solar_noon.time, sun.latitude, sun.longitude,
            0.0, zone, sun.month, sun.day, sun.year,
            sun.sun_distance)
        sun.solar_noon.elevation = sun.elevation
    else:
        sun.sunset.time = tl
        sun.sunset.azimuth = sun.azimuth
        sun.sunset.elevation = sun.elevation

##########################################################################
## Get the elapsed julian time since 1/1/2000 12:00 gmt
## Y2k epoch (1/1/2000 12:00 gmt) is Julian day 2451545.0
##########################################################################


def julian_time_from_y2k(utc_time, year, month, day):
    century = 36525.0  # Days in Julian Century
    epoch = 2451545.0  # Julian Day for 1/1/2000 12:00 gmt
    jd = get_julian_day(year, month, day)
    return ((jd + (utc_time / 24)) - epoch) / century


def get_julian_day(year, month, day):
    if month <= 2:
        year -= 1
        month += 12
    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4.0)
    jd = (math.floor((365.25 * (year + 4716.0))) +
         math.floor(30.6001 * (month + 1)) + day + B - 1524.5)
    return jd


def calc_time_julian_cent(jd):
    t = (jd - 2451545.0) / 36525.0
    return t


def sun_declination(e, L):
    return (math.asin(math.sin(e) * math.sin(L)))


def calc_equation_of_time(t):
    epsilon = obliquity_correction(t)
    ml = radians(mean_longitude_sun(t))
    e = eccentricity_earth_orbit(t)
    m = radians(mean_anomaly_sun(t))
    y = math.tan(radians(epsilon) / 2.0)
    y = y * y
    sin2ml = math.sin(2.0 * ml)
    cos2ml = math.cos(2.0 * ml)
    sin4ml = math.sin(4.0 * ml)
    sinm = math.sin(m)
    sin2m = math.sin(2.0 * m)
    etime = (y * sin2ml - 2.0 * e * sinm + 4.0 * e * y *
             sinm * cos2ml - 0.5 * y ** 2 * sin4ml - 1.25 * e ** 2 * sin2m)
    return (degrees(etime) * 4)


def obliquity_correction(t):
    ec = obliquity_of_ecliptic(t)
    omega = 125.04 - 1934.136 * t
    return (ec + 0.00256 * math.cos(radians(omega)))


def obliquity_of_ecliptic(t):
    return ((23.0 + 26.0 / 60 + (21.4480 - 46.8150) / 3600 * t -
            (0.00059 / 3600) * t ** 2 + (0.001813 / 3600) * t ** 3))


def true_longitude_of_sun(t):
    return (mean_longitude_sun(t) + equation_of_sun_center(t))


def calc_sun_apparent_long(t):
    o = true_longitude_of_sun(t)
    omega = 125.04 - 1934.136 * t
    lamb = o - 0.00569 - 0.00478 * math.sin(radians(omega))
    return lamb


def apparent_longitude_of_sun(t):
    return (radians(true_longitude_of_sun(t) - 0.00569 - 0.00478 *
            math.sin(radians(125.04 - 1934.136 * t))))


def mean_longitude_sun(t):
    return (280.46646 + 36000.76983 * t + 0.0003032 * t ** 2) % 360


def equation_of_sun_center(t):
    m = radians(mean_anomaly_sun(t))
    c = ((1.914602 - 0.004817 * t - 0.000014 * t ** 2) * math.sin(m) +
        (0.019993 - 0.000101 * t) * math.sin(m * 2) +
         0.000289 * math.sin(m * 3))
    return c


def mean_anomaly_sun(t):
    return (357.52911 + t * (35999.05029 - 0.0001537 * t))


def eccentricity_earth_orbit(t):
    return (0.016708634 - 0.000042037 * t - 0.0000001267 * t ** 2)
