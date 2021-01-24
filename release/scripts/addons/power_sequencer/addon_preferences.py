#
# Copyright (C) 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
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
"""
Add-on preferences and interface in the Blender preferences window.
"""
import subprocess

import bpy
from bpy.props import BoolProperty, StringProperty


def get_preferences(context):
    return context.preferences.addons[__package__].preferences


class PowerSequencerPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    proxy_25: bpy.props.BoolProperty(name="25%", default=False)
    proxy_50: bpy.props.BoolProperty(name="50%", default=False)
    proxy_75: bpy.props.BoolProperty(name="75%", default=False)
    proxy_100: bpy.props.BoolProperty(name="100%", default=False)

    # Code adapted from Krzysztof Trzciński's work
    ffmpeg_executable: StringProperty(
        name="Path to ffmpeg executable",
        default="",
        update=lambda self, context: self.update_ffmpeg_executable(context),
        subtype="FILE_PATH",
    )
    ffmpeg_status: StringProperty(default="")
    ffmpeg_is_executable_valid: BoolProperty(default=False)

    def update_ffmpeg_executable(self, context):
        error_message, info = self._try_run_ffmpeg(self.ffmpeg_executable)
        self.ffmpeg_is_executable_valid = error_message == ""
        self.ffmpeg_status = error_message if error_message != "" else info

    def _try_run_ffmpeg(self, path):
        """Runs ffmpeg -version, and returns an error message if it failed"""
        error_message, info = "", ""
        try:
            info: str = subprocess.check_output([path, "-version"]).decode("utf-8")
            info = info[: info.find("Copyright")]
            print(info)
        except (OSError, subprocess.CalledProcessError):
            error_message = "Path `{}` is not a valid ffmpeg executable".format(path)
        return error_message, info

    def draw(self, context):
        layout = self.layout

        layout.label(text="Proxy")

        row = layout.row()
        row.prop(self, "proxy_25")
        row.prop(self, "proxy_50")
        row.prop(self, "proxy_75")
        row.prop(self, "proxy_100")

        text = [
            "(Optional) FFMpeg executable to use for multithread renders and proxy generation. "
            "Use this to render with a version of ffmpeg that's not on your system's PATH variable."
        ]
        for line in text:
            layout.label(text=line)
        layout.prop(self, "ffmpeg_executable")
        icon = "INFO" if self.ffmpeg_is_executable_valid else "ERROR"
        layout.label(text=self.ffmpeg_status, icon=icon)


register_preferences, unregister_preferences = bpy.utils.register_classes_factory(
    [PowerSequencerPreferences]
)
