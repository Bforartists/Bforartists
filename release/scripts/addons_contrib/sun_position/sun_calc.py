from mathutils import *
import math
import datetime

from . properties import *

Degrees = "\xb0"


def format_time(theTime, UTCzone, daylightSavings, longitude):
    hh = str(int(theTime))
    min = (theTime - int(theTime)) * 60
    sec = int((min - int(min)) * 60)
    mm = "0" + str(int(min)) if min < 10 else str(int(min))
    ss = "0" + str(sec) if sec < 10 else str(sec)

    zone = UTCzone
    if(longitude < 0):
        zone *= -1
    if daylightSavings:
        zone += 1
    gt = int(theTime) - zone

    if gt < 0:
        gt = 24 + gt
    elif gt > 23:
        gt = gt - 24
    gt = str(gt)

    return ("Local: " + hh + ":" + mm + ":" + ss,
            "UTC: " + gt + ":" + mm + ":" + ss)


def format_hms(theTime):
    hh = str(int(theTime))
    min = (theTime - int(theTime)) * 60
    sec = int((min - int(min)) * 60)
    mm = "0" + str(int(min)) if min < 10 else str(int(min))
    ss = "0" + str(sec) if sec < 10 else str(sec)

    return (hh + ":" + mm + ":" + ss)


def format_lat_long(latLong, isLatitude):
    hh = str(abs(int(latLong)))
    min = abs((latLong - int(latLong)) * 60)
    sec = abs(int((min - int(min)) * 60))
    mm = "0" + str(int(min)) if min < 10 else str(int(min))
    ss = "0" + str(sec) if sec < 10 else str(sec)
    if latLong == 0:
        coordTag = " "
    else:
        if isLatitude:
            coordTag = " N" if latLong > 0 else " S"
        else:
            coordTag = " E" if latLong > 0 else " W"

    return hh + Degrees + " " + mm + "' " + ss + '"' + coordTag

############################################################################
#
# PlaceSun() will cycle through all the selected objects of type LAMP or
# MESH and call setSunPosition to place them in the sky.
#
############################################################################


def Move_sun():
    if Sun.PP.UsageMode == "HDR":
        Sun.Theta = math.pi / 2 - degToRad(Sun.Elevation)
        Sun.Phi = -Sun.Azimuth

        locX = math.sin(Sun.Phi) * math.sin(-Sun.Theta) * Sun.SunDistance
        locY = math.sin(Sun.Theta) * math.cos(Sun.Phi) * Sun.SunDistance
        locZ = math.cos(Sun.Theta) * Sun.SunDistance

        try:
            nt = bpy.context.scene.world.node_tree.nodes
            envTex = nt.get(Sun.HDR_texture)
            if Sun.Bind.azDiff and envTex.texture_mapping.rotation.z == 0.0:
                envTex.texture_mapping.rotation.z = Sun.Bind.azDiff

            if envTex and Sun.BindToSun:
                az = Sun.Azimuth
                if Sun.Bind.azStart < az:
                    taz = az - Sun.Bind.azStart
                else:
                    taz = -(Sun.Bind.azStart - az)
                envTex.texture_mapping.rotation.z += taz
                Sun.Bind.azStart = az

            obj = bpy.context.scene.objects.get(Sun.SunObject)

            try:
                obj.location = locX, locY, locZ
            except:
                pass

            if obj.type == 'LAMP':
                obj.rotation_euler = (
                    (math.radians(Sun.Elevation - 90), 0, -Sun.Azimuth))
        except:
            pass
        return True

    totalObjects = len(Sun.Selected_objects)

    localTime = Sun.Time
    if Sun.Longitude > 0:
        zone = Sun.UTCzone * -1
    else:
        zone = Sun.UTCzone
    if Sun.DaylightSavings:
        zone -= 1

    northOffset = radToDeg(Sun.NorthOffset)

    if Sun.ShowRiseSet:
        calcSunrise_Sunset(1)
        calcSunrise_Sunset(0)

    getSunPosition(None, localTime, Sun.Latitude, Sun.Longitude,
                   northOffset, zone, Sun.Month, Sun.Day, Sun.Year,
                   Sun.SunDistance)

    if Sun.UseSkyTexture:
        try:
            nt = bpy.context.scene.world.node_tree.nodes
            sunTex = nt.get(Sun.SkyTexture)
            if sunTex:
                locX = math.sin(Sun.Phi) * math.sin(-Sun.Theta)
                locY = math.sin(Sun.Theta) * math.cos(Sun.Phi)
                locZ = math.cos(Sun.Theta)
                sunTex.texture_mapping.rotation.z = 0.0
                sunTex.sun_direction = locX, locY, locZ

        except:
            pass

    if Sun.UseSunObject:
        try:
            obj = bpy.context.scene.objects.get(Sun.SunObject)
            setSunPosition(obj, Sun.SunDistance)
            if obj.type == 'LAMP':
                obj.rotation_euler = (
                    (math.radians(Sun.Elevation - 90), 0,
                     math.radians(-Sun.AzNorth)))
        except:
            pass

    if totalObjects < 1 or not Sun.UseObjectGroup:
        return False

    if Sun.ObjectGroup == 'ECLIPTIC':
        # Ecliptic
        if totalObjects > 1:
            timeIncrement = Sun.TimeSpread / (totalObjects - 1)
            localTime = localTime + timeIncrement * (totalObjects - 1)
        else:
            timeIncrement = Sun.TimeSpread

        for obj in Sun.Selected_objects:
            mesh = obj.type
            if mesh == 'LAMP' or mesh == 'MESH':
                getSunPosition(obj,
                               localTime,
                               Sun.Latitude, Sun.Longitude,
                               northOffset, zone,
                               Sun.Month, Sun.Day, Sun.Year,
                               Sun.SunDistance)
                setSunPosition(obj, Sun.SunDistance)
                localTime = localTime - timeIncrement
                if mesh == 'LAMP':
                    obj.rotation_euler = (
                        (math.radians(Sun.Elevation - 90), 0,
                         math.radians(-Sun.AzNorth)))
    else:
        # Analemma
        dayIncrement = 365 / totalObjects
        day = Sun.Day_of_year + dayIncrement * (totalObjects - 1)
        for obj in Sun.Selected_objects:
            mesh = obj.type
            if mesh == 'LAMP' or mesh == 'MESH':
                dt = (datetime.date(Sun.Year, 1, 1) +
                      datetime.timedelta(day - 1))
                getSunPosition(obj, localTime,
                               Sun.Latitude, Sun.Longitude,
                               northOffset, zone, dt.month, dt.day,
                               Sun.Year, Sun.SunDistance)
                setSunPosition(obj, Sun.SunDistance)
                day -= dayIncrement
                if mesh == 'LAMP':
                    obj.rotation_euler = (
                        (math.radians(Sun.Elevation - 90), 0,
                         math.radians(-Sun.AzNorth)))

    return True

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


def getSunPosition(obj, localTime, latitude, longitude, northOffset,
                   utcZone, month, day, year, distance):

    longitude *= -1                 # for internal calculations
    utcTime = localTime + utcZone   # Set Greenwich Meridian Time

    if latitude > 89.93:            # Latitude 90 and -90 gives
        latitude = degToRad(89.93)  # erroneous results so nudge it
    elif latitude < -89.93:
        latitude = degToRad(-89.93)
    else:
        latitude = degToRad(latitude)

    t = julianTimeFromY2k(utcTime, year, month, day)

    e = degToRad(obliquityCorrection(t))
    L = apparentLongitudeOfSun(t)
    solarDec = sunDeclination(e, L)
    eqtime = calcEquationOfTime(t)

    timeCorrection = (eqtime - 4 * longitude) + 60 * utcZone
    trueSolarTime = ((utcTime - utcZone) * 60.0 + timeCorrection) % 1440

    hourAngle = trueSolarTime / 4.0 - 180.0
    if hourAngle < -180.0:
        hourAngle += 360.0

    csz = (math.sin(latitude) * math.sin(solarDec) +
           math.cos(latitude) * math.cos(solarDec) *
           math.cos(degToRad(hourAngle)))
    if csz > 1.0:
        csz = 1.0
    elif csz < -1.0:
        csz = -1.0

    zenith = math.acos(csz)

    azDenom = math.cos(latitude) * math.sin(zenith)

    if abs(azDenom) > 0.001:
        azRad = ((math.sin(latitude) *
                  math.cos(zenith)) - math.sin(solarDec)) / azDenom
        if abs(azRad) > 1.0:
            azRad = -1.0 if (azRad < 0.0) else 1.0
        azimuth = 180.0 - radToDeg(math.acos(azRad))
        if hourAngle > 0.0:
            azimuth = -azimuth
    else:
        azimuth = 180.0 if (latitude > 0.0) else 0.0

    if azimuth < 0.0:
        azimuth = azimuth + 360.0

    exoatmElevation = 90.0 - radToDeg(zenith)

    if exoatmElevation > 85.0:
        refractionCorrection = 0.0
    else:
        te = math.tan(degToRad(exoatmElevation))
        if exoatmElevation > 5.0:
            refractionCorrection = (
                58.1 / te - 0.07 / (te ** 3) + 0.000086 / (te ** 5))
        elif (exoatmElevation > -0.575):
            s1 = (-12.79 + exoatmElevation * 0.711)
            s2 = (103.4 + exoatmElevation * (s1))
            s3 = (-518.2 + exoatmElevation * (s2))
            refractionCorrection = 1735.0 + exoatmElevation * (s3)
        else:
            refractionCorrection = -20.774 / te

        refractionCorrection = refractionCorrection / 3600

    if Sun.ShowRefraction:
        solarElevation = 90.0 - (radToDeg(zenith) - refractionCorrection)
    else:
        solarElevation = 90.0 - radToDeg(zenith)

    solarAzimuth = azimuth + northOffset

    Sun.AzNorth = solarAzimuth

    Sun.Theta = math.pi / 2 - degToRad(solarElevation)
    Sun.Phi = degToRad(solarAzimuth) * -1
    Sun.Azimuth = azimuth
    Sun.Elevation = solarElevation


def setSunPosition(obj, distance):

    locX = math.sin(Sun.Phi) * math.sin(-Sun.Theta) * distance
    locY = math.sin(Sun.Theta) * math.cos(Sun.Phi) * distance
    locZ = math.cos(Sun.Theta) * distance

    #----------------------------------------------
    # Update selected object in viewport
    #----------------------------------------------
    try:
        obj.location = locX, locY, locZ
    except:
        pass


def calcSunriseSetUTC(rise, jd, latitude, longitude):
    t = calcTimeJulianCent(jd)
    eqTime = calcEquationOfTime(t)
    solarDec = calcSunDeclination(t)
    hourAngle = calcHourAngleSunrise(latitude, solarDec)
    if not rise:
        hourAngle = -hourAngle
    delta = longitude + radToDeg(hourAngle)
    timeUTC = 720 - (4.0 * delta) - eqTime
    return timeUTC


def calcSunDeclination(t):
    e = degToRad(obliquityCorrection(t))
    L = apparentLongitudeOfSun(t)
    solarDec = sunDeclination(e, L)
    return solarDec


def calcHourAngleSunrise(lat, solarDec):
    latRad = degToRad(lat)
    HAarg = (math.cos(degToRad(90.833)) /
             (math.cos(latRad) * math.cos(solarDec))
             - math.tan(latRad) * math.tan(solarDec))
    if HAarg < -1.0:
        HAarg = -1.0
    elif HAarg > 1.0:
        HAarg = 1.0
    HA = math.acos(HAarg)
    return HA


def calcSolarNoon(jd, longitude, timezone, dst):
    t = calcTimeJulianCent(jd - longitude / 360.0)
    eqTime = calcEquationOfTime(t)
    noonOffset = 720.0 - (longitude * 4.0) - eqTime
    newt = calcTimeJulianCent(jd + noonOffset / 1440.0)
    eqTime = calcEquationOfTime(newt)

    nv = 780.0 if dst else 720.0
    noonLocal = (nv - (longitude * 4.0) - eqTime + (timezone * 60.0)) % 1440
    Sun.SolarNoon.time = noonLocal / 60.0


def calcSunrise_Sunset(rise):
    if Sun.Longitude > 0:
        zone = Sun.UTCzone * -1
    else:
        zone = Sun.UTCzone

    jd = getJulianDay(Sun.Year, Sun.Month, Sun.Day)
    timeUTC = calcSunriseSetUTC(rise, jd, Sun.Latitude, Sun.Longitude)
    newTimeUTC = calcSunriseSetUTC(rise, jd + timeUTC / 1440.0,
                                   Sun.Latitude, Sun.Longitude)
    timeLocal = newTimeUTC + (-zone * 60.0)
    tl = timeLocal / 60.0
    getSunPosition(None, tl, Sun.Latitude, Sun.Longitude, 0.0,
                   zone, Sun.Month, Sun.Day, Sun.Year,
                   Sun.SunDistance)
    if Sun.DaylightSavings:
        timeLocal += 60.0
        tl = timeLocal / 60.0
    if tl < 0.0:
        tl += 24.0
    elif tl > 24.0:
        tl -= 24.0
    if rise:
        Sun.Sunrise.time = tl
        Sun.Sunrise.azimuth = Sun.Azimuth
        Sun.Sunrise.elevation = Sun.Elevation
        calcSolarNoon(jd, Sun.Longitude, -zone, Sun.DaylightSavings)
        getSunPosition(None, Sun.SolarNoon.time, Sun.Latitude, Sun.Longitude,
                       0.0, zone, Sun.Month, Sun.Day, Sun.Year,
                       Sun.SunDistance)
        Sun.SolarNoon.elevation = Sun.Elevation
    else:
        Sun.Sunset.time = tl
        Sun.Sunset.azimuth = Sun.Azimuth
        Sun.Sunset.elevation = Sun.Elevation

##########################################################################
# Get the elapsed julian time since 1/1/2000 12:00 gmt
# Y2k epoch (1/1/2000 12:00 gmt) is Julian day 2451545.0
##########################################################################


def julianTimeFromY2k(utcTime, year, month, day):
    century = 36525.0  # Days in Julian Century
    epoch = 2451545.0  # Julian Day for 1/1/2000 12:00 gmt
    jd = getJulianDay(year, month, day)
    return ((jd + (utcTime / 24)) - epoch) / century


def getJulianDay(year, month, day):
    if month <= 2:
        year -= 1
        month += 12
    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4.0)
    jd = (math.floor((365.25 * (year + 4716.0))) +
          math.floor(30.6001 * (month + 1)) + day + B - 1524.5)
    return jd


def calcTimeJulianCent(jd):
    t = (jd - 2451545.0) / 36525.0
    return t


def sunDeclination(e, L):
    return (math.asin(math.sin(e) * math.sin(L)))


def calcEquationOfTime(t):
    epsilon = obliquityCorrection(t)
    ml = degToRad(meanLongitudeSun(t))
    e = eccentricityEarthOrbit(t)
    m = degToRad(meanAnomalySun(t))
    y = math.tan(degToRad(epsilon) / 2.0)
    y = y * y
    sin2ml = math.sin(2.0 * ml)
    cos2ml = math.cos(2.0 * ml)
    sin4ml = math.sin(4.0 * ml)
    sinm = math.sin(m)
    sin2m = math.sin(2.0 * m)
    etime = (y * sin2ml - 2.0 * e * sinm + 4.0 * e * y *
             sinm * cos2ml - 0.5 * y ** 2 * sin4ml - 1.25 * e ** 2 * sin2m)
    return (radToDeg(etime) * 4)


def obliquityCorrection(t):
    ec = obliquityOfEcliptic(t)
    omega = 125.04 - 1934.136 * t
    return (ec + 0.00256 * math.cos(degToRad(omega)))


def obliquityOfEcliptic(t):
    return ((23.0 + 26.0 / 60 + (21.4480 - 46.8150) / 3600 * t -
             (0.00059 / 3600) * t ** 2 + (0.001813 / 3600) * t ** 3))


def trueLongitudeOfSun(t):
    return (meanLongitudeSun(t) + equationOfSunCenter(t))


def calcSunApparentLong(t):
    o = trueLongitudeOfSun(t)
    omega = 125.04 - 1934.136 * t
    lamb = o - 0.00569 - 0.00478 * math.sin(degToRad(omega))
    return lamb


def apparentLongitudeOfSun(t):
    return (degToRad(trueLongitudeOfSun(t) - 0.00569 - 0.00478 *
                     math.sin(degToRad(125.04 - 1934.136 * t))))


def meanLongitudeSun(t):
    return (280.46646 + 36000.76983 * t + 0.0003032 * t ** 2) % 360


def equationOfSunCenter(t):
    m = degToRad(meanAnomalySun(t))
    c = ((1.914602 - 0.004817 * t - 0.000014 * t ** 2) * math.sin(m) +
         (0.019993 - 0.000101 * t) * math.sin(m * 2) +
         0.000289 * math.sin(m * 3))
    return c


def meanAnomalySun(t):
    return (357.52911 + t * (35999.05029 - 0.0001537 * t))


def eccentricityEarthOrbit(t):
    return (0.016708634 - 0.000042037 * t - 0.0000001267 * t ** 2)


def degToRad(angleDeg):
    return (math.pi * angleDeg / 180.0)


def radToDeg(angleRad):
    return (180.0 * angleRad / math.pi)
