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

"""
Script for checking source code spelling.

   python3 source/tools/check_source/check_spelling_c.py some_soure_file.py


Currently only python source is checked.
"""

import os
PRINT_QTC_TASKFORMAT = False
if "USE_QTC_TASK" in os.environ:
    PRINT_QTC_TASKFORMAT = True

ONLY_ONCE = True
USE_COLOR = True
_only_once_ids = set()

if USE_COLOR:
    COLOR_WORD = "\033[92m"
    COLOR_ENDC = "\033[0m"
else:
    COLOR_WORD = ""
    COLOR_ENDC = ""


import enchant
dict_spelling = enchant.Dict("en_US")

from check_spelling_c_config import (
    dict_custom,
    dict_ignore,
)


def words_from_text(text):
    """ Extract words to treat as English for spell checking.
    """
    text = text.strip("#'\"")
    text = text.replace("/", " ")
    text = text.replace("-", " ")
    text = text.replace("+", " ")
    text = text.replace("%", " ")
    text = text.replace(",", " ")
    text = text.replace("=", " ")
    text = text.replace("|", " ")
    words = text.split()

    # filter words
    words[:] = [w.strip("*?!:;.,'\"`") for w in words]

    def word_ok(w):
        # check for empty string
        if not w:
            return False

        # ignore all uppercase words
        if w.isupper():
            return False

        # check for string with no characters in it
        is_alpha = False
        for c in w:
            if c.isalpha():
                is_alpha = True
                break
        if not is_alpha:
            return False

        # check for prefix/suffix which render this not a real word
        # example '--debug', '\n'
        # TODO, add more
        if w[0] in "%-+\\@":
            return False

        # check for code in comments
        for c in r"<>{}[]():._0123456789\&*":
            if c in w:
                return False

        # check for words which contain lower case but have upper case
        # ending chars eg - 'StructRNA', we can ignore these.
        if len(w) > 1:
            has_lower = False
            for c in w:
                if c.islower():
                    has_lower = True
                    break
            if has_lower and (not w[1:].islower()):
                return False

        return True
    words[:] = [w for w in words if word_ok(w)]

    # text = " ".join(words)

    # print(text)
    return words


class Comment:
    __slots__ = (
        "file",
        "text",
        "line",
        "type",
    )

    def __init__(self, file, text, line, type):
        self.file = file
        self.text = text
        self.line = line
        self.type = type

    def parse(self):
        return words_from_text(self.text)


def extract_py_comments(filepath):

    import token
    import tokenize

    source = open(filepath, encoding='utf-8')

    comments = []

    prev_toktype = token.INDENT

    tokgen = tokenize.generate_tokens(source.readline)
    for toktype, ttext, (slineno, scol), (elineno, ecol), ltext in tokgen:
        if toktype == token.STRING and prev_toktype == token.INDENT:
            comments.append(Comment(filepath, ttext, slineno, 'DOCSTRING'))
        elif toktype == tokenize.COMMENT:
            # non standard hint for commented CODE that we can ignore
            if not ttext.startswith("#~"):
                comments.append(Comment(filepath, ttext, slineno, 'COMMENT'))
        prev_toktype = toktype
    return comments


def extract_c_comments(filepath):
    """
    Extracts comments like this:

        /*
         * This is a multi-line comment, notice the '*'s are aligned.
         */
    """
    i = 0
    text = open(filepath, encoding='utf-8').read()

    BEGIN = "/*"
    END = "*/"
    TABSIZE = 4
    SINGLE_LINE = False
    STRIP_DOXY = True
    STRIP_DOXY_DIRECTIVES = (
        r"\section",
        r"\subsection",
        r"\subsubsection",
        r"\ingroup",
        r"\param[in]",
        r"\param[out]",
        r"\param[in,out]",
        r"\param",
        r"\page",
    )
    SKIP_COMMENTS = (
        "BEGIN GPL LICENSE BLOCK",
    )

    # http://doc.qt.nokia.com/qtcreator-2.4/creator-task-lists.html#task-list-file-format
    # file\tline\ttype\tdescription
    # ... > foobar.tasks

    # reverse these to find blocks we won't parse
    PRINT_NON_ALIGNED = False
    PRINT_SPELLING = True

    def strip_doxy_comments(block_split):

        for i, l in enumerate(block_split):
            for directive in STRIP_DOXY_DIRECTIVES:
                if directive in l:
                    l_split = l.split()
                    l_split[l_split.index(directive) + 1] = " "
                    l = " ".join(l_split)
                    del l_split
                    break
            block_split[i] = l

    comments = []

    while i >= 0:
        i = text.find(BEGIN, i)
        if i != -1:
            i_next = text.find(END, i)
            if i_next != -1:

                # not essential but seek ack to find beginning of line
                while i > 0 and text[i - 1] in {"\t", " "}:
                    i -= 1

                block = text[i:i_next + len(END)]

                # add whitespace in front of the block (for alignment test)
                ws = []
                j = i
                while j > 0 and text[j - 1] != "\n":
                    ws .append("\t" if text[j - 1] == "\t" else " ")
                    j -= 1
                ws.reverse()
                block = "".join(ws) + block

                ok = True

                if not (SINGLE_LINE or ("\n" in block)):
                    ok = False

                if ok:
                    for c in SKIP_COMMENTS:
                        if c in block:
                            ok = False
                            break

                if ok:
                    # expand tabs
                    block_split = [l.expandtabs(TABSIZE) for l in block.split("\n")]

                    # now validate that the block is aligned
                    align_vals = tuple(sorted(set([l.find("*") for l in block_split])))
                    is_aligned = len(align_vals) == 1

                    if is_aligned:
                        if PRINT_SPELLING:
                            if STRIP_DOXY:
                                strip_doxy_comments(block_split)

                            align = align_vals[0] + 1
                            block = "\n".join([l[align:] for l in block_split])[:-len(END)]

                            # now strip block and get text
                            # print(block)

                            # ugh - not nice or fast
                            slineno = 1 + text.count("\n", 0, i)

                            comments.append(Comment(filepath, block, slineno, 'COMMENT'))
                    else:
                        if PRINT_NON_ALIGNED:
                            lineno = 1 + text.count("\n", 0, i)
                            if PRINT_QTC_TASKFORMAT:
                                filepath = os.path.abspath(filepath)
                                print("%s\t%d\t%s\t%s" % (filepath, lineno, "comment", align_vals))
                            else:
                                print(filepath + ":" + str(lineno) + ":")

            i = i_next
        else:
            pass

    return comments


def spell_check_comments(filepath):

    if filepath.endswith(".py"):
        comment_list = extract_py_comments(filepath)
    else:
        comment_list = extract_c_comments(filepath)

    for comment in comment_list:
        for w in comment.parse():
            # if len(w) < 15:
            #     continue

            w_lower = w.lower()
            if w_lower in dict_custom or w_lower in dict_ignore:
                continue

            if not dict_spelling.check(w):

                if ONLY_ONCE:
                    if w_lower in _only_once_ids:
                        continue
                    else:
                        _only_once_ids.add(w_lower)

                if PRINT_QTC_TASKFORMAT:
                    print("%s\t%d\t%s\t%s, suggest (%s)" %
                          (comment.file,
                           comment.line,
                           "comment",
                           w,
                           " ".join(dict_spelling.suggest(w)),
                           ))
                else:
                    print("%s:%d: %s%s%s, suggest (%s)" %
                          (comment.file,
                           comment.line,
                           COLOR_WORD,
                           w,
                           COLOR_ENDC,
                           " ".join(dict_spelling.suggest(w)),
                           ))


def spell_check_comments_recursive(dirpath):
    from os.path import join, splitext

    def source_list(path, filename_check=None):
        for dirpath, dirnames, filenames in os.walk(path):
            # skip '.git'
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]

            for filename in filenames:
                filepath = join(dirpath, filename)
                if filename_check is None or filename_check(filepath):
                    yield filepath

    def is_source(filename):
        ext = splitext(filename)[1]
        return (ext in {
            ".c",
            ".inl",
            ".cpp",
            ".cxx",
            ".hpp",
            ".hxx",
            ".h",
            ".hh",
            ".m",
            ".mm",
            ".osl",
            ".py",
        })

    for filepath in source_list(dirpath, is_source):
        spell_check_comments(filepath)


import sys
import os

if __name__ == "__main__":
    for filepath in sys.argv[1:]:
        if os.path.isdir(filepath):
            # recursive search
            spell_check_comments_recursive(filepath)
        else:
            # single file
            spell_check_comments(filepath)
