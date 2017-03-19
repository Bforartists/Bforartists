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
import bpy
from bpy.types import Panel


class CollectionButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "collection"


class COLLECTION_PT_context_collection(CollectionButtonsPanel, Panel):
    bl_label = ""
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        space = context.space_data

        collection = context.layer_collection
        name = collection.name
        if name == 'Master Collection':
            layout.label(text=name, icon='COLLAPSEMENU')
        else:
            layout.prop(collection, "name", text="", icon='COLLAPSEMENU')


def template_engine_settings(col, settings, name, use_icon_view=False):
    icons = {
            False: 'ZOOMIN',
            True: 'X',
            }

    use_name = "{0}_use".format(name)
    use = getattr(settings, use_name)

    row = col.row()
    col = row.column()
    col.active = use

    if use_icon_view:
        col.template_icon_view(settings, name)
    else:
        col.prop(settings, name)

    row.prop(settings, "{}_use".format(name), text="", icon=icons[use], emboss=False)


class COLLECTION_PT_clay_settings(CollectionButtonsPanel, Panel):
    bl_label = "Render Settings"
    COMPAT_ENGINES = {'BLENDER_CLAY'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        return scene and (scene.render.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        collection = context.layer_collection
        settings = collection.get_engine_settings()

        col = layout.column()
        template_engine_settings(col, settings, "type")
        template_engine_settings(col, settings, "matcap_icon", use_icon_view=True)
        template_engine_settings(col, settings, "matcap_rotation")
        template_engine_settings(col, settings, "matcap_hue")
        template_engine_settings(col, settings, "matcap_saturation")
        template_engine_settings(col, settings, "matcap_value")
        template_engine_settings(col, settings, "ssao_factor_cavity")
        template_engine_settings(col, settings, "ssao_factor_edge")
        template_engine_settings(col, settings, "ssao_distance")
        template_engine_settings(col, settings, "ssao_attenuation")


class COLLECTION_PT_object_mode_settings(CollectionButtonsPanel, Panel):
    bl_label = "Object Mode Settings"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and (ob.mode == 'OBJECT')

    def draw(self, context):
        layout = self.layout

        collection = context.layer_collection
        settings = collection.get_mode_settings('OBJECT')

        col = layout.column()
        template_engine_settings(col, settings, "show_wire")
        template_engine_settings(col, settings, "show_backface_culling")


class COLLECTION_PT_edit_mode_settings(CollectionButtonsPanel, Panel):
    bl_label = "Edit Mode Settings"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and (ob.mode == 'EDIT')

    def draw(self, context):
        layout = self.layout

        collection = context.layer_collection
        settings = collection.get_mode_settings('EDIT')

        col = layout.column()
        template_engine_settings(col, settings, "show_occlude_wire")
        template_engine_settings(col, settings, "backwire_opacity")
        template_engine_settings(col, settings, "face_normals_show")
        template_engine_settings(col, settings, "vert_normals_show")
        template_engine_settings(col, settings, "loop_normals_show")
        template_engine_settings(col, settings, "normals_length")


classes = (
    COLLECTION_PT_context_collection,
    COLLECTION_PT_clay_settings,
    COLLECTION_PT_object_mode_settings,
    COLLECTION_PT_edit_mode_settings,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
