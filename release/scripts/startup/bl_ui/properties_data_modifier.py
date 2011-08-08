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


class ModifierButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "modifier"


class DATA_PT_modifiers(ModifierButtonsPanel, bpy.types.Panel):
    bl_label = "Modifiers"

    def draw(self, context):
        layout = self.layout

        ob = context.object

        layout.operator_menu_enum("object.modifier_add", "type")

        for md in ob.modifiers:
            box = layout.template_modifier(md)
            if box:
                # match enum type to our functions, avoids a lookup table.
                getattr(self, md.type)(box, ob, md)

    # the mt.type enum is (ab)used for a lookup on function names
    # ...to avoid lengthy if statements
    # so each type must have a function here.

    def ARMATURE(self, layout, ob, md):
        split = layout.split()

        col = split.column()
        col.label(text="Object:")
        col.prop(md, "object", text="")
        col.prop(md, "use_deform_preserve_volume")

        col = split.column()
        col.label(text="Bind To:")
        col.prop(md, "use_vertex_groups", text="Vertex Groups")
        col.prop(md, "use_bone_envelopes", text="Bone Envelopes")

        layout.separator()

        row = layout.row()
        row.prop_search(md, "vertex_group", ob, "vertex_groups", text="")
        sub = row.row()
        sub.active = bool(md.vertex_group)
        sub.prop(md, "invert_vertex_group")

        layout.prop(md, "use_multi_modifier")

    def ARRAY(self, layout, ob, md):
        layout.prop(md, "fit_type")

        if md.fit_type == 'FIXED_COUNT':
            layout.prop(md, "count")
        elif md.fit_type == 'FIT_LENGTH':
            layout.prop(md, "fit_length")
        elif md.fit_type == 'FIT_CURVE':
            layout.prop(md, "curve")

        layout.separator()

        split = layout.split()

        col = split.column()
        col.prop(md, "use_constant_offset")
        sub = col.column()
        sub.active = md.use_constant_offset
        sub.prop(md, "constant_offset_displace", text="")

        col.separator()

        col.prop(md, "use_merge_vertices", text="Merge")
        sub = col.column()
        sub.active = md.use_merge_vertices
        sub.prop(md, "use_merge_vertices_cap", text="First Last")
        sub.prop(md, "merge_threshold", text="Distance")

        col = split.column()
        col.prop(md, "use_relative_offset")
        sub = col.column()
        sub.active = md.use_relative_offset
        sub.prop(md, "relative_offset_displace", text="")

        col.separator()

        col.prop(md, "use_object_offset")
        sub = col.column()
        sub.active = md.use_object_offset
        sub.prop(md, "offset_object", text="")

        layout.separator()

        layout.prop(md, "start_cap")
        layout.prop(md, "end_cap")

    def BEVEL(self, layout, ob, md):
        split = layout.split()

        split.prop(md, "width")
        split.prop(md, "use_only_vertices")

        layout.label(text="Limit Method:")
        layout.row().prop(md, "limit_method", expand=True)
        if md.limit_method == 'ANGLE':
            layout.prop(md, "angle_limit")
        elif md.limit_method == 'WEIGHT':
            layout.row().prop(md, "edge_weight_method", expand=True)

    def BOOLEAN(self, layout, ob, md):
        split = layout.split()

        col = split.column()
        col.label(text="Operation:")
        col.prop(md, "operation", text="")

        col = split.column()
        col.label(text="Object:")
        col.prop(md, "object", text="")

    def BUILD(self, layout, ob, md):
        split = layout.split()

        col = split.column()
        col.prop(md, "frame_start")
        col.prop(md, "frame_duration")

        col = split.column()
        col.prop(md, "use_random_order")
        sub = col.column()
        sub.active = md.use_random_order
        sub.prop(md, "seed")

    def CAST(self, layout, ob, md):
        split = layout.split(percentage=0.25)

        split.label(text="Cast Type:")
        split.prop(md, "cast_type", text="")

        split = layout.split(percentage=0.25)

        col = split.column()
        col.prop(md, "use_x")
        col.prop(md, "use_y")
        col.prop(md, "use_z")

        col = split.column()
        col.prop(md, "factor")
        col.prop(md, "radius")
        col.prop(md, "size")
        col.prop(md, "use_radius_as_size")

        split = layout.split()

        col = split.column()
        col.label(text="Vertex Group:")
        col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")
        col = split.column()
        col.label(text="Control Object:")
        col.prop(md, "object", text="")
        if md.object:
            col.prop(md, "use_transform")

    def CLOTH(self, layout, ob, md):
        layout.label(text="Settings can be found inside the Physics context")

    def COLLISION(self, layout, ob, md):
        layout.label(text="Settings can be found inside the Physics context")

    def CURVE(self, layout, ob, md):
        split = layout.split()

        col = split.column()
        col.label(text="Object:")
        col.prop(md, "object", text="")
        col = split.column()
        col.label(text="Vertex Group:")
        col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")
        layout.label(text="Deformation Axis:")
        layout.row().prop(md, "deform_axis", expand=True)

    def DECIMATE(self, layout, ob, md):
        layout.prop(md, "ratio")
        layout.label(text="Face Count: %s" % str(md.face_count))

    def DISPLACE(self, layout, ob, md):
        split = layout.split()

        col = split.column()
        col.label(text="Texture:")
        col.template_ID(md, "texture", new="texture.new")
        col.label(text="Vertex Group:")
        col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")

        col = split.column()
        col.label(text="Direction:")
        col.prop(md, "direction", text="")
        col.label(text="Texture Coordinates:")
        col.prop(md, "texture_coords", text="")
        if md.texture_coords == 'OBJECT':
            layout.prop(md, "texture_coords_object", text="Object")
        elif md.texture_coords == 'UV' and ob.type == 'MESH':
            layout.prop_search(md, "uv_layer", ob.data, "uv_textures")

        layout.separator()

        row = layout.row()
        row.prop(md, "mid_level")
        row.prop(md, "strength")

    def EDGE_SPLIT(self, layout, ob, md):
        split = layout.split()

        col = split.column()
        col.prop(md, "use_edge_angle", text="Edge Angle")
        sub = col.column()
        sub.active = md.use_edge_angle
        sub.prop(md, "split_angle")

        split.prop(md, "use_edge_sharp", text="Sharp Edges")

    def EXPLODE(self, layout, ob, md):
        split = layout.split()

        col = split.column()
        col.label(text="Vertex group:")
        col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")
        sub = col.column()
        sub.active = bool(md.vertex_group)
        sub.prop(md, "protect")
        col.label(text="Particle UV")
        col.prop_search(md, "particle_uv", ob.data, "uv_textures", text="")

        col = split.column()
        col.prop(md, "use_edge_cut")
        col.prop(md, "show_unborn")
        col.prop(md, "show_alive")
        col.prop(md, "show_dead")
        col.prop(md, "use_size")

        layout.operator("object.explode_refresh", text="Refresh")

    def FLUID_SIMULATION(self, layout, ob, md):
        layout.label(text="Settings can be found inside the Physics context")

    def HOOK(self, layout, ob, md):
        split = layout.split()

        col = split.column()
        col.label(text="Object:")
        col.prop(md, "object", text="")
        if md.object and md.object.type == 'ARMATURE':
            col.label(text="Bone:")
            col.prop_search(md, "subtarget", md.object.data, "bones", text="")
        col = split.column()
        col.label(text="Vertex Group:")
        col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")

        layout.separator()

        split = layout.split()

        col = split.column()
        col.prop(md, "falloff")
        col.prop(md, "force", slider=True)

        col = split.column()
        col.operator("object.hook_reset", text="Reset")
        col.operator("object.hook_recenter", text="Recenter")

        if ob.mode == 'EDIT':
            layout.separator()
            row = layout.row()
            row.operator("object.hook_select", text="Select")
            row.operator("object.hook_assign", text="Assign")

    def LATTICE(self, layout, ob, md):
        split = layout.split()

        col = split.column()
        col.label(text="Object:")
        col.prop(md, "object", text="")

        col = split.column()
        col.label(text="Vertex Group:")
        col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")

    def MASK(self, layout, ob, md):
        split = layout.split()

        col = split.column()
        col.label(text="Mode:")
        col.prop(md, "mode", text="")
        col = split.column()
        if md.mode == 'ARMATURE':
            col.label(text="Armature:")
            col.prop(md, "armature", text="")
        elif md.mode == 'VERTEX_GROUP':
            col.label(text="Vertex Group:")
            col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")

        sub = col.column()
        sub.active = bool(md.vertex_group)
        sub.prop(md, "invert_vertex_group")

    def MESH_DEFORM(self, layout, ob, md):
        split = layout.split()

        col = split.column()
        sub = col.column()
        sub.label(text="Object:")
        sub.prop(md, "object", text="")
        sub.active = not md.is_bound
        col = split.column()
        col.label(text="Vertex Group:")
        col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")

        sub = col.column()
        sub.active = bool(md.vertex_group)
        sub.prop(md, "invert_vertex_group")

        layout.separator()

        if md.is_bound:
            layout.operator("object.meshdeform_bind", text="Unbind")
        else:
            layout.operator("object.meshdeform_bind", text="Bind")

            row = layout.row()
            row.prop(md, "precision")
            row.prop(md, "use_dynamic_bind")

    def MIRROR(self, layout, ob, md):
        split = layout.split(percentage=0.25)

        col = split.column()
        col.label(text="Axis:")
        col.prop(md, "use_x")
        col.prop(md, "use_y")
        col.prop(md, "use_z")

        col = split.column()
        col.label(text="Options:")
        col.prop(md, "use_mirror_merge", text="Merge")
        col.prop(md, "use_clip", text="Clipping")
        col.prop(md, "use_mirror_vertex_groups", text="Vertex Groups")

        col = split.column()
        col.label(text="Textures:")
        col.prop(md, "use_mirror_u", text="U")
        col.prop(md, "use_mirror_v", text="V")

        col = layout.column()

        if md.use_mirror_merge == True:
            col.prop(md, "merge_threshold")
        col.label(text="Mirror Object:")
        col.prop(md, "mirror_object", text="")

    def MULTIRES(self, layout, ob, md):
        layout.row().prop(md, "subdivision_type", expand=True)

        split = layout.split()
        col = split.column()
        col.prop(md, "levels", text="Preview")
        col.prop(md, "sculpt_levels", text="Sculpt")
        col.prop(md, "render_levels", text="Render")

        col = split.column()

        col.enabled = ob.mode != 'EDIT'
        col.operator("object.multires_subdivide", text="Subdivide")
        col.operator("object.multires_higher_levels_delete", text="Delete Higher")
        col.operator("object.multires_reshape", text="Reshape")
        col.operator("object.multires_base_apply", text="Apply Base")
        col.prop(md, "use_subsurf_uv")
        col.prop(md, "show_only_control_edges")

        layout.separator()

        col = layout.column()
        row = col.row()
        if md.is_external:
            row.operator("object.multires_external_pack", text="Pack External")
            row.label()
            row = col.row()
            row.prop(md, "filepath", text="")
        else:
            row.operator("object.multires_external_save", text="Save External...")
            row.label()

    def PARTICLE_INSTANCE(self, layout, ob, md):
        layout.prop(md, "object")
        layout.prop(md, "particle_system_index", text="Particle System")

        split = layout.split()
        col = split.column()
        col.label(text="Create From:")
        col.prop(md, "use_normal")
        col.prop(md, "use_children")
        col.prop(md, "use_size")

        col = split.column()
        col.label(text="Show Particles When:")
        col.prop(md, "show_alive")
        col.prop(md, "show_unborn")
        col.prop(md, "show_dead")

        layout.separator()

        layout.prop(md, "use_path", text="Create Along Paths")

        split = layout.split()
        split.active = md.use_path
        col = split.column()
        col.row().prop(md, "axis", expand=True)
        col.prop(md, "use_preserve_shape")

        col = split.column()
        col.prop(md, "position", slider=True)
        col.prop(md, "random_position", text="Random", slider=True)

    def PARTICLE_SYSTEM(self, layout, ob, md):
        layout.label(text="Settings can be found inside the Particle context")

    def SCREW(self, layout, ob, md):
        split = layout.split()

        col = split.column()
        col.prop(md, "axis")
        col.prop(md, "object", text="AxisOb")
        col.prop(md, "angle")
        col.prop(md, "steps")
        col.prop(md, "render_steps")

        col = split.column()
        row = col.row()
        row.active = (md.object is None or md.use_object_screw_offset == False)
        row.prop(md, "screw_offset")
        row = col.row()
        row.active = (md.object is not None)
        row.prop(md, "use_object_screw_offset")
        col.prop(md, "use_normal_calculate")
        col.prop(md, "use_normal_flip")
        col.prop(md, "iterations")

    def SHRINKWRAP(self, layout, ob, md):
        split = layout.split()
        col = split.column()
        col.label(text="Target:")
        col.prop(md, "target", text="")
        col = split.column()
        col.label(text="Vertex Group:")
        col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")

        split = layout.split()

        col = split.column()
        col.prop(md, "offset")
        col.prop(md, "subsurf_levels")

        col = split.column()
        col.label(text="Mode:")
        col.prop(md, "wrap_method", text="")

        if md.wrap_method == 'PROJECT':
            split = layout.split(percentage=0.25)

            col = split.column()
            col.label(text="Axis:")
            col.prop(md, "use_project_x")
            col.prop(md, "use_project_y")
            col.prop(md, "use_project_z")

            col = split.column()
            col.label(text="Direction:")
            col.prop(md, "use_negative_direction")
            col.prop(md, "use_positive_direction")

            col = split.column()
            col.label(text="Cull Faces:")
            col.prop(md, "cull_face", expand=True)

            layout.label(text="Auxiliary Target:")
            layout.prop(md, "auxiliary_target", text="")

        elif md.wrap_method == 'NEAREST_SURFACEPOINT':
            layout.prop(md, "use_keep_above_surface")

    def SIMPLE_DEFORM(self, layout, ob, md):
        split = layout.split()

        col = split.column()
        col.label(text="Mode:")
        col.prop(md, "deform_method", text="")

        col = split.column()
        col.label(text="Vertex Group:")
        col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")

        split = layout.split()

        col = split.column()
        col.label(text="Origin:")
        col.prop(md, "origin", text="")
        sub = col.column()
        sub.active = (md.origin is not None)
        sub.prop(md, "use_relative")

        col = split.column()
        col.label(text="Deform:")
        col.prop(md, "factor")
        col.prop(md, "limits", slider=True)
        if md.deform_method in {'TAPER', 'STRETCH'}:
            col.prop(md, "lock_x")
            col.prop(md, "lock_y")

    def SMOKE(self, layout, ob, md):
        layout.label(text="Settings can be found inside the Physics context")

    def SMOOTH(self, layout, ob, md):
        split = layout.split(percentage=0.25)

        col = split.column()
        col.label(text="Axis:")
        col.prop(md, "use_x")
        col.prop(md, "use_y")
        col.prop(md, "use_z")

        col = split.column()
        col.prop(md, "factor")
        col.prop(md, "iterations")
        col.label(text="Vertex Group:")
        col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")

    def SOFT_BODY(self, layout, ob, md):
        layout.label(text="Settings can be found inside the Physics context")

    def SOLIDIFY(self, layout, ob, md):
        split = layout.split()

        col = split.column()
        col.prop(md, "thickness")
        col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")

        col.label(text="Crease:")
        col.prop(md, "edge_crease_inner", text="Inner")
        col.prop(md, "edge_crease_outer", text="Outer")
        col.prop(md, "edge_crease_rim", text="Rim")
        col.label(text="Material Index Offset:")

        col = split.column()

        col.prop(md, "offset")
        sub = col.column()
        sub.active = bool(md.vertex_group)
        sub.prop(md, "invert_vertex_group", text="Invert")

        col.prop(md, "use_even_offset")
        col.prop(md, "use_quality_normals")
        col.prop(md, "use_rim")

        sub = col.column()
        sub.label()
        row = sub.split(align=True, percentage=0.4)
        row.prop(md, "material_offset", text="")
        row = row.row()
        row.active = md.use_rim
        row.prop(md, "material_offset_rim", text="Rim")

    def SUBSURF(self, layout, ob, md):
        layout.row().prop(md, "subdivision_type", expand=True)

        split = layout.split()
        col = split.column()
        col.label(text="Subdivisions:")
        col.prop(md, "levels", text="View")
        col.prop(md, "render_levels", text="Render")

        col = split.column()
        col.label(text="Options:")
        col.prop(md, "use_subsurf_uv")
        col.prop(md, "show_only_control_edges")

    def SURFACE(self, layout, ob, md):
        layout.label(text="Settings can be found inside the Physics context")

    def UV_PROJECT(self, layout, ob, md):
        if ob.type == 'MESH':
            split = layout.split()

            col = split.column()
            col.label(text="Image:")
            col.prop(md, "image", text="")

            col = split.column()
            col.label(text="UV Layer:")
            col.prop_search(md, "uv_layer", ob.data, "uv_textures", text="")

            split = layout.split()
            col = split.column()
            col.prop(md, "use_image_override")
            col.prop(md, "projector_count", text="Projectors")
            for proj in md.projectors:
                col.prop(proj, "object", text="")

            col = split.column()
            sub = col.column(align=True)
            sub.prop(md, "aspect_x", text="Aspect X")
            sub.prop(md, "aspect_y", text="Aspect Y")

            sub = col.column(align=True)
            sub.prop(md, "scale_x", text="Scale X")
            sub.prop(md, "scale_y", text="Scale Y")

    def WARP(self, layout, ob, md):
        use_falloff = (md.falloff_type != 'NONE')
        split = layout.split()

        col = split.column()
        col.label(text="From:")
        col.prop(md, "object_from", text="")

        col.prop(md, "use_volume_preserve")

        col = split.column()
        col.label(text="To:")
        col.prop(md, "object_to", text="")
        col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")

        col = layout.column()

        row = col.row(align=True)
        row.prop(md, "strength")
        if use_falloff:
            row.prop(md, "falloff_radius")

        col.prop(md, "falloff_type")
        if use_falloff:
            if md.falloff_type == 'CURVE':
                col.template_curve_mapping(md, "falloff_curve")

        # 2 new columns
        split = layout.split()
        col = split.column()
        col.label(text="Texture:")
        col.prop(md, "texture", text="")

        col = split.column()
        col.label(text="Texture Coordinates:")
        col.prop(md, "texture_coords", text="")

        if md.texture_coords == 'OBJECT':
            layout.prop(md, "texture_coords_object", text="Object")
        elif md.texture_coords == 'UV' and ob.type == 'MESH':
            layout.prop_search(md, "uv_layer", ob.data, "uv_textures")

    def WAVE(self, layout, ob, md):
        split = layout.split()

        col = split.column()
        col.label(text="Motion:")
        col.prop(md, "use_x")
        col.prop(md, "use_y")
        col.prop(md, "use_cyclic")

        col = split.column()
        col.prop(md, "use_normal")
        sub = col.column()
        sub.active = md.use_normal
        sub.prop(md, "use_normal_x", text="X")
        sub.prop(md, "use_normal_y", text="Y")
        sub.prop(md, "use_normal_z", text="Z")

        split = layout.split()

        col = split.column()
        col.label(text="Time:")
        sub = col.column(align=True)
        sub.prop(md, "time_offset", text="Offset")
        sub.prop(md, "lifetime", text="Life")
        col.prop(md, "damping_time", text="Damping")

        col = split.column()
        col.label(text="Position:")
        sub = col.column(align=True)
        sub.prop(md, "start_position_x", text="X")
        sub.prop(md, "start_position_y", text="Y")
        col.prop(md, "falloff_radius", text="Falloff")

        layout.separator()

        layout.prop(md, "start_position_object")
        layout.prop_search(md, "vertex_group", ob, "vertex_groups")
        split = layout.split(percentage=0.33)
        col = split.column()
        col.label(text="Texture")
        col = split.column()
        col.template_ID(md, "texture", new="texture.new")
        layout.prop(md, "texture_coords")
        if md.texture_coords == 'MAP_UV' and ob.type == 'MESH':
            layout.prop_search(md, "uv_layer", ob.data, "uv_textures")
        elif md.texture_coords == 'OBJECT':
            layout.prop(md, "texture_coords_object")

        layout.separator()

        split = layout.split()

        col = split.column()
        col.prop(md, "speed", slider=True)
        col.prop(md, "height", slider=True)

        col = split.column()
        col.prop(md, "width", slider=True)
        col.prop(md, "narrowness", slider=True)

    @staticmethod
    def weight_vg_mask(layout, ob, md):
        layout.label(text="Influence/Mask Options:")
        split = layout.split()
        col1 = split.column()
        col2 = split.column()

        col1.label(text="Global Influence:")
        col2.prop(md, "mask_constant", text="")

        if not md.mask_texture:
            col1.label(text="Vertex Group Mask:")
            col2.prop_search(md, "mask_vertex_group", ob, "vertex_groups", text="")

        if not md.mask_vertex_group:
            col1.label(text="Texture Mask:")
            col2.template_ID(md, "mask_texture", new="texture.new")
            if md.mask_texture:
                split = layout.split()
                col = split.column()
                col.label(text="Texture Coordinates:")
                col.prop(md, "mask_tex_mapping", text="")
                col = split.column()
                col.label(text="Use Channel:")
                col.prop(md, "mask_tex_use_channel", text="")

                if md.mask_tex_mapping == 'OBJECT':
                    layout.prop(md, "mask_tex_map_obj", text="Object")
                elif md.mask_tex_mapping == 'UV' and ob.type == 'MESH':
                    layout.prop_search(md, "mask_tex_uv_layer", ob.data, "uv_textures")

    def WEIGHT_VGEDIT(self, layout, ob, md):
        if ob.type == 'MESH':
            split = layout.split()
            col = split.column()
            col.label(text="Vertex Group:")
            col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")

            col = split.column()
            col.label(text="Default Weight:")
            col.prop(md, "default_weight", text="")

            layout.prop(md, "use_map")
            if md.use_map:
                split = layout.split()
                col = split.column()
                col.label("Input:")
                col.label("Output:")
                col = split.column()
                col.prop(md, "map_input_low", text="Min")
                col.prop(md, "map_output_low", text="Min")
                col = split.column()
                col.prop(md, "map_input_high", text="Max")
                col.prop(md, "map_output_high", text="Max")

            layout.prop(md, "use_map_curve")
            if md.use_map_curve:
                col = layout.column()
                col.template_curve_mapping(md, "map_curve")

            layout.prop(md, "use_reverse")

            layout.prop(md, "use_clamp")
            if md.use_clamp:
                row = layout.row()
                row.prop(md, "clamp_weight_min")
                row.prop(md, "clamp_weight_max")

            row = layout.row()
            row.prop(md, "use_add")
            row.prop(md, "use_remove")
            row = layout.row()
            if md.use_add:
                row.prop(md, "add_threshold")
            if md.use_remove:
                row.prop(md, "remove_threshold")

            # Common mask options…
            layout.separator()
            self.weight_vg_mask(layout, ob, md)

    def WEIGHT_VGMIX(self, layout, ob, md):
        if ob.type == 'MESH':
            split = layout.split()
            col = split.column()
            col.label(text="Vertex Group 1:")
            col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")
            col.label(text="Default Weight 1:")
            col.prop(md, "default_weight", text="")

            col.label(text="Mix Mode:")
            col.prop(md, "mix_mode", text="")

            col = split.column()
            col.label(text="Vertex Group 2:")
            col.prop_search(md, "vertex_group2", ob, "vertex_groups", text="")
            col.label(text="Default Weight 2:")
            col.prop(md, "default_weight2", text="")

            col.label(text="Mix Set:")
            col.prop(md, "mix_set", text="")

            # Common mask options…
            layout.separator()
            self.weight_vg_mask(layout, ob, md)

    def WEIGHT_VGPROXIMITY(self, layout, ob, md):
        if ob.type == 'MESH':
            split = layout.split()
            col = split.column()
            col.label(text="Vertex Group:")
            col.prop_search(md, "vertex_group", ob, "vertex_groups", text="")

            col = split.column()
            col.label(text="Target Object:")
            col.prop(md, "target", text="")

            row = layout.row()
            row.prop(md, "proximity_mode", expand=True)
            if md.proximity_mode == 'GEOMETRY':
                row = layout.row()
                row.prop(md, "proximity_geometry", expand=True)

            row = layout.split()
            row.prop(md, "min_dist")
            row.prop(md, "max_dist")

            # Common mask options…
            layout.separator()
            self.weight_vg_mask(layout, ob, md)

if __name__ == "__main__":  # only for live edit.
    bpy.utils.register_module(__name__)
