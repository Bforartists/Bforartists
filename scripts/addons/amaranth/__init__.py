# SPDX-License-Identifier: GPL-2.0-or-later
"""
Amaranth

Using Blender every day, you get to change little things on it to speedup
your workflow. The problem is when you have to switch computers with
somebody else's Blender, it sucks.
That's the main reason behind Amaranth. I ported all sort of little changes
I find useful into this addon.

What is it about? Anything, whatever I think it can speedup workflow,
I'll try to add it. Enjoy <3
"""

import sys

# import amaranth's modules

# NOTE: avoid local imports whenever possible!
# Thanks to Christopher Crouzet for let me know about this.
# http://stackoverflow.com/questions/13392038/python-making-a-class-variable-static-even-when-a-module-is-imported-in-differe

from amaranth import prefs

from amaranth.modeling import symmetry_tools

from amaranth.scene import (
    refresh,
    save_reload,
    current_blend,
    stats,
    goto_library,
    debug,
    material_remove_unassigned,
    )

from amaranth.node_editor import (
    id_panel,
    display_image,
    templates,
    simplify_nodes,
    node_stats,
    normal_node,
    )

from amaranth.render import (
    border_camera,
    meshlight_add,
    meshlight_select,
    passepartout,
    final_resolution,
    samples_scene,
    render_output_z,
    )

from amaranth.animation import (
    time_extra_info,
    frame_current,
    motion_paths,
    jump_frames,
    )

from amaranth.misc import (
    color_management,
    dupli_group_id,
    toggle_wire,
    sequencer_extra_info,
    )


# register the addon + modules found in globals()
bl_info = {
    "name": "Amaranth Toolset",
    "author": "Pablo Vazquez, Bassam Kurdali, Sergey Sharybin, Lukas Tönne, Cesar Saez, CansecoGPC",
    "version": (1, 0, 20),
    "blender": (3, 2, 0),
    "location": "Everywhere!",
    "description": "A collection of tools and settings to improve productivity",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/interface/amaranth.html",
    "category": "Interface",
}


def _call_globals(attr_name):
    for m in globals().values():
        if hasattr(m, attr_name):
            getattr(m, attr_name)()


def register():
    _call_globals("register")


def unregister():
    _call_globals("unregister")
