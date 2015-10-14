# ##### BEGIN GPL LICENSE BLOCK #####
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

bl_info = {
    "name": "Powerlib",
    "description": "Control panel for managing "
    "groups contained in linked libraries",
    "author": "Olivier Amrein, Francesco Siddi",
    "version": (0, 5),
    "blender": (2, 53, 0),
    "location": "Properties Panel",
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Object/PowerLib",
    "tracker_url": "https://developer.blender.org/T31475",
    "category": "3D View"}


import bpy
from bpy.props import (FloatProperty, BoolProperty,
FloatVectorProperty, StringProperty, EnumProperty)

#  Generic function to toggle across 3 different model resolutions
def SetProxyResolution(elem,target_resolution):

    obj = bpy.data.objects[elem.name]

    try:
       dupgroup_name = obj.dupli_group.name
    except:
        return

    root = dupgroup_name[:-3]
    ext = dupgroup_name[-3:]
    new_group = root + target_resolution

    if ext in {'_hi', '_lo', '_me'}:
        try:
            obj.dupli_group = bpy.data.groups[new_group]
            #print("PowerLib: CHANGE " + str(elem) + " to " + new_group)
        except:
            print ("Group %s not found" % new_group.upper())


class PowerlibPanel(bpy.types.Panel):
    bl_label = "Powerlib"
    bl_idname = "SCENE_PT_powerlib"
    bl_context = "scene"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        object = bpy.context.active_object
        scene = context.scene
        active_subgroup = scene.ActiveSubgroup

        if len(active_subgroup) > 0:
            ob = bpy.data.objects[active_subgroup]
        else:
            ob = bpy.context.active_object

        if ob.dupli_type == 'GROUP':
            group = ob.dupli_group
            group_name = group.name  # set variable for group toggle
            group_objs = bpy.data.groups[group.name].objects
            total_groups = 0

            row = layout.row()
            row.label(" GROUP: " + group.name, icon = 'GROUP')
            active_subgroup = scene.ActiveSubgroup
            if len(active_subgroup) > 0:
                subgroup = row.operator("powerlib.display_subgroup_content",
                text="Back to subgroup", icon='BACK')
                subgroup.item_name = ''

            box = layout.box()

            for elem in group_objs:

                if elem.dupli_group != None:
                    row = box.row()
                    col=row.row()

                    total_groups += 1

                    if (elem.dupli_type == 'GROUP'):
                        subgroup = col.operator("powerlib.toggle_subgroup",
                        text="", icon='RESTRICT_VIEW_OFF', emboss=False)
                        subgroup.display = "NONE"
                        subgroup.item_name = elem.name
                        subgroup.group_name = group.name
                        col.label(elem.name)
                    else:
                        subgroup = col.operator("powerlib.toggle_subgroup",
                        text="", icon='RESTRICT_VIEW_ON', emboss=False)
                        subgroup.display = "GROUP"
                        subgroup.item_name = elem.name
                        subgroup.group_name = group.name
                        col.label(elem.name)

                    if len(bpy.data.groups[elem.dupli_group.name].objects.items()) > 1:
                        subgroup = col.operator("powerlib.display_subgroup_content",
                        text="Explore", icon='GROUP')
                        subgroup.item_name = elem.name
                    else:
                        col.label(text="")

                    resolution = str(elem.dupli_group.name)[-3:]
                    if resolution in {'_hi', '_lo', '_me'}:
                        res = resolution[-2:].upper()

                        subgroup = col.operator("powerlib.toggle_subgroup_res",
                        text=res, icon='FILE_REFRESH')
                        subgroup.item_name = elem.name
                        subgroup.group_name = group.name
                    else:
                        col.label(text="")
                else:
                    pass

            if total_groups == 0 :
                box.label(" No subgroups found in this group",icon="LAYER_USED")
                resolution = str(object.dupli_group.name)[-3:]
                if resolution in {'_hi', '_lo', '_me'}:

                    res = resolution[-2:].upper()

                    subgroup = box.operator("powerlib.toggle_subgroup_res",
                    text=res, icon='FILE_REFRESH')
                    subgroup.item_name = bpy.context.active_object.name
                    subgroup.group_name = group.name
            else:
                row = layout.row(align=True)
                row.label("Total groups: " + str(total_groups))
                box = layout.box()
                row = box.row(align=True)
                group = row.operator("powerlib.toggle_group",
                text="Show All", icon='RESTRICT_VIEW_OFF')
                group.display = "showall"
                group.group_name = group_name

                group = row.operator("powerlib.toggle_group",
                text="Hide All", icon='RESTRICT_VIEW_ON')
                group.display = "hideall"
                group.group_name = group_name

                row = box.row()

                row.label(text="Set all subgroups to: ")

                row = box.row(align=True)

                group = row.operator("powerlib.toggle_group",
                text="Low", icon='MESH_CIRCLE')
                group.display = "low"
                group.group_name = group_name

                group = row.operator("powerlib.toggle_group",
                text="Medium", icon='MESH_UVSPHERE')
                group.display = "medium"
                group.group_name = group_name

                group = row.operator("powerlib.toggle_group",
                text="High", icon='MESH_ICOSPHERE')
                group.display = "high"
                group.group_name = group_name

        else:
            layout.label(" Select a group")


class ToggleSubgroupResolution(bpy.types.Operator):
    bl_idname = "powerlib.toggle_subgroup_res"
    bl_label = "Powerlib Toggle Soubgroup Res"
    bl_description = "Change the resolution of a subgroup"
    item_name = bpy.props.StringProperty()
    group_name = bpy.props.StringProperty()

    def execute(self, context):

        group_name = self.group_name
        item_name = self.item_name

        obj = bpy.data.objects[item_name]

        dupgroup = obj.dupli_group
        dupgroup_name = obj.dupli_group.name

        root = dupgroup_name[:-2]
        ext = dupgroup_name[-2:]

        if (root + 'me') in bpy.data.groups:
            if ext == 'hi':
                new_group = root + "me"
            elif ext == 'me':
                new_group = root + "lo"
            elif ext == 'lo':
                new_group = root + "hi"
            else:
                new_group = dupgroup  # if error, do not change dupligroup
        else:
            if ext == 'hi':
                new_group = root + "lo"
            elif ext == 'lo':
                new_group = root + "hi"
            else:
                new_group = dupgroup  # if error, do not change dupligroup

        if bpy.data.groups[dupgroup_name].library:
            # link needed object
            filepath = bpy.data.groups[dupgroup_name].library.filepath

            print(filepath)
            with bpy.data.libraries.load(filepath,
            link=True) as (data_from, data_to):
                data_to.groups.append(new_group)

        try:
            obj.dupli_group = bpy.data.groups[new_group]
            print("PowerLib: CHANGE " + str(item_name) + " to " + new_group)
        except:
            self.report({'WARNING'}, "Group %s not found" % new_group.upper())

        return {'FINISHED'}


class ToggleAllSubgroups(bpy.types.Operator):
    bl_idname = "powerlib.toggle_group"
    bl_label = "Powerlib Toggle Group"
    bl_description = "Toggle a property for all subgroups"
    display = bpy.props.StringProperty()
    group_name = bpy.props.StringProperty()

    def execute(self, context):

        display = self.display
        grp_name = self.group_name
        group_objs = bpy.data.groups[grp_name].objects

        for elem in group_objs:
            if display == 'showall':
                elem.dupli_type = "GROUP"
                #print("Powerlib: SHOW " + elem.name)
            elif display == 'hideall':
                elem.dupli_type = "NONE"
                #print("Powerlib: HIDE " + elem.name)
            if display == 'low':
                #print("Powerlib: ALL LOW " + elem.name)
                SetProxyResolution(elem,'_lo')
            elif display == 'medium':
                #print("Powerlib: ALL MEDIUM " + elem.name)
                SetProxyResolution(elem,'_me')
            elif display == 'high':
                #print("Powerlib: ALL HIGH " + elem.name)
                SetProxyResolution(elem,'_hi')
            else:
                print("nothing")

        return {'FINISHED'}


class ToggleSubgroupDisplay(bpy.types.Operator):
    bl_idname = "powerlib.toggle_subgroup"
    bl_label = "Powelib Toggle Subgroup"
    bl_description = "Toggle the display of a subgroup"
    display = bpy.props.StringProperty()
    item_name = bpy.props.StringProperty()
    group_name = bpy.props.StringProperty()

    def execute(self, context):

        display = self.display
        obj_name = self.item_name
        grp_name = self.group_name

        print("Powerlib: " + obj_name + " is being set to " + display)

        bpy.data.groups[grp_name].objects[obj_name].dupli_type = display
        return {'FINISHED'}


class DisplaySubgroupContent(bpy.types.Operator):
    bl_idname = "powerlib.display_subgroup_content"
    bl_label = "Powerlib Display Subgroup Content"
    bl_description = "Display the content of a subgroup"

    item_name = bpy.props.StringProperty()

    def execute(self, context):
        scene = context.scene
        scene.ActiveSubgroup = self.item_name
        return {'FINISHED'}


def register():
    bpy.types.Scene.ActiveSubgroup = StringProperty(
            name="Commit untracked",
            default="",
            description="Add untracked files into svn and commit all of them")
    bpy.utils.register_class(DisplaySubgroupContent)
    bpy.utils.register_class(ToggleSubgroupResolution)
    bpy.utils.register_class(ToggleAllSubgroups)
    bpy.utils.register_class(ToggleSubgroupDisplay)
    bpy.utils.register_class(PowerlibPanel)

def unregister():
    del bpy.types.Scene.ActiveSubgroup
    bpy.utils.unregister_class(DisplaySubgroupContent)
    bpy.utils.unregister_class(ToggleSubgroupResolution)
    bpy.utils.unregister_class(ToggleAllSubgroups)
    bpy.utils.unregister_class(ToggleSubgroupDisplay)
    bpy.utils.unregister_class(PowerlibPanel)

if __name__ == "__main__":
    register()
