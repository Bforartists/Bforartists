# SPDX-License-Identifier: GPL-2.0-or-later

# type: ignore

from bpy.props import (
  BoolProperty,
  EnumProperty,
  FloatProperty,
  IntProperty,
  IntVectorProperty,
  PointerProperty,
)
from bpy.types import PropertyGroup, Scene
from bpy.utils import register_class, unregister_class

# yapf: disable
_MODE_KWARGS = dict(
  items=(
    ('NODES', "Nodes", "Selected nodes in the current node tree"),
    ('TREES', "Trees", "All node trees in the current .blend file")),
  name="Mode",
  default='NODES',
  options=set())
# yapf: enable


class NA_PG_Settings(PropertyGroup):
    arrange_mode: EnumProperty(**_MODE_KWARGS, description="What to arrange")

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    margin: IntVectorProperty(
      name="Spacing",
      description="Space between nodes",
      default=(50, 50),
      min=0,
      options=set(),
      subtype='XYZ',
      size=2)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    iterations: IntProperty(
      name="Iterations",
      description=
      "Number of times to reduce crossings between links (higher values give less crossings, but are slower). To resolve all unnecessary crossings, this option may need to be set very high (since it is probabilistic)",
      default=25,
      min=1,
      options=set())

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    # yapf: disable
    direction: EnumProperty(
      items = (
        ('LEFT_DOWN', "Bottom Left", ""),
        ('RIGHT_DOWN', "Bottom Right", ""),
        ('LEFT_UP', "Top Left", ""),
        ('RIGHT_UP', "Top Right", ""),
        None,
        ('BALANCED',
        "Balanced",
        "Combine four extreme layouts, evening out their directional tendencies")),
      name="Node Alignment",
      description="Direction of layout",
      default='BALANCED',
      options=set())

    socket_alignment: EnumProperty(
      items=(
        ('NONE', "None", "Only try to align the tops of nodes"),
        ('MODERATE', "Moderate", "Align sockets or node tops depending on the heights of the nodes"),
        ('FULL', "Full", "Always try to align sockets with other sockets")),
      name="Socket Alignment",
      description="Method to align sockets with other sockets",
      default='MODERATE',
      options=set())

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    add_reroutes: BoolProperty(
      name="Add Reroutes",
      description="Insert reroutes into links",
      default=True,
      options=set())
    # yapf: enable

    keep_reroutes_outside_frames: BoolProperty(
      name="Place Reroutes Outside Frames",
      description="Always attatch reroutes to the lowest common frame of the nodes they connect",
      default=False,
      options=set())

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    stack_collapsed: BoolProperty(
      name="Stack Collapsed Nodes",
      description="Stack collapsed math and vector math nodes on top of one another",
      default=False,
      options=set())

    stack_margin_y_fac: FloatProperty(
      name="Spacing Y Factor",
      description="Factor for vertical spacing between stacked nodes",
      default=0.5,
      min=0,
      max=1,
      subtype='FACTOR',
      options=set())

    optimize_sizes: BoolProperty(
      name="Optimize Sizes",
      description="Make the widths of collapsed nodes fit their display name exactly",
      default=False,
      options=set())

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    recenter_mode: EnumProperty(**_MODE_KWARGS, description="What to recenter")

    # yapf: disable
    origin: EnumProperty(
      items=(
        ('CENTER',
         "Center",
         "Move selected nodes by the difference of their average location from (0, 0)"),
        ('ACTIVE_OUTPUT',
         "Active Output",
         "Move selected nodes by the difference of the active output(s) location from (0, 0)"),
        ('ACTIVE_NODE',
         "Active Node",
         "Move selected nodes by the difference of the active node's location from (0, 0)")),
      name="Origin",
      default='CENTER',
      options=set())
    # yapf: enable


def register() -> None:
    register_class(NA_PG_Settings)
    Scene.na_settings = PointerProperty(type=NA_PG_Settings)


def unregister() -> None:
    if NA_PG_Settings.is_registered:
        unregister_class(NA_PG_Settings)
    del Scene.na_settings
