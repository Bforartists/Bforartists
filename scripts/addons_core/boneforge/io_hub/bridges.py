"""Registry of format bridges known to the IO hub.

Each entry describes one external-addon-backed import/export bridge:
the human-readable name, icon, the function that detects whether the
dep is installed + enabled, the op id of the bridge's auto-installer
(GitHub one-click install), the op id of the manual-prefs fallback,
and the bl_idname of the bridge's main sidebar panel.

The hub iterates this list to render status rows + install buttons,
and the Install All operator iterates it to fire each missing dep's
auto-install in turn.

Adding a new format bridge later: append one dict here, the hub picks
it up automatically on next register.
"""

from __future__ import annotations


# Each dict shape:
#   id              — internal identifier
#   name            — human-readable name shown in the hub
#   icon            — Blender icon name for the status row
#   find_addon_fn   — callable returning truthy if the dep is enabled
#   auto_install_op — bl_idname of the auto-download install operator
#   manual_op       — bl_idname of the open-preferences fallback op
#   website_op      — bl_idname of the open-website operator (optional)
#   panel_id        — bl_idname of the bridge's main sidebar panel
#   docs_url        — a URL describing the format / dep, for the hub UI


def _vrm_finder():
    from boneforge.vrm.bridge import find_vrm_addon
    return find_vrm_addon()


def _mmd_finder():
    from boneforge.mmd.bridge import find_mmd_addon
    return find_mmd_addon()


KNOWN_BRIDGES: list[dict] = [
    {
        "id":              "vrm",
        "name":            "VRM / VRoid",
        "icon":            "WORLD",
        "find_addon_fn":   _vrm_finder,
        "auto_install_op": "boneforge.vrm_install_auto",
        "manual_op":       "boneforge.install_vrm_addon",
        "website_op":      "boneforge.vrm_open_website",
        "panel_id":        "BONEFORGE_PT_vrm",
        "dep_label":       "vrm-addon-for-blender",
    },
    {
        "id":              "mmd",
        "name":            "MMD / PMX",
        "icon":            "OUTLINER_OB_ARMATURE",
        "find_addon_fn":   _mmd_finder,
        "auto_install_op": "boneforge.mmd_install_auto",
        "manual_op":       "boneforge.install_mmd_addon",
        "website_op":      "boneforge.mmd_open_website",
        "panel_id":        "BONEFORGE_PT_mmd",
        "dep_label":       "mmd_tools",
    },
]


def is_bridge_active(bridge_id: str) -> bool:
    """Return True if the bridge's external dep is installed AND enabled."""
    for b in KNOWN_BRIDGES:
        if b["id"] == bridge_id:
            try:
                return b["find_addon_fn"]() is not None
            except Exception:
                return False
    return False


def all_active_ids() -> list[str]:
    """Return the ids of every bridge whose dep is currently active."""
    return [b["id"] for b in KNOWN_BRIDGES
            if is_bridge_active(b["id"])]


def all_inactive_bridges() -> list[dict]:
    """Return the descriptors of every bridge whose dep is missing."""
    return [b for b in KNOWN_BRIDGES if not is_bridge_active(b["id"])]
