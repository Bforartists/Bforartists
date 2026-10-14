import bpy


class AddMeshExtraObjectsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    show_round_cube: bpy.props.BoolProperty(
        name = "Round Cube",
        default = True,
    )
    show_single_vert: bpy.props.BoolProperty(
        name = "Single Vert Menu",
        default = True,
    )
    show_torus_objects: bpy.props.BoolProperty(
        name = "Torus Objects Menu",
        default = True,
    )
    show_math_functions: bpy.props.BoolProperty(
        name = "Math Functions Menu",
        default = True,
    )
    show_gears: bpy.props.BoolProperty(
        name = "Gears Menu",
        default = True,
    )
    show_pipe_joints: bpy.props.BoolProperty(
        name = "Pipe Joints Menu",
        default = True,
    )
    show_gemstones: bpy.props.BoolProperty(
        name = "Gemstones Menu",
        default = True,
    )
    show_extras: bpy.props.BoolProperty(
        name = "Extras Menu",
        default = True,
    )
    show_parent_to_empty: bpy.props.BoolProperty(
        name = "Parent to Empty",
        default = True,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(heading="Filter Add Menu Items")
        col.prop(self, "show_round_cube")
        col.prop(self, "show_single_vert")
        col.prop(self, "show_torus_objects")
        col.prop(self, "show_math_functions")
        col.prop(self, "show_gears")
        col.prop(self, "show_pipe_joints")
        col.prop(self, "show_gemstones")
        col.prop(self, "show_extras")
        col.prop(self, "show_parent_to_empty")
