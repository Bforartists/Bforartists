"""Operator class collection for registration."""

from .settings_ops import AA_OT_export_settings, AA_OT_import_settings
from .timeline_slider_ops import CLASSES as _timeline_slider_classes
from .diagnostics_ops import AA_OT_copy_diagnostics, AA_OT_refresh_diagnostics
from .keymanager_ops import classes as _keymanager_classes
from .anim_offset_ops import classes as _anim_offset_classes
from .curve_tool_ops import classes as _curve_tool_classes

from .p2_select_ops import classes as _p2_select_classes
from .p2_channel_ops import classes as _p2_channel_classes
from .p2_keymeta_ops import classes as _p2_keymeta_classes
from .p2_diag_ops import classes as _p2_diag_classes
from .p2_key_ops import classes as _p2_key_classes

from ..core.p3_properties import CLASSES as _p3_property_classes
from .p3_breakdown_ops import CLASSES as _p3_breakdown_classes
from .p3_inbetween_ops import CLASSES as _p3_inbetween_classes
from .p3_pose_compare_ops import CLASSES as _p3_pose_compare_classes
from .p3_preset_ops import CLASSES as _p3_preset_classes
from .p3_modal_ops import CLASSES as _p3_modal_classes

from .help_popup import classes as _help_popup_classes

from ..core.p4_properties import CLASSES as _p4_property_classes
from .p4_offset_ops import CLASSES as _p4_offset_classes
from .p4_pushpull_ops import CLASSES as _p4_pushpull_classes
from .p4_modal_ops import CLASSES as _p4_modal_classes

from ..core.p5_properties import CLASSES as _p5_property_classes
from .p5_overlay_ops import CLASSES as _p5_overlay_classes
from .p5_nav_ops import CLASSES as _p5_nav_classes

from ..core.p6_properties import CLASSES as _p6_property_classes
from ..core.p7_properties import CLASSES as _p7_property_classes
from .p6_retime_ops import CLASSES as _p6_retime_classes
from .p6_ripple_ops import CLASSES as _p6_ripple_classes
from .p6_range_ops import CLASSES as _p6_range_classes
from .p6_gap_ops import CLASSES as _p6_gap_classes
from .p6_modal_ops import CLASSES as _p6_modal_classes
from .p6_diag_ops import CLASSES as _p6_diag_classes

from .p7_session_ops import CLASSES as _p7_session_classes
from .p7_locator_ops import CLASSES as _p7_locator_classes
from .p7_proxy_ops import CLASSES as _p7_proxy_classes
from .p7_bake_ops import CLASSES as _p7_bake_classes
from .p7_manage_ops import CLASSES as _p7_manage_classes
from .p7_cleanup_ops import CLASSES as _p7_cleanup_classes

from ..core.p8_properties import CLASSES as _p8_property_classes
from .p8_match_ops import CLASSES as _p8_match_classes
from .p8_switch_ops import CLASSES as _p8_switch_classes
from .p8_detect_ops import CLASSES as _p8_detect_classes
from .p8_batch_ops import CLASSES as _p8_batch_classes
from .p8_chain_ops import CLASSES as _p8_chain_classes

from ..core.p9_properties import CLASSES as _p9_property_classes
from .p9_select_ops import CLASSES as _p9_select_classes
from .p9_mirror_ops import CLASSES as _p9_mirror_classes
from .p9_pair_ops import CLASSES as _p9_pair_classes
from .p9_batch_ops import CLASSES as _p9_batch_classes

from ..core.p10_properties import CLASSES as _p10_property_classes
from .p10_shelf_ops import CLASSES as _p10_shelf_classes
from .p10_pie_ops import CLASSES as _p10_pie_classes
from .p10_macro_ops import CLASSES as _p10_macro_classes
from .p10_batch_ops import CLASSES as _p10_batch_classes
from .p10_preset_ops import CLASSES as _p10_preset_classes
from .p10_recovery_ops import CLASSES as _p10_recovery_classes
from .p10_audit_ops import CLASSES as _p10_audit_classes
from .p10_diag_ops import CLASSES as _p10_diag_classes
from .p10_setup_ops import CLASSES as _p10_setup_classes

from ..core.p11_properties import CLASSES as _p11_property_classes
from .p11_layer_ops import CLASSES as _p11_layer_classes
from .p11_assign_ops import CLASSES as _p11_assign_classes
from .p11_blend_ops import CLASSES as _p11_blend_classes

# --- LIPSYNC LAYER (Phase 12) ---
from ..core.p12_properties import CLASSES as _p12_property_classes
from .p12_setup_ops import CLASSES as _p12_setup_classes
from .p12_bake_ops import CLASSES as _p12_bake_classes
from .p12_viseme_ops import CLASSES as _p12_viseme_classes

# --- v12: hybrid PREVIEW/SHIPPED + shape keys ---
from .p12_mode_ops import CLASSES as _p12_mode_classes
from .p12_shape_key_ops import CLASSES as _p12_shape_key_classes

# --- INSTALL/UNINSTALL HYGIENE (v11.1) ---
from .lifecycle_ops import CLASSES as _lifecycle_classes

# --- ANIM ASSIST HOMES ---
from .home_ops import CLASSES as _home_classes

from .nla_ops import CLASSES as _nla_classes
from .driver_ops import CLASSES as _driver_classes

CLASSES: tuple[type, ...] = (
    *_driver_classes,
    *_nla_classes,
    *_timeline_slider_classes,
    *_home_classes,
    *_p3_property_classes,
    *_p4_property_classes,
    AA_OT_export_settings,
    AA_OT_import_settings,
    AA_OT_copy_diagnostics,
    AA_OT_refresh_diagnostics,
    *_keymanager_classes,
    *_anim_offset_classes,
    *_curve_tool_classes,
    *_p2_select_classes,
    *_p2_channel_classes,
    *_p2_keymeta_classes,
    *_p2_diag_classes,
    *_p2_key_classes,
    *_p3_breakdown_classes,
    *_p3_inbetween_classes,
    *_p3_pose_compare_classes,
    *_p3_preset_classes,
    *_p3_modal_classes,
    *_p4_offset_classes,
    *_p4_pushpull_classes,
    *_p4_modal_classes,
    *_p5_property_classes,
    *_p5_overlay_classes,
    *_p5_nav_classes,
    *_p6_property_classes,
    *_p6_retime_classes,
    *_p6_ripple_classes,
    *_p6_range_classes,
    *_p6_gap_classes,
    *_p6_modal_classes,
    *_p6_diag_classes,
    *_p7_property_classes,
    *_p7_session_classes,
    *_p7_locator_classes,
    *_p7_proxy_classes,
    *_p7_bake_classes,
    *_p7_manage_classes,
    *_p7_cleanup_classes,
    *_p8_property_classes,
    *_p8_match_classes,
    *_p8_switch_classes,
    *_p8_detect_classes,
    *_p8_batch_classes,
    *_p8_chain_classes,
    *_p9_property_classes,
    *_p9_select_classes,
    *_p9_mirror_classes,
    *_p9_pair_classes,
    *_p9_batch_classes,
    *_p10_property_classes,
    *_p10_shelf_classes,
    *_p10_pie_classes,
    *_p10_macro_classes,
    *_p10_batch_classes,
    *_p10_preset_classes,
    *_p10_recovery_classes,
    *_p10_audit_classes,
    *_p10_diag_classes,
    *_p10_setup_classes,
    *_p11_property_classes,
    *_p11_layer_classes,
    *_p11_assign_classes,
    *_p11_blend_classes,
    # --- LIPSYNC LAYER (Phase 12) ---
    *_p12_property_classes,
    *_p12_setup_classes,
    *_p12_bake_classes,
    *_p12_viseme_classes,
    # --- v12: hybrid PREVIEW/SHIPPED + shape keys ---
    *_p12_mode_classes,
    *_p12_shape_key_classes,
    # --- INSTALL/UNINSTALL HYGIENE (v11.1) ---
    *_lifecycle_classes,
    *_help_popup_classes,
)
