# SPDX-FileCopyrightText: 2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

__all__ = (
    "open_external_editor"
)


def open_external_editor(filepath, line, column, /):
    # Internal Python implementation for `TEXT_OT_jump_to_file_at_point`.
    # Returning a non-empty string represents an error, an empty string for success.
    import shlex
    import subprocess
    from string import Template
    from bpy import context

    text_editor = context.preferences.filepaths.text_editor
    text_editor_args = context.preferences.filepaths.text_editor_args

    # The caller should check this.
    assert text_editor

    if not text_editor_args:
        return (
            "Provide text editor argument format in File Paths/Applications Preferences, "
            "see input field tool-tip for more information",
        )

    if "$filepath" not in text_editor_args:
        return "Text Editor Args Format must contain $filepath"

    args = [text_editor]
    template_vars = {
        "filepath": filepath,
        "line": line + 1,
        "column": column + 1,
        "line0": line,
        "column0": column,
    }

    try:
        args.extend([Template(arg).substitute(**template_vars) for arg in shlex.split(text_editor_args)])
    except BaseException as ex:
        return "Exception parsing template: %r" % ex

    try:
        # With `check=True` if `process.returncode != 0` an exception will be raised.
        subprocess.run(args, check=True)
    except BaseException as ex:
        return "Exception running external editor: %r" % ex

    return ""
