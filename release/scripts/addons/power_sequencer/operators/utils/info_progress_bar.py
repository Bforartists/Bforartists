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
import bpy


class InfoProgressBar:
    """
    Draws a progress bar in the info header area
    """

    def __init__(self, progress_min=0, progress_max=100):
        assert progress_min < progress_max

        self.progress_min = progress_min
        self.progress_max = progress_max

        self._progress = bpy.props.FloatProperty(
            default=self.progress_min,
            min=self.progress_min,
            max=self.progress_max,
            subtype="PERCENTAGE",
        )
        self._visible = False

    def update(self, context):
        for area in context.screen.areas:
            if area.type == "INFO":
                area.tag_redraw()

    def draw(self):
        if self.progress >= self.progress_max:
            self.visible = False
        else:
            self.layout.prop(self, "_progress", text="Progress", slider=True)

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        self._progress = min(max(self.progress_min, value), self.progress_max)

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        self._visible = value

        if self._visible:
            bpy.types.INFO_HT_header.append(self.draw)
            bpy.app.handlers.scene_update_post.add(self.update)
        else:
            bpy.types.INFO_HT_header.remove(self.draw)
            bpy.app.handlers.scene_update_post.remove(self.update)
