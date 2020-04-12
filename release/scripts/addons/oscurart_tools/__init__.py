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
    "name": "Oscurart Tools",
    "author": "Oscurart",
    "version": (4, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Context Menu > Object/Edit Modes",
    "description": "Tools for objects, render, shapes, and files.",
    "warning": "",
    "doc_url": "https://www.oscurart.com.ar",
    "category": "Object",
}


import bpy
from bpy.app.handlers import persistent
from bpy.types import Menu
from oscurart_tools.files import reload_images
from oscurart_tools.files import save_incremental
from oscurart_tools.files import collect_images
from oscurart_tools.mesh import overlap_uvs
from oscurart_tools.mesh import overlap_island
from oscurart_tools.mesh import select_doubles
from oscurart_tools.mesh import shapes_to_objects
from oscurart_tools.mesh import remove_modifiers
from oscurart_tools.mesh import vertex_color_id
from oscurart_tools.object import distribute
from oscurart_tools.object import selection
from oscurart_tools.object import search_and_select
from oscurart_tools.mesh import apply_linked_meshes
from oscurart_tools.render import render_tokens
from oscurart_tools.render import batch_maker
from oscurart_tools.render import material_overrides
from oscurart_tools.mesh import flipped_uvs
from oscurart_tools.mesh import print_uv_stats

from bpy.types import (
        AddonPreferences,
        Panel,
        PropertyGroup,
        )
from bpy.props import (
        StringProperty,
        BoolProperty,
        IntProperty,
        PointerProperty,
        CollectionProperty,
        )

# mesh
class VIEW3D_MT_edit_mesh_oscurarttools(Menu):
    bl_label = "OscurartTools"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.uv_island_copy")
        layout.operator("mesh.uv_island_paste")
        layout.operator("mesh.select_doubles")
        layout.operator("mesh.print_uv_stats")        
        layout.separator()
        layout.operator("image.reload_images_osc")
        layout.operator("file.save_incremental_backup")
        layout.operator("file.collect_all_images")
        layout.operator("file.create_batch_maker_osc")


def menu_funcMesh(self, context):
    self.layout.menu("VIEW3D_MT_edit_mesh_oscurarttools")
    self.layout.separator()

# image
class IMAGE_MT_uvs_oscurarttools(Menu):
    bl_label = "OscurartTools"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.uv_island_copy")
        layout.operator("mesh.uv_island_paste")
        layout.operator("mesh.overlap_uv_faces")
        layout.operator("mesh.select_flipped_uvs")
        layout.separator()
        layout.operator("image.reload_images_osc")
        layout.operator("file.save_incremental_backup")
        layout.operator("file.collect_all_images")
        layout.operator("file.create_batch_maker_osc")


def menu_funcImage(self, context):
    self.layout.menu("IMAGE_MT_uvs_oscurarttools")
    self.layout.separator()


# object
class VIEW3D_MT_object_oscurarttools(Menu):
    bl_label = "OscurartTools"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.vertex_color_mask")
        layout.operator("object.distribute_osc")
        layout.operator("mesh.remove_modifiers")
        layout.operator("object.search_and_select_osc")
        layout.operator("object.shape_key_to_objects_osc")
        layout.operator("mesh.apply_linked_meshes")
        layout.operator("mesh.print_uv_stats")        
        layout.separator()
        layout.operator("image.reload_images_osc")
        layout.operator("file.save_incremental_backup")
        layout.operator("file.collect_all_images")
        layout.operator("file.create_batch_maker_osc")

def menu_funcObject(self, context):
    self.layout.menu("VIEW3D_MT_object_oscurarttools")
    self.layout.separator()

# ========================= End of Scripts =========================


classes = (
    VIEW3D_MT_edit_mesh_oscurarttools,
    IMAGE_MT_uvs_oscurarttools,
    VIEW3D_MT_object_oscurarttools,
    reload_images.reloadImages,
    overlap_uvs.CopyUvIsland,
    overlap_uvs.PasteUvIsland,
    distribute.DistributeOsc,
    selection.OSSELECTION_HT_OscSelection,
    save_incremental.saveIncrementalBackup,
    collect_images.collectImagesOsc,
    overlap_island.OscOverlapUv,
    select_doubles.SelectDoubles,
    shapes_to_objects.ShapeToObjects,
    search_and_select.SearchAndSelectOt,
    apply_linked_meshes.ApplyLRT,
    batch_maker.oscBatchMaker,
    remove_modifiers.RemoveModifiers,
    vertex_color_id.createVCMask,
    material_overrides.OVERRIDES_PT_OscOverridesGUI,
    material_overrides.OscTransferOverrides,
    material_overrides.OscAddOverridesSlot,
    material_overrides.OscRemoveOverridesSlot,
    material_overrides.OscOverridesUp,
    material_overrides.OscOverridesDown,
    material_overrides.OscOverridesKill,
    flipped_uvs.selectFlippedUvs,
    print_uv_stats.uvStats
    )

def register():
    from bpy.types import Scene
    Scene.multimeshedit = StringProperty()
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.prepend(menu_funcMesh)
    bpy.types.IMAGE_MT_uvs_context_menu.prepend(menu_funcImage)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(menu_funcObject)
    bpy.app.handlers.render_init.append(render_tokens.replaceTokens)
    bpy.app.handlers.render_cancel.append(render_tokens.restoreTokens)
    bpy.app.handlers.render_complete.append(render_tokens.restoreTokens)
    bpy.app.handlers.render_pre.append(material_overrides.ApplyOverrides)
    bpy.app.handlers.render_cancel.append(material_overrides.RestoreOverrides)
    bpy.app.handlers.render_post.append(material_overrides.RestoreOverrides)

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_funcMesh)
    bpy.types.IMAGE_MT_uvs_context_menu.remove(menu_funcImage)
    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_funcObject)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
