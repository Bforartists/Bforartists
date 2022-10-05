# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Hotkey: 'Ctrl Tab'",
    "description": "Switch between 3d view object/edit modes",
    "author": "pitiwazou, meta-androcto, italic",
    "version": (0, 1, 2),
    "blender": (2, 80, 0),
    "location": "3D View",
    "warning": "",
    "doc_url": "",
    "category": "Mode Switch Pie"
}

import bpy
from bpy.types import (
    Menu,
    Operator
)


class PIE_OT_ClassObject(Operator):
    bl_idname = "class.object"
    bl_label = "Class Object"
    bl_description = "Edit/Object Mode Switch"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode == "OBJECT":
            bpy.ops.object.mode_set(mode="EDIT")
        else:
            bpy.ops.object.mode_set(mode="OBJECT")
        return {'FINISHED'}


class PIE_OT_ClassTexturePaint(Operator):
    bl_idname = "class.pietexturepaint"
    bl_label = "Class Texture Paint"
    bl_description = "Texture Paint"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.paint.texture_paint_toggle()
        else:
            bpy.ops.paint.texture_paint_toggle()
        return {'FINISHED'}


class PIE_OT_ClassWeightPaint(Operator):
    bl_idname = "class.pieweightpaint"
    bl_label = "Class Weight Paint"
    bl_description = "Weight Paint"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.paint.weight_paint_toggle()
        else:
            bpy.ops.paint.weight_paint_toggle()
        return {'FINISHED'}


class PIE_OT_ClassVertexPaint(Operator):
    bl_idname = "class.pievertexpaint"
    bl_label = "Class Vertex Paint"
    bl_description = "Vertex Paint"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.paint.vertex_paint_toggle()
        else:
            bpy.ops.paint.vertex_paint_toggle()
        return {'FINISHED'}


class PIE_OT_ClassParticleEdit(Operator):
    bl_idname = "class.pieparticleedit"
    bl_label = "Class Particle Edit"
    bl_description = "Particle Edit (must have active particle system)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.particle.particle_edit_toggle()
        else:
            bpy.ops.particle.particle_edit_toggle()
        return {'FINISHED'}


# Set Mode Operator #
class PIE_OT_SetObjectModePie(Operator):
    bl_idname = "object.set_object_mode_pie"
    bl_label = "Set the object interactive mode"
    bl_description = "I set the interactive mode of object"
    bl_options = {'REGISTER'}

    mode: bpy.props.StringProperty(name="Interactive mode", default="OBJECT")

    def execute(self, context):
        if (context.active_object):
            try:
                bpy.ops.object.mode_set(mode=self.mode)
            except TypeError:
                msg = context.active_object.name + " It is not possible to enter into the interactive mode"
                self.report(type={"WARNING"}, message=msg)
        else:
            self.report(type={"WARNING"}, message="There is no active object")
        return {'FINISHED'}


# Edit Selection Modes
class PIE_OT_ClassVertex(Operator):
    bl_idname = "class.vertex"
    bl_label = "Class Vertex"
    bl_description = "Vert Select Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "EDGE, FACE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            return {'FINISHED'}


class PIE_OT_ClassEdge(Operator):
    bl_idname = "class.edge"
    bl_label = "Class Edge"
    bl_description = "Edge Select Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        if bpy.ops.mesh.select_mode != "VERT, FACE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            return {'FINISHED'}


class PIE_OT_ClassFace(Operator):
    bl_idname = "class.face"
    bl_label = "Class Face"
    bl_description = "Face Select Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        if bpy.ops.mesh.select_mode != "VERT, EDGE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            return {'FINISHED'}


class PIE_OT_VertsEdgesFaces(Operator):
    bl_idname = "verts.edgesfaces"
    bl_label = "Verts Edges Faces"
    bl_description = "Vert/Edge/Face Select Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
            return {'FINISHED'}


# Menus
class PIE_MT_ObjectEditotherModes(Menu):
    """Edit/Object Others modes"""
    bl_idname = "MENU_MT_objecteditmodeothermodes"
    bl_label = "Edit Selection Modes"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        box = pie.split().column()

        box.operator("class.vertex", text="Vertex", icon='VERTEXSEL')
        box.operator("class.edge", text="Edge", icon='EDGESEL')
        box.operator("class.face", text="Face", icon='FACESEL')
        box.operator("verts.edgesfaces", text="Vertex/Edges/Faces", icon='OBJECT_DATAMODE')


class PIE_MT_ObjectEditMode(Menu):
    """Modes Switch"""
    bl_idname = "PIE_MT_objecteditmode"
    bl_label = "Mode Switch (Ctrl Tab)"

    def draw(self, context):
        layout = self.layout
        ob = context.object
        # No Object Selected #
        if not ob or not ob.select_get():
            message = "No Active Object Selected"
            pie = layout.menu_pie()
            pie.separator()
            pie.separator()
            pie.separator()
            box = pie.box()
            box.label(text=message, icon="INFO")

        elif ob and ob.type == 'MESH' and ob.mode in {
                'OBJECT', 'SCULPT', 'VERTEX_PAINT',
                'WEIGHT_PAINT', 'TEXTURE_PAINT',
                'PARTICLE_EDIT', 'GPENCIL_EDIT',
        }:
            pie = layout.menu_pie()
            # 4 - LEFT
            pie.operator("class.pieweightpaint", text="Weight Paint", icon='WPAINT_HLT')
            # 6 - RIGHT
            pie.operator("class.pietexturepaint", text="Texture Paint", icon='TPAINT_HLT')
            # 2 - BOTTOM
            pie.menu("MENU_MT_objecteditmodeothermodes", text="Edit Modes", icon='EDITMODE_HLT')
            # 8 - TOP
            pie.operator("class.object", text="Object/Edit Toggle", icon='OBJECT_DATAMODE')
            # 7 - TOP - LEFT
            pie.operator("sculpt.sculptmode_toggle", text="Sculpt", icon='SCULPTMODE_HLT')
            # 9 - TOP - RIGHT
            pie.operator("class.pievertexpaint", text="Vertex Paint", icon='VPAINT_HLT')
            # 1 - BOTTOM - LEFT
            pie.separator()
            # 3 - BOTTOM - RIGHT
            if context.object.particle_systems:
                pie.operator("class.pieparticleedit", text="Particle Edit", icon='PARTICLEMODE')
            else:
                pie.separator()

        elif ob and ob.type == 'MESH' and ob.mode in {'EDIT'}:
            pie = layout.menu_pie()
            # 4 - LEFT
            pie.operator("class.pieweightpaint", text="Weight Paint", icon='WPAINT_HLT')
            # 6 - RIGHT
            pie.operator("class.pietexturepaint", text="Texture Paint", icon='TPAINT_HLT')
            # 2 - BOTTOM
            pie.menu("MENU_MT_objecteditmodeothermodes", text="Edit Modes", icon='EDITMODE_HLT')
            # 8 - TOP
            pie.operator("class.object", text="Edit/Object Toggle", icon='OBJECT_DATAMODE')
            # 7 - TOP - LEFT
            pie.operator("sculpt.sculptmode_toggle", text="Sculpt", icon='SCULPTMODE_HLT')
            # 9 - TOP - RIGHT
            pie.operator("class.pievertexpaint", text="Vertex Paint", icon='VPAINT_HLT')
            # 1 - BOTTOM - LEFT
            pie.separator()
            # 3 - BOTTOM - RIGHT
            if context.object.particle_systems:
                pie.operator("class.pieparticleedit", text="Particle Edit", icon='PARTICLEMODE')
            else:
                pie.separator()

        elif ob and ob.type == 'CURVE':
            pie = layout.menu_pie()
            # 4 - LEFT
            pie.separator()
            # 6 - RIGHT
            pie.separator()
            # 2 - BOTTOM
            pie.separator()
            # 8 - TOP
            pie.operator("object.editmode_toggle", text="Edit/Object", icon='OBJECT_DATAMODE')
            # 7 - TOP - LEFT
            pie.separator()
            # 9 - TOP - RIGHT
            pie.separator()
            # 1 - BOTTOM - LEFT
            pie.separator()
            # 3 - BOTTOM - RIGHT
            pie.separator()

        elif ob and ob.type == 'ARMATURE':
            pie = layout.menu_pie()
            # 4 - LEFT
            pie.operator(PIE_OT_SetObjectModePie.bl_idname, text="Object", icon="OBJECT_DATAMODE").mode = "OBJECT"
            # 6 - RIGHT
            pie.operator(PIE_OT_SetObjectModePie.bl_idname, text="Pose", icon="POSE_HLT").mode = "POSE"
            # 2 - BOTTOM
            pie.operator(PIE_OT_SetObjectModePie.bl_idname, text="Edit", icon="EDITMODE_HLT").mode = "EDIT"
            # 8 - TOP
            pie.operator("object.editmode_toggle", text="Edit Mode", icon='OBJECT_DATAMODE')
            # 7 - TOP - LEFT
            pie.separator()
            # 9 - TOP - RIGHT
            pie.separator()
            # 1 - BOTTOM - LEFT
            pie.separator()
            # 3 - BOTTOM - RIGHT
            pie.separator()

        elif ob and ob.type == 'FONT':
            pie = layout.menu_pie()
            pie.separator()
            pie.separator()
            pie.separator()
            pie.operator("object.editmode_toggle", text="Edit/Object Toggle", icon='OBJECT_DATAMODE')
            pie.separator()
            pie.separator()
            pie.separator()
            # 3 - BOTTOM - RIGHT
            pie.separator()

        elif ob and ob.type == 'SURFACE':
            pie = layout.menu_pie()
            pie.separator()
            pie.separator()
            pie.separator()
            pie.operator("object.editmode_toggle", text="Edit/Object Toggle", icon='OBJECT_DATAMODE')
            pie.separator()
            pie.separator()
            pie.separator()
            # 3 - BOTTOM - RIGHT
            pie.separator()

        elif ob and ob.type == 'META':
            pie = layout.menu_pie()
            pie.separator()
            pie.separator()
            pie.separator()
            pie.operator("object.editmode_toggle", text="Edit/Object Toggle", icon='OBJECT_DATAMODE')
            pie.separator()
            pie.separator()
            pie.separator()
            # 3 - BOTTOM - RIGHT
            pie.separator()

        elif ob and ob.type == 'LATTICE':
            pie = layout.menu_pie()
            pie.separator()
            pie.separator()
            pie.separator()
            pie.operator("object.editmode_toggle", text="Edit/Object Toggle", icon='OBJECT_DATAMODE')
            pie.separator()
            pie.separator()
            pie.separator()

        if ob and ob.type == 'GPENCIL':
            pie = layout.menu_pie()
            # 4 - LEFT
            pie.operator(PIE_OT_SetObjectModePie.bl_idname, text="Sculpt",
                         icon="SCULPTMODE_HLT").mode = "SCULPT_GPENCIL"
            # 6 - RIGHT
            pie.operator(PIE_OT_SetObjectModePie.bl_idname, text="Draw", icon="GREASEPENCIL").mode = "PAINT_GPENCIL"
            # 2 - BOTTOM
            pie.operator(PIE_OT_SetObjectModePie.bl_idname, text="Edit", icon="EDITMODE_HLT").mode = "EDIT_GPENCIL"
            # 8 - TOP
            pie.operator(PIE_OT_SetObjectModePie.bl_idname, text="Object", icon="OBJECT_DATAMODE").mode = "OBJECT"
            # 7 - TOP - LEFT
            pie.separator()
            # 9 - TOP - RIGHT
            pie.separator()
            # 1 - BOTTOM - LEFT
            pie.separator()
            # 3 - BOTTOM - RIGHT
            pie.operator(
                PIE_OT_SetObjectModePie.bl_idname,
                text="Weight Paint",
                icon="WPAINT_HLT").mode = "WEIGHT_GPENCIL"

        elif ob and ob.type in {"LIGHT", "CAMERA", "EMPTY", "SPEAKER"}:
            message = "Active Object has only Object Mode available"
            pie = layout.menu_pie()
            pie.separator()
            pie.separator()
            pie.separator()
            box = pie.box()
            box.label(text=message, icon="INFO")


classes = (
    PIE_MT_ObjectEditMode,
    PIE_OT_ClassObject,
    PIE_OT_ClassVertex,
    PIE_OT_ClassEdge,
    PIE_OT_ClassFace,
    PIE_MT_ObjectEditotherModes,
    PIE_OT_ClassTexturePaint,
    PIE_OT_ClassWeightPaint,
    PIE_OT_ClassVertexPaint,
    PIE_OT_ClassParticleEdit,
    PIE_OT_VertsEdgesFaces,
    PIE_OT_SetObjectModePie,
)

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        # Select Mode
        km = wm.keyconfigs.addon.keymaps.new(name='Object Non-modal')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'TAB', 'PRESS', ctrl=True)
        kmi.properties.name = "PIE_MT_objecteditmode"
        addon_keymaps.append((km, kmi))

        km = wm.keyconfigs.addon.keymaps.new(name='Grease Pencil Stroke Edit Mode')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'TAB', 'PRESS', ctrl=True)
        kmi.properties.name = "PIE_MT_objecteditmode"
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()
