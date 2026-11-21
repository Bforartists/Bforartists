"""Deprecated stub — animation layers were removed in v3.0.16.

BoneCraft is a rigging extension; NLA-based additive animation layering
is Blender's native responsibility, not BoneCraft's.  This file is kept
as an empty stub so any external code importing
``boneforge.animation.anim_layers`` doesn't raise ImportError during the
transition.  The module is no longer registered by animation/__init__.py.
"""


def register():
    """No-op — anim_layers is deprecated and no longer registered."""


def unregister():
    """No-op — anim_layers is deprecated and no longer registered."""
