#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#======================= END GPL LICENSE BLOCK ========================

import os
import traceback
import importlib

from .utils.rig import RIG_DIR

from . import feature_set_list


def get_rigs(base_dir, base_path, *, path=[], feature_set=feature_set_list.DEFAULT_NAME):
    """ Recursively searches for rig types, and returns a list.

    :param base_path: base dir where rigs are stored
    :type path:str
    :param path:      rig path inside the base dir
    :type path:str
    """

    rigs = {}
    impl_rigs = {}

    dir_path = os.path.join(base_dir, *path)

    try:
        files = os.listdir(dir_path)
    except FileNotFoundError:
        files = []

    files.sort()

    for f in files:
        is_dir = os.path.isdir(os.path.join(dir_path, f))  # Whether the file is a directory

        # Stop cases
        if f[0] in [".", "_"]:
            continue
        if f.count(".") >= 2 or (is_dir and "." in f):
            print("Warning: %r, filename contains a '.', skipping" % os.path.join(*base_path, *path, f))
            continue

        if is_dir:
            # Check for sub-rigs
            sub_rigs, sub_impls = get_rigs(base_dir, base_path, path=[*path, f], feature_set=feature_set)
            rigs.update(sub_rigs)
            impl_rigs.update(sub_impls)
        elif f.endswith(".py"):
            # Check straight-up python files
            subpath = [*path, f[:-3]]
            key = '.'.join(subpath)
            # Don't reload rig modules - it breaks isinstance
            rig_module = importlib.import_module('.'.join(base_path + subpath))
            if hasattr(rig_module, "Rig"):
                rigs[key] = {"module": rig_module,
                             "feature_set": feature_set}
            if hasattr(rig_module, 'IMPLEMENTATION') and rig_module.IMPLEMENTATION:
                impl_rigs[key] = rig_module

    return rigs, impl_rigs


# Public variables
rigs = {}
implementation_rigs = {}

def get_internal_rigs():
    global rigs, implementation_rigs

    BASE_RIGIFY_DIR = os.path.dirname(__file__)
    BASE_RIGIFY_PATH = __name__.split('.')[:-1]

    rigs, implementation_rigs = get_rigs(os.path.join(BASE_RIGIFY_DIR, RIG_DIR), [*BASE_RIGIFY_PATH, RIG_DIR])

def get_external_rigs(set_list):
    # Clear and fill rigify rigs and implementation rigs public variables
    for rig in list(rigs.keys()):
        if rigs[rig]["feature_set"] != feature_set_list.DEFAULT_NAME:
            rigs.pop(rig)
            if rig in implementation_rigs:
                implementation_rigs.pop(rig)

    # Get external rigs
    for feature_set in set_list:
        try:
            base_dir, base_path = feature_set_list.get_dir_path(feature_set, RIG_DIR)

            external_rigs, external_impl_rigs = get_rigs(base_dir, base_path, feature_set=feature_set)
        except Exception:
            print("Rigify Error: Could not load feature set '%s' rigs: exception occurred.\n" % (feature_set))
            traceback.print_exc()
            print("")
            continue

        rigs.update(external_rigs)
        implementation_rigs.update(external_impl_rigs)
