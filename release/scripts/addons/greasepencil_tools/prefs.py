# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
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

import bpy
import os
from bpy.props import (
        BoolProperty,
        EnumProperty,
        StringProperty,
        PointerProperty,
        FloatProperty,
        # IntProperty,
        )

from .ui_panels import GP_PT_sidebarPanel

def get_addon_prefs():
    import os
    addon_name = os.path.splitext(__name__)[0]
    addon_prefs = bpy.context.preferences.addons[addon_name].preferences
    return (addon_prefs)

from .timeline_scrub import GPTS_timeline_settings, draw_ts_pref

## Addons Preferences Update Panel
def update_panel(self, context):
    try:
        bpy.utils.unregister_class(GP_PT_sidebarPanel)
    except:
        pass
    GP_PT_sidebarPanel.bl_category = get_addon_prefs().category
    bpy.utils.register_class(GP_PT_sidebarPanel)

## keymap binder for rotate canvas
def auto_rebind(self, context):
    unregister_keymaps()
    register_keymaps()

class GreasePencilAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = os.path.splitext(__name__)[0] #'greasepencil-addon' ... __package__ ?
    # bl_idname = __name__

    ts: PointerProperty(type=GPTS_timeline_settings)

    category : StringProperty(
            name="Category",
            description="Choose a name for the category of the panel",
            default="Grease Pencil",
            update=update_panel)

    # --- props
    use_clic_drag : BoolProperty(
        name='Use click drag directly on points',
        description="Change the active tool to 'tweak' during modal, Allow to direct clic-drag points of the box",
        default=True)

    default_deform_type : EnumProperty(
        items=(('KEY_LINEAR', "Linear (perspective mode)", "Linear interpolation, like corner deform / perspective tools of classic 2D", 'IPO_LINEAR',0),
               ('KEY_BSPLINE', "Spline (smooth deform)", "Spline interpolation transformation\nBest when lattice is subdivided", 'IPO_CIRC',1),
               ),
        name='Starting Interpolation', default='KEY_LINEAR', description='Choose default interpolation when entering mode')

    # About interpolation : https://docs.blender.org/manual/en/2.83/animation/shape_keys/shape_keys_panel.html#fig-interpolation-type

    auto_swap_deform_type : BoolProperty(
        name='Auto swap interpolation mode',
        description="Automatically set interpolation to 'spline' when subdividing lattice\n Back to 'linear' when",
        default=True)

    ## rotate canvas variables

    ## Use HUD
    canvas_use_hud: BoolProperty(
        name = "Use Hud",
        description = "Display angle lines and angle value as text on viewport",
        default = False)

    ## Canvas rotate
    canvas_use_shortcut: BoolProperty(
        name = "Use Default Shortcut",
        description = "Use default shortcut: mouse double-click + modifier",
        default = True,
        update=auto_rebind)

    mouse_click : EnumProperty(
        name="Mouse button", description="click on right/left/middle mouse button in combination with a modifier to trigger alignement",
        default='MIDDLEMOUSE',
        items=(
            ('RIGHTMOUSE', 'Right click', 'Use click on Right mouse button', 'MOUSE_RMB', 0),
            ('LEFTMOUSE', 'Left click', 'Use click on Left mouse button', 'MOUSE_LMB', 1),
            ('MIDDLEMOUSE', 'Mid click', 'Use click on Mid mouse button', 'MOUSE_MMB', 2),
            ),
        update=auto_rebind)

    use_shift: BoolProperty(
            name = "combine with shift",
            description = "add shift",
            default = False,
            update=auto_rebind)

    use_alt: BoolProperty(
            name = "combine with alt",
            description = "add alt",
            default = True,
            update=auto_rebind)

    use_ctrl: BoolProperty(
            name = "combine with ctrl",
            description = "add ctrl",
            default = True,
            update=auto_rebind)

    rc_angle_step: FloatProperty(
        name="Angle Steps",
        description="Step the rotation using this angle when using rotate canvas step modifier",
        default=0.2617993877991494, # 15
        min=0.01745329238474369, # 1
        max=3.1415927410125732, # 180
        soft_min=0.01745329238474369, # 1
        soft_max=1.5707963705062866, # 90
        step=10, precision=1, subtype='ANGLE', unit='ROTATION')

    def draw(self, context):
            prefs = get_addon_prefs()
            layout = self.layout
            # layout.use_property_split = True
            row= layout.row(align=True)

            ## TAB CATEGORY
            box = layout.box()
            row = box.row(align=True)
            row.label(text="Panel Category:")
            row.prop(self, "category", text="")

            ## BOX DEFORM
            box = layout.box()
            row = box.row(align=True)
            row.label(text='Box Deform:')
            row.operator("wm.call_menu", text="", icon='QUESTION').name = "GPT_MT_box_deform_doc"
            box.prop(self, "use_clic_drag")

            box.prop(self, "default_deform_type")
            box.label(text="Deformer type can be changed during modal with 'M' key, this is for default behavior", icon='INFO')

            box.prop(self, "auto_swap_deform_type")
            box.label(text="Once 'M' is hit, auto swap is desactivated to stay in your chosen mode", icon='INFO')

            ## ROTATE CANVAS
            box = layout.box()
            box.label(text='Rotate canvas:')

            box.prop(self, "canvas_use_shortcut", text='Bind Shortcuts')

            if self.canvas_use_shortcut:

                row = box.row()
                row.label(text="(Auto rebind when changing shortcut)")#icon=""
                # row.operator("prefs.rebind_shortcut", text='Bind/Rebind shortcuts', icon='FILE_REFRESH')#EVENT_SPACEKEY
                row = box.row(align = True)
                row.prop(self, "use_ctrl", text='Ctrl')#, expand=True
                row.prop(self, "use_alt", text='Alt')#, expand=True
                row.prop(self, "use_shift", text='Shift')#, expand=True
                row.prop(self, "mouse_click",text='')#expand=True

                if not self.use_ctrl and not self.use_alt and not self.use_shift:
                    box.label(text="Choose at least one modifier to combine with click (default: Ctrl+Alt)", icon="ERROR")# INFO

                if not all((self.use_ctrl, self.use_alt, self.use_shift)):
                    row = box.row(align = True)
                    snap_key_list = []
                    if not self.use_ctrl:
                        snap_key_list.append('Ctrl')
                    if not self.use_shift:
                        snap_key_list.append('Shift')
                    if not self.use_alt:
                        snap_key_list.append('Alt')

                    row.label(text=f"Step rotation with: {' or '.join(snap_key_list)}", icon='DRIVER_ROTATIONAL_DIFFERENCE')
                    row.prop(self, "rc_angle_step", text='Angle Steps')


            else:
                box.label(text="No hotkey has been set automatically. Following operators needs to be set manually:", icon="ERROR")
                box.label(text="view3d.rotate_canvas")
            box.prop(self, 'canvas_use_hud')

            ## SCRUB TIMELINE
            box = layout.box()
            draw_ts_pref(prefs.ts, box)



class GPT_MT_box_deform_doc(bpy.types.Menu):
    # bl_idname = "OBJECT_MT_custom_menu"
    bl_label = "Box Deform Infos Sheet"

    def draw(self, context):
        layout = self.layout
        # call another menu
        #layout.operator("wm.call_menu", text="Unwrap").name = "VIEW3D_MT_uv_map"
        #**Behavior from context mode**
        col = layout.column()
        col.label(text='Box Deform Tool')
        col.label(text="Usage:", icon='MOD_LATTICE')
        col.label(text="Use the shortcut 'Ctrl+T' in available modes (listed below)")
        col.label(text="The lattice box is generated facing your view (be sure to face canvas if you want to stay on it)")
        col.label(text="Use shortcuts below to deform (a help will be displayed in the topbar)")

        col.separator()
        col.label(text="Shortcuts:", icon='HAND')
        col.label(text="Spacebar / Enter : Confirm")
        col.label(text="Delete / Backspace / Tab(twice) / Ctrl+T : Cancel")
        col.label(text="M : Toggle between Linear and Spline mode at any moment")
        col.label(text="1-9 top row number : Subdivide the box")
        col.label(text="Ctrl + arrows-keys : Subdivide the box incrementally in individual X/Y axis")

        col.separator()
        col.label(text="Modes and deformation target:", icon='PIVOT_BOUNDBOX')
        col.label(text="- Object mode : The whole GP object is deformed (including all frames)")
        col.label(text="- GPencil Edit mode : Deform Selected points")
        col.label(text="- Gpencil Paint : Deform last Strokes")
        # col.label(text="- Lattice edit : Revive the modal after a ctrl+Z")

        col.separator()
        col.label(text="Notes:", icon='TEXT')
        col.label(text="- If you return in box deform after applying (with a ctrl+Z), you need to hit 'Ctrl+T' again to revive the modal.")
        col.label(text="- A cancel warning will be displayed the first time you hit Tab")

### rotate canvas keymap

addon_keymaps = []
def register_keymaps():
    pref = get_addon_prefs()
    if not pref.canvas_use_shortcut:
        return
    addon = bpy.context.window_manager.keyconfigs.addon

    km = addon.keymaps.new(name = "3D View", space_type = "VIEW_3D")

    if 'view3d.rotate_canvas' not in km.keymap_items:
        km = addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('view3d.rotate_canvas',
        type=pref.mouse_click, value="PRESS", alt=pref.use_alt, ctrl=pref.use_ctrl, shift=pref.use_shift, any=False)

        addon_keymaps.append((km, kmi))

def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


### REGISTER ---

classes = (
    GPTS_timeline_settings,
    GPT_MT_box_deform_doc,
    GreasePencilAddonPrefs,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # Force box deform running to false
    bpy.context.preferences.addons[os.path.splitext(__name__)[0]].preferences.boxdeform_running = False
    register_keymaps()

def unregister():
    unregister_keymaps()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
