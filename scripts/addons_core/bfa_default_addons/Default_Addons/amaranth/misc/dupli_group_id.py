# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Object ID for Dupli Groups
Say you have a linked character or asset, you can now set an Object ID for the
entire instance (the objects in the group), and use it with the Object Index
pass later in compositing. Something that I always wanted and it wasn't
possible!

In order for the Object ID to be loaded afterwards on computers without
Amaranth installed, it will automatically create a text file (called
AmaranthStartup.py) and save it inside the .blend, this will autorun on
startup and set the OB IDs. Remember to have auto-run python scripts on your
startup preferences.

Set a Pass Index and press "Apply Object ID to Duplis" on the Relations panel,
Object Properties.
"""


import bpy
from amaranth.scene.debug import AMTH_SCENE_OT_blender_instance_open


# Some settings are bound to be saved on a startup py file
# TODO: refactor this, amth_text should not be declared as a global variable,
#       otherwise becomes confusing when you call it in the classes below.
def amaranth_text_startup(context):

    amth_text_name = "AmaranthStartup.py"
    amth_text_exists = False

    global amth_text

    try:
        if bpy.data.texts:
            for tx in bpy.data.texts:
                if tx.name == amth_text_name:
                    amth_text_exists = True
                    amth_text = bpy.data.texts[amth_text_name]
                    break
                else:
                    amth_text_exists = False

        if not amth_text_exists:
            bpy.ops.text.new()
            amth_text = bpy.data.texts[((len(bpy.data.texts) * -1) + 1)]
            amth_text.name = amth_text_name
            amth_text.write("# Amaranth Startup Script\nimport bpy\n")
            amth_text.use_module = True

        return amth_text_exists
    except AttributeError:
        return None


# FEATURE: Dupli  Group Path
def ui_dupli_group_library_path(self, context):

    ob = context.object

    row = self.layout.row()
    row.alignment = "LEFT"

    if ob and ob.instance_collection and ob.instance_collection.library:
        lib = ob.instance_collection.library.filepath

        row.operator(AMTH_SCENE_OT_blender_instance_open.bl_idname,
                     text="Library: %s" % lib,
                     emboss=False,
                     icon="LINK_BLEND").filepath = lib
# // FEATURE: Dupli  Group Path


# FEATURE: Object ID for objects inside DupliGroups
class AMTH_OBJECT_OT_id_dupligroup(bpy.types.Operator):

    """Set the Object ID for objects in the dupli group"""
    bl_idname = "object.amaranth_object_id_duplis"
    bl_label = "Apply Object ID to Duplis"

    clear = False

    @classmethod
    def poll(cls, context):
        return context.active_object.instance_collection

    def execute(self, context):
        self.__class__.clear = False
        ob = context.active_object
        amaranth_text_startup(context)
        script_exists = False
        script_intro = "# OB ID: %s" % ob.name
        obdata = 'bpy.data.objects[" % s"]' % ob.name
        # TODO: cleanup script var using format or template strings
        script = "%s" % (
            "\nif %(obdata)s and %(obdata)s.instance_collection and %(obdata)s.pass_index != 0: %(obname)s \n"
            "    for dob in %(obdata)s.instance_collection.objects: %(obname)s \n"
            "        dob.pass_index = %(obdata)s.pass_index %(obname)s \n" %
            {"obdata": obdata, "obname": script_intro})

        for txt in bpy.data.texts:
            if txt.name == amth_text.name:
                for li in txt.lines:
                    if script_intro == li.body:
                        script_exists = True
                        continue

        if not script_exists:
            amth_text.write("\n")
            amth_text.write(script_intro)
            amth_text.write(script)

        if ob and ob.instance_collection:
            if ob.pass_index != 0:
                for dob in ob.instance_collection.objects:
                    dob.pass_index = ob.pass_index

        self.report({"INFO"},
                    "%s ID: %s to all objects in this Dupli Group" % (
                        "Applied" if not script_exists else "Updated",
                        ob.pass_index))

        return {"FINISHED"}


class AMTH_OBJECT_OT_id_dupligroup_clear(bpy.types.Operator):

    """Clear the Object ID from objects in dupli group"""
    bl_idname = "object.amaranth_object_id_duplis_clear"
    bl_label = "Clear Object ID from Duplis"

    @classmethod
    def poll(cls, context):
        return context.active_object.instance_collection

    def execute(self, context):
        context.active_object.pass_index = 0
        AMTH_OBJECT_OT_id_dupligroup.clear = True
        amth_text_exists = amaranth_text_startup(context)
        match_first = "# OB ID: %s" % context.active_object.name

        if amth_text_exists:
            for txt in bpy.data.texts:
                if txt.name == amth_text.name:
                    for li in txt.lines:
                        if match_first in li.body:
                            li.body = ""
                            continue

        self.report({"INFO"}, "Object IDs back to normal")
        return {"FINISHED"}


def ui_object_id_duplis(self, context):

    if context.active_object.instance_collection:
        split = self.layout.split()
        row = split.row(align=True)
        row.enabled = context.active_object.pass_index != 0
        row.operator(
            AMTH_OBJECT_OT_id_dupligroup.bl_idname)
        row.operator(
            AMTH_OBJECT_OT_id_dupligroup_clear.bl_idname,
            icon="X", text="")
        split.separator()

        if AMTH_OBJECT_OT_id_dupligroup.clear:
            self.layout.label(text="Next time you save/reload this file, "
                              "object IDs will be back to normal",
                              icon="INFO")
# // FEATURE: Object ID for objects inside DupliGroups


def register():
    bpy.utils.register_class(AMTH_OBJECT_OT_id_dupligroup)
    bpy.utils.register_class(AMTH_OBJECT_OT_id_dupligroup_clear)
    bpy.types.OBJECT_PT_instancing.append(ui_dupli_group_library_path)
    bpy.types.OBJECT_PT_relations.append(ui_object_id_duplis)


def unregister():
    bpy.utils.unregister_class(AMTH_OBJECT_OT_id_dupligroup)
    bpy.utils.unregister_class(AMTH_OBJECT_OT_id_dupligroup_clear)
    bpy.types.OBJECT_PT_instancing.remove(ui_dupli_group_library_path)
    bpy.types.OBJECT_PT_relations.remove(ui_object_id_duplis)
