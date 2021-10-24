# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import time
from blenderkit import colors

def add_report(text='', timeout=5, color=colors.GREEN):
    global reports
    # check for same reports and just make them longer by the timeout.
    for old_report in reports:
        if old_report.text == text:
            old_report.timeout = old_report.age + timeout
            return
    report = Report(text=text, timeout=timeout, color=color)
    reports.append(report)


class Report():
    def __init__(self, text='', timeout=5, color=(.5, 1, .5, 1)):
        self.text = text
        self.timeout = timeout
        self.start_time = time.time()
        self.color = color
        self.draw_color = color
        self.age = 0

    def fade(self):
        fade_time = 1
        self.age = time.time() - self.start_time
        if self.age + fade_time > self.timeout:
            alpha_multiplier = (self.timeout - self.age) / fade_time
            self.draw_color = (self.color[0], self.color[1], self.color[2], self.color[3] * alpha_multiplier)
            if self.age > self.timeout:
                global reports
                try:
                    reports.remove(self)
                except Exception as e:
                    pass;

    def draw(self, x, y):
        if bpy.context.area.as_pointer() == active_area_pointer:
            ui_bgl.draw_text(self.text, x, y + 8, 16, self.draw_color)