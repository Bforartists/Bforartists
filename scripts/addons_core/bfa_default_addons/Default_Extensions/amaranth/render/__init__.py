from . import border_camera
from . import meshlight_add
from . import meshlight_select
from . import passepartout
from . import final_resolution
from . import samples_scene

def register():
    border_camera.register()
    meshlight_add.register()
    meshlight_select.register()
    passepartout.register()
    final_resolution.register()
    samples_scene.register()

def unregister():
    samples_scene.unregister()
    final_resolution.unregister()
    passepartout.unregister()
    meshlight_select.unregister()
    meshlight_add.unregister()
    border_camera.unregister()
