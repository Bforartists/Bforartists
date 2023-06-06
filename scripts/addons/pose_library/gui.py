# SPDX-License-Identifier: GPL-2.0-or-later

"""
Pose Library - GUI definition.
"""

import bpy
from bpy.types import (
    AssetHandle,
    Context,
    Menu,
    Panel,
    UIList,
    WindowManager,
    WorkSpace,
)


class PoseLibraryPanel:
    @classmethod
    def pose_library_panel_poll(cls, context: Context) -> bool:
        return bool(context.object and context.object.mode == 'POSE')

    @classmethod
    def poll(cls, context: Context) -> bool:
        return cls.pose_library_panel_poll(context)


class VIEW3D_PT_pose_library(PoseLibraryPanel, Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animation"
    bl_label = "Pose Library"

    def draw(self, context: Context) -> None:
        layout = self.layout

        if hasattr(layout, "template_asset_view"):
            workspace = context.workspace
            wm = context.window_manager
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

            # Make sure operators properties match those used in
            # `pose_library_list_item_context_menu` so shortcuts show in menus (see T103267).
            activate_op_props.flipped = False


def pose_library_list_item_context_menu(self: UIList, context: Context) -> None:
    def is_pose_asset_view() -> bool:
        # Important: Must check context first, or the menu is added for every kind of list.
        list = getattr(context, "ui_list", None)
        if not list or list.bl_idname != "UI_UL_asset_view" or list.list_id != "pose_assets":
            return False
        if not context.active_file:
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

    layout.separator()

    # Make sure these operator properties match those used in `VIEW3D_PT_pose_library`.
    layout.operator("poselib.apply_pose_asset", text="Apply Pose").flipped = False
    layout.operator("poselib.apply_pose_asset", text="Apply Pose Flipped").flipped = True

    old_op_ctx = layout.operator_context
    layout.operator_context = 'INVOKE_DEFAULT'
    props = layout.operator("poselib.blend_pose_asset", text="Blend Pose")
    layout.operator_context = old_op_ctx

    layout.separator()
    props = layout.operator("poselib.pose_asset_select_bones", text="Select Pose Bones")
    props.select = True
    props = layout.operator("poselib.pose_asset_select_bones", text="Deselect Pose Bones")
    props.select = False

    if not is_pose_asset_view():
        layout.separator()
        layout.operator("asset.assign_action")

    layout.separator()
    if is_pose_asset_view():
        layout.operator("asset.open_containing_blend_file")

        props.select = False


class DOPESHEET_PT_asset_panel(PoseLibraryPanel, Panel):
    bl_space_type = "DOPESHEET_EDITOR"
    bl_region_type = "UI"
    bl_label = "Create Pose Asset"
    bl_category = "Action"

    def draw(self, context: Context) -> None:
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("poselib.create_pose_asset").activate_new_action = True
        if bpy.types.POSELIB_OT_restore_previous_action.poll(context):
            row.operator("poselib.restore_previous_action", text="", icon='LOOP_BACK')
        col.operator("poselib.copy_as_asset", icon="COPYDOWN")

        layout.operator("poselib.convert_old_poselib")


def pose_library_list_item_asset_menu(self: UIList, context: Context) -> None:
    layout = self.layout
    layout.menu("ASSETBROWSER_MT_asset")


class ASSETBROWSER_MT_asset(Menu):
    bl_label = "Asset"

    @classmethod
    def poll(cls, context):
        from bpy_extras.asset_utils import SpaceAssetInfo

        return SpaceAssetInfo.is_asset_browser_poll(context)

    def draw(self, context: Context) -> None:
        layout = self.layout

        layout.operator("poselib.paste_asset", icon='PASTEDOWN')
        layout.separator()
        layout.operator("poselib.create_pose_asset").activate_new_action = False


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
    DOPESHEET_PT_asset_panel,
    VIEW3D_PT_pose_library,
    ASSETBROWSER_MT_asset,
)

_register, _unregister = bpy.utils.register_classes_factory(classes)


def register() -> None:
    _register()

    WorkSpace.active_pose_asset_index = bpy.props.IntProperty(
        name="Active Pose Asset",
        # TODO explain which list the index belongs to, or how it can be used to get the pose.
        description="Per workspace index of the active pose asset",
    )
    # Register for window-manager. This is a global property that shouldn't be
    # written to files.
    WindowManager.pose_assets = bpy.props.CollectionProperty(type=AssetHandle)

    bpy.types.UI_MT_list_item_context_menu.prepend(pose_library_list_item_context_menu)
    bpy.types.ASSETBROWSER_MT_context_menu.prepend(pose_library_list_item_context_menu)
    bpy.types.ASSETBROWSER_MT_editor_menus.append(pose_library_list_item_asset_menu)

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
    bpy.types.ASSETBROWSER_MT_editor_menus.remove(pose_library_list_item_asset_menu)
