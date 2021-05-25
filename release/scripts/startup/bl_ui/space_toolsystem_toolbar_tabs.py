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

# <pep8 compliant>

import bpy
from bpy.types import Panel

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
        elif width_scale > 120.0:
            column_count = 3
        elif width_scale > 80:
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
    bl_options = {'DEFAULT_CLOSED'}

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

                    col.separator( factor = 0.5)
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
                    col.separator( factor = 0.5)
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
    bl_options = {'DEFAULT_CLOSED'}

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


class VIEW3D_PT_objecttab_mirror(toolshelf_calculate, Panel):
    bl_label = "Mirror"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"
    bl_options = {'DEFAULT_CLOSED'}

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
            props = col.operator("transform.mirror", text="X Global", icon = "MIRROR_X")
            props.constraint_axis = (True, False, False)
            props.orient_type = 'GLOBAL'
            props = col.operator("transform.mirror", text="Y Global", icon = "MIRROR_Y")
            props.constraint_axis = (False, True, False)
            props.orient_type = 'GLOBAL'
            props = col.operator("transform.mirror", text="Z Global", icon = "MIRROR_Z")
            props.constraint_axis = (False, False, True)
            props.orient_type = 'GLOBAL'

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
                props = row.operator("transform.mirror", text="", icon = "MIRROR_X")
                props.constraint_axis = (True, False, False)
                props.orient_type = 'GLOBAL'
                props = row.operator("transform.mirror", text="", icon = "MIRROR_Y")
                props.constraint_axis = (False, True, False)
                props.orient_type = 'GLOBAL'
                row = col.row(align=True)
                props = row.operator("transform.mirror", text="", icon = "MIRROR_Z")
                props.constraint_axis = (False, False, True)
                props.orient_type = 'GLOBAL'

                if _context.edit_object and _context.edit_object.type in {'MESH', 'SURFACE'}:
                    row.operator("object.vertex_group_mirror", text="", icon = "MIRROR_VERTEXGROUP")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("transform.mirror", text="", icon='TRANSFORM_MIRROR')

                row.operator_context = 'EXEC_REGION_WIN'
                props = row.operator("transform.mirror", text="", icon = "MIRROR_X")
                props.constraint_axis = (True, False, False)
                row = col.row(align=True)
                props.orient_type = 'GLOBAL'
                props = row.operator("transform.mirror", text="", icon = "MIRROR_Y")
                props.constraint_axis = (False, True, False)
                props.orient_type = 'GLOBAL'
                props = row.operator("transform.mirror", text="", icon = "MIRROR_Z")
                props.constraint_axis = (False, False, True)
                props.orient_type = 'GLOBAL'

                if _context.edit_object and _context.edit_object.type in {'MESH', 'SURFACE'}:
                    row = col.row(align=True)
                    row.operator("object.vertex_group_mirror", text="", icon = "MIRROR_VERTEXGROUP")

            elif column_count == 1:

                col.operator("transform.mirror", text="", icon='TRANSFORM_MIRROR')

                col.operator_context = 'EXEC_REGION_WIN'
                props = col.operator("transform.mirror", text="", icon = "MIRROR_X")
                props.constraint_axis = (True, False, False)
                props.orient_type = 'GLOBAL'
                props = col.operator("transform.mirror", text="", icon = "MIRROR_Y")
                props.constraint_axis = (False, True, False)
                props.orient_type = 'GLOBAL'
                props = col.operator("transform.mirror", text="", icon = "MIRROR_Z")
                props.constraint_axis = (False, False, True)
                props.orient_type = 'GLOBAL'

                if _context.edit_object and _context.edit_object.type in {'MESH', 'SURFACE'}:
                    col.operator("object.vertex_group_mirror", text="", icon = "MIRROR_VERTEXGROUP")


class VIEW3D_PT_objecttab_mirror_local(toolshelf_calculate, Panel):
    bl_label = "Local"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"
    bl_parent_id = "VIEW3D_PT_objecttab_mirror"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator_context = 'EXEC_REGION_WIN'
            props = col.operator("transform.mirror", text="X Global", icon = "MIRROR_X")
            props.constraint_axis = (True, False, False)
            props.orient_type = 'LOCAL'
            props = col.operator("transform.mirror", text="Y Global", icon = "MIRROR_Y")
            props.constraint_axis = (False, True, False)
            props.orient_type = 'LOCAL'
            props = col.operator("transform.mirror", text="Z Global", icon = "MIRROR_Z")
            props.constraint_axis = (False, False, True)
            props.orient_type = 'LOCAL'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator_context = 'EXEC_REGION_WIN'
                props = row.operator("transform.mirror", text="", icon = "MIRROR_X")
                props.constraint_axis = (True, False, False)
                props.orient_type = 'LOCAL'
                props = row.operator("transform.mirror", text="", icon = "MIRROR_Y")
                props.constraint_axis = (False, True, False)
                props.orient_type = 'LOCAL'
                props = row.operator("transform.mirror", text="", icon = "MIRROR_Z")
                props.constraint_axis = (False, False, True)
                props.orient_type = 'LOCAL'


            elif column_count == 2:
                row = col.row(align=True)
                row.operator_context = 'EXEC_REGION_WIN'
                props = row.operator("transform.mirror", text="", icon = "MIRROR_X")
                props.constraint_axis = (True, False, False)
                props.orient_type = 'LOCAL'
                props = row.operator("transform.mirror", text="", icon = "MIRROR_Y")
                props.constraint_axis = (False, True, False)
                props.orient_type = 'LOCAL'
                row = col.row(align=True)
                props = row.operator("transform.mirror", text="", icon = "MIRROR_Z")
                props.constraint_axis = (False, False, True)
                props.orient_type = 'LOCAL'

            elif column_count == 1:


                col.operator_context = 'EXEC_REGION_WIN'
                props = col.operator("transform.mirror", text="", icon = "MIRROR_X")
                props.constraint_axis = (True, False, False)
                props.orient_type = 'LOCAL'
                props = col.operator("transform.mirror", text="", icon = "MIRROR_Y")
                props.constraint_axis = (False, True, False)
                props.orient_type = 'LOCAL'
                props = col.operator("transform.mirror", text="", icon = "MIRROR_Z")
                props.constraint_axis = (False, False, True)
                props.orient_type = 'LOCAL'


class VIEW3D_PT_objecttab_clear(toolshelf_calculate, Panel):
    bl_label = "Clear"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

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
    bl_options = {'DEFAULT_CLOSED'}

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

            props = col.operator("object.transform_apply", text="Location", text_ctxt=i18n_contexts.default, icon = "APPLYMOVE")
            props.location, props.rotation, props.scale = True, False, False

            props = col.operator("object.transform_apply", text="Rotation", text_ctxt=i18n_contexts.default, icon = "APPLYROTATE")
            props.location, props.rotation, props.scale = False, True, False

            props = col.operator("object.transform_apply", text="Scale", text_ctxt=i18n_contexts.default, icon = "APPLYSCALE")
            props.location, props.rotation, props.scale = False, False, True

            props = col.operator("object.transform_apply", text="All Transforms", text_ctxt=i18n_contexts.default, icon = "APPLYALL")
            props.location, props.rotation, props.scale = True, True, True

            props = col.operator("object.transform_apply", text="Rotation & Scale", text_ctxt=i18n_contexts.default, icon = "APPLY_ROTSCALE")
            props.location, props.rotation, props.scale = False, True, True

            col.separator(factor = 0.5)

            col.operator("object.visual_transform_apply", text="Visual Transform", text_ctxt=i18n_contexts.default, icon = "VISUALTRANSFORM")
            col.operator("object.duplicates_make_real", icon = "MAKEDUPLIREAL")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                props = row.operator("object.transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "APPLYMOVE")
                props.location, props.rotation, props.scale = True, False, False

                props = row.operator("object.transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "APPLYROTATE")
                props.location, props.rotation, props.scale = False, True, False

                props = row.operator("object.transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "APPLYSCALE")
                props.location, props.rotation, props.scale = False, False, True

                row = col.row(align=True)
                props = row.operator("object.transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "APPLYALL")
                props.location, props.rotation, props.scale = True, True, True

                props = row.operator("object.transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "APPLY_ROTSCALE")
                props.location, props.rotation, props.scale = False, True, True

                row = col.row(align=True)
                row.operator("object.visual_transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "VISUALTRANSFORM")
                row.operator("object.duplicates_make_real", text="", icon = "MAKEDUPLIREAL")

            elif column_count == 2:

                row = col.row(align=True)
                props = row.operator("object.transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "APPLYMOVE")
                props.location, props.rotation, props.scale = True, False, False

                props = row.operator("object.transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "APPLYROTATE")
                props.location, props.rotation, props.scale = False, True, False

                row = col.row(align=True)
                props = row.operator("object.transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "APPLYSCALE")
                props.location, props.rotation, props.scale = False, False, True

                props = row.operator("object.transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "APPLYALL")
                props.location, props.rotation, props.scale = True, True, True

                row = col.row(align=True)
                props = row.operator("object.transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "APPLY_ROTSCALE")
                props.location, props.rotation, props.scale = False, True, True

                row = col.row(align=True)
                row.operator("object.visual_transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "VISUALTRANSFORM")
                row.operator("object.duplicates_make_real", text="", icon = "MAKEDUPLIREAL")

            elif column_count == 1:

                props = col.operator("object.transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "APPLYMOVE")
                props.location, props.rotation, props.scale = True, False, False

                props = col.operator("object.transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "APPLYROTATE")
                props.location, props.rotation, props.scale = False, True, False

                props = col.operator("object.transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "APPLYSCALE")
                props.location, props.rotation, props.scale = False, False, True

                props = col.operator("object.transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "APPLYALL")
                props.location, props.rotation, props.scale = True, True, True

                props = col.operator("object.transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "APPLY_ROTSCALE")
                props.location, props.rotation, props.scale = False, True, True

                col.separator(factor = 0.5)

                col.operator("object.visual_transform_apply", text="", text_ctxt=i18n_contexts.default, icon = "VISUALTRANSFORM")
                col.operator("object.duplicates_make_real", text="", icon = "MAKEDUPLIREAL")


class VIEW3D_PT_objecttab_apply_delta(toolshelf_calculate, Panel):
    bl_label = "Apply Deltas"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_objecttab_apply"
    bl_options = {'DEFAULT_CLOSED'}

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

            col.operator("object.transforms_to_deltas", text="Location to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYMOVEDELTA").mode = 'LOC'
            col.operator("object.transforms_to_deltas", text="Rotation to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYROTATEDELTA").mode = 'ROT'
            col.operator("object.transforms_to_deltas", text="Scale to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYSCALEDELTA").mode = 'SCALE'
            col.operator("object.transforms_to_deltas", text="All Transforms to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYALLDELTA").mode = 'ALL'

            col.separator(factor = 0.5)

            col.operator("object.anim_transforms_to_deltas", icon = "APPLYANIDELTA")


        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYMOVEDELTA").mode = 'LOC'
                row.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYROTATEDELTA").mode = 'ROT'
                row.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYSCALEDELTA").mode = 'SCALE'

                row = col.row(align=True)
                row.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYALLDELTA").mode = 'ALL'
                row.operator("object.anim_transforms_to_deltas", text="", icon = "APPLYANIDELTA")


            elif column_count == 2:

                row = col.row(align=True)
                row.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYMOVEDELTA").mode = 'LOC'
                row.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYROTATEDELTA").mode = 'ROT'

                row = col.row(align=True)
                row.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYSCALEDELTA").mode = 'SCALE'
                row.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYALLDELTA").mode = 'ALL'

                row = col.row(align=True)
                row.operator("object.anim_transforms_to_deltas", text = "", icon = "APPLYANIDELTA")

            elif column_count == 1:

                col.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYMOVEDELTA").mode = 'LOC'
                col.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYROTATEDELTA").mode = 'ROT'
                col.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYSCALEDELTA").mode = 'SCALE'
                col.operator("object.transforms_to_deltas", text="", text_ctxt=i18n_contexts.default, icon = "APPLYALLDELTA").mode = 'ALL'

                col.separator(factor = 0.5)

                col.operator("object.anim_transforms_to_deltas", text="", icon = "APPLYANIDELTA")


class VIEW3D_PT_objecttab_snap(toolshelf_calculate, Panel):
    bl_label = "Snap"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"

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

                col.separator(factor = 0.5)

                row = col.row(align=True)
                row.operator("view3d.snap_cursor_to_selected", text = "", icon = "CURSORTOSELECTION")
                row.operator("view3d.snap_cursor_to_center", text = "", icon = "CURSORTOCENTER")
                row.operator("view3d.snap_cursor_to_active", text = "", icon = "CURSORTOACTIVE")

                row = col.row(align=True)
                row.operator("view3d.snap_cursor_to_grid", text = "", icon = "CURSORTOGRID")

            elif column_count == 2:

                row = col.row(align=True)

                row.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOR").use_offset = False
                row.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOROFFSET").use_offset = True

                row = col.row(align=True)

                row.operator("view3d.snap_selected_to_active", text = "", icon = "SELECTIONTOACTIVE")
                row.operator("view3d.snap_selected_to_grid", text = "", icon = "SELECTIONTOGRID")

                col.separator(factor = 0.5)

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
    bl_options = {'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        obj = context.object
        if obj is None:
            return
        elif obj.type == 'MESH':
            pass
        return overlay.show_toolshelf_tabs == True and context.mode in {'OBJECT'}

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("object.shade_smooth", icon ='SHADING_SMOOTH')
            col.operator("object.shade_flat", icon ='SHADING_FLAT')

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("object.shade_smooth", text = "", icon ='SHADING_SMOOTH')
                row.operator("object.shade_flat", text = "", icon ='SHADING_FLAT')

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("object.shade_smooth", text = "", icon ='SHADING_SMOOTH')
                row.operator("object.shade_flat", text = "", icon ='SHADING_FLAT')

            elif column_count == 1:

                col.operator("object.shade_smooth", text = "", icon ='SHADING_SMOOTH')
                col.operator("object.shade_flat", text = "", icon ='SHADING_FLAT')



# -------------------------------------- Mesh

class VIEW3D_PT_meshtab_merge(toolshelf_calculate, Panel):
    bl_label = "Merge"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Mesh"
    bl_context = "mesh_edit"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

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
                row.operator("mesh.merge", text="", icon = "MERGE").type = 'COLLAPSE'

                row = col.row(align=True)
                row.operator("mesh.remove_doubles", text="", icon = "REMOVE_DOUBLES")

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("mesh.merge", text="", icon = "MERGE_CENTER").type = 'CENTER'
                row.operator("mesh.merge", text="", icon = "MERGE_CURSOR").type = 'CURSOR'

                row = col.row(align=True)
                row.operator("mesh.merge", text="", icon = "MERGE").type = 'COLLAPSE'
                row.operator("mesh.remove_doubles", text="", icon = "REMOVE_DOUBLES")

            elif column_count == 1:

                col.operator("mesh.merge", text="", icon = "MERGE_CENTER").type = 'CENTER'
                col.operator("mesh.merge", text="", icon = "MERGE_CURSOR").type = 'CURSOR'
                col.operator("mesh.merge", text="", icon = "MERGE").type = 'COLLAPSE'

                col.separator(factor = 0.5)

                col.operator("mesh.remove_doubles", text="", icon = "REMOVE_DOUBLES")


class VIEW3D_PT_meshtab_split(toolshelf_calculate, Panel):
    bl_label = "Split"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Mesh"
    bl_context = "mesh_edit"
    bl_options = {'DEFAULT_CLOSED'}

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
    bl_options = {'DEFAULT_CLOSED'}

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
    bl_options = {'DEFAULT_CLOSED'}

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

                col.separator( factor = 0.5)
                row = col.row(align=True)
                row.operator("mesh.knife_project", text = "", icon='KNIFE_PROJECT')

                if with_bullet:
                    row.operator("mesh.convex_hull", text = "", icon = "CONVEXHULL")


                col.separator( factor = 0.5)
                row = col.row(align=True)
                row.operator("mesh.symmetrize", text = "", icon = "SYMMETRIZE")
                row.operator("mesh.symmetry_snap", text = "", icon = "SNAP_SYMMETRY")


            elif column_count == 2:


                row = col.row(align=True)
                row.operator("mesh.extrude_repeat", text = "", icon = "REPEAT")
                row.operator("mesh.spin", text = "", icon = "SPIN").angle = pi * 2

                col.separator( factor = 0.5)
                row = col.row(align=True)
                row.operator("mesh.knife_project", text = "", icon='KNIFE_PROJECT')

                if with_bullet:
                    row.operator("mesh.convex_hull", text = "", icon = "CONVEXHULL")

                col.separator( factor = 0.5)
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
    bl_options = {'DEFAULT_CLOSED'}

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

)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
