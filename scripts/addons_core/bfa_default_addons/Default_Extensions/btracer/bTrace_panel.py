# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Panel

# Draw Brush panel in Toolbar
class addTracerObjectPanel(Panel):
    bl_idname = "BTRACE_PT_object_brush"
    bl_label = "BTracer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_category = "Create"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        Btrace = context.window_manager.curve_tracer
        addon_prefs = context.preferences.addons[__package__].preferences
        switch_expand = addon_prefs.expand_enum
        obj = context.object

        # Color Blender Panel options
        def color_blender():
            # Buttons for Color Blender
            row = box.row()
            row.label(text="Color palette")
            row.prop(Btrace, "mmColors", text="")

            # Show Custom Colors if selected
            if Btrace.mmColors == 'CUSTOM':
                row = box.row(align=True)
                for i in range(1, 9):
                    row.prop(Btrace, "mmColor" + str(i), text="")
            # Show Earth Colors
            elif Btrace.mmColors == 'BW':
                row = box.row(align=True)
                row.prop(Btrace, "bwColor1", text="")
                row.prop(Btrace, "bwColor2", text="")
            # Show Earth Colors
            elif Btrace.mmColors == 'BRIGHT':
                row = box.row(align=True)
                for i in range(1, 5):
                    row.prop(Btrace, "brightColor" + str(i), text="")
            # Show Earth Colors
            elif Btrace.mmColors == 'EARTH':
                row = box.row(align=True)
                for i in range(1, 6):
                    row.prop(Btrace, "earthColor" + str(i), text="")
            # Show Earth Colors
            elif Btrace.mmColors == 'GREENBLUE':
                row = box.row(align=True)
                for i in range(1, 4):
                    row.prop(Btrace, "greenblueColor" + str(i), text="")
            elif Btrace.mmColors == 'RANDOM':
                row = box.row()

        # Curve noise settings
        def curve_noise():
            row = box.row()
            row.label(text="F-Curve Noise", icon='RNDCURVE')
            row = box.row(align=True)
            row.prop(Btrace, "fcnoise_rot", toggle=True)
            row.prop(Btrace, "fcnoise_loc", toggle=True)
            row.prop(Btrace, "fcnoise_scale", toggle=True)

            col = box.column(align=True)
            col.prop(Btrace, "fcnoise_amp")
            col.prop(Btrace, "fcnoise_timescale")
            box.prop(Btrace, "fcnoise_key")

        # Curve Panel options
        def curve_settings():
            # Button for curve options
            row = self.layout.row()
            row = box.row(align=True)

            row.prop(Btrace, "show_curve_settings",
                     icon='CURVE_BEZCURVE', text="Curve Settings")
            row.prop(Btrace, "material_settings",
                     icon='MATERIAL_DATA', text="Material Settings")

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
                        row.operator("object.colorblenderclear",
                                     text="Reset Material Keyframes",
                                     icon="KEY_DEHLT")
                        row.prop(Btrace, "mmSkip", text="Keyframe every")
                    color_blender()
                row = box.row()

            if Btrace.show_curve_settings:
                # selected curve options
                if len(context.selected_objects) > 0 and obj.type == 'CURVE':
                    col = box.column(align=True)
                    col.label(text="Edit Curves for:", icon='IPO_BEZIER')
                    col.separator()
                    col.label(text="Selected Curve Bevel Options")
                    row = col.row(align=True)
                    row.prop(obj.data, "bevel_depth", text="Depth")
                    row.prop(obj.data, "bevel_resolution", text="Resolution")
                    row = col.row(align=True)
                    row.prop(obj.data, "resolution_u")
                else:  # For new curve
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

        # Grow Animation Panel options
        def add_grow():
            # Button for grow animation option
            row = box.row()
            row.label(text="Animate Final Curve", icon="NONE")
            row = box.row()
            row.prop(Btrace, "animate", text="Add Grow Curve Animation", icon="META_BALL")
            box.separator()
            if Btrace.animate:
                box.label(text="Frame Animation Settings:", icon="META_BALL")
                col = box.column(align=True)
                col.prop(Btrace, "anim_auto")
                if not Btrace.anim_auto:
                    row = col.row(align=True)
                    row.prop(Btrace, "anim_f_start")
                    row.prop(Btrace, "anim_length")
                row = col.row(align=True)
                row.prop(Btrace, "anim_delay")
                row.prop(Btrace, "anim_f_fade")

                box.label(text="Additional Settings")
                row = box.row()
                row.prop(Btrace, "anim_tails")
                row.prop(Btrace, "anim_keepr")

        # Start Btrace Panel
        if switch_expand == 'list':
            layout.label(text="Available Tools:", icon="COLLAPSEMENU")
            col = layout.column(align=True)
            col.prop(Btrace, "btrace_toolmenu", text="")
        elif switch_expand == 'col':
            col = layout.column(align=True)
            col.prop(Btrace, "btrace_toolmenu", expand=True)
        elif switch_expand == 'row':
            row = layout.row(align=True)
            row.alignment = 'CENTER'
            row.prop(Btrace, "btrace_toolmenu", text="", expand=True)

        # Start Object Tools
        sel = context.selected_objects

        # Default option (can be expanded into help)
        if Btrace.btrace_toolmenu == 'tool_help':
            row = layout.row()
            row.label(text="Pick an option", icon="HELP")

        # Object Trace
        elif Btrace.btrace_toolmenu == 'tool_objectTrace':
            row = layout.row()
            row.label(text="  Trace Tool:", icon="FORCE_CURVE")
            box = self.layout.box()
            row = box.row()
            row.label(text="Object Trace", icon="FORCE_MAGNETIC")
            row.operator("object.btobjecttrace", text="Run!", icon="PLAY")
            row = box.row()
            row.prop(Btrace, "settings_toggle", icon="MODIFIER", text="Settings")
            myselected = "Selected %d" % len(context.selected_objects)
            row.label(text=myselected)
            if Btrace.settings_toggle:
                box.label(text="Edge Type for Curves:", icon="IPO_CONSTANT")
                row = box.row(align=True)
                row.prop(Btrace, "convert_edgetype", text="")
                box.prop(Btrace, "object_duplicate")
                if len(sel) > 1:
                    box.prop(Btrace, "convert_joinbefore")
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
                add_grow()        # Grow settings here

        # Objects Connect
        elif Btrace.btrace_toolmenu == 'tool_objectsConnect':
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
                    box.operator("object.select_order",
                                 text="Click to start order selection",
                                 icon='UV_SYNC_SELECT')
                row = box.row()
                row.prop(Btrace, "connect_noise", text="Add F-Curve Noise")
                if Btrace.connect_noise:
                    curve_noise()     # Show Curve Noise settings

                curve_settings()      # Show Curve/material settings
                add_grow()            # Grow settings here

        # Mesh Follow
        elif Btrace.btrace_toolmenu == 'tool_meshFollow':
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
                        row.label(text="Random Select of Total")
                        row.prop(Btrace, "fol_perc_verts", text="%")
                    if Btrace.fol_sel_option == 'CUSTOM':
                        row.label(text="Choose selection in Edit Mode")
                    if Btrace.fol_sel_option == 'ALL':
                        row.label(text="Select All items")
                col = box.column(align=True)
                col.label(text="Time Options", icon="TIME")
                col.prop(Btrace, "particle_step")
                row = col.row(align=True)
                row.prop(Btrace, "fol_start_frame")
                row.prop(Btrace, "fol_end_frame")
                curve_settings()  # Show Curve/material settings
                add_grow()        # Grow settings here

        # Handwriting Tools
        elif Btrace.btrace_toolmenu == 'tool_handwrite':
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
            row.operator("gpencil.draw", text="Line", icon='ZOOM_OUT').mode = 'DRAW_STRAIGHT'
            row.operator("gpencil.draw", text="Erase", icon='TPAINT_HLT').mode = 'ERASER'
            row = box.row()
            row.operator("gpencil.data_unlink", text="Delete Grease Pencil Layer", icon="CANCEL")
            row = box.row()
            curve_settings()  # Show Curve/material settings
            add_grow()        # Grow settings here

        # Particle Trace
        elif Btrace.btrace_toolmenu == 'tool_particleTrace':
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
                add_grow()        # Grow settings here

        # Connect Particles
        elif Btrace.btrace_toolmenu == 'tool_particleConnect':
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
                add_grow()        # Grow settings here

        # Grow Animation
        elif Btrace.btrace_toolmenu == 'tool_growCurve':
            row = layout.row()
            row.label(text="  Curve Tool:", icon="OUTLINER_OB_CURVE")
            box = self.layout.box()
            row = box.row()
            row.label(text="Grow Curve", icon="META_BALL")
            row.operator("curve.btgrow", text="Run!", icon="PLAY")
            row = box.row()
            row.prop(Btrace, "settings_toggle", icon="MODIFIER", text="Settings")
            row.operator("object.btreset", icon="KEY_DEHLT")
            if Btrace.settings_toggle:
                box.label(text="Frame Animation Settings:")
                col = box.column(align=True)
                col.prop(Btrace, "anim_auto")
                if not Btrace.anim_auto:
                    row = col.row(align=True)
                    row.prop(Btrace, "anim_f_start")
                    row.prop(Btrace, "anim_length")
                row = col.row(align=True)
                row.prop(Btrace, "anim_delay")
                row.prop(Btrace, "anim_f_fade")

                box.label(text="Additional Settings")
                row = box.row()
                row.prop(Btrace, "anim_tails")
                row.prop(Btrace, "anim_keepr")

        # F-Curve Noise Curve
        elif Btrace.btrace_toolmenu == 'tool_fcurve':
            row = layout.row()
            row.label(text="  Curve Tool:", icon="OUTLINER_OB_CURVE")
            box = self.layout.box()
            row = box.row()
            row.label(text="F-Curve Noise", icon='RNDCURVE')
            row.operator("object.btfcnoise", icon='PLAY', text="Run!")
            row = box.row()
            row.prop(Btrace, "settings_toggle", icon='MODIFIER', text='Settings')
            row.operator("object.btreset", icon='KEY_DEHLT')
            if Btrace.settings_toggle:
                curve_noise()

        # Color Blender
        elif Btrace.btrace_toolmenu == 'tool_colorblender':
            row = layout.row()
            row.label(text="  Curve/Object Tool:", icon="OUTLINER_OB_CURVE")
            box = self.layout.box()
            row = box.row()
            row.label(text="Color Blender", icon="COLOR")
            row.operator("object.colorblender", icon='PLAY', text="Run!")
            row = box.row()
            row.operator("object.colorblenderclear", text="Reset Keyframes", icon="KEY_DEHLT")
            row.prop(Btrace, "mmSkip", text="Keyframe every")
            color_blender()
