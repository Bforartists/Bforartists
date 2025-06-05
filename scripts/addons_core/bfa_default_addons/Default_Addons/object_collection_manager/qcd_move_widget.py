# SPDX-FileCopyrightText: 2011 Ryan Inch
#
# SPDX-License-Identifier: GPL-2.0-or-later

import time
from math import cos, sin, pi, floor
import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader

from bpy.types import Operator

from . import internals

from .qcd_operators import (
    get_move_selection,
    get_move_active,
    )

def spacer():
    spacer = 10
    return round(spacer * scale_factor())

def scale_factor():
    return bpy.context.preferences.system.ui_scale

def get_coords(area):
    x = area["vert"][0]
    y = area["vert"][1]
    w = area["width"]
    h = area["height"]

    vertices = (
        (x, y-h), # bottom left
        (x+w, y-h), # bottom right
        (x, y), # top left
        (x+w, y)) # top right

    indices = (
        (0, 1, 2), (2, 1, 3))

    return vertices, indices

def get_x_coords(area):
    x = area["vert"][0]
    y = area["vert"][1]
    w = area["width"]
    h = area["height"]

    vertices = (
        (x, y), # top left A
        (x+(w*0.1), y), # top left B
        (x+w, y), # top right A
        (x+w-(w*0.1), y), # top right B
        (x, y-h), # bottom left A
        (x+(w*0.1), y-h), # bottom left B
        (x+w, y-h), # bottom right A
        (x+w-(w*0.1), y-h), # bottom right B
        (x+(w/2)-(w*0.05), y-(h/2)), # center left
        (x+(w/2)+(w*0.05), y-(h/2))  # center right
        )

    indices = (
        (0,1,8), (1,8,9), # top left bar
        (2,3,9), (3,9,8), # top right bar
        (4,5,8), (5,8,9), # bottom left bar
        (6,7,8), (6,9,8)  # bottom right bar
        )

    return vertices, indices

def get_circle_coords(area):
    # set x, y to center
    x = area["vert"][0] + area["width"] / 2
    y = area["vert"][1] - area["width"] / 2
    radius = area["width"] / 2
    sides = 32
    vertices = [(radius * cos(side * 2 * pi / sides) + x,
                 radius * sin(side * 2 * pi / sides) + y)
                 for side in range(sides + 1)]

    return vertices

def draw_rounded_rect(area, shader, color, tl=5, tr=5, bl=5, br=5, outline=False):
    sides = 32

    tl = round(tl * scale_factor())
    tr = round(tr * scale_factor())
    bl = round(bl * scale_factor())
    br = round(br * scale_factor())

    gpu.state.blend_set('ALPHA')

    if outline:
        thickness = round(2 * scale_factor())
        thickness = max(thickness, 2)
        shader.uniform_float("lineWidth", thickness)

    draw_type = 'TRI_FAN' if not outline else 'LINE_STRIP'

    # top left corner
    vert_x = area["vert"][0] + tl
    vert_y = area["vert"][1] - tl
    tl_vert = (vert_x, vert_y)
    vertices = [(vert_x, vert_y)] if not outline else []

    for side in range(sides+1):
        if (8<=side<=16):
            cosine = tl * cos(side * 2 * pi / sides) + vert_x
            sine = tl * sin(side * 2 * pi / sides) + vert_y
            vertices.append((cosine,sine))

    if not outline:
        batch = batch_for_shader(shader, draw_type, {"pos": vertices})
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)
    else:
        batch = batch_for_shader(shader, draw_type, {"pos": [(v[0], v[1], 0) for v in vertices], "color": [color for v in vertices]})
        shader.bind()
        batch.draw(shader)

    # top right corner
    vert_x = area["vert"][0] + area["width"] - tr
    vert_y = area["vert"][1] - tr
    tr_vert = (vert_x, vert_y)
    vertices = [(vert_x, vert_y)] if not outline else []

    for side in range(sides+1):
        if (0<=side<=8):
            cosine = tr * cos(side * 2 * pi / sides) + vert_x
            sine = tr * sin(side * 2 * pi / sides) + vert_y
            vertices.append((cosine,sine))

    if not outline:
        batch = batch_for_shader(shader, draw_type, {"pos": vertices})
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)
    else:
        batch = batch_for_shader(shader, draw_type, {"pos": [(v[0], v[1], 0) for v in vertices], "color": [color for v in vertices]})
        shader.bind()
        batch.draw(shader)

    # bottom left corner
    vert_x = area["vert"][0] + bl
    vert_y = area["vert"][1] - area["height"] + bl
    bl_vert = (vert_x, vert_y)
    vertices = [(vert_x, vert_y)] if not outline else []

    for side in range(sides+1):
        if (16<=side<=24):
            cosine = bl * cos(side * 2 * pi / sides) + vert_x
            sine = bl * sin(side * 2 * pi / sides) + vert_y
            vertices.append((cosine,sine))

    if not outline:
        batch = batch_for_shader(shader, draw_type, {"pos": vertices})
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)
    else:
        batch = batch_for_shader(shader, draw_type, {"pos": [(v[0], v[1], 0) for v in vertices], "color": [color for v in vertices]})
        shader.bind()
        batch.draw(shader)

    # bottom right corner
    vert_x = area["vert"][0] + area["width"] - br
    vert_y = area["vert"][1] - area["height"] + br
    br_vert = (vert_x, vert_y)
    vertices = [(vert_x, vert_y)] if not outline else []

    for side in range(sides+1):
        if (24<=side<=32):
            cosine = br * cos(side * 2 * pi / sides) + vert_x
            sine = br * sin(side * 2 * pi / sides) + vert_y
            vertices.append((cosine,sine))

    if not outline:
        batch = batch_for_shader(shader, draw_type, {"pos": vertices})
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)
    else:
        batch = batch_for_shader(shader, draw_type, {"pos": [(v[0], v[1], 0) for v in vertices], "color": [color for v in vertices]})
        shader.bind()
        batch.draw(shader)

    if not outline:
        vertices = []
        indices = []
        base_ind = 0

        # left edge
        width = max(tl, bl)
        le_x = tl_vert[0]-tl
        vertices.extend([
            (le_x, tl_vert[1]),
            (le_x+width, tl_vert[1]),
            (le_x, bl_vert[1]),
            (le_x+width, bl_vert[1])
            ])
        indices.extend([
            (base_ind,base_ind+1,base_ind+2),
            (base_ind+2,base_ind+3,base_ind+1)
            ])
        base_ind += 4

        # right edge
        width = max(tr, br)
        re_x = tr_vert[0]+tr
        vertices.extend([
            (re_x, tr_vert[1]),
            (re_x-width, tr_vert[1]),
            (re_x, br_vert[1]),
            (re_x-width, br_vert[1])
            ])
        indices.extend([
            (base_ind,base_ind+1,base_ind+2),
            (base_ind+2,base_ind+3,base_ind+1)
            ])
        base_ind += 4

        # top edge
        width = max(tl, tr)
        te_y = tl_vert[1]+tl
        vertices.extend([
            (tl_vert[0], te_y),
            (tl_vert[0], te_y-width),
            (tr_vert[0], te_y),
            (tr_vert[0], te_y-width)
            ])
        indices.extend([
            (base_ind,base_ind+1,base_ind+2),
            (base_ind+2,base_ind+3,base_ind+1)
            ])
        base_ind += 4

        # bottom edge
        width = max(bl, br)
        be_y = bl_vert[1]-bl
        vertices.extend([
            (bl_vert[0], be_y),
            (bl_vert[0], be_y+width),
            (br_vert[0], be_y),
            (br_vert[0], be_y+width)
            ])
        indices.extend([
            (base_ind,base_ind+1,base_ind+2),
            (base_ind+2,base_ind+3,base_ind+1)
            ])
        base_ind += 4

        # middle
        vertices.extend([
            tl_vert,
            tr_vert,
            bl_vert,
            br_vert
            ])
        indices.extend([
            (base_ind,base_ind+1,base_ind+2),
            (base_ind+2,base_ind+3,base_ind+1)
            ])

        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
        shader.bind()

        shader.uniform_float("color", color)
        batch.draw(shader)

    else:
        overlap = round(thickness / 2 - scale_factor() / 2)

        # left edge
        le_x = tl_vert[0]-tl
        vertices = [
            (le_x, tl_vert[1] + (overlap if tl == 0 else 0)),
            (le_x, bl_vert[1] - (overlap if bl == 0 else 0))
            ]

        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": [(v[0], v[1], 0) for v in vertices], "color": [color for v in vertices]})
        shader.bind()
        batch.draw(shader)

        # right edge
        re_x = tr_vert[0]+tr
        vertices = [
            (re_x, tr_vert[1] + (overlap if tr == 0 else 0)),
            (re_x, br_vert[1] - (overlap if br == 0 else 0))
            ]

        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": [(v[0], v[1], 0) for v in vertices], "color": [color for v in vertices]})
        shader.bind()
        batch.draw(shader)

        # top edge
        te_y = tl_vert[1]+tl
        vertices = [
            (tl_vert[0] - (overlap if tl == 0 else 0), te_y),
            (tr_vert[0] + (overlap if tr == 0 else 0), te_y)
            ]

        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": [(v[0], v[1], 0) for v in vertices], "color": [color for v in vertices]})
        shader.bind()
        batch.draw(shader)

        # bottom edge
        be_y = bl_vert[1]-bl
        vertices = [
            (bl_vert[0] - (overlap if bl == 0 else 0), be_y),
            (br_vert[0] + (overlap if br == 0 else 0), be_y)
            ]

        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": [(v[0], v[1], 0) for v in vertices], "color": [color for v in vertices]})
        shader.bind()
        batch.draw(shader)


    gpu.state.blend_set('NONE')

def mouse_in_area(mouse_pos, area, buf = 0):
    x = mouse_pos[0]
    y = mouse_pos[1]

    # check left
    if x+buf < area["vert"][0]:
        return False

    # check right
    if x-buf > area["vert"][0] + area["width"]:
        return False

    # check top
    if y-buf > area["vert"][1]:
        return False

    # check bottom
    if y+buf < area["vert"][1] - area["height"]:
        return False

    # if we reach here we're in the area
    return True

def account_for_view_bounds(area):
    # make sure it renders in the 3d view - prioritize top left

    # right
    if area["vert"][0] + area["width"] > bpy.context.region.width:
        x = bpy.context.region.width - area["width"]
        y = area["vert"][1]

        area["vert"] = (x, y)

    # left
    if area["vert"][0] < 0:
        x = 0
        y = area["vert"][1]

        area["vert"] = (x, y)

    # bottom
    if area["vert"][1] - area["height"] < 0:
        x = area["vert"][0]
        y = area["height"]

        area["vert"] = (x, y)

    # top
    if area["vert"][1] > bpy.context.region.height:
        x = area["vert"][0]
        y = bpy.context.region.height

        area["vert"] = (x, y)

def update_area_dimensions(area, w=0, h=0):
    area["width"] += w
    area["height"] += h

class QCDMoveWidget(Operator):
    """Move objects to QCD Slots"""
    bl_idname = "view3d.qcd_move_widget"
    bl_label = "QCD Move Widget"

    slots = {
        "ONE":1,
        "TWO":2,
        "THREE":3,
        "FOUR":4,
        "FIVE":5,
        "SIX":6,
        "SEVEN":7,
        "EIGHT":8,
        "NINE":9,
        "ZERO":10,
        }

    last_type = ''
    last_type_value = ''
    initialized = False
    moved = False

    def modal(self, context, event):
        if event.type == 'TIMER':
            if self.hover_time and self.hover_time + 0.5 < time.time():
                self.draw_tooltip = True

                context.area.tag_redraw()
            return {'RUNNING_MODAL'}


        context.area.tag_redraw()

        if len(self.areas) == 1:
            return {'RUNNING_MODAL'}

        if self.last_type == 'LEFTMOUSE' and self.last_type_value == 'PRESS' and event.type == 'MOUSEMOVE':
            if mouse_in_area(self.mouse_pos, self.areas["Grab Bar"]):
                x_offset = self.areas["Main Window"]["vert"][0] - self.mouse_pos[0]
                x = event.mouse_region_x + x_offset

                y_offset = self.areas["Main Window"]["vert"][1] - self.mouse_pos[1]
                y = event.mouse_region_y + y_offset

                self.areas["Main Window"]["vert"] = (x, y)

                self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)

        elif event.type == 'MOUSEMOVE':
            self.draw_tooltip = False
            self.hover_time = None
            self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)

            if not mouse_in_area(self.mouse_pos, self.areas["Main Window"], 50 * scale_factor()):
                if self.initialized:
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

                    if self.moved:
                        bpy.ops.ed.undo_push()

                    return {'FINISHED'}

            else:
                self.initialized = True

        elif event.value == 'PRESS' and event.type == 'LEFTMOUSE':
            if not mouse_in_area(self.mouse_pos, self.areas["Main Window"], 10 * scale_factor()):
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

                if self.moved:
                    bpy.ops.ed.undo_push()

                return {'FINISHED'}

            for num in range(20):
                if not self.areas.get(f"Button {num + 1}", None):
                    continue

                if mouse_in_area(self.mouse_pos, self.areas[f"Button {num + 1}"]):
                    bpy.ops.view3d.move_to_qcd_slot(slot=str(num + 1), toggle=event.shift)
                    self.moved = True

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

            return {'CANCELLED'}

        if event.value == 'PRESS' and event.type in self.slots:
            move_to = self.slots[event.type]

            if event.alt:
                move_to += 10

            if event.shift:
                bpy.ops.view3d.move_to_qcd_slot(slot=str(move_to), toggle=True)
            else:
                bpy.ops.view3d.move_to_qcd_slot(slot=str(move_to), toggle=False)

            self.moved = True

        if event.type != 'MOUSEMOVE' and event.type != 'INBETWEEN_MOUSEMOVE':
            self.last_type = event.type
            self.last_type_value = event.value

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callback
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
            self._timer = context.window_manager.event_timer_add(0.1, window=context.window)

            self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)

            self.draw_tooltip = False

            self.hover_time = None

            self.areas = {}

            # MAIN WINDOW BACKGROUND
            x = self.mouse_pos[0] - spacer()*2
            y = self.mouse_pos[1] + spacer()*2
            main_window = {
                # Top Left Vertex
                "vert": (x,y),
                "width": 0,
                "height": 0,
                "value": None
                }

            self.areas["Main Window"] = main_window
            allocate_main_ui(self, context)
            account_for_view_bounds(main_window)

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


def allocate_main_ui(self, context):
    main_window = self.areas["Main Window"]
    self.areas.clear()
    main_window["width"] = 0
    main_window["height"] = 0
    self.areas["Main Window"] = main_window

    cur_width_pos = main_window["vert"][0]
    cur_height_pos = main_window["vert"][1]

    # GRAB BAR
    grab_bar = {
        "vert": main_window["vert"],
        "width": 0,
        "height": round(23 * scale_factor()),
        "value": None
        }

    # add grab bar to areas
    self.areas["Grab Bar"] = grab_bar


    # WINDOW TITLE
    wt_indent_x = spacer()*2
    wt_y_offset = round(spacer()/2)
    window_title = {
        "vert": main_window["vert"],
        "width": 0,
        "height": round(13 * scale_factor()),
        "value": "Move Objects to QCD Slots"
        }

    x = main_window["vert"][0] + wt_indent_x
    y = main_window["vert"][1] - window_title["height"] - wt_y_offset
    window_title["vert"] = (x, y)

    # add window title to areas
    self.areas["Window Title"] = window_title

    cur_height_pos = window_title["vert"][1]


    # MAIN BUTTON AREA
    button_size = round(20 * scale_factor())
    button_gap = round(1 * scale_factor())
    button_group = 5
    button_group_gap = round(20 * scale_factor())
    button_group_width = button_size * button_group + button_gap * (button_group - 1)

    mba_indent_x = spacer()*2
    mba_outdent_x = spacer()*2
    mba_indent_y = spacer()
    x = cur_width_pos + mba_indent_x
    y = cur_height_pos - mba_indent_y
    main_button_area = {
        "vert": (x, y),
        "width": 0,
        "height": 0,
        "value": None
        }

    # add main button area to areas
    self.areas["Main Button Area"] = main_button_area

    # update current position
    cur_width_pos = main_button_area["vert"][0]
    cur_height_pos = main_button_area["vert"][1]


    # BUTTON ROW 1 A
    button_row_1_a = {
        "vert": main_button_area["vert"],
        "width": button_group_width,
        "height": button_size,
        "value": None
        }

    # add button row 1 A to areas
    self.areas["Button Row 1 A"] = button_row_1_a

    # advance width pos to start of next row
    cur_width_pos += button_row_1_a["width"]
    cur_width_pos += button_group_gap

    # BUTTON ROW 1 B
    x = cur_width_pos
    y = cur_height_pos
    button_row_1_b = {
        "vert": (x, y),
        "width": button_group_width,
        "height": button_size,
        "value": None
        }

    # add button row 1 B to areas
    self.areas["Button Row 1 B"] = button_row_1_b

    # reset width pos to start of main button area
    cur_width_pos = main_button_area["vert"][0]
    # update height pos
    cur_height_pos -= button_row_1_a["height"]
    # add gap between button rows
    cur_height_pos -= button_gap


    # BUTTON ROW 2 A
    x = cur_width_pos
    y = cur_height_pos
    button_row_2_a = {
        "vert": (x, y),
        "width": button_group_width,
        "height": button_size,
        "value": None
        }

    # add button row 2 A to areas
    self.areas["Button Row 2 A"] = button_row_2_a

    # advance width pos to start of next row
    cur_width_pos += button_row_2_a["width"]
    cur_width_pos += button_group_gap

    # BUTTON ROW 2 B
    x = cur_width_pos
    y = cur_height_pos
    button_row_2_b = {
        "vert": (x, y),
        "width": button_group_width,
        "height": button_size,
        "value": None
        }

    # add button row 2 B to areas
    self.areas["Button Row 2 B"] = button_row_2_b


    selected_objects = get_move_selection()
    active_object = get_move_active()


    # BUTTONS
    def get_buttons(button_row, row_num):
        cur_width_pos = button_row["vert"][0]
        cur_height_pos = button_row["vert"][1]
        for num in range(button_group):
            slot_num = row_num + num

            qcd_slot_name = internals.qcd_slots.get_name(f"{slot_num}")

            if qcd_slot_name:
                qcd_laycol = internals.layer_collections[qcd_slot_name]["ptr"]
                collection_objects = qcd_laycol.collection.objects

                # BUTTON
                x = cur_width_pos
                y = cur_height_pos
                button = {
                    "vert": (x, y),
                    "width": button_size,
                    "height": button_size,
                    "value": slot_num
                    }

                self.areas[f"Button {slot_num}"] = button

                # ACTIVE OBJECT ICON
                if active_object and active_object in selected_objects and active_object.name in collection_objects:
                    x = cur_width_pos + round(button_size / 4)
                    y = cur_height_pos - round(button_size / 4)
                    active_object_indicator = {
                    "vert": (x, y),
                    "width": floor(button_size / 2),
                    "height": floor(button_size / 2),
                    "value": None
                    }

                    self.areas[f"Button {slot_num} Active Object Indicator"] = active_object_indicator

                elif not set(selected_objects).isdisjoint(collection_objects):
                    x = cur_width_pos + round(button_size / 4) + floor(1 * scale_factor())
                    y = cur_height_pos - round(button_size / 4) - floor(1 * scale_factor())
                    selected_object_indicator = {
                        "vert": (x, y),
                        "width": floor(button_size / 2) - floor(1 * scale_factor()),
                        "height": floor(button_size / 2) - floor(1 * scale_factor()),
                        "value": None
                        }

                    self.areas[f"Button {slot_num} Selected Object Indicator"] = selected_object_indicator

                elif collection_objects:
                    x = cur_width_pos + floor(button_size / 4)
                    y = cur_height_pos - button_size / 2 + 1 * scale_factor()
                    object_indicator = {
                    "vert": (x, y),
                    "width": round(button_size / 2),
                    "height": round(2 * scale_factor()),
                    "value": None
                    }
                    self.areas[f"Button {slot_num} Object Indicator"] = object_indicator

            else:
                x = cur_width_pos + 2 * scale_factor()
                y = cur_height_pos - 2 * scale_factor()
                X_icon = {
                    "vert": (x, y),
                    "width": button_size - 4 * scale_factor(),
                    "height": button_size - 4 * scale_factor(),
                    "value": None
                    }

                self.areas[f"X_icon {slot_num}"] = X_icon

            cur_width_pos += button_size
            cur_width_pos += button_gap

    get_buttons(button_row_1_a, 1)
    get_buttons(button_row_1_b, 6)
    get_buttons(button_row_2_a, 11)
    get_buttons(button_row_2_b, 16)


    # UPDATE DYNAMIC DIMENSIONS
    width = button_row_1_a["width"] + button_group_gap + button_row_1_b["width"]
    height = button_row_1_a["height"] + button_gap + button_row_2_a["height"]
    update_area_dimensions(main_button_area, width, height)

    width = main_button_area["width"] + mba_indent_x + mba_outdent_x
    height = main_button_area["height"] + mba_indent_y * 2 + window_title["height"] + wt_y_offset
    update_area_dimensions(main_window, width, height)

    update_area_dimensions(grab_bar, main_window["width"])


def draw_callback_px(self, context):
    allocate_main_ui(self, context)

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    line_shader = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')

    addon_prefs = context.preferences.addons[__package__].preferences

    # main window background
    main_window = self.areas["Main Window"]
    outline_color = addon_prefs.qcd_ogl_widget_menu_back_outline
    background_color = addon_prefs.qcd_ogl_widget_menu_back_inner
    draw_rounded_rect(main_window, line_shader, outline_color[:], outline=True)
    draw_rounded_rect(main_window, shader, background_color)

    # draw window title
    window_title = self.areas["Window Title"]
    x = window_title["vert"][0]
    y = window_title["vert"][1]
    h = window_title["height"]
    text = window_title["value"]
    text_color = addon_prefs.qcd_ogl_widget_menu_back_text
    font_id = 0
    blf.position(font_id, x, y, 0)
    blf.size(font_id, int(h))
    blf.color(font_id, text_color[0], text_color[1], text_color[2], 1)
    blf.draw(font_id, text)

    in_tooltip_area = False
    tooltip_slot_idx = None

    for num in range(20):
        slot_num = num + 1
        qcd_slot_name = internals.qcd_slots.get_name(f"{slot_num}")
        if qcd_slot_name:
            qcd_laycol = internals.layer_collections[qcd_slot_name]["ptr"]
            collection_objects = qcd_laycol.collection.objects
            selected_objects = get_move_selection()
            active_object = get_move_active()
            button_area = self.areas[f"Button {slot_num}"]

            # colors
            button_color = addon_prefs.qcd_ogl_widget_tool_inner
            icon_color = addon_prefs.qcd_ogl_widget_tool_text
            if not qcd_laycol.exclude:
                button_color = addon_prefs.qcd_ogl_widget_tool_inner_sel
                icon_color = addon_prefs.qcd_ogl_widget_tool_text_sel

            if mouse_in_area(self.mouse_pos, button_area):
                in_tooltip_area = True
                tooltip_slot_idx = slot_num

                mod = 0.1

                if button_color[0] + mod > 1 or button_color[1] + mod > 1 or button_color[2] + mod > 1:
                    mod = -mod

                button_color = (
                    button_color[0] + mod,
                    button_color[1] + mod,
                    button_color[2] + mod,
                    button_color[3]
                    )


            # button roundness
            tl = tr = bl = br = 0
            rounding = 5

            if num < 10:
                if not internals.qcd_slots.contains(idx=f"{num+2}"):
                    tr = rounding

                if not internals.qcd_slots.contains(idx=f"{num}"):
                    tl = rounding
            else:
                if not internals.qcd_slots.contains(idx=f"{num+2}"):
                    br = rounding

                if not internals.qcd_slots.contains(idx=f"{num}"):
                    bl = rounding

            if num in [0,5]:
                tl = rounding
            elif num in [4,9]:
                tr = rounding
            elif num in [10,15]:
                bl = rounding
            elif num in [14,19]:
                br = rounding

            # draw button
            outline_color = addon_prefs.qcd_ogl_widget_tool_outline
            draw_rounded_rect(button_area, line_shader, outline_color[:], tl, tr, bl, br, outline=True)
            draw_rounded_rect(button_area, shader, button_color, tl, tr, bl, br)

            # ACTIVE OBJECT
            if active_object and active_object in selected_objects and active_object.name in collection_objects:
                active_object_indicator = self.areas[f"Button {slot_num} Active Object Indicator"]

                vertices = get_circle_coords(active_object_indicator)
                batch = batch_for_shader(shader, 'TRI_FAN', {"pos": vertices})
                shader.bind()
                shader.uniform_float("color", icon_color[:] + (1,))

                gpu.state.blend_set('ALPHA')

                batch.draw(shader)

                gpu.state.blend_set('NONE')

            # SELECTED OBJECTS
            elif not set(selected_objects).isdisjoint(collection_objects):
                selected_object_indicator = self.areas[f"Button {slot_num} Selected Object Indicator"]

                alpha = addon_prefs.qcd_ogl_selected_icon_alpha
                vertices = get_circle_coords(selected_object_indicator)
                line_shader.uniform_float("lineWidth", 2 * scale_factor())
                color = icon_color[:] + (alpha,)
                batch = batch_for_shader(line_shader, 'LINE_STRIP', {"pos": [(v[0], v[1], 0) for v in vertices], "color": [color for v in vertices]})
                shader.bind()

                gpu.state.blend_set('ALPHA')

                batch.draw(line_shader)

                gpu.state.blend_set('NONE')

            # OBJECTS
            elif collection_objects:
                object_indicator = self.areas[f"Button {slot_num} Object Indicator"]

                alpha = addon_prefs.qcd_ogl_objects_icon_alpha
                vertices, indices = get_coords(object_indicator)
                batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
                shader.bind()
                shader.uniform_float("color", icon_color[:] + (alpha,))

                gpu.state.blend_set('ALPHA')

                batch.draw(shader)

                gpu.state.blend_set('NONE')


        # X ICON
        else:
            X_icon = self.areas[f"X_icon {slot_num}"]
            X_icon_color = addon_prefs.qcd_ogl_widget_menu_back_text

            vertices, indices = get_x_coords(X_icon)
            batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
            shader.bind()
            shader.uniform_float("color", X_icon_color[:] + (1,))

            gpu.state.blend_set('ALPHA')

            batch.draw(shader)

            gpu.state.blend_set('NONE')

    if in_tooltip_area:
        if self.draw_tooltip:
            slot_name = internals.qcd_slots.get_name(f"{tooltip_slot_idx}")
            slot_string = f"QCD Slot {tooltip_slot_idx}: \"{slot_name}\"\n"
            hotkey_string = (
                "  * LMB - Move objects to slot.\n"
                "  * Shift+LMB - Toggle objects\' slot."
                )

            draw_tooltip(self, context, shader, line_shader, f"{slot_string}{hotkey_string}")

            self.hover_time = None

        else:
            if not self.hover_time:
                self.hover_time = time.time()


def draw_tooltip(self, context, shader, line_shader, message):
    addon_prefs = context.preferences.addons[__package__].preferences

    font_id = 0
    line_height = 11 * scale_factor()
    text_color = addon_prefs.qcd_ogl_widget_tooltip_text
    blf.size(font_id, int(line_height))
    blf.color(font_id, text_color[0], text_color[1], text_color[2], 1)

    lines = message.split("\n")
    longest = [0,""]
    num_lines = len(lines)

    for line in lines:
        w, _ = blf.dimensions(font_id, line)

        if w > longest[0]:
            longest[0] = w
            longest[1] = line

    w, h = blf.dimensions(font_id, longest[1])

    line_spacer = 1 * scale_factor()
    padding = 4 * scale_factor()

    # draw background
    tooltip = {
        "vert": self.mouse_pos,
        "width": w + spacer()*2,
        "height": (line_height * num_lines + line_spacer * num_lines) + padding*3,
        "value": None
        }

    x = tooltip["vert"][0] - spacer()*2
    y = tooltip["vert"][1] + tooltip["height"] + round(5 * scale_factor())
    tooltip["vert"] = (x, y)

    account_for_view_bounds(tooltip)

    outline_color = addon_prefs.qcd_ogl_widget_tooltip_outline
    background_color = addon_prefs.qcd_ogl_widget_tooltip_inner
    draw_rounded_rect(tooltip, line_shader, outline_color[:], outline=True)
    draw_rounded_rect(tooltip, shader, background_color)

    line_pos = padding + line_height
    # draw text
    for num, line in enumerate(lines):
        x = tooltip["vert"][0] + spacer()
        y = tooltip["vert"][1] - line_pos
        blf.position(font_id, x, y, 0)
        blf.draw(font_id, line)

        line_pos += line_height + line_spacer
