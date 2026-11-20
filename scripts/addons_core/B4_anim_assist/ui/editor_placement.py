# --- UI/UX FOUNDATION ---
"""Editor placement constants and Panel mixin base classes.

Defines the four sidebar contexts every Anim Assist panel can dock into
and provides ready-made ``Panel`` mixin base classes that fix
``bl_space_type``, ``bl_region_type``, and ``bl_category`` so any panel can reuse them.

For tools that should appear in more than one editor (e.g. a Key Range
panel useful in both the Dope Sheet and Graph Editor), use
``make_editor_variants`` to clone a base panel into per-editor subclasses
without duplicating ``draw()``.

Editor → domain mapping:

* ``DOPESHEET_EDITOR`` — key timing, ranges, bookmarks, key metadata,
  key editing.
* ``GRAPH_EDITOR`` — curve analysis, interpolation, slope/value tools,
  channel diagnostics.
* ``VIEW_3D`` — viewport overlays, pose tools, manipulators,
  trajectory/motion features.
* ``NLA_EDITOR`` — strip-only / NLA-only tools.

All panels should use these mixins (or call ``make_editor_variants``)
rather than declaring ``bl_space_type`` and ``bl_category`` literals
inline. This guarantees a single source of truth if the category name
ever changes.
"""

from __future__ import annotations

from typing import Iterable

from bpy.types import Panel

from .. import constants


# ---------------------------------------------------------------------------
# Editor space-type constants
# ---------------------------------------------------------------------------

EDITOR_DOPESHEET: str = "DOPESHEET_EDITOR"
EDITOR_GRAPH: str = "GRAPH_EDITOR"
EDITOR_VIEW3D: str = "VIEW_3D"
EDITOR_NLA: str = "NLA_EDITOR"

#: Stable iteration order for the editors the foundation supports.
SUPPORTED_EDITORS: tuple[str, ...] = (
    EDITOR_DOPESHEET,
    EDITOR_GRAPH,
    EDITOR_VIEW3D,
    EDITOR_NLA,
)

#: Human-readable suffix appended to bl_idname clones for cross-editor
#: variants. Order must match ``SUPPORTED_EDITORS``.
EDITOR_SUFFIXES: dict[str, str] = {
    EDITOR_DOPESHEET: "_ds",
    EDITOR_GRAPH: "_ge",
    EDITOR_VIEW3D: "_v3d",
    EDITOR_NLA: "_nla",
}


# ---------------------------------------------------------------------------
# Mixin base classes
# ---------------------------------------------------------------------------

class _SidebarPanelBase(Panel):
    """Common N-panel sidebar settings for every Anim Assist panel."""

    bl_region_type = "UI"
    bl_category = constants.ANIMASSIST_CATEGORY


class DopeSheetSidebarPanel(_SidebarPanelBase):
    """Panel mixin for the Dope Sheet sidebar."""

    bl_space_type = EDITOR_DOPESHEET


class GraphEditorSidebarPanel(_SidebarPanelBase):
    """Panel mixin for the Graph Editor sidebar."""

    bl_space_type = EDITOR_GRAPH


class View3DSidebarPanel(_SidebarPanelBase):
    """Panel mixin for the 3D viewport sidebar."""

    bl_space_type = EDITOR_VIEW3D


class NLASidebarPanel(_SidebarPanelBase):
    """Panel mixin for the NLA editor sidebar."""

    bl_space_type = EDITOR_NLA


#: Lookup table for ``make_editor_variants``.
_EDITOR_BASE_BY_SPACE: dict[str, type[_SidebarPanelBase]] = {
    EDITOR_DOPESHEET: DopeSheetSidebarPanel,
    EDITOR_GRAPH: GraphEditorSidebarPanel,
    EDITOR_VIEW3D: View3DSidebarPanel,
    EDITOR_NLA: NLASidebarPanel,
}


# ---------------------------------------------------------------------------
# Cross-editor cloning helper
# ---------------------------------------------------------------------------

def detached_panel_clone(base_cls: type[Panel], name: str, *, _editor_base=None, **overrides) -> type[Panel]:
    """Copy a panel class into an independent class for another editor.

    Never subclass a registered panel to make an editor variant: registering
    a subclass of a registered ``bpy.types.Panel`` rebinds the parent's RNA
    struct, the parent loses its Python class ("unable to get Python class
    for RNA struct"), and its panel draws empty. Copying the class body and
    reusing the base's own bases keeps both panels independent.
    """
    ns = {k: v for k, v in vars(base_cls).items() if k not in ("__dict__", "__weakref__", "bl_rna")}
    ns.update(overrides)
    bases = base_cls.__bases__
    if _editor_base is not None:
        editor_bases = set(_EDITOR_BASE_BY_SPACE.values())
        bases = tuple(_editor_base if b in editor_bases else b for b in bases)
    return type(name, bases, ns)


def make_editor_variants(
    base_cls: type[Panel],
    editors: Iterable[str],
) -> tuple[type[Panel], ...]:
    """Clone ``base_cls`` into per-editor subclasses with shared ``draw``.

    The base class must already provide a ``draw`` (and any other panel
    methods) and a ``bl_idname``. Each clone reuses the same ``draw`` but
    overrides ``bl_idname`` (suffixed with ``_ds`` / ``_ge`` / etc.) and
    ``bl_space_type`` so Blender treats them as distinct panels.

    Returns the variants in the order they were requested. Any unknown
    editor key is silently skipped (no exception).
    """
    base_idname = getattr(base_cls, "bl_idname", None)
    if not base_idname:
        raise ValueError(
            f"{base_cls.__name__} needs a bl_idname before it can be cloned"
        )

    variants: list[type[Panel]] = []
    for editor in editors:
        editor_base = _EDITOR_BASE_BY_SPACE.get(editor)
        if editor_base is None:
            continue

        # If the base class already lives in this editor, return it
        # unchanged so we don't double-register.
        if getattr(base_cls, "bl_space_type", None) == editor:
            variants.append(base_cls)
            continue

        suffix = EDITOR_SUFFIXES[editor]
        clone_name = f"{base_cls.__name__}{suffix.upper()}"
        clone_idname = f"{base_idname}{suffix}"

        clone = detached_panel_clone(
            base_cls, clone_name,
            bl_idname=clone_idname,
            bl_space_type=editor,
            _editor_base=editor_base,
        )
        variants.append(clone)

    return tuple(variants)


__all__ = [
    "detached_panel_clone",
    "EDITOR_DOPESHEET",
    "EDITOR_GRAPH",
    "EDITOR_VIEW3D",
    "EDITOR_NLA",
    "EDITOR_SUFFIXES",
    "SUPPORTED_EDITORS",
    "DopeSheetSidebarPanel",
    "GraphEditorSidebarPanel",
    "View3DSidebarPanel",
    "NLASidebarPanel",
    "make_editor_variants",
]
