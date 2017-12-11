""" An experimental new keymap for Blender.
    Work in progress!
"""

# TODO:
# - N-panel etc. appear to have hard-coded 'I' as "insert key" key.  Make that
#   user-configurable.

import bpy
import bmesh

######################
# Misc configuration
######################
DEVELOPER_HOTKEYS = False  # Weird hotkeys that only developers use

# Left mouse-button select
bpy.context.user_preferences.inputs.select_mouse = 'LEFT'

# Basic transform keys
TRANSLATE_KEY = 'F'
ROTATE_KEY = 'D'
SCALE_KEY = 'S'

# Specials Menu Key
SPECIALS_MENU_KEY = 'Q'

# Keyframe setting key
KEYFRAME_KEY = 'K'


################################
# Helper functions and classes
################################
class SetManipulator(bpy.types.Operator):
    """Set's the manipulator mode"""
    bl_idname = "view3d.manipulator_set"
    bl_label = "Set Manipulator"
    mode = bpy.props.EnumProperty(items=[("NONE", "None", ""),
                                         ("TRANSLATE", "Translate", ""),
                                         ("ROTATE", "Rotate", ""),
                                         ("SCALE", "Scale", "")],
                                         default="NONE")

    def execute(self, context):
        if self.mode == "NONE":
            context.space_data.show_manipulator = False
        elif self.mode == "TRANSLATE":
            context.space_data.show_manipulator = True
            context.space_data.use_manipulator_translate = True
            context.space_data.use_manipulator_rotate = False
            context.space_data.use_manipulator_scale = False
        elif self.mode == "ROTATE":
            context.space_data.show_manipulator = True
            context.space_data.use_manipulator_translate = False
            context.space_data.use_manipulator_rotate = True
            context.space_data.use_manipulator_scale = False
        elif self.mode == "SCALE":
            context.space_data.show_manipulator = True
            context.space_data.use_manipulator_translate = False
            context.space_data.use_manipulator_rotate = False
            context.space_data.use_manipulator_scale = True

        return {'FINISHED'}
bpy.utils.register_class(SetManipulator)


class ContextualTranslate(bpy.types.Operator):
    """ Either translates, or sets the manipulator type to translate,
        depending on whether the manipulator is on or not.
    """
    bl_idname = "view3d.contextual_translate"
    bl_label = "Contextual Translate"

    def execute(self, context):
        if context.space_data.show_manipulator:
            context.space_data.transform_manipulators = {'TRANSLATE'}
        else:
            bpy.ops.transform.translate('INVOKE_DEFAULT')
        return {'FINISHED'}
bpy.utils.register_class(ContextualTranslate)


class ContextualRotate(bpy.types.Operator):
    """ Either rotates, or sets the manipulator type to rotate,
        depending on whether the manipulator is on or not.
    """
    bl_idname = "view3d.contextual_rotate"
    bl_label = "Contextual Rotate"

    def execute(self, context):
        if context.space_data.show_manipulator:
            context.space_data.transform_manipulators = {'ROTATE'}
        else:
            bpy.ops.transform.rotate('INVOKE_DEFAULT')
        return {'FINISHED'}
bpy.utils.register_class(ContextualRotate)


class ContextualScale(bpy.types.Operator):
    """ Either scales, or sets the manipulator type to scale,
        depending on whether the manipulator is on or not.
    """
    bl_idname = "view3d.contextual_scale"
    bl_label = "Contextual Scale"

    def execute(self, context):
        if context.space_data.show_manipulator:
            context.space_data.transform_manipulators = {'SCALE'}
        else:
            bpy.ops.transform.resize('INVOKE_DEFAULT')
        return {'FINISHED'}
bpy.utils.register_class(ContextualScale)


class ModeSwitchMenu(bpy.types.Menu):
    """ A menu for switching between object modes.
    """
    bl_idname = "OBJECT_MT_mode_switch_menu"
    bl_label = "Switch Mode"

    def draw(self, context):
        layout = self.layout
        layout.operator_enum("object.mode_set", "mode")
bpy.utils.register_class(ModeSwitchMenu)


class TweakSelect3dview(bpy.types.Operator):
    """ Selects and translates an element in the scene.
    """
    bl_idname = "view3d.tweak_select"
    bl_label = "Tweak Select 3d View"
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return True
    
    def invoke(self, context, event):
        result = bpy.ops.view3d.select('INVOKE_DEFAULT')
        if 'FINISHED' in result:
            bpy.ops.transform.translate('INVOKE_DEFAULT')
        return result
bpy.utils.register_class(TweakSelect3dview)


class ObjectDeleteNoConfirm(bpy.types.Operator):
    """Delete selected objects without the confirmation popup"""
    bl_idname = "object.delete_no_confirm"
    bl_label = "Delete Objects No Confirm"
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        bpy.ops.object.delete()

        return {'FINISHED'}
bpy.utils.register_class(ObjectDeleteNoConfirm)


class ShiftSubsurfLevel(bpy.types.Operator):
    """ Shift the viewport subsurf level of the selected objects up or
        down by the given amount.  The render subsurf level is treated
        as the upper limit, to prevent the user from accidentally
        exploding their CPU and RAM usage. 
    """
    bl_idname = "object.shift_subsurf_level"
    bl_label = "Shift Subdivision Level"

    delta = bpy.props.IntProperty(name="Delta", description="Amount to increase/decrease the subdivision level", default=1)
    new_if_missing = bpy.props.BoolProperty(name="New if Missing", description="Whether to add a new Subdivision Surface modifier if none exists", default=False)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            object_list = [context.active_object]
        elif context.mode == 'OBJECT':
            object_list = context.selected_objects
            
        for obj in object_list:
            # Find the last subsurf modifier in the stack
            m = None
            for mod in obj.modifiers:
                if mod.type == "SUBSURF":
                    m = mod

            # Add a subsurf modifier if necessary
            if not m and self.delta > 0:
                if self.new_if_missing:
                    m = obj.modifiers.new(name="Subsurf", type='SUBSURF')
                    m.levels = 0
                else:
                    return {'FINISHED'}

            # Adjust it's subsurf level
            if m:
                if self.delta > 0:
                    if (m.levels + self.delta) <= m.render_levels:
                        m.levels += self.delta
                    elif m.levels != m.render_levels:
                        m.levels = m.render_levels
                elif self.delta < 0:
                    if (m.levels + self.delta) >= 0:
                        m.levels += self.delta
                    elif m.levels != 0:
                        m.levels = 0
        return {'FINISHED'}
bpy.utils.register_class(ShiftSubsurfLevel)


class SetEditMeshSelectMode(bpy.types.Operator):
    """ Set edit mesh select mode (vert, edge, face).
    """
    bl_idname = "view3d.set_edit_mesh_select_mode"
    bl_label = "Set Edit Mesh Select Mode"
    mode = bpy.props.EnumProperty(items=[("VERT", "Vertex", ""),
                                         ("EDGE", "Edge", ""),
                                         ("FACE", "Face", "")],
                                         default="VERT")
    toggle = bpy.props.BoolProperty(name="Toggle", default=False)
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        if self.mode == "VERT":
            mode = 0
        elif self.mode == "EDGE":
            mode = 1
        else:  # self.mode == "FACE"
            mode = 2
        
        select_mode = context.tool_settings.mesh_select_mode
        if self.toggle:
            select_mode[mode] = [True, False][select_mode[mode]]
        else:
            select_mode[mode] = True
            for i in range(0,3):
                if i != mode:
                    select_mode[i] = False
            
        return {'FINISHED'}
bpy.utils.register_class(SetEditMeshSelectMode)


class MeshCreateEdgeFaceContextual(bpy.types.Operator):
    """ Creates edges or faces from selected vertices,
        but understands that if it's creating an edge across
        an existing face that it should split it.
    """
    bl_idname = "mesh.create_edge_face_contextual"
    bl_label = "Create Edge/Face Contextual"
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None) and (context.mode == "EDIT_MESH")
    
    def execute(self, context):
        bm = bmesh.from_edit_mesh(context.active_object.data)
        
        # Get a list of selected vertices
        selected_verts = [v.index for v in bm.verts if v.select]
        
        # Accumulate a list of faces that the selected verts belong to,
        # and a count for each face of how many selected verts belong to
        # them.
        face_counts = {}
        for i in selected_verts:
            for f in bm.verts[i].link_faces:
                if f.index in face_counts:
                    face_counts[f.index] += 1
                else:
                    face_counts[f.index] = 1
        
        # Check if any face has all selected verts
        do_connect = False
        for i in face_counts:
            if face_counts[i] == len(selected_verts):
                do_connect = True
                break
        
        # Do the chosen operation
        if not do_connect:
            bpy.ops.mesh.edge_face_add()
        else:
            bpy.ops.mesh.vert_connect()
        
        return {'FINISHED'}
bpy.utils.register_class(MeshCreateEdgeFaceContextual)


class MeshDeleteContextual(bpy.types.Operator):
    """ Deletes mesh elements based on context instead
        of forcing the user to select from a menu what
        it should delete.
    """
    bl_idname = "mesh.delete_contextual"
    bl_label = "Mesh Delete Contextual"
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None) and (context.mode == "EDIT_MESH")
    
    def execute(self, context):
        select_mode = context.tool_settings.mesh_select_mode
        
        if select_mode[0]:
            bpy.ops.mesh.delete(type='VERT')
        elif select_mode[1] and not select_mode[2]:
            bpy.ops.mesh.delete(type='EDGE')
        elif select_mode[2] and not select_mode[1]:
            bpy.ops.mesh.delete(type='FACE')
        else:
            bpy.ops.mesh.delete(type='VERT')
            
        return {'FINISHED'}
bpy.utils.register_class(MeshDeleteContextual)


class MeshDissolveContextual(bpy.types.Operator):
    """ Dissolves mesh elements based on context instead
        of forcing the user to select from a menu what
        it should dissolve.
    """
    bl_idname = "mesh.dissolve_contextual"
    bl_label = "Mesh Dissolve Contextual"
    bl_options = {'UNDO'}
    
    use_verts = bpy.props.BoolProperty(name="Use Verts", default=False)
    
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None) and (context.mode == "EDIT_MESH")
    
    def execute(self, context):
        select_mode = context.tool_settings.mesh_select_mode
        
        if select_mode[0]:
            bpy.ops.mesh.dissolve_verts()
        elif select_mode[1] and not select_mode[2]:
            bpy.ops.mesh.dissolve_edges(use_verts=self.use_verts)
        elif select_mode[2] and not select_mode[1]:
            bpy.ops.mesh.dissolve_faces(use_verts=self.use_verts)
        else:
            bpy.ops.mesh.dissolve_verts()
            
        return {'FINISHED'}
bpy.utils.register_class(MeshDissolveContextual)


class MeshMergeContextual(bpy.types.Operator):
    """ Merges mesh elements, doing it in a way based on the current
        selection mode.
    """
    bl_idname = "mesh.merge_contextual"
    bl_label = "Mesh Merge Contextual"
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None) and (context.mode == "EDIT_MESH")
    
    def execute(self, context):
        select_mode = context.tool_settings.mesh_select_mode
        if select_mode[0]:
            bpy.ops.mesh.merge()
        else:
            bpy.ops.mesh.edge_collapse()
        return {'FINISHED'}
bpy.utils.register_class(MeshMergeContextual)


#kmi = km.keymap_items.new('mesh.edge_collapse', 'M', 'CLICK')
#kmi = km.keymap_items.new('mesh.merge', 'M', 'PRESS', alt=True)

###########
# Keymaps
###########

def clear_keymap(kc):
    """ Clears all the keymaps, so we can start from scratch, building
        things back up again one-by-one.
    """
    # Map Window
    km = kc.keymaps.new('Window', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Screen
    km = kc.keymaps.new('Screen', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Editing this part of the keymap seems
    # to cause problems, so leaving alone.
    # Map Screen Editing
    #km = kc.keymaps.new('Screen Editing', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map View2D
    km = kc.keymaps.new('View2D', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Frames
    km = kc.keymaps.new('Frames', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Header
    km = kc.keymaps.new('Header', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map View2D Buttons List
    km = kc.keymaps.new('View2D Buttons List', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Property Editor
    km = kc.keymaps.new('Property Editor', space_type='PROPERTIES', region_type='WINDOW', modal=False)

    # Map Markers
    km = kc.keymaps.new('Markers', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Animation
    km = kc.keymaps.new('Animation', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Timeline
    km = kc.keymaps.new('Timeline', space_type='TIMELINE', region_type='WINDOW', modal=False)

    # Map Outliner
    km = kc.keymaps.new('Outliner', space_type='OUTLINER', region_type='WINDOW', modal=False)

    # Map 3D View Generic
    km = kc.keymaps.new('3D View Generic', space_type='VIEW_3D', region_type='WINDOW', modal=False)

    # Map Grease Pencil
    km = kc.keymaps.new('Grease Pencil', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Face Mask
    km = kc.keymaps.new('Face Mask', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Pose
    km = kc.keymaps.new('Pose', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Object Mode
    km = kc.keymaps.new('Object Mode', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Image Paint
    km = kc.keymaps.new('Image Paint', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Vertex Paint
    km = kc.keymaps.new('Vertex Paint', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Weight Paint
    km = kc.keymaps.new('Weight Paint', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Sculpt
    km = kc.keymaps.new('Sculpt', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Mesh
    km = kc.keymaps.new('Mesh', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Curve
    km = kc.keymaps.new('Curve', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Armature
    km = kc.keymaps.new('Armature', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Metaball
    km = kc.keymaps.new('Metaball', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Lattice
    km = kc.keymaps.new('Lattice', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Particle
    km = kc.keymaps.new('Particle', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Font
    km = kc.keymaps.new('Font', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Object Non-modal
    km = kc.keymaps.new('Object Non-modal', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map 3D View
    km = kc.keymaps.new('3D View', space_type='VIEW_3D', region_type='WINDOW', modal=False)

    # Map View3D Gesture Circle
    km = kc.keymaps.new('View3D Gesture Circle', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map Gesture Border
    km = kc.keymaps.new('Gesture Border', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map Standard Modal Map
    km = kc.keymaps.new('Standard Modal Map', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map Animation Channels
    km = kc.keymaps.new('Animation Channels', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map UV Editor
    km = kc.keymaps.new('UV Editor', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Transform Modal Map
    km = kc.keymaps.new('Transform Modal Map', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map UV Sculpt
    km = kc.keymaps.new('UV Sculpt', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map View3D Fly Modal
    km = kc.keymaps.new('View3D Fly Modal', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map View3D Rotate Modal
    km = kc.keymaps.new('View3D Rotate Modal', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map View3D Move Modal
    km = kc.keymaps.new('View3D Move Modal', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map View3D Zoom Modal
    km = kc.keymaps.new('View3D Zoom Modal', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map Graph Editor Generic
    km = kc.keymaps.new('Graph Editor Generic', space_type='GRAPH_EDITOR', region_type='WINDOW', modal=False)

    # Map Graph Editor
    km = kc.keymaps.new('Graph Editor', space_type='GRAPH_EDITOR', region_type='WINDOW', modal=False)

    # Map Image Generic
    km = kc.keymaps.new('Image Generic', space_type='IMAGE_EDITOR', region_type='WINDOW', modal=False)

    # Map Image
    km = kc.keymaps.new('Image', space_type='IMAGE_EDITOR', region_type='WINDOW', modal=False)

    # Map Node Generic
    km = kc.keymaps.new('Node Generic', space_type='NODE_EDITOR', region_type='WINDOW', modal=False)

    # Map Node Editor
    km = kc.keymaps.new('Node Editor', space_type='NODE_EDITOR', region_type='WINDOW', modal=False)

    # Map File Browser
    km = kc.keymaps.new('File Browser', space_type='FILE_BROWSER', region_type='WINDOW', modal=False)

    # Map File Browser Main
    km = kc.keymaps.new('File Browser Main', space_type='FILE_BROWSER', region_type='WINDOW', modal=False)

    # Map File Browser Buttons
    km = kc.keymaps.new('File Browser Buttons', space_type='FILE_BROWSER', region_type='WINDOW', modal=False)

    # Map Dopesheet
    km = kc.keymaps.new('Dopesheet', space_type='DOPESHEET_EDITOR', region_type='WINDOW', modal=False)

    # Map NLA Generic
    km = kc.keymaps.new('NLA Generic', space_type='NLA_EDITOR', region_type='WINDOW', modal=False)

    # Map NLA Channels
    km = kc.keymaps.new('NLA Channels', space_type='NLA_EDITOR', region_type='WINDOW', modal=False)

    # Map NLA Editor
    km = kc.keymaps.new('NLA Editor', space_type='NLA_EDITOR', region_type='WINDOW', modal=False)

    # Map Text
    km = kc.keymaps.new('Text', space_type='TEXT_EDITOR', region_type='WINDOW', modal=False)

    # Map Sequencer
    km = kc.keymaps.new('Sequencer', space_type='SEQUENCE_EDITOR', region_type='WINDOW', modal=False)

    # Map Logic Editor
    km = kc.keymaps.new('Logic Editor', space_type='LOGIC_EDITOR', region_type='WINDOW', modal=False)

    # Map Console
    km = kc.keymaps.new('Console', space_type='CONSOLE', region_type='WINDOW', modal=False)

    # Map Clip
    km = kc.keymaps.new('Clip', space_type='CLIP_EDITOR', region_type='WINDOW', modal=False)

    # Map Clip Editor
    km = kc.keymaps.new('Clip Editor', space_type='CLIP_EDITOR', region_type='WINDOW', modal=False)

    # Map Clip Graph Editor
    km = kc.keymaps.new('Clip Graph Editor', space_type='CLIP_EDITOR', region_type='WINDOW', modal=False)





def MapAdd_Window(kc):
    """ Window Map
    """
    km = kc.keymaps.new('Window', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Quit
    kmi = km.keymap_items.new('wm.quit_blender', 'Q', 'PRESS', ctrl=True)

    # Operator search menu
    kmi = km.keymap_items.new('wm.search_menu', 'TAB', 'PRESS')

    # Open
    kmi = km.keymap_items.new('wm.open_mainfile', 'O', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('wm.link', 'O', 'PRESS', ctrl=True, alt=True)
    kmi = km.keymap_items.new('wm.append', 'O', 'PRESS', ctrl=True, shift=True)
    kmi.properties.link = False
    kmi = km.keymap_items.new('wm.read_homefile', 'N', 'PRESS', ctrl=True)

    # Save
    kmi = km.keymap_items.new('wm.save_mainfile', 'S', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('wm.save_as_mainfile', 'S', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('wm.save_homefile', 'U', 'PRESS', ctrl=True)

    # NDof Device
    # TODO: fix NDof below
    #kmi = km.keymap_items.new('wm.call_menu', 'NDOF_BUTTON_MENU', 'PRESS')
    #kmi.properties.name = 'USERPREF_MT_ndof_settings'
    #kmi = km.keymap_items.new('wm.ndof_sensitivity_change', 'NDOF_BUTTON_PLUS', 'PRESS')
    #kmi.properties.decrease = False
    #kmi.properties.fast = False
    #kmi = km.keymap_items.new('wm.ndof_sensitivity_change', 'NDOF_BUTTON_MINUS', 'PRESS')
    #kmi.properties.decrease = True
    #kmi.properties.fast = False
    #kmi = km.keymap_items.new('wm.ndof_sensitivity_change', 'NDOF_BUTTON_PLUS', 'PRESS', shift=True)
    #kmi.properties.decrease = False
    #kmi.properties.fast = True
    #kmi = km.keymap_items.new('wm.ndof_sensitivity_change', 'NDOF_BUTTON_MINUS', 'PRESS', shift=True)
    #kmi.properties.decrease = True
    #kmi.properties.fast = True

    # Misc
    # TODO: find good replacements for the F# keys
    kmi = km.keymap_items.new('wm.window_fullscreen_toggle', 'F11', 'CLICK', alt=True)

    # Development/debugging
    if DEVELOPER_HOTKEYS:
        kmi = km.keymap_items.new('wm.redraw_timer', 'T', 'CLICK', ctrl=True, alt=True)
        kmi = km.keymap_items.new('wm.debug_menu', 'D', 'CLICK', ctrl=True, alt=True)

    # ???
    kmi = km.keymap_items.new('info.reports_display_update', 'TIMER', 'ANY', any=True)

# TODO: find good replacements for the F# keys
def MapAdd_Screen(kc):
    """ Screen Map
    """
    km = kc.keymaps.new('Screen', space_type='EMPTY', region_type='WINDOW', modal=False)

    kmi = km.keymap_items.new('screen.animation_step', 'TIMER0', 'ANY', any=True)
    kmi = km.keymap_items.new('screen.screen_set', 'RIGHT_ARROW', 'PRESS', ctrl=True)
    kmi.properties.delta = 1
    kmi = km.keymap_items.new('screen.screen_set', 'LEFT_ARROW', 'PRESS', ctrl=True)
    kmi.properties.delta = -1
    
    # TODO: figure out a better hotkey for this
    kmi = km.keymap_items.new('screen.screen_full_area', 'UP_ARROW', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('screen.screen_full_area', 'DOWN_ARROW', 'PRESS', ctrl=True)
    
    #kmi = km.keymap_items.new('screen.screenshot', 'F3', 'PRESS', ctrl=True)
    #kmi = km.keymap_items.new('screen.screencast', 'F3', 'PRESS', alt=True)
    #kmi = km.keymap_items.new('screen.region_quadview', 'Q', 'PRESS', ctrl=True, alt=True)
    #kmi = km.keymap_items.new('screen.repeat_history', 'F3', 'PRESS')
    #kmi = km.keymap_items.new('screen.repeat_last', 'R', 'PRESS', shift=True)
    #kmi = km.keymap_items.new('screen.region_flip', 'F5', 'PRESS')
    #kmi = km.keymap_items.new('screen.redo_last', 'F6', 'PRESS')
    #kmi = km.keymap_items.new('script.reload', 'F8', 'PRESS')
    kmi = km.keymap_items.new('file.execute', 'RET', 'PRESS')
    kmi = km.keymap_items.new('file.execute', 'NUMPAD_ENTER', 'PRESS')
    kmi = km.keymap_items.new('file.cancel', 'ESC', 'PRESS')
    kmi = km.keymap_items.new('ed.undo', 'Z', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('ed.redo', 'Z', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('ed.undo_history', 'Z', 'PRESS', ctrl=True, alt=True)
    kmi = km.keymap_items.new('render.render', 'F12', 'PRESS')
    kmi = km.keymap_items.new('render.render', 'F12', 'PRESS', ctrl=True)
    #kmi.properties.animation = True
    kmi = km.keymap_items.new('render.view_cancel', 'ESC', 'PRESS')
    kmi = km.keymap_items.new('render.view_show', 'F11', 'PRESS')
    kmi = km.keymap_items.new('render.play_rendered_anim', 'F11', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('screen.userpref_show', 'U', 'PRESS', ctrl=True, alt=True)

    # Editing this seems to cause problems.
    # TODO: file bug report
    # Screen Editing
    #km = kc.keymaps.new('Screen Editing', space_type='EMPTY', region_type='WINDOW', modal=False)
    #
    #kmi = km.keymap_items.new('screen.actionzone', 'LEFTMOUSE', 'PRESS')
    #kmi.properties.modifier = 0
    #kmi = km.keymap_items.new('screen.actionzone', 'LEFTMOUSE', 'PRESS', shift=True)
    #kmi.properties.modifier = 1
    #kmi = km.keymap_items.new('screen.actionzone', 'LEFTMOUSE', 'PRESS', ctrl=True)
    #kmi.properties.modifier = 2
    #kmi = km.keymap_items.new('screen.area_split', 'NONE', 'ANY')
    #kmi = km.keymap_items.new('screen.area_join', 'NONE', 'ANY')
    #kmi = km.keymap_items.new('screen.area_dupli', 'NONE', 'ANY', shift=True)
    #kmi = km.keymap_items.new('screen.area_swap', 'NONE', 'ANY', ctrl=True)
    #kmi = km.keymap_items.new('screen.region_scale', 'NONE', 'ANY')
    #kmi = km.keymap_items.new('screen.area_move', 'LEFTMOUSE', 'PRESS')
    #kmi = km.keymap_items.new('screen.area_options', 'RIGHTMOUSE', 'PRESS')


def MapAdd_View2D(kc):
    """ View 2D Map
    """
    km = kc.keymaps.new('View2D', space_type='EMPTY', region_type='WINDOW', modal=False)

    kmi = km.keymap_items.new('view2d.scroller_activate', 'LEFTMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroller_activate', 'MIDDLEMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.pan', 'MIDDLEMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.pan', 'MIDDLEMOUSE', 'PRESS', shift=True)
    kmi = km.keymap_items.new('view2d.pan', 'TRACKPADPAN', 'ANY')
    kmi = km.keymap_items.new('view2d.scroll_right', 'WHEELDOWNMOUSE', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('view2d.scroll_left', 'WHEELUPMOUSE', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('view2d.scroll_down', 'WHEELDOWNMOUSE', 'PRESS', shift=True)
    kmi = km.keymap_items.new('view2d.scroll_up', 'WHEELUPMOUSE', 'PRESS', shift=True)
    kmi = km.keymap_items.new('view2d.zoom_out', 'WHEELOUTMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.zoom_in', 'WHEELINMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.zoom_out', 'NUMPAD_MINUS', 'PRESS')
    kmi = km.keymap_items.new('view2d.zoom_in', 'NUMPAD_PLUS', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroll_down', 'WHEELDOWNMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroll_up', 'WHEELUPMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroll_right', 'WHEELDOWNMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroll_left', 'WHEELUPMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.zoom', 'MIDDLEMOUSE', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('view2d.zoom', 'TRACKPADZOOM', 'ANY')
    kmi = km.keymap_items.new('view2d.zoom_border', 'B', 'PRESS', shift=True)

    # View2D Buttons List
    km = kc.keymaps.new('View2D Buttons List', space_type='EMPTY', region_type='WINDOW', modal=False)

    kmi = km.keymap_items.new('view2d.scroller_activate', 'LEFTMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroller_activate', 'MIDDLEMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.pan', 'MIDDLEMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.pan', 'TRACKPADPAN', 'ANY')
    kmi = km.keymap_items.new('view2d.scroll_down', 'WHEELDOWNMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroll_up', 'WHEELUPMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroll_down', 'PAGE_DOWN', 'PRESS')
    kmi.properties.page = True
    kmi = km.keymap_items.new('view2d.scroll_up', 'PAGE_UP', 'PRESS')
    kmi.properties.page = True
    kmi = km.keymap_items.new('view2d.zoom', 'MIDDLEMOUSE', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('view2d.zoom', 'TRACKPADZOOM', 'ANY')
    kmi = km.keymap_items.new('view2d.zoom_out', 'NUMPAD_MINUS', 'PRESS')
    kmi = km.keymap_items.new('view2d.zoom_in', 'NUMPAD_PLUS', 'PRESS')
    kmi = km.keymap_items.new('view2d.reset', 'HOME', 'PRESS')


def MapAdd_View3D_Generic(kc):
    """ View 3D Generic Map
    """
    km = kc.keymaps.new('3D View Generic', space_type='VIEW_3D', region_type='WINDOW', modal=False)
    
    kmi = km.keymap_items.new('view3d.toolshelf', 'SEMI_COLON', 'PRESS')
    kmi = km.keymap_items.new('view3d.properties', 'QUOTE', 'PRESS')


def MapAdd_View3D_Global(kc):
    """ View 3D Global Map
    """
    km = kc.keymaps.new('3D View', space_type='VIEW_3D', region_type='WINDOW', modal=False)

    #-----------------
    # View navigation
    #-----------------

    # ???
    kmi = km.keymap_items.new('view3d.rotate', 'MOUSEROTATE', 'ANY')
    kmi = km.keymap_items.new('view3d.smoothview', 'TIMER1', 'ANY', any=True)

    # Basics with mouse
    kmi = km.keymap_items.new('view3d.rotate', 'MIDDLEMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view3d.move', 'MIDDLEMOUSE', 'PRESS', shift=True)
    kmi = km.keymap_items.new('view3d.zoom', 'MIDDLEMOUSE', 'PRESS', ctrl=True)
    #kmi = km.keymap_items.new('view3d.dolly', 'MIDDLEMOUSE', 'PRESS', shift=True, ctrl=True)

    # Basics with mouse wheel
    kmi = km.keymap_items.new('view3d.zoom', 'WHEELINMOUSE', 'PRESS')
    kmi.properties.delta = 1
    kmi = km.keymap_items.new('view3d.zoom', 'WHEELOUTMOUSE', 'PRESS')
    kmi.properties.delta = -1
    kmi = km.keymap_items.new('view3d.view_pan', 'WHEELUPMOUSE', 'PRESS', ctrl=True)
    kmi.properties.type = 'PANRIGHT'
    kmi = km.keymap_items.new('view3d.view_pan', 'WHEELDOWNMOUSE', 'PRESS', ctrl=True)
    kmi.properties.type = 'PANLEFT'
    kmi = km.keymap_items.new('view3d.view_pan', 'WHEELUPMOUSE', 'PRESS', shift=True)
    kmi.properties.type = 'PANUP'
    kmi = km.keymap_items.new('view3d.view_pan', 'WHEELDOWNMOUSE', 'PRESS', shift=True)
    kmi.properties.type = 'PANDOWN'
    kmi = km.keymap_items.new('view3d.view_orbit', 'WHEELUPMOUSE', 'PRESS', ctrl=True, alt=True)
    kmi.properties.type = 'ORBITLEFT'
    kmi = km.keymap_items.new('view3d.view_orbit', 'WHEELDOWNMOUSE', 'PRESS', ctrl=True, alt=True)
    kmi.properties.type = 'ORBITRIGHT'
    kmi = km.keymap_items.new('view3d.view_orbit', 'WHEELUPMOUSE', 'PRESS', shift=True, alt=True)
    kmi.properties.type = 'ORBITUP'
    kmi = km.keymap_items.new('view3d.view_orbit', 'WHEELDOWNMOUSE', 'PRESS', shift=True, alt=True)
    kmi.properties.type = 'ORBITDOWN'

    # Basics with trackpad
    kmi = km.keymap_items.new('view3d.rotate', 'TRACKPADPAN', 'ANY', alt=True)
    kmi = km.keymap_items.new('view3d.move', 'TRACKPADPAN', 'ANY')
    kmi = km.keymap_items.new('view3d.zoom', 'TRACKPADZOOM', 'ANY')
    
    # Perspective/ortho
    kmi = km.keymap_items.new('view3d.view_persportho', 'NUMPAD_5', 'CLICK')

    # Camera view
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_0', 'CLICK')
    kmi.properties.type = 'CAMERA'
    
    # Basics with numpad
    kmi = km.keymap_items.new('view3d.view_orbit', 'NUMPAD_8', 'CLICK')
    kmi.properties.type = 'ORBITUP'
    kmi = km.keymap_items.new('view3d.view_orbit', 'NUMPAD_2', 'CLICK')
    kmi.properties.type = 'ORBITDOWN'
    kmi = km.keymap_items.new('view3d.view_orbit', 'NUMPAD_4', 'CLICK')
    kmi.properties.type = 'ORBITLEFT'
    kmi = km.keymap_items.new('view3d.view_orbit', 'NUMPAD_6', 'CLICK')
    kmi.properties.type = 'ORBITRIGHT'
    kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_8', 'CLICK', ctrl=True)
    kmi.properties.type = 'PANUP'
    kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_2', 'CLICK', ctrl=True)
    kmi.properties.type = 'PANDOWN'
    kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_4', 'CLICK', ctrl=True)
    kmi.properties.type = 'PANLEFT'
    kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_6', 'CLICK', ctrl=True)
    kmi.properties.type = 'PANRIGHT'
    kmi = km.keymap_items.new('view3d.zoom', 'NUMPAD_PLUS', 'CLICK')
    kmi.properties.delta = 1
    kmi = km.keymap_items.new('view3d.zoom', 'NUMPAD_MINUS', 'CLICK')
    kmi.properties.delta = -1

    # Zoom in/out alternatives
    kmi = km.keymap_items.new('view3d.zoom', 'EQUAL', 'CLICK', ctrl=True)
    kmi.properties.delta = 1
    kmi = km.keymap_items.new('view3d.zoom', 'MINUS', 'CLICK', ctrl=True)
    kmi.properties.delta = -1

    # Front/Right/Top/Back/Left/Bottom
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_1', 'CLICK')
    kmi.properties.type = 'FRONT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_3', 'CLICK')
    kmi.properties.type = 'RIGHT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_7', 'CLICK')
    kmi.properties.type = 'TOP'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_1', 'CLICK', ctrl=True)
    kmi.properties.type = 'BACK'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_3', 'CLICK', ctrl=True)
    kmi.properties.type = 'LEFT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_7', 'CLICK', ctrl=True)
    kmi.properties.type = 'BOTTOM'

    kmi = km.keymap_items.new('view3d.viewnumpad', 'MIDDLEMOUSE', 'CLICK', alt=True)
    kmi.properties.type = 'FRONT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'EVT_TWEAK_M', 'EAST', alt=True)
    kmi.properties.type = 'RIGHT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'EVT_TWEAK_M', 'NORTH', alt=True)
    kmi.properties.type = 'TOP'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'MIDDLEMOUSE', 'DOUBLE_CLICK', alt=True)
    kmi.properties.type = 'BACK'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'EVT_TWEAK_M', 'WEST', alt=True)
    kmi.properties.type = 'LEFT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'EVT_TWEAK_M', 'SOUTH', alt=True)
    kmi.properties.type = 'BOTTOM'

    # Selection-aligned Front/Right/Top/Back/Left/Bottom
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_1', 'CLICK', shift=True)
    kmi.properties.type = 'FRONT'
    kmi.properties.align_active = True
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_3', 'CLICK', shift=True)
    kmi.properties.type = 'RIGHT'
    kmi.properties.align_active = True
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_7', 'CLICK', shift=True)
    kmi.properties.type = 'TOP'
    kmi.properties.align_active = True
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_1', 'CLICK', shift=True, ctrl=True)
    kmi.properties.type = 'BACK'
    kmi.properties.align_active = True
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_3', 'CLICK', shift=True, ctrl=True)
    kmi.properties.type = 'LEFT'
    kmi.properties.align_active = True
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_7', 'CLICK', shift=True, ctrl=True)
    kmi.properties.type = 'BOTTOM'
    kmi.properties.align_active = True

    # NDOF Device
    kmi = km.keymap_items.new('view3d.ndof_orbit', 'NDOF_BUTTON_MENU', 'ANY')
    kmi = km.keymap_items.new('view3d.ndof_pan', 'NDOF_BUTTON_MENU', 'ANY', shift=True)
    kmi = km.keymap_items.new('view3d.view_selected', 'NDOF_BUTTON_FIT', 'PRESS')
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_FRONT', 'PRESS')
    kmi.properties.type = 'FRONT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_BACK', 'PRESS')
    kmi.properties.type = 'BACK'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_LEFT', 'PRESS')
    kmi.properties.type = 'LEFT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_RIGHT', 'PRESS')
    kmi.properties.type = 'RIGHT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_TOP', 'PRESS')
    kmi.properties.type = 'TOP'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_BOTTOM', 'PRESS')
    kmi.properties.type = 'BOTTOM'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_FRONT', 'PRESS', shift=True)
    kmi.properties.type = 'FRONT'
    kmi.properties.align_active = True
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_RIGHT', 'PRESS', shift=True)
    kmi.properties.type = 'RIGHT'
    kmi.properties.align_active = True
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_TOP', 'PRESS', shift=True)
    kmi.properties.type = 'TOP'
    kmi.properties.align_active = True

    # Fly mode
    #kmi = km.keymap_items.new('view3d.fly', 'F', 'CLICK', shift=True)

    # Misc
    # TODO: This needs a good go-over.  Try to pair this down to the
    # fewest useful ones. And try to find non-numpad hotkey alternatives
    # to have in addition for ones that use numpad hotkeys.
    kmi = km.keymap_items.new('view3d.view_selected', 'NUMPAD_PERIOD', 'CLICK')
    kmi = km.keymap_items.new('view3d.view_center_cursor', 'NUMPAD_PERIOD', 'CLICK', ctrl=True)
    kmi = km.keymap_items.new('view3d.zoom_camera_1_to_1', 'NUMPAD_ENTER', 'CLICK', shift=True)
    #kmi = km.keymap_items.new('view3d.view_center_camera', 'HOME', 'CLICK')
    kmi = km.keymap_items.new('view3d.view_all', 'HOME', 'CLICK')
    kmi.properties.center = False
    kmi = km.keymap_items.new('view3d.view_all', 'HOME', 'CLICK', shift=True)
    kmi.properties.center = True

    #-------------
    # Manipulator
    #-------------
    
    kmi = km.keymap_items.new('view3d.manipulator', 'EVT_TWEAK_L', 'ANY', shift=True)
    kmi.properties.release_confirm = True
    kmi.properties.use_planar_constraint = True
    kmi = km.keymap_items.new('view3d.manipulator', 'EVT_TWEAK_L', 'ANY', shift=True)
    kmi.properties.release_confirm = True
    kmi.properties.use_accurate = True
    kmi = km.keymap_items.new('view3d.manipulator', 'EVT_TWEAK_L', 'ANY', any=True)
    kmi.properties.release_confirm = True

    # TODO: figure out something sane for manipulators
    kmi = km.keymap_items.new('wm.context_toggle', 'SPACE', 'PRESS', ctrl=True)
    kmi.properties.data_path = 'space_data.show_manipulator'

    #-----------
    # Selection
    #-----------
    
    # Click select
    kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'CLICK') # Replace
    kmi.properties.extend = False
    kmi.properties.deselect = False
    kmi.properties.toggle = False
    kmi.properties.center = False
    kmi.properties.enumerate = False
    kmi.properties.object = False
    kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'CLICK', shift=True) # Extend
    kmi.properties.extend = True
    kmi.properties.deselect = False
    kmi.properties.toggle = False
    kmi.properties.center = False
    kmi.properties.enumerate = False
    kmi.properties.object = False
    kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'CLICK', ctrl=True) # Deselect
    kmi.properties.extend = False
    kmi.properties.deselect = True
    kmi.properties.toggle = False
    kmi.properties.center = False
    kmi.properties.enumerate = False
    kmi.properties.object = False
    
    # Enumerate select
    kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'CLICK', alt=True) # Replace
    kmi.properties.extend = False
    kmi.properties.center = False
    kmi.properties.enumerate = True
    kmi.properties.object = False
    kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'CLICK', shift=True, alt=True) # Extend
    kmi.properties.extend = True
    kmi.properties.center = False
    kmi.properties.enumerate = True
    kmi.properties.object = False
    kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'CLICK', ctrl=True, alt=True) # Center (TODO: deselect)
    kmi.properties.extend = False
    kmi.properties.center = True
    kmi.properties.enumerate = True
    kmi.properties.object = False

    # Border select
    kmi = km.keymap_items.new('view3d.select_border', 'EVT_TWEAK_L', 'ANY') # Replace
    kmi.properties.extend = False
    kmi = km.keymap_items.new('view3d.select_border', 'EVT_TWEAK_L', 'ANY', shift=True) # Extend
    kmi.properties.extend = True
    kmi = km.keymap_items.new('view3d.select_border', 'EVT_TWEAK_L', 'ANY', ctrl=True) # Deselect (handled in modal)
    kmi.properties.extend = False

    # Lasso select
    kmi = km.keymap_items.new('view3d.select_lasso', 'EVT_TWEAK_L', 'ANY', alt=True) # Replace
    kmi.properties.extend = False
    kmi.properties.deselect = False
    kmi = km.keymap_items.new('view3d.select_lasso', 'EVT_TWEAK_L', 'ANY', alt=True, shift=True) # Extend
    kmi.properties.extend = True
    kmi.properties.deselect = False
    kmi = km.keymap_items.new('view3d.select_lasso', 'EVT_TWEAK_L', 'ANY', alt=True, ctrl=True) # Deselect
    kmi.properties.extend = False
    kmi.properties.deselect = True

    # Paint select
    #kmi = km.keymap_items.new('view3d.select_circle', 'C', 'CLICK')

    #-----------------------
    # Transforms via hotkey
    #-----------------------
    
    # Grab, rotate scale
    kmi = km.keymap_items.new('view3d.contextual_translate', TRANSLATE_KEY, 'PRESS')
    kmi = km.keymap_items.new('view3d.tweak_select', 'EVT_TWEAK_R', 'ANY')
    
    #kmi = km.keymap_items.new('transform.translate', 'EVT_TWEAK_S', 'ANY')
    kmi = km.keymap_items.new('view3d.contextual_rotate', ROTATE_KEY, 'PRESS')
    kmi = km.keymap_items.new('view3d.contextual_scale', SCALE_KEY, 'PRESS')

    # Mirror, shear, warp, to-sphere
    #kmi = km.keymap_items.new('transform.mirror', 'M', 'CLICK', ctrl=True)
    #kmi = km.keymap_items.new('transform.shear', 'S', 'CLICK', shift=True, ctrl=True, alt=True)
    #kmi = km.keymap_items.new('transform.warp', 'W', 'CLICK', shift=True)
    #kmi = km.keymap_items.new('transform.tosphere', 'S', 'CLICK', shift=True, alt=True)

    #-------------------------
    # Transform texture space
    #-------------------------
    # TODO (?)
    #kmi = km.keymap_items.new('transform.translate', 'T', 'CLICK', shift=True)
    #kmi.properties.texture_space = True
    #kmi = km.keymap_items.new('transform.resize', 'T', 'CLICK', shift=True, alt=True)
    #kmi.properties.texture_space = True

    #------------------
    # Transform spaces
    #------------------
    kmi = km.keymap_items.new('transform.select_orientation', 'SPACE', 'CLICK', alt=True)
    kmi = km.keymap_items.new('transform.create_orientation', 'SPACE', 'CLICK', ctrl=True, alt=True)
    kmi.properties.use = True

    #----------
    # Snapping
    #----------
    #kmi = km.keymap_items.new('wm.context_toggle', 'TAB', 'CLICK', shift=True)
    #kmi.properties.data_path = 'tool_settings.use_snap'
    #kmi = km.keymap_items.new('transform.snap_type', 'TAB', 'CLICK', shift=True, ctrl=True)

    #---------------
    # Snapping Menu
    #---------------
    kmi = km.keymap_items.new('wm.call_menu', 'S', 'PRESS', shift=True)
    kmi.properties.name = 'VIEW3D_MT_snap'

    #-----------
    # 3d cursor
    #-----------
    kmi = km.keymap_items.new('view3d.cursor3d', 'ACTIONMOUSE', 'CLICK')

    #-------------------
    # Toggle local view
    #-------------------
    kmi = km.keymap_items.new('view3d.localview', 'NUMPAD_SLASH', 'CLICK')

    #--------
    # Layers
    #--------
    """
    kmi = km.keymap_items.new('view3d.layers', 'ACCENT_GRAVE', 'CLICK')
    kmi.properties.nr = 0
    kmi = km.keymap_items.new('view3d.layers', 'ONE', 'CLICK', any=True)
    kmi.properties.nr = 1
    kmi = km.keymap_items.new('view3d.layers', 'TWO', 'CLICK', any=True)
    kmi.properties.nr = 2
    kmi = km.keymap_items.new('view3d.layers', 'THREE', 'CLICK', any=True)
    kmi.properties.nr = 3
    kmi = km.keymap_items.new('view3d.layers', 'FOUR', 'CLICK', any=True)
    kmi.properties.nr = 4
    kmi = km.keymap_items.new('view3d.layers', 'FIVE', 'CLICK', any=True)
    kmi.properties.nr = 5
    kmi = km.keymap_items.new('view3d.layers', 'SIX', 'CLICK', any=True)
    kmi.properties.nr = 6
    kmi = km.keymap_items.new('view3d.layers', 'SEVEN', 'CLICK', any=True)
    kmi.properties.nr = 7
    kmi = km.keymap_items.new('view3d.layers', 'EIGHT', 'CLICK', any=True)
    kmi.properties.nr = 8
    kmi = km.keymap_items.new('view3d.layers', 'NINE', 'CLICK', any=True)
    kmi.properties.nr = 9
    kmi = km.keymap_items.new('view3d.layers', 'ZERO', 'CLICK', any=True)
    kmi.properties.nr = 10
    """

    #------------------
    # Viewport drawing
    #------------------
    kmi = km.keymap_items.new('wm.context_toggle_enum', 'Z', 'PRESS')
    kmi.properties.data_path = 'space_data.viewport_shade'
    kmi.properties.value_1 = 'SOLID'
    kmi.properties.value_2 = 'WIREFRAME'
    
    kmi = km.keymap_items.new('wm.context_menu_enum', 'Z', 'PRESS', alt=True)
    kmi.properties.data_path = 'space_data.viewport_shade'
    
    #-------------
    # Pivot point
    #-------------
    kmi = km.keymap_items.new('wm.context_set_enum', 'COMMA', 'CLICK')
    kmi.properties.data_path = 'space_data.pivot_point'
    kmi.properties.value = 'BOUNDING_BOX_CENTER'
    kmi = km.keymap_items.new('wm.context_set_enum', 'COMMA', 'CLICK', ctrl=True)
    kmi.properties.data_path = 'space_data.pivot_point'
    kmi.properties.value = 'MEDIAN_POINT'
    kmi = km.keymap_items.new('wm.context_toggle', 'COMMA', 'CLICK', alt=True)
    kmi.properties.data_path = 'space_data.use_pivot_point_align'
    kmi = km.keymap_items.new('wm.context_set_enum', 'PERIOD', 'CLICK')
    kmi.properties.data_path = 'space_data.pivot_point'
    kmi.properties.value = 'CURSOR'
    kmi = km.keymap_items.new('wm.context_set_enum', 'PERIOD', 'CLICK', ctrl=True)
    kmi.properties.data_path = 'space_data.pivot_point'
    kmi.properties.value = 'INDIVIDUAL_ORIGINS'
    kmi = km.keymap_items.new('wm.context_set_enum', 'PERIOD', 'CLICK', alt=True)
    kmi.properties.data_path = 'space_data.pivot_point'
    kmi.properties.value = 'ACTIVE_ELEMENT'

    #------
    # Misc
    #------
    kmi = km.keymap_items.new('view3d.zoom_border', 'V', 'CLICK')
    kmi = km.keymap_items.new('view3d.clip_border', 'V', 'PRESS', alt=True)
    kmi = km.keymap_items.new('view3d.render_border', 'V', 'PRESS', shift=True)
    kmi = km.keymap_items.new('view3d.camera_to_view', 'NUMPAD_0', 'CLICK', ctrl=True, alt=True)
    kmi = km.keymap_items.new('view3d.object_as_camera', 'NUMPAD_0', 'CLICK', ctrl=True)
    

def MapAdd_View3D_Object_Nonmodal(kc):
    """ Object Non-modal Map
        This essentially applies globally within the 3d view.  But technically
        only when objects are involved (but when are they not...?).
    """
    km = kc.keymaps.new('Object Non-modal', space_type='EMPTY', region_type='WINDOW', modal=False)
    
    # Mode switching
    kmi = km.keymap_items.new('wm.call_menu', 'SPACE', 'PRESS')
    kmi.properties.name = 'OBJECT_MT_mode_switch_menu'


def MapAdd_View3D_ObjectMode(kc):
    """ Object Mode Map
    """
    km = kc.keymaps.new('Object Mode', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Delete
    kmi = km.keymap_items.new('object.delete_no_confirm', 'X', 'CLICK')
    kmi = km.keymap_items.new('object.delete_no_confirm', 'DEL', 'CLICK')

    # Proportional editing
    kmi = km.keymap_items.new('wm.context_toggle', 'O', 'PRESS')
    kmi.properties.data_path = 'tool_settings.use_proportional_edit_objects'
    kmi = km.keymap_items.new('wm.context_cycle_enum', 'O', 'PRESS', shift=True)
    kmi.properties.data_path = 'tool_settings.proportional_edit_falloff'
    
    # Game engine start
    kmi = km.keymap_items.new('view3d.game_start', 'P', 'PRESS')
    
    # Selection
    kmi = km.keymap_items.new('object.select_all', 'A', 'PRESS')
    kmi.properties.action = 'TOGGLE'
    kmi = km.keymap_items.new('object.select_all', 'I', 'PRESS', ctrl=True)
    kmi.properties.action = 'INVERT'
    kmi = km.keymap_items.new('object.select_linked', 'L', 'PRESS', shift=True)
    kmi = km.keymap_items.new('object.select_grouped', 'G', 'PRESS', shift=True)
    kmi = km.keymap_items.new('object.select_mirror', 'M', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('object.select_hierarchy', 'LEFT_BRACKET', 'PRESS')
    kmi.properties.direction = 'PARENT'
    kmi.properties.extend = False
    kmi = km.keymap_items.new('object.select_hierarchy', 'LEFT_BRACKET', 'PRESS', shift=True)
    kmi.properties.direction = 'PARENT'
    kmi.properties.extend = True
    kmi = km.keymap_items.new('object.select_hierarchy', 'RIGHT_BRACKET', 'PRESS')
    kmi.properties.direction = 'CHILD'
    kmi.properties.extend = False
    kmi = km.keymap_items.new('object.select_hierarchy', 'RIGHT_BRACKET', 'PRESS', shift=True)
    kmi.properties.direction = 'CHILD'
    kmi.properties.extend = True
    
    # Parenting
    kmi = km.keymap_items.new('object.parent_set', 'P', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('object.parent_no_inverse_set', 'P', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('object.parent_clear', 'P', 'PRESS', alt=True)

    # Constraints
    kmi = km.keymap_items.new('object.constraint_add_with_targets', 'C', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('object.constraints_clear', 'C', 'PRESS', ctrl=True, alt=True)
    
    # Transforms
    kmi = km.keymap_items.new('object.location_clear', TRANSLATE_KEY, 'PRESS', alt=True)
    kmi = km.keymap_items.new('object.rotation_clear', ROTATE_KEY, 'PRESS', alt=True)
    kmi = km.keymap_items.new('object.scale_clear', SCALE_KEY, 'PRESS', alt=True)
    kmi = km.keymap_items.new('object.origin_clear', 'O', 'PRESS', alt=True)
    
    # Hiding
    kmi = km.keymap_items.new('object.hide_view_set', 'H', 'PRESS') # Hide selected
    kmi.properties.unselected = False
    kmi = km.keymap_items.new('object.hide_view_set', 'H', 'PRESS', shift=True) # Hide unselected
    kmi.properties.unselected = True
    kmi = km.keymap_items.new('object.hide_view_clear', 'H', 'PRESS', alt=True) # Unhide
    
    #kmi = km.keymap_items.new('object.hide_render_set', 'H', 'PRESS', ctrl=True)
    #kmi = km.keymap_items.new('object.hide_render_clear', 'H', 'PRESS', ctrl=True, alt=True)
    
    
    # Layer management
    kmi = km.keymap_items.new('object.move_to_layer', 'M', 'PRESS')

    # Add menus
    kmi = km.keymap_items.new('wm.call_menu', 'A', 'PRESS', shift=True)
    kmi.properties.name = 'INFO_MT_add'
    kmi = km.keymap_items.new('wm.call_menu', 'L', 'PRESS', ctrl=True)
    kmi.properties.name = 'VIEW3D_MT_make_links'
    
    # Duplication
    kmi = km.keymap_items.new('object.duplicate_move', 'D', 'PRESS', shift=True)
    kmi = km.keymap_items.new('object.duplicate_move_linked', 'D', 'PRESS', alt=True)
    kmi = km.keymap_items.new('object.duplicates_make_real', 'A', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('wm.call_menu', 'U', 'PRESS')
    kmi.properties.name = 'VIEW3D_MT_make_single_user'
    
    # Apply menu
    kmi = km.keymap_items.new('wm.call_menu', 'A', 'PRESS', ctrl=True)
    kmi.properties.name = 'VIEW3D_MT_object_apply'
    
    # Groups
    kmi = km.keymap_items.new('group.create', 'G', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('group.objects_remove', 'G', 'PRESS', ctrl=True, alt=True)
    kmi = km.keymap_items.new('group.objects_add_active', 'G', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('group.objects_remove_active', 'G', 'PRESS', shift=True, alt=True)

    # Make proxy
    kmi = km.keymap_items.new('object.proxy_make', 'P', 'PRESS', ctrl=True, alt=True)
    
    # Keyframe insertion
    kmi = km.keymap_items.new('anim.keyframe_insert_menu', KEYFRAME_KEY, 'PRESS')
    kmi = km.keymap_items.new('anim.keyframe_delete_v3d', KEYFRAME_KEY, 'PRESS', alt=True)
    kmi = km.keymap_items.new('anim.keying_set_active_set', KEYFRAME_KEY, 'PRESS', shift=True, ctrl=True, alt=True)
    
    # Misc
    kmi = km.keymap_items.new('object.join', 'J', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('object.convert', 'C', 'PRESS', alt=True)
    #kmi = km.keymap_items.new('object.make_local', 'L', 'PRESS')
    kmi = km.keymap_items.new('wm.call_menu', SPECIALS_MENU_KEY, 'PRESS')
    kmi.properties.name = 'VIEW3D_MT_object_specials'
    
    # Subdivision surface shortcuts
    #kmi = km.keymap_items.new('object.subdivision_set', 'ZERO', 'PRESS', ctrl=True)
    #kmi.properties.level = 0
    #kmi = km.keymap_items.new('object.subdivision_set', 'ONE', 'PRESS', ctrl=True)
    #kmi.properties.level = 1
    #kmi = km.keymap_items.new('object.subdivision_set', 'TWO', 'PRESS', ctrl=True)
    #kmi.properties.level = 2
    #kmi = km.keymap_items.new('object.subdivision_set', 'THREE', 'PRESS', ctrl=True)
    #kmi.properties.level = 3
    #kmi = km.keymap_items.new('object.subdivision_set', 'FOUR', 'PRESS', ctrl=True)
    #kmi.properties.level = 4
    #kmi = km.keymap_items.new('object.subdivision_set', 'FIVE', 'PRESS', ctrl=True)
    #kmi.properties.level = 5


def MapAdd_View3D_MeshEditMode(kc):
    """ Mesh Edit Mode Map
    """
    km = kc.keymaps.new('Mesh', space_type='EMPTY', region_type='WINDOW', modal=False)

    #---------------------------------
    # Vertex/Edge/Face mode switching
    #---------------------------------
    kmi = km.keymap_items.new('view3d.set_edit_mesh_select_mode', 'ONE', 'PRESS')
    kmi.properties.mode = 'VERT'
    kmi.properties.toggle = False
    kmi = km.keymap_items.new('view3d.set_edit_mesh_select_mode', 'TWO', 'PRESS')
    kmi.properties.mode = 'EDGE'
    kmi.properties.toggle = False
    kmi = km.keymap_items.new('view3d.set_edit_mesh_select_mode', 'THREE', 'PRESS')
    kmi.properties.mode = 'FACE'
    kmi.properties.toggle = False

    kmi = km.keymap_items.new('view3d.set_edit_mesh_select_mode', 'ONE', 'PRESS', shift=True)
    kmi.properties.mode = 'VERT'
    kmi.properties.toggle = True
    kmi = km.keymap_items.new('view3d.set_edit_mesh_select_mode', 'TWO', 'PRESS', shift=True)
    kmi.properties.mode = 'EDGE'
    kmi.properties.toggle = True
    kmi = km.keymap_items.new('view3d.set_edit_mesh_select_mode', 'THREE', 'PRESS', shift=True)
    kmi.properties.mode = 'FACE'
    kmi.properties.toggle = True

    #-----------
    # Selection
    #-----------
    
    # Shortest path
    kmi = km.keymap_items.new('mesh.shortest_path_pick', 'RIGHTMOUSE', 'PRESS', alt=True) # Replace
    # TODO: add, remove
    
    # Edge loop
    kmi = km.keymap_items.new('mesh.loop_select', 'LEFTMOUSE', 'DOUBLE_CLICK') # Replace
    kmi.properties.extend = False
    kmi.properties.deselect = False
    kmi = km.keymap_items.new('mesh.loop_select', 'LEFTMOUSE', 'DOUBLE_CLICK', shift=True) # Add
    kmi.properties.extend = True
    kmi.properties.deselect = False
    kmi = km.keymap_items.new('mesh.loop_select', 'LEFTMOUSE', 'DOUBLE_CLICK', ctrl=True) # Remove
    kmi.properties.extend = False
    kmi.properties.deselect = True
    
    # Edge ring
    kmi = km.keymap_items.new('mesh.edgering_select', 'LEFTMOUSE', 'DOUBLE_CLICK', alt=True) # Replace
    kmi.properties.extend = False
    kmi.properties.deselect = False
    kmi = km.keymap_items.new('mesh.edgering_select', 'LEFTMOUSE', 'DOUBLE_CLICK', alt=True, shift=True) # Add
    kmi.properties.extend = True
    kmi.properties.deselect = False
    kmi = km.keymap_items.new('mesh.edgering_select', 'LEFTMOUSE', 'DOUBLE_CLICK', alt=True, ctrl=True) # Remove
    kmi.properties.extend = False
    kmi.properties.deselect = True
    
    # Select linked
    # TODO: proper replace/add/remove selection
    kmi = km.keymap_items.new('mesh.select_linked', 'L', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('mesh.select_linked_pick', 'L', 'PRESS')
    kmi.properties.deselect = False
    kmi = km.keymap_items.new('mesh.select_linked_pick', 'L', 'PRESS', shift=True)
    kmi.properties.deselect = True
    
    # Misc selection
    kmi = km.keymap_items.new('mesh.select_all', 'A', 'PRESS')
    kmi.properties.action = 'TOGGLE'
    kmi = km.keymap_items.new('mesh.select_all', 'I', 'PRESS', ctrl=True)
    kmi.properties.action = 'INVERT'
    kmi = km.keymap_items.new('mesh.select_more', 'RIGHT_BRACKET', 'PRESS')
    kmi = km.keymap_items.new('mesh.select_less', 'LEFT_BRACKET', 'PRESS')
    #kmi = km.keymap_items.new('mesh.select_non_manifold', 'M', 'PRESS', shift=True, ctrl=True, alt=True)
    #kmi = km.keymap_items.new('mesh.faces_select_linked_flat', 'F', 'PRESS', shift=True, ctrl=True, alt=True)
    #kmi = km.keymap_items.new('mesh.select_similar', 'G', 'PRESS', shift=True)

    # Proportional editing
    kmi = km.keymap_items.new('wm.context_toggle_enum', 'O', 'CLICK')
    kmi.properties.data_path = 'tool_settings.proportional_edit'
    kmi.properties.value_1 = 'DISABLED'
    kmi.properties.value_2 = 'ENABLED'
    kmi = km.keymap_items.new('wm.context_cycle_enum', 'O', 'PRESS', shift=True)
    kmi.properties.data_path = 'tool_settings.proportional_edit_falloff'
    kmi = km.keymap_items.new('wm.context_toggle_enum', 'O', 'PRESS', alt=True)
    kmi.properties.data_path = 'tool_settings.proportional_edit'
    kmi.properties.value_1 = 'DISABLED'
    kmi.properties.value_2 = 'CONNECTED'

    # Hiding
    kmi = km.keymap_items.new('mesh.hide', 'H', 'CLICK')
    kmi.properties.unselected = False
    kmi = km.keymap_items.new('mesh.hide', 'H', 'PRESS', shift=True)
    kmi.properties.unselected = True
    kmi = km.keymap_items.new('mesh.reveal', 'H', 'PRESS', alt=True)

    #-----------------
    # Create Geometry
    #-----------------
    
    # Add Primitive
    kmi = km.keymap_items.new('wm.call_menu', 'A', 'PRESS', shift=True)
    kmi.properties.name = 'INFO_MT_mesh_add'
    
    # Add edge and face / vertex connect
    kmi = km.keymap_items.new('mesh.create_edge_face_contextual', 'C', 'CLICK')
    kmi = kmi = km.keymap_items.new('mesh.vert_connect', 'C', 'PRESS', shift=True)
    
    kmi = km.keymap_items.new('mesh.fill', 'C', 'PRESS', alt=True)
    kmi = km.keymap_items.new('mesh.beautify_fill', 'C', 'PRESS', alt=True, shift=True)
    
    # Subdivide
    kmi = km.keymap_items.new('mesh.subdivide', 'W', 'CLICK')
    
    # Loop cut
    kmi = km.keymap_items.new('mesh.loopcut_slide', 'T', 'PRESS')
    
    # Knife
    kmi = km.keymap_items.new('mesh.knife_tool', 'K', 'PRESS')
    
    # Extrude
    kmi = km.keymap_items.new('view3d.edit_mesh_extrude_move_normal', 'E', 'PRESS')
    kmi = km.keymap_items.new('wm.call_menu', 'E', 'PRESS', alt=True)
    kmi.properties.name = 'VIEW3D_MT_edit_mesh_extrude'
    
    kmi = km.keymap_items.new('mesh.dupli_extrude_cursor', 'ACTIONMOUSE', 'PRESS', ctrl=True)
    kmi.properties.rotate_source = True
    kmi = km.keymap_items.new('mesh.dupli_extrude_cursor', 'ACTIONMOUSE', 'PRESS', shift=True, ctrl=True)
    kmi.properties.rotate_source = False
    
    # Inset/Outset
    kmi = km.keymap_items.new('mesh.inset', 'I', 'PRESS')
    kmi.properties.use_outset = False
    kmi = km.keymap_items.new('mesh.inset', 'I', 'PRESS', shift=True)
    kmi.properties.use_outset = True
    
    # Bevel
    kmi = km.keymap_items.new('mesh.bevel', 'B', 'PRESS')
    
    # Bridge
    kmi = km.keymap_items.new('mesh.bridge_edge_loops', 'B', 'PRESS', shift=True)

    # Duplicate
    kmi = km.keymap_items.new('mesh.duplicate_move', 'D', 'PRESS', shift=True)
    
    # Rip
    kmi = km.keymap_items.new('mesh.rip_move', 'R', 'PRESS')
    
    # Split / Separate
    kmi = km.keymap_items.new('mesh.split', 'Y', 'PRESS')
    kmi = km.keymap_items.new('mesh.separate', 'Y', 'PRESS', shift=True)
    

    #-----------------
    # Remove Geometry
    #-----------------

    # Delete/Dissolve
    kmi = km.keymap_items.new('mesh.delete_contextual', 'X', 'CLICK')
    kmi = km.keymap_items.new('mesh.delete_contextual', 'DEL', 'CLICK')
    
    kmi = km.keymap_items.new('mesh.dissolve_contextual', 'X', 'PRESS', shift=True)
    kmi.properties.use_verts = True
    kmi = km.keymap_items.new('mesh.dissolve_contextual', 'DEL', 'PRESS', shift=True)
    kmi.properties.use_verts = True
    
    kmi = km.keymap_items.new('wm.call_menu', 'X', 'PRESS', alt=True)
    kmi.properties.name = 'VIEW3D_MT_edit_mesh_delete'
    kmi = km.keymap_items.new('wm.call_menu', 'DEL', 'PRESS', alt=True)
    kmi.properties.name = 'VIEW3D_MT_edit_mesh_delete'

    # Merge/collapse
    kmi = km.keymap_items.new('mesh.merge_contextual', 'M', 'PRESS')
    kmi = km.keymap_items.new('mesh.merge', 'M', 'PRESS', alt=True)
    
    #-----------------
    # Deform Geometry
    #-----------------
    
    # Smooth
    kmi = km.keymap_items.new('mesh.vertices_smooth', 'W', 'PRESS', shift=True)
    
    # Shrink / Fatten
    kmi = km.keymap_items.new('transform.shrink_fatten', 'S', 'PRESS', alt=True)
    
    #------
    # Misc
    #------
    
    # Vert/edge properties
    #kmi = km.keymap_items.new('transform.edge_crease', 'E', 'PRESS', shift=True)
    
    # Tri/quad conversion
    #kmi = km.keymap_items.new('mesh.quads_convert_to_tris', 'T', 'PRESS', ctrl=True)
    #kmi = km.keymap_items.new('mesh.quads_convert_to_tris', 'T', 'PRESS', shift=True, ctrl=True)
    #kmi.properties.use_beauty = False
    #kmi = km.keymap_items.new('mesh.tris_convert_to_quads', 'J', 'PRESS', alt=True)

    # Tool Menus
    kmi = km.keymap_items.new('wm.call_menu', SPECIALS_MENU_KEY, 'PRESS')
    kmi.properties.name = 'VIEW3D_MT_edit_mesh_specials'
    kmi = km.keymap_items.new('wm.call_menu', 'ONE', 'PRESS', alt=True)
    kmi.properties.name = 'VIEW3D_MT_edit_mesh_vertices'
    kmi = km.keymap_items.new('wm.call_menu', 'TWO', 'PRESS', alt=True)
    kmi.properties.name = 'VIEW3D_MT_edit_mesh_edges'
    kmi = km.keymap_items.new('wm.call_menu', 'THREE', 'PRESS', alt=True)
    kmi.properties.name = 'VIEW3D_MT_edit_mesh_faces'

    # UV's
    kmi = km.keymap_items.new('wm.call_menu', 'U', 'PRESS')
    kmi.properties.name = 'VIEW3D_MT_uv_map'

    # Calculate normals
    kmi = km.keymap_items.new('mesh.normals_make_consistent', 'N', 'PRESS', ctrl=True)
    kmi.properties.inside = False
    kmi = km.keymap_items.new('mesh.normals_make_consistent', 'N', 'PRESS', shift=True, ctrl=True)
    kmi.properties.inside = True

    # Subsurf shortcuts
    kmi = km.keymap_items.new('object.shift_subsurf_level', 'EQUAL', 'PRESS')
    kmi.properties.delta = 1
    kmi.properties.new_if_missing = True
    kmi = km.keymap_items.new('object.shift_subsurf_level', 'MINUS', 'PRESS')
    kmi.properties.delta = -1
    kmi.properties.new_if_missing = False

    # Rigging
    kmi = km.keymap_items.new('object.vertex_parent_set', 'P', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('wm.call_menu', 'H', 'PRESS', ctrl=True)
    kmi.properties.name = 'VIEW3D_MT_hook'
    kmi = km.keymap_items.new('wm.call_menu', 'G', 'PRESS', ctrl=True)
    kmi.properties.name = 'VIEW3D_MT_vertex_group'

def MapAdd_KnifeToolModal(kc):
    # Map Knife Tool Modal Map
    km = kc.keymaps.new('Knife Tool Modal Map', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Add cut
    kmi = km.keymap_items.new_modal('ADD_CUT', 'LEFTMOUSE', 'PRESS', any=True)
    
    # Finish
    kmi = km.keymap_items.new_modal('CONFIRM', 'RIGHTMOUSE', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('CONFIRM', 'RET', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('CONFIRM', 'NUMPAD_ENTER', 'PRESS', any=True)
    #kmi = km.keymap_items.new_modal('CONFIRM', 'SPACE', 'PRESS', any=True)
    
    # Cancel
    kmi = km.keymap_items.new_modal('CANCEL', 'ESC', 'PRESS', any=True)
    
    
    kmi = km.keymap_items.new_modal('NEW_CUT', 'E', 'PRESS')
    
    # Snapping
    kmi = km.keymap_items.new_modal('SNAP_MIDPOINTS_ON', 'LEFT_CTRL', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('SNAP_MIDPOINTS_OFF', 'LEFT_CTRL', 'RELEASE', any=True)
    kmi = km.keymap_items.new_modal('SNAP_MIDPOINTS_ON', 'RIGHT_CTRL', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('SNAP_MIDPOINTS_OFF', 'RIGHT_CTRL', 'RELEASE', any=True)
    kmi = km.keymap_items.new_modal('ANGLE_SNAP_TOGGLE', 'C', 'PRESS')
    
    # Ignore snapping
    kmi = km.keymap_items.new_modal('IGNORE_SNAP_ON', 'LEFT_SHIFT', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('IGNORE_SNAP_OFF', 'LEFT_SHIFT', 'RELEASE', any=True)
    kmi = km.keymap_items.new_modal('IGNORE_SNAP_ON', 'RIGHT_SHIFT', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('IGNORE_SNAP_OFF', 'RIGHT_SHIFT', 'RELEASE', any=True)
    
    # Cut through toggle
    kmi = km.keymap_items.new_modal('CUT_THROUGH_TOGGLE', 'Z', 'PRESS')
    

def MapAdd_Sculpt(kc):
    # Map Sculpt
    km = kc.keymaps.new('Sculpt', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Sculpt strokesff
    kmi = km.keymap_items.new('sculpt.brush_stroke', 'LEFTMOUSE', 'PRESS')
    kmi.properties.mode = 'NORMAL'
    kmi = km.keymap_items.new('sculpt.brush_stroke', 'LEFTMOUSE', 'PRESS', ctrl=True)
    kmi.properties.mode = 'INVERT'
    kmi = km.keymap_items.new('sculpt.brush_stroke', 'LEFTMOUSE', 'PRESS', shift=True)
    kmi.properties.mode = 'SMOOTH'
    
    # Change stroke methods
    kmi = km.keymap_items.new('wm.context_menu_enum', 'A', 'PRESS')
    kmi.properties.data_path = 'tool_settings.sculpt.brush.sculpt_stroke_method'
    kmi = km.keymap_items.new('wm.context_toggle', 'S', 'PRESS', shift=True)
    kmi.properties.data_path = 'tool_settings.sculpt.brush.use_smooth_stroke'
    kmi = km.keymap_items.new('wm.context_menu_enum', 'R', 'PRESS')
    kmi.properties.data_path = 'tool_settings.sculpt.brush.texture_angle_source_random'
    
    # Brush scale
    kmi = km.keymap_items.new('brush.scale_size', 'LEFT_BRACKET', 'PRESS')
    kmi.properties.scalar = 0.9
    kmi = km.keymap_items.new('brush.scale_size', 'RIGHT_BRACKET', 'PRESS')
    kmi.properties.scalar = 1.1111111111
    kmi = km.keymap_items.new('wm.radial_control', 'R', 'PRESS')
    kmi.properties.data_path_primary = 'tool_settings.sculpt.brush.size'
    kmi.properties.data_path_secondary = 'tool_settings.unified_paint_settings.size'
    kmi.properties.use_secondary = 'tool_settings.unified_paint_settings.use_unified_size'
    kmi.properties.rotation_path = 'tool_settings.sculpt.brush.texture_slot.angle'
    kmi.properties.color_path = 'tool_settings.sculpt.brush.cursor_color_add'
    kmi.properties.fill_color_path = ''
    kmi.properties.zoom_path = ''
    kmi.properties.image_id = 'tool_settings.sculpt.brush'
    
    # Brush strength
    kmi = km.keymap_items.new('wm.radial_control', 'R', 'PRESS', shift=True)
    kmi.properties.data_path_primary = 'tool_settings.sculpt.brush.strength'
    kmi.properties.data_path_secondary = 'tool_settings.unified_paint_settings.strength'
    kmi.properties.use_secondary = 'tool_settings.unified_paint_settings.use_unified_strength'
    kmi.properties.rotation_path = 'tool_settings.sculpt.brush.texture_slot.angle'
    kmi.properties.color_path = 'tool_settings.sculpt.brush.cursor_color_add'
    kmi.properties.fill_color_path = ''
    kmi.properties.zoom_path = ''
    kmi.properties.image_id = 'tool_settings.sculpt.brush'
    
    # Brush angle
    kmi = km.keymap_items.new('wm.radial_control', 'R', 'PRESS', ctrl=True)
    kmi.properties.data_path_primary = 'tool_settings.sculpt.brush.texture_slot.angle'
    kmi.properties.data_path_secondary = ''
    kmi.properties.use_secondary = ''
    kmi.properties.rotation_path = 'tool_settings.sculpt.brush.texture_slot.angle'
    kmi.properties.color_path = 'tool_settings.sculpt.brush.cursor_color_add'
    kmi.properties.fill_color_path = ''
    kmi.properties.zoom_path = ''
    kmi.properties.image_id = 'tool_settings.sculpt.brush'
    
    # Dyntopo detail size
    kmi = km.keymap_items.new('wm.radial_control', 'D', 'PRESS', shift=True)
    kmi.properties.data_path_primary = 'tool_settings.sculpt.detail_size'
    kmi.properties.data_path_secondary = ''
    kmi.properties.use_secondary = ''
    kmi.properties.rotation_path = 'tool_settings.sculpt.brush.texture_slot.angle'
    kmi.properties.color_path = 'tool_settings.sculpt.brush.cursor_color_add'
    kmi.properties.fill_color_path = ''
    kmi.properties.zoom_path = ''
    kmi.properties.image_id = 'tool_settings.sculpt.brush'
    
    # Dynamic topology
    kmi = km.keymap_items.new('sculpt.dynamic_topology_toggle', 'D', 'PRESS', ctrl=True)
    
    # Hiding
    kmi = km.keymap_items.new('paint.hide_show', 'H', 'PRESS')
    kmi.properties.action = 'HIDE'
    kmi.properties.area = 'INSIDE'
    kmi = km.keymap_items.new('paint.hide_show', 'H', 'PRESS', shift=True)
    kmi.properties.action = 'SHOW'
    kmi.properties.area = 'INSIDE'
    kmi = km.keymap_items.new('paint.hide_show', 'H', 'PRESS', alt=True)
    kmi.properties.action = 'SHOW'
    kmi.properties.area = 'ALL'
    
    # Masking
    # TODO: mask menu on alt-m
    kmi = km.keymap_items.new('paint.mask_flood_fill', 'M', 'PRESS', alt=True)
    kmi.properties.mode = 'VALUE'
    kmi.properties.value = 0.0
    kmi = km.keymap_items.new('paint.mask_flood_fill', 'I', 'PRESS', ctrl=True)
    kmi.properties.mode = 'INVERT'
    
    # Subdivision levels
    kmi = km.keymap_items.new('object.subdivision_set', 'EQUAL', 'PRESS')
    kmi.properties.level = 1
    kmi.properties.relative = True
    kmi = km.keymap_items.new('object.subdivision_set', 'MINUS', 'PRESS')
    kmi.properties.level = -1
    kmi.properties.relative = True
    #kmi = km.keymap_items.new('object.subdivision_set', 'ZERO', 'PRESS', ctrl=True)
    #kmi.properties.level = 0
    #kmi = km.keymap_items.new('object.subdivision_set', 'ONE', 'PRESS', ctrl=True)
    #kmi.properties.level = 1
    #kmi = km.keymap_items.new('object.subdivision_set', 'TWO', 'PRESS', ctrl=True)
    #kmi.properties.level = 2
    #kmi = km.keymap_items.new('object.subdivision_set', 'THREE', 'PRESS', ctrl=True)
    #kmi.properties.level = 3
    #kmi = km.keymap_items.new('object.subdivision_set', 'FOUR', 'PRESS', ctrl=True)
    #kmi.properties.level = 4
    #kmi = km.keymap_items.new('object.subdivision_set', 'FIVE', 'PRESS', ctrl=True)
    #kmi.properties.level = 5
    
    # Brush switching by index
    kmi = km.keymap_items.new('brush.active_index_set', 'ONE', 'PRESS')
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 0
    kmi = km.keymap_items.new('brush.active_index_set', 'TWO', 'PRESS')
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 1
    kmi = km.keymap_items.new('brush.active_index_set', 'THREE', 'PRESS')
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 2
    kmi = km.keymap_items.new('brush.active_index_set', 'FOUR', 'PRESS')
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 3
    kmi = km.keymap_items.new('brush.active_index_set', 'FIVE', 'PRESS')
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 4
    kmi = km.keymap_items.new('brush.active_index_set', 'SIX', 'PRESS')
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 5
    kmi = km.keymap_items.new('brush.active_index_set', 'SEVEN', 'PRESS')
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 6
    kmi = km.keymap_items.new('brush.active_index_set', 'EIGHT', 'PRESS')
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 7
    kmi = km.keymap_items.new('brush.active_index_set', 'NINE', 'PRESS')
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 8
    kmi = km.keymap_items.new('brush.active_index_set', 'ZERO', 'PRESS')
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 9
    kmi = km.keymap_items.new('brush.active_index_set', 'ONE', 'PRESS', shift=True)
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 10
    kmi = km.keymap_items.new('brush.active_index_set', 'TWO', 'PRESS', shift=True)
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 11
    kmi = km.keymap_items.new('brush.active_index_set', 'THREE', 'PRESS', shift=True)
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 12
    kmi = km.keymap_items.new('brush.active_index_set', 'FOUR', 'PRESS', shift=True)
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 13
    kmi = km.keymap_items.new('brush.active_index_set', 'FIVE', 'PRESS', shift=True)
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 14
    kmi = km.keymap_items.new('brush.active_index_set', 'SIX', 'PRESS', shift=True)
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 15
    kmi = km.keymap_items.new('brush.active_index_set', 'SEVEN', 'PRESS', shift=True)
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 16
    kmi = km.keymap_items.new('brush.active_index_set', 'EIGHT', 'PRESS', shift=True)
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 17
    kmi = km.keymap_items.new('brush.active_index_set', 'NINE', 'PRESS', shift=True)
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 18
    kmi = km.keymap_items.new('brush.active_index_set', 'ZERO', 'PRESS', shift=True)
    kmi.properties.mode = 'sculpt'
    kmi.properties.index = 19
    
    # Brush switching by type
    kmi = km.keymap_items.new('paint.brush_select', 'D', 'PRESS')
    kmi.properties.paint_mode = 'SCULPT'
    kmi.properties.sculpt_tool = 'DRAW'
    kmi = km.keymap_items.new('paint.brush_select', 'S', 'PRESS')
    kmi.properties.paint_mode = 'SCULPT'
    kmi.properties.sculpt_tool = 'SMOOTH'
    kmi = km.keymap_items.new('paint.brush_select', 'P', 'PRESS')
    kmi.properties.paint_mode = 'SCULPT'
    kmi.properties.sculpt_tool = 'PINCH'
    kmi = km.keymap_items.new('paint.brush_select', 'I', 'PRESS')
    kmi.properties.paint_mode = 'SCULPT'
    kmi.properties.sculpt_tool = 'INFLATE'
    kmi = km.keymap_items.new('paint.brush_select', 'G', 'PRESS')
    kmi.properties.paint_mode = 'SCULPT'
    kmi.properties.sculpt_tool = 'GRAB'
    kmi = km.keymap_items.new('paint.brush_select', 'L', 'PRESS')
    kmi.properties.paint_mode = 'SCULPT'
    kmi.properties.sculpt_tool = 'LAYER'
    kmi = km.keymap_items.new('paint.brush_select', 'T', 'PRESS', shift=True)
    kmi.properties.paint_mode = 'SCULPT'
    kmi.properties.sculpt_tool = 'FLATTEN'
    kmi = km.keymap_items.new('paint.brush_select', 'C', 'PRESS')
    kmi.properties.paint_mode = 'SCULPT'
    kmi.properties.sculpt_tool = 'CLAY'
    kmi = km.keymap_items.new('paint.brush_select', 'C', 'PRESS', shift=True)
    kmi.properties.paint_mode = 'SCULPT'
    kmi.properties.sculpt_tool = 'CREASE'
    kmi = km.keymap_items.new('paint.brush_select', 'K', 'PRESS')
    kmi.properties.paint_mode = 'SCULPT'
    kmi.properties.sculpt_tool = 'SNAKE_HOOK'
    kmi = km.keymap_items.new('paint.brush_select', 'M', 'PRESS')
    kmi.properties.paint_mode = 'SCULPT'
    kmi.properties.sculpt_tool = 'MASK'
    kmi.properties.toggle = True
    kmi.properties.create_missing = True
    
    # Stencil manipulation
    kmi = km.keymap_items.new('brush.stencil_control', 'RIGHTMOUSE', 'PRESS')
    kmi.properties.mode = 'TRANSLATION'
    kmi = km.keymap_items.new('brush.stencil_control', 'RIGHTMOUSE', 'PRESS', ctrl=True)
    kmi.properties.mode = 'SCALE'
    kmi = km.keymap_items.new('brush.stencil_control', 'RIGHTMOUSE', 'PRESS', shift=True)
    kmi.properties.mode = 'ROTATION'
    kmi = km.keymap_items.new('brush.stencil_control', 'RIGHTMOUSE', 'PRESS', alt=True)
    kmi.properties.mode = 'TRANSLATION'
    kmi.properties.texmode = 'SECONDARY'
    kmi = km.keymap_items.new('brush.stencil_control', 'RIGHTMOUSE', 'PRESS', ctrl=True, alt=True)
    kmi.properties.mode = 'SCALE'
    kmi.properties.texmode = 'SECONDARY'
    kmi = km.keymap_items.new('brush.stencil_control', 'RIGHTMOUSE', 'PRESS', shift=True, alt=True)
    kmi.properties.mode = 'ROTATION'
    kmi.properties.texmode = 'SECONDARY'


def MapAdd_WeightPaint(kc):
    km = kc.keymaps.new('Weight Paint', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Select bones/objects/etc
    kmi = km.keymap_items.new('view3d.select', 'LEFTMOUSE', 'PRESS', alt=True)
    kmi.properties.extend = False
    kmi.properties.deselect = False
    kmi.properties.toggle = False
    kmi.properties.center = False
    kmi.properties.enumerate = False
    kmi.properties.object = False
    kmi = km.keymap_items.new('view3d.select', 'LEFTMOUSE', 'PRESS', alt=True, shift=True)
    kmi.properties.extend = True
    kmi.properties.deselect = False
    kmi.properties.toggle = False
    kmi.properties.center = False
    kmi.properties.enumerate = False
    kmi.properties.object = False
    kmi = km.keymap_items.new('view3d.select', 'LEFTMOUSE', 'PRESS', alt=True, ctrl=True)
    kmi.properties.extend = False
    kmi.properties.deselect = True
    kmi.properties.toggle = False
    kmi.properties.center = False
    kmi.properties.enumerate = False
    kmi.properties.object = False

    # Paint weight
    kmi = km.keymap_items.new('paint.weight_paint', 'LEFTMOUSE', 'PRESS')
    
    # Weight gradient
    kmi = km.keymap_items.new('paint.weight_gradient', 'LEFTMOUSE', 'PRESS', ctrl=True)
    kmi.properties.type = 'LINEAR'
    kmi = km.keymap_items.new('paint.weight_gradient', 'LEFTMOUSE', 'PRESS', ctrl=True, shift=True)
    kmi.properties.type = 'RADIAL'
    
    # Sample weight
    kmi = km.keymap_items.new('paint.weight_sample', 'RIGHTMOUSE', 'PRESS', alt=True)
    kmi = km.keymap_items.new('paint.weight_sample_group', 'RIGHTMOUSE', 'PRESS', alt=True, shift=True)
    
    # Brush radius
    # TODO: armature pose mode masks this, instead of this masking
    # armature pose mode.  Fix.
    kmi = km.keymap_items.new('brush.scale_size', 'LEFT_BRACKET', 'PRESS')
    kmi.properties.scalar = 0.9
    kmi = km.keymap_items.new('brush.scale_size', 'RIGHT_BRACKET', 'PRESS')
    kmi.properties.scalar = 1.1111111111111111
    kmi = km.keymap_items.new('wm.radial_control', 'R', 'PRESS')
    kmi.properties.data_path_primary = 'tool_settings.weight_paint.brush.size'
    kmi.properties.data_path_secondary = 'tool_settings.unified_paint_settings.size'
    kmi.properties.use_secondary = 'tool_settings.unified_paint_settings.use_unified_size'
    kmi.properties.rotation_path = 'tool_settings.weight_paint.brush.texture_slot.angle'
    kmi.properties.color_path = 'tool_settings.weight_paint.brush.cursor_color_add'
    kmi.properties.fill_color_path = ''
    kmi.properties.zoom_path = ''
    kmi.properties.image_id = 'tool_settings.weight_paint.brush'
    kmi.properties.secondary_tex = False
    
    # Brush strength
    kmi = km.keymap_items.new('wm.radial_control', 'R', 'PRESS', shift=True)
    kmi.properties.data_path_primary = 'tool_settings.weight_paint.brush.strength'
    kmi.properties.data_path_secondary = 'tool_settings.unified_paint_settings.strength'
    kmi.properties.use_secondary = 'tool_settings.unified_paint_settings.use_unified_strength'
    kmi.properties.rotation_path = 'tool_settings.weight_paint.brush.texture_slot.angle'
    kmi.properties.color_path = 'tool_settings.weight_paint.brush.cursor_color_add'
    kmi.properties.fill_color_path = ''
    kmi.properties.zoom_path = ''
    kmi.properties.image_id = 'tool_settings.weight_paint.brush'
    kmi.properties.secondary_tex = False
    
    # Brush weight
    kmi = km.keymap_items.new('wm.radial_control', 'W', 'PRESS')
    kmi.properties.data_path_primary = 'tool_settings.weight_paint.brush.weight'
    kmi.properties.data_path_secondary = 'tool_settings.unified_paint_settings.weight'
    kmi.properties.use_secondary = 'tool_settings.unified_paint_settings.use_unified_weight'
    kmi.properties.rotation_path = 'tool_settings.weight_paint.brush.texture_slot.angle'
    kmi.properties.color_path = 'tool_settings.weight_paint.brush.cursor_color_add'
    kmi.properties.fill_color_path = ''
    kmi.properties.zoom_path = ''
    kmi.properties.image_id = 'tool_settings.weight_paint.brush'
    kmi.properties.secondary_tex = False
    kmi = km.keymap_items.new('paint.weight_set', 'K', 'PRESS', shift=True)
    
    # Brush selection by index
    kmi = km.keymap_items.new('brush.active_index_set', 'ONE', 'PRESS')
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 0
    kmi = km.keymap_items.new('brush.active_index_set', 'TWO', 'PRESS')
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 1
    kmi = km.keymap_items.new('brush.active_index_set', 'THREE', 'PRESS')
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 2
    kmi = km.keymap_items.new('brush.active_index_set', 'FOUR', 'PRESS')
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 3
    kmi = km.keymap_items.new('brush.active_index_set', 'FIVE', 'PRESS')
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 4
    kmi = km.keymap_items.new('brush.active_index_set', 'SIX', 'PRESS')
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 5
    kmi = km.keymap_items.new('brush.active_index_set', 'SEVEN', 'PRESS')
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 6
    kmi = km.keymap_items.new('brush.active_index_set', 'EIGHT', 'PRESS')
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 7
    kmi = km.keymap_items.new('brush.active_index_set', 'NINE', 'PRESS')
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 8
    kmi = km.keymap_items.new('brush.active_index_set', 'ZERO', 'PRESS')
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 9
    kmi = km.keymap_items.new('brush.active_index_set', 'ONE', 'PRESS', shift=True)
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 10
    kmi = km.keymap_items.new('brush.active_index_set', 'TWO', 'PRESS', shift=True)
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 11
    kmi = km.keymap_items.new('brush.active_index_set', 'THREE', 'PRESS', shift=True)
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 12
    kmi = km.keymap_items.new('brush.active_index_set', 'FOUR', 'PRESS', shift=True)
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 13
    kmi = km.keymap_items.new('brush.active_index_set', 'FIVE', 'PRESS', shift=True)
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 14
    kmi = km.keymap_items.new('brush.active_index_set', 'SIX', 'PRESS', shift=True)
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 15
    kmi = km.keymap_items.new('brush.active_index_set', 'SEVEN', 'PRESS', shift=True)
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 16
    kmi = km.keymap_items.new('brush.active_index_set', 'EIGHT', 'PRESS', shift=True)
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 17
    kmi = km.keymap_items.new('brush.active_index_set', 'NINE', 'PRESS', shift=True)
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 18
    kmi = km.keymap_items.new('brush.active_index_set', 'ZERO', 'PRESS', shift=True)
    kmi.properties.mode = 'weight_paint'
    kmi.properties.index = 19
    
    # ??? kmi = km.keymap_items.new('brush.stencil_control', 'RIGHTMOUSE', 'PRESS')
    # ??? kmi.properties.mode = 'TRANSLATION'
    # ??? kmi = km.keymap_items.new('brush.stencil_control', 'RIGHTMOUSE', 'PRESS', shift=True)
    # ??? kmi.properties.mode = 'SCALE'
    # ??? kmi = km.keymap_items.new('brush.stencil_control', 'RIGHTMOUSE', 'PRESS', ctrl=True)
    # ??? kmi.properties.mode = 'ROTATION'
    # ??? kmi = km.keymap_items.new('brush.stencil_control', 'RIGHTMOUSE', 'PRESS', alt=True)
    # ??? kmi.properties.mode = 'TRANSLATION'
    # ??? kmi.properties.texmode = 'SECONDARY'
    # ??? kmi = km.keymap_items.new('brush.stencil_control', 'RIGHTMOUSE', 'PRESS', shift=True, alt=True)
    # ??? kmi.properties.mode = 'SCALE'
    # ??? kmi.properties.texmode = 'SECONDARY'
    # ??? kmi = km.keymap_items.new('brush.stencil_control', 'RIGHTMOUSE', 'PRESS', ctrl=True, alt=True)
    # ??? kmi.properties.mode = 'ROTATION'
    # ??? kmi.properties.texmode = 'SECONDARY'
    #kmi = km.keymap_items.new('wm.context_menu_enum', 'A', 'PRESS')
    #kmi.properties.data_path = 'tool_settings.vertex_paint.brush.stroke_method'
    #kmi = km.keymap_items.new('wm.context_toggle', 'M', 'PRESS')
    #kmi.properties.data_path = 'weight_paint_object.data.use_paint_mask'
    #kmi = km.keymap_items.new('wm.context_toggle', 'V', 'PRESS')
    #kmi.properties.data_path = 'weight_paint_object.data.use_paint_mask_vertex'
    #kmi = km.keymap_items.new('wm.context_toggle', 'S', 'PRESS', shift=True)
    #kmi.properties.data_path = 'tool_settings.weight_paint.brush.use_smooth_stroke'


def MapAdd_ModalStandard(kc):
    """ Standard Modal Map
        Super basic modal stuff that applies globally in Blender.
    """
    km = kc.keymaps.new('Standard Modal Map', space_type='EMPTY', region_type='WINDOW', modal=True)

    kmi = km.keymap_items.new_modal('CANCEL', 'ESC', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('APPLY', 'LEFTMOUSE', 'ANY', any=True)
    kmi = km.keymap_items.new_modal('APPLY', 'RET', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('APPLY', 'NUMPAD_ENTER', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('STEP10', 'LEFT_CTRL', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('STEP10_OFF', 'LEFT_CTRL', 'RELEASE', any=True)


def MapAdd_ModalTransform(kc):
    """ Transform Modal Map
        Keys for when the user is in a transform mode, such as grab/rotate/scale.
    """
    km = kc.keymaps.new('Transform Modal Map', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Cancel
    kmi = km.keymap_items.new_modal('CANCEL', 'ESC', 'PRESS', any=True)

    # Confirm
    kmi = km.keymap_items.new_modal('CONFIRM', 'LEFTMOUSE', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('CONFIRM', 'RET', 'CLICK', any=True)
    kmi = km.keymap_items.new_modal('CONFIRM', 'NUMPAD_ENTER', 'CLICK', any=True)

    # Snapping
    kmi = km.keymap_items.new_modal('SNAP_TOGGLE', 'TAB', 'PRESS', shift=True)
    kmi = km.keymap_items.new_modal('SNAP_INV_ON', 'LEFT_CTRL', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('SNAP_INV_OFF', 'LEFT_CTRL', 'RELEASE', any=True)
    kmi = km.keymap_items.new_modal('SNAP_INV_ON', 'RIGHT_CTRL', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('SNAP_INV_OFF', 'RIGHT_CTRL', 'RELEASE', any=True)
    kmi = km.keymap_items.new_modal('ADD_SNAP', 'A', 'CLICK')
    kmi = km.keymap_items.new_modal('REMOVE_SNAP', 'A', 'CLICK', alt=True)

    # Proportional edit adjusting
    kmi = km.keymap_items.new_modal('PROPORTIONAL_SIZE_UP', 'PAGE_UP', 'PRESS')
    kmi = km.keymap_items.new_modal('PROPORTIONAL_SIZE_DOWN', 'PAGE_DOWN', 'PRESS')
    kmi = km.keymap_items.new_modal('PROPORTIONAL_SIZE_UP', 'WHEELDOWNMOUSE', 'PRESS')
    kmi = km.keymap_items.new_modal('PROPORTIONAL_SIZE_DOWN', 'WHEELUPMOUSE', 'PRESS')

    # Auto-ik adjusting
    kmi = km.keymap_items.new_modal('AUTOIK_CHAIN_LEN_UP', 'PAGE_UP', 'PRESS', shift=True)
    kmi = km.keymap_items.new_modal('AUTOIK_CHAIN_LEN_DOWN', 'PAGE_DOWN', 'PRESS', shift=True)
    kmi = km.keymap_items.new_modal('AUTOIK_CHAIN_LEN_UP', 'WHEELDOWNMOUSE', 'PRESS', shift=True)
    kmi = km.keymap_items.new_modal('AUTOIK_CHAIN_LEN_DOWN', 'WHEELUPMOUSE', 'PRESS', shift=True)

    # Constraining to axes
    kmi = km.keymap_items.new_modal('AXIS_X', 'X', 'CLICK')
    kmi = km.keymap_items.new_modal('AXIS_Y', 'Y', 'CLICK')
    kmi = km.keymap_items.new_modal('AXIS_Z', 'Z', 'CLICK')
    kmi = km.keymap_items.new_modal('PLANE_X', 'X', 'CLICK', shift=True)
    kmi = km.keymap_items.new_modal('PLANE_Y', 'Y', 'CLICK', shift=True)
    kmi = km.keymap_items.new_modal('PLANE_Z', 'Z', 'CLICK', shift=True)

    # Overrides ("No, really, actually translate") and trackball rotate
    kmi = km.keymap_items.new_modal('TRANSLATE', TRANSLATE_KEY, 'PRESS')
    kmi = km.keymap_items.new_modal('ROTATE', ROTATE_KEY, 'PRESS')
    kmi = km.keymap_items.new_modal('RESIZE', SCALE_KEY, 'PRESS')


def MapAdd_ModalBorderSelect(kc):
    """ Border Select Modal Map
        Determines behavior when in border select tool.
    """
    km = kc.keymaps.new('Gesture Border', space_type='EMPTY', region_type='WINDOW', modal=True)

    kmi = km.keymap_items.new_modal('CANCEL', 'ESC', 'PRESS', any=True)

    kmi = km.keymap_items.new_modal('BEGIN', 'LEFTMOUSE', 'PRESS')
    kmi = km.keymap_items.new_modal('SELECT', 'LEFTMOUSE', 'RELEASE')
    kmi = km.keymap_items.new_modal('SELECT', 'LEFTMOUSE', 'RELEASE', shift=True)
    kmi = km.keymap_items.new_modal('DESELECT', 'LEFTMOUSE', 'RELEASE', ctrl=True)


def MapAdd_AnimationGlobal(kc):
    # Map Frames
    km = kc.keymaps.new('Frames', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Forward/backward 1 frame
    kmi = km.keymap_items.new('screen.frame_offset', 'LEFT_ARROW', 'PRESS')
    kmi.properties.delta = -1
    kmi = km.keymap_items.new('screen.frame_offset', 'RIGHT_ARROW', 'PRESS')
    kmi.properties.delta = 1
    #kmi = km.keymap_items.new('screen.frame_offset', 'WHEELDOWNMOUSE', 'PRESS', alt=True)
    #kmi.properties.delta = 1
    #kmi = km.keymap_items.new('screen.frame_offset', 'WHEELUPMOUSE', 'PRESS', alt=True)
    #kmi.properties.delta = -1

    # Forward/backward 10 frames
    kmi = km.keymap_items.new('screen.frame_offset', 'LEFT_ARROW', 'PRESS', shift=True)
    kmi.properties.delta = -10
    kmi = km.keymap_items.new('screen.frame_offset', 'RIGHT_ARROW', 'PRESS', shift=True)
    kmi.properties.delta = 10
    
    # Jump to prev/next keyframe
    kmi = km.keymap_items.new('screen.keyframe_jump', 'UP_ARROW', 'PRESS')
    kmi.properties.next = True
    kmi = km.keymap_items.new('screen.keyframe_jump', 'DOWN_ARROW', 'PRESS')
    kmi.properties.next = False
    
    # Jump to start/end of frame range
    kmi = km.keymap_items.new('screen.frame_jump', 'UP_ARROW', 'PRESS', shift=True)
    kmi.properties.end = True
    kmi = km.keymap_items.new('screen.frame_jump', 'DOWN_ARROW', 'PRESS', shift=True)
    kmi.properties.end = False
    #kmi = km.keymap_items.new('screen.frame_jump', 'MEDIA_LAST', 'PRESS')
    #kmi.properties.end = True
    #kmi = km.keymap_items.new('screen.frame_jump', 'MEDIA_FIRST', 'PRESS')
    #kmi.properties.end = False
    
    # Animation playback
    kmi = km.keymap_items.new('screen.animation_play', 'A', 'PRESS', alt=True)
    kmi = km.keymap_items.new('screen.animation_play', 'MEDIA_PLAY', 'PRESS')
    kmi = km.keymap_items.new('screen.animation_play', 'A', 'PRESS', shift=True, alt=True)
    kmi.properties.reverse = True
    kmi = km.keymap_items.new('screen.animation_cancel', 'ESC', 'PRESS')
    kmi = km.keymap_items.new('screen.animation_cancel', 'MEDIA_STOP', 'PRESS')


def MapAdd_AnimationSpaces(kc):
    # Map Animation
    km = kc.keymaps.new('Animation', space_type='EMPTY', region_type='WINDOW', modal=False)
    
    # Scrub timeline
    kmi = km.keymap_items.new('anim.change_frame', 'RIGHTMOUSE', 'PRESS')
    
    # Switch time display
    kmi = km.keymap_items.new('wm.context_toggle', 'T', 'PRESS', ctrl=True)
    kmi.properties.data_path = 'space_data.show_seconds'
    
    # Set preview range
    # TODO: should this really be here?
    kmi = km.keymap_items.new('anim.previewrange_set', 'P', 'PRESS')
    kmi = km.keymap_items.new('anim.previewrange_clear', 'P', 'PRESS', alt=True)


def MapAdd_Markers(kc):
    # Map Markers
    km = kc.keymaps.new('Markers', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Create markers
    kmi = km.keymap_items.new('marker.add', 'M', 'PRESS')
    kmi = km.keymap_items.new('marker.duplicate', 'D', 'PRESS', shift=True)
    
    # Delete markers
    kmi = km.keymap_items.new('marker.delete', 'X', 'PRESS')
    
    # Name markers
    kmi = km.keymap_items.new('marker.rename', 'M', 'PRESS', ctrl=True)
    
    # Move markers
    kmi = km.keymap_items.new('marker.move', TRANSLATE_KEY, 'PRESS')
    #kmi = km.keymap_items.new('marker.move', 'EVT_TWEAK_S', 'ANY')
    
    # Marker selection
    # TODO: shift = add, ctrl = remove
    kmi = km.keymap_items.new('marker.select', 'SELECTMOUSE', 'CLICK')
    kmi = km.keymap_items.new('marker.select', 'SELECTMOUSE', 'CLICK', shift=True)
    kmi.properties.extend = True
    kmi = km.keymap_items.new('marker.select_border', 'EVT_TWEAK_S', 'ANY')
    kmi = km.keymap_items.new('marker.select_all', 'A', 'PRESS')
    
    # Select associated camera
    # TODO: shift = add, ctrl = remove
    kmi = km.keymap_items.new('marker.select', 'SELECTMOUSE', 'PRESS', alt=True)
    kmi.properties.extend = False
    kmi.properties.camera = True
    kmi = km.keymap_items.new('marker.select', 'SELECTMOUSE', 'PRESS', shift=True, alt=True)
    kmi.properties.extend = True
    kmi.properties.camera = True
    
    # Bind marker to camera
    kmi = km.keymap_items.new('marker.camera_bind', 'B', 'PRESS', ctrl=True)


# TODO
def MapAdd_ArmaturePose(kc):
    # Map Pose
    km = kc.keymaps.new('Pose', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Keyframing
    kmi = km.keymap_items.new('anim.keyframe_insert_menu', KEYFRAME_KEY, 'PRESS')
    kmi = km.keymap_items.new('anim.keyframe_delete_v3d', KEYFRAME_KEY, 'PRESS', alt=True)
    kmi = km.keymap_items.new('anim.keying_set_active_set', KEYFRAME_KEY, 'PRESS', shift=True, ctrl=True, alt=True)

    # Hiding
    kmi = km.keymap_items.new('pose.hide', 'H', 'PRESS')
    kmi.properties.unselected = False
    kmi = km.keymap_items.new('pose.hide', 'H', 'PRESS', shift=True)
    kmi.properties.unselected = True
    kmi = km.keymap_items.new('pose.reveal', 'H', 'PRESS', alt=True)

    # Selection
    kmi = km.keymap_items.new('pose.select_all', 'A', 'PRESS')
    kmi.properties.action = 'TOGGLE'
    kmi = km.keymap_items.new('pose.select_all', 'I', 'PRESS', ctrl=True)
    kmi.properties.action = 'INVERT'
    kmi = km.keymap_items.new('pose.select_hierarchy', 'LEFT_BRACKET', 'PRESS')
    kmi.properties.direction = 'PARENT'
    kmi.properties.extend = False
    kmi = km.keymap_items.new('pose.select_hierarchy', 'LEFT_BRACKET', 'PRESS', shift=True)
    kmi.properties.direction = 'PARENT'
    kmi.properties.extend = True
    kmi = km.keymap_items.new('pose.select_hierarchy', 'RIGHT_BRACKET', 'PRESS')
    kmi.properties.direction = 'CHILD'
    kmi.properties.extend = False
    kmi = km.keymap_items.new('pose.select_hierarchy', 'RIGHT_BRACKET', 'PRESS', shift=True)
    kmi.properties.direction = 'CHILD'
    kmi.properties.extend = True
    kmi = km.keymap_items.new('pose.select_grouped', 'G', 'PRESS', shift=True)
    #kmi = km.keymap_items.new('pose.select_linked', 'L', 'PRESS')
    #kmi = km.keymap_items.new('pose.select_flip_active', 'F', 'PRESS', shift=True)

    # Transforms
    kmi = km.keymap_items.new('pose.rot_clear', ROTATE_KEY, 'PRESS', alt=True)
    kmi = km.keymap_items.new('pose.loc_clear', TRANSLATE_KEY, 'PRESS', alt=True)
    kmi = km.keymap_items.new('pose.scale_clear', SCALE_KEY, 'PRESS', alt=True)
    kmi = km.keymap_items.new('pose.quaternions_flip', 'I', 'PRESS') # "invert" quaternion
    #kmi = km.keymap_items.new('pose.rotation_mode_set', 'R', 'PRESS', ctrl=True)

    # Pose copy/paste
    kmi = km.keymap_items.new('pose.copy', 'C', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('pose.paste', 'V', 'PRESS', ctrl=True)
    kmi.properties.flipped = False
    kmi = km.keymap_items.new('pose.paste', 'V', 'PRESS', shift=True, ctrl=True)
    kmi.properties.flipped = True
    
    # Pose tools
    kmi = km.keymap_items.new('pose.breakdown', 'T', 'PRESS')
    kmi = km.keymap_items.new('pose.relax', 'R', 'PRESS')
    kmi = km.keymap_items.new('pose.push', 'R', 'PRESS', shift=True)
    
    

    # Pose library
    kmi = km.keymap_items.new('poselib.browse_interactive', 'L', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('poselib.pose_add', 'L', 'PRESS', shift=True)
    kmi = km.keymap_items.new('poselib.pose_remove', 'L', 'PRESS', alt=True)
    kmi = km.keymap_items.new('poselib.pose_rename', 'L', 'PRESS', shift=True, ctrl=True)

    # Specials menu
    kmi = km.keymap_items.new('wm.call_menu', SPECIALS_MENU_KEY, 'PRESS')
    kmi.properties.name = 'VIEW3D_MT_pose_specials'

    # Object-mode emulation
    #kmi = km.keymap_items.new('object.parent_set', 'P', 'PRESS', ctrl=True)
    #kmi = km.keymap_items.new('wm.call_menu', 'A', 'PRESS', shift=True)
    #kmi.properties.name = 'INFO_MT_add'
    
    # TODO: operators relevant to rigging
    #kmi = km.keymap_items.new('wm.call_menu', 'W', 'PRESS', shift=True)
    #kmi.properties.name = 'VIEW3D_MT_bone_options_toggle'
    #kmi = km.keymap_items.new('wm.call_menu', 'W', 'PRESS', shift=True, ctrl=True)
    #kmi.properties.name = 'VIEW3D_MT_bone_options_enable'
    #kmi = km.keymap_items.new('wm.call_menu', 'W', 'PRESS', alt=True)
    #kmi.properties.name = 'VIEW3D_MT_bone_options_disable'
    #kmi = km.keymap_items.new('wm.call_menu', 'A', 'PRESS', ctrl=True)
    #kmi.properties.name = 'VIEW3D_MT_pose_apply'
    
    #kmi = km.keymap_items.new('pose.constraint_add_with_targets', 'C', 'PRESS', shift=True, ctrl=True)
    #kmi = km.keymap_items.new('pose.constraints_clear', 'C', 'PRESS', ctrl=True, alt=True)
    #kmi = km.keymap_items.new('pose.ik_add', 'I', 'PRESS', shift=True)
    #kmi = km.keymap_items.new('pose.ik_clear', 'I', 'PRESS', ctrl=True, alt=True)
    #kmi = km.keymap_items.new('wm.call_menu', 'G', 'PRESS', ctrl=True)
    #kmi.properties.name = 'VIEW3D_MT_pose_group'
    
    #kmi = km.keymap_items.new('armature.layers_show_all', 'ACCENT_GRAVE', 'PRESS', ctrl=True)
    #kmi = km.keymap_items.new('armature.armature_layers', 'M', 'PRESS', shift=True)
    #kmi = km.keymap_items.new('pose.bone_layers', 'M', 'PRESS')
    #kmi = km.keymap_items.new('transform.transform', 'S', 'PRESS', ctrl=True, alt=True)
    #kmi.properties.mode = 'BONE_SIZE'
    
    
    


def MapAdd_FileBrowserGlobal(kc):
    # Map File Browser
    km = kc.keymaps.new('File Browser', space_type='FILE_BROWSER', region_type='WINDOW', modal=False)

    kmi = km.keymap_items.new('file.bookmark_toggle', 'N', 'PRESS')
    kmi = km.keymap_items.new('file.parent', 'P', 'PRESS')
    kmi = km.keymap_items.new('file.bookmark_add', 'B', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('file.hidedot', 'H', 'PRESS')
    kmi = km.keymap_items.new('file.previous', 'BACK_SPACE', 'PRESS')
    kmi = km.keymap_items.new('file.next', 'BACK_SPACE', 'PRESS', shift=True)
    kmi = km.keymap_items.new('file.directory_new', 'I', 'PRESS')
    kmi = km.keymap_items.new('file.delete', 'X', 'PRESS')
    kmi = km.keymap_items.new('file.delete', 'DEL', 'PRESS')
    kmi = km.keymap_items.new('file.smoothscroll', 'TIMER1', 'ANY', any=True)

def MapAdd_FileBrowserMain(kc):
    # Map File Browser Main
    km = kc.keymaps.new('File Browser Main', space_type='FILE_BROWSER', region_type='WINDOW', modal=False)

    kmi = km.keymap_items.new('file.execute', 'LEFTMOUSE', 'DOUBLE_CLICK')
    kmi.properties.need_active = True
    kmi = km.keymap_items.new('file.select', 'LEFTMOUSE', 'CLICK')
    kmi = km.keymap_items.new('file.select', 'LEFTMOUSE', 'CLICK', shift=True)
    kmi.properties.extend = True
    kmi = km.keymap_items.new('file.select', 'LEFTMOUSE', 'CLICK', alt=True)
    kmi.properties.extend = True
    kmi.properties.fill = True
    kmi = km.keymap_items.new('file.select_all_toggle', 'A', 'PRESS')
    kmi = km.keymap_items.new('file.refresh', 'NUMPAD_PERIOD', 'PRESS')
    kmi = km.keymap_items.new('file.select_border', 'B', 'PRESS')
    kmi = km.keymap_items.new('file.select_border', 'EVT_TWEAK_L', 'ANY')
    kmi = km.keymap_items.new('file.rename', 'LEFTMOUSE', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('file.highlight', 'MOUSEMOVE', 'ANY', any=True)
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_PLUS', 'PRESS')
    kmi.properties.increment = 1
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_PLUS', 'PRESS', shift=True)
    kmi.properties.increment = 10
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_PLUS', 'PRESS', ctrl=True)
    kmi.properties.increment = 100
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_MINUS', 'PRESS')
    kmi.properties.increment = -1
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_MINUS', 'PRESS', shift=True)
    kmi.properties.increment = -10
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_MINUS', 'PRESS', ctrl=True)
    kmi.properties.increment = -100

def MapAdd_FileBrowserButtons(kc):
    # Map File Browser Buttons
    km = kc.keymaps.new('File Browser Buttons', space_type='FILE_BROWSER', region_type='WINDOW', modal=False)

    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_PLUS', 'PRESS')
    kmi.properties.increment = 1
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_PLUS', 'PRESS', shift=True)
    kmi.properties.increment = 10
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_PLUS', 'PRESS', ctrl=True)
    kmi.properties.increment = 100
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_MINUS', 'PRESS')
    kmi.properties.increment = -1
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_MINUS', 'PRESS', shift=True)
    kmi.properties.increment = -10
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_MINUS', 'PRESS', ctrl=True)
    kmi.properties.increment = -100


def MapAdd_Outliner(kc):
    # Map Outliner
    km = kc.keymaps.new('Outliner', space_type='OUTLINER', region_type='WINDOW', modal=False)

    # Selection
    kmi = km.keymap_items.new('outliner.item_activate', 'LEFTMOUSE', 'CLICK')
    kmi.properties.extend = False
    kmi.properties.recursive = False
    kmi = km.keymap_items.new('outliner.item_activate', 'LEFTMOUSE', 'CLICK', shift=True)
    kmi.properties.extend = True
    kmi.properties.recursive = False
    kmi = km.keymap_items.new('outliner.item_activate', 'LEFTMOUSE', 'CLICK', ctrl=True)
    kmi.properties.extend = False
    kmi.properties.recursive = True
    kmi = km.keymap_items.new('outliner.item_activate', 'LEFTMOUSE', 'CLICK', shift=True, ctrl=True)
    kmi.properties.extend = True
    kmi.properties.recursive = True
    # kmi = km.keymap_items.new('outliner.select_border', 'B', 'PRESS')
    kmi = km.keymap_items.new('outliner.selected_toggle', 'A', 'PRESS')

    # Toggle item properties
    kmi = km.keymap_items.new('outliner.renderability_toggle', 'R', 'PRESS')
    kmi = km.keymap_items.new('outliner.selectability_toggle', 'S', 'PRESS')
    kmi = km.keymap_items.new('outliner.visibility_toggle', 'V', 'PRESS')

    # Expand / Collapse items
    kmi = km.keymap_items.new('outliner.item_openclose', 'RET', 'PRESS')
    kmi.properties.all = False
    kmi = km.keymap_items.new('outliner.item_openclose', 'RET', 'PRESS', shift=True)
    kmi.properties.all = True
    kmi = km.keymap_items.new('outliner.show_one_level', 'NUMPAD_PLUS', 'PRESS')
    kmi = km.keymap_items.new('outliner.show_one_level', 'NUMPAD_MINUS', 'PRESS')
    kmi.properties.open = False
    kmi = km.keymap_items.new('outliner.expanded_toggle', 'A', 'PRESS', shift=True)
    kmi = km.keymap_items.new('outliner.show_hierarchy', 'HOME', 'PRESS')

    # Rename items
    kmi = km.keymap_items.new('outliner.item_rename', 'LEFTMOUSE', 'DOUBLE_CLICK')
    kmi = km.keymap_items.new('outliner.item_rename', 'LEFTMOUSE', 'PRESS', ctrl=True)
    
    # Right-click menu
    kmi = km.keymap_items.new('outliner.operation', 'RIGHTMOUSE', 'PRESS')
    
    # Navigtion
    kmi = km.keymap_items.new('outliner.show_active', 'PERIOD', 'PRESS')
    kmi = km.keymap_items.new('outliner.show_active', 'NUMPAD_PERIOD', 'PRESS')
    kmi = km.keymap_items.new('outliner.scroll_page', 'PAGE_DOWN', 'PRESS')
    kmi = km.keymap_items.new('outliner.scroll_page', 'PAGE_UP', 'PRESS')
    kmi.properties.up = True
    
    # Misc
    # TODO: keying set alternative
    #kmi = km.keymap_items.new('outliner.keyingset_add_selected', 'K', 'PRESS')
    #kmi = km.keymap_items.new('outliner.keyingset_remove_selected', 'K', 'PRESS', alt=True)
    kmi = km.keymap_items.new('anim.keyframe_insert', KEYFRAME_KEY, 'PRESS')
    kmi = km.keymap_items.new('anim.keyframe_delete', KEYFRAME_KEY, 'PRESS', alt=True)
    kmi = km.keymap_items.new('outliner.drivers_add_selected', 'D', 'PRESS')
    kmi = km.keymap_items.new('outliner.drivers_delete_selected', 'D', 'PRESS', alt=True)


def MapAdd_Console(kc):
    # Map Console
    km = kc.keymaps.new('Console', space_type='CONSOLE', region_type='WINDOW', modal=False)

    # Cursor navigation
    kmi = km.keymap_items.new('console.move', 'LEFT_ARROW', 'PRESS')
    kmi.properties.type = 'PREVIOUS_CHARACTER'
    kmi = km.keymap_items.new('console.move', 'RIGHT_ARROW', 'PRESS')
    kmi.properties.type = 'NEXT_CHARACTER'
    kmi = km.keymap_items.new('console.move', 'LEFT_ARROW', 'PRESS', ctrl=True)
    kmi.properties.type = 'PREVIOUS_WORD'
    kmi = km.keymap_items.new('console.move', 'RIGHT_ARROW', 'PRESS', ctrl=True)
    kmi.properties.type = 'NEXT_WORD'
    kmi = km.keymap_items.new('console.move', 'HOME', 'PRESS')
    kmi.properties.type = 'LINE_BEGIN'
    kmi = km.keymap_items.new('console.move', 'END', 'PRESS')
    kmi.properties.type = 'LINE_END'
    
    # Console history
    kmi = km.keymap_items.new('console.history_cycle', 'UP_ARROW', 'PRESS')
    kmi.properties.reverse = True
    kmi = km.keymap_items.new('console.history_cycle', 'DOWN_ARROW', 'PRESS')
    kmi.properties.reverse = False
    
    # Font size
    kmi = km.keymap_items.new('wm.context_cycle_int', 'WHEELUPMOUSE', 'PRESS', ctrl=True)
    kmi.properties.data_path = 'space_data.font_size'
    kmi.properties.reverse = False
    kmi = km.keymap_items.new('wm.context_cycle_int', 'WHEELDOWNMOUSE', 'PRESS', ctrl=True)
    kmi.properties.data_path = 'space_data.font_size'
    kmi.properties.reverse = True
    kmi = km.keymap_items.new('wm.context_cycle_int', 'NUMPAD_PLUS', 'PRESS', ctrl=True)
    kmi.properties.data_path = 'space_data.font_size'
    kmi.properties.reverse = False
    kmi = km.keymap_items.new('wm.context_cycle_int', 'NUMPAD_MINUS', 'PRESS', ctrl=True)
    kmi.properties.data_path = 'space_data.font_size'
    kmi.properties.reverse = True
    
    # Indenting
    kmi = km.keymap_items.new('console.insert', 'TAB', 'PRESS', ctrl=True)
    kmi.properties.text = '\t'
    kmi = km.keymap_items.new('console.indent', 'TAB', 'PRESS')
    kmi = km.keymap_items.new('console.unindent', 'TAB', 'PRESS', shift=True)
    
    # Deleting
    kmi = km.keymap_items.new('console.delete', 'DEL', 'PRESS')
    kmi.properties.type = 'NEXT_CHARACTER'
    kmi = km.keymap_items.new('console.delete', 'BACK_SPACE', 'PRESS')
    kmi.properties.type = 'PREVIOUS_CHARACTER'
    kmi = km.keymap_items.new('console.delete', 'BACK_SPACE', 'PRESS', shift=True)
    kmi.properties.type = 'PREVIOUS_CHARACTER'
    kmi = km.keymap_items.new('console.delete', 'DEL', 'PRESS', ctrl=True)
    kmi.properties.type = 'NEXT_WORD'
    kmi = km.keymap_items.new('console.delete', 'BACK_SPACE', 'PRESS', ctrl=True)
    kmi.properties.type = 'PREVIOUS_WORD'
    
    # Clear line
    kmi = km.keymap_items.new('console.clear_line', 'RET', 'PRESS', shift=True)
    
    # Copy/paste
    kmi = km.keymap_items.new('console.copy_as_script', 'C', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('console.copy', 'C', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('console.paste', 'V', 'PRESS', ctrl=True)
    
    # Execute code
    kmi = km.keymap_items.new('console.execute', 'RET', 'PRESS')
    kmi.properties.interactive = True
    kmi = km.keymap_items.new('console.execute', 'NUMPAD_ENTER', 'PRESS')
    kmi.properties.interactive = True
    
    # Auto-complete
    kmi = km.keymap_items.new('console.autocomplete', 'SPACE', 'PRESS', ctrl=True)
    
    # Selection
    kmi = km.keymap_items.new('console.select_set', 'LEFTMOUSE', 'PRESS')
    
    # Text input
    kmi = km.keymap_items.new('console.insert', 'TEXTINPUT', 'ANY', any=True)


# TODO: sort out the text editor keymap
def MapAdd_TextEditorGeneric(kc):
    # Map Text Generic
    km = kc.keymaps.new('Text Generic', space_type='TEXT_EDITOR', region_type='WINDOW', modal=False)

    kmi = km.keymap_items.new('text.start_find', 'F', 'PRESS', ctrl=True)

def MapAdd_TextEditor(kc):
    # Map Text
    km = kc.keymaps.new('Text', space_type='TEXT_EDITOR', region_type='WINDOW', modal=False)

    # Font size
    kmi = km.keymap_items.new('wm.context_cycle_int', 'WHEELUPMOUSE', 'PRESS', ctrl=True)
    kmi.properties.data_path = 'space_data.font_size'
    kmi.properties.reverse = False
    kmi = km.keymap_items.new('wm.context_cycle_int', 'WHEELDOWNMOUSE', 'PRESS', ctrl=True)
    kmi.properties.data_path = 'space_data.font_size'
    kmi.properties.reverse = True
    kmi = km.keymap_items.new('wm.context_cycle_int', 'NUMPAD_PLUS', 'PRESS', ctrl=True)
    kmi.properties.data_path = 'space_data.font_size'
    kmi.properties.reverse = False
    kmi = km.keymap_items.new('wm.context_cycle_int', 'NUMPAD_MINUS', 'PRESS', ctrl=True)
    kmi.properties.data_path = 'space_data.font_size'
    kmi.properties.reverse = True
    
    # File management
    kmi = km.keymap_items.new('text.new', 'N', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('text.open', 'O', 'PRESS', alt=True)
    kmi = km.keymap_items.new('text.reload', 'R', 'PRESS', alt=True)
    kmi = km.keymap_items.new('text.save', 'S', 'PRESS', alt=True)
    kmi = km.keymap_items.new('text.save_as', 'S', 'PRESS', shift=True, ctrl=True, alt=True)
    
    # Run script
    kmi = km.keymap_items.new('text.run_script', 'P', 'PRESS', alt=True)
    
    # Copy/paste etc.
    kmi = km.keymap_items.new('text.cut', 'X', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('text.copy', 'C', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('text.paste', 'V', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('text.cut', 'DEL', 'PRESS', shift=True)
    kmi = km.keymap_items.new('text.copy', 'INSERT', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('text.paste', 'INSERT', 'PRESS', shift=True)
    kmi = km.keymap_items.new('text.duplicate_line', 'D', 'PRESS', ctrl=True)
    
    # Find / replace
    kmi = km.keymap_items.new('text.find', 'G', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('text.replace', 'H', 'PRESS', ctrl=True)
    
    # Text-to-3D-object
    kmi = km.keymap_items.new('text.to_3d_object', 'M', 'PRESS', alt=True)
    kmi.properties.split_lines = False
    kmi = km.keymap_items.new('text.to_3d_object', 'M', 'PRESS', ctrl=True)
    kmi.properties.split_lines = True
    
    # Move lines
    kmi = km.keymap_items.new('text.move_lines', 'UP_ARROW', 'PRESS', shift=True, ctrl=True)
    kmi.properties.direction = 'UP'
    kmi = km.keymap_items.new('text.move_lines', 'DOWN_ARROW', 'PRESS', shift=True, ctrl=True)
    kmi.properties.direction = 'DOWN'
    
    # Linebreak, indent, etc.
    kmi = km.keymap_items.new('text.line_break', 'RET', 'PRESS')
    kmi = km.keymap_items.new('text.line_break', 'NUMPAD_ENTER', 'PRESS')
    kmi = km.keymap_items.new('text.indent', 'TAB', 'PRESS')
    kmi = km.keymap_items.new('text.unindent', 'TAB', 'PRESS', shift=True)
    kmi = km.keymap_items.new('text.uncomment', 'D', 'PRESS', shift=True, ctrl=True)
    
    # Cursor navigation
    kmi = km.keymap_items.new('text.jump', 'J', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('text.move', 'HOME', 'PRESS')
    kmi.properties.type = 'LINE_BEGIN'
    kmi = km.keymap_items.new('text.move', 'END', 'PRESS')
    kmi.properties.type = 'LINE_END'
    kmi = km.keymap_items.new('text.move', 'E', 'PRESS', ctrl=True)
    kmi.properties.type = 'LINE_END'
    kmi = km.keymap_items.new('text.move', 'E', 'PRESS', shift=True, ctrl=True)
    kmi.properties.type = 'LINE_END'
    kmi = km.keymap_items.new('text.move', 'LEFT_ARROW', 'PRESS')
    kmi.properties.type = 'PREVIOUS_CHARACTER'
    kmi = km.keymap_items.new('text.move', 'RIGHT_ARROW', 'PRESS')
    kmi.properties.type = 'NEXT_CHARACTER'
    kmi = km.keymap_items.new('text.move', 'LEFT_ARROW', 'PRESS', ctrl=True)
    kmi.properties.type = 'PREVIOUS_WORD'
    kmi = km.keymap_items.new('text.move', 'RIGHT_ARROW', 'PRESS', ctrl=True)
    kmi.properties.type = 'NEXT_WORD'
    kmi = km.keymap_items.new('text.move', 'UP_ARROW', 'PRESS')
    kmi.properties.type = 'PREVIOUS_LINE'
    kmi = km.keymap_items.new('text.move', 'DOWN_ARROW', 'PRESS')
    kmi.properties.type = 'NEXT_LINE'
    kmi = km.keymap_items.new('text.move', 'PAGE_UP', 'PRESS')
    kmi.properties.type = 'PREVIOUS_PAGE'
    kmi = km.keymap_items.new('text.move', 'PAGE_DOWN', 'PRESS')
    kmi.properties.type = 'NEXT_PAGE'
    kmi = km.keymap_items.new('text.move', 'HOME', 'PRESS', ctrl=True)
    kmi.properties.type = 'FILE_TOP'
    kmi = km.keymap_items.new('text.move', 'END', 'PRESS', ctrl=True)
    kmi.properties.type = 'FILE_BOTTOM'
    
    # Selection
    kmi = km.keymap_items.new('text.selection_set', 'EVT_TWEAK_L', 'ANY')
    kmi = km.keymap_items.new('text.selection_set', 'LEFTMOUSE', 'PRESS', shift=True)
    kmi.properties.select = True
    kmi = km.keymap_items.new('text.cursor_set', 'LEFTMOUSE', 'PRESS')
    kmi = km.keymap_items.new('text.select_all', 'A', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('text.select_line', 'A', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('text.select_word', 'LEFTMOUSE', 'DOUBLE_CLICK')
    kmi = km.keymap_items.new('text.move_select', 'HOME', 'PRESS', shift=True)
    kmi.properties.type = 'LINE_BEGIN'
    kmi = km.keymap_items.new('text.move_select', 'END', 'PRESS', shift=True)
    kmi.properties.type = 'LINE_END'
    kmi = km.keymap_items.new('text.move_select', 'LEFT_ARROW', 'PRESS', shift=True)
    kmi.properties.type = 'PREVIOUS_CHARACTER'
    kmi = km.keymap_items.new('text.move_select', 'RIGHT_ARROW', 'PRESS', shift=True)
    kmi.properties.type = 'NEXT_CHARACTER'
    kmi = km.keymap_items.new('text.move_select', 'LEFT_ARROW', 'PRESS', shift=True, ctrl=True)
    kmi.properties.type = 'PREVIOUS_WORD'
    kmi = km.keymap_items.new('text.move_select', 'RIGHT_ARROW', 'PRESS', shift=True, ctrl=True)
    kmi.properties.type = 'NEXT_WORD'
    kmi = km.keymap_items.new('text.move_select', 'UP_ARROW', 'PRESS', shift=True)
    kmi.properties.type = 'PREVIOUS_LINE'
    kmi = km.keymap_items.new('text.move_select', 'DOWN_ARROW', 'PRESS', shift=True)
    kmi.properties.type = 'NEXT_LINE'
    kmi = km.keymap_items.new('text.move_select', 'PAGE_UP', 'PRESS', shift=True)
    kmi.properties.type = 'PREVIOUS_PAGE'
    kmi = km.keymap_items.new('text.move_select', 'PAGE_DOWN', 'PRESS', shift=True)
    kmi.properties.type = 'NEXT_PAGE'
    kmi = km.keymap_items.new('text.move_select', 'HOME', 'PRESS', shift=True, ctrl=True)
    kmi.properties.type = 'FILE_TOP'
    kmi = km.keymap_items.new('text.move_select', 'END', 'PRESS', shift=True, ctrl=True)
    kmi.properties.type = 'FILE_BOTTOM'
    
    # Deletion
    kmi = km.keymap_items.new('text.delete', 'DEL', 'PRESS')
    kmi.properties.type = 'NEXT_CHARACTER'
    kmi = km.keymap_items.new('text.delete', 'BACK_SPACE', 'PRESS')
    kmi.properties.type = 'PREVIOUS_CHARACTER'
    kmi = km.keymap_items.new('text.delete', 'BACK_SPACE', 'PRESS', shift=True)
    kmi.properties.type = 'PREVIOUS_CHARACTER'
    kmi = km.keymap_items.new('text.delete', 'DEL', 'PRESS', ctrl=True)
    kmi.properties.type = 'NEXT_WORD'
    kmi = km.keymap_items.new('text.delete', 'BACK_SPACE', 'PRESS', ctrl=True)
    kmi.properties.type = 'PREVIOUS_WORD'
    
    # Insert mode toggle
    kmi = km.keymap_items.new('text.overwrite_toggle', 'INSERT', 'PRESS')
    
    # Scrolling
    kmi = km.keymap_items.new('text.scroll_bar', 'LEFTMOUSE', 'PRESS')
    kmi = km.keymap_items.new('text.scroll_bar', 'MIDDLEMOUSE', 'PRESS')
    kmi = km.keymap_items.new('text.scroll', 'MIDDLEMOUSE', 'PRESS')
    kmi = km.keymap_items.new('text.scroll', 'TRACKPADPAN', 'ANY')
    kmi = km.keymap_items.new('text.scroll', 'WHEELUPMOUSE', 'PRESS')
    kmi.properties.lines = -1
    kmi = km.keymap_items.new('text.scroll', 'WHEELDOWNMOUSE', 'PRESS')
    kmi.properties.lines = 1
    
    # Right-click menu
    kmi = km.keymap_items.new('wm.call_menu', 'RIGHTMOUSE', 'PRESS', any=True)
    kmi.properties.name = 'TEXT_MT_toolbox'
    
    # Auto-complete
    kmi = km.keymap_items.new('text.autocomplete', 'SPACE', 'PRESS', ctrl=True)
    
    # ?
    kmi = km.keymap_items.new('text.line_number', 'TEXTINPUT', 'ANY', any=True)
    
    # Text input
    kmi = km.keymap_items.new('text.insert', 'TEXTINPUT', 'ANY', any=True)


# TODO: sort out node editor
def MapAdd_NodeEditorGeneric(kc):
    km = kc.keymaps.new('Node Generic', space_type='NODE_EDITOR', region_type='WINDOW', modal=False)

    kmi = km.keymap_items.new('node.toolbar', 'SEMI_COLON', 'PRESS')
    kmi = km.keymap_items.new('node.properties', 'QUOTE', 'PRESS')


def MapAdd_NodeEditor(kc):
    km = kc.keymaps.new('Node Editor', space_type='NODE_EDITOR', region_type='WINDOW', modal=False)

    # TODO: create a specials menu with useful but less-used commands
    #kmi = km.keymap_items.new('node.show_cyclic_dependencies', 'C', 'PRESS')
    
    # View navigation
    kmi = km.keymap_items.new('node.view_all', 'HOME', 'PRESS')
    kmi = km.keymap_items.new('node.view_selected', 'NUMPAD_PERIOD', 'PRESS')
    
    # Basic selection
    # TODO: replace/add/remove selection
    # TODO: create better model for node vs socket selection.  Right now
    #       extend-select is just over-loaded to do socket selection,
    #       which kind of sucks.  Fixing this will likely require
    #       C-code changes to Blender.
    # TODO: write tweak-move operator so that simple select can use click
    #       instead of press.
    kmi = km.keymap_items.new('node.select', 'SELECTMOUSE', 'PRESS') # Replace
    kmi.properties.extend = False
    kmi = km.keymap_items.new('node.select', 'SELECTMOUSE', 'PRESS', shift=True) # Add
    kmi.properties.extend = True
    #kmi = km.keymap_items.new('node.select', 'SELECTMOUSE', 'PRESS', ctrl=True) # Remove
    #kmi.properties.extend = False
    
    # Border selection
    # TODO: replace/add/remove selection
    kmi = km.keymap_items.new('node.select_border', 'EVT_TWEAK_S', 'ANY') # Replace
    kmi.properties.tweak = True
    #kmi = km.keymap_items.new('node.select_border', 'EVT_TWEAK_S', 'ANY', shift=True) # Add
    #kmi.properties.tweak = True
    #kmi = km.keymap_items.new('node.select_border', 'EVT_TWEAK_S', 'ANY', ctrl=True) # Remove
    #kmi.properties.tweak = True
    
    # Lasso select
    # TODO: replace/add/remove selection
    kmi = km.keymap_items.new('node.select_lasso', 'EVT_TWEAK_S', 'ANY', alt=True) # Add
    kmi.properties.deselect = False
    kmi = km.keymap_items.new('node.select_lasso', 'EVT_TWEAK_S', 'ANY', ctrl=True, alt=True) # Remove
    kmi.properties.deselect = True
    
    # Select all/invert
    kmi = km.keymap_items.new('node.select_all', 'A', 'PRESS')
    kmi.properties.action = 'TOGGLE'
    kmi = km.keymap_items.new('node.select_all', 'I', 'PRESS', ctrl=True)
    kmi.properties.action = 'INVERT'
    
    # Find node
    kmi = km.keymap_items.new('node.find_node', 'F', 'PRESS', ctrl=True)
    
    # Moving nodes
    # ??? kmi = km.keymap_items.new('node.translate_attach', TRANSLATE_KEY, 'PRESS')
    # ??? kmi = km.keymap_items.new('node.translate_attach', 'EVT_TWEAK_A', 'ANY')
    # ??? kmi = km.keymap_items.new('node.translate_attach', 'EVT_TWEAK_S', 'ANY')
    kmi = km.keymap_items.new('transform.translate', TRANSLATE_KEY, 'PRESS')
    kmi.properties.release_confirm = False
    kmi = km.keymap_items.new('transform.translate', 'EVT_TWEAK_L', 'ANY')
    kmi.properties.release_confirm = True
    kmi = km.keymap_items.new('transform.rotate', ROTATE_KEY, 'PRESS')
    kmi = km.keymap_items.new('transform.resize', SCALE_KEY, 'PRESS')
    
    # Resize node
    kmi = km.keymap_items.new('node.resize', 'LEFTMOUSE', 'PRESS')
    
    # Add nodes
    kmi = km.keymap_items.new('wm.call_menu', 'A', 'PRESS', shift=True)
    kmi.properties.name = 'NODE_MT_add'
    
    # Delete nodes
    kmi = km.keymap_items.new('node.delete', 'X', 'CLICK')
    kmi = km.keymap_items.new('node.delete', 'DEL', 'CLICK')
    kmi = km.keymap_items.new('node.delete_reconnect', 'X', 'PRESS', shift=True) # like "dissolve" in mesh editing
    kmi = km.keymap_items.new('node.delete_reconnect', 'DEL', 'PRESS', shift=True)
    
    # Duplicate nodes
    kmi = km.keymap_items.new('node.duplicate_move', 'D', 'PRESS', shift=True)
    kmi = km.keymap_items.new('node.duplicate_move_keep_inputs', 'D', 'PRESS', shift=True, ctrl=True)
    
    # Copy/paste nodes
    kmi = km.keymap_items.new('node.clipboard_copy', 'C', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('node.clipboard_paste', 'V', 'PRESS', ctrl=True)
    
    # Dragging links from sockets
    # TODO: these operators do not appear to work with tweak events, but
    #       they clearly should be triggered by them rather than by
    #       clicks/presses.  Investigate and fix.
    kmi = km.keymap_items.new('node.link', 'LEFTMOUSE', 'PRESS')
    kmi.properties.detach = False
    kmi = km.keymap_items.new('node.link', 'LEFTMOUSE', 'PRESS', ctrl=True)
    kmi.properties.detach = True
    
    # Connect selected sockets
    kmi = km.keymap_items.new('node.link_make', 'C', 'PRESS')
    kmi.properties.replace = False
    kmi = km.keymap_items.new('node.link_make', 'C', 'PRESS', shift=True)
    kmi.properties.replace = True
    
    # Hide and mute
    kmi = km.keymap_items.new('node.hide_toggle', 'H', 'PRESS')
    kmi = km.keymap_items.new('node.mute_toggle', 'M', 'PRESS')
    
    # Drag to cut links or add reroutes
    kmi = km.keymap_items.new('node.links_cut', 'RIGHTMOUSE', 'PRESS')
    kmi = km.keymap_items.new('node.add_reroute', 'RIGHTMOUSE', 'PRESS', shift=True)
    
    # Node groups
    kmi = km.keymap_items.new('node.group_make', 'G', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('node.group_ungroup', 'G', 'PRESS', alt=True)
    kmi = km.keymap_items.new('node.group_separate', 'Y', 'CLICK')
    kmi = km.keymap_items.new('node.group_edit', 'SPACE', 'PRESS')
    kmi.properties.exit = False
    kmi = km.keymap_items.new('node.group_edit', 'SPACE', 'PRESS', shift=True)
    kmi.properties.exit = True
    
    # Compositing backdrop
    # TODO: backdrop navigation should correspond to normal viewport
    #       navigation, just with alt held down.  Specifically, you can't
    #       alt-MMB-drag to zoom right now.  Fix (write a modal python
    #       operator).
    kmi = km.keymap_items.new('node.backimage_move', 'MIDDLEMOUSE', 'PRESS', alt=True)
    kmi = km.keymap_items.new('node.backimage_zoom', 'WHEELOUTMOUSE', 'PRESS', alt=True)
    kmi.properties.factor = 0.833329975605011
    kmi = km.keymap_items.new('node.backimage_zoom', 'WHEELINMOUSE', 'PRESS', alt=True)
    kmi.properties.factor = 1.2000000476837158
    kmi = km.keymap_items.new('node.backimage_zoom', 'NUMPAD_MINUS', 'PRESS', alt=True)
    kmi.properties.factor = 0.833329975605011
    kmi = km.keymap_items.new('node.backimage_zoom', 'NUMPAD_PLUS', 'PRESS', alt=True)
    kmi.properties.factor = 1.2000000476837158
    kmi = km.keymap_items.new('node.backimage_fit', 'HOME', 'PRESS', alt=True)
    kmi = km.keymap_items.new('node.backimage_sample', 'RIGHTMOUSE', 'PRESS', alt=True)
    kmi = km.keymap_items.new('node.viewer_border', 'V', 'PRESS', shift=True)

    # Compositing misc
    kmi = km.keymap_items.new('node.select_link_viewer', 'RIGHTMOUSE', 'PRESS', ctrl=True)
    #kmi = km.keymap_items.new('node.read_renderlayers', 'R', 'PRESS', ctrl=True)
    #kmi = km.keymap_items.new('node.read_fullsamplelayers', 'R', 'PRESS', shift=True)
    #kmi = km.keymap_items.new('node.render_changed', 'Z', 'PRESS')

    # TODO: sort these out
    # kmi = km.keymap_items.new('node.join', 'J', 'PRESS', ctrl=True)
    # ??? kmi = km.keymap_items.new('node.parent_set', 'P', 'PRESS', ctrl=True)
    # ??? kmi = km.keymap_items.new('node.parent_clear', 'P', 'PRESS', alt=True)
    # kmi = km.keymap_items.new('node.preview_toggle', 'H', 'PRESS', shift=True)
    # kmi = km.keymap_items.new('node.hide_socket_toggle', 'H', 'PRESS', ctrl=True)
    # kmi = km.keymap_items.new('node.select_linked_to', 'L', 'PRESS', shift=True)
    # kmi = km.keymap_items.new('node.select_linked_from', 'L', 'PRESS')
    # kmi = km.keymap_items.new('node.select_same_type', 'G', 'PRESS', shift=True)
    # kmi = km.keymap_items.new('node.select_same_type_step', 'RIGHT_BRACKET', 'PRESS', shift=True)
    # kmi.properties.prev = False
    # kmi = km.keymap_items.new('node.select_same_type_step', 'LEFT_BRACKET', 'PRESS', shift=True)
    # kmi.properties.prev = True
    # kmi = km.keymap_items.new('node.move_detach_links', 'D', 'PRESS', alt=True)
    # kmi = km.keymap_items.new('node.move_detach_links_release', 'EVT_TWEAK_A', 'ANY', alt=True)
    # kmi = km.keymap_items.new('node.move_detach_links', 'EVT_TWEAK_S', 'ANY', alt=True)
    # kmi = km.keymap_items.new('node.detach_translate_attach', 'C', 'PRESS', alt=True)


def MapAdd_AnimationChannels(kc):
    # Map Animation Channels
    km = kc.keymaps.new('Animation Channels', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Click-select
    # TODO: replace/add/remove select
    kmi = km.keymap_items.new('anim.channels_click', 'LEFTMOUSE', 'CLICK')
    kmi = km.keymap_items.new('anim.channels_click', 'LEFTMOUSE', 'PRESS', shift=True)
    kmi.properties.extend = True
    #kmi = km.keymap_items.new('anim.channels_click', 'LEFTMOUSE', 'PRESS', shift=True, ctrl=True)
    #kmi.properties.children_only = True
    
    # Border-select
    # TODO: replace/add/remove select
    kmi = km.keymap_items.new('anim.channels_select_border', 'EVT_TWEAK_L', 'ANY')
    
    # Select all / invert selection
    kmi = km.keymap_items.new('anim.channels_select_all_toggle', 'A', 'PRESS')
    kmi = km.keymap_items.new('anim.channels_select_all_toggle', 'I', 'PRESS', ctrl=True)
    kmi.properties.invert = True
    
    # Delete
    kmi = km.keymap_items.new('anim.channels_delete', 'X', 'PRESS')
    kmi = km.keymap_items.new('anim.channels_delete', 'DEL', 'PRESS')
    
    """
    kmi = km.keymap_items.new('anim.channels_rename', 'LEFTMOUSE', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('anim.channels_select_border', 'B', 'PRESS')
    kmi = km.keymap_items.new('anim.channels_setting_toggle', 'W', 'PRESS', shift=True)
    kmi = km.keymap_items.new('anim.channels_setting_enable', 'W', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('anim.channels_setting_disable', 'W', 'PRESS', alt=True)
    kmi = km.keymap_items.new('anim.channels_editable_toggle', 'TAB', 'PRESS')
    kmi = km.keymap_items.new('anim.channels_expand', 'NUMPAD_PLUS', 'PRESS')
    kmi = km.keymap_items.new('anim.channels_collapse', 'NUMPAD_MINUS', 'PRESS')
    kmi = km.keymap_items.new('anim.channels_expand', 'NUMPAD_PLUS', 'PRESS', ctrl=True)
    kmi.properties.all = False
    kmi = km.keymap_items.new('anim.channels_collapse', 'NUMPAD_MINUS', 'PRESS', ctrl=True)
    kmi.properties.all = False
    kmi = km.keymap_items.new('anim.channels_move', 'PAGE_UP', 'PRESS')
    kmi.properties.direction = 'UP'
    kmi = km.keymap_items.new('anim.channels_move', 'PAGE_DOWN', 'PRESS')
    kmi.properties.direction = 'DOWN'
    kmi = km.keymap_items.new('anim.channels_move', 'PAGE_UP', 'PRESS', shift=True)
    kmi.properties.direction = 'TOP'
    kmi = km.keymap_items.new('anim.channels_move', 'PAGE_DOWN', 'PRESS', shift=True)
    kmi.properties.direction = 'BOTTOM'
    kmi = km.keymap_items.new('anim.channels_group', 'G', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('anim.channels_ungroup', 'G', 'PRESS', alt=True)
    """



def MapAdd_GraphEditorGeneric(kc):
    # Map Graph Editor Generic
    km = kc.keymaps.new('Graph Editor Generic', space_type='GRAPH_EDITOR', region_type='WINDOW', modal=False)
    
    # TODO: toggle for animation channels as well
    kmi = km.keymap_items.new('graph.properties', 'QUOTE', 'PRESS')


def MapAdd_GraphEditor(kc):
    # Map Graph Editor
    # TODO: figure out selection model.  What selection tools map to what
    #       key/mouse combos?  How important is it to be analagous to
    #       mesh-edit mode?
    km = kc.keymaps.new('Graph Editor', space_type='GRAPH_EDITOR', region_type='WINDOW', modal=False)

    # Scrub
    kmi = km.keymap_items.new('graph.cursor_set', 'ACTIONMOUSE', 'PRESS')

    # Basic click-selection
    # TODO: replace/add/remove select
    kmi = km.keymap_items.new('graph.clickselect', 'SELECTMOUSE', 'CLICK')
    kmi.properties.extend = False
    kmi.properties.column = False
    kmi.properties.curves = False
    kmi = km.keymap_items.new('graph.clickselect', 'SELECTMOUSE', 'PRESS', shift=True)
    kmi.properties.extend = True
    kmi.properties.column = False
    kmi.properties.curves = False
    
    # Box select
    # TODO: replace/add/remove select
    kmi = km.keymap_items.new('graph.select_border', 'EVT_TWEAK_S', 'ANY',)
    kmi.properties.axis_range = False
    kmi.properties.include_handles = False
    kmi = km.keymap_items.new('graph.select_border', 'EVT_TWEAK_S', 'ANY', alt=True)
    kmi.properties.axis_range = False
    kmi.properties.include_handles = True
    
    # Curve select
    # TODO: replace/add/remove select
    kmi = km.keymap_items.new('graph.clickselect', 'L', 'PRESS')
    kmi.properties.extend = False
    kmi.properties.column = False
    kmi.properties.curves = True
    kmi = km.keymap_items.new('graph.clickselect', 'L', 'PRESS', shift=True)
    kmi.properties.extend = True
    kmi.properties.column = False
    kmi.properties.curves = True
    
    # Column selection
    # TODO: replace/add/remove select
    kmi = km.keymap_items.new('graph.clickselect', 'SELECTMOUSE', 'DOUBLE_CLICK')
    kmi.properties.extend = False
    kmi.properties.column = True
    kmi.properties.curves = False
    kmi = km.keymap_items.new('graph.clickselect', 'SELECTMOUSE', 'DOUBLE_CLICK', shift=True)
    kmi.properties.extend = True
    kmi.properties.column = True
    kmi.properties.curves = False
    
    # Select to the left/right of the time cursor
    kmi = km.keymap_items.new('graph.select_leftright', 'SELECTMOUSE', 'PRESS', alt=True)
    kmi.properties.mode = 'CHECK'
    kmi.properties.extend = False
    kmi = km.keymap_items.new('graph.select_leftright', 'SELECTMOUSE', 'PRESS', alt=True, shift=True)
    kmi.properties.mode = 'CHECK'
    kmi.properties.extend = True
    
    # Select all / invert selection
    kmi = km.keymap_items.new('graph.select_all_toggle', 'A', 'PRESS')
    kmi.properties.invert = False
    kmi = km.keymap_items.new('graph.select_all_toggle', 'I', 'PRESS', ctrl=True)
    kmi.properties.invert = True
    
    # Select more/less
    kmi = km.keymap_items.new('graph.select_less', 'LEFT_BRACKET', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('graph.select_more', 'RIGHT_BRACKET', 'PRESS', ctrl=True)
    
    # Transforms
    kmi = km.keymap_items.new('transform.translate', 'F', 'PRESS')
    kmi = km.keymap_items.new('transform.rotate', 'D', 'PRESS')
    kmi = km.keymap_items.new('transform.resize', 'S', 'PRESS')
    #kmi = km.keymap_items.new('transform.transform', 'E', 'PRESS')
    #kmi.properties.mode = 'TIME_EXTEND'
    
    # Tweak
    # TODO: write tweak operator
    #kmi = km.keymap_items.new('transform.translate', 'EVT_TWEAK_A', 'ANY')
    
    # Add keyframes
    kmi = km.keymap_items.new('graph.keyframe_insert', 'K', 'PRESS')
    kmi = km.keymap_items.new('graph.click_insert', 'ACTIONMOUSE', 'CLICK', ctrl=True)
    
    # Duplicate
    kmi = km.keymap_items.new('graph.duplicate_move', 'D', 'PRESS', shift=True)
    
    # Delete
    # TODO: create a no-confirm delete operator
    kmi = km.keymap_items.new('graph.delete', 'X', 'PRESS')
    kmi = km.keymap_items.new('graph.delete', 'DEL', 'PRESS')
    
    # Copy/paste
    kmi = km.keymap_items.new('graph.copy', 'C', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('graph.paste', 'V', 'PRESS', ctrl=True)
    
    # View navigation
    # TODO: what about non-numpad keyboards?
    kmi = km.keymap_items.new('graph.view_all', 'HOME', 'PRESS')
    kmi = km.keymap_items.new('graph.view_selected', 'NUMPAD_PERIOD', 'PRESS')
    
    # Interpolation / Handle type
    # TODO: decide on hot keys for these
    kmi = km.keymap_items.new('graph.handle_type', 'V', 'PRESS')
    kmi = km.keymap_items.new('graph.interpolation_type', 'T', 'PRESS')
    
    """
    kmi = km.keymap_items.new('wm.context_toggle', 'H', 'PRESS', ctrl=True)
    kmi.properties.data_path = 'space_data.show_handles'
    kmi = km.keymap_items.new('graph.select_leftright', 'LEFT_BRACKET', 'PRESS')
    kmi.properties.mode = 'LEFT'
    kmi.properties.extend = False
    kmi = km.keymap_items.new('graph.select_leftright', 'RIGHT_BRACKET', 'PRESS')
    kmi.properties.mode = 'RIGHT'
    kmi.properties.extend = False
    kmi = km.keymap_items.new('graph.select_column', 'K', 'PRESS')
    kmi.properties.mode = 'KEYS'
    kmi = km.keymap_items.new('graph.select_column', 'K', 'PRESS', ctrl=True)
    kmi.properties.mode = 'CFRA'
    kmi = km.keymap_items.new('graph.select_column', 'K', 'PRESS', shift=True)
    kmi.properties.mode = 'MARKERS_COLUMN'
    kmi = km.keymap_items.new('graph.select_column', 'K', 'PRESS', alt=True)
    kmi.properties.mode = 'MARKERS_BETWEEN'
    kmi = km.keymap_items.new('graph.select_linked', 'L', 'PRESS')
    kmi = km.keymap_items.new('graph.frame_jump', 'G', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('graph.snap', 'S', 'PRESS', shift=True)
    kmi = km.keymap_items.new('graph.mirror', 'M', 'PRESS', shift=True)

    kmi = km.keymap_items.new('graph.clean', 'O', 'PRESS')
    kmi = km.keymap_items.new('graph.smooth', 'O', 'PRESS', alt=True)
    kmi = km.keymap_items.new('graph.sample', 'O', 'PRESS', shift=True)
    kmi = km.keymap_items.new('graph.bake', 'C', 'PRESS', alt=True)
    kmi = km.keymap_items.new('graph.previewrange_set', 'P', 'PRESS', ctrl=True, alt=True)
    kmi = km.keymap_items.new('graph.fmodifier_add', 'M', 'PRESS', shift=True, ctrl=True)
    kmi.properties.only_active = False
    kmi = km.keymap_items.new('anim.channels_editable_toggle', 'TAB', 'PRESS')
    kmi = km.keymap_items.new('marker.add', 'M', 'PRESS')
    kmi = km.keymap_items.new('marker.rename', 'M', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('graph.extrapolation_type', 'E', 'PRESS', shift=True)
    """


wm = bpy.context.window_manager
kc = wm.keyconfigs.new('Blender 2012 (experimental!)')

clear_keymap(kc)

MapAdd_Window(kc)
MapAdd_Screen(kc)

MapAdd_View2D(kc)

MapAdd_View3D_Global(kc)
MapAdd_View3D_Object_Nonmodal(kc)
MapAdd_View3D_ObjectMode(kc)
MapAdd_View3D_MeshEditMode(kc)
MapAdd_KnifeToolModal(kc)
MapAdd_Sculpt(kc)
MapAdd_WeightPaint(kc)
MapAdd_View3D_Generic(kc)

MapAdd_ModalStandard(kc)
MapAdd_ModalTransform(kc)
MapAdd_ModalBorderSelect(kc)

MapAdd_AnimationGlobal(kc)
MapAdd_AnimationSpaces(kc)
MapAdd_Markers(kc)

MapAdd_ArmaturePose(kc)

MapAdd_FileBrowserGlobal(kc)
MapAdd_FileBrowserMain(kc)
MapAdd_FileBrowserButtons(kc)

MapAdd_Outliner(kc)

MapAdd_Console(kc)

MapAdd_TextEditorGeneric(kc)
MapAdd_TextEditor(kc)

MapAdd_NodeEditorGeneric(kc)
MapAdd_NodeEditor(kc)

MapAdd_AnimationChannels(kc)

MapAdd_GraphEditorGeneric(kc)
MapAdd_GraphEditor(kc)










