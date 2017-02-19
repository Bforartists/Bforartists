# ##### BEGIN GPL LICENSE BLOCK #####
#
#  SCA Tree Generator, a Blender addon
#  (c) 2013 Michel J. Anders (varkenvarken)
#
#  This module is: kdtree.py
#  a pure python implementation of a kdtree
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

from copy import copy, deepcopy


class Hyperrectangle:
    '''an axis aligned bounding box of arbitrary dimension'''

    def __init__(self, dim, min, max):
        self.dim = dim
        self.min = deepcopy(min)  # min and max should never point to the same instance
        self.max = deepcopy(max)

    def extend(self, pos):
        '''adapt the hyperectangle if necessary so it will contain pos.'''
        for i in range(self.dim):
            if pos[i] < self.min[i]:
                self.min[i] = pos[i]
            elif pos[i] > self.max[i]:
                self.max[i] = pos[i]

    def distance_squared(self, pos):
        '''return the distance squared to the nearest edge, or zero if pos lies within the hyperrectangle'''
        result = 0.0
        for i in range(self.dim):
            if pos[i] < self.min[i]:
                result += (pos[i] - self.min[i]) ** 2
            elif pos[i] > self.max[i]:
                result += (pos[i] - self.max[i]) ** 2
        return result

    def __str__(self):
        return "[(%d) %s:%s]" % (int(self.dim), str(self.min), str(self.max))


class Node:
    """implements a node in a kd-tree"""

    def __init__(self, pos, data=None):
        self.pos = deepcopy(pos)
        self.data = data
        self.left = None
        self.right = None
        self.dim = len(pos)
        self.dir = 0
        self.count = 0
        self.level = 0
        self.rect = Hyperrectangle(self.dim, pos, pos)

    def addleft(self, node):
        self.left = node
        self.rect.extend(node.pos)
        node.level = self.level + 1
        node.dir = (self.dir + 1) % self.dim

    def addright(self, node):
        self.right = node
        self.rect.extend(node.pos)
        node.level = self.level + 1
        node.dir = (self.dir + 1) % self.dim

    def distance_squared(self, pos):
        d = self.pos - pos
        return d.dot(d)

    def _str(self, level):
        s = '  ' * level + str(self.dir) + ' ' + str(self.pos) + ' ' + str(self.rect) + '\n'
        return s + ('' if self.left is None else 'L:' + self.left._str(level + 1)) + ('' if self.right is None else 'R:' + self.right._str(level + 1))

    def __str__(self):
        return self._str(0)


class Tree:
    """implements a kd-tree"""

    def __init__(self, dim):
        self.root = None
        self.nnearest = 0  # number of nearest neighbor queries
        self.count = 0  # number of nodes visited
        self.level = 0  # deepest node level

    def resetcounters(self):
        self.nnearest = 0  # number of nearest neighbor queries
        self.count = 0  # number of nodes visited

    def _insert(self, node, pos, data):
        if pos[node.dir] < node.pos[node.dir]:
            if node.left is None:
                node.addleft(Node(pos, data))
                return node.left
            else:
                node.rect.extend(pos)
                return self._insert(node.left, pos, data)
        else:
            if node.right is None:
                node.addright(Node(pos, data))
                return node.right
            else:
                node.rect.extend(pos)
                return self._insert(node.right, pos, data)

    def insert(self, pos, data):
        if self.root is None:
            self.root = Node(pos, data)
            self.level = self.root.level
            return self.root
        else:
            node = self._insert(self.root, pos, data)
            if node.level > self.level:
                self.level = node.level
            return node

    def _nearest(self, node, pos, checkempty, level=0):

        self.count += 1

        dir = node.dir
        d = pos[dir] - node.pos[dir]

        result = node
        distsq = None
        if checkempty and (node.data is None):
            result = None
        else:
            distsq = node.distance_squared(pos)

        if d <= 0:
            neartree = node.left
            fartree = node.right
        else:
            neartree = node.right
            fartree = node.left

        if neartree is not None:
            nearnode, neardistsq = self._nearest(neartree, pos, checkempty, level + 1)
            if (result is None) or (neardistsq is not None and neardistsq < distsq):
                result, distsq = nearnode, neardistsq

        if fartree is not None:
            if (result is None) or (fartree.rect.distance_squared(pos) < distsq):
                farnode, fardistsq = self._nearest(fartree, pos, checkempty, level + 1)
                if (result is None) or (fardistsq is not None and fardistsq < distsq):
                    result, distsq = farnode, fardistsq

        return result, distsq

    def nearest(self, pos, checkempty=False):
        self.nnearest += 1
        if self.root is None:
            return None, None
        self.root.count = 0
        node, distsq = self._nearest(self.root, pos, checkempty)
        self.count += self.root.count
        return node, distsq

    def __str__(self):
        return str(self.root)

if __name__ == "__main__":

    class vector(list):

        def __init__(self, *args):
            super().__init__([float(a) for a in args])

        def __str__(self):
            return "<%.1f %.1f %.1f>" % tuple(self[0:3])

        def __sub__(self, other):
            return vector(self[0] - other[0], self[1] - other[1], self[2] - other[2])

        def __add__(self, other):
            return vector(self[0] + other[0], self[1] + other[1], self[2] + other[2])

        def __mul__(self, other):
            s = sum(self[i] * other[i] for i in (0, 1, 2))
            #print("ds",s,self,other,[self[i]*other[i] for i in (0,1,2)])
            return s

        def dot(self, other):
            return sum(self[k] * other[k] for k in (0, 1, 2))

    from random import random, seed, shuffle
    from time import time
    import unittest

    class TestVector(unittest.TestCase):
        def test_ops(self):
            v1 = vector(1, 0, 0)
            v2 = vector(2, 1, 0)
            self.assertAlmostEqual(v1 * v2, 2.0)
            self.assertAlmostEqual(v1.dot(v2), 2.0)
            v3 = vector(-1, -1, 0)
            self.assertListEqual(v1 - v2, v3)
            v4 = vector(3, 1, 0)
            self.assertListEqual(v1 + v2, v4)

    class TestHyperRectangle(unittest.TestCase):

        def setUp(self):
            self.left = vector(0, 0, 0)
            self.right = vector(1, 1, 1)
            self.left1 = vector(-1, 0, 0)
            self.left2 = vector(0, -1, 0)
            self.left3 = vector(0, 0, -1)
            self.right1 = vector(2, 0, 0)
            self.right2 = vector(0, 2, 0)
            self.right3 = vector(0, 0, 2)

        def test_constructor(self):
            hr = Hyperrectangle(3, self.left, self.right)
            self.assertListEqual(hr.min, self.left)
            self.assertListEqual(hr.max, self.right)

        def test_extend(self):
            hr = Hyperrectangle(3, self.left, self.right)
            hr.extend(self.left1)
            self.assertListEqual(hr.min, [-1, 0, 0])
            self.assertListEqual(hr.max, [1, 1, 1])
            hr.extend(self.left2)
            self.assertListEqual(hr.min, [-1, -1, 0])
            self.assertListEqual(hr.max, [1, 1, 1])
            hr.extend(self.left3)
            self.assertListEqual(hr.min, [-1, -1, -1])
            self.assertListEqual(hr.max, [1, 1, 1])
            hr.extend(self.right1)
            self.assertListEqual(hr.min, [-1, -1, -1])
            self.assertListEqual(hr.max, [2, 1, 1])
            hr.extend(self.right2)
            self.assertListEqual(hr.min, [-1, -1, -1])
            self.assertListEqual(hr.max, [2, 2, 1])
            hr.extend(self.right3)
            self.assertListEqual(hr.min, [-1, -1, -1])
            self.assertListEqual(hr.max, [2, 2, 2])

        def test_distance_squared(self):
            hr = Hyperrectangle(3, self.left, self.right)
            self.assertAlmostEqual(hr.distance_squared(vector(0.5, 0.5, 0.5)), 0.0)
            self.assertAlmostEqual(hr.distance_squared(vector(0, 0, 0)), 0.0)
            self.assertAlmostEqual(hr.distance_squared(vector(-1, 0, 0)), 1.0)
            self.assertAlmostEqual(hr.distance_squared(vector(2, 0, 0)), 1.0)
            self.assertAlmostEqual(hr.distance_squared(vector(2, 2, 2)), 3.0)
            self.assertAlmostEqual(hr.distance_squared(vector(0.5, 2, 2)), 2.0)
            self.assertAlmostEqual(hr.distance_squared(vector(0.5, -1, -1)), 2.0)
            self.assertAlmostEqual(hr.distance_squared(vector(0.5, 0.5, 2)), 1.0)

    class TestTree(unittest.TestCase):

        def setUp(self):
            seed(42)
            r = (-1, 0, 1)
            self.points = [vector(k, l, m) for k in r for l in r for m in r]
            d = (-0.1, 0, 0.1)
            self.d = [vector(k, l, m) for k in d for l in d for m in d if (k * l * m) != 0]
            self.repeats = 4

        def test_simple(self):
            tree = Tree(3)
            p1 = vector(0, 0, 0)
            p2 = vector(-1, 0, 0)
            p3 = vector(-1, 1, 0)
            d = vector(0.1, 0.1, 0.1)

            tree.insert(p1, p1)
            node, distsq = tree.nearest(p1)
            self.assertListEqual(node.pos, p1)
            self.assertAlmostEqual(distsq, 0.0)
            node, distsq = tree.nearest(p1 + d)
            self.assertListEqual(node.pos, p1)
            self.assertAlmostEqual(distsq, 0.03)

            tree.insert(p2, p2)
            node, distsq = tree.nearest(p1)
            self.assertListEqual(node.pos, p1)
            self.assertAlmostEqual(distsq, 0.0)
            node, distsq = tree.nearest(p1 + d)
            self.assertListEqual(node.pos, p1)
            self.assertAlmostEqual(distsq, 0.03)

            node, distsq = tree.nearest(p2)
            self.assertListEqual(node.pos, p2)
            self.assertAlmostEqual(distsq, 0.0)
            node, distsq = tree.nearest(p2 + d)
            self.assertListEqual(node.pos, p2)
            self.assertAlmostEqual(distsq, 0.03)

            tree.insert(p3, p3)
            node, distsq = tree.nearest(p1)
            self.assertListEqual(node.pos, p1)
            self.assertAlmostEqual(distsq, 0.0)
            node, distsq = tree.nearest(p1 + d)
            self.assertListEqual(node.pos, p1)
            self.assertAlmostEqual(distsq, 0.03)

            node, distsq = tree.nearest(p2)
            self.assertListEqual(node.pos, p2)
            self.assertAlmostEqual(distsq, 0.0)
            node, distsq = tree.nearest(p2 + d)
            self.assertListEqual(node.pos, p2)
            self.assertAlmostEqual(distsq, 0.03)

            node, distsq = tree.nearest(p3)
            self.assertListEqual(node.pos, p3)
            self.assertAlmostEqual(distsq, 0.0)
            node, distsq = tree.nearest(p3 + d)
            self.assertListEqual(node.pos, p3)
            self.assertAlmostEqual(distsq, 0.03)

        def test_nearest(self):
            for n in range(self.repeats):
                tree = Tree(3)
                shuffle(self.points)
                for p in self.points:
                    tree.insert(p, p)  # data equal to position

                for p in self.points:
                    for d in self.d:
                        node, distsq = tree.nearest(p + d)
                        s = "%s %s %s %s\n%s" % (str(p + d), str(p), str(d), str(node.pos), str(tree.root))
                        self.assertListEqual(node.pos, p, msg=s)
                        self.assertListEqual(node.data, p)
                        self.assertAlmostEqual(distsq, d.dot(d), msg=s)

                for p in self.points:
                    node, distsq = tree.nearest(p)
                    self.assertListEqual(node.pos, p)
                    self.assertListEqual(node.data, p)
                    self.assertAlmostEqual(distsq, 0.0)

        def test_nearest_empty(self):
            for n in range(self.repeats):
                tree = Tree(3)
                shuffle(self.points)
                for p in self.points:
                    tree.insert(p, p)  # data equal to position

                for p in self.points:
                    for d in self.d:
                        node, distsq = tree.nearest(p + d)
                        s = "%s %s %s %s\n%s" % (str(p + d), str(p), str(d), str(node.pos), str(tree.root))
                        self.assertListEqual(node.pos, p, msg=s)
                        self.assertListEqual(node.data, p)
                        self.assertAlmostEqual(distsq, d.dot(d), msg=s)

                for p in self.points:
                    node, distsq = tree.nearest(p)
                    self.assertListEqual(node.pos, p)
                    self.assertListEqual(node.data, p)
                    self.assertAlmostEqual(distsq, 0.0)

                # zeroing out a node should not affect retrieving any other node ...
                node, _ = tree.nearest(self.points[-1])  # last point
                node.data = None
                for p in self.points[:-1]:  # all but last
                    for d in self.d:
                        node, distsq = tree.nearest(p + d)
                        s = "%s %s %s %s\n%s" % (str(p + d), str(p), str(d), str(node.pos), str(tree.root))
                        self.assertListEqual(node.pos, p, msg=s)
                        self.assertListEqual(node.data, p)
                        self.assertAlmostEqual(distsq, d.dot(d), msg=s)

                for p in self.points[:-1]:  # all but last
                    node, distsq = tree.nearest(p)
                    self.assertListEqual(node.pos, p)
                    self.assertListEqual(node.data, p)
                    self.assertAlmostEqual(distsq, 0.0)

                # ... also, we should be able to retrieve the node anyway ...
                node, distsq = tree.nearest(self.points[-1])
                self.assertListEqual(node.pos, self.points[-1])
                self.assertIsNone(node.data)
                self.assertAlmostEqual(distsq, 0.0)

                # ... even for points nearby ...
                for d in self.d:
                    node, distsq = tree.nearest(self.points[-1] + d)
                    self.assertEqual(node.pos, self.points[-1])
                    self.assertIsNone(node.data)
                    self.assertAlmostEqual(distsq, d.dot(d))

                # ... unless we set checkempty
                node, distsq = tree.nearest(self.points[-1], checkempty=True)
                self.assertNotEqual(node.pos, self.points[-1])
                self.assertIsNotNone(node.data)
                self.assertAlmostEqual(distsq, 1.0)  # on a perpendicular grid nearest neighbor is at most 1 away

        def test_performance(self):
            tree = Tree(3)
            tsize = 1000
            qsize = 1000
            emptyq = 3

            print("<performance test, may take several seconds>")
            qpos = [vector(random(), random(), random()) for p in range(qsize)]
            for p in range(tsize):
                pos = vector(random(), random(), random())
                tree.insert(pos, pos)
            s = time()
            for p in qpos:
                node, distsq = tree.nearest(p)
            e = time() - s
            print("queries|tree size|tree height|empties|query load|query time")
            print("{0:7d}|{2:9d}|{1.level:11d}|      0|{3:10.2f}|{4:10.1f}".format(qsize, tree, tsize, float(tree.count) / qsize, e))

            tree.resetcounters()
            empty = []
            for p in range(tsize * 9):
                pos = vector(random(), random(), random())
                tree.insert(pos, pos)
                if (p % emptyq) == 1:
                    empty.append(pos)
            s = time()
            for p in qpos:
                node, distsq = tree.nearest(p)
            e2 = time() - s
            print("{0:7d}|{2:9d}|{1.level:11d}|      0|{3:10.2f}|{4:10.1f}".format(qsize, tree, tsize * 10, float(tree.count) / qsize, e2))

            self.assertLess(e2, 3 * e, msg="a 10x bigger tree shouldn't take more than 3x the time to query")

            for p in empty:
                node, distsq = tree.nearest(p)
                node.data = None
            tree.resetcounters()
            s = time()
            for p in qpos:
                node, distsq = tree.nearest(p, checkempty=True)
            e3 = time() - s
            print("{0:7d}|{2:9d}|{1.level:11d}|{5:7d}|{3:10.2f}|{4:10.1f}".format(qsize, tree, tsize * 10, float(tree.count) / qsize, e3, tsize * 10 // emptyq))

    unittest.main()
