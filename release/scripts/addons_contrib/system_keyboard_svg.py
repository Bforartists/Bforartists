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

# this script creates Keyboard layout images of the current keyboard configuration.
# first implementation done by jbakker
# version 0.2 - file manager directory on export, modified the SVG layout (lijenstina)

bl_info = {
    "name": "Keyboard Layout (SVG)",
    "author": "Jbakker",
    "version": (0, 2),
    "blender": (2, 60, 0),
    "location": "Help Menu > Save Shortcuts as SVG files",
    "description": "Save the hotkeys as .svg files (search: Keyboard)",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/System/keymaps_to_svg",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "System"
    }

import bpy
import os
from math import ceil
from bpy.props import StringProperty

keyboard = (
    ('`', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE',
    'ZERO', 'MINUS', 'EQUAL', 'BACKSPACE'),
    ('TAB', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '(', ')', '\\'),
    ('CAPSLOCK', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', "'", 'ENTER'),
    ('SHIFT', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/', 'SHIFT'),
    ('CONTROL', 'OSKEY', 'ALT', 'SPACE', 'ALT', 'OSKEY', 'MENUKEY', 'CONTROL')
    )

# default dimension of a single key [width, height]
HEIGHT_KEY = 160
DEFAULT_KEY_DIMENSION = 170, HEIGHT_KEY
# alternative dimensions of specific keys [keyname,[width, height]]
ALTERNATIVE_KEY_DIMENSIONS = {
    'BACKSPACE': (270, HEIGHT_KEY),
    'TAB': (220, HEIGHT_KEY),
    '\\': (220, HEIGHT_KEY),
    'CAPSLOCK': (285, HEIGHT_KEY),
    'ENTER': (345, HEIGHT_KEY),
    'SHIFT': (410, HEIGHT_KEY),
    'CONTROL': (230, HEIGHT_KEY),
    'ALT': DEFAULT_KEY_DIMENSION,
    'OSKEY': DEFAULT_KEY_DIMENSION,
    'MENUKEY': DEFAULT_KEY_DIMENSION,
    'SPACE': (1290, HEIGHT_KEY),
}
INFO_STRING = "Modifier keys Info: [C] = Ctrl, [A] = Alt, [S] = Shift"


def createKeyboard(viewtype, filepaths):
    """
    Creates a keyboard layout (.svg) file of the current configuration for a specific viewtype.
    example of a viewtype is "VIEW_3D".
    """

    for keyconfig in bpy.data.window_managers[0].keyconfigs:
        kc_map = {}
        for keymap in keyconfig.keymaps:
            if keymap.space_type == viewtype:
                for key in keymap.keymap_items:
                    if key.map_type == 'KEYBOARD':
                        test = 0
                        cont = ""
                        if key.ctrl:
                            test = test + 1
                            cont = "C"
                        if key.alt:
                            test = test + 2
                            cont = cont + "A"
                        if key.shift:
                            test = test + 4
                            cont = cont + "S"
                        if key.oskey:
                            test = test + 8
                            cont = cont + "O"
                        if len(cont) > 0:
                            cont = "[" + cont + "] "
                        ktype = key.type
                        if ktype not in kc_map:
                            kc_map[ktype] = []
                        kc_map[ktype].append((test, cont + key.name))

        filename = "keyboard_%s.svg" % viewtype
        export_path = os.path.join(os.path.normpath(filepaths), filename)
        with open(export_path, mode="w") as svgfile:
            svgfile.write("""<?xml version="1.0" standalone="no"?>
    <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
        """)
            svgfile.write("""<svg width="2800" height="1000" version="1.1" xmlns="http://www.w3.org/2000/svg">
        """)
            svgfile.write("""<style>
    rect {
        fill:rgb(223,235,238);
        stroke-width:1;
        stroke:rgb(0,0,0);
    }
    text.header {
        font-size:xx-large;
    }
    text.key {
        fill:rgb(0,65,100);
        font-size:x-large;
        stroke-width:2;
        stroke:rgb(0,65,100);
    }
    text.action {
        font-size:smaller;
    }
    text.add0 {
        font-size:smaller;
        fill:rgb(0,0,0)
    }
    text.add1 {
        font-size:smaller;
        fill:rgb(255,0,0)
    }
    text.add2 {
        font-size:smaller;
        fill:rgb(0,128,115)
    }
    text.add3 {
       font-size:smaller;
       fill:rgb(128,128,0)
    }
    text.add4 {
        font-size:smaller;
        fill:rgb(0,0,255)
    }
    text.add5 {
        font-size:smaller;
        fill:rgb(128,0,128)
    }
    text.add6 {
        font-size:smaller;
        fill:rgb(0, 128, 128)
    }
    text.add7 {
        font-size:smaller;
        fill:rgb(128,128,128)
    }
    text.add8 {
        font-size:smaller;
        fill:rgb(128,128,128)
    }
    text.add9 {
        font-size:smaller;
        fill:rgb(255,128,128)
    }
    text.add10 {
        font-size:smaller;
        fill:rgb(128,255,128)
    }
    text.add11 {
        font-size:smaller;
        fill:rgb(255,255,128)
    }
    text.add12 {
        font-size:smaller;
        fill:rgb(128,128,255)
    }
    text.add13 {
        font-size:smaller;
        fill:rgb(255,128,255)
    }
    text.add14 {
        font-size:smaller;
        fill:rgb(128,255,255)
    }
    text.add15 {
        font-size:smaller;
        fill:rgb(255,255,128)
    }
    </style>
    """)
            svgfile.write("""<text class="header" x="30" y="32">Keyboard Layout for """ + viewtype + """</text>
    """)

            x = 20
            xgap = 20
            ygap = 20
            y = 48
            for row in keyboard:
                x = 30
                for key in row:
                    width, height = ALTERNATIVE_KEY_DIMENSIONS.get(key, DEFAULT_KEY_DIMENSION)
                    tx = ceil(width * 0.2)
                    ty = 32
                    svgfile.write("""<rect x=\"""" + str(x) +
                                  """\" y=\"""" + str(y) +
                                  """\" width=\"""" + str(width) +
                                  """\" height=\"""" + str(height) +
                                  """\" rx="20" ry="20" />
        """)
                    svgfile.write("""<text class="key" x=\"""" + str(x + tx) +
                                  """\" y=\"""" + str(y + ty) +
                                  """\" width=\"""" + str(width) +
                                  """\" height=\"""" + str(height) + """\">
        """)
                    svgfile.write(key)
                    svgfile.write("</text>")
                    ty = ty + 16
                    tx = 4
                    if key in kc_map:
                        for a in kc_map[key]:
                            svgfile.write("""<text class="add""" + str(a[0]) +
                                          """" x=\"""" + str(x + tx) +
                                          """\" y=\"""" + str(y + ty) +
                                          """\" width=\"""" + str(width) +
                                          """\" height=\"""" + str(height) + """\">
        """)
                            svgfile.write(a[1])
                            svgfile.write("</text>")
                            ty = ty + 16
                    x = x + width + xgap
                y = y + HEIGHT_KEY + ygap

            svgfile.write("""<text class="header" x="30" y="975" >""")
            svgfile.write(INFO_STRING)
            svgfile.write("</text>")

            svgfile.write("""</svg>""")


class WM_OT_keyboardlayout(bpy.types.Operator):
    bl_idname = "wm.keyboardlayout"
    bl_label = "Save Shortcuts as SVG files"
    bl_description = ("Export the keyboard layouts in SVG format\n"
                      "for each Editor in a separate file")

    directory = StringProperty(
        subtype='FILE_PATH',
        options={'SKIP_SAVE'},
        )

    def invoke(self, context, event):
        if not self.directory:
            self.directory = ""

        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not (os.path.isdir(self.directory) and os.path.exists(self.directory)):
            self.report({'WARNING'},
                        "Chosen path is not a directory or it doesn't exist. Operation Cancelled")
            return {'CANCELLED'}

        # Iterate over all viewtypes to export the keyboard layout
        for vt in ('VIEW_3D',
                   'LOGIC_EDITOR',
                   'NODE_EDITOR',
                   'CONSOLE',
                   'GRAPH_EDITOR',
                   'PROPERTIES',
                   'SEQUENCE_EDITOR',
                   'OUTLINER',
                   'IMAGE_EDITOR',
                   'TEXT_EDITOR',
                   'DOPESHEET_EDITOR',
                   'Window'):

            createKeyboard(vt, self.directory)

        return {'FINISHED'}


def menu_func_help(self, context):
    self.layout.separator()
    self.layout.operator(WM_OT_keyboardlayout.bl_idname, icon="IMGDISPLAY")


def register():
    bpy.utils.register_class(WM_OT_keyboardlayout)

    bpy.types.INFO_MT_help.append(menu_func_help)


def unregister():
    bpy.types.INFO_MT_help.remove(menu_func_help)

    bpy.utils.unregister_class(WM_OT_keyboardlayout)


if __name__ == "__main__":
    register()
