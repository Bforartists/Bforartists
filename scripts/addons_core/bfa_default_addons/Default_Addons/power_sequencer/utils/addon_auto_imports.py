# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import pkgutil
import importlib

reload_event = False


def setup_addon_modules(path, package_name, ignore_packages=[], ignore_modules=[]):
    """
    Imports and reloads all modules in this addon.

    path -- __path__ from __init__.py
    package_name -- __name__ from __init__.py
    ignore_packages -- list of packages to ignore,
    skips the package if the string is in the name
    ignore_modules -- list of module_names to ignore, strings
    skips the module if the string is in the name
    """

    def get_submodule_names(path=path[0], root=""):
        module_names = []
        for ignore in ignore_packages:
            if ignore in root:
                return []
        for importer, module_name, is_package in pkgutil.iter_modules([path]):
            skip_module = False
            for ignore in ignore_modules:
                if ignore in module_name:
                    skip_module = True
            if skip_module:
                continue
            if is_package:
                sub_path = path + "\\" + module_name
                sub_root = root + module_name + "."
                module_names.extend(get_submodule_names(sub_path, sub_root))
            else:
                module_names.append(root + module_name)
        return module_names

    def import_submodules(names):
        modules = []
        for name in names:
            modules.append(importlib.import_module("." + name, package_name))
        return modules

    def reload_modules(modules):
        for module in modules:
            importlib.reload(module)

    names = get_submodule_names()
    modules = import_submodules(names)
    if reload_event:
        reload_modules(modules)
    return modules


reload_event = True
