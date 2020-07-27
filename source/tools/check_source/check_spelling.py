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

   python3 source/tools/check_source/check_spelling.py some_soure_file.py

- Pass in a path for it to be checked recursively.
- Pass in '--strings' to check strings instead of comments.

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


import re
re_vars = re.compile("[A-Za-z]+")
re_url = re.compile(r'(https?|ftp)://\S+')

def words_from_text(text):
    """ Extract words to treat as English for spell checking.
    """

    # Strip out URL's.
    text = re_url.sub(" ", text)

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


def extract_code_strings(filepath):
    import pygments
    from pygments import lexers
    from pygments.token import Token

    comments = []
    code_words = set()

    # lex = lexers.find_lexer_class_for_filename(filepath)
    # if lex is None:
    #     return comments, code_words
    if filepath.endswith(".py"):
        lex = lexers.get_lexer_by_name("python")
    else:
        lex = lexers.get_lexer_by_name("c")

    slineno = 1
    with open(filepath, encoding='utf-8') as fh:
        source = fh.read()

    for ty, ttext in lex.get_tokens(source):
        if ty in {Token.Literal.String, Token.Literal.String.Double, Token.Literal.String.Single}:
            comments.append(Comment(filepath, ttext, slineno, 'STRING'))
        else:
            for match in re_vars.finditer(ttext):
                code_words.add(match.group(0))
        # Ugh - not nice or fast.
        slineno += ttext.count("\n")

    return comments, code_words


def extract_py_comments(filepath):

    import token
    import tokenize

    source = open(filepath, encoding='utf-8')

    comments = []
    code_words = set()

    prev_toktype = token.INDENT

    tokgen = tokenize.generate_tokens(source.readline)
    for toktype, ttext, (slineno, scol), (elineno, ecol), ltext in tokgen:
        if toktype == token.STRING:
            if prev_toktype == token.INDENT:
                comments.append(Comment(filepath, ttext, slineno, 'DOCSTRING'))
        elif toktype == tokenize.COMMENT:
            # non standard hint for commented CODE that we can ignore
            if not ttext.startswith("#~"):
                comments.append(Comment(filepath, ttext, slineno, 'COMMENT'))
        else:
            for match in re_vars.finditer(ttext):
                code_words.add(match.group(0))

        prev_toktype = toktype
    return comments, code_words


def extract_c_comments(filepath):
    """
    Extracts comments like this:

        /*
         * This is a multi-line comment, notice the '*'s are aligned.
         */
    """
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

    comment_ranges = []

    i = 0
    while i != -1:
        i = text.find(BEGIN, i)
        if i != -1:
            i_next = text.find(END, i)
            if i_next != -1:
                # Not essential but seek back to find beginning of line.
                while i > 0 and text[i - 1] in {"\t", " "}:
                    i -= 1
                i_next += len(END)
                comment_ranges.append((i, i_next))
            i = i_next
        else:
            pass

    # Collect variables from code, so we can reference variables from code blocks
    # without this generating noise from the spell checker.

    code_ranges = []
    if not comment_ranges:
        code_ranges.append((0, len(text)))
    else:
        for index in range(len(comment_ranges) + 1):
            if index == 0:
                i_prev = 0
            else:
                i_prev = comment_ranges[index - 1][1]

            if index == len(comment_ranges):
                i_next = len(text)
            else:
                i_next = comment_ranges[index][0]

            code_ranges.append((i_prev, i_next))

    code_words = set()

    for i, i_next in code_ranges:
        for match in re_vars.finditer(text[i:i_next]):
            code_words.add(match.group(0))

    comments = []

    for i, i_next in comment_ranges:
        block = text[i:i_next]

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

    return comments, code_words


def spell_check_file(filepath, check_type='COMMENTS'):

    if check_type == 'COMMENTS':
        if filepath.endswith(".py"):
            comment_list, code_words = extract_py_comments(filepath)
        else:
            comment_list, code_words = extract_c_comments(filepath)
    elif check_type == 'STRINGS':
        comment_list, code_words = extract_code_strings(filepath)

    for comment in comment_list:
        for w in comment.parse():
            # if len(w) < 15:
            #     continue

            w_lower = w.lower()
            if w_lower in dict_custom or w_lower in dict_ignore:
                continue

            if not dict_spelling.check(w):

                # Ignore literals that show up in code,
                # gets rid of a lot of noise from comments that reference variables.
                if w in code_words:
                    # print("Skipping", w)
                    continue

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


def spell_check_file_recursive(dirpath, check_type='COMMENTS'):
    from os.path import join, splitext

    def source_list(path, filename_check=None):
        for dirpath, dirnames, filenames in os.walk(path):
            # skip '.git'
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for filename in filenames:
                if filename.startswith("."):
                    continue
                filepath = join(dirpath, filename)
                if filename_check is None or filename_check(filepath):
                    yield filepath

    def is_source(filename):
        ext = splitext(filename)[1]
        return (ext in {
            ".c",
            ".cc",
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
        spell_check_file(filepath, check_type=check_type)


import sys
import os

if __name__ == "__main__":
    # TODO, use argparse to expose more options.
    args = sys.argv[1:]
    try:
        args.remove("--strings")
        check_type = 'STRINGS'
    except ValueError:
        check_type = 'COMMENTS'

    print(check_type)
    for filepath in args:
        if os.path.isdir(filepath):
            # recursive search
            spell_check_file_recursive(filepath, check_type=check_type)
        else:
            # single file
            spell_check_file(filepath, check_type=check_type)
