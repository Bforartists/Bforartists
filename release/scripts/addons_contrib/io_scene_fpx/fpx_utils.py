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
# initial script copyright (c)2013 Alexander Nussbaumer
#
# ##### END COPYRIGHT BLOCK #####


#import blender stuff
from bpy import (
        ops,
        )
from bpy.path import (
        resolve_ncase,
        )
from os import (
        path,
        )


class FpxUtilities:

    ###########################################################################
    TAG_NAME = "raw_dump"

    @staticmethod
    def str_begin_tag(value):
        print("<{}>".format(value))

    @staticmethod
    def str_end_tag(value):
        print("</{}>".format(value))

    @staticmethod
    def dump_bin(dump, address=0, comment="", max_size=0x0000000FFFFF, sector_list=None, sector_size=None, add_tags=True):
        if dump is None:
            return
        tag_name = FpxUtilities.TAG_NAME
        gap_hex = "|| "
        default_marker_left = ' ('
        default_marker_right = ')  '
        view_output = []
        view_chr = []
        max_index = len(dump) - 1
        last_sector_view_address = -1

        if max_index > max_size:
            max_index = max_size

        if add_tags:
            FpxUtilities.str_begin_tag(tag_name)

        for index, value in enumerate(dump):
            view_address = index + address
            view_address_16 = view_address & 15

            # cut of value to char
            if isinstance(value, str):
                if (value >= chr(32) and value < chr(127)):
                    value_chr = value
                else:
                    value_chr = '.'
            else:
                if (value >= 32 and value < 127):
                    value_chr = chr(value)
                else:
                    value_chr = '.'
            if (value >= 32 and value < 127):
                value_chr = chr(value)
            else:
                value_chr = '.'

            if index == 0 or view_address_16 == 0:
                # show address
                if sector_list is not None and sector_size is not None:
                    # address must be 0
                    sector_index = view_address // sector_size
                    sector_view_address = ((view_address % sector_size) + sector_list[sector_index]) & ~15
                    if index and sector_view_address != (last_sector_view_address & ~15) + 16:
                        marker_left = '[['
                        marker_right = ']]]'
                    else:
                        marker_left = default_marker_left
                        marker_right = default_marker_right
                    view_output.append("{:08X}{}{:08X}{}".format(sector_view_address, marker_left, index, marker_right))
                    last_sector_view_address = sector_view_address
                else:
                    view_output.append("{:08X}{}{:08X}{}".format(view_address_16, default_marker_left, index, default_marker_right))

            if index == 0 and view_address_16 != 0:
                # fill gap between 'address' and  'data'
                # and between 'data' and 'char'
                for n in range(view_address_16):
                    view_output.append(gap_hex)
                    view_chr.append(" ")

            if isinstance(value, str):
                view_output.append("{:02X} ".format(ord(value)))
            else:
                view_output.append("{:02X} ".format(value))
            view_chr.append(value_chr)

            if index >= max_index or view_address_16 == 15:
                if view_address_16 != 15:
                    # fill gap between 'data' and 'char'
                    for n in range(view_address_16, 15):
                        view_output.append(gap_hex)

                # merge all
                view_output.append(" ")
                view_output.append("".join(view_chr))
                view_chr = []

                if comment:
                    if view_address_16 != 15:
                        # fill gap between 'char' and 'comment'
                        for n in range(view_address_16, 15):
                            view_output.append(" ")
                    view_output.append("  ")
                    view_output.append(comment)
                    comment = None

                if index < max_index:
                    view_output.append("\n")

                if index >= max_index:
                    break

        print("".join(view_output))

        if add_tags:
            FpxUtilities.str_end_tag(tag_name)


    ###########################################################################
    @staticmethod
    def toGoodName(s):
        if not s:
            return s

        sx = []
        for c in s:
            if (
                    (c != '_') and (c != '.') and
                    (c != '[') and (c != ']') and
                    (c != '(') and (c != ')') and
                    (c != '{') and (c != '}') and
                    (c < '0' or c > '9') and
                    (c < 'A' or c > 'Z') and
                    (c < 'a' or c > 'z')
                    ):
                c = '_'
            sx.append(c)
        return str().join(sx).lower().strip(". ")

    ###########################################################################
    @staticmethod
    def toGoodFilePath(s):
        """ source path/filenames are based on windows systems """
        if not s:
            return s

        # detecting custom operating system
        if path.sep != '\\':
            # replace windows sep to custom os sep
            s = s.replace('\\', path.sep)

            # find and cutoff drive letter
            i = s.find(':')
            if i > -1:
                s = s[i + 1:]

        # try to handle case sensitive names in case of such os
        s = resolve_ncase(s)

        return s

    ###########################################################################
    @staticmethod
    def enable_edit_mode(enable, blender_context):
        if blender_context.active_object is None or not blender_context.active_object.type in {'CURVE', 'MESH', 'ARMATURE', }:
            return

        if enable:
            modeString = 'EDIT'
        else:
            modeString = 'OBJECT'

        if ops.object.mode_set.poll():
            ops.object.mode_set(mode=modeString)

    ###########################################################################
    @staticmethod
    def select_all(select):
        if select:
            actionString = 'SELECT'
        else:
            actionString = 'DESELECT'

        if ops.object.select_all.poll():
            ops.object.select_all(action=actionString)
        elif ops.curve.select_all.poll():
            ops.curve.select_all(action=actionString)
        elif ops.mesh.select_all.poll():
            ops.mesh.select_all(action=actionString)
        elif ops.pose.select_all.poll():
            ops.pose.select_all(action=actionString)


    ###########################################################################
    @staticmethod
    def set_scene_to_metric(blender_context):
        # set metrics
        blender_context.scene.unit_settings.system = 'METRIC'
        blender_context.scene.unit_settings.system_rotation = 'DEGREES'
        blender_context.scene.unit_settings.scale_length = 0.001 # 1.0mm
        blender_context.scene.unit_settings.use_separate = False

        blender_context.tool_settings.normal_size = 1.0 # 1.0mm

        # set all 3D views to texture shaded
        # and set up the clipping
        for screen in blender_context.blend_data.screens:
            for area in screen.areas:
                if (area.type != 'VIEW_3D'):
                    continue

                for space in area.spaces:
                    if (space.type != 'VIEW_3D'):
                        continue
                    #adjust clipping to new units
                    space.clip_start = 0.1 # 0.1mm
                    space.clip_end = 1000000.0 # 1km

                    #space.viewport_shade = 'SOLID'
                    #space.show_textured_solid = True
                    space.show_backface_culling = True

            screen.scene.tool_settings.normal_size = 10

            #screen.scene.game_settings.material_mode = 'MULTITEXTURE'


    ###########################################################################
    @staticmethod
    def set_scene_to_default(blender_scene):
        # set default
        blender_scene.unit_settings.system = 'NONE'
        blender_scene.unit_settings.system_rotation = 'DEGREES'
        blender_scene.unit_settings.scale_length = 1.0
        blender_scene.unit_settings.use_separate = False


    ###########################################################################

###############################################################################


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
