# Animation Clips in the Asset Library: Design Proposal

Draft 2, 2026-11-24. Status: proposal for discussion, nothing decided.
Part of the animation and rigging plan. See `anim-rig-01-vision-and-consolidation.md` for the vision
and `anim-rig-06-campaign-2027.md` for where this sits in the tiers.

## At a glance

> 🎞️ **Browse a clip, see it move, drag it onto a character or into the NLA.**

| | Today | Proposed |
|---|---|---|
| 🧍 Drop a clip on a character | Not possible | Drag from the shelf or the Asset Browser |
| 📚 Drop a clip in the NLA | Not possible | Becomes a strip under the cursor |
| 🧊 Clips for plain objects | No workflow | Same shelf, same drag |
| 👀 Preview | Still picture | Plays on hover, on the thumbnail or the character |
| ✅ Does it fit my rig? | No check | Fitting rigs light up while dragging |

## 1. 🎯 Goal

**Animation clips work like every other asset: browse them, see them move, drag them onto a
character or into the NLA, and they play.**

Today the asset library handles poses well and animation clips barely at all. This document proposes
making clips first-class: for characters and for plain objects, in the Asset Browser, the asset
shelf, the 3D View and the NLA.

## 2. 🔍 What exists today

Checked in the source on `Bfa5v5.3.0`.

| Area | Today |
|---|---|
| Storing a clip as an asset | Works. Any action can be marked as an asset, whatever its length |
| Pose shelf in the 3D View | Shows every action asset, but only in Pose Mode, and treats each one as a single pose: click applies it, drag blends it |
| Using a clip from the Asset Browser | One operator, "Assign Action", gives the clip to the active object. No drag and drop |
| Dropping a clip in the 3D View | **Not possible.** The 3D View accepts drops of objects, collections, materials, node groups, images and worlds. Not actions |
| Dropping a clip in the NLA | **Not possible.** The NLA accepts no drops at all. A strip is added through a menu |
| Object animation (no armature) | No shelf, no library workflow |
| Preview | A still thumbnail. No motion |
| Checking that a clip fits a rig | None. A clip made for another rig is applied silently and does nothing or the wrong thing |

So a multi-frame clip in the pose shelf looks like a pose and behaves like a pose. That is confusing,
and it is why an animation library "works for poses but not for clips".

## 3. 🖐️ What the artist does

1. Open the **Animation** asset shelf in the 3D View, in Object Mode or Pose Mode.
2. Clips and poses are shown apart, and clips carry a small badge with their length.
3. **Hover** a clip: the thumbnail plays, or the selected character previews the motion in the viewport.
4. **Drag a clip onto a character.** Rigs the clip fits light up. Rigs it does not fit are dimmed.
5. Release: the clip is on the character and plays. A small popup at the cursor offers how:
   **Replace**, **Insert at Playhead**, **Add as Layer**, **Add as NLA Strip**.
6. **Drag a clip into the NLA**: it becomes a strip on the track and frame under the cursor.
7. **Drag a clip onto a plain object**: object animation (a bounce, a spin, a wobble, a camera move) is applied the same way.
8. Save your own: select a frame range, **Create Animation Asset**, done.

A sketch of both drop targets:

```
+--------------------------------------------+
| 3D View                                    |
|        o                                   |
|       /|\    <-- rig lights up: clip fits  |
|       / \                                  |
|              +---------------------+       |
|              | Replace             |       |
|              | Insert at Playhead  |       |
|              | Add as Layer        |       |
|              | Add as NLA Strip    |       |
|              +---------------------+       |
+--------------------------------------------+
| Animation   Poses | Clips                  |
| [Idle 2s] [Walk 1s, loop] [Jump 1s] [Wave] |
+--------------------------------------------+
        |
        |  or drag into the NLA
        v
+--------------------------------------------+
| NLA                                        |
| Hero  | [ Idle ][ Walk   ][ Jump ]         |
|       |            [ Wave ]   <-- dropped  |
+--------------------------------------------+
```

### 3.1 The four levels, for clips

See the vision document, section 3.1.

| Level | For clips |
|---|---|
| 🖐️ **1. Touch** | Hover to preview on the character. Drag onto a rig, an object or an NLA track |
| 🧩 **2. Assemble** | A shelf of clips that fit your rig. Drop one and it plays. Line clips up in the NLA like building blocks |
| 🎛️ **3. Tune** | Replace, insert, layer or strip. Loop, trim and blend strips. Selected bones only |
| 🔬 **4. Craft** | A dropped clip is an ordinary action. Edit its keys, save your own back to the library |

### 3.2 Five uses

| Who | What they do | Result |
|---|---|---|
| 🎮 **A game developer** | Drags Idle, Walk and Jump onto a kit biped, one after another into the NLA | A playable set of motions in a minute |
| 🔤 **A motion designer** | Drags "Bounce" onto a logo, then "Wobble" as a layer | Object animation with no keys set by hand |
| 🎥 **A product artist** | Drags "Turntable" onto the camera | A presentation spin |
| 🎬 **An animator** | Drops a walk, then drops a wave as a layer on the arm only | A waving walk, ready to polish |
| 🦴 **A rigger** | Presses Test with Animation on a new rig | A walk cycle shows the bad elbow before anyone animates on it |

## 4. 🧩 Building blocks

### 4.1 Tell clips and poses apart

Both are actions. The library needs to know which is which:

- **Automatically**: an action with keys on one frame is a pose; anything longer is a clip.
- **Stored on the asset** as a tag or property when it is created, so it can be filtered without
  opening the file. Extra facts stored the same way: length, frame rate, whether it loops, what it
  was made for (see 4.3), and whether it moves the character through space or stays in place.

The shelf then shows two groups, or two tabs: **Poses** and **Clips**. The pose tools stay exactly as they are.

### 4.2 Drop targets

The main new work, and it is core work: teach two editors to accept an action being dropped.

**3D View.** Dropping on an object or armature applies the clip to it. Dropping on empty space
applies to the active object. The object under the cursor is highlighted while dragging, as it is for materials.

**NLA.** Dropping on a track creates a strip at the frame under the cursor. Dropping below the last
track creates a new track. Dropping on an object's row with no tracks creates the first one.

**Dope Sheet and Timeline.** Dropping inserts the clip's keys at the frame under the cursor into the
current action. Lower priority than the first two.

**How to apply**, chosen on release and remembered as the default:

| Mode | Result |
|---|---|
| Replace | The clip becomes the object's action |
| Insert at Playhead | The clip's keys are copied into the current action at the current frame |
| Add as Layer | The clip is added as a layer of the current action |
| Add as NLA Strip | The current action is pushed down if needed and the clip is added as a strip |

"Insert" and "Layer" make a copy, so editing the result never changes the library clip.
"Replace" and "NLA Strip" can link or copy, following the asset import setting the browser already has.

### 4.3 Compatibility

A clip only makes sense on a rig with matching bones. Three levels:

1. **Check by names.** Compare the bone names the clip animates with the target's bones. Show the
   match while dragging: full, partial, none. This is cheap and catches most mistakes. Object clips
   (location, rotation, scale) fit any object.
2. **Check by rig type.** Rigs from our rigging addon carry a rig description. A clip made on one
   bipedal rig then fits every bipedal rig from the kit, whatever its proportions. The asset stores
   the rig type it was made for.
3. **Retarget on drop.** When the clip is for a different skeleton, offer to retarget it. This
   depends on a working retargeting tool and comes last.

Blender 5 actions already record what kind of data each slot animates (object, armature and so on),
which gives a first safety check for free.

### 4.4 Preview

- **Thumbnail playback** on hover, from a short strip of frames rendered when the asset is created.
- **Live preview on the selected character** while hovering, cleared when the cursor leaves. This is
  the same mechanism as a pose preview and tells the artist more than any thumbnail.
- **Length badge** and a loop icon on the thumbnail.

### 4.5 Creating clip assets

- **Create Animation Asset** from the Dope Sheet, NLA or 3D View: uses the selected keys, the preview
  range or a chosen range.
- Options: selected bones only or the whole character, mark as looping, in place or with travel.
- The preview strip and the stored facts (4.1) are generated at this point.
- **Batch import**: turn a folder of animation files into a clip library in one step. This is how a
  starter library gets built.

### 4.6 A starter library, opt-in

Clips need content to be useful on day one.

- **Source.** The mesh2motion project publishes rigs and animations under CC0, which can be shipped
  without conditions. Quality must be inspected first; see `anim-rig-04`, part A.3.
- **Delivery.** Animation libraries are large. To keep Bforartists light, the starter library is an
  **opt-in download**, in the same way as the planned Online Essentials. A small set of object clips
  (bounce, spin, wobble, turntable) can ship built in, because they are tiny and work on anything.
- **Tied to the rigging kit.** Clips made for the kit's full rigs fit every character built with
  that rig. This is also what powers "Test with Animation" in the rig builder.

## 5. ⚙️ What is core and what is addon

| Piece | Where | Why |
|---|---|---|
| Action drop targets in the 3D View and NLA | **Core** | Addons cannot add drop targets to editors |
| Object under the cursor highlighted while dragging | Core | Same |
| Animation asset shelf for Object and Pose Mode | Addon or `bl_ui` | The shelf system supports this today |
| Click and drag actions on the shelf | Addon | Already supported, used by the Pose Library |
| Clip and pose separation, stored facts | Addon, with asset metadata | No file format change needed |
| Compatibility check by names and rig type | Addon | |
| Hover preview on the character | Addon first | Same approach as pose preview |
| Thumbnail playback | Core or addon | Needs a look at what the asset preview system allows |
| Create Animation Asset, batch import | Addon | |

The core part is small and self-contained, and it is the part that makes the feature feel native.
Without it, the fallback is drag from the *shelf* only (which an addon can handle) and no dropping
from the Asset Browser or into the NLA.

**Where it lives:** the natural home is the bundled Pose Library add-on, since it already owns action
assets and the shelf. Because that add-on comes from Blender, changes there must be marked as BFA
changes and carried through merges. The alternative is to put clips in `bfa_animation` and leave the
Pose Library untouched. The second is safer for merges; the first is tidier for users.
*Recommendation: build it in `bfa_animation`, reusing the Pose Library's operators for poses.*

## 6. 🔗 Fit with the rest of the plan

- **Rigging kit:** "Test with Animation" drops a stock clip on a freshly built rig.
- **Puppetry:** a recorded take can be saved straight to the library as a clip.
- **Tweening and layers:** dropped clips can be layered and blended with native layered actions.
- **Coworker:** optional. It could find a clip by description ("a tired walk") or fetch libraries,
  but nothing here needs it.
- **File compatibility:** a dropped clip is an ordinary action. Files open in Blender unchanged.

## 7. ⚠️ Risks and open points

- **Core changes must survive merges.** Blender may add action drop support itself. Keep the change
  small and in the same style as the existing drop targets so it is easy to replace.
- **Layered actions are new.** "Add as Layer" depends on how complete Blender's layering is at the
  time. Needs checking against the current build before it is promised.
- **Linked or copied.** Linked clips save space but cannot be edited. The default needs a decision.
  *Recommendation: copy by default, as artists expect to tweak.*
- **Travel.** Clips that move the character through space need a rule for where they start when
  dropped. *Recommendation: start from the character's current position.*
- **Frame rate.** A clip made at another frame rate must be rescaled on drop, or flagged.
- **Starter library quality and size** are unknown until the CC0 content is inspected.

## 8. 🏁 Milestones

**First: clips are usable.**

- Animation shelf in Object and Pose Mode, with poses and clips apart.
- Drag from the shelf onto a character or object, with Replace and Insert.
- Compatibility check by names.
- Create Animation Asset.
- A small built-in set of object clips.

**Second: clips feel native.**

- Core drop targets: Asset Browser to 3D View, and anything to the NLA.
- Add as NLA Strip and Add as Layer.
- Hover preview on the character, length badges.

**Third: a library.**

- Opt-in starter library download.
- Compatibility by rig type, for rigs from the rigging kit.
- Batch import. Thumbnail playback.
- Retarget on drop, once retargeting exists.
