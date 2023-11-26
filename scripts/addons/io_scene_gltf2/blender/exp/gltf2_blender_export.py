# SPDX-FileCopyrightText: 2018-2021 The glTF-Blender-IO authors
#
# SPDX-License-Identifier: Apache-2.0

import time

import bpy
import sys
import traceback

from ...io.com.gltf2_io_debug import print_console, print_newline
from ...io.exp import gltf2_io_export
from ...io.exp import gltf2_io_draco_compression_extension
from ...io.exp.gltf2_io_user_extensions import export_user_extensions
from ..com import gltf2_blender_json
from . import gltf2_blender_gather
from .gltf2_blender_gltf2_exporter import GlTF2Exporter
from .gltf2_blender_gltf2_exporter import fix_json


def save(context, export_settings):
    """Start the glTF 2.0 export and saves to content either to a .gltf or .glb file."""
    if bpy.context.active_object is not None:
        if bpy.context.active_object.mode != "OBJECT": # For linked object, you can't force OBJECT mode
            bpy.ops.object.mode_set(mode='OBJECT')

    original_frame = bpy.context.scene.frame_current
    if not export_settings['gltf_current_frame']:
        bpy.context.scene.frame_set(0)

    __notify_start(context)
    start_time = time.time()
    pre_export_callbacks = export_settings["pre_export_callbacks"]
    for callback in pre_export_callbacks:
        callback(export_settings)

    json, buffer = __export(export_settings)

    post_export_callbacks = export_settings["post_export_callbacks"]
    for callback in post_export_callbacks:
        callback(export_settings)
    __write_file(json, buffer, export_settings)

    end_time = time.time()
    __notify_end(context, end_time - start_time)

    if not export_settings['gltf_current_frame']:
        bpy.context.scene.frame_set(int(original_frame))
    return {'FINISHED'}


def __export(export_settings):
    exporter = GlTF2Exporter(export_settings)
    __gather_gltf(exporter, export_settings)
    buffer = __create_buffer(exporter, export_settings)
    exporter.finalize_images()

    export_user_extensions('gather_gltf_extensions_hook', export_settings, exporter.glTF)
    exporter.traverse_extensions()

    # now that addons possibly add some fields in json, we can fix in needed
    json = fix_json(exporter.glTF.to_dict())

    # Convert additional data if needed
    if export_settings['gltf_unused_textures'] is True:
        additional_json_textures = fix_json([i.to_dict() for i in exporter.additional_data.additional_textures])

        # Now that we have the final json, we can add the additional data
        # We can not do that for all people, because we don't want this extra to become "a standard"
        # So let's use the "extras" field filled by a user extension

        export_user_extensions('gather_gltf_additional_textures_hook', export_settings, json, additional_json_textures)

        # if len(additional_json_textures) > 0:
        #     if json.get('extras') is None:
        #         json['extras'] = {}
        #     json['extras']['additionalTextures'] = additional_json_textures

    return json, buffer


def __gather_gltf(exporter, export_settings):
    active_scene_idx, scenes, animations = gltf2_blender_gather.gather_gltf2(export_settings)

    unused_skins = export_settings['vtree'].get_unused_skins()

    if export_settings['gltf_draco_mesh_compression']:
        gltf2_io_draco_compression_extension.encode_scene_primitives(scenes, export_settings)
        exporter.add_draco_extension()

    export_user_extensions('gather_gltf_hook', export_settings, active_scene_idx, scenes, animations)

    for idx, scene in enumerate(scenes):
        exporter.add_scene(scene, idx==active_scene_idx, export_settings=export_settings)
    for animation in animations:
        exporter.add_animation(animation)
    exporter.traverse_unused_skins(unused_skins)
    exporter.traverse_additional_textures()
    exporter.traverse_additional_images()


def __create_buffer(exporter, export_settings):
    buffer = bytes()
    if export_settings['gltf_format'] == 'GLB':
        buffer = exporter.finalize_buffer(export_settings['gltf_filedirectory'], is_glb=True)
    else:
        exporter.finalize_buffer(export_settings['gltf_filedirectory'],
                                 export_settings['gltf_binaryfilename'])

    return buffer


def __write_file(json, buffer, export_settings):
    try:
        gltf2_io_export.save_gltf(
            json,
            export_settings,
            gltf2_blender_json.BlenderJSONEncoder,
            buffer)
    except AssertionError as e:
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb)  # Fixed format
        tb_info = traceback.extract_tb(tb)
        for tbi in tb_info:
            filename, line, func, text = tbi
            print_console('ERROR', 'An error occurred on line {} in statement {}'.format(line, text))
        print_console('ERROR', str(e))
        raise e


def __notify_start(context):
    print_console('INFO', 'Starting glTF 2.0 export')
    context.window_manager.progress_begin(0, 100)
    context.window_manager.progress_update(0)


def __notify_end(context, elapsed):
    print_console('INFO', 'Finished glTF 2.0 export in {} s'.format(elapsed))
    context.window_manager.progress_end()
    print_newline()
