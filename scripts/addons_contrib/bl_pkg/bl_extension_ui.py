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
    USERPREF_PT_addons,
)

from . import repo_status_text


# -----------------------------------------------------------------------------
# Generic Utilities


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


def extensions_panel_draw_legacy_addons(
        layout,
        context,
        *,
        search_lower,
        enabled_only,
        installed_only,
        used_addon_module_name_map,
):
    # NOTE: this duplicates logic from `USERPREF_PT_addons` eventually this logic should be used instead.
    # Don't de-duplicate the logic as this is a temporary state - as long as extensions remains experimental.
    import addon_utils
    from bpy.app.translations import (
        pgettext_iface as iface_,
    )
    from .bl_extension_ops import (
        pkg_info_check_exclude_filter_ex,
    )

    addons = [
        (mod, addon_utils.module_bl_info(mod))
        for mod in addon_utils.modules(refresh=False)
    ]

    # Initialized on demand.
    user_addon_paths = []

    for mod, bl_info in addons:
        module_name = mod.__name__
        is_extension = addon_utils.check_extension(module_name)
        if is_extension:
            continue

        if search_lower and (
                not pkg_info_check_exclude_filter_ex(
                    bl_info["name"],
                    bl_info["description"],
                    search_lower,
                )
        ):
            continue

        is_enabled = module_name in used_addon_module_name_map
        if enabled_only and (not is_enabled):
            continue

        col_box = layout.column()
        box = col_box.box()
        colsub = box.column()
        row = colsub.row(align=True)

        row.operator(
            "preferences.addon_expand",
            icon='DISCLOSURE_TRI_DOWN' if bl_info["show_expanded"] else 'DISCLOSURE_TRI_RIGHT',
            emboss=False,
        ).module = module_name

        row.operator(
            "preferences.addon_disable" if is_enabled else "preferences.addon_enable",
            icon='CHECKBOX_HLT' if is_enabled else 'CHECKBOX_DEHLT', text="",
            emboss=False,
        ).module = module_name

        sub = row.row()
        sub.active = is_enabled
        sub.label(text=bl_info["name"])

        if bl_info["warning"]:
            sub.label(icon='ERROR')

        row_right = row.row()
        row_right.alignment = 'RIGHT'

        row_right.label(text="Installed (Legacy)   ")
        row_right.active = False

        if bl_info["show_expanded"]:
            split = box.split(factor=0.15)
            col_a = split.column()
            col_b = split.column()
            if value := bl_info["description"]:
                col_a.label(text="Description:")
                col_b.label(text=iface_(value))

            col_a.label(text="File:")
            col_b.label(text=mod.__file__, translate=False)

            if value := bl_info["author"]:
                col_a.label(text="Author:")
                col_b.label(text=value, translate=False)
            if value := bl_info["version"]:
                col_a.label(text="Version:")
                col_b.label(text=".".join(str(x) for x in value), translate=False)
            if value := bl_info["warning"]:
                col_a.label(text="Warning:")
                col_b.label(text="  " + iface_(value), icon='ERROR')
            del value

            # Include for consistency.
            col_a.label(text="Type:")
            col_b.label(text="add-on")

            user_addon = USERPREF_PT_addons.is_user_addon(mod, user_addon_paths)

            if bl_info["doc_url"] or bl_info.get("tracker_url"):
                split = box.row().split(factor=0.15)
                split.label(text="Internet:")
                sub = split.row()
                if bl_info["doc_url"]:
                    sub.operator(
                        "wm.url_open", text="Documentation", icon='HELP',
                    ).url = bl_info["doc_url"]
                # Only add "Report a Bug" button if tracker_url is set
                # or the add-on is bundled (use official tracker then).
                if bl_info.get("tracker_url"):
                    sub.operator(
                        "wm.url_open", text="Report a Bug", icon='URL',
                    ).url = bl_info["tracker_url"]
                elif not user_addon:
                    addon_info = (
                        "Name: %s %s\n"
                        "Author: %s\n"
                    ) % (bl_info["name"], str(bl_info["version"]), bl_info["author"])
                    props = sub.operator(
                        "wm.url_open_preset", text="Report a Bug", icon='URL',
                    )
                    props.type = 'BUG_ADDON'
                    props.id = addon_info

            if user_addon:
                rowsub = col_b.row()
                rowsub.alignment = 'RIGHT'
                rowsub.operator(
                    "preferences.addon_remove", text="Remove", icon='CANCEL',
                ).module = module_name

            if is_enabled:
                if (addon_preferences := used_addon_module_name_map[module_name].preferences) is not None:
                    USERPREF_PT_addons.draw_addon_preferences(layout, context, addon_preferences)


def extensions_panel_draw_impl(
        self,
        context,
        search_lower,
        filter_by_type,
        enabled_only,
        installed_only,
        show_development,
):
    """
    Show all the items... we may want to paginate at some point.
    """
    import os
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

    # To access enabled add-ons.
    show_addons = filter_by_type in {"", "add-on"}
    if show_addons:
        used_addon_module_name_map = {addon.module: addon for addon in context.preferences.addons}

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
            has_remote = (repo.repo_url != "")
            if has_remote:
                # NOTE: it would be nice to detect when the repository ran sync and it failed.
                # This isn't such an important distinction though, the main thing users should be aware of
                # is that a "sync" is required.
                box.label(text="Repository: \"{:s}\" must sync with the remote repository.".format(repo.name))
            del repo
            continue
        else:
            repo = repos_all[repo_index]
            has_remote = (repo.repo_url != "")
            del repo

        for pkg_id, item_remote in pkg_manifest_remote.items():
            if filter_by_type and (filter_by_type != item_remote["type"]):
                continue
            if search_lower and (not pkg_info_check_exclude_filter(item_remote, search_lower)):
                continue

            item_local = pkg_manifest_local.get(pkg_id)
            is_installed = item_local is not None

            if installed_only and (is_installed == 0):
                continue

            if is_installed and (item_local["type"] == "add-on"):
                addon_module_name = "bl_ext.{:s}.{:s}".format(repos_all[repo_index].module, pkg_id)
                is_enabled_addon = addon_module_name in used_addon_module_name_map

                # This only makes sense for add-ons at the moment.
                if enabled_only and (not is_enabled_addon):
                    continue
            else:
                is_enabled_addon = False
                addon_module_name = None

            item_version = item_remote["version"]
            if item_local is None:
                item_local_version = None
                is_outdated = False
            else:
                item_local_version = item_local["version"]
                is_outdated = item_local_version != item_version

            key = (pkg_id, repo_index)
            if show_development:
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

            if show_development:
                if mark:
                    props = row_button.operator("bl_pkg.pkg_mark_clear", text="", icon='RADIOBUT_ON', emboss=False)
                else:
                    props = row_button.operator("bl_pkg.pkg_mark_set", text="", icon='RADIOBUT_OFF', emboss=False)
                props.pkg_id = pkg_id
                props.repo_index = repo_index
                del props

            if is_installed and (addon_module_name is not None):
                row_button.operator(
                    "preferences.addon_disable" if is_enabled_addon else "preferences.addon_enable",
                    icon='CHECKBOX_HLT' if is_enabled_addon else 'CHECKBOX_DEHLT',
                    text=label,
                    emboss=False,
                ).module = addon_module_name
            else:
                # Use a blank icon to avoid odd text alignment when mixing with installed add-ons.
                row_button.active = is_installed
                row_button.label(text=label, icon='BLANK1')
            del label

            row_right = row.row()
            row_right.alignment = 'RIGHT'

            if has_remote:
                if is_installed:
                    # Include uninstall below.
                    if is_outdated:
                        props = row_right.operator("bl_pkg.pkg_install", text="Update")
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
            else:
                # Right space for alignment with the button.
                row_right.label(text="Installed (Local)   ")
                row_right.active = False

            if show:
                split = box.split(factor=0.15)
                col_a = split.column()
                col_b = split.column()

                col_a.label(text="Description:")
                # The full description may be multiple lines (not yet supported by Blender's UI).
                col_b.label(text=item_remote["tagline"])

                if is_installed:
                    col_a.label(text="Path:")
                    col_b.label(text=os.path.join(repos_all[repo_index].directory, pkg_id), translate=False)

                col_a.label(text="Maintainer:")
                col_b.label(text=item_remote["maintainer"])

                col_a.label(text="License:")
                col_b.label(text=",".join([x.removeprefix("SPDX:") for x in item_remote["license"]]))

                col_a.label(text="Version:")
                if is_outdated:
                    col_b.label(text="{:s} ({:s} available)".format(item_local_version, item_version))
                else:
                    col_b.label(text=item_version)

                if has_remote:
                    col_a.label(text="Size:")
                    col_b.label(text=size_as_fmt_string(item_remote["archive_size"]))

                if not filter_by_type:
                    col_a.label(text="Type:")
                    col_b.label(text=item_remote["type"])

                if len(repos_all) > 1:
                    col_a.label(text="Repository:")
                    col_b.label(text=repos_all[repo_index].name)

                if value := item_remote.get("website"):
                    col_a.label(text="Internet:")
                    # Use half size button, for legacy add-ons there are two, here there is one
                    # however one large button looks silly, so use a half size still.
                    col_b.split(factor=0.5).operator("wm.url_open", text="Website", icon='HELP').url = value
                del value

                # Note that we could allow removing extensions from non-remote extension repos
                # although this is destructive, so don't enable this right now.
                if is_installed and has_remote:
                    rowsub = col_b.row()
                    rowsub.alignment = 'RIGHT'
                    props = rowsub.operator("bl_pkg.pkg_uninstall", text="Remove")
                    props.repo_index = repo_index
                    props.pkg_id = pkg_id
                    del props, rowsub

                # Show addon user preferences.
                if is_enabled_addon:
                    if (addon_preferences := used_addon_module_name_map[addon_module_name].preferences) is not None:
                        USERPREF_PT_addons.draw_addon_preferences(layout, context, addon_preferences)

    if show_addons:
        extensions_panel_draw_legacy_addons(
            layout,
            context,
            search_lower=search_lower,
            enabled_only=enabled_only,
            installed_only=installed_only,
            used_addon_module_name_map=used_addon_module_name_map,
        )


class USERPREF_PT_extensions_bl_pkg_filter(Panel):
    bl_label = "Extensions Filter"

    bl_space_type = 'TOPBAR'  # dummy.
    bl_region_type = 'HEADER'
    bl_ui_units_x = 12

    def draw(self, context):
        layout = self.layout

        wm = context.window_manager
        layout.prop(wm, "extension_enabled_only")
        layout.prop(wm, "extension_installed_only")


class USERPREF_MT_extensions_bl_pkg_settings(Menu):
    bl_label = "Extension Settings"

    def draw(self, context):
        layout = self.layout

        addon_prefs = context.preferences.addons[__package__].preferences

        layout.operator("bl_pkg.repo_sync_all", text="Check for Updates", icon='FILE_REFRESH')
        layout.operator("bl_pkg.pkg_upgrade_all", text="Update All", icon='FILE_REFRESH')

        layout.separator()

        layout.operator("bl_pkg.pkg_install_files", icon='IMPORT', text="Install Extensions (from file)...")
        layout.operator("preferences.addon_install", icon='IMPORT', text="Install Legacy Add-on (from file)...")

        layout.separator()

        layout.prop(addon_prefs, "show_development")

        if addon_prefs.show_development:
            layout.separator()

            # We might want to expose this for all users, the purpose of this
            # is to refresh after changes have been made to the repos outside of Blender
            # it's disputable if this is a common case.
            layout.operator("preferences.addon_refresh", text="Refresh (file-system)", icon='FILE_REFRESH')
            layout.separator()

            layout.operator("bl_pkg.pkg_install_marked", text="Install Marked", icon='IMPORT')
            layout.operator("bl_pkg.pkg_uninstall_marked", text="Uninstall Marked", icon='X')
            layout.operator("bl_pkg.obsolete_marked")

            layout.separator()

            layout.operator("bl_pkg.repo_lock")
            layout.operator("bl_pkg.repo_unlock")


def extensions_panel_draw(panel, context):
    prefs = context.preferences
    if not prefs.experimental.use_extension_repos:
        # Unexpected, the extension is disabled but this add-on is.
        # In this case don't show the UI as it is confusing.
        return

    from .bl_extension_ops import (
        blender_filter_by_type_map,
    )

    wm = context.window_manager
    layout = panel.layout

    row = layout.split(factor=0.5)
    row_a = row.row()
    row_a.prop(wm, "extension_search", text="", icon='VIEWZOOM')
    row_b = row.row()
    row_b.prop(wm, "extension_type", text="")
    row_b.popover("USERPREF_PT_extensions_bl_pkg_filter", text="", icon='FILTER')

    row_b.separator()
    row_b.menu("USERPREF_MT_extensions_bl_pkg_settings", text="", icon='DOWNARROW_HLT')
    row_b.popover("USERPREF_PT_extensions_repos", text="", icon='PREFERENCES')
    del row, row_a, row_b

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

    addon_prefs = prefs.addons[__package__].preferences

    extensions_panel_draw_impl(
        panel,
        context,
        wm.extension_search.lower(),
        blender_filter_by_type_map[wm.extension_type],
        wm.extension_enabled_only,
        wm.extension_installed_only,
        addon_prefs.show_development,
    )


classes = (
    # Pop-overs.
    USERPREF_PT_extensions_bl_pkg_filter,
    USERPREF_MT_extensions_bl_pkg_settings,
)


def register():
    USERPREF_PT_addons.append(extensions_panel_draw)

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    USERPREF_PT_addons.remove(extensions_panel_draw)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
