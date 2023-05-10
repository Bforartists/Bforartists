# SPDX-License-Identifier: GPL-2.0-or-later

if "bpy" in locals():
    import importlib
    importlib.reload(settings)
    importlib.reload(utils_i18n)
    importlib.reload(utils_languages_menu)
else:
    import bpy
    from bpy.types import Operator
    from bpy.props import (
        BoolProperty,
        EnumProperty,
    )
    from . import settings
    from bl_i18n_utils import utils as utils_i18n
    from bl_i18n_utils import utils_languages_menu

import concurrent.futures
import io
import os
import shutil
import subprocess
import tempfile


# Operators ###################################################################

def i18n_updatetranslation_svn_branches_callback(pot, lng, settings):
    if not lng['use']:
        return
    if os.path.isfile(lng['po_path']):
        po = utils_i18n.I18nMessages(uid=lng['uid'], kind='PO', src=lng['po_path'], settings=settings)
        po.update(pot)
    else:
        po = pot
    po.write(kind="PO", dest=lng['po_path'])
    print("{} PO written!".format(lng['uid']))


class UI_OT_i18n_updatetranslation_svn_branches(Operator):
    """Update i18n svn's branches (po files)"""
    bl_idname = "ui.i18n_updatetranslation_svn_branches"
    bl_label = "Update I18n Branches"

    use_skip_pot_gen: BoolProperty(
        name="Skip POT",
        description="Skip POT file generation",
        default=False,
    )

    def execute(self, context):
        if not hasattr(self, "settings"):
            self.settings = settings.settings
        i18n_sett = context.window_manager.i18n_update_svn_settings
        self.settings.FILE_NAME_POT = i18n_sett.pot_path

        context.window_manager.progress_begin(0, len(i18n_sett.langs) + 1)
        context.window_manager.progress_update(0)
        if not self.use_skip_pot_gen:
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "exitcode=0:" + os.environ.get("ASAN_OPTIONS", "")
            # Generate base pot from RNA messages (we use another blender instance here, to be able to perfectly
            # control our environment (factory startup, specific addons enabled/disabled...)).
            # However, we need to export current user settings about this addon!
            cmmd = (
                bpy.app.binary_path,
                "--background",
                "--factory-startup",
                "--python",
                os.path.join(os.path.dirname(utils_i18n.__file__), "bl_extract_messages.py"),
                "--",
                "--settings",
                self.settings.to_json(),
            )
            # Not working (UI is not refreshed...).
            #self.report({'INFO'}, "Extracting messages, this will take some time...")
            context.window_manager.progress_update(1)
            ret = subprocess.run(cmmd, env=env)
            if ret.returncode != 0:
                self.report({'ERROR'}, "Message extraction process failed!")
                context.window_manager.progress_end()
                return {'CANCELLED'}

        # Now we should have a valid POT file, we have to merge it in all languages po's...
        with concurrent.futures.ProcessPoolExecutor() as exctr:
            pot = utils_i18n.I18nMessages(kind='PO', src=self.settings.FILE_NAME_POT, settings=self.settings)
            num_langs = len(i18n_sett.langs)
            for progress, _ in enumerate(exctr.map(i18n_updatetranslation_svn_branches_callback,
                                                   (pot,) * num_langs,
                                                   [dict(lng.items()) for lng in i18n_sett.langs],
                                                   (self.settings,) * num_langs,
                                                   chunksize=4)):
                context.window_manager.progress_update(progress + 2)
        context.window_manager.progress_end()
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def i18n_cleanuptranslation_svn_branches_callback(lng, settings):
    if not lng['use']:
        print("Skipping {} language ({}).".format(lng['name'], lng['uid']))
        return
    po = utils_i18n.I18nMessages(uid=lng['uid'], kind='PO', src=lng['po_path'], settings=settings)
    errs = po.check(fix=True)
    cleanedup_commented = po.clean_commented()
    po.write(kind="PO", dest=lng['po_path'])
    print("Processing {} language ({}).\n"
          "Cleaned up {} commented messages.\n".format(lng['name'], lng['uid'], cleanedup_commented) +
          ("Errors in this po, solved as best as possible!\n\t" + "\n\t".join(errs) if errs else "") + "\n")


class UI_OT_i18n_cleanuptranslation_svn_branches(Operator):
    """Clean up i18n svn's branches (po files)"""
    bl_idname = "ui.i18n_cleanuptranslation_svn_branches"
    bl_label = "Clean up I18n Branches"

    def execute(self, context):
        if not hasattr(self, "settings"):
            self.settings = settings.settings
        i18n_sett = context.window_manager.i18n_update_svn_settings
        # 'DEFAULT' and en_US are always valid, fully-translated "languages"!
        stats = {"DEFAULT": 1.0, "en_US": 1.0}

        context.window_manager.progress_begin(0, len(i18n_sett.langs) + 1)
        context.window_manager.progress_update(0)
        with concurrent.futures.ProcessPoolExecutor() as exctr:
            num_langs = len(i18n_sett.langs)
            for progress, _ in enumerate(exctr.map(i18n_cleanuptranslation_svn_branches_callback,
                                                   [dict(lng.items()) for lng in i18n_sett.langs],
                                                   (self.settings,) * num_langs,
                                                   chunksize=4)):
                context.window_manager.progress_update(progress + 1)

        context.window_manager.progress_end()

        return {'FINISHED'}


def i18n_updatetranslation_svn_trunk_callback(lng, settings):
    reports = []
    if lng['uid'] in settings.IMPORT_LANGUAGES_SKIP:
        reports.append("Skipping {} language ({}), edit settings if you want to enable it.".format(lng['name'], lng['uid']))
        return lng['uid'], 0.0, reports
    if not lng['use']:
        reports.append("Skipping {} language ({}).".format(lng['name'], lng['uid']))
        return lng['uid'], 0.0, reports
    po = utils_i18n.I18nMessages(uid=lng['uid'], kind='PO', src=lng['po_path'], settings=settings)
    errs = po.check(fix=True)
    reports.append("Processing {} language ({}).\n"
                   "Cleaned up {} commented messages.\n".format(lng['name'], lng['uid'], po.clean_commented()) +
                   ("Errors in this po, solved as best as possible!\n\t" + "\n\t".join(errs) if errs else ""))
    if lng['uid'] in settings.IMPORT_LANGUAGES_RTL:
        po.write(kind="PO", dest=lng['po_path_trunk'][:-3] + "_raw.po")
        po.rtl_process()
    po.write(kind="PO", dest=lng['po_path_trunk'])
    po.write(kind="PO_COMPACT", dest=lng['po_path_git'])
    ret = po.write(kind="MO", dest=lng['mo_path_trunk'])
    if (ret.stdout):
        reports.append(ret.stdout.decode().rstrip("\n"))
    if (ret.stderr):
        stderr_str = ret.stderr.decode().rstrip("\n")
        if ret.returncode != 0:
            reports.append("ERROR: " + stderr_str)
        else:
            reports.append(stderr_str)
    po.update_info()
    return lng['uid'], po.nbr_trans_msgs / po.nbr_msgs, reports


class UI_OT_i18n_updatetranslation_svn_trunk(Operator):
    """Update i18n svn's branches (po files)"""
    bl_idname = "ui.i18n_updatetranslation_svn_trunk"
    bl_label = "Update I18n Trunk"

    def execute(self, context):
        if not hasattr(self, "settings"):
            self.settings = settings.settings
        i18n_sett = context.window_manager.i18n_update_svn_settings
        # 'DEFAULT' and en_US are always valid, fully-translated "languages"!
        stats = {"DEFAULT": 1.0, "en_US": 1.0}

        context.window_manager.progress_begin(0, len(i18n_sett.langs) + 1)
        context.window_manager.progress_update(0)
        with concurrent.futures.ProcessPoolExecutor() as exctr:
            num_langs = len(i18n_sett.langs)
            for progress, (lng_uid, stats_val, reports) in enumerate(exctr.map(i18n_updatetranslation_svn_trunk_callback,
                                                                      [dict(lng.items()) for lng in i18n_sett.langs],
                                                                      (self.settings,) * num_langs,
                                                                      chunksize=4)):
                context.window_manager.progress_update(progress + 1)
                stats[lng_uid] = stats_val
                print("".join(reports) + "\n")

        # Copy pot file from branches to trunk.
        shutil.copy2(self.settings.FILE_NAME_POT, self.settings.TRUNK_PO_DIR)

        print("Generating languages' menu...")
        context.window_manager.progress_update(progress + 2)
        # First complete our statistics by checking po files we did not touch this time!
        po_to_uid = {os.path.basename(lng.po_path): lng.uid for lng in i18n_sett.langs}
        for po_path in os.listdir(self.settings.TRUNK_PO_DIR):
            uid = po_to_uid.get(po_path, None)
            po_path = os.path.join(self.settings.TRUNK_PO_DIR, po_path)
            if uid and uid not in stats:
                po = utils_i18n.I18nMessages(uid=uid, kind='PO', src=po_path, settings=self.settings)
                stats[uid] = po.nbr_trans_msgs / po.nbr_msgs if po.nbr_msgs > 0 else 0
        utils_languages_menu.gen_menu_file(stats, self.settings)
        context.window_manager.progress_end()

        return {'FINISHED'}


class UI_OT_i18n_updatetranslation_svn_statistics(Operator):
    """Create or extend a 'i18n_info.txt' Text datablock"""
    """(it will contain statistics and checks about current branches and/or trunk)"""
    bl_idname = "ui.i18n_updatetranslation_svn_statistics"
    bl_label = "Update I18n Statistics"

    use_branches: BoolProperty(
        name="Check Branches",
        description="Check po files in branches",
        default=True,
    )

    use_trunk: BoolProperty(
        name="Check Trunk",
        description="Check po files in trunk",
        default=False,
    )

    report_name = "i18n_info.txt"

    def execute(self, context):
        if not hasattr(self, "settings"):
            self.settings = settings.settings
        i18n_sett = context.window_manager.i18n_update_svn_settings

        buff = io.StringIO()
        lst = []
        if self.use_branches:
            lst += [(lng, lng.po_path) for lng in i18n_sett.langs]
        if self.use_trunk:
            lst += [(lng, lng.po_path_trunk) for lng in i18n_sett.langs
                                             if lng.uid not in self.settings.IMPORT_LANGUAGES_SKIP]

        context.window_manager.progress_begin(0, len(lst))
        context.window_manager.progress_update(0)
        for progress, (lng, path) in enumerate(lst):
            context.window_manager.progress_update(progress + 1)
            if not lng.use:
                print("Skipping {} language ({}).".format(lng.name, lng.uid))
                continue
            buff.write("Processing {} language ({}, {}).\n".format(lng.name, lng.uid, path))
            po = utils_i18n.I18nMessages(uid=lng.uid, kind='PO', src=path, settings=self.settings)
            po.print_info(prefix="    ", output=buff.write)
            errs = po.check(fix=False)
            if errs:
                buff.write("    WARNING! Po contains following errors:\n")
                buff.write("        " + "\n        ".join(errs))
                buff.write("\n")
            buff.write("\n\n")

        text = None
        if self.report_name not in bpy.data.texts:
            text = bpy.data.texts.new(self.report_name)
        else:
            text = bpy.data.texts[self.report_name]
        data = text.as_string()
        data = data + "\n" + buff.getvalue()
        text.from_string(data)
        self.report({'INFO'}, "Info written to {} text datablock!".format(self.report_name))
        context.window_manager.progress_end()

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


classes = (
    UI_OT_i18n_updatetranslation_svn_branches,
    UI_OT_i18n_cleanuptranslation_svn_branches,
    UI_OT_i18n_updatetranslation_svn_trunk,
    UI_OT_i18n_updatetranslation_svn_statistics,
)
