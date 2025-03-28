# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
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
# ##### END GPL LICENSE BLOCK #####

bl_info = {
        "name": "Power User Tools",
        "description": "Additional set of user experience tools and operators to assist with every day use for the power user.",
        "author": "Draise (@trinumedia)",
        "version": (0, 2, 3),
        "blender": (4, 4, 0),
        "location": "Varios consistent locations for the power user - customize as you need! ",
        "warning": "This is a Bforartists exclusive addon for the time being", # used for warning icon and text in add-ons panel
        "doc_url": "https://www.bforartists.de/data/manualbfa4/35.4_Addon_-_Power_User_Tools.pdf",
        "tracker_url": "https://github.com/Bforartists/Bforartists",
        "support": "OFFICIAL",
        "category": "Bforartists"
        }


import sys
import os
import importlib

# Get the directory of the current file
module_dir = os.path.dirname(__file__)

# Add the module directory to Python path
if module_dir not in sys.path:
    sys.path.append(module_dir)

# Import submodules
try:
    from . import prefs
    from . import properties
    from . import toolshelf
    from . import ui
    from . import ops
except ImportError as e:
    print(f"Error importing submodules: {e}")
    raise

submodule_names = [
    "prefs",
    "properties",
    "toolshelf",
    "ui",
    "ops",
]

def register():
    try:
        for submodule_name in submodule_names:
            # Dynamically import the submodule
            submodule = importlib.import_module(f".{submodule_name}", package=__name__)
            #print(f"Registering submodule: {submodule_name}")
            if hasattr(submodule, "register"):
                submodule.register()
    except Exception as e:
        print(f"Error during registration: {e}")
        raise

def unregister():
    try:
        for submodule_name in reversed(submodule_names):
            submodule = importlib.import_module(f".{submodule_name}", package=__name__)
            #print(f"Unregistering submodule: {submodule_name}")
            if hasattr(submodule, "unregister"):
                submodule.unregister()
    except Exception as e:
        print(f"Error during unregistration: {e}")
        raise
