# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import datetime as dt

from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_copy_markers_as_timecodes(bpy.types.Operator):
    """
    Formats and copies all the markers as timecodes to put in a Youtube video's description
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])

    @classmethod
    def poll(cls, context):
        return context.scene.timeline_markers

    def execute(self, context):
        render = context.scene.render

        if len(context.scene.timeline_markers) == 0:
            self.report({"INFO"}, "No markers found")
            return {"CANCELLED"}

        sorted_markers = sorted(context.scene.timeline_markers, key=lambda m: m.frame)

        framerate = render.fps / render.fps_base
        last_marker_seconds = sorted_markers[-1].frame / framerate
        seconds_in_hour = 3600.0
        time_format = "%H:%M:%S" if last_marker_seconds >= seconds_in_hour else "%M:%S"

        markers_as_timecodes = []
        for marker in sorted_markers:
            time = dt.datetime(year=1, month=1, day=1) + dt.timedelta(
                seconds=marker.frame / framerate
            )
            markers_as_timecodes.append(time.strftime(time_format) + " " + marker.name)

        bpy.context.window_manager.clipboard = "\n".join(markers_as_timecodes)
        return {"FINISHED"}
