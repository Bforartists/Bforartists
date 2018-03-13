# ##### BEGIN GPL LICENSE BLOCK #####
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENCE BLOCK #####

bl_info = {
    "name": "Bone Selection Sets",
    "author": "Inês Almeida, Sybren A. Stüvel, Antony Riakiotakis, Dan Eicher",
    "version": (2, 1, 0),
    "blender": (2, 75, 0),
    "location": "Properties > Object Data (Armature) > Selection Sets",
    "description": "List of Bone sets for easy selection while animating",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Animation/SelectionSets",
    "category": "Animation",
}

import bpy
from bpy.types import (
    Operator,
    Menu,
    Panel,
    UIList,
    PropertyGroup,
)
from bpy.props import (
    StringProperty,
    IntProperty,
    EnumProperty,
    CollectionProperty,
)


# Data Structure ##############################################################

# Note: bones are stored by name, this means that if the bone is renamed,
# there can be problems. However, bone renaming is unlikely during animation
class SelectionEntry(PropertyGroup):
    name = StringProperty(name="Bone Name")


class SelectionSet(PropertyGroup):
    name = StringProperty(name="Set Name")
    bone_ids = CollectionProperty(type=SelectionEntry)


# UI Panel w/ UIList ##########################################################

class POSE_MT_selection_sets_specials(Menu):
    bl_label = "Selection Sets Specials"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.selection_set_delete_all", icon='X')
        layout.operator("pose.selection_set_remove_bones", icon='X')
        layout.operator("pose.selection_set_copy", icon='COPYDOWN')
        layout.operator("pose.selection_set_paste", icon='PASTEDOWN')


class POSE_PT_selection_sets(Panel):
    bl_label = "Selection Sets"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return (context.object and
                context.object.type == 'ARMATURE' and
                context.object.pose)

    def draw(self, context):
        layout = self.layout

        arm = context.object

        row = layout.row()
        row.enabled = (context.mode == 'POSE')

        # UI list
        rows = 4 if len(arm.selection_sets) > 0 else 1
        row.template_list(
            "POSE_UL_selection_set", "",  # type and unique id
            arm, "selection_sets",  # pointer to the CollectionProperty
            arm, "active_selection_set",  # pointer to the active identifier
            rows=rows
        )

        # add/remove/specials UI list Menu
        col = row.column(align=True)
        col.operator("pose.selection_set_add", icon='ZOOMIN', text="")
        col.operator("pose.selection_set_remove", icon='ZOOMOUT', text="")
        col.menu("POSE_MT_selection_sets_specials", icon='DOWNARROW_HLT', text="")

        # move up/down arrows
        if len(arm.selection_sets) > 0:
            col.separator()
            col.operator("pose.selection_set_move", icon='TRIA_UP', text="").direction = 'UP'
            col.operator("pose.selection_set_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        # buttons
        row = layout.row()

        sub = row.row(align=True)
        sub.operator("pose.selection_set_assign", text="Assign")
        sub.operator("pose.selection_set_unassign", text="Remove")

        sub = row.row(align=True)
        sub.operator("pose.selection_set_select", text="Select")
        sub.operator("pose.selection_set_deselect", text="Deselect")


class POSE_UL_selection_set(UIList):
    def draw_item(self, context, layout, data, set, icon, active_data, active_propname, index):
        layout.prop(set, "name", text="", icon='GROUP_BONE', emboss=False)


class POSE_MT_create_new_selection_set(Menu):
    bl_label = "Choose Selection Set"

    def draw(self, context):
        layout = self.layout
        layout.operator("pose.selection_set_add_and_assign",
                        text="New Selection Set")


class POSE_MT_selection_sets(Menu):
    bl_label = 'Select Selection Set'

    @classmethod
    def poll(cls, context):
        return POSE_OT_selection_set_select.poll(context)

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_DEFAULT'
        for idx, sel_set in enumerate(context.object.selection_sets):
            props = layout.operator(POSE_OT_selection_set_select.bl_idname, text=sel_set.name)
            props.selection_set_index = idx


# Operators ###################################################################

class PluginOperator(Operator):
    @classmethod
    def poll(cls, context):
        return (context.object and
                context.object.type == 'ARMATURE' and
                context.mode == 'POSE')


class NeedSelSetPluginOperator(PluginOperator):
    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False
        arm = context.object
        return 0 <= arm.active_selection_set < len(arm.selection_sets)


class POSE_OT_selection_set_delete_all(PluginOperator):
    bl_idname = "pose.selection_set_delete_all"
    bl_label = "Delete All Sets"
    bl_description = "Deletes All Selection Sets"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        arm = context.object
        arm.selection_sets.clear()
        return {'FINISHED'}


class POSE_OT_selection_set_remove_bones(PluginOperator):
    bl_idname = "pose.selection_set_remove_bones"
    bl_label = "Remove Bones from Sets"
    bl_description = "Removes the Active Bones from All Sets"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        arm = context.object

        # iterate only the selected bones in current pose that are not hidden
        for bone in context.selected_pose_bones:
            for selset in arm.selection_sets:
                if bone.name in selset.bone_ids:
                    idx = selset.bone_ids.find(bone.name)
                    selset.bone_ids.remove(idx)

        return {'FINISHED'}


class POSE_OT_selection_set_move(NeedSelSetPluginOperator):
    bl_idname = "pose.selection_set_move"
    bl_label = "Move Selection Set in List"
    bl_description = "Move the active Selection Set up/down the list of sets"
    bl_options = {'UNDO', 'REGISTER'}

    direction = EnumProperty(
        name="Move Direction",
        description="Direction to move the active Selection Set: UP (default) or DOWN",
        items=[
            ('UP', "Up", "", -1),
            ('DOWN', "Down", "", 1),
        ],
        default='UP'
    )

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False
        arm = context.object
        return len(arm.selection_sets) > 1

    def execute(self, context):
        arm = context.object

        active_idx = arm.active_selection_set
        new_idx = active_idx + (-1 if self.direction == 'UP' else 1)

        if new_idx < 0 or new_idx >= len(arm.selection_sets):
            return {'FINISHED'}

        arm.selection_sets.move(active_idx, new_idx)
        arm.active_selection_set = new_idx

        return {'FINISHED'}


class POSE_OT_selection_set_add(PluginOperator):
    bl_idname = "pose.selection_set_add"
    bl_label = "Create Selection Set"
    bl_description = "Creates a new empty Selection Set"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        arm = context.object
        sel_sets = arm.selection_sets
        new_sel_set = sel_sets.add()
        new_sel_set.name = uniqify("SelectionSet", sel_sets.keys())

        # select newly created set
        arm.active_selection_set = len(sel_sets) - 1

        return {'FINISHED'}


class POSE_OT_selection_set_remove(NeedSelSetPluginOperator):
    bl_idname = "pose.selection_set_remove"
    bl_label = "Delete Selection Set"
    bl_description = "Delete a Selection Set"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        arm = context.object

        arm.selection_sets.remove(arm.active_selection_set)

        # change currently active selection set
        numsets = len(arm.selection_sets)
        if (arm.active_selection_set > (numsets - 1) and numsets > 0):
            arm.active_selection_set = len(arm.selection_sets) - 1

        return {'FINISHED'}


class POSE_OT_selection_set_assign(PluginOperator):
    bl_idname = "pose.selection_set_assign"
    bl_label = "Add Bones to Selection Set"
    bl_description = "Add selected bones to Selection Set"
    bl_options = {'UNDO', 'REGISTER'}

    def invoke(self, context, event):
        arm = context.object

        if not (arm.active_selection_set < len(arm.selection_sets)):
            bpy.ops.wm.call_menu("INVOKE_DEFAULT",
                                 name="POSE_MT_selection_set_create")
        else:
            bpy.ops.pose.selection_set_assign('EXEC_DEFAULT')

        return {'FINISHED'}

    def execute(self, context):
        arm = context.object
        act_sel_set = arm.selection_sets[arm.active_selection_set]

        # iterate only the selected bones in current pose that are not hidden
        for bone in context.selected_pose_bones:
            if bone.name not in act_sel_set.bone_ids:
                bone_id = act_sel_set.bone_ids.add()
                bone_id.name = bone.name

        return {'FINISHED'}


class POSE_OT_selection_set_unassign(NeedSelSetPluginOperator):
    bl_idname = "pose.selection_set_unassign"
    bl_label = "Remove Bones from Selection Set"
    bl_description = "Remove selected bones from Selection Set"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        arm = context.object
        act_sel_set = arm.selection_sets[arm.active_selection_set]

        # iterate only the selected bones in current pose that are not hidden
        for bone in context.selected_pose_bones:
            if bone.name in act_sel_set.bone_ids:
                idx = act_sel_set.bone_ids.find(bone.name)
                act_sel_set.bone_ids.remove(idx)

        return {'FINISHED'}


class POSE_OT_selection_set_select(NeedSelSetPluginOperator):
    bl_idname = "pose.selection_set_select"
    bl_label = "Select Selection Set"
    bl_description = "Add Selection Set bones to current selection"
    bl_options = {'UNDO', 'REGISTER'}

    selection_set_index = IntProperty(
        name='Selection Set Index',
        default=-1,
        description='Which Selection Set to select; -1 uses the active Selection Set')

    def execute(self, context):
        arm = context.object

        if self.selection_set_index == -1:
            idx = arm.active_selection_set
        else:
            idx = self.selection_set_index
        sel_set = arm.selection_sets[idx]

        for bone in context.visible_pose_bones:
            if bone.name in sel_set.bone_ids:
                bone.bone.select = True

        return {'FINISHED'}


class POSE_OT_selection_set_deselect(NeedSelSetPluginOperator):
    bl_idname = "pose.selection_set_deselect"
    bl_label = "Deselect Selection Set"
    bl_description = "Remove Selection Set bones from current selection"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        arm = context.object
        act_sel_set = arm.selection_sets[arm.active_selection_set]

        for bone in context.selected_pose_bones:
            if bone.name in act_sel_set.bone_ids:
                bone.bone.select = False

        return {'FINISHED'}


class POSE_OT_selection_set_add_and_assign(PluginOperator):
    bl_idname = "pose.selection_set_add_and_assign"
    bl_label = "Create and Add Bones to Selection Set"
    bl_description = "Creates a new Selection Set with the currently selected bones"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        bpy.ops.pose.selection_set_add('EXEC_DEFAULT')
        bpy.ops.pose.selection_set_assign('EXEC_DEFAULT')
        return {'FINISHED'}


class POSE_OT_selection_set_copy(NeedSelSetPluginOperator):
    bl_idname = "pose.selection_set_copy"
    bl_label = "Copy Selection Set to Clipboard"
    bl_description = "Converts the Selection Set to JSON and places it on the clipboard"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        context.window_manager.clipboard = to_json(context)
        self.report({'INFO'}, 'Copied Selection Set to Clipboard')
        return {'FINISHED'}


class POSE_OT_selection_set_paste(PluginOperator):
    bl_idname = "pose.selection_set_paste"
    bl_label = "Paste Selection Set from Clipboard"
    bl_description = "Adds a new Selection Set from copied JSON on the clipboard"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        import json

        try:
            from_json(context, context.window_manager.clipboard)
        except (json.JSONDecodeError, KeyError):
            self.report({'ERROR'}, 'The clipboard does not contain a Selection Set')
        else:
            # Select the pasted Selection Set.
            context.object.active_selection_set = len(context.object.selection_sets) - 1

        return {'FINISHED'}


# Registry ####################################################################

classes = (
    POSE_MT_create_new_selection_set,
    POSE_MT_selection_sets_specials,
    POSE_MT_selection_sets,
    POSE_PT_selection_sets,
    POSE_UL_selection_set,
    SelectionEntry,
    SelectionSet,
    POSE_OT_selection_set_delete_all,
    POSE_OT_selection_set_remove_bones,
    POSE_OT_selection_set_move,
    POSE_OT_selection_set_add,
    POSE_OT_selection_set_remove,
    POSE_OT_selection_set_assign,
    POSE_OT_selection_set_unassign,
    POSE_OT_selection_set_select,
    POSE_OT_selection_set_deselect,
    POSE_OT_selection_set_add_and_assign,
    POSE_OT_selection_set_copy,
    POSE_OT_selection_set_paste,
)


def add_sss_button(self, context):
    self.layout.menu('POSE_MT_selection_sets')


def to_json(context) -> str:
    """Convert the active bone selection set of the current rig to JSON."""
    import json

    arm = context.object
    active_idx = arm.active_selection_set
    sel_set = arm.selection_sets[active_idx]

    return json.dumps({
        'name': sel_set.name,
        'bones': [bone_id.name for bone_id in sel_set.bone_ids]
    })


def from_json(context, as_json: str):
    """Add the single bone selection set from JSON to the current rig."""
    import json

    sel_set = json.loads(as_json)

    sel_sets = context.object.selection_sets
    new_sel_set = sel_sets.add()
    new_sel_set.name = uniqify(sel_set['name'], sel_sets.keys())

    for bone_name in sel_set['bones']:
        bone_id = new_sel_set.bone_ids.add()
        bone_id.name = bone_name


def uniqify(name: str, other_names: list) -> str:
    """Return a unique name with .xxx suffix if necessary.

    >>> uniqify('hey', ['there'])
    'hey'
    >>> uniqify('hey', ['hey.001', 'hey.005'])
    'hey'
    >>> uniqify('hey', ['hey', 'hey.001', 'hey.005'])
    'hey.002'
    >>> uniqify('hey', ['hey', 'hey.005', 'hey.001'])
    'hey.002'
    >>> uniqify('hey', ['hey', 'hey.005', 'hey.001', 'hey.left'])
    'hey.002'
    >>> uniqify('hey', ['hey', 'hey.001', 'hey.002'])
    'hey.003'

    It also works with a dict_keys object:
    >>> uniqify('hey', {'hey': 1, 'hey.005': 1, 'hey.001': 1}.keys())
    'hey.002'
    """

    if name not in other_names:
        return name

    # Construct the list of numbers already in use.
    offset = len(name) + 1
    others = (n[offset:] for n in other_names
              if n.startswith(name + '.'))
    numbers = sorted(int(suffix) for suffix in others
                     if suffix.isdigit())

    # Find the first unused number.
    min_index = 1
    for num in numbers:
        if min_index < num:
            break
        min_index = num + 1
    return "{}.{:03d}".format(name, min_index)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.selection_sets = CollectionProperty(
        type=SelectionSet,
        name="Selection Sets",
        description="List of groups of bones for easy selection"
    )
    bpy.types.Object.active_selection_set = IntProperty(
        name="Active Selection Set",
        description="Index of the currently active selection set",
        default=0
    )

    wm = bpy.context.window_manager
    km = wm.keyconfigs.active.keymaps['Pose']

    kmi = km.keymap_items.new('wm.call_menu', 'W', 'PRESS', alt=True, shift=True)
    kmi.properties.name = 'POSE_MT_selection_sets'

    bpy.types.VIEW3D_MT_select_pose.append(add_sss_button)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Object.selection_sets
    del bpy.types.Object.active_selection_set


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    register()
