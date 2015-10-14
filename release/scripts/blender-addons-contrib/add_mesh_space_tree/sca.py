# ##### BEGIN GPL LICENSE BLOCK #####
#
#  SCA Tree Generator, a Blender addon
#  (c) 2013 Michel J. Anders (varkenvarken)
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

from collections import defaultdict as dd
from random import random, seed, expovariate
from math import sqrt, pow, sin, cos
from functools import partial

from mathutils import Vector

from .kdtree import Tree


class Branchpoint:
    def __init__(self, p, parent):
        self.v = Vector(p)
        self.parent = parent
        self.connections = 0
        self.apex = None
        self.shoot = None
        self.index = None


def sphere(r, p):
    r2 = r * r
    while True:
        x = (random() * 2 - 1) * r
        y = (random() * 2 - 1) * r
        z = (random() * 2 - 1) * r
        if x * x + y * y + z * z <= r2:
            yield p + Vector((x, y, z))


class SCA:
    def __init__(self, NENDPOINTS=100, d=0.3, NBP=2000, KILLDIST=5, INFLUENCE=15, SEED=42, volume=partial(sphere, 5, Vector((0, 0, 8))), TROPISM=0.0, exclude=lambda p: False,
        startingpoints=[]):
        seed(SEED)
        self.d = d
        self.NBP = NBP
        self.KILLDIST = KILLDIST * KILLDIST * d * d
        self.INFLUENCE = INFLUENCE * INFLUENCE * d * d
        self.TROPISM = TROPISM
        self.exclude = exclude
        self.endpoints = []

        self.volumepoint = volume()
        for i in range(NENDPOINTS):
            self.endpoints.append(next(self.volumepoint))

        self.branchpoints = [Branchpoint((0, 0, 0), None)] if len(startingpoints) == 0 else startingpoints

    def iterate(self, newendpointsper1000=0, maxtime=0.0):  # maxtime still ignored for now

        endpointsadded = 0.0
        niterations = 0.0
        newendpointsper1000 /= 1000.0
        t = expovariate(newendpointsper1000) if newendpointsper1000 > 0.0 else 1  # time to the first new 'endpoint add event'

        while self.NBP > 0 and (len(self.endpoints) > 0):
            self.NBP -= 1
            closestsendpoints = dd(list)

            kill = set()

            for ei, e in enumerate(self.endpoints):
                distance = None
                closestbp = None
                for bi, b in enumerate(self.branchpoints):
                    ddd = b.v - e
                    ddd = ddd.dot(ddd)
                    if ddd < self.KILLDIST:
                        kill.add(ei)
                    elif (ddd < self.INFLUENCE and b.shoot is None) and ((distance is None) or (ddd < distance)):
                        closestbp = bi
                        distance = ddd
                if not (closestbp is None):
                    closestsendpoints[closestbp].append(ei)

            if len(closestsendpoints) < 1:
                break

            for bi in closestsendpoints:
                sd = Vector((0, 0, 0))
                n = 0
                for ei in closestsendpoints[bi]:
                    dv = self.branchpoints[bi].v - self.endpoints[ei]
                    ll = sqrt(dv.dot(dv))
                    sd -= dv / ll
                    n += 1
                sd /= n
                ll = sqrt(sd.dot(sd))
                # don't know if this assumption is true:
                # if the unnormalised direction is very small, the endpoints are nearly coplanar/colinear and at roughly the same distance
                # so no endpoints will be killed and we might end up adding the same branch again and again
                if ll < 1e-3:
                    #print('SD very small')
                    continue

                sd /= ll
                sd[2] += self.TROPISM
                ll = sqrt(sd.dot(sd))
                sd /= ll

                newp = self.branchpoints[bi].v + sd * self.d
                # the assumption we made earlier is not suffucient to prevent adding the same branch so we need an expensive check:
                tooclose = False
                for dbi in self.branchpoints:
                    dddd = newp - dbi.v
                    if dddd.dot(dddd) < 1e-3:
                        #print('BP to close to another')
                        tooclose = True
                if tooclose:
                    continue

                if not self.exclude(newp):
                    bp = Branchpoint(newp, bi)
                    self.branchpoints.append(bp)
                    nbpi = len(self.branchpoints) - 1
                    bp = self.branchpoints[bi]
                    bp.connections += 1
                    if bp.apex is None:
                        bp.apex = nbpi
                    else:
                        bp.shoot = nbpi
                    while not (bp.parent is None):
                        bp = self.branchpoints[bp.parent]
                        bp.connections += 1

            self.endpoints = [ep for ei, ep in enumerate(self.endpoints) if not(ei in kill)]

            if newendpointsper1000 > 0.0:
                # generate new endpoints with a poisson process
                # when we first arrive here, t already hold the time to the first event
                niterations += 1
                while t < niterations:  # we keep on adding endpoints as long as the next event still happens within this iteration
                    self.endpoints.append(next(self.volumepoint))
                    endpointsadded += 1
                    t += expovariate(newendpointsper1000)  # time to new 'endpoint add event'

        #if newendpointsper1000 > 0.0:
            #print("newendpoints/iteration %.3f, actual %.3f in %5.f iterations"%(newendpointsper1000,endpointsadded/niterations,niterations))

    def iterate2(self, newendpointsper1000=0, maxtime=0.0):  # maxtime still ignored for now
        """iterate using a kdtree fr the branchpoints"""
        endpointsadded = 0.0
        niterations = 0.0
        newendpointsper1000 /= 1000.0
        t = expovariate(newendpointsper1000) if newendpointsper1000 > 0.0 else 1  # time to the first new 'endpoint add event'

        tree = Tree(3)
        for bpi, bp in enumerate(self.branchpoints):
            bp.index = bpi
            tree.insert(bp.v, bp)

        while self.NBP > 0 and (len(self.endpoints) > 0):
            self.NBP -= 1
            closestsendpoints = dd(list)

            kill = set()

            for ei, e in enumerate(self.endpoints):
                distance = None
                closestbp, distance = tree.nearest(e, checkempty=True)  # ignore forks, they have .data set to None
                if closestbp is not None:
                    if distance < self.KILLDIST:
                        kill.add(ei)
                    elif distance < self.INFLUENCE:
                        closestsendpoints[closestbp.data.index].append(ei)

            if len(closestsendpoints) < 1:
                break

            for bi in closestsendpoints:
                sd = Vector((0, 0, 0))
                n = 0
                for ei in closestsendpoints[bi]:
                    dv = self.branchpoints[bi].v - self.endpoints[ei]
                    dv.normalize()
                    sd -= dv
                    n += 1
                sd /= n
                ll = sd.length_squared
                # don't know if this assumption is true:
                # if the unnormalised direction is very small, the endpoints are nearly coplanar/colinear and at roughly the same distance
                # so no endpoints will be killed and we might end up adding the same branch again and again
                if ll < 1e-3:
                    #print('SD very small')
                    continue

                sd /= ll
                sd[2] += self.TROPISM
                sd.normalize()

                newp = self.branchpoints[bi].v + sd * self.d
                # the assumption we made earlier is not suffucient to prevent adding the same branch so we need an expensive check:
                _, dddd = tree.nearest(newp)  # no checkempty here, we want to check for forks as well
                if dddd < 1e-3:
                        #print('BP to close to another')
                        continue

                if not self.exclude(newp):
                    bp = Branchpoint(newp, bi)
                    self.branchpoints.append(bp)
                    nbpi = len(self.branchpoints) - 1
                    bp.index = nbpi
                    tree.insert(bp.v, bp)
                    bp = self.branchpoints[bi]
                    bp.connections += 1
                    if bp.apex is None:
                        bp.apex = nbpi
                    else:
                        bp.shoot = nbpi
                        node, _ = tree.nearest(bp.v)
                        node.data = None  # signal that this is a fork so that we might ignore it when searching for nearest neighbors
                    while not (bp.parent is None):
                        bp = self.branchpoints[bp.parent]
                        bp.connections += 1

            self.endpoints = [ep for ei, ep in enumerate(self.endpoints) if not(ei in kill)]

            if newendpointsper1000 > 0.0:
                # generate new endpoints with a poisson process
                # when we first arrive here, t already hold the time to the first event
                niterations += 1
                while t < niterations:  # we keep on adding endpoints as long as the next event still happens within this iteration
                    self.endpoints.append(next(self.volumepoint))
                    endpointsadded += 1
                    t += expovariate(newendpointsper1000)  # time to new 'endpoint add event'
