# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****


bl_info = {
    "name": "Render Notify",
    "author": "Campbell Barton",
    "version": (0, 0, 1),
    "blender": (2, 65, 0),
    "location": "Uses desktop notify facilities",
    "description": "Notify when a rendered completes",
    "warning": "Currently only Linux/Unix supported (using 'notify-send')",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6"
                "/Py/Scripts/Render/Render_Notify",
    "category": "Render"}

# TODO. add Win/OSX support if possible.


import bpy
import time
from bpy.app.handlers import persistent
from datetime import timedelta

timer = [0.0]


def clean_float(text):
    # strip trailing zeros: 0.000 -> 0.0
    index = text.rfind(".")
    if index != -1:
        index += 2
        head, tail = text[:index], text[index:]
        tail = tail.rstrip("0")
        text = head + tail
    return text


@persistent
def render_begin(scene):
    timer[0] = time.time()


@persistent
def render_complete(scene):
    import os
    import shlex
    time_val = round(time.time() - timer[0], 2)
    time_str = clean_float(str(timedelta(seconds=time_val)))
    file_str = os.path.basename(bpy.data.filepath)
    msg = "%s render complete in %s" % (file_str, time_str)
    os.system("notify-send --app-name=Blender --icon=blender %s" %
              shlex.quote(msg))


def register():
    bpy.app.handlers.render_complete.append(render_complete)
    bpy.app.handlers.render_pre.append(render_begin)


def unregister():
    bpy.app.handlers.render_complete.remove(render_complete)
    bpy.app.handlers.render_pre.remove(render_begin)


if __name__ == '__main__':
    register()
