# SPDX-FileCopyrightText: 2009-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from bl_ui.properties_animviz import (
    MotionPathButtonsPanel,
    MotionPathButtonsPanel_display,
)
import bpy
from bpy.types import Panel, Menu
from rna_prop_ui import PropertyPanel
from bl_ui.space_properties import PropertiesAnimationMixin

# BFA - Added icons and floated peroperties left

class ObjectButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"


class OBJECT_PT_context_object(ObjectButtonsPanel, Panel):
    bl_label = ""
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        space = context.space_data

        if space.use_pin_id:
            layout.template_ID(space, "pin_id")
        else:
            row = layout.row()
            row.template_ID(context.view_layer.objects, "active", filter='AVAILABLE')


class OBJECT_PT_transform(ObjectButtonsPanel, Panel):
    bl_label = "Transform"

    def draw(self, context):
        draw4L = False

        layout = self.layout
        layout.use_property_split = True

        ob = context.object

        col = layout.column()
        row = col.row(align=True)
        row.prop(ob, "location")
        row.use_property_decorate = False
        row.prop(ob, "lock_location", text="", emboss=False, icon='DECORATE_UNLOCKED')

        rotation_mode = ob.rotation_mode
        if rotation_mode == 'QUATERNION':
            draw4L = True
            col = layout.column()
            row = col.row(align=True)
            row.prop(ob, "rotation_quaternion", text="Rotation")
            sub = row.column(align=True)
            sub.use_property_decorate = False
            if ob.lock_rotations_4d:
                sub.prop(ob, "lock_rotation_w", text="", emboss=False, icon='DECORATE_UNLOCKED')
            else:
                sub.label(text="", icon='BLANK1')
            sub.prop(ob, "lock_rotation", text="", emboss=False, icon='DECORATE_UNLOCKED')
        elif rotation_mode == 'AXIS_ANGLE':
            draw4L = True
            col = layout.column()
            row = col.row(align=True)
            row.prop(ob, "rotation_axis_angle", text="Rotation")

            sub = row.column(align=True)
            sub.use_property_decorate = False
            if ob.lock_rotations_4d:
                sub.prop(ob, "lock_rotation_w", text="", emboss=False, icon='DECORATE_UNLOCKED')
            else:
                sub.label(text="", icon='BLANK1')
            sub.prop(ob, "lock_rotation", text="", emboss=False, icon='DECORATE_UNLOCKED')
        else:
            col = layout.column()
            row = col.row(align=True)
            row.prop(ob, "rotation_euler", text="Rotation")
            row.use_property_decorate = False
            row.prop(ob, "lock_rotation", text="", emboss=False, icon='DECORATE_UNLOCKED')
        
        layout.label(text="Mode") # bfa - Label on its own layout
        
        row = layout.row(align=True)
        row.label(text="", icon='BLANK1') # bfa - icon has spacer - works better then separator at 4 factor
        row.separator(factor=1.0) # bfa - helps the icon has spacer!
        row.use_property_decorate = False # bfa - no decorator before 4L/blank icon
        row.prop(ob, "rotation_mode", text="") # bfa - no label 

        if draw4L:
            row.prop(ob, "lock_rotations_4d", text="", emboss=True, icon='4L_ON' if ob.lock_rotations_4d else '4L_OFF')
        else:
            # bfa - When not in quaternion/axis modes, we show a blank icon instead of the 4l toggle
            row.label(text="", icon='BLANK1')

        row.prop_decorator(ob, "rotation_mode") # bfa - show decorator after 4L 

        col = layout.column()
        row = col.row(align=True)
        row.prop(ob, "scale")
        row.use_property_decorate = False
        row.prop(ob, "lock_scale", text="", emboss=False, icon='DECORATE_UNLOCKED')


class OBJECT_PT_delta_transform(ObjectButtonsPanel, Panel):
    bl_label = "Delta Transform"
    bl_parent_id = "OBJECT_PT_transform"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        ob = context.object

        col = layout.column()
        col.prop(ob, "delta_location", text="Location")

        rotation_mode = ob.rotation_mode
        if rotation_mode == 'QUATERNION':
            col.prop(ob, "delta_rotation_quaternion", text="Rotation")
        elif rotation_mode == 'AXIS_ANGLE':
            pass
        else:
            col.prop(ob, "delta_rotation_euler", text="Rotation")

        col.prop(ob, "delta_scale", text="Scale")


class OBJECT_PT_parent_inverse_transform(ObjectButtonsPanel, Panel):
    bl_label = "Parent Inverse Transform"
    bl_parent_id = "OBJECT_PT_transform"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.parent

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        ob = context.object
        layout.template_matrix(ob, "matrix_parent_inverse")

        props = layout.operator("object.parent_clear", text="Clear Parent Inverse Transform")
        props.type = 'CLEAR_INVERSE'


class OBJECT_PT_relations(ObjectButtonsPanel, Panel):
    bl_label = "Relations"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)

        ob = context.object

        col = flow.column()
        col.prop(ob, "parent")
        parent = ob.parent
        if parent:
            row = col.row()
            row.separator()
            sub = row.column()
            sub.prop(ob, "parent_type")
            if ob.parent_type == 'BONE' and parent.type == 'ARMATURE':
                sub.prop_search(ob, "parent_bone", parent.data, "bones")
            elif ob.parent_type == 'VERTEX':
                col.prop(ob, "parent_vertices", text="Parent Vertex", index=0)
                sub.prop(ob, "use_parent_final_indices")
            elif ob.parent_type == 'VERTEX_3':
                col.prop(ob, "parent_vertices", text="Parent Vertices")
                sub.prop(ob, "use_parent_final_indices")
            sub.use_property_split = False
            sub.prop(ob, "use_camera_lock_parent")

        col.separator()

        col = flow.column()

        col.prop(ob, "track_axis", text="Tracking Axis")
        col.prop(ob, "up_axis", text="Up Axis")

        col.separator()

        col = flow.column()

        col.prop(ob, "pass_index")


class COLLECTION_MT_context_menu(Menu):
    bl_label = "Collection Specials"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.collection_unlink", text = "Delete", icon='DELETE')
        layout.operator("object.collection_objects_select", icon = "HAND")
        layout.operator("object.instance_offset_from_cursor", icon = "CURSOR")


class OBJECT_PT_collections(ObjectButtonsPanel, Panel):
    bl_label = "Collections"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        obj = context.object

        row = layout.row(align=True)
        if bpy.data.collections:
            row.operator("object.collection_link", text="Link to Existing Collection", icon="DECORATE_LINKED")
            row.operator("object.collection_add", text="", icon='ADD')
        else:
            row.operator("object.collection_add", text="Add to New Collection", icon='ADD')

        for collection in obj.users_collection:
            col = layout.column(align=True)

            col.context_pointer_set("collection", collection)

            row = col.box().row()
            row.prop(collection, "name", text="")
            row.operator("object.collection_remove", text="", icon='X', emboss=False)
            row.menu("COLLECTION_MT_context_menu", icon='DOWNARROW_HLT', text="")

            row = col.box().row()
            row.prop(collection, "instance_offset", text="")


class OBJECT_PT_display(ObjectButtonsPanel, Panel):
    bl_label = "Viewport Display"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 10

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        obj = context.object
        obj_type = obj.type
        is_geometry = (obj_type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME', 'CURVES', 'POINTCLOUD'})
        has_bounds = (is_geometry or obj_type in {'LATTICE', 'ARMATURE'})
        is_wire = (obj_type in {'CAMERA', 'EMPTY'})
        is_empty_image = (obj_type == 'EMPTY' and obj.empty_display_type == 'IMAGE')
        is_dupli = (obj.instance_type != 'NONE')
        is_gpencil = (obj_type == 'GREASEPENCIL')

        col = layout.column(align = True)
        col.label(text = "Show")

        row = col.row()
        row.separator()
        row.use_property_split = False
        row.prop(obj, "show_name", text="Name")
        row.prop_decorator(obj, "show_name")
        row = col.row()
        row.separator()
        row.use_property_split = False
        row.prop(obj, "show_axis", text="Axis")
        row.prop_decorator(obj, "show_axis")

        # Makes no sense for cameras, armatures, etc.!
        # but these settings do apply to dupli instances
        if is_geometry or is_dupli:
            row = col.row()
            row.separator()
            row.use_property_split = False
            row.prop(obj, "show_wire", text="Wireframe")
            row.prop_decorator(obj, "show_wire")
        if obj_type == 'MESH' or is_dupli:
            row = col.row()
            row.separator()
            row.use_property_split = False
            row.prop(obj, "show_all_edges", text="All Edges")
            row.prop_decorator(obj, "show_all_edges")
        if is_geometry:
            row = col.row()
            row.separator()
            row.use_property_split = False
            row.prop(obj, "show_texture_space", text="Texture Space")
            row.prop_decorator(obj, "show_texture_space")
            row = col.row()
            row.separator()
            row.use_property_split = False
            row.prop(obj.display, "show_shadows", text="Shadow")
        row = col.row()
        row.separator()
        row.use_property_split = False
        row.prop(obj, "show_in_front", text="In Front")
        row.prop_decorator(obj, "show_in_front")

        # if obj_type == 'MESH' or is_empty_image:
        #    col.prop(obj, "show_transparent", text="Transparency") #bfa - we have it in the output

        sub = layout.column()
        if is_wire:
            # wire objects only use the max. display type for duplis
            sub.active = is_dupli
        sub.prop(obj, "display_type", text="Display As")

        if is_geometry or is_dupli or is_empty_image or is_gpencil:
            # Only useful with object having faces/materials...
            col.prop(obj, "color")

        if has_bounds:
            split = layout.split(factor = 0.35)
            col = split.column()
            col.use_property_split = False
            col.prop(obj, "show_bounds", text="Bounds")
            col = split.column()
            if obj.show_bounds or (obj.display_type == 'BOUNDS'):
                col.prop(obj, "display_bounds_type", text="")
            else:
                col.label(icon='DISCLOSURE_TRI_RIGHT')


class OBJECT_PT_instancing(ObjectButtonsPanel, Panel):
    bl_label = "Instancing"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        # FONT objects need (vertex) instancing for the "Object Font" feature.
        return (ob.type in {'MESH', 'EMPTY', 'FONT'})

    def draw(self, context):
        layout = self.layout

        ob = context.object

        row = layout.row()
        row.prop(ob, "instance_type", expand=True)

        layout.use_property_split = False

        if ob.instance_type == 'VERTS':
            row = layout.row()

            row.prop(ob, "use_instance_vertices_rotation", text="Align to Vertex Normal")
            row.prop_decorator(ob, "use_instance_vertices_rotation")

        elif ob.instance_type == 'COLLECTION':
            row = layout.row()

            row.prop(ob, "instance_collection", text="Collection")
            row.prop_decorator(ob, "instance_collection")

        if ob.instance_type != 'NONE' or ob.particle_systems:
            layout.label(text = "Show Instancer")

            row = layout.row()

            row.separator()
            row.prop(ob, "show_instancer_for_viewport", text="Viewport")
            row.prop_decorator(ob, "show_instancer_for_viewport")

            row = layout.row()

            row.separator()
            row.prop(ob, "show_instancer_for_render", text="Render")
            row.prop_decorator(ob, "show_instancer_for_render")


class OBJECT_PT_instancing_size(ObjectButtonsPanel, Panel):
    bl_label = "Scale by Face Size"
    bl_parent_id = "OBJECT_PT_instancing"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return (ob is not None) and (ob.instance_type == 'FACES')

    def draw_header(self, context):

        ob = context.object
        self.layout.prop(ob, "use_instance_faces_scale", text="")

    def draw(self, context):
        layout = self.layout
        ob = context.object
        layout.use_property_split = True

        layout.active = ob.use_instance_faces_scale
        layout.prop(ob, "instance_faces_scale", text="Factor")


class OBJECT_PT_lineart(ObjectButtonsPanel, Panel):
    bl_label = "Line Art"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 10

    @classmethod
    def poll(cls, context):
        ob = context.object
        return (ob.type in {'MESH', 'FONT', 'CURVE', 'SURFACE', 'CURVES'})

    def draw(self, context):
        layout = self.layout
        ob = context.object
        lineart = ob.lineart

        layout.use_property_split = True

        layout.prop(lineart, "usage")

        split = layout.split(factor = 0.37)
        col = split.column()
        col.use_property_split = False
        
        col.prop(lineart, "use_crease_override", text="Override Crease")
        col = split.column()
        if lineart.use_crease_override:
            col.prop(lineart, "crease_threshold", slider=True, text="")
        else:
            col.label(icon='DISCLOSURE_TRI_RIGHT')
        
        row = layout.split(factor = 0.37)
        row.use_property_split = False
        row.prop(lineart, "use_intersection_priority_override", text="Intersection Priority")
        
        if lineart.use_intersection_priority_override:
            row.use_property_split = True
            row.active = lineart.use_intersection_priority_override
            row.prop(lineart, "intersection_priority", text="")
        else:
            col = row.column()
            row.use_property_split = False
            col.label(icon='DISCLOSURE_TRI_RIGHT')


class OBJECT_PT_motion_paths(MotionPathButtonsPanel, Panel):
    # bl_label = "Object Motion Paths"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.object)

    def draw(self, context):
        # layout = self.layout

        ob = context.object
        avs = ob.animation_visualization
        mpath = ob.motion_path

        self.draw_settings(context, avs, mpath)


class OBJECT_PT_motion_paths_display(MotionPathButtonsPanel_display, Panel):
    # bl_label = "Object Motion Paths"
    bl_context = "object"
    bl_parent_id = "OBJECT_PT_motion_paths"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.object)

    def draw(self, context):
        # layout = self.layout

        ob = context.object
        avs = ob.animation_visualization
        mpath = ob.motion_path

        self.draw_settings(context, avs, mpath)


class OBJECT_PT_visibility(ObjectButtonsPanel, Panel):
    bl_label = "Visibility"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
        'BLENDER_WORKBENCH',
    }

    @classmethod
    def poll(cls, context):
        return (context.object) and (context.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        layout = self.layout
        ob = context.object

        col = layout.column()
        # bfa - we turn the selectable on or off in the outliner. Not in a hidden panel.
        # col.prop(ob, "hide_select", text="Selectable", toggle=False, invert_checkbox=True)
        col.prop(ob, "hide_surface_pick", text="Surface Picking", toggle=False, invert_checkbox=True)
        
        col = layout.column(align = True)
        col.label(text = "Show in")

        row = col.row()
        row.use_property_split = False
        row.separator()
        row.prop(ob, "hide_viewport", text="Viewports", toggle=False, invert_checkbox=True)
        row.prop_decorator(ob, "hide_viewport")

        row = col.row()
        row.use_property_split = False
        row.separator()
        row.prop(ob, "hide_render", text = "Renders", toggle=False, invert_checkbox=True)
        row.prop_decorator(ob, "hide_render")
        col.separator()

        if context.engine == 'BLENDER_EEVEE':
            if ob.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'CURVES', 'POINTCLOUD', 'VOLUME'}:
                layout.separator()
                col.label(text = "Ray Visibility")
                row = col.row()
                row.use_property_split = False
                row.separator()
                row.prop(ob, "visible_camera", text="Camera", toggle=False)
                row = col.row()
                row.separator()
                row.prop(ob, "visible_shadow", text="Shadow", toggle=False)
                col.separator()

            if ob.type in {'LIGHT'}:
                col.label(text = "Ray Visibility")
                row = col.row()
                row.use_property_split = False
                row = col.row()
                row.separator()
                row.prop(ob, "visible_diffuse", text="Diffuse", toggle=False)
                row = col.row()
                row.separator()
                row.prop(ob, "visible_glossy", text="Glossy", toggle=False)
                row = col.row()
                row.separator()
                row.prop(ob, "visible_transmission", text="Transmission", toggle=False)
                row = col.row()
                row.separator()
                row.prop(ob, "visible_volume_scatter", text="Volume Scatter", toggle=False)

            if ob.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'CURVES', 'POINTCLOUD', 'VOLUME'}:
                col.label(text = "Light Probes")
                row = col.row()
                row.separator()
                row.use_property_split = False
                row.prop(ob, "hide_probe_volume", text="Volume", toggle=False, invert_checkbox=True)
                row = col.row()
                row.separator()
                row.prop(ob, "hide_probe_volume", text="Sphere", toggle=False, invert_checkbox=True)
                row = col.row()
                row.separator()
                row.prop(ob, "hide_probe_plane", text="Plane", toggle=False, invert_checkbox=True)

        if ob.type == 'GREASEPENCIL':

            col.label(text = "Grease Pencil")

            row = col.row()
            row.separator()
            row.use_property_split = False
            row.prop(ob, "use_grease_pencil_lights", toggle=False)
            row.prop_decorator(ob, "use_grease_pencil_lights")
        
        col.separator()
        col.label(text = "Mask")
        row = col.row()
        row.separator()
        row.prop(ob, "is_holdout")
        row.prop_decorator(ob, "is_holdout")


def has_geometry_visibility(ob):
    return ob and (
        (ob.type in {
            'MESH',
            'CURVE',
            'SURFACE',
            'FONT',
            'META',
            'LIGHT',
            'VOLUME',
            'POINTCLOUD',
            'CURVES',
        }) or (ob.instance_type == 'COLLECTION' and ob.instance_collection)
    )


class OBJECT_PT_shading(ObjectButtonsPanel, Panel):
    bl_label = "Shading"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
    }

    @classmethod
    def poll(cls, context):
        if context.engine not in cls.COMPAT_ENGINES:
            return False

        return has_geometry_visibility(context.object)

    def draw(self, context):
        pass

# BFA - light parent panel
class OBJECT_PT_lightoptions(ObjectButtonsPanel, Panel):
    bl_label = "Light Options"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout


class OBJECT_MT_light_linking_context_menu(Menu):
    bl_label = "Light Linking Specials"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.light_linking_receivers_select", icon = 'HAND')


class OBJECT_PT_light_linking(ObjectButtonsPanel, Panel):
    bl_label = "Light Linking"
    bl_parent_id = "OBJECT_PT_lightoptions"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        object = context.object
        light_linking = object.light_linking

        col = layout.column()

        col.template_ID(
            light_linking,
            "receiver_collection",
            new="object.light_linking_receiver_collection_new",
        )

        if not light_linking.receiver_collection:
            return

        row = layout.row()
        col = row.column()
        col.template_light_linking_collection(row, light_linking, "receiver_collection")

        col = row.column()
        sub = col.column(align=True)
        prop = sub.operator("object.light_linking_receivers_link", icon='ADD', text="")
        prop.link_state = 'INCLUDE'
        sub.operator("object.light_linking_unlink_from_collection", icon='REMOVE', text="")
        sub = col.column()
        sub.menu("OBJECT_MT_light_linking_context_menu", icon='DOWNARROW_HLT', text="")


class OBJECT_MT_shadow_linking_context_menu(Menu):
    bl_label = "Shadow Linking Specials"

    def draw(self, _context):
        layout = self.layout

        layout.operator("object.light_linking_blockers_select", icon = 'HAND')

class OBJECT_PT_shadow_linking(ObjectButtonsPanel, Panel):
    bl_label = "Shadow Linking"
    bl_parent_id = "OBJECT_PT_lightoptions" # BFA - moved to own light options
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        object = context.object
        light_linking = object.light_linking

        col = layout.column()

        col.template_ID(
            light_linking,
            "blocker_collection",
            new="object.light_linking_blocker_collection_new",
        )

        if not light_linking.blocker_collection:
            return

        row = layout.row()
        col = row.column()
        col.template_light_linking_collection(row, light_linking, "blocker_collection")

        col = row.column()
        sub = col.column(align=True)
        prop = sub.operator("object.light_linking_blockers_link", icon='ADD', text="")
        prop.link_state = 'INCLUDE'
        sub.operator("object.light_linking_unlink_from_collection", icon='REMOVE', text="")
        sub = col.column()
        sub.menu("OBJECT_MT_shadow_linking_context_menu", icon='DOWNARROW_HLT', text="")


class OBJECT_PT_shadow_terminator(ObjectButtonsPanel, Panel):
    bl_label = "Shadow Terminator"
    bl_parent_id = "OBJECT_PT_shading"
    bl_context = "object"
    COMPAT_ENGINES = {
        'BLENDER_EEVEE',
        'CYCLES',
    }

    @classmethod
    def poll(cls, context):
        return (context.object) and (context.engine in cls.COMPAT_ENGINES) and (context.object.type != 'LIGHT')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=True)

        ob = context.object
        if context.engine == 'BLENDER_EEVEE':
            flow.prop(ob, "shadow_terminator_normal_offset", text="Normal Offset")

        flow.prop(ob, "shadow_terminator_geometry_offset", text="Geometry Offset")

        if context.engine != 'BLENDER_EEVEE':
            flow.prop(ob, "shadow_terminator_shading_offset", text="Shading Offset")


class OBJECT_PT_animation(ObjectButtonsPanel, PropertiesAnimationMixin, PropertyPanel, Panel):
    _animated_id_context_property = "object"


class OBJECT_PT_custom_props(ObjectButtonsPanel, PropertyPanel, Panel):
    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_WORKBENCH',
    }
    _context_path = "object"
    _property_type = bpy.types.Object


classes = (
    OBJECT_PT_context_object,
    OBJECT_PT_transform,
    OBJECT_PT_delta_transform,
    OBJECT_PT_parent_inverse_transform,
    OBJECT_PT_relations,
    COLLECTION_MT_context_menu,
    OBJECT_PT_collections,
    OBJECT_PT_instancing,
    OBJECT_PT_instancing_size,
    OBJECT_PT_motion_paths,
    OBJECT_PT_motion_paths_display,
    OBJECT_PT_display,
    OBJECT_PT_shading,
    OBJECT_PT_lightoptions, # BFA - move light all panels to own parent panel for easier discovery.
    OBJECT_MT_light_linking_context_menu,
    OBJECT_PT_light_linking,
    OBJECT_MT_shadow_linking_context_menu,
    OBJECT_PT_shadow_linking,
    OBJECT_PT_shadow_terminator,
    OBJECT_PT_visibility,
    OBJECT_PT_lineart,
    OBJECT_PT_animation,
    OBJECT_PT_custom_props,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
