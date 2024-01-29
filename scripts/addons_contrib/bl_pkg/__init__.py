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


def cookie_from_session():
    # This path is a unique string for this session.
    # Don't use a constant as it may be changed at run-time.
    return bpy.app.tempdir

# -----------------------------------------------------------------------------
# Wrap Handlers


_monkeypatch_extenions_repos_update_dirs = set()


def monkeypatch_extenions_repos_update_pre_impl():
    _monkeypatch_extenions_repos_update_dirs.clear()

    extension_repos = bpy.context.preferences.filepaths.extension_repos
    for repo_item in extension_repos:
        if not repo_item.enabled:
            continue

        _monkeypatch_extenions_repos_update_dirs.add(repo_item.directory)


def monkeypatch_extenions_repos_update_post_impl():
    from . import bl_extension_ops

    bl_extension_ops.repo_cache_store_refresh_from_prefs()

    # Refresh newly added directories.
    extension_repos = bpy.context.preferences.filepaths.extension_repos
    for repo_item in extension_repos:
        if not repo_item.enabled:
            continue

        directory = repo_item.directory
        if directory in _monkeypatch_extenions_repos_update_dirs:
            continue
        # Ignore missing because the new repo might not have a JSON file.
        repo_cache_store.refresh_remote_from_directory(directory=directory, force=True)
        repo_cache_store.refresh_local_from_directory(directory=directory, ignore_missing=True)

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
            ('KEYMAP', "Key Maps", "Only show key-maps"),
        ),
        name="Filter by Type",
        description="Show extensions by type",
        default='ALL',
    )
    WindowManager.extension_installed_only = BoolProperty(
        name="Installed Extensions Only",
        description="Only show installed extensions",
    )

    monkeypatch_install()

    # addon_prefs = bpy.context.preferences.addons[__name__].preferences


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
    del WindowManager.extension_installed_only

    for cls in classes:
        bpy.utils.unregister_class(cls)

    if repo_cache_store is None:
        pass
    else:
        repo_cache_store.clear()
        repo_cache_store = None

    monkeypatch_uninstall()
