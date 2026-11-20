"""Install/remove Blender drivers for live shape-key viseme evaluation (PREVIEW).

In PREVIEW mode each wired shape key gets a single-property scripted driver
whose expression calls ``aa_p12_viseme_value(scene, viseme_role, link_name)``.
The function looks up the link by name, finds the active cue at the current
time, blends visemes via smoothstep, and returns a 0..1 value for the
requested shape key.

In SHIPPED mode drivers are torn down and the same evaluation is baked into
shape key fcurves (see p12_lipsync_engine.bake_shape_keys).

Driver namespace registration
-----------------------------
The function ``aa_p12_viseme_value`` is registered into
``bpy.app.driver_namespace`` at addon load. After every file open the
namespace is wiped, so we re-register on ``load_post`` via the handler
exposed below.

Driver fragility mitigation
---------------------------
- Function body is fully wrapped in try/except so any error returns 0.0
  (mouth at rest), never crashes the depsgraph.
- Drivers are only installed when both the link and its target mesh exist;
  install_drivers returns 0 silently if either is missing.
- remove_drivers tolerates already-removed drivers.
"""

from __future__ import annotations

from .logging import get_logger

__all__ = [
    "DRIVER_FN_NAME",
    "aa_p12_viseme_value",
    "register_driver_namespace",
    "unregister_driver_namespace",
    "load_post_handler",
    "register_handlers",
    "unregister_handlers",
    "install_drivers_for_link",
    "remove_drivers_for_link",
]

_log = get_logger(__name__)

DRIVER_FN_NAME = "aa_p12_viseme_value"


# ---------------------------------------------------------------------------
# Driver expression target (called by every driver, every frame)
# ---------------------------------------------------------------------------

def aa_p12_viseme_value(time_seconds: float, viseme_role: str, link_layer_name: str) -> float:
    """Driver entry point. Returns blended value 0..1 for shape key at this frame.

    All errors swallowed to 0.0 - drivers must NEVER raise into the depsgraph.
    """
    try:
        import bpy
        from . import p12_cue_table as ct
        scene = bpy.context.scene
        if scene is None:
            return 0.0
        p12 = getattr(scene, "anim_assist_p12", None)
        if p12 is None:
            return 0.0
        for link in p12.layer_links:
            if link.layer_name != link_layer_name:
                continue
            cues = ct.read_cues_from_link(link)
            return ct.viseme_value_at_time(cues, time_seconds, viseme_role)
        return 0.0
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Driver namespace registration (called on register and on load_post)
# ---------------------------------------------------------------------------

def register_driver_namespace() -> None:
    """Make aa_p12_viseme_value callable from driver expressions."""
    try:
        import bpy
        bpy.app.driver_namespace[DRIVER_FN_NAME] = aa_p12_viseme_value
    except Exception:
        _log.exception("Could not register driver namespace entry")


def unregister_driver_namespace() -> None:
    """Remove the driver namespace entry. Safe if absent."""
    try:
        import bpy
        bpy.app.driver_namespace.pop(DRIVER_FN_NAME, None)
    except Exception:
        _log.debug("Could not unregister driver namespace entry", exc_info=True)


# ---------------------------------------------------------------------------
# load_post handler - re-registers the driver namespace after every file open
# ---------------------------------------------------------------------------


def _persistent(fn):  # type: ignore[no-untyped-def]
    """``bpy.app.handlers.persistent`` when available; identity under test stubs.

    Imported lazily: this module only binds ``bpy`` inside functions so it
    stays importable without Blender.
    """
    try:
        import bpy
        deco = bpy.app.handlers.persistent
    except (ImportError, AttributeError):
        return fn
    return deco(fn)


@_persistent  # non-persistent handlers are dropped on file load - fatal for load_post
def load_post_handler(_scene) -> None:
    """Re-install the driver namespace entry. Bound to bpy.app.handlers.load_post."""
    register_driver_namespace()


def register_handlers() -> None:
    """Add load_post_handler to bpy.app.handlers if not already present."""
    try:
        import bpy
        if load_post_handler not in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.append(load_post_handler)
    except Exception:
        _log.exception("Could not register load_post handler")


def unregister_handlers() -> None:
    """Remove load_post_handler from bpy.app.handlers."""
    try:
        import bpy
        if load_post_handler in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(load_post_handler)
    except Exception:
        _log.debug("Could not unregister load_post handler", exc_info=True)


# ---------------------------------------------------------------------------
# Per-link driver install / remove
# ---------------------------------------------------------------------------

def install_drivers_for_link(link, mesh_obj, wiring: dict[str, str]) -> int:
    """Install scripted drivers on every wired shape key. Returns count installed.

    *wiring* is {viseme_name: shape_key_name}. Missing shape keys are silently
    skipped. Existing AA drivers on the same key_blocks are removed first to
    avoid duplicates.
    """
    if mesh_obj is None or wiring is None:
        return 0
    sk = getattr(mesh_obj.data, "shape_keys", None)
    if sk is None:
        return 0
    try:
        import bpy
        fps_num = float(bpy.context.scene.render.fps)
        fps_den = float(max(1, bpy.context.scene.render.fps_base))
        fps = fps_num / fps_den
    except Exception:
        fps = 24.0

    installed = 0
    for viseme_name, key_name in wiring.items():
        if not key_name:
            continue
        kb = sk.key_blocks.get(key_name)
        if kb is None:
            continue
        # Remove any existing driver before installing fresh one.
        try:
            kb.driver_remove("value")
        except RuntimeError:
            pass
        try:
            fcurve = kb.driver_add("value")
        except (RuntimeError, AttributeError):
            continue
        drv = fcurve.driver
        drv.type = "SCRIPTED"
        drv.expression = (
            DRIVER_FN_NAME
            + "(frame / " + str(fps) + ', "'
            + viseme_name + '", "'
            + link.layer_name + '")'
        )
        installed += 1
    return installed


def remove_drivers_for_link(mesh_obj, wiring: dict[str, str]) -> int:
    """Remove drivers on every wired shape key. Returns count removed."""
    if mesh_obj is None or wiring is None:
        return 0
    sk = getattr(mesh_obj.data, "shape_keys", None)
    if sk is None:
        return 0
    removed = 0
    for key_name in wiring.values():
        if not key_name:
            continue
        kb = sk.key_blocks.get(key_name)
        if kb is None:
            continue
        try:
            kb.driver_remove("value")
            removed += 1
        except RuntimeError:
            pass
    return removed
