# ##### BEGIN GPL LICENSE BLOCK #####
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

# <pep8 compliant>

"""Importing a vector file into Model format.
"""

__author__ = "howard.trickey@gmail.com"

from . import geom
from . import model
from . import vecfile
from . import art2polyarea
from . import triquad
from . import offset
import math


class ImportOptions(object):
    """Contains options used to control model import.

    Attributes:
      quadrangulate: bool - should n-gons be quadrangulated?
      convert_options: art2polyarea.ConvertOptions -
        options about how to convert vector files into
        polygonal areas
      scaled_side_target: float - scale model so that longest side
        is this length, if > 0.
      extrude_depth: float - if > 0, extrude polygons up by this amount
      bevel_amount: float - if > 0, inset polygons by this amount
      bevel_pitch: float - if > 0, angle in radians of bevel
      cap_back: bool - should we cap the back, if extruding?
    """

    def __init__(self):
        self.quadrangulate = True
        self.convert_options = art2polyarea.ConvertOptions()
        self.scaled_side_target = 4.0
        self.extrude_depth = 0.0
        self.bevel_amount = 0.0
        self.bevel_pitch = 45.0 * math.pi / 180.0
        self.cap_back = False


def ReadVecFileToModel(fname, options):
    """Read vector art file and convert to Model.

    Args:
      fname: string - the file to read
      options: ImportOptions - specifies some choices about import
    Returns:
      (Model, string): if there was a major problem, Model may be None.
        The string will be errors and warnings.
    """

    art = vecfile.ParseVecFile(fname)
    if art is None:
        return (None, "Problem reading file or unhandled type")
    return ArtToModel(art, options)


def ArtToModel(art, options):
    """Convert an Art object into a Model object.

    Args:
      art: geom.Art - the Art object to convert.
      options: ImportOptions - specifies some choices about import
    Returns:
      (geom.Model, string): if there was a major problem, Model may be None.
        The string will be errors and warnings.
    """

    pareas = art2polyarea.ArtToPolyAreas(art, options.convert_options)
    if not pareas:
        return (None, "No visible faces found")
    if options.scaled_side_target > 0:
        pareas.scale_and_center(options.scaled_side_target)
    m = model.PolyAreasToModel(pareas, options.bevel_amount,
      options.bevel_pitch, options.quadrangulate)
    if options.extrude_depth > 0:
        model.ExtrudePolyAreasInModel(m, pareas, options.extrude_depth,
          options.cap_back)
    return (m, "")
