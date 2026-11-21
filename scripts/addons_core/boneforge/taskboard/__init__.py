"""BoneCraft Task Board — module root.

Registers all Task Board sub-modules in dependency order:

  1. sidebar       -- hub shell panels (BF_PT_sb_overview,
                      BF_PT_sb_inspect, etc.) MUST register first
                      because panel.py and bone_inspector.py reference
                      these idnames via bl_parent_id.
  2. panel         -- Task Board panels (children of BF_PT_sb_overview)
  3. bone_menu     -- right-click context menu
  4. bone_inspector -- Bone Inspector (child of BF_PT_sb_inspect)
"""

import traceback
import logging

logger = logging.getLogger(__name__)

_modules: list = []


def register():
    global _modules

    # sidebar provides hub shell panels that other modules reference
    # via bl_parent_id -- it MUST load before panel and bone_inspector.
    core_modules = ("sidebar", "panel")

    # Optional modules that may not exist yet (high / medium tier).
    optional_modules = ("bone_menu", "bone_inspector")

    for name in core_modules:
        try:
            mod = __import__(f"{__package__}.{name}", fromlist=[name])
            mod.register()
            _modules.append(mod)
            logger.debug(f"[BoneCraft TaskBoard] registered: {name}")
        except Exception:
            traceback.print_exc()
            logger.error(f"[BoneCraft TaskBoard] Failed to register core module: {name}")

    for name in optional_modules:
        try:
            mod = __import__(f"{__package__}.{name}", fromlist=[name])
            mod.register()
            _modules.append(mod)
            logger.debug(f"[BoneCraft TaskBoard] registered optional: {name}")
        except ImportError:
            pass  # Module not yet created — silently skip.
        except Exception:
            traceback.print_exc()
            logger.warning(f"[BoneCraft TaskBoard] optional module {name} failed to register")


def unregister():
    for mod in reversed(_modules):
        try:
            mod.unregister()
        except Exception:
            traceback.print_exc()
            logger.error(f"[BoneCraft TaskBoard] Failed to unregister {getattr(mod, '__name__', mod)}")
    _modules.clear()

# ── v3.3.0 Tool Registry ────────────────────────────────────────

def _get_manifest():
    """Return this phase's :class:`ToolManifest`.

    Lazy-imported because the registry module lives under
    ``boneforge.core`` and we want to avoid an eager dependency cycle
    if this phase is imported before ``boneforge.core``.
    """
    from boneforge.core.tool_registry import ToolManifest
    return ToolManifest(
        id='taskboard_overview',
        name='Rig Builder',
        description='Overview hub, Task Board, bone inspector, sidebar layout.',
        icon='BOOKMARKS',
        default_enabled=True,
        register_fn=register,
        unregister_fn=unregister,
    )

