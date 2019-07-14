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

# <pep8-80 compliant>

# panels get subclassed (not registered directly)
# menus are referenced `as is`

import bpy
from bpy.types import Menu, UIList


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
    # ~ bl_region_type = 'UI'
    bl_label = "Mask Display"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        return space_data.mask and space_data.mode == 'MASK'

    def draw(self, context):
        layout = self.layout

        space_data = context.space_data
        row = layout.row(align=True)
        row.prop(space_data, "show_mask_smooth", text="Smooth")
        row.prop(space_data, "mask_display_type", text="")
        row = layout.row(align=True)
        row.prop(space_data, "show_mask_overlay", text="Overlay")
        sub = row.row()
        sub.active = space_data.show_mask_overlay
        sub.prop(space_data, "mask_overlay_mode", text="")


class MASK_PT_tools:
    bl_label = "Mask Tools"
    bl_category = "Mask"

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        return space_data.mask and space_data.mode == 'MASK'

    def draw(self, _context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Spline:")
        col.operator("mask.delete")
        col.operator("mask.cyclic_toggle")
        col.operator("mask.switch_direction")
        col.operator("mask.handle_type_set").type = 'VECTOR'
        col.operator("mask.feather_weight_clear")

        col = layout.column(align=True)
        col.label(text="Parenting:")
        row = col.row(align=True)
        row.operator("mask.parent_set", text="Parent")
        row.operator("mask.parent_clear", text="Clear")

        col = layout.column(align=True)
        col.label(text="Animation:")
        row = col.row(align=True)
        row.operator("mask.shape_key_insert", text="Insert Key")
        row.operator("mask.shape_key_clear", text="Clear Key")
        col.operator("mask.shape_key_feather_reset", text="Reset Feather Animation")
        col.operator("mask.shape_key_rekey", text="Re-Key Shape Points")


class MASK_MT_mask(Menu):
    bl_label = "Mask"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mask.delete", icon = "DELETE")
        layout.operator("mask.duplicate_move", text = "Duplicate", icon = "DUPLICATE")

        layout.separator()

        layout.operator("mask.cyclic_toggle", icon = 'TOGGLE_CYCLIC')
        layout.operator("mask.switch_direction", icon = 'SWITCH_DIRECTION')
        layout.operator("mask.normals_make_consistent", icon = "RECALC_NORMALS")
        layout.operator("mask.handle_type_set", icon = 'HANDLE_AUTO')

        layout.separator()

        layout.operator("mask.parent_clear", icon = "PARENT_CLEAR")
        layout.operator("mask.parent_set", icon = "PARENT_SET")

        layout.separator()

        layout.operator("mask.copy_splines", icon = "COPYDOWN")
        layout.operator("mask.paste_splines", icon = "PASTEDOWN")

        layout.separator()

        layout.menu("MASK_MT_visibility")
        layout.menu("MASK_MT_transform")
        layout.menu("MASK_MT_animation")

class MASK_MT_visibility(Menu):
    bl_label = "Show/Hide"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mask.hide_view_clear", text = "Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("mask.hide_view_set", text = "Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("mask.hide_view_set", text = "Hide Unselected", icon = "HIDE_UNSELECTED").unselected = True


class MASK_MT_transform(Menu):
    bl_label = "Transform"

    def draw(self, _context):
        layout = self.layout

        layout.operator("transform.translate", icon = "TRANSFORM_MOVE")
        layout.operator("transform.rotate", icon = "TRANSFORM_ROTATE")
        layout.operator("transform.resize", text = "Scale",  icon = "TRANSFORM_SCALE")
        layout.operator("transform.transform", text = "Scale Feather", icon = 'SHRINK_FATTEN').mode = 'MASK_SHRINKFATTEN'

        layout.separator()

        layout.operator("mask.feather_weight_clear", text = "  Clear Feather Weight", icon = "CLEAR")


class MASK_MT_animation(Menu):
    bl_label = "Animation"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mask.shape_key_clear", icon = "CLEAR")
        layout.operator("mask.shape_key_insert", icon = "KEYFRAMES_INSERT")
        layout.operator("mask.shape_key_feather_reset", icon = "RESET")
        layout.operator("mask.shape_key_rekey", icon = 'KEY_HLT')


# Workaround to separate the tooltips
class MASK_MT_select_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mask.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mask.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class MASK_MT_select_none(bpy.types.Operator):
    """None\nDeselects everything """       # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mask.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mask.select_all(action = 'DESELECT')
        return {'FINISHED'}


class MASK_MT_select(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mask.select_box", icon = 'CIRCLE_SELECT')
        layout.operator("mask.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("mask.select_all", icon = 'SELECT_ALL').action = 'SELECT'
        layout.operator("mask.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("mask.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip
        
        layout.separator()

        layout.operator("mask.select_linked", text = "Select Linked", icon = "LINKED")

        layout.separator()

        layout.operator("mask.select_more", icon = "SELECTMORE")
        layout.operator("mask.select_less", icon = "SELECTLESS")


classes = (
    MASK_UL_layers,
    MASK_MT_mask,
    MASK_MT_visibility,
    MASK_MT_transform,
    MASK_MT_animation,  
    MASK_MT_select_inverse,
    MASK_MT_select_none,
    MASK_MT_select,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
