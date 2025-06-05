# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Converts a formatted string to a float tuple:
#   IN - '(0.5, 0.2)' -> CONVERT -> OUT - (0.5, 0.2)
def toTuple(stringIn):
    sTemp = str(stringIn)[1:len(str(stringIn)) - 1].split(', ')
    fTemp = []
    for i in sTemp:
        fTemp.append(float(i))
    return tuple(fTemp)


# Converts a formatted string to a float tuple:
#   IN - '[0.5, 0.2]' -> CONVERT -> OUT - [0.5, 0.2]
def toList(stringIn):
    sTemp = str(stringIn)[1:len(str(stringIn)) - 1].split(', ')
    fTemp = []
    for i in sTemp:
        fTemp.append(float(i))
    return fTemp


# Converts each item of a list into a float:
def toFloats(inList):
    outList = []
    for i in inList:
        outList.append(float(i))
    return outList


# Converts each item of a list into an integer:
def toInts(inList):
    outList = []
    for i in inList:
        outList.append(int(i))
    return outList


# Sets all faces smooth.  Done this way since I can't
# find a simple way without using bpy.ops:
def smooth(mesh):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(mesh)
    return mesh


# This try block allows for the script to psudo-intelligently select the
# appropriate random to use.  If Numpy's random is present it will use that.
# If Numpy's random is not present, it will through a "module not found"
# exception and instead use the slower built-in random that Python has.
try:
    # from numpy.random import random_integers as randint
    from numpy.random import normal as gauss
    # from numpy.random import (beta,
    # uniform,
    # seed,
    # weibull)
    # print("Rock Generator: Numpy found.")
    numpy = True
except:
    from random import (
        # randint,
        gauss,
        # uniform,
        # seed
        )
    # from random import betavariate as beta
    # from random import weibullvariate as weibull
    print("Rock Generator: Numpy not found.  Using Python's random.")
    numpy = False
# Artificially skews a normal (gaussian) distribution.  This will not create
# a continuous distribution curve but instead acts as a piecewise finction.
# This linearly scales the output on one side to fit the bounds.
#
# Example output histograms:
#
# Upper skewed:                 Lower skewed:
#  |                 ▄           |      _
#  |                 █           |      █
#  |                 █_          |      █
#  |                 ██          |     _█
#  |                _██          |     ██
#  |              _▄███_         |     ██ _
#  |             ▄██████         |    ▄██▄█▄_
#  |          _█▄███████         |    ███████
#  |         _██████████_        |   ████████▄▄█_ _
#  |      _▄▄████████████        |   ████████████▄█_
#  | _▄_ ▄███████████████▄_      | _▄███████████████▄▄_
#   -------------------------     -----------------------
#                    |mu               |mu
#   Histograms were generated in R (http://www.r-project.org/) based on the
#   calculations below and manually duplicated here.
#
# param:  mu          - mu is the mean of the distribution.
#         sigma       - sigma is the standard deviation of the distribution.
#         bounds      - bounds[0] is the lower bound and bounds[1]
#                       is the upper bound.
#         upperSkewed - if the distribution is upper skewed.
# return: out         - Rondomly generated value from the skewed distribution.
#
# @todo: Because NumPy's random value generators are faster when called
#   a bunch of times at once, maybe allow this to generate and return
#   multiple values at once?


def skewedGauss(mu, sigma, bounds, upperSkewed=True):
    raw = gauss(mu, sigma)

    # Quicker to check an extra condition than do unnecessary math. . . .
    if raw < mu and not upperSkewed:
        out = ((mu - bounds[0]) / (3 * sigma)) * raw + ((mu * (bounds[0] - (mu - 3 * sigma))) / (3 * sigma))
    elif raw > mu and upperSkewed:
        out = ((mu - bounds[1]) / (3 * -sigma)) * raw + ((mu * (bounds[1] - (mu + 3 * sigma))) / (3 * -sigma))
    else:
        out = raw

    return out


# @todo create a def for generating an alpha and beta for a beta distribution
#   given a mu, sigma, and an upper and lower bound.  This proved faster in
#   profiling in addition to providing a much better distribution curve
#   provided multiple iterations happen within this function; otherwise it was
#   slower.
#   This might be a scratch because of the bounds placed on mu and sigma:
#
#   For alpha > 1 and beta > 1:
#   mu^2 - mu^3           mu^3 - mu^2 + mu
#   ----------- < sigma < ----------------
#      1 + mu                  2 - mu
#
# def generateBeta(mu, sigma, scale, repitions=1):
    # results = []
#
    # return results
