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
import bpy

narrowui = bpy.context.user_preferences.view.properties_width_check

class View3DPanel():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'


# ********** default tools for objectmode ****************


class VIEW3D_PT_tools_objectmode(View3DPanel, bpy.types.Panel):
    bl_context = "objectmode"
    bl_label = "Object Tools"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Transform:")
        col.operator("transform.translate")
        col.operator("transform.rotate")
        col.operator("transform.resize", text="Scale")

        col = layout.column(align=True)
        col.operator("object.origin_set", text="Origin")

        col = layout.column(align=True)
        col.label(text="Object:")
        col.operator("object.duplicate_move")
        col.operator("object.delete")
        col.operator("object.join")

        active_object = context.active_object
        if active_object and active_object.type == 'MESH':

            col = layout.column(align=True)
            col.label(text="Shading:")
            col.operator("object.shade_smooth", text="Smooth")
            col.operator("object.shade_flat", text="Flat")

        col = layout.column(align=True)
        col.label(text="Keyframes:")
        col.operator("anim.keyframe_insert_menu", text="Insert")
        col.operator("anim.keyframe_delete_v3d", text="Remove")

        col = layout.column(align=True)
        col.label(text="Repeat:")
        col.operator("screen.repeat_last")
        col.operator("screen.repeat_history", text="History...")

        col = layout.column(align=True)
        col.label(text="Grease Pencil:")
        row = col.row()
        row.operator("gpencil.draw", text="Draw").mode = 'DRAW'
        row.operator("gpencil.draw", text="Line").mode = 'DRAW_STRAIGHT'
        row.operator("gpencil.draw", text="Erase").mode = 'ERASER'

# ********** default tools for editmode_mesh ****************


class VIEW3D_PT_tools_meshedit(View3DPanel, bpy.types.Panel):
    bl_context = "mesh_edit"
    bl_label = "Mesh Tools"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Transform:")
        col.operator("transform.translate")
        col.operator("transform.rotate")
        col.operator("transform.resize", text="Scale")
        col.operator("transform.shrink_fatten", text="Along Normal")


        col = layout.column(align=True)
        col.label(text="Deform:")
        col.operator("transform.edge_slide")
        col.operator("mesh.rip_move")
        col.operator("mesh.vertices_smooth")


        col = layout.column(align=True)
        col.label(text="Add:")
        col.operator("view3d.edit_mesh_extrude_move_normal", text="Extrude Region")
        col.operator("view3d.edit_mesh_extrude_individual_move", text="Extrude Individual")
        col.operator("mesh.subdivide")
        col.operator("mesh.loopcut_slide")
        col.operator("mesh.duplicate_move", text="Duplicate")
        col.operator("mesh.spin")
        col.operator("mesh.screw")

        col = layout.column(align=True)
        col.label(text="Remove:")
        col.operator("mesh.delete")
        col.operator("mesh.merge")
        col.operator("mesh.remove_doubles")

        col = layout.column(align=True)
        col.label(text="Normals:")
        col.operator("mesh.normals_make_consistent", text="Recalculate")
        col.operator("mesh.flip_normals", text="Flip Direction")

        col = layout.column(align=True)
        col.label(text="UV Mapping:")
        col.operator("wm.call_menu", text="Unwrap").name = "VIEW3D_MT_uv_map"
        col.operator("mesh.mark_seam")
        col.operator("mesh.mark_seam", text="Clear Seam").clear = True


        col = layout.column(align=True)
        col.label(text="Shading:")
        col.operator("mesh.faces_shade_smooth", text="Smooth")
        col.operator("mesh.faces_shade_flat", text="Flat")

        col = layout.column(align=True)
        col.label(text="Repeat:")
        col.operator("screen.repeat_last")
        col.operator("screen.repeat_history", text="History...")

        col = layout.column(align=True)
        col.label(text="Grease Pencil:")
        row = col.row()
        row.operator("gpencil.draw", text="Draw").mode = 'DRAW'
        row.operator("gpencil.draw", text="Line").mode = 'DRAW_STRAIGHT'
        row.operator("gpencil.draw", text="Erase").mode = 'ERASER'


class VIEW3D_PT_tools_meshedit_options(View3DPanel, bpy.types.Panel):
    bl_context = "mesh_edit"
    bl_label = "Mesh Options"

    def draw(self, context):
        layout = self.layout

        ob = context.active_object

        if ob:
            mesh = context.active_object.data
            col = layout.column(align=True)
            col.prop(mesh, "use_mirror_x")
            col.prop(mesh, "use_mirror_topology")
            col.prop(context.tool_settings, "edge_path_mode")

# ********** default tools for editmode_curve ****************


class VIEW3D_PT_tools_curveedit(View3DPanel, bpy.types.Panel):
    bl_context = "curve_edit"
    bl_label = "Curve Tools"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Transform:")
        col.operator("transform.translate")
        col.operator("transform.rotate")
        col.operator("transform.resize", text="Scale")

        col = layout.column(align=True)
        col.operator("transform.transform", text="Tilt").mode = 'TILT'
        col.operator("transform.transform", text="Shrink/Fatten").mode = 'CURVE_SHRINKFATTEN'

        col = layout.column(align=True)
        col.label(text="Curve:")
        col.operator("curve.duplicate")
        col.operator("curve.delete")
        col.operator("curve.cyclic_toggle")
        col.operator("curve.switch_direction")
        col.operator("curve.spline_type_set")

        col = layout.column(align=True)
        col.label(text="Handles:")
        row = col.row()
        row.operator("curve.handle_type_set", text="Auto").type = 'AUTOMATIC'
        row.operator("curve.handle_type_set", text="Vector").type = 'VECTOR'
        row = col.row()
        row.operator("curve.handle_type_set", text="Align").type = 'ALIGN'
        row.operator("curve.handle_type_set", text="Free").type = 'FREE_ALIGN'

        col = layout.column(align=True)
        col.label(text="Modeling:")
        col.operator("curve.extrude")
        col.operator("curve.subdivide")

        col = layout.column(align=True)
        col.label(text="Repeat:")
        col.operator("screen.repeat_last")
        col.operator("screen.repeat_history", text="History...")

        col = layout.column(align=True)
        col.label(text="Grease Pencil:")
        row = col.row()
        row.operator("gpencil.draw", text="Draw").mode = 'DRAW'
        row.operator("gpencil.draw", text="Line").mode = 'DRAW_STRAIGHT'
        row.operator("gpencil.draw", text="Erase").mode = 'ERASER'

# ********** default tools for editmode_surface ****************


class VIEW3D_PT_tools_surfaceedit(View3DPanel, bpy.types.Panel):
    bl_context = "surface_edit"
    bl_label = "Surface Tools"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Transform:")
        col.operator("transform.translate")
        col.operator("transform.rotate")
        col.operator("transform.resize", text="Scale")

        col = layout.column(align=True)
        col.label(text="Curve:")
        col.operator("curve.duplicate")
        col.operator("curve.delete")
        col.operator("curve.cyclic_toggle")
        col.operator("curve.switch_direction")

        col = layout.column(align=True)
        col.label(text="Modeling:")
        col.operator("curve.extrude")
        col.operator("curve.subdivide")

        col = layout.column(align=True)
        col.label(text="Repeat:")
        col.operator("screen.repeat_last")
        col.operator("screen.repeat_history", text="History...")

        col = layout.column(align=True)
        col.label(text="Grease Pencil:")
        row = col.row()
        row.operator("gpencil.draw", text="Draw").mode = 'DRAW'
        row.operator("gpencil.draw", text="Line").mode = 'DRAW_STRAIGHT'
        row.operator("gpencil.draw", text="Erase").mode = 'ERASER'

# ********** default tools for editmode_text ****************


class VIEW3D_PT_tools_textedit(View3DPanel, bpy.types.Panel):
    bl_context = "text_edit"
    bl_label = "Text Tools"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Text Edit:")
        col.operator("font.text_copy", text="Copy")
        col.operator("font.text_cut", text="Cut")
        col.operator("font.text_paste", text="Paste")

        col = layout.column(align=True)
        col.label(text="Set Case:")
        col.operator("font.case_set", text="To Upper").case = 'UPPER'
        col.operator("font.case_set", text="To Lower").case = 'LOWER'

        col = layout.column(align=True)
        col.label(text="Style:")
        col.operator("font.style_toggle", text="Bold").style = 'BOLD'
        col.operator("font.style_toggle", text="Italic").style = 'ITALIC'
        col.operator("font.style_toggle", text="Underline").style = 'UNDERLINE'

        col = layout.column(align=True)
        col.label(text="Repeat:")
        col.operator("screen.repeat_last")
        col.operator("screen.repeat_history", text="History...")


# ********** default tools for editmode_armature ****************


class VIEW3D_PT_tools_armatureedit(View3DPanel, bpy.types.Panel):
    bl_context = "armature_edit"
    bl_label = "Armature Tools"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Transform:")
        col.operator("transform.translate")
        col.operator("transform.rotate")
        col.operator("transform.resize", text="Scale")

        col = layout.column(align=True)
        col.label(text="Bones:")
        col.operator("armature.bone_primitive_add", text="Add")
        col.operator("armature.duplicate_move", text="Duplicate")
        col.operator("armature.delete", text="Delete")

        col = layout.column(align=True)
        col.label(text="Modeling:")
        col.operator("armature.extrude_move")
        col.operator("armature.subdivide_multi", text="Subdivide")

        col = layout.column(align=True)
        col.label(text="Repeat:")
        col.operator("screen.repeat_last")
        col.operator("screen.repeat_history", text="History...")

        col = layout.column(align=True)
        col.label(text="Grease Pencil:")
        row = col.row()
        row.operator("gpencil.draw", text="Draw").mode = 'DRAW'
        row.operator("gpencil.draw", text="Line").mode = 'DRAW_STRAIGHT'
        row.operator("gpencil.draw", text="Erase").mode = 'ERASER'


class VIEW3D_PT_tools_armatureedit_options(View3DPanel, bpy.types.Panel):
    bl_context = "armature_edit"
    bl_label = "Armature Options"

    def draw(self, context):
        layout = self.layout

        arm = context.active_object.data

        col = layout.column(align=True)
        col.prop(arm, "x_axis_mirror")

# ********** default tools for editmode_mball ****************


class VIEW3D_PT_tools_mballedit(View3DPanel, bpy.types.Panel):
    bl_context = "mball_edit"
    bl_label = "Meta Tools"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Transform:")
        col.operator("transform.translate")
        col.operator("transform.rotate")
        col.operator("transform.resize", text="Scale")

        col = layout.column(align=True)
        col.label(text="Repeat:")
        col.operator("screen.repeat_last")
        col.operator("screen.repeat_history", text="History...")

        col = layout.column(align=True)
        col.label(text="Grease Pencil:")
        row = col.row()
        row.operator("gpencil.draw", text="Draw").mode = 'DRAW'
        row.operator("gpencil.draw", text="Line").mode = 'DRAW_STRAIGHT'
        row.operator("gpencil.draw", text="Erase").mode = 'ERASER'

# ********** default tools for editmode_lattice ****************


class VIEW3D_PT_tools_latticeedit(View3DPanel, bpy.types.Panel):
    bl_context = "lattice_edit"
    bl_label = "Lattice Tools"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Transform:")
        col.operator("transform.translate")
        col.operator("transform.rotate")
        col.operator("transform.resize", text="Scale")

        col = layout.column(align=True)
        col.operator("lattice.make_regular")

        col = layout.column(align=True)
        col.label(text="Repeat:")
        col.operator("screen.repeat_last")
        col.operator("screen.repeat_history", text="History...")

        col = layout.column(align=True)
        col.label(text="Grease Pencil:")
        row = col.row()
        row.operator("gpencil.draw", text="Draw").mode = 'DRAW'
        row.operator("gpencil.draw", text="Line").mode = 'DRAW_STRAIGHT'
        row.operator("gpencil.draw", text="Erase").mode = 'ERASER'


# ********** default tools for posemode ****************


class VIEW3D_PT_tools_posemode(View3DPanel, bpy.types.Panel):
    bl_context = "posemode"
    bl_label = "Pose Tools"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Transform:")
        col.operator("transform.translate")
        col.operator("transform.rotate")
        col.operator("transform.resize", text="Scale")

        col = layout.column(align=True)
        col.label(text="In-Between:")
        row = col.row()
        row.operator("pose.push", text="Push")
        row.operator("pose.relax", text="Relax")
        col.operator("pose.breakdown", text="Breakdowner")

        col = layout.column(align=True)
        col.label(text="Pose:")
        row = col.row()
        row.operator("pose.copy", text="Copy")
        row.operator("pose.paste", text="Paste")

        col = layout.column(align=True)
        col.operator("poselib.pose_add", text="Add To Library")

        col = layout.column(align=True)
        col.label(text="Keyframes:")

        col.operator("anim.keyframe_insert_menu", text="Insert")
        col.operator("anim.keyframe_delete_v3d", text="Remove")

        col = layout.column(align=True)
        col.label(text="Repeat:")
        col.operator("screen.repeat_last")
        col.operator("screen.repeat_history", text="History...")

        col = layout.column(align=True)
        col.label(text="Grease Pencil:")
        row = col.row()
        row.operator("gpencil.draw", text="Draw").mode = 'DRAW'
        row.operator("gpencil.draw", text="Line").mode = 'DRAW_STRAIGHT'
        row.operator("gpencil.draw", text="Erase").mode = 'ERASER'


class VIEW3D_PT_tools_posemode_options(View3DPanel, bpy.types.Panel):
    bl_context = "posemode"
    bl_label = "Pose Options"

    def draw(self, context):
        layout = self.layout

        arm = context.active_object.data

        col = layout.column(align=True)
        col.prop(arm, "x_axis_mirror")
        col.prop(arm, "auto_ik")

# ********** default tools for paint modes ****************


class PaintPanel():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def paint_settings(self, context):
        ts = context.tool_settings

        if context.sculpt_object:
            return ts.sculpt
        elif context.vertex_paint_object:
            return ts.vertex_paint
        elif context.weight_paint_object:
            return ts.weight_paint
        elif context.texture_paint_object:
            return ts.image_paint
        elif context.particle_edit_object:
            return ts.particle_edit

        return False


class VIEW3D_PT_tools_brush(PaintPanel, bpy.types.Panel):
    bl_label = "Brush"

    def poll(self, context):
        return self.paint_settings(context)

    def draw(self, context):
        layout = self.layout

        settings = self.paint_settings(context)
        brush = settings.brush

        if not context.particle_edit_object:
            col = layout.split().column()

            if context.sculpt_object and context.tool_settings.sculpt:
                col.template_ID_preview(settings, "brush", new="brush.add", filter="is_sculpt_brush", rows=3, cols=8)
            elif context.texture_paint_object and context.tool_settings.image_paint:
                col.template_ID_preview(settings, "brush", new="brush.add", filter="is_imapaint_brush", rows=3, cols=8)
            elif context.vertex_paint_object and context.tool_settings.vertex_paint:
                col.template_ID_preview(settings, "brush", new="brush.add", filter="is_vpaint_brush", rows=3, cols=8)
            elif context.weight_paint_object and context.tool_settings.weight_paint:
                col.template_ID_preview(settings, "brush", new="brush.add", filter="is_wpaint_brush", rows=3, cols=8)
            else:
                row = col.row()

                if context.sculpt_object and brush:
                    defaultbrushes = 8
                elif context.texture_paint_object and brush:
                    defaultbrushes = 4
                else:
                    defaultbrushes = 7

                row.template_list(settings, "brushes", settings, "active_brush_index", rows=2, maxrows=defaultbrushes)

        # Particle Mode #

        # XXX This needs a check if psys is editable.
        if context.particle_edit_object:
            # XXX Select Particle System
            layout.column().prop(settings, "tool", expand=True)

            if settings.tool != 'NONE':
                col = layout.column()
                col.prop(brush, "size", slider=True)
                if settings.tool != 'ADD':
                    col.prop(brush, "strength", slider=True)

            if settings.tool == 'ADD':
                col.prop(brush, "count")
                col = layout.column()
                col.prop(settings, "add_interpolate")
                sub = col.column(align=True)
                sub.active = settings.add_interpolate
                sub.prop(brush, "steps", slider=True)
                sub.prop(settings, "add_keys", slider=True)
            elif settings.tool == 'LENGTH':
                layout.prop(brush, "length_mode", expand=True)
            elif settings.tool == 'PUFF':
                layout.prop(brush, "puff_mode", expand=True)
                layout.prop(brush, "use_puff_volume")

        # Sculpt Mode #

        elif context.sculpt_object and brush:

            col = layout.column()


            col.separator()

            row = col.row(align=True)

            if brush.use_locked_size:
                row.prop(brush, "use_locked_size", toggle=True, text="", icon='LOCKED')
                row.prop(brush, "unprojected_radius", text="Radius", slider=True)
            else:
                row.prop(brush, "use_locked_size", toggle=True, text="", icon='UNLOCKED')
                row.prop(brush, "size", text="Radius", slider=True)

            row.prop(brush, "use_size_pressure", toggle=True, text="")


            if brush.sculpt_tool not in ('SNAKE_HOOK', 'GRAB', 'ROTATE'):
                col.separator()

                row = col.row(align=True)

                if brush.use_space and brush.sculpt_tool not in ('SMOOTH'):
                    if brush.use_space_atten:
                        row.prop(brush, "use_space_atten", toggle=True, text="", icon='LOCKED')
                    else:
                        row.prop(brush, "use_space_atten", toggle=True, text="", icon='UNLOCKED')

                row.prop(brush, "strength", text="Strength", slider=True)
                row.prop(brush, "use_strength_pressure", text="")



            if brush.sculpt_tool not in ('SMOOTH'):
                col.separator()

                row = col.row(align=True)
                row.prop(brush, "autosmooth_factor", slider=True)
                row.prop(brush, "use_inverse_smooth_pressure", toggle=True, text="")



            if brush.sculpt_tool in ('GRAB', 'SNAKE_HOOK'):
                col.separator()

                row = col.row(align=True)
                row.prop(brush, "normal_weight", slider=True)



            if brush.sculpt_tool in ('CREASE', 'BLOB'):
                col.separator()

                row = col.row(align=True)
                row.prop(brush, "crease_pinch_factor", slider=True, text="Pinch")

            if brush.sculpt_tool not in ('PINCH', 'INFLATE', 'SMOOTH'):
                row = col.row(align=True)

                col.separator()

                if brush.use_original_normal:
                    row.prop(brush, "use_original_normal", toggle=True, text="", icon='LOCKED')
                else:
                    row.prop(brush, "use_original_normal", toggle=True, text="", icon='UNLOCKED')

                row.prop(brush, "sculpt_plane", text="")

            #if brush.sculpt_tool in ('CLAY', 'CLAY_TUBES', 'FLATTEN', 'FILL', 'SCRAPE'):
            if brush.sculpt_tool in ('CLAY', 'FLATTEN', 'FILL', 'SCRAPE'):
                row = col.row(align=True)
                row.prop(brush, "plane_offset", slider=True)
                row.prop(brush, "use_offset_pressure", text="")

                col.separator()

                row= col.row()
                row.prop(brush, "use_plane_trim", text="Trim")
                row= col.row()
                row.active=brush.use_plane_trim
                row.prop(brush, "plane_trim", slider=True, text="Distance")

            col.separator()

            row= col.row()
            row.prop(brush, "use_frontface", text="Front Faces Only")

            col.separator()
            col.row().prop(brush, "direction", expand=True)

            if brush.sculpt_tool in ('DRAW', 'CREASE', 'BLOB', 'INFLATE', 'LAYER', 'CLAY'):
                col.separator()

                col.prop(brush, "use_accumulate")



            if brush.sculpt_tool == 'LAYER':
                col.separator()

                ob = context.sculpt_object
                do_persistent = True

                # not supported yet for this case
                for md in ob.modifiers:
                    if md.type == 'MULTIRES':
                        do_persistent = False

                if do_persistent:
                    col.prop(brush, "use_persistent")
                    col.operator("sculpt.set_persistent_base")

        # Texture Paint Mode #

        elif context.texture_paint_object and brush:
            col = layout.column()
            col.template_color_wheel(brush, "color", value_slider=True)
            col.prop(brush, "color", text="")

            row = col.row(align=True)
            row.prop(brush, "size", text="Radius", slider=True)
            row.prop(brush, "use_size_pressure", toggle=True, text="")

            row = col.row(align=True)
            row.prop(brush, "strength", text="Strength", slider=True)
            row.prop(brush, "use_strength_pressure", toggle=True, text="")

            row = col.row(align=True)
            row.prop(brush, "jitter", slider=True)
            row.prop(brush, "use_jitter_pressure", toggle=True, text="")

            col.prop(brush, "blend", text="Blend")

            col = layout.column()
            col.active = (brush.blend not in ('ERASE_ALPHA', 'ADD_ALPHA'))
            col.prop(brush, "use_alpha")


        # Weight Paint Mode #

        elif context.weight_paint_object and brush:
            layout.prop(context.tool_settings, "vertex_group_weight", text="Weight", slider=True)
            layout.prop(context.tool_settings, "auto_normalize", text="Auto Normalize")

            col = layout.column()

            row = col.row(align=True)
            row.prop(brush, "size", text="Radius", slider=True)
            row.prop(brush, "use_size_pressure", toggle=True, text="")

            row = col.row(align=True)
            row.prop(brush, "strength", text="Strength", slider=True)
            row.prop(brush, "use_strength_pressure", toggle=True, text="")

            row = col.row(align=True)
            row.prop(brush, "jitter", slider=True)
            row.prop(brush, "use_jitter_pressure", toggle=True, text="")

        # Vertex Paint Mode #

        elif context.vertex_paint_object and brush:
            col = layout.column()
            col.template_color_wheel(brush, "color", value_slider=True)
            col.prop(brush, "color", text="")

            row = col.row(align=True)
            row.prop(brush, "size", text="Radius", slider=True)
            row.prop(brush, "use_size_pressure", toggle=True, text="")

            row = col.row(align=True)
            row.prop(brush, "strength", text="Strength", slider=True)
            row.prop(brush, "use_strength_pressure", toggle=True, text="")

            # XXX - TODO
            #row = col.row(align=True)
            #row.prop(brush, "jitter", slider=True)
            #row.prop(brush, "use_jitter_pressure", toggle=True, text="")


class VIEW3D_PT_tools_brush_texture(PaintPanel, bpy.types.Panel):
    bl_label = "Texture"
    bl_default_closed = True

    def poll(self, context):
        settings = self.paint_settings(context)
        return (settings and settings.brush and (context.sculpt_object or
                             context.texture_paint_object))

    def draw(self, context):
        layout = self.layout

        settings = self.paint_settings(context)
        brush = settings.brush
        tex_slot = brush.texture_slot

        col = layout.column()

        col.template_ID_preview(brush, "texture", new="texture.new", rows=3, cols=8)

        if context.sculpt_object:
            #XXX duplicated from properties_texture.py

            wide_ui = context.region.width > narrowui


            col.separator()


            col.label(text="Brush Mapping:")
            row = col.row(align=True)
            row.prop(tex_slot, "map_mode", expand=True)

            col.separator()

            col = layout.column()
            col.active = tex_slot.map_mode in ('FIXED')
            col.label(text="Angle:")
            
            col = layout.column()
            if not brush.use_anchor and brush.sculpt_tool not in ('GRAB', 'SNAKE_HOOK', 'THUMB', 'ROTATE') and tex_slot.map_mode in ('FIXED'):
                col.prop(brush, "texture_angle_source", text="")
            else:
                col.prop(brush, "texture_angle_source_no_random", text="")

            #row = col.row(align=True)
            #row.label(text="Angle:")
            #row.active = tex_slot.map_mode in ('FIXED', 'TILED')

            #row = col.row(align=True)

            #col = row.column()
            #col.active = tex_slot.map_mode in ('FIXED')
            #col.prop(brush, "use_rake", toggle=True, icon='PARTICLEMODE', text="")

            col = layout.column()
            col.prop(tex_slot, "angle", text="")
            col.active = tex_slot.map_mode in ('FIXED', 'TILED')

            #col = layout.column()
            #col.prop(brush, "use_random_rotation")
            #col.active = (not brush.use_rake) and (not brush.use_anchor) and brush.sculpt_tool not in ('GRAB', 'SNAKE_HOOK', 'THUMB', 'ROTATE') and tex_slot.map_mode in ('FIXED')

            split = layout.split()

            col = split.column()
            col.prop(tex_slot, "offset")

            if wide_ui:
                col = split.column()
            else:
                col.separator()

            col.prop(tex_slot, "size")

            col = layout.column()

            row = col.row(align=True)
            row.label(text="Sample Bias:")
            row = col.row(align=True)
            row.prop(brush, "texture_sample_bias", slider=True, text="")

            row = col.row(align=True)
            row.label(text="Overlay:")
            row.active = tex_slot.map_mode in ('FIXED', 'TILED')

            row = col.row(align=True)

            col = row.column()

            if brush.use_texture_overlay:
                col.prop(brush, "use_texture_overlay", toggle=True, text="", icon='MUTE_IPO_OFF')
            else:
                col.prop(brush, "use_texture_overlay", toggle=True, text="", icon='MUTE_IPO_ON')

            col.active = tex_slot.map_mode in ('FIXED', 'TILED')

            col = row.column()
            col.prop(brush, "texture_overlay_alpha", text="Alpha")
            col.active = tex_slot.map_mode in ('FIXED', 'TILED') and brush.use_texture_overlay


class VIEW3D_PT_tools_brush_tool(PaintPanel, bpy.types.Panel):
    bl_label = "Tool"
    bl_default_closed = True

    def poll(self, context):
        settings = self.paint_settings(context)
        return (settings and settings.brush and
            (context.sculpt_object or context.texture_paint_object or
            context.vertex_paint_object or context.weight_paint_object))

    def draw(self, context):
        layout = self.layout

        settings = self.paint_settings(context)
        brush = settings.brush
        texture_paint = context.texture_paint_object
        sculpt = context.sculpt_object

        col = layout.column(align=True)

        if context.sculpt_object:
            col.prop(brush, "sculpt_tool", expand=False, text="")
            col.operator("brush.reset")
        elif context.texture_paint_object:
            col.prop(brush, "imagepaint_tool", expand=False, text="")
        elif context.vertex_paint_object or context.weight_paint_object:
            col.prop(brush, "vertexpaint_tool", expand=False, text="")


class VIEW3D_PT_tools_brush_stroke(PaintPanel, bpy.types.Panel):
    bl_label = "Stroke"
    bl_default_closed = True

    def poll(self, context):
        settings = self.paint_settings(context)
        return (settings and settings.brush and (context.sculpt_object or
                             context.vertex_paint_object or
                             context.weight_paint_object or
                             context.texture_paint_object))

    def draw(self, context):
        layout = self.layout

        settings = self.paint_settings(context)
        brush = settings.brush
        texture_paint = context.texture_paint_object

        col = layout.column()

        if context.sculpt_object:
            col.label(text="Stroke Method:")
            col.prop(brush, "stroke_method", text="")

            if brush.use_anchor:
                col.separator()
                row = col.row()
                row.prop(brush, "edge_to_edge", "Edge To Edge")

            if brush.use_airbrush:
                col.separator()
                row = col.row()
                row.prop(brush, "rate", text="Rate", slider=True)

            if brush.use_space:
                col.separator()
                row = col.row()
                row.active = brush.use_space
                row.prop(brush, "spacing", text="Spacing")

            if brush.sculpt_tool not in ('GRAB', 'THUMB', 'SNAKE_HOOK', 'ROTATE') and (not brush.use_anchor) and (not brush.restore_mesh):
                col = layout.column()
                col.separator()

                col.prop(brush, "use_smooth_stroke")

                sub = col.column()
                sub.active = brush.use_smooth_stroke
                sub.prop(brush, "smooth_stroke_radius", text="Radius", slider=True)
                sub.prop(brush, "smooth_stroke_factor", text="Factor", slider=True)

                col.separator()

                row = col.row(align=True)
                row.prop(brush, "jitter", slider=True)
                row.prop(brush, "use_jitter_pressure", toggle=True, text="")

        else:
            row = col.row()
            row.prop(brush, "use_airbrush")

            row = col.row()
            row.active = brush.use_airbrush and (not brush.use_space) and (not brush.use_anchor)
            row.prop(brush, "rate", slider=True)

            col.separator()

            if not texture_paint:
                row = col.row()
                row.prop(brush, "use_smooth_stroke")

                col = layout.column()
                col.active = brush.use_smooth_stroke
                col.prop(brush, "smooth_stroke_radius", text="Radius", slider=True)
                col.prop(brush, "smooth_stroke_factor", text="Factor", slider=True)

            col.separator()

            col = layout.column()
            col.active = (not brush.use_anchor) and (brush.sculpt_tool not in ('GRAB', 'THUMB', 'ROTATE', 'SNAKE_HOOK'))

            row = col.row()
            row.prop(brush, "use_space")

            row = col.row()
            row.active = brush.use_space
            row.prop(brush, "spacing", text="Spacing")

            #col.prop(brush, "use_space_atten", text="Adaptive Strength")
            #col.prop(brush, "use_adaptive_space", text="Adaptive Spacing")

            #col.separator()

            #if texture_paint:
            #    row.prop(brush, "use_spacing_pressure", toggle=True, text="")


class VIEW3D_PT_tools_brush_curve(PaintPanel, bpy.types.Panel):
    bl_label = "Curve"
    bl_default_closed = True

    def poll(self, context):
        settings = self.paint_settings(context)
        return (settings and settings.brush and settings.brush.curve)

    def draw(self, context):
        layout = self.layout

        settings = self.paint_settings(context)
        brush = settings.brush

        layout.template_curve_mapping(brush, "curve", brush=True)

        row = layout.row(align=True)
        row.operator("brush.curve_preset", icon="SMOOTHCURVE", text="").shape = 'SMOOTH'
        row.operator("brush.curve_preset", icon="SPHERECURVE", text="").shape = 'ROUND'
        row.operator("brush.curve_preset", icon="ROOTCURVE", text="").shape = 'ROOT'
        row.operator("brush.curve_preset", icon="SHARPCURVE", text="").shape = 'SHARP'
        row.operator("brush.curve_preset", icon="LINCURVE", text="").shape = 'LINE'
        row.operator("brush.curve_preset", icon="NOCURVE", text="").shape = 'MAX'

class VIEW3D_PT_sculpt_options(PaintPanel, bpy.types.Panel):
    bl_label = "Options"
    bl_default_closed = True

    def poll(self, context):
        return (context.sculpt_object and context.tool_settings.sculpt)

    def draw(self, context):
        layout = self.layout

        wide_ui = context.region.width > narrowui

        tool_settings = context.tool_settings
        sculpt = tool_settings.sculpt
        settings = self.paint_settings(context)
        brush = settings.brush

        split = layout.split()

        col = split.column()

        col.prop(sculpt, "use_openmp", text="Threaded Sculpt")
        col.prop(sculpt, "fast_navigate")
        col.prop(sculpt, "show_brush")

        col.label(text="Unified Settings:")
        col.prop(tool_settings, "sculpt_paint_use_unified_size", text="Size")
        col.prop(tool_settings, "sculpt_paint_use_unified_strength", text="Strength")

        if wide_ui:
            col = split.column()
        else:
            col.separator()

        col.label(text="Lock:")
        row = col.row(align=True)
        row.prop(sculpt, "lock_x", text="X", toggle=True)
        row.prop(sculpt, "lock_y", text="Y", toggle=True)
        row.prop(sculpt, "lock_z", text="Z", toggle=True)

		
		
class VIEW3D_PT_sculpt_symmetry(PaintPanel):
    bl_label = "Symmetry"
    bl_default_closed = True

    def poll(self, context):
        return (context.sculpt_object and context.tool_settings.sculpt)

    def draw(self, context):
        wide_ui = context.region.width > narrowui

        layout = self.layout

        sculpt = context.tool_settings.sculpt
        settings = self.paint_settings(context)
        brush = settings.brush

        split = layout.split()

        col = split.column()

        col.label(text="Mirror:")
        col.prop(sculpt, "symmetry_x", text="X")
        col.prop(sculpt, "symmetry_y", text="Y")
        col.prop(sculpt, "symmetry_z", text="Z")

        if wide_ui:
            col = split.column()
        else:
            col.separator()

        col.prop(sculpt, "radial_symm", text="Radial")

        col = layout.column()

        col.separator()

        col.prop(sculpt, "use_symmetry_feather", text="Feather")

class VIEW3D_PT_tools_brush_appearance(PaintPanel):
    bl_label = "Appearance"
    bl_default_closed = True

    def poll(self, context):
        return (context.sculpt_object and context.tool_settings.sculpt) or (context.vertex_paint_object and context.tool_settings.vertex_paint) or (context.weight_paint_object and context.tool_settings.weight_paint) or (context.texture_paint_object and context.tool_settings.image_paint)

    def draw(self, context):
        layout = self.layout

        sculpt = context.tool_settings.sculpt
        settings = self.paint_settings(context)
        brush = settings.brush

        col = layout.column();

        if context.sculpt_object and context.tool_settings.sculpt:
            #if brush.sculpt_tool in ('DRAW', 'INFLATE', 'CLAY', 'PINCH', 'CREASE', 'BLOB', 'FLATTEN', 'FILL', 'SCRAPE', 'CLAY_TUBES'):
            if brush.sculpt_tool in ('DRAW', 'INFLATE', 'CLAY', 'PINCH', 'CREASE', 'BLOB', 'FLATTEN', 'FILL', 'SCRAPE'):
                col.prop(brush, "add_col", text="Add Color")
                col.prop(brush, "sub_col", text="Subtract Color")
            else:
                col.prop(brush, "add_col", text="Color")
        else:
            col.prop(brush, "add_col", text="Color")

        col = layout.column()
        col.label(text="Icon:")

        row = col.row(align=True)
        row.prop(brush, "use_custom_icon")
        if brush.use_custom_icon:
            row = col.row(align=True)
            row.prop(brush, "icon_filepath", text="")

# ********** default tools for weightpaint ****************


class VIEW3D_PT_tools_weightpaint(View3DPanel, bpy.types.Panel):
    bl_context = "weightpaint"
    bl_label = "Weight Tools"

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        col.operator("object.vertex_group_normalize_all", text="Normalize All")
        col.operator("object.vertex_group_normalize", text="Normalize")
        col.operator("object.vertex_group_invert", text="Invert")
        col.operator("object.vertex_group_clean", text="Clean")
        col.operator("object.vertex_group_levels", text="Levels")


class VIEW3D_PT_tools_weightpaint_options(View3DPanel, bpy.types.Panel):
    bl_context = "weightpaint"
    bl_label = "Options"

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        wpaint = tool_settings.weight_paint

        col = layout.column()
        col.prop(wpaint, "all_faces")
        col.prop(wpaint, "normals")
        col.prop(wpaint, "spray")

        obj = context.weight_paint_object
        if obj.type == 'MESH':
            mesh = obj.data
            col.prop(mesh, "use_mirror_x")
            col.prop(mesh, "use_mirror_topology")

        col.label(text="Unified Settings:")
        col.prop(tool_settings, "sculpt_paint_use_unified_size", text="Size")
        col.prop(tool_settings, "sculpt_paint_use_unified_strength", text="Strength")

# Commented out because the Apply button isn't an operator yet, making these settings useless
#		col.label(text="Gamma:")
#		col.prop(wpaint, "gamma", text="")
#		col.label(text="Multiply:")
#		col.prop(wpaint, "mul", text="")

# Also missing now:
# Soft, Vgroup, X-Mirror and "Clear" Operator.

# ********** default tools for vertexpaint ****************


class VIEW3D_PT_tools_vertexpaint(View3DPanel, bpy.types.Panel):
    bl_context = "vertexpaint"
    bl_label = "Options"

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        vpaint = tool_settings.vertex_paint

        col = layout.column()
        #col.prop(vpaint, "mode", text="")
        col.prop(vpaint, "all_faces")
        col.prop(vpaint, "normals")
        col.prop(vpaint, "spray")

        col.label(text="Unified Settings:")
        col.prop(tool_settings, "sculpt_paint_use_unified_size", text="Size")
        col.prop(tool_settings, "sculpt_paint_use_unified_strength", text="Strength")

# Commented out because the Apply button isn't an operator yet, making these settings useless
#		col.label(text="Gamma:")
#		col.prop(vpaint, "gamma", text="")
#		col.label(text="Multiply:")
#		col.prop(vpaint, "mul", text="")

# ********** default tools for texturepaint ****************


class VIEW3D_PT_tools_projectpaint(View3DPanel, bpy.types.Panel):
    bl_context = "texturepaint"
    bl_label = "Project Paint"

    def poll(self, context):
        return context.tool_settings.image_paint.brush.imagepaint_tool != 'SMEAR'

    def draw_header(self, context):
        ipaint = context.tool_settings.image_paint

        self.layout.prop(ipaint, "use_projection", text="")

    def draw(self, context):
        layout = self.layout

        ipaint = context.tool_settings.image_paint
        settings = context.tool_settings.image_paint
        use_projection = ipaint.use_projection

        col = layout.column()
        sub = col.column()
        sub.active = use_projection
        sub.prop(ipaint, "use_occlude")
        sub.prop(ipaint, "use_backface_cull")

        split = layout.split()

        col = split.column()
        col.active = (use_projection)
        col.prop(ipaint, "use_normal_falloff")

        col = split.column()
        col.active = (ipaint.use_normal_falloff and use_projection)
        col.prop(ipaint, "normal_angle", text="")

        col = layout.column(align=False)
        row = col.row()
        row.active = (use_projection)
        row.prop(ipaint, "use_stencil_layer", text="Stencil")

        row2 = row.row(align=False)
        row2.active = (use_projection and ipaint.use_stencil_layer)
        row2.menu("VIEW3D_MT_tools_projectpaint_stencil", text=context.active_object.data.uv_texture_stencil.name)
        row2.prop(ipaint, "invert_stencil", text="", icon='IMAGE_ALPHA')

        col = layout.column()
        sub = col.column()
        row = sub.row()
        row.active = (settings.brush.imagepaint_tool == 'CLONE')

        row.prop(ipaint, "use_clone_layer", text="Layer")
        row.menu("VIEW3D_MT_tools_projectpaint_clone", text=context.active_object.data.uv_texture_clone.name)

        sub = col.column()
        sub.prop(ipaint, "seam_bleed")

        col.label(text="External Editing")
        row = col.split(align=True, percentage=0.55)
        row.operator("image.project_edit", text="Quick Edit")
        row.operator("image.project_apply", text="Apply")
        row = col.row(align=True)
        row.prop(ipaint, "screen_grab_size", text="")

        sub = col.column()
        sub.operator("paint.project_image", text="Apply Camera Image")

        sub.operator("image.save_dirty", text="Save All Edited")


class VIEW3D_PT_imagepaint_options(PaintPanel):
    bl_label = "Options"
    bl_default_closed = True

    def poll(self, context):
        return (context.texture_paint_object and context.tool_settings.image_paint)

    def draw(self, context):
        layout = self.layout

        col = layout.column()

        tool_settings = context.tool_settings
        col.label(text="Unified Settings:")
        col.prop(tool_settings, "sculpt_paint_use_unified_size", text="Size")
        col.prop(tool_settings, "sculpt_paint_use_unified_strength", text="Strength")
        
class VIEW3D_MT_tools_projectpaint_clone(bpy.types.Menu):
    bl_label = "Clone Layer"

    def draw(self, context):
        layout = self.layout
        for i, tex in enumerate(context.active_object.data.uv_textures):
            prop = layout.operator("wm.context_set_int", text=tex.name)
            prop.data_path = "active_object.data.uv_texture_clone_index"
            prop.value = i


class VIEW3D_MT_tools_projectpaint_stencil(bpy.types.Menu):
    bl_label = "Mask Layer"

    def draw(self, context):
        layout = self.layout
        for i, tex in enumerate(context.active_object.data.uv_textures):
            prop = layout.operator("wm.context_set_int", text=tex.name)
            prop.data_path = "active_object.data.uv_texture_stencil_index"
            prop.value = i


class VIEW3D_PT_tools_particlemode(View3DPanel, bpy.types.Panel):
    '''default tools for particle mode'''
    bl_context = "particlemode"
    bl_label = "Options"

    def draw(self, context):
        layout = self.layout

        pe = context.tool_settings.particle_edit
        ob = pe.object

        layout.prop(pe, "type", text="")

        ptcache = None

        if pe.type == 'PARTICLES':
            if ob.particle_systems:
                if len(ob.particle_systems) > 1:
                    layout.template_list(ob, "particle_systems", ob, "active_particle_system_index", type='ICONS')

                ptcache = ob.particle_systems[ob.active_particle_system_index].point_cache
        else:
            for md in ob.modifiers:
                if md.type == pe.type:
                    ptcache = md.point_cache

        if ptcache and len(ptcache.point_cache_list) > 1:
            layout.template_list(ptcache, "point_cache_list", ptcache, "active_point_cache_index", type='ICONS')


        if not pe.editable:
            layout.label(text="Point cache must be baked")
            layout.label(text="to enable editing!")

        col = layout.column(align=True)
        if pe.hair:
            col.active = pe.editable
            col.prop(pe, "emitter_deflect", text="Deflect emitter")
            sub = col.row()
            sub.active = pe.emitter_deflect
            sub.prop(pe, "emitter_distance", text="Distance")

        col = layout.column(align=True)
        col.active = pe.editable
        col.label(text="Keep:")
        col.prop(pe, "keep_lengths", text="Lengths")
        col.prop(pe, "keep_root", text="Root")
        if not pe.hair:
            col.label(text="Correct:")
            col.prop(pe, "auto_velocity", text="Velocity")
        col.prop(ob.data, "use_mirror_x")

        col = layout.column(align=True)
        col.active = pe.editable
        col.label(text="Draw:")
        col.prop(pe, "draw_step", text="Path Steps")
        if pe.hair:
            col.prop(pe, "draw_particles", text="Children")
        else:
            if pe.type == 'PARTICLES':
                col.prop(pe, "draw_particles", text="Particles")
            col.prop(pe, "fade_time")
            sub = col.row()
            sub.active = pe.fade_time
            sub.prop(pe, "fade_frames", slider=True)


def register():
    pass


def unregister():
    pass

if __name__ == "__main__":
    register()
