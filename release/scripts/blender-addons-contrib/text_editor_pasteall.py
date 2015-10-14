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

bl_info = {
    "name": "PasteAll",
    "author": "Dalai Felinto (dfelinto)",
    "version": (0, 7),
    "blender": (2, 60, 0),
    "location": "Text editor > Properties panel",
    "description": "Send your selection or text to www.pasteall.org",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Text_Editor/PasteAll",
    "tracker_url": "https://developer.blender.org/T23493",
    "category": "Text Editor"}

# ########################################################
# PasteAll.org Text Sender Script
#
# Dalai Felinto (dfelinto)
# blenderecia.orgfree.com
#
# Rio de Janeiro - Brasil
# Vancouver - Canada
#
# Original code: 23rd August 2010 (Blender 2.5.3 rev. 31525)
#
# Important Note:
# This script is not official. I did it for fun and for my own usage.
# And please do not abuse of their generosity - use it wisely (a.k.a no flood).
#
# ########################################################


import bpy
import urllib
import urllib.request
import webbrowser

class TEXT_PT_pasteall(bpy.types.Panel):
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_label = "PasteAll.org"

    def draw(self, context):
        layout = self.layout
        layout.operator("text.pasteall", icon='URL')
        layout.prop(context.scene, "use_webbrowser")

class TEXT_OT_pasteall(bpy.types.Operator):
    """"""
    bl_idname = "text.pasteall"
    bl_label = "PasteAll.org"
    bl_description = "Send the current text or selection to www.pasteall.org"

    @classmethod
    def poll(cls, context):
        if context.area.type != 'TEXT_EDITOR':
            return False
        else:
            return context.space_data.text != None

    def invoke(self, context, event):
        import webbrowser
        st = context.space_data

        # get the selected text
        text = self.get_selected_text(st.text)
        # if no text is selected send the whole file
        if text is None: text = st.text.as_string()

        # get the file type based on the extension
        format = self.get_file_format(st.text)

        # send the text and receive the returned page
        html = self.send_text(text, format)

        if html is None:
            self.report({'ERROR'}, "Error in sending the text to the server.")
            return {'CANCELLED'}

        # get the link of the posted page
        page = self.get_page(str(html))

        if page is None or page == "":
            self.report({'ERROR'}, "Error in retrieving the page.")
            return {'CANCELLED'}
        else:
            self.report({'INFO'}, page)

        # store the link in the clipboard
        bpy.context.window_manager.clipboard = page

        if context.scene.use_webbrowser:
            try:
                webbrowser.open_new_tab(page)
            except:
                self.report({'WARNING'}, "Error in opening the page %s." % (page))

        return {'FINISHED'}

    def send_text(self, text, format):
        """"""
        import urllib
        url = "http://www.pasteall.org/index.php"
        values = {  'action' : 'savepaste',
                    'parent_id' : '0',
                    'language_id': format,
                    'code' : text }

        try:
            data = urllib.parse.urlencode(values).encode()
            req = urllib.request.Request(url, data)
            response = urllib.request.urlopen(req)
            page_source = response.read()
        except:
            return None
        else:
            return page_source

    def get_page(self, html):
        """"""
        id = html.find('directlink')
        id_begin = id + 12 # hardcoded: directlink">
        id_end = html[id_begin:].find("</a>")

        if id != -1 and id_end != -1:
            return html[id_begin:id_begin + id_end]
        else:
            return None

    def get_selected_text(self, text):
        """"""
        current_line = text.current_line
        select_end_line = text.select_end_line

        current_character = text.current_character
        select_end_character = text.select_end_character

        # if there is no selected text return None
        if current_line == select_end_line:
            if current_character == select_end_character:
                return None
            else:
                return current_line.body[min(current_character,select_end_character):max(current_character,select_end_character)]

        text_return = None
        writing = False
        normal_order = True # selection from top to bottom

        for line in text.lines:
            if not writing:
                if line == current_line:
                    text_return = current_line.body[current_character:] + "\n"
                    writing = True
                    continue
                elif line == select_end_line:
                    text_return =  select_end_line.body[select_end_character:] + "\n"
                    writing = True
                    normal_order = False
                    continue
            else:
                if normal_order:
                    if line == select_end_line:
                        text_return += select_end_line.body[:select_end_character]
                        break
                    else:
                        text_return += line.body + "\n"
                        continue
                else:
                    if line == current_line:
                        text_return += current_line.body[:current_character]
                        break
                    else:
                        text_return += line.body + "\n"
                        continue

        return text_return

    def get_file_format(self, text):
        """Try to guess what is the format based on the file extension"""
        extensions =   {'diff':'24',
                        'patch':'24',
                        'py':'62',
                        'c':'12',
                        'cpp':'18'}

        type = text.name.split(".")[-1]
        return extensions.get(type, '0')

def register():
    bpy.types.Scene.use_webbrowser = bpy.props.BoolProperty(
        name='Launch Browser',
        description='Opens the page with the submitted text.',
        default=True)

    bpy.utils.register_module(__name__)

def unregister():
    del bpy.types.Scene.use_webbrowser
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()


