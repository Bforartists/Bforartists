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
# Main Operations Module
# This module serves as the central hub for all operations and panels
# -----------------------------------------------------------------------------

import bpy
from bpy.types import Panel

# Import operations from submodules
from .operators.geometry_nodes import (
    get_geometry_nodes_inputs,
    GN_ASSET_NAMES,
)

from .wizard_handlers import (
    WIZARD_HANDLERS,
)

# Import wizard utilities
from .wizard_handlers import draw_wizard_button

# -----------------------------------------------------------------------------
# Icon Compatibility
# -----------------------------------------------------------------------------

def is_bforartists():
    """Check if running in Bforartists (has BFA-specific UI elements)."""
    return "OUTLINER_MT_view" in dir(bpy.types)


def get_icon(bfa_icon, blender_fallback):
    """Get appropriate icon for Bforartists or Blender."""
    return bfa_icon if is_bforartists() else blender_fallback

# -----------------------------------------------------------------------------
# Version-Aware Socket Drawing Helpers
# -----------------------------------------------------------------------------

def _draw_socket_prop(layout, modifier, socket_id, socket_name, socket_type):
    """Draw a socket property, handling version differences.

    Blender 5.0-5.1: ID property dict access modifier['["Socket_3"]'] works for .prop().
    Blender 5.2+:    ID property dict is gone — each socket under
                     modifier.properties.inputs is an RNA struct with a .value
                     property that must be drawn directly.
    """
    row = layout.row()

    if bpy.app.version >= (5, 2, 0):
        # Blender 5.2+: draw the socket's .value property via the RNA pointer
        try:
            socket_ptr = getattr(modifier.properties.inputs, socket_id)
        except AttributeError:
            # Shouldn't happen, but fall back to dict-style (will likely fail)
            data = modifier
            prop = f'["{socket_id}"]'
        else:
            # socket_ptr is an RNA struct like SocketFloat, SocketBool etc.
            # Draw its .value property for editable control.
            _draw_socket_value(row, socket_ptr, socket_name, socket_type)
            return
    else:
        # Blender 5.0-5.1: direct ID property dict access
        data = modifier
        prop = f'["{socket_id}"]'

    # Legacy 5.0-5.1 codepath (or fallback)
    if socket_type == 'BOOLEAN':
        row.prop(data, prop, text=socket_name, toggle=True)
    elif socket_type in ('FLOAT', 'INT'):
        row.label(text=socket_name)
        row.prop(data, prop, text="", slider=False)
    else:
        row.prop(data, prop, text=socket_name)


def _draw_socket_value(row, socket_ptr, socket_name, socket_type):
    """Draw the .value property of a socket RNA struct (Blender 5.2+).

    The socket_ptr is an RNA struct (e.g., NodesSocketFloat) with a 'value'
    property that holds the actual editable data. In the modifier context,
    unconnected inputs store their value in 'value' (not 'default_value').
    """
    # Use split layout for label + control (mimics modifier stack style)
    split = row.split(factor=0.45, align=True)

    if socket_type == 'BOOLEAN':
        # Checkbox: label in left split, toggle in right split
        split.label(text=socket_name)
        split.prop(socket_ptr, "value", text="", toggle=True)
    elif socket_type in ('FLOAT', 'INT'):
        # Numeric: label | value input
        split.label(text=socket_name)
        split.prop(socket_ptr, "value", text="")
    elif socket_type in ('RGBA', 'VECTOR'):
        # Color / Vector: label | value0
        split.label(text=socket_name)
        split.prop(socket_ptr, "value", text="")
    else:
        # STRING, OBJECT, COLLECTION, MATERIAL, IMAGE, TEXTURE, or other:
        # Full-width property
        row.prop(socket_ptr, "value", text=socket_name)


# -----------------------------------------------------------------------------
# Panel Definitions
# -----------------------------------------------------------------------------

class OBJECT_PT_GeometryNodesPanel(Panel):
    """Panel in the sidebar for editing Geometry Nodes Assets properties."""
    bl_idname = "OBJECT_PT_geometry_nodes_panel"
    bl_label = "Asset Properties"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Item"

    show_panel = True  # Controls whether the panel should be shown
    
    @classmethod
    def poll(cls, context):
        """Only show panel for objects with Geometry Nodes modifiers from the asset list."""
        if not cls.show_panel or not context.object or not context.object.modifiers:
            return False
            
        # Check if any modifier is a Geometry Nodes modifier with a node group whose name starts with our smart primitive names
        for mod in context.object.modifiers:
            if (mod.type == 'NODES' and
                mod.node_group and
                any(mod.node_group.name.startswith(name) for name in GN_ASSET_NAMES)):
                return True
        return False

    def draw(self, context):
        layout = self.layout
        obj = context.object

        # Find the first Geometry Nodes modifier that matches our primitive names
        mod = next((m for m in obj.modifiers
                   if m.type == 'NODES' and
                   m.node_group and
                   any(m.node_group.name.startswith(name) for name in GN_ASSET_NAMES)), None)

        if mod and mod.node_group:
            # Add the asset wizard button using centralized utility

            # Check if this is Bforartists
            if "OUTLINER_MT_view" in dir(bpy.types):
                icon = "WIZARD"
            else:
                icon = "EXPERIMENTAL"

            draw_wizard_button(layout, obj, "Open Asset Wizard", icon, 1.5)
            layout.separator()

            # Main panel header

            layout.label(text=f"{mod.node_group.name}", icon='NODETREE')

            # Get and display all inputs
            inputs = get_geometry_nodes_inputs(mod)

            # Track current panel to group sockets together
            current_panel = None
            panel_box = None

            for socket_name, socket_id, socket_type, parent_panel in inputs:
                # If we've moved to a new panel, create a new box
                if parent_panel != current_panel:
                    if panel_box:  # Close previous panel if it exists
                        panel_box.separator()
                    current_panel = parent_panel
                    if current_panel:
                        panel_box = layout.box()
                        panel_box.label(text=current_panel, icon='NODE')

                # If we're in a panel, use the panel_box layout
                target_layout = panel_box if current_panel else layout

                # Version-aware socket drawing (handles Blender 5.0-5.2+)
                _draw_socket_prop(target_layout, mod, socket_id, socket_name, socket_type)


class OBJECT_PT_AssetsModifierPanel(Panel):
    """Creates a custom panel in the Modifier properties for Assets"""
    bl_label = "Asset Operators"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "modifier"
    bl_parent_id = 'DATA_PT_modifiers'

    @classmethod
    def poll(cls, context):
        # Show panel if any Smart Primitive modifier exists in the stack
        if context.object and context.object.modifiers:
            # Check all modifiers in the stack
            for mod in context.object.modifiers:
                if (mod.type == 'NODES' and
                    mod.node_group and
                    any(mod.node_group.name.startswith(name) for name in WIZARD_HANDLERS)):
                    return True
        return False

    def draw(self, context):
        layout = self.layout
        obj = context.object

        # Add the apply button with proper spacing
        # Add the asset wizard button using centralized utility

        # Check if this is Bforartists
        if "OUTLINER_MT_view" in dir(bpy.types):
            icon = "WIZARD"
        else:
            icon = "EXPERIMENTAL"

        draw_wizard_button(layout, obj, "Open Asset Wizard", icon, 1.5)


# -----------------------------------------------------------------------------
# Handler Functions
# -----------------------------------------------------------------------------

def object_added_handler(scene):
    """Activates the panel when an object with Geometry Nodes is added to the scene."""
    for obj in scene.objects:
        if obj not in object_added_handler.known_objects:
            # Only activate panel for our specific primitives
            mod = next((m for m in obj.modifiers
                       if m.type == 'NODES' and
                       m.node_group and
                       any(m.node_group.name.startswith(name) for name in GN_ASSET_NAMES)), None)
            if mod:
                OBJECT_PT_GeometryNodesPanel.show_panel = True
            object_added_handler.known_objects.add(obj)

object_added_handler.known_objects = set()

# -----------------------------------------------------------------------------
# Panel Registration
# -----------------------------------------------------------------------------

classes = (
    OBJECT_PT_GeometryNodesPanel,
    OBJECT_PT_AssetsModifierPanel,
)

def register():
    """Register all panel classes."""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            if "already registered" not in str(e):
                print(f"⚠ Error registering {cls.__name__}: {e}")
    
    # Add handler only if it's not already there
    if object_added_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(object_added_handler)

def unregister():
    """Unregister all panel classes."""
    # Remove handler if it exists
    if object_added_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(object_added_handler)
        
    # Unregister panel classes with robust error handling
    for cls in reversed(classes):
        try:
            # Check if the class has the bl_rna attribute (indicating it's registered)
            if hasattr(cls, 'bl_rna'):
                bpy.utils.unregister_class(cls)
            else:
                # The class doesn't have bl_rna, so it's not registered or already unregistered
                print(f"⚠ Skipping unregistration of {cls.__name__}: not registered (missing bl_rna)")
        except RuntimeError as e:
            if "not registered" not in str(e):
                print(f"⚠ Error unregistering {cls.__name__}: {e}")
        except Exception as e:
            # Handle other potential errors gracefully
            print(f"⚠ Error unregistering {cls.__name__}: {e}")