"""BoneCraft Phase 2C — Multi-Bone Chain Dynamics.

Verlet-integration secondary motion simulation for bone chains.
Used for hair, cloth overlap, tails, and other secondary animation.
Category: Advanced Rigging.
"""

import bpy
import json
from mathutils import Vector
from bpy.props import FloatProperty, BoolProperty, PointerProperty, CollectionProperty, StringProperty
from bpy.types import PropertyGroup, Operator, Panel
from boneforge.core import register_handler_chain, unregister_handler_chain
from boneforge.i18n import T


# Registry of armature names with chain dynamics enabled.
# Populated by BF_OT_AddChainDynamics, pruned by BF_OT_RemoveChainDynamics and unregister().
_dynamics_registry = set()  # set of armature object names (str)

# Per-armature JSON cache: name -> (raw_json_str, parsed_dict)
# Avoids re-parsing the custom property string every frame when state hasn't changed.
_chain_state_cache = {}  # type: dict[str, tuple[str, dict]]


class BF_ChainDynamicsSegmentOverride(PropertyGroup):
    """Per-segment override for chain dynamics parameters."""
    bone_name: StringProperty(name="Bone Name")
    use_override: BoolProperty(name="Use Override", default=False)
    stiffness: FloatProperty(name="Stiffness", min=0.0, max=1.0, default=0.5)
    damping: FloatProperty(name="Damping", min=0.0, max=1.0, default=0.3)
    mass: FloatProperty(name="Mass", min=0.01, max=10.0, default=1.0)


class BF_ChainDynamicsSettings(PropertyGroup):
    """Global chain dynamics settings stored on armature."""
    stiffness: FloatProperty(
        name="Stiffness",
        description="Spring stiffness (0=loose, 1=stiff)",
        min=0.0, max=1.0, default=0.5
    )
    damping: FloatProperty(
        name="Damping",
        description="Velocity damping (0=no damping, 1=full damping)",
        min=0.0, max=1.0, default=0.3
    )
    mass: FloatProperty(
        name="Mass",
        description="Mass per bone segment",
        min=0.01, max=10.0, default=1.0
    )
    gravity_scale: FloatProperty(
        name="Gravity Scale",
        description="Gravity influence multiplier",
        min=0.0, max=2.0, default=1.0
    )
    segment_overrides: CollectionProperty(
        type=BF_ChainDynamicsSegmentOverride,
        name="Segment Overrides"
    )


class BF_OT_AddChainDynamics(Operator):
    """Add spring-damper dynamics to selected bone chain."""
    bl_idname = "boneforge.add_chain_dynamics"
    bl_label = "Add Chain Dynamics"
    bl_options = {'REGISTER', 'UNDO'}

    stiffness: FloatProperty(description='How strongly the chain springs back to its rest shape',
        name="Stiffness", min=0.0, max=1.0, default=0.5
    )
    damping: FloatProperty(description="How quickly the chain's swinging dies down",
        name="Damping", min=0.0, max=1.0, default=0.3
    )
    mass: FloatProperty(description='How heavy each bone of the chain is; heavier swings further',
        name="Mass", min=0.01, max=10.0, default=1.0
    )
    gravity_scale: FloatProperty(description='How strongly gravity pulls the chain; 0 floats, 1 is normal',
        name="Gravity Scale", min=0.0, max=2.0, default=1.0
    )

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' and
                context.object and
                context.object.type == 'ARMATURE' and
                context.selected_pose_bones)

    def execute(self, context):
        armature = context.object
        selected_bones = context.selected_pose_bones

        if not selected_bones:
            self.report({'ERROR'}, "No bones selected")
            return {'CANCELLED'}

        # Create chain config
        chain_config = {
            "bones": [b.name for b in selected_bones],
            "stiffness": self.stiffness,
            "damping": self.damping,
            "mass": self.mass,
            "gravity_scale": self.gravity_scale,
            "velocities": {b.name: [0.0, 0.0, 0.0] for b in selected_bones},
            "rest_positions": {}
        }

        # Store rest positions in local bone space
        for bone in selected_bones:
            pbone = armature.pose.bones[bone.name]
            chain_config["rest_positions"][bone.name] = [
                pbone.location.x, pbone.location.y, pbone.location.z
            ]

        # Store as JSON custom property
        if "boneforge_p2c_dynamics" not in armature:
            armature["boneforge_p2c_dynamics"] = ""

        armature["boneforge_p2c_dynamics"] = json.dumps(chain_config)
        armature["boneforge_chain_bone_count"] = len(selected_bones)

        # Register armature in module registry and invalidate its cache
        _dynamics_registry.add(armature.name)
        _chain_state_cache.pop(armature.name, None)

        # Register frame change handler
        if _chain_dynamics_handler not in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.append(_chain_dynamics_handler)

        self.report({'INFO'}, f"Added dynamics to {len(selected_bones)} bones")
        return {'FINISHED'}


class BF_OT_RemoveChainDynamics(Operator):
    """Remove dynamics from the active armature."""
    bl_idname = "boneforge.remove_chain_dynamics"
    bl_label = "Remove Chain Dynamics"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' and
                context.object and
                context.object.type == 'ARMATURE')

    def execute(self, context):
        armature = context.object

        if "boneforge_p2c_dynamics" in armature:
            del armature["boneforge_p2c_dynamics"]
            if "boneforge_chain_bone_count" in armature:
                del armature["boneforge_chain_bone_count"]
            _dynamics_registry.discard(armature.name)
            _chain_state_cache.pop(armature.name, None)
            self.report({'INFO'}, "Removed chain dynamics")
        else:
            self.report({'WARNING'}, "No dynamics found on this armature")

        return {'FINISHED'}


class BF_OT_BakeChainDynamics(Operator):
    """Bake simulation to keyframes and remove handler."""
    bl_idname = "boneforge.bake_chain_dynamics"
    bl_label = "Bake Chain Dynamics"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' and
                context.object and
                context.object.type == 'ARMATURE')

    def execute(self, context):
        armature = context.object

        if "boneforge_p2c_dynamics" not in armature:
            self.report({'ERROR'}, "No chain dynamics on this armature")
            return {'CANCELLED'}

        # Get animation range
        scene = context.scene
        start_frame = scene.frame_start
        end_frame = scene.frame_end

        try:
            chain_data = json.loads(armature["boneforge_p2c_dynamics"])
        except (json.JSONDecodeError, TypeError) as e:
            self.report({"ERROR"}, f"Corrupt dynamics data: {e}")
            return {"CANCELLED"}
        bone_names = chain_data["bones"]

        # Ensure action exists
        if not armature.animation_data:
            armature.animation_data_create()

        if not armature.animation_data.action:
            action = bpy.data.actions.new(name=f"{armature.name}_Dynamics")
            armature.animation_data.action = action
        else:
            action = armature.animation_data.action

        # Insert keyframes for each bone
        for frame in range(start_frame, end_frame + 1):
            scene.frame_set(frame)
            for bone_name in bone_names:
                if bone_name not in armature.pose.bones:
                    continue
                pbone = armature.pose.bones[bone_name]
                pbone.keyframe_insert(data_path="location", frame=frame)
                pbone.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        self.report({'INFO'}, f"Baked {len(bone_names)} bones to {end_frame - start_frame + 1} frames")

        # Remove dynamics
        del armature["boneforge_p2c_dynamics"]

        return {'FINISHED'}


def _chain_dynamics_handler(scene):
    """Frame change handler for chain dynamics simulation.

    Iterates only the registered armatures (O(N_registered)) instead of
    all scene objects. Skips json.loads when the stored property hasn't
    changed since last frame; updates the cache after writing back.
    """
    dead = set()
    for obj_name in _dynamics_registry:
        obj = bpy.data.objects.get(obj_name)
        if obj is None:
            dead.add(obj_name)
            continue

        if "boneforge_p2c_dynamics" not in obj:
            continue

        raw_json = obj["boneforge_p2c_dynamics"]
        cached = _chain_state_cache.get(obj_name)
        if cached and cached[0] == raw_json:
            chain_data = cached[1]
        else:
            try:
                chain_data = json.loads(raw_json)
            except (json.JSONDecodeError, TypeError):
                continue

        armature = obj
        bone_names = chain_data["bones"]
        stiffness = chain_data.get("stiffness", 0.5)
        damping = chain_data.get("damping", 0.3)
        mass = chain_data.get("mass", 1.0)
        gravity_scale = chain_data.get("gravity_scale", 1.0)
        velocities = chain_data.get("velocities", {})
        rest_positions = chain_data.get("rest_positions", {})

        # Gravity vector (Blender Y-up convention, downward)
        gravity = Vector((0.0, -9.81 * gravity_scale * 0.001, 0.0))  # scaled for frame delta
        dt = 1.0 / 24.0  # standard frame time

        # Verlet integration step for each bone
        for bone_name in bone_names:
            if bone_name not in armature.pose.bones:
                continue

            pbone = armature.pose.bones[bone_name]

            # Current position in bone local space
            current_pos = pbone.location.copy()
            rest_pos = Vector(rest_positions.get(bone_name, [0, 0, 0]))

            # Get velocity or initialize
            vel_key = f"vel_{bone_name}"
            if vel_key not in velocities:
                velocities[vel_key] = [0.0, 0.0, 0.0]

            velocity = Vector(velocities.get(vel_key, [0.0, 0.0, 0.0]))

            # Spring force: pull toward rest pose
            spring_offset = rest_pos - current_pos
            spring_force = spring_offset * stiffness

            # Apply gravity
            force = spring_force + gravity

            # Damping
            acceleration = force / mass
            velocity = velocity * (1.0 - damping) + acceleration * dt

            # Update position (Verlet style)
            new_pos = current_pos + velocity * dt

            # Apply to bone
            pbone.location = new_pos

            # Store velocity for next frame
            velocities[vel_key] = [velocity.x, velocity.y, velocity.z]

        # Save updated state (schema identical to v18)
        chain_data["velocities"] = velocities
        new_json = json.dumps(chain_data)
        obj["boneforge_p2c_dynamics"] = new_json
        _chain_state_cache[obj_name] = (new_json, chain_data)

    # Prune dead references (objects deleted externally)
    if dead:
        _dynamics_registry -= dead
        for name in dead:
            _chain_state_cache.pop(name, None)


class BONEFORGE_PT_p2c_chain_dynamics(Panel):
    """Chain Dynamics panel in Rig Construction tab."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2c_chain_dynamics"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Chain Dynamics"))

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' and
                context.object and
                context.object.type == 'ARMATURE')

    def draw(self, context):
        layout = self.layout
        armature = context.object

        has_dynamics = "boneforge_p2c_dynamics" in armature

        if has_dynamics:
            bone_count = armature.get("boneforge_chain_bone_count", 0)
            layout.label(text=f"Active Chain: {bone_count} bones")

            row = layout.row(align=True)
            row.operator("boneforge.bake_chain_dynamics", text=T("Bake"), icon='CAMERA_DATA')
            row.operator("boneforge.remove_chain_dynamics", text=T("Remove"), icon='X')
            _draw_dynamics_settings(layout, armature, default_closed=False)
        else:
            layout.label(text=T("Select bone chain and add dynamics"))
            layout.operator("boneforge.add_chain_dynamics", icon='PHYSICS')
            _draw_dynamics_settings(layout, armature, default_closed=True)


def _draw_dynamics_settings(layout, armature, default_closed):
    """The chain's physics settings, in a fold below the actions (act first, tune later)."""
    from boneforge.core.helpers import draw_helper, options_fold
    col = options_fold(layout, "bc_chain_dynamics_settings", text="Settings", default_closed=default_closed)
    if col is None:
        return
    for name in ("stiffness", "damping", "mass", "gravity_scale"):
        col.prop(armature.boneforge_chain_dynamics, name)
    col.label(text=T("Collision uses simplified sphere approximation."))
    col.label(text=T("Concave surfaces may not collide correctly."))


def _chain_dynamics_frame_change(scene):
    """Frame change handler for chain dynamics simulation."""
    _chain_dynamics_handler(scene)


def register():
    """Register chain dynamics classes and properties."""
    bpy.utils.register_class(BF_ChainDynamicsSegmentOverride)
    bpy.utils.register_class(BF_ChainDynamicsSettings)
    bpy.utils.register_class(BF_OT_AddChainDynamics)
    bpy.utils.register_class(BF_OT_RemoveChainDynamics)
    bpy.utils.register_class(BF_OT_BakeChainDynamics)
    bpy.utils.register_class(BONEFORGE_PT_p2c_chain_dynamics)

    bpy.types.Object.boneforge_chain_dynamics = PointerProperty(
        type=BF_ChainDynamicsSettings,
        name="Chain Dynamics"
    )

    # Register handler chain
    register_handler_chain('frame_change_post', _chain_dynamics_frame_change, priority=70)


def unregister():
    """Unregister chain dynamics classes and properties."""
    # Clear module-level state before removing the handler
    _dynamics_registry.clear()
    _chain_state_cache.clear()

    # Unregister handler chain
    unregister_handler_chain('frame_change_post', _chain_dynamics_frame_change)

    if hasattr(bpy.types.Object, 'boneforge_chain_dynamics'):
        del bpy.types.Object.boneforge_chain_dynamics

    bpy.utils.unregister_class(BONEFORGE_PT_p2c_chain_dynamics)
    bpy.utils.unregister_class(BF_OT_BakeChainDynamics)
    bpy.utils.unregister_class(BF_OT_RemoveChainDynamics)
    bpy.utils.unregister_class(BF_OT_AddChainDynamics)
    bpy.utils.unregister_class(BF_ChainDynamicsSettings)
    bpy.utils.unregister_class(BF_ChainDynamicsSegmentOverride)
