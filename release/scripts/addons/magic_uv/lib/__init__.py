# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8-80 compliant>

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.5"
__date__ = "6 Mar 2021"

if "bpy" in locals():
    import importlib
    importlib.reload(bglx)
else:
    from . import bglx

import bpy
