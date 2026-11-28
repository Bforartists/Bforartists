# Image Editor Painting 2027: Pieces, Layers, Render Round Trip, Camera Planes

Draft 4, 2026-11-27. Status: proposal, decisions in section 7 recorded. Sizes are estimates made
without measuring the work. Draft 3 reorders the tiers around the goal in section 0.

This is the design note for making the Image Editor's paint mode a place where real 2D work can be
finished: texture editing, matte painting over a render, and concept bashing from the 3D viewport.
Brush engines are a separate subject, and the one we have is good enough to start. This note
covers what the brushes need around them to be useful.

## 0. The goal

From the maintainer, 27 November 2026. Layers matter, but they are a means. The goal is:

1. **Work with pieces of images together.** Drop pictures in, move, scale, rotate and distort
   them with gizmos, cut bits out, blend them. Photo bashing.
2. **Pull from the render, push back into the render.** One click each way.
3. **Draw the way Grease Pencil draws**, but straight onto an image. Same tools, same places.
4. **Familiar, fast, easy.** Nothing to set up, nothing to look up.
5. Together these make **texture painting in the Image Editor really useful**.

## At a glance

> 🎨 **One story: drop it in, move it, paint it, send it back to the render. Never leave.**

| Tier | Name | The artist can now... | Size |
|---|---|---|---|
| 0 🧱 | Foundations | (nothing yet: layer data, flatten, gizmo speed and undo proven in a prototype) | M |
| 1 ✋ | Pieces | drop or paste pictures in as layers, move, scale, rotate and distort them with a gizmo, cut bits out, erase, paint on layers | L |
| 2 🔁 | Render Round Trip | paint over a render or the viewport with one button, and have the paint come out on top of every new render and show in the camera | M |
| 3 ✏️ | Draws Like Grease Pencil | find the Grease Pencil tools in the same places: shapes, eyedropper, erase, same keys | M |
| 4 🎥 | Camera Planes | split the layers into planes in front of the camera, with depth | S to M |
| 5 💾 | Layer Files and Depth | exchange layered files with Krita, group and mask layers, crop | M |
| 6 🏔️ | Selections, Projection, Adjustments | use full selections with every brush, project the painting onto geometry, adjustment layers | L |

Tiers 1 to 3 are the goal itself and come first. Tier 4 is small and can be built alongside. All
six are wanted in 2027. Tiers 5 and 6 are the ones that slip into 2028 if something has to.

**Is it possible?** Yes. Nothing here needs a new kind of technology. The honest picture:

- The pieces mostly exist: 25 blend modes, a 3x3 image transform, a tile undo system, a 2D gizmo, a
  camera-frame plane importer, a "new image from pixels" function.
- What is missing is the idea of a layer. Today every stroke writes straight into the one buffer of
  the image shown in the editor. There is no stack, no selection, and nothing that moves pixels.
- The hard parts are speed while painting on large images with many layers, and undo of stack
  changes. Both are known problems with known answers (section 5).

## 1. What exists today

Checked in the source on 27 November 2026.

| Area | Today | Where |
|---|---|---|
| Stroke target | The image shown in the editor, its own buffer, byte or float. One line decides it | `sculpt_paint/mesh/paint_image_2d.cc:1665` |
| Undo | 64 px tiles, keyed by image. Works for any image without extra code | `space_image/image_undo.cc`, `paint_image.cc:121` |
| Layers | None. Texture Paint "slots" are a list of separate images to choose from, not a stack | `DNA_material_types.h:260` |
| Blend modes | 25 modes in the image library, threaded | `IMB_imbuf.hh:210`, `imbuf/intern/rectop.cc` |
| Moving pixels | Only flip and rotate by 90 degrees for the whole image. No crop operator | `image_ops.cc:3006`, `3074` |
| Selection | None in paint mode | `space_image.py:1359` |
| 2D gizmo | Shared by the UV editor and the Sequencer. Switched off in paint mode | `transform_gizmo_2d.cc:82`, `229` |
| Drop a file | Opens the picture and replaces what the editor shows | `bl_operators/image.py:304` |
| Paste | Makes a new image called "Clipboard" | `image_ops.cc:3228` |
| Render Result | Cannot be painted. Bforartists hides paint mode for it. No "copy render to image" operator | `space_image.py:1251` |
| Viewport snapshot | `Image from View` already makes an image from the 3D view and can project it back | `paint_image_proj.cc:6571` |
| Camera display | Camera background images with opacity, front or back, fit or crop | `DNA_camera_types.h:164` |
| Planes | `Import Images as Planes` can size a plane to the camera frame and track the camera. It does not parent to it | `bl_operators/image_as_planes.py:620` |

Bforartists has no changes in the paint stroke code today, so there is nothing of ours to break
there, and nothing to carry through merges yet.

## 2. Principles

1. **Files stay compatible.** A layered painting opens in vanilla Blender. There it shows as the
   flat picture, and every layer is present as a normal image. Nothing is lost on a save there.
2. **A layer is an Image.** No new kind of data. Anything that works on an image (save, pack, use
   in a material, use in the compositor, paint in the 3D view) works on a layer.
3. **One click per intent.** "Paint over this render", "show it in the camera", "make planes" are
   single buttons, not recipes.
4. **Drag and drop first.** Pictures arrive by dropping or pasting, and land under the cursor with
   the gizmo already on them.
5. **Native where speed or the editor is involved.** The layer stack, flatten, stroke target and
   gizmo are C++. Setup operators such as the camera planes can be Python.
6. **Opt-in until it has passed a beta**, same six steps per tier as the animation campaign
   (`anim-rig-06-campaign-2027.md`, section 2).

## 3. The data model

### 3.1 Recommended: a stack of Images, described on the flat image

```
Image "Matte_01"            <- the flat result. This is what materials, the compositor
  |                            and vanilla Blender see.
  +- layer stack (custom properties on the image)
       3  "Highlights"   Image "Matte_01.Highlights"   Add      60 %
       2  "Trees"        Image "Matte_01.Trees"        Mix     100 %   moved, scaled
       1  "Paint"        Image "Matte_01.Paint"        Mix     100 %   <- active
       0  "Render"       Image "Matte_01.Render"       Mix     100 %   locked
```

- The stack lives in **custom properties** on the flat image: for each layer a pointer to its
  Image, name, visible, locked, opacity, blend mode, a 2D transform (offset, rotation, scale, and
  four corners for perspective), and a **reference** switch.
- A **reference layer** is seen in the editor but left out of the flat result. The render under a
  paint-over is one. So the flat image holds the paint alone, with transparency, and can be laid
  over a new render or over the live viewport (Tier 2). Traced photos and guides use it too.
- Custom properties are kept by vanilla Blender on load and save, and the pointers keep the layer
  images alive. A Bforartists-only DNA struct would be dropped by vanilla on save, so it is not
  used. This follows the rule in `CLAUDE.md`.
- A stroke goes to the active layer's image. That is the one-line redirect in
  `paint_2d_new_stroke`. Fill and gradient read the editor image directly in two more places.
- Undo of strokes comes for free, because the tile undo is keyed by image.
- Layers may be smaller or larger than the canvas. A dropped photo keeps its own resolution until
  the artist applies the transform.

### 3.2 Alternatives considered

| Option | For | Against |
|---|---|---|
| **Stack of Images in custom properties** (recommended) | Vanilla compatible, undo for free, small change to the stroke code | Many image datablocks, needs naming and cleanup rules |
| New DNA struct for layers | Clean, fast to read | Lost when vanilla saves the file. Breaks the compatibility promise |
| One multilayer EXR per painting | One file on disk, Krita reads it | Packed multilayer cannot be painted today, undo does not cover passes, float only |
| A compositor node group as the stack | Non-destructive, vanilla renders it | Slow to paint through, heavy UI, wrong tool for bashing photos |
| Wait for Blender's layered textures | No merge burden | Designed in 2022, still not shipped, aimed at PBR materials and not at 2D painting |

### 3.3 On disk

- Inside the blend: layers are packed images, like any painted image today.
- Flat export: `Save As` on the flat image, unchanged.
- Layered export and import: **OpenRaster (.ora)** first, see 3.4. Multilayer EXR second, for
  float work. PSD import later, and only if the image library we ship can read PSD layers. That
  has to be checked, it is not verified.

### 3.4 What OpenRaster is

OpenRaster is an open file format for layered pictures, made by the open source graphics programs
so they can pass layered work to each other. It plays the role PSD plays between commercial
programs, but the specification is public and short. The file ending is `.ora`.

An `.ora` file is a zip archive. Rename it to `.zip` and it opens:

```
painting.ora
  mimetype              the text "image/openraster"
  stack.xml             the layer list: order, names, and per layer the settings below
  data/layer0.png       one PNG per layer
  data/layer1.png
  mergedimage.png       the flat picture, for programs that only want the result
  Thumbnails/thumbnail.png
```

| | |
|---|---|
| Per layer it stores | name, visible, opacity, blend mode, position (x, y), and groups of layers |
| Reads and writes it | Krita, GIMP, MyPaint |
| Does not read it | Photoshop |
| Why it suits us | A zip, PNGs and a small XML file. We can write and read it with what Bforartists already ships, no new library |

Limits to know about:

- **No float.** Layers are PNG, so 8 or 16 bit. A paint-over of a scene-linear render loses its
  range above white. That is what the multilayer EXR export is for.
- **Position only.** A layer has x and y, no rotation or scale. On export, layers with a pending
  transform are written already transformed. The layers in the blend file are not touched.
- **No masks or adjustment layers** in the standard. Programs add their own extras, which others
  ignore. When Tiers 5 and 6 arrive, masks are applied on export.
- **Blend modes** are a fixed list (normal, multiply, screen, overlay, darken, lighten, dodge,
  burn, hard and soft light, difference, colour, luminosity, hue, saturation, add). Our modes
  outside that list are written as normal, with a warning.

So OpenRaster is the everyday bridge to Krita and back for texture and concept work, and EXR is
the bridge for render paint-overs.

## 4. The tiers

The order follows the goal in section 0: first working with pieces, then the trip to the render
and back, then the familiar drawing tools. Layers come first only as far as the pieces need them.

### Tier 0 🧱 Foundations

Prototype only, nothing ships.

- Layer stack stored and read from C++, with an RNA view for the UI and for scripts.
- Flatten: active layer redirect, and a flat image that updates while a stroke is running.
- A layer drawn with a pending transform, moved with the gizmo, at full frame rate.
- Measure: 4K and 8K, byte and float, 5 and 30 layers. This decides between the plain and the
  cached flatten (section 5.1).
- Undo test: stroke, add layer, move layer, stroke, reorder, undo all the way back.
- Check that a layered UDIM image works (each layer is then a tiled image with the same tiles).

Exit check: painting on layer 3 of 10 at 4K feels the same as painting on a single image, and
dragging a 4K photo layer with the gizmo is smooth.

### Tier 1 ✋ Pieces: layers, drop, gizmo, cut

The heart of the plan. One release, because none of these is useful without the others.

**Layers, the part the pieces need**

- **Layers panel** in the Image Editor sidebar, laid out like the Grease Pencil Layers panel: list
  with eye, lock, name, thumbnail, drag to reorder. Opacity and blend mode above the list.
- New, duplicate, delete, merge down, flatten, clear, alpha lock.
- `Image > New` gets a "Layered" checkbox. Any ordinary image can be converted to a layered one
  and back. Painting on an ordinary image stays exactly as it is.
- The 3D viewport Texture Paint slot can point at a layered image. The stroke there goes to the
  active layer, and the model shows the flat result. So a texture is painted in the Image Editor
  with layers and seen on the model at the same time.

**Bring pictures in**

- **Drop a file** on a layered image: it becomes a new layer under the cursor, with the gizmo on
  it. Drop on an ordinary image shows a small dialog: `Open`, or `Add as Layer` (which converts
  the image to a layered one first). A modifier key skips the dialog. Same for image assets from
  the Asset Browser, so a folder of photo cut-outs works as a bashing library.
- **Paste** (`Ctrl V`) makes a layer, not a separate "Clipboard" image. A screenshot or a copy
  from a browser lands straight on the canvas.

**Move them**

- **Layer transform tool**: move, rotate, scale, flip, with the existing 2D gizmo, plus
  **perspective** by dragging the four corners. Perspective is what makes a photo sit on a wall
  or a floor, so it is part of this tier and not an extra.
- Clicking a pixel with the tool picks the layer under the cursor, so pieces are grabbed
  directly, without going to the list.
- The transform is **kept as numbers** on the layer and shown live. Nothing is resampled until
  `Apply Transform`, a merge, or a stroke on that layer. A photo can be moved ten times without
  getting soft.
- Number fields in the panel. Fit to canvas, fill canvas, centre.

**Cut them**

- Box and lasso select with three results: **cut to new layer**, **copy to new layer**, delete.
  This is the least selection that makes bashing possible: take the tree out of the photo, leave
  the sky. Selections that every brush respects come in Tier 6.
- An **Erase tool** with soft brushes, to blend a piece into what is under it.
- Quick colour match on a layer as plain operators: hue and saturation, brightness and contrast,
  levels, invert. They change the pixels. Adjustment layers that stay editable are Tier 6.

### Tier 2 🔁 Render Round Trip

**Pull from the render**

- **`Paint Over Render`** button in the Image Editor header when a Render Result or Viewer image
  is shown, and in the Render menu. It:
  1. copies the shown picture into a new layered image as a locked **reference layer** "Render",
  2. adds an empty layer "Paint" above it and makes it active,
  3. switches the editor to that image in paint mode with a brush ready.
- **`Paint Over Viewport`** in the 3D view does the same from a viewport snapshot. The code for
  the snapshot exists in `Image from View`.
- The image remembers scene, camera and frame. **`Refresh Render Layer`** replaces only the
  reference layer after a new render. The paint stays.
- Options: which pass to copy (combined by default), and "also bring passes as layers" for AO,
  mist or an object matte, hidden by default.
- Colour: renders are scene-linear float. The painting stays float and is shown through the same
  view transform as the render, so colours do not shift when the button is pressed.

**Push back into the render**

A reference layer is seen in the editor but left out of the flat result (section 3.1). So the
flat image is the paint alone, with transparency. That makes the way back simple:

- **`Composite Over Render`**: one button adds an Image node with the painting and an Alpha Over
  after the render layers in the compositor. From then on every render comes out with the paint
  on top. Change the lighting, render again, the paint is still there. Nothing to redo.
- **`Show in Camera`**: one button puts the painting on the scene camera, in front, with an
  opacity slider. It updates while you paint, and because it is the paint alone, the live 3D
  scene shows through underneath. This is the painting "cast" into the viewport.
- **Per layer**: the same two buttons in the layer's right-click menu, `Composite Layer Over
  Render` and `Show Layer in Camera`. They send that one layer by itself. A layer is an ordinary
  image, so this needs nothing new. Useful when only the fog, or only the sky, should go back.
- `Save a Copy` with the reference included gives the full picture as a file.

Stills first. The paint sits over every frame of a locked-off shot, which is already useful.
Paint that changes per frame is not in this plan.

### Tier 3 ✏️ Draws Like Grease Pencil

Someone who knows Grease Pencil draw mode should find the same tools in the same places, with the
same keys, when painting on an image. Today the two differ:

| | Grease Pencil draw mode | Image paint today |
|---|---|---|
| Tools | Draw, Erase, Fill, Trim, Eyedropper, Line, Polyline, Arc, Curve, Box, Circle | Draw, Blur, Smear, Clone, Fill, Mask |
| Layers | Panel with opacity, blend, masks, transform, adjustments, groups | None |
| Select | Tweak, box, circle, lasso | None |

- Add to image paint: **Line, Polyline, Arc, Curve, Box, Circle** (drawn with the active brush),
  **Eyedropper** as a tool. Erase arrives in Tier 1.
- Same tool order in the toolbar, same icons where the tool is the same. Hotkeys are a separate
  question (open decision 12).
- Same header layout: brush, colour, radius and strength in the same order as Grease Pencil.
- Smooth stroke (stabiliser) reachable from the header as in Grease Pencil.
- Blur, Smear and Clone stay. They are what an image has and strokes do not.

This tier is UI and operators around the existing brush code. It covers tools and layout only
(decision 9). How the stroke itself feels (smoothing, pressure response) is brush engine work and
not part of this plan.

### Tier 4 🎥 Camera Planes

- **Layers to Camera Planes.** Each visible layer becomes a plane, parented to the camera and
  sized to fill its frame at its distance. Options:
  - **Near** and **Far**: the distance of the first and the last plane from the camera. The
    layers are spread between them in stack order, top layer nearest.
  - **Bias**: a slider from -1 to 1. At 0 the planes are evenly spaced. Towards 1 they bunch up
    at the far end, with wide gaps near the camera. Towards -1 they bunch up near the camera.
    The planes move live while the slider is dragged, and each plane rescales to keep filling
    the frame.
  - Material: emission with alpha, so it looks the same as the painting.
  - Later: **from the render depth**, where each layer goes to the typical depth of the render
    under its painted pixels.
- Each plane uses the layer's own image, so painting in the Image Editor, or straight on the
  plane in the 3D view, updates both. The planes are real objects, so they are in the render,
  behind and in front of scene objects. Unparent them and move the camera and you have a 2.5D
  matte painting with parallax.
- The plane sizing code exists in `Import Images as Planes`. Parenting and spacing are new.

### Tier 5 💾 Layer Files and Depth

- Export and import of OpenRaster (section 3.4), then multilayer EXR.
- Layer groups, clipping to the layer below, layer masks.
- Crop tool and canvas resize that act on all layers.
- Image selectors fold layer images under their parent (section 5.4).

### Tier 6 🏔️ Selections, Projection, Adjustments

- Full selections: rectangle, ellipse, lasso, by colour, stored as a mask. Every brush and fill
  respects them. Moving selected pixels lifts them into a floating layer.
- Camera projection of the painting onto scene geometry, for camera moves that planes cannot
  survive. Blender has the parts (UV Project, `Project Edit`, `Project Apply`) but no clean
  workflow.
- Adjustment layers that stay editable (levels, hue and saturation, curves).

## 5. The hard parts

### 5.1 Speed while painting

Every dab changes the active layer, and the flat picture has to follow at once.

- **Plain way:** re-blend all layers for the tiles the dab touched. Fine for a few layers.
- **Cached way** (what Krita does): keep one picture of everything below the active layer and one
  of everything above. A dab then costs two blends whatever the number of layers. The caches are
  rebuilt when the active layer or the stack changes.
- **Later:** draw the stack on the GPU in the Image Editor and only flatten on the CPU when another
  user (material, compositor, save) asks for it.

Tier 0 measures the plain way first. The cached way is only built if the numbers ask for it.

Dragging a layer with the gizmo has the same problem in another form: resampling a 4K photo on
the CPU for every mouse move is too slow. While the gizmo is held, the layer is drawn by the GPU
in the Image Editor with its matrix, and the flat image is updated once, on release. The model in
the 3D view and the camera overlay therefore follow on release, not during the drag.

### 5.2 Undo

Strokes use the image tile undo. Stack changes (add, delete, reorder, opacity) are ordinary data
changes. Mixing the two undo systems inside paint mode is a known weak spot in Blender. The plan is
to push stack changes into the same paint undo stack as their own step type, and to prove it in
Tier 0 before any UI is built.

### 5.3 Merges with Blender

- The stroke redirect is three small marked edits in `paint_image_2d.cc`. The rest is new files.
- Blender may refactor painting, and its own layered textures project may arrive one day. Because
  our layers are plain images with custom properties, a converter to whatever Blender ships stays
  possible.

### 5.4 Datablock clutter

Thirty layers are thirty images in every image dropdown. Layer images get a flag in the stack so
the image selectors can fold them under their parent. In vanilla Blender they show as a flat list
with clear names (`Matte_01.Trees`).

## 6. What others have done

Found in a quick search on 27 November 2026. None of these were tested or read for this note.

| Add-on | What it is said to do |
|---|---|
| [Layerify](https://superhivemarket.com/products/layerify) (commercial) | Layers in the Image Editor with a free transform tool, also painting on the model. The closest to this plan |
| [Image Editor Plus](https://blendermarket.com/products/image-editor-plus) | Layers with position, rotation and scale in the Image Editor. Listing dates from 2021 |
| [Paint System](https://extensions.blender.org/add-ons/paint-system/versions/), [HAS Paint Layers](https://extensions.blender.org/add-ons/has-paint-layers/), [Ucupaint](https://digitalproduction.com/2026/11/03/ucupaint-3-blender-texture-painting/) | Layered texturing through material nodes, aimed at painting on models |
| [MattePainter](https://blendermarket.com/products/mattepainter) | Matte painting planes and masks, with the painting done outside Blender |

Blender's own [layered textures design](https://projects.blender.org/blender/blender/issues/68894)
is from 2022, is aimed at PBR materials, and has not shipped.

What an add-on cannot do well, and why this is planned natively: redirect the stroke, flatten at
painting speed, hook into paint undo, and own the drop and the gizmo in the editor.

To do: find the add-on the maintainer remembers, try Layerify and Image Editor Plus, and write an
`anim-rig-07` style survey of what to learn from them.

## 7. ✅ Decisions recorded

From the maintainer, 27 November 2026.

| # | Question | Decision |
|---|---|---|
| 1 | Layers as plain images with custom properties (section 3.1)? | Yes. Files must work in vanilla Blender, with no add-on and without Bforartists |
| 2 | Scope for 2027 | All tiers in 2027 if possible. Tiers 1 to 3 first (draft 3 numbering), Tiers 5 and 6 are the ones that may slip |
| 3 | Where does this sit against the animation campaign? | Separate track |
| 4 | Dropping a picture on the Image Editor | A layer on a layered image. A dialog (Open or Add as Layer) on an ordinary image |
| 6 | Camera planes spacing | Near and Far distance with a Bias slider, so the planes can sit closer together far away or closer together near the camera. Depth placement from the render later |
| 7 | Layered image as the default for `Image > New` in paint mode? | Not until it is stable and tested |
| 8 | What the plan is for | Section 0. Pieces, gizmos and bashing, the trip to the render and back, and drawing like Grease Pencil come before layer extras. The tiers were reordered for this in draft 3 |
| 5 | First layered file format | OpenRaster (section 3.4). Multilayer EXR second |
| 9 | What "like Grease Pencil" covers | Tools and layout only. Not the stroke feel |
| 10 | Getting paint alone back onto the render | Reference layers, yes. Also any single layer can be sent to the compositor or shown over the camera by itself |
| 11 | Selection | Minimal cut (box and lasso to a new layer) in Tier 1, full selections in Tier 6. Selection here means pixels in a layer, or whole layers. There are no strokes to select, this is raster. Selecting strokes stays a Grease Pencil thing |

Still open:

| # | Question | Suggested answer |
|---|---|---|
| 12 | Hotkeys for the new image paint tools: the same as their Grease Pencil twins? | Yes where the key is free in the Image Editor. Not part of decision 9 |
