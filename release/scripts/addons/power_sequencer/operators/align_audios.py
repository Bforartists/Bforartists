#
# Copyright (C) 2016-2019 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# This file is part of Power Sequencer.
#
# Power Sequencer is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Power Sequencer is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Power Sequencer. If
# not, see <https://www.gnu.org/licenses/>.
#
import bpy

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_align_audios(bpy.types.Operator):
    """*brief* Align two audio strips


    Tries to synchronize the selected audio strip to the active audio strip by comparing the sound.
    Useful to synchronize audio of the same event recorded with different microphones.

    To use this feature, you must have [ffmpeg](https://www.ffmpeg.org/download.html) and
    [scipy](https://www.scipy.org/install.html) installed on your computer and available on the PATH (command line) to work.

    The longer the audio files, the longer the tool can take to run, as it has to convert, analyze,
    and compare the audio sources to work.
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "https://i.imgur.com/xkBUzDj.gif",
        "description": doc_description(__doc__),
        "shortcuts": [],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not context.scene:
            return False

        active = context.scene.sequence_editor.active_strip
        selected = context.selected_sequences
        ok = (
            len(selected) == 2
            and active in selected
            and all(map(lambda s: s.type == "SOUND", selected))
        )
        return ok

    def execute(self, context):
        try:
            import scipy
        except ImportError:
            self.report({"ERROR"}, "Scipy must be installed to align audios")
            return {"FINISHED"}

        if not is_ffmpeg_available():
            self.report({"ERROR"}, "ffmpeg must be installed to align audios")
            return {"FINISHED"}

        # This import is here because otherwise, it slows down blender startup
        from .audiosync import find_offset

        scene = context.scene

        active = scene.sequence_editor.active_strip
        active_filepath = bpy.path.abspath(active.sound.filepath)

        selected = context.selected_sequences
        selected.pop(selected.index(active))

        align_strip = selected[0]
        align_strip_filepath = bpy.path.abspath(align_strip.sound.filepath)

        offset, score = find_offset(align_strip_filepath, active_filepath)

        initial_offset = active.frame_start - align_strip.frame_start

        fps = scene.render.fps / scene.render.fps_base
        frames = int(offset * fps)

        align_strip.frame_start -= frames - initial_offset

        self.report({"INFO"}, "Alignment score: " + str(round(score, 1)))

        return {"FINISHED"}


def is_ffmpeg_available():
    """
    Returns true if ffmpeg is installed and available from the PATH
    """
    try:
        subprocess.call(["ffmpeg", "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except OSError:
        return False
