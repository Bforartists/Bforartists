# SPDX-FileCopyrightText: 2022-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""User interface imports and preferences for the addon."""

# import addon_utils
# from time import sleep
import bpy
import os

from bpy.app.handlers import persistent
from pathlib import Path

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
    model_gui,
    shading_gui,
    texturing_gui,
    nodes,  # for POV specific nodes
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


    # -----------------------------------UTF-8---------------------------------- #
    # Check and fix all strings in current .blend file to be valid UTF-8 Unicode
    # sometimes needed for old, 2.4x / 2.6x area files
    try:
        bpy.ops.wm.blend_strings_utf8_validate()
    except BaseException as e:
        print(e.__doc__)
        print("An exception occurred: {}".format(e))
        pass
    # --------------------------------Workspaces------------------------------- #

    # If this file is not the default do nothing so as to not mess up project dependant workspaces
    if bpy.data.filepath:
        return

    available_workspaces = bpy.data.workspaces

    if all(tabs in available_workspaces for tabs in ["POV-Mo", "POV-Ed"]):
        print(
            "\nPOV-Mo and POV-Ed tabs respectively provide GUI and TEXT\n"
            "oriented POV workspaces akin to Moray and POVWIN"
        )
        return
    if "POV-Ed" not in available_workspaces:
        print(
            "\nTo use POV centric workspaces you can set POV render option\n"
            "and save it with File > Defaults > Save Startup File menu"
        )
        try:
            if all(
                othertabs not in available_workspaces
                for othertabs in ["Geometry Nodes", "POV-Ed"]
            ):
                bpy.ops.workspace.append_activate(
                    idname="Geometry Nodes",
                    filepath=os.path.join(bpy.utils.user_resource("CONFIG"), "startup.blend"),
                )
        except BaseException as e:
            print(e.__doc__)
            print("An exception occurred: {}".format(e))
            try:
                # Last resort: try to import from the blender templates
                for p in Path(next(bpy.utils.app_template_paths())).rglob("startup.blend"):
                    bpy.ops.workspace.append_activate(idname="Geometry Nodes", filepath=str(p))
            except BaseException as e:
                print(e.__doc__)
                print("An exception occurred: {}".format(e))
                # Giving up as prerequisites can't be found
                print(
                    "\nFactory Geometry Nodes workspace needed for POV text centric"
                    "\nworkspace to activate when POV is set as default renderer"
                )
        finally:
            # Create POVWIN like editor (text oriented editing)
            if (
                "POV-Ed" not in available_workspaces
                and "Geometry Nodes" in available_workspaces
            ):
                wsp = available_workspaces.get("Geometry Nodes")
                context = bpy.context
                if context.scene.render.engine == "POVRAY_RENDER" and wsp is not None:
                    context_override = {"workspace": wsp}
                    with context.temp_override(**context_override):
                        bpy.ops.workspace.duplicate()
                    del context_override
                    available_workspaces["Geometry Nodes.001"].name = "POV-Ed"
                    # May be already done, but explicitly make this workspace the active one
                    context.window.workspace = available_workspaces["POV-Ed"]
                    pov_screen = available_workspaces["POV-Ed"].screens[0]
                    pov_workspace = pov_screen.areas
                    pov_window = context.window
                    # override = bpy.context.copy()  # crashes
                    override = {}
                    properties_area = pov_workspace[0]
                    nodes_to_3dview_area = pov_workspace[1]
                    view3d_to_text_area = pov_workspace[2]
                    spreadsheet_to_console_area = pov_workspace[3]

                    try:
                        nodes_to_3dview_area.ui_type = "VIEW_3D"
                        override["window"] = pov_window
                        override["screen"] = bpy.context.screen
                        override["area"] = nodes_to_3dview_area
                        override["region"] = nodes_to_3dview_area.regions[-1]
                        bpy.ops.screen.space_type_set_or_cycle(
                            override, "INVOKE_DEFAULT", space_type="VIEW_3D"
                        )
                        space = nodes_to_3dview_area.spaces.active
                        space.region_3d.view_perspective = "CAMERA"

                        override["window"] = pov_window
                        override["screen"] = bpy.context.screen
                        override["area"] = view3d_to_text_area
                        override["region"] = view3d_to_text_area.regions[-1]
                        override["scene"] = bpy.context.scene
                        override["space_data"] = view3d_to_text_area.spaces.active
                        bpy.ops.screen.space_type_set_or_cycle(
                            override, "INVOKE_DEFAULT", space_type="TEXT_EDITOR"
                        )
                        view3d_to_text_area.spaces.active.show_region_ui = True

                        spreadsheet_to_console_area.ui_type = "CONSOLE"
                        override["window"] = pov_window
                        override["screen"] = bpy.context.screen
                        override["area"] = spreadsheet_to_console_area
                        override["region"] = spreadsheet_to_console_area.regions[-1]
                        bpy.ops.screen.space_type_set_or_cycle(
                            override, "INVOKE_DEFAULT", space_type="CONSOLE"
                        )
                        space = properties_area.spaces.active
                        space.context = "RENDER"
                        bpy.ops.workspace.reorder_to_front(
                            {"workspace": available_workspaces["POV-Ed"]}
                        )
                    except AttributeError:
                        # In case necessary area types lack in existing blend files
                        pass
    if "POV-Mo" not in available_workspaces:
        try:
            if all(tab not in available_workspaces for tab in ["Rendering", "POV-Mo"]):
                bpy.ops.workspace.append_activate(
                    idname="Rendering",
                    filepath=os.path.join(bpy.utils.user_resource("CONFIG"), "startup.blend"),
                )
        except BaseException as e:
            print(e.__doc__)
            print("An exception occurred: {}".format(e))
            try:
                # Last resort: try to import from the blender templates
                for p in Path(next(bpy.utils.app_template_paths())).rglob("startup.blend"):
                    bpy.ops.workspace.append_activate(idname="Rendering", filepath=str(p))
            except BaseException as e:
                print(e.__doc__)
                print("An exception occurred: {}".format(e))
                # Giving up
                print(
                    "\nFactory 'Rendering' workspace needed for POV GUI centric"
                    "\nworkspace to activate when POV is set as default renderer"
                )
        finally:
            # Create Moray like workspace (GUI oriented editing)
            if "POV-Mo" not in available_workspaces and "Rendering" in available_workspaces:
                wsp1 = available_workspaces.get("Rendering")
                context = bpy.context
                if context.scene.render.engine == "POVRAY_RENDER" and wsp1 is not None:
                    context_override = {"workspace": wsp1}
                    with context.temp_override(**context_override):
                        bpy.ops.workspace.duplicate()
                    del context_override
                    available_workspaces["Rendering.001"].name = "POV-Mo"
                    # Already done it would seem, but explicitly make this workspace the active one
                    context.window.workspace = available_workspaces["POV-Mo"]
                    pov_screen = available_workspaces["POV-Mo"].screens[0]
                    pov_workspace = pov_screen.areas
                    pov_window = context.window
                    # override = bpy.context.copy()  # crashes
                    override = {}
                    properties_area = pov_workspace[0]
                    image_editor_to_view3d_area = pov_workspace[2]

                    try:
                        image_editor_to_view3d_area.ui_type = "VIEW_3D"
                        override["window"] = pov_window
                        override["screen"] = bpy.context.screen
                        override["area"] = image_editor_to_view3d_area
                        override["region"] = image_editor_to_view3d_area.regions[-1]
                        bpy.ops.screen.space_type_set_or_cycle(
                            override, "INVOKE_DEFAULT", space_type="VIEW_3D"
                        )
                        space = (
                            image_editor_to_view3d_area.spaces.active
                        )  # Uncomment For non quad view
                        space.region_3d.view_perspective = (
                            "CAMERA"  # Uncomment For non quad view
                        )
                        space.show_region_toolbar = True
                        # bpy.ops.view3d.camera_to_view(override)  # Uncomment For non quad view ?
                        for num, reg in enumerate(image_editor_to_view3d_area.regions):
                            if reg.type != "view3d":
                                override["region"] = image_editor_to_view3d_area.regions[num]
                        bpy.ops.screen.region_quadview(override)  # Comment out for non quad
                        propspace = properties_area.spaces.active
                        propspace.context = "MATERIAL"
                        bpy.ops.workspace.reorder_to_front(
                            {"workspace": available_workspaces["POV-Mo"]}
                        )
                    except (AttributeError, TypeError):
                        # In case necessary types lack in existing blend files
                        pass
                    # available_workspaces.update()


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
    model_gui.register()
    shading_gui.register()
    texturing_gui.register()
    nodes.register()
    scripting_gui.register()

    if pov_centric_moray_like_workspace not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(pov_centric_moray_like_workspace)


def unregister():
    if pov_centric_moray_like_workspace in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(pov_centric_moray_like_workspace)

    scripting_gui.unregister()
    nodes.unregister()
    texturing_gui.unregister()
    shading_gui.unregister()
    model_gui.unregister()
    scenography_gui.unregister()
    render_gui.unregister()
    update_files.unregister()
