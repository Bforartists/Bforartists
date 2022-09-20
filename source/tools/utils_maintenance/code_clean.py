#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Example:
  ./source/tools/utils/code_clean.py /src/cmake_debug --match ".*/editmesh_.*" --fix=use_const_vars

Note: currently this is limited to paths in "source/" and "intern/",
we could change this if it's needed.
"""

import argparse
import re
import subprocess
import sys
import os

from typing import (
    Any,
    Dict,
    Generator,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
)

# List of (source_file, all_arguments)
ProcessedCommands = List[Tuple[str, str]]

USE_MULTIPROCESS = True

VERBOSE = False

# Print the output of the compiler (_very_ noisy, only useful for troubleshooting compiler issues).
VERBOSE_COMPILER = False

# Print the result of each attempted edit:
#
# - Causes code not to compile.
# - Compiles but changes the resulting behavior.
# - Succeeds.
VERBOSE_EDIT_ACTION = False


BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SOURCE_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "..", ".."))


# -----------------------------------------------------------------------------
# General Utilities

# Note that we could use a hash, however there is no advantage, compare it's contents.
def file_as_bytes(filename: str) -> bytes:
    with open(filename, 'rb') as fh:
        return fh.read()


def line_from_span(text: str, start: int, end: int) -> str:
    while start > 0 and text[start - 1] != '\n':
        start -= 1
    while end < len(text) and text[end] != '\n':
        end += 1
    return text[start:end]


def files_recursive_with_ext(path: str, ext: Tuple[str, ...]) -> Generator[str, None, None]:
    for dirpath, dirnames, filenames in os.walk(path):
        # skip '.git' and other dot-files.
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for filename in filenames:
            if filename.endswith(ext):
                yield os.path.join(dirpath, filename)


# -----------------------------------------------------------------------------
# Execution Wrappers

def run(args: str, *, quiet: bool) -> int:
    if VERBOSE_COMPILER and not quiet:
        out = sys.stdout.fileno()
    else:
        out = subprocess.DEVNULL

    import shlex
    p = subprocess.Popen(shlex.split(args), stdout=out, stderr=out)
    p.wait()
    return p.returncode


# -----------------------------------------------------------------------------
# Build System Access

def cmake_cache_var(cmake_dir: str, var: str) -> Optional[str]:
    with open(os.path.join(cmake_dir, "CMakeCache.txt"), encoding='utf-8') as cache_file:
        lines = [
            l_strip for l in cache_file
            if (l_strip := l.strip())
            if not l_strip.startswith(("//", "#"))
        ]

    for l in lines:
        if l.split(":")[0] == var:
            return l.split("=", 1)[-1]
    return None


RE_CFILE_SEARCH = re.compile(r"\s\-c\s([\S]+)")


def process_commands(cmake_dir: str, data: Sequence[str]) -> Optional[ProcessedCommands]:
    compiler_c = cmake_cache_var(cmake_dir, "CMAKE_C_COMPILER")
    compiler_cxx = cmake_cache_var(cmake_dir, "CMAKE_CXX_COMPILER")
    if compiler_c is None:
        sys.stderr.write("Can't find C compiler in %r" % cmake_dir)
        return None
    if compiler_cxx is None:
        sys.stderr.write("Can't find C++ compiler in %r" % cmake_dir)
        return None

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


def find_build_args_ninja(build_dir: str) -> Optional[ProcessedCommands]:
    import time
    cmake_dir = build_dir
    make_exe = "ninja"
    process = subprocess.Popen(
        [make_exe, "-t", "commands"],
        stdout=subprocess.PIPE,
        cwd=build_dir,
    )
    while process.poll():
        time.sleep(1)
    assert process.stdout is not None

    out = process.stdout.read()
    process.stdout.close()
    # print("done!", len(out), "bytes")
    data = out.decode("utf-8", errors="ignore").split("\n")
    return process_commands(cmake_dir, data)


def find_build_args_make(build_dir: str) -> Optional[ProcessedCommands]:
    import time
    make_exe = "make"
    process = subprocess.Popen(
        [make_exe, "--always-make", "--dry-run", "--keep-going", "VERBOSE=1"],
        stdout=subprocess.PIPE,
        cwd=build_dir,
    )
    while process.poll():
        time.sleep(1)
    assert process.stdout is not None

    out = process.stdout.read()
    process.stdout.close()

    # print("done!", len(out), "bytes")
    data = out.decode("utf-8", errors="ignore").split("\n")
    return process_commands(build_dir, data)


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

from collections import namedtuple
Edit = namedtuple(
    "Edit", (
        # Keep first, for sorting.
        "span",

        "content",
        "content_fail",

        # Optional.
        "extra_build_args",
    ),

    defaults=(
        # `extra_build_args`.
        None,
    )
)
del namedtuple


class EditGenerator:
    __slots__ = ()

    def __new__(cls, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> Any:
        raise RuntimeError("%s should not be instantiated" % cls)

    @staticmethod
    def edit_list_from_file(_source: str, _data: str, _shared_edit_data: Any) -> List[Edit]:
        raise RuntimeError("This function must be overridden by it's subclass!")
        return []

    @staticmethod
    def setup() -> Any:
        return None

    @staticmethod
    def teardown(_shared_edit_data: Any) -> None:
        pass


class edit_generators:
    # fake module.

    class sizeof_fixed_array(EditGenerator):
        """
        Use fixed size array syntax with `sizeof`:

        Replace:
          sizeof(float) * 4 * 4
        With:
          sizeof(float[4][4])
        """
        @staticmethod
        def edit_list_from_file(_source: str, data: str, _shared_edit_data: Any) -> List[Edit]:
            edits = []

            for match in re.finditer(r"sizeof\(([a-zA-Z_]+)\) \* (\d+) \* (\d+)", data):
                edits.append(Edit(
                    span=match.span(),
                    content='sizeof(%s[%s][%s])' % (match.group(1), match.group(2), match.group(3)),
                    content_fail='__ALWAYS_FAIL__',
                ))

            for match in re.finditer(r"sizeof\(([a-zA-Z_]+)\) \* (\d+)", data):
                edits.append(Edit(
                    span=match.span(),
                    content='sizeof(%s[%s])' % (match.group(1), match.group(2)),
                    content_fail='__ALWAYS_FAIL__',
                ))

            for match in re.finditer(r"\b(\d+) \* sizeof\(([a-zA-Z_]+)\)", data):
                edits.append(Edit(
                    span=match.span(),
                    content='sizeof(%s[%s])' % (match.group(2), match.group(1)),
                    content_fail='__ALWAYS_FAIL__',
                ))
            return edits

    class use_const(EditGenerator):
        """
        Use const variables:

        Replace:
          float abc[3] = {0, 1, 2};
        With:
          const float abc[3] = {0, 1, 2};

        Replace:
          float abc[3]
        With:
          const float abc[3]

        As well as casts.

        Replace:
          (float *)
        With:
          (const float *)

        Replace:
          (float (*))
        With:
          (const float (*))
        """
        @staticmethod
        def edit_list_from_file(_source: str, data: str, _shared_edit_data: Any) -> List[Edit]:
            edits = []

            # `float abc[3] = {0, 1, 2};` -> `const float abc[3] = {0, 1, 2};`
            for match in re.finditer(r"(\(|, |  )([a-zA-Z_0-9]+ [a-zA-Z_0-9]+\[)\b([^\n]+ = )", data):
                edits.append(Edit(
                    span=match.span(),
                    content='%s const %s%s' % (match.group(1), match.group(2), match.group(3)),
                    content_fail='__ALWAYS_FAIL__',
                ))

            # `float abc[3]` -> `const float abc[3]`
            for match in re.finditer(r"(\(|, )([a-zA-Z_0-9]+ [a-zA-Z_0-9]+\[)", data):
                edits.append(Edit(
                    span=match.span(),
                    content='%s const %s' % (match.group(1), match.group(2)),
                    content_fail='__ALWAYS_FAIL__',
                ))

            # `(float *)`      -> `(const float *)`
            # `(float (*))`    -> `(const float (*))`
            # `(float (*)[4])` -> `(const float (*)[4])`
            for match in re.finditer(
                    r"(\()"
                    r"([a-zA-Z_0-9]+\s*)"
                    r"(\*+\)|\(\*+\))"
                    r"(|\[[a-zA-Z_0-9]+\])",
                    data,
            ):
                edits.append(Edit(
                    span=match.span(),
                    content='%sconst %s%s%s' % (match.group(1), match.group(2), match.group(3), match.group(4)),
                    content_fail='__ALWAYS_FAIL__',
                ))

            return edits

    class use_zero_before_float_suffix(EditGenerator):
        """
        Use zero before the float suffix.

        Replace:
          1.f
        With:
          1.0f

        Replace:
          1.0F
        With:
          1.0f
        """
        @staticmethod
        def edit_list_from_file(_source: str, data: str, _shared_edit_data: Any) -> List[Edit]:
            edits = []

            # `1.f` -> `1.0f`
            for match in re.finditer(r"\b(\d+)\.([fF])\b", data):
                edits.append(Edit(
                    span=match.span(),
                    content='%s.0%s' % (match.group(1), match.group(2)),
                    content_fail='__ALWAYS_FAIL__',
                ))

            # `1.0F` -> `1.0f`
            for match in re.finditer(r"\b(\d+\.\d+)F\b", data):
                edits.append(Edit(
                    span=match.span(),
                    content='%sf' % (match.group(1),),
                    content_fail='__ALWAYS_FAIL__',
                ))

            return edits

    class use_elem_macro(EditGenerator):
        """
        Use the `ELEM` macro for more abbreviated expressions.

        Replace:
          (a == b || a == c)
          (a != b && a != c)
        With:
          (ELEM(a, b, c))
          (!ELEM(a, b, c))
        """
        @staticmethod
        def edit_list_from_file(_source: str, data: str, _shared_edit_data: Any) -> List[Edit]:
            edits = []

            for use_brackets in (True, False):

                test_equal = (
                    r'([^\|\(\)]+)'  # group 1 (no (|))
                    r'\s+==\s+'
                    r'([^\|\(\)]+)'  # group 2 (no (|))
                )

                test_not_equal = (
                    r'([^\|\(\)]+)'  # group 1 (no (|))
                    r'\s+!=\s+'
                    r'([^\|\(\)]+)'  # group 2 (no (|))
                )

                if use_brackets:
                    test_equal = r'\(' + test_equal + r'\)'
                    test_not_equal = r'\(' + test_not_equal + r'\)'

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
                                edits.append(Edit(
                                    span=match.span(),
                                    content='(%sELEM(%s, %s))' % (
                                        ('' if is_equal else '!'),
                                        var,
                                        ', '.join(var_rest),
                                    ),
                                    # Use same expression otherwise this can change values
                                    # inside assert when it shouldn't.
                                    content_fail='(%s__ALWAYS_FAIL__(%s, %s))' % (
                                        ('' if is_equal else '!'),
                                        var,
                                        ', '.join(var_rest),
                                    ),
                                ))

            return edits

    class use_str_elem_macro(EditGenerator):
        """
        Use `STR_ELEM` macro:

        Replace:
          (STREQ(a, b) || STREQ(a, c))
        With:
          (STR_ELEM(a, b, c))
        """
        @staticmethod
        def edit_list_from_file(_source: str, data: str, _shared_edit_data: Any) -> List[Edit]:
            edits = []

            for use_brackets in (True, False):

                test_equal = (
                    r'STREQ'
                    r'\('
                    r'([^\|\(\),]+)'  # group 1 (no (|,))
                    r',\s+'
                    r'([^\|\(\),]+)'  # group 2 (no (|,))
                    r'\)'
                )

                test_not_equal = (
                    '!'  # Only difference.
                    r'STREQ'
                    r'\('
                    r'([^\|\(\),]+)'  # group 1 (no (|,))
                    r',\s+'
                    r'([^\|\(\),]+)'  # group 2 (no (|,))
                    r'\)'
                )

                if use_brackets:
                    test_equal = r'\(' + test_equal + r'\)'
                    test_not_equal = r'\(' + test_not_equal + r'\)'

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
                                edits.append(Edit(
                                    span=match.span(),
                                    content='(%sSTR_ELEM(%s, %s))' % (
                                        ('' if is_equal else '!'),
                                        var,
                                        ', '.join(var_rest),
                                    ),
                                    # Use same expression otherwise this can change values
                                    # inside assert when it shouldn't.
                                    content_fail='(%s__ALWAYS_FAIL__(%s, %s))' % (
                                        ('' if is_equal else '!'),
                                        var,
                                        ', '.join(var_rest),
                                    ),
                                ))

            return edits

    class use_const_vars(EditGenerator):
        """
        Use `const` where possible:

        Replace:
          float abc[3] = {0, 1, 2};
        With:
          const float abc[3] = {0, 1, 2};
        """
        @staticmethod
        def edit_list_from_file(_source: str, data: str, _shared_edit_data: Any) -> List[Edit]:
            edits = []

            # for match in re.finditer(r"(  [a-zA-Z0-9_]+ [a-zA-Z0-9_]+ = [A-Z][A-Z_0-9_]*;)", data):
            #     edits.append(Edit(
            #         span=match.span(),
            #         content='const %s' % (match.group(1).lstrip()),
            #         content_fail='__ALWAYS_FAIL__',
            #     ))

            for match in re.finditer(r"(  [a-zA-Z0-9_]+ [a-zA-Z0-9_]+ = .*;)", data):
                edits.append(Edit(
                    span=match.span(),
                    content='const %s' % (match.group(1).lstrip()),
                    content_fail='__ALWAYS_FAIL__',
                ))

            return edits

    class remove_return_parens(EditGenerator):
        """
        Remove redundant parenthesis around return arguments:

        Replace:
          return (value);
        With:
          return value;
        """
        @staticmethod
        def edit_list_from_file(_source: str, data: str, _shared_edit_data: Any) -> List[Edit]:
            edits = []

            # Remove `return (NULL);`
            for match in re.finditer(r"return \(([a-zA-Z_0-9]+)\);", data):
                edits.append(Edit(
                    span=match.span(),
                    content='return %s;' % (match.group(1)),
                    content_fail='return __ALWAYS_FAIL__;',
                ))
            return edits

    class use_streq_macro(EditGenerator):
        """
        Use `STREQ` macro:

        Replace:
          strcmp(a, b) == 0
        With:
          STREQ(a, b)

        Replace:
          strcmp(a, b) != 0
        With:
          !STREQ(a, b)
        """
        @staticmethod
        def edit_list_from_file(_source: str, data: str, _shared_edit_data: Any) -> List[Edit]:
            edits = []

            # `strcmp(a, b) == 0` -> `STREQ(a, b)`
            for match in re.finditer(r"\bstrcmp\((.*)\) == 0", data):
                edits.append(Edit(
                    span=match.span(),
                    content='STREQ(%s)' % (match.group(1)),
                    content_fail='__ALWAYS_FAIL__',
                ))
            for match in re.finditer(r"!strcmp\((.*)\)", data):
                edits.append(Edit(
                    span=match.span(),
                    content='STREQ(%s)' % (match.group(1)),
                    content_fail='__ALWAYS_FAIL__',
                ))

            # `strcmp(a, b) != 0` -> `!STREQ(a, b)`
            for match in re.finditer(r"\bstrcmp\((.*)\) != 0", data):
                edits.append(Edit(
                    span=match.span(),
                    content='!STREQ(%s)' % (match.group(1)),
                    content_fail='__ALWAYS_FAIL__',
                ))
            for match in re.finditer(r"\bstrcmp\((.*)\)", data):
                edits.append(Edit(
                    span=match.span(),
                    content='!STREQ(%s)' % (match.group(1)),
                    content_fail='__ALWAYS_FAIL__',
                ))

            return edits

    class use_array_size_macro(EditGenerator):
        """
        Use macro for an error checked array size:

        Replace:
          sizeof(foo) / sizeof(*foo)
        With:
          ARRAY_SIZE(foo)
        """
        @staticmethod
        def edit_list_from_file(_source: str, data: str, _shared_edit_data: Any) -> List[Edit]:
            edits = []
            # Note that this replacement is only valid in some cases,
            # so only apply with validation that binary output matches.
            for match in re.finditer(r"\bsizeof\((.*)\) / sizeof\([^\)]+\)", data):
                edits.append(Edit(
                    span=match.span(),
                    content='ARRAY_SIZE(%s)' % match.group(1),
                    content_fail='__ALWAYS_FAIL__',
                ))

            return edits

    class header_clean(EditGenerator):
        """
        Clean headers, ensuring that the headers removed are not used directly or indirectly.

        Note that the `CFLAGS` should be set so missing prototypes error instead of warn:
        With GCC: `-Werror=missing-prototypes`
        """

        @staticmethod
        def _header_guard_from_filename(f: str) -> str:
            return '__%s__' % os.path.basename(f).replace('.', '_').upper()

        @classmethod
        def setup(cls) -> Any:
            # For each file replace `pragma once` with old-style header guard.
            # This is needed so we can remove the header with the knowledge the source file didn't use it indirectly.
            files: List[Tuple[str, str, str, str]] = []
            shared_edit_data = {
                'files': files,
            }
            for f in files_recursive_with_ext(
                    os.path.join(SOURCE_DIR, 'source'),
                    ('.h', '.hh', '.inl', '.hpp', '.hxx'),
            ):
                with open(f, 'r', encoding='utf-8') as fh:
                    data = fh.read()

                for match in re.finditer(r'^[ \t]*#\s*(pragma\s+once)\b', data, flags=re.MULTILINE):
                    header_guard = cls._header_guard_from_filename(f)
                    start, end = match.span()
                    src = data[start:end]
                    dst = (
                        '#ifndef %s\n#define %s' % (header_guard, header_guard)
                    )
                    dst_footer = '\n#endif /* %s */\n' % header_guard
                    files.append((f, src, dst, dst_footer))
                    data = data[:start] + dst + data[end:] + dst_footer
                    with open(f, 'w', encoding='utf-8') as fh:
                        fh.write(data)
                    break
            return shared_edit_data

        @staticmethod
        def teardown(shared_edit_data: Any) -> None:
            files = shared_edit_data['files']
            for f, src, dst, dst_footer in files:
                with open(f, 'r', encoding='utf-8') as fh:
                    data = fh.read()

                data = data.replace(
                    dst, src,
                ).replace(
                    dst_footer, '',
                )
                with open(f, 'w', encoding='utf-8') as fh:
                    fh.write(data)

        @classmethod
        def edit_list_from_file(cls, _source: str, data: str, _shared_edit_data: Any) -> List[Edit]:
            edits = []

            # Remove include.
            for match in re.finditer(r"^(([ \t]*#\s*include\s+\")([^\"]+)(\"[^\n]*\n))", data, flags=re.MULTILINE):
                header_name = match.group(3)
                header_guard = cls._header_guard_from_filename(header_name)
                edits.append(Edit(
                    span=match.span(),
                    content='',  # Remove the header.
                    content_fail='%s__ALWAYS_FAIL__%s' % (match.group(2), match.group(4)),
                    extra_build_args=('-D' + header_guard),
                ))

            return edits


def test_edit(
        source: str,
        output: str,
        output_bytes: Optional[bytes],
        build_args: str,
        data: str,
        data_test: str,
        keep_edits: bool = True,
        expect_failure: bool = False,
) -> bool:
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
            if VERBOSE_EDIT_ACTION:
                print("Changed code, skip...", hex(hash(output_bytes)), hex(hash(output_bytes_test)))
    else:
        if not expect_failure:
            if VERBOSE_EDIT_ACTION:
                print("Failed to compile, skip...")

    with open(source, 'w', encoding='utf-8') as fh:
        fh.write(data)
    return False


# -----------------------------------------------------------------------------
# List Fix Functions

def edit_function_get_all() -> List[str]:
    fixes = []
    for name in dir(edit_generators):
        value = getattr(edit_generators, name)
        if type(value) is type and issubclass(value, EditGenerator):
            fixes.append(name)
    fixes.sort()
    return fixes


def edit_class_from_id(name: str) -> Type[EditGenerator]:
    result = getattr(edit_generators, name)
    assert issubclass(result, EditGenerator)
    # MYPY 0.812 doesn't recognize the assert above.
    return result  # type: ignore


# -----------------------------------------------------------------------------
# Accept / Reject Edits

def apply_edit(data: str, text_to_replace: str, start: int, end: int, *, verbose: bool) -> str:
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


def wash_source_with_edits(arg_group: Tuple[str, str, str, str, bool, Any]) -> None:
    (source, output, build_args, edit_to_apply, skip_test, shared_edit_data) = arg_group
    # build_args = build_args + " -Werror=duplicate-decl-specifier"
    with open(source, 'r', encoding='utf-8') as fh:
        data = fh.read()
    edit_generator_class = edit_class_from_id(edit_to_apply)
    edits = edit_generator_class.edit_list_from_file(source, data, shared_edit_data)
    edits.sort(reverse=True)
    if not edits:
        return

    if skip_test:
        # Just apply all edits.
        for (start, end), text, _text_always_fail, _extra_build_args in edits:
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

    for (start, end), text, text_always_fail, extra_build_args in edits:
        build_args_for_edit = build_args
        if extra_build_args:
            # Add directly after the compile command.
            a, b = build_args.split(' ', 1)
            build_args_for_edit = a + ' ' + extra_build_args + ' ' + b

        data_test = apply_edit(data, text, start, end, verbose=VERBOSE)
        if test_edit(
                source, output, output_bytes, build_args_for_edit, data, data_test,
                keep_edits=False,
        ):
            # This worked, check if the change would fail if replaced with 'text_always_fail'.
            data_test_always_fail = apply_edit(data, text_always_fail, start, end, verbose=False)
            if test_edit(
                    source, output, output_bytes, build_args_for_edit, data, data_test_always_fail,
                    expect_failure=True, keep_edits=False,
            ):
                if VERBOSE_EDIT_ACTION:
                    print("Edit at", (start, end), "doesn't fail, assumed to be ifdef'd out, continuing")
                continue

            # Apply the edit.
            data = data_test
            with open(source, 'w', encoding='utf-8') as fh:
                fh.write(data)


# -----------------------------------------------------------------------------
# Edit Source Code From Args

def run_edits_on_directory(
        build_dir: str,
        regex_list: List[re.Pattern[str]],
        edit_to_apply: str,
        skip_test: bool = False,
) -> int:
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
        return 1

    if args is None:
        # Error will have been reported.
        return 1

    # needed for when arguments are referenced relatively
    os.chdir(build_dir)

    # Weak, but we probably don't want to handle extern.
    # this limit could be removed.
    source_paths = (
        os.path.join("intern", "ghost"),
        os.path.join("intern", "guardedalloc"),
        os.path.join("source"),
    )

    def output_from_build_args(build_args: str) -> str:
        import shlex
        build_args_split = shlex.split(build_args)
        i = build_args_split.index("-o")
        return build_args_split[i + 1]

    def test_path(c: str) -> bool:
        # Skip any generated source files (files in the build directory).
        if os.path.abspath(c).startswith(build_dir):
            return False
        # Raise an exception since this should never happen,
        # we want to know about it early if it does, as it will cause failure
        # when attempting to compile the missing file.
        if not os.path.exists(c):
            raise Exception("Missing source file: " + c)

        for source_path in source_paths:
            index = c.rfind(source_path)
            # print(c)
            if index != -1:
                # Remove first part of the path, we don't want to match
                # against paths in Blender's repo.
                # print(source_path)
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

    edit_generator_class = edit_class_from_id(edit_to_apply)

    shared_edit_data = edit_generator_class.setup()

    try:
        if USE_MULTIPROCESS:
            args_expanded = [
                (c, output_from_build_args(build_args), build_args, edit_to_apply, skip_test, shared_edit_data)
                for (c, build_args) in args
            ]
            import multiprocessing
            job_total = multiprocessing.cpu_count()
            pool = multiprocessing.Pool(processes=job_total * 2)
            pool.map(wash_source_with_edits, args_expanded)
            del args_expanded
        else:
            # now we have commands
            for c, build_args in args:
                wash_source_with_edits(
                    (c, output_from_build_args(build_args), build_args, edit_to_apply, skip_test, shared_edit_data)
                )
    except Exception as ex:
        raise ex
    finally:
        edit_generator_class.teardown(shared_edit_data)

    print("\n" "Exit without errors")
    return 0


def create_parser() -> argparse.ArgumentParser:
    from textwrap import indent, dedent

    edits_all = edit_function_get_all()

    # Create docstring for edits.
    edits_all_docs = []
    for edit in edits_all:
        edits_all_docs.append(
            "  %s\n%s" % (
                edit,
                indent(dedent(getattr(edit_generators, edit).__doc__ or '').strip('\n') + '\n', '    '),
            )
        )

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
        help="Specify the edit preset to run.\n\n" + "\n".join(edits_all_docs) + "\n",
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


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    build_dir = args.build_dir
    regex_list = []

    for expr in args.match:
        try:
            regex_list.append(re.compile(expr))
        except Exception as ex:
            print(f"Error in expression: {expr}\n  {ex}")
            return 1

    return run_edits_on_directory(build_dir, regex_list, args.edit, args.skip_test)


if __name__ == "__main__":
    sys.exit(main())
