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
    ("source/tools/check_blender_release/", (), {}),
    ("source/tools/check_source/", (), {'MYPYPATH': "modules"}),
    ("source/tools/check_wiki/", (), {}),
    ("source/tools/utils/", (), {}),
    ("source/tools/utils_api/", (), {}),
    ("source/tools/utils_build/", (), {}),
    ("source/tools/utils_doc/", (), {}),
    ("source/tools/utils_ide/", (), {}),
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
        "build_files/cmake/cmake_qtcreator_project.py",
        "build_files/cmake/cmake_static_check_smatch.py",
        "build_files/cmake/cmake_static_check_sparse.py",
        "build_files/cmake/cmake_static_check_splint.py",
        "source/tools/check_blender_release/check_module_enabled.py",
        "source/tools/check_blender_release/check_module_numpy.py",
        "source/tools/check_blender_release/check_module_requests.py",
        "source/tools/check_blender_release/check_release.py",
        "source/tools/check_blender_release/check_static_binaries.py",
        "source/tools/check_blender_release/check_utils.py",
        "source/tools/check_blender_release/scripts/modules_enabled.py",
        "source/tools/check_blender_release/scripts/requests_basic_access.py",
        "source/tools/check_blender_release/scripts/requests_import.py",
        "source/tools/check_source/check_descriptions.py",
        "source/tools/check_source/check_header_duplicate.py",
        "source/tools/check_source/check_unused_defines.py",
        "source/tools/utils/blend2json.py",
        "source/tools/utils/blender_keyconfig_export_permutations.py",
        "source/tools/utils/blender_merge_format_changes.py",
        "source/tools/utils/blender_theme_as_c.py",
        "source/tools/utils/credits_git_gen.py",
        "source/tools/utils/cycles_commits_sync.py",
        "source/tools/utils/cycles_timeit.py",
        "source/tools/utils/gdb_struct_repr_c99.py",
        "source/tools/utils/git_log.py",
        "source/tools/utils/git_log_review_commits.py",
        "source/tools/utils/git_log_review_commits_advanced.py",
        "source/tools/utils/make_cursor_gui.py",
        "source/tools/utils/make_gl_stipple_from_xpm.py",
        "source/tools/utils/make_shape_2d_from_blend.py",
        "source/tools/utils/weekly_report.py",
        "source/tools/utils_api/bpy_introspect_ui.py",  # Uses `bpy`.
        "source/tools/utils_doc/rna_manual_reference_updater.py",
        "source/tools/utils_ide/qtcreator/externaltools/qtc_assembler_preview.py",
        "source/tools/utils_ide/qtcreator/externaltools/qtc_blender_diffusion.py",
        "source/tools/utils_ide/qtcreator/externaltools/qtc_cpp_to_c_comments.py",
        "source/tools/utils_ide/qtcreator/externaltools/qtc_doxy_file.py",
        "source/tools/utils_ide/qtcreator/externaltools/qtc_project_update.py",
        "source/tools/utils_ide/qtcreator/externaltools/qtc_sort_paths.py",
        "source/tools/utils_maintenance/blender_menu_search_coverage.py",  # Uses `bpy`.
        "source/tools/utils_maintenance/blender_update_themes.py",  # Uses `bpy`.
        "source/tools/utils_maintenance/trailing_space_clean.py",
        "source/tools/utils_maintenance/trailing_space_clean_config.py",
    )
)

PATHS = tuple(
    (os.path.join(SOURCE_DIR, p_items[0].replace("/", os.sep)), *p_items[1:])
    for p_items in PATHS
)
