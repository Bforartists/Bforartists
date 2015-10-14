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
    "name": "Game Property Visualizer",
    "author": "Bartius Crouch/Vilem Novak",
    "version": (2, 6),
    "blender": (2, 65, 4),
    "location": "View3D > Properties panel > Display tab",
    "description": "Display the game properties next to selected objects "
                   "in the 3d-view",
    "warning": "Script is returning errors",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/3D_interaction/Game_Property_Visualiser",
    "tracker_url": "https://developer.blender.org/T22607",
    "category": "3D View"}

"""
Displays game properties next to selected objects(under name)

How to use:
    just toggle the button 'Visualize game props' in the right side panel
"""

import bgl
import blf
import bpy
import mathutils


# calculate locations and store them as ID property in the mesh
def calc_callback(self, context):
    # polling
    if context.mode == 'EDIT_MESH':
        return

    # get screen information
    mid_x = context.region.width / 2.0
    mid_y = context.region.height / 2.0
    width = context.region.width
    height = context.region.height

    # get matrices
    view_mat = context.space_data.region_3d.perspective_matrix

    ob_mat = context.active_object.matrix_world
    total_mat = view_mat * ob_mat

    # calculate location info
    texts = []

    # uncomment 2 lines below, to enable live updating of the selection
    #ob=context.active_object
    for ob in context.selected_objects:
        locs = []
        ob_mat = ob.matrix_world
        total_mat = view_mat*ob_mat

        for p in ob.game.properties:
            # d = {'data':p.name+':'+str(p.value)}
            # print (d)
            locs.append(mathutils.Vector((0, 0, 0, 1)))

        for loc in locs:
            vec = total_mat * loc # order is important
            # dehomogenise
            vec = mathutils.Vector((vec[0]/vec[3], vec[1]/vec[3], vec[2]/vec[3]))
            x = int(mid_x + vec[0]*width / 2.0)
            y = int(mid_y + vec[1]*height / 2.0)
            texts += [x, y]

    # store as ID property in mesh
    context.scene['GamePropsVisualizer'] = texts


# draw in 3d-view
def draw_callback(self, context):
    # polling
    if context.mode == 'EDIT_MESH':
        return

    """
    # retrieving ID property data
    try:
        texts = context.scene['GamePropsVisualizer']
    except:
        return

    if not texts:
        return
    """

    texts = context.scene['GamePropsVisualizer']

    # draw
    i = 0

    blf.size(0, 12, 72)


    bgl.glColor3f(1.0, 1.0, 1.0)
    for ob in bpy.context.selected_objects:
        for pi,p in enumerate(ob.game.properties):
            blf.position(0, texts[i], texts[i+1] - (pi+1) * 14, 0)
            if p.type=='FLOAT':
                t=p.name+':  '+ str('%g' % p.value)
            else:
                t=p.name+':  '+ str(p.value)
            blf.draw(0, t)
            i += 2


# operator
class GamePropertyVisualizer(bpy.types.Operator):
    bl_idname = "view3d.game_props_visualizer"
    bl_label = "Game Properties Visualizer"
    bl_description = "Toggle the visualization of game properties"

    _handle_calc = None
    _handle_draw = None

    @staticmethod
    def handle_add(self, context):
        GamePropertyVisualizer._handle_calc = bpy.types.SpaceView3D.draw_handler_add(
            calc_callback, (self, context), 'WINDOW', 'POST_VIEW')
        GamePropertyVisualizer._handle_draw = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback, (self, context), 'WINDOW', 'POST_PIXEL')

    @staticmethod
    def handle_remove():
        if GamePropertyVisualizer._handle_calc is not None:
            bpy.types.SpaceView3D.draw_handler_remove(GamePropertyVisualizer._handle_calc, 'WINDOW')
        if GamePropertyVisualizer._handle_draw is not None:
            bpy.types.SpaceView3D.draw_handler_remove(GamePropertyVisualizer._handle_draw, 'WINDOW')
        GamePropertyVisualizer._handle_calc = None
        GamePropertyVisualizer._handle_draw = None

    @classmethod
    def poll(cls, context):
        return context.mode != 'EDIT_MESH'

    def modal(self, context, event):
        if not context.scene.display_game_properties:
            return self.cancel(context)
        context.area.tag_redraw()
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            if not context.scene.display_game_properties:
                # operator is called and not running
                GamePropertyVisualizer.handle_add(self, context)
                context.scene.display_game_properties = True
                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
            else:
                # operator is called again, stop displaying
                return self.cancel(context)
        else:
            self.report({'WARNING'}, "View3D not found, can't run operator")
            return {'CANCELLED'}

    def cancel(self, context):
        GamePropertyVisualizer.handle_remove()
        context.scene.display_game_properties = False
        context.area.tag_redraw()
        return {'FINISHED'}


# defining the panel
def menu_func(self, context):
    layout = self.layout
    col = layout.column()
    if not context.scene.display_game_properties:
        text = "Visualize game props"
    else:
        text = "Hide game props"
    col.operator(GamePropertyVisualizer.bl_idname, text=text)
    layout.separator()


def register():
    bpy.utils.register_class(GamePropertyVisualizer)
    bpy.types.Scene.display_game_properties = bpy.props.BoolProperty(name='Visualize Game Poperties')
    bpy.types.VIEW3D_PT_view3d_display.prepend(menu_func)

def unregister():
    GamePropertyVisualizer.handle_remove()
    bpy.utils.unregister_class(GamePropertyVisualizer)
    bpy.types.VIEW3D_PT_view3d_display.remove(menu_func)
    del bpy.types.Scene.display_game_properties

if __name__ == "__main__":
    register()
