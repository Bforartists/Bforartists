import bpy


@bpy.app.handlers.persistent
def populate_boolean_properties(scene):
    prefs = bpy.context.preferences.addons[__package__].preferences
    if prefs.versioning:
        for obj in bpy.data.objects:
            if not obj.get("BoolToolRoot"):
                continue

            # convert_canvas
            if obj.get("BoolToolRoot"):
                obj.booleans.canvas = True
                del obj["BoolToolRoot"]
                if obj.get("BoolTool_FTransform"):
                    del obj["BoolTool_FTransform"]

                for modifier in obj.modifiers:
                    if modifier.type == 'BOOLEAN' and "BTool_" in modifier.name:
                        modifier.name = "boolean_" + modifier.object.name
                        cutter = modifier.object

                        if cutter.get("BoolToolBrush"):
                            cutter.booleans.cutter = cutter.get("BoolToolBrush")
                            del cutter["BoolToolBrush"]
                            if cutter.get("BoolTool_FTransform"):
                                del cutter["BoolTool_FTransform"]



#### ------------------------------ REGISTRATION ------------------------------ ####

def register():
    # HANDLERS
    bpy.app.handlers.load_post.append(populate_boolean_properties)

def unregister():
    # HANDLERS
    bpy.app.handlers.load_post.remove(populate_boolean_properties)
