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
# UI Module for Child Addon
# Contains menus, preferences, and UI extensions
# -----------------------------------------------------------------------------

import bpy
import os
from bpy.types import Menu, Operator, Panel

# Import wizard utilities
from .wizard_handlers import detect_wizard_for_object, draw_wizard_button

# Import operations from submodules
from .ops import OBJECT_OT_ApplySelected


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
# Wizard Interface Operator
# -----------------------------------------------------------------------------

class WIZARD_OT_TriggerAssetWizard(Operator):
    """Trigger the appropriate wizard for the selected asset or object"""
    bl_idname = "wizard.trigger_asset_wizard"
    bl_label = "Trigger Asset Wizard"
    bl_description = "Run the appropriate wizard for the selected object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Available when there's an active object"""
        return context.object is not None

    def execute(self, context):
        obj = context.object
        
        # Check for Blend Normals by Proximity modifier
        if obj.modifiers:
            for mod in obj.modifiers:
                if mod.type == 'NODES' and mod.node_group:
                    if "Blend Normals by Proximity" in mod.node_group.name:
                        # Trigger the blend normals wizard
                        bpy.ops.wizard.blend_normals_by_proximity('INVOKE_DEFAULT')
                        self.report({'INFO'}, "Blend Normals wizard triggered")
                        return {'FINISHED'}
        
        # Add more wizard detection here as you implement them
        # Example: if "Another Wizard Asset" in some_property: trigger another wizard
        
        self.report({'INFO'}, "No wizard detected for this object")
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


# -----------------------------------------------------------------------------
# Preferences
# -----------------------------------------------------------------------------

class LIBADDON_APT_child_preferences(bpy.types.AddonPreferences):
    bl_idname = "modular_child_addons"

    def draw(self, context):
        layout = self.layout

        layout.label(
            text="Child Addon - Default Asset Library Functions",
            icon="INFO")

        layout.label(
            text="This is the functional child addon installed by the parent library addon.")
        layout.label(
            text="It provides operators, panels, wizards, and UI extensions.")
        layout.label(
            text="To manage libraries or uninstall, use the parent addon preferences.")

        # Status info
        box = layout.box()
        box.label(text="Addon Status", icon='CHECKBOX_HLT')
        
        # Check if parent addon is active
        # NOTE: Parent addon package name is hardcoded here as this child addon
        # is specifically designed for the bfa_default_library parent addon.
        # For multi-parent support, this would need to be made configurable.
        parent_active = "bfa_default_library" in bpy.context.preferences.addons
        if parent_active:
            box.label(text="Parent Addon: Active", icon='CHECKMARK')
        else:
            box.label(text="Parent Addon: Inactive", icon='X')
        
        # Child addon status is always active since we're in its preferences
        box.label(text="Child Addon: Active", icon='CHECKMARK')


# -----------------------------------------------------------------------------#
# Interface Entries
# -----------------------------------------------------------------------------#

# 3D View - Object - Asset
def wizard_menu_func(self, context):
    """Add wizard trigger to asset menu"""
    layout = self.layout
    obj = context.object

    if context.object:
        # Check if object has any wizard-compatible features
        has_wizard, _, _ = detect_wizard_for_object(obj)

        if has_wizard:
            # WIZARD icon is Bforartists-only, use INFO for Blender
            icon = get_icon("WIZARD", "INFO")
            draw_wizard_button(layout, obj, "Open Asset Wizard", icon, 1.5)

# 3D View - Object - Apply
def apply_join_menu_func(self, context):
    """Add apply operators to apply menu"""
    layout = self.layout

    if context.object:
        layout.separator()
        # JOIN icon is Bforartists-only, use MESH_DATA for Blender
        op = layout.operator("object.apply_selected_objects",
                             text="Visual Geometry and Join",
                             icon=get_icon('JOIN', 'MESH_DATA'))
        op.join_on_apply = True
        op.boolean_on_apply = False
        op.remesh_on_apply = False


def apply_boolean_menu_func(self, context):
    """Add boolean apply operator to apply menu"""
    layout = self.layout

    if context.object:
        op = layout.operator("object.apply_selected_objects",
                             text="Visual Geometry and Boolean",
                             icon='MOD_BOOLEAN')
        op.join_on_apply = False
        op.boolean_on_apply = True
        op.remesh_on_apply = False


def apply_remesh_menu_func(self, context):
    """Add remesh apply operator to apply menu"""
    layout = self.layout

    if context.object:
        op = layout.operator("object.apply_selected_objects",
                             text="Visual Geometry and Remesh",
                             icon='MOD_REMESH')
        op.join_on_apply = False
        op.boolean_on_apply = False
        op.remesh_on_apply = True

# -----------------------------------------------------------------------------#
# Classes
# -----------------------------------------------------------------------------#

classes = (
    WIZARD_OT_TriggerAssetWizard,
    LIBADDON_APT_child_preferences,
)

# -----------------------------------------------------------------------------#
# Register
# -----------------------------------------------------------------------------#

# Track menu registration to prevent duplicates
_menu_registered = False


def register():
    """Register UI classes and append menu functions."""
    global _menu_registered

    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            if "already registered" not in str(e):
                print(f"⚠ Error registering {cls.__name__}: {e}")

    # Add menu functions only once (prevent duplicates from multiple parent addons)
    if not _menu_registered:
        bpy.types.VIEW3D_MT_object_asset.append(wizard_menu_func)
        bpy.types.VIEW3D_MT_object_apply.append(apply_join_menu_func)
        bpy.types.VIEW3D_MT_object_apply.append(apply_boolean_menu_func)
        bpy.types.VIEW3D_MT_object_apply.append(apply_remesh_menu_func)
        _menu_registered = True


def unregister():
    """Unregister UI classes and remove menu functions."""
    global _menu_registered

    # Remove menu functions if registered
    if _menu_registered:
        try:
            bpy.types.VIEW3D_MT_object_asset.remove(wizard_menu_func)
        except ValueError:
            pass
        try:
            bpy.types.VIEW3D_MT_object_apply.remove(apply_join_menu_func)
        except ValueError:
            pass
        try:
            bpy.types.VIEW3D_MT_object_apply.remove(apply_boolean_menu_func)
        except ValueError:
            pass
        try:
            bpy.types.VIEW3D_MT_object_apply.remove(apply_remesh_menu_func)
        except ValueError:
            pass
        _menu_registered = False

    # Unregister classes
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            if "not registered" not in str(e):
                print(f"⚠ Error unregistering {cls.__name__}: {e}")