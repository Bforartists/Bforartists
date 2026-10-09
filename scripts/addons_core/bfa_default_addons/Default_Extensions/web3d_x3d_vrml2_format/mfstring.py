# SPDX-FileCopyrightText: 2025 Vincent Marchetti
#
# SPDX-License-Identifier: GPL-3.0-or-later

__all__ = ['encode', 'decode']

import logging
logger = logging.getLogger("mfstring")
logger.addHandler( logging.NullHandler() )
logger.setLevel( logging.WARN )

"""
The `_ONLY_WARN_ON_ERRORS_` flag controls error handling for invalid SFString or MFString encodings.

- If `False` (default), an invalid encoding raises an exception.
- If `True`, no exception is raised; instead, a warning is logged.

This is useful for tolerant X3D importers that process MFString encodings with invalid SFString items without failing.
However, setting `_ONLY_WARN_ON_ERRORS_ = True` does not guarantee a meaningful decoded value —
its sole purpose is to prevent exceptions.
"""
_ONLY_WARN_ON_ERRORS_ = True

"""
Python (targeting 3.7) implementation of the rules for
encoding X3D MFString values into a single unicode string.
"""

BACKSLASH=u"\u005C"   # unicode REVERSE_SOLIDUS, the \ character
QUOTE_MARK= u"\u0022" # double quotes "
SPACE=u" "
ITEM_SEPARATORS = u", \n\r\t" # allowed without warning between list items

from io import StringIO

class SlashEncodingError(ValueError):
    "Exception thrown when an a string cannot be slash-decoded"

    def __init__(self,xString, *tups, **keyw):
        """initialize SlashEncodingError

        xString: the unicode string that fails as argument to slash_decoding
        """
        self.encodedString = xString
        Exception.__init__(self,xString, *tups, **keyw)

    def __str__(self):
        return "invalid slash-encoded value: {%s}" % (self.encodedString)

class ListEncodingError(ValueError):
    "Exception thrown when an a string cannot be decoded as a list of strings"
    def __init__(self,xString, *tups, **keyw):
        """initialize ListEncodingError

        xString : the unicode string that fails as argument to decoding
        """
        Exception.__init__(self,xString, *tups, **keyw)

    def __str__(self):
        return "invalid slash-encoded value: {%s}" % self.args[0]


def slash_encode(aString):
    """Applies escaping to backslash and quote character

    Applied to elements of an MFString collection to allow the complete
    list to be encoded as a space delimited list of strings enclosed in unescaped quotes

    This method is exposed for the purpose of testing. It is applied to the
    elements of an MFString as part of the encode function. Users of this module will
    not have to call this function.

    aString : arbitrary unicode string
    return :  unicode string with \ --> \\ ; " --> \" replacements
    """
    rv=StringIO()
    for c in aString:
        if c==BACKSLASH or c==QUOTE_MARK:
            rv.write(BACKSLASH)
        rv.write(c)
    return rv.getvalue()


def slash_decode(xString):
    """Reverses the slash_encoding

    This method is exposed for the purpose of testing. It is applied to the
    elements of an MFString as part of the decode function. Users of this module will
    not have to call this function.

    xString : a unicode string that is the result of an application of the slash_encode algorithm
    returns : The string that would be encoded to xString
    """
    logger.debug("slash_decode: %r" % (xString,))
    rv = StringIO()
    it = iter(xString)

    for c in it:
        if c == BACKSLASH:
            try:
                next_char = next(it)
                if next_char not in {BACKSLASH, QUOTE_MARK}:
                    raise SlashEncodingError(xString)
                rv.write(next_char)
            except StopIteration:
                raise SlashEncodingError(xString)
        else:
            rv.write(c)

    return rv.getvalue()



def encode(aList):
    """Encode a list of unicode strings to a single unicode string

    aList: a sequence of unicode strings
    returns: a unicode string
    """
    slash_encoded_items = [slash_encode(s) for s in aList ]
    quoted_items = ['"%s"' % item for item in slash_encoded_items]
    return SPACE.join(quoted_items)



def decode(mfstring_enc):
    """Decode unicode string into a list of unicode strings

    This method is to be applied to the normalized attribute value, the
    result of appluing the algorithm specified in the section 3.3.3 of the
    XML reference document
    https://www.w3.org/TR/2008/REC-xml-20081126/#AVNormalize

    mfstring_enc : A unicode string, the result of the application of the encode function
    returns : Python list of unicode strings
    """
    ret_val = []
    ix_start = None
    in_quotes = False
    escaping = False

    for ix, c in enumerate(mfstring_enc):
        if in_quotes:
            if c == QUOTE_MARK and not escaping:
                try:
                    ret_val.append(slash_decode(mfstring_enc[ix_start:ix]))
                except SlashEncodingError as exc:
                    if _ONLY_WARN_ON_ERRORS_:
                        logger.warning(str(exc))
                        ret_val.append(mfstring_enc[ix_start:ix])
                    else:
                        raise
                in_quotes = False
            escaping = (c == BACKSLASH) and not escaping
        else:
            if c == QUOTE_MARK:
                in_quotes = True
                escaping = False
                ix_start = ix + 1
            elif c not in ITEM_SEPARATORS:
                msg = f"Unexpected character {c!r} between MFString items"
                if _ONLY_WARN_ON_ERRORS_:
                    logger.warning(msg)
                else:
                    raise ListEncodingError(msg)

    if in_quotes:
        msg = "Encoded MFString not terminated by an unescaped quote"
        if _ONLY_WARN_ON_ERRORS_:
            logger.warning(msg)
        else:
            raise ListEncodingError(msg)

    return ret_val
