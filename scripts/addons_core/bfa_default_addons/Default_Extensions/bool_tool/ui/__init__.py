if "bpy" in locals():
    import importlib
    for mod in [icons,
                lists,
                menus,
                panels,
                ]:
        importlib.reload(mod)
else:
    import bpy
    from . import (
        icons,
        lists,
        menus,
        panels,
    )


#### ------------------------------ REGISTRATION ------------------------------ ####

modules = (
    icons,
    lists,
    menus,
    panels,
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
