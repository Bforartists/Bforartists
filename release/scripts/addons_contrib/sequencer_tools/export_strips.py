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

import bpy
from bpy.props import StringProperty

class SEQExportStrip(bpy.types.Operator):
    """Export (render) selected strips in sequencer"""
    bl_idname = "sequencer.export_strips"
    bl_label = "Export Strips"

    filepath = StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        sce = bpy.context.scene
        back_filepath = sce.render.filepath
        back_seq = sce.render.use_sequencer
        back_start = sce.frame_start
        back_end = sce.frame_end
        hidden_seq = []

        sce.render.use_sequencer = True
        sce.render.filepath = self.filepath
        seq = sce.sequence_editor
        start = end = None
        for strip in seq.sequences_all:
            if not strip.select:
                if not strip.mute:
                    strip.mute = True
                    hidden_seq.append(strip)
                continue
            if start is None or strip.frame_final_start < start:
                start = strip.frame_final_start
            if end is None or strip.frame_final_end > end:
                end = strip.frame_final_end
        sce.frame_start = start
        sce.frame_end = end

        # Non-blocking render!
        bpy.ops.render.render("INVOKE_DEFAULT", animation=True)

        for strip in hidden_seq:
            strip.mute = False
        sce.render.use_sequencer = back_seq
        sce.render.filepath = back_filepath
        sce.frame_start = back_start
        sce.frame_end = back_end
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = bpy.context.scene.render.filepath
        winman = context.window_manager
        winman.fileselect_add(self)
        return {'RUNNING_MODAL'}
