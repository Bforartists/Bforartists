# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

if "bpy" in locals():
    import importlib
    importlib.reload(view3d_copy_paste_uv_editmode)
    importlib.reload(view3d_copy_paste_uv_objectmode)
    importlib.reload(view3d_uv_manipulation)
    importlib.reload(view3d_uv_mapping)
    importlib.reload(uvedit_copy_paste_uv)
    importlib.reload(uvedit_uv_manipulation)
    importlib.reload(uvedit_editor_enhancement)
    importlib.reload(VIEW3D_MT_object)
    importlib.reload(VIEW3D_MT_uv_map)
    importlib.reload(IMAGE_MT_uvs)
else:
    from . import view3d_copy_paste_uv_editmode
    from . import view3d_copy_paste_uv_objectmode
    from . import view3d_uv_manipulation
    from . import view3d_uv_mapping
    from . import uvedit_copy_paste_uv
    from . import uvedit_uv_manipulation
    from . import uvedit_editor_enhancement
    from . import VIEW3D_MT_object
    from . import VIEW3D_MT_uv_map
    from . import IMAGE_MT_uvs

import bpy
