import bpy
from bpy.app.handlers import persistent

from .functions.set import add_boolean_modifier
from .functions.list import (
    list_selected_cutters,
    list_cutter_users,
)


# Duplicate Modifier for Duplicated Cutters
@persistent
def duplicate_boolean_modifier(scene, depsgraph):
    prefs = bpy.context.preferences.addons[__package__].preferences
    if prefs.experimental:
        if bpy.context.active_object and bpy.context.active_object.type == "MESH":
            cutters = list_selected_cutters(bpy.context)

            # find_original_cutter
            original_cutters = []
            for cutter in cutters:
                if cutter.booleans.cutter:
                    if ".0" in cutter.name:
                        if ".001" in cutter.name:
                            original_name = cutter.name.split('.')[0]
                        else:
                            name, number = cutter.name.rsplit('.', 1)
                            previous_number = str(int(number) - 1).zfill(len(number))
                            original_name = name + '.' + previous_number

                        for obj in bpy.data.objects:
                            if obj.name == original_name:
                                if obj.booleans.cutter:
                                    original_cutters.append(obj)

            # duplicate_modifiers
            if original_cutters:
                canvases = list_cutter_users(original_cutters)
                for canvas in canvases:
                    if canvas.booleans.slice == True:
                        return

                    for cutter in cutters:
                        if canvas == cutter:
                            return

                        if not any(modifier.object == cutter for modifier in canvas.modifiers):
                            for modifier in canvas.modifiers:
                                if modifier.type == 'BOOLEAN' and modifier.object in original_cutters:
                                    add_boolean_modifier(canvas, cutter, modifier.operation, prefs.solver)



#### ------------------------------ REGISTRATION ------------------------------ ####

def register():
    # HANDLER
    bpy.app.handlers.depsgraph_update_pre.append(duplicate_boolean_modifier)

def unregister():
    # HANDLER
    bpy.app.handlers.depsgraph_update_pre.remove(duplicate_boolean_modifier)
