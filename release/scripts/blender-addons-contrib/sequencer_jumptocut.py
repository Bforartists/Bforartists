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
    "name": "Jump to Cut",
    "author": "Carlos Padial",
    "version": (5, 0, 2),
    "blender": (2, 63, 0),
    "category": "Sequencer",
    "location": "Sequencer > UI > Jump to Cut",
    "description": "Tool collection to help speed up editting and grade videos with blender",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Sequencer/Jump_to_cut",
    "tracker_url": "https://developer.blender.org/T24279"}


import bpy

class Jumptocut(bpy.types.Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_label = "Jump to Cut"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="NLA")

    def draw(self, context):
        layout = self.layout

        row=layout.row()
        split=row.split(percentage=0.5)
        colL = split.column()
        colR = split.column()
        colL.operator("sequencer.jumpprev", icon="PLAY_REVERSE")
        colR.operator("sequencer.jumpnext", icon='PLAY')

        row=layout.row()
        split=row.split()
        colL = split.column()
        colR = split.column()
        colL.operator("sequencer.markprev", icon="MARKER_HLT")
        colR.operator("sequencer.marknext", icon='MARKER_HLT')

        row=layout.row()
        split=row.split()
        colL1 = split.column()
        colL2 = split.column()
        colL1.operator("sequencer.sourcein", icon="REW")
        colL2.operator("sequencer.sourceout", icon='FF')


        row=layout.row()
        split=row.split()
        colR1 = split.column()
        colR1.operator("sequencer.setinout", icon="ARROW_LEFTRIGHT")
        row=layout.row()
        split=row.split(percentage=0.5)
        colR1 = split.column()
        colR1.operator("sequencer.triminout", icon="FULLSCREEN_EXIT")
        colR2 = split.column()
        colR2.operator("sequencer.setstartend", icon="SETTINGS")

        row=layout.row()
        split=row.split()
        colR1 = split.column()
        colR2 = split.column()
        colR1.operator("sequencer.metacopy", icon="COPYDOWN")
        colR2.operator("sequencer.metapaste", icon='PASTEDOWN')

#-----------------------------------------------------------------------------------------------------

class OBJECT_OT_Setinout(bpy.types.Operator):
    bl_label = "Mark in & out to active strip"
    bl_idname = "sequencer.setinout"
    bl_description = "set IN and OUT markers to the active strip limits"

    def invoke(self, context, event):
        scene=bpy.context.scene
        markers=scene.timeline_markers
        seq=scene.sequence_editor
        if seq:
            strip= seq.active_strip
            if strip != None:
                sin = strip.frame_start + strip.frame_offset_start
                sout = sin + strip.frame_final_duration
                if "IN" not in markers:
                    mark=markers.new(name="IN")
                    mark.frame=sin
                else:
                    mark=markers["IN"]
                    mark.frame=sin
                if "OUT" not in markers:
                    mark= markers.new(name="OUT")
                    mark.frame=sout
                else:
                    mark=markers["OUT"]
                    mark.frame=sout
        return {'FINISHED'}


def triminout(strip,sin,sout):
    start = strip.frame_start+strip.frame_offset_start
    end = start+strip.frame_final_duration
    if end > sin:
        if start < sin:
            strip.select_right_handle = False
            strip.select_left_handle = True
            bpy.ops.sequencer.snap(frame=sin)
            strip.select_left_handle = False
    if start < sout:
        if end > sout:
            strip.select_left_handle = False
            strip.select_right_handle = True
            bpy.ops.sequencer.snap(frame=sout)
            strip.select_right_handle = False
    return {'FINISHED'}


class OBJECT_OT_Triminout(bpy.types.Operator):
    bl_label = "Trim to in & out"
    bl_idname = "sequencer.triminout"
    bl_description = "trim the selected strip to IN and OUT markers (if exists)"

    def invoke(self, context, event):
        scene=bpy.context.scene
        markers=scene.timeline_markers
        seq=scene.sequence_editor
        if seq:
            strip= seq.active_strip
            if strip != None:
                if "IN" and "OUT" in markers:
                    sin=markers["IN"].frame
                    sout=markers["OUT"].frame
                    triminout(strip,sin,sout)
                else:
                    self.report({'WARNING'}, "there is no IN and OUT")
            bpy.ops.sequencer.reload()
        return {'FINISHED'}

def searchprev(j, list):
    list.sort(reverse=True)
    for i in list:
        if i < j:
            result = i
            break
    else: result = j
    return result

def searchnext(j, list):
    list.sort()
    for i in list:
        if i > j:
            result = i
            break
    else: result = j
    return result

def geteditpoints(seq):
    #this create a list of editpoints including strips from
    # inside metastrips. It reads only 1 level into the metastrip
    editpoints = []
    cliplist = []
    metalist = []
    if seq:
        for i in seq.sequences:
            if i.type == 'META':
                metalist.append(i)
                start = i.frame_start + i.frame_offset_start
                end = start + i.frame_final_duration
                editpoints.append(start)
                editpoints.append(end)
            else:
                cliplist.append(i)
        for i in metalist:
            for j in i.sequences:
                cliplist.append(j)
        for i in cliplist:
            start = i.frame_start + i.frame_offset_start
            end = start + i.frame_final_duration
            editpoints.append(start)
            editpoints.append(end)
            #print(start," ",end)
    return editpoints

#JUMP
class OBJECT_OT_Jumpprev(bpy.types.Operator):  #Operator jump previous edit point
    bl_label = "Cut previous"
    bl_idname = "sequencer.jumpprev"
    bl_description = "jump to previous edit point"

    editpoints = []

    def invoke(self, context, event):
        scene=bpy.context.scene
        seq=scene.sequence_editor
        editpoints = geteditpoints(seq)
        bpy.context.scene.frame_current = searchprev(scene.frame_current, editpoints)
        return {'FINISHED'}

class OBJECT_OT_Jumpnext(bpy.types.Operator):  #Operator jump next edit point
    bl_label = "Cut next"
    bl_idname = "sequencer.jumpnext"
    bl_description = "jump to next edit point"

    def invoke(self, context, event):
        scene=bpy.context.scene
        seq=scene.sequence_editor
        editpoints = geteditpoints(seq)
        bpy.context.scene.frame_current = searchnext(scene.frame_current, editpoints)
        last = 0
        for i in editpoints:
            if i > last: last = i
        if bpy.context.scene.frame_current == last:
            bpy.context.scene.frame_current = last-1
            self.report({'INFO'},'Last Frame')
        return {'FINISHED'}

# MARKER
class OBJECT_OT_Markerprev(bpy.types.Operator):
    bl_label = "Marker previous"
    bl_idname = "sequencer.markprev"
    bl_description = "jump to previous marker"

    def invoke(self, context, event):
        markerlist = []
        scene= bpy.context.scene
        markers = scene.timeline_markers
        for i in markers: markerlist.append(i.frame)
        bpy.context.scene.frame_current = searchprev(scene.frame_current, markerlist)
        return {'FINISHED'}

class OBJECT_OT_Markernext(bpy.types.Operator):
    bl_label = "Marker next"
    bl_idname = "sequencer.marknext"
    bl_description = "jump to next marker"

    def invoke(self, context, event):
        markerlist = []
        scene= bpy.context.scene
        markers = scene.timeline_markers
        for i in markers: markerlist.append(i.frame)
        bpy.context.scene.frame_current = searchnext(scene.frame_current, markerlist)
        return {'FINISHED'}

# SOURCE IN OUT

class OBJECT_OT_Sourcein(bpy.types.Operator):  #Operator source in
    bl_label = "Source IN"
    bl_idname = "sequencer.sourcein"
    bl_description = "add a marker named IN"

    def invoke(self, context, event):
        scene=bpy.context.scene
        seq = scene.sequence_editor
        markers=scene.timeline_markers
        if "OUT" in markers:
            sout=markers["OUT"]
            if scene.frame_current <= sout.frame:
                if "IN" not in markers:
                    sin=markers.new(name="IN")
                    sin.frame=scene.frame_current
                else:
                    sin=markers["IN"]
                    sin.frame=scene.frame_current
            #trying to set in after out
            else:
                if "IN" not in markers:
                    sin=markers.new(name="IN")
                    sin.frame=sout.frame
                else:
                    sin=markers["IN"]
                    sin.frame=sout.frame
                self.report({'WARNING'},'IN after OUT')
        else:
            if "IN" not in markers:
                sin=markers.new(name="IN")
                sin.frame=scene.frame_current
            else:
                sin=markers["IN"]
                sin.frame=scene.frame_current
        if seq:
            bpy.ops.sequencer.reload()
        return {'FINISHED'}

class OBJECT_OT_Sourceout(bpy.types.Operator):  #Operator source out
    bl_label = "Source OUT"
    bl_idname = "sequencer.sourceout"
    bl_description = "add a marker named OUT"

    def invoke(self, context, event):
        scene=bpy.context.scene
        seq = scene.sequence_editor
        markers=scene.timeline_markers
        if "IN" in markers:
            sin=markers["IN"]
            if scene.frame_current >= sin.frame:
                if "OUT" not in markers:
                    sout= markers.new(name="OUT")
                    sout.frame=scene.frame_current
                else:
                    sout=markers["OUT"]
                    sout.frame=scene.frame_current
            #trying to set out before in
            else:
                if "OUT" not in markers:
                    sout= markers.new(name="OUT")
                    sout.frame = sin.frame
                else:
                    sout=markers["OUT"]
                    sout.frame = sin.frame
                self.report({'WARNING'}, "OUT before IN")
        else:
            sout= markers.new(name="OUT")
            sout.frame=scene.frame_current
        if seq:
            bpy.ops.sequencer.reload()
        return {'FINISHED'}



class OBJECT_OT_Setstartend(bpy.types.Operator):  #Operator set start & end
    bl_label = "set Start & End"
    bl_idname = "sequencer.setstartend"
    bl_description = "set Start = In and End = Out"

    def invoke(self, context, event):
        scene=bpy.context.scene
        seq = scene.sequence_editor
        markers=scene.timeline_markers
        if seq:
            if "IN" and "OUT" in markers:
                sin=markers["IN"]
                sout=markers["OUT"]
                scene.frame_start = sin.frame
                scene.frame_end = sout.frame
                print("change")
            else:
                self.report({'WARNING'}, "there is no IN and OUT")
            bpy.ops.sequencer.reload()
        return {'FINISHED'}


# COPY PASTE

class OBJECT_OT_Metacopy(bpy.types.Operator):  #Operator copy source in/out
    bl_label = "Trim & Meta-Copy"
    bl_idname = "sequencer.metacopy"
    bl_description = "make meta from selected strips, trim it to in/out (if available) and copy it to clipboard"

    def invoke(self, context, event):
        # rehacer
        scene=bpy.context.scene
        seq = scene.sequence_editor
        markers=scene.timeline_markers
        strip1= seq.active_strip
        if strip1 != None:
            if "IN" and "OUT" in markers:
                sin=markers["IN"].frame
                sout=markers["OUT"].frame
                bpy.ops.sequencer.meta_make()
                strip2= seq.active_strip
                triminout(strip2,sin,sout)
                bpy.ops.sequencer.copy()
                bpy.ops.sequencer.meta_separate()
                self.report({'INFO'}, "META has been trimed and copied")
            else:
                bpy.ops.sequencer.meta_make()
                bpy.ops.sequencer.copy()
                bpy.ops.sequencer.meta_separate()
                self.report({'WARNING'}, "No In & Out!! META has been copied")
        else:
            self.report({'ERROR'}, "No strip selected")
        return {'FINISHED'}

class OBJECT_OT_Metapaste(bpy.types.Operator):  #Operator paste source in/out
    bl_label = "Paste in current Frame"
    bl_idname = "sequencer.metapaste"
    bl_description = "paste source from clipboard to current frame"

    def invoke(self, context, event):
        # rehacer
        scene=bpy.context.scene
        bpy.ops.sequencer.paste()
        bpy.ops.sequencer.snap(frame=scene.frame_current)
        return {'FINISHED'}

# Registering / Unregister

def register():
    bpy.utils.register_class(Jumptocut)
    bpy.utils.register_class(OBJECT_OT_Jumpprev)
    bpy.utils.register_class(OBJECT_OT_Jumpnext)
    bpy.utils.register_class(OBJECT_OT_Markerprev)
    bpy.utils.register_class(OBJECT_OT_Markernext)
    bpy.utils.register_class(OBJECT_OT_Sourcein)
    bpy.utils.register_class(OBJECT_OT_Sourceout)
    bpy.utils.register_class(OBJECT_OT_Metacopy)
    bpy.utils.register_class(OBJECT_OT_Metapaste)
    bpy.utils.register_class(OBJECT_OT_Triminout)
    bpy.utils.register_class(OBJECT_OT_Setinout)
    bpy.utils.register_class(OBJECT_OT_Setstartend)

def unregister():
    bpy.utils.unregister_class(Jumptocut)
    bpy.utils.unregister_class(OBJECT_OT_Jumpprev)
    bpy.utils.unregister_class(OBJECT_OT_Jumpnext)
    bpy.utils.unregister_class(OBJECT_OT_Markerprev)
    bpy.utils.unregister_class(OBJECT_OT_Markernext)
    bpy.utils.unregister_class(OBJECT_OT_Sourcein)
    bpy.utils.unregister_class(OBJECT_OT_Sourceout)
    bpy.utils.unregister_class(OBJECT_OT_Metacopy)
    bpy.utils.unregister_class(OBJECT_OT_Metapaste)
    bpy.utils.unregister_class(OBJECT_OT_Triminout)
    bpy.utils.unregister_class(OBJECT_OT_Setinout)
    bpy.utils.unregister_class(OBJECT_OT_Setstartend)
if __name__ == "__main__":
    register()
