# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
# by LeoMoon Studios, Marcin Zielinski, Martin Wacker,
# Bassam Kurdali, Jared Felsman, meta-androcto #

bl_info = {
    "name": "Animated Text",
    "author": "LeoMoon Studios, Marcin Zielinski, Martin Wacker, "
              "Bassam Kurdali, Jared Felsman, meta-androcto",
    "version": (0, 3, 1),
    "blender": (2, 74, 5),
    "location": "Properties Editor > Font",
    "description": "Typing & Counting Animated Text",
    "warning": "",
    "wiki_url": "",
    "category": "Animation"
}

import bpy
import random
from bpy.types import (
        Operator,
        Panel,
        PropertyGroup,
        )
from bpy.props import (
        FloatProperty,
        PointerProperty,
        BoolProperty,
        IntProperty,
        EnumProperty,
        StringProperty,
        )
from bpy.app.handlers import persistent


# In case of error set it to true so it can be used for console runes
DEBUG = False


# Use just as a regular print (switchable as the UI will be constantly updated
def debug_print_vars(*args, **kwargs):
    global DEBUG
    if DEBUG:
        print(*args, **kwargs)


def formatCounter(inputs, timeSeparators, timeLeadZeroes, timeTrailZeroes, timeModulo):
    f = 0
    s = 0
    m = 0
    h = 0
    out = ''
    neg = ''
    if inputs < 0:
        neg = '-'
        inputs = abs(inputs)

    if timeSeparators >= 0:
        if timeSeparators == 0:
            out = int(inputs)
            out = format(out, '0' + str(timeLeadZeroes) + 'd')
        else:
            s, f = divmod(int(inputs), timeModulo)
            out = format(f, '0' + str(timeLeadZeroes) + 'd')

    if timeSeparators >= 1:
        if timeSeparators == 1:
            out = format(s, '0' + str(timeTrailZeroes) + 'd') + ":" + out
        else:
            m, s = divmod(s, 60)
            out = format(s, '02d') + ":" + out

    if timeSeparators >= 2:
        if timeSeparators == 2:
            out = format(m, '0' + str(timeTrailZeroes) + 'd') + ":" + out
        else:
            h, m = divmod(m, 60)
            out = format(m, '02d') + ":" + out

    if timeSeparators >= 3:
        out = format(h, '0' + str(timeTrailZeroes) + 'd') + ":" + out

    return neg + out


class TextCounter_Props(PropertyGroup):

    # A placeholder for the text box
    default_string = 'Enter a number or an expression'

    def val_up(self, context):
        textcounter_update_val(context.object, context.scene)

    ifAnimated = BoolProperty(
        name='Counter Active',
        default=False,
        update=val_up
        )
    counter = FloatProperty(
        name='Counter',
        update=val_up
        )
    padding = IntProperty(
        name='Padding',
        update=val_up,
        min=1
        )
    ifDecimal = BoolProperty(
        name='Decimal',
        default=False,
        update=val_up
        )
    decimals = IntProperty(
        name='Decimal',
        update=val_up,
        min=0
        )
    typeEnum = EnumProperty(
        items=[
            ('ANIMATED', 'Animated', 'Counter values from f-curves'),
            ('DYNAMIC', 'Dynamic', 'Counter values from expression')
        ],
        name='Type',
        update=val_up,
        default='ANIMATED'
        )
    formattingEnum = EnumProperty(
        items=[
            ('NUMBER', 'Number', 'Counter values as numbers'),
            ('TIME', 'Time', 'Counter values as time')
        ],
        name='Formatting Type',
        update=val_up,
        default='NUMBER'
        )
    # set to 0 as eval will crash in it's default state
    expr = StringProperty(
        name='Expression',
        description="Enter a number or a numeric expression",
        update=val_up,
        default=default_string
        )
    prefix = StringProperty(
        name='Prefix',
        update=val_up,
        default=''
        )
    sufix = StringProperty(
        name='Sufix',
        update=val_up,
        default=''
        )
    ifTextFile = BoolProperty(
        name='Override with Text File',
        default=False,
        update=val_up
        )
    textFile = StringProperty(
        name='Text File',
        update=val_up,
        default=''
        )
    ifTextFormatting = BoolProperty(
        name='Numerical Formatting',
        default=False,
        update=val_up
        )
    timeSeparators = IntProperty(
        name='Separators',
        update=val_up,
        min=0, max=3
        )
    timeModulo = IntProperty(
        name='Last Separator Modulo',
        update=val_up,
        min=1,
        default=24
        )
    timeLeadZeroes = IntProperty(
        name='Leading Zeroes',
        update=val_up,
        min=1,
        default=2
        )
    timeTrailZeroes = IntProperty(
        name='Trailing Zeroes',
        update=val_up,
        min=1,
        default=2
        )

    str_error = False

    def dyn_get(self):
        try:
            TextCounter_Props.str_error = False
            if self.expr in [TextCounter_Props.default_string, None, ""]:
                return '0'
            return str(eval(self.expr))
        except Exception as e:
            TextCounter_Props.str_error = True
            debug_print_vars('Expr Error: ' + str(e.args))
            return '0'

    dynamicCounter = StringProperty(
        name='Dynamic Counter',
        get=dyn_get,
        default=''
        )

    def form_up(self, context):
        textcounter_update_val(context.object, context.scene)

    def form_get(self):
        inputs = 0

        if self.typeEnum == 'ANIMATED':
            inputs = float(self.counter)
        elif self.typeEnum == 'DYNAMIC':
            inputs = float(self.dynamicCounter)
        return formatCounter(inputs, self.timeSeparators, self.timeLeadZeroes,
                             self.timeTrailZeroes, self.timeModulo)

    def form_set(self, value):
        counter = 0
        separators = value.split(':')
        for idx, i in enumerate(separators[:-1]):
            counter += int(i) * 60**(len(separators) - 2 - idx) * self.timeModulo
        counter += int(separators[-1])
        self.counter = float(counter)

    formattedCounter = StringProperty(
        name='Formatted Counter',
        get=form_get,
        set=form_set,
        default=''
        )


def textcounter_update_val(text, scene):
    text.update_tag(refresh={'DATA'})
    props = text.data.text_counter_props
    counter = 0
    line = ''
    out = ''
    neg = ''

    if props.typeEnum == 'ANIMATED':
        counter = props.counter
    elif props.typeEnum == 'DYNAMIC':
        if props.expr in [props.default_string, None, ""]:
            return 0
        try:
            counter = eval(props.expr)
        except Exception as e:
            debug_print_vars('Expr Error: ' + str(e.args))

    isNumeric = True  # always true for counter not overrided
    if props.ifTextFile:
        txt = bpy.data.texts[props.textFile] if \
              props.textFile in bpy.data.texts.keys() else None
        if txt:
            clampedCounter = max(0, min(int(counter), len(txt.lines) - 1))
            line = txt.lines[clampedCounter].body
            if props.ifTextFormatting:
                try:
                    line = float(line)
                except Exception as ex:
                    debug_print_vars('Expr Error: ' + str(ex.args))
                    isNumeric = False
                    out = line
            else:
                isNumeric = False
                out = line
        else:
            line = counter
    else:
        line = counter

    if isNumeric:
        if props.formattingEnum == 'NUMBER':
            # add minus before padding zeroes
            neg = '-' if line < 0 else ''
            line = abs(line)
            # int / decimal
            if not props.ifDecimal:
                line = int(line)
            out = ('{:.' + str(props.decimals) + 'f}').format(line)

            # padding
            arr = out.split('.')
            arr[0] = arr[0].zfill(props.padding)
            out = arr[0]
            if len(arr) > 1:
                out += '.' + arr[1]
        elif props.formattingEnum == 'TIME':
            out = formatCounter(
                        line, props.timeSeparators, props.timeLeadZeroes,
                        props.timeTrailZeroes, props.timeModulo
                        )

    # prefix/sufix
    if props.ifTextFile:
        text.data.body = out
        if props.ifTextFormatting and isNumeric:
            text.data.body = props.prefix + neg + out + props.sufix
    else:
        text.data.body = props.prefix + neg + out + props.sufix


@persistent
def textcounter_text_update_frame(scene):
    for text in scene.objects:
        if text.type == 'FONT' and text.data.text_counter_props.ifAnimated:
            textcounter_update_val(text, scene)


# text scrambler #

@persistent
def textscrambler_update_frame(scene):
    for text in scene.objects:
        if text.type == 'FONT' and text.data.use_text_scrambler:
            uptext(text.data)


def update_func(self, context):
    uptext(self)


# Register all operators and panels

def uptext(text):
    source = text.source_text
    if source in bpy.data.texts:
        r = bpy.data.texts[source].as_string()
    else:
        r = source

    base = len(r)
    prog = text.scrambler_progress / 100.0

    c = int(base * prog)

    clean = r[:base - c]
    scrambled = ""
    for i in range(c):
        scrambled += random.choice(text.characters)
    text.body = clean + scrambled


# Typing Text #

def animate_text(scene):

    objects = scene.objects

    for obj in objects:
        if obj.type == "FONT" and "runAnimation" in obj and obj.runAnimation:
            endFrame = obj.startFrame + (len(obj.defaultTextBody) * obj.typeSpeed)
            if obj.manualEndFrame:
                endFrame = obj.endFrame

            if scene.frame_current < obj.startFrame:
                obj.data.body = ""

            elif scene.frame_current >= obj.startFrame and scene.frame_current <= endFrame:
                frameStringLength = (scene.frame_current - obj.startFrame) / obj.typeSpeed
                obj.data.body = obj.defaultTextBody[0:int(frameStringLength)]

            elif scene.frame_current > endFrame:
                obj.data.body = obj.defaultTextBody


# Typewriter #

def uptext1(text):
    '''
    slice the source text up to the character_count
    '''
    source = text.source_text
    if source in bpy.data.texts:
        text.body = bpy.data.texts[source].as_string()[:text.character_count]
    else:
        text.body = source[:text.character_count]


@persistent
def typewriter_text_update_frame(scene):
    '''
    sadly we need this for frame change updating
    '''
    for text in scene.objects:
        if text.type == 'FONT' and text.data.use_animated_text:
            uptext1(text.data)


def update_func1(self, context):
    '''
    updates when changing the value
    '''
    uptext1(self)


class TextCounterPanel(Panel):
    """Creates a Panel in the Font properties window"""
    bl_label = "Text Counter"
    bl_idname = "text_counter_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'FONT'

    def draw_header(self, context):
        self.layout.prop(context.object.data.text_counter_props, 'ifAnimated', '')

    def draw(self, context):
        props = context.object.data.text_counter_props
        error = props.str_error

        layout = self.layout
        layout.enabled = props.ifAnimated
        row = layout.row()
        row.prop(props, 'typeEnum', expand=True)

        row = layout.row()
        if props.typeEnum == 'ANIMATED':
            row.prop(props, 'counter')
        elif props.typeEnum == 'DYNAMIC':
            row.alert = error
            row.prop(props, 'expr')
            row = layout.row()
            row.prop(props, 'dynamicCounter')

        # formatting type enum
        boxy = layout.box()
        split = boxy.split(align=True)
        col = split.column()
        row = col.row(align=True)
        row.prop(props, 'formattingEnum', expand=True)

        if props.formattingEnum == 'NUMBER':
            row = col.row(align=True)
            row.prop(props, 'ifDecimal')
            row.prop(props, 'padding')
            row.prop(props, 'decimals')
            row = col.row(align=True)
            row.prop(props, 'prefix')
            row.prop(props, 'sufix')
        elif props.formattingEnum == 'TIME':
            row = col.row(align=True)
            row.prop(props, 'formattedCounter')

            row = col.row(align=False)
            row.prop(props, 'timeSeparators')
            row.prop(props, 'timeModulo')

            row = col.row(align=True)
            row.prop(props, 'timeLeadZeroes')
            row.prop(props, 'timeTrailZeroes')
            row = col.row(align=True)
            row.prop(props, 'prefix')
            row.prop(props, 'sufix')

        boxy = layout.box()
        row = boxy.row()
        row.prop(props, 'ifTextFile')
        row = boxy.row()
        row.prop(props, "ifTextFormatting")
        row.prop_search(props, "textFile", bpy.data, "texts", text="Text File")
        if not props.ifTextFile:
            row.enabled = False


class TEXT_PT_Textscrambler(Panel):
    bl_label = "Text scrambler"
    bl_idname = "TEXT_PT_Textscrambler"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'FONT'

    def draw_header(self, context):
        text = context.active_object.data
        layout = self.layout
        layout.prop(text, 'use_text_scrambler', text="")

    def draw(self, context):
        text = context.active_object.data
        layout = self.layout
        layout.prop(text, 'scrambler_progress', text="Progress")
        layout.prop(text, 'source_text', text="Source text")
        layout.prop(text, 'characters', text="Characters")


class makeTextAnimatedPanel(Panel):
    bl_label = "Typing Animation"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_idname = "OBJECT_PT_animtext"
    bl_context = "data"

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.type == 'FONT'

    def draw(self, context):
        layout = self.layout
        obj = bpy.context.active_object
        row = layout.row()
        row.prop(obj, "runAnimation")

        if obj.runAnimation:
            row = layout.row()
            row.prop(obj, "defaultTextBody")

            row = layout.row()
            row.operator("animate.set_text", text="Use Current Text", icon="TEXT")

            row = layout.row()
            row.prop(obj, "typeSpeed")

            row = layout.row()
            row.prop(obj, "startFrame")
            row.operator("animate.set_start_frame", text="Use Current Frame", icon="TIME")

            row = layout.row()
            row.label(text="Calculated End Frame : " +
                      str(obj.startFrame + (len(obj.defaultTextBody) * obj.typeSpeed)))
            row.prop(obj, "manualEndFrame")

            if obj.manualEndFrame:
                row = layout.row()
                row.prop(obj, "endFrame")
                row.operator("animate.set_end_frame", text="Use Current Frame", icon="PREVIEW_RANGE")


class TEXT_PT_Typewriter(Panel):
    '''
    Typewriter Effect Panel
    '''
    bl_label = "Typewriter Effect"
    bl_idname = "TEXT_PT_Typewriter"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'FONT'

    def draw_header(self, context):
        text = context.active_object.data
        layout = self.layout
        layout.prop(text, 'use_animated_text', text="")

    def draw(self, context):
        text = context.active_object.data
        layout = self.layout
        layout.prop(text, 'character_count')
        layout.prop(text, 'source_text')


class OBJECT_OT_SetTextButton(Operator):
    bl_idname = "animate.set_text"
    bl_label = "Use Current Text"
    bl_description = "Set the Text to be typed to the current Text of the Text object"

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.type == 'FONT'

    def execute(self, context):
        context.active_object.defaultTextBody = context.active_object.data.body
        return{'FINISHED'}


class OBJECT_OT_SetStartFrameButton(Operator):
    bl_idname = "animate.set_start_frame"
    bl_label = "Use Current Frame"
    bl_description = "Set Start Frame to same value as Current Animation Frame"

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.type == 'FONT'

    def execute(self, context):
        context.active_object.startFrame = bpy.context.scene.frame_current

        return{'FINISHED'}


class OBJECT_OT_SetEndFrameButton(Operator):
    bl_idname = "animate.set_end_frame"
    bl_label = "Use Current Frame"
    bl_description = "Set End Frame to same value as Current Animation Frame"

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.type == 'FONT'

    def execute(self, context):
        context.active_object.endFrame = bpy.context.scene.frame_current

        return{'FINISHED'}


classes = (
    TextCounter_Props,
    TextCounterPanel,
    TEXT_PT_Typewriter,
    TEXT_PT_Textscrambler,
    makeTextAnimatedPanel,
    OBJECT_OT_SetTextButton,
    OBJECT_OT_SetStartFrameButton,
    OBJECT_OT_SetEndFrameButton,
    )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TextCurve.text_counter_props = PointerProperty(type=TextCounter_Props)

    bpy.types.TextCurve.scrambler_progress = IntProperty(
            name="Scrambler progress",
            update=update_func,
            min=0, max=100,
            options={'ANIMATABLE'}
            )
    bpy.types.TextCurve.use_text_scrambler = BoolProperty(
            name="Use Text Scrambler",
            default=False
            )
    bpy.types.TextCurve.source_text = StringProperty(
            name="Source Text"
            )
    bpy.types.TextCurve.characters = StringProperty(
            name="Characters",
            default="ABCDEFGHJKLMNOPQRSTUVWXYZabcdefghjklmnopqrstuvwxyz"
            )
    bpy.types.TextCurve.character_count = IntProperty(
            name="Character count",
            update=update_func1,
            min=0,
            options={'ANIMATABLE'}
            )
    bpy.types.TextCurve.backup_text = StringProperty(
            name="Backup text"
            )
    bpy.types.TextCurve.use_animated_text = BoolProperty(
            name="Use animated text",
            default=False
            )
    bpy.types.TextCurve.source_text = StringProperty(
            name="Source Text"
            )
    bpy.types.Object.defaultTextBody = StringProperty(
            name="Text to Type",
            description="The text string you wish to be animated",
            options={'HIDDEN'}
            )
    bpy.types.Object.startFrame = IntProperty(
            name="Start Frame",
            description="The frame to start the typing animation on"
            )
    bpy.types.Object.endFrame = IntProperty(
            name="End Frame",
            description="The frame to stop the typing animation on"
            )
    bpy.types.Object.typeSpeed = IntProperty(
            name="Typing Speed",
            description="The speed in frames. E.G. 2 = every 2 frames",
            default=2
            )
    bpy.types.Object.runAnimation = BoolProperty(
            name="Animate Text?",
            description="Run this during animation?",
            default=False
            )
    bpy.types.Object.manualEndFrame = BoolProperty(
            name="Set different End Frame?",
            description="If this is set and the value is less then calculated frame\n"
                        " the remaining text will suddenly appear",
            default=False
            )

    bpy.app.handlers.frame_change_post.append(textcounter_text_update_frame)
    bpy.app.handlers.frame_change_pre.append(textscrambler_update_frame)
    bpy.app.handlers.frame_change_pre.append(animate_text)
    bpy.app.handlers.frame_change_post.append(typewriter_text_update_frame)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    bpy.app.handlers.frame_change_pre.remove(animate_text)
    bpy.app.handlers.frame_change_post.remove(textcounter_text_update_frame)
    bpy.app.handlers.frame_change_pre.remove(textscrambler_update_frame)
    bpy.app.handlers.frame_change_post.remove(typewriter_text_update_frame)

    del bpy.types.TextCurve.text_counter_props
    del bpy.types.TextCurve.scrambler_progress
    del bpy.types.TextCurve.use_text_scrambler
    del bpy.types.TextCurve.source_text
    del bpy.types.TextCurve.characters
    del bpy.types.TextCurve.character_count
    del bpy.types.TextCurve.backup_text
    del bpy.types.TextCurve.use_animated_text
    del bpy.types.Object.defaultTextBody
    del bpy.types.Object.startFrame
    del bpy.types.Object.endFrame
    del bpy.types.Object.typeSpeed
    del bpy.types.Object.runAnimation
    del bpy.types.Object.manualEndFrame


if __name__ == "__main__":
    register()
