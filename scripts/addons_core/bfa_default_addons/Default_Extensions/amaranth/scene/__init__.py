from . import current_blend
from . import debug
from . import goto_library
from . import material_remove_unassigned
from . import refresh
from . import save_reload
from . import stats

def register():
    current_blend.register()
    refresh.register()
    save_reload.register()
    stats.register()
    debug.register()
    goto_library.register()
    material_remove_unassigned.register()

def unregister():
    material_remove_unassigned.unregister()
    goto_library.unregister()
    debug.unregister()
    stats.unregister()
    save_reload.unregister()
    refresh.unregister()
    current_blend.unregister()
