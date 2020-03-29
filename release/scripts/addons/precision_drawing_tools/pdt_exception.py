# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

# -----------------------------------------------------------------------
# Author: Alan Odom (Clockmender), Rune Morling (ermo) Copyright (c) 2019
# -----------------------------------------------------------------------
#
# Exceptions are used in the absence of nullable types in python


class SelectionError(Exception):
    """Selection Error Exception."""
    pass


class InvalidVector(Exception):
    """Invalid Vector Exception."""
    pass


class CommandFailure(Exception):
    """Command Failure Exception."""
    pass


class ObjectModeError(Exception):
    """Object Mode Error Exception."""
    pass


class MathsError(Exception):
    """Mathematical Expression Error Exception."""
    pass


class InfRadius(Exception):
    """Infinite Radius Error Exception."""
    pass


class NoObjectError(Exception):
    """No Active Object Exception."""
    pass


class IntersectionError(Exception):
    """Failure to Find Intersect Exception."""
    pass


class InvalidOperation(Exception):
    """Invalid Operation Error Exception."""
    pass


class VerticesConnected(Exception):
    """Vertices Already Connected Exception."""
    pass


class InvalidAngle(Exception):
    """Angle Given was Outside Parameters Exception."""
    pass

class ShaderError(Exception):
    """GL Shader Error Exception."""
    pass

class FeatureError(Exception):
    """Wrong Feature Type Error Exception."""
    pass

class DistanceError(Exception):
    """Invalid Distance (Separation) Error."""
    pass
