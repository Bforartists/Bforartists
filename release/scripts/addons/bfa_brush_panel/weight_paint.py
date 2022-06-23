import bpy

from .common import column_count, draw_brush_button


def icon_name_from_weight_brush(weight_brush: bpy.types.Brush):
    # Values should match toolsystem
    # release\scripts\startup\bl_ui\space_toolsystem_toolbar.py
    icon_prefix = "brush.paint_weight."
    idname = weight_brush.weight_tool
    icon_name = icon_prefix + idname.lower()
    return icon_name


# TODO: generalize this base calss to work with all modes
class WeightBrushPanelBase(bpy.types.Panel):
    bl_label = "Brush"  # Override this
    bl_region_type = "TOOLS"
    bl_space_type = "VIEW_3D"
    bl_category = "Brushes"
    bl_options = {"HIDE_BG"}

    tool_name = ""  # Override this

    @classmethod
    def poll(cls, context):
        return context.mode == "PAINT_WEIGHT"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.scale_y = 2
        num_cols = column_count(context.region)
        if num_cols == 4:
            col = layout.column(align=True)
            icon_only = False
        else:
            col = layout.column_flow(columns=num_cols, align=True)
            icon_only = True

        for brush in sorted(bpy.data.brushes, key=lambda brush: brush.name):
            if not brush.use_paint_weight:
                continue
            if brush.weight_tool == self.tool_name:
                draw_brush_button(
                    context,
                    col,
                    icon_only,
                    brush,
                    "weight_paint",
                    icon_name_from_weight_brush,
                )


WEIGHT_TOOLS = ["DRAW", "SMEAR", "AVERAGE", "BLUR"]
panel_classes = [
    type(
        f"BFA_PT_brush_weight_{tool_name}",
        (WeightBrushPanelBase,),
        {
            "bl_label": tool_name.capitalize(),
            "tool_name": tool_name,
        },
    )
    for tool_name in WEIGHT_TOOLS
]


def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in panel_classes:
        bpy.utils.unregister_class(cls)
