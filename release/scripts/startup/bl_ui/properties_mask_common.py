# SPDX-License-Identifier: GPL-2.0-or-later

# panels get subclassed (not registered directly)
# menus are referenced `as is`

from bpy.types import Menu, UIList
from bpy.app.translations import contexts as i18n_contexts


# Use by both image & clip context menus.
def draw_mask_context_menu(layout, _context):
    layout.operator_menu_enum("mask.handle_type_set", "type")
    layout.operator("mask.switch_direction", icon = "SWITCH_DIRECTION")
    layout.operator("mask.cyclic_toggle", icon = "TOGGLE_CYCLIC")

    layout.separator()
    layout.operator("mask.copy_splines", icon='COPYDOWN')
    layout.operator("mask.paste_splines", icon='PASTEDOWN')

    layout.separator()

    layout.operator("mask.shape_key_rekey", text="Re-Key Shape Points", icon = "SHAPEKEY_DATA")
    layout.operator("mask.feather_weight_clear", icon = "KEYFRAMES_CLEAR")
    layout.operator("mask.shape_key_feather_reset", text="Reset Feather Animation", icon = "RESET")

    layout.separator()

    layout.operator("mask.parent_set", icon = "PARENT_SET")
    layout.operator("mask.parent_clear", icon = "PARENT_CLEAR")

    layout.separator()

    layout.operator("mask.delete", icon = "DELETE")


class MASK_UL_layers(UIList):
    def draw_item(self, _context, layout, _data, item, icon,
                  _active_data, _active_propname, _index):
        # assert(isinstance(item, bpy.types.MaskLayer)
        mask = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(mask, "name", text="", emboss=False, icon_value=icon)
            row = layout.row(align=True)
            row.prop(mask, "hide", text="", emboss=False)
            row.prop(mask, "hide_select", text="", emboss=False)
            row.prop(mask, "hide_render", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class MASK_PT_mask:
    # subclasses must define...
    # ~ bl_space_type = 'CLIP_EDITOR'
    # ~ bl_region_type = 'UI'
    bl_label = "Mask Settings"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        return space_data.mask and space_data.mode == 'MASK'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sc = context.space_data
        mask = sc.mask

        col = layout.column(align=True)
        col.prop(mask, "frame_start")
        col.prop(mask, "frame_end")


class MASK_PT_layers:
    # subclasses must define...
    # ~ bl_space_type = 'CLIP_EDITOR'
    # ~ bl_region_type = 'UI'
    bl_label = "Mask Layers"

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        return space_data.mask and space_data.mode == 'MASK'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sc = context.space_data
        mask = sc.mask
        active_layer = mask.layers.active

        rows = 4 if active_layer else 1

        row = layout.row()
        row.template_list("MASK_UL_layers", "", mask, "layers",
                          mask, "active_layer_index", rows=rows)

        sub = row.column(align=True)

        sub.operator("mask.layer_new", icon='ADD', text="")
        sub.operator("mask.layer_remove", icon='REMOVE', text="")

        if active_layer:
            sub.separator()

            sub.operator("mask.layer_move", icon='TRIA_UP', text="").direction = 'UP'
            sub.operator("mask.layer_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

            # blending
            row = layout.row(align=True)
            row.prop(active_layer, "alpha")
            row.prop(active_layer, "invert", text="", icon='IMAGE_ALPHA')

            layout.prop(active_layer, "blend")
            layout.prop(active_layer, "falloff")

            col = layout.column()
            col.use_property_split = False
            col.prop(active_layer, "use_fill_overlap", text="Overlap")
            col.prop(active_layer, "use_fill_holes", text="Holes")


class MASK_PT_spline:
    # subclasses must define...
    # ~ bl_space_type = 'CLIP_EDITOR'
    # ~ bl_region_type = 'UI'
    bl_label = "Active Spline"

    @classmethod
    def poll(cls, context):
        sc = context.space_data
        mask = sc.mask

        if mask and sc.mode == 'MASK':
            return mask.layers.active and mask.layers.active.splines.active

        return False

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sc = context.space_data
        mask = sc.mask
        spline = mask.layers.active.splines.active

        col = layout.column()
        col.prop(spline, "offset_mode")
        col.prop(spline, "weight_interpolation", text="Interpolation")

        col.use_property_split = False
        col.prop(spline, "use_cyclic")
        col.prop(spline, "use_fill")
        col.prop(spline, "use_self_intersection_check")


class MASK_PT_point:
    # subclasses must define...
    # ~ bl_space_type = 'CLIP_EDITOR'
    # ~ bl_region_type = 'UI'
    bl_label = "Active Point"

    @classmethod
    def poll(cls, context):
        sc = context.space_data
        mask = sc.mask

        if mask and sc.mode == 'MASK':
            mask_layer_active = mask.layers.active
            return (mask_layer_active and
                    mask_layer_active.splines.active_point)

        return False

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sc = context.space_data
        mask = sc.mask
        point = mask.layers.active.splines.active_point
        parent = point.parent

        col = layout.column()
        # Currently only parenting the movie-clip is allowed,
        # so do not over-complicate things for now by using single template_ID
        #col.template_any_ID(parent, "id", "id_type", text="")

        col.label(text="Parent:")
        col.prop(parent, "id", text="")

        if parent.id_type == 'MOVIECLIP' and parent.id:
            clip = parent.id
            tracking = clip.tracking

            row = col.row()
            row.prop(parent, "type", expand=True)

            col.prop_search(parent, "parent", tracking, "objects", text = "Object", icon='OBJECT_DATA')

            tracks_list = "tracks" if parent.type == 'POINT_TRACK' else "plane_tracks"

            if parent.parent in tracking.objects:
                ob = tracking.objects[parent.parent]
                col.prop_search(parent, "sub_parent", ob,
                                tracks_list, icon='ANIM_DATA', text="Track")
            else:
                col.prop_search(parent, "sub_parent", tracking, tracks_list, text="Track", icon = 'ANIM_DATA')


class MASK_PT_display:
    # subclasses must define...
    # ~ bl_space_type = 'CLIP_EDITOR'
    # ~ bl_region_type = 'HEADER'
    bl_label = "Mask Display"

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        return space_data.mask and space_data.mode == 'MASK'

    def draw(self, context):
        layout = self.layout
        layout.label(text="Mask Display")

        space_data = context.space_data

        row = layout.row(align=True)
        row.prop(space_data, "show_mask_spline", text="Spline")
        sub = row.row()
        if space_data.show_mask_spline:
            sub.active = space_data.show_mask_spline
            sub.prop(space_data, "mask_display_type", text="")
        else:
            row.label(icon='DISCLOSURE_TRI_RIGHT')
    
        row = layout.row(align=True)
        row.prop(space_data, "show_mask_overlay", text="Overlay")
        if space_data.show_mask_overlay:
            sub = row.row()
            sub.active = space_data.show_mask_overlay
            sub.prop(space_data, "mask_overlay_mode", text="")
            
            row = layout.row()
            row.active = (space_data.mask_overlay_mode in ['COMBINED'] and space_data.show_mask_overlay)
            row.prop(space_data, "blend_factor", text="Blending Factor")
        else:
            row.label(icon='DISCLOSURE_TRI_RIGHT')


class MASK_PT_transforms:
    # subclasses must define...
    # ~ bl_space_type = 'CLIP_EDITOR'
    # ~ bl_region_type = 'TOOLS'
    bl_label = "Transforms"
    bl_category = "Mask"

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        return space_data.mask and space_data.mode == 'MASK'

    def draw(self, _context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Transform:")
        col.operator("transform.translate")
        col.operator("transform.rotate")
        col.operator("transform.resize", text="Scale")
        col.operator("transform.transform", text="Scale Feather").mode = 'MASK_SHRINKFATTEN'

# bfa - former mask tools panel. Keeping code for compatibility reasons
# class MASK_PT_tools:
#     bl_label = "Mask Tools"
#     bl_category = "Mask"

#     @classmethod
#     def poll(cls, context):
#         space_data = context.space_data
#         return space_data.mask and space_data.mode == 'MASK'

#     def draw(self, _context):
#         layout = self.layout

#         col = layout.column(align=True)
#         col.label(text="Spline:")
#         col.operator("mask.delete", icon = "DELETE")
#         col.operator("mask.cyclic_toggle", icon = "TOGGLE_CYCLIC")
#         col.operator("mask.switch_direction", icon = "SWITCH_DIRECTION")
#         col.operator("mask.handle_type_set", icon = "HANDLE_VECTOR").type = 'VECTOR'
#         col.operator("mask.feather_weight_clear", icon = "CLEAR")

#         col = layout.column(align=True)
#         col.label(text="Parenting:")
#         row = col.row(align=True)
#         row.operator("mask.parent_set", text="Parent", icon = "PARENT_SET")
#         row.operator("mask.parent_clear", text="Clear", icon = "PARENT_CLEAR")

#         col = layout.column(align=True)
#         col.label(text="Animation:")
#         row = col.row(align=True)
#         row.operator("mask.shape_key_insert", text="Insert Key", icon = "KEYFRAME")
#         row.operator("mask.shape_key_clear", text="Clear Key", icon = "KEYFRAMES_CLEAR")
#         col.operator("mask.shape_key_feather_reset", text="Reset Feather Animation", icon = "RESET")
#         col.operator("mask.shape_key_rekey", text="Re-Key Shape Points", icon = "SHAPEKEY_DATA")


class MASK_MT_mask(Menu):
    bl_label = "Mask"

    def draw(self, _context):
        layout = self.layout

        layout.menu("MASK_MT_transform")

        layout.separator()

        layout.operator("mask.duplicate_move", text = "Duplicate", icon = "DUPLICATE")
        layout.operator("mask.delete", icon = "DELETE")

        layout.separator()

        layout.operator("mask.copy_splines", icon = "COPYDOWN")
        layout.operator("mask.paste_splines", icon = "PASTEDOWN")

        layout.separator()

        layout.operator("mask.parent_set", icon = "PARENT_SET")
        layout.operator("mask.parent_clear", icon = "PARENT_CLEAR")

        layout.separator()

        layout.operator("mask.cyclic_toggle", icon = 'TOGGLE_CYCLIC')
        layout.operator("mask.switch_direction", icon = 'SWITCH_DIRECTION')
        layout.operator("mask.normals_make_consistent", icon = "RECALC_NORMALS")
        layout.operator_menu_enum("mask.handle_type_set", "type")

        layout.separator()

        layout.menu("MASK_MT_animation")
        layout.menu("MASK_MT_visibility")


class MASK_MT_add(Menu):
    bl_idname = "MASK_MT_add"
    bl_label = "Add"
    bl_translation_context = i18n_contexts.operator_default

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mask.primitive_circle_add", text="Circle", icon='MESH_CIRCLE')
        layout.operator("mask.primitive_square_add", text="Square", icon='MESH_PLANE')

        layout.separator()

        layout.operator("mask.add_vertex_slide", text="Add Vertex and Slide", icon='SLIDE_VERTEX')


class MASK_MT_visibility(Menu):
    bl_label = "Show/Hide"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mask.hide_view_clear", text = "Show Hidden", icon = "HIDE_OFF")
        layout.operator("mask.hide_view_set", text = "Hide Selected", icon = "HIDE_ON").unselected = False
        layout.operator("mask.hide_view_set", text = "Hide Unselected", icon = "HIDE_UNSELECTED").unselected = True


class MASK_MT_transform(Menu):
    bl_label = "Transform"

    def draw(self, _context):
        layout = self.layout

        layout.operator("transform.translate", icon = "TRANSFORM_MOVE")
        layout.operator("transform.rotate", icon = "TRANSFORM_ROTATE")
        layout.operator("transform.resize", text = "Scale",  icon = "TRANSFORM_SCALE")

        layout.separator()

        layout.operator("transform.tosphere", icon = "TOSPHERE")
        layout.operator("transform.shear", icon = "SHEAR")
        layout.operator("transform.push_pull", icon = "PUSH_PULL")

        layout.separator()

        layout.operator("transform.transform", text = "Scale Feather", icon = 'SHRINK_FATTEN').mode = 'MASK_SHRINKFATTEN'
        layout.operator("mask.feather_weight_clear", text = "  Clear Feather Weight", icon = "CLEAR")


class MASK_MT_animation(Menu):
    bl_label = "Animation"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mask.shape_key_insert", icon = "KEYFRAMES_INSERT")
        layout.operator("mask.shape_key_clear", icon = "CLEAR")
        layout.operator("mask.shape_key_feather_reset", text="Reset Feather Animation", icon='RESET')
        layout.operator("mask.shape_key_rekey", text="Re-key Shape Points", icon = "SHAPEKEY_DATA")


class MASK_MT_select(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mask.select_all", text = "All", icon = 'SELECT_ALL').action = 'SELECT'
        layout.operator("mask.select_all", text = "None", icon = 'SELECT_NONE').action = 'DESELECT'
        layout.operator("mask.select_all", text = "Invert", icon = 'INVERSE').action = 'INVERT'

        layout.separator()

        layout.operator("mask.select_box", icon = 'BORDER_RECT')
        layout.operator("mask.select_circle", icon = 'CIRCLE_SELECT')
        layout.operator_menu_enum("mask.select_lasso", "mode")

        layout.separator()

        layout.operator("mask.select_linked", text = "Linked", icon = "LINKED")

        layout.separator()

        layout.operator("mask.select_more", text = "More", icon = "SELECTMORE")
        layout.operator("mask.select_less", text = "Less", icon = "SELECTLESS")


classes = (
    MASK_UL_layers,
    MASK_MT_mask,
    MASK_MT_add,
    MASK_MT_visibility,
    MASK_MT_transform,
    MASK_MT_animation,
    MASK_MT_select,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
