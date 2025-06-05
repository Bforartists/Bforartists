# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Menu, Operator
from bpy.props import BoolProperty, EnumProperty
from mathutils import Matrix

from .op_pie_wrappers import WM_OT_call_menu_pie_drag_only


class OBJECT_MT_parenting_pie(Menu):
    bl_label = 'Object Parenting'
    bl_idname = 'OBJECT_MT_parenting_pie'

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        # <
        # Clear Parent (Keep Transform)
        pie.operator(
            OBJECT_OT_clear_parent.bl_idname,
            text="Clear Parent",
            icon='X',
        ).keep_transform = True

        # >
        # Set Parent (Keep Transform)
        pie.operator(OBJECT_OT_parent_set_simple.bl_idname, icon='CON_CHILDOF')

        # v
        pie.separator()

        # ^
        pie.separator()

        # <^
        # Clear Parent
        pie.operator(
            OBJECT_OT_clear_parent.bl_idname,
            text="Clear Parent (Without Correction)",
            icon='UNLINKED',
        ).keep_transform = False

        # ^>
        # Set Parent (Advanced)
        pie.operator(OBJECT_OT_parent_set_advanced.bl_idname, icon='CON_CHILDOF')

        # <v
        # Clear Inverse
        pie.operator(
            OBJECT_OT_clear_parent_inverse_matrix.bl_idname,
            text="Clear Offset Correction",
            icon='DRIVER_DISTANCE',
        )

        # v>
        pie.separator()


def selected_objs_with_parents(context):
    return [ob for ob in context.selected_objects if ob.parent]


class OBJECT_OT_clear_parent(Operator):
    """Clear the parent of selected objects"""

    bl_idname = "object.parent_clear_py"
    bl_label = "Clear Parent"
    bl_options = {'REGISTER', 'UNDO'}

    keep_transform: BoolProperty(
        name="Keep Transform",
        description="Whether to preserve the object's world-space transforms by affecting its local space transforms",
    )

    @classmethod
    def description(cls, context, properties):
        if properties.keep_transform:
            return "Clear the parent of selected objects, while preserving their position in space"
        else:
            return "Clear the parent of selected objects, without affecting their Loc/Rot/Scale values. This may cause the now parentless children to change position"

    @classmethod
    def poll(cls, context):
        if not selected_objs_with_parents(context):
            cls.poll_message_set("No selected objects have parents.")
            return False

        return set_parent_poll_check_linked(cls, context)

    def execute(self, context):
        objs = selected_objs_with_parents(context)

        op_type = 'CLEAR_KEEP_TRANSFORM' if self.keep_transform else 'CLEAR'
        bpy.ops.object.parent_clear(type=op_type)

        # Report what was done.
        objs_str = objs[0].name if len(objs) == 1 else f"{len(objs)} objects"
        self.report({'INFO'}, f"Cleared parent of {objs_str}")
        return {'FINISHED'}


class OBJECT_OT_clear_parent_inverse_matrix(Operator):
    """Preserve the parenting relationship, but clear the correction offset, such that when the child's transforms are reset, it will move to the same position as the parent"""

    bl_idname = "object.parent_clear_inverse_matrix_py"
    bl_label = "Clear Parent Inverse Matrix"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        objs_with_parents = selected_objs_with_parents(context)
        if not objs_with_parents:
            cls.poll_message_set("No selected objects have parents.")
            return False

        identity_matrix = Matrix.Identity(4)
        if not any(
            [obj.matrix_parent_inverse != identity_matrix for obj in objs_with_parents]
        ):
            cls.poll_message_set("No selected objects have a parenting offset set.")
            return False

        return set_parent_poll_check_linked(cls, context)

    def execute(self, context):
        objs = selected_objs_with_parents(context)
        bpy.ops.object.parent_clear(type='CLEAR_INVERSE')

        # Report what was done.
        objs_str = objs[0].name if len(objs) == 1 else f"{len(objs)} objects"
        self.report({'INFO'}, f"Cleared parenting offset of {objs_str}")
        return {'FINISHED'}


class OBJECT_OT_parent_set_simple(Operator):
    """Parent the selected objects to the active one, while preserving their position in space"""

    bl_idname = "object.parent_set_simple"
    bl_label = "Set Parent"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not len(context.selected_objects) > 1 and context.active_object:
            cls.poll_message_set(
                "Only one object is selected. You can't parent an object to itself."
            )
            return False

        return set_parent_poll_check_linked(cls, context)

    def execute(self, context):
        parent_ob = context.active_object
        objs_to_parent = [obj for obj in context.selected_objects if obj != parent_ob]

        try:
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}

        # Report what was done.
        objs_str = (
            objs_to_parent[0].name
            if len(objs_to_parent) == 1
            else f"{len(objs_to_parent)} objects"
        )
        self.report({'INFO'}, f"Parented {objs_str} to {parent_ob.name}")
        return {'FINISHED'}


class OBJECT_OT_parent_set_advanced(Operator):
    """Parent selected objects to the active one"""

    bl_idname = "object.parent_set_advanced"
    bl_label = "Set Parent (Advanced)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not len(context.selected_objects) > 1 and context.active_object:
            cls.poll_message_set(
                "Only one object is selected. You can't parent an object to itself."
            )
            return False

        return set_parent_poll_check_linked(cls, context)

    def get_parent_method_items(self, context):
        parent_ob = context.active_object
        items = [
            (
                'OBJECT',
                "Object",
                "Use simple object parenting, with no additional behaviours",
                'OBJECT_DATAMODE',
            ),
            (
                'CONSTRAINT',
                "Constraint",
                "Create a constraint-based parenting set-up",
                'CONSTRAINT',
            ),
        ]
        if parent_ob.type == 'ARMATURE':
            items.append(
                (
                    'MODIFIER',
                    "Armature Modifier",
                    "Add an Armature Modifier to the children, so they are deformed by this armature",
                    'MODIFIER',
                )
            )
            if parent_ob.data.bones.active:
                items.append(
                    (
                        'BONE_RELATIVE',
                        "Bone: " + parent_ob.data.bones.active.name,
                        """Parent to the armature's active bone. This option is deprecated, please set the "Parent Method" to "Constraint", and choose the Armature Constraint""",
                        'BONE_DATA',
                    )
                )
        elif parent_ob.type == 'CURVE':
            items.append(
                (
                    'MODIFIER',
                    "Curve Modifier",
                    "Add a Curve Modifier to the children, so they are deformed by this curve",
                    'MODIFIER',
                )
            )
            items.append(
                (
                    'FOLLOW',
                    "(Legacy) Follow Path",
                    """Animate the curve's Evaluation Time, causing all children to move along the path over time. This option is deprecated, please set the "Parent Method" to "Constraint", and choose the Follow Path Constraint""",
                    'CURVE_DATA',
                )
            )
        elif parent_ob.type == 'LATTICE':
            items.append(
                (
                    'MODIFIER',
                    "Lattice Modifier",
                    "Add a Lattice Modifier to the children, so they are deformed by this lattice",
                    'MODIFIER',
                )
            )

        if parent_ob.type in ('MESH', 'CURVE', 'LATTICE'):
            items.append(
                (
                    'VERTEX',
                    "Nearest Point",
                    "Parent to the nearest point (mesh vertex, lattice point, curve point) of the target object",
                    'VERTEXSEL',
                )
            )
            items.append(
                (
                    'VERTEX_TRI',
                    "Nearest Triangle",
                    "Parent to the nearest 3 points of the target object",
                    'MESH_DATA',
                )
            )

        return [
            (item[0], item[1], item[2], item[3], idx) for idx, item in enumerate(items)
        ]

    parent_method: EnumProperty(
        name="Parent Method",
        description="Type of parenting behaviour",
        items=get_parent_method_items,
        default=0,
    )

    def get_constraint_type_items(self, context):
        items = [
            (
                'COPY_TRANSFORMS',
                "Copy Transforms",
                "In addition to Object parenting, add a Copy Transforms constraint to the children, which snaps and locks them to the parent in world space",
                'CON_TRANSLIKE',
                0,
            ),
            (
                'CHILD_OF',
                "Child Of",
                "Instead of Object parenting, add a Child Of constraint to the children. This preserves the child's world-space transforms as well as their Loc/Rot/Scale values, by storing a parenting offset in the constraint itself",
                'CON_CHILDOF',
                1,
            ),
        ]
        if context.active_pose_bone:
            items.append(
                (
                    'ARMATURE',
                    "Armature",
                    "In addition to Object parenting, add an Armature constraint to the children. The child objects will only follow the parent bone when it is moved in Pose Mode, but not when it is moved in Edit Mode",
                    'CON_ARMATURE',
                    2,
                )
            )
        elif context.active_object.type == 'CURVE':
            items.append(
                (
                    'FOLLOW_PATH',
                    "Follow Path",
                    "Instead of parenting, add a Follow Path constraint to the children, and animate the curve's Evaluation Time, causing the constrained objects to follow the curve's path over time",
                    'CON_FOLLOWPATH',
                    2,
                )
            )
        return items

    constraint_type: EnumProperty(
        name="Constraint Type",
        description="What type of Constraint to use for parenting",
        items=get_constraint_type_items,
    )

    vgroup_init_method: EnumProperty(
        name="Initialize Vertex Groups",
        items=[
            (
                'NONE',
                "None",
                "Do not initialize vertex groups on the child meshes",
                'BLANK1',
                0,
            ),
            (
                'EMPTY_GROUPS',
                "Empty Groups",
                "On all child meshes, generate empty vertex groups for each deforming bone of the parent Armature",
                'GROUP_VERTEX',
                1,
            ),
            (
                'PROXIMITY_WEIGHTS',
                "Auto-Weights",
                "On all child meshes, generate Vertex Groups for the parent Armature's deforming bones, based on the mesh surface's proximity to each bone",
                'ARMATURE_DATA',
                2,
            ),
            (
                'ENVELOPE_WEIGHTS',
                "Auto-Weights (From Envelopes)",
                "On all child meshes, generate vertex groups using the parent Armature's bone envelopes",
                'OUTLINER_OB_ARMATURE',
                3,
            ),
        ],
    )

    transform_correction: EnumProperty(
        name="Keep Transform",
        description="This parent is transformed. This will result in the child moving by the same amount when the relationship is created",
        items=[
            (
                'NONE',
                "None",
                "Simply create the parenting relationship, even if it may cause the children to be moved",
                'UNPINNED',
                0,
            ),
            (
                'MATRIX_LOCAL',
                "Normal",
                "After creating the relationship, snap the children back to their original positions. This will affect their Loc/Rot/Scale values",
                'PINNED',
                1,
            ),
            (
                'MATRIX_INTERNAL',
                "Magic Offset",
                "The child will not move and its Loc/Rot/Scale values won't be affected, even if the parent is transformed. This is done by storing an internal parenting offset value",
                'SHADERFX',
                2,
            ),
        ],
        default='MATRIX_LOCAL',
    )

    def invoke(self, context, _event):
        parent_ob = context.active_object
        if parent_ob.type == 'ARMATURE':
            self.parent_method = 'MODIFIER'

        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        parent_ob = context.active_object

        layout.prop(self, 'parent_method')

        if self.parent_method == 'CONSTRAINT':
            layout.prop(self, 'constraint_type', icon='CONSTRAINT')
        elif self.parent_method == 'MODIFIER':
            if parent_ob.type == 'ARMATURE':
                layout.prop(self, 'vgroup_init_method', icon='GROUP_VERTEX')

        if self.parent_method == 'CONSTRAINT' and self.constraint_type != 'ARMATURE':
            # Skip drawing transform_correction for constraint types where
            # it's irrelevant.
            return

        if parent_ob.matrix_world != Matrix.Identity(4):
            # If the parent has any world-space transforms, we offer corrections
            # for that to be applied to the children, so they don't move.
            layout.prop(self, 'transform_correction')

    def execute(self, context):
        parent_ob = context.active_object
        keep_transform = self.transform_correction == 'MATRIX_INTERNAL'

        objs_to_parent = [obj for obj in context.selected_objects if obj != parent_ob]
        matrix_backups = [
            (obj.matrix_world.copy(), obj.matrix_local.copy()) for obj in objs_to_parent
        ]

        op_parent_method = self.parent_method

        if self.parent_method == 'MODIFIER':
            if parent_ob.type == 'ARMATURE':
                if self.vgroup_init_method == 'NONE':
                    op_parent_method = 'ARMATURE'
                elif self.vgroup_init_method == 'EMPTY_GROUPS':
                    op_parent_method = 'ARMATURE_NAME'
                elif self.vgroup_init_method == 'ENVELOPE_WEIGHTS':
                    op_parent_method = 'ARMATURE_ENVELOPE'
                elif self.vgroup_init_method == 'PROXIMITY_WEIGHTS':
                    op_parent_method = 'ARMATURE_AUTO'
            elif parent_ob.type == 'LATTICE':
                op_parent_method = 'LATTICE'
            elif parent_ob.type == 'CURVE':
                op_parent_method = 'CURVE'
        elif self.parent_method == 'CONSTRAINT':
            if self.constraint_type == 'FOLLOW_PATH':
                op_parent_method = 'PATH_CONST'
            elif self.constraint_type == 'ARMATURE':
                return self.parent_with_arm_con(context, keep_transform)
            elif self.constraint_type == 'CHILD_OF':
                return self.parent_with_child_of_con(context)
            elif self.constraint_type == 'COPY_TRANSFORMS':
                return self.parent_with_copy_transforms_con(context)

        try:
            bpy.ops.object.parent_set(
                type=op_parent_method, keep_transform=keep_transform
            )
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}

        if self.transform_correction != 'MATRIX_INTERNAL':
            for obj in objs_to_parent:
                obj.matrix_parent_inverse = Matrix.Identity(4)
        if self.transform_correction == 'MATRIX_LOCAL':
            for obj, matrices in zip(objs_to_parent, matrix_backups):
                # Find expected world matrix of this object:
                # Parent world matrix @ inverted self inverse matrix @ basis matrix
                obj.matrix_local = matrices[1]
                obj.matrix_world = matrices[0]

        # Report what was done.
        objs_str = (
            objs_to_parent[0].name
            if len(objs_to_parent) == 1
            else f"{len(objs_to_parent)} objects"
        )
        self.report({'INFO'}, f"Parented {objs_str} to {parent_ob.name}")
        return {'FINISHED'}

    def parent_with_arm_con(self, context, keep_transform):
        """Parent selected objects to the active bone."""
        rig = context.active_object
        active_bone = rig.data.bones.active
        if not active_bone:
            self.report({'ERROR'}, "No active bone.")
            return {'CANCELLED'}

        try:
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=keep_transform)
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}

        objs_to_parent = [obj for obj in context.selected_objects if obj != rig]
        for obj in objs_to_parent:
            arm_con = None
            for con in obj.constraints:
                if con.type == 'ARMATURE':
                    con.targets.clear()
                    arm_con = con
                    break
            if not arm_con:
                arm_con = obj.new(type='ARMATURE')

                target = arm_con.targets.new()
                target.target = rig
                target.subtarget = active_bone.name

        # Draw a nice info message.
        objs_str = (
            obj.name if len(objs_to_parent) == 1 else f"{len(objs_to_parent)} objects"
        )
        self.report({'INFO'}, f"Constrained {objs_str} to {active_bone.name}")
        return {'FINISHED'}

    def parent_with_child_of_con(self, context):
        """Parent selected bones to the active object/bone using Child Of constraints."""
        parent_ob = context.active_object
        objs_to_parent = [obj for obj in context.selected_objects if obj != parent_ob]

        for obj in objs_to_parent:
            if obj.parent:
                self.report(
                    {'WARNING'},
                    f"Warning: A Child Of Constraint was added to {obj.name}, which already has a parent. This results in double-parenting. Existing parent should be removed!",
                )
            for con in obj.constraints:
                if con.type == 'CHILD_OF':
                    self.report(
                        {'WARNING'},
                        f"Warning: A Child Of Constraint was added to {obj.name}, which already had a Child Of constraint. This results in double-parenting. Existing constraint should be removed!",
                    )

            childof = obj.constraints.new(type='CHILD_OF')
            childof.target = parent_ob
            if context.active_pose_bone:
                childof.subtarget = context.active_pose_bone.name
                childof.inverse_matrix = (
                    parent_ob.matrix_world @ context.active_pose_bone.matrix
                ).inverted()
            else:
                childof.inverse_matrix = parent_ob.matrix_world.inverted()

        # Draw a nice info message.
        objs_str = (
            obj.name if len(objs_to_parent) == 1 else f"{len(objs_to_parent)} objects"
        )
        parent_str = (
            context.active_pose_bone.name
            if context.active_pose_bone
            else parent_ob.name
        )
        self.report({'INFO'}, f"Constrained {objs_str} to {parent_str}")
        return {'FINISHED'}

    def parent_with_copy_transforms_con(self, context):
        """Parent selected bones to the active object/bone using Copy Transforms constraints."""
        parent_ob = context.active_object
        objs_to_parent = [obj for obj in context.selected_objects if obj != parent_ob]

        for obj in objs_to_parent:
            copytrans = obj.constraints.new(type='COPY_TRANSFORMS')
            copytrans.target = parent_ob
            if context.active_pose_bone:
                copytrans.subtarget = context.active_pose_bone.name

        # Draw a nice info message.
        objs_str = (
            obj.name if len(objs_to_parent) == 1 else f"{len(objs_to_parent)} objects"
        )
        parent_str = (
            context.active_pose_bone.name
            if context.active_pose_bone
            else parent_ob.name
        )
        self.report({'INFO'}, f"Constrained {objs_str} to {parent_str}")
        return {'FINISHED'}


def set_parent_poll_check_linked(cls, context):
    if any([ob.library for ob in context.selected_objects]):
        cls.poll_message_set(
            "An object is linked. You need to override it to change the parenting."
        )
        return False
    if any([ob.override_library and ob.override_library.is_system_override for ob in context.selected_objects]):
        cls.poll_message_set(
            "An object is overridden but not editable. You need to make it an editable override to change the parenting."
        )
        return False
    return True

### Header Menu UI
def draw_new_header_menu(self, context):
    layout = self.layout

    # Set Parent
    layout.operator(OBJECT_OT_parent_set_simple.bl_idname, icon='CON_CHILDOF')

    # Set Parent (Advanced)
    layout.operator(OBJECT_OT_parent_set_advanced.bl_idname, icon='CON_CHILDOF')

    layout.separator()
    # <
    # Clear Parent (Keep Transform)
    layout.operator(
        OBJECT_OT_clear_parent.bl_idname,
        text="Clear Parent",
        icon='X',
    ).keep_transform = True

    # Clear Parent (Without Correction)
    layout.operator(
        OBJECT_OT_clear_parent.bl_idname,
        text="Clear Parent (Without Correction)",
        icon='UNLINKED',
    ).keep_transform = False

    # Clear Offset Correction (aka Clear Inverse Matrix)
    layout.operator(
        OBJECT_OT_clear_parent_inverse_matrix.bl_idname,
        text="Clear Offset Correction",
        icon='DRIVER_DISTANCE',
    )


registry = [
    OBJECT_MT_parenting_pie,
    OBJECT_OT_clear_parent,
    OBJECT_OT_clear_parent_inverse_matrix,
    OBJECT_OT_parent_set_simple,
    OBJECT_OT_parent_set_advanced,
]


def register():
    WM_OT_call_menu_pie_drag_only.register_drag_hotkey(
        keymap_name="Object Mode",
        pie_name=OBJECT_MT_parenting_pie.bl_idname,
        hotkey_kwargs={'type': "P", 'value': "PRESS"},
        on_drag=False,
    )

    bpy.types.VIEW3D_MT_object_parent.draw_old = bpy.types.VIEW3D_MT_object_parent.draw
    bpy.types.VIEW3D_MT_object_parent.draw = draw_new_header_menu


def unregister():
    bpy.types.VIEW3D_MT_object_parent.draw = bpy.types.VIEW3D_MT_object_parent.draw_old
