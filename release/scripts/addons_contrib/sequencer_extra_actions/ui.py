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


# UI
class SEQUENCER_EXTRA_MT_input(bpy.types.Menu):
    bl_label = "Input"

    def draw(self, context):
        self.layout.operator_context = 'INVOKE_REGION_WIN'
        self.layout.operator('sequencerextra.striprename',
        text='File Name to Strip Name', icon='PLUGIN')
        self.layout.operator('sequencerextra.editexternally',
        text='Open with External Editor', icon='PLUGIN')
        self.layout.operator('sequencerextra.edit',
        text='Open with Editor', icon='PLUGIN')
        self.layout.operator('sequencerextra.createmovieclip',
        text='Create Movieclip strip', icon='PLUGIN')


def sequencer_add_menu_func(self, context):
    self.layout.operator('sequencerextra.recursiveload', 
    text='recursive load from browser', icon='PLUGIN')
    self.layout.separator()


def sequencer_select_menu_func(self, context):
    self.layout.operator_menu_enum('sequencerextra.select_all_by_type',
    'type', text='All by Type', icon='PLUGIN')
    self.layout.separator()
    self.layout.operator('sequencerextra.selectcurrentframe',
    text='Before Current Frame', icon='PLUGIN').mode = 'BEFORE'
    self.layout.operator('sequencerextra.selectcurrentframe',
    text='After Current Frame', icon='PLUGIN').mode = 'AFTER'
    self.layout.operator('sequencerextra.selectcurrentframe',
    text='On Current Frame', icon='PLUGIN').mode = 'ON'
    self.layout.separator()
    self.layout.operator('sequencerextra.selectsamechannel',
    text='Same Channel', icon='PLUGIN')


def sequencer_strip_menu_func(self, context):
    self.layout.operator('sequencerextra.extendtofill',
    text='Extend to Fill', icon='PLUGIN')
    self.layout.operator('sequencerextra.distribute',
    text='Distribute', icon='PLUGIN')
    self.layout.operator_menu_enum('sequencerextra.fadeinout',
    'mode', text='Fade', icon='PLUGIN')
    self.layout.operator_menu_enum('sequencerextra.copyproperties',
    'prop', icon='PLUGIN')
    self.layout.operator('sequencerextra.slidegrab',
    text='Slide Grab', icon='PLUGIN')
    self.layout.operator_menu_enum('sequencerextra.slide',
    'mode', icon='PLUGIN')
    self.layout.operator('sequencerextra.insert',
    text='Insert (Single Channel)', icon='PLUGIN').singlechannel = True
    self.layout.operator('sequencerextra.insert',
    text='Insert', icon='PLUGIN').singlechannel = False
    self.layout.operator('sequencerextra.ripplecut',
    text='Ripple Cut', icon='PLUGIN')
    self.layout.operator('sequencerextra.rippledelete',
    text='Ripple Delete', icon='PLUGIN')
    self.layout.separator()


def sequencer_header_func(self, context):
    self.layout.menu("SEQUENCER_EXTRA_MT_input")
    if context.space_data.view_type in ('PREVIEW', 'SEQUENCER_PREVIEW'):
        self.layout.operator('sequencerextra.jogshuttle',
        text='Jog/Shuttle', icon='NDOF_TURN')
    if context.space_data.view_type in ('SEQUENCER', 'SEQUENCER_PREVIEW'):
        self.layout.operator('sequencerextra.navigateup',
        text='Navigate Up', icon='FILE_PARENT')
    if context.space_data.view_type in ('SEQUENCER', 'SEQUENCER_PREVIEW'):
        self.layout.operator('sequencerextra.placefromfilebrowser',
        text='File Place', icon='TRIA_DOWN').insert = False
    if context.space_data.view_type in ('SEQUENCER', 'SEQUENCER_PREVIEW'):
        self.layout.operator('sequencerextra.placefromfilebrowser',
        text='File Insert', icon='TRIA_RIGHT').insert = True
    if context.space_data.view_type in ('SEQUENCER', 'SEQUENCER_PREVIEW'):
        self.layout.operator('sequencerextra.placefromfilebrowserproxy',
        text='Proxy Place', icon='TRIA_DOWN')
    if context.space_data.view_type in ('SEQUENCER', 'SEQUENCER_PREVIEW'):
        self.layout.operator('sequencerextra.placefromfilebrowserproxy',
        text='Proxy Insert', icon='TRIA_RIGHT').insert = True


def time_frame_menu_func(self, context):
    self.layout.operator('timeextra.trimtimelinetoselection',
    text='Trim to Selection', icon='PLUGIN')
    self.layout.operator('timeextra.trimtimeline',
    text='Trim to Timeline Content', icon='PLUGIN')
    self.layout.separator()
    self.layout.operator('screenextra.frame_skip',
    text='Skip Forward One Second', icon='PLUGIN').back = False
    self.layout.operator('screenextra.frame_skip',
    text='Skip Back One Second', icon='PLUGIN').back = True
    self.layout.separator()


def time_header_func(self, context):
    self.layout.operator('sequencerextra.jogshuttle',
    text='Jog/Shuttle', icon='NDOF_TURN')


def clip_header_func(self, context):
    self.layout.operator('sequencerextra.jogshuttle',
    text='Jog/Shuttle', icon='NDOF_TURN')


def clip_clip_menu_func(self, context):
    self.layout.operator('clipextra.openactivestrip',
    text='Open Active Strip', icon='PLUGIN')
    self.layout.operator('clipextra.openfromfilebrowser',
    text='Open from File Browser', icon='PLUGIN')
    self.layout.separator()


class ExifInfoPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "EXIF Info Panel"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'

    @staticmethod
    def has_sequencer(context):
        return (context.space_data.view_type\
        in {'SEQUENCER', 'SEQUENCER_PREVIEW'})

    @classmethod
    def poll(cls, context):
        return cls.has_sequencer(context)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="NLA")

    def draw(self, context):
        layout = self.layout
        sce = context.scene
        row = layout.row()
        row.operator("sequencerextra.read_exif")
        row = layout.row()
        row.label(text="Exif Data", icon='RENDER_REGION')
        row = layout.row()

        try:
            strip = context.scene.sequence_editor.active_strip

            f = strip.frame_start
            frame = sce.frame_current
            try:
                if len(sce['metadata']) == 1:
                    for d in sce['metadata'][0]:
                        split = layout.split(percentage=0.5)
                        col = split.column()
                        row = col.row()
                        col.label(text=d)
                        col = split.column()
                        col.label(str(sce['metadata'][0][d]))
                else:
                    for d in sce['metadata'][frame - f]:
                        split = layout.split(percentage=0.5)
                        col = split.column()
                        row = col.row()
                        col.label(text=d)
                        col = split.column()
                        col.label(str(sce['metadata'][frame - f][d]))
            except KeyError:
                pass
        except AttributeError:
            pass
