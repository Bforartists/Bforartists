# SPDX-FileCopyrightText: 2011-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from . import presets

# A sorting func for collections (working in-place).
# XXX Not optimized at all…
# XXX If some items in the collection do not have the sortkey property, they are just ignored…
def collection_property_sort(collection, sortkey, start_idx=0):
    while start_idx + 1 < len(collection):
        while not hasattr(collection[start_idx], sortkey):
            start_idx += 1
            if start_idx + 1 >= len(collection):
                return collection
        min_idx = start_idx
        min_prop = collection[start_idx]
        for i, prop in enumerate(collection[start_idx + 1:]):
            if not hasattr(prop, sortkey):
                continue
            if getattr(prop, sortkey) < getattr(min_prop, sortkey):
                min_prop = prop
                min_idx = i + start_idx + 1
        collection.move(min_idx, start_idx)
        start_idx += 1
    return collection


def scene_render_copy_settings_update():
    """Prepare internal data for render_copy_settings (gathering all existing render settings, and scenes)."""
    current_scene = getattr(bpy.context, "scene", None)
    if current_scene is None:
        return
    cp_sett = current_scene.render_copy_settings

    # Get all available render settings, and update accordingly affected_settings…
    props = {}
    for prop in current_scene.render.bl_rna.properties:
        if prop.identifier in {'rna_type'}:
            continue
        if prop.is_readonly:
            continue
        props[prop.identifier] = prop.name
    corr = 0
    for i, sett in enumerate(cp_sett.affected_settings):
        if sett.strid not in props:
            cp_sett.affected_settings.remove(i - corr)
            corr += 1
        else:
            del props[sett.strid]
    for strid, name in props.items():
        sett = cp_sett.affected_settings.add()
        sett.name = "{} [{}]".format(name, strid)
        sett.strid = strid
    collection_property_sort(cp_sett.affected_settings, "name")

    # Get all available scenes, and update accordingly allowed_scenes…
    regex = None
    if cp_sett.filter_scene:
        try:
            import re
            try:
                regex = re.compile(cp_sett.filter_scene)
            except Exception as e:
                print("The filter-scene regex did not compile:\n    (%s)." % str(e))
                return
        except:
            regex = None
            print("Unable to import the re module, regex scene filtering will be disabled!")
    scenes = set()
    for scene in bpy.data.scenes:
        if scene == current_scene:  # Exclude current scene!
            continue
        # If a valid filtering regex, only keep scenes matching it.
        if regex:
            if regex.match(scene.name):
                scenes.add(scene.name)
        else:
            scenes.add(scene.name)
    for i, scene in enumerate(cp_sett.allowed_scenes):
        if scene.name not in scenes:
            cp_sett.allowed_scenes.remove(i)
        else:
            scenes.remove(scene.name)
    for scene in scenes:
        sett = cp_sett.allowed_scenes.add()
        sett.name = scene
    collection_property_sort(cp_sett.allowed_scenes, "name")


from bpy.props import EnumProperty


class RenderCopySettingsOPPreset(bpy.types.Operator):
    """Apply some presets of render settings to copy to other scenes"""
    bl_idname = "scene.render_copy_settings_preset"
    bl_label = "Render: Copy Settings Preset"
    bl_description = "Apply or clear this preset of render settings"
    # Enable undo…
    bl_option = {'REGISTER', 'UNDO'}

    presets: EnumProperty(items=(p.rna_enum for p in presets.presets),
                          default=set(),
                          options={'ENUM_FLAG'})

    @staticmethod
    def process_elements(settings, elts):
        setts = []
        val = True
        for sett in settings:
            if sett.strid in elts:
                setts.append(sett)
                val = val and sett.copy
        for e in setts:
            e.copy = not val

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        cp_sett = context.scene.render_copy_settings
        for p in presets.presets:
            if p.rna_enum[0] in self.presets:
                self.process_elements(cp_sett.affected_settings, p.elements)
        return {'FINISHED'}


# Real interesting stuff…

def do_copy(context, affected_settings, allowed_scenes):
    # Stores render settings from current scene.
    p = {sett: getattr(context.scene.render, sett)
         for sett in affected_settings}
    # put it in all other (valid) scenes’ render settings!
    for scene in bpy.data.scenes:
        # If scene not in allowed scenes, skip.
        if scene.name not in allowed_scenes:
            continue
        # Propagate all affected settings.
        for sett, val in p.items():
            setattr(scene.render, sett, val)


class RenderCopySettingsOPCopy(bpy.types.Operator):
    """Copy render settings from current scene to others"""
    bl_idname = "scene.render_copy_settings"
    bl_label = "Render: Copy Settings"
    # Enable undo…
    bl_option = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        regex = None
        cp_sett = context.scene.render_copy_settings
        affected_settings = {sett.strid for sett in cp_sett.affected_settings if sett.copy}
        allowed_scenes = {sce.name for sce in cp_sett.allowed_scenes if sce.allowed}
        do_copy(context, affected_settings=affected_settings, allowed_scenes=allowed_scenes)
        return {'FINISHED'}


classes = (
    RenderCopySettingsOPPreset,
    RenderCopySettingsOPCopy,
)
