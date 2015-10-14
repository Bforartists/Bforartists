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
    "name": "Render Time Estimation",
    "author": "Jason van Gumster (Fweeb)",
    "version": (0, 5, 2),
    "blender": (2, 65, 4),
    "location": "UV/Image Editor > Properties > Image",
    "description": "Estimates the time to complete rendering on animations",
    "warning": "Does not work on OpenGL renders.",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Render/Render_Time_Estimation",
    "tracker_url": "https://developer.blender.org/T30452",
    "category": "Render"}


import bpy, time
from bpy.app.handlers import persistent
from datetime import timedelta
import blf


timer = {"average": 0.0, "total": 0.0, "time_start": 0.0, "is_rendering": False, "hud": False}

def set_rendering(scene):
    timer["is_rendering"] = True

@persistent
def unset_rendering(scene):
    timer["is_rendering"] = False

@persistent
def start_timer(scene):
    set_rendering(scene)

    if scene.frame_current == scene.frame_start:
        timer["average"] = 0.0
        timer["total"] = 0.0

    timer["time_start"] = time.time()

@persistent
def end_timer(scene):
    render_time = time.time() - timer["time_start"]
    timer["total"] += render_time
    if scene.frame_current == scene.frame_start:
        timer["average"] = render_time
    else:
        timer["average"] = (timer["average"] + render_time) / 2

    print("Total render time: " + str(timedelta(seconds = timer["total"])))
    print("Estimated completion: " + str(timedelta(seconds = (timer["average"] * (scene.frame_end - scene.frame_current)))))


# UI

def image_panel_rendertime(self, context):
    scene = context.scene
    layout = self.layout

    if context.space_data.image is not None and context.space_data.image.type == 'RENDER_RESULT':
        layout.label(text = "Total render time: " + str(timedelta(seconds = timer["total"])))

        if timer["is_rendering"] and scene.frame_current != scene.frame_start:
            layout.label(text = "Estimated completion: " + str(timedelta(seconds = (timer["average"] * (scene.frame_end - scene.frame_current)))))

def draw_callback_px(self, context):
    scene = context.scene

    font_id = 0  # XXX, need to find out how best to get this.

    # draw some text
    blf.position(font_id, 15, 30, 0)
    blf.size(font_id, 18, 72)
    blf.enable(font_id, blf.SHADOW)
    blf.shadow(font_id, 5, 0.0, 0.0, 0.0, 1.0)

    # Shorten / cut off milliseconds
    time_total = str(timedelta(seconds = timer["total"]))
    pos = time_total.rfind(".")
    if pos != -1:
        time_total = time_total[0:pos+3]

    time_estimated = str(timedelta(seconds = (timer["average"] * (scene.frame_end - scene.frame_current))))
    pos = time_estimated.rfind(".")
    if pos != -1:
        time_estimated = time_estimated[0:pos]


    blf.draw(font_id, "Total render time " + time_total)
    if timer["is_rendering"] and scene.frame_current != scene.frame_start:
        blf.position(font_id, 15, 12, 0)
        blf.draw(font_id, "Estimated completion: " + time_estimated)

    # restore defaults
    blf.disable(font_id, blf.SHADOW)

class RenderTimeHUD(bpy.types.Operator):
    bl_idname = "view2d.rendertime_hud"
    bl_label = "Display Render Times"
    last_activity = 'NONE'

    _handle = None

    @staticmethod
    def handle_add(self, context):
        RenderTimeHUD._handle = bpy.types.SpaceImageEditor.draw_handler_add(
            draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL')

    @staticmethod
    def handle_remove():
        if RenderTimeHUD._handle is not None:
            bpy.types.SpaceImageEditor.draw_handler_remove(RenderTimeHUD._handle, 'WINDOW')
        RenderTimeHUD._handle = None

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        #if event.type in {'ESC'}:
        if timer["hud"] == False:
            RenderTimeHUD.handle_remove()
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == 'IMAGE_EDITOR':
            if timer["hud"] == False:
                # Add the region OpenGL drawing callback
                RenderTimeHUD.handle_add(self, context)
                timer["hud"] = True

                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
            else:
                timer["hud"] = False
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "UV/Image Editor not found, cannot run operator")
            return {'CANCELLED'}

def display_hud(self, context):
    layout = self.layout
    text = RenderTimeHUD.bl_label if RenderTimeHUD._handle is None else "Hide Render Times"
    layout.operator("view2d.rendertime_hud", text=text)

# Registration

def register():
    bpy.app.handlers.render_complete.append(unset_rendering)
    bpy.app.handlers.render_cancel.append(unset_rendering)
    bpy.app.handlers.render_pre.append(start_timer)
    bpy.app.handlers.render_post.append(end_timer)
    bpy.types.IMAGE_PT_image_properties.append(image_panel_rendertime)
    bpy.utils.register_class(RenderTimeHUD)
    bpy.types.IMAGE_HT_header.append(display_hud)

    # Keymapping      XXX TODO - This doesn't work for some reason
    #kc = bpy.context.window_manager.keyconfigs.addon
    #km = kc.keymaps.new(name = "View 2D", space_type = 'IMAGE_EDITOR')
    #kmi = km.keymap_items.new("view2d.rendertime_hud", 'E', 'PRESS')
    #kmi.active = True

def unregister():
    RenderTimeHUD.handle_remove()

    #kc = bpy.context.window_manager.keyconfigs.addon
    #km = kc.keymaps["View 2D"]
    #km.keymap_items.remove(km.keymap_items["view2d.rendertime_hud"])

    bpy.types.IMAGE_HT_header.remove(display_hud)
    bpy.utils.unregister_class(RenderTimeHUD)
    bpy.app.handlers.render_pre.remove(start_timer)
    bpy.app.handlers.render_post.remove(end_timer)
    bpy.app.handlers.render_cancel.remove(unset_rendering)
    bpy.app.handlers.render_complete.remove(unset_rendering)
    bpy.types.IMAGE_PT_image_properties.remove(image_panel_rendertime)

if __name__ == '__main__':
    register()
