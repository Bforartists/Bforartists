"""BoneCraft Phase 2C — Ribbon System.

Creates NURBS surface strips for smooth twist distribution
along bone chains, used for spines and limb twist correction.
Category: Advanced Rigging.
"""

import bpy
from bpy.props import FloatProperty, EnumProperty
from bpy.types import Panel, Operator
import mathutils
from boneforge.weights.shapes import generate_sphere_wire, create_shape_object
from boneforge.i18n import T


class BONEFORGE_PT_p2c_ribbon(Panel):
    """Ribbon System panel"""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2c_ribbon"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneCraft"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.label(text=T("Ribbon"))

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "POSE"
            and context.active_object is not None
            and context.active_object.type == "ARMATURE"
        )

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        arm = context.active_object

        col = layout.column(align=True)
        col.label(text=T("Chain Configuration"))
        col.label(text=T("(Select first bone in chain)"))

        col = layout.column(align=True)
        if context.active_bone:
            # Count chain length
            root_bone = context.active_bone
            chain_length = 1
            current = root_bone
            while current.children:
                current = current.children[0]
                chain_length += 1
            col.label(text=f"Chain Length: {chain_length}")

        # act first, tune later: control bones and width are adjusted after generating
        layout.operator("boneforge.generate_ribbon", text=T("Generate Ribbon"))
        layout.operator("boneforge.remove_ribbon", text=T("Remove Ribbon"))
        from boneforge.core.helpers import draw_helper
        draw_helper(layout, context, T("Control bones and width: adjust them after generating, "
                                       "in the Adjust Last Operation panel."))


class BF_OT_GenerateRibbon(Operator):
    """Generate NURBS ribbon surface on selected bone chain"""
    bl_idname = "boneforge.generate_ribbon"
    bl_label = "Generate Ribbon"
    bl_options = {"REGISTER", "UNDO"}

    # options: tuned after the click in Adjust Last Operation
    control_count: EnumProperty(
        name="Control Bones",
        description="Number of control bones along the ribbon",
        items=[('2', "2 Bones", ""), ('3', "3 Bones", ""), ('5', "5 Bones", "")],
        default='3',
    )
    width: FloatProperty(
        name="Ribbon Width",
        description="Width of the ribbon surface",
        min=0.01, max=10.0, default=1.0,
    )

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "POSE"
            and context.active_object is not None
            and context.active_object.type == "ARMATURE"
            and context.active_bone is not None
        )

    def execute(self, context):
        arm_obj = context.active_object
        arm = arm_obj.data
        root_bone = context.active_bone

        control_count = int(self.control_count)
        ribbon_width = self.width

        # Collect chain bones
        chain_bones = self._collect_chain(root_bone)
        if len(chain_bones) < 2:
            self.report({"ERROR"}, "Chain must have at least 2 bones")
            return {"FINISHED"}

        # Create NURBS surface
        surface_name = f"{root_bone.name}_Ribbon_Surface"
        surface_data = bpy.data.curves.new(surface_name, "SURFACE")
        surface_data.dimensions = "3D"
        surface_obj = bpy.data.objects.new(surface_name, surface_data)
        context.collection.objects.link(surface_obj)

        # Fit surface to chain
        self._create_ribbon_surface(surface_obj, arm_obj, chain_bones, control_count, ribbon_width)

        # Hide from render
        surface_obj.hide_render = True

        # Create control bones
        control_bones = self._create_ribbon_control_bones(arm_obj, chain_bones, control_count)

        # Add to BoneForge_Rigs collection
        if "BoneForge_Rigs" not in bpy.data.collections:
            rigs_coll = bpy.data.collections.new("BoneForge_Rigs")
            context.collection.children.link(rigs_coll)
        else:
            rigs_coll = bpy.data.collections["BoneForge_Rigs"]

        # Apply deform constraints to chain bones
        self._apply_deform_constraints(arm_obj, chain_bones, surface_obj, control_count)

        self.report({"INFO"}, f"Created Ribbon on {root_bone.name}")
        return {"FINISHED"}

    def _collect_chain(self, root_bone):
        """Collect linear bone chain from root"""
        chain = [root_bone]
        current = root_bone
        while current.children:
            current = current.children[0]
            chain.append(current)
        return chain

    def _create_ribbon_surface(self, surface_obj, arm_obj, chain_bones, control_count, width):
        """Create NURBS surface fitted to bone chain"""
        surface = surface_obj.data

        # Get bone positions
        positions = []
        for bone in chain_bones:
            bone_world = arm_obj.matrix_world @ bone.head
            positions.append(bone_world)

        # Create surface with U along chain, V across width
        surface.resolution_u = len(chain_bones)
        surface.resolution_v = 2

        # Create two edge curves (left and right sides)
        spline_u = surface.splines.new("NURBS")
        spline_u.points.add(len(chain_bones) - 1)
        spline_u.use_endpoint_u = True

        for i, pos in enumerate(positions):
            point = spline_u.points[i]
            point.co = (pos.x, pos.y, pos.z, 1.0)

        # Second edge curve (offset by width)
        spline_u2 = surface.splines.new("NURBS")
        spline_u2.points.add(len(chain_bones) - 1)
        spline_u2.use_endpoint_u = True

        for i, pos in enumerate(positions):
            offset_pos = pos + mathutils.Vector((width, 0, 0))
            point = spline_u2.points[i]
            point.co = (offset_pos.x, offset_pos.y, offset_pos.z, 1.0)

    def _create_ribbon_control_bones(self, arm_obj, chain_bones, control_count):
        """Create control bones at evenly spaced positions"""
        arm = arm_obj.data
        control_bones = []

        # Calculate positions along chain
        chain_length = len(chain_bones) - 1
        step = chain_length / (control_count - 1) if control_count > 1 else 0

        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode="EDIT")

        for i in range(control_count):
            bone_index = min(int(i * step), len(chain_bones) - 1)
            bone = chain_bones[bone_index]

            ctrl_name = f"{chain_bones[0].name}_Ribbon_Ctrl_{i:02d}"
            new_bone = arm.edit_bones.new(ctrl_name)
            new_bone.head = bone.head.copy()
            new_bone.tail = new_bone.head + mathutils.Vector((0, 0, 0.1))

            control_bones.append(new_bone)

        bpy.ops.object.mode_set(mode="OBJECT")

        # Assign sphere wireframe shapes to control bones
        for ctrl_bone in control_bones:
            verts, edges = generate_sphere_wire(radius=0.03, rings=4, segments=6)
            shape_obj = create_shape_object(f"{ctrl_bone.name}_Shape", verts, edges)
            pose_bone = arm_obj.pose.bones[ctrl_bone.name]
            pose_bone.custom_shape = shape_obj

        return control_bones

    def _apply_deform_constraints(self, arm_obj, chain_bones, surface_obj, control_count):
        """Apply Surface Deform or Shrinkwrap constraints to deform bones"""
        arm = arm_obj.data

        # Switch to pose mode
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode="POSE")

        # Apply Surface Deform constraint to chain bones
        for i, bone in enumerate(chain_bones):
            pose_bone = arm_obj.pose.bones[bone.name]
            constraint = pose_bone.constraints.new(type="SURFACE_DEFORM")
            constraint.target = surface_obj
            constraint.deform_mode = "NEAREST_SURFACEPOINT"


class BF_OT_RemoveRibbon(Operator):
    """Remove Ribbon surface and constraints from selected chain"""
    bl_idname = "boneforge.remove_ribbon"
    bl_label = "Remove Ribbon"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "POSE"
            and context.active_object is not None
            and context.active_object.type == "ARMATURE"
            and context.active_bone is not None
        )

    def execute(self, context):
        arm_obj = context.active_object
        arm = arm_obj.data
        root_bone = context.active_bone

        # Collect chain
        chain_bones = self._collect_chain(root_bone)

        # Remove SURFACE_DEFORM constraints
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode="POSE")

        for bone in chain_bones:
            pose_bone = arm_obj.pose.bones[bone.name]
            for constraint in pose_bone.constraints:
                if constraint.type == "SURFACE_DEFORM":
                    pose_bone.constraints.remove(constraint)

        # Clean up ribbon surface object
        for obj in bpy.data.objects:
            if obj.name.startswith(f"{root_bone.name}_Ribbon"):
                bpy.data.objects.remove(obj, do_unlink=True)

        self.report({"INFO"}, "Removed Ribbon")
        return {"FINISHED"}

    def _collect_chain(self, root_bone):
        """Collect linear bone chain from root"""
        chain = [root_bone]
        current = root_bone
        while current.children:
            current = current.children[0]
            chain.append(current)
        return chain


def register():
    """Register Ribbon classes and properties"""
    bpy.utils.register_class(BONEFORGE_PT_p2c_ribbon)
    bpy.utils.register_class(BF_OT_GenerateRibbon)
    bpy.utils.register_class(BF_OT_RemoveRibbon)

    # Scene properties
    bpy.types.Scene.boneforge_ribbon_control_count = EnumProperty(
        name="Control Bone Count",
        description="Number of control bones",
        items=[
            ('2', "2 Bones", ""),
            ('3', "3 Bones", ""),
            ('5', "5 Bones", ""),
        ],
        default='3',
    )
    bpy.types.Scene.boneforge_ribbon_width = FloatProperty(
        name="Ribbon Width",
        description="Width of the ribbon surface",
        min=0.01,
        max=10.0,
        default=1.0,
    )


def unregister():
    """Unregister Ribbon classes and properties"""
    bpy.utils.unregister_class(BONEFORGE_PT_p2c_ribbon)
    bpy.utils.unregister_class(BF_OT_GenerateRibbon)
    bpy.utils.unregister_class(BF_OT_RemoveRibbon)

    # Remove scene properties
    if hasattr(bpy.types.Scene, "boneforge_ribbon_control_count"):
        del bpy.types.Scene.boneforge_ribbon_control_count
    if hasattr(bpy.types.Scene, "boneforge_ribbon_width"):
        del bpy.types.Scene.boneforge_ribbon_width
