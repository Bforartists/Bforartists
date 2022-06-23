bl_info = {
    "name": "Bforartists Brush Panel",
    "author": "Iyad Ahmed (@cgonfire), Draise (@trinumedia)",
    "version": (0, 0, 10),
    "blender": (3, 1, 0),
    "location": "3D View > Tools",
    "description": "This is an official Bforartists addon to add top-level brush presets to panels in the toolshelf. Weight Paint mode only (for now)",
    "category": "Weight Paint",
}

## INFO ##
# This version of the addon adds Weight Paint top-level brush presets into a new toolshelf tab and brush panels you can collapse, pin or use.
# The panels update depending on how many brush presets you have per brush group.
# The buttons also highlight when activated, and the list updates when you create and remove brushes.
# The iconography also updates to custom icons when they are defined by the user.
# The panel also is responsive with the standard 1,2,3 and text row format defined by Bforartists.
# In use cases, this has already proven a huge time saver when weighting rigs - very intuitive.

## KNOWN ISSUES ##
# There is a known issue which will require a new patch to Bforartists which is... when making or deleting brushes, the panel will not update till you mouse over it.
# A future patch will intentionally update the panels when you make and
# delete brushes from the property shelf operators. Coming soon.

## TO DO ##
# - add the other paint modes: Grease Pencil Draw Mode, Vertex Paint Mode, Texture Paint Mode and potentially Sculpt Mode
# - Add the 16px built in icons as the defaults for the brushes instead of the larger ones (breaks layout)

## Updates ##
# - removed icons from panel headers

import sys

from bpy.utils import register_submodule_factory

submodule_names = ["operators", "icon_manager", "weight_paint"]


register, _unregister = register_submodule_factory(__name__, submodule_names)


def unregister():
    _unregister()
    # Based on https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040
    for module_name in list(sys.modules.keys()):
        if module_name.startswith(__name__):
            del sys.modules[module_name]
