######################################################################################################
# An simple add-on to auto cut in two and mirror an object                                           #
# Actualy partialy uncommented (see further version)                                                 #
# Author: Lapineige, Bookyakuno                                                                                  #
# License: GPL v3                                                                                    #
######################################################################################################
# 2.8 update by Bookyakuno, meta-androcto

bl_info = {
    "name": "Auto Mirror",
    "description": "Super fast cutting and mirroring for mesh",
    "author": "Lapineige",
    "version": (2, 5, 2),
    "blender": (2, 80, 0),
    "location": "View 3D > Sidebar > Tools Tab > AutoMirror (panel)",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/"
                "Py/Scripts/Modeling/AutoMirror",
    "category": "Mesh"}


import bpy
from mathutils import Vector

import bmesh
import bpy
import collections
import mathutils
import math
from bpy_extras import view3d_utils
from bpy.types import (
        Operator,
        Menu,
        Panel,
        AddonPreferences,
        )
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty,
        )


# Operator

class AlignVertices(bpy.types.Operator):

    """ Automatically cut an object along an axis """

    bl_idname = "object.align_vertices"
    bl_label = "Align Vertices on 1 Axis"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH"

    def execute(self, context):
        bpy.ops.object.mode_set(mode = 'OBJECT')

        x1,y1,z1 = bpy.context.scene.cursor.location
        bpy.ops.view3d.snap_cursor_to_selected()

        x2,y2,z2 = bpy.context.scene.cursor.location

        bpy.context.scene.cursor.location[0], \
        bpy.context.scene.cursor.location[1], \
        bpy.context.scene.cursor.location[2]  = 0, 0, 0

        #Vertices coordinate to 0 (local coordinate, so on the origin)
        for vert in bpy.context.object.data.vertices:
            if vert.select:
                if bpy.context.scene.AutoMirror_axis == 'x':
                    axis = 0
                elif bpy.context.scene.AutoMirror_axis == 'y':
                    axis = 1
                elif bpy.context.scene.AutoMirror_axis == 'z':
                    axis = 2
                vert.co[axis] = 0
        #
        bpy.context.scene.cursor.location = x2,y2,z2

        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

        bpy.context.scene.cursor.location = x1,y1,z1

        bpy.ops.object.mode_set(mode = 'EDIT')
        return {'FINISHED'}


class AutoMirror(bpy.types.Operator):
    """ Automatically cut an object along an axis """
    bl_idname = "object.automirror"
    bl_label = "AutoMirror"
    bl_options = {'REGISTER'} # 'UNDO' ?

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH"

    def draw(self, context):
        layout = self.layout
        if bpy.context.object and bpy.context.object.type == 'MESH':
            layout.prop(context.scene, "AutoMirror_axis", text="Mirror axis")
            layout.prop(context.scene, "AutoMirror_orientation", text="Orientation")
            layout.prop(context.scene, "AutoMirror_threshold", text="Threshold")
            layout.prop(context.scene, "AutoMirror_toggle_edit", text="Toggle edit")
            layout.prop(context.scene, "AutoMirror_cut", text="Cut and mirror")
            if bpy.context.scene.AutoMirror_cut:
                layout.prop(context.scene, "AutoMirror_clipping", text="Clipping")
                layout.prop(context.scene, "AutoMirror_apply_mirror", text="Apply mirror")

        else:
            layout.label(icon="ERROR", text="No mesh selected")

    def get_local_axis_vector(self, context, X, Y, Z, orientation):
        loc = context.object.location
        bpy.ops.object.mode_set(mode="OBJECT") # Needed to avoid to translate vertices

        v1 = Vector((loc[0],loc[1],loc[2]))
        bpy.ops.transform.translate(value=(X*orientation, Y*orientation, Z*orientation),
                                        constraint_axis=((X==1), (Y==1), (Z==1)),
                                        orient_type='LOCAL')
        v2 = Vector((loc[0],loc[1],loc[2]))
        bpy.ops.transform.translate(value=(-X*orientation, -Y*orientation, -Z*orientation),
                                        constraint_axis=((X==1), (Y==1), (Z==1)),
                                        orient_type='LOCAL')

        bpy.ops.object.mode_set(mode="EDIT")
        return v2-v1

    def execute(self, context):
        X,Y,Z = 0,0,0
        if bpy.context.scene.AutoMirror_axis == 'x':
            X = 1
        elif bpy.context.scene.AutoMirror_axis == 'y':
            Y = 1
        elif bpy.context.scene.AutoMirror_axis == 'z':
            Z = 1

        current_mode = bpy.context.object.mode # Save the current mode

        if bpy.context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT") # Go to edit mode
        bpy.ops.mesh.select_all(action='SELECT') # Select all the vertices
        if bpy.context.scene.AutoMirror_orientation == 'positive':
            orientation = 1
        else:
            orientation = -1
        cut_normal = self.get_local_axis_vector(context, X, Y, Z, orientation)

        # Cut the mesh
        bpy.ops.mesh.bisect(
                plane_co=(
                bpy.context.object.location[0],
                bpy.context.object.location[1],
                bpy.context.object.location[2]
                ),
                plane_no=cut_normal,
                use_fill= False,
                clear_inner= bpy.context.scene.AutoMirror_cut,
                clear_outer= 0,
                threshold= bpy.context.scene.AutoMirror_threshold) 

        bpy.ops.object.align_vertices() # Use to align the vertices on the origin, needed by the "threshold"

        if not bpy.context.scene.AutoMirror_toggle_edit:
            bpy.ops.object.mode_set(mode=current_mode) # Reload previous mode

        if bpy.context.scene.AutoMirror_cut:
            bpy.ops.object.modifier_add(type='MIRROR') # Add a mirror modifier
            bpy.context.object.modifiers[-1].use_axis[0] = X # Choose the axis to use, based on the cut's axis
            bpy.context.object.modifiers[-1].use_axis[1] = Y
            bpy.context.object.modifiers[-1].use_axis[2] = Z
            bpy.context.object.modifiers[-1].use_clip = context.scene.Use_Matcap
            bpy.context.object.modifiers[-1].show_on_cage = context.scene.AutoMirror_show_on_cage
            if bpy.context.scene.AutoMirror_apply_mirror:
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.modifier_apply(apply_as= 'DATA', modifier= bpy.context.object.modifiers[-1].name)
                if bpy.context.scene.AutoMirror_toggle_edit:
                    bpy.ops.object.mode_set(mode='EDIT')
                else:
                    bpy.ops.object.mode_set(mode=current_mode)

        return {'FINISHED'}


# Panel

class VIEW3D_PT_BisectMirror(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Auto Mirror"
    bl_category = 'Edit'
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        layout = self.layout
        if bpy.context.object and bpy.context.object.type == 'MESH':

            layout.operator("object.automirror")
            layout.prop(context.scene, "AutoMirror_axis", text="Mirror Axis", expand=True)
            layout.prop(context.scene, "AutoMirror_orientation", text="Orientation")
            layout.prop(context.scene, "AutoMirror_threshold", text="Threshold")
            layout.prop(context.scene, "AutoMirror_toggle_edit", text="Toggle Edit")
            layout.prop(context.scene, "AutoMirror_cut", text="Cut and Mirror")
            if bpy.context.scene.AutoMirror_cut:
                layout.prop(context.scene, "Use_Matcap", text="Use Clip")
                layout.prop(context.scene, "AutoMirror_show_on_cage", text="Editable")
                layout.prop(context.scene, "AutoMirror_apply_mirror", text="Apply Mirror")

        else:
            layout.label(icon="ERROR", text="No mesh selected")

# Properties

bpy.types.Scene.AutoMirror_axis = bpy.props.EnumProperty(
    items = [("x", "X", "", 1),("y", "Y", "", 2),("z", "Z", "", 3)],
    description="Axis used by the mirror modifier")

bpy.types.Scene.AutoMirror_orientation = bpy.props.EnumProperty(
    items = [("positive", "Positive", "", 1),("negative", "Negative", "", 2)],
    description="Choose the side along the axis of the editable part (+/- coordinates)")

bpy.types.Scene.AutoMirror_threshold = bpy.props.FloatProperty(
    default= 0.001, min= 0.001,
    description="Vertices closer than this distance are merged on the loopcut")

bpy.types.Scene.AutoMirror_toggle_edit = bpy.props.BoolProperty(
    default= False,
    description="If not in edit mode, change mode to edit")

bpy.types.Scene.AutoMirror_cut = bpy.props.BoolProperty(
    default= True,
    description="If enabeled, cut the mesh in two parts and mirror it. If not, just make a loopcut")

bpy.types.Scene.AutoMirror_clipping = bpy.props.BoolProperty(
    default=True)
bpy.types.Scene.Use_Matcap = bpy.props.BoolProperty(default=True,
description="Use clipping for the mirror modifier")

bpy.types.Scene.AutoMirror_show_on_cage = bpy.props.BoolProperty(
    default=False,
    description="Enable to edit the cage (it's the classical modifier's option)")

bpy.types.Scene.AutoMirror_apply_mirror = bpy.props.BoolProperty(

        description="Apply the mirror modifier (useful to symmetrise the mesh)")


# Add-ons Preferences Update Panel

# Define Panel classes for updating
panels = (
        VIEW3D_PT_BisectMirror,
        )


def update_panel(self, context):
    message = ": Updating Panel locations has failed"
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panels:
            panel.bl_category = context.preferences.addons[__name__].preferences.category
            bpy.utils.register_class(panel)

    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))
        pass


class AutoMirrorAddonPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    category: StringProperty(
            name="Tab Category",
            description="Choose a name for the category of the panel",
            default="Edit",
            update=update_panel
            )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        col = row.column()
        col.label(text="Tab Category:")
        col.prop(self, "category", text="")
            
# define classes for registration
classes = (
    VIEW3D_PT_BisectMirror,
    AutoMirror,
    AlignVertices,
    AutoMirrorAddonPreferences
    )


# registering and menu integration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    update_panel(None, bpy.context)

# unregistering and removing menus
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
