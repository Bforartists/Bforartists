# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Object Color Rules",
    "author": "Campbell Barton",
    "version": (0, 0, 2),
    "blender": (2, 80, 0),
    "location": "Properties > Object Buttons",
    "description": "Rules for assigning object color (for object & wireframe colors).",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/object/color_rules.html",
    "category": "Object",
}


def test_name(rule, needle, haystack, cache):
    if rule.use_match_regex:
        if not cache:
            import re
            re_needle = re.compile(needle)
            cache[:] = [re_needle]
        else:
            re_needle = cache[0]
        return (re_needle.match(haystack) is not None)
    else:
        return (needle in haystack)


class rule_test:
    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        raise RuntimeError("%s should not be instantiated" % cls)

    @staticmethod
    def NAME(obj, rule, cache):
        match_name = rule.match_name
        return test_name(rule, match_name, obj.name, cache)

    def DATA(obj, rule, cache):
        match_name = rule.match_name
        obj_data = obj.data
        if obj_data is not None:
            return test_name(rule, match_name, obj_data.name, cache)
        else:
            return False

    @staticmethod
    def COLLECTION(obj, rule, cache):
        if not cache:
            match_name = rule.match_name
            objects = {o for g in bpy.data.collections if test_name(rule, match_name, g.name, cache) for o in g.objects}
            cache["objects"] = objects
        else:
            objects = cache["objects"]

        return obj in objects

    @staticmethod
    def MATERIAL(obj, rule, cache):
        match_name = rule.match_name
        materials = getattr(obj.data, "materials", None)

        return ((materials is not None) and
                (any((test_name(rule, match_name, m.name) for m in materials if m is not None))))

    @staticmethod
    def TYPE(obj, rule, cache):
        return (obj.type == rule.match_object_type)

    @staticmethod
    def EXPR(obj, rule, cache):
        if not cache:
            match_expr = rule.match_expr
            expr = compile(match_expr, rule.name, 'eval')

            namespace = {}
            namespace.update(__import__("math").__dict__)

            cache["expr"] = expr
            cache["namespace"] = namespace
        else:
            expr = cache["expr"]
            namespace = cache["namespace"]

        try:
            return bool(eval(expr, {}, {"self": obj}))
        except:
            import traceback
            traceback.print_exc()
            return False


class rule_draw:
    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        raise RuntimeError("%s should not be instantiated" % cls)

    @staticmethod
    def _generic_match_name(layout, rule):
        layout.label(text="Match Name:")
        row = layout.row(align=True)
        row.prop(rule, "match_name", text="")
        row.prop(rule, "use_match_regex", text="", icon='SORTALPHA')

    @staticmethod
    def NAME(layout, rule):
        rule_draw._generic_match_name(layout, rule)

    @staticmethod
    def DATA(layout, rule):
        rule_draw._generic_match_name(layout, rule)

    @staticmethod
    def COLLECTION(layout, rule):
        rule_draw._generic_match_name(layout, rule)

    @staticmethod
    def MATERIAL(layout, rule):
        rule_draw._generic_match_name(layout, rule)

    @staticmethod
    def TYPE(layout, rule):
        row = layout.row()
        row.prop(rule, "match_object_type")

    @staticmethod
    def EXPR(layout, rule):
        col = layout.column()
        col.label(text="Scripted Expression:")
        col.prop(rule, "match_expr", text="")


def object_colors_calc(rules, objects):
    from mathutils import Color

    rules_cb = [getattr(rule_test, rule.type) for rule in rules]
    rules_blend = [(1.0 - rule.factor, rule.factor) for rule in rules]
    rules_color = [Color(rule.color) for rule in rules]
    rules_cache = [{} for i in range(len(rules))]
    rules_inv = [rule.use_invert for rule in rules]
    changed_count = 0

    for obj in objects:
        is_set = False
        obj_color = Color(obj.color[0:3])

        for (rule, test_cb, color, blend, cache, use_invert) \
             in zip(rules, rules_cb, rules_color, rules_blend, rules_cache, rules_inv):

            if test_cb(obj, rule, cache) is not use_invert:
                if is_set is False:
                    obj_color = color
                else:
                    # prevent mixing colors losing saturation
                    obj_color_s = obj_color.s
                    obj_color = (obj_color * blend[0]) + (color * blend[1])
                    obj_color.s = (obj_color_s * blend[0]) + (color.s * blend[1])

                is_set = True

        if is_set:
            obj.color[0:3] = obj_color
            changed_count += 1
    return changed_count


def object_colors_select(rule, objects):
    cache = {}

    rule_type = rule.type
    test_cb = getattr(rule_test, rule_type)

    for obj in objects:
        obj.select_set(test_cb(obj, rule, cache))


def object_colors_rule_validate(rule, report):
    rule_type = rule.type

    if rule_type in {'NAME', 'DATA', 'COLLECTION', 'MATERIAL'}:
        if rule.use_match_regex:
            import re
            try:
                re.compile(rule.match_name)
            except Exception as e:
                report({'ERROR'}, "Rule %r: %s" % (rule.name, str(e)))
                return False

    elif rule_type == 'EXPR':
        try:
            compile(rule.match_expr, rule.name, 'eval')
        except Exception as e:
            report({'ERROR'}, "Rule %r: %s" % (rule.name, str(e)))
            return False

    return True



import bpy
from bpy.types import (
    Operator,
    Panel,
    UIList,
)
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    CollectionProperty,
    BoolVectorProperty,
    FloatVectorProperty,
)


class OBJECT_PT_color_rules(Panel):
    bl_label = "Color Rules"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        # Rig type list
        row = layout.row()
        row.template_list(
            "OBJECT_UL_color_rule", "color_rules",
            scene, "color_rules",
            scene, "color_rules_active_index",
        )

        col = row.column()
        colsub = col.column(align=True)
        colsub.operator("object.color_rules_add", icon='ADD', text="")
        colsub.operator("object.color_rules_remove", icon='REMOVE', text="")

        colsub = col.column(align=True)
        colsub.operator("object.color_rules_move", text="", icon='TRIA_UP').direction = -1
        colsub.operator("object.color_rules_move", text="", icon='TRIA_DOWN').direction = 1

        colsub = col.column(align=True)
        colsub.operator("object.color_rules_select", text="", icon='RESTRICT_SELECT_OFF')

        if scene.color_rules:
            index = scene.color_rules_active_index
            rule = scene.color_rules[index]

            box = layout.box()
            row = box.row(align=True)
            row.prop(rule, "name", text="")
            row.prop(rule, "type", text="")
            row.prop(rule, "use_invert", text="", icon='ARROW_LEFTRIGHT')

            draw_cb = getattr(rule_draw, rule.type)
            draw_cb(box, rule)

            row = layout.split(factor=0.75, align=True)
            props = row.operator("object.color_rules_assign", text="Assign Selected")
            props.use_selection = True
            props = row.operator("object.color_rules_assign", text="All")
            props.use_selection = False


class OBJECT_UL_color_rule(UIList):
    def draw_item(self, context, layout, data, rule, icon, active_data, active_propname, index):
        # assert(isinstance(rule, bpy.types.ShapeKey))
        # scene = active_data
        split = layout.split(factor=0.5)
        row = split.split(align=False)
        row.label(text="%s (%s)" % (rule.name, rule.type.lower()))
        split = split.split(factor=0.7)
        split.prop(rule, "factor", text="", emboss=False)
        split.prop(rule, "color", text="")


class OBJECT_OT_color_rules_assign(Operator):
    """Assign colors to objects based on user rules"""
    bl_idname = "object.color_rules_assign"
    bl_label = "Assign Colors"
    bl_options = {'UNDO'}

    use_selection: BoolProperty(
        name="Selected",
        description="Apply to selected (otherwise all objects in the scene)",
        default=True,
    )

    def execute(self, context):
        scene = context.scene

        if self.use_selection:
            objects = context.selected_editable_objects
        else:
            objects = scene.objects

        rules = scene.color_rules[:]
        for rule in rules:
            if not object_colors_rule_validate(rule, self.report):
                return {'CANCELLED'}

        changed_count = object_colors_calc(rules, objects)
        self.report({'INFO'}, "Set colors for {} of {} objects".format(changed_count, len(objects)))
        return {'FINISHED'}


class OBJECT_OT_color_rules_select(Operator):
    """Select objects matching the current rule"""
    bl_idname = "object.color_rules_select"
    bl_label = "Select Rule"
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        rule = scene.color_rules[scene.color_rules_active_index]

        if not object_colors_rule_validate(rule, self.report):
            return {'CANCELLED'}

        objects = context.visible_objects
        object_colors_select(rule, objects)
        return {'FINISHED'}


class OBJECT_OT_color_rules_add(Operator):
    bl_idname = "object.color_rules_add"
    bl_label = "Add Color Layer"
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        rules = scene.color_rules
        rule = rules.add()
        rule.name = "Rule.%.3d" % len(rules)
        scene.color_rules_active_index = len(rules) - 1
        return {'FINISHED'}


class OBJECT_OT_color_rules_remove(Operator):
    bl_idname = "object.color_rules_remove"
    bl_label = "Remove Color Layer"
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        rules = scene.color_rules
        rules.remove(scene.color_rules_active_index)
        if scene.color_rules_active_index > len(rules) - 1:
            scene.color_rules_active_index = len(rules) - 1
        return {'FINISHED'}


class OBJECT_OT_color_rules_move(Operator):
    bl_idname = "object.color_rules_move"
    bl_label = "Remove Color Layer"
    bl_options = {'UNDO'}
    direction: IntProperty()

    def execute(self, context):
        scene = context.scene
        rules = scene.color_rules
        index = scene.color_rules_active_index
        index_new = index + self.direction
        if index_new < len(rules) and index_new >= 0:
            rules.move(index, index_new)
            scene.color_rules_active_index = index_new
            return {'FINISHED'}
        else:
            return {'CANCELLED'}


class ColorRule(bpy.types.PropertyGroup):
    name: StringProperty(
        name="Rule Name",
    )
    color: FloatVectorProperty(
        name="Color",
        description="Color to assign",
        subtype='COLOR', size=3, min=0, max=1, precision=3, step=0.1,
        default=(0.5, 0.5, 0.5),
    )
    factor: FloatProperty(
        name="Opacity",
        description="Color to assign",
        min=0, max=1, precision=1, step=0.1,
        default=1.0,
    )
    type: EnumProperty(
        name="Rule Type",
        items=(
            ('NAME', "Name", "Object name contains this text (or matches regex)"),
            ('DATA', "Data Name", "Object data name contains this text (or matches regex)"),
            ('COLLECTION', "Collection Name", "Object in collection that contains this text (or matches regex)"),
            ('MATERIAL', "Material Name", "Object uses a material name that contains this text (or matches regex)"),
            ('TYPE', "Type", "Object type"),
            ('EXPR', "Expression", (
                "Scripted expression (using 'self' for the object) eg:\n"
                "  self.type == 'MESH' and len(self.data.vertices) > 20"
            )
            ),
        ),
    )

    use_invert: BoolProperty(
        name="Invert",
        description="Match when the rule isn't met",
    )

    # ------------------
    # Matching Variables

    # shared by all name matching
    match_name: StringProperty(
        name="Match Name",
    )
    use_match_regex: BoolProperty(
        name="Regex",
        description="Use regular expressions for pattern matching",
    )
    # type == 'TYPE'
    match_object_type: EnumProperty(
        name="Object Type",
        items=([(i.identifier, i.name, "")
                for i in bpy.types.Object.bl_rna.properties['type'].enum_items]
               )
    )
    # type == 'EXPR'
    match_expr: StringProperty(
        name="Expression",
        description="Python expression, where 'self' is the object variable"
    )


classes = (
    OBJECT_PT_color_rules,
    OBJECT_OT_color_rules_add,
    OBJECT_OT_color_rules_remove,
    OBJECT_OT_color_rules_move,
    OBJECT_OT_color_rules_assign,
    OBJECT_OT_color_rules_select,
    OBJECT_UL_color_rule,
    ColorRule,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.color_rules = CollectionProperty(type=ColorRule)
    bpy.types.Scene.color_rules_active_index = IntProperty()


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.color_rules
