# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import os
import shutil
import sys

from datetime import datetime
from bpy.types import Operator
from .utils import get_keyframe_list

# ------------------------------------------------------
# Button: Render VSE
# ------------------------------------------------------


class STORYPENCIL_OT_RenderAction(Operator):
    bl_idname = "storypencil.render_vse"
    bl_label = "Render Strips"
    bl_description = "Render VSE strips"

    # Extension by FFMPEG container type
    video_ext = {
        "MPEG1": ".mpg",
        "MPEG2": ".dvd",
        "MPEG4": ".mp4",
        "AVI": ".avi",
        "QUICKTIME": ".mov",
        "DV": ".dv",
        "OGG": ".ogv",
        "MKV": ".mkv",
        "FLASH": ".flv",
        "WEBM": ".webm"
    }
    # Extension by image format
    image_ext = {
        "BMP": ".bmp",
        "IRIS": ".rgb",
        "PNG": ".png",
        "JPEG": ".jpg",
        "JPEG2000": ".jp2",
        "TARGA": ".tga",
        "TARGA_RAW": ".tga",
        "CINEON": ".cin",
        "DPX": ".dpx",
        "OPEN_EXR_MULTILAYER": ".exr",
        "OPEN_EXR": ".exr",
        "HDR": ".hdr",
        "TIFF": ".tif",
        "WEBP": ".webp"
    }

    # --------------------------------------------------------------------
    # Format an int adding 4 zero padding
    # --------------------------------------------------------------------
    def format_to4(self, value):
        return f"{value:04}"

    # --------------------------------------------------------------------
    # Add frames every N frames
    # --------------------------------------------------------------------
    def add_missing_frames(self, sq, step, keyframe_list):
        missing = []
        lk = len(keyframe_list)
        if lk == 0:
            return

        # Add mid frames
        if step > 0:
            for i in range(0, lk - 1):
                dist = keyframe_list[i + 1] - keyframe_list[i]
                if dist > step:
                    delta = int(dist / step)
                    e = 1
                    for x in range(1, delta):
                        missing.append(keyframe_list[i] + (step * e))
                        e += 1

        keyframe_list.extend(missing)
        keyframe_list.sort()

    # ------------------------------
    # Execute
    # ------------------------------
    def execute(self, context):
        scene = bpy.context.scene
        image_settings = scene.render.image_settings
        is_video_output = image_settings.file_format in {
            'FFMPEG', 'AVI_JPEG', 'AVI_RAW'}
        step = scene.storypencil_render_step

        sequences = scene.sequence_editor.sequences_all
        prv_start = scene.frame_start
        prv_end = scene.frame_end
        prv_frame = bpy.context.scene.frame_current

        prv_path = scene.render.filepath
        prv_format = image_settings.file_format
        prv_use_file_extension = scene.render.use_file_extension
        prv_ffmpeg_format = scene.render.ffmpeg.format
        rootpath = bpy.path.abspath(scene.storypencil_render_render_path)
        only_selected = scene.storypencil_render_onlyselected
        channel = scene.storypencil_render_channel

        context.window.cursor_set('WAIT')

        # Create list of selected strips because the selection is changed when adding new strips
        Strips = []
        for sq in sequences:
            if sq.type == 'SCENE':
                if only_selected is False or sq.select is True:
                    Strips.append(sq)

        # Sort strips
        Strips = sorted(Strips, key=lambda strip: strip.frame_start)

        # For video, clear BL_proxy folder because sometimes the video
        # is not rendered as expected if this folder has data.
        # This ensure the output video is correct.
        if is_video_output:
            proxy_folder = os.path.join(rootpath, "BL_proxy")
            if os.path.exists(proxy_folder):
                for filename in os.listdir(proxy_folder):
                    file_path = os.path.join(proxy_folder, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print('Failed to delete %s. Reason: %s' %
                              (file_path, e))

        try:
            Videos = []
            Sheets = []
            # Read all strips and render the output
            for sq in Strips:
                strip_name = sq.name
                strip_scene = sq.scene
                scene.frame_start = int(sq.frame_start + sq.frame_offset_start)
                scene.frame_end = int(scene.frame_start + sq.frame_final_duration - 1)                # Image
                if is_video_output is False:
                    # Get list of any keyframe
                    strip_start = sq.frame_offset_start
                    if strip_start < strip_scene.frame_start:
                        strip_start = strip_scene.frame_start

                    strip_end = strip_start + sq.frame_final_duration - 1
                    keyframe_list = get_keyframe_list(
                        strip_scene, strip_start, strip_end)
                    self.add_missing_frames(sq, step, keyframe_list)

                    scene.render.use_file_extension = True
                    foldername = strip_name
                    if scene.storypencil_add_render_byfolder is True:
                        root_folder = os.path.join(rootpath, foldername)
                    else:
                        root_folder = rootpath

                    frame_nrr = 0
                    print("Render:" + strip_name + "/" + strip_scene.name)
                    print("Image From:", strip_start, "To", strip_end)
                    for key in range(int(strip_start), int(strip_end) + 1):
                        if key not in keyframe_list:
                            continue

                        keyframe = key + sq.frame_start
                        if scene.use_preview_range:
                            if keyframe < scene.frame_preview_start:
                                continue
                            if keyframe > scene.frame_preview_end:
                                break
                        else:
                            if keyframe < scene.frame_start:
                                continue
                            if keyframe > scene.frame_end:
                                break
                        # For frame name use only the number
                        if scene.storypencil_render_numbering == 'FRAME':
                            # Real
                            framename = strip_name + '.' + self.format_to4(key)
                        else:
                            # Consecutive
                            frame_nrr += 1
                            framename = strip_name + '.' + \
                                self.format_to4(frame_nrr)

                        filepath = os.path.join(root_folder, framename)

                        sheet = os.path.realpath(filepath)
                        sheet = bpy.path.ensure_ext(
                            sheet, self.image_ext[image_settings.file_format])
                        Sheets.append([sheet, keyframe])

                        scene.render.filepath = filepath

                        # Render Frame
                        scene.frame_set(int(keyframe - 1.0), subframe=0.0)
                        bpy.ops.render.render(
                            animation=False, write_still=True)

                        # Add strip with the corresponding length
                        if scene.storypencil_add_render_strip:
                            frame_start = sq.frame_start + key - 1
                            index = keyframe_list.index(key)
                            if index < len(keyframe_list) - 1:
                                key_next = keyframe_list[index + 1]
                                frame_end = frame_start + (key_next - key)
                            else:
                                frame_end = scene.frame_end + 1

                            if index == 0 and frame_start > scene.frame_start:
                                frame_start = scene.frame_start

                            if frame_end < frame_start:
                                frame_end = frame_start
                            image_ext = self.image_ext[image_settings.file_format]
                            bpy.ops.sequencer.image_strip_add(directory=root_folder,
                                                              files=[
                                                                  {"name": framename + image_ext}],
                                                              frame_start=int(frame_start),
                                                              frame_end=int(frame_end),
                                                              channel=channel)
                else:
                    print("Render:" + strip_name + "/" + strip_scene.name)
                    print("Video From:", scene.frame_start,
                          "To", scene.frame_end)
                    # Video
                    filepath = os.path.join(rootpath, strip_name)

                    if image_settings.file_format == 'FFMPEG':
                        ext = self.video_ext[scene.render.ffmpeg.format]
                    else:
                        ext = '.avi'

                    if not filepath.endswith(ext):
                        filepath += ext

                    scene.render.use_file_extension = False
                    scene.render.filepath = filepath

                    # Render Animation
                    bpy.ops.render.render(animation=True)

                    # Add video to add strip later
                    if scene.storypencil_add_render_strip:
                        Videos.append(
                            [filepath, sq.frame_start + sq.frame_offset_start])

            # Add pending video Strips
            for vid in Videos:
                bpy.ops.sequencer.movie_strip_add(filepath=vid[0],
                                                  frame_start=int(vid[1]),
                                                  channel=channel)

            scene.frame_start = prv_start
            scene.frame_end = prv_end
            scene.render.use_file_extension = prv_use_file_extension
            image_settings.file_format = prv_format
            scene.render.ffmpeg.format = prv_ffmpeg_format

            scene.render.filepath = prv_path
            scene.frame_set(int(prv_frame))

            context.window.cursor_set('DEFAULT')

            return {'FINISHED'}

        except:
            print("Unexpected error:" + str(sys.exc_info()))
            self.report({'ERROR'}, "Unable to render")
            scene.frame_start = prv_start
            scene.frame_end = prv_end
            scene.render.use_file_extension = prv_use_file_extension
            image_settings.file_format = prv_format

            scene.render.filepath = prv_path
            scene.frame_set(int(prv_frame))
            context.window.cursor_set('DEFAULT')
            return {'FINISHED'}
