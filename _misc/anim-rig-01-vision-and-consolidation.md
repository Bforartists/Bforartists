# Animation and Rigging in Bforartists: Vision and Consolidation Plan

Draft 7, 2026-11-25. Status: proposal for discussion, nothing decided.

Companion documents:

- `anim-rig-02-rigging-addon.md`: the rigging addon in detail.
- `anim-rig-03-animation-addon.md`: the animation addon in detail.
- `anim-rig-04-research-and-puppetry.md`: assessment of papers and open projects, the asset library as the rigging system, and live puppetry.
- `anim-rig-05-animation-clip-library.md`: animation clips as real assets, dragged onto rigs and into the NLA.
- `anim-rig-06-campaign-2027.md`: **the build plan.** Seven tiers, how each is built, tested, documented and released, and the decisions taken so far.
- `anim-rig-07-addon-survey.md`: what thirty-two existing add-ons teach us, the "white box" habits, and proposed additions per tier.
- `7086-anim-assist-review.md`, `7087-ghost-tool-review.md`, `7088-bonecraft-review.md`: reviews of the three submitted addons.

## At a glance

> 🎭 **Rig by dragging. Animate by touching.**
> Two addons that turn the 3D View into a puppet workshop.

**The goal:** make animation fun, to the point, and about storytelling, whoever or whatever the
character is. A beginner should be able to work like a capable technical director and animator.

**The rule:** what we add is *handling* and *setup* of what Blender already has. The finished
character is plain Blender data and renders in vanilla Blender one to one (section 3.3).

| | What it is | The artist's question |
|---|---|---|
| 🦴 **Rigging addon** | Drag rig parts onto a model, they snap together, press Build | "How do I make this thing movable?" |
| 🎬 **Animation addon** | Grab the character to pose it, see ghosts and arcs, get smart in-betweens | "How do I make it move?" |
| 🎞️ **Clip library** | Animation clips as assets, dropped onto rigs and into the NLA | "Can I reuse this motion?" |
| 🤖 **Optional extras** | Learned helpers and capture, as opt-in downloads | "Can the computer suggest it?" |

**Every tool is built in four levels**, described in section 3.1. These icons mark them in all six documents:

| Icon | Level | In short |
|---|---|---|
| 🖐️ | **1. Touch** | Gesture first, viewport first, real-time first |
| 🧩 | **2. Assemble** | High level: easy to use, modular |
| 🎛️ | **3. Tune** | Mid level: tunable, editable, procedural |
| 🔬 | **4. Craft** | Low level: granular control |

Other icons used: 🦴 rigging, 🎬 animation, 🎞️ clips, 👻 ghosts (onion skin), 📌 pins, 🧲 sockets,
🎭 live puppetry, 📦 assets, ⚙️ core C++ work, 🤖 optional download.

## 1. 🧭 Why this document exists

Three addons were submitted (Anim Assist, Ghost Tool, BoneCraft) to improve animation and rigging.
The reviews found a good idea inside each one, but no shared plan behind them: they are three
separate toolboxes that overlap each other and the native tools.

This document supplies the plan that was missing. It answers three questions:

1. What experience do we want?
2. How do three addons become two?
3. In what order do we build it, and what can be reused from the submitted code?

## 2. 🎭 The vision: puppetry

**Animating a character should feel like moving a puppet with your hands, in the viewport.**

Today a Bforartists animator spends much of the day in the Dope Sheet and Graph Editor, and a rigger
spends it in Edit Mode, constraint stacks and property panels. Both are working on a description of
the character instead of the character.

The goal is to turn that around:

- **The viewport is the workplace.** The Dope Sheet and Graph Editor stay, but as places to refine,
  not places you must go.
- **You touch the character, not the controls.** Click and drag the arm to move the arm.
- **You build a rig by placing parts**, the way you would assemble a puppet, not by naming bones.
- **The computer fills in what is obvious**: where a joint sits inside a mesh, what the body does
  when a hand is pulled, what happens between two poses.

This is point and click first, taken one step further: **point and drag**.

### 2.1 Five artists, five afternoons

What the finished tools should make possible. The tier that delivers each one is in
`anim-rig-06-campaign-2027.md`.

| Who | What they want | What they do | Tier |
|---|---|---|---|
| 🐉 **An illustrator** with a sculpted dragon, who has never rigged | A posed dragon for a book cover | Drops the quadruped rig on the model, drags two wing parts onto the shoulders, draws one stroke down the tail. Presses Build. Pulls the neck round and lifts a claw | 1 and 5 |
| 🤖 **A solo game developer** with a walking robot | A walk cycle to export | Selects the robot's pieces, turns them into bones, drops pistons on the legs. Each piston is one slider from 0 to 1. Drags a walk clip from the library to check the knees | 1, 2 and 5 |
| 🎬 **An animator** on a short film | An acting shot, blocked today | Hides every control. Pins both feet, pulls the chest forward, pulls a hand to the table. Turns on ghosts, drags the arc of the hand, presses Tween | 3 and 4 |
| 📺 **A teacher** who records lessons with a mascot | Thirty seconds of a talking, waving character | Presses Record and moves the head with the mouse while the audio plays. Second take: the arm. Third take: the webcam drives the face | 6 |
| 🧑‍🔧 **A studio rigger** | A house rig the whole team can use | Opens a kit rig, switches the markers back on, swaps the hand for a four-finger one, adds a custom ear part and saves it as an asset. It is all ordinary bones, so the usual tools work | 1 |

The first four never open the Graph Editor. The fifth can open anything, and finds nothing hidden.

## 3. 📐 Design principles

### 3.1 Four levels of control

Every tool is designed in four levels, in this order. An artist gets a result at level 1 and is never
forced further down. A specialist can always go further down, and finds plain Blender data at the bottom.

| Icon | Level | In short |
|---|---|---|
| 🖐️ | **1. Touch** | Gesture first, viewport first, real-time first |
| 🧩 | **2. Assemble** | High level: easy to use, modular |
| 🎛️ | **3. Tune** | Mid level: tunable, editable, procedural |
| 🔬 | **4. Craft** | Low level: granular control |

What each level promises:

- 🖐️ **Touch.** You do it by clicking and dragging on the character, and you see the result while
  your hand is still moving. No "apply and wait".
- 🧩 **Assemble.** Ready-made pieces that fit together, and a sensible result with no settings touched.
- 🎛️ **Tune.** Every result has handles and a few options. Change one and the result updates. You
  never start over to change your mind.
- 🔬 **Craft.** Underneath it is ordinary bones, constraints, weights and keyframes, and every native
  tool works on them.

The same task, at each level:

| Task | 🖐️ Touch | 🧩 Assemble | 🎛️ Tune | 🔬 Craft |
|---|---|---|---|---|
| **Rig an arm** | Drag the arm part onto the model. It lands inside the mesh and snaps to the shoulder | Arm, hand and shoulder come as matching parts. Build Rig does the rest | Drag the elbow marker, choose IK or FK, set the finger count, press Rebuild | Edit the bones, constraints and weights by hand |
| **Pose a reach** | Pin the feet, pull the hand | The Puppet tool works on any rig, with nothing to set up | Set how stiff the spine is, how far the hips may follow | Rotate single controls, edit the keys |
| **In-between a jump** | Drag the arc of the hips where you want it | Press Tween between two poses | Timing per part, overlap amount, which feet stay planted | Edit the resulting keys in the Graph Editor |
| **Reuse a walk** | Drag the clip onto the character | Clips that fit the rig light up | Replace, insert, layer or NLA strip. Trim and loop | Edit the action like any other |

Two rules follow:

1. **Level 1 is designed first.** A feature that exists only as a panel of settings is not finished.
2. **Level 4 is never blocked.** A feature that cannot be opened up and edited by hand is not finished either.

"Real-time first" means immediate feedback while dragging. Its fullest form, performing a take live,
is the last tier of the campaign, because it needs the posing tools underneath it.

### 3.2 The nine principles

Every feature in the two addons is measured against these.

1. **Gesture first.** The main way to use a tool is a click or drag in the viewport. Panels hold
   options, never the only way in.
2. **Still point and click.** Every gesture tool is also a visible button with an icon and a tooltip.
   Hotkeys are optional accelerators.
3. **Plain Blender results.** Whatever the tools do, the file contains only standard bones,
   constraints, drivers and keyframes. A file made with these addons opens, plays and renders in
   Blender with the addons absent. Solvers, predictions and helpers are tools that write plain data,
   never something the file needs at playback.
4. **Nothing left behind.** No helper objects, collections, materials or hidden datablocks in the
   user's scene. Viewport aids are drawn, not created.
5. **Both graphics backends.** Everything drawn works on OpenGL and Vulkan (and Metal on macOS).
6. **One way to do a thing.** If Bforartists already has a tool, the addon improves or reuses it. It
   does not add a second one.
7. **Works on rigs we did not make.** Animation tools must work on Rigify rigs and imported rigs,
   with a better experience on rigs built by our rigging addon.
8. **Suggestions, never surprises.** Anything the computer proposes (a pose, an in-between, a joint
   position) is shown as a preview and applied only when the artist accepts it.
9. **Small and readable.** Each addon is small enough for one maintainer to read fully and to carry
   through the weekly Blender merges.

### 3.3 Handling and setup

Set by the maintainer on 24 November 2026. It sharpens principles 3 and 4.

**Anything we add is one of two things:**

| | What it is | Examples | In the file afterwards |
|---|---|---|---|
| 🏗️ **Setup** | A tool that builds native Blender data for the artist | Bones, constraints, a few drivers, weights, shape keys, native modifiers and simulations, actions | Only that native data |
| 🖐️ **Handling** | A tool for working that data with your hands | Posing on the mesh, pins, ghosts, paths, gizmos, snapping, drag and drop | Nothing, or keyframes |

**What is not allowed** is a third kind: anything the character needs in order to give the right
result. No solver of ours that the pose depends on, no modifier of ours, no script the rig must
run, no helper rigs.

**Speed is handling** (maintainer, 25 November 2026). Performance does not have to match vanilla
Blender. Only the result does. So we may add things that make playback faster, in the addons or in
Bforartists itself, on one condition: **without them the file falls back to plain Blender
evaluation and gives the same result, only slower.**

| | Allowed | Not allowed |
|---|---|---|
| ⚡ **Speed-up** | A cache of the evaluated pose or mesh, a light stand-in shown while playing, faster evaluation in Bforartists. Remove it and the same frames come out | A cache or helper that holds the only copy of the motion. Remove it and the character moves differently or not at all |

A speed-up has to say when it is in use, has to refresh or switch itself off when the rig or the
animation changes, and can always be cleared with one button.

**The vanilla check.** A file made with these tools is opened in vanilla Blender of the same version,
with our addons absent, and a frame is rendered. It must match the same frame rendered in
Bforartists. Any speed-up is first switched on, and the frame is rendered both with it and in
vanilla Blender without it. Playback speed is not compared. This check is part of the test step
of every tier.

What this means in practice:

- The rig's switches (IK or FK, parent, detail level) are ordinary properties. Our panel shows them
  nicely, and without our panel they are still there and still work.
- Our panel and gizmos come from the addon reading the rig description. Nothing is stored in the
  file to draw them.
- Learned helpers, capture and suggestions produce keyframes or marker positions, then step away.
- The rig description is plain custom properties. Vanilla Blender ignores it.

### 3.4 White box habits

Taken from the survey of existing add-ons (`anim-rig-07`, section 1) and accepted. They are how
level 4 (🔬 Craft) is kept honest.

1. **Visible stages.** Markers, then bones, then controls and weights. Each can be inspected before the next.
2. **A report under the button.** After every large operator, a short list of what changed and what to check.
3. **Refuse and explain.** If it cannot work, stop, say why, change nothing.
4. **One step back.** One undo per gesture and per operator.
5. **The source is never overwritten.** Tween, bake and retarget write to a new action or layer.
6. **Bakes are reduced to editable keys.**
7. **Guesses are stored as ordinary data** the artist can edit: vertex groups, bone collections, key types.
8. **The rig is never converted.**
9. **Honest scope.** Known limits are written in the manual, with numbers.

## 4. 🔀 From three addons to two

### 4.1 The two addons

| | **Rigging addon** | **Animation addon** |
|---|---|---|
| Working folder name | `bfa_rigging` | `bfa_animation` |
| The artist's question | "How do I make this thing movable?" | "How do I make it move?" |
| Mode it lives in | Object, Edit Armature, Weight Paint | Pose, Object |
| Where its UI goes | Asset shelf (rig parts), viewport gizmos, one sidebar tab | Tool Shelf tools, Overlays popover, one sidebar tab |
| Result in the file | Armature, constraints, drivers, weights | Keyframes |

Final names are open. Plain names are suggested so the addons read as part of Bforartists.

### 4.2 The contract between them

The two addons must not depend on each other's code. They share one thing: **rig description data**,
stored on the armature as ordinary custom properties and bone collections.

The rigging addon writes it. The animation addon reads it. It says, in plain terms:

- which parts the rig has (arm, leg, spine, tail, piston) and which bones belong to each;
- which control moves which part, in FK and in IK;
- which parts mirror each other;
- which spots are natural pins (feet, hands, hips);
- which area of the mesh belongs to which part.

When this data is missing (a Rigify rig, an imported rig), the animation addon works it out as well
as it can: Rigify rigs from Rigify's own naming and properties, other rigs from bone names, hierarchy
and skin weights. The artist can correct the guess once and it is saved on the rig.

This contract is what makes "drag the mesh to pose" and "full body IK" work on any rig, and it is the
main thing to design carefully before any feature work.

### 4.3 Where the submitted code goes

| Submitted | Goes to | Notes |
|---|---|---|
| **Ghost Tool**: mesh onion skin | Animation | Needs a new way to build and draw ghosts (see the animation document) |
| **Ghost Tool**: editable motion paths, marker and handle drag | Animation | The best gesture feature already written |
| **Ghost Tool**: Physics Feel | Animation, later | Seed for motion suggestions |
| **Ghost Tool**: easing presets, snapshots, Diff mode, Draw to Keys, export, API, floating toolbar | Dropped | |
| **Anim Assist**: matching (IK/FK, world, parent, target) | Animation | Becomes part of pins and full body IK |
| **Anim Assist**: mirror pairs | Animation | Pair detection also feeds the rig description |
| **Anim Assist**: proxy bake sessions | Animation | Reworked as "work in a temporary space, bake back to plain keys" |
| **Anim Assist**: ripple and gap retiming | Native menus | Plain entries in the Dope Sheet menus, not an addon feature |
| **Anim Assist**: Timeline overlay, header strips, macros, recovery, help browser, layers, curve and breakdown duplicates | Dropped | |
| **Anim Assist** and **BoneCraft**: lip sync and visemes (four systems in total) | One system, split | Face rig setup in Rigging, driving it in Animation. Later phase |
| **BoneCraft**: auto-rig wizard, marker detection, auto skin | Rigging | Marker detection becomes the "smart placement" behind drag and drop |
| **BoneCraft**: rig components (limb, spine, tail, digit, face, foot, spline) | Rigging | The starting point for the parts library |
| **BoneCraft**: mechanisms (hinge, slide, piston, gear) | Rigging | Become parts in the same library |
| **BoneCraft**: chain dynamics | Both | The "simulated" utility part in Rigging, follow-through suggestions in Animation. Always baked to keys |
| **BoneCraft**: rig validator | Rigging | |
| **BoneCraft**: control picker | Dropped | Replaced by posing on the mesh |
| **BoneCraft**: retargeting | Animation, later | Needs fixing for Blender 5 first |
| **BoneCraft**: weights, pose library, breakdowner, correctives, wrappers, task board | Dropped | Native tools exist |
| **BoneCraft**: VRChat, VRM, MMD, atlas baker | Outside | The author's own extension on the Blender Extensions platform |

Roughly: of about 173,000 submitted lines, perhaps 25,000 to 35,000 are candidates for reuse, and
all of it needs rework to meet the principles in section 3.

## 5. 💡 The ideas, at a glance

Each is developed in the rigging or animation document. "Core work" means a change in Bforartists
C++, which costs more and has to survive merges, so it is flagged early.

| # | Idea | Addon | Reuse from submissions | Core work needed | Difficulty |
|---|---|---|---|---|---|
| 1 | Drag and drop rig parts that socket together, with smart placement inside the mesh | Rigging | BoneCraft components, marker detection | No | Medium |
| 2 | Drag on the mesh to pose, with the part highlighted | Animation | None | No to start, helpful later | Medium |
| 3 | Full body IK with pins | Animation | Anim Assist matching | No to start, likely later for speed | High |
| 4 | Fast onion skin and motion paths on both graphics backends | Animation | Ghost Tool (design and UI, not the method) | **Yes** for proper onion skin | High |
| 5 | Motion prediction and suggested poses | Animation | Ghost Tool Physics Feel | No | Medium, open-ended |
| 6 | Smart tweening from key poses and guides | Animation | None | No | Medium for the rule-based part, very high for the learned part |
| 7 | Quick face and hand rigs from presets | Rigging | BoneCraft face and digit components | No | Medium |
| 8 | Modular enough for machines and creatures | Rigging | BoneCraft mechanisms, tail and spline components | No | Medium, mostly design |

Added from the maintainer's own notes (April 2026):

| # | Idea | Addon | Reuse from submissions | Core work needed | Difficulty |
|---|---|---|---|---|---|
| 9 | Rig asset library: full rigs (biped to arachnid), human, animal and utility parts, mocap-compatible skeletons, starter character meshes | Rigging and `assets_bfa/` | Little | No | Medium, mostly content. Licence check for mocap skeletons |
| 10 | Draw a stroke on the model to make a rig part | Rigging | None | No | Medium |
| 11 | Map a rig from an existing model onto a new mesh | Rigging | BoneCraft marker detection, retarget mapping | No | High |
| 12 | Better skin weights than automatic weights or voxel heat maps | Rigging | BoneCraft skin generation, to be tested | Possibly | Medium for guided weights, high for a new method |
| 13 | Edit Mode helpers: Bounding Bone, Shapes Assignment, Proxy Rig Maker, Objects to Bones | Rigging | None | No | Low each |
| 14 | Motion markers to bones, from the Clip Editor, Sequencer video or webcam | Animation | None | No for tracked markers, yes or a model for markerless | Low for quick setup, very high for markerless |

Added from the research and brainstorm in `anim-rig-04-research-and-puppetry.md`:

| # | Idea | Addon | Reuse | Core work needed | Difficulty |
|---|---|---|---|---|---|
| 15 | Character kits: body-part assets that carry mesh, rig part and weights, and blend together when dropped | Rigging and `bfa_default_library` | Existing asset wizards and Mesh Blend by Proximity | No | High, needs a prototype |
| 16 | Fit a full rig into a mesh by template fitting (Baran and Popović) | Rigging | The skinning half is already native | No | Medium to high |
| 17 | Test a new rig with stock animations before committing | Rigging | CC0 animations from mesh2motion, if adopted | No | Low |
| 18 | Live puppetry: record a performance with the mouse, layered in takes | Animation | Mesh posing and pins | No | Medium |
| 19 | Puppetry from webcam, phone or game controller | Animation, as opt-in extensions | None | Yes for camera and controller input | High |
| 20 | Learned rigging and tweening as opt-in extensions that plug into core "slots" | Both | UniRig, MotionBricks as candidates | No | High, licence checks first |

The notes also set four requirements for every rig the addon builds: **modular, performant, flexible,
intuitive**, with "performant" spelled out as mostly bones and constraints, few or no drivers, and no
more than four levels deep. These are in the rigging document, section 1.2, and they drive the engine
decision in section 9 below.

## 6. 🔭 What others do

Short notes so we design with our eyes open. Items marked (searched) were looked up for this
document; the rest is general knowledge and should be confirmed before anyone relies on it.

- **Blender itself.** The Animation 2025 project has delivered layered, slotted actions. A search of
  the current roadmap material found no committed plan for full body IK, mesh onion skin or rigging
  with nodes (searched). So these gaps are likely to stay open in Blender for a while, which makes
  them a real chance for Bforartists to differ, and a merge risk if Blender later ships its own.
- **Posing on the mesh.** Blender Studio ran an experiment with "mesh-based character interaction",
  and an older Blender design task (#92218, "Mesh Gizmos / Face Maps") was shelved as too unstable
  (searched). A commercial add-on, Surface Poser, sells this workflow today for Blender 4.5 and later
  (searched). So the idea is proven, wanted, and not in Blender.
- **Cascadeur.** The reference for physics-aware posing and automatic in-betweens. It added learned
  in-betweening in 2025, motion styles later that year, and "Motion Generation" between key poses in
  2026. It runs on the artist's computer and was trained on the vendor's own motion capture (searched).
  That last point matters: the data is the hard part, not the code.
- **Maya and others.** Full body IK with pins (HumanIK) and on-mesh selection ("invisible rigs") are
  long-standing studio workflows. Rig pickers are the older answer to the same problem.
- **Rigify.** Already modular: a rig is built from typed parts (arm, leg, paw, spine, tail, tentacle,
  finger, face, skin chains). What it lacks is the artist-facing side: placing parts by dragging and
  fitting them to a mesh.

## 7. 🗺️ Roadmap

**Superseded by `anim-rig-06-campaign-2027.md`.** The tier plan there reorders this roadmap after the
maintainer's decisions of 24 November 2026: the rigging kit comes first, viewport posing comes before
any puppetry, character kits wait until the kit has proven itself, and learned features are opt-in
through Coworker or optional downloads. The phases below are kept as the first draft.

**Changed on 25 November 2026 (maintainer):** full body IK with pins moves forward, from Phase 4 to
Phase 2, because it is what makes posing fun. Live recording with the mouse or a webcam moves to
Phase 4. The campaign document carries the same change in its Tiers 2 and 4.

Phases are ordered so that each one ships something an artist can use, and so the riskiest
foundations are tested early. No dates: each phase needs sizing once the open decisions are made.

**Phase 0: Foundations (design, little code)**

- Agree this vision and the principles.
- Design the rig description contract (section 4.2).
- Decide the open questions in section 9.
- Prototype the two riskiest pieces, throwaway quality: the mesh highlight and drag (idea 2), and the
  onion skin drawing path on OpenGL and Vulkan (idea 4).

**Phase 1: See your motion (Animation addon, first release)**

- Onion skin and live motion paths, with editable paths (ideas 4).
- Built from the reduced Ghost Tool, with ghost generation replaced.
- Opt-in. This is the smallest release that proves the "work in the viewport" direction.

**Phase 2: Touch the character (Animation addon)**

- Drag on the mesh to pose (idea 2), reading the rig description or guessing it.
- **Full body IK with pins** (idea 3): pin the feet, pull a hand, and the body follows.
- Matching from Anim Assist folded in.
- Mirror-pair tools.
- Quick setup of tracked markers to bones, with bake to keys (first level of idea 14).

**Phase 3: Build a puppet (Rigging addon, first release)**

- Rig parts in the asset shelf, drag and drop with sockets and smart placement (idea 1).
- Body and hand parts, the bipedal full rig, starter character meshes (ideas 7 and 9).
- Build, Rebuild, guided automatic weights, validator with a sweep check, Test with Animation (idea 17).
- Rig parts registered with the existing asset wizard system.
- A second release adds drawing a stroke to make a part, face presets and the Edit Mode helpers (ideas 10 and 13).
- Writes the rig description, so Phase 2 tools work at their best on these rigs.

**Phase 4: Perform and tween (Animation addon)**

- Live recording with the mouse: perform a part while the timeline plays (idea 18).
- Live recording with a webcam: face first, then hands (from ideas 14 and 19). The detection model
  is an optional download.
- Rule-based smart tweening: arcs, contact locking, overlap (first half of idea 6).

**Phase 5: Beyond bipeds (Rigging addon)**

- Mechanical parts and free-form creature parts (idea 8).
- The remaining full rigs: bird, lizard, fish, dinosaur, insect, arachnid (idea 9).
- Map a rig from an existing model, and template fitting of full rigs (ideas 11 and 16).
- Character kits, if the blending prototype works (idea 15).
- A better skinning method, if the research finds one (idea 12).

**Phase 6: Suggestions (Animation addon, research)**

- Motion and pose suggestions (idea 5).
- Learned in-betweening, if the data and licensing questions can be answered (second half of idea 6).
- Face animation and lip sync.
- Markerless full body capture from video (last level of idea 14).
- Further puppetry inputs as opt-in extensions: face-capture apps, phone, game controller (idea 19).
- Learned rigging and tweening extensions (idea 20).

## 8. 🤝 Working with the contributor

The submitted addons show a contributor with a great deal of energy and the right instincts about
what is missing. The reviews ask for much smaller submissions. This plan gives that request a positive
shape: here is where each good piece belongs, and here is the order.

Suggested approach:

1. Share this vision and the three reviews together, so the "no" comes with a "here is the yes".
2. Ask for Phase 1 first, as one pull request against the animation addon folder.
3. Agree the rules once (see each review, section 9) so later phases do not repeat the discussion.
4. Keep design discussion in tracker issues, one per idea, linked from the pull requests.

## 9. ❓ Open decisions

Decisions already taken are recorded in `anim-rig-06-campaign-2027.md`, section 1. In short:
learned features are opt-in through Coworker or optional downloads (decision 3 below), CC0 content is
welcome as an opt-in library (decision 5), and the addons stay opt-in until beta-tested (decision 4).
Core C++ work is now decided (1). Still open: the engine that builds the bones (2), the three notes
that need a definition (6), and who owns the rig description (8).

These need a maintainer decision before Phase 1 starts. A recommendation is given for each.

1. **Is core C++ work in scope for onion skin?** Proper onion skin needs Bforartists to evaluate the
   character at other frames without moving the playhead, the way native motion paths already do.
   An addon alone cannot do that cleanly. *Recommendation: yes, as a small, isolated core feature,
   with an addon-only fallback first (see the animation document).*
   **Decided, 25 November 2026: yes, and wider.** Ideas that need speed or a place inside the editors
   are built natively in C++: onion skin, live and editable motion paths, picking on the mesh, drop
   targets, retiming operators. The addons hold setup and guidance. Work starts in 2027, after asset
   and product milestones. See `anim-rig-06`, sections 4 and 6.
2. **Which engine builds the bones: our own light recipes, or Rigify?** Rigify is bundled, maintained
   upstream and already modular, but its rigs are feature-rich and heavy, which is the opposite of the
   "light, few drivers, four levels deep" requirement. *Recommendation: our own light part recipes,
   kept as plain data, with BoneCraft's component layer as the reference to study. Confirm with a
   short trial that builds the same arm both ways and compares bone count, driver count, depth and
   playback speed.*
3. **How far do we go with learned (AI) features?** Learned tweening, markerless capture and learned
   skinning each need a trained model, data we have the right to use, a runtime to ship, and a licence
   that fits a GPL application. *Recommendation: commit only to the rule-based and physics-based
   versions now, and treat every learned part as research and a separate opt-in download if it ever happens.*
4. **Are the addons on by default?** *Recommendation: opt-in until Phase 2 has been tested by
   animators, then decide per addon.*
5. **May we ship mocap-compatible skeletons?** Layouts published by engine and tool vendors have
   their own terms. *Recommendation: check before building any, and prefer mapping presets over
   shipping copies of the skeletons.*
   Update: mesh2motion publishes rigs and animations under CC0, which may remove the need. See `anim-rig-04`, part A.3.
6. **Three notes need a one-line definition** before design: Bounding Bone, Proxy Rig Maker, and the
   "low, mid, high" collections. See the rigging document, sections 1.2 and 3.8.
7. **Five more decisions** from the research document are listed in `anim-rig-04`, part D: CC0 seed
   content, character kits, learned features as extensions, mouse puppetry (now Phase 4), and device input in the core.
8. **Who owns the rig description format?** It will be relied on by both addons and by user files.
   *Recommendation: Bforartists maintainers own it, documented in the manual, versioned from the start.*
