"""BoneCraft Phase 2C — Space Switching System.

Allows bones to switch between multiple parent spaces (World, Origin, other bones)
with keyframeable transitions. All constraints are standard Blender Child Of constraints
that work without BoneCraft installed.
"""
import json
import bpy
from boneforge.i18n import T


# ============================================================================
# OPERATORS
# ============================================================================

class BF_OT_AddSpace(bpy.types.Operator):
    """Add a new space for the active bone."""
    bl_idname = "boneforge.add_space"
    bl_label = "Add Space"
    bl_options = {'REGISTER', 'UNDO'}

    space_name: bpy.props.StringProperty(
        name="Space Name",
        description="Name of the new space",
        default="Space"
    )
    target_type: bpy.props.EnumProperty(
        name="Target Type",
        description="Type of space target",
        items=[
            ('WORLD', "World", "World space"),
            ('ORIGIN', "Origin", "Armature origin"),
            ('BONE', "Bone", "Another bone"),
        ],
        default='WORLD'
    )
    target_bone: bpy.props.StringProperty(
        name="Target Bone",
        description="Name of target bone (if Target Type is BONE)",
        default=""
    )
    blend_weight: bpy.props.FloatProperty(
        name="Blend Weight",
        description="Default blend weight (0.0-1.0)",
        min=0.0,
        max=1.0,
        default=1.0
    )

    @classmethod
    def poll(cls, context):
        return (context.active_object and
                context.active_object.type == 'ARMATURE' and
                context.mode == 'POSE' and
                context.active_pose_bone is not None)

    def execute(self, context):
        armature = context.active_object
        pbone = context.active_pose_bone

        # Load existing spaces
        spaces = _load_spaces(pbone)

        # Check for duplicate names
        if any(s['name'] == self.space_name for s in spaces):
            self.report({'ERROR'}, f"Space '{self.space_name}' already exists")
            return {'CANCELLED'}

        # Validate target_bone if needed
        if self.target_type == 'BONE' and not self.target_bone:
            self.report({'ERROR'}, "Target bone is required for BONE target type")
            return {'CANCELLED'}

        if self.target_type == 'BONE' and self.target_bone not in armature.pose.bones:
            self.report({'ERROR'}, f"Target bone '{self.target_bone}' not found")
            return {'CANCELLED'}

        # Add new space
        new_space = {
            'name': self.space_name,
            'target_type': self.target_type,
            'target_bone': self.target_bone if self.target_type == 'BONE' else '',
            'blend_weight': self.blend_weight
        }
        spaces.append(new_space)

        # Save spaces
        _save_spaces(pbone, spaces)

        # Create Child Of constraint
        _create_space_constraint(pbone, new_space, armature)

        self.report({'INFO'}, f"Added space '{self.space_name}'")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class BF_OT_RemoveSpace(bpy.types.Operator):
    """Remove a space from the active bone."""
    bl_idname = "boneforge.remove_space"
    bl_label = "Remove Space"
    bl_options = {'REGISTER', 'UNDO'}

    space_name: bpy.props.StringProperty(
        name="Space Name",
        description="Name of space to remove",
        default=""
    )

    @classmethod
    def poll(cls, context):
        return (context.active_object and
                context.active_object.type == 'ARMATURE' and
                context.mode == 'POSE' and
                context.active_pose_bone is not None)

    def execute(self, context):
        armature = context.active_object
        pbone = context.active_pose_bone

        spaces = _load_spaces(pbone)

        # Find and remove space
        space_idx = None
        for i, s in enumerate(spaces):
            if s['name'] == self.space_name:
                space_idx = i
                break

        if space_idx is None:
            self.report({'ERROR'}, f"Space '{self.space_name}' not found")
            return {'CANCELLED'}

        space = spaces.pop(space_idx)
        _save_spaces(pbone, spaces)

        # Remove constraint
        constraint_name = _get_constraint_name(space['name'])
        if constraint_name in pbone.constraints:
            pbone.constraints.remove(pbone.constraints[constraint_name])

        # Remove custom property if it was active
        prop_name = f"boneforge_p2c_space_{pbone.name}_active"
        if prop_name in armature.data:
            del armature.data[prop_name]

        self.report({'INFO'}, f"Removed space '{self.space_name}'")
        return {'FINISHED'}


class BF_OT_SetDefaultSpace(bpy.types.Operator):
    """Set a space as the default (active) space."""
    bl_idname = "boneforge.set_default_space"
    bl_label = "Set Default Space"
    bl_options = {'REGISTER', 'UNDO'}

    space_name: bpy.props.StringProperty(
        name="Space Name",
        description="Name of space to set as default",
        default=""
    )

    @classmethod
    def poll(cls, context):
        return (context.active_object and
                context.active_object.type == 'ARMATURE' and
                context.mode == 'POSE' and
                context.active_pose_bone is not None)

    def execute(self, context):
        armature = context.active_object
        pbone = context.active_pose_bone

        spaces = _load_spaces(pbone)

        # Find space
        if not any(s['name'] == self.space_name for s in spaces):
            self.report({'ERROR'}, f"Space '{self.space_name}' not found")
            return {'CANCELLED'}

        # Store active space name
        prop_name = f"boneforge_p2c_space_{pbone.name}_active"
        armature.data[prop_name] = self.space_name

        # Update all constraint influences
        _update_space_influences(pbone, spaces)

        self.report({'INFO'}, f"Set default space to '{self.space_name}'")
        return {'FINISHED'}


class BF_OT_SwitchSpace(bpy.types.Operator):
    """Switch space with keyframing for smooth transition."""
    bl_idname = "boneforge.switch_space"
    bl_label = "Switch Space (Keyframed)"
    bl_options = {'REGISTER', 'UNDO'}

    space_name: bpy.props.StringProperty(
        name="Space Name",
        description="Name of space to switch to",
        default=""
    )

    @classmethod
    def poll(cls, context):
        return (context.active_object and
                context.active_object.type == 'ARMATURE' and
                context.mode == 'POSE' and
                context.active_pose_bone is not None)

    def execute(self, context):
        scene = context.scene
        armature = context.active_object
        pbone = context.active_pose_bone
        frame_current = scene.frame_current

        spaces = _load_spaces(pbone)

        # Find space
        if not any(s['name'] == self.space_name for s in spaces):
            self.report({'ERROR'}, f"Space '{self.space_name}' not found")
            return {'CANCELLED'}

        # Store world position before switching
        world_matrix = armature.matrix_world @ pbone.matrix

        # Insert keyframe at current frame with old active space (influence 1.0)
        prop_name = f"boneforge_p2c_space_{pbone.name}_active"
        current_space = armature.data.get(prop_name, spaces[0]['name'] if spaces else '')

        for space in spaces:
            constraint_name = _get_constraint_name(space['name'])
            if constraint_name in pbone.constraints:
                constraint = pbone.constraints[constraint_name]
                constraint.influence = 1.0 if space['name'] == current_space else 0.0
                constraint.keyframe_insert('influence', frame=frame_current)

        # Switch to new space
        armature.data[prop_name] = self.space_name

        # Move bone back to world position
        _set_bone_world_position(pbone, world_matrix, armature)

        # Insert keyframe at next frame with new space influences
        for space in spaces:
            constraint_name = _get_constraint_name(space['name'])
            if constraint_name in pbone.constraints:
                constraint = pbone.constraints[constraint_name]
                constraint.influence = 1.0 if space['name'] == self.space_name else 0.0
                constraint.keyframe_insert('influence', frame=frame_current + 1)

        # Keyframe location/rotation to maintain position
        pbone.keyframe_insert('location', frame=frame_current)
        pbone.keyframe_insert('location', frame=frame_current + 1)
        pbone.keyframe_insert('rotation_quaternion', frame=frame_current)
        pbone.keyframe_insert('rotation_quaternion', frame=frame_current + 1)

        self.report({'INFO'}, f"Switched to space '{self.space_name}'")
        return {'FINISHED'}


class BF_OT_SwitchSpaceOnly(bpy.types.Operator):
    """Switch space without keyframing."""
    bl_idname = "boneforge.switch_space_only"
    bl_label = "Switch Space"
    bl_options = {'REGISTER', 'UNDO'}

    space_name: bpy.props.StringProperty(
        name="Space Name",
        description="Name of space to switch to",
        default=""
    )

    @classmethod
    def poll(cls, context):
        return (context.active_object and
                context.active_object.type == 'ARMATURE' and
                context.mode == 'POSE' and
                context.active_pose_bone is not None)

    def execute(self, context):
        armature = context.active_object
        pbone = context.active_pose_bone

        spaces = _load_spaces(pbone)

        # Find space
        if not any(s['name'] == self.space_name for s in spaces):
            self.report({'ERROR'}, f"Space '{self.space_name}' not found")
            return {'CANCELLED'}

        # Store world position
        world_matrix = armature.matrix_world @ pbone.matrix

        # Switch space
        prop_name = f"boneforge_p2c_space_{pbone.name}_active"
        armature.data[prop_name] = self.space_name

        # Update constraint influences
        _update_space_influences(pbone, spaces)

        # Move bone back to world position
        _set_bone_world_position(pbone, world_matrix, armature)

        self.report({'INFO'}, f"Switched to space '{self.space_name}'")
        return {'FINISHED'}


# ============================================================================
# PANELS
# ============================================================================

class BONEFORGE_PT_p2c_space_switch(bpy.types.Panel):
    """Space switch setup and animator controls — merged panel."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2c_space_switch"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"

    def draw_header(self, context):
        self.layout.label(text=T("Space Switch"))

    @classmethod
    def poll(cls, context):
        return (context.active_object and
                context.active_object.type == 'ARMATURE' and
                context.mode == 'POSE' and
                context.active_pose_bone is not None)

    def draw(self, context):
        layout = self.layout
        pbone = context.active_pose_bone
        armature = context.active_object

        spaces = _load_spaces(pbone)
        prop_name = f"boneforge_p2c_space_{pbone.name}_active"
        active_space = armature.data.get(prop_name, spaces[0]['name'] if spaces else '')

        if not spaces:
            layout.label(text=T("No spaces defined"), icon='INFO')
            layout.operator("boneforge.add_space", text=T("Add Space"))
            return

        # Switch buttons — active space depressed, others flat
        col = layout.column(align=True)
        col.scale_y = 1.2
        for space in spaces:
            if space['name'] == active_space:
                op = col.operator("boneforge.switch_space",
                                  text=f"● {space['name']}", depress=True)
            else:
                op = col.operator("boneforge.switch_space_only",
                                  text=space['name'])
            op.space_name = space['name']

        layout.separator(factor=0.5)

        # Management — add / remove per space
        layout.label(text=T("Manage Spaces:"))
        for space in spaces:
            row = layout.row(align=True)
            row.label(text=space['name'])
            props = row.operator("boneforge.remove_space", text="", icon='X')
            props.space_name = space['name']

        layout.operator("boneforge.add_space", text=T("Add Space"), icon='ADD')


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _load_spaces(pbone):
    """Load spaces from custom property."""
    prop_name = 'boneforge_p2c_spaces'
    if prop_name in pbone:
        try:
            spaces_data = json.loads(pbone[prop_name])
            return spaces_data
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def _save_spaces(pbone, spaces):
    """Save spaces to custom property."""
    pbone['boneforge_p2c_spaces'] = json.dumps(spaces)


def _get_constraint_name(space_name):
    """Get constraint name for a space."""
    return f"BF_Space_{space_name}"


def _create_space_constraint(pbone, space, armature):
    """Create Child Of constraint for a space."""
    constraint_name = _get_constraint_name(space['name'])

    # Remove if exists
    if constraint_name in pbone.constraints:
        pbone.constraints.remove(pbone.constraints[constraint_name])

    # Create new constraint
    constraint = pbone.constraints.new('CHILD_OF')
    constraint.name = constraint_name
    constraint.influence = 0.0  # Start inactive

    # Set target
    if space['target_type'] == 'WORLD':
        # No target for world space
        constraint.target = None
    elif space['target_type'] == 'ORIGIN':
        # Target armature itself
        constraint.target = armature
        constraint.subtarget = ''
    elif space['target_type'] == 'BONE':
        # Target specific bone
        constraint.target = armature
        constraint.subtarget = space['target_bone']


def _update_space_influences(pbone, spaces):
    """Update constraint influences based on active space."""
    armature = pbone.id_data
    prop_name = f"boneforge_p2c_space_{pbone.name}_active"
    active_space = armature.get(prop_name, spaces[0]['name'] if spaces else '')

    for space in spaces:
        constraint_name = _get_constraint_name(space['name'])
        if constraint_name in pbone.constraints:
            constraint = pbone.constraints[constraint_name]
            constraint.influence = 1.0 if space['name'] == active_space else 0.0


def _set_bone_world_position(pbone, world_matrix, armature):
    """Set bone's local matrix to match world position."""
    armature_inv = armature.matrix_world.inverted()
    pbone.matrix = armature_inv @ world_matrix


# ============================================================================
# REGISTRATION
# ============================================================================

classes = (
    BF_OT_AddSpace,
    BF_OT_RemoveSpace,
    BF_OT_SetDefaultSpace,
    BF_OT_SwitchSpace,
    BF_OT_SwitchSpaceOnly,
    BONEFORGE_PT_p2c_space_switch,
)


def register():
    """Register space switch operators and panels."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister space switch operators and panels."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
