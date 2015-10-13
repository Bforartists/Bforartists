# ##### BEGIN GPL LICENSE BLOCK #####
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
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------


# ##### BEGIN COPYRIGHT BLOCK #####
#
# initial script copyright (c)2013, 2014 Alexander Nussbaumer
#
# ##### END COPYRIGHT BLOCK #####


bl_info = {
    'name': "Future Pinball FPx format (.fpm/.fpl/.fpt)",
    'description': "Import Future Pinball Model, Library and Table files",
    'author': "Alexander Nussbaumer",
    'version': (0, 0, 201401111),
    'blender': (2, 68, 0),
    'location': "File > Import",
    'warning': "",
    'wiki_url': "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Import-Export/FuturePinball_FPx",
    'tracker_url': "https://developer.blender.org/T36215",
    'category': "Import-Export"}


# KNOWN ISSUES & TODOs & MAYBEs (in a random order):
#
# - issue: material assignment is not consistent.
#       models got multiple materials assigned.
#       models got crystal material assigned instead texture.
# - issue: some images could not be loaded to blender.
#       #DEBUG fpl images.load C:\Users\user\AppData\Local\Temp\__grab__fpl__\bulb_trigger_star_v2\Bulb-Trigger-Star-v2.bmp
#       IMB_ibImageFromMemory: unknown fileformat (C:\Users\user\AppData\Local\Temp\__grab__fpl__\bulb_trigger_star_v2\Bulb-Trigger-Star-v2.bmp)
#       #DEBUG fpl images.load C:\Users\user\AppData\Local\Temp\__grab__fpl__\gameover\GameOver.tga
#       decodetarga: incomplete file, 7.9% missing
#
# - todo: delete all unused temporary scenes with its content.
#       to shrink file size.
# - todo: create better light settings.
#       should give nice results for "Blender Render" and "Cycles Render" render engine.
# - todo: create better material settings.
#       handling texture, color, transparent, crystal, light, chrome.
# - todo: create camera + setup
#       to see the whole table, playfield, backglass.
# - todo: make all materials and material textures as separate.
#       to bypass cyclic textures at texture baking.
# - todo: cut holes to playfield and surfaces for mask models.
#       using curves? - by separate model mask and add as curve - multiple curves to one mesh?
#       using boolean? - by separate model mask and for each a boolean modifier?
# - todo: align models only on .fpt import not as currently on .fpm level.
#       find a way to get a general method, to align model position alignment at .fpt level, not on .fpm level.
#       (more hardcoding?)
# - todo: improve mark_as_ramp_end_point handling (see def create_ramp_curve_points).
#
# - maybe: add a pop-up message/dialog to inform the user, that the import process takes its time.
#       progress bar/text - is there something like that available in blender?
# - maybe: light dome (baking ambient occlusion has some issues)
# - maybe: import image lists as image sequences (maybe for BGE usage far far later)
# - maybe: animation got lost by got rid of using dupli-groups
#       copy the animations object-by-object and make them as NLA action strip (maybe for BGE usage far far later)
# - maybe: import sounds. (maybe for BGE usage far far later)
# - maybe: import music. (maybe for BGE usage far far later)
# - maybe: import VisualBasic script and transform to python script. (maybe for BGE usage far far later)
#
# - maybe: add possibility to export/write back future pinball model files (.fpm)
#       import/handle/export collision data
#       rewrite/extend cfb_spec.py for write IO
#       rewrite/extend fpx_spec.py for write IO
#       rewrite/extend lzo_spec.py for write IO


# To support reload properly, try to access a package var,
# if it's there, reload everything
if 'bpy' in locals():
    import imp
    if 'io_scene_fpx.fpx_ui' in locals():
        imp.reload(io_scene_fpx.fpx_ui)
else:
    from io_scene_fpx.fpx_ui import (
            FpmImportOperator,
            FplImportOperator,
            FptImportOperator,
            )


#import blender stuff
from bpy.utils import (
        register_module,
        unregister_module,
        )
from bpy.types import (
        INFO_MT_file_export,
        INFO_MT_file_import,
        )


###############################################################################
# registration
def register():
    ####################
    # F8 - key
    import imp
    imp.reload(fpx_ui)
    # F8 - key
    ####################

    fpx_ui.register()

    register_module(__name__)
    INFO_MT_file_import.append(FpmImportOperator.menu_func)
    INFO_MT_file_import.append(FplImportOperator.menu_func)
    INFO_MT_file_import.append(FptImportOperator.menu_func)


def unregister():
    fpx_ui.unregister()

    unregister_module(__name__)
    INFO_MT_file_import.remove(FpmImportOperator.menu_func)
    INFO_MT_file_import.remove(FplImportOperator.menu_func)
    INFO_MT_file_import.remove(FptImportOperator.menu_func)


###############################################################################
# global entry point
if (__name__ == "__main__"):
    register()

###############################################################################


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
