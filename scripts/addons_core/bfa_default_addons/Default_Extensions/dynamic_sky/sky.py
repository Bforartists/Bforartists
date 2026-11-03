# SPDX-FileCopyrightText: 2015 Pratik Solanki (Draguu)
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.app.handlers import persistent
from bpy.props import IntProperty, StringProperty
from bpy.types import Operator


# Handle error notifications
def error_handlers(self, error, reports="ERROR"):
    if self and reports:
        self.report({'WARNING'}, reports + " (see the system console for details)")

    print("\n[Dynamic Sky]\nError: {}\n".format(error))


# Bumped when a feature changes the tree; MIGRATIONS[n] upgrades a world's
# node tree from version n to n+1. Version 0 = any pre-versioning tree.
SKY_VERSION = 10


def _add_hdri(nt):
    # Splice a mix (fac 0 = procedural, 1 = HDRI) between the final combine
    # mix and the Background node. Fac 0.0 is pixel-identical to the
    # pre-HDRI tree, so this is safe for both fresh builds and migration.
    if "Sky_HDRI_blend" in nt.nodes:
        return
    bg = nt.nodes["Scene_Brightness"]
    if not bg.inputs[0].links:
        return  # hand-edited tree; the UI degrades per-control
    link = bg.inputs[0].links[0]
    combine, out_socket = link.from_node, link.from_socket
    combine.name = "combine"

    env = nt.nodes.new(type="ShaderNodeTexEnvironment")
    env.name = "Environment_Texture"
    env.location = (6150, 60)

    blend = nt.nodes.new(type="ShaderNodeMixRGB")
    blend.name = "Sky_HDRI_blend"
    blend.inputs[0].default_value = 0.0
    blend.location = (6500, 360)

    nt.links.remove(link)
    nt.links.new(blend.inputs[1], out_socket)
    nt.links.new(blend.inputs[2], env.outputs[0])
    nt.links.new(bg.inputs[0], blend.outputs[0])


def _add_horizon(nt):
    # The horizon line lives in ramp element positions, which are not
    # sockets; shift the coordinate feeding the ramps instead: an identity
    # Math ADD (offset 0.0) between the sky normal and the three ramps.
    if "Horizon_height" in nt.nodes:
        return
    sky_hor = nt.nodes["Sky_and_Horizon_colors"]
    if not sky_hor.inputs[0].links:
        return  # hand-edited tree; the UI degrades per-control
    sc4 = sky_hor.inputs[0].links[0].from_node
    if not sc4.inputs[0].links:
        return
    link = sc4.inputs[0].links[0]
    skynor, out_socket = link.from_node, link.from_socket
    # Name the walked-to nodes on first touch (renaming is visually inert);
    # later features and diagnostics find them by name.
    sc4.name = "sc4"
    skynor.name = "skynor"
    for other in (l.to_node for l in out_socket.links):
        if other != sc4 and other.type == 'VALTORGB':
            # sc3 feeds three mix nodes, sc3_1 only one
            other.name = "sc3" if len(other.outputs[0].links) > 1 else "sc3_1"

    add = nt.nodes.new(type="ShaderNodeMath")
    add.name = "Horizon_height"
    add.inputs[1].default_value = 0.0
    add.location = (3550, 1070)

    targets = [l.to_socket for l in out_socket.links]
    while out_socket.links:
        nt.links.remove(out_socket.links[0])
    nt.links.new(add.inputs[0], out_socket)
    for to_socket in targets:
        nt.links.new(to_socket, add.outputs[0])


def _add_night(nt):
    # Stars and moon live in the camera-ray branch only (combine input 2):
    # lighting them would add noise for a negligible light contribution.
    # Both opacities default 0.0, so the tree stays pixel-identical.
    if "Stars_opacity" in nt.nodes:
        return
    combine = nt.nodes.get("combine")
    if combine is None:
        # tree predates the HDRI step that names combine
        bg = nt.nodes["Scene_Brightness"]
        if not bg.inputs[0].links:
            return  # hand-edited tree; the UI degrades per-control
        combine = bg.inputs[0].links[0].from_node
        combine.name = "combine"
    if not combine.inputs[2].links:
        return  # hand-edited tree; the UI degrades per-control
    link = combine.inputs[2].links[0]
    sunopa_1, out_socket = link.from_node, link.from_socket
    sunopa_1.name = "sunopa_1"

    # Star field: Voronoi distance is 0 at cell centers; a tight inverted
    # ramp keeps only the centers as points. The unlinked Vector input
    # falls back to Generated coordinates (the ray direction).
    stars_tex = nt.nodes.new(type="ShaderNodeTexVoronoi")
    stars_tex.name = "Stars_texture"
    stars_tex.inputs[2].default_value = 30.0  # Scale = star density
    stars_tex.location = (5100, -140)

    stars_ramp = nt.nodes.new(type="ShaderNodeValToRGB")
    stars_ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    stars_ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    stars_ramp.color_ramp.elements[1].position = 0.05
    stars_ramp.location = (5350, -140)

    stars = nt.nodes.new(type="ShaderNodeMixRGB")
    stars.name = "Stars_opacity"
    stars.blend_type = 'ADD'
    stars.inputs[0].default_value = 0.0
    stars.location = (5700, 100)

    # Moon disc: the sun-disc pattern (direction ball -> ramps sharpening
    # the dot product into a disc), tinted by Moon_color.
    moon_tcor = nt.nodes.new(type="ShaderNodeTexCoord")
    moon_tcor.location = (4650, -420)

    moon_nor = nt.nodes.new(type="ShaderNodeNormal")
    moon_nor.name = "Moon_normal"
    moon_nor.location = (4900, -420)

    moon_ramp1 = nt.nodes.new(type="ShaderNodeValToRGB")
    moon_ramp1.color_ramp.elements[0].position = 0.969
    moon_ramp1.color_ramp.interpolation = 'EASE'
    moon_ramp1.location = (5150, -420)

    moon_ramp2 = nt.nodes.new(type="ShaderNodeValToRGB")
    moon_ramp2.color_ramp.elements[0].position = 0.991
    moon_ramp2.color_ramp.elements[1].position = 1
    moon_ramp2.color_ramp.interpolation = 'EASE'
    moon_ramp2.location = (5450, -420)

    moon_col = nt.nodes.new(type="ShaderNodeMixRGB")
    moon_col.name = "Moon_color"
    moon_col.blend_type = 'MULTIPLY'
    moon_col.inputs[0].default_value = 1.0
    moon_col.inputs[2].default_value = (1, 1, 1, 1)
    moon_col.location = (5700, -420)

    moon = nt.nodes.new(type="ShaderNodeMixRGB")
    moon.name = "Moon_opacity"
    moon.blend_type = 'ADD'
    moon.inputs[0].default_value = 0.0
    moon.location = (5940, -60)

    ntl = nt.links.new
    ntl(stars_ramp.inputs[0], stars_tex.outputs[0])
    ntl(stars.inputs[2], stars_ramp.outputs[0])
    ntl(moon_nor.inputs[0], moon_tcor.outputs[0])
    ntl(moon_ramp1.inputs[0], moon_nor.outputs[1])
    ntl(moon_ramp2.inputs[0], moon_ramp1.outputs[0])
    ntl(moon_col.inputs[1], moon_ramp2.outputs[0])
    ntl(moon.inputs[2], moon_col.outputs[0])

    nt.links.remove(link)
    ntl(stars.inputs[1], out_socket)
    ntl(moon.inputs[1], stars.outputs[0])
    ntl(combine.inputs[2], moon.outputs[0])


def _name_cloud_drift(nt):
    # Rename-only: the Math ADD in the cloud coordinate chain has a free
    # input (0.5, its long-standing default) — expose it as the drift
    # control. Names the walked-to nodes on the way; plan 08 reuses them.
    if "Cloud_drift" in nt.nodes:
        return
    node = nt.nodes["Cloud_color"]
    for name in ("sc2", "n2", "Cloud_mapping", "crgb", "Cloud_drift"):
        if not node.inputs[0].links:
            return  # hand-edited tree; the UI degrades per-control
        node = node.inputs[0].links[0].from_node
        node.name = name


def _add_clouds(nt):
    # Coverage/softness shift the noise value before it hits its ramp (ramp
    # element positions aren't sockets, same rule as the horizon). ADD 0 /
    # MULTIPLY 1 are identity. Coverage gates the density texture (n1->sc1),
    # softness scales the detail texture (n2->sc2).
    # ponytail: per-chain knobs; give both chains both if a visual pass wants it
    if "Cloud_coverage" in nt.nodes:
        return
    density = nt.nodes["Cloud_density"]
    if not density.inputs[2].links:
        return  # hand-edited tree; the UI degrades per-control
    sc1 = density.inputs[2].links[0].from_node
    sc1.name = "sc1"
    for ramp, name, op, ident in (
            (sc1, "Cloud_coverage", 'ADD', 0.0),
            (nt.nodes.get("sc2"), "Cloud_softness", 'MULTIPLY', 1.0)):
        if ramp is None or not ramp.inputs[0].links:
            continue  # hand-edited tree; the UI degrades per-control
        link = ramp.inputs[0].links[0]
        node = nt.nodes.new(type="ShaderNodeMath")
        node.name = name
        node.operation = op
        node.inputs[1].default_value = ident
        node.location = (ramp.location[0] - 300, ramp.location[1])
        out_socket = link.from_socket
        nt.links.remove(link)
        nt.links.new(node.inputs[0], out_socket)
        nt.links.new(ramp.inputs[0], node.outputs[0])


def _add_temperature(nt):
    # Kelvin tint for the sun: Blackbody -> MULTIPLY mix spliced on
    # Sun_color's *output* (its input socket stays free - old presets write
    # it). Fac 0.0 is identity, so old trees render pixel-identical.
    if "Sun_temperature" in nt.nodes:
        return
    sunrgb = nt.nodes["Sun_color"]
    if not sunrgb.outputs[0].links:
        return  # hand-edited tree; the UI degrades per-control
    targets = [l.to_socket for l in sunrgb.outputs[0].links]

    body = nt.nodes.new(type="ShaderNodeBlackbody")
    body.name = "Sun_temperature"
    body.inputs[0].default_value = 5500.0
    body.location = (4344.3, 130)

    mix = nt.nodes.new(type="ShaderNodeMixRGB")
    mix.name = "Sun_temperature_mix"
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 0.0
    mix.location = (4600, 300)

    while sunrgb.outputs[0].links:
        nt.links.remove(sunrgb.outputs[0].links[0])
    nt.links.new(mix.inputs[1], sunrgb.outputs[0])
    nt.links.new(mix.inputs[2], body.outputs[0])
    for to_socket in targets:
        nt.links.new(to_socket, mix.outputs[0])


def _add_hdri_rotation(nt):
    # Feed the environment texture Generated coordinates through a Mapping
    # node; its Z rotation is the control. Rotation (0,0,0) of Generated
    # coordinates equals the unlinked Vector input's fallback: identity.
    if "HDRI_rotation" in nt.nodes:
        return
    env = nt.nodes.get("Environment_Texture")
    if env is None or env.inputs[0].links:
        return  # hand-edited tree; the UI degrades per-control

    tcor = nt.nodes.new(type="ShaderNodeTexCoord")
    tcor.location = (5700, 60)

    mapping = nt.nodes.new(type="ShaderNodeMapping")
    mapping.name = "HDRI_rotation"
    mapping.location = (5925, 60)

    nt.links.new(mapping.inputs[0], tcor.outputs[0])
    nt.links.new(env.inputs[0], mapping.outputs[0])


def _add_clouds_over(nt):
    # Procedural clouds over the HDRI: a SCREEN mix (fac 0 = identity)
    # between the HDRI blend and the Background node, compositing the
    # density-masked cloud color over whatever the blend produced. Lets
    # HDRI/hybrid skies keep procedural clouds, which the blend otherwise
    # replaces wholesale.
    if "Clouds_over_HDRI" in nt.nodes:
        return
    blend = nt.nodes.get("Sky_HDRI_blend")
    bg = nt.nodes.get("Scene_Brightness")
    opacity = nt.nodes.get("Cloud_opacity")
    if blend is None or bg is None or opacity is None:
        return  # hand-edited tree; the UI degrades per-control
    if not (bg.inputs[0].links
            and bg.inputs[0].links[0].from_node == blend
            and opacity.inputs[2].links):
        return  # hand-edited tree; the UI degrades per-control
    clouds = opacity.inputs[2].links[0].from_node
    clouds.name = "clouds_masked"

    over = nt.nodes.new(type="ShaderNodeMixRGB")
    over.name = "Clouds_over_HDRI"
    over.blend_type = 'SCREEN'
    over.inputs[0].default_value = 0.0
    over.location = (6600, 160)

    nt.links.remove(bg.inputs[0].links[0])
    nt.links.new(over.inputs[1], blend.outputs[0])
    nt.links.new(over.inputs[2], clouds.outputs[0])
    nt.links.new(bg.inputs[0], over.outputs[0])


def _add_star_size(nt):
    # Per-star size: the Voronoi cell's random color shifts the distance
    # before the ramp cutoff (0.05), so high-random cells stay "white"
    # further out and render bigger stars. Variation 0 shifts nothing, so
    # the tree stays pixel-identical.
    if "Star_size_variation" in nt.nodes:
        return
    tex = nt.nodes.get("Stars_texture")
    if tex is None or not tex.outputs[0].links:
        return  # pre-night or hand-edited tree; the UI degrades per-control
    link = tex.outputs[0].links[0]
    ramp, to_socket = link.to_node, link.to_socket
    ramp.name = "stars_ramp"

    rand = nt.nodes.new(type="ShaderNodeMath")
    rand.name = "Star_size_variation"
    rand.operation = 'MULTIPLY'
    rand.inputs[1].default_value = 0.0  # the exposed variation slider
    rand.location = (5150, -340)

    # rand * variation * -0.05 + distance: sizes grow, no star ever drops out
    spread = nt.nodes.new(type="ShaderNodeMath")
    spread.name = "Star_size_spread"
    spread.operation = 'MULTIPLY_ADD'
    spread.inputs[1].default_value = -0.05
    spread.location = (5350, -340)

    nt.links.remove(link)
    nt.links.new(rand.inputs[0], tex.outputs["Color"])
    nt.links.new(spread.inputs[0], rand.outputs[0])
    nt.links.new(spread.inputs[2], tex.outputs[0])
    nt.links.new(to_socket, spread.outputs[0])


# Version 1 was the first stamped tree, so 0->1 is stamp-only: a no-op
# placeholder keeps list indices aligned with versions.
MIGRATIONS = [lambda nt: None, _add_hdri, _add_horizon, _add_night,
              _name_cloud_drift, _add_clouds, _add_temperature,
              _add_hdri_rotation, _add_clouds_over, _add_star_size]


def sync_background_mode(world):
    # The blend socket changed behind the stored mode's back (preset, bake,
    # reset): point the tab back at reality. The enum's update handler is
    # idempotent for the synced value, so the look never changes here.
    node = (world.node_tree.nodes.get("Sky_HDRI_blend")
            if world.node_tree else None)
    if node is None:
        return
    value = node.inputs[0].default_value
    mode = ('PROCEDURAL' if value <= 0.0 else
            'HDRI' if value >= 1.0 else 'HYBRID')
    if mode == 'HYBRID':
        world.dynsky_hybrid_blend = value
    if world.dynsky_background_mode != mode:
        world.dynsky_background_mode = mode


def migrate(world):
    # Recognize our worlds structurally, never by name; users rename worlds.
    # Linked worlds are read-only.
    if world.library is not None:
        return
    if not (world.node_tree and "Sky_normal" in world.node_tree.nodes):
        return
    for step in MIGRATIONS[world.get("dynamic_sky_version", 0):]:
        try:
            step(world.node_tree)
        except Exception as e:
            # one mangled tree must not abort the remaining steps/worlds
            error_handlers(None, "while updating world {!r}: {}".format(world.name, e))
    world["dynamic_sky_version"] = SKY_VERSION
    try:
        # Files saved before the stored mode existed: derive it once
        sync_background_mode(world)
    except AttributeError:
        pass  # properties not registered (mid-unregister)


@persistent
def _migrate_all(*_args):
    # Registered as both load_post handler and one-shot timer
    for world in bpy.data.worlds:
        migrate(world)


class DYNSKY_OT_use_world(Operator):
    bl_idname = "dynsky.use_world"
    bl_label = "Use Dynamic Sky World"
    bl_description = "Make this Dynamic Sky world the active world of the scene"

    name: StringProperty()

    def execute(self, context):
        world = bpy.data.worlds.get(self.name)
        if world is None:
            self.report({'WARNING'}, "World {!r} not found".format(self.name))
            return {'CANCELLED'}
        context.scene.world = world
        return {'FINISHED'}


class DYNSKY_OT_migrate(Operator):
    bl_idname = "dynsky.migrate"
    bl_label = "Update Sky"
    bl_description = ("Upgrade this Dynamic Sky world's node tree to the current\n"
                      "version, adding any controls it is missing")

    def execute(self, context):
        migrate(context.scene.world)
        return {'FINISHED'}


def check_world_name(name_id="Dynamic"):
    # check if the new name pattern is in world data
    name_list = []
    suffix = 1
    try:
        name_list = [world.name for world in bpy.data.worlds if name_id in world.name]
        new_name = "{}_{}".format(name_id, len(name_list) + suffix)
        if new_name in name_list:
            # KISS failed - numbering is not sequential
            # try harvesting numbers in world names, find the rightmost ones
            test_num = []
            from re import findall
            for words in name_list:
                test_num.append(findall(r"\d+", words))

            suffix += max([int(l[-1]) for l in test_num])
            new_name = "{}_{}".format(name_id, suffix)
        return new_name
    except Exception as e:
        error_handlers(False, e)
        pass
    return name_id


def check_cycles():
    return ('cycles' in bpy.context.preferences.addons.keys())


def build_render_scene(world, filepath, width, height, samples=8, equirect=False):
    # Throwaway scene rendering the world alone: never touches the user's
    # scene or render settings. PNG bakes the view transform in (thumbnails);
    # EXR stays scene-linear (environment maps). Requires the Cycles addon.
    from math import atan2, degrees, radians, sqrt
    scene = bpy.data.scenes.new("_dynsky_render")
    cam_data = bpy.data.cameras.new("_dynsky_cam")
    cam = bpy.data.objects.new("_dynsky_cam", cam_data)
    try:
        scene.world = world
        scene.collection.objects.link(cam)
        scene.camera = cam
        # Look at the horizon; ponytail: the equirect Z rotation is one
        # visual calibration away if the baked sun azimuth reads shifted
        cam.rotation_euler = (radians(90.0), 0.0,
                              radians(-90.0) if equirect else 0.0)
        if equirect:
            cam_data.type = 'PANO'
            cam_data.panorama_type = 'EQUIRECTANGULAR'
        else:
            # Thumbnails aim at the shader sun, tilted a little upward, so
            # the tile shows sun and sky instead of the below-horizon half
            ball = (world.node_tree.nodes.get("Sky_normal")
                    if world.node_tree else None)
            if ball is not None:
                x, y, z = ball.outputs[0].default_value
                if x or y or z:
                    tilt = min(max(degrees(atan2(z, sqrt(x * x + y * y))), 10.0), 60.0)
                    cam.rotation_euler = (radians(90.0 + tilt), 0.0, -atan2(x, y))
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = samples
        scene.render.resolution_x = width
        scene.render.resolution_y = height
        scene.render.resolution_percentage = 100
        if not equirect:
            # Punchier than AgX at 128px; EXR output ignores the view transform
            scene.view_settings.view_transform = 'Standard'
        scene.render.image_settings.file_format = 'OPEN_EXR' if equirect else 'PNG'
        scene.render.filepath = filepath
    except Exception:
        free_render_scene(scene, cam, cam_data)
        raise
    return scene, cam, cam_data


def free_render_scene(scene, cam, cam_data):
    bpy.data.scenes.remove(scene)
    bpy.data.objects.remove(cam)
    bpy.data.cameras.remove(cam_data)


def render_world_to_file(world, filepath, width, height, samples=8, equirect=False):
    scene, cam, cam_data = build_render_scene(world, filepath, width, height,
                                              samples, equirect)
    try:
        bpy.ops.render.render(write_still=True, scene=scene.name)
    finally:
        free_render_scene(scene, cam, cam_data)


# One interactive sky render (bake or HDRI export) at a time; it runs as a
# native render job so the UI stays alive, and these handlers pick the
# result up when it lands. state["on_done"]/state["on_cancel"] carry the
# per-job follow-up work.
_render_job = None


def _bake_apply(world, filepath):
    # Load the finished EXR and switch the background over to it
    name = "{:s}_bake".format(world.name)
    stale = bpy.data.images.get(name)
    if stale is not None:
        bpy.data.images.remove(stale)
    image = bpy.data.images.load(filepath)
    image.name = name
    image.pack()  # survives without the temp file
    world.node_tree.nodes["Environment_Texture"].image = image
    # Clouds stay baked into the image, so the overlay stays off
    world.node_tree.nodes["Sky_HDRI_blend"].inputs[0].default_value = 1.0
    sync_background_mode(world)
    return name


def _bake_restore(state):
    # Put the blend/overlay sockets back the way the bake found them
    try:
        nodes = state["world"].node_tree.nodes
        blend = nodes.get("Sky_HDRI_blend")
        clouds_over = nodes.get("Clouds_over_HDRI")
        if blend is not None:
            blend.inputs[0].default_value = state["old_blend"]
        if clouds_over is not None:
            clouds_over.inputs[0].default_value = state["old_over"]
    except ReferenceError:
        pass  # world died mid-bake (file load, undo); nothing to restore


def _render_take(*args):
    # Claim the running job if this handler call is about our temp scene;
    # other renders finishing must not trigger our finalizer
    global _render_job
    state = _render_job
    if state is None:
        return None
    if args and getattr(args[0], "name", "") != state["scene"].name:
        return None
    _render_job = None
    for handlers, fn in ((bpy.app.handlers.render_complete, _render_complete),
                         (bpy.app.handlers.render_cancel, _render_cancel)):
        if fn in handlers:
            handlers.remove(fn)
    try:
        free_render_scene(state["scene"], state["cam"], state["cam_data"])
    except ReferenceError:
        pass
    return state


def _render_complete(*args):
    state = _render_take(*args)
    if state is not None:
        state["on_done"](state)


def _render_cancel(*args):
    state = _render_take(*args)
    if state is not None:
        state["on_cancel"](state)


def _start_render_job(state, scene):
    # The caller built the throwaway scene; hand it to the render job system
    global _render_job
    _render_job = state
    bpy.app.handlers.render_complete.append(_render_complete)
    bpy.app.handlers.render_cancel.append(_render_cancel)
    result = bpy.ops.render.render('INVOKE_DEFAULT', write_still=True,
                                   scene=scene.name)
    if 'CANCELLED' in result:
        _render_cancel(scene)
        return False
    return True


def _bake_done(state):
    try:
        name = _bake_apply(state["world"], state["filepath"])
        print("[Dynamic Sky] Baked sky to image {!r}".format(name))
    except Exception as e:
        _bake_restore(state)
        print("[Dynamic Sky] Bake to World failed: {}".format(e))


class DYNSKY_OT_bake_world(Operator):
    bl_idname = "dynsky.bake_world"
    bl_label = "Bake to World"
    bl_description = ("Render the procedural sky to an equirectangular HDR\n"
                      "image and switch the background over to it")
    bl_options = {'REGISTER', 'UNDO'}

    resolution: IntProperty(name="Width", default=2048, min=64, max=16384,
                            description="Baked image width (height is half)")
    samples: IntProperty(name="Samples", default=32, min=1, max=4096)

    @classmethod
    def poll(cls, context):
        # No presets.py import here: presets.py imports sky.py
        world = context.scene.world
        return bool(check_cycles() and world and world.node_tree
                    and "Sky_normal" in world.node_tree.nodes)

    def execute(self, context):
        import os
        world = context.scene.world
        nodes = world.node_tree.nodes
        env = nodes.get("Environment_Texture")
        blend = nodes.get("Sky_HDRI_blend")
        if env is None or blend is None:
            self.report({'WARNING'}, "This sky is missing its HDRI nodes; run Update Sky")
            return {'CANCELLED'}
        if _render_job is not None:
            self.report({'INFO'}, "A sky render is already running")
            return {'CANCELLED'}
        clouds_over = nodes.get("Clouds_over_HDRI")
        old_blend = blend.inputs[0].default_value
        old_over = clouds_over.inputs[0].default_value if clouds_over else 0.0
        # Bake the pure procedural look: no HDRI feedback, no doubled clouds
        blend.inputs[0].default_value = 0.0
        if clouds_over:
            clouds_over.inputs[0].default_value = 0.0
        filepath = os.path.join(bpy.app.tempdir, "{:s}_bake.exr".format(world.name))
        state = {"world": world, "filepath": filepath,
                 "old_blend": old_blend, "old_over": old_over,
                 "on_done": _bake_done, "on_cancel": _bake_restore}

        if bpy.app.background:
            # No event loop headless; render synchronously as before
            try:
                render_world_to_file(world, filepath, self.resolution,
                                     self.resolution // 2, self.samples,
                                     equirect=True)
                name = _bake_apply(world, filepath)
            except Exception as e:
                _bake_restore(state)
                error_handlers(self, e, "Bake to World failed")
                return {'CANCELLED'}
            self.report({'INFO'}, "Baked sky to image {!r}".format(name))
            return {'FINISHED'}

        # Interactive: hand the render to Blender's job system so the UI
        # stays responsive; progress and Esc work like any other render
        try:
            scene, cam, cam_data = build_render_scene(
                world, filepath, self.resolution, self.resolution // 2,
                self.samples, equirect=True)
        except Exception as e:
            _bake_restore(state)
            error_handlers(self, e, "Bake to World failed")
            return {'CANCELLED'}
        state.update(scene=scene, cam=cam, cam_data=cam_data)
        if not _start_render_job(state, scene):
            self.report({'WARNING'}, "Could not start the bake render")
            return {'CANCELLED'}
        self.report({'INFO'}, "Baking sky in the background...")
        return {'FINISHED'}


class DYNSKY_OT_export_hdri(Operator):
    bl_idname = "dynsky.export_hdri"
    bl_label = "Export HDRI"
    bl_description = ("Render the sky as seen to an equirectangular .exr\n"
                      "file, for game engines and other applications")

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.exr", options={'HIDDEN'})
    resolution: IntProperty(name="Width", default=2048, min=64, max=16384,
                            description="Image width (height is half)")
    samples: IntProperty(name="Samples", default=32, min=1, max=4096)

    @classmethod
    def poll(cls, context):
        return DYNSKY_OT_bake_world.poll(context)

    def invoke(self, context, event):
        self.filepath = "{:s}_sky.exr".format(context.scene.world.name)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.filepath.lower().endswith(".exr"):
            self.filepath += ".exr"
        # WYSIWYG: unlike the bake, HDRI blend and cloud overlay stay as set
        if bpy.app.background:
            # No event loop headless; render synchronously as before
            try:
                render_world_to_file(context.scene.world, self.filepath,
                                     self.resolution, self.resolution // 2,
                                     self.samples, equirect=True)
            except Exception as e:
                error_handlers(self, e, "Export HDRI failed")
                return {'CANCELLED'}
            self.report({'INFO'}, "Exported sky to {:s}".format(self.filepath))
            return {'FINISHED'}

        if _render_job is not None:
            self.report({'INFO'}, "A sky render is already running")
            return {'CANCELLED'}
        # The job's write_still saves the EXR itself; nothing to load back
        # and nothing to restore on cancel
        try:
            scene, cam, cam_data = build_render_scene(
                context.scene.world, self.filepath, self.resolution,
                self.resolution // 2, self.samples, equirect=True)
        except Exception as e:
            error_handlers(self, e, "Export HDRI failed")
            return {'CANCELLED'}
        filepath = self.filepath
        state = {"scene": scene, "cam": cam, "cam_data": cam_data,
                 "on_done": lambda s: print(
                     "[Dynamic Sky] Exported sky to {:s}".format(filepath)),
                 "on_cancel": lambda s: None}
        if not _start_render_job(state, scene):
            self.report({'WARNING'}, "Could not start the export render")
            return {'CANCELLED'}
        self.report({'INFO'}, "Exporting sky in the background...")
        return {'FINISHED'}


class dsky(Operator):
    bl_idname = "sky.dyn"
    bl_label = "Make a Procedural sky"
    bl_description = "Make a Procedural Sky with parameters in the 3D View"

    def get_node_types(self, node_tree, node_type):
        for node in node_tree.nodes:
            if node.type == node_type:
                return node
        return None

    def execute(self, context):
        world = None
        try:
            get_name = check_world_name()
            context.scene.dynamic_sky_name = get_name

            world = bpy.data.worlds.new(get_name)
            if check_cycles():
                # 3.5 replaced the sample_as_light toggle with a sampling_method
                # enum; world.cycles raises when the Cycles addon is disabled
                world.cycles.sampling_method = 'MANUAL'
                world.cycles.sample_map_resolution = 2048
            # Eevee extracts a virtual sun from the world above this radiance
            # threshold (W/m^2); set explicitly so the sun disc casts light
            world.sun_threshold = 10.0
            if bpy.app.version < (5, 0, 0):
                # 5.0 always creates the node tree; use_nodes goes away in 6.0
                world.use_nodes = True

            nt = world.node_tree
            # Note: (see T52714) to avoid string localization problems, assign the name for
            # nodes that will be exposed in the 3D view (pattern UI name with underscore)
            bg = self.get_node_types(nt, "BACKGROUND")
            bg.name = "Scene_Brightness"
            bg.inputs[0].default_value[:3] = (0.5, .1, 0.6)
            bg.inputs[1].default_value = 1
            bg.location = (6708.3, 360)

            ntl = nt.links.new
            tcor = nt.nodes.new(type="ShaderNodeTexCoord")
            tcor.location = (243.729, 1005)

            map1 = nt.nodes.new(type="ShaderNodeMapping")
            map1.vector_type = 'NORMAL'
            map1.location = (786.54, 730)

            nor = nt.nodes.new(type="ShaderNodeNormal")
            nor.name = "Sky_normal"
            nor.location = (1220.16, 685)

            cr1 = nt.nodes.new(type="ShaderNodeValToRGB")
            cr1.color_ramp.elements[0].position = 0.969
            cr1.color_ramp.interpolation = 'EASE'
            cr1.location = (1671.33, 415)
            cr2 = nt.nodes.new(type="ShaderNodeValToRGB")
            cr2.color_ramp.elements[0].position = 0.991
            cr2.color_ramp.elements[1].position = 1
            cr2.color_ramp.interpolation = 'EASE'
            cr2.location = (2196.6, 415)
            cr3 = nt.nodes.new(type="ShaderNodeValToRGB")
            cr3.color_ramp.elements[0].position = 0.779
            cr3.color_ramp.elements[1].position = 1
            cr3.color_ramp.interpolation = 'EASE'
            cr3.location = (2196.6, 415)

            mat1 = nt.nodes.new(type="ShaderNodeMath")
            mat1.operation = 'MULTIPLY'
            mat1.inputs[1].default_value = 0.2
            mat1.location = (2196.6, 685)
            mat2 = nt.nodes.new(type="ShaderNodeMath")
            mat2.operation = 'MULTIPLY'
            mat2.inputs[1].default_value = 2
            mat2.location = (3294, 685)
            mat3 = nt.nodes.new(type="ShaderNodeMath")
            mat3.operation = 'MULTIPLY'
            mat3.inputs[1].default_value = 40.9
            mat3.location = (2745.24, 415)
            mat4 = nt.nodes.new(type="ShaderNodeMath")
            mat4.operation = 'SUBTRACT'
            mat4.inputs[1].default_value = 1
            mat4.location = (3294, 415)
            ntl(mat2.inputs[0], mat1.outputs[0])
            ntl(mat4.inputs[0], mat3.outputs[0])
            ntl(mat1.inputs[0], cr3.outputs[0])
            ntl(mat3.inputs[0], cr2.outputs[0])

            soft = nt.nodes.new(type="ShaderNodeMixRGB")
            soft.name = "Soft_hard"
            soft.location = (3819.3, 550)
            soft_1 = nt.nodes.new(type="ShaderNodeMixRGB")
            soft_1.location = (3819.3, 185)
            soft.inputs[0].default_value = 1
            soft_1.inputs[0].default_value = 0.466
            ntl(soft.inputs[1], mat2.outputs[0])
            ntl(soft.inputs[2], mat4.outputs[0])
            ntl(soft_1.inputs[1], mat2.outputs[0])
            ntl(soft_1.inputs[2], cr2.outputs[0])

            mix1 = nt.nodes.new(type="ShaderNodeMixRGB")
            mix1.blend_type = 'MULTIPLY'
            mix1.inputs[0].default_value = 1
            mix1.location = (4344.3, 630)
            mix1_1 = nt.nodes.new(type="ShaderNodeMixRGB")
            mix1_1.blend_type = 'MULTIPLY'
            mix1_1.inputs[0].default_value = 1
            mix1_1.location = (4344.3, 90)

            mix2 = nt.nodes.new(type="ShaderNodeMixRGB")
            mix2.location = (4782, 610)
            mix2_1 = nt.nodes.new(type="ShaderNodeMixRGB")
            mix2_1.location = (5131.8, 270)
            mix2.inputs[1].default_value = (0, 0, 0, 1)
            mix2.inputs[2].default_value = (32, 22, 14, 200)
            mix2_1.inputs[1].default_value = (0, 0, 0, 1)
            mix2_1.inputs[2].default_value = (1, 0.820, 0.650, 1)

            ntl(mix1.inputs[1], soft.outputs[0])
            ntl(mix1_1.inputs[1], soft_1.outputs[0])
            ntl(mix2.inputs[0], mix1.outputs[0])
            ntl(mix2_1.inputs[0], mix1_1.outputs[0])

            gam = nt.nodes.new(type="ShaderNodeGamma")
            gam.inputs[1].default_value = 2.3
            gam.location = (5131.8, 610)

            gam2 = nt.nodes.new(type="ShaderNodeGamma")
            gam2.name = "Sun_value"
            gam2.inputs[1].default_value = 1
            gam2.location = (5524.5, 610)

            gam3 = nt.nodes.new(type="ShaderNodeGamma")
            gam3.name = "Shadow_color_saturation"
            gam3.inputs[1].default_value = 1
            gam3.location = (5524.5, 880)

            sunopa = nt.nodes.new(type="ShaderNodeMixRGB")
            sunopa.blend_type = 'ADD'
            sunopa.inputs[0].default_value = 1
            sunopa.location = (5940.6, 610)
            sunopa_1 = nt.nodes.new(type="ShaderNodeMixRGB")
            sunopa_1.blend_type = 'ADD'
            sunopa_1.inputs[0].default_value = 1
            sunopa_1.location = (5524.5, 340)

            combine = nt.nodes.new(type="ShaderNodeMixRGB")
            combine.location = (6313.8, 360)
            ntl(combine.inputs[1], sunopa.outputs[0])
            ntl(combine.inputs[2], sunopa_1.outputs[0])
            lp = nt.nodes.new(type="ShaderNodeLightPath")
            lp.location = (5940.6, 130)
            ntl(combine.inputs[0], lp.outputs[0])

            ntl(gam2.inputs[0], gam.outputs[0])
            ntl(gam.inputs[0], mix2.outputs[0])
            ntl(bg.inputs[0], combine.outputs[0])

            map2 = nt.nodes.new(type="ShaderNodeMapping")
            map2.inputs['Scale'].default_value[2] = 6.00
            map2.inputs['Scale'].default_value[0] = 1.5
            map2.inputs['Scale'].default_value[1] = 1.5
            map2.location = (2196.6, 1510)

            n1 = nt.nodes.new(type="ShaderNodeTexNoise")
            n1.inputs['Scale'].default_value = 3.8
            n1.inputs['Detail'].default_value = 2.4
            n1.inputs['Distortion'].default_value = 0.5
            n1.location = (2745.24, 1780)

            n2 = nt.nodes.new(type="ShaderNodeTexNoise")
            n2.inputs['Scale'].default_value = 2.0
            n2.inputs['Detail'].default_value = 10
            n2.inputs['Distortion'].default_value = 0.2
            n2.location = (2745.24, 1510)

            ntl(n2.inputs[0], map2.outputs[0])
            ntl(n1.inputs[0], map2.outputs[0])

            sc1 = nt.nodes.new(type="ShaderNodeValToRGB")
            sc1.location = (3294, 1780)
            sc2 = nt.nodes.new(type="ShaderNodeValToRGB")
            sc2.location = (3294, 1510)
            sc3 = nt.nodes.new(type="ShaderNodeValToRGB")
            sc3.location = (3819.3, 820)
            sc3_1 = nt.nodes.new(type="ShaderNodeValToRGB")
            sc3_1.location = (4344.3, 1360)
            sc4 = nt.nodes.new(type="ShaderNodeValToRGB")
            sc4.location = (3819.3, 1090)

            sc1.color_ramp.elements[1].position = 0.649
            sc1.color_ramp.elements[0].position = 0.408

            sc2.color_ramp.elements[1].position = 0.576
            sc2.color_ramp.elements[0].position = 0.408

            sc3.color_ramp.elements.new(0.5)
            sc3.color_ramp.elements[2].position = 0.435

            sc3.color_ramp.elements[1].position = 0.160
            sc3.color_ramp.elements[0].position = 0.027

            sc3.color_ramp.elements[1].color = (1, 1, 1, 1)
            sc3.color_ramp.elements[0].color = (0.419, 0.419, 0.419, 0.419)

            sc3.color_ramp.elements[0].position = 0.0
            sc4.color_ramp.elements[0].position = 0.0
            sc4.color_ramp.elements[1].position = 0.469
            sc4.color_ramp.elements[1].color = (0, 0, 0, 1)
            sc4.color_ramp.elements[0].color = (1, 1, 0.917412, 1)

            sc3_1.color_ramp.elements.new(0.5)
            sc3_1.color_ramp.elements[2].position = 0.435

            sc3_1.color_ramp.elements[1].position = 0.187
            sc3_1.color_ramp.elements[1].color = (1, 1, 1, 1)
            sc3_1.color_ramp.elements[0].color = (0, 0, 0, 0)
            sc3_1.color_ramp.elements[0].position = 0.0

            smix1 = nt.nodes.new(type="ShaderNodeMixRGB")
            smix1.location = (3819.3, 1550)
            smix1.name = "Cloud_color"
            smix2 = nt.nodes.new(type="ShaderNodeMixRGB")
            smix2.location = (4344.3, 1630)
            smix2.name = "Cloud_density"
            smix2_1 = nt.nodes.new(type="ShaderNodeMixRGB")
            smix2_1.location = (4782, 1360)

            smix3 = nt.nodes.new(type="ShaderNodeMixRGB")
            smix3.location = (4344.3, 1090)
            smix3.name = "Sky_and_Horizon_colors"

            smix4 = nt.nodes.new(type="ShaderNodeMixRGB")
            smix4.location = (4782, 880)

            smix5 = nt.nodes.new(type="ShaderNodeMixRGB")
            smix5.name = "Cloud_opacity"
            smix5.location = (5131.8, 880)

            smix1.inputs[1].default_value = (1, 1, 1, 1)
            smix1.inputs[2].default_value = (0, 0, 0, 1)
            smix2.inputs[0].default_value = 0.267
            smix2.blend_type = 'MULTIPLY'
            smix2_1.inputs[0].default_value = 1
            smix2_1.blend_type = 'MULTIPLY'

            smix3.inputs[1].default_value = (0.434, 0.838, 1, 1)
            smix3.inputs[2].default_value = (0.962, 0.822, 0.822, 1)
            smix4.blend_type = 'MULTIPLY'
            smix4.inputs[0].default_value = 1
            smix5.blend_type = 'SCREEN'
            smix5.inputs[0].default_value = 1

            srgb = nt.nodes.new(type="ShaderNodeSeparateColor")
            srgb.location = (786.54, 1370)
            aniadd = nt.nodes.new(type="ShaderNodeMath")
            aniadd.location = (1220.16, 1235)
            crgb = nt.nodes.new(type="ShaderNodeCombineColor")
            crgb.location = (1671.33, 1510)
            sunrgb = nt.nodes.new(type="ShaderNodeMixRGB")
            sunrgb.name = "Sun_color"

            sunrgb.blend_type = 'MULTIPLY'
            sunrgb.inputs[2].default_value = (32, 30, 30, 200)
            sunrgb.inputs[0].default_value = 1
            sunrgb.location = (4344.3, 360)

            ntl(mix2.inputs[2], sunrgb.outputs[0])

            ntl(smix1.inputs[0], sc2.outputs[0])
            ntl(smix2.inputs[1], smix1.outputs[0])
            ntl(smix2.inputs[2], sc1.outputs[0])
            ntl(smix2_1.inputs[2], sc3_1.outputs[0])
            ntl(smix3.inputs[0], sc4.outputs[0])
            ntl(smix4.inputs[2], smix3.outputs[0])
            ntl(smix4.inputs[1], sc3.outputs[0])
            ntl(smix5.inputs[1], smix4.outputs[0])
            ntl(smix2_1.inputs[1], smix2.outputs[0])
            ntl(smix5.inputs[2], smix2_1.outputs[0])
            ntl(sunopa.inputs[1], gam3.outputs[0])
            ntl(gam3.inputs[0], smix5.outputs[0])
            ntl(mix1.inputs[2], sc3.outputs[0])
            ntl(sunopa.inputs[2], gam2.outputs[0])

            ntl(sc1.inputs[0], n1.outputs['Fac'])
            ntl(sc2.inputs[0], n2.outputs['Fac'])

            skynor = nt.nodes.new(type="ShaderNodeNormal")
            skynor.location = (3294, 1070)

            ntl(sc3.inputs[0], skynor.outputs[1])
            ntl(sc4.inputs[0], skynor.outputs[1])
            ntl(sc3_1.inputs[0], skynor.outputs[1])
            ntl(map2.inputs[0], crgb.outputs[0])
            ntl(skynor.inputs[0], tcor.outputs[0])
            ntl(mix1_1.inputs[2], sc3.outputs[0])
            ntl(srgb.inputs[0], tcor.outputs[0])
            ntl(crgb.inputs[1], srgb.outputs[1])
            ntl(crgb.inputs[2], srgb.outputs[2])
            ntl(aniadd.inputs[1], srgb.outputs[0])
            ntl(crgb.inputs[0], aniadd.outputs[0])

            ntl(cr1.inputs[0], nor.outputs[1])
            ntl(cr2.inputs[0], cr1.outputs[0])
            ntl(cr3.inputs[0], nor.outputs[1])
            ntl(nor.inputs[0], map1.outputs[0])
            ntl(map1.inputs[0], tcor.outputs[0])
            ntl(sunopa_1.inputs[1], smix5.outputs[0])
            ntl(sunopa_1.inputs[2], mix2_1.outputs[0])

            world_out = self.get_node_types(nt, "OUTPUT_WORLD")
            world_out.location = (7167.3, 360)

            _add_hdri(nt)
            _add_horizon(nt)
            _add_night(nt)
            _name_cloud_drift(nt)
            _add_clouds(nt)
            _add_temperature(nt)
            _add_hdri_rotation(nt)
            _add_clouds_over(nt)
            _add_star_size(nt)

            world["dynamic_sky_version"] = SKY_VERSION

        except Exception as e:
            error_handlers(self, e, "Make a Procedural sky has failed")

            # don't leave a half-built world behind
            if world is not None and world.users == 0:
                bpy.data.worlds.remove(world)
            return {"CANCELLED"}

        context.scene.world = world
        return {'FINISHED'}
