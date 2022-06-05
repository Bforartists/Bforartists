# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

if "bpy" in locals():
    import importlib
    importlib.reload(bglx)
else:
    from . import bglx

import bpy
