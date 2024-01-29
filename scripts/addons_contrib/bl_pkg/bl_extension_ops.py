# SPDX-FileCopyrightText: 2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Blender, thin wrapper around ``blender_extension_utils``.
Where the operator shows progress, any errors and supports canceling operations.

 /src/blender/blender.bin --factory-startup --python ./blender/bl_extension_ops.py

bpy.ops.bl_pkg.demo('INVOKE_DEFAULT')

/src/blender/blender.bin \
    --factory-startup --python ./blender/bl_extension_ops.py -b \
    --python-expr "__import__('bpy').ops.bl_pkg.demo()"
"""

__all__ = (
    "extension_repos_read",
)

import os

from functools import partial

from typing import (
    NamedTuple,
)

import bpy

from bpy.types import (
    Operator,
)
from bpy.props import (
    StringProperty,
    # BoolProperty,
    IntProperty,
)
from bpy.app.translations import (
    pgettext_iface as iface_,
)

# Localize imports.
from . import (
    bl_extension_utils,
)  # noqa: E402

from . import (
    repo_status_text,
    cookie_from_session,
)

from .bl_extension_utils import (
    RepoLock,
    RepoLockContext,
)

# Enable extensions when they're installed.
USE_ENABLE_ON_INSTALL = True


rna_prop_directory = StringProperty(name="Directory", subtype='FILE_PATH')
rna_prop_repo_index = IntProperty(name="Repo Index", default=-1)
rna_prop_repo_url = StringProperty(name="Repo URL", subtype='FILE_PATH')
rna_prop_pkg_id = StringProperty(name="Package ID")


is_background = bpy.app.background

# Execute tasks concurrently.
is_concurrent = True

# Selected check-boxes.
blender_extension_mark = set()
blender_extension_show = set()


# Map the enum value to the value in the manifest.
blender_filter_by_type_map = {
    "ALL": "",
    "ADDON": "add-on",
    "KEYMAP": "key-map",
    "THEME": "theme",
}


# -----------------------------------------------------------------------------
# Signal Context Manager (Catch Control-C)
#


class CheckSIGINT_Context:
    __slots__ = (
        "has_interrupt",
        "_old_fn",
    )

    def _signal_handler_sigint(self, _, __):
        self.has_interrupt = True
        print("INTERRUPT")

    def __init__(self):
        self.has_interrupt = False
        self._old_fn = None

    def __enter__(self):
        import signal
        self._old_fn = signal.signal(signal.SIGINT, self._signal_handler_sigint)
        return self

    def __exit__(self, _ty, _value, _traceback):
        import signal
        signal.signal(signal.SIGINT, self._old_fn or signal.SIG_DFL)


# -----------------------------------------------------------------------------
# Internal Utilities
#

def lock_result_any_failed_with_report(op, lock_result, report_type='ERROR'):
    """
    Convert any locking errors from ``bl_extension_utils.RepoLock.acquire`` into reports.

    Note that we might want to allow some repositories not to lock and still proceed (in the future).
    """
    any_errors = False
    for directory, lock_result_for_repo in lock_result.items():
        if lock_result_for_repo is None:
            continue
        print("Error \"{:s}\" locking \"{:s}\"".format(lock_result_for_repo, repr(directory)))
        op.report({report_type}, lock_result_for_repo)
        any_errors = True
    return any_errors


def pkg_info_check_exclude_filter(item, search_lower):
    return (
        (search_lower in item["name"].lower() or search_lower in iface_(item["name"]).lower()) or
        (search_lower in item["description"].lower() or search_lower in iface_(item["description"]).lower())
    )


class RepoItem(NamedTuple):
    name: str
    directory: str
    repo_url: str
    module: str
    use_cache: bool


def repo_cache_store_refresh_from_prefs(include_disabled=False):
    from . import repo_cache_store
    extension_repos = bpy.context.preferences.filepaths.extension_repos
    repo_cache_store.refresh_from_repos(
        repos=[
            (repo.directory_or_default, repo.remote_path) for repo in extension_repos
            if include_disabled or repo.enabled
        ],
    )


def _preferences_ensure_disabled(*, repo_item, pkg_id_sequence, default_set):
    import sys
    import addon_utils

    result = {}
    errors = []

    def handle_error(ex):
        print("Error:", ex)
        errors.append(str(ex))

    modules_clear = []

    module_base_elem = ("bl_ext", repo_item.module)

    repo_module = sys.modules.get(".".join(module_base_elem))
    if repo_module is None:
        print("Repo module \"{:s}\" not in \"sys.modules\", unexpected!".format(".".join(module_base_elem)))

    for pkg_id in pkg_id_sequence:
        addon_module_elem = (*module_base_elem, pkg_id)
        addon_module_name = ".".join(addon_module_elem)
        loaded_default, loaded_state = addon_utils.check(addon_module_name)

        result[addon_module_name] = loaded_default, loaded_state

        # Not loaded or default, skip.
        if not (loaded_default or loaded_state):
            continue

        # This report isn't needed, it just shows a warning in the case of irregularities
        # which may be useful when debugging issues.
        if repo_module is not None:
            if not hasattr(repo_module, pkg_id):
                print("Repo module \"{:s}.{:s}\" not a sub-module!".format(".".join(module_base_elem), pkg_id))

        addon_utils.disable(addon_module_name, default_set=default_set, handle_error=handle_error)

        modules_clear.append(pkg_id)

    # Clear modules.

    # Extensions, repository & final `.` to ensure the module is part of the repository.
    prefix_base = ".".join(module_base_elem) + "."
    # Needed for `startswith` check.
    prefix_addon_modules = {prefix_base + pkg_id for pkg_id in modules_clear}
    # Needed for `startswith` check (sub-modules).
    prefix_addon_modules_base = tuple([module + "." for module in prefix_addon_modules])

    # NOTE(@ideasman42): clearing the modules is not great practice,
    # however we need to ensure this is fully un-loaded then reloaded.
    for key, value in list(sys.modules.items()):
        if not key.startswith(prefix_base):
            continue
        if not (
                # This module is the add-on.
                key in prefix_addon_modules or
                # This module is a sub-module of the add-on.
                key.startswith(prefix_addon_modules_base)
        ):
            continue

        # Use pop instead of del because there is a (very) small chance
        # that classes defined in a removed module define a `__del__` method manipulates modules.
        sys.modules.pop(key, None)

    # Now remove from the module from it's parent (when found).
    # Although in most cases this isn't needed because disabling the add-on typically deletes the module,
    # don't report a warning if this is the case.
    if repo_module is not None:
        for pkg_id in pkg_id_sequence:
            if not hasattr(repo_module, pkg_id):
                continue
            delattr(repo_module, pkg_id)

    return result, errors


def _preferences_ensure_enabled(*, repo_item, pkg_id_sequence, result):
    import addon_utils

    errors = []

    def handle_error(ex):
        print("Error:", ex)
        errors.append(str(ex))

    for addon_module_name, (loaded_default, loaded_state) in result.items():
        # The module was not loaded, so no need to restore it.
        if not loaded_state:
            continue

        addon_utils.enable(addon_module_name, default_set=loaded_default, handle_error=handle_error)


def _preferences_ui_redraw():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != 'PREFERENCES':
                continue
            area.tag_redraw()


def _preferences_ui_refresh_addons():
    import addon_utils
    # TODO: make a public method.
    addon_utils.modules._is_first = True


def extension_repos_read_index(index):
    extension_repos = bpy.context.preferences.filepaths.extension_repos
    index_test = 0
    for repo_item in extension_repos:
        if not repo_item.enabled:
            continue
        if index == index_test:
            return RepoItem(
                name=repo_item.name,
                directory=repo_item.directory_or_default,
                repo_url=repo_item.remote_path,
                module=repo_item.module,
                use_cache=repo_item.use_cache,
            )
        index_test += 1
    return None


def extension_repos_read(include_disabled=False):
    extension_repos = bpy.context.preferences.filepaths.extension_repos
    return [
        RepoItem(
            name=repo_item.name,
            directory=repo_item.directory_or_default,
            repo_url=repo_item.remote_path,
            module=repo_item.module,
            use_cache=repo_item.use_cache,
        )
        for repo_item in extension_repos
        if include_disabled or repo_item.enabled
    ]


def _extension_repos_index_from_directory(directory):
    directory = os.path.normpath(directory)
    repos_all = extension_repos_read()
    for i, repo_item in enumerate(repos_all):
        if os.path.normpath(repo_item.directory) == directory:
            return i
    if os.path.exists(directory):
        for i, repo_item in enumerate(repos_all):
            if os.path.normpath(repo_item.directory) == directory:
                return i
    return -1


def _extension_repos_add(directory, repo_url):
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    repo_item = addon_prefs.repos.add()
    repo_item.directory = directory
    repo_item.repo_url = repo_url
    # Pick a name, the update function ensures it's a valid module name & unique.
    repo_item.module = directory.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
    addon_prefs.active_repo_index = len(addon_prefs.repos) - 1


def _extension_repos_remove(directory):
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    i = _extension_repos_index_from_directory(directory)
    if i == -1:
        return
    if i >= addon_prefs.active_repo_index:
        addon_prefs.active_repo_index -= 1
    addon_prefs.repos.remove(i)


def _extensions_repo_from_directory(directory):
    repos_all = extension_repos_read()
    repo_index = _extension_repos_index_from_directory(directory)
    if repo_index == -1:
        return None
    return repos_all[repo_index]


def _extensions_repo_from_directory_and_report(directory, report_fn):
    if not directory:
        report_fn({'ERROR', "Directory not set"})
        return None

    repo_item = _extensions_repo_from_directory(directory)
    if repo_item is None:
        report_fn({'ERROR'}, "Directory has no repo entry: {:s}".format(directory))
        return None
    return repo_item


def _pkg_marked_by_repo(pkg_manifest_all):
    # NOTE: pkg_manifest_all can be from local or remote source.
    wm = bpy.context.window_manager
    search_lower = wm.extension_search.lower()
    filter_by_type = blender_filter_by_type_map[wm.extension_type]

    repo_pkg_map = {}
    for pkg_id, repo_index in blender_extension_mark:
        # While this should be prevented, any marked packages out of the range will cause problems, skip them.
        if repo_index >= len(pkg_manifest_all):
            continue

        pkg_manifest = pkg_manifest_all[repo_index]
        item = pkg_manifest.get(pkg_id)
        if item is None:
            continue
        if filter_by_type and (filter_by_type != item["type"]):
            continue
        if search_lower and not pkg_info_check_exclude_filter(item, search_lower):
            continue

        pkg_list = repo_pkg_map.get(repo_index)
        if pkg_list is None:
            pkg_list = repo_pkg_map[repo_index] = []
        pkg_list.append(pkg_id)
    return repo_pkg_map


# -----------------------------------------------------------------------------
# Internal Implementation
#

def _is_modal(op):
    if is_background:
        return False
    if not op.options.is_invoke:
        return False
    return True


class CommandHandle:
    __slots__ = (
        "modal_timer",
        "cmd_batch",
        "wm",
        "request_exit",
    )

    def __init__(self):
        self.modal_timer = None
        self.cmd_batch = None
        self.wm = None
        self.request_exit = None

    @staticmethod
    def op_exec_from_iter(op, context, cmd_batch, is_modal):
        if not is_modal:
            with CheckSIGINT_Context() as sigint_ctx:
                has_request_exit = cmd_batch.exec_blocking(
                    report_fn=_report,
                    request_exit_fn=lambda: sigint_ctx.has_interrupt,
                    concurrent=is_concurrent,
                )
            if has_request_exit:
                op.report({'WARNING'}, "Command interrupted")
                return {'FINISHED'}

            return {'FINISHED'}

        handle = CommandHandle()
        handle.cmd_batch = cmd_batch
        handle.modal_timer = context.window_manager.event_timer_add(0.01, window=context.window)
        handle.wm = context.window_manager

        handle.wm.modal_handler_add(op)
        op._runtime_handle = handle
        return {'RUNNING_MODAL'}

    def op_modal_step(self, op, context):
        command_info = self.cmd_batch.exec_non_blocking(
            request_exit=self.request_exit,
        )
        if command_info is None:
            self.wm.event_timer_remove(self.modal_timer)
            del op._runtime_handle
            context.workspace.status_text_set(None)
            repo_status_text.running = False
            return {'FINISHED'}

        # Avoid high CPU usage by only redrawing when there has been a change.
        msg_list = self.cmd_batch.calc_status_log_or_none()
        if msg_list is not None:
            context.workspace.status_text_set(
                " | ".join(
                    ["{:s}: {:s}".format(ty, str(msg)) for (ty, msg) in msg_list]
                )
            )

            # Setting every time is a bit odd. but OK.
            repo_status_text.title = self.cmd_batch.title
            repo_status_text.log = msg_list
            repo_status_text.running = True
            _preferences_ui_redraw()

        return {'RUNNING_MODAL'}

    def op_modal_impl(self, op, context, event):
        refresh = False
        if event.type == 'TIMER':
            refresh = True
        elif event.type == 'ESC':
            if not self.request_exit:
                print("Request exit!")
                self.request_exit = True
                refresh = True

        if refresh:
            return self.op_modal_step(op, context)
        return {'RUNNING_MODAL'}


def _report(ty, msg):
    if ty == 'DONE':
        assert msg == ""
        return

    if is_background:
        print(ty, msg)
        return


def _repo_dir_and_index_get(repo_index, directory, report_fn):
    if repo_index != -1:
        repo_item = extension_repos_read_index(repo_index)
        directory = repo_item.directory if (repo_item is not None) else ""
    if not directory:
        report_fn({'ERROR'}, "Repository not set")
    return directory


# -----------------------------------------------------------------------------
# Public Repository Actions
#

class _BlPkgCmdMixIn:
    """
    Utility to execute mix-in.

    Sub-class must define.
    - bl_idname
    - bl_label
    - exec_command_iter
    - exec_command_finish
    """
    cls_slots = (
        "_runtime_handle",
    )

    @classmethod
    def __init_subclass__(cls) -> None:
        for attr in ("exec_command_iter", "exec_command_finish"):
            if getattr(cls, attr) is getattr(_BlPkgCmdMixIn, attr):
                raise Exception("Subclass did not define 'exec_command_iter'!")

    def exec_command_iter(self, is_modal):
        raise Exception("Subclass must define!")

    def exec_command_finish(self):
        raise Exception("Subclass must define!")

    def execute(self, context):
        is_modal = _is_modal(self)
        cmd_batch = self.exec_command_iter(is_modal)
        # It's possible the action could not be started.
        # In this case `exec_command_iter` should report an error.
        if cmd_batch is None:
            return {'CANCELLED'}
        result = CommandHandle.op_exec_from_iter(self, context, cmd_batch, is_modal)
        if 'FINISHED' in result:
            self.exec_command_finish()
        return result

    def modal(self, context, event):
        result = self._runtime_handle.op_modal_impl(self, context, event)
        if 'FINISHED' in result:
            self.exec_command_finish()
        return result


class BlPkgDummyProgress(Operator, _BlPkgCmdMixIn):
    bl_idname = "bl_pkg.dummy_progress"
    bl_label = "Ext Demo"
    __slots__ = _BlPkgCmdMixIn.cls_slots

    def exec_command_iter(self, is_modal):
        return bl_extension_utils.CommandBatch(
            title="Dummy Progress",
            batch=[
                partial(
                    bl_extension_utils.dummy_progress,
                    use_idle=is_modal,
                ),
            ],
        )

    def exec_command_finish(self):
        _preferences_ui_redraw()


class BlPkgRepoSync(Operator, _BlPkgCmdMixIn):
    bl_idname = "bl_pkg.repo_sync"
    bl_label = "Ext Repo Sync"
    __slots__ = _BlPkgCmdMixIn.cls_slots + (
        "directory",
    )

    directory: rna_prop_directory
    repo_index: rna_prop_repo_index

    def exec_command_iter(self, is_modal):
        directory = _repo_dir_and_index_get(self.repo_index, self.directory, self.report)
        if not directory:
            return None

        if (repo_item := _extensions_repo_from_directory_and_report(directory, self.report)) is None:
            return None

        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except BaseException as ex:
                self.report({'ERROR'}, str(ex))
                return {'CANCELLED'}

        # Needed to refresh.
        self.directory = directory

        # Lock repositories.
        self.repo_lock = RepoLock(repo_directories=[directory], cookie=cookie_from_session())
        if lock_result_any_failed_with_report(self, self.repo_lock.acquire()):
            return None

        return bl_extension_utils.CommandBatch(
            title="Sync",
            batch=[
                partial(
                    bl_extension_utils.repo_sync,
                    directory=directory,
                    repo_url=repo_item.repo_url,
                    use_idle=is_modal,
                )
            ],
        )

    def exec_command_finish(self):
        from . import repo_cache_store

        # Unlock repositories.
        lock_result_any_failed_with_report(self, self.repo_lock.release(), report_type='WARNING')
        del self.repo_lock

        repo_cache_store_refresh_from_prefs()
        repo_cache_store.refresh_remote_from_directory(directory=self.directory, force=True)
        _preferences_ui_redraw()


class BlPkgRepoSyncAll(Operator, _BlPkgCmdMixIn):
    bl_idname = "bl_pkg.repo_sync_all"
    bl_label = "Ext Repo Sync All"
    __slots__ = _BlPkgCmdMixIn.cls_slots

    def exec_command_iter(self, is_modal):
        repos_all = extension_repos_read()
        if not repos_all:
            self.report({'INFO'}, "No repositories to sync")
            return None

        for repo_item in repos_all:
            if not os.path.exists(repo_item.directory):
                try:
                    os.makedirs(repo_item.directory)
                except BaseException as ex:
                    self.report({'ERROR'}, str(ex))
                    return None

        cmd_batch = []
        for repo_item in repos_all:
            cmd_batch.append(partial(
                bl_extension_utils.repo_sync,
                directory=repo_item.directory,
                repo_url=repo_item.repo_url,
                use_idle=is_modal,
            ))

        repos_lock = [repo_item.directory for repo_item in repos_all]

        # Lock repositories.
        self.repo_lock = RepoLock(repo_directories=repos_lock, cookie=cookie_from_session())
        if lock_result_any_failed_with_report(self, self.repo_lock.acquire()):
            return None

        return bl_extension_utils.CommandBatch(
            title="Sync All",
            batch=cmd_batch,
        )

    def exec_command_finish(self):
        from . import repo_cache_store

        # Unlock repositories.
        lock_result_any_failed_with_report(self, self.repo_lock.release(), report_type='WARNING')
        del self.repo_lock

        repo_cache_store_refresh_from_prefs()

        for repo_item in extension_repos_read():
            repo_cache_store.refresh_remote_from_directory(directory=repo_item.directory, force=True)

        _preferences_ui_redraw()


class BlPkgPkgUpgradeAll(Operator, _BlPkgCmdMixIn):
    bl_idname = "bl_pkg.pkg_upgrade_all"
    bl_label = "Ext Package Upgrade All"
    __slots__ = _BlPkgCmdMixIn.cls_slots + (
        "_repo_directories",
    )

    def exec_command_iter(self, is_modal):
        from . import repo_cache_store
        self._repo_directories = set()
        self._addon_restore = []

        repos_all = extension_repos_read()

        # Track add-ons to disable before uninstalling.
        handle_addons_info = []

        packages_to_upgrade = [[] for _ in range(len(repos_all))]
        package_count = 0

        pkg_manifest_local_all = list(repo_cache_store.pkg_manifest_from_local_ensure())
        for repo_index, pkg_manifest_remote in enumerate(repo_cache_store.pkg_manifest_from_remote_ensure()):
            if pkg_manifest_remote is None:
                continue

            pkg_manifest_local = pkg_manifest_local_all[repo_index]
            if pkg_manifest_local is None:
                continue

            for pkg_id, item_remote in pkg_manifest_remote.items():
                item_local = pkg_manifest_local.get(pkg_id)
                if item_local is None:
                    # Not installed.
                    continue

                if item_remote["version"] != item_local["version"]:
                    packages_to_upgrade[repo_index].append(pkg_id)
                    package_count += 1

            if packages_to_upgrade[repo_index]:
                handle_addons_info.append((repos_all[repo_index], list(packages_to_upgrade[repo_index])))

        cmd_batch = []
        for repo_index, pkg_id_sequence in enumerate(packages_to_upgrade):
            if not pkg_id_sequence:
                continue
            repo_item = repos_all[repo_index]
            cmd_batch.append(partial(
                bl_extension_utils.pkg_install,
                directory=repo_item.directory,
                repo_url=repo_item.repo_url,
                pkg_id_sequence=pkg_id_sequence,
                use_cache=repo_item.use_cache,
                use_idle=is_modal,
            ))
            self._repo_directories.add(repo_item.directory)

        if not cmd_batch:
            self.report({'ERROR'}, "No installed packages to upgrade")
            return None

        # Lock repositories.
        self.repo_lock = RepoLock(repo_directories=list(self._repo_directories), cookie=cookie_from_session())
        if lock_result_any_failed_with_report(self, self.repo_lock.acquire()):
            return None

        for repo_item, pkg_id_sequence in handle_addons_info:
            result, errors = _preferences_ensure_disabled(
                repo_item=repo_item,
                pkg_id_sequence=pkg_id_sequence,
                default_set=False,
            )
            self._addon_restore.append((repo_item, pkg_id_sequence, result))

        return bl_extension_utils.CommandBatch(
            title="Update {:d} Package(s)".format(package_count),
            batch=cmd_batch,
        )

    def exec_command_finish(self):

        # Unlock repositories.
        lock_result_any_failed_with_report(self, self.repo_lock.release(), report_type='WARNING')
        del self.repo_lock

        # Refresh installed packages for repositories that were operated on.
        from . import repo_cache_store
        for directory in self._repo_directories:
            repo_cache_store.refresh_local_from_directory(directory=directory)

        for repo_item, pkg_id_sequence, result in self._addon_restore:
            _preferences_ensure_enabled(
                repo_item=repo_item,
                pkg_id_sequence=pkg_id_sequence,
                result=result,
            )

        _preferences_ui_redraw()
        _preferences_ui_refresh_addons()


class BlPkgPkgInstallMarked(Operator, _BlPkgCmdMixIn):
    bl_idname = "bl_pkg.pkg_install_marked"
    bl_label = "Ext Package Install_marked"
    __slots__ = _BlPkgCmdMixIn.cls_slots + (
        "_repo_directories",
    )

    def exec_command_iter(self, is_modal):
        from . import repo_cache_store
        repos_all = extension_repos_read()
        pkg_manifest_remote_all = list(repo_cache_store.pkg_manifest_from_remote_ensure())
        repo_pkg_map = _pkg_marked_by_repo(pkg_manifest_remote_all)
        self._repo_directories = set()
        package_count = 0

        cmd_batch = []
        for repo_index, pkg_id_sequence in sorted(repo_pkg_map.items()):
            repo_item = repos_all[repo_index]
            # Filter out already installed.
            pkg_manifest_local = repo_cache_store.refresh_local_from_directory(repo_item.directory)
            if pkg_manifest_local is None:
                continue
            pkg_id_sequence = [pkg_id for pkg_id in pkg_id_sequence if pkg_id not in pkg_manifest_local]
            if not pkg_id_sequence:
                continue

            cmd_batch.append(partial(
                bl_extension_utils.pkg_install,
                directory=repo_item.directory,
                repo_url=repo_item.repo_url,
                pkg_id_sequence=pkg_id_sequence,
                use_cache=repo_item.use_cache,
                use_idle=is_modal,
            ))
            self._repo_directories.add(repo_item.directory)
            package_count += len(pkg_id_sequence)

        if not cmd_batch:
            self.report({'ERROR'}, "No un-installed packages marked")
            return None

        # Lock repositories.
        self.repo_lock = RepoLock(repo_directories=list(self._repo_directories), cookie=cookie_from_session())
        if lock_result_any_failed_with_report(self, self.repo_lock.acquire()):
            return None

        return bl_extension_utils.CommandBatch(
            title="Install {:d} Marked Package(s)".format(package_count),
            batch=cmd_batch,
        )

    def exec_command_finish(self):

        # Unlock repositories.
        lock_result_any_failed_with_report(self, self.repo_lock.release(), report_type='WARNING')
        del self.repo_lock

        # Refresh installed packages for repositories that were operated on.
        from . import repo_cache_store
        for directory in self._repo_directories:
            repo_cache_store.refresh_local_from_directory(directory=directory)

        _preferences_ui_redraw()
        _preferences_ui_refresh_addons()


class BlPkgPkgUninstallMarked(Operator, _BlPkgCmdMixIn):
    bl_idname = "bl_pkg.pkg_uninstall_marked"
    bl_label = "Ext Package Uninstall_marked"
    __slots__ = _BlPkgCmdMixIn.cls_slots + (
        "_repo_directories",
    )

    def exec_command_iter(self, is_modal):
        from . import repo_cache_store
        # TODO: check if the packages are already installed (notify the user).
        # Perhaps re-install?
        repos_all = extension_repos_read()
        pkg_manifest_local_all = list(repo_cache_store.pkg_manifest_from_local_ensure())
        repo_pkg_map = _pkg_marked_by_repo(pkg_manifest_local_all)
        package_count = 0

        self._repo_directories = set()

        # Track add-ons to disable before uninstalling.
        handle_addons_info = []

        cmd_batch = []
        for repo_index, pkg_id_sequence in sorted(repo_pkg_map.items()):
            repo_item = repos_all[repo_index]

            # Filter out not installed.
            pkg_manifest_local = repo_cache_store.refresh_local_from_directory(repo_item.directory)
            if pkg_manifest_local is None:
                continue
            pkg_id_sequence = [pkg_id for pkg_id in pkg_id_sequence if pkg_id in pkg_manifest_local]
            if not pkg_id_sequence:
                continue

            cmd_batch.append(
                partial(
                    bl_extension_utils.pkg_uninstall,
                    directory=repo_item.directory,
                    pkg_id_sequence=pkg_id_sequence,
                    use_idle=is_modal,
                ))
            self._repo_directories.add(repo_item.directory)
            package_count += len(pkg_id_sequence)

            handle_addons_info.append((repo_item, pkg_id_sequence))

        if not cmd_batch:
            self.report({'ERROR'}, "No installed packages marked")
            return None

        # Lock repositories.
        self.repo_lock = RepoLock(repo_directories=list(self._repo_directories), cookie=cookie_from_session())
        if lock_result_any_failed_with_report(self, self.repo_lock.acquire()):
            return None

        for repo_item, pkg_id_sequence in handle_addons_info:
            # No need to store the result (`_`) because the add-ons aren't going to be enabled again.
            _, errors = _preferences_ensure_disabled(
                repo_item=repo_item,
                pkg_id_sequence=pkg_id_sequence,
                default_set=True,
            )

        return bl_extension_utils.CommandBatch(
            title="Uninstall {:d} Marked Package(s)".format(package_count),
            batch=cmd_batch,
        )

    def exec_command_finish(self):

        # Unlock repositories.
        lock_result_any_failed_with_report(self, self.repo_lock.release(), report_type='WARNING')
        del self.repo_lock

        # Refresh installed packages for repositories that were operated on.
        from . import repo_cache_store
        for directory in self._repo_directories:
            repo_cache_store.refresh_local_from_directory(directory=directory)

        _preferences_ui_redraw()
        _preferences_ui_refresh_addons()


class BlPkgPkgInstall(Operator, _BlPkgCmdMixIn):
    bl_idname = "bl_pkg.pkg_install"
    bl_label = "Ext Package Install"
    __slots__ = _BlPkgCmdMixIn.cls_slots

    directory: rna_prop_directory
    repo_index: rna_prop_repo_index

    pkg_id: rna_prop_pkg_id

    def exec_command_iter(self, is_modal):
        self._addon_restore = []

        directory = _repo_dir_and_index_get(self.repo_index, self.directory, self.report)
        if not directory:
            return None
        self.directory = directory

        if (repo_item := _extensions_repo_from_directory_and_report(directory, self.report)) is None:
            return None

        if not (pkg_id := self.pkg_id):
            self.report({'ERROR'}, "Package ID not set")
            return None

        # Detect upgrade.
        from . import repo_cache_store
        pkg_manifest_local = repo_cache_store.refresh_local_from_directory(directory=self.directory)
        is_installed = pkg_manifest_local is not None and (pkg_id in pkg_manifest_local)
        del repo_cache_store, pkg_manifest_local

        if is_installed:
            pkg_id_sequence = (pkg_id,)
            result, errors = _preferences_ensure_disabled(
                repo_item=repo_item,
                pkg_id_sequence=pkg_id_sequence,
                default_set=False,
            )
            self._addon_restore.append((repo_item, pkg_id_sequence, result))
            del pkg_id_sequence

        # Lock repositories.
        self.repo_lock = RepoLock(repo_directories=[repo_item.directory], cookie=cookie_from_session())
        if lock_result_any_failed_with_report(self, self.repo_lock.acquire()):
            return None

        return bl_extension_utils.CommandBatch(
            title="Install Package",
            batch=[
                partial(
                    bl_extension_utils.pkg_install,
                    directory=directory,
                    repo_url=repo_item.repo_url,
                    pkg_id_sequence=(pkg_id,),
                    use_cache=repo_item.use_cache,
                    use_idle=is_modal,
                )
            ],
        )

    def exec_command_finish(self):

        # Unlock repositories.
        lock_result_any_failed_with_report(self, self.repo_lock.release(), report_type='WARNING')
        del self.repo_lock

        # Refresh installed packages for repositories that were operated on.
        from . import repo_cache_store
        repo_cache_store.refresh_local_from_directory(directory=self.directory)

        _preferences_ui_redraw()
        _preferences_ui_refresh_addons()

        if self._addon_restore:
            # Upgrade.
            for repo_item, pkg_id_sequence, result in self._addon_restore:
                _preferences_ensure_enabled(
                    repo_item=repo_item,
                    pkg_id_sequence=pkg_id_sequence,
                    result=result,
                )
        else:
            # Install.
            if USE_ENABLE_ON_INSTALL:
                import addon_utils

                # TODO: it would be nice to include this message in the banner.
                def handle_error(ex):
                    self.report({'ERROR'}, str(ex))

                repo_item = _extensions_repo_from_directory(self.directory)
                addon_module_name = "bl_ext.{:s}.{:s}".format(repo_item.module, self.pkg_id)
                addon_utils.enable(addon_module_name, default_set=True, handle_error=handle_error)


class BlPkgPkgUninstall(Operator, _BlPkgCmdMixIn):
    bl_idname = "bl_pkg.pkg_uninstall"
    bl_label = "Ext Package Uninstall"
    __slots__ = _BlPkgCmdMixIn.cls_slots

    directory: rna_prop_directory
    repo_index: rna_prop_repo_index

    pkg_id: rna_prop_pkg_id

    def exec_command_iter(self, is_modal):

        directory = _repo_dir_and_index_get(self.repo_index, self.directory, self.report)
        if not directory:
            return None
        self.directory = directory

        if (repo_item := _extensions_repo_from_directory_and_report(directory, self.report)) is None:
            return None

        if not (pkg_id := self.pkg_id):
            self.report({'ERROR'}, "Package ID not set")
            return None

        _, errors = _preferences_ensure_disabled(
            repo_item=repo_item,
            pkg_id_sequence=(pkg_id,),
            default_set=True,
        )

        # Lock repositories.
        self.repo_lock = RepoLock(repo_directories=[repo_item.directory], cookie=cookie_from_session())
        if lock_result_any_failed_with_report(self, self.repo_lock.acquire()):
            return None

        return bl_extension_utils.CommandBatch(
            title="Uninstall Package",
            batch=[
                partial(
                    bl_extension_utils.pkg_uninstall,
                    directory=directory,
                    pkg_id_sequence=(pkg_id, ),
                    use_idle=is_modal,
                ),
            ],
        )

    def exec_command_finish(self):

        # Unlock repositories.
        lock_result_any_failed_with_report(self, self.repo_lock.release(), report_type='WARNING')
        del self.repo_lock

        # Refresh installed packages for repositories that were operated on.
        from . import repo_cache_store
        repo_cache_store.refresh_local_from_directory(directory=self.directory)

        _preferences_ui_redraw()
        _preferences_ui_refresh_addons()


# -----------------------------------------------------------------------------
# Non Wrapped Actions
#
# These actions don't wrap command line access.
#
# NOTE: create/destroy might not be best names.

class BlPkgStatusClear(Operator):
    bl_idname = "bl_pkg.pkg_status_clear"
    bl_label = "Clear Status"

    def execute(self, _context):
        repo_status_text.running = False
        repo_status_text.log.clear()
        _preferences_ui_redraw()
        return {'FINISHED'}


class BlPkgPkgMarkSet(Operator):
    bl_idname = "bl_pkg.pkg_mark_set"
    bl_label = "Mark Package"

    pkg_id: rna_prop_pkg_id
    repo_index: rna_prop_repo_index

    def execute(self, _context):
        key = (self.pkg_id, self.repo_index)
        blender_extension_mark.add(key)
        _preferences_ui_redraw()
        return {'FINISHED'}


class BlPkgPkgMarkClear(Operator):
    bl_idname = "bl_pkg.pkg_mark_clear"
    bl_label = "Mark Package"

    pkg_id: rna_prop_pkg_id
    repo_index: rna_prop_repo_index

    def execute(self, _context):
        key = (self.pkg_id, self.repo_index)
        blender_extension_mark.discard(key)
        _preferences_ui_redraw()
        return {'FINISHED'}


class BlPkgPkgShowSet(Operator):
    bl_idname = "bl_pkg.pkg_show_set"
    bl_label = "Show Package Set"

    pkg_id: rna_prop_pkg_id
    repo_index: rna_prop_repo_index

    def execute(self, _context):
        key = (self.pkg_id, self.repo_index)
        blender_extension_show.add(key)
        _preferences_ui_redraw()
        return {'FINISHED'}


class BlPkgPkgShowClear(Operator):
    bl_idname = "bl_pkg.pkg_show_clear"
    bl_label = "Show Package Clear"

    pkg_id: rna_prop_pkg_id
    repo_index: rna_prop_repo_index

    def execute(self, _context):
        key = (self.pkg_id, self.repo_index)
        blender_extension_show.discard(key)
        _preferences_ui_redraw()
        return {'FINISHED'}


class BlPkgPkgShowSettings(Operator):
    bl_idname = "bl_pkg.pkg_show_settings"
    bl_label = "Show Settings"

    pkg_id: rna_prop_pkg_id
    repo_index: rna_prop_repo_index

    def execute(self, context):
        repo_item = extension_repos_read_index(self.repo_index)
        bpy.ops.preferences.addon_show(module="bl_ext.{:s}.{:s}".format(repo_item.module, self.pkg_id))
        return {'FINISHED'}


# -----------------------------------------------------------------------------
# Testing Operators
#


class BlPkgObsoleteMarked(Operator):
    """Zeroes package versions, useful for development - to test upgrading"""
    bl_idname = "bl_pkg.obsolete_marked"
    bl_label = "Obsolete Marked Packages (Testing)"

    def execute(self, _context):
        from . import (
            repo_cache_store,
        )

        repos_all = extension_repos_read()
        pkg_manifest_local_all = list(repo_cache_store.pkg_manifest_from_local_ensure())
        repo_pkg_map = _pkg_marked_by_repo(pkg_manifest_local_all)
        found = False

        repos_lock = [repos_all[repo_index].directory for repo_index in sorted(repo_pkg_map.keys())]

        with RepoLockContext(repo_directories=repos_lock, cookie=cookie_from_session()) as lock_result:
            if lock_result_any_failed_with_report(self, lock_result):
                return {'CANCELLED'}

            directories_update = set()

            for repo_index, pkg_id_sequence in sorted(repo_pkg_map.items()):
                repo_item = repos_all[repo_index]
                pkg_manifest_local = repo_cache_store.refresh_local_from_directory(repo_item.directory)
                found_for_repo = False
                for pkg_id in pkg_id_sequence:
                    is_installed = pkg_id in pkg_manifest_local
                    if not is_installed:
                        continue

                    bl_extension_utils.pkg_make_obsolete_for_testing(repo_item.directory, pkg_id)
                    found = True
                    found_for_repo = True

                if found_for_repo:
                    directories_update.add(repo_item.directory)

            if not found:
                self.report({'ERROR'}, "No installed packages marked")
                return {'CANCELLED'}

            for directory in directories_update:
                repo_cache_store.refresh_remote_from_directory(directory=directory, force=True)
                repo_cache_store.refresh_local_from_directory(directory=directory)
            _preferences_ui_redraw()

        return {'FINISHED'}


class BlPkgRepoLock(Operator):
    """Lock repositories - to test locking"""
    bl_idname = "bl_pkg.repo_lock"
    bl_label = "Lock Repository (Testing)"

    lock = None

    def execute(self, _context):
        repos_all = extension_repos_read()
        repos_lock = [repo_item.directory for repo_item in repos_all]

        lock_handle = RepoLock(repo_directories=repos_lock, cookie=cookie_from_session())
        lock_result = lock_handle.acquire()
        if lock_result_any_failed_with_report(self, lock_result):
            # At least one lock failed, unlock all and return.
            lock_handle.release()
            return {'CANCELLED'}

        self.report({'INFO'}, "Locked {:d} repos(s)".format(len(lock_result)))
        BlPkgRepoLock.lock = lock_handle
        return {'FINISHED'}


class BlPkgRepoUnlock(Operator):
    """Unlock repositories - to test unlocking"""
    bl_idname = "bl_pkg.repo_unlock"
    bl_label = "Unlock Repository (Testing)"

    def execute(self, _context):
        lock_handle = BlPkgRepoLock.lock
        if lock_handle is None:
            self.report({'ERROR'}, "Lock not held!")
            return {'CANCELLED'}

        lock_result = lock_handle.release()

        BlPkgRepoLock.lock = None

        if lock_result_any_failed_with_report(self, lock_result):
            # This isn't canceled, but there were issues unlocking.
            return {'FINISHED'}

        self.report({'INFO'}, "Unlocked {:d} repos(s)".format(len(lock_result)))
        return {'FINISHED'}


# -----------------------------------------------------------------------------
# Register
#
classes = (
    BlPkgRepoSync,
    BlPkgRepoSyncAll,

    BlPkgPkgInstall,
    BlPkgPkgUninstall,

    BlPkgPkgUpgradeAll,
    BlPkgPkgInstallMarked,
    BlPkgPkgUninstallMarked,

    # UI only operator (to select a package).
    BlPkgStatusClear,
    BlPkgPkgShowSet,
    BlPkgPkgShowClear,
    BlPkgPkgMarkSet,
    BlPkgPkgMarkClear,
    BlPkgPkgShowSettings,

    BlPkgObsoleteMarked,
    BlPkgRepoLock,
    BlPkgRepoUnlock,

    # Dummy commands (for testing).
    BlPkgDummyProgress,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
