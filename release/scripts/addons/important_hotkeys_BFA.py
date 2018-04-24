
import bpy
import bgl
import blf

# Author: Reiner "Tiles" Prokein
# Homepage: http://www.reinerstilesets.de
# Name: Important Hotkeys BFA
# Build 146

# This is the Bforartists version of the Important Hotkeys addon.
# This addon displays some important hotkeys in the upper left corner. 
# Some of them are  mode dependant. So when you are for example in edit mode, 
# then you get some edit mode hotkeys.

# This script is under Apache license

# ¸¸♫·¯·♪¸¸♩·¯·♬¸¸¸¸♫·¯·♪¸¸♩·¯·♬¸¸¸¸♫·¯·♪¸¸♩·¯·♬¸¸¸¸♫·¯·♪¸¸♩·¯·♬¸¸¸¸♫·¯·♪¸¸♩·¯·♬¸¸¸¸♫·¯·♪¸¸♩·¯·♬¸¸

bl_info = {
    "name": "Important Hotkeys BFA",
    "author": "Reiner 'Tiles' Prokein",
    "version": (1, 0, 2),
    "blender": (2, 76, 0),
    "location": "3D View > Properties Panel > Important Hotkeys",
    "description": "This addon displays some important hotkeys in the upper left corner of the 3D view",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "User Interface"}

# ---------------------- Some variables, needed to position the text

pos_x = 10 # Initial X position.
pos_y = 30 # initial Y position. This value gets substracted from the screen height.
subpos_y = 0 # needed to calculate the position of the array strings below the title.

# With this function we retreive the hotkey.
def handle_keys(km, keystring):
    
    if keystring == "Not found": # Let's make the string empty when text is "Not Found". We want to fill it with our hotkey now.
        keystring = ""
    else:     # if keystring has already a content. 
        keystring += ("  |  ") # There might be more than one hotkey. So we separate them by a | 
    if km.shift:
        keystring += "Shift " # has shift key?
    if km.ctrl:
        keystring += "Ctrl " # has control key?
    if km.alt:
        keystring += "Alt " # has alt key?
    if km.key_modifier != "NONE":
        keystring += km.key_modifier  + " " #key modifier when available. And a gap
    keystring += km.type # And finally the main key. 
    
    return keystring # calculation done, send the result back

# the mode text. drawn when an object is selected. It appends to the first part. See below, def draw_maintext
def draw_modetext(self, context, obj):
    
    # ------------ Get the hotkeys -------------------------------------------------
    wm = context.window_manager # Blender window manager
    
    # -------------------------------------- 3D View section
    keymaps_3DV = wm.keyconfigs['Blender User'].keymaps['3D View'] # Hotkeys in the '3D View' section, 'Blender User' for actual hotkeys
    
    if not self._flag: # self._flag is false     
        # print(tuple(keymaps_3DV.keymap_items.keys()))      # debug. prints the tuple content for the 3d view keymaps.
        for item, km in keymaps_3DV.keymap_items.items(): # all the items in the tuple
 
            # ------------- Move object
            if item == 'transform.translate' and km.type != "EVT_TWEAK_S":
                self.move_obj_string = handle_keys(km, self.move_obj_string) # retreive the result and set the string

            # ------------- Rotate object 
            elif item == 'transform.rotate':
                self.rotate_obj_string = handle_keys(km, self.rotate_obj_string)
                
            # ------------- Scale object 
            elif item == 'transform.resize':
                self.scale_obj_string = handle_keys(km, self.scale_obj_string)
                
     # -------------------------------------- Object Mode section         
    keymaps_OBJECTMODE = wm.keyconfigs['Blender User'].keymaps['Object Mode']
    
    if not self._flag: # self._flag is false    
        # print(tuple(keymaps_OBJECTMODE.keymap_items.keys()))      # debug. prints the tuple content for the 3d view keymaps.
        for item, km in keymaps_OBJECTMODE.keymap_items.items(): # all the items in the tuple
                
            # ------------- Make parent
            if item == 'object.parent_set':
                self.make_parent = handle_keys(km, self.make_parent) # retreive the result and set the string

            # ------------- Clear parent
            elif item == 'object.parent_clear':
                self.clear_parent = handle_keys(km, self.clear_parent)
                
            # ------------- Join meshes
            elif item == 'object.join':
                self.join_mesh = handle_keys(km, self.join_mesh)

                
    # ----------------------------------------- Mesh section -------------------------------------    
    keymaps_MESH = wm.keyconfigs['Blender User'].keymaps['Mesh']
    
    if not self._flag:
        #print(tuple(keymaps_MESH.keymap_items.keys()))      # debug. prints the tuple content for the 3d view keymaps.
        for item, km in keymaps_MESH.keymap_items.items(): # all the items in the tuple
 
            
            if item == 'mesh.select_mode':
                # ------------- Point Edit
                if km.properties.type == 'VERT':
                    self.mesh_select_verts = handle_keys(km, self.mesh_select_verts)
           
                # ------------- Edge Edit
                elif item == 'mesh.select_mode' and km.properties.type == 'EDGE':
                    self.mesh_select_edges = handle_keys(km, self.mesh_select_edges)
               
                # ------------- Face Edit
                elif item == 'mesh.select_mode' and km.properties.type == 'FACE':
                    self.mesh_select_faces = handle_keys(km, self.mesh_select_faces)

            # ------------- Pick shortest path
            elif item == 'mesh.shortest_path_pick':
                self.mesh_shortest_path = handle_keys(km, self.mesh_shortest_path)

            # ------------- extrude
            elif item == 'view3d.edit_mesh_extrude_move_normal':
                self.mesh_extrude = handle_keys(km, self.mesh_extrude)
                
            # ------------- Separate
            elif item == 'mesh.separate':
                self.mesh_separate = handle_keys(km, self.mesh_separate)
                
            elif item == 'mesh.mark_seam':
                # ------------- Mark Seam
                if km.properties.clear == False:
                    self.mesh_mark_seam = handle_keys(km, self.mesh_mark_seam)
                ## ------------- Clear Seam  - not longer valid, made new class for tooltip in bfa. See below
                #elif km.properties.clear == True:
                #    self.mesh_clear_seam = handle_keys(km, self.mesh_clear_seam)

            elif item == 'mesh.clear_seam':
                self.clear_seam = handle_keys(km, self.clear_seam)

            elif item == 'mesh.loop_select':
                # ------------- Loop select
                if km.properties.toggle == False:
                    self.mesh_loop_select = handle_keys(km, self.mesh_loop_select)
                # ------------- Loop select add
                elif km.properties.toggle == True:
                    self.mesh_loop_select_add = handle_keys(km, self.mesh_loop_select_add)
                    
            elif item == 'mesh.edgering_select':
                # ------------- Edgering select
                if km.properties.toggle == False:
                    self.mesh_edgering_select = handle_keys(km, self.mesh_edgering_select)
                # ------------- Edgering select add
                elif km.properties.toggle == True:
                    self.mesh_edgering_select_add = handle_keys(km, self.mesh_edgering_select_add)
                    
    # ----------------------------------------- Pose section -------------------------------------    
    keymaps_MESH = wm.keyconfigs['Blender User'].keymaps['Pose']
    
    if not self._flag:
        #print(tuple(keymaps_MESH.keymap_items.keys()))      # debug. prints the tuple content for the 3d view keymaps.
        for item, km in keymaps_MESH.keymap_items.items(): # all the items in the tuple
            
            # ------------- Make Parent
            if item == 'object.parent_set':
                self.pose_parent_set = handle_keys(km, self.pose_parent_set)

    # ----------------------------------------- Sculpt section -------------------------------------    
    keymaps_SCULPT = wm.keyconfigs['Blender User'].keymaps['Sculpt']
    
    if not self._flag:
        #print(tuple(keymaps_SCULPT.keymap_items.keys()))      # debug. prints the tuple content for the 3d view keymaps.
        for item, km in keymaps_SCULPT.keymap_items.items(): # all the items in the tuple
             
            if item == 'wm.radial_control':
                # ------------- Brush Size
                if km.properties.data_path_primary == "tool_settings.sculpt.brush.size" and km.properties.data_path_secondary == "tool_settings.unified_paint_settings.size" and km.properties.use_secondary == "tool_settings.unified_paint_settings.use_unified_size" and km.properties.rotation_path == "tool_settings.sculpt.brush.texture_slot.angle" and km.properties.color_path == "tool_settings.sculpt.brush.cursor_color_add" and km.properties.image_id == "tool_settings.sculpt.brush":
                    self.sculpt_brush_size = handle_keys(km, self.sculpt_brush_size)
                
                # ------------- Brush Strength
                elif km.properties.data_path_primary == "tool_settings.sculpt.brush.strength" and km.properties.data_path_secondary == "tool_settings.unified_paint_settings.strength" and km.properties.use_secondary == "tool_settings.unified_paint_settings.use_unified_strength" and km.properties.rotation_path == "tool_settings.sculpt.brush.texture_slot.angle" and km.properties.color_path == "tool_settings.sculpt.brush.cursor_color_add" and km.properties.image_id == "tool_settings.sculpt.brush":
                    self.sculpt_brush_strength = handle_keys(km, self.sculpt_brush_strength)
                    
                # ------------- Brush Angle
                elif km.properties.data_path_primary == "tool_settings.sculpt.brush.texture_slot.angle" and km.properties.rotation_path == "tool_settings.sculpt.brush.texture_slot.angle" and km.properties.color_path == "tool_settings.sculpt.brush.cursor_color_add" and km.properties.image_id == "tool_settings.sculpt.brush":
                    self.sculpt_brush_angle = handle_keys(km, self.sculpt_brush_angle)
                   
            elif item == 'brush.stencil_control':
                 # ------------- Stencil Brush control Translation
                if km.properties.mode == 'TRANSLATION' and km.properties.texmode == 'PRIMARY':
                    self.stencil_control_translate = handle_keys(km, self.stencil_control_translate)

                # ------------- Stencil Brush control Translation Secondary
                elif item == 'brush.stencil_control' and km.properties.mode == 'TRANSLATION' and km.properties.texmode == 'SECONDARY':
                    self.stencil_control_translate_sec = handle_keys(km, self.stencil_control_translate_sec)
                
                # ------------- Stencil Brush control Scale
                elif item == 'brush.stencil_control' and km.properties.mode == 'SCALE' and km.properties.texmode == 'SECONDARY':
                    self.stencil_control_scale = handle_keys(km, self.stencil_control_scale)
                
    # ----------------------------------------- Vertexpaint section -------------------------------------    
    keymaps_VERTEXPAINT = wm.keyconfigs['Blender User'].keymaps['Vertex Paint']
    
    if not self._flag:
        #print(tuple(keymaps_VERTEXPAINT.keymap_items.keys()))      # debug. prints the tuple content for the 3d view keymaps.
        for item, km in keymaps_VERTEXPAINT.keymap_items.items(): # all the items in the tuple
 
            
            if item == 'wm.radial_control':
                # ------------- Brush Size
                if km.properties.data_path_primary == "tool_settings.vertex_paint.brush.size" and km.properties.data_path_secondary == "tool_settings.unified_paint_settings.size" and km.properties.use_secondary == "tool_settings.unified_paint_settings.use_unified_size" and km.properties.rotation_path == "tool_settings.vertex_paint.brush.texture_slot.angle" and km.properties.color_path == "tool_settings.vertex_paint.brush.cursor_color_add" and km.properties.fill_color_path == "tool_settings.vertex_paint.brush.color" and km.properties.image_id == "tool_settings.vertex_paint.brush":
                    self.vertexpaint_brush_size = handle_keys(km, self.vertexpaint_brush_size)
                
                # ------------- Brush Strength
                elif km.properties.data_path_primary == "tool_settings.vertex_paint.brush.strength" and km.properties.data_path_secondary == "tool_settings.unified_paint_settings.strength" and km.properties.use_secondary == "tool_settings.unified_paint_settings.use_unified_strength" and km.properties.rotation_path == "tool_settings.vertex_paint.brush.texture_slot.angle" and km.properties.color_path == "tool_settings.vertex_paint.brush.cursor_color_add" and km.properties.fill_color_path == "tool_settings.vertex_paint.brush.color" and km.properties.image_id == "tool_settings.vertex_paint.brush":
                    self.vertexpaint_brush_strength = handle_keys(km, self.vertexpaint_brush_strength)
                    
                # ------------- Brush Angle
                elif km.properties.data_path_primary == "tool_settings.vertex_paint.brush.texture_slot.angle" and km.properties.data_path_secondary == "" and km.properties.use_secondary == "" and km.properties.rotation_path == "tool_settings.vertex_paint.brush.texture_slot.angle" and km.properties.color_path == "tool_settings.vertex_paint.brush.cursor_color_add" and km.properties.fill_color_path == "tool_settings.vertex_paint.brush.color" and km.properties.image_id == "tool_settings.vertex_paint.brush":
                    self.vertexpaint_brush_angle = handle_keys(km, self.vertexpaint_brush_angle)
                
        
            elif item == 'brush.stencil_control':
                # ------------- Stencil Brush control Translation
                if km.properties.mode == 'TRANSLATION' and km.properties.texmode == 'PRIMARY':
                    self.vertexpaint_stencil_control_translate = handle_keys(km, self.vertexpaint_stencil_control_translate)
                
            # ------------- Stencil Brush control Scale
                elif km.properties.mode == 'SCALE' and km.properties.texmode == 'PRIMARY':
                    self.vertexpaint_stencil_control_scale = handle_keys(km, self.vertexpaint_stencil_control_scale)
                    
            # ------------- Stencil Brush control Rotation
                elif km.properties.mode == 'ROTATION' and km.properties.texmode == 'PRIMARY':
                    self.vertexpaint_stencil_control_rotate = handle_keys(km, self.vertexpaint_stencil_control_rotate)
                    
                # ------------- Stencil Brush control Translation Secondary
                elif km.properties.mode == 'TRANSLATION' and km.properties.texmode == 'SECONDARY':
                    self.vertexpaint_stencil_control_translate_sec = handle_keys(km, self.vertexpaint_stencil_control_translate_sec)
                    
            # ------------- Stencil Brush control Scale Secondary
                elif km.properties.mode == 'SCALE' and km.properties.texmode == 'SECONDARY':
                    self.vertexpaint_stencil_control_scale_sec = handle_keys(km, self.vertexpaint_stencil_control_scale_sec)
                    
            # ------------- Stencil Brush control Rotation Secondary
                elif km.properties.mode == 'ROTATION' and km.properties.texmode == 'SECONDARY':
                    self.vertexpaint_stencil_control_rotate_sec = handle_keys(km, self.vertexpaint_stencil_control_rotate_sec)
                    
     # ----------------------------------------- Weightpaint section -------------------------------------    
    keymaps_WEIGHTPAINT = wm.keyconfigs['Blender User'].keymaps['Weight Paint']
    
    if not self._flag:
        #print(tuple(keymaps_WEIGHTPAINT.keymap_items.keys()))      # debug. prints the tuple content for the 3d view keymaps.
        for item, km in keymaps_WEIGHTPAINT.keymap_items.items(): # all the items in the tuple
            
            # ------------- Select bone
            if item == 'paint.weight_sample':
                self.weightpaint_bone_select = handle_keys(km, self.weightpaint_bone_select)
            # ------------- Select bone
            if item == 'paint.weight_gradient':
                self.weightpaint_draw_gradient = handle_keys(km, self.weightpaint_draw_gradient)
            
            elif item == 'wm.radial_control':
                # ------------- Brush Size
                if km.properties.data_path_primary == "tool_settings.weight_paint.brush.size" and km.properties.data_path_secondary == "tool_settings.unified_paint_settings.size" and km.properties.use_secondary == "tool_settings.unified_paint_settings.use_unified_size" and km.properties.rotation_path == "tool_settings.weight_paint.brush.texture_slot.angle" and km.properties.color_path == "tool_settings.weight_paint.brush.cursor_color_add" and km.properties.image_id == "tool_settings.weight_paint.brush":
                    self.weightpaint_brush_size = handle_keys(km, self.weightpaint_brush_size)
                
                # ------------- Brush Strength
                elif km.properties.data_path_primary == "tool_settings.weight_paint.brush.strength" and km.properties.data_path_secondary == "tool_settings.unified_paint_settings.strength" and km.properties.use_secondary == "tool_settings.unified_paint_settings.use_unified_strength" and km.properties.rotation_path == "tool_settings.weight_paint.brush.texture_slot.angle" and km.properties.color_path == "tool_settings.weight_paint.brush.cursor_color_add" and km.properties.image_id == "tool_settings.weight_paint.brush":
                    self.weightpaint_brush_strength = handle_keys(km, self.weightpaint_brush_strength)
                    
                # ------------- Brush weight
                elif km.properties.data_path_primary == "tool_settings.weight_paint.brush.weight" and km.properties.data_path_secondary == "tool_settings.unified_paint_settings.weight" and km.properties.use_secondary == "tool_settings.unified_paint_settings.use_unified_weight" and km.properties.rotation_path == "tool_settings.weight_paint.brush.texture_slot.angle" and km.properties.color_path == "tool_settings.weight_paint.brush.cursor_color_add" and km.properties.image_id == "tool_settings.weight_paint.brush":
                    self.weightpaint_brush_weight = handle_keys(km, self.weightpaint_brush_weight)
                
        
            elif item == 'brush.stencil_control':
                # ------------- Stencil Brush control Translation
                if km.properties.mode == 'TRANSLATION' and km.properties.texmode == 'PRIMARY':
                    self.weightpaint_stencil_control_translate = handle_keys(km, self.weightpaint_stencil_control_translate)
                
                # ------------- Stencil Brush control Scale
                elif km.properties.mode == 'SCALE' and km.properties.texmode == 'PRIMARY':
                    self.weightpaint_stencil_control_scale = handle_keys(km, self.weightpaint_stencil_control_scale)
                    
                # ------------- Stencil Brush control Rotation
                elif km.properties.mode == 'ROTATION' and km.properties.texmode == 'PRIMARY':
                    self.weightpaint_stencil_control_rotate = handle_keys(km, self.weightpaint_stencil_control_rotate)
                    
                # ------------- Stencil Brush control Translation Secondary
                elif km.properties.mode == 'TRANSLATION' and km.properties.texmode == 'SECONDARY':
                    self.weightpaint_stencil_control_translate_sec = handle_keys(km, self.weightpaint_stencil_control_translate_sec)
                    
                # ------------- Stencil Brush control Scale Secondary
                elif km.properties.mode == 'SCALE' and km.properties.texmode == 'SECONDARY':
                    self.weightpaint_stencil_control_scale_sec = handle_keys(km, self.weightpaint_stencil_control_scale_sec)

                 # ------------- Stencil Brush control Rotation Secondary
                elif km.properties.mode == 'ROTATION' and km.properties.texmode == 'SECONDARY':
                    self.weightpaint_stencil_control_rotate_sec = handle_keys(km, self.weightpaint_stencil_control_rotate_sec)

      # ----------------------------------------- Paint Curve section -------------------------------------    
    keymaps_PAINTCURVE = wm.keyconfigs['Blender User'].keymaps['Paint Curve']
    
    if not self._flag:
        #print(tuple(keymaps_PAINTCURVE.keymap_items.keys()))      # debug. prints the tuple content for the 3d view keymaps.
        for item, km in keymaps_PAINTCURVE.keymap_items.items(): # all the items in the tuple
            
            # ------------- Select bone
            if item == 'paintcurve.add_point_slide':
                self.texturepaint_strokemethod_curve = handle_keys(km, self.texturepaint_strokemethod_curve)               
                
 # ----------------------------------------- texturepaint section -------------------------------------    
    keymaps_TEXTUREPAINT = wm.keyconfigs['Blender User'].keymaps['Image Paint']
    
    if not self._flag:
        #print(tuple(keymaps_TEXTUREPAINT.keymap_items.keys()))      # debug. prints the tuple content
        for item, km in keymaps_TEXTUREPAINT.keymap_items.items(): # all the items in the tuple
 
            
            if item == 'wm.radial_control':
                # ------------- Brush Size
                if km.properties.data_path_primary == "tool_settings.image_paint.brush.size" and km.properties.data_path_secondary == "tool_settings.unified_paint_settings.size" and km.properties.use_secondary == "tool_settings.unified_paint_settings.use_unified_size" and km.properties.rotation_path == "tool_settings.image_paint.brush.mask_texture_slot.angle" and km.properties.color_path == "tool_settings.image_paint.brush.cursor_color_add" and km.properties.fill_color_path == "tool_settings.image_paint.brush.color" and km.properties.zoom_path == "space_data.zoom" and km.properties.image_id == "tool_settings.image_paint.brush" and km.properties.secondary_tex == True:
                    self.texturepaint_brush_size = handle_keys(km, self.texturepaint_brush_size)
                
                # ------------- Brush Strength
                elif km.properties.data_path_primary == "tool_settings.image_paint.brush.strength" and km.properties.data_path_secondary == "tool_settings.unified_paint_settings.strength" and km.properties.use_secondary == "tool_settings.unified_paint_settings.use_unified_strength" and km.properties.rotation_path == "tool_settings.image_paint.brush.mask_texture_slot.angle" and km.properties.color_path == "tool_settings.image_paint.brush.cursor_color_add" and km.properties.fill_color_path == "tool_settings.image_paint.brush.color" and km.properties.image_id == "tool_settings.image_paint.brush" and km.properties.secondary_tex == True:
                    self.texturepaint_brush_strength = handle_keys(km, self.texturepaint_brush_strength)
                    
                # ------------- Brush angle
                elif km.properties.data_path_primary == "tool_settings.image_paint.brush.texture_slot.angle" and km.properties.rotation_path == "tool_settings.image_paint.brush.texture_slot.angle" and km.properties.color_path == "tool_settings.image_paint.brush.cursor_color_add" and km.properties.fill_color_path == "tool_settings.image_paint.brush.color" and km.properties.image_id == "tool_settings.image_paint.brush" and km.properties.secondary_tex == False:
                    self.texturepaint_brush_angle = handle_keys(km, self.texturepaint_brush_angle)
                    
                # ------------- Mask angle
                elif km.properties.data_path_primary == "tool_settings.image_paint.brush.mask_texture_slot.angle" and km.properties.rotation_path == "tool_settings.image_paint.brush.mask_texture_slot.angle" and km.properties.color_path == "tool_settings.image_paint.brush.cursor_color_add" and km.properties.fill_color_path == "tool_settings.image_paint.brush.color" and km.properties.image_id == "tool_settings.image_paint.brush" and km.properties.secondary_tex == True:
                    self.texturepaint_mask_angle = handle_keys(km, self.texturepaint_mask_angle)
                          
            
            elif item == 'brush.stencil_control':
                # ------------- Stencil Brush control Translation
                if km.properties.mode == 'TRANSLATION' and km.properties.texmode == 'PRIMARY':
                    self.texturepaint_stencil_control_translate = handle_keys(km, self.texturepaint_stencil_control_translate)
                
                # ------------- Stencil Brush control Scale
                elif km.properties.mode == 'SCALE' and km.properties.texmode == 'PRIMARY':
                    self.texturepaint_stencil_control_scale = handle_keys(km, self.texturepaint_stencil_control_scale)
                    
                # ------------- Stencil Brush control Rotation
                elif km.properties.mode == 'ROTATION' and km.properties.texmode == 'PRIMARY':
                    self.texturepaint_stencil_control_rotate = handle_keys(km, self.texturepaint_stencil_control_rotate)
                    
                # ------------- Stencil Brush control Translation Secondary
                elif km.properties.mode == 'TRANSLATION' and km.properties.texmode == 'SECONDARY':
                    self.texturepaint_stencil_control_translate_sec = handle_keys(km, self.texturepaint_stencil_control_translate_sec)
                    
                # ------------- Stencil Brush control Scale Secondary
                elif km.properties.mode == 'SCALE' and km.properties.texmode == 'SECONDARY':
                    self.texturepaint_stencil_control_scale_sec = handle_keys(km, self.texturepaint_stencil_control_scale_sec)
                    
                # ------------- Stencil Brush control Rotation Secondary
                elif km.properties.mode == 'ROTATION' and km.properties.texmode == 'SECONDARY':
                    self.texturepaint_stencil_control_rotate_sec = handle_keys(km, self.texturepaint_stencil_control_rotate_sec)
                
 # ----------------------------------------- Particle section -------------------------------------    
    keymaps_PARTICLE = wm.keyconfigs['Blender User'].keymaps['Particle']
    
    if not self._flag:
        #print(tuple(keymaps_PARTICLE.keymap_items.keys()))      # debug. prints the tuple content
        for item, km in keymaps_PARTICLE.keymap_items.items(): # all the items in the tuple
 
            
            if item == 'wm.radial_control':
                # ------------- Brush Size
                if km.properties.data_path_primary == "tool_settings.particle_edit.brush.size":
                    self.particle_brush_size = handle_keys(km, self.particle_brush_size)
                
                # ------------- Brush Strength
                elif item == 'wm.radial_control' and km.properties.data_path_primary == "tool_settings.particle_edit.brush.strength":  
                    self.particle_brush_strength = handle_keys(km, self.particle_brush_strength)

 # ----------------------------------------- Curve section -------------------------------------    
    keymaps_CURVE = wm.keyconfigs['Blender User'].keymaps['Curve']
    
    if not self._flag:
        #print(tuple(keymaps_CURVE.keymap_items.keys()))      # debug. prints the tuple content
        for item, km in keymaps_CURVE.keymap_items.items(): # all the items in the tuple
 
            # ------------- Extrude
            if item == 'curve.extrude_move':
                self.curve_extrude = handle_keys(km, self.curve_extrude)
                
            # ------------- add vertex
            elif item == 'curve.vertex_add':
                self.curve_vertex_add = handle_keys(km, self.curve_vertex_add)

 # ----------------------------------------- Armature section -------------------------------------    
    keymaps_ARMATURE = wm.keyconfigs['Blender User'].keymaps['Armature']
    
    if not self._flag:
        #print(tuple(keymaps_ARMATURE.keymap_items.keys()))      # debug. prints the tuple content
        for item, km in keymaps_ARMATURE.keymap_items.items(): # all the items in the tuple
 
            # ------------- Extrude
            if item == 'armature.extrude_move':
                self.armature_extrude = handle_keys(km, self.armature_extrude) 
                
            # ------------- Extrude forked
            elif item == 'armature.extrude_forked':
                self.armature_extrude_forked = handle_keys(km, self.armature_extrude_forked)
                
             # ------------- Make parent
            elif item == 'armature.parent_set':
                self.armature_parent_set = handle_keys(km, self.armature_parent_set) 
                
            # ------------- Clear parent
            elif item == 'armature.parent_clear':
                handle_keys(km, self.armature_parent_clear)
                self.armature_parent_clear = handle_keys(km, self.armature_parent_clear)
                
            # ------------- Separate bones
            elif item == 'armature.separate':
                self.armature_separate = handle_keys(km, self.armature_separate)
 
            elif item == 'sketch.draw_stroke':
                # ------------- Skeleton sketching draw stroke
                if km.properties.snap == False:
                    self.armature_sketching_draw = handle_keys(km, self.armature_sketching_draw)
                
                # ------------- Skeleton sketching draw stroke snap   
                elif km.properties.snap == True:
                    self.armature_sketching_draw_snap = handle_keys(km, self.armature_sketching_draw_snap)
                    
            elif item == 'sketch.draw_preview':
                # ------------- Skeleton sketching draw preview sketching 
                if km.properties.snap == False:
                    self.armature_sketching_preview = handle_keys(km, self.armature_sketching_preview)
                
                # ------------- Skeleton sketching draw preview sketching snap 
                elif km.properties.snap == True:
                    self.armature_sketching_preview_snap = handle_keys(km, self.armature_sketching_preview_snap)
                    
            # ------------- Skeleton sketching finish stroke
            elif item == 'sketch.finish_stroke':
                self.armature_sketching_finish_stroke = handle_keys(km, self.armature_sketching_finish_stroke) 

        self._flag = True # One time goingh through the tuples and setting the strings is enough.
    
    # ----------------------------------------------------------------------------   
    
    scene   = context.scene
    mode = obj.mode # The different modes

    texts = [] # Our text array

    if mode == 'OBJECT':
        if obj.type == 'MESH':
            texts.append(([
                "------",
                "Move - 1 x " + self.move_obj_string,
                "Rotate - 1 x " + self.rotate_obj_string,
                "Scale - 1 x " + self.scale_obj_string,
                "Trackball - 2 x " + self.rotate_obj_string,
                "------",
                "Set Parent - " + self.make_parent,
                "Clear Parent - " + self.clear_parent,
                "Join Mesh - " + self.join_mesh,
                ]))

        elif obj.type:
            texts.append(([
                "------",
                "Move - 1 x "+ self.move_obj_string,
                "Rotate - 1 x "+ self.rotate_obj_string,
                "Scale - 1 x " + self.scale_obj_string,
                "Trackball - 2 x "+ self.rotate_obj_string,
                "------",
                "Set Parent - "+ self.make_parent,
                "Clear Parent - "+ self.clear_parent,
                ]))
    elif mode == 'EDIT':
        if obj.type == 'MESH':
            texts.append(([
                "------",
                "Move - 1 x "+ self.move_obj_string,
                "Rotate - 1 x "+ self.rotate_obj_string,
                "Scale - 1 x "+ self.scale_obj_string,
                "Trackball - 2 x "+ self.rotate_obj_string,
                "Vertex Slide - 2 x "+ self.move_obj_string,
                "------",
                "Point Select Mode - " + self.mesh_select_verts,
                "Edge Select Mode - " + self.mesh_select_edges,
                "Face Select Mode - " + self.mesh_select_faces,
                "------",
                "Pick shortest path - " + self.mesh_shortest_path,
                "Extrude - " + self.mesh_extrude,
                "Separate - " + self.mesh_separate,
                "------",
                "Select Edgeloop - " + self.mesh_loop_select,
                "Add Edgeloop to selection - " + self.mesh_loop_select_add,
                "Select Edgering - " + self.mesh_edgering_select,
                "Add Edgering to selection - " + self.mesh_edgering_select_add,
                "Mark Seam - " + self.mesh_mark_seam,
                "Clear Seam - " + self.clear_seam,
                ]))
        elif obj.type == 'CURVE':
            texts.append(([
                "------",
                "Move - 1 x "+ self.move_obj_string,
                "Rotate - 1 x "+ self.rotate_obj_string,
                "Scale - 1 x "+ self.scale_obj_string,
                "Trackball - 2 x "+ self.rotate_obj_string,
                "------",
                "Extrude - " + self.curve_extrude,
                "Add Vertex - " + self.curve_vertex_add,
                ]))
        # Has Surface the same hotkey set than curve? Unsure
        elif obj.type == 'SURFACE':
            texts.append(([
                "------",
                "Move - 1 x "+ self.move_obj_string,
                "Rotate - 1 x "+ self.rotate_obj_string,
                "Scale - 1 x "+ self.scale_obj_string,
                "Trackball - 2 x "+ self.rotate_obj_string,
                "------",
                "Extrude - " + self.curve_extrude,
                "Add Vertex - " + self.curve_vertex_add,
                ]))
        elif obj.type == 'FONT':
            texts.append(([
                "------",
                "Move - 1 x "+ self.move_obj_string,
                "Rotate - 1 x "+ self.rotate_obj_string,
                "Scale - 1 x "+ self.scale_obj_string,
                "Trackball - 2 x "+ self.rotate_obj_string,
                "------",
                "Text object in edit mode works like in a text editor",
                "Note that some hotkeys don't work.",
                "Their keystrokes gets captured by the text object."
                ]))
        elif obj.type == 'MBALL':
            texts.append(([
                "------",
                "Move - 1 x "+ self.move_obj_string,
                "Rotate - 1 x "+ self.rotate_obj_string,
                "Scale - 1 x "+ self.scale_obj_string,
                "Trackball - 2 x "+ self.rotate_obj_string
                ]))
        elif obj.type == 'LATTICE':
            texts.append(([
                "------",
                "Move - 1 x "+ self.move_obj_string,
                "Rotate - 1 x "+ self.rotate_obj_string,
                "Scale - 1 x "+ self.scale_obj_string,
                "Trackball - 2 x "+ self.rotate_obj_string,
                ]))
        elif obj.type == 'ARMATURE':
            texts.append(([
                "------",
                "Move - 1 x "+ self.move_obj_string,
                "Rotate - 1 x "+ self.rotate_obj_string,
                "Scale - 1 x "+ self.scale_obj_string,
                "Trackball - 2 x "+ self.rotate_obj_string,
                "------",
                "Extrude - " + self.armature_extrude,
                "Extrude forked (2 or more joints) - " + self.armature_extrude_forked,
                "Make Parent - " + self.armature_parent_set,
                "Clear Parent - " + self.armature_parent_clear,
                "Separate Bones - " + self.armature_separate,
                "------",
                "For Skeleton Sketching:",
                "Draw Stroke - " + self.armature_sketching_draw,
                "Draw Stroke snap - " + self.armature_sketching_draw_snap,
                "Draw Preview - " + self.armature_sketching_preview,
                "Draw Preview snap - " + self.armature_sketching_preview_snap,
                "Finish stroke - " + self.armature_sketching_finish_stroke
                ]))                
                
    elif mode == 'SCULPT':
        texts.append(([
            "------",
            "Radial Control Keys:",
            "Brush size - " + self.sculpt_brush_size,
            "Brush strength - " + self.sculpt_brush_strength,
            "Brush angle - " + self.sculpt_brush_angle,
            "------",
            "Texture, Brush Mapping in Stencil mode:", 
            "Move - " + self.stencil_control_translate,
            "Move Secondary - " + self.stencil_control_translate_sec,
            "Scale - " + self.stencil_control_scale
            ]))
    elif mode == 'VERTEX_PAINT':
        texts.append(([
            "------",
            "Radial Control Keys:",
            "Radius - " + self.vertexpaint_brush_size,
            "Strength -  " + self.vertexpaint_brush_strength,
            "Angle - " + self.vertexpaint_brush_angle,
            "------",
            "Texture, Brush Mapping in Stencil mode:", 
            "Move - " + self.vertexpaint_stencil_control_translate,
            "Rotate - " + self.vertexpaint_stencil_control_rotate,
            "Scale - " + self.vertexpaint_stencil_control_scale,
            "Move secondary - " + self.vertexpaint_stencil_control_translate_sec,
            "Rotate secondary - " + self.vertexpaint_stencil_control_rotate_sec,
            "Scale secondary - " + self.vertexpaint_stencil_control_scale_sec
            ]))
    elif mode == 'WEIGHT_PAINT':
        texts.append(([
            "------",
            "Select Bone for weightpainting - " + self.weightpaint_bone_select,
            "Draw Gradient - " + self.weightpaint_draw_gradient,
            "------",
            "Radial Control Keys:",
            "Radius - " + self.weightpaint_brush_size,
            "Strength -  " + self.weightpaint_brush_strength,
            "Weight - " + self.weightpaint_brush_weight,
            "------",
            "Texture, Brush Mapping in Stencil mode:", 
            "Move - " + self.weightpaint_stencil_control_translate,
            "Rotate - " + self.weightpaint_stencil_control_rotate,
            "Scale - " + self.weightpaint_stencil_control_scale,
            "Move secondary - " + self.weightpaint_stencil_control_translate_sec,
            "Rotate secondary - " + self.weightpaint_stencil_control_rotate_sec,
            "Scale secondary - " + self.weightpaint_stencil_control_scale_sec
            ]))
    elif mode == 'TEXTURE_PAINT':
        texts.append(([
            "------",
            "Radial Control Keys:",
            "Radius - " + self.texturepaint_brush_size,
            "Strength -  " + self.texturepaint_brush_strength,
            "Angle - " + self.texturepaint_brush_angle,
            "Mask Angle - " + self.texturepaint_mask_angle,
            "------",
            "Texture Paint, Brush Mapping in Stencil mode:", 
            "Move - " + self.texturepaint_stencil_control_translate,
            "Rotate - " + self.texturepaint_stencil_control_rotate,
            "Scale - " + self.texturepaint_stencil_control_scale,
            "Move secondary - " + self.texturepaint_stencil_control_translate_sec,
            "Rotate secondary - " + self.texturepaint_stencil_control_rotate_sec,
            "Scale secondary - " + self.texturepaint_stencil_control_scale_sec,
            "------",
            "Texture Paint, Stroke, Stroke Method Curve:", 
            "Add Curve Point - " + self.texturepaint_strokemethod_curve,
            ]))
    elif mode == 'PARTICLE_EDIT':
        texts.append(([
            "------",
            "Radial Control Keys (Brush is not None):",
            "Radius - " + self.particle_brush_size,
            "Strength -  " + self.particle_brush_strength,
            ]))
    elif mode == 'POSE':
        texts.append(([
            "------",
            "Make Parent - "+ self.pose_parent_set,
            ]))


            
    self.mod_Y = 8.2 * scene.important_hotkeys_font_size # our second text block needs a bit offset. Every new line adds 0.55. Plus a bit more because of the + 1 to have a spacing between the lines.
    
    # Draw the text
    for data in texts:
        subpos_y = context.region.height-pos_y-context.scene.important_hotkeys_font_size-self.mod_Y # initial texts position
        for d in data:
            blf.position(0, pos_x, subpos_y-self.mod_Y, 0)
            blf.draw(0, d)
            subpos_y -= context.scene.important_hotkeys_font_size + 1 # Our spacing between the lines is the font size plus 1 to have a gap between the lines.
            

# The main text. Always shown. Navigation is the same everywhere.
def draw_maintext(self, context):

    # ------------ Get the hotkeys -------------------------------------------------
    
    wm            = bpy.context.window_manager # Blender window manager
    keymaps_3DV   = wm.keyconfigs['Blender User'].keymaps['3D View'] # 3D View hotkeys
    
    # ------------------------ 3d view section
    if self._flag2 == False:
        
        self.select_with = bpy.context.user_preferences.inputs.select_mouse # Select with left or right
        
        for item, km in keymaps_3DV.keymap_items.items(): # all the items in the tuple
            
            # ------------- Add to selection
            if item == 'view3d.select':
                if km.properties.extend == False and km.properties.deselect == False and km.properties.toggle == True and km.properties.center == False and km.properties.enumerate == False and km.properties.object == False:
                    self.add_to_selection = handle_keys(km, self.add_to_selection)
                    
            # ------------- Move viewport
            elif item == 'view3d.move':
                self.move_view_string = handle_keys(km, self.move_view_string)

            # ------------- Rotate viewport
            elif item == 'view3d.rotate':
                self.rotate_view_string = handle_keys(km, self.rotate_view_string)

            # ------------- Zoom viewport
            elif item == 'view3d.zoom':
                self.zoom_view_string = handle_keys(km, self.zoom_view_string)
                
            # Reset 3D View is a plugin, and might not be installed.
            elif item == 'view.reset_3d_view':
                self.resetview_string = handle_keys(km, self.resetview_string)
                
            # Switch to camera
            elif item == 'view3d.viewnumpad' and km.properties.type == 'CAMERA':
                self.switch_to_camera = handle_keys(km, self.switch_to_camera)
                
            # Set 3d cursor
            elif item == 'view3d.cursor3d':
                self.set_3d_cursor = handle_keys(km, self.set_3d_cursor)
                
    # -------------------- Screen section
    keymaps_3DV   = wm.keyconfigs['Blender User'].keymaps['Screen']
    
    if self._flag2 == False:
        
        for item, km in keymaps_3DV.keymap_items.items(): # all the items in the tuple
                  
            # Render image
            if item == 'render.render' and km.properties.animation == False:
                self.render_image = handle_keys(km, self.render_image)
                
            # Show/Hide Renderview
            if item == 'render.view_show':
                self.render_view_show = handle_keys(km, self.render_view_show)
                
    # ---------------------- Window section
    keymaps_WIN   = wm.keyconfigs['Blender User'].keymaps['Window']
    
    if self._flag2 == False:
        
        for item, km in keymaps_WIN.keymap_items.items(): # all the items in the tuple
                  
            # Render image
            if item == 'wm.search_menu':
                self.search_menu = handle_keys(km, self.search_menu)

    # ---------------------- Grease Pencil section
    keymaps_GPENCIL   = wm.keyconfigs['Blender User'].keymaps['Grease Pencil']
    keymaps_STROKEEDIT   = wm.keyconfigs['Blender User'].keymaps['Grease Pencil Stroke Edit Mode']
    
    if self._flag2 == False:
        
        for item, km in keymaps_GPENCIL.keymap_items.items(): # all the items in the tuple
            #print(tuple(keymaps_GPENCIL.keymap_items.keys()))      # debug. prints the tuple content

            if item == 'wm.call_menu_pie':
                if km.properties.name == 'GPENCIL_MT_pie_tool_palette':
                    self.gpencil_tool_pie = handle_keys(km, self.gpencil_tool_pie)

                if km.properties.name == 'GPENCIL_MT_pie_settings_palette':
                    self.gpencil_settings_pie = handle_keys(km, self.gpencil_settings_pie)

        for item, km in keymaps_STROKEEDIT.keymap_items.items(): # all the items in the tuple
            #print(tuple(keymaps_STROKEEDIT.keymap_items.keys()))      # debug. prints the tuple content

            if item == 'wm.call_menu_pie':
                if km.properties.name == 'GPENCIL_MT_pie_sculpt':
                    self.gpencil_sculpt_pie = handle_keys(km, self.gpencil_sculpt_pie)


  
    self._flag2 = True # One time goingh through the tuple and set the strings is enough.
    
    # ------------------- Draw the text

    font_id = 0  # XXX, need to find out how best to get this.
    
    # color variables
    font_color_r, font_color_g, font_color_b, font_color_alpha = context.scene.important_hotkeys_text_color

    # Calculate the text
    blf.position(0, pos_x, context.region.height-pos_y, 0) #titleposition
    blf.size(font_id, context.scene.important_hotkeys_font_size, 72)
    bgl.glColor4f(font_color_r, font_color_g, font_color_b, font_color_alpha * 0.8) # color variables

    
    
    texts = []
    texts.append(([
        "Important hotkeys",
        " ",
        "Select with - "+ self.select_with + " Mouse Button",
        "Add to / subtract from selection - "+ self.add_to_selection,
        "Selection methods Circle, Border and Lasso select can be negated by holding Shift key",
        "Move view - "+ self.move_view_string,
        "Rotate view - "+ self.rotate_view_string,
        "Zoom view - " + self.zoom_view_string,
        "Reset 3D view - " + self.resetview_string,
        "Set 3D Cursor - " + self.set_3d_cursor,
        "Search Menu - " + self.search_menu,
        "------",
        "Switch to / from Camera view - " + self.switch_to_camera,
        "Render image - " + self.render_image,
        "Show/Hide Renderview - " + self.render_view_show
        ]))

    # We need some entries for the grease pencil mode too. The method with the empty lines is a dirty one. 
    # But working. The alternative would have been a third text block. Do not want. 
    # This method is easier to implement and to maintain :)

    gp_edit = context.gpencil_data and context.gpencil_data.use_stroke_edit_mode
    if gp_edit:
        texts.append(([
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "------",
            "Grease Pencil Tools Pie menu - " + self.gpencil_tool_pie,
            "Grease Pencil Settings Pie menu - " + self.gpencil_settings_pie,
            "Grease Pencil Sculpting Pie menu - " + self.gpencil_sculpt_pie,
            ]))
    
    # Draw the text
    for data in texts:
        subpos_y = context.region.height-pos_y-context.scene.important_hotkeys_font_size # initial texts position
        for d in data:
            blf.position(0, pos_x, subpos_y, 0)
            blf.draw(0, d)
            subpos_y -= context.scene.important_hotkeys_font_size + 1 # Our spacing between the lines is the font size plus 1 to have a gap between the lines.
            
            
    # the second part of the text. When an object is selected ... 
    # This one goes to the def draw_modetext
    if context.active_object:
        draw_modetext(self, context, context.active_object)
    
# ----------------------- Mainclass. Here happens the work.

class ModalDrawOperator(bpy.types.Operator):
    """Shows a list with important hotkeys"""
    bl_idname = "view3d.modal_operator"
    bl_label = "Simple Modal View3D Operator"
    
    # We need to limit the check loop so that it only runs once. 
    # For that we need the involved variables to be accessible across the functions
    # And a flag so that the stuff runs just onc
    def __init__(self):
        self._flag = False # our run once flag for the modal text
        self._flag2 = False # our run once flag for the fixed text
        self.mod_Y = 0
        
        # ------------Fixed strings
        # 3d view
        self.select_with = "Not found"
        self.add_to_selection = "Not found"
        self.move_view_string = "Not found"
        self.rotate_view_string = "Not found"
        self.zoom_view_string = "Not found"
        self.resetview_string = "Not found" # plugin reset 3d view
        self.set_3d_cursor = "Not found" # plugin reset 3d view
        # Window
        self.search_menu = "Not found" # plugin reset 3d view
        # Grease Pencil
        self.gpencil_tool_pie = "Not found"
        self.gpencil_settings_pie = "Not found"
        self.gpencil_sculpt_pie = "Not found"
        # Screen
        self.switch_to_camera = "Not found"
        self.render_image = "Not found" 
        self.render_view_show = "Not found"  
        # ---------- Modal strings
        # 3D View
        self.move_obj_string = "Not found"
        self.rotate_obj_string = "Not found"
        self.scale_obj_string = "Not found"
        # Object Mode
        self.make_parent = "Not found"
        self.clear_parent = "Not found"
        self.join_mesh = "Not found"
        # Mesh
        self.mesh_select_verts = "Not found"
        self.mesh_select_edges = "Not found"
        self.mesh_select_faces = "Not found"
        self.mesh_shortest_path = "Not found"
        self.mesh_extrude = "Not found"
        self.mesh_separate = "Not found"
        self.mesh_loop_select = "Not found"
        self.mesh_loop_select_add = "Not found"
        self.mesh_edgering_select = "Not found"
        self.mesh_edgering_select_add = "Not found"
        self.mesh_mark_seam = "Not found"
        self.clear_seam = "Not found"
        # Pose
        self.pose_parent_set = "Not found"
        # Sculpt
        self.sculpt_brush_size = "Not found"
        self.sculpt_brush_strength = "Not found"
        self.sculpt_brush_angle = "Not found"
        self.stencil_control_translate = "Not found"
        self.stencil_control_translate_sec = "Not found"
        self.stencil_control_scale = "Not found"
        # Vertexpaint
        self.vertexpaint_brush_size = "Not found"
        self.vertexpaint_brush_strength = "Not found"
        self.vertexpaint_brush_angle = "Not found"
        self.vertexpaint_stencil_control_translate = "Not found"
        self.vertexpaint_stencil_control_rotate = "Not found"
        self.vertexpaint_stencil_control_scale = "Not found"
        self.vertexpaint_stencil_control_translate_sec = "Not found"
        self.vertexpaint_stencil_control_rotate_sec = "Not found"
        self.vertexpaint_stencil_control_scale_sec = "Not found"
        # Weightpaint
        self.weightpaint_bone_select = "Not found"
        self.weightpaint_draw_gradient = "Not found"
        self.weightpaint_brush_size = "Not found"
        self.weightpaint_brush_strength = "Not found"
        self.weightpaint_brush_weight = "Not found"
        self.weightpaint_stencil_control_translate = "Not found"
        self.weightpaint_stencil_control_rotate = "Not found"
        self.weightpaint_stencil_control_scale = "Not found"
        self.weightpaint_stencil_control_translate_sec = "Not found"
        self.weightpaint_stencil_control_rotate_sec = "Not found"
        self.weightpaint_stencil_control_scale_sec = "Not found"
        # Texturepaint
        self.texturepaint_brush_size = "Not found"
        self.texturepaint_brush_strength = "Not found"
        self.texturepaint_brush_angle = "Not found"
        self.texturepaint_mask_angle = "Not found"
        self.texturepaint_stencil_control_translate = "Not found"
        self.texturepaint_stencil_control_rotate = "Not found"
        self.texturepaint_stencil_control_scale = "Not found"
        self.texturepaint_stencil_control_translate_sec = "Not found"
        self.texturepaint_stencil_control_rotate_sec = "Not found"
        self.texturepaint_stencil_control_scale_sec = "Not found"
        self.texturepaint_strokemethod_curve = "Not found"
        # Particle Edit
        self.particle_brush_size = "Not found"
        self.particle_brush_strength = "Not found"
        # Curve
        self.curve_extrude = "Not found"
        self.curve_vertex_add ="Not found"
        # Armature
        self.armature_extrude = "Not found"
        self.armature_extrude_forked = "Not found"
        self.armature_parent_set = "Not found"
        self.armature_parent_clear = "Not found"
        self.armature_separate = "Not found"
        self.armature_sketching_draw = "Not found"
        self.armature_sketching_draw_snap = "Not found"
        self.armature_sketching_preview = "Not found"
        self.armature_sketching_preview_snap = "Not found"
        self.armature_sketching_finish_stroke = "Not found"
       
            
    # Our modal function. The text will display as long as it is not cancelled.
    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()
            
            if not context.window_manager.showhide_flag:
                # stop script
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                return {'CANCELLED'}
            
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            if context.window_manager.showhide_flag is False:
                context.window_manager.showhide_flag = True # operator is called for the first time, start everything
                
                # Add draw handler
                self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_maintext, (self, context), 'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)
                
                return {'RUNNING_MODAL'}
            else:
                # operator is called again, stop displaying
                context.window_manager.showhide_flag = False
                self.key = []
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

#------------------------ Menu - a buttton in the 3d View in the Properties sidebar in the Show Text panel

class VIEW3D_PT_ShowtextPanel(bpy.types.Panel):
    bl_label = "Important Hotkeys"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    def draw(self, context):
        sc = context.scene
        layout = self.layout
        
        wm = context.window_manager

        if not wm.showhide_flag:
            layout.operator("view3d.modal_operator", text="Show text")
        else:
            layout.operator("view3d.modal_operator", text="Hide text")
        # --------------------------- color and text variables   

        # one method to split the elements
        # create column to be able to merge vertically with align=true on a column
        #col = layout.column(align=True)
        # create the test2 row within column and allow horizontal merge with align=true on this row
        #row = col.row(align=True)
        # we don't want to put anything else on this row other than the 'split' item
        #split = row.split(align=True, percentage=0.2)
        # put 2 things inside the split
        #split.prop(sc , "important_hotkeys_text_color", text="")
        #split.prop(sc, "important_hotkeys_font_size", text="Fontsize")
        
        # another method to split the elements
        row = layout.row(align=True)
        split = row.split(percentage=0.2)
        left_side = split.column(align=True)
        left_side.prop(sc , "important_hotkeys_text_color", text="")
        split = split.split()
        right_side = split.column()
        right_side.prop(sc, "important_hotkeys_font_size", text="Fontsize")
                
                  
# properties used by the script
def init_properties():
    scene = bpy.types.Scene
    wm = bpy.types.WindowManager

    # Runstate initially always set to False
    # note: it is not stored in the Scene, but in window manager.
    # I guess we could also create and use a self.showhide_flag instead.
    wm.showhide_flag = bpy.props.BoolProperty(default=False) 
    
    # the font size.
    scene.important_hotkeys_font_size = bpy.props.IntProperty(
        name="Text Size",
        description="Text size displayed on 3D View",
        default=11, min=8, max=150)
    
    # color variables
    scene.important_hotkeys_text_color = bpy.props.FloatVectorProperty(
        name="Text Color",
        description="Color for the text",
        default=(1.0, 1.0, 1.0, 1.0),
        min=0.1,
        max=1,
        subtype='COLOR',
        size=4)
        
            
# removal of properties when script is disabled
def clear_properties():
    props = (
        "showhide_flag",
        "important_hotkeys_font_size",
        "important_hotkeys_text_color", # color variables
    )
            
# -------------------------- Register - Unregister

def register():
    init_properties()  # everything initialize.
    bpy.utils.register_class(ModalDrawOperator)
    bpy.utils.register_class(VIEW3D_PT_ShowtextPanel)

def unregister():
    bpy.utils.unregister_class(ModalDrawOperator)
    bpy.utils.unregister_class(VIEW3D_PT_ShowtextPanel) 
    clear_properties() # cleaning up after the job is done

if __name__ == "__main__":
    register()
    

