#!/usr/bin/env python3

import os
from os.path import join, splitext

from trailing_space_clean_config import PATHS

SOURCE_EXT = (
    # C/C++
    ".c", ".h", ".cpp", ".hpp", ".cc", ".hh", ".cxx", ".hxx", ".inl",
    # GLSL
    ".glsl",
    # Python
    ".py",
    # Text (also CMake)
    ".txt", ".cmake", ".rst",
)


def is_source(filename):
    return filename.endswith(SOURCE_EXT)


def path_iter(path, filename_check=None):
    for dirpath, dirnames, filenames in os.walk(path):
        # skip ".git"
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]

        for filename in filenames:
            if filename.startswith("."):
                continue
            filepath = join(dirpath, filename)
            if filename_check is None or filename_check(filepath):
                yield filepath


def path_expand(paths, filename_check=None):
    for f in paths:
        if not os.path.exists(f):
            print("Missing:", f)
        elif os.path.isdir(f):
            yield from path_iter(f, filename_check)
        else:
            yield f


def rstrip_file(filename):
    with open(filename, "r", encoding="utf-8") as fh:
        data_src = fh.read()

    data_dst = []
    for l in data_src.rstrip().splitlines(True):
        data_dst.append(l.rstrip() + "\n")

    data_dst = "".join(data_dst)
    len_strip = len(data_src) - len(data_dst)
    if len_strip != 0:
        with open(filename, "w", encoding="utf-8") as fh:
            fh.write(data_dst)
    return len_strip


def main():
    for f in path_expand(PATHS, is_source):
        len_strip = rstrip_file(f)
        if len_strip != 0:
            print(f"Strip ({len_strip}): {f}")


if __name__ == "__main__":
    main()
