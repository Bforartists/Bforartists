#!/usr/bin/env python3

import multiprocessing
import os
import sys
import subprocess

VERSION_MIN = (6, 0, 0)
VERSION_MAX_RECOMMENDED = (9, 0, 1)
CLANG_FORMAT_CMD = "clang-format"

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
os.chdir(BASE_DIR)


extensions = (
    ".c", ".cc", ".cpp", ".cxx",
    ".h", ".hh", ".hpp", ".hxx",
    ".m", ".mm",
    ".osl", ".glsl",
)

extensions_only_retab = (
    ".cmake",
    "CMakeLists.txt",
    ".sh",
)

ignore_files = {
    "intern/cycles/render/sobol.cpp",  # Too heavy for clang-format
}


def compute_paths(paths):
    # Optionally pass in files to operate on.
    if not paths:
        paths = (
            "intern/atomic",
            "intern/audaspace",
            "intern/clog",
            "intern/cycles",
            "intern/dualcon",
            "intern/eigen",
            "intern/ffmpeg",
            "intern/ghost",
            "intern/glew-mx",
            "intern/guardedalloc",
            "intern/iksolver",
            "intern/locale",
            "intern/memutil",
            "intern/mikktspace",
            "intern/opencolorio",
            "intern/opensubdiv",
            "intern/openvdb",
            "intern/rigidbody",
            "intern/string",
            "intern/utfconv",
            "source",
            "tests/gtests",
        )

    if os.sep != "/":
        paths = [f.replace("/", os.sep) for f in paths]
    return paths


def source_files_from_git(paths):
    cmd = ("git", "ls-tree", "-r", "HEAD", *paths, "--name-only", "-z")
    files = subprocess.check_output(cmd).split(b'\0')
    return [f.decode('ascii') for f in files]


def convert_tabs_to_spaces(files):
    for f in files:
        print("TabExpand", f)
        with open(f, 'r', encoding="utf-8") as fh:
            data = fh.read()
            if False:
                # Simple 4 space
                data = data.expandtabs(4)
            else:
                # Complex 2 space
                # because some comments have tabs for alignment.
                def handle(l):
                    ls = l.lstrip("\t")
                    d = len(l) - len(ls)
                    if d != 0:
                        return ("  " * d) + ls.expandtabs(4)
                    else:
                        return l.expandtabs(4)

                lines = data.splitlines(keepends=True)
                lines = [handle(l) for l in lines]
                data = "".join(lines)
        with open(f, 'w', encoding="utf-8") as fh:
            fh.write(data)


def clang_format_ensure_version():
    global CLANG_FORMAT_CMD
    clang_format_cmd = None
    version_output = None
    for i in range(2, -1, -1):
        clang_format_cmd = (
            "clang-format-" + (".".join(["%d"] * i) % VERSION_MIN[:i])
            if i > 0 else
            "clang-format"
        )
        try:
            version_output = subprocess.check_output((clang_format_cmd, "-version")).decode('utf-8')
        except FileNotFoundError as e:
            continue
        CLANG_FORMAT_CMD = clang_format_cmd
        break
    version = next(iter(v for v in version_output.split() if v[0].isdigit()), None)
    if version is not None:
        version = version.split("-")[0]
        version = tuple(int(n) for n in version.split("."))
    if version is not None:
        print("Using %s (%d.%d.%d)..." % (CLANG_FORMAT_CMD, version[0], version[1], version[2]))
    return version


def clang_format_file(files):
    cmd = [CLANG_FORMAT_CMD, "-i", "-verbose"] + files
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT)


def clang_print_output(output):
    print(output.decode('utf8', errors='ignore').strip())


def clang_format(files):
    pool = multiprocessing.Pool()

    # Process in chunks to reduce overhead of starting processes.
    cpu_count = multiprocessing.cpu_count()
    chunk_size = min(max(len(files) // cpu_count // 2, 1), 32)
    for i in range(0, len(files), chunk_size):
        files_chunk = files[i:i+chunk_size];
        pool.apply_async(clang_format_file, args=[files_chunk], callback=clang_print_output)

    pool.close()
    pool.join()

def argparse_create():
    import argparse

    # When --help or no args are given, print this help
    usage_text = "Format source code"
    epilog = "This script runs clang-format on multiple files/directories"
    parser = argparse.ArgumentParser(description=usage_text, epilog=epilog)
    parser.add_argument(
        "--expand-tabs",
        dest="expand_tabs",
        default=False,
        action='store_true',
        help="Run a pre-pass that expands tabs "
        "(default=False)",
        required=False,
    )
    parser.add_argument(
        "paths",
        nargs=argparse.REMAINDER,
        help="All trailing arguments are treated as paths."
    )

    return parser


def main():
    version = clang_format_ensure_version()
    if version is None:
        print("Unable to detect 'clang-format -version'")
        sys.exit(1)
    if version < VERSION_MIN:
        print("Version of clang-format is too old:", version, "<", VERSION_MIN)
        sys.exit(1)
    if version > VERSION_MAX_RECOMMENDED:
        print(
            "WARNING: Version of clang-format is too recent:",
            version, ">=", VERSION_MAX_RECOMMENDED,
        )
        print(
            "You may want to install clang-format-%d.%d, "
            "or use the precompiled libs repository." %
            (version[0], version[1]),
        )

    args = argparse_create().parse_args()

    use_default_paths = not bool(args.paths)

    paths = compute_paths(args.paths)
    print("Operating on:")
    for p in paths:
        print(" ", p)

    files = [
        f for f in source_files_from_git(paths)
        if f.endswith(extensions)
        if f not in ignore_files
    ]

    # Always operate on all cmake files (when expanding tabs and no paths given).
    files_retab = [
        f for f in source_files_from_git((".",) if use_default_paths else paths)
        if f.endswith(extensions_only_retab)
        if f not in ignore_files
    ]

    if args.expand_tabs:
        convert_tabs_to_spaces(files + files_retab)
    clang_format(files)


if __name__ == "__main__":
    main()
