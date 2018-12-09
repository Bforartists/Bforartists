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

# <pep8 compliant>

import os

if "bpy" in locals():
    import importlib
    importlib.reload(settings)
    importlib.reload(utils_i18n)
else:
    import bpy
    from bpy.types import (
        Operator,
        Panel,
        PropertyGroup,
        UIList,
    )
    from bpy.props import (
        BoolProperty,
        IntProperty,
        StringProperty,
        CollectionProperty,
    )
    from . import settings
    from bl_i18n_utils import utils as utils_i18n

from bpy.app.translations import pgettext_iface as iface_


# Data ########################################################################

class I18nUpdateTranslationLanguage(PropertyGroup):
    """Settings/info about a language."""

    uid: StringProperty(
        name="Language ID",
        description="ISO code (eg. \"fr_FR\")",
        default="",
    )

    num_id: IntProperty(
        name="Numeric ID",
        description="Numeric ID (read only!)",
        default=0, min=0,
    )

    name: StringProperty(
        name="Language Name",
        description="Language label (eg. \"French (Français)\")",
        default="",
    )

    use: BoolProperty(
        name="Use",
        description="If this language should be used in the current operator",
        default=True,
    )

    po_path: StringProperty(
        name="PO File Path",
        description="Path to the relevant po file in branches",
        subtype='FILE_PATH',
        default="",
    )

    po_path_trunk: StringProperty(
        name="PO Trunk File Path",
        description="Path to the relevant po file in trunk",
        subtype='FILE_PATH',
        default="",
    )

    mo_path_trunk: StringProperty(
        name="MO File Path",
        description="Path to the relevant mo file",
        subtype='FILE_PATH',
        default="",
    )

    po_path_git: StringProperty(
        name="PO Git Master File Path",
        description="Path to the relevant po file in Blender's translations git repository",
        subtype='FILE_PATH',
        default="",
    )


class I18nUpdateTranslationSettings(PropertyGroup):
    """Settings/info about a language"""

    langs: CollectionProperty(
        name="Languages",
        type=I18nUpdateTranslationLanguage,
        description="Languages to update in branches",
    )

    active_lang: IntProperty(
        name="Active Language",
        default=0,
        description="Index of active language in langs collection",
    )

    pot_path: StringProperty(
        name="POT File Path",
        description="Path to the pot template file",
        subtype='FILE_PATH',
        default="",
    )

    is_init: BoolProperty(
        description="Whether these settings have already been auto-set or not",
        default=False,
        options={'HIDDEN'},
    )


# UI ##########################################################################

class UI_UL_i18n_languages(UIList):
    """ """

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon_value=icon)
            layout.prop(item, "use", text="")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=item.uid)
            layout.prop(item, "use", text="")


class UI_PT_i18n_update_translations_settings(Panel):
    """ """

    bl_label = "I18n Update Translation"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        i18n_sett = context.window_manager.i18n_update_svn_settings

        if not i18n_sett.is_init and bpy.ops.ui.i18n_updatetranslation_svn_init_settings.poll():
            bpy.ops.ui.i18n_updatetranslation_svn_init_settings()

        if not i18n_sett.is_init:
            layout.label(text="Could not init languages data!")
            layout.label(text="Please edit the preferences of the UI Translate add-on")
        else:
            split = layout.split(factor=0.75)
            split.template_list("UI_UL_i18n_languages", "", i18n_sett, "langs", i18n_sett, "active_lang", rows=8)
            col = split.column()
            col.operator("ui.i18n_updatetranslation_svn_init_settings", text="Reset Settings")
            deselect = any(l.use for l in i18n_sett.langs)
            op = col.operator("ui.i18n_updatetranslation_svn_settings_select",
                              text="Deselect All" if deselect else "Select All")
            op.use_invert = False
            op.use_select = not deselect
            col.operator("ui.i18n_updatetranslation_svn_settings_select", text="Invert Selection").use_invert = True
            col.separator()
            col.operator("ui.i18n_updatetranslation_svn_branches", text="Update Branches")
            col.operator("ui.i18n_updatetranslation_svn_trunk", text="Update Trunk")
            col.operator("ui.i18n_updatetranslation_svn_statistics", text="Statistics")

            if i18n_sett.active_lang >= 0 and i18n_sett.active_lang < len(i18n_sett.langs):
                lng = i18n_sett.langs[i18n_sett.active_lang]
                col = layout.column()
                col.active = lng.use
                row = col.row()
                row.label(text="[{}]: \"{}\" ({})".format(lng.uid, iface_(lng.name), lng.num_id), translate=False)
                row.prop(lng, "use", text="")
                col.prop(lng, "po_path")
                col.prop(lng, "po_path_trunk")
                col.prop(lng, "mo_path_trunk")
                col.prop(lng, "po_path_git")
            layout.separator()
            layout.prop(i18n_sett, "pot_path")

            layout.separator()
            layout.label(text="Add-ons:")
            row = layout.row()
            op = row.operator("ui.i18n_addon_translation_invoke", text="Refresh I18n Data...")
            op.op_id = "ui.i18n_addon_translation_update"
            op = row.operator("ui.i18n_addon_translation_invoke", text="Export PO...")
            op.op_id = "ui.i18n_addon_translation_export"
            op = row.operator("ui.i18n_addon_translation_invoke", text="Import PO...")
            op.op_id = "ui.i18n_addon_translation_import"


# Operators ###################################################################

class UI_OT_i18n_updatetranslation_svn_init_settings(Operator):
    """Init settings for i18n svn's update operators"""

    bl_idname = "ui.i18n_updatetranslation_svn_init_settings"
    bl_label = "Init I18n Update Settings"
    bl_option = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.window_manager is not None

    def execute(self, context):
        if not hasattr(self, "settings"):
            self.settings = settings.settings
        i18n_sett = context.window_manager.i18n_update_svn_settings

        # First, create the list of languages from settings.
        i18n_sett.langs.clear()
        root_br = self.settings.BRANCHES_DIR
        root_tr_po = self.settings.TRUNK_PO_DIR
        root_git_po = self.settings.GIT_I18N_PO_DIR
        root_tr_mo = os.path.join(self.settings.TRUNK_DIR, self.settings.MO_PATH_TEMPLATE, self.settings.MO_FILE_NAME)
        if not (os.path.isdir(root_br) and os.path.isdir(root_tr_po)):
            return {'CANCELLED'}
        isocodes = ((e, os.path.join(root_br, e, e + ".po")) for e in os.listdir(root_br))
        isocodes = dict(e for e in isocodes if os.path.isfile(e[1]))
        for num_id, name, uid in self.settings.LANGUAGES[2:]:  # Skip "default" and "en" languages!
            best_po = utils_i18n.find_best_isocode_matches(uid, isocodes)
            #print(uid, "->", best_po)
            lng = i18n_sett.langs.add()
            lng.uid = uid
            lng.num_id = num_id
            lng.name = name
            if best_po:
                lng.use = True
                isocode = best_po[0]
                lng.po_path = isocodes[isocode]
                lng.po_path_trunk = os.path.join(root_tr_po, isocode + ".po")
                lng.mo_path_trunk = root_tr_mo.format(isocode)
                lng.po_path_git = os.path.join(root_git_po, isocode + ".po")
            else:
                lng.use = False
                language, _1, _2, language_country, language_variant = utils_i18n.locale_explode(uid)
                for isocode in (language, language_variant, language_country, uid):
                    p = os.path.join(root_br, isocode, isocode + ".po")
                    if not os.path.exists(p):
                        lng.use = True
                        lng.po_path = p
                        lng.po_path_trunk = os.path.join(root_tr_po, isocode + ".po")
                        lng.mo_path_trunk = root_tr_mo.format(isocode)
                        lng.po_path_git = os.path.join(root_git_po, isocode + ".po")
                        break

        i18n_sett.pot_path = self.settings.FILE_NAME_POT
        i18n_sett.is_init = True
        return {'FINISHED'}


class UI_OT_i18n_updatetranslation_svn_settings_select(Operator):
    """(De)select (or invert selection of) all languages for i18n svn's update operators"""

    bl_idname = "ui.i18n_updatetranslation_svn_settings_select"
    bl_label = "Init I18n Update Select Languages"

    # Operator Arguments
    use_select: BoolProperty(
        name="Select All",
        description="Select all if True, else deselect all",
        default=True,
    )

    use_invert: BoolProperty(
        name="Invert Selection",
        description="Inverse selection (overrides 'Select All' when True)",
        default=False,
    )
    # /End Operator Arguments

    @classmethod
    def poll(cls, context):
        return context.window_manager is not None

    def execute(self, context):
        if self.use_invert:
            for lng in context.window_manager.i18n_update_svn_settings.langs:
                lng.use = not lng.use
        else:
            for lng in context.window_manager.i18n_update_svn_settings.langs:
                lng.use = self.use_select
        return {'FINISHED'}


classes = (
    I18nUpdateTranslationLanguage,
    I18nUpdateTranslationSettings,
    UI_UL_i18n_languages,
    UI_PT_i18n_update_translations_settings,
    UI_OT_i18n_updatetranslation_svn_init_settings,
    UI_OT_i18n_updatetranslation_svn_settings_select,
)
