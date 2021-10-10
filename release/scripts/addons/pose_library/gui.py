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

"""
Pose Library - GUI definition.
"""

import bpy
from bpy.types import (
    AssetHandle,
    Context,
    Panel,
    UIList,
    WindowManager,
    WorkSpace,
)

from bpy_extras import asset_utils


class PoseLibraryPanel:
    @classmethod
    def pose_library_panel_poll(cls, context: Context) -> bool:
        return bool(
            context.object
            and context.object.mode == 'POSE'
        )

    @classmethod
    def poll(cls, context: Context) -> bool:
        return cls.pose_library_panel_poll(context);


class VIEW3D_PT_pose_library(PoseLibraryPanel, Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animation"
    bl_label = "Pose Library"

    def draw(self, context: Context) -> None:
        layout = self.layout

        row = layout.row(align=True)
        row.operator("poselib.create_pose_asset").activate_new_action = False
        if bpy.types.POSELIB_OT_restore_previous_action.poll(context):
            row.operator("poselib.restore_previous_action", text="", icon='LOOP_BACK')
        row.operator("poselib.copy_as_asset", icon="COPYDOWN", text="")

        wm = context.window_manager
        layout.prop(wm, "poselib_flipped")

        if hasattr(layout, "template_asset_view"):
            workspace = context.workspace
            activate_op_props, drag_op_props = layout.template_asset_view(
                "pose_assets",
                workspace,
                "asset_library_ref",
                wm,
                "pose_assets",
                workspace,
                "active_pose_asset_index",
                filter_id_types={"filter_action"},
                activate_operator="poselib.apply_pose_asset",
                drag_operator="poselib.blend_pose_asset",
            )
            drag_op_props.release_confirm = True
            drag_op_props.flipped = wm.poselib_flipped
            activate_op_props.flipped = wm.poselib_flipped


def pose_library_list_item_context_menu(self: UIList, context: Context) -> None:
    def is_pose_asset_view() -> bool:
        # Important: Must check context first, or the menu is added for every kind of list.
        list = getattr(context, "ui_list", None)
        if not list or list.bl_idname != "UI_UL_asset_view" or list.list_id != "pose_assets":
            return False
        if not context.asset_handle:
            return False
        return True

    def is_pose_library_asset_browser() -> bool:
        asset_library_ref = getattr(context, "asset_library_ref", None)
        if not asset_library_ref:
            return False
        asset = getattr(context, "asset_file_handle", None)
        if not asset:
            return False
        return bool(asset.id_type == 'ACTION')

    if not is_pose_asset_view() and not is_pose_library_asset_browser():
        return

    layout = self.layout
    wm = context.window_manager

    layout.separator()

    layout.operator("poselib.apply_pose_asset", text="Apply Pose")

    old_op_ctx = layout.operator_context
    layout.operator_context = 'INVOKE_DEFAULT'
    props = layout.operator("poselib.blend_pose_asset", text="Blend Pose")
    props.flipped = wm.poselib_flipped
    layout.operator_context = old_op_ctx

    props = layout.operator("poselib.pose_asset_select_bones", text="Select Pose Bones")
    props.select = True
    props = layout.operator("poselib.pose_asset_select_bones", text="Deselect Pose Bones")
    props.select = False

    layout.separator()
    if is_pose_asset_view():
        layout.operator("asset.open_containing_blend_file")


class ASSETBROWSER_PT_pose_library_usage(PoseLibraryPanel, asset_utils.AssetBrowserPanel, Panel):
    bl_region_type = "TOOLS"
    bl_label = "Pose Library"
    asset_categories = {'ANIMATIONS'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return (
            cls.pose_library_panel_poll(context)
            and cls.asset_browser_panel_poll(context)
        )

    def draw(self, context: Context) -> None:
        layout = self.layout
        wm = context.window_manager

        col = layout.column(align=True)
        col.prop(wm, "poselib_flipped")
        props = col.operator("poselib.apply_pose_asset")
        props.flipped = wm.poselib_flipped
        props = col.operator("poselib.blend_pose_asset")
        props.flipped = wm.poselib_flipped

        row = col.row(align=True)
        props = row.operator("poselib.pose_asset_select_bones", text="Select", icon="BONE_DATA")
        props.flipped = wm.poselib_flipped
        props.select = True
        props = row.operator("poselib.pose_asset_select_bones", text="Deselect")
        props.flipped = wm.poselib_flipped
        props.select = False


class ASSETBROWSER_PT_pose_library_editing(PoseLibraryPanel, asset_utils.AssetBrowserPanel, Panel):
    bl_region_type = "TOOL_PROPS"
    bl_label = "Pose Library"
    asset_categories = {'ANIMATIONS'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return (
            cls.pose_library_panel_poll(context)
            and cls.asset_browser_panel_poll(context)
        )

    def draw(self, context: Context) -> None:
        layout = self.layout

        col = layout.column(align=True)
        col.enabled = bpy.types.ASSET_OT_assign_action.poll(context)
        col.label(text="Activate & Edit")
        col.operator("asset.assign_action")

        # Creation
        col = layout.column(align=True)
        col.enabled = bpy.types.POSELIB_OT_paste_asset.poll(context)
        col.label(text="Create Pose Asset")
        col.operator("poselib.paste_asset", icon="PASTEDOWN")


class DOPESHEET_PT_asset_panel(PoseLibraryPanel, Panel):
    bl_space_type = "DOPESHEET_EDITOR"
    bl_region_type = "UI"
    bl_label = "Create Pose Asset"
    bl_category = "Pose Library"

    def draw(self, context: Context) -> None:
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("poselib.create_pose_asset").activate_new_action = True
        if bpy.types.POSELIB_OT_restore_previous_action.poll(context):
            row.operator("poselib.restore_previous_action", text="", icon='LOOP_BACK')
        col.operator("poselib.copy_as_asset", icon="COPYDOWN")

        layout.operator("poselib.convert_old_poselib")


### Messagebus subscription to monitor asset library changes.
_msgbus_owner = object()

def _on_asset_library_changed() -> None:
    """Update areas when a different asset library is selected."""
    refresh_area_types = {'DOPESHEET_EDITOR', 'VIEW_3D'}
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type not in refresh_area_types:
                continue

            area.tag_redraw()

def register_message_bus() -> None:
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.FileAssetSelectParams, "asset_library_ref"),
        owner=_msgbus_owner,
        args=(),
        notify=_on_asset_library_changed,
        options={'PERSISTENT'},
    )

def unregister_message_bus() -> None:
    bpy.msgbus.clear_by_owner(_msgbus_owner)

@bpy.app.handlers.persistent
def _on_blendfile_load_pre(none, other_none) -> None:
    # The parameters are required, but both are None.
    unregister_message_bus()

@bpy.app.handlers.persistent
def _on_blendfile_load_post(none, other_none) -> None:
    # The parameters are required, but both are None.
    register_message_bus()


classes = (
    ASSETBROWSER_PT_pose_library_editing,
    ASSETBROWSER_PT_pose_library_usage,
    DOPESHEET_PT_asset_panel,
    VIEW3D_PT_pose_library,
)

_register, _unregister = bpy.utils.register_classes_factory(classes)


def register() -> None:
    _register()

    WorkSpace.active_pose_asset_index = bpy.props.IntProperty(
        name="Active Pose Asset",
        # TODO explain which list the index belongs to, or how it can be used to get the pose.
        description="Per workspace index of the active pose asset"
    )
    # Register for window-manager. This is a global property that shouldn't be
    # written to files.
    WindowManager.pose_assets = bpy.props.CollectionProperty(type=AssetHandle)

    bpy.types.UI_MT_list_item_context_menu.prepend(pose_library_list_item_context_menu)
    bpy.types.ASSETBROWSER_MT_context_menu.prepend(pose_library_list_item_context_menu)

    register_message_bus()
    bpy.app.handlers.load_pre.append(_on_blendfile_load_pre)
    bpy.app.handlers.load_post.append(_on_blendfile_load_post)


def unregister() -> None:
    _unregister()

    unregister_message_bus()

    del WorkSpace.active_pose_asset_index
    del WindowManager.pose_assets

    bpy.types.UI_MT_list_item_context_menu.remove(pose_library_list_item_context_menu)
    bpy.types.ASSETBROWSER_MT_context_menu.remove(pose_library_list_item_context_menu)

