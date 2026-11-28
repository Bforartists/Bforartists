# Image Editor Painting 2027: Layers, Transform, Paint Over Render, Camera Planes

Draft 2, 2026-11-27. Status: proposal, decisions in section 7 recorded. Sizes are estimates made
without measuring the work.

This is the design note for making the Image Editor's paint mode a place where real 2D work can be
finished: texture editing, matte painting over a render, and concept bashing from the 3D viewport.
Brush engines are a separate subject. This note covers what the brushes need around them to be
useful: layers, moving things, bringing pictures in, and getting the result back into 3D.

## At a glance

> 🎨 **One story: render, paint over it in layers, see it back in the camera. Never leave.**

| Tier | Name | The artist can now... | Size |
|---|---|---|---|
| 0 🧱 | Foundations | (nothing yet: layer data, flatten, undo proven in a prototype) | M |
| 1 🗂️ | Layers | paint on layers with opacity, blend modes, lock, merge, and save them | L |
| 2 ✋ | Move and Drop | drop or paste a picture in as a layer, then move, scale, rotate and flip it with a gizmo | M |
| 3 🖼️ | Paint Over Render | press one button on a render or the viewport and paint on top of it, then refresh the render underneath | S |
| 4 🎥 | Back to 3D | see the painting live in the camera, and split the layers into planes in front of the camera | S to M |
| 5 ✂️ | Selections and Masks | select a region, cut, copy, move it, mask a layer, crop | L |
| 6 🏔️ | Projection and Adjustments | project the painting onto scene geometry, adjustment layers, layer groups | L |

Tiers 1 to 4 are the 2027 goal. They are what turns "possible but painful" into "useful". Tiers 5
and 6 are wanted in 2027 as well if the first four land in time. They start once the first four
have been used on real work, and they are the ones that slip into 2028 if something has to.

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
  Image, name, visible, locked, opacity, blend mode, and a 2D transform (offset, rotation, scale).
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

### Tier 0 🧱 Foundations

Prototype only, nothing ships.

- Layer stack stored and read from C++, with an RNA view for the UI and for scripts.
- Flatten: active layer redirect, and a flat image that updates while a stroke is running.
- Measure: 4K and 8K, byte and float, 5 and 30 layers. This decides between the plain and the
  cached flatten (section 5.1).
- Undo test: stroke, add layer, stroke, reorder, undo all the way back.

Exit check: painting on layer 3 of 10 at 4K feels the same as painting on a single image.

### Tier 1 🗂️ Layers

- **Layers panel** in the Image Editor sidebar and as a tab next to Tool: list with eye, lock,
  name, thumbnail, drag to reorder. Opacity and blend mode above the list, as in Krita.
- Operators: new layer, duplicate, delete, merge down, flatten, move up and down, clear,
  convert an ordinary image to a layered one and back, alpha lock.
- `Image > New` gets a "Layered" checkbox. Painting on an ordinary image stays exactly as it is.
- The 3D viewport Texture Paint slot can point at a layered image. The stroke there goes to the
  active layer as well, and the model shows the flat result.
- Export and import of OpenRaster.

### Tier 2 ✋ Move and Drop

- **Drop a file** on the Image Editor while a layered image is shown: it becomes a new layer under
  the cursor. Drop on an ordinary image shows a small dialog: `Open`, or `Add as Layer` (which
  converts the image to a layered one first). A modifier key skips the dialog. Same for image
  assets from the Asset Browser.
- **Paste** (`Ctrl V`) makes a layer in a layered image, not a separate "Clipboard" image.
- **Layer transform tool**: move, rotate, scale, flip, with the existing 2D gizmo. It needs a new
  bounds case for pixel layers and the paint mode block lifted for this tool.
- The transform is **kept as numbers** on the layer and shown live. Nothing is resampled until
  `Apply Transform`, a merge, or a stroke on that layer. So a photo can be moved ten times without
  getting soft.
- Number fields for position, rotation and scale in the Layers panel. Fit to canvas, fill canvas,
  centre.
- Later in this tier, if time allows: perspective (four corner) distort. It is the single most
  used transform in photo bashing, and the image transform function already takes a 3x3 matrix.

### Tier 3 🖼️ Paint Over Render

- **`Paint Over Render`** button in the Image Editor header when a Render Result or Viewer image
  is shown, and in the Render menu. It:
  1. copies the shown picture into a new layered image, as a locked bottom layer "Render",
  2. adds an empty layer "Paint" above it and makes it active,
  3. switches the editor to that image in paint mode with a brush ready.
- **`Paint Over Viewport`** in the 3D view does the same from a viewport snapshot. The code for
  the snapshot exists in `Image from View`.
- The new image remembers scene, camera and frame. **`Refresh Render Layer`** replaces only the
  bottom layer after a new render. The paint layers stay. This is the loop that makes iteration
  possible: change the lighting, render, refresh, keep the paint.
- Options: which pass to copy (combined by default), and "also bring passes as layers" for AO,
  mist or an object matte, hidden by default.
- Colour: renders are scene-linear float. The painting stays float and is shown through the same
  view transform as the render, so the colours do not shift when the button is pressed. Float
  painting at render size is part of the Tier 0 speed measurement.
- Back to the compositor: the flat image is an ordinary image, so an Image node picks it up. A
  `Use in Compositor` button adds that node.

Stills first. Painting over an animation (a layer that holds per frame) is not in this plan.

### Tier 4 🎥 Back to 3D

Three ways, from cheap to deep. The first two are in this tier.

1. **Show in Camera.** One button puts the flat image on the scene camera as a background image,
   in front, with an opacity slider. It updates as you paint. This is the "cast the painting into
   the viewport" answer, and it is almost free because camera background images already exist.
2. **Layers to Camera Planes.** Each visible layer becomes a plane, parented to the camera and
   sized to fill its frame at its distance. Options:
   - **Near** and **Far**: the distance of the first and the last plane from the camera. The
     layers are spread between them in stack order, top layer nearest.
   - **Bias**: a slider from -1 to 1. At 0 the planes are evenly spaced. Towards 1 they bunch up
     at the far end, with wide gaps near the camera. Towards -1 they bunch up near the camera.
     The planes move live while the slider is dragged, and each plane rescales to keep filling
     the frame.
   - Later: **from the render depth**, where each layer goes to the typical depth of the render
     under its painted pixels. Needs a depth pass kept from Tier 3.
   - material: emission with alpha, so it looks the same as the painting.

   Each plane uses the layer's own image, so painting in the Image Editor, or straight on the plane
   in the 3D view, updates both. Unparent the planes and move the camera and you have a 2.5D matte
   painting with parallax. The plane sizing code exists in `Import Images as Planes`. The parenting
   and the depth placement are new.
3. **Project onto geometry** (Tier 6). The painting is projected from the camera onto the scene
   meshes, for camera moves that planes cannot survive. Blender has the parts (UV Project,
   `Project Edit` and `Project Apply`) but no clean workflow.

### Tier 5 ✂️ Selections and Masks

- Rectangle, ellipse, lasso and "by colour" selection in paint mode, stored as a mask image.
- Strokes and fills respect the selection. Cut, copy, paste, delete, and move the selected pixels
  (which lifts them into a floating layer, as in Krita).
- Layer masks, clipping to the layer below.
- Crop tool and canvas resize that act on all layers.

This tier is large because selection touches every tool. That is why it comes after the first
four, which give the most with the least.

### Tier 6 🏔️ Projection and Adjustments

- Camera projection of the painting onto geometry (see Tier 4, third way).
- Adjustment layers (levels, hue and saturation, curves) and layer groups.
- Reference layers and a colour picker that samples the flat result.

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
| 2 | Scope for 2027 | Tiers 1 to 4, and Tiers 5 and 6 in the same year if possible |
| 3 | Where does this sit against the animation campaign? | Separate track |
| 4 | Dropping a picture on the Image Editor | A layer on a layered image. A dialog (Open or Add as Layer) on an ordinary image |
| 6 | Camera planes spacing | Near and Far distance with a Bias slider, so the planes can sit closer together far away or closer together near the camera. Depth placement from the render later |
| 7 | Layered image as the default for `Image > New` in paint mode? | Not until it is stable and tested |

Still open:

| # | Question | Suggested answer |
|---|---|---|
| 5 | First layered file format | OpenRaster, explained in section 3.4. Multilayer EXR second |
