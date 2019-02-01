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

# <pep8-80 compliant>

# This script was developed with financial support from the Foundation for
# Science and Technology of Portugal, under the grant SFRH/BD/66452/2009.


bl_info = {
    "name": "Carnegie Mellon University Mocap Library Browser",
    "author": "Daniel Monteiro Basso <daniel@basso.inf.br>",
    "version": (2015, 3, 20),
    "blender": (2, 66, 6),
    "location": "View3D > Tools",
    "description": "Assistant for using CMU Motion Capture data",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/3D_interaction/CMU_Mocap_Library_Browser",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Animation"}


if 'bpy' in locals():
    import importlib
    library = importlib.reload(library)
    download = importlib.reload(download)
    makehuman = importlib.reload(makehuman)
    data = importlib.reload(data)
else:
    from . import library
    from . import download
    from . import makehuman
    from . import data

import os
import bpy


class CMUMocapSubjectBrowser(bpy.types.Panel):
    bl_idname = "object.cmu_mocap_subject_browser"
    bl_label = "CMU Mocap Subject Browser"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Animation'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        data.initialize_subjects(context)
        layout = self.layout
        cml = context.preferences.addons['cmu_mocap_browser'].preferences
        layout.template_list("UI_UL_list", "SB", cml, "subject_list",
            cml, "subject_active")
        layout.prop(cml, "subject_import_name")
        if cml.subject_active != -1:
            sidx = cml.subject_list[cml.subject_active].idx
            remote_fname = library.skeleton_url.format(sidx)
            tid = "{0:02d}".format(sidx)
            local_path = os.path.expanduser(cml.local_storage)
            if cml.follow_structure:
                local_path = os.path.join(local_path, tid)
            local_fname = os.path.join(local_path, tid + ".asf")
            do_import = False
            if os.path.exists(local_fname):
                label = "Import Selected"
                do_import = True
            elif cml.automatically_import:
                label = "Download and Import Selected"
            else:
                label = "Download Selected"

            props = layout.operator("mocap.download_import",
                                    text=label, icon='ARMATURE_DATA')
            props.remote_file = remote_fname
            props.local_file = local_fname
            props.do_import = do_import


class CMUMocapMotionBrowser(bpy.types.Panel):
    bl_idname = "object.cmu_mocap_motion_browser"
    bl_label = "CMU Mocap Motion Browser"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Animation'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        cml = context.preferences.addons['cmu_mocap_browser'].preferences
        layout.template_list("UI_UL_list", "MB", cml, "motion_list",
            cml, "motion_active")
        if cml.motion_active == -1:
            return
        sidx = cml.subject_list[cml.subject_active].idx
        midx = cml.motion_list[cml.motion_active].idx
        motion = library.subjects[sidx]['motions'][midx]
        fps = motion['fps']
        ifps = fps // cml.frame_skip
        row = layout.row()
        row.column().label(text="Original: {0:d} fps.".format(fps))
        row.column().label(text="Importing: {0:d} fps.".format(ifps))
        layout.prop(cml, "frame_skip")
        layout.prop(cml, "cloud_scale")
        remote_fname = library.motion_url.format(sidx, midx)
        tid = "{0:02d}".format(sidx)
        local_path = os.path.expanduser(cml.local_storage)
        if cml.follow_structure:
            local_path = os.path.join(local_path, tid)
        for target, icon, ext in (
                ('Motion Data', 'POSE_DATA', 'amc'),
                ('Marker Cloud', 'EMPTY_DATA', 'c3d'),
                ('Movie', 'FILE_MOVIE', 'mpg')):
            action = "Import" if ext != 'mpg' else "Open"
            fname = "{0:02d}_{1:02d}.{2}".format(sidx, midx, ext)
            local_fname = os.path.join(local_path, fname)
            do_import = False
            if os.path.exists(local_fname):
                label = "{0} {1}".format(action, target)
                do_import = True
            elif cml.automatically_import:
                label = "Download and {0} {1}".format(action, target)
            else:
                label = "Download {0}".format(target)
            row = layout.row()
            props = row.operator("mocap.download_import", text=label, icon=icon)
            props.remote_file = remote_fname + ext
            props.local_file = local_fname
            props.do_import = do_import
            row.active = ext in motion['files']


class CMUMocapToMakeHuman(bpy.types.Panel):
    bl_idname = "object.cmu_mocap_makehuman"
    bl_label = "CMU Mocap to MakeHuman"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Animation'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        cml = context.preferences.addons['cmu_mocap_browser'].preferences
        layout.prop_search(cml, "floor", context.scene, "objects")
        layout.prop(cml, "feet_angle")
        layout.operator("object.cmu_align", text='Align armatures')
        layout.operator("object.cmu_transfer", text='Transfer animation')


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
