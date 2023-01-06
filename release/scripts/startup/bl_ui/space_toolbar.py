# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>
import bpy
import math
from bpy.types import (
    Header,
    Menu,
    Panel,
)
from bpy.app.translations import contexts as i18n_contexts
#import math

class TOOLBAR_HT_header(Header):
    bl_space_type = 'TOOLBAR'

    def draw(self, context):
        layout = self.layout

        window = context.window
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu

        layout.popover(panel="TOOLBAR_PT_type", text = "")

        ############## toolbars ##########################################################################

        if addon_prefs.toolbar_show_quicktoggle:
            layout.scale_x = 0.7
            layout.operator("screen.header_toolbar_file", text = "", icon = "THREE_DOTS")
            layout.scale_x = 1
            TOOLBAR_MT_file.hide_file_toolbar(context, layout) # bfa - show hide the complete toolbar container
            layout.scale_x = 0.7
            layout.operator("screen.header_toolbar_meshedit", text = "", icon = "THREE_DOTS")
            layout.scale_x = 1
            TOOLBAR_MT_meshedit.hide_meshedit_toolbar(context, layout)
            layout.scale_x = 0.7
            layout.operator("screen.header_toolbar_primitives", text = "", icon = "THREE_DOTS")
            layout.scale_x = 1
            TOOLBAR_MT_primitives.hide_primitives_toolbar(context, layout)
            layout.scale_x = 0.7
            layout.operator("screen.header_toolbar_image", text = "", icon = "THREE_DOTS")
            layout.scale_x = 1
            TOOLBAR_MT_image.hide_image_toolbar(context, layout)
            layout.scale_x = 0.7
            layout.operator("screen.header_toolbar_tools", text = "", icon = "THREE_DOTS")
            layout.scale_x = 1
            TOOLBAR_MT_tools.hide_tools_toolbar(context, layout)
            layout.scale_x = 0.7
            layout.operator("screen.header_toolbar_animation", text = "", icon = "THREE_DOTS")
            layout.scale_x = 1
            TOOLBAR_MT_animation.hide_animation_toolbar(context, layout)
            layout.scale_x = 0.7
            layout.operator("screen.header_toolbar_edit", text = "", icon = "THREE_DOTS")
            layout.scale_x = 1
            TOOLBAR_MT_edit.hide_edit_toolbar(context, layout)

            layout.separator_spacer()
            layout.scale_x = 0.7
            layout.operator("screen.header_toolbar_misc", text = "", icon = "THREE_DOTS")
            layout.scale_x = 1
            TOOLBAR_MT_misc.hide_misc_toolbar(context, layout)
        else:

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

############################### Toolbar Type Panel ########################################

class TOOLBAR_PT_type(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Toolbar Types"

    def draw(self, context):
        layout = self.layout
        screen = bpy.ops.screen

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.label(text = "Toolbar Types:")
        # bfa - for toolbar types in context.area to show or hide
        # the toolbar content see bpy_types.py - class Menu

        col = layout.column(align = True)

        row = col.row()
        if not context.area.file_toolbars:
            row.active_default = True
        row.separator()
        row.operator("screen.header_toolbar_file", text = "File")

        row = col.row()
        if not context.area.meshedit_toolbars:
            row.active_default = True
        row.separator()
        row.operator("screen.header_toolbar_meshedit", text = "Meshedit")

        row = col.row()
        if not context.area.primitives_toolbars:
            row.active_default = True
        row.separator()
        row.operator("screen.header_toolbar_primitives", text = "Primitives")

        row = col.row()
        if not context.area.image_toolbars:
            row.active_default = True
        row.separator()
        row.operator("screen.header_toolbar_image", text = "Image")

        row = col.row()
        if not context.area.tools_toolbars:
            row.active_default = True
        row.separator()
        row.operator("screen.header_toolbar_tools", text = "Tools")

        row = col.row()
        if not context.area.animation_toolbars:
            row.active_default = True
        row.separator()
        row.operator("screen.header_toolbar_animation", text = "Animation")

        row = col.row()
        if not context.area.edit_toolbars:
            row.active_default = True
        row.separator()
        row.operator("screen.header_toolbar_edit", text = "Edit")

        row = col.row()
        if not context.area.misc_toolbars:
            row.active_default = True
        row.separator()
        row.operator("screen.header_toolbar_misc", text = "Misc")

        row = col.row()
        row.separator()
        row.label( text = "Note that you need to save the")
        row = col.row()
        row.separator()
        row.label( text = "startup file to make the changes")
        row = col.row()
        row.separator()
        row.label( text = "at the toolbar types permanent")


        col = layout.column()
        col.label( text = "Options:")
        row = layout.row()
        row.separator()
        row.prop(addon_prefs, "toolbar_show_quicktoggle")

#######################################################################

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

class TOOLBAR_PT_menu_file(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Toolbars File"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.label(text = "Toolbars File:")

        col = layout.column(align = True)
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "file_load_save")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "file_recover")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "file_link_append")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "file_import_menu")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "file_export_menu")

        col = layout.column(align = True)
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "file_import_common")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "file_import_common2")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "file_import_uncommon")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "file_export_common")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "file_export_common2")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "file_export_uncommon")

        col = layout.column(align = True)
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "file_render")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "file_render_opengl")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "file_render_misc")


############### bfa - Load Save menu hidable by the flag in the right click menu

class TOOLBAR_MT_file(Menu):
    bl_idname = "TOOLBAR_MT_file"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        layout.popover(panel="TOOLBAR_PT_menu_file", text = "")

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

        if addon_prefs.file_recover:

            row = layout.row(align=True)
            row.operator("wm.revert_mainfile", text="", icon='FILE_REFRESH')
            row.operator("wm.recover_last_session", text="", icon='RECOVER_LAST')
            row.operator("wm.recover_auto_save", text="", icon='RECOVER_AUTO')

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
            row.operator("wm.obj_import", text="", icon='LOAD_OBJ')
            row.operator("wm.alembic_import", text="", icon = "LOAD_ABC" )


        if addon_prefs.file_import_common2:

            row = layout.row(align=True)
            row.operator("wm.collada_import", text="", icon='LOAD_DAE')
            row.operator("import_anim.bvh", text="", icon='LOAD_BVH')
            row.operator("import_scene.gltf", text="", icon='LOAD_GLTF')


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
            row.operator("wm.obj_export", text="", icon='SAVE_OBJ')
            row.operator("wm.alembic_export", text="", icon = "SAVE_ABC" )

        if addon_prefs.file_export_common2:

            row = layout.row(align=True)
            row.operator("wm.collada_export", text="", icon='SAVE_DAE')
            row.operator("export_anim.bvh", text="", icon='SAVE_BVH')
            row.operator("wm.usd_export", text="", icon='SAVE_USD')
            row.operator("export_scene.gltf", text="", icon='SAVE_GLTF')

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


class TOOLBAR_PT_menu_meshedit(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Toolbars Mesh Edit"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.label(text = "Toolbars Mesh Edit:")

        col = layout.column(align = True)
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "mesh_vertices_splitconnect")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "mesh_vertices_misc")

        col = layout.column(align = True)
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "mesh_edges_subdiv")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "mesh_edges_sharp")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "mesh_edges_freestyle")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "mesh_edges_misc")

        col = layout.column(align = True)
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "mesh_faces_general")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "mesh_faces_freestyle")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "mesh_faces_tris")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "mesh_faces_rotatemisc")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "mesh_cleanup")


############### bfa - Load Save menu hidable by the flag in the right click menu


class TOOLBAR_MT_meshedit(Menu):
    bl_idname = "TOOLBAR_MT_meshedit"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        layout.popover(panel="TOOLBAR_PT_menu_meshedit", text = "")

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

                        with_freestyle = bpy.app.build_options.freestyle
                        row = layout.row(align=True)
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


class TOOLBAR_PT_menu_primitives(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Toolbars Primitives"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.label(text = "Toolbars Primitives:")

        col = layout.column(align = True)
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "primitives_mesh")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "primitives_curve")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "primitives_surface")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "primitives_metaball")

        col = layout.column(align = True)
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "primitives_volume")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "primitives_point_cloud")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "primitives_gpencil")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "primitives_gpencil_lineart")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "primitives_light")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "primitives_other")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "primitives_empties")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "primitives_image")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "primitives_lightprobe")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "primitives_forcefield")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "primitives_collection")


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

        layout.popover(panel="TOOLBAR_PT_menu_primitives", text = "")

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

            if addon_prefs.primitives_point_cloud:

                row = layout.row(align=True)
                row.operator("object.pointcloud_add", text="", icon='OUTLINER_OB_POINTCLOUD')


            if addon_prefs.primitives_volume:

                row = layout.row(align=True)
                row.operator("object.volume_import", text="", icon='FILE_VOLUME')
                row.operator("object.volume_add", text="", icon='OUTLINER_OB_VOLUME')

            if addon_prefs.primitives_gpencil:

                row = layout.row(align=True)
                row.operator("object.gpencil_add", text="", icon='EMPTY_AXIS').type= 'EMPTY'
                row.operator("object.gpencil_add", text="", icon='STROKE').type= 'STROKE'
                row.operator("object.gpencil_add", text="", icon='MONKEY').type= 'MONKEY'

            if addon_prefs.primitives_gpencil_lineart:

                row = layout.row(align=True)
                row.operator("object.gpencil_add", text="", icon='LINEART_SCENE').type= 'LRT_SCENE'
                row.operator("object.gpencil_add", text="", icon='LINEART_COLLECTION').type= 'LRT_COLLECTION'
                row.operator("object.gpencil_add", text="", icon='LINEART_OBJECT').type= 'LRT_OBJECT'

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
                row.operator("object.camera_add", text="", icon='OUTLINER_OB_CAMERA').rotation = (1.5708, 0.0, 0.0)
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
                row.operator("object.effector_add", text="", icon='FORCE_FLUIDFLOW').type='FLUID'
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

                if addon_prefs.primitives_point_cloud:

                    row = layout.row(align=True)
                    row.operator("object.pointcloud_add", text="", icon='OUTLINER_OB_POINTCLOUD')

                if addon_prefs.primitives_volume:

                    row = layout.row(align=True)
                    row.operator("object.volume_import", text="", icon='FILE_VOLUME')
                    row.operator("object.volume_add", text="", icon='OUTLINER_OB_VOLUME')

                if addon_prefs.primitives_gpencil:

                    row = layout.row(align=True)
                    row.operator("object.gpencil_add", text="", icon='EMPTY_AXIS').type= 'EMPTY'
                    row.operator("object.gpencil_add", text="", icon='STROKE').type= 'STROKE'
                    row.operator("object.gpencil_add", text="", icon='MONKEY').type= 'MONKEY'

                if addon_prefs.primitives_gpencil_lineart:

                    row = layout.row(align=True)
                    row.operator("object.gpencil_add", text="", icon='LINEART_SCENE').type= 'LRT_SCENE'
                    row.operator("object.gpencil_add", text="", icon='LINEART_COLLECTION').type= 'LRT_COLLECTION'
                    row.operator("object.gpencil_add", text="", icon='LINEART_OBJECT').type= 'LRT_OBJECT'

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
                    row.operator("object.camera_add", text="", icon='OUTLINER_OB_CAMERA').rotation = (1.5708, 0.0, 0.0)
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
                    row.operator("object.effector_add", text="", icon='FORCE_FLUIDFLOW').type='FLUID'
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


class TOOLBAR_PT_menu_image(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Toolbars Image"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.label(text = "Toolbars Image:")

        col = layout.column(align = True)
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "image_uv_mirror")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "image_uv_rotate")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "image_uv_align")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "image_uv_unwrap")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "image_uv_modify")


############### bfa - menu hidable by the flag in the right click menu

# special classes to call the rotate functionality in the image editor from the toolbar editor
# Original operators doesn't work directly from toolbar
class TOOLBAR_MT_image_uv_rotate_clockwise(bpy.types.Operator):
    """Rotate selected UV geometry clockwise by 90 degrees"""
    bl_idname = "image.uv_rotate_clockwise"
    bl_label = "Rotate UV by 90"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for area in bpy.context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.transform.rotate(override, value = math.pi/2 )
        return {'FINISHED'}


class TOOLBAR_MT_image_uv_rotate_counterclockwise(bpy.types.Operator):
    """Rotate selected UV geometry counter clockwise by 90 degrees"""
    bl_idname = "image.uv_rotate_counterclockwise"
    bl_label = "Rotate UV by minus 90"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for area in bpy.context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.transform.rotate(override, value = math.pi/-2 )
        return {'FINISHED'}


class TOOLBAR_MT_image_uv_mirror_x(bpy.types.Operator):
    """Mirror selected UV geometry along X axis"""
    bl_idname = "image.uv_mirror_x"
    bl_label = "Mirror X"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for area in bpy.context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.transform.mirror(override, constraint_axis=(True, False, False))
        return {'FINISHED'}


class TOOLBAR_MT_image_uv_mirror_y(bpy.types.Operator):
    """Mirror selected UV geometry along Y axis"""
    bl_idname = "image.uv_mirror_y"
    bl_label = "Mirror Y"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for area in bpy.context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.transform.mirror(override, constraint_axis=(False, True, False))
        return {'FINISHED'}


class TOOLBAR_MT_image(Menu):
    bl_idname = "TOOLBAR_MT_image"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        layout.popover(panel="TOOLBAR_PT_menu_image", text = "")

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        obj = context.active_object
        mode = 'OBJECT' if obj is None else obj.mode

        ## ------------------ image sub toolbars

        if addon_prefs.image_uv_mirror:

            row = layout.row(align=True)

            row.operator("image.uv_mirror_x", text="", icon = "MIRROR_X")
            row.operator("image.uv_mirror_y", text="", icon = "MIRROR_Y")

        if addon_prefs.image_uv_rotate:

            row = layout.row(align=True)

            row.operator("image.uv_rotate_clockwise", text="", icon = "ROTATE_PLUS_90")
            row.operator("image.uv_rotate_counterclockwise", text="", icon = "ROTATE_MINUS_90")

        if addon_prefs.image_uv_align:

            row = layout.row(align=True)

            #row.operator_enum("uv.align", "axis")  # W, 2/3/4 # bfa - enum is no good idea in header. It enums below each other. And the header just shows besides ...

            row.operator("uv.align", text= "", icon = "ALIGN").axis = 'ALIGN_S'
            row.operator("uv.align", text= "", icon = "STRAIGHTEN_X").axis = 'ALIGN_T'
            row.operator("uv.align", text= "", icon = "STRAIGHTEN_Y").axis = 'ALIGN_U'
            row.operator("uv.align", text= "", icon = "ALIGNAUTO").axis = 'ALIGN_AUTO'
            row.operator("uv.align", text= "", icon = "ALIGNHORIZONTAL").axis = 'ALIGN_X'
            row.operator("uv.align", text= "", icon = "ALIGNVERTICAL").axis = 'ALIGN_Y'
            row.operator("uv.align_rotation", text= "", icon = "DRIVER_ROTATIONAL_DIFFERENCE")

            # Try to give unique tooltip fails at wrong context issue. It throws an error when you are not in edit mode, have no uv editor open, and there is no mesh selected.
            # Code remains here for now. Maybe we find a solution at a later point.
            #row.operator("image.uv_straighten", text= "straighten")

        if addon_prefs.image_uv_unwrap:

            row = layout.row(align=True)
            row.operator("uv.mark_seam", text="", icon ="MARK_SEAM").clear = False
            sub = row.row()
            sub.active = (mode == 'EDIT')
            sub.operator("uv.clear_seam", text="", icon ="CLEAR_SEAM")
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
            sub = row.row()
            sub.active = (mode == 'EDIT')
            sub.operator("mesh.faces_mirror_uv", text="", icon ="COPYMIRRORED")
            #row.operator("uv.minimize_stretch") # doesn't work in toolbar editor, needs to be performed in image editor where the uv mesh is.


######################################## Tools ##############################################


class TOOLBAR_PT_menu_tools(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Toolbars Tools"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.label(text = "Toolbars Tools:")

        col = layout.column(align = True)
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "tools_parent")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "tools_objectdata")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "tools_link_to_scn")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "tools_linked_objects")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "tools_join")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "tools_origin")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "tools_shading")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "tools_datatransfer")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "tools_relations")


############### bfa - menu hidable by the flag in the right click menu


class TOOLBAR_PT_normals_autosmooth(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Auto Smooth"

    @classmethod
    def poll(cls, context):
        if context.active_object is None:
            return False

        if context.active_object.type != "MESH":
            return False

        return True

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        if context.active_object is None:
            return

        if context.active_object.type != "MESH":
            return

        mesh = context.active_object.data

        split = layout.split()
        split.active = not mesh.has_custom_normals
        split.use_property_split = False
        col = split.column()
        col.prop(mesh, "use_auto_smooth", text="Auto Smooth")
        col = split.column()
        row = col.row(align = True)
        row.prop(mesh, "auto_smooth_angle", text="")
        row.prop_decorator(mesh, "auto_smooth_angle")

        col = layout.column()
        if mesh.has_custom_normals:
            col.label(text = "No Autosmooth. Custom normals", icon = 'INFO')

        col = layout.column()

        if mesh.has_custom_normals:
            col.operator("mesh.customdata_custom_splitnormals_clear", icon='X')
        else:
            col.operator("mesh.customdata_custom_splitnormals_add", icon='ADD')


class TOOLBAR_MT_tools(Menu):
    bl_idname = "TOOLBAR_MT_tools"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        layout.popover(panel="TOOLBAR_PT_menu_tools", text = "")

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
                    row.operator("object.make_override_library", text="", icon = "LIBRARY_DATA_OVERRIDE")

                if addon_prefs.tools_join:

                    obj_type = obj.type

                    row = layout.row(align=True)
                    if obj_type in {'MESH', 'CURVE', 'SURFACE', 'ARMATURE'}:
                        row.operator("object.join", icon ='JOIN', text= "" )

                if addon_prefs.tools_origin:

                    obj_type = obj.type

                    if obj_type in {'MESH', 'CURVE', 'SURFACE', 'ARMATURE', 'FONT', 'LATTICE'}:

                        row = layout.row(align=True)
                        row.operator("object.origin_set", icon ='GEOMETRY_TO_ORIGIN', text="").type='GEOMETRY_ORIGIN'
                        row.operator("object.origin_set", icon ='ORIGIN_TO_GEOMETRY', text="").type='ORIGIN_GEOMETRY'
                        row.operator("object.origin_set", icon ='ORIGIN_TO_CURSOR', text="").type='ORIGIN_CURSOR'
                        row.operator("object.origin_set", icon ='ORIGIN_TO_CENTEROFMASS', text="").type='ORIGIN_CENTER_OF_MASS'
                        row.operator("object.origin_set", icon ='ORIGIN_TO_VOLUME', text = "").type='ORIGIN_CENTER_OF_VOLUME'

                if addon_prefs.tools_shading:

                    obj_type = obj.type

                    if obj_type in {'MESH', 'CURVE', 'SURFACE'}:

                        row = layout.row(align=True)
                        row.operator("object.shade_smooth", icon ='SHADING_SMOOTH', text="")
                        row.operator("object.shade_flat", icon ='SHADING_FLAT', text="")
                        row.popover(panel="TOOLBAR_PT_normals_autosmooth", text="", icon="NORMAL_SMOOTH")

                if addon_prefs.tools_datatransfer:

                    obj_type = obj.type

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


class TOOLBAR_PT_menu_animation(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Toolbars Animation"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.label(text = "Toolbars Animation:")

        col = layout.column(align = True)
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "animation_keyframes")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "animation_play")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "animation_range")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "animation_keyframetype")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "animation_sync")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "animation_keyingset")


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

        layout.popover(panel="TOOLBAR_PT_menu_animation", text = "")

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
    """Applies the current location"""
    bl_idname = "view3d.tb_apply_location"
    bl_label = "Apply Location"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False, isolate_users=True)
        return {'FINISHED'}

class VIEW3D_MT_object_apply_rotate(bpy.types.Operator):
    """Applies the current rotation"""
    bl_idname = "view3d.tb_apply_rotate"
    bl_label = "Apply Rotation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False, isolate_users=True)
        return {'FINISHED'}

class VIEW3D_MT_object_apply_scale(bpy.types.Operator):
    """Applies the current scale"""
    bl_idname = "view3d.tb_apply_scale"
    bl_label = "Apply Scale"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True, isolate_users=True)
        return {'FINISHED'}

class VIEW3D_MT_object_apply_all(bpy.types.Operator):
    """Applies the current location, rotation and scale"""
    bl_idname = "view3d.tb_apply_all"
    bl_label = "Apply All"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True, isolate_users=True)
        return {'FINISHED'}

class VIEW3D_MT_object_apply_rotscale(bpy.types.Operator):
    """Applies the current rotation and scale"""
    bl_idname = "view3d.tb_apply_rotscale"
    bl_label = "Apply Rotation & Scale"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True, isolate_users=True)
        return {'FINISHED'}

### --- Panel

class TOOLBAR_PT_menu_edit(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Toolbars Edit"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.label(text = "Toolbars Edit:")

        col = layout.column(align = True)
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "edit_edit")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "edit_weightinedit")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "edit_objectapply")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "edit_objectapply2")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "edit_objectapplydeltas")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "edit_objectclear")

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

        layout.popover(panel="TOOLBAR_PT_menu_edit", text = "")

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

            if addon_prefs.edit_objectapply2:

                mode = obj.mode

                if mode == 'OBJECT':

                    row = layout.row(align=True)
                    row.operator("object.visual_transform_apply", text = "", text_ctxt=i18n_contexts.default, icon = "VISUALTRANSFORM")
                    row.operator("object.duplicates_make_real", text = "", icon = "MAKEDUPLIREAL")
                    row.operator("object.parent_inverse_apply", text="", icon = "APPLY_PARENT_INVERSE")

            if addon_prefs.edit_objectapplydeltas:

                if mode == 'OBJECT':

                    row = layout.row(align=True)

                    myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYMOVEDELTA")
                    myvar.mode = 'LOC'
                    myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

                    myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYROTATEDELTA")
                    myvar.mode = 'ROT'
                    myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

                    myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYSCALEDELTA")
                    myvar.mode = 'SCALE'
                    myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

                    myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYALLDELTA")
                    myvar.mode = 'ALL'
                    myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'




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


class TOOLBAR_PT_menu_misc(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Toolbars Misc"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.label(text = "Toolbars Misc:")

        col = layout.column(align = True)
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "misc_viewport")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "misc_undoredo")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "misc_undohistory")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "misc_repeat")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "misc_scene")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "misc_viewlayer")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "misc_last")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "misc_operatorsearch")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "misc_info")


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

        layout.popover(panel="TOOLBAR_PT_menu_misc", text = "")

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        ## ------------------ Misc sub toolbars

        if addon_prefs.misc_viewport:

            if obj is not None:
                row = layout.row(align=True)
                row.popover(panel="OBJECT_PT_display", text="", icon = "VIEW")

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

        if addon_prefs.misc_viewlayer:

            window = context.window
            screen = context.screen
            scene = window.scene

            row = layout.row(align=True)
            layout.template_search(window, "view_layer", scene, "view_layers", new="scene.view_layer_add", unlink="scene.view_layer_remove")

        if addon_prefs.misc_last:

            row = layout.row(align=True)
            row.operator("screen.redo_last", text="Last", icon = "LASTOPERATOR")

        if addon_prefs.misc_operatorsearch:

            row = layout.row(align=True)
            row.operator("wm.search_menu", text="", icon='SEARCH_MENU')
            row.operator("wm.search_operator", text="", icon='VIEWZOOM')

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
    TOOLBAR_PT_menu_file,
    TOOLBAR_PT_menu_misc,
    TOOLBAR_PT_menu_edit,
    TOOLBAR_PT_type,
    VIEW3D_MT_object_apply_location,
    VIEW3D_MT_object_apply_rotate,
    VIEW3D_MT_object_apply_scale,
    VIEW3D_MT_object_apply_all,
    VIEW3D_MT_object_apply_rotscale,
    TOOLBAR_PT_menu_animation,
    TOOLBAR_PT_normals_autosmooth,
    TOOLBAR_PT_menu_tools,
    TOOLBAR_PT_menu_image,
    TOOLBAR_PT_menu_primitives,
    TOOLBAR_PT_menu_meshedit,
    TOOLBAR_MT_image_uv_rotate_clockwise,
    TOOLBAR_MT_image_uv_rotate_counterclockwise,
    TOOLBAR_MT_image_uv_mirror_x,
    TOOLBAR_MT_image_uv_mirror_y,
)


# -------------------- Register -------------------------------------------------------------------

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
