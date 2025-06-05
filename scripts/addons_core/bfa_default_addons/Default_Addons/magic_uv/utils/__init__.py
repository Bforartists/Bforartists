# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

if "bpy" in locals():
    import importlib
    importlib.reload(bl_class_registry)
    importlib.reload(compatibility)
    importlib.reload(graph)
    importlib.reload(property_class_registry)
else:
    from . import bl_class_registry
    from . import compatibility
    from . import graph
    from . import property_class_registry

import bpy
