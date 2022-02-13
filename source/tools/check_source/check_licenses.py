#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Check license headers follow the SPDX spec
https://spdx.org/licenses/

This can be activated by calling "make check_licenses" from Blenders root directory.
"""

import os
import sys
import argparse

from dataclasses import dataclass

from typing import (
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
)

# -----------------------------------------------------------------------------
# Constants

# Faster bug makes exceptions and errors more difficult to troubleshoot.
USE_MULTIPROCESS = False

EXPECT_SPDX_IN_FIRST_CHARS = 1024

# Show unique headers after modifying them.
# Useful when reviewing changes as there may be many duplicates.
REPORT_UNIQUE_HEADER_MAPPING = False
mapping: Dict[str, List[str]] = {}

SOURCE_DIR = os.path.normpath(
    os.path.abspath(
        os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    )
)

SPDX_IDENTIFIER_FILE = os.path.join(
    SOURCE_DIR, "doc", "license", "SPDX-license-identifiers.txt"
)

with open(SPDX_IDENTIFIER_FILE, "r", encoding="utf-8") as fh:
    ACCEPTABLE_LICENSES = set(l.split()[0] for l in sorted(fh) if "https://spdx.org/licenses/" in l)
del fh

# -----------------------------------------------------------------------------
# File Type Checks


# Use '/* .. */' style comments.
def filename_is_c_compat(filename: str) -> bool:
    return filename.endswith(
        (
            # C.
            ".c",
            ".h",
            # C++
            ".cc",
            ".cxx",
            ".cpp",
            ".hh",
            ".hxx",
            ".hpp",
            # Objective-C/C++
            ".m",
            ".mm",
            # OPENCL.
            ".cl",
        )
    )


def filename_is_cmake(filename: str) -> bool:
    return filename.endswith(("CMakeLists.txt", ".cmake"))


# Use '#' style comments.
def filename_is_script_compat(filename: str) -> bool:
    return filename.endswith((".py", ".sh", "GNUmakefile"))


# -----------------------------------------------------------------------------
# Cursor Motion


def next_line(text: str, index: int) -> int:
    index = text.find("\n", index + 1)
    if index == -1 or index + 1 == len(text):
        return -1
    return index + 1


def next_line_non_empty(text: str, index: int) -> int:
    while index < len(text):
        index_prev = index
        index = text.find("\n", index)
        if index == -1:
            index = index_prev
            break
        if text[index_prev:index].strip():
            index = index_prev
            break
        # Step over the newline.
        index = index + 1
    return index


def txt_prev_line_while_fn(text: str, index: int, fn: Callable[[str], bool]) -> int:
    """
    Return the next line where ``fn`` fails.
    """
    while index > 0:
        index_prev = index
        index = text.rfind("\n", index)
        if index == -1:
            index = 0
        if not fn(text[index_prev:index]):
            index = index_prev
            break
    return index


def txt_next_line_while_fn(text: str, index: int, fn: Callable[[str], bool]) -> int:
    """
    Return the next line where ``fn`` fails.
    """
    while index < len(text):
        index_prev = index
        index = text.find("\n", index)
        if index == -1:
            index = len(text)
        if not fn(text[index_prev:index]):
            index = index_prev
            break
        # Step over the newline.
        index = index + 1
    return index


def txt_next_eol(text: str, pos: int, limit: int, step_over: bool) -> int:
    """
    Extend ``pos`` to just before the next EOL, otherwise EOF.
    As this is intended for use as a range, ``text[pos]``
    will either be ``\n`` or equal to out of range (equal to ``len(text)``).
    """
    if pos + 1 >= len(text):
        return pos
    # Already at the bounds.
    if text[pos] == "\n":
        return pos + (1 if step_over else 0)
    pos_next = text.find("\n", pos, limit)
    if pos_next == -1:
        return limit
    return pos_next + (1 if step_over else 0)


def txt_prev_bol(text: str, pos: int, limit: int) -> int:

    if pos == 0:
        return pos
    # Already at the bounds.
    if text[pos - 1] == "\n":
        return pos
    pos_next = text.rfind("\n", limit, pos)
    if pos_next == -1:
        return limit
    # We don't want to include the newline.
    return pos_next + 1


def txt_expand_to_line_bounds(
    text: str,
    *,
    span: Tuple[int, int],
    span_limit: Optional[Tuple[int, int]],
) -> Tuple[int, int]:
    return (
        txt_prev_bol(text, span[0], span_limit[0] if span_limit else 0),
        txt_next_eol(
            text, span[1], span_limit[1] if span_limit else len(text), step_over=True
        ),
    )


def txt_anonymous_years(text: str) -> str:
    """
    Replace year with text, since we don't want to consider them different when looking at unique headers.
    """
    # Could use regex, this is OK in practice.
    for year in range(1990, 2023):
        year_as_string = str(year)
        text = text.replace(year_as_string, "####")
    text = text.replace("####-####", "####")
    return text


# -----------------------------------------------------------------------------
# License Checker


def check_contents(filepath: str, text: str) -> None:
    """
    Check for license text, e.g: ``SPDX-License-Identifier: GPL-2.0-or-later``

    Intentionally be strict here... no extra spaces, no trailing space at the end of line etc.
    As there is no reason to be sloppy in this case.
    """
    identifier = "SPDX-License-Identifier: "
    identifier_beg = text[:EXPECT_SPDX_IN_FIRST_CHARS].find(identifier)
    if identifier_beg == -1:
        # Allow completely empty files (sometimes `__init__.py`).
        if not text.rstrip():
            return
        print("Missing:", filepath)
        return
    identifier_end = identifier_beg + len(identifier)
    line_end = txt_next_eol(text, identifier_end, len(text), step_over=False)
    license_text = text[identifier_end:line_end]
    # For C/C++ comments.
    license_text = license_text.rstrip("*/")
    for license_id in license_text.split():
        if license_id in {"AND", "OR"}:
            continue

        if license_id not in ACCEPTABLE_LICENSES:
            print(
                "Unexpected:",
                "{:s}:{:d}".format(filepath, text[:identifier_beg].count("\n") + 1),
                "contains license",
                repr(license_text),
                "not in",
                SPDX_IDENTIFIER_FILE,
            )

    # Check for blank lines:
    blank_lines = text[:identifier_beg].count("\n")
    if filename_is_script_compat(filepath):
        if blank_lines > 0 and text.startswith("#!/"):
            blank_lines -= 1
    if blank_lines > 0:
        print("SPDX not on first line:", filepath)

    if REPORT_UNIQUE_HEADER_MAPPING:
        if filename_is_c_compat(filepath):
            comment_beg = text.rfind("/*", 0, identifier_beg)
            if comment_beg == -1:
                print("Comment Block:", filepath, "failed to find comment start")
                return
            comment_end = text.find("*/", identifier_end, len(text))
            if comment_end == -1:
                print("Comment Block:", filepath, "failed to find comment end")
                return
            comment_end += 2
            comment_block = text[comment_beg + 2 : comment_end - 2]
            comment_block = "\n".join(
                [l.removeprefix(" *") for l in comment_block.split("\n")]
            )
        elif filename_is_script_compat(filepath) or filename_is_cmake(filepath):
            comment_beg = txt_prev_bol(text, identifier_beg, 0)
            comment_end = txt_next_eol(text, identifier_beg, len(text), step_over=False)

            comment_beg = txt_next_line_while_fn(
                text,
                comment_beg,
                lambda l: l.startswith("#") and not l.startswith("#!/"),
            )
            comment_end = txt_next_line_while_fn(
                text,
                comment_end,
                lambda l: l.startswith("#"),
            )

            comment_block = text[comment_beg:comment_end].rstrip()
            comment_block = "\n".join(
                [l.removeprefix("# ") for l in comment_block.split("\n")]
            )
        else:
            raise Exception("Unknown file type: {:s}".format(filepath))

        mapping.setdefault(txt_anonymous_years(comment_block), []).append(filepath)


# -----------------------------------------------------------------------------
# Main Function & Source Listing

operation = check_contents


def source_files(
    path: str,
    paths_exclude: Tuple[str, ...],
    filename_test: Callable[[str], bool],
) -> Generator[str, None, None]:
    paths_exclude_set = set(p.rstrip("/") for p in paths_exclude)
    paths_exclude = tuple(p.rstrip("/") + "/" for p in paths_exclude)
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        if dirpath in paths_exclude_set or dirpath.startswith(paths_exclude):
            continue
        for filename in filenames:
            if filename.startswith("."):
                continue
            filepath = os.path.join(dirpath, filename)
            if filename_test(filename):
                yield filepath


def operation_wrap(filepath: str) -> None:
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            text = f.read()
        except Exception as ex:
            print("Failed to read", filepath, "with", repr(ex))
            return

        operation(filepath, text)


def argparse_create() -> argparse.ArgumentParser:

    # When --help or no args are given, print this help
    description = __doc__
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--show-headers",
        dest="show_headers",
        type=bool,
        default=False,
        required=False,
        help="Show unique headers (useful for spotting irregularities).",
    )

    return parser


def main() -> None:
    global REPORT_UNIQUE_HEADER_MAPPING

    args = argparse_create().parse_args()

    REPORT_UNIQUE_HEADER_MAPPING = args.show_headers

    # Ensure paths are relative to the root, no matter where this script runs from.
    os.chdir(SOURCE_DIR)

    @dataclass
    class Pass:
        filename_test: Callable[[str], bool]
        source_dirs_include: Tuple[str, ...]
        source_dirs_exclude: Tuple[str, ...]

    passes = (
        Pass(
            filename_test=filename_is_c_compat,
            source_dirs_include=(".",),
            source_dirs_exclude=(
                "./extern",
                "./intern/cycles",
                # "./release/scripts/addons",
                "./release/scripts/addons_contrib",
                "./source/tools",
                # Needs manual handling as it mixes two licenses.
                "./intern/atomic",
            ),
        ),
        Pass(
            filename_test=filename_is_cmake,
            source_dirs_include=(".",),
            source_dirs_exclude=(
                # This is an exception, it has it's own CMake files we do not maintain.
                "./extern/audaspace",
                "./extern/quadriflow/3rd/lemon-1.3.1",
            ),
        ),
        Pass(
            filename_test=filename_is_script_compat,
            source_dirs_include=(".",),
            source_dirs_exclude=(
                # This is an exception, it has it's own CMake files we do not maintain.
                "./extern",
                "./intern/cycles",
                "./release/scripts/addons_contrib",
                # Just data.
                "./doc/python_api/examples",
                "./release/scripts/addons/presets",
                "./release/scripts/presets",
                "./release/scripts/templates_py",
            ),
        ),
    )

    for pass_data in passes:
        if USE_MULTIPROCESS:
            filepath_args = [
                filepath
                for dirpath in pass_data.source_dirs_include
                for filepath in source_files(
                    dirpath,
                    pass_data.source_dirs_exclude,
                    pass_data.filename_test,
                )
            ]
            import multiprocessing

            job_total = multiprocessing.cpu_count()
            pool = multiprocessing.Pool(processes=job_total * 2)
            pool.map(operation_wrap, filepath_args)
        else:
            for filepath in [
                filepath
                for dirpath in pass_data.source_dirs_include
                for filepath in source_files(
                    dirpath,
                    pass_data.source_dirs_exclude,
                    pass_data.filename_test,
                )
            ]:
                operation_wrap(filepath)

    if REPORT_UNIQUE_HEADER_MAPPING:
        print("#####################")
        print("Unique Header Listing")
        print("#####################")
        print("")
        for k, v in sorted(mapping.items()):
            print("=" * 79)
            print(k)
            print("-" * 79)
            v.sort()
            for filepath in v:
                print("-", filepath)
            print("")


if __name__ == "__main__":
    main()
