# SPDX-FileCopyrightText: 2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
GUI (WARNING) this is a hack!
Written to allow a UI without modifying Blender.
"""

__all__ = (
    "register",
    "unregister",
)

import bpy

from bpy.types import (
    Menu,
    Panel,
)

from bl_ui.space_userpref import (
    USERPREF_PT_extensions,
    ExtensionsPanel,
)

from . import repo_status_text


# Allow marking packages.
USE_MARK = False


# -----------------------------------------------------------------------------
#


def size_as_fmt_string(num: float) -> str:
    for unit in ("b", "kb", "mb", "gb", "tb", "pb", "eb", "zb"):
        if abs(num) < 1024.0:
            return "{:3.1f}{:s}".format(num, unit)
        num /= 1024.0
    unit = "yb"
    return "{:.1f}{:s}".format(num, unit)


def sizes_as_percentage_string(size_partial: int, size_final: int) -> str:
    if size_final == 0:
        percent = 0.0
    else:
        size_partial = min(size_partial, size_final)
        percent = size_partial / size_final

    return "{:-6.2f}%".format(percent * 100)


def userpref_addons_draw_ext(
        self,
        _context,
        search_lower,
        filter_by_type,
        installed_only,
):
    """
    Show all the items... we may want to paginate at some point.
    """
    from .bl_extension_ops import (
        blender_extension_mark,
        blender_extension_show,
        extension_repos_read,
        pkg_info_check_exclude_filter,
        repo_cache_store_refresh_from_prefs,
    )

    from . import repo_cache_store

    # This isn't elegant, but the preferences aren't available on registration.
    if not repo_cache_store.is_init():
        repo_cache_store_refresh_from_prefs()

    layout = self.layout

    # Define a top-most column to place warnings (if-any).
    # Needed so the warnings aren't mixed in with other content.
    layout_topmost = layout.column()

    repos_all = extension_repos_read()

    remote_ex = None
    local_ex = None

    def error_fn_remote(ex):
        nonlocal remote_ex
        remote_ex = ex

    def error_fn_local(ex):
        nonlocal remote_ex
        remote_ex = ex

    for repo_index, (
            pkg_manifest_remote,
            pkg_manifest_local,
    ) in enumerate(zip(
        repo_cache_store.pkg_manifest_from_remote_ensure(error_fn=error_fn_remote),
        repo_cache_store.pkg_manifest_from_local_ensure(error_fn=error_fn_local),
    )):
        # Show any exceptions created while accessing the JSON,
        # if the JSON has an IO error while being read or if the directory doesn't exist.
        # In general users should _not_ see these kinds of errors however we cannot prevent
        # IO errors in general and it is better to show a warning than to ignore the error entirely
        # or cause a trace-back which breaks the UI.
        if (remote_ex is not None) or (local_ex is not None):
            repo = repos_all[repo_index]
            box = layout_topmost.box()
            if remote_ex is not None:
                box.label(text="Repository Remote \"{:s}\": {:s}".format(repo.name, str(remote_ex)))
                remote_ex = None

            if local_ex is not None:
                box.label(text="Repository Local \"{:s}\": {:s}".format(repo.name, str(local_ex)))
                local_ex = None
            continue

        if pkg_manifest_remote is None:
            box = layout_topmost.box()
            repo = repos_all[repo_index]
            if repo.repo_url == "":
                box.label(text="Repository: \"{:s}\" has no remote set.".format(repo.name))
            else:
                # NOTE: it would be nice to detect when the repository ran sync and it failed.
                # This isn't such an important distinction though, the main thing users should be aware of
                # is that a "sync" is required.
                box.label(text="Repository: \"{:s}\" must sync with the remote repository.".format(repo.name))
            del repo
            continue

        for pkg_id, item_remote in pkg_manifest_remote.items():
            if filter_by_type and (filter_by_type != item_remote["type"]):
                continue
            if search_lower and (not pkg_info_check_exclude_filter(item_remote, search_lower)):
                continue

            item_version = item_remote["version"]

            item_local = pkg_manifest_local.get(pkg_id)
            is_installed = item_local is not None

            if installed_only and (is_installed == 0):
                continue

            if item_local is None:
                item_local_version = None
                is_outdated = False
            else:
                item_local_version = item_local["version"]
                is_outdated = item_local_version != item_version

            key = (pkg_id, repo_index)
            mark = key in blender_extension_mark
            show = key in blender_extension_show
            del key

            box = layout.box()

            # Left align so the operator text isn't centered.
            row = box.row(align=True)
            # row.label
            if show:
                props = row.operator("bl_pkg.pkg_show_clear", text="", icon='DISCLOSURE_TRI_DOWN', emboss=False)
            else:
                props = row.operator("bl_pkg.pkg_show_set", text="", icon='DISCLOSURE_TRI_RIGHT', emboss=False)
            props.pkg_id = pkg_id
            props.repo_index = repo_index
            del props

            row_button = row.row()
            row_button.alignment = 'LEFT'

            label = item_remote["name"]
            if is_outdated:
                label = label + " (outdated)"

            if USE_MARK:
                if mark:
                    props = row_button.operator("bl_pkg.pkg_mark_clear", text=label, icon='CHECKBOX_HLT', emboss=False)
                else:
                    props = row_button.operator("bl_pkg.pkg_mark_set", text=label, icon='CHECKBOX_DEHLT', emboss=False)
                props.pkg_id = pkg_id
                props.repo_index = repo_index
                del props

                row_button.active = mark
                del row_button
            else:
                row_button.active = is_installed
                row_button.label(text=label)

            row_right = row.row()
            row_right.alignment = 'RIGHT'

            if is_installed:
                # Include uninstall below.
                if is_outdated:
                    props = row_right.operator("bl_pkg.pkg_install", text="Upgrade")
                    props.repo_index = repo_index
                    props.pkg_id = pkg_id
                    del props
                else:
                    # Right space for alignment with the button.
                    row_right.label(text="Installed   ")
                    row_right.active = False
            else:
                props = row_right.operator("bl_pkg.pkg_install", text="Install")
                props.repo_index = repo_index
                props.pkg_id = pkg_id
                del props

            if show:
                split = box.split(factor=0.15)
                row_a = split.column()
                row_b = split.column()

                row_a.label(text="Version:")
                if item_local_version is not None and (item_version != item_local_version):
                    row_b.label(text="{:s} ({:s} available)".format(item_local_version, item_version))
                else:
                    row_b.label(text=item_version)

                row_a.label(text="Description:")
                row_b.label(text=item_remote["description"])

                row_a.label(text="Size:")
                row_b.label(text=size_as_fmt_string(item_remote["archive_size"]))

                if len(repos_all) > 1:
                    row_a.label(text="Repository:")
                    row_b.label(text=repos_all[repo_index].name)

                if is_installed:
                    # Include uninstall below.
                    props = row_a.operator("bl_pkg.pkg_uninstall", text="Remove")
                    props.repo_index = repo_index
                    props.pkg_id = pkg_id
                    del props

                    rowsub = row_b.row()
                    rowsub.alignment = 'RIGHT'
                    props = rowsub.operator("bl_pkg.pkg_show_settings", text="", icon='SETTINGS')
                    props.repo_index = repo_index
                    props.pkg_id = pkg_id
                    del props, rowsub


class USERPREF_PT_extensions_bl_pkg_filter(Panel):
    bl_label = "Extensions Filter"

    bl_space_type = 'TOPBAR'  # dummy.
    bl_region_type = 'HEADER'
    bl_ui_units_x = 12

    def draw(self, context):
        layout = self.layout

        wm = context.window_manager
        layout.prop(wm, "extension_installed_only")


class USERPREF_MT_extensions_bl_pkg_settings(Menu):
    bl_label = "Extension Settings"

    def draw(self, context):
        layout = self.layout

        if USE_MARK:
            layout.operator("bl_pkg.pkg_install_marked", text="Install Marked", icon='IMPORT')
            layout.operator("bl_pkg.pkg_uninstall_marked", text="Uninstall Marked", icon='X')
            layout.operator("bl_pkg.obsolete_marked")

        layout.operator("bl_pkg.repo_sync_all", text="Check for Updates", icon='FILE_REFRESH')
        layout.operator("bl_pkg.pkg_upgrade_all", text="Upgrade All", icon='FILE_REFRESH')

        layout.operator("bl_pkg.repo_lock")
        layout.operator("bl_pkg.repo_unlock")


class USERPREF_PT_extensions_bl_pkg(ExtensionsPanel, Panel):
    bl_label = "Extensions"
    # Keep header so panel can be moved under the repositories list until design is finished.
    # bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        from .bl_extension_ops import (
            blender_filter_by_type_map,
        )

        wm = context.window_manager
        layout = self.layout

        row = layout.row()
        rowsub = row.split(factor=0.75)
        rowsub.prop(wm, "extension_search", text="", icon='VIEWZOOM')
        rowsub.prop(wm, "extension_type", text="")
        rowsub = row.row(align=True)
        rowsub.popover("USERPREF_PT_extensions_bl_pkg_filter", text="", icon='FILTER')
        rowsub.menu("USERPREF_MT_extensions_bl_pkg_settings", text="", icon='PREFERENCES')
        del rowsub

        if repo_status_text.log:
            box = layout.box()
            row = box.split(factor=0.5, align=True)
            if repo_status_text.running:
                row.label(text=repo_status_text.title + "...")
            else:
                row.label(text=repo_status_text.title)
            rowsub = row.row(align=True)
            rowsub.alignment = 'RIGHT'
            rowsub.operator("bl_pkg.pkg_status_clear", text="", icon='X', emboss=False)
            boxsub = box.box()
            for ty, msg in repo_status_text.log:
                if ty == 'STATUS':
                    boxsub.label(text=msg)
                elif ty == 'PROGRESS':
                    msg_str, progress_unit, progress, progress_range = msg
                    if progress <= progress_range:
                        boxsub.progress(
                            factor=progress / progress_range,
                            text="{:s}, {:s}".format(
                                sizes_as_percentage_string(progress, progress_range),
                                msg_str,
                            ),
                        )
                    elif progress_unit == 'BYTE':
                        boxsub.progress(factor=0.0, text="{:s}, {:s}".format(msg_str, size_as_fmt_string(progress)))
                    else:
                        # We might want to support other types.
                        boxsub.progress(factor=0.0, text="{:s}, {:d}".format(msg_str, progress))
                else:
                    boxsub.label(text="{:s}: {:s}".format(ty, msg))

            # Hide when running.
            if repo_status_text.running:
                return

        userpref_addons_draw_ext(
            self,
            context,
            wm.extension_search.lower(),
            blender_filter_by_type_map[wm.extension_type],
            wm.extension_installed_only,
        )


classes = (
    USERPREF_PT_extensions_bl_pkg,

    # Pop-overs.
    USERPREF_PT_extensions_bl_pkg_filter,
    USERPREF_MT_extensions_bl_pkg_settings,
)


def register():
    USERPREF_PT_extensions.unused = False
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    USERPREF_PT_extensions.unused = True
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
