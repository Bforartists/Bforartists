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
    bl_label = "Mirror Local"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

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
    bl_options = {'HIDE_BG'}

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

                row.operator("mesh.blend_from_shape", text="", icon = "BLENDFROMSHAPE")
                row.operator("mesh.shape_propagate_to_all", text="", icon = "SHAPEPROPAGATE")

                row = col.row(align=True)
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
                row.operator("mesh.blend_from_shape", text="", icon = "BLENDFROMSHAPE")
                row.operator("mesh.shape_propagate_to_all", text="", icon = "SHAPEPROPAGATE")

                row = col.row(align=True)
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

            props = col.operator("paint.mask_flood_fill", text="Invert Mask", icon = "INVERT_MASK")
            props.mode = 'INVERT'

            props = col.operator("paint.mask_flood_fill", text="Fill Mask", icon = "FILL_MASK")
            props.mode = 'VALUE'
            props.value = 1

            props = col.operator("paint.mask_flood_fill", text="Clear Mask", icon = "CLEAR_MASK")
            props.mode = 'VALUE'
            props.value = 0

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
            props = col.operator("mesh.paint_mask_slice", text="Mask Slice and Fill Holes", icon = "MASK_SLICE")
            props.new_object = False
            props = col.operator("mesh.paint_mask_slice", text="Mask Slice to New Object", icon = "MASK_SLICE")

            col.separator(factor = 0.5)

            props = col.operator("sculpt.dirty_mask", text='Dirty Mask', icon = "DIRTY_VERTEX")


        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                props = row.operator("paint.mask_flood_fill", text="", icon = "INVERT_MASK")
                props.mode = 'INVERT'

                props = row.operator("paint.mask_flood_fill", text="", icon = "FILL_MASK")
                props.mode = 'VALUE'
                props.value = 1

                props = row.operator("paint.mask_flood_fill", text="", icon = "CLEAR_MASK")
                props.mode = 'VALUE'
                props.value = 0

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
                props = row.operator("mesh.paint_mask_slice", text="", icon = "MASK_SLICE")
                props.new_object = False
                props = row.operator("mesh.paint_mask_slice", text="", icon = "MASK_SLICE")

                row = col.row(align=True)
                props = row.operator("sculpt.dirty_mask", text='', icon = "DIRTY_VERTEX")


            elif column_count == 2:

                row = col.row(align=True)
                props = row.operator("paint.mask_flood_fill", text="", icon = "INVERT_MASK")
                props.mode = 'INVERT'

                props = row.operator("paint.mask_flood_fill", text="", icon = "FILL_MASK")
                props.mode = 'VALUE'
                props.value = 1

                row = col.row(align=True)
                props = row.operator("paint.mask_flood_fill", text="", icon = "CLEAR_MASK")
                props.mode = 'VALUE'
                props.value = 0

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
                props = row.operator("mesh.paint_mask_slice", text="", icon = "MASK_SLICE")
                props.new_object = False
                props = row.operator("mesh.paint_mask_slice", text="", icon = "MASK_SLICE")

                row = col.row(align=True)
                props = row.operator("sculpt.dirty_mask", text='', icon = "DIRTY_VERTEX")

            elif column_count == 1:

                col = layout.column(align=True)
                col.scale_y = 2

                props = col.operator("paint.mask_flood_fill", text="", icon = "INVERT_MASK")
                props.mode = 'INVERT'

                props = col.operator("paint.mask_flood_fill", text="", icon = "FILL_MASK")
                props.mode = 'VALUE'
                props.value = 1

                props = col.operator("paint.mask_flood_fill", text="", icon = "CLEAR_MASK")
                props.mode = 'VALUE'
                props.value = 0

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
                props = col.operator("mesh.paint_mask_slice", text="", icon = "MASK_SLICE")
                props.new_object = False
                props = col.operator("mesh.paint_mask_slice", text="", icon = "MASK_SLICE")

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

            op = col.operator("sculpt.mask_init", text='Per Vertex', icon = "SELECT_UNGROUPED_VERTS")
            op.mode = 'RANDOM_PER_VERTEX'

            op = col.operator("sculpt.mask_init", text='Per Face Set', icon = "FACESEL")
            op.mode = 'RANDOM_PER_FACE_SET'

            op = col.operator("sculpt.mask_init", text='Per Loose Part', icon = "SELECT_LOOSE")
            op.mode = 'RANDOM_PER_LOOSE_PART'


        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                op = row.operator("sculpt.mask_init", text='', icon = "SELECT_UNGROUPED_VERTS")
                op.mode = 'RANDOM_PER_VERTEX'

                op = row.operator("sculpt.mask_init", text='', icon = "FACESEL")
                op.mode = 'RANDOM_PER_FACE_SET'

                op = row.operator("sculpt.mask_init", text='', icon = "SELECT_LOOSE")
                op.mode = 'RANDOM_PER_LOOSE_PART'

            elif column_count == 2:

                row = col.row(align=True)
                op = row.operator("sculpt.mask_init", text='', icon = "SELECT_UNGROUPED_VERTS")
                op.mode = 'RANDOM_PER_VERTEX'

                op = row.operator("sculpt.mask_init", text='', icon = "FACESEL")
                op.mode = 'RANDOM_PER_FACE_SET'

                row = col.row(align=True)
                op = row.operator("sculpt.mask_init", text='', icon = "SELECT_LOOSE")
                op.mode = 'RANDOM_PER_LOOSE_PART'


            elif column_count == 1:

                col = layout.column(align=True)
                col.scale_y = 2

                col = layout.column(align=True)
                col.scale_y = 2

                op = col.operator("sculpt.mask_init", text='', icon = "SELECT_UNGROUPED_VERTS")
                op.mode = 'RANDOM_PER_VERTEX'

                op = col.operator("sculpt.mask_init", text='', icon = "FACESEL")
                op.mode = 'RANDOM_PER_FACE_SET'

                op = col.operator("sculpt.mask_init", text='', icon = "SELECT_LOOSE")
                op.mode = 'RANDOM_PER_LOOSE_PART'


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

    #curve edit mode
    VIEW3D_PT_curvetab_curve,
    VIEW3D_PT_curvetab_controlpoints,
    VIEW3D_PT_surfacetab_surface,
    VIEW3D_PT_curvetab_controlpoints_surface,
    VIEW3D_PT_segmentstab_segments,

)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
