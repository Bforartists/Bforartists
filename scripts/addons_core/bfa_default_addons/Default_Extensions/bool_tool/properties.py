import bpy


#### ------------------------------ PROPERTIES ------------------------------ ####

class OBJECT_PG_booleans(bpy.types.PropertyGroup):
    # OBJECT-level Properties

    canvas: bpy.props.BoolProperty(
        name = "Boolean Canvas",
        default = False,
    )
    cutter: bpy.props.StringProperty(
        name = "Boolean Cutter",
    )
    slice: bpy.props.BoolProperty(
        name = "Boolean Slice",
        default = False,
    )

    slice_of: bpy.props.PointerProperty(
        name = "Slice of...",
        type = bpy.types.Object,
    )

    cutters_active_index: bpy.props.IntProperty(
        name = "Active Cutter Index",
        default = -1,
    )



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_PG_booleans,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # PROPERTY
    bpy.types.Object.booleans = bpy.props.PointerProperty(type=OBJECT_PG_booleans, name="Boolean Tools")


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # PROPERTY
    del bpy.types.Object.booleans
