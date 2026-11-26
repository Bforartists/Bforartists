# What Existing Add-ons Teach Us: A Survey

Draft 2, 2026-11-24. Status: the ideas in part 1 are accepted by the maintainer and folded into the
tier plan. Part 2 is new and for discussion.
Part of the animation and rigging plan. Read `anim-rig-01-vision-and-consolidation.md` first.

Thirty-two add-ons the maintainer rates were looked at for ideas that would improve our proposals
while keeping the tools **white box**. Part 1 (sections 2 to 10) covers twelve animation and posing
add-ons. Part 2 (sections 11 to 20) covers twenty rigging systems and free extensions, read against
the maintainer's rule that anything we add is **handling and setup** of what Blender already has.

**How they were checked.** Product pages, FAQs and, where they exist, manuals were read on
24 November 2026. Nothing was bought, installed or run, and no source code was read. Several pages
explain themselves only through animated pictures, which could not be read. Where that left a gap it
is marked **(not on the page)**. Prices and sales counts are as listed that day.

## At a glance

> 🔍 **The good ideas are already out there, one paid add-on at a time. Nobody has put them together,
> and several pay for their power by taking over the rig or the file.**

| Area | Add-on | The idea worth taking | The trap to avoid |
|---|---|---|---|
| 📌 Full body posing | FreeIK | Pin anything, grab anything, change what the body hangs from while posing | The rig is converted and needs the add-on's own keying |
| ✨ Tweening | Blaze Puppeteer | Mark key poses as anchors per body part, draw the walk path on the floor | Helper rigs in the file, a learned model, humanoids only |
| 👻 Ghosts and paths | Arc Buster, Animates Suite, Clean Graph | The path is a 3D control: sculpt it, lattice it, lock shape or timing | A suite of many small panels |
| 👆 Posing on the mesh | Skin Selection | One mesh area can reach several controls | Every area painted by hand |
| 🦴 Bones from a mesh | Lazy Bones | Shrink the mesh to its centre lines, turn those into bones | Fragile on untidy meshes |
| 🧩 Rig building | SimpleSkelly, Rig It Quick | Three visible stages. Rigid bind for machines. Adopt an existing skeleton | Humanoid only, heavy rigs |
| 🎨 Weights | SkinKit | Rules that know what clothes, chains and small parts are. A Test Pose button | None found |
| 🔁 Retargeting | RetargetKit | Check, report, restore. Refuse and say why | None found |
| 📦 Character kit | Ultimate Character Kit | Body parts as an asset library, with a live preview of the joined result | Unrigged, and the assets may not be redistributed |
| 🏗️ Rig systems | Auto-Rig Pro, BlenRig, CloudRig, Rigi-All | Controls made by posing. A log with fix buttons. A guide with pictures. Parts labelled for export | Panel-driven. A script stored in the file for the rig's interface |
| 🔧 Bone tools | EasyBones, B-Bone Gizmos, BBone Tools, Bone Aligner | A joint at the centre of a selected loop. Bendy bones shaped with handles | Hotkey-first |
| 🎚️ Drivers | Easy Driver, Driver Helper | Show two states, get the driver | None found |
| 🙂 Faces | Faceit | A temporary face rig that authors standard shape keys, then goes away | None found |
| 🧵 Flesh and cloth | Simply Cloth, X-Muscle | Presets and pins for Blender's own cloth, baked | A system of its own on top of the rig |
| 🎨 Weights | Voxel Heat Diffuse Skinning | Protect hand-painted areas when re-skinning. Push a joint to the centre of the volume | A closed binary that cannot be bundled |
| 🔁 Retargeting | Retarget, Bulletproof Retarget | "The one that moves is the source." Preview live, then bake | None found |
| 〰️ Paths | Editable Motion Paths | Edit motion with the same keys and falloff as editing a mesh | Hotkey-first |
| 🎞️ Clips | Moveset | Clips with sliders (tempo, energy, mood) that bake to plain actions | None found |

## 1. 🔲 What "white box" means here

A white box tool lets the artist see what it did, understand it, and change it by hand.
A black box tool gives a result that can only be accepted or thrown away.

White box is level 4 of the four levels (🔬 Craft) made into a rule for every tool. The survey
shows nine habits that make a tool white box. They are now in the vision document as section 3.4.

| # | Habit | Seen in | In our tools |
|---|---|---|---|
| 1 | **Visible stages.** Each stage can be inspected before the next | SimpleSkelly: guides, then skeleton, then controls | Markers, then bones, then controls and weights. Build Rig can stop after any stage |
| 2 | **A report under the button.** What was done, in plain words | RetargetKit | After Build Rig, Tween, Bake and Retarget: a short list of what changed and what to check |
| 3 | **Refuse and explain.** If it cannot work, stop, say why, change nothing | RetargetKit | Every operator checks first. Messages name the part and the fix |
| 4 | **One step back.** One undo, or a Restore button | SkinKit, RetargetKit | One undo step per gesture and per operator |
| 5 | **The source is never overwritten** | RetargetKit: a new action, the old one kept | Tween, bake and retarget write to a new action or layer |
| 6 | **Bakes are reduced to editable keys** | Blaze Puppeteer "Unbaking" | A key on every frame is a black box. Every bake offers Reduce Keys |
| 7 | **Guesses are stored as ordinary data the artist can edit** | Skin Selection: vertex groups | Mesh areas as vertex groups, rig parts as bone collections, anchors as key types |
| 8 | **The rig is never converted** | FreeIK, the counter-example | Solvers are tools. The rig stays as it was |
| 9 | **Honest scope.** Known limits are written down with numbers | SkinKit, RetargetKit | A "Known limits" part on every manual page |

## 2. 📌 FreeIK: two-handed posing

*$29, listed as GPL, Blender 2.8 to 5.1, 400+ sales. The public repository holds a demo only.*

### What it does

- Any bone can be pinned. Pinned bones change colour.
- Drag any bone and the rest of the body follows.
- **Pose parent**: while posing, the artist can change which bone the body hangs from. This is
  separate from the **playback parent**, which decides how poses interpolate.
- Three posing modes: **Smooth**, **Rope** and **Stretch** (shown only in pictures; Stretch gives squash and stretch).
- The skeleton may contain loops, and the rig can split into parts during a shot.
- Objects are posed the same way as bones.
- Most functions are in one pie menu.

### How it does it, and what that costs

This is the "custom space" the maintainer mentioned. From its manual:

- **Make Links** adds a ball-socket constraint between every bone and its neighbour. The add-on's own solver then runs the rig.
- Animating needs a second add-on for a special keying set, because the bones gain an extra rotation channel.
- Bones must not be renamed afterwards.
- Whenever a pin changes, every bone must be keyed on that frame.
- The manual calls the rig "quite heavy" and advises staying under 100 constrained bones, about two characters. A rewrite of the solver in C is planned but not done.
- Blender's own constraints and limits are not taken into account yet.
- **Clear Links** turns it back into a plain armature, with a bake.

So the feel is excellent and the price is that the rig becomes a FreeIK rig.

### Ideas for our proposal

| Idea | Level | Where |
|---|---|---|
| **Pose root.** While dragging, choose what the body hangs from: grab the hand and the whole character swings from it. Working state only, never saved in the rig | 🖐️ | `anim-rig-03`, section 4 |
| **Posing modes as a tool option**: Even (the whole chain shares the bend), Rope (the chain trails behind the dragged end), Stretch | 🎛️ | section 4.4 |
| **Pins to other parts, not only to the world.** Hand pinned to hip, two hands on one sword. This is the white box form of "loops in the skeleton" | 🖐️ | section 4.1 |
| **Pinned parts change colour** on the mesh highlight | 🖐️ | section 3 |
| **Objects pose like bones.** The Puppet tool works on plain parented objects, which suits machines | 🧩 | section 3 |
| **Pin ranges.** FreeIK keys the pin itself. Ours cannot leave a live pin in the file, so a pin held across frames is a marked range that the tween bakes into keys | 🎛️ | section 7.2 |

**The lesson for the solver.** FreeIK's Python solver is its stated weak point. That supports doing
the solver prototype in Tier 0 instead of Tier 3, with a clear number to beat: one heavy biped at
interactive speed. If the prototype fails, the solver's inner loop goes to the core before Tier 3 starts.

**Where ours would differ.** No conversion, no extra channels, no special keying. The solver runs
only during the drag and writes ordinary rotations to the rig's own controls.

## 3. ✨ Blaze Puppeteer: anchors and paths

*$59 and up, listed as GPL, Blender 4.2 to 5.2, 100+ sales.*

### What it does

- The artist blocks key poses as usual, then **marks them as anchors**. An anchor has a scope: full
  body, hands, feet, or one hand or foot. Anchors show as badges on the timeline and as ghosts.
- **Waypoints**: click on the ground to say where the character is at a frame.
- **Dense path**: draw a stroke on the ground; it becomes an editable curve the character travels along.
- Press generate. In-betweens of up to ten seconds are produced.
- **History** per character keeps every result. **Variation**, **Loop**, **Extend** rework one.
- **Root extraction** moves the travel onto the root control. **Unbaking** reduces the result to fewer keys.

### How it does it, and what that costs

- It is built on a learned model (Kimodo, described as NVIDIA's motion model), run on the artist's computer. Download size and hardware needs are not stated.
- Setup creates two helper rigs in the file, which must not be edited.
- Humanoids only. No fingers. Its own documentation says feet can slide and contacts can miss.
- Some features send data to an online service and cost credits.

### Ideas for our proposal

These are interface ideas, and all work with rule-based tweening. None needs a model.

| Idea | Level | Where |
|---|---|---|
| **Anchors with scope.** For a tween, the artist says which key poses are fixed and for which parts: "the feet must hit this pose, the arms are free" | 🎛️ | `anim-rig-03`, section 7.2 |
| **Anchors as native key types.** Blender keys already have a type (Keyframe, Breakdown, Extreme, Hold, Generated) shown by shape and colour in the Dope Sheet. Use them: anchors are Extremes, keys written by the tween are Generated. No new data, and it reads at a glance (to verify in the current build) | 🔬 | section 7.2 |
| **Draw the travel path on the floor.** A stroke becomes the route of the hips or root between two poses | 🖐️ | sections 5.4 and 7.2 |
| **Ground waypoints**: click where the character should be at this frame | 🖐️ | section 7.2 |
| **A short history of proposals.** The last few tween results stay available as ghosts to flip between, before one is accepted | 🎛️ | section 7.2 |
| **Reduce Keys after every bake**, with three strengths | 🔬 | sections 4, 7 and 9 |
| **Travel onto the root control**, and its opposite, in place | 🎛️ | `anim-rig-05`, section 4.1 |
| **A five-chain mapping** (two legs, two arms, spine) is enough to describe a foreign humanoid rig | 🧩 | `anim-rig-01`, section 4.2 |

**For the optional slot.** Blaze Puppeteer shows that a learned in-between source can be delivered
inside Blender and run locally. Kimodo joins MotionBricks as a candidate for the opt-in "in-between
source" slot. Its licence was not checked.

## 4. 👻 Arc Buster, Animates Suite and Clean Graph: ghosts and paths

*Arc Buster $25, Animates Suite $65, Clean Graph $40. All listed as GPL.*

### What they do

**Arc Buster** treats the motion path as a control in the 3D View:

- Keys and their curve handles are grabbed directly on the path. Works for FK, IK, objects and cameras.
- **Preserve Arc** changes timing while the shape of the path stays. **Keep Timing** does the reverse.
- **Sculpt**: nudge, smooth and ripple the motion with a brush on the path.
- **Lattice**: a cage around a section of the path reshapes all its keys together.
- **Polish**: smooths keys, handles and spacing.
- Several paths can be edited at once. Changes in the Graph Editor show on the path live.
- **Onion skins**: on all frames, every few frames, keys only, or keys of one bone. Past and future colours, opacity, falloff, solid or wire. Ghosts can be limited to chosen bones.

**Animates Suite** adds tools around it: breakdown and overshoot sliders, key amplify, retimer, key
colours, **Lock to World**, **Temp Pivot**, and **Pick Up and Release** for props.

**Clean Graph** has eight panels of key and curve tools, with handles on the motion path, a tool to
place keys with a click, and a time cursor for offsetting and scaling keys. Its page gives little detail (not on the page).

How any of them build their ghosts, and how fast, is not stated.

### Ideas for our proposal

| Idea | Level | Where |
|---|---|---|
| **Ghosts on keys only.** For pose-to-pose work the key poses matter, not every frame. Likely the best default, and far cheaper to draw | 🧩 | `anim-rig-03`, section 5 |
| **Ghosts of one part.** Show only the arm being worked on | 🎛️ | section 5.5 |
| **Two locks on the path: Shape and Timing.** Lock the shape and retime along it, or lock the timing and reshape | 🎛️ | section 5.4 |
| **Sculpt the path** with a brush: smooth, nudge, relax spacing | 🖐️ | section 5.4 |
| **Reshape a section** with a cage or a falloff drag, so a run of keys moves together | 🖐️ | section 5.4 |
| **Paths for objects and cameras**, not only bones | 🧩 | section 5 |
| **Temp Pivot.** Put the gizmo pivot anywhere for one move: rotate the body about the planted hand | 🖐️ | section 3.2 |
| **Pick Up and Release.** Attach a hand to a prop for a range and bake the hand-off. This is the "pin to another part" idea from FreeIK, applied to props | 🧩 | section 9 |

**What to leave.** Breakdown sliders, retiming, key amplify and curve cleanup are Graph Editor and
Dope Sheet tools, and Bforartists already has native versions of several. They are not part of the
viewport-first plan. The two retiming entries already proposed for the native menus cover the gap.

## 5. 👆 Skin Selection: picking on the mesh

*$10, GPL, Blender 2.8 to 5.1, 700+ sales, about nine years old. By the author of Auto-Rig Pro.*

### What it does

- Click an area of the mesh to select the control behind it.
- **One area can hold up to three controls**: click for the first, Shift-click for the second, Alt-click for the third.
- Areas are stored as vertex groups with a prefix, made and painted by hand, and can be mirrored.
- It runs as a mode that is started and stopped, showing only the meshes.
- Stated limits: picking can be wrong in orthographic views, it works "generally fine" up to about 25,000 faces, and subdivision slows it.

### Ideas for our proposal

| Idea | Level | Where |
|---|---|---|
| **One area, several controls.** Drag for the main control, drag with a modifier for the second: the hand area gives IK hand, or FK wrist, or the fingers | 🖐️ | `anim-rig-03`, section 3.2 |
| **Areas are vertex groups when corrected.** Areas come from the weights automatically. When the artist corrects one, it is saved as a named vertex group that can be painted with the native tools. This answers the open point "a simple way to correct the guess" | 🔬 | section 3.4 |
| **No mode.** Ours is a tool in the Tool Shelf, so everything else keeps working | 🧩 | section 3 |
| **Test list from its limits**: orthographic views, subdivided meshes, and a face-count budget must be in the Tier 0 highlight prototype | | `anim-rig-06`, Tier 0 |

Skin Selection has done this for nine years with hand-painted areas. The step we add is that areas
are worked out automatically, and that dragging poses instead of only selecting.

## 6. 🦴 Lazy Bones: bones from a mesh

*$10, GPL, Blender 4.3 to 5.2, 700+ sales. Described by its author as experimental.*

### What it does

1. A simulation **shrinks the mesh** towards its centre lines. The artist watches and can pick the frame to keep.
2. Cleanup tools tidy the result.
3. The 3D cursor marks the root. Bones will point away from it.
4. The remaining **edges are turned into bones**.
5. A "Bone Doctor" menu repairs common problems. Then manual tweaks.

It fails on small models, holes and flipped normals, by its own FAQ. Weights are not covered.

### Ideas for our proposal

| Idea | Level | Where |
|---|---|---|
| **Shrink to centre lines** as a placement method for creatures that match no template. Classical, no model, and the artist sees it happen. A built-in entry for the "skeleton suggestion" slot | 🧩 | `anim-rig-02`, section 3.5 |
| **Edges to Bones.** Turn selected edges into a bone chain. A fifth Edit Mode helper, cheap, and useful by itself for cables, hair cards and tentacles | 🔬 | section 3.8 |
| **A root point sets bone direction**: bones point away from where the artist says the body starts | 🧩 | section 3.5 |
| **Check the mesh before placing**: scale, holes and normals, with a message that says what to fix | | section 3.5, validator |
| **Doctor fixes in the validator**: each reported problem gets a Fix button where a fix is safe | 🎛️ | section 6 |

## 7. 🧩 SimpleSkelly and Rig It Quick: rig building

*SimpleSkelly $10, Rig It Quick $15. Both GPL. Both new, with one rating each.*

### What they do

**SimpleSkelly** has three workflows:

- **Quick Rig**: choose biped or quadruped, place guides, then **Create Guides, Build Skeleton, Create Rig** as three steps. The skeleton can be inspected before controls are made. Controls come from Rigify.
- **Mecha Bind**: each selected mesh object is attached to its closest bone. For rigid, hard-surface models.
- **Custom Rig**: on an existing armature, the artist says which bones are the hips, spine, arms and legs, and controls are created for them.

**Rig It Quick** detects the body from the mesh, builds a humanoid skeleton and weights it. Its
useful details: **naming presets** on build (Rigify, Mixamo, Auto-Rig Pro, Unreal, Unity), landmarks
to adjust joints, a validator, and export presets. Humanoids only.

Neither page describes viewport gizmos. Their "guides" are our markers.

### Ideas for our proposal

| Idea | Level | Where |
|---|---|---|
| **Build in three visible stages**: markers, bones, controls and weights. Build Rig runs all three. A rigger can stop after any one | 🔬 | `anim-rig-02`, section 2 |
| **Rigid Bind.** Each selected object goes to its nearest bone, whole, with no weight blending. One button for machines, armour and props | 🧩 | section 3.7 |
| **Adopt a skeleton.** Take an imported or hand-made armature, tag its chains, and get kit controls and a rig description without rebuilding it. Makes foreign rigs first-class | 🧩 | sections 3.5 and 3.6 |
| **Naming presets on build.** The same biped can be built with Unreal, Mixamo or Unity bone names. This replaces shipping copies of vendor skeletons and removes most of that licence question | 🎛️ | section 3.2 |
| **Export check** in the validator: bones per vertex, naming, root bone, for game engines | 🎛️ | section 6 |

**What this confirms.** Both generate through Rigify or produce humanoids only. Drag and drop parts,
sockets, gizmos and creature rigs are not offered by either. That part of our plan is still open ground.

## 8. 🎨 SkinKit: weights

*$19, GPL, Blender 4.2 to 5.2, an extension, pure Python.*

### What it does

One **Auto Skin** button, built around rules about what things are:

- **Never fails.** Every vertex gets weights, on meshes with holes, loose parts or flipped normals.
- **Clothes follow the body**: they copy weights from the skin beneath them.
- **Chains** (hair, skirts, ears) weight only what hangs from them.
- **Small rigid parts** (buttons, buckles, eyes) move as one piece.
- **Split objects** stay glued at the seam. **Left and right** never bleed into each other.
- Helper, IK and end bones are skipped.
- Options: quality, bones per vertex (four by default), **Joint Sharpness**.
- **Test Pose** bends every joint to show the result. **Rest Pose** returns.
- **Clean Weights** limits, prunes and normalises.

The author publishes numbers: on one avatar, native automatic weights left 29,002 of 34,059 vertices
unweighted and SkinKit weighted all of them in ten seconds. On a clean Rigify character, both give
practically the same result. These are the author's figures and were not verified.

It writes ordinary vertex groups, in one undo step.

### Ideas for our proposal

SkinKit is the closest match to "better weights" in the maintainer's notes, and it is rule-based.

| Idea | Level | Where |
|---|---|---|
| **The rule list for guided weights.** Clothes follow body, chains own what hangs, small parts rigid, seams glued, sides apart. Our rig description already knows which part is which, so these rules cost us less | 🧩 | `anim-rig-02`, section 3.7 |
| **"Every vertex gets weights"** as the pass mark for Tier 1 skinning | | `anim-rig-06`, Tier 1 |
| **Test Pose button.** Bend every joint through its range and back. This is the sweep check as something the artist presses and watches | 🖐️ | section 3.7, validator |
| **Joint sharpness as a gizmo**: a ring at each joint, dragged wider for a softer bend | 🎛️ | section 7 |
| **Skin Clothes to Body** as its own action, for clothing added after the rig is built | 🧩 | section 3.7 |
| **Game limits**: bones per vertex as a build option | 🎛️ | section 3.7 |

**An honest question for the plan.** SkinKit is GPL and solves a problem we planned to research.
Before writing our own method, a hands-on comparison on our test characters is worth a day. If it
holds up, approaching its author is cheaper than building a rival.

## 9. 🔁 RetargetKit: retargeting

*$10, GPL, Blender 4.2 and newer, 10+ sales, three months old.*

### What it does

- Recognises eleven rig families and maps them **through one middle skeleton**.
- Mapping is shown as rows with dropdowns of bone names. **Auto-Map**, **Mirror Mapping**, **Check Mapping**, presets.
- **Line Up Rest Poses**: a T-pose source onto an A-pose target is handled automatically.
- Floor placement, optional **Hold Planted Feet**, root motion onto a named root bone.
- **All Actions** retargets a whole library in one go.
- The result is a new, plain action. The source is untouched. **Restore Target** undoes it.
- A **report** under the button says what was lined up, what was held, and how far the feet drifted.
- If the rigs are in a state it cannot handle, it stops, says why, and changes nothing.
- Its page lists its own limits with measurements, such as foot drift on rigs of different proportions.

### Ideas for our proposal

| Idea | Level | Where |
|---|---|---|
| **Our rig description is the middle skeleton.** Part names (arm, leg, spine) are what both sides map to. Kit rigs then need no mapping at all | 🧩 | `anim-rig-01`, section 4.2 |
| **Retarget on drop** becomes practical: a clip from another rig family is mapped through the description when dropped | 🖐️ | `anim-rig-05`, section 4.3 |
| **Check, report, restore** as the standard shape of every large operator, not only retargeting | 🔬 | section 1 above |
| **Line up rest poses** automatically, never as a manual step | 🧩 | `anim-rig-03`, section 9 |
| **All Actions** is the batch import that builds a clip library | 🧩 | `anim-rig-05`, section 4.5 |

As with SkinKit: it is GPL and small. BoneCraft's retargeter is broken on Blender 5. Comparing the
two before repairing BoneCraft's would be sensible.

## 10. 📦 Ultimate Character Kit: a kit of body parts

*$30, 200+ sales, Blender 4.2 to 5.2.*

### What it is

An asset library of base-mesh body parts for building characters, aimed at beginners. Its pages
describe installation only. What the parts are, how many, and how they are joined is **not on the
page**. One detail from its FAQ: a companion tool previews the combined character "without having to
combine everything". The parts appear to be unrigged (the maintainer's own description).

Its licence does not allow the assets to be redistributed, so nothing from it can be shipped.

### Ideas for our proposal

| Idea | Level | Where |
|---|---|---|
| **Preview the joined character live, combine on Build.** The parts stay separate and editable while assembling, with a live blended preview. Build Rig applies the blend and smooths weights across the seams. This answers the open point about blending and skinning order | 🎛️ | `anim-rig-04`, part B.4 |
| **The kit is an asset library first.** It needs no new system: a catalogue of parts in the Asset Browser, each with a rig part attached | 🧩 | part B.2 |
| **Our parts must be our own**, made for the kit or from CC0 sources | | part B.4 |

The difference we would add is the one the maintainer named: the same idea, but rigged.

---

# Part 2. Rigging systems and free extensions

## 11. 🧰 The lens for this part: handling and setup

The maintainer's rule, added to the vision document as section 3.3:

> Anything we add is **setup** or **handling** of what already exists in Blender. The finished
> character is plain Blender data. It opens in vanilla Blender and renders the same, one to one.

| | What it is | Examples | In the file afterwards |
|---|---|---|---|
| 🏗️ **Setup** | A tool that builds native data for you | Bones, constraints, a few drivers, weights, shape keys, native modifiers, native cloth settings, actions | Only the native data |
| 🖐️ **Handling** | A tool for working that data with your hands | Posing on the mesh, pins, ghosts, paths, gizmos, snapping | Nothing. At most keyframes |
| ⚡ **Speed-up** (added 25 November 2026) | Something that makes playback faster. It counts as handling | A cache of the evaluated pose or mesh, a light stand-in while playing, faster evaluation in Bforartists | Allowed if the file falls back without it and gives the same result, only slower |
| 🚫 **Neither** | Something the character needs in order to give the right result | Our own solver that the pose depends on, our own modifier, a script the rig must run, helper rigs | Not allowed |

This sorts the twenty add-ons below quickly. The best of them are pure setup (Simply Cloth, Easy
Driver, Faceit after baking) or pure handling (B-Bone Gizmos, Editable Motion Paths). The ones to be
careful with put something of their own between the artist and the render.

None of the pages read states plainly whether its results work in vanilla Blender without the
add-on, except CloudRig, Editable Motion Paths and one Rigi-All tool. Where this document says
"native", that is from the page's description, not a test.

## 12. 🏗️ Auto-Rig Pro and BlenRig: complete rig systems

*Auto-Rig Pro: $50 full, $25 lite, 71,500+ sales, 449 ratings. BlenRig: free, GPL, 800+ sales on the store.*

### What they do

**Auto-Rig Pro** is the market leader, by the same author as Skin Selection.

- **Smart** places the bones of a humanoid automatically. The result stays editable.
- **Limbs can be duplicated or removed**, to rig spiders and centaurs. Fingers, toes, ears, tail, wings, spline and three-bone limbs.
- Reference bones are edited, then the rig follows.
- **Control shapes are edited on the rig**, with automatic mirroring.
- IK-FK snap that works with auto-keying. A parent switcher for hands and feet.
- Skinning built on the native heat method, with meshes split into their parts and made solid first.
- A remapper for retargeting, and **export presets** for Unity, Unreal and Godot.
- Secondary controls come in three kinds, each labelled: twist (exports), additive (exports), **bendy bones ("Blender only")**.
- An **Update** button upgrades rigs made with older versions.

**BlenRig** is a film-quality biped rig.

- An **interactive guide** leads through every step with text and pictures, shown in the viewport. Its page says this "automates more than 50% of the labor".
- It ships **pre-weighted meshes**, so only hands and face need weight painting.
- It generates shape keys and their drivers.
- By its own FAQ: bipeds only, no extra limbs, no modular workflow, not for game engines by default.

### Ideas for our proposal

| Idea | Kind | Level | Where |
|---|---|---|---|
| **Every part says where it works**: "exports to game engines" or "Blender only". Shown on the part's thumbnail and in the report after Build | Setup | 🧩 | `anim-rig-02`, sections 3.1 and 3.2 |
| **Rig version and an Update button.** The rig description carries a version. Rebuild brings an older rig up to date | Setup | 🔬 | section 3.6 |
| **Edit control shapes on the rig**: drag a control's outline to resize or reshape it, mirrored automatically. This is the gesture form of the Shapes Assignment helper | Handling | 🖐️ | section 3.8 |
| **Parent switching**, set up with native Child Of constraints and switched without the pose jumping | Setup and handling | 🎛️ | `anim-rig-03`, section 9 |
| **A guide with a picture per step, that also frames the view** on the area the step is about | Handling | 🧩 | `anim-rig-02`, section 2 |
| **Pre-weighted reference bodies.** Our character assets carry good weights. A new character of similar build gets them by transfer, which is the Variation stage | Setup | 🧩 | sections 3.3 and 3.7 |

**What this confirms.** The best-selling rigger is modular and panel-driven. The most guided one is
not modular. Nobody combines modular, guided and gesture-first, which is our plan.

## 13. ☁️ CloudRig and Rigi-All: generators

*CloudRig: free, GPL, by Blender Studio, 120,000+ downloads. Rigi-All: free, GPL, 46,000+ downloads.*

### What they do

**CloudRig** is the Blender Studio's own rig generator, used on their films.

- A simple input armature (the metarig). Each bone is given a **component type** and options. Press **Generate**. Change an option and regenerate.
- About thirty component types, well beyond bodies: toon chains with bendy bones, feathers, lattices, aim, spheres, eyelids, curves with hooks, and a **physics chain that uses Blender's built-in cloth simulation**.
- **Actions as controls.** The rigger poses the rig (a blink, a fist), keys that pose as an action, and CloudRig wires it to a control with native Action constraints. **Corrective actions** switch on when two others are active together. Shape keys with matching names are driven too.
- A **Generation Log** lists problems found, many with a one-button fix. Its documentation says it "will NEVER automatically fix your mistakes", only detect and offer.
- IK/FK switches with **Snap and Bake** over a frame range.
- Copy a component to other bones. Symmetrize components.
- The rig's interface panel works without CloudRig installed, because **a script is stored in the file** and attached to the rig. Blender may ask permission to run it.

**Rigi-All** makes a Rigify rig from a model that already has a skeleton. Select a chain of bones and
press **Make Arms**, **Make Legs**, **Make Spine**, and so on. An option completes the other side.
Cleanup tools remove unused bones and vertex groups.

### Ideas for our proposal

| Idea | Kind | Level | Where |
|---|---|---|---|
| **Make a control by posing.** Pose a fist, a blink or a smile, press one button, and get a control that plays it, built from a native Action constraint. No drivers, and the pose stays an editable action. The cheapest route to hand and face controls | Setup | 🖐️ | `anim-rig-02`, section 4 |
| **Correctives the same way**: sculpt or pose the fix, and it is wired to switch on with the poses that need it | Setup | 🎛️ | section 4 |
| **The validator as a log with Fix buttons**, and the rule that nothing is ever fixed silently | Handling | 🎛️ | section 6 |
| **A simulated chain from native cloth**, replacing BoneCraft's own chain dynamics, which needs a script running during playback. Baked to keys when done | Setup | 🧩 | section 3.2, utility parts |
| **Select a chain, press "Make Arm"**, with the other side completed automatically. This is "Adopt a skeleton" from part 1, made concrete | Setup | 🧩 | sections 3.5 and 3.6 |
| **Snap and Bake over a range** for every IK/FK or parent switch | Handling | 🎛️ | `anim-rig-03`, section 4.4 |
| **Cleanup fixes**: remove unused bones and empty vertex groups | Setup | 🔬 | `anim-rig-02`, section 6 |

**A third candidate for the engine.** The open decision was "our own light recipes, or Rigify".
CloudRig belongs in that comparison. It is maintained by Blender Studio, GPL, built for "whatever
weird character or prop" a film needs, and it regenerates. Against it: its weight against the "four
levels deep" rule is unknown, and it is not bundled with Blender. The Tier 0 trial becomes a
three-way comparison: the same arm built with our recipe, with Rigify and with CloudRig.

**One thing to do differently.** CloudRig stores a script in the file for the rig's panel. Under the
handling and setup rule our rigs carry no script. The panel comes from the addon reading the rig
description. Without the addon the rig still poses and renders, and its switches are ordinary
properties anyone can find.

## 14. 🔧 Small bone tools

*All free, GPL, on the Blender Extensions platform.*

| Add-on | What it does |
|---|---|
| **EasyBones** | In mesh Edit Mode, select vertices and place a bone there: new bone at the selection centre, move a head or tail to it, extend, or span the selection end to end. No switching to the armature |
| **B-Bone Gizmos** | A Pose Mode tool. Bendy bones are shaped with gizmos "like bezier handles". A plain bone is turned into a bendy bone automatically when the tool is used |
| **BBone Tools** | Edit Mode helpers for bendy bones: set handles, convert to and from plain chains |
| **Bone Aligner** | Aligns bones of two armatures that share a name |
| **FreePicker** | A floating panel of hand-made buttons, each selecting a set of bones or objects |

### Ideas for our proposal

| Idea | Kind | Level | Where |
|---|---|---|---|
| **A joint at the centre of a selected loop.** Select an edge loop at the elbow and the marker goes to its centre. Exact placement for those who want it, in the mode they are already in | Setup | 🔬 | `anim-rig-02`, section 3.5 |
| **Bendy parts.** A tail, spine, tentacle or rubber-hose limb as one or two bendy bones instead of a long chain. Native, and it suits the "light rig" rule well. Labelled "Blender only" for export | Setup | 🧩 | section 3.2 |
| **Handles on bendy bones in the Puppet tool**: drag two handles to curve a tail | Handling | 🖐️ | `anim-rig-03`, section 3.2 |
| **Align to a template**: snap matching bones of a new rig to an existing one | Setup | 🔬 | `anim-rig-02`, section 3.5, level 4 |

Pickers stay out of the plan. Posing on the mesh does the same job with nothing to build.

## 15. 🎚️ Drivers and switching

*Easy Driver: free, 21,000+ downloads. Driver Helper: free. FK/IK Snapping Tools: free. All GPL on the platform.*

- **Easy Driver** makes a driver by demonstration. Move the bone to its start, press **Record Min Pose**. Move it to its end, press **Record Max Pose**. The add-on finds which axis changed and builds the driver. Targets can be several bones, shape keys, or any property. Works even when the bone is moved by IK.
- **Driver Helper** writes the expression that maps a range to 0 to 1, with easing.
- **FK/IK Snapping Tools** snaps one way or the other with one click, after the limb's bones are assigned once.

### Ideas for our proposal

| Idea | Kind | Level | Where |
|---|---|---|---|
| **Drivers by demonstration.** Where a driver cannot be avoided (shape-key faces, correctives, a machine's linked parts), the artist shows two states and the driver is built. The result is an ordinary driver | Setup | 🖐️ | `anim-rig-02`, sections 3.2 and 4 |
| **Easing on the mapping**, as a choice and not a typed formula | Setup | 🎛️ | section 4 |
| **Assign once, then one click**, for snapping on rigs we did not build. On kit rigs the rig description already knows | Handling | 🧩 | `anim-rig-03`, section 4.4 |

Together with "make a control by posing" (section 13), this gives two ways to wire things without
the Drivers editor: an action for poses, a demonstrated driver for values.

## 16. 🙂 Faceit: faces

*$78 to $99, GPL, 10,100+ sales, 81 ratings.*

### What it does

- The artist **places landmarks** on the face and picks which meshes are eyes, teeth, tongue.
- A face rig is fitted, and from it the **52 standard face shape keys** (the ARKit set) are generated, fitted to the character's own shape. Its page calls this "semi-automatic and non-destructive".
- The expressions can be corrected by posing or sculpting, then **baked into final shape keys**.
- One click adds a control rig for animating them.
- Face capture can be imported or recorded live, and mixed by face region.

### Ideas for our proposal

| Idea | Kind | Level | Where |
|---|---|---|---|
| **A temporary face rig that authors shape keys.** The face part is fitted with landmarks, produces the shapes, and can then be removed. What stays is shape keys, the most portable face data there is: vanilla Blender, every game engine | Setup | 🧩 | `anim-rig-02`, section 4 |
| **Use the standard 52 names.** Phone and webcam face capture output exactly this set. A face built this way connects to live capture with nothing to map | Setup | 🧩 | section 4, and Tier 6 |
| **Two face routes, one placement**: bones for film-style faces, shape keys for games and capture. Same landmarks | Setup | 🎛️ | section 4 |
| **Mix takes by face region**: brows from one take, mouth from another | Handling | 🎛️ | `anim-rig-04`, part C.6 |

## 17. 🧵 X-Muscle System and Simply Cloth: flesh and cloth

*X-Muscle: $40, GPL, 3,500+ sales. Simply Cloth: $36, MIT, 18,900+ sales, 187 ratings.*

### What they do

**Simply Cloth** describes itself as "a workflow helper" for cloth. It converts an object to a cloth
simulation with presets (silk, denim, cotton), manages pins as layers, helps with sewing, adds
wrinkles, and bakes. Its page does not say in so many words that it sets up Blender's own cloth, but
its settings read that way.

**X-Muscle** adds muscles between bones that flex, jiggle and push the skin, with automatic
attachment and weighting. It is a system of its own, with its own objects, cache and controllers.

### Ideas for our proposal

| Idea | Kind | Level | Where |
|---|---|---|---|
| **Simply Cloth is the model for a setup tool.** Presets by material name, pins by selecting an area, one Bake button. Nothing new is invented, the native feature is made approachable | Setup | 🧩 | The rule in section 11 |
| **Secondary motion as parts**: cape, skirt, hair strip, antenna. Each sets up native cloth or soft body with a named preset and pins from the rig description. Baked for final | Setup | 🧩 | `anim-rig-02`, section 3.2 |
| **A light "bulge" helper**: one stretch bone across a joint that keeps volume, for biceps and calves. Native constraints only | Setup | 🎛️ | section 3.2 |

A full muscle system is outside this plan. It conflicts with the "light, four levels deep" rule, and
it is a simulation product in its own right.

## 18. 🎨 Voxel Heat Diffuse Skinning: weights

*$30, 13,100+ sales, 77 ratings. Its Python is GPL. Its solver is a closed binary that is "NOT under GPL".*

### What it does

- Turns the mesh into a solid block of small cubes, then spreads heat from the bones through the
  solid. Works on meshes that are not watertight, where the native method fails.
- **Protect Selected Vertex Weight** keeps chosen areas as they are.
- A two-phase mode: native-style heat for some meshes, the solid method for others.
- A **Joint Alignment Tool**: place a joint in a flat view, then push it to the surface or to the centre of the volume with one click.
- By its own words the result "just gives you a good start point".

### Ideas for our proposal

| Idea | Kind | Level | Where |
|---|---|---|---|
| **Protect what was painted by hand.** Rebuild and re-skin never overwrite areas the artist corrected | Setup | 🎛️ | `anim-rig-02`, section 3.7 |
| **Choose the method per mesh**: body one way, armour and props rigid, clothes following the body | Setup | 🎛️ | section 3.7 |
| **Push to centre of volume** as a button on any marker. Our placement level 1, offered as a single action | Setup | 🖐️ | section 3.5 |

The solver cannot be bundled, because it is closed. SkinKit, in part 1, takes a similar approach in
plain Python under the GPL and remains the one to test first.

## 19. 🔁 Retarget and Bulletproof Retarget

*Both free, GPL, on the Blender Extensions platform, Blender 5 and newer. Retarget: 37,000+ downloads. Bulletproof: new, 144 downloads.*

### What they do

**Retarget** is a toolkit built on two older open projects. Presets for many rig families. It **binds**
the target to the source with constraints, so the result is seen live, then **bakes**. It also
converts rigs for Rigify, applies a pose as the rest pose, adds a root bone and transfers root motion.

**Bulletproof Retarget** aims at one click:

- Select both characters and press **Use Selected**. **The one that is moving is the source.**
- It recognises about 27 rig families and maps up to 58 joints with no lists to fill in.
- Root motion as three choices: **Full, In Place, None**. A Floor option.
- Rest poses are lined up automatically.
- It writes a new action, keeps the old one, restores the scene as it found it, and warns in a report where hands or feet could not land.

### Ideas for our proposal

| Idea | Kind | Level | Where |
|---|---|---|---|
| **"The one that moves is the source."** No source and target fields | Handling | 🧩 | `anim-rig-03`, section 9 |
| **Preview live, then bake.** Bind with native constraints to look, bake to keep, and the constraints are removed | Setup and handling | 🎛️ | section 9 |
| **Full, In Place, None** for travel, in the popup when a clip is dropped | Handling | 🎛️ | `anim-rig-05`, section 4.2 |
| **Apply a pose as the rest pose**, with the mesh following, as an Edit helper | Setup | 🔬 | `anim-rig-02`, section 3.8 |

**For the Tier 0 comparison.** Part 1 proposed testing the paid RetargetKit against BoneCraft's
broken retargeter. These two are free, GPL and already on the official platform, so they go first.
Retargeting may need no new code from us at all, only good integration with the rig description.

## 20. 〰️ Editable Motion Paths and Moveset

*Both free, GPL, on the Blender Extensions platform.*

### What they do

**Editable Motion Paths** (3,300+ downloads, Blender 4.4 and newer) is the closest thing found to
our own section on paths. Its line is "edit animation like a mesh".

- Keys are points, handles are curve handles. Click and drag, or use the same move, rotate and scale keys as everywhere else.
- **Blender's own proportional editing** gives the falloff.
- Four kinds of path: location, **rotation (the path of the bone's tip)**, scale, and a single value.
- A dot per frame, a speed graph that can be dragged, and a **sculpt tool** on the path: grab, smooth, pinch, slow, fast, even.
- Path **coloured by speed or by jitter**, onion-skin ghosts, centre of mass, snapshots.
- Heavy rigs are calculated **in the background, in a hidden scene that is removed afterwards**, nearest frames first.
- Its page says it "only writes ordinary keys and handles" and that files open fine without it. Its manual mentions a few custom properties and saved snapshots, so that claim needs a check.
- Its author states openly that they are an artist and that the code was written with an AI assistant.

**Moveset** (free tier: 55 clips) puts **procedural animations with sliders** on any humanoid: tempo,
energy, posture, mood. Pressing Bake turns each into a plain action. Animations made with it are
free to use commercially.

### Ideas for our proposal

| Idea | Kind | Level | Where |
|---|---|---|---|
| **Edit motion with the keys you already know.** Move, rotate, scale and proportional editing work on path points as they do on a mesh. Nothing new to learn, which is very much a Bforartists idea | Handling | 🖐️ | `anim-rig-03`, section 5.4 |
| **A rotation path**: the trail of the bone's tip, for FK arms and heads, where a location path shows nothing | Handling | 🧩 | section 5.4 |
| **Colour the path by speed or jitter**, so pops and stutters show at a glance | Handling | 🧩 | section 5 |
| **A hidden scene, removed afterwards, for evaluating other frames.** If this works as described, onion skin and paths can be filled without moving the playhead **and without core C++ work** | Handling | | section 5.2, and the open decision on core work |
| **Clips with sliders.** A walk asset with tempo, energy and mood, previewed live, baked to a plain action when dropped | Setup | 🎛️ | `anim-rig-05`, section 4 |

**Two things to check before Tier 2 is built.**

1. Editable Motion Paths against the reduced Ghost Tool, as the base for our motion view. It is free,
   GPL and already does much of what PR #7087 was asked to become. What it lacks for us is the
   point-and-click side: it is driven by hotkeys.
2. The hidden-scene method. It would settle open decision 1 in the vision document in favour of
   "no core work needed for onion skin".

# Part 3. Four talks from the Blender Conference 2026

Added 2026-11-25. Read from the automatic captions of the four recordings, not watched. The
captions garble names and some terms, and everything shown on screen without being said is missing.
Times and counts below are what the speakers said, not measurements.

| Talk | What it is | Biggest idea for us |
|---|---|---|
| T1 🧩 Rigify: Future Proof Rigging Concepts | A prototype of rigging in the 3D View with single clicks, on top of Rigify | Place **joints, not bones**, in guided steps, and let the tool work out the rolls |
| T2 ☁️ CloudRig: Rigging ALL THE THINGS! | A walk through CloudRig's way of working, by its developer at Blender Studio | **Live preview** of what Build will make, and a switch never makes the pose jump |
| T3 👄 The Quest for the Ultimate Stylized Mouth Rig | A cartoon mouth made of one curve and Geometry Nodes, used on a film in production | **Four points drive a whole mouth**, and a fast display mode for animators |
| T4 🗿 Motion Sculpting: A New Animation Paradigm | An alpha tool that edits a whole stretch of animation by grabbing the character, by a game animator and tool developer | **Proportional editing through time**: one drag changes the pose on the frames around it, with a falloff |

## T1. 🧩 Rigify: Future Proof Rigging Concepts

The speaker's starting point is ours almost word for word: by the time an animator has learned
heads, tails, rolls, constraints and collections, they have lost interest in animating. His question:
**can we rig with one button and a tablet?** The prototype is called "Rigify Smart UI".

What it does, as described:

- **Everything happens in the 3D View.** Tools in the toolbar, an asset shelf in the viewport, a list in the sidebar.
- **Single click only.** No double click, no keyboard. A long press opens a pie menu. A click in empty space means "next step".
- **Placements are points.** The artist places joints. Bones, rolls and chain directions are worked out from them.
- **Each part is placed in guided steps.** For an arm: click the shoulder and the wrist, slide where the elbow splits the line, turn a circle to set the bend direction (four fixed directions or free), then choose how the hand lies (three presets or free).
- **Clicks land inside the mesh.** A click finds the middle of the volume under the cursor, with no need to select the mesh. Fingers use surface placement with an adjustable depth.
- **Spines, tails and eyelids are a line with two handles** plus a slider for how many bones to split it into.
- **The tool keeps the artist inside a rig that will work.** A foot stays aligned, a leg chain stays on one plane. The rule can be broken on purpose.
- **Rig frames.** A frame is a page that holds placements. Frames nest, connect to each other and are **mirrored one by one**: mirror the fingers but not the arm, or one eye but not the face.
- **Assisted editing.** Re-run the guided steps of a part starting from where it was left. Free editing is also there.
- **Names from one label.** Type "index" and the bones become index 1, 2, 3.
- **The asset shelf holds single parts and assemblies** (a hand, a whole horse). Drag one in, then fix each frame. The speaker reports about six minutes for a horse.
- **It writes a normal Rigify metarig** and presses Generate. The artist can continue by hand from there, and positions can be read back.

One warning from the talk: he had to draw his own controls in the viewport, because Blender does not
offer what he needed. That is the same trap as the hand-drawn toolbar in PR #7086, and the reason
our native C++ route matters here.

### Ideas for our proposal

| Idea | Kind | Level | Where |
|---|---|---|---|
| **Joints, not bones.** Markers are points. Rolls and directions are derived, and never asked for | Setup | 🖐️ | `anim-rig-02`, markers |
| **Guided steps per part**, with "click empty space for next". The same steps can be re-run later from the current positions | Handling | 🖐️ | `anim-rig-02`, placement |
| **Bend direction as a dial**, and segment count as a slider on the part | Handling | 🖐️ | `anim-rig-02`, gizmos |
| **Mirror per group**, not per rig. A group is a part or a nest of parts | Setup | 🧩 | `anim-rig-02`, mirror |
| **Rails**: the tool holds a part in a shape that will build correctly, with a visible way to leave the rails | Handling | 🧩 | `anim-rig-02`, white box habits |
| **Assemblies in the shelf**: a hand or a whole creature is a saved group of parts | Setup | 🧩 | `anim-rig-02`, asset library |
| **One label names a chain** | Setup | 🧩 | `anim-rig-02`, naming presets |
| **Single click as the design test.** If a step cannot be done with one click or one drag, redesign it. This also makes the tools ready for tablets | Handling | 🖐️ | `anim-rig-01`, level 1 |
| **The placement layer is separate from the engine.** It only needs each part type to say what points it wants. The speaker says it should work over CloudRig too | Setup | 🎛️ | `anim-rig-02` section 5, engine decision |

## T2. ☁️ CloudRig: Rigging ALL THE THINGS!

The developer is clear about what CloudRig is **not**: it does not place bones and it does not help
with weights. It builds the controls. That is the reverse of T1, and the two together cover what
our rigging addon wants to be.

What the talk adds to section 13:

- **Live preview.** Assign a part type to a bone and the controls it will make are drawn at once, before Generate. Change "stretch segments" from 1 to 2 and the preview updates. The preview also shows where the pole target will land.
- **Rebuild often.** A chain rebuilds in about 80 milliseconds by his account, a human in a couple of seconds. Animation on the rig is kept.
- **One checkbox per behaviour.** "Hinge" makes a limb stop inheriting rotation. Each such switch arrives in the rig with a slider **and a button that flips it without moving the pose**, plus a bake over a range.
- **Parent switching as a list.** Add the possible parents, give each a display name, mark the default. The slider and the no-jump button are generated.
- **The log is opinionated and short.** It warns only about things the author feels strongly about, so it has no ignore list. Examples: a rig still named "Armature", bones named "Bone.001", and an IK chain whose bones do not lie on one plane. The last one has a Fix button that corrects positions and rolls, so IK and FK agree exactly.
- **It refuses and says why.** An IK part on a single bone stops the build with a plain message. Greyed-out menu entries explain why they are greyed out.
- **Good presets replace fiddling.** A set of bone colours and a library of control shapes with picture previews. Scaling a control shape is a separate action from scaling the bone.
- **Small repairs to everyday Blender:** duplicate and extrude number bones sensibly, parent and delete work without entering Edit Mode, symmetrize also flips the rig settings, an object can be parented to several bones at once through the native Armature constraint.
- **Not bundled on purpose.** As an extension it can ship a fix in days. Bundled, a fix waits for the next release.
- **Gaps he names:** no quadruped legs yet, no good face preset, and one maintainer.

Most of the talk is driven by hotkeys (Shift T, Ctrl R, P, X, Shift Alt S). For Bforartists each of
those needs a button first.

### Ideas for our proposal

| Idea | Kind | Level | Where |
|---|---|---|---|
| **Live preview before Build**: the controls a part will make are drawn while its options change | Handling | 🧩 | `anim-rig-02`, build |
| **No switch without a no-jump button.** Every generated switch (IK or FK, hinge, parent) comes with "switch and keep the pose" and a bake | Setup | 🧩 | `anim-rig-02` and `anim-rig-03`, matching |
| **Parent choices as a named list** on the part, with a default | Setup | 🎛️ | `anim-rig-02`, part options |
| **A straight-plane check for IK chains**, with a Fix button, so matching is exact | Setup | 🎛️ | `anim-rig-02`, validator |
| **Greyed-out entries say why** | Handling | 🧩 | `anim-rig-01`, white box habits |
| **A short, opinionated check list** in place of an ignore system | Setup | 🧩 | `anim-rig-02`, validator |
| **Control shape scale is its own gizmo**, apart from bone scale | Handling | 🎛️ | `anim-rig-02`, control shapes |
| **Everyday repairs as native fixes**: bone numbering on duplicate, parent and delete from Pose Mode, symmetrize that carries settings | Handling | 🔬 | Bforartists core, outside both addons |
| **Rebuild speed as a target**, measured per part and per full rig | Setup | 🎛️ | `anim-rig-06`, Tier 1 tests |

## T3. 👄 The Quest for the Ultimate Stylized Mouth Rig

A studio rigger wanted the flat "bean" mouth of 2D cartoons on a 3D head, without caring about the
head's topology. The system is in use on a film in production.

How it works, as described:

- **One curve object with four points** is the whole mouth control. The head mesh gets a Geometry Nodes modifier. Nothing else is needed.
- **The mouth shape is projected onto the head.** The hole is made by transparency in the shader, so the mesh is not cut.
- **The inside of the mouth** is that shape pushed inwards along a chosen bone.
- **An outer ring, the lips, covers the seam.** Its normals and texture coordinates are taken from the head, so it reads as one surface. In the speaker's words: just cover the ugly parts. He compares it to replacement mouths in stop motion.
- **Two display modes.** A fast one for animators in solid view, where the faces in the hole are simply deleted, and an accurate one for render.
- **Switches for the hard cases:** a closed mouth becomes a line, and a tube shape handles "ooh". Animators flip the switch on one frame.
- **Fixed topology** was chosen over rebuilding the mesh every frame, to keep everything stable downstream.
- The curve's control bones are made with CloudRig's curve part "in a few clicks".

Problems he lists: no rest pose, lips cannot roll or push out, the projection needs a dense mesh,
and hooks must sit first in the modifier stack. He wants an option for eight points.

It passes our rule as described: Geometry Nodes, a shader and a curve are all native, so the file
should render one to one in vanilla Blender. Not tested.

### Ideas for our proposal

| Idea | Kind | Level | Where |
|---|---|---|---|
| **A cartoon mouth part**: a node asset plus one curve with four control points, dropped on a head | Setup | 🧩 | `anim-rig-02`, face presets. `bfa_default_library` |
| **Few points, big shape** as the rule for face controls. Four by default, eight as an option | Setup | 🧩 | `anim-rig-02`, face presets |
| **Animator view and render view** on heavy parts: a fast approximate display while animating, the exact one for render. Same result at render | Handling | 🎛️ | `anim-rig-01` section 3.3, speed-ups |
| **Cover the seam.** For kit parts that meet (mouth and head, limb and body), a covering ring is cheaper and steadier than a perfect join | Setup | 🎛️ | `anim-rig-04`, character kits |
| **Shape switches keyed on one frame** for cases a single setup cannot reach (closed, tube) | Setup | 🎛️ | `anim-rig-02`, face presets |

## T4. 🗿 Motion Sculpting: A New Animation Paradigm

The most watched of the four. The speaker wants animation to feel like clay on a table, with one
difference: you can see time and go back. His stated goal is to animate **without ever opening the
Graph Editor**. The tool is an alpha, and he says so. It works best on animation that already exists.

His comparison is modelling. Sculpting did not win by making meshes simpler. It won by making them
dense and giving artists brushes. He treats animation the same way: a key on every frame is fine if
the tools work on what you see.

How it works, as described:

- **Two limits he sets himself: a plain skeleton, and forward kinematics only.** No control rig. Then the pose on any frame can be worked out from the animation curves alone, without asking Blender to evaluate the scene. That is what makes everything below instant.
- **A motion cache** of the frames around the playhead, built that way.
- **Live motion paths** for every selected bone, and **live onion skins** from the real mesh. The mesh is sent to the graphics card once and bent there by the cached bones. Corrective modifiers are not shown.
- **Pick on the mesh** through the skin weights. A double click takes the whole limb. A limb is a chain that ends where bones are disconnected, or one the artist marks.
- **One gesture, three steps.** A solver poses the current frame (rotate, or pull the chain like IK, with pole handles that appear by themselves). The change is then **spread to the frames before and after**, inside a range the artist sets with two flags, with a falloff shape. While dragging it is written to the cache. On release it is written to the curves.
- **Locks that last one gesture.** Lock the feet, drag the hips: the feet keep **their own animation**, they are not frozen to a spot. Rotation can be locked up or down the chain. Nothing is a rig state, so there is no IK or FK switch to manage.
- **A motion brush** on the path: grab and smooth, like a sculpt brush, over the frames under it.
- **A spline on top of dense keys.** Mark a few frames as knots, then shape the stretch between them as one curve, with "tension" handles that push motion towards either end.
- **Time spread** (he calls it a wormhole): ghosts and paths are shifted sideways on screen by their time. Motion that happens on the spot becomes a row of poses that can be read and grabbed.
- **Ghosts coloured by speed.** Sliders to spread, gather and smooth keys.
- **Several characters at once**, to edit a kick and the reaction to it together.
- **For full production rigs** he uses another trick: hidden copies of the scene, one per processor core, evaluated in parallel to fill the cache.

What he says is missing: blocking from nothing, steps that must stay planted, stretchy limbs, and a
way back. Edits overwrite the animation. Snapshots are planned. An audience member pointed out the
likeness to "ephemeral rigging", and he agreed.

### What the documentation adds

Read 2026-11-25 from `animate-pro.org/docs/motionator`: the overview, getting started, edit mode,
solvers, motion paths and onion skins pages. The pages on locks, brush, spline, blockout, wormhole
and the patch notes were not read.

- **Product facts.** Needs Blender 5.2 or later. Alpha: "expect bugs and instability". Not sold alone; it is part of a yearly bundle, installed through the author's own installer add-on. No licence is stated on the pages read, so GPL is not to be assumed.
- **Three modes.** Sculpt (edits spread over the range), Blockout (every change keys the whole character on the current frame, with key types such as Key Pose and Breakdown), Edit (define limbs). Retime, Mixer, Looper and Physics are listed as future modes.
- **Two rig modes.** "Motionator Rig" uses its own fast FK maths. "Production Rig" uses Blender's evaluation and "supports any constraint setup". So the control rig case is already on his side of the table.
- **The range is two pairs of pins:** inner pins for frames that take the full change, outer pins for the fade. Default 12 frames each way. Seven falloff shapes per side. The range can stay pinned to the playhead.
- **Path keys have four drags:** drag moves the pose on that frame, Ctrl drag translates, Shift drag smooths, Shift Ctrl drag spreads or gathers in time. Hovering a key previews that frame in the ghosts.
- **Limb types:** FK, IK, Spine, and one called BK. A spine has one driver part and each bone follows by a stiffness value, with an optional look-at handle. A stiffness slider per part writes Blender's own IK stiffness.
- **Temporary IK chains:** click an ancestor to make it the chain root for now.
- **Three chain solvers to choose from,** and two ways for a pole to behave. Reach is capped at 99.9 % so limbs do not pop.
- **Onion skin choices:** a decimated copy of the mesh or rigid cut-outs, a "rigid weight" setting that trades accuracy for speed, a ghost every third frame by default, colour by speed, several shading styles.
- **Cache settings:** selected only, visible range, or the full animation, with an update priority.
- **Vulkan or Metal is required.** The ghost shaders do not run on OpenGL.
- **What it leaves in the file:** helper bones are real bones in a bone collection named `AMP_Helpers`, plus the generated picking shapes. Blender's auto keying is switched off while it runs and restored after.

Not stated on the pages read: undo behaviour, whether keys go straight into the action, and whether
several characters are supported (the talk showed two).

What this changes in our reading:

- **Blockout mode is the missing half.** Sculpting needs animation to exist. Keying the whole character with a key type per pose is how he starts from nothing, and it matches our use of Blender's own key types for anchors.
- **The spine with one driver and a stiffness per bone** is a small, clear model for our spine and tail parts.
- **Inner and outer range pins** are a better control than a single radius, and belong on our timeline.
- **We must not depend on Vulkan.** Bforartists still runs on OpenGL, and our tests run on both.
- **Helper bones in the file are fine under our rule** (they are native data), but we should name what we leave and offer to remove it.

### How we could do this

It fits our rule with nothing to argue: the result is plain keyframes on the rig's own bones, so
the file plays and renders the same in vanilla Blender. It is pure handling.

The honest reading of the talk is that half of his engineering is working around Blender. Those are
exactly the parts we plan to build natively, so the order below starts there.

| Step | What we build | Native or addon | Tier |
|---|---|---|---|
| 1 | **A pose cache for a frame range.** Fast path for plain skeletons straight from the curves. For rigs with constraints, background evaluation on several cores, the way native motion paths do it today but kept up to date | Native C++ | 2 |
| 2 | **Live paths and ghosts from that cache.** Ghosts are the real mesh, bent on the graphics card. This is the onion skin already planned, with one shared cache | Native C++ | 2 |
| 3 | **Proportional editing through time.** Move, rotate and scale in Pose Mode gain a time range and a falloff, beside the proportional editing artists already know. Existing keys in the range are adjusted. An option keys every frame first | Native C++ | 3 |
| 4 | **Locks for one gesture**: keep these parts where their animation has them while I move that one. This needs our posing solver run once per frame in the range, so it comes with puppet posing | Native solver, addon interface | 3 |
| 5 | **Motion brush** on the path: grab and smooth | Native C++ | 4 |
| 6 | **Knots over dense keys**, and Reduce Keys afterwards so the result stays editable by hand | Addon | 4 |
| 7 | **Time spread** as a display option for ghosts and paths, and colour by speed | Native C++ | 4 |

What we would do differently:

- **Work on control rigs too.** His main tool needs a bare skeleton. With the rig description we know which control moves which part of the mesh, so step 3 can write to the controls of a kit rig, and to the bones of a game or motion capture skeleton.
- **Do not require a key on every frame.** Step 3 on ordinary keys is already useful, and it leaves animation that can still be edited the old way.
- **A way back from day one.** Sculpt into a copy of the action, with one button to compare and to return. This is white box habit 5, source never overwritten.
- **Buttons before hotkeys,** and no floating toolbar drawn by hand. The range flags can be handles on the timeline.

Where it pays off first: **the clip library.** A stock walk or a captured take is dense, plain
skeleton animation, which is the case this method handles best. "Drop a clip, then reshape it by
hand" joins Tier 2 to Tier 3 in one story.

Risks: step 4 is a solve on every frame of the range for every mouse move, and may be slow on a
heavy character. Ghosts bent on the graphics card ignore correctives, so they are a preview, not
the final shape. And this is a live product by a known developer. We take the ideas, not the code,
and should say where they came from.

## What the four talks change

| Finding | Effect on the plan |
|---|---|
| T1 is our rigging addon's first level, already prototyped by a Rigify developer | Our direction is confirmed by someone working inside Blender's own rig system. It is also a sign that Blender may get this itself, which is the "Blender overlap" risk in `anim-rig-06` |
| T1 places, T2 builds controls, neither does weights | The gap we alone would fill is the full line: place, build, weigh, check, all by dragging |
| T1 separates placement from the engine | A fourth option for the Tier 0 engine trial: **our placement and handling on top of an existing engine**, with our own recipes only where the light-rig rule needs them |
| T2's developer keeps CloudRig out of the bundle on purpose | A point against bundling our Python addons: fixes wait for a release. Native C++ has no choice, the addons do |
| T2 and T3 are both hotkey and node heavy for the rigger | The ideas carry over. The interfaces do not: every action needs a button |
| T4 gets live paths and ghosts only by avoiding Blender's own evaluation | The strongest case so far for the native cache. With it, the limits he sets himself fall away |
| T4's core gesture is proportional editing through time | A small native feature on its own, and the first slice of motion sculpting we can ship |
| T3 builds a face feature from nodes alone | Face and mouth parts can be node assets in `bfa_default_library`, which Bforartists already ships and maintains |

Not checked: whether the T1 prototype is published and under what licence, the speakers' slides,
and anything shown but not said.

## 21. 🧭 What this changes in the plan

Additions by tier. None changes the tier order. The first table (part 1) is accepted and is now in
`anim-rig-06-campaign-2027.md`. The second table (part 2) is proposed.

**From part 1:**

| Tier | Addition | From |
|---|---|---|
| **0 Foundations** | A fifth prototype: the full body solver on the heavy biped, with a speed target. Highlight prototype tested in orthographic views and on subdivided meshes | FreeIK, Skin Selection |
| **0 Foundations** | Nine white box habits added to the principles | All |
| **0 Foundations** | One-day hands-on comparisons: SkinKit against native weights, RetargetKit against BoneCraft's retargeter | SkinKit, RetargetKit |
| **1 Rigging Kit** | Three visible build stages. Report under Build Rig. Test Pose button. Guided weight rules. Rigid Bind. Naming presets. Edges to Bones | SimpleSkelly, SkinKit, Rig It Quick, Lazy Bones |
| **2 Clips and Motion View** | Ghosts on keys only, ghosts of one part. Shape and Timing locks on the path. Paths for objects and cameras. Batch import through the rig description | Arc Buster, RetargetKit |
| **3 Puppet Posing** | Pose root. Pins to other parts and props. Posing modes. One area, several controls. Corrected areas as vertex groups. Temp Pivot | FreeIK, Skin Selection, Animates |
| **4 Pose Assist and Tweening** | Anchors with scope, shown as key types. Floor path and waypoints. History of proposals. Reduce Keys. Path sculpt and section reshape | Blaze Puppeteer, Arc Buster |
| **5 Creatures, Machines, Kits** | Shrink to centre lines. Adopt a skeleton. Live blended kit preview, combined on Build. Joint sharpness gizmo | Lazy Bones, SimpleSkelly, Ultimate Character Kit, SkinKit |
| **6 Live Puppetry and Optional Intelligence** | Kimodo as a second candidate for the in-between slot, after a licence check | Blaze Puppeteer |

**From part 2:**

| Tier | Addition | From |
|---|---|---|
| **0 Foundations** | The engine trial becomes three-way: our recipe, Rigify, CloudRig | CloudRig |
| **0 Foundations** | Test the hidden-scene method for evaluating other frames. Compare Editable Motion Paths with the reduced Ghost Tool | Editable Motion Paths |
| **0 Foundations** | Retargeting comparison starts with the two free extensions | Retarget, Bulletproof Retarget |
| **0 Foundations** | "Handling and setup" and the vanilla render check become rules | Maintainer |
| **1 Rigging Kit** | Parts labelled for export. Rig version and Update. Validator as a log with Fix buttons. Joint at the centre of a selected loop. Push to centre of volume. Protect painted weights. Guide with pictures that frames the view | Auto-Rig Pro, CloudRig, EasyBones, Voxel Heat Diffuse, BlenRig |
| **1 Rigging Kit** | Make a control by posing, for hand curls and fists | CloudRig |
| **2 Clips and Motion View** | Path editing with the standard keys and proportional editing. Rotation paths. Colour by speed or jitter. Full, In Place, None on drop | Editable Motion Paths, Bulletproof Retarget |
| **3 Puppet Posing** | Snap and Bake over a range. Parent switching without a jump. Handles on bendy bones | CloudRig, Auto-Rig Pro, B-Bone Gizmos |
| **4 Pose Assist and Tweening** | Clips with sliders | Moveset |
| **5 Creatures, Machines, Kits** | Bendy parts. Simulated chain from native cloth. Secondary motion parts with presets. Face part that authors the 52 standard shape keys. Drivers by demonstration. Correctives by posing. Bulge helper. Edit control shapes on the rig | CloudRig, Simply Cloth, Faceit, Easy Driver, X-Muscle, Auto-Rig Pro |
| **6 Live Puppetry** | Face capture connects to the standard shape keys with no mapping. Mix takes by face region | Faceit |

## 22. 📣 What this says about the opportunity

- Bought separately, the add-ons surveyed here cost about 300 US dollars in total at single-user prices.
- Each covers one slice. None joins rigging, posing, ghosts, tweening and clips through one shared
  description of the rig.
- The two most powerful (FreeIK, Blaze Puppeteer) take over part of the rig or the file. An
  integrated set that leaves plain Blender data behind is not on offer anywhere in this list.
- Of the twenty in part 2, fourteen are free and GPL on the official Blender Extensions platform.
  For retargeting, path editing, drivers and bone placement, good free building blocks already exist.
  The work for us is to choose, integrate and give them a point-and-click face, more than to invent.
- Auto-Rig Pro, with over 71,000 sales, shows how large the demand for easier rigging is.
- Several are one-author tools at a low price. Some authors may welcome their ideas, or their code,
  landing in a free application. All but the character kit are listed as GPL.

## 23. ❓ Not checked

- No add-on was installed or run. Feel, speed and reliability are taken from the authors' own words.
- No source code was read, so "listed as GPL" is the store's label, not a verified licence.
- FreeIK's Smooth and Rope modes, multi-pin behaviour, and Blaze Puppeteer's motion transfer are shown only in pictures or not explained.
- The free Clean Graph page did not load. Lazy Bones' feature list is in images.
- Kimodo's licence, download size and hardware needs.
- Whether native key types can be set from an add-on in the way section 3 proposes. To verify in the build.
- Part 2: the external manuals of Auto-Rig Pro, BlenRig, Faceit, X-Muscle and Simply Cloth were not
  read, only their store pages. How BlenRig fits a rig to a new body, and Auto-Rig Pro's "Match to
  Rig", are therefore not described here.
- Whether each add-on's result works in vanilla Blender. Only CloudRig, Editable Motion Paths and one
  Rigi-All tool say so on the pages read.
- The hidden-scene method in Editable Motion Paths comes from a summary of its manual, not a full read, and was not tested.
- How heavy CloudRig's rigs are against the "four levels deep" rule.
- Several pages contradict themselves on supported Blender versions or licence (Easy Driver, Bone Aligner, BlenRig, X-Muscle).
- Reviews are thin everywhere: most of these products show fewer than a dozen ratings and no written reviews.

## Sources

- FreeIK: https://superhivemarket.com/products/freeik , manual https://xbodya13.github.io/free_ik_doc/ , demo https://github.com/xbodya13/free_ik_demo
- Blaze Puppeteer: https://superhivemarket.com/products/blaze-puppeteer (and its docs and FAQ tabs)
- Ultimate Character Kit: https://superhivemarket.com/products/ultimate-character-kit
- Clean Graph: https://superhivemarket.com/products/clean-graph
- Animates Arc Buster: https://superhivemarket.com/products/animates-arc-buster
- Animates Suite: https://superhivemarket.com/products/animates-suite
- Skin Selection: https://superhivemarket.com/products/skin-selection
- Lazy Bones: https://superhivemarket.com/products/lazy-bones
- SimpleSkelly: https://superhivemarket.com/products/simpleskelly-1
- Rig It Quick: https://superhivemarket.com/products/rig-it-quick
- SkinKit: https://superhivemarket.com/products/skinkit
- RetargetKit: https://superhivemarket.com/products/retargetkit
- Auto-Rig Pro: https://superhivemarket.com/products/auto-rig-pro
- BlenRig: https://superhivemarket.com/products/blenrig
- Faceit: https://superhivemarket.com/products/faceit
- X-Muscle System: https://superhivemarket.com/products/x-muscle-system
- Simply Cloth: https://superhivemarket.com/products/simply-cloth
- Voxel Heat Diffuse Skinning: https://superhivemarket.com/products/voxel-heat-diffuse-skinning
- CloudRig: https://extensions.blender.org/add-ons/cloudrig/ and https://studio.blender.org/tools/addons/cloudrig/
- Rigi-All: https://extensions.blender.org/add-ons/rigi-all/
- EasyBones: https://extensions.blender.org/add-ons/easybones/
- FreePicker: https://extensions.blender.org/add-ons/freepicker/
- Bone Aligner: https://extensions.blender.org/add-ons/bone-aligner/
- Easy Driver: https://extensions.blender.org/add-ons/easy-driver/
- Driver Helper: https://extensions.blender.org/add-ons/driver-helper/
- BBone Tools: https://extensions.blender.org/add-ons/bbone-tools/
- B-Bone Gizmos: https://extensions.blender.org/add-ons/bbone-gizmo/
- FK/IK Snapping Tools: https://extensions.blender.org/add-ons/fk-ik-snapping-tools/
- Retarget: https://extensions.blender.org/add-ons/retarget/
- Bulletproof Retarget: https://extensions.blender.org/add-ons/bulletproof-retarget/
- Editable Motion Paths: https://extensions.blender.org/add-ons/editable-motion-paths/
- Moveset: https://extensions.blender.org/add-ons/moveset/

Part 3, recordings on the Blender channel (captions only): `youtube.com/watch?v=CTX9lB95e40` (Rigify), `youtube.com/watch?v=IgUhwbDrUAI` (CloudRig), `youtube.com/watch?v=WvJKzSva5Xc` (mouth rig), `youtube.com/watch?v=M2J_fQNLDfg` (motion sculpting).
