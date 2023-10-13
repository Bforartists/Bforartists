# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy

from spa_sequencer.shared_folders.core import (
    get_active_shared_folder,
    get_scene_users,
    get_shared_folders_root_collection,
)
from spa_sequencer.utils import register_classes, unregister_classes


class COLLECTION_UL_shared_folders(bpy.types.UIList):
    """Display shared folder items."""

    bl_idname = "COLLECTION_UL_shared_folders"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname
    ):
        users = get_scene_users(item)
        row = layout.row()
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row.prop(item, "name", icon_value=icon, text="", emboss=False)
            row.alignment = "EXPAND"
            row = layout.row()
            row.alignment = "RIGHT"
            # Shot context: expose link/unlink operators
            if context.area.type == "VIEW_3D":
                # Unlinked
                if context.scene not in users:
                    kwargs = {
                        "operator": "collection.shared_folder_shots_link",
                        "icon": "UNLINKED",
                    }
                # Linked
                else:
                    kwargs = {
                        "operator": "collection.shared_folder_shots_unlink",
                        "icon": "LINKED",
                        "depress": True,
                    }

                props = row.operator(**kwargs, text="", emboss=False)
                props.shared_folder_name = item.name
            # Sequence editor context
            else:
                # Display the number of users
                row.label(text=f"{len(users)} ")
        elif self.layout_type in {"GRID"}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)


class BASE_PT_SharedFoldersPanel(bpy.types.Panel):
    bl_label = "Shared Folders"
    bl_category = "Sequencer"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        root_col = get_shared_folders_root_collection()
        if not root_col or len(root_col.children) == 0:
            self.layout.operator("collection.shared_folder_new", icon="ADD")
            return

        if context.window_manager.active_shared_folder_index >= len(root_col.children):
            context.window_manager.active_shared_folder_index = (
                len(root_col.children) - 1
            )

        shared_folder = get_active_shared_folder(context)

        row = self.layout.row()
        col = row.column()

        col.template_list(
            COLLECTION_UL_shared_folders.bl_idname,
            "",
            root_col,
            "children",
            context.window_manager,
            "active_shared_folder_index",
            type="DEFAULT",
            rows=3,
        )

        col = row.column(align=True)

        props = col.operator("collection.shared_folder_new", icon="ADD", text="")

        props = col.operator("collection.shared_folder_delete", icon="REMOVE", text="")
        props.shared_folder_name = shared_folder.name

        if context.area.type == "VIEW_3D":
            return

        col.separator()

        props = col.operator(
            "collection.shared_folder_shots_select", icon="RESTRICT_SELECT_OFF", text=""
        )
        props.shared_folder_name = shared_folder.name

        col.separator()

        props = col.operator(
            "collection.shared_folder_shots_link", icon="LINKED", text=""
        )
        props.shared_folder_name = shared_folder.name

        props = col.operator(
            "collection.shared_folder_shots_unlink", icon="UNLINKED", text=""
        )
        props.shared_folder_name = shared_folder.name


class VIEW3D_PT_SharedFoldersPanel(BASE_PT_SharedFoldersPanel):
    """
    Panel that displays and gives control over the list of shared folders within the
    active shot.
    """

    bl_space_type = "VIEW_3D"


class SEQUENCER_PT_SharedFoldersPanel(BASE_PT_SharedFoldersPanel):
    """
    Panel that displays and gives control over the list of shared folders within the
    sequence editor.
    """

    bl_space_type = "SEQUENCE_EDITOR"


def draw_shared_folder_menu(self, context: bpy.types.Context):
    """Shared folder entries in outliner context menu for collections."""
    self.layout.separator()
    self.layout.operator(
        "collection.shared_folder_from_collection", icon="OUTLINER_COLLECTION"
    )


classes = (
    COLLECTION_UL_shared_folders,
    SEQUENCER_PT_SharedFoldersPanel,
    VIEW3D_PT_SharedFoldersPanel,
)


def register():
    register_classes(classes)

    bpy.types.OUTLINER_MT_collection.append(draw_shared_folder_menu)


def unregister():
    unregister_classes(classes)
    bpy.types.OUTLINER_MT_collection.remove(draw_shared_folder_menu)
