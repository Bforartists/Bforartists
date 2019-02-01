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
    "location": "View3D > Toolbar and View3D > Specials (W-key)",
    "description": "Tools for objects, render, shapes, and files.",
    "warning": "",
    "wiki_url": "https://www.oscurart.com.ar",
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
from oscurart_tools.object import distribute
from oscurart_tools.object import selection
from oscurart_tools.object import search_and_select
from oscurart_tools.mesh import apply_linked_meshes
from oscurart_tools.render import render_tokens
from oscurart_tools.render import batch_maker

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

        layout.operator("object.distribute_osc")
        layout.operator("object.search_and_select_osc")
        layout.operator("object.shape_key_to_objects_osc")
        layout.operator("mesh.apply_linked_meshes")        
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
    selection.OscSelection,
    save_incremental.saveIncrementalBackup,
    collect_images.collectImagesOsc,
    overlap_island.OscOverlapUv,
    select_doubles.SelectDoubles,
    shapes_to_objects.ShapeToObjects,
    search_and_select.SearchAndSelectOt,
    apply_linked_meshes.ApplyLRT,
    batch_maker.oscBatchMaker
    )

def register():   
    from bpy.types import Scene
    Scene.multimeshedit = StringProperty()
    bpy.types.VIEW3D_MT_edit_mesh_specials.prepend(menu_funcMesh)
    bpy.types.IMAGE_MT_uvs_specials.prepend(menu_funcImage)
    bpy.types.VIEW3D_MT_object_specials.prepend(menu_funcObject)
    bpy.app.handlers.render_pre.append(render_tokens.replaceTokens)
    bpy.app.handlers.render_cancel.append(render_tokens.restoreTokens) 
    bpy.app.handlers.render_post.append(render_tokens.restoreTokens) 
    

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)                                            
                                                                              

def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_funcMesh)
    bpy.types.IMAGE_MT_uvs_specials.remove(menu_funcImage)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_funcObject)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
