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

"""Convert an Art object to a list of PolyArea objects.
"""

__author__ = "howard.trickey@gmail.com"

import math
from . import geom
from . import vecfile
import itertools


class ConvertOptions(object):
    """Contains options used to control art to poly conversion.

    Attributes:
      subdiv_kind: int - one of a few 'enum' strings:
          'UNIFORM' - all curves subdivided the same amount
          'ADAPTIVE' - curves subdivided until flat enough
          'EVEN' - curves subdivided to make segments of uniform length
      smoothness: int - controls smoothness of curve conversion:
        usage depends on subdiv_kind:
          'UNIFORM': number of times to subdivide
          'ADAPTIVE': if subdivide a quarter circle bezier this many times,
            then that is the definition of 'flat enough'
          'EVEN': proportional to 1/uniform-length-of-segments
            (so higher numbers mean shorter segments)

      filled_only: bool - look only at filled faces
      combine_paths: bool - use union of all subpaths to find
        boundaries and holes instead of just looking for compound
        paths in the input file
      ignore_white: bool - ignore white-filled paths (background, probably)
    """

    def __init__(self):
        self.subdiv_kind = "UNIFORM"
        self.smoothness = 1
        self.filled_only = True
        self.combine_paths = False
        self.ignore_white = True


def ArtToPolyAreas(art, options):
    """Convert Art object to PolyAreas.

    Each filled Path in the Art object will produce zero
    or more PolyAreas.  If options.filled_only is False, then stroked paths
    produce PolyAreas too.

    If options.ignore_white is True, we assume that white is the background
    color and not intended to produce polyareas (for example, sometimes there
    is a filled background rectangle for the entire page).

    If options.combine_paths is True, use the union of all subpaths of all
    Paths to look for outer boundaries and holes, else just look insdie each
    Path separately.

    Args:
      art: geom.Art - contains Paths to convert
      options: ConvertOptions
    Returns:
      geom.PolyAreas
    """

    ans = geom.PolyAreas()
    paths_to_convert = art.paths
    if options.filled_only:
        paths_to_convert = [p for p in paths_to_convert if p.filled]
    if options.ignore_white:
        paths_to_convert = [p for p in paths_to_convert \
            if p.fillpaint != geom.white_paint]
    # TODO: look for dup paths (both filled and stroked) and dedup
    # TODO (perhaps): look for a 'background rectangle' and remove
    if options.subdiv_kind == "EVEN":
        _SetEvenLength(options, paths_to_convert)
    if options.combine_paths:
        combinedpath = geom.Path()
        combinedpath.subpaths = _flatten([p.subpaths \
            for p in paths_to_convert])
        areas = PathToPolyAreas(combinedpath, options, ans.points)
    else:
        areas = _flatten([PathToPolyAreas(p, options, ans.points) \
            for p in paths_to_convert])
    ans.polyareas.extend(areas)
    return ans


def PathToPolyAreas(path, options, points):
    """Convert Path object to list of PolyArea, sharing points.

    Like ArtToPolyAreas, but for a single Path in Art.

    Usually only one PolyArea will be in the returned list,
    but there may be zero if the path has zero area,
    and there may be more than one if it contains
    non-overlapping polygons.
    (TODO: or if it self-crosses)

    Args:
      path: geom.Path - the path to convert
      options: ConvertOptions
      points: geom.Points - use this shared points for all areas
    Returns:
      list of geom.PolyArea
    """

    subpolyareas = [
        _SubpathToPolyArea(sp, options, points, path.fillpaint.color) \
        for sp in path.subpaths]
    subpolyareas = [pa for pa in subpolyareas if len(pa.poly) > 0]
    return CombineSimplePolyAreas(subpolyareas)


def CombineSimplePolyAreas(subpolyareas):
    """Combine PolyAreas without holes into ones that may have holes.

    Take the poly's in each argument PolyArea and find those that
    are contained in others, so returning a list of PolyAreas that may
    contain holes.
    The argument PolyAreas may be reused an modified in forming
    the result.

    Args:
      subpolyareas: list of geom.PolyArea
    Returns:
      list of geom.PolyArea
    """

    n = len(subpolyareas)
    areas = [geom.SignedArea(pa.poly, pa.points) for pa in subpolyareas]
    lens = list(map(lambda x: len(x.poly), subpolyareas))
    cls = dict()
    for i in range(n):
        for j in range(n):
            cls[(i, j)] = _ClassifyPathPairs(subpolyareas[i], subpolyareas[j])
    # calculate set cont where (i,j) is in cont if
    # subpolyareas[i] contains subpolyareas[j]
    cont = set()
    for i in range(n):
        for j in range(n):
            if i != j and _Contains(i, j, areas, lens, cls):
                cont.add((i, j))
    # now make real PolyAreas, with holes assigned
    polyareas = []
    assigned = set()
    count = 0
    while len(assigned) < n and count < n:
        for i in range(n):
            if i in assigned:
                continue
            if _IsBoundary(i, n, cont, assigned):
                # have a new boundary area, i
                assigned.add(i)
                holes = _GetHoles(i, n, cont, assigned)
                pa = subpolyareas[i]
                for j in holes:
                    pa.AddHole(subpolyareas[j])
                polyareas.append(pa)
        count += 1
    if len(assigned) < n:
        # shouldn't happen
        print("Whoops, PathToPolyAreas didn't assign all")
    return polyareas


def _SubpathToPolyArea(subpath, options, points, color=(0.0, 0.0, 0.0)):
    """Return a PolyArea representing a single subpath.

    Converts curved segments into approximating line
    segments.
    For 'EVEN' subdiv_kind, divides lines too.
    Ignores zero-length or near zero-length segments.
    Ensures that face is CCW-oriented.
    Use the data field of the PolyArea to hold the filling color.

    Args:
      subpath: geom.Subpath - the subpath to convert
      options: ConvertOptions
      points: geom.Points - used this shared Points for area
      color: (float, float, float) - rgb of filling color
    Returns:
      geom.PolyArea
    """

    face = []
    prev = None
    ans = geom.PolyArea()
    ans.points = points
    ans.data = color
    for seg in subpath.segments:
        (ty, start, end) = seg[0:3]
        if not prev or prev != start:
            face.append(start)
        if ty == "L":
            if options.subdiv_kind == "EVEN":
                lines = _EvenLineDivide(start, end, options)
                face.extend(lines[1:])
            else:
                face.append(end)
            prev = end
        elif ty == "B":
            approx = Bezier3Approx([start, seg[3], seg[4], end], options)
            # first point of approx should be current end of face
            face.extend(approx[1:])
            prev = end
        elif ty == "Q":
            print("unimplemented segment type Q")
        elif ty == "A":
            approx = ArcApprox(start, end, seg[3], seg[4], seg[5], seg[6],
                options)
            face.extend(approx[1:])
            prev = end
        else:
            print("unexpected segment type", ty)
    # now make a cleaned face in a new PolyArea
    # with no two successive points approximately equal
    if len(face) <= 2:
        # degenerate face, return an empty PolyArea
        return ans
    previndex = -1
    for i in range(0, len(face)):
        point = face[i]
        newindex = ans.points.AddPoint(point)
        if newindex == previndex or \
            i == len(face) - 1 and newindex == ans.poly[0]:
            continue
        ans.poly.append(newindex)
        previndex = newindex
    # make sure that face is CCW oriented
    if geom.SignedArea(ans.poly, ans.points) < 0.0:
        ans.poly.reverse()
    return ans


def Bezier3Approx(cps, options):
    """Compute a polygonal approximation to a cubic bezier segment.

    Args:
      cps: list of 4 coord tuples -
          (start, control point 1, control point 2, end)
      options: ConvertOptions
    Returns:
      list of tuples (coordinates) for straight line approximation of the
      bezier
    """

    if options.subdiv_kind == "EVEN":
        return _EvenBezier3Approx(cps, options)
    else:
        return _SubdivideBezier3Approx(cps, options, 0)


def _SetEvenLength(options, paths):
    """Use the bounding box of paths to set even_length in options.

    We want the option.smoothness parameter to control the length
    of segments that we will try to divide Bezier curves into when
    using the EVEN method.  More smoothness -> shorter length.
    But the user should think of this in terms of the overall dimensions
    of their diagram, not in absolute terms.
    Let's say that smoothness==0 means the length should 1/4 the
    size of the longest size of the bounding box, and, for general
    smoothness:

                    longest_side_length
      even_length = -------------------
                    4 * (smoothness+1)

    Args:
      options: ConvertOptions
      paths: list of geom.Path
    Side effects:
      Sets options.even_length according to above formula
    """

    minx = 1e10
    maxx = -1e10
    miny = 1e10
    maxy = -1e10
    for p in paths:
        for sp in p.subpaths:
            for seg in sp.segments:
                endi = 3 if seg[0] == 'A' else len(seg)
                for (x, y) in seg[1:endi]:
                    minx = min(minx, x)
                    maxx = max(maxx, x)
                    miny = min(miny, y)
                    maxy = max(maxy, y)
    longest_side_length = max(maxx - minx, maxy - miny)
    if longest_side_length <= 0:
        longest_side_length = 1.0
    options.even_length = longest_side_length / \
        (4.0 * (options.smoothness + 1))


def _EvenBezier3Approx(cps, options):
    """Use even segment lengths to approximate a cubic bezier segment.

    Args:
      cps: list of 4 coord tuples -
          (start, control point 1, control point 2, end)
      options: ConvertOptions
    Returns:
      list of tuples (coordinates) for straight line approximation of the
      bezier
    """

    # This could be made better by recursing a couple of times
    # but the average of the control polygon and chord length is a good
    # first order approximation.
    arc_length = 0.5 * (geom.VecLen(geom.VecSub(cps[3], cps[0])) + \
                 0.5 * (geom.VecLen(geom.VecSub(cps[1], cps[0])) + \
                        geom.VecLen(geom.VecSub(cps[2], cps[1])) + \
                        geom.VecLen(geom.VecSub(cps[3], cps[2]))))
    # make sure segment lengths are at least as short as even_length
    numsegs = math.ceil(arc_length / options.even_length)
    # unless smoothness is zero, make sure Beziers split at least once
    if options.smoothness > 0 and numsegs == 1:
        numsegs = 2
    ans = [cps[0]]
    for i in range(1, numsegs):
        t = i * (1.0 / numsegs)
        pt = _BezierEval(cps, t)
        ans.append(pt)
    ans.append(cps[3])
    return ans


def _BezierEval(cps, t):
    """Evaluate a cubic Bezier at parameter t.

    Args:
      cps: list of 4 coord tuples -
          (start, control point 1, control point 2, end)
      t: float - parameter (0 -> start, 1 -> end)
    Returns:
      tuple (coordinates) of point at parameter t along the curve
    """

    b1 = _Bez3step(cps, 1, t)
    b2 = _Bez3step(b1, 2, t)
    b3 = _Bez3step(b2, 3, t)
    return b3[0]


def _EvenLineDivide(start, end, options):
    """Like _EvenBezier3Approx, but for line segments.

    Args:
      start: tuple - coords of start point
      end: tuple - coords of end point
      options: ConvertOptions
    Returns:
      list of tuples (coordinates) for pieces of lines.
    """

    line_length = geom.VecLen(geom.VecSub(end, start))
    numsegs = math.ceil(line_length / options.even_length)
    ans = [start]
    for i in range(1, numsegs):
        t = i * (1.0 / numsegs)
        pt = _LinInterp(start, end, t)
        ans.append(pt)
    ans.append(end)
    return ans


def _LinInterp(a, b, t):
    """Return the point that is t of the way from a to b.

    Args:
      a: tuple - coords of start point
      b: tuple - coords of end point
      t: float - interpolation parameter
    Returns:
      tuple (coordinates)
    """

    n = len(a)  # dimension of coordinates
    ans = [0.0] * n
    for i in range(n):
        ans[i] = (1.0 - t) * a[i] + t * b[i]
    return tuple(ans)


# These ratios chosen so that a 4-bezier approximation
# to a circle gets subdivided 0, 1, 2, etc. times
# when using 'adaptive'.
adaptive_ratios = [1.2286, 1.0531, 1.0136, 1.0124, 1.0030, 1.0007]


def _SubdivideBezier3Approx(cps, options, recurse_count):
    """Use successive bisection to approximate a cubic bezier segment.

    Args:
      cps: list of 4 coord tuples -
          (start, control point 1, control point 2, end)
      options: ConvertOptions
      recurse_count: int - how deep have we recursed so far
    Returns:
      list of tuples (coordinates) for straight line approximation of
      the bezier
    """

    (vs, _, _, ve) = b0 = cps
    subdivide_num = options.smoothness
    adaptive = (options.subdiv_kind == "ADAPTIVE")
    if recurse_count >= subdivide_num and not adaptive:
        return [vs, ve]
    alpha = 0.5
    b1 = _Bez3step(b0, 1, alpha)
    b2 = _Bez3step(b1, 2, alpha)
    b3 = _Bez3step(b2, 3, alpha)
    if adaptive:
        straightlen = geom.VecLen(geom.VecSub(ve, vs))
        if straightlen < geom.DISTTOL:
            return [vs, ve]
        approxcurvelen = \
          geom.VecLen(geom.VecSub(cps[1], cps[0])) + \
          geom.VecLen(geom.VecSub(cps[2], cps[1])) + \
          geom.VecLen(geom.VecSub(cps[3], cps[2]))
        ratio = approxcurvelen / straightlen
        if subdivide_num < 0:
            subdivide_num = 0
        elif subdivide_num >= len(adaptive_ratios):
            subdivide_num = len(adaptive_ratios) - 1
        aratio = adaptive_ratios[subdivide_num]
        if ratio <= aratio:
            return [vs, ve]
    else:
        if subdivide_num - recurse_count == 1:
            # recursive case would do this too, but optimize a bit
            return [vs, b3[0], ve]
    left = [b0[0], b1[0], b2[0], b3[0]]
    right = [b3[0], b2[1], b1[2], b0[3]]
    ansleft = _SubdivideBezier3Approx(left, options, recurse_count + 1)
    ansright = _SubdivideBezier3Approx(right, options, recurse_count + 1)
    # ansleft ends with b3[0] and ansright starts with it
    return ansleft + ansright[1:]


def _Bez3step(b, r, alpha):
    """Cubic bezier step r for interpolating at parameter alpha.

    Steps 1, 2, 3 are applied in succession to the 4 points
    representing a bezier segment, making a triangular arrangement
    of interpolating the previous step's output, so that after
    step 3 we have the point that is at parameter alpha of the segment.
    The left-half control points will be on the left side of the triangle
    and the right-half control points will be on the right side of the
    triangle.

    Args:
      b: list of tuples (coordinates), of length 5-r
      r: int - step number (0=orig points and cps)
      alpha: float - value in range 0..1 where want to divide at
    Returns:
      list of length 4-r, of vertex coordinates, giving linear interpolations
          at parameter alpha between successive pairs of points in b
    """

    ans = []
    n = len(b[0])  # dimension of coordinates
    beta = 1 - alpha
    for i in range(0, 4 - r):
        # find c, alpha of the way from b[i] to b[i+1]
        t = [0.0] * n
        for d in range(n):
            t[d] = b[i][d] * beta + b[i + 1][d] * alpha
        ans.append(tuple(t))
    return ans


def ArcApprox(start, end, rad, xrot, large_arc, ccw, options):
    """Approximate an elliptical arc with line segments, according to options.

    Implementation follows notes in F.6 of SVG spec.

    Args:
      start: (float, float) - starting point
      end: (float, float) - ending point
      rad: (float, float) - x-radius, y-radius
      xrot: float - angle of rotation from x-axis, in degrees
      large_arc: bool - should we take a larger arc?
      ccw: bool - does arc proceed counter-clockwise?
      options: ConvertOptions
    Returns:
      list of tuples (coordinates) for straight line approximation of arc
    """

    if start == end:
        return [start]
    (rx, ry) = rad
    if rx == 0.0 or ry == 0.0:
        # treat same as line
        if options.subdiv_kind == "EVEN":
            return _EvenLineDivide(start, end, options)
        else:
            return [start, end]
    rx = abs(rx)
    ry = abs(ry)
    (x1, y1) = start
    (x2, y2) = end

    # Convert to center parameterization.
    # Primed coords: origin at midpoint of (start, end)
    # followed by rotaiton to line up coord axes with ellipse axes
    x1p = (x1 - x2) / 2.0
    y1p = (y1 - y2) / 2.0
    phi = xrot * math.pi / 180.0
    cos_phi = math.cos(phi)
    sin_phi = math.sin(phi)
    (x1p, y1p) = (cos_phi * x1p + sin_phi * y1p, \
        -sin_phi * x1p + cos_phi * y1p)
    # perhaps scale up rx, ry to make ellipse achievable
    lam = (x1p ** 2) / rx ** 2 + (y1p ** 2) / ry ** 2
    if lam > 1.0:
        slam = math.sqrt(lam)
        rx *= slam
        ry *= slam
    cf2 = (rx ** 2 * ry ** 2 - rx ** 2 * y1p ** 2 - ry ** 2 * x1p ** 2) / \
        (rx ** 2 * y1p ** 2 + ry ** 2 * x1p ** 2)
    if cf2 <= 0.0:
        cfactor = 0.0
    else:
        cfactor = math.sqrt(cf2)
    if large_arc == ccw:
        cfactor = -cfactor
    cxp = cfactor * rx * y1p / ry
    cyp = -cfactor * ry * x1p / rx
    cx = cos_phi * cxp - sin_phi * cyp + (x1 + x2) / 2.0
    cy = sin_phi * cxp + cos_phi * cyp + (y1 + y2) / 2.0
    theta1 = _Angle((1.0, 0.0), ((x1p - cxp) / rx, (y1p - cyp) / ry))
    delta_theta = _Angle(((x1p - cxp) / rx, (y1p - cyp) / ry),
        ((-x1p - cxp) / rx, (-y1p - cyp) / ry))
    if not ccw and delta_theta > 0.0:
        delta_theta -= 2 * math.pi
    elif ccw and delta_theta < 0.0:
        delta_theta += 2 * math.pi
    if abs(delta_theta) < 1e-5:
        # shouldn't happen
        return [start, end]

    # Now arc is:
    #  (x, y) = M * col(rx * cos theta, ry * sin theta) + col(cx, cy)
    # where theta goes from theta1 to theta1 + delta_theta
    # and M is rotation matrix for phi
    # Let's ignore the fact that the axes may have different lengths
    # and just divide delta_theta into the right number of segments
    # to satisfy the smoothness options.
    if options.subdiv_kind == "EVEN":
        # arc_length = pi*d * fraction of circle represented by delta_theta
        arc_length = abs(delta_theta * (rx + ry) / 2.0)
        numsegs = math.ceil(arc_length / options.even_length)
    else:
        # for smoothness 0, have 1 segment per quarter circle
        # and double for each smoothness increment after that
        numsegs = (2 ** options.smoothness) * \
            math.ceil(abs(delta_theta) / (math.pi * 2.0))
    theta_incr = delta_theta / numsegs
    ans = start
    theta = theta1
    endtheta = theta1 + delta_theta
    ans = [start]
    # end condition should be theta ~== endtheta but also
    # should be no more than numsegs iters
    for i in range(numsegs):
        theta = theta + theta_incr
        if abs(theta - endtheta) < 1e-5:
            break
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        x = cos_phi * rx * cos_theta - sin_phi * ry * sin_theta + cx
        y = sin_phi * rx * cos_theta + cos_phi * ry * sin_theta + cy
        ans.append((x, y))
    ans.append(end)
    return ans


def _Angle(u, v):
    """Return angle between two vectors.

    Args:
      u: (float, float)
      v: (float, float)
    Returns:
      float - angle in radians between u and v, where
        it is +/- depending on sign of ux * vy - uy * vx
    """

    (ux, uy) = u
    (vx, vy) = v
    costheta = (ux * vx + uy * vy) / \
        (math.sqrt(ux ** 2 + uy ** 2) * math.sqrt(vx ** 2 + vy ** 2))
    if costheta > 1.0:
        costheta = 1.0
    if costheta < -1.0:
        costheta = -1.0
    theta = math.acos(costheta)
    if ux * vy - uy * vx < 0.0:
        theta = -theta
    return theta


def _ClassifyPathPairs(a, b):
    """Classify vertices of path b with respect to path a.

    Args:
      a: geom.PolyArea - the test outer face (ignoring holes)
      b: geom.PolyArea - the test inner face (ignoring holes)
    Returns:
      (int, int) - first is #verts of b inside a, second is #verts of b on a
    """

    num_in = 0
    num_on = 0
    for v in b.poly:
        vp = b.points.pos[v]
        k = geom.PointInside(vp, a.poly, a.points)
        if k > 0:
            num_in += 1
        elif k == 0:
            num_on += 1
    return (num_in, num_on)


def _Contains(i, j, areas, lens, cls):
    """Return True if path i contains majority of vertices of path j.

    Args:
      i: index of supposed containing path
      j: index of supposed contained path
      areas: list of floats - areas of all the paths
      lens: list of ints - lenths of each of the paths
      cls: dict - maps pairs to result of _ClassifyPathPairs
    Returns:
      bool - True if path i contains at least 55% of j's vertices
    """

    if i == j:
        return False
    (jinsidei, joni) = cls[(i, j)]
    if jinsidei == 0 or joni == lens[j] or \
       float(jinsidei) / float(lens[j]) < 0.55:
        return False
    else:
        (insidej, _) = cls[(j, i)]
        if float(insidej) / float(lens[i]) > 0.55:
            return areas[i] > areas[j]  # tie breaker
        else:
            return True


def _IsBoundary(i, n, cont, assigned):
    """Is path i a boundary, given current assignment?

    Args:
      i: int - index of a path to test for boundary possiblity
      n: int - total number of paths
      cont: dict - maps path pairs (i,j) to _Contains(i,j,...) result
      assigned: set  of int - which paths are already assigned
    Returns:
      bool - True if there is no unassigned j, j!=i, such that
             path j contains path i
    """

    for j in range(0, n):
        if j == i or j in assigned:
            continue
        if (j, i) in cont:
            return False
    return True


def _GetHoles(i, n, cont, assigned):
    """Find holes for path i: i.e., unassigned paths directly inside it.

    Directly inside means there is not some other unassigned path k
    such that path such that path i contains k and path k contains j.
    (If such a k is already assigned, then its islands have been assigned too.)

    Args:
      i: int - index of a boundary path
      n: int - total number of paths
      cont: dict - maps path pairs (i,j) to _Contains(i,j,...) result
      assigned: set  of int - which paths are already assigned
    Returns:
      list of int - indices of paths that are islands
    Side Effect:
      Adds island indices to assigned set.
    """

    isls = []
    for j in range(0, n):
        if j in assigned:
            continue   # catches i==j too, since i is assigned by now
        if (i, j) in cont:
            directly = True
            for k in range(0, n):
                if k == j or k in assigned:
                    continue
                if (i, k) in cont and (k, j) in cont:
                    directly = False
                    break
            if directly:
                isls.append(j)
                assigned.add(j)
    return isls


def _flatten(l):
    """Return a flattened shallow list.

    Args:
      l : list of lists
    Returns:
      list - concatenation of sublists of l

    """

    return list(itertools.chain.from_iterable(l))
