"""Import / export of picker layouts as BoneCraft-native JSON."""
import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper

from boneforge.control_ui import layout as _layout
from boneforge.control_ui import picker as _picker


def _active_armature(context):
    obj = context.active_object
    if obj is not None and obj.type == 'ARMATURE':
        return obj
    return None


def _redraw(context):
    if context.area:
        context.area.tag_redraw()


class BF_OT_PickerToggleEdit(bpy.types.Operator):
    """Toggle picker layout edit mode for this rig"""
    bl_idname = "boneforge.picker_toggle_edit"
    bl_label = "Edit Layout"
    bl_options = {'REGISTER', 'UNDO'}

    enabled: bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=True)

    @classmethod
    def poll(cls, context):
        return _active_armature(context) is not None

    def execute(self, context):
        arm = _active_armature(context)
        _picker.set_edit_mode(arm, self.enabled)
        _redraw(context)
        return {'FINISHED'}


class BF_OT_PickerToggleSnap(bpy.types.Operator):
    """Toggle picker layout snap-to-grid for this rig"""
    bl_idname = "boneforge.picker_toggle_snap"
    bl_label = "Snap to Grid"
    bl_options = {'REGISTER', 'UNDO'}

    enabled: bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=True)

    @classmethod
    def poll(cls, context):
        return _active_armature(context) is not None

    def execute(self, context):
        arm = _active_armature(context)
        _picker.set_snap_to_grid(arm, self.enabled)
        _redraw(context)
        return {'FINISHED'}


class BF_OT_PickerMoveControl(bpy.types.Operator):
    """Move a picker control rect in layout JSON"""
    bl_idname = "boneforge.picker_move_control"
    bl_label = "Move Picker Control"
    bl_options = {'REGISTER', 'UNDO'}

    control_id: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    dx: bpy.props.FloatProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=0.0)
    dy: bpy.props.FloatProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=0.0)
    grid: bpy.props.FloatProperty(description='Grid step the control moves in', default=0.25, min=0.01)

    @classmethod
    def poll(cls, context):
        return _active_armature(context) is not None

    def execute(self, context):
        arm = _active_armature(context)
        data = _picker.ensure_layout(arm)
        try:
            edited = _layout.move_control(
                data, self.control_id, self.dx, self.dy,
                snap=_picker.snap_to_grid_enabled(arm),
                grid=self.grid,
            )
        except Exception as exc:
            self.report({'ERROR'}, "Move failed: %s" % exc)
            return {'CANCELLED'}
        _picker.set_layout(arm, edited)
        _redraw(context)
        return {'FINISHED'}


class BF_OT_PickerResizeControl(bpy.types.Operator):
    """Resize a picker control rect in layout JSON"""
    bl_idname = "boneforge.picker_resize_control"
    bl_label = "Resize Picker Control"
    bl_options = {'REGISTER', 'UNDO'}

    control_id: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    dw: bpy.props.FloatProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=0.0)
    dh: bpy.props.FloatProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=0.0)
    grid: bpy.props.FloatProperty(description='Grid step the control resizes in', default=0.25, min=0.01)

    @classmethod
    def poll(cls, context):
        return _active_armature(context) is not None

    def execute(self, context):
        arm = _active_armature(context)
        data = _picker.ensure_layout(arm)
        try:
            edited = _layout.resize_control(
                data, self.control_id, self.dw, self.dh,
                snap=_picker.snap_to_grid_enabled(arm),
                grid=self.grid,
            )
        except Exception as exc:
            self.report({'ERROR'}, "Resize failed: %s" % exc)
            return {'CANCELLED'}
        _picker.set_layout(arm, edited)
        _redraw(context)
        return {'FINISHED'}


class BF_OT_PickerRelabelControl(bpy.types.Operator):
    """Set a picker control display label in layout JSON"""
    bl_idname = "boneforge.picker_relabel_control"
    bl_label = "Relabel Picker Control"
    bl_options = {'REGISTER', 'UNDO'}

    control_id: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    label: bpy.props.StringProperty(description='New label shown on the control', name="Label", default="")

    @classmethod
    def poll(cls, context):
        return _active_armature(context) is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        arm = _active_armature(context)
        data = _picker.ensure_layout(arm)
        try:
            edited = _layout.relabel_control(data, self.control_id, self.label)
        except Exception as exc:
            self.report({'ERROR'}, "Relabel failed: %s" % exc)
            return {'CANCELLED'}
        _picker.set_layout(arm, edited)
        _redraw(context)
        return {'FINISHED'}


class BF_OT_PickerExportLayout(bpy.types.Operator, ExportHelper):
    """Export this rig's picker layout to a BoneCraft JSON file"""
    bl_idname = "boneforge.picker_export_layout"
    bl_label = "Export Picker Layout"
    bl_options = {'REGISTER'}
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'ARMATURE'

    def execute(self, context):
        arm = context.active_object
        data = _picker.ensure_layout(arm)
        try:
            with open(self.filepath, "w", encoding="utf-8") as fh:
                fh.write(_layout.layout_to_json(data))
        except Exception as exc:
            self.report({'ERROR'}, "Export failed: %s" % exc)
            return {'CANCELLED'}
        self.report({'INFO'}, "Exported layout (%d controls)"
                    % len(data.get("controls", [])))
        return {'FINISHED'}


class BF_OT_PickerImportLayout(bpy.types.Operator, ImportHelper):
    """Import a BoneCraft picker layout JSON onto this rig"""
    bl_idname = "boneforge.picker_import_layout"
    bl_label = "Import Picker Layout"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'ARMATURE'

    def execute(self, context):
        from boneforge import bfa_guard
        bfa_guard.require_bforartists("control_ui")
        try:
            with open(self.filepath, encoding="utf-8") as fh:
                data = _layout.layout_from_json(fh.read())
        except Exception as exc:
            self.report({'ERROR'}, "Read failed: %s" % exc)
            return {'CANCELLED'}
        problems = _layout.validate_layout(data)
        if problems:
            self.report({'ERROR'}, "Invalid layout: %s" % problems[0])
            return {'CANCELLED'}
        _picker.set_layout(context.active_object, data)
        if context.area:
            context.area.tag_redraw()
        self.report({'INFO'}, "Imported layout (%d controls)"
                    % len(data.get("controls", [])))
        return {'FINISHED'}


classes = (
    BF_OT_PickerToggleEdit,
    BF_OT_PickerToggleSnap,
    BF_OT_PickerMoveControl,
    BF_OT_PickerResizeControl,
    BF_OT_PickerRelabelControl,
    BF_OT_PickerExportLayout,
    BF_OT_PickerImportLayout,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
