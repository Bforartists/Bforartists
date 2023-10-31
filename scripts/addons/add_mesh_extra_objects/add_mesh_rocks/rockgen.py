# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Blender rock creation tool
#
# Based on BlenderGuru's asteroid tutorial and personal experimentation.
#   Tutorial: http://www.blenderguru.com/how-to-make-a-realistic-asteroid/
# Update with another tutorial shared by "rusted" of BlenderArtists:
#   Tutorial: http://saschahenrichs.blogspot.com/2010/03/3dsmax-environment-modeling-1.html
#
# Uses the NumPy Gaussian random number generator to generate a
# a rock within a given range and give some randomness to the displacement
# texture values.  NumPy's gaussian generator was chosen as, based on
# profiling I performed, it runs in about half the time as the built in
# Python gaussian equivalent.  I would like to shift the script to use the
# NumPy beta distribution as it ran in about half the time as the NumPy
# gaussian once the skew calculations are added.
#
# Set lower and upper bounds to the same for no randomness.
#
# Tasks:
#   Generate meshes with random scaling between given values.
#       - Allow for a skewed distribution
#           *** Completed on 4/17/2011 ***
#       - Create a set of meshes that can be used
#   Give the user the ability to set the subsurf level (detail level)
#       *** Completed on 4/29/2011 ***
#       - Set subsurf modifiers to default at view:3, render:3.
#           *** Completed on 4/17/2011 ***
#       - Set crease values to allow for hard edges on first subsurf.
#           *** Completed on 4/29/2011 ***
#   Be able to generate and add a texture to the displacement modifiers.
#       *** Completed 5/17/2011 ***
#       - Generate three displacement modifiers.
#           - The first only uses a Musgrave for initial intentations.
#           *** Now generating four displacement modifiers ***
#           *** Completed on 5/17/2011 ***
#       - Set a randomness for the type and values of the displacement texture.
#           *** Completed 5/9/2011 ***
#       - Allow the user to set a value for the range of displacement.
#           -> Modification: have user set "roughness" and "roughness range".
#           *** Compleded on 4/23/2011 ***
#   Set material settings and assign material textures
#       *** Completed 6/9/2011 ***
#       - Mossiness of the rocks.
#           *** Completed 6/9/2011 ***
#       - Color of the rocks.
#           *** Completed 5/16/2011 ***
#       - Wetness/shinyness of the rock.
#           *** Completed 5/6/2011 ***
#       - For all the user provides a mean value for a skewed distribution.
#           *** Removed to lessen usage complexity ***
#   Add some presets (mesh) to make it easier to use
#       - Examples: river rock, asteroid, quaried rock, etc
#           *** Completed 7/12/2011 ***
#
# Code Optimization:
#   Remove all "bpy.ops" operations with "bpy.data" base operations.
#   Remove material/texture cataloging with building a list of
#       returned values from bpy.data.*.new() operations.
#       *** Completed on 9/6/2011 ***
#   Search for places where list comprehensions can be used.
#   Look for alternate methods
#       - Possible alternate and more efficient data structures
#       - Possible alternate algorithms may realize greater performance
#       - Look again at multi-processing.  Without bpy.ops is might
#           be viable.
#
# Future tasks:
#   Multi-thread the script
#       *** Will not be implemented.  Multi-processing is adding to much
#           overhead to realize a performance increase ***
#       - Learn basic multi-threading in Python (multiprocessing)
#       - Break material generation into separate threads (processes)
#       - Break mesh generation into separate threads (processes)
#       - Move name generation, texture ID generation, etc to process first
#       - Roll version to 2.0 on completion
#
# Paul "BrikBot" Marshall
# Created: April 17, 2011
# Last Modified: November 17, 2011
# Homepage (blog): http://post.darkarsenic.com/
#                       //blog.darkarsenic.com/
# Thanks to Meta-Androco, RickyBlender, Ace Dragon, and PKHG for ideas
#   and testing.
#
# Coded in IDLE, tested in Blender 2.59.  NumPy Recommended.
# Search for "@todo" to quickly find sections that need work.
#
# Remember -
#   Functional code comes before fast code.  Once it works, then worry about
#   making it faster/more efficient.

import bpy
import time
from . import (
    settings,
    utils
)
from .utils import skewedGauss
from .randomize_texture import randomizeTexture
from bpy_extras import object_utils
from mathutils import (
    Vector
)
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    EnumProperty
)

# This try block allows for the script to psudo-intelligently select the
# appropriate random to use.  If Numpy's random is present it will use that.
# If Numpy's random is not present, it will through a "module not found"
# exception and instead use the slower built-in random that Python has.
try:
    from numpy.random import random_integers as randint
    from numpy.random import normal as gauss
    from numpy.random import (
        seed,
        weibull)
#    print("Rock Generator: Numpy found.")
    numpy = True
except:
    from random import (
        randint,
        gauss,
        seed)
    from random import weibullvariate as weibull
    print("Rock Generator: Numpy not found.  Using Python's random.")
    numpy = False

# Global variables:
LASTROCK = 0


# Creates a new mesh:
#
# param: verts - Vector of vertices for the mesh.
#        edges - Edges for the mesh.  Can be "[]".
#        faces - Face tuples corresponding to vertices.
#        name  - Name of the mesh.
def createMeshObject(context, verts, edges, faces, name):
    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces.
    mesh.from_pydata(verts, edges, faces)

    # Update mesh geometry after adding stuff.
    mesh.update()

    if bpy.context.mode == "EDIT_MESH":
        bpy.ops.object.mode_set(mode='OBJECT')

    return object_utils.object_data_add(context, mesh, operator=None)


# Generates an object based on one of several different mesh types.
# All meshes have exactly eight vertices, and may be built from either
# tri's or quads.
#
# param: muX        - mean X offset value
#        sigmaX     - X offset standard deviation
#        scaleX     - X upper and lower bounds
#        upperSkewX - Is the distribution upperskewed?
#        muY        - mean Y offset value
#        sigmaY     - Y offset standard deviation
#        scaleY     - Y upper and lower bounds
#        upperSkewY - Is the distribution upperskewed?
#        muZ        - mean Z offset value
#        sigmaZ     - Z offset standard deviation
#        scaleZ     - Z upper and lower bounds
#        upperSkewY - Is the distribution upperskewed?
#        base       - base number on the end of the object name
#        shift      - Addition to the base number for multiple runs.
#        scaleDisplace - Scale the displacement maps
#
# return: name      - the built name of the object
def generateObject(context, muX, sigmaX, scaleX, upperSkewX, muY, sigmaY,
                   scaleY, upperSkewY, muZ, sigmaZ, scaleZ, upperSkewZ, base,
                   shift, scaleDisplace, scale_fac):
    x = []
    y = []
    z = []
    shape = randint(0, 11)

    # Cube
    # Use parameters to re-scale cube:
    # Reversed if/for nesting.  Should be a little faster.
    if shape == 0:
        for j in range(8):
            if sigmaX == 0:
                x.append(scaleX[0] / 2)
            else:
                x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 2)
            if sigmaY == 0:
                y.append(scaleY[0] / 2)
            else:
                y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) / 2)
            if sigmaZ == 0:
                z.append(scaleZ[0] / 2)
            else:
                z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
    elif shape == 1:
        for j in range(8):
            if j in [0, 1, 3, 4]:
                if sigmaX == 0:
                    x.append(scaleX[0] / 2)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 2)
                if sigmaY == 0:
                    y.append(scaleY[0] / 2)
                else:
                    y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) / 2)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
            elif j in [2, 5]:
                if sigmaX == 0:
                    x.append(0)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 4)
                if sigmaY == 0:
                    y.append(scaleY[0] / 2)
                else:
                    y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) / 2)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
            elif j in [6, 7]:
                if sigmaX == 0:
                    x.append(0)
                else:
                    x.append(skewedGauss(0, sigmaX, scaleX, upperSkewX) / 4)
                if sigmaY == 0:
                    y.append(0)
                else:
                    y.append(skewedGauss(0, sigmaY, scaleY, upperSkewY) / 4)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
    elif shape == 2:
        for j in range(8):
            if j in [0, 2, 5, 7]:
                if sigmaX == 0:
                    x.append(scaleX[0] / 4)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 4)
                if sigmaY == 0:
                    y.append(0)
                else:
                    y.append(skewedGauss(0, sigmaY, scaleY, upperSkewY) / 4)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 4)
            elif j in [1, 3, 4, 6]:
                if sigmaX == 0:
                    x.append(scaleX[0] / 2)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 2)
                if sigmaY == 0:
                    y.append(scaleY[0] / 2)
                else:
                    y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) / 2)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
    elif shape == 3:
        for j in range(8):
            if j > 0:
                if sigmaX == 0:
                    x.append(scaleX[0] / 2)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 2)
                if sigmaY == 0:
                    y.append(scaleY[0] / 2)
                else:
                    y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) / 2)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
            else:
                if sigmaX == 0:
                    x.append(0)
                else:
                    x.append(skewedGauss(0, sigmaX, scaleX, upperSkewX) / 8)
                if sigmaY == 0:
                    y.append(0)
                else:
                    y.append(skewedGauss(0, sigmaY, scaleY, upperSkewY) / 8)
                if sigmaZ == 0:
                    z.append(0)
                else:
                    z.append(skewedGauss(0, sigmaZ, scaleZ, upperSkewZ) / 8)
    elif shape == 4:
        for j in range(10):
            if j in [0, 9]:
                if sigmaX == 0:
                    x.append(0)
                else:
                    x.append(skewedGauss(0, sigmaX, scaleX, upperSkewX) / 2)
                if sigmaY == 0:
                    y.append(0)
                else:
                    y.append(skewedGauss(0, sigmaY, scaleY, upperSkewY) / 2)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
            elif j in [1, 2, 3, 4]:
                if sigmaX == 0:
                    x.append(scaleX[0] / 2)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 2)
                if sigmaY == 0:
                    y.append(scaleY[0] / 2)
                else:
                    y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) / 2)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
            elif j in [5, 7]:
                if sigmaX == 0:
                    x.append(0)
                else:
                    x.append(skewedGauss(0, sigmaX, scaleX, upperSkewX) / 3)
                if sigmaY == 0:
                    y.append(scaleY[0] / 3)
                else:
                    y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) / 3)
                if sigmaZ == 0:
                    z.append(0)
                else:
                    z.append(skewedGauss(0, sigmaZ, scaleZ, upperSkewZ) / 6)
            elif j in [6, 8]:
                if sigmaX == 0:
                    x.append(scaleX[0] / 3)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 3)
                if sigmaY == 0:
                    y.append(0)
                else:
                    y.append(skewedGauss(0, sigmaY, scaleY, upperSkewY) / 3)
                if sigmaZ == 0:
                    z.append(0)
                else:
                    z.append(skewedGauss(0, sigmaZ, scaleZ, upperSkewZ) / 6)
    elif shape == 5:
        for j in range(10):
            if j == 0:
                if sigmaX == 0:
                    x.append(0)
                else:
                    x.append(skewedGauss(0, sigmaX, scaleX, upperSkewX) / 8)
                if sigmaY == 0:
                    y.append(0)
                else:
                    y.append(skewedGauss(0, sigmaY, scaleY, upperSkewY) / 8)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
            elif j in [1, 2]:
                if sigmaX == 0:
                    x.append(scaleZ[0] * .125)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) * 0.125)
                if sigmaY == 0:
                    y.append(scaleZ[0] * 0.2165)
                else:
                    y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) * 0.2165)
                if sigmaZ == 0:
                    z.append(0)
                else:
                    z.append(skewedGauss(0, sigmaZ, scaleZ, upperSkewZ) / 4)
            elif j == 3:
                if sigmaX == 0:
                    x.append(scaleX[0] / 4)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 4)
                if sigmaY == 0:
                    y.append(0)
                else:
                    y.append(skewedGauss(0, sigmaY, scaleY, upperSkewY) / 4)
                if sigmaZ == 0:
                    z.append(0)
                else:
                    z.append(skewedGauss(0, sigmaZ, scaleZ, upperSkewZ) / 4)
            elif j in [4, 6]:
                if sigmaX == 0:
                    x.append(scaleX[0] * 0.25)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) * 0.25)
                if sigmaY == 0:
                    y.append(scaleY[0] * 0.433)
                else:
                    y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) * 0.433)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
            elif j == 5:
                if sigmaX == 0:
                    x.append(scaleX[0] / 4)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 4)
                if sigmaY == 0:
                    y.append(0)
                else:
                    y.append(skewedGauss(0, sigmaY, scaleY, upperSkewY) / 2)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
            elif j in [7, 9]:
                if sigmaX == 0:
                    x.append(scaleX[0] * 0.10825)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) * 0.10825)
                if sigmaY == 0:
                    y.append(scaleY[0] * 0.2165)
                else:
                    y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) * 0.2165)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
            elif j == 8:
                if sigmaX == 0:
                    x.append(scaleX[0] / 2)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 2)
                if sigmaY == 0:
                    y.append(0)
                else:
                    y.append(skewedGauss(0, sigmaY, scaleY, upperSkewY) / 4)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
    elif shape == 6:
        for j in range(7):
            if j > 0:
                if sigmaX == 0:
                    x.append(scaleX[0] / 2)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 2)
                if sigmaY == 0:
                    y.append(scaleY[0] / 2)
                else:
                    y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) / 2)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
            else:
                if sigmaX == 0:
                    x.append(scaleX[0] / 2)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 2)
                if sigmaY == 0:
                    y.append(0)
                else:
                    y.append(skewedGauss(0, sigmaY, scaleY, upperSkewY) / 2)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
    elif shape == 7:
        for j in range(10):
            if j in [1, 3, 4, 5, 8, 9]:
                if sigmaX == 0:
                    x.append(scaleX[0] / 2)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 2)
                if sigmaY == 0:
                    y.append(scaleY[0] / 2)
                else:
                    y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) / 2)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
            else:
                if sigmaX == 0:
                    x.append(scaleX[0] / 2)
                else:
                    x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 2)
                if sigmaY == 0:
                    y.append(0)
                else:
                    y.append(skewedGauss(0, sigmaY, scaleY, upperSkewY) / 2)
                if sigmaZ == 0:
                    z.append(scaleZ[0] / 2)
                else:
                    z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
    elif shape == 8:
        for j in range(7):
            if sigmaX == 0:
                x.append(scaleX[0] / 2)
            else:
                x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 2)
            if sigmaY == 0:
                y.append(scaleY[0] / 2)
            else:
                y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) / 2)
            if sigmaZ == 0:
                z.append(scaleZ[0] / 2)
            else:
                z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
    elif shape == 9:
        for j in range(8):
            if sigmaX == 0:
                x.append(scaleX[0] / 2)
            else:
                x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 2)
            if sigmaY == 0:
                y.append(scaleY[0] / 2)
            else:
                y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) / 2)
            if sigmaZ == 0:
                z.append(scaleZ[0] / 2)
            else:
                z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
    elif shape == 10:
        for j in range(7):
            if sigmaX == 0:
                x.append(scaleX[0] / 2)
            else:
                x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 2)
            if sigmaY == 0:
                y.append(scaleY[0] / 2)
            else:
                y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) / 2)
            if sigmaZ == 0:
                z.append(scaleZ[0] / 2)
            else:
                z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)
    elif shape == 11:
        for j in range(7):
            if sigmaX == 0:
                x.append(scaleX[0] / 2)
            else:
                x.append(skewedGauss(muX, sigmaX, scaleX, upperSkewX) / 2)
            if sigmaY == 0:
                y.append(scaleY[0] / 2)
            else:
                y.append(skewedGauss(muY, sigmaY, scaleY, upperSkewY) / 2)
            if sigmaZ == 0:
                z.append(scaleZ[0] / 2)
            else:
                z.append(skewedGauss(muZ, sigmaZ, scaleZ, upperSkewZ) / 2)

    # This is for scaling the displacement textures.
    # Scale the vertices so that their average is equal to 1 * scale factor.
    if scaleDisplace:
        averageX = (sum(x) / len(x)) * scale_fac[0]
        for i in range(len(x)):
            x[i] /= averageX
        averageY = (sum(y) / len(y)) * scale_fac[1]
        for i in range(len(y)):
            y[i] /= averageY
        averageZ = (sum(z) / len(z)) * scale_fac[2]
        for i in range(len(z)):
            z[i] /= averageZ

    # Build vertex and face arrays:
    if shape == 1:
        verts = [(-x[0], -y[0], -z[0]), (x[1], -y[1], -z[1]), (x[2], -y[2], z[2]),
                 (-x[3], y[3], -z[3]), (x[4], y[4], -z[4]), (x[5], y[5], z[5]),
                 (x[6], y[6], z[6]), (x[7], y[7], -z[7])]
        faces = [[0, 1, 2], [0, 1, 7], [3, 0, 7], [3, 4, 7], [1, 4, 7], [3, 4, 5], [1, 2, 6],
                 [1, 4, 6], [4, 5, 6], [0, 2, 6], [0, 3, 6], [3, 5, 6]]
    elif shape == 2:
        verts = [(-x[0], y[0], -z[0]), (x[1], -y[1], -z[1]), (x[2], y[2], -z[2]),
                 (-x[3], y[3], -z[3]), (-x[4], -y[4], z[4]), (x[5], y[5], z[5]),
                 (x[6], y[6], z[6]), (-x[7], y[7], z[7])]
        faces = [[0, 1, 2], [0, 2, 3], [0, 3, 7], [0, 7, 4], [1, 4, 5], [0, 1, 4], [5, 1, 2],
                 [5, 2, 6], [3, 2, 6], [3, 6, 7], [5, 4, 7], [5, 6, 7]]
    elif shape == 3:
        verts = [(x[0], y[0], z[0]), (x[1], -y[1], -z[1]), (x[2], y[2], -z[2]),
                 (-x[3], y[3], -z[3]), (x[4], -y[4], z[4]), (x[5], y[5], z[5]),
                 (-x[6], y[6], z[6]), (-x[7], -y[7], z[7])]
        faces = [[0, 1, 2], [0, 2, 3], [0, 3, 6], [0, 6, 7], [0, 7, 4], [0, 4, 1], [5, 4, 1, 2],
                 [5, 6, 3, 2], [5, 4, 7, 6]]
    elif shape == 4:
        verts = [(x[0], y[0], z[0]), (x[1], -y[1], -z[1]), (x[2], y[2], -z[2]),
                 (-x[3], y[3], -z[3]), (-x[4], -y[4], -z[4]), (x[5], -y[5], -z[5]),
                 (x[6], y[6], -z[6]), (x[7], y[7], -z[7]), (-x[8], y[8], -z[8]),
                 (x[9], y[9], -z[9])]
        faces = [[0, 1, 6], [0, 6, 2], [0, 2, 7], [0, 7, 3], [0, 3, 8], [0, 8, 4], [0, 4, 5],
                 [0, 5, 1], [1, 9, 2], [2, 9, 3], [3, 9, 4], [4, 9, 1], [1, 6, 2], [2, 7, 3],
                 [3, 8, 4], [4, 5, 1]]
    elif shape == 5:
        verts = [(x[0], y[0], z[0]), (x[1], -y[1], z[1]), (x[2], y[2], z[2]),
                 (-x[3], y[3], z[3]), (x[4], -y[4], -z[4]), (x[5], y[5], -z[5]),
                 (x[6], y[6], -z[6]), (-x[7], y[7], -z[7]), (-x[8], y[8], -z[8]),
                 (-x[9], -y[9], -z[9])]
        faces = [[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 4, 5], [1, 5, 2], [2, 5, 6], [2, 6, 7],
                 [2, 7, 3], [3, 7, 8], [3, 8, 9], [3, 9, 1], [1, 9, 4], [4, 5, 9], [5, 6, 7],
                 [7, 8, 9], [9, 5, 7]]
    elif shape == 6:
        verts = [(x[0], y[0], z[0]), (x[1], -y[1], -z[1]), (x[2], y[2], -z[2]),
                 (-x[3], y[3], -z[3]), (-x[4], y[4], z[4]), (-x[5], -y[5], z[5]),
                 (-x[6], -y[6], -z[6])]
        faces = [[0, 1, 2], [0, 2, 3, 4], [0, 1, 6, 5], [0, 4, 5], [1, 2, 3, 6], [3, 4, 5, 6]]
    elif shape == 7:
        verts = [(x[0], y[0], z[0]), (x[1], -y[1], -z[1]), (x[2], y[2], -z[2]),
                 (x[3], y[3], -z[3]), (-x[4], y[4], -z[4]), (-x[5], y[5], z[5]),
                 (-x[6], y[6], z[6]), (-x[7], y[7], -z[7]), (-x[8], -y[8], -z[8]),
                 (-x[9], -y[9], z[9])]
        faces = [[0, 1, 2], [0, 2, 3], [0, 5, 6], [0, 6, 9], [0, 1, 8, 9], [0, 3, 4, 5],
                 [1, 2, 7, 8], [2, 3, 4, 7], [4, 5, 6, 7], [6, 7, 8, 9]]
    elif shape == 8:
        verts = [(x[0], y[0], z[0]), (x[1], -y[1], -z[1]), (x[2], y[2], -z[2]),
                 (-x[3], y[3], -z[3]), (-x[4], -y[4], -z[4]), (-x[5], -y[5], z[5]),
                 (-x[6], y[6], z[6])]
        faces = [[0, 2, 1], [0, 1, 4], [0, 4, 5], [0, 5, 6], [0, 6, 3, 2], [2, 1, 4, 3],
                 [3, 6, 5, 4]]
    elif shape == 9:
        verts = [(-x[0], -y[0], -z[0]), (-x[1], y[1], -z[1]), (-x[2], y[2], z[2]),
                 (-x[3], -y[3], z[3]), (x[4], -y[4], -z[4]), (x[5], y[5], -z[5]),
                 (x[6], y[6], z[6]), (x[7], -y[7], z[7])]
        faces = [[0, 1, 6, 2], [1, 5, 7, 6], [5, 4, 3, 7], [4, 0, 2, 3], [0, 1, 5, 4], [3, 2, 6, 7]]
    elif shape == 10:
        verts = [(-x[0], -y[0], -z[0]), (-x[1], y[1], -z[1]), (-x[2], y[2], z[2]),
                 (x[3], -y[3], z[3]), (x[4], y[4], z[4]), (x[5], y[5], -z[5]),
                 (x[6], -y[6], -z[6])]
        faces = [[0, 2, 3], [0, 3, 6], [0, 1, 5, 6], [2, 3, 4], [0, 1, 2], [1, 2, 4, 5], [3, 4, 5, 6]]
    elif shape == 11:
        verts = [(-x[0], -y[0], -z[0]), (-x[1], y[1], -z[1]), (-x[2], y[2], z[2]),
                 (x[3], -y[3], z[3]), (x[4], y[4], z[4]), (x[5], y[5], -z[5]),
                 (x[6], -y[6], -z[6])]
        faces = [[0, 2, 3], [0, 3, 6], [0, 1, 5, 6], [2, 3, 4], [5, 6, 3], [1, 5, 3, 4], [0, 1, 4, 2]]
    else:
        verts = [(-x[0], -y[0], -z[0]), (-x[1], y[1], -z[1]), (-x[2], -y[2], z[2]),
                 (-x[3], y[3], z[3]), (x[4], -y[4], -z[4]), (x[5], y[5], -z[5]),
                 (x[6], -y[6], z[6]), (x[7], y[7], z[7])]
        faces = [[0, 1, 3, 2], [0, 1, 5, 4], [0, 4, 6, 2], [7, 5, 4, 6], [7, 3, 2, 6], [7, 5, 1, 3]]

    # name = "Rock." + str(base + shift).zfill(3)
    name = "rock"

    # Make object:
    obj = createMeshObject(context, verts, [], faces, name)

    if scaleDisplace:
        # bpy.data.objects[name].scale = Vector((averageX, averageY, averageZ))
        obj.scale = Vector((averageX, averageY, averageZ))

    # For a slight speed bump / Readability:
    # mesh = bpy.data.meshes[name]
    mesh = obj.data

    creases = mesh.edge_creases_ensure().data

    # Apply creasing:
    if shape == 0:
        for i in range(12):
            # todo: "0.375 / 3"?  WTF?  That = 0.125. . . .
            #   *** Completed 7/15/2011: Changed second one ***
            creases[i].value = gauss(0.125, 0.125)
    elif shape == 1:
        for i in [0, 2]:
            creases[i].value = gauss(0.5, 0.125)
        for i in [6, 9, 11, 12]:
            creases[i].value = gauss(0.25, 0.05)
        for i in [5, 7, 15, 16]:
            creases[i].value = gauss(0.125, 0.025)
    elif shape == 2:
        for i in range(18):
            creases[i].value = gauss(0.125, 0.025)
    elif shape == 3:
        for i in [0, 1, 6, 10, 13]:
            creases[i].value = gauss(0.25, 0.05)
        creases[8].value = gauss(0.5, 0.125)
    elif shape == 4:
        for i in [5, 6, 7, 10, 14, 16, 19, 21]:
            creases[i].value = gauss(0.5, 0.125)
    elif shape == 7:
        for i in range(18):
            if i in [0, 1, 2, 3, 6, 7, 8, 9, 13, 16]:
                creases[i].value = gauss(0.5, 0.125)
            elif i in [11, 17]:
                creases[i].value = gauss(0.25, 0.05)
            else:
                creases[i].value = gauss(0.125, 0.025)
    elif shape == 8:
        for i in range(12):
            if i in [0, 3, 8, 9, 10]:
                creases[i].value = gauss(0.5, 0.125)
            elif i == 11:
                creases[i].value = gauss(0.25, 0.05)
            else:
                creases[i].value = gauss(0.125, 0.025)
    elif shape == 9:
        for i in range(12):
            if i in [0, 3, 4, 11]:
                creases[i].value = gauss(0.5, 0.125)
            else:
                creases[i].value = gauss(0.25, 0.05)
    elif shape == 10:
        for i in range(12):
            if i in [0, 2, 3, 4, 8, 11]:
                creases[i].value = gauss(0.5, 0.125)
            elif i in [1, 5, 7]:
                creases[i].value = gauss(0.25, 0.05)
            else:
                creases[i].value = gauss(0.125, 0.025)
    elif shape == 11:
        for i in range(11):
            if i in [1, 2, 3, 4, 8, 11]:
                creases[i].value = gauss(0.25, 0.05)
            else:
                creases[i].value = gauss(0.125, 0.025)

    return obj


# Creates rock objects:
def generateRocks(context, scaleX, skewX, scaleY, skewY, scaleZ, skewZ,
                  scale_fac, detail, display_detail, deform, rough,
                  smooth_fac, smooth_it,
                  numOfRocks=1, userSeed=1.0,
                  scaleDisplace=False, randomSeed=True, use_enter_edit_mode=False):
    global LASTROCK
    sigmaX = 0
    sigmaY = 0
    sigmaZ = 0
    upperSkewX = False
    upperSkewY = False
    upperSkewZ = False
    shift = 0
    # vertexScaling = []

    # Seed the random Gaussian value generator:
    if randomSeed:
        seed(int(time.time()))
    else:
        seed(userSeed)

    # These values need to be really small to look good.
    # So the user does not have to use such ridiculously small values:
    deform /= 10
    rough /= 100

    # Verify that the min really is the min:
    if scaleX[1] < scaleX[0]:
        scaleX[0], scaleX[1] = scaleX[1], scaleX[0]
    if scaleY[1] < scaleY[0]:
        scaleY[0], scaleY[1] = scaleY[1], scaleY[0]
    if scaleZ[1] < scaleZ[0]:
        scaleZ[0], scaleZ[1] = scaleZ[1], scaleZ[0]

    # todo: edit below to allow for skewing the distribution
    #   *** todo completed 4/22/2011 ***
    #   *** Code now generating "int not scriptable error" in Blender ***
    #
    # Calculate mu and sigma for a Gaussian distributed random number
    #   generation:
    # If the lower and upper bounds are the same, skip the math.
    #
    # sigma is the standard deviation of the values.  The 95% interval is three
    # standard deviations, which is what we want most generated values to fall
    # in.  Since it might be skewed we are going to use half the difference
    # between the mean and the furthest bound and scale the other side down
    # post-number generation.
    if scaleX[0] != scaleX[1]:
        skewX = (skewX + 1) / 2
        muX = scaleX[0] + ((scaleX[1] - scaleX[0]) * skewX)
        if skewX < 0.5:
            sigmaX = (scaleX[1] - muX) / 3
        else:
            sigmaX = (muX - scaleX[0]) / 3
            upperSkewX = True
    else:
        muX = scaleX[0]
    if scaleY[0] != scaleY[1]:
        skewY = (skewY + 1) / 2
        muY = scaleY[0] + ((scaleY[1] - scaleY[0]) * skewY)
        if skewY < 0.5:
            sigmaY = (scaleY[1] - muY) / 3
        else:
            sigmaY = (muY - scaleY[0]) / 3
            upperSkewY = True
    else:
        muY = scaleY[0]
    if scaleZ[0] != scaleZ[1]:
        skewZ = (skewZ + 1) / 2
        muZ = scaleZ[0] + ((scaleZ[1] - scaleZ[0]) * skewZ)
        if skewZ < 0.5:
            sigmaZ = (scaleZ[1] - muZ) / 3
        else:
            sigmaZ = (muZ - scaleZ[0]) / 3
            upperSkewZ = True
    else:
        muZ = scaleZ

    rocks = []

    for i in range(numOfRocks):
        # todo: enable different random values for each (x,y,z) coordinate for
        # each vertex.  This will add additional randomness to the shape of the
        # generated rocks.
        #   *** todo completed 4/19/2011 ***
        #   *** Code is notably slower at high rock counts ***

        # name = generateObject(context, muX, sigmaX, scaleX, upperSkewX, muY,
        rock = generateObject(
            context, muX, sigmaX, scaleX, upperSkewX, muY,
            sigmaY, scaleY, upperSkewY, muZ, sigmaZ, scaleZ,
            upperSkewZ, i, LASTROCK, scaleDisplace, scale_fac)

        # rock = bpy.data.objects[name]

        # todo Map what the two new textures will be:
        # This is not working.  It works on paper so . . . ???
        #   *** todo completed on 4/23/2011 ***
        #   *** todo re-added as the first rock is getting
        #       'Texture.001' twice. ***
        #   *** todo completed on 4/25/2011 ***
        #   *** Script no longer needs to map new texture names 9/6/2011 ***

        # Create the four new textures:
        # todo Set displacement texture parameters:
        #   *** todo completed on 5/31/2011 ***
        # Voronoi has been removed from being an option for the fine detail
        #   texture.
        texTypes = ['CLOUDS', 'MUSGRAVE', 'DISTORTED_NOISE', 'STUCCI', 'VORONOI']
        newTex = []
        # The first texture is to give a more ranodm base shape appearance:
        newTex.append(bpy.data.textures.new(
            name='rock_displacement',
            type=texTypes[1]))
        randomizeTexture(newTex[0], 0)
        newTex.append(bpy.data.textures.new(
            name='rock_displacement',
            type=texTypes[4]))
        randomizeTexture(newTex[1], 0)
        if numpy:
            newTex.append(bpy.data.textures.new(
                name='rock_displacement',
                type=texTypes[int(round(weibull(1, 1)[0] / 2.125))]))
            randomizeTexture(newTex[2], 1)
            newTex.append(bpy.data.textures.new(
                name='rock_displacement',
                type=texTypes[int(round(weibull(1, 1)[0] / 2.125))]))
            randomizeTexture(newTex[3], 2)
        else:
            newTex.append(bpy.data.textures.new(
                name='rock_displacement',
                type=texTypes[int(round(weibull(1, 1) / 2.125))]))
            randomizeTexture(newTex[2], 1)
            newTex.append(bpy.data.textures.new(
                name='rock_displacement',
                type=texTypes[int(round(weibull(1, 1) / 2.125))]))
            randomizeTexture(newTex[3], 2)

        # Add modifiers:
        rock.modifiers.new(name="Subsurf", type='SUBSURF')
        rock.modifiers.new(name="Subsurf", type='SUBSURF')
        rock.modifiers.new(name="Displace", type='DISPLACE')
        rock.modifiers.new(name="Displace", type='DISPLACE')
        rock.modifiers.new(name="Displace", type='DISPLACE')
        rock.modifiers.new(name="Displace", type='DISPLACE')

        # If smoothing is enabled, allow a little randomness into the
        #   smoothing factor. Then add the smoothing modifier.
        if smooth_fac > 0.0 and smooth_it > 0:
            rock.modifiers.new(name="Smooth", type='SMOOTH')
            rock.modifiers[6].factor = gauss(smooth_fac, (smooth_fac ** 0.5) / 12)
            rock.modifiers[6].iterations = smooth_it
        # Make a call to random to keep things consistent:
        else:
            gauss(0, 1)

        # Set subsurf modifier parameters:
        rock.modifiers[0].levels = display_detail
        rock.modifiers[0].render_levels = detail
        rock.modifiers[1].levels = display_detail
        rock.modifiers[1].render_levels = detail

        # todo Set displacement modifier parameters:
        #   *** todo completed on 4/23/2011 ***
        #   *** toned down the variance on 4/26/2011 ***
        #   *** added third modifier on 4/28/2011 ***
        #   *** texture access changed on 9/6/2011 ***
        rock.modifiers[2].texture = newTex[0]
        rock.modifiers[2].strength = gauss(deform / 100, (1 / 300) * deform)
        rock.modifiers[2].mid_level = 0
        rock.modifiers[3].texture = newTex[1]
        rock.modifiers[3].strength = gauss(deform, (1 / 3) * deform)
        rock.modifiers[3].mid_level = 0
        rock.modifiers[4].texture = newTex[2]
        rock.modifiers[4].strength = gauss(rough * 2, (1 / 3) * rough)
        rock.modifiers[5].texture = newTex[3]
        rock.modifiers[5].strength = gauss(rough, (1 / 3) * rough)

        # Set mesh to be smooth and fix the normals:
        utils.smooth(rock.data)
        # utils.smooth(bpy.data.meshes[name])
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.normals_make_consistent()
        bpy.ops.object.editmode_toggle()

        if use_enter_edit_mode:
            for m in rock.modifiers:
                m.show_in_editmode = True
                m.show_on_cage = True

        # Store the last value of i:
        shift = i

        rocks.append(rock)

    # Add the shift to LASTROCK:
    LASTROCK += shift + 1

    return rocks


# Much of the code below is more-or-less imitation of other addons and as such
# I have left it undocumented.

class OBJECT_OT_add_mesh_rock(bpy.types.Operator):
    """Add rock objects"""
    bl_idname = "mesh.add_mesh_rock"
    bl_label = "Add Rocks"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Add rocks"

    # Get the preset values from the XML file.
    #   -> The script was morphed into a Python module
    #       to support this.
    # Tell settings.py to parse the XML file with the settings.
    # Then get the default values resulting from the parsing.
    # Make a list containing the default values and append to that
    # the presets specified in the same XML file.  This list will
    # be used to load preset values.
    settings.parse()
    defaults = settings.getDefault()
    presetsList = [defaults]
    presetsList += settings.getPresetLists()
    presets = []
    lastPreset = 0

    # Build the presets list for the enum property.
    # This needs to be a for loop as the user might add presets to
    # the XML file and those should show here:
    for i, preset in enumerate(presetsList):
        presets.append((str(i), preset[0], preset[0] + " preset values"))

    preset_values: EnumProperty(
        name="Presets",
        items=presets,
        description="Preset values for some rock types")

    num_of_rocks: IntProperty(
        name="Number of rocks",
        description="Number of rocks to generate. WARNING: Slow at high values!",
        min=1, max=1048576,
        soft_max=20,
        default=1)

    scale_X: FloatVectorProperty(
        name="X scale",
        description="X axis scaling range",
        min=0.0, max=256.0, step=1,
        default=defaults[1], size=2)
    skew_X: FloatProperty(
        name="X skew",
        description="X Skew ratio. 0.5 is no skew",
        min=-1.0, max=1.0, default=defaults[4])
    scale_Y: FloatVectorProperty(
        name="Y scale",
        description="Y axis scaling range",
        min=.0, max=256.0, step=1,
        default=defaults[2], size=2)
    skew_Y: FloatProperty(
        name="Y skew",
        description="Y Skew ratio. 0.5 is no skew",
        min=-1.0, max=1.0, default=defaults[5])
    scale_Z: FloatVectorProperty(
        name="Z scale",
        description="Z axis scaling range",
        min=0.0, max=256.0, step=1,
        default=defaults[3], size=2)
    skew_Z: FloatProperty(
        name="Z skew",
        description="Z Skew ratio. 0.5 is no skew",
        min=-1.0, max=1.0, default=defaults[6])
    use_scale_dis: BoolProperty(
        name="Scale displace textures",
        description="Scale displacement textures with dimensions.  May cause stretched textures",
        default=defaults[7])
    scale_fac: FloatVectorProperty(
        name="Scaling Factor",
        description="XYZ scaling factor.  1: no scaling",
        min=0.0001, max=256.0, step=0.1,
        default=defaults[8], size=3)

    # @todo Possible to title this section "Physical Properties:"?
    deform: FloatProperty(
        name="Deformation",
        description="Rock deformation",
        min=0.0, soft_max=50, max=1024.0, default=defaults[9])
    rough: FloatProperty(
        name="Roughness",
        description="Rock roughness",
        min=0.0, soft_max=50, max=1024.0, default=defaults[10])
    detail: IntProperty(
        name="Detail level",
        description="Detail level.  WARNING: Slow at high values!",
        min=1, soft_max=4, max=10, default=defaults[11])
    display_detail: IntProperty(
        name="Display Detail",
        description="Display detail.  Use a lower value for high numbers of rocks",
        min=1, soft_max=4, max=10, default=defaults[12])
    smooth_fac: FloatProperty(
        name="Smooth Factor",
        description="Smoothing factor.  A value of 0 disables",
        min=0.0, max=128.0, default=defaults[13])
    smooth_it: IntProperty(
        name="Smooth Iterations",
        description="Smoothing iterations.  A value of 0 disables",
        min=0, max=50, default=defaults[14])

    use_generate: BoolProperty(
        name="Generate Rocks",
        description="Enable actual generation",
        default=defaults[15])
    use_random_seed: BoolProperty(
        name="Use a random seed",
        description="Create a seed based on time. Causes user seed to be ignored",
        default=defaults[16])
    user_seed: IntProperty(
        name="User seed",
        description="Use a specific seed for the generator",
        min=0, max=1048576, default=defaults[17])

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, 'num_of_rocks')
        box = layout.box()
        box.prop(self, 'scale_X')
        box.prop(self, 'skew_X')
        box.prop(self, 'scale_Y')
        box.prop(self, 'skew_Y')
        box.prop(self, 'scale_Z')
        box.prop(self, 'skew_Z')
        box.prop(self, 'use_scale_dis')
        if self.use_scale_dis:
            box.prop(self, 'scale_fac')
        else:
            self.scale_fac = utils.toFloats(self.defaults[8])
        box = layout.box()
        box.prop(self, 'deform')
        box.prop(self, 'rough')
        box.prop(self, 'detail')
        box.prop(self, 'display_detail')
        box.prop(self, 'smooth_fac')
        box.prop(self, 'smooth_it')

        box = layout.box()
        box.prop(self, 'use_generate')
        box.prop(self, 'use_random_seed')
        if not self.use_random_seed:
            box.prop(self, 'user_seed')
        box.prop(self, 'preset_values')

    def execute(self, context):
        # turn off 'Enter Edit Mode'
        use_enter_edit_mode = bpy.context.preferences.edit.use_enter_edit_mode
        bpy.context.preferences.edit.use_enter_edit_mode = False

        # The following "if" block loads preset values:
        if self.lastPreset != int(self.preset_values):
            self.scale_X = utils.toFloats(self.presetsList[int(self.preset_values)][1])
            self.scale_Y = utils.toFloats(self.presetsList[int(self.preset_values)][2])
            self.scale_Z = utils.toFloats(self.presetsList[int(self.preset_values)][3])
            self.skew_X = float(self.presetsList[int(self.preset_values)][4])
            self.skew_Y = float(self.presetsList[int(self.preset_values)][5])
            self.skew_Z = float(self.presetsList[int(self.preset_values)][6])
            self.use_scale_dis = bool(self.presetsList[int(self.preset_values)][7])
            self.scale_fac = utils.toFloats(self.presetsList[int(self.preset_values)][8])
            self.deform = float(self.presetsList[int(self.preset_values)][9])
            self.rough = float(self.presetsList[int(self.preset_values)][10])
            self.detail = int(self.presetsList[int(self.preset_values)][11])
            self.display_detail = int(self.presetsList[int(self.preset_values)][12])
            self.smooth_fac = float(self.presetsList[int(self.preset_values)][13])
            self.smooth_it = int(self.presetsList[int(self.preset_values)][14])
            self.use_generate = bool(self.presetsList[int(self.preset_values)][15])
            self.use_random_seed = bool(self.presetsList[int(self.preset_values)][16])
            self.user_seed = int(self.presetsList[int(self.preset_values)][17])
            self.lastPreset = int(self.preset_values)

        # todo Add deform, deform_Var, rough, and rough_Var:
        #   *** todo completed 4/23/2011 ***
        #   *** Eliminated "deform_Var" and "rough_Var" so the script is not
        #       as complex to use.  May add in again as advanced features. ***
        if self.use_generate:
            rocks = generateRocks(context,
                          self.scale_X,
                          self.skew_X,
                          self.scale_Y,
                          self.skew_Y,
                          self.scale_Z,
                          self.skew_Z,
                          self.scale_fac,
                          self.detail,
                          self.display_detail,
                          self.deform,
                          self.rough,
                          self.smooth_fac,
                          self.smooth_it,
                          self.num_of_rocks,
                          self.user_seed,
                          self.use_scale_dis,
                          self.use_random_seed,
                          use_enter_edit_mode)

        for rock in rocks:
            rock.select_set(True)

        if use_enter_edit_mode:
            bpy.ops.object.mode_set(mode = 'EDIT')

        # restore pre operator state
        bpy.context.preferences.edit.use_enter_edit_mode = use_enter_edit_mode

        return {'FINISHED'}

# Register:
def menu_func_rocks(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(
        OBJECT_OT_add_mesh_rock.bl_idname,
        text="Rock Generator",
        icon="MESH_ICOSPHERE")


classes = (
    OBJECT_OT_add_mesh_rock,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func_rocks)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func_rocks)


if __name__ == "__main__":
    register()
