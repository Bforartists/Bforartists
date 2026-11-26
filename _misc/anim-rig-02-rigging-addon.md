# Rigging Addon: Design Proposal

Draft 3, 2026-11-24. Status: proposal for discussion, nothing decided.
Read `anim-rig-01-vision-and-consolidation.md` first: it holds the vision, the principles and the roadmap.

Working folder name: `bfa_rigging`.

See also `anim-rig-04-research-and-puppetry.md`: part A assesses the papers and open projects behind
smart placement and skinning, and part B develops the asset library and character kit idea.

Draft 2 folds in the maintainer's own rigging notes and the "Assets - Smart Rigging" sketch of
9 April 2026. Where a note was unclear it is marked **(to confirm)**.

## At a glance

> 🦴 **Pick up a part, drop it on the model, adjust, press Build.**

| | |
|---|---|
| 📦 **Where the parts are** | The asset shelf at the bottom of the 3D View |
| 🧲 **How they join** | Sockets that light up and snap while you drag |
| 🖐️ **How you adjust** | Markers and gizmos on the model |
| ▶️ **How you finish** | One button: Build Rig. Later: Rebuild |
| 📄 **What you get** | Ordinary bones, constraints and weights. Light: few or no drivers |
| 🐙 **What it can rig** | People, animals, creatures and machines, from the same parts |

## 1. 🎯 Goal

**Build a rig the way you assemble a puppet: pick up a part, drop it on the model, adjust, press a button, done.**

An artist with no rigging training should get a working character rig in minutes. A rigger should be
able to open the same rig and change anything, because the result is ordinary bones and constraints.

Covers ideas 1, 7 and 8 from the vision, plus the Edit Mode helpers and the asset lists from the notes.

### 1.1 The problem with today's auto-riggers

From the notes: current auto-riggers let you draw or place markers and then build, but:

- there is no drag and drop;
- they are not modular and are hard to adjust afterwards;
- their settings need scripts;
- the rigs they produce are heavy and slow.

### 1.2 Requirements

The sketch lists four goals: **easy to build, easy to refine, easy to extend with modules, adaptable.**
The notes turn these into requirements that every part in the library must meet.

| Requirement | What it means in practice |
|---|---|
| **Modular** | A rig is made of parts that plug into each other through sockets. New kinds of rig come from new combinations, not new code |
| **Performant** | Light and simple. Mostly bones and constraints. As few drivers as possible, ideally none. **No more than four levels of dependency deep.** No scripts needed at playback. Optional speed-ups such as a playback cache are allowed when the rig gives the same result without them (vision document, section 3.3) |
| **Flexible** | A few markers move everything that depends on them. Markers can be toggled in and out at any time. Bones can still be edited by hand afterwards |
| **Intuitive** | Clear colour coding, labels, and control shapes that look like what they do. Bone collections named and ordered the same way on every rig, in low, mid and high detail levels **(to confirm: low / mid / high as levels of control detail)** |

The sketch also names three stages of work, used below to organise the tools:
**Creation** (build a rig), **Adaptation** (fit and adjust it), **Variation** (reuse it on other characters).

### 1.3 The four levels, for rigging

See the vision document, section 3.1.

| Level | In the rigging addon |
|---|---|
| 🖐️ **1. Touch** | Drag a part onto the model. Draw a stroke along a tail. Drag a marker to move a joint. Sockets light up under the cursor |
| 🧩 **2. Assemble** | Whole rigs and parts from the shelf. Mirror with one click. Build Rig. A guide panel that names the next step |
| 🎛️ **3. Tune** | Finger count, IK or FK, detail level, limb length, as gizmos and in the asset wizard. Switch markers back on, swap a part, press Rebuild, keep the animation |
| 🔬 **4. Craft** | The built rig is plain bones and constraints. Edit them, repaint weights with the native tools, save your own parts as assets |

## 2. 🖐️ What the artist does

Following the sketch: asset shelf along the bottom, viewport in the middle, a small guide panel on the side.

1. Select the model. Open the **Rig Parts** asset shelf in the 3D View.
2. **Drag a part onto the model**: a spine, an arm, a leg, a hand, a face, a tail, a piston.
   Or **draw it**: sketch a stroke along the limb and the stroke becomes the part's guide (section 3.4).
3. The part **lands inside the mesh** and fits itself to the shape: the arm runs down the middle of
   the arm, joints sit at the elbow and wrist.
4. If dropped near an existing part, it **snaps into the nearest socket** (arm into shoulder, hand
   into wrist). The socket lights up while dragging.
5. **Markers with gizmos** let the artist nudge any joint. Moving a marker moves everything that hangs from it.
6. Parts placed on one side offer a **mirror** with one click.
7. Press **Build Rig**. Every part is attached to its nearest parent socket, recursively, and
   controls, constraints and skin weights are generated.
8. Later changes: toggle the markers back in, adjust or swap a part, press **Rebuild**. Animation made on the rig survives.

A sketch of the screen while placing an arm:

```
+------------------------------------------------------------+---------------+
| 3D View                                                    | Rig Guide     |
|                                                            |               |
|                  (o)   head socket                         | 1 Spine   ok  |
|                   |                                        | 2 Arms    ..  |
|       o----o----(O)----o----o      markers on the joints   | 3 Legs        |
|                   |      \                                 | 4 Hands       |
|                   |       shoulder socket lights up        |               |
|                   o                                        | [ Build Rig ] |
|                  / \            [Arm] ~~~> being dragged   | [ Test ]      |
|                 o   o                                      |               |
+------------------------------------------------------------+---------------+
| Rig Parts   [Biped] [Spine] [Arm] [Leg] [Foot] [Hand] [Tail] [Piston] ...  |
+----------------------------------------------------------------------------+
```

A small **guide panel** (the "wizard" box in the sketch) shows the current step and the next button
to press. It is a helper for new users, not a separate mode: every step is also available directly.

Shortcut for common cases: **whole-character rigs** (biped, quadruped, bird and so on) drop as one
piece, fit themselves, and can then be edited part by part.

### 2.1 Four rigs, built from parts

| Character | Parts used | How long it should take | Tier |
|---|---|---|---|
| 🧍 **Cartoon hero** | Biped full rig, dropped as one piece. Three-finger hands. Face preset, low detail | A few minutes | 1, face in 5 |
| 👽 **Six-legged alien** | Spine. Leg part dropped three times and mirrored. Two tentacles drawn as strokes. Tail | Ten minutes | 5 |
| 🏗️ **Excavator** | Objects to Bones for the body. Three hinges and three pistons on the arm. Each is one 0 to 1 slider | Ten minutes | 1 and 5 |
| 🦅 **Bird** | Bird full rig. Wing parts fitted by dragging the wrist and tip markers | A few minutes | 5 |

Nothing in the alien or the excavator needed a new kind of rig. They are new combinations of the
same parts, which is the point of the socket system.

## 3. 🧩 Building blocks

### 3.1 Parts

A part is a small, self-contained piece of rig with three things:

- **Markers**: a few points the artist places. This is all the artist sees before building.
- **Sockets**: named points where other parts attach, with a type ("limb root", "digit root",
  "head", "generic"). An arm has a socket at the wrist; a hand has a plug that fits it.
  On build, each part finds the nearest compatible parent socket and attaches, and its children do the same.
- **A recipe**: what gets built from the markers (control bones, IK/FK, deform bones, shapes, colours,
  collections) and what the part writes into the rig description (section 3.6).

How parts chain through sockets:

```
Spine --(shoulder)--> Arm --(wrist)--> Hand --(digit)--> Fingers
  |
  +----(hip)--------> Leg --(ankle)--> Foot
  |
  +----(head)-------> Head and Face
  |
  +----(generic)----> Tail, Wing, Tentacle, Piston ...
```

Parts are stored as assets, so they appear in the asset shelf with thumbnails and can be dragged.
Users and studios can save their own parts.

### 3.2 The rig asset library

Taken from the notes.

| Family | Assets |
|---|---|
| **Full rigs** | Bipedal, quadrupedal, bird, lizard, fish, dinosaur, insect, arachnid |
| **Human parts** | Spine. Arms with shoulder. Legs with hips. Feet. Hands: three fingers and thumb, four fingers and thumb, single finger, thumb, palm |
| **Animal parts** | Bird wings, membrane wings, tails, hind legs, fore legs, tentacle |
| **Utility parts** | Piston, two-joint, three-joint and four-joint chains, curve chain, simulated chain |
| **Face** | Jaw, eyes, eyelids, brows, lips, tongue, whole-face presets (section 4) |
| **Mocap-compatible skeletons** | Unreal Engine, Mixamo, Cascadeur, and one more from the notes **(to confirm: "Alliance?")** |

Idea 8 (machines and creatures) falls out of this structure: nothing assumes two arms and two legs.
A spider is eight leg parts on a body. An excavator is hinges and pistons. Symmetry is offered, never
required, and nothing depends on bone names.

**Mocap-compatible skeletons** are full rigs whose deform bones match a known layout and naming, so
motion capture and animation libraries for that layout can be applied with little or no retargeting.
Open point: skeleton layouts published by engine and tool vendors have their own licence terms.
Whether we may ship rigs that reproduce them needs checking before any are built.

### 3.3 Character assets

Also from the notes: simple starter meshes that pair with the full rigs, so a new user can drop a
character, drop a rig, and animate within a minute. They are also the test set for smart placement.

| Asset | Purpose |
|---|---|
| Cube, sphere | Simplest possible characters, for bouncing-ball style exercises |
| Tailed | Tail and follow-through practice |
| Bipedal, quadruped | Neutral body types |
| Heroic, feminine, masculine, heavy | Proportion variants of the biped, to test and show how one rig adapts |

These belong with the BFA asset library (`assets_bfa/`), not inside the addon.

### 3.4 Drag, drop, draw and sockets

Bforartists already has the pieces for the gestures:

- The **asset shelf** supports a click action and a drag action per shelf. The bundled Pose Library
  uses exactly this (click to apply, drag to blend), so the pattern is proven in the repo.
- **Gizmos** can be written by an addon. Several bundled add-ons already do it.

**Drop.** In plain steps:

1. While dragging, cast a ray from the cursor into the model.
2. Look for a compatible socket near the cursor. If one is close, snap to it and highlight it.
3. Otherwise place the part's root at the centre of the mesh under the cursor (section 3.5).
4. Show a preview of the markers while the mouse is still held. Release to place, Esc to cancel.

**Draw.** From the sketch ("you draw the gizmo"): with a part chosen, the artist draws one stroke
along the limb. The stroke is pushed to the centre of the mesh, split at the bends, and becomes the
part's markers. This is the fastest route for tails, tentacles, spines and odd creature limbs, where
a preset shape is rarely right.

**How the markers are made, two ideas from the sketch to try:**

- *Grease Pencil as the gizmo.* The drawn stroke itself stays as the editable guide.
- *Geometry Nodes to generate the gizmo systems.* A node setup turns a few points into the full set
  of markers and previews.

Both are worth a prototype. The caution with each is principle 4 of the vision: nothing may be left
in the user's file. A Grease Pencil object or a nodes modifier used as a guide is a real object in
the scene, so it would have to be clearly temporary and removed on build, or the same look achieved
by drawing only. Decide after the prototype.

### 3.5 Smart placement inside the mesh

Four levels, built in this order:

1. **Centre of thickness.** A ray through the mesh gives an entry and an exit point. The joint goes
   halfway between. This alone is a large improvement on placing bones by eye.
2. **Follow the limb.** From the root, step along the inside of the mesh, re-centring at each step,
   to lay the rest of the part down the limb. Joints are put where the mesh bends or narrows.
3. **Whole-character fitting.** For full rigs, fit the whole template inside the mesh at once.
   First choice is classical template fitting (Baran and Popović 2007, whose skinning half is already
   the native automatic weights): no training data, no download. BoneCraft's marker detection is a
   second candidate and needs a hands-on test. A learned model such as UniRig could offer a
   suggestion through an opt-in extension. See `anim-rig-04`, part A.
4. **Map from an existing model.** From the notes: use a model that is already rigged as a template
   and map its bone structure onto a new mesh of similar build. This is the **Variation** stage: rig
   one character well, then reuse that rig across a cast. It ties in with the proportion variants in 3.3.

Every automatic result is a suggestion: markers are shown with a confidence colour and can be dragged.

### 3.6 The rig description

On build, every part records what it is and what belongs to it, as ordinary custom properties and
bone collections on the armature. This is the contract with the animation addon described in the
vision document. It is also what makes **Rebuild** possible, and what lets the validator explain
problems in the artist's terms ("the left hand is not attached to an arm").

### 3.7 Skinning

From the notes: skin faster and better than the native automatic weights, and better than voxel heat maps.

Approach, in order:

1. **Start with what is there.** Native automatic weights on build, so the first release works.
2. **Use the rig description.** Because we know what each part is, weights can be guided: fingers do
   not bleed into neighbouring fingers, a limb does not grab the torso. This is cheap and may fix most
   of the common failures.
3. **Research a better method.** Candidates to evaluate: voxel and distance-through-the-volume
   methods, which handle separate and overlapping meshes better; smoothing-based methods; and learned
   skinning models. Learned models carry the same questions as learned tweening in the animation
   document: training data we may use, a licence that fits a GPL application, and download size.
4. **Transfer from a template** when the rig was mapped from an existing model (3.5, level 4).

All hand correction is done with the native weight tools. The addon adds no second set.

### 3.8 Edit Mode helpers

Four small tools from the notes. Each is one operator with an icon, in the Armature menus and Tool Shelf.

| Tool | What it does | Status |
|---|---|---|
| **Bounding Bone** | On the active bone, create a bone that bounds it **(to confirm: a bone sized to enclose the active bone's chain or its mesh area, for use as a master or cage control)** | Needs a one-line definition from the maintainer |
| **Shapes Assignment** | Assign control shapes to selected bones from a shape library, with size and colour, in one step | New. Native custom shapes are set one bone at a time |
| **Proxy Rig Maker** | Make a light stand-in for a heavy character **(to confirm: low-detail proxy mesh pieces parented to bones for fast playback, or a simplified control rig)** | Needs a one-line definition |
| **Objects to Bones** | Turn selected objects into bones of an armature, keeping their positions, hierarchy and animation, with each object attached to its bone | New. Useful for mechanical models and imported rigid animation |

## 4. 🙂 Face and hand rigs (idea 7)

The promise: **drop, fit, done**, and still editable.

- **Hands.** A whole-hand preset drops onto the wrist socket and lays fingers into the mesh.
  Three or four fingers plus thumb. Curl, spread and fist controls come with it.
- **Faces.** A whole-face preset is placed with a handful of landmark markers (eye corners, mouth
  corners, chin, brow), each dragged on the mesh. The preset builds jaw, eyes, lids, brows and lips.
- **Three detail levels**, matching the low, mid and high collections: upgrading from one to another keeps the placement.
- **Shape-key faces.** Many characters use shape keys instead of bones. The face preset should be
  able to create on-face controls that drive existing shape keys, so both kinds of character are
  posed the same way. This is one place where a few drivers are unavoidable.
- **Posing a face** is where "drag on the mesh" matters most: pull the lip corner, not a control
  floating in front of the face. That tool is in the animation addon; the face parts must record the
  mesh areas for it.
- **Ready for capture.** Face and hand parts should name and place their bones so that motion markers
  from video can be connected to them quickly (see the animation document, section 8).

Lip sync belongs to a later phase and is split: the mouth-shape setup here, the driving in the
animation addon. One system, replacing the four in the submitted addons.

## 5. ❓ Open question: which engine builds the bones

This is the biggest technical decision for this addon. The requirements in 1.2 change the picture.

| | Our own light part recipes | Build on Rigify |
|---|---|---|
| Light and simple, few or no drivers, four levels deep | Designed for it from the start | **Unlikely to pass.** Rigify rigs are feature-rich, use many drivers and deep helper chains. Needs measuring |
| Maintenance | We maintain it | Bundled and maintained upstream |
| Part types available | Must be written. BoneCraft has limb, spine, tail, digit, face, foot, spline and mechanisms as a reference | Arm, leg, paw, spine, tail, finger, palm, tentacle, face and skin chains exist. No mechanical parts |
| Rebuild without losing animation | Must be designed in | Supported |
| Familiar to riggers | New | Widely known |
| Risk | More code of our own to carry | Heavy rigs, and we depend on its design |

**Recommendation:** our own light part recipes, because "performant, light and simple" is a headline
requirement and it is the one Rigify is least likely to meet. Keep recipes as plain data ("these
bones, these constraints"), with one small builder that creates them. BoneCraft's component layer is
built that way and is the reference to study, though its rigs also need measuring against the
four-level rule.

Before committing, a short trial: build the same arm both ways and compare bone count, driver count,
depth of dependencies and playback speed. Rigify stays fully usable beside the addon for those who want it.

## 6. ♻️ What to reuse from BoneCraft

| Piece | Use | Condition |
|---|---|---|
| Marker detection and guessing | Smart placement level 3 | Test on real characters first |
| Wizard flow | The guide panel: pick, fit, review, build | Rebuilt with standard layouts, as a helper and not a mode |
| Component builders | Reference for light part recipes | Measured against the requirements in 1.2 |
| Mechanisms (hinge, slide, piston, gear) | Utility parts | Reworked as parts with sockets |
| Skin generation with proxy mesh | Skinning | Only if better than native in tests |
| Rig validator | Validator | Reads the rig description |
| Chain dynamics | "Simulated" utility part | Result baked to keys, nothing live in the file |
| Everything else | Not used | See the BoneCraft review |

## 7. 🖥️ Interface

- **Asset shelf** in the 3D View: rig assets by family, as in the sketch. Part options use the
  existing asset wizard system from `bfa_default_library`.
- **Gizmos first**: sockets, limb length, finger count and blend width are handles in the viewport.
  Build and Test with Animation are viewport buttons. See `anim-rig-04`, part B.3.
- **One Tool Shelf tool**: "Rig Parts", active while placing, drawing and adjusting, with marker gizmos.
- **One sidebar tab**: the guide panel, options for the selected part, Build and Rebuild, validator results.
- **Menu entries**: Add > Armature for full rigs, Armature menus for the Edit Mode helpers.
- **Consistent look on every rig**: one colour scheme (left, right, centre, IK, FK), one set of
  control shapes, one collection layout with low, mid and high levels.
- Icons on every operator, plain panel titles, left-aligned checkboxes, strings in `locale/po`.
- No private layout code, no second translation system, no changes to region sizes.

## 8. ⚠️ Risks

- **Smart placement quality.** If joints land in the wrong place too often, the gesture feels broken.
  Needs testing on many body types early, using the character assets in 3.3.
- **The four-level rule against features.** Foot roll, IK/FK blending and stretch all add depth.
  Each part needs a decision on what it leaves out to stay light.
- **Sockets across very different parts.** A generic socket type must exist so creature and
  mechanical rigs are never blocked by a missing match.
- **Rebuild safety.** Rebuilding must not lose animation or hand-made changes. Needs clear rules on
  what a rebuild is allowed to touch.
- **Library upkeep.** Eight full rigs, about twenty parts and nine character meshes are content, and content needs an owner.
- **Licences** for mocap-compatible skeleton layouts and for any learned skinning model.

## 9. 🏁 Milestones

**First release (Phase 3 in the roadmap): Creation.**

- Parts: spine, arms with shoulder, legs with hips, feet, hand presets, two-joint and three-joint chains.
- Full rig: bipedal.
- Drag and drop with sockets, placement levels 1 and 2, marker gizmos, mirror.
- Build, Rebuild, guided automatic weights.
- Test with Animation, and a sweep check in the validator.
- Rig description written on build. One colour, shape and collection scheme.
- Character assets: cube, sphere, bipedal.

**Second release: Adaptation.**

- Draw-a-stroke placement. Toggle markers in and out on a built rig.
- Face presets. Shapes Assignment and Objects to Bones.
- Quadrupedal full rig, tails, hind and fore legs.

**Third release (Phase 5): Variation and beyond bipeds.**

- Map a rig from an existing model. Proportion variants.
- Bird, lizard, fish, dinosaur, insect and arachnid rigs. Wings, tentacle.
- Piston, four-joint, curve and simulated chains.
- Mocap-compatible skeletons, if the licence check allows.
- Better skinning method, if the research finds one.
