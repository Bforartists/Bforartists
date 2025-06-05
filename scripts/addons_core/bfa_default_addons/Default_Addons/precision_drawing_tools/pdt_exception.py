# SPDX-FileCopyrightText: 2019-2022 Alan Odom (Clockmender)
# SPDX-FileCopyrightText: 2019-2022 Rune Morling (ermo)
#
# SPDX-License-Identifier: GPL-2.0-or-later

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
