import bpy

from bpy.types import Panel

from . import common
from . import ops

from bpy.app.translations import contexts as i18n_contexts

context = bpy.context

class BFA_PT_toolshelf_animation(bpy.types.Panel):
    bl_label = "Animation"
    bl_region_type = "TOOLS"
    bl_space_type = "VIEW_3D"
    bl_category = "Animation"
    bl_options = {"HIDE_BG"}

    # Check if properties are enabled and that this draws in the correct mode exclusively.
    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        view = context.space_data
        if context.object is not None and context.object.mode in {'OBJECT', 'POSE'}:
            return view.show_toolshelf_tabs == True and wm.BFA_UI_addon_props.BFA_PROP_toggle_animationpanel
        else:
            return False

    def draw(self, context):
        layout = self.layout

        num_cols = common.column_count(context.region)

        #text buttons
        if num_cols == 4:
            col = layout.column(align=True)
            col.scale_y = 2

            wm = context.window_manager
            # Animation Operators
            if wm.BFA_UI_addon_props.BFA_PROP_toggle_animationpanel:
                col.operator("anim.keyframe_insert", text="Insert Frame", icon='KEYFRAMES_INSERT')
                col.operator("anim.keyframe_insert_menu", text="Insert Frame with Keying Set", icon='KEYFRAMES_INSERT').always_prompt = True
                col.operator("anim.keyframe_delete_v3d", text="Delete frames", icon='KEYFRAMES_REMOVE')
                col.operator("anim.keyframe_clear_v3d", text="Clear frames", icon='KEYFRAMES_CLEAR')
                col.operator("anim.keying_set_active_set", text="Change Keying Set", icon='KEYINGSET')

                col.separator()

                col.operator("nla.bake", text="Bake Action", icon='BAKE_ACTION')
                col.operator("grease_pencil.bake_grease_pencil_animation", text="Bake Object Transform to Grease Pencil", icon="BAKE_ACTION")


            #col = layout.column(align=True)
            #col.operator("operator.name", text="label", icon="DELETE")
            #col.operator("operator.name", text="label", icon="DELETE")

            #if context.mode in {'OBJECT'} # Alternative method
            #   col = layout.column(align=True)
            #   col.operator("operator.name", text="label", icon="DELETE")
            #   col.operator("operator.name", text="label", icon="DELETE")

        # icon buttons
        else:
            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if num_cols == 3:

                wm = context.window_manager
                if wm.BFA_UI_addon_props.BFA_PROP_toggle_animationpanel:
                    row = col.row(align=True)
                    row.operator("anim.keyframe_insert", text="", icon='KEYFRAMES_INSERT')
                    row.operator("anim.keyframe_insert_menu", text="", icon='KEYFRAMES_INSERT').always_prompt = True
                    row.operator("anim.keyframe_delete_v3d", text="", icon='KEYFRAMES_REMOVE')

                    row = col.row(align=True)
                    row.operator("anim.keyframe_clear_v3d", text="", icon='KEYFRAMES_CLEAR')
                    row.operator("anim.keying_set_active_set", text="", icon='KEYINGSET')
                    row.operator("nla.bake", text="", icon='BAKE_ACTION')
                    row.operator("grease_pencil.bake_grease_pencil_animation", text="", icon="BAKE_ACTION")



                #col.separator( factor = 0.5) # Button Separator

                #row = col.row(align=True)
                #row.operator("operator.name", text="", icon="DELETE")
                #row.operator("operator.name", text="", icon="DELETE")

                #if context.mode in {'OBJECT'}
                #   row = col.row(align=True)
                #   row.operator("operator.name", text="", icon="DELETE")
                #   row.operator("operator.name", text="", icon="DELETE")

            elif num_cols == 2:
                wm = context.window_manager
                if wm.BFA_UI_addon_props.BFA_PROP_toggle_animationpanel:
                    row = col.row(align=True)
                    row.operator("anim.keyframe_insert", text="", icon='KEYFRAMES_INSERT')
                    row.operator("anim.keyframe_insert_menu", text="", icon='KEYFRAMES_INSERT').always_prompt = True

                    row = col.row(align=True)
                    row.operator("anim.keyframe_delete_v3d", text="", icon='KEYFRAMES_REMOVE')
                    row.operator("anim.keyframe_clear_v3d", text="", icon='KEYFRAMES_CLEAR')

                    row = col.row(align=True)
                    row.operator("anim.keying_set_active_set", text="", icon='KEYINGSET')
                    row.operator("nla.bake", text="", icon='BAKE_ACTION')



                #col.separator( factor = 0.5) # Button Separator

                #row = col.row(align=True)
                #row.operator("operator.name", text="", icon="DELETE")
                #row.operator("operator.name", text="", icon="DELETE")

                #if context.mode in {'OBJECT'}
                #   row = col.row(align=True)
                #   row.operator("operator.name", text="", icon="DELETE")
                #   row.operator("operator.name", text="", icon="DELETE")

            elif num_cols == 1:
                wm = context.window_manager
                if wm.BFA_UI_addon_props.BFA_PROP_toggle_animationpanel:
                    col.operator("anim.keyframe_insert", text="", icon='KEYFRAMES_INSERT')
                    col.operator("anim.keyframe_insert_menu", text="", icon='KEYFRAMES_INSERT').always_prompt = True
                    col.operator("anim.keyframe_delete_v3d", text="", icon='KEYFRAMES_REMOVE')
                    col.operator("anim.keyframe_clear_v3d", text="", icon='KEYFRAMES_CLEAR')
                    col.operator("anim.keying_set_active_set", text="", icon='KEYINGSET')

                    col.separator()

                    col.operator("nla.bake", text="", icon='BAKE_ACTION')


                #col.separator( factor = 0.5)
                #col.operator("operator.name", text="", icon="DELETE")
                #col.operator("operator.name", text="", icon="DELETE")

                #if context.mode in {'OBJECT'}
                #   col = col.row(align=True)
                #   col.operator("operator.name", text="", icon="DELETE")
                #   col.operator("operator.name", text="", icon="DELETE")

class BFA_PT_toolshelf_frames(bpy.types.Panel):
    bl_label = "Frames"
    bl_region_type = "TOOLS"
    bl_space_type = "VIEW_3D"
    bl_category = "Animation"
    bl_options = {"HIDE_BG"}

    # Check if properties are enabled and that this draws in the correct mode exclusively.
    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        view = context.space_data
        if context.object is not None and context.object.mode in {'OBJECT', 'POSE', 'PAINT_GREASE_PENCIL', 'EDIT_GREASE_PENCIL', 'SCULPT_GREASE_PENCIL', 'VERTEX_GREASE_PENCIL'}:
            return view.show_toolshelf_tabs == True and wm.BFA_UI_addon_props.BFA_PROP_toggle_insertframes
        else:
            return False

        #return ((wm.BFA_UI_addon_props.BFA_PROP_toggle_insertframes) and context.object.mode in {'OBJECT', 'POSE', 'PAINT_GREASE_PENCIL', 'EDIT_GREASE_PENCIL', 'SCULPT_GPENCIL_LEGACY', 'VERTEX_GPENCIL'})

    def draw(self, context):
        layout = self.layout

        num_cols = common.column_count(context.region)

        #text buttons
        if num_cols == 4:
            col = layout.column(align=True)
            col.scale_y = 2

            wm = context.window_manager

            # Insert Frame Operators
            if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertframes:
                col.separator()

                col.operator("anim.insertframe_right", text="Insert Frame Left", icon="TRIA_LEFT")
                col.operator("anim.removeframe_left", text="Remove Frame Left", icon="PANEL_CLOSE")

                col.separator()

                col.operator("anim.insertframe_left", text="Insert Frame Right", icon="TRIA_RIGHT")
                col.operator("anim.removeframe_right", text="Remove Frame Right", icon="PANEL_CLOSE")

        # icon buttons
        else:
            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if num_cols == 3:
                wm = context.window_manager

                if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertframes:
                    row = col.row(align=True)
                    row.operator("anim.insertframe_left", text="", icon="TRIA_LEFT")
                    row.operator("anim.removeframe_left", text="", icon="PANEL_CLOSE")

                    col.separator( factor = 0.5) # Button Separator

                    row = col.row(align=True)
                    row.operator("anim.insertframe_right", text="", icon="TRIA_RIGHT")
                    row.operator("anim.removeframe_right", text="", icon="PANEL_CLOSE")

            elif num_cols == 2:
                wm = context.window_manager

                if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertframes:
                    row = col.row(align=True)
                    row.operator("anim.insertframe_left", text="", icon="TRIA_LEFT")
                    row.operator("anim.removeframe_left", text="", icon="PANEL_CLOSE")

                    col.separator( factor = 0.5) # Button Separator

                    row = col.row(align=True)
                    row.operator("anim.insertframe_right", text="", icon="TRIA_RIGHT")
                    row.operator("anim.removeframe_right", text="", icon="PANEL_CLOSE")

            elif num_cols == 1:
                wm = context.window_manager

                if wm.BFA_UI_addon_props.BFA_PROP_toggle_insertframes:
                    col.separator()
                    col.operator("anim.insertframe_left", text="", icon="TRIA_LEFT")
                    col.operator("anim.removeframe_left", text="", icon="PANEL_CLOSE")
                    col.separator()
                    col.operator("anim.insertframe_right", text="", icon="TRIA_RIGHT")
                    col.operator("anim.removeframe_right", text="", icon="PANEL_CLOSE")



panel_classes = [
    BFA_PT_toolshelf_animation,
    BFA_PT_toolshelf_frames,
]

def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in panel_classes:
        bpy.utils.unregister_class(cls)

    wm = context.window_manager
    if not wm.BFA_UI_addon_props.BFA_PROP_toggle_insertframes and not wm.BFA_UI_addon_props.BFA_PROP_toggle_animationpanel:
        bpy.utils.unregister_class(BFA_PT_toolshelf_animation)
        bpy.utils.unregister_class(BFA_PT_toolshelf_frames)

