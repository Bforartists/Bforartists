# SPDX-FileCopyrightText: 2011-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "AnimAll",
    "author": "Daniel Salazar (ZanQdo), Damien Picard (pioverfour)",
    "version": (0, 10, 1),
    "blender": (4, 0, 0),
    "location": "3D View > Toolbox > Animation tab > AnimAll",
    "description": "Allows animation of mesh, lattice, curve and surface data",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/animation/animall.html",
    "category": "Animation",
}

import bpy
from bpy.types import (Operator, Panel, AddonPreferences)
from bpy.props import (BoolProperty, StringProperty)
from bpy.app.handlers import persistent
from bpy.app.translations import (pgettext_iface as iface_,
                                  pgettext_data as data_)
from . import translations

import re

# Property Definitions
class AnimallProperties(bpy.types.PropertyGroup):
    key_selected: BoolProperty(
        name="Key Selected Only",
        description="Insert keyframes only on selected elements",
        default=False)

    # Generic attributes
    key_point_location: BoolProperty(
        name="Location",
        description="Insert keyframes on point locations",
        default=False)
    key_shape_key: BoolProperty(
        name="Shape Key",
        description="Insert keyframes on active Shape Key layer",
        default=False)
    key_material_index: BoolProperty(
        name="Material Index",
        description="Insert keyframes on face material indices",
        default=False)

    # Mesh attributes
    key_vertex_bevel: BoolProperty(
        name="Vertex Bevel",
        description="Insert keyframes on vertex bevel weight",
        default=False)

    key_vertex_crease: BoolProperty(
        name="Vertex Crease",
        description="Insert keyframes on vertex crease weight",
        default=False)

    key_vertex_group: BoolProperty(
        name="Vertex Group",
        description="Insert keyframes on active vertex group values",
        default=False)

    key_edge_bevel: BoolProperty(
        name="Edge Bevel",
        description="Insert keyframes on edge bevel weight",
        default=False)
    key_edge_crease: BoolProperty(
        name="Edge Crease",
        description="Insert keyframes on edge creases",
        default=False)

    key_active_attribute: BoolProperty(
        name="Active Attribute",
        description="Insert keyframes on active attribute values",
        default=False)
    key_uvs: BoolProperty(
        name="UV Map",
        description="Insert keyframes on active UV coordinates",
        default=False)

    # Curve and surface attributes
    key_radius: BoolProperty(
        name="Radius",
        description="Insert keyframes on point radius (Shrink/Fatten)",
        default=False)
    key_tilt: BoolProperty(
        name="Tilt",
        description="Insert keyframes on point tilt",
        default=False)


# Utility functions

def refresh_ui_keyframes():
    try:
        for area in bpy.context.screen.areas:
            if area.type in ('TIMELINE', 'GRAPH_EDITOR', 'DOPESHEET_EDITOR'):
                area.tag_redraw()
    except:
        pass


def insert_key(data, key, group=None):
    try:
        if group is not None:
            data.keyframe_insert(key, group=group)
        else:
            data.keyframe_insert(key)
    except:
        pass


def delete_key(data, key):
    try:
        data.keyframe_delete(key)
    except:
        pass


def get_attribute(data, name, type=None, domain=None):
    if name in data.attributes:
        return data.attributes[name]
    if type is not None and domain is not None:
        return data.attributes.new(name, type, domain)


def get_attribute_paths(data, attribute, key_selected):
    # Cannot animate string attributes?
    if attribute.data_type == 'STRING':
        return ()

    if attribute.data_type in {'FLOAT', 'INT', 'BOOLEAN', 'INT8'}:
        attribute_key = "value"
    elif attribute.data_type in {'FLOAT_COLOR', 'BYTE_COLOR'}:
        attribute_key = "color"
    elif attribute.data_type in {'FLOAT_VECTOR', 'FLOAT2'}:
        attribute_key = "vector"

    if attribute.domain == 'POINT':
        group = data_("Vertex %s")
    elif attribute.domain == 'EDGE':
        group = data_("Edge %s")
    elif attribute.domain == 'FACE':
        group = data_("Face %s")
    elif attribute.domain == 'CORNER':
        group = data_("Loop %s")

    for e_i, _attribute_data in enumerate(attribute.data):
        if (not key_selected
                or attribute.domain == 'POINT' and data.vertices[e_i].select
                or attribute.domain == 'EDGE' and data.edges[e_i].select
                or attribute.domain == 'FACE' and data.polygons[e_i].select
                or attribute.domain == 'CORNER' and is_selected_vert_loop(data, e_i)):
            yield (f'attributes["{attribute.name}"].data[{e_i}].{attribute_key}', group % e_i)


def insert_attribute_key(data, attribute, key_selected):
    for path, group in get_attribute_paths(data, attribute, key_selected):
        if path:
            insert_key(data, path, group=group)


def delete_attribute_key(data, attribute, key_selected):
    for path, group in get_attribute_paths(data, attribute, key_selected):
        if path:
            delete_key(data, path)


def is_selected_vert_loop(data, loop_i):
    """Get selection status of vertex corresponding to a loop"""
    vertex_index = data.loops[loop_i].vertex_index
    return data.vertices[vertex_index].select


# GUI (Panel)

class VIEW3D_PT_animall(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Animation"
    bl_label = ''

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.type in {'MESH', 'LATTICE', 'CURVE', 'SURFACE'}

    def draw_header(self, context):

        layout = self.layout
        row = layout.row()
        row.label(text='AnimAll', icon='ARMATURE_DATA')

    def draw(self, context):
        obj = context.active_object
        animall_properties = context.scene.animall_properties

        layout = self.layout

        layout.label(text='Key:')

        layout.use_property_split = True
        layout.use_property_decorate = False

        if obj.type == 'LATTICE':
            col = layout.column(heading="Points", align=True)
            col.prop(animall_properties, "key_point_location")

            col = layout.column(heading="Others", align=True)
            col.prop(animall_properties, "key_shape_key")

        elif obj.type == 'MESH':
            col = layout.column(heading="Points", align=True)
            col.prop(animall_properties, "key_point_location")
            col.prop(animall_properties, "key_vertex_bevel", text="Bevel")
            col.prop(animall_properties, "key_vertex_crease", text="Crease")
            col.prop(animall_properties, "key_vertex_group")

            col = layout.column(heading="Edges", align=True)
            col.prop(animall_properties, "key_edge_bevel", text="Bevel")
            col.prop(animall_properties, "key_edge_crease", text="Crease")

            col = layout.column(heading="Faces", align=True)
            col.prop(animall_properties, "key_material_index")

            col = layout.column(heading="Others", align=True)
            col.prop(animall_properties, "key_active_attribute")
            col.prop(animall_properties, "key_uvs")
            col.prop(animall_properties, "key_shape_key")

        elif obj.type in {'CURVE', 'SURFACE'}:
            col = layout.column(align=True)
            col = layout.column(heading="Points", align=True)
            col.prop(animall_properties, "key_point_location")
            col.prop(animall_properties, "key_radius")
            col.prop(animall_properties, "key_tilt")

            col = layout.column(heading="Splines", align=True)
            col.prop(animall_properties, "key_material_index")

            col = layout.column(heading="Others", align=True)
            col.prop(animall_properties, "key_shape_key")

        if animall_properties.key_shape_key:
            shape_key = obj.active_shape_key
            shape_key_index = obj.active_shape_key_index

            if shape_key_index > 0:
                col = layout.column(align=True)
                row = col.row(align=True)
                row.prop(shape_key, "value", text=shape_key.name, icon="SHAPEKEY_DATA")
                row.prop(obj, "show_only_shape_key", text="")
                if shape_key.value < 1:
                    col.label(text=iface_('Maybe set "%s" to 1.0?') % shape_key.name, icon="INFO")
            elif shape_key is not None:
                col = layout.column(align=True)
                col.label(text="Cannot key on Basis Shape", icon="ERROR")
            else:
                col = layout.column(align=True)
                col.label(text="No active Shape Key", icon="ERROR")

            if animall_properties.key_point_location:
                col.label(text='"Location" and "Shape Key" are redundant?', icon="INFO")

        layout.use_property_split = False
        layout.separator()
        row = layout.row()
        row.prop(animall_properties, "key_selected")

        row = layout.row(align=True)
        row.operator("anim.insert_keyframe_animall", icon="KEY_HLT")
        row.operator("anim.delete_keyframe_animall", icon="KEY_DEHLT")
        row = layout.row()
        row.operator("anim.clear_animation_animall", icon="CANCEL")


class ANIM_OT_insert_keyframe_animall(Operator):
    bl_label = "Insert Key"
    bl_idname = "anim.insert_keyframe_animall"
    bl_description = "Insert a Keyframe"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        animall_properties = context.scene.animall_properties

        if context.mode == 'OBJECT':
            objects = context.selected_objects
        else:
            objects = context.objects_in_mode_unique_data[:]

        mode = context.object.mode

        # Separate loop for lattices, curves and surfaces, since keyframe insertion
        # has to happen in Edit Mode, otherwise points move back upon mode switch...
        # (except for curve shape keys)
        for obj in [o for o in objects if o.type in {'CURVE', 'SURFACE', 'LATTICE'}]:
            data = obj.data

            if obj.type == 'LATTICE':
                if animall_properties.key_shape_key:
                    if obj.active_shape_key_index > 0:
                        sk_name = obj.active_shape_key.name
                        for p_i, point in enumerate(obj.active_shape_key.data):
                            if not animall_properties.key_selected or data.points[p_i].select:
                                insert_key(point, 'co', group=data_("%s Point %s") % (sk_name, p_i))

                if animall_properties.key_point_location:
                    for p_i, point in enumerate(data.points):
                        if not animall_properties.key_selected or point.select:
                            insert_key(point, 'co_deform', group=data_("Point %s") % p_i)

            else:
                if animall_properties.key_material_index:
                    for s_i, spline in enumerate(data.splines):
                        if (not animall_properties.key_selected
                                or any(point.select for point in spline.points)
                                or any(point.select_control_point for point in spline.bezier_points)):
                            insert_key(spline, 'material_index', group=data_("Spline %s") % s_i)

                for s_i, spline in enumerate(data.splines):
                    if spline.type == 'BEZIER':
                        for v_i, CV in enumerate(spline.bezier_points):
                            if (not animall_properties.key_selected
                                    or CV.select_control_point
                                    or CV.select_left_handle
                                    or CV.select_right_handle):
                                if animall_properties.key_point_location:
                                    insert_key(CV, 'co', group=data_("Spline %s CV %s") % (s_i, v_i))
                                    insert_key(CV, 'handle_left', group=data_("Spline %s CV %s") % (s_i, v_i))
                                    insert_key(CV, 'handle_right', group=data_("Spline %s CV %s") % (s_i, v_i))

                                if animall_properties.key_radius:
                                    insert_key(CV, 'radius', group=data_("Spline %s CV %s") % (s_i, v_i))

                                if animall_properties.key_tilt:
                                    insert_key(CV, 'tilt', group=data_("Spline %s CV %s") % (s_i, v_i))

                    elif spline.type in ('POLY', 'NURBS'):
                        for v_i, CV in enumerate(spline.points):
                            if not animall_properties.key_selected or CV.select:
                                if animall_properties.key_point_location:
                                    insert_key(CV, 'co', group=data_("Spline %s CV %s") % (s_i, v_i))

                                if animall_properties.key_radius:
                                    insert_key(CV, 'radius', group=data_("Spline %s CV %s") % (s_i, v_i))

                                if animall_properties.key_tilt:
                                    insert_key(CV, 'tilt', group=data_("Spline %s CV %s") % (s_i, v_i))

        bpy.ops.object.mode_set(mode='OBJECT')

        for obj in [o for o in objects if o.type in {'MESH', 'CURVE', 'SURFACE'}]:
            data = obj.data
            if obj.type == 'MESH':
                if animall_properties.key_point_location:
                    for v_i, vert in enumerate(data.vertices):
                        if not animall_properties.key_selected or vert.select:
                            insert_key(vert, 'co', group=data_("Vertex %s") % v_i)

                if animall_properties.key_vertex_bevel:
                    attribute = get_attribute(data, "bevel_weight_vert", 'FLOAT', 'POINT')
                    insert_attribute_key(data, attribute, animall_properties.key_selected)

                if animall_properties.key_vertex_crease:
                    attribute = get_attribute(data, "crease_vert", 'FLOAT', 'POINT')
                    insert_attribute_key(data, attribute, animall_properties.key_selected)

                if animall_properties.key_vertex_group:
                    for v_i, vert in enumerate(data.vertices):
                        if not animall_properties.key_selected or vert.select:
                            for group in vert.groups:
                                insert_key(group, 'weight', group=data_("Vertex %s") % v_i)

                if animall_properties.key_edge_bevel:
                    attribute = get_attribute(data, "bevel_weight_edge", 'FLOAT', 'EDGE')
                    insert_attribute_key(data, attribute, animall_properties.key_selected)

                if animall_properties.key_edge_crease:
                    attribute = get_attribute(data, "crease_edge", 'FLOAT', 'EDGE')
                    insert_attribute_key(data, attribute, animall_properties.key_selected)

                if animall_properties.key_material_index:
                    for p_i, polygon in enumerate(data.polygons):
                        if not animall_properties.key_selected or polygon.select:
                            insert_key(polygon, 'material_index', group=data_("Face %s") % p_i)

                if animall_properties.key_active_attribute:
                    if data.attributes.active is not None:
                        for path, group in get_attribute_paths(
                                data, data.attributes.active,
                                animall_properties.key_selected):
                            if path:
                                insert_key(data, path, group=group)

                if animall_properties.key_uvs:
                    if data.uv_layers.active is not None:
                        for uv_i, uv in enumerate(data.uv_layers.active.data):
                            if not animall_properties.key_selected or uv.select:
                                insert_key(uv, 'uv', group=data_("UV Layer %s") % uv_i)

                if animall_properties.key_shape_key:
                    if obj.active_shape_key_index > 0:
                        sk_name = obj.active_shape_key.name
                        for v_i, vert in enumerate(obj.active_shape_key.data):
                            if not animall_properties.key_selected or data.vertices[v_i].select:
                                insert_key(vert, 'co', group=data_("%s Vertex %s") % (sk_name, v_i))

            elif obj.type in {'CURVE', 'SURFACE'}:
                # Shape key keys have to be inserted in object mode for curves...
                if animall_properties.key_shape_key:
                    sk_name = obj.active_shape_key.name
                    global_spline_index = 0  # numbering for shape keys, which have flattened indices
                    for s_i, spline in enumerate(data.splines):
                        if spline.type == 'BEZIER':
                            for v_i, CV in enumerate(spline.bezier_points):
                                if (not animall_properties.key_selected
                                        or CV.select_control_point
                                        or CV.select_left_handle
                                        or CV.select_right_handle):
                                    if obj.active_shape_key_index > 0:
                                        CV = obj.active_shape_key.data[global_spline_index]
                                        insert_key(CV, 'co', group=data_("%s Spline %s CV %s") % (sk_name, s_i, v_i))
                                        insert_key(
                                            CV, 'handle_left', group=data_("%s Spline %s CV %s") %
                                            (sk_name, s_i, v_i))
                                        insert_key(
                                            CV, 'handle_right', group=data_("%s Spline %s CV %s") %
                                            (sk_name, s_i, v_i))
                                        insert_key(
                                            CV, 'radius', group=data_("%s Spline %s CV %s") %
                                            (sk_name, s_i, v_i))
                                        insert_key(CV, 'tilt', group=data_("%s Spline %s CV %s") % (sk_name, s_i, v_i))
                                global_spline_index += 1

                        elif spline.type in ('POLY', 'NURBS'):
                            for v_i, CV in enumerate(spline.points):
                                if not animall_properties.key_selected or CV.select:
                                    if obj.active_shape_key_index > 0:
                                        CV = obj.active_shape_key.data[global_spline_index]
                                        insert_key(CV, 'co', group=data_("%s Spline %s CV %s") % (sk_name, s_i, v_i))
                                        insert_key(
                                            CV, 'radius', group=data_("%s Spline %s CV %s") % (sk_name, s_i, v_i))
                                        insert_key(CV, 'tilt', group=data_("%s Spline %s CV %s") % (sk_name, s_i, v_i))
                                global_spline_index += 1

        bpy.ops.object.mode_set(mode=mode)
        refresh_ui_keyframes()

        return {'FINISHED'}


class ANIM_OT_delete_keyframe_animall(Operator):
    bl_label = "Delete Key"
    bl_idname = "anim.delete_keyframe_animall"
    bl_description = "Delete a Keyframe"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        animall_properties = context.scene.animall_properties

        if context.mode == 'OBJECT':
            objects = context.selected_objects
        else:
            objects = context.objects_in_mode_unique_data[:]

        mode = context.object.mode

        for obj in objects:
            data = obj.data
            if obj.type == 'MESH':
                bpy.ops.object.mode_set(mode='OBJECT')

                if animall_properties.key_point_location:
                    for vert in data.vertices:
                        if not animall_properties.key_selected or vert.select:
                            delete_key(vert, 'co')

                if animall_properties.key_vertex_bevel:
                    attribute = get_attribute(data, "bevel_weight_vert", 'FLOAT', 'POINT')
                    if attribute is not None:
                        delete_attribute_key(data, attribute, animall_properties.key_selected)

                if animall_properties.key_vertex_crease:
                    attribute = get_attribute(data, "crease_vert", 'FLOAT', 'POINT')
                    if attribute is not None:
                        delete_attribute_key(data, attribute, animall_properties.key_selected)

                if animall_properties.key_vertex_group:
                    for vert in data.vertices:
                        if not animall_properties.key_selected or vert.select:
                            for group in vert.groups:
                                delete_key(group, 'weight')

                if animall_properties.key_edge_bevel:
                    attribute = get_attribute(data, "bevel_weight_edge", 'FLOAT', 'EDGE')
                    if attribute is not None:
                        delete_attribute_key(data, attribute, animall_properties.key_selected)

                if animall_properties.key_edge_crease:
                    attribute = get_attribute(data, "crease_edge", 'FLOAT', 'EDGE')
                    if attribute is not None:
                        delete_attribute_key(data, attribute, animall_properties.key_selected)

                if animall_properties.key_material_index:
                    for p_i, polygon in enumerate(data.polygons):
                        if not animall_properties.key_selected or polygon.select:
                            delete_key(polygon, 'material_index')

                if animall_properties.key_shape_key:
                    if obj.active_shape_key:
                        for v_i, vert in enumerate(obj.active_shape_key.data):
                            if not animall_properties.key_selected or data.vertices[v_i].select:
                                delete_key(vert, 'co')

                if animall_properties.key_uvs:
                    if data.uv_layers.active is not None:
                        for uv in data.uv_layers.active.data:
                            if not animall_properties.key_selected or uv.select:
                                delete_key(uv, 'uv')

                if animall_properties.key_active_attribute:
                    if data.attributes.active is not None:
                        for path, _group in get_attribute_paths(
                                data, data.attributes.active,
                                animall_properties.key_selected):
                            if path:
                                delete_key(data, path)

                bpy.ops.object.mode_set(mode=mode)

            elif obj.type == 'LATTICE':
                if animall_properties.key_shape_key:
                    if obj.active_shape_key:
                        for point in obj.active_shape_key.data:
                            delete_key(point, 'co')

                if animall_properties.key_point_location:
                    for point in data.points:
                        if not animall_properties.key_selected or point.select:
                            delete_key(point, 'co_deform')

            elif obj.type in {'CURVE', 'SURFACE'}:
                # Run this outside the splines loop (only once)
                if animall_properties.key_shape_key:
                    if obj.active_shape_key_index > 0:
                        for CV in obj.active_shape_key.data:
                            delete_key(CV, 'co')
                            delete_key(CV, 'handle_left')
                            delete_key(CV, 'handle_right')

                for spline in data.splines:
                    if spline.type == 'BEZIER':
                        for CV in spline.bezier_points:
                            if (not animall_properties.key_selected
                                    or CV.select_control_point
                                    or CV.select_left_handle
                                    or CV.select_right_handle):
                                if animall_properties.key_point_location:
                                    delete_key(CV, 'co')
                                    delete_key(CV, 'handle_left')
                                    delete_key(CV, 'handle_right')
                                if animall_properties.key_radius:
                                    delete_key(CV, 'radius')
                                if animall_properties.key_tilt:
                                    delete_key(CV, 'tilt')

                    elif spline.type in ('POLY', 'NURBS'):
                        for CV in spline.points:
                            if not animall_properties.key_selected or CV.select:
                                if animall_properties.key_point_location:
                                    delete_key(CV, 'co')
                                if animall_properties.key_radius:
                                    delete_key(CV, 'radius')
                                if animall_properties.key_tilt:
                                    delete_key(CV, 'tilt')

        refresh_ui_keyframes()

        return {'FINISHED'}


class ANIM_OT_clear_animation_animall(Operator):
    bl_label = "Clear Animation"
    bl_idname = "anim.clear_animation_animall"
    bl_description = ("Delete all keyframes for this object\n"
                      "If in a specific case it doesn't work\n"
                      "try to delete the keys manually")
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)

    def execute(self, context):
        if context.mode == 'OBJECT':
            objects = context.selected_objects
        else:
            objects = context.objects_in_mode_unique_data

        for obj in objects:
            try:
                data = obj.data
                data.animation_data_clear()
            except:
                self.report({'WARNING'}, "Clear Animation could not be performed")
                return {'CANCELLED'}

        refresh_ui_keyframes()

        return {'FINISHED'}


# Add-ons Preferences Update Panel

# Define Panel classes for updating
panels = [VIEW3D_PT_animall]


def update_panel(self, context):
    message = "AnimAll: Updating Panel locations has failed"
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panels:
            panel.bl_category = context.preferences.addons[__name__].preferences.category
            bpy.utils.register_class(panel)

    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))
        pass


class AnimallAddonPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    category: StringProperty(
        name="Tab Category",
        description="Choose a name for the category of the panel",
        default="Animation",
        update=update_panel
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column()

        col.label(text="Tab Category:")
        col.prop(self, "category", text="")


@persistent
def update_attribute_animation(_):
    """Update attributes from the old format"""
    path_re = re.compile(r"^vertex_colors|(vertices|edges)\[([0-9]+)\]\.(bevel_weight|crease)")
    attribute_map = {
        ("vertices", "bevel_weight"): ("bevel_weight_vert", "FLOAT", "POINT"),
        ("edges", "bevel_weight"):    ("bevel_weight_edge", "FLOAT", "POINT"),
        ("vertices", "crease"):       ("crease_vert", "FLOAT", "EDGE"),
        ("edges", "crease"):          ("crease_edge", "FLOAT", "EDGE"),
    }
    for mesh in bpy.data.meshes:
        print(f"Updating {mesh.name}")
        for fcurve in mesh.animation_data.action.fcurves:
            if fcurve.data_path.startswith("vertex_colors"):
                # Update pre-3.3 vertex colors
                fcurve.data_path = fcurve.data_path.replace("vertex_colors", "attributes")
            else:
                # Update pre-4.0 attributes
                match = path_re.match(fcurve.data_path)
                if match is None:
                    continue
                domain, index, src_attribute = match.groups()
                attribute, type, domain = attribute_map[(domain, src_attribute)]
                get_attribute(mesh, attribute, type, domain)
                fcurve.data_path = f'attributes["{attribute}"].data[{index}].value'


register_classes, unregister_classes = bpy.utils.register_classes_factory(
    (AnimallProperties, VIEW3D_PT_animall, ANIM_OT_insert_keyframe_animall,
     ANIM_OT_delete_keyframe_animall, ANIM_OT_clear_animation_animall,
     AnimallAddonPreferences))

def register():
    register_classes()
    bpy.types.Scene.animall_properties = bpy.props.PointerProperty(type=AnimallProperties)
    update_panel(None, bpy.context)
    bpy.app.handlers.load_post.append(update_attribute_animation)
    bpy.app.translations.register(__name__, translations.translations_dict)

def unregister():
    bpy.app.translations.unregister(__name__)
    bpy.app.handlers.load_post.remove(update_attribute_animation)
    del bpy.types.Scene.animall_properties
    unregister_classes()

if __name__ == "__main__":
    register()
