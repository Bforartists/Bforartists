"""Show the CATS sidebar tab's sections in Properties > Scene tab too.

The CATS tab's sections (CATS, VRChat, VRChat Tools, Import / Export) are copied
into the Properties editor's Scene tab, which exists whatever is selected,
next to Rig Builder. Each copy shares the original panel's ``draw`` and
``draw_header`` (children keep their own ``poll``), so the sidebar and the
Scene tab always show the same tools. The section roots poll true while
Preferences > Tabs > Scene Properties is on; the CATS preference switch hides
only the sidebar tab.

Same technique as ``core/properties_mirror.py`` (Armature data tab), but
walking each section's tree root-first so nested sub-panels find their
parent's copy. Called from ``boneforge.register`` after every module has
registered its own panels.
"""

import logging

import bpy

logger = logging.getLogger(__name__)

SUFFIX = "_Scene"

# Section root -> order in the Scene tab (Rig Builder is 1; Mechanisms follows it, spec D10).
ROOTS = (
    ("BF_PT_mech", 2),
    ("CATS_PT_main", 3),
    ("BF_PT_sb_vrchat", 4),
    ("BF_PT_cats_vrc_tools", 5),
    ("BF_PT_sb_io", 6),
)

_classes: list = []


def _scene_root(cls, context):
    from boneforge.core.tab_switches import scene_tab_on
    return scene_tab_on(context)


def _permanent(orig_func):
    """A child's own poll, evaluated as if every sidebar tab switch were on."""
    def poll(cls, context):
        from boneforge.core.tab_switches import tabs_on
        return orig_func(cls, tabs_on(context))
    return poll


def _tree(root_id):
    """Root panel and its VIEW_3D descendants, parents before children."""
    panels = [c for c in bpy.types.Panel.__subclasses__()
              if getattr(c, "is_registered", False)
              and getattr(c, "bl_space_type", "") == "VIEW_3D"]
    by_id = {getattr(c, "bl_idname", c.__name__): c for c in panels}
    root = by_id.get(root_id)
    if root is None:
        return []
    ordered, frontier = [root], [root_id]
    while frontier:
        parent = frontier.pop(0)
        for c in panels:
            if getattr(c, "bl_parent_id", "") == parent:
                ordered.append(c)
                frontier.append(c.bl_idname)
    return ordered


def _copy(orig, order=None):
    # The original's own methods first (draw helpers such as _draw_group), then
    # the Scene-tab placement on top.
    attrs = {name: value for name, value in vars(orig).items()
             if not name.startswith("__") and not name.startswith("bl_")
             and (callable(value) or isinstance(value, (staticmethod, classmethod)))}
    attrs.update({
        "bl_idname": orig.bl_idname + SUFFIX,
        "bl_label": getattr(orig, "bl_label", " "),
        "bl_space_type": "PROPERTIES",
        "bl_region_type": "WINDOW",
        "bl_context": "scene",
        "bl_options": set(getattr(orig, "bl_options", set())),
        "draw": orig.draw,
    })
    for hook in ("draw_header", "draw_header_preset"):
        if hasattr(orig, hook):
            attrs[hook] = getattr(orig, hook)
    parent = getattr(orig, "bl_parent_id", "")
    if order is not None:                               # a section root
        attrs["bl_order"] = order
        attrs["bl_options"] |= {"DEFAULT_CLOSED"}
        attrs["poll"] = classmethod(_scene_root)
    else:
        attrs["bl_parent_id"] = parent + SUFFIX
        if hasattr(orig, "bl_order"):
            attrs["bl_order"] = orig.bl_order
        if hasattr(orig, "poll"):
            attrs["poll"] = classmethod(_permanent(orig.poll.__func__))
    return type(orig.__name__ + SUFFIX, (bpy.types.Panel,), attrs)


def register():
    """(Re)build every Scene-tab copy from the panels registered right now.

    Safe to call again: the previous copies are removed first. The tool
    toggle calls it after a tool is switched on or off so the copies follow.
    """
    unregister()
    for root_id, order in ROOTS:
        for orig in _tree(root_id):
            try:
                copy = _copy(orig, order if orig.bl_idname == root_id else None)
                bpy.utils.register_class(copy)
                _classes.append(copy)
            except Exception as exc:                        # one bad panel must not break the add-on
                logger.warning("[BoneCraft] Scene-tab copy of %s failed: %s", orig.__name__, exc)


def unregister():
    for copy in reversed(_classes):
        try:
            bpy.utils.unregister_class(copy)
        except Exception:
            pass
    _classes.clear()
