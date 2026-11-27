# Animation and Rigging Campaign 2027: Tiers and Phases

Draft 6, 2026-11-25. Status: proposal. Sizes and dates are estimates made without measuring the work.

This is the build plan for the animation and rigging work. It turns the "shopping list" in the other
documents into tiers that can be built, tested, documented and released one at a time.

- Vision and principles: `anim-rig-01-vision-and-consolidation.md`
- Rigging addon: `anim-rig-02-rigging-addon.md`
- Animation addon: `anim-rig-03-animation-addon.md`
- Research, asset library, puppetry: `anim-rig-04-research-and-puppetry.md`
- Animation clips in the asset library: `anim-rig-05-animation-clip-library.md`

## At a glance

> 🎭 **One story for 2027: animate by touching, rig by dragging.**

| Tier | Name | The artist can now... |
|---|---|---|
| 0 🧱 | Foundations | (nothing yet: design and prototypes) |
| 1 🎞️ | Clips, Motion View and Full Body Posing | drop a walk on a rig you already have, see ghosts and arcs, pin the feet and pull a hand |
| 2 🦴 | Rigging Kit | rig a biped in five minutes by dragging parts |
| 3 🖐️ | Puppet Posing | pose by grabbing the mesh, with no controls showing |
| 4 ✨ | Performance, Pose Assist and Tweening | perform a take with mouse or webcam, get a jump from two poses |
| 5 🐙 | Creatures, Machines and Character Kits | rig a spider or an excavator, assemble a kit character |
| 6 🎭 | More Puppetry Inputs and Optional Intelligence | perform with a phone or controller, use learned helpers |

When each is built, counted in quarters from the start. **The start is in 2027, after the asset and
product milestones that come first.** Releases follow about a quarter later, see section 6.

```
                      Start      +1      +2      +3      +4      +5     Later
T0 Foundations        [=====]
T1 Clips, Motion, Full Body    [=====]
T2 Rigging Kit                         [=====]
T3 Puppet Posing                               [=====]
T4 Perform, Assist, Tween                              [=====]
T5 Creatures and Kits                                  [.............]
T6 More Puppetry Inputs                                        [.............]
```

Each tier goes through six steps: 📝 design, 🔨 build, 🧪 tests, 📖 documentation, 🧑‍🎨 beta, 📣 release.

## 1. ✅ Decisions recorded

From the maintainer, 24 November 2026.

| Question | Decision |
|---|---|
| Use open CC0 rigs and animations? | Yes, as an opt-in library. Clips must become real assets that can be dragged onto rigs and into the NLA. Own document: `anim-rig-05` |
| Character kits (body parts that arrive rigged)? | Later. First the rigging kit must be well integrated, easy, gizmo heavy, drag and drop, and foolproof. Characters are then built with it |
| Learned (AI) features? | Opt-in only, through Coworker or a similar system of optional downloads, so Bforartists ships light |
| Mouse puppetry and a phone web app? | Yes. Mouse recording in Tier 4 (updated 25 November 2026). Phone web app later, Tier 6 |
| Camera and controllers? | Webcam recording in Tier 4 (updated 25 November 2026). Webcam and phone first, because everyone has them. Controllers through the simple VR system. VR control without a headset would be welcome, later |
| Modernise the NLA | A core feature: gestures and gizmos on the strips, built natively in C++ (26 November 2026). In Tier 1, where clips arrive |
| Self-contained rigs | No script in the blend file. Switches are bone properties, buttons are generic Bforartists operators reading the rig description, and all keys sit on one armature (25 November 2026). Vision document, section 4.2.1 |
| Order of the first two tiers | **Animation first, then rigging** (25 November 2026, replaces "the rigging kit comes first"). Tier 1 makes posing and animation fun on the rigs artists already have. Tier 2 then builds rigs. This is the best early win for an artist |
| Full body IK with pins | First, in Tier 1 (25 November 2026). It is what makes posing fun |
| Order | Viewport posing comes before all puppetry: selection, manipulation, puppet-like posing (anchor and pull, smart collisions, physics), then pose assist, auto-pose and tweening |
| Timeframe | Starts in 2027, after asset and product milestones (updated 25 November 2026). The later tiers run into 2028. On the roadmap, section 6 |
| Native or addon (25 November 2026) | Ideas that need speed or a place inside the editors are built into Bforartists natively in C++. The addons hold setup and guidance. See section 4 |
| Goal | Make animation fun, to the point and about storytelling, whoever or whatever the character is. A beginner can work like a capable technical director and animator |
| What we may add | Only handling and setup of what Blender already has. The result is compatible with vanilla Blender and renders there one to one |
| Playback speed and caches (25 November 2026) | Allowed, in the addons or in Bforartists itself. Speed counts as handling. The condition: without the speed-up the file falls back and still renders one to one in vanilla Blender |
| Ideas from existing add-ons | Document and use them. See `anim-rig-07-addon-survey.md` |

## 2. 🔁 How every tier is run

Each tier goes through the same six steps and is not called done until the last one.

| Step | What happens | Exit check |
|---|---|---|
| 📝 **1. Design** | A short design note in `_misc`, a tracker issue per feature, mock-ups of the gestures | Maintainer signs off the note |
| 🔨 **2. Build** | One branch per issue, compile to verify, PRs into `master` | Feature works on the test characters |
| 🧪 **3. Tests** | Automated tests for the maths and data. A written manual test script for the gestures. Run on OpenGL and Vulkan, on a light and a heavy character | Test script passes on both backends. **Vanilla check passes**: the demo file renders the same in vanilla Blender with the addons absent, including when a speed-up was in use. Playback speed is not compared |
| 📖 **4. Documentation** | Manual pages, tooltips reviewed, translations in `locale/po`, release notes | Pages written and linked from the addon |
| 🧑‍🎨 **5. Beta** | Opt-in in a development build. A small group of animators and riggers try it on real work and report | Blocking reports fixed |
| 📣 **6. Release and publicity** | Ships in a Bforartists release. Demo file, a short video, a news post, social posts | Published |

Rules that hold across all tiers:

- **Opt-in until it has passed a beta** with artists.
- **Handling and setup only.** Everything added either builds native Blender data or helps the
  artist work it. Files open and render one to one in vanilla Blender with the addons absent.
  Speed-ups such as caches are allowed when the file gives the same result without them, only
  slower. See the vision document, section 3.3.
- **White box.** The nine habits in the vision document, section 3.4, apply to every operator.
- **Light install.** Anything large or model-based is an optional download.
- **A tier may ship without the next one.** Each has to be useful by itself.
- **Four levels in every tier.** Each feature ships with all four levels from the vision document,
  section 3.1, and the design note for the tier lists them.

| Tier | 🖐️ Touch | 🧩 Assemble | 🎛️ Tune | 🔬 Craft |
|---|---|---|---|---|
| 1 Clips, Motion View, Full Body Posing | Drag clips, drag path points, drag a bone with pins | Shelf of fitting clips, Ghosts and Paths toggles | Apply modes, ghost range, falloff | Plain actions and keys |
| 2 Rigging Kit | Drag parts, drag markers | Parts, sockets, Build Rig | Gizmos, asset wizard, Rebuild | Plain bones and weights |
| 3 Puppet Posing | Drag the mesh, click to pin | One Puppet tool, any rig | Stiffness, limits, correct a guessed part | Native controls stay usable |
| 4 Performance, Assist and Tweening | Perform a take, drag arcs and guides | Tween and Auto-pose buttons | Timing, overlap, contacts | Keys in the Graph Editor |
| 5 Creatures, Machines, Kits | Draw a stroke, drag kit parts | Full creature rigs, kits | Detail levels, blend width | Save your own parts |
| 6 More Puppetry Inputs | Perform with a phone or controller | Puppet presets | Smoothing, takes, layers | Reduce to keys and edit |

## 3. 🪜 The tiers

Seven tiers. The first column is the name to use in issues and release notes.

### 🧱 Tier 0. Foundations

*Design and prototypes. Little shipped code.*

- Agree the vision and principles.
- Design the **rig description**: the data on an armature that both addons share.
- Set the two addon folders, `bfa_rigging` and `bfa_animation`, with manifests, test setup and manual stubs.
- Build the **test characters**: cube, sphere, a light biped, a heavy biped, a quadruped, one machine.
- Prototypes, throwaway quality, to remove the biggest unknowns:
  1. Drop a rig part from the asset shelf and fit it inside a mesh.
  2. Highlight a mesh area and drag it to pose.
  3. Draw ghosts in the viewport on OpenGL and Vulkan.
  4. Build the same arm with our own recipe and with Rigify, and compare weight and speed.
- Reply on the three open PRs (see the three review documents).

From the survey of existing add-ons (`anim-rig-07`):

- A fifth prototype: the full body solver on the heavy biped, with a speed target. Run it on a Rigify rig through a guessed description, because Tier 1 ships before kit rigs exist.
- The highlight prototype is also tested in orthographic views and on subdivided meshes.
- The engine trial is three-way: our recipe, Rigify and CloudRig. A fourth measure beside weight and speed: can the result work with no script in the file (vision document, section 4.2.1).
- A sixth prototype: one arm with an IK and FK switch, a snap button and a parent switch, built with no script in the file. Opened in vanilla Blender with auto-run off, the switch must still work.
- Test the hidden-scene method for evaluating other frames. Onion skin is now planned as native C++ work, so this is a comparison and a possible interim version, not a replacement.
- Hands-on comparisons, a day each: SkinKit against native weights. The free Retarget and Bulletproof
  Retarget extensions, then RetargetKit, against BoneCraft's retargeter. Editable Motion Paths against the reduced Ghost Tool.

Interface work that needs neither addon, so it can ship before the campaign starts:

- **A tabbed Tool Shelf in the Dope Sheet, Graph Editor and NLA.** These editors have no Tool Shelf
  today, so common operators sit in header menus. Built natively in C++ (a new region per editor, a
  toggle in the View menu, the tabs on/off switch) with Python panels that mirror the header menus
  one to one: Select, Marker, Channel, Key, plus Strip and Tracks in the NLA. No new tools in the
  first version. Starts closed in short editors such as the Timeline. Files stay compatible: Blender
  drops a region it does not know when it reads a file. That round trip still needs a hands-on test.
  Later, `bfa_animation` puts its buttons here.
- **A transform box in the Graph Editor and Dope Sheet.** A box around the selected keys with
  handles to move, scale from any side and, in the Graph Editor, rotate. Built natively in C++ on the
  2D transform box the Image Editor and Sequencer preview already use. It gets a tool button in the
  new Tool Shelf, so scaling keys in time no longer needs a pivot and a hotkey. Nothing is stored in
  the file.

*For example:* a maintainer drops a prototype arm on the light biped and it lands inside the mesh, on OpenGL and on Vulkan.

**Done when:** the rig description is written down, the four prototypes have answers, and the engine decision is made.

### 🎞️ Tier 1. Clips, Motion View and Full Body Posing

*Animate before building. Posing and animation made fun on the rigs artists already have: Rigify, CloudRig, imported and hand-made rigs. The first release of the animation addon. Maintainer priority.*

- **Works on existing rigs.** No kit rig exists yet in this tier, so every tool reads a guessed rig description: Rigify from its own naming and properties, other rigs from bone names, hierarchy and weights. The artist corrects the guess once and it is saved on the rig.

- **Onion skin and motion paths**, with editable paths. Built natively in C++, with Ghost Tool (PR #7087) as the reference for behaviour.
- **Animation clips as assets**: animation shelf, drag onto rigs and objects, compatibility check, Create Animation Asset. See `anim-rig-05`.
- Native work: action drop targets in the 3D View and the NLA. Ripple and gap retiming as native Dope Sheet operators.
- **Test with Animation** in the rig builder, using stock clips.
- Opt-in starter library of CC0 rigs and clips, if the content passes inspection.

From the survey:

- Ghosts on keys only as the default. Ghosts of one part.
- Path editing with the standard move, rotate and scale keys and proportional editing. Shape and Timing locks.
- Rotation paths. Path coloured by speed or jitter. Paths for objects and cameras.
- One native pose cache for a frame range, shared by live paths and ghosts. Ghosts bent on the graphics card. (Motion sculpting, steps 1 and 2: `anim-rig-07`, T4.)
- Travel on drop: Full, In Place, None.
- **A modern NLA, with gestures and gizmos on the strips** (core feature, 26 November 2026). Clips
  land in the NLA, so the NLA has to be pleasant to touch. Built natively in C++:
  - Handles on each strip: drag an end to trim, drag the body to move it in time or to another track.
  - A stretch handle to change speed, and dragging past the end to repeat the clip.
  - Blend-in and blend-out handles on the strip corners, drawn as a visible ramp.
  - Overlap two strips to make a transition. Snapping to strip ends, markers and the playhead.
  - Slip: slide the action inside the strip without moving the strip.
  - Drop a clip from the asset shelf straight onto a track, with a preview of where it lands.
  - The same handle look and behaviour as the retiming handles and the transform box, and a button
    for each gesture in the new Tool Shelf.
  Every gizmo edits ordinary strip settings, so files stay plain Blender files. What the NLA already
  does by hotkey today, and what the Sequencer's strip handles can lend, still needs a code check.
- **Full body IK with pins** (moved here from Tier 3, 25 November 2026): click to pin any part, drag
  another, and the whole body follows. In this tier it is used on the bones and controls. Tier 3 adds
  grabbing the mesh on top of the same solver. Writes plain keys on the rig's own controls.
- **Retiming handles in the Dope Sheet and Timeline.** Drag over a frame range to get a bar with
  handles: the ends stretch or squash the keys inside, and the keys after the range ripple along or
  stay, by a checkbox. A middle handle slides the range. Built natively in C++ on the ripple and gap
  operators, and on the gizmo group Bforartists already has in the Dope Sheet. Writes plain keys.
- Batch import of clip folders through the rig description.

*For example:* a game developer drags Idle, Walk and Jump onto the new rig and watches the ghosts to check the stride.

**Done when:** a clip dragged from the library plays on a Rigify rig and on an imported game rig, ghosts show its motion on both graphics backends, and a pose with both feet pinned is made on the heavy biped at interactive speed.

### 🦴 Tier 2. Rigging Kit

*The first release of the rigging addon. It builds rigs the Tier 1 tools already know how to pose.*

- Writes the rig description on build, so the Tier 1 tools need no guessing on kit rigs.

- Rig parts as assets in the shelf: spine, arms with shoulder, legs with hips, feet, hands, two-joint and three-joint chains.
- **Drag and drop** onto the model, **sockets** that snap and light up, placement inside the mesh.
- **Gizmos** for markers, limb length and finger count. Mirror with one click.
- Build, Rebuild, guided automatic weights.
- Part options through the existing **asset wizard** system. A guide panel for new users.
- One colour scheme, one set of control shapes, one collection layout on every rig.
- Bipedal full rig. Light rigs: few or no drivers, four levels deep at most.
- Validator with a sweep check.
- Edit Mode helpers: Shapes Assignment, Objects to Bones.

From the survey:

- Build in three visible stages, with a report under Build Rig.
- Validator as a log with Fix buttons. Nothing is fixed silently.
- Guided weights by rule: clothes follow the body, chains own what hangs from them, small parts stay rigid, sides stay apart. Every vertex gets weights. Hand-painted areas are protected on Rebuild.
- Test Pose button: bend every joint and back.
- Rigid Bind for machines. Naming presets on build. Parts labelled "exports" or "Blender only".
- Exact placement helpers: joint at the centre of a selected loop, push to centre of volume, Edges to Bones.
- Make a control by posing: fist and finger curls from a native Action constraint.
- A rig version, with Update through Rebuild.

*For example:* a hobbyist with a finished character model and a game jam this weekend rigs it before lunch.

**Done when:** a new user rigs the light biped in under five minutes following only the guide panel, and the result passes the validator.

### 🖐️ Tier 3. Puppet Posing

*Touch the character. The heart of the animation addon.*

- **Select and pose on the mesh**: hover highlights the part, drag poses it.
- **Manipulation gizmos** for rotate, move and twist on the part, without grabbing controls.
- **Anchor and pull on the mesh**: the full body IK and pins from Tier 1, now driven by grabbing the mesh. The "two hands" way of posing.
- Matching (IK/FK, world, parent) and mirror pairs, contributed from Anim Assist.
- Works on kit rigs through the rig description, and on Rigify and imported rigs by guessing.

From the survey:

- Pose root: choose what the body hangs from while dragging.
- Pins to other parts and to props, with baked hand-offs.
- Posing modes: Even, Rope, Stretch.
- One mesh area, several controls. Corrected areas saved as paintable vertex groups.
- Temp Pivot. Snap and Bake over a range. Parent switching without a jump. Handles on bendy bones.
- **Proportional editing through time**: a pose change spreads to the frames around it, with a range and a falloff. Locks that last one gesture. Sculpt into a copy of the action. (Motion sculpting, steps 3 and 4.)

*For example:* an animator blocks a character sitting down at a table: feet pinned, hips pulled back, a hand pulled to the table edge.

**Done when:** an animator blocks a ten-pose sequence on the heavy biped without selecting a single control bone.

### ✨ Tier 4. Performance, Pose Assist and Tweening

*Perform it, and the computer helps. Rule-based and physics-based. The only model is the webcam detector, an optional download.*

- **Mouse puppetry** (moved here from Tier 6, 25 November 2026): record a performance while the timeline plays. Takes and layers. Loop recording. Reduce Keys after each take.
- **Webcam recording** (moved here from Tier 6): face first, then hands. Needs native camera input, and a detection model delivered as an optional download. Mouse recording works without it.

- **Pose assist**: joint limits, balance and centre of mass shown while posing.
- **Smart collisions**: parts stop at the floor and at the body instead of passing through.
- **Auto-pose**: move a few parts and the rest of the body settles into a natural pose.
- **Tweening**: arcs, planted contacts, timing guides, overlap. Previewed as ghosts, written as keys.
- **Physics suggestions**: ballistic arcs for jumps, follow-through for tails and loose parts.
- Temporary working spaces with bake back to plain keys.

From the survey:

- Anchors with scope (feet fixed, arms free), shown with Blender's own key types.
- Draw the travel path on the floor. Ground waypoints.
- A short history of tween proposals to flip between.
- Reduce Keys after every bake. Sculpt the path and reshape a section.
- Motion brush on the path. Knots over dense keys. Time spread and colour by speed for ghosts. (Motion sculpting, steps 5 to 7.)
- Clips with sliders (tempo, energy, mood), baked to plain actions.
- **Key sculpting in the Graph Editor.** Brush tools with a visible circle, radius and strength:
  Grab, Smooth, Flatten, Push and Relax, and Noise. Native C++, sharing the falloff and the Reduce
  Keys step with the motion brush in the viewport, so both editors sculpt the same way. Works on
  sparse keys. On dense keys it works through the knots.

*For example:* a crouch and a landing become a jump. A tail gets its follow-through suggested and baked.

**Done when:** two key poses of a jump produce an accepted in-between with a correct arc and planted feet, with no trip to the Graph Editor, and a user with only a mouse records a short gesturing take.

### 🐙 Tier 5. Creatures, Machines and Character Kits

*The rigging kit grows up. After the kit has proven itself.*

- Full rigs: quadruped, bird, lizard, fish, dinosaur, insect, arachnid.
- Animal parts: wings, tails, hind and fore legs, tentacle. Draw a stroke to make a part.
- Utility parts: piston, four-joint, curve and simulated chains. Mechanical controls as 0 to 1 sliders.
- Face presets in three detail levels. Shape-key faces.
- Fit a full rig into a mesh by template fitting. Map a rig from an existing model.
- **Character kits**: body-part assets that carry mesh, rig and weights, and blend together when dropped.
- Remaining Edit Mode helpers: Bounding Bone, Proxy Rig Maker.

From the survey:

- Shrink to centre lines, for creatures that match no template. Adopt a skeleton: select a chain, press Make Arm.
- Bendy parts for tails, spines and rubber-hose limbs. Simulated chain and secondary motion parts (cape, skirt, hair) set up on native cloth, with presets, baked.
- Face part that authors the 52 standard shape keys, then can be removed. Bones or shape keys from the same landmarks.
- Drivers by demonstration. Correctives by posing. A light bulge helper.
- Edit control shapes on the rig. Joint sharpness gizmo.
- Kits: live blended preview, combined on Build.

*For example:* an illustrator rigs a dragon for a book cover, and a product artist rigs an excavator arm with three sliders.

**Done when:** a six-legged creature and a machine with pistons are each built from parts alone, and a kit character is assembled and animated without opening Weight Paint.

### 🎭 Tier 6. More Puppetry Inputs and Optional Intelligence

*Perform it. Everything here is opt-in, and the model-based parts are optional downloads.*

- Mouse and webcam recording are now in Tier 4.
- **Phone as controller**: a small web page served on the local network, with sticks, sliders and tilt.
- **Markers to bones** from the Clip Editor, with bake to keys.
- **Controllers** through the existing VR system. VR control without a headset: investigate. It may
  not be possible, since the VR system normally needs a headset connected. Not checked.
- **Learned features through Coworker** (section 5): suggest a skeleton, learned in-betweens, find a clip by description.
- Lip sync, one system.

From the survey:

- Face capture connects to the standard shape keys with nothing to map. Mix takes by face region.
- Kimodo joins MotionBricks as a candidate for the learned in-between slot, after a licence check.

*For example:* a teacher records a mascot greeting in three takes: head, hand, face.

**Done when:** a user records a short talking, gesturing character with a phone as the controller.

### 🔖 Bookmarked for later

Ideas noted on 25 November 2026. Not designed, not placed in a tier, not decided.

- **Husk proxy mesh.** Cut the character's mesh into pieces by weight and parent each piece to its
  bone, with no deformation, as a fast stand-in for animating. This is likely what "Proxy Rig Maker"
  in Tier 5 means. It is a speed-up under the "speed is handling" rule: the real mesh stays in the
  file and renders. It could also serve the click targets for posing on the mesh, and the ghosts.
  To think about: where pieces are cut at a joint, how the stand-in is switched and kept up to date,
  one object or many.
- **Quick secondary motion.** Wiggle-bone style follow-through that stays stable, applied by a short
  wizard from assets, possibly built on Geometry Nodes working on bones. Tier 5 currently says native
  cloth, baked. To think about: what "stable" needs (same result on every playback, no drift after
  scrubbing), whether Geometry Nodes can read and write bones well enough today (not checked), and
  how it reaches plain keys so vanilla Blender renders the same.
- **Rigged character presets.** Ready characters, rigged and weighted, to drop in and animate.
  Close to the full rigs and character kits in Tier 5, and to the decision that characters come
  after the rigging kit. To think about: whether a few simple presets earlier would help testing and
  publicity, and that they are built with the kit so they prove it.

- **Pose sculpting.** A modal brush tool for Pose Mode, like the Grab brush in Sculpt Mode: drag on
  the character and every bone under the brush circle follows, fading out with the falloff. Further
  brushes could follow the same pattern: Smooth or Relax (even out a chain), Straighten, Twist, Reset
  towards rest. Close to posing on the mesh in Tier 3, which drags one part with the solver. The
  brush is the many-bones version and suits tails, spines, fingers, hair chains and tentacles. With
  the range and falloff through time from motion sculpting, the same brush edits several frames.
  To think about: brush on the bones or on the mesh surface, FK only or through the solver, how it
  treats control rigs through the rig description, and whether an Edit Mode version for fitting
  joints into a mesh is wanted too.

- **Synoptic control picker, possibly as a new editor.** A 2D view of the character's controls to
  click, for what has no mesh to click on: IK and FK switches, fingers, face, props, selection
  sets. The plan so far says posing on the mesh replaces the picker. A picker generated from the
  rig description, with no layout to author per rig, would complement it. A new editor type is
  possible: Bforartists already has one of its own (the Toolbar editor), and files stay loadable in
  Blender. To think about: a tear-off panel first and an editor only if it needs its own canvas with
  pan and zoom, what else a "rig editor" would hold (rig description, parts list, validator, part
  options), and how rigs without a description get a layout.

- **Rudimentary lip sync as kits.** The PR authors wanted lip sync engines; Tier 6 has "lip sync, one
  system" with no design. Three levels to think about, each ending in plain keys or shape keys:
  1. *Sound to jaw.* Loudness of the audio opens the mouth. Blender's own "Bake Sound to F-Curves"
     already does this, so a one-button setup on a face part or the curve mouth is cheap. Whether
     Geometry Nodes can read sound directly is not checked.
  2. *Script to mouth shapes.* Import an SRT or a typed line, turn words into phonemes with a
     pronunciation dictionary, and spread them over the subtitle's time span. Rough timing, good
     enough for puppets and stylised characters. Needs a dictionary per language, with a licence check.
  3. *Aligned phonemes.* A model lines the phonemes up with the audio. This is what Coworker is for:
     an optional download, writing the same plain keys as level 2.
  A small fixed set of mouth shapes as assets (about eight), so all three levels drive the same thing.
- **Four outside projects, looked at on 25 November 2026.** All are optional downloads at most
  (section 5), never bundled. Licences below come from READMEs and one news article, not from the
  licence files.
  - *RGB MoCap* (video to motion, runs locally, exports FBX, BVH or a Blender project). Use: a "bring
    in a capture" path for the clip library. We build the import, retarget and clean-up side, not the
    capture. Its pose models and body models have their own terms.
  - *IBMM* (Disney Research: in-betweens generated as Bézier curves from sparse control points, with
    ease in and out as an input). No code or weights found. Use: as the design target for Tier 4
    tweening. Output must be sparse, editable curves, never a key on every frame.
  - *HairDeck* (one image to hair cards plus spring-bone chains, Apache-2.0 per its README). Use:
    its chain output is a ready test case for the secondary motion wizard. Hair generation itself is
    outside this campaign.
  - *anymove* (one generated video to a creature animation, Apache-2.0 code, paid video service, a
    reader trained per creature). Use: watch only. Its own notes list foot sliding, failed
    eight-legged walks and about seven clips per usable move.

## 4. 👥 Who builds what

| Tier | Addon | Lead | Core C++ work | Contributor-friendly parts |
|---|---|---|---|---|
| 0 Foundations | Both | Maintainers | For the interface work only: Tool Shelf region and transform box in the animation editors | Prototypes, test characters |
| 1 Clips, Motion View, Full Body Posing | `bfa_animation` | Maintainers | **Yes**: the full body solver's inner loop if speed needs it, mesh onion skin, live and editable motion paths, action drop targets, NLA strip gizmos, ripple and gap retiming, retiming handles | Clip library, compatibility check, batch import |
| 2 Rigging Kit | `bfa_rigging` | Maintainers | **Yes**: part and socket highlight while dragging from the asset shelf. Tool Shelf width setting | Part recipes, mechanisms, validator (from BoneCraft) |
| 3 Puppet Posing | `bfa_animation` | Maintainers | **Yes**: highlight and picking on the mesh | Matching, mirror pairs (from Anim Assist) |
| 4 Performance, Assist and Tweening | `bfa_animation` | Maintainers | **Yes**: camera input, key sculpting brushes in the Graph Editor | Physics suggestions, proxy bake |
| 5 Creatures, Machines, Kits | `bfa_rigging`, `bfa_default_library` | Shared | None expected | Rig and part content, creature rigs |
| 6 Puppetry and Intelligence | `bfa_animation`, Coworker, extensions | Shared | None expected | Phone web page, input mappings |

**Native first where it counts** (maintainer, 25 November 2026). A feature goes into C++ when it has
to be fast on a heavy character or has to sit inside an editor: evaluating other frames, drawing in
the viewport, picking on the mesh, drop targets, menu operators. Everything else stays in the two
Python addons, which keeps them small. Native features still follow the handling and setup rule and
carry BFA marker comments, and each one adds to the weekly merge load.

"Maintainers" is whoever the Bforartists team assigns. This plan does not assume how many people that is.

## 5. 🤖 Coworker and optional downloads

Coworker (`Draise14/bfa_coworker`, GPL 3 or later) is a separate add-on that puts an assistant in
every editor. From its README, it already does two things this campaign needs:

- **One-click optional downloads**: it fetches a local model runner and model presets on request, with nothing bundled.
- **Tools the assistant can call**, with permissions, approvals and one undo step per turn.

Only the README was read for this plan, not the code.

**The rule:** not everyone wants AI. So the rigging and animation addons must be complete and useful
with Coworker absent, and must contain no models and no model code.

**The split:**

| | In the core addons | In Coworker or an optional download |
|---|---|---|
| Rig placement | Stroke, centre of mesh, template fitting | "Suggest a skeleton" from a learned model |
| In-betweens | Rule-based and physics-based tweening | Learned in-betweens |
| Finding clips | Browse, search by name and tag | Find by description |
| Capture | Tracked markers to bones | Markerless face, hand and body from a webcam |
| Setup help | Guide panel, tooltips, validator messages | "Rig this for me", "why does this elbow bend wrong?" |

**How they connect:** each core addon offers a small number of named slots, for example "skeleton
suggestion" and "in-between source". Anything can fill a slot: a built-in method, or a provider
registered by Coworker. If nothing extra is installed, the built-in method is used and no AI option
is shown at all.

**Coworker as a tool user:** the addons' operators are ordinary operators, so Coworker can drive
them: build a rig, run the validator, drop a clip, record a take. That costs the core addons nothing.

**Open point:** whether optional downloads should live in Coworker, or in a small shared "optional
components" service that Coworker and other features both use. The second keeps model-free downloads
(clip libraries, camera support) available to users who do not install Coworker.
*Recommendation: a shared service, with Coworker as one user of it.*

**The licence rule** for anything downloaded this way: code licence, model licence and training data
terms are all read and allow commercial use; hardware needs and download size are shown before the download.

## 6. 📅 Roadmap

A sketch to show the order and the overlap, not a commitment. It assumes the tiers are built one
after another, animation first, and each tier takes about one quarter from design to release. Whether that holds depends on
how many people work on it, which this plan does not know.

**The start is gated, not dated.** The campaign begins in 2027, once the asset and product
milestones ahead of it are done. Which milestones those are, and the quarter they free up, is for
the maintainer to fill in. Everything below counts from that start.

| When | Building | Releasing |
|---|---|---|
| Now | Nothing | Replies on the three PRs |
| Before the start | Asset and product milestones (not part of this plan) | |
| Start, in 2027 | Tier 0 | Design notes, tracker issues, call for contributors |
| Start + 1 quarter | Tier 1 | |
| Start + 2 quarters | Tier 2 | **Tier 1 Clips, Motion View and Full Body Posing** |
| Start + 3 quarters | Tier 3 | **Tier 2 Rigging Kit** |
| Start + 4 quarters | Tier 4, start of Tier 5 | **Tier 3 Puppet Posing** |
| Start + 5 quarters | Tier 5, start of Tier 6 | **Tier 4 Performance, Pose Assist and Tweening** |
| After that | Tier 6 | **Tier 5**, then **Tier 6** |

With a start in the first half of 2027, Tier 1 can release that year, and Tier 2 with an early start.
Tiers 3 and 4 follow into 2028. Building the first two tiers one after the other adds a quarter
compared with the earlier side-by-side plan. Contributors could start Tier 2 part recipes early to win some of it back. With a later start, 2027 delivers Tier 0 and the first builds only. More native C++
work also makes each tier longer than the addon-only version of this plan assumed. If something has
to give, Tier 5 and Tier 6 are the ones to move: Tiers 1 to 4 already deliver the promise of "animate by
touching, rig by dragging".

## 7. 📣 Publicity

One story for the year: **"Puppetry: animate by touching, rig by dragging."** Each release adds a chapter.

| Release | Headline | Demo |
|---|---|---|
| Tier 1 | "See your motion. Drag and drop animation. Pin and pull" | Clip library onto a Rigify rig, ghosts and path editing, a pose made with pinned feet |
| Tier 2 | "Rig a character in five minutes" | Uncut screen recording, mesh to posed character |
| Tier 3 | "Pose without controls" | Hands-on posing with every control hidden |
| Tier 4 | "Perform your animation. Two poses, one jump" | A mouse and webcam take, then a plain in-between beside a smart one |
| Tier 5 | "Rig anything" | A creature and a machine built from parts |
| Tier 6 | "Any controller" | A phone-driven performance, start to finish |

For each: a demo file users can open, a video under two minutes, manual pages live on release day,
a news post, and a short call for beta testers before it.

## 8. ⚠️ Risks to the campaign

- **Size.** This is the largest feature effort in the plan documents so far. Without more hands,
  hold the line at Tier 4.
- **The start depends on other milestones.** If they slip, this slips with them.
- **Guessing is now on the critical path.** Tier 1 ships before any kit rig exists, so full body posing and clip drops depend on reading rigs we did not build. If the guess is poor on common rigs, Tier 1 is not fun. The Tier 0 solver prototype is run on a Rigify rig for this reason.
- **Native work in Tiers 0 to 4** must be carried through the weekly Blender merges. More of
  the plan is native than before, so this risk is larger.
- **The solver in Tiers 3 and 4** is the hardest single piece. If it is not good enough, Tier 4 slips.
- **Content.** Rigs, parts, clips and demo characters all need an owner and a quality bar.
- **Blender overlap.** If Blender ships onion skin, on-mesh posing or full body posing, ours must
  adapt. Plain file results keep that painless for users.
- **Contributor fit.** The three PRs must be reshaped a great deal. The plan works without them, but slower.

## 9. ➡️ Next steps

1. Maintainer review of this plan and the tier order.
2. Post the replies on PRs #7086, #7087 and #7088.
3. Open a tracker issue per tier, and one for the rig description.
4. Add the campaign to the Bforartists roadmap, behind the asset and product milestones.
5. Start the Tier 0 prototypes when those milestones are done.
