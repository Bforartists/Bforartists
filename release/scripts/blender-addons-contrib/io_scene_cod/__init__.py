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

# <pep8 compliant>

"""
Blender-CoD: Blender Add-On for Call of Duty modding
Version: alpha 3

Copyright (c) 2011 CoDEmanX, Flybynyt -- blender-cod@online.de

http://code.google.com/p/blender-cod/

TODO
- UI for xmodel and xanim import (planned for alpha 4/5)

"""

bl_info = {
    "name": "Blender-CoD - Add-On for Call of Duty modding (alpha 3)",
    "author": "CoDEmanX, Flybynyt",
    "version": (0, 3, 5),
    "blender": (2, 62, 0),
    "location": "File > Import  |  File > Export",
    "description": "Export models to *.XMODEL_EXPORT and animations to *.XANIM_EXPORT",
    "warning": "Alpha version, please report any bugs!",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Import-Export/Call_of_Duty_IO",
    "tracker_url": "https://developer.blender.org/T30482",
    "support": "TESTING",
    "category": "Import-Export"
}

# To support reload properly, try to access a package var, if it's there, reload everything
if "bpy" in locals():
    import imp
    if "import_xmodel" in locals():
        imp.reload(import_xmodel)
    if "export_xmodel" in locals():
        imp.reload(export_xmodel)
    if "import_xanim" in locals():
        imp.reload(import_xanim)
    if "export_xanim" in locals():
        imp.reload(export_xanim)

import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty, StringProperty, EnumProperty
import bpy_extras.io_utils
from bpy_extras.io_utils import ExportHelper, ImportHelper
import time

# Planned for alpha 4/5
class ImportXmodel(bpy.types.Operator, ImportHelper):
    """Load a CoD XMODEL_EXPORT File"""
    bl_idname = "import_scene.xmodel"
    bl_label = "Import XMODEL_EXPORT"
    bl_options = {'PRESET'}

    filename_ext = ".XMODEL_EXPORT"
    filter_glob = StringProperty(default="*.XMODEL_EXPORT", options={'HIDDEN'})

    #use_meshes = BoolProperty(name="Meshes", description="Import meshes", default=True)
    #use_armature = BoolProperty(name="Armature", description="Import Armature", default=True)
    #use_bind_armature = BoolProperty(name="Bind Meshes to Armature", description="Parent imported meshes to armature", default=True)

    #use_split_objects = BoolProperty(name="Object", description="Import OBJ Objects into Blender Objects", default=True)
    #use_split_groups = BoolProperty(name="Group", description="Import OBJ Groups into Blender Objects", default=True)

    #use_image_search = BoolProperty(name="Image Search", description="Search subdirs for any associated images (Warning, may be slow)", default=True)

    def execute(self, context):
        from . import import_xmodel
        start_time = time.clock()
        result = import_xmodel.load(self, context, **self.as_keywords(ignore=("filter_glob", "check_existing")))

        if not result:
            self.report({'INFO'}, "Import finished in %.4f sec." % (time.clock() - start_time))
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, result)
            return {'CANCELLED'}

    """
    def draw(self, context):
        layout = self.layout

        col = layout.column()
        col.prop(self, "use_meshes")
        col.prop(self, "use_armature")

        row = layout.row()
        row.active = self.use_meshes and self.use_armature
        row.prop(self, "use_bind_armature")
    """

    @classmethod
    def poll(self, context):
        return (context.scene is not None)

class ImportXanim(bpy.types.Operator, ImportHelper):
    """Load a CoD XANIM_EXPORT File"""
    bl_idname = "import_scene.xanim"
    bl_label = "Import XANIM_EXPORT"
    bl_options = {'PRESET'}

    filename_ext = ".XANIM_EXPORT"
    filter_glob = StringProperty(default="*.XANIM_EXPORT;*.NT_EXPORT", options={'HIDDEN'})

    def execute(self, context):
        # print("Selected: " + context.active_object.name)
        from . import import_xanim

        return import_xanim.load(self, context, **self.as_keywords(ignore=("filter_glob",)))

class ExportXmodel(bpy.types.Operator, ExportHelper):
    """Save a CoD XMODEL_EXPORT File"""

    bl_idname = "export_scene.xmodel"
    bl_label = 'Export XMODEL_EXPORT'
    bl_options = {'PRESET'}

    filename_ext = ".XMODEL_EXPORT"
    filter_glob = StringProperty(default="*.XMODEL_EXPORT", options={'HIDDEN'})

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    use_version = EnumProperty(
        name="Format Version",
        description="XMODEL_EXPORT format version for export",
        items=(('5', "Version 5", "vCoD, CoD:UO"),
               ('6', "Version 6", "CoD2, CoD4, CoD5, CoD7")),
        default='6',
        )

    use_selection = BoolProperty(
        name="Selection only",
        description="Export selected meshes only (object or weight paint mode)",
        default=False
        )

    use_vertex_colors = BoolProperty(
        name="Vertex colors",
        description="Export vertex colors (if disabled, white color will be used)",
        default=True
        )

    use_vertex_colors_alpha = BoolProperty(
        name="As alpha",
        description="Turn RGB vertex colors into grayscale (average value) and use it as alpha transparency. White is 1 (opaque), black 0 (invisible)",
        default=False
        )

    use_apply_modifiers = BoolProperty(
        name="Apply Modifiers",
        description="Apply all mesh modifiers except Armature (preview resolution)",
        default=True
        )

    use_armature = BoolProperty(
        name="Armature",
        description="Export bones (if disabled, only a 'tag_origin' bone will be written)",
        default=True
        )

    use_vertex_cleanup = BoolProperty(
        name="Clean up vertices",
        description="Try this if you have problems converting to xmodel. Skips vertices which aren't used by any face and updates references.",
        default=False
        )

    use_armature_pose = BoolProperty(
        name="Pose animation to models",
        description="Export meshes with Armature modifier applied as a series of XMODEL_EXPORT files",
        default=False
        )

    use_frame_start = IntProperty(
        name="Start",
        description="First frame to export",
        default=1,
        min=0
        )

    use_frame_end = IntProperty(
        name="End",
        description="Last frame to export",
        default=250,
        min=0
        )

    use_weight_min = BoolProperty(
        name="Minimum bone weight",
        description="Try this if you get 'too small weight' errors when converting",
        default=False,
        )

    use_weight_min_threshold = FloatProperty(
        name="Threshold",
        description="Smallest allowed weight (minimum value)",
        default=0.010097,
        min=0.0,
        max=1.0,
        precision=6
        )

    def execute(self, context):
        from . import export_xmodel
        start_time = time.clock()
        result = export_xmodel.save(self, context, **self.as_keywords(ignore=("filter_glob", "check_existing")))

        if not result:
            self.report({'INFO'}, "Export finished in %.4f sec." % (time.clock() - start_time))
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, result)
            return {'CANCELLED'}

    # Extend ExportHelper invoke function to support dynamic default values
    def invoke(self, context, event):

        #self.use_frame_start = context.scene.frame_start
        self.use_frame_start = context.scene.frame_current

        #self.use_frame_end = context.scene.frame_end
        self.use_frame_end = context.scene.frame_current

        return super().invoke(context, event)

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.prop(self, "use_version", expand=True)

        # Calculate number of selected mesh objects
        if context.mode in {'OBJECT', 'PAINT_WEIGHT'}:
            meshes_selected = len([m for m in bpy.data.objects if m.type == 'MESH' and m.select])
        else:
            meshes_selected = 0

        col = layout.column(align=True)
        col.prop(self, "use_selection", "Selection only (%i meshes)" % meshes_selected)
        col.enabled = bool(meshes_selected)

        col = layout.column(align=True)
        col.prop(self, "use_apply_modifiers")

        col = layout.column(align=True)
        col.enabled = not self.use_armature_pose
        if self.use_armature and self.use_armature_pose:
            col.prop(self, "use_armature", "Armature  (disabled)")
        else:
            col.prop(self, "use_armature")

        if self.use_version == '6':

            row = layout.row(align=True)
            row.prop(self, "use_vertex_colors")

            sub = row.split()
            sub.active = self.use_vertex_colors
            sub.prop(self, "use_vertex_colors_alpha")

        col = layout.column(align=True)
        col.label("Advanced:")

        col = layout.column(align=True)
        col.prop(self, "use_vertex_cleanup")

        box = layout.box()

        col = box.column(align=True)
        col.prop(self, "use_armature_pose")

        sub = box.column()
        sub.active = self.use_armature_pose
        sub.label(text="Frame range: (%i frames)" % (abs(self.use_frame_end - self.use_frame_start) + 1))

        row = sub.row(align=True)
        row.prop(self, "use_frame_start")
        row.prop(self, "use_frame_end")

        box = layout.box()

        col = box.column(align=True)
        col.prop(self, "use_weight_min")

        sub = box.column()
        sub.enabled = self.use_weight_min
        sub.prop(self, "use_weight_min_threshold")

    @classmethod
    def poll(self, context):
        return (context.scene is not None)

class ExportXanim(bpy.types.Operator, ExportHelper):
    """Save a XMODEL_XANIM File"""

    bl_idname = "export_scene.xanim"
    bl_label = 'Export XANIM_EXPORT'
    bl_options = {'PRESET'}

    filename_ext = ".XANIM_EXPORT"
    filter_glob = StringProperty(default="*.XANIM_EXPORT", options={'HIDDEN'})

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    use_selection = BoolProperty(
        name="Selection only",
        description="Export selected bones only (pose mode)",
        default=False
        )

    use_framerate = IntProperty(
        name="Framerate",
        description="Set frames per second for export, 30 fps is commonly used.",
        default=24,
        min=1,
        max=100
        )

    use_frame_start = IntProperty(
        name="Start",
        description="First frame to export",
        default=1,
        min=0
        )

    use_frame_end = IntProperty(
        name="End",
        description="Last frame to export",
        default=250,
        min=0
        )

    use_notetrack = BoolProperty(
        name="Notetrack",
        description="Export timeline markers as notetrack nodes",
        default=True
        )

    use_notetrack_format = EnumProperty(
        name="Notetrack format",
        description="Notetrack format to use. Always set 'CoD 7' for Black Ops, even if not using notetrack!",
        items=(('5', "CoD 5", "Separate NT_EXPORT notetrack file for 'World at War'"),
               ('7', "CoD 7", "Separate NT_EXPORT notetrack file for 'Black Ops'"),
               ('1', "all other", "Inline notetrack data for all CoD versions except WaW and BO")),
        default='1',
        )

    def execute(self, context):
        from . import export_xanim
        start_time = time.clock()
        result = export_xanim.save(self, context, **self.as_keywords(ignore=("filter_glob", "check_existing")))

        if not result:
            self.report({'INFO'}, "Export finished in %.4f sec." % (time.clock() - start_time))
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, result)
            return {'CANCELLED'}

    # Extend ExportHelper invoke function to support dynamic default values
    def invoke(self, context, event):

        self.use_frame_start = context.scene.frame_start
        self.use_frame_end = context.scene.frame_end
        self.use_framerate = round(context.scene.render.fps / context.scene.render.fps_base)

        return super().invoke(context, event)

    def draw(self, context):

        layout = self.layout

        bones_selected = 0
        armature = None

        # Take the first armature
        for ob in bpy.data.objects:
            if ob.type == 'ARMATURE' and len(ob.data.bones) > 0:
                armature = ob.data

                # Calculate number of selected bones if in pose-mode
                if context.mode == 'POSE':
                    bones_selected = len([b for b in armature.bones if b.select])

                # Prepare info string
                armature_info = "%s (%i bones)" % (ob.name, len(armature.bones))
                break
        else:
            armature_info = "Not found!"

        if armature:
            icon = 'NONE'
        else:
            icon = 'ERROR'

        col = layout.column(align=True)
        col.label("Armature: %s" % armature_info, icon)

        col = layout.column(align=True)
        col.prop(self, "use_selection", "Selection only (%i bones)" % bones_selected)
        col.enabled = bool(bones_selected)

        layout.label(text="Frame range: (%i frames)" % (abs(self.use_frame_end - self.use_frame_start) + 1))

        row = layout.row(align=True)
        row.prop(self, "use_frame_start")
        row.prop(self, "use_frame_end")

        col = layout.column(align=True)
        col.prop(self, "use_framerate")

        # Calculate number of markers in export range
        frame_min = min(self.use_frame_start, self.use_frame_end)
        frame_max = max(self.use_frame_start, self.use_frame_end)
        num_markers = len([m for m in context.scene.timeline_markers if frame_max >= m.frame >= frame_min])

        col = layout.column(align=True)
        col.prop(self, "use_notetrack", text="Notetrack (%i nodes)" % num_markers)

        col = layout.column(align=True)
        col.prop(self, "use_notetrack_format", expand=True)

    @classmethod
    def poll(self, context):
        return (context.scene is not None)

def menu_func_xmodel_import(self, context):
    self.layout.operator(ImportXmodel.bl_idname, text="CoD Xmodel (.XMODEL_EXPORT)")
"""
def menu_func_xanim_import(self, context):
    self.layout.operator(ImportXanim.bl_idname, text="CoD Xanim (.XANIM_EXPORT)")
"""
def menu_func_xmodel_export(self, context):
    self.layout.operator(ExportXmodel.bl_idname, text="CoD Xmodel (.XMODEL_EXPORT)")

def menu_func_xanim_export(self, context):
    self.layout.operator(ExportXanim.bl_idname, text="CoD Xanim (.XANIM_EXPORT)")

def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_func_xmodel_import)
    #bpy.types.INFO_MT_file_import.append(menu_func_xanim_import)
    bpy.types.INFO_MT_file_export.append(menu_func_xmodel_export)
    bpy.types.INFO_MT_file_export.append(menu_func_xanim_export)

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_func_xmodel_import)
    #bpy.types.INFO_MT_file_import.remove(menu_func_xanim_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_xmodel_export)
    bpy.types.INFO_MT_file_export.remove(menu_func_xanim_export)

if __name__ == "__main__":
    register()
