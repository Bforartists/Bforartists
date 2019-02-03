# -*- coding: utf-8 -*-

import bpy
import bgl
import blf
import sys
import os
import datetime
import math

from . sun_calc import degToRad, format_hms
from . properties import Display, Sun

# ---------------------------------------------------------------------------


class MapObject:

    class Origin:
        x = 0
        y = 0

    def __init__(self, t, w, h):
        self.type = t
        self.width = w
        self.height = h
        self.heightFactor = .50
        self.opacity = 1.0
        self.focused = False
        self.view3d_area = None
        self.colorStyle = 'N'
        self.origin = self.Origin()

    def set_dimensions(self, width):
        self.width = width
        self.height = int(width * self.heightFactor)

    def check_focus(self, context, event):
        self.focused = self.is_focused(context, event)
        return self.focused

    def is_focused(self, context, event):
        if context.area != self.view3d_area:
            return False

        x = event.mouse_region_x
        y = event.mouse_region_y

        for reg in self.view3d_area.regions:
            if reg.type == 'WINDOW':
                if x < 0 or x > reg.width:
                    return False
                else:
                    break

        if x < self.origin.x or x > (self.origin.x + self.width) or \
                y < self.origin.y or y > (self.origin.y + self.height) or \
                y < 0 or y > reg.height:
            return False
        return True

    def near_border(self, context, event):
        if context.area != self.view3d_area:
            return False

        x = event.mouse_region_x
        y = event.mouse_region_y

        for reg in self.view3d_area.regions:
            if reg.type == 'WINDOW':
                if x < 20 or x > (reg.width - 20) or \
                        y < 20 or y > (reg.height - 20):
                    return True
                else:
                    break
        return False

# ---------------------------------------------------------------------------


class MapClass:

    class mouse:
        pass

    class grab:

        class spot:
            pass

        class offset:
            pass

    class zoom:
        pass

    class image:
        pass

    def __init__(self):
        self.handler1 = None
        self.handler2 = None
        self.view3d_area = None
        self.draw_region = None
        self.glImage = None
        self.mapLocation = 'VIEWPORT'
        self.init_zoom_preference = True
        self.reset(self.mapLocation)

    def init(self, location):
        self.object = [MapObject('MAP', 0, 0), MapObject('TEXT', 100, 160)]
        self.object[0].set_dimensions(200)
        self.object[1].origin.x = 10
        self.object[1].origin.y = 80
        self.mapLocation = location

    def zoom_preferences(self, invert_zoom_wheel, invert_mouse_zoom):
        self.init_zoom_preference = False
        if invert_zoom_wheel:
            self.zoom.wheel_up = 'OUT'
            self.zoom.wheel_down = 'IN'
        else:
            self.zoom.wheel_up = 'IN'
            self.zoom.wheel_down = 'OUT'
        if invert_mouse_zoom:
            self.zoom.mouse_up = 'IN'
            self.zoom.mouse_down = 'OUT'
        else:
            self.zoom.mouse_up = 'OUT'
            self.zoom.mouse_down = 'IN'

    def reset(self, location):
        self.init(location)
        self.action = None
        self.isActive = False
        self.start = False
        self.stop = False
        self.lockCrosshair = True
        self.showInfo = False
        self.latitude = 0.0
        self.longitude = 0.0
        self.ctrlPress = False
        self.altPress = False
        self.lineWidth = 1.0
        self.textureless = False
        self.mouse.x = 0
        self.mouse.y = 0
        self.grab.spot.x = 0
        self.grab.spot.y = 0
        self.grab.offset.x = 0
        self.grab.offset.y = 0
        self.zoom.width = 0
        self.zoom.x = 0
        self.zoom.y = 0
        self.image.name = None
        self.image.bindcode = 0
        self.image.loaded = False
        self.image.free_it = False

    def clear_callbacks(self):
        if self.mapLocation == 'PANEL':
            pl = bpy.types.SpaceProperties
        else:
            pl = bpy.types.SpaceView3D
        if self.handler2 is not None:
            pl.draw_handler_remove(self.handler2, 'WINDOW')
            self.handler2 = None
        if self.handler1 is not None:
            pl.draw_handler_remove(self.handler1, 'WINDOW')
            self.handler1 = None

    def set_view3d_area(self, area):
        for obj in self.object:
            obj.view3d_area = area

    def activate(self, context):
        if context.area.type == 'PROPERTIES':
            self.reset(self.mapLocation)

            def fw(self, context):
                if self.mapLocation == 'PANEL':
                    self.draw_region = context.region
                areas = bpy.context.screen.areas
                for area in areas:
                    if area.type == 'VIEW_3D':
                        self.view3d_area = context.area
                        if self.mapLocation == 'PANEL':
                            return True
                        for reg in area.regions:
                            if reg.type == 'WINDOW':
                                self.draw_region = reg
                                Display.refresh()
                                return True
                return False
            if not fw(self, context):
                self.draw_region = context.region

            self.set_view3d_area(self.view3d_area)
            self.start = True
            if self.mapLocation == 'PANEL':
                self.handler1 = bpy.types.SpaceProperties.draw_handler_add(
                    Map_load_callback,
                    (self, context), 'WINDOW', 'POST_PIXEL')
            else:
                self.handler1 = bpy.types.SpaceView3D.draw_handler_add(
                    Map_load_callback,
                    (self, context), 'WINDOW', 'POST_PIXEL')
            self.isActive = True
            return True
        else:
            return False

    def activateBGLcallback(self, context):
        if self.mapLocation == 'PANEL':
            self.handler2 = bpy.types.SpaceProperties.draw_handler_add(
                Draw_map_callback,
                (self, context), 'WINDOW', 'POST_PIXEL')
        else:
            self.handler2 = bpy.types.SpaceView3D.draw_handler_add(
                Draw_map_callback,
                (self, context), 'WINDOW', 'POST_PIXEL')
        self.view3d_area = context.area
        self.set_view3d_area(self.view3d_area)
        bpy.ops.sunpos.map('INVOKE_DEFAULT')

    def deactivate(self):
        self.clear_callbacks()
        self.stop = False
        self.action = None
        self.image.loaded = False
        if self.glImage is not None:
            try:
                if self.glImage.bindcode == self.image.bindcode:
                    self.glImage.gl_free()
                    bpy.data.images.remove(self.glImage)
            except:
                pass
        self.image.free_it = False
        self.glImage = None
        self.image.bindcode = 0
        self.isActive = False
        if Sun.SP:
            Sun.SP.ShowMap = False

    def load_blender_image(self, file_name):
        if file_name == "None":
            self.textureless = True
            self.object[0].heightFactor = .5
            return True
        else:
            self.textureless = False

        # S.L. fix to use any relative path
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.image.name = dir_path + os.path.sep + file_name
        if os.path.exists(self.image.name):
            try:
                self.glImage = bpy.data.images.load(self.image.name)
                if self.glImage is not None:
                    self.image.loaded = True
                    self.glImage.user_clear()
                    self.object[0].heightFactor = \
                        self.glImage.size[1] / self.glImage.size[0]
                    return True
                else:
                    return False
            except:
                pass
        return False

    def load_gl_image(self):
        for i in range(1, 6):  # Make up to 6 tries to load image
            self.glImage.gl_load(bgl.GL_NEAREST, bgl.GL_NEAREST)
            if self.glImage.bindcode != 0:
                self.image.bindcode = self.glImage.bindcode
                return True
        return False

    def show_text_in_viewport(self, text):

        def text_line(fx, fy, reduce, c, str):
            bgl.glColor4f(c[0], c[1], c[2], c[3])
            blf.position(0, fx, fy, 0)
            blf.draw(0, str)
            if reduce:
                fy -= 20
            return fy

        if text.colorStyle == 'N':
            tColor = (0.8, 0.8, 0.8, 1.0)
            vColor = (1.0, 1.0, 1.0, 1.0)
        else:
            tColor = (0.0, 0.0, 0.0, 1.0)
            vColor = (0.23, 0.09, 0.18, 1.0)

        blf.size(0, 14, 72)
        fx = text.origin.x
        fy = text.origin.y + 140
        fy = text_line(fx + 10, fy, True, tColor, str(Sun.SP.Month) +
                       " / " + str(Sun.SP.Day) +
                       " / " + str(Sun.SP.Year))

        fy = text_line(fx, fy, False, tColor, "  Day: ")
        fy = text_line(fx + 40, fy, True, vColor, str(Sun.SP.Day_of_year))
        fy = text_line(fx, fy, False, tColor, "Time: ")
        fy = text_line(fx + 40, fy, True, vColor, format_hms(Sun.SP.Time))

        if Sun.ShowRiseSet:
            fy -= 10
            fy = text_line(fx, fy, True, tColor, "Solar Noon:")
            fy = text_line(fx + 14, fy, True, vColor,
                           format_hms(Sun.SolarNoon.time))
            fy -= 10
            fy = text_line(fx, fy, False, tColor, "Rise: ")
            if Sun.RiseSetOK:
                fy = text_line(fx + 40, fy, True, vColor,
                               format_hms(Sun.Sunrise.time))
            else:
                fy = text_line(fx + 40, fy, True, vColor, "--------")
            fy = text_line(fx, fy, False, tColor, " Set: ")
            if Sun.RiseSetOK:
                fy = text_line(fx + 40, fy, True, vColor,
                               format_hms(Sun.Sunset.time))
            else:
                fy = text_line(fx + 40, fy, True, vColor, "--------")

    def locked_crosshair_event(self, action, event):
        self.mouse.x = event.mouse_region_x
        self.mouse.y = event.mouse_region_y
        self.grab.offset.x = event.mouse_region_x
        self.grab.offset.y = event.mouse_region_y
        self.lockCrosshair = True
        Display.refresh()
        return Map_function[action](event)

    # -----------------------------------------------------------------------

    def event_controller(self, context, event):

        if not Sun.SP.ShowMap or event.type == 'TIMER':
            return {'PASS_THROUGH'}

        mapInFocus = self.object[0].check_focus(context, event)

        if event.type == 'MOUSEMOVE':
            if self.action == None:
                if mapInFocus:
                    if self.object[0].near_border(context, event):
                        return {'PASS_THROUGH'}
                    else:
                        return {'RUNNING_MODAL'}
                else:
                    return {'PASS_THROUGH'}
            if self.action in ('PAN', 'ZOOM', 'TIME', 'DAY', 'G'):
                return self.locked_crosshair_event(self.action, event)

        if event.type in ('LEFT_CTRL', 'LEFT_ALT', 'RIGHT_CTRL', 'RIGHT_ALT'):
            Key_function[event.type](event)
            return {'RUNNING_MODAL'}

        self.object[1].check_focus(context, event)

        if event.type in ('MIDDLEMOUSE', 'LEFTMOUSE', 'G'):
            val = Key_function[event.type](context, event)
            if val:
                return val
        elif event.type in ('RIGHTMOUSE', 'ESC',
                            'T', 'D', 'X', 'Y', 'R', 'S', 'E', 'A', 'O', 'C', 'H', 'F1'):
            Display.refresh()
            return Key_function[event.type](event)

        if self.action in ('PAN', 'ZOOM', 'TIME', 'DAY', 'G', 'O'):
            return self.locked_crosshair_event(self.action, event)

        if not mapInFocus:
            return {'PASS_THROUGH'}

        if self.action in ('X', 'Y'):
            return Map_function[self.action](event)
        else:
            self.mouse.x = event.mouse_region_x
            self.mouse.y = event.mouse_region_y

        if event.type == 'WHEELUPMOUSE':
            wheel_zoom(self.zoom.wheel_up)
        elif event.type == 'WHEELDOWNMOUSE':
            wheel_zoom(self.zoom.wheel_down)
        elif self.action == 'CROSS':
            self.lockCrosshair = False
            Display.refresh()

        return {'RUNNING_MODAL'}

# ---------------------------------------------------------------------------


Map = MapClass()


# ---------------------------------------------------------------------------


def key_Ctrl(event):
    if event.value == 'PRESS':
        Map.ctrlPress = True
    elif event.value == 'RELEASE':
        Map.ctrlPress = False


def key_Alt(event):
    if event.value == 'PRESS':
        Map.altPress = True
    elif event.value == 'RELEASE':
        Map.altPress = False


def key_Esc(event):
    if Map.object[1].focused and Map.showInfo:
        if event.value == 'RELEASE':
            Map.action = None
            Map.showInfo = False
        return {'RUNNING_MODAL'}
    if Map.object[0].focused:
        if Map.action is None:
            Map.stop = True
            return {'FINISHED'}
    if Map.action is not None:
        if event.value == 'RELEASE':
            Map.action = None
        return {'RUNNING_MODAL'}
    return {'PASS_THROUGH'}


def key_LeftMouse(context, event):
    if event.value == 'PRESS':
        if Map.action is not None:
            Map.action = None
            Display.refresh()
            return {'RUNNING_MODAL'}
        elif Map.object[0].focused:
            if Map.object[0].near_border(context, event):
                Map.action = 'BORDER'
                Map.lockCrosshair = True
                return {'PASS_THROUGH'}
            Map.action = 'CROSS'
            Map.lockCrosshair = False
            Display.refresh()
        else:
            return {'PASS_THROUGH'}
    elif event.value == 'RELEASE':
        Map.lockCrosshair = True
        Map.action = None
        Display.refresh()
        return {'PASS_THROUGH'}

    return False


def key_MiddleMouse(context, event):
    if event.value == 'PRESS':
        if Map.object[1].focused and Map.showInfo:
            Map.action = 'G' if Map.action != 'G' else None
            Map.grab.spot.y = event.mouse_region_y
            Map.grab.spot.x = event.mouse_region_x
        elif Map.object[0].focused:
            if Map.ctrlPress:
                map = Map.object[0]
                Map.action = 'ZOOM'
                Map.zoom.width = map.width
                Map.zoom.x = map.origin.x
                Map.zoom.y = map.origin.y
            else:
                Map.action = 'PAN'
            Map.grab.spot.x = event.mouse_region_x
            Map.grab.spot.y = event.mouse_region_y
        else:
            return {'PASS_THROUGH'}
    elif event.value == 'RELEASE':
        Map.action = None
        Map.object[0].focused = False
        Map.object[1].focused = False
        Display.refresh()
    return {'RUNNING_MODAL'}

# ---------------------------------------------------------------------------


def key_A(event):
    if event.value == 'PRESS':
        if Map.object[0].focused:
            Sun.SP.ObjectGroup = 'ANALEMMA'
        else:
            return {'PASS_THROUGH'}
    return {'RUNNING_MODAL'}


def key_C(event):
    if event.value == 'PRESS':
        if Map.object[0].focused or Map.object[1].focused:
            if Map.object[1].colorStyle == 'N':
                Map.object[1].colorStyle = 'R'
            else:
                Map.object[1].colorStyle = 'N'
        else:
            return {'PASS_THROUGH'}
    return {'RUNNING_MODAL'}


def key_E(event):
    if event.value == 'PRESS':
        if Map.object[0].focused:
            Sun.SP.ObjectGroup = 'ECLIPTIC'
        else:
            return {'PASS_THROUGH'}
    return {'RUNNING_MODAL'}


def key_G(context, event):
    if event.value == 'PRESS':
        if Map.object[1].focused and Map.showInfo:
            Map.action = 'G' if Map.action != 'G' else None
            Map.grab.spot.y = event.mouse_region_y
            Map.grab.spot.x = event.mouse_region_x
            Display.refresh()
        elif Map.object[0].focused:
            Map.action = 'PAN' if Map.action != 'PAN' else None
            Map.grab.spot.x = event.mouse_region_x
            Map.grab.spot.y = event.mouse_region_y
            return False
        else:
            return {'PASS_THROUGH'}
    return {'RUNNING_MODAL'}


def key_H(event):
    if event.value == 'PRESS':
        if Map.object[0].focused:
            Map.action = None
            bpy.ops.object.help_operator('INVOKE_DEFAULT')
    return {'RUNNING_MODAL'}


def key_R(event):
    if event.value == 'PRESS':
        if Map.object[0].focused:
            Map.lineWidth += 1.0
            if Map.lineWidth == 4.0:
                Map.lineWidth = 0.0
        else:
            Map.action = None
            return {'PASS_THROUGH'}
    return {'RUNNING_MODAL'}


def key_S(event):
    if event.value == 'PRESS':
        if Map.object[0].focused:
            Map.showInfo = True if not Map.showInfo else False
            Sun.PP.ShowRiseSet = True
            Sun.ShowRiseSet = True
        else:
            return {'PASS_THROUGH'}
    return {'RUNNING_MODAL'}


def key_TDOXY(event):
    if event.value == 'PRESS':
        if Map.object[0].focused:
            Map.grab.spot.x = event.mouse_region_x
            Map.grab.spot.y = event.mouse_region_y
            if event.type == 'T':
                if Map.action == 'TIME':
                    Map.action = None
                    Map.showInfo = False
                else:
                    Map.action = 'TIME'
                    Map.showInfo = True
            elif event.type == 'D':
                if Map.action == 'DAY':
                    Map.action = None
                    Map.showInfo = False
                else:
                    Map.action = 'DAY'
                    Map.showInfo = True
            else:
                Map.action = event.type
        else:
            Map.action = None
            return {'PASS_THROUGH'}
    return {'RUNNING_MODAL'}


# ---------------------------------------------------------------------------

def map_Pan(event):
    return {'RUNNING_MODAL'}


def map_Zoom(event):
    mouse_zoom()
    return {'RUNNING_MODAL'}


def map_Time(event):
    if event.type == 'WHEELUPMOUSE':
        time_change_wheel(Map.zoom.wheel_up)
    elif event.type == 'WHEELDOWNMOUSE':
        time_change_wheel(Map.zoom.wheel_down)
    else:
        time_change()
    return {'RUNNING_MODAL'}


def map_Day(event):
    if event.type == 'WHEELUPMOUSE':
        day_change_wheel(Map.zoom.wheel_up)
    elif event.type == 'WHEELDOWNMOUSE':
        day_change_wheel(Map.zoom.wheel_down)
    else:
        day_change()
    return {'RUNNING_MODAL'}


def map_G(event):
    if Map.grab.offset.x < Map.grab.spot.x:
        off = Map.grab.spot.x - Map.grab.offset.x
        Map.object[1].origin.x -= off
    else:
        off = Map.grab.offset.x - Map.grab.spot.x
        Map.object[1].origin.x += off
    if Map.grab.offset.y < Map.grab.spot.y:
        off = Map.grab.spot.y - Map.grab.offset.y
        Map.object[1].origin.y -= off
    else:
        off = Map.grab.offset.y - Map.grab.spot.y
        Map.object[1].origin.y += off

    Map.grab.spot.x = Map.mouse.x
    Map.grab.spot.y = Map.mouse.y

    return {'RUNNING_MODAL'}


def map_O(event):
    if event.type == 'WHEELUPMOUSE':
        opacity_change_wheel(Map.zoom.wheel_up)
    elif event.type == 'WHEELDOWNMOUSE':
        opacity_change_wheel(Map.zoom.wheel_down)
    else:
        opacity_change()
    Display.refresh()
    return {'RUNNING_MODAL'}


def map_X(event):
    if event.type == 'WHEELUPMOUSE':
        X_change_wheel(Map.zoom.wheel_up)
    elif event.type == 'WHEELDOWNMOUSE':
        X_change_wheel(Map.zoom.wheel_down)
    else:
        Map.mouse.y = Map.grab.spot.y
        Map.mouse.x = event.mouse_region_x
        Map.lockCrosshair = False
    Display.refresh()
    return {'RUNNING_MODAL'}


def map_Y(event):
    if event.type == 'WHEELUPMOUSE':
        Y_change_wheel(Map.zoom.wheel_up)
    elif event.type == 'WHEELDOWNMOUSE':
        Y_change_wheel(Map.zoom.wheel_down)
    else:
        Map.mouse.x = Map.grab.spot.x
        Map.mouse.y = event.mouse_region_y
        Map.lockCrosshair = False
    Display.refresh()
    return {'RUNNING_MODAL'}

############################################################################

Key_function = dict([('LEFT_CTRL', key_Ctrl), ('LEFT_ALT', key_Alt),
                     ('RIGHT_CTRL', key_Ctrl), ('RIGHT_ALT', key_Alt),
                     ('MIDDLEMOUSE', key_MiddleMouse),
                     ('LEFTMOUSE', key_LeftMouse),
                     ('RIGHTMOUSE', key_Esc), ('ESC', key_Esc),
                     ('A', key_A), ('E', key_E), ('G', key_G), ('C', key_C),
                     ('H', key_H), ('F1', key_H),
                     ('R', key_R), ('S', key_S),
                     ('T', key_TDOXY), ('D', key_TDOXY), ('O', key_TDOXY),
                     ('X', key_TDOXY), ('Y', key_TDOXY)])

# ---------------------------------------------------------------------------

Map_function = dict([('PAN', map_Pan), ('ZOOM', map_Zoom),
                     ('TIME', map_Time), ('DAY', map_Day),
                     ('G', map_G), ('O', map_O),
                     ('X', map_X), ('Y', map_Y)])

############################################################################


def wheel_zoom(action):
    mf = 0.2 if Map.ctrlPress else 0.0
    af = 0.07 if Map.altPress else 0.0
    if action == 'IN':
        scale = 1.10 + mf - af
    else:
        scale = .90 - mf + af
    if Map.object[0].width * scale < 50:
        return
    else:
        Map.object[0].set_dimensions(int(int(Map.object[0].width * scale)))
    x = Map.mouse.x - Map.object[0].origin.x
    y = Map.mouse.y - Map.object[0].origin.y
    Map.object[0].origin.x += x - int(x * scale)
    Map.object[0].origin.y += y - int(y * scale)
    Map.lockCrosshair = True
    Display.refresh()


def mouse_zoom():
    if Map.mouse.y > Map.grab.spot.y:
        s = Map.mouse.y - Map.grab.spot.y
        action = Map.zoom.mouse_up
    elif Map.mouse.y < Map.grab.spot.y:
        s = Map.grab.spot.y - Map.mouse.y
        action = Map.zoom.mouse_down
    else:
        s = 0
        action = Map.zoom.mouse_down

    if action == 'IN':
        scale = 1 + s * .01
    else:
        scale = 1 - s * .006

    w = int(Map.zoom.width * scale)
    if w < 50:
        return
    Map.object[0].set_dimensions(w)
    x = Map.grab.spot.x - Map.zoom.x
    y = Map.grab.spot.y - Map.zoom.y
    Map.object[0].origin.x = x - int(x * scale) + Map.zoom.x
    Map.object[0].origin.y = y - int(y * scale) + Map.zoom.y


# ---------------------------------------------------------------------------


def check_time_boundary():
    if Sun.SP.Time > 24.0:
        Sun.SP.Time += -24.0
    elif Sun.SP.Time < 0.0:
        Sun.SP.Time += 24.0
    Display.refresh()


def time_change_wheel(action):
    if action == 'IN':
        val = 1.0 if not Map.altPress else 0.0166
    else:
        val = -1.0 if not Map.altPress else -0.0166
    mf = 1.5 if Map.ctrlPress else 1.0
    Sun.SP.Time += mf * val
    check_time_boundary()


def time_change():
    if Map.mouse.x == Map.grab.spot.x:
        return
    mf = 50 if Map.ctrlPress else 1000
    if Map.altPress:
        sx = 0.0001 if Map.mouse.x > Map.grab.spot.x else -0.0001
    else:
        sx = (Map.mouse.x - Map.grab.spot.x) / mf
    Sun.SP.Time += sx
    Map.grab.spot.x = Map.mouse.x
    check_time_boundary()

# ---------------------------------------------------------------------------


def day_change_wheel(action):
    wf = wheel_factor(action)
    day_change_bounds(wf)


def day_change():
    if Map.mouse.x == Map.grab.spot.x:
        return
    cf = 1 if Map.ctrlPress else 3
    if Map.altPress:
        mf = 1 if Map.mouse.x > Map.grab.spot.x else -1
    else:
        mf = (Map.mouse.x - Map.grab.spot.x) / cf
    day_change_bounds(mf)
    Map.grab.spot.x = Map.mouse.x


def day_change_bounds(wf):
    if Sun.SP.Day_of_year + wf > 366:
        Sun.SP.Day_of_year = 1
        Sun.SP.Year += 1
    elif Sun.SP.Day_of_year + wf < 1:
        Sun.SP.Day_of_year = 366
        Sun.SP.Year -= 1
    else:
        Sun.SP.Day_of_year += wf
    dt = (datetime.date(Sun.SP.Year, 1, 1) +
          datetime.timedelta(Sun.SP.Day_of_year - 1))
    Sun.SP.Day = dt.day
    Sun.SP.Month = dt.month
    Display.refresh()

# ---------------------------------------------------------------------------


def opacity_change_wheel(action):
    if action == 'IN':
        val = 0.05 if not Map.altPress else 0.01
    else:
        val = -0.05 if not Map.altPress else -0.01
    mf = 1.5 if Map.ctrlPress else 1.0
    obj = Map.object[0]
    obj.opacity += mf * val
    opacity_change_bounds(obj)


def opacity_change():
    if Map.mouse.x > Map.grab.spot.x:
        s = Map.mouse.x - Map.grab.spot.x
        action = '+'
    elif Map.mouse.x < Map.grab.spot.x:
        s = Map.grab.spot.x - Map.mouse.x
        action = '-'
    else:
        action = '-'
        s = 0
    s /= 10
    obj = Map.object[0]

    if action == '+':
        scale = obj.opacity + s * .002
    else:
        scale = obj.opacity - s * .002
    obj.opacity = scale
    opacity_change_bounds(obj)


def opacity_change_bounds(obj):
    if obj.opacity > 1.0:
        obj.opacity = 1.0
        Map.grab.spot.x = Map.mouse.x
    elif obj.opacity < 0.0:
        obj.opacity = 0.0
        Map.grab.spot.x = Map.mouse.x

# ---------------------------------------------------------------------------


def X_change_wheel(action):
    wf = wheel_factor(action)
    if Sun.SP.Longitude + wf > 180.0:
        Sun.SP.Longitude = -180.0
    elif Sun.SP.Longitude + wf < -180.0:
        Sun.SP.Longitude = 180.0
    else:
        Sun.SP.Longitude += wf


def Y_change_wheel(action):
    wf = wheel_factor(action)
    if Sun.SP.Latitude + wf > 90.0:
        Sun.SP.Latitude = -90.0
    elif Sun.SP.Latitude + wf < -90.0:
        Sun.SP.Latitude = 90.0
    else:
        Sun.SP.Latitude += wf


def wheel_factor(action):
    if action == 'IN':
        val = 5.0 if not Map.altPress else 1.0
    else:
        val = -5.0 if not Map.altPress else -1.0
    wf = 3 * val if Map.ctrlPress else 1.0 * val
    return wf

############################################################################


def Map_load_callback(self, context):

    if Sun.SP.ShowMap and not Map.image.loaded:
        Map.glImage = None
        if not Map.load_blender_image(Sun.MapName):
            print("Could not load image file: ", Map.image.name)
            Sun.SP.ShowMap = False

    if Map.start:
        def set_region_data():
            Map.activateBGLcallback(context)
            bgl.glTexParameteri(bgl.GL_TEXTURE_2D,
                                bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_LINEAR)
            bgl.glTexParameteri(bgl.GL_TEXTURE_2D,
                                bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)
            Map.object[0].set_dimensions(0)
            Map.toolProps = None
            Map.toolPropsWidth = 0
            for reg in Map.view3d_area.regions:
                if reg.type == 'TOOL_PROPS':
                    Map.toolProps = reg
                    Map.toolProps_width = reg.width
                elif reg.type == 'WINDOW':
                    Map.region = reg
                    Map.saved_region_width = reg.width
                    Map.object[0].set_dimensions(int(reg.width * .8))
                    Map.object[0].origin.x = \
                        int((Map.region.width - Map.object[0].width) / 2)
                    Map.object[0].origin.y = 2
            return

        Map.start = False

        if Map.image.loaded:
            if not Map.load_gl_image():
                print("Could not load image file: ", Map.image.name)
            elif Map.glImage.bindcode != 0:
                Map.image.free_it = True
                set_region_data()
                return
            print("Could not get texture in gl_load()")
            Map.glImage = None
            Map.image.bindcode = 0
            Sun.SP.ShowMap = False

        elif Map.textureless:
            set_region_data()
            return
        else:
            Sun.SP.ShowMap = False
        return

    if Map.stop:
        Map.deactivate()
        return

    return


############################################################################


def Draw_map_callback(self, context):

    if context.area != Map.view3d_area:
        return
    elif context.area.type == 'PROPERTIES' and \
            context.space_data.context != 'WORLD':
        return

    # Check if window area has changed for sticky zoom
    theMap = Map.object[0]
    if Map.region.width < Map.saved_region_width:
        diff = Map.saved_region_width - Map.region.width
        if theMap.origin.x + theMap.width > Map.saved_region_width:
            if theMap.origin.x > 0:
                theMap.origin.x -= diff
            else:
                theMap.width -= diff
        else:
            if Map.toolProps is not None:
                if Map.toolProps.width > Map.toolProps_width:
                    theMap.origin.x -= diff
                Map.toolProps_width = Map.toolProps.width
            if theMap.origin.x < 0:
                theMap.origin.x += diff
    else:
        diff = Map.region.width - Map.saved_region_width
        if theMap.width > Map.saved_region_width:
            theMap.width += diff
        else:
            if Map.toolProps is not None:
                if Map.toolProps.width < Map.toolProps_width:
                    theMap.origin.x += diff
                Map.toolProps_width = Map.toolProps.width
    theMap.set_dimensions(theMap.width)
    Map.saved_region_width = Map.region.width

    # Latitude and longitude are set to an equidistant
    # cylindrical projection with lat/long 0/0 exactly
    # in the middle of the image.

    zLong = theMap.width / 2
    longFac = zLong / 180
    zLat = theMap.height / 2
    latFac = zLat / 90
    crossChange = True

    if not Map.action == 'PAN':
        x = Map.mouse.x
        y = Map.mouse.y
        if x < theMap.origin.x or x > theMap.origin.x + theMap.width:
            crossChange = False
            x = 0
        else:
            testBoundary = theMap.origin.x + theMap.width
            if testBoundary < Map.region.width:
                rightBoundary = testBoundary
            else:
                rightBoundary = Map.region.width
            if x > rightBoundary:
                crossChange = False
                x = rightBoundary
        cX = x - zLong - theMap.origin.x

        if longFac:
            newLongitude = cX / longFac
        else:
            newLongitude = 0.0

        if y < theMap.origin.y or y < 0:
            crossChange = False
            y = 0
        elif y > theMap.origin.y + theMap.height:
            crossChange = False
            y = theMap.origin.y + theMap.height
        cY = y - zLat - theMap.origin.y

        if latFac:
            newLatitude = cY / latFac
        else:
            newLatitude = 0.0

        if newLatitude == Map.latitude and newLongitude == Map.longitude:
            crossChange = False
        else:
            Map.latitude = newLatitude
            Map.longitude = newLongitude
    else:
        if Map.grab.offset.x < Map.grab.spot.x:
            off = Map.grab.spot.x - Map.grab.offset.x
            theMap.origin.x -= off
        else:
            off = Map.grab.offset.x - Map.grab.spot.x
            theMap.origin.x += off
        if Map.grab.offset.y < Map.grab.spot.y:
            off = Map.grab.spot.y - Map.grab.offset.y
            theMap.origin.y -= off
        else:
            off = Map.grab.offset.y - Map.grab.spot.y
            theMap.origin.y += off
        Map.grab.spot.x = Map.mouse.x
        Map.grab.spot.y = Map.mouse.y

    Lx = theMap.origin.x
    Ly = theMap.origin.y

    # ---------------------
    # Draw a textured quad
    # ---------------------

    if not Map.textureless:
        bgl.glEnable(bgl.GL_BLEND)
        if Map.glImage.bindcode == 0:
            Map.load_gl_image()
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, Map.glImage.bindcode[0])
        bgl.glEnable(bgl.GL_TEXTURE_2D)
        bgl.glColor4f(1.0, 1.0, 1.0, Map.object[0].opacity)
        bgl.glBegin(bgl.GL_QUADS)
        bgl.glTexCoord2f(0.0, 0.0)
        bgl.glVertex2f(Lx, Ly)
        bgl.glTexCoord2f(1.0, 0.0)
        bgl.glVertex2f(Lx + theMap.width, Ly)
        bgl.glTexCoord2f(1.0, 1.0)
        bgl.glVertex2f(Lx + theMap.width, Ly + theMap.height)
        bgl.glTexCoord2f(0.0, 1.0)
        bgl.glVertex2f(Lx, theMap.height + Ly)
        bgl.glEnd()
        bgl.glDisable(bgl.GL_TEXTURE_2D)

    # -----------------------
    # Output text for stats
    # -----------------------
    if Map.action == 'TIME' or Map.action == 'DAY' or Map.showInfo:
        Map.show_text_in_viewport(Map.object[1])

    # ---------------------
    # draw the crosshair
    # ---------------------
    x = theMap.width / 2.0
    if crossChange and not Map.lockCrosshair:
        if Map.action != 'Y':
            Sun.SP.Longitude = newLongitude
    longitude = (Sun.SP.Longitude * x / 180.0) + x

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_LINES)
    bgl.glLineWidth(1.0)
    alpha = 1.0 if Map.action == 'Y' else 0.5
    color = (0.894, 0.741, .510, alpha)
    bgl.glColor4f(color[0], color[1], color[2], color[3])
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex2f(Lx + longitude, Ly)
    bgl.glVertex2f(Lx + longitude, Ly + theMap.height)
    bgl.glEnd()

    y = theMap.height / 2.0
    if crossChange and not Map.lockCrosshair:
        if Map.action != 'X':
            Sun.SP.Latitude = newLatitude
    latitude = (Sun.SP.Latitude * y / 90.0) + y

    alpha = 1.0 if Map.action == 'X' else 0.5
    color = (0.894, 0.741, .510, alpha)
    bgl.glColor4f(color[0], color[1], color[2], color[3])
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex2f(Lx, Ly + latitude)
    bgl.glVertex2f(Lx + theMap.width, Ly + latitude)
    bgl.glEnd()

    # ---------------------
    # draw the border
    # ---------------------
    bgl.glDisable(bgl.GL_BLEND)
    color = (0.6, 0.6, .6, 1.0)
    bgl.glColor4f(color[0], color[1], color[2], color[3])
    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glVertex2f(Lx, Ly)
    bgl.glVertex2f(Lx + theMap.width, Ly)
    bgl.glVertex2f(Lx + theMap.width, Ly + theMap.height)
    bgl.glVertex2f(Lx, theMap.height + Ly)
    bgl.glVertex2f(Lx, Ly)
    bgl.glEnd()

    if not Sun.ShowRiseSet or not Map.lineWidth:
        bgl.glDisable(bgl.GL_LINES)
        bgl.glFlush()
        return

    if Map.action == 'G':
        draw_text_region()

    # ------------------------
    # draw the sunrise, sunset
    # ------------------------

    def draw_angled_line(color, angle, bx, by):
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius
        bgl.glColor4f(color[0], color[1], color[2], color[3])
        bgl.glBegin(bgl.GL_LINES)
        bgl.glVertex2f(bx, by)
        bgl.glVertex2f(bx + x, by + y)
        bgl.glEnd()

    px = Lx + longitude
    py = Ly + latitude

    radius = 30 + Map.lineWidth * 10
    if Sun.RiseSetOK and Map.lineWidth:
        color = (0.2, 0.6, 1.0, 0.9)
        angle = -(degToRad(Sun.Sunrise.azimuth) - math.pi / 2)
        bgl.glLineWidth(Map.lineWidth)
        draw_angled_line(color, angle, px, py)

        color = (0.86, 0.18, 0.18, 0.9)
        angle = -(degToRad(Sun.Sunset.azimuth) - math.pi / 2)
        draw_angled_line(color, angle, px, py)

    # ------------------------
    # draw current time line
    # ------------------------

    if Map.textureless:
        phi = degToRad(Sun.AzNorth) * -1
    else:
        phi = degToRad(Sun.Azimuth) * -1
    x = math.sin(phi) * math.sin(-Sun.Theta) * (radius + 10)
    y = math.sin(Sun.Theta) * math.cos(phi) * (radius + 10)
    night = (0.24, 0.29, 0.94, 0.9)
    day = (0.85, 0.77, 0.60, 0.9)
    if Sun.SolarNoon.elevation < 0.0:
        color = night
    elif Sun.Elevation >= Sun.Sunrise.elevation:
        if Sun.Time >= Sun.Sunset.time and \
                Sun.Elevation <= Sun.Sunset.elevation:
            color = night
        else:
            color = day
    else:
        color = night
    bgl.glLineWidth(Map.lineWidth + 1.0)

    bgl.glColor4f(color[0], color[1], color[2], color[3])
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex2f(px, py)
    bgl.glVertex2f(px + x, py + y)
    bgl.glEnd()
    bgl.glLineWidth(1.0)
    bgl.glDisable(bgl.GL_LINES)
    bgl.glFlush()

# ---------------------------------------------------------------------------


def draw_text_region():
    x = Map.object[1].origin.x
    y = Map.object[1].origin.y - 5

    bgl.glEnable(bgl.GL_BLEND)
    color = (0.894, 0.741, .510, 0.2)
    bgl.glColor4f(color[0], color[1], color[2], color[3])
    bgl.glBegin(bgl.GL_QUADS)
    bgl.glVertex2f(x, y)
    bgl.glVertex2f(x + Map.object[1].width, y)
    bgl.glVertex2f(x + Map.object[1].width, y + Map.object[1].height)
    bgl.glVertex2f(x, Map.object[1].height + y)
    bgl.glEnd()
    bgl.glDisable(bgl.GL_BLEND)


# ---------------------------------------------------------------------------


class SunPos_Help(bpy.types.Operator):
    bl_idname = "object.help_operator"
    bl_label = "Map help"

    def execute(self, context):
        self.report({'INFO'}, self.message)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=400, height=200)

    def draw(self, context):
        self.layout.label(text="Available map commands:")

        row = self.layout.row()
        split = row.split(percentage=.27)
        colL = split.column()
        colR = split.column()
        colL.label(text="Esc or Right Mouse ")
        colR.label("Close map or text.")
        colL.label(text="Left Mouse")
        colR.label(text="Move crosshair.")
        colL.label(text="G or MiddleMouse")
        colR.label("Pan mode. Grab and move map or text.")
        colL.label(text="Ctrl Middlemouse")
        colR.label(text="Mouse zoom to point.")
        colL.label(text="C")
        colR.label("Invert text color.")
        colL.label(text="R")
        colR.label(text="Toggle through thickness of the radiating rise/set lines.")
        colL.label(text="S")
        colR.label(text="Show statistics data. Move with pan command.")
        self.layout.label("----- The following are changed by moving " +
                          "the mouse or using the scroll wheel.")
        self.layout.label(text="----- Use Ctrl for coarse increments or Alt for fine.")
        row = self.layout.row()
        split = row.split(percentage=.25)
        colL = split.column()
        colR = split.column()
        colL.label(text="Scroll wheel")
        colR.label(text="Zoom to point.")
        colL.label(text="T")
        colR.label(text="Time mode.")
        colL.label(text="D")
        colR.label(text="Day mode.")
        colL.label(text="O")
        colR.label(text="Change map opacity.")
        colL.label(text="X")
        colR.label(text="Lock latitude and change longitude.")
        colL.label(text="Y")
        colR.label(text="Lock longitude and change latitude.")
        colL.label(text="A")
        colR.label(text="Show analemma if object group is set.")
        colL.label(text="E")
        colR.label(text="Show ecliptic if object group is set.")
