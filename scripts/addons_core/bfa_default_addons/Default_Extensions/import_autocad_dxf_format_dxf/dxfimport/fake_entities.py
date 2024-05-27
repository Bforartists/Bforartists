# SPDX-FileCopyrightText: 2014-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later


class ArcEntity:
    """
    Used in convert.bulge_to_cubic() since bulges define how much a straight polyline segment should be transformed to
    an arc. ArcEntity is just used to call do.arc() without having a real Arc-Entity from dxfgrabber.
    """
    def __init__(self, start, end, center, radius, angdir):
        self.start_angle = start
        self.end_angle = end
        self.center = center
        self.radius = radius
        self.angdir = angdir

    def __str__(self):
        return "startangle: %s, endangle: %s, center: %s, radius: %s, angdir: %s" % \
               (str(self.start_angle), str(self.end_angle), str(self.center), str(self.radius), str(self.angdir))


class LineEntity:
    """
    Used in do._gen_meshface()
    """
    def __init__(self, start, end):
        self.start = start
        self.end = end
