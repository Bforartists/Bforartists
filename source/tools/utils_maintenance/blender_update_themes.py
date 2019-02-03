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

# this script updates XML themes once new settings are added
#
#  ./blender.bin --background --python source/tools/utils/blender_update_themes.py

import bpy
import os


def update(filepath):
    import rna_xml
    context = bpy.context

    print("Updating theme: %r" % filepath)
    preset_xml_map = (
        ("preferences.themes[0]", "Theme"),
        ("preferences.ui_styles[0]", "Theme"),
    )
    rna_xml.xml_file_run(
        context,
        filepath,
        preset_xml_map,
    )

    rna_xml.xml_file_write(
        context,
        filepath,
        preset_xml_map,
    )


def main():
    for path in bpy.utils.preset_paths("interface_theme"):
        for fn in os.listdir(path):
            if fn.endswith(".xml"):
                fn_full = os.path.join(path, fn)
                update(fn_full)


if __name__ == "__main__":
    main()
