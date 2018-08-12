#!/usr/bin/env python3

import os
from os.path import join, splitext

from autopep8_clean_config import PATHS, BLACKLIST

print(PATHS)
SOURCE_EXT = (
    # Python
    ".py",
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


def main():
    import subprocess
    for f in path_expand(PATHS, is_source):
        if f in BLACKLIST:
            continue

        print(f)
        subprocess.call((
            "autopep8",
            "--ignore",
            ",".join((
                # Info: Use "isinstance()" instead of comparing types directly.
                # Why disable?: Changes code logic, in rare cases we want to compare exact types.
                "E721",
                # Info: Fix bare except.
                # Why disable?: Disruptive, leave our exceptions alone.
                "E722",
                # Info: Put imports on separate lines.
                # Why disable?: Disruptive, we manage our own imports.
                "E401",
                # Info: Fix various deprecated code (via lib2to3)
                # Why disable?: causes imports to be added/re-arranged.
                "W690",
            )),
            "--aggressive",
            "--in-place",
            # Prefer to manually handle line wrapping
            "--max-line-length", "200",
            f,
        ))


if __name__ == "__main__":
    main()
