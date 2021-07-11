# ====================== BEGIN GPL LICENSE BLOCK ======================
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
# ======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>

import importlib


# Submodules to load during register
submodules = (
    'copy_mirror_parameters',
)

loaded_submodules = []


def register():
    # Lazily load modules to make reloading easier. Loading this way
    # hides the sub-modules and their dependencies from initial_load_order.
    loaded_submodules[:] = [
        importlib.import_module(__name__ + '.' + name) for name in submodules
    ]

    for mod in loaded_submodules:
        mod.register()


def unregister():
    for mod in reversed(loaded_submodules):
        mod.unregister()

    loaded_submodules.clear()
