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

# <pep8-80 compliant>

bl_info = {
    "name": "UV Layout",
    "author": "Campbell Barton, Matt Ebb",
    "version": (1, 1, 1),
    "blender": (2, 80, 0),
    "location": "Image-Window > UVs > Export UV Layout",
    "description": "Export the UV layout as a 2D graphic",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Import-Export/UV_Layout",
    "support": 'OFFICIAL',
    "category": "Import-Export",
}


# @todo write the wiki page

if "bpy" in locals():
    import importlib
    if "export_uv_eps" in locals():
        importlib.reload(export_uv_eps)
    if "export_uv_png" in locals():
        importlib.reload(export_uv_png)
    if "export_uv_svg" in locals():
        importlib.reload(export_uv_svg)

import os
import bpy

from bpy.props import (
    StringProperty,
    BoolProperty,
    EnumProperty,
    IntVectorProperty,
    FloatProperty,
)


class ExportUVLayout(bpy.types.Operator):
    """Export UV layout to file"""

    bl_idname = "uv.export_layout"
    bl_label = "Export UV Layout"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        subtype='FILE_PATH',
    )
    export_all: BoolProperty(
        name="All UVs",
        description="Export all UVs in this mesh (not just visible ones)",
        default=False,
    )
    modified: BoolProperty(
        name="Modified",
        description="Exports UVs from the modified mesh",
        default=False,
    )
    mode: EnumProperty(
        items=(
            ('SVG', "Scalable Vector Graphic (.svg)",
             "Export the UV layout to a vector SVG file"),
            ('EPS', "Encapsulate PostScript (.eps)",
             "Export the UV layout to a vector EPS file"),
            ('PNG', "PNG Image (.png)",
             "Export the UV layout to a bitmap image"),
        ),
        name="Format",
        description="File format to export the UV layout to",
        default='PNG',
    )
    size: IntVectorProperty(
        size=2,
        default=(1024, 1024),
        min=8, max=32768,
        description="Dimensions of the exported file",
    )
    opacity: FloatProperty(
        name="Fill Opacity",
        min=0.0, max=1.0,
        default=0.25,
        description="Set amount of opacity for exported UV layout",
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH' and obj.data.uv_layers

    def invoke(self, context, event):
        self.size = self.get_image_size(context)
        self.filepath = self.get_default_file_name(context) + "." + self.mode.lower()
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def get_default_file_name(self, context):
        AMOUNT = 3
        objects = list(self.iter_objects_to_export(context))
        name = " ".join(sorted([obj.name for obj in objects[:AMOUNT]]))
        if len(objects) > AMOUNT:
            name += " and more"
        return name

    def check(self, context):
        if any(self.filepath.endswith(ext) for ext in (".png", ".eps", ".svg")):
            self.filepath = self.filepath[:-4]

        ext = "." + self.mode.lower()
        self.filepath = bpy.path.ensure_ext(self.filepath, ext)
        return True

    def execute(self, context):
        obj = context.active_object
        is_editmode = (obj.mode == 'EDIT')
        if is_editmode:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        filepath = self.filepath
        filepath = bpy.path.ensure_ext(filepath, "." + self.mode.lower())

        meshes = list(self.iter_meshes_to_export(context))
        polygon_data = list(self.iter_polygon_data_to_draw(context, meshes))
        different_colors = set(color for _, color in polygon_data)
        if self.modified:
            self.free_meshes(meshes)

        export = self.get_exporter()
        export(filepath, polygon_data, different_colors, self.size[0], self.size[1], self.opacity)

        if is_editmode:
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        return {'FINISHED'}

    def iter_meshes_to_export(self, context):
        depsgraph = context.evaluated_depsgraph_get()
        for obj in self.iter_objects_to_export(context):
            if self.modified:
                yield obj.evaluated_get(depsgraph).to_mesh()
            else:
                yield obj.data

    @staticmethod
    def iter_objects_to_export(context):
        for obj in {*context.selected_objects, context.active_object}:
            if obj.type != 'MESH':
                continue
            mesh = obj.data
            if mesh.uv_layers.active is None:
                continue
            yield obj

    @staticmethod
    def free_meshes(meshes):
        for mesh in meshes:
            bpy.data.meshes.remove(mesh)

    @staticmethod
    def currently_image_image_editor(context):
        return isinstance(context.space_data, bpy.types.SpaceImageEditor)

    def get_currently_opened_image(self, context):
        if not self.currently_image_image_editor(context):
            return None
        return context.space_data.image

    def get_image_size(self, context):
        # fallback if not in image context
        image_width = self.size[0]
        image_height = self.size[1]

        # get size of "active" image if some exist
        image = self.get_currently_opened_image(context)
        if image is not None:
            width, height = image.size
            if width and height:
                image_width = width
                image_height = height

        return image_width, image_height

    def iter_polygon_data_to_draw(self, context, meshes):
        for mesh in meshes:
            uv_layer = mesh.uv_layers.active.data
            for polygon in mesh.polygons:
                if self.export_all or polygon.select:
                    start = polygon.loop_start
                    end = start + polygon.loop_total
                    uvs = tuple(tuple(uv.uv) for uv in uv_layer[start:end])
                    yield (uvs, self.get_polygon_color(mesh, polygon))

    @staticmethod
    def get_polygon_color(mesh, polygon, default=(0.8, 0.8, 0.8)):
        if polygon.material_index < len(mesh.materials):
            material = mesh.materials[polygon.material_index]
            if material is not None:
                return tuple(material.diffuse_color)[:3]
        return default

    def get_exporter(self):
        if self.mode == 'PNG':
            from . import export_uv_png
            return export_uv_png.export
        elif self.mode == 'EPS':
            from . import export_uv_eps
            return export_uv_eps.export
        elif self.mode == 'SVG':
            from . import export_uv_svg
            return export_uv_svg.export
        else:
            assert False


def menu_func(self, context):
    self.layout.operator(ExportUVLayout.bl_idname)


def register():
    bpy.utils.register_class(ExportUVLayout)
    bpy.types.IMAGE_MT_uvs.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ExportUVLayout)
    bpy.types.IMAGE_MT_uvs.remove(menu_func)


if __name__ == "__main__":
    register()
