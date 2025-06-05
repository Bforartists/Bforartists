# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import gpu
import math
from mathutils import Vector

from .utils.functions import (
    find_strips_mouse,
    trim_strips,
    find_snap_candidate,
    find_closest_surrounding_cuts,
)

from .utils.draw import (
    draw_line,
    draw_rectangle,
    draw_triangle_equilateral,
    draw_arrow_head,
    get_color_gizmo_primary,
    get_color_gizmo_secondary,
)
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description

if not bpy.app.background:
    SHADER = gpu.shader.from_builtin("UNIFORM_COLOR")


class POWER_SEQUENCER_OT_mouse_trim(bpy.types.Operator):
    """
    *brief* Cut or Trim strips quickly with the mouse cursor


    Click somewhere in the Sequencer to insert a cut, click and drag to trim
    With this function you can quickly cut and remove a section of strips while keeping or
    collapsing the remaining gap.
    Press <kbd>Ctrl</kbd> to snap to cuts.

    A [video demo](https://youtu.be/GiLmDhmMVAM?t=1m35s) is available.
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "https://i.imgur.com/wVvX4ex.gif",
        "description": doc_description(__doc__),
        "shortcuts": [
            (
                {"type": "T", "value": "PRESS"},
                {"select_mode": "CONTEXT", "gap_remove": False},
                "Trim using the mouse cursor",
            ),
            (
                {"type": "T", "value": "PRESS", "shift": True},
                {"select_mode": "CURSOR", "gap_remove": True},
                "Trim in all channels",
            ),
            (
                {"type": "T", "value": "PRESS", "shift": True, "alt": True},
                {"select_mode": "CURSOR", "gap_remove": True},
                "Trim in all channels and remove gaps",
            ),
            (
                {"type": "T", "value": "PRESS", "ctrl": True},
                {"select_mode": "CONTEXT", "gap_remove": False},
                "Trim using the mouse cursor",
            ),
            (
                {"type": "T", "value": "PRESS", "ctrl": True, "alt": True},
                {"select_mode": "CONTEXT", "gap_remove": True},
                "Trim using the mouse cursor and remove gaps",
            ),
            (
                {"type": "T", "value": "PRESS", "ctrl": True, "shift": True},
                {"select_mode": "CURSOR", "gap_remove": True},
                "Trim in all channels",
            ),
            (
                {"type": "T", "value": "PRESS", "ctrl": True, "shift": True, "alt": True},
                {"select_mode": "CURSOR", "gap_remove": True},
                "Trim in all channels and remove gaps",
            ),
        ],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    select_mode: bpy.props.EnumProperty(
        items=[
            ("CURSOR", "Time cursor", "Select all of the strips the time cursor overlaps"),
            ("CONTEXT", "Smart", "Uses the selection if possible, else uses the other modes"),
        ],
        name="Selection mode",
        description="Cut only the strip under the mouse or all strips under the time cursor",
        default="CONTEXT",
    )
    select_linked: bpy.props.BoolProperty(
        name="Use linked time",
        description="In mouse or CONTEXT mode, always cut linked strips if this is checked",
        default=False,
    )
    gap_remove: bpy.props.BoolProperty(
        name="Remove gaps",
        description="When trimming the sequences, remove gaps automatically",
        default=True,
    )

    TABLET_TRIM_DISTANCE_THRESHOLD = 6
    # Don't rename these variables, we're using setattr to access them dynamically
    trim_start, channel_start = 0, 0
    trim_end, channel_end = 0, 0
    is_trimming = False
    trim_side = "end"

    mouse_start_y = -1.0

    draw_handler = None

    use_audio_scrub = False

    event_shift_released = True
    event_alt_released = True

    event_ripple, event_ripple_string = "LEFT_ALT", "Alt"
    event_select_mode, event_select_mode_string = "LEFT_SHIFT", "Shift"
    event_change_side = "O"

    @classmethod
    def poll(cls, context):
        return context.sequences

    def invoke(self, context, event):
        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)

        self.use_audio_scrub = context.scene.use_audio_scrub
        context.scene.use_audio_scrub = False

        self.mouse_start_y = event.mouse_region_y

        self.trim_initialize(context, event)
        self.update_frame(context, event)
        self.draw_start(context, event)
        self.update_header_text(context, event)

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):

        if event.type == self.event_change_side and event.value == "PRESS":
            self.trim_side = "start" if self.trim_side == "end" else "end"

        if event.type == self.event_ripple and event.value == "PRESS":
            self.gap_remove = False if self.gap_remove else True

        if event.type == self.event_select_mode and event.value == "PRESS":
            self.select_mode = "CONTEXT" if self.select_mode == "CURSOR" else "CURSOR"

        if event.type in {"ESC"}:
            self.draw_stop()
            context.scene.use_audio_scrub = self.use_audio_scrub
            return {"FINISHED"}

        # Start and end trim
        if event.type == "LEFTMOUSE" or (event.type in ["RET", "T"] and event.value == "PRESS"):
            self.trim_apply(context, event)
            self.draw_stop()
            context.scene.use_audio_scrub = self.use_audio_scrub
            return {"FINISHED"}

        # Update trim
        if event.type == "MOUSEMOVE":
            self.draw_stop()
            self.update_frame(context, event)
            self.draw_start(context, event)
            self.update_header_text(context, event)
            return {"PASS_THROUGH"}

        return {"RUNNING_MODAL"}

    def trim_initialize(self, context, event):
        frame, self.channel_start = get_frame_and_channel(event)
        self.trim_start = find_snap_candidate(context, frame) if event.ctrl else frame
        self.trim_end, self.channel_end = self.trim_start, self.channel_start
        self.is_trimming = True

    def update_frame(self, context, event):
        frame, channel = get_frame_and_channel(event)
        frame_trim = find_snap_candidate(context, frame) if event.ctrl else frame
        setattr(self, "channel_" + self.trim_side, channel)
        setattr(self, "trim_" + self.trim_side, frame_trim)
        context.scene.frame_current = getattr(self, "trim_" + self.trim_side)

    def draw_start(self, context, event):
        """Initializes the drawing handler, see draw()"""
        to_trim, to_delete = self.find_strips_to_trim(context)
        target_strips = to_trim + to_delete

        draw_args = (self, context, self.trim_start, self.trim_end, target_strips, self.gap_remove)
        self.draw_handler = bpy.types.SpaceSequenceEditor.draw_handler_add(
            draw, draw_args, "WINDOW", "POST_PIXEL"
        )

    def draw_stop(self):
        if self.draw_handler:
            bpy.types.SpaceSequenceEditor.draw_handler_remove(self.draw_handler, "WINDOW")

    def update_header_text(self, context, event):
        text = (
            "Trim from {} to {}".format(self.trim_start, self.trim_end)
            + ", "
            + "({}) Gap Remove {}".format(
                self.event_ripple_string, "ON" if self.gap_remove else "OFF"
            )
            + ", "
            + "({}) Mode: {}".format(self.event_select_mode_string, self.select_mode.capitalize())
            + ", "
            + "(Ctrl) Snap: {}".format("ON" if event.ctrl else "OFF")
            + ", "
            + "({}) Change Side".format(self.event_change_side)
        )
        context.area.header_text_set(text)

    def trim_apply(self, context, event):
        start_x = context.region.view2d.region_to_view(
            x=event.mouse_region_x, y=event.mouse_region_y
        )[0]
        distance_to_start = abs(event.mouse_region_x - start_x)

        is_cutting = (
            self.trim_start == self.trim_end
            or event.is_tablet
            and distance_to_start <= self.TABLET_TRIM_DISTANCE_THRESHOLD
        )
        if is_cutting:
            self.cut(context)
        else:
            self.trim(context)
        self.is_trimming = False

    def cut(self, context):
        to_cut = self.find_strips_to_cut(context)
        bpy.ops.sequencer.select_all(action="DESELECT")
        for s in to_cut:
            s.select = True

        if len(to_cut) == 0:
            bpy.ops.power_sequencer.gap_remove()
        else:
            frame_current = context.scene.frame_current
            context.scene.frame_current = self.trim_start
            bpy.ops.sequencer.split(frame=context.scene.frame_current, type="SOFT", side="BOTH")
            context.scene.frame_current = frame_current

    def find_strips_to_cut(self, context):
        """
        Returns a list of strips to cut, either the strip hovered by the mouse or all strips under
        the time cursor, depending on the select_mode
        """
        to_cut, overlapping_strips = [], []
        if self.select_mode == "CONTEXT":
            overlapping_strips = find_strips_mouse(
                context, self.trim_start, self.channel_start, self.select_linked
            )
            to_cut.extend(overlapping_strips)
        if self.select_mode == "CURSOR" or (
            not overlapping_strips and self.select_mode == "CONTEXT"
        ):
            to_cut = [
                s
                for s in context.sequences
                if not s.lock and s.frame_final_start <= self.trim_start <= s.frame_final_end
            ]
        return to_cut

    def trim(self, context):
        to_trim, to_delete = self.find_strips_to_trim(context)
        trim_strips(context, self.trim_start, self.trim_end, to_trim, to_delete)
        if (self.gap_remove and self.select_mode == "CURSOR") or (
            self.select_mode == "CONTEXT" and to_trim == [] and to_delete == []
        ):
            context.scene.frame_current = min(self.trim_start, self.trim_end)
            bpy.ops.power_sequencer.gap_remove()
        else:
            context.scene.frame_current = self.trim_end

    def find_strips_to_trim(self, context):
        """
        Returns two lists of strips to trim and strips to delete
        """
        to_trim, to_delete = [], []

        trim_start = min(self.trim_start, self.trim_end)
        trim_end = max(self.trim_start, self.trim_end)

        channel_min = min(self.channel_start, self.channel_end)
        channel_max = max(self.channel_start, self.channel_end)
        channels = set(range(channel_min, channel_max + 1))

        for s in context.sequences:
            if s.lock:
                continue
            if self.select_mode == "CONTEXT" and s.channel not in channels:
                continue

            if trim_start <= s.frame_final_start and trim_end >= s.frame_final_end:
                to_delete.append(s)
                continue
            if (
                s.frame_final_start <= trim_start <= s.frame_final_end
                or s.frame_final_start <= trim_end <= s.frame_final_end
            ):
                to_trim.append(s)

        return to_trim, to_delete


def draw(self, context, frame_start=-1, frame_end=-1, target_strips=[], draw_arrows=False):
    """
    Draws the line and arrows that represent the trim

    Params:
    - start_x and end_x are Vector(), the start_x and end_x of the drawn trim line's vertices in region coordinates
    """
    view_to_region = context.region.view2d.view_to_region

    # Detect and draw the gap's limits if not trimming any strips
    if not target_strips:
        strip_before, strip_after = find_closest_surrounding_cuts(context, frame_end)
        frame_start = strip_before.frame_final_end
        frame_end = strip_after.frame_final_start
        channels = [strip_before.channel, strip_after.channel]
    else:
        channels = {s.channel for s in target_strips}

    start_x, start_y = view_to_region(
        min(frame_start, frame_end), math.floor(min(channels)), clip=False
    )
    end_x, end_y = view_to_region(
        max(frame_start, frame_end), math.floor(max(channels) + 1), clip=False
    )

    start_x = max(start_x, context.region.x)
    start_y = max(start_y, context.region.y)

    end_x = min(end_x, context.region.x + context.region.width)
    end_y = min(end_y, context.region.y + context.region.height)

    # Draw
    color_line = get_color_gizmo_primary(context)
    color_fill = color_line.copy()
    color_fill[-1] = 0.3

    rect_origin = Vector((start_x, start_y))
    rect_size = Vector((end_x - start_x, abs(start_y - end_y)))

    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(3.0)
    draw_rectangle(SHADER, rect_origin, rect_size, color_fill)
    # Vertical lines
    draw_line(SHADER, Vector((start_x, start_y)), Vector((start_x, end_y)), color_line)
    draw_line(SHADER, Vector((end_x, start_y)), Vector((end_x, end_y)), color_line)

    offset = 20.0
    radius = 12.0
    if draw_arrows and end_x - start_x > 2 * offset + radius:
        center_y = (end_y + start_y) / 2.0
        center_1 = Vector((start_x + offset, center_y))
        center_2 = Vector((end_x - offset, center_y))
        draw_triangle_equilateral(SHADER, center_1, radius, color=color_line)
        draw_triangle_equilateral(SHADER, center_2, radius, math.pi, color=color_line)

    gpu.state.line_width_set(1)
    gpu.state.blend_set('NONE')


def get_frame_and_channel(event):
    """
    Returns a tuple of (frame, channel)
    """
    frame_float, channel_float = bpy.context.region.view2d.region_to_view(
        x=event.mouse_region_x, y=event.mouse_region_y
    )
    return round(frame_float), math.floor(channel_float)
