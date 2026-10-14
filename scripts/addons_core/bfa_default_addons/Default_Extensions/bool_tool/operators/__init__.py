if "bpy" in locals():
    import importlib
    for mod in [boolean,
                canvas,
                cutter,
                select,
                ]:
        importlib.reload(mod)
else:
    import bpy
    from . import (
        boolean,
        canvas,
        cutter,
        select,
    )


#### ------------------------------ REGISTRATION ------------------------------ ####

modules = (
    boolean,
    canvas,
    cutter,
    select,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
