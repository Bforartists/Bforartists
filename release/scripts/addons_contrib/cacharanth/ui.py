### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import bpy, os
from bpy.types import Operator, Panel, UIList
from bpy.props import *
from bpy_extras.io_utils import ImportHelper

from cacharanth import meshcache
from cacharanth.meshcache import MESH_OP_MeshcacheExport, MESH_OP_MeshcacheImport


class MESH_OP_MeshcacheRefresh(Operator):
    """Refresh"""
    bl_idname = "scene.meshcache_refresh"
    bl_label = "Refresh"

    def execute(self, context):
        context.scene.frame_current = context.scene.frame_current
        return {'FINISHED'}


class CACHARANTH_GroupSelect(Operator):
    bl_idname = "cacharanth.group_select"
    bl_label = "Select Group"
    bl_description = "Switch to another material in this mesh"

    def avail_groups(self,context):
        items = [(str(i),x.name,x.name, "GROUP", i) for i,x in enumerate(bpy.data.groups)]
        return items

    group_select = bpy.props.EnumProperty(items = avail_groups, name = "Available Groups")

    @classmethod
    def poll(cls, context):
        return bpy.data.groups

    def execute(self,context):
        bpy.context.scene.meshcache_group = bpy.data.groups[int(self.group_select)].name
        return {'FINISHED'}


def MeshcacheFolderSet(context, filepath):
    import os

    fp =  filepath if os.path.isdir(filepath) else  os.path.dirname(filepath)
    for sc in bpy.data.scenes:
        sc.meshcache_folder = fp
    return {'FINISHED'}


class MeshcacheFolderSetButton(Operator, ImportHelper):
    bl_idname = "buttons.meshcache_folder_set"
    bl_label = "Set Mesh Cache Folder"
    filename_ext = ".mdd"

    def execute(self, context):
        return MeshcacheFolderSet(context, self.filepath)


class MESH_UL_MeshcacheExcludeName(bpy.types.UIList):
    def draw_item(self, context, layout, data, rule, icon, active_data, active_propname, index):
        split = layout.split(0.5)
        row = split.split(align=False)
        row.label(text="%s" % (rule.name))


class MESH_OT_MeshcacheExcludeNameAdd(Operator):
    bl_idname = "buttons.meshcache_exclude_add"
    bl_label = "Add Exclude Rule"
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        rules = scene.meshcache_exclude_names
        rule = rules.add()
        rule.name = "Rule.%.3d" % len(rules)
        scene.meshcache_exclude_names_active_index = len(rules) - 1
        return {'FINISHED'}


class MESH_OT_MeshcacheExcludeNameRemove(Operator):
    bl_idname = "buttons.meshcache_exclude_remove"
    bl_label = "Remove Exclude Rule"
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        rules = scene.meshcache_exclude_names
        rules.remove(scene.meshcache_exclude_names_active_index)
        if scene.meshcache_exclude_names_active_index > len(rules) - 1:
            scene.meshcache_exclude_names_active_index = len(rules) - 1
        return {'FINISHED'}

class MeshcacheExcludeNames(bpy.types.PropertyGroup):
    name = StringProperty(
            name="Rule Name",
            )

class VIEW3D_PT_MeshcacheToolsPanel(Panel):
    """Cacharanth Panel"""
    bl_label = "Cacharanth Tools"
    bl_idname = "VIEW3D_PT_MeshcacheToolsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Cacharanth"

    def draw(self, context):
        layout = self.layout

        scene = bpy.context.scene
        howmany_exported = MESH_OP_MeshcacheExport.howmany_exported
        howmany_exported_excluded = MESH_OP_MeshcacheExport.howmany_excluded
        howmany_imported = MESH_OP_MeshcacheImport.howmany_imported
        howmany_imported_excluded = MESH_OP_MeshcacheImport.howmany_excluded

        row = layout.row(align=True)
        row.prop(scene, "meshcache_apply_to", expand=True)

        if scene.meshcache_apply_to == 'GROUP':
            if bpy.data.groups:
                row = layout.row(align=True)
                row.enabled = len(bpy.data.groups) != 0
                row.label(text="Select Group:")
                row.operator_menu_enum("cacharanth.group_select",
                                               "group_select",
                                               text=scene.meshcache_group,
                                               icon="GROUP")
            else:
                row = layout.row(align=True)
                row.label(text="There are no groups", icon="ERROR")
        else:
            row = layout.row(align=True)
            row.label(text="{0} Selected Objects".format(
                      len(context.selected_objects)))

        row = layout.row(align=True)
        row.prop(scene, "meshcache_folder", text="Export Path")
        row.operator("buttons.meshcache_folder_set", icon='FILESEL', text="")


        row = layout.row(align=True)
        row.label(text="Export Settings:")
        row.prop(scene, "meshcache_frame_start", text="Frame Start")
        row.prop(scene, "meshcache_frame_end", text="Frame End")
        row.prop(scene, "meshcache_frame_rate", text="FPS")

        row = layout.row(align=True)
        row.prop(scene, "use_meshcache_exclude_names",
                 text="Exclude Objects by Name")

        if scene.use_meshcache_exclude_names:
            row = layout.row()
            row.template_list(
                    "MESH_UL_MeshcacheExcludeName", "meshcache_exclude_names",
                    scene, "meshcache_exclude_names",
                    scene, "meshcache_exclude_names_active_index")

            col = row.column()
            colsub = col.column(align=True)
            colsub.operator("buttons.meshcache_exclude_add", icon='ZOOMIN', text="")
            colsub.operator("buttons.meshcache_exclude_remove", icon='ZOOMOUT', text="")

            if scene.meshcache_exclude_names:
                index = scene.meshcache_exclude_names_active_index
                rule = scene.meshcache_exclude_names[index]

                row = layout.row(align=True)
                row.prop(rule, "name", text="Exclude Text")

        layout.separator()

        row = layout.row(align=True)
        row.operator("object.meshcache_import", icon="IMPORT")
        row.operator("object.meshcache_export", icon="EXPORT")
        row.operator("scene.meshcache_refresh", icon="FILE_REFRESH", text="")

        row = layout.row(align=True)
        row.label(text="Export:")
        row.label(text="{0} Exported".format(str(howmany_exported)))
        row.label(text="{0} Excluded".format(str(howmany_exported_excluded)))

        row = layout.row(align=True)
        row.label(text="Import:")
        row.label(text="{0} Imported".format(str(howmany_imported)))
        row.label(text="{0} Excluded".format(str(howmany_imported_excluded)))

classes = (
    VIEW3D_PT_MeshcacheToolsPanel,
    MESH_OP_MeshcacheRefresh,
    MESH_UL_MeshcacheExcludeName,
    MESH_OT_MeshcacheExcludeNameAdd,
    MESH_OT_MeshcacheExcludeNameRemove,
    MeshcacheExcludeNames,
    MeshcacheFolderSetButton,
    CACHARANTH_GroupSelect
    )

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    from bpy.types import Scene

    Scene.meshcache_apply_to = EnumProperty(
            name="Apply To",
            items=(('GROUP', "Group", "Objects in a group"),
                   ('OBJECT', "Selected Objects", "Selected objects only"),
                   ),
            default='OBJECT',
            )

    Scene.meshcache_folder = StringProperty(default="Choose a Path...")
    Scene.meshcache_group = StringProperty(default="Select Group")
    Scene.meshcache_frame_start = IntProperty(default=1,
                                              soft_min=0)
    Scene.meshcache_frame_end = IntProperty(default=1,
                                            soft_min=1)
    Scene.meshcache_frame_rate = IntProperty(default=24,
                                             soft_min=1)

    Scene.use_meshcache_exclude_names = BoolProperty(
                                            default=False,
                                            name="Exclude by Name",
                                            description="Exclude objects with a name including text")
    Scene.meshcache_exclude_names = CollectionProperty(type=MeshcacheExcludeNames)
    Scene.meshcache_exclude_names_active_index = IntProperty()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
