import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def bool_tool_manual_map():
    url_manual_prefix = "https://nickberckley.github.io/bool_tool/"

    # Carver
    url_manual_mapping = (# Brush Boolean
                          ("bpy.ops.object.boolean_brush_union", "booleans/brush_booleans.html"),
                          ("bpy.ops.object.boolean_brush_intersect", "booleans/brush_booleans.html"),
                          ("bpy.ops.object.boolean_brush_difference", "booleans/brush_booleans.html"),
                          ("bpy.ops.object.boolean_brush_slice", "booleans/brush_booleans.html"),
                          # Auto Boolean
                          ("bpy.ops.object.boolean_auto_union", "booleans/auto_booleans.html"),
                          ("bpy.ops.object.boolean_auto_intersect", "booleans/auto_booleans.html"),
                          ("bpy.ops.object.boolean_auto_difference", "booleans/auto_booleans.html"),
                          ("bpy.ops.object.boolean_auto_slice", "booleans/auto_booleans.html"),
                          # Carver
                          ("bpy.ops.object.carve_box", "carver/index.html"),
                          ("bpy.ops.object.carve_circle", "carver/index.html"),
                          ("bpy.ops.object.carve_polyline", "carver/index.html"),
                          # Cutter Utilities
                          ("bpy.ops.object.boolean_toggle_cutter", "utilities/toggle.html"),
                          ("bpy.ops.object.boolean_remove_cutter", "utilities/remove.html"),
                          ("bpy.ops.object.boolean_apply_cutter", "utilities/apply.html"),
                          # Canvas Utilities
                          ("bpy.ops.object.boolean_toggle_all", "utilities/toggle.html"),
                          ("bpy.ops.object.boolean_remove_all", "utilities/remove.html"),
                          ("bpy.ops.object.boolean_apply_all", "utilities/apply.html"),
                          # Select
                          ("bpy.ops.object.select_cutter_canvas", "utilities/select.html"),
                          ("bpy.ops.object.boolean_select_all", "utilities/select.html"),
    )

    return url_manual_prefix, url_manual_mapping



#### ------------------------------ REGISTRATION ------------------------------ ####

def register():
    # MANUAL
    bpy.utils.register_manual_map(bool_tool_manual_map)

def unregister():
    # MANUAL
    bpy.utils.unregister_manual_map(bool_tool_manual_map)
