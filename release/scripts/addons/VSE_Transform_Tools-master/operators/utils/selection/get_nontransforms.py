def get_nontransforms(strips):
    """
    Get a list of the non-transform strips from the given list of
    strips.
    """
    nontransforms = []
    for i in range(len(strips)):
        if strips[i].type != "TRANSFORM" and strips[i].type != "SOUND":
            nontransforms.append(strips[i])

    return nontransforms

