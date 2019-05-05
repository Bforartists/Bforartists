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

from . import utils


def get_rigs(base_path, path, feature_set='rigify'):
    """ Recursively searches for rig types, and returns a list.

    :param base_path: base dir where rigs are stored
    :type path:str
    :param path:      rig path inside the base dir
    :type path:str
    """

    rigs = {}
    impl_rigs = {}

    try:
        files = os.listdir(os.path.join(base_path, path))
    except FileNotFoundError:
        files = []

    files.sort()

    for f in files:
        is_dir = os.path.isdir(os.path.join(base_path, path, f))  # Whether the file is a directory

        # Stop cases
        if f[0] in [".", "_"]:
            continue
        if f.count(".") >= 2 or (is_dir and "." in f):
            print("Warning: %r, filename contains a '.', skipping" % os.path.join(path, f))
            continue

        if is_dir:
            # Check directories
            module_name = os.path.join(path, "__init__").replace(os.sep, ".")
            # Check for sub-rigs
            sub_rigs, sub_impls = get_rigs(base_path, os.path.join(path, f, ""), feature_set)  # "" adds a final slash
            rigs.update({"%s.%s" % (f, l): sub_rigs[l] for l in sub_rigs})
            impl_rigs.update({"%s.%s" % (f, l): sub_rigs[l] for l in sub_impls})
        elif f.endswith(".py"):
            # Check straight-up python files
            f = f[:-3]
            module_name = os.path.join(path, f).replace(os.sep, ".")
            rig_module = utils.get_resource(module_name, base_path=base_path)
            if hasattr(rig_module, "Rig"):
                rigs[f] = {"module": rig_module,
                           "feature_set": feature_set}
            if hasattr(rig_module, 'IMPLEMENTATION') and rig_module.IMPLEMENTATION:
                impl_rigs[f] = rig_module

    return rigs, impl_rigs


# Public variables
MODULE_DIR = os.path.dirname(os.path.dirname(__file__))

rigs, implementation_rigs = get_rigs(MODULE_DIR, os.path.join(os.path.basename(os.path.dirname(__file__)), utils.RIG_DIR, ''))


def get_external_rigs(feature_sets_path):
    # Clear and fill rigify rigs and implementation rigs public variables
    for rig in list(rigs.keys()):
        if rigs[rig]["feature_set"] != "rigify":
            rigs.pop(rig)
            if rig in implementation_rigs:
                implementation_rigs.pop(rig)

    # Get external rigs
    for feature_set in os.listdir(feature_sets_path):
        if feature_set:
            try:
                try:
                    utils.get_resource(os.path.join(feature_set, '__init__'), feature_sets_path)
                except FileNotFoundError:
                    print("Rigify Error: Could not load feature set '%s': __init__.py not found.\n" % (feature_set))
                    continue

                external_rigs, external_impl_rigs = get_rigs(feature_sets_path, os.path.join(feature_set, utils.RIG_DIR), feature_set)
            except Exception:
                print("Rigify Error: Could not load feature set '%s' rigs: exception occurred.\n" % (feature_set))
                traceback.print_exc()
                print("")
                continue

            rigs.update(external_rigs)
            implementation_rigs.update(external_impl_rigs)
