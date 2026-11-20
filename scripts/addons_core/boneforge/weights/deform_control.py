"""BoneCraft Deform vs Control Rig Management — Tag, manage, and export deform bones."""
import bpy
from bpy.types import Panel, Operator, UIList, PropertyGroup
from bpy.props import BoolProperty, StringProperty, EnumProperty, CollectionProperty, IntProperty
from boneforge.i18n import T

# ============================================================================
# Remapping Templates
# ============================================================================

REMAP_TEMPLATES = {
    'rigify': {
        'name': 'Rigify',
        'description': 'Rigify DEF- prefix convention',
        'rules': [
            ('DEF-', True),  # DEF- prefix = deform
        ]
    },
    'ue5': {
        'name': 'UE5 Mannequin',
        'description': 'UE5 Mannequin naming (ik_ = control, others = deform)',
        'rules': [
            ('ik_', False),  # ik_ prefix = control
            ('hand_', False),  # hand_ = control
            ('foot_', False),  # foot_ = control
        ],
        'default_deform': True,  # Everything else is deform
    },
    'unity': {
        'name': 'Unity Humanoid',
        'description': 'Unity Humanoid standard naming',
        'rules': [
            ('Armature|', True),  # Root deform
            ('Hips', True),
            ('Spine', True),
            ('Chest', True),
            ('Neck', True),
            ('Head', True),
            ('LeftShoulder', True),
            ('RightShoulder', True),
            ('LeftUpperArm', True),
            ('RightUpperArm', True),
            ('LeftLowerArm', True),
            ('RightLowerArm', True),
            ('LeftHand', True),
            ('RightHand', True),
            ('LeftUpperLeg', True),
            ('RightUpperLeg', True),
            ('LeftLowerLeg', True),
            ('RightLowerLeg', True),
            ('LeftFoot', True),
            ('RightFoot', True),
        ]
    },
}

# ============================================================================
# Validation Helpers
# ============================================================================

def is_valid_bone_name(name):
    """Check if bone name follows conventions: no spaces, no special chars, under 63 chars."""
    if not name or len(name) >= 63:
        return False
    # Allow alphanumeric, hyphens, underscores, and dots
    import re
    return bool(re.match(r'^[a-zA-Z0-9_.\-]+$', name)) and ' ' not in name

# ============================================================================
# Operators
# ============================================================================

class BF_OT_TagDeformBones(Operator):
    """Auto-tag deform bones based on naming convention (DEF- prefix)."""
    bl_idname = "boneforge.tag_deform_bones"
    bl_label = "Tag Deform Bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' and
                context.active_object and
                context.active_object.type == 'ARMATURE')

    def execute(self, context):
        armature = context.active_object.data
        deform_count = 0
        control_count = 0

        for bone in armature.bones:
            # Check for DEF- prefix
            is_deform = bone.name.startswith('DEF-')
            bone['boneforge_deform_layer'] = is_deform

            if is_deform:
                deform_count += 1
            else:
                control_count += 1

        self.report({'INFO'}, f"Tagged {deform_count} deform, {control_count} control bones")
        return {'FINISHED'}

class BF_OT_RemapDeformNames(Operator):
    """Remap deform tags and rename bones using preset templates."""
    bl_idname = "boneforge.remap_deform_names"
    bl_label = "Remap Deform Names"
    bl_options = {'REGISTER', 'UNDO'}

    template: EnumProperty(description='Naming scheme to rename the deform bones to',
        name="Template",
        items=[
            ('rigify', 'Rigify', 'DEF- prefix'),
            ('ue5', 'UE5 Mannequin', 'UE5 naming convention'),
            ('unity', 'Unity Humanoid', 'Unity standard'),
        ],
        default='rigify'
    )

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' and
                context.active_object and
                context.active_object.type == 'ARMATURE')

    def execute(self, context):
        armature_obj = context.active_object
        armature = armature_obj.data
        template = REMAP_TEMPLATES.get(self.template)

        if not template:
            self.report({'ERROR'}, f"Template {self.template} not found")
            return {'CANCELLED'}

        deform_count = 0
        control_count = 0

        # Enter edit mode to rename bones
        bpy.ops.object.mode_set(mode='EDIT')

        try:
            armature = context.active_object.data

            for bone in armature.edit_bones:
                is_deform = False

                # Apply rules
                for rule in template.get('rules', []):
                    if isinstance(rule, tuple) and len(rule) == 2:
                        pattern, is_def = rule
                        if pattern in bone.name:
                            is_deform = is_def
                            break

                # Apply default if no rules matched
                if 'default_deform' in template and not any(
                    pattern in bone.name for pattern, _ in template.get('rules', [])
                ):
                    is_deform = template['default_deform']

                # Rename based on template
                old_name = bone.name
                new_name = old_name

                if self.template == 'rigify' and is_deform and not old_name.startswith('DEF-'):
                    new_name = 'DEF-' + old_name
                elif self.template == 'ue5' and is_deform:
                    # For UE5: remove ik_, hand_, foot_ prefixes from deform bones
                    for prefix in ['ik_', 'hand_', 'foot_']:
                        if old_name.startswith(prefix):
                            new_name = old_name[len(prefix):]
                            break
                elif self.template == 'unity':
                    # Unity uses specific bone names; only tag, don't rename
                    pass

                bone.name = new_name

                if is_deform:
                    deform_count += 1
                else:
                    control_count += 1

            # Return to pose mode and tag bones
            bpy.ops.object.mode_set(mode='POSE')
            armature = context.active_object.data

            for bone in armature.bones:
                is_deform = False

                # Reapply rules to tag properly
                for rule in template.get('rules', []):
                    if isinstance(rule, tuple) and len(rule) == 2:
                        pattern, is_def = rule
                        if pattern in bone.name:
                            is_deform = is_def
                            break

                if 'default_deform' in template and not any(
                    pattern in bone.name for pattern, _ in template.get('rules', [])
                ):
                    is_deform = template['default_deform']

                bone['boneforge_deform_layer'] = is_deform

        except Exception as e:
            self.report({'ERROR'}, f"Remap failed: {str(e)}")
            bpy.ops.object.mode_set(mode='POSE')
            return {'CANCELLED'}

        self.report({'INFO'}, f"Remapped: {deform_count} deform, {control_count} control bones")
        return {'FINISHED'}

class BF_OT_ExportDeformOnly(Operator):
    """Export deform-tagged bones only via FBX."""
    bl_idname = "boneforge.export_deform_only"
    bl_label = "Export Deform Bones (FBX)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        description="FBX file path",
        subtype='FILE_PATH'
    )

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' and
                context.active_object and
                context.active_object.type == 'ARMATURE')

    def execute(self, context):
        armature = context.active_object.data

        # Check if any deform bones exist
        deform_bones = [
            b for b in armature.bones
            if b.get('boneforge_deform_layer', False)
        ]

        if not deform_bones:
            self.report({'WARNING'}, "No deform bones to export")
            return {'CANCELLED'}

        # Hide all non-deform bones
        for bone in armature.bones:
            is_deform = bone.get('boneforge_deform_layer', False)
            bone.hide = not is_deform

        try:
            # Export using bpy.ops with corrected FBX parameters
            bpy.ops.export_scene.fbx(
                filepath=self.filepath,
                use_selection=True,
                use_armature=True,
                object_types={'ARMATURE', 'MESH'},
                use_armature_deform_only=True,
                add_leaf_bones=False,
            )
            self.report({'INFO'}, f"Exported {len(deform_bones)} deform bones to {self.filepath}")
            result = {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            result = {'CANCELLED'}
        finally:
            # Restore visibility
            for bone in armature.bones:
                bone.hide = False

        return result

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# ============================================================================
# Property Groups
# ============================================================================

class BONEFORGE_BoneListItem(PropertyGroup):
    """Bone list item for UIList."""
    name: StringProperty(name="Bone Name")
    is_deform: BoolProperty(name="Is Deform", default=False)
    display_name: StringProperty(name="Display Name")

# ============================================================================
# UI Lists
# ============================================================================

class BONEFORGE_UL_DeformBones(UIList):
    """List of deform bones."""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """Render one deform-bone row with a validity icon, bone name, and DEF toggle."""
        row = layout.row(align=True)

        # Validation indicator
        icon_status = 'CHECKMARK' if is_valid_bone_name(item.name) else 'ERROR'
        row.label(text="", icon=icon_status)

        row.label(text=item.name, icon='BONE_DATA')
        row.prop(item, 'is_deform', text="DEF", toggle=True)

class BONEFORGE_UL_ControlBones(UIList):
    """List of control bones."""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """Render one control-bone row with a validity icon, bone name, and CTL toggle."""
        row = layout.row(align=True)

        # Validation indicator
        icon_status = 'CHECKMARK' if is_valid_bone_name(item.name) else 'ERROR'
        row.label(text="", icon=icon_status)

        row.label(text=item.name, icon='BONE_DATA')
        row.prop(item, 'is_deform', text="CTL", toggle=True)

# ============================================================================
# Panels
# ============================================================================

class BONEFORGE_PT_p2b_deform_control(Panel):
    """Deform vs Control rig management panel."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2b_deform_control"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"

    def draw_header(self, context):
        self.layout.label(text=T("Deform vs Control"))

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' and
                context.active_object and
                context.active_object.type == 'ARMATURE')

    def draw(self, context):
        layout = self.layout
        armature = context.active_object.data

        # Tag and remap buttons
        row = layout.row(align=True)
        row.operator("boneforge.tag_deform_bones", icon='TAG')
        row.operator("boneforge.remap_deform_names", icon='SETTINGS')

        layout.separator()

        deform_bones, control_bones = self._split_bones(armature)

        layout.label(
            text=f"Deform Bones ({len(deform_bones)}):",
        )
        self._draw_bone_section(
            layout,
            bones=deform_bones,
            empty_text=T("No deform bones tagged yet"),
            tag_text=T("DEF"),
        )

        layout.separator()

        layout.label(
            text=f"Control Bones ({len(control_bones)}):",
        )
        self._draw_bone_section(
            layout,
            bones=control_bones,
            empty_text=T("No control bones detected"),
            tag_text=T("CTL"),
        )

        layout.separator()

        # Export button
        layout.operator("boneforge.export_deform_only", icon='EXPORT')

    def _split_bones(self, armature):
        """Split bones into deform and control groups without mutating Blender data.

        v3.7.2: previous version checked only the BoneCraft custom property
        ``boneforge_deform_layer``. On a freshly Rigify-generated rig the
        property is unset on every bone, so the panel reported every bone
        (including the DEF- prefixed deform bones with ``use_deform=True``)
        as a control bone. Now we use the explicit tag when ANY bone has
        been tagged (so the user's intent wins), and otherwise fall back
        to a heuristic: ``bone.use_deform`` or a ``DEF-`` name prefix —
        which matches Rigify's convention.
        """
        has_explicit_tag = any(
            bone.get('boneforge_deform_layer', False)
            for bone in armature.bones
        )
        deform_bones = []
        control_bones = []
        for bone in armature.bones:
            if has_explicit_tag:
                is_deform = bool(bone.get('boneforge_deform_layer', False))
            else:
                is_deform = bool(getattr(bone, 'use_deform', False)) or \
                            bone.name.startswith('DEF-')
            if is_deform:
                deform_bones.append(bone)
            else:
                control_bones.append(bone)
        return deform_bones, control_bones

    def _draw_bone_section(self, layout, bones, empty_text, tag_text):
        """Draw a read-only bone list that is safe inside Blender 5.1 panel draw."""
        box = layout.box()
        column = box.column(align=True)

        if not bones:
            column.label(text=empty_text, icon='INFO')
            return

        for bone in bones:
            row = column.row(align=True)
            icon_status = 'CHECKMARK' if is_valid_bone_name(bone.name) else 'ERROR'
            row.label(text="", icon=icon_status)
            row.label(text=bone.name, icon='BONE_DATA')
            row.label(text=tag_text)

# ============================================================================
# Registration
# ============================================================================

_classes = [
    BONEFORGE_BoneListItem,
    BF_OT_TagDeformBones,
    BF_OT_RemapDeformNames,
    BF_OT_ExportDeformOnly,
    BONEFORGE_UL_DeformBones,
    BONEFORGE_UL_ControlBones,
    BONEFORGE_PT_p2b_deform_control,
]

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except (RuntimeError, ValueError):
            pass
