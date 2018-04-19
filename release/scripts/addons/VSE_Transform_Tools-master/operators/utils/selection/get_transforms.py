def get_transforms(strips):
    """
    Get a list of the selected transform strips
    """
    transforms = []
    for i in range(len(strips)):
        if strips[i].type == "TRANSFORM":
            transforms.append(strips[i])

    return transforms
