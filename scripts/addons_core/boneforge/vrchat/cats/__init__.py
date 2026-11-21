"""BoneCraft VRChat Cats Tools — Avatar Utilities.

Registers all Cats-equivalent tool modules. Each module can be independently
disabled from addon preferences without affecting others.

Includes: fix model, bone name translation, zero-weight cleanup, mesh joining,
material atlas combiner, viseme generator, bone tools, armature tools, and mesh tools.
"""

import logging

logger = logging.getLogger(__name__)

_modules = []


def register():
    """Register all Cats tool modules with error handling."""
    import importlib
    from boneforge.vrchat.cats import (
        pipeline,
        validator,
        fix_model,
        translate,
        cleanup,
        join_meshes,
        material_atlas,
        eye_tracking,
        shape_key_tools,
        transform_tools,
        viseme_generator,
        bone_tools,
        armature_tools,
        mesh_tools,
        cats_panel,
    )

    module_list = [
        pipeline,
        # validator is pure-python (no register/unregister), skip it here
        fix_model,
        translate,
        cleanup,
        join_meshes,
        material_atlas,
        eye_tracking,
        shape_key_tools,
        transform_tools,
        viseme_generator,
        bone_tools,
        armature_tools,
        mesh_tools,
        cats_panel,
    ]

    for mod in module_list:
        try:
            importlib.reload(mod)
            mod.register()
            _modules.append(mod)
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to register {mod.__name__}: {e}")


def unregister():
    """Unregister all Cats tool modules in reverse order."""
    for mod in reversed(_modules):
        try:
            mod.unregister()
        except Exception as e:
            logger.error(f"[BoneCraft] Failed to unregister {mod.__name__}: {e}")
    _modules.clear()
