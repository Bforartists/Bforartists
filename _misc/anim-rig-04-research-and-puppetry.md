# Research Notes: Papers, Open Projects, the Asset Library and Live Puppetry

Draft 2, 2026-11-24. Status: brainstorm and assessment, nothing decided.
Read `anim-rig-01-vision-and-consolidation.md` first. This document feeds the rigging document
(`anim-rig-02`) and the animation document (`anim-rig-03`).

It answers three questions from the maintainer:

1. Are these papers and projects useful for the vision?
2. Can the asset library itself be the rigging system: drag, drop, blend, and it is rigged?
3. What about puppetry out of the box, from a webcam, a phone or a controller?

**How the sources were checked.** Repository licences, model licences and READMEs were read on
GitHub and Hugging Face on 24 November 2026. Papers were read from their project pages or
abstracts only, not in full. One paper (Baran and Popović) could not be opened and is described from
general knowledge. Nothing was installed or run. Anything not checked is marked.

---

## At a glance

**The papers and projects, sorted by what we can do with them:**

| | Project | What an artist would notice |
|---|---|---|
| ✅ **Use** | Baran and Popović 2007 | Drop a full rig on a character and it finds its own place inside the mesh |
| ✅ **Use** | mesh2motion (CC0 content) | A starter library of rigs and clips, and a "Test with Animation" button |
| 🤖 **Optional download** | UniRig, SkinTokens | A "Suggest Skeleton" button for odd creatures with no template |
| 🤖 **Optional download** | MotionBricks | Learned in-betweens for humanoids, if its terms allow |
| 💡 **Inspiration** | AnyMachine | Machine controls as 0 to 1 sliders, and a sweep check that finds parts passing through each other |
| 💡 **Inspiration** | UniMate, RigNet | Nothing shipped. Non-commercial terms, or superseded |

**The asset library as the rigger:** 📦 parts from the shelf, then 🧲 body parts that arrive already rigged and blend together.

**Live puppetry, in the order to build it:**
🖱️ mouse and pen, ⌨️ key triggers, 🔊 audio level, then 📱 phone, 📷 webcam, 🎮 controller.
The first three need no hardware and no download.

## Part A. The papers and projects

### A.1 Summary

| Project | What it does | Kind | Code licence | Model or asset licence | Use for us |
|---|---|---|---|---|---|
| **Baran and Popović 2007** ("Pinocchio") | Fits a template skeleton inside a mesh, then computes skin weights | Classical maths, no training data | Technique is published | None needed | **High.** Half of it is already in Bforartists |
| **mesh2motion** | Web app: import a model, pick a skeleton type, fit it, test animations, export | Hand-built tool and content | MIT | **CC0** rigs, models and animations | **High.** Content and workflow |
| **UniRig** (and successor SkinTokens) | Mesh in, skeleton and skin weights out, for humans, animals and objects | Learned model | MIT | MIT model card. Training data from Objaverse, terms not checked | **Medium.** Optional download, not built in |
| **RigNet** (arXiv 2005.00559) | Mesh in, skeleton and skin weights out | Learned model, 2020 | GPL 3 | Weights and data terms not checked | **Low.** Superseded by UniRig |
| **MotionBricks** (NVIDIA) | Generates motion between poses you place, in real time. Also object interaction | Learned model | Apache 2.0 | NVIDIA Open Model Agreement, not read | **Medium to high** as the reference for smart tweening. Humanoid only, NVIDIA runtime |
| **UniMate** | Text to motion for many skeleton types, including your own rig | Learned model | MIT | **CC BY-NC 4.0** checkpoints, non-commercial | **Inspiration only.** Cannot ship |
| **AnyMachine** | Experiments in building working mechanical rigs by script, with automatic checks | Method notes and scripts, not a library | MIT | Not applicable | **Inspiration** for mechanical parts and the validator |

### A.2 Baran and Popović 2007: automatic rigging by fitting a template

*Described from general knowledge; the PDF could not be opened.*

The paper has two halves:

1. **Skeleton fitting.** Take a ready-made skeleton and find where it best sits inside a new mesh,
   using the mesh's inner volume.
2. **Skin weights by heat.** Treat each bone as a heat source and let the heat spread over the surface.

**The second half is already in Bforartists.** The native "With Automatic Weights" cites this paper
directly in the source (`source/blender/editors/armature/meshlaplacian.cc:351`). So the well-known
weaknesses of automatic weights are the weaknesses of this method: it fails on meshes with holes,
separate shells or overlapping parts.

**The first half is not in Bforartists, and it is exactly idea 11** ("map a bone structure onto any
mesh") and smart placement level 3 in the rigging document. It needs no training data, no download
and no special hardware, and it works from a template, which fits our library of full rigs perfectly:
drop the biped rig on a character and it finds its own place.

**Verdict:** the best first approach for whole-character placement. Classical, predictable, licence-free.
Worth a prototype before looking at any learned model.

### A.3 mesh2motion: open content and a proven workflow

A web application in the spirit of Mixamo, but open. The flow is: import a model, pick a skeleton
type, adjust the skeleton to fit inside the model, test with animations, export.

Why it matters to us:

- **The assets are CC0**: rigs, models and animations, with Blender source files in a separate
  repository (`Mesh2Motion/mesh2motion-assets`). CC0 content can be shipped in Bforartists with no
  conditions. This could seed the rig asset library *and* a starter animation library, and it sidesteps
  the licence question around vendor skeleton layouts.
- **The workflow matches ours** and adds one step worth copying: **test the rig with stock animations
  before you commit.** Seeing a walk cycle on the freshly fitted rig is the fastest way to spot bad
  joints and bad weights.
- The code is MIT but is TypeScript for the browser, so it is a reference for behaviour, not code to reuse.

**Verdict:** adopt the content if quality holds up on inspection, and add a "Test with Animation"
step to the rig builder. The assets were not opened for this review.

### A.4 UniRig and SkinTokens: learned rigging for anything

A trained model that looks at a mesh and writes a skeleton and skin weights, for people, animals,
fantasy creatures and objects. SkinTokens is the same group's newer version.

For it:

- It handles the "alien creature" case that template fitting cannot: no template needed.
- Code and model card are both MIT, which is compatible with Bforartists.

Against building it in:

- It needs a large machine-learning runtime and, in practice, a strong graphics card. That is
  hundreds of megabytes to gigabytes, and several of its dependencies are awkward to install.
- The output is a bare skeleton with weights: no controls, no IK, no sockets. It gives us a
  *suggestion for marker placement*, which our parts would then be built on.
- Its training models come from Objaverse, a large collection of user-uploaded assets with mixed
  licences. Whether that affects the model's terms was not checked.

**Verdict:** a good candidate for a separate, opt-in "Suggest Skeleton" extension that feeds markers
into our rig builder. Not part of the core addon. Design the placement step so a suggestion can come
from anywhere: a stroke, a template fit, or a model like this.

### A.5 RigNet

The 2020 paper that started learned rigging. Same idea as UniRig, older, slower and narrower.
Code is GPL 3. **Verdict:** historical reference. UniRig covers it.

### A.6 MotionBricks: the closest thing to the tweening dream

NVIDIA's 2026 system. Its "Inbetweener" demo is the workflow from idea 6: choose poses, place them,
and it generates the motion through them. It also generates walking, running, vaulting and sitting
from simple targets, and claims real-time speed.

For it:

- Code is Apache 2.0, and the model is published.
- It is built around sparse key poses, which is how animators think.

Against, today:

- **Humanoid only**, on two fixed skeletons (NVIDIA's SOMA and a robot). Any other character needs
  retargeting in and out, and creatures or machines are not covered.
- **NVIDIA runtime.** It is built on NVIDIA's own libraries. Whether it runs on other graphics cards
  was not checked.
- **Model terms.** The weights are under the "NVIDIA Open Model Agreement", which was not read. It
  must be read before any plan relies on it.

**Verdict:** the reference for what smart tweening should feel like, and the strongest candidate for
a future opt-in "learned tween" engine for humanoids. It confirms the plan in the animation document:
build the tween tool so the rule-based engine is one source of in-betweens and a learned engine can
be plugged in as another.

### A.7 UniMate: motion for any skeleton, but not usable

A 2026 model that animates very different skeletons (bipeds, quadrupeds, birds, fish, insects,
snakes, rigid machines) from a text prompt, and accepts your own rig.

It is the right idea for "works on aliens and machines too". But the published checkpoints are
**CC BY-NC 4.0, non-commercial**, and part of its training data is a commercial pack that cannot be
redistributed. Bforartists users do commercial work, so this cannot be shipped or recommended.

**Verdict:** inspiration only. Worth watching: it proves cross-skeleton motion generation is
possible, and a later release may come with usable terms.

### A.8 AnyMachine: ideas for mechanical rigging

Not a tool. It is a set of documented experiments where mechanical rigs (a laptop hinge, a
four-legged walker, a spider, a 160-part machine with working hydraulics) are built by script and
checked automatically. Three ideas are worth taking:

1. **Every control is a simple 0 to 1 slider.** A hinge is "closed to open", a piston is "in to out".
   That is the right artist-facing language for mechanical parts.
2. **Measure the joint from the mesh.** Find the hinge axis from the geometry instead of asking the
   artist to place it. This is smart placement for machines.
3. **Check by sweeping.** Run every control through its range and test for parts passing through
   each other and for sliding feet. BoneCraft's mechanism "Sweep test" is the same idea, and it
   belongs in our validator for every rig, not just machines.

**Verdict:** design input for the utility parts and the validator.

### A.9 What this changes in the plan

1. **Whole-character placement starts with template fitting** (A.2), not with a learned model.
2. **The rig asset library may be seeded from CC0 content** (A.3), which also answers the open
   decision about mocap-compatible skeletons.
3. **Add "Test with Animation"** to the rig builder (A.3).
4. **Add a sweep check** to the validator (A.8).
5. **Mechanical controls are 0 to 1 sliders** (A.8).
6. **Learned features become a clear, separate track.** The earlier recommendation was "research
   only". It can now be sharper: there *are* usable open models for rigging (UniRig) and, with terms
   still to read, for humanoid tweening (MotionBricks). None should be built in. Each can be an
   opt-in extension that plugs into a slot the core addons provide:
   - rigging addon: a "skeleton suggestion" slot;
   - animation addon: an "in-between source" slot.
7. **The rule for any learned model** before it is even offered as an extension: code licence, model
   licence and training data terms all read and compatible with commercial use; works without one
   vendor's hardware, or says clearly that it does not; download size stated up front.

---

## Part B. The asset library as the rigging system

The question: could rigging simply *be* dragging assets from the asset library, like the existing
asset wizards, with smart mesh blending, so that what you build is already rigged?

**Yes, and Bforartists already has two of the three pieces.**

### B.1 What exists today

- **The asset wizard system** in `bfa_default_library`: drop an asset, and an "Open Asset Wizard"
  button offers its settings. Handlers are registered per asset type.
- **Mesh Blend by Proximity**, also in `bfa_default_library`: a geometry nodes setup with its own
  operator that blends one mesh smoothly into its neighbours.
- **Asset shelf drag and click actions**, used by the Pose Library.

### B.2 Three ways to use them, from simple to ambitious

**Level 1: rig parts are library assets.**
Rig parts live in the BFA default library next to the smart primitives, appear in the asset shelf,
and each has an asset wizard for its options (finger count, IK or FK, detail level). This is the
rigging document's plan, using the wizard system that already exists instead of a new one.

**Level 2: character parts that arrive rigged.**
A library of *body* parts: torso, head, arm, leg, hand, tail, wing. Each asset carries its mesh, its
rig part and its skin weights together. The artist drags a torso into the scene, drags an arm onto
its shoulder socket, and:

- the meshes **blend** at the join (Mesh Blend by Proximity);
- the rig parts **socket** together;
- the weights are already there.

The result is a character kit: build a creature from parts and it is rigged the moment it is assembled.
This is the strongest form of "drag, drop, done" and fits the puppetry vision well. It pairs with the
character assets in the rigging document (cube, sphere, biped, quadruped, heroic and so on), which
would become kits instead of fixed meshes.

**Level 3: your own mesh, rigged by dropping.**
For a model the artist made or imported: drop a full rig on it and it fits itself (template fitting,
Part A.2), or drop parts one by one.

**Example: a creature from a kit (Level 2).**

1. 📦 Drag a torso from the shelf into the scene.
2. 🧲 Drag an arm near its shoulder. The socket lights up, the arm snaps on, the meshes blend at the join.
3. Do the same for legs, a head and a tail. Drag a blend handle to make a join softer or sharper.
4. 🖐️ Grab the hand and pull. The creature already poses, because every part arrived with its rig and weights.

No Edit Mode, no Weight Paint, no Build button.

### B.3 Everything in the 3D View

To keep this gesture and gizmo based:

- **Sockets are visible gizmos**: small rings on the model that light up when a compatible part is dragged near.
- **Part options are gizmos where possible**: drag a handle to lengthen a limb, drag a ring to set
  finger spread, click a dot to add or remove a finger. The asset wizard panel holds the same options
  for those who prefer a panel.
- **Blend width is a gizmo** at each join.
- **Build and Test with Animation are buttons in the viewport**, at the edge of the view, in the
  style of the existing navigation gizmos.
- **Nothing requires leaving the 3D View.** The sidebar tab mirrors the options but is never needed.

### B.4 Open points

- **Blending and skinning order.** Mesh Blend by Proximity is a live modifier. A character made of
  blended parts must still deform correctly at the joins. Either the blend is applied when the rig is
  built and weights are smoothed across the seam, or the blend stays live and is proven to work after
  the armature. This needs a prototype before Level 2 is promised.
- **No leftovers.** A kit character must end up as ordinary meshes and an ordinary armature, per the
  principles in the vision.
- **Content cost.** Level 2 is a content project as much as a code project. CC0 sources (Part A.3)
  help with rigs and animations, not with blendable body parts.
- **Ownership.** The asset wizard system belongs to `bfa_default_library`. The rigging addon should
  register its handlers there, not copy the system.

### B.5 Recommendation

Build Level 1 as planned, on the existing wizard system. Prototype Level 2 with two parts (a torso
and an arm) to settle the blending question. If it works, Level 2 becomes the headline feature of
the rigging addon, because nothing else on the list delivers "it is rigged the moment you assemble it".

---

## Part C. Live puppetry: perform it, do not key it

The question: webcam puppetry out of the box, a phone as a controller, simple and easy animation by performing.

### C.1 The idea

Keyframe animation asks for one pose at a time. Puppetry asks for a **performance**: press record,
move, and the character moves with you. Short takes, layered one over another: first the body, then
the head, then the hands. It is the fastest way for a non-animator to get lively motion, and it is
the purest form of the vision.

One design covers every device:

- **Inputs** are streams of numbers: a mouse position, a face shape, a tilt, a stick.
- **A mapping** connects each stream to something on the rig. With the rig description, mappings can
  be presets: "head follows my head", "this stick drives the tail".
- **Record** writes the result as ordinary keyframes, with a smoothing step, onto the rig's normal
  controls. Layered takes use Bforartists' native layered actions.

Nothing live is left in the file. A recorded performance is plain animation that plays in Blender.

**Three performances:**

| Who | Setup | The takes |
|---|---|---|
| 📺 **A teacher with a mascot** | Mouse and webcam. Preset "Head and Face" | Take 1: head follows the mouse while the voice track plays. Take 2: the webcam adds the face. Take 3: one hand, with the mouse |
| 🎞️ **A storyboard artist** making an animatic | Mouse only. Preset "Walk Along" | Drags the character through the set while the timeline plays. Feet stay planted through pins. Rough, fast, good enough to judge timing |
| 🐕 **A game animator** adding life to an idle | Phone as a controller. Preset "Tail and Ears" | Loops the idle. Each pass adds a layer: tail on one stick, ears on the other |

In all three the result is ordinary keyframes on layers, ready to be cleaned up by hand.

### C.2 Input devices, from cheapest to hardest

| Input | What it needs | Out of the box? | Notes |
|---|---|---|---|
| **Mouse or pen** | Nothing | **Yes** | Drag a part while the timeline plays and the motion is recorded. Builds on mesh posing and pins |
| **Keyboard triggers** | Nothing | **Yes** | Tap a key to fire a pose or a blink in time with playback |
| **Audio level** | Reading the sound track | Likely | Mouth flap from a voice track. The simplest lip sync there is |
| **Tracked video** (Clip Editor) | Nothing new | **Yes** | Already in the animation document, section 8 |
| **Webcam: face, hands, body** | A way to read the camera, plus a detection model | **No, needs work** | See C.3 |
| **Phone as controller** | A connection between phone and computer | **No, needs work** | See C.4 |
| **Game controller** | A way to read the controller | **No, needs work** | See C.5 |
| **VR controllers** | A headset | Partly | The bundled VR add-on already reads controller positions. Two hands in space is real two-handed puppetry |

The first three rows need no hardware, no downloads and no core changes. They are where puppetry
should start, because every user has a mouse.

### C.3 Webcam

What is needed, and what Bforartists has:

1. **Reading the camera.** Bforartists has no webcam input: a search of the source found none, and
   the bundled Python has no camera library. This needs either core work or an added library.
2. **Finding the face, hands or body.** This needs a trained detection model. Google's MediaPipe is
   the usual choice: it finds face landmarks and a set of standard face shapes, hand joints and body
   joints, and it runs on ordinary computers without a graphics card. Its code is Apache 2.0.
   The licences of its individual model files were not checked.
3. **Mapping to the rig.** Face shapes map to shape keys or face controls. Hand and body joints go
   through the full body solver. A single camera sees a flat picture, so depth is a guess: faces and
   hands work well, full bodies less so.

"Out of the box" is the hard part. Shipping a camera library and a model inside Bforartists adds
size and a new kind of dependency. The realistic shape is an **official opt-in extension**, one
click to install, that plugs into the puppetry inputs. Face first, since it gives the most for the least.

Privacy must be designed in: the camera is only on while a visible record or preview button is
active, an indicator shows it, and no picture leaves the computer.

### C.4 Phone as a controller

A phone has tilt sensors, a touch screen, and on many models a face-tracking camera. Three routes:

1. **A web page served by Bforartists.** The addon runs a small local server, shows a QR code, and
   the phone opens a page with virtual sticks, sliders and tilt. Nothing to install on the phone.
   Catch: phone browsers only allow tilt sensors on secure connections, which is awkward on a home
   network. Touch controls work without that.
2. **Existing face-capture apps.** Several phone apps already stream face shapes over the local
   network in a common format. Bforartists would only need to listen. This gives high-quality face
   capture with no detection model on our side, for users who have such a phone.
3. **Our own phone app.** Most work, and an app to maintain in two stores. Not recommended.

Any of these opens a network connection on the local network. It must be off by default, switched on
by an obvious button, and limited to the local network.

### C.5 Game controllers

Sticks and triggers are excellent puppet controls: two sticks drive a head and a body, triggers drive
a jaw. Bforartists does not read game controllers outside VR. Adding it needs a small core change or
an added library. A modest, well-contained piece of work, and useful beyond puppetry.

### C.6 Making it simple

- **Puppet presets.** Pick "Head and Face", "Two Hands", "Walk Along", "Tail and Ears". Each preset
  wires inputs to the rig through the rig description, so there is nothing to set up.
- **One Record button in the viewport**, with a count-in.
- **Takes.** Each recording is a take. Keep, redo, or layer another on top.
- **Smoothing slider** after recording, and **Reduce Keys** to make the result editable.
- **Loop recording**: play a short range on repeat and add a layer each pass. This is how puppeteers
  and musicians build up a performance.
- **Works with pins and physics.** Feet stay planted and tails follow through while you perform the body.

### C.7 Recommendation

1. **Add live recording with the mouse to the animation addon** as part of Phase 2, straight after
   mesh posing. It costs little once mesh posing and pins exist, needs no hardware, and makes the
   puppetry vision real for every user.
2. **Design the input side as a small, open "puppet input" slot**, so webcam, phone and controller
   support can be added as extensions without touching the core addon.
3. **Listen for existing face-capture apps** as the first hardware step: the least work for the best result.
4. **Webcam face capture as an official opt-in extension** next, once the camera and model questions are answered.
5. **Game controller support** when someone can do the core work.
6. **Decide separately** whether live puppetry justifies a small core feature for device input in
   general (camera and controllers), since several of these depend on it.

---

## Part D. Decisions

Answered by the maintainer on 24 November 2026. The full record and the resulting tier plan are in
`anim-rig-06-campaign-2027.md`.

| Question | Answer |
|---|---|
| CC0 rigs and animations as seed content | Yes, opt-in and library based. Clips must first become real drag-and-drop assets: see `anim-rig-05-animation-clip-library.md` |
| Character kits | Later, after the rigging kit is solid. Tier 5 |
| Learned features as opt-in extensions | Yes, through Coworker or a similar optional-download system. Tier 6, and section 5 of the campaign plan |
| Mouse puppetry | Yes, later, with a phone web page. Tier 6 |
| Device input in the core | Webcam and phone first. Controllers through the VR system. All after viewport posing, pose assist and tweening |

The questions as first asked:

1. **Adopt mesh2motion's CC0 rigs and animations** as seed content, after inspecting quality?
2. **Character kits (Part B, Level 2)**: prototype now, or after the first rigging release?
3. **Learned features as opt-in extensions with core "slots"**: agree the approach and the licence rule in A.9?
4. **Live puppetry**: confirm mouse recording as part of Phase 2?
5. **Device input in the core** (camera, game controllers): in scope or not?

## Sources

- Baran and Popović 2007: https://www.cs.toronto.edu/~jacobson/seminar/baran-and-popovic-2007.pdf (not readable here)
- RigNet: https://arxiv.org/abs/2005.00559 and https://github.com/zhan-xu/RigNet
- UniRig: https://zjp-shadow.github.io/works/UniRig/ and https://github.com/VAST-AI-Research/UniRig
- SkinTokens: https://github.com/VAST-AI-Research/SkinTokens
- UniMate: https://github.com/Friedrich-M/UniMate
- AnyMachine: https://github.com/apekshik/anymachine
- MotionBricks: https://nvlabs.github.io/motionbricks/ and https://github.com/NVlabs/motionbricks
- mesh2motion: https://github.com/scottpetrovic/mesh2motion-app/
- MediaPipe: https://github.com/google-ai-edge/mediapipe
