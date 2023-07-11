# SPDX-FileCopyrightText: 2021-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""With respect to camera frame and optics distortions, also export environment

with world, sky, atmospheric effects such as rainbows or smoke """

import bpy

import os
from imghdr import what  # imghdr is a python lib to identify image file types
from math import atan, pi, sqrt, degrees
from . import voxel_lib  # for smoke rendering
from .model_primitives import write_object_modifiers


# -------- find image texture # used for export_world -------- #


def image_format(img_f):
    """Identify input image filetypes to transmit to POV."""
    # First use the below explicit extensions to identify image file prospects
    ext = {
        "JPG": "jpeg",
        "JPEG": "jpeg",
        "GIF": "gif",
        "TGA": "tga",
        "IFF": "iff",
        "PPM": "ppm",
        "PNG": "png",
        "SYS": "sys",
        "TIFF": "tiff",
        "TIF": "tiff",
        "EXR": "exr",
        "HDR": "hdr",
    }.get(os.path.splitext(img_f)[-1].upper(), "")
    # Then, use imghdr to really identify the filetype as it can be different
    if not ext:
        # maybe add a check for if path exists here?
        print(" WARNING: texture image has no extension")  # too verbose

        ext = what(img_f)  # imghdr is a python lib to identify image file types
    return ext


def img_map(ts):
    """Translate mapping type from Blender UI to POV syntax and return that string."""
    image_map = ""
    texdata = bpy.data.textures[ts.texture]
    if ts.mapping == "FLAT":
        image_map = "map_type 0 "
    elif ts.mapping == "SPHERE":
        image_map = "map_type 1 "
    elif ts.mapping == "TUBE":
        image_map = "map_type 2 "

    # map_type 3 and 4 in development (?) (ENV in pov 3.8)
    # for POV-Ray, currently they just seem to default back to Flat (type 0)
    # elif ts.mapping=="?":
    #    image_map = " map_type 3 "
    # elif ts.mapping=="?":
    #    image_map = " map_type 4 "
    if ts.use_interpolation:  # Available if image sampling class reactivated?
        image_map += " interpolate 2 "
    if texdata.extension == "CLIP":
        image_map += " once "
    # image_map += "}"
    # if ts.mapping=='CUBE':
    #    image_map+= "warp { cubic } rotate <-90,0,180>"
    # no direct cube type mapping. Though this should work in POV 3.7
    # it doesn't give that good results(best suited to environment maps?)
    # if image_map == "":
    #    print(" No texture image  found ")
    return image_map


def img_map_transforms(ts):
    """Translate mapping transformations from Blender UI to POV syntax and return that string."""
    # XXX TODO: unchecked textures give error of variable referenced before assignment XXX
    # POV-Ray "scale" is not a number of repetitions factor, but ,its
    # inverse, a standard scale factor.
    # 0.5 Offset is needed relatively to scale because center of the
    # scale is 0.5,0.5 in blender and 0,0 in POV
    # Strange that the translation factor for scale is not the same as for
    # translate.
    # TODO: verify both matches with other blender renderers / internal in previous versions.
    image_map_transforms = ""
    image_map_transforms = "scale <%.4g,%.4g,%.4g> translate <%.4g,%.4g,%.4g>" % (
        ts.scale[0],
        ts.scale[1],
        ts.scale[2],
        ts.offset[0],
        ts.offset[1],
        ts.offset[2],
    )
    # image_map_transforms = (" translate <-0.5,-0.5,0.0> scale <%.4g,%.4g,%.4g> translate <%.4g,%.4g,%.4g>" % \
    # ( 1.0 / ts.scale.x,
    # 1.0 / ts.scale.y,
    # 1.0 / ts.scale.z,
    # (0.5 / ts.scale.x) + ts.offset.x,
    # (0.5 / ts.scale.y) + ts.offset.y,
    # ts.offset.z))
    # image_map_transforms = (
    # "translate <-0.5,-0.5,0> "
    # "scale <-1,-1,1> * <%.4g,%.4g,%.4g> "
    # "translate <0.5,0.5,0> + <%.4g,%.4g,%.4g>" % \
    # (1.0 / ts.scale.x,
    # 1.0 / ts.scale.y,
    # 1.0 / ts.scale.z,
    # ts.offset.x,
    # ts.offset.y,
    # ts.offset.z)
    # )
    return image_map_transforms


def img_map_bg(wts):
    """Translate world mapping from Blender UI to POV syntax and return that string."""
    tex = bpy.data.textures[wts.texture]
    image_mapBG = ""
    # texture_coords refers to the mapping of world textures:
    if wts.texture_coords in ["VIEW", "GLOBAL"]:
        image_mapBG = " map_type 0 "
    elif wts.texture_coords == "ANGMAP":
        image_mapBG = " map_type 1 "
    elif wts.texture_coords == "TUBE":
        image_mapBG = " map_type 2 "

    if tex.use_interpolation:
        image_mapBG += " interpolate 2 "
    if tex.extension == "CLIP":
        image_mapBG += " once "
    # image_mapBG += "}"
    # if wts.mapping == 'CUBE':
    #   image_mapBG += "warp { cubic } rotate <-90,0,180>"
    # no direct cube type mapping. Though this should work in POV 3.7
    # it doesn't give that good results(best suited to environment maps?)
    # if image_mapBG == "":
    #    print(" No background texture image  found ")
    return image_mapBG


def path_image(image):
    """Conform a path string to POV syntax to avoid POV errors."""
    return bpy.path.abspath(image.filepath, library=image.library).replace("\\", "/")
    # .replace("\\","/") to get only forward slashes as it's what POV prefers,
    # even on windows


# end find image texture
# -----------------------------------------------------------------------------


def export_camera(file, scene, global_matrix, render, tab_write):
    """Translate camera from Blender UI to POV syntax and write to exported file."""
    camera = scene.camera

    # DH disabled for now, this isn't the correct context
    active_object = None  # bpy.context.active_object # does not always work  MR
    matrix = global_matrix @ camera.matrix_world
    focal_point = camera.data.dof.focus_distance

    # compute resolution
    q_size = render.resolution_x / render.resolution_y
    tab_write(file, "#declare camLocation  = <%.6f, %.6f, %.6f>;\n" % matrix.translation[:])
    tab_write(
        file,
        (
            "#declare camLookAt = <%.6f, %.6f, %.6f>;\n"
            % tuple(degrees(e) for e in matrix.to_3x3().to_euler())
        ),
    )

    tab_write(file, "camera {\n")
    if scene.pov.baking_enable and active_object and active_object.type == "MESH":
        tab_write(file, "mesh_camera{ 1 3\n")  # distribution 3 is what we want here
        tab_write(file, "mesh{%s}\n" % active_object.name)
        tab_write(file, "}\n")
        tab_write(file, "location <0,0,.01>")
        tab_write(file, "direction <0,0,-1>")

    else:
        if camera.data.type == "ORTHO":
            # XXX todo: track when SensorHeightRatio was added to see if needed (not used)
            sensor_height_ratio = (
                render.resolution_x * camera.data.ortho_scale / render.resolution_y
            )
            tab_write(file, "orthographic\n")
            # Blender angle is radian so should be converted to degrees:
            # % (camera.data.angle * (180.0 / pi) )
            # but actually argument is not compulsory after angle in pov ortho mode
            tab_write(file, "angle\n")
            tab_write(file, "right <%6f, 0, 0>\n" % -camera.data.ortho_scale)
            tab_write(file, "location  <0, 0, 0>\n")
            tab_write(file, "look_at  <0, 0, -1>\n")
            tab_write(file, "up <0, %6f, 0>\n" % (camera.data.ortho_scale / q_size))

        elif camera.data.type == "PANO":
            tab_write(file, "panoramic\n")
            tab_write(file, "location  <0, 0, 0>\n")
            tab_write(file, "look_at  <0, 0, -1>\n")
            tab_write(file, "right <%s, 0, 0>\n" % -q_size)
            tab_write(file, "up <0, 1, 0>\n")
            tab_write(file, "angle  %f\n" % (360.0 * atan(16.0 / camera.data.lens) / pi))
        elif camera.data.type == "PERSP":
            # Standard camera otherwise would be default in pov
            tab_write(file, "location  <0, 0, 0>\n")
            tab_write(file, "look_at  <0, 0, -1>\n")
            tab_write(file, "right <%s, 0, 0>\n" % -q_size)
            tab_write(file, "up <0, 1, 0>\n")
            tab_write(
                file,
                "angle  %f\n"
                % (2 * atan(camera.data.sensor_width / 2 / camera.data.lens) * 180.0 / pi),
            )

        tab_write(
            file,
            "rotate  <%.6f, %.6f, %.6f>\n" % tuple(degrees(e) for e in matrix.to_3x3().to_euler()),
        )

        tab_write(file, "translate <%.6f, %.6f, %.6f>\n" % matrix.translation[:])
        if camera.data.dof.use_dof and (focal_point != 0 or camera.data.dof.focus_object):
            tab_write(
                file, "aperture %.3g\n" % (1 / (camera.data.dof.aperture_fstop * 10000) * 1000)
            )
            tab_write(
                file,
                "blur_samples %d %d\n"
                % (camera.data.pov.dof_samples_min, camera.data.pov.dof_samples_max),
            )
            tab_write(file, "variance 1/%d\n" % camera.data.pov.dof_variance)
            tab_write(file, "confidence %.3g\n" % camera.data.pov.dof_confidence)
            if camera.data.dof.focus_object:
                focal_ob = scene.objects[camera.data.dof.focus_object.name]
                matrix_blur = global_matrix @ focal_ob.matrix_world
                tab_write(file, "focal_point <%.4f,%.4f,%.4f>\n" % matrix_blur.translation[:])
            else:
                tab_write(file, "focal_point <0, 0, %f>\n" % focal_point)
    if camera.data.pov.normal_enable:
        tab_write(
            file,
            "normal {%s %.4f turbulence %.4f scale %.4f}\n"
            % (
                camera.data.pov.normal_patterns,
                camera.data.pov.cam_normal,
                camera.data.pov.turbulence,
                camera.data.pov.scale,
            ),
        )
    tab_write(file, "}\n")


exported_lights_count = 0


def export_lights(lamps, file, scene, global_matrix, tab_write):
    """Translate lights from Blender UI to POV syntax and write to exported file."""

    from .render import write_matrix, tab_write

    # Incremented after each lamp export to declare its target
    # currently used for Fresnel diffuse shader as their slope vector:
    global exported_lights_count
    # Get all lamps and keep their count in a global variable
    for exported_lights_count, ob in enumerate(lamps, start=1):
        lamp = ob.data

        matrix = global_matrix @ ob.matrix_world

        # Color is no longer modified by energy
        # any way to directly get bpy_prop_array as tuple?
        color = tuple(lamp.color)

        tab_write(file, "light_source {\n")
        tab_write(file, "< 0,0,0 >\n")
        tab_write(file, "color srgb<%.3g, %.3g, %.3g>\n" % color)

        if lamp.type == "POINT":
            pass
        elif lamp.type == "SPOT":
            tab_write(file, "spotlight\n")

            # Falloff is the main radius from the centre line
            tab_write(file, "falloff %.2f\n" % (degrees(lamp.spot_size) / 2.0))  # 1 TO 179 FOR BOTH
            tab_write(
                file, "radius %.6f\n" % ((degrees(lamp.spot_size) / 2.0) * (1.0 - lamp.spot_blend))
            )

            # Blender does not have a tightness equivalent, 0 is most like blender default.
            tab_write(file, "tightness 0\n")  # 0:10f

            tab_write(file, "point_at  <0, 0, -1>\n")
            if lamp.pov.use_halo:
                tab_write(file, "looks_like{\n")
                tab_write(file, "sphere{<0,0,0>,%.6f\n" % lamp.shadow_soft_size)
                tab_write(file, "hollow\n")
                tab_write(file, "material{\n")
                tab_write(file, "texture{\n")
                tab_write(file, "pigment{rgbf<1,1,1,%.4f>}\n" % (lamp.pov.halo_intensity * 5.0))
                tab_write(file, "}\n")
                tab_write(file, "interior{\n")
                tab_write(file, "media{\n")
                tab_write(file, "emission 1\n")
                tab_write(file, "scattering {1, 0.5}\n")
                tab_write(file, "density{\n")
                tab_write(file, "spherical\n")
                tab_write(file, "color_map{\n")
                tab_write(file, "[0.0 rgb <0,0,0>]\n")
                tab_write(file, "[0.5 rgb <1,1,1>]\n")
                tab_write(file, "[1.0 rgb <1,1,1>]\n")
                tab_write(file, "}\n")
                tab_write(file, "}\n")
                tab_write(file, "}\n")
                tab_write(file, "}\n")
                tab_write(file, "}\n")
                tab_write(file, "}\n")
                tab_write(file, "}\n")
        elif lamp.type == "SUN":
            tab_write(file, "parallel\n")
            tab_write(file, "point_at  <0, 0, -1>\n")  # *must* be after 'parallel'

        elif lamp.type == "AREA":
            # Area lights have no falloff type, so always use blenders lamp quad equivalent
            # for those?
            tab_write(file, "fade_power %d\n" % 2)
            size_x = lamp.size
            samples_x = lamp.pov.shadow_ray_samples_x
            if lamp.shape == "SQUARE":
                size_y = size_x
                samples_y = samples_x
            else:
                size_y = lamp.size_y
                samples_y = lamp.pov.shadow_ray_samples_y

            tab_write(
                file,
                "area_light <%.6f,0,0>,<0,%.6f,0> %d, %d\n"
                % (size_x, size_y, samples_x, samples_y),
            )
            tab_write(file, "area_illumination\n")
            if lamp.pov.shadow_ray_sample_method == "CONSTANT_JITTERED":
                if lamp.pov.use_jitter:
                    tab_write(file, "jitter\n")
            else:
                tab_write(file, "adaptive 1\n")
                tab_write(file, "jitter\n")

        # No shadow checked either at global or light level:
        if not scene.pov.use_shadows or (lamp.pov.shadow_method == "NOSHADOW"):
            tab_write(file, "shadowless\n")

        # Sun shouldn't be attenuated. Area lights have no falloff attribute so they
        # are put to type 2 attenuation a little higher above.
        if lamp.type not in {"SUN", "AREA"}:
            tab_write(file, "fade_power %d\n" % 2)  # Use blenders lamp quad equivalent

        write_matrix(file, matrix)

        tab_write(file, "}\n")

        # v(A,B) rotates vector A about origin by vector B.
        file.write(
            "#declare lampTarget%s= vrotate(<%.4g,%.4g,%.4g>,<%.4g,%.4g,%.4g>);\n"
            % (
                exported_lights_count,
                -ob.location.x,
                -ob.location.y,
                -ob.location.z,
                ob.rotation_euler.x,
                ob.rotation_euler.y,
                ob.rotation_euler.z,
            )
        )


def export_world(file, world, scene, global_matrix, tab_write):
    """write world as POV background and sky_sphere to exported file"""
    render = scene.pov
    agnosticrender = scene.render
    camera = scene.camera
    # matrix = global_matrix @ camera.matrix_world  # view dependant for later use NOT USED
    if not world:
        return

    # These lines added to get sky gradient (visible with PNG output)

    # For simple flat background:
    if not world.pov.use_sky_blend:
        # No alpha with Sky option:
        if render.alpha_mode == "SKY" and not agnosticrender.film_transparent:
            tab_write(
                file, "background {rgbt<%.3g, %.3g, %.3g, 0>}\n" % (world.pov.horizon_color[:])
            )

        elif render.alpha_mode == "STRAIGHT" or agnosticrender.film_transparent:
            tab_write(
                file, "background {rgbt<%.3g, %.3g, %.3g, 1>}\n" % (world.pov.horizon_color[:])
            )
        else:
            # Non fully transparent background could premultiply alpha and avoid
            # anti-aliasing display issue
            tab_write(
                file,
                "background {rgbft<%.3g, %.3g, %.3g, %.3g, 0>}\n"
                % (
                    world.pov.horizon_color[0],
                    world.pov.horizon_color[1],
                    world.pov.horizon_color[2],
                    render.alpha_filter,
                ),
            )

    world_tex_count = 0
    # For Background image textures
    for t in world.pov_texture_slots:  # risk to write several sky_spheres but maybe ok.
        if t:
            tex = bpy.data.textures[t.texture]
        if tex.type is not None:
            world_tex_count += 1
            # XXX No enable checkbox for world textures yet (report it?)
            # if t and tex.type == 'IMAGE' and t.use:
            if tex.type == "IMAGE":
                image_filename = path_image(tex.image)
                if tex.image.filepath != image_filename:
                    tex.image.filepath = image_filename
                if image_filename != "" and t.use_map_blend:
                    textures_blend = image_filename
                    # colvalue = t.default_value
                    t_blend = t

                # Commented below was an idea to make the Background image oriented as camera
                # taken here:
                # http://news.pov.org/pov.newusers/thread/%3Cweb.4a5cddf4e9c9822ba2f93e20@news.pov.org%3E/
                # Replace 4/3 by the ratio of each image found by some custom or existing
                # function
                # mapping_blend = (" translate <%.4g,%.4g,%.4g> rotate z*degrees" \
                #                "(atan((camLocation - camLookAt).x/(camLocation - " \
                #                "camLookAt).y)) rotate x*degrees(atan((camLocation - " \
                #                "camLookAt).y/(camLocation - camLookAt).z)) rotate y*" \
                #                "degrees(atan((camLocation - camLookAt).z/(camLocation - " \
                #                "camLookAt).x)) scale <%.4g,%.4g,%.4g>b" % \
                #                (t_blend.offset.x / 10 , t_blend.offset.y / 10 ,
                #                 t_blend.offset.z / 10, t_blend.scale.x ,
                #                 t_blend.scale.y , t_blend.scale.z))
                # using camera rotation valuesdirectly from blender seems much easier
                if t_blend.texture_coords == "ANGMAP":
                    mapping_blend = ""
                else:
                    # POV-Ray "scale" is not a number of repetitions factor, but its
                    # inverse, a standard scale factor.
                    # 0.5 Offset is needed relatively to scale because center of the
                    # UV scale is 0.5,0.5 in blender and 0,0 in POV
                    # Further Scale by 2 and translate by -1 are
                    # required for the sky_sphere not to repeat

                    mapping_blend = (
                        "scale 2 scale <%.4g,%.4g,%.4g> translate -1 "
                        "translate <%.4g,%.4g,%.4g> rotate<0,0,0> "
                        % (
                            (1.0 / t_blend.scale.x),
                            (1.0 / t_blend.scale.y),
                            (1.0 / t_blend.scale.z),
                            0.5 - (0.5 / t_blend.scale.x) - t_blend.offset.x,
                            0.5 - (0.5 / t_blend.scale.y) - t_blend.offset.y,
                            t_blend.offset.z,
                        )
                    )

                    # The initial position and rotation of the pov camera is probably creating
                    # the rotation offset should look into it someday but at least background
                    # won't rotate with the camera now.
                # Putting the map on a plane would not introduce the skysphere distortion and
                # allow for better image scale matching but also some waay to chose depth and
                # size of the plane relative to camera.
                tab_write(file, "sky_sphere {\n")
                tab_write(file, "pigment {\n")
                tab_write(
                    file,
                    'image_map{%s "%s" %s}\n'
                    % (image_format(textures_blend), textures_blend, img_map_bg(t_blend)),
                )
                tab_write(file, "}\n")
                tab_write(file, "%s\n" % mapping_blend)
                # The following layered pigment opacifies to black over the texture for
                # transmit below 1 or otherwise adds to itself
                tab_write(file, "pigment {rgb 0 transmit %s}\n" % tex.intensity)
                tab_write(file, "}\n")
                # tab_write(file, "scale 2\n")
                # tab_write(file, "translate -1\n")

    # For only Background gradient

    if world_tex_count == 0 and world.pov.use_sky_blend:
        tab_write(file, "sky_sphere {\n")
        tab_write(file, "pigment {\n")
        # maybe Should follow the advice of POV doc about replacing gradient
        # for skysphere..5.5
        tab_write(file, "gradient y\n")
        tab_write(file, "color_map {\n")

        if render.alpha_mode == "TRANSPARENT":
            tab_write(
                file,
                "[0.0 rgbft<%.3g, %.3g, %.3g, %.3g, 0>]\n"
                % (
                    world.pov.horizon_color[0],
                    world.pov.horizon_color[1],
                    world.pov.horizon_color[2],
                    render.alpha_filter,
                ),
            )
            tab_write(
                file,
                "[1.0 rgbft<%.3g, %.3g, %.3g, %.3g, 0>]\n"
                % (
                    world.pov.zenith_color[0],
                    world.pov.zenith_color[1],
                    world.pov.zenith_color[2],
                    render.alpha_filter,
                ),
            )
        if agnosticrender.film_transparent or render.alpha_mode == "STRAIGHT":
            tab_write(file, "[0.0 rgbt<%.3g, %.3g, %.3g, 0.99>]\n" % (world.pov.horizon_color[:]))
            # aa premult not solved with transmit 1
            tab_write(file, "[1.0 rgbt<%.3g, %.3g, %.3g, 0.99>]\n" % (world.pov.zenith_color[:]))
        else:
            tab_write(file, "[0.0 rgbt<%.3g, %.3g, %.3g, 0>]\n" % (world.pov.horizon_color[:]))
            tab_write(file, "[1.0 rgbt<%.3g, %.3g, %.3g, 0>]\n" % (world.pov.zenith_color[:]))
        tab_write(file, "}\n")
        tab_write(file, "}\n")
        tab_write(file, "}\n")
        # Sky_sphere alpha (transmit) is not translating into image alpha the same
        # way as 'background'

    # if world.pov.light_settings.use_indirect_light:
    #    scene.pov.radio_enable=1

    # Maybe change the above to a function copyInternalRenderer settings when
    # user pushes a button, then:
    # scene.pov.radio_enable = world.pov.light_settings.use_indirect_light
    # and other such translations but maybe this would not be allowed either?

    # -----------------------------------------------------------------------------

    mist = world.mist_settings

    if mist.use_mist:
        tab_write(file, "fog {\n")
        if mist.falloff == "LINEAR":
            tab_write(file, "distance %.6f\n" % ((mist.start + mist.depth) * 0.368))
        elif mist.falloff in ["QUADRATIC", "INVERSE_QUADRATIC"]:  # n**2 or squrt(n)?
            tab_write(file, "distance %.6f\n" % ((mist.start + mist.depth) ** 2 * 0.368))
        tab_write(
            file,
            "color rgbt<%.3g, %.3g, %.3g, %.3g>\n"
            % (*world.pov.horizon_color, (1.0 - mist.intensity)),
        )
        # tab_write(file, "fog_offset %.6f\n" % mist.start) #create a pov property to prepend
        # tab_write(file, "fog_alt %.6f\n" % mist.height) #XXX right?
        # tab_write(file, "turbulence 0.2\n")
        # tab_write(file, "turb_depth 0.3\n")
        tab_write(file, "fog_type 1\n")  # type2 for height
        tab_write(file, "}\n")
    if scene.pov.media_enable:
        tab_write(file, "media {\n")
        tab_write(
            file,
            "scattering { %d, rgb %.12f*<%.4g, %.4g, %.4g>\n"
            % (
                int(scene.pov.media_scattering_type),
                scene.pov.media_diffusion_scale,
                *(scene.pov.media_diffusion_color[:]),
            ),
        )
        if scene.pov.media_scattering_type == "5":
            tab_write(file, "eccentricity %.3g\n" % scene.pov.media_eccentricity)
        tab_write(file, "}\n")
        tab_write(
            file,
            "absorption %.12f*<%.4g, %.4g, %.4g>\n"
            % (scene.pov.media_absorption_scale, *(scene.pov.media_absorption_color[:])),
        )
        tab_write(file, "\n")
        tab_write(file, "samples %.d\n" % scene.pov.media_samples)
        tab_write(file, "}\n")


# -----------------------------------------------------------------------------
def export_rainbows(rainbows, file, scene, global_matrix, tab_write):
    """write all POV rainbows primitives to exported file"""

    from .render import write_matrix, tab_write

    pov_mat_name = "Default_texture"
    for ob in rainbows:
        povdataname = ob.data.name  # enough? XXX not used nor matrix fn?
        angle = degrees(ob.data.spot_size / 2.5)  # radians in blender (2
        width = ob.data.spot_blend * 10
        distance = ob.data.shadow_buffer_clip_start
        # eps=0.0000001
        # angle = br/(cr+eps) * 10 #eps is small epsilon variable to avoid dividing by zero
        # width = ob.dimensions[2] #now let's say width of rainbow is the actual proxy height
        # formerly:
        # cz-bz # let's say width of the rainbow is height of the cone (interfacing choice

        # v(A,B) rotates vector A about origin by vector B.
        # and avoid a 0 length vector by adding 1

        # file.write("#declare %s_Target= vrotate(<%.6g,%.6g,%.6g>,<%.4g,%.4g,%.4g>);\n" % \
        # (povdataname, -(ob.location.x+0.1), -(ob.location.y+0.1), -(ob.location.z+0.1),
        # ob.rotation_euler.x, ob.rotation_euler.y, ob.rotation_euler.z))

        direction = (  # XXX currently not used (replaced by track to?)
            ob.location.x,
            ob.location.y,
            ob.location.z,
        )  # not taking matrix into account
        rmatrix = global_matrix @ ob.matrix_world

        # ob.rotation_euler.to_matrix().to_4x4() * mathutils.Vector((0,0,1))
        # XXX Is result of the below offset by 90 degrees?
        up = ob.matrix_world.to_3x3()[1].xyz  # * global_matrix

        # XXX TO CHANGE:
        # formerly:
        # tab_write(file, "#declare %s = rainbow {\n"%povdataname)

        # clumsy for now but remove the rainbow from instancing
        # system because not an object. use lamps later instead of meshes

        # del data_ref[dataname]
        tab_write(file, "rainbow {\n")

        tab_write(file, "angle %.4f\n" % angle)
        tab_write(file, "width %.4f\n" % width)
        tab_write(file, "distance %.4f\n" % distance)
        tab_write(file, "arc_angle %.4f\n" % ob.pov.arc_angle)
        tab_write(file, "falloff_angle %.4f\n" % ob.pov.falloff_angle)
        tab_write(file, "direction <%.4f,%.4f,%.4f>\n" % rmatrix.translation[:])
        tab_write(file, "up <%.4f,%.4f,%.4f>\n" % (up[0], up[1], up[2]))
        tab_write(file, "color_map {\n")
        tab_write(file, "[0.000  color srgbt<1.0, 0.5, 1.0, 1.0>]\n")
        tab_write(file, "[0.130  color srgbt<0.5, 0.5, 1.0, 0.9>]\n")
        tab_write(file, "[0.298  color srgbt<0.2, 0.2, 1.0, 0.7>]\n")
        tab_write(file, "[0.412  color srgbt<0.2, 1.0, 1.0, 0.4>]\n")
        tab_write(file, "[0.526  color srgbt<0.2, 1.0, 0.2, 0.4>]\n")
        tab_write(file, "[0.640  color srgbt<1.0, 1.0, 0.2, 0.4>]\n")
        tab_write(file, "[0.754  color srgbt<1.0, 0.5, 0.2, 0.6>]\n")
        tab_write(file, "[0.900  color srgbt<1.0, 0.2, 0.2, 0.7>]\n")
        tab_write(file, "[1.000  color srgbt<1.0, 0.2, 0.2, 1.0>]\n")
        tab_write(file, "}\n")

        # tab_write(file, "texture {%s}\n"%pov_mat_name)
        write_object_modifiers(ob, file)
        # tab_write(file, "rotate x*90\n")
        # matrix = global_matrix @ ob.matrix_world
        # write_matrix(file, matrix)
        tab_write(file, "}\n")
        # continue #Don't render proxy mesh, skip to next object


def export_smoke(file, smoke_obj_name, smoke_path, comments, global_matrix):
    """export Blender smoke type fluids to pov media using df3 library"""

    from .render import write_matrix, tab_write

    flowtype = -1  # XXX todo: not used yet? should trigger emissive for fire type
    depsgraph = bpy.context.evaluated_depsgraph_get()
    smoke_obj = bpy.data.objects[smoke_obj_name].evaluated_get(depsgraph)
    domain = None
    smoke_modifier = None
    # Search smoke domain target for smoke modifiers
    for mod in smoke_obj.modifiers:
        if mod.type == "FLUID":
            if mod.fluid_type == "DOMAIN":
                domain = smoke_obj
                smoke_modifier = mod

            elif mod.fluid_type == "FLOW":
                if mod.flow_settings.flow_type == "BOTH":
                    flowtype = 2
                elif mod.flow_settings.flow_type == "FIRE":
                    flowtype = 1
                elif mod.flow_settings.flow_type == "SMOKE":
                    flowtype = 0
    eps = 0.000001  # XXX not used currently. restore from corner case ... zero div?
    if domain is not None:
        mod_set = smoke_modifier.domain_settings
        channeldata = []
        for v in mod_set.density_grid:
            channeldata.append(v.real)
            print(v.real)
        # -------- Usage in voxel texture:
        # channeldata = []
        # if channel == 'density':
        # for v in mod_set.density_grid:
        # channeldata.append(v.real)

        # if channel == 'fire':
        # for v in mod_set.flame_grid:
        # channeldata.append(v.real)

        resolution = mod_set.resolution_max
        big_res = [
            mod_set.domain_resolution[0],
            mod_set.domain_resolution[1],
            mod_set.domain_resolution[2],
        ]

        if mod_set.use_noise:
            big_res[0] = big_res[0] * (mod_set.noise_scale + 1)
            big_res[1] = big_res[1] * (mod_set.noise_scale + 1)
            big_res[2] = big_res[2] * (mod_set.noise_scale + 1)
        # else:
        # p = []
        # -------- gather smoke domain settings
        # BBox = domain.bound_box
        # p.append([BBox[0][0], BBox[0][1], BBox[0][2]])
        # p.append([BBox[6][0], BBox[6][1], BBox[6][2]])
        # mod_set = smoke_modifier.domain_settings
        # resolution = mod_set.resolution_max
        # smokecache = mod_set.point_cache
        # ret = read_cache(smokecache, mod_set.use_noise, mod_set.noise_scale + 1, flowtype)
        # res_x = ret[0]
        # res_y = ret[1]
        # res_z = ret[2]
        # density = ret[3]
        # fire = ret[4]

        # if res_x * res_y * res_z > 0:
        # -------- new cache format
        # big_res = []
        # big_res.append(res_x)
        # big_res.append(res_y)
        # big_res.append(res_z)
        # else:
        # max = domain.dimensions[0]
        # if (max - domain.dimensions[1]) < -eps:
        # max = domain.dimensions[1]

        # if (max - domain.dimensions[2]) < -eps:
        # max = domain.dimensions[2]

        # big_res = [int(round(resolution * domain.dimensions[0] / max, 0)),
        # int(round(resolution * domain.dimensions[1] / max, 0)),
        # int(round(resolution * domain.dimensions[2] / max, 0))]

        # if mod_set.use_noise:
        # big_res = [big_res[0] * (mod_set.noise_scale + 1),
        # big_res[1] * (mod_set.noise_scale + 1),
        # big_res[2] * (mod_set.noise_scale + 1)]

        # if channel == 'density':
        # channeldata = density

        # if channel == 'fire':
        # channeldata = fire

        # sc_fr = '%s/%s/%s/%05d' % (
        # efutil.export_path,
        # efutil.scene_filename(),
        # bpy.context.scene.name,
        # bpy.context.scene.frame_current
        # )
        #               if not os.path.exists( sc_fr ):
        #                   os.makedirs(sc_fr)
        #
        #               smoke_filename = '%s.smoke' % bpy.path.clean_name(domain.name)
        #               smoke_path = '/'.join([sc_fr, smoke_filename])
        #
        #               with open(smoke_path, 'wb') as smoke_file:
        #                   # Binary densitygrid file format
        #                   #
        #                   # File header
        #                   smoke_file.write(b'SMOKE')        #magic number
        #                   smoke_file.write(struct.pack('<I', big_res[0]))
        #                   smoke_file.write(struct.pack('<I', big_res[1]))
        #                   smoke_file.write(struct.pack('<I', big_res[2]))
        # Density data
        #                   smoke_file.write(struct.pack('<%df'%len(channeldata), *channeldata))
        #
        #               LuxLog('Binary SMOKE file written: %s' % (smoke_path))

        # return big_res[0], big_res[1], big_res[2], channeldata

        mydf3 = voxel_lib.df3(big_res[0], big_res[1], big_res[2])
        sim_sizeX, sim_sizeY, sim_sizeZ = mydf3.size()
        for x in range(sim_sizeX):
            for y in range(sim_sizeY):
                for z in range(sim_sizeZ):
                    mydf3.set(x, y, z, channeldata[((z * sim_sizeY + y) * sim_sizeX + x)])
        try:
            mydf3.exportDF3(smoke_path)
        except ZeroDivisionError:
            print("Show smoke simulation in 3D view before export")
        print("Binary smoke.df3 file written in preview directory")
        if comments:
            file.write("\n//--Smoke--\n\n")

        # Note: We start with a default unit cube.
        #       This is mandatory to read correctly df3 data - otherwise we could just directly use
        #       bbox coordinates from the start, and avoid scale/translate operations at the end...
        file.write("box{<0,0,0>, <1,1,1>\n")
        file.write("    pigment{ rgbt 1 }\n")
        file.write("    hollow\n")
        file.write("    interior{ //---------------------\n")
        file.write("        media{ method 3\n")
        file.write("               emission <1,1,1>*1\n")  # 0>1 for dark smoke to white vapour
        file.write("               scattering{ 1, // Type\n")
        file.write("                  <1,1,1>*0.1\n")
        file.write("                } // end scattering\n")
        file.write('                density{density_file df3 "%s"\n' % smoke_path)
        file.write("                        color_map {\n")
        file.write("                        [0.00 rgb 0]\n")
        file.write("                        [0.05 rgb 0]\n")
        file.write("                        [0.20 rgb 0.2]\n")
        file.write("                        [0.30 rgb 0.6]\n")
        file.write("                        [0.40 rgb 1]\n")
        file.write("                        [1.00 rgb 1]\n")
        file.write("                       } // end color_map\n")
        file.write("               } // end of density\n")
        file.write("               samples %i // higher = more precise\n" % resolution)
        file.write("         } // end of media --------------------------\n")
        file.write("    } // end of interior\n")

        # START OF TRANSFORMATIONS

        # Size to consider here are bbox dimensions (i.e. still in object space, *before* applying
        # loc/rot/scale and other transformations (like parent stuff), aka matrix_world).
        bbox = smoke_obj.bound_box
        dim = [
            abs(bbox[6][0] - bbox[0][0]),
            abs(bbox[6][1] - bbox[0][1]),
            abs(bbox[6][2] - bbox[0][2]),
        ]

        # We scale our cube to get its final size and shapes but still in *object* space (same as Blender's bbox).
        file.write("scale<%.6g,%.6g,%.6g>\n" % (dim[0], dim[1], dim[2]))

        # We offset our cube such that (0,0,0) coordinate matches Blender's object center.
        file.write("translate<%.6g,%.6g,%.6g>\n" % (bbox[0][0], bbox[0][1], bbox[0][2]))

        # We apply object's transformations to get final loc/rot/size in world space!
        # Note: we could combine the two previous transformations with this matrix directly...
        write_matrix(file, global_matrix @ smoke_obj.matrix_world)

        # END OF TRANSFORMATIONS

        file.write("}\n")

        # file.write("               interpolate 1\n")
        # file.write("               frequency 0\n")
        # file.write("   }\n")
        # file.write("}\n")
