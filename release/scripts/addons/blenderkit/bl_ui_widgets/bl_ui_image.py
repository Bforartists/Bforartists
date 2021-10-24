from . bl_ui_widget import *

import blf
import bpy

class BL_UI_Image(BL_UI_Widget):

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)

        self.__state = 0
        self.__image = None
        self.__image_size = (24, 24)
        self.__image_position = (4, 2)

    def set_image_size(self, imgage_size):
        self.__image_size = imgage_size

    def set_image_position(self, image_position):
        self.__image_position = image_position

    def set_image(self, rel_filepath):
        try:
            if self.__image is None or self.__image.filepath != rel_filepath:
                self.__image = bpy.data.images.load(rel_filepath, check_existing=True)
                self.__image.gl_load()
        except:
            pass

    def update(self, x, y):
        super().update(x, y)

    def draw(self):
        if not self._is_visible:
            return

        area_height = self.get_area_height()

        self.shader.bind()

        bgl.glEnable(bgl.GL_BLEND)

        self.batch_panel.draw(self.shader)

        self.draw_image()

        bgl.glDisable(bgl.GL_BLEND)


    def draw_image(self):
        if self.__image is not None:
            try:
                y_screen_flip = self.get_area_height() - self.y_screen

                off_x, off_y =  self.__image_position
                sx, sy = self.__image_size

                # bottom left, top left, top right, bottom right
                vertices = (
                            (self.x_screen + off_x, y_screen_flip - off_y),
                            (self.x_screen + off_x, y_screen_flip - sy - off_y),
                            (self.x_screen + off_x + sx, y_screen_flip - sy - off_y),
                            (self.x_screen + off_x + sx, y_screen_flip - off_y))

                self.shader_img = gpu.shader.from_builtin('2D_IMAGE')
                self.batch_img = batch_for_shader(self.shader_img, 'TRI_FAN',
                { "pos" : vertices,
                "texCoord": ((0, 1), (0, 0), (1, 0), (1, 1))
                },)

                # send image to gpu if it isn't there already
                if self.__image.gl_load():
                    raise Exception()

                bgl.glActiveTexture(bgl.GL_TEXTURE0)
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.__image.bindcode)

                self.shader_img.bind()
                self.shader_img.uniform_int("image", 0)
                self.batch_img.draw(self.shader_img)
                return True
            except:
                pass

        return False

    def set_mouse_down(self, mouse_down_func):
        self.mouse_down_func = mouse_down_func

    def mouse_down(self, x, y):
        return False

    def mouse_move(self, x, y):
        return

    def mouse_up(self, x, y):
        return
