# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>

import bpy
from bpy.types import Panel
import bmesh

from bpy.app.translations import contexts as i18n_contexts


class toolshelf_calculate( Panel):

    @staticmethod
    def ts_width(layout, region, scale_y):

        # Currently this just checks the width,
        # we could have different layouts as preferences too.
        system = bpy.context.preferences.system
        view2d = region.view2d
        view2d_scale = (
            view2d.region_to_view(1.0, 0.0)[0] -
            view2d.region_to_view(0.0, 0.0)[0]
        )
        width_scale = region.width * view2d_scale / system.ui_scale

        # how many rows. 4 is text buttons.

        if width_scale > 160.0:
            column_count = 4
        elif width_scale > 140.0:
            column_count = 3
        elif width_scale > 90:
            column_count = 2
        else:
            column_count = 1

        return column_count

# ------------------------ Object

class VIEW3D_PT_objecttab_transform(toolshelf_calculate, Panel):
    bl_label = "Transform"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True and context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL', 'EDIT_GPENCIL', 'POSE'}

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y= 1.75)

        obj = context.object

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("transform.tosphere", text="To Sphere", icon = "TOSPHERE")
            col.operator("transform.shear", text="Shear", icon = "SHEAR")
            col.operator("transform.bend", text="Bend", icon = "BEND")
            col.operator("transform.push_pull", text="Push/Pull", icon = 'PUSH_PULL')

            if context.mode in {'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE',
                                'EDIT_LATTICE', 'EDIT_METABALL'}:

                col = layout.column(align=True)
                col.scale_y = 2

                col.operator("transform.vertex_warp", text="Warp", icon = "MOD_WARP")
                col.operator_context = 'EXEC_REGION_WIN'
                col.operator("transform.vertex_random", text="Randomize", icon = 'RANDOMIZE').offset = 0.1
                col.operator_context = 'INVOKE_REGION_WIN'

            if context.mode == 'EDIT_MESH':

                col = layout.column(align=True)
                col.scale_y = 2
                col.operator("transform.shrink_fatten", text="Shrink Fatten", icon = 'SHRINK_FATTEN')
                col.operator("transform.skin_resize", icon = "MOD_SKIN")

            if context.mode == 'EDIT_CURVE':

                col = layout.column(align=True)
                col.scale_y = 2
                col.operator("transform.transform", text="Radius", icon = 'SHRINK_FATTEN').mode = 'CURVE_SHRINKFATTEN'

            if context.active_object is not None and obj.type != 'ARMATURE':

                col = layout.column(align=True)
                col.scale_y = 2
                col.operator("transform.translate", text="Move Texture Space", icon = "MOVE_TEXTURESPACE").texture_space = True
                col.operator("transform.resize", text="Scale Texture Space", icon = "SCALE_TEXTURESPACE").texture_space = True

            elif context.active_object is not None and obj.type == 'ARMATURE' and obj.mode in {'OBJECT'}:

                col = layout.column(align=True)
                col.scale_y = 2
                col.operator("transform.translate", text="Move Texture Space", icon = "MOVE_TEXTURESPACE").texture_space = True
                col.operator("transform.resize", text="Scale Texture Space", icon = "SCALE_TEXTURESPACE").texture_space = True

            if context.mode == 'OBJECT':
                col = layout.column(align=True)
                col.scale_y = 2

                col.operator_context = 'EXEC_REGION_WIN'
                # XXX see alignmenu() in edit.c of b2.4x to get this working
                col.operator("transform.transform", text="Align to Transform Orientation", icon = "ALIGN_TRANSFORM").mode = 'ALIGN'
                col.operator("object.randomize_transform", icon = "RANDOMIZE_TRANSFORM")
                col.operator("object.align", icon = "ALIGN")

            # armature specific extensions follow

            if context.active_object is not None and obj.type == 'ARMATURE' and obj.mode in {'EDIT', 'POSE'}:

                col = layout.column(align=True)
                col.scale_y = 2
                if obj.data.display_type == 'BBONE':
                    col.operator("transform.transform", text="Scale BBone", icon='TRANSFORM_SCALE').mode = 'BONE_SIZE'

                elif obj.data.display_type == 'ENVELOPE':
                    col.operator("transform.transform", text="Scale Envelope Distance", icon='TRANSFORM_SCALE').mode = 'BONE_SIZE'
                    col.operator("transform.transform", text="Scale Radius", icon='TRANSFORM_SCALE').mode = 'BONE_ENVELOPE'

            if context.active_object is not None and context.edit_object and context.edit_object.type == 'ARMATURE':

                col.operator("armature.align", icon = "ALIGN")


        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("transform.tosphere", text="", icon = "TOSPHERE")
                row.operator("transform.shear", text="", icon = "SHEAR")
                row.operator("transform.bend", text="", icon = "BEND")

                row = col.row(align=True)
                row.operator("transform.push_pull", text="", icon = 'PUSH_PULL')

                if context.mode in {'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE',
                                    'EDIT_LATTICE', 'EDIT_METABALL'}:

                    row.operator("transform.vertex_warp", text="", icon = "MOD_WARP")
                    row.operator_context = 'EXEC_REGION_WIN'
                    row.operator("transform.vertex_random", text="", icon = 'RANDOMIZE').offset = 0.1
                    row.operator_context = 'INVOKE_REGION_WIN'

                if context.mode == 'EDIT_MESH':

                    col.separator( factor = 0.5)
                    row = col.row(align=True)
                    row.operator("transform.shrink_fatten", text="", icon = 'SHRINK_FATTEN')
                    row.operator("transform.skin_resize", text="", icon = "MOD_SKIN")

                if context.mode == 'EDIT_CURVE':

                    col.separator( factor = 0.5)
                    row = col.row(align=True)
                    row.operator("transform.transform", text="", icon = 'SHRINK_FATTEN').mode = 'CURVE_SHRINKFATTEN'

                if context.active_object is not None and obj.type != 'ARMATURE':

                    col.separator( factor = 0.5)
                    row = col.row(align=True)
                    row.operator("transform.translate", text="", icon = "MOVE_TEXTURESPACE").texture_space = True
                    row.operator("transform.resize", text="", icon = "SCALE_TEXTURESPACE").texture_space = True

                elif context.active_object is not None and obj.type == 'ARMATURE' and obj.mode in {'OBJECT'}:

                    col.separator( factor = 0.5)

                    row = col.row(align=True)
                    row.operator("transform.translate", text="", icon = "MOVE_TEXTURESPACE").texture_space = True
                    row.operator("transform.resize", text="", icon = "SCALE_TEXTURESPACE").texture_space = True


                if context.mode == 'OBJECT':

                    col.separator( factor = 0.5)

                    row = col.row(align=True)
                    row.operator_context = 'EXEC_REGION_WIN'
                    # XXX see alignmenu() in edit.c of b2.4x to get this working
                    row.operator("transform.transform", text="", icon = "ALIGN_TRANSFORM").mode = 'ALIGN'
                    row.operator("object.randomize_transform", text = "", icon = "RANDOMIZE_TRANSFORM")
                    row.operator("object.align", text = "", icon = "ALIGN")

                if context.active_object is not None and obj.type == 'ARMATURE' and obj.mode in {'EDIT', 'POSE'}:

                    col.separator( factor = 0.5)

                    row = col.row(align=True)
                    if obj.data.display_type == 'BBONE':
                        row.operator("transform.transform", text="", icon='TRANSFORM_SCALE').mode = 'BONE_SIZE'

                    elif obj.data.display_type == 'ENVELOPE':
                        row.operator("transform.transform", text="", icon='TRANSFORM_SCALE').mode = 'BONE_SIZE'
                        row.operator("transform.transform", text="", icon='TRANSFORM_SCALE').mode = 'BONE_ENVELOPE'

                if context.active_object is not None and context.edit_object and context.edit_object.type == 'ARMATURE':

                    row.operator("armature.align", text="", icon = "ALIGN")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("transform.tosphere", text="", icon = "TOSPHERE")
                row.operator("transform.shear", text="", icon = "SHEAR")

                row = col.row(align=True)
                row.operator("transform.bend", text="", icon = "BEND")
                row.operator("transform.push_pull", text="", icon = 'PUSH_PULL')

                if context.mode in {'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE',
                                    'EDIT_LATTICE', 'EDIT_METABALL'}:
                    row = col.row(align=True)
                    row.operator("transform.vertex_warp", text="", icon = "MOD_WARP")
                    row.operator_context = 'EXEC_REGION_WIN'
                    row.operator("transform.vertex_random", text="", icon = 'RANDOMIZE').offset = 0.1
                    row.operator_context = 'INVOKE_REGION_WIN'

                if context.mode == 'EDIT_MESH':

                    col.separator( factor = 0.5)
                    row = col.row(align=True)
                    row.operator("transform.shrink_fatten", text="", icon = 'SHRINK_FATTEN')
                    row.operator("transform.skin_resize", text="", icon = "MOD_SKIN")

                if context.mode == 'EDIT_CURVE':

                    col.separator( factor = 0.5)
                    row = col.row(align=True)
                    row.operator("transform.transform", text="", icon = 'SHRINK_FATTEN').mode = 'CURVE_SHRINKFATTEN'

                if context.active_object is not None and obj.type != 'ARMATURE':

                    col.separator( factor = 0.5)

                    row = col.row(align=True)
                    row.operator("transform.translate", text="", icon = "MOVE_TEXTURESPACE").texture_space = True
                    row.operator("transform.resize", text="", icon = "SCALE_TEXTURESPACE").texture_space = True

                elif context.active_object is not None and obj.type == 'ARMATURE' and obj.mode in {'OBJECT'}:

                    col.separator( factor = 0.5)

                    row = col.row(align=True)
                    row.operator("transform.translate", text="", icon = "MOVE_TEXTURESPACE").texture_space = True
                    row.operator("transform.resize", text="", icon = "SCALE_TEXTURESPACE").texture_space = True

                if context.mode == 'OBJECT':

                    col.separator( factor = 0.5)

                    row = col.row(align=True)
                    row.operator_context = 'EXEC_REGION_WIN'
                    # XXX see alignmenu() in edit.c of b2.4x to get this working
                    row.operator("transform.transform", text="", icon = "ALIGN_TRANSFORM").mode = 'ALIGN'
                    row.operator("object.randomize_transform", text = "", icon = "RANDOMIZE_TRANSFORM")
                    row = col.row(align=True)
                    row.operator("object.align", text = "", icon = "ALIGN")

                if context.active_object is not None and obj.type == 'ARMATURE' and obj.mode in {'EDIT', 'POSE'}:

                    col.separator( factor = 0.5)

                    row = col.row(align=True)
                    if obj.data.display_type == 'BBONE':
                        row.operator("transform.transform", text="", icon='TRANSFORM_SCALE').mode = 'BONE_SIZE'

                    elif obj.data.display_type == 'ENVELOPE':
                        row.operator("transform.transform", text="", icon='TRANSFORM_SCALE').mode = 'BONE_SIZE'
                        row.operator("transform.transform", text="", icon='TRANSFORM_SCALE').mode = 'BONE_ENVELOPE'
                        row = col.row(align=True)

                if context.active_object is not None and context.edit_object and context.edit_object.type == 'ARMATURE':

                    row.operator("armature.align", text="", icon = "ALIGN")

            elif column_count == 1:

                col.operator("transform.tosphere", text="", icon = "TOSPHERE")
                col.operator("transform.shear", text="", icon = "SHEAR")
                col.operator("transform.bend", text="", icon = "BEND")
                col.operator("transform.push_pull", text="", icon = 'PUSH_PULL')

                if context.mode in {'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL'}:
                    col.separator( factor = 0.5)
                    col.operator("transform.vertex_warp", text="", icon = "MOD_WARP")
                    col.operator_context = 'EXEC_REGION_WIN'
                    col.operator("transform.vertex_random", text="", icon = 'RANDOMIZE').offset = 0.1
                    col.operator_context = 'INVOKE_REGION_WIN'

                if context.mode == 'EDIT_MESH':

                    col.separator( factor = 0.5)
                    col.operator("transform.shrink_fatten", text="", icon = 'SHRINK_FATTEN')
                    col.operator("transform.skin_resize", text="", icon = "MOD_SKIN")

                if context.mode == 'EDIT_CURVE':

                    col.separator( factor = 0.5)
                    col.operator("transform.transform", text="", icon = 'SHRINK_FATTEN').mode = 'CURVE_SHRINKFATTEN'

                if context.active_object is not None and obj.type != 'ARMATURE':

                    col.separator( factor = 0.5)
                    col.operator("transform.translate", text="", icon = "MOVE_TEXTURESPACE").texture_space = True
                    col.operator("transform.resize", text="", icon = "SCALE_TEXTURESPACE").texture_space = True

                elif context.active_object is not None and obj.type == 'ARMATURE' and obj.mode in {'OBJECT'}:

                    col.separator( factor = 0.5)
                    col.operator("transform.translate", text="", icon = "MOVE_TEXTURESPACE").texture_space = True
                    col.operator("transform.resize", text="", icon = "SCALE_TEXTURESPACE").texture_space = True

                if context.mode == 'OBJECT':

                    col.separator( factor = 0.5)
                    col.operator_context = 'EXEC_REGION_WIN'
                    # XXX see alignmenu() in edit.c of b2.4x to get this working
                    col.operator("transform.transform", text="", icon = "ALIGN_TRANSFORM").mode = 'ALIGN'
                    col.operator("object.randomize_transform", text = "", icon = "RANDOMIZE_TRANSFORM")
                    col.operator("object.align", text = "", icon = "ALIGN")

                if context.active_object is not None and obj.type == 'ARMATURE' and obj.mode in {'EDIT', 'POSE'}:

                    col.separator( factor = 0.5)

                    if obj.data.display_type == 'BBONE':
                        col.operator("transform.transform", text="", icon='TRANSFORM_SCALE').mode = 'BONE_SIZE'

                    elif obj.data.display_type == 'ENVELOPE':
                        col.operator("transform.transform", text="", icon='TRANSFORM_SCALE').mode = 'BONE_SIZE'
                        col.operator("transform.transform", text="", icon='TRANSFORM_SCALE').mode = 'BONE_ENVELOPE'

                if context.active_object is not None and context.edit_object and context.edit_object.type == 'ARMATURE':

                    col.operator("armature.align", text="", icon = "ALIGN")


class VIEW3D_PT_objecttab_set_origin(toolshelf_calculate, Panel):
    bl_label = "Set Origin"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"
    bl_context = "objectmode"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("object.origin_set", text = "Geometry to Origin", icon ='GEOMETRY_TO_ORIGIN').type='GEOMETRY_ORIGIN'
            col.operator("object.origin_set", text = "Origin to Geometry", icon ='ORIGIN_TO_GEOMETRY').type='ORIGIN_GEOMETRY'
            col.operator("object.origin_set", text = "Origin to 3D Cursor", icon ='ORIGIN_TO_CURSOR').type='ORIGIN_CURSOR'
            col.operator("object.origin_set", text = "Origin to Center of Mass (Surface)", icon ='ORIGIN_TO_CENTEROFMASS').type='ORIGIN_CENTER_OF_MASS'
            col.operator("object.origin_set", text = "Origin to Center of Mass (Volume)", icon ='ORIGIN_TO_VOLUME').type='ORIGIN_CENTER_OF_VOLUME'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("object.origin_set", text = "", icon ='GEOMETRY_TO_ORIGIN').type='GEOMETRY_ORIGIN'
                row.operator("object.origin_set", text = "", icon ='ORIGIN_TO_GEOMETRY').type='ORIGIN_GEOMETRY'
                row.operator("object.origin_set", text = "", icon ='ORIGIN_TO_CURSOR').type='ORIGIN_CURSOR'
                row = col.row(align=True)
                row.operator("object.origin_set", text = "", icon ='ORIGIN_TO_CENTEROFMASS').type='ORIGIN_CENTER_OF_MASS'
                row.operator("object.origin_set", text = "", icon ='ORIGIN_TO_VOLUME').type='ORIGIN_CENTER_OF_VOLUME'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("object.origin_set", text = "", icon ='GEOMETRY_TO_ORIGIN').type='GEOMETRY_ORIGIN'
                row.operator("object.origin_set", text = "", icon ='ORIGIN_TO_GEOMETRY').type='ORIGIN_GEOMETRY'
                row = col.row(align=True)
                row.operator("object.origin_set", text = "", icon ='ORIGIN_TO_CURSOR').type='ORIGIN_CURSOR'
                row.operator("object.origin_set", text = "", icon ='ORIGIN_TO_CENTEROFMASS').type='ORIGIN_CENTER_OF_MASS'
                row = col.row(align=True)
                row.operator("object.origin_set", text = "", icon ='ORIGIN_TO_VOLUME').type='ORIGIN_CENTER_OF_VOLUME'

            elif column_count == 1:

                col.operator("object.origin_set", text = "", icon ='GEOMETRY_TO_ORIGIN').type='GEOMETRY_ORIGIN'
                col.operator("object.origin_set", text = "", icon ='ORIGIN_TO_GEOMETRY').type='ORIGIN_GEOMETRY'
                col.operator("object.origin_set", text = "", icon ='ORIGIN_TO_CURSOR').type='ORIGIN_CURSOR'
                col.operator("object.origin_set", text = "", icon ='ORIGIN_TO_CENTEROFMASS').type='ORIGIN_CENTER_OF_MASS'
                col.operator("object.origin_set", text = "", icon ='ORIGIN_TO_VOLUME').type='ORIGIN_CENTER_OF_VOLUME'


# Workaround to separate the tooltips
class VIEW3D_MT_object_mirror_global_x(bpy.types.Operator):
    """Mirror global around X axis"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mirror.global_x"        # unique identifier for buttons and menu items to reference.
    bl_label = "Mirror Global X"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.transform.mirror(orient_type='GLOBAL', constraint_axis=(True, False, False))
        return {'FINISHED'}


# Workaround to separate the tooltips
class VIEW3D_MT_object_mirror_global_y(bpy.types.Operator):
    """Mirror global around X axis"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mirror.global_y"        # unique identifier for buttons and menu items to reference.
    bl_label = "Mirror Global X"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.transform.mirror(orient_type='GLOBAL', constraint_axis=(False, True, False))
        return {'FINISHED'}


# Workaround to separate the tooltips
class VIEW3D_MT_object_mirror_global_z(bpy.types.Operator):
    """Mirror global around Z axis"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mirror.global_z"        # unique identifier for buttons and menu items to reference.
    bl_label = "Mirror Global Z"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.transform.mirror(orient_type='GLOBAL', constraint_axis=(False, False, True))
        return {'FINISHED'}


class VIEW3D_PT_objecttab_mirror(toolshelf_calculate, Panel):
    bl_label = "Mirror"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True and context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL', 'EDIT_GPENCIL'}

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("transform.mirror", text="Interactive Mirror", icon='TRANSFORM_MIRROR')

            col.operator_context = 'EXEC_REGION_WIN'
            col.operator("mirror.global_x", text="X Global", icon='MIRROR_X')
            col.operator("mirror.global_y", text="Y Global", icon='MIRROR_Y')
            col.operator("mirror.global_z", text="Z Global", icon='MIRROR_Z')

            if _context.edit_object and _context.edit_object.type in {'MESH', 'SURFACE'}:
                col.operator("object.vertex_group_mirror", icon = "MIRROR_VERTEXGROUP")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("transform.mirror", text="", icon='TRANSFORM_MIRROR')

                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("mirror.global_x", text="", icon='MIRROR_X')
                row.operator("mirror.global_y", text="", icon='MIRROR_Y')

                row = col.row(align=True)
                row.operator("mirror.global_z", text="", icon='MIRROR_Z')

                if _context.edit_object and _context.edit_object.type in {'MESH', 'SURFACE'}:
                    row.operator("object.vertex_group_mirror", text="", icon = "MIRROR_VERTEXGROUP")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("transform.mirror", text="", icon='TRANSFORM_MIRROR')

                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("mirror.global_x", text="", icon='MIRROR_X')

                row = col.row(align=True)
                row.operator("mirror.global_y", text="", icon='MIRROR_Y')
                row.operator("mirror.global_z", text="", icon='MIRROR_Z')

                if _context.edit_object and _context.edit_object.type in {'MESH', 'SURFACE'}:
                    row = col.row(align=True)
                    row.operator("object.vertex_group_mirror", text="", icon = "MIRROR_VERTEXGROUP")

            elif column_count == 1:

                col.operator("transform.mirror", text="", icon='TRANSFORM_MIRROR')

                col.operator_context = 'EXEC_REGION_WIN'
                col.operator("mirror.global_x", text="", icon='MIRROR_X')
                col.operator("mirror.global_y", text="", icon='MIRROR_Y')
                col.operator("mirror.global_z", text="", icon='MIRROR_Z')

                if _context.edit_object and _context.edit_object.type in {'MESH', 'SURFACE'}:
                    col.operator("object.vertex_group_mirror", text="", icon = "MIRROR_VERTEXGROUP")


# Workaround to separate the tooltips
class VIEW3D_MT_object_mirror_local_x(bpy.types.Operator):
    """Mirror local around X axis"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mirror.local_x"        # unique identifier for buttons and menu items to reference.
    bl_label = "Mirror Local X"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.transform.mirror(orient_type='LOCAL', constraint_axis=(True, False, False))
        return {'FINISHED'}


# Workaround to separate the tooltips
class VIEW3D_MT_object_mirror_local_y(bpy.types.Operator):
    """Mirror local around X axis"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mirror.local_y"        # unique identifier for buttons and menu items to reference.
    bl_label = "Mirror Local X"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.transform.mirror(orient_type='LOCAL', constraint_axis=(False, True, False))
        return {'FINISHED'}


# Workaround to separate the tooltips
class VIEW3D_MT_object_mirror_local_z(bpy.types.Operator):
    """Mirror local around Z axis"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mirror.local_z"        # unique identifier for buttons and menu items to reference.
    bl_label = "Mirror Local Z"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.transform.mirror(orient_type='LOCAL', constraint_axis=(False, False, True))
        return {'FINISHED'}


class VIEW3D_PT_objecttab_mirror_local(toolshelf_calculate, Panel):
    bl_label = "Mirror Local"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True and context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL', 'EDIT_GPENCIL'}

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator_context = 'EXEC_REGION_WIN'
            col.operator("mirror.local_x", text="X Local", icon='MIRROR_X')
            col.operator("mirror.local_y", text="Y Local", icon='MIRROR_Y')
            col.operator("mirror.local_z", text="Z Local", icon='MIRROR_Z')

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("mirror.local_x", text="", icon='MIRROR_X')
                row.operator("mirror.local_y", text="", icon='MIRROR_Y')
                row.operator("mirror.local_z", text="", icon='MIRROR_Z')

            elif column_count == 2:
                row = col.row(align=True)
                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("mirror.local_x", text="", icon='MIRROR_X')
                row.operator("mirror.local_y", text="", icon='MIRROR_Y')

                row = col.row(align=True)
                row.operator("mirror.local_z", text="", icon='MIRROR_Z')

            elif column_count == 1:

                col.operator_context = 'EXEC_REGION_WIN'
                col.operator("mirror.local_x", text="", icon='MIRROR_X')
                col.operator("mirror.local_y", text="", icon='MIRROR_Y')
                col.operator("mirror.local_z", text="", icon='MIRROR_Z')


class VIEW3D_PT_objecttab_clear(toolshelf_calculate, Panel):
    bl_label = "Clear"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"
    bl_context = "objectmode"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("object.location_clear", text="Location", icon = "CLEARMOVE").clear_delta = False
            col.operator("object.rotation_clear", text="Rotation", icon = "CLEARROTATE").clear_delta = False
            col.operator("object.scale_clear", text="Scale", icon = "CLEARSCALE").clear_delta = False

            col.separator(factor = 0.5)

            col.operator("object.origin_clear", text="Origin", icon = "CLEARORIGIN")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("object.location_clear", text="", icon = "CLEARMOVE").clear_delta = False
                row.operator("object.rotation_clear", text="", icon = "CLEARROTATE").clear_delta = False
                row.operator("object.scale_clear", text="", icon = "CLEARSCALE").clear_delta = False

                row = col.row(align=True)
                row.operator("object.origin_clear", text="", icon = "CLEARORIGIN")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("object.location_clear", text="", icon = "CLEARMOVE").clear_delta = False
                row.operator("object.rotation_clear", text="", icon = "CLEARROTATE").clear_delta = False

                row = col.row(align=True)
                row.operator("object.scale_clear", text="", icon = "CLEARSCALE").clear_delta = False
                row.operator("object.origin_clear", text="", icon = "CLEARORIGIN")

            elif column_count == 1:

                col.operator("object.location_clear", text="", icon = "CLEARMOVE").clear_delta = False
                col.operator("object.rotation_clear", text="", icon = "CLEARROTATE").clear_delta = False
                col.operator("object.scale_clear", text="", icon = "CLEARSCALE").clear_delta = False

                col.separator(factor = 0.5)

                col.operator("object.origin_clear", text="", icon = "CLEARORIGIN")


class VIEW3D_PT_objecttab_apply(toolshelf_calculate, Panel):
    bl_label = "Apply"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"
    bl_context = "objectmode"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2


            #bfa - separated tooltips. classes are in space_toolbar.py
            col.operator("view3d.tb_apply_location", text="Location", icon = "APPLYMOVE")
            col.operator("view3d.tb_apply_rotate", text="Rotation", icon = "APPLYROTATE")
            col.operator("view3d.tb_apply_scale", text="Scale", icon = "APPLYSCALE")
            col.operator("view3d.tb_apply_all", text="All Transforms", icon = "APPLYALL")
            col.operator("view3d.tb_apply_rotscale", text="Rotation & Scale", icon = "APPLY_ROTSCALE")

            col.separator(factor = 0.5)

            col.operator("object.visual_transform_apply", text="Visual Transform", text_ctxt=i18n_contexts.default, icon = "VISUALTRANSFORM")
            col.operator("object.duplicates_make_real", icon = "MAKEDUPLIREAL")
            col.operator("object.parent_inverse_apply", text="Parent Inverse", text_ctxt=i18n_contexts.default, icon = "APPLY_PARENT_INVERSE")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("view3d.tb_apply_location", text="", icon = "APPLYMOVE")
                row.operator("view3d.tb_apply_rotate", text="", icon = "APPLYROTATE")
                row.operator("view3d.tb_apply_scale", text="", icon = "APPLYSCALE")

                row = col.row(align=True)
                row.operator("view3d.tb_apply_all", text="", icon = "APPLYALL")
                row.operator("view3d.tb_apply_rotscale", text="", icon = "APPLY_ROTSCALE")

                row = col.row(align=True)
                row.operator("object.visual_transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "VISUALTRANSFORM")
                row.operator("object.duplicates_make_real", text="", icon = "MAKEDUPLIREAL")
                row.operator("object.parent_inverse_apply", text="", icon = "APPLY_PARENT_INVERSE")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("view3d.tb_apply_location", text="", icon = "APPLYMOVE")
                row.operator("view3d.tb_apply_rotate", text="", icon = "APPLYROTATE")

                row = col.row(align=True)
                row.operator("view3d.tb_apply_scale", text="", icon = "APPLYSCALE")
                row.operator("view3d.tb_apply_all", text="", icon = "APPLYALL")

                row = col.row(align=True)
                row.operator("view3d.tb_apply_rotscale", text="", icon = "APPLY_ROTSCALE")

                row = col.row(align=True)
                row.operator("object.visual_transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "VISUALTRANSFORM")
                row.operator("object.duplicates_make_real", text="", icon = "MAKEDUPLIREAL")

                row = col.row(align=True)
                row.operator("object.parent_inverse_apply", text="", icon = "APPLY_PARENT_INVERSE")

            elif column_count == 1:

                col.operator("view3d.tb_apply_location", text="", icon = "APPLYMOVE")
                col.operator("view3d.tb_apply_rotate", text="", icon = "APPLYROTATE")
                col.operator("view3d.tb_apply_scale", text="", icon = "APPLYSCALE")
                col.operator("view3d.tb_apply_all", text="", icon = "APPLYALL")
                col.operator("view3d.tb_apply_rotscale", text="", icon = "APPLY_ROTSCALE")

                col.separator(factor = 0.5)

                col.operator("object.visual_transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "VISUALTRANSFORM")
                col.operator("object.duplicates_make_real", text="", icon = "MAKEDUPLIREAL")
                col.operator("object.parent_inverse_apply", text="", icon = "APPLY_PARENT_INVERSE")



class VIEW3D_PT_objecttab_apply_delta(toolshelf_calculate, Panel):
    bl_label = "Apply Deltas"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"
    bl_context = "objectmode"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        # bfa - the desctription in myvar.arg comes from release\scripts\startup\bl_operators\object.py
        # defined in class TransformsToDeltas(Operator): by a string property

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            myvar = col.operator("object.transforms_to_deltas", text="Location to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYMOVEDELTA")
            myvar.mode = 'LOC'
            myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

            myvar = col.operator("object.transforms_to_deltas", text="Rotation to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYROTATEDELTA")
            myvar.mode = 'ROT'
            myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

            myvar = col.operator("object.transforms_to_deltas", text="Scale to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYSCALEDELTA")
            myvar.mode = 'SCALE'
            myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

            myvar = col.operator("object.transforms_to_deltas", text="All Transforms to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYALLDELTA")
            myvar.mode = 'ALL'
            myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

            col.separator(factor = 0.5)

            col.operator("object.anim_transforms_to_deltas", icon = "APPLYANIDELTA")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYMOVEDELTA")
                myvar.mode = 'LOC'
                myvar.arg = 'Convert normal object transforms to delta transforms\nAny existing delta transform will be included as well'

                myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYROTATEDELTA")
                myvar.mode = 'ROT'
                myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

                myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYALLDELTA")
                myvar.mode = 'SCALE'
                myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

                row = col.row(align=True)
                myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYALLDELTA")
                myvar.mode = 'ALL'
                myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

                row.operator("object.anim_transforms_to_deltas", text="", icon = "APPLYANIDELTA")


            elif column_count == 2:

                row = col.row(align=True)
                myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYMOVEDELTA")
                myvar.mode = 'LOC'
                myvar.arg = 'Convert normal object transforms to delta transforms\nAny existing delta transform will be included as well'

                myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYROTATEDELTA")
                myvar.mode = 'ROT'
                myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

                row = col.row(align=True)
                myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYSCALEDELTA")
                myvar.mode = 'SCALE'
                myvar.arg = 'nConverts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

                myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYALLDELTA")
                myvar.mode = 'ALL'
                myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

                row = col.row(align=True)
                row.operator("object.anim_transforms_to_deltas", text="", icon = "APPLYANIDELTA")

            elif column_count == 1:

                myvar = col.operator("object.transforms_to_deltas", text="", icon = "APPLYMOVEDELTA")
                myvar.mode = 'LOC'
                myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

                myvar = col.operator("object.transforms_to_deltas", text="", icon = "APPLYROTATEDELTA")
                myvar.mode = 'ROT'
                myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

                myvar = col.operator("object.transforms_to_deltas", text="", icon = "APPLYSCALEDELTA")
                myvar.mode = 'SCALE'
                myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

                myvar = col.operator("object.transforms_to_deltas", text="", icon = "APPLYALLDELTA")
                myvar.mode = 'ALL'
                myvar.arg = 'Converts normal object transforms to delta transforms\nAny existing delta transform will be included as well'

                col.separator(factor = 0.5)

                col.operator("object.anim_transforms_to_deltas", text = "", icon = "APPLYANIDELTA")


class VIEW3D_PT_objecttab_snap(toolshelf_calculate, Panel):
    bl_label = "Snap"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True and context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL', 'EDIT_GPENCIL', 'POSE'}

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor", icon = "SELECTIONTOCURSOR").use_offset = False
            col.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor (Keep Offset)", icon = "SELECTIONTOCURSOROFFSET").use_offset = True
            col.operator("view3d.snap_selected_to_active", text="Selection to Active", icon = "SELECTIONTOACTIVE")
            col.operator("view3d.snap_selected_to_grid", text="Selection to Grid", icon = "SELECTIONTOGRID")

            col.separator()

            col.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected", icon = "CURSORTOSELECTION")
            col.operator("view3d.snap_cursor_to_center", text="Cursor to World Origin", icon = "CURSORTOCENTER")
            col.operator("view3d.snap_cursor_to_active", text="Cursor to Active", icon = "CURSORTOACTIVE")
            col.operator("view3d.snap_cursor_to_grid", text="Cursor to Grid", icon = "CURSORTOGRID")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOR").use_offset = False
                row.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOROFFSET").use_offset = True
                row.operator("view3d.snap_selected_to_active", text = "", icon = "SELECTIONTOACTIVE")

                row = col.row(align=True)
                row.operator("view3d.snap_selected_to_grid", text = "", icon = "SELECTIONTOGRID")
                row.operator("view3d.snap_cursor_to_selected", text = "", icon = "CURSORTOSELECTION")
                row.operator("view3d.snap_cursor_to_center", text = "", icon = "CURSORTOCENTER")

                row = col.row(align=True)
                row.operator("view3d.snap_cursor_to_active", text = "", icon = "CURSORTOACTIVE")
                row.operator("view3d.snap_cursor_to_grid", text = "", icon = "CURSORTOGRID")

            elif column_count == 2:

                row = col.row(align=True)

                row.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOR").use_offset = False
                row.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOROFFSET").use_offset = True

                row = col.row(align=True)

                row.operator("view3d.snap_selected_to_active", text = "", icon = "SELECTIONTOACTIVE")
                row.operator("view3d.snap_selected_to_grid", text = "", icon = "SELECTIONTOGRID")

                row = col.row(align=True)
                row.operator("view3d.snap_cursor_to_selected", text = "", icon = "CURSORTOSELECTION")
                row.operator("view3d.snap_cursor_to_center", text = "", icon = "CURSORTOCENTER")

                row = col.row(align=True)
                row.operator("view3d.snap_cursor_to_active", text = "", icon = "CURSORTOACTIVE")
                row.operator("view3d.snap_cursor_to_grid", text = "", icon = "CURSORTOGRID")

            elif column_count == 1:

                col.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOR").use_offset = False
                col.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOROFFSET").use_offset = True
                col.operator("view3d.snap_selected_to_active", text = "", icon = "SELECTIONTOACTIVE")
                col.operator("view3d.snap_selected_to_grid", text = "", icon = "SELECTIONTOGRID")

                col.separator(factor = 0.5)

                col.operator("view3d.snap_cursor_to_selected", text = "", icon = "CURSORTOSELECTION")
                col.operator("view3d.snap_cursor_to_center", text = "", icon = "CURSORTOCENTER")
                col.operator("view3d.snap_cursor_to_active", text = "", icon = "CURSORTOACTIVE")
                col.operator("view3d.snap_cursor_to_grid", text = "", icon = "CURSORTOGRID")


class VIEW3D_PT_objecttab_shading(toolshelf_calculate, Panel):
    bl_label = "Shading"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        obj = context.object
        if obj is None:
            return
        return overlay.show_toolshelf_tabs == True and context.mode in {'OBJECT'} and obj.type in {'MESH', 'CURVE', 'SURFACE'}

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("object.shade_smooth", icon ='SHADING_SMOOTH')
            col.operator("object.shade_flat", icon ='SHADING_FLAT')
            col.popover(panel="TOOLBAR_PT_normals_autosmooth", text="Auto Smooth", icon="NORMAL_SMOOTH")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("object.shade_smooth", text = "", icon ='SHADING_SMOOTH')
                row.operator("object.shade_flat", text = "", icon ='SHADING_FLAT')
                row.popover(panel="TOOLBAR_PT_normals_autosmooth", text="", icon="NORMAL_SMOOTH")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("object.shade_smooth", text = "", icon ='SHADING_SMOOTH')
                row.operator("object.shade_flat", text = "", icon ='SHADING_FLAT')

                row = col.row()
                row.popover(panel="TOOLBAR_PT_normals_autosmooth", text="", icon="NORMAL_SMOOTH")

            elif column_count == 1:

                col.operator("object.shade_smooth", text = "", icon ='SHADING_SMOOTH')
                col.operator("object.shade_flat", text = "", icon ='SHADING_FLAT')


                row = col.row()
                row.alignment = 'LEFT'
                row.popover(panel="TOOLBAR_PT_normals_autosmooth", text="", icon="NORMAL_SMOOTH")



# -------------------------------------- Mesh

class VIEW3D_PT_meshtab_merge(toolshelf_calculate, Panel):
    bl_label = "Merge"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Mesh"
    bl_context = "mesh_edit"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)
        obedit = bpy.context.edit_object

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator_enum("mesh.merge", "type")

            col.operator("mesh.remove_doubles", text="By Distance", icon = "REMOVE_DOUBLES")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("mesh.merge", text="", icon = "MERGE_CENTER").type = 'CENTER'
                row.operator("mesh.merge", text="", icon = "MERGE_CURSOR").type = 'CURSOR'

                if obedit and obedit.type == "MESH":
                    row = col.row(align=True)
                    em = bmesh.from_edit_mesh(obedit.data)
                    if "VERT" in em.select_mode:
                        first_sel_is_vert = False
                        last_sel_is_vert = False
                        if len(em.select_history) >= 1:
                            first_sel_is_vert = isinstance(em.select_history[0], bmesh.types.BMVert)
                            last_sel_is_vert = isinstance(em.select_history[-1], bmesh.types.BMVert)

                            if first_sel_is_vert:
                                # show merge first
                                #pass # delete this
                                row.operator("mesh.merge", text="", icon = "MERGE_AT_FIRST").type = 'FIRST'

                            if last_sel_is_vert:
                                # show merge last
                                #pass # delete this
                                row.operator("mesh.merge", text="", icon = "MERGE_AT_LAST").type = 'LAST'

                row = col.row(align=True)

                row.operator("mesh.merge", text="", icon = "MERGE").type = 'COLLAPSE'
                row.operator("mesh.remove_doubles", text="", icon = "REMOVE_DOUBLES")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("mesh.merge", text="", icon = "MERGE_CENTER").type = 'CENTER'
                row.operator("mesh.merge", text="", icon = "MERGE_CURSOR").type = 'CURSOR'

                if obedit and obedit.type == "MESH":
                    row = col.row(align=True)
                    em = bmesh.from_edit_mesh(obedit.data)
                    if "VERT" in em.select_mode:
                        first_sel_is_vert = False
                        last_sel_is_vert = False
                        if len(em.select_history) >= 1:
                            first_sel_is_vert = isinstance(em.select_history[0], bmesh.types.BMVert)
                            last_sel_is_vert = isinstance(em.select_history[-1], bmesh.types.BMVert)

                            if first_sel_is_vert:
                                # show merge first
                                #pass # delete this
                                row.operator("mesh.merge", text="", icon = "MERGE_AT_FIRST").type = 'FIRST'

                            if last_sel_is_vert:
                                # show merge last
                                #pass # delete this
                                row.operator("mesh.merge", text="", icon = "MERGE_AT_LAST").type = 'LAST'


                row = col.row(align=True)
                row.operator("mesh.merge", text="", icon = "MERGE").type = 'COLLAPSE'
                row.operator("mesh.remove_doubles", text="", icon = "REMOVE_DOUBLES")

            elif column_count == 1:

                col.operator("mesh.merge", text="", icon = "MERGE_CENTER").type = 'CENTER'
                col.operator("mesh.merge", text="", icon = "MERGE_CURSOR").type = 'CURSOR'

                if obedit and obedit.type == "MESH":
                    em = bmesh.from_edit_mesh(obedit.data)
                    if "VERT" in em.select_mode:
                        first_sel_is_vert = False
                        last_sel_is_vert = False
                        if len(em.select_history) >= 1:
                            first_sel_is_vert = isinstance(em.select_history[0], bmesh.types.BMVert)
                            last_sel_is_vert = isinstance(em.select_history[-1], bmesh.types.BMVert)

                            if first_sel_is_vert:
                                # show merge first
                                #pass # delete this
                                col.operator("mesh.merge", text="", icon = "MERGE_AT_FIRST").type = 'FIRST'

                            if last_sel_is_vert:
                                # show merge last
                                #pass # delete this
                                col.operator("mesh.merge", text="", icon = "MERGE_AT_LAST").type = 'LAST'

                col.operator("mesh.merge", text="", icon = "MERGE").type = 'COLLAPSE'

                col.separator(factor = 0.5)

                col.operator("mesh.remove_doubles", text="", icon = "REMOVE_DOUBLES")


class VIEW3D_PT_meshtab_split(toolshelf_calculate, Panel):
    bl_label = "Split"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Mesh"
    bl_context = "mesh_edit"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("mesh.split", text="Selection", icon = "SPLIT")
            col.operator("mesh.edge_split", text="Faces by edges", icon = "SPLITEDGE").type = 'EDGE'
            col.operator("mesh.edge_split", text="Faces/Edges by Vertices", icon = "SPLIT_BYVERTICES").type = 'VERT'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("mesh.split", text="", icon = "SPLIT")
                row.operator("mesh.edge_split", text="", icon = "SPLITEDGE").type = 'EDGE'
                row.operator("mesh.edge_split", text="", icon = "SPLIT_BYVERTICES").type = 'VERT'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("mesh.split", text="", icon = "SPLIT")
                row = col.row(align=True)
                row.operator("mesh.edge_split", text="", icon = "SPLITEDGE").type = 'EDGE'
                row.operator("mesh.edge_split", text="", icon = "SPLIT_BYVERTICES").type = 'VERT'

            elif column_count == 1:

                col.operator("mesh.split", text="", icon = "SPLIT")
                col.operator("mesh.edge_split", text="", icon = "SPLITEDGE").type = 'EDGE'
                col.operator("mesh.edge_split", text="", icon = "SPLIT_BYVERTICES").type = 'VERT'


class VIEW3D_PT_meshtab_separate(toolshelf_calculate, Panel):
    bl_label = "Separate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Mesh"
    bl_context = "mesh_edit"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("mesh.separate", text="Selection", icon = "SEPARATE").type = 'SELECTED'
            col.operator("mesh.separate", text="By Material", icon = "SEPARATE_BYMATERIAL").type = 'MATERIAL'
            col.operator("mesh.separate", text="By Loose Parts", icon = "SEPARATE_LOOSE").type = 'LOOSE'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("mesh.separate", text="", icon = "SEPARATE").type = 'SELECTED'
                row.operator("mesh.separate", text="", icon = "SEPARATE_BYMATERIAL").type = 'MATERIAL'
                row.operator("mesh.separate", text="", icon = "SEPARATE_LOOSE").type = 'LOOSE'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("mesh.separate", text="", icon = "SEPARATE").type = 'SELECTED'
                row = col.row(align=True)
                row.operator("mesh.separate", text="", icon = "SEPARATE_BYMATERIAL").type = 'MATERIAL'
                row.operator("mesh.separate", text="", icon = "SEPARATE_LOOSE").type = 'LOOSE'

            elif column_count == 1:

                col.operator("mesh.separate", text="", icon = "SEPARATE").type = 'SELECTED'
                col.operator("mesh.separate", text="", icon = "SEPARATE_BYMATERIAL").type = 'MATERIAL'
                col.operator("mesh.separate", text="", icon = "SEPARATE_LOOSE").type = 'LOOSE'


class VIEW3D_PT_meshtab_tools(toolshelf_calculate, Panel):
    bl_label = "Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Mesh"
    bl_context = "mesh_edit"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout
        from math import pi
        with_bullet = bpy.app.build_options.bullet

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("mesh.extrude_repeat", icon = "REPEAT")
            col.operator("mesh.spin", icon = "SPIN").angle = pi * 2

            col.separator(factor = 0.5)

            col.operator("mesh.knife_project", icon='KNIFE_PROJECT')

            if with_bullet:
                col.operator("mesh.convex_hull", icon = "CONVEXHULL")

            col.separator(factor = 0.5)

            col.operator("mesh.symmetrize", icon = "SYMMETRIZE", text = "Symmetrize")
            col.operator("mesh.symmetry_snap", icon = "SNAP_SYMMETRY")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("mesh.extrude_repeat", text = "", icon = "REPEAT")
                row.operator("mesh.spin", text = "", icon = "SPIN").angle = pi * 2
                row.operator("mesh.knife_project", text = "", icon='KNIFE_PROJECT')

                row = col.row(align=True)
                if with_bullet:
                    row.operator("mesh.convex_hull", text = "", icon = "CONVEXHULL")
                row.operator("mesh.symmetrize", text = "", icon = "SYMMETRIZE")
                row.operator("mesh.symmetry_snap", text = "", icon = "SNAP_SYMMETRY")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("mesh.extrude_repeat", text = "", icon = "REPEAT")
                row.operator("mesh.spin", text = "", icon = "SPIN").angle = pi * 2

                row = col.row(align=True)
                row.operator("mesh.knife_project", text = "", icon='KNIFE_PROJECT')

                if with_bullet:
                    row.operator("mesh.convex_hull", text = "", icon = "CONVEXHULL")

                row = col.row(align=True)
                row.operator("mesh.symmetrize", text = "", icon = "SYMMETRIZE")
                row.operator("mesh.symmetry_snap", text = "", icon = "SNAP_SYMMETRY")

            elif column_count == 1:

                col.operator("mesh.extrude_repeat", text = "", icon = "REPEAT")
                col.operator("mesh.spin", text = "", icon = "SPIN").angle = pi * 2

                col.separator(factor = 0.5)

                col.operator("mesh.knife_project", text = "", icon='KNIFE_PROJECT')

                if with_bullet:
                    col.operator("mesh.convex_hull", text = "", icon = "CONVEXHULL")

                col.separator(factor = 0.5)

                col.operator("mesh.symmetrize", text = "", icon = "SYMMETRIZE")
                col.operator("mesh.symmetry_snap", text = "", icon = "SNAP_SYMMETRY")


class VIEW3D_PT_meshtab_normals(toolshelf_calculate, Panel):
    bl_label = "Normals"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Mesh"
    bl_context = "mesh_edit"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("mesh.normals_make_consistent", text="Recalculate Outside", icon = 'RECALC_NORMALS').inside = False
            col.operator("mesh.normals_make_consistent", text="Recalculate Inside", icon = 'RECALC_NORMALS_INSIDE').inside = True
            col.operator("mesh.flip_normals", text = "Flip", icon = 'FLIP_NORMALS')

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("mesh.normals_make_consistent", text="", icon = 'RECALC_NORMALS').inside = False
                row.operator("mesh.normals_make_consistent", text="", icon = 'RECALC_NORMALS_INSIDE').inside = True
                row.operator("mesh.flip_normals", text = "", icon = 'FLIP_NORMALS')

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("mesh.normals_make_consistent", text="", icon = 'RECALC_NORMALS').inside = False
                row.operator("mesh.normals_make_consistent", text="", icon = 'RECALC_NORMALS_INSIDE').inside = True
                row = col.row(align=True)
                row.operator("mesh.flip_normals", text = "", icon = 'FLIP_NORMALS')

            elif column_count == 1:

                col.operator("mesh.normals_make_consistent", text="", icon = 'RECALC_NORMALS').inside = False
                col.operator("mesh.normals_make_consistent", text="", icon = 'RECALC_NORMALS_INSIDE').inside = True
                col.operator("mesh.flip_normals", text = "", icon = 'FLIP_NORMALS')


class VIEW3D_PT_meshtab_shading(toolshelf_calculate, Panel):
    bl_label = "Shading"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Mesh"
    bl_context = "mesh_edit"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("mesh.faces_shade_smooth", icon = 'SHADING_SMOOTH')
            col.operator("mesh.faces_shade_flat", icon = 'SHADING_FLAT')

            col.separator(factor = 0.5)

            col.operator("mesh.mark_sharp", text="Smooth Edges", icon = 'SHADING_EDGE_SMOOTH').clear = True
            col.operator("mesh.mark_sharp", text="Sharp Edges", icon = 'SHADING_EDGE_SHARP')

            col.separator(factor = 0.5)

            props = col.operator("mesh.mark_sharp", text="Smooth Vertices", icon = 'SHADING_VERT_SMOOTH')
            props.use_verts = True
            props.clear = True
            col.operator("mesh.mark_sharp", text="Sharp Vertices", icon = 'SHADING_VERT_SHARP').use_verts = True

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("mesh.faces_shade_smooth", text="", icon = 'SHADING_SMOOTH')
                row.operator("mesh.faces_shade_flat", text="", icon = 'SHADING_FLAT')
                row.operator("mesh.mark_sharp", text="", icon = 'SHADING_EDGE_SMOOTH').clear = True

                row = col.row(align=True)
                row.operator("mesh.mark_sharp", text="", icon = 'SHADING_EDGE_SHARP')
                props = row.operator("mesh.mark_sharp", text="", icon = 'SHADING_VERT_SMOOTH')
                props.use_verts = True
                props.clear = True
                row.operator("mesh.mark_sharp", text="", icon = 'SHADING_VERT_SHARP').use_verts = True

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("mesh.faces_shade_smooth", text="", icon = 'SHADING_SMOOTH')
                row.operator("mesh.faces_shade_flat", text="", icon = 'SHADING_FLAT')

                row = col.row(align=True)
                row.operator("mesh.mark_sharp", text="", icon = 'SHADING_EDGE_SMOOTH').clear = True
                row.operator("mesh.mark_sharp", text="", icon = 'SHADING_EDGE_SHARP')

                row = col.row(align=True)
                props = row.operator("mesh.mark_sharp", text="", icon = 'SHADING_VERT_SMOOTH')
                props.use_verts = True
                props.clear = True
                row.operator("mesh.mark_sharp", text="", icon = 'SHADING_VERT_SHARP').use_verts = True

            elif column_count == 1:

                col.operator("mesh.faces_shade_smooth", text="", icon = 'SHADING_SMOOTH')
                col.operator("mesh.faces_shade_flat", text="", icon = 'SHADING_FLAT')

                col.separator(factor = 0.5)

                col.operator("mesh.mark_sharp", text="", icon = 'SHADING_EDGE_SMOOTH').clear = True
                col.operator("mesh.mark_sharp", text="", icon = 'SHADING_EDGE_SHARP')

                col.separator(factor = 0.5)

                props = col.operator("mesh.mark_sharp", text="", icon = 'SHADING_VERT_SMOOTH')
                props.use_verts = True
                props.clear = True
                col.operator("mesh.mark_sharp", text="", icon = 'SHADING_VERT_SHARP').use_verts = True


class VIEW3D_PT_meshtab_cleanup(toolshelf_calculate, Panel):
    bl_label = "Clean Up"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Mesh"
    bl_context = "mesh_edit"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("mesh.delete_loose", icon = "DELETE")

            col.separator(factor = 0.5)

            col.operator("mesh.decimate", icon = "DECIMATE")
            col.operator("mesh.dissolve_degenerate", icon = "DEGENERATE_DISSOLVE")
            col.operator("mesh.dissolve_limited", icon='DISSOLVE_LIMITED')
            col.operator("mesh.face_make_planar", icon = "MAKE_PLANAR")

            col.separator(factor = 0.5)

            col.operator("mesh.vert_connect_nonplanar", icon = "SPLIT_NONPLANAR")
            col.operator("mesh.vert_connect_concave", icon = "SPLIT_CONCAVE")
            col.operator("mesh.fill_holes", icon = "FILL_HOLE")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("mesh.delete_loose", text = "", icon = "DELETE")
                row.operator("mesh.decimate", text = "", icon = "DECIMATE")
                row.operator("mesh.dissolve_degenerate", text = "", icon = "DEGENERATE_DISSOLVE")

                row = col.row(align=True)
                row.operator("mesh.dissolve_limited", text = "", icon='DISSOLVE_LIMITED')
                row.operator("mesh.face_make_planar", text = "", icon = "MAKE_PLANAR")
                row.operator("mesh.vert_connect_nonplanar", text = "", icon = "SPLIT_NONPLANAR")

                row = col.row(align=True)
                row.operator("mesh.vert_connect_concave", text = "", icon = "SPLIT_CONCAVE")
                row.operator("mesh.fill_holes", text = "", icon = "FILL_HOLE")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("mesh.delete_loose", text = "", icon = "DELETE")
                row.operator("mesh.decimate", text = "", icon = "DECIMATE")

                row = col.row(align=True)
                row.operator("mesh.dissolve_degenerate", text = "", icon = "DEGENERATE_DISSOLVE")
                row.operator("mesh.dissolve_limited", text = "", icon='DISSOLVE_LIMITED')

                row = col.row(align=True)
                row.operator("mesh.face_make_planar", text = "", icon = "MAKE_PLANAR")
                row.operator("mesh.vert_connect_nonplanar", text = "", icon = "SPLIT_NONPLANAR")

                row = col.row(align=True)
                row.operator("mesh.vert_connect_concave", text = "", icon = "SPLIT_CONCAVE")
                row.operator("mesh.fill_holes", text = "", icon = "FILL_HOLE")

            elif column_count == 1:

                col.operator("mesh.delete_loose", text = "", icon = "DELETE")

                col.separator(factor = 0.5)

                col.operator("mesh.decimate", text = "", icon = "DECIMATE")
                col.operator("mesh.dissolve_degenerate", text = "", icon = "DEGENERATE_DISSOLVE")
                col.operator("mesh.dissolve_limited", text = "", icon='DISSOLVE_LIMITED')
                col.operator("mesh.face_make_planar", text = "", icon = "MAKE_PLANAR")

                col.separator(factor = 0.5)

                col.operator("mesh.vert_connect_nonplanar", text = "", icon = "SPLIT_NONPLANAR")
                col.operator("mesh.vert_connect_concave", text = "", icon = "SPLIT_CONCAVE")
                col.operator("mesh.fill_holes", text = "", icon = "FILL_HOLE")


class VIEW3D_PT_meshtab_dissolve(toolshelf_calculate, Panel):
    bl_label = "Dissolve"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Mesh"
    bl_context = "mesh_edit"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("mesh.dissolve_verts", icon='DISSOLVE_VERTS')
            col.operator("mesh.dissolve_edges", icon='DISSOLVE_EDGES')
            col.operator("mesh.dissolve_faces", icon='DISSOLVE_FACES')

            col.separator(factor = 0.5)

            col.operator("mesh.dissolve_limited", icon='DISSOLVE_LIMITED')
            col.operator("mesh.dissolve_mode", icon='DISSOLVE_SELECTION')

            col.separator(factor = 0.5)

            col.operator("mesh.edge_collapse", icon='EDGE_COLLAPSE')

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("mesh.dissolve_verts", text = "", icon='DISSOLVE_VERTS')
                row.operator("mesh.dissolve_edges", text = "", icon='DISSOLVE_EDGES')
                row.operator("mesh.dissolve_faces", text = "", icon='DISSOLVE_FACES')

                row = col.row(align=True)
                row.operator("mesh.dissolve_limited", text = "", icon='DISSOLVE_LIMITED')
                row.operator("mesh.dissolve_mode", text = "", icon='DISSOLVE_SELECTION')
                row.operator("mesh.edge_collapse", text = "", icon='EDGE_COLLAPSE')

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("mesh.dissolve_verts", text = "", icon='DISSOLVE_VERTS')
                row.operator("mesh.dissolve_edges", text = "", icon='DISSOLVE_EDGES')

                row = col.row(align=True)
                row.operator("mesh.dissolve_faces", text = "", icon='DISSOLVE_FACES')
                row.operator("mesh.dissolve_limited", text = "", icon='DISSOLVE_LIMITED')

                row = col.row(align=True)
                row.operator("mesh.dissolve_mode", text = "", icon='DISSOLVE_SELECTION')
                row.operator("mesh.edge_collapse", text = "", icon='EDGE_COLLAPSE')

            elif column_count == 1:

                col.operator("mesh.dissolve_verts", text = "", icon='DISSOLVE_VERTS')
                col.operator("mesh.dissolve_edges", text = "", icon='DISSOLVE_EDGES')
                col.operator("mesh.dissolve_faces", text = "", icon='DISSOLVE_FACES')

                col.separator(factor = 0.5)

                col.operator("mesh.dissolve_limited", text = "", icon='DISSOLVE_LIMITED')
                col.operator("mesh.dissolve_mode", text = "", icon='DISSOLVE_SELECTION')

                col.separator(factor = 0.5)

                col.operator("mesh.edge_collapse", text = "", icon='EDGE_COLLAPSE')


class VIEW3D_PT_vertextab_vertex(toolshelf_calculate, Panel):
    bl_label = "Vertex"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Vertex"
    bl_context = "mesh_edit"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("mesh.edge_face_add", text="Make Edge/Face", icon='MAKE_EDGEFACE')
            col.operator("mesh.vert_connect_path", text = "Connect Vertex Path", icon = "VERTEXCONNECTPATH")
            col.operator("mesh.vert_connect", text = "Connect Vertex Pairs", icon = "VERTEXCONNECT")

            col.separator(factor = 0.5)

            col.operator_context = 'EXEC_REGION_WIN'
            col.operator("mesh.vertices_smooth_laplacian", text="Smooth Laplacian", icon = "SMOOTH_LAPLACIAN")
            col.operator_context = 'INVOKE_REGION_WIN'

            col.separator(factor = 0.5)

            col.operator("transform.vert_crease", icon = "VERTEX_CREASE")

            col.separator(factor = 0.5)

            col.operator("mesh.blend_from_shape", icon = "BLENDFROMSHAPE")
            col.operator("mesh.shape_propagate_to_all", text="Propagate to Shapes", icon = "SHAPEPROPAGATE")

            col.separator(factor = 0.5)

            col.operator("object.vertex_parent_set", icon = "VERTEX_PARENT")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("mesh.edge_face_add", text="", icon='MAKE_EDGEFACE')
                row.operator("mesh.vert_connect_path", text = "", icon = "VERTEXCONNECTPATH")
                row.operator("mesh.vert_connect", text = "", icon = "VERTEXCONNECT")

                row = col.row(align=True)
                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("mesh.vertices_smooth_laplacian", text="", icon = "SMOOTH_LAPLACIAN")
                row.operator_context = 'INVOKE_REGION_WIN'
                row.operator("transform.vert_crease", text = "", icon = "VERTEX_CREASE")

                row.operator("mesh.blend_from_shape", text="", icon = "BLENDFROMSHAPE")

                row = col.row(align=True)
                row.operator("mesh.shape_propagate_to_all", text="", icon = "SHAPEPROPAGATE")
                row.operator("object.vertex_parent_set", text="", icon = "VERTEX_PARENT")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("mesh.edge_face_add", text="", icon='MAKE_EDGEFACE')
                row.operator("mesh.vert_connect_path", text = "", icon = "VERTEXCONNECTPATH")

                row = col.row(align=True)
                row.operator("mesh.vert_connect", text = "", icon = "VERTEXCONNECT")
                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("mesh.vertices_smooth_laplacian", text="", icon = "SMOOTH_LAPLACIAN")
                row.operator_context = 'INVOKE_REGION_WIN'

                row = col.row(align=True)
                row.operator("transform.vert_crease", text = "", icon = "VERTEX_CREASE")
                row.operator("mesh.blend_from_shape", text="", icon = "BLENDFROMSHAPE")

                row = col.row(align=True)
                row.operator("mesh.shape_propagate_to_all", text="", icon = "SHAPEPROPAGATE")
                row.operator("object.vertex_parent_set", text="", icon = "VERTEX_PARENT")

            elif column_count == 1:

                col.operator("mesh.edge_face_add", text="", icon='MAKE_EDGEFACE')
                col.operator("mesh.vert_connect_path", text = "", icon = "VERTEXCONNECTPATH")
                col.operator("mesh.vert_connect", text = "", icon = "VERTEXCONNECT")

                col.separator(factor = 0.5)

                col.operator_context = 'EXEC_REGION_WIN'
                col.operator("mesh.vertices_smooth_laplacian", text="", icon = "SMOOTH_LAPLACIAN")
                col.operator_context = 'INVOKE_REGION_WIN'

                col.separator(factor = 0.5)
                col.operator("transform.vert_crease", text = "", icon = "VERTEX_CREASE")

                col.separator(factor = 0.5)

                col.operator("mesh.blend_from_shape", text="", icon = "BLENDFROMSHAPE")
                col.operator("mesh.shape_propagate_to_all", text="", icon = "SHAPEPROPAGATE")

                col.separator(factor = 0.5)

                col.operator("object.vertex_parent_set", text="", icon = "VERTEX_PARENT")


class VIEW3D_PT_edgetab_Edge(toolshelf_calculate, Panel):
    bl_label = "Edge"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Edge"
    bl_context = "mesh_edit"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        with_freestyle = bpy.app.build_options.freestyle

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.operator_context = 'INVOKE_REGION_WIN'

            col.scale_y = 2

            col.operator("mesh.bridge_edge_loops", icon = "BRIDGE_EDGELOOPS")
            col.operator("mesh.screw", icon = "MOD_SCREW")

            col.separator(factor = 0.5)

            col.operator("mesh.subdivide", icon='SUBDIVIDE_EDGES')
            col.operator("mesh.subdivide_edgering", icon = "SUBDIV_EDGERING")
            col.operator("mesh.unsubdivide", icon = "UNSUBDIVIDE")

            col.separator(factor = 0.5)

            col.operator("mesh.edge_rotate", text="Rotate Edge CW", icon = "ROTATECW").use_ccw = False
            col.operator("mesh.edge_rotate", text="Rotate Edge CCW", icon = "ROTATECCW").use_ccw = True

            col.separator(factor = 0.5)

            col.operator("transform.edge_crease", icon = "CREASE")
            col.operator("transform.edge_bevelweight", icon = "BEVEL")

            col.separator(factor = 0.5)

            col.operator("mesh.mark_sharp", icon = "MARKSHARPEDGES")
            col.operator("mesh.mark_sharp", text="Clear Sharp", icon = "CLEARSHARPEDGES").clear = True

            col.operator("mesh.mark_sharp", text="Mark Sharp from Vertices", icon = "MARKSHARPVERTS").use_verts = True
            props = col.operator("mesh.mark_sharp", text="Clear Sharp from Vertices", icon = "CLEARSHARPVERTS")
            props.use_verts = True
            props.clear = True

            if with_freestyle:
                col.separator(factor = 0.5)

                col.operator("mesh.mark_freestyle_edge", icon = "MARK_FS_EDGE").clear = False
                col.operator("mesh.mark_freestyle_edge", text="Clear Freestyle Edge", icon = "CLEAR_FS_EDGE").clear = True

        # icon buttons
        else:

            col = layout.column(align=True)
            col.operator_context = 'INVOKE_REGION_WIN'
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("mesh.bridge_edge_loops", text="", icon = "BRIDGE_EDGELOOPS")
                row.operator("mesh.screw", text="", icon = "MOD_SCREW")
                row.operator("mesh.subdivide", text="", icon='SUBDIVIDE_EDGES')

                row = col.row(align=True)
                row.operator("mesh.subdivide_edgering", text="", icon = "SUBDIV_EDGERING")
                row.operator("mesh.unsubdivide", text="", icon = "UNSUBDIVIDE")
                row.operator("mesh.edge_rotate", text="", icon = "ROTATECW").use_ccw = False

                row = col.row(align=True)
                row.operator("mesh.edge_rotate", text="", icon = "ROTATECCW").use_ccw = True
                row.operator("transform.edge_crease", text="", icon = "CREASE")
                row.operator("transform.edge_bevelweight", text="", icon = "BEVEL")

                row = col.row(align=True)
                row.operator("mesh.mark_sharp", text="", icon = "MARKSHARPEDGES")
                row.operator("mesh.mark_sharp", text="", icon = "CLEARSHARPEDGES").clear = True
                row.operator("mesh.mark_sharp", text="", icon = "MARKSHARPVERTS").use_verts = True
                row = col.row(align=True)
                props = row.operator("mesh.mark_sharp", text="", icon = "CLEARSHARPVERTS")
                props.use_verts = True
                props.clear = True

                if with_freestyle:

                    row.operator("mesh.mark_freestyle_edge", text="", icon = "MARK_FS_EDGE").clear = False
                    row.operator("mesh.mark_freestyle_edge", text="", icon = "CLEAR_FS_EDGE").clear = True

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("mesh.bridge_edge_loops", text="", icon = "BRIDGE_EDGELOOPS")
                row.operator("mesh.screw", text="", icon = "MOD_SCREW")

                row = col.row(align=True)
                row.operator("mesh.subdivide", text="", icon='SUBDIVIDE_EDGES')
                row.operator("mesh.subdivide_edgering", text="", icon = "SUBDIV_EDGERING")
                row = col.row(align=True)
                row.operator("mesh.unsubdivide", text="", icon = "UNSUBDIVIDE")

                row = col.row(align=True)
                row.operator("mesh.edge_rotate", text="", icon = "ROTATECW").use_ccw = False
                row.operator("mesh.edge_rotate", text="", icon = "ROTATECCW").use_ccw = True

                row = col.row(align=True)
                row.operator("transform.edge_crease", text="", icon = "CREASE")
                row.operator("transform.edge_bevelweight", text="", icon = "BEVEL")

                row = col.row(align=True)
                row.operator("mesh.mark_sharp", text="", icon = "MARKSHARPEDGES")
                row.operator("mesh.mark_sharp", text="", icon = "CLEARSHARPEDGES").clear = True

                row = col.row(align=True)
                row.operator("mesh.mark_sharp", text="", icon = "MARKSHARPVERTS").use_verts = True
                props = row.operator("mesh.mark_sharp", text="", icon = "CLEARSHARPVERTS")
                props.use_verts = True
                props.clear = True

                if with_freestyle:

                    row = col.row(align=True)
                    row.operator("mesh.mark_freestyle_edge", text="", icon = "MARK_FS_EDGE").clear = False
                    row.operator("mesh.mark_freestyle_edge", text="", icon = "CLEAR_FS_EDGE").clear = True

            elif column_count == 1:

                col = layout.column(align=True)
                col.scale_y = 2

                col.operator("mesh.bridge_edge_loops", text="", icon = "BRIDGE_EDGELOOPS")
                col.operator("mesh.screw", text="", icon = "MOD_SCREW")

                col.separator(factor = 0.5)

                col.operator("mesh.subdivide", text="", icon='SUBDIVIDE_EDGES')
                col.operator("mesh.subdivide_edgering", text="", icon = "SUBDIV_EDGERING")
                col.operator("mesh.unsubdivide", text="", icon = "UNSUBDIVIDE")

                col.separator(factor = 0.5)

                col.operator("mesh.edge_rotate", text="", icon = "ROTATECW").use_ccw = False
                col.operator("mesh.edge_rotate", text="", icon = "ROTATECCW").use_ccw = True

                col.separator(factor = 0.5)

                col.operator("transform.edge_crease", text="", icon = "CREASE")
                col.operator("transform.edge_bevelweight", text="", icon = "BEVEL")

                col.separator(factor = 0.5)

                col.operator("mesh.mark_sharp", text="", icon = "MARKSHARPEDGES")
                col.operator("mesh.mark_sharp", text="", icon = "CLEARSHARPEDGES").clear = True

                col.separator(factor = 0.5)

                col.operator("mesh.mark_sharp", text="", icon = "MARKSHARPVERTS").use_verts = True
                props = col.operator("mesh.mark_sharp", text="", icon = "CLEARSHARPVERTS")
                props.use_verts = True
                props.clear = True

                if with_freestyle:

                    col.separator(factor = 0.5)
                    col.operator("mesh.mark_freestyle_edge", text="", icon = "MARK_FS_EDGE").clear = False
                    col.operator("mesh.mark_freestyle_edge", text="", icon = "CLEAR_FS_EDGE").clear = True


class VIEW3D_PT_facetab_face(toolshelf_calculate, Panel):
    bl_label = "Face"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Face"
    bl_context = "mesh_edit"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator_context = 'INVOKE_REGION_WIN'

            col.operator("mesh.poke", icon = "POKEFACES")

            col.separator(factor = 0.5)

            props = col.operator("mesh.quads_convert_to_tris", icon = "TRIANGULATE")
            props.quad_method = props.ngon_method = 'BEAUTY'
            col.operator("mesh.tris_convert_to_quads", icon = "TRISTOQUADS")
            col.operator("mesh.solidify", text="Solidify Faces", icon = "SOLIDIFY")
            col.operator("mesh.wireframe", icon = "WIREFRAME")

            col.separator(factor = 0.5)

            col.operator("mesh.fill", icon = "FILL")
            col.operator("mesh.fill_grid", icon = "GRIDFILL")
            col.operator("mesh.beautify_fill", icon = "BEAUTIFY")

            col.separator(factor = 0.5)

            col.operator("mesh.intersect", icon = "INTERSECT")
            col.operator("mesh.intersect_boolean", icon = "BOOLEAN_INTERSECT")

            col.separator(factor = 0.5)

            col.operator("mesh.face_split_by_edges", icon = "SPLITBYEDGES")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.operator_context = 'INVOKE_REGION_WIN'
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("mesh.poke", text = "", icon = "POKEFACES")
                props = row.operator("mesh.quads_convert_to_tris", text = "", icon = "TRIANGULATE")
                props.quad_method = props.ngon_method = 'BEAUTY'
                row.operator("mesh.tris_convert_to_quads", text = "", icon = "TRISTOQUADS")

                row = col.row(align=True)
                row.operator("mesh.solidify", text="", icon = "SOLIDIFY")
                row.operator("mesh.wireframe", text = "", icon = "WIREFRAME")
                row.operator("mesh.fill", text = "", icon = "FILL")

                row = col.row(align=True)
                row.operator("mesh.fill_grid", text = "", icon = "GRIDFILL")
                row.operator("mesh.beautify_fill", text = "", icon = "BEAUTIFY")

                row.operator("mesh.intersect", text = "", icon = "INTERSECT")

                row = col.row(align=True)
                row.operator("mesh.intersect_boolean", text = "", icon = "BOOLEAN_INTERSECT")
                row.operator("mesh.face_split_by_edges", text = "", icon = "SPLITBYEDGES")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("mesh.poke", text = "", icon = "POKEFACES")
                props = row.operator("mesh.quads_convert_to_tris", text = "", icon = "TRIANGULATE")
                props.quad_method = props.ngon_method = 'BEAUTY'

                row = col.row(align=True)
                row.operator("mesh.tris_convert_to_quads", text = "", icon = "TRISTOQUADS")
                row.operator("mesh.solidify", text="", icon = "SOLIDIFY")

                row = col.row(align=True)
                row.operator("mesh.wireframe", text = "", icon = "WIREFRAME")
                row.operator("mesh.fill", text = "", icon = "FILL")

                row = col.row(align=True)
                row.operator("mesh.fill_grid", text = "", icon = "GRIDFILL")
                row.operator("mesh.beautify_fill", text = "", icon = "BEAUTIFY")

                row = col.row(align=True)
                row.operator("mesh.intersect", text = "", icon = "INTERSECT")

                row = col.row(align=True)
                row.operator("mesh.intersect_boolean", text = "", icon = "BOOLEAN_INTERSECT")
                row.operator("mesh.face_split_by_edges", text = "", icon = "SPLITBYEDGES")

            elif column_count == 1:

                col.operator("mesh.poke", text = "", icon = "POKEFACES")

                col.separator(factor = 0.5)

                props = col.operator("mesh.quads_convert_to_tris", text = "", icon = "TRIANGULATE")
                props.quad_method = props.ngon_method = 'BEAUTY'
                col.operator("mesh.tris_convert_to_quads", text = "", icon = "TRISTOQUADS")
                col.operator("mesh.solidify", text = "", icon = "SOLIDIFY")
                col.operator("mesh.wireframe", text = "", icon = "WIREFRAME")

                col.separator(factor = 0.5)

                col.operator("mesh.fill", text = "", icon = "FILL")
                col.operator("mesh.fill_grid", text = "", icon = "GRIDFILL")
                col.operator("mesh.beautify_fill", text = "", icon = "BEAUTIFY")

                col.separator(factor = 0.5)

                col.operator("mesh.intersect", text = "", icon = "INTERSECT")
                col.operator("mesh.intersect_boolean", text = "", icon = "BOOLEAN_INTERSECT")

                col.separator(factor = 0.5)

                col.operator("mesh.face_split_by_edges", text = "", icon = "SPLITBYEDGES")


class VIEW3D_PT_uvtab_uv(toolshelf_calculate, Panel):
    bl_label = "UV"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "UV"
    bl_context = "mesh_edit"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("uv.unwrap", text = "Unwrap ABF", icon='UNWRAP_ABF').method = 'ANGLE_BASED'
            col.operator("uv.unwrap", text = "Unwrap Conformal", icon='UNWRAP_LSCM').method = 'CONFORMAL'

            col.separator(factor = 0.5)

            col.operator_context = 'INVOKE_DEFAULT'
            col.operator("uv.smart_project", icon = "MOD_UVPROJECT")
            col.operator("uv.lightmap_pack", icon = "LIGHTMAPPACK")
            col.operator("uv.follow_active_quads", icon = "FOLLOWQUADS")

            col.separator(factor = 0.5)

            col.operator_context = 'EXEC_REGION_WIN'
            col.operator("uv.cube_project", icon = "CUBEPROJECT")
            col.operator("uv.cylinder_project", icon = "CYLINDERPROJECT")
            col.operator("uv.sphere_project", icon = "SPHEREPROJECT")

            col.separator(factor = 0.5)

            col.operator_context = 'INVOKE_REGION_WIN'
            col.operator("uv.project_from_view", icon = "PROJECTFROMVIEW").scale_to_bounds = False
            col.operator("uv.project_from_view", text="Project from View (Bounds)", icon = "PROJECTFROMVIEW_BOUNDS").scale_to_bounds = True

            col.separator(factor = 0.5)

            col.operator("mesh.mark_seam", icon = "MARK_SEAM").clear = False
            col.operator("mesh.clear_seam", text="Clear Seam", icon = 'CLEAR_SEAM')

            col.separator(factor = 0.5)

            col.operator("uv.reset", icon = "RESET")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("uv.unwrap", text = "", icon='UNWRAP_ABF').method = 'ANGLE_BASED'
                row.operator("uv.unwrap", text = "", icon='UNWRAP_LSCM').method = 'CONFORMAL'

                row.operator_context = 'INVOKE_DEFAULT'
                row.operator("uv.smart_project", text = "", icon = "MOD_UVPROJECT")

                row = col.row(align=True)
                row.operator("uv.lightmap_pack", text = "", icon = "LIGHTMAPPACK")
                row.operator("uv.follow_active_quads", text = "", icon = "FOLLOWQUADS")
                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("uv.cube_project", text = "", icon = "CUBEPROJECT")

                row = col.row(align=True)
                row.operator("uv.cylinder_project", text = "", icon = "CYLINDERPROJECT")
                row.operator("uv.sphere_project", text = "", icon = "SPHEREPROJECT")
                row.operator_context = 'INVOKE_REGION_WIN'
                row.operator("uv.project_from_view", text = "", icon = "PROJECTFROMVIEW").scale_to_bounds = False

                row = col.row(align=True)
                row.operator("uv.project_from_view", text="", icon = "PROJECTFROMVIEW_BOUNDS").scale_to_bounds = True
                row.operator("mesh.mark_seam", text = "", icon = "MARK_SEAM").clear = False
                row.operator("mesh.clear_seam", text = "", icon = 'CLEAR_SEAM')

                row = col.row(align=True)
                row.operator("uv.reset", text = "", icon = "RESET")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("uv.unwrap", text = "", icon='UNWRAP_ABF').method = 'ANGLE_BASED'
                row.operator("uv.unwrap", text = "", icon='UNWRAP_LSCM').method = 'CONFORMAL'

                row = col.row(align=True)
                row.operator_context = 'INVOKE_DEFAULT'
                row.operator("uv.smart_project", text = "", icon = "MOD_UVPROJECT")
                row.operator("uv.lightmap_pack", text = "", icon = "LIGHTMAPPACK")

                row = col.row(align=True)
                row.operator("uv.follow_active_quads", text = "", icon = "FOLLOWQUADS")
                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("uv.cube_project", text = "", icon = "CUBEPROJECT")

                row = col.row(align=True)
                row.operator("uv.cylinder_project", text = "", icon = "CYLINDERPROJECT")
                row.operator("uv.sphere_project", text = "", icon = "SPHEREPROJECT")

                row = col.row(align=True)
                row.operator_context = 'INVOKE_REGION_WIN'
                row.operator("uv.project_from_view", text = "", icon = "PROJECTFROMVIEW").scale_to_bounds = False
                row.operator("uv.project_from_view", text = "", icon = "PROJECTFROMVIEW_BOUNDS").scale_to_bounds = True

                row = col.row(align=True)
                row.operator("mesh.mark_seam", text = "", icon = "MARK_SEAM").clear = False
                row.operator("mesh.clear_seam", text = "", icon = 'CLEAR_SEAM')

                row = col.row(align=True)
                row.operator("uv.reset", text = "", icon = "RESET")

            elif column_count == 1:

                col.operator("uv.unwrap", text = "", icon='UNWRAP_ABF').method = 'ANGLE_BASED'
                col.operator("uv.unwrap", text = "", icon='UNWRAP_LSCM').method = 'CONFORMAL'

                col.separator(factor = 0.5)

                col.operator_context = 'INVOKE_DEFAULT'
                col.operator("uv.smart_project", text = "", icon = "MOD_UVPROJECT")
                col.operator("uv.lightmap_pack", text = "", icon = "LIGHTMAPPACK")
                col.operator("uv.follow_active_quads", text = "", icon = "FOLLOWQUADS")

                col.separator(factor = 0.5)

                col.operator_context = 'EXEC_REGION_WIN'
                col.operator("uv.cube_project", text = "", icon = "CUBEPROJECT")
                col.operator("uv.cylinder_project", text = "", icon = "CYLINDERPROJECT")
                col.operator("uv.sphere_project", text = "", icon = "SPHEREPROJECT")

                col.separator(factor = 0.5)

                col.operator_context = 'INVOKE_REGION_WIN'
                col.operator("uv.project_from_view", text = "", icon = "PROJECTFROMVIEW").scale_to_bounds = False
                col.operator("uv.project_from_view", text = "", icon = "PROJECTFROMVIEW_BOUNDS").scale_to_bounds = True

                col.separator(factor = 0.5)

                col.operator("mesh.mark_seam", text = "", icon = "MARK_SEAM").clear = False
                col.operator("mesh.clear_seam", text = "", icon = 'CLEAR_SEAM')

                col.separator(factor = 0.5)

                col.operator("uv.reset", text = "", icon = "RESET")


# Workaround to separate the tooltips
class MASK_MT_flood_fill_invert(bpy.types.Operator):
    """Inverts the mask"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mask.flood_fill_invert"        # unique identifier for buttons and menu items to reference.
    bl_label = "Invert Mask"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.paint.mask_flood_fill(mode = 'INVERT')
        return {'FINISHED'}


# Workaround to separate the tooltips
class MASK_MT_flood_fill_fill(bpy.types.Operator):
    """Fills the mask"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mask.flood_fill_fill"        # unique identifier for buttons and menu items to reference.
    bl_label = "Fill Mask"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.paint.mask_flood_fill(mode = 'VALUE', value = 1)
        return {'FINISHED'}


# Workaround to separate the tooltips
class MASK_MT_flood_fill_clear(bpy.types.Operator):
    """Clears the mask"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mask.flood_fill_clear"        # unique identifier for buttons and menu items to reference.
    bl_label = "Clear Mask"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.paint.mask_flood_fill(mode = 'VALUE', value = 0)
        return {'FINISHED'}


class VIEW3D_PT_masktab_mask(toolshelf_calculate, Panel):
    bl_label = "Mask"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Mask"
    bl_context = "sculpt_mode"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("mask.flood_fill_invert", text="Invert Mask", icon = "INVERT_MASK")
            col.operator("mask.flood_fill_fill", text="Fill Mask", icon = "FILL_MASK")
            col.operator("mask.flood_fill_clear", text="Clear Mask", icon = "CLEAR_MASK")

            col.separator(factor = 0.5)

            props = col.operator("sculpt.mask_filter", text='Smooth Mask', icon = "PARTICLEBRUSH_SMOOTH")
            props.filter_type = 'SMOOTH'
            props.auto_iteration_count = True

            props = col.operator("sculpt.mask_filter", text='Sharpen Mask', icon = "SHARPEN")
            props.filter_type = 'SHARPEN'
            props.auto_iteration_count = True

            props = col.operator("sculpt.mask_filter", text='Grow Mask', icon = "SELECTMORE")
            props.filter_type = 'GROW'
            props.auto_iteration_count = True

            props = col.operator("sculpt.mask_filter", text='Shrink Mask', icon = "SELECTLESS")
            props.filter_type = 'SHRINK'
            props.auto_iteration_count = True

            props = col.operator("sculpt.mask_filter", text='Increase Contrast', icon = "INC_CONTRAST")
            props.filter_type = 'CONTRAST_INCREASE'
            props.auto_iteration_count = False

            props = col.operator("sculpt.mask_filter", text='Decrease Contrast', icon = "DEC_CONTRAST")
            props.filter_type = 'CONTRAST_DECREASE'
            props.auto_iteration_count = False

            col.separator(factor = 0.5)

            props = col.operator("sculpt.expand", text="Expand Mask by Topology", icon = "MESH_DATA")
            props.target = 'MASK'
            props.falloff_type = 'GEODESIC'
            props.invert = True

            props = col.operator("sculpt.expand", text="Expand Mask by Curvature", icon = "CURVE_DATA")
            props.target = 'MASK'
            props.falloff_type = 'NORMALS'
            props.invert = False

            col.separator(factor = 0.5)

            props = col.operator("mesh.paint_mask_extract", text="Mask Extract", icon = "PACKAGE")

            col.separator(factor = 0.5)

            props = col.operator("mesh.paint_mask_slice", text="Mask Slice", icon = "MASK_SLICE")
            props.fill_holes = False
            props.new_object = False
            props = col.operator("mesh.paint_mask_slice", text="Mask Slice and Fill Holes", icon = "MASK_SLICE_FILL")
            props.new_object = False
            props = col.operator("mesh.paint_mask_slice", text="Mask Slice to New Object", icon = "MASK_SLICE_NEW")

            col.separator(factor = 0.5)

            props = col.operator("sculpt.dirty_mask", text='Dirty Mask', icon = "DIRTY_VERTEX")


        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("mask.flood_fill_invert", text="", icon = "INVERT_MASK")
                row.operator("mask.flood_fill_fill", text="", icon = "FILL_MASK")
                row.operator("mask.flood_fill_clear", text="", icon = "CLEAR_MASK")

                row = col.row(align=True)
                props = row.operator("sculpt.mask_filter", text='', icon = "PARTICLEBRUSH_SMOOTH")
                props.filter_type = 'SMOOTH'
                props.auto_iteration_count = True

                props = row.operator("sculpt.mask_filter", text='', icon = "SHARPEN")
                props.filter_type = 'SHARPEN'
                props.auto_iteration_count = True

                props = row.operator("sculpt.mask_filter", text='', icon = "SELECTMORE")
                props.filter_type = 'GROW'
                props.auto_iteration_count = True

                row = col.row(align=True)
                props = row.operator("sculpt.mask_filter", text='', icon = "SELECTLESS")
                props.filter_type = 'SHRINK'
                props.auto_iteration_count = True

                props = row.operator("sculpt.mask_filter", text='', icon = "INC_CONTRAST")
                props.filter_type = 'CONTRAST_INCREASE'
                props.auto_iteration_count = False

                props = row.operator("sculpt.mask_filter", text='', icon = "DEC_CONTRAST")
                props.filter_type = 'CONTRAST_DECREASE'
                props.auto_iteration_count = False

                row = col.row(align=True)
                props = row.operator("sculpt.expand", text="", icon = "MESH_DATA")
                props.target = 'MASK'
                props.falloff_type = 'GEODESIC'
                props.invert = True

                props = row.operator("sculpt.expand", text="", icon = "CURVE_DATA")
                props.target = 'MASK'
                props.falloff_type = 'NORMALS'
                props.invert = False

                props = row.operator("mesh.paint_mask_extract", text="", icon = "PACKAGE")

                row = col.row(align=True)
                props = row.operator("mesh.paint_mask_slice", text="", icon = "MASK_SLICE")
                props.fill_holes = False
                props.new_object = False
                props = row.operator("mesh.paint_mask_slice", text="", icon = "MASK_SLICE_FILL")
                props.new_object = False
                props = row.operator("mesh.paint_mask_slice", text="", icon = "MASK_SLICE_NEW")

                row = col.row(align=True)
                props = row.operator("sculpt.dirty_mask", text='', icon = "DIRTY_VERTEX")


            elif column_count == 2:

                row = col.row(align=True)
                row.operator("mask.flood_fill_invert", text="", icon = "INVERT_MASK")
                row.operator("mask.flood_fill_fill", text="", icon = "FILL_MASK")

                row = col.row(align=True)
                row.operator("mask.flood_fill_clear", text="", icon = "CLEAR_MASK")

                props = row.operator("sculpt.mask_filter", text='', icon = "PARTICLEBRUSH_SMOOTH")
                props.filter_type = 'SMOOTH'
                props.auto_iteration_count = True

                row = col.row(align=True)
                props = row.operator("sculpt.mask_filter", text='', icon = "SHARPEN")
                props.filter_type = 'SHARPEN'
                props.auto_iteration_count = True

                props = row.operator("sculpt.mask_filter", text='', icon = "SELECTMORE")
                props.filter_type = 'GROW'
                props.auto_iteration_count = True

                row = col.row(align=True)
                props = row.operator("sculpt.mask_filter", text='', icon = "SELECTLESS")
                props.filter_type = 'SHRINK'
                props.auto_iteration_count = True

                props = row.operator("sculpt.mask_filter", text='', icon = "INC_CONTRAST")
                props.filter_type = 'CONTRAST_INCREASE'
                props.auto_iteration_count = False

                row = col.row(align=True)
                props = row.operator("sculpt.mask_filter", text='', icon = "DEC_CONTRAST")
                props.filter_type = 'CONTRAST_DECREASE'
                props.auto_iteration_count = False

                props = row.operator("sculpt.expand", text="", icon = "MESH_DATA")
                props.target = 'MASK'
                props.falloff_type = 'GEODESIC'
                props.invert = True

                row = col.row(align=True)
                props = row.operator("sculpt.expand", text="", icon = "CURVE_DATA")
                props.target = 'MASK'
                props.falloff_type = 'NORMALS'
                props.invert = False

                props = row.operator("mesh.paint_mask_extract", text="", icon = "PACKAGE")

                row = col.row(align=True)
                props = row.operator("mesh.paint_mask_slice", text="", icon = "MASK_SLICE")
                props.fill_holes = False
                props.new_object = False

                row = col.row(align=True)
                props = row.operator("mesh.paint_mask_slice", text="", icon = "MASK_SLICE_FILL")
                props.new_object = False
                props = row.operator("mesh.paint_mask_slice", text="", icon = "MASK_SLICE_NEW")

                row = col.row(align=True)
                props = row.operator("sculpt.dirty_mask", text='', icon = "DIRTY_VERTEX")

            elif column_count == 1:

                col = layout.column(align=True)
                col.scale_y = 2

                col.operator("mask.flood_fill_invert", text="", icon = "INVERT_MASK")
                col.operator("mask.flood_fill_fill", text="", icon = "FILL_MASK")
                col.operator("mask.flood_fill_clear", text="", icon = "CLEAR_MASK")

                col.separator(factor = 0.5)

                props = col.operator("sculpt.mask_filter", text='', icon = "PARTICLEBRUSH_SMOOTH")
                props.filter_type = 'SMOOTH'
                props.auto_iteration_count = True

                props = col.operator("sculpt.mask_filter", text='', icon = "SHARPEN")
                props.filter_type = 'SHARPEN'
                props.auto_iteration_count = True

                props = col.operator("sculpt.mask_filter", text='', icon = "SELECTMORE")
                props.filter_type = 'GROW'
                props.auto_iteration_count = True

                props = col.operator("sculpt.mask_filter", text='', icon = "SELECTLESS")
                props.filter_type = 'SHRINK'
                props.auto_iteration_count = True

                props = col.operator("sculpt.mask_filter", text='', icon = "INC_CONTRAST")
                props.filter_type = 'CONTRAST_INCREASE'
                props.auto_iteration_count = False

                props = col.operator("sculpt.mask_filter", text='', icon = "DEC_CONTRAST")
                props.filter_type = 'CONTRAST_DECREASE'
                props.auto_iteration_count = False

                col.separator(factor = 0.5)

                props = col.operator("sculpt.expand", text="", icon = "MESH_DATA")
                props.target = 'MASK'
                props.falloff_type = 'GEODESIC'
                props.invert = True

                props = col.operator("sculpt.expand", text="", icon = "CURVE_DATA")
                props.target = 'MASK'
                props.falloff_type = 'NORMALS'
                props.invert = False

                col.separator(factor = 0.5)

                props = col.operator("mesh.paint_mask_extract", text="", icon = "PACKAGE")

                col.separator(factor = 0.5)

                props = col.operator("mesh.paint_mask_slice", text="", icon = "MASK_SLICE")
                props.fill_holes = False
                props.new_object = False
                props = col.operator("mesh.paint_mask_slice", text="", icon = "MASK_SLICE_FILL")
                props.new_object = False
                props = col.operator("mesh.paint_mask_slice", text="", icon = "MASK_SLICE_NEW")

                col.separator(factor = 0.5)

                props = col.operator("sculpt.dirty_mask", text='', icon = "DIRTY_VERTEX")


class VIEW3D_PT_masktab_random_mask(toolshelf_calculate, Panel):
    bl_label = "Random Mask"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Mask"
    bl_context = "sculpt_mode"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("sculpt.mask_init", text='Per Vertex', icon = "SELECT_UNGROUPED_VERTS").mode = 'RANDOM_PER_VERTEX'
            col.operator("sculpt.mask_init", text='Per Face Set', icon = "FACESEL").mode = 'RANDOM_PER_FACE_SET'
            col.operator("sculpt.mask_init", text='Per Loose Part', icon = "SELECT_LOOSE").mode = 'RANDOM_PER_LOOSE_PART'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("sculpt.mask_init", text='', icon = "SELECT_UNGROUPED_VERTS").mode = 'RANDOM_PER_VERTEX'
                row.operator("sculpt.mask_init", text='', icon = "FACESEL").mode = 'RANDOM_PER_FACE_SET'
                row.operator("sculpt.mask_init", text='', icon = "SELECT_LOOSE").mode = 'RANDOM_PER_LOOSE_PART'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("sculpt.mask_init", text='', icon = "SELECT_UNGROUPED_VERTS").mode = 'RANDOM_PER_VERTEX'
                row.operator("sculpt.mask_init", text='', icon = "FACESEL").mode = 'RANDOM_PER_FACE_SET'

                row = col.row(align=True)
                row.operator("sculpt.mask_init", text='', icon = "SELECT_LOOSE").mode = 'RANDOM_PER_LOOSE_PART'


            elif column_count == 1:

                col = layout.column(align=True)
                col.scale_y = 2

                col.operator("sculpt.mask_init", text='', icon = "SELECT_UNGROUPED_VERTS").mode = 'RANDOM_PER_VERTEX'
                col.operator("sculpt.mask_init", text='', icon = "FACESEL").mode = 'RANDOM_PER_FACE_SET'
                col.operator("sculpt.mask_init", text='', icon = "SELECT_LOOSE").mode = 'RANDOM_PER_LOOSE_PART'


class VIEW3D_PT_facesetstab_facesets(toolshelf_calculate, Panel):
    bl_label = "Face Sets"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Face Sets"
    bl_context = "sculpt_mode"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("sculpt.face_sets_create", text='Face Set from Masked', icon = "MOD_MASK").mode = 'MASKED'
            col.operator("sculpt.face_sets_create", text='Face Set from Visible', icon = "FILL_MASK").mode = 'VISIBLE'
            col.operator("sculpt.face_sets_create", text='Face Set from Edit Mode Selection', icon = "EDITMODE_HLT").mode = 'SELECTION'

            col.separator(factor = 0.5)

            col.operator("sculpt.face_set_edit", text='Grow Face Set', icon = 'SELECTMORE').mode = 'GROW'
            col.operator("sculpt.face_set_edit", text='Shrink Face Set', icon = 'SELECTLESS').mode = 'SHRINK'

            col.separator(factor = 0.5)

            col.operator("mesh.face_set_extract", text='Extract Face Set', icon = "SEPARATE")

            col.separator(factor = 0.5)

            col.operator("sculpt.face_set_change_visibility", text='Invert Visible Face Sets', icon = "INVERT_MASK").mode = 'INVERT'
            col.operator("sculpt.face_set_change_visibility", text='Show All Face Sets', icon = "HIDE_OFF").mode = 'SHOW_ALL'
            col.operator("sculpt.face_set_change_visibility", text='Toggle Visibility', icon = "HIDE_UNSELECTED").mode = 'TOGGLE'
            col.operator("sculpt.face_set_change_visibility", text='Hide Active Face Sets', icon = "HIDE_ON").mode = 'HIDE_ACTIVE'

            col.separator(factor = 0.5)

            col.operator("sculpt.face_sets_randomize_colors", text='Randomize Colors', icon = "COLOR")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("sculpt.face_sets_create", text='', icon = "MOD_MASK").mode = 'MASKED'
                row.operator("sculpt.face_sets_create", text='', icon = "FILL_MASK").mode = 'VISIBLE'
                row.operator("sculpt.face_sets_create", text='', icon = "EDITMODE_HLT").mode = 'SELECTION'

                row = col.row(align=True)
                row.operator("sculpt.face_set_edit", text='', icon = 'SELECTMORE').mode = 'GROW'
                row.operator("sculpt.face_set_edit", text='', icon = 'SELECTLESS').mode = 'SHRINK'
                row.operator("mesh.face_set_extract", text='', icon = "SEPARATE")

                row = col.row(align=True)
                row.operator("sculpt.face_set_change_visibility", text='', icon = "INVERT_MASK").mode = 'INVERT'
                row.operator("sculpt.face_set_change_visibility", text='', icon = "HIDE_OFF").mode = 'SHOW_ALL'
                row.operator("sculpt.face_set_change_visibility", text='T', icon = "HIDE_UNSELECTED").mode = 'TOGGLE'

                row = col.row(align=True)
                row.operator("sculpt.face_set_change_visibility", text='', icon = "HIDE_ON").mode = 'HIDE_ACTIVE'
                row.operator("sculpt.face_sets_randomize_colors", text='', icon = "COLOR")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("sculpt.face_sets_create", text='', icon = "MOD_MASK").mode = 'MASKED'
                row.operator("sculpt.face_sets_create", text='', icon = "FILL_MASK").mode = 'VISIBLE'

                row = col.row(align=True)
                row.operator("sculpt.face_sets_create", text='', icon = "EDITMODE_HLT").mode = 'SELECTION'
                row.operator("sculpt.face_set_edit", text='', icon = 'SELECTMORE').mode = 'GROW'

                row = col.row(align=True)
                row.operator("sculpt.face_set_edit", text='', icon = 'SELECTLESS').mode = 'SHRINK'
                row.operator("mesh.face_set_extract", text='', icon = "SEPARATE")

                row = col.row(align=True)
                row.operator("sculpt.face_set_change_visibility", text='', icon = "INVERT_MASK").mode = 'INVERT'
                row.operator("sculpt.face_set_change_visibility", text='', icon = "HIDE_OFF").mode = 'SHOW_ALL'

                row = col.row(align=True)
                row.operator("sculpt.face_set_change_visibility", text='', icon = "HIDE_UNSELECTED").mode = 'TOGGLE'
                row.operator("sculpt.face_set_change_visibility", text='', icon = "HIDE_ON").mode = 'HIDE_ACTIVE'

                row = col.row(align=True)
                row.operator("sculpt.face_sets_randomize_colors", text='', icon = "COLOR")

            elif column_count == 1:

                col.operator("sculpt.face_sets_create", text='', icon = "MOD_MASK").mode = 'MASKED'
                col.operator("sculpt.face_sets_create", text='', icon = "FILL_MASK").mode = 'VISIBLE'
                col.operator("sculpt.face_sets_create", text='', icon = "EDITMODE_HLT").mode = 'SELECTION'

                col.separator(factor = 0.5)

                col.operator("sculpt.face_set_edit", text='', icon = 'SELECTMORE').mode = 'GROW'
                col.operator("sculpt.face_set_edit", text='', icon = 'SELECTLESS').mode = 'SHRINK'

                col.separator(factor = 0.5)

                col.operator("mesh.face_set_extract", text='', icon = "SEPARATE")

                col.separator(factor = 0.5)

                col.operator("sculpt.face_set_change_visibility", text='', icon = "INVERT_MASK").mode = 'INVERT'
                col.operator("sculpt.face_set_change_visibility", text='', icon = "HIDE_OFF").mode = 'SHOW_ALL'
                col.operator("sculpt.face_set_change_visibility", text='', icon = "HIDE_UNSELECTED").mode = 'TOGGLE'
                col.operator("sculpt.face_set_change_visibility", text='', icon = "HIDE_ON").mode = 'HIDE_ACTIVE'

                col.separator(factor = 0.5)

                col.operator("sculpt.face_sets_randomize_colors", text='', icon = "COLOR")


class VIEW3D_PT_facesetstab_init_facesets(toolshelf_calculate, Panel):
    bl_label = "Initialize Face Sets"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Face Sets"
    bl_context = "sculpt_mode"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("sculpt.face_sets_init", text='By Loose Parts', icon = "SELECT_LOOSE").mode = 'LOOSE_PARTS'
            col.operator("sculpt.face_sets_init", text='By Face Set Boundaries', icon = "SELECT_BOUNDARY").mode = 'FACE_SET_BOUNDARIES'
            col.operator("sculpt.face_sets_init", text='By Materials', icon = "MATERIAL_DATA").mode = 'MATERIALS'
            col.operator("sculpt.face_sets_init", text='By Normals', icon = "RECALC_NORMALS").mode = 'NORMALS'
            col.operator("sculpt.face_sets_init", text='By UV Seams', icon = "MARK_SEAM").mode = 'UV_SEAMS'
            col.operator("sculpt.face_sets_init", text='By Edge Creases', icon = "CREASE").mode = 'CREASES'
            col.operator("sculpt.face_sets_init", text='By Edge Bevel Weight', icon = "BEVEL").mode = 'BEVEL_WEIGHT'
            col.operator("sculpt.face_sets_init", text='By Sharp Edges', icon = "SELECT_SHARPEDGES").mode = 'SHARP_EDGES'
            col.operator("sculpt.face_sets_init", text='By Face Maps', icon = "FACE_MAPS").mode = 'FACE_MAPS'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("sculpt.face_sets_init", text='', icon = "SELECT_LOOSE").mode = 'LOOSE_PARTS'
                row.operator("sculpt.face_sets_init", text='', icon = "SELECT_BOUNDARY").mode = 'FACE_SET_BOUNDARIES'
                row.operator("sculpt.face_sets_init", text='', icon = "MATERIAL_DATA").mode = 'MATERIALS'

                row = col.row(align=True)
                row.operator("sculpt.face_sets_init", text='', icon = "RECALC_NORMALS").mode = 'NORMALS'
                row.operator("sculpt.face_sets_init", text='', icon = "MARK_SEAM").mode = 'UV_SEAMS'
                row.operator("sculpt.face_sets_init", text='', icon = "CREASE").mode = 'CREASES'

                row = col.row(align=True)
                row.operator("sculpt.face_sets_init", text='', icon = "BEVEL").mode = 'BEVEL_WEIGHT'
                row.operator("sculpt.face_sets_init", text='', icon = "SELECT_SHARPEDGES").mode = 'SHARP_EDGES'
                row.operator("sculpt.face_sets_init", text='', icon = "FACE_MAPS").mode = 'FACE_MAPS'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("sculpt.face_sets_init", text='', icon = "SELECT_LOOSE").mode = 'LOOSE_PARTS'
                row.operator("sculpt.face_sets_init", text='', icon = "SELECT_BOUNDARY").mode = 'FACE_SET_BOUNDARIES'

                row = col.row(align=True)
                row.operator("sculpt.face_sets_init", text='', icon = "MATERIAL_DATA").mode = 'MATERIALS'
                row.operator("sculpt.face_sets_init", text='', icon = "RECALC_NORMALS").mode = 'NORMALS'

                row = col.row(align=True)
                row.operator("sculpt.face_sets_init", text='', icon = "MARK_SEAM").mode = 'UV_SEAMS'
                row.operator("sculpt.face_sets_init", text='', icon = "CREASE").mode = 'CREASES'

                row = col.row(align=True)
                row.operator("sculpt.face_sets_init", text='', icon = "BEVEL").mode = 'BEVEL_WEIGHT'
                row.operator("sculpt.face_sets_init", text='', icon = "SELECT_SHARPEDGES").mode = 'SHARP_EDGES'

                row = col.row(align=True)
                row.operator("sculpt.face_sets_init", text='', icon = "FACE_MAPS").mode = 'FACE_MAPS'

            elif column_count == 1:

                col.operator("sculpt.face_sets_init", text='', icon = "SELECT_LOOSE").mode = 'LOOSE_PARTS'
                col.operator("sculpt.face_sets_init", text='', icon = "SELECT_BOUNDARY").mode = 'FACE_SET_BOUNDARIES'
                col.operator("sculpt.face_sets_init", text='', icon = "MATERIAL_DATA").mode = 'MATERIALS'
                col.operator("sculpt.face_sets_init", text='', icon = "RECALC_NORMALS").mode = 'NORMALS'
                col.operator("sculpt.face_sets_init", text='', icon = "MARK_SEAM").mode = 'UV_SEAMS'
                col.operator("sculpt.face_sets_init", text='', icon = "CREASE").mode = 'CREASES'
                col.operator("sculpt.face_sets_init", text='', icon = "BEVEL").mode = 'BEVEL_WEIGHT'
                col.operator("sculpt.face_sets_init", text='', icon = "SELECT_SHARPEDGES").mode = 'SHARP_EDGES'
                col.operator("sculpt.face_sets_init", text='', icon = "FACE_MAPS").mode = 'FACE_MAPS'


class VIEW3D_PT_painttab_paint(toolshelf_calculate, Panel):
    bl_label = "Paint"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Paint"
    bl_context = "vertexpaint"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("paint.vertex_color_set", icon = "COLOR")
            col.operator("paint.vertex_color_smooth", icon = "PARTICLEBRUSH_SMOOTH")
            col.operator("paint.vertex_color_dirt", icon = "DIRTY_VERTEX")
            col.operator("paint.vertex_color_from_weight", icon = "VERTCOLFROMWEIGHT")

            col.separator( factor = 0.5)

            col.operator("paint.vertex_color_invert", text="Invert", icon = "REVERSE_COLORS")
            col.operator("paint.vertex_color_levels", text="Levels", icon = "LEVELS")
            col.operator("paint.vertex_color_hsv", text="Hue Saturation Value", icon = "HUESATVAL")
            col.operator("paint.vertex_color_brightness_contrast", text="Bright/Contrast", icon = "BRIGHTNESS_CONTRAST")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("paint.vertex_color_set", text="", icon = "COLOR")
                row.operator("paint.vertex_color_smooth", text="", icon = "PARTICLEBRUSH_SMOOTH")
                row.operator("paint.vertex_color_dirt", text="", icon = "DIRTY_VERTEX")

                row = col.row(align=True)
                row.operator("paint.vertex_color_from_weight", text="", icon = "VERTCOLFROMWEIGHT")
                row.operator("paint.vertex_color_invert", text="", icon = "REVERSE_COLORS")
                row.operator("paint.vertex_color_levels", text="", icon = "LEVELS")

                row = col.row(align=True)
                row.operator("paint.vertex_color_hsv", text="", icon = "HUESATVAL")
                row.operator("paint.vertex_color_brightness_contrast", text="", icon = "BRIGHTNESS_CONTRAST")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("paint.vertex_color_set", text="", icon = "COLOR")
                row.operator("paint.vertex_color_smooth", text="", icon = "PARTICLEBRUSH_SMOOTH")

                row = col.row(align=True)
                row.operator("paint.vertex_color_dirt", text="", icon = "DIRTY_VERTEX")
                row.operator("paint.vertex_color_from_weight", text="", icon = "VERTCOLFROMWEIGHT")

                row = col.row(align=True)
                row.operator("paint.vertex_color_invert", text="", icon = "REVERSE_COLORS")
                row.operator("paint.vertex_color_levels", text="", icon = "LEVELS")

                row = col.row(align=True)
                row.operator("paint.vertex_color_hsv", text="", icon = "HUESATVAL")
                row.operator("paint.vertex_color_brightness_contrast", text="", icon = "BRIGHTNESS_CONTRAST")

            elif column_count == 1:

                col.operator("paint.vertex_color_set", text="", icon = "COLOR")
                col.operator("paint.vertex_color_smooth", text="", icon = "PARTICLEBRUSH_SMOOTH")
                col.operator("paint.vertex_color_dirt", text="", icon = "DIRTY_VERTEX")
                col.operator("paint.vertex_color_from_weight", text="", icon = "VERTCOLFROMWEIGHT")

                col.separator( factor = 0.5)

                col.operator("paint.vertex_color_invert", text="", icon = "REVERSE_COLORS")
                col.operator("paint.vertex_color_levels", text="", icon = "LEVELS")
                col.operator("paint.vertex_color_hsv", text="", icon = "HUESATVAL")
                col.operator("paint.vertex_color_brightness_contrast", text="", icon = "BRIGHTNESS_CONTRAST")


class VIEW3D_PT_painttab_colorpicker(toolshelf_calculate, Panel):
    bl_label = "Color Picker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Paint"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True and context.mode in {'PAINT_VERTEX', 'PAINT_TEXTURE'}

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("paint.sample_color", text = "Color Picker", icon='EYEDROPPER')

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("paint.sample_color", text = "", icon='EYEDROPPER')

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("paint.sample_color", text = "", icon='EYEDROPPER')

            elif column_count == 1:

                col.operator("paint.sample_color", text = "", icon='EYEDROPPER')


class VIEW3D_PT_weightstab_weights(toolshelf_calculate, Panel):
    bl_label = "Weights"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Weights"
    bl_context = "weightpaint"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True
    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("paint.weight_from_bones", text = "Assign Automatic from Bones", icon = "BONE_DATA").type = 'AUTOMATIC'
            col.operator("paint.weight_from_bones", text = "Assign from Bone Envelopes", icon = "ENVELOPE_MODIFIER").type = 'ENVELOPES'

            col.separator(factor = 0.5)

            col.operator("object.vertex_group_normalize_all", text = "Normalize All", icon='WEIGHT_NORMALIZE_ALL')
            col.operator("object.vertex_group_normalize", text = "Normalize", icon='WEIGHT_NORMALIZE')

            col.separator(factor = 0.5)

            col.operator("object.vertex_group_mirror", text="Mirror", icon='WEIGHT_MIRROR')
            col.operator("object.vertex_group_invert", text="Invert", icon='WEIGHT_INVERT')
            col.operator("object.vertex_group_clean", text="Clean", icon='WEIGHT_CLEAN')

            col.separator(factor = 0.5)

            col.operator("object.vertex_group_quantize", text = "Quantize", icon = "WEIGHT_QUANTIZE")
            col.operator("object.vertex_group_levels", text = "Levels", icon = 'WEIGHT_LEVELS')
            col.operator("object.vertex_group_smooth", text = "Smooth", icon='WEIGHT_SMOOTH')

            props = col.operator("object.data_transfer", text="Transfer Weights", icon = 'WEIGHT_TRANSFER_WEIGHTS')
            props.use_reverse_transfer = True
            props.data_type = 'VGROUP_WEIGHTS'

            col.operator("object.vertex_group_limit_total", text="Limit Total", icon='WEIGHT_LIMIT_TOTAL')
            col.operator("object.vertex_group_fix", text="Fix Deforms", icon='WEIGHT_FIX_DEFORMS')

            col.separator(factor = 0.5)

            col.operator("paint.weight_set", icon = "MOD_VERTEX_WEIGHT")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("paint.weight_from_bones", text = "", icon = "BONE_DATA").type = 'AUTOMATIC'
                row.operator("paint.weight_from_bones", text = "", icon = "ENVELOPE_MODIFIER").type = 'ENVELOPES'
                row.operator("object.vertex_group_normalize_all", text = "", icon='WEIGHT_NORMALIZE_ALL')

                row = col.row(align=True)
                row.operator("object.vertex_group_normalize", text = "", icon='WEIGHT_NORMALIZE')
                row.operator("object.vertex_group_mirror", text="", icon='WEIGHT_MIRROR')
                row.operator("object.vertex_group_invert", text="", icon='WEIGHT_INVERT')

                row = col.row(align=True)
                row.operator("object.vertex_group_clean", text="", icon='WEIGHT_CLEAN')
                row.operator("object.vertex_group_quantize", text = "", icon = "WEIGHT_QUANTIZE")
                row.operator("object.vertex_group_levels", text = "", icon = 'WEIGHT_LEVELS')

                row = col.row(align=True)
                row.operator("object.vertex_group_smooth", text = "", icon='WEIGHT_SMOOTH')
                props = row.operator("object.data_transfer", text="", icon = 'WEIGHT_TRANSFER_WEIGHTS')
                props.use_reverse_transfer = True
                props.data_type = 'VGROUP_WEIGHTS'
                row.operator("object.vertex_group_limit_total", text="", icon='WEIGHT_LIMIT_TOTAL')

                row = col.row(align=True)
                row.operator("object.vertex_group_fix", text="", icon='WEIGHT_FIX_DEFORMS')
                row.operator("paint.weight_set", text="", icon = "MOD_VERTEX_WEIGHT")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("paint.weight_from_bones", text = "", icon = "BONE_DATA").type = 'AUTOMATIC'
                row.operator("paint.weight_from_bones", text = "", icon = "ENVELOPE_MODIFIER").type = 'ENVELOPES'

                row = col.row(align=True)
                row.operator("object.vertex_group_normalize_all", text = "", icon='WEIGHT_NORMALIZE_ALL')
                row.operator("object.vertex_group_normalize", text = "", icon='WEIGHT_NORMALIZE')

                row = col.row(align=True)
                row.operator("object.vertex_group_mirror", text="", icon='WEIGHT_MIRROR')
                row.operator("object.vertex_group_invert", text="", icon='WEIGHT_INVERT')

                row = col.row(align=True)
                row.operator("object.vertex_group_clean", text="", icon='WEIGHT_CLEAN')
                row.operator("object.vertex_group_quantize", text = "", icon = "WEIGHT_QUANTIZE")

                row = col.row(align=True)
                row.operator("object.vertex_group_levels", text = "", icon = 'WEIGHT_LEVELS')
                row.operator("object.vertex_group_smooth", text = "", icon='WEIGHT_SMOOTH')

                row = col.row(align=True)
                props = row.operator("object.data_transfer", text="", icon = 'WEIGHT_TRANSFER_WEIGHTS')
                props.use_reverse_transfer = True
                props.data_type = 'VGROUP_WEIGHTS'
                row.operator("object.vertex_group_limit_total", text="", icon='WEIGHT_LIMIT_TOTAL')

                row = col.row(align=True)
                row.operator("object.vertex_group_fix", text="", icon='WEIGHT_FIX_DEFORMS')
                row.operator("paint.weight_set", text="", icon = "MOD_VERTEX_WEIGHT")

            elif column_count == 1:

                col.operator("paint.weight_from_bones", text = "", icon = "BONE_DATA").type = 'AUTOMATIC'
                col.operator("paint.weight_from_bones", text = "", icon = "ENVELOPE_MODIFIER").type = 'ENVELOPES'

                col.separator(factor = 0.5)

                col.operator("object.vertex_group_normalize_all", text = "", icon='WEIGHT_NORMALIZE_ALL')
                col.operator("object.vertex_group_normalize", text = "", icon='WEIGHT_NORMALIZE')

                col.separator(factor = 0.5)

                col.operator("object.vertex_group_mirror", text="", icon='WEIGHT_MIRROR')
                col.operator("object.vertex_group_invert", text="", icon='WEIGHT_INVERT')
                col.operator("object.vertex_group_clean", text="", icon='WEIGHT_CLEAN')

                col.separator(factor = 0.5)

                col.operator("object.vertex_group_quantize", text = "", icon = "WEIGHT_QUANTIZE")
                col.operator("object.vertex_group_levels", text = "", icon = 'WEIGHT_LEVELS')
                col.operator("object.vertex_group_smooth", text = "", icon='WEIGHT_SMOOTH')

                props = col.operator("object.data_transfer", text="", icon = 'WEIGHT_TRANSFER_WEIGHTS')
                props.use_reverse_transfer = True
                props.data_type = 'VGROUP_WEIGHTS'

                col.operator("object.vertex_group_limit_total", text="", icon='WEIGHT_LIMIT_TOTAL')
                col.operator("object.vertex_group_fix", text="", icon='WEIGHT_FIX_DEFORMS')

                col.separator(factor = 0.5)

                col.operator("paint.weight_set", text="", icon = "MOD_VERTEX_WEIGHT")


class VIEW3D_PT_curvetab_curve(toolshelf_calculate, Panel):
    bl_label = "Curve"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Curve"
    bl_context = "curve_edit"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("curve.split", icon = "SPLIT")
            col.operator("curve.separate", icon = "SEPARATE")

            col.separator(factor = 0.5)

            col.operator("curve.cyclic_toggle", icon = 'TOGGLE_CYCLIC')
            col.operator("curve.decimate", icon = "DECIMATE")

            col.separator(factor = 0.5)

            col.operator("transform.tilt", icon = "TILT")
            col.operator("curve.tilt_clear", icon = "CLEAR_TILT")

            col.separator(factor = 0.5)

            col.operator("curve.normals_make_consistent", icon = 'RECALC_NORMALS')

            col.separator(factor = 0.5)

            col.operator("curve.dissolve_verts", icon='DISSOLVE_VERTS')

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("curve.split", text = "", icon = "SPLIT")
                row.operator("curve.separate", text = "", icon = "SEPARATE")
                row.operator("curve.cyclic_toggle", text = "", icon = 'TOGGLE_CYCLIC')

                row = col.row(align=True)
                row.operator("curve.decimate", text = "", icon = "DECIMATE")
                row.operator("transform.tilt", text = "", icon = "TILT")
                row.operator("curve.tilt_clear", text = "", icon = "CLEAR_TILT")

                row = col.row(align=True)
                row.operator("curve.normals_make_consistent", text = "", icon = 'RECALC_NORMALS')
                row.operator("curve.dissolve_verts", text = "", icon='DISSOLVE_VERTS')

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("curve.split", text = "", icon = "SPLIT")
                row.operator("curve.separate", text = "", icon = "SEPARATE")

                row = col.row(align=True)
                row.operator("curve.cyclic_toggle", text = "", icon = 'TOGGLE_CYCLIC')
                row.operator("curve.decimate", text = "", icon = "DECIMATE")

                row = col.row(align=True)
                row.operator("transform.tilt", text = "", icon = "TILT")
                row.operator("curve.tilt_clear", text = "", icon = "CLEAR_TILT")

                row = col.row(align=True)
                row.operator("curve.normals_make_consistent", text = "", icon = 'RECALC_NORMALS')
                row.operator("curve.dissolve_verts", text = "", icon='DISSOLVE_VERTS')

            elif column_count == 1:

                col.operator("curve.split", text = "", icon = "SPLIT")
                col.operator("curve.separate", text = "", icon = "SEPARATE")

                col.separator(factor = 0.5)

                col.operator("curve.cyclic_toggle", text = "", icon = 'TOGGLE_CYCLIC')
                col.operator("curve.decimate", text = "", icon = "DECIMATE")

                col.separator(factor = 0.5)

                col.operator("transform.tilt", text = "", icon = "TILT")
                col.operator("curve.tilt_clear", text = "", icon = "CLEAR_TILT")

                col.separator(factor = 0.5)

                col.operator("curve.normals_make_consistent", text = "", icon = 'RECALC_NORMALS')

                col.separator(factor = 0.5)

                col.operator("curve.dissolve_verts", text = "", icon='DISSOLVE_VERTS')


class VIEW3D_PT_curvetab_controlpoints(toolshelf_calculate, Panel):
    bl_label = "Control Points"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Control Points"
    bl_context = "curve_edit"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("curve.extrude_move", text = "Extrude Curve", icon = 'EXTRUDE_REGION')

            col.separator(factor = 0.5)

            col.operator("curve.make_segment", icon = "MAKE_CURVESEGMENT")

            col.separator(factor = 0.5)

            col.operator("transform.tilt", icon = 'TILT')
            col.operator("curve.tilt_clear",icon = "CLEAR_TILT")

            col.separator(factor = 0.5)

            col.operator("curve.normals_make_consistent", icon = 'RECALC_NORMALS')

            col.separator(factor = 0.5)

            col.operator("curve.smooth", icon = 'PARTICLEBRUSH_SMOOTH')
            col.operator("curve.smooth_weight", icon = "SMOOTH_WEIGHT")
            col.operator("curve.smooth_radius", icon = "SMOOTH_RADIUS")
            col.operator("curve.smooth_tilt", icon = "SMOOTH_TILT")

            col.separator(factor = 0.5)

            col.operator("object.vertex_parent_set", icon = "VERTEX_PARENT")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("curve.extrude_move", text = "", icon = 'EXTRUDE_REGION')
                row.operator("curve.make_segment", text = "", icon = "MAKE_CURVESEGMENT")
                row.operator("transform.tilt", text = "", icon = 'TILT')

                row = col.row(align=True)
                row.operator("curve.tilt_clear", text = "",icon = "CLEAR_TILT")
                row.operator("curve.normals_make_consistent", text = "", icon = 'RECALC_NORMALS')
                row.operator("curve.smooth", text = "", icon = 'PARTICLEBRUSH_SMOOTH')

                row = col.row(align=True)
                row.operator("curve.smooth_weight", text = "", icon = "SMOOTH_WEIGHT")
                row.operator("curve.smooth_radius", text = "", icon = "SMOOTH_RADIUS")
                row.operator("curve.smooth_tilt", text = "", icon = "SMOOTH_TILT")

                row = col.row(align=True)
                row.operator("object.vertex_parent_set", text = "", icon = "VERTEX_PARENT")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("curve.extrude_move", text = "", icon = 'EXTRUDE_REGION')
                row.operator("curve.make_segment", text = "", icon = "MAKE_CURVESEGMENT")

                row = col.row(align=True)
                row.operator("transform.tilt", text = "", icon = 'TILT')
                row.operator("curve.tilt_clear", text = "",icon = "CLEAR_TILT")

                row = col.row(align=True)
                row.operator("curve.normals_make_consistent", text = "", icon = 'RECALC_NORMALS')
                row.operator("curve.smooth", text = "", icon = 'PARTICLEBRUSH_SMOOTH')

                row = col.row(align=True)
                row.operator("curve.smooth_weight", text = "", icon = "SMOOTH_WEIGHT")
                row.operator("curve.smooth_radius", text = "", icon = "SMOOTH_RADIUS")

                row = col.row(align=True)
                row.operator("curve.smooth_tilt", text = "", icon = "SMOOTH_TILT")
                row.operator("object.vertex_parent_set", text = "", icon = "VERTEX_PARENT")

            elif column_count == 1:

                col.operator("curve.extrude_move", text = "", icon = 'EXTRUDE_REGION')

                col.separator(factor = 0.5)

                col.operator("curve.make_segment", text = "", icon = "MAKE_CURVESEGMENT")

                col.separator(factor = 0.5)

                col.operator("transform.tilt", text = "", icon = 'TILT')
                col.operator("curve.tilt_clear", text = "",icon = "CLEAR_TILT")

                col.separator(factor = 0.5)

                col.operator("curve.normals_make_consistent", text = "", icon = 'RECALC_NORMALS')

                col.separator(factor = 0.5)

                col.operator("curve.smooth", text = "", icon = 'PARTICLEBRUSH_SMOOTH')
                col.operator("curve.smooth_weight", text = "", icon = "SMOOTH_WEIGHT")
                col.operator("curve.smooth_radius", text = "", icon = "SMOOTH_RADIUS")
                col.operator("curve.smooth_tilt", text = "", icon = "SMOOTH_TILT")

                col.separator(factor = 0.5)

                col.operator("object.vertex_parent_set", text = "", icon = "VERTEX_PARENT")


class VIEW3D_PT_surfacetab_surface(toolshelf_calculate, Panel):
    bl_label = "Surface"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Surface"
    bl_context = "surface_edit"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("curve.spin", icon = 'SPIN')

            col.separator(factor = 0.5)

            col.operator("curve.split", icon = "SPLIT")
            col.operator("curve.separate", icon = "SEPARATE")

            col.separator(factor = 0.5)

            col.operator("curve.cyclic_toggle", icon = 'TOGGLE_CYCLIC')

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("curve.spin", text = "", icon = 'SPIN')
                row.operator("curve.split", text = "", icon = "SPLIT")
                row.operator("curve.separate", text = "", icon = "SEPARATE")

                row = col.row(align=True)
                row.operator("curve.cyclic_toggle", text = "", icon = 'TOGGLE_CYCLIC')

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("curve.spin", text = "", icon = 'SPIN')
                row.operator("curve.split", text = "", icon = "SPLIT")

                row = col.row(align=True)
                row.operator("curve.separate", text = "", icon = "SEPARATE")
                row.operator("curve.cyclic_toggle", text = "", icon = 'TOGGLE_CYCLIC')

            elif column_count == 1:

                col.operator("curve.spin", text = "", icon = 'SPIN')

                col.separator(factor = 0.5)

                col.operator("curve.split", text = "", icon = "SPLIT")
                col.operator("curve.separate", text = "", icon = "SEPARATE")

                col.separator(factor = 0.5)

                col.operator("curve.cyclic_toggle", text = "", icon = 'TOGGLE_CYCLIC')


class VIEW3D_PT_curvetab_controlpoints_surface(toolshelf_calculate, Panel):
    bl_label = "Control Points"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Control Points"
    bl_context = "surface_edit"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("curve.extrude_move", text = "Extrude Curve", icon = 'EXTRUDE_REGION')

            col.separator(factor = 0.5)

            col.operator("curve.make_segment", icon = "MAKE_CURVESEGMENT")

            col.separator(factor = 0.5)

            col.operator("curve.smooth", icon = 'PARTICLEBRUSH_SMOOTH')

            col.separator(factor = 0.5)

            col.operator("object.vertex_parent_set", icon = "VERTEX_PARENT")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("curve.extrude_move", text = "", icon = 'EXTRUDE_REGION')
                row.operator("curve.make_segment", text = "", icon = "MAKE_CURVESEGMENT")
                row.operator("curve.smooth", text = "", icon = 'PARTICLEBRUSH_SMOOTH')

                row = col.row(align=True)
                row.operator("object.vertex_parent_set", text = "", icon = "VERTEX_PARENT")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("curve.extrude_move", text = "", icon = 'EXTRUDE_REGION')
                row.operator("curve.make_segment", text = "", icon = "MAKE_CURVESEGMENT")

                row = col.row(align=True)
                row.operator("curve.smooth", text = "", icon = 'PARTICLEBRUSH_SMOOTH')
                row.operator("object.vertex_parent_set", text = "", icon = "VERTEX_PARENT")

            elif column_count == 1:

                col.operator("curve.extrude_move", text = "", icon = 'EXTRUDE_REGION')

                col.separator(factor = 0.5)

                col.operator("curve.make_segment", text = "", icon = "MAKE_CURVESEGMENT")

                col.separator(factor = 0.5)

                col.operator("curve.smooth", text = "", icon = 'PARTICLEBRUSH_SMOOTH')

                col.separator(factor = 0.5)

                col.operator("object.vertex_parent_set", text = "", icon = "VERTEX_PARENT")


class VIEW3D_PT_segmentstab_segments(toolshelf_calculate, Panel):
    bl_label = "Segments"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Segments"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        # curve and surface object in edit mode by poll, not by bl_context
        return overlay.show_toolshelf_tabs == True and context.mode in {'EDIT_SURFACE','EDIT_CURVE'}

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("curve.subdivide", icon = 'SUBDIVIDE_EDGES')
            col.operator("curve.switch_direction", icon = 'SWITCH_DIRECTION')

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("curve.subdivide", text = "", icon = 'SUBDIVIDE_EDGES')
                row.operator("curve.switch_direction", text = "", icon = 'SWITCH_DIRECTION')

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("curve.subdivide", text = "", icon = 'SUBDIVIDE_EDGES')
                row.operator("curve.switch_direction", text = "", icon = 'SWITCH_DIRECTION')

            elif column_count == 1:

                col.operator("curve.subdivide", text = "", icon = 'SUBDIVIDE_EDGES')
                col.operator("curve.switch_direction", text = "", icon = 'SWITCH_DIRECTION')


class VIEW3D_PT_gp_gpenciltab_dissolve(toolshelf_calculate, Panel):
    bl_label = "Dissolve"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "greasepencil_edit"
    bl_category = "Gpencil"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("gpencil.dissolve", text="Dissolve", icon = "DISSOLVE_VERTS").type = 'POINTS'
            col.operator("gpencil.dissolve", text="Dissolve Between", icon = "DISSOLVE_BETWEEN").type = 'BETWEEN'
            col.operator("gpencil.dissolve", text="Dissolve Unselected", icon = "DISSOLVE_UNSELECTED").type = 'UNSELECT'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("gpencil.dissolve", text="", icon = "DISSOLVE_VERTS").type = 'POINTS'
                row.operator("gpencil.dissolve", text="", icon = "DISSOLVE_BETWEEN").type = 'BETWEEN'
                row.operator("gpencil.dissolve", text="", icon = "DISSOLVE_UNSELECTED").type = 'UNSELECT'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("gpencil.dissolve", text="", icon = "DISSOLVE_VERTS").type = 'POINTS'
                row.operator("gpencil.dissolve", text="", icon = "DISSOLVE_BETWEEN").type = 'BETWEEN'

                row = col.row(align=True)
                row.operator("gpencil.dissolve", text="", icon = "DISSOLVE_UNSELECTED").type = 'UNSELECT'

            elif column_count == 1:

                col.operator("gpencil.dissolve", text="", icon = "DISSOLVE_VERTS").type = 'POINTS'
                col.operator("gpencil.dissolve", text="", icon = "DISSOLVE_BETWEEN").type = 'BETWEEN'
                col.operator("gpencil.dissolve", text="", icon = "DISSOLVE_UNSELECTED").type = 'UNSELECT'


class VIEW3D_PT_gp_gpenciltab_cleanup(toolshelf_calculate, Panel):
    bl_label = "Clean Up"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "greasepencil_edit"
    bl_category = "Gpencil"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("gpencil.frame_clean_fill", text="Boundary Strokes", icon = "CLEAN_CHANNELS").mode = 'ACTIVE'
            col.operator("gpencil.frame_clean_fill", text="Boundary Strokes all Frames", icon = "CLEAN_CHANNELS_FRAMES").mode = 'ALL'

            col.separator(factor = 0.5)

            col.operator("gpencil.frame_clean_loose", text="Delete Loose Points", icon = "DELETE_LOOSE")
            col.operator("gpencil.stroke_merge_by_distance", text="Merge by Distance", icon = "MERGE")

            col.separator(factor = 0.5)

            col.operator("gpencil.frame_clean_duplicate", text="Delete Duplicated Frames", icon = "DELETE_DUPLICATE")
            col.operator("gpencil.recalc_geometry", text="Recalculate Geometry", icon = "FILE_REFRESH")
            col.operator("gpencil.reproject", icon = "REPROJECT")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("gpencil.frame_clean_fill", text="", icon = "CLEAN_CHANNELS").mode = 'ACTIVE'
                row.operator("gpencil.frame_clean_fill", text="", icon = "CLEAN_CHANNELS_FRAMES").mode = 'ALL'
                row.operator("gpencil.frame_clean_loose", text="", icon = "DELETE_LOOSE")

                row = col.row(align=True)
                row.operator("gpencil.stroke_merge_by_distance", text="", icon = "MERGE")
                row.operator("gpencil.frame_clean_duplicate", text="", icon = "DELETE_DUPLICATE")
                row.operator("gpencil.recalc_geometry", text="", icon = "FILE_REFRESH")

                row = col.row(align=True)
                row.operator("gpencil.reproject", text = "", icon = "REPROJECT")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("gpencil.frame_clean_fill", text="", icon = "CLEAN_CHANNELS").mode = 'ACTIVE'
                row.operator("gpencil.frame_clean_fill", text="", icon = "CLEAN_CHANNELS_FRAMES").mode = 'ALL'

                row = col.row(align=True)
                row.operator("gpencil.frame_clean_loose", text="", icon = "DELETE_LOOSE")
                row.operator("gpencil.stroke_merge_by_distance", text="", icon = "MERGE")

                row = col.row(align=True)
                row.operator("gpencil.frame_clean_duplicate", text="", icon = "DELETE_DUPLICATE")
                row.operator("gpencil.recalc_geometry", text="", icon = "FILE_REFRESH")

                row = col.row(align=True)
                row.operator("gpencil.reproject", text = "", icon = "REPROJECT")

            elif column_count == 1:

                col.operator("gpencil.frame_clean_fill", text="", icon = "CLEAN_CHANNELS").mode = 'ACTIVE'
                col.operator("gpencil.frame_clean_fill", text="", icon = "CLEAN_CHANNELS_FRAMES").mode = 'ALL'

                col.separator(factor = 0.5)

                col.operator("gpencil.frame_clean_loose", text="", icon = "DELETE_LOOSE")
                col.operator("gpencil.stroke_merge_by_distance", text="", icon = "MERGE")

                col.separator(factor = 0.5)

                col.operator("gpencil.frame_clean_duplicate", text="", icon = "DELETE")
                col.operator("gpencil.recalc_geometry", text="", icon = "FILE_REFRESH")
                col.operator("gpencil.reproject", text = "", icon = "REPROJECT")


class VIEW3D_PT_gp_gpenciltab_separate(toolshelf_calculate, Panel):
    bl_label = "Separate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "greasepencil_edit"
    bl_category = "Gpencil"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("gpencil.stroke_separate", text="Separate Selected Points", icon = "SEPARATE_GP_POINTS").mode = 'POINT'
            col.operator("gpencil.stroke_separate", text="Separate Selected Strokes", icon = "SEPARATE_GP_STROKES").mode = 'STROKE'
            col.operator("gpencil.stroke_separate", text="Separate Active Layer", icon = "SEPARATE_GP_STROKES").mode = 'LAYER'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("gpencil.stroke_separate", text="", icon = "SEPARATE_GP_POINTS").mode = 'POINT'
                row.operator("gpencil.stroke_separate", text="", icon = "SEPARATE_GP_STROKES").mode = 'STROKE'
                row.operator("gpencil.stroke_separate", text="", icon = "SEPARATE_GP_LAYER").mode = 'LAYER'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("gpencil.stroke_separate", text="", icon = "SEPARATE_GP_POINTS").mode = 'POINT'
                row.operator("gpencil.stroke_separate", text="", icon = "SEPARATE_GP_STROKES").mode = 'STROKE'

                row = col.row(align=True)
                row.operator("gpencil.stroke_separate", text="", icon = "SEPARATE_GP_LAYER").mode = 'LAYER'

            elif column_count == 1:

                col.operator("gpencil.stroke_separate", text="", icon = "SEPARATE_GP_POINTS").mode = 'POINT'
                col.operator("gpencil.stroke_separate", text="", icon = "SEPARATE_GP_STROKES").mode = 'STROKE'
                col.operator("gpencil.stroke_separate", text="", icon = "SEPARATE_GP_LAYER").mode = 'LAYER'


class VIEW3D_PT_gp_stroketab_stroke(toolshelf_calculate, Panel):
    bl_label = "Stroke"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "greasepencil_edit"
    bl_category = "Stroke"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("gpencil.stroke_subdivide", text="Subdivide", icon = "SUBDIVIDE_EDGES").only_selected = False
            col.operator("gpencil.stroke_trim", text="Trim", icon = "CUT")

            col.separator(factor = 0.5)

            col.operator("gpencil.stroke_join", text="Join", icon = "JOIN").type = 'JOIN'
            col.operator("gpencil.stroke_join", text="Join and Copy", icon = "JOINCOPY").type = 'JOINCOPY'

            col.separator(factor = 0.5)

            col.operator("gpencil.set_active_material", text="Set as Active Material", icon = "MATERIAL")

            col.separator(factor = 0.5)

            # Convert
            op = col.operator("gpencil.stroke_cyclical_set", text="Close", icon = 'TOGGLE_CLOSE')
            op.type = 'CLOSE'
            op.geometry = True
            col.operator("gpencil.stroke_cyclical_set", text="Toggle Cyclic", icon = 'TOGGLE_CYCLIC').type = 'TOGGLE'
            col.operator("gpencil.stroke_flip", text="Switch Direction", icon = "FLIP")
            col.operator("gpencil.stroke_start_set", text="Set Start Point   ", icon = "STARTPOINT")

            col.separator(factor = 0.5)

            col.operator("gpencil.stroke_normalize", text="Normalize Thickness", icon = "MOD_THICKNESS").mode = 'THICKNESS'
            col.operator("gpencil.stroke_normalize", text="Normalize Opacity", icon = "MOD_OPACITY").mode = 'OPACITY'

            col.separator(factor = 0.5)
            col.operator("gpencil.reset_transform_fill", text="Reset Fill Transform", icon = "RESET")
            col.operator("gpencil.stroke_outline", text="Outline", icon="OUTLINE")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("gpencil.stroke_subdivide", text="", icon = "SUBDIVIDE_EDGES").only_selected = False
                row.operator("gpencil.stroke_trim", text="", icon = "CUT")
                row.operator("gpencil.stroke_join", text="", icon = "JOIN").type = 'JOIN'

                row = col.row(align=True)
                row.operator("gpencil.stroke_join", text="", icon = "JOINCOPY").type = 'JOINCOPY'
                row.operator("gpencil.set_active_material", text="", icon = "MATERIAL")
                # Convert
                op = row.operator("gpencil.stroke_cyclical_set", text="", icon = 'TOGGLE_CLOSE')
                op.type = 'CLOSE'
                op.geometry = True

                row = col.row(align=True)
                row.operator("gpencil.stroke_cyclical_set", text="", icon = 'TOGGLE_CYCLIC').type = 'TOGGLE'
                row.operator("gpencil.stroke_flip", text="", icon = "FLIP")
                row.operator("gpencil.stroke_start_set", text="", icon = "STARTPOINT")


                row = col.row(align=True)
                row.operator("gpencil.stroke_normalize", text="", icon = "MOD_THICKNESS").mode = 'THICKNESS'
                row.operator("gpencil.stroke_normalize", text="", icon = "MOD_OPACITY").mode = 'OPACITY'
                row.operator("gpencil.reset_transform_fill", text="", icon = "RESET")

                row = col.row(align=True)
                row.operator("gpencil.stroke_outline", text="", icon="OUTLINE")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("gpencil.stroke_subdivide", text="", icon = "SUBDIVIDE_EDGES").only_selected = False
                row.operator("gpencil.stroke_trim", text="", icon = "CUT")

                row = col.row(align=True)
                row.operator("gpencil.stroke_join", text="", icon = "JOIN").type = 'JOIN'
                row.operator("gpencil.stroke_join", text="", icon = "JOINCOPY").type = 'JOINCOPY'

                row = col.row(align=True)
                row.operator("gpencil.set_active_material", text="", icon = "MATERIAL")
                # Convert
                op = row.operator("gpencil.stroke_cyclical_set", text="", icon = 'TOGGLE_CLOSE')
                op.type = 'CLOSE'
                op.geometry = True

                row = col.row(align=True)
                row.operator("gpencil.stroke_cyclical_set", text="", icon = 'TOGGLE_CYCLIC').type = 'TOGGLE'
                row.operator("gpencil.stroke_flip", text="", icon = "FLIP")

                row = col.row(align=True)
                row.operator("gpencil.stroke_start_set", text="", icon = "STARTPOINT")
                row.operator("gpencil.stroke_normalize", text="", icon = "MOD_THICKNESS").mode = 'THICKNESS'

                row = col.row(align=True)
                row.operator("gpencil.stroke_normalize", text="", icon = "MOD_OPACITY").mode = 'OPACITY'
                row.operator("gpencil.reset_transform_fill", text="", icon = "RESET")

                row = col.row(align=True)
                row.operator("gpencil.stroke_outline", text="", icon="OUTLINE")

            elif column_count == 1:

                col.operator("gpencil.stroke_subdivide", text="", icon = "SUBDIVIDE_EDGES").only_selected = False
                col.operator("gpencil.stroke_trim", text="", icon = "CUT")

                col.separator(factor = 0.5)

                col.operator("gpencil.stroke_join", text="", icon = "JOIN").type = 'JOIN'
                col.operator("gpencil.stroke_join", text="", icon = "JOINCOPY").type = 'JOINCOPY'

                col.separator(factor = 0.5)

                col.operator("gpencil.set_active_material", text="", icon = "MATERIAL")

                col.separator(factor = 0.5)

                # Convert
                op = col.operator("gpencil.stroke_cyclical_set", text="", icon = 'TOGGLE_CLOSE')
                op.type = 'CLOSE'
                op.geometry = True
                col.operator("gpencil.stroke_cyclical_set", text="", icon = 'TOGGLE_CYCLIC').type = 'TOGGLE'
                col.operator("gpencil.stroke_flip", text="", icon = "FLIP")
                col.operator("gpencil.stroke_start_set", text="", icon = "STARTPOINT")

                col.separator(factor = 0.5)

                col.operator("gpencil.stroke_normalize", text="", icon = "MOD_THICKNESS").mode = 'THICKNESS'
                col.operator("gpencil.stroke_normalize", text="", icon = "MOD_OPACITY").mode = 'OPACITY'

                col.separator(factor = 0.5)

                col.operator("gpencil.reset_transform_fill", text="", icon = "RESET")
                col.operator("gpencil.stroke_outline", text="", icon="OUTLINE")


class VIEW3D_PT_gp_stroketab_simplify(toolshelf_calculate, Panel):
    bl_label = "Simplify"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "greasepencil_edit"
    bl_category = "Stroke"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("gpencil.stroke_simplify_fixed", text="Fixed", icon = "MOD_SIMPLIFY")
            col.operator("gpencil.stroke_simplify", text="Adaptative", icon = "SIMPLIFY_ADAPTIVE")
            col.operator("gpencil.stroke_sample", text="Sample", icon = "SIMPLIFY_SAMPLE")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("gpencil.stroke_simplify_fixed", text="", icon = "MOD_SIMPLIFY")
                row.operator("gpencil.stroke_simplify", text="", icon = "SIMPLIFY_ADAPTIVE")
                row.operator("gpencil.stroke_sample", text="", icon = "SIMPLIFY_SAMPLE")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("gpencil.stroke_simplify_fixed", text="", icon = "MOD_SIMPLIFY")
                row.operator("gpencil.stroke_simplify", text="", icon = "SIMPLIFY_ADAPTIVE")

                row = col.row(align=True)
                row.operator("gpencil.stroke_sample", text="", icon = "SIMPLIFY_SAMPLE")

            elif column_count == 1:

                col.operator("gpencil.stroke_simplify_fixed", text="", icon = "MOD_SIMPLIFY")
                col.operator("gpencil.stroke_simplify", text="", icon = "SIMPLIFY_ADAPTIVE")
                col.operator("gpencil.stroke_sample", text="", icon = "SIMPLIFY_SAMPLE")


class VIEW3D_PT_gp_stroketab_togglecaps(toolshelf_calculate, Panel):
    bl_label = "Toggle Caps"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "greasepencil_edit"
    bl_category = "Stroke"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("gpencil.stroke_caps_set", text="Both", icon = "TOGGLECAPS_BOTH").type = 'TOGGLE'
            col.operator("gpencil.stroke_caps_set", text="Start", icon = "TOGGLECAPS_START").type = 'START'
            col.operator("gpencil.stroke_caps_set", text="End", icon = "TOGGLECAPS_END").type = 'END'
            col.operator("gpencil.stroke_caps_set", text="Default", icon = "TOGGLECAPS_DEFAULT").type = 'DEFAULT'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("gpencil.stroke_caps_set", text="", icon = "TOGGLECAPS_BOTH").type = 'TOGGLE'
                row.operator("gpencil.stroke_caps_set", text="", icon = "TOGGLECAPS_START").type = 'START'
                row.operator("gpencil.stroke_caps_set", text="", icon = "TOGGLECAPS_END").type = 'END'

                row = col.row(align=True)
                row.operator("gpencil.stroke_caps_set", text="", icon = "TOGGLECAPS_DEFAULT").type = 'DEFAULT'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("gpencil.stroke_caps_set", text="", icon = "TOGGLECAPS_BOTH").type = 'TOGGLE'
                row.operator("gpencil.stroke_caps_set", text="", icon = "TOGGLECAPS_START").type = 'START'

                row = col.row(align=True)
                row.operator("gpencil.stroke_caps_set", text="", icon = "TOGGLECAPS_END").type = 'END'
                row.operator("gpencil.stroke_caps_set", text="", icon = "TOGGLECAPS_DEFAULT").type = 'DEFAULT'

            elif column_count == 1:

                col.operator("gpencil.stroke_caps_set", text="", icon = "TOGGLECAPS_BOTH").type = 'TOGGLE'
                col.operator("gpencil.stroke_caps_set", text="", icon = "TOGGLECAPS_START").type = 'START'
                col.operator("gpencil.stroke_caps_set", text="", icon = "TOGGLECAPS_END").type = 'END'
                col.operator("gpencil.stroke_caps_set", text="", icon = "TOGGLECAPS_DEFAULT").type = 'DEFAULT'


class VIEW3D_PT_gp_stroketab_reproject(toolshelf_calculate, Panel):
    bl_label = "Reproject Strokes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "greasepencil_edit"
    bl_category = "Stroke"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("gpencil.reproject", text="Front", icon = "VIEW_FRONT").type = 'FRONT'
            col.operator("gpencil.reproject", text="Side", icon = "VIEW_LEFT").type = 'SIDE'
            col.operator("gpencil.reproject", text="Top", icon = "VIEW_TOP").type = 'TOP'
            col.operator("gpencil.reproject", text="View", icon = "VIEW").type = 'VIEW'
            col.operator("gpencil.reproject", text="Surface", icon = "REPROJECT").type = 'SURFACE'
            col.operator("gpencil.reproject", text="Cursor", icon = "CURSOR").type = 'CURSOR'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("gpencil.reproject", text="", icon = "VIEW_FRONT").type = 'FRONT'
                row.operator("gpencil.reproject", text="", icon = "VIEW_LEFT").type = 'SIDE'
                row.operator("gpencil.reproject", text="", icon = "VIEW_TOP").type = 'TOP'

                row = col.row(align=True)
                row.operator("gpencil.reproject", text="", icon = "VIEW").type = 'VIEW'
                row.operator("gpencil.reproject", text="", icon = "REPROJECT").type = 'SURFACE'
                row.operator("gpencil.reproject", text="", icon = "CURSOR").type = 'CURSOR'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("gpencil.reproject", text="", icon = "VIEW_FRONT").type = 'FRONT'
                row.operator("gpencil.reproject", text="", icon = "VIEW_LEFT").type = 'SIDE'

                row = col.row(align=True)
                row.operator("gpencil.reproject", text="", icon = "VIEW_TOP").type = 'TOP'
                row.operator("gpencil.reproject", text="", icon = "VIEW").type = 'VIEW'

                row = col.row(align=True)
                row.operator("gpencil.reproject", text="", icon = "REPROJECT").type = 'SURFACE'
                row.operator("gpencil.reproject", text="", icon = "CURSOR").type = 'CURSOR'

            elif column_count == 1:

                col.operator("gpencil.reproject", text="", icon = "VIEW_FRONT").type = 'FRONT'
                col.operator("gpencil.reproject", text="", icon = "VIEW_LEFT").type = 'SIDE'
                col.operator("gpencil.reproject", text="", icon = "VIEW_TOP").type = 'TOP'
                col.operator("gpencil.reproject", text="", icon = "VIEW").type = 'VIEW'
                col.operator("gpencil.reproject", text="", icon = "REPROJECT").type = 'SURFACE'
                col.operator("gpencil.reproject", text="", icon = "CURSOR").type = 'CURSOR'


class VIEW3D_PT_gp_pointtab_point(toolshelf_calculate, Panel):
    bl_label = "Point"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "greasepencil_edit"
    bl_category = "Point"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("gpencil.extrude_move", text="Extrude", icon = "EXTRUDE_REGION")
            col.operator("gpencil.stroke_smooth", text="Smooth", icon = "PARTICLEBRUSH_SMOOTH").only_selected = True
            col.operator("gpencil.stroke_merge", text="Merge", icon = "MERGE")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("gpencil.extrude_move", text="", icon = "EXTRUDE_REGION")
                row.operator("gpencil.stroke_smooth", text="", icon = "PARTICLEBRUSH_SMOOTH").only_selected = True
                row.operator("gpencil.stroke_merge", text="", icon = "MERGE")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("gpencil.extrude_move", text="", icon = "EXTRUDE_REGION")
                row.operator("gpencil.stroke_smooth", text="", icon = "PARTICLEBRUSH_SMOOTH").only_selected = True

                row = col.row(align=True)
                row.operator("gpencil.stroke_merge", text="", icon = "MERGE")

            elif column_count == 1:

                col.operator("gpencil.extrude_move", text="", icon = "EXTRUDE_REGION")
                col.operator("gpencil.stroke_smooth", text="", icon = "PARTICLEBRUSH_SMOOTH").only_selected = True
                col.operator("gpencil.stroke_merge", text="", icon = "MERGE")


class VIEW3D_PT_gp_drawtab_draw(toolshelf_calculate, Panel):
    bl_label = "Draw"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "greasepencil_paint"
    bl_category = "Draw"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("gpencil.interpolate", text="Interpolate", icon = "INTERPOLATE")
            col.operator("gpencil.interpolate_sequence", text="Interpolate Sequence", icon = "SEQUENCE")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("gpencil.interpolate", text="", icon = "EXTRUDE_REGION")
                row.operator("gpencil.interpolate_sequence", text="", icon = "SEQUENCE")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("gpencil.interpolate", text="", icon = "INTERPOLATE")
                row.operator("gpencil.interpolate_sequence", text="", icon = "SEQUENCE")

            elif column_count == 1:

                col.operator("gpencil.interpolate", text="", icon = "INTERPOLATE")
                col.operator("gpencil.interpolate_sequence", text="", icon = "SEQUENCE")


class VIEW3D_PT_gp_drawtab_animation(toolshelf_calculate, Panel):
    bl_label = "Animation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "greasepencil_paint"
    bl_category = "Animation"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("gpencil.blank_frame_add", text="Insert Blank Keyframe (Active Layer)", icon = "ADD")
            col.operator("gpencil.blank_frame_add", text="Insert Blank Keyframe (All Layers)", icon = "ADD_ALL").all_layers = True

            col.operator("gpencil.frame_duplicate", text="Duplicate Active Keyframe (Active Layer)", icon = "DUPLICATE")
            col.operator("gpencil.frame_duplicate", text="Duplicate Active Keyframe (All Layers)", icon = "DUPLICATE_ALL").mode = 'ALL'

            col.operator("gpencil.delete", text="Delete Active Keyframe (Active Layer)", icon = "DELETE").type = 'FRAME'
            col.operator("gpencil.active_frames_delete_all", text="Delete Active Keyframes (All Layers)", icon = "DELETE_ALL")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("gpencil.blank_frame_add", text="", icon = "ADD")
                row.operator("gpencil.blank_frame_add", text="", icon = "ADD_ALL").all_layers = True

                row = col.row(align=True)
                row.operator("gpencil.frame_duplicate", text="", icon = "DUPLICATE")
                row.operator("gpencil.frame_duplicate", text="", icon = "DUPLICATE_ALL").mode = 'ALL'

                row = col.row(align=True)
                row.operator("gpencil.delete", text="", icon = "DELETE").type = 'FRAME'
                row.operator("gpencil.active_frames_delete_all", text="", icon = "DELETE_ALL")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("gpencil.blank_frame_add", text="", icon = "ADD")
                row.operator("gpencil.blank_frame_add", text="", icon = "ADD_ALL").all_layers = True

                row = col.row(align=True)
                row.operator("gpencil.frame_duplicate", text="", icon = "DUPLICATE")
                row.operator("gpencil.frame_duplicate", text="", icon = "DUPLICATE_ALL").mode = 'ALL'

                row = col.row(align=True)
                row.operator("gpencil.delete", text="", icon = "DELETE").type = 'FRAME'
                row.operator("gpencil.active_frames_delete_all", text="", icon = "DELETE_ALL")

            elif column_count == 1:

                col.operator("gpencil.blank_frame_add", text="", icon = "ADD")
                col.operator("gpencil.blank_frame_add", text="", icon = "ADD_ALL").all_layers = True

                col.operator("gpencil.frame_duplicate", text="", icon = "DUPLICATE")
                col.operator("gpencil.frame_duplicate", text="", icon = "DUPLICATE_ALL").mode = 'ALL'

                col.operator("gpencil.delete", text="", icon = "DELETE").type = 'FRAME'
                col.operator("gpencil.active_frames_delete_all", text="", icon = "DELETE_ALL")


class VIEW3D_PT_gp_drawtab_cleanup(toolshelf_calculate, Panel):
    bl_label = "Clean Up"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "greasepencil_paint"
    bl_category = "Clean Up"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        ob = _context.active_object
        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("gpencil.frame_clean_fill", text="Boundary Strokes", icon = "CLEAN_CHANNELS").mode = 'ACTIVE'
            col.operator("gpencil.frame_clean_fill", text="Boundary Strokes all Frames", icon = "CLEAN_CHANNELS_FRAMES").mode = 'ALL'
            col.operator("gpencil.frame_clean_loose", text="Delete Loose Points", icon = "DELETE_LOOSE")
            col.operator("gpencil.frame_clean_duplicate", text="Delete Duplicated Frames", icon = "DELETE_DUPLICATE")
            col.operator("gpencil.recalc_geometry", text="Recalculate Geometry", icon = "FILE_REFRESH")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("gpencil.frame_clean_fill", text="", icon = "CLEAN_CHANNELS").mode = 'ACTIVE'
                row.operator("gpencil.frame_clean_fill", text="", icon = "CLEAN_CHANNELS_FRAMES").mode = 'ALL'
                row.operator("gpencil.frame_clean_loose", text="", icon = "DELETE_LOOSE")

                row = col.row(align=True)
                row.operator("gpencil.frame_clean_duplicate", text="", icon = "DELETE_DUPLICATE")
                row.operator("gpencil.recalc_geometry", text="", icon = "FILE_REFRESH")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("gpencil.frame_clean_fill", text="", icon = "CLEAN_CHANNELS").mode = 'ACTIVE'
                row.operator("gpencil.frame_clean_fill", text="", icon = "CLEAN_CHANNELS_FRAMES").mode = 'ALL'

                row = col.row(align=True)
                row.operator("gpencil.frame_clean_loose", text="", icon = "DELETE_LOOSE")
                row.operator("gpencil.frame_clean_duplicate", text="", icon = "DELETE_DUPLICATE")

                row = col.row(align=True)
                row.operator("gpencil.recalc_geometry", text="", icon = "FILE_REFRESH")

            elif column_count == 1:

                col.operator("gpencil.frame_clean_fill", text="", icon = "CLEAN_CHANNELS").mode = 'ACTIVE'
                col.operator("gpencil.frame_clean_fill", text="", icon = "CLEAN_CHANNELS_FRAMES").mode = 'ALL'
                col.operator("gpencil.frame_clean_loose", text="", icon = "DELETE_LOOSE")
                col.operator("gpencil.frame_clean_duplicate", text="", icon = "DELETE_DUPLICATE")
                col.operator("gpencil.recalc_geometry", text="", icon = "FILE_REFRESH")


class VIEW3D_PT_gp_weightstab_weights(toolshelf_calculate, Panel):
    bl_label = "Weights"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "greasepencil_weight"
    bl_category = "Weights"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("gpencil.vertex_group_normalize_all", text="Normalize All", icon = "WEIGHT_NORMALIZE_ALL")
            col.operator("gpencil.vertex_group_normalize", text="Normalize", icon = "WEIGHT_NORMALIZE")

            col.separator(factor = 0.5)

            col.operator("gpencil.vertex_group_invert", text="Invert", icon='WEIGHT_INVERT')
            col.operator("gpencil.vertex_group_smooth", text="Smooth", icon='WEIGHT_SMOOTH')

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("gpencil.vertex_group_normalize_all", text="", icon = "WEIGHT_NORMALIZE_ALL")
                row.operator("gpencil.vertex_group_normalize", text="", icon = "WEIGHT_NORMALIZE")
                row.operator("gpencil.vertex_group_invert", text="", icon='WEIGHT_INVERT')

                row = col.row(align=True)
                row.operator("gpencil.vertex_group_smooth", text="", icon='WEIGHT_SMOOTH')

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("gpencil.vertex_group_normalize_all", text="", icon = "WEIGHT_NORMALIZE_ALL")
                row.operator("gpencil.vertex_group_normalize", text="", icon = "WEIGHT_NORMALIZE")

                row = col.row(align=True)
                row.operator("gpencil.vertex_group_invert", text="", icon='WEIGHT_INVERT')
                row.operator("gpencil.vertex_group_smooth", text="", icon='WEIGHT_SMOOTH')

            elif column_count == 1:

                col.operator("gpencil.vertex_group_normalize_all", text="", icon = "WEIGHT_NORMALIZE_ALL")
                col.operator("gpencil.vertex_group_normalize", text="", icon = "WEIGHT_NORMALIZE")

                col.separator(factor = 0.5)

                col.operator("gpencil.vertex_group_invert", text="", icon='WEIGHT_INVERT')
                col.operator("gpencil.vertex_group_smooth", text="", icon='WEIGHT_SMOOTH')


class VIEW3D_PT_gp_weightstab_generate_weights(toolshelf_calculate, Panel):
    bl_label = "Generate Weights"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "greasepencil_weight"
    bl_category = "Weights"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("gpencil.generate_weights", text="With Empty Groups", icon = "PARTICLEBRUSH_WEIGHT").mode = 'NAME'
            col.operator("gpencil.generate_weights", text="With Automatic Weights", icon = "PARTICLEBRUSH_WEIGHT").mode = 'AUTO'


        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("gpencil.generate_weights", text="", icon = "PARTICLEBRUSH_WEIGHT").mode = 'NAME'
                row.operator("gpencil.generate_weights", text="", icon = "PARTICLEBRUSH_WEIGHT").mode = 'AUTO'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("gpencil.generate_weights", text="", icon = "PARTICLEBRUSH_WEIGHT").mode = 'NAME'
                row.operator("gpencil.generate_weights", text="", icon = "PARTICLEBRUSH_WEIGHT").mode = 'AUTO'

            elif column_count == 1:

                col.operator("gpencil.generate_weights", text="", icon = "PARTICLEBRUSH_WEIGHT").mode = 'NAME'
                col.operator("gpencil.generate_weights", text="", icon = "PARTICLEBRUSH_WEIGHT").mode = 'AUTO'


class VIEW3D_PT_gp_painttab_paint(toolshelf_calculate, Panel):
    bl_label = "Paint"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "greasepencil_vertex"
    bl_category = "Paint"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("gpencil.vertex_color_set", text="Set Vertex Colors", icon = "NODE_VERTEX_COLOR")
            col.operator("gpencil.stroke_reset_vertex_color", icon = "RESET")

            col.separator(factor = 0.5)

            col.operator("gpencil.vertex_color_invert", text="Invert", icon = "NODE_INVERT")
            col.operator("gpencil.vertex_color_levels", text="Levels", icon = "LEVELS")
            col.operator("gpencil.vertex_color_hsv", text="Hue Saturation Value", icon = "HUESATVAL")
            col.operator("gpencil.vertex_color_brightness_contrast", text="Bright/Contrast", icon = "BRIGHTNESS_CONTRAST")


        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("gpencil.vertex_color_set", text="", icon = "NODE_VERTEX_COLOR")
                row.operator("gpencil.stroke_reset_vertex_color", text="", icon = "RESET")
                row.operator("gpencil.vertex_color_invert", text="", icon = "NODE_INVERT")

                row = col.row(align=True)
                row.operator("gpencil.vertex_color_levels", text="", icon = "LEVELS")
                row.operator("gpencil.vertex_color_hsv", text="", icon = "HUESATVAL")
                row.operator("gpencil.vertex_color_brightness_contrast", text="", icon = "BRIGHTNESS_CONTRAST")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("gpencil.vertex_color_set", text="", icon = "NODE_VERTEX_COLOR")
                row.operator("gpencil.stroke_reset_vertex_color", text="", icon = "RESET")

                row = col.row(align=True)
                row.operator("gpencil.vertex_color_invert", text="", icon = "NODE_INVERT")
                row.operator("gpencil.vertex_color_levels", text="", icon = "LEVELS")

                row = col.row(align=True)
                row.operator("gpencil.vertex_color_hsv", text="", icon = "HUESATVAL")
                row.operator("gpencil.vertex_color_brightness_contrast", text="", icon = "BRIGHTNESS_CONTRAST")

            elif column_count == 1:

                col.operator("gpencil.vertex_color_set", text="", icon = "NODE_VERTEX_COLOR")
                col.operator("gpencil.stroke_reset_vertex_color", text="", icon = "RESET")

                col.separator(factor = 0.5)

                col.operator("gpencil.vertex_color_invert", text="", icon = "NODE_INVERT")
                col.operator("gpencil.vertex_color_levels", text="", icon = "LEVELS")
                col.operator("gpencil.vertex_color_hsv", text="", icon = "HUESATVAL")
                col.operator("gpencil.vertex_color_brightness_contrast", text="", icon = "BRIGHTNESS_CONTRAST")


class VIEW3D_PT_gp_armaturetab_armature(toolshelf_calculate, Panel):
    bl_label = "Armature"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "armature_edit"
    bl_category = "Armature"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        edit_object = _context.edit_object
        arm = edit_object.data

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("transform.transform", text="Set Bone Roll", icon = "SET_ROLL").mode = 'BONE_ROLL'
            col.operator("armature.roll_clear", text="Clear Bone Roll", icon = "CLEAR_ROLL")

            col.separator(factor = 0.5)

            col.operator("armature.extrude_move", icon = 'EXTRUDE_REGION')

            if arm.use_mirror_x:
                col.operator("armature.extrude_forked", icon = "EXTRUDE_REGION")

            col.operator("armature.duplicate_move", icon = "DUPLICATE")
            col.operator("armature.fill", icon = "FILLBETWEEN")

            col.separator(factor = 0.5)

            col.operator("armature.split", icon = "SPLIT")
            col.operator("armature.separate", icon = "SEPARATE")
            col.operator("armature.symmetrize", icon = "SYMMETRIZE")

            col.separator(factor = 0.5)

            col.operator("armature.subdivide", text="Subdivide", icon = 'SUBDIVIDE_EDGES')
            col.operator("armature.switch_direction", text="Switch Direction", icon = "SWITCH_DIRECTION")

            col.separator(factor = 0.5)

            col.operator_context = 'INVOKE_REGION_WIN'
            col.operator("armature.armature_layers", icon = "LAYER")
            col.operator("armature.bone_layers", icon = "BONE_LAYER")

            col.separator(factor = 0.5)

            col.operator_context = 'EXEC_REGION_WIN'
            col.operator("armature.parent_set", text="Make Parent", icon='PARENT_SET')
            col.operator("armature.parent_clear", text="Clear Parent", icon='PARENT_CLEAR')


        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("transform.transform", text="", icon = "SET_ROLL").mode = 'BONE_ROLL'
                row.operator("armature.roll_clear", text="", icon = "CLEAR_ROLL")
                row.operator("armature.extrude_move", text="", icon = 'EXTRUDE_REGION')

                row = col.row(align=True)
                if arm.use_mirror_x:
                    row.operator("armature.extrude_forked", text="", icon = "EXTRUDE_REGION")
                row.operator("armature.duplicate_move", text="", icon = "DUPLICATE")
                row.operator("armature.fill", text="", icon = "FILLBETWEEN")

                row = col.row(align=True)
                row.operator("armature.split", text="", icon = "SPLIT")
                row.operator("armature.separate", text="", icon = "SEPARATE")
                row.operator("armature.symmetrize", text="", icon = "SYMMETRIZE")

                row = col.row(align=True)
                row.operator("armature.subdivide", text="", icon = 'SUBDIVIDE_EDGES')
                row.operator("armature.switch_direction", text="", icon = "SWITCH_DIRECTION")
                row.operator_context = 'INVOKE_REGION_WIN'
                row.operator("armature.armature_layers", text="", icon = "LAYER")

                row = col.row(align=True)
                row.operator("armature.bone_layers", text="", icon = "BONE_LAYER")
                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("armature.parent_set", text="", icon='PARENT_SET')
                row.operator("armature.parent_clear", text="", icon='PARENT_CLEAR')

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("transform.transform", text="", icon = "SET_ROLL").mode = 'BONE_ROLL'
                row.operator("armature.roll_clear", text="", icon = "CLEAR_ROLL")

                row = col.row(align=True)
                row.operator("armature.extrude_move", text="", icon = 'EXTRUDE_REGION')
                if arm.use_mirror_x:
                    row.operator("armature.extrude_forked", text="", icon = "EXTRUDE_REGION")

                row = col.row(align=True)
                row.operator("armature.duplicate_move", text="", icon = "DUPLICATE")
                row.operator("armature.fill", text="", icon = "FILLBETWEEN")

                row = col.row(align=True)
                row.operator("armature.split", text="", icon = "SPLIT")
                row.operator("armature.separate", text="", icon = "SEPARATE")

                row = col.row(align=True)
                row.operator("armature.symmetrize", text="", icon = "SYMMETRIZE")
                row.operator("armature.subdivide", text="", icon = 'SUBDIVIDE_EDGES')

                row = col.row(align=True)
                row.operator("armature.switch_direction", text="", icon = "SWITCH_DIRECTION")
                row.operator_context = 'INVOKE_REGION_WIN'
                row.operator("armature.armature_layers", text="", icon = "LAYER")

                row = col.row(align=True)
                row.operator("armature.bone_layers", text="", icon = "BONE_LAYER")
                row.operator_context = 'EXEC_REGION_WIN'
                row.operator("armature.parent_set", text="", icon='PARENT_SET')

                row = col.row(align=True)
                row.operator("armature.parent_clear", text="", icon='PARENT_CLEAR')

            elif column_count == 1:

                col.operator("transform.transform", text="", icon = "SET_ROLL").mode = 'BONE_ROLL'
                col.operator("armature.roll_clear", text="", icon = "CLEAR_ROLL")

                col.separator(factor = 0.5)

                col.operator("armature.extrude_move", text="", icon = 'EXTRUDE_REGION')

                if arm.use_mirror_x:
                    col.operator("armature.extrude_forked", text="", icon = "EXTRUDE_REGION")

                col.operator("armature.duplicate_move", text="", icon = "DUPLICATE")
                col.operator("armature.fill", text="", icon = "FILLBETWEEN")

                col.separator(factor = 0.5)

                col.operator("armature.split", text="", icon = "SPLIT")
                col.operator("armature.separate", text="", icon = "SEPARATE")
                col.operator("armature.symmetrize", text="", icon = "SYMMETRIZE")

                col.separator(factor = 0.5)

                col.operator("armature.subdivide", text="", icon = 'SUBDIVIDE_EDGES')
                col.operator("armature.switch_direction", text="", icon = "SWITCH_DIRECTION")

                col.separator(factor = 0.5)

                col.operator_context = 'INVOKE_REGION_WIN'
                col.operator("armature.armature_layers", text="", icon = "LAYER")
                col.operator("armature.bone_layers", text="", icon = "BONE_LAYER")

                col.separator(factor = 0.5)

                col.operator_context = 'EXEC_REGION_WIN'
                col.operator("armature.parent_set", text="", icon='PARENT_SET')
                col.operator("armature.parent_clear", text="", icon='PARENT_CLEAR')


class VIEW3D_PT_gp_armaturetab_recalcboneroll(toolshelf_calculate, Panel):
    bl_label = "Recalculate Bone Roll"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "armature_edit"
    bl_category = "Armature"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        edit_object = _context.edit_object
        arm = edit_object.data

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.label(text="- Positive: -")
            col.operator("armature.calculate_roll", text= "Local + X Tangent", icon = "ROLL_X_TANG_POS").type = 'POS_X'
            col.operator("armature.calculate_roll", text= "Local + Z Tangent", icon = "ROLL_Z_TANG_POS").type = 'POS_Z'
            col.operator("armature.calculate_roll", text= "Global + X Axis", icon = "ROLL_X_POS").type = 'GLOBAL_POS_X'
            col.operator("armature.calculate_roll", text= "Global + Y Axis", icon = "ROLL_Y_POS").type = 'GLOBAL_POS_Y'
            col.operator("armature.calculate_roll", text= "Global + Z Axis", icon = "ROLL_Z_POS").type = 'GLOBAL_POS_Z'

            col.separator(factor = 0.5)

            col.label(text="- Negative: -")
            col.operator("armature.calculate_roll", text= "Local - X Tangent", icon = "ROLL_X_TANG_NEG").type = 'NEG_X'
            col.operator("armature.calculate_roll", text= "Local - Z Tangent", icon = "ROLL_Z_TANG_NEG").type = 'NEG_Z'
            col.operator("armature.calculate_roll", text= "Global - X Axis", icon = "ROLL_X_NEG").type = 'GLOBAL_NEG_X'
            col.operator("armature.calculate_roll", text= "Global - Y Axis", icon = "ROLL_Y_NEG").type = 'GLOBAL_NEG_Y'
            col.operator("armature.calculate_roll", text= "Global - Z Axis", icon = "ROLL_Z_NEG").type = 'GLOBAL_NEG_Z'

            col.separator(factor = 0.5)

            col.label(text="- Other: -")
            col.operator("armature.calculate_roll", text= "Active Bone", icon = "BONE_DATA").type = 'ACTIVE'
            col.operator("armature.calculate_roll", text= "View Axis", icon = "MANIPUL").type = 'VIEW'
            col.operator("armature.calculate_roll", text= "Cursor", icon = "CURSOR").type = 'CURSOR'


        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                col.label(text="- Positive: -")
                row = col.row(align=True)
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_X_TANG_POS").type = 'POS_X'
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_Z_TANG_POS").type = 'POS_Z'
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_X_POS").type = 'GLOBAL_POS_X'

                row = col.row(align=True)
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_Y_POS").type = 'GLOBAL_POS_Y'
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_Z_POS").type = 'GLOBAL_POS_Z'

                col = layout.column(align=True)
                col.scale_x = 2
                col.scale_y = 2

                col.label(text="- Negative: -")
                row = col.row(align=True)
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_X_TANG_NEG").type = 'NEG_X'
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_Z_TANG_NEG").type = 'NEG_Z'
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_X_NEG").type = 'GLOBAL_NEG_X'

                row = col.row(align=True)
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_Y_NEG").type = 'GLOBAL_NEG_Y'
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_Z_NEG").type = 'GLOBAL_NEG_Z'

                col = layout.column(align=True)
                col.scale_x = 2
                col.scale_y = 2

                col.label(text="- Other: -")
                row = col.row(align=True)
                row.operator("armature.calculate_roll", text= "", icon = "BONE_DATA").type = 'ACTIVE'
                row.operator("armature.calculate_roll", text= "", icon = "MANIPUL").type = 'VIEW'
                row.operator("armature.calculate_roll", text= "", icon = "CURSOR").type = 'CURSOR'

            elif column_count == 2:

                col.label(text="- Positive: -")
                row = col.row(align=True)
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_X_TANG_POS").type = 'POS_X'
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_Z_TANG_POS").type = 'POS_Z'

                row = col.row(align=True)
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_X_POS").type = 'GLOBAL_POS_X'
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_Y_POS").type = 'GLOBAL_POS_Y'

                row = col.row(align=True)
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_Z_POS").type = 'GLOBAL_POS_Z'

                col = layout.column(align=True)
                col.scale_x = 2
                col.scale_y = 2

                col.label(text="- Negative: -")
                row = col.row(align=True)
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_X_TANG_NEG").type = 'NEG_X'
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_Z_TANG_NEG").type = 'NEG_Z'

                row = col.row(align=True)
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_X_NEG").type = 'GLOBAL_NEG_X'
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_Y_NEG").type = 'GLOBAL_NEG_Y'

                row = col.row(align=True)
                row.operator("armature.calculate_roll", text= "", icon = "ROLL_Z_NEG").type = 'GLOBAL_NEG_Z'

                col = layout.column(align=True)
                col.scale_x = 2
                col.scale_y = 2

                col.label(text="- Other: -")
                row = col.row(align=True)
                row.operator("armature.calculate_roll", text= "", icon = "BONE_DATA").type = 'ACTIVE'
                row.operator("armature.calculate_roll", text= "", icon = "MANIPUL").type = 'VIEW'

                row = col.row(align=True)
                row.operator("armature.calculate_roll", text= "", icon = "CURSOR").type = 'CURSOR'

            elif column_count == 1:

                col.label(text="- Positive: -")
                col.operator("armature.calculate_roll", text= "", icon = "ROLL_X_TANG_POS").type = 'POS_X'
                col.operator("armature.calculate_roll", text= "", icon = "ROLL_Z_TANG_POS").type = 'POS_Z'
                col.operator("armature.calculate_roll", text= "", icon = "ROLL_X_POS").type = 'GLOBAL_POS_X'
                col.operator("armature.calculate_roll", text= "", icon = "ROLL_Y_POS").type = 'GLOBAL_POS_Y'
                col.operator("armature.calculate_roll", text= "", icon = "ROLL_Z_POS").type = 'GLOBAL_POS_Z'

                col.separator(factor = 0.5)

                col.label(text="- Negative: -")
                col.operator("armature.calculate_roll", text= "", icon = "ROLL_X_TANG_NEG").type = 'NEG_X'
                col.operator("armature.calculate_roll", text= "", icon = "ROLL_Z_TANG_NEG").type = 'NEG_Z'
                col.operator("armature.calculate_roll", text= "", icon = "ROLL_X_NEG").type = 'GLOBAL_NEG_X'
                col.operator("armature.calculate_roll", text= "", icon = "ROLL_Y_NEG").type = 'GLOBAL_NEG_Y'
                col.operator("armature.calculate_roll", text= "", icon = "ROLL_Z_NEG").type = 'GLOBAL_NEG_Z'

                col.separator(factor = 0.5)

                col.label(text="- Other: -")
                col.operator("armature.calculate_roll", text= "", icon = "BONE_DATA").type = 'ACTIVE'
                col.operator("armature.calculate_roll", text= "", icon = "MANIPUL").type = 'VIEW'
                col.operator("armature.calculate_roll", text= "", icon = "CURSOR").type = 'CURSOR'


class VIEW3D_PT_gp_armaturetab_names(toolshelf_calculate, Panel):
    bl_label = "Names"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "armature_edit"
    bl_category = "Armature"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator_context = 'EXEC_REGION_WIN'
            col.operator("armature.autoside_names", text="Auto-Name Left/Right", icon = "RENAME_X").type = 'XAXIS'
            col.operator("armature.autoside_names", text="Auto-Name Front/Back", icon = "RENAME_Y").type = 'YAXIS'
            col.operator("armature.autoside_names", text="Auto-Name Top/Bottom", icon = "RENAME_Z").type = 'ZAXIS'
            col.operator("armature.flip_names", icon = "FLIP")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                col.operator_context = 'EXEC_REGION_WIN'

                row = col.row(align=True)
                row.operator("armature.autoside_names", text="", icon = "RENAME_X").type = 'XAXIS'
                row.operator("armature.autoside_names", text="", icon = "RENAME_Y").type = 'YAXIS'
                row.operator("armature.autoside_names", text="", icon = "RENAME_Z").type = 'ZAXIS'

                row = col.row(align=True)
                row.operator("armature.flip_names", text="", icon = "FLIP")

            elif column_count == 2:

                col.operator_context = 'EXEC_REGION_WIN'

                row = col.row(align=True)
                row.operator("armature.autoside_names", text="", icon = "RENAME_X").type = 'XAXIS'
                row.operator("armature.autoside_names", text="", icon = "RENAME_Y").type = 'YAXIS'

                row = col.row(align=True)
                row.operator("armature.autoside_names", text="", icon = "RENAME_Z").type = 'ZAXIS'
                row.operator("armature.flip_names", text="", icon = "FLIP")

            elif column_count == 1:

                col.operator_context = 'EXEC_REGION_WIN'
                col.operator("armature.autoside_names", text="", icon = "RENAME_X").type = 'XAXIS'
                col.operator("armature.autoside_names", text="", icon = "RENAME_Y").type = 'YAXIS'
                col.operator("armature.autoside_names", text="", icon = "RENAME_Z").type = 'ZAXIS'
                col.operator("armature.flip_names", text="", icon = "FLIP")



class VIEW3D_PT_gp_posetab_pose(toolshelf_calculate, Panel):
    bl_label = "Pose"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("pose.quaternions_flip", icon = "FLIP")

            col.separator( factor = 0.5)

            col.operator_context = 'INVOKE_AREA'
            col.operator("armature.armature_layers", text="Change Armature Layers", icon = "LAYER")
            col.operator("pose.bone_layers", text="Change Bone Layers", icon = "BONE_LAYER")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("pose.quaternions_flip", text="", icon = "FLIP")
                row.operator_context = 'INVOKE_AREA'
                row.operator("armature.armature_layers", text="", icon = "LAYER")
                row.operator("pose.bone_layers", text="", icon = "BONE_LAYER")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("pose.quaternions_flip", text="", icon = "FLIP")
                row.operator_context = 'INVOKE_AREA'
                row.operator("armature.armature_layers", text="", icon = "BONE_LAYER")

                row = col.row(align=True)
                row.operator("pose.bone_layers", text="", icon = "LAYER")

            elif column_count == 1:

                col.operator("pose.quaternions_flip", text="", icon = "FLIP")

                col.separator( factor = 0.5)

                col.operator_context = 'INVOKE_AREA'
                col.operator("armature.armature_layers", text="", icon = "LAYER")
                col.operator("pose.bone_layers", text="", icon = "BONE_LAYER")


class VIEW3D_PT_gp_posetab_cleartransform(toolshelf_calculate, Panel):
    bl_label = "Clear Transform"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("pose.transforms_clear", text="All", icon = "CLEAR")
            col.operator("pose.user_transforms_clear", icon = "NODE_TRANSFORM_CLEAR")

            col.separator(factor = 0.5)

            col.operator("pose.loc_clear", text="Location", icon = "CLEARMOVE")
            col.operator("pose.rot_clear", text="Rotation", icon = "CLEARROTATE")
            col.operator("pose.scale_clear", text="Scale", icon = "CLEARSCALE")

            col.separator(factor = 0.5)

            col.operator("pose.user_transforms_clear", text="Reset Unkeyed", icon = "RESET")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("pose.transforms_clear", text="", icon = "CLEAR")
                row.operator("pose.user_transforms_clear", text="", icon = "NODE_TRANSFORM_CLEAR")
                row.operator("pose.loc_clear", text="", icon = "CLEARMOVE")

                row = col.row(align=True)
                row.operator("pose.rot_clear", text="", icon = "CLEARROTATE")
                row.operator("pose.scale_clear", text="", icon = "CLEARSCALE")
                row.operator("pose.user_transforms_clear", text="", icon = "RESET")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("pose.transforms_clear", text="", icon = "CLEAR")
                row.operator("pose.user_transforms_clear", text="", icon = "NODE_TRANSFORM_CLEAR")

                row = col.row(align=True)
                row.operator("pose.loc_clear", text="", icon = "CLEARMOVE")
                row.operator("pose.rot_clear", text="", icon = "CLEARROTATE")

                row = col.row(align=True)
                row.operator("pose.scale_clear", text="", icon = "CLEARSCALE")
                row.operator("pose.user_transforms_clear", text="", icon = "RESET")

            elif column_count == 1:

                col.operator("pose.transforms_clear", text="", icon = "CLEAR")
                col.operator("pose.user_transforms_clear", text="", icon = "NODE_TRANSFORM_CLEAR")

                col.separator(factor = 0.5)

                col.operator("pose.loc_clear", text="", icon = "CLEARMOVE")
                col.operator("pose.rot_clear", text="", icon = "CLEARROTATE")
                col.operator("pose.scale_clear", text="", icon = "CLEARSCALE")

                col.separator(factor = 0.5)

                col.operator("pose.user_transforms_clear", text="", icon = "RESET")


class VIEW3D_PT_gp_posetab_apply(toolshelf_calculate, Panel):
    bl_label = "Apply"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("pose.armature_apply", icon = "MOD_ARMATURE")
            col.operator("pose.armature_apply", text="Apply Selected as Rest Pose", icon = "MOD_ARMATURE_SELECTED").selected = True
            col.operator("pose.visual_transform_apply", icon = "APPLYMOVE")

            col.separator( factor = 0.5)

            props = col.operator("object.assign_property_defaults", icon = "ASSIGN")
            props.process_bones = True

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("pose.armature_apply", text="", icon = "MOD_ARMATURE")
                row.operator("pose.armature_apply", text="", icon = "MOD_ARMATURE_SELECTED").selected = True
                row.operator("pose.visual_transform_apply", text="", icon = "APPLYMOVE")
                props = row.operator("object.assign_property_defaults", text="", icon = "ASSIGN")
                props.process_bones = True

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("pose.armature_apply", text="", icon = "MOD_ARMATURE")
                row.operator("pose.armature_apply", text="", icon = "MOD_ARMATURE_SELECTED").selected = True

                row = col.row(align=True)
                row.operator("pose.visual_transform_apply", text="", icon = "APPLYMOVE")
                props = row.operator("object.assign_property_defaults", text="", icon = "ASSIGN")
                props.process_bones = True

            elif column_count == 1:

                col.operator("pose.armature_apply", text="", icon = "MOD_ARMATURE")
                col.operator("pose.armature_apply", text="", icon = "MOD_ARMATURE_SELECTED").selected = True
                col.operator("pose.visual_transform_apply", text="", icon = "APPLYMOVE")

                col.separator( factor = 0.5)

                props = col.operator("object.assign_property_defaults", text="", icon = "ASSIGN")
                props.process_bones = True


class VIEW3D_PT_gp_posetab_inbetweens(toolshelf_calculate, Panel):
    bl_label = "In-Betweens"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("pose.push_rest", icon = 'PUSH_POSE')
            col.operator("pose.relax_rest", icon = 'RELAX_POSE')
            col.operator("pose.push", icon = 'POSE_FROM_BREAKDOWN')
            col.operator("pose.relax", icon = 'POSE_RELAX_TO_BREAKDOWN')
            col.operator("pose.breakdown", icon = 'BREAKDOWNER_POSE')
            col.operator("pose.blend_to_neighbor", icon = 'BLEND_TO_NEIGHBOUR')


        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("pose.push_rest", text = "", icon = 'PUSH_POSE')
                row.operator("pose.relax_rest", text = "", icon = 'RELAX_POSE')
                row.operator("pose.push", text = "", icon = 'POSE_FROM_BREAKDOWN')

                row = col.row(align=True)
                row.operator("pose.relax", text = "", icon = 'POSE_RELAX_TO_BREAKDOWN')
                row.operator("pose.breakdown", text = "", icon = 'BREAKDOWNER_POSE')
                row.operator("pose.blend_to_neighbor", text = "", icon = 'BLEND_TO_NEIGHBOUR')

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("pose.push_rest", text = "", icon = 'PUSH_POSE')
                row.operator("pose.relax_rest", text = "", icon = 'RELAX_POSE')

                row = col.row(align=True)
                row.operator("pose.push", text = "", icon = 'POSE_FROM_BREAKDOWN')
                row.operator("pose.relax", text = "", icon = 'POSE_RELAX_TO_BREAKDOWN')

                row = col.row(align=True)
                row.operator("pose.breakdown", text = "", icon = 'BREAKDOWNER_POSE')
                row.operator("pose.blend_to_neighbor", text = "", icon = 'BLEND_TO_NEIGHBOUR')

            elif column_count == 1:

                col.operator("pose.push_rest", text = "", icon = 'PUSH_POSE')
                col.operator("pose.relax_rest", text = "", icon = 'RELAX_POSE')
                col.operator("pose.push", text = "", icon = 'POSE_FROM_BREAKDOWN')
                col.operator("pose.relax", text = "", icon = 'POSE_RELAX_TO_BREAKDOWN')
                col.operator("pose.breakdown", text = "", icon = 'BREAKDOWNER_POSE')
                col.operator("pose.blend_to_neighbor", text = "", icon = 'BLEND_TO_NEIGHBOUR')


class VIEW3D_PT_gp_posetab_propagate(toolshelf_calculate, Panel):
    bl_label = "Propagate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("pose.propagate", icon = "PROPAGATE").mode = 'WHILE_HELD'

            col.separator(factor = 0.5)

            col.operator("pose.propagate", text="To Next Keyframe", icon = "PROPAGATE_NEXT").mode = 'NEXT_KEY'
            col.operator("pose.propagate", text="To Last Keyframe (Make Cyclic)", icon = "PROPAGATE_PREVIOUS").mode = 'LAST_KEY'

            col.separator(factor = 0.5)

            col.operator("pose.propagate", text="On Selected Keyframes", icon = "PROPAGATE_SELECTED").mode = 'SELECTED_KEYS'

            col.separator(factor = 0.5)

            col.operator("pose.propagate", text="On Selected Markers", icon = "PROPAGATE_MARKER").mode = 'SELECTED_MARKERS'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("pose.propagate", text="", icon = "PROPAGATE").mode = 'WHILE_HELD'
                row.operator("pose.propagate", text="", icon = "PROPAGATE_NEXT").mode = 'NEXT_KEY'
                row.operator("pose.propagate", text="", icon = "PROPAGATE_PREVIOUS").mode = 'LAST_KEY'

                row = col.row(align=True)
                row.operator("pose.propagate", text="", icon = "PROPAGATE_SELECTED").mode = 'SELECTED_KEYS'
                row.operator("pose.propagate", text="", icon = "PROPAGATE_MARKER").mode = 'SELECTED_MARKERS'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("pose.propagate", text="", icon = "PROPAGATE").mode = 'WHILE_HELD'
                row.operator("pose.propagate", text="", icon = "PROPAGATE_NEXT").mode = 'NEXT_KEY'

                row = col.row(align=True)
                row.operator("pose.propagate", text="", icon = "PROPAGATE_PREVIOUS").mode = 'LAST_KEY'
                row.operator("pose.propagate", text="", icon = "PROPAGATE_SELECTED").mode = 'SELECTED_KEYS'

                row = col.row(align=True)
                row.operator("pose.propagate", text="", icon = "PROPAGATE_MARKER").mode = 'SELECTED_MARKERS'

            elif column_count == 1:

                col.operator("pose.propagate", text="", icon = "PROPAGATE").mode = 'WHILE_HELD'

                col.separator(factor = 0.5)

                col.operator("pose.propagate", text="", icon = "PROPAGATE_NEXT").mode = 'NEXT_KEY'
                col.operator("pose.propagate", text="", icon = "PROPAGATE_PREVIOUS").mode = 'LAST_KEY'

                col.separator(factor = 0.5)

                col.operator("pose.propagate", text="", icon = "PROPAGATE_SELECTED").mode = 'SELECTED_KEYS'

                col.separator(factor = 0.5)

                col.operator("pose.propagate", text="", icon = "PROPAGATE_MARKER").mode = 'SELECTED_MARKERS'


class VIEW3D_PT_gp_posetab_poselibrary(toolshelf_calculate, Panel):
    bl_label = "Pose Library"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("poselib.browse_interactive", text="Browse Poses", icon = "FILEBROWSER")

            col.separator(factor = 0.5)

            col.operator("poselib.pose_add", text="Add Pose", icon = "LIBRARY")
            col.operator("poselib.pose_rename", text="Rename Pose", icon='RENAME')
            col.operator("poselib.pose_remove", text="Remove Pose", icon = "DELETE")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("poselib.browse_interactive", text="", icon = "FILEBROWSER")
                row.operator("poselib.pose_add", text="", icon = "LIBRARY")
                row.operator("poselib.pose_rename", text="", icon='RENAME')

                row = col.row(align=True)
                row.operator("poselib.pose_remove", text="", icon = "DELETE")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("poselib.browse_interactive", text="", icon = "FILEBROWSER")
                row.operator("poselib.pose_add", text="", icon = "LIBRARY")

                row = col.row(align=True)
                row.operator("poselib.pose_rename", text="", icon='RENAME')
                row.operator("poselib.pose_remove", text="", icon = "DELETE")

            elif column_count == 1:

                col.operator("poselib.browse_interactive", text="", icon = "FILEBROWSER")

                col.separator(factor = 0.5)

                col.operator("poselib.pose_add", text="", icon = "LIBRARY")
                col.operator("poselib.pose_rename", text="", icon='RENAME')
                col.operator("poselib.pose_remove", text="", icon = "DELETE")


class VIEW3D_PT_gp_posetab_motionpaths(toolshelf_calculate, Panel):
    bl_label = "Motion Paths"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("pose.paths_calculate", text="Calculate", icon ='MOTIONPATHS_CALCULATE')
            col.operator("pose.paths_clear", text="Clear", icon ='MOTIONPATHS_CLEAR')
            col.operator("pose.paths_update", text="Update Armature Motion Paths", icon = "MOTIONPATHS_UPDATE")
            col.operator("object.paths_update_visible", text="Update All Motion Paths", icon = "MOTIONPATHS_UPDATE_ALL")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("pose.paths_calculate", text="", icon ='MOTIONPATHS_CALCULATE')
                row.operator("pose.paths_clear", text="", icon ='MOTIONPATHS_CLEAR')

                row = col.row(align=True)
                row.operator("pose.paths_update", text="", icon = "MOTIONPATHS_UPDATE")
                row.operator("object.paths_update_visible", text="", icon = "MOTIONPATHS_UPDATE_ALL")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("pose.paths_calculate", text="", icon ='MOTIONPATHS_CALCULATE')
                row.operator("pose.paths_clear", text="", icon ='MOTIONPATHS_CLEAR')
                row = col.row(align=True)
                row.operator("pose.paths_update", text="", icon = "MOTIONPATHS_UPDATE")
                row.operator("object.paths_update_visible", text="", icon = "MOTIONPATHS_UPDATE_ALL")

            elif column_count == 1:

                col.operator("pose.paths_calculate", text="", icon ='MOTIONPATHS_CALCULATE')
                col.operator("pose.paths_clear", text="", icon ='MOTIONPATHS_CLEAR')
                col.operator("pose.paths_update", text="", icon = "MOTIONPATHS_UPDATE")
                col.operator("object.paths_update_visible", text="", icon = "MOTIONPATHS_UPDATE_ALL")


class VIEW3D_PT_gp_posetab_ik(toolshelf_calculate, Panel):
    bl_label = "IK"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("pose.ik_add", icon= "ADD_IK")
            col.operator("pose.ik_clear", icon = "CLEAR_IK")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("pose.ik_add", text = "", icon= "ADD_IK")
                row.operator("pose.ik_clear", text = "", icon = "CLEAR_IK")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("pose.ik_add", text = "", icon= "ADD_IK")
                row.operator("pose.ik_clear", text = "", icon = "CLEAR_IK")

            elif column_count == 1:

                col.operator("pose.ik_add", text = "", icon= "ADD_IK")
                col.operator("pose.ik_clear", text = "", icon = "CLEAR_IK")


class VIEW3D_PT_gp_posetab_constraints(toolshelf_calculate, Panel):
    bl_label = "Constraints"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("pose.constraint_add_with_targets", icon = "CONSTRAINT_DATA")
            col.operator("pose.constraints_copy", icon = "COPYDOWN")

            col.separator(factor = 0.5)

            col.operator("pose.constraints_clear", icon = "CLEAR_CONSTRAINT")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("pose.constraint_add_with_targets", text = "", icon = "CONSTRAINT_DATA")
                row.operator("pose.constraints_copy", text = "", icon = "COPYDOWN")
                row.operator("pose.constraints_clear", text = "", icon = "CLEAR_CONSTRAINT")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("pose.constraint_add_with_targets", text = "", icon = "CONSTRAINT_DATA")
                row.operator("pose.constraints_copy", text = "", icon = "COPYDOWN")

                row = col.row(align=True)
                row.operator("pose.constraints_clear", text = "", icon = "CLEAR_CONSTRAINT")


            elif column_count == 1:

                col.operator("pose.constraint_add_with_targets", text = "", icon = "CONSTRAINT_DATA")
                col.operator("pose.constraints_copy", text = "", icon = "COPYDOWN")

                col.separator(factor = 0.5)

                col.operator("pose.constraints_clear", text = "", icon = "CLEAR_CONSTRAINT")


class VIEW3D_PT_gp_posetab_names(toolshelf_calculate, Panel):
    bl_label = "Names"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator_context = 'EXEC_REGION_WIN'
            col.operator("pose.autoside_names", text="Auto-Name Left/Right", icon = "RENAME_X").axis = 'XAXIS'
            col.operator("pose.autoside_names", text="Auto-Name Front/Back", icon = "RENAME_Y").axis = 'YAXIS'
            col.operator("pose.autoside_names", text="Auto-Name Top/Bottom", icon = "STRING").axis = 'ZAXIS'
            col.operator("pose.flip_names", icon = "FLIP")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                col.operator_context = 'EXEC_REGION_WIN'

                row = col.row(align=True)
                row.operator("pose.autoside_names", text="", icon = "RENAME_X").axis = 'XAXIS'
                row.operator("pose.autoside_names", text="", icon = "RENAME_Y").axis = 'YAXIS'
                row.operator("pose.autoside_names", text="", icon = "RENAME_Z").axis = 'ZAXIS'

                row = col.row(align=True)
                row.operator("pose.flip_names", text="", icon = "FLIP")

            elif column_count == 2:

                col.operator_context = 'EXEC_REGION_WIN'

                row = col.row(align=True)
                row.operator("pose.autoside_names", text="", icon = "RENAME_X").axis = 'XAXIS'
                row.operator("pose.autoside_names", text="", icon = "RENAME_Y").axis = 'YAXIS'

                row = col.row(align=True)
                row.operator("pose.autoside_names", text="", icon = "RENAME_Z").axis = 'ZAXIS'
                row.operator("pose.flip_names", text="", icon = "FLIP")

            elif column_count == 1:

                col.operator_context = 'EXEC_REGION_WIN'
                col.operator("pose.autoside_names", text="", icon = "RENAME_X").axis = 'XAXIS'
                col.operator("pose.autoside_names", text="", icon = "RENAME_Y").axis = 'YAXIS'
                col.operator("pose.autoside_names", text="", icon = "RENAME_Z").axis = 'ZAXIS'
                col.operator("pose.flip_names", text="", icon = "FLIP")


classes = (

    #object menu
    VIEW3D_PT_objecttab_transform,
    VIEW3D_PT_objecttab_set_origin,
    VIEW3D_PT_objecttab_mirror,
    VIEW3D_PT_objecttab_mirror_local,
    VIEW3D_PT_objecttab_clear,
    VIEW3D_PT_objecttab_apply,
    VIEW3D_PT_objecttab_apply_delta,
    VIEW3D_PT_objecttab_snap,
    VIEW3D_PT_objecttab_shading,

    #mesh menu
    VIEW3D_PT_meshtab_merge,
    VIEW3D_PT_meshtab_split,
    VIEW3D_PT_meshtab_separate,
    VIEW3D_PT_meshtab_tools,
    VIEW3D_PT_meshtab_normals,
    VIEW3D_PT_meshtab_shading,
    VIEW3D_PT_meshtab_cleanup,
    VIEW3D_PT_meshtab_dissolve,

    #mesh edit mode
    VIEW3D_PT_vertextab_vertex,
    VIEW3D_PT_edgetab_Edge,
    VIEW3D_PT_facetab_face,
    VIEW3D_PT_uvtab_uv,

    #mesh sculpt mode
    VIEW3D_PT_masktab_mask,
    VIEW3D_PT_masktab_random_mask,
    VIEW3D_PT_facesetstab_facesets,
    VIEW3D_PT_facesetstab_init_facesets,

    #mesh vertex paint mode
    VIEW3D_PT_painttab_paint,
    VIEW3D_PT_painttab_colorpicker,

    #mesh weight paint mode
    VIEW3D_PT_weightstab_weights,

    #curve edit mode
    VIEW3D_PT_curvetab_curve,
    VIEW3D_PT_curvetab_controlpoints,
    VIEW3D_PT_surfacetab_surface,
    VIEW3D_PT_curvetab_controlpoints_surface,
    VIEW3D_PT_segmentstab_segments,

    # grease pencil edit mode
    VIEW3D_PT_gp_gpenciltab_dissolve,
    VIEW3D_PT_gp_gpenciltab_cleanup,
    VIEW3D_PT_gp_gpenciltab_separate,
    VIEW3D_PT_gp_stroketab_stroke,
    VIEW3D_PT_gp_stroketab_simplify,
    VIEW3D_PT_gp_stroketab_togglecaps,
    VIEW3D_PT_gp_stroketab_reproject,
    VIEW3D_PT_gp_pointtab_point,

    # grease pencil draw mode
    VIEW3D_PT_gp_drawtab_draw,
    VIEW3D_PT_gp_drawtab_animation,
    VIEW3D_PT_gp_drawtab_cleanup,

    # grease pencil weights mode
    VIEW3D_PT_gp_weightstab_weights,
    VIEW3D_PT_gp_weightstab_generate_weights,

    # grease pencil vertex paint
    VIEW3D_PT_gp_painttab_paint,

    # armature edit mode
    VIEW3D_PT_gp_armaturetab_armature,
    VIEW3D_PT_gp_armaturetab_recalcboneroll,
    VIEW3D_PT_gp_armaturetab_names,

    #armature pose mode
    VIEW3D_PT_gp_posetab_pose,
    VIEW3D_PT_gp_posetab_cleartransform,
    VIEW3D_PT_gp_posetab_apply,
    VIEW3D_PT_gp_posetab_inbetweens,
    VIEW3D_PT_gp_posetab_propagate,
    VIEW3D_PT_gp_posetab_poselibrary,
    VIEW3D_PT_gp_posetab_motionpaths,
    VIEW3D_PT_gp_posetab_ik,
    VIEW3D_PT_gp_posetab_constraints,
    VIEW3D_PT_gp_posetab_names,

    # bfa - separated tooltips
    MASK_MT_flood_fill_invert,
    MASK_MT_flood_fill_fill,
    MASK_MT_flood_fill_clear,
    VIEW3D_MT_object_mirror_global_x,
    VIEW3D_MT_object_mirror_global_y,
    VIEW3D_MT_object_mirror_global_z,
    VIEW3D_MT_object_mirror_local_x,
    VIEW3D_MT_object_mirror_local_y,
    VIEW3D_MT_object_mirror_local_z,

)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
