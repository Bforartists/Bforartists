import bpy
from .get_highest_transform import get_highest_transform


def ensure_transforms():
    """
    Check each selected strip. If it is not a transform strip, use
    bpy.ops.vse_transform_tools.add_transform() to add a transform to
    that strip.

    Returns
        :final_selected: A list of all the transform strips related to
                         the current selected strips, both those
                         pre-existing and those added by this function.
                         (list of bpy.types.Sequence)
    """
    context = bpy.context
    scene = context.scene

    selected = bpy.context.selected_sequences
    transforms = []
    for strip in selected:
        transform_strip = get_highest_transform(strip)
        if transform_strip not in transforms:
            transforms.append(transform_strip)

    for strip in selected:
        if not strip in transforms:
            strip.select = False

    for strip in transforms:
        strip.select = True

    new_active = get_highest_transform(
        scene.sequence_editor.active_strip)

    scene.sequence_editor.active_strip = new_active

    final_selected = []
    for strip in transforms:
        bpy.ops.sequencer.select_all(action="DESELECT")

        if not strip.type == "TRANSFORM":
            strip.select = True
            bpy.ops.vse_transform_tools.add_transform()
            active = scene.sequence_editor.active_strip
            final_selected.append(active)

        else:
            final_selected.append(strip)

    return final_selected

