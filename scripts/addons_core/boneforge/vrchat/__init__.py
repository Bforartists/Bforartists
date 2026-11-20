"""BoneCraft VRChat — Avatar Assembly and Publishing Tools.

Registers all VRChat phase submodules: naming, clothing, hair physics,
performance tools, humanoid mapping, visemes, export pipeline, Cats
tools, and the four workspace panels.
Category: VRChat.
"""

import traceback

import bpy
from bpy.types import Panel

from boneforge.core import active_armature
from boneforge.i18n import T
import logging

logger = logging.getLogger(__name__)


# ── Parent Panels ──────────────────────────────────────────────────
# B-01: Parent panel for humanoid, visemes, and other Properties sub-panels

class BONEFORGE_PT_vrc_main(Panel):
    """BoneCraft VRChat main Properties panel."""

    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw_header(self, context):
        self.layout.label(text=T("BoneCraft VRChat"))

    @classmethod
    def poll(cls, context):
        # Hidden (2026-10-08): the full VRChat section now shows in
        # Properties > Scene tab (core/scene_tab_mirror.py). The class stays
        # registered because its sub-panels' draw code is reused there.
        return False

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)
        if arm:
            layout.label(text=f"Armature: {arm.name}")


# B-02: Parent panel for hair sub-panels

class BONEFORGE_PT_vrc_hair(Panel):
    """BoneCraft VRChat hair physics Properties panel."""

    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_hair"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_parent_id = "BONEFORGE_PT_vrc_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.label(text=T("Hair Physics"))

    @classmethod
    def poll(cls, context):
        return False                # hidden with BONEFORGE_PT_vrc_main (see above)

    def draw(self, context):
        layout = self.layout
        layout.label(text=T("Configure hair physics chains and colliders"))


_parent_panels = (
    BONEFORGE_PT_vrc_main,
    BONEFORGE_PT_vrc_hair,
)


# ── Module Registration ────────────────────────────────────────────

_modules = []


def register():
    """Register all VRChat submodules in dependency order."""
    global _modules

    # B-01/B-02: Register parent panels FIRST so child bl_parent_id resolves
    for cls in _parent_panels:
        try:
            bpy.utils.register_class(cls)
        except RuntimeError as e:
            logger.error(f"[BoneCraft] Failed to register {cls.__name__}: {e}")

    # Core systems first (no UI dependencies)
    module_names = (
        'naming',
        'clothing',
        'hair',
        'performance',
        'humanoid',
        'visemes',
        'export',
        'cats',
        'mtoon_preserve',
        # UI panels last (depend on operators from above)
        'spaces',
    )

    for name in module_names:
        try:
            mod = __import__(f'{__package__}.{name}', fromlist=[name])
            mod.register()
            _modules.append(mod)
        except Exception:
            traceback.print_exc()
            logger.error(f"BoneCraft VRChat: failed to register {name}")


def unregister():
    """Unregister all VRChat submodules in reverse order."""
    for mod in reversed(_modules):
        try:
            mod.unregister()
        except Exception:
            traceback.print_exc()
    _modules.clear()

    # Unregister parent panels last
    for cls in reversed(_parent_panels):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as exc:
            logger.debug("./vrchat/__init__.py suppressed RuntimeError: %s", exc)

# ── v3.3.0 Tool Registry ────────────────────────────────────────

def _get_manifest():
    """Return this phase's :class:`ToolManifest`.

    Lazy-imported because the registry module lives under
    ``boneforge.core`` and we want to avoid an eager dependency cycle
    if this phase is imported before ``boneforge.core``.
    """
    from boneforge.core.tool_registry import ToolManifest
    return ToolManifest(
        id='vrchat_avatar',
        name='CATS',
        description='VRChat clothing merge, hair physbones, naming detector, performance optimisation, FBX export.',
        icon='COMMUNITY',
        default_enabled=True,
        register_fn=register,
        unregister_fn=unregister,
    )

