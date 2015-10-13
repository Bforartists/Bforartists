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
    "name": "Clay Render",
    "author": "Fabio Russo <ruesp83@libero.it>",
    "version": (1, 2),
    "blender": (2, 56, 0),
    "location": "Render > Clay Render",
    "description": "This script, applies a temporary material to all objects"\
        " of the scene.",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Clay_Render",
    "tracker_url": "https://developer.blender.org/T22971",
    "category": "Render"}

import bpy
from bpy.props import BoolProperty


def Create_Mat():
    id = bpy.data.materials.new("Clay_Render")
    #diffuse
    id.diffuse_shader = "OREN_NAYAR"
    id.diffuse_color = 0.800, 0.741, 0.536
    id.diffuse_intensity = 1
    id.roughness = 0.909
    #specular
    id.specular_shader = "COOKTORR"
    id.specular_color = 1, 1, 1
    id.specular_hardness = 10
    id.specular_intensity = 0.115


def Alternative_Clay(self, msg):
    Find = False
    AM = None
    i = 0
    for mat in bpy.data.materials:
        if (mat.Mat_Clay) and (not Find):
            Find = True
            AM = mat
            i += 1

        else:
            if (mat.Mat_Clay):
                i += 1

    if msg is True:
        if (i == 1):
            self.report({'INFO'}, "The material \"" + AM.name + "\" is set "\
                "as Clay!")
        else:
            if (i > 1):
                self.report({'WARNING'}, "Two or more materials are set as "\
                    "Clay. \"" + AM.name + "\" will be used!")

    return AM


def Get_Mat():
    Mat = bpy.data.materials["Clay_Render"]
    return Mat


def Exist_Mat():
    if bpy.data.materials.get("Clay_Render"):
        return True

    else:
        return False


class ClayPinned(bpy.types.Operator):
    bl_idname = "render.clay_pinned"
    bl_label = "Clay Pinned"
    bl_description = "Clay Material Stores"

    def execute(self, context):
        if bpy.types.Scene.Clay_Pinned:
            bpy.types.Scene.Clay_Pinned = False
        else:
            if bpy.types.Scene.Clay:
                if bpy.data.materials[0].users == 0:
                    bpy.data.materials.remove(Get_Mat())
                    bpy.types.Scene.Clay_Pinned = True

            else:
                bpy.types.Scene.Clay_Pinned = True

        return {'FINISHED'}


class CheckClay(bpy.types.Operator):
    bl_idname = "render.clay"
    bl_label = "Clay Render"
    bl_description = "Use Clay Render"

    def execute(self, context):
        if bpy.types.Scene.Clay:
            #Clay Attivato
            ac = Alternative_Clay(self, True)
            if ac is None:
                if not Exist_Mat():
                    Create_Mat()
                rl = context.scene.render.layers
                rl.active.material_override = Get_Mat()

            else:
                context.scene.render.layers.active.material_override = ac

            bpy.types.Scene.Clay = False

        else:
            context.scene.render.layers.active.material_override = None
            if bpy.types.Scene.Clay_Pinned:
                if bpy.data.materials[0].users == 0:
                    bpy.data.materials.remove(Get_Mat())
            bpy.types.Scene.Clay = True

        return {'FINISHED'}


def draw_clay_render(self, context):
    ok_clay = not bpy.types.Scene.Clay
    pin = not bpy.types.Scene.Clay_Pinned

    rnl = context.scene.render.layers.active
    split = self.layout.split()
    col = split.column()

    col.operator(CheckClay.bl_idname, emboss=False, icon='CHECKBOX_HLT'\
        if ok_clay else 'CHECKBOX_DEHLT')
    col = split.column()
    if Alternative_Clay(self, False) is None:
        if Exist_Mat():
            if (bpy.data.materials[0].users == 0) or (ok_clay):
                row = col.row(align=True)
                im = Get_Mat()
                row.prop(im, "diffuse_color", text="")
                row.operator(ClayPinned.bl_idname, text="", icon='PINNED'\
                    if pin else 'UNPINNED')

                if ok_clay:
                    row.active = True

                else:
                    row.active = False

            else:
                col.label('Clay Material applied to an object')

    else:
        col.label('Custom Material Clay')

    self.layout.separator()


def draw_clay_options(self, context):
    cm = context.material
    layout = self.layout
    layout.prop(cm, "Mat_Clay", text="Clay")


def draw_clay_warning(self, context):
    if not bpy.types.Scene.Clay:
        self.layout.label("Render Clay Enabled", "ERROR")


def register():
    bpy.types.Scene.Clay = BoolProperty(
    name='Clay Render',
    description='Use Clay Render',
    default=False)

    bpy.types.Scene.Clay_Pinned = BoolProperty(
    name='Clay Pinned',
    description='Clay Material Stores',
    default=False)

    bpy.types.Material.Mat_Clay = bpy.props.BoolProperty(
        name='Use as Clay',
        description='Use as Clay',
        default=False)

    bpy.utils.register_class(ClayPinned)
    bpy.utils.register_class(CheckClay)
    bpy.types.RENDER_PT_render.prepend(draw_clay_render)
    bpy.types.MATERIAL_PT_options.append(draw_clay_options)
    bpy.types.INFO_HT_header.append(draw_clay_warning)


def unregister():
    bpy.context.scene.render.layers.active.material_override = None
    if (Exist_Mat()) and (bpy.data.materials[0].users == 0):
        bpy.data.materials.remove(Get_Mat())
    del bpy.types.Scene.Clay
    del bpy.types.Scene.Clay_Pinned
    del bpy.types.Material.Mat_Clay
    bpy.utils.unregister_class(ClayPinned)
    bpy.utils.unregister_class(CheckClay)
    bpy.types.RENDER_PT_render.remove(draw_clay_render)
    bpy.types.MATERIAL_PT_options.remove(draw_clay_options)
    bpy.types.INFO_HT_header.remove(draw_clay_warning)


if __name__ == "__main__":
    register()
