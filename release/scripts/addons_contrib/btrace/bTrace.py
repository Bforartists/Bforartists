#BEGIN GPL LICENSE BLOCK

#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software Foundation,
#Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

#END GPL LICENCE BLOCK

bl_info = {
    "name": "Btrace",
    "author": "liero, crazycourier, Atom, Meta-Androcto, MacKracken",
    "version": (1, 1, ),
    "blender": (2, 71, 0),
    "location": "View3D > Toolshelf > Addons Tab",
    "description": "Tools for converting/animating objects/particles into curves",
    "warning": "Still under development, bug reports appreciated",
    "wiki_url": "",
    "tracker_url": "https://developer.blender.org/T29563",
    "category": "Add Curve"}


#### TO DO LIST ####
### [   ]  Add more options to curve radius/modulation plus cyclic/connect curve option

import bpy
import selection_utils
from bpy.props import FloatProperty, EnumProperty, IntProperty, BoolProperty, FloatVectorProperty


def deselect_others(ob, context):
    """For tool menu select, deselects others if one selected"""
    selected = addTracerObjectPanel.selected
    ob[selected] = False
    keys = [key for key in ob.keys() if ob[key]]  # all the True keys
    if len(keys) <= 0:
        ob[selected] = True  # reselect
        return None
    for key in keys:
        addTracerObjectPanel.selected = key
        ob[key] = True


# Class for properties panel
class TracerPropertiesMenu(bpy.types.PropertyGroup):
    """Toolbar show/hide booleans for tool options"""
    tool_objectTrace = BoolProperty(name="Object Trace", default=False, description="Trace selected mesh object with a curve", update=deselect_others)
    tool_objectsConnect = BoolProperty(name="Objects Connect", default=False, description="Connect objects with a curve controlled by hooks", update=deselect_others)
    tool_particleTrace = BoolProperty(name="Particle Trace", default=False, description="Trace particle path with a  curve", update=deselect_others)
    tool_meshFollow = BoolProperty(name="Mesh Follow", default=False, description="Follow selection items on animated mesh object", update=deselect_others)
    tool_particleConnect = BoolProperty(name="Particle Connect", default=False, description="Connect particles with a curves and animated over particle lifetime", update=deselect_others)
    tool_growCurve = BoolProperty(name="Grow Curve", default=False, description="Animate curve bevel over time by keyframing points radius", update=deselect_others)
    tool_handwrite = BoolProperty(name="Handwriting", default=False, description="Create and Animate curve using the grease pencil", update=deselect_others)
    tool_fcurve = BoolProperty(name="F-Curve Noise", default=False, description="Add F-Curve noise to selected objects", update=deselect_others)
    tool_colorblender = BoolProperty(name="Color Blender", default=False, description="Add F-Curve noise to selected objects", update=deselect_others)


# Class to define properties
class TracerProperties(bpy.types.PropertyGroup):
    """Options for tools"""
    curve_spline = EnumProperty(name="Spline", items=(("POLY", "Poly", "Use Poly spline type"),  ("NURBS", "Nurbs", "Use Nurbs spline type"), ("BEZIER", "Bezier", "Use Bezier spline type")), description="Choose which type of spline to use when curve is created", default="BEZIER")
    curve_handle = EnumProperty(name="Handle", items=(("ALIGNED", "Aligned", "Use Aligned Handle Type"), ("AUTOMATIC", "Automatic", "Use Auto Handle Type"), ("FREE_ALIGN", "Free Align", "Use Free Handle Type"), ("VECTOR", "Vector", "Use Vector Handle Type")), description="Choose which type of handle to use when curve is created",  default="VECTOR")
    curve_resolution = IntProperty(name="Bevel Resolution", min=1, max=32, default=4, description="Adjust the Bevel resolution")
    curve_depth = FloatProperty(name="Bevel Depth", min=0.0, max=100.0, default=0.1, description="Adjust the Bevel depth")
    curve_u = IntProperty(name="Resolution U", min=0, max=64, default=12, description="Adjust the Surface resolution")
    curve_join = BoolProperty(name="Join Curves", default=False, description="Join all the curves after they have been created")
    curve_smooth = BoolProperty(name="Smooth", default=True, description="Render curve smooth")
    # Option to Duplicate Mesh
    object_duplicate = BoolProperty(name="Apply to Copy", default=False, description="Apply curve to a copy of object")
    # Distort Mesh options
    distort_modscale = IntProperty(name="Modulation Scale", min=0, max=50, default=2, description="Add a scale to modulate the curve at random points, set to 0 to disable")
    distort_noise = FloatProperty(name="Mesh Noise", min=0.0, max=50.0, default=0.00, description="Adjust noise added to mesh before adding curve")
    # Particle Options
    particle_step = IntProperty(name="Step Size", min=1, max=50, default=5, description="Sample one every this number of frames")
    particle_auto = BoolProperty(name='Auto Frame Range', default=True, description='Calculate Frame Range from particles life')
    particle_f_start = IntProperty(name='Start Frame', min=1, max=5000, default=1, description='Start frame')
    particle_f_end = IntProperty(name='End Frame', min=1, max=5000, default=250, description='End frame')
    # F-Curve Modifier Properties
    fcnoise_rot = BoolProperty(name="Rotation", default=False, description="Affect Rotation")
    fcnoise_loc = BoolProperty(name="Location", default=True, description="Affect Location")
    fcnoise_scale = BoolProperty(name="Scale", default=False, description="Affect Scale")
    fcnoise_amp = IntProperty(name="Amp", min=1, max=500, default=5, description="Adjust the amplitude")
    fcnoise_timescale = FloatProperty(name="Time Scale", min=1, max=500, default=50, description="Adjust the time scale")
    fcnoise_key = BoolProperty(name="Add Keyframe", default=True, description="Keyframe is needed for tool, this adds a LocRotScale keyframe")
    show_curve_settings = BoolProperty(name="Curve Settings", default=False, description="Change the curve settings for the created curve")
    material_settings = BoolProperty(name="Material Settings", default=False, description="Change the material settings for the created curve")
    particle_settings = BoolProperty(name="Particle Settings", default=False, description="Show the settings for the created curve")
    animation_settings = BoolProperty(name="Animation Settings", default=False, description="Show the settings for the Animations")
    distort_curve = BoolProperty(name="Add Distortion", default=False, description="Set options to distort the final curve")
    connect_noise = BoolProperty(name="F-Curve Noise", default=False, description="Adds F-Curve Noise Modifier to selected objects")
    settings_objectTrace = BoolProperty(name="Object Trace Settings", default=False, description="Trace selected mesh object with a curve")
    settings_objectsConnect = BoolProperty(name="Objects Connect Settings", default=False, description="Connect objects with a curve controlled by hooks")
    settings_objectTrace = BoolProperty(name="Object Trace Settings", default=False, description="Trace selected mesh object with a curve")
    respect_order = BoolProperty(name="Order", default=False, description="Remember order objects were selected")
    settings_particleTrace = BoolProperty(name="Particle Trace Settings", default=False, description="Trace particle path with a  curve")
    settings_particleConnect = BoolProperty(name="Particle Connect Settings", default=False, description="Connect particles with a curves and animated over particle lifetime")
    settings_growCurve = BoolProperty(name="Grow Curve Settings", default=False, description="Animate curve bevel over time by keyframing points radius")
    settings_fcurve = BoolProperty(name="F-Curve Settings", default=False, description="F-Curve Settings")
    settings_toggle = BoolProperty(name="Settings", default=False, description="Toggle Settings")
    # Animation Options
    anim_auto = BoolProperty(name='Auto Frame Range', default=True, description='Automatically calculate Frame Range')
    anim_f_start = IntProperty(name='Start', min=1, max=2500, default=1, description='Start frame / Hidden object')
    anim_length = IntProperty(name='Duration', min=1, soft_max=1000, max=2500, default=100, description='Animation Length')
    anim_f_fade = IntProperty(name='Fade After', min=0, soft_max=250, max=2500, default=10, description='Fade after this frames / Zero means no fade')
    anim_delay = IntProperty(name='Grow', min=0, max=50, default=5, description='Frames it takes a point to grow')
    anim_tails = BoolProperty(name='Tails on endpoints', default=True, description='Set radius to zero for open splines endpoints')
    anim_keepr = BoolProperty(name='Keep Radius', default=True, description='Try to keep radius data from original curve')
    animate = BoolProperty(name="Animate Result", default=False, description='Animate the final curve objects')
    # Convert to Curve options
    convert_conti = BoolProperty(name='Continuous', default=True, description='Create a continuous curve using verts from mesh')
    convert_everyedge = BoolProperty(name='Every Edge', default=False, description='Create a curve from all verts in a mesh')
    convert_edgetype = EnumProperty(name="Edge Type for Curves",
        items=(("CONTI", "Continuous", "Create a continuous curve using verts from mesh"),  ("EDGEALL", "All Edges", "Create a curve from every edge in a mesh")),
        description="Choose which type of spline to use when curve is created", default="CONTI")
    convert_joinbefore = BoolProperty(name="Join objects before convert", default=False, description='Join all selected mesh to one object before converting to mesh')
    # Mesh Follow Options
    fol_edge_select = BoolProperty(name='Edge', default=False, description='Grow from edges')
    fol_vert_select = BoolProperty(name='Vertex', default=False, description='Grow from verts')
    fol_face_select = BoolProperty(name='Face', default=True, description='Grow from faces')
    fol_mesh_type = EnumProperty(name='Mesh type', default='VERTS', description='Mesh feature to draw cruves from', items=(
        ("VERTS", "Verts", "Draw from Verts"), ("EDGES", "Edges", "Draw from Edges"), ("FACES", "Faces", "Draw from Faces"), ("OBJECT", "Object", "Draw from Object origin")))
    fol_start_frame = IntProperty(name="Start Frame", min=1, max=2500, default=1, description="Start frame for range to trace")
    fol_end_frame = IntProperty(name="End Frame", min=1, max=2500, default=250, description="End frame for range to trace")
    fol_perc_verts = FloatProperty(name="Reduce selection by", min=0.001, max=1.000, default=0.5, description="percentage of total verts to trace")
    fol_sel_option = EnumProperty(name="Selection type", description="Choose which objects to follow", default="RANDOM", items=(
        ("RANDOM", "Random", "Follow Random items"),  ("CUSTOM", "Custom Select", "Follow selected items"), ("ALL", "All", "Follow all items")))
    trace_mat_color = FloatVectorProperty(name="Material Color", description="Choose material color", min=0, max=1, default=(0.0,0.3,0.6), subtype="COLOR")
    trace_mat_random = BoolProperty(name="Random Color", default=False, description='Make the material colors random')

    # Material custom Properties properties
    mat_simple_adv_toggle = EnumProperty(name="Material Options", items=(("SIMPLE", "Simple", "Show Simple Material Options"), ("ADVANCED", "Advanced", "Show Advanced Material Options")), description="Choose which Material Options to show", default="SIMPLE")
    mat_run_color_blender = BoolProperty(name="Run Color Blender", default=False, description="Generate colors from a color scheme")
    mmColors = bpy.props.EnumProperty(
        items=(("RANDOM", "Random", "Use random colors"),
                ("CUSTOM", "Custom", "Use custom colors"),
                ("BW", "Black/White", "Use Black and White"),
                ("BRIGHT", "Bright Colors", "Use Bright colors"),
                ("EARTH", "Earth", "Use Earth colors"),
                ("GREENBLUE", "Green to Blue", "Use Green to Blue colors")),
        description="Choose which type of colors the materials uses",
        default="BRIGHT",
        name="Define a color palette")
    # Custom property for how many keyframes to skip
    mmSkip = bpy.props.IntProperty(name="frames", min=1, max=500, default=20, description="Number of frames between each keyframes")
    # Custom property to enable/disable random order for the
    mmBoolRandom = bpy.props.BoolProperty(name="Random Order", default=False, description="Randomize the order of the colors")
    # Custom Color properties
    mmColor1 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.8, 0.8, 0.8), description="Custom Color 1", subtype="COLOR")
    mmColor2 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.8, 0.8, 0.3), description="Custom Color 2", subtype="COLOR")
    mmColor3 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.8, 0.5, 0.6), description="Custom Color 3", subtype="COLOR")
    mmColor4 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.2, 0.8, 0.289), description="Custom Color 4", subtype="COLOR")
    mmColor5 = bpy.props.FloatVectorProperty(min=0, max=1, default=(1.0, 0.348, 0.8), description="Custom Color 5", subtype="COLOR")
    mmColor6 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.4, 0.67, 0.8), description="Custom Color 6", subtype="COLOR")
    mmColor7 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.66, 0.88, 0.8), description="Custom Color 7", subtype="COLOR")
    mmColor8 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.8, 0.38, 0.22), description="Custom Color 8", subtype="COLOR")
    # BW Color properties
    bwColor1 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.0,0.0,0.0), description="Black/White Color 1", subtype="COLOR")
    bwColor2 = bpy.props.FloatVectorProperty(min=0, max=1, default=(1.0,1.0,1.0), description="Black/White Color 2", subtype="COLOR")
    # Bright Color properties
    brightColor1 = bpy.props.FloatVectorProperty(min=0, max=1, default=(1.0, 0.0, 0.75), description="Bright Color 1", subtype="COLOR")
    brightColor2 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.0,1.0,1.0), description="Bright Color 2", subtype="COLOR")
    brightColor3 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.0,1.0,0.0), description="Bright Color 3", subtype="COLOR")
    brightColor4 = bpy.props.FloatVectorProperty(min=0, max=1, default=(1.0,1.0,0.0), description="Bright Color 4", subtype="COLOR")
    # Earth Color Properties
    earthColor1 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.068, 0.019, 0.014), description="Earth Color 1", subtype="COLOR")
    earthColor2 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.089, 0.060, 0.047), description="Earth Color 2", subtype="COLOR")
    earthColor3 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.188, 0.168, 0.066), description="Earth Color 3", subtype="COLOR")
    earthColor4 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.445, 0.296, 0.065), description="Earth Color 4", subtype="COLOR")
    earthColor5 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.745, 0.332, 0.065), description="Earth Color 5", subtype="COLOR")
    # Green to Blue Color properties
    greenblueColor1 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.296, 0.445, 0.074), description="Green/Blue Color 1", subtype="COLOR")
    greenblueColor2 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.651, 1.0, 0.223), description="Green/Blue Color 2", subtype="COLOR")
    greenblueColor3 = bpy.props.FloatVectorProperty(min=0, max=1, default=(0.037, 0.047, 0.084), description="Green/Blue Color 3", subtype="COLOR")


############################
## Draw Brush panel in Toolbar
############################
class addTracerObjectPanel(bpy.types.Panel):
    bl_label = "Btrace: Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = 'objectmode'
    selected = "tool_objectTrace"
    bl_category = 'Create'
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self, context):
        layout = self.layout
        Btrace = bpy.context.window_manager.curve_tracer
        btracemenu = props = bpy.context.window_manager.btrace_menu
        obj = bpy.context.object


        ############################
        ## Color Blender Panel options
        ############################
        def color_blender():
            """Buttons for Color Blender"""
            row = box.row()
            row.label("Color palette")
            row.prop(Btrace, 'mmColors', text="")
            # Show Custom Colors if selected
            if Btrace.mmColors == 'CUSTOM':
                row = box.row(align=True)
                row.prop(Btrace, 'mmColor1', text="")
                row.prop(Btrace, 'mmColor2', text="")
                row.prop(Btrace, 'mmColor3', text="")
                row.prop(Btrace, 'mmColor4', text="")
                row.prop(Btrace, 'mmColor5', text="")
                row.prop(Btrace, 'mmColor6', text="")
                row.prop(Btrace, 'mmColor7', text="")
                row.prop(Btrace, 'mmColor8', text="")
            # Show Earth Colors
            elif Btrace.mmColors == 'BW':
                row = box.row(align=True)
                row.prop(Btrace, 'bwColor1', text="")
                row.prop(Btrace, 'bwColor2', text="")
            # Show Earth Colors
            elif Btrace.mmColors == 'BRIGHT':
                row = box.row(align=True)
                row.prop(Btrace, 'brightColor1', text="")
                row.prop(Btrace, 'brightColor2', text="")
                row.prop(Btrace, 'brightColor3', text="")
                row.prop(Btrace, 'brightColor4', text="")
            # Show Earth Colors
            elif Btrace.mmColors == 'EARTH':
                row = box.row(align=True)
                row.prop(Btrace, 'earthColor1', text="")
                row.prop(Btrace, 'earthColor2', text="")
                row.prop(Btrace, 'earthColor3', text="")
                row.prop(Btrace, 'earthColor4', text="")
                row.prop(Btrace, 'earthColor5', text="")
            # Show Earth Colors
            elif Btrace.mmColors == 'GREENBLUE':
                row = box.row(align=True)
                row.prop(Btrace, 'greenblueColor1', text="")
                row.prop(Btrace, 'greenblueColor2', text="")
                row.prop(Btrace, 'greenblueColor3', text="")
            elif Btrace.mmColors == 'RANDOM':
                row = box.row()

        ############################
        ## Curve Panel options
        ############################
        def curve_settings():
            """Button for curve options"""
            row = self.layout.row()
            row = box.row(align=True)

            row.prop(Btrace, 'show_curve_settings', icon='CURVE_BEZCURVE', text="Curve Settings")
            row.prop(Btrace, 'material_settings', icon='MATERIAL_DATA', text="Material Settings")
            if Btrace.material_settings:
                row = box.row()
                row.label(text="Material Settings", icon='COLOR')
                row = box.row()
                row.prop(Btrace, "trace_mat_random")
                if not Btrace.trace_mat_random:
                    row = box.row()
                    row.prop(Btrace, "trace_mat_color", text="")
                else:
                    row.prop(Btrace, "mat_run_color_blender")
                    if Btrace.mat_run_color_blender:
                        row = box.row()
                        row.operator("object.colorblenderclear", text="Reset Material Keyframes", icon="KEY_DEHLT")
                        row.prop(Btrace, 'mmSkip', text="Keyframe every")

                    color_blender()
                row = box.row()
            if Btrace.show_curve_settings:
                #if  or btracemenu.tool_handwrite:
                if len(bpy.context.selected_objects) > 0 and obj.type == 'CURVE': # selected curve options
                    col = box.column(align=True)
                    col.label(text="Edit Curves for", icon='CURVE_BEZCURVE')
                    col.label(text="Selected Curve Bevel Options")
                    row = col.row(align=True)
                    row.prop(obj.data, 'bevel_depth', text="Depth")
                    row.prop(obj.data, 'bevel_resolution', text="Resolution")
                    row = col.row(align=True)
                    row.prop(obj.data, 'resolution_u')
                else: # For new curve
                    box.label(text="New Curve Settings", icon='CURVE_BEZCURVE')
                    box.prop(Btrace, "curve_spline")
                    box.prop(Btrace, "curve_handle")
                    box.label(text="Bevel Options")
                    col = box.column(align=True)
                    row = col.row(align=True)
                    row.prop(Btrace, "curve_depth", text="Depth")
                    row.prop(Btrace, "curve_resolution", text="Resolution")
                    row = col.row(align=True)
                    row.prop(Btrace, "curve_u")

        ############################
        ## Grow Animation Panel options
        ############################
        def add_grow():
            """Button for grow animation option"""
            row = box.row()
            row.label(text="Animate Final Curve")
            row = box.row()
            row.prop(Btrace, "animate", text="Add Grow Curve Animation", icon="META_BALL")
            row.label("")
            if Btrace.animate:
                box.label(text='Frame Animation Settings:', icon="META_BALL")
                col = box.column(align=True)
                col.prop(Btrace, 'anim_auto')
                if not Btrace.anim_auto:
                    row = col.row(align=True)
                    row.prop(Btrace, 'anim_f_start')
                    row.prop(Btrace, 'anim_length')
                row = col.row(align=True)
                row.prop(Btrace, 'anim_delay')
                row.prop(Btrace, 'anim_f_fade')

                box.label(text='Additional Settings')
                row = box.row()
                row.prop(Btrace, 'anim_tails')
                row.prop(Btrace, 'anim_keepr')

        ##################################################################
        ## Start Btrace Panel
        ##################################################################
        col = self.layout.column(align=True)
        #col.label(text="Trace Tools")
        row = col.row()
        row.prop(btracemenu, "tool_objectTrace", text="Ojbect Trace", icon="FORCE_MAGNETIC")
        row.prop(btracemenu, "tool_objectsConnect", text="Object Connect", icon="OUTLINER_OB_EMPTY")
        row = col.row()
        row.prop(btracemenu, "tool_meshFollow", text="Mesh Follow", icon="DRIVER")
        row.prop(btracemenu, "tool_handwrite", text="Handwriting", icon='BRUSH_DATA')
        row = col.row()
        row.prop(btracemenu, "tool_particleTrace", icon="PARTICLES", text="Particle Trace")
        row.prop(btracemenu, "tool_particleConnect", icon="MOD_PARTICLES", text="Particle Connect")
        row = layout.row()
        col = layout.column(align=True)
        row = col.row()
        row.prop(btracemenu, "tool_growCurve", icon="META_BALL", text="Grow Animation")
        row.prop(btracemenu, "tool_fcurve", text="Fcurve Noise", icon='RNDCURVE')
        row = col.row()
        row.prop(btracemenu, "tool_colorblender", text="Color Blender", icon="COLOR")
        row.label(text="")
        row = layout.row()

        ##########################
        ## Start  Object Tools
        ##########################
        sel = bpy.context.selected_objects
        ############################
        ### Object Trace
        ############################
        if btracemenu.tool_objectTrace:
            row = layout.row()
            row.label(text="  Trace Tool:", icon="FORCE_CURVE")
            box = self.layout.box()
            row = box.row()
            row.label(text="Object Trace", icon="FORCE_MAGNETIC")
            row.operator("object.btobjecttrace", text="Run!", icon="PLAY")
            row = box.row()
            row.prop(Btrace, "settings_toggle", icon='MODIFIER', text='Settings')
            myselected = "Selected %d" % len(bpy.context.selected_objects)
            row.label(text=myselected)
            if Btrace.settings_toggle:
                row = box.row()
                row.label(text='Edge Draw Method')
                row = box.row(align=True)
                row.prop(Btrace, 'convert_edgetype')
                box.prop(Btrace, "object_duplicate")
                if len(sel) > 1:
                    box.prop(Btrace, 'convert_joinbefore')
                else:
                    Btrace.convert_joinbefore = False
                row = box.row()
                row.prop(Btrace, "distort_curve")
                if Btrace.distort_curve:
                    col = box.column(align=True)
                    col.prop(Btrace, "distort_modscale")
                    col.prop(Btrace, "distort_noise")
                row = box.row()
                curve_settings()  # Show Curve/material settings
                add_grow()  # Grow settings here

        ############################
        ### Objects Connect
        ############################
        if btracemenu.tool_objectsConnect:
            row = layout.row()
            row.label(text="  Trace Tool:", icon="FORCE_CURVE")
            box = self.layout.box()
            row = box.row()
            row.label(text="Objects Connect", icon="OUTLINER_OB_EMPTY")
            row.operator("object.btobjectsconnect", text="Run!", icon="PLAY")
            row = box.row()
            row.prop(Btrace, "settings_toggle", icon='MODIFIER', text='Settings')
            row.label(text="")
            if Btrace.settings_toggle:
                row = box.row()
                row.prop(Btrace, "respect_order", text="Selection Options")
                if Btrace.respect_order:
                    box.operator("object.select_order", text="Click to start order selection", icon='UV_SYNC_SELECT')
                row = box.row()
                row.prop(Btrace, "connect_noise", text="Add F-Curve Noise")
                if Btrace.connect_noise:
                    row = box.row()
                    row.label(text="F-Curve Noise", icon='RNDCURVE')
                    row = box.row(align=True)
                    row.prop(Btrace, "fcnoise_rot")
                    row.prop(Btrace, "fcnoise_loc")
                    row.prop(Btrace, "fcnoise_scale")
                    col = box.column(align=True)
                    col.prop(Btrace, "fcnoise_amp")
                    col.prop(Btrace, "fcnoise_timescale")
                    box.prop(Btrace, "fcnoise_key")
                curve_settings()  # Show Curve/material settings
                add_grow()  # Grow settings here

        ############################
        ### Mesh Follow
        ############################
        if btracemenu.tool_meshFollow:
            row = layout.row()
            row.label(text="  Trace Tool:", icon="FORCE_CURVE")
            box = self.layout.box()
            row = box.row()
            row.label(text="Mesh Follow", icon="DRIVER")
            row.operator("object.btmeshfollow", text="Run!", icon="PLAY")
            row = box.row()
            if Btrace.fol_mesh_type == 'OBJECT':
                a, b = "Trace Object", "SNAP_VOLUME"
            if Btrace.fol_mesh_type == 'VERTS':
                a, b = "Trace Verts", "SNAP_VERTEX"
            if Btrace.fol_mesh_type == 'EDGES':
                a, b = "Trace Edges", "SNAP_EDGE"
            if Btrace.fol_mesh_type == 'FACES':
               a, b = "Trace Faces", "SNAP_FACE"
            row.prop(Btrace, "settings_toggle", icon='MODIFIER', text='Settings')
            row.label(text=a, icon=b)
            if Btrace.settings_toggle:
                col = box.column(align=True)
                row = col.row(align=True)
                row.prop(Btrace, "fol_mesh_type", expand=True)
                row = col.row(align=True)
                if Btrace.fol_mesh_type != 'OBJECT':
                    row.prop(Btrace, "fol_sel_option", expand=True)
                    row = box.row()
                    if Btrace.fol_sel_option == 'RANDOM':
                        row.label("Random Select of Total")
                        row.prop(Btrace, "fol_perc_verts", text="%")
                    if Btrace.fol_sel_option == 'CUSTOM':
                        row.label("Choose selection in Edit Mode")
                    if Btrace.fol_sel_option == 'ALL':
                        row.label("Select All items")
                col = box.column(align=True)
                col.label("Time Options", icon="TIME")
                col.prop(Btrace, "particle_step")
                row = col.row(align=True)
                row.prop(Btrace, "fol_start_frame")
                row.prop(Btrace, "fol_end_frame")
                curve_settings()  # Show Curve/material settings
                add_grow()  # Grow settings here

         ############################
        ### Handwriting Tools
        ############################
        if btracemenu.tool_handwrite:
            row = layout.row()
            row.label(text="  Trace Tool:", icon="FORCE_CURVE")
            box = self.layout.box()
            row = box.row()
            row.label(text='Handwriting', icon='BRUSH_DATA')
            row.operator("curve.btwriting", text="Run!", icon='PLAY')
            row = box.row()
            row = box.row()
            row.label(text='Grease Pencil Writing Tools')
            col = box.column(align=True)
            row = col.row(align=True)
            row.operator("gpencil.draw", text="Draw", icon='BRUSH_DATA').mode = 'DRAW'
            row.operator("gpencil.draw", text="Poly", icon='VPAINT_HLT').mode = 'DRAW_POLY'
            row = col.row(align=True)
            row.operator("gpencil.draw", text="Line", icon='ZOOMOUT').mode = 'DRAW_STRAIGHT'
            row.operator("gpencil.draw", text="Erase", icon='TPAINT_HLT').mode = 'ERASER'
            row = box.row()
            row.operator("gpencil.data_unlink", text="Delete Grease Pencil Layer", icon="CANCEL")
            row = box.row()
            curve_settings()  # Show Curve/material settings
            add_grow()  # Grow settings here

        ############################
        ### Particle Trace
        ############################
        if btracemenu.tool_particleTrace:
            row = layout.row()
            row.label(text="  Trace Tool:", icon="FORCE_CURVE")
            box = self.layout.box()
            row = box.row()
            row.label(text="Particle Trace", icon="PARTICLES")
            row.operator("particles.particletrace", text="Run!", icon="PLAY")
            row = box.row()
            row.prop(Btrace, "settings_toggle", icon='MODIFIER', text='Settings')
            row.label(text="")
            if Btrace.settings_toggle:
                box.prop(Btrace, "particle_step")
                row = box.row()
                row.prop(Btrace, "curve_join")
                curve_settings()  # Show Curve/material settings
                add_grow()  # Grow settings here

        ############################
        ### Connect Particles
        ############################
        if btracemenu.tool_particleConnect:
            row = layout.row()
            row.label(text="  Trace Tool:", icon="FORCE_CURVE")
            box = self.layout.box()
            row = box.row()
            row.label(text='Particle Connect', icon='MOD_PARTICLES')
            row.operator("particles.connect", icon="PLAY", text='Run!')
            row = box.row()
            row.prop(Btrace, "settings_toggle", icon='MODIFIER', text='Settings')
            row.label(text="")
            if Btrace.settings_toggle:
                box.prop(Btrace, "particle_step")
                row = box.row()
                row.prop(Btrace, 'particle_auto')
                if not Btrace.particle_auto:
                    row = box.row(align=True)
                    row.prop(Btrace, 'particle_f_start')
                    row.prop(Btrace, 'particle_f_end')
                curve_settings()  # Show Curve/material settings
                add_grow()  # Grow settings here

        #######################
        #### Grow Animation ####
        #######################
        if btracemenu.tool_growCurve:
            row = layout.row()
            row.label(text="  Curve Tool:", icon="OUTLINER_OB_CURVE")
            box = self.layout.box()
            row = box.row()
            row.label(text="Grow Curve", icon="META_BALL")
            row.operator('curve.btgrow', text='Run!', icon='PLAY')
            row = box.row()
            row.prop(Btrace, "settings_toggle", icon='MODIFIER', text='Settings')
            row.operator('object.btreset',  icon='KEY_DEHLT')
            if Btrace.settings_toggle:
                box.label(text='Frame Animation Settings:')
                col = box.column(align=True)
                col.prop(Btrace, 'anim_auto')
                if not Btrace.anim_auto:
                    row = col.row(align=True)
                    row.prop(Btrace, 'anim_f_start')
                    row.prop(Btrace, 'anim_length')
                row = col.row(align=True)
                row.prop(Btrace, 'anim_delay')
                row.prop(Btrace, 'anim_f_fade')

                box.label(text='Additional Settings')
                row = box.row()
                row.prop(Btrace, 'anim_tails')
                row.prop(Btrace, 'anim_keepr')

        #######################
        #### F-Curve Noise Curve ####
        #######################
        if btracemenu.tool_fcurve:
            row = layout.row()
            row.label(text="  Curve Tool:", icon="OUTLINER_OB_CURVE")
            box = self.layout.box()
            row = box.row()
            row.label(text="F-Curve Noise", icon='RNDCURVE')
            row.operator("object.btfcnoise", icon='PLAY', text="Run!")
            row = box.row()
            row.prop(Btrace, "settings_toggle", icon='MODIFIER', text='Settings')
            row.operator('object.btreset',  icon='KEY_DEHLT')
            if Btrace.settings_toggle:
                row = box.row(align=True)
                row.prop(Btrace, "fcnoise_rot")
                row.prop(Btrace, "fcnoise_loc")
                row.prop(Btrace, "fcnoise_scale")
                col = box.column(align=True)
                col.prop(Btrace, "fcnoise_amp")
                col.prop(Btrace, "fcnoise_timescale")
                box.prop(Btrace, "fcnoise_key")

        #######################
        #### Color Blender ####
        #######################
        if btracemenu.tool_colorblender:
            row = layout.row()
            row.label(text="  Curve/Object Tool:", icon="OUTLINER_OB_CURVE")
            box = self.layout.box()
            row = box.row()
            row.label(text="Color Blender", icon="COLOR")
            row.operator("object.colorblender", icon='PLAY', text="Run!")
            row = box.row()
            row.operator("object.colorblenderclear", text="Reset Keyframes", icon="KEY_DEHLT")
            row.prop(Btrace, 'mmSkip', text="Keyframe every")
            color_blender()

###### END PANEL ##############
###############################


################## ################## ################## ############
## Object Trace
## creates a curve with a modulated radius connecting points of a mesh
################## ################## ################## ############

class OBJECT_OT_objecttrace(bpy.types.Operator):
    bl_idname = "object.btobjecttrace"
    bl_label = "Btrace: Object Trace"
    bl_description = "Trace selected mesh object with a curve with the option to animate"
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type in {'MESH', 'FONT'})

    def invoke(self, context, event):
        import bpy

        # Run through each selected object and convert to to a curved object
        brushObj = bpy.context.selected_objects
        Btrace = bpy.context.window_manager.curve_tracer
        # Duplicate Mesh
        if Btrace.object_duplicate:
            bpy.ops.object.duplicate_move()
            brushObj = bpy.context.selected_objects
        # Join Mesh
        if Btrace.convert_joinbefore:
            if len(brushObj) > 1:  # Only run if multiple objects selected
                bpy.ops.object.join()
                brushObj = bpy.context.selected_objects

        for i in brushObj:
            bpy.context.scene.objects.active = i
            if i and i.type != 'CURVE':
                bpy.ops.object.btconvertcurve()
                addtracemat(bpy.context.object.data)
            if Btrace.animate:
                bpy.ops.curve.btgrow()
        return {'FINISHED'}


################## ################## ################## ############
## Objects Connect
## connect selected objects with a curve + hooks to each node
## possible handle types: 'FREE' 'AUTO' 'VECTOR' 'ALIGNED'
################## ################## ################## ############

class OBJECT_OT_objectconnect(bpy.types.Operator):
    bl_idname = "object.btobjectsconnect"
    bl_label = "Btrace: Objects Connect"
    bl_description = "Connect selected objects with a curve and add hooks to each node"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(bpy.context.selected_objects) > 1

    def invoke(self, context, event):
        import bpy, selection_utils
        list = []
        Btrace = bpy.context.window_manager.curve_tracer
        curve_handle = Btrace.curve_handle
        if curve_handle == 'AUTOMATIC':  # hackish because of naming conflict in api
            curve_handle = 'AUTO'
        # Check if Btrace group exists, if not create
        bgroup = bpy.data.groups.keys()
        if 'Btrace' not in bgroup:
            bpy.ops.group.create(name="Btrace")
        #  check if noise
        if Btrace.connect_noise:
            bpy.ops.object.btfcnoise()
        # check if respect order is checked, create list of objects
        if Btrace.respect_order == True:
            selobnames = selection_utils.selected
            obnames = []
            for ob in selobnames:
                obnames.append(bpy.data.objects[ob])
        else:
            obnames = bpy.context.selected_objects  # No selection order

        for a in obnames:
            list.append(a)
            a.select = False

        # trace the origins
        tracer = bpy.data.curves.new('tracer', 'CURVE')
        tracer.dimensions = '3D'
        spline = tracer.splines.new('BEZIER')
        spline.bezier_points.add(len(list) - 1)
        curve = bpy.data.objects.new('curve', tracer)
        bpy.context.scene.objects.link(curve)

        # render ready curve
        tracer.resolution_u = Btrace.curve_u
        tracer.bevel_resolution = Btrace.curve_resolution  # Set bevel resolution from Panel options
        tracer.fill_mode = 'FULL'
        tracer.bevel_depth = Btrace.curve_depth  # Set bevel depth from Panel options

        # move nodes to objects
        for i in range(len(list)):
            p = spline.bezier_points[i]
            p.co = list[i].location
            p.handle_right_type = curve_handle
            p.handle_left_type = curve_handle

        bpy.context.scene.objects.active = curve
        bpy.ops.object.mode_set(mode='OBJECT')

        # place hooks
        for i in range(len(list)):
            list[i].select = True
            curve.data.splines[0].bezier_points[i].select_control_point = True
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.hook_add_selob()
            bpy.ops.object.mode_set(mode='OBJECT')
            curve.data.splines[0].bezier_points[i].select_control_point = False
            list[i].select = False

        bpy.ops.object.select_all(action='DESELECT')
        curve.select = True # selected curve after it's created
        addtracemat(bpy.context.object.data) # Add material
        if Btrace.animate: # Add Curve Grow it?
            bpy.ops.curve.btgrow()
        bpy.ops.object.group_link(group="Btrace") # add to Btrace group
        if Btrace.animate:
            bpy.ops.curve.btgrow() # Add grow curve
        return {'FINISHED'}


################## ################## ################## ############
## Particle Trace
## creates a curve from each particle of a system
################## ################## ################## ############
def  curvetracer(curvename, splinename):
    Btrace = bpy.context.window_manager.curve_tracer
    tracer = bpy.data.curves.new(splinename, 'CURVE')
    tracer.dimensions = '3D'
    curve = bpy.data.objects.new(curvename, tracer)
    bpy.context.scene.objects.link(curve)
    try:
        tracer.fill_mode = 'FULL'
    except:
        tracer.use_fill_front = tracer.use_fill_back = False
    tracer.bevel_resolution = Btrace.curve_resolution
    tracer.bevel_depth = Btrace.curve_depth
    tracer.resolution_u = Btrace.curve_u
    return tracer, curve


class OBJECT_OT_particletrace(bpy.types.Operator):
    bl_idname = "particles.particletrace"
    bl_label = "Btrace: Particle Trace"
    bl_description = "Creates a curve from each particle of a system. Keeping particle amount under 250 will make this run faster"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (bpy.context.object and bpy.context.object.particle_systems)

    def execute(self, context):
        Btrace = bpy.context.window_manager.curve_tracer
        particle_step = Btrace.particle_step    # step size in frames
        obj = bpy.context.object
        ps = obj.particle_systems.active
        curvelist = []
        curve_handle = Btrace.curve_handle
        if curve_handle == 'AUTOMATIC':  # hackish naming conflict
            curve_handle = 'AUTO'
        if curve_handle == 'FREE_ALIGN':  # hackish naming conflict
            curve_handle = 'FREE'

        # Check if Btrace group exists, if not create
        bgroup = bpy.data.groups.keys()
        if 'Btrace' not in bgroup:
            bpy.ops.group.create(name="Btrace")

        if Btrace.curve_join:
            tracer = curvetracer('Tracer', 'Splines')
        for x in ps.particles:
            if not Btrace.curve_join:
                tracer = curvetracer('Tracer.000', 'Spline.000')
            spline = tracer[0].splines.new('BEZIER')
            spline.bezier_points.add((x.lifetime - 1) // particle_step)  # add point to spline based on step size
            for t in list(range(int(x.lifetime))):
                bpy.context.scene.frame_set(t + x.birth_time)
                if not t % particle_step:
                    p = spline.bezier_points[t // particle_step]
                    p.co = x.location
                    p.handle_right_type = curve_handle
                    p.handle_left_type = curve_handle
            particlecurve = tracer[1]
            curvelist.append(particlecurve)
        # add to group
        bpy.ops.object.select_all(action='DESELECT')
        for curveobject in curvelist:
            curveobject.select = True
            bpy.context.scene.objects.active = curveobject
            bpy.ops.object.group_link(group="Btrace")
            addtracemat(curveobject.data)  # Add material

        if Btrace.animate:
            bpy.ops.curve.btgrow()  # Add grow curve

        return {'FINISHED'}


###########################################################################
## Particle Connect
## connect all particles in active system with a continuous animated curve
###########################################################################

class OBJECT_OT_traceallparticles(bpy.types.Operator):
    bl_idname = 'particles.connect'
    bl_label = 'Connect Particles'
    bl_description = 'Create a continuous animated curve from particles in active system'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (bpy.context.object and bpy.context.object.particle_systems)

    def execute(self, context):

        obj = bpy.context.object
        ps = obj.particle_systems.active
        set = ps.settings

        # Grids distribution not supported
        if set.distribution == 'GRID':
            self.report({'INFO'},"Grid distribution mode for particles not supported.")
            return{'FINISHED'}

        Btrace = bpy.context.window_manager.curve_tracer
        particle_f_start = Btrace.particle_f_start # Get frame start
        particle_f_end = Btrace.particle_f_end # Get frame end
        curve_handle = Btrace.curve_handle
        if curve_handle == 'AUTOMATIC': # hackish because of naming conflict in api
            curve_handle = 'AUTO'
        if curve_handle == 'FREE_ALIGN':
            curve_handle = 'FREE'
        tracer = bpy.data.curves.new('Splines','CURVE') # define what kind of object to create
        curve = bpy.data.objects.new('Tracer',tracer) # Create new object with settings listed above
        bpy.context.scene.objects.link(curve) # Link newly created object to the scene
        spline = tracer.splines.new('BEZIER')  # add a new Bezier point in the new curve
        spline.bezier_points.add(set.count-1)

        tracer.dimensions = '3D'
        tracer.resolution_u = Btrace.curve_u
        tracer.bevel_resolution = Btrace.curve_resolution
        tracer.fill_mode = 'FULL'
        tracer.bevel_depth = Btrace.curve_depth

        if Btrace.particle_auto:
            f_start = int(set.frame_start)
            f_end = int(set.frame_end + set.lifetime)
        else:
            if particle_f_end <= particle_f_start:
                 particle_f_end = particle_f_start + 1
            f_start = particle_f_start
            f_end = particle_f_end

        for bFrames in range(f_start, f_end):
            bpy.context.scene.frame_set(bFrames)
            if not (bFrames-f_start) % Btrace.particle_step:
                for bFrames in range(set.count):
                    if ps.particles[bFrames].alive_state != 'UNBORN':
                        e = bFrames
                    bp = spline.bezier_points[bFrames]
                    pt = ps.particles[e]
                    bp.co = pt.location
                    #bp.handle_left = pt.location
                    #bp.handle_right = pt.location
                    bp.handle_right_type = curve_handle
                    bp.handle_left_type = curve_handle
                    bp.keyframe_insert('co')
                    bp.keyframe_insert('handle_left')
                    bp.keyframe_insert('handle_right')
        # Select new curve
        bpy.ops.object.select_all(action='DESELECT')
        curve.select = True
        bpy.context.scene.objects.active = curve
        addtracemat(curve.data) #Add material
        if Btrace.animate:
            bpy.ops.curve.btgrow()
        return{'FINISHED'}

################## ################## ################## ############
## Writing Tool
## Writes a curve by animating its point's radii
##
################## ################## ################## ############
class OBJECT_OT_writing(bpy.types.Operator):
    bl_idname = 'curve.btwriting'
    bl_label = 'Write'
    bl_description = 'Use Grease Pencil to write and convert to curves'
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod  ### Removed so panel still draws if nothing is selected
    # def poll(cls, context):
    #     return (context.scene.grease_pencil or context.object.grease_pencil != None)

    def execute(self, context):
        Btrace = bpy.context.window_manager.curve_tracer
        obj = bpy.context.object
        gactive = bpy.context.active_object # set selected object before convert
        bpy.ops.gpencil.convert(type='CURVE')
        gactiveCurve = bpy.context.active_object # get curve after convert
        # render ready curve
        gactiveCurve.data.resolution_u = Btrace.curve_u
        gactiveCurve.data.bevel_resolution = Btrace.curve_resolution  # Set bevel resolution from Panel options
        gactiveCurve.data.fill_mode = 'FULL'
        gactiveCurve.data.bevel_depth = Btrace.curve_depth  # Set bevel depth from Panel options

        writeObj = bpy.context.selected_objects
        if Btrace.animate:
            for i in writeObj:
                bpy.context.scene.objects.active = i
                bpy.ops.curve.btgrow()
                addtracemat(bpy.context.object.data) #Add material
        else:
            for i in writeObj:
                bpy.context.scene.objects.active = i
                addtracemat(bpy.context.object.data) #Add material

        # Delete grease pencil strokes
        bpy.context.scene.objects.active = gactive
        bpy.ops.gpencil.data_unlink()
        bpy.context.scene.objects.active = gactiveCurve
        # Smooth object
        bpy.ops.object.shade_smooth()
        # Return to first frame
        bpy.context.scene.frame_set(Btrace.anim_f_start)

        return{'FINISHED'}

################## ################## ################## ############
## Create Curve
## Convert mesh to curve using either Continuous, All Edges, or Sharp Edges
## Option to create noise
################## ################## ################## ############

class OBJECT_OT_convertcurve(bpy.types.Operator):
    bl_idname = "object.btconvertcurve"
    bl_label = "Btrace: Create Curve"
    bl_description = "Convert mesh to curve using either Continuous, All Edges, or Sharp Edges"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import bpy, random, mathutils
        from mathutils import Vector

        Btrace = bpy.context.window_manager.curve_tracer
        traceobjects = bpy.context.selected_objects # create a list with all the selected objects

        obj = bpy.context.object

        ### Convert Font
        if obj.type == 'FONT':
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.convert(target='CURVE') # Convert edges to curve
            bpy.context.object.data.dimensions = '3D'

        # make a continuous edge through all vertices
        if obj.type == 'MESH':
            # Add noise to mesh
            if Btrace.distort_curve:
                for v in obj.data.vertices:
                    for u in range(3):
                        v.co[u] += Btrace.distort_noise * (random.uniform(-1,1))

            if Btrace.convert_edgetype == 'CONTI':
                ## Start Continuous edge
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.delete(type='EDGE_FACE')
                bpy.ops.mesh.select_all(action='DESELECT')
                verts = bpy.context.object.data.vertices
                bpy.ops.object.mode_set(mode='OBJECT')
                li = []
                p1 = random.randint(0,len(verts)-1)

                for v in verts:
                    li.append(v.index)
                li.remove(p1)
                for z in range(len(li)):
                    x = []
                    for px in li:
                        d = verts[p1].co - verts[px].co # find distance from first vert
                        x.append(d.length)
                    p2 = li[x.index(min(x))] # find the shortest distance list index
                    verts[p1].select = verts[p2].select = True
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.context.tool_settings.mesh_select_mode = [True, False, False]
                    bpy.ops.mesh.edge_face_add()
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                    # verts[p1].select = verts[p2].select = False #Doesn't work after Bmesh merge
                    li.remove(p2)  # remove item from list.
                    p1 = p2
                # Convert edges to curve
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.convert(target='CURVE')

            if Btrace.convert_edgetype == 'EDGEALL':
                ## Start All edges
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.delete(type='ONLY_FACE')
                bpy.ops.object.mode_set()
                bpy.ops.object.convert(target='CURVE')
                for sp in obj.data.splines:
                    sp.type = Btrace.curve_spline

        obj = bpy.context.object
        # Set spline type to custom property in panel
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.spline_type_set(type=Btrace.curve_spline)
        # Set handle type to custom property in panel
        bpy.ops.curve.handle_type_set(type=Btrace.curve_handle)
        bpy.ops.object.editmode_toggle()
        obj.data.fill_mode = 'FULL'
        # Set resolution to custom property in panel
        obj.data.bevel_resolution = Btrace.curve_resolution
        obj.data.resolution_u = Btrace.curve_u
        # Set depth to custom property in panel
        obj.data.bevel_depth = Btrace.curve_depth
        # Smooth object
        bpy.ops.object.shade_smooth()
        # Modulate curve radius and add distortion
        if Btrace.distort_curve:
            scale = Btrace.distort_modscale
            if scale == 0:
                return {'FINISHED'}
            for u in obj.data.splines:
                for v in u.bezier_points:
                    v.radius = scale*round(random.random(),3)
        return {'FINISHED'}


################## ################## ################## ############
## Mesh Follow, trace vertex or faces
## Create curve at center of selection item, extruded along animation
## Needs to be animated mesh!!!
################## ################## ################## ############

class OBJECT_OT_meshfollow(bpy.types.Operator):
    bl_idname = "object.btmeshfollow"
    bl_label = "Btrace: Vertex Trace"
    bl_description = "Trace Vertex or Face on an animated mesh"
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type in {'MESH'})

    def execute(self, context):
        import bpy, random
        from mathutils import Vector

        Btrace = bpy.context.window_manager.curve_tracer
        distort_curve = Btrace.distort_curve    # modulate the resulting curve
        stepsize = Btrace.particle_step
        traceobjects = bpy.context.selected_objects  # create a list with all the selected objects

        obj = bpy.context.object
        scn = bpy.context.scene
        meshdata = obj.data
        cursor = bpy.context.scene.cursor_location.copy()  # Store the location to restore at end of script
        drawmethod = Btrace.fol_mesh_type  # Draw from Edges, Verts, or Faces
        if drawmethod == 'VERTS':
            meshobjs = obj.data.vertices
        if drawmethod == 'FACES':
            meshobjs = obj.data.polygons  # untested
        if drawmethod == 'EDGES':
            meshobjs = obj.data.edges  # untested

        # Frame properties
        start_frame, end_frame = Btrace.fol_start_frame, Btrace.fol_end_frame
        if start_frame > end_frame:  # Make sure the math works
            startframe = end_frame - 5  # if start past end, goto (end - 5)
        frames = int((end_frame - start_frame) / stepsize)

        def getsel_option():  # Get selection objects.
            sel = []
            seloption, fol_mesh_type = Btrace.fol_sel_option, Btrace.fol_mesh_type  # options = 'random', 'custom', 'all'
            if fol_mesh_type == 'OBJECT':
                pass
            else:
                if seloption == 'CUSTOM':
                    for i in meshobjs:
                        if i.select == True:
                            sel.append(i.index)
                if seloption == 'RANDOM':
                    for i in list(meshobjs):
                        sel.append(i.index)
                    finalsel = int(len(sel) * Btrace.fol_perc_verts)
                    remove = len(sel) - finalsel
                    for i in range(remove):
                        sel.pop(random.randint(0, len(sel) - 1))
                if seloption == 'ALL':
                    for i in list(meshobjs):
                        sel.append(i.index)

            return sel

        def get_coord(objindex):
            obj_co = []  # list of vector coordinates to use
            frame_x = start_frame
            for i in range(frames):  # create frame numbers list
                scn.frame_set(frame_x)
                if drawmethod != 'OBJECT':
                    followed_item = meshobjs[objindex]
                    if drawmethod == 'VERTS':
                        g_co = obj.matrix_local * followed_item.co  # find Vert vector

                    if drawmethod == 'FACES':
                        g_co = obj.matrix_local * followed_item.normal  # find Face vector

                    if drawmethod == 'EDGES':
                        v1 = followed_item.vertices[0]
                        v2 = followed_item.vertices[1]
                        co1 = bpy.context.object.data.vertices[v1]
                        co2 = bpy.context.object.data.vertices[v2]
                        localcenter = co1.co.lerp(co2.co, 0.5)
                        g_co = obj.matrix_world * localcenter

                if drawmethod == 'OBJECT':
                    g_co = objindex.location.copy()

                obj_co.append(g_co)
                frame_x = frame_x + stepsize

            scn.frame_set(start_frame)
            return obj_co

        def make_curve(co_list):
            Btrace = bpy.context.window_manager.curve_tracer
            tracer = bpy.data.curves.new('tracer','CURVE')
            tracer.dimensions = '3D'
            spline = tracer.splines.new('BEZIER')
            spline.bezier_points.add(len(co_list)-  1)
            curve = bpy.data.objects.new('curve',tracer)
            scn.objects.link(curve)
            curvelist.append(curve)
            # render ready curve
            tracer.resolution_u = Btrace.curve_u
            tracer.bevel_resolution = Btrace.curve_resolution  # Set bevel resolution from Panel options
            tracer.fill_mode = 'FULL'
            tracer.bevel_depth = Btrace.curve_depth  # Set bevel depth from Panel options
            curve_handle = Btrace.curve_handle
            if curve_handle == 'AUTOMATIC': # hackish AUTOMATIC doesn't work here
                curve_handle = 'AUTO'

            # move bezier points to objects
            for i in range(len(co_list)):
                p = spline.bezier_points[i]
                p.co = co_list[i]
                p.handle_right_type = curve_handle
                p.handle_left_type = curve_handle
            return curve

        # Run methods
        # Check if Btrace group exists, if not create
        bgroup = bpy.data.groups.keys()
        if 'Btrace' not in bgroup:
            bpy.ops.group.create(name="Btrace")

        Btrace = bpy.context.window_manager.curve_tracer
        sel = getsel_option()  # Get selection
        curvelist = []  # list to use for grow curve

        if Btrace.fol_mesh_type == 'OBJECT':
            vector_list = get_coord(obj)
            curvelist.append(make_curve(vector_list))
        else:
            for i in sel:
                vector_list = get_coord(i)
                curvelist.append(make_curve(vector_list))
        # Select new curves and add to group
        bpy.ops.object.select_all(action='DESELECT')
        for curveobject in curvelist:
            if curveobject.type == 'CURVE':
                curveobject.select = True
                bpy.context.scene.objects.active = curveobject
                bpy.ops.object.group_link(group="Btrace")
                addtracemat(curveobject.data)
                curveobject.select = False

        if Btrace.animate:  # Add grow curve
            for curveobject in curvelist:
                curveobject.select = True
            bpy.ops.curve.btgrow()
            for curveobject in curvelist:
                curveobject.select = False

        obj.select = False  # Deselect original object
        return {'FINISHED'}

###################################################################
#### Add Tracer Material
###################################################################

def addtracemat(matobj):
    matslots = bpy.context.object.data.materials.items()  # Check if a material exists, skip if it does
    if len(matslots) < 1:  # Make sure there is only one material slot
        engine = bpy.context.scene.render.engine
        Btrace = bpy.context.window_manager.curve_tracer
        if not Btrace.mat_run_color_blender:  # Check if color blender is to be run
            if Btrace.trace_mat_random:  # Create Random color for each item
                # Use random color from chosen palette, assign color lists for each palette
                import random
                brightColors  = [Btrace.brightColor1, Btrace.brightColor2, Btrace.brightColor3, Btrace.brightColor4]
                bwColors = [Btrace.bwColor1, Btrace.bwColor2]
                customColors = [Btrace.mmColor1, Btrace.mmColor2, Btrace.mmColor3, Btrace.mmColor4, Btrace.mmColor5, Btrace.mmColor6, Btrace.mmColor7, Btrace.mmColor8]
                earthColors = [Btrace.earthColor1, Btrace.earthColor2, Btrace.earthColor3, Btrace.earthColor4, Btrace.earthColor5]
                greenblueColors = [Btrace.greenblueColor1, Btrace.greenblueColor2, Btrace.greenblueColor3]
                if Btrace.mmColors == 'BRIGHT':
                    #print(random.randint(0, len(brightColors) - 1))
                    mat_color = brightColors[random.randint(0, len(brightColors) - 1)]
                if Btrace.mmColors == 'BW':
                    mat_color = bwColors[random.randint(0, len(bwColors) - 1)]
                if Btrace.mmColors == 'CUSTOM':
                    mat_color = customColors[random.randint(0, len(customColors) - 1)]
                if Btrace.mmColors == 'EARTH':
                    mat_color = earthColors[random.randint(0, len(earthColors) - 1)]
                if Btrace.mmColors == 'GREENBLUE':
                    mat_color = greenblueColors[random.randint(0, len(greenblueColors) - 1)]
                if Btrace.mmColors == 'RANDOM':
                    mat_color = (random.random(), random.random(), random.random())
            else:  # Choose Single color
                mat_color = Btrace.trace_mat_color
            # mat_color = Btrace.trace_mat_color
            TraceMat = bpy.data.materials.new('TraceMat')
            # add cycles or BI render material options
            if engine == 'CYCLES':
                TraceMat.use_nodes = True
                Diffuse_BSDF = TraceMat.node_tree.nodes['Diffuse BSDF']
                r, g, b = mat_color[0], mat_color[1], mat_color[2]
                Diffuse_BSDF.inputs[0].default_value = [r, g, b, 1]
                TraceMat.diffuse_color = mat_color
            else:
                TraceMat.diffuse_color = mat_color
                TraceMat.specular_intensity = 0.5
            # Add material to object
            matobj.materials.append(bpy.data.materials.get(TraceMat.name))

        else:  # Run color blender operator
            bpy.ops.object.colorblender()

    return {'FINISHED'}

###################################################################
#### Add Color Blender Material
###################################################################

# This is the magical material changer!
class OBJECT_OT_materialChango(bpy.types.Operator):
    bl_idname = 'object.colorblender'
    bl_label = 'Color Blender'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        import bpy, random
        Btrace = bpy.context.window_manager.curve_tracer  # properties panel
        colorObjects = bpy.context.selected_objects

        # Set color lists
        brightColors  = [Btrace.brightColor1, Btrace.brightColor2, Btrace.brightColor3, Btrace.brightColor4]
        bwColors = [Btrace.bwColor1, Btrace.bwColor2]
        customColors = [Btrace.mmColor1, Btrace.mmColor2, Btrace.mmColor3, Btrace.mmColor4, Btrace.mmColor5, Btrace.mmColor6, Btrace.mmColor7, Btrace.mmColor8]
        earthColors = [Btrace.earthColor1, Btrace.earthColor2, Btrace.earthColor3, Btrace.earthColor4, Btrace.earthColor5]
        greenblueColors = [Btrace.greenblueColor1, Btrace.greenblueColor2, Btrace.greenblueColor3]

        colorList = Btrace.mmColors
        engine = bpy.context.scene.render.engine

        # Go through each selected object and run the operator
        for i in colorObjects:
            theObj = i
            # Check to see if object has materials
            checkMaterials = len(theObj.data.materials)
            if engine == 'CYCLES':
                materialName = "colorblendMaterial"
                madMat = bpy.data.materials.new(materialName)
                madMat.use_nodes = True
                if checkMaterials == 0:
                    theObj.data.materials.append(madMat)
                else:
                    theObj.material_slots[0].material = madMat
            else: # This is internal
                if checkMaterials == 0:
                    # Add a material
                    materialName = "colorblendMaterial"
                    madMat = bpy.data.materials.new(materialName)
                    theObj.data.materials.append(madMat)
                else:
                    pass # pass since we have what we need
                # assign the first material of the object to "mat"
                madMat = theObj.data.materials[0]


            # Numbers of frames to skip between keyframes
            skip = Btrace.mmSkip


            # Random material function
            def colorblenderRandom():
                randomRGB = (random.random(), random.random(), random.random())
                if engine == 'CYCLES':
                    Diffuse_BSDF = madMat.node_tree.nodes['Diffuse BSDF']
                    mat_color = randomRGB
                    r, g, b = mat_color[0], mat_color[1], mat_color[2]
                    Diffuse_BSDF.inputs[0].default_value = [r, g, b, 1]
                    madMat.diffuse_color = mat_color
                else:
                    madMat.diffuse_color = randomRGB

            def colorblenderCustom():
                if engine == 'CYCLES':
                    Diffuse_BSDF = madMat.node_tree.nodes['Diffuse BSDF']
                    mat_color = random.choice(customColors)
                    r, g, b = mat_color[0], mat_color[1], mat_color[2]
                    Diffuse_BSDF.inputs[0].default_value = [r, g, b, 1]
                    madMat.diffuse_color = mat_color
                else:
                    madMat.diffuse_color = random.choice(customColors)

            # Black and white color
            def colorblenderBW():
                if engine == 'CYCLES':
                    Diffuse_BSDF = madMat.node_tree.nodes['Diffuse BSDF']
                    mat_color = random.choice(bwColors)
                    r, g, b = mat_color[0], mat_color[1], mat_color[2]
                    Diffuse_BSDF.inputs[0].default_value = [r, g, b, 1]
                    madMat.diffuse_color = mat_color
                else:
                    madMat.diffuse_color = random.choice(bwColors)

            # Bright colors
            def colorblenderBright():
                if engine == 'CYCLES':
                    Diffuse_BSDF = madMat.node_tree.nodes['Diffuse BSDF']
                    mat_color = random.choice(brightColors)
                    r, g, b = mat_color[0], mat_color[1], mat_color[2]
                    Diffuse_BSDF.inputs[0].default_value = [r, g, b, 1]
                    madMat.diffuse_color = mat_color
                else:
                    madMat.diffuse_color = random.choice(brightColors)

            # Earth Tones
            def colorblenderEarth():
                if engine == 'CYCLES':
                    Diffuse_BSDF = madMat.node_tree.nodes['Diffuse BSDF']
                    mat_color = random.choice(earthColors)
                    r, g, b = mat_color[0], mat_color[1], mat_color[2]
                    Diffuse_BSDF.inputs[0].default_value = [r, g, b, 1]
                    madMat.diffuse_color = mat_color
                else:
                    madMat.diffuse_color = random.choice(earthColors)

            # Green to Blue Tones
            def colorblenderGreenBlue():
                if engine == 'CYCLES':
                    Diffuse_BSDF = madMat.node_tree.nodes['Diffuse BSDF']
                    mat_color = random.choice(greenblueColors)
                    r, g, b = mat_color[0], mat_color[1], mat_color[2]
                    Diffuse_BSDF.inputs[0].default_value = [r, g, b, 1]
                    madMat.diffuse_color = mat_color
                else:
                    madMat.diffuse_color = random.choice(greenblueColors)

            # define frame start/end variables
            scn = bpy.context.scene
            start = scn.frame_start
            end = scn.frame_end
            # Go to each frame in iteration and add material
            while start<=(end+(skip-1)):

                bpy.context.scene.frame_set(frame=start)

                # Check what colors setting is checked and run the appropriate function
                if Btrace.mmColors=='RANDOM':
                    colorblenderRandom()
                elif Btrace.mmColors=='CUSTOM':
                    colorblenderCustom()
                elif Btrace.mmColors=='BW':
                    colorblenderBW()
                elif Btrace.mmColors=='BRIGHT':
                    colorblenderBright()
                elif Btrace.mmColors=='EARTH':
                    colorblenderEarth()
                elif Btrace.mmColors=='GREENBLUE':
                    colorblenderGreenBlue()
                else:
                    pass

                # Add keyframe to material
                if engine == 'CYCLES':
                    madMat.node_tree.nodes['Diffuse BSDF'].inputs[0].keyframe_insert('default_value')
                    madMat.keyframe_insert('diffuse_color') # not sure if this is need, it's viewport color only
                else:
                    madMat.keyframe_insert('diffuse_color')

                # Increase frame number
                start += skip
        return{'FINISHED'}

###### This clears the keyframes ######
class OBJECT_OT_clearColorblender(bpy.types.Operator):
    bl_idname = 'object.colorblenderclear'
    bl_label = 'Clear colorblendness'
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):

        import bpy, random
        mcolorblend = context.window_manager.colorblender_operator # properties panel
        colorObjects = bpy.context.selected_objects

        # Go through each selected object and run the operator
        for i in colorObjects:
            theObj = i
            # assign the first material of the object to "mat"
            matCl = theObj.data.materials[0]

            # define frame start/end variables
            scn = bpy.context.scene
            start = scn.frame_start
            end = scn.frame_end

            # Remove all keyframes from diffuse_color, super sloppy need to find better way
            while start <= (end * 2):
                bpy.context.scene.frame_set(frame=start)
                matCl.keyframe_delete('diffuse_color')
                start += 1

        return{'FINISHED'}


################## ################## ################## ############
## F-Curve Noise
## will add noise modifiers to each selected object f-curves
## change type to: 'rotation' | 'location' | 'scale' | '' to effect all
## first record a keyframe for this to work (to generate the f-curves)
################## ################## ################## ############

class OBJECT_OT_fcnoise(bpy.types.Operator):
    bl_idname = "object.btfcnoise"
    bl_label = "Btrace: F-curve Noise"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import bpy, random

        Btrace = bpy.context.window_manager.curve_tracer
        amp = Btrace.fcnoise_amp
        timescale = Btrace.fcnoise_timescale
        addkeyframe = Btrace.fcnoise_key

        # This sets properties for Loc, Rot and Scale if they're checked in the Tools window
        noise_rot = 'rotation'
        noise_loc = 'location'
        noise_scale = 'scale'
        if not Btrace.fcnoise_rot:
            noise_rot = 'none'
        if not Btrace.fcnoise_loc:
            noise_loc = 'none'
        if not Btrace.fcnoise_scale:
            noise_scale = 'none'

        type = noise_loc, noise_rot, noise_scale # Add settings from panel for type of keyframes
        amplitude = amp
        time_scale = timescale

        for i in bpy.context.selected_objects:
            # Add keyframes, this is messy and should only add keyframes for what is checked
            if addkeyframe == True:
                bpy.ops.anim.keyframe_insert(type="LocRotScale")
            for obj in bpy.context.selected_objects:
                if obj.animation_data:
                    for c in obj.animation_data.action.fcurves:
                        if c.data_path.startswith(type):
                            # clean modifiers
                            for m in c.modifiers :
                                c.modifiers.remove(m)
                            # add noide modifiers
                            n = c.modifiers.new('NOISE')
                            n.strength = amplitude
                            n.scale = time_scale
                            n.phase = random.randint(0,999)
        return {'FINISHED'}

################## ################## ################## ############
## Curve Grow Animation
## Animate curve radius over length of time
################## ################## ################## ############
class OBJECT_OT_curvegrow(bpy.types.Operator):
    bl_idname = 'curve.btgrow'
    bl_label = 'Run Script'
    bl_description = 'Keyframe points radius'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type in {'CURVE'})

    def execute(self, context):
        Btrace = bpy.context.window_manager.curve_tracer
        anim_f_start, anim_length, anim_auto = Btrace.anim_f_start, Btrace.anim_length, Btrace.anim_auto
        curve_resolution, curve_depth = Btrace.curve_resolution, Btrace.curve_depth
        # make the curve visible
        objs = bpy.context.selected_objects
        for i in objs: # Execute on multiple selected objects
            bpy.context.scene.objects.active = i
            obj = bpy.context.active_object
            try:
                obj.data.fill_mode = 'FULL'
            except:
                obj.data.dimensions = '3D'
                obj.data.fill_mode = 'FULL'
            if not obj.data.bevel_resolution:
                obj.data.bevel_resolution = curve_resolution
            if not obj.data.bevel_depth:
                obj.data.bevel_depth = curve_depth
            if anim_auto:
                anim_f_start = bpy.context.scene.frame_start
                anim_length = bpy.context.scene.frame_end
            # get points data and beautify
            actual, total = anim_f_start, 0
            for sp in obj.data.splines:
                total += len(sp.points) + len(sp.bezier_points)
            step = anim_length / total
            for sp in obj.data.splines:
                sp.radius_interpolation = 'BSPLINE'
                po = [p for p in sp.points] + [p for p in sp.bezier_points]
                if not Btrace.anim_keepr:
                    for p in po:
                        p.radius = 1
                if Btrace.anim_tails and not sp.use_cyclic_u:
                    po[0].radius = po[-1].radius = 0
                    po[1].radius = po[-2].radius = .65
                ra = [p.radius for p in po]

                # record the keyframes
                for i in range(len(po)):
                    po[i].radius = 0
                    po[i].keyframe_insert('radius', frame=actual)
                    actual += step
                    po[i].radius = ra[i]
                    po[i].keyframe_insert('radius', frame=(actual + Btrace.anim_delay))

                    if Btrace.anim_f_fade:
                        po[i].radius = ra[i]
                        po[i].keyframe_insert('radius', frame=(actual + Btrace.anim_f_fade - step))
                        po[i].radius = 0
                        po[i].keyframe_insert('radius', frame=(actual + Btrace.anim_delay + Btrace.anim_f_fade))

            bpy.context.scene.frame_set(Btrace.anim_f_start)
        return{'FINISHED'}

################## ################## ################## ############
## Remove animation and curve radius data
################## ################## ################## ############
class OBJECT_OT_reset(bpy.types.Operator):
    bl_idname = 'object.btreset'
    bl_label = 'Clear animation'
    bl_description = 'Remove animation / curve radius data'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objs = bpy.context.selected_objects
        for i in objs: # Execute on multiple selected objects
            bpy.context.scene.objects.active = i
            obj = bpy.context.active_object
            obj.animation_data_clear()
            if obj.type == 'CURVE':
                for sp in obj.data.splines:
                    po = [p for p in sp.points] + [p for p in sp.bezier_points]
                    for p in po:
                        p.radius = 1
        return{'FINISHED'}

### Define Classes to register
classes = [
    TracerProperties,
    TracerPropertiesMenu,
    addTracerObjectPanel,
    OBJECT_OT_convertcurve,
    OBJECT_OT_objecttrace,
    OBJECT_OT_objectconnect,
    OBJECT_OT_writing,
    OBJECT_OT_particletrace,
    OBJECT_OT_traceallparticles,
    OBJECT_OT_curvegrow,
    OBJECT_OT_reset,
    OBJECT_OT_fcnoise,
    OBJECT_OT_meshfollow,
    OBJECT_OT_materialChango,
    OBJECT_OT_clearColorblender
    ]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.WindowManager.curve_tracer = bpy.props.PointerProperty(type=TracerProperties)
    bpy.types.WindowManager.btrace_menu = bpy.props.PointerProperty(type=TracerPropertiesMenu, update=deselect_others)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.WindowManager.curve_tracer
if __name__ == "__main__":
    register()
