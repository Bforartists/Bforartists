# Animation and rigging tools

This contribution adds Anim Assist, Ghost Tool and BoneCraft as built-in
Bforartists tools. With default settings, all three tools are available when
Bforartists starts. You do not need a separate download or installation.

## What each tool does

### Anim Assist 12.11.1

Anim Assist supports key edits, breakdowns and changes to timing. It can also
match poses, mirror poses and bake animation.

The bottom Timeline toolbar has four stages: Block, Spline, Polish and Deliver.
Select All to show tools from all four stages.

The Anim Assist menu and sidebar provide controls for animation editors.
Controls in the Dope Sheet, Graph Editor, Drivers and NLA editors adapt to
the tasks that each editor supports. Numeric tools have sliders, popouts and
settings. You can save your preferred layouts.

### Ghost Tool 4.3.3

Ghost Tool provides editable motion markers, onion-skin previews, motion trails,
easing presets and snapshots. These tools help you compare poses and motion.

Ghost Tool controls are in the 3D Viewport header, Tool Shelf and sidebar.
You control when Ghost Tool generates previews or starts live updates.

### BoneCraft 9.2.18

BoneCraft provides tools for character rigs, joint placement and skin weights.
It also provides IK/FK controls, poses, retargeting and export tools.
BoneCraft includes starter rigs and mapping presets.

BoneCraft controls are in the Object, Armature, Pose and Weights menus,
Tool Shelf and sidebar. Each location provides controls for its related tasks.

## Settings and extra integrations

The update keeps your existing tool settings. The update enables missing tools
once when it first opens an older preferences file.
Save preferences to keep your later choices, including disabled tools.

Bforartists does not build rigs, generate previews or edit animation keys at
startup. VRM, MMD and other external integrations can require additional
software. The tools install that software only when you request it.

## Try the tools

1. Build this branch.
2. Start Bforartists with a separate test profile.
3. Test Anim Assist controls in a short Timeline.
4. Test Anim Assist controls after you resize the Timeline.
5. Test the native Undo command.
6. Test the native Redo command.
7. Generate Ghost Tool markers.
8. Generate Ghost Tool onion-skin previews.
9. Build a BoneCraft starter rig.
10. Test the rig's pose controls.

## Source and license

The [B4Artists Toolkit](https://github.com/Axleonex/B4Artists_Toolkit)
contains the source for these tools.

Published versions:

- [Anim Assist 12.11.1](https://github.com/Axleonex/B4Artists_Toolkit/releases/tag/anim-assist-v12.11.1)
- [Ghost Tool 4.3.3](https://github.com/Axleonex/B4Artists_Toolkit/releases/tag/ghost-v4.3.3)
- [BoneCraft 9.2.18](https://github.com/Axleonex/B4Artists_Toolkit/releases/tag/bonecraft-v9.2.18)

Each tool includes the Toolkit's GPL-2.0-or-later license.
Each tool keeps its existing copyright and license notices.
