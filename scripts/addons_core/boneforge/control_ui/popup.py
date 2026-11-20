"""Floating popup picker — the panel's controls in an on-demand dialog."""
import bpy

from boneforge.control_ui import layout as _layout
from boneforge.control_ui import picker as _picker


class BF_OT_PickerPopup(bpy.types.Operator):
    """Open a floating control picker for the active rig"""
    bl_idname = "boneforge.picker_popup"
    bl_label = "Control Picker"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == 'ARMATURE'
                and len(obj.data.collections))

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=320)

    def draw(self, context):
        layout = self.layout
        arm = context.active_object
        data = _picker.ensure_layout(arm)
        groups = {}
        for c in data.get("controls", []):
            groups.setdefault(c.get("group", "Controls"), []).append(c)
        layout.label(text=arm.name, icon='ARMATURE_DATA')
        for group in _layout.PICKER_GROUPS:
            ctrls = groups.get(group)
            if not ctrls:
                continue
            box = layout.box()
            op = box.operator("boneforge.picker_select_group", text=group,
                              icon='GROUP_BONE')
            op.group = group
            grid = box.grid_flow(columns=4, even_columns=True)
            for c in sorted(ctrls, key=lambda x: x["id"]):
                op = grid.operator("boneforge.picker_select",
                                   text=c["id"].replace("-", " "))
                op.bones = c["bone"]
        row = layout.row(align=True)
        row.operator("boneforge.picker_mirror_selection", icon='MOD_MIRROR')
        row.operator("boneforge.picker_add_set", icon='ADD')


classes = (
    BF_OT_PickerPopup,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
