#!/usr/bin/env python3
# Apache License, Version 2.0
# python3 -m unittest check_style_c_test.SourceCodeTest.test_whitespace_kw_indent

# ----
import os
import sys
sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..", "check_source",
    ))
# ----

import unittest

warnings = []
import check_style_c
check_style_c.print = warnings.append

# ----
parser = check_style_c.create_parser()
# dummy, not used at the moment
args = parser.parse_args(["."])
# ----

# store errors we found
errors = set()

FUNC_BEGIN = """
void func(void)
{
"""
FUNC_END = """
}"""


def test_code(code):
    warnings.clear()
    check_style_c.scan_source("test.c", code, args)
    err_found = [w.split(":", 3)[2].strip() for w in warnings]
    # print(warnings)
    return err_found


class SourceCodeTest(unittest.TestCase):

    def assertWarning(self, err_found, *errors_test):
        err_set = set(err_found)
        errors.update(err_set)
        self.assertEqual(err_set, set(errors_test))

    def test_brace_function(self):
        # --------------------------------------------------------------------
        # brace on not on newline (function)
        code = """
void func(void) {
\t/* pass */
}"""
        err_found = test_code(code)
        self.assertWarning(err_found, "E101")

        code = """
void func(void)
{
\t/* pass */
}"""
        err_found = test_code(code)
        self.assertWarning(err_found)

    def test_brace_kw_whitespace(self):
        # --------------------------------------------------------------------
        # brace has whitespace after it

        code = FUNC_BEGIN + """
\tif (1){
\t\t/* pass */
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found, "E107", "E150")

        code = FUNC_BEGIN + """
\tif (1) {
\t\t/* pass */
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found)

    def test_brace_kw_newline(self):
        # --------------------------------------------------------------------
        # brace on on newline (if, for... )

        code = FUNC_BEGIN + """
\tif (1)
\t{
\t\t/* pass */
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found, "E108")

        code = FUNC_BEGIN + """
\tif (1) {
\t\t/* pass */
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found)

        # allow preprocessor splitting newlines
        #
        # #ifdef USE_FOO
        #     if (1)
        # #endif
        #     {
        #         ...
        #     }
        #
        code = FUNC_BEGIN + """
#ifdef USE_FOO
\tif (1)
#endif
\t{
\t\t/* pass */
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found)

    def test_brace_do_while(self):
        # --------------------------------------------------------------------
        # brace on on newline do, while

        code = FUNC_BEGIN + """
\tif (1)
\t{
\t\t/* pass */
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found, "E108")

        code = FUNC_BEGIN + """
\tif (1) {
\t\t/* pass */
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found)

    def test_brace_kw_multiline(self):
        # --------------------------------------------------------------------
        # brace-multi-line

        code = FUNC_BEGIN + """
\tif (a &&
\t    b) {
\t\t/* pass */
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found, "E103", "E104")

        code = FUNC_BEGIN + """
\tif (a &&
\t    b)
\t{
\t\t/* pass */
\t}""" + FUNC_END

        err_found = test_code(code)
        self.assertWarning(err_found)

    def test_brace_indent(self):
        # --------------------------------------------------------------------
        # do {} while (1);
        code = FUNC_BEGIN + """
\tif (1) {
\t\t/* pass */
\t\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found, "E104")

        code = FUNC_BEGIN + """
\tif (1) {
\t\t/* pass */
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found)

    def test_whitespace_kw_no_parens(self):
        # --------------------------------------------------------------------
        # if MACRO {}
        code = FUNC_BEGIN + """
\tif MACRO {
\t\t/* pass */
\t\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found, "E104", "E105")

        code = FUNC_BEGIN + """
\tif (1) {
\t\t/* pass */
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found)

    def test_whitespace_kw_missing(self):
        # --------------------------------------------------------------------
        code = FUNC_BEGIN + """
\tif(1) {
\t\t/* pass */
\t\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found, "E104", "E106")

        code = FUNC_BEGIN + """
\tif (1) {
\t\t/* pass */
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found)

    def test_brace_kw_newline_missing(self):
        # --------------------------------------------------------------------
        code = FUNC_BEGIN + """
\tif (1 &&
\t    1) fn();
\telse {}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found, "E103", "E109", "E201")

        code = FUNC_BEGIN + """
\tif (1 &&
\t    1)
\t{
\t\tfn();
\t}
\telse {}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found)

    def test_brace_kw_newline_split(self):
        # --------------------------------------------------------------------
        # else
        # if () ...

        code = FUNC_BEGIN + """
\tif (1) {
\t\tfn();
\t}
\telse
\tif () {
\t\tfn();
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found, "E115")

        # Allow an exceptional case - when we have preprocessor in-between
        # #ifdef USE_FOO
        #     if (1) {
        #         fn();
        #     }
        #     else
        # #endif
        #     if (1) {
        #         fn();
        #     }
        code = FUNC_BEGIN + """
#ifdef USE_FOO
\tif (1) {
\t\tfn();
\t}
\telse
#endif
\tif () {
\t\tfn();
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found)

        code = FUNC_BEGIN + """
\tif (1) {
\t\tfn();
\t}
\telse if () {
\t\tfn();
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found)

    def test_whitespace_kw_indent(self):
        # --------------------------------------------------------------------
        code = FUNC_BEGIN + """
\tif (a &&
\t\t\tb &&
\t    c)
\t{
\t\t/* pass */
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found, "E110")

        code = FUNC_BEGIN + """
\tif (a &&
\t    b &&
\t    c)
\t{
\t\t/* pass */
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found)

    def test_switch(self):
        # --------------------------------------------------------------------
        code = FUNC_BEGIN + """
\tswitch (value) {
\t\tcase 0 :
\t\t\tcall();
\t\t\tbreak;
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found, "E132")

        code = FUNC_BEGIN + """
\tswitch (value) {
\t\tcase 0:
\t\t\tcall();
\t\t\tbreak;
\t}""" + FUNC_END
        err_found = test_code(code)
        self.assertWarning(err_found)

    def test_whitespace_operator(self):
        ab_test = (
            ("a= 1;",
             "a = 1;"),
            ("a =A;",
             "a = A;"),
            ("a = A+0;",
             "a = A + 0;"),
            ("a+= 1;",
             "a += 1;"),
            ("a*= 1;",
             "a *= 1;"),
            ("a *=1;",
             "a *= 1;"),
            ("a/= 1;",
             "a /= 1;"),
            ("a /=1;",
             "a /= 1;"),
            ("a = a?a:0;",
             "a = a ? a : 0;"),
            ("a = a?a:0;",
             "a = a ? a : 0;"),
            ("a = a?a : 0;",
             "a = a ? a : 0;"),
            ("if (a<1) { call(); }",
             "if (a < 1) { call(); }"),
            ("if (a? c : d) { call(); }",
             "if (a ? c : d) { call(); }"),
            ("if (a ?c : d) { call(); }",
             "if (a ? c : d) { call(); }"),

            # check casts don't confuse us
            ("a = 1+ (size_t)-b;",
             "a = 1 + (size_t)-b;"),
            ("a = -(int)b+1;",
             "a = -(int)b + 1;"),
            ("a = 1+ (int *)*b;",
             "a = 1 + (int *)*b;"),
        )

        for expr_fail, expr_ok in ab_test:
            code = FUNC_BEGIN + expr_fail + FUNC_END
            err_found = test_code(code)
            self.assertWarning(err_found, "E130")

            code = FUNC_BEGIN + expr_ok + FUNC_END
            err_found = test_code(code)
            self.assertWarning(err_found)


class SourceCodeTestComplete(unittest.TestCase):
    """ Check we ran all tests.
    """

    def _test_complete(self):
        # --------------------------------------------------------------------
        # Check we test all errors
        errors_uniq = set()
        with open(check_style_c.__file__, 'r', encoding='utf-8') as fh:
            import re
            # E100
            err_re_main = re.compile(r'.*\("(E\d+)"')
            # E100.0
            err_re_subv = re.compile(r'.*\("(E\d+)\.\d+"')        # --> E100
            err_re_subv_group = re.compile(r'.*\("(E\d+\.\d+)"')  # --> E100.0
            for l in fh:
                g = err_re_subv.match(l)
                if g is None:
                    g = err_re_main.match(l)
                    is_sub = False
                else:
                    is_sub = True

                if g:
                    err = g.group(1)
                    self.assertIn(err, errors)

                    # ----
                    # now check we didn't use multiple times
                    if is_sub:
                        err = err_re_subv_group.match(l).group(1)
                    self.assertNotIn(err, errors_uniq)
                    errors_uniq.add(err)


if __name__ == '__main__':
    unittest.main(exit=False)
