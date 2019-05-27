# gpl: author Yadoob
# -*- coding: utf-8 -*-

import bpy
from bpy.types import (
    Operator,
    Panel,
)
from bpy.props import (
    BoolProperty,
    StringProperty,
)
from .warning_messages_utils import (
    warning_messages,
    c_data_has_images,
)


class TEXTURE_OT_patern_rename(Operator):
    bl_idname = "texture.patern_rename"
    bl_label = "Texture Renamer"
    bl_description = ("Replace the Texture names pattern with the attached Image ones\n"
                      "Works on all Textures (Including Brushes)\n"
                      "The First field - the name pattern to replace\n"
                      "The Second - search for existing names")
    bl_options = {'REGISTER', 'UNDO'}

    def_name = "Texture"    # default name
    is_not_undo = False     # prevent drawing props on undo

    named: StringProperty(
        name="Search for name",
        description="Enter the name pattern or choose the one from the dropdown list below",
        default=def_name
    )
    replace_all: BoolProperty(
        name="Replace all",
        description="Replace all the Textures in the data with the names of the images attached",
        default=False
    )

    @classmethod
    def poll(cls, context):
        return c_data_has_images()

    def draw(self, context):
        layout = self.layout
        if not self.is_not_undo:
            layout.label(text="*Only Undo is available*", icon="INFO")
            return

        layout.prop(self, "replace_all")

        box = layout.box()
        box.enabled = not self.replace_all
        box.prop(self, "named", text="Name pattern", icon="SYNTAX_ON")

        box = layout.box()
        box.enabled = not self.replace_all
        box.prop_search(self, "named", bpy.data, "textures")

    def invoke(self, context, event):
        self.is_not_undo = True
        return context.window_manager.invoke_props_dialog(self)

    def check(self, context):
        return self.is_not_undo

    def execute(self, context):
        errors = []     # collect texture names without images attached
        tex_count = len(bpy.data.textures)

        for texture in bpy.data.textures:
            try:
                is_allowed = self.named in texture.name if not self.replace_all else True
                if texture and is_allowed and texture.type in {"IMAGE"}:
                    textname = ""
                    img = (bpy.data.textures[texture.name].image if bpy.data.textures[texture.name] else None)
                    if not img:
                        errors.append(str(texture.name))
                    for word in img.name:
                        if word != ".":
                            textname = textname + word
                        else:
                            break
                    texture.name = textname
                if texture.type != "IMAGE":  # rename specific textures as clouds, environment map...
                    texture.name = texture.type.lower()
            except:
                continue

        if tex_count == 0:
            warning_messages(self, 'NO_TEX_RENAME')
        elif errors:
            warning_messages(self, 'TEX_RENAME_F', errors, 'TEX')

        # reset name to default
        self.named = self.def_name

        self.is_not_undo = False

        return {'FINISHED'}


class TEXTURE_PT_rename_panel(Panel):
    bl_label = "Texture Rename"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "texture"

    def draw(self, context):
        layout = self.layout
        layout.operator("texture.patern_rename")


def register():
    bpy.utils.register_class(TEXTURE_OT_patern_rename)
    bpy.utils.register_class(TEXTURE_PT_rename_panel)


def unregister():
    bpy.utils.unregister_class(TEXTURE_PT_rename_panel)
    bpy.utils.unregister_class(TEXTURE_OT_patern_rename)


if __name__ == "__main__":
    register()
