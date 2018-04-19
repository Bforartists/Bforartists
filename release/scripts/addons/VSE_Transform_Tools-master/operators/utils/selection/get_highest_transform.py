import bpy
from .get_input_tree import get_input_tree


def get_highest_transform(strip):
    """
    Return the highest transform strip in a modifier hierarchy

    Args
        :strip: A strip (bpy.types.Sequence)
    """
    scene = bpy.context.scene

    all_sequences = list(sorted(scene.sequence_editor.sequences_all,
                                key=lambda x: x.channel))

    all_sequences.reverse()

    checked_strips = []

    for seq in all_sequences:
        if seq not in checked_strips:
            tree = get_input_tree(seq)

            if strip in tree:
                for branch in tree:
                    if branch.type == "TRANSFORM":
                        return branch

                    elif branch == strip:
                        return seq
            else:
                checked_strips.extend(tree)
