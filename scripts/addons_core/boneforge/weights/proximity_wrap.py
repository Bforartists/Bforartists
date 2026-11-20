"""BoneCraft Phase 2B — Proximity Wrap.

Binds a target mesh to a driver mesh using Surface Deform,
allowing clothing and accessories to follow body deformation.
Category: Deform Management.
"""

import bpy
import json
from bpy.props import (
    PointerProperty, EnumProperty, FloatProperty
)
from boneforge.i18n import T
from bpy.types import PropertyGroup, Operator, Panel


FALLOFF_TYPE_ENUM = [
    ('NEAREST_POINT', "Nearest Point", "Use nearest point on surface"),
    ('NEAREST_FACE', "Nearest Face", "Use nearest face on surface"),
    ('RAY_CAST', "Ray Cast", "Cast ray to surface"),
]


class BF_ProximityWrapSettings(PropertyGroup):
    """Proximity Wrap parameters."""
    driver_mesh: PointerProperty(
        name="Driver Mesh",
        description="Mesh to drive deformation",
        type=bpy.types.Object
    )
    falloff_type: EnumProperty(
        name="Falloff Type",
        items=FALLOFF_TYPE_ENUM,
        default='NEAREST_POINT'
    )
    max_distance: FloatProperty(
        name="Max Distance",
        description="Maximum influence distance",
        min=0.0, max=1000.0, default=10.0
    )


class BF_OT_BindProximityWrap(Operator):
    """Bind Proximity Wrap modifier to driver mesh."""
    bl_idname = "boneforge.bind_proximity_wrap"
    bl_label = "Bind Proximity Wrap"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and
                context.object and
                context.object.type == 'MESH')

    def execute(self, context):
        target_mesh = context.object
        settings = target_mesh.boneforge_proximity_wrap

        if not settings.driver_mesh:
            self.report({'ERROR'}, "No driver mesh selected")
            return {'CANCELLED'}

        if settings.driver_mesh.type != 'MESH':
            self.report({'ERROR'}, "Driver must be a mesh object")
            return {'CANCELLED'}

        # Surface Deform cannot bind a mesh to itself
        if settings.driver_mesh == target_mesh:
            self.report(
                {'ERROR'},
                "Driver mesh must be a different object than the target mesh",
            )
            return {'CANCELLED'}

        # Check if modifier already exists
        if "ProximityWrap" in target_mesh.modifiers:
            self.report({'WARNING'}, "Proximity Wrap already applied")
            return {'FINISHED'}

        # Verify armature (if any) is in rest pose
        if settings.driver_mesh.parent and settings.driver_mesh.parent.type == 'ARMATURE':
            armature = settings.driver_mesh.parent
            # Check all pose bones have identity transforms
            for pose_bone in armature.pose.bones:
                matrix = pose_bone.matrix_basis
                # Check if close to identity (with small tolerance for floating point)
                tolerance = 0.0001
                for i in range(4):
                    for j in range(4):
                        if i == j:
                            if abs(matrix[i][j] - 1.0) > tolerance:
                                self.report({'ERROR'}, f"Bone {pose_bone.name} is not in rest pose")
                                return {'CANCELLED'}
                        else:
                            if abs(matrix[i][j]) > tolerance:
                                self.report({'ERROR'}, f"Bone {pose_bone.name} is not in rest pose")
                                return {'CANCELLED'}

        # Add Surface Deform modifier
        mod = target_mesh.modifiers.new(name="ProximityWrap", type='SURFACE_DEFORM')

        # Configure modifier
        mod.target = settings.driver_mesh

        # Bind the modifier
        with context.temp_override(object=target_mesh):
            bpy.ops.object.surfacedeform_bind(modifier="ProximityWrap")

        # Store settings as custom property
        config = {
            "driver_mesh": settings.driver_mesh.name,
            "falloff_type": settings.falloff_type,
            "max_distance": settings.max_distance
        }
        target_mesh["boneforge_p2b_proxwrap"] = json.dumps(config)

        self.report({'INFO'}, f"Bound Proximity Wrap to {settings.driver_mesh.name}")
        return {'FINISHED'}


class BF_OT_UnbindProximityWrap(Operator):
    """Unbind Proximity Wrap modifier."""
    bl_idname = "boneforge.unbind_proximity_wrap"
    bl_label = "Unbind Proximity Wrap"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and
                context.object and
                context.object.type == 'MESH' and
                "ProximityWrap" in context.object.modifiers)

    def execute(self, context):
        mesh_obj = context.object
        mod = mesh_obj.modifiers["ProximityWrap"]

        # Reset bind state
        mod.show_viewport = False
        mod.show_render = False

        self.report({'INFO'}, "Unbound Proximity Wrap")
        return {'FINISHED'}


class BF_OT_RebindProximityWrap(Operator):
    """Rebind Proximity Wrap modifier to update binding."""
    bl_idname = "boneforge.rebind_proximity_wrap"
    bl_label = "Rebind Proximity Wrap"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and
                context.object and
                context.object.type == 'MESH' and
                "ProximityWrap" in context.object.modifiers)

    def execute(self, context):
        target_mesh = context.object

        if "ProximityWrap" not in target_mesh.modifiers:
            self.report({'ERROR'}, "No Proximity Wrap modifier found")
            return {'CANCELLED'}

        # Rebind the modifier
        try:
            with context.temp_override(object=target_mesh):
                bpy.ops.object.surfacedeform_bind(modifier="ProximityWrap")
            self.report({'INFO'}, "Rebound Proximity Wrap")
            return {'FINISHED'}
        except RuntimeError as e:
            self.report({'ERROR'}, f"Rebind failed: {str(e)}")
            return {'CANCELLED'}


class BONEFORGE_PT_p2b_proximity_wrap(Panel):
    """Proximity Wrap panel in Object mode."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2b_proximity_wrap"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_parent_id = "BF_PT_sb_skin"
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Proximity Wrap"))

    @classmethod
    def poll(cls, context):
        # Show, don't hide: when the requirement fails, draw() says what to select.
        return True

    def draw(self, context):
        if not (context.mode == 'OBJECT' and context.object is not None and context.object.type == 'MESH'):
            from boneforge.core import needs
            needs.draw(self.layout, context, 'Proximity Wrap needs a mesh selected, in Object Mode.', ('MESH',))
            return
        layout = self.layout
        mesh_obj = context.object
        settings = mesh_obj.boneforge_proximity_wrap

        has_proximity_wrap = "ProximityWrap" in mesh_obj.modifiers

        if has_proximity_wrap:
            layout.label(text=T("Proximity Wrap Active"), icon='CHECKMARK')

            mod = mesh_obj.modifiers["ProximityWrap"]
            if mod.target:
                layout.label(text=f"Driver: {mod.target.name}")

            row = layout.row(align=True)
            row.operator("boneforge.rebind_proximity_wrap", text=T("Rebind"), icon='PINNED')
            row.operator("boneforge.unbind_proximity_wrap", text=T("Unbind"), icon='X')

        else:
            layout.label(text=T("Configure and bind"), icon='INFO')

            layout.prop(settings, "driver_mesh")            # what it binds to: picked first
            layout.operator("boneforge.bind_proximity_wrap", icon='MOD_MESHDEFORM')
            from boneforge.core.helpers import draw_helper, options_fold
            col = options_fold(layout, "bc_proximity_wrap_options")
            if col is not None:
                col.prop(settings, "falloff_type")
                col.prop(settings, "max_distance")


def register():
    """Register Proximity Wrap classes and properties."""
    bpy.utils.register_class(BF_ProximityWrapSettings)
    bpy.utils.register_class(BF_OT_BindProximityWrap)
    bpy.utils.register_class(BF_OT_UnbindProximityWrap)
    bpy.utils.register_class(BF_OT_RebindProximityWrap)
    bpy.utils.register_class(BONEFORGE_PT_p2b_proximity_wrap)

    bpy.types.Object.boneforge_proximity_wrap = PointerProperty(
        type=BF_ProximityWrapSettings,
        name="Proximity Wrap"
    )


def unregister():
    """Unregister Proximity Wrap classes and properties."""
    if hasattr(bpy.types.Object, 'boneforge_proximity_wrap'):
        del bpy.types.Object.boneforge_proximity_wrap

    bpy.utils.unregister_class(BONEFORGE_PT_p2b_proximity_wrap)
    bpy.utils.unregister_class(BF_OT_RebindProximityWrap)
    bpy.utils.unregister_class(BF_OT_UnbindProximityWrap)
    bpy.utils.unregister_class(BF_OT_BindProximityWrap)
    bpy.utils.unregister_class(BF_ProximityWrapSettings)
