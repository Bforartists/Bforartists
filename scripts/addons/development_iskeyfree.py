# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# PEP8 compliant (https://www.python.org/dev/peps/pep-0008)

bl_info = {
    "name": "Is key Free",
    "author": "Antonio Vazquez (antonioya)",
    "version": (1, 1, 2),
    "blender": (2, 80, 0),
    "location": "Text Editor > Sidebar > Dev Tab",
    "description": "Find free shortcuts, inform about used and print a key list",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/development/is_key_free.html",
    "category": "Development",
}

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    StringProperty,
    PointerProperty,
)
from bpy.types import (
    Operator,
    Panel,
    PropertyGroup,
)


# ------------------------------------------------------
# Class to find keymaps
# ------------------------------------------------------

class MyChecker():
    lastfind = None
    lastkey = None
    mylist = []

    # Init
    def __init__(self):
        self.var = 5

    # Verify if the key is used
    @classmethod
    def check(cls, findkey, ctrl, alt, shift, oskey):
        if len(findkey) > 0:
            cmd = ""
            if ctrl :
                cmd += "Ctrl+"
            if alt :
                cmd += "Alt+"
            if shift :
                cmd += "Shift+"
            if oskey :
                cmd += "OsKey+"
            cls.lastfind = cmd + findkey.upper()
            cls.lastkey = findkey.upper()
        else:
            cls.lastfind = None
            cls.lastkey = None

        wm = bpy.context.window_manager
        mykeys = []

        for context, keyboardmap in wm.keyconfigs.user.keymaps.items():
            for myitem in keyboardmap.keymap_items:
                if myitem.active and myitem.type == findkey:
                    if ctrl and not myitem.ctrl:
                        continue
                    if alt and not myitem.alt:
                        continue
                    if shift and not myitem.shift:
                        continue
                    if oskey and not myitem.oskey:
                        continue
                    t = (context,
                         myitem.type,
                         "Ctrl" if myitem.ctrl else "",
                         "Alt" if myitem.alt else "",
                         "Shift" if myitem.shift else "",
                         "OsKey" if myitem.oskey else "",
                         myitem.name)

                    mykeys.append(t)

        sortkeys = sorted(mykeys, key=lambda key: (key[0], key[1], key[2], key[3], key[4], key[5]))

        cls.mylist.clear()
        for e in sortkeys:
            cmd = ""
            if e[2] != "":
                cmd += e[2] + "+"
            if e[3] != "":
                cmd += e[3] + "+"
            if e[4] != "":
                cmd += e[4] + "+"
            if e[5] != "":
                cmd += e[5] + "+"

            cmd += e[1]

            if e[6] != "":
                cmd += "  " + e[6]
            cls.mylist.append([e[0], cmd])

    # return context
    @classmethod
    def getcontext(cls):
        return str(bpy.context.screen.name)

    # return last search
    @classmethod
    def getlast(cls):
        return cls.lastfind

    # return last key
    @classmethod
    def getlastkey(cls):
        return cls.lastkey

    # return result of last search
    @classmethod
    def getlist(cls):
        return cls.mylist

    # verify if key is valid
    @classmethod
    def isvalidkey(cls, txt):
        allkeys = [
            "LEFTMOUSE", "MIDDLEMOUSE", "RIGHTMOUSE", "BUTTON4MOUSE", "BUTTON5MOUSE", "BUTTON6MOUSE",
            "BUTTON7MOUSE",
            "MOUSEMOVE", "INBETWEEN_MOUSEMOVE", "TRACKPADPAN", "TRACKPADZOOM",
            "MOUSEROTATE", "WHEELUPMOUSE", "WHEELDOWNMOUSE", "WHEELINMOUSE", "WHEELOUTMOUSE",
            "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
            "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "ZERO", "ONE", "TWO",
            "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", "LEFT_CTRL", "LEFT_ALT", "LEFT_SHIFT",
            "RIGHT_ALT",
            "RIGHT_CTRL", "RIGHT_SHIFT", "OSKEY", "GRLESS", "ESC", "TAB", "RET", "SPACE", "LINE_FEED",
            "BACK_SPACE",
            "DEL", "SEMI_COLON", "PERIOD", "COMMA", "QUOTE", "ACCENT_GRAVE", "MINUS", "SLASH", "BACK_SLASH",
            "EQUAL",
            "LEFT_BRACKET", "RIGHT_BRACKET", "LEFT_ARROW", "DOWN_ARROW", "RIGHT_ARROW", "UP_ARROW", "NUMPAD_2",
            "NUMPAD_4", "NUMPAD_6", "NUMPAD_8", "NUMPAD_1", "NUMPAD_3", "NUMPAD_5", "NUMPAD_7", "NUMPAD_9",
            "NUMPAD_PERIOD", "NUMPAD_SLASH", "NUMPAD_ASTERIX", "NUMPAD_0", "NUMPAD_MINUS", "NUMPAD_ENTER",
            "NUMPAD_PLUS",
            "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "F13", "F14", "F15",
            "F16", "F17",
            "F18", "F19", "PAUSE", "INSERT", "HOME", "PAGE_UP", "PAGE_DOWN", "END", "MEDIA_PLAY", "MEDIA_STOP",
            "MEDIA_FIRST", "MEDIA_LAST", "TEXTINPUT", "WINDOW_DEACTIVATE", "TIMER", "TIMER0", "TIMER1", "TIMER2",
            "TIMER_JOBS", "TIMER_AUTOSAVE", "TIMER_REPORT", "TIMERREGION", "NDOF_MOTION", "NDOF_BUTTON_MENU",
            "NDOF_BUTTON_FIT", "NDOF_BUTTON_TOP", "NDOF_BUTTON_BOTTOM", "NDOF_BUTTON_LEFT", "NDOF_BUTTON_RIGHT",
            "NDOF_BUTTON_FRONT", "NDOF_BUTTON_BACK", "NDOF_BUTTON_ISO1", "NDOF_BUTTON_ISO2",
            "NDOF_BUTTON_ROLL_CW",
            "NDOF_BUTTON_ROLL_CCW", "NDOF_BUTTON_SPIN_CW", "NDOF_BUTTON_SPIN_CCW", "NDOF_BUTTON_TILT_CW",
            "NDOF_BUTTON_TILT_CCW", "NDOF_BUTTON_ROTATE", "NDOF_BUTTON_PANZOOM", "NDOF_BUTTON_DOMINANT",
            "NDOF_BUTTON_PLUS", "NDOF_BUTTON_MINUS", "NDOF_BUTTON_ESC", "NDOF_BUTTON_ALT", "NDOF_BUTTON_SHIFT",
            "NDOF_BUTTON_CTRL", "NDOF_BUTTON_1", "NDOF_BUTTON_2", "NDOF_BUTTON_3", "NDOF_BUTTON_4",
            "NDOF_BUTTON_5",
            "NDOF_BUTTON_6", "NDOF_BUTTON_7", "NDOF_BUTTON_8", "NDOF_BUTTON_9", "NDOF_BUTTON_10",
            "NDOF_BUTTON_A",
            "NDOF_BUTTON_B", "NDOF_BUTTON_C"
            ]
        try:
            allkeys.index(txt)
            return True
        except ValueError:
            return False


mychecker = MyChecker()  # Global class handler


# ------------------------------------------------------
# Button: Class for search button
# ------------------------------------------------------
class RunActionCheck(Operator):
    bl_idname = "iskeyfree.action_check"
    bl_label = ""
    bl_description = "Verify if the selected shortcut is free"

    # noinspection PyUnusedLocal
    def execute(self, context):
        scene = context.scene.is_keyfree
        txt = scene.data.upper()
        global mychecker
        mychecker.check(txt, scene.use_crtl, scene.use_alt, scene.use_shift,
                        scene.use_oskey)

        return {'FINISHED'}


# ------------------------------------------------------
# Defines UI panel
# ------------------------------------------------------
class UIControlPanel(Panel):
    bl_idname = "DEVISKEYFREE_PT_ui"
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = "UI"
    bl_label = "Is Key Free"
    bl_category = 'Dev'
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    def draw(self, context):
        layout = self.layout
        scene = context.scene.is_keyfree

        row = layout.row(align=True)
        row.prop(scene, "data")
        row.operator("iskeyfree.action_check", icon="VIEWZOOM")

        row = layout.row(align=True)
        row.prop(scene, "use_crtl", toggle=True)
        row.prop(scene, "use_alt", toggle=True)
        row.prop(scene, "use_shift", toggle=True)
        row.prop(scene, "use_oskey", toggle=True)

        row = layout.row()
        row.prop(scene, "numpad")

        layout.operator("iskeyfree.run_export_keys", icon="FILE_TEXT")

        global mychecker
        mylist = mychecker.getlist()
        oldcontext = None

        box = None
        if len(mylist) > 0:
            cmd = mychecker.getlast()
            if cmd is not None:
                row = layout.row()
                row.label(text="Current uses of " + str(cmd), icon="PARTICLE_DATA")
            for e in mylist:
                if oldcontext != e[0]:
                    box = layout.box()
                    box.label(text=e[0], icon="UNPINNED")
                    oldcontext = e[0]

                row = box.row(align=True)
                row.label(text=e[1])
        else:
            cmd = mychecker.getlast()
            if cmd is not None:
                box = layout.box()
                if mychecker.isvalidkey(mychecker.getlastkey()) is False:
                    box.label(text=str(mychecker.getlastkey()) + " looks not valid key", icon="ERROR")
                else:
                    box.label(text=str(cmd) + " is free", icon="FILE_TICK")


# ------------------------------------------------------
# Update key (special values) event handler
# ------------------------------------------------------
# noinspection PyUnusedLocal
def update_data(self, context):
    scene = context.scene.is_keyfree
    if scene.numpad != "NONE":
        scene.data = scene.numpad


class IskeyFreeProperties(PropertyGroup):
    data: StringProperty(
        name="Key", maxlen=32,
        description="Shortcut to verify"
    )
    use_crtl: BoolProperty(
        name="Ctrl",
        description="Ctrl key used in shortcut",
        default=False
    )
    use_alt: BoolProperty(
        name="Alt",
        description="Alt key used in shortcut",
        default=False
    )
    use_shift: BoolProperty(
        name="Shift",
        description="Shift key used in shortcut",
        default=False
    )
    use_oskey: BoolProperty(
        name="OsKey",
        description="Operating system key used in shortcut",
        default=False
    )
    numpad: EnumProperty(
        items=(
            ('NONE', "Select key", ""),
            ("LEFTMOUSE", "LEFTMOUSE", ""),
            ("MIDDLEMOUSE", "MIDDLEMOUSE", ""),
            ("RIGHTMOUSE", "RIGHTMOUSE", ""),
            ("BUTTON4MOUSE", "BUTTON4MOUSE", ""),
            ("BUTTON5MOUSE", "BUTTON5MOUSE", ""),
            ("BUTTON6MOUSE", "BUTTON6MOUSE", ""),
            ("BUTTON7MOUSE", "BUTTON7MOUSE", ""),
            ("MOUSEMOVE", "MOUSEMOVE", ""),
            ("INBETWEEN_MOUSEMOVE", "INBETWEEN_MOUSEMOVE", ""),
            ("TRACKPADPAN", "TRACKPADPAN", ""),
            ("TRACKPADZOOM", "TRACKPADZOOM", ""),
            ("MOUSEROTATE", "MOUSEROTATE", ""),
            ("WHEELUPMOUSE", "WHEELUPMOUSE", ""),
            ("WHEELDOWNMOUSE", "WHEELDOWNMOUSE", ""),
            ("WHEELINMOUSE", "WHEELINMOUSE", ""),
            ("WHEELOUTMOUSE", "WHEELOUTMOUSE", ""),
            ("A", "A", ""),
            ("B", "B", ""),
            ("C", "C", ""),
            ("D", "D", ""),
            ("E", "E", ""),
            ("F", "F", ""),
            ("G", "G", ""),
            ("H", "H", ""),
            ("I", "I", ""),
            ("J", "J", ""),
            ("K", "K", ""),
            ("L", "L", ""),
            ("M", "M", ""),
            ("N", "N", ""),
            ("O", "O", ""),
            ("P", "P", ""),
            ("Q", "Q", ""),
            ("R", "R", ""),
            ("S", "S", ""),
            ("T", "T", ""),
            ("U", "U", ""),
            ("V", "V", ""),
            ("W", "W", ""),
            ("X", "X", ""),
            ("Y", "Y", ""),
            ("Z", "Z", ""),
            ("ZERO", "ZERO", ""),
            ("ONE", "ONE", ""),
            ("TWO", "TWO", ""),
            ("THREE", "THREE", ""),
            ("FOUR", "FOUR", ""),
            ("FIVE", "FIVE", ""),
            ("SIX", "SIX", ""),
            ("SEVEN", "SEVEN", ""),
            ("EIGHT", "EIGHT", ""),
            ("NINE", "NINE", ""),
            ("LEFT_CTRL", "LEFT_CTRL", ""),
            ("LEFT_ALT", "LEFT_ALT", ""),
            ("LEFT_SHIFT", "LEFT_SHIFT", ""),
            ("RIGHT_ALT", "RIGHT_ALT", ""),
            ("RIGHT_CTRL", "RIGHT_CTRL", ""),
            ("RIGHT_SHIFT", "RIGHT_SHIFT", ""),
            ("OSKEY", "OSKEY", ""),
            ("GRLESS", "GRLESS", ""),
            ("ESC", "ESC", ""),
            ("TAB", "TAB", ""),
            ("RET", "RET", ""),
            ("SPACE", "SPACE", ""),
            ("LINE_FEED", "LINE_FEED", ""),
            ("BACK_SPACE", "BACK_SPACE", ""),
            ("DEL", "DEL", ""),
            ("SEMI_COLON", "SEMI_COLON", ""),
            ("PERIOD", "PERIOD", ""),
            ("COMMA", "COMMA", ""),
            ("QUOTE", "QUOTE", ""),
            ("ACCENT_GRAVE", "ACCENT_GRAVE", ""),
            ("MINUS", "MINUS", ""),
            ("SLASH", "SLASH", ""),
            ("BACK_SLASH", "BACK_SLASH", ""),
            ("EQUAL", "EQUAL", ""),
            ("LEFT_BRACKET", "LEFT_BRACKET", ""),
            ("RIGHT_BRACKET", "RIGHT_BRACKET", ""),
            ("LEFT_ARROW", "LEFT_ARROW", ""),
            ("DOWN_ARROW", "DOWN_ARROW", ""),
            ("RIGHT_ARROW", "RIGHT_ARROW", ""),
            ("UP_ARROW", "UP_ARROW", ""),
            ("NUMPAD_1", "NUMPAD_1", ""),
            ("NUMPAD_2", "NUMPAD_2", ""),
            ("NUMPAD_3", "NUMPAD_3", ""),
            ("NUMPAD_4", "NUMPAD_4", ""),
            ("NUMPAD_5", "NUMPAD_5", ""),
            ("NUMPAD_6", "NUMPAD_6", ""),
            ("NUMPAD_7", "NUMPAD_7", ""),
            ("NUMPAD_8", "NUMPAD_8", ""),
            ("NUMPAD_9", "NUMPAD_9", ""),
            ("NUMPAD_0", "NUMPAD_0", ""),
            ("NUMPAD_PERIOD", "NUMPAD_PERIOD", ""),
            ("NUMPAD_SLASH", "NUMPAD_SLASH", ""),
            ("NUMPAD_ASTERIX", "NUMPAD_ASTERIX", ""),
            ("NUMPAD_MINUS", "NUMPAD_MINUS", ""),
            ("NUMPAD_ENTER", "NUMPAD_ENTER", ""),
            ("NUMPAD_PLUS", "NUMPAD_PLUS", ""),
            ("F1", "F1", ""),
            ("F2", "F2", ""),
            ("F3", "F3", ""),
            ("F4", "F4", ""),
            ("F5", "F5", ""),
            ("F6", "F6", ""),
            ("F7", "F7", ""),
            ("F8", "F8", ""),
            ("F9", "F9", ""),
            ("F10", "F10", ""),
            ("F11", "F11", ""),
            ("F12", "F12", ""),
            ("F13", "F13", ""),
            ("F14", "F14", ""),
            ("F15", "F15", ""),
            ("F16", "F16", ""),
            ("F17", "F17", ""),
            ("F18", "F18", ""),
            ("F19", "F19", ""),
            ("PAUSE", "PAUSE", ""),
            ("INSERT", "INSERT", ""),
            ("HOME", "HOME", ""),
            ("PAGE_UP", "PAGE_UP", ""),
            ("PAGE_DOWN", "PAGE_DOWN", ""),
            ("END", "END", ""),
            ("MEDIA_PLAY", "MEDIA_PLAY", ""),
            ("MEDIA_STOP", "MEDIA_STOP", ""),
            ("MEDIA_FIRST", "MEDIA_FIRST", ""),
            ("MEDIA_LAST", "MEDIA_LAST", ""),
            ("TEXTINPUT", "TEXTINPUT", ""),
            ("WINDOW_DEACTIVATE", "WINDOW_DEACTIVATE", ""),
            ("TIMER", "TIMER", ""),
            ("TIMER0", "TIMER0", ""),
            ("TIMER1", "TIMER1", ""),
            ("TIMER2", "TIMER2", ""),
            ("TIMER_JOBS", "TIMER_JOBS", ""),
            ("TIMER_AUTOSAVE", "TIMER_AUTOSAVE", ""),
            ("TIMER_REPORT", "TIMER_REPORT", ""),
            ("TIMERREGION", "TIMERREGION", ""),
            ("NDOF_MOTION", "NDOF_MOTION", ""),
            ("NDOF_BUTTON_MENU", "NDOF_BUTTON_MENU", ""),
            ("NDOF_BUTTON_FIT", "NDOF_BUTTON_FIT", ""),
            ("NDOF_BUTTON_TOP", "NDOF_BUTTON_TOP", ""),
            ("NDOF_BUTTON_BOTTOM", "NDOF_BUTTON_BOTTOM", ""),
            ("NDOF_BUTTON_LEFT", "NDOF_BUTTON_LEFT", ""),
            ("NDOF_BUTTON_RIGHT", "NDOF_BUTTON_RIGHT", ""),
            ("NDOF_BUTTON_FRONT", "NDOF_BUTTON_FRONT", ""),
            ("NDOF_BUTTON_BACK", "NDOF_BUTTON_BACK", ""),
            ("NDOF_BUTTON_ISO1", "NDOF_BUTTON_ISO1", ""),
            ("NDOF_BUTTON_ISO2", "NDOF_BUTTON_ISO2", ""),
            ("NDOF_BUTTON_ROLL_CW", "NDOF_BUTTON_ROLL_CW", ""),
            ("NDOF_BUTTON_ROLL_CCW", "NDOF_BUTTON_ROLL_CCW", ""),
            ("NDOF_BUTTON_SPIN_CW", "NDOF_BUTTON_SPIN_CW", ""),
            ("NDOF_BUTTON_SPIN_CCW", "NDOF_BUTTON_SPIN_CCW", ""),
            ("NDOF_BUTTON_TILT_CW", "NDOF_BUTTON_TILT_CW", ""),
            ("NDOF_BUTTON_TILT_CCW", "NDOF_BUTTON_TILT_CCW", ""),
            ("NDOF_BUTTON_ROTATE", "NDOF_BUTTON_ROTATE", ""),
            ("NDOF_BUTTON_PANZOOM", "NDOF_BUTTON_PANZOOM", ""),
            ("NDOF_BUTTON_DOMINANT", "NDOF_BUTTON_DOMINANT", ""),
            ("NDOF_BUTTON_PLUS", "NDOF_BUTTON_PLUS", ""),
            ("NDOF_BUTTON_MINUS", "NDOF_BUTTON_MINUS", ""),
            ("NDOF_BUTTON_ESC", "NDOF_BUTTON_ESC", ""),
            ("NDOF_BUTTON_ALT", "NDOF_BUTTON_ALT", ""),
            ("NDOF_BUTTON_SHIFT", "NDOF_BUTTON_SHIFT", ""),
            ("NDOF_BUTTON_CTRL", "NDOF_BUTTON_CTRL", ""),
            ("NDOF_BUTTON_1", "NDOF_BUTTON_1", ""),
            ("NDOF_BUTTON_2", "NDOF_BUTTON_2", ""),
            ("NDOF_BUTTON_3", "NDOF_BUTTON_3", ""),
            ("NDOF_BUTTON_4", "NDOF_BUTTON_4", ""),
            ("NDOF_BUTTON_5", "NDOF_BUTTON_5", ""),
            ("NDOF_BUTTON_6", "NDOF_BUTTON_6", ""),
            ("NDOF_BUTTON_7", "NDOF_BUTTON_7", ""),
            ("NDOF_BUTTON_8", "NDOF_BUTTON_8", ""),
            ("NDOF_BUTTON_9", "NDOF_BUTTON_9", ""),
            ("NDOF_BUTTON_10", "NDOF_BUTTON_10", ""),
            ("NDOF_BUTTON_A", "NDOF_BUTTON_A", ""),
            ("NDOF_BUTTON_B", "NDOF_BUTTON_B", ""),
            ("NDOF_BUTTON_C", "NDOF_BUTTON_C", "")
        ),
        name="Quick Type",
        description="Enter key code in find text",
        update=update_data
    )


class IsKeyFreeRunExportKeys(Operator):
    bl_idname = "iskeyfree.run_export_keys"
    bl_label = "List all Shortcuts"
    bl_description = ("List all existing shortcuts in a text block\n"
                      "The newly generated list will be made active in the Text Editor\n"
                      "To access the previous ones, select them from the Header dropdown")

    def all_shortcuts_name(self, context):
        new_name, def_name, ext = "", "All_Shortcuts", ".txt"
        suffix = 1
        try:
            # first slap a simple linear count + 1 for numeric suffix, if it fails
            # harvest for the rightmost numbers and append the max value
            list_txt = []
            data_txt = bpy.data.texts
            list_txt = [txt.name for txt in data_txt if txt.name.startswith("All_Shortcuts")]
            new_name = "{}_{}{}".format(def_name, len(list_txt) + 1, ext)

            if new_name in list_txt:
                from re import findall
                test_num = [findall(r"\d+", words) for words in list_txt]
                suffix += max([int(l[-1]) for l in test_num])
                new_name = "{}_{}{}".format(def_name, suffix, ext)
            return new_name
        except:
            return None

    def execute(self, context):
        wm = bpy.context.window_manager
        from collections import defaultdict
        mykeys = defaultdict(list)
        file_name = self.all_shortcuts_name(context) or "All_Shortcut.txt"
        start_note = "# Note: Some of the shortcuts entries don't have a name. Mostly Modal stuff\n"
        col_width, col_shortcuts = 2, 2

        for ctx_type, keyboardmap in wm.keyconfigs.user.keymaps.items():
            for myitem in keyboardmap.keymap_items:
                padding = len(myitem.name)
                col_width = padding + 2 if padding > col_width else col_width

                short_type = myitem.type if myitem.type else "UNKNOWN"
                is_ctrl = " Ctrl" if myitem.ctrl else ""
                is_alt = " Alt" if myitem.alt else ""
                is_shift = " Shift" if myitem.shift else ""
                is_oskey = " OsKey" if myitem.oskey else ""
                short_cuts = "{}{}{}{}{}".format(short_type, is_ctrl, is_alt, is_shift, is_oskey)

                t = (
                    myitem.name if myitem.name else "No Name",
                    short_cuts,
                )
                mykeys[ctx_type].append(t)
                padding_s = len(short_cuts) + 2
                col_shortcuts = padding_s if padding_s > col_shortcuts else col_shortcuts

        max_line = col_shortcuts + col_width + 4
        textblock = bpy.data.texts.new(file_name)
        total = sum([len(mykeys[ctxs]) for ctxs in mykeys])
        textblock.write('# %d Total Shortcuts\n\n' % total)
        textblock.write(start_note)

        for ctx in mykeys:
            textblock.write("\n[%s]\nEntries: %s\n\n" % (ctx, len(mykeys[ctx])))
            line_k = sorted(mykeys[ctx])
            for keys in line_k:
                add_ticks = "-" * (max_line - (len(keys[0]) + len(keys[1])))
                entries = "{ticks} {entry}".format(ticks=add_ticks, entry=keys[1])
                textblock.write("{name} {entry}\n".format(name=keys[0], entry=entries))

            textblock.write("\n\n")

        # try to set the created text block to active
        if context.area.type in {"TEXT_EDITOR"}:
            bpy.context.space_data.text = bpy.data.texts[file_name]

        self.report({'INFO'}, "See %s textblock" % file_name)

        return {"FINISHED"}


# -----------------------------------------------------
# Registration
# ------------------------------------------------------
classes = (
    IskeyFreeProperties,
    RunActionCheck,
    UIControlPanel,
    IsKeyFreeRunExportKeys,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.is_keyfree = PointerProperty(type=IskeyFreeProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.is_keyfree
