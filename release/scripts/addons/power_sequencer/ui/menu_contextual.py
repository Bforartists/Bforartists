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
from ..operators.utils.global_settings import SequenceTypes


class POWER_SEQUENCER_MT_contextual(bpy.types.Menu):
    bl_label = "Power Sequencer"
    # bl_idname = "SEQUENCER_MT_power_sequencer_menu"

    def draw(self, context):
        layout = self.layout

        if not bpy.data.is_saved:
            layout.label("Please save your project")
            layout.operator("wm.save_as_mainfile", icon="SAVE_AS", text="Save as")
            return

        if not context.sequences:
            layout.operator(
                "power_sequencer.import_local_footage", icon="SEQUENCE", text="Import local footage"
            )
            return

        selection = context.selected_sequences
        active_strip = context.scene.sequence_editor.active_strip
        types = set([s.type for s in selection])

        if active_strip.type == "GAMMA_CROSS":
            layout.operator(
                "power_sequencer.crossfade_edit", icon="ACTION_TWEAK", text="Edit crossfade"
            )

        for t in types:
            if t in SequenceTypes.VIDEO:
                layout.operator("power_sequencer.fade_add", icon="IMAGE_ALPHA", text="Fade strips")
                break

        if len(selection) == 1:
            for s in [active_strip, selection[0]]:
                if s.type in SequenceTypes.VIDEO or s.type in SequenceTypes.IMAGE:
                    layout.separator()
                    layout.operator(
                        "power_sequencer.crossfade_add", icon="IMAGE_ALPHA", text="Auto crossfade"
                    )
                    break

        # TODO: Doesn't work from the menu, I guess there's an issue with the invoke method?
        # layout.separator()
        # layout.operator('power_sequencer.grab_closest_handle_or_cut', icon='SNAP_SURFACE', text='Grab cut or handle')

        if len(selection) > 1:
            layout.separator()

            layout.operator(
                "power_sequencer.ripple_delete", icon="AUTOMERGE_ON", text="Ripple delete"
            )
            layout.operator("power_sequencer.snap_selection", icon="SNAP_ON", text="Snap selection")

        layout.separator()

        layout.operator(
            "power_sequencer.import_local_footage", icon="SEQUENCE", text="Import local footage"
        )
        layout.operator(
            "power_sequencer.render_video", icon="RENDER_ANIMATION", text="Render video for the web"
        )
