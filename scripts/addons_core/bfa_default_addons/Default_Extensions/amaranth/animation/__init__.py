from . import frame_current
from . import jump_frames
from . import motion_paths
from . import time_extra_info

def register():
    frame_current.register()
    jump_frames.register()
    motion_paths.register()
    time_extra_info.register()

def unregister():
    time_extra_info.unregister()
    motion_paths.unregister()
    jump_frames.unregister()
    frame_current.unregister()