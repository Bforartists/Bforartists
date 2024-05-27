# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

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
