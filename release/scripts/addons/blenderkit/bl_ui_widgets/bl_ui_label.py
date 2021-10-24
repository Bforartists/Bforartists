from . bl_ui_widget import *

import blf

class BL_UI_Label(BL_UI_Widget):

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)

        self._text_color        = (1.0, 1.0, 1.0, 1.0)
        self._text = "Label"
        self._text_size = 16
        self._ralign = 'LEFT'
        self._valign = 'TOP'

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
        if not self._is_visible:
            return


        area_height = self.get_area_height()

        font_id = 1
        blf.size(font_id, self._text_size, 72)
        size = blf.dimensions(font_id, self._text)

        textpos_y = area_height - self.y_screen - self.height

        r, g, b, a = self._text_color
        x = self.x_screen
        y = textpos_y
        if self._halign != 'LEFT':
            width, height = blf.dimensions(font_id, self._text)
            if self._halign == 'RIGHT':
                x -= width
            elif self._halign == 'CENTER':
                x -= width // 2
            if self._valign == 'CENTER':
                y -= height // 2
            # bottom could be here but there's no reason for it
        blf.position(font_id, x, y, 0)

        blf.color(font_id, r, g, b, a)

        blf.draw(font_id, self._text)
