# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy, sys, json
from bpy.types import Menu, Operator
from bpy.props import StringProperty
from .op_pie_wrappers import WM_OT_call_menu_pie_drag_only


AVAILABLE_PROPERTIES_EDITORS = []


class PIE_MT_editor_switch(Menu):
    bl_idname = "PIE_MT_editor_switch"
    bl_label = "Editor Switch"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator(
            'wm.call_menu_pie', text="Video Editing...", icon="SEQUENCE"
        ).name = "PIE_MT_editor_switch_video"
        # 6 - RIGHT
        pie.operator('wm.call_menu_pie', text="Nodes...", icon="NODETREE").name = (
            "PIE_MT_editor_switch_nodes"
        )
        # 2 - BOTTOM
        pie.operator('wm.call_menu_pie', text="Data...", icon="PRESET").name = (
            "PIE_MT_editor_switch_data"
        )
        # 8 - TOP
        pie.operator(
            WM_OT_set_area_type.bl_idname, text="3D View", icon="VIEW3D"
        ).ui_type = "VIEW_3D"
        # 7 - TOP - LEFT
        pie.operator(
            'wm.call_menu_pie', text="2D Editors...", icon="FILE_IMAGE"
        ).name = "PIE_MT_editor_switch_image"
        # 9 - TOP - RIGHT
        pie.operator('wm.call_menu_pie', text="Script...", icon="SCRIPT").name = (
            "PIE_MT_editor_switch_script"
        )
        # 1 - BOTTOM - LEFT
        pie.separator()
        # 3 - BOTTOM - RIGHT
        pie.operator(
            'wm.call_menu_pie', text="Animation...", icon="ARMATURE_DATA"
        ).name = "PIE_MT_editor_switch_anim"


class PIE_MT_editor_switch_video(Menu):
    bl_idname = "PIE_MT_editor_switch_video"
    bl_label = "Editor Switch: Video"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        # 4 - LEFT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname,
            text="Sequencer & Preview",
            icon="SEQ_SPLITVIEW",
        )
        op.ui_type = "SEQUENCE_EDITOR"
        op.view_type = 'SEQUENCER_PREVIEW'
        # 6 - RIGHT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Movie Clip Editor", icon="SEQUENCE"
        )
        op.ui_type = "CLIP_EDITOR"
        op.mode = 'TRACKING'
        op.view = 'CLIP'
        # 2 - BOTTOM
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Clip Mask Editor", icon="MOD_MASK"
        )
        op.ui_type = "CLIP_EDITOR"
        op.mode = 'MASK'
        # 8 - TOP
        pie.separator()
        # 7 - TOP - LEFT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Preview", icon="SEQ_PREVIEW"
        )
        op.ui_type = "SEQUENCE_EDITOR"
        op.view_type = 'PREVIEW'
        # 9 - TOP - RIGHT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Tracking: Dopesheet", icon="ACTION"
        )
        op.ui_type = "CLIP_EDITOR"
        op.mode = 'TRACKING'
        op.view = 'DOPESHEET'
        # 1 - BOTTOM - LEFT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Sequencer", icon="SEQ_SEQUENCER"
        )
        op.ui_type = "SEQUENCE_EDITOR"
        op.view_type = 'SEQUENCER'
        # 3 - BOTTOM - RIGHT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Tracking: Graph", icon="GRAPH"
        )
        op.ui_type = "CLIP_EDITOR"
        op.mode = 'TRACKING'
        op.view = 'GRAPH'


class PIE_MT_editor_switch_nodes(Menu):
    bl_idname = "PIE_MT_editor_switch_nodes"
    bl_label = "Editor Switch: Nodes"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        # 4 - LEFT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Compositing", icon="NODE_COMPOSITING"
        )
        op.ui_type = 'CompositorNodeTree'
        # 6 - RIGHT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Shader", icon="NODE_MATERIAL"
        )
        op.ui_type = 'ShaderNodeTree'
        op.shader_type = 'OBJECT'
        # 2 - BOTTOM
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Geometry", icon="GEOMETRY_NODES"
        )
        op.ui_type = 'GeometryNodeTree'
        # 8 - TOP
        op = pie.operator(WM_OT_set_area_type.bl_idname, text="Texture", icon="TEXTURE")
        op.ui_type = 'TextureNodeTree'
        # 7 - TOP - LEFT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Line Style", icon="LINE_DATA"
        )
        op.ui_type = 'ShaderNodeTree'
        op.shader_type = 'LINESTYLE'
        # 9 - TOP - RIGHT
        if get_custom_nodetree_types(context, layout):
            pie.menu(
                'PIE_MT_editor_switch_nodes_custom',
                text="Custom Nodes",
                icon='NODETREE',
            )
        else:
            pie.separator()
        # 1 - BOTTOM - LEFT
        pie.separator()
        # 3 - BOTTOM - RIGHT
        op = pie.operator(WM_OT_set_area_type.bl_idname, text="World", icon="WORLD")
        op.ui_type = 'ShaderNodeTree'
        op.shader_type = 'WORLD'


class PIE_MT_editor_switch_nodes_custom(Menu):
    bl_idname = "PIE_MT_editor_switch_nodes_custom"
    bl_label = "Editor Switch: Custom Nodes"

    def draw(self, context):
        layout = self.layout

        for ui_type, label, icon in get_custom_nodetree_types(context, layout):
            layout.operator(
                WM_OT_set_area_type.bl_idname, text=label, icon=icon
            ).ui_type = ui_type


def get_custom_nodetree_types(context, layout):
    """There are no rules In love, war, and Python scripting.
    The only way to get custom node tree types is this:
    - Try to set the UI type to some nonsense
    - The resulting error tells you the possible UI types
    - Catch and crunch the error string into a set
    - Subtract from this the set of built-in UI types
    - The result is a set of the custom node tree type names
    - We can get their class with bl_rna_get_subclass_py

    """
    builtin_types = set(
        [
            'VIEW_3D',
            'IMAGE_EDITOR',
            'UV',
            'CompositorNodeTree',
            'TextureNodeTree',
            'GeometryNodeTree',
            'ShaderNodeTree',
            'SEQUENCE_EDITOR',
            'CLIP_EDITOR',
            'DOPESHEET',
            'TIMELINE',
            'FCURVES',
            'DRIVERS',
            'NLA_EDITOR',
            'TEXT_EDITOR',
            'CONSOLE',
            'INFO',
            'OUTLINER',
            'PROPERTIES',
            'FILES',
            'ASSETS',
            'SPREADSHEET',
            'PREFERENCES',
        ]
    )
    ret = []
    try:
        context.area.ui_type = "Nonsense."
    except Exception as exc:
        exc_type, exc_value, tb = sys.exc_info()
        if not exc_value:
            return []
        type_list_str = (
            str(exc_value)
            .split("not found in ")[-1]
            .replace("(", "[")
            .replace(")", "]")
            .replace("'", '"')
        )
        type_list = set(json.loads(type_list_str))
        custom_types = type_list - builtin_types

        for type_name in custom_types:
            type_class = bpy.types.NodeTree.bl_rna_get_subclass_py(type_name)
            if not type_class:
                continue
            ret.append((type_name, type_class.bl_label, type_class.bl_icon))

    return ret


class PIE_MT_editor_switch_data(Menu):
    bl_idname = "PIE_MT_editor_switch_data"
    bl_label = "Editor Switch: Data"

    def draw(self, context):
        pie = self.layout.menu_pie()

        # 4 - LEFT
        pie.operator(
            WM_OT_set_area_type.bl_idname, text="File Browser", icon="FILEBROWSER"
        ).ui_type = "FILES"
        # 6 - RIGHT
        pie.operator(
            WM_OT_set_area_type.bl_idname, text="Preferences", icon="PREFERENCES"
        ).ui_type = "PREFERENCES"
        # 2 - BOTTOM
        pie.operator(
            WM_OT_set_area_type.bl_idname, text="Outliner", icon="OUTLINER"
        ).ui_type = "OUTLINER"
        # 8 - TOP
        pie.operator(
            WM_OT_set_area_type.bl_idname, text="Properties", icon="PROPERTIES"
        ).ui_type = "PROPERTIES"
        # 7 - TOP - LEFT
        pie.operator(
            WM_OT_set_area_type.bl_idname, text="Asset Browser", icon="ASSET_MANAGER"
        ).ui_type = "ASSETS"
        # 9 - TOP - RIGHT
        pie.menu(
            "PIE_MT_editor_switch_properties",
            text="Properties Types...",
            icon="PROPERTIES",
        )
        # 1 - BOTTOM - LEFT
        pie.operator(
            WM_OT_set_area_type.bl_idname, text="Spreadsheet", icon="SPREADSHEET"
        ).ui_type = "SPREADSHEET"
        # 3 - BOTTOM - RIGHT
        pie.menu(
            "PIE_MT_editor_switch_outliner", text="Outliner Types...", icon="OUTLINER"
        )


class PIE_MT_editor_switch_outliner(Menu):
    bl_idname = "PIE_MT_editor_switch_outliner"
    bl_label = "Editor Switch: Outliner"

    def draw(self, context):
        pie = self.layout#.menu_pie()

        # 4 - LEFT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Scenes", icon="SCENE_DATA"
        )
        op.ui_type = "OUTLINER"
        op.display_mode = 'SCENES'
        # 6 - RIGHT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="View Layer", icon="RENDERLAYERS"
        )
        op.ui_type = "OUTLINER"
        op.display_mode = 'VIEW_LAYER'
        # 2 - BOTTOM
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Video Sequencer", icon="SEQUENCE"
        )
        op.ui_type = "OUTLINER"
        op.display_mode = 'SEQUENCE'
        # 8 - TOP
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Blender File", icon="FILE_BLEND"
        )
        op.ui_type = "OUTLINER"
        op.display_mode = 'LIBRARIES'
        # 7 - TOP - LEFT
        op = pie.operator(WM_OT_set_area_type.bl_idname, text="Data API", icon="RNA")
        op.ui_type = "OUTLINER"
        op.display_mode = 'DATA_API'
        # 9 - TOP - RIGHT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname,
            text="Library Overrides",
            icon="LIBRARY_DATA_OVERRIDE",
        )
        op.ui_type = "OUTLINER"
        op.display_mode = 'LIBRARY_OVERRIDES'
        # 1 - BOTTOM - LEFT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Orphan Data", icon="ORPHAN_DATA"
        )
        op.ui_type = "OUTLINER"
        op.display_mode = 'ORPHAN_DATA'
        # 3 - BOTTOM - RIGHT


def get_available_properties_editors(context):
    """Similar hack as get_custom_nodetree_types.
    Ideally we need an existing Properties editor, otherwise
    the list of available types is not up to date.
    Although even in that case, we still don't get an error,
    so this is fine.
    """
    org_ui_type = context.area.ui_type
    try:
        space = None
        for area in context.screen.areas:
            if area.ui_type == 'PROPERTIES':
                space = area.spaces.active
                break
        if not space:
            context.area.ui_type = 'PROPERTIES'
            space = context.space_data
        space.context = "Nonsense."
    except Exception as exc:
        exc_type, exc_value, tb = sys.exc_info()
        if not exc_value:
            return []
        type_list_str = (
            str(exc_value)
            .split("not found in ")[-1]
            .replace("(", "[")
            .replace(")", "]")
            .replace("'", '"')
        )
        available_types = set(json.loads(type_list_str))
        context.area.ui_type = org_ui_type
        return available_types


class PIE_MT_editor_switch_properties(Menu):
    bl_idname = "PIE_MT_editor_switch_properties"
    bl_label = "Editor Switch: Properties"

    def draw(self, context):
        layout = self.layout

        available_editors = get_available_properties_editors(context)

        def safe_draw(pie, text, icon, context_name):
            if context_name in available_editors:
                op = pie.operator(WM_OT_set_area_type.bl_idname, text=text, icon=icon)
                op.ui_type = "PROPERTIES"
                op.context_name = context_name
            else:
                pie.separator()

        safe_draw(layout, "Render", 'SCENE', 'RENDER')
        safe_draw(layout, "Output", 'OUTPUT', 'OUTPUT')
        safe_draw(layout, "View Layer", 'RENDERLAYERS', 'VIEW_LAYER')
        safe_draw(layout, "Scene", 'SCENE_DATA', 'SCENE')
        safe_draw(layout, "World", 'WORLD', 'WORLD')
        layout.separator()
        safe_draw(layout, "Object", 'OBJECT_DATAMODE', 'OBJECT')
        safe_draw(layout, "Modifiers", 'MODIFIER', 'MODIFIER')
        safe_draw(layout, "Particles", 'PARTICLES', 'PARTICLES')
        safe_draw(layout, "Physics", 'PHYSICS', 'PHYSICS')
        safe_draw(layout, "Constraints", 'CONSTRAINT', 'CONSTRAINT')
        safe_draw(layout, "Object Data", 'OUTLINER_DATA_MESH', 'DATA')
        safe_draw(layout, "Material", 'MATERIAL', 'MATERIAL')
        layout.separator()
        safe_draw(layout, "Texture", 'TEXTURE', 'TEXTURE')


class PIE_MT_editor_switch_image(Menu):
    bl_idname = "PIE_MT_editor_switch_image"
    bl_label = "Editor Switch: 2D Editors"

    def draw(self, context):
        pie = self.layout.menu_pie()

        # 4 - LEFT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Image Viewer", icon="SEQ_PREVIEW"
        )
        op.ui_type = "IMAGE_EDITOR"
        op.ui_mode = "VIEW"
        # 6 - RIGHT
        op = pie.operator(WM_OT_set_area_type.bl_idname, text="UV Editor", icon="UV")
        op.ui_type = "UV"
        # 2 - BOTTOM
        pie.separator()
        # 8 - TOP
        pie.separator()
        # 7 - TOP - LEFT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Image Paint", icon="TPAINT_HLT"
        )
        op.ui_type = "IMAGE_EDITOR"
        op.ui_mode = "PAINT"
        # 9 - TOP - RIGHT
        pie.separator()
        # 1 - BOTTOM - LEFT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Image Masking", icon="MOD_MASK"
        )
        op.ui_type = "IMAGE_EDITOR"
        op.ui_mode = "PAINT"
        # 3 - BOTTOM - RIGHT


class PIE_MT_editor_switch_script(Menu):
    bl_idname = "PIE_MT_editor_switch_script"
    bl_label = "Editor Switch: Script"

    def draw(self, context):
        pie = self.layout.menu_pie()

        # 4 - LEFT
        pie.separator()
        # 6 - RIGHT
        pie.operator(
            WM_OT_set_area_type.bl_idname, text="Text Editor", icon="TEXT"
        ).ui_type = "TEXT_EDITOR"
        # 2 - BOTTOM
        pie.operator(
            WM_OT_set_area_type.bl_idname, text="Python Console", icon="CONSOLE"
        ).ui_type = "CONSOLE"
        # 8 - TOP
        pie.operator(
            WM_OT_set_area_type.bl_idname, text="Info", icon="INFO"
        ).ui_type = "INFO"
        # 7 - TOP - LEFT
        # 9 - TOP - RIGHT
        # 1 - BOTTOM - LEFT
        # 3 - BOTTOM - RIGHT


class PIE_MT_editor_switch_anim(Menu):
    bl_idname = "PIE_MT_editor_switch_anim"
    bl_label = "Editor Switch: Animation"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        # 4 - LEFT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Grease Pencil", icon="GREASEPENCIL"
        )
        op.ui_type = 'DOPESHEET'
        op.ui_mode = 'GPENCIL'
        # 6 - RIGHT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Dopesheet", icon="ACTION"
        )
        op.ui_type = 'DOPESHEET'
        op.ui_mode = 'DOPESHEET'
        # 2 - BOTTOM
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Driver Editor", icon="DRIVER"
        )
        op.ui_type = 'DRIVERS'
        # 8 - TOP
        op = pie.operator(WM_OT_set_area_type.bl_idname, text="Timeline", icon="TIME")
        op.ui_type = 'TIMELINE'
        # 7 - TOP - LEFT
        pie.separator()
        # 9 - TOP - RIGHT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Graph Editor", icon="GRAPH"
        )
        op.ui_type = 'FCURVES'
        # 1 - BOTTOM - LEFT
        op = pie.operator(WM_OT_set_area_type.bl_idname, text="NLA Editor", icon="NLA")
        op.ui_type = 'NLA_EDITOR'
        # 3 - BOTTOM - RIGHT
        op = pie.operator(
            WM_OT_set_area_type.bl_idname, text="Action Editor", icon="OBJECT_DATAMODE"
        )
        op.ui_type = 'DOPESHEET'
        op.ui_mode = 'ACTION'


class WM_OT_set_area_type(Operator):
    """Change editor type and sub-type"""

    bl_idname = "wm.set_area_type"
    bl_label = "Change Editor Type"
    bl_options = {'REGISTER', 'INTERNAL'}

    ui_type: StringProperty(name="Area Type")
    view_type: StringProperty(default="", options={'SKIP_SAVE'})
    shader_type: StringProperty(default="", options={'SKIP_SAVE'})
    context_name: StringProperty(default="", options={'SKIP_SAVE'})
    display_mode: StringProperty(default="", options={'SKIP_SAVE'})
    ui_mode: StringProperty(default="", options={'SKIP_SAVE'})
    mode: StringProperty(default="", options={'SKIP_SAVE'})
    view: StringProperty(default="", options={'SKIP_SAVE'})

    def execute(self, context):
        context.area.ui_type = self.ui_type
        if self.view_type:
            context.space_data.view_type = self.view_type
        if self.shader_type:
            context.space_data.shader_type = self.shader_type
        if self.context_name:
            context.space_data.context = self.context_name
        if self.display_mode:
            context.space_data.display_mode = self.display_mode
        if self.ui_mode:
            context.space_data.ui_mode = self.ui_mode
        if self.mode:
            context.space_data.mode = self.mode
        if self.view:
            context.space_data.view = self.view

        return {'FINISHED'}


registry = [
    PIE_MT_editor_switch,
    PIE_MT_editor_switch_video,
    PIE_MT_editor_switch_nodes,
    PIE_MT_editor_switch_nodes_custom,
    PIE_MT_editor_switch_data,
    PIE_MT_editor_switch_outliner,
    PIE_MT_editor_switch_properties,
    PIE_MT_editor_switch_image,
    PIE_MT_editor_switch_script,
    PIE_MT_editor_switch_anim,
    WM_OT_set_area_type,
]


def register():
    WM_OT_call_menu_pie_drag_only.register_drag_hotkey(
        keymap_name="Window",
        pie_name=PIE_MT_editor_switch.bl_idname,
        hotkey_kwargs={'type': "S", 'value': "PRESS", 'ctrl': True, 'alt': True},
        on_drag=False,
    )
