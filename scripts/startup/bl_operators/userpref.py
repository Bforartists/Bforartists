# SPDX-FileCopyrightText: 2019-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import (
    Operator,
    OperatorFileListElement,
)
from bpy.props import (
    BoolProperty,
    EnumProperty,
    IntProperty,
    StringProperty,
    CollectionProperty,
)
from bpy.app.translations import (
    pgettext_iface as iface_,
    pgettext_tip as rpt_,
)


def _zipfile_root_namelist(file_to_extract):
    # Return a list of root paths from zipfile.ZipFile.namelist.
    import os
    root_paths = []
    for f in file_to_extract.namelist():
        # Python's `zipfile` API always adds a separate at the end of directories.
        # use `os.path.normpath` instead of `f.removesuffix(os.sep)`
        # since paths could be stored as `./paths/./`.
        #
        # Note that `..` prefixed paths can exist in ZIP files but they don't write to parent directory when extracting.
        # Nor do they pass the `os.sep not in f` test, this is important,
        # otherwise `shutil.rmtree` below could made to remove directories outside the installation directory.
        f = os.path.normpath(f)
        if os.sep not in f:
            root_paths.append(f)
    return root_paths


def _module_filesystem_remove(path_base, filenames):
    # Remove all Python modules defined by `filenames` in `base_path`.
    # The `filenames` argument is expected to be a result from `_zipfile_root_namelist`
    # but could be any iterable of file-names.
    import os
    import shutil
    module_names = {
        filename_only for filename in filenames
        # Excludes non module names including hidden (dot-files).
        if (filename_only := os.path.splitext(filename)[0]).isidentifier()
    }

    paths_stale = []
    for f in os.listdir(path_base):
        f_base = os.path.splitext(f)[0]
        if f_base in module_names:
            f_full = os.path.join(path_base, f)
            if os.path.isdir(f_full) and (not os.path.islink(f_full)):
                shutil.rmtree(f_full, ignore_errors=True)
            else:
                try:
                    os.remove(f_full)
                except Exception:
                    pass

            if os.path.exists(f_full):
                paths_stale.append(f_full)

    if paths_stale:
        import addon_utils
        addon_utils.stale_pending_stage_paths(path_base, paths_stale)


def _wm_wait_cursor(value):
    for wm in bpy.data.window_managers:
        for window in wm.windows:
            if value:
                window.cursor_modal_set('WAIT')
            else:
                window.cursor_modal_restore()


class PREFERENCES_OT_keyconfig_activate(Operator):
    bl_idname = "preferences.keyconfig_activate"
    bl_label = "Activate Keyconfig"

    filepath: StringProperty(
        subtype='FILE_PATH',
    )

    def execute(self, _context):
        if bpy.utils.keyconfig_set(self.filepath, report=self.report):
            return {'FINISHED'}
        else:
            return {'CANCELLED'}


class PREFERENCES_OT_copy_prev(Operator):
    """Copy settings from previous version"""
    bl_idname = "preferences.copy_prev"
    bl_label = "Copy Previous Settings"

    @classmethod
    def _old_version_path(cls, version):
        return bpy.utils.resource_path('USER', major=version[0], minor=version[1])

    @classmethod
    def previous_version(cls):
        import os
        # Find config folder from previous version.
        #
        # Always allow to load startup data from any release from current major release cycle, and the previous one.

        # NOTE: This value may need to be updated when the release cycle system is modified.
        # Here could be `6` in theory (Blender 3.6 LTS), just give it a bit of extra room, such that it does not have to
        # be updated if there ever exist a 3.7 release e.g.
        MAX_MINOR_VERSION_FOR_PREVIOUS_MAJOR_LOOKUP = 10

        version_new = bpy.app.version[:2]
        version_old = [version_new[0], version_new[1] - 1]

        while True:
            while version_old[1] >= 0:
                if os.path.isdir(cls._old_version_path(version_old)):
                    return tuple(version_old)
                version_old[1] -= 1
            if version_new[0] == version_old[0]:
                # Retry with older major version.
                version_old[0] -= 1
                version_old[1] = MAX_MINOR_VERSION_FOR_PREVIOUS_MAJOR_LOOKUP
            else:
                break

        return None

    @classmethod
    def _old_path(cls):
        version_old = cls.previous_version()
        return cls._old_version_path(version_old) if version_old else None

    @classmethod
    def _new_path(cls):
        return bpy.utils.resource_path('USER')

    @classmethod
    def poll(cls, _context):
        import os

        old = cls._old_path()
        new = cls._new_path()
        if not old:
            return False

        # Disable operator in case config path is overridden with environment
        # variable. That case has no automatic per-version configuration.
        userconfig_path = os.path.normpath(bpy.utils.user_resource('CONFIG'))
        new_userconfig_path = os.path.normpath(os.path.join(new, "config"))
        if userconfig_path != new_userconfig_path:
            return False

        # Enable operator if new config path does not exist yet.
        if os.path.isdir(old) and not os.path.isdir(new):
            return True

        # Enable operator also if there are no new user preference yet.
        old_userpref = os.path.join(old, "config", "userpref.blend")
        new_userpref = os.path.join(new, "config", "userpref.blend")
        return os.path.isfile(old_userpref) and not os.path.isfile(new_userpref)

    def execute(self, _context):
        import shutil
        shutil.copytree(self._old_path(), self._new_path(), dirs_exist_ok=True, symlinks=True)

        # Reload preferences and `recent-files.txt`.
        bpy.ops.wm.read_userpref()
        bpy.ops.wm.read_history()
        # Fix operator presets that have unwanted filepath properties
        bpy.ops.wm.operator_presets_cleanup()

        # don't loose users work if they open the splash later.
        if bpy.data.is_saved is bpy.data.is_dirty is False:
            bpy.ops.wm.read_homefile()
        else:
            self.report({'INFO'}, "Reload Start-Up file to restore settings")

        return {'FINISHED'}


class PREFERENCES_OT_keyconfig_test(Operator):
    """Test key configuration for conflicts"""
    bl_idname = "preferences.keyconfig_test"
    bl_label = "Test Key Configuration for Conflicts"

    def execute(self, context):
        from bpy_extras import keyconfig_utils

        wm = context.window_manager
        kc = wm.keyconfigs.default

        if keyconfig_utils.keyconfig_test(kc):
            print("CONFLICT")

        return {'FINISHED'}


class PREFERENCES_OT_keyconfig_import(Operator):
    """Import key configuration from a Python script"""
    bl_idname = "preferences.keyconfig_import"
    bl_label = "Import Key Configuration..."

    filepath: StringProperty(
        subtype='FILE_PATH',
        default="keymap.py",
    )
    filter_folder: BoolProperty(
        name="Filter folders",
        default=True,
        options={'HIDDEN'},
    )
    filter_text: BoolProperty(
        name="Filter text",
        default=True,
        options={'HIDDEN'},
    )
    filter_python: BoolProperty(
        name="Filter Python",
        default=True,
        options={'HIDDEN'},
    )
    keep_original: BoolProperty(
        name="Keep Original",
        description="Keep original file after copying to configuration folder",
        default=True,
    )

    # When importing keymap files with the same name with built-in presets (like
    # "Blender" or "Industry Compatible"), we need to rename the imported ones
    # so those entries can be properly removed (built-in ones can't be removed).
    # See #118035.
    @classmethod
    def _preset_prevent_name_collision(cls, config_name):
        import os
        from bpy.utils import is_path_builtin
        path = bpy.utils.user_resource(
            'SCRIPTS',
            path=os.path.join("presets", "keyconfig"),
            create=True,
        )

        config_name_final = config_name
        config_name_noext, config_name_ext = os.path.splitext(config_name)
        preset_path = bpy.utils.preset_find(config_name_noext, "keyconfig", ext=".py")

        if preset_path is not None and is_path_builtin(preset_path):
            config_name_final = "{:s} (User){:s}".format(config_name_noext, config_name_ext)

        return os.path.join(path, config_name_final)

    def execute(self, _context):
        import shutil
        from os.path import basename

        if not self.filepath:
            self.report({'ERROR'}, "Filepath not set")
            return {'CANCELLED'}

        config_name = basename(self.filepath)

        path = self._preset_prevent_name_collision(config_name)

        try:
            if self.keep_original:
                shutil.copy(self.filepath, path)
            else:
                shutil.move(self.filepath, path)
        except Exception as ex:
            self.report({'ERROR'}, rpt_("Installing keymap failed: {:s}").format(str(ex)))
            return {'CANCELLED'}

        # sneaky way to check we're actually running the code.
        if bpy.utils.keyconfig_set(path, report=self.report):
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

    def invoke(self, context, _event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

# This operator is also used by interaction presets saving - AddPresetBase


class PREFERENCES_OT_keyconfig_export(Operator):
    """Export key configuration to a Python script"""
    bl_idname = "preferences.keyconfig_export"
    bl_label = "Export Key Configuration..."

    all: BoolProperty(
        name="All Keymaps",
        default=False,
        description="Write all keymaps (not just user modified)",
    )
    filepath: StringProperty(
        subtype='FILE_PATH',
        default="",
    )
    filter_folder: BoolProperty(
        name="Filter folders",
        default=True,
        options={'HIDDEN'},
    )
    filter_text: BoolProperty(
        name="Filter text",
        default=True,
        options={'HIDDEN'},
    )
    filter_python: BoolProperty(
        name="Filter Python",
        default=True,
        options={'HIDDEN'},
    )

    def execute(self, context):
        from bl_keymap_utils.io import keyconfig_export_as_data

        if not self.filepath:
            raise Exception("Filepath not set")

        if not self.filepath.endswith(".py"):
            self.filepath += ".py"

        wm = context.window_manager

        keyconfig_export_as_data(
            wm,
            wm.keyconfigs.active,
            self.filepath,
            all_keymaps=self.all,
        )

        return {'FINISHED'}

    def invoke(self, context, _event):
        import os
        wm = context.window_manager
        if not self.filepath:
            self.filepath = os.path.join(
                os.path.expanduser("~"),
                bpy.path.display_name_to_filepath(wm.keyconfigs.active.name) + ".py",
            )
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


def _keyitem_selection_poll(context):
    """Poll for row operators: a key map in the context, or a non-empty selection."""
    import rna_keymap_ui
    if getattr(context, "keymap", None) is not None:
        return True
    return bool(rna_keymap_ui.keymap_selection_count())


def _keymap_filter_labels_clear(_context):
    from bl_keymap_utils import editor_meta
    for label_name, _use_filter in editor_meta.labels_list():
        editor_meta.label_filter_set(label_name, False)


def _keyitem_targets(op, context):
    """(key map, item) pairs to act on: the selection, or the context row (and the selection if it is selected)."""
    import rna_keymap_ui
    if op.use_selection:
        return rna_keymap_ui.keymap_selection_items()

    km = getattr(context, "keymap", None)
    if km is None:
        return []
    kmi = km.keymap_items.from_id(op.item_id)
    if kmi is None:
        return []
    return rna_keymap_ui.keymap_selection_targets(km, kmi)


class PREFERENCES_OT_keymap_restore(Operator):
    """Restore key map(s)"""
    bl_idname = "preferences.keymap_restore"
    bl_label = "Restore Key Map(s)"

    all: BoolProperty(
        name="All Keymaps",
        description="Restore all keymaps to default",
    )

    def execute(self, context):
        wm = context.window_manager

        if self.all:
            for km in wm.keyconfigs.user.keymaps:
                km.restore_to_default()
        else:
            km = context.keymap
            km.restore_to_default()

        context.preferences.is_dirty = True
        return {'FINISHED'}


class PREFERENCES_OT_keyitem_restore(Operator):
    """Restore key map item"""
    bl_idname = "preferences.keyitem_restore"
    bl_label = "Restore Key Map Item"

    item_id: IntProperty(
        name="Item Identifier",
        description="Identifier of the item to restore",
    )
    use_selection: BoolProperty(
        name="Use Selection",
        description="Act on every selected key map item rather than on one row",
        default=False,
        options={'SKIP_SAVE'},
    )

    @classmethod
    def poll(cls, context):
        return _keyitem_selection_poll(context)

    def execute(self, context):
        restored = 0
        for km, kmi in _keyitem_targets(self, context):
            if (not kmi.is_user_defined) and kmi.is_user_modified:
                km.restore_item_to_default(kmi)
                restored += 1

        if restored:
            context.preferences.is_dirty = True
        elif self.use_selection:
            self.report({'INFO'}, "No selected key map item was customized")
        return {'FINISHED'}


class PREFERENCES_OT_keyitem_intent_detach(Operator):
    """Detach the key map item from its shared shortcut, so it keeps a key of its own"""
    bl_idname = "preferences.keyitem_intent_detach"
    bl_label = "Detach from Shared Shortcut"

    item_id: IntProperty(
        name="Item Identifier",
        description="Identifier of the item to detach",
    )

    @classmethod
    def poll(cls, context):
        keymap = getattr(context, "keymap", None)
        return keymap

    def invoke(self, context, event):
        km = context.keymap
        kmi = km.keymap_items.from_id(self.item_id)
        if kmi is None or not kmi.intent:
            return {'CANCELLED'}
        intent = context.window_manager.keyconfigs.user.intents.get(kmi.intent)
        label = intent.label if intent else kmi.intent
        return context.window_manager.invoke_confirm(
            self,
            event,
            title=self.bl_label,
            message=rpt_("Detach \"{:s}\" from shared shortcut \"{:s}\"? "
                         "The item keeps its current key but no longer follows the shared shortcut.").format(
                kmi.name or kmi.idname, label),
            confirm_text="Detach",
            translate=False,
        )

    def execute(self, context):
        km = context.keymap
        kmi = km.keymap_items.from_id(self.item_id)
        if kmi is None:
            return {'CANCELLED'}
        kmi.intent = ""
        context.preferences.is_dirty = True
        return {'FINISHED'}


class PREFERENCES_OT_keyintent_category_toggle(Operator):
    """Show or hide the shared shortcuts of this category"""
    bl_idname = "preferences.keyintent_category_toggle"
    bl_label = "Toggle Shared Shortcut Category"
    bl_options = {'INTERNAL'}

    category: StringProperty(
        name="Category",
        description="Category of shared shortcuts to show or hide",
    )

    def execute(self, context):
        intents = [
            intent for intent in context.window_manager.keyconfigs.user.intents
            if intent.category == self.category
        ]
        if not intents:
            return {'CANCELLED'}
        expanded = not intents[0].show_category_expanded
        for intent in intents:
            intent.show_category_expanded = expanded
        return {'FINISHED'}


class PREFERENCES_OT_keyintent_restore(Operator):
    """Restore the key of the shared shortcut to the key configuration preset"""
    bl_idname = "preferences.keyintent_restore"
    bl_label = "Restore Shared Shortcut"

    intent: StringProperty(
        name="Shared Shortcut",
        description="Identifier of the shared shortcut to restore",
    )

    def execute(self, context):
        intent = context.window_manager.keyconfigs.user.intents.get(self.intent)
        if intent is None:
            return {'CANCELLED'}
        if intent.is_user_modified:
            intent.restore_to_default()
            context.preferences.is_dirty = True
        return {'FINISHED'}


class PREFERENCES_OT_keyintent_reveal(Operator):
    """Show this shared shortcut in the Shared Shortcuts column"""
    bl_idname = "preferences.keyintent_reveal"
    bl_label = "Show Shared Shortcut"
    bl_options = {'INTERNAL'}

    intent: StringProperty(
        name="Shared Shortcut",
        description="Identifier of the shared shortcut to show",
    )

    @classmethod
    def description(cls, context, props):
        intent = context.window_manager.keyconfigs.user.intents.get(props.intent)
        if intent is None:
            return None
        return rpt_("Show \"{:s}\" in the Shared Shortcuts column").format(intent.label)

    def execute(self, context):
        import rna_keymap_ui
        kc = context.window_manager.keyconfigs.user
        intent = kc.intents.get(self.intent)
        if intent is None:
            return {'CANCELLED'}

        # The column may be hidden, and the intent inside a collapsed category.
        area = context.area
        if area is not None and area.type == 'PREFERENCES':
            if not rna_keymap_ui.keymap_intents_region_visible(area):
                with context.temp_override(area=area):
                    bpy.ops.screen.region_toggle(region_type='CHANNELS')
        if intent.category and not intent.show_category_expanded:
            for other in kc.intents:
                if other.category == intent.category:
                    other.show_category_expanded = True

        rna_keymap_ui.set_intent_reveal_target(intent)
        return {'FINISHED'}


class PREFERENCES_OT_keyitem_add(Operator):
    """Add key map item"""
    bl_idname = "preferences.keyitem_add"
    bl_label = "Add Key Map Item"

    def execute(self, context):
        km = context.keymap

        if km.is_modal:
            km.keymap_items.new_modal("", 'A', 'PRESS')
        else:
            km.keymap_items.new("none", 'A', 'PRESS')

        # clear filter and expand keymap so we can see the newly added item
        if context.space_data.filter_text != "":
            context.space_data.filter_text = ""
            km.show_expanded_items = True
            km.show_expanded_children = True

        context.preferences.is_dirty = True
        return {'FINISHED'}


class PREFERENCES_OT_keyitem_copy(Operator):
    """Copy this key map item to the clipboard, to paste into another key map or """ \
        """key configuration, or to share as text"""
    bl_idname = "preferences.keyitem_copy"
    bl_label = "Copy Key Map Item"

    item_id: IntProperty(
        name="Item Identifier",
        description="Identifier of the item to copy",
    )
    use_selection: BoolProperty(
        name="Use Selection",
        description="Act on every selected key map item rather than on one row",
        default=False,
        options={'SKIP_SAVE'},
    )

    @classmethod
    def poll(cls, context):
        return _keyitem_selection_poll(context)

    def execute(self, context):
        import rna_keymap_ui
        targets = _keyitem_targets(self, context)
        if not targets:
            self.report({'ERROR'}, "Key map item not found")
            return {'CANCELLED'}

        rna_keymap_ui.keymap_items_clipboard_set(targets)
        if len(targets) == 1:
            km, kmi = targets[0]
            self.report(
                {'INFO'},
                rpt_("Copied \"{:s}\" to the clipboard").format(
                    rna_keymap_ui.keymap_item_label(km, kmi)),
            )
        else:
            self.report(
                {'INFO'},
                rpt_("Copied {:d} shortcuts to the clipboard").format(len(targets)),
            )
        return {'FINISHED'}


class PREFERENCES_OT_keyitem_paste(Operator):
    """Add the key map items on the clipboard to this key map"""
    bl_idname = "preferences.keyitem_paste"
    bl_label = "Paste Key Map Item"

    use_source_keymap: BoolProperty(
        name="Back Where They Came From",
        description="Put each copy into the key map it was copied from, for when no key map "
                    "is being pointed at",
        default=False,
        options={'SKIP_SAVE'},
    )

    @classmethod
    def poll(cls, context):
        import rna_keymap_ui
        clips = rna_keymap_ui.keymap_item_clipboard()
        if clips is None:
            cls.poll_message_set("The clipboard does not hold a copied key map item")
            return False

        km = getattr(context, "keymap", None)
        if km is None:
            # No key map in the context: paste back into the source key maps.
            if rna_keymap_ui.keymap_clipboard_sources(clips):
                return True
            cls.poll_message_set(
                "The copied text does not say which key map it came from")
            return False

        if rna_keymap_ui.keymap_clipboard_pasteable(km, clips):
            return True

        # Poll message based on the first item.
        clip = clips[0]
        if km.is_modal:
            if clip["modal"] is None:
                cls.poll_message_set(
                    "A shortcut for an operator cannot be pasted into a modal key map")
            else:
                cls.poll_message_set(
                    rpt_("This key map has no \"{:s}\" to bind, the copied item "
                         "belongs to \"{:s}\"").format(clip["label"], clip["modal"]))
        else:
            cls.poll_message_set(
                rpt_("The copied item belongs to the modal key map \"{:s}\", "
                     "it can only be pasted into a modal key map").format(clip["modal"]))
        return False

    def execute(self, context):
        import rna_keymap_ui
        km = None if self.use_source_keymap else getattr(context, "keymap", None)

        clips = rna_keymap_ui.keymap_item_clipboard(use_cache=False)
        if clips is None:
            self.report({'ERROR'}, "The clipboard does not hold a copied key map item")
            return {'CANCELLED'}

        if km is None:
            sources = rna_keymap_ui.keymap_clipboard_sources(clips)
            if not sources:
                self.report({'ERROR'}, "The copied text does not say which key map it came from")
                return {'CANCELLED'}
            return self._paste_to_sources(context, sources, skipped=len(clips) - len(sources))

        pasteable = rna_keymap_ui.keymap_clipboard_pasteable(km, clips)
        if not pasteable:
            self.report({'ERROR'}, "Nothing on the clipboard fits this key map")
            return {'CANCELLED'}

        if len(pasteable) > 1:
            return self._paste_set(context, km, pasteable, skipped=len(clips) - len(pasteable))

        clip = pasteable[0]
        try:
            kmi_new = rna_keymap_ui.keymap_item_clipboard_paste(km, clip)
        except Exception as ex:
            self.report({'ERROR'}, rpt_("Cannot paste this key map item: {:s}").format(str(ex)))
            return {'CANCELLED'}
        if kmi_new is None:
            self.report({'ERROR'}, "Nothing to paste")
            return {'CANCELLED'}
        kmi_new.show_expanded = True

        is_modal = km.is_modal
        conflicts = [
            kmi for kmi in km.keymap_items
            if kmi.id != kmi_new.id and kmi.compare(kmi_new) and (
                (kmi.propvalue != kmi_new.propvalue) if is_modal
                else (kmi.idname != kmi_new.idname)
            )
        ]

        self._reveal(context, km)
        context.preferences.is_dirty = True

        name = rna_keymap_ui.keymap_item_label(km, kmi_new)
        if not clip["available"]:
            self.report(
                {'WARNING'},
                rpt_("Pasted \"{:s}\", but this Blender has no such operator; "
                     "the shortcut will not do anything").format(clip["idname"]),
            )
        elif kmi_new.is_user_duplicate:
            self.report(
                {'INFO'},
                rpt_("Pasted \"{:s}\" beside the shortcut it copies, "
                     "ready to be changed").format(name),
            )
        elif not conflicts:
            self.report({'INFO'}, rpt_("Pasted \"{:s}\"").format(name))
        else:
            conflict_names = ", ".join(
                "\"{:s}\"".format(rna_keymap_ui.keymap_item_label(km, kmi))
                for kmi in conflicts
            )
            if is_modal:
                self.report(
                    {'WARNING'},
                    rpt_("Pasted \"{:s}\", but this key is already used by {:s}; use "
                         "\"Override Conflicts\" to give it priority").format(
                        name, conflict_names),
                )
            else:
                self.report(
                    {'WARNING'},
                    rpt_("Pasted \"{:s}\", but this key is already used by {:s}; use "
                         "\"Override Conflicts\" once the preferences are reloaded").format(
                        name, conflict_names),
                )
        return {'FINISHED'}

    def _reveal(self, context, km):
        """Clear the filter and expand the key map, so pasted items are visible."""
        space_data = getattr(context, "space_data", None)
        if space_data is not None and space_data.filter_text != "":
            space_data.filter_text = ""
        km.show_expanded_items = True
        km.show_expanded_children = True

    def _paste_set(self, context, km, clips, skipped):
        """Paste several items into one key map and select them."""
        import rna_keymap_ui
        wm = context.window_manager

        pasted = []
        failed = 0
        for clip in clips:
            try:
                kmi_new = rna_keymap_ui.keymap_item_clipboard_paste(km, clip)
            except Exception:
                kmi_new = None
            if kmi_new is None:
                failed += 1
                continue
            pasted.append(kmi_new)

        if not pasted:
            self.report({'ERROR'}, "None of the copied shortcuts could be pasted")
            return {'CANCELLED'}

        wm.keymap_selection_clear()
        for kmi_new in pasted:
            wm.keymap_selection_set(km, kmi_new, True)
        rna_keymap_ui.keymap_selection_changed()

        self._reveal(context, km)
        context.preferences.is_dirty = True

        message = rpt_("Pasted and selected {:d} shortcuts").format(len(pasted))
        if skipped or failed:
            self.report(
                {'WARNING'},
                rpt_("{:s} — {:d} did not fit this key map").format(message, skipped + failed),
            )
        else:
            self.report({'INFO'}, message)
        return {'FINISHED'}

    def _paste_to_sources(self, context, sources, skipped):
        """Paste each item back into its source key map (no key map in the context)."""
        import rna_keymap_ui
        wm = context.window_manager

        pasted = []
        failed = 0
        for km, clip in sources:
            try:
                kmi_new = rna_keymap_ui.keymap_item_clipboard_paste(km, clip)
            except Exception:
                kmi_new = None
            if kmi_new is None:
                failed += 1
                continue
            pasted.append((km, kmi_new))

        if not pasted:
            self.report({'ERROR'}, "None of the copied shortcuts could be pasted")
            return {'CANCELLED'}

        # Selected so they can be found again through the filters.
        wm.keymap_selection_clear()
        for km, kmi_new in pasted:
            wm.keymap_selection_set(km, kmi_new, True)
            self._reveal(context, km)
        rna_keymap_ui.keymap_selection_changed()
        context.preferences.is_dirty = True

        names = {km.name for km, _kmi_new in pasted}
        if len(pasted) == 1:
            km, kmi_new = pasted[0]
            message = rpt_("Pasted \"{:s}\" into {:s}").format(
                rna_keymap_ui.keymap_item_label(km, kmi_new), km.name)
        elif len(names) == 1:
            message = rpt_("Pasted {:d} shortcuts into {:s}").format(
                len(pasted), next(iter(names)))
        else:
            message = rpt_("Pasted {:d} shortcuts into {:d} key maps").format(
                len(pasted), len(names))

        if skipped or failed:
            self.report(
                {'WARNING'},
                rpt_("{:s} — {:d} could not be placed").format(message, skipped + failed),
            )
        else:
            self.report({'INFO'}, message)
        return {'FINISHED'}


class PREFERENCES_OT_keyitem_unshadow(Operator):
    """Disable the earlier key map items that use this key, so this one runs"""
    bl_idname = "preferences.keyitem_unshadow"
    bl_label = "Disable Conflicting Key Map Items"

    item_id: IntProperty(
        name="Item Identifier",
        description="Identifier of the item to give priority to",
    )

    @classmethod
    def poll(cls, context):
        return getattr(context, "keymap", None) is not None

    def execute(self, context):
        import rna_keymap_ui
        km = context.keymap
        kmi = km.keymap_items.from_id(self.item_id)
        if kmi is None:
            self.report({'ERROR'}, "Key map item not found")
            return {'CANCELLED'}

        # Items are matched in order, so only earlier items shadow this one.
        shadowing = []
        for kmi_other in km.keymap_items:
            if kmi_other.id == kmi.id:
                break
            if kmi_other.active and kmi_other.compare(kmi):
                shadowing.append(kmi_other)

        if not shadowing:
            self.report({'INFO'}, "Nothing is overriding this item")
            return {'CANCELLED'}

        names = [rna_keymap_ui.keymap_item_label(km, kmi_other) for kmi_other in shadowing]
        for kmi_other in shadowing:
            kmi_other.active = False

        context.preferences.is_dirty = True
        self.report(
            {'INFO'},
            rpt_("Disabled {:s}").format(", ".join("\"{:s}\"".format(n) for n in names)),
        )
        return {'FINISHED'}


class PREFERENCES_OT_keyitem_remove(Operator):
    """Remove key map item"""
    bl_idname = "preferences.keyitem_remove"
    bl_label = "Remove Key Map Item"

    item_id: IntProperty(
        name="Item Identifier",
        description="Identifier of the item to remove",
    )
    use_selection: BoolProperty(
        name="Use Selection",
        description="Act on every selected key map item rather than on one row",
        default=False,
        options={'SKIP_SAVE'},
    )

    @classmethod
    def poll(cls, context):
        return _keyitem_selection_poll(context)

    def execute(self, context):
        import rna_keymap_ui
        targets = _keyitem_targets(self, context)
        if not targets:
            return {'CANCELLED'}

        wm = context.window_manager
        keymap_prefs = context.preferences.keymap
        for km, kmi in targets:
            # Deselect first: the selection stores the item id, which is about to be invalid.
            wm.keymap_selection_set(km, kmi, False)
            keymap_prefs.item_forget(km, kmi)
            km.keymap_items.remove(kmi)
        rna_keymap_ui.keymap_selection_changed()

        if len(targets) > 1:
            self.report({'INFO'}, rpt_("Removed {:d} shortcuts").format(len(targets)))
        context.preferences.is_dirty = True
        return {'FINISHED'}


class PREFERENCES_OT_keymap_activity_clear(Operator):
    """Clear the list of recently used key map items"""
    bl_idname = "preferences.keymap_activity_clear"
    bl_label = "Clear Recently Used Key Map Items"

    def execute(self, context):
        context.window_manager.keymap_activity_clear()
        return {'FINISHED'}


class PREFERENCES_OT_keymap_activity_find(Operator):
    """Filter the key map editor to show matching items"""
    bl_idname = "preferences.keymap_activity_find"
    bl_label = "Find Key Map Item"

    filter_type: EnumProperty(
        name="Search Type",
        items=(
            ('NAME', "Name", "Search by operator name"),
            ('KEY', "Key-Binding", "Search by key binding"),
        ),
    )
    filter_text: StringProperty(
        name="Filter Text",
        description="Text to search for",
    )
    use_exact: BoolProperty(
        name="Exact Key Binding",
        description="Match the whole key binding rather than any binding containing it",
        default=False,
        options={'SKIP_SAVE'},
    )

    @classmethod
    def description(cls, _context, props):
        if props.filter_type != 'KEY':
            return "Search the key map editor for this operator"
        if props.use_exact:
            return "Show everything else bound to this exact key binding"
        return "Search the key map editor for this key binding"

    def execute(self, context):
        space = context.space_data
        if space is None or space.type != 'PREFERENCES':
            return {'CANCELLED'}
        space.filter_type = self.filter_type
        space.filter_text = self.filter_text
        space.use_filter_key_exact = self.use_exact and self.filter_type == 'KEY'
        space.use_filter_user_modified = False
        _keymap_filter_labels_clear(context)
        space.use_filter_addon = False
        space.use_filter_conflicts = False
        return {'FINISHED'}


def _keymap_conflicts_check_show(context, targets):
    """Set the conflict check group to `targets` and show their conflicts; False without a preferences editor."""
    import rna_keymap_ui

    space = _preferences_space(context)
    if space is None:
        return False

    # Items are held by identity, not pushed through the search field:
    # a key string does not reliably round-trip and cannot carry several bindings.
    rna_keymap_ui.keymap_conflict_check_set(targets)

    # Other filters would narrow the result.
    space.filter_text = ""
    space.use_filter_key_exact = False
    space.use_filter_user_modified = False
    _keymap_filter_labels_clear(context)
    space.use_filter_addon = False
    space.use_filter_conflicts = True
    return True


class PREFERENCES_OT_keymap_conflicts_check(Operator):
    """Show every shortcut in conflict with these, in this and every key map active at the same time"""
    bl_idname = "preferences.keymap_conflicts_check"
    bl_label = "Check for Conflicts"

    item_id: IntProperty(
        name="Item Identifier",
        description="Identifier of the item to check",
    )
    use_selection: BoolProperty(
        name="Use Selection",
        description="Check every selected key map item rather than one row",
        default=False,
        options={'SKIP_SAVE'},
    )

    @classmethod
    def poll(cls, context):
        return _keyitem_selection_poll(context)

    def execute(self, context):
        targets = _keyitem_targets(self, context)
        if not targets:
            self.report({'ERROR'}, "Key map item not found")
            return {'CANCELLED'}
        if not _keymap_conflicts_check_show(context, targets):
            return {'CANCELLED'}
        return {'FINISHED'}


def _keyitem_add_keymap(context, name):
    """The active user key map with this name, or None."""
    km = context.window_manager.keyconfigs.user.keymaps.get(name)
    return None if km is None else km.active()


def _keyitem_add_keymap_for_space(space_type):
    """Name of the editor's own key map (the outermost hierarchy entry with this space type), or None."""
    if not space_type or space_type == 'EMPTY':
        return None
    from bl_keymap_utils import keymap_hierarchy
    for name, entry_space_type, _region_type, _children in keymap_hierarchy.generate():
        if entry_space_type == space_type:
            return name
    return None


def _keyitem_add_live_item(props, context):
    """The (key map, item) the dialog is editing, or (None, None)."""
    km = _keyitem_add_keymap(context, props.live_keymap_name)
    if km is None:
        return None, None
    return km, km.keymap_items.from_id(props.live_item_id)


def _keyitem_add_create(props, km):
    """Add an unbound item for the dialog's key capture field to fill in."""
    kmi = km.keymap_items.new(props.idname, 'NONE', 'PRESS')
    if props.variant:
        import rna_keymap_ui
        rna_keymap_ui.usage_variant_apply(kmi, props.variant)
    props.live_keymap_name = km.name
    props.live_item_id = kmi.id
    return kmi


def _keyitem_add_keymap_name_update(props, context):
    """
    Move the live item to the chosen key map, keeping the captured key.
    Module level: property update callbacks receive the properties, not the operator.
    """
    km_old, kmi_old = _keyitem_add_live_item(props, context)
    if km_old is None or km_old.name == props.keymap_name:
        return
    km_new = _keyitem_add_keymap(context, props.keymap_name)
    if km_new is None or km_new.is_modal:
        props.keymap_name = km_old.name
        return
    event = None
    if kmi_old is not None:
        event = (kmi_old.type, kmi_old.value, kmi_old.ctrl, kmi_old.alt,
                 kmi_old.shift, kmi_old.oskey)
        km_old.keymap_items.remove(kmi_old)
    kmi_new = _keyitem_add_create(props, km_new)
    if event is not None:
        (kmi_new.type, kmi_new.value, kmi_new.ctrl, kmi_new.alt,
         kmi_new.shift, kmi_new.oskey) = event


class PREFERENCES_OT_keyitem_add_for_operator(Operator):
    """Add a shortcut for this operator in a key map of your choosing"""
    bl_idname = "preferences.keyitem_add_for_operator"
    bl_label = "Add Shortcut"

    idname: StringProperty(
        name="Operator",
        description="Identifier of the operator to bind",
        options={'SKIP_SAVE'},
    )
    variant: StringProperty(
        name="Variant",
        description="Which use of the operator to bind, if it has several",
        options={'SKIP_SAVE'},
    )
    name: StringProperty(
        name="Name",
        description=(
            "What to call this shortcut in the key map editor. "
            "Empty to use the operator's own name"
        ),
        options={'SKIP_SAVE'},
    )

    keymap_name: StringProperty(
        name="Key Map",
        description="Key map to add the shortcut to, which decides where it applies",
        options={'SKIP_SAVE'},
        update=_keyitem_add_keymap_name_update,
    )
    space_type: StringProperty(
        name="Space Type",
        description="Editor the operation was used in, which helps place the shortcut",
        options={'SKIP_SAVE'},
    )
    live_keymap_name: StringProperty(options={'SKIP_SAVE', 'HIDDEN'})
    live_item_id: IntProperty(default=0, options={'SKIP_SAVE', 'HIDDEN'})

    _KEYMAP_BY_MODULE = {
        "object": "Object Mode",
        "mesh": "Mesh",
        "curve": "Curve",
        "armature": "Armature",
        "pose": "Pose",
        "sculpt": "Sculpt",
        "paint": "Paint Curve",
        "view3d": "3D View",
        "node": "Node Editor",
        "graph": "Graph Editor",
        "action": "Dopesheet",
        "nla": "NLA Editor",
        "sequencer": "Sequencer",
        "clip": "Clip Editor",
        "image": "Image",
        "uv": "UV Editor",
        "text": "Text",
        "console": "Console",
        "file": "File Browser",
        "outliner": "Outliner",
        "transform": "3D View",
        "gpencil": "Grease Pencil",
        "screen": "Screen",
        "wm": "Window",
    }

    def _keymap_name_default(self):
        """
        Default key map for the dialog: by operator module, or by the editor the operator was
        last used in for editor-scoped operators (`wm.context_*`) and unknown modules.
        """
        import rna_keymap_ui

        module = self.idname.partition(".")[0]
        by_module = self._KEYMAP_BY_MODULE.get(module)
        if by_module is None or rna_keymap_ui.usage_variant_is_editor_scoped(
                self.idname, self.variant):
            by_space = _keyitem_add_keymap_for_space(self.space_type)
            if by_space is not None:
                return by_space
        return by_module or "Window"

    def invoke(self, context, _event):
        if not self.idname:
            return {'CANCELLED'}
        if not self.keymap_name:
            self.keymap_name = self._keymap_name_default()
        if not self.name:
            import rna_keymap_ui
            self.name = rna_keymap_ui.usage_suggested_name(context, self.idname, self.variant)

        km = _keyitem_add_keymap(context, self.keymap_name)
        if km is None or km.is_modal:
            # Modal key maps bind modal actions, not operators.
            self.report({'ERROR'}, "Cannot add a shortcut to \"{:s}\"".format(self.keymap_name))
            return {'CANCELLED'}
        _keyitem_add_create(self, km)
        context.preferences.is_dirty = True
        return context.window_manager.invoke_props_dialog(self, width=340)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        # Same icon as "Change Shortcut...".
        col.label(text=self.idname, translate=False, icon='HAND')
        if self.variant:
            sub = col.row()
            sub.active = False
            sub.label(text=self.variant, translate=False)

        col.separator()
        col.prop(self, "name")

        col.prop_search(
            self, "keymap_name",
            context.window_manager.keyconfigs.user, "keymaps",
            text="Key Map",
        )

        km, kmi = _keyitem_add_live_item(self, context)

        col.separator()
        if kmi is None:
            col.label(text="Key map item was removed", icon='ERROR')
            return

        col.prop(kmi, "type", text="Key", full_event=True)

        import rna_keymap_ui
        clashes = rna_keymap_ui.keymap_item_clashes(km, kmi)
        if clashes:
            key = kmi.to_string()

            # Certain clashes block this shortcut; shared ones are the same key in key maps
            # that need not both be active (same rule as the tree's conflict marker).
            certain = []
            shared = []
            for keymap_name, item_id, label, is_here in clashes:
                target = certain if rna_keymap_ui.keymap_clash_is_certain(
                    km.name, keymap_name, is_here) else shared
                target.append((keymap_name, item_id, label, is_here))

            def draw_clash_line(layout, text, icon, keymap_name, item_id, is_outranked):
                """One clash row, with a button to show it in the tree."""
                row = layout.row(align=True)
                row.label(text=text, translate=False, icon=icon)
                sub_row = row.row(align=True)
                sub_row.alignment = 'RIGHT'
                sub_row.alert = False
                props = sub_row.operator(
                    "preferences.keyitem_flash_conflict",
                    text="",
                    icon='VIEWZOOM',
                    emboss=False,
                )
                props.keymap_name = keymap_name
                props.item_id = item_id
                props.is_outranked = is_outranked

            def draw_remaining(layout, count):
                """Overflow line for lists capped at `_KMI_CLASH_MAX_KEYMAPS`."""
                if count > 0:
                    layout.label(
                        text=iface_("and {:d} more").format(count),
                        translate=False,
                        icon='BLANK1',
                    )

            cap = rna_keymap_ui._KMI_CLASH_MAX_KEYMAPS

            if certain:
                col.separator()
                sub = col.column(align=True)
                sub.alert = True
                for index, (keymap_name, item_id, label, is_here) in enumerate(certain[:cap]):
                    if index:
                        text = iface_("and {:s} in {:s}").format(label, keymap_name)
                    elif is_here:
                        text = iface_("{:s} already runs {:s} here").format(key, label)
                    else:
                        text = iface_("{:s} runs {:s} in {:s} first").format(
                            key, label, keymap_name)
                    # A certain clash in another key map means that key map is matched first.
                    draw_clash_line(
                        sub, text, 'ERROR' if index == 0 else 'BLANK1',
                        keymap_name, item_id, not is_here,
                    )
                draw_remaining(sub, len(certain) - min(len(certain), cap))

            if shared:
                col.separator()
                sub = col.column(align=True)
                sub.label(
                    text=iface_("{:s} is also used in other key maps").format(key),
                    translate=False,
                    icon='INFO',
                )
                for keymap_name, item_id, label, _is_here in shared[:cap]:
                    draw_clash_line(
                        sub,
                        iface_("{:s} in {:s}").format(label, keymap_name),
                        'BLANK1',
                        keymap_name,
                        item_id,
                        False,
                    )
                draw_remaining(sub, len(shared) - min(len(shared), cap))

    def cancel(self, context):
        # Remove the temporary item created in `invoke`.
        km, kmi = _keyitem_add_live_item(self, context)
        if kmi is not None:
            km.keymap_items.remove(kmi)
            context.preferences.is_dirty = True

    def execute(self, context):
        km, kmi = _keyitem_add_live_item(self, context)
        if kmi is None:
            self.report({'ERROR'}, "Add Shortcut has to be invoked, not executed directly")
            return {'CANCELLED'}
        if kmi.type == 'NONE':
            km.keymap_items.remove(kmi)
            self.report({'WARNING'}, "No key was pressed, so no shortcut was added")
            return {'CANCELLED'}

        name = self.name.strip()
        if name and name != kmi.name:
            from bl_keymap_utils import editor_meta
            editor_meta.custom_name_set(km, kmi, name)

        context.preferences.is_dirty = True

        # Show the new item among the user modified items.
        # The dialog is a popup, so the editor must be found rather than read from the context.
        space = _preferences_space(context)
        if space is not None:
            import rna_keymap_ui

            space.filter_text = ""
            space.use_filter_key_exact = False
            space.use_filter_user_modified = True
            _keymap_filter_labels_clear(context)
            space.use_filter_addon = False
            space.use_filter_conflicts = False
            rna_keymap_ui.keymap_conflict_check_clear()
            # Collapse everything so only the revealed row is expanded.
            rna_keymap_ui.keymap_filtered_collapse()
            kmi.show_expanded = False
            rna_keymap_ui.set_reveal_target(km, kmi)

        self.report(
            {'INFO'},
            rpt_("Added \"{:s}\" to {:s} on {:s}").format(
                "{:s} [{:s}]".format(self.idname, self.variant) if self.variant else self.idname,
                km.name, kmi.to_string()),
        )
        return {'FINISHED'}


class PREFERENCES_OT_keymap_hide_item(Operator):
    """Keep this shortcut out of the usage lists, and stop counting it"""
    bl_idname = "preferences.keymap_hide_item"
    bl_label = "Hide Shortcut"

    keymap_name: StringProperty(name="Key Map", options={'SKIP_SAVE'})
    item_id: IntProperty(name="Item Identifier", default=0, options={'SKIP_SAVE'})
    use_item_id: BoolProperty(name="By Identifier", default=False, options={'SKIP_SAVE'})
    idname: StringProperty(name="Operator", options={'SKIP_SAVE'})
    key_string: StringProperty(name="Key Binding", options={'SKIP_SAVE'})
    is_modal: BoolProperty(name="Modal", options={'SKIP_SAVE'})
    propvalue: StringProperty(name="Modal Action", options={'SKIP_SAVE'})
    hide: BoolProperty(name="Hide", default=True, options={'SKIP_SAVE'})
    use_selection: BoolProperty(
        name="Use Selection",
        description="Act on every selected key map item rather than on one row",
        default=False,
        options={'SKIP_SAVE'},
    )

    def execute(self, context):
        import rna_keymap_ui
        from bl_keymap_utils import editor_meta
        if self.use_selection:
            targets = rna_keymap_ui.keymap_selection_items()
            if not targets:
                self.report({'ERROR'}, "No key map items are selected")
                return {'CANCELLED'}
            for km, kmi in targets:
                editor_meta.hidden_set(km, kmi, self.hide)
            self.report(
                {'INFO'},
                (rpt_("Hid {:d} shortcuts") if self.hide
                 else rpt_("Unhid {:d} shortcuts")).format(len(targets)),
            )
            return {'FINISHED'}

        kc = context.window_manager.keyconfigs.user
        km = kc.keymaps.get(self.keymap_name)
        if km is None:
            self.report({'ERROR'}, "Key map not found")
            return {'CANCELLED'}
        km = km.active()

        kmi = None
        if self.use_item_id:
            kmi = km.keymap_items.from_id(self.item_id)
        else:
            # Match the same way the recently used list does: key string plus idname/propvalue.
            for candidate in km.keymap_items:
                if candidate.to_string() != self.key_string:
                    continue
                if (candidate.propvalue == self.propvalue) if self.is_modal else (
                        candidate.idname == self.idname):
                    kmi = candidate
                    break
        if kmi is None:
            self.report({'ERROR'}, "Key map item not found")
            return {'CANCELLED'}

        editor_meta.hidden_set(km, kmi, self.hide)
        return {'FINISHED'}


class PREFERENCES_OT_keymap_hide_operator(Operator):
    """Keep this operation out of the usage lists, and stop counting it"""
    bl_idname = "preferences.keymap_hide_operator"
    bl_label = "Hide Operation"

    idname: StringProperty(name="Operator", options={'SKIP_SAVE'})
    variant: StringProperty(name="Variant", options={'SKIP_SAVE'})
    hide: BoolProperty(name="Hide", default=True, options={'SKIP_SAVE'})

    def execute(self, _context):
        from bl_keymap_utils import editor_meta
        if not self.idname:
            return {'CANCELLED'}
        editor_meta.operator_hidden_set(self.idname, self.variant, self.hide)
        return {'FINISHED'}


def _keymap_label_targets(op, context):
    """Targets for the label operators: the selection, or the item named by the properties."""
    import rna_keymap_ui
    if op.use_selection:
        return rna_keymap_ui.keymap_selection_items()
    km, kmi = _keymap_item_by_id(context, op.keymap_name, op.item_id)
    if kmi is None:
        return []
    return rna_keymap_ui.keymap_selection_targets(km, kmi)


def _keymap_label_report(op, targets, name, assign):
    if len(targets) > 1:
        text = rpt_("Added {:d} shortcuts to \"{:s}\"") if assign else rpt_(
            "Removed {:d} shortcuts from \"{:s}\"")
        op.report({'INFO'}, text.format(len(targets), name))


class PREFERENCES_OT_keymap_label_new(Operator):
    """Create a label, a named group of shortcuts to filter the key map editor by"""
    bl_idname = "preferences.keymap_label_new"
    bl_label = "New Label"

    name: StringProperty(
        name="Name",
        description="Name of the label",
        options={'SKIP_SAVE'},
    )
    assign: BoolProperty(
        name="Assign",
        description="Add the shortcut, or the selection, to the new label",
        default=False,
        options={'SKIP_SAVE'},
    )
    keymap_name: StringProperty(name="Key Map", options={'SKIP_SAVE', 'HIDDEN'})
    item_id: IntProperty(name="Item Identifier", options={'SKIP_SAVE', 'HIDDEN'})
    use_selection: BoolProperty(name="Use Selection", options={'SKIP_SAVE', 'HIDDEN'})

    def invoke(self, context, _event):
        # The dialog's context does not hold the row, so remember it now.
        km = getattr(context, "keymap", None)
        if km is not None:
            self.keymap_name = km.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, _context):
        layout = self.layout
        layout.activate_init = True
        layout.prop(self, "name")

    def execute(self, context):
        from bl_keymap_utils import editor_meta
        name = self.name.strip()
        if not name:
            self.report({'ERROR'}, "The label needs a name")
            return {'CANCELLED'}

        editor_meta.label_add(name)
        if self.assign:
            targets = _keymap_label_targets(self, context)
            for km, kmi in targets:
                editor_meta.label_item_set(name, km, kmi, True)
            _keymap_label_report(self, targets, name, True)

        return {'FINISHED'}


class PREFERENCES_OT_keymap_label_remove(Operator):
    """Remove the label from every shortcut and forget it"""
    bl_idname = "preferences.keymap_label_remove"
    bl_label = "Remove Label"

    name: StringProperty(name="Name", options={'SKIP_SAVE'})

    def execute(self, _context):
        from bl_keymap_utils import editor_meta
        if not editor_meta.label_remove(self.name):
            return {'CANCELLED'}
        return {'FINISHED'}


class PREFERENCES_OT_keymap_label_filter_toggle(Operator):
    """Toggle filtering the key map editor by this label"""
    bl_idname = "preferences.keymap_label_filter_toggle"
    bl_label = "Toggle Label Filter"

    name: StringProperty(name="Name", options={'SKIP_SAVE'})

    def execute(self, _context):
        from bl_keymap_utils import editor_meta
        if not editor_meta.label_filter_toggle(self.name):
            return {'CANCELLED'}
        return {'FINISHED'}


class PREFERENCES_OT_keyitem_rename(Operator):
    """Set a custom display name for this shortcut (empty to restore default)"""
    bl_idname = "preferences.keyitem_rename"
    bl_label = "Rename Shortcut"

    item_id: IntProperty(name="Item Identifier", options={'SKIP_SAVE', 'HIDDEN'})
    keymap_name: StringProperty(name="Key Map", options={'SKIP_SAVE', 'HIDDEN'})
    name: StringProperty(name="Name", options={'SKIP_SAVE'})

    def invoke(self, context, _event):
        from bl_keymap_utils import editor_meta
        km = getattr(context, "keymap", None)
        if km is None:
            return {'CANCELLED'}
        kmi = km.keymap_items.from_id(self.item_id)
        if kmi is None:
            return {'CANCELLED'}
        self.keymap_name = km.name
        self.name = editor_meta.custom_name_get(km, kmi)
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, _context):
        layout = self.layout
        layout.activate_init = True
        layout.prop(self, "name")

    def execute(self, context):
        from bl_keymap_utils import editor_meta
        km, kmi = _keymap_item_by_id(context, self.keymap_name, self.item_id)
        if kmi is None:
            return {'CANCELLED'}
        editor_meta.custom_name_set(km, kmi, self.name)
        return {'FINISHED'}


class PREFERENCES_OT_keymap_label_assign(Operator):
    """Add this shortcut to a label, or take it off one"""
    bl_idname = "preferences.keymap_label_assign"
    bl_label = "Assign Label"

    name: StringProperty(name="Name", options={'SKIP_SAVE'})
    assign: BoolProperty(
        name="Assign",
        description="Add the label rather than remove it",
        default=True,
        options={'SKIP_SAVE'},
    )
    keymap_name: StringProperty(name="Key Map", options={'SKIP_SAVE'})
    item_id: IntProperty(name="Item Identifier", options={'SKIP_SAVE'})
    use_selection: BoolProperty(
        name="Use Selection",
        description="Act on every selected key map item rather than on one row",
        default=False,
        options={'SKIP_SAVE'},
    )

    @classmethod
    def description(cls, _context, props):
        if props.assign:
            return rpt_("Add to the \"{:s}\" label").format(props.name)
        return rpt_("Remove from the \"{:s}\" label").format(props.name)

    def execute(self, context):
        from bl_keymap_utils import editor_meta
        targets = _keymap_label_targets(self, context)
        if not targets:
            self.report({'ERROR'}, "Key map item not found")
            return {'CANCELLED'}

        for km, kmi in targets:
            editor_meta.label_item_set(self.name, km, kmi, self.assign)
        _keymap_label_report(self, targets, self.name, self.assign)

        return {'FINISHED'}


class PREFERENCES_OT_keyitem_select(Operator):
    """Select this shortcut, so edits apply to the whole selection. Double-click to expand it"""
    bl_idname = "preferences.keyitem_select"
    bl_label = "Key Map Item"

    item_id: IntProperty(
        name="Item Identifier",
        description="Identifier of the item to select",
        options={'SKIP_SAVE'},
    )
    idname: StringProperty(
        name="Operator",
        description="Identifier of the operator the item runs",
        options={'SKIP_SAVE'},
    )
    use_local_expand: BoolProperty(
        name="Local Expansion",
        description="The row is in the search results, which keep their own expansion",
        default=False,
        options={'SKIP_SAVE'},
    )
    extend: BoolProperty(
        name="Extend",
        description="Select every row between the last one clicked and this one",
        default=False,
        options={'SKIP_SAVE'},
    )

    # (row key, time) of the last click, for double-click detection.
    _last_click = None

    @classmethod
    def description(cls, _context, props):
        module, _, operator = props.idname.partition(".")
        text = ""
        if module and operator:
            try:
                op = getattr(getattr(bpy.ops, module), operator)
                text = op.get_rna_type().description
            except (AttributeError, KeyError):
                text = ""
        return "{:s}\n\n{:s}".format(
            text or props.idname,
            rpt_("Click to select, shift-click to select a range, double-click to expand"),
        )

    def invoke(self, context, event):
        self.extend = event.shift
        return self.execute(context)

    def _is_double_click(self, context, km):
        import time
        cls = PREFERENCES_OT_keyitem_select
        now = time.monotonic()
        where = (km.name, km.space_type, km.region_type, self.item_id)
        within = context.preferences.inputs.mouse_double_click_time / 1000.0

        last = cls._last_click
        if (last is not None) and (last[0] == where) and ((now - last[1]) <= within):
            # Consumed, so a third click starts a new pair.
            cls._last_click = None
            return True
        cls._last_click = (where, now)
        return False

    def execute(self, context):
        import rna_keymap_ui
        km = getattr(context, "keymap", None)
        if km is None:
            return {'CANCELLED'}
        kmi = km.keymap_items.from_id(self.item_id)
        if kmi is None:
            return {'CANCELLED'}

        wm = context.window_manager
        if self.extend and rna_keymap_ui.keymap_select_range(context, km, kmi):
            # Range selection only adds and keeps the anchor.
            rna_keymap_ui.keymap_selection_changed()
            return {'FINISHED'}

        # A double-click toggles twice, leaving the selection unchanged.
        wm.keymap_selection_set(km, kmi, not wm.keymap_selection_contains(km, kmi))
        rna_keymap_ui.keymap_select_anchor_set(km, kmi)
        if self._is_double_click(context, km):
            if self.use_local_expand:
                rna_keymap_ui.keymap_filtered_expand_toggle(km.name, self.item_id)
            else:
                kmi.show_expanded = not kmi.show_expanded
        rna_keymap_ui.keymap_selection_changed()
        return {'FINISHED'}


class PREFERENCES_OT_keymap_select_all(Operator):
    """Select or deselect every shortcut shown in the key map editor"""
    bl_idname = "preferences.keymap_select_all"
    bl_label = "(De)select All Shortcuts"

    action: EnumProperty(
        name="Action",
        description="What to do to the shortcuts on show",
        items=(
            ('SELECT', "Select", "Select every listed key map item"),
            ('DESELECT', "Deselect", "Deselect every key map item"),
            ('INVERT', "Invert", "Invert the selection of the listed key map items"),
        ),
        default='SELECT',
        options={'SKIP_SAVE'},
    )

    @classmethod
    def poll(cls, context):
        import rna_keymap_ui
        if context.preferences.active_section != 'KEYMAP':
            return False
        # Also bound to a click on empty space: fail with no selection so the click passes through.
        return bool(rna_keymap_ui.keymap_selection_count())

    def execute(self, context):
        import rna_keymap_ui
        wm = context.window_manager

        if self.action == 'DESELECT':
            wm.keymap_selection_clear()
            rna_keymap_ui.keymap_selection_changed()
            return {'FINISHED'}

        rows = rna_keymap_ui.keymap_visible_items(context)
        if not rows:
            self.report({'WARNING'}, "No shortcuts are on show to select")
            return {'CANCELLED'}

        for km, kmi in rows:
            if self.action == 'SELECT':
                wm.keymap_selection_set(km, kmi, True)
            else:
                wm.keymap_selection_set(km, kmi, not wm.keymap_selection_contains(km, kmi))
        rna_keymap_ui.keymap_selection_changed()
        return {'FINISHED'}


class PREFERENCES_OT_keyitem_expand(Operator):
    """Show or hide the settings of this shortcut"""
    bl_idname = "preferences.keyitem_expand"
    bl_label = "Expand Key Map Item"

    keymap_name: StringProperty(name="Key Map", options={'SKIP_SAVE'})
    item_id: IntProperty(name="Item Identifier", default=0, options={'SKIP_SAVE'})

    def execute(self, _context):
        import rna_keymap_ui
        rna_keymap_ui.keymap_filtered_expand_toggle(self.keymap_name, self.item_id)
        return {'FINISHED'}


class PREFERENCES_OT_keymap_filter_refresh(Operator):
    """Drop the items the filter is still showing after they stopped matching"""
    bl_idname = "preferences.keymap_filter_refresh"
    bl_label = "Refresh Filtered Key Map List"

    def execute(self, context):
        import rna_keymap_ui
        rna_keymap_ui.keymap_filter_refresh()
        space = context.space_data
        if space is not None and space.type == 'PREFERENCES':
            # The tree is drawn in another region.
            for region in context.area.regions:
                region.tag_redraw()
        return {'FINISHED'}


def _keymap_hierarchy_path(entries, name):
    """Hierarchy entries from the root down to the named key map, or None."""
    for entry_name, space_type, region_type, children in entries:
        here = (entry_name, space_type, region_type)
        if entry_name == name:
            return [here]
        below = _keymap_hierarchy_path(children, name)
        if below is not None:
            return [here] + below
    return None


def _keymap_item_by_id(context, keymap_name, item_id):
    """(key map, item) by name and id, either may be None."""
    km = context.window_manager.keyconfigs.user.keymaps.get(keymap_name)
    km = km.active() if km is not None else None
    kmi = km.keymap_items.from_id(item_id) if km is not None else None
    return km, kmi


def _preferences_space(context):
    """The preferences space from the context or the first open one (a popup's context does not hold the editor)."""
    space = context.space_data
    if space is not None and space.type == 'PREFERENCES':
        return space
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'PREFERENCES':
                return area.spaces.active
    return None


def keymap_tree_expand_to(context, keymap_name):
    """
    Clear filters, collapse all key maps and expand only the named one.
    Returns the key map, or None if it does not exist or no preferences editor is open.
    """
    space = _preferences_space(context)
    if space is None:
        return None

    space.filter_text = ""
    space.use_filter_user_modified = False
    _keymap_filter_labels_clear(context)
    space.use_filter_addon = False
    space.use_filter_conflicts = False
    context.preferences.keymap.show_ui_keyconfig = False

    kc = context.window_manager.keyconfigs.user
    for km in kc.keymaps:
        akm = km.active()
        if akm is not None:
            akm.show_expanded_children = False
            akm.show_expanded_items = False

    from bl_keymap_utils import keymap_hierarchy
    path = _keymap_hierarchy_path(keymap_hierarchy.generate(), keymap_name)
    if path is None:
        # Not in the hierarchy, no parents to expand.
        km = kc.keymaps.get(keymap_name)
        if km is None:
            return None
        km = km.active()
        km.show_expanded_children = True
        km.show_expanded_items = True
        return km

    target = None
    last = len(path) - 1
    for i, (name, space_type, region_type) in enumerate(path):
        km = kc.keymaps.find(name, space_type=space_type, region_type=region_type)
        if km is None:
            continue
        km = km.active()
        km.show_expanded_children = True
        km.show_expanded_items = (i == last)
        if i == last:
            target = km
    return target


class PREFERENCES_OT_keymap_activity_reveal(Operator):
    """Show this item in the key map editor below"""
    bl_idname = "preferences.keymap_activity_reveal"
    bl_label = "Reveal Key Map Item"

    keymap_name: StringProperty(
        name="Key Map",
        description="Name of the key map that contains the item",
    )
    idname: StringProperty(
        name="Operator",
        description="Operator identifier of the item",
    )
    key_string: StringProperty(
        name="Key Binding",
        description="Key binding of the item",
    )
    is_modal: BoolProperty(
        name="Is Modal",
        description="The item is a modal key map action, which has no operator identifier",
        default=False,
    )
    propvalue: StringProperty(
        name="Property Value",
        description="Identifier of the modal action the item maps to, used instead of "
        "the operator identifier when the item is modal",
    )

    def execute(self, context):
        import rna_keymap_ui
        if not self.keymap_name:
            # Cancel before `keymap_tree_expand_to` clears the search, see `_wide_operator`.
            return {'CANCELLED'}
        target_km = keymap_tree_expand_to(context, self.keymap_name)
        if target_km is None:
            return {'CANCELLED'}

        for kmi in target_km.keymap_items:
            if kmi.to_string() != self.key_string:
                continue
            if (kmi.propvalue == self.propvalue) if self.is_modal else (kmi.idname == self.idname):
                rna_keymap_ui.set_reveal_target(target_km, kmi)
                return {'FINISHED'}

        rna_keymap_ui.scroll_to_keymap(target_km)
        return {'FINISHED'}


class PREFERENCES_OT_keymap_undo(Operator):
    """Take back the last change made to the key map"""
    bl_idname = "preferences.keymap_undo"
    bl_label = "Undo Key Map Change"

    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        if not wm.keymap_undo_len:
            cls.poll_message_set("Nothing has been changed about the key map yet")
            return False
        return True

    def execute(self, context):
        import rna_keymap_ui
        wm = context.window_manager
        if not wm.keymap_undo():
            self.report({'INFO'}, "Nothing left to take back")
            return {'CANCELLED'}
        # Undo may have removed selected items.
        wm.keymap_selection_clear()
        rna_keymap_ui.keymap_selection_changed()
        context.preferences.is_dirty = True
        return {'FINISHED'}


class PREFERENCES_OT_keymap_redo(Operator):
    """Put back the last change to the key map that was taken back"""
    bl_idname = "preferences.keymap_redo"
    bl_label = "Redo Key Map Change"

    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        if not wm.keymap_redo_len:
            cls.poll_message_set("Nothing has been taken back to put back")
            return False
        return True

    def execute(self, context):
        import rna_keymap_ui
        wm = context.window_manager
        if not wm.keymap_redo():
            self.report({'INFO'}, "Nothing left to put back")
            return {'CANCELLED'}
        wm.keymap_selection_clear()
        rna_keymap_ui.keymap_selection_changed()
        context.preferences.is_dirty = True
        return {'FINISHED'}


class PREFERENCES_OT_keymap_view_back(Operator):
    """Go back to whatever the key map editor was showing before"""
    bl_idname = "preferences.keymap_view_back"
    bl_label = "Back"

    @classmethod
    def poll(cls, context):
        import rna_keymap_ui
        space = getattr(context, "space_data", None)
        if (space is None) or (space.type != 'PREFERENCES'):
            return False
        if not rna_keymap_ui.keymap_view_history_depth():
            cls.poll_message_set("The editor has not been shown anything else yet")
            return False
        return True

    def execute(self, context):
        import rna_keymap_ui
        if not rna_keymap_ui.keymap_view_back(context):
            return {'CANCELLED'}
        return {'FINISHED'}


class PREFERENCES_OT_keymap_isolate(Operator):
    """Clear the search and show only this key map, expanded, in the tree below"""
    bl_idname = "preferences.keymap_isolate"
    bl_label = "Show Key Map in Tree"

    keymap_name: StringProperty(
        name="Key Map",
        description="Name of the key map to expand",
    )

    def execute(self, context):
        import rna_keymap_ui
        km = keymap_tree_expand_to(context, self.keymap_name)
        if km is None:
            return {'CANCELLED'}
        rna_keymap_ui.scroll_to_keymap(km)
        return {'FINISHED'}


class PREFERENCES_OT_keyitem_reveal(Operator):
    """Clear the search and show this shortcut where it lives in the full tree"""
    bl_idname = "preferences.keyitem_reveal"
    bl_label = "View in Full Tree"

    keymap_name: StringProperty(
        name="Key Map",
        description="Name of the key map that contains the item",
    )
    item_id: IntProperty(
        name="Item Identifier",
        description="Identifier of the key map item within its key map",
        default=-1,
    )

    @classmethod
    def description(cls, context, props):
        import rna_keymap_ui
        km, kmi = _keymap_item_by_id(context, props.keymap_name, props.item_id)
        if kmi is None:
            return None
        return rpt_("Show {:s} [{:s}] in {:s}, clearing the search").format(
            rna_keymap_ui.keymap_item_label(km, kmi),
            kmi.to_string() or rpt_("no key"),
            km.name,
        )

    def execute(self, context):
        import rna_keymap_ui
        km = keymap_tree_expand_to(context, self.keymap_name)
        if km is None:
            return {'CANCELLED'}
        kmi = km.keymap_items.from_id(self.item_id)
        if kmi is None:
            # The item is gone, still show the key map.
            rna_keymap_ui.scroll_to_keymap(km)
            return {'FINISHED'}
        rna_keymap_ui.set_reveal_target(km, kmi)
        return {'FINISHED'}


class PREFERENCES_OT_keyitem_flash_conflict(Operator):
    """Point out the shortcut that claims this one's key binding"""
    bl_idname = "preferences.keyitem_flash_conflict"
    bl_label = "Show Conflicting Shortcut"

    keymap_name: StringProperty(
        name="Key Map",
        description="Name of the key map that contains the item",
    )
    item_id: IntProperty(
        name="Item Identifier",
        description="Identifier of the key map item within its key map",
        default=-1,
    )
    is_outranked: BoolProperty(
        name="Answers First",
        description="Whether that key map is offered the key before the one being looked at",
        default=False,
        options={'SKIP_SAVE'},
    )
    # The row the marker was pressed on, used for a conflict check when the target row is not
    # drawn. Left empty by the Add Shortcut dialog, whose item has no row yet.
    source_keymap_name: StringProperty(
        name="From Key Map",
        description="Name of the key map holding the shortcut the marker belongs to",
        options={'SKIP_SAVE'},
    )
    source_item_id: IntProperty(
        name="From Item Identifier",
        description="Identifier of the shortcut the marker belongs to",
        default=-1,
        options={'SKIP_SAVE'},
    )

    @classmethod
    def description(cls, context, props):
        import rna_keymap_ui
        km, kmi = _keymap_item_by_id(context, props.keymap_name, props.item_id)
        if kmi is None:
            return None
        text = (
            rpt_("{:s} [{:s}] in {:s} is offered this key first, so this shortcut only runs "
                 "where that key map does not apply")
            if props.is_outranked else
            rpt_("{:s} [{:s}] in {:s} claims this key binding")
        )
        return text.format(
            rna_keymap_ui.keymap_item_label(km, kmi),
            kmi.to_string() or rpt_("no key"),
            km.name,
        )

    def execute(self, context):
        import rna_keymap_ui
        km, kmi = _keymap_item_by_id(context, self.keymap_name, self.item_id)
        if kmi is None:
            self.report({'INFO'}, "The shortcut in the way is no longer there")
            return {'CANCELLED'}

        if rna_keymap_ui.keymap_row_is_drawn(km, kmi):
            # Already drawn, flash in place.
            rna_keymap_ui.set_conflict_flash(km, kmi)
            return {'FINISHED'}

        # Not drawn (filtered or collapsed): a conflict check on the source row shows this one
        # along with the other conflicts. The flash is set for when the tree redraws.
        km_from, kmi_from = _keymap_item_by_id(
            context, self.source_keymap_name, self.source_item_id)
        if kmi_from is not None and _keymap_conflicts_check_show(context, [(km_from, kmi_from)]):
            rna_keymap_ui.set_conflict_flash(km, kmi)
            rna_keymap_ui.set_reveal_target(km, kmi)
            return {'FINISHED'}

        # No source row, expand the tree to it instead.
        if keymap_tree_expand_to(context, self.keymap_name) is None:
            return {'CANCELLED'}
        rna_keymap_ui.set_conflict_flash(km, kmi)
        rna_keymap_ui.set_reveal_target(km, kmi)
        return {'FINISHED'}


class PREFERENCES_OT_keyconfig_remove(Operator):
    """Remove key config"""
    bl_idname = "preferences.keyconfig_remove"
    bl_label = "Remove Key Config"

    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        keyconf = wm.keyconfigs.active
        return keyconf and keyconf.is_user_defined

    def execute(self, context):
        wm = context.window_manager
        keyconfig = wm.keyconfigs.active
        wm.keyconfigs.remove(keyconfig)
        return {'FINISHED'}


# -----------------------------------------------------------------------------
# Add-on Operators

class PREFERENCES_OT_addon_enable(Operator):
    """Turn on the legacy add-ons\n
No action required. The legacy addons comes with Bforartists, and are enabled by default\n
If you accidentally deactivated it, you will need to reactivate it""" # BFA
    bl_idname = "preferences.addon_enable"
    bl_label = "Enable Add-on"

    module: StringProperty(
        name="Module",
        description="Module name of the add-on to enable",
    )

    def execute(self, _context):
        import addon_utils

        err_str = ""

        def err_cb(ex):
            import traceback
            traceback.print_exc()

            # The full trace-back in the UI is unwieldy and associated with unhandled exceptions.
            # Only show a single exception instead of the full trace-back,
            # developers can debug using information printed in the console.
            nonlocal err_str
            err_str = str(ex)

        # Refreshing wheels can be slow, use the wait cursor.
        cursor_set = self.options.is_invoke
        if cursor_set:
            _wm_wait_cursor(True)

        # Ensure any wheels are setup before enabling.
        module_name = self.module

        mod = addon_utils.enable(module_name, default_set=True, handle_error=err_cb)

        if mod:
            bl_info = addon_utils.module_bl_info(mod)

            info_ver = bl_info.get("blender", (0, 0, 0))

            if info_ver > bpy.app.version:
                self.report(
                    {'WARNING'},
                    rpt_(
                        "This script was written for Blender "
                        "version {:d}.{:d}.{:d} and might not "
                        "function (correctly), "
                        "though it is enabled"
                    ).format(*info_ver)
                )
            result = {'FINISHED'}
        else:

            if err_str:
                self.report({'ERROR'}, err_str)

            result = {'CANCELLED'}

        if cursor_set:
            _wm_wait_cursor(False)

        return result


class PREFERENCES_OT_addon_disable(Operator):
    """Turn off this add-on"""
    bl_idname = "preferences.addon_disable"
    bl_label = "Disable Add-on"

    module: StringProperty(
        name="Module",
        description="Module name of the add-on to disable",
    )

    def execute(self, _context):
        import addon_utils

        err_str = ""

        def err_cb(ex):
            import traceback
            nonlocal err_str
            err_str = traceback.format_exc()
            print(err_str)

        # Refreshing wheels can be slow, use the wait cursor.
        cursor_set = self.options.is_invoke
        if cursor_set:
            _wm_wait_cursor(True)

        module_name = self.module
        addon_utils.disable(module_name, default_set=True, handle_error=err_cb)

        if err_str:
            self.report({'ERROR'}, err_str)

        if cursor_set:
            _wm_wait_cursor(False)

        return {'FINISHED'}


class PREFERENCES_OT_theme_install(Operator):
    """Load and apply a Blender XML theme file"""
    bl_idname = "preferences.theme_install"
    bl_label = "Install Theme..."

    overwrite: BoolProperty(
        name="Overwrite",
        description="Remove existing theme file if exists",
        default=True,
    )
    filepath: StringProperty(
        subtype='FILE_PATH',
    )
    filter_folder: BoolProperty(
        name="Filter folders",
        default=True,
        options={'HIDDEN'},
    )
    filter_glob: StringProperty(
        default="*.xml",
        options={'HIDDEN'},
    )

    def execute(self, _context):
        import os
        import shutil
        import traceback

        xmlfile = self.filepath

        path_themes = bpy.utils.user_resource(
            'SCRIPTS',
            path=os.path.join("presets", "interface_theme"),
            create=True,
        )

        if not path_themes:
            self.report({'ERROR'}, "Failed to get themes path")
            return {'CANCELLED'}

        path_dest = os.path.join(path_themes, os.path.basename(xmlfile))

        if not self.overwrite:
            if os.path.exists(path_dest):
                self.report({'WARNING'}, rpt_("File already installed to {!r}").format(path_dest))
                return {'CANCELLED'}

        try:
            shutil.copyfile(xmlfile, path_dest)
            bpy.ops.script.execute_preset(
                filepath=path_dest,
                menu_idname="USERPREF_MT_interface_theme_presets",
            )
        except Exception:
            traceback.print_exc()
            return {'CANCELLED'}

        return {'FINISHED'}

    def invoke(self, context, _event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class PREFERENCES_OT_addon_refresh(Operator):
    """Scan add-on directories for new modules"""
    bl_idname = "preferences.addon_refresh"
    bl_label = "Refresh"

    def execute(self, _context):
        import addon_utils

        addon_utils.modules_refresh()

        return {'FINISHED'}


# Note: shares some logic with PREFERENCES_OT_app_template_install
# but not enough to de-duplicate. Fixed here may apply to both.
class PREFERENCES_OT_addon_install(Operator):
    """Install an add-on"""
    bl_idname = "preferences.addon_install"
    bl_label = "Install Add-on"

    overwrite: BoolProperty(
        name="Overwrite",
        description="Remove existing add-ons with the same ID",
        default=True,
    )

    enable_on_install: BoolProperty(
        name="Enable on Install",
        description="Enable after installing",
        default=False,
    )

    def _target_path_items(_self, context):
        default_item = ('DEFAULT', "Default", "")
        if context is None:
            return (
                default_item,
            )

        paths = context.preferences.filepaths
        script_directories_items = [
            (item.name, item.name, "") for index, item in enumerate(paths.script_directories)
            if item.directory
        ]
        return (
            (default_item, None, *script_directories_items) if script_directories_items else
            (default_item,)
        )

    target: EnumProperty(
        name="Target Path",
        items=_target_path_items,
    )

    filepath: StringProperty(
        subtype='FILE_PATH',
    )
    filter_folder: BoolProperty(
        name="Filter folders",
        default=True,
        options={'HIDDEN'},
    )
    filter_python: BoolProperty(
        name="Filter Python",
        default=True,
        options={'HIDDEN'},
    )
    filter_glob: StringProperty(
        default="*.py;*.zip",
        options={'HIDDEN'},
    )

    def execute(self, context):
        import addon_utils
        import traceback
        import zipfile
        import shutil
        import os

        pyfile = self.filepath

        if self.target == 'DEFAULT':
            # Don't use `bpy.utils.script_paths(path="addons")` because we may not be able to write to it.
            path_addons = bpy.utils.user_resource('SCRIPTS', path="addons", create=True)
        else:
            paths = context.preferences.filepaths
            for script_directory in paths.script_directories:
                if script_directory.name == self.target:
                    path_addons = os.path.join(script_directory.directory, "addons")
                    break

        if not path_addons:
            self.report({'ERROR'}, "Failed to get add-ons path")
            return {'CANCELLED'}

        if not os.path.isdir(path_addons):
            try:
                os.makedirs(path_addons, exist_ok=True)
            except Exception:
                traceback.print_exc()

        # Check if we are installing from a target path,
        # doing so causes 2+ addons of same name or when the same from/to
        # location is used, removal of the file!
        addon_path = ""
        pyfile_dir = os.path.dirname(pyfile)
        for addon_path in addon_utils.paths():
            if os.path.samefile(pyfile_dir, addon_path):
                self.report({'ERROR'}, rpt_("Source file is in the add-on search path: {!r}").format(addon_path))
                return {'CANCELLED'}
        del addon_path
        del pyfile_dir
        # done checking for exceptional case

        addons_old = {mod.__name__ for mod in addon_utils.modules()}

        # check to see if the file is in compressed format (.zip)
        if zipfile.is_zipfile(pyfile):
            try:
                file_to_extract = zipfile.ZipFile(pyfile, "r")
            except Exception:
                traceback.print_exc()
                return {'CANCELLED'}

            file_to_extract_root = _zipfile_root_namelist(file_to_extract)

            if "__init__.py" in file_to_extract_root:
                self.report({'ERROR'}, rpt_(
                    "ZIP packaged incorrectly; __init__.py should be in a directory, not at top-level"
                ))
                return {'CANCELLED'}

            if self.overwrite:
                _module_filesystem_remove(path_addons, file_to_extract_root)
            else:
                for f in file_to_extract_root:
                    path_dest = os.path.join(path_addons, os.path.basename(f))
                    if os.path.exists(path_dest):
                        self.report({'WARNING'}, rpt_("File already installed to {!r}").format(path_dest))
                        return {'CANCELLED'}

            try:  # extract the file to "addons"
                file_to_extract.extractall(path_addons)
            except Exception:
                traceback.print_exc()
                return {'CANCELLED'}

        else:
            path_dest = os.path.join(path_addons, os.path.basename(pyfile))

            if self.overwrite:
                _module_filesystem_remove(path_addons, [os.path.basename(pyfile)])
            elif os.path.exists(path_dest):
                self.report({'WARNING'}, rpt_("File already installed to {!r}").format(path_dest))
                return {'CANCELLED'}

            # if not compressed file just copy into the addon path
            try:
                shutil.copyfile(pyfile, path_dest)
            except Exception:
                traceback.print_exc()
                return {'CANCELLED'}

        addons_new = {mod.__name__ for mod in addon_utils.modules()} - addons_old
        addons_new.discard("modules")

        # disable any addons we may have enabled previously and removed.
        # this is unlikely but do just in case. bug #23978.
        for new_addon in addons_new:
            addon_utils.disable(new_addon, default_set=True)

        # possible the zip contains multiple addons, we could disallow this
        # but for now just use the first
        for mod in addon_utils.modules(refresh=False):
            if mod.__name__ in addons_new:
                bl_info = addon_utils.module_bl_info(mod)

                # show the newly installed addon.
                context.preferences.view.show_addons_enabled_only = False
                context.window_manager.addon_filter = 'All'
                context.window_manager.addon_search = bl_info["name"]
                break

        # in case a new module path was created to install this addon.
        bpy.utils.refresh_script_paths()

        # Auto enable if needed.
        if self.enable_on_install:
            for mod in addon_utils.modules(refresh=False):
                if mod.__name__ in addons_new:
                    bpy.ops.preferences.addon_enable(module=mod.__name__)

        # print message
        msg = rpt_("Modules Installed ({:s}) from {!r} into {!r}").format(
            ", ".join(sorted(addons_new)), pyfile, path_addons,
        )

        print(msg)
        self.report({'INFO'}, msg)

        return {'FINISHED'}

    def invoke(self, context, _event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class PREFERENCES_OT_addon_remove(Operator):
    """Delete the add-on from the file system"""
    bl_idname = "preferences.addon_remove"
    bl_label = "Remove Add-on"

    module: StringProperty(
        name="Module",
        description="Module name of the add-on to remove",
    )

    @staticmethod
    def path_from_addon(module):
        import os
        import addon_utils

        for mod in addon_utils.modules():
            if mod.__name__ == module:
                filepath = mod.__file__
                if os.path.exists(filepath):
                    if os.path.splitext(os.path.basename(filepath))[0] == "__init__":
                        return os.path.dirname(filepath), True
                    else:
                        return filepath, False
        return None, False

    def execute(self, context):
        import addon_utils
        import os

        path, isdir = PREFERENCES_OT_addon_remove.path_from_addon(self.module)
        if path is None:
            self.report({'WARNING'}, rpt_("Add-on path {!r} could not be found").format(path))
            return {'CANCELLED'}

        # in case its enabled
        addon_utils.disable(self.module, default_set=True)

        import shutil
        if isdir and (not os.path.islink(path)):
            shutil.rmtree(path, ignore_errors=True)
        else:
            try:
                os.remove(path)
            except Exception:
                pass

        if os.path.exists(path):
            addon_utils.stale_pending_stage_paths(os.path.dirname(path), [path])

        addon_utils.modules_refresh()

        context.area.tag_redraw()
        return {'FINISHED'}

    # lame confirmation check
    def draw(self, _context):
        self.layout.label(text=iface_("Remove Add-on: {!r}?").format(self.module), translate=False)
        path, _isdir = PREFERENCES_OT_addon_remove.path_from_addon(self.module)
        self.layout.label(text=iface_("Path: {!r}").format(path), translate=False)

    def invoke(self, context, _event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=600)


class PREFERENCES_OT_addon_expand(Operator):
    """Display information and preferences for this add-on"""
    bl_idname = "preferences.addon_expand"
    bl_label = ""
    bl_options = {'INTERNAL'}

    module: StringProperty(
        name="Module",
        description="Module name of the add-on to expand",
    )

    def execute(self, _context):
        import addon_utils

        addon_module_name = self.module

        # Ensure `addons_fake_modules` is set.
        _modules = addon_utils.modules(refresh=False)
        mod = addon_utils.addons_fake_modules.get(addon_module_name)
        if mod is not None:
            bl_info = addon_utils.module_bl_info(mod)
            bl_info["show_expanded"] = not bl_info["show_expanded"]

        return {'FINISHED'}


class PREFERENCES_OT_addon_show(Operator):
    """Show add-on preferences"""
    bl_idname = "preferences.addon_show"
    bl_label = ""
    bl_options = {'INTERNAL'}

    module: StringProperty(
        name="Module",
        description="Module name of the add-on to expand",
    )

    def execute(self, context):
        import addon_utils

        addon_module_name = self.module

        # Ensure `addons_fake_modules` is set.
        _modules = addon_utils.modules(refresh=False)
        mod = addon_utils.addons_fake_modules.get(addon_module_name)
        if mod is not None:
            bl_info = addon_utils.module_bl_info(mod)
            bl_info["show_expanded"] = True

            context.preferences.active_section = 'ADDONS'
            context.preferences.view.show_addons_enabled_only = False
            context.window_manager.addon_filter = 'All'
            context.window_manager.addon_search = bl_info["name"]

            # No need to show the editor if it is already visible in the main window.
            if 'PREFERENCES' not in (area.type for area in context.screen.areas):
                bpy.ops.screen.userpref_show('INVOKE_DEFAULT')

        return {'FINISHED'}


# Note: shares some logic with PREFERENCES_OT_addon_install
# but not enough to de-duplicate. Fixes here may apply to both.
class PREFERENCES_OT_app_template_install(Operator):
    """Install an application template"""
    bl_idname = "preferences.app_template_install"
    bl_label = "Install Template from File..."

    overwrite: BoolProperty(
        name="Overwrite",
        description="Remove existing template with the same ID",
        default=True,
    )

    filepath: StringProperty(
        subtype='FILE_PATH',
    )
    filter_folder: BoolProperty(
        name="Filter folders",
        default=True,
        options={'HIDDEN'},
    )
    filter_glob: StringProperty(
        default="*.zip",
        options={'HIDDEN'},
    )

    def execute(self, _context):
        import traceback
        import zipfile
        import os

        filepath = self.filepath

        path_app_templates = bpy.utils.user_resource(
            'SCRIPTS',
            path=os.path.join("startup", "bl_app_templates_user"),
            create=True,
        )

        if not path_app_templates:
            self.report({'ERROR'}, "Failed to get add-ons path")
            return {'CANCELLED'}

        if not os.path.isdir(path_app_templates):
            try:
                os.makedirs(path_app_templates, exist_ok=True)
            except Exception:
                traceback.print_exc()

        app_templates_old = set(os.listdir(path_app_templates))

        # check to see if the file is in compressed format (.zip)
        if zipfile.is_zipfile(filepath):
            try:
                file_to_extract = zipfile.ZipFile(filepath, "r")
            except Exception:
                traceback.print_exc()
                return {'CANCELLED'}

            file_to_extract_root = _zipfile_root_namelist(file_to_extract)
            if self.overwrite:
                _module_filesystem_remove(path_app_templates, file_to_extract_root)
            else:
                for f in file_to_extract_root:
                    path_dest = os.path.join(path_app_templates, os.path.basename(f))
                    if os.path.exists(path_dest):
                        self.report({'WARNING'}, rpt_("File already installed to {!r}").format(path_dest))
                        return {'CANCELLED'}

            try:  # extract the file to "bl_app_templates_user"
                file_to_extract.extractall(path_app_templates)
            except Exception:
                traceback.print_exc()
                return {'CANCELLED'}

        else:
            # Only support installing zip-files.
            self.report({'WARNING'}, rpt_("Expected a zip-file {!r}").format(filepath))
            return {'CANCELLED'}

        app_templates_new = set(os.listdir(path_app_templates)) - app_templates_old

        # in case a new module path was created to install this addon.
        bpy.utils.refresh_script_paths()

        # print message
        msg = rpt_("Template Installed ({:s}) from {!r} into {!r}").format(
            ", ".join(sorted(app_templates_new)),
            filepath,
            path_app_templates,
        )

        print(msg)
        self.report({'INFO'}, msg)

        return {'FINISHED'}

    def invoke(self, context, _event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


# -----------------------------------------------------------------------------
# Studio Light Operations

class PREFERENCES_OT_studiolight_install(Operator):
    """Install a user defined light"""
    bl_idname = "preferences.studiolight_install"
    bl_label = "Install Light"

    def update_type(self, context):
        filter_glob = "*.sl" if self.type == 'STUDIO' else "*.png;*.jpg;*.hdr;*.exr"
        if filter_glob == self.filter_glob:
            return

        self.filter_glob = filter_glob

        space_data = context.space_data
        if space_data is not None and space_data.type == 'FILE_BROWSER':
            space_data.params.filter_glob = filter_glob

    files: CollectionProperty(
        name="File Path",
        type=OperatorFileListElement,
    )
    directory: StringProperty(
        subtype='DIR_PATH',
    )
    filter_folder: BoolProperty(
        name="Filter Folders",
        default=True,
        options={'HIDDEN'},
    )
    filter_glob: StringProperty(
        default="*.png;*.jpg;*.hdr;*.exr",
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    type: EnumProperty(
        name="Type",
        items=(
            ('MATCAP', "MatCap", "Install custom MatCaps"),
            ('WORLD', "World", "Install custom HDRIs"),
            ('STUDIO', "Studio", "Install custom Studio Lights"),
        ),
        update=update_type,
    )

    def execute(self, context):
        import os
        import shutil
        prefs = context.preferences

        path_studiolights = os.path.join("studiolights", self.type.lower())
        path_studiolights = bpy.utils.user_resource('DATAFILES', path=path_studiolights, create=True)
        if not path_studiolights:
            self.report({'ERROR'}, "Failed to create Studio Light path")
            return {'CANCELLED'}

        installed = 0

        for e in self.files:
            filepath = os.path.join(self.directory, e.name)

            try:
                shutil.copy(filepath, path_studiolights)
            except Exception as ex:
                msg = rpt_("Unable to copy {!r}: {:s}").format(e.name, str(ex))
                print(msg)
                self.report({'WARNING'}, msg)
                continue

            prefs.studio_lights.load(os.path.join(path_studiolights, e.name), self.type)
            installed += 1

        if installed == 0:
            return {'CANCELLED'}

        # print message
        msg = rpt_("StudioLight Installed {!r} into {!r}").format(
            ", ".join(e.name for e in self.files),
            path_studiolights,
        )
        print(msg)
        self.report({'INFO'}, msg)
        return {'FINISHED'}

    def invoke(self, context, _event):
        wm = context.window_manager

        if self.type == 'STUDIO':
            self.filter_glob = "*.sl"

        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class PREFERENCES_OT_studiolight_new(Operator):
    """Save custom studio light from the studio light editor settings"""
    bl_idname = "preferences.studiolight_new"
    bl_label = "Save Custom Studio Light"

    filename: StringProperty(
        name="Name",
        default="StudioLight",
        subtype='FILE_NAME',
    )

    ask_override = False

    def execute(self, context):
        import os
        prefs = context.preferences
        wm = context.window_manager
        filename = bpy.path.ensure_ext(self.filename, ".sl")

        path_studiolights = bpy.utils.user_resource(
            'DATAFILES',
            path=os.path.join("studiolights", "studio"),
            create=True,
        )
        if not path_studiolights:
            self.report({'ERROR'}, "Failed to get Studio Light path")
            return {'CANCELLED'}

        filepath_final = os.path.join(path_studiolights, filename)
        if os.path.isfile(filepath_final):
            if not self.ask_override:
                self.ask_override = True
                return wm.invoke_props_dialog(self, width=320)
            else:
                for studio_light in prefs.studio_lights:
                    if studio_light.name == filename:
                        bpy.ops.preferences.studiolight_uninstall(index=studio_light.index)

        prefs.studio_lights.new(path=filepath_final)

        # print message
        msg = rpt_("StudioLight Installed {!r} into {!r}").format(self.filename, str(path_studiolights))
        print(msg)
        self.report({'INFO'}, msg)
        return {'FINISHED'}

    def draw(self, _context):
        layout = self.layout
        if self.ask_override:
            layout.label(text="Warning, file already exists. Overwrite existing file?")
        else:
            layout.prop(self, "filename")

    def invoke(self, context, _event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=320)


class PREFERENCES_OT_studiolight_uninstall(Operator):
    """Delete Studio Light"""
    bl_idname = "preferences.studiolight_uninstall"
    bl_label = "Uninstall Studio Light"
    index: IntProperty()

    def execute(self, context):
        import os
        prefs = context.preferences
        for studio_light in prefs.studio_lights:
            if studio_light.index == self.index:
                filepath = studio_light.path
                if filepath and os.path.exists(filepath):
                    os.unlink(filepath)
                prefs.studio_lights.remove(studio_light)
                return {'FINISHED'}
        return {'CANCELLED'}


class PREFERENCES_OT_studiolight_copy_settings(Operator):
    """Copy Studio Light settings to the Studio Light editor"""
    bl_idname = "preferences.studiolight_copy_settings"
    bl_label = "Copy Studio Light Settings"
    index: IntProperty()

    def execute(self, context):
        prefs = context.preferences
        system = prefs.system
        for studio_light in prefs.studio_lights:
            if studio_light.index == self.index:
                system.light_ambient = studio_light.light_ambient
                for sys_light, light in zip(system.solid_lights, studio_light.solid_lights):
                    sys_light.use = light.use
                    sys_light.diffuse_color = light.diffuse_color
                    sys_light.specular_color = light.specular_color
                    sys_light.smooth = light.smooth
                    sys_light.direction = light.direction
                return {'FINISHED'}
        return {'CANCELLED'}

# BFA
class PREFERENCES_OT_studiolight_show(Operator):
    """Show light preferences"""
    bl_idname = "preferences.studiolight_show"
    bl_label = ""
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, _context):
        return bpy.ops.screen.userpref_show.poll()

    def execute(self, context):
        context.preferences.active_section = 'LIGHTS'
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        return {'FINISHED'}


class PREFERENCES_OT_script_directory_new(Operator):
    bl_idname = "preferences.script_directory_add"
    bl_label = "Add Python Script Directory"

    directory: StringProperty(
        subtype='DIR_PATH',
    )
    filter_folder: BoolProperty(
        name="Filter Folders",
        default=True,
        options={'HIDDEN'},
    )

    def execute(self, context):
        import os

        script_directories = context.preferences.filepaths.script_directories

        new_dir = script_directories.new()
        # Assign path selected via file browser.
        new_dir.directory = self.directory
        new_dir.name = os.path.basename(self.directory.rstrip(os.sep))

        assert context.preferences.is_dirty is True

        return {'FINISHED'}

    def invoke(self, context, _event):
        wm = context.window_manager

        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class PREFERENCES_OT_script_directory_remove(Operator):
    bl_idname = "preferences.script_directory_remove"
    bl_label = "Remove Python Script Directory"

    index: IntProperty(
        name="Index",
        description="Index of the script directory to remove",
    )

    def execute(self, context):
        script_directories = context.preferences.filepaths.script_directories
        for search_index, script_directory in enumerate(script_directories):
            if search_index == self.index:
                script_directories.remove(script_directory)
                break

        assert context.preferences.is_dirty is True

        return {'FINISHED'}

# BFA
class PREFERENCES_OT_filepaths_show(Operator):
    """Show, edit and add file paths to Asset Libraries\nThis button opens the Preferences"""
    bl_idname = "preferences.filepaths_show"
    bl_label = ""
    bl_options = {'INTERNAL'}

    def execute(self, context):
        context.preferences.active_section = 'ASSETS'
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        return {'FINISHED'}


classes = (
    PREFERENCES_OT_addon_disable,
    PREFERENCES_OT_addon_enable,
    PREFERENCES_OT_addon_expand,
    PREFERENCES_OT_addon_install,
    PREFERENCES_OT_addon_refresh,
    PREFERENCES_OT_addon_remove,
    PREFERENCES_OT_addon_show,
    PREFERENCES_OT_app_template_install,
    PREFERENCES_OT_copy_prev,
    PREFERENCES_OT_keyconfig_activate,
    PREFERENCES_OT_keyconfig_export,
    PREFERENCES_OT_keyconfig_import,
    PREFERENCES_OT_keyconfig_remove,
    PREFERENCES_OT_keyconfig_test,
    PREFERENCES_OT_keyitem_add,
    PREFERENCES_OT_keyitem_intent_detach,
    PREFERENCES_OT_keyintent_category_toggle,
    PREFERENCES_OT_keyintent_restore,
    PREFERENCES_OT_keyintent_reveal,
    PREFERENCES_OT_keyitem_copy,
    PREFERENCES_OT_keyitem_paste,
    PREFERENCES_OT_keyitem_remove,
    PREFERENCES_OT_keyitem_restore,
    PREFERENCES_OT_keyitem_unshadow,
    PREFERENCES_OT_keymap_activity_clear,
    PREFERENCES_OT_keymap_activity_find,
    PREFERENCES_OT_keymap_conflicts_check,
    PREFERENCES_OT_keyitem_select,
    PREFERENCES_OT_keymap_select_all,
    PREFERENCES_OT_keymap_label_new,
    PREFERENCES_OT_keymap_label_remove,
    PREFERENCES_OT_keymap_label_filter_toggle,
    PREFERENCES_OT_keymap_label_assign,
    PREFERENCES_OT_keyitem_rename,
    PREFERENCES_OT_keyitem_add_for_operator,
    PREFERENCES_OT_keymap_hide_item,
    PREFERENCES_OT_keymap_hide_operator,
    PREFERENCES_OT_keyitem_expand,
    PREFERENCES_OT_keymap_filter_refresh,
    PREFERENCES_OT_keymap_activity_reveal,
    PREFERENCES_OT_keymap_undo,
    PREFERENCES_OT_keymap_redo,
    PREFERENCES_OT_keymap_view_back,
    PREFERENCES_OT_keymap_isolate,
    PREFERENCES_OT_keyitem_reveal,
    PREFERENCES_OT_keyitem_flash_conflict,
    PREFERENCES_OT_keymap_restore,
    PREFERENCES_OT_theme_install,
    PREFERENCES_OT_studiolight_install,
    PREFERENCES_OT_studiolight_new,
    PREFERENCES_OT_studiolight_uninstall,
    PREFERENCES_OT_studiolight_copy_settings,
    PREFERENCES_OT_studiolight_show, # BFA
    PREFERENCES_OT_filepaths_show, # BFA
    PREFERENCES_OT_script_directory_new,
    PREFERENCES_OT_script_directory_remove,
)
