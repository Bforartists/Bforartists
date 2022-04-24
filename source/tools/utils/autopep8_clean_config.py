# SPDX-License-Identifier: GPL-2.0-or-later

import os
PATHS = (
    "build_files",
    "doc",
    "release/datafiles",
    "release/lts",
    "release/scripts/freestyle",
    "release/scripts/modules",
    "release/scripts/presets",
    "release/scripts/startup",
    "release/scripts/templates_py",
    "source/blender",
    "source/tools",
    "tests",
)

BLACKLIST = (
    "source/tools/svn_rev_map/sha1_to_rev.py",
    "source/tools/svn_rev_map/rev_to_sha1.py",
    "source/tools/svn_rev_map/rev_to_sha1.py",
    "release/scripts/modules/rna_manual_reference.py",
)

SOURCE_DIR = os.path.normpath(os.path.abspath(os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))))

PATHS = tuple(
    os.path.join(SOURCE_DIR, p.replace("/", os.sep))
    for p in PATHS
)

BLACKLIST = set(
    os.path.join(SOURCE_DIR, p.replace("/", os.sep))
    for p in BLACKLIST
)


def files(path, test_fn):
    for dirpath, dirnames, filenames in os.walk(path):
        # skip '.git'
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for filename in filenames:
            if test_fn(filename):
                filepath = os.path.join(dirpath, filename)
                yield filepath
