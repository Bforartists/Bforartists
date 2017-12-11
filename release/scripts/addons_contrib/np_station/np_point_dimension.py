
# BEGIN GPL LICENSE BLOCK #####
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
# END GPL LICENSE BLOCK #####



bl_info = {
    'name': 'NP 020 Point Dimension',
    'author': 'Okavango & the Blenderartists community',
    'version': (0, 2, 0),
    'blender': (2, 75, 0),
    'location': 'View3D',
    'warning': '',
    'description': 'Creates OpenGL dimensions with use of snap',
    'wiki_url': '',
    'category': '3D View'}

import bpy
import copy
import bgl
import blf
import mathutils
from bpy_extras import view3d_utils
from bpy.app.handlers import persistent
from mathutils import Vector, Matrix
from blf import ROTATION
from math import radians

from .utils_geometry import *
from .utils_graphics import *
from .utils_function import *



###############
## FUNCTIONS ##
###############

def display_toggle_callback(self, context):
    apply_layer_settings(context)


#######################
## CUSTOM PROPERTIES ##
#######################

# defining properties that will be assigned to each created dimension item:


class NPDM_dim_definition(bpy.types.PropertyGroup):

    index = bpy.props.IntProperty(name='Index', description='Unique ID index', default=0, min=0)
    kind = bpy.props.StringProperty(name='Kind', description='Type of the dimension', default='ALIGNED')
    show = bpy.props.BoolProperty(name='Show', description='Is the dimension displayed in the viewport', default=True, update=display_toggle_callback)
    selected = bpy.props.BoolProperty(name='Selected', description='Is dimension currently selected', default=False, update=display_toggle_callback)

    a_co3d = bpy.props.FloatVectorProperty(name='A_co3d', description='World coordinates of object point A', default=(0.0, 0.0, 0.0), update=display_toggle_callback)
    b_co3d = bpy.props.FloatVectorProperty(name='A_co3d', description='World coordinates of object point B', default=(0.0, 0.0, 0.0), update=display_toggle_callback)

    base_show = bpy.props.BoolProperty(name='Base_Show', description='Is the base line displayed', default=True, update=display_toggle_callback)
    base_distance = bpy.props.IntProperty(name="Base_Distance", description='Distance of the base line from the object points', default=0, max=5000, min=-5000, update=display_toggle_callback)
    base_extend = bpy.props.IntProperty(name="Base_Extend", description='Extension of the base line beyond the guide lines', default=0, max=5000, min=-5000, update=display_toggle_callback)
    base_thickness = bpy.props.FloatProperty(name="Base_Thickness", description='Thickness of the base line', default=1.0, max=30, min=0, update=display_toggle_callback)
    base_color = bpy.props.FloatVectorProperty(name='Base_Color', description = 'Color of the base line', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, update=display_toggle_callback)

    guide_show = bpy.props.BoolProperty(name='Guide_Show', description='Are the guide lines displayed', default=True, update=display_toggle_callback)
    guide_direction = bpy.props.EnumProperty(name="Guide_Direction", description='Direction of the guide lines starting from the object points', items=('2D_PERPENDICULAR_POSITIVE', '2D_PERPENDICULAR_NEGATIVE', '3D_X_POSITIVE', '3D_X_NEGATIVE','3D_Y_POSITIVE','3D_Y_NEGATIVE','3D_Z_POSITIVE','3D_Z_NEGATIVE'), default='2D_PERPENDICULAR_POSITIVE', update=display_toggle_callback)
    guide_type = bpy.props.EnumProperty(name="Guide_Type", description='Type of the guide lines regarding offset from the object points', items=('FIXED_LENGTH', 'OFFSET'), default='FIXED_LENGTH', update=display_toggle_callback)
    guide_length = bpy.props.IntProperty(name="Guide_Length", description='Length of the guide lines, if the type is FIXED_LENGTH', default=0, max=5000, min=-5000, update=display_toggle_callback)
    guide_offset = bpy.props.IntProperty(name="Guide_Offset", description='Offset of the guide lines from the object points, if the type is OFFSET', default=0, max=5000, min=-5000, update=display_toggle_callback)
    guide_extend = bpy.props.IntProperty(name="Guide_Extend", description='Extension of the guide lines beyond the base line', default=0, max=5000, min=-5000, update=display_toggle_callback)
    guide_thickness = bpy.props.FloatProperty(name="Guide_Thickness", description='Thickness of the guide lines', default=1.0, max=30, min=0, update=display_toggle_callback)
    guide_color = bpy.props.FloatVectorProperty(name='Guide_Color',  description = 'Color of the guide lines', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, update=display_toggle_callback)

    arrow_show = bpy.props.BoolProperty(name='Arrow_Show', description='Are the arrows displayed', default=True, update=display_toggle_callback)
    arrow_shape = bpy.props.EnumProperty(name="Arrow_Shape", description='Shape of the base line arrows', items=('NONE', 'ARROW', 'TRIANGLE', 'DOT','TICK'), default='NONE', update=display_toggle_callback)
    arrow_size = bpy.props.IntProperty(name="Arrow_Size", description='Size of the base line arrows', default=10, max=50, min=-50, update=display_toggle_callback)
    arrow_thickness = bpy.props.FloatProperty(name="Arrow_Thickness", description='Thickness of the base line arrows, if type is TICK', default=1.0, max=30, min=0, update=display_toggle_callback) #for shape thick, or use rectangular shape
    arrow_color = bpy.props.FloatVectorProperty(name='Arrow_Color', description = 'Color of the base line arrows', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, update=display_toggle_callback)

    num_show = bpy.props.BoolProperty(name='Num_Show', description='Is the numeric displayed', default=True, update=display_toggle_callback)
    num_scale = bpy.props.FloatProperty(name="Num_Scale", description='Measurement multiplier (for example, for cm use 100)', default=100, min=0, step=1, precision=3, update=display_toggle_callback)
    num_suffix = bpy.props.EnumProperty(name="Num_Suffix", description='Unit extension to be displayed after the numeric', items=(("'", "'", ''), ('"', '"', ''), ('thou', 'thou', ''), ('km', 'km', ''), ('m', 'm', ''), ('cm', 'cm', ''), ('mm', 'mm', ''), ('nm', 'nm', ''), ('NONE', 'NONE', '')), default='NONE', update=display_toggle_callback)
    num_override = bpy.props.StringProperty(name='Num_Override', description='Text do be displayed instead of the measurement', default='')
    num_note = bpy.props.StringProperty(name='Num_Note', description='Text do be displayed together and after the measurement', default='')
    num_along = bpy.props.FloatProperty(name="Num_Along", description='Position of the numeric along the base line', default=0.0, max=+110, min=-110, step=1, precision=3, update=display_toggle_callback)
    num_offset = bpy.props.IntProperty(name="Num_Offset", description='Offset of the numeric from the base line', default=10, max=5000, min=-5000, update=display_toggle_callback)
    num_size = bpy.props.IntProperty(name="Num_Size", description='Size of the numeric', default=10, max=50, min=1, update=display_toggle_callback)
    num_color = bpy.props.FloatVectorProperty(name='Num_Color', description = 'Color of the numeric', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, update=display_toggle_callback)

    mark_dim_show = bpy.props.BoolProperty(name='Mark_Dim_Show', description='Is the dimension marker displayed', default=True, update=display_toggle_callback)
    mark_dim_shape = bpy.props.EnumProperty(name="Mark_Dim_Shape", description='Shape of the dimension marker', items=('SQUARE', 'DIAMOND', 'DOT'), default='SQUARE', update=display_toggle_callback)
    mark_dim_size = bpy.props.IntProperty(name="Mark_Dim_Size", description='Size of the dimension marker', default=10, max=50, min=1, update=display_toggle_callback)
    mark_dim_color = bpy.props.FloatVectorProperty(name='Mark_Dim_Color', description = 'Color of the dimension marker', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, update=display_toggle_callback)
    mark_dim_selected = bpy.props.BoolProperty(name='Mark_Dim_Selected', description='Is the dimension marker currently selected', default=False, update=display_toggle_callback)

    mark_a_show = bpy.props.BoolProperty(name='Mark_A_Show', description='Is the A point marker displayed', default=True, update=display_toggle_callback)
    mark_a_shape = bpy.props.EnumProperty(name="Mark_A_Shape", description='Shape of the A point marker', items=('DOT', 'DIAMOND', 'SQUARE'), default='DOT', update=display_toggle_callback)
    mark_a_size = bpy.props.IntProperty(name="Mark_A_Size", description='Size of the A point marker', default=10, max=50, min=1, update=display_toggle_callback)
    mark_a_color = bpy.props.FloatVectorProperty(name='Mark_A_Color', description = 'Color of the A point marker', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, update=display_toggle_callback)
    mark_a_selected = bpy.props.BoolProperty(name='Mark_A_Selected', description='Is the A point marker currently selected', default=False, update=display_toggle_callback)

    mark_b_show = bpy.props.BoolProperty(name='Mark_B_Show', description='Is the B point marker displayed', default=True, update=display_toggle_callback)
    mark_b_shape = bpy.props.EnumProperty(name="Mark_B_Shape", description='Shape of the B point marker', items=('DOT', 'DIAMOND', 'SQUARE'), default='DOT', update=display_toggle_callback)
    mark_b_size = bpy.props.IntProperty(name="Mark_B_Size", description='Size of the A point marker', default=10, max=50, min=1, update=display_toggle_callback)
    mark_b_color = bpy.props.FloatVectorProperty(name='Mark_B_Color', description = 'Color of the B point marker', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, update=display_toggle_callback)
    mark_b_selected = bpy.props.BoolProperty(name='Mark_B_Selected', description='Is the B point marker currently selected', default=False, update=display_toggle_callback)

    mark_base_show = bpy.props.BoolProperty(name='Mark_Base_Show', description='Is the base line marker displayed', default=True, update=display_toggle_callback)
    mark_base_shape = bpy.props.EnumProperty(name="Mark_Base_Shape", description='Shape of the base line marker', items=('DOT', 'DIAMOND', 'SQUARE'), default='DOT', update=display_toggle_callback)
    mark_base_size = bpy.props.IntProperty(name="Mark_Base_Size", description='Size of the base line marker', default=10, max=50, min=1, update=display_toggle_callback)
    mark_base_color = bpy.props.FloatVectorProperty(name='Mark_Base_Color', description = 'Color of the base line marker', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, update=display_toggle_callback)
    mark_base_selected = bpy.props.BoolProperty(name='Mark_Base_Selected', description='Is the base line marker currently selected', default=False, update=display_toggle_callback)

    mark_guide_show = bpy.props.BoolProperty(name='Mark_Guide_Show', description='Is the guide line marker displayed', default=True, update=display_toggle_callback)
    mark_guide_shape = bpy.props.EnumProperty(name="Mark_Guide_Shape", description='Shape of the guide line marker', items=('DOT', 'DIAMOND', 'SQUARE'), default='DOT', update=display_toggle_callback)
    mark_guide_size = bpy.props.IntProperty(name="Mark_Guide_Size", description='Size of the guide line marker', default=10, max=50, min=1, update=display_toggle_callback)
    mark_guide_color = bpy.props.FloatVectorProperty(name='Mark_Guide_Color', description = 'Color of the guide linen marker', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, update=display_toggle_callback)
    mark_guide_selected = bpy.props.BoolProperty(name='Mark_Guide_Selected', description='Is the guide line marker currently selected', default=False, update=display_toggle_callback)

    mark_num_show = bpy.props.BoolProperty(name='Mark_Num_Show', description='Is the numeric marker displayed', default=True, update=display_toggle_callback)
    mark_num_shape = bpy.props.EnumProperty(name="Mark_Num_Shape", description='Shape of the numeric marker', items=('DIAMOND', 'DOT', 'SQUARE'), default='DIAMOND', update=display_toggle_callback)
    mark_num_size = bpy.props.IntProperty(name="Mark_Num_Size", description='Size of the numeric marker', default=10, max=50, min=1, update=display_toggle_callback)
    mark_num_color = bpy.props.FloatVectorProperty(name='Mark_Num_Color', description = 'Color of the numeric marker', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, update=display_toggle_callback)
    mark_num_selected = bpy.props.BoolProperty(name='Mark_Num_Selected', description='Is the numeric marker currently selected', default=False, update=display_toggle_callback)


def register():




def unregister():


    pass
