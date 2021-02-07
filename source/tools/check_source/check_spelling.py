#!/usr/bin/env python3

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

ONLY_ONCE = True
USE_COLOR = True

_words_visited = set()
_files_visited = set()

# Lowercase word -> suggestion list.
_suggest_map = {}

VERBOSE_CACHE = False

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


# -----------------------------------------------------------------------------
# General Utilities

def hash_of_file_and_len(fp):
    import hashlib
    with open(fp, 'rb') as fh:
        data = fh.read()
        m = hashlib.sha512()
        m.update(data)
        return m.digest(), len(data)


import re
re_vars = re.compile("[A-Za-z]+")

# First remove this from comments, so we don't spell check example code, doxygen commands, etc.
re_ignore = re.compile(
    r'('

    # URL.
    r'(https?|ftp)://\S+|'
    # Email address: <me@email.com>
    #                <someone@foo.bar-baz.com>
    r"<\w+@[\w\.\-]+>|"

    # Convention for TODO/FIXME messages: TODO(my name) OR FIXME(name+name) OR XXX(some-name) OR NOTE(name/other-name):
    r"\b(TODO|FIXME|XXX|NOTE)\([A-Za-z\s\+\-/]+\)|"

    # Doxygen style: <pre> ... </pre>
    r"<pre>.+</pre>|"
    # Doxygen style: \code ... \endcode
    r"\s+\\code\b.+\s\\endcode\b|"
    # Doxygen style #SOME_CODE.
    r'#\S+|'
    # Doxygen commands: \param foo
    r"\\(section|subsection|subsubsection|ingroup|param|page|a|see)\s+\S+|"
    # Doxygen commands without any arguments after them: \command
    r"\\(retval|todo)\b|"
    # Doxygen 'param' syntax used rarely: \param foo[in,out]
    r"\\param\[[a-z,]+\]\S*|"

    # Words containing underscores: a_b
    r'\S*\w+_\S+|'
    # Words containing arrows: a->b
    r'\S*\w+\->\S+'
    # Words containing dot notation: a.b  (NOT  ab... since this is used in English).
    r'\w+\.\w+\S*|'

    # Single and back-tick quotes (often used to reference code).
    r"\s\`[^\n`]+\`|"
    r"\s'[^\n']+'"

    r')',
    re.MULTILINE | re.DOTALL,
)
# Then extract words.
re_words = re.compile(
    r"\b("
    # Capital words, with optional '-' and "'".
    r"[A-Z]+[\-'A-Z]*[A-Z]|"
    # Lowercase words, with optional '-' and "'".
    r"[A-Za-z][\-'a-z]*[a-z]+"
    r")\b"
)

re_not_newline = re.compile("[^\n]")


def words_from_text(text):
    """ Extract words to treat as English for spell checking.
    """
    # Replace non-newlines with white-space, so all alignment is kept.
    def replace_ignore(match):
        start, end = match.span()
        return re_not_newline.sub(" ", match.string[start:end])

    # Handy for checking what we ignore, incase we ignore too much and miss real errors.
    # for match in re_ignore.finditer(text):
    #     print(match.group(0))

    # Strip out URL's, code-blocks, etc.
    text = re_ignore.sub(replace_ignore, text)

    words = []
    for match in re_words.finditer(text):
        words.append((match.group(0), match.start()))

    def word_ok(w):
        # Ignore all uppercase words.
        if w.isupper():
            return False
        return True
    words[:] = [w for w in words if word_ok(w[0])]
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

    def line_and_column_from_comment_offset(self, pos):
        text = self.text
        slineno = self.line + text.count("\n", 0, pos)
        # Allow for -1 to be not found.
        scol = text.rfind("\n", 0, pos) + 1
        if scol == 0:
            # Not found.
            scol = pos
        else:
            scol = pos - scol
        return slineno, scol


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

    slineno = 0
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
    SKIP_COMMENTS = (
        # GPL header.
        "This program is free software; you can",
    )

    # reverse these to find blocks we won't parse
    PRINT_NON_ALIGNED = False
    PRINT_SPELLING = True

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
            # Allow plurals of these variables too.
            code_words.add(match.group(0) + "'s")

    comments = []

    slineno = 0
    i_prev = 0
    for i, i_next in comment_ranges:

        ok = True
        block = text[i:i_next]
        for c in SKIP_COMMENTS:
            if c in block:
                ok = False
                break

        if not ok:
            continue

        # Add white-space in front of the block (for alignment test)
        # allow for -1 being not found, which results as zero.
        j = text.rfind("\n", 0, i) + 1
        block = (" " * (i - j)) + block

        slineno += text.count("\n", i_prev, i)
        comments.append(Comment(filepath, block, slineno, 'COMMENT'))
        i_prev = i

    return comments, code_words


def spell_check_report(filepath, report):
    w, slineno, scol = report
    w_lower = w.lower()

    if ONLY_ONCE:
        if w_lower in _words_visited:
            return
        else:
            _words_visited.add(w_lower)

    suggest = _suggest_map.get(w_lower)
    if suggest is None:
        _suggest_map[w_lower] = suggest = " ".join(dict_spelling.suggest(w))

    print("%s:%d:%d: %s%s%s, suggest (%s)" % (
        filepath,
        slineno + 1,
        scol + 1,
        COLOR_WORD,
        w,
        COLOR_ENDC,
        suggest,
    ))


def spell_check_file(filepath, check_type='COMMENTS'):
    if check_type == 'COMMENTS':
        if filepath.endswith(".py"):
            comment_list, code_words = extract_py_comments(filepath)
        else:
            comment_list, code_words = extract_c_comments(filepath)
    elif check_type == 'STRINGS':
        comment_list, code_words = extract_code_strings(filepath)

    for comment in comment_list:
        for w, pos in comment.parse():
            w_lower = w.lower()
            if w_lower in dict_custom or w_lower in dict_ignore:
                continue

            if not dict_spelling.check(w):

                # Ignore literals that show up in code,
                # gets rid of a lot of noise from comments that reference variables.
                if w in code_words:
                    # print("Skipping", w)
                    continue

                slineno, scol = comment.line_and_column_from_comment_offset(pos)
                yield (w, slineno, scol)


def spell_check_file_recursive(dirpath, check_type='COMMENTS', cache_data=None):
    import os
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
        for report in spell_check_file_with_cache_support(filepath, check_type=check_type, cache_data=cache_data):
            spell_check_report(filepath, report)


# -----------------------------------------------------------------------------
# Cache File Support
#
# Cache is formatted as follows:
# (
#     # Store all misspelled words.
#     {filepath: (size, sha512, [reports, ...])},
#
#     # Store suggestions, as these are slow to re-calculate.
#     {lowercase_words: suggestions},
# )
#

def spell_cache_read(cache_filepath):
    import pickle
    cache_data = {}, {}
    if os.path.exists(cache_filepath):
        with open(cache_filepath, 'rb') as fh:
            cache_data = pickle.load(fh)
    return cache_data


def spell_cache_write(cache_filepath, cache_data):
    import pickle
    with open(cache_filepath, 'wb') as fh:
        pickle.dump(cache_data, fh)


def spell_check_file_with_cache_support(filepath, check_type='COMMENTS', cache_data=None):
    """
    Iterator each item is a report: (word, line_number, column_number)
    """
    _files_visited.add(filepath)

    if cache_data is None:
        yield from spell_check_file(filepath, check_type=check_type)
        return

    cache_data_for_file = cache_data.get(filepath)
    if cache_data_for_file and len(cache_data_for_file) != 3:
        cache_data_for_file = None

    cache_hash_test, cache_len_test = hash_of_file_and_len(filepath)
    if cache_data_for_file is not None:
        cache_len, cache_hash, cache_reports = cache_data_for_file
        if cache_len_test == cache_len:
            if cache_hash_test == cache_hash:
                if VERBOSE_CACHE:
                    print("Using cache for:", filepath)
                yield from cache_reports
                return

    cache_reports = []
    for report in spell_check_file(filepath, check_type=check_type):
        cache_reports.append(report)

    cache_data[filepath] = (cache_len_test, cache_hash_test, cache_reports)

    yield from cache_reports


# -----------------------------------------------------------------------------
# Extract Bad Spelling from a Source File


# -----------------------------------------------------------------------------
# Main & Argument Parsing

def argparse_create():
    import argparse

    # When --help or no args are given, print this help
    description = __doc__
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        '--extract',
        dest='extract',
        choices=('COMMENTS', 'STRINGS'),
        default='COMMENTS',
        required=False,
        metavar='WHAT',
        help=(
            'Text to extract for checking.\n'
            '\n'
            '- ``COMMENTS`` extracts comments from source code.\n'
            '- ``STRINGS`` extracts text.'
        ),
    )

    parser.add_argument(
        "--cache-file",
        dest="cache_file",
        help=(
            "Optional cache, for fast re-execution, "
            "avoiding re-extracting spelling when files have not been modified."
        ),
        required=False,
    )

    parser.add_argument(
        "paths",
        nargs='+',
        help="Files or directories to walk recursively.",
    )

    return parser


def main():
    global _suggest_map

    import os

    args = argparse_create().parse_args()

    check_type = args.extract
    cache_filepath = args.cache_file

    cache_data = None
    if cache_filepath:
        cache_data, _suggest_map = spell_cache_read(cache_filepath)
        clear_stale_cache = True

    # print(check_type)
    try:
        for filepath in args.paths:
            if os.path.isdir(filepath):
                # recursive search
                spell_check_file_recursive(filepath, check_type=check_type, cache_data=cache_data)
            else:
                # single file
                for report in spell_check_file_with_cache_support(
                        filepath, check_type=check_type, cache_data=cache_data):
                    spell_check_report(filepath, report)
    except KeyboardInterrupt:
        clear_stale_cache = False

    if cache_filepath:
        if VERBOSE_CACHE:
            print("Writing cache:", len(cache_data))

        if clear_stale_cache:
            # Don't keep suggestions for old misspellings.
            _suggest_map = {w_lower: _suggest_map[w_lower] for w_lower in _words_visited}

            for filepath in list(cache_data.keys()):
                if filepath not in _files_visited:
                    del cache_data[filepath]

        spell_cache_write(cache_filepath, (cache_data, _suggest_map))


if __name__ == "__main__":
    main()
