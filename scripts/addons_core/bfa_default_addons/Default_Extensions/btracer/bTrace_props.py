# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import (
        Panel,
        PropertyGroup,
        )
from bpy.props import (
        FloatProperty,
        EnumProperty,
        IntProperty,
        BoolProperty,
        FloatVectorProperty,
        )


# Class to define properties
class TracerProperties(PropertyGroup):
    """Options for tools"""
    curve_spline: EnumProperty(
            name="Spline",
            items=(("POLY", "Poly", "Use Poly spline type"),
                   ("NURBS", "Nurbs", "Use Nurbs spline type"),
                   ("BEZIER", "Bezier", "Use Bezier spline type")),
            description="Choose which type of spline to use when curve is created",
            default="BEZIER"
            )
    curve_handle: EnumProperty(
            name="Handle",
            items=(("ALIGNED", "Aligned", "Use Aligned Handle Type"),
                   ("AUTOMATIC", "Automatic", "Use Auto Handle Type"),
                   ("FREE_ALIGN", "Free Align", "Use Free Handle Type"),
                   ("VECTOR", "Vector", "Use Vector Handle Type")),
            description="Choose which type of handle to use when curve is created",
            default="VECTOR"
            )
    curve_resolution: IntProperty(
            name="Bevel Resolution",
            min=1, max=32,
            default=4,
            description="Adjust the Bevel resolution"
            )
    curve_depth: FloatProperty(
            name="Bevel Depth",
            min=0.0, max=100.0,
            default=0.1,
            description="Adjust the Bevel depth"
            )
    curve_u: IntProperty(
            name="Resolution U",
            min=0, max=64,
            default=12,
            description="Adjust the Surface resolution"
            )
    curve_join: BoolProperty(
            name="Join Curves",
            default=False,
            description="Join all the curves after they have been created"
            )
    curve_smooth: BoolProperty(
            name="Smooth",
            default=True,
            description="Render curve smooth"
            )
    # Option to Duplicate Mesh
    object_duplicate: BoolProperty(
            name="Apply to Copy",
            default=False,
            description="Apply curve to a copy of object"
            )
    # Distort Mesh options
    distort_modscale: IntProperty(
            name="Modulation Scale",
            min=0, max=50,
            default=2,
            description="Add a scale to modulate the curve at random points, set to 0 to disable"
            )
    distort_noise: FloatProperty(
            name="Mesh Noise",
            min=0.0, max=50.0,
            default=0.00,
            description="Adjust noise added to mesh before adding curve"
            )
    # Particle Options
    particle_step: IntProperty(
            name="Step Size",
            min=1, max=50,
            default=5,
            description="Sample one every this number of frames"
            )
    particle_auto: BoolProperty(
            name="Auto Frame Range",
            default=True,
            description="Calculate Frame Range from particles life"
            )
    particle_f_start: IntProperty(
            name='Start Frame',
            min=1, max=5000,
            default=1,
            description='Start frame'
            )
    particle_f_end: IntProperty(
            name="End Frame",
            min=1, max=5000,
            default=250,
            description="End frame"
            )
    # F-Curve Modifier Properties
    fcnoise_rot: BoolProperty(
            name="Rotation",
            default=False,
            description="Affect Rotation"
            )
    fcnoise_loc: BoolProperty(
            name="Location",
            default=True,
            description="Affect Location"
            )
    fcnoise_scale: BoolProperty(
            name="Scale",
            default=False,
            description="Affect Scale"
            )
    fcnoise_amp: IntProperty(
            name="Amp",
            min=1, max=500,
            default=5,
            description="Adjust the amplitude"
            )
    fcnoise_timescale: FloatProperty(
            name="Time Scale",
            min=1, max=500,
            default=50,
            description="Adjust the time scale"
            )
    fcnoise_key: BoolProperty(
            name="Add Keyframe",
            default=True,
            description="Keyframe is needed for tool, this adds a LocRotScale keyframe"
            )
    show_curve_settings: BoolProperty(
            name="Curve Settings",
            default=False,
            description="Change the curve settings for the created curve"
            )
    material_settings: BoolProperty(
            name="Material Settings",
            default=False,
            description="Change the material settings for the created curve"
            )
    particle_settings: BoolProperty(
            name="Particle Settings",
            default=False,
            description="Show the settings for the created curve"
            )
    animation_settings: BoolProperty(
            name="Animation Settings",
            default=False,
            description="Show the settings for the Animations"
            )
    distort_curve: BoolProperty(
            name="Add Distortion",
            default=False,
            description="Set options to distort the final curve"
            )
    connect_noise: BoolProperty(
            name="F-Curve Noise",
            default=False,
            description="Adds F-Curve Noise Modifier to selected objects"
            )
    settings_objectTrace: BoolProperty(
            name="Object Trace Settings",
            default=False,
            description="Trace selected mesh object with a curve"
            )
    settings_objectsConnect: BoolProperty(
            name="Objects Connect Settings",
            default=False,
            description="Connect objects with a curve controlled by hooks"
            )
    settings_objectTrace: BoolProperty(
            name="Object Trace Settings",
            default=False,
            description="Trace selected mesh object with a curve"
            )
    respect_order: BoolProperty(
            name="Order",
            default=False,
            description="Remember order objects were selected"
            )
    settings_particleTrace: BoolProperty(
            name="Particle Trace Settings",
            default=False,
            description="Trace particle path with a  curve"
            )
    settings_particleConnect: BoolProperty(
            name="Particle Connect Settings",
            default=False,
            description="Connect particles with a curves and animated over particle lifetime"
            )
    settings_growCurve: BoolProperty(
            name="Grow Curve Settings",
            default=False,
            description="Animate curve bevel over time by keyframing points radius"
            )
    settings_fcurve: BoolProperty(
            name="F-Curve Settings",
            default=False,
            description="F-Curve Settings"
            )
    settings_toggle: BoolProperty(
            name="Settings",
            default=False,
            description="Toggle Settings"
            )
    # Animation Options
    anim_auto: BoolProperty(
            name="Auto Frame Range",
            default=True,
            description="Automatically calculate Frame Range"
            )
    anim_f_start: IntProperty(
            name="Start",
            min=1, max=2500,
            default=1,
            description="Start frame / Hidden object"
            )
    anim_length: IntProperty(
            name="Duration",
            min=1,
            soft_max=1000, max=2500,
            default=100,
            description="Animation Length"
            )
    anim_f_fade: IntProperty(
            name="Fade After",
            min=0,
            soft_max=250, max=2500,
            default=10,
            description="Fade after this frames / Zero means no fade"
            )
    anim_delay: IntProperty(
            name="Grow",
            min=0, max=50,
            default=5,
            description="Frames it takes a point to grow"
            )
    anim_tails: BoolProperty(
            name='Tails on endpoints',
            default=True,
            description='Set radius to zero for open splines endpoints'
            )
    anim_keepr: BoolProperty(
            name="Keep Radius",
            default=True,
            description="Try to keep radius data from original curve"
            )
    animate: BoolProperty(
            name="Animate Result",
            default=False,
            description="Animate the final curve objects"
            )
    # Convert to Curve options
    convert_conti: BoolProperty(
            name="Continuous",
            default=True,
            description="Create a continuous curve using verts from mesh"
            )
    convert_everyedge: BoolProperty(
            name="Every Edge",
            default=False,
            description="Create a curve from all verts in a mesh"
            )
    convert_edgetype: EnumProperty(
            name="Edge Type for Curves",
            items=(("CONTI", "Continuous", "Create a continuous curve using verts from mesh"),
                   ("EDGEALL", "All Edges", "Create a curve from every edge in a mesh")),
            description="Choose which type of spline to use when curve is created",
            default="CONTI"
            )
    convert_joinbefore: BoolProperty(
            name="Join objects before convert",
            default=False,
            description="Join all selected mesh to one object before converting to mesh"
            )
    # Mesh Follow Options
    fol_edge_select: BoolProperty(
            name="Edge",
            default=False,
            description="Grow from edges"
            )
    fol_vert_select: BoolProperty(
            name="Vertex",
            default=False,
            description="Grow from verts"
            )
    fol_face_select: BoolProperty(
            name="Face",
            default=True,
            description="Grow from faces"
            )
    fol_mesh_type: EnumProperty(
            name="Mesh type",
            default="VERTS",
            description="Mesh feature to draw cruves from",
            items=(("VERTS", "Verts", "Draw from Verts"),
                   ("EDGES", "Edges", "Draw from Edges"),
                   ("FACES", "Faces", "Draw from Faces"),
                   ("OBJECT", "Object", "Draw from Object origin"))
            )
    fol_start_frame: IntProperty(
            name="Start Frame",
            min=1, max=2500,
            default=1,
            description="Start frame for range to trace"
            )
    fol_end_frame: IntProperty(
            name="End Frame",
            min=1, max=2500,
            default=250,
            description="End frame for range to trace"
            )
    fol_perc_verts: FloatProperty(
            name="Reduce selection by",
            min=0.001, max=1.000,
            default=0.5,
            description="percentage of total verts to trace"
            )
    fol_sel_option: EnumProperty(
            name="Selection type",
            description="Choose which objects to follow",
            default="RANDOM",
            items=(("RANDOM", "Random", "Follow Random items"),
                   ("CUSTOM", "Custom Select", "Follow selected items"),
                   ("ALL", "All", "Follow all items"))
            )
    trace_mat_color: FloatVectorProperty(
            name="Material Color",
            description="Choose material color",
            min=0, max=1,
            default=(0.0, 0.3, 0.6),
            subtype="COLOR"
            )
    trace_mat_random: BoolProperty(
            name="Random Color",
            default=False,
            description='Make the material colors random'
            )
    # Material custom Properties properties
    mat_simple_adv_toggle: EnumProperty(
            name="Material Options",
            items=(("SIMPLE", "Simple", "Show Simple Material Options"),
                   ("ADVANCED", "Advanced", "Show Advanced Material Options")),
            description="Choose which Material Options to show",
            default="SIMPLE"
            )
    mat_run_color_blender: BoolProperty(
            name="Run Color Blender",
            default=False,
            description="Generate colors from a color scheme"
            )
    mmColors: EnumProperty(
            items=(("RANDOM", "Random", "Use random colors"),
                    ("CUSTOM", "Custom", "Use custom colors"),
                    ("BW", "Black/White", "Use Black and White"),
                    ("BRIGHT", "Bright Colors", "Use Bright colors"),
                    ("EARTH", "Earth", "Use Earth colors"),
                    ("GREENBLUE", "Green to Blue", "Use Green to Blue colors")),
            description="Choose which type of colors the materials uses",
            default="BRIGHT",
            name="Define a color palette"
            )
    # Custom property for how many keyframes to skip
    mmSkip: IntProperty(
            name="frames",
            min=1, max=500,
            default=20,
            description="Number of frames between each keyframes"
            )
    # Custom property to enable/disable random order for the
    mmBoolRandom: BoolProperty(
            name="Random Order",
            default=False,
            description="Randomize the order of the colors"
            )
    # Custom Color properties
    mmColor1: FloatVectorProperty(
            min=0, max=1,
            default=(0.8, 0.8, 0.8),
            description="Custom Color 1", subtype="COLOR"
            )
    mmColor2: FloatVectorProperty(
            min=0, max=1,
            default=(0.8, 0.8, 0.3),
            description="Custom Color 2",
            subtype="COLOR"
            )
    mmColor3: FloatVectorProperty(
            min=0, max=1,
            default=(0.8, 0.5, 0.6),
            description="Custom Color 3",
            subtype="COLOR"
            )
    mmColor4: FloatVectorProperty(
            min=0, max=1,
            default=(0.2, 0.8, 0.289),
            description="Custom Color 4",
            subtype="COLOR"
            )
    mmColor5: FloatVectorProperty(
            min=0, max=1,
            default=(1.0, 0.348, 0.8),
            description="Custom Color 5",
            subtype="COLOR"
            )
    mmColor6: FloatVectorProperty(
            min=0, max=1,
            default=(0.4, 0.67, 0.8),
            description="Custom Color 6",
            subtype="COLOR"
            )
    mmColor7: FloatVectorProperty(
            min=0, max=1,
            default=(0.66, 0.88, 0.8),
            description="Custom Color 7",
            subtype="COLOR"
            )
    mmColor8: FloatVectorProperty(
            min=0, max=1,
            default=(0.8, 0.38, 0.22),
            description="Custom Color 8",
            subtype="COLOR"
            )
    # BW Color properties
    bwColor1: FloatVectorProperty(
            min=0, max=1,
            default=(0.0, 0.0, 0.0),
            description="Black/White Color 1",
            subtype="COLOR"
            )
    bwColor2: FloatVectorProperty(
            min=0, max=1,
            default=(1.0, 1.0, 1.0),
            description="Black/White Color 2",
            subtype="COLOR"
            )
    # Bright Color properties
    brightColor1: FloatVectorProperty(
            min=0, max=1,
            default=(1.0, 0.0, 0.75),
            description="Bright Color 1",
            subtype="COLOR"
            )
    brightColor2: FloatVectorProperty(
            min=0, max=1,
            default=(0.0, 1.0, 1.0),
            description="Bright Color 2",
            subtype="COLOR"
            )
    brightColor3: FloatVectorProperty(
            min=0, max=1,
            default=(0.0, 1.0, 0.0),
            description="Bright Color 3",
            subtype="COLOR"
            )
    brightColor4: FloatVectorProperty(
            min=0, max=1,
            default=(1.0, 1.0, 0.0),
            description="Bright Color 4", subtype="COLOR"
            )
    # Earth Color Properties
    earthColor1: FloatVectorProperty(
            min=0, max=1,
            default=(0.068, 0.019, 0.014),
            description="Earth Color 1",
            subtype="COLOR"
            )
    earthColor2: FloatVectorProperty(
            min=0, max=1,
            default=(0.089, 0.060, 0.047),
            description="Earth Color 2",
            subtype="COLOR"
            )
    earthColor3: FloatVectorProperty(
            min=0, max=1,
            default=(0.188, 0.168, 0.066),
            description="Earth Color 3",
            subtype="COLOR"
            )
    earthColor4: FloatVectorProperty(
            min=0, max=1,
            default=(0.445, 0.296, 0.065),
            description="Earth Color 4",
            subtype="COLOR"
            )
    earthColor5: FloatVectorProperty(
            min=0, max=1,
            default=(0.745, 0.332, 0.065),
            description="Earth Color 5",
            subtype="COLOR"
            )
    # Green to Blue Color properties
    greenblueColor1: FloatVectorProperty(
            min=0, max=1,
            default=(0.296, 0.445, 0.074),
            description="Green/Blue Color 1",
            subtype="COLOR"
            )
    greenblueColor2: FloatVectorProperty(
            min=0, max=1,
            default=(0.651, 1.0, 0.223),
            description="Green/Blue Color 2",
            subtype="COLOR"
            )
    greenblueColor3: FloatVectorProperty(
            min=0, max=1,
            default=(0.037, 0.047, 0.084),
            description="Green/Blue Color 3",
            subtype="COLOR"
            )

    # Toolbar show/hide booleans for tool options
    btrace_menu_items = [
            ('tool_help', "Choose Tool",
             "Pick one of the options below", "INFO", 0),
            ('tool_objectTrace', "Object Trace",
             "Trace selected mesh object with a curve", "FORCE_MAGNETIC", 1),
            ('tool_objectsConnect', "Objects Connect",
             "Connect objects with a curve controlled by hooks", "OUTLINER_OB_EMPTY", 2),
            ('tool_meshFollow', "Mesh Follow",
             "Follow selection items on animated mesh object", "DRIVER", 3),
        #     ('tool_handwrite', "Handwriting",
        #      "Create and Animate curve using the grease pencil", "BRUSH_DATA", 4),
            ('tool_particleTrace', "Particle Trace",
             "Trace particle path with a  curve", "PARTICLES", 5),
            ('tool_particleConnect', "Particle Connect",
             "Connect particles with a curves and animated over particle lifetime", "MOD_PARTICLES", 6),
            ('tool_growCurve', "Grow Curve",
             "Animate curve bevel over time by keyframing points radius", "META_BALL", 7),
            ('tool_fcurve', "F-Curve Noise",
             "Add F-Curve noise to selected objects", "RNDCURVE", 8),
            ('tool_colorblender', "Color Blender",
             "Pick the color of the created curves", "COLOR", 9),
            ]

    btrace_toolmenu: EnumProperty(
            name="Tools",
            items=btrace_menu_items,
            description="",
            default='tool_help'
            )
