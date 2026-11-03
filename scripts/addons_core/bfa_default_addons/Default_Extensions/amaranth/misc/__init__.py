from . import color_management
from . import dupli_group_id
from . import sequencer_extra_info
from . import toggle_wire

def register():
    color_management.register()
    dupli_group_id.register()
    sequencer_extra_info.register()
    toggle_wire.register()

def unregister():
    toggle_wire.unregister()
    sequencer_extra_info.unregister()
    dupli_group_id.unregister()
    color_management.unregister()