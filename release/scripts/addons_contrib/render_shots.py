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
    "name": "Render Shots",
    "author": "Aaron Symons",
    "version": (0, 3, 2),
    "blender": (2, 76, 0),
    "location": "Properties > Render > Render Shots",
    "description": "Render an image or animation from different camera views",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php?title=Extensions:2.6/Py"\
                "/Scripts/Render/Render_Shots",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Render"}


import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty
from bpy.app.handlers import persistent
import os, shutil


#####################################
# Update Functions
#####################################
def shape_nav(self, context):
    nav = self.rs_shotshape_nav
    
    if self.rs_shotshape_shape != "":
        shapeVerts = bpy.data.objects[self.rs_shotshape_shape].data.vertices
        max = len(shapeVerts)-1
        min = max - (max+max)
        
        if nav > max or nav < min:
            nav = 0
        
        v = shapeVerts[nav].co
        self.location = (v[0], v[1], v[2])
    return None


def is_new_object(ob):
    try:
        isNew = ob["rs_shotshape_use_frames"]
    except:
        isNew = None
    
    return True if isNew is None else False


def update_shot_list(scn):
    scn.rs_is_updating = True
    if hasattr(scn, 'rs_create_folders'):
        scn.rs_create_folders = False
    
    for ob in bpy.data.objects:
        if ob.type == 'CAMERA':
            if is_new_object(ob):
                ob["rs_shot_include"] = True
                ob["rs_shot_start"] = scn.frame_start
                ob["rs_shot_end"] = scn.frame_end
                ob["rs_shot_output"] = ""
                ob["rs_toggle_panel"] = True
                ob["rs_settings_use"] = False
                ob["rs_resolution_x"] = scn.render.resolution_x
                ob["rs_resolution_y"] = scn.render.resolution_y
                ob["rs_cycles_samples"] = 10
                ob["rs_shotshape_use"] = False
                ob["rs_shotshape_shape"] = ""
                ob["rs_shotshape_nav"] = 0
                ob["rs_shotshape_nav_start"] = False
                ob["rs_shotshape_offset"] = 1
                ob["rs_shotshape_use_frames"] = False
            else:
                ob["rs_shot_include"]
                ob["rs_shot_start"]
                ob["rs_shot_end"]
                ob["rs_shot_output"]
                ob["rs_toggle_panel"]
                ob["rs_settings_use"]
                ob["rs_resolution_x"]
                ob["rs_resolution_y"]
                ob["rs_cycles_samples"]
                ob["rs_shotshape_use"]
                ob["rs_shotshape_shape"]
                ob["rs_shotshape_nav"]
                ob["rs_shotshape_nav_start"]
                ob["rs_shotshape_offset"]
                ob["rs_shotshape_use_frames"]
    
    scn.rs_is_updating = False


#####################################
# Initialisation
#####################################
def init_props():
    object = bpy.types.Object
    scene = bpy.types.Scene
    
    # Camera properties
    object.rs_shot_include = BoolProperty(name="", 
        description="Include this shot during render", default=True)
    
    object.rs_shot_start = IntProperty(name="Start",
        description="First frame in this shot",
        default=0, min=0, max=300000)
    
    object.rs_shot_end = IntProperty(name="End",
        description="Last frame in this shot", 
        default=0, min=0, max=300000)

    object.rs_shot_output = StringProperty(name="",
        description="Directory/name to save to", subtype='DIR_PATH')
    
    object.rs_toggle_panel = BoolProperty(name="",
        description="Show/hide options for this shot", default=True)
    
    # Render settings
    object.rs_settings_use = BoolProperty(name = "", default=False, 
        description = "Use specific render settings for this shot")
    
    object.rs_resolution_x = IntProperty(name="X",
        description="Number of horizontal pixels in the rendered image",
        default=2000, min=4, max=10000)
    
    object.rs_resolution_y = IntProperty(name="Y",
        description = "Number of vertical pixels in the rendered image",
        default=2000, min=4, max=10000)
    
    object.rs_cycles_samples = IntProperty(name="Samples",
        description = "Number of samples to render for each pixel",
        default=10, min=1, max=2147483647)
    
    # Shot shapes
    object.rs_shotshape_use = BoolProperty(name="", default=False,
        description="Use a shape to set a series of shots for this camera")
    
    object.rs_shotshape_shape = StringProperty(name="Shape:", 
        description="Select an object")
    
    object.rs_shotshape_nav = IntProperty(name="Navigate", 
        description="Navigate through this shape's vertices (0 = first vertex)", 
        default=0, update=shape_nav)
    
    object.rs_shotshape_nav_start = BoolProperty(name="Start from here", 
        default=False,
        description="Start from this vertex (skips previous vertices)")
    
    object.rs_shotshape_offset = IntProperty(name="Offset", 
        description="Offset between frames (defines animation length)", 
        default=1, min=1, max=200)
    
    object.rs_shotshape_use_frames = BoolProperty(name="Use frame range",
        description="Use the shot's frame range instead of the object's vertex"\
        " count", default=False)

    # Internal
    scene.rs_is_updating = BoolProperty(name="", description="", default=False)

    scene.rs_create_folders = BoolProperty(name="", description="", default=False)

    scene.rs_main_folder = StringProperty(name="Main Folder",
                subtype='DIR_PATH', default="",
                description="Main folder in which to create the sub folders")
    
    scene.rs_overwrite_folders = BoolProperty(name="Overwrite", default=False,
                description="Overwrite existing folders (this will delete all"\
                " files inside any existing folders)")



#####################################
# Operators and Functions
#####################################
RENDER_DONE = True
RENDER_SETTINGS_HELP = False
TIMELINE = {"start": 1, "end": 250, "current": 1}
RENDER_SETTINGS = {"cycles_samples": 10, "res_x": 1920, "res_y": 1080}


@persistent
def render_finished(unused):
    global RENDER_DONE
    RENDER_DONE = True


def using_cycles(scn):
    return True if scn.render.engine == 'CYCLES' else False


def timeline_handler(scn, mode):
    global TIMELINE
    
    if mode == 'GET':
        TIMELINE["start"] = scn.frame_start
        TIMELINE["end"] = scn.frame_end
        TIMELINE["current"] = scn.frame_current
    
    elif mode == 'SET':
        scn.frame_start = TIMELINE["start"]
        scn.frame_end = TIMELINE["end"]
        scn.frame_current = TIMELINE["current"]


def render_settings_handler(scn, mode, cycles_on, ob):
    global RENDER_SETTINGS
    
    if mode == 'GET':
        RENDER_SETTINGS["cycles_samples"] = scn.cycles.samples
        RENDER_SETTINGS["res_x"] = scn.render.resolution_x
        RENDER_SETTINGS["res_y"] = scn.render.resolution_y
    
    elif mode == 'SET':
        if cycles_on:
            scn.cycles.samples = ob["rs_cycles_samples"]
        scn.render.resolution_x = ob["rs_resolution_x"]
        scn.render.resolution_y = ob["rs_resolution_y"]
    
    elif mode == 'REVERT':
        if cycles_on:
            scn.cycles.samples = RENDER_SETTINGS["cycles_samples"]
        scn.render.resolution_x = RENDER_SETTINGS["res_x"]
        scn.render.resolution_y = RENDER_SETTINGS["res_y"]


def frames_from_verts(ob, end, shape, mode):
    start = ob.rs_shot_start
    frame_range = (end - start)+1
    verts = len(shape.data.vertices)
    
    if frame_range % verts != 0:
        end += 1
        return create_frames_from_verts(ob, end, shape, mode)
    else:
        if mode == 'OFFSET':
            return frame_range / verts
        elif mode == 'END':
            return end


def keyframes_handler(scn, ob, shape, mode):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select = True
    
    start = ob.rs_shotshape_nav if ob.rs_shotshape_nav_start else 0
    
    if ob.rs_shotshape_use_frames and shape is not None:
        firstframe = ob.rs_shot_start
        offset = frames_from_verts(ob, ob.rs_shot_end, shape, 'OFFSET')
    else:
        firstframe = 1
        offset = ob.rs_shotshape_offset
    
    if mode == 'SET':
        scn.frame_current = firstframe
        for vert in shape.data.vertices:
            if vert.index >= start:
                ob.location = vert.co
                bpy.ops.anim.keyframe_insert_menu(type='Location')
                scn.frame_current += offset
        return (len(shape.data.vertices) - start) * offset
    
    elif mode == 'WIPE':
        ob.animation_data_clear()


class RENDER_OT_RenderShots_create_folders(bpy.types.Operator):
    ''' Create the output folders for all cameras '''
    bl_idname = "render.rendershots_create_folders"
    bl_label = "Create Folders"
    
    mode = IntProperty()
    
    def execute(self, context):
        scn = context.scene
        
        if self.mode == 1: # Display options
            scn.rs_create_folders = True
        
        elif self.mode == 2: # Create folders
            if scn.rs_main_folder != "" and not scn.rs_main_folder.isspace():
                for ob in bpy.data.objects:
                    if ob.type == 'CAMERA' and not is_new_object(ob):
                        # Name cleaning
                        if "." in ob.name:
                            name = ob.name.split(".")
                            camName = name[0]+name[1]
                        else:
                            camName = ob.name
                        
                        mainFolder = scn.rs_main_folder
                        destination = os.path.join(mainFolder, camName)
                        
                        # Folder creation
                        if scn.rs_overwrite_folders:
                            if os.path.isdir(destination):
                                shutil.rmtree(destination)
                            
                            os.mkdir(destination)
                            ob.rs_shot_output = destination+"\\"
                        else:
                            if not os.path.isdir(destination):
                                ob.rs_shot_output = destination+"\\"
                
                                os.makedirs(destination_path)
                self.report({'INFO'}, "Output folders created")
                scn.rs_overwrite_folders = False
                scn.rs_create_folders = False
            else:
                self.report({'ERROR'}, "No main folder selected")
        
        elif self.mode == 3: # Cancelled
            scn.rs_overwrite_folders = False
            scn.rs_create_folders = False
        
        return {'FINISHED'}


class RENDER_OT_RenderShots_settingshelp(bpy.types.Operator):
    ''' \
        Edit the resolutions and see the changes in 3D View ('ESC' to finish)\
    '''
    bl_idname = "render.rendershots_settingshelp"
    bl_label = "Render Settings Help"
    
    cam = StringProperty()

    def execute(self, context):
        global RENDER_SETTINGS_HELP
        RENDER_SETTINGS_HELP = True

        scn = context.scene

        render_settings_handler(scn, 'GET', using_cycles(scn), None)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        scn = context.scene
        ob = bpy.data.objects[self.cam]

        if event.type in {'ESC'}:
            global RENDER_SETTINGS_HELP
            RENDER_SETTINGS_HELP = False
            render_settings_handler(scn, 'REVERT', using_cycles(scn), None)
            return {'FINISHED'}
        
        scn.render.resolution_x = ob["rs_resolution_x"]
        scn.render.resolution_y = ob["rs_resolution_y"]
        
        return {'PASS_THROUGH'}


class RENDER_OT_RenderShots_constraints_add(bpy.types.Operator):
    ''' Add the tracking constraints and Empty for this camera '''
    bl_idname = "render.rendershots_constraints_add"
    bl_label = "Create Constraints"
    
    cam = StringProperty()
    
    def execute(self, context):
        ob = bpy.data.objects[self.cam]
        ssName = "LookAt_for_"+ob.name
        
        bpy.ops.object.add(type="EMPTY")
        context.active_object.name = ssName
        
        target = bpy.data.objects[ssName]
        
        ob.constraints.new(type="DAMPED_TRACK").name="SS_Damped"
        damped_track = ob.constraints["SS_Damped"]
        damped_track.target = target
        damped_track.track_axis = 'TRACK_NEGATIVE_Z'
        damped_track.influence = 0.994
        
        ob.constraints.new(type="LOCKED_TRACK").name="SS_Locked"
        locked_track = ob.constraints["SS_Locked"]
        locked_track.target = target
        locked_track.track_axis = 'TRACK_Y'
        locked_track.lock_axis = 'LOCK_Z'
        locked_track.influence = 1.0
        
        return {'FINISHED'}


class RENTER_OT_rendershots_refresh(bpy.types.Operator):
    ''' Adds newly created cameras to the list '''
    bl_idname = "render.rendershots_refresh"
    bl_label = "Refresh"    
    
    def execute(self, context):
        update_shot_list(context.scene)
        return {'FINISHED'}


class RENDER_OT_RenderShots_render(bpy.types.Operator):
    ''' Render shots '''
    bl_idname = "render.rendershots_render"
    bl_label = "Render"    
    
    animation = BoolProperty(default=False)
    _timer = None
    _usingShape = False
    
    def execute(self, context):
        global RENDER_DONE
        RENDER_DONE = True
        
        scn = context.scene
        self.camList = []
        self.vertTrack = -1
        self.cam = ""

        for ob in bpy.data.objects:
            if ob.type == 'CAMERA' and not is_new_object(ob):
                if ob["rs_shot_include"]:
                    output = ob["rs_shot_output"]
                    
                    addToList = False
                    
                    if output != "" and not output.isspace():
                        addToList = True
                    else:
                        message = "\"%s\" has no output destination" % ob.name
                        self.report({'WARNING'}, message)
                    
                    if ob["rs_shotshape_use"]:
                        shotShape = ob["rs_shotshape_shape"]
                        if shotShape == "":
                            addToList = False
                            self.report({'WARNING'}, 
                                        "\"%s\" has no shot shape" % ob.name)
                        elif bpy.data.objects[shotShape].type != 'MESH':
                            errObj = bpy.data.objects[shotShape].name
                            addToList = False
                            self.report({'ERROR'},
                                        "\"%s\" is not a mesh object" % errObj)
                        #else:
                        #    bpy.data.objects[shotShape].hide_render = True
                    if addToList:
                        self.camList.append(ob.name)
        
        self.camList.reverse()
        timeline_handler(scn, 'GET')
        render_settings_handler(scn, 'GET', using_cycles(scn), None)
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(3, context.window)
        return {'RUNNING_MODAL'}
    
    
    def modal(self, context, event):
        global RENDER_DONE
        
        scn = context.scene
        
        if event.type in {'ESC'}:
            context.window_manager.event_timer_remove(self._timer)
            keyframes_handler(scn, bpy.data.objects[self.cam], None, 'WIPE')
            render_settings_handler(scn, 'REVERT', using_cycles(scn), None)
            timeline_handler(scn, 'SET')
            return {'CANCELLED'}
        
        if RENDER_DONE and self.camList:
            RENDER_DONE = False
            objs = bpy.data.objects
            range = 0
            
            if self._usingShape:
                keyframes_handler(scn, objs[self.cam], None, 'WIPE')
            
            self._usingShape = False
            
            if not self._usingShape and self.camList:
                self.cam = self.camList.pop()
            
            ob = objs[self.cam]
            
            # Output and name cleaning
            scn.camera = ob
            output = ob["rs_shot_output"]
            
            if output[-1] == "/" or output[-1] == "\\":
                if "." in self.cam:
                    camName = self.cam.split(".")
                    output += camName[0]+camName[1]
                else:
                    output += self.cam
            
            # Shot shapes
            if ob["rs_shotshape_use"]:
                self._usingShape = True
                shape = ob["rs_shotshape_shape"]
                range = keyframes_handler(scn, ob, objs[shape], 'SET')
            
            # Render settings
            if ob["rs_settings_use"]:
                render_settings_handler(scn, 'SET', using_cycles(scn), ob)
            else:
                render_settings_handler(scn, 'REVERT', using_cycles(scn), None)
            
            context.scene.render.filepath = output
            
            # Render
            ssUsing = ob["rs_shotshape_use"]
            if self.animation and not ssUsing and not self._usingShape:
                scn.frame_start = ob["rs_shot_start"]
                scn.frame_end = ob["rs_shot_end"]
                bpy.ops.render.render('INVOKE_DEFAULT', animation=True)
            
            elif self.animation and ssUsing and self._usingShape:
                if ob["rs_shotshape_use_frames"]:
                    scn.frame_start = ob.rs_shot_start
                    scn.frame_end = frames_from_verts(ob, ob.rs_shot_end, 
                                                        objs[shape], 'END')
                else:
                    scn.frame_start = 1
                    scn.frame_end = range
                bpy.ops.render.render('INVOKE_DEFAULT', animation=True)
            
            elif not self.animation and not ssUsing and not self._usingShape:
                bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)
        
        elif RENDER_DONE and not self.camList:
            context.window_manager.event_timer_remove(self._timer)
            keyframes_handler(scn, bpy.data.objects[self.cam], None, 'WIPE')
            render_settings_handler(scn, 'REVERT', using_cycles(scn), None)
            timeline_handler(scn, 'SET')
            return {'FINISHED'}
        
        return {'PASS_THROUGH'}


class RENDER_OT_RenderShots_previewcamera(bpy.types.Operator):
    ''' Preview this shot (makes this the active camera in 3D View) '''
    bl_idname = "render.rendershots_preview_camera"
    bl_label = "Preview Camera"
    
    camera = bpy.props.StringProperty()
    
    def execute(self, context):
        scn = context.scene
        cam = bpy.data.objects[self.camera]
        scn.objects.active = cam
        scn.camera = cam
        return {'FINISHED'}


#####################################
# UI
#####################################
class RENDER_PT_RenderShots(bpy.types.Panel):
    bl_label = "Render Shots"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    
    def draw(self, context):
        global RENDER_SETTINGS_HELP
        
        layout = self.layout
        scn = context.scene

        ANI_ICO, STILL_ICO = "RENDER_ANIMATION", "RENDER_STILL"
        INCL_ICO = "RESTRICT_RENDER_OFF"
        RENDER_OP = "render.rendershots_render"
        
        row = layout.row()
        row.operator(RENDER_OP, text="Image", icon=STILL_ICO)
        row.operator(RENDER_OP, text="Animation", icon=ANI_ICO).animation=True
        
        row = layout.row()

        if scn.rs_create_folders:
            row.operator("render.rendershots_create_folders", 
                        icon="FILE_TICK").mode=2
        else:
            row.operator("render.rendershots_create_folders", 
                        icon="NEWFOLDER").mode=1
        
        row.operator("render.rendershots_refresh", icon="FILE_REFRESH")
        
        if scn.rs_create_folders:
            row = layout.row()
            col = row.column(align=True)
            colrow = col.row()
            colrow.label(text="Main Folder:")
            colrow = col.row()
            colrow.prop(scn, "rs_main_folder", text="")
            colrow = col.row()
            colrow.prop(scn, "rs_overwrite_folders")
            colrow.operator("render.rendershots_create_folders", text="Cancel", 
                            icon="X").mode=3
        
        if not scn.rs_is_updating:
            for ob in bpy.data.objects:
                if ob.type == 'CAMERA' and not is_new_object(ob):
                    TOGL_ICO = "TRIA_DOWN" if ob["rs_toggle_panel"] else "TRIA_LEFT"
                    
                    box = layout.box()
                    box.active = ob["rs_shot_include"]
                    col = box.column()
                    row = col.row()
                    row.label(text="\""+ob.name+"\"")
                    row.operator("render.rendershots_preview_camera", text="", 
                                    icon="OUTLINER_OB_CAMERA").camera=ob.name
                    row.prop(ob, "rs_shotshape_use", icon="MESH_DATA")
                    row.prop(ob, "rs_settings_use", icon="SETTINGS")
                    row.prop(ob, "rs_shot_include", icon=INCL_ICO)
                    row.prop(ob, "rs_toggle_panel", icon=TOGL_ICO, emboss=False)
                    
                    if ob["rs_toggle_panel"]:
                        col.separator()
                        row = col.row()
                        rowbox = row.box()
                        col = rowbox.column()
                        
                        if ob["rs_shotshape_use"]:
                            row = col.row()
                            row.label(text="Shot Shape:")
                            row = col.row()
                            row.prop_search(ob, "rs_shotshape_shape", 
                                            scn, "objects", text="", 
                                            icon="OBJECT_DATA")
                            row = col.row(align=True)
                            row.prop(ob, "rs_shotshape_nav")
                            row.prop(ob, "rs_shotshape_nav_start")
                            row = col.row(align=True)
                            row.prop(ob, "rs_shotshape_offset")
                            row.prop(ob, "rs_shotshape_use_frames")
                            row = col.row()
                            row.operator("render.rendershots_constraints_add", 
                                        icon="CONSTRAINT_DATA").cam=ob.name
                            col.separator()
                        
                        if ob["rs_settings_use"]:
                            row = col.row()
                            row.label(text="Render Settings:")
                            row = col.row()
                            rowcol = row.column(align=True)
                            rowcol.prop(ob, "rs_resolution_x")
                            rowcol.prop(ob, "rs_resolution_y")
                            
                            rowcol = row.column()
                            if not RENDER_SETTINGS_HELP:
                                rowcol.operator("render.rendershots_settingshelp", 
                                            text="", icon="HELP").cam=ob.name
                            else:
                                rowcol.label(icon="TIME")
                            
                            if using_cycles(scn):
                                rowcol.prop(ob, "rs_cycles_samples")
                            else:
                                rowcol.label()
                            
                            col.separator()
                        
                        row = col.row()
                        row.label(text="Shot Settings:")
                        row = col.row(align=True)
                        row.prop(ob, "rs_shot_start")
                        row.prop(ob, "rs_shot_end")
                        row = col.row()
                        out = ob["rs_shot_output"]
                        row.alert = False if out != "" and not out.isspace() else True
                        row.prop(ob, "rs_shot_output")


def register():
    bpy.utils.register_module(__name__)
    init_props()
    bpy.app.handlers.render_complete.append(render_finished)

def unregister():
    bpy.app.handlers.render_complete.remove(render_finished)
    bpy.utils.unregister_module(__name__)
    
    object = bpy.types.Object
    scene = bpy.types.Scene
    
    # Camera properties
    del object.rs_shot_include
    del object.rs_shot_start
    del object.rs_shot_end
    del object.rs_shot_output
    del object.rs_toggle_panel
    
    # Render settings
    del object.rs_settings_use
    del object.rs_resolution_x
    del object.rs_resolution_y
    del object.rs_cycles_samples
    
    # Shot shapes
    del object.rs_shotshape_use
    del object.rs_shotshape_shape
    del object.rs_shotshape_nav
    del object.rs_shotshape_nav_start
    del object.rs_shotshape_offset
    del object.rs_shotshape_use_frames

    # Internal
    del scene.rs_is_updating
    del scene.rs_create_folders
    del scene.rs_main_folder
    del scene.rs_overwrite_folders

if __name__ == '__main__':
    register()
