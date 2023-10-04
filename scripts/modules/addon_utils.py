# SPDX-FileCopyrightText: 2011-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

__all__ = (
    "paths",
    "modules",
    "check",
    "enable",
    "disable",
    "disable_all",
    "reset_all",
    "module_bl_info",
)

import bpy as _bpy
_preferences = _bpy.context.preferences

error_encoding = False
# (name, file, path)
error_duplicates = []
addons_fake_modules = {}


# called only once at startup, avoids calling 'reset_all', correct but slower.
def _initialize_once():
    for path in paths():
        _bpy.utils._sys_path_ensure_append(path)

    _initialize_extensions_repos_once()

    for addon in _preferences.addons:
        enable(addon.module)


def paths():
    return [
        path for subdir in (
            # RELEASE SCRIPTS: official scripts distributed in Blender releases.
            "addons",
            # CONTRIB SCRIPTS: good for testing but not official scripts yet
            # if folder addons_contrib/ exists, scripts in there will be loaded too.
            "addons_contrib",
        )
        for path in _bpy.utils.script_paths(subdir=subdir)
    ]


# A version of `paths` that includes extension repositories returning a list `(path, package)` pairs.
#
# Notes on the ``package`` value.
#
# - For top-level modules (the "addons" directories, the value is an empty string)
#   because those add-ons can be imported directly.
# - For extension repositories the value is a module string (which can be imported for example)
#   where any modules within the `path` can be imported as a sub-module.
#   So for example, given a list value of: `("/tmp/repo", "bl_ext.temp_repo")`.
#
#   An add-on located at `/tmp/repo/my_handy_addon.py` will have a unique module path of:
#   `bl_ext.temp_repo.my_handy_addon`, which can be imported and will be the value of it's `Addon.module`.
def _paths_with_extension_repos():

    import os
    addon_paths = [(path, "") for path in paths()]

    if _preferences.experimental.use_extension_repos:
        for repo in _preferences.filepaths.extension_repos:
            dirpath = repo.directory
            if not os.path.isdir(dirpath):
                continue
            addon_paths.append((dirpath, "%s.%s" % (_ext_base_pkg_idname, repo.module)))

    return addon_paths


def _fake_module(mod_name, mod_path, speedy=True, force_support=None):
    global error_encoding
    import os

    if _bpy.app.debug_python:
        print("fake_module", mod_path, mod_name)
    import ast
    ModuleType = type(ast)
    try:
        file_mod = open(mod_path, "r", encoding='UTF-8')
    except OSError as ex:
        print("Error opening file:", mod_path, ex)
        return None

    with file_mod:
        if speedy:
            lines = []
            line_iter = iter(file_mod)
            l = ""
            while not l.startswith("bl_info"):
                try:
                    l = line_iter.readline()
                except UnicodeDecodeError as ex:
                    if not error_encoding:
                        error_encoding = True
                        print("Error reading file as UTF-8:", mod_path, ex)
                    return None

                if len(l) == 0:
                    break
            while l.rstrip():
                lines.append(l)
                try:
                    l = line_iter.readline()
                except UnicodeDecodeError as ex:
                    if not error_encoding:
                        error_encoding = True
                        print("Error reading file as UTF-8:", mod_path, ex)
                    return None

            data = "".join(lines)

        else:
            data = file_mod.read()
    del file_mod

    try:
        ast_data = ast.parse(data, filename=mod_path)
    except BaseException:
        print("Syntax error 'ast.parse' can't read:", repr(mod_path))
        import traceback
        traceback.print_exc()
        ast_data = None

    body_info = None

    if ast_data:
        for body in ast_data.body:
            if body.__class__ == ast.Assign:
                if len(body.targets) == 1:
                    if getattr(body.targets[0], "id", "") == "bl_info":
                        body_info = body
                        break

    if body_info:
        try:
            mod = ModuleType(mod_name)
            mod.bl_info = ast.literal_eval(body.value)
            mod.__file__ = mod_path
            mod.__time__ = os.path.getmtime(mod_path)
        except:
            print("AST error parsing bl_info for:", repr(mod_path))
            import traceback
            traceback.print_exc()
            return None

        if force_support is not None:
            mod.bl_info["support"] = force_support

        return mod
    else:
        print(
            "fake_module: addon missing 'bl_info' "
            "gives bad performance!:",
            repr(mod_path),
        )
        return None


def modules_refresh(*, module_cache=addons_fake_modules):
    global error_encoding
    import os

    error_encoding = False
    error_duplicates.clear()

    modules_stale = set(module_cache.keys())

    for path, pkg_id in _paths_with_extension_repos():

        # Force all user contributed add-ons to be 'TESTING'.
        force_support = 'TESTING' if ((not pkg_id) and path.endswith("addons_contrib")) else None

        for mod_name, mod_path in _bpy.path.module_names(path, package=pkg_id):
            modules_stale.discard(mod_name)
            mod = module_cache.get(mod_name)
            if mod:
                if mod.__file__ != mod_path:
                    print(
                        "multiple addons with the same name:\n"
                        "  %r\n"
                        "  %r" % (mod.__file__, mod_path)
                    )
                    error_duplicates.append((mod.bl_info["name"], mod.__file__, mod_path))

                elif mod.__time__ != os.path.getmtime(mod_path):
                    print(
                        "reloading addon:",
                        mod_name,
                        mod.__time__,
                        os.path.getmtime(mod_path),
                        repr(mod_path),
                    )
                    del module_cache[mod_name]
                    mod = None

            if mod is None:
                mod = _fake_module(
                    mod_name,
                    mod_path,
                    force_support=force_support,
                )
                if mod:
                    module_cache[mod_name] = mod

    # just in case we get stale modules, not likely
    for mod_stale in modules_stale:
        del module_cache[mod_stale]
    del modules_stale


def modules(*, module_cache=addons_fake_modules, refresh=True):
    if refresh or ((module_cache is addons_fake_modules) and modules._is_first):
        modules_refresh(module_cache=module_cache)
        modules._is_first = False

    mod_list = list(module_cache.values())
    mod_list.sort(
        key=lambda mod: (
            mod.bl_info.get("category", ""),
            mod.bl_info.get("name", ""),
        )
    )
    return mod_list


modules._is_first = True


def check(module_name):
    """
    Returns the loaded state of the addon.

    :arg module_name: The name of the addon and module.
    :type module_name: string
    :return: (loaded_default, loaded_state)
    :rtype: tuple of booleans
    """
    import sys
    loaded_default = module_name in _preferences.addons

    mod = sys.modules.get(module_name)
    loaded_state = (
        (mod is not None) and
        getattr(mod, "__addon_enabled__", Ellipsis)
    )

    if loaded_state is Ellipsis:
        print(
            "Warning: addon-module", module_name, "found module "
            "but without '__addon_enabled__' field, "
            "possible name collision from file:",
            repr(getattr(mod, "__file__", "<unknown>")),
        )

        loaded_state = False

    if mod and getattr(mod, "__addon_persistent__", False):
        loaded_default = True

    return loaded_default, loaded_state

# utility functions


def _addon_ensure(module_name):
    addons = _preferences.addons
    addon = addons.get(module_name)
    if not addon:
        addon = addons.new()
        addon.module = module_name


def _addon_remove(module_name):
    addons = _preferences.addons

    while module_name in addons:
        addon = addons.get(module_name)
        if addon:
            addons.remove(addon)


def enable(module_name, *, default_set=False, persistent=False, handle_error=None):
    """
    Enables an addon by name.

    :arg module_name: the name of the addon and module.
    :type module_name: string
    :arg default_set: Set the user-preference.
    :type default_set: bool
    :arg persistent: Ensure the addon is enabled for the entire session (after loading new files).
    :type persistent: bool
    :arg handle_error: Called in the case of an error, taking an exception argument.
    :type handle_error: function
    :return: the loaded module or None on failure.
    :rtype: module
    """

    import os
    import sys
    import importlib
    from bpy_restrict_state import RestrictBlend

    if handle_error is None:
        def handle_error(_ex):
            import traceback
            traceback.print_exc()

    # reload if the mtime changes
    mod = sys.modules.get(module_name)
    # chances of the file _not_ existing are low, but it could be removed
    if mod and os.path.exists(mod.__file__):

        if getattr(mod, "__addon_enabled__", False):
            # This is an unlikely situation,
            # re-register if the module is enabled.
            # Note: the UI doesn't allow this to happen,
            # in most cases the caller should 'check()' first.
            try:
                mod.unregister()
            except BaseException as ex:
                print(
                    "Exception in module unregister():",
                    repr(getattr(mod, "__file__", module_name)),
                )
                handle_error(ex)
                return None

        mod.__addon_enabled__ = False
        mtime_orig = getattr(mod, "__time__", 0)
        mtime_new = os.path.getmtime(mod.__file__)
        if mtime_orig != mtime_new:
            print("module changed on disk:", repr(mod.__file__), "reloading...")

            try:
                importlib.reload(mod)
            except BaseException as ex:
                handle_error(ex)
                del sys.modules[module_name]
                return None
            mod.__addon_enabled__ = False

    # add the addon first it may want to initialize its own preferences.
    # must remove on fail through.
    if default_set:
        _addon_ensure(module_name)

    # Split registering up into 3 steps so we can undo
    # if it fails par way through.

    # Disable the context: using the context at all
    # while loading an addon is really bad, don't do it!
    with RestrictBlend():

        # 1) try import
        try:
            # Use instead of `__import__` so that sub-modules can eventually be supported.
            # This is also documented to be the preferred way to import modules.
            mod = importlib.import_module(module_name)
            if mod.__file__ is None:
                # This can happen when the addon has been removed but there are
                # residual `.pyc` files left behind.
                raise ImportError(name=module_name)
            mod.__time__ = os.path.getmtime(mod.__file__)
            mod.__addon_enabled__ = False
        except BaseException as ex:
            # If the add-on doesn't exist, don't print full trace-back because the back-trace is in this case
            # is verbose without any useful details. A missing path is better communicated in a short message.
            # Account for `ImportError` & `ModuleNotFoundError`.
            if isinstance(ex, ImportError) and ex.name == module_name:
                print("Add-on not loaded:", repr(module_name), "cause:", str(ex))
            else:
                handle_error(ex)

            if default_set:
                _addon_remove(module_name)
            return None

        # 1.1) Fail when add-on is too old.
        # This is a temporary 2.8x migration check, so we can manage addons that are supported.

        if mod.bl_info.get("blender", (0, 0, 0)) < (2, 80, 0):
            if _bpy.app.debug:
                print("Warning: Add-on '%s' was not upgraded for 2.80, ignoring" % module_name)
            return None

        # 2) Try register collected modules.
        # Removed register_module, addons need to handle their own registration now.

        from _bpy import _bl_owner_id_get, _bl_owner_id_set
        owner_id_prev = _bl_owner_id_get()
        _bl_owner_id_set(module_name)

        # 3) Try run the modules register function.
        try:
            mod.register()
        except BaseException as ex:
            print(
                "Exception in module register():",
                getattr(mod, "__file__", module_name),
            )
            handle_error(ex)
            del sys.modules[module_name]
            if default_set:
                _addon_remove(module_name)
            return None
        finally:
            _bl_owner_id_set(owner_id_prev)

    # * OK loaded successfully! *
    mod.__addon_enabled__ = True
    mod.__addon_persistent__ = persistent

    if _bpy.app.debug_python:
        print("\taddon_utils.enable", mod.__name__)

    return mod


def disable(module_name, *, default_set=False, handle_error=None):
    """
    Disables an addon by name.

    :arg module_name: The name of the addon and module.
    :type module_name: string
    :arg default_set: Set the user-preference.
    :type default_set: bool
    :arg handle_error: Called in the case of an error, taking an exception argument.
    :type handle_error: function
    """
    import sys

    if handle_error is None:
        def handle_error(_ex):
            import traceback
            traceback.print_exc()

    mod = sys.modules.get(module_name)

    # Possible this add-on is from a previous session and didn't load a
    # module this time. So even if the module is not found, still disable
    # the add-on in the user preferences.
    if mod and getattr(mod, "__addon_enabled__", False) is not False:
        mod.__addon_enabled__ = False
        mod.__addon_persistent = False

        try:
            mod.unregister()
        except BaseException as ex:
            mod_path = getattr(mod, "__file__", module_name)
            print("Exception in module unregister():", repr(mod_path))
            del mod_path
            handle_error(ex)
    else:
        print(
            "addon_utils.disable: %s not %s" % (
                module_name,
                "disabled" if mod is None else "loaded")
        )

    # could be in more than once, unlikely but better do this just in case.
    if default_set:
        _addon_remove(module_name)

    if _bpy.app.debug_python:
        print("\taddon_utils.disable", module_name)


def reset_all(*, reload_scripts=False):
    """
    Sets the addon state based on the user preferences.
    """
    import sys

    # initializes addons_fake_modules
    modules_refresh()

    for path, pkg_id in _paths_with_extension_repos():
        if not pkg_id:
            _bpy.utils._sys_path_ensure_append(path)

        for mod_name, _mod_path in _bpy.path.module_names(path, package=pkg_id):
            is_enabled, is_loaded = check(mod_name)

            # first check if reload is needed before changing state.
            if reload_scripts:
                import importlib
                mod = sys.modules.get(mod_name)
                if mod:
                    importlib.reload(mod)

            if is_enabled == is_loaded:
                pass
            elif is_enabled:
                enable(mod_name)
            elif is_loaded:
                print("\taddon_utils.reset_all unloading", mod_name)
                disable(mod_name)


def disable_all():
    import sys
    # Collect modules to disable first because dict can be modified as we disable.

    # NOTE: don't use `getattr(item[1], "__addon_enabled__", False)` because this runs on all modules,
    # including 3rd party modules unrelated to Blender.
    #
    # Some modules may have their own `__getattr__` and either:
    # - Not raise an `AttributeError` (is they should),
    #   causing `hasattr` & `getattr` to raise an exception instead of treating the attribute as missing.
    # - Generate modules dynamically, modifying `sys.modules` which is being iterated over,
    #   causing a RuntimeError: "dictionary changed size during iteration".
    #
    # Either way, running 3rd party logic here can cause undefined behavior.
    # Use direct `__dict__` access to bypass `__getattr__`, see: #111649.
    addon_modules = [
        item for item in sys.modules.items()
        if type(mod_dict := getattr(item[1], "__dict__", None)) is dict
        if mod_dict.get("__addon_enabled__")
    ]
    # Check the enabled state again since it's possible the disable call
    # of one add-on disables others.
    for mod_name, mod in addon_modules:
        if getattr(mod, "__addon_enabled__", False):
            disable(mod_name)


def _blender_manual_url_prefix():
    return "https://docs.blender.org/manual/%s/%d.%d" % (_bpy.utils.manual_language_code(), *_bpy.app.version[:2])


def module_bl_info(mod, *, info_basis=None):
    if info_basis is None:
        info_basis = {
            "name": "",
            "author": "",
            "version": (),
            "blender": (),
            "location": "",
            "description": "",
            "doc_url": "",
            "support": 'COMMUNITY',
            "category": "",
            "warning": "",
            "show_expanded": False,
        }

    addon_info = getattr(mod, "bl_info", {})

    # avoid re-initializing
    if "_init" in addon_info:
        return addon_info

    if not addon_info:
        mod.bl_info = addon_info

    for key, value in info_basis.items():
        addon_info.setdefault(key, value)

    if not addon_info["name"]:
        addon_info["name"] = mod.__name__

    doc_url = addon_info["doc_url"]
    if doc_url:
        doc_url_prefix = "{BLENDER_MANUAL_URL}"
        if doc_url_prefix in doc_url:
            addon_info["doc_url"] = doc_url.replace(
                doc_url_prefix,
                _blender_manual_url_prefix(),
            )

    addon_info["_init"] = None
    return addon_info


# -----------------------------------------------------------------------------
# Extensions

# Module-like class, store singletons.
class _ext_global:
    __slots__ = ()

    # Store a map of `preferences.filepaths.extension_repos` -> `module_id`.
    # Only needed to detect renaming between `bpy.app.handlers.extension_repos_update_{pre & post}` events.
    idmap = {}

    # The base package created by `JunctionModuleHandle`.
    module_handle = None


# The name (in `sys.modules`) keep this short because it's stored as part of add-on modules name.
_ext_base_pkg_idname = "bl_ext"


def _extension_preferences_idmap():
    repos_idmap = {}
    if _preferences.experimental.use_extension_repos:
        for repo in _preferences.filepaths.extension_repos:
            repos_idmap[repo.as_pointer()] = repo.module
    return repos_idmap


def _extension_dirpath_from_preferences():
    repos_dict = {}
    if _preferences.experimental.use_extension_repos:
        for repo in _preferences.filepaths.extension_repos:
            repos_dict[repo.module] = repo.directory
    return repos_dict


def _extension_dirpath_from_handle():
    repos_info = {}
    for module_id, module in _ext_global.module_handle.submodule_items():
        # Account for it being unset although this should never happen unless script authors
        # meddle with the modules.
        try:
            dirpath = module.__path__[0]
        except BaseException:
            dirpath = ""
        repos_info[module_id] = dirpath
    return repos_info

# Use `bpy.app.handlers.extension_repos_update_{pre/post}` to track changes to extension repositories
# and sync the changes to the Python module.


@_bpy.app.handlers.persistent
def _initialize_extension_repos_pre(*_):
    _ext_global.idmap = _extension_preferences_idmap()


@_bpy.app.handlers.persistent
def _initialize_extension_repos_post(*_):
    # Map `module_id` -> `dirpath`.
    repos_info_prev = _extension_dirpath_from_handle()
    repos_info_next = _extension_dirpath_from_preferences()

    # Map `repo.as_pointer()` -> `module_id`.
    repos_idmap_prev = _ext_global.idmap
    repos_idmap_next = _extension_preferences_idmap()

    # Map `module_id` -> `repo.as_pointer()`.
    repos_idmap_next_reverse = {value: key for key, value in repos_idmap_next.items()}

    # Mainly needed when the `preferences.experimental.use_extension_repos` option is enabled at run-time.
    #
    # Filter `repos_idmap_prev` so only items which were also in the `repos_info_prev` are included.
    # This is an awkward situation, they should be in sync, however when enabling the experimental option
    # means the preferences wont have changed, but the module will not be in sync with the preferences.
    # Support this by removing items in `repos_idmap_prev` which aren't also initialized in the managed package.
    #
    # The only situation this would be useful to keep is if we want to support renaming a package
    # that manipulates all add-ons using it, when those add-ons are in the preferences but have not had
    # their package loaded. It's possible we want to do this but is also reasonably obscure.
    for repo_id_prev, module_id_prev in list(repos_idmap_prev.items()):
        if module_id_prev not in repos_info_prev:
            del repos_idmap_prev[repo_id_prev]

    # NOTE(@ideasman42): supporting renaming at all is something we might limit to extensions
    # which have no add-ons loaded as supporting renaming add-ons in-place seems error prone as the add-on
    # may define internal variables based on the full package path.

    submodules_add = []  # List of module names to add: `(module_id, dirpath)`.
    submodules_del = []  # List of module names to remove: `module_id`.
    submodules_rename_module = []  # List of module names: `(module_id_src, module_id_dst)`.
    submodules_rename_dirpath = []  # List of module names: `(module_id, dirpath)`.

    renamed_prev = set()
    renamed_next = set()

    # Detect rename modules & module directories.
    for module_id_next, dirpath_next in repos_info_next.items():
        # Lookup never fails, as the "next" values use: `preferences.filepaths.extension_repos`.
        repo_id = repos_idmap_next_reverse[module_id_next]
        # Lookup may fail if this is a newly added module.
        # Don't attempt to setup `submodules_add` though as it's possible
        # the module name persists while the underlying `repo_id` changes.
        module_id_prev = repos_idmap_prev.get(repo_id)
        if module_id_prev is None:
            continue

        # Detect rename.
        if module_id_next != module_id_prev:
            submodules_rename_module.append((module_id_prev, module_id_next))
            renamed_prev.add(module_id_prev)
            renamed_next.add(module_id_next)

        # Detect `dirpath` change.
        if dirpath_next != repos_info_prev[module_id_prev]:
            submodules_rename_dirpath.append((module_id_next, dirpath_next))

    # Detect added modules.
    for module_id, dirpath in repos_info_next.items():
        if (module_id not in repos_info_prev) and (module_id not in renamed_next):
            submodules_add.append((module_id, dirpath))
    # Detect deleted modules.
    for module_id, _dirpath in repos_info_prev.items():
        if (module_id not in repos_info_next) and (module_id not in renamed_prev):
            submodules_del.append(module_id)

    # Apply changes to the `_ext_base_pkg_idname` named module so it matches extension data from the preferences.
    module_handle = _ext_global.module_handle
    for module_id in submodules_del:
        module_handle.unregister_submodule(module_id)
    for module_id, dirpath in submodules_add:
        module_handle.register_submodule(module_id, dirpath)
    for module_id_prev, module_id_next in submodules_rename_module:
        module_handle.rename_submodule(module_id_prev, module_id_next)
    for module_id, dirpath in submodules_rename_dirpath:
        module_handle.rename_directory(module_id, dirpath)

    _ext_global.idmap.clear()

    # Force refreshing if directory paths change.
    if submodules_del or submodules_add or submodules_rename_dirpath:
        modules._is_first = True


def _initialize_extensions_repos_once():
    from bpy_extras.extensions.junction_module import JunctionModuleHandle
    module_handle = JunctionModuleHandle(_ext_base_pkg_idname)
    module_handle.register_module()
    _ext_global.module_handle = module_handle

    # Setup repositories for the first time.
    # Intentionally don't call `_initialize_extension_repos_pre` as this is the first time,
    # the previous state is not useful to read.
    _initialize_extension_repos_post()

    # Internal handlers intended for Blender's own handling of repositories.
    _bpy.app.handlers._extension_repos_update_pre.append(_initialize_extension_repos_pre)
    _bpy.app.handlers._extension_repos_update_post.append(_initialize_extension_repos_post)
