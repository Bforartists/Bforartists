# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy, re
from bpy.types import Menu, Operator, Constraint, UILayout, Object
from .hotkeys import register_hotkey
from bpy.props import BoolProperty, StringProperty
from bpy.utils import flip_name
from .pie_camera import get_current_camera


class PIE_MT_object_selection(Menu):
    bl_idname = "PIE_MT_object_selection"
    bl_label = "Object Select"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("object.select_parent_object", text="Parent", icon='FILE_PARENT')
        # 6 - RIGHT
        pie.operator("object.select_children_of_active", text=f"Direct Children", icon='CON_CHILDOF')
        # 2 - BOTTOM
        pie.operator("object.select_all", text="Deselect All", icon='OUTLINER_DATA_POINTCLOUD').action='DESELECT'
        # 8 - TOP
        pie.operator("object.select_all", text="Select All", icon='OUTLINER_OB_POINTCLOUD').action='SELECT'
        # 7 - TOP - LEFT
        pie.operator("object.select_all", text="Invert Selection", icon='CLIPUV_DEHLT').action='INVERT'
        # 9 - TOP - RIGHT
        pie.operator("object.select_siblings_of_active", text="Siblings", icon='PARTICLES')
        # 1 - BOTTOM - LEFT
        text = "Active Camera"
        cam = get_current_camera(context)
        if cam:
            text += f" ({cam.name})"
        pie.operator("object.select_active_camera", text=text, icon='OUTLINER_OB_CAMERA')
        # 3 - BOTTOM - RIGHT
        pie.menu("PIE_MT_object_selection_more", text="Select Menu", icon='THREE_DOTS')


class PIE_MT_object_selection_more(Menu):
    bl_idname = "PIE_MT_object_selection_more"
    bl_label = "More Object Select"

    def draw(self, context):
        layout = self.layout
        
        # Modal selection operators.
        layout.separator()
        layout.operator("view3d.select_circle", text="Circle Select", icon='MESH_CIRCLE')
        layout.operator("view3d.select_box", text="Box Select", icon='SELECT_SET')
        layout.operator_menu_enum("view3d.select_lasso", "mode", icon='MOD_CURVE')

        # Select based on the active object.
        layout.separator()
        layout.operator_menu_enum("object.select_grouped", "type", text="Select Grouped", icon='OUTLINER_COLLECTION')
        layout.operator_menu_enum("object.select_linked", "type", text="Select Linked", icon='DUPLICATE')

        # Select based on parameters.
        layout.separator()
        layout.operator_menu_enum("object.select_by_type", "type", text="Select All by Type", icon='OUTLINER_OB_MESH')
        layout.operator("object.select_random", text="Select Random", icon='RNDCURVE')
        layout.operator("object.select_pattern", text="Select Pattern...", icon='FILTER')
        layout.operator('object.select_by_name_search', icon='VIEWZOOM')

        layout.separator()
        layout.menu("VIEW3D_MT_select_any_camera", text="Select Camera", icon='OUTLINER_OB_CAMERA')


class VIEW3D_MT_select_any_camera(Menu):
    bl_idname = "VIEW3D_MT_select_any_camera"
    bl_label = "Select Camera"

    def draw(self, context):
        layout = self.layout
        active_cam = get_current_camera(context)
        
        all_cams = [obj for obj in sorted(context.scene.objects, key=lambda o: o.name) if obj.type == 'CAMERA']

        for cam in all_cams:
            icon = 'OUTLINER_DATA_CAMERA'
            if cam == active_cam:
                icon = 'OUTLINER_OB_CAMERA'
            layout.operator('object.select_object_by_name', text=cam.name, icon=icon).obj_name=cam.name


### Object relationship selection operators.


def get_selected_parents(context) -> list:
    """Return objects which are selected or active, and have children.
    Active object is always first."""
    objects = context.selected_objects or [context.active_object]
    parents = [o for o in objects if o.children]
    if context.active_object and context.active_object in parents:
        idx = parents.index(context.active_object)
        if idx > -1:
            parents.pop(idx)
        parents.insert(0, context.active_object)
    return parents


def deselect_all_objects(context):
    for obj in context.selected_objects:
        obj.select_set(False)


class ObjectSelectOperatorMixin:
    extend_selection: BoolProperty(
        name="Extend Selection",
        description="Objects that are already selected will remain selected",
    )

    def invoke(self, context, event):
        if event.shift:
            self.extend_selection = True
        else:
            self.extend_selection = False

        return self.execute(context)

    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            cls.poll_message_set("Must be in Object Mode.")
            return False
        return True

    def execute(self, context):
        if not self.extend_selection:
            deselect_all_objects(context)

        return {'FINISHED'}


class OBJECT_OT_select_children_of_active(Operator, ObjectSelectOperatorMixin):
    """Select the children of the active object"""

    bl_idname = "object.select_children_of_active"
    bl_label = "Select Children"
    bl_options = {'REGISTER', 'UNDO'}

    recursive: BoolProperty(default=False, options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False
        obj = context.active_object
        if not (obj and obj.children):
            cls.poll_message_set("Active object has no children.")
            return False
        return True

    @classmethod
    def description(cls, context, props):
        recursively = " recursively" if props.recursive else ""
        return f"Select children of active object{recursively}." + "\n\nShift: Extend current selection"

    def execute(self, context):
        super().execute(context)

        counter = 0
        children = context.active_object.children
        if self.recursive:
            children = context.active_object.children_recursive
        for child in children:
            if not child.select_get():
                counter += 1
                child.select_set(True)

        self.report({'INFO'}, f"Selected {counter} objects.")
        return {'FINISHED'}


class OBJECT_OT_select_siblings_of_active(Operator, ObjectSelectOperatorMixin):
    """Select siblings of active object.\n\nShift: Extend current selection"""

    bl_idname = "object.select_siblings_of_active"
    bl_label = "Select Siblings"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False
        obj = context.active_object
        if not (obj and obj.parent):
            cls.poll_message_set("Active object has no parent.")
            return False
        if not len(obj.parent.children) > 1:
            cls.poll_message_set("Active object has no siblings.")
            return False
        return True

    def execute(self, context):
        super().execute(context)

        counter = 0
        for child in context.active_object.parent.children:
            if not child.select_get():
                counter += 1
                child.select_set(True)

        self.report({'INFO'}, f"Selected {counter} objects.")
        return {'FINISHED'}


class OBJECT_OT_select_parent_object(Operator, ObjectSelectOperatorMixin):
    """Select parent of the active object.\n\nShift: Extend current selection"""

    bl_idname = "object.select_parent_object"
    bl_label = "Select Parent Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False
        obj = context.active_object
        if not (obj and obj.parent):
            cls.poll_message_set("Active object has no parent.")
            return False
        return True

    def execute(self, context):
        super().execute(context)

        active_obj = context.active_object

        active_obj.parent.select_set(True)
        context.view_layer.objects.active = active_obj.parent

        return {'FINISHED'}


class OBJECT_OT_select_active_camera(Operator, ObjectSelectOperatorMixin):
    """Select the active camera of the scene or viewport"""

    bl_idname = "object.select_active_camera"
    bl_label = "Select Active Camera"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        cam = get_current_camera(context)
        if not cam:
            cls.poll_message_set("No active camera.")
            return False
        if not cam.visible_get():
            cls.poll_message_set("Camera is hidden, it cannot be selected.")
            return False
        return True

    def execute(self, context):
        super().execute(context)
        cam = get_current_camera(context)
        if context.active_object and context.mode != 'MODE':
            bpy.ops.object.mode_set(mode='OBJECT')
        cam.select_set(True)
        context.view_layer.objects.active = cam
        return {'FINISHED'}


### Object name-based selection operators.


class PIE_MT_select_object_name_relation(Menu):
    bl_idname = 'PIE_MT_select_object_name_relation'
    bl_label = "Select by Name"

    def draw(self, context):
        layout = self.layout
        active_obj = context.active_object

        pie = layout.menu_pie()

        # 4 - LEFT
        pie.operator(
            OBJECT_OT_select_symmetry_object.bl_idname,
            text="Flip Selection",
            icon='MOD_MIRROR',
        )
        # 6 - RIGHT
        pie.operator('object.select_by_name_search', icon='VIEWZOOM')
        # 2 - BOTTOM
        lower_obj = context.scene.objects.get(increment_name(active_obj.name, increment=-1))
        if lower_obj:
            op = pie.operator('object.select_object_by_name', text=lower_obj.name, icon='TRIA_DOWN')
            op.obj_name = lower_obj.name
        else:
            pie.separator()
        # 8 - TOP
        higher_obj = context.scene.objects.get(increment_name(active_obj.name, increment=1)) or context.scene.objects.get(active_obj.name + ".001")
        if higher_obj:
            op = pie.operator('object.select_object_by_name', text=higher_obj.name, icon='TRIA_UP')
            op.obj_name = higher_obj.name
        else:
            pie.separator()
        # 7 - TOP - LEFT
        constraints = OBJECT_MT_PIE_constrained_objects.get_dependent_constraints(context)
        if len(constraints) == 1:
            draw_select_constraint_owner(pie, constraints[0])
        elif len(constraints) > 1:
            pie.menu('OBJECT_MT_PIE_constrained_objects', icon='THREE_DOTS')
        else:
            pie.separator()
        # 9 - TOP - RIGHT
        constraints = OBJECT_MT_PIE_obj_constraint_targets.get_constraints_with_target(context)
        if len(constraints) == 1:
            draw_select_constraint_target(pie, constraints[0])
        elif len(constraints) > 1:
            pie.menu('OBJECT_MT_PIE_obj_constraint_targets', icon='THREE_DOTS')
        else:
            pie.separator()
        # 1 - BOTTOM - LEFT
        pie.operator("object.select_pattern", text=f"Select Pattern...", icon='FILTER')
        # 3 - BOTTOM - RIGHT
        pie.separator()


class OBJECT_OT_select_symmetry_object(Operator, ObjectSelectOperatorMixin):
    """Select opposite objects.\n\nShift: Extend current selection"""

    bl_idname = "object.select_opposite"
    bl_label = "Select Opposite Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene_obs = context.scene.objects
        sel_obs = context.selected_objects[:]
        active_obj = context.active_object
        flipped_objs = [scene_obs.get(flip_name(ob.name)) for ob in sel_obs]
        flipped_active = scene_obs.get(flip_name(active_obj.name))
        if not (flipped_active or any(flipped_objs)):
            cls.poll_message_set("No selected objects with corresponding opposite objects.")
            return False
        return True

    def execute(self, context):
        scene_obs = context.scene.objects
        sel_obs = context.selected_objects[:]
        active_obj = context.active_object

        flipped_objs = [scene_obs.get(flip_name(ob.name)) for ob in sel_obs]
        flipped_active = scene_obs.get(flip_name(active_obj.name))

        notflipped = sum([flipped_obj in (obj, None) for obj, flipped_obj in zip(sel_obs, flipped_objs)])
        if notflipped > 0:
            self.report({'WARNING'}, f"{notflipped} objects had no opposite.")

        super().execute(context)

        for ob in flipped_objs:
            if not ob:
                continue
            ob.select_set(True)

        if flipped_active:
            context.view_layer.objects.active = flipped_active

        return {'FINISHED'}


class OBJECT_OT_select_object_by_name_search(Operator, ObjectSelectOperatorMixin):
    """Select an object via a search box"""

    bl_idname = "object.select_by_name_search"
    bl_label = "Search Object..."
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: StringProperty(name="Object")

    def invoke(self, context, _event):
        obj = context.active_object
        if obj:
            self.obj_name = obj.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop_search(
            self, 'obj_name', context.scene, 'objects', icon='OBJECT_DATA'
        )
        layout.prop(self, 'extend_selection')

    def execute(self, context):
        obj = context.scene.objects.get(self.obj_name)
        if not self.extend_selection:
            deselect_all_objects(context)

        obj.select_set(True)
        context.view_layer.objects.active = obj

        return {'FINISHED'}


class OBJECT_OT_select_object_by_name(Operator, ObjectSelectOperatorMixin):
    """Select this object.\n\nShift: Extend current selection"""

    bl_idname = "object.select_object_by_name"
    bl_label = "Select Object By Name"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    obj_name: StringProperty(
        name="Object Name", description="Name of the object to select"
    )

    def execute(self, context):
        obj = context.scene.objects.get(self.obj_name)

        if not obj:
            self.report({'ERROR'}, "Object name not found in scene: " + self.obj_name)
            return {'CANCELLED'}

        if not obj.visible_get():
            self.report({'ERROR'}, "Object is hidden, so it cannot be selected.")
            return {'CANCELLED'}

        super().execute(context)

        obj.select_set(True)
        context.view_layer.objects.active = obj

        return {'FINISHED'}


def increment_name(name: str, increment=1, default_zfill=1) -> str:
    # Increment LAST number in the name.
    # Negative numbers will be clamped to 0.
    # Digit length will be preserved, so 10 will decrement to 09.
    # 99 will increment to 100, not 00.

    # If no number was found, one will be added at the end of the base name.
    # The length of this in digits is set with the `default_zfill` param.

    # This is not meant to be able to add a whole .001 suffix at the end of a name,
    # although we can account for the inverse of that easily enough.

    if name.endswith(".001") and increment==-1:
        # Special case.
        return name[:-4]

    numbers_in_name = re.findall(r'\d+', name)
    if not numbers_in_name:
        return name + "_" + str(max(0, increment)).zfill(default_zfill)

    last = numbers_in_name[-1]
    incremented = str(max(0, int(last) + increment)).zfill(len(last))
    split = name.rsplit(last, 1)
    return incremented.join(split)


class OBJECT_MT_PIE_obj_constraint_targets(Menu):
    bl_label = "Constraint Targets"

    @staticmethod
    def get_constraints_with_target(context):
        return [con for con in context.active_object.constraints if hasattr(con, 'target') and con.target in set(context.scene.objects)]

    @classmethod
    def poll(cls, context):
        return cls.get_constraints_with_target(context)

    def draw(self, context):
        layout = self.layout

        for constraint in self.get_constraint_targets(context):
            draw_select_constraint_target(layout, constraint)


class OBJECT_MT_PIE_constrained_objects(Menu):
    bl_label = "Constrained Objects"

    @staticmethod
    def get_dependent_constraints(context):
        dependent_ids = bpy.data.user_map()[context.active_object]
        dependent_objects = [id for id in dependent_ids if type(id)==Object and id in set(context.scene.objects)]
        ret = []
        for dependent_object in dependent_objects:
            for con in dependent_object.constraints:
                if hasattr(con, 'target') and con.target == context.active_object:
                    ret.append(con)
                    break
        return ret

    @classmethod
    def poll(cls, context):
        return cls.get_dependent_constraints(context)

    def draw(self, context):
        layout = self.layout

        for constraint in self.get_dependent_constraints(context):
            draw_select_constraint_owner(layout, constraint)


def draw_select_constraint_target(layout, constraint):
    icon = get_constraint_icon(constraint)
    layout.operator(
        'object.select_object_by_name',
        text=f"Constraint Target: {constraint.target.name} ({constraint.name})",
        icon=icon,
    ).obj_name=constraint.target.name


def draw_select_constraint_owner(layout, constraint):
    icon = get_constraint_icon(constraint)
    layout.operator(
        'object.select_object_by_name',
        text=f"Constrained Object: {constraint.id_data.name} ({constraint.name})",
        icon=icon,
    ).obj_name=constraint.id_data.name


def get_constraint_icon(constraint: Constraint) -> str:
    """We do not ask questions about this function. We accept it."""
    if constraint.type == 'ACTION':
        return 'ACTION'

    icons = UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.keys()
    # This magic number can change between blender versions. Last updated: 4.1.1
    constraint_icon_magic_offset = 42
    return icons[UILayout.icon(constraint) - constraint_icon_magic_offset]

### Mesh selection UI.


class PIE_MT_mesh_selection(Menu):
    bl_idname = "PIE_MT_mesh_selection"
    bl_label = "Mesh Select"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("mesh.select_less", text="Select Less", icon='REMOVE')
        # 6 - RIGHT
        pie.operator("mesh.select_more", text="Select More", icon='ADD')
        # 2 - BOTTOM
        pie.operator("mesh.select_all", text="Deselect All", icon='OUTLINER_DATA_POINTCLOUD').action='DESELECT'
        # 8 - TOP
        pie.operator("mesh.select_all", text="Select All", icon='OUTLINER_OB_POINTCLOUD').action='SELECT'
        # 7 - TOP - LEFT
        pie.operator("mesh.select_all", text="Invert Selection", icon='CLIPUV_DEHLT').action='INVERT'
        # 9 - TOP - RIGHT
        pie.operator("mesh.select_linked", text="Select Linked", icon='FILE_3D')
        # 1 - BOTTOM - LEFT
        pie.operator('wm.call_menu_pie', text='Select Loops...', icon='MOD_WAVE').name='PIE_MT_mesh_selection_loops'
        # 3 - BOTTOM - RIGHT
        pie.menu("PIE_MT_mesh_selection_more", text="More...", icon='THREE_DOTS')


class PIE_MT_mesh_selection_more(Menu):
    bl_idname = "PIE_MT_mesh_selection_more"
    bl_label = "Mesh Selection Mode"

    def draw(self, context):
        layout = self.layout

        vert_mode, edge_mode, face_mode = context.tool_settings.mesh_select_mode

        # Selection modes.
        layout.operator("mesh.select_mode", text="Vertex Select Mode", icon='VERTEXSEL', depress=vert_mode).type = 'VERT'
        layout.operator("mesh.select_mode", text="Edge Select Mode", icon='EDGESEL', depress=edge_mode).type = 'EDGE'
        layout.operator("mesh.select_mode", text="Face Select Mode", icon='FACESEL', depress=face_mode).type = 'FACE'

        # Modal selection operators.
        layout.separator()
        layout.operator("view3d.select_circle", text="Circle Select", icon='MESH_CIRCLE')
        layout.operator("view3d.select_box", text="Box Select", icon='SELECT_SET')
        layout.operator_menu_enum("view3d.select_lasso", "mode", icon='MOD_CURVE')

        # Select based on what's active.
        layout.separator()
        layout.menu("VIEW3D_MT_edit_mesh_select_linked", icon='FILE_3D')
        layout.menu("VIEW3D_MT_edit_mesh_select_similar", icon='CON_TRANSLIKE')
        layout.operator_menu_enum("mesh.select_axis", "axis", text="Select Side", icon='AXIS_SIDE')
        layout.operator("mesh.select_nth", text="Checker Deselect", icon='TEXTURE')

        # Select based on some parameter.
        layout.separator()
        layout.menu("VIEW3D_MT_edit_mesh_select_by_trait")
        layout.operator("mesh.select_by_attribute", text="Select All By Attribute", icon='GEOMETRY_NODES')

        # User-defined GeoNode Select operations.
        layout.template_node_operator_asset_menu_items(catalog_path="Select")


class PIE_MT_mesh_selection_loops(Menu):
    bl_idname = "PIE_MT_mesh_selection_loops"
    bl_label = "Select Loop"

    def draw(self, context):
        pie = self.layout.menu_pie()

        # 4 - LEFT
        pie.operator('mesh.loop_multi_select', text="Edge Loops", icon='MOD_WAVE').ring=False
        # 6 - RIGHT
        pie.operator('mesh.loop_multi_select', text="Edge Rings", icon='CURVES').ring=True
        # 2 - BOTTOM
        pie.operator('mesh.loop_to_region', text="Loop Inner Region", icon='SHADING_SOLID')
        # 8 - TOP
        pie.operator('mesh.region_to_loop', text="Boundary Loop", icon='MESH_CIRCLE')


registry = [
    PIE_MT_object_selection,
    PIE_MT_object_selection_more,
    VIEW3D_MT_select_any_camera,

    OBJECT_OT_select_children_of_active,
    OBJECT_OT_select_siblings_of_active,
    OBJECT_OT_select_parent_object,

    OBJECT_OT_select_active_camera,

    PIE_MT_select_object_name_relation,
    OBJECT_OT_select_symmetry_object,
    OBJECT_OT_select_object_by_name_search,
    OBJECT_OT_select_object_by_name,

    OBJECT_MT_PIE_obj_constraint_targets,
    OBJECT_MT_PIE_constrained_objects,

    PIE_MT_mesh_selection,
    PIE_MT_mesh_selection_more,
    PIE_MT_mesh_selection_loops,
]


def draw_edge_sharpness_in_traits_menu(self, context):
    self.layout.operator("mesh.edges_select_sharp", text="Edge Sharpness")


def register():
    # Weird that this built-in operator is not included in this built-in menu.
    bpy.types.VIEW3D_MT_edit_mesh_select_by_trait.prepend(draw_edge_sharpness_in_traits_menu)

    register_hotkey(
        'wm.call_menu_pie',
        op_kwargs={'name': 'PIE_MT_object_selection'},
        hotkey_kwargs={'type': "A", 'value': "PRESS"},
        key_cat="Object Mode",
    )
    register_hotkey(
        'wm.call_menu_pie',
        op_kwargs={'name': 'PIE_MT_select_object_name_relation'},
        hotkey_kwargs={'type': "F", 'value': "PRESS", 'ctrl': True},
        key_cat="Object Mode",
    )
    register_hotkey(
        'wm.call_menu_pie',
        op_kwargs={'name': 'PIE_MT_mesh_selection'},
        hotkey_kwargs={'type': "A", 'value': "PRESS"},
        key_cat="Mesh",
    )


def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_select_by_trait.remove(draw_edge_sharpness_in_traits_menu)
