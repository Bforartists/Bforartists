# SPDX-FileCopyrightText: 2015 Pratik Solanki (Draguu)
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os

import bpy
from bl_operators.presets import AddPresetBase
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import StringProperty
from bpy.types import (
        Menu,
        Operator,
        )


# Single source of truth for every exposed socket: reset, presets, UI and
# tests all iterate this. Rows are (node, collection, index, default,
# section, label), in UI order. index may be (socket, component) to target
# one component of a vector socket.
SKY_DEFAULTS = (
    ("Scene_Brightness", "inputs", 1, 1.0, "Background", "Strength"),
    ("Sky_HDRI_blend", "inputs", 0, 0.0, "Background", "HDRI blend"),
    ("HDRI_rotation", "inputs", (2, 2), 0.0, "Background", "Rotation"),
    ("Clouds_over_HDRI", "inputs", 0, 0.0, "Background", "Clouds over HDRI"),
    ("Shadow_color_saturation", "inputs", 1, 1.0, "Atmosphere", "Shadow color saturation"),
    ("Sky_and_Horizon_colors", "inputs", 1, (0.434, 0.838, 1.0, 1.0), "Atmosphere", "Sky color"),
    ("Sky_and_Horizon_colors", "inputs", 2, (0.962, 0.822, 0.822, 1.0), "Atmosphere", "Horizon Color"),
    ("Horizon_height", "inputs", 1, 0.0, "Atmosphere", "Horizon height"),
    # Sun direction: the Normal node's draggable ball is its output socket
    ("Sky_normal", "outputs", 0, (0.0, 0.0, 1.0), "Sun", ""),
    ("Sun_color", "inputs", 1, (0.5, 0.5, 0.5, 1.0), "Sun", ""),
    ("Sun_value", "inputs", 1, 1.0, "Sun", "Strength"),
    ("Soft_hard", "inputs", 0, 1.0, "Sun", "Soft hard"),
    ("Sun_temperature", "inputs", 0, 5500.0, "Sun", "Temperature"),
    ("Sun_temperature_mix", "inputs", 0, 0.0, "Sun", "Temperature strength"),
    ("Cloud_color", "inputs", 1, (1.0, 1.0, 1.0, 1.0), "Clouds", "Cloud color"),
    ("Cloud_opacity", "inputs", 0, 1.0, "Clouds", "Cloud opacity"),
    ("Cloud_density", "inputs", 0, 0.267, "Clouds", "Cloud density"),
    ("Cloud_coverage", "inputs", 1, 0.0, "Clouds", "Cloud coverage"),
    ("Cloud_softness", "inputs", 1, 1.0, "Clouds", "Cloud softness"),
    ("Cloud_mapping", "inputs", 3, (1.5, 1.5, 6.0), "Clouds", "Cloud scale"),
    ("Cloud_mapping", "inputs", (1, 2), 0.0, "Clouds", "Cloud altitude"),
    ("Cloud_mapping", "inputs", (2, 2), 0.0, "Clouds", "Drift direction"),
    # 0.5 is the Math-node input default old worlds have always rendered with
    ("Cloud_drift", "inputs", 0, 0.5, "Clouds", "Cloud drift"),
    ("Stars_opacity", "inputs", 0, 0.0, "Night", "Stars opacity"),
    ("Stars_texture", "inputs", 2, 30.0, "Night", "Stars density"),
    ("Star_size_variation", "inputs", 1, 0.0, "Night", "Star size variation"),
    ("Moon_opacity", "inputs", 0, 0.0, "Night", "Moon opacity"),
    ("Moon_color", "inputs", 2, (1.0, 1.0, 1.0, 1.0), "Night", "Moon color"),
    ("Moon_normal", "outputs", 0, (0.0, 0.0, 1.0), "Night", ""),
)


def sky_index(index):
    # (socket, component) rows target one component of a vector socket
    return index if isinstance(index, tuple) else (index, None)


def sky_get(nodes, name, collection, index):
    i, sub = sky_index(index)
    value = getattr(nodes[name], collection)[i].default_value
    return value if sub is None else value[sub]


def sky_set(nodes, name, collection, index, value):
    i, sub = sky_index(index)
    socket = getattr(nodes[name], collection)[i]
    if sub is None:
        socket.default_value = value
    else:
        socket.default_value[sub] = value


def sky_key(name, collection, index):
    i, sub = sky_index(index)
    key = "{:s}.{:s}.{:d}".format(name, collection, i)
    return key if sub is None else "{:s}.{:d}".format(key, sub)


def sky_rna_path(name, collection, index):
    i, sub = sky_index(index)
    path = 'nodes["{:s}"].{:s}[{:d}].default_value'.format(name, collection, i)
    return path if sub is None else "{:s}[{:d}]".format(path, sub)


def reset_sky_defaults(nodes):
    for name, collection, index, value, *_ in SKY_DEFAULTS:
        sky_set(nodes, name, collection, index, value)


def is_bundled_preset(filepath):
    # Bundled presets live in the extension's own presets/ dir: read-only in
    # practice, and any edit would be lost on update
    import os
    bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets")
    return filepath.startswith(bundled + os.sep)


def bundled_active():
    # A bundled preset is a locked template: while one is active the value
    # panels gray out and save/delete/reset are unavailable
    path = DYNSKY_OT_preset_save.active_preset_path()
    return path is not None and is_bundled_preset(path)


# Curated tile order for the preset grid; user presets follow alphabetically
BUNDLED_ORDER = ("dawn", "noon", "golden", "sunset", "dusk", "overcast", "storm", "night")


def preset_files():
    # [(display_name, filepath)] for the grid: bundled first in curated
    # order, then the user's own A-Z
    import os
    bundled, user = [], []
    for directory in bpy.utils.preset_paths("dynamic_sky"):
        if not os.path.isdir(directory):
            continue
        for fn in sorted(os.listdir(directory)):
            if not fn.endswith(".py"):
                continue
            path = os.path.join(directory, fn)
            entry = (bpy.path.display_name(fn), path)
            (bundled if is_bundled_preset(path) else user).append(entry)

    def curated(entry):
        stem = os.path.splitext(os.path.basename(entry[1]))[0]
        return (BUNDLED_ORDER.index(stem) if stem in BUNDLED_ORDER
                else len(BUNDLED_ORDER))
    bundled.sort(key=curated)
    user.sort(key=lambda entry: entry[0].lower())
    return bundled + user


# One lazy previews collection for all preset thumbnails, keyed by PNG path
_thumbs = None


# Static thumbnail for the "New" grid card (dashed border + plus); lives
# outside the scanned preset dir so it can never clash with a preset name
NEW_TILE = os.path.join(os.path.dirname(__file__), "presets", "new_tile.png")


def thumb_path(preset_path):
    return os.path.splitext(preset_path)[0] + ".png"


def round_thumb(png_path, radius=16):
    # Bake rounded corners into the PNG's alpha: UILayout can't round
    # widgets, so the tile look is carried by the image itself. Multiplying
    # alpha keeps it (near-)idempotent for already-rounded files.
    img = bpy.data.images.load(png_path)
    try:
        w, h = img.size
        px = [0.0] * w * h * 4
        img.pixels.foreach_get(px)
        for y in range(h):
            for x in range(w):
                # Signed distance to a rounded rect covering the image,
                # with a 1px soft edge so the corners aren't jagged
                dx = max(abs(x + 0.5 - w / 2) - (w / 2 - radius), 0.0)
                dy = max(abs(y + 0.5 - h / 2) - (h / 2 - radius), 0.0)
                a = min(max(radius + 0.5 - (dx * dx + dy * dy) ** 0.5, 0.0), 1.0)
                if a < 1.0:
                    px[(y * w + x) * 4 + 3] *= a
        img.pixels.foreach_set(px)
        img.filepath_raw = png_path
        img.file_format = 'PNG'
        img.save()
    finally:
        bpy.data.images.remove(img)


def thumb_icon_id(preset_path):
    # 0 = no thumbnail (caption-only tile); PNGs load lazily during draw
    import os
    global _thumbs
    png = thumb_path(preset_path)
    if not os.path.exists(png):
        return 0
    if _thumbs is None:
        import bpy.utils.previews
        _thumbs = bpy.utils.previews.new()
    if png not in _thumbs:
        _thumbs.load(png, png, 'IMAGE')
    return _thumbs[png].icon_id


def refresh_thumbs():
    # Drop cached previews; they reload lazily on the next draw
    if _thumbs is not None:
        _thumbs.clear()


def clear_thumbs():
    global _thumbs
    if _thumbs is not None:
        import bpy.utils.previews
        bpy.utils.previews.remove(_thumbs)
        _thumbs = None


def update_thumbnail(context, preset_path):
    # Best-effort: a failed render just means a caption-only tile
    from .sky import check_cycles, render_world_to_file
    if not check_cycles():
        return  # ponytail: Eevee-only users get captions, no tile images
    try:
        render_world_to_file(context.scene.world, thumb_path(preset_path), 128, 128)
        round_thumb(thumb_path(preset_path))
    except Exception as e:
        print("[Dynamic Sky] thumbnail render failed: {}".format(e))
        return
    refresh_thumbs()


def sky_world_ok(context):
    world = context.scene.world
    return world and world.node_tree and "Sky_normal" in world.node_tree.nodes


def sky_socket_values(nodes):
    # Current values of all user-facing sockets, keyed "Node.collection.index"
    # (".component" appended for vector-component rows)
    values = {}
    for name, collection, index, *_ in SKY_DEFAULTS:
        value = sky_get(nodes, name, collection, index)
        try:
            value = list(value)
        except TypeError:
            value = float(value)
        values[sky_key(name, collection, index)] = value
    return values


def apply_sky_values(nodes, values):
    for name, collection, index, *_ in SKY_DEFAULTS:
        sky_set(nodes, name, collection, index,
                values[sky_key(name, collection, index)])


# Socket values as of the last preset apply/save; lets a preset switch
# tell real edits from an untouched preset, so autosave only writes dirty
_active_values = None


def note_active_values(context):
    global _active_values
    _active_values = (sky_socket_values(context.scene.world.node_tree.nodes)
                      if sky_world_ok(context) else None)


def autosave_active(context):
    # Document model: unsaved edits on a user preset are saved before
    # anything replaces them (applying another preset, New, JSON import)
    path = DYNSKY_OT_preset_save.active_preset_path()
    if path is None or is_bundled_preset(path) or not sky_world_ok(context):
        return
    values = sky_socket_values(context.scene.world.node_tree.nodes)
    if values == _active_values:
        return
    write_preset_file(path, values)
    update_thumbnail(context, path)


def write_preset_file(filepath, values):
    # The same format AddPresetBase writes, so execute_preset can run it
    import os
    import importlib.util
    with open(filepath, "w", encoding="utf-8") as file_preset:
        file_preset.write("import bpy\n")
        file_preset.write("nodes = bpy.context.scene.world.node_tree.nodes\n\n")
        for name, collection, index, *_ in SKY_DEFAULTS:
            file_preset.write('{:s} = {!r}\n'.format(
                sky_rna_path(name, collection, index),
                values[sky_key(name, collection, index)]))
    try:
        # execute_preset imports the file, and the import machinery can serve
        # stale cached bytecode when size and mtime are unchanged
        os.remove(importlib.util.cache_from_source(filepath))
    except OSError:
        pass


class DYNSKY_OT_sky_reset(Operator):
    bl_idname = "dynsky.sky_reset"
    bl_label = "Reset Sky Settings"
    bl_description = "Set all sky settings back to their default values"

    @classmethod
    def poll(cls, context):
        return sky_world_ok(context) and not bundled_active()

    def execute(self, context):
        from .sky import sync_background_mode
        reset_sky_defaults(context.scene.world.node_tree.nodes)
        sync_background_mode(context.scene.world)
        return {'FINISHED'}


class DYNSKY_MT_presets(Menu):
    bl_label = "Sky Presets"
    preset_subdir = "dynamic_sky"
    # Through our own operator so the stored background mode gets synced
    preset_operator = "dynsky.preset_apply"

    def draw(self, context):
        Menu.draw_preset(self, context)
        layout = self.layout
        layout.separator()
        # draw_preset switches the operator context; the file browser needs invoke
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("dynsky.preset_import", text="Import from JSON...", icon='IMPORT')
        layout.operator("dynsky.preset_export", text="Export Current to JSON...", icon='EXPORT')


class DYNSKY_OT_preset_add(AddPresetBase, Operator):
    bl_idname = "dynsky.preset_add"
    bl_label = "New Dynamic Sky Preset"
    bl_description = "Add a new preset starting from the default sky values"
    preset_menu = "DYNSKY_MT_presets"
    preset_subdir = "dynamic_sky"
    preset_defines = ["nodes = bpy.context.scene.world.node_tree.nodes"]
    preset_values = [
        sky_rna_path(name, collection, index)
        for name, collection, index, *_ in SKY_DEFAULTS
    ]

    @staticmethod
    def preset_exists(filename):
        # Case-insensitive: filenames keep typed case but menu labels are
        # title-cased, so "dfg" and "Dfg" would look identical to the user
        import os
        target = filename.lower() + ".py"
        for directory in bpy.utils.preset_paths("dynamic_sky"):
            for fn in os.listdir(directory):
                if fn.lower() == target:
                    return True
        return False

    @classmethod
    def unique_name(cls, base):
        # Auto-number taken names (dfg -> dfg_1) instead of refusing
        if not cls.preset_exists(base):
            return base
        suffix = 1
        while cls.preset_exists("{:s}_{:d}".format(base, suffix)):
            suffix += 1
        return "{:s}_{:d}".format(base, suffix)

    def execute(self, context):
        adding = self.name.strip() and not (self.remove_name or self.remove_active)
        if adding:
            self.name = self.unique_name(self.as_filename(self.name.strip()))
            autosave_active(context)
            # A new preset starts from the default sky, not from the current look
            from .sky import sync_background_mode
            reset_sky_defaults(context.scene.world.node_tree.nodes)
            sync_background_mode(context.scene.world)
        result = AddPresetBase.execute(self, context)
        if adding and 'FINISHED' in result:
            path = bpy.utils.preset_find(self.name, "dynamic_sky")
            if path:
                update_thumbnail(context, path)
            note_active_values(context)
        return result


class DYNSKY_OT_preset_apply(Operator):
    bl_idname = "dynsky.preset_apply"
    bl_label = "Apply Sky Preset"
    bl_description = "Apply this sky preset"

    filepath: StringProperty(options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return sky_world_ok(context)

    def execute(self, context):
        from .sky import sync_background_mode
        autosave_active(context)
        result = bpy.ops.script.execute_preset(
            filepath=self.filepath, menu_idname="DYNSKY_MT_presets")
        if sky_world_ok(context):
            sync_background_mode(context.scene.world)
        if 'FINISHED' in result:
            note_active_values(context)
        return result


class DYNSKY_OT_preset_save(Operator):
    bl_idname = "dynsky.preset_save"
    bl_label = "Save Dynamic Sky Preset"
    bl_description = "Overwrite the active preset with the current settings"

    @staticmethod
    def active_preset_path():
        # The menu label holds the active preset's display name ("Sky Presets" =
        # none active, "Presets" = just removed). Compare case-insensitively:
        # the label is title-cased, so it never matches lowercase filenames exactly.
        import os
        label = DYNSKY_MT_presets.bl_label.lower()
        if label in {"sky presets", "presets"}:
            return None
        for directory in bpy.utils.preset_paths("dynamic_sky"):
            for fn in os.listdir(directory):
                if fn.endswith(".py") and bpy.path.display_name(fn).lower() == label:
                    return os.path.join(directory, fn)
        return None

    @classmethod
    def poll(cls, context):
        path = cls.active_preset_path()
        return (sky_world_ok(context) and path is not None
                and not is_bundled_preset(path))

    def execute(self, context):
        # AddPresetBase refuses to overwrite an existing preset file,
        # so write the same format it writes ourselves
        filepath = self.active_preset_path()
        if filepath is None:
            self.report({'WARNING'}, "No active preset to save")
            return {'CANCELLED'}
        if is_bundled_preset(filepath):
            self.report({'WARNING'},
                        "Bundled presets can't be overwritten; add a new preset instead")
            return {'CANCELLED'}
        write_preset_file(filepath, sky_socket_values(context.scene.world.node_tree.nodes))
        update_thumbnail(context, filepath)
        note_active_values(context)
        self.report({'INFO'}, "Saved preset \"{:s}\"".format(DYNSKY_MT_presets.bl_label))
        return {'FINISHED'}


class DYNSKY_OT_preset_delete(Operator):
    bl_idname = "dynsky.preset_delete"
    bl_label = "Delete Dynamic Sky Preset"
    bl_description = "Delete the current preset"

    @classmethod
    def poll(cls, context):
        path = DYNSKY_OT_preset_save.active_preset_path()
        return path is not None and not is_bundled_preset(path)

    def execute(self, context):
        # Not AddPresetBase's remove: its lookup title-cases the name and
        # silently misses lowercase preset files
        import os
        import importlib.util
        filepath = DYNSKY_OT_preset_save.active_preset_path()
        if filepath is None:
            return {'CANCELLED'}
        if is_bundled_preset(filepath):
            self.report({'WARNING'}, "Bundled presets can't be deleted")
            return {'CANCELLED'}
        try:
            os.remove(filepath)
        except OSError as ex:
            self.report({'ERROR'}, "Unable to delete preset: {!r}".format(ex))
            return {'CANCELLED'}
        try:
            os.remove(importlib.util.cache_from_source(filepath))
        except OSError:
            pass
        try:
            os.remove(thumb_path(filepath))
        except OSError:
            pass
        refresh_thumbs()
        self.report({'INFO'}, "Deleted preset \"{:s}\"".format(DYNSKY_MT_presets.bl_label))
        DYNSKY_MT_presets.bl_label = "Sky Presets"
        return {'FINISHED'}


class DYNSKY_OT_preset_duplicate(Operator):
    bl_idname = "dynsky.preset_duplicate"
    bl_label = "Duplicate Dynamic Sky Preset"
    bl_description = ("Create an editable copy of the active preset\n"
                      "from the current settings")

    name: StringProperty(name="Name", options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return (sky_world_ok(context)
                and DYNSKY_OT_preset_save.active_preset_path() is not None)

    def invoke(self, context, event):
        self.name = "{:s} Copy".format(DYNSKY_MT_presets.bl_label)
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # Same flow as the JSON import, minus the parsing: current socket
        # values become a new user preset, which becomes the active one
        import os
        preset_name = DYNSKY_OT_preset_add.as_filename(self.name.strip())
        if not preset_name:
            self.report({'WARNING'}, "No preset name given")
            return {'CANCELLED'}
        preset_name = DYNSKY_OT_preset_add.unique_name(preset_name)
        target_dir = bpy.utils.user_resource(
            'SCRIPTS', path=os.path.join("presets", "dynamic_sky"), create=True)
        if not target_dir:
            self.report({'WARNING'}, "Failed to create presets path")
            return {'CANCELLED'}
        preset_path = os.path.join(target_dir, preset_name + ".py")
        write_preset_file(preset_path,
                          sky_socket_values(context.scene.world.node_tree.nodes))
        DYNSKY_MT_presets.bl_label = bpy.path.display_name(preset_name)
        update_thumbnail(context, preset_path)
        note_active_values(context)
        self.report({'INFO'}, "Duplicated to preset \"{:s}\"".format(
            DYNSKY_MT_presets.bl_label))
        return {'FINISHED'}


class DYNSKY_OT_preset_export(Operator, ExportHelper):
    bl_idname = "dynsky.preset_export"
    bl_label = "Export Sky Preset"
    bl_description = "Export the current sky settings to a JSON file for sharing"
    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return sky_world_ok(context)

    def execute(self, context):
        import json
        values = sky_socket_values(context.scene.world.node_tree.nodes)
        try:
            with open(self.filepath, "w", encoding="utf-8") as file_json:
                json.dump(values, file_json, indent=4, sort_keys=True)
        except OSError as ex:
            self.report({'ERROR'}, "Unable to export preset: {!r}".format(ex))
            return {'CANCELLED'}
        self.report({'INFO'}, "Exported sky settings to \"{:s}\"".format(self.filepath))
        return {'FINISHED'}


class DYNSKY_OT_preset_import(Operator, ImportHelper):
    bl_idname = "dynsky.preset_import"
    bl_label = "Import Sky Preset"
    bl_description = ("Import sky settings from a JSON file,\n"
                      "add them as a preset and apply them")
    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context):
        import json
        import os
        try:
            with open(self.filepath, "r", encoding="utf-8") as file_json:
                raw = json.load(file_json)
        except (OSError, ValueError) as ex:
            self.report({'ERROR'}, "Unable to read preset: {!r}".format(ex))
            return {'CANCELLED'}
        if not isinstance(raw, dict):
            self.report({'ERROR'}, "Not a Dynamic Sky preset file")
            return {'CANCELLED'}

        # Trust boundary: keep only known sockets with numbers of the right
        # shape, fall back to the default for anything missing or malformed
        values = {}
        for name, collection, index, default, *_ in SKY_DEFAULTS:
            key = sky_key(name, collection, index)
            value = raw.get(key, default)
            try:
                if isinstance(default, tuple):
                    value = [float(v) for v in value]
                    if len(value) != len(default):
                        value = list(default)
                else:
                    value = float(value)
            except (TypeError, ValueError):
                value = list(default) if isinstance(default, tuple) else default
            values[key] = value

        preset_name = DYNSKY_OT_preset_add.as_filename(
            os.path.splitext(os.path.basename(self.filepath))[0]) or "imported"
        preset_name = DYNSKY_OT_preset_add.unique_name(preset_name)
        target_dir = bpy.utils.user_resource(
            'SCRIPTS', path=os.path.join("presets", "dynamic_sky"), create=True)
        if not target_dir:
            self.report({'WARNING'}, "Failed to create presets path")
            return {'CANCELLED'}
        preset_path = os.path.join(target_dir, preset_name + ".py")
        autosave_active(context)
        write_preset_file(preset_path, values)

        display = bpy.path.display_name(preset_name)
        if sky_world_ok(context):
            from .sky import sync_background_mode
            apply_sky_values(context.scene.world.node_tree.nodes, values)
            sync_background_mode(context.scene.world)
            DYNSKY_MT_presets.bl_label = display
            update_thumbnail(context, preset_path)
            note_active_values(context)
        self.report({'INFO'}, "Imported preset \"{:s}\"".format(display))
        return {'FINISHED'}
