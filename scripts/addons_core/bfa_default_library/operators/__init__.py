# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# -----------------------------------------------------------------------------
# Operators Module Initialization
# Central registry for all operator classes
# -----------------------------------------------------------------------------

from .geometry_nodes import (
    OBJECT_OT_InjectNodegroupToCollection,
    OBJECT_OT_MeshBlendbyProximity,
)

from .compositor import (
    COMPOSITOR_OT_ApplyCompositorSetup,
    COMPOSITOR_OT_ResetCompositor
)

from .shader import (
    SHADER_OT_ApplyShaderSetup,
    SHADER_OT_CreateNewMaterial
)

# Combine all operator classes
operator_classes = (
    OBJECT_OT_InjectNodegroupToCollection,
    OBJECT_OT_MeshBlendbyProximity,
    COMPOSITOR_OT_ApplyCompositorSetup,
    COMPOSITOR_OT_ResetCompositor,
    SHADER_OT_ApplyShaderSetup,
    SHADER_OT_CreateNewMaterial,
)

def register():
    """Register all operator classes"""
    from bpy.utils import register_class
    for cls in operator_classes:
        register_class(cls)

def unregister():
    """Unregister all operator classes"""
    from bpy.utils import unregister_class
    for cls in reversed(operator_classes):
        unregister_class(cls)
