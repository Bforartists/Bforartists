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

# Script copyright (C) Campbell Barton

bl_info = {
    "name": "Library Hide",
    "description": "Hide objects within library dupligroups",
    "author": "Campbell Barton",
    "version": (1, 0),
    "blender": (2, 63, 0),
    'location': 'Search: RayCast View Operator',
    "wiki_url": "",
    "tracker_url":"",
    "category": "3D View",
}

import bpy
from mathutils import Vector
from bpy_extras import view3d_utils

LIB_HIDE_TEXT_ID = "blender_hide_objects.py"

LIB_HIDE_TEXT_HEADER = """
import bpy
print("running: %r" % __file__)
def hide(name, lib):
    obj = bpy.data.objects.get((name, lib))
    if obj is None:
        print("hide can't find: %r %r" % (name, lib))
    else:
        obj.hide = obj.hide_render = True

"""

def pick_object(context, event, pick_objects, ray_max=10000.0):
    """Run this function on left mouse, execute the ray cast"""
    # get the context arguments
    scene = context.scene
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    ray_target = ray_origin + (view_vector * ray_max)

    scene.cursor_location = ray_target

    def visible_objects_and_duplis():
        """Loop over (object, matrix) pairs (mesh only)"""

        for obj in context.visible_objects:  # scene.objects:
            if obj.hide:
                continue

            if obj.type == 'MESH':
                yield (None, obj, obj.matrix_world.copy())

            if obj.dupli_type != 'NONE':
                print("DupliInst: %r" % obj)
                obj.dupli_list_create(scene)
                # matrix = obj.matrix_world.copy()
                for dob in obj.dupli_list:
                    obj_dupli = dob.object
                    if not obj_dupli.hide:
                        # print("Dupli: %r" % obj_dupli)
                        if obj_dupli.type == 'MESH':
                            yield (obj, obj_dupli, dob.matrix.copy())

                obj.dupli_list_clear()

    def obj_ray_cast(obj, matrix):
        """Wrapper for ray casting that moves the ray into object space"""

        # get the ray relative to the object
        matrix_inv = matrix.inverted()
        ray_origin_obj = matrix_inv * ray_origin
        ray_target_obj = matrix_inv * ray_target

        mesh = obj.data
        if not mesh.polygons:
            return None, None, None

        hit, normal, face_index = obj.ray_cast(ray_origin_obj, ray_target_obj)

        if face_index == -1:
            hit, normal, face_index = obj.ray_cast(ray_target_obj, ray_origin_obj)

        if face_index != -1:
            return hit, normal, face_index
        else:
            return None, None, None

    # cast rays and find the closest object
    best_length_squared = ray_max * ray_max
    best_obj = None
    best_obj_parent = None

    for obj_parent, obj, matrix in visible_objects_and_duplis():
        if obj.type == 'MESH':
            hit, normal, face_index = obj_ray_cast(obj, matrix)
            if hit is not None:
                length_squared = (hit - ray_origin).length_squared
                if length_squared < best_length_squared:
                    best_length_squared = length_squared
                    best_obj = obj
                    best_obj_parent = obj_parent

    # now we have the object under the mouse cursor,
    # we could do lots of stuff but for the example just select.
    if best_obj is not None:
        pick_objects.append((best_obj, best_obj.hide, best_obj.hide_render))
        best_obj.hide = True
        best_obj.hide_render = True
        
        #if best_obj_parent:
        #    best_obj_parent.update_tag(refresh={'OBJECT'})
        #scene.update()
        return True
    else:
        print("found none")
        return False


def pick_finalize(context, pick_objects):
    text = bpy.data.texts.get((LIB_HIDE_TEXT_ID, None))
    if text is None:
        text = bpy.data.texts.new(LIB_HIDE_TEXT_ID)
        text.use_module = True
        is_new = True
    else:
        is_new = False

    if is_new:
        data = []
        
        data += LIB_HIDE_TEXT_HEADER.split("\n")
    else:
        data = text.as_string().split("\n")

    data.append("# ---")
    
    for pick_obj_tuple in pick_objects:
        
        pick_obj = pick_obj_tuple[0]
        
        pick_obj.hide = True
        pick_obj.hide_render = True

        line = "hide(%r, %s)" % (pick_obj.name, repr(pick_obj.library.filepath) if pick_obj.library is not None else "None")
        data.append(line)
    
    text.from_string("\n".join(data))


def pick_restore(pick_obj):
    best_obj, hide, hide_render = pick_obj
    best_obj.hide = hide
    best_obj.hide_render = hide_render


class ViewOperatorRayCast(bpy.types.Operator):
    """Modal object selection with a ray cast"""
    bl_idname = "view3d.modal_operator_raycast"
    bl_label = "RayCast View Operator"

    _header_text = "Add: LMB, Undo: BackSpace, Finish: Enter"

    def _update_header(self, context):
        if self.pick_objects:
            pick_obj = self.pick_objects[-1][0]
            info_obj = "%s, %s" % (pick_obj.name, pick_obj.library.filepath if pick_obj.library is not None else "None")
            info = "%s - added: %s" % (ViewOperatorRayCast._header_text, info_obj)
        else:
            info = ViewOperatorRayCast._header_text

        context.area.header_text_set(info)

    def modal(self, context, event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navigation
            return {'PASS_THROUGH'}
        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                if pick_object(context, event, self.pick_objects):
                    self._update_header(context)
                return {'RUNNING_MODAL'}
        elif event.type == 'BACK_SPACE':
            if event.value == 'RELEASE':
                if self.pick_objects:
                    pick_obj = self.pick_objects.pop()
                    pick_restore(pick_obj)
                    self._update_header(context)

        elif event.type in {'RET', 'NUMPAD_ENTER'}:
            if event.value == 'RELEASE':
                if self.pick_objects:  # avoid enter taking effect on startup
                    pick_finalize(context, self.pick_objects)
                    context.area.header_text_set()
                    self.report({'INFO'}, "Finished")
                    return {'FINISHED'}
                
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            if event.value == 'RELEASE':
                for pick_obj in self.pick_objects:
                    pick_restore(pick_obj)
                context.area.header_text_set()
                self.report({'INFO'}, "Cancelled")
                return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            
            self.pick_objects = []
            self._update_header(context)

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(ViewOperatorRayCast)


def unregister():
    bpy.utils.unregister_class(ViewOperatorRayCast)


if __name__ == "__main__":
    register()
