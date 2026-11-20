"""BoneCraft — profile-driven game export (BF-GAP-05b / R5).

Drives FBX/GLB export from a selected :mod:`io_hub.profiles` profile, runs the
profile's rig-validator checks (explicit, never silent fixes), filters actions
to prevent corrupt multi-take exports, and supports a deform-only hierarchy and
root-motion bake.

Two layers:
  * pure mapping ``profile_to_fbx_kwargs`` / ``profile_to_gltf_kwargs`` —
    no ``bpy``, unit-testable headlessly;
  * the export + check operators that call Blender's exporters.

Clean-room: export settings derive from public format/engine docs; checks reuse
BoneCraft's own ``rig_validator``.
"""

# ``profiles`` is imported lazily inside the functions that need it so the pure
# kwargs mappers stay importable without triggering io_hub/__init__ (bpy).


# ── pure profile -> exporter kwargs ───────────────────────────

def profile_to_fbx_kwargs(profile):
    """Map a profile dict onto ``export_scene.fbx`` keyword arguments."""
    return {
        "axis_forward": profile["axis_forward"],
        "axis_up": profile["axis_up"],
        "primary_bone_axis": profile["primary_bone_axis"],
        "secondary_bone_axis": profile["secondary_bone_axis"],
        "use_armature_deform_only": bool(profile["deform_only"]),
        "add_leaf_bones": bool(profile["add_leaf_bones"]),
        "apply_unit_scale": True,
        "apply_scale_options": 'FBX_SCALE_NONE',
        "mesh_smooth_type": 'OFF',
        "use_mesh_modifiers": True,
        "bake_anim_use_all_actions": False,
        "bake_anim_use_nla_strips": False,
        "bake_anim_force_startend_keying": True,
        "path_mode": 'AUTO',
    }


def profile_to_gltf_kwargs(profile):
    """Map a profile dict onto ``export_scene.gltf`` keyword arguments."""
    return {
        "export_format": 'GLB',
        "export_yup": (profile["axis_up"] == "Y"),
        "export_apply": True,
        "export_def_bones": bool(profile["deform_only"]),
    }


# Action export modes (pure description; the operator resolves them in-host).
ACTION_MODES = (
    ('ACTIVE', "Active Action", "Export only the armature's active action"),
    ('ALL', "All Actions", "Export every action as a separate take"),
    ('NONE', "No Animation", "Export the rest pose only"),
)


def resolve_action_kwargs(mode):
    """Pure: bake-animation kwargs for an action export mode."""
    if mode == 'NONE':
        return {"bake_anim": False}
    return {"bake_anim": True,
            "bake_anim_use_all_actions": (mode == 'ALL')}


# Keyframe interpolation modes for export (game engines often want stepped or
# linear curves rather than Bezier).
INTERP_MODES = (
    ('BEZIER', "Bezier", "Keep smooth Bezier interpolation"),
    ('LINEAR', "Linear", "Straight-line interpolation between keys"),
    ('CONSTANT', "Constant", "Stepped / held keys"),
)


def _action_fcurves(action):
    """F-curves across legacy and slotted (Blender 4.4+) action APIs."""
    if action is None:
        return []
    layers = getattr(action, "layers", None)
    if layers:
        fcurves = []
        for layer in layers:
            for strip in layer.strips:
                for cb in getattr(strip, "channelbags", []):
                    fcurves.extend(cb.fcurves)
        if fcurves:
            return fcurves
    return list(getattr(action, "fcurves", []))


def set_action_interpolation(action, mode):
    """Set every keyframe's interpolation on ``action`` (in-host). Returns the
    number of keyframes changed. ``BEZIER`` is a no-op pass-through."""
    if action is None or mode == 'BEZIER':
        return 0
    n = 0
    for fc in _action_fcurves(action):
        for kp in fc.keyframe_points:
            kp.interpolation = mode
            n += 1
        fc.update()
    return n


# ── checks (in-host; reuse rig_validator) ─────────────────────


def check_shape_keys(objects):
    """Validate shape keys on the exported meshes (explicit, never silent).

    Returns ``{check, status, bone, message, fix}`` dicts: a warn per mesh that
    carries shape keys (so the user confirms shape-key export is intended), and
    a warn for a relative key whose basis is not the first block (a common cause
    of broken morph export).
    """
    findings = []
    for ob in objects:
        if ob.type != 'MESH':
            continue
        sk = ob.data.shape_keys
        if sk is None:
            continue
        blocks = list(sk.key_blocks)
        if len(blocks) <= 1:
            continue
        findings.append({
            "check": "shape_keys", "status": "warn", "bone": ob.name,
            "message": "%s has %d shape keys — ensure shape-key (morph) export "
                       "is enabled for this target" % (ob.name, len(blocks) - 1),
            "fix": "",
        })
        if sk.use_relative and sk.reference_key and blocks \
                and sk.reference_key.name != blocks[0].name:
            findings.append({
                "check": "shape_keys", "status": "warn", "bone": ob.name,
                "message": "%s relative basis is not the first key block — "
                           "morph targets may export incorrectly" % ob.name,
                "fix": "",
            })
    return findings

def run_profile_checks(armature_obj, profile_id):
    """Run only the checks the profile asks for; return a list of dicts
    ``{check, status, bone, message, fix}`` (status in pass/warn/fail)."""
    from boneforge.advanced_rigging import rig_validator
    from boneforge.io_hub import profiles as _profiles
    profile = _profiles.get_profile(profile_id)
    check_fns = {
        "naming": rig_validator.check_naming,
        "structure": rig_validator.check_structure,
        "weights": rig_validator.check_weights,
    }
    findings = []
    for name in profile["checks"]:
        fn = check_fns.get(name)
        if fn is None:
            continue
        try:
            for r in fn(armature_obj):
                findings.append({
                    "check": r.check_name, "status": r.status,
                    "bone": r.affected_bone, "message": r.message,
                    "fix": r.fix_operator or "",
                })
        except Exception as exc:                       # never hard-fail a check
            findings.append({"check": name, "status": "fail", "bone": "",
                             "message": "check error: %s" % exc, "fix": ""})
    # shape-key validation on the meshes this armature deforms
    import bpy
    meshes = [o for o in bpy.context.scene.objects
              if o.type == 'MESH' and (o.parent is armature_obj or any(
                  m.type == 'ARMATURE' and m.object is armature_obj
                  for m in o.modifiers))]
    findings.extend(check_shape_keys(meshes))
    return findings


# ── export (in-host) ──────────────────────────────────────────

def _deform_bone_names(armature_obj):
    return {b.name for b in armature_obj.data.bones if b.use_deform}


def _deformed_meshes(context, armature):
    """Selected meshes the armature deforms (all of them if none is selected)."""
    def deformed(o):
        return o.type == 'MESH' and (o.parent is armature or any(
            m.type == 'ARMATURE' and m.object is armature for m in o.modifiers))
    sel = [o for o in context.selected_objects if deformed(o)]
    return sel or [o for o in context.scene.objects if deformed(o)]


def export_with_profile(context, profile_id, filepath, action_mode='ACTIVE',
                        root_motion=False, interpolation='BEZIER', t_pose=None,
                        bone_naming='NONE'):
    """Export the selection using ``profile_id``'s settings.

    Returns ``(ok, message)``. ``root_motion`` temporarily tags the profile's
    custom-root bone as a deform bone so its motion survives a deform-only
    export (restored afterwards). ``interpolation`` (BEZIER/LINEAR/CONSTANT)
    rewrites the exported action's keyframe interpolation for engines that need
    stepped/linear curves. ``t_pose`` (default: the profile's ``t_pose``)
    exports a copy whose rest is a T-pose — arms horizontal, legs straight —
    for targets that expect one (Unity humanoid, VRChat); the rest pose only,
    no animation.
    """
    import bpy
    from boneforge.io_hub import profiles as _profiles
    if action_mode == 'ALL' and bone_naming != 'NONE':
        return False, "Choose Active Action or No Animation for bone naming presets; All Actions requires original names"
    profile = _profiles.get_profile(profile_id)
    armature = context.active_object
    if armature is not None and armature.type != 'ARMATURE':
        for ob in context.selected_objects:
            if ob.type == 'ARMATURE':
                armature = ob
                break

    if interpolation != 'BEZIER' and armature is not None \
            and armature.animation_data and armature.animation_data.action:
        set_action_interpolation(armature.animation_data.action, interpolation)

    restore_root = None
    if root_motion and profile.get("root_motion") and profile.get("custom_root") \
            and armature is not None:
        root_bone = armature.data.bones.get(profile["custom_root"])
        if root_bone is not None and not root_bone.use_deform:
            root_bone.use_deform = True       # include root in deform-only export
            restore_root = root_bone

    if t_pose is None:
        t_pose = bool(profile.get("t_pose", False))
    tpose_state = None
    prev_sel = list(context.selected_objects)
    prev_active = context.view_layer.objects.active
    if t_pose and armature is not None:
        from boneforge.io_hub import tpose
        meshes = _deformed_meshes(context, armature)
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        arm2, copies, _moved = tpose.make_tpose_copies(armature, meshes, context)
        tpose_state = (armature, meshes, arm2, copies)
        for o in context.view_layer.objects:
            o.select_set(False)
        for o in [arm2] + copies:
            o.select_set(True)
        context.view_layer.objects.active = arm2
        action_mode = 'NONE'

    try:
        from boneforge.io_hub.bone_naming import export_copies
        with export_copies(context, context.selected_objects, bone_naming):
            if profile["container"] == 'FBX':
                kwargs = profile_to_fbx_kwargs(profile)
                kwargs.update(resolve_action_kwargs(action_mode))
                bpy.ops.export_scene.fbx(filepath=filepath, use_selection=True,
                                         **kwargs)
            else:
                kwargs = profile_to_gltf_kwargs(profile)
                if action_mode == 'NONE':
                    kwargs["export_animations"] = False
                bpy.ops.export_scene.gltf(filepath=filepath, use_selection=True,
                                          **kwargs)
    except Exception as exc:
        return False, "Export failed: %s" % exc
    finally:
        if restore_root is not None:
            restore_root.use_deform = False
        if tpose_state is not None:
            from boneforge.io_hub import tpose
            tpose.remove_tpose_copies(*tpose_state)
            for o in prev_sel:
                o.select_set(True)
            context.view_layer.objects.active = prev_active
    return True, "Exported %s (%s)%s" % (profile["name"], profile["container"],
                                         ", T-pose" if t_pose else "")


# ── operators ─────────────────────────────────────────────────

def _register():
    import bpy
    from boneforge.io_hub.bone_naming import naming_items
    from bpy_extras.io_utils import ExportHelper

    def _profile_items(self, context):
        from boneforge.io_hub import profiles as _profiles
        return [(pid, _profiles.get_profile(pid)["name"], "")
                for pid in _profiles.available_profiles()]

    class BONEFORGE_PG_ProfileFinding(bpy.types.PropertyGroup):
        """WindowManager storage row for one profile export check finding."""
        check_name: bpy.props.StringProperty(name="Check", default="")
        status: bpy.props.StringProperty(name="Status", default="")
        bone_name: bpy.props.StringProperty(name="Bone", default="")
        message: bpy.props.StringProperty(name="Message", default="")
        fix_operator: bpy.props.StringProperty(name="Fix Operator", default="")

    class BONEFORGE_UL_ProfileFindings(bpy.types.UIList):
        """UIList for profile export check findings."""

        def draw_item(self, context, layout, data, item, icon,
                      active_data, active_propname, index):
            icons = {
                'pass': 'CHECKMARK',
                'warn': 'INFO',
                'fail': 'ERROR',
            }
            row = layout.row(align=True)
            row.label(text="[%s]" % item.check_name,
                      icon=icons.get(item.status, 'QUESTION'))
            row.label(text=item.message)
            if item.bone_name:
                try:
                    props = row.operator("boneforge.select_validation_bone",
                                         text="", icon='RESTRICT_SELECT_OFF')
                    props.bone_name = item.bone_name
                except Exception:
                    row.label(text="", icon='BONE_DATA')
            if item.fix_operator:
                try:
                    row.operator(item.fix_operator, text="Fix",
                                 icon='TOOL_SETTINGS')
                except Exception:
                    row.label(text="Fix unavailable", icon='INFO')

    def _store_profile_findings(context, findings):
        coll = context.window_manager.boneforge_profile_findings
        coll.clear()
        for finding in findings:
            item = coll.add()
            item.check_name = finding.get("check", "") or ""
            item.status = finding.get("status", "") or ""
            item.bone_name = finding.get("bone", "") or ""
            item.message = finding.get("message", "") or ""
            item.fix_operator = finding.get("fix", "") or ""
        context.window_manager.boneforge_profile_finding_index = 0

    class BF_OT_ProfileExport(bpy.types.Operator, ExportHelper):
        """Export the selected rig using a game-engine export profile"""
        bl_idname = "boneforge.profile_export"
        bl_label = "Export (Profile)"
        bl_options = {'REGISTER'}
        filename_ext = ""

        profile_id: bpy.props.EnumProperty(description='Game engine or platform the export is set up for', name="Profile", items=_profile_items)
        action_mode: bpy.props.EnumProperty(description='Which animation to export with the rig', name="Animation", items=ACTION_MODES,
                                            default='ACTIVE')
        bone_naming: bpy.props.EnumProperty(
            name="Bone Names", items=naming_items, default=0,
            description="Bone naming preset for export copies only")
        root_motion: bpy.props.BoolProperty(description="Export the root bone's movement as root motion", name="Root Motion", default=False)
        interpolation: bpy.props.EnumProperty(description='How the exported keys blend from one to the next', name="Interpolation",
                                              items=INTERP_MODES, default='BEZIER')
        t_pose: bpy.props.EnumProperty(description='Export the rest pose as a T-pose or as modelled',
            name="T-Pose", default='PROFILE',
            items=(('PROFILE', "Profile default", "T-pose for Unity humanoid and VRChat, as modelled otherwise"),
                   ('ON', "Export in T-pose", "Arms horizontal, legs straight (rest pose only, no animation)"),
                   ('OFF', "Export as modelled", "Keep the modelled rest pose (e.g. A-pose)")))
        filter_glob: bpy.props.StringProperty(default="*.fbx;*.glb",
                                              options={'HIDDEN'})

        @classmethod
        def poll(cls, context):
            return any(o.type == 'ARMATURE' for o in context.selected_objects) \
                or (context.active_object is not None
                    and context.active_object.type in {'ARMATURE', 'MESH'})

        def execute(self, context):
            from boneforge import bfa_guard
            bfa_guard.require_bforartists("profile_export")
            ok, msg = export_with_profile(context, self.profile_id,
                                          self.filepath, self.action_mode,
                                          self.root_motion, self.interpolation,
                                          None if self.t_pose == 'PROFILE'
                                          else self.t_pose == 'ON', bone_naming=self.bone_naming)
            self.report({'INFO'} if ok else {'ERROR'}, msg)
            return {'FINISHED'} if ok else {'CANCELLED'}

    class BF_OT_ProfileCheck(bpy.types.Operator):
        """Run the selected profile's rig checks on the active armature"""
        bl_idname = "boneforge.profile_check"
        bl_label = "Check for Export"
        bl_options = {'REGISTER'}

        profile_id: bpy.props.EnumProperty(options={'HIDDEN', 'SKIP_SAVE'}, name="Profile", items=_profile_items)

        @classmethod
        def poll(cls, context):
            obj = context.active_object
            return obj is not None and obj.type == 'ARMATURE'

        def execute(self, context):
            findings = run_profile_checks(context.active_object, self.profile_id)
            _store_profile_findings(context, findings)
            bad = [f for f in findings if f["status"] in ("warn", "fail")]
            if bad:
                self.report({'WARNING'},
                            "%d issue(s) for %s — review before export"
                            % (len(bad), self.profile_id))
            else:
                self.report({'INFO'}, "Rig passes %s checks" % self.profile_id)
            return {'FINISHED'}

    class BF_OT_ApplyTransformsFix(bpy.types.Operator):
        """Explicit fix: apply object transforms so the export scale is clean"""
        bl_idname = "boneforge.export_fix_apply_transforms"
        bl_label = "Apply Transforms (Fix)"
        bl_options = {'REGISTER', 'UNDO'}

        @classmethod
        def poll(cls, context):
            return context.active_object is not None

        def execute(self, context):
            try:
                bpy.ops.object.transform_apply(location=False, rotation=True,
                                               scale=True)
            except Exception as exc:
                self.report({'ERROR'}, "Could not apply transforms: %s" % exc)
                return {'CANCELLED'}
            self.report({'INFO'}, "Applied rotation + scale")
            return {'FINISHED'}

    class BONEFORGE_PT_profile_export(bpy.types.Panel):
        """Game-export profile: rig-check, explicit fixes, and export."""
        bl_idname = "BONEFORGE_PT_profile_export"
        bl_label = " "
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = "CATS"
        bl_parent_id = "BF_PT_sb_io"
        bl_order = 48
        bl_options = {'DEFAULT_CLOSED'}

        def draw_header(self, context):
            self.layout.label(text="Game Export")

        @classmethod
        def poll(cls, context):
            # Show, don't hide: when the requirement fails, draw() says what to select.
            return True

        def draw(self, context):
            if not (context.active_object is not None and context.active_object.type == 'ARMATURE'):
                from boneforge.core import needs
                needs.draw(self.layout, context, 'Game Export needs an armature selected.', ('ARMATURE',))
                return
            layout = self.layout
            wm = context.window_manager
            layout.label(text="Validate before export:", icon='CHECKMARK')
            layout.operator("boneforge.profile_check", icon='VIEWZOOM')

            if hasattr(wm, 'boneforge_profile_findings'):
                results = wm.boneforge_profile_findings
                fail_count = sum(1 for r in results if r.status == 'fail')
                warn_count = sum(1 for r in results if r.status == 'warn')
                if fail_count:
                    layout.label(text="FAIL: %d" % fail_count, icon='ERROR')
                if warn_count:
                    layout.label(text="WARN: %d" % warn_count, icon='INFO')
                if results and not fail_count and not warn_count:
                    layout.label(text="All profile checks passed", icon='CHECKMARK')
                if results:
                    layout.template_list(
                        "BONEFORGE_UL_ProfileFindings",
                        "profile_findings",
                        wm,
                        "boneforge_profile_findings",
                        wm,
                        "boneforge_profile_finding_index",
                        rows=5,
                    )
                else:
                    layout.label(text="No profile check results yet", icon='INFO')

            layout.separator(factor=0.5)
            box = layout.box()
            box.label(text="Explicit fixes (never silent):")
            box.operator("boneforge.export_fix_apply_transforms",
                         icon='APPLYALL')
            layout.separator(factor=0.5)
            op = layout.operator("boneforge.profile_export", icon='EXPORT')
            op.bone_naming = context.scene.boneforge_game_export_settings.bone_naming

    return (BONEFORGE_PG_ProfileFinding, BONEFORGE_UL_ProfileFindings,
            BF_OT_ProfileExport, BF_OT_ProfileCheck, BF_OT_ApplyTransformsFix,
            BONEFORGE_PT_profile_export)


_classes = ()


def _profile_finding_class():
    for cls in _classes:
        if cls.__name__ == "BONEFORGE_PG_ProfileFinding":
            return cls
    return None


def _init_properties():
    import bpy
    finding_cls = _profile_finding_class()
    if finding_cls is None:
        return
    bpy.types.WindowManager.boneforge_profile_findings = \
        bpy.props.CollectionProperty(
            type=finding_cls,
            description="Profile export check findings",
        )
    bpy.types.WindowManager.boneforge_profile_finding_index = \
        bpy.props.IntProperty(name="Profile Finding Index", default=0)


def _clear_properties():
    import bpy
    if hasattr(bpy.types.WindowManager, 'boneforge_profile_findings'):
        del bpy.types.WindowManager.boneforge_profile_findings
    if hasattr(bpy.types.WindowManager, 'boneforge_profile_finding_index'):
        del bpy.types.WindowManager.boneforge_profile_finding_index


def register():
    import bpy
    global _classes
    _classes = _register()
    for cls in _classes:
        bpy.utils.register_class(cls)
    _init_properties()


def unregister():
    import bpy
    _clear_properties()
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
