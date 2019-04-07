'''
BEGIN GPL LICENSE BLOCK

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

END GPL LICENSE BLOCK
'''

bl_info = {
    "name": "Exact Edit",
    "author": "nBurn",
    "version": (0, 2, 0),
    "blender": (2, 77, 0),
    "location": "View3D",
    "description": "Tool for precisely setting distance, scale, and rotation",
    "wiki_url": "https://github.com/n-Burn/Exact_Edit/wiki",
    "category": "Object"
}

if "bpy" in locals():
    import importlib
    importlib.reload(xedit_set_meas)
    importlib.reload(xedit_free_rotate)
else:
    from . import xedit_set_meas
    from . import xedit_free_rotate

import bpy


class XEDIT_PT_ui_pan(bpy.types.Panel):
    # Creates a panel in the 3d view N Panel
    bl_label = 'Exact Edit'
    bl_idname = 'xedit_base_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_context = 'objectmode'
    bl_category = 'Tools'

    def draw(self, context):
        row = self.layout.row(align=True)
        col = row.column()
        col.operator("view3d.xedit_set_meas_op", text="Set Measure", icon="EDIT")
        col.operator("view3d.xedit_free_rotate_op", text="Free Rotate", icon="FORCE_MAGNETIC")


classes = (
    xedit_set_meas.XEDIT_OT_store_meas_btn,
    xedit_set_meas.XEDIT_OT_meas_inp_dlg,
    xedit_set_meas.XEDIT_OT_set_meas,
    xedit_free_rotate.XEDIT_OT_free_rotate,
    XEDIT_PT_ui_pan
)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    #
    '''
    bpy.utils.register_class(xedit_set_meas.XEditStoreMeasBtn)
    bpy.utils.register_class(xedit_set_meas.XEditMeasureInputPanel)
    bpy.utils.register_class(xedit_set_meas.XEditSetMeas)
    bpy.utils.register_class(xedit_free_rotate.XEditFreeRotate)
    bpy.utils.register_class(XEditPanel)
    '''

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    #
    '''
    bpy.utils.unregister_class(xedit_set_meas.XEDIT_OT_store_meas_btn)
    bpy.utils.unregister_class(xedit_set_meas.XEDIT_OT_meas_inp_dlg)
    bpy.utils.unregister_class(xedit_set_meas.XEDIT_OT_set_meas)
    bpy.utils.unregister_class(xedit_free_rotate.XEditFreeRotate)
    bpy.utils.unregister_class(XEDIT_PT_ui_pan)
    '''

if __name__ == "__main__":
    register()
