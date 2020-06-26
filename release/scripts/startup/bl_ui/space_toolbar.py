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
from bpy.types import Header, Menu
from bpy.app.translations import contexts as i18n_contexts
#import math


class TOOLBAR_HT_header(Header):
    bl_space_type = 'TOOLBAR'

    def draw(self, context):
        layout = self.layout

        window = context.window
        scene = context.scene

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu
        TOOLBAR_MT_toolbar_type.draw_collapsible(context, layout) # bfa the toolbar type

        ############## toolbars ##########################################################################

        TOOLBAR_MT_file.hide_file_toolbar(context, layout) # bfa - show hide the complete toolbar container
        TOOLBAR_MT_meshedit.hide_meshedit_toolbar(context, layout)
        TOOLBAR_MT_primitives.hide_primitives_toolbar(context, layout)
        TOOLBAR_MT_image.hide_image_toolbar(context, layout)
        TOOLBAR_MT_tools.hide_tools_toolbar(context, layout)
        TOOLBAR_MT_animation.hide_animation_toolbar(context, layout)
        TOOLBAR_MT_edit.hide_edit_toolbar(context, layout)

        layout.separator_spacer()

        TOOLBAR_MT_misc.hide_misc_toolbar(context, layout)

########################################################################

# bfa - show hide the editortype menu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus

########################################################################

################ Toolbar type

# Everything menu in this class is collapsible.
class TOOLBAR_MT_toolbar_type(Menu):
    bl_idname = "TOOLBAR_MT_toolbar_type"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.operator("screen.toolbar_toolbox", text="Type")


######################################## Toolbars ##############################################


######################################## File ##############################################


#################### Holds the Toolbars menu for file, collapsible

class TOOLBAR_MT_menu_file(Menu):
    bl_idname = "TOOLBAR_MT_menu_file"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)


    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_file_menu") # see class TOOLBAR_MT_file below


##################### Load Save sub toolbars menu

class TOOLBAR_MT_toolbars_file_menu(Menu):
    bl_label = "Toolbars File"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.prop(addon_prefs, "file_load_save")
        layout.prop(addon_prefs, "file_link_append")
        layout.prop(addon_prefs, "file_import_menu")
        layout.prop(addon_prefs, "file_export_menu")

        layout.prop(addon_prefs, "file_import_common")
        layout.prop(addon_prefs, "file_import_common2")
        layout.prop(addon_prefs, "file_import_uncommon")
        layout.prop(addon_prefs, "file_export_common")
        layout.prop(addon_prefs, "file_export_common2")
        layout.prop(addon_prefs, "file_export_uncommon")

        layout.prop(addon_prefs, "file_render")
        layout.prop(addon_prefs, "file_render_opengl")
        layout.prop(addon_prefs, "file_render_misc")


############### bfa - Load Save menu hidable by the flag in the right click menu

class TOOLBAR_MT_file(Menu):
    bl_idname = "TOOLBAR_MT_file"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        TOOLBAR_MT_menu_file.draw_collapsible(context, layout)

        ## ------------------ Load / Save sub toolbars

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        if addon_prefs.file_load_save:

            row = layout.row(align=True)

            row.operator("wm.read_homefile", text="", icon='NEW')

            row = layout.row(align=True)

            row.menu("TOPBAR_MT_file_new", text="", icon='FILE_NEW')

            row = layout.row(align=True)

            row.operator("wm.open_mainfile", text="", icon='FILE_FOLDER')
            row.menu("TOPBAR_MT_file_open_recent", text="", icon='OPEN_RECENT')

            row = layout.row(align=True)

            row.operator("wm.save_mainfile", text="", icon='FILE_TICK')
            row.operator("wm.save_as_mainfile", text="", icon='SAVE_AS')
            row.operator("wm.save_as_mainfile", text="", icon='SAVE_COPY')

        ## ------------------ Link Append

        if addon_prefs.file_link_append:

            row = layout.row(align=True)

            row.operator("wm.link", text="", icon='LINK_BLEND')
            row.operator("wm.append", text="", icon='APPEND_BLEND')

        ## ------------------ Import menu

        if addon_prefs.file_import_menu:

            layout.menu("TOPBAR_MT_file_import", icon='IMPORT', text = "")

        if addon_prefs.file_export_menu:

            layout.menu("TOPBAR_MT_file_export", icon='EXPORT', text = "")

        ## ------------------ Import single types

        if addon_prefs.file_import_common:

            row = layout.row(align=True)

            row.operator("import_scene.fbx", text="", icon='LOAD_FBX')
            row.operator("import_scene.obj", text="", icon='LOAD_OBJ')
            row.operator("wm.alembic_import", text="", icon = "LOAD_ABC" )


        if addon_prefs.file_import_common2:

            row = layout.row(align=True)

            row.operator("wm.collada_import", text="", icon='LOAD_DAE')
            row.operator("import_anim.bvh", text="", icon='LOAD_BVH')
            #row.operator("import_scene.autodesk_3ds", text="", icon='LOAD_3DS') # bfa - not ported to 2.8 yet
            row.operator("import_scene.gltf", text="", icon='LOAD_GITF')


        ## ------------------ Import uncommon

        if addon_prefs.file_import_uncommon:

            row = layout.row(align=True)

            row.operator("import_mesh.stl", text="", icon='LOAD_STL')
            row.operator("import_mesh.ply", text="", icon='LOAD_PLY')
            row.operator("import_scene.x3d", text="", icon='LOAD_X3D')
            row.operator("import_curve.svg", text="", icon='LOAD_SVG')

        ## ------------------ Export common

        if addon_prefs.file_export_common:

            row = layout.row(align=True)

            row.operator("export_scene.fbx", text="", icon='SAVE_FBX')
            row.operator("export_scene.obj", text="", icon='SAVE_OBJ')
            row.operator("wm.alembic_export", text="", icon = "SAVE_ABC" )

        if addon_prefs.file_export_common2:

            row = layout.row(align=True)

            row.operator("wm.collada_export", text="", icon='SAVE_DAE')
            row.operator("export_anim.bvh", text="", icon='SAVE_BVH')
            #row.operator("export_scene.autodesk_3ds", text="", icon='SAVE_3DS') # bfa - not ported to 2.8 yet
            row.operator("export_scene.gltf", text="", icon='SAVE_GITF')

        ## ------------------ Export uncommon

        if addon_prefs.file_export_uncommon:

            row = layout.row(align=True)

            row.operator("export_mesh.stl", text="", icon='SAVE_STL')
            row.operator("export_mesh.ply", text="", icon='SAVE_PLY')
            row.operator("export_scene.x3d", text="", icon='SAVE_X3D')

        ## ------------------ Render

        if addon_prefs.file_render:

            row = layout.row(align=True)

            row.operator("render.render", text="", icon='RENDER_STILL').use_viewport = True
            props = row.operator("render.render", text="", icon='RENDER_ANIMATION')
            props.animation = True
            props.use_viewport = True

        ## ------------------ Render

        if addon_prefs.file_render_opengl:

            row = layout.row(align=True)

            row.operator("render.opengl", text="", icon = 'RENDER_STILL_VIEW')
            row.operator("render.opengl", text="", icon = 'RENDER_ANI_VIEW').animation = True

        ## ------------------ Render

        if addon_prefs.file_render_misc:

            row = layout.row(align=True)

            row.operator("sound.mixdown", text="", icon='PLAY_AUDIO')

            row = layout.row(align=True)

            row.operator("render.view_show", text="", icon = 'HIDE_RENDERVIEW')
            row.operator("render.play_rendered_anim", icon='PLAY', text="")



######################################## Mesh Edit ##############################################


#################### Holds the Toolbars menu for Mesh Edit, collapsible

class TOOLBAR_MT_menu_meshedit(Menu):
    bl_idname = "TOOLBAR_MT_menu_meshedit"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)


    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_meshedit_menu") # see class TOOLBAR_MT_file below


##################### Load Save sub toolbars menu

class TOOLBAR_MT_toolbars_meshedit_menu(Menu):
    bl_label = "Toolbars Mesh Edit"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.prop(addon_prefs, "mesh_vertices_splitconnect")
        layout.prop(addon_prefs, "mesh_vertices_misc")

        layout.prop(addon_prefs, "mesh_edges_subdiv")
        layout.prop(addon_prefs, "mesh_edges_sharp")
        layout.prop(addon_prefs, "mesh_edges_freestyle")
        layout.prop(addon_prefs, "mesh_edges_rotate")
        layout.prop(addon_prefs, "mesh_edges_misc")

        layout.prop(addon_prefs, "mesh_faces_general")
        layout.prop(addon_prefs, "mesh_faces_freestyle")
        layout.prop(addon_prefs, "mesh_faces_tris")
        layout.prop(addon_prefs, "mesh_faces_rotatemisc")

        layout.prop(addon_prefs, "mesh_cleanup")


############### bfa - Load Save menu hidable by the flag in the right click menu

class TOOLBAR_MT_meshedit(Menu):
    bl_idname = "TOOLBAR_MT_meshedit"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        TOOLBAR_MT_menu_meshedit.draw_collapsible(context, layout)

        ## ------------------ Vertices

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        obj = context.object
        if obj is not None:

            mode = obj.mode
            with_freestyle = bpy.app.build_options.freestyle

            if mode == 'EDIT':

                if obj.type == 'MESH':

                    if addon_prefs.mesh_vertices_splitconnect:

                        row = layout.row(align=True)

                        row.operator("mesh.split", text = "", icon = "SPLIT")
                        row.operator("mesh.vert_connect_path", text = "", icon = "VERTEXCONNECTPATH")
                        row.operator("mesh.vert_connect", text = "", icon = "VERTEXCONNECT")

                    if addon_prefs.mesh_vertices_misc:

                        row = layout.row(align=True)

                        with_bullet = bpy.app.build_options.bullet

                        if with_bullet:
                            row.operator("mesh.convex_hull", text = "", icon = "CONVEXHULL")

                        row.operator("mesh.blend_from_shape", text = "", icon = "BLENDFROMSHAPE")
                        row.operator("mesh.shape_propagate_to_all", text = "", icon = "SHAPEPROPAGATE")


                    ## ------------------ Edges

                    if addon_prefs.mesh_edges_subdiv:

                        row = layout.row(align=True)

                        row.operator("mesh.subdivide_edgering", text = "", icon = "SUBDIVEDGELOOP")
                        row.operator("mesh.unsubdivide", text = "", icon = "UNSUBDIVIDE")

                    if addon_prefs.mesh_edges_sharp:

                        row = layout.row(align=True)

                        row.operator("mesh.mark_sharp", text = "", icon = "MARKSHARPEDGES")
                        row.operator("mesh.mark_sharp", text = "", icon = "CLEARSHARPEDGES").clear = True

                    if addon_prefs.mesh_edges_freestyle:

                        row = layout.row(align=True)

                        if with_freestyle:
                            row.operator("mesh.mark_freestyle_edge", text = "", icon = "MARK_FS_EDGE").clear = False
                            row.operator("mesh.mark_freestyle_edge", text = "", icon = "CLEAR_FS_EDGE").clear = True

                    if addon_prefs.mesh_edges_rotate:

                        row = layout.row(align=True)

                        row.operator("mesh.edge_rotate", text = "", icon = "ROTATECW").use_ccw = False

                    if addon_prefs.mesh_edges_misc:

                        row = layout.row(align=True)

                        row.operator("mesh.edge_split", text = "", icon = "SPLITEDGE")
                        row.operator("mesh.bridge_edge_loops", text = "", icon = "BRIDGE_EDGELOOPS")

                    ## ------------------ Faces

                    if addon_prefs.mesh_faces_general:

                        row = layout.row(align=True)

                        with_freestyle = bpy.app.build_options.freestyle

                        row.operator("mesh.fill", text = "", icon = "FILL")
                        row.operator("mesh.fill_grid", text = "", icon = "GRIDFILL")
                        row.operator("mesh.beautify_fill", text = "", icon = "BEAUTIFY")
                        row.operator("mesh.solidify", text = "", icon = "SOLIDIFY")
                        row.operator("mesh.intersect", text = "", icon = "INTERSECT")
                        row.operator("mesh.intersect_boolean", text = "", icon = "BOOLEAN_INTERSECT")
                        row.operator("mesh.wireframe", text = "", icon = "WIREFRAME")

                    if addon_prefs.mesh_faces_freestyle:

                        row = layout.row(align=True)

                        if with_freestyle:
                            row.operator("mesh.mark_freestyle_face", text = "", icon = "MARKFSFACE").clear = False
                            row.operator("mesh.mark_freestyle_face", text = "", icon = "CLEARFSFACE").clear = True

                    if addon_prefs.mesh_faces_tris:

                        row = layout.row(align=True)

                        row.operator("mesh.poke", text = "", icon = "POKEFACES")
                        props = row.operator("mesh.quads_convert_to_tris", text = "", icon = "TRIANGULATE")
                        props.quad_method = props.ngon_method = 'BEAUTY'
                        row.operator("mesh.tris_convert_to_quads", text = "", icon = "TRISTOQUADS")
                        row.operator("mesh.face_split_by_edges", text = "", icon = "SPLITBYEDGES")

                    if addon_prefs.mesh_faces_rotatemisc:

                        row = layout.row(align=True)

                        row.operator("mesh.uvs_rotate", text = "", icon = "ROTATE_UVS")
                        row.operator("mesh.uvs_reverse", text = "", icon = "REVERSE_UVS")
                        row.operator("mesh.colors_rotate", text = "", icon = "ROTATE_COLORS")
                        row.operator("mesh.colors_reverse", text = "", icon = "REVERSE_COLORS")

                    ## ------------------ Cleanup

                    if addon_prefs.mesh_cleanup:

                        row = layout.row(align=True)

                        row.operator("mesh.delete_loose", text = "", icon = "DELETE_LOOSE")

                        row = layout.row(align=True)

                        row.operator("mesh.decimate", text = "", icon = "DECIMATE")
                        row.operator("mesh.dissolve_degenerate", text = "", icon = "DEGENERATE_DISSOLVE")
                        row.operator("mesh.face_make_planar", text = "", icon = "MAKE_PLANAR")
                        row.operator("mesh.vert_connect_nonplanar", text = "", icon = "SPLIT_NONPLANAR")
                        row.operator("mesh.vert_connect_concave", text = "", icon = "SPLIT_CONCAVE")
                        row.operator("mesh.fill_holes", text = "", icon = "FILL_HOLE")




######################################## Primitives ##############################################


#################### Holds the Toolbars menu for Primitives, collapsible

class TOOLBAR_MT_menu_primitives(Menu):
    bl_idname = "TOOLBAR_MT_menu_primitives"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_primitives_menu") # see class below


##################### Primitives toolbars menu

class TOOLBAR_MT_toolbars_primitives_menu(Menu):
    bl_label = "Toolbars Primitives"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.prop(addon_prefs, "primitives_mesh")
        layout.prop(addon_prefs, "primitives_curve")
        layout.prop(addon_prefs, "primitives_surface")
        layout.prop(addon_prefs, "primitives_metaball")
        layout.prop(addon_prefs, "primitives_gpencil")
        layout.prop(addon_prefs, "primitives_light")
        layout.prop(addon_prefs, "primitives_other")
        layout.prop(addon_prefs, "primitives_empties")
        layout.prop(addon_prefs, "primitives_image")
        layout.prop(addon_prefs, "primitives_lightprobe")
        layout.prop(addon_prefs, "primitives_forcefield")
        layout.prop(addon_prefs, "primitives_collection")


############### bfa - menu hidable by the flag in the right click menu

class TOOLBAR_MT_primitives(Menu):
    bl_idname = "TOOLBAR_MT_primitives"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        #rd = scene.render

        TOOLBAR_MT_menu_primitives.draw_collapsible(context, layout)

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        obj = context.object

        if obj is None:

            ## ------------------ primitives sub toolbars

            if addon_prefs.primitives_mesh:

                row = layout.row(align=True)

                row.operator("mesh.primitive_plane_add", text="", icon='MESH_PLANE')
                row.operator("mesh.primitive_cube_add", text="", icon='MESH_CUBE')
                row.operator("mesh.primitive_circle_add", text="", icon='MESH_CIRCLE')
                row.operator("mesh.primitive_uv_sphere_add", text="", icon='MESH_UVSPHERE')
                row.operator("mesh.primitive_ico_sphere_add", text="", icon='MESH_ICOSPHERE')
                row.operator("mesh.primitive_cylinder_add", text="", icon='MESH_CYLINDER')
                row.operator("mesh.primitive_cone_add", text="", icon='MESH_CONE')
                row.operator("mesh.primitive_torus_add", text="", icon='MESH_TORUS')
                row.operator("mesh.primitive_grid_add", text = "", icon='MESH_GRID')

            if addon_prefs.primitives_curve:

                row = layout.row(align=True)

                row.operator("curve.primitive_bezier_curve_add", text="", icon='CURVE_BEZCURVE')
                row.operator("curve.primitive_bezier_circle_add", text="", icon='CURVE_BEZCIRCLE')
                row.operator("curve.primitive_nurbs_curve_add", text="", icon='CURVE_NCURVE')
                row.operator("curve.primitive_nurbs_circle_add", text="", icon='CURVE_NCIRCLE')
                row.operator("curve.primitive_nurbs_path_add", text="", icon='CURVE_PATH')

            if addon_prefs.primitives_surface:

                row = layout.row(align=True)

                row.operator("surface.primitive_nurbs_surface_curve_add", text="", icon='SURFACE_NCURVE')
                row.operator("surface.primitive_nurbs_surface_circle_add", text="", icon='SURFACE_NCIRCLE')
                row.operator("surface.primitive_nurbs_surface_surface_add", text="", icon='SURFACE_NSURFACE')
                row.operator("surface.primitive_nurbs_surface_cylinder_add", text="", icon='SURFACE_NCYLINDER')
                row.operator("surface.primitive_nurbs_surface_sphere_add", text="", icon='SURFACE_NSPHERE')
                row.operator("surface.primitive_nurbs_surface_torus_add", text="", icon='SURFACE_NTORUS')

            if addon_prefs.primitives_metaball:

                row = layout.row(align=True)

                row.operator("object.metaball_add", text="", icon='META_BALL').type= 'BALL'
                row.operator("object.metaball_add", text="", icon='META_CAPSULE').type= 'CAPSULE'
                row.operator("object.metaball_add", text="", icon='META_PLANE').type= 'PLANE'
                row.operator("object.metaball_add", text="", icon='META_ELLIPSOID').type= 'ELLIPSOID'
                row.operator("object.metaball_add", text="", icon='META_CUBE').type= 'CUBE'

            if addon_prefs.primitives_gpencil:

                row = layout.row(align=True)

                row.operator("object.gpencil_add", text="", icon='EMPTY_AXIS').type= 'EMPTY'
                row.operator("object.gpencil_add", text="", icon='STROKE').type= 'STROKE'
                row.operator("object.gpencil_add", text="", icon='MONKEY').type= 'MONKEY'

            if addon_prefs.primitives_light:

                row = layout.row(align=True)

                row.operator("object.light_add", text="", icon='LIGHT_POINT').type= 'POINT'
                row.operator("object.light_add", text="", icon='LIGHT_SUN').type= 'SUN'
                row.operator("object.light_add", text="", icon='LIGHT_SPOT').type= 'SPOT'
                row.operator("object.light_add", text="", icon='LIGHT_AREA').type= 'AREA'

            if addon_prefs.primitives_other:

                row = layout.row(align=True)

                row.operator("object.text_add", text="", icon='OUTLINER_OB_FONT')
                row.operator("object.armature_add", text="", icon='OUTLINER_OB_ARMATURE')
                row.operator("object.add", text="", icon='OUTLINER_OB_LATTICE').type = 'LATTICE'
                row.operator("object.camera_add", text="", icon='OUTLINER_OB_CAMERA')
                row.operator("object.speaker_add", text="", icon='OUTLINER_OB_SPEAKER')

            if addon_prefs.primitives_empties:

                row = layout.row(align=True)

                row.operator("object.empty_add", text="", icon='OUTLINER_OB_EMPTY').type = 'PLAIN_AXES'
                row.operator("object.empty_add", text="", icon='EMPTY_SPHERE').type = 'SPHERE'
                row.operator("object.empty_add", text="", icon='EMPTY_CIRCLE').type = 'CIRCLE'
                row.operator("object.empty_add", text="", icon='EMPTY_CONE').type = 'CONE'
                row.operator("object.empty_add", text="", icon='EMPTY_CUBE').type = 'CUBE'
                row.operator("object.empty_add", text="", icon='EMPTY_SINGLE_ARROW').type = 'SINGLE_ARROW'
                row.operator("object.empty_add", text="", icon='EMPTY_ARROWS').type = 'ARROWS'
                row.operator("object.empty_add", text="", icon='EMPTY_IMAGE').type = 'IMAGE'

            if addon_prefs.primitives_image:

                row = layout.row(align=True)

                row.operator("object.load_reference_image", text="", icon='IMAGE_REFERENCE')
                row.operator("object.load_background_image", text="", icon='IMAGE_BACKGROUND')

            if addon_prefs.primitives_lightprobe:

                row = layout.row(align=True)

                row.operator("object.lightprobe_add", text="", icon='LIGHTPROBE_CUBEMAP').type='CUBEMAP'
                row.operator("object.lightprobe_add", text="", icon='LIGHTPROBE_PLANAR').type='PLANAR'
                row.operator("object.lightprobe_add", text="", icon='LIGHTPROBE_GRID').type='GRID'

            if addon_prefs.primitives_forcefield:

                row = layout.row(align=True)

                row.operator("object.effector_add", text="", icon='FORCE_BOID').type='BOID'
                row.operator("object.effector_add", text="", icon='FORCE_CHARGE').type='CHARGE'
                row.operator("object.effector_add", text="", icon='FORCE_CURVE').type='GUIDE'
                row.operator("object.effector_add", text="", icon='FORCE_DRAG').type='DRAG'
                row.operator("object.effector_add", text="", icon='FORCE_FORCE').type='FORCE'
                row.operator("object.effector_add", text="", icon='FORCE_HARMONIC').type='HARMONIC'
                row.operator("object.effector_add", text="", icon='FORCE_LENNARDJONES').type='LENNARDJ'
                row.operator("object.effector_add", text="", icon='FORCE_MAGNETIC').type='MAGNET'
                row.operator("object.effector_add", text="", icon='FORCE_FLUIDFLOW').type='SMOKE'
                row.operator("object.effector_add", text="", icon='FORCE_TEXTURE').type='TEXTURE'
                row.operator("object.effector_add", text="", icon='FORCE_TURBULENCE').type='TURBULENCE'
                row.operator("object.effector_add", text="", icon='FORCE_VORTEX').type='VORTEX'
                row.operator("object.effector_add", text="", icon='FORCE_WIND').type='WIND'

            if addon_prefs.primitives_collection:

                row = layout.row(align=True)

                row.operator("object.collection_instance_add", text="", icon='GROUP')

        elif obj is not None:

            mode = obj.mode

            if mode == 'OBJECT':

                ## ------------------ primitives sub toolbars

                if addon_prefs.primitives_mesh:

                    row = layout.row(align=True)

                    row.operator("mesh.primitive_plane_add", text="", icon='MESH_PLANE')
                    row.operator("mesh.primitive_cube_add", text="", icon='MESH_CUBE')
                    row.operator("mesh.primitive_circle_add", text="", icon='MESH_CIRCLE')
                    row.operator("mesh.primitive_uv_sphere_add", text="", icon='MESH_UVSPHERE')
                    row.operator("mesh.primitive_ico_sphere_add", text="", icon='MESH_ICOSPHERE')
                    row.operator("mesh.primitive_cylinder_add", text="", icon='MESH_CYLINDER')
                    row.operator("mesh.primitive_cone_add", text="", icon='MESH_CONE')
                    row.operator("mesh.primitive_torus_add", text="", icon='MESH_TORUS')
                    row.operator("mesh.primitive_grid_add", text = "", icon='MESH_GRID')

                if addon_prefs.primitives_curve:

                    row = layout.row(align=True)

                    row.operator("curve.primitive_bezier_curve_add", text="", icon='CURVE_BEZCURVE')
                    row.operator("curve.primitive_bezier_circle_add", text="", icon='CURVE_BEZCIRCLE')
                    row.operator("curve.primitive_nurbs_curve_add", text="", icon='CURVE_NCURVE')
                    row.operator("curve.primitive_nurbs_circle_add", text="", icon='CURVE_NCIRCLE')
                    row.operator("curve.primitive_nurbs_path_add", text="", icon='CURVE_PATH')

                if addon_prefs.primitives_surface:

                    row = layout.row(align=True)

                    row.operator("surface.primitive_nurbs_surface_curve_add", text="", icon='SURFACE_NCURVE')
                    row.operator("surface.primitive_nurbs_surface_circle_add", text="", icon='SURFACE_NCIRCLE')
                    row.operator("surface.primitive_nurbs_surface_surface_add", text="", icon='SURFACE_NSURFACE')
                    row.operator("surface.primitive_nurbs_surface_cylinder_add", text="", icon='SURFACE_NCYLINDER')
                    row.operator("surface.primitive_nurbs_surface_sphere_add", text="", icon='SURFACE_NSPHERE')
                    row.operator("surface.primitive_nurbs_surface_torus_add", text="", icon='SURFACE_NTORUS')

                if addon_prefs.primitives_metaball:

                    row = layout.row(align=True)

                    row.operator("object.metaball_add", text="", icon='META_BALL').type= 'BALL'
                    row.operator("object.metaball_add", text="", icon='META_CAPSULE').type= 'CAPSULE'
                    row.operator("object.metaball_add", text="", icon='META_PLANE').type= 'PLANE'
                    row.operator("object.metaball_add", text="", icon='META_ELLIPSOID').type= 'ELLIPSOID'
                    row.operator("object.metaball_add", text="", icon='META_CUBE').type= 'CUBE'

                if addon_prefs.primitives_gpencil:

                    row = layout.row(align=True)

                    row.operator("object.gpencil_add", text="", icon='EMPTY_AXIS').type= 'EMPTY'
                    row.operator("object.gpencil_add", text="", icon='STROKE').type= 'STROKE'
                    row.operator("object.gpencil_add", text="", icon='MONKEY').type= 'MONKEY'

                if addon_prefs.primitives_light:

                    row = layout.row(align=True)

                    row.operator("object.light_add", text="", icon='LIGHT_POINT').type= 'POINT'
                    row.operator("object.light_add", text="", icon='LIGHT_SUN').type= 'SUN'
                    row.operator("object.light_add", text="", icon='LIGHT_SPOT').type= 'SPOT'
                    row.operator("object.light_add", text="", icon='LIGHT_AREA').type= 'AREA'

                if addon_prefs.primitives_other:

                    row = layout.row(align=True)

                    row.operator("object.text_add", text="", icon='OUTLINER_OB_FONT')
                    row.operator("object.armature_add", text="", icon='OUTLINER_OB_ARMATURE')
                    row.operator("object.add", text="", icon='OUTLINER_OB_LATTICE').type = 'LATTICE'
                    row.operator("object.camera_add", text="", icon='OUTLINER_OB_CAMERA')
                    row.operator("object.speaker_add", text="", icon='OUTLINER_OB_SPEAKER')

                if addon_prefs.primitives_empties:

                    row = layout.row(align=True)

                    row.operator("object.empty_add", text="", icon='OUTLINER_OB_EMPTY').type = 'PLAIN_AXES'
                    row.operator("object.empty_add", text="", icon='EMPTY_SPHERE').type = 'SPHERE'
                    row.operator("object.empty_add", text="", icon='EMPTY_CIRCLE').type = 'CIRCLE'
                    row.operator("object.empty_add", text="", icon='EMPTY_CONE').type = 'CONE'
                    row.operator("object.empty_add", text="", icon='EMPTY_CUBE').type = 'CUBE'
                    row.operator("object.empty_add", text="", icon='EMPTY_SINGLE_ARROW').type = 'SINGLE_ARROW'       
                    row.operator("object.empty_add", text="", icon='EMPTY_ARROWS').type = 'ARROWS'
                    row.operator("object.empty_add", text="", icon='EMPTY_IMAGE').type = 'IMAGE'

                if addon_prefs.primitives_image:

                    row = layout.row(align=True)

                    row.operator("object.load_reference_image", text="", icon='IMAGE_REFERENCE')
                    row.operator("object.load_background_image", text="", icon='IMAGE_BACKGROUND')

                if addon_prefs.primitives_lightprobe:

                    row = layout.row(align=True)

                    row.operator("object.lightprobe_add", text="", icon='LIGHTPROBE_CUBEMAP').type='CUBEMAP'
                    row.operator("object.lightprobe_add", text="", icon='LIGHTPROBE_PLANAR').type='PLANAR'
                    row.operator("object.lightprobe_add", text="", icon='LIGHTPROBE_GRID').type='GRID'

                if addon_prefs.primitives_forcefield:

                    row = layout.row(align=True)

                    row.operator("object.effector_add", text="", icon='FORCE_BOID').type='BOID'
                    row.operator("object.effector_add", text="", icon='FORCE_CHARGE').type='CHARGE'
                    row.operator("object.effector_add", text="", icon='FORCE_CURVE').type='GUIDE'
                    row.operator("object.effector_add", text="", icon='FORCE_DRAG').type='DRAG'
                    row.operator("object.effector_add", text="", icon='FORCE_FORCE').type='FORCE'
                    row.operator("object.effector_add", text="", icon='FORCE_HARMONIC').type='HARMONIC'
                    row.operator("object.effector_add", text="", icon='FORCE_LENNARDJONES').type='LENNARDJ'
                    row.operator("object.effector_add", text="", icon='FORCE_MAGNETIC').type='MAGNET'
                    row.operator("object.effector_add", text="", icon='FORCE_FLUIDFLOW').type='SMOKE'
                    row.operator("object.effector_add", text="", icon='FORCE_TEXTURE').type='TEXTURE'
                    row.operator("object.effector_add", text="", icon='FORCE_TURBULENCE').type='TURBULENCE'
                    row.operator("object.effector_add", text="", icon='FORCE_VORTEX').type='VORTEX'
                    row.operator("object.effector_add", text="", icon='FORCE_WIND').type='WIND'

                if addon_prefs.primitives_collection:

                    row = layout.row(align=True)

                    row.operator("object.collection_instance_add", text="", icon='GROUP')

            if mode == 'EDIT':

                if obj.type == 'MESH':

                    if addon_prefs.primitives_mesh:

                        row = layout.row(align=True)

                        row.operator("mesh.primitive_plane_add", text="", icon='MESH_PLANE')
                        row.operator("mesh.primitive_cube_add", text="", icon='MESH_CUBE')
                        row.operator("mesh.primitive_circle_add", text="", icon='MESH_CIRCLE')
                        row.operator("mesh.primitive_uv_sphere_add", text="", icon='MESH_UVSPHERE')
                        row.operator("mesh.primitive_ico_sphere_add", text="", icon='MESH_ICOSPHERE')
                        row.operator("mesh.primitive_cylinder_add", text="", icon='MESH_CYLINDER')
                        row.operator("mesh.primitive_cone_add", text="", icon='MESH_CONE')
                        row.operator("mesh.primitive_torus_add", text="", icon='MESH_TORUS')
                        row.operator("mesh.primitive_grid_add", text = "", icon='MESH_GRID')

                if obj.type == 'CURVE':

                    if addon_prefs.primitives_curve:

                        row = layout.row(align=True)

                        row.operator("curve.primitive_bezier_curve_add", text="", icon='CURVE_BEZCURVE')
                        row.operator("curve.primitive_bezier_circle_add", text="", icon='CURVE_BEZCIRCLE')
                        row.operator("curve.primitive_nurbs_curve_add", text="", icon='CURVE_NCURVE')
                        row.operator("curve.primitive_nurbs_circle_add", text="", icon='CURVE_NCIRCLE')
                        row.operator("curve.primitive_nurbs_path_add", text="", icon='CURVE_PATH')

                if obj.type == 'SURFACE':

                    if addon_prefs.primitives_surface:

                        row = layout.row(align=True)

                        row.operator("surface.primitive_nurbs_surface_curve_add", text="", icon='SURFACE_NCURVE')
                        row.operator("surface.primitive_nurbs_surface_circle_add", text="", icon='SURFACE_NCIRCLE')
                        row.operator("surface.primitive_nurbs_surface_surface_add", text="", icon='SURFACE_NSURFACE')
                        row.operator("surface.primitive_nurbs_surface_cylinder_add", text="", icon='SURFACE_NCYLINDER')
                        row.operator("surface.primitive_nurbs_surface_sphere_add", text="", icon='SURFACE_NSPHERE')
                        row.operator("surface.primitive_nurbs_surface_torus_add", text="", icon='SURFACE_NTORUS')

                if obj.type == 'META':

                    if addon_prefs.primitives_metaball:

                        row = layout.row(align=True)

                        row.operator("object.metaball_add", text="", icon='META_BALL').type= 'BALL'
                        row.operator("object.metaball_add", text="", icon='META_CAPSULE').type= 'CAPSULE'
                        row.operator("object.metaball_add", text="", icon='META_PLANE').type= 'PLANE'
                        row.operator("object.metaball_add", text="", icon='META_ELLIPSOID').type= 'ELLIPSOID'
                        row.operator("object.metaball_add", text="", icon='META_CUBE').type= 'CUBE'


######################################## Image ##############################################

# Try to give unique tooltip fails at wrong context issue. Code remains for now. Maybe we find a solution here.

#class VIEW3D_MT_uv_straighten(bpy.types.Operator):
#    """Straighten\nStraightens the selected geometry"""
#    bl_idname = "image.uv_straighten"
#    bl_label = "straighten"
#    bl_options = {'REGISTER', 'UNDO'}

#    def execute(self, context):
#        for area in bpy.context.screen.areas:
#            if area.type == 'IMAGE_EDITOR':
#                override = bpy.context.copy()
#                override['area'] = area
#                bpy.ops.uv.align(axis = 'ALIGN_S')
#        return {'FINISHED'}


#################### Holds the Toolbars menu for Image, collapsible

class TOOLBAR_MT_menu_image(Menu):
    bl_idname = "TOOLBAR_MT_menu_image"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)


    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_image_menu") # see class below


##################### Image toolbars menu

class TOOLBAR_MT_toolbars_image_menu(Menu):
    bl_label = "Toolbars Image"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.prop(addon_prefs, "image_uv_align")
        layout.prop(addon_prefs, "image_uv_unwrap")
        layout.prop(addon_prefs, "image_uv_modify")


############### bfa - menu hidable by the flag in the right click menu

class TOOLBAR_MT_image(Menu):
    bl_idname = "TOOLBAR_MT_image"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        TOOLBAR_MT_menu_image.draw_collapsible(context, layout)

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        ## ------------------ image sub toolbars

        if addon_prefs.image_uv_align:

            row = layout.row(align=True)

            ############################################### doesn't work from toolbar

            #row.operator("transform.mirror", text="", icon = "MIRROR_X").constraint_axis[0] = True
            #row.operator("transform.mirror", text="", icon = "MIRROR_Y").constraint_axis[1] = True

            #row = layout.row(align=True)

            #row.operator("transform.rotate", text="", icon = "ROTATE_PLUS_90").value = math.pi / 2
            #row.operator("transform.rotate", text="", icon = "ROTATE_MINUS_90").value = math.pi / -2

            ################################################

            #row.operator_enum("uv.align", "axis")  # W, 2/3/4 # bfa - enum is no good idea in header. It enums below each other. And the header just shows besides ...

            row.operator("uv.align", text= "", icon = "STRAIGHTEN").axis = 'ALIGN_S'
            row.operator("uv.align", text= "", icon = "STRAIGHTEN_X").axis = 'ALIGN_T'
            row.operator("uv.align", text= "", icon = "STRAIGHTEN_Y").axis = 'ALIGN_U'
            row.operator("uv.align", text= "", icon = "ALIGNAUTO").axis = 'ALIGN_AUTO'
            row.operator("uv.align", text= "", icon = "ALIGNHORIZONTAL").axis = 'ALIGN_X'
            row.operator("uv.align", text= "", icon = "ALIGNVERTICAL").axis = 'ALIGN_Y'

            # Try to give unique tooltip fails at wrong context issue. It throws an error when you are not in edit mode, have no uv editor open, and there is no mesh selected.
            # Code remains here for now. Maybe we find a solution at a later point.
            #row.operator("image.uv_straighten", text= "straighten")

        if addon_prefs.image_uv_unwrap:

            row = layout.row(align=True)

            row.operator("uv.mark_seam", text="", icon ="MARK_SEAM").clear = False
            row.operator("uv.mark_seam", text="", icon ="CLEAR_SEAM").clear = True
            row.operator("uv.seams_from_islands", text="", icon ="SEAMSFROMISLAND")

            row = layout.row(align=True)

            row.operator("uv.unwrap", text = "", icon='UNWRAP_ABF').method='ANGLE_BASED'
            row.operator("uv.unwrap", text = "", icon='UNWRAP_LSCM').method='CONFORMAL'

        if addon_prefs.image_uv_modify:

            row = layout.row(align=True)

            row.operator("uv.pin", text= "", icon = "PINNED").clear = False
            row.operator("uv.pin", text="", icon = "UNPINNED").clear = True

            row = layout.row(align=True)

            row.operator("uv.weld", text="", icon='WELD')
            #row.operator("uv.stitch") # doesn't work in toolbar editor, needs to be performed in image editor where the uv mesh is.
            row.operator("uv.remove_doubles", text="", icon='REMOVE_DOUBLES')

            row = layout.row(align=True)

            row.operator("uv.average_islands_scale", text="", icon ="AVERAGEISLANDSCALE")
            row.operator("uv.pack_islands", text="", icon ="PACKISLAND")
            row.operator("mesh.faces_mirror_uv", text="", icon ="COPYMIRRORED")
            #row.operator("uv.minimize_stretch") # doesn't work in toolbar editor, needs to be performed in image editor where the uv mesh is.



######################################## Tools ##############################################

#################### Holds the Toolbars menu for Tools, collapsible

class TOOLBAR_MT_menu_tools(Menu):
    bl_idname = "TOOLBAR_MT_menu_tools"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)


    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_tools_menu") # see class below


##################### Tools toolbars menu

class TOOLBAR_MT_toolbars_tools_menu(Menu):
    bl_label = "Toolbars Tools"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.prop(addon_prefs, "tools_parent")
        layout.prop(addon_prefs, "tools_objectdata")
        layout.prop(addon_prefs, "tools_link_to_scn")
        layout.prop(addon_prefs, "tools_linked_objects")
        layout.prop(addon_prefs, "tools_join")
        layout.prop(addon_prefs, "tools_origin")
        layout.prop(addon_prefs, "tools_shading")
        layout.prop(addon_prefs, "tools_datatransfer")
        layout.prop(addon_prefs, "tools_relations")


############### bfa - menu hidable by the flag in the right click menu

class TOOLBAR_MT_tools(Menu):
    bl_idname = "TOOLBAR_MT_tools"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        TOOLBAR_MT_menu_tools.draw_collapsible(context, layout)

        obj = context.object

        ## ------------------ Tools sub toolbars

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        if obj is not None:

            mode = obj.mode

            if mode == 'OBJECT':

                if addon_prefs.tools_parent:

                    row = layout.row(align=True)

                    row.operator("object.parent_set", icon='PARENT_SET', text="")
                    row.operator("object.parent_clear", icon='PARENT_CLEAR', text="")

                if addon_prefs.tools_objectdata:

                    row = layout.row(align=True)

                    row.operator("object.make_single_user", icon='MAKE_SINGLE_USER', text="")
                    row.menu("VIEW3D_MT_make_links", text = "", icon='LINK_DATA' )


                if addon_prefs.tools_link_to_scn:

                    operator_context_default = layout.operator_context
                    if len(bpy.data.scenes) > 10:
                        layout.operator_context = 'INVOKE_REGION_WIN'
                        layout.operator("object.make_links_scene", text="Link to SCN", icon='OUTLINER_OB_EMPTY')
                    else:
                        layout.operator_context = 'EXEC_REGION_WIN'
                        layout.operator_menu_enum("object.make_links_scene", "scene", text="Link to SCN")

                if addon_prefs.tools_linked_objects:

                    row = layout.row(align=True)

                    row.operator("object.make_local", icon='MAKE_LOCAL', text="")
                    row.operator("object.proxy_make", icon='MAKE_PROXY', text="")

                if addon_prefs.tools_join:

                    obj_type = obj.type

                    row = layout.row(align=True)

                    if obj_type in {'MESH', 'CURVE', 'SURFACE', 'ARMATURE'}:
                        row.operator("object.join", icon ='JOIN', text= "" )

                if addon_prefs.tools_origin:

                    obj_type = obj.type

                    row = layout.row(align=True)

                    if obj_type in {'MESH', 'CURVE', 'SURFACE', 'ARMATURE', 'FONT', 'LATTICE'}:

                        row = layout.row(align=True)

                        row.operator("object.origin_set", icon ='GEOMETRY_TO_ORIGIN', text="").type='GEOMETRY_ORIGIN'
                        row.operator("object.origin_set", icon ='ORIGIN_TO_GEOMETRY', text="").type='ORIGIN_GEOMETRY'
                        row.operator("object.origin_set", icon ='ORIGIN_TO_CURSOR', text="").type='ORIGIN_CURSOR'
                        row.operator("object.origin_set", icon ='ORIGIN_TO_CENTEROFMASS', text="").type='ORIGIN_CENTER_OF_MASS'
                        row.operator("object.origin_set", icon ='ORIGIN_TO_VOLUME', text = "").type='ORIGIN_CENTER_OF_VOLUME'

                if addon_prefs.tools_shading:

                    obj_type = obj.type

                    row = layout.row(align=True)

                    if obj_type in {'MESH', 'CURVE', 'SURFACE'}:

                        row = layout.row(align=True)

                        row.operator("object.shade_smooth", icon ='SHADING_SMOOTH', text="")
                        row.operator("object.shade_flat", icon ='SHADING_FLAT', text="")

                if addon_prefs.tools_datatransfer:

                    obj_type = obj.type

                    row = layout.row(align=True)

                    if obj_type == 'MESH':

                        row = layout.row(align=True)

                        row.operator("object.data_transfer", icon ='TRANSFER_DATA', text="")
                        row.operator("object.datalayout_transfer", icon ='TRANSFER_DATA_LAYOUT', text="")
                        row.operator("object.join_uvs", icon ='TRANSFER_UV', text = "")


            if mode == 'EDIT':

                if addon_prefs.tools_relations:

                    row = layout.row(align=True)

                    row.operator("object.vertex_parent_set", text = "", icon = "VERTEX_PARENT" )

                    if obj.type == 'ARMATURE':

                        row = layout.row(align=True)

                        row.operator("armature.parent_set", icon='PARENT_SET', text="")
                        row.operator("armature.parent_clear", icon='PARENT_CLEAR', text="")

######################################## Animation ##############################################

#################### Holds the Toolbars menu for Animation, collapsible

class TOOLBAR_MT_menu_animation(Menu):
    bl_idname = "TOOLBAR_MT_menu_animation"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_animation_menu") # see class below

##################### Animation toolbars menu

class TOOLBAR_MT_toolbars_animation_menu(Menu):
    bl_label = "Toolbars Animation"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.prop(addon_prefs, "animation_keyframes")
        layout.prop(addon_prefs, "animation_play")
        layout.prop(addon_prefs, "animation_range")
        layout.prop(addon_prefs, "animation_keyframetype")
        layout.prop(addon_prefs, "animation_sync")
        layout.prop(addon_prefs, "animation_keyingset")


############### bfa - menu hidable by the flag in the right click menu

class TOOLBAR_MT_animation(Menu):
    bl_idname = "TOOLBAR_MT_animation"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        screen = context.screen
        toolsettings = context.tool_settings
        userprefs = context.preferences

        TOOLBAR_MT_menu_animation.draw_collapsible(context, layout)

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        ## ------------------ Animation sub toolbars

        if addon_prefs.animation_keyframes:

            obj = context.object

            if obj is not None:

                mode = obj.mode

                if mode == 'OBJECT':

                    row = layout.row(align=True)

                    row.operator("anim.keyframe_insert_menu", icon= 'KEYFRAMES_INSERT',text="")
                    row.operator("anim.keyframe_delete_v3d", icon= 'KEYFRAMES_REMOVE',text="")
                    row.operator("nla.bake", icon= 'BAKE_ACTION',text="")
                    row.operator("anim.keyframe_clear_v3d", icon= 'KEYFRAMES_CLEAR',text="")

                    row = layout.row(align=True)

                    row.operator("object.paths_calculate", icon ='MOTIONPATHS_CALCULATE',  text="")
                    row.operator("object.paths_clear", icon ='MOTIONPATHS_CLEAR',  text="")

                if mode == 'POSE':

                    row = layout.row(align=True)

                    row.operator("anim.keyframe_insert_menu", icon= 'KEYFRAMES_INSERT',text="")
                    row.operator("anim.keyframe_delete_v3d", icon= 'KEYFRAMES_REMOVE',text="")
                    row.operator("nla.bake", icon= 'BAKE_ACTION',text="")
                    row.operator("anim.keyframe_clear_v3d", icon= 'KEYFRAMES_CLEAR',text="")

                    row = layout.row(align=True)

                    row.operator("object.paths_calculate", icon ='MOTIONPATHS_CALCULATE',  text="")
                    row.operator("object.paths_clear", icon ='MOTIONPATHS_CLEAR',  text="")

        if addon_prefs.animation_play:

            row = layout.row(align=True)
            row.operator("screen.frame_jump", text="", icon='REW').end = False
            row.operator("screen.keyframe_jump", text="", icon='PREV_KEYFRAME').next = False

            if not screen.is_animation_playing:
                # if using JACK and A/V sync:
                #   hide the play-reversed button
                #   since JACK transport doesn't support reversed playback
                if scene.sync_mode == 'AUDIO_SYNC' and context.preferences.system.audio_device == 'JACK':
                    sub = row.row(align=True)
                    sub.scale_x = 1.4
                    sub.operator("screen.animation_play", text="", icon='PLAY')
                else:
                    row.operator("screen.animation_play", text="", icon='PLAY_REVERSE').reverse = True
                    row.operator("screen.animation_play", text="", icon='PLAY')
            else:
                sub = row.row(align=True)
                sub.scale_x = 1.4
                sub.operator("screen.animation_play", text="", icon='PAUSE')
            row.operator("screen.keyframe_jump", text="", icon='NEXT_KEYFRAME').next = True
            row.operator("screen.frame_jump", text="", icon='FF').end = True

            row = layout.row(align=True)

            row.prop(scene, "frame_current", text="")

        if addon_prefs.animation_range:

            row = layout.row(align=True)

            row.prop(scene, "use_preview_range", text="", toggle=True)
            row.prop(scene, "lock_frame_selection_to_range", text="", icon = "LOCKED", toggle=True)

            row = layout.row(align=True)
            if not scene.use_preview_range:
                row.prop(scene, "frame_start", text="Start")
                row.prop(scene, "frame_end", text="End")
            else:
                row.prop(scene, "frame_preview_start", text="Start")
                row.prop(scene, "frame_preview_end", text="End")

        if addon_prefs.animation_keyingset:

            row = layout.row(align=True)

            row.operator("anim.keyframe_insert", text="", icon='KEY_HLT')
            row.operator("anim.keyframe_delete", text="", icon='KEY_DEHLT')

            row = layout.row(align=True)

            row.prop(toolsettings, "use_keyframe_insert_auto", text="", toggle=True)

            row.prop_search(scene.keying_sets_all, "active", scene, "keying_sets_all", text="")


        if addon_prefs.animation_sync:

            row = layout.row(align=True)

            layout.prop(scene, "sync_mode", text="")

        if addon_prefs.animation_keyframetype:

            row = layout.row(align=True)

            layout.prop(toolsettings, "keyframe_type", text="", icon_only=True)


######################################## Edit toolbars ##############################################

class VIEW3D_MT_object_apply_location(bpy.types.Operator):
    """Apply Location\nApplies the current location"""
    bl_idname = "view3d.tb_apply_location"
    bl_label = "Apply Move"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        return {'FINISHED'}

class VIEW3D_MT_object_apply_rotate(bpy.types.Operator):
    """Apply Rotation\nApplies the current rotation"""
    bl_idname = "view3d.tb_apply_rotate"
    bl_label = "Apply Rotate"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        return {'FINISHED'}

class VIEW3D_MT_object_apply_scale(bpy.types.Operator):
    """Apply Scale\nApplies the current scale"""
    bl_idname = "view3d.tb_apply_scale"
    bl_label = "Apply Scale"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
        return {'FINISHED'}

class VIEW3D_MT_object_apply_all(bpy.types.Operator):
    """Apply All\nApplies the current location, rotation and scale"""
    bl_idname = "view3d.tb_apply_all"
    bl_label = "Apply All"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        return {'FINISHED'}

class VIEW3D_MT_object_apply_rotscale(bpy.types.Operator):
    """Apply Rotation & Scale\nApplies the current rotation and scale"""
    bl_idname = "view3d.tb_apply_rotscale"
    bl_label = "Apply Rotate Scale"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        return {'FINISHED'}

#################### Holds the Toolbars menu for Edit, collapsible

class TOOLBAR_MT_menu_edit(Menu):
    bl_idname = "TOOLBAR_MT_menu_edit"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_edit_menu") # see class below

##################### Tools toolbars menu

class TOOLBAR_MT_toolbars_edit_menu(Menu):
    bl_label = "Toolbars Edit"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.prop(addon_prefs, "edit_edit")
        layout.prop(addon_prefs, "edit_weightinedit")
        layout.prop(addon_prefs, "edit_objectapply")
        layout.prop(addon_prefs, "edit_objectapplydeltas")
        layout.prop(addon_prefs, "edit_objectclear")

############### bfa - menu hidable by the flag in the right click menu

class TOOLBAR_MT_edit(Menu):
    bl_idname = "TOOLBAR_MT_edit"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        obj = context.object

        TOOLBAR_MT_menu_edit.draw_collapsible(context, layout)

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        ## ------------------ Edit sub toolbars

        if obj is not None:

            if addon_prefs.edit_edit:

                mode = obj.mode

                if mode == 'EDIT':

                    row = layout.row(align=True)

                    row.operator("mesh.dissolve_verts", icon='DISSOLVE_VERTS', text="")
                    row.operator("mesh.dissolve_edges", icon='DISSOLVE_EDGES', text="")
                    row.operator("mesh.dissolve_faces", icon='DISSOLVE_FACES', text="")
                    row.operator("mesh.dissolve_limited", icon='DISSOLVE_LIMITED', text="")
                    row.operator("mesh.dissolve_mode", icon='DISSOLVE_SELECTION', text="")
                    row.operator("mesh.edge_collapse", icon='EDGE_COLLAPSE', text="")

                    row = layout.row(align=True)

                    row.operator("mesh.remove_doubles", icon='REMOVE_DOUBLES', text="")

                    row = layout.row(align=True)

                    row.operator_menu_enum("mesh.merge", "type", text = "", icon = "MERGE")
                    row.operator_menu_enum("mesh.separate", "type", text = "", icon = "SEPARATE")

            if addon_prefs.edit_weightinedit:

                mode = obj.mode

                if mode in ( 'EDIT', 'WEIGHT_PAINT'):

                    row = layout.row(align=True)

                    row.operator("object.vertex_group_normalize_all", icon='WEIGHT_NORMALIZE_ALL', text="")
                    row.operator("object.vertex_group_normalize",icon='WEIGHT_NORMALIZE', text="")
                    row.operator("object.vertex_group_mirror",icon='WEIGHT_MIRROR', text="")
                    row.operator("object.vertex_group_invert", icon='WEIGHT_INVERT',text="")
                    row.operator("object.vertex_group_clean", icon='WEIGHT_CLEAN',text="")
                    row.operator("object.vertex_group_quantize", icon='WEIGHT_QUANTIZE',text="")
                    row.operator("object.vertex_group_levels", icon='WEIGHT_LEVELS',text="")
                    row.operator("object.vertex_group_smooth", icon='WEIGHT_SMOOTH',text="")
                    row.operator("object.vertex_group_limit_total", icon='WEIGHT_LIMIT_TOTAL',text="")
                    row.operator("object.vertex_group_fix", icon='WEIGHT_FIX_DEFORMS',text="")

            if addon_prefs.edit_objectapply:

                mode = obj.mode

                if mode == 'OBJECT':

                    row = layout.row(align=True)

                    row.operator("view3d.tb_apply_location", text="", icon = "APPLYMOVE") # needed a tooltip, so see above ...
                    row.operator("view3d.tb_apply_rotate", text="", icon = "APPLYROTATE")
                    row.operator("view3d.tb_apply_scale", text="", icon = "APPLYSCALE")
                    row.operator("view3d.tb_apply_all", text="", icon = "APPLYALL")
                    row.operator("view3d.tb_apply_rotscale", text="", icon = "APPLY_ROTSCALE")

                    row = layout.row(align=True)

                    row.operator("object.visual_transform_apply", text = "", text_ctxt=i18n_contexts.default, icon = "VISUALTRANSFORM")
                    row.operator("object.duplicates_make_real", text = "", icon = "MAKEDUPLIREAL")

            if addon_prefs.edit_objectapplydeltas:

                if mode == 'OBJECT':

                    row = layout.row(align=True)

                    # TO DO - Useful tooltips
                    row.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYMOVEDELTA").mode = 'LOC'
                    row.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYROTATEDELTA").mode = 'ROT'
                    row.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYSCALEDELTA").mode = 'SCALE'

                    row.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYALLDELTA").mode = 'ALL'
                    row.operator("object.anim_transforms_to_deltas", text = "", icon = "APPLYANIDELTA")

            if addon_prefs.edit_objectclear:

                mode = obj.mode

                if mode == 'OBJECT':

                    row = layout.row(align=True)

                    row.operator("object.location_clear", text="", icon = "CLEARMOVE")
                    row.operator("object.rotation_clear", text="", icon = "CLEARROTATE")
                    row.operator("object.scale_clear", text="", icon = "CLEARSCALE")
                    row.operator("object.origin_clear", text="", icon = "CLEARORIGIN")

######################################## Misc ##############################################

#################### Holds the Toolbars menu for Misc, collapsible

class TOOLBAR_MT_menu_misc(Menu):
    bl_idname = "TOOLBAR_MT_menu_misc"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_misc_menu") # see class below

##################### Tools toolbars menu

class TOOLBAR_MT_toolbars_misc_menu(Menu):
    bl_label = "Toolbars Misc"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.prop(addon_prefs, "misc_undoredo")
        layout.prop(addon_prefs, "misc_undohistory")
        layout.prop(addon_prefs, "misc_repeat")
        layout.prop(addon_prefs, "misc_scene")
        layout.prop(addon_prefs, "misc_last")
        layout.prop(addon_prefs, "misc_operatorsearch")
        layout.prop(addon_prefs, "misc_info")

############### bfa - menu hidable by the flag in the right click menu

class TOOLBAR_MT_misc(Menu):
    bl_idname = "TOOLBAR_MT_misc"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        window = context.window
        screen = context.screen
        scene = window.scene
        obj = context.object

        TOOLBAR_MT_menu_misc.draw_collapsible(context, layout)

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        ## ------------------ Misc sub toolbars

        if addon_prefs.misc_undoredo:

            row = layout.row(align=True)

            row.operator("ed.undo", icon='UNDO',text="")
            row.operator("ed.redo", icon='REDO',text="")

        if addon_prefs.misc_undohistory:

            row = layout.row(align=True)
            row.operator("ed.undo_history", icon='UNDO_HISTORY',text="")

        if addon_prefs.misc_repeat:

            row = layout.row(align=True)

            row.operator("screen.repeat_last", icon='REPEAT', text="")
            row.operator("screen.repeat_history", icon='REDO_HISTORY', text="")

        if addon_prefs.misc_scene:

            row = layout.row(align=True)

            layout.template_ID(window, "scene", new="scene.new", unlink="scene.delete") # bfa - the scene drodpown box from the info menu bar

        if addon_prefs.misc_last:

            row = layout.row(align=True)

            row.operator("screen.redo_last", text="Last", icon = "LASTOPERATOR")

        if addon_prefs.misc_operatorsearch:

            row = layout.row(align=True)

            row.operator("wm.search_menu", text="", icon='VIEWZOOM')

        if addon_prefs.misc_info:

            row = layout.row(align=True)

            row.separator_spacer()

            # messages
            row.template_reports_banner()
            row.template_running_jobs()

            # stats
            scene = context.scene
            view_layer = context.view_layer

            row.label(text=scene.statistics(view_layer), translate=False)

classes = (

    TOOLBAR_HT_header,
    ALL_MT_editormenu,
    TOOLBAR_MT_toolbar_type,
    TOOLBAR_MT_menu_file,
    TOOLBAR_MT_toolbars_file_menu,
    TOOLBAR_MT_menu_misc,
    TOOLBAR_MT_toolbars_misc_menu,
    TOOLBAR_MT_menu_edit,
    TOOLBAR_MT_toolbars_edit_menu,
    VIEW3D_MT_object_apply_location,
    VIEW3D_MT_object_apply_rotate,
    VIEW3D_MT_object_apply_scale,
    VIEW3D_MT_object_apply_all,
    VIEW3D_MT_object_apply_rotscale,
    TOOLBAR_MT_menu_animation,
    TOOLBAR_MT_toolbars_animation_menu,
    TOOLBAR_MT_menu_tools,
    TOOLBAR_MT_toolbars_tools_menu,
    TOOLBAR_MT_menu_image,
    TOOLBAR_MT_toolbars_image_menu,
    TOOLBAR_MT_menu_primitives,
    TOOLBAR_MT_toolbars_primitives_menu,
    TOOLBAR_MT_menu_meshedit,
    TOOLBAR_MT_toolbars_meshedit_menu,

)


# -------------------- Register -------------------------------------------------------------------

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
