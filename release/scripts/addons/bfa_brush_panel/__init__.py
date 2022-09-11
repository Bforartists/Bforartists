bl_info = {
    "name": "Bforartists Brush Panel",
    "author": "Iyad Ahmed (@cgonfire), Draise (@trinumedia)",
    "version": (0, 0, 11),
    "blender": (3, 1, 0),
    "location": "3D View > Tools",
    "description": "Official BFA add-on to display brushes in a top-level panel",
    "category": "Paint",
}

## INFO ##
# This add-on adds top-level brush presets into a new toolshelf tab and brush panels you can collapse, pin or use.
# The panels update depending on how many brush presets you have per brush group.
# The buttons also highlight when activated, and the list updates when you create and remove brushes.
# The iconography also updates to custom icons when they are defined by the user.
# The panel also is responsive with the standard 1,2,3 and text row format defined by Bforartists.
# In use cases, this has already proven a huge time saver when weighting rigs - very intuitive.


import sys

from bpy.utils import register_submodule_factory

submodule_names = [
    "operators",
    "icon_system",
    "weight_paint",
    "vertex_paint",
    "texture_paint",
    "texture_paint_image_editor"
]

register, unregister = register_submodule_factory(__name__, submodule_names)
