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

"""Functions for dealing with PDF files.
"""

__author__ = "howard.trickey@gmail.com"

import re
import sys
try:
    import zlib
except ImportError:
    zlib = None

# Python 2 and 3 differ in the type of result of indexing into
# a 'bytes' string, so define a function that returns the
# integer value regardless of the python version.
if sys.version_info[0] == 3:
    def ordat(b, i):
        return b[i]
else:
    def ordat(b, i):
        return ord(b[i])

WARN = True  # print Warnings about strange things?

# PDF objects
OBOOL = 0
ONUM = 1
OSTRING = 2
ONAME = 3
OARRAY = 4
ODICT = 5
OSTREAM = 6
ONULL = 7
OINDIRECTDEF = 8
OINDIRECTREF = 9

_re_psbool = re.compile(br'true|false')
_re_psint = re.compile(br'(\+|-)?[0-9]+')
_re_psreal = re.compile(br'((\+|-)?([0-9]+\.[0-9]*)|(\.[0-9]+))')
_re_psstring = re.compile(br'\((\\.|.)*?\)')
_re_pshexstring = re.compile(br'<[0-9A-Fa-f]*>')
_re_psname = re.compile(br'/([^\0\t\n\f\r \(\)<>[\]{}/%]*)')
_re_psnull = re.compile(br'null')
_re_pskeyword = re.compile(br'[A-Za-z]+')
_re_psstreameol = re.compile(br'\r\n|\n')
_re_psendstream = re.compile(br'endstream')
_re_pseol = re.compile(br'(\r\n|\n|\r)')
_re_pswhitespaceandcomments = re.compile(br'([\0\t\n\f\r ]|%[^\n\r]*[\n\r]+)*')

# Object Notes:
# The string re is not really right - the spec allows
# balanced parentheses to appear in a string unescaped.
# Also, strings need to convert the following escapes:
#   \n \r \t \b \f \( \) \\ \ddd (octal).
# Octal chars ddd can have 1, 2, or 3 octal digits with high order
# overflow ignored and leading zeros as needed (but not required,
# needed only if a normal digit follows the octal one).
#
# Hex strings may have odd number of digits - the last is assumed to be 0
#
# The token / (with no regular characters after it) is a valid name
# Names may include arbitrary characters by writing its 2-digit hex
# code preceded by a '#'.
#
# Array objects: sequence of objects enclosed in [ and ]
#
# Dictionary objects: sequence of key-value pairs enclosed in << and >>
# The keys must be names.  A dictionary entry whose value is null is
# equivalent to an absent entry.
# By convention, dictonary objects have a value with key /Type that
# identifies the type of dictionary. Sometimes there is a subtype,
# with key /Subtype or /S.  Values of type and subtype are always names.
#
# Stream objects: a dictionary followed by zero or more lines of bytes
# bracketed by keywords "stream" and "endstream". All streams must be
# indirect objects, and the dictionary must be a direct object.
#
# An Indirect Object Definition: two ints (object #, generation #)
# followed by the object bracketed by "obj" and "endobj"
#
# An Indirect Object Reference: two ints (object #, generation #) followed
# by "R".
# An indirect object reference to an object not defined in the file
# is taken as a reference to the null object.


def GetPDFObject(s, i):
    """Get one complete object starting at s[i].

    Args:
      s: bytes holding contents of a PDF file
      i: index into s
    Returns:
      ((objectid, value), int) - where int is i after the object
                                 use None instead of (objectid, value) if
                                 there are no more objects in s
    """

    m = _re_pswhitespaceandcomments.match(s, i)
    if m:
        i = m.end()
    if i == len(s):
        return (None, i)
    m = _re_psname.match(s, i)
    if m:
        return ((ONAME, s[m.start() + 1:m.end()].decode()), m.end())
    m = _re_psreal.match(s, i)
    if m:
        return ((ONUM, float(m.group())), m.end())
    m = _re_psint.match(s, i)
    if m:
        # could also be start of indirect object def or ref
        (o, j) = GetPDFIndirectObjectRefOrDef(s, i)
        if o is not None:
            return (o, j)
        else:
            return ((ONUM, int(m.group())), m.end())
    m = _re_psbool.match(s, i)
    if m:
        if m.group == b'true':
            v = True
        else:
            v = False
        return ((OBOOL, v), m.end())
    m = _re_psnull.match(s, i)
    if m:
        return ((ONULL, None), m.end())
    m = _re_psstring.match(s, i)
    if m:
        return GetPDFLiteralString(s, i)
    m = _re_pshexstring.match(s, i)
    if m:
        return GetPDFHexString(s, i, m.end())
    c = ordat(s, i)
    if c == ord('['):
        return GetPDFArray(s, i)
    elif c == ord('<') and i < len(s) - 1 and ordat(s, i + 1) == ord('<'):
        (o, j) = GetPDFDict(s, i)
        # check if followed by stream
        (w, k) = GetPDFKeyword(s, j)
        if w == b'stream':
            m = _re_psstreameol.match(s, k)
            if m:
                streamstart = m.end()
                streamend = s.find(b'endstream', streamstart)
                if streamend > 0:
                    # just return byte offsets in s where stream
                    # contents start and (most probably) end
                    return ((OSTREAM, (o[1], streamstart, streamend)),
                        streamend + 9)
        return (o, j)
    return (None, i + 1)


def GetPDFIndirectObjectRefOrDef(s, i):
    """Get an indirect object def or ref starting at s[i].

    Args:
      s: bytes holding contents of a PDF file
      i: index into s
    Returns:
      ((OINDIRECTDEF, (obj#,gen#,obj)), newi)
      or ((OINDIRECTREF, (obj#, gen#)), newi)
      or (None, i)
    """

    (v, j) = GetPDFTwoInts(s, i)
    if v is None:
        return (None, i)
    (obj_number, gen_number) = v
    (w, j) = GetPDFKeyword(s, j)
    if w == b'R':
        return ((OINDIRECTREF, (obj_number, gen_number)), j)
    elif w == b'obj':
        (obj, j) = GetPDFObject(s, j)
        if obj is not None:
            (w, j) = GetPDFKeyword(s, j)
            if w == b'endobj':
                return ((OINDIRECTDEF, (obj_number, gen_number, obj)), j)
    return (None, i)


def GetPDFTwoInts(s, i):
    """If there are two ints starting at s[i], return them, else return None.

    Args:
      s: PDF file contents
      i: index into s
    Returns:
      ((int, int), newi) or (None, i)
    """

    m = _re_pswhitespaceandcomments.match(s, i)
    j = i
    if m:
        j = m.end()
    if j == len(s):
        return (None, i)
    m = _re_psint.match(s, j)
    if m:
        a = int(m.group())
        j = m.end()
        m = _re_pswhitespaceandcomments.match(s, j)
        if m:
            j = m.end()
        if j == len(s):
            return (None, i)
        m = _re_psint.match(s, j)
        if m:
            b = int(m.group())
            return ((a, b), m.end())
    return (None, i)


def GetPDFKeyword(s, i):
    """Get a keyword (alphabetic chars, as byte string) starting at s[i].

    If there is not a keyword there, just return (b'',i).

    Args:
      s: bytes holding contents of a PDF file
      i: index into s
    Returns:
      (keyword, newi) - keyword will be b'' if couldn't find one
    """

    m = _re_pswhitespaceandcomments.match(s, i)
    j = i
    if m:
        j = m.end()
    if j == len(s):
        return (b'', i)
    m = _re_pskeyword.match(s, j)
    if m:
        return (m.group(), m.end())
    return (b'', i)


def GetPDFLiteralString(s, i):
    """Convert and return object for pdf literal string starting at s[i]."""

    j = i + 1
    balen = 0
    v = []
    while j < len(s):
        c = ordat(s, j)
        if c == ord(')'):
            if balen == 0:
                return ((OSTRING, ''.join(v)), j + 1)
            else:
                balen -= 1
        elif c == ord('('):
            balen += 1
        elif c == ord('\\'):
            j += 1
            if j == len(s):
                if WARN:
                    print("unterminated string at", i)
                return ((OSTRING, ''.join(v)), j)
            c = ordat(s, j)
            if c == ord('n'):
                v += '\n'
            elif c == ord('f'):
                v += '\f'
            elif c == ord('r'):
                v += '\r'
            elif c == ord('t'):
                v += '\t'
            elif ord('0') <= c <= ord('7'):
                x = ord(c) - ord('0')
                j += 1
                if j < len(s):
                    c = ordat(s, j)
                    if ord('0') <= c <= ord('7'):
                        x = x * 8 + c - ord('0')
                        j += 1
                        if j < len(s):
                            c = ordat(s, j)
                            if ord('0') <= c <= ord('7'):
                                x = x * 8 + c - ord('0')
                if x >= 256:
                    x %= 256
                v += chr(x)
            else:
                m = _re_pseol.match(s, j)
                if m:
                    # backslash used for line continuation
                    j = m.end() - 1  # -1 to compensate for +1 that will happen
                else:
                    v += chr(c)
        else:
            m = _re_pseol.match(s, j)
            if m:
                v += '\n'
                j = m.end() - 1  # -1 to compensate for +1
            else:
                v += chr(c)
        j += 1
    if WARN:
        print('unterminated string at', i)
    return ((OSTRING, ''.join(v)), j)


def GetPDFHexString(s, i, iend):
    """Convert and return pdf hex string starting at s[i],
    ending at s[iend-1]."""

    j = i + 1
    v = []
    c = ''
    jend = iend - 1
    while j < jend:
        p = _re_pswhitespaceandcomments.match(s, j)
        if p:
            j = p.end()
        d = chr(ordat(s, j))
        if c != '':
            v.append(FromHexPair(c, d))
            c = ''
        else:
            c = d
        j += 1
    if c != '':
        v.append(FromHexPair(c, '0'))
    return ((OSTRING, ''.join(v)), iend)


def FromHexPair(a, b):
    """Interpret string a+b as hex pair, and return the pair's value."""

    try:
        v = int(a + b, 16)
    except TypeError:
        if WARN:
            print('funny hex pair', a + b)
        v = 0
    return chr(v)


def GetPDFArray(s, i):
    """Convert and return object array starting at s[i]."""

    j = i + 1
    v = []
    while j < len(s):
        m = _re_pswhitespaceandcomments.match(s, j)
        if m:
            j = m.end()
            if j == len(s):
                break
        if ordat(s, j) == ord(']'):
            return ((OARRAY, v), j + 1)
        (o, j) = GetPDFObject(s, j)
        if o is None:
            break
        v.append(o)
    if WARN:
        print('unterminated array starting at', i)
    return ((OARRAY, v), j)


def GetPDFDict(s, i):
    """Convert and return object dict starting at s[i]."""

    j = i + 2
    v = {}
    while j < len(s):
        m = _re_pswhitespaceandcomments.match(s, j)
        if m:
            j = m.end()
            if j == len(s):
                break
        if ordat(s, j) == ord('>') and ordat(s, j + 1) == ord('>'):
            return ((ODICT, v), j + 2)
        (o, j) = GetPDFObject(s, j)
        if o is None:
            break
        if o[0] != ONAME:
            if WARN:
                print('expected name at', i)
            break
        name = o[1]
        (o, j) = GetPDFObject(s, j)
        if o is None:
            break
        v[name] = o
    if WARN:
        print('unterminated dict starting at', i)
    return ((ODICT, v), j)


def GetPDFTrailerAndCrossrefs(s):
    """Find and return the (last) PDF trailer dictionary and cross reference
    dict.

    Args:
      s: PDF file (as bytes)
    Returns:
      (trailer dict, crossref dict)
    """

    startxrefi = s.rfind(b'startxref')
    if startxrefi == -1:
        if WARN:
            print('cannot find startxref')
        return (None, None)
    crossrefi = -1
    m = _re_pseol.match(s, startxrefi + 9)
    if m:
        m2 = _re_psint.match(s, m.end())
        if m2:
            crossrefi = int(m2.group())
    if crossrefi <= 0:
        if WARN:
            print('cannot find crossref index')
        return (None, None)
    crossrefs = {}
    last_trailerdict = None
    while crossrefi > 0:
        i = crossrefi
        if s[i:i + 4] != b'xref':
            if WARN:
                print('cannot find xref')
            break
        m = _re_pseol.match(s, i + 4)
        if m:
            i = m.end()
        while i < startxrefi:
            # Get start of subsection
            (v, i) = GetPDFTwoInts(s, i)
            if v is None:
                break
            (idstart, nentries) = v
            m = _re_pswhitespaceandcomments.match(s, i)
            if m:
                i = m.end()
            for k in range(idstart, idstart + nentries):
                byteoffset = int(s[i:i + 10])
                gen = int(s[i + 11:i + 16])
                inuse = (ordat(s, i + 17) == ord('n'))
                if inuse:
                    crossrefs[(k, gen)] = byteoffset
                i += 20
        # Should be at 'trailer' now
        (w, i) = GetPDFKeyword(s, i)
        if w != b'trailer':
            if WARN:
                print('cannot find trailer')
            break
        (trailero, i) = GetPDFObject(s, i)
        if trailero is None or trailero[0] != ODICT:
            if WARN:
                print('cannot find trailer dict')
                break
        trailerdict = trailero[1]
        if last_trailerdict is None:
            last_trailerdict = trailerdict
        if 'Prev' in trailerdict:
            crossrefi = trailerdict['Prev']
        else:
            crossrefi = -1
    return (last_trailerdict, crossrefs)


def ReadPDFPageOneContents(filename):
    """Read a PDF file and return Content string for its first page.

    Args:
      filename: name of file
    Returns:
      string: Content string for first page
    """

    try:
        f = open(filename, "rb")  # binary since some parts may be compressed
    except IOError:
        if WARN:
            print("Can't open file", filename)
        return ''
    contents = f.read()
    f.close()
    return GetPDFPageOneContents(contents)


def GetPDFPageOneContents(s):
    """Find and return first page in PDF file, given as string.

    First get the last trailer's dictionary, which should contain
    the Root object, and also the crossref dictionary which gives
    byte offsets for all indirect objects.
    Then from Root object, find Pages object (a page tree), and
    follow leftmost Kid until get to a leaf Page object, which
    in turn has the desired Contents object, which is a stream
    or an array of streams. Decompress (if necessary) the
    stream(s) and return their concatenation.

    Args:
      s: bytes holding contents of a PDF file
    Returns:
      string: the decoded (possibly decompressed) contents of the first page
    """

    (trailerdict, crossrefs) = GetPDFTrailerAndCrossrefs(s)
    if not trailerdict or not crossrefs:
        if WARN:
            print('problem finding trailer or crossrefs')
        return ''
    if 'Root' not in trailerdict:
        if WARN:
            print('cannot find Root object')
        return ''
    root = GetTypedValFromDictEntry(trailerdict, 'Root', ODICT, s, crossrefs)
    if root is None:
        if WARN:
            print('cannot find root dictionary')
            return ''
    pagesdict = GetTypedValFromDictEntry(root, 'Pages', ODICT, s, crossrefs)
    if pagesdict is None:
        if WARN:
            print('cannot find Pages dictionary')
        return ''
    pnode = pagesdict
    while pnode:
        pnodetype = PDFDictType(pnode)
        if pnodetype == 'Pages':
            kidsarray = GetTypedValFromDictEntry(pnode, 'Kids', OARRAY, s,
                crossrefs)
            if not kidsarray:
                if WARN:
                    print('cannot find Kids in Pages')
                return ''
            if len(kidsarray) == 0:
                if WARN:
                    print('Kids array has no Page')
                return ''
            pnodeobj = GetPDFObjFromIndirectRef(kidsarray[0], s, crossrefs)
            if PDFObjHasType(pnodeobj, ODICT):
                pnode = pnodeobj[1]
            else:
                if WARN:
                    print('Kids element has unexpected type')
                    return ''
        elif pnodetype == 'Page':
            contentsobj = GetPDFObjFromDictEntry(pnode, 'Contents', s,
                crossrefs)
            if contentsobj is None:
                # it is legal for there to be no contents object:
                # means empty page
                if WARN:
                    print('First Page is empty')
                return ''
            if contentsobj[0] == OSTREAM:
                return GetPDFStreamContents(contentsobj, s, crossrefs)
            elif contentsobj[0] == OARRAY:
                pieces = []
                for c in contentsobj[1]:
                    if not PDFObjHasType(c, OINDIRECTREF):
                        if WARN:
                            print('Contents obj child not an indirect ref')
                        return ''
                    o = GetPDFObjFromIndirectRef(c, s, crossrefs)
                    if not PDFObjHasType(o, OSTREAM):
                        if WARN:
                            print('Contents obj child not a stream')
                        return ''
                    pieces.append(GetPDFStreamContents(o, s, crossrefs))
                return '\n'.join(pieces)
            else:
                if WARN:
                    print('Contents object has unexpected type',
                        contentsobj[0])
                return ''
        else:
            if WARN:
                print('Page tree node has unexpected type', pnodetype)
            return ''
    # shouldn't get here
    return ''


def GetPDFObjFromIndirectRef(obj, s, crossrefs):
    """Return the Object that is referred to by an indirect reference.

    Args:
      obj: (int, value) - should be (OINDIRECTREF, (obj_number, gen_number))
      s: string - contents of PDF file
      crossrefs: dict - maps (obj_number, gen_number) to byte offset in s
    Returns:
      (objectid, value) - the referred value (inside containing OINDIRECTDEF)
                          or None if there is any problem
    """

    if not PDFObjHasType(obj, OINDIRECTREF):
        return None
    key = obj[1]
    if key not in crossrefs:
        return None
    i = crossrefs[key]
    if i < 0 or i >= len(s):
        return None
    (o, _) = GetPDFObject(s, i)
    if PDFObjHasType(o, OINDIRECTDEF):
        return o[1][2]
    else:
        return None


def GetPDFObjFromDictEntry(d, entryname, s, crossrefs):
    """Return the PDF object that should be at given entry in d.

    Follow any Indirect refs until get a real object.
    """

    if entryname not in d:
        return None
    o = d[entryname]
    if PDFObjHasType(o, OINDIRECTREF):
        return GetPDFObjFromIndirectRef(o, s, crossrefs)
    else:
        return o


def GetTypedValFromDictEntry(d, entryname, ty, s, crossrefs):
    """Return the value that should be found by entry in d and have type ty."""

    o = GetPDFObjFromDictEntry(d, entryname, s, crossrefs)
    if PDFObjHasType(o, ty):
        return o[1]
    else:
        return None


def PDFObjHasType(o, ty):
    """Return True if o, a PDF Object, has type ty."""

    if o is None:
        return False
    return o[0] == ty


def PDFDictType(d):
    """Return string value of 'Type' entry in d, '' if not there."""

    if 'Type' in d:
        tyobj = d['Type']
        if PDFObjHasType(tyobj, ONAME):
            return tyobj[1]
    return ''


def GetPDFStreamContents(contentsobj, s, crossrefs):
    """Return the contents of a stream object, applying any needed filters.

    For now, only handle FlateDecode filter, and with no DecodeParms.

    Args:
      contentsobj: (OSTREAM, (dict, istart, iend))
      s: bytes - PDF file contents
      crossrefs: dict - maps (obj_number, gen_number) to byte offset in s
    Returns:
      string - the contents (decoded using default (UTF-8) decoder)
    """

    if not PDFObjHasType(contentsobj, OSTREAM):
        return None
    (d, istart, _) = contentsobj[1]
    length = GetTypedValFromDictEntry(d, 'Length', ONUM, s, crossrefs)
    if length is None:
        return ''
    ans = s[istart:istart + length]
    filterobj = GetPDFObjFromDictEntry(d, 'Filter', s, crossrefs)
    if filterobj is None:
        return ans.decode()
    filters = []
    if PDFObjHasType(filterobj, ONAME):
        filters = [filterobj[1]]
    elif PDFObjHasType(filterobj, OARRAY):
        for o in filterobj[1]:
            if PDFObjHasType(o, ONAME):
                filters.append(o[1])
    for fname in filters:
        if fname == 'FlateDecode':
            if not zlib:
                raise RuntimeError("pdf decoding requires missing zlib module")
            ans = zlib.decompress(ans)
            ans = ans.decode()
        else:
            if WARN:
                print('unhandled stream filter', fname)
            return ''
    return ans


if __name__ == "__main__":
    if len(sys.argv) == 2:
        page1contents = ReadPDFPageOneContents(sys.argv[1])
        sys.stdout.write(page1contents)
