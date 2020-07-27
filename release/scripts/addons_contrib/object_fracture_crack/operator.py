
if "bpy" in locals():
    import importlib
    importlib.reload(cell_main)
    importlib.reload(crack_functions)
    importlib.reload(material_functions)
    importlib.reload(utilities)

else:
    from .process import cell_main
    from .process import crack_functions
    from .process import material_functions
    from . import utilities

import bpy

from bpy.types import (
        Operator,
        )

class FRACTURE_OT_Cell(Operator):
    bl_idname = "object.add_fracture_cell"
    bl_label = "Fracture Cell"
    bl_description = "Make fractured cells from selected object."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH"

    def execute(self, context):
        #keywords = self.as_keywords()  # ignore=("blah",)

        fracture_cell_props = context.window_manager.fracture_cell_props
        cell_keywords = utilities._cell_props_to_dict(fracture_cell_props)

        originals = context.selected_editable_objects
        for original in originals:
            cell_main.main(context, original, **cell_keywords)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=300)

    def draw(self, context):
        cell_props = context.window_manager.fracture_cell_props

        layout = self.layout

        box = layout.box()
        col = box.column()
        col.label(text="Fracture From")
        row = col.row()
        #row.prop(cell_props, "source")
        row.prop(cell_props, "source_vert_own")
        row.prop(cell_props, "source_vert_child")
        row = col.row()
        row.prop(cell_props, "source_particle_own")
        row.prop(cell_props, "source_particle_child")
        row = col.row()
        row.prop(cell_props, "source_random")
        row.prop(cell_props, "source_pencil")

        box = layout.box()
        col = box.column()
        col.label(text="Transform")
        row = col.row()
        row.prop(cell_props, "pre_simplify")
        row.prop(cell_props, "source_noise")
        row = col.row(align=True)
        row.prop(cell_props, "margin")
        row.prop(cell_props, "use_recenter")
        row = col.row(align=True)
        row.prop(cell_props, "cell_scale")
        # could be own section, control how we subdiv
        #row.prop(cell_props, "use_island_split")

        box = layout.box()
        col = box.column()
        col.label(text="Recursive Shatter")
        row = col.row(align=True)
        row.prop(cell_props, "recursion")
        row.prop(cell_props, "recursion_chance")
        row = col.row(align=True)
        if cell_props.recursion > 0:
            row.enabled = True
        else:
            row.enabled = False
        row.prop(cell_props, "recursion_source_limit")
        row.prop(cell_props, "recursion_clamp")
        row = col.row()
        row.prop(cell_props, "recursion_chance_select")#, expand=True)

        box = layout.box()
        col = box.column()
        col.label(text="Interior Meshes")
        row = col.row(align=True)
        row.prop(cell_props, "use_data_match")
        row.prop(cell_props, "use_interior_vgroup")
        row = col.row(align=True)
        row.prop(cell_props, "use_smooth_faces")
        row.prop(cell_props, "use_sharp_edges")
        if cell_props.use_sharp_edges == True:
            row.prop(cell_props, "use_sharp_edges_apply")

        row = col.row()
        if cell_props.use_data_match == True:
            row.enabled = True
        else:
            row.enabled = False
        row.alignment = 'LEFT'
        # on same row for even layout but infact are not all that related
        row.prop(cell_props, "material_index")

        box = layout.box()
        col = box.column()
        col.label(text="Custom Properties")
        row = col.row(align=True)
        row.prop(cell_props, "use_mass")
        if cell_props.use_mass:
            row = col.row(align=True)
            row.prop(cell_props, "mass_name")
            row = col.row(align=True)
            row.prop(cell_props, "mass_mode")
            row.prop(cell_props, "mass")

        box = layout.box()
        col = box.column()
        col.label(text="Object Management")
        row = col.row(align=True)
        row.prop(cell_props, "original_hide")
        row.prop(cell_props, "cell_relocate")

        box = layout.box()
        col = box.column()
        col.label(text="Collections:")
        row = col.row(align=True)
        row.prop(cell_props, "use_collection")
        if cell_props.use_collection:
            row.prop(cell_props, "new_collection")
            row = col.row(align=True)
            row.prop(cell_props, "collection_name")

        box = layout.box()
        col = box.column()
        col.label(text="Debug")
        row = col.row(align=True)
        row.prop(cell_props, "use_debug_points")
        row.prop(cell_props, "use_debug_bool")
        row = col.row(align=True)
        row.prop(cell_props, "use_debug_redraw")

class FRACTURE_OT_Crack(Operator):
    bl_idname = "object.add_fracture_crack"
    bl_label = "Crack It"
    bl_description = "Make a cracked object from cell objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH"

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=250)

    def execute(self, context):
        crack_props = context.window_manager.fracture_crack_props

        cells = context.selected_editable_objects
        object = None

        if cells:
            # clear sharp edges for correct crack surface.
            bpy.context.view_layer.objects.active = cells[0]
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.reveal()

            bpy.ops.mesh.mark_sharp(clear=True, use_verts=True)
            bpy.ops.object.mode_set(mode='OBJECT')

            for cell in cells:
                bpy.context.view_layer.objects.active = cell
                bpy.ops.object.modifier_remove(modifier="EDGE_SPLIT_cell")
                bpy.context.object.vertex_groups.clear()

            bpy.context.view_layer.objects.active = cells[0]
            object = crack_functions.make_join(cells)

        if object:
            bpy.context.view_layer.objects.active = object

            crack_functions.add_modifiers()
            bpy.context.object.modifiers['DECIMATE_crackit'].ratio = crack_props.modifier_decimate
            bpy.context.object.modifiers['SMOOTH_crackit'].factor = crack_props.modifier_smooth

            crack_functions.multiExtrude(
                off=0.1,
                rotx=0, roty=0, rotz=0,
                sca=crack_props.extrude_scale,
                var1=crack_props.extrude_var, var2=crack_props.extrude_var, var3=crack_props.extrude_var,
                num=crack_props.extrude_num, ran=0
                )
            bpy.ops.object.modifier_apply(modifier='DECIMATE_crackit')
            bpy.ops.object.shade_smooth()

            if crack_props.modifier_wireframe == True:
                bpy.ops.object.modifier_add(type='WIREFRAME')
                wireframe = bpy.context.object.modifiers[-1]
                wireframe.name = 'WIREFRAME_crackit'
                wireframe.use_even_offset = False
                wireframe.thickness = 0.01
        else:
            assert("Joining into One object had been failed. Mesh object can only be joined.")

        return {'FINISHED'}

    def draw(self, context):
        cell_props = context.window_manager.fracture_cell_props
        crack_props = context.window_manager.fracture_crack_props
        layout = self.layout

        box = layout.box()
        col = box.column()
        col.label(text='Execute After Fracture Cell')

        box = layout.box()
        col = box.column()
        col.label(text="Surface:")
        row = col.row(align=True)
        row.prop(crack_props, "modifier_decimate")
        row = col.row(align=True)
        row.prop(crack_props, "modifier_smooth")

        col = box.column()
        col.label(text="Extrude:")
        row = col.row(align=True)
        row.prop(crack_props, "extrude_scale")
        row = col.row(align=True)
        row.prop(crack_props, "extrude_var")
        row = col.row(align=True)
        row.prop(crack_props, "extrude_num")

        col = box.column()
        col.label(text="Post Processing")
        row = col.row(align=True)
        row.prop(crack_props, "modifier_wireframe")


class FRACTURE_OT_Material(Operator):
    bl_idname = "object.add_fracture_material"
    bl_label = "Material Preset"
    bl_description = ("Material preset for cracked object")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        # included - type that can have materials
        included = ['MESH', 'CURVE', 'SURFACE', 'FONT', 'META']
        return (obj is not None and obj.type in included)

    def execute(self, context):
        material_props = context.window_manager.fracture_material_props

        mat_name = material_props.material_preset
        mat_lib_name = material_props.material_lib_name
        mat_ui_name = material_props.get_ui_mat_name(mat_name) if not mat_lib_name else mat_name

        try:
            material_functions.appendMaterial(
                    mat_lib_name = mat_lib_name,
                    mat_name = mat_name,
                    mat_ui_names = mat_ui_name
                    )
        except Exception as e:
            material_functions.error_handlers(
                    self, "mesh.crackit_material", e,
                    "The active Object could not have the Material {} applied".format(mat_ui_name)
                    )
            return {"CANCELLED"}

        return {'FINISHED'}
