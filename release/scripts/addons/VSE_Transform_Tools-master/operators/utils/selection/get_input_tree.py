def get_input_tree(strip):
    """
    Recursively gather a list of the strip and all subsequent input_1
    and input_2 strips in it's heirarchy.

    Arg
        :strip: A strip (bpy.types.Sequence)
    Return
        :inputs: A list of strips from an input heirarchy (list of
                 bpy.types.Sequence)
    """
    inputs = [strip]

    if hasattr(strip, 'input_1'):
        inputs.extend(get_input_tree(strip.input_1))
    if hasattr(strip, 'input_2'):
        inputs.extend(get_input_tree(strip.input_2))

    return inputs
