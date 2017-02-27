# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
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

import bpy
from . import library


def initialize_subjects(context):
    """
        Initializes the main object and the subject (actor) list
    """
    cml = context.user_preferences.addons['cmu_mocap_browser'].preferences
    if hasattr(cml, 'initialized'):
        return
    cml.initialized = True
    while cml.subject_list:
        cml.subject_list.remove(0)
    for k, v in library.subjects.items():
        n = cml.subject_list.add()
        n.name = "{:d} - {}".format(k, v['desc'])
        n.idx = k


def update_motions(obj, context):
    """
        Updates the motion list after a subject is selected
    """
    sidx = -1
    if obj.subject_active != -1:
        sidx = obj.subject_list[obj.subject_active].idx
    while obj.motion_list:
        obj.motion_list.remove(0)
    if sidx != -1:
        for k, v in library.subjects[sidx]["motions"].items():
            n = obj.motion_list.add()
            n.name = "{:d} - {}".format(k, v["desc"])
            n.idx = k
        obj.motion_active = -1


class ListItem(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()
    idx = bpy.props.IntProperty()


class CMUMocapLib(bpy.types.AddonPreferences):
    bl_idname = 'cmu_mocap_browser'

    local_storage = bpy.props.StringProperty(
        name="Local Storage",
        subtype='DIR_PATH',
        description="Location to store downloaded resources",
        default="~/cmu_mocap_lib"
        )
    follow_structure = bpy.props.BoolProperty(
        name="Follow Library Folder Structure",
        description="Store resources in subfolders of the local storage",
        default=True
        )
    automatically_import = bpy.props.BoolProperty(
        name="Automatically Import after Download",
        description="Import the resource after the download is finished",
        default=True
        )
    subject_list = bpy.props.CollectionProperty(
        name="subjects", type=ListItem
        )
    subject_active = bpy.props.IntProperty(
        name="subject_idx", default=-1, update=update_motions
        )
    subject_import_name = bpy.props.StringProperty(
        name="Armature Name",
        description="Identifier of the imported subject's armature",
        default="Skeleton"
        )
    motion_list = bpy.props.CollectionProperty(
        name="motions", type=ListItem
        )
    motion_active = bpy.props.IntProperty(
        name="motion_idx", default=-1
        )
    frame_skip = bpy.props.IntProperty(
        # usually the sample rate is 120, so the default 4 gives you 30fps
        name="Fps Divisor", default=4,
        description="Frame supersampling factor", min=1
        )
    cloud_scale = bpy.props.FloatProperty(
        name="Marker Cloud Scale",
        description="Scale the marker cloud by this value",
        default=1., min=0.0001, max=1000000.0,
        soft_min=0.001, soft_max=100.0
        )
    floor = bpy.props.StringProperty(
        name="Floor",
        description="Object to use as floor constraint"
        )
    feet_angle = bpy.props.FloatProperty(
        name="Feet Angle",
        description="Fix for wrong initial feet position",
        default=0
        )

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.url_open",
            text="Carnegie Mellon University Mocap Library",
            icon='URL').url = 'http://mocap.cs.cmu.edu/'
        layout.prop(self, "local_storage")
        layout.prop(self, "follow_structure")
        layout.prop(self, "automatically_import")

