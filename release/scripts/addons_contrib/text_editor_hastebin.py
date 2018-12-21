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
    "name": "hastebin",
    "author": "Dalai Felinto (dfelinto)",
    "version": (0, 8),
    "blender": (2, 78, 0),
    "location": "Text editor > Properties panel",
    "description": "Send your selection or text to hastebin.com",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Text_Editor/hastebin",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Text Editor"}


import bpy

class TEXT_PT_hastebin(bpy.types.Panel):
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_label = "hastebin.com"

    def draw(self, context):
        layout = self.layout
        layout.operator("text.hastebin", icon='URL')
        layout.prop(context.scene, "use_webbrowser")


class TEXT_OT_hastebin(bpy.types.Operator):
    """"""
    bl_idname = "text.hastebin"
    bl_label = "hastebin.com"
    bl_description = "Send the current text or selection to http://hastebin.com"

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

        # send the text and receive the returned page
        page = self.send_text(text)

        if page is None:
            return {'CANCELLED'}

        # store the link in the clipboard
        bpy.context.window_manager.clipboard = page

        if context.scene.use_webbrowser:
            try:
                webbrowser.open_new_tab(page)
            except:
                self.report({'WARNING'}, "Error in opening the page %s." % (page))

        return {'FINISHED'}

    def send_text(self, text):
        """"""
        import requests
        base_url = "https://hastebin.com"

        try:
            response = requests.post(base_url + "/documents", text)
            final_url = "%s/%s" % (base_url, response.json()['key'])

        except requests.exceptions.SSLError:
            self.report({'ERROR'}, "Error with SSL authorization, requires a more recent Blender")
            return None

        except:
            self.report({'ERROR'}, "Error in sending the text to the server.")
            return None

        else:
            return final_url

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


def register():
    bpy.types.Scene.use_webbrowser = bpy.props.BoolProperty(
        name='Launch Browser',
        description='Opens the page with the submitted text',
        default=True)

    bpy.utils.register_module(__name__)


def unregister():
    del bpy.types.Scene.use_webbrowser
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
