# Animation Addon: Design Proposal

Draft 3, 2026-11-24. Status: proposal for discussion, nothing decided.
Read `anim-rig-01-vision-and-consolidation.md` first: it holds the vision, the principles and the roadmap.

Working folder name: `bfa_animation`.

## At a glance

> 🎬 **Grab the character, not the controls. See the motion while you make it.**

| | |
|---|---|
| 🖐️ **Pose** | Hover a body part, it lights up. Drag it |
| 📌 **Pin** | Click a foot to plant it. Pull anything else and the body follows |
| 👻 **Ghosts** | Faded poses before and after the current frame |
| 〰️ **Paths** | The arc of a hand or foot, with points you can drag |
| ✨ **Tween** | Two key poses in, a previewed in-between out |
| 📄 **What you get** | Ordinary keyframes on the rig's normal controls |

## 1. 🎯 Goal

**Pose and animate by touching the character in the viewport, and see the motion while you do it.**

Less time in the Dope Sheet and Graph Editor. The animator grabs the character, sees where it was
and where it is going, and lets the computer handle what follows from the pose.

Covers ideas 2, 3, 4, 5 and 6 from the vision, plus motion from video and markers from the maintainer's notes.

See also `anim-rig-04-research-and-puppetry.md`: part A assesses MotionBricks and UniMate for smart
tweening, and part C develops live puppetry (mouse, webcam, phone, controllers).

**The rule that shapes everything here:** the addon is a set of tools that write ordinary keyframes
on ordinary bones. Pins, solvers, ghosts and suggestions exist only while working. The saved file
plays and renders in Blender without the addon.

## 2. 🖐️ What the artist does

1. Select the character and pick the **Puppet** tool in the Tool Shelf.
2. Hover: the part under the cursor **lights up on the mesh**. No bones or controls need to be visible.
3. **Drag** the part to pose it. Drag a hand and the arm follows. Drag the chest and the spine bends.
4. Click a foot with the **Pin** modifier: it stays put. Now drag the hips and the legs bend to keep the feet planted.
5. Turn on **Ghosts** in the Overlays popover: faded copies show the poses before and after.
6. Turn on **Paths**: the hand's arc appears. **Drag a point on the arc** to fix the motion.
7. Set a second key pose further along the timeline. Press **Tween**: the in-betweens are proposed as
   ghosts, with arcs and planted feet. Accept, or adjust a guide and try again.

A sketch of the screen while posing:

```
+--------------------------------------------------------------+
| 3D View                     Overlays: [x] Ghosts  [x] Paths  |
| [Puppet]                                                     |
|                 .  .  o          ghosts before, faded        |
|               .  . /#|\                                      |
|             .   . / #| \___o  <-- hand being dragged         |
|                    /#|        `-.                            |
|     path of hand -'  |           `o  drag this point         |
|                     / \                                      |
|                 [pin] [pin]   <-- both feet pinned           |
+--------------------------------------------------------------+
| Status bar:  Drag: pose   Click: select   Pin key: pin part  |
+--------------------------------------------------------------+
   # = the part under the cursor, highlighted on the mesh
```

### 2.1 The four levels, for animation

See the vision document, section 3.1.

| Level | In the animation addon |
|---|---|
| 🖐️ **1. Touch** | Hover, drag to pose, click to pin, drag a point on a path. Later: record a performance live |
| 🧩 **2. Assemble** | One Puppet tool that works on any rig. Ghosts and Paths as two checkboxes. One Tween button. Clips dropped from the library |
| 🎛️ **3. Tune** | Stiffness per part, timing and overlap guides, ghost range, path falloff. Change a guide and the preview updates. Accept or reject |
| 🔬 **4. Craft** | Everything ends as plain keys. The Dope Sheet, Graph Editor and every native pose tool work on them as before |

### 2.2 Four shots, start to finish

| Shot | With today's tools | With the Puppet tool | Tier |
|---|---|---|---|
| ☕ **Reach for a cup** | Select the hand control, move it. Select the chest, rotate. Fix the hips. Fix the feet that slid | Pin both feet. Pull the hand to the cup. Chest and hips follow | 3 |
| 🦘 **A jump** | Key the crouch and the landing. Add breakdowns by hand. Fix the arc in the Graph Editor | Key the crouch and the landing. Press Tween. The airborne arc and planted feet are previewed. Accept | 4 |
| 🐈 **A tail swish** | Key every tail bone, offset the keys one by one for overlap | Drag the tail base. Follow-through is suggested as ghosts. Accept, baked to keys | 4 |
| 👋 **A wave over a walk** | Find the arm curves in the walk, key around them | Drop a walk clip. Drop a wave clip as a layer. Pull the hand higher on one frame | 2 and 3 |

## 3. 👆 Posing on the mesh (idea 2)

### 3.1 How it works

1. Cast a ray from the cursor onto the character's mesh.
2. Find which rig part owns that spot. With a rig from our rigging addon this is stored in the rig
   description. Otherwise it is worked out from the skin weights: the bone with the most influence
   there, then the control that moves that bone.
3. Draw that part's area of the mesh as a highlight.
4. On drag, move the control: rotate for FK parts, translate for IK parts, or hand over to the full
   body solver when pins are active (section 4).
5. On release, key it if auto-keying is on. One undo step per drag.

### 3.2 Gestures

| Gesture | Result |
|---|---|
| Hover | Highlight the part |
| Click | Select its control, so every native tool still works on it |
| Drag | Pose the part |
| Drag with a modifier | Switch between rotate and move, or twist |
| Click with the Pin modifier | Pin or unpin the part |
| Double-click | Select the whole limb |

Each gesture is also a visible option of the tool, shown in the tool settings and the status bar.
Controls can be hidden while the tool is active, and shown again at any time. This is optional: the
classic way of grabbing controls keeps working.

### 3.3 Prior art

- Blender Studio experimented with mesh-based character interaction, and an older Blender design
  ("Mesh Gizmos / Face Maps") was shelved as unstable.
- A commercial add-on (Surface Poser) offers click-on-mesh posing for Blender today.

So the workflow is proven and wanted, and not part of Blender. It is a good place for Bforartists to lead.

### 3.4 Open points

- **Highlight cost.** Drawing a deforming mesh area every frame from an addon needs careful caching.
  This is the first thing to prototype. If it is too slow on heavy characters, the highlight moves
  into the core overlay code.
- **Mapping quality on foreign rigs.** The weight-based guess will sometimes pick a helper bone.
  The artist needs a simple way to correct it once and have it remembered on the rig.
- **Faces.** Small parts close together need a smaller pick radius and probably a zoom-dependent rule.

## 4. 📌 Full body IK with pins (idea 3)

### 4.1 What it is

Any part can be pinned in place, and any part can be dragged. The whole skeleton rearranges itself to
satisfy both: pull a hand and the shoulder, spine and hips follow, while pinned feet stay planted.
"Posing with two hands" in practice means: pin one, drag the other, or pin several and drag the body.

### 4.2 The key design choice: a tool, not a constraint

The solver runs **only while the artist drags**. Its result is written as plain rotations and
positions on the rig's normal controls, then keyed. Pins are remembered as working state, not as
constraints that the file needs.

Why this matters:

- The file stays plain Blender data. It renders in Blender with no addon.
- It works on any rig, because nothing is added to the rig.
- A pose made with the solver is an ordinary pose: it can be edited with every native tool.

The cost: pins do not hold by themselves during playback. Keeping a foot planted across a frame
range is done by the tweening tools (section 7), which bake it into keys.

### 4.3 Options for the solver

| Option | For | Against |
|---|---|---|
| **Our own solver in the addon** (numeric, using the maths library Blender ships) | No core changes, full control over behaviour, easy to iterate | Speed on dense rigs is unproven |
| **Blender's iTaSC solver** (already built in) | Exists, supports several targets on one skeleton | Old, known for quirks, works as a constraint so it conflicts with 4.2, little upstream attention |
| **A new solver in the core** | Fastest, could be offered upstream | Most work, must be carried through merges |

**Recommendation:** start with our own solver in the addon and measure. A humanoid has around sixty
bones that matter for posing, which should be workable. Move the inner loop into the core only if
measurements say so. Do not build on iTaSC.

### 4.4 Behaviour that makes or breaks it

- Joint limits and preferred bend directions, read from the rig or the rig description.
- Stiffness per part, so the spine does not do all the work.
- A sense of balance: the hips follow when reaching far (ties into section 6).
- Stability: small mouse moves must give small changes, with no flipping.

Anim Assist's matching tools (IK/FK, world, parent and target matching, switch compensation) solve
the neighbouring problem of keeping a pose when control modes change. They belong here and are the
part of Anim Assist most worth reworking.

## 5. 👻 Onion skin and motion paths (idea 4)

### 5.1 What Ghost Tool got right, and wrong

Right: the features and the feel. Mesh ghosts before and after the current frame, live paths with
key dots and spacing, and dragging a point on the path to change the animation.

Wrong: how ghosts are made. Ghost Tool moves the playhead to each ghost frame, copies the mesh into a
real object with its own material, and puts it in the scene. That is slow, wipes unkeyed poses, and
leaves objects in the file.

### 5.2 The right way: two parts

**Part A, getting the shapes without moving the playhead.**

Native motion paths already solve this: Bforartists builds a small private copy of the scene's
evaluation, containing only what the path needs, and steps *that* through time. The same approach
can capture the deformed mesh at each ghost frame. This needs core work, because addons cannot create
such a private evaluation.

Until that exists, an addon-only fallback:

- **Capture as you go.** Whenever the playhead visits a frame (playing or scrubbing), store the
  deformed shape. Ghosts fill in as the animator works, with no extra cost and no risk to the pose.
- **Refresh on demand.** A button plays through the range once to fill the gaps, clearly as an
  action the artist asked for.
- Stored shapes are thrown away when the animation or the mesh changes.

**Part B, drawing.**

Ghosts are **drawn**, never created as objects. Stored shapes are sent to the graphics card once and
drawn each frame with a tint and fade. Nothing is added to the scene, so nothing can leak into a
save, a render or an export.

### 5.3 Both graphics backends

Drawing through Bforartists' own drawing layer works on OpenGL, Vulkan and Metal, with two rules the
submitted code does not fully follow:

- Thick lines must use the dedicated line shaders, since plain line width is ignored on Vulkan and Metal.
- No features that exist on only one backend.

Every drawing feature gets tested on OpenGL and Vulkan before merge.

### 5.4 Editable paths

Kept from Ghost Tool, as the best gesture feature already written: drag a point on the path and the
curves follow, drag key handles on the path, falloff to neighbouring frames. It needs:

- no default hotkeys that shadow native ones;
- display toggles kept off the undo stack;
- world positions along the path taken from the same private evaluation as Part A, not by moving the playhead.

### 5.5 Where the controls go

- **Overlays popover**: Ghosts on/off, frames before and after, style. Paths on/off.
- **Sidebar tab**: the detailed options.
- Nothing added to the tool header, Timeline header or Graph Editor header.

## 6. 🔮 Motion prediction and suggestions (idea 5)

From the maintainer's notes: physics-based motion for tweening, follow-through and plotting between
key poses, in the spirit of Cascadeur. That is the reference for this section and the next.

Always shown as a ghost or a dotted path, applied only on a click.

Three levels, cheapest first:

1. **Physics you can calculate.** For a jump or a thrown object: the arc gravity dictates, drawn as a
   suggested path through the airborne frames. Centre of mass and a balance indicator while posing.
   Ghost Tool's "Physics Feel" (gravity arc, pendulum, bounce, settle) is a seed for this.
2. **Follow-through.** For tails, hair, ears and loose limbs: suggested overlap and settle, generated
   from the motion of the parent. BoneCraft's chain dynamics is related. The result is baked to keys.
3. **Suggested poses.** From the character's own animation and the pose library: "poses like this
   one", offered as ghosts to snap to. Learned prediction of the next pose belongs with section 7.3.

Level 1 and 2 are ordinary maths and can be reliable. Level 3 is open-ended and should start as an experiment.

## 7. ✨ Smart tweening (idea 6)

The promise: set the key poses, give a few guides, and get in-betweens worth keeping.

### 7.1 What a plain in-between gets wrong

Blender interpolates each control's values separately. So hands cut straight through arcs, planted
feet slide, and everything arrives at once.

The same two key poses, A and B:

```
Plain in-between                     Smart tween

hand:  A o-----------------o B       hand:  A o               o B
         straight line                         `-.         .-'
                                                  `-..o..-'      follows an arc

foot:  slides between the poses      foot:  stays planted

all parts arrive on the same frame   hips first, then chest, then hand
```

### 7.2 Rule-based tweening (build this)

No learning involved, fully predictable, and it fixes those three problems:

- **Arcs.** In-betweens are calculated for where the hand *is in space*, along a curved path, and the
  full body solver (section 4) works out the pose for each frame.
- **Contacts.** A part pinned in both key poses stays planted in between.
- **Timing guides.** The artist sets spacing per part: ease, favour one pose, hold, overshoot.
- **Overlap.** Parts down the chain arrive a little later, by a chosen amount.
- **Path guides.** Draw or drag the arc you want (section 5.4) and the tween follows it.

The result is shown as ghosts first, then written as keys: either on every frame, or as a few
breakdown keys the artist chooses. Native breakdown and blend tools stay as they are for quick fixes.

This depends on the full body solver, so it follows it in the roadmap.

### 7.3 Learned tweening (research only for now)

Tools like Cascadeur now generate motion between key poses with a trained model, with style choices
such as walk or run. It is impressive and it is where the field is heading. Before Bforartists
commits, four questions need answers:

1. **Data.** The model is only as good as the motion it learned from. Cascadeur trained on its own
   studio's motion capture. We would need data we have the right to use and to redistribute a model from.
2. **Licence.** The model file and the runtime that executes it must be compatible with a GPL application.
3. **Size and delivery.** Models are large. This would be a separate, opt-in download, never part of
   the standard install.
4. **Skeletons.** Models are trained on one skeleton layout. Arbitrary rigs, creatures and machines
   need mapping, and may not work at all.

**Recommendation:** design the tween tool so that the rule-based engine is one "source of
in-betweens" and a learned engine could be added as another later, without changing the interface.
Build only the first now.

The strongest current candidate for that later engine is NVIDIA's MotionBricks, whose Inbetweener
generates motion through poses you place. Its code is Apache 2.0, but it is humanoid only, built on
NVIDIA's runtime, and its model terms are still to be read. See `anim-rig-04`, part A.6.

## 8. 🎥 Motion from video and markers

From the maintainer's notes: a quick and easy way to drive bones from motion markers, for a face, a
full body, a hand or a single marker, taken from a webcam, a video in the Sequencer, or the Movie Clip Editor.

### 8.1 What exists

The Movie Clip Editor already tracks markers in footage, and a bone can follow a track through a
constraint. What is missing is the setup: today it is many manual steps per marker.

### 8.2 Three levels

1. **Marker to bone, quick setup.** Select tracked markers and a bone (or a face, hand or body
   part), press one button. The tool creates the connection, scales the motion to the character, and
   offers **Bake to Keys** so the file ends up with plain keyframes and no dependency on the footage.
   This is buildable now with native tracking and is the first step.
2. **Marker sets.** Presets that know which marker goes to which bone for a face, a hand or a body,
   matched to the parts from the rigging addon. Place or track the markers in the named spots and the
   whole set connects at once.
3. **Markerless capture from webcam or video.** The computer finds the face, hands or body in the
   picture by itself. This needs a trained pose-detection model, so it carries the same four
   questions as learned tweening (section 7.3): data, licence, download size and delivery. Live webcam
   input also needs a way to read the camera, which Bforartists does not have built in.
   Research only for now.

Capture from one camera gives motion on a flat picture, not in depth. Levels 1 and 2 should be
presented honestly as best for faces, hands seen from the front, and reference-driven motion, with
the full body solver (section 4) used to turn flat targets into a believable pose.

## 9. 🧰 Other tools that belong here

- **Live recording** (puppetry): press record, drag a part while the timeline plays, and the
  performance is written as keys. Takes can be layered. Starts with the mouse, with webcam, phone and
  controller input as later opt-in extensions. See `anim-rig-04`, part C.
- **Mirror pairs** (from Anim Assist): mirror a pose, swap sides, match the opposite side. Pair
  information comes from the rig description.
- **Work in a temporary space, bake back** (from Anim Assist's proxy bake): animate a hand relative
  to a prop or the world for a range, then bake to plain keys on the normal controls.
- **Retargeting** (from BoneCraft): later, and only after it is fixed for Blender 5.

## 10. 🖥️ Interface

- **Tool Shelf**: one "Puppet" tool for posing, pinning and path editing, with its options in the tool settings.
- **Overlays popover**: Ghosts and Paths.
- **One sidebar tab**: pins, tween guides, detailed display options.
- **Menu entries** in the Pose menu for every action, with icons.
- Icons on every operator, plain panel titles, left-aligned checkboxes, strings in `locale/po`.
- No custom-drawn toolbars, no additions to native headers, no new default hotkeys that replace native ones.

## 11. ♻️ What to reuse

| Piece | From | Use | Condition |
|---|---|---|---|
| Editable motion paths, marker and handle drag | Ghost Tool | Section 5.4 | Reworked as in the Ghost Tool review |
| Path drawing | Ghost Tool | Section 5 | Line shaders fixed for Vulkan and Metal |
| Onion skin options and UI ideas | Ghost Tool | Section 5 | Ghost generation and storage replaced |
| Physics Feel | Ghost Tool | Section 6, level 1 | Later phase |
| Matching (IK/FK, world, parent, target) | Anim Assist | Section 4 | Extracted from the larger addon |
| Mirror-pair detection and tools | Anim Assist | Section 9 | Same |
| Proxy bake sessions | Anim Assist | Section 9 | Same, simplified |
| Chain dynamics | BoneCraft | Section 6, level 2 | Baked to keys, no live handler in the file |
| Everything else | | Not used | See the reviews |

## 12. ⚠️ Risks

- **Speed.** The mesh highlight, the solver and the ghosts all run while the artist drags. Each must
  be measured on a production-weight character before it is built out.
- **Solver quality.** A full body solver that flips or drifts is worse than none. This is the hardest
  single piece in the whole plan.
- **Core work.** Proper onion skin needs a core change, which must be kept small and carried through
  the weekly merges.
- **Blender catching up.** If Blender ships its own onion skin or full body IK, ours must give way
  or adapt. Keeping file results plain makes that painless for users.
- **Expectations for tweening.** "Smart" promises a lot. The rule-based version should be presented
  for what it is: better arcs, planted feet and overlap, not automatic acting.

## 13. 🏁 First milestone

The smallest thing worth shipping (Phase 1 in the roadmap):

- Onion skin drawn in the viewport, filled by capture as you go and refresh on demand.
- Live motion paths, with editable points and handles.
- Controls in the Overlays popover and one sidebar tab.
- Tested on OpenGL and Vulkan, on a heavy character.
- Nothing written to the file except keyframes.

Posing on the mesh and pins follow in Phase 2.
