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

# <pep8-80 compliant>

"""
Example:
  ./source/tools/utils/code_clean.py /src/cmake_debug --match ".*/editmesh_.*" --fix=use_const_vars

Note: currently this is limited to paths in "source/" and "intern/",
we could change this if it's needed.
"""

import re
import subprocess
import sys
import os

USE_MULTIPROCESS = True

VERBOSE = False

# Print the output of the compiler (_very_ noisy, only useful for troubleshooting compiler issues).
VERBOSE_COMPILER = False


# -----------------------------------------------------------------------------
# General Utilities

# Note that we could use a hash, however there is no advantage, compare it's contents.
def file_as_bytes(filename):
    with open(filename, 'rb') as fh:
        return fh.read()


def line_from_span(text, start, end):
    while start > 0 and text[start - 1] != '\n':
        start -= 1
    while end < len(text) and text[end] != '\n':
        end += 1
    return text[start:end]


# -----------------------------------------------------------------------------
# Execution Wrappers

def run(args, *, quiet):
    if VERBOSE_COMPILER and not quiet:
        out = sys.stdout
    else:
        out = subprocess.DEVNULL

    import shlex
    p = subprocess.Popen(shlex.split(args), stdout=out, stderr=out)
    p.wait()
    return p.returncode


# -----------------------------------------------------------------------------
# Build System Access

def cmake_cache_var(cmake_dir, var):
    cache_file = open(os.path.join(cmake_dir, "CMakeCache.txt"), encoding='utf-8')
    lines = [l_strip for l in cache_file for l_strip in (l.strip(),)
             if l_strip if not l_strip.startswith("//") if not l_strip.startswith("#")]
    cache_file.close()

    for l in lines:
        if l.split(":")[0] == var:
            return l.split("=", 1)[-1]
    return None


RE_CFILE_SEARCH = re.compile(r"\s\-c\s([\S]+)")


def process_commands(cmake_dir, data):
    compiler_c = cmake_cache_var(cmake_dir, "CMAKE_C_COMPILER")
    compiler_cxx = cmake_cache_var(cmake_dir, "CMAKE_CXX_COMPILER")
    file_args = []

    for l in data:
        if (
                (compiler_c in l) or
                (compiler_cxx in l)
        ):
            # Extract:
            #   -c SOME_FILE
            c_file_search = re.search(RE_CFILE_SEARCH, l)
            if c_file_search is not None:
                c_file = c_file_search.group(1)
                file_args.append((c_file, l))
            else:
                # could print, NO C FILE FOUND?
                pass

    file_args.sort()

    return file_args


def find_build_args_ninja(build_dir):
    cmake_dir = build_dir
    make_exe = "ninja"
    process = subprocess.Popen(
        [make_exe, "-t", "commands"],
        stdout=subprocess.PIPE,
        cwd=build_dir,
    )
    while process.poll():
        time.sleep(1)

    out = process.stdout.read()
    process.stdout.close()
    # print("done!", len(out), "bytes")
    data = out.decode("utf-8", errors="ignore").split("\n")
    return process_commands(cmake_dir, data)


def find_build_args_make(build_dir):
    make_exe = "make"
    process = subprocess.Popen(
        [make_exe, "--always-make", "--dry-run", "--keep-going", "VERBOSE=1"],
        stdout=subprocess.PIPE,
        cwd=build_dir,
    )
    while process.poll():
        time.sleep(1)

    out = process.stdout.read()
    process.stdout.close()

    # print("done!", len(out), "bytes")
    data = out.decode("utf-8", errors="ignore").split("\n")
    return process_commands(cmake_dir, data)


# -----------------------------------------------------------------------------
# Create Edit Lists

# Create an edit list from a file, in the format:
#
#    [((start_index, end_index), text_to_replace), ...]
#
# Note that edits should not overlap, in the _very_ rare case overlapping edits are needed,
# this could be run multiple times on the same code-base.
#
# Although this seems like it's not a common use-case.

def edit_list_from_file__sizeof_fixed_array(_source, data):
    edits = []

    for match in re.finditer(r"sizeof\(([a-zA-Z_]+)\) \* (\d+) \* (\d+)", data):
        edits.append((
            match.span(),
            'sizeof(%s[%s][%s])' % (match.group(1), match.group(2), match.group(3)),
            '__ALWAYS_FAIL__',
        ))

    for match in re.finditer(r"sizeof\(([a-zA-Z_]+)\) \* (\d+)", data):
        edits.append((
            match.span(),
            'sizeof(%s[%s])' % (match.group(1), match.group(2)),
            '__ALWAYS_FAIL__',
        ))

    for match in re.finditer(r"\b(\d+) \* sizeof\(([a-zA-Z_]+)\)", data):
        edits.append((
            match.span(),
            'sizeof(%s[%s])' % (match.group(2), match.group(1)),
            '__ALWAYS_FAIL__',
        ))
    return edits


def edit_list_from_file__use_const(_source, data):
    edits = []

    # Replace:
    #   float abc[3] = {0, 1, 2};
    # With:
    #   const float abc[3] = {0, 1, 2};

    for match in re.finditer(r"(\(|, |  )([a-zA-Z_0-9]+ [a-zA-Z_0-9]+\[)\b([^\n]+ = )", data):
        edits.append((
            match.span(),
            '%s const %s%s' % (match.group(1), match.group(2), match.group(3)),
            '__ALWAYS_FAIL__',
        ))

    # Replace:
    #   float abc[3]
    # With:
    #   const float abc[3]
    for match in re.finditer(r"(\(|, )([a-zA-Z_0-9]+ [a-zA-Z_0-9]+\[)", data):
        edits.append((
            match.span(),
            '%s const %s' % (match.group(1), match.group(2)),
            '__ALWAYS_FAIL__',
        ))

    return edits


def edit_list_from_file__use_zero_before_float_suffix(_source, data):
    edits = []

    # Replace:
    #   1.f
    # With:
    #   1.0f

    for match in re.finditer(r"\b(\d+)\.([fF])\b", data):
        edits.append((
            match.span(),
            '%s.0%s' % (match.group(1), match.group(2)),
            '__ALWAYS_FAIL__',
        ))

    # Replace:
    #   1.0F
    # With:
    #   1.0f

    for match in re.finditer(r"\b(\d+\.\d+)F\b", data):
        edits.append((
            match.span(),
            '%sf' % (match.group(1),),
            '__ALWAYS_FAIL__',
        ))

    return edits

def edit_list_from_file__use_elem_macro(_source, data):
    edits = []

    # Replace:
    #   (a == b || a == c)
    #   (a != b && a != c)
    # With:
    #   (ELEM(a, b, c))
    #   (!ELEM(a, b, c))

    test_equal = (
        r'[\(]*'
        r'([^\|\(\)]+)'  # group 1 (no (|))
        r'\s+==\s+'
        r'([^\|\(\)]+)'  # group 2 (no (|))
        r'[\)]*'
    )

    test_not_equal = (
        r'[\(]*'
        r'([^\|\(\)]+)'  # group 1 (no (|))
        r'\s+!=\s+'
        r'([^\|\(\)]+)'  # group 2 (no (|))
        r'[\)]*'
    )

    for is_equal in (True, False):
        for n in reversed(range(2, 64)):
            if is_equal:
                re_str = r'\(' + r'\s+\|\|\s+'.join([test_equal] * n) + r'\)'
            else:
                re_str = r'\(' + r'\s+\&\&\s+'.join([test_not_equal] * n) + r'\)'

            for match in re.finditer(re_str, data):
                var = match.group(1)
                var_rest = []
                groups = match.groups()
                groups_paired = [(groups[i * 2], groups[i * 2 + 1]) for i in range(len(groups) // 2)]
                found = True
                for a, b in groups_paired:
                    # Unlikely but possible the checks are swapped.
                    if b == var and a != var:
                        a, b = b, a

                    if a != var:
                        found = False
                        break
                    var_rest.append(b)

                if found:
                    edits.append((
                        match.span(),
                        '(%sELEM(%s, %s))' % (
                            ('' if is_equal else '!'),
                            var,
                            ', '.join(var_rest),
                        ),
                        # Use same expression otherwise this can change values inside assert when it shouldn't.
                        '(%s__ALWAYS_FAIL__(%s, %s))' % (
                            ('' if is_equal else '!'),
                            var,
                            ', '.join(var_rest),
                        ),
                    ))

    return edits


def edit_list_from_file__use_str_elem_macro(_source, data):
    edits = []

    # Replace:
    #   (STREQ(a, b) || STREQ(a, c))
    # With:
    #   (STR_ELEM(a, b, c))

    test_equal = (
        r'[\(]*'
        r'STREQ'
        '\('
        '([^\|\(\),]+)'  # group 1 (no (|,))
        ',\s+'
        '([^\|\(\),]+)'  # group 2 (no (|,))
        '\)'
        r'[\)]*'
    )

    test_not_equal = (
        r'[\(]*'
        '!' # Only difference.
        r'STREQ'
        '\('
        '([^\|\(\),]+)'  # group 1 (no (|,))
        ',\s+'
        '([^\|\(\),]+)'  # group 2 (no (|,))
        '\)'
        r'[\)]*'
    )

    for is_equal in (True, False):
        for n in reversed(range(2, 64)):
            if is_equal:
                re_str = r'\(' + r'\s+\|\|\s+'.join([test_equal] * n) + r'\)'
            else:
                re_str = r'\(' + r'\s+\&\&\s+'.join([test_not_equal] * n) + r'\)'

            for match in re.finditer(re_str, data):
                if _source == '/src/blender/source/blender/editors/mesh/editmesh_extrude_spin.c':
                    print(match.groups())
                var = match.group(1)
                var_rest = []
                groups = match.groups()
                groups_paired = [(groups[i * 2], groups[i * 2 + 1]) for i in range(len(groups) // 2)]
                found = True
                for a, b in groups_paired:
                    # Unlikely but possible the checks are swapped.
                    if b == var and a != var:
                        a, b = b, a

                    if a != var:
                        found = False
                        break
                    var_rest.append(b)

                if found:
                    edits.append((
                        match.span(),
                        '(%sSTR_ELEM(%s, %s))' % (
                            ('' if is_equal else '!'),
                            var,
                            ', '.join(var_rest),
                        ),
                        # Use same expression otherwise this can change values inside assert when it shouldn't.
                        '(%s__ALWAYS_FAIL__(%s, %s))' % (
                            ('' if is_equal else '!'),
                            var,
                            ', '.join(var_rest),
                        ),
                    ))

    return edits


def edit_list_from_file__use_const_vars(_source, data):
    edits = []

    # Replace:
    #   float abc[3] = {0, 1, 2};
    # With:
    #   const float abc[3] = {0, 1, 2};

    # for match in re.finditer(r"(  [a-zA-Z0-9_]+ [a-zA-Z0-9_]+ = [A-Z][A-Z_0-9_]*;)", data):
    #     edits.append((
    #         match.span(),
    #         'const %s' % (match.group(1).lstrip()),
    #         '__ALWAYS_FAIL__',
    #     ))

    for match in re.finditer(r"(  [a-zA-Z0-9_]+ [a-zA-Z0-9_]+ = .*;)", data):
        edits.append((
            match.span(),
            'const %s' % (match.group(1).lstrip()),
            '__ALWAYS_FAIL__',
        ))

    return edits


def edit_list_from_file__remove_return_parens(_source, data):
    edits = []

    # Remove `return (NULL);`
    for match in re.finditer(r"return \(([a-zA-Z_0-9]+)\);", data):
        edits.append((
            match.span(),
            'return %s;' % (match.group(1)),
            'return __ALWAYS_FAIL__;',
        ))
    return edits


def edit_list_from_file__use_streq_macro(_source, data):
    edits = []

    # Replace:
    #   strcmp(a, b) == 0
    # With:
    #   STREQ(a, b)
    for match in re.finditer(r"\bstrcmp\((.*)\) == 0", data):
        edits.append((
            match.span(),
            'STREQ(%s)' % (match.group(1)),
            '__ALWAYS_FAIL__',
        ))
    for match in re.finditer(r"!strcmp\((.*)\)", data):
        edits.append((
            match.span(),
            'STREQ(%s)' % (match.group(1)),
            '__ALWAYS_FAIL__',
        ))

    # Replace:
    #   strcmp(a, b) != 0
    # With:
    #   !STREQ(a, b)
    for match in re.finditer(r"\bstrcmp\((.*)\) != 0", data):
        edits.append((
            match.span(),
            '!STREQ(%s)' % (match.group(1)),
            '__ALWAYS_FAIL__',
        ))
    for match in re.finditer(r"\bstrcmp\((.*)\)", data):
        edits.append((
            match.span(),
            '!STREQ(%s)' % (match.group(1)),
            '__ALWAYS_FAIL__',
        ))

    return edits


def edit_list_from_file__use_array_size_macro(_source, data):
    edits = []

    # Replace:
    #   sizeof(foo) / sizeof(*foo)
    # With:
    #   ARRAY_SIZE(foo)
    #
    # Note that this replacement is only valid in some cases,
    # so only apply with validation that binary output matches.
    for match in re.finditer(r"\bsizeof\((.*)\) / sizeof\([^\)]+\)", data):
        edits.append((
            match.span(),
            'ARRAY_SIZE(%s)' % match.group(1),
            '__ALWAYS_FAIL__',
        ))

    return edits


def test_edit(source, output, output_bytes, build_args, data, data_test, keep_edits=True, expect_failure=False):
    """
    Return true if `data_test` has the same object output as `data`.
    """
    if os.path.exists(output):
        os.remove(output)

    with open(source, 'w', encoding='utf-8') as fh:
        fh.write(data_test)

    ret = run(build_args, quiet=expect_failure)
    if ret == 0:
        output_bytes_test = file_as_bytes(output)
        if (output_bytes is None) or (file_as_bytes(output) == output_bytes):
            if not keep_edits:
                with open(source, 'w', encoding='utf-8') as fh:
                    fh.write(data)
            return True
        else:
            print("Changed code, skip...", hex(hash(output_bytes)), hex(hash(output_bytes_test)))
    else:
        if not expect_failure:
            print("Failed to compile, skip...")

    with open(source, 'w', encoding='utf-8') as fh:
        fh.write(data)
    return False


# -----------------------------------------------------------------------------
# List Fix Functions

def edit_function_get_all():
    fixes = []
    for name in globals().keys():
        if name.startswith("edit_list_from_file__"):
            fixes.append(name.split("__")[1])
    fixes.sort()
    print(fixes)
    return fixes


def edit_function_get_from_id(name):
    return globals().get("edit_list_from_file__" + name)


# -----------------------------------------------------------------------------
# Accept / Reject Edits

def apply_edit(data, text_to_replace, start, end, *, verbose):
    if verbose:
        line_before = line_from_span(data, start, end)

    data = data[:start] + text_to_replace + data[end:]

    if verbose:
        end += len(text_to_replace) - (end - start)
        line_after = line_from_span(data, start, end)

        print("")
        print("Testing edit:")
        print(line_before)
        print(line_after)

    return data


def wash_source_with_edits(arg_group):
    (source, output, build_args, edit_to_apply, skip_test) = arg_group
    # build_args = build_args + " -Werror=duplicate-decl-specifier"
    with open(source, 'r', encoding='utf-8') as fh:
        data = fh.read()
    edit_list_from_file_fn = edit_function_get_from_id(edit_to_apply)
    edits = edit_list_from_file_fn(source, data)
    edits.sort(reverse=True)
    if not edits:
        return

    if skip_test:
        # Just apply all edits.
        for (start, end), text, text_always_fail in edits:
            data = apply_edit(data, text, start, end, verbose=VERBOSE)
        with open(source, 'w', encoding='utf-8') as fh:
            fh.write(data)
        return

    test_edit(
        source, output, None, build_args, data, data,
        keep_edits=False,
    )
    if not os.path.exists(output):
        raise Exception("Failed to produce output file: " + output)
    output_bytes = file_as_bytes(output)

    for (start, end), text, text_always_fail in edits:
        data_test = apply_edit(data, text, start, end, verbose=VERBOSE)
        if test_edit(
                source, output, output_bytes, build_args, data, data_test,
                keep_edits=False,
        ):
            # This worked, check if the change would fail if replaced with 'text_always_fail'.
            data_test_always_fail = apply_edit(data, text_always_fail, start, end, verbose=False)
            if test_edit(
                    source, output, output_bytes, build_args, data, data_test_always_fail,
                    expect_failure=True, keep_edits=False,
            ):
                print("Edit at", (start, end), "doesn't fail, assumed to be ifdef'd out, continuing")
                continue

            # Apply the edit.
            data = data_test
            with open(source, 'w', encoding='utf-8') as fh:
                fh.write(data)


# -----------------------------------------------------------------------------
# Edit Source Code From Args

def header_clean_all(build_dir, regex_list, edit_to_apply, skip_test=False):
    # currently only supports ninja or makefiles
    build_file_ninja = os.path.join(build_dir, "build.ninja")
    build_file_make = os.path.join(build_dir, "Makefile")
    if os.path.exists(build_file_ninja):
        print("Using Ninja")
        args = find_build_args_ninja(build_dir)
    elif os.path.exists(build_file_make):
        print("Using Make")
        args = find_build_args_make(build_dir)
    else:
        sys.stderr.write(
            "Can't find Ninja or Makefile (%r or %r), aborting" %
            (build_file_ninja, build_file_make)
        )
        return
    # needed for when arguments are referenced relatively
    os.chdir(build_dir)

    # Weak, but we probably don't want to handle extern.
    # this limit could be removed.
    source_paths = (
        os.path.join("intern", "ghost"),
        os.path.join("intern", "guardedalloc"),
        os.path.join("source"),
    )

    def output_from_build_args(build_args):
        import shlex
        build_args = shlex.split(build_args)
        i = build_args.index("-o")
        return build_args[i + 1]

    def test_path(c):
        for source_path in source_paths:
            index = c.rfind(source_path)
            print(c)
            if index != -1:
                # Remove first part of the path, we don't want to match
                # against paths in Blender's repo.
                print(source_path)
                c_strip = c[index:]
                for regex in regex_list:
                    if regex.match(c_strip) is not None:
                        return True
        return False

    # Filter out build args.
    args_orig_len = len(args)
    args = [
        (c, build_args)
        for (c, build_args) in args
        if test_path(c)
    ]
    print("Operating on %d of %d files..." % (len(args), args_orig_len))
    for (c, build_args) in args:
        print(" ", c)
    del args_orig_len

    if USE_MULTIPROCESS:
        args = [
            (c, output_from_build_args(build_args), build_args, edit_to_apply, skip_test)
            for (c, build_args) in args
        ]
        import multiprocessing
        job_total = multiprocessing.cpu_count()
        pool = multiprocessing.Pool(processes=job_total * 2)
        pool.map(wash_source_with_edits, args)
    else:
        # now we have commands
        for i, (c, build_args) in enumerate(args):
            wash_source_with_edits(
                (c, output_from_build_args(build_args), build_args, edit_to_apply, skip_test)
            )

    print("\n" "Exit without errors")



def create_parser():
    edits_all = edit_function_get_all()

    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "build_dir",
        help="list of files or directories to check",
    )
    parser.add_argument(
        "--match",
        nargs='+',
        required=True,
        metavar="REGEX",
        help="Match file paths against this expression",
    )
    parser.add_argument(
        "--edit",
        dest="edit",
        choices=edits_all,
        help=(
            "Specify the edit preset to run."
        ),
        required=True,
    )
    parser.add_argument(
        "--skip-test",
        dest="skip_test",
        default=False,
        action='store_true',
        help=(
            "Perform all edits without testing if they perform functional changes. "
            "Use to quickly preview edits, or to perform edits which are manually checked (default=False)"
        ),
        required=False,
    )

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    build_dir = args.build_dir
    regex_list = []

    for i, expr in enumerate(args.match):
        try:
            regex_list.append(re.compile(expr))
        except Exception as ex:
            print(f"Error in expression: {expr}\n  {ex}")
            return 1

    return header_clean_all(build_dir, regex_list, args.edit, args.skip_test)


if __name__ == "__main__":
    sys.exit(main())
