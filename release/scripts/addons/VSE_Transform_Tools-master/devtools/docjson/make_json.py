import os
import json

from .get_operator_tag import get_operator_tag
from .get_operator_docstring import get_operator_docstring

def make_shortcuts(idname):
    shortcuts = {
        "vse_transform_tools.select": {
            "0": "keys=RIGHTMOUSE; function=Select Visible Strip",
            "1": "keys=SHIFT; function=Enable Multi Selection",
            "2": "keys=A; function=Toggle Selection",
        },
        "vse_transform_tools.add_transform": {
            "0": "keys=T"
        },
        "vse_transform_tools.grab": {
            "0": "keys=G; function=Begin Moving, Add Transform if Needed",
            "1": "keys=SHIFT; function=Hold to Enable Fine Tuning",
            "2": "keys=CTRL; function=Hold to Enable Snapping",
            "3": "keys=RIGHTMOUSE; function=Escape Grab Mode",
            "4": "keys=ESC; function=Escape Grab Mode",
            "5": "keys=LEFTMOUSE; function=Set Position, End Grab Mode",
            "6": "keys=RET; function=Set Position, End Grab Mode",
            "7": "keys=ZERO ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE PERIOD; function=Set Position by Value Entered",
            "8": "keys=X Y; function=Constrain Grabbing to Respective Axis",
            "9": "keys=MIDDLEMOUSE; function=Constrain Grabbing to Axis",
            "10": "keys=ALT G; function=Set Position to [0, 0]",
        },
        "vse_transform_tools.scale": {
            "0": "keys=S; function=Begin Scaling, Add Transform if Needed",
            "1": "keys=SHIFT; function=Enable Fine Tuning",
            "2": "keys=CTRL; function=Enable Snap scaling",
            "3": "keys=RIGHTMOUSE; function=Escape Scale Mode",
            "4": "keys=ESC; function=Escape Scale Mode",
            "5": "keys=LEFTMOUSE; function=Set Scale, End Scale Mode",
            "6": "keys=RET; function=Set Scale, End Scale Mode",
            "7": "keys=ZERO ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE PERIOD; function=Set Scale by Value Entered",
            "8": "keys=X Y; function=Constrain Scaling to Respective Axis",
            "9": "keys=MIDDLEMOUSE; function=Constrain Scaling to Axis",
            "10": "keys=ALT S; function=Unscale",
        },
        "vse_transform_tools.rotate": {
            "0": "keys=R; function=Begin Rotating, Add Transform if Needed",
            "1": "keys=SHIFT; function=Hold to Enable Fine Tuning",
            "2": "keys=CTRL; function=Hold to Enable Stepwise Rotation",
            "3": "keys=RIGHTMOUSE; function=Escape Rotate Mode",
            "4": "keys=ESC; function=Escape Rotate Mode",
            "5": "keys=LEFTMOUSE; function=Set Rotation, End Rotate Mode",
            "6": "keys=RET; function=Set Rotation, End Rotate Mode",
            "7": "keys=ZERO ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE PERIOD; function=Set Rotation to Value Entered",
            "8": "keys=ALT R; function=Set Rotation to 0 Degrees",
        },
        "vse_transform_tools.adjust_alpha": {
            "0": "keys=Q; function=Begin Alpha Adjusting",
            "1": "keys=CTRL; function=Round to Nearest Tenth",
            "2": "keys=RIGHTMOUSE; function=Escape Alpha Adjust Mode",
            "4": "keys=ESC; function=Escape Alpha Adjust Mode",
            "5": "keys=LEFTMOUSE; function=Set Alpha, End Alpha Adjust Mode",
            "6": "keys=RET; function=Set Alpha, End Alpha Adjust Mode",
            "7": "keys=ZERO ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE PERIOD; function=Set Alpha to Value Entered",
            "8": "keys=ALT Q; function=Set Alpha to 1.0",
        },
        "vse_transform_tools.crop": {
            "0": "keys=C; function=Begin/Set Cropping, Add Transform if Needed",
            "1": "keys=ESC; function=Escape Crop Mode",
            "2": "keys=LEFTMOUSE; function=Click Handles to Drag",
            "3": "keys=RET; function=Set Crop, End Grab Mode",
            "4": "keys=ALT C; function=Uncrop",
        },
        "vse_transform_tools.autocrop": {
            "0": "keys=SHIFT C"
        },
        "vse_transform_tools.call_menu": {
            "0": "keys=I"
        },
        "vse_transform_tools.increment_pivot": {
            "0": "keys=PERIOD"
        },
        "vse_transform_tools.decrement_pivot": {
            "0": "keys=COMMA"
        },
        "vse_transform_tools.duplicate": {
            "0": "keys=SHIFT D"
        },
        "vse_transform_tools.delete": {
            "0": "keys=DEL"
        },
        "vse_transform_tools.meta_toggle": {
            "0": "keys=TAB"
        },
        "vse_transform_tools.set_cursor2d": {
            "0": "keys=LEFTMOUSE; function=Cursor 2D to mouse position",
            "1": "keys=CTRL LEFTMOUSE; function=Snap Cursor 2D to nearest strip corner or mid-point"
        },
        "vse_transform_tools.pixelate": {
            "0": "keys=P"
        },
        "vse_transform_tools.track_transform": {
            "0": "keys=",
        },
    }

    return shortcuts[idname]


def make_json(ops_path, output_path=None):
    """
    Make a JSON out of all the data we gather about the operators
    """

    info = {}

    for file in sorted(os.listdir(ops_path)):
        if not file.startswith('_') and not file == 'utils':
            filepath = os.path.join(ops_path, file, file + '.py')

            idname = get_operator_tag(filepath, "bl_idname")
            label = get_operator_tag(filepath, "bl_label")
            description = get_operator_tag(filepath, "bl_description")
            docstring = get_operator_docstring(filepath)
            shortcuts = make_shortcuts(idname)

            info[idname] = {}
            info[idname]["label"] = label
            info[idname]["description"] = description
            info[idname]["docstring"] = docstring
            info[idname]["shortcuts"] = shortcuts

    if output_path:
        text = json.dumps(info, indent=4, sort_keys=True)
        with open(output_path, 'w') as f:
            f.write(text)

    return info
