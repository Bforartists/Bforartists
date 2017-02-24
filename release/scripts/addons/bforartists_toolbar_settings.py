
bl_info = {
    "name": "Toolbar Settings Bforartists",
    "author": "Your Name Here",
    "version": (1, 0),
    "blender": (2, 76, 0),
    "location": "User Preferences > Addons",
    "description": "Toolbar Settings. DO NOT TURN OFF! This addon contains the settings for the toolbar editor",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "User Interface",
    }


import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import BoolProperty


class bforartists_toolbar_settings(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    # file

    file_load_save = BoolProperty(name="Load / Save", default=True,)
    file_link_append = BoolProperty(name="Link / Append", default=False,)
    file_import_common = BoolProperty(name="Import Common", default=True,)
    file_import_uncommon = BoolProperty(name="Import Uncommon", default=False,)
    file_export_common = BoolProperty(name="Export Common", default=True,)
    file_export_uncommon = BoolProperty(name="Export Uncommon", default=False,)
    file_render = BoolProperty(name="Render", default=True,)
    file_render_opengl = BoolProperty(name="Render Open GL", default=False,)
    file_render_misc = BoolProperty(name="Render Misc", default=False,)

    # view

    view_align = BoolProperty(name="Align", default=False,)
    view_camera = BoolProperty(name="Camera", default=False,)

    # primitives

    primitives_mesh = BoolProperty(name="Mesh", default=True,)
    primitives_curve = BoolProperty(name="Curve", default=False,)
    primitives_surface = BoolProperty(name="Surface", default=False,)
    primitives_metaball = BoolProperty(name="Metaball", default=False,)
    primitives_lamp = BoolProperty(name="Lamp", default=False,)
    primitives_other = BoolProperty(name="Other", default=True,)
    primitives_empties = BoolProperty(name="Empties", default=False,)
    primitives_forcefield = BoolProperty(name="Force Field", default=False,)

    # Image

    image_uv_common = BoolProperty(name="UV Common", default=True,)
    image_uv_misc = BoolProperty(name="UV Misc", default=True,)
    image_uv_align = BoolProperty(name="UV Align", default=True,)

    # Tools

    tools_relations = BoolProperty(name="Relations", default=True,)
    tools_edit = BoolProperty(name="Edit", default=False,)

    # Animation

    animation_keyframes = BoolProperty(name="Keyframes", default=True,)
    animation_range = BoolProperty(name="Range", default=False,)
    animation_play = BoolProperty(name="Play", default=False,)
    animation_sync = BoolProperty(name="Sync", default=False,)
    animation_keyframetype = BoolProperty(name="Keyframetype", default=False,)
    animation_keyingset = BoolProperty(name="Keyingset", default=False,)
    
    # edit

    edit_edit = BoolProperty(name="Edit", default=True,)
    edit_weightinedit = BoolProperty(name="Weight in Edit", default=True,)
    edit_objectapply = BoolProperty(name="Object Apply", default=True,)
    edit_objectclear = BoolProperty(name="Object Clear", default=True,)

    # misc

    misc_history = BoolProperty(name="History", default=True,)
    misc_misc = BoolProperty(name="Misc", default=False,)


    def draw(self, context):
        layout = self.layout
        layout.label(text="Here you can turn on or off the single toolbars in the toolbar editor. Don't forget to save User Settings.")
        layout.label(text="The corresponding toolbar container has to be enabled in the toolbar.")

        layout.separator()

        layout.label(text="The File toolbar container")

        row = layout.row()

        row.prop(self, "file_load_save")
        row.prop(self, "file_link_append")
        row.prop(self, "file_import_common")
        row.prop(self, "file_import_uncommon")

        row = layout.row()

        row.prop(self, "file_export_common")
        row.prop(self, "file_export_uncommon")
        row.prop(self, "file_render")
        row.prop(self, "file_render_opengl")

        row = layout.row()

        row.prop(self, "file_render_misc")

        layout.label(text="The View toolbar container")

        row = layout.row()

        row.prop(self, "view_align")
        row.prop(self, "view_camera")

        layout.label(text="The Primitives toolbar container")

        row = layout.row()

        row.prop(self, "primitives_mesh")
        row.prop(self, "primitives_curve")
        row.prop(self, "primitives_surface")
        row.prop(self, "primitives_metaball")

        row = layout.row()

        row.prop(self, "primitives_lamp")
        row.prop(self, "primitives_other")
        row.prop(self, "primitives_empties")
        row.prop(self, "primitives_forcefield")

        layout.label(text="The Image toolbar container")

        row = layout.row()

        row.prop(self, "image_uv_common")
        row.prop(self, "image_uv_misc")      
        row.prop(self, "image_uv_align")

        layout.label(text="The Tools toolbar container")

        row = layout.row()

        row.prop(self, "tools_relations")
        row.prop(self, "tools_edit")     

        layout.label(text="The Animation toolbar container")

        row = layout.row()

        row.prop(self, "animation_keyframes")
        row.prop(self, "animation_range")
        row.prop(self, "animation_play")
        row.prop(self, "animation_sync")

        row = layout.row()
        
        row.prop(self, "animation_keyframetype")
        row.prop(self, "animation_keyingset")

        layout.label(text="The Edit toolbar container")

        row = layout.row()

        row.prop(self, "edit_edit")
        row.prop(self, "edit_weightinedit")
        row.prop(self, "edit_objectapply")
        row.prop(self, "edit_objectclear")

        layout.label(text="The Misc toolbar container")

        row = layout.row()

        row.prop(self, "misc_history")
        row.prop(self, "misc_misc")
        


class OBJECT_OT_BFA_Toolbar_prefs(Operator):
    """Display example preferences"""
    bl_idname = "object.addon_prefs_example"
    bl_label = "Addon Preferences Example"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__name__].preferences

        info = ("Boolean %r" %( addon_prefs.boolean))

        self.report({'INFO'}, info)
        print(info)

        return {'FINISHED'}


# Registration
def register():
    bpy.utils.register_class(OBJECT_OT_BFA_Toolbar_prefs)
    bpy.utils.register_class(bforartists_toolbar_settings)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_BFA_Toolbar_prefs)
    bpy.utils.unregister_class(bforartists_toolbar_settings)