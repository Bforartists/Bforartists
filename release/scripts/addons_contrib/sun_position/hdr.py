# -*- coding: utf-8 -*-

import bpy
import bgl
import blf
import sys
import os
import math

from . sun_calc import degToRad, radToDeg, format_hms
from . properties import Display, Sun

# ---------------------------------------------------------------------------


class HdrObject:

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


class HdrClass:

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

    class last:
        pass

    def __init__(self):
        self.handler1 = None
        self.handler2 = None
        self.view3d_area = None
        self.draw_region = None
        self.glImage = None
        self.init_zoom_preference = True
        self.reset()
        self.last.filename = None
        self.last.image = None
        self.last.pixels = None
        self.last.projection = None

    def init(self):
        self.object = [HdrObject('MAP', 0, 0), HdrObject('TEXT', 100, 160)]
        self.object[0].set_dimensions(200)
        self.object[1].origin.x = 10
        self.object[1].origin.y = 80

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

    def reset(self):
        self.init()
        self.action = None
        self.isActive = False
        self.start = False
        self.stop = False
        self.lockCrosshair = True
        self.elevation = 0.0
        self.azimuth = 0.0
        self.ctrlPress = False
        self.altPress = False
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
        if self.handler2 is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self.handler2, 'WINDOW')
            self.handler2 = None
        if self.handler1 is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self.handler1, 'WINDOW')
            self.handler1 = None

    def set_view3d_area(self, area):
        for obj in self.object:
            obj.view3d_area = area

    def activate(self, context):
        if context.area.type == 'PROPERTIES':
            self.reset()

            def fw(self, context):
                self.draw_region = context.region
                areas = bpy.context.screen.areas
                for area in areas:
                    if area.type == 'VIEW_3D':
                        self.view3d_area = context.area
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
            self.handler1 = bpy.types.SpaceView3D.draw_handler_add(
                Hdr_load_callback,
                (self, context), 'WINDOW', 'POST_PIXEL')
            self.isActive = True
            return True
        else:
            return False

    def activateBGLcallback(self, context):
        self.handler2 = bpy.types.SpaceView3D.draw_handler_add(
            Draw_hdr_callback, (self, context), 'WINDOW', 'POST_PIXEL')
        self.view3d_area = context.area
        self.set_view3d_area(self.view3d_area)
        bpy.ops.sunpos.hdr('INVOKE_DEFAULT')

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
            Sun.SP.ShowHdr = False
            Sun.SP.BindToSun = True
        Sun.BindToSun = False
        Display.refresh()

    def make_dummy_file(self, file_name):
        fname = file_name.replace("\\", "/")
        if os.path.exists(fname):
            return False
        else:
            return True

    def load_blender_image(self, file_name):
        fn = file_name
        self.image.name = fn.replace("\\", "/")
        if os.path.exists(self.image.name):
            try:
                self.glImage = bpy.data.images.load(self.image.name)
                self.glImage.pixels = self.last.pixels
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

    def locked_crosshair_event(self, action, event):
        self.mouse.x = event.mouse_region_x
        self.mouse.y = event.mouse_region_y
        self.grab.offset.x = event.mouse_region_x
        self.grab.offset.y = event.mouse_region_y
        self.lockCrosshair = True
        Display.refresh()
        return Hdr_function[action](event)

    # -----------------------------------------------------------------------

    def event_controller(self, context, event):

        if not Sun.SP.ShowHdr or event.type == 'TIMER':
            return {'PASS_THROUGH'}

        hdrInFocus = self.object[0].check_focus(context, event)

        if event.type == 'MOUSEMOVE':
            if self.action == None:
                if hdrInFocus:
                    if self.object[0].near_border(context, event):
                        return {'PASS_THROUGH'}
                    else:
                        return {'RUNNING_MODAL'}
                else:
                    return {'PASS_THROUGH'}
            if self.action in ('PAN', 'ZOOM', 'G'):
                return self.locked_crosshair_event(self.action, event)

        if event.type in ('LEFT_CTRL', 'LEFT_ALT', 'RIGHT_CTRL', 'RIGHT_ALT'):
            Key_function[event.type](event)
            return {'RUNNING_MODAL'}

        self.object[1].check_focus(context, event)

        if event.type in ('MIDDLEMOUSE', 'LEFTMOUSE', 'G'):
            val = Key_function[event.type](context, event)
            if val:
                return val
        elif event.type in ('RIGHTMOUSE', 'ESC', 'H', 'F1'):
            Display.refresh()
            return Key_function[event.type](event)

        if self.action in ('PAN', 'ZOOM', 'G'):
            return self.locked_crosshair_event(self.action, event)

        if not hdrInFocus:
            return {'PASS_THROUGH'}

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


Hdr = HdrClass()


# ---------------------------------------------------------------------------


def key_Ctrl(event):
    if event.value == 'PRESS':
        Hdr.ctrlPress = True
    elif event.value == 'RELEASE':
        Hdr.ctrlPress = False


def key_Alt(event):
    if event.value == 'PRESS':
        Hdr.altPress = True
    elif event.value == 'RELEASE':
        Hdr.altPress = False


def key_Esc(event):
    if Hdr.object[0].focused:
        if Hdr.action is None:
            Hdr.stop = True
            return {'FINISHED'}
    if Hdr.action is not None:
        if event.value == 'RELEASE':
            Hdr.action = None
        return {'RUNNING_MODAL'}
    return {'PASS_THROUGH'}


def key_LeftMouse(context, event):
    if event.value == 'PRESS':
        if Hdr.action is not None:
            Hdr.action = None
            Display.refresh()
            return {'RUNNING_MODAL'}
        elif Hdr.object[0].focused:
            if Hdr.object[0].near_border(context, event):
                Hdr.action = 'BORDER'
                Hdr.lockCrosshair = True
                return {'PASS_THROUGH'}
            Hdr.action = 'CROSS'
            Hdr.lockCrosshair = False
            Display.refresh()
        else:
            return {'PASS_THROUGH'}
    elif event.value == 'RELEASE':
        Hdr.lockCrosshair = True
        Hdr.action = None
        Display.refresh()
        return {'PASS_THROUGH'}

    return False


def key_MiddleMouse(context, event):
    if event.value == 'PRESS':
        if Hdr.object[0].focused:
            if Hdr.ctrlPress:
                hdr = Hdr.object[0]
                Hdr.action = 'ZOOM'
                Hdr.zoom.width = hdr.width
                Hdr.zoom.x = hdr.origin.x
                Hdr.zoom.y = hdr.origin.y
            else:
                Hdr.action = 'PAN' if Hdr.action != 'PAN' else None
            Hdr.grab.spot.x = event.mouse_region_x
            Hdr.grab.spot.y = event.mouse_region_y
            return False
        else:
            return {'PASS_THROUGH'}
    elif event.value == 'RELEASE':
        Hdr.action = None
        Hdr.object[0].focused = False
        Hdr.object[1].focused = False
        Display.refresh()
    return {'RUNNING_MODAL'}

# ---------------------------------------------------------------------------


def key_G(context, event):
    if event.value == 'PRESS':
        if Hdr.object[0].focused:
            Hdr.action = 'PAN' if Hdr.action != 'PAN' else None
            Hdr.grab.spot.x = event.mouse_region_x
            Hdr.grab.spot.y = event.mouse_region_y
            return False
        else:
            return {'PASS_THROUGH'}
    return {'RUNNING_MODAL'}


def key_H(event):
    if event.value == 'PRESS':
        if Hdr.object[0].focused:
            Hdr.action = None
            bpy.ops.object.hdrhelp_operator('INVOKE_DEFAULT')
    return {'RUNNING_MODAL'}


# ---------------------------------------------------------------------------

def hdr_Pan(event):
    return {'RUNNING_MODAL'}


def hdr_Zoom(event):
    mouse_zoom()
    return {'RUNNING_MODAL'}


def hdr_G(event):
    if Hdr.grab.offset.x < Hdr.grab.spot.x:
        off = Hdr.grab.spot.x - Hdr.grab.offset.x
        Hdr.object[1].origin.x -= off
    else:
        off = Hdr.grab.offset.x - Hdr.grab.spot.x
        Hdr.object[1].origin.x += off
    if Hdr.grab.offset.y < Hdr.grab.spot.y:
        off = Hdr.grab.spot.y - Hdr.grab.offset.y
        Hdr.object[1].origin.y -= off
    else:
        off = Hdr.grab.offset.y - Hdr.grab.spot.y
        Hdr.object[1].origin.y += off

    Hdr.grab.spot.x = Hdr.mouse.x
    Hdr.grab.spot.y = Hdr.mouse.y

    return {'RUNNING_MODAL'}


############################################################################

Key_function = dict([('LEFT_CTRL', key_Ctrl), ('LEFT_ALT', key_Alt),
                     ('RIGHT_CTRL', key_Ctrl), ('RIGHT_ALT', key_Alt),
                     ('MIDDLEMOUSE', key_MiddleMouse),
                     ('LEFTMOUSE', key_LeftMouse),
                     ('RIGHTMOUSE', key_Esc), ('ESC', key_Esc),
                     ('G', key_G), ('H', key_H), ('F1', key_H)])

# ---------------------------------------------------------------------------

Hdr_function = dict([('PAN', hdr_Pan), ('ZOOM', hdr_Zoom),
                     ('G', hdr_G)])

############################################################################


def wheel_zoom(action):
    mf = 0.2 if Hdr.ctrlPress else 0.0
    af = 0.07 if Hdr.altPress else 0.0
    if action == 'IN':
        scale = 1.10 + mf - af
    else:
        scale = .90 - mf + af
    if Hdr.object[0].width * scale < 50:
        return
    else:
        Hdr.object[0].set_dimensions(int(int(Hdr.object[0].width * scale)))
    x = Hdr.mouse.x - Hdr.object[0].origin.x
    y = Hdr.mouse.y - Hdr.object[0].origin.y
    Hdr.object[0].origin.x += x - int(x * scale)
    Hdr.object[0].origin.y += y - int(y * scale)
    Hdr.lockCrosshair = True
    Display.refresh()


def mouse_zoom():
    if Hdr.mouse.y > Hdr.grab.spot.y:
        s = Hdr.mouse.y - Hdr.grab.spot.y
        action = Hdr.zoom.mouse_up
    elif Hdr.mouse.y < Hdr.grab.spot.y:
        s = Hdr.grab.spot.y - Hdr.mouse.y
        action = Hdr.zoom.mouse_down
    else:
        s = 0
        action = Hdr.zoom.mouse_down

    if action == 'IN':
        scale = 1 + s * .01
    else:
        scale = 1 - s * .006

    w = int(Hdr.zoom.width * scale)
    if w < 50:
        return
    Hdr.object[0].set_dimensions(w)
    x = Hdr.grab.spot.x - Hdr.zoom.x
    y = Hdr.grab.spot.y - Hdr.zoom.y
    Hdr.object[0].origin.x = x - int(x * scale) + Hdr.zoom.x
    Hdr.object[0].origin.y = y - int(y * scale) + Hdr.zoom.y


# --------------------------------------------------------------------------


############################################################################


def Hdr_load_callback(self, context):

    def remove_imagedata(name):
        bd = bpy.data
        for i in bd.images:
            if i.name == name:
                bd.images.remove(i)

    if Sun.SP.ShowHdr and not Hdr.image.loaded:
        Hdr.glImage = None
        fileName = None
        projection = "EQUIRECTANGULAR"
        try:
            nt = bpy.context.scene.world.node_tree.nodes
            envTex = nt.get(Sun.HDR_texture)
            if envTex.type != "TEX_ENVIRONMENT":
                Sun.SP.ShowHdr = False
            elif envTex.image == None:
                Sun.SP.ShowHdr = False
            else:
                envTex.texture_mapping.rotation.z = 0.0
                projection = envTex.projection
                prefs = bpy.context.preferences
                fileName = prefs.filepaths.temporary_directory + "tmpSun.png"

                st = envTex.image.copy()
                if projection == "MIRROR_BALL":
                    st.scale(256, 256)
                    Hdr.last.image = st.copy()
                    Hdr.last.image.scale(512, 256)
                    ConvertToLatLong(st, Hdr.last.image)
                else:
                    st.scale(512, 256)
                    Hdr.last.image = st.copy()
                    Hdr.last.image.scale(512, 256)

                if Hdr.make_dummy_file(fileName) == True:
                    Hdr.last.image.save_render(fileName)
                Hdr.last.pixels = list(Hdr.last.image.pixels)
        except:
            pass

        if Sun.SP.ShowHdr:
            if not Hdr.load_blender_image(fileName):
                print("Could not load image file: ", Hdr.image.name)
                Sun.SP.ShowHdr = False
            else:
                try:
                    nt = bpy.context.scene.world.node_tree.nodes
                    envTex = nt.get(Sun.HDR_texture)
                    if projection == "MIRROR_BALL":
                        envTex.texture_mapping.rotation.z = degToRad(270.0)
                    else:
                        envTex.texture_mapping.rotation.z = degToRad(90.0)
                except:
                    pass

    if Hdr.start:
        def set_region_data():
            Hdr.activateBGLcallback(context)
            bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER,
                                bgl.GL_LINEAR)
            bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER,
                                bgl.GL_LINEAR)
            Hdr.object[0].set_dimensions(0)
            Hdr.toolProps = None
            Hdr.toolPropsWidth = 0
            for reg in Hdr.view3d_area.regions:
                if reg.type == 'TOOL_PROPS':
                    Hdr.toolProps = reg
                    Hdr.toolProps_width = reg.width
                elif reg.type == 'WINDOW':
                    Hdr.region = reg
                    Hdr.saved_region_width = reg.width
                    Hdr.object[0].set_dimensions(int(reg.width * .5))
                    Hdr.object[0].origin.x = \
                        int((Hdr.region.width - Hdr.object[0].width) / 2)
                    Hdr.object[0].origin.y = 2
            return

        Hdr.start = False
        if Hdr.image.loaded:
            if not Hdr.load_gl_image():
                print("Could not load image file: ", Hdr.image.name)
            elif Hdr.glImage.bindcode != 0:
                Hdr.image.free_it = True
                set_region_data()
                return
            print("Could not get texture in gl_load()")
            Hdr.glImage = None
            Hdr.image.bindcode = 0
            Sun.SP.ShowHdr = False
        else:
            Sun.SP.ShowHdr = False
        return

    if Hdr.stop:
        Hdr.deactivate()
        return

    return


############################################################################
# Thanks to Domino for the Pixel and ImageBuffer classes
############################################################################


class Pixel:

    def __init__(self, r=0.0, g=0.0, b=0.0, a=None, colour=None):
        self.r = r
        self.g = g
        self.b = b
        self.a = a
        if colour:
            self.r = colour[0]
            self.g = colour[1]
            self.b = colour[2]
            if len(colour) > 3:
                self.a = colour[3]
        if self.a is None:
            self.a = 1.0

    def as_tuple(self):
        return (self.r, self.g, self.b, self.a)


class ImageBuffer:

    def __init__(self, image, clear=False):
        self.image = image
        self.x, self.y = self.image.size
        if clear:
            self.clear()
        else:
            self.buffer = list(self.image.pixels)

    def update(self):
        self.image.pixels = self.buffer

    def _index(self, x, y):
        if x < 0 or y < 0 or x >= self.x or y >= self.y:
            return None
        return (x + y * self.x) * 4

    def clear(self):
        self.buffer = [0.0 for i in range(self.x * self.y * 4)]

    def set_pixel(self, x, y, colour):
        index = self._index(x, y)
        if index is not None:
            self.buffer[index:index + 4] = colour.as_tuple()

    def get_pixel(self, x, y):
        index = self._index(x, y)
        if index is not None:
            return Pixel(colour=self.buffer[index:index + 4])
        else:
            return None


def ConvertToLatLong(inpic, outpic):

    width = inpic.size[0]
    height = inpic.size[1]

    uv_width = width * 2 - 1
    uv_height = height - 1

    pc_width = 0.5 * width
    pc_height = 0.5 * height

    p_in = ImageBuffer(inpic)
    p_out = ImageBuffer(outpic)
    p_out.clear()

    flip = width * 2 - 1

    for col in range(0, width * 2):
        phi = (col / uv_width) * 2 * math.pi
        for row in range(0, height):
            theta = (1 - row / uv_height) * math.pi
            m = math.sqrt(2 * (1 + math.sin(-theta) * math.sin(phi)))
            x = int((math.sin(theta) * math.cos(phi) / m + 1) * pc_width)
            y = int((math.cos(theta) / m + 1) * pc_height)
            pixel = p_in.get_pixel(x, y)
            p_out.set_pixel(flip - col, row, pixel)
    p_out.update()


############################################################################


def Draw_hdr_callback(self, context):

    if context.area != Hdr.view3d_area:
        return
    elif context.area.type == 'PROPERTIES' and \
            context.space_data.context != 'WORLD':
        return

    # Check if window area has changed for sticky zoom
    theHdr = Hdr.object[0]
    if Hdr.region.width < Hdr.saved_region_width:
        diff = Hdr.saved_region_width - Hdr.region.width
        if theHdr.origin.x + theHdr.width > Hdr.saved_region_width:
            if theHdr.origin.x > 0:
                theHdr.origin.x -= diff
            else:
                theHdr.width -= diff
        else:
            if Hdr.toolProps is not None:
                if Hdr.toolProps.width > Hdr.toolProps_width:
                    theHdr.origin.x -= diff
                Hdr.toolProps_width = Hdr.toolProps.width
            if theHdr.origin.x < 0:
                theHdr.origin.x += diff
    else:
        diff = Hdr.region.width - Hdr.saved_region_width
        if theHdr.width > Hdr.saved_region_width:
            theHdr.width += diff
        else:
            if Hdr.toolProps is not None:
                if Hdr.toolProps.width < Hdr.toolProps_width:
                    theHdr.origin.x += diff
                Hdr.toolProps_width = Hdr.toolProps.width
    theHdr.set_dimensions(theHdr.width)
    Hdr.saved_region_width = Hdr.region.width

    zAzim = theHdr.width / 2
    azimFac = zAzim / 180
    zElev = theHdr.height / 2
    elevFac = zElev / 90
    crossChange = True

    if not Hdr.action == 'PAN':
        x = Hdr.mouse.x
        y = Hdr.mouse.y
        if x < theHdr.origin.x or x > theHdr.origin.x + theHdr.width:
            crossChange = False
            x = 0
        else:
            testBoundary = theHdr.origin.x + theHdr.width
            if testBoundary < Hdr.region.width:
                rightBoundary = testBoundary
            else:
                rightBoundary = Hdr.region.width
            if x > rightBoundary:
                crossChange = False
                x = rightBoundary
        cX = x - zAzim - theHdr.origin.x

        if azimFac:
            newAzimuth = cX / azimFac
        else:
            newAzimuth = 0.0

        if y < theHdr.origin.y or y < 0:
            crossChange = False
            y = 0
        elif y > theHdr.origin.y + theHdr.height:
            crossChange = False
            y = theHdr.origin.y + theHdr.height
        cY = y - zElev - theHdr.origin.y

        if elevFac:
            newElevation = cY / elevFac
        else:
            newElevation = 0.0

        if newElevation == Hdr.elevation and newAzimuth == Hdr.azimuth:
            crossChange = False
        else:
            Hdr.elevation = newElevation
            Hdr.azimuth = newAzimuth
    else:
        if Hdr.grab.offset.x < Hdr.grab.spot.x:
            off = Hdr.grab.spot.x - Hdr.grab.offset.x
            theHdr.origin.x -= off
        else:
            off = Hdr.grab.offset.x - Hdr.grab.spot.x
            theHdr.origin.x += off
        if Hdr.grab.offset.y < Hdr.grab.spot.y:
            off = Hdr.grab.spot.y - Hdr.grab.offset.y
            theHdr.origin.y -= off
        else:
            off = Hdr.grab.offset.y - Hdr.grab.spot.y
            theHdr.origin.y += off
        Hdr.grab.spot.x = Hdr.mouse.x
        Hdr.grab.spot.y = Hdr.mouse.y

    Lx = theHdr.origin.x
    Ly = theHdr.origin.y

    # ---------------------
    # Draw a textured quad
    # ---------------------

    bgl.glEnable(bgl.GL_BLEND)
    if Hdr.glImage.bindcode == 0:
        Hdr.load_gl_image()
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, Hdr.glImage.bindcode)
    bgl.glEnable(bgl.GL_TEXTURE_2D)
    bgl.glColor4f(1.0, 1.0, 1.0, Hdr.object[0].opacity)
    bgl.glBegin(bgl.GL_QUADS)
    bgl.glTexCoord2f(0.0, 0.0)
    bgl.glVertex2f(Lx, Ly)
    bgl.glTexCoord2f(1.0, 0.0)
    bgl.glVertex2f(Lx + theHdr.width, Ly)
    bgl.glTexCoord2f(1.0, 1.0)
    bgl.glVertex2f(Lx + theHdr.width, Ly + theHdr.height)
    bgl.glTexCoord2f(0.0, 1.0)
    bgl.glVertex2f(Lx, theHdr.height + Ly)
    bgl.glEnd()
    bgl.glDisable(bgl.GL_TEXTURE_2D)

    # ---------------------
    # draw the crosshair
    # ---------------------
    x = theHdr.width / 2.0
    if crossChange and not Hdr.lockCrosshair:
        Sun.SP.HDR_azimuth = degToRad(newAzimuth + 180)
    azimuth = ((radToDeg(Sun.SP.HDR_azimuth) - 180) * x / 180.0) + x

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_LINES)
    bgl.glLineWidth(1.0)
    alpha = 0.8
    color = (0.4, 0.4, 0.4, alpha)
    bgl.glColor4f(color[0], color[1], color[2], color[3])
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex2f(Lx + azimuth, Ly)
    bgl.glVertex2f(Lx + azimuth, Ly + theHdr.height)
    bgl.glEnd()

    y = theHdr.height / 2.0
    if crossChange and not Hdr.lockCrosshair:
        Sun.SP.HDR_elevation = newElevation
    elevation = (Sun.SP.HDR_elevation * y / 90.0) + y

    bgl.glColor4f(color[0], color[1], color[2], color[3])
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex2f(Lx, Ly + elevation)
    bgl.glVertex2f(Lx + theHdr.width, Ly + elevation)
    bgl.glEnd()

    # ---------------------
    # draw the border
    # ---------------------
    bgl.glDisable(bgl.GL_BLEND)
    color = (0.6, 0.6, .6, 1.0)
    bgl.glColor4f(color[0], color[1], color[2], color[3])
    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glVertex2f(Lx, Ly)
    bgl.glVertex2f(Lx + theHdr.width, Ly)
    bgl.glVertex2f(Lx + theHdr.width, Ly + theHdr.height)
    bgl.glVertex2f(Lx, theHdr.height + Ly)
    bgl.glVertex2f(Lx, Ly)
    bgl.glEnd()

    bgl.glLineWidth(1.0)
    bgl.glDisable(bgl.GL_LINES)
    bgl.glFlush()

# ---------------------------------------------------------------------------


class SunPos_HdrHelp(bpy.types.Operator):
    bl_idname = "object.hdrhelp_operator"
    bl_label = "Hdr help"

    def execute(self, context):
        self.report({'INFO'}, self.message)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=400, height=200)

    def draw(self, context):
        self.layout.label(text="Available commands:")

        row = self.layout.row()
        split = row.split(percentage=.26)
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
        self.layout.label("--- The following are changed by moving " +
                          "the mouse or using the scroll wheel.")
        self.layout.label(text="--- Use Ctrl for coarse increments or Alt for fine.")
        row = self.layout.row()
        split = row.split(percentage=.25)
        colL = split.column()
        colR = split.column()
        colL.label(text="Scroll wheel")
        colR.label(text="Zoom to point.")
