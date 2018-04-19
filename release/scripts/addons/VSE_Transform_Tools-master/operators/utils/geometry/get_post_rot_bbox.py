import math


def get_post_rot_bbox(left, right, bottom, top, rotation):
    """
    Return bounding box of a rotated rectangle.

    Args
        :left:     left horizontal position of the unrotated rectangle
                   (float)
        :right:    right horizontal position of the unrotated rectangle
                   (float)
        :bottom:   bottom vertical position of the unrotated rectangle
                   (float)
        :top:      top vertical position of the unrotated rectangle
                   (float)
        :rotation: rotation of the rectangle in radians (float)
    Returns
        :b_left:   minimum horizontal extremity of the rotated rectangle
        :b_right:  maximum horizontal extremity of the rotated rectangle
        :b_bottom: minimum vertical extremity of the rotated rectangle
        :b_top:    maximum vertical extremity of the rotated rectangle
    """

    rotation = abs(rotation)
    width = right - left
    height = top - bottom

    b_width = (math.sin(rotation) * height) + (math.cos(rotation) * width)
    b_height = (math.sin(rotation) * width) + (math.cos(rotation) * height)

    diff_x = (b_width - width) / 2
    b_left = left - diff_x
    b_right = right + diff_x

    diff_y = (b_height - height) / 2
    b_bottom = bottom - diff_y
    b_top = top + diff_y

    return b_left, b_right, b_bottom, b_top
