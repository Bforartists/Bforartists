import bpy
import math

from ..utils.geometry import get_transform_box
from ..utils.geometry import get_pos_x
from ..utils.geometry import get_pos_y
from ..utils.geometry import set_pos_x
from ..utils.geometry import set_pos_y
from ..utils.geometry import get_preview_offset


def crop_scale(self, strip, crops):
    """
    Set the strip_in crop and the strip's scale and position.

    When cropping, the transform strip's position and scale must change
    along with the crop it's input in order to keep the same location in
    the preview window.

    Parameters
    ----------
    strip : bpy.types.Sequence
        This is the transform strip that will be cropped
    crops : list of int
        Left, right, bottom, top crops to apply to the strip
    """
    context = bpy.context
    scene = context.scene

    res_x = scene.render.resolution_x
    res_y = scene.render.resolution_y

    left, right, bottom, top = get_transform_box(strip)
    width = right - left
    height = top - bottom

    strip_in = strip.input_1

    crop_left, crop_right, crop_bottom, crop_top = crops

    rot = math.radians(strip.rotation_start)

    cos = math.cos(rot)
    sin = math.sin(rot)

    crop_xl = strip_in.crop.min_x
    crop_xr = strip_in.crop.max_x
    crop_yb = strip_in.crop.min_y
    crop_yt = strip_in.crop.max_y

    crop_adjust_l = crop_left - crop_xl
    crop_adjust_r = crop_right - crop_xr
    crop_adjust_b = crop_bottom - crop_yb
    crop_adjust_t = crop_top - crop_yt

    proxy_facs = {
        'NONE': 1.0,
        'SCENE': 1.0,
        'FULL': 1.0,
        'PROXY_100': 1.0,
        'PROXY_75': 0.75,
        'PROXY_50': 0.5,
        'PROXY_25': 0.25
    }

    proxy_key = context.space_data.proxy_render_size
    proxy_fac = proxy_facs[proxy_key]

    orig_width = res_x
    orig_height = res_y
    if hasattr(strip_in, 'elements'):
        orig_width = strip_in.elements[0].orig_width
        orig_height = strip_in.elements[0].orig_height

        if not (strip_in.type == 'IMAGE' and proxy_fac < 1.0):
            orig_width /= proxy_fac
            orig_height /= proxy_fac

    elif strip_in.type == "SCENE":
        strip_scene = bpy.data.scenes[strip_in.name]

        orig_width = strip_scene.render.resolution_x
        orig_height = strip_scene.render.resolution_y

    strip_in.crop.min_x = crop_left
    strip_in.crop.max_x = crop_right
    strip_in.crop.min_y = crop_bottom
    strip_in.crop.max_y = crop_top

    # Find the scale_x growth factor
    scl_x = 0
    if orig_width - crop_left - crop_right > 0:
        scl_x = (orig_width - crop_left - crop_right) / (orig_width - crop_xl - crop_xr)

    scl_y = 0
    if orig_height - crop_top - crop_bottom > 0:
        scl_y = (orig_height - crop_bottom - crop_top) / (orig_height - crop_yb - crop_yt)

    strip.scale_start_x *= scl_x
    strip.scale_start_y *= scl_y

    # Find the translation difference between old and new
    width_diff = (width * scl_x) - width
    height_diff = (height * scl_y) - height

    left_shift = 0
    right_shift = 0
    if abs(crop_adjust_l + crop_adjust_r) > 0:
        left_shift = width_diff * (crop_adjust_l / (crop_adjust_l + crop_adjust_r))
        right_shift = width_diff * (crop_adjust_r / (crop_adjust_l + crop_adjust_r))

    bottom_shift = 0
    top_shift = 0
    if abs(crop_adjust_b + crop_adjust_t) > 0:
        bottom_shift = height_diff * (crop_adjust_b / (crop_adjust_b + crop_adjust_t))
        top_shift = height_diff * (crop_adjust_t / (crop_adjust_b + crop_adjust_t))

    pos_x = get_pos_x(strip)
    pos_y = get_pos_y(strip)

    pos_x -= (left_shift * cos) / 2
    pos_x += (right_shift * cos) / 2
    pos_x += (bottom_shift * sin) / 2
    pos_x -= (top_shift * sin) / 2

    pos_y -= (bottom_shift * cos) / 2
    pos_y += (top_shift * cos) / 2
    pos_y -= (left_shift * sin) / 2
    pos_y += (right_shift * sin) / 2

    strip.translate_start_x = set_pos_x(strip, pos_x)
    strip.translate_start_y = set_pos_y(strip, pos_y)

    self.scale_factor_x = (res_x / orig_width) * strip.scale_start_x
    self.scale_factor_y = (res_y / orig_height) * strip.scale_start_y

    self.init_crop_left = crop_xl
    self.init_crop_right = crop_xr
    self.init_crop_bottom = crop_yb
    self.init_crop_top = crop_yt

    offset_x, offset_y, fac, preview_zoom = get_preview_offset()
    self.crop_left = crop_xl * self.scale_factor_x
    self.crop_right = crop_xr * self.scale_factor_x
    self.crop_bottom = crop_yb * self.scale_factor_y
    self.crop_top = crop_yt * self.scale_factor_y
