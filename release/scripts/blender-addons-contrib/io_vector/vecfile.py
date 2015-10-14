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

"""Reading various vector file formats.

Functions for classifying files, tokenizing, and parsing them.
The ultimate goal is to parse a file into an instance of the class Art,
which has the line segments, bezier segments, arc segments,
and faces specified in a vector file.
"""

__author__ = "howard.trickey@gmail.com"

import re
from . import geom
from . import pdf
from . import svg

WARN = True   # print Warnings about strange things?

# Token types

TNAME = 0
TLITNAME = 1
TSTRING = 2
TNUM = 3


def ClassifyFile(filename):
    """Classify file into one of known vector types.

    Args:
      filename: string, the name of the file to classify
    Returns:
      (string, string), giving maintype and version.
      If there's an error, returns ("error", reason-string)
    """

    if filename.endswith(".svg"):
        return ("svg", "")
    try:
        f = open(filename, "rb")
        start = f.read(25)
    except IOError:
        return ("error", "file open error")

    # Encapsulated Postscript files start like
    #   %!PS-Adobe-X.X EPSF-Y.Y
    # where the first number is the version of PostScript Document Structuring
    # Convention, and the second number is the level of EPSF.
    # Adobe Illustrator files, version 8 and earlier, have
    #   %%+ procset Adobe_Illustrator...
    # sometime before %%EndProlog
    if start.startswith(b"%!PS-Adobe-"):
        ans = ("ps", "")
        if start[14:20] == b" EPSF-":
            ans = ("eps", start[20:23].decode())
        if start[14:19] == b" PDF-":
            ans = ("pdf", start[19:22].decode())
        if ans[0] != "pdf" and _FindAdobeIllustrator(f):
            ans = ("ai", "eps")
    # PDF files start with %PDF
    # Adobe Illustrator files, version 9 and later, have
    #   %%+ procset Adobe_Illustrator...
    # sometime before %%EndProlog
    elif start.startswith(b"%PDF"):
        ans = ("pdf", start[5:8].decode())
        if _FindAdobeIllustrator(f):
            ans = ("ai", "pdf")
    else:
        ans = ("error", "unknown file type")
    f.close()
    return ans


def _FindAdobeIllustrator(f):
    """Does a file contain "Adobe_Illustrator"?

    Args:
      f: an open File
    Returns:
      bool: True if reading forward in f, we find "Adobe_Illustrator"
    """

    while True:
        s = f.readline()
        if not s or s.startswith(b"%%EndProlog"):
            break
        if s.find(b"Adobe_Illustrator") >= 0:
            return True
    return False


def ParseVecFile(filename):
    """Parse a vector art file and return an Art object for it.

    Right now, handled file types  are: EPS, Adobe Illustrator, PDF

    Args:
      filename: string - name of the file to read and parse
    Returns:
      geom.Art: object containing paths drawn in the file.
           Return None if there was a major problem reading the file.
    """

    (major, minor) = ClassifyFile(filename)
    if (major == "error"):
        print("Couldn't get Art:", minor)
        return None
    if major == "pdf" or (major == "ai" and minor == "pdf"):
        contents = pdf.ReadPDFPageOneContents(filename)
        if contents:
            toks = TokenizeAIEPS(contents)
            return ParsePS(toks, major, minor)
        else:
            return None
    elif major == "eps" or (major == "ai" and minor == "eps"):
        toks = TokenizeAIEPSFile(filename)
        return ParsePS(toks, major, minor)
    elif major == "svg":
        return svg.ParseSVGFile(filename)
    else:
        return None


def ParseAIEPSFile(filename):
    """Parse an AI (eps kind) file and return an Art object for it.

    Args:
      filename: string - name of the file to read and parse
    Returns:
      geom.Art - object containing paths and faces drawn in the file
    """

    toks = TokenizeAIEPSFile(filename)
    return ParsePS(toks, "ai", "eps")


def TokenizeAIEPSFile(filename):
    """Tokenize the after-setup part of an AI (eps kind) file.

    Runs TokenizeAIEPS (see below) on the contents of the file.

    Args:
      filename: name of the file to tokenize
    Returns:
      list of (tokenid, value) tuples
    """

    try:
        f = open(filename, "rU")  # 'U'-> all newline reps converted to '\n'
    except IOError:
        if WARN:
            print("Can't open file", filename)
        return []
    contents = f.read()
    f.close()
    return TokenizeAIEPS(contents)

# Regular expressions for PostScript tokens
_re_psname = re.compile(r"[^ \t\r\n()<>[\]{}/%]+")
_re_psfloat = re.compile(r"(\+|-)?(([0-9]+\.[0-9]*)|(\.[0-9]+))")
_re_psint = re.compile(r"(\+|-)?[0-9]+")
_re_psstring = re.compile(r"\((\\.|.)*?\)")
_re_pshexstring = re.compile(r"<.*>")


def TokenizeAIEPS(s):
    """Tokenize the after-setup part of the an AI (eps kind) string.

    Args:
      s: string to tokenize
    Returns:
      list of (Txxx, val) where Txxx is a token type constant
    """

    i = s.find("%%EndSetup")
    i += 10
    if i == -1:
        return (False, "couldn't find illustration part of file")
    ans = []
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
        elif c == "%":
            i = s.find("\n", i)
            if i < 0:
                i = len(s)
                break
            i += 1
        elif c == "/":
            m = _re_psname.match(s, i + 1)
            if m:
                ans.append((TLITNAME, m.group()))
                i = m.end()
            else:
                if WARN:
                    print("empty name at", i)
                i += 1
        elif c == "(":
            m = _re_psstring.match(s, i)
            if m:
                ans.append((TSTRING, s[m.start() + 1:m.end() - 1]))
                i = m.end()
            else:
                if WARN:
                    print("unterminated string at", i)
                i = len(s)
        elif c == "<":
            m = _re_pshexstring.match(s, i)
            if m:
                ans.append((TSTRING, s[m.start() + 1:m.end() - 1]))
                i = m.end()
            else:
                if WARN:
                    print("unterminated hex string at", i)
                i = len(s)  # unterminated hex string
        elif c == "[" or c == "]" or c == "{" or c == "}":
            ans.append((TNAME, c))
            i += 1
        elif c == "-" or c.isdigit():
            m = _re_psfloat.match(s, i)
            if m:
                v = float(m.group())
                ans.append((TNUM, v))
                i = m.end()
            else:
                m = _re_psint.match(s, i)
                if m:
                    v = int(m.group())
                    ans.append((TNUM, v))
                    i = m.end()
                else:
                    if WARN:
                        print("number parse problem at", i)
                    i += 1
        else:
            m = _re_psname.match(s, i)
            if m:
                ans.append((TNAME, m.group()))
                i = m.end()
            else:
                if WARN:
                    print("tokenize error at", i, s[i:i + 10], "...")
                i += 1
    return ans


class GState(object):
    """Object to hold graphic state.

    Attributes:
      ctm: geom.TransformMatrix - current transform matrix
      fillpaint: geom.Paint
      strokepaint: geom.Paint
    """

    def __init__(self):
        self.ctm = geom.TransformMatrix()
        self.fillpaint = geom.black_paint
        self.strokepaint = geom.black_paint

    def Copy(self):
        """Return a copy of this graphics state."""

        gs = GState()
        gs.ctm = self.ctm.Copy()
        gs.fillpaint = self.fillpaint  # ok to share, paint is immutable
        gs.strokepaint = self.strokepaint
        return gs


class _PathState(object):
    """Object to hold state while parsing Adobe paths.

    Attributes:
      art: geom.Art, used  to accumulate answer
      curpath: geom.Path
      cursubpath: geom.Subpath - not yet added into curpath
      curpoint: coordinates of current point, None if none
      incompound: true if parsing an ai/eps compound path
      gstate: GState - the current graphics state
      gstack: list of GState - stack when graphics state pushed
      messages: list of string - warnings, errors
    """

    def __init__(self):
        """Construct the _PathState object."""

        self.art = geom.Art()
        self.ResetPath()
        self.incompound = False
        self.gstate = GState()
        self.statestack = []
        self.messages = []

    def CloseSubpath(self):
        """Close the current subpath.

        Close the current subpath by appending a straight line segment from
        current point to starting point of the subpath, terminating current
        subpath.
        Does nothing if current subpath is already closed or is empty.
        """

        if not self.cursubpath.Empty():
            startp = geom.Subpath.SegStart(self.cursubpath.segments[0])
            if startp != self.curpoint:
                self.cursubpath.AddSegment(("L", self.curpoint, startp))
                self.curpoint = startp
            self.curpath.AddSubpath(self.cursubpath)
            self.cursubpath = geom.Subpath()

    def ResetPath(self):
        """Reset the current path state to empty,
        discarding any current path."""

        self.curpath = geom.Path()
        self.cursubpath = geom.Subpath()
        self.curpoint = None
        self.incompound = False

    def StartCompound(self):
        """Mark entry to an ai/eps compound path."""

        self.incompound = True

    def EndCompound(self):
        """Finish off an ai/eps compound path."""

        if not self.curpath.Empty():
            self.art.paths.append(self.curpath)
        self.ResetPath()

    def DrawPath(self, dofill, dostroke, fillevenodd=False):
        """End the current path and add its subpaths to art.

        Assume any finally closing of the current subpath, if needed,
        was done separately.
        If we are in an ai/eps compound path, don't close off the
        current path yet - wait until EndCompound - but record
        the fill/stroke parameters for later use.

        Arguments:
          dofill: if true, the path is to be filled
          dostroke: if true, the path is to be stroked
          fillevenodd: it true, use even-odd fill rule,
              else nonzero winding number rule
        """

        if not self.cursubpath.Empty():
            self.curpath.AddSubpath(self.cursubpath)
            self.cursubpath = geom.Subpath()
        p = self.curpath
        if not p.Empty():
            p.filled = dofill
            p.fillevenodd = fillevenodd
            p.stroked = dostroke
            if dofill:
                p.fillpaint = self.gstate.fillpaint
            if dostroke:
                p.strokepaint = self.gstate.strokepaint
            if not self.incompound:
                self.art.paths.append(p)
                self.ResetPath()
        elif not self.incompound:
            self.ResetPath()

    def MoveTo(self, x, y, relative=False):
        """Begin a new subpath, starting at (x,y).

        If the previous path construction was also a MoveTo,
        its effect is overridden.
        If relative is True, the move should be relative
        to the previous point, else it is absolute.

        Args:
          x: float
          y: float - the 2d coord to start at
          relative: bool - if true, then a relative move, else absolute
        """

        (xp, yp) = self.gstate.ctm.Apply((x, y))
        if relative and self.curpoint:
            xp += self.curpoint[0]
            yp += self.curpoint[1]
        p = (xp, yp)
        if not self.cursubpath.Empty():
            self.curpath.AddSubpath(self.cursubpath)
        self.cursubpath = geom.Subpath()
        self.curpoint = p

    def LineTo(self, x, y, relative=False):
        """Append a straight line segment from current point to (x,y).

        Does nothing if there is no current point, or the segment
        would have no length.
        If relative is True, the endpoint of the line is relative to the start.

        Args:
          x: float
          y: float - the 2d coord to make the line to.
          relative: bool - if true, then a relative lineto
        """

        if self.curpoint == -1:
            return
        (xp, yp) = self.gstate.ctm.Apply((x, y))
        if relative and self.curpoint:
            xp += self.curpoint[0]
            yp += self.curpoint[1]
        p = (xp, yp)
        if p != self.curpoint:
            self.cursubpath.AddSegment(("L", self.curpoint, p))
            self.curpoint = p

    def Bezier3To(self, x, y, cp1x, cp1y, cp2x, cp2y,
                  use_start_as_cp=False, relative=False):
        """Append a cubic bezier curve from current point to (x,y).

        Args:
          x: float
          y: float - the 2d coord that ends the curve
          cp1x: float
          cp1y: float - first bezier control point
          cp2x: float
          cp2y: float - second bezier control point
          use_start_as_cp: bool - if True, ignore cp1x,cp2y and use current
              point as first control point instead
          relative: bool - if True, all coords are relative to previous point
        """

        if self.curpoint == -1:
            return
        (rx, ry) = (0, 0)
        if relative and self.curpoint:
            (rx, ry) = self.curpoint
        if use_start_as_cp:
            cp1 = self.curpoint
        else:
            cp1 = self.gstate.ctm.Apply((cp1x + rx, cp1y + ry))
        cp2 = self.gstate.ctm.Apply((cp2x + rx, cp2y + ry))
        p = self.gstate.ctm.Apply((x + rx, y + ry))
        self.cursubpath.AddSegment(("B", self.curpoint, p, cp1, cp2))
        self.curpoint = p

    def PushGState(self):
        """Push the graphics state, leaving a copy in gstate."""

        newgstate = self.gstate.Copy()
        self.statestack.append(self.gstate)
        self.gstate = newgstate

    def PopGState(self):
        """Pop the graphics state (no-op if stack is empty)."""

        if self.statestack:
            self.gstate = self.statestack.pop()


def ParsePS(toks, major="pdf", minor=""):
    """Parse a Postscript-like token list into an Art object.

    Four kinds of files use approximately the same painting
    model and operators:
      Encapsulated Postscript (EPS) - Postscript with Document
        Structuring Convention Comments: in general, these
        can have Postscript procedures and are not handled
        by the code here, but many programs producing eps
        just use the path creating/painting operators or
        abbreviations for them.
      Adobe Illustrator, version <=8: Uses EPS but with
        paths are all just single subpaths unless enclosed
        in compound path brackets (*u ... *U)
      Adobe Illustrator, version >=9: PDF for page description
      PDF: similar to Postscript, but some different operators

     We can parse each into an Art structure using approximately
     the same code.

    Args:
      toks: list of (Txxx, val), result of Tokenizing a file
      major: string - major version ("ps", "eps", "pdf", or "ai")
      minor: string - minor version (version number for ps, eps, pdf,
                      and "eps" or "pdf" for "ai")
    Returns:
      geom.Art: object with the paths painted by the token stream
    """

    pstate = _PathState()
    i = 0
    while i < len(toks):
        (t, v) = toks[i]
        i += 1
        if t == TNAME:
            # zero-operand operator or unhandled one
            # since all handled multi-operand operators
            # are handled below
            if v == "h" or v == "H" or v == "closepath":
                pstate.CloseSubpath()
            elif v == "f" or v == "F" or v == "fill":
                # fill path using nonzero winding number rule
                pstate.DrawPath(True, False, False)
            elif v == "f*" or v == "eofill":
                # fill path using even-odd rule
                pstate.DrawPath(True, False, True)
            elif v == "s":
                # close and stroke path
                pstate.CloseSubpath()
                pstate.DrawPath(False, True)
            elif v == "S" or v == "stroke":
                # stroke path
                pstate.DrawPath(False, True)
            elif v == "b":
                # close, fill and stroke path using nonzero winding rule
                pstate.CloseSubpath()
                pstate.DrawPath(True, True, False)
            elif v == "B":
                # fill and stroke path uwing nonzero winding rule
                pstate.DrawPath(True, True, False)
            elif v == "b*":
                # close, fill and stroke path using even-odd rule
                pstate.CloseSubpath()
                pstate.DrawPath(True, True, True)
            elif v == "B*":
                # fill and stroke path using even-odd rule
                pstate.DrawPath(True, True, True)
            elif v == "n" or v == "N" or v == "newpath":
                # finish path no-op, probably after clipping
                # (which is not handled yet)
                pstate.ResetPath()
            elif v == "*u" and major == "ai" and minor == "eps":
                # beginning of AI compound path
                pstate.StartCompound()
            elif v == "*U" and major == "ai" and minor == "eps":
                # end of AI compound path
                pstate.EndCompound()
            elif v == "q" or v == "gsave":
                pstate.PushGState()
            elif v == "Q" or v == "grestore":
                pstate.PopGState()
        elif t == TNUM:
            # see if have nargs numbers followed by an op name
            op = ""
            args = [float(v)]
            iend = min(i + 6, len(toks))
            while i < iend:
                t = toks[i][0]
                if t == TNUM:
                    args.append(float(toks[i][1]))
                    i += 1
                elif t == TNAME:
                    op = toks[i][1]
                    i += 1
                    break
                else:
                    break
            if op and len(args) <= 6:
                if len(args) == 1:
                    if op == "g":
                        # gray level for non-stroking operations
                        pstate.gstate.fillpaint = geom.Paint(args[0],
                            args[0], args[0])
                    elif op == "G":
                        pstate.gstate.strokepaint = geom.Paint(args[0],
                            args[0], args[0])
                if len(args) == 2:
                    if op == "m" or op == "moveto":
                        pstate.MoveTo(args[0], args[1], False)
                    elif op == "rmoveto":
                        pstate.MoveTo(args[0], args[1], True)
                    elif op == "l" or op == "L" or op == "lineto":
                        pstate.LineTo(args[0], args[1], False)
                    elif op == "rlineto":
                        pstate.LineTo(args[0], args[1], True)
                    elif op == "scale":
                        pstate.gstate.ctm.ComposeTransform(args[0], 0.0,
                            0.0, args[1], 0.0, 0.0)
                    elif op == "translate":
                        pstate.gstate.ctm.ComposeTransform(0.0, 0.0,
                            0.0, 0.0, args[0], args[1])
                if len(args) == 3:
                    if op == "rg" or op == "scn":
                        # rgb for non-stroking operations
                        # For scn should really refer to Color space from
                        # cs operator, which in turn may need to look in
                        # Resource Dictionary in pdf,
                        # so for now punt and assume rgb if three operands
                        pstate.gstate.fillpaint = geom.Paint(args[0],
                            args[1], args[2])
                    elif op == "RG" or op == "SCN":
                        pstate.gstate.strokepaint = geom.Paint(args[0],
                            args[1], args[2])
                elif len(args) == 4:
                    if op == "v" or op == "V":
                        # cubic bezier but use start as first cp
                        pstate.Bezier3To(args[2], args[3], 0.0, 0.0,
                                         args[0], args[1],
                                         use_start_as_cp=True)
                    elif op == "y" or op == "Y":
                        # cubic bezier but use last as second cp
                        pstate.Bezier3To(args[2], args[3], args[0], args[1],
                                         args[2], args[3])
                    elif op == "re" or op == "rectfill" or op == "rectstroke":
                        # rectangle with x, y, width, height as args
                        # drawn as complete subpath  (a PDF operator)
                        x = args[0]
                        y = args[1]
                        w = args[2]
                        h = args[3]
                        pstate.MoveTo(x, y)
                        pstate.LineTo(x + w, y)
                        pstate.LineTo(x + w, y + h)
                        pstate.LineTo(x, h + y)
                        pstate.CloseSubpath()
                        if op == "rectfill":
                            pstate.DrawPath(True, False)
                        elif op == "rectstroke":
                            pstate.DrawPath(False, True)
                    elif op == "k" or op == "scn":
                        # cmyk for non-stroking operations
                        # For scn should really refer to Color space from
                        # cs operator, which in turn may need to look in
                        # Resource Dictionary in pdf,
                        # so for now punt and assume cmyk if four operands
                        pstate.gstate.fillpaint = geom.Paint.CMYK(args[0],
                            args[1], args[2], args[3])
                    elif op == "K" or op == "SCN":
                        pstate.gstate.strokepaint = geom.Paint.CMYK(args[0],
                            args[1], args[2], args[3])
                elif len(args) == 6:
                    if op == "c" or op == "C" or op == "curveto":
                        # corner and non-corner cubic beziers
                        pstate.Bezier3To(args[4], args[5], args[0], args[1],
                                         args[2], args[3], False, False)
                    elif op == "rcurveto":
                        pstate.Bezier3To(args[4], args[5], args[0], args[1],
                                         args[2], args[3], False, True)
                    elif op == "cm" or op == "concat":
                        pstate.gstate.ctm.ComposeTransform(args[0], args[1],
                            args[2], args[3], args[4], args[5])
    return pstate.art


# Notes on Adobe Illustrator post version 8:
# Outside format is PDF.
# A Page object may have a PieceInfo with Illustrator attribute
# pointing to an object with a Private attribute that points to
# an object with AIMetaData and AIPrivateData[123456]
# AIMetaData points to the prolog of an old-style AI file
# AIPrivate1 points to a thumbnail image
# AIPrivate2-6 point to compressed stream objects - need more investigation.
# But AI version12 does different stuff: has AIPrivateData1-6 etc.
# It appears that AIPrivate6 obj has the %EndSetup and then old-style AI file
# So: hacky way that will sometimes work:
# 1) find "/AIPrivateData6 Z 0 R"  for some Z
# 2) find "Z 0 obj"
# 3) find following stream, and then endstream
# 4) flatedecode the stream if necessary
# 5) look for "%%EndSetup, if found: tokenize and parse like old AI files
