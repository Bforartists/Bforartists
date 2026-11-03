# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
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


# import amaranth's modules

# NOTE: avoid local imports whenever possible!
# Thanks to Christopher Crouzet for let me know about this.
# http://stackoverflow.com/questions/13392038/python-making-a-class-variable-static-even-when-a-module-is-imported-in-differe

from . import prefs

from . import modeling
from . import scene
from . import node_editor
from . import render
from . import animation
from . import misc

def register():
    prefs.register()
    modeling.register()
    scene.register()
    node_editor.register()
    render.register()
    animation.register()
    misc.register()

def unregister():
    prefs.unregister()
    misc.unregister()
    animation.unregister()
    render.unregister()
    node_editor.unregister()
    scene.unregister()
    modeling.unregister()
