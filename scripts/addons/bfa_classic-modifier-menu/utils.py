import bpy


def fetch_user_preferences(attr_id=None):
    prefs = bpy.context.preferences.addons[__package__].preferences

    if attr_id is None:
        return prefs
    else:
        return getattr(prefs, attr_id)


def fetch_op_data(class_name):
    type_class = getattr(bpy.types, class_name)
    type_props = type_class.bl_rna.properties["type"]

    OPERATOR_DATA = {
        enum_it.identifier: (enum_it.name, enum_it.icon)
            for enum_it in type_props.enum_items_static
        }

    TRANSLATION_CONTEXT = type_props.translation_context

    return (OPERATOR_DATA, TRANSLATION_CONTEXT)
