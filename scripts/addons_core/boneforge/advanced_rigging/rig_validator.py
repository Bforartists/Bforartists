"""BoneCraft Phase 2C — Rig Validator.

Comprehensive validation checks for armature rigs including naming,
structure, weights, drivers, and collection organization.
"""
import re
import json
from dataclasses import dataclass
from typing import List, Callable, Optional
import bpy

import logging
from boneforge.i18n import T

logger = logging.getLogger(__name__)

try:
    from boneforge.core import get_custom_checks
except ImportError:
    def get_custom_checks():
        """Fallback if core not available."""
        return {}


# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# Blender truncates bone names beyond this length; names longer are flagged.
BLENDER_BONE_NAME_LIMIT: int = 63

# A pose-bone scale component smaller than this is treated as zero.
_ZERO_SCALE_EPSILON: float = 0.001

# Vertex-group weight contributions below this are considered negligible
# and not counted toward deform-bone influence totals.
_NEGLIGIBLE_WEIGHT_THRESHOLD: float = 0.001

# Allowed deviation of a per-vertex weight sum from 1.0 before warning.
_WEIGHT_SUM_TOLERANCE: float = 0.01


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ValidationResult:
    """Result of a single validation check."""
    check_name: str
    status: str  # 'pass', 'warn', 'fail'
    affected_bone: str = ""
    message: str = ""
    fix_operator: Optional[str] = None  # bl_idname of fix operator, if any


# ============================================================================
# VALIDATION CHECKS
# ============================================================================

def check_naming(armature_obj) -> List[ValidationResult]:
    """Check bone naming conventions.

    Rules:
    - No spaces or special characters (except underscore, dot and hyphen)
    - No bone names longer than 63 characters
    - No duplicate bone names
    """
    results = []
    armature = armature_obj.data

    # Track names for duplicates
    seen_names = {}
    invalid_chars_pattern = re.compile(r'[^\w.\-]')

    for bone in armature.bones:
        name = bone.name

        # Check for spaces/special chars (except _ . and -: CTRL-/MCH-/DEF- and Rigify ORG- names)
        if invalid_chars_pattern.search(name):
            results.append(ValidationResult(
                check_name="naming",
                status="fail",
                affected_bone=name,
                message=f"Bone '{name}' contains invalid characters (spaces/special chars not allowed)"
            ))

        # Check length
        if len(name) > BLENDER_BONE_NAME_LIMIT:
            results.append(ValidationResult(
                check_name="naming",
                status="fail",
                affected_bone=name,
                message=f"Bone '{name}' exceeds {BLENDER_BONE_NAME_LIMIT} character limit"
            ))

        # Check duplicates
        if name in seen_names:
            results.append(ValidationResult(
                check_name="naming",
                status="fail",
                affected_bone=name,
                message=f"Bone '{name}' is a duplicate of another bone"
            ))
        else:
            seen_names[name] = True

    if not results:
        results.append(ValidationResult(
            check_name="naming",
            status="pass",
            message="All bone names are valid"
        ))

    return results


def check_structure(armature_obj) -> List[ValidationResult]:
    """Check armature structure.

    Rules:
    - IK chains should have pole targets
    - No bones with zero scale
    - Space switch module: at least 2 spaces defined if used
    - SDK module: at least 2 curve points per relationship if used
    """
    results = []
    armature = armature_obj.data
    pose = armature_obj.pose

    # Check for zero scale bones
    for bone in armature.bones:
        pbone = pose.bones[bone.name]
        scale = pbone.scale
        if any(abs(s) < _ZERO_SCALE_EPSILON for s in scale):
            results.append(ValidationResult(
                check_name="structure",
                status="warn",
                affected_bone=bone.name,
                message=f"Bone '{bone.name}' has near-zero scale"
            ))

    # Check for IK chains without pole targets
    for bone in pose.bones:
        has_ik = False
        has_pole = False
        for constraint in bone.constraints:
            if constraint.type == 'IK':
                has_ik = True
                if constraint.pole_target is not None:
                    has_pole = True

        if has_ik and not has_pole:
            results.append(ValidationResult(
                check_name="structure",
                status="warn",
                affected_bone=bone.name,
                message=f"IK constraint on '{bone.name}' has no pole target"
            ))

    # Check space switch validation
    has_space_switch = False
    for bone in pose.bones:
        for prop in bone.keys():
            if prop.startswith('boneforge_p2c_space_') and prop.endswith('_active'):
                has_space_switch = True
                # Count Child Of constraints with "BF_Space_" prefix
                space_count = 0
                for constraint in bone.constraints:
                    if constraint.type == 'CHILD_OF' and 'BF_Space_' in constraint.name:
                        space_count += 1
                if space_count < 2:
                    results.append(ValidationResult(
                        check_name="structure",
                        status="warn",
                        affected_bone=bone.name,
                        message=f"Space switch on '{bone.name}' has less than 2 spaces"
                    ))
                break

    if has_space_switch:
        results.append(ValidationResult(
            check_name="structure",
            status="pass",
            message="Space switch module validated"
        ))

    # Check SDK validation
    has_sdk = armature.get("boneforge_p2c_sdk")
    if has_sdk:
        try:
            sdk_data = json.loads(armature["boneforge_p2c_sdk"])
            for i, sdk in enumerate(sdk_data):
                for target in sdk.get('driven_targets', []):
                    curve_points = target.get('curve_points', [])
                    if len(curve_points) < 2:
                        results.append(ValidationResult(
                            check_name="structure",
                            status="warn",
                            message=f"SDK relationship {i} target '{target.get('target_bone', 'unknown')}' has less than 2 curve points"
                        ))
        except (json.JSONDecodeError, KeyError) as exc:
            logger.debug("./advanced_rigging/rig_validator.py suppressed (json.JSONDecodeError, KeyError): %s", exc)

    if not results:
        results.append(ValidationResult(
            check_name="structure",
            status="pass",
            message="Armature structure is valid"
        ))

    return results


def check_weights(armature_obj) -> List[ValidationResult]:
    """Check vertex weight assignments.

    Rules:
    - All deform bones should have vertices weighted to them
    - Weight totals should sum to ~1.0 per vertex
    - No negligible influences (< 0.001)

    Only runs if mesh is parented to armature.
    """
    results = []
    armature = armature_obj.data

    # Find parented mesh
    mesh_obj = None
    for obj in bpy.context.scene.objects:
        if (obj.type == 'MESH' and
            obj.parent == armature_obj and
            obj.parent_type == 'ARMATURE'):
            mesh_obj = obj
            break

    if not mesh_obj:
        results.append(ValidationResult(
            check_name="weights",
            status="pass",
            message="No mesh parented (skipped)"
        ))
        return results

    mesh = mesh_obj.data
    vgroups = mesh_obj.vertex_groups

    # Check deform bones have weights
    deform_bones = {b.name for b in armature.bones if b.use_deform}

    for bone_name in deform_bones:
        if bone_name not in vgroups:
            results.append(ValidationResult(
                check_name="weights",
                status="warn",
                affected_bone=bone_name,
                message=f"Deform bone '{bone_name}' has no vertex group"
            ))
            continue

        vgroup = vgroups[bone_name]
        if len(vgroup.index_list) == 0:
            results.append(ValidationResult(
                check_name="weights",
                status="warn",
                affected_bone=bone_name,
                message=f"Deform bone '{bone_name}' has no vertices weighted"
            ))
        else:
            # Per-bone check: verify ALL vertex weights are not all negligible
            all_weights_negligible = True
            for vert in mesh.vertices:
                try:
                    weight = vgroup.weight(vert.index)
                    if weight > _NEGLIGIBLE_WEIGHT_THRESHOLD:
                        all_weights_negligible = False
                        break
                except RuntimeError as exc:
                    logger.debug("./advanced_rigging/rig_validator.py suppressed RuntimeError: %s", exc)

            if all_weights_negligible and len(vgroup.index_list) > 0:
                results.append(ValidationResult(
                    check_name="weights",
                    status="warn",
                    affected_bone=bone_name,
                    message=f"Deform bone '{bone_name}' has all weights below {_NEGLIGIBLE_WEIGHT_THRESHOLD}"
                ))

    # Check weight totals
    for vert in mesh.vertices:
        total_weight = 0.0
        negligible_count = 0
        for vgroup in vgroups:
            try:
                weight = vgroup.weight(vert.index)
                if weight > _NEGLIGIBLE_WEIGHT_THRESHOLD:
                    total_weight += weight
                else:
                    negligible_count += 1
            except RuntimeError as exc:
                logger.debug("./advanced_rigging/rig_validator.py suppressed RuntimeError: %s", exc)

        if abs(total_weight - 1.0) > _WEIGHT_SUM_TOLERANCE:
            results.append(ValidationResult(
                check_name="weights",
                status="warn",
                affected_bone=str(vert.index),
                message=f"Vertex {vert.index} weights sum to {total_weight:.2f}, not 1.0"
            ))

        if negligible_count > 0:
            results.append(ValidationResult(
                check_name="weights",
                status="warn",
                affected_bone=str(vert.index),
                message=f"Vertex {vert.index} has {negligible_count} negligible weights"
            ))

    if not results:
        results.append(ValidationResult(
            check_name="weights",
            status="pass",
            message="Weight assignments are valid"
        ))

    return results


def check_drivers(armature_obj) -> List[ValidationResult]:
    """Check driver validity.

    Rules:
    - No missing bone references
    - No expressions that need Python (simple expressions run without it)
    - No circular dependencies
    """
    results = []
    armature = armature_obj.data

    if not armature_obj.animation_data or not armature_obj.animation_data.drivers:
        results.append(ValidationResult(
            check_name="drivers",
            status="pass",
            message="No drivers found"
        ))
        return results

    bones = {b.name for b in armature.bones}

    # Build driver dependency graph
    driver_graph = {}  # driven_bone -> [driver_bones]

    for fcurve in armature_obj.animation_data.drivers:
        driver = fcurve.driver

        # Check for Python expressions
        if driver.type == 'SCRIPTED' and not driver.is_simple_expression:
            results.append(ValidationResult(
                check_name="drivers",
                status="warn",
                message=f"Driver uses Python expression: {driver.expression}",
                affected_bone=fcurve.data_path
            ))

        # Extract driven bone from data path
        driven_bone = None
        if 'pose.bones["' in fcurve.data_path:
            start = fcurve.data_path.find('pose.bones["') + len('pose.bones["')
            end = fcurve.data_path.find('"]', start)
            if end > start:
                driven_bone = fcurve.data_path[start:end]

        # Check variable references and build graph
        for var in driver.variables:
            for target in var.targets:
                if target.id_type == 'ARMATURE' and target.id:
                    if target.bone_target and target.bone_target not in bones:
                        results.append(ValidationResult(
                            check_name="drivers",
                            status="fail",
                            affected_bone=target.bone_target,
                            message=f"Driver references missing bone '{target.bone_target}'"
                        ))

                    # Add to graph if we found driven bone
                    if driven_bone and target.bone_target:
                        if driven_bone not in driver_graph:
                            driver_graph[driven_bone] = []
                        driver_graph[driven_bone].append(target.bone_target)

    # Check for circular dependencies using DFS
    def has_cycle(graph):
        """Detect cycle in directed graph using DFS."""
        visited = set()
        rec_stack = set()

        def visit(node, path):
            """Recursively traverse from ``node`` and return True if the path loops back onto the DFS stack."""
            if node in rec_stack:
                return True  # Cycle found
            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if visit(neighbor, path + [node]):
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if visit(node, []):
                    return True
        return False

    if has_cycle(driver_graph):
        results.append(ValidationResult(
            check_name="drivers",
            status="fail",
            message="Circular dependency detected in drivers"
        ))

    if not results:
        results.append(ValidationResult(
            check_name="drivers",
            status="pass",
            message="All drivers are valid"
        ))

    return results


def check_collections(armature_obj) -> List[ValidationResult]:
    """Check bone collection organization.

    Rules:
    - All bones should be in at least one collection
    - At least one collection should contain 'deform' or 'DEF'
    - At least one collection should contain 'control' or 'CTL'
    """
    results = []
    armature = armature_obj.data

    # Check if collections exist
    if not hasattr(armature, 'collections') or len(armature.collections) == 0:
        results.append(ValidationResult(
            check_name="collections",
            status="warn",
            message="No bone collections defined"
        ))
        return results

    # Check each bone
    for bone in armature.bones:
        in_collection = False
        for collection in armature.collections:
            if bone.name in [b.name for b in collection.bones]:
                in_collection = True
                break

        if not in_collection:
            results.append(ValidationResult(
                check_name="collections",
                status="warn",
                affected_bone=bone.name,
                message=f"Bone '{bone.name}' is not in any collection"
            ))

    # Check for deform collection
    has_deform_collection = False
    for collection in armature.collections:
        if 'deform' in collection.name.lower() or 'def' in collection.name.lower():
            has_deform_collection = True
            break

    if not has_deform_collection:
        results.append(ValidationResult(
            check_name="collections",
            status="warn",
            message="No bone collection contains 'deform' or 'DEF' in name"
        ))

    # Check for control collection
    has_control_collection = False
    for collection in armature.collections:
        if 'control' in collection.name.lower() or 'ctl' in collection.name.lower():
            has_control_collection = True
            break

    if not has_control_collection:
        results.append(ValidationResult(
            check_name="collections",
            status="warn",
            message="No bone collection contains 'control' or 'CTL' in name"
        ))

    if not results:
        results.append(ValidationResult(
            check_name="collections",
            status="pass",
            message="All bones are organized in collections"
        ))

    return results


# ============================================================================
# CUSTOM CHECK REGISTRY
# ============================================================================

_custom_checks = {}


def register_custom_check(name: str, check_fn: Callable[[bpy.types.Object], List[ValidationResult]]):
    """Register a custom validation check function.

    Args:
        name: Unique name for the check
        check_fn: Function taking armature_obj and returning list of ValidationResult
    """
    _custom_checks[name] = check_fn


# ============================================================================
# MAIN VALIDATION
# ============================================================================

def run_all_checks(armature_obj) -> List[ValidationResult]:
    """Run all validation checks on an armature."""
    if not armature_obj or armature_obj.type != 'ARMATURE':
        return [ValidationResult(
            check_name="init",
            status="fail",
            message="Not an armature object"
        )]

    all_results = []

    # Run built-in checks
    check_functions = [
        check_naming,
        check_structure,
        check_weights,
        check_drivers,
        check_collections,
    ]

    for check_fn in check_functions:
        try:
            results = check_fn(armature_obj)
            all_results.extend(results)
        except Exception as e:
            all_results.append(ValidationResult(
                check_name=check_fn.__name__,
                status="fail",
                message=f"Check error: {str(e)}"
            ))

    # Run locally registered custom checks
    for name, check_fn in _custom_checks.items():
        try:
            results = check_fn(armature_obj)
            all_results.extend(results)
        except Exception as e:
            all_results.append(ValidationResult(
                check_name=name,
                status="fail",
                message=f"Custom check error: {str(e)}"
            ))

    # Run custom checks from core module
    try:
        core_custom_checks = get_custom_checks()
        for name, check_fn in core_custom_checks.items():
            try:
                results = check_fn(armature_obj)
                all_results.extend(results)
            except Exception as e:
                all_results.append(ValidationResult(
                    check_name=f"core_{name}",
                    status="fail",
                    message=f"Custom check error: {str(e)}"
                ))
    except Exception as e:
        pass  # Core custom checks not available

    return all_results


# ============================================================================
# OPERATORS
# ============================================================================

class BF_OT_RunValidation(bpy.types.Operator):
    """Run validation checks on the active armature."""
    bl_idname = "boneforge.run_validation"
    bl_label = "Run Validation"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        armature_obj = context.active_object
        results = run_all_checks(armature_obj)

        # CollectionProperty is read-only as an attribute; we must clear()
        # and .add() items individually rather than assigning a list.
        coll = context.window_manager.boneforge_validation_results
        coll.clear()
        for r in results:
            item = coll.add()
            item.check_name = r.check_name or ""
            item.status = r.status or ""
            item.affected_bone = r.affected_bone or ""
            item.message = r.message or ""
            item.fix_operator = r.fix_operator or ""

        context.window_manager.boneforge_validation_index = 0
        self.report({'INFO'}, f"Validation completed ({len(results)} results)")
        return {'FINISHED'}


class BF_OT_ExportValidationReport(bpy.types.Operator):
    """Export validation results to a text file."""
    bl_idname = "boneforge.export_validation_report"
    bl_label = "Export Report"
    bl_options = {'REGISTER'}

    filename_ext = ".txt"
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath for validation report",
        default="validation_report.txt"
    )

    @classmethod
    def poll(cls, context):
        return hasattr(context.window_manager, 'boneforge_validation_results')

    def execute(self, context):
        results = context.window_manager.boneforge_validation_results
        armature = context.active_object.name if context.active_object else "Unknown"

        # Build report
        lines = [
            f"BoneCraft Validation Report",
            f"Armature: {armature}",
            f"{'=' * 60}",
            ""
        ]

        # Group by status
        for status in ['fail', 'warn', 'pass']:
            status_results = [r for r in results if r.status == status]
            if not status_results:
                continue

            lines.append(f"{status.upper()} ({len(status_results)})")
            lines.append("-" * 60)

            for result in status_results:
                lines.append(f"  Check: {result.check_name}")
                if result.affected_bone:
                    lines.append(f"  Bone: {result.affected_bone}")
                lines.append(f"  {result.message}")
                if result.fix_operator:
                    lines.append(f"  Fix: {result.fix_operator}")
                lines.append("")

        # Write file
        report_text = "\n".join(lines)
        with open(bpy.path.abspath(self.filepath), 'w') as f:
            f.write(report_text)

        self.report({'INFO'}, f"Report exported to {self.filepath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class BF_OT_SelectValidationBone(bpy.types.Operator):
    """Select the bone affected by a validation result."""
    bl_idname = "boneforge.select_validation_bone"
    bl_label = "Select Bone"
    bl_options = {'REGISTER'}

    bone_name: bpy.props.StringProperty(
        name="Bone Name",
        description="Name of bone to select"
    )

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        armature = context.active_object
        if self.bone_name not in armature.data.bones:
            self.report({'WARNING'}, f"Bone '{self.bone_name}' not found")
            return {'CANCELLED'}

        # Switch to pose mode for bone selection.
        if context.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')

        bpy.ops.pose.select_all(action='DESELECT')

        bone = armature.data.bones[self.bone_name]
        armature.data.bones.active = bone

        # v3.0.24: Bforartists 5.2 strips both ``Bone.select`` and
        # ``Bone.select_head``/``select_tail``.  The only portable way
        # to toggle selection across Blender + Bforartists is via the
        # pose operators, which go through the same code path the UI
        # uses.  ``select_pattern`` takes a glob and matches exact name
        # if no wildcards are present.
        # Blender / Bforartists 5 select on the pose bone; ``pose.select_pattern``
        # (the last fallback below) no longer exists there.
        selected = False
        pose_bone = armature.pose.bones.get(self.bone_name)
        if pose_bone is not None and hasattr(pose_bone, "select"):
            pose_bone.select = True
            selected = True
        if not selected:
            try:
                bone.select = True
                selected = True
            except AttributeError:
                pass
        if not selected:
            try:
                bone.select_head = True
                bone.select_tail = True
                selected = True
            except AttributeError:
                pass
        if not selected:
            # Final fallback — drive the Pose-mode select operator.
            try:
                bpy.ops.pose.select_pattern(
                    pattern=self.bone_name,
                    case_sensitive=True,
                    extend=False,
                )
            except Exception as exc:
                self.report({'WARNING'},
                            f"Could not select '{self.bone_name}': {exc}")
                return {'CANCELLED'}

        self.report({'INFO'}, f"Selected bone '{self.bone_name}'")
        if context.area is not None:
            context.area.tag_redraw()
        return {'FINISHED'}


# ============================================================================
# PANEL
# ============================================================================

class BONEFORGE_UL_ValidationResults(bpy.types.UIList):
    """UIList for validation results."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """Render one validation-result row with a pass/warn/fail icon, check name, and message."""
        # Status icons
        status_icons = {
            'pass': 'CHECKMARK',
            'warn': 'INFO',
            'fail': 'ERROR'
        }
        status_icon = status_icons.get(item.status, 'QUESTION')

        row = layout.row()
        row.label(text=f"[{item.check_name}]", icon=status_icon)
        row.label(text=item.message)

        if item.affected_bone:
            props = row.operator("boneforge.select_validation_bone", text=T("Select"), icon='RESTRICT_SELECT_OFF')
            props.bone_name = item.affected_bone

        if item.fix_operator:
            row.operator(item.fix_operator, text=T("Fix"), icon='TOOL_SETTINGS')


class BONEFORGE_PT_p2c_rig_validator(bpy.types.Panel):
    """Rig validation panel."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2c_rig_validator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"

    def draw_header(self, context):
        self.layout.label(text=T("Rig Validator"))

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        # Run button
        layout.operator("boneforge.run_validation", icon='CHECKMARK')

        # Results list
        if hasattr(wm, 'boneforge_validation_results'):
            results = wm.boneforge_validation_results

            # Summary
            fail_count = sum(1 for r in results if r.status == 'fail')
            warn_count = sum(1 for r in results if r.status == 'warn')

            if fail_count > 0:
                row = layout.row()
                row.label(text=f"FAIL: {fail_count}", icon='ERROR')

            if warn_count > 0:
                row = layout.row()
                row.label(text=f"WARN: {warn_count}", icon='INFO')

            if fail_count == 0 and warn_count == 0:
                layout.label(text=T("All checks passed!"), icon='CHECKMARK')

            # List
            layout.label(text=T("Results:"))
            layout.template_list(
                "BONEFORGE_UL_ValidationResults",
                "validation_results",
                wm,
                "boneforge_validation_results",
                wm,
                "boneforge_validation_index",
                rows=6
            )

            # Export button
            layout.operator("boneforge.export_validation_report", icon='EXPORT')


# ============================================================================
# REGISTRATION
# ============================================================================

class BONEFORGE_PG_ValidationResult(bpy.types.PropertyGroup):
    """Blender-side storage for a single ValidationResult row.

    A CollectionProperty must reference a registered PropertyGroup subclass
    with real bpy.props fields; monkey-patching bpy.types.PropertyGroup does
    not register per-instance fields.
    """
    check_name: bpy.props.StringProperty(name="Check", default="")
    status: bpy.props.StringProperty(name="Status", default="")
    affected_bone: bpy.props.StringProperty(name="Bone", default="")
    message: bpy.props.StringProperty(name="Message", default="")
    fix_operator: bpy.props.StringProperty(name="Fix Operator", default="")


def _init_properties():
    """Initialize window manager properties."""
    bpy.types.WindowManager.boneforge_validation_results = bpy.props.CollectionProperty(
        type=BONEFORGE_PG_ValidationResult,
        description="Validation results"
    )
    bpy.types.WindowManager.boneforge_validation_index = bpy.props.IntProperty(
        name="Validation Index",
        default=0
    )


def _clear_properties():
    """Clear window manager properties."""
    if hasattr(bpy.types.WindowManager, 'boneforge_validation_results'):
        del bpy.types.WindowManager.boneforge_validation_results
    if hasattr(bpy.types.WindowManager, 'boneforge_validation_index'):
        del bpy.types.WindowManager.boneforge_validation_index


# BONEFORGE_PT_p2c_rig_validator is intentionally excluded here.
# It is delegated through BF_PT_sb_rig_validator in taskboard/sidebar.py
# under the Inspect hub, so it must not register as a standalone panel.
classes = (
    BONEFORGE_PG_ValidationResult,
    BONEFORGE_UL_ValidationResults,
    BF_OT_RunValidation,
    BF_OT_ExportValidationReport,
    BF_OT_SelectValidationBone,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    _init_properties()


def unregister():
    _clear_properties()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
