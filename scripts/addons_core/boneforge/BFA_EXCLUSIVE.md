# BoneCraft — B4Artists Exclusive Build

This package is BoneCraft, the B4Artists-exclusive advanced version of
BoneForge. It is intended for Bforartists users; standard Blender users
should install the open Blender BoneForge package instead.

The package includes internal runtime validation so the exclusive build remains
separate from the non-exclusive open Blender build. Implementation details are
intentionally not documented here.

## Build split

| Area | Open Blender BoneForge | BoneCraft (B4Artists exclusive) |
|---|---|---|
| Host support | Standard Blender | Bforartists |
| Published in | `Axleonex/BoneForge_ALTERNATIVE_CATS_for_5.0_Blender` | `Axleonex/B4Artists_Toolkit` |
| Release zip | `BoneForge-<version>.zip` | `BoneForge-BFA-<version>.zip` (published as `BoneCraft-BFA-<version>.zip`) |
| CATS avatar cleanup | Included | Included |
| Material Atlas Combiner | Included | Included |
| Selectable materials and textures | Included | Included |
| Atlas UV0 export default | Included | Included |
| Basic auto-rig and Mixamo-style avatar helpers | Included | Included |
| Production control-rig construction | Not included | Included |
| Smart landmark / joint detection suite | Not included | Included |
| Animator control layer | Not included | Included |
| Control Picker / rig UI | Not included | Included |
| Advanced retargeting core and source maps | Not included | Included |
| Profile-driven game export | Not included | Included |
| B4Artists-exclusive release gate | Not included | Included |

## Compatibility notes

- Package name remains `boneforge`; saved preferences and scene properties carry
  over from earlier BoneCraft installs.
- `bl_info` name is "BoneCraft" (the open build is "BoneForge"), so both builds are distinguishable in the
  add-on browser. Do not install both in the same host.
