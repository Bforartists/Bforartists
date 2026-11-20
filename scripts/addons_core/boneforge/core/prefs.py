"""BoneCraft addon-wide user preferences.

Central preferences panel with per-module enable/disable toggles
and shared settings. Each phase module reads its enabled state from
here but never writes to it.
"""

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)

from boneforge import tab_sides as _tab_sides


def _on_language_change(self, context):
    """Force all 3D viewport side panels (Tool Shelf and sidebar) to redraw on language switch."""
    from boneforge.i18n import T  # noqa: trigger cache reset
    import bpy as _bpy
    try:
        for window in _bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type in {'UI', 'TOOLS'}:
                            region.tag_redraw()
    except Exception:
        pass


def _side_changed(key):
    """``update`` for a tab's side setting: move the tab on the next timer tick."""
    def update(self, context):
        from boneforge import tab_sides
        tab_sides.schedule(key)
    return update


def _draw_tabs(layout, prefs):
    """Preferences > Tabs: per tab, its show switch and its side (Left | Right); then the Scene Properties switch."""
    from boneforge import tab_sides
    from boneforge.i18n import T
    box = layout.box()
    box.label(text=T("Tabs"))
    col = box.column(align=True)
    for _key, _category, side_pref, show_pref in tab_sides.TABS:
        row = col.row(align=True)
        row.prop(prefs, show_pref)
        side = row.row(align=True)
        side.active = bool(getattr(prefs, show_pref))      # greyed out while the tab is hidden
        side.prop(prefs, side_pref, expand=True)
    box.separator(factor=1.5)                               # a gap between the tab switches and Scene Properties
    col = box.column(align=True)
    row = col.split(factor=0.325, align=True)               # the bar lines up with the Left | Right bars above
    row.label(text=T("Scene Properties"))                   # starts where the checkboxes start
    row.prop(prefs, "show_scene_tab", text=T("Show"), toggle=True)   # blue while on


def _shelf_width_changed(self, context):
    """``update`` for the Shelf Width settings: every shelf is checked again at once."""
    from boneforge.core import shelf_width
    shelf_width.forget_all()


def _draw_shelf_width(layout, prefs):
    """Preferences > Shelf Width: widen narrow shelves holding these tabs, and how wide (core/shelf_width.py)."""
    from boneforge.i18n import T
    box = layout.box()
    box.label(text=T("Shelf Width"))
    col = box.column(align=True)
    col.prop(prefs, "auto_widen")
    widths = col.row(align=True)
    widths.active = bool(getattr(prefs, "auto_widen", True))
    widths.prop(prefs, "shelf_min_left")
    widths.prop(prefs, "shelf_min_right")


class BoneForgePreferences(bpy.types.AddonPreferences):
    """Global addon preferences for BoneCraft.

    Exposes user-configurable toggles (module enablement, UI options,
    defaults) that persist across Blender sessions. Accessed via
    Edit → Preferences → Add-ons → BoneCraft, and programmatically
    through ``boneforge.core.addon_prefs(context)``.
    """

    bl_idname = "boneforge"

    # ── i18n language selector ───────────────────────────────────
    language: EnumProperty(
        name="Language",
        description="BoneCraft interface language",
        items=[
            ("en", "English",    "English",    0),
            ("ja", "日本語",      "Japanese",   1),
            ("ko", "한국어",      "Korean",     2),
            ("zh", "中文",        "Mandarin",   3),
            ("pt", "Português",  "Portuguese", 4),
            ("es", "Español",    "Spanish",    5),
            ("fr", "Français",   "French",     6),
        ],
        default="en",
        update=_on_language_change,
    )

    # ── v3.3.0 tool registry persistence ────────────────────────
    # CSV of enabled tool ids, written by BF_OT_ToggleTool. Empty/unset
    # means "first run — enable all defaults". Read at register time by
    # boneforge.__init__._load_enabled_set.
    enabled_tools_csv: StringProperty(
        name="Enabled Tools",
        description="Internal: comma-separated list of enabled tool ids",
        default="",
        options={'HIDDEN'},
    )

    # Tools this user has seen; a tool not in it starts as its manifest says
    # (boneforge.tool_startup). Written at register time.
    known_tools_csv: StringProperty(
        name="Known Tools",
        description="Internal: comma-separated list of tool ids this user has seen",
        default="",
        options={'HIDDEN'},
    )

    # ── Legacy module toggles (kept for backward-compat read on first
    # 3.3.0 register; new toggle UI lives below in draw()) ──────

    enable_collection_ui: BoolProperty(
        name="Bone Collection Panel",
        description="Show the bone-collection grouping panel in the 3D viewport sidebar",
        default=True,
    )
    enable_bookmarks: BoolProperty(
        name="Visibility Bookmarks",
        description="Enable saving and restoring bone-collection visibility states",
        default=True,
    )
    enable_hotkey_popup: BoolProperty(
        name="Hotkey Pop-up",
        description="Enable the floating pop-up panel triggered by a viewport hotkey",
        default=True,
    )

    # ── Hotkey popup settings ───────────────────────────────────

    popup_width: IntProperty(
        name="Pop-up Width",
        description="Remembered width of the hotkey pop-up panel in pixels",
        default=300,
        min=200,
        max=600,
    )



    # ── Phase 2 module toggles ─────────────────────────────────

    # v3.0.26: enable_tween removed (Tween Machine was animation-centric).
    enable_pose_library: BoolProperty(
        name="Pose Library",
        description="Enable the visual pose browser with thumbnail previews",
        default=True,
    )
    enable_graph_tools: BoolProperty(
        name="Graph & Viewport Tools",
        description="Enable breakdowner, delta mover, and inline graph editor",
        default=True,
    )
    enable_correctives: BoolProperty(
        name="Corrective Shape Keys",
        description="Enable angle-based corrective shape key authoring",
        default=True,
    )
    enable_rigify_enhance: BoolProperty(
        name="Rigify Auto-Enhancement",
        description="Enable automatic Rigify rig detection and enhancement",
        default=True,
    )

    # ── Phase 2B module toggles ──────────────────────────────────

    enable_shapes: BoolProperty(
        name="Custom Bone Shapes",
        description="Enable the bone shape library and shape generators",
        default=True,
    )
    enable_weight_mirror: BoolProperty(
        name="Weight Mirror",
        description="Enable mesh-relative weight mirroring with KDTree matching",
        default=True,
    )
    enable_weight_transfer: BoolProperty(
        name="Weight Transfer",
        description="Enable cross-mesh weight transfer tools",
        default=True,
    )
    enable_weight_table: BoolProperty(
        name="Weight Table",
        description="Enable tabular vertex weight editing",
        default=True,
    )
    enable_weight_tools: BoolProperty(
        name="Weight Paint Tools",
        description="Enable flood-to-zero, flood-to-one, and custom weight tools",
        default=True,
    )
    enable_deform_control: BoolProperty(
        name="Deform/Control Tagging",
        description="Enable bone deform/control tagging and FBX export helpers",
        default=True,
    )
    enable_delta_mush: BoolProperty(
        name="Delta Mush",
        description="Enable Corrective Smooth modifier wrapper for smooth deformations",
        default=True,
    )
    enable_proximity_wrap: BoolProperty(
        name="Proximity Wrap",
        description="Enable Surface Deform modifier wrapper for mesh binding",
        default=True,
    )

    # ── Phase 2C module toggles ──────────────────────────────────

    enable_space_switch: BoolProperty(
        name="Space Switching",
        description="Enable keyframed parent space switching with Child Of constraints",
        default=True,
    )
    enable_rig_validator: BoolProperty(
        name="Rig Validator",
        description="Enable armature validation checks and custom check registry",
        default=True,
    )
    enable_spline_ik: BoolProperty(
        name="Spline IK Builder",
        description="Enable NURBS-based Spline IK chain creation",
        default=True,
    )
    enable_ribbon: BoolProperty(
        name="Ribbon Builder",
        description="Enable NURBS ribbon surface strip deformation",
        default=True,
    )
    enable_sdk_system: BoolProperty(
        name="Set-Driven Keys",
        description="Enable generalized driver creation and SDK workflow",
        default=True,
    )
    enable_chain_dynamics: BoolProperty(
        name="Chain Dynamics",
        description="Enable Verlet-integration secondary motion on bone chains",
        default=True,
    )
    enable_viseme: BoolProperty(
        name="Viseme System",
        description="Enable viseme shape key management and lip sync generation",
        default=True,
    )
    enable_rig_notes: BoolProperty(
        name="Rig Notes",
        description="Enable rig documentation, viewport overlays, and rig readme",
        default=True,
    )
    enable_game_export: BoolProperty(
        name="Game Export",
        description="Enable game engine export helpers and deform-only baking",
        default=True,
    )

    # ── VRChat phase toggles ──────────────────────────────────

    enable_vrchat: BoolProperty(
        name="CATS",
        description="Enable VRChat avatar assembly, PhysBones, visemes, and export",
        default=True,
    )

    # ── Phase 3 module toggles ─────────────────────────────────

    enable_autorig: BoolProperty(
        name="Auto-Rig Wizard",
        description="Enable the in-viewport auto-rigging wizard",
        default=True,
    )
    enable_retarget: BoolProperty(
        name="Animation Retargeting",
        description="Enable the clip browser and retargeting engine",
        default=True,
    )

    # ── Phase 3 proportion overrides ──────────────────────────

    proportion_shoulder: FloatProperty(
        name="Shoulder Ratio",
        description="Neck base to shoulder as fraction of total arm length",
        default=0.18,
        min=0.05,
        max=0.40,
        precision=3,
    )
    proportion_elbow: FloatProperty(
        name="Elbow Ratio",
        description="Shoulder to elbow as fraction of total arm length",
        default=0.48,
        min=0.30,
        max=0.65,
        precision=3,
    )
    proportion_hip: FloatProperty(
        name="Hip Ratio",
        description="Pelvis center to hip joint as fraction of leg length",
        default=0.10,
        min=0.02,
        max=0.25,
        precision=3,
    )
    proportion_knee: FloatProperty(
        name="Knee Ratio",
        description="Hip to knee as fraction of leg length",
        default=0.52,
        min=0.35,
        max=0.65,
        precision=3,
    )

    # ── Phase 3 clip library ──────────────────────────────────

    clip_library_path: StringProperty(
        name="Clip Library",
        description="Folder containing animation clip files (FBX, BVH, .blend)",
        subtype='DIR_PATH',
        default="",
    )

    # ── Phase 2 settings ───────────────────────────────────────

    smart_bake_tolerance: FloatProperty(
        name="Smart Bake Tolerance",
        description="Maximum deviation from linear interpolation before a keyframe is kept",
        default=0.01,
        min=0.001,
        max=1.0,
        precision=4,
    )

    # ── Viewport tabs: show switch (v7.1.1) and side ───────────
    show_tab_boneforge: BoolProperty(
        name="BoneCraft",
        description="Show the BoneCraft tab in the 3D viewport (its Properties copies always stay)",
        default=True,
    )
    show_tab_cats: BoolProperty(
        name="CATS",
        description="Show the CATS tab in the 3D viewport (Properties > Scene tab shows CATS, VRChat and Import / Export while Scene Properties is on)",
        default=True,
    )
    show_tab_rig_builder: BoolProperty(
        name="Rig Builder",
        description="Show the Rig Builder tab in the 3D viewport (Properties > Scene tab shows Rig Builder while Scene Properties is on)",
        default=True,
    )
    show_scene_tab: BoolProperty(
        name="Scene Properties",
        description="Show BoneCraft's sections (Rig Builder, Mechanisms, CATS, VRChat, Import / Export) in Properties > Scene tab",
        default=True,
    )
    # Side of the 3D viewport for each tab: left Tool Shelf (T) or right sidebar (N). See boneforge/tab_sides.py.
    side_boneforge: EnumProperty(
        name="BoneCraft side", items=_tab_sides.SIDE_ITEMS, default=_tab_sides.DEFAULT_SIDE["boneforge"],
        update=_side_changed("boneforge"),
    )
    side_cats: EnumProperty(
        name="CATS side", items=_tab_sides.SIDE_ITEMS, default=_tab_sides.DEFAULT_SIDE["cats"],
        update=_side_changed("cats"),
    )
    side_rig_builder: EnumProperty(
        name="Rig Builder side", items=_tab_sides.SIDE_ITEMS, default=_tab_sides.DEFAULT_SIDE["rig_builder"],
        update=_side_changed("rig_builder"),
    )
    # Start the shelves holding these tabs wide enough (see boneforge/core/shelf_width.py).
    auto_widen: BoolProperty(
        name="Widen Narrow Shelves",
        description="When a shelf holding a BoneCraft tab is narrower than the width below, widen it once. "
                    "A shelf you drag narrower afterwards stays as you left it",
        default=True, update=_shelf_width_changed,
    )
    shelf_min_left: IntProperty(
        name="Left", description="Minimum width of the left Tool Shelf, in pixels at 1x UI scale",
        default=240, min=100, max=800, update=_shelf_width_changed,
    )
    shelf_min_right: IntProperty(
        name="Right", description="Minimum width of the right sidebar, in pixels at 1x UI scale",
        default=260, min=100, max=800, update=_shelf_width_changed,
    )
    show_helpers: BoolProperty(
        name="Show Helpers",
        description="Show BoneCraft's teaching text: what / when lines, 'How this works' notes "
                    "and full guided-step sentences. VRChat's Compact Mode turns this off",
        default=True,
    )
    rigs_library_owned: StringProperty(
        name="BoneCraft Rigs library owner",
        description="Name of the asset library entry BoneCraft added (removed again when BoneCraft is disabled)",
        default="",
        options={'HIDDEN'},
    )
    def draw(self, context):
        from boneforge.i18n import T
        layout = self.layout

        # Language selector
        lang_box = layout.box()
        lang_box.label(text=T("Language / 言語 / 언어 / 语言"))
        lang_box.prop(self, "language")
        layout.separator(factor=0.5)

        # ── Viewport Tabs: show switch and side ─────────────────
        _draw_tabs(layout, self)
        _draw_shelf_width(layout, self)
        help_box = layout.box()
        help_box.label(text=T("Helpers"), icon='INFO')
        help_box.prop(self, "show_helpers")
        layout.separator(factor=0.5)

        # v3.3.1: Tools list driven by the registry. Two-column split
        # (40% toggle button, 60% description) with checkbox-style
        # icons so the click target and current state are visually
        # obvious. Each click goes through BF_OT_ToggleTool which
        # defers the register/unregister via bpy.app.timers (no crash).
        box = layout.box()
        box.label(text=T("Tools"))
        col = box.column(align=True)
        col.label(
            text=T("Click a tool to toggle it. Disabling removes the tool's classes and panels from this session."),
            icon='INFO',
        )
        col.separator(factor=0.5)

        try:
            from boneforge.core.tool_registry import get_registry
            registry = get_registry()
        except ImportError:
            col.label(
                text=T("Tool registry unavailable."),
                icon='ERROR',
            )
        else:
            tools = sorted(registry.all_tools(), key=lambda m: m.name)
            if not tools:
                col.label(
                    text=T("No tools registered yet — Blender may still be loading."),
                    icon='INFO',
                )
            for manifest in tools:
                enabled = registry.is_enabled(manifest.id)

                # 40 / 60 split — button on the left, description on
                # the right. Keeps buttons visually distinct from
                # full-width labels.
                split = col.split(factor=0.4, align=True)

                op = split.operator(
                    "boneforge.toggle_tool",
                    text=T(manifest.name),
                    icon=("CHECKBOX_HLT" if enabled else "CHECKBOX_DEHLT"),
                    depress=enabled,
                )
                op.tool_id = manifest.id

                desc_row = split.row(align=True)
                desc_row.label(
                    text=T(manifest.description),
                    icon=manifest.icon,
                )

                if manifest.depends_on:
                    dep_split = col.split(factor=0.4, align=True)
                    dep_split.label(text="")
                    dep_split.label(
                        text=f"requires: {', '.join(manifest.depends_on)}",
                    )

                col.separator(factor=0.3)

        # v3.3.1: legacy toggle box removed from UI. The BoolProperty
        # fields (enable_collection_ui etc.) are still defined on this
        # AddonPreferences class so v3.2.x user preferences round-trip
        # without erroring; they just don't render any more. Removal
        # in 3.4.0.

        # v3.3.1: settings boxes below are gated on the registry's
        # enabled state for the corresponding phase. If the phase is
        # disabled, its settings are hidden — there's nothing to
        # configure.
        try:
            from boneforge.core.tool_registry import get_registry
            _registry = get_registry()
            _is_enabled = _registry.is_enabled
        except ImportError:
            _is_enabled = lambda _id: True  # fail open

        # Hotkey popup (ui_panels)
        if _is_enabled("phase1_panels"):
            box = layout.box()
            box.label(text=T("Hotkey Pop-up"))
            box.prop(self, "popup_width")
            box.label(
                text=T("Configure the hotkey in Keymap → 3D View → BoneCraft Rig Panel"),
                icon='INFO',
            )

            box.separator(factor=0.5)

        # v3.2.3: Maintenance — hot-reload, state purge.
        box = layout.box()
        box.label(text=T("Maintenance"))
        col = box.column(align=True)
        col.label(
            text=T("If you re-installed BoneCraft and Blender still shows the old UI, click Reload below."),
            icon='INFO',
        )
        col.label(
            text=T("Reloading purges sys.modules, scrubs Scene props, and deletes __pycache__/ files. No restart needed."),
        )
        row = col.row(align=True)
        row.operator(
            "boneforge.reload_addon",
            text=T("Reload BoneCraft"),
            icon='FILE_REFRESH',
        )
        row.operator(
            "boneforge.purge_state",
            text=T("Purge State"),
            icon='TRASH',
        )


# ── Helper ──────────────────────────────────────────────────────

def addon_prefs(context: bpy.types.Context) -> BoneForgePreferences:
    """Convenience accessor for BoneCraft addon preferences."""
    return context.preferences.addons["boneforge"].preferences


# ── Registration ────────────────────────────────────────────────

classes = (BoneForgePreferences,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
