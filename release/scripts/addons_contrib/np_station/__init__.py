### BEGIN GPL LICENSE BLOCK #####
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
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

# Many thanks to Blender Artists, Mano Wii and Elegant Artz

bl_info = {
    'name': 'NP Station',
    'author': 'Okavango with the help of Blenderartists community',
    'version': (0, 2, 0),
    'blender': (2, 78, 0),
    'location': 'View3D > Toolshelf > Tools tab',
    'warning': '',
    'description': 'Set of utilities for CAD-like precision modeling',
    'wiki_url': 'https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Object/NP_Station',
    'category': '3D View'}

if 'bpy' in locals():
    import imp
    imp.reload(np_point_move)
    imp.reload(np_point_copy)
    imp.reload(np_point_instance)
    imp.reload(np_point_array)
    imp.reload(np_roto_move)
    imp.reload(np_point_scale)
    imp.reload(np_float_rectangle)
    imp.reload(np_float_box)
    imp.reload(np_point_align)
    imp.reload(np_point_distance)
    imp.reload(np_float_poly)
    imp.reload(np_shader_brush)

else:
    from . import np_point_move
    from . import np_point_copy
    from . import np_point_instance
    from . import np_point_array
    from . import np_roto_move
    from . import np_point_scale
    from . import np_float_rectangle
    from . import np_float_box
    from . import np_point_align
    from . import np_point_distance
    from . import np_float_poly
    from . import np_shader_brush

import bpy


# Defining the class that will make a NP tab panel in the tool shelf with the operator buttons:

class NP020BasePanel(bpy.types.Panel):
    # Creates a panel in the 3d view Toolshelf window
    bl_label = 'NP Station'
    bl_idname = 'NP_PT_020_base_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = 'objectmode'
    bl_category = 'Tools'

    def draw(self, context):
        layout = self.layout

        row = self.layout.row(True)
        col = row.column(True)
        col.label(" Create:",icon = "MESH_CUBE")
        col.separator()
        col.operator('object.np_020_float_poly', icon='MESH_DATA', text='float_poly')
        col.operator('object.np_020_float_rectangle', icon='MESH_PLANE', text='float_rectangle')
        col.operator('object.np_020_float_box', icon='MESH_CUBE', text='float_box')

        self.layout.separator()
        row = self.layout.row(True)
        col = row.column(True)
        col.label(" Modify:",icon = "MODIFIER")
        col.separator()
        col.operator('object.np_020_point_move', icon='MAN_TRANS', text='point_move')
        col.operator('object.np_020_point_copy', icon='ROTACTIVE', text='point_copy')
        col.operator('object.np_020_point_instance', icon='ROTATECOLLECTION', text='point_instance')
        col.operator('object.np_020_point_array', icon='MOD_ARRAY', text='point_array')
        col.operator('object.np_020_roto_move', icon='MAN_ROT', text='roto_move')
        col.operator('object.np_020_point_scale', icon='MAN_SCALE', text='point_scale')
        col.operator('object.np_020_point_align', icon='ORTHO', text='point_align')


        self.layout.separator()
        row = self.layout.row(True)
        col = row.column(True)
        col.label(" Transfer:",icon = 'BRUSH_DATA')
        col.separator()
        col.operator('object.np_020_shader_brush', icon='MOD_DYNAMICPAINT', text='shader_brush')


        self.layout.separator()
        row = self.layout.row(True)
        col = row.column(True)
        col.label(" Measure:",icon = "ALIGN")
        col.separator()
        col.operator('object.np_020_point_distance', icon='ARROW_LEFTRIGHT', text='point_distance')


##########################################################################################


# Add-ons Preferences Update Panel

# Define Panel classes for updating
panels = [
        NP020BasePanel,
        ]


def update_panel(self, context):
    message = "Bool Tool: Updating Panel locations has failed"
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panels:
            panel.bl_category = context.user_preferences.addons[__package__].preferences.category
            bpy.utils.register_class(panel)

    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__package__, message, e))
        pass



# Defining the settings in the addons tab:

class NP020Preferences(bpy.types.AddonPreferences):
    # This must match the addon name, use '__package__' when defining this in a submodule of a python package.

    bl_idname = __name__


    category = bpy.props.StringProperty(
            name="",
            description="Choose a name for the category of the panel",
            default="Tools",
            update=update_panel,
            )

#----------------------------------------------------------------------------------------


    np_col_scheme = bpy.props.EnumProperty(
        name ='',
        items = (
            ('csc_default_grey', 'Blender_Default_NP_GREY',''),
            ('csc_school_marine', 'NP_school_paper_NP_MARINE','')),
        default = 'csc_default_grey',
        description = 'Choose the overall addon color scheme, according to your current Blender theme')

    np_size_num = bpy.props.IntProperty(
            name='',
            description='Size of the numerics that display on-screen dimensions, the default is 18',
            default=18,
            min=10,
            max=30)

    np_scale_dist = bpy.props.FloatProperty(
            name='',
            description='Distance multiplier (for example, for cm use 100)',
            default=100,
            min=0,
            step=100,
            precision=2)

    np_suffix_dist = bpy.props.EnumProperty(
        name='',
        items=(("'", "'", ''), ('"', '"', ''), (' thou', 'thou', ''),
               (' km', 'km', ''), (' m', 'm', ''), (' cm', 'cm', ''),
               (' mm', 'mm', ''), (' nm', 'nm', ''), ('None', 'None', '')),
        default=' cm',
        description='Add a unit extension after the numerical distance ')

    np_display_badge = bpy.props.BoolProperty(
            name='Display badge',
            description='Use the graphical badge near the mouse cursor',
            default=True)

    np_size_badge = bpy.props.IntProperty(
            name='badge_size',
            description='Size of the mouse badge, the default is 2',
            default=2,
            min=0,
            step=10)

    op_prefs = bpy.props.EnumProperty(
        name ='Individual operator settings',
        items = (
            ('nppd', 'NP Point Distance',''),
            ('npsb', 'NP Shader Brush',''),
            ('nppl', 'NP Point Align',''),
            ('npps', 'NP Point Scale',''),
            ('nprm', 'NP Roto Move',''),
            ('nppa', 'NP Point Array',''),
            ('nppi', 'NP Point Instance',''),
            ('nppc', 'NP Point Copy',''),
            ('nppm', 'NP Point Move',''),
            ('npfr', 'NP Float Box',''),
            ('npfr', 'NP Float Rectangle',''),
            ('npfp', 'NP Float Poly','')),
        default = 'npfp',
        description = 'Choose which settings would you like to access')


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

    '''
    nppc_dist_scale = bpy.props.FloatProperty(
            name='Unit scale',
            description='Distance multiplier (for example, for cm use 100)',
            default=100,
            min=0,
            step=1,
            precision=3)

    nppc_suffix = bpy.props.EnumProperty(
        name='Unit suffix',
        items=(("'","'",''), ('"','"',''), ('thou','thou',''), ('km','km',''), ('m','m',''), ('cm','cm',''), ('mm','mm',''), ('nm','nm',''), ('None','None','')),
        default='cm',
        description='Add a unit extension after the numerical distance ')

    nppc_badge = bpy.props.BoolProperty(
            name='Mouse badge',
            description='Use the graphical badge near the mouse cursor',
            default=True)

    nppc_badge_size = bpy.props.FloatProperty(
            name='size',
            description='Size of the mouse badge, the default is 2.0',
            default=2,
            min=0.5,
            step=10,
            precision=1)

    nppc_col_line_main_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    nppc_col_line_shadow_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    nppc_col_num_main_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    nppc_col_num_shadow_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    nppc_col_line_main = bpy.props.FloatVectorProperty(name='', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the measurement line, to disable it set alpha to 0.0')

    nppc_col_line_shadow = bpy.props.FloatVectorProperty(name='', default=(0.1, 0.1, 0.1, 0.25), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the line shadow, to disable it set alpha to 0.0')

    nppc_col_num_main = bpy.props.FloatVectorProperty(name='', default=(0.1, 0.1, 0.1, 0.75), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the number, to disable it set alpha to 0.0')

    nppc_col_num_shadow = bpy.props.FloatVectorProperty(name='', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the number shadow, to disable it set alpha to 0.0')
    '''
#----------------------------------------------------------------------------------------

    '''
    nppi_dist_scale = bpy.props.FloatProperty(
            name='Unit scale',
            description='Distance multiplier (for example, for cm use 100)',
            default=100,
            min=0,
            step=1,
            precision=3)

    nppi_suffix = bpy.props.EnumProperty(
        name='Unit suffix',
        items=(("'","'",''), ('"','"',''), ('thou','thou',''), ('km','km',''), ('m','m',''), ('cm','cm',''), ('mm','mm',''), ('nm','nm',''), ('None','None','')),
        default='cm',
        description='Add a unit extension after the numerical distance ')

    nppi_badge = bpy.props.BoolProperty(
            name='Mouse badge',
            description='Use the graphical badge near the mouse cursor',
            default=True)

    nppi_badge_size = bpy.props.FloatProperty(
            name='size',
            description='Size of the mouse badge, the default is 2.0',
            default=2,
            min=0.5,
            step=10,
            precision=1)

    nppi_col_line_main_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    nppi_col_line_shadow_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    nppi_col_num_main_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    nppi_col_num_shadow_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    nppi_col_line_main = bpy.props.FloatVectorProperty(name='', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the measurement line, to disable it set alpha to 0.0')

    nppi_col_line_shadow = bpy.props.FloatVectorProperty(name='', default=(0.1, 0.1, 0.1, 0.25), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the line shadow, to disable it set alpha to 0.0')

    nppi_col_num_main = bpy.props.FloatVectorProperty(name='', default=(0.1, 0.1, 0.1, 0.75), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the number, to disable it set alpha to 0.0')

    nppi_col_num_shadow = bpy.props.FloatVectorProperty(name='', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the number shadow, to disable it set alpha to 0.0')
    '''
#----------------------------------------------------------------------------------------

    nppd_scale = bpy.props.FloatProperty(
            name = 'Scale',
            description = 'Distance multiplier (for example, for cm use 100)',
            default = 100,
            min = 0,
            step = 1,
            precision = 3)

    nppd_suffix = bpy.props.EnumProperty(
        name = 'Suffix',
        items = (
            ("'", "'", ''), ('"', '"', ''), (
                'thou', 'thou', ''), ('km', 'km', ''),
            ('m', 'm', ''), ('cm', 'cm', ''), ('mm', 'mm', ''), ('nm', 'nm', ''), ('None', 'None', '')),
        default = 'cm',
        description = 'Add a unit extension after the number ')

    nppd_badge = bpy.props.BoolProperty(
            name = 'Mouse badge',
            description = 'Use the graphical badge near the mouse cursor',
            default = True)

    nppd_step = bpy.props.EnumProperty(
        name ='Step',
        items = (
            ('simple', 'simple',
             'one-step procedure, stops after the second click'),
            ('continuous', 'continuous', 'continuous repetition of command, ESC or RMB to interrupt (some performance slowdown)')),
        default = 'simple',
        description = 'The way the command behaves after the second click')

    nppd_hold = bpy.props.BoolProperty(
            name = 'Hold result',
            description = 'Include an extra step to display the last measured distance in the viewport',
            default = False)

    nppd_gold = bpy.props.BoolProperty(
            name = 'Golden ratio',
            description = 'Display a marker showing the position of the golden division point (1.61803 : 1)',
            default = False)

    nppd_info = bpy.props.BoolProperty(
            name = 'Value to header info',
            description = 'Display last measured distance on the header',
            default = True)

    nppd_clip = bpy.props.BoolProperty(
            name = 'Value to clipboard',
            description = 'Copy last measured distance to clipboard for later reuse',
            default = True)

    nppd_col_line_main_DEF = bpy.props.BoolProperty(
            name = 'Default',
            description = 'Use the default color',
            default = True)

    nppd_col_line_shadow_DEF = bpy.props.BoolProperty(
            name = 'Default',
            description = 'Use the default color',
            default = True)

    nppd_col_num_main_DEF = bpy.props.BoolProperty(
            name = 'Default',
            description = 'Use the default color',
            default = True)

    nppd_col_num_shadow_DEF = bpy.props.BoolProperty(
            name = 'Default',
            description = 'Use the default color',
            default = True)

    nppd_xyz_lines = bpy.props.BoolProperty(
            name = 'XYZ lines',
            description = 'Display axial distance lines',
            default = True)

    nppd_xyz_distances = bpy.props.BoolProperty(
            name = 'XYZ distances',
            description = 'Display axial distances',
            default = True)

    nppd_xyz_backdrop = bpy.props.BoolProperty(
            name = 'XYZ backdrop',
            description = 'Display backdrop field for xyz distances',
            default = False)

    nppd_stereo_cage = bpy.props.BoolProperty(
            name = 'Stereo cage',
            description = 'Display bounding box that contains the dimension',
            default = True)

    nppd_col_line_main = bpy.props.FloatVectorProperty(
        name = '',
        default = (1.0,
     1.0,
     1.0,
     1.0),
        size = 4,
        subtype = "COLOR",
        min = 0,
        max = 1,
        description = 'Color of the measurement line, to disable it set alpha to 0.0')

    nppd_col_line_shadow = bpy.props.FloatVectorProperty(
        name = '',
        default = (0.1,
     0.1,
     0.1,
     0.25),
        size = 4,
        subtype = "COLOR",
        min = 0,
        max = 1,
        description = 'Color of the line shadow, to disable it set alpha to 0.0')

    nppd_col_num_main = bpy.props.FloatVectorProperty(
        name = '',
        default = (0.1,
     0.1,
     0.1,
     0.75),
        size = 4,
        subtype = "COLOR",
        min = 0,
        max = 1,
        description = 'Color of the number, to disable it set alpha to 0.0')

    nppd_col_num_shadow = bpy.props.FloatVectorProperty(
        name = '',
        default = (1.0,
     1.0,
     1.0,
     0.65),
        size = 4,
        subtype = "COLOR",
        min = 0,
        max = 1,
        description = 'Color of the number shadow, to disable it set alpha to 0.0')

#----------------------------------------------------------------------------------------
    '''
    nppa_dist_scale = bpy.props.FloatProperty(
            name='Unit scale',
            description='Distance multiplier (for example, for cm use 100)',
            default=100,
            min=0,
            step=1,
            precision=3)

    nppa_suffix = bpy.props.EnumProperty(
        name='Unit suffix',
        items=(("'","'",''), ('"','"',''), ('thou','thou',''), ('km','km',''), ('m','m',''), ('cm','cm',''), ('mm','mm',''), ('nm','nm',''), ('None','None','')),
        default='cm',
        description='Add a unit extension after the numerical distance ')

    nppa_badge = bpy.props.BoolProperty(
            name='Mouse badge',
            description='Use the graphical badge near the mouse cursor',
            default=True)

    nppa_badge_size = bpy.props.FloatProperty(
            name='size',
            description='Size of the mouse badge, the default is 2.0',
            default=2,
            min=0.5,
            step=10,
            precision=1)

    nppa_col_line_main_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    nppa_col_line_shadow_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    nppa_col_num_main_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    nppa_col_num_shadow_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    nppa_col_line_main = bpy.props.FloatVectorProperty(name='', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the measurement line, to disable it set alpha to 0.0')

    nppa_col_line_shadow = bpy.props.FloatVectorProperty(name='', default=(0.1, 0.1, 0.1, 0.25), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the line shadow, to disable it set alpha to 0.0')

    nppa_col_num_main = bpy.props.FloatVectorProperty(name='', default=(0.1, 0.1, 0.1, 0.75), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the number, to disable it set alpha to 0.0')

    nppa_col_num_shadow = bpy.props.FloatVectorProperty(name='', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the number shadow, to disable it set alpha to 0.0')
    '''

#----------------------------------------------------------------------------------------

    '''

    npfp_badge = bpy.props.BoolProperty(
            name='Mouse badge',
            description='Use the graphical badge near the mouse cursor',
            default=True)

    npfp_badge_size = bpy.props.FloatProperty(
            name='size',
            description='Size of the mouse badge, the default is 2.0',
            default=2,
            min=0.5,
            step=10,
            precision=1)
    '''
    npfp_point_markers = bpy.props.BoolProperty(
            name='Point markers',
            description='Use the markers for the start and other points of the poly',
            default=True)

    npfp_point_size = bpy.props.FloatProperty(
            name='size',
            description='Size of the start and point markers, the default is 5.0',
            default=5,
            min=0.5,
            step=50,
            precision=1)

    npfp_point_color_DEF = bpy.props.BoolProperty(
            name='Default point COLOR',
            description='Use the default color for the point markers',
            default=True)

    npfp_wire = bpy.props.BoolProperty(
            name='Wire contour',
            description="Use the 'show wireframe' option over the object's solid drawing",
            default=True)

    npfp_smooth = bpy.props.BoolProperty(
            name='Smooth shading',
            description='Automaticaly turn on smooth shading for the poly object',
            default=False)

    npfp_material = bpy.props.BoolProperty(
            name='Base material',
            description='Automaticaly assign a base material to the poly object',
            default=True)

    npfp_bevel = bpy.props.BoolProperty(
            name='Bevel',
            description='Start the bevel operation after the extrusion',
            default=False)

    npfp_point_color = bpy.props.FloatVectorProperty(
            name='', default=(0.3, 0.3, 0.3, 1.0),
            size=4, subtype="COLOR", min=0, max=1,
            description='Color of the point markers')
    '''
    npfp_col_line_main = bpy.props.FloatVectorProperty(
            name='', default=(1.0, 1.0, 1.0, 1.0),
            size=4, subtype="COLOR", min=0, max=1,
            description='Color of the measurement line, to disable it set alpha to 0.0')

    npfp_col_line_shadow = bpy.props.FloatVectorProperty(
            name='', default=(0.1, 0.1, 0.1, 0.25),
            size=4, subtype="COLOR", min=0, max=1,
            description='Color of the line shadow, to disable it set alpha to 0.0')

    npfp_col_num_main = bpy.props.FloatVectorProperty(
            name='', default=(0.1, 0.1, 0.1, 0.75),
            size=4, subtype="COLOR", min=0, max=1,
            description='Color of the number, to disable it set alpha to 0.0')

    npfp_col_num_shadow = bpy.props.FloatVectorProperty(
            name='', default=(1.0, 1.0, 1.0, 1.0),
            size=4, subtype="COLOR", min=0, max=1,
            description='Color of the number shadow, to disable it set alpha to 0.0')
    '''

#----------------------------------------------------------------------------------------

    '''
    npfr_dist_scale = bpy.props.FloatProperty(
            name='Unit scale',
            description='Distance multiplier (for example, for cm use 100)',
            default=100,
            min=0,
            step=1,
            precision=3)

    npfr_suffix = bpy.props.EnumProperty(
        name='Unit suffix',
        items=(("'","'",''), ('"','"',''), ('thou','thou',''), ('km','km',''), ('m','m',''), ('cm','cm',''), ('mm','mm',''), ('nm','nm',''), ('None','None','')),
        default='cm',
        description='Add a unit extension after the numerical distance ')

    npfr_badge = bpy.props.BoolProperty(
            name='Mouse badge',
            description='Use the graphical badge near the mouse cursor',
            default=True)

    npfr_badge_size = bpy.props.FloatProperty(
            name='size',
            description='Size of the mouse badge, the default is 2.0',
            default=2,
            min=0.5,
            step=10,
            precision=1)

    npfr_col_line_main_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    npfr_col_line_shadow_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    npfr_col_num_main_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    npfr_col_num_shadow_DEF = bpy.props.BoolProperty(
            name='Default',
            description='Use the default color',
            default=True)

    npfr_col_line_main = bpy.props.FloatVectorProperty(name='', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the measurement line, to disable it set alpha to 0.0')

    npfr_col_line_shadow = bpy.props.FloatVectorProperty(name='', default=(0.1, 0.1, 0.1, 0.25), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the line shadow, to disable it set alpha to 0.0')

    npfr_col_num_main = bpy.props.FloatVectorProperty(name='', default=(0.25, 0.35, 0.4, 1.0), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the number, to disable it set alpha to 0.0')

    npfr_col_num_shadow = bpy.props.FloatVectorProperty(name='', default=(1.0, 1.0, 1.0, 1.0), size=4, subtype="COLOR", min=0, max=1, description = 'Color of the number shadow, to disable it set alpha to 0.0')

    '''
##########################################################################################


    def draw(self, context):
        layout = self.layout

        box = layout.box()
        row = box.row()
        col = row.column()
        col.label(text='Tab category:')
        col = row.column()
        col.prop(self, "category")
        split = layout.split()
        split = layout.split()
        split = layout.split()
        col = split.column()
        col.label(text='Main color scheme:')
        col = split.column()
        col.prop(self, "np_col_scheme")
        split = layout.split()
        col = split.column()
        col.label(text='Size of the numerics:')
        col = split.column()
        col.prop(self, "np_size_num")
        split = layout.split()
        col = split.column()
        col.label(text='Unit scale for distance:')
        col = split.column()
        col.prop(self, "np_scale_dist")
        split = layout.split()
        col = split.column()
        col.label(text='Unit suffix for distance:')
        col = split.column()
        col.prop(self, "np_suffix_dist")
        split = layout.split()
        col = split.column()
        col.label(text='Mouse badge:')
        col = split.column()
        col = split.column()
        col.prop(self, "np_display_badge")
        if self.np_display_badge == True:
            col = split.column()
            col.prop(self, "np_size_badge")
        else:
            col = split.column()

        split = layout.split()
        split = layout.split()
        box = layout.box()
        row = box.row()
        #row.prop(self, "np_num_size")
        #row.prop(self, "np_num_size")
        #row.prop(self, "np_num_size")
        #box.alignment = 'LEFT'
        #split = layout.split()
        #col = split.column()
        #split = layout.split()
        #col = split.column()
        row.prop(self, "op_prefs")
        split = layout.split()
        split = layout.split()
        if self.op_prefs == 'nppc':
            layout = self.layout
            split = layout.split()
            split.label(text='No individual settings for this operator yet')
            split = layout.split()


        elif self.op_prefs == 'nppi':
            layout = self.layout
            split = layout.split()
            split.label(text='No individual settings for this operator yet')
            split = layout.split()


        elif self.op_prefs == 'nppa':
            layout = self.layout
            split = layout.split()
            split.label(text='No individual settings for this operator yet')
            split = layout.split()

        elif self.op_prefs == 'nprm':
            layout = self.layout
            split = layout.split()
            split.label(text='No individual settings for this operator yet')
            split = layout.split()

        elif self.op_prefs == 'npps':
            layout = self.layout
            split = layout.split()
            split.label(text='No individual settings for this operator yet')
            split = layout.split()

        elif self.op_prefs == 'nppl':
            layout = self.layout
            split = layout.split()
            split.label(text='No individual settings for this operator yet')
            split = layout.split()

        elif self.op_prefs == 'npsb':
            layout = self.layout
            split = layout.split()
            split.label(text='No individual settings for this operator yet')
            split = layout.split()

        elif self.op_prefs == 'nppd':
            layout = self.layout
            split = layout.split()
            split.label(text='NOTE: This operator is affected only by these individual settings')
            split = layout.split()
            split = layout.split()
            col = split.column()
            col.prop(self, "nppd_scale")
            col = split.column()
            col.prop(self, "nppd_suffix")
            split = layout.split()
            col = split.column()
            col.prop(self, "nppd_step")
            col = split.column()
            col.prop(self, "nppd_badge")
            split = layout.split()
            col = split.column()
            col.prop(self, "nppd_hold")
            col = split.column()
            col.prop(self, "nppd_gold")
            col = split.column()
            col.prop(self, "nppd_info")
            col = split.column()
            col.prop(self, "nppd_clip")
            split = layout.split()
            col = split.column()
            col.label(text='Line Main COLOR')
            col.prop(self, "nppd_col_line_main_DEF")
            if self.nppd_col_line_main_DEF == False:
                col.prop(self, "nppd_col_line_main")
            col = split.column()
            col.label(text='Line Shadow COLOR')
            col.prop(self, "nppd_col_line_shadow_DEF")
            if self.nppd_col_line_shadow_DEF == False:
                col.prop(self, "nppd_col_line_shadow")
            col = split.column()
            col.label(text='Numerical Main COLOR')
            col.prop(self, "nppd_col_num_main_DEF")
            if self.nppd_col_num_main_DEF == False:
                col.prop(self, "nppd_col_num_main")
            col = split.column()
            col.label(text='Numerical Shadow COLOR')
            col.prop(self, "nppd_col_num_shadow_DEF")
            if self.nppd_col_num_shadow_DEF == False:
                col.prop(self, "nppd_col_num_shadow")
            split = layout.split()
            col = split.column()
            col.prop(self, "nppd_stereo_cage")
            col = split.column()
            col.prop(self, "nppd_xyz_lines")
            col = split.column()
            col.prop(self, "nppd_xyz_distances")
            if self.nppd_xyz_distances == True:
                col = split.column()
                col.prop(self, "nppd_xyz_backdrop")
            else:
                col = split.column()


        elif self.op_prefs == 'npfp':
            layout = self.layout
            split = layout.split()
            col = split.column()
            col.prop(self, "npfp_point_markers")
            col = split.column()
            if self.npfp_point_markers is True:
                col.prop(self, "npfp_point_size")
            col = split.column()
            col.prop(self, "npfp_point_color_DEF")
            col = split.column()
            if self.npfp_point_color_DEF is False:
                col.prop(self, "npfp_point_color")
            split = layout.split()
            col = split.column()
            col.prop(self, "npfp_bevel")
            col = split.column()
            col.prop(self, "npfp_material")
            col = split.column()
            col.prop(self, "npfp_smooth")
            col = split.column()
            col.prop(self, "npfp_wire")

        elif self.op_prefs == 'nppm':
            layout = self.layout
            split = layout.split()
            split.label(text='No individual settings for this operator yet')
            split = layout.split()
            '''
        elif self.op_prefs == 'nppc':
            layout = self.layout
            split = layout.split()
            split.label(text='No individual settings for this operator yet')
            split = layout.split()

        elif self.op_prefs == 'nppi':
            layout = self.layout
            split = layout.split()
            split.label(text='No individual settings for this operator yet')
            split = layout.split()
            '''

        elif self.op_prefs == 'npfr':
            layout = self.layout
            split = layout.split()
            split.label(text='No individual settings for this operator yet')
            split = layout.split()
            '''
            col = split.column()
            col.prop(self, "npfr_dist_scale")
            col = split.column()
            col.prop(self, "npfr_suffix")
            split = layout.split()
            col = split.column()
            col.label(text='Line Main COLOR')
            col.prop(self, "npfr_col_line_main_DEF")
            if self.npfr_col_line_main_DEF == False:
                col.prop(self, "npfr_col_line_main")
            col = split.column()
            col.label(text='Line Shadow COLOR')
            col.prop(self, "npfr_col_line_shadow_DEF")
            if self.npfr_col_line_shadow_DEF == False:
                col.prop(self, "npfr_col_line_shadow")
            col = split.column()
            col.label(text='Numerical Main COLOR')
            col.prop(self, "npfr_col_num_main_DEF")
            if self.npfr_col_num_main_DEF == False:
                col.prop(self, "npfr_col_num_main")
            col = split.column()
            col.label(text='Numerical Shadow COLOR')
            col.prop(self, "npfr_col_num_shadow_DEF")
            if self.npfr_col_num_shadow_DEF == False:
                col.prop(self, "npfr_col_num_shadow")
            split = layout.split()
            col = split.column()
            col.prop(self, "npfr_badge")
            col = split.column()
            if self.npfr_badge == True:
                col.prop(self, "npfr_badge_size")
            col = split.column()
            col = split.column()
            '''
##########################################################################################

def register():
    bpy.utils.register_class(NP020Preferences)
    update_panel(None, bpy.context)
    # This registers all classes defined in this module *and its submodules*
    bpy.utils.register_module(__name__)

    # Hence, submodule register functions shall only add the few missing bits, but not try to re-register the classes.
    np_point_move.register()
    np_point_copy.register()
    np_point_instance.register()
    np_point_array.register()
    np_roto_move.register()
    np_point_scale.register()
    np_float_rectangle.register()
    np_float_box.register()
    np_point_align.register()
    np_point_distance.register()
    np_float_poly.register()
    np_shader_brush.register()

def unregister():
    bpy.utils.unregister_class(NP020Preferences)

    bpy.utils.unregister_module(__name__)
    #bpy.utils.unregister_class(NP020PointMove)
    np_point_move.unregister()
    np_point_copy.unregister()
    np_point_instance.unregister()
    np_point_array.unregister()
    np_roto_move.unregister()
    np_point_scale.unregister()
    np_float_rectangle.unregister()
    np_float_box.unregister()
    np_point_align.unregister()
    np_point_distance.unregister()
    np_float_poly.unregister()
    np_shader_brush.unregister()

if __name__ == '__main__':
    register()

