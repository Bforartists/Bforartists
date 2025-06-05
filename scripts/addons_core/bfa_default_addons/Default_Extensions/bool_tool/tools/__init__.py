import bpy
from . import (
    carver,
)


#### ------------------------------ REGISTRATION ------------------------------ ####

modules = [
    carver,
]

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
