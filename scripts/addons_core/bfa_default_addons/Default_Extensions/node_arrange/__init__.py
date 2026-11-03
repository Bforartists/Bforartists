# SPDX-License-Identifier: GPL-2.0-or-later

from . import keymaps, operators, properties, ui


def register() -> None:
    properties.register()
    operators.register()
    keymaps.register()
    ui.register()


def unregister() -> None:
    ui.unregister()
    keymaps.unregister()
    operators.unregister()
    properties.unregister()
