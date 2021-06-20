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

"""User interface imports and preferences for the addon."""

# import addon_utils
# from time import sleep
import bpy


from bpy.app.handlers import persistent

# from bpy.utils import register_class, unregister_class
# from bpy.types import (
# Operator,
# Menu,
# UIList,
# Panel,
# Brush,
# Material,
# Light,
# World,
# ParticleSettings,
# FreestyleLineStyle,
# )

# from bl_operators.presets import AddPresetBase

from . import (
    render_gui,
    scenography_gui,
    object_gui,
    shading_gui,
    texturing_gui,
    shading_nodes,  # for POV specific nodes
    scripting_gui,
    update_files,
)


# ------------ POV-Centric WORKSPACE ------------ #
@persistent
def pov_centric_moray_like_workspace(dummy):
    """Set up a POV centric Workspace if addon was activated and saved as default renderer.

    This would bring a ’_RestrictData’ error because UI needs to be fully loaded before
    workspace changes so registering this function in bpy.app.handlers is needed.
    By default handlers are freed when loading new files, but here we want the handler
    to stay running across multiple files as part of this add-on. That is why the
    bpy.app.handlers.persistent decorator is used (@persistent) above.
    """
    # Scripting workspace may have been altered from factory though, so should
    # we put all within a Try... Except AttributeErrors ? Any better solution ?
    # Should it simply not run when opening existing file? be a preferences operator to create
    # Moray like workspace
    if 'Scripting' in bpy.data.workspaces:

        wsp = bpy.data.workspaces.get('Scripting')
        context = bpy.context
        if context.scene.render.engine == 'POVRAY_RENDER' and wsp is not None:
            bpy.ops.workspace.duplicate({'workspace': wsp})
            bpy.data.workspaces['Scripting.001'].name = 'POV'
            # Already done it would seem, but explicitly make this workspace the active one
            context.window.workspace = bpy.data.workspaces['POV']
            pov_screen = bpy.data.workspaces['POV'].screens[0]
            pov_workspace = pov_screen.areas
            pov_window = context.window
            try:
                # Already outliners but invert both types
                pov_workspace[1].spaces[0].display_mode = 'LIBRARIES'
                pov_workspace[3].spaces[0].display_mode = 'VIEW_LAYER'
            except AttributeError:
                # But not necessarily outliners in existing blend files
                pass
            override = bpy.context.copy()

            for area in pov_workspace:
                if area.type == 'VIEW_3D':
                    for region in [r for r in area.regions if r.type == 'WINDOW']:
                        for space in area.spaces:
                            if space.type == 'VIEW_3D':
                                # override['screen'] = pov_screen
                                override['area'] = area
                                override['region'] = region
                                # bpy.data.workspaces['POV'].screens[0].areas[6].spaces[0].width = 333 # Read only,
                                # how do we set ?
                                # This has a glitch:
                                # bpy.ops.screen.area_move(override, x=(area.x + area.width), y=(area.y + 5), delta=100)
                                # bpy.ops.screen.area_move(override, x=(area.x + 5), y=area.y, delta=-100)

                                bpy.ops.screen.space_type_set_or_cycle(
                                    override, space_type='TEXT_EDITOR'
                                )
                                space.show_region_ui = True
                                # bpy.ops.screen.region_scale(override)
                                # bpy.ops.screen.region_scale()
                                break

                elif area.type == 'CONSOLE':
                    for region in [r for r in area.regions if r.type == 'WINDOW']:
                        for space in area.spaces:
                            if space.type == 'CONSOLE':
                                override['screen'] = pov_screen
                                override['window'] = pov_window
                                override['area'] = area
                                override['region'] = region

                                # area_x = area.x + (area.width / 2)
                                # area_y = area.y + area.height
                                bpy.ops.screen.space_type_set_or_cycle(override, space_type='INFO')
                                try:
                                    if area == pov_workspace[6] and bpy.ops.screen.area_move.poll(
                                        override
                                    ):
                                        # bpy.ops.screen.area_move(override, x = area_x, y = area_y, delta = -300)
                                        pass
                                        # pov_window.cursor_warp(area_x, area_y-300) # Is manual move emulation necessary
                                        # despite the delta?
                                except IndexError:
                                    # Not necessarily so many areas in existing blend files
                                    pass

                                break

                elif area.type == 'INFO':
                    for region in [r for r in area.regions if r.type == 'WINDOW']:
                        for space in area.spaces:
                            if space.type == 'INFO':
                                # override['screen'] = pov_screen
                                override['area'] = area
                                override['region'] = region
                                bpy.ops.screen.space_type_set_or_cycle(
                                    override, space_type='CONSOLE'
                                )

                                break

                elif area.type == 'TEXT_EDITOR':
                    for region in [r for r in area.regions if r.type == 'WINDOW']:
                        for space in area.spaces:
                            if space.type == 'TEXT_EDITOR':
                                # override['screen'] = pov_screen
                                override['area'] = area
                                override['region'] = region
                                # bpy.ops.screen.space_type_set_or_cycle(space_type='VIEW_3D')
                                # space.type = 'VIEW_3D'
                                bpy.ops.screen.space_type_set_or_cycle(
                                    override, space_type='VIEW_3D'
                                )

                                # bpy.ops.screen.area_join(override, cursor=(area.x, area.y + area.height))

                                break

                if area.type == 'VIEW_3D':
                    for region in [r for r in area.regions if r.type == 'WINDOW']:
                        for space in area.spaces:
                            if space.type == 'VIEW_3D':
                                # override['screen'] = pov_screen
                                override['area'] = area
                                override['region'] = region
                                bpy.ops.screen.region_quadview(override)
                                space.region_3d.view_perspective = 'CAMERA'
                                # bpy.ops.screen.space_type_set_or_cycle(override, space_type = 'TEXT_EDITOR')
                                # bpy.ops.screen.region_quadview(override)

                elif area.type == 'OUTLINER':
                    for region in [
                        r for r in area.regions if r.type == 'HEADER' and (r.y - area.y)
                    ]:
                        for space in area.spaces:
                            if space.display_mode == 'LIBRARIES':
                                override['area'] = area
                                override['region'] = region
                                override['window'] = pov_window
                                bpy.ops.screen.region_flip(override)

            bpy.data.workspaces.update()

            '''
            for window in bpy.context.window_manager.windows:
                for area in [a for a in window.screen.areas if a.type == 'VIEW_3D']:
                    for region in [r for r in area.regions if r.type == 'WINDOW']:
                        context_override = {
                            'window': window,
                            'screen': window.screen,
                            'area': area,
                            'region': region,
                            'space_data': area.spaces.active,
                            'scene': bpy.context.scene
                            }
                        bpy.ops.view3d.camera_to_view(context_override)
            '''

        else:
            print(
                "\nPOV centric workspace available if you set render option\n"
                "and save it in default file with CTRL+U"
            )

    else:
        print(
            "\nThe factory 'Scripting' workspace is needed before POV centric "
            "\nworkspace may activate when POV is set as your default renderer"
        )
    # -----------------------------------UTF-8---------------------------------- #
    # Check and fix all strings in current .blend file to be valid UTF-8 Unicode
    # sometimes needed for old, 2.4x / 2.6x area files
    bpy.ops.wm.blend_strings_utf8_validate()


def check_material(mat):
    """Allow use of material properties buttons rather than nodes."""
    if mat is not None:
        if mat.use_nodes:
            if not mat.node_tree:  # FORMERLY : #mat.active_node_material is not None:
                return True
            return False
        return True
    return False


def simple_material(mat):
    """Test if a material is nodeless."""
    return (mat is not None) and (not mat.use_nodes)


def pov_context_tex_datablock(context):
    """Recreate texture context type as deprecated in blender 2.8."""
    idblock = context.brush
    if idblock and context.scene.texture_context == 'OTHER':
        return idblock

    # idblock = bpy.context.active_object.active_material
    idblock = context.view_layer.objects.active.active_material
    if idblock and context.scene.texture_context == 'MATERIAL':
        return idblock

    idblock = context.scene.world
    if idblock and context.scene.texture_context == 'WORLD':
        return idblock

    idblock = context.light
    if idblock and context.scene.texture_context == 'LIGHT':
        return idblock

    if context.particle_system and context.scene.texture_context == 'PARTICLES':
        idblock = context.particle_system.settings

    return idblock

    idblock = context.line_style
    if idblock and context.scene.texture_context == 'LINESTYLE':
        return idblock


# class TextureTypePanel(TextureButtonsPanel):

# @classmethod
# def poll(cls, context):
# tex = context.texture
# engine = context.scene.render.engine
# return tex and ((tex.type == cls.tex_type and not tex.use_nodes) and (engine in cls.COMPAT_ENGINES))


def register():
    update_files.register()
    render_gui.register()
    scenography_gui.register()
    object_gui.register()
    shading_gui.register()
    texturing_gui.register()
    shading_nodes.register()
    scripting_gui.register()

    if pov_centric_moray_like_workspace not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(pov_centric_moray_like_workspace)


def unregister():
    if pov_centric_moray_like_workspace in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(pov_centric_moray_like_workspace)

    scripting_gui.unregister()
    shading_nodes.unregister()
    texturing_gui.unregister()
    shading_gui.unregister()
    object_gui.unregister()
    scenography_gui.unregister()
    render_gui.unregister()
    update_files.unregister()
