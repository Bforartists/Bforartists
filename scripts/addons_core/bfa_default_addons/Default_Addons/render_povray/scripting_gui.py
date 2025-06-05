# SPDX-FileCopyrightText: 2021-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""User interface to POV Scene Description Language snippets or full includes:

import, load, create or edit """

import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import Operator, Menu, Panel
from sys import platform  # really import here, as in ui.py and in render.py?
import os  # really import here and in render.py?
from os.path import isfile


def locate_docpath():
    """POV can be installed with some include files.

    Get their path as defined in user preferences or registry keys for
    the user to be able to invoke them."""

    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    # Use the system preference if its set.
    if pov_documents := addon_prefs.docpath_povray:
        if os.path.exists(pov_documents):
            return pov_documents
        # Implicit else, as here return was still not triggered:
        print(
            "User Preferences path to povray documents %r NOT FOUND, checking $PATH" % pov_documents
        )

    # Windows Only
    if platform.startswith("win"):
        import winreg

        try:
            win_reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, "Software\\POV-Ray\\v3.7\\Windows"
            )
            win_docpath = winreg.QueryValueEx(win_reg_key, "DocPath")[0]
            pov_documents = os.path.join(win_docpath, "Insert Menu")
            if os.path.exists(pov_documents):
                return pov_documents
        except FileNotFoundError:
            return ""
    # search the path all os's
    pov_documents_default = "include"

    os_path_ls = os.getenv("PATH").split(":") + [""]

    for dir_name in os_path_ls:
        pov_documents = os.path.join(dir_name, pov_documents_default)
        if os.path.exists(pov_documents):
            return pov_documents
    return ""


# ---------------------------------------------------------------- #


class TextButtonsPanel:
    """Use this class to define buttons from the side tab of
    text window."""

    bl_space_type = "TEXT_EDITOR"
    bl_region_type = "UI"
    bl_label = "POV-Ray"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        text = context.space_data
        rd = context.scene.render
        return text and (rd.engine in cls.COMPAT_ENGINES)


# ---------------------------------------------------------------- #
# Text Povray Settings
# ---------------------------------------------------------------- #


class TEXT_OT_POV_insert(Operator):
    """Create blender text editor operator to insert pov snippets like other pov IDEs"""

    bl_idname = "text.povray_insert"
    bl_label = "Insert"

    filepath: bpy.props.StringProperty(name="Filepath", subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        text = context.space_data.text
        return context.area.type == "TEXT_EDITOR" and text is not None
        # return bpy.ops.text.insert.poll() this Bpy op has no poll()

    def execute(self, context):
        if self.filepath and isfile(self.filepath):
            with open(self.filepath, "r") as file:
                bpy.ops.text.insert(text=file.read())

                # places the cursor at the end without scrolling -.-
                # context.space_data.text.write(file.read())
            if not file.closed:
                file.close()
        return {"FINISHED"}


def validinsert(ext):
    """Since preview images could be in same folder, filter only insertable text"""
    return ext in {".txt", ".inc", ".pov"}


class TEXT_MT_POV_insert(Menu):
    """Create a menu launcher in text editor for the TEXT_OT_POV_insert operator ."""

    bl_label = "Insert"
    bl_idname = "TEXT_MT_POV_insert"

    def draw(self, context):
        pov_documents = locate_docpath()
        prop = self.layout.operator("wm.path_open", text="Open folder", icon="FILE_FOLDER")
        prop.filepath = pov_documents
        self.layout.separator()

        # todo: structure submenus by dir
        pov_insert_items_list = [root for root, dirs, files in os.walk(pov_documents)]
        print(pov_insert_items_list)
        self.path_menu(
            pov_insert_items_list,
            "text.povray_insert",
            # {"internal": True},
            filter_ext=validinsert,
        )


class TEXT_PT_POV_custom_code(TextButtonsPanel, Panel):
    """Use this class to create a panel in text editor for the user to decide if he renders text

    only or adds to 3d scene."""

    bl_label = "POV"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw(self, context):
        layout = self.layout

        text = context.space_data.text

        if pov_documents := locate_docpath():
            # print(pov_documents)
            layout.menu(TEXT_MT_POV_insert.bl_idname)

        else:
            layout.label(text="Please configure ", icon="INFO")
            layout.label(text="default pov include path ")
            layout.label(text="in addon preferences")
            # layout.separator()
            layout.operator(
                "preferences.addon_show",
                text="Go to Render: Persistence of Vision addon",
                icon="PREFERENCES",
            ).module = "render_povray"

        if text:
            box = layout.box()
            box.label(text="Source to render:", icon="RENDER_STILL")
            row = box.row()
            row.prop(text.pov, "custom_code", expand=True)
            if text.pov.custom_code in {"3dview"}:
                box.operator("render.render", icon="OUTLINER_DATA_ARMATURE")
            if text.pov.custom_code in {"text"}:
                rtext = bpy.context.space_data.text  # is r a typo ? or why written, not used
                box.operator("text.run", icon="ARMATURE_DATA")
            # layout.prop(text.pov, "custom_code")
            elif text.pov.custom_code in {"both"}:
                box.operator("render.render", icon="POSE_HLT")
                layout.label(text="Please specify declared", icon="INFO")
                layout.label(text="items in properties ")
                # layout.label(text="")
                layout.label(text="replacement fields")


# ---------------------------------------------------------------- #
# Text editor templates from header menu


class TEXT_MT_POV_templates(Menu):
    """Use this class to create a menu for the same pov templates scenes as other pov IDEs."""

    bl_label = "POV"

    # We list templates on file evaluation, we can assume they are static data,
    # and better avoid running this on every draw call.
    template_paths = [os.path.join(os.path.dirname(__file__), "templates_pov")]

    def draw(self, context):
        self.path_menu(self.template_paths, "text.open", props_default={"internal": True})


def menu_func_templates(self, context):
    """Add POV files to the text editor templates menu"""
    # Do not depend on POV being active renderer here...
    self.layout.menu("TEXT_MT_POV_templates")


# ---------------------------------------------------------------- #
# POV Import menu


class VIEW_MT_POV_import(Menu):
    """Use this class for the import menu."""

    bl_idname = "POVRAY_MT_import_tools"
    bl_label = "Import"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_REGION_WIN"
        layout.operator("import_scene.pov", icon="FORCE_LENNARDJONES")


def menu_func_import(self, context):
    """Add the import operator to menu"""
    engine = context.scene.render.engine
    if engine == "POVRAY_RENDER":
        self.layout.operator("import_scene.pov", icon="FORCE_LENNARDJONES")


classes = (
    VIEW_MT_POV_import,
    TEXT_OT_POV_insert,
    TEXT_MT_POV_insert,
    TEXT_PT_POV_custom_code,
    TEXT_MT_POV_templates,
)


def register():
    for cls in classes:
        register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TEXT_MT_templates.append(menu_func_templates)


def unregister():
    bpy.types.TEXT_MT_templates.remove(menu_func_templates)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    for cls in reversed(classes):
        unregister_class(cls)
