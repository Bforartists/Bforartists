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
    # "doc_url": "",
    "support": 'OFFICIAL',
    "category": "System",
}

if "bpy" in locals():
    # This doesn't need to be inline because sub-modules aren't important into the global name-space.
    # The check for `bpy` ensures this is always assigned before use.
    # pylint: disable-next=used-before-assignment
    _local_module_reload()

import bpy

from bpy.props import (
    BoolProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)


# -----------------------------------------------------------------------------
# Local Module Reload

def _local_module_reload():
    import importlib
    from . import (
        bl_extension_cli,
        bl_extension_local,
        bl_extension_notify,
        bl_extension_ops,
        bl_extension_ui,
        bl_extension_utils,
    )
    importlib.reload(bl_extension_cli)
    importlib.reload(bl_extension_local)
    importlib.reload(bl_extension_notify)
    importlib.reload(bl_extension_ops)
    importlib.reload(bl_extension_ui)
    importlib.reload(bl_extension_utils)


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
    if repo_item.use_remote_url:
        if not (remote_url := repo_item.remote_url):
            return None, None
    else:
        remote_url = ""
    return directory, remote_url


def repo_active_or_none():
    prefs = bpy.context.preferences
    extensions = prefs.extensions
    active_extension_index = extensions.active_repo
    try:
        active_repo = None if active_extension_index < 0 else extensions.repos[active_extension_index]
    except IndexError:
        active_repo = None
    return active_repo


def repo_stats_calc_outdated_for_repo_directory(repo_directory):

    repo_cache_store = repo_cache_store_ensure()
    pkg_manifest_local = repo_cache_store.refresh_local_from_directory(
        directory=repo_directory,
        error_fn=print,
    )
    if pkg_manifest_local is None:
        return 0

    pkg_manifest_remote = repo_cache_store.refresh_remote_from_directory(
        directory=repo_directory,
        error_fn=print,
    )

    if pkg_manifest_remote is None:
        return 0

    package_count = 0
    for pkg_id, item_local in pkg_manifest_local.items():
        item_remote = pkg_manifest_remote.get(pkg_id)
        # Local-only (unlikely but not impossible).
        if item_remote is None:
            continue

        if item_remote.version != item_local.version:
            package_count += 1
    return package_count


def repo_stats_calc():
    # NOTE: if repositories get very large, this could be optimized to only check repositories that have changed.
    # Although this isn't called all that often - it's unlikely to be a bottleneck.

    if bpy.app.background:
        return

    import os
    package_count = 0

    for repo_item in bpy.context.preferences.extensions.repos:
        if not repo_item.enabled:
            continue
        if not repo_item.use_remote_url:
            continue
        if not repo_item.remote_url:
            continue

        # If the directory is missing, ignore it.
        # Otherwise users may be bothered with errors from unrelated repositories
        # because calculating status currently runs after many actions.
        repo_directory = repo_item.directory
        if not os.path.isdir(repo_directory):
            continue

        package_count += repo_stats_calc_outdated_for_repo_directory(repo_directory)

    bpy.context.window_manager.extensions_updates = package_count


def print_debug(*args, **kw):
    if not bpy.app.debug:
        return
    print(*args, **kw)


def repos_to_notify():
    import os
    from . import bl_extension_ops
    from .bl_extension_utils import (
        repo_index_outdated,
        scandir_with_demoted_errors,
        PKG_MANIFEST_FILENAME_TOML,
    )

    repos_notify = []
    do_online_sync = False

    # To use notifications on startup requires:
    # - The splash displayed.
    # - The status bar displayed.
    #
    # Since it's not all that common to disable the status bar just run notifications
    # if any repositories are marked to run notifications.

    prefs = bpy.context.preferences
    extension_repos = prefs.extensions.repos

    repos_remote = []
    for repo_item in extension_repos:
        if not repo_item.enabled:
            continue
        if not repo_item.use_remote_url:
            continue
        remote_url = repo_item.remote_url
        # Invalid, if there is no remote path this can't update.
        if not remote_url:
            continue

        # WARNING: this could be a more expensive check, use a "reasonable" guess.
        # This is technically incorrect because knowing if a repository has any installed
        # packages requires reading it's meta-data and comparing it with the directory contents.
        # Chances are - if the directory contains *any* directories containing a package manifest
        # this means it has packages installed.
        #
        # Simply check the repositories directory isn't empty (ignoring dot-files).
        # Importantly, this may be false positives but *not* false negatives.
        repo_is_empty = True
        repo_directory = repo_item.directory
        if os.path.isdir(repo_directory):
            for entry in scandir_with_demoted_errors(repo_directory):
                if not entry.is_dir():
                    continue
                if entry.name.startswith("."):
                    continue
                if not os.path.exists(os.path.join(entry.path, PKG_MANIFEST_FILENAME_TOML)):
                    continue
                repo_is_empty = False
                break
        if repo_is_empty:
            continue

        repos_remote.append(repo_item)

    # Update all repos together or none, to avoid bothering users
    # multiple times in a day.
    do_online_sync = False
    for repo_item in repos_remote:
        if not repo_item.use_sync_on_startup:
            continue
        if repo_index_outdated(repo_item.directory):
            do_online_sync = True
            break

    for repo_item in repos_remote:
        repos_notify.append((
            bl_extension_ops.RepoItem(
                name=repo_item.name,
                directory=repo_directory,
                source="" if repo_item.use_remote_url else repo_item.source,
                remote_url=remote_url,
                module=repo_item.module,
                use_cache=repo_item.use_cache,
                access_token=repo_item.access_token if repo_item.use_access_token else "",
            ),
            repo_item.use_sync_on_startup and do_online_sync,
        ))

    return repos_notify


# -----------------------------------------------------------------------------
# Handlers

@bpy.app.handlers.persistent
def extenion_repos_sync(*_):
    # Ignore in background mode as this is for the UI to stay in sync.
    # Automated tasks must sync explicitly.
    if bpy.app.background:
        return

    # This is called from operators (create or an explicit call to sync)
    # so calling a modal operator is "safe".
    if (active_repo := repo_active_or_none()) is None:
        return

    print_debug("SYNC:", active_repo.name)
    # There may be nothing to upgrade.

    if not active_repo.use_remote_url:
        return

    # NOTE: both `extensions.repo_sync_all` and `bl_extension_notify.update_non_blocking` can be used here.
    # Call the modal operator in this case as this handler is called after adding a repository.
    # The operator has the benefit of showing a progress bar and reporting errors.
    # Since this function is used after adding a new repository, it's important the user is aware of any
    # errors synchronizing data as there may be connection/access issues they need to resolve.
    if not bpy.ops.extensions.repo_sync_all.poll():
        print("skipping sync, poll failed")
        return

    from contextlib import redirect_stdout
    import io
    stdout = io.StringIO()

    with redirect_stdout(stdout):
        bpy.ops.extensions.repo_sync_all('INVOKE_DEFAULT', use_active_only=True)

    if text := stdout.getvalue():
        repo_status_text.from_message("Sync \"{:s}\"".format(active_repo.name), text)


@bpy.app.handlers.persistent
def extenion_repos_files_clear(directory, _):
    # Perform a "safe" file deletion by only removing files known to be either
    # packages or known extension meta-data.
    #
    # Safer because removing a repository which points to an arbitrary path
    # has the potential to wipe user data #119481.
    import shutil
    import os
    from .bl_extension_utils import (
        scandir_with_demoted_errors,
        PKG_MANIFEST_FILENAME_TOML,
        REPO_LOCAL_PRIVATE_DIR,
    )
    # Unlikely but possible a new repository is immediately removed before initializing,
    # avoid errors in this case.
    if not os.path.isdir(directory):
        return

    if os.path.isdir(path := os.path.join(directory, REPO_LOCAL_PRIVATE_DIR)):
        try:
            shutil.rmtree(path)
        except Exception as ex:
            print("Failed to remove files", ex)

    for entry in scandir_with_demoted_errors(directory):
        if not entry.is_dir():
            continue
        path = entry.path
        if not os.path.exists(os.path.join(path, PKG_MANIFEST_FILENAME_TOML)):
            continue
        try:
            shutil.rmtree(path)
        except Exception as ex:
            print("Failed to remove files", ex)


# -----------------------------------------------------------------------------
# Wrap Handlers

_monkeypatch_extenions_repos_update_dirs = set()


def monkeypatch_extenions_repos_update_pre_impl():
    _monkeypatch_extenions_repos_update_dirs.clear()

    extension_repos = bpy.context.preferences.extensions.repos
    for repo_item in extension_repos:
        if not repo_item.enabled:
            continue
        directory, _repo_path = repo_paths_or_none(repo_item)
        if directory is None:
            continue

        _monkeypatch_extenions_repos_update_dirs.add(directory)


def monkeypatch_extenions_repos_update_post_impl():
    import os
    # pylint: disable-next=redefined-outer-name
    from . import bl_extension_ops

    repo_cache_store = repo_cache_store_ensure()
    bl_extension_ops.repo_cache_store_refresh_from_prefs(repo_cache_store)

    # Refresh newly added directories.
    extension_repos = bpy.context.preferences.extensions.repos
    for repo_item in extension_repos:
        if not repo_item.enabled:
            continue
        directory, _repo_path = repo_paths_or_none(repo_item)
        if directory is None:
            continue
        # Happens for newly added extension directories.
        if not os.path.exists(directory):
            continue
        if directory in _monkeypatch_extenions_repos_update_dirs:
            continue
        # Ignore missing because the new repo might not have a JSON file.
        repo_cache_store.refresh_remote_from_directory(directory=directory, error_fn=print, force=True)
        repo_cache_store.refresh_local_from_directory(directory=directory, error_fn=print, ignore_missing=True)

    _monkeypatch_extenions_repos_update_dirs.clear()

    # Based on changes, the statistics may need to be re-calculated.
    repo_stats_calc()


@bpy.app.handlers.persistent
def monkeypatch_extensions_repos_update_pre(*_):
    print_debug("PRE:")
    try:
        monkeypatch_extenions_repos_update_pre_impl()
    except Exception as ex:
        print_debug("ERROR", str(ex))
    try:
        monkeypatch_extensions_repos_update_pre._fn_orig()
    except Exception as ex:
        print_debug("ERROR", str(ex))


@bpy.app.handlers.persistent
def monkeypatch_extenions_repos_update_post(*_):
    print_debug("POST:")
    try:
        monkeypatch_extenions_repos_update_post._fn_orig()
    except Exception as ex:
        print_debug("ERROR", str(ex))
    try:
        monkeypatch_extenions_repos_update_post_impl()
    except Exception as ex:
        print_debug("ERROR", str(ex))


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
    for i, fn in enumerate(handlers):
        if fn is fn_override:
            handlers[i] = fn_override._fn_orig
            del fn_override._fn_orig
            break

    handlers = bpy.app.handlers._extension_repos_update_post
    fn_override = monkeypatch_extenions_repos_update_post
    for i, fn in enumerate(handlers):
        if fn is fn_override:
            handlers[i] = fn_override._fn_orig
            del fn_override._fn_orig
            break


# Text to display in the UI (while running...).
repo_status_text = StatusInfoUI()

# Singleton to cache all repositories JSON data and handles refreshing.
_repo_cache_store = None


def repo_cache_store_ensure():
    # pylint: disable-next=global-statement
    global _repo_cache_store

    if _repo_cache_store is not None:
        return _repo_cache_store

    from . import (
        bl_extension_ops,
        bl_extension_utils,
    )
    _repo_cache_store = bl_extension_utils.RepoCacheStore(bpy.app.version)
    bl_extension_ops.repo_cache_store_refresh_from_prefs(_repo_cache_store)
    return _repo_cache_store


def repo_cache_store_clear():
    # pylint: disable-next=global-statement
    global _repo_cache_store

    if _repo_cache_store is None:
        return
    _repo_cache_store.clear()
    _repo_cache_store = None


# -----------------------------------------------------------------------------
# Theme Integration

def theme_preset_draw(menu, context):
    from .bl_extension_utils import (
        pkg_theme_file_list,
    )
    layout = menu.layout
    repos_all = [
        repo_item for repo_item in context.preferences.extensions.repos
        if repo_item.enabled
    ]
    if not repos_all:
        return
    import os
    repo_cache_store = repo_cache_store_ensure()
    menu_idname = type(menu).__name__

    for i, pkg_manifest_local in enumerate(repo_cache_store.pkg_manifest_from_local_ensure(error_fn=print)):
        if pkg_manifest_local is None:
            continue
        repo_item = repos_all[i]
        directory = repo_item.directory
        for pkg_idname, value in pkg_manifest_local.items():
            if value.type != "theme":
                continue

            theme_dir, theme_files = pkg_theme_file_list(directory, pkg_idname)
            for filename in theme_files:
                props = layout.operator(menu.preset_operator, text=bpy.path.display_name(filename))
                props.filepath = os.path.join(theme_dir, filename)
                props.menu_idname = menu_idname


def cli_extension(argv):
    from . import bl_extension_cli
    return bl_extension_cli.cli_extension_handler(argv)


class BlExtDummyGroup(bpy.types.PropertyGroup):
    # Dummy.
    pass


# -----------------------------------------------------------------------------
# Registration

classes = (
    BlExtDummyGroup,
)

cli_commands = []


def register():
    prefs = bpy.context.preferences

    from bpy.types import WindowManager
    from . import (
        bl_extension_ops,
        bl_extension_ui,
    )

    repo_cache_store_clear()

    for cls in classes:
        bpy.utils.register_class(cls)

    bl_extension_ops.register()
    bl_extension_ui.register()

    WindowManager.addon_tags = PointerProperty(
        name="Addon Tags",
        type=BlExtDummyGroup,
    )
    WindowManager.extension_tags = PointerProperty(
        name="Extension Tags",
        type=BlExtDummyGroup,
    )

    WindowManager.extension_search = StringProperty(
        name="Filter",
        description="Filter by extension name, author & category",
        options={'TEXTEDIT_UPDATE'},
    )
    WindowManager.extension_type = EnumProperty(
        items=(
            ('ADDON', "Add-ons", "Only show add-ons"),
            ('THEME', "Themes", "Only show themes"),
        ),
        name="Filter by Type",
        description="Show extensions by type",
        default='ADDON',
    )
    WindowManager.extension_enabled_only = BoolProperty(
        name="Show Enabled Extensions",
        description="Only show enabled extensions",
    )
    WindowManager.extension_updates_only = BoolProperty(
        name="Show Updates Available",
        description="Only show extensions with updates available",
    )
    WindowManager.extension_installed_only = BoolProperty(
        name="Show Installed Extensions",
        description="Only show installed extensions",
    )

    from bl_ui.space_userpref import USERPREF_MT_interface_theme_presets
    USERPREF_MT_interface_theme_presets.append(theme_preset_draw)

    handlers = bpy.app.handlers._extension_repos_sync
    handlers.append(extenion_repos_sync)

    handlers = bpy.app.handlers._extension_repos_files_clear
    handlers.append(extenion_repos_files_clear)

    cli_commands.append(bpy.utils.register_cli_command("extension", cli_extension))

    monkeypatch_install()

    if not bpy.app.background:
        if prefs.view.show_extensions_updates:
            from . import bl_extension_notify
            bl_extension_notify.update_non_blocking(repos_fn=repos_to_notify)


def unregister():
    from bpy.types import WindowManager
    from . import (
        bl_extension_ops,
        bl_extension_ui,
    )

    bl_extension_ops.unregister()
    bl_extension_ui.unregister()

    del WindowManager.extension_tags
    del WindowManager.extension_search
    del WindowManager.extension_type
    del WindowManager.extension_enabled_only
    del WindowManager.extension_installed_only

    for cls in classes:
        bpy.utils.unregister_class(cls)

    repo_cache_store_clear()

    from bl_ui.space_userpref import USERPREF_MT_interface_theme_presets
    USERPREF_MT_interface_theme_presets.remove(theme_preset_draw)

    handlers = bpy.app.handlers._extension_repos_sync
    if extenion_repos_sync in handlers:
        handlers.remove(extenion_repos_sync)

    handlers = bpy.app.handlers._extension_repos_files_clear
    if extenion_repos_files_clear in handlers:
        handlers.remove(extenion_repos_files_clear)

    for cmd in cli_commands:
        bpy.utils.unregister_cli_command(cmd)
    cli_commands.clear()

    monkeypatch_uninstall()
