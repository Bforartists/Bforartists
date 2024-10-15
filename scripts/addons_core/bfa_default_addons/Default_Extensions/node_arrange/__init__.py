# SPDX-License-Identifier: GPL-2.0-or-later

from importlib import reload

should_reload = 'operators' in locals()
from . import (
  ui,
  operators,
  properties,
)

if should_reload:
    properties = reload(properties)
    operators = reload(operators)
    ui = reload(ui)


def register() -> None:
    ui.register()
    operators.register()
    properties.register()


def unregister() -> None:
    properties.unregister()
    operators.unregister()
    ui.unregister()
