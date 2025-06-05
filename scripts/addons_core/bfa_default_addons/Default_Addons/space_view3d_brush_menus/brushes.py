# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Menu
from . import utils_core
from bl_ui.properties_paint_common import UnifiedPaintPanel

# Particle Tools

particle_tools = (
    ("Comb", 'COMB'),
    ("Smooth", 'SMOOTH'),
    ("Add", 'ADD'),
    ("Length", 'LENGTH'),
    ("Puff", 'PUFF'),
    ("Cut", 'CUT'),
    ("Weight", 'WEIGHT')
)

# Brush Datapaths

brush_datapath = {
    'SCULPT': "tool_settings.sculpt.brush",
    'VERTEX_PAINT': "tool_settings.vertex_paint.brush",
    'WEIGHT_PAINT': "tool_settings.weight_paint.brush",
    'TEXTURE_PAINT': "tool_settings.image_paint.brush",
    'PARTICLE_EDIT': "tool_settings.particle_edit.tool"
}

# Brush Icons

brush_icon = {
    'SCULPT': {
    "BLOB": 'BRUSH_BLOB',
    "BOUNDARY": 'BRUSH_GRAB',
    "CLAY": 'BRUSH_CLAY',
    "CLAY_STRIPS": 'BRUSH_CLAY_STRIPS',
    "CLAY_THUMB": 'BRUSH_CLAY_STRIPS',
    "CLOTH": 'BRUSH_SCULPT_DRAW',
    "CREASE": 'BRUSH_CREASE',
    "DISPLACEMENT_ERASER": 'BRUSH_SCULPT_DRAW',
    "DISPLACEMENT_SMEAR": 'BRUSH_SCULPT_DRAW',
    "DRAW": 'BRUSH_SCULPT_DRAW',
    "DRAW_FACE_SETS": 'BRUSH_MASK',
    "DRAW_SHARP": 'BRUSH_SCULPT_DRAW',
    "ELASTIC_DEFORM": 'BRUSH_GRAB',
    "FILL": 'BRUSH_FILL',
    "FLATTEN": 'BRUSH_FLATTEN',
    "GRAB": 'BRUSH_GRAB',
    "INFLATE": 'BRUSH_INFLATE',
    "LAYER": 'BRUSH_LAYER',
    "MASK": 'BRUSH_MASK',
    "MULTIPLANE_SCRAPE": 'BRUSH_SCRAPE',
    "NUDGE": 'BRUSH_NUDGE',
    "PAINT": 'BRUSH_SCULPT_DRAW',
    "PINCH": 'BRUSH_PINCH',
    "POSE": 'BRUSH_GRAB',
    "ROTATE": 'BRUSH_ROTATE',
    "SCRAPE": 'BRUSH_SCRAPE',
    "SIMPLIFY": 'BRUSH_DATA',
    "SMOOTH": 'BRUSH_SMOOTH',
    "SNAKE_HOOK": 'BRUSH_SNAKE_HOOK',
    "THUMB": 'BRUSH_THUMB',
    "TOPOLOGY": 'BRUSH_GRAB',
    },

    'VERTEX_PAINT': {
    "AVERAGE": 'BRUSH_BLUR',
    "BLUR": 'BRUSH_BLUR',
    "DRAW": 'BRUSH_MIX',
    "SMEAR": 'BRUSH_BLUR',
    },

    'WEIGHT_PAINT': {
    "AVERAGE": 'BRUSH_BLUR',
    "BLUR": 'BRUSH_BLUR',
    "DRAW": 'BRUSH_MIX',
    "SMEAR": 'BRUSH_BLUR',
    },

    'TEXTURE_PAINT': {
    "CLONE": 'BRUSH_CLONE',
    "DRAW": 'BRUSH_TEXDRAW',
    "FILL": 'BRUSH_TEXFILL',
    "MASK": 'BRUSH_TEXMASK',
    "SMEAR": 'BRUSH_SMEAR',
    "SOFTEN": 'BRUSH_SOFTEN',
    },
}

def get_brush_icon(mode, tool):
    mode_icons = brush_icon.get(mode, None)

    if mode_icons == None:
        print(f"Warning: icons for mode {mode} aren't supported")
        return 'BRUSH_DATA'

    icon = mode_icons.get(tool, None)

    if icon == None:
        print(f"Warning: Could not find icon for tool {tool} in mode {mode}")
        return 'BRUSH_DATA'


    return icon


class BrushesMenu(Menu):
    bl_label = "Brush"
    bl_idname = "VIEW3D_MT_sv3_brushes_menu"

    def draw(self, context):
        mode = utils_core.get_mode()
        layout = self.layout
        settings = UnifiedPaintPanel.paint_settings(context)
        colum_n = utils_core.addon_settings()

        layout.row().label(text="Brush")
        layout.row().separator()

        has_brush = utils_core.get_brush_link(context, types="brush")
        current_brush = eval("bpy.context.{}".format(brush_datapath[mode])) if has_brush else None

        # get the current brush's name
        if current_brush and utils_core.get_mode() != 'PARTICLE_EDIT':
            current_brush = current_brush.name

        if mode == 'PARTICLE_EDIT':
            # if you are in particle edit mode add the menu items for particle mode
            for tool in particle_tools:
                utils_core.menuprop(
                        layout.row(), tool[0], tool[1], brush_datapath[mode],
                        icon='RADIOBUT_OFF', disable=True,
                        disable_icon='RADIOBUT_ON'
                        )
        else:
            column_flow = layout.column_flow(columns=colum_n)

            # iterate over all the brushes
            for item in bpy.data.brushes:
                if mode == 'SCULPT':
                    if item.use_paint_sculpt:
                        # if you are in sculpt mode and the brush
                        # is a sculpt brush add the brush to the menu
                        utils_core.menuprop(
                                column_flow.row(), item.name,
                                'bpy.data.brushes["%s"]' % item.name,
                                brush_datapath[mode], icon=get_brush_icon(mode, item.sculpt_tool),
                                disable=True, custom_disable_exp=(item.name, current_brush),
                                path=True
                                )
                if mode == 'VERTEX_PAINT':
                    if item.use_paint_vertex:
                        # if you are in vertex paint mode and the brush
                        # is a vertex paint brush add the brush to the menu
                        utils_core.menuprop(
                                column_flow.row(), item.name,
                                'bpy.data.brushes["%s"]' % item.name,
                                brush_datapath[mode], icon=get_brush_icon(mode, item.vertex_tool),
                                disable=True, custom_disable_exp=(item.name, current_brush),
                                path=True
                                )
                if mode == 'WEIGHT_PAINT':
                    if item.use_paint_weight:
                        # if you are in weight paint mode and the brush
                        # is a weight paint brush add the brush to the menu
                        utils_core.menuprop(
                                column_flow.row(), item.name,
                                'bpy.data.brushes["%s"]' % item.name,
                                brush_datapath[mode], icon=get_brush_icon(mode, item.weight_tool),
                                disable=True, custom_disable_exp=(item.name, current_brush),
                                path=True
                                )
                if utils_core.get_mode() == 'TEXTURE_PAINT':
                    if item.use_paint_image:
                        # if you are in texture paint mode and the brush
                        # is a texture paint brush add the brush to the menu
                        utils_core.menuprop(
                                column_flow.row(), item.name,
                                'bpy.data.brushes["%s"]' % item.name,
                                brush_datapath[mode], icon=get_brush_icon(mode, item.image_tool),
                                disable=True, custom_disable_exp=(item.name, current_brush),
                                path=True
                                )


def register():
    bpy.utils.register_class(BrushesMenu)

def unregister():
    bpy.utils.unregister_class(BrushesMenu)
