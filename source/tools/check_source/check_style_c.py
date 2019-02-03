#!/usr/bin/env python3

# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Contributor(s): Campbell Barton
#
# #**** END GPL LICENSE BLOCK #****

# <pep8 compliant>

"""
This script runs outside of blender and scans source

   python3 source/tools/check_source/check_style_c.py source/

"""

import os
import re

from check_style_c_config import IGNORE, IGNORE_DIR, SOURCE_DIR, TAB_SIZE, LIN_SIZE
IGNORE = tuple([os.path.join(SOURCE_DIR, ig) for ig in IGNORE])
IGNORE_DIR = tuple([os.path.join(SOURCE_DIR, ig) for ig in IGNORE_DIR])
WARN_TEXT = False


def is_ignore(f):
    for ig in IGNORE:
        if f == ig:
            return True
    for ig in IGNORE_DIR:
        if f.startswith(ig):
            return True
    return False


def hash_of_file(fp):
    import hashlib
    with open(fp, 'rb') as fh:
        return hashlib.sha512(fh.read()).digest()


# TODO
#
# Add checks for:
# - macro brace use
# - line length - in a not-too-annoying way
#   (allow for long arrays in struct definitions, PyMethodDef for eg)

from pygments import lex  # highlight
from pygments.lexers import CLexer
# from pygments.formatters import RawTokenFormatter

from pygments.token import Token

import argparse

PRINT_QTC_TASKFORMAT = False
if "USE_QTC_TASK" in os.environ:
    PRINT_QTC_TASKFORMAT = True


global filepath
tokens = []


# could store index here too, then have prev/next methods
class TokStore:
    __slots__ = (
        "type",
        "text",
        "line",
        "flag",
    )

    def __init__(self, type, text, line):
        self.type = type
        self.text = text
        self.line = line
        self.flag = 0


# flags
IS_CAST = (1 << 0)


def tk_range_to_str(a, b, expand_tabs=False):
    txt = "".join([tokens[i].text for i in range(a, b + 1)])
    if expand_tabs:
        txt = txt.expandtabs(TAB_SIZE)
    return txt


def tk_item_is_newline(tok):
    return tok.type == Token.Text and tok.text.strip("\t ") == "\n"


def tk_item_is_ws_newline(tok):
    return (tok.text == "") or \
           (tok.type == Token.Text and tok.text.isspace()) or \
           (tok.type in Token.Comment)


def tk_item_is_ws(tok):
    return (tok.text == "") or \
           (tok.type == Token.Text and tok.text.strip("\t ") != "\n" and tok.text.isspace()) or \
           (tok.type in Token.Comment)


# also skips comments
def tk_advance_ws(index, direction):
    while tk_item_is_ws(tokens[index + direction]) and index > 0:
        index += direction
    return index


def tk_advance_no_ws(index, direction):
    index += direction
    while tk_item_is_ws(tokens[index]) and index > 0:
        index += direction
    return index


def tk_advance_ws_newline(index, direction):
    while tk_item_is_ws_newline(tokens[index + direction]) and index > 0:
        index += direction
    return index + direction


def tk_advance_line_start(index):
    """ Go the the first non-whitespace token of the line.
    """
    while tokens[index].line == tokens[index - 1].line and index > 0:
        index -= 1
    return tk_advance_no_ws(index, 1)


def tk_advance_line(index, direction):
    line = tokens[index].line
    while tokens[index + direction].line == line or tokens[index].text == "\n":
        index += direction
    return index


def tk_advance_to_token(index, direction, text, type_):
    """ Advance to a token.
    """
    index += direction
    while True:
        if (tokens[index].text == text) and (tokens[index].type == type_):
            return index
        index += direction
    return None


def tk_advance_line_to_token(index, direction, text, type_):
    """ Advance to a token (on the same line).
    """
    assert(isinstance(text, str))
    line = tokens[index].line
    index += direction
    while tokens[index].line == line:
        if (tokens[index].text == text) and (tokens[index].type == type_):
            return index
        index += direction
    return None


def tk_advance_line_to_token_with_fn(index, direction, text, fn):
    """ Advance to a token (on the same line).
    """
    assert(isinstance(text, str))
    line = tokens[index].line
    index += direction
    while tokens[index].line == line:
        if (tokens[index].text == text) and fn(tokens[index]):
            return index
        index += direction
    return None


def tk_advance_flag(index, direction, flag):
    state = (tokens[index].flag & flag)
    while ((tokens[index + direction].flag) & flag == state) and index > 0:
        index += direction
    return index


def tk_match_backet(index):
    backet_start = tokens[index].text
    assert(tokens[index].type == Token.Punctuation)
    assert(backet_start in "[]{}()")

    if tokens[index].text in "({[":
        direction = 1
        backet_end = {"(": ")", "[": "]", "{": "}"}[backet_start]
    else:
        direction = -1
        backet_end = {")": "(", "]": "[", "}": "{"}[backet_start]

    level = 1
    index_match = index + direction
    while True:
        item = tokens[index_match]
        # For checking odd braces:
        # print(filepath, tokens[index].line, item.line)
        if item.type == Token.Punctuation:
            if item.text == backet_start:
                level += 1
            elif item.text == backet_end:
                level -= 1
                if level == 0:
                    break

        index_match += direction

    return index_match


def tk_index_is_linestart(index):
    index_prev = tk_advance_ws_newline(index, -1)
    return tokens[index_prev].line < tokens[index].line


def extract_to_linestart(index):
    ls = []
    line = tokens[index].line
    index -= 1
    while index > 0 and tokens[index].line == line:
        ls.append(tokens[index].text)
        index -= 1

    if index != 0:
        ls.append(tokens[index].text.rsplit("\n", 1)[1])

    ls.reverse()
    return "".join(ls)


def extract_ws_indent(index):
    # could optimize this
    text = extract_to_linestart(index)
    return text[:len(text) - len(text.lstrip("\t"))]


def extract_statement_if(fn, index_kw):
    # assert(tokens[index_kw].text == "if")

    # ignore preprocessor
    i_linestart = tk_advance_line_start(index_kw)
    if tokens[i_linestart].text.startswith("#"):
        return None

    # seek back
    # i = index_kw

    i_start = tk_advance_ws(index_kw - 1, direction=-1)

    # seek forward
    i_next = tk_advance_ws_newline(index_kw, direction=1)

    # print(tokens[i_next])

    if tokens[i_next].type != Token.Punctuation or tokens[i_next].text != "(":
        warning(fn, "E105", "no '(' after '%s'" % tokens[index_kw].text, i_start, i_next)
        return None

    i_end = tk_match_backet(i_next)

    return (i_start, i_end)


def extract_operator(index_op):
    op_text = ""
    i = 0
    while tokens[index_op + i].type == Token.Operator:
        op_text += tokens[index_op + i].text
        i += 1
    return op_text, index_op + (i - 1)


def extract_cast(index):
    # to detect a cast is quite involved... sigh
    # assert(tokens[index].text == "(")

    # TODO, comment within cast, but that's rare
    i_start = index
    i_end = tk_match_backet(index)

    # first check we are not '()'
    if i_start + 1 == i_end:
        return None

    # check we have punctuation before the cast
    i = i_start - 1
    while tokens[i].text.isspace():
        i -= 1

    # avoids  'foo(bar)test'
    # but not ' = (bar)test'
    if tokens[i].type == Token.Keyword:
        # allow 'return (bar)test'
        if tokens[i].text != "return":
            return None
    elif tokens[i].type == Token.Name:
        return None

    # validate types
    tokens_cast = [tokens[i] for i in range(i_start + 1, i_end)]
    for t in tokens_cast:
        if t.type == Token.Keyword:
            # allow: '(struct FooBar)'
            if t.text not in {"const", "struct"}:
                return None
        elif t.type == Token.Operator and t.text != "*":
            # prevent '(a + b)'
            # note, we could have '(float(*)[1+2])' but this is unlikely
            return None
        elif t.type == Token.Punctuation and t.text not in '()[]':
            # prevent '(a, b)'
            return None
    tokens_cast_strip = []
    for t in tokens_cast:
        if t.type in Token.Comment:
            pass
        elif t.type == Token.Text and t.text.isspace():
            pass
        elif t.type == Token.Keyword and t.text in {"const", "struct"}:
            pass
        elif t.type == Token.Keyword.Type and tokens_cast_strip and tokens_cast_strip[-1].type == Token.Keyword.Type:
            # ignore chained types `signed char`, `unsigned int`... etc.
            tokens_cast_strip[-1] = t
        else:
            tokens_cast_strip.append(t)
    # check token order and types
    if not tokens_cast_strip:
        return None
    if tokens_cast_strip[0].type not in {Token.Name, Token.Type, Token.Keyword.Type}:
        return None
    t_prev = None
    for t in tokens_cast_strip[1:]:
        # prevent identifiers after the first: '(a b)'
        if t.type in {Token.Keyword.Type, Token.Name, Token.Text}:
            return None
        # prevent: '(a * 4)'
        # allow:   '(a (*)[4])'
        if t_prev is not None and t_prev.text == "*" and t.type != Token.Punctuation:
            return None
        t_prev = t
    del t_prev

    # debug only
    '''
    string = "".join(tokens[i].text for i in range(i_start, i_end + 1))
    #string = "".join(tokens[i].text for i in range(i_start + 1, i_end))
    #types = [tokens[i].type for i in range(i_start + 1, i_end)]
    types = [t.type for t in tokens_cast_strip]

    print("STRING:", string)
    print("TYPES: ", types)
    print()
    '''

    # Set the cast flags, so other checkers can use
    for i in range(i_start, i_end + 1):
        tokens[i].flag |= IS_CAST

    return (i_start, i_end)


def tk_range_find_by_type(index_start, index_end, type_, filter_tk=None):
    if index_start < index_end:
        for i in range(index_start, index_end + 1):
            if tokens[i].type == type_:
                if filter_tk is None or filter_tk(tokens[i]):
                    return i
    return -1


def warning(fn, id_, message, index_kw_start, index_kw_end):
    if PRINT_QTC_TASKFORMAT:
        fn("%s\t%d\t%s\t%s %s" % (filepath, tokens[index_kw_start].line, "comment", id_, message))
    else:
        fn("%s:%d: %s: %s" % (filepath, tokens[index_kw_start].line, id_, message))
        if WARN_TEXT:
            fn(tk_range_to_str(index_kw_start, index_kw_end, expand_tabs=True))


def warning_lineonly(fn, id_, message, line):
    if PRINT_QTC_TASKFORMAT:
        fn("%s\t%d\t%s\t%s %s" % (filepath, line, "comment", id_, message))
    else:
        fn("%s:%d: %s: %s" % (filepath, line, id_, message))

    # print(tk_range_to_str(index_kw_start, index_kw_end))


# ------------------------------------------------------------------
# Own Blender rules here!

def blender_check_kw_if(fn, index_kw_start, index_kw, index_kw_end):

    # check if we have: 'if('
    if not tk_item_is_ws(tokens[index_kw + 1]):
        warning(fn, "E106", "no white space between '%s('" % tokens[index_kw].text, index_kw_start, index_kw_end)

    # check for: ){
    index_next = tk_advance_ws_newline(index_kw_end, 1)
    if tokens[index_next].type == Token.Punctuation and tokens[index_next].text == "{":
        if not tk_item_is_ws_newline(tokens[index_next - 1]):
            warning(fn, "E107", "no white space between trailing bracket '%s (){'" %
                    tokens[index_kw].text, index_kw_start, index_kw_end)

        # check for: if ()
        #            {
        # note: if the if statement is multi-line we allow it
        if ((tokens[index_kw].line == tokens[index_kw_end].line) and
                (tokens[index_kw].line == tokens[index_next].line - 1)):

            if ((tokens[index_kw].line + 1 != tokens[index_next].line) and
                (tk_range_find_by_type(index_kw + 1, index_next - 1, Token.Comment.Preproc,
                                       filter_tk=lambda tk: tk.text in {
                                           "if", "ifdef", "ifndef", "else", "elif", "endif"}) != -1)):

                # allow this to go unnoticed
                pass
            else:
                warning(fn, "E108", "if body brace on a new line '%s ()\\n{'" %
                        tokens[index_kw].text, index_kw, index_kw_end)
    else:
        # no '{' on a multi-line if
        if tokens[index_kw].line != tokens[index_kw_end].line:
            # double check this is not...
            # if (a &&
            #     b); <--
            #
            # While possible but not common for 'if' statements, it's used in this example:
            #
            # do {
            #     foo;
            # } while(a &&
            #         b);
            #
            if not (tokens[index_next].type == Token.Punctuation and tokens[index_next].text == ";"):
                warning(fn, "E109", "multi-line if should use a brace '%s (\\n\\n) statement;'" %
                        tokens[index_kw].text, index_kw, index_kw_end)

        # check for correct single line use & indentation
        if not (tokens[index_next].type == Token.Punctuation and tokens[index_next].text == ";"):
            if tokens[index_next].type == Token.Keyword and tokens[index_next].text in {"if", "while", "for"}:
                ws_kw = extract_ws_indent(index_kw)
                ws_end = extract_ws_indent(index_next)
                if len(ws_kw) + 1 != len(ws_end):
                    # check for:
                    # #ifdef FOO
                    #     if (a)
                    # #else
                    #     if (b)
                    # endif
                    #     { ...
                    #
                    has_sep = False
                    if len(ws_kw) == len(ws_end):
                        for i in range(index_kw + 1, index_next):
                            if tokens[i].type == Token.Comment.Preproc:
                                has_sep = True
                                break
                    if not has_sep:
                        warning(fn, "E200", "bad single line indent '%s (...) {'" %
                                tokens[index_kw].text, index_kw, index_next)
                    del has_sep
                del ws_kw, ws_end
            else:
                index_end = tk_advance_to_token(index_next, 1, ";", Token.Punctuation)
                if tokens[index_kw].line != tokens[index_end].line:
                    # check for:
                    # if (a)
                    # b;
                    #
                    # should be:
                    #
                    # if (a)
                    #     b;
                    ws_kw = extract_ws_indent(index_kw)
                    ws_end = extract_ws_indent(index_end)
                    if len(ws_kw) + 1 != len(ws_end):
                        warning(fn, "E201", "bad single line indent '%s (...) {'" %
                                tokens[index_kw].text, index_kw, index_end)
                    del ws_kw, ws_end
                del index_end

    # multi-line statement
    if (tokens[index_kw].line != tokens[index_kw_end].line):
        # check for: if (a &&
        #                b) { ...
        # brace should be on a newline.
        #
        if tokens[index_kw_end].line == tokens[index_next].line:
            if not (tokens[index_next].type == Token.Punctuation and tokens[index_next].text == ";"):
                warning(fn, "E103", "multi-line should use a on a new line '%s (\\n\\n) {'" %
                        tokens[index_kw].text, index_kw, index_kw_end)

        # Note: this could be split into its own function
        # since it's not specific to if-statements,
        # can also work for function calls.
        #
        # check indentation on a multi-line statement:
        # if (a &&
        # b)
        # {
        #
        # should be:
        # if (a &&
        #     b)
        # {

        # Skip the first token
        # Extract '    if ('  then convert to
        #         '        '  and check lines for correct indent.
        index_kw_bracket = tk_advance_ws_newline(index_kw, 1)
        ws_indent = extract_to_linestart(index_kw_bracket + 1)
        ws_indent = "".join([("\t" if c == "\t" else " ") for c in ws_indent])
        l_last = tokens[index_kw].line
        for i in range(index_kw + 1, index_kw_end + 1):
            if tokens[i].line != l_last:
                l_last = tokens[i].line
                # ignore blank lines
                if tokens[i].text == "\n":
                    pass
                elif tokens[i].text.startswith("#"):
                    pass
                else:

                    # check indentation is good
                    # use startswith because there are function calls within 'if' checks sometimes.
                    ws_indent_test = extract_to_linestart(i + 1)
                    # print("indent: %r   %s" % (ws_indent_test, tokens[i].text))
                    # if ws_indent_test != ws_indent:

                    if ws_indent_test.startswith(ws_indent):
                        pass
                    elif tokens[i].text.startswith(ws_indent):
                        # needed for some comments
                        pass
                    else:
                        warning(fn, "E110", "if body brace mult-line indent mismatch", i, i)
        del index_kw_bracket
        del ws_indent
        del l_last

    # check for: if () { ... };
    #
    # no need to have semicolon after brace.
    if tokens[index_next].text == "{":
        index_final = tk_match_backet(index_next)
        index_final_step = tk_advance_no_ws(index_final, 1)
        if tokens[index_final_step].text == ";":
            warning(fn, "E111", "semi-colon after brace '%s () { ... };'" %
                    tokens[index_kw].text, index_final_step, index_final_step)


def blender_check_kw_else(fn, index_kw):
    # for 'else if' use the if check.
    i_next = tk_advance_ws_newline(index_kw, 1)

    # check there is at least one space between:
    # else{
    if index_kw + 1 == i_next:
        warning(fn, "E112", "else has no space between following brace 'else{'", index_kw, i_next)

    # check if there are more than 1 spaces after else, but nothing after the following brace
    # else     {
    #     ...
    #
    # check for this case since this is needed sometimes:
    # else     { a = 1; }
    if ((tokens[index_kw].line == tokens[i_next].line) and
            (tokens[index_kw + 1].type == Token.Text) and
            (len(tokens[index_kw + 1].text) > 1) and
            (tokens[index_kw + 1].text.isspace())):

        # check if the next data after { is on a newline
        i_next_next = tk_advance_ws_newline(i_next, 1)
        if tokens[i_next].line != tokens[i_next_next].line:
            warning(fn, "E113", "unneeded whitespace before brace 'else ... {'", index_kw, i_next)

    # this check only tests for:
    # else
    # {
    # ... which is never OK
    #
    # ... except if you have
    # else
    # #preprocessor
    # {

    if tokens[i_next].type == Token.Punctuation and tokens[i_next].text == "{":
        if tokens[index_kw].line < tokens[i_next].line:
            # check for preproc
            i_newline = tk_advance_line(index_kw, 1)
            if tokens[i_newline].text.startswith("#"):
                pass
            else:
                warning(fn, "E114", "else body brace on a new line 'else\\n{'", index_kw, i_next)

    # this check only tests for:
    # else
    # if
    # ... which is never OK
    if tokens[i_next].type == Token.Keyword and tokens[i_next].text == "if":
        if tokens[index_kw].line < tokens[i_next].line:
            # allow for:
            #     ....
            #     else
            # #endif
            #     if
            if ((tokens[index_kw].line + 1 != tokens[i_next].line) and
                any(True for i in range(index_kw + 1, i_next)
                    if (tokens[i].type == Token.Comment.Preproc and
                        tokens[i].text.lstrip("# \t").startswith((
                            "if", "ifdef", "ifndef",
                            "else", "elif", "endif",
                        ))
                        )
                    )):

                # allow this to go unnoticed
                pass

            if ((tokens[index_kw].line + 1 != tokens[i_next].line) and
                (tk_range_find_by_type(index_kw + 1, i_next - 1, Token.Comment.Preproc,
                                       filter_tk=lambda tk: tk.text in {
                                           "if", "ifdef", "ifndef", "else", "elif", "endif", }) != -1)):
                # allow this to go unnoticed
                pass
            else:
                warning(fn, "E115", "else if is split by a new line 'else\\nif'", index_kw, i_next)

    # check
    # } else
    # ... which is never OK
    i_prev = tk_advance_no_ws(index_kw, -1)
    if tokens[i_prev].type == Token.Punctuation and tokens[i_prev].text == "}":
        if tokens[index_kw].line == tokens[i_prev].line:
            warning(fn, "E116", "else has no newline before the brace '} else'", i_prev, index_kw)


def blender_check_kw_switch(fn, index_kw_start, index_kw, index_kw_end):
    # In this function we check the body of the switch

    # switch (value) {
    # ...
    # }

    # assert(tokens[index_kw].text == "switch")

    index_next = tk_advance_ws_newline(index_kw_end, 1)

    if tokens[index_next].type == Token.Punctuation and tokens[index_next].text == "{":
        ws_switch_indent = extract_to_linestart(index_kw)

        if ws_switch_indent.isspace():

            # 'case' should have at least 1 indent.
            # otherwise expect 2 indent (or more, for nested switches)
            ws_test = {
                "case": ws_switch_indent + "\t",
                "default:": ws_switch_indent + "\t",

                "break": ws_switch_indent + "\t\t",
                "return": ws_switch_indent + "\t\t",
                "continue": ws_switch_indent + "\t\t",
                "goto": ws_switch_indent + "\t\t",
            }

            index_final = tk_match_backet(index_next)

            for i in range(index_next + 1, index_final):
                # 'default' is seen as a label
                # print(tokens[i].type, tokens[i].text)
                if tokens[i].type in {Token.Keyword, Token.Name.Label}:
                    if tokens[i].text in {"case", "default:", "break", "return", "continue", "goto"}:
                        ws_other_indent = extract_to_linestart(i)
                        # non ws start - we ignore for now, allow case A: case B: ...
                        if ws_other_indent.isspace():
                            ws_test_other = ws_test[tokens[i].text]
                            if not ws_other_indent.startswith(ws_test_other):
                                warning(fn, "E117", "%s is not indented enough" % tokens[i].text, i, i)

                        if tokens[i].text == "case":
                            # while where here, check:
                            #     case ABC :
                            # should be...
                            #     case ABC:

                            # Note, this might be either 'Punctuation' or 'Operator', we need to check both.
                            i_case = tk_advance_line_to_token_with_fn(
                                i, 1, ":",
                                lambda t: t.type in {Token.Punctuation, Token.Operator})
                            # can be None when the identifier isn't an 'int'
                            if i_case is not None:
                                if tokens[i_case - 1].text.isspace():
                                    warning(fn, "E132", "%s space before colon" % tokens[i].text, i, i_case)
                            del i_case

        else:
            warning(fn, "E119", "switch isn't the first token in the line", index_kw_start, index_kw_end)
    else:
        warning(fn, "E120", "switch brace missing", index_kw_start, index_kw_end)


def blender_check_kw_sizeof(fn, index_kw):
    if tokens[index_kw + 1].text != "(":
        warning(fn, "E121", "expected '%s('" % tokens[index_kw].text, index_kw, index_kw + 1)


def blender_check_cast(fn, index_kw_start, index_kw_end):
    # detect: '( float...'
    if tokens[index_kw_start + 1].text.isspace():
        warning(fn, "E122", "cast has space after first bracket '( type...'", index_kw_start, index_kw_end)
    # detect: '...float )'
    if tokens[index_kw_end - 1].text.isspace():
        warning(fn, "E123", "cast has space before last bracket '... )'", index_kw_start, index_kw_end)
    # detect no space before operator: '(float*)'

    for i in range(index_kw_start + 1, index_kw_end):
        if tokens[i].text == "*":
            # allow: '(*)'
            if tokens[i - 1].type == Token.Punctuation:
                pass
            elif tokens[i - 1].text.isspace():
                pass
            else:
                warning(fn, "E124", "cast has no preceding whitespace '(type*)'", index_kw_start, index_kw_end)


def blender_check_comma(fn, index_kw):
    i_next = tk_advance_ws_newline(index_kw, 1)

    # check there is at least one space between:
    # ,sometext
    if index_kw + 1 == i_next:
        # allow: (struct FooBar){ .a, .b, .c,}
        if tokens[i_next].text != "}":
            warning(fn, "E125", "comma has no space after it ',sometext'", index_kw, i_next)

    if tokens[index_kw - 1].type == Token.Text and tokens[index_kw - 1].text.isspace():
        warning(fn, "E126", "comma space before it 'sometext ,", index_kw, i_next)


def blender_check_period(fn, index_kw):
    # check we're now apart of ...
    if (tokens[index_kw - 1].text == ".") or (tokens[index_kw + 1].text == "."):
        return

    # 'a.b'
    if tokens[index_kw - 1].type == Token.Text and tokens[index_kw - 1].text.isspace():
        # C99 allows struct members to be declared as follows:
        # struct FooBar = { .a = 1, .b = 2, };
        # ... check for this case by allowing comma or brace beforehand.
        i_prev = tk_advance_ws_newline(index_kw - 1, -1)
        if tokens[i_prev].text not in {",", "{"}:
            warning(fn, "E127", "period space before it 'sometext .", index_kw, index_kw)
    if tokens[index_kw + 1].type == Token.Text and tokens[index_kw + 1].text.isspace():
        warning(fn, "E128", "period space after it '. sometext", index_kw, index_kw)


def _is_ws_pad(index_start, index_end):
    return (tokens[index_start - 1].text.isspace() and
            tokens[index_end + 1].text.isspace())


def blender_check_operator(fn, index_start, index_end, op_text, is_cpp):
    if op_text == "->":
        # allow compiler to handle
        return

    if len(op_text) == 1:
        if op_text in {"+", "-"}:
            # detect (-a) vs (a - b)
            index_prev = index_start - 1
            if (tokens[index_prev].text.isspace() and
                    tokens[index_prev - 1].flag & IS_CAST):
                index_prev -= 1
            if tokens[index_prev].flag & IS_CAST:
                index_prev = tk_advance_flag(index_prev, -1, IS_CAST)

            if not (
                    tokens[index_prev].text.isspace() or
                    (tokens[index_prev].text in {"[", "(", "{"}) or
                    # Allow: (uint)-1
                    # Or:    (struct FooBar)&var
                    (tokens[index_prev].flag & IS_CAST)
            ):
                warning(fn, "E130", "no space before operator '%s'" % op_text, index_start, index_end)
            if (not tokens[index_end + 1].text.isspace() and
                    tokens[index_end + 1].text not in {"]", ")", "}"}):
                # TODO, needs work to be useful
                # warning(fn, "E130", "no space after operator '%s'" % op_text, index_start, index_end)
                pass

        elif op_text in {"/", "%", "^", "|", "=", "<", ">", "?"}:
            if not _is_ws_pad(index_start, index_end):
                if not (is_cpp and ("<" in op_text or ">" in op_text)):
                    warning(fn, "E130", "no space around operator '%s'" % op_text, index_start, index_end)
        elif op_text == ":":
            # check we're not
            #     case 1:
            #
            # .. somehow 'case A:' doesn't suffer from this problem.
            #
            # note, it looks like this may be a quirk in pygments, how it handles 'default' too.
            if not (tokens[index_start - 1].text.isspace() or tokens[index_start - 1].text == "default"):
                i_case = tk_advance_line_to_token(index_start, -1, "case", Token.Keyword)
                if i_case is None:
                    warning(fn, "E130", "no space around operator '%s'" % op_text, index_start, index_end)
        elif op_text == "&":
            pass  # TODO, check if this is a pointer reference or not
        elif op_text == "*":

            index_prev = index_start - 1
            if (tokens[index_prev].text.isspace() and
                    tokens[index_prev - 1].flag & IS_CAST):
                index_prev -= 1
            if tokens[index_prev].flag & IS_CAST:
                index_prev = tk_advance_flag(index_prev, -1, IS_CAST)

            # This check could be improved, it's a bit fuzzy
            if ((tokens[index_start - 1].flag & IS_CAST) or
                    (tokens[index_start + 1].flag & IS_CAST)):
                # allow:
                #     a = *(int *)b;
                # and:
                #     b = (int *)*b;
                pass
            elif ((tokens[index_start - 1].type in Token.Number) or
                    (tokens[index_start + 1].type in Token.Number)):
                warning(fn, "E130", "no space around operator '%s'" % op_text, index_start, index_end)
            elif not (tokens[index_start - 1].text.isspace() or tokens[index_start - 1].text in {"(", "[", "{"}):
                warning(fn, "E130", "no space before operator '%s'" % op_text, index_start, index_end)
    elif len(op_text) == 2:
        # todo, remove operator check from `if`
        if op_text in {"+=", "-=", "*=", "/=", "&=", "|=", "^=",
                       "&&", "||",
                       "==", "!=", "<=", ">=",
                       "<<", ">>",
                       "%=",
                       # not operators, pointer mix-ins
                       ">*", "<*", "-*", "+*", "=*", "/*", "%*", "^*", "|*",
                       }:
            if not _is_ws_pad(index_start, index_end):
                if not (is_cpp and ("<" in op_text or ">" in op_text)):
                    warning(fn, "E130", "no space around operator '%s'" % op_text, index_start, index_end)

        elif op_text in {"++", "--"}:
            pass  # TODO, figure out the side we are adding to!
            '''
            if     (tokens[index_start - 1].text.isspace() or
                    tokens[index_end   + 1].text.isspace()):
                warning(fn, "E130", "spaces surrounding operator '%s'" % op_text, index_start, index_end)
            '''
        elif op_text in {"!!", "!*"}:
            # operators we _dont_ want whitespace after (pointers mainly)
            # we can assume these are pointers
            if tokens[index_end + 1].text.isspace():
                warning(fn, "E130", "spaces after operator '%s'" % op_text, index_start, index_end)

        elif op_text == "**":
            pass  # handle below
        elif op_text == "::":
            pass  # C++, ignore for now
        elif op_text == ":!*":
            pass  # ignore for now
        elif op_text == "*>":
            pass  # ignore for now, C++ <Class *>
        else:
            warning(fn, "E000.0", "unhandled operator 2 '%s'" % op_text, index_start, index_end)
    elif len(op_text) == 3:
        if op_text in {">>=", "<<="}:
            if not _is_ws_pad(index_start, index_end):
                if not (is_cpp and ("<" in op_text or ">" in op_text)):
                    warning(fn, "E130", "no space around operator '%s'" % op_text, index_start, index_end)
        elif op_text == "***":
            pass
        elif op_text in {"*--", "*++"}:
            pass
        elif op_text in {"--*", "++*"}:
            pass
        elif op_text == ">::":
            pass
        elif op_text == "::~":
            pass
        else:
            warning(fn, "E000.1", "unhandled operator 3 '%s'" % op_text, index_start, index_end)
    elif len(op_text) == 4:
        if op_text == "*>::":
            pass
        else:
            warning(fn, "E000.2", "unhandled operator 4 '%s'" % op_text, index_start, index_end)
    else:
        warning(fn, "E000.3", "unhandled operator (len > 4) '%s'" % op_text, index_start, index_end)

    if len(op_text) > 1:
        if op_text[0] == "*" and op_text[-1] == "*":
            if ((not tokens[index_start - 1].text.isspace()) and
                    (not tokens[index_start - 1].type == Token.Punctuation)):
                warning(fn, "E130", "no space before pointer operator '%s'" % op_text, index_start, index_end)
            if tokens[index_end + 1].text.isspace():
                warning(fn, "E130", "space before pointer operator '%s'" % op_text, index_start, index_end)

    # check if we are first in the line
    if op_text[0] == "!":
        # if (a &&
        #     !b)
        pass
    elif op_text[0] == "*" and tokens[index_start + 1].text.isspace() is False:
        pass  # *a = b
    elif len(op_text) == 1 and op_text[0] == "-" and tokens[index_start + 1].text.isspace() is False:
        pass  # -1
    elif len(op_text) == 2 and op_text == "++" and tokens[index_start + 1].text.isspace() is False:
        pass  # ++a
    elif len(op_text) == 2 and op_text == "--" and tokens[index_start + 1].text.isspace() is False:
        pass  # --a
    elif len(op_text) == 1 and op_text[0] == "&":
        # if (a &&
        #     &b)
        pass
    elif len(op_text) == 1 and op_text[0] == "~":
        # C++
        # ~ClassName
        pass
    elif len(op_text) == 1 and op_text[0] == "?":
        # (a == b)
        # ? c : d
        pass
    elif len(op_text) == 1 and op_text[0] == ":":
        # a = b ? c
        #      : d
        pass
    else:
        if tk_index_is_linestart(index_start):
            warning(fn, "E143", "operator starts a new line '%s'" % op_text, index_start, index_end)


def blender_check_linelength(fn, index_start, index_end, length):
    if length > LIN_SIZE:
        text = tk_range_to_str(index_start, index_end, expand_tabs=True)
        for l in text.split("\n"):
            if len(l) > LIN_SIZE:
                warning(fn, "E144", "line length %d > %d" % (len(l), LIN_SIZE), index_start, index_end)


def blender_check_function_definition(fn, i):
    # Warning, this is a fairly slow check and guesses
    # based on some fuzzy rules

    # assert(tokens[index].text == "{")

    # check function declaration is not:
    #  'void myfunc() {'
    # ... other uses are handled by checks for statements
    # this check is rather simplistic but tends to work well enough.

    i_prev = i - 1
    while tokens[i_prev].text == "":
        i_prev -= 1

    # ensure this isn't '{' in its own line
    if tokens[i_prev].line == tokens[i].line:

        # check we '}' isn't on same line...
        i_next = i + 1
        found = False
        while tokens[i_next].line == tokens[i].line:
            if tokens[i_next].text == "}":
                found = True
                break
            i_next += 1
        del i_next

        if found is False:

            # First check this isn't an assignment
            i_prev = tk_advance_no_ws(i, -1)
            # avoid '= {'
            # if tokens(index_prev).text != "="
            # print(tokens[i_prev].text)
            # allow:
            # - 'func()[] {'
            # - 'func() {'

            if tokens[i_prev].text in {")", "]"}:
                i_prev = i - 1
                while tokens[i_prev].line == tokens[i].line:
                    i_prev -= 1
                split = tokens[i_prev].text.rsplit("\n", 1)
                if len(split) > 1 and split[-1] != "":
                    split_line = split[-1]
                else:
                    split_line = tokens[i_prev + 1].text

                if split_line and split_line[0].isspace():
                    pass
                else:
                    # no whitespace!
                    i_begin = i_prev + 1

                    # skip blank
                    if tokens[i_begin].text == "":
                        i_begin += 1
                    # skip static
                    if tokens[i_begin].text == "static":
                        i_begin += 1
                    while tokens[i_begin].text.isspace():
                        i_begin += 1
                    # now we are done skipping stuff

                    warning(fn, "E101", "function's '{' must be on a newline", i_begin, i)


def blender_check_brace_indent(fn, i):
    # assert(tokens[index].text == "{")

    i_match = tk_match_backet(i)

    if tokens[i].line != tokens[i_match].line:
        ws_i_match = extract_to_linestart(i_match)

        # allow for...
        # a[] = {1, 2,
        #        3, 4}
        # ... so only check braces which are the first text
        if ws_i_match.isspace():
            ws_i = extract_to_linestart(i)
            ws_i_match_lstrip = ws_i_match.lstrip()

            ws_i = ws_i[:len(ws_i) - len(ws_i.lstrip())]
            ws_i_match = ws_i_match[:len(ws_i_match) - len(ws_i_match_lstrip)]
            if ws_i != ws_i_match:
                warning(fn, "E104", "indentation '{' does not match brace", i, i_match)


def quick_check_includes(fn, lines):
    # Find overly relative headers (could check other things here too...)

    # header dupes
    inc = set()

    base = os.path.dirname(filepath)
    match = quick_check_includes.re_inc_match
    for i, l in enumerate(lines):
        m = match(l)
        if m is not None:
            l_header = m.group(1)

            # check if the include is overly relative
            if l_header.startswith("../") and 0:
                l_header_full = os.path.join(base, l_header)
                l_header_full = os.path.normpath(l_header_full)
                if os.path.exists(l_header_full):
                    l_header_rel = os.path.relpath(l_header_full, base)
                    if l_header.count("/") != l_header_rel.count("/"):
                        warning_lineonly(fn, "E170", "overly relative include %r" % l_header, i + 1)

            # check if we're in mode than once
            len_inc = len(inc)
            inc.add(l_header)
            if len(inc) == len_inc:
                warning_lineonly(fn, "E171", "duplicate includes %r" % l_header, i + 1)


quick_check_includes.re_inc_match = re.compile(r"\s*#\s*include\s+\"([a-zA-Z0-9_\-\.\/]+)\"").match


def quick_check_indentation(fn, lines):
    """
    Quick check for multiple tab indents.
    """
    t_prev = -1
    ls_prev = ""

    ws_prev = ""
    ws_prev_expand = ""

    for i, l in enumerate(lines):
        skip = False

        # skip blank lines
        ls = l.strip()

        # comment or pre-processor
        if ls:
            # #ifdef ... or ... // comment
            if ls[0] == "#":

                # check preprocessor indentation here
                # basic rules, NEVER INDENT
                # just need to check multi-line macros.
                if l[0] != "#":
                    # we have indent, check previous line
                    if not ls_prev.rstrip().endswith("\\"):
                        # report indented line
                        warning_lineonly(
                            fn, "E145", "indentation found with preprocessor "
                            "(expected none or after '#')", i + 1)

                skip = True
            if ls[0:2] == "//":
                skip = True
            # label:
            elif (':' in ls and l[0] != '\t'):
                skip = True
            # /* comment */
            # ~ elif ls.startswith("/*") and ls.endswith("*/"):
            # ~     skip = True
            # /* some comment...
            elif ls.startswith("/*"):
                skip = True
            # line ending a comment: */
            elif ls == "*/":
                skip = True
            # * middle of multi line comment block
            elif ls.startswith("* "):
                skip = True
            # exclude muli-line defines
            elif ls.endswith("\\") or ls.endswith("(void)0") or ls_prev.endswith("\\"):
                skip = True

        ls_prev = ls

        if skip:
            continue

        if ls:
            ls = l.lstrip("\t")
            tabs = l[:len(l) - len(ls)]
            t = len(tabs)
            if (t > t_prev + 1) and (t_prev != -1):
                warning_lineonly(
                    fn, "E146", "indentation mismatch (indent of %d) '%s'" %
                    (t - t_prev, tabs), i + 1)
            t_prev = t

            # check for same indentation with different space/tab mix
            ws = l[:len(l) - len(l.lstrip())]
            ws_expand = ws.expandtabs(4)
            if ws_expand == ws_prev_expand:
                if ws != ws_prev:
                    warning_lineonly(
                        fn, "E152", "indentation tab/space mismatch",
                        i + 1)
            ws_prev = ws
            ws_prev_expand = ws_expand


import re
re_ifndef = re.compile(r"^\s*#\s*ifndef\s+([A-z0-9_]+).*$")
re_define = re.compile(r"^\s*#\s*define\s+([A-z0-9_]+).*$")


def quick_check_include_guard(fn, lines):
    # found = 0
    def_value = ""
    ok = False

    def fn_as_guard(fn):
        name = os.path.basename(fn).upper().replace(".", "_").replace("-", "_")
        return "__%s__" % name

    for i, l in enumerate(lines):
        ndef_match = re_ifndef.match(l)
        if ndef_match:
            ndef_value = ndef_match.group(1).strip()
            for j in range(i + 1, len(lines)):
                l_next = lines[j]
                def_match = re_define.match(l_next)
                if def_match:
                    def_value = def_match.group(1).strip()
                    if def_value == ndef_value:
                        ok = True
                        break
                elif l_next.strip():
                    # print(filepath)
                    # found non empty non ndef line. quit
                    break
                else:
                    # allow blank lines
                    pass
            break

    guard = fn_as_guard(filepath)

    if ok:
        # print("found:", def_value, "->", filepath)
        if def_value != guard:
            # print("%s: %s -> %s" % (filepath, def_value, guard))
            warning_lineonly(
                fn, "E147", "non-conforming include guard (found %r, expected %r)" %
                (def_value, guard), i + 1)
    else:
        warning_lineonly(
            fn, "E148", "missing include guard %r" % guard, 1)


def quick_check_source(fp, code, args, fn):

    global filepath

    is_header = fp.endswith((".h", ".hxx", ".hpp"))

    filepath = fp

    lines = code.split("\n")

    if is_header:
        quick_check_include_guard(fn, lines)

    quick_check_includes(fn, lines)

    quick_check_indentation(fn, lines)


def scan_source(fp, code, args, fn):
    # print("scanning: %r" % fp)

    global filepath

    is_cpp = fp.endswith((".cpp", ".cxx"))

    filepath = fp

    # if "displist.c" not in filepath:
    #     return

    filepath_base = os.path.basename(filepath)
    filepath_split = filepath.split(os.sep)

    # print(highlight(code, CLexer(), RawTokenFormatter()).decode('utf-8'))

    del tokens[:]
    line = 1

    for ttype, text in lex(code, CLexer()):
        if text:
            tokens.append(TokStore(ttype, text, line))
            line += text.count("\n")

    col = 0  # track line length
    index_line_start = 0

    for i, tok in enumerate(tokens):
        # print(tok.type, tok.text)
        if tok.type == Token.Keyword:
            if tok.text in {"switch", "while", "if", "for"}:
                item_range = extract_statement_if(fn, i)
                if item_range is not None:
                    blender_check_kw_if(fn, item_range[0], i, item_range[1])
                if tok.text == "switch":
                    blender_check_kw_switch(fn, item_range[0], i, item_range[1])
            elif tok.text == "else":
                blender_check_kw_else(fn, i)
            elif tok.text == "sizeof":
                blender_check_kw_sizeof(fn, i)
        elif tok.type == Token.Punctuation:
            if tok.text == ",":
                blender_check_comma(fn, i)
            elif tok.text == ".":
                blender_check_period(fn, i)
            elif tok.text == "[":
                # note, we're quite relaxed about this but
                # disallow 'foo ['
                if tokens[i - 1].text.isspace():
                    if is_cpp and tokens[i + 1].text == "]":
                        # c++ can do delete []
                        pass
                    else:
                        warning(fn, "E149", "space before '['", i, i)
            elif tok.text == "(":
                # check if this is a cast, eg:
                #  (char), (char **), (float (*)[3])
                item_range = extract_cast(i)
                if item_range is not None:
                    blender_check_cast(fn, item_range[0], item_range[1])
            elif tok.text == "{":
                # check matching brace is indented correctly (slow!)
                blender_check_brace_indent(fn, i)

                # check previous character is either a '{' or whitespace.
                if ((tokens[i - 1].line == tok.line) and
                            not (tokens[i - 1].text.isspace() or
                                 tokens[i - 1].text == "{" or
                                 tokens[i - 1].flag & IS_CAST)
                        ):
                    warning(fn, "E150", "no space before '{'", i, i)

                blender_check_function_definition(fn, i)

        elif tok.type == Token.Operator:
            # we check these in pairs, only want first
            if tokens[i - 1].type != Token.Operator:
                op, index_kw_end = extract_operator(i)
                blender_check_operator(fn, i, index_kw_end, op, is_cpp)
        elif tok.type in Token.Comment:
            doxyfn = None
            if "\\file" in tok.text:
                doxyfn = tok.text.split("\\file", 1)[1].strip().split()[0]
            elif "@file" in tok.text:
                doxyfn = tok.text.split("@file", 1)[1].strip().split()[0]

            if doxyfn is not None:
                doxyfn_base = os.path.basename(doxyfn)
                if doxyfn_base != filepath_base:
                    warning(fn, "E151", "doxygen filename mismatch %s != %s" % (doxyfn_base, filepath_base), i, i)
                doxyfn_split = doxyfn.split("/")
                if len(doxyfn_split) > 1:
                    fp_split = filepath_split[-len(doxyfn_split):]
                    if doxyfn_split != fp_split:
                        warning(fn, "E151", "doxygen filepath mismatch %s != %s" % (doxyfn, "/".join(fp_split)), i, i)
                    del fp_split
                del doxyfn_base, doxyfn_split
            del doxyfn

        # ensure line length
        if (not args.no_length_check) and tok.type == Token.Text and tok.text == "\n":
            # check line len
            blender_check_linelength(fn, index_line_start, i - 1, col)

            col = 0
            index_line_start = i + 1
        else:
            col += len(tok.text.expandtabs(TAB_SIZE))

        # elif tok.type == Token.Name:
        #    print(tok.text)

        # print(ttype, type(ttype))
        # print((ttype, value))

    # for ttype, value in la:
    #    #print(value, end="")


def scan_source_filepath__cached(filepath, args, fn, cache):
    cache_files_src, cache_files_dst = cache
    h_code = hash_of_file(filepath)
    info_src = cache_files_src.get(filepath)
    if info_src is not None and info_src[0] == h_code:
        for a in info_src[1]:
            fn(*a)
        cache_files_dst[filepath] = info_src
        return None
    else:
        lines = []
        info_dst = (h_code, lines)
        def fn_wrap(*a):
            fn_wrap.lines.append(a)
            fn_wrap.fn(*a)
        fn_wrap.fn = fn
        fn_wrap.lines = lines
        cache_files_dst[filepath] = info_dst
        return cache_files_src, cache_files_dst, fn_wrap


def scan_source_filepath(filepath, args, fn, cache=None):
    # for quick tests
    # ~ if not filepath.endswith("creator.c"):
    # ~     return

    code = open(filepath, 'r', encoding="utf-8").read()

    if cache:
        cache_result = scan_source_filepath__cached(filepath, args, fn, cache)
        if cache_result is None:
            # No need to ececute
            return
        else:
            cache_files_src, cache_files_dst, fn = cache_result
        del cache_result

    # fast checks which don't require full parsing
    quick_check_source(filepath, code, args, fn)

    # use lexer
    scan_source(filepath, code, args, fn)


def scan_source_recursive(dirpath, args, fn, cache=None):
    import os
    from os.path import join, splitext

    def source_list(path, filename_check=None):
        for dirpath, dirnames, filenames in os.walk(path):
            # skip '.git'
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]

            for filename in filenames:
                # avoid scanning backup files
                if not filename.startswith("."):
                    filepath = join(dirpath, filename)
                    if filename_check is None or filename_check(filepath):
                        yield filepath

    def is_source(filename):
        # skip temp files
        if filename.startswith("."):
            return False
        ext = splitext(filename)[1]
        return (ext in {".c", ".inl", ".cpp", ".cxx", ".cc", ".hpp", ".hxx", ".h", ".hh", ".osl"})

    for filepath in sorted(source_list(dirpath, is_source)):
        if is_ignore(filepath):
            continue

        scan_source_filepath(filepath, args, fn, cache)


def create_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Check C/C++ code for conformance with blenders style guide:\n"
            "http://wiki.blender.org/index.php/Dev:Doc/CodeStyle)")
    )
    parser.add_argument(
        "paths",
        nargs='+',
        help="list of files or directories to check",
    )
    parser.add_argument(
        "-l",
        "--no-length-check",
        action="store_true",
        help="skip warnings for long lines",
    )
    return parser


def main(argv=None):
    import sys
    import os

    # For cache
    import pickle

    if argv is None:
        argv = sys.argv[1:]

    parser = create_parser()
    args = parser.parse_args(argv)
    del argv

    print("Scanning:", SOURCE_DIR)


    if 0:
        # SOURCE_DIR = os.path.normpath(
        #     os.path.abspath(os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))))
        # scan_source_recursive(os.path.join(SOURCE_DIR, "source", "blender", "bmesh"))
        scan_source_recursive(os.path.join(SOURCE_DIR, "source/blender/makesrna/intern"), args)
        sys.exit(0)

    cache_filename = os.environ.get("CHECK_STYLE_C_CACHE", "")
    if cache_filename:
        if os.path.exists(cache_filename):
            with open(cache_filename, 'rb') as fh:
                (hash_of_script_src, cache_files_src) = pickle.load(fh)
        else:
            hash_of_script_src = b''

        cache_files_dst = {}
        hash_of_script_dst = hash_of_file(__file__)
        # If we change the Python code, ignore old cache.
        if hash_of_script_src != hash_of_script_dst:
            cache_files_src = {}
        cache = (cache_files_src, cache_files_dst)
    else:
        cache = None

    for filepath in args.paths:
        if os.path.isdir(filepath):
            # recursive search
            scan_source_recursive(filepath, args, print, cache)
        else:
            # single file
            scan_source_filepath(filepath, args, print, cache)


    if cache_filename:
        with open(cache_filename, 'wb') as fh:
            pickle.dump((hash_of_script_dst, cache_files_dst), fh)


if __name__ == "__main__":
    main()
