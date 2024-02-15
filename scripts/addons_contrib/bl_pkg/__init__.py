# SPDX-FileCopyrightText: 2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Blender Extensions",
    "author": "Campbell Barton",
    "version": (0, 0, 1),
    "blender": (4, 0, 0),
    "location": "Edit -> Preferences -> Extensions",
    "description": "Extension repository support for remote repositories",
    "warning": "",
    # "doc_url": "{BLENDER_MANUAL_URL}/addons/bl_pkg/bl_pkg.html",
    "support": 'OFFICIAL',
    "category": "System",
}

import bpy

from bpy.props import (
    BoolProperty,
    EnumProperty,
    IntProperty,
    StringProperty,
)

from bpy.types import (
    AddonPreferences,
)


class BlExtPreferences(AddonPreferences):
    bl_idname = __name__
    timeout: IntProperty(
        name="Time Out",
        default=10,
    )
    show_development: BoolProperty(
        name="Show Development Utilities",
        description="Show utilities intended for developing the extension",
        default=False,
    )


class StatusInfoUI:
    __slots__ = (
        # The the title of the status/notification.
        "title",
        # The result of an operation.
        "log",
        # Set to true when running (via a modal operator).
        "running",
    )

    def __init__(self):
        self.log = []
        self.title = ""
        self.running = False

    def from_message(self, title, text):
        log_new = []
        for line in text.split("\n"):
            if not (line := line.rstrip()):
                continue
            # Don't show any prefix for "Info" since this is implied.
            log_new.append(('STATUS', line.removeprefix("Info: ")))
        if not log_new:
            return

        self.title = title
        self.running = False
        self.log = log_new


def cookie_from_session():
    # This path is a unique string for this session.
    # Don't use a constant as it may be changed at run-time.
    return bpy.app.tempdir


# -----------------------------------------------------------------------------
# Shared Low Level Utilities

def repo_paths_or_none(repo_item):
    if (directory := repo_item.directory) == "":
        return None, None
    if repo_item.use_remote_path:
        if not (remote_path := repo_item.remote_path):
            return None, None
    else:
        remote_path = ""
    return directory, remote_path


def repo_active_or_none():
    prefs = bpy.context.preferences
    if not prefs.experimental.use_extension_repos:
        return

    paths = prefs.filepaths
    active_extension_index = paths.active_extension_repo
    try:
        active_repo = None if active_extension_index < 0 else paths.extension_repos[active_extension_index]
    except IndexError:
        active_repo = None
    return active_repo


# -----------------------------------------------------------------------------
# Handlers

@bpy.app.handlers.persistent
def extenion_repos_sync(*_):
    # This is called from operators (create or an explicit call to sync)
    # so calling a modal operator is "safe".
    if (active_repo := repo_active_or_none()) is None:
        return

    print("SYNC:", active_repo.name)
    # There may be nothing to upgrade.

    from contextlib import redirect_stdout
    import io
    stdout = io.StringIO()

    with redirect_stdout(stdout):
        bpy.ops.bl_pkg.repo_sync_all('INVOKE_DEFAULT', use_active_only=True)

    if text := stdout.getvalue():
        repo_status_text.from_message("Sync \"{:s}\"".format(active_repo.name), text)


@bpy.app.handlers.persistent
def extenion_repos_upgrade(*_):
    # This is called from operators (create or an explicit call to sync)
    # so calling a modal operator is "safe".
    if (active_repo := repo_active_or_none()) is None:
        return

    print("UPGRADE:", active_repo.name)

    from contextlib import redirect_stdout
    import io
    stdout = io.StringIO()

    with redirect_stdout(stdout):
        bpy.ops.bl_pkg.pkg_upgrade_all('INVOKE_DEFAULT', use_active_only=True)

    if text := stdout.getvalue():
        repo_status_text.from_message("Upgrade \"{:s}\"".format(active_repo.name), text)


# -----------------------------------------------------------------------------
# Wrap Handlers

_monkeypatch_extenions_repos_update_dirs = set()


def monkeypatch_extenions_repos_update_pre_impl():
    _monkeypatch_extenions_repos_update_dirs.clear()

    extension_repos = bpy.context.preferences.filepaths.extension_repos
    for repo_item in extension_repos:
        if not repo_item.enabled:
            continue
        directory, _repo_path = repo_paths_or_none(repo_item)
        if directory is None:
            continue

        _monkeypatch_extenions_repos_update_dirs.add(directory)


def monkeypatch_extenions_repos_update_post_impl():
    from . import bl_extension_ops

    bl_extension_ops.repo_cache_store_refresh_from_prefs()

    # Refresh newly added directories.
    extension_repos = bpy.context.preferences.filepaths.extension_repos
    for repo_item in extension_repos:
        if not repo_item.enabled:
            continue
        directory, _repo_path = repo_paths_or_none(repo_item)
        if directory is None:
            continue

        if directory in _monkeypatch_extenions_repos_update_dirs:
            continue
        # Ignore missing because the new repo might not have a JSON file.
        repo_cache_store.refresh_remote_from_directory(directory=directory, error_fn=print, force=True)
        repo_cache_store.refresh_local_from_directory(directory=directory, error_fn=print, ignore_missing=True)

    _monkeypatch_extenions_repos_update_dirs.clear()


@bpy.app.handlers.persistent
def monkeypatch_extensions_repos_update_pre(*_):
    print("PRE:")
    try:
        monkeypatch_extenions_repos_update_pre_impl()
    except BaseException as ex:
        print("ERROR", str(ex))
    try:
        monkeypatch_extensions_repos_update_pre._fn_orig()
    except BaseException as ex:
        print("ERROR", str(ex))


@bpy.app.handlers.persistent
def monkeypatch_extenions_repos_update_post(*_):
    print("POST:")
    try:
        monkeypatch_extenions_repos_update_post._fn_orig()
    except BaseException as ex:
        print("ERROR", str(ex))
    try:
        monkeypatch_extenions_repos_update_post_impl()
    except BaseException as ex:
        print("ERROR", str(ex))


def monkeypatch_install():
    import addon_utils

    handlers = bpy.app.handlers._extension_repos_update_pre
    fn_orig = addon_utils._initialize_extension_repos_pre
    fn_override = monkeypatch_extensions_repos_update_pre
    for i, fn in enumerate(handlers):
        if fn is fn_orig:
            handlers[i] = fn_override
            fn_override._fn_orig = fn_orig
            break

    handlers = bpy.app.handlers._extension_repos_update_post
    fn_orig = addon_utils._initialize_extension_repos_post
    fn_override = monkeypatch_extenions_repos_update_post
    for i, fn in enumerate(handlers):
        if fn is fn_orig:
            handlers[i] = fn_override
            fn_override._fn_orig = fn_orig
            break


def monkeypatch_uninstall():
    handlers = bpy.app.handlers._extension_repos_update_pre
    fn_override = monkeypatch_extensions_repos_update_pre
    for i in range(len(handlers)):
        fn = handlers[i]
        if fn is fn_override:
            handlers[i] = fn_override._fn_orig
            del fn_override._fn_orig
            break

    handlers = bpy.app.handlers._extension_repos_update_post
    fn_override = monkeypatch_extenions_repos_update_post
    for i in range(len(handlers)):
        fn = handlers[i]
        if fn is fn_override:
            handlers[i] = fn_override._fn_orig
            del fn_override._fn_orig
            break


# Text to display in the UI (while running...).
repo_status_text = StatusInfoUI()

# Singleton to cache all repositories JSON data and handles refreshing.
repo_cache_store = None


# -----------------------------------------------------------------------------
# Theme Integration

def theme_preset_draw(menu, context):
    layout = menu.layout
    repos_all = [
        repo_item for repo_item in context.preferences.filepaths.extension_repos
        if repo_item.enabled
    ]
    if not repos_all:
        return
    import os
    menu_idname = type(menu).__name__
    for i, pkg_manifest_local in enumerate(repo_cache_store.pkg_manifest_from_local_ensure(error_fn=print)):
        if pkg_manifest_local is None:
            continue
        repo_item = repos_all[i]
        directory = repo_item.directory
        for pkg_idname, value in pkg_manifest_local.items():
            if value["type"] != "theme":
                continue

            theme_dir = os.path.join(directory, pkg_idname)
            theme_files = [
                filename for entry in os.scandir(theme_dir)
                if ((not entry.is_dir()) and
                    (not (filename := entry.name).startswith(".")) and
                    filename.lower().endswith(".xml"))
            ]
            theme_files.sort()
            for filename in theme_files:
                props = layout.operator(menu.preset_operator, text=bpy.path.display_name(filename))
                props.filepath = os.path.join(theme_dir, os.path.join(theme_dir, filename))
                props.menu_idname = menu_idname


# -----------------------------------------------------------------------------
# Registration

classes = (
    BlExtPreferences,
)


def register():
    # pylint: disable-next=global-statement
    global repo_cache_store

    from bpy.types import WindowManager
    from . import (
        bl_extension_ops,
        bl_extension_ui,
        bl_extension_utils,
    )

    if repo_cache_store is None:
        repo_cache_store = bl_extension_utils.RepoCacheStore()
    else:
        repo_cache_store.clear()
    bl_extension_ops.repo_cache_store_refresh_from_prefs()

    for cls in classes:
        bpy.utils.register_class(cls)

    bl_extension_ops.register()
    bl_extension_ui.register()

    WindowManager.extension_search = StringProperty(
        name="Filter",
        description="Filter by extension name, author & category",
        options={'TEXTEDIT_UPDATE'},
    )
    WindowManager.extension_type = EnumProperty(
        items=(
            ('ALL', "All", "Show all extensions"),
            None,
            ('ADDON', "Add-ons", "Only show add-ons"),
            ('THEME', "Themes", "Only show themes"),
            ('KEYMAP', "Keymaps", "Only show keymaps"),
        ),
        name="Filter by Type",
        description="Show extensions by type",
        default='ALL',
    )
    WindowManager.extension_enabled_only = BoolProperty(
        name="Enabled Extensions Only",
        description="Only show enabled extensions",
    )
    WindowManager.extension_installed_only = BoolProperty(
        name="Installed Extensions Only",
        description="Only show installed extensions",
    )

    from bl_ui.space_userpref import USERPREF_MT_interface_theme_presets
    USERPREF_MT_interface_theme_presets.append(theme_preset_draw)

    handlers = bpy.app.handlers._extension_repos_sync
    handlers.append(extenion_repos_sync)

    handlers = bpy.app.handlers._extension_repos_upgrade
    handlers.append(extenion_repos_upgrade)

    monkeypatch_install()


def unregister():
    # pylint: disable-next=global-statement
    global repo_cache_store

    from bpy.types import WindowManager
    from . import (
        bl_extension_ops,
        bl_extension_ui,
    )

    bl_extension_ops.unregister()
    bl_extension_ui.unregister()

    del WindowManager.extension_search
    del WindowManager.extension_type
    del WindowManager.extension_enabled_only
    del WindowManager.extension_installed_only

    for cls in classes:
        bpy.utils.unregister_class(cls)

    if repo_cache_store is None:
        pass
    else:
        repo_cache_store.clear()
        repo_cache_store = None

    from bl_ui.space_userpref import USERPREF_MT_interface_theme_presets
    USERPREF_MT_interface_theme_presets.remove(theme_preset_draw)

    handlers = bpy.app.handlers._extension_repos_sync
    if extenion_repos_sync in handlers:
        handlers.remove(extenion_repos_sync)

    handlers = bpy.app.handlers._extension_repos_upgrade
    if extenion_repos_upgrade in handlers:
        handlers.remove(extenion_repos_upgrade)

    monkeypatch_uninstall()
