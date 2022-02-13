# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8-80 compliant>

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.5"
__date__ = "6 Mar 2021"

if "bpy" in locals():
    import importlib
    importlib.reload(bl_class_registry)
    importlib.reload(compatibility)
    importlib.reload(property_class_registry)
else:
    from . import bl_class_registry
    from . import compatibility
    from . import property_class_registry

import bpy
