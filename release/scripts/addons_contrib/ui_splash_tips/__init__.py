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

# <pep8 compliant>

bl_info = {
    "name": "Splash Startup Tips",
    "description": "Show a tip on startup",
    "blender": (2, 73, 0),
    "location": "Splash Screen",
    "warning": "",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "System",
}


def u_randint(s, e):
    import os
    import struct
    data_type = 'Q'
    size = struct.calcsize(data_type)
    data = struct.unpack(data_type, os.urandom(size))[0]
    return s + (data % (e - s))


def read_random_line(f):
    import os

    chunk_size = 16
    with open(f, 'rb') as f_handle:
        f_handle.seek(0, os.SEEK_END)
        size = f_handle.tell()
        # i = random.randint(0, size)
        i = u_randint(0, size)
        while True:
            i -= chunk_size
            if i < 0:
                chunk_size += i
                i = 0
            f_handle.seek(i, os.SEEK_SET)
            d = f_handle.read(chunk_size)
            i_newline = d.rfind(b'\n')
            if i_newline != -1:
                i += i_newline + 1
                break
            if i == 0:
                break
        f_handle.seek(i, os.SEEK_SET)
        return f_handle.readline()


def find_random_tip():
    import os

    text = read_random_line(
            os.path.join(os.path.dirname(__file__), "tips.txt"),
            ).rstrip()

    url_index = text.rfind(b' ~')
    if url_index != -1:
        text, url = text[:url_index], text[url_index + 2:]
    else:
        url = b''
    return text.decode("utf-8"), url.decode("utf-8")


def menu_func(self, context):
    url_prefix = "https://docs.blender.org/manual/en/dev/"

    layout = self.layout
    tip, url = find_random_tip()
    tip = tip.split("\\n")
    row = layout.row()
    row.label(text="Tip: " + tip[0])
    if url:
        row.operator("wm.url_open", text="", icon='URL').url = url_prefix + url
    for tip_line in tip[1:]:
        row = layout.row()
        row.label(tip_line.strip())
    layout.separator()
    layout.separator()


import bpy


def register():
    bpy.types.USERPREF_MT_splash_footer.append(menu_func)


def unregister():
    bpy.types.USERPREF_MT_splash_footer.remove(menu_func)


if __name__ == "__main__":
    register()
