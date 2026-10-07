import bpy


#### ------------------------------ PROPERTIES ------------------------------ ####

class OBJECT_PG_booleans(bpy.types.PropertyGroup):
    # OBJECT-level Properties

    canvas: bpy.props.BoolProperty(
        name = "Boolean Canvas",
        options = set(),
        default = False,
    )
    cutter: bpy.props.StringProperty(
        name = "Boolean Cutter",
        options = set(),
    )
    slice: bpy.props.BoolProperty(
        name = "Boolean Slice",
        options = set(),
        default = False,
    )

    slice_of: bpy.props.PointerProperty(
        name = "Slice of...",
        type = bpy.types.Object,
        options = set(),
    )
    carver: bpy.props.BoolProperty(
        name = "Is Carver Cutter",
        options = set(),
        default = False,
    )

    modifiers_list_index: bpy.props.IntProperty()



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = (
    OBJECT_PG_booleans,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # PROPERTY
    bpy.types.Object.booleans = bpy.props.PointerProperty(type=OBJECT_PG_booleans, name="Booleans")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # PROPERTY
    del bpy.types.Object.booleans
