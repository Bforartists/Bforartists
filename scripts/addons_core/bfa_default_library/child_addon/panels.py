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
    get_geometry_nodes_inputs_grouped,
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
# Collapsible Sub-Panel State
# -----------------------------------------------------------------------------

# Module-level dict that tracks which sub-panels are open/closed.
# Key:  "{modifier.name}::{panel_name}"
# This persists across redraws for the lifetime of the module (session).
_panel_open_state = {}


def _panel_state_key(modifier, panel_name):
    """Return a stable key for a panel's open/closed state."""
    return f"{getattr(modifier, 'name', '?')}::{panel_name}"


def _is_panel_open(modifier, panel_name):
    """Return True if the named sub-panel should be drawn expanded."""
    key = _panel_state_key(modifier, panel_name)
    return _panel_open_state.get(key, True)  # default: open


def _toggle_panel(modifier, panel_name):
    """Toggle the open/closed state of a sub-panel."""
    key = _panel_state_key(modifier, panel_name)
    _panel_open_state[key] = not _panel_open_state.get(key, True)


# -----------------------------------------------------------------------------
# Version-Aware Socket Drawing Helpers
# -----------------------------------------------------------------------------

def _draw_socket_prop(layout, modifier, socket_id, socket_name, socket_type):
    """Draw a socket property, mirroring the modifier-stack style.

    Uses property-split layout so labels appear to the left of the control,
    exactly like native GN modifier properties.
    """
    row = layout.row()
    row.use_property_split = True
    row.use_property_decorate = True

    if bpy.app.version >= (5, 2, 0):
        # Blender 5.2+: socket is an RNA struct — draw its .value property
        try:
            socket_ptr = getattr(modifier.properties.inputs, socket_id)
        except AttributeError:
            # Fallback to dict-style (will fail in 5.2, but safe for older)
            _draw_socket_prop_legacy(row, modifier, socket_id, socket_name, socket_type)
            return
        else:
            if socket_type == 'BOOLEAN':
                # Booleans look better with a simple row (no split needed)
                row = layout.row()
                row.prop(socket_ptr, "value", text=socket_name, toggle=True)
            else:
                row.prop(socket_ptr, "value", text=socket_name)
            return
    else:
        # Blender 5.0-5.1: ID property dict access
        _draw_socket_prop_legacy(row, modifier, socket_id, socket_name, socket_type)


def _draw_socket_prop_legacy(row, modifier, socket_id, socket_name, socket_type):
    """Fallback drawing for Blender 5.0-5.1 (ID-property dict style)."""
    if socket_type == 'BOOLEAN':
        sub = row.row()
        sub.prop(modifier, f'["{socket_id}"]', text=socket_name, toggle=True)
    elif socket_type in ('FLOAT', 'INT'):
        sub = row.row()
        sub.prop(modifier, f'["{socket_id}"]', text=socket_name)
    else:
        sub = row.row()
        sub.prop(modifier, f'["{socket_id}"]', text=socket_name)


# -----------------------------------------------------------------------------
# Sub-Panel Drawing Helper
# -----------------------------------------------------------------------------

def _draw_collapsible_sub_panel(layout, modifier, panel_name, socket_list):
    """Draw a collapsible sub-panel with an arrow toggle, matching modifier stack style.

    Args:
        layout:   Parent UILayout.
        modifier: The GN modifier (used for state key).
        panel_name: Display name / header text.
        socket_list: List of (socket_name, socket_id, socket_type) tuples.
    """
    is_open = _is_panel_open(modifier, panel_name)
    icon = 'DISCLOSURE_TRI_DOWN' if is_open else 'DISCLOSURE_TRI_RIGHT'

    # Collapsible header row
    header = layout.row()
    header.alignment = 'LEFT'
    op = header.operator(
        "object.toggle_gn_subpanel",
        text=panel_name,
        icon=icon,
        emboss=False,
    )
    op.panel_name = panel_name
    op.modifier_name = modifier.name

    if not is_open:
        return  # Collapsed — body is hidden

    # Body: indented box containing the sockets
    body = layout.box()
    body.use_property_split = True
    body.use_property_decorate = True

    for socket_name, socket_id, socket_type in socket_list:
        _draw_socket_prop(body, modifier, socket_id, socket_name, socket_type)


# -----------------------------------------------------------------------------
# Toggle Sub-Panel Operator
# -----------------------------------------------------------------------------

class OBJECT_OT_toggle_gn_subpanel(bpy.types.Operator):
    """Toggle the visibility of a Geometry Nodes sub-panel in the sidebar."""
    bl_idname = "object.toggle_gn_subpanel"
    bl_label = "Toggle GN Sub-Panel"
    bl_description = "Show or hide this property group"
    bl_options = {'INTERNAL'}

    panel_name: bpy.props.StringProperty(name="Panel Name")
    modifier_name: bpy.props.StringProperty(name="Modifier Name")

    def execute(self, context):
        obj = context.object
        if obj:
            mod = obj.modifiers.get(self.modifier_name)
            if mod:
                _toggle_panel(mod, self.panel_name)
        # Force all 3D view areas to redraw
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}


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
        layout.use_property_split = True
        layout.use_property_decorate = False  # we enable per-row where needed

        # Find the first Geometry Nodes modifier that matches our primitive names
        mod = next((m for m in obj.modifiers
                   if m.type == 'NODES' and
                   m.node_group and
                   any(m.node_group.name.startswith(name) for name in GN_ASSET_NAMES)), None)

        if not (mod and mod.node_group):
            return

        # --- Wizard button ---
        icon = "WIZARD" if "OUTLINER_MT_view" in dir(bpy.types) else "EXPERIMENTAL"
        draw_wizard_button(layout, obj, "Open Asset Wizard", icon, 1.5)
        layout.separator()

        # --- Node-group header ---
        layout.label(text=mod.node_group.name, icon='NODETREE')

        # --- Retrieve inputs as nested groups ---
        groups = get_geometry_nodes_inputs_grouped(mod)

        for panel_name, sockets in groups:
            if panel_name is None:
                # Root-level sockets — draw directly
                for socket_name, socket_id, socket_type in sockets:
                    _draw_socket_prop(layout, mod, socket_id, socket_name, socket_type)
            else:
                # Sub-panel with collapsible arrow header
                _draw_collapsible_sub_panel(layout, mod, panel_name, sockets)


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
    OBJECT_OT_toggle_gn_subpanel,
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