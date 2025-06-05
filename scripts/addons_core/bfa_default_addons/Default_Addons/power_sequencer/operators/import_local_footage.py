# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import os
import re

import bpy

from .utils.functions import convert_duration_to_frames
from .utils.doc import doc_brief, doc_description, doc_idname, doc_name
from ..addon_preferences import get_preferences
from .utils.global_settings import (
    Extensions,
    EXTENSIONS_ALL,
    EXTENSIONS_AUDIO,
    EXTENSIONS_IMG,
    EXTENSIONS_VIDEO,
)


class POWER_SEQUENCER_OT_import_local_footage(bpy.types.Operator):
    """*brief* Imports video, images, and audio from the project folder

    Finds and imports all valid video, audio files, and pictures in the blend file's folder and
    sub-folders, ignoring folders named BL_proxy.

    If you set it in the add-on preferences, it also sets imported sequences to use proxies. See
    `Preferences -> Add-ons -> Blender Power Sequencer -> Proxy`
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "I", "value": "PRESS", "ctrl": True, "shift": True},
                {"keep_audio": True},
                "Import Local Footage",
            )
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    keep_audio: bpy.props.BoolProperty(
        name="Keep Audio from Video Files",
        description=("If False, the audio that comes with video files will" " not be imported"),
        default=True,
    )
    img_length: bpy.props.FloatProperty(
        name="Image strip Length",
        description="Controls the duration of the imported image strip in seconds",
        default=3.0,
        min=1.0,
    )
    img_padding: bpy.props.FloatProperty(
        name="Image Padding",
        description="Padding added between imported image strips in seconds",
        default=1.0,
        min=0.0,
    )

    sequencer_area = None
    directory = ""

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def execute(self, context):
        self.sequencer_area = self.get_sequencer_area(context)
        self.directory = os.path.split(bpy.data.filepath)[0]

        filepaths = self.find_local_footage_files()
        files_to_import = [
            os.path.join(self.directory, f) for f in self.find_new_files_to_import(filepaths)
        ]
        if not files_to_import:
            self.report({"INFO"}, "No new files to import found")
            return {"FINISHED"}

        bpy.ops.screen.animation_cancel(restore_frame=True)

        audio = self.import_audios(
            context, [f for f in files_to_import if f.lower().endswith(EXTENSIONS_AUDIO)]
        )
        video = self.import_videos(
            context, [f for f in files_to_import if f.lower().endswith(EXTENSIONS_VIDEO)]
        )
        img = self.import_imgs(
            context, [f for f in files_to_import if f.lower().endswith(EXTENSIONS_IMG)]
        )

        bpy.data.texts["POWER_SEQUENCER_IMPORTS"].from_string(json.dumps(filepaths))

        for s in audio:
            s.show_waveform = True

        imported = audio + video + img
        for s in imported:
            s.select = True
        self.set_selected_strips_proxies(context)
        self.report({"INFO"}, "Imported {!s} strips from newly found files.".format(len(imported)))
        return {"FINISHED"}

    def get_sequencer_area(self, context):
        """
        Returns the sequencer area to use as a context override in
        some operators
        """
        sequencer_area = None
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if not area.type == "SEQUENCE_EDITOR":
                    continue
                sequencer_area = {
                    "window": window,
                    "screen": window.screen,
                    "area": area,
                    "scene": context.scene,
                }
        return sequencer_area

    def find_local_footage_files(self, ignored_directories=["BL_proxy"]):
        """
        Returns a list of relative filepaths in all subdirectories of the `self.directory`
        for all valid files that can be imported in the Sequencer
        """
        files_list = []
        for root, dirs, files in os.walk(self.directory):
            for directory in ignored_directories:
                if directory in dirs:
                    dirs.remove(directory)

            files = [f for f in sorted(files) if f.lower().endswith(EXTENSIONS_ALL)]
            files = map(lambda name: os.path.join(root, name), files)
            files = map(lambda path: os.path.relpath(path, self.directory), files)
            files_list.extend(list(files))

        return files_list

    def create_import_text_block(self, name):
        """
        Creates a new text data block that contains an empty json list, renames it to `name` and
        returns it
        """
        re.compile(r"^Text.[0-9]{3}$")

        bpy.ops.text.new()

        # Find the newly created text file's identifier
        ids = [text.name for text in bpy.data.texts if text.name.startswith("Text")]
        id = max(ids)

        text_file = bpy.data.texts[id]
        text_file.name = name
        text_file.from_string("[]")
        return text_file

    def find_new_files_to_import(self, filepaths):
        """
        Gets and optionally creates the list of already imported files in this project
        Returns a list of paths from filepaths that are not in the imported text file
        """
        text_file = (
            bpy.data.texts.get("POWER_SEQUENCER_IMPORTS")
            if "POWER_SEQUENCER_IMPORTS" in bpy.data.texts.keys()
            else self.create_import_text_block("POWER_SEQUENCER_IMPORTS")
        )
        imported_files = json.loads(text_file.as_string())
        files_to_import = [p for p in filepaths if p not in imported_files]
        return files_to_import

    def import_videos(self, context, videos_filepaths):
        """
        Imports a list of files using movie_strip_add
        Returns the list of imported sequences
        """
        frame = context.scene.frame_current

        context.window_manager.progress_begin(0, len(videos_filepaths))
        imported = []
        for index, f in enumerate(videos_filepaths):
            is_first_import = index == 0
            bpy.ops.sequencer.movie_strip_add(
                self.sequencer_area,
                filepath=f,
                frame_start=frame,
                sound=self.keep_audio,
                use_framerate=is_first_import,
            )
            imported.extend(context.selected_sequences)
            frame = context.selected_sequences[0].frame_final_end
            context.window_manager.progress_update(index)

        context.window_manager.progress_end()
        return imported

    def import_audios(self, context, audio_filepaths):
        """
        Imports audio files as sound strips from a list of absolute file paths
        Returns the list of newly imported audio files
        """
        frame = context.scene.frame_current
        imported = []
        for f in audio_filepaths:
            bpy.ops.sequencer.sound_strip_add(self.sequencer_area, filepath=f, frame_start=frame)
            imported.extend(context.selected_sequences)
            frame = context.selected_sequences[0].frame_final_end
        return imported

    def import_imgs(self, context, img_filepaths):
        frame = context.scene.frame_current
        strip_length = convert_duration_to_frames(context, self.img_length)
        strip_padding = convert_duration_to_frames(context, self.img_padding)

        new_sequences = []
        for f in img_filepaths:
            head, tail = os.path.split(f)
            bpy.ops.sequencer.image_strip_add(
                self.sequencer_area,
                directory=head,
                files=[{"name": tail}],
                frame_start=frame,
                frame_end=frame + strip_length,
            )
            frame += strip_length + strip_padding
            new_sequences.extend(context.selected_sequences)

        return new_sequences

    def set_selected_strips_proxies(self, context):
        proxy_sizes = ["25", "50", "75", "100"]

        use_proxy = False
        prefs = get_preferences(context)
        for size in proxy_sizes:
            if hasattr(prefs, "proxy_" + size):
                use_proxy = True
                break

        if not use_proxy:
            return

        for s in [s for s in context.selected_sequences if s.type in ["MOVIE", "IMAGE"]]:
            s.use_proxy = True
            s.proxy.build_25 = prefs.proxy_25
            s.proxy.build_50 = prefs.proxy_50
            s.proxy.build_75 = prefs.proxy_75
            s.proxy.build_100 = prefs.proxy_100
