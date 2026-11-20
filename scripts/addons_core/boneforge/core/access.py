"""BoneCraft's tools where Bforartists puts its own (UI critique, 2026-10-10).

Bforartists gives each tool a fixed, predictable place, and keeps tools apart from their settings:

- Header menus reach everything. BoneCraft adds its entries to Add > Armature (rig generators),
  Pose and Weights (day-to-day operators) and Object (mechanisms).
- Tool Shelf tabs hold buttons for day-to-day operators. BoneCraft adds a panel to Bforartists' own
  Pose and Weights tabs, drawn the way those tabs draw theirs: operators only, each with an icon,
  text buttons in a wide shelf and an icon grid in a narrow one.
- Settings (how much, which side, what to fit) stay in the BoneCraft sidebar tab.

The panels and menus here hold operators only, never properties, and no header shows an icon.
"""
import bpy
from bpy.types import Menu, Panel

from boneforge.i18n import T

# Day-to-day pose operators: (operator, text, icon, properties)
POSE_ENTRIES = (
    ("boneforge.breakdowner", "Breakdowner", 'BREAKDOWNER_POSE', None),
    ("boneforge.delta_move", "Delta Move", 'TRANSFORM_ORIGINS', None),
    ("boneforge.euler_filter", "Euler Filter", 'GRAPH', None),
    ("boneforge.tangent_set_type", "Auto Clamped Tangents", 'HANDLE_AUTOCLAMPED', {"type": 'AUTO_CLAMPED'}),
    ("boneforge.tangent_set_type", "Vector Tangents", 'HANDLE_VECTOR', {"type": 'VECTOR'}),
    None,
    ("boneforge.picker_popup", "Picker", 'RESTRICT_SELECT_OFF', None),
    ("boneforge.rig_panel_popup", "Bone Collections", 'GROUP_BONE', None),
    ("boneforge.show_all_collections", "Show All Collections", 'HIDE_OFF', None),
    ("boneforge.hide_all_collections", "Hide All Collections", 'HIDE_ON', None),
)

WEIGHT_ENTRIES = (
    ("boneforge.flood_to_zero", "Flood to Zero", 'PAINT_SUBTRACT', None),
    ("boneforge.flood_to_one", "Flood to One", 'PAINT_ADD', None),
    ("boneforge.flood_to_custom", "Flood to Custom", 'FLOODFILL', None),
    None,
    ("boneforge.mirror_active_weight", "Mirror Active Weight", 'WEIGHT_MIRROR', None),
    ("boneforge.normalize_vertex_weights", "Normalize Selected", 'WEIGHT_NORMALIZE', None),
)

# Rig checks: done now and then, so in the menu, not on the shelf
CHECK_ENTRIES = (
    ("boneforge.run_validation", "Validate Rig", 'CHECKMARK', None),
    ("boneforge.open_health_check", "Health Check", 'VIEWZOOM', None),
)


def _exists(idname):
    cat, name = idname.split(".", 1)
    return hasattr(getattr(bpy.ops, cat, None), name)


def _operator(layout, entry, *, icon_only=False):
    idname, text, icon, props = entry
    op = layout.operator(idname, text="" if icon_only else T(text), icon=icon)
    for key, value in (props or {}).items():
        setattr(op, key, value)


def draw_entries(layout, context, entries):
    """Buttons the way Bforartists draws its Tool Shelf tabs: text buttons when wide, an icon grid when narrow."""
    entries = [e for e in entries if e is None or _exists(e[0])]
    columns = 4
    region = getattr(context, "region", None)
    if region is not None and getattr(region, "view2d", None) is not None:
        try:
            from bl_ui.space_toolsystem_common import toolsystem_column_count
            columns = toolsystem_column_count(region)
        except Exception:                                  # noqa: BLE001 - not Bforartists' toolsystem: text buttons
            columns = 4
    col = layout.column(align=True)
    col.scale_y = 2
    if columns == 4:
        for entry in entries:
            if entry is None:
                col.separator(factor=0.5)
            else:
                _operator(col, entry)
        return
    row, used = None, 0
    for entry in entries:
        if entry is None:
            col.separator(factor=0.5)
            row, used = None, 0
            continue
        if row is None or used == columns:
            row, used = col.row(align=True), 0
            row.alignment = 'LEFT'
            row.scale_x = 2
        _operator(row, entry, icon_only=True)
        used += 1


def draw_menu(layout, entries):
    for entry in entries:
        if entry is None:
            layout.separator()
        elif _exists(entry[0]):
            _operator(layout, entry)


# -- Tool Shelf: buttons in Bforartists' own Pose and Weights tabs ------------------------------

class _ShelfPanel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'HIDE_BG'}

    @classmethod
    def poll(cls, context):
        view = getattr(context, "space_data", None)
        return bool(getattr(view, "show_toolshelf_tabs", True))


class BC_PT_shelf_pose(_ShelfPanel):
    bl_idname = "BC_PT_shelf_pose"
    bl_label = "BoneCraft"
    bl_category = "Pose"
    bl_context = "posemode"

    def draw(self, context):
        draw_entries(self.layout, context, POSE_ENTRIES)


class BC_PT_shelf_weights(_ShelfPanel):
    bl_idname = "BC_PT_shelf_weights"
    bl_label = "BoneCraft"
    bl_category = "Weights"
    bl_context = "weightpaint"

    def draw(self, context):
        draw_entries(self.layout, context, WEIGHT_ENTRIES)


# -- Header menus --------------------------------------------------------------------------------

def _quick_rig(layout, scene, op_id, label, icon):
    """A rig to add. Its options (fit, weights, controllers, pose) are tuned after the click."""
    op = layout.operator("boneforge.add_quick_rig", text=label, icon=icon)
    op.rig_op_id = op_id
    op.rig_label = label


class BC_MT_add_quick_rig(Menu):
    """Premade rigs, fitted to the selected mesh. Tune each in Adjust Last Operation after adding it."""
    bl_idname = "BC_MT_add_quick_rig"
    bl_label = "Quick Rig"

    def draw(self, context):
        from boneforge.autorig.quick_human import FALLBACK_OP_ID, discover_rigify_metarigs
        layout, scene = self.layout, context.scene
        layout.operator_context = 'EXEC_REGION_WIN'
        _quick_rig(layout, scene, FALLBACK_OP_ID, "BoneCraft Humanoid", 'ARMATURE_DATA')
        rigs = discover_rigify_metarigs()
        if rigs:
            layout.separator()
        for rig in rigs:
            _quick_rig(layout, scene, rig["op_id"], rig["label"], 'OUTLINER_OB_ARMATURE')


class BC_MT_pose(Menu):
    """BoneCraft's pose operators."""
    bl_idname = "BC_MT_pose"
    bl_label = "BoneCraft"

    def draw(self, context):
        layout = self.layout
        draw_menu(layout, POSE_ENTRIES)
        layout.separator()
        if getattr(bpy.types, "BF_MT_bone_context_menu", None) is not None:
            layout.menu("BF_MT_bone_context_menu", text=T("Rig Setup"), icon='TOOL_SETTINGS')
        layout.separator()
        draw_menu(layout, CHECK_ENTRIES)


class BC_MT_weights(Menu):
    """BoneCraft's weight paint operators."""
    bl_idname = "BC_MT_weights"
    bl_label = "BoneCraft"

    def draw(self, context):
        draw_menu(self.layout, WEIGHT_ENTRIES)


class BC_MT_mechanisms(Menu):
    """Build interlocking, moving parts: add the parts, then joints and links between them."""
    bl_idname = "BC_MT_mechanisms"
    bl_label = "Mechanisms"

    def draw(self, context):
        layout = self.layout
        if _exists("boneforge.mech_add_parts"):
            layout.operator("boneforge.mech_add_parts", text=T("Add Parts from Selection"), icon='ADD')
        for menu, text, icon in (("BC_MT_mech_add_joint", "Add Joint", 'CON_PIVOT'),
                                 ("BC_MT_mech_add_link", "Add Link", 'LINKED')):
            if getattr(bpy.types, menu, None) is not None:
                layout.menu(menu, text=T(text), icon=icon)
        if _exists("boneforge.mech_test"):
            layout.separator()
            layout.operator("boneforge.mech_test", text=T("Test Motion"), icon='PLAY')


def _add_armature(self, context):
    layout = self.layout
    layout.separator()
    layout.menu("BC_MT_add_quick_rig", text=T("Quick Rig"), icon='OUTLINER_OB_ARMATURE')
    layout.operator_context = 'INVOKE_REGION_WIN'
    session = getattr(context.scene, "boneforge_autorig_session", None)
    if session is not None and session.is_active:
        layout.label(text=T("Auto-Rig Wizard: in progress in Rig Builder"), icon='INFO')
    elif _exists("boneforge.autorig_wizard_start"):
        layout.operator("boneforge.autorig_wizard_start", text=T("Auto-Rig Wizard"), icon='OUTLINER_OB_ARMATURE')
    if _exists("boneforge.add_mannequin"):
        layout.operator("boneforge.add_mannequin", text=T("Mannequin for Active Rig"), icon='OUTLINER_OB_MESH')


def _pose(self, context):
    self.layout.separator()
    self.layout.menu("BC_MT_pose", icon='ARMATURE_DATA')


def _weights(self, context):
    self.layout.separator()
    self.layout.menu("BC_MT_weights", icon='MOD_VERTEX_WEIGHT')


def _object(self, context):
    self.layout.separator()
    self.layout.menu("BC_MT_mechanisms", text=T("Mechanisms"), icon='MOD_ARMATURE')


MENUS = (BC_MT_add_quick_rig, BC_MT_pose, BC_MT_weights, BC_MT_mechanisms)
PANELS = (BC_PT_shelf_pose, BC_PT_shelf_weights)
HOOKS = (("VIEW3D_MT_armature_add", _add_armature), ("VIEW3D_MT_pose", _pose),
         ("VIEW3D_MT_paint_weight", _weights), ("VIEW3D_MT_object", _object))


def _drop(host):
    """Take this module's entries off a host menu, also those a reloaded copy of it added."""
    for func in list(getattr(host.draw, "_draw_funcs", ())):
        if getattr(func, "__module__", None) == __name__:
            host.remove(func)


def _unregister_class(idname):
    """Unregister the class registered as ``idname`` if this module (or a reloaded copy) made it."""
    cls = getattr(bpy.types, idname, None)
    if cls is not None and getattr(cls, "__module__", None) == __name__:
        bpy.utils.unregister_class(cls)


def register():
    for cls in MENUS + PANELS:
        _unregister_class(cls.bl_idname)
        bpy.utils.register_class(cls)
    for menu, func in HOOKS:
        host = getattr(bpy.types, menu, None)
        if host is not None:
            _drop(host)                                   # a reload must not add the entries twice
            host.append(func)


def unregister():
    for menu, _func in HOOKS:
        host = getattr(bpy.types, menu, None)
        if host is not None:
            _drop(host)
    for cls in reversed(MENUS + PANELS):
        _unregister_class(cls.bl_idname)
