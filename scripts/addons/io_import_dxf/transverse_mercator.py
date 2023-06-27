# SPDX-FileCopyrightText: 2014-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from math import sin, cos, atan, atanh, radians, tan, sinh, asin, cosh, degrees

# see conversion formulas at
# http://en.wikipedia.org/wiki/Transverse_Mercator_projection
# http://mathworld.wolfram.com/MercatorProjection.html


class TransverseMercator:
    radius = 6378137

    def __init__(self, lat=0, lon=0):
        self.lat = lat  # in degrees
        self.lon = lon  # in degrees
        self.lat_rad = radians(self.lat)
        self.lon_rad = radians(self.lon)

    def fromGeographic(self, lat, lon):
        lat_rad = radians(lat)
        lon_rad = radians(lon)
        B = cos(lat_rad) * sin(lon_rad - self.lon_rad)
        x = self.radius * atanh(B)
        y = self.radius * (atan(tan(lat_rad) / cos(lon_rad - self.lon_rad)) - self.lat_rad)
        return x, y

    def toGeographic(self, x, y):
        x /= self.radius
        y /= self.radius
        D = y + self.lat_rad
        lon = atan(sinh(x) / cos(D))
        lat = asin(sin(D) / cosh(x))

        lon = self.lon + degrees(lon)
        lat = degrees(lat)
        return lat, lon
