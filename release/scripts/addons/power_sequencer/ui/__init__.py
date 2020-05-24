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
from .menu_contextual import POWER_SEQUENCER_MT_contextual
from .menu_toolbar import (
    POWER_SEQUENCER_MT_main,
    POWER_SEQUENCER_MT_playback,
    POWER_SEQUENCER_MT_strips,
    POWER_SEQUENCER_MT_select,
    POWER_SEQUENCER_MT_edit,
    POWER_SEQUENCER_MT_markers,
    POWER_SEQUENCER_MT_file,
    POWER_SEQUENCER_MT_trim,
    POWER_SEQUENCER_MT_preview,
    POWER_SEQUENCER_MT_audio,
    POWER_SEQUENCER_MT_transitions,
)

classes = [
    POWER_SEQUENCER_MT_contextual,
    POWER_SEQUENCER_MT_main,
    POWER_SEQUENCER_MT_playback,
    POWER_SEQUENCER_MT_strips,
    POWER_SEQUENCER_MT_select,
    POWER_SEQUENCER_MT_edit,
    POWER_SEQUENCER_MT_markers,
    POWER_SEQUENCER_MT_file,
    POWER_SEQUENCER_MT_trim,
    POWER_SEQUENCER_MT_preview,
    POWER_SEQUENCER_MT_audio,
    POWER_SEQUENCER_MT_transitions,
]

register_ui, unregister_ui = bpy.utils.register_classes_factory(classes)
