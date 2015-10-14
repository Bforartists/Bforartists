# ***** BEGIN GPL LICENSE BLOCK *****
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
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Bone Selection Groups",
    "author": "Antony Riakiotakis",
    "version": (1, 0, 2),
    "blender": (2, 75, 0),
    "location": "Properties > Object Buttons",
    "description": "Operator and storage for restoration of bone selection state.",
    "category": "Animation",
}

import bpy
from bpy.types import (
    Operator,
    Panel,
    UIList,
)

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    CollectionProperty,
    BoolVectorProperty,
    FloatVectorProperty,
)


class POSE_PT_selection_sets(Panel):
    bl_label = "Selection Sets"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout

        armature = context.object

        # Rig type list
        row = layout.row()
        row.template_list(
            "POSE_UL_selection_set", "",
            armature, "selection_sets",
            armature, "active_selection_set")

        col = row.column()
        colsub = col.column(align=True)
        colsub.operator("pose.selection_set_add", icon='ZOOMIN', text="")
        colsub.operator("pose.selection_set_remove", icon='ZOOMOUT', text="")

        layout.operator("pose.selection_set_toggle")


class POSE_UL_selection_set(UIList):
    def draw_item(self, context, layout, data, set, icon, active_data, active_propname, index):
        layout.prop(set, "name", text="", emboss=False)


class SelectionEntry(bpy.types.PropertyGroup):
    name = StringProperty(name="Bone Name")


class SelectionSet(bpy.types.PropertyGroup):
    name = StringProperty(name="Set Name")
    bone_ids = CollectionProperty(type=SelectionEntry)


class PluginOperator(Operator):
    @classmethod
    def poll(self, context):
        return (context.object and
                context.object.type == 'ARMATURE' and
                context.mode == 'POSE')


class POSE_OT_selection_set_add(PluginOperator):
    bl_idname = "pose.selection_set_add"
    bl_label = "Add Selection Set"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        keep = False
        armature = context.object
        pose = armature.pose

        selection_set = armature.selection_sets.add()
        selection_set.name = "SelectionSet.%d" % len(armature.selection_sets)
        armature.active_selection_set = len(armature.selection_sets) - 1
        for bone in pose.bones:
            if (bone.bone.select):
                bone_id = selection_set.bone_ids.add()
                bone_id.name = bone.name
                keep = True

        if (not keep):
            armature.selection_sets.remove(armature.active_selection_set)
            numsets = len(armature.selection_sets)
            if (armature.active_selection_set > (numsets - 1) and numsets > 0):
                armature.active_selection_set = len(armature.selection_sets) - 1
            return {'CANCELLED'}

        return {'FINISHED'}


class POSE_OT_selection_set_remove(PluginOperator):
    bl_idname = "pose.selection_set_remove"
    bl_label = "Delete Selection Set"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        armature = context.object

        armature.selection_sets.remove(armature.active_selection_set)
        numsets = len(armature.selection_sets)
        if (armature.active_selection_set > (numsets - 1) and numsets > 0):
            armature.active_selection_set = len(armature.selection_sets) - 1
        return {'FINISHED'}


class POSE_OT_selection_set_toggle(PluginOperator):
    bl_idname = "pose.selection_set_toggle"
    bl_label = "Toggle Selection Set"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        armature = context.object
        pose = armature.pose

        selection_set = armature.selection_sets[armature.active_selection_set]
        for bone in pose.bones:
            bone.bone.select = False

        for bone in selection_set.bone_ids:
            pose.bones[bone.name].bone.select = True

        return {'FINISHED'}


class MotionPathsCopyStartFrame(Operator):
    bl_idname = "anim.motionpaths_copy_scene_startframe"
    bl_label = "Copy Scene Start Frame"
    bl_options = {'REGISTER', 'UNDO'}

    armature_paths = BoolProperty()

    @classmethod
    def poll(cls, context):
        return (context.object)

    def execute(self, context):
        avs = None
        motionpath = None
        ob = context.object
        scene = context.scene

        if (self.armature_paths):
            avs = ob.pose.animation_visualization
        else:
            avs = ob.animation_visualization

        preview = scene.use_preview_range

        if (avs):
            motionpath = avs.motion_path

        if (motionpath):
            if (preview):
                motionpath.frame_start = scene.frame_preview_start
                motionpath.frame_end = scene.frame_preview_end
            else:
                motionpath.frame_start = scene.frame_start
                motionpath.frame_end = scene.frame_end
        else:
            return {'CANCELLED'}

        return {'FINISHED'}


classes = (
    POSE_PT_selection_sets,
    POSE_UL_selection_set,
    SelectionEntry,
    SelectionSet,
    POSE_OT_selection_set_add,
    POSE_OT_selection_set_remove,
    POSE_OT_selection_set_toggle,
    MotionPathsCopyStartFrame
)


def copy_frames_armature(self, context):
    layout = self.layout
    layout.operator("anim.motionpaths_copy_scene_startframe").armature_paths = True


def copy_frames_object(self, context):
    layout = self.layout
    layout.operator("anim.motionpaths_copy_scene_startframe").armature_paths = False


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.selection_sets = CollectionProperty(type=SelectionSet)
    bpy.types.Object.active_selection_set = IntProperty()
    bpy.types.DATA_PT_motion_paths.append(copy_frames_armature)
    bpy.types.OBJECT_PT_motion_paths.append(copy_frames_object)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Object.selection_sets
    del bpy.types.Object.active_selection_set


if __name__ == "__main__":
    register()
