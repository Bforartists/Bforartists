# SPDX-FileCopyrightText: 2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Startup notifications.
"""

__all__ = (
    "register",
    "unregister",
)


import bpy

from . import bl_extension_ops
from . import bl_extension_utils

# Request the processes exit, then wait for them to exit.
# NOTE(@ideasman42): This is all well and good but any delays exiting are unwanted,
# only keep this as a reference and in case we can speed up forcing them to exit.
USE_GRACEFUL_EXIT = False


# -----------------------------------------------------------------------------
# Internal Utilities

def sync_status_count_outdated_extensions(repos_notify):
    from . import repo_cache_store

    repos_notify_directories = [repo_item.directory for repo_item in repos_notify]

    package_count = 0

    for (
            pkg_manifest_remote,
            pkg_manifest_local,
    ) in zip(
        repo_cache_store.pkg_manifest_from_remote_ensure(
            error_fn=print,
            directory_subset=repos_notify_directories,
        ),
        repo_cache_store.pkg_manifest_from_local_ensure(
            error_fn=print,
            directory_subset=repos_notify_directories,
            # Needed as these have been updated.
            check_files=True,
        ),
    ):
        if pkg_manifest_remote is None:
            continue
        if pkg_manifest_local is None:
            continue

        for pkg_id, item_remote in pkg_manifest_remote.items():
            item_local = pkg_manifest_local.get(pkg_id)
            if item_local is None:
                # Not installed.
                continue

            if item_remote["version"] != item_local["version"]:
                package_count += 1
    return package_count


# -----------------------------------------------------------------------------
# Update Iterator
#
# This is a black-box which handled running the updates, yielding status text.


def sync_status_generator(repos_notify):

    # Generator results...
    # -> None: do nothing.
    # -> (text, ICON_ID, NUMBER_OF_UPDATES)

    # ################ #
    # Setup The Update #
    # ################ #

    yield None

    from functools import partial

    cmd_batch_partial = []
    for repo_item in repos_notify:
        # Local only repositories should still refresh, but not run the sync.
        assert repo_item.remote_url
        cmd_batch_partial.append(partial(
            bl_extension_utils.repo_sync,
            directory=repo_item.directory,
            repo_url=repo_item.remote_url,
            online_user_agent=bl_extension_ops.online_user_agent_from_blender(),
            # Never sleep while there is no input, as this blocks Blender.
            use_idle=False,
            # Needed so the user can exit blender without warnings about a broken pipe.
            # TODO: write to a temporary location, once done:
            # There is no chance of corrupt data as the data isn't written directly to the target JSON.
            force_exit_ok=not USE_GRACEFUL_EXIT,
        ))

    yield None

    # repos_lock = [repo_item.directory for repo_item in self.repos_notify]

    # Lock repositories.
    # self.repo_lock = bl_extension_utils.RepoLock(repo_directories=repos_lock, cookie=cookie_from_session())

    import atexit

    cmd_batch = None

    def cmd_force_quit():
        if cmd_batch is None:
            return
        cmd_batch.exec_non_blocking(request_exit=True)

        if USE_GRACEFUL_EXIT:
            import time
            # Force all commands to close.
            while not cmd_batch.exec_non_blocking(request_exit=True).all_complete:
                # Avoid high CPU usage on exit.
                time.sleep(0.01)

    atexit.register(cmd_force_quit)

    cmd_batch = bl_extension_utils.CommandBatch(
        # Used as a prefix in status.
        title="Update",
        batch=cmd_batch_partial,
    )
    del cmd_batch_partial

    yield None

    # ############## #
    # Run The Update #
    # ############## #

    # The count is unknown.
    update_total = -1

    while True:
        command_result = cmd_batch.exec_non_blocking(
            # TODO: if Blender requested an exit... this should request exit here.
            request_exit=False,
        )
        # Forward new messages to reports.
        msg_list_per_command = cmd_batch.calc_status_log_since_last_request_or_none()
        if bpy.app.debug:
            if msg_list_per_command is not None:
                for i, msg_list in enumerate(msg_list_per_command, 1):
                    for (ty, msg) in msg_list:
                        # TODO: output this information to a place for users, if they want to debug.
                        if len(msg_list_per_command) > 1:
                            # These reports are flattened, note the process number that fails so
                            # whoever is reading the reports can make sense of the messages.
                            msg = "{:s} (process {:d} of {:d})".format(msg, i, len(msg_list_per_command))
                        if ty == 'STATUS':
                            print('INFO', msg)
                        else:
                            print(ty, msg)

        # TODO: more elegant way to detect changes.
        # Re-calculating the same information each time then checking if it's different isn't great.
        if command_result.status_data_changed:
            if command_result.all_complete:
                update_total = sync_status_count_outdated_extensions(repos_notify)
            yield (cmd_batch.calc_status_data(), update_total)
        else:
            yield None

        if command_result.all_complete:
            break

    atexit.unregister(cmd_force_quit)

    # ################### #
    # Finalize The Update #
    # ################### #

    yield None

    # Unlock repositories.
    # lock_result_any_failed_with_report(self, self.repo_lock.release(), report_type='WARNING')
    # self.repo_lock = None


# -----------------------------------------------------------------------------
# Private API

# The timer before running the timer (initially).
TIME_WAIT_INIT = 0.05
# The time between calling the timer.
TIME_WAIT_STEP = 0.1

state_text = (
    "Checking for updates...",
)


class NotifyHandle:
    __slots__ = (
        "splash_region",
        "state",

        "sync_generator",
        "sync_info",
    )

    def __init__(self, repos_notify):
        self.splash_region = None
        self.state = 0
        # We could start the generator separately, this seems OK here for now.
        self.sync_generator = iter(sync_status_generator(repos_notify))
        # TEXT/ICON_ID/COUNT
        self.sync_info = None


# When non-null, the timer is running.
_notify = None


def _region_exists(region):
    # TODO: this is a workaround for there being no good way to inspect temporary regions.
    # A better solution could be to store the `PyObject` in the `ARegion` so that it gets invalidated when freed.
    # This is a bigger change though - so use the context override as a way to check if a region is valid.
    exists = False
    try:
        with bpy.context.temp_override(region=region):
            exists = True
    except TypeError:
        pass
    return exists


def _ui_refresh_timer():
    if _notify is None:
        return None

    default_wait = TIME_WAIT_STEP

    sync_info = next(_notify.sync_generator, ...)
    # If the generator exited, early exit here.
    if sync_info is ...:
        return None
    if sync_info is None:
        # Nothing changed, no action is needed (waiting for a response).
        return default_wait

    # Re-display.
    assert isinstance(sync_info, tuple)
    assert len(sync_info) == 2

    _notify.sync_info = sync_info

    # Check if the splash_region is valid.
    if _notify.splash_region is not None:
        if not _region_exists(_notify.splash_region):
            _notify.splash_region = None
            return None
        _notify.splash_region.tag_redraw()
        _notify.splash_region.tag_refresh_ui()

    # TODO: redraw the status bar.

    return default_wait


def splash_draw_status_fn(self, context):
    if _notify.splash_region is None:
        _notify.splash_region = context.region_popup

    if _notify.sync_info is None:
        self.layout.label(text="Updates starting...")
    else:
        status_data, update_count = _notify.sync_info
        text, icon = bl_extension_utils.CommandBatch.calc_status_text_icon_from_data(status_data, update_count)
        row = self.layout.row(align=True)
        if update_count > 0:
            row.operator("bl_pkg.extensions_show_for_update", text="", icon=icon)
        else:
            row.label(text="", icon=icon)
        row.label(text=text)

    self.layout.separator()
    self.layout.separator()


# -----------------------------------------------------------------------------
# Public API


def register(repos_notify):
    global _notify
    _notify = NotifyHandle(repos_notify)
    bpy.types.WM_MT_splash.append(splash_draw_status_fn)
    bpy.app.timers.register(_ui_refresh_timer, first_interval=TIME_WAIT_INIT)


def unregister():
    global _notify
    assert _notify is not None
    _notify = None

    bpy.types.WM_MT_splash.remove(splash_draw_status_fn)
    # This timer is responsible for un-registering itself.
    # `bpy.app.timers.unregister(_ui_refresh_timer)`
