from . bl_ui_widget import *

import blf

class BL_UI_Label(BL_UI_Widget):

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)

        self._text_color        = (1.0, 1.0, 1.0, 1.0)
        self._text = "Label"
        self._text_size = 16

    @property
    def text_color(self):
        return self._text_color

    @text_color.setter
    def text_color(self, value):
        self._text_color = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    @property
    def text_size(self):
        return self._text_size

    @text_size.setter
    def text_size(self, value):
        self._text_size = value

    def is_in_rect(self, x, y):
        return False

    def draw(self):
        if not self.visible:
            return

        area_height = self.get_area_height()

        blf.size(0, self._text_size, 72)
        size = blf.dimensions(0, self._text)

        textpos_y = area_height - self.y_screen - self.height
        blf.position(0, self.x_screen, textpos_y, 0)

        r, g, b, a = self._text_color

        blf.color(0, r, g, b, a)

        blf.draw(0, self._text)
