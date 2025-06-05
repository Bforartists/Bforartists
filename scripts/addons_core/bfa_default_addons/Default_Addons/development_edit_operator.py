# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later


bl_info = {
    "name": "Edit Operator Source",
    "author": "scorpion81",
    "version": (1, 2, 3),
    "blender": (3, 2, 0),
    "location": "Text Editor > Sidebar > Edit Operator",
    "description": "Opens source file of chosen operator or call locations, if source not available",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/development/edit_operator.html",
    "category": "Development",
}

import bpy
import sys
import os
import inspect
from bpy.types import (
        Operator,
        Panel,
        Header,
        Menu,
        PropertyGroup
        )
from bpy.props import (
        EnumProperty,
        StringProperty,
        IntProperty
        )

def make_loc(prefix, c):
    #too long and not helpful... omitting for now
    space = ""
    #if hasattr(c, "bl_space_type"):
    #    space = c.bl_space_type

    region = ""
    #if hasattr(c, "bl_region_type"):
    #   region = c.bl_region_type

    label = ""
    if hasattr(c, "bl_label"):
        label = c.bl_label

    return prefix+": " + space + " " + region + " " + label

def walk_module(opname, mod, calls=[], exclude=[]):

    for name, m in inspect.getmembers(mod):
        if inspect.ismodule(m):
            if m.__name__ not in exclude:
                #print(name, m.__name__)
                walk_module(opname, m, calls, exclude)
        elif inspect.isclass(m):
            if (issubclass(m, Panel) or \
                issubclass(m, Header) or \
                issubclass(m, Menu)) and mod.__name__ != "bl_ui":
                if hasattr(m, "draw"):
                    loc = ""
                    file = ""
                    line = -1
                    src, n = inspect.getsourcelines(m.draw)
                    for i, s in enumerate(src):
                        if opname in s:
                            file = mod.__file__
                            line = n + i

                            if issubclass(m, Panel) and name != "Panel":
                                loc = make_loc("Panel", m)
                                calls.append([opname, loc, file, line])
                            if issubclass(m, Header) and name != "Header":
                                loc = make_loc("Header", m)
                                calls.append([opname, loc, file, line])
                            if issubclass(m, Menu) and name != "Menu":
                                loc = make_loc("Menu", m)
                                calls.append([opname, loc, file, line])


def getclazz(opname):
    opid = opname.split(".")
    opmod = getattr(bpy.ops, opid[0])
    op = getattr(opmod, opid[1])
    id = op.get_rna_type().bl_rna.identifier
    try:
        clazz = getattr(bpy.types, id)
        return clazz
    except AttributeError:
        return None


def getmodule(opname):
    addon = True
    clazz = getclazz(opname)

    if clazz is None:
        return  "", -1, False

    modn = clazz.__module__

    try:
        line = inspect.getsourcelines(clazz)[1]
    except IOError:
        line = -1
    except TypeError:
        line = -1

    if modn == 'bpy.types':
        mod = 'C operator'
        addon = False
    elif modn != '__main__':
        mod = sys.modules[modn].__file__
    else:
        addon = False
        mod = modn

    return mod, line, addon


def get_ops():
    allops = []
    opsdir = dir(bpy.ops)
    for opmodname in opsdir:
        opmod = getattr(bpy.ops, opmodname)
        opmoddir = dir(opmod)
        for o in opmoddir:
            name = opmodname + "." + o
            clazz = getclazz(name)
            #if (clazz is not None) :# and clazz.__module__ != 'bpy.types'):
            allops.append(name)
        del opmoddir

    # add own operator name too, since its not loaded yet when this is called
    allops.append("text.edit_operator")
    l = sorted(allops)
    del allops
    del opsdir

    return [(y, y, "", x) for x, y in enumerate(l)]

class OperatorEntry(PropertyGroup):

    label : StringProperty(
            name="Label",
            description="",
            default=""
            )

    path : StringProperty(
            name="Path",
            description="",
            default=""
            )

    line : IntProperty(
            name="Line",
            description="",
            default=-1
            )

class TEXT_OT_EditOperator(Operator):
    bl_idname = "text.edit_operator"
    bl_label = "Edit Operator"
    bl_description = "Opens the source file of operators chosen from Menu"
    bl_property = "op"

    items = get_ops()

    op : EnumProperty(
            name="Op",
            description="",
            items=items
            )

    path : StringProperty(
            name="Path",
            description="",
            default=""
            )

    line : IntProperty(
            name="Line",
            description="",
            default=-1
            )

    def show_text(self, context, path, line):
        found = False

        for t in bpy.data.texts:
            if t.filepath == path:
                #switch to the wanted text first
                context.space_data.text = t
                ctx = context.copy()
                ctx['edit_text'] = t
                bpy.ops.text.jump(ctx, line=line)
                found = True
                break

        if (found is False):
            self.report({'INFO'},
                        "Opened file: " + path)
            bpy.ops.text.open(filepath=path)
            bpy.ops.text.jump(line=line)

    def show_calls(self, context):
        import bl_ui
        import addon_utils
        import sys

        exclude = []
        exclude.extend(sys.stdlib_module_names)
        exclude.append("bpy")
        exclude.append("sys")

        calls = []
        walk_module(self.op, bl_ui, calls, exclude)

        for m in addon_utils.modules():
            try:
                mod = sys.modules[m.__name__]
                walk_module(self.op, mod, calls, exclude)
            except KeyError:
                continue

        for c in calls:
            cl = context.scene.calls.add()
            cl.name = c[0]
            cl.label = c[1]
            cl.path = c[2]
            cl.line = c[3]

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'PASS_THROUGH'}

    def execute(self, context):
        if self.path != "" and self.line != -1:
            #invocation of one of the "found" locations
            self.show_text(context, self.path, self.line)
            return {'FINISHED'}
        else:
            context.scene.calls.clear()
            path, line, addon = getmodule(self.op)

            if addon:
                self.show_text(context, path, line)

                #add convenient "source" button, to toggle back from calls to source
                c = context.scene.calls.add()
                c.name = self.op
                c.label = "Source"
                c.path = path
                c.line = line

                self.show_calls(context)
                context.area.tag_redraw()

                return {'FINISHED'}
            else:

                self.report({'WARNING'},
                            "Found no source file for " + self.op)

                self.show_calls(context)
                context.area.tag_redraw()

                return {'FINISHED'}


class TEXT_PT_EditOperatorPanel(Panel):
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Edit Operator"
    bl_category = "Text"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        op = layout.operator("text.edit_operator")
        op.path = ""
        op.line = -1

        if len(context.scene.calls) > 0:
            box = layout.box()
            box.label(text="Calls of: " + context.scene.calls[0].name)
            box.operator_context = 'EXEC_DEFAULT'
            for c in context.scene.calls:
                op = box.operator("text.edit_operator", text=c.label)
                op.path = c.path
                op.line = c.line
                op.op = c.name


def register():
    bpy.utils.register_class(OperatorEntry)
    bpy.types.Scene.calls = bpy.props.CollectionProperty(name="Calls",
                                                         type=OperatorEntry)
    bpy.utils.register_class(TEXT_OT_EditOperator)
    bpy.utils.register_class(TEXT_PT_EditOperatorPanel)


def unregister():
    bpy.utils.unregister_class(TEXT_PT_EditOperatorPanel)
    bpy.utils.unregister_class(TEXT_OT_EditOperator)
    del bpy.types.Scene.calls
    bpy.utils.unregister_class(OperatorEntry)


if __name__ == "__main__":
    register()
