# SPDX-License-Identifier: GPL-2.0-or-later

import os
from typing import (
    Any,
    Tuple,
    Dict,
)

PATHS: Tuple[Tuple[str, Tuple[Any, ...], Dict[str, str]], ...] = (
    ("build_files/cmake/", (), {'MYPYPATH': "modules"}),
    ("build_files/utils/", (), {'MYPYPATH': "modules"}),
    ("doc/manpage/blender.1.py", (), {}),
    ("source/tools/check_source/", (), {'MYPYPATH': "modules"}),
    ("source/tools/utils_maintenance/", (), {'MYPYPATH': "modules"}),
)

SOURCE_DIR = os.path.normpath(os.path.abspath(os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))))

BLACKLIST = set(
    os.path.join(SOURCE_DIR, p.replace("/", os.sep))
    for p in
    (
        "build_files/cmake/clang_array_check.py",
        "build_files/cmake/cmake_netbeans_project.py",
        "build_files/cmake/cmake_print_build_options.py",
        "build_files/cmake/cmake_qtcreator_project.py",
        "build_files/cmake/cmake_static_check_smatch.py",
        "build_files/cmake/cmake_static_check_sparse.py",
        "build_files/cmake/cmake_static_check_splint.py",
        "build_files/utils/make_test.py",
        "build_files/utils/make_update.py",
        "build_files/utils/make_utils.py",
        "source/tools/check_source/check_cmake_consistency.py",
        "source/tools/check_source/check_descriptions.py",
        "source/tools/check_source/check_header_duplicate.py",
        "source/tools/check_source/check_licenses.py",
        "source/tools/check_source/check_spelling.py",
        "source/tools/check_source/check_unused_defines.py",
        "source/tools/utils_maintenance/blender_menu_search_coverage.py",
        "source/tools/utils_maintenance/blender_update_themes.py",
        "source/tools/utils_maintenance/clang_format_paths.py",
        "source/tools/utils_maintenance/trailing_space_clean.py",
        "source/tools/utils_maintenance/trailing_space_clean_config.py",
        "tests/python/bl_keymap_validate.py",
    )
)

PATHS = tuple(
    (os.path.join(SOURCE_DIR, p_items[0].replace("/", os.sep)), *p_items[1:])
    for p_items in PATHS
)
