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

# panels get subclassed (not registered directly)
# menus are referenced `as is`

import bpy
from bpy.types import Menu


class MASK_PT_mask:
    # subclasses must define...
    #~ bl_space_type = 'CLIP_EDITOR'
    #~ bl_region_type = 'UI'
    bl_label = "Mask Settings"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        return space_data.mask and space_data.mode == 'MASK'

    def draw(self, context):
        layout = self.layout

        sc = context.space_data
        mask = sc.mask

        col = layout.column(align=True)
        col.prop(mask, "frame_start")
        col.prop(mask, "frame_end")


class MASK_PT_layers:
    # subclasses must define...
    #~ bl_space_type = 'CLIP_EDITOR'
    #~ bl_region_type = 'UI'
    bl_label = "Mask Layers"

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        return space_data.mask and space_data.mode == 'MASK'

    def draw(self, context):
        layout = self.layout

        sc = context.space_data
        mask = sc.mask
        active_layer = mask.layers.active

        rows = 5 if active_layer else 2

        row = layout.row()
        row.template_list(mask, "layers",
                          mask, "active_layer_index", rows=rows)

        sub = row.column(align=True)

        sub.operator("mask.layer_new", icon='ZOOMIN', text="")
        sub.operator("mask.layer_remove", icon='ZOOMOUT', text="")

        if active_layer:
            sub.separator()

            props = sub.operator("mask.layer_move", icon='TRIA_UP', text="")
            props.direction = 'UP'

            props = sub.operator("mask.layer_move", icon='TRIA_DOWN', text="")
            props.direction = 'DOWN'

            layout.prop(active_layer, "name")

            # blending
            row = layout.row(align=True)
            row.prop(active_layer, "alpha")
            row.prop(active_layer, "invert", text="", icon='IMAGE_ALPHA')

            layout.prop(active_layer, "blend")
            layout.prop(active_layer, "falloff")


class MASK_PT_spline():
    # subclasses must define...
    #~ bl_space_type = 'CLIP_EDITOR'
    #~ bl_region_type = 'UI'
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

        sc = context.space_data
        mask = sc.mask
        spline = mask.layers.active.splines.active

        col = layout.column()
        col.prop(spline, "weight_interpolation")
        
        row = col.row()
        row.prop(spline, "use_cyclic")
        row.prop(spline, "use_fill")


class MASK_PT_point():
    # subclasses must define...
    #~ bl_space_type = 'CLIP_EDITOR'
    #~ bl_region_type = 'UI'
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

        sc = context.space_data
        mask = sc.mask
        point = mask.layers.active.splines.active_point
        parent = point.parent

        col = layout.column()
        col.prop(point, "handle_type")

        col = layout.column()
        # Currently only parenting yo movie clip is allowed, so do not
        # ver-oplicate things for now and use single template_ID
        #col.template_any_ID(parent, "id", "id_type", text="")

        col.label("Parent:")
        col.prop(parent, "id", text="")

        if parent.id_type == 'MOVIECLIP' and parent.id:
            clip = parent.id
            tracking = clip.tracking

            col.prop_search(parent, "parent", tracking,
                            "objects", icon='OBJECT_DATA', text="Object:")

            if parent.parent in tracking.objects:
                object = tracking.objects[parent.parent]
                col.prop_search(parent, "sub_parent", object,
                                "tracks", icon='ANIM_DATA', text="Track:")
            else:
                col.prop_search(parent, "sub_parent", tracking,
                                "tracks", icon='ANIM_DATA', text="Track:")


class MASK_PT_display():
    # subclasses must define...
    #~ bl_space_type = 'CLIP_EDITOR'
    #~ bl_region_type = 'UI'
    bl_label = "Mask Display"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        return space_data.mask and space_data.mode == 'MASK'

    def draw(self, context):
        layout = self.layout

        space_data = context.space_data

        layout.prop(space_data, "mask_draw_type", text="")
        layout.prop(space_data, "show_mask_smooth")


class MASK_PT_tools():
    # subclasses must define...
    #~ bl_space_type = 'CLIP_EDITOR'
    #~ bl_region_type = 'TOOLS'
    bl_label = "Mask Tools"

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        return space_data.mask and space_data.mode == 'MASK'

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Transform:")
        col.operator("transform.translate")
        col.operator("transform.rotate")
        col.operator("transform.resize", text="Scale")
        props = col.operator("transform.transform", text="Shrink/Fatten")
        props.mode = 'MASK_SHRINKFATTEN'

        col = layout.column(align=True)
        col.label(text="Spline:")
        col.operator("mask.delete")
        col.operator("mask.cyclic_toggle")
        col.operator("mask.switch_direction")

        col = layout.column(align=True)
        col.label(text="Parenting:")
        col.operator("mask.parent_set")
        col.operator("mask.parent_clear")


class MASK_MT_mask(Menu):
    bl_label = "Mask"

    def draw(self, context):
        layout = self.layout

        layout.operator("mask.delete")

        layout.separator()
        layout.operator("mask.cyclic_toggle")
        layout.operator("mask.switch_direction")
        layout.operator("mask.normals_make_consistent")
        layout.operator("mask.feather_weight_clear")  # TODO, better place?

        layout.separator()
        layout.operator("mask.parent_clear")
        layout.operator("mask.parent_set")

        layout.separator()
        layout.menu("MASK_MT_visibility")
        layout.menu("MASK_MT_transform")
        layout.menu("MASK_MT_animation")


class MASK_MT_visibility(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("mask.hide_view_clear", text="Show Hidden")
        layout.operator("mask.hide_view_set", text="Hide Selected")

        props = layout.operator("mask.hide_view_set", text="Hide Unselected")
        props.unselected = True


class MASK_MT_transform(Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout

        layout.operator("transform.translate")
        layout.operator("transform.rotate")
        layout.operator("transform.resize")
        props = layout.operator("transform.transform", text="Shrink/Fatten")
        props.mode = 'MASK_SHRINKFATTEN'


class MASK_MT_animation(Menu):
    bl_label = "Animation"

    def draw(self, context):
        layout = self.layout

        layout.operator("mask.shape_key_clear")
        layout.operator("mask.shape_key_insert")
        layout.operator("mask.shape_key_feather_reset")
        layout.operator("mask.shape_key_rekey")


class MASK_MT_select(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        sc = context.space_data

        layout.operator("mask.select_border")
        layout.operator("mask.select_circle")

        layout.separator()

        layout.operator("mask.select_all").action = 'TOGGLE'
        layout.operator("mask.select_all", text="Inverse").action = 'INVERT'

if __name__ == "__main__":  # only for live edit.
    bpy.utils.register_module(__name__)
