# SPDX-FileCopyrightText: 2020-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import bpy
from bpy.types import Operator
from bpy.app.translations import (
    pgettext_data as data_,
    pgettext_rpt as rpt_,
)


from bpy_extras.asset_utils import (
    SpaceAssetInfo,
)


class AssetBrowserMetadataOperator:
    @classmethod
    def poll(cls, context):
        if not SpaceAssetInfo.is_asset_browser_poll(context) or not context.asset:
            return False

        if not context.asset.local_id:
            Operator.poll_message_set(
                "Asset metadata from external asset libraries cannot be "
                "edited, only assets stored in the current file can"
            )
            return False
        return True


class ASSET_OT_tag_add(AssetBrowserMetadataOperator, Operator):
    """Add a new keyword tag to the active asset"""

    bl_idname = "asset.tag_add"
    bl_label = "Add Asset Tag"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_asset = context.asset
        active_asset.metadata.tags.new(data_("Tag"))

        return {'FINISHED'}


class ASSET_OT_tag_remove(AssetBrowserMetadataOperator, Operator):
    """Remove an existing keyword tag from the active asset"""

    bl_idname = "asset.tag_remove"
    bl_label = "Remove Asset Tag"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False

        active_asset = context.asset
        asset_metadata = active_asset.metadata
        return asset_metadata.active_tag in range(len(asset_metadata.tags))

    def execute(self, context):
        active_asset = context.asset
        asset_metadata = active_asset.metadata
        tag = asset_metadata.tags[asset_metadata.active_tag]

        asset_metadata.tags.remove(tag)
        asset_metadata.active_tag -= 1

        return {'FINISHED'}

# BFA - Custom tags assignment for the shelves
class ASSET_OT_tag_add_shelf(AssetBrowserMetadataOperator, Operator):
    """Adds pre-defined tags to assign a Node Group to an Asset Shelf"""
    bl_idname = "asset.tag_add_shelf"
    bl_label = "Assign Node Group to Asset Shelf"
    bl_options = {'REGISTER', 'UNDO'}

    tag_type: bpy.props.EnumProperty(
        name="Tag Type",
        description="Type of tag to add",
        items=[
            ('GEOMETRY_NODES', "Geometry Nodes", "Add Geometry Nodes tag"),
            ('3D_VIEW', "3D View", "Add 3D View tag"),
            ('SHADER', "Shader", "Add Shader tag"),
            ('COMPOSITOR', "Compositor", "Add Compositor tag"),
        ],
        default='GEOMETRY_NODES'
    )

    def execute(self, context):
        active_asset = context.asset
        tag_map = {
            'GEOMETRY_NODES': "Geometry Nodes",
            '3D_VIEW': "3D View",
            'SHADER': "Shader",
            'COMPOSITOR': "Compositor"
        }

        tag_name = tag_map[self.tag_type]
        # Remove other shelf tags if they exist, except when adding 3D_VIEW and GEOMETRY_NODES exists
        for existing_tag in active_asset.metadata.tags:
            if existing_tag.name in tag_map.values() and existing_tag.name != tag_name:
                # Keep GEOMETRY_NODES tag when adding 3D_VIEW
                if not (self.tag_type == '3D_VIEW' and existing_tag.name == "Geometry Nodes"):
                    active_asset.metadata.tags.remove(existing_tag)

        # Add new tag if it doesn't exist
        if tag_name not in active_asset.metadata.tags:
            active_asset.metadata.tags.new(tag_name)

        return {'FINISHED'}



class ASSET_OT_open_containing_blend_file(Operator):
    """Open the blend file that contains the active asset"""

    bl_idname = "asset.open_containing_blend_file"
    bl_label = "Open Blend File"
    bl_options = {'REGISTER'}

    _process = None  # Optional[subprocess.Popen]

    @classmethod
    def poll(cls, context):
        asset = getattr(context, "asset", None)

        if not asset:
            cls.poll_message_set("No asset selected")
            return False
        if asset.local_id:
            cls.poll_message_set("Selected asset is contained in the current file")
            return False
        if asset.is_online:
            cls.poll_message_set("Selected asset is stored online")
            return False
        if not asset.owner_asset_library.is_editable:
            cls.poll_message_set(
                "The asset library this asset belongs to is not editable"
            )
            return False
        # This could become a built-in query, for now this is good enough.
        if asset.full_library_path.endswith(".asset.blend"):
            cls.poll_message_set(
                "Selected asset is contained in a file managed by the asset system, manual edits should be avoided",
            )
            return False
        return True

    def execute(self, context):
        asset = context.asset

        if asset.local_id:
            self.report({'WARNING'}, "This asset is stored in the current blend file")
            return {'CANCELLED'}

        asset_lib_path = asset.full_library_path
        self.open_in_new_blender(asset_lib_path)

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        if self._process is None:
            self.report({'ERROR'}, "Unable to find any running process")
            self.cancel(context)
            return {'CANCELLED'}

        returncode = self._process.poll()
        if returncode is None:
            # Process is still running.
            return {'RUNNING_MODAL'}

        if returncode:
            self.report({'WARNING'}, rpt_("Blender sub-process exited with error code {:d}").format(returncode))

        if bpy.ops.asset.library_refresh.poll():
            bpy.ops.asset.library_refresh()

        self.cancel(context)
        return {'FINISHED'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

    def open_in_new_blender(self, filepath):
        import subprocess

        cli_args = [bpy.app.binary_path, str(filepath)]
        self._process = subprocess.Popen(cli_args)


class ASSET_OT_browse_containing_blend_file(Operator):
    """Open the system's file browser with the blend file that contains the active asset"""

    bl_idname = "asset.browse_containing_blend_file"
    bl_label = "Open File Location"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        asset = getattr(context, "asset", None)

        if not asset:
            cls.poll_message_set("No asset selected")
            return False
        if asset.local_id and not bpy.data.filepath:
            cls.poll_message_set("Asset local to the current file, which is not saved anywhere")
            return False
        if asset.is_online:
            cls.poll_message_set("Selected asset is stored online")
            return False
        return True

    def execute(self, context):
        from pathlib import Path

        asset = context.asset

        if asset.local_id:
            asset_path = Path(bpy.data.filepath)
        else:
            asset_path = Path(asset.full_library_path)
        return bpy.ops.wm.path_open(filepath=str(asset_path.parent))


# BFA - Clear the entire local remote assets cache directory.
# This covers online essentials AND all third-party remote asset libraries.
# All cached listings, previews, and thumbnails are deleted, forcing a fresh
# download on the next library refresh. Useful when the cache becomes stale
# or corrupted.
class ASSET_OT_clear_remote_assets_cache(Operator):
    """Deletes the entire remote assets cache (Online Essentials + all third-party libraries), forcing fresh downloads of files and thumbnails"""

    bl_idname = "asset.clear_remote_assets_cache"
    bl_label = "Clear Remote Assets Cache"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        prefs = context.preferences
        if not prefs.experimental.use_remote_asset_libraries:
            cls.poll_message_set("Remote asset libraries are not enabled")
            return False
        # User needs at least one remote source enabled.
        has_remote = (
            prefs.asset_libraries.use_online_essentials or
            any(lib.enabled and lib.use_remote_url for lib in prefs.filepaths.asset_libraries)
        )
        if not has_remote:
            cls.poll_message_set("No remote asset libraries or online essentials enabled")
            return False
        return True

    def execute(self, context):
        import shutil
        from pathlib import Path

        # The online-essentials cache lives under {cache}/remote-assets/online-essentials/.
        # All third-party remote libraries also cache under {cache}/remote-assets/{md5_hash}/.
        # So removing the parent directory clears everything globally.
        cache_root = Path(bpy.types.AssetLibrary.online_assets_cache_path()).parent

        if not cache_root.exists():
            self.report({'INFO'}, "Remote assets cache is already empty")
            return {'FINISHED'}

        shutil.rmtree(str(cache_root))
        self.report({'INFO'}, "Remote assets cache cleared")

        # Auto-refresh remote asset listings so the user doesn't have to do it manually.
        if bpy.ops.asset.library_reload_listing.poll():
            bpy.ops.asset.library_reload_listing()

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=360)

    def draw(self, context):
        layout = self.layout
        layout.label(
            text="Warning: This will permanently delete all locally cached files",
            icon='ERROR',
        )
        layout.label(
            text="for every remote asset library, including thumbnails and files.",
        )



# BFA - Open the remote assets cache folder in the system file browser.
# Shows the directory containing cached data for online essentials and all
# third-party remote asset libraries. Useful for inspection and troubleshooting.
class ASSET_OT_open_remote_assets_cache(Operator):
    """Open the system file browser at the remote assets cache directory (Online Essentials + all third-party libraries)"""

    bl_idname = "asset.open_remote_assets_cache"
    bl_label = "Open Remote Assets Cache"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        prefs = context.preferences
        if not prefs.experimental.use_remote_asset_libraries:
            cls.poll_message_set("Remote asset libraries are not enabled")
            return False
        # User needs at least one remote source enabled.
        has_remote = (
            prefs.asset_libraries.use_online_essentials or
            any(lib.enabled and lib.use_remote_url for lib in prefs.filepaths.asset_libraries)
        )
        if not has_remote:
            cls.poll_message_set("No remote asset libraries or online essentials enabled")
            return False
        return True

    def execute(self, context):
        from pathlib import Path

        cache_root = Path(bpy.types.AssetLibrary.online_assets_cache_path()).parent
        # Ensure the directory exists before trying to open it.
        cache_root.mkdir(parents=True, exist_ok=True)
        return bpy.ops.wm.path_open(filepath=str(cache_root))


classes = (
    ASSET_OT_tag_add,
    ASSET_OT_tag_remove,
    ASSET_OT_tag_add_shelf, # BFA
    ASSET_OT_open_containing_blend_file,
    ASSET_OT_browse_containing_blend_file,
    # BFA - operators for managing the remote assets cache (covers online essentials + all third-party remote libraries)
    ASSET_OT_clear_remote_assets_cache,
    ASSET_OT_open_remote_assets_cache,
)
