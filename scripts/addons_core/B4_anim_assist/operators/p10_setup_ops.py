"""
P10 Setup Operations — Addon initialization and validation operators.

Operators for safe disable, hotkey conflict checking, first-run setup,
demo configuration loading, debug toggling, and comprehensive validation.
"""

from bpy.types import Operator

from ..core.logging import get_logger
from ..core.p10_audit import log_operation
from ..core.p10_properties import get_p10
from ..core.helpers import report_failure

_log = get_logger(__name__)


class AA_OT_p10_safe_disable(Operator):
    """Safely disable the addon by clearing all state first."""
    bl_idname = "animassist.p10_safe_disable"
    bl_label = "Safe Disable"
    bl_options = {'REGISTER'}

    def execute(self, context):
        """Execute safe disable by running cleanup and clearing state."""
        try:
            # Import here to avoid circular imports
            from ..core import p10_diagnostics

            # Run stale cleanup
            p10_diagnostics.run_stale_cleanup()
            _log.info("Stale cleanup completed")

            # Clear audit state
            try:
                from ..core import p10_audit
                p10_audit.clear_all()
                _log.info("P10 audit state cleared")
            except Exception as e:
                _log.warning(f"Could not clear p10_audit: {e}")

            # Clear recovery state
            try:
                from ..core import p10_recovery
                p10_recovery.clear_snapshots()
                _log.info("P10 recovery state cleared")
            except Exception as e:
                _log.warning(f"Could not clear p10_recovery: {e}")

            # Clear tool registry
            try:
                from ..core import p10_tool_registry
                p10_tool_registry.clear()
                _log.info("P10 tool registry cleared")
            except Exception as e:
                _log.warning(f"Could not clear p10_tool_registry: {e}")

            log_operation("safe_disable", success=True, detail="State cleared")
            self.report({'INFO'}, "Addon cleanup completed. State cleared.")
            return {'FINISHED'}

        except Exception as e:
            _log.error(f"Safe disable failed: {e}", exc_info=True)
            report_failure(self, "Could not disable safely", "Save your file, then disable Anim Assist in Preferences > Add-ons", e)
            return {'CANCELLED'}


class AA_OT_p10_check_hotkey_conflicts(Operator):
    """Check for hotkey conflicts in the registered hotkeys."""
    bl_idname = "animassist.p10_check_hotkey_conflicts"
    bl_label = "Check Hotkey Conflicts"
    bl_options = {'REGISTER'}

    def execute(self, context):
        """Execute hotkey conflict checking."""
        try:
            from ..core.hotkeys import get_manager

            manager = get_manager()
            conflicts = []

            # Check for duplicates in registered hotkeys
            if hasattr(manager, '_registered') and manager._registered:
                key_type_counts = {}
                for entry in manager._registered:
                    key_type = getattr(entry, 'key_type', None)
                    if key_type:
                        if key_type not in key_type_counts:
                            key_type_counts[key_type] = []
                        key_type_counts[key_type].append(entry)

                # Find conflicts (same key_type appearing multiple times)
                for key_type, entries in key_type_counts.items():
                    if len(entries) > 1:
                        conflicts.append(f"{key_type}: {len(entries)} entries")

            if conflicts:
                conflict_str = "; ".join(conflicts)
                _log.warning(f"Hotkey conflicts detected: {conflict_str}")
                self.report({'WARNING'}, f"Hotkey conflicts found: {conflict_str}")
            else:
                _log.info("No hotkey conflicts detected")
                self.report({'INFO'}, "No hotkey conflicts detected")

            log_operation("check_hotkey_conflicts", success=True, detail=f"conflicts_found={len(conflicts)}")
            return {'FINISHED'}

        except Exception as e:
            _log.error(f"Hotkey conflict check failed: {e}", exc_info=True)
            report_failure(self, "Could not check hotkeys", "Restart Bforartists and run First Run Setup again", e)
            return {'CANCELLED'}


class AA_OT_p10_first_run_setup(Operator):
    """Initialize default settings for first-time users."""
    bl_idname = "animassist.p10_first_run_setup"
    bl_label = "First Run Setup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Execute first run setup with sensible defaults."""
        p10 = None
        try:
            p10 = get_p10(context)
            if p10 is None:
                self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
                return {'CANCELLED'}

            from ..core.p10_tool_registry import seed_registered_tools

            tool_count = seed_registered_tools()
            # Repair discovery on repeated setup without resetting the user's
            # chosen settings, favorites or recent tools.
            if not p10.first_run_complete:
                p10.recovery_enabled = True
                p10.max_recents = 20
                p10.audit_enabled = True
                p10.shelf_mode = "COMPACT"
            p10.first_run_complete = True

            _log.info("First run setup completed: %d searchable tools", tool_count)

            log_operation(
                "first_run_setup", success=True,
                detail=f"searchable_tools={tool_count}",
            )

            self.report({'INFO'}, f"Setup complete: {tool_count} tools available in Search")
            return {'FINISHED'}

        except Exception as e:
            if p10 is not None:
                p10.first_run_complete = False
            _log.error(f"First run setup failed: {e}", exc_info=True)
            report_failure(self, "First Run Setup did not finish", "Restart Bforartists and run it again from Properties > Scene > Anim Assist > Setup", e)
            return {'CANCELLED'}


class AA_OT_p10_load_demo_config(Operator):
    """Load a demo configuration for testing purposes."""
    bl_idname = "animassist.p10_load_demo_config"
    bl_label = "Load Demo Config"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Execute demo configuration load."""
        try:
            p10 = get_p10(context)
            if p10 is None:
                self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
                return {'CANCELLED'}

            # Enable debug panel
            p10.show_debug_panel = True
            _log.info("Debug panel enabled")

            # Enable audit
            p10.audit_enabled = True
            _log.info("Audit enabled")

            # Use real tools; the previous sample IDs had no operators.
            from ..core.p10_tool_registry import seed_registered_tools
            tool_count = seed_registered_tools()

            log_operation(
                "load_demo_config", success=True,
                detail=f"debug_panel_enabled=True, audit_enabled=True, searchable_tools={tool_count}",
            )

            self.report({'INFO'}, "Demo configuration loaded successfully")
            return {'FINISHED'}

        except Exception as e:
            _log.error(f"Demo config load failed: {e}", exc_info=True)
            report_failure(self, "Could not load the demo configuration", "Run First Run Setup from Properties > Scene > Anim Assist > Setup instead", e)
            return {'CANCELLED'}


class AA_OT_p10_toggle_debug(Operator):
    """Toggle the debug panel visibility."""
    bl_idname = "animassist.p10_toggle_debug"
    bl_label = "Toggle Debug Panel"
    bl_options = {'REGISTER'}

    def execute(self, context):
        """Execute debug panel toggle."""
        try:
            p10 = get_p10(context)
            if p10 is None:
                self.report({'ERROR'}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
                return {'CANCELLED'}

            # Toggle the debug panel
            new_state = not p10.show_debug_panel
            p10.show_debug_panel = new_state

            state_str = "enabled" if new_state else "disabled"
            _log.info(f"Debug panel {state_str}")

            log_operation("toggle_debug", success=True, detail=f"show_debug_panel={new_state}")

            self.report({'INFO'}, f"Debug panel {state_str}")
            return {'FINISHED'}

        except Exception as e:
            _log.error(f"Debug toggle failed: {e}", exc_info=True)
            report_failure(self, "Debug toggle failed", "Restart Bforartists and run First Run Setup again", e)
            return {'CANCELLED'}


class AA_OT_p10_final_validation(Operator):
    """Run comprehensive validation of all P10 phases and components."""
    bl_idname = "animassist.p10_final_validation"
    bl_label = "Final Validation"
    bl_options = {'REGISTER'}

    def execute(self, context):
        """Execute comprehensive validation."""
        try:
            from ..core import p10_diagnostics

            validation_results = {}
            all_passed = True

            # Validate registration (returns list of issues; empty = pass)
            try:
                reg_issues = p10_diagnostics.validate_registration()
                reg_passed = len(reg_issues) == 0
                validation_results['registration'] = reg_passed
                if not reg_passed:
                    all_passed = False
                _log.info(f"Registration validation: {'PASSED' if reg_passed else 'FAILED — ' + '; '.join(reg_issues)}")
            except Exception as e:
                _log.error(f"Registration validation error: {e}")
                validation_results['registration'] = False
                all_passed = False

            # Run leak check (returns list of warnings; empty = pass)
            try:
                leak_warnings = p10_diagnostics.run_leak_check()
                leak_passed = len(leak_warnings) == 0
                validation_results['leak_check'] = leak_passed
                if not leak_passed:
                    all_passed = False
                _log.info(f"Leak check: {'PASSED' if leak_passed else 'WARNINGS — ' + '; '.join(leak_warnings)}")
            except Exception as e:
                _log.error(f"Leak check error: {e}")
                validation_results['leak_check'] = False
                all_passed = False

            # Check capabilities registry
            try:
                from ..core import capabilities as caps_mod

                cap_dict = caps_mod.get_registry().all_capabilities()
                has_expected = len(cap_dict) > 0
                validation_results['capabilities'] = has_expected
                if not has_expected:
                    all_passed = False
                _log.info(f"Capabilities registry: {len(cap_dict)} entries found")
            except Exception as e:
                _log.error(f"Capabilities check error: {e}")
                validation_results['capabilities'] = False
                all_passed = False

            # Report results
            log_operation(
                "final_validation", success=all_passed,
                detail=(
                    f"registration={validation_results.get('registration', False)}, "
                    f"leak_check={validation_results.get('leak_check', False)}, "
                    f"capabilities={validation_results.get('capabilities', False)}"
                ),
            )

            if all_passed:
                self.report({'INFO'}, "Final validation PASSED: all components healthy")
            else:
                failed_checks = [k for k, v in validation_results.items() if not v]
                self.report({'WARNING'}, f"Final validation FAILED: {', '.join(failed_checks)}")

            return {'FINISHED'}

        except Exception as e:
            _log.error(f"Final validation failed: {e}", exc_info=True)
            report_failure(self, "Final validation error", "Restart Bforartists and run First Run Setup again", e)
            return {'CANCELLED'}


CLASSES = (
    AA_OT_p10_safe_disable,
    AA_OT_p10_check_hotkey_conflicts,
    AA_OT_p10_first_run_setup,
    AA_OT_p10_load_demo_config,
    AA_OT_p10_toggle_debug,
    AA_OT_p10_final_validation,
)
