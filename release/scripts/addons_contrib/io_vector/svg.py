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

"""Reading SVG file format.
"""

__author__ = "howard.trickey@gmail.com"

import re
import xml.dom.minidom
from . import geom

TOL = 1e-5


def ParseSVGFile(filename):
    """Parse an SVG file name and return an Art object for it.

    Args:
      filename: string - name of file to read and parse
    Returns:
      geom.Art
    """

    dom = xml.dom.minidom.parse(filename)
    return _SVGDomToArt(dom)


def ParseSVGString(s):
    """Parse an SVG string and return an Art object for it.

    Args:
      s: string - contains svg
    Returns:
      geom.Art
    """

    dom = xml.dom.minidom.parseString(s)
    return _SVGDomToArg(dom)


class _SState(object):
    """Holds state that affects the conversion.
    """

    def __init__(self):
        self.ctm = geom.TransformMatrix()
        self.fill = "black"
        self.fillrule = "nonzero"
        self.stroke = "none"
        self.dpi = 90  # default Inkscape DPI


def _SVGDomToArt(dom):
    """Convert an svg file in dom form into an Art object.

    Args:
      dom: xml.dom.minidom.Document
    Returns:
      geom.Art
    """

    art = geom.Art()
    svgs = dom.getElementsByTagName('svg')
    if len(svgs) == 0:
        return art
    gs = _SState()
    gs.ctm.d = -1.0
    _ProcessChildren(svgs[0], art, gs)
    return art


def _ProcessChildren(nodes, art, gs):
    """Process a list of SVG nodes, updating art.

    Args:
      nodes: list of xml.dom.Node
      art: geom.Art
      gs: _SState
    Side effects:
      Maybe adds paths to art.
    """

    for node in nodes.childNodes:
        _ProcessNode(node, art, gs)


def _ProcessNode(node, art, gs):
    """Process an SVG node, updating art.

    Args:
      node: xml.dom.Node
      art: geom.Art
      gs: _SState
    Side effects:
      Maybe adds paths to art.
    """

    if node.nodeType != node.ELEMENT_NODE:
        return
    tag = node.tagName
    if tag == 'g':
        _ProcessChildren(node, art, gs)
    elif tag == 'defs':
        pass  # TODO
    elif tag == 'path':
        _ProcessPath(node, art, gs)
    elif tag == 'polygon':
        _ProcessPolygon(node, art, gs)
    elif tag == 'rect':
        _ProcessRect(node, art, gs)
    elif tag == 'ellipse':
        _ProcessEllipse(node, art, gs)
    elif tag == 'circle':
        _ProcessCircle(node, art, gs)


def _ProcessPolygon(node, art, gs):
    """Process a 'polygon' SVG node, updating art.

    Args:
      node: xml.dom.Node - a 'polygon' node
      arg: geom.Art
      gs: _SState
    Side effects:
      Adds path for polygon to art
    """

    if node.hasAttribute('points'):
        coords = _ParseCoordPairList(node.getAttribute('points'))
        n = len(coords)
        if n > 0:
            c = [gs.ctm.Apply(coords[i]) for i in range(n)]
            sp = geom.Subpath()
            sp.segments = [('L', c[i], c[i % n]) for i in range(n)]
            sp.closed = True
            path = geom.Path()
            _SetPathAttributes(path, node, gs)
            path.subpaths = [sp]
            art.paths.append(path)


def _ProcessPath(node, art, gs):
    """Process a 'polygon' SVG node, updating art.

    Args:
      node: xml.dom.Node - a 'polygon' node
      arg: geom.Art
      gs: _SState
    Side effects:
      Adds path for polygon to art
    """

    if not node.hasAttribute('d'):
        return
    s = node.getAttribute('d')
    i = 0
    n = len(s)
    path = geom.Path()
    _SetPathAttributes(path, node, gs)
    initpt = (0.0, 0.0)
    subpath = None
    while i < len(s):
        (i, subpath, initpt) = _ParseSubpath(s, i, initpt, gs)
        if subpath:
            if not subpath.Empty():
                path.AddSubpath(subpath)
        else:
            break
    if path.subpaths:
        art.paths.append(path)


def _ParseSubpath(s, i, initpt, gs):
    """Parse a moveto-drawto-command-group starting at s[i] and return Subpath.

    Args:
      s: string - should be the 'd' attribute of a 'path' element
      i: int - index in s to start parsing
      initpt: (float, float) - coordinates of initial point
      gs: _SState - used to transform coordinates
    Returns:
      (int, geom.Subpath, (float, float)) -
          (index after subpath and subsequent whitespace,
          the Subpath itself or Non if there was an error, final point)
    """

    subpath = geom.Subpath()
    i = _SkipWS(s, i)
    n = len(s)
    if i >= n:
        return (i, None, initpt)
    if s[i] == 'M':
        move_cmd = 'M'
    elif s[i] == 'm':
        move_cmd = 'm'
    else:
        return (i, None, initpt)
    (i, cur) = _ParseCoordPair(s, _SkipWS(s, i + 1))
    if not cur:
        return (i, None, initpt)
    prev_cmd = 'L'  # implicit cmd if coords follow directly
    if move_cmd == 'm':
        cur = geom.VecAdd(initpt, cur)
        prev_cmd = 'l'
    while True:
        implicit_cmd = False
        if i < n:
            cmd = s[i]
            if _PeekCoord(s, i):
                cmd = prev_cmd
                implicit_cmd = True
        else:
            cmd = None
        if cmd == 'z' or cmd == 'Z' or cmd == None:
            if cmd:
                i = _SkipWS(s, i + 1)
                subpath.closed = True
            return (i, subpath, cur)
        if not implicit_cmd:
            i = _SkipWS(s, i + 1)
        if cmd == 'l' or cmd == 'L':
            (i, p1) = _ParseCoordPair(s, i)
            if not p1:
                break
            if cmd == 'l':
                p1 = geom.VecAdd(cur, p1)
            subpath.AddSegment(_LineSeg(cur, p1, gs))
            cur = p1
        elif cmd == 'c' or cmd == 'C':
            (i, p1, p2, p3) = _ParseThreeCoordPairs(s, i)
            if not p1:
                break
            if cmd == 'c':
                p1 = geom.VecAdd(cur, p1)
                p2 = geom.VecAdd(cur, p2)
                p3 = geom.VecAdd(cur, p3)
            subpath.AddSegment(_Bezier3Seg(cur, p3, p1, p2, gs))
            cur = p3
        elif cmd == 'a' or cmd == 'A':
            (i, p1, rad, rot, la, ccw) = _ParseArc(s, i)
            if not p1:
                break
            if cmd == 'a':
                p1 = geom.VecAdd(cur, p1)
            subpath.AddSegment(_ArcSeg(cur, p1, rad, rot, la, ccw, gs))
            cur = p1
        elif cmd == 'h' or cmd == 'H':
            (i, x) = _ParseCoord(s, i)
            if x is None:
                break
            if cmd == 'h':
                x += cur[0]
            subpath.AddSegment(_LineSeg(cur, (x, cur[1]), gs))
            cur = (x, cur[1])
        elif cmd == 'v' or cmd == 'V':
            (i, y) = _ParseCoord(s, i)
            if y is None:
                break
            if cmd == 'v':
                y += cur[1]
            subpath.AddSegment(_LineSeg(cur, (cur[0], y), gs))
            cur = (cur[0], y)
        elif cmd == 's' or cmd == 'S':
            (i, p2, p3) = _ParseTwoCoordPairs(s, i)
            if not p2:
                break
            if cmd == 's':
                p2 = geom.VecAdd(cur, p2)
                p3 = geom.VecAdd(cur, p3)
            # p1 is reflection of cp2 of previous command
            # through current point (but p1 is cur if no previous)
            if len(subpath.segments) > 0 and subpath.segments[-1][0] == 'B':
                p4 = subpath.segments[-1][4]
            else:
                p4 = cur
            p1 = geom.VecAdd(cur, geom.VecSub(cur, p4))
            subpath.AddSegment(_Bezier3Seg(cur, p3, p1, p2, gs))
            cur = p3
        else:
            # TODO: quadratic beziers, 'q', and 't'
            break
        i = _SkipCommaSpace(s, i)
        prev_cmd = cmd
    return (i, None, cur)


def _ProcessRect(node, art, gs):
    """Process a 'rect' SVG node, updating art.

    Args:
      node: xml.dom.Node - a 'polygon' node
      arg: geom.Art
      gs: _SState
    Side effects:
      Adds path for rectangle to art
    """

    if not (node.hasAttribute('width') and node.hasAttribute('height')):
        return
    w = _ParseLengthAttrOrDefault(node, 'width', gs, 0.0)
    h = _ParseLengthAttrOrDefault(node, 'height', gs, 0.0)
    if w <= 0.0 or h <= 0.0:
        return
    x = _ParseCoordAttrOrDefault(node, 'x', 0.0)
    y = _ParseCoordAttrOrDefault(node, 'y', 0.0)
    rx = _ParseLengthAttrOrDefault(node, 'rx', gs, 0.0)
    ry = _ParseLengthAttrOrDefault(node, 'ry', gs, 0.0)
    if rx == 0.0 and ry > 0.0:
        rx = ry
    elif rx > 0.0 and ry == 0.0:
        ry = rx
    if rx > w / 2.0:
        rx = w / 2.0
    if ry > h / 2.0:
        ry = h / 2.0
    subpath = geom.Subpath()
    subpath.closed = True
    if rx == 0.0 and ry == 0.0:
        subpath.AddSegment(_LineSeg((x, y), (x + w, y), gs))
        subpath.AddSegment(_LineSeg((x + w, y), (x + w, y + h), gs))
        subpath.AddSegment(_LineSeg((x + w, y + h), (x, y + h), gs))
        subpath.AddSegment(_LineSeg((x, y + h), (x, y), gs))
    else:
        wmid = w - 2 * rx
        hmid = h - 2 * ry
        # top line
        if wmid > TOL:
            subpath.AddSegment(_LineSeg((x + rx, y), (x + rx + wmid, y), gs))
        # top right corner: remember, y positive downward, so this clockwise
        subpath.AddSegment(_ArcSeg((x + rx + wmid, y), (x + w, y + ry),
            (rx, ry), 0.0, False, False, gs))
        # right line
        if hmid > TOL:
            subpath.AddSegment(_LineSeg((x + w, y + ry),
                (x + w, y + ry + hmid), gs))
        # bottom right corner
        subpath.AddSegment(_ArcSeg((x + w, y + ry + hmid),
            (x + rx + wmid, y + h),
            (rx, ry), 0.0, False, False, gs))
        # bottom line
        if wmid > TOL:
            subpath.AddSegment(_LineSeg((x + rx + wmid, y + h),
                (x + rx, y + h), gs))
        # bottom left corner
        subpath.AddSegment(_ArcSeg((x + rx, y + h), (x, y + ry + hmid),
            (rx, ry), 0.0, False, False, gs))
        # left line
        if hmid > TOL:
            subpath.AddSegment(_LineSeg((x, y + ry + hmid), (x, y + ry), gs))
        # top left corner
        subpath.AddSegment(_ArcSeg((x, y + ry), (x + rx, y),
            (rx, ry), 0.0, False, False, gs))
    path = geom.Path()
    _SetPathAttributes(path, node, gs)
    path.subpaths = [subpath]
    art.paths.append(path)


def _ProcessEllipse(node, art, gs):
    """Process an 'ellipse' SVG node, updating art.

    Args:
      node: xml.dom.Node - a 'polygon' node
      arg: geom.Art
      gs: _SState
    Side effects:
      Adds path for ellipse to art
    """

    if not (node.hasAttribute('rx') and node.hasAttribute('ry')):
        return
    rx = _ParseLengthAttrOrDefault(node, 'rx', gs, 0.0)
    ry = _ParseLengthAttrOrDefault(node, 'ry', gs, 0.0)
    if rx < TOL or ry < TOL:
        return
    cx = _ParseCoordAttrOrDefault(node, 'cx', 0.0)
    cy = _ParseCoordAttrOrDefault(node, 'cy', 0.0)
    subpath = _FullEllipseSubpath(cx, cy, rx, ry, gs)
    path = geom.Path()
    path.subpaths = [subpath]
    _SetPathAttributes(path, node, gs)
    art.paths.append(path)


def _ProcessCircle(node, art, gs):
    """Process a 'circle' SVG node, updating art.

    Args:
      node: xml.dom.Node - a 'polygon' node
      arg: geom.Art
      gs: _SState
    Side effects:
      Adds path for circle to art
    """

    if not node.hasAttribute('r'):
        return
    r = _ParseLengthAttrOrDefault(node, 'r', gs, 0.0)
    if r < TOL:
        return
    cx = _ParseCoordAttrOrDefault(node, 'cx', 0.0)
    cy = _ParseCoordAttrOrDefault(node, 'cy', 0.0)
    subpath = _FullEllipseSubpath(cx, cy, r, r, gs)
    path = geom.Path()
    path.subpaths = [subpath]
    _SetPathAttributes(path, node, gs)
    art.paths.append(path)


def _FullEllipseSubpath(cx, cy, rx, ry, gs):
    """Return a Subpath for a full ellipse.

    Args:
      cx: float - center x
      cy: float - center y
      rx: float - x radius
      ry: float - y radius
      gs: _SState - for transform
    Returns:
      geom.Subpath
    """

    # arc starts at 3 o'clock
    # TODO: if gs has rotate transform, figure that out
    # and use that as angle for arc x-rotation
    subpath = geom.Subpath()
    subpath.closed = True
    subpath.AddSegment(_ArcSeg((cx + rx, cy), (cx, cy + ry),
        (rx, ry), 0.0, False, False, gs))
    subpath.AddSegment(_ArcSeg((cx, cy + ry), (cx - rx, cy),
        (rx, ry), 0.0, False, False, gs))
    subpath.AddSegment(_ArcSeg((cx - rx, cy), (cx, cy - ry),
        (rx, ry), 0.0, False, False, gs))
    subpath.AddSegment(_ArcSeg((cx, cy - ry), (cx + rx, cy),
        (rx, ry), 0.0, False, False, gs))
    return subpath


def _LineSeg(p1, p2, gs):
    """Return an 'L' segment, transforming coordinates.

    Args:
      p1: (float, float) - start point
      p2: (float, float) - end point
      gs: _SState - used to transform coordinates
    Returns:
      tuple - an 'L' type geom.Subpath segment
    """

    return ('L', gs.ctm.Apply(p1), gs.ctm.Apply(p2))


def _Bezier3Seg(p1, p2, c1, c2, gs):
    """Return a 'B' segment, transforming coordinates.

    Args:
      p1: (float, float) - start point
      p2: (float, float) - end point
      c1: (float, float) - first control point
      c2: (float, float) - second control point
      gs: _SState - used to transform coordinates
    Returns:
      tuple - an 'L' type geom.Subpath segment
    """

    return ('B', gs.ctm.Apply(p1), gs.ctm.Apply(p2),
        gs.ctm.Apply(c1), gs.ctm.Apply(c2))


def _ArcSeg(p1, p2, rad, rot, la, ccw, gs):
    """Return an 'A' segment, with attempt to transform.

    Our A segments don't allow modeling the effect of
    arbitrary transforms, but we can handle translation
    and scaling.

    Args:
      p1: (float, float) - start point
      p2: (float, float) - end point
      rad: (float, float) - (x radius, y radius)
      rot: float - x axis rotation, in degrees
      la: bool - large arc if True
      ccw: bool - counter-clockwise if True
      gs: _SState - used to transform
    Returns:
      tuple - an 'A' type geom.Subpath segment
    """

    tp1 = gs.ctm.Apply(p1)
    tp2 = gs.ctm.Apply(p2)
    rx = rad[0] * gs.ctm.a
    ry = rad[1] * gs.ctm.d
    # if one of axes is mirrored, invert the ccw flag
    if rx * ry < 0.0:
        ccw = not ccw
    trad = (abs(rx), abs(ry))
    # TODO: abs(gs.ctm.a) != abs(ts.ctm.d), adjust xrot
    return ('A', tp1, tp2, trad, rot, la, ccw)


def _SetPathAttributes(path, node, gs):
    """Set the attributes related to filling/stroking in path.

    Use attribute settings in node, if there, else those in the
    current graphics state, gs.

    Arguments:
      path: geom.Path
      node: xml.dom.Node
      gs: _SState
    Side effects:
      May set filled, fillevenodd, stroked, fillpaint, strokepaint in path.
    """

    fill = gs.fill
    stroke = gs.stroke
    fillrule = gs.fillrule
    if node.hasAttribute('style'):
        style = _CSSInlineDict(node.getAttribute('style'))
        if 'fill' in style:
            fill = style['fill']
        if 'stroke' in style:
            stroke = style['stroke']
        if 'fill-rule' in style:
            fillrule = style['fill-rule']
    if node.hasAttribute('fill'):
        fill = node.getAttribute('fill')
    if fill != 'none':
        paint = _ParsePaint(fill)
        if paint is not None:
            path.fillpaint = paint
            path.filled = True
    if node.hasAttribute('stroke'):
        stroke = node.getAttribute('stroke')
    if stroke != 'none':
        paint = _ParsePaint(stroke)
        if stroke is not None:
            path.strokepaint = paint
            path.stroked = True
    if node.hasAttribute('fill-rule'):
        fillrule = node.getAttribute('fill-rule')
    path.fillevenodd = (fillrule == 'evenodd')


# Some useful regular expressions
_re_float = re.compile(r"(\+|-)?(([0-9]+\.[0-9]*)|(\.[0-9]+)|([0-9]+))")
_re_int = re.compile(r"(\+|-)?[0-9]+")
_re_wsopt = re.compile(r"\s*")
_re_wscommaopt = re.compile(r"(\s*,\s*)|(\s*)")
_re_namevalue = re.compile(r"\s*(\S+)\s*:\s*(\S+)\s*(?:;|$)")


def _CSSInlineDict(s):
    """Parse string s as CSS inline spec, and return a dictionary for it.

    An inline CSS spec is semi-colon separated list of prop : value pairs,
    such as: "fill:none;fill-rule : evenodd"

    Args:
      s: string - inline CSS spec
    Returns:
      dict : maps string (prop name) -> string (value)
    """

    pairs = _re_namevalue.findall(s)
    return dict(pairs)


def _ParsePaint(s):
    """Parse an SVG paint definition and return our version of Paint.

    If is 'none', return None.
    If fail to parse (e.g., a TODO syntax), return black_paint.

    Args:
      s: string - should contain an SVG paint spec
    Returns:
      geom.Paint or None
    """

    if len(s) == 0 or s == 'none':
        return None
    if s[0] == '#':
        if len(s) == 7:
            # 6 hex digits
            return geom.Paint( \
              int(s[1:3], 16) / 255.0,
              int(s[3:5], 16) / 255.0,
              int(s[5:7], 16) / 255.0)
        elif len(s) == 4:
            # 3 hex digits
            return geom.Paint( \
              int(s[1], 16) * 17 / 255.0,
              int(s[2], 16) * 17 / 255.0,
              int(s[3], 16) * 17 / 255.0)
    else:
        if s in geom.ColorDict:
            return geom.ColorDict[s]
    return geom.black_paint


def _ParseLengthAttrOrDefault(node, attr, gs, default):
    """Parse the given attribute as a length, else return default.

    Args:
      node: xml.dom.Node
      attr: string - the attribute name
      gs: _SState - for dots-per-inch, for units conversion
      default: float - to return if no attr or error parsing it
    Returns:
      float - the length
    """

    if not node.hasAttribute(attr):
        return default
    (_, v) = _ParseLength(node.getAttribute(attr), gs, 0)
    if v is None:
        return default
    else:
        return v


def _ParseCoordAttrOrDefault(node, attr, default):
    """Parse the given attribute as a coordinate, else return default.

    Args:
      node: xml.dom.Node
      attr: string - the attribute name
      default: float - to return if no attr or error parsing it
    Returns:
      float - the coordinate
    """

    if not node.hasAttribute(attr):
        return default
    (_, v) = _ParseCoord(node.getAttribute(attr), 0)
    if v is None:
        return default
    else:
        return v


def _ParseCoord(s, i):
    """Parse a coordinate (floating point number).

    Args:
      s: string
      i: int - where to start parsing
    Returns:
      (int, float or None) - int is index after the coordinate
        and subsequent white space
    """

    m = _re_float.match(s, i)
    if m:
        return (_SkipWS(s, m.end()), float(m.group()))
    else:
        return (i, None)


def _PeekCoord(s, i):
    """Return True if s[i] starts a coordinate.

    Args:
      s: string
      i: int - place in s to start looking
    Returns:
      bool - True if s[i] starts a coordinate, perhaps after comma / space
    """

    i = _SkipCommaSpace(s, i)
    m = _re_float.match(s, i)
    return True if m else False


def _ParseCoordPair(s, i):
    """Parse pair of coordinates, with optional comma between.

    Args:
      s: string
      i: int - where to start parsing
    Returns:
      (int, (float, float) or None) - int is index after the coordinate
        and subsequent white space
    """

    (j, x) = _ParseCoord(s, i)
    if x is not None:
        j = _SkipCommaSpace(s, j)
        (j, y) = _ParseCoord(s, j)
        if y is not None:
            return (_SkipWS(s, j), (x, y))
    return (i, None)


def _ParseTwoCoordPairs(s, i):
    """Parse two coordinate pairs, optionally separated by commas.

    Args:
      s: string
      i: int - where to start parsing
    Returns:
      (int, (float, float) or None, (float, float) or None) -
        int is index after the coordinate and subsequent white space
    """

    (j, pair1) = _ParseCoordPair(s, i)
    if pair1:
        j = _SkipCommaSpace(s, j)
        (j, pair2) = _ParseCoordPair(s, j)
        if pair2:
            return (j, pair1, pair2)
    return (i, None, None)


def _ParseThreeCoordPairs(s, i):
    """Parse three coordinate pairs, optionally separated by commas.

    Args:
      s: string
      i: int - where to start parsing
    Returns:
      (int, (float, float) or None, (float, float) or None,
          (float, float) or None) -
        int is index after the coordinateand subsequent white space
    """

    (j, pair1) = _ParseCoordPair(s, i)
    if pair1:
        j = _SkipCommaSpace(s, j)
        (j, pair2) = _ParseCoordPair(s, j)
        if pair2:
            j = _SkipCommaSpace(s, j)
            (j, pair3) = _ParseCoordPair(s, j)
            if pair3:
                return (j, pair1, pair2, pair3)
    return (i, None, None, None)


def _ParseCoordPairList(s):
    """Parse a list of coordinate pairs.

    The numbers should be separated by whitespace
    or a comma with optional whitespace around it.

    Args:
      s: string - should contain coordinate pairs
    Returns:
      list of (float, float)
    """

    ans = []
    i = _SkipWS(s, 0)
    while i < len(s):
        (i, pair) = _ParseCoordPair(s, i)
        if not pair:
            break
        ans.append(pair)
    return ans


# units to be scaled by 'dots-per-inch' with these factors
_UnitDict = {
  'in': 1.0, 'mm': 0.0393700787,
  'cm': 0.393700787, 'pt': 0.0138888889, 'pc': 0.166666667,
  # assume 10pt font, 5pt font x-height
  'em': 0.138888889, 'ex': 0.0138888889 * 5}


def _ParseLength(s, gs, i):
    """Parse a length (floating point number, with possible units).

    Args:
      s: string
      gs: _SState, for dpi if needed for units conversion
      i: int - where to start parsing
    Returns:
      (int, float or None) - int is index after the coordinate
        and subsequent white space; float is converted to user coords
    """

    (i, v) = _ParseCoord(s, i)
    if v is None:
        return (i, None)
    upi = 1.0
    if i < len(s):
        if s[i] == '%':
            # supposed to be percentage of nearest enclosing
            # viewport in appropriate direction.
            # for now, assume viewport is 10in in each dir
            upi = dpi * 10.0 / 100.0
        elif i < len(s) - 1:
            cc = s[i:i + 2]
            if cc == 'px':
                upi = 1.0
                i += 2
            elif cc in _UnitDict:
                upi = gs.dpi * _UnitDict[cc]
                i += 2
    return (i, v * upi)


def _ParseArc(s, i):
    """Parse an elliptical arc specification.

    Args:
      s: string
      i: int - where to start parsing
    Returns:
      (int, (float, float) or None, (float, float), float, bool, bool) -
        int is index after spec and subsequent white space,
        first (float, float) is end point of arc
        second (float, float) is (x-radius, y-radius)
        float is x-axis rotation, in degrees
        first bool is True if larger arc is to be used
        second bool is True if arc follows ccw direction
    """

    (j, rad) = _ParseCoordPair(s, i)
    if rad:
        j = _SkipCommaSpace(s, j)
        (j, rot) = _ParseCoord(s, j)
        if rot is not None:
            j = _SkipCommaSpace(s, j)
            (j, f) = _ParseCoord(s, j)  # should really just look for 0 or 1
            if f is not None:
                laf = (f != 0.0)
                j = _SkipCommaSpace(s, j)
                (j, f) = _ParseCoord(s, j)
                if f is not None:
                    ccw = (f != 0.0)
                    j = _SkipCommaSpace(s, j)
                    (j, pt) = _ParseCoordPair(s, j)
                    if pt:
                        return (j, pt, rad, rot, laf, ccw)
    return (i, None, None, None, None, None)


def _SkipWS(s, i):
    """Skip optional whitespace at s[i]... and return new i.

    Args:
      s: string
      i: int - index into s
    Returns:
      int - index of first none-whitespace character from s[i], or len(s)
    """

    m = _re_wsopt.match(s, i)
    if m:
        return m.end()
    else:
        return i


def _SkipCommaSpace(s, i):
    """Skip optional space with optional comma in it.

    Args:
      s: string
      i: int - index into s
    Returns:
      int - index after optional space with optional comma
    """

    m = _re_wscommaopt.match(s, i)
    if m:
        return m.end()
    else:
        return i
