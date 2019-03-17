# These forwarding imports are for backwards compatibility with legacy code
# that expects a single utils.py file. New code should import directly from
# the modules that contain the utilities. Also, don't add more imports here.

from .errors import MetarigError

from .misc import angle_on_plane, linsrgb_to_srgb, gamma_correct, copy_attributes

from .naming import ORG_PREFIX, MCH_PREFIX, DEF_PREFIX, ROOT_NAME
from .naming import strip_trailing_number, unique_name, org_name, strip_org, strip_mch, strip_def
from .naming import org, make_original_name, mch, make_mechanism_name, deformer, make_deformer_name
from .naming import insert_before_lr, random_id

from .bones import new_bone, copy_bone_simple, copy_bone, flip_bone, put_bone, make_nonscaling_child
from .bones import align_bone_roll, align_bone_x_axis, align_bone_z_axis, align_bone_y_axis

from .widgets import WGT_PREFIX, obj_to_bone, create_widget, write_widget, create_circle_polygon

from .widgets_basic import create_line_widget, create_circle_widget, create_cube_widget, create_chain_widget
from .widgets_basic import create_sphere_widget, create_limb_widget, create_bone_widget

from .widgets_special import create_compass_widget, create_root_widget
from .widgets_special import create_neck_bend_widget, create_neck_tweak_widget

from .animation import get_keyed_frames, bones_in_frame, overwrite_prop_animation

from .rig import RIG_DIR, METARIG_DIR, MODULE_NAME, TEMPLATE_DIR, outdated_types, upgradeMetarigTypes
from .rig import get_rig_type, get_metarig_module, write_metarig, get_resource
from .rig import connected_children_names, has_connected_children

from .layers import get_layers, ControlLayersOption
