# SPDX-License-Identifier: GPL-3.0-or-later


"""
Addon preferences management.
"""

import bpy

from bfa_3Dsequencer.utils import register_classes, unregister_classes


class SPASequencerAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    shot_template_prefix: bpy.props.StringProperty(
        name="Shot Template Prefix",
        description="Scene name prefix that identifies Scene Templates",
        default="TEMPLATE_SHOT",
    )

    def draw(self, context):
        self.layout.prop(self, "shot_template_prefix")


def get_addon_prefs() -> SPASequencerAddonPreferences:
    """Get the Addon Preferences instance."""
    return bpy.context.preferences.addons[__package__].preferences


classes = (SPASequencerAddonPreferences,)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
