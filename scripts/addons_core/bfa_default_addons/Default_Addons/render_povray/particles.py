# SPDX-FileCopyrightText: 2021-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Get some Blender particle objects translated to POV."""

import bpy

import random


def pixel_relative_guess(ob):
    """Convert some object x dimension to a rough pixel relative order of magnitude"""
    from bpy_extras import object_utils

    scene = bpy.context.scene
    cam = scene.camera
    render = scene.render
    # Get rendered image resolution
    output_x_res = render.resolution_x
    focal_length = cam.data.lens
    # Get object bounding box size
    object_location = ob.location
    object_dimension_x = ob.dimensions[0]
    world_to_camera = object_utils.world_to_camera_view(scene, cam, object_location)

    apparent_size = (object_dimension_x * focal_length) / world_to_camera[2]
    sensor_width = cam.data.sensor_width
    pixel_pitch_x = sensor_width / output_x_res
    return apparent_size / pixel_pitch_x


def export_hair(file, ob, mod, p_sys, global_matrix):
    """Get Blender path particles (hair strands) objects translated to POV sphere_sweep unions."""
    # tstart = time.time()
    from .render import write_matrix

    textured_hair = 0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    p_sys_settings = p_sys.settings.evaluated_get(depsgraph)
    if ob.material_slots[p_sys_settings.material - 1].material and ob.active_material is not None:
        pmaterial = ob.material_slots[p_sys_settings.material - 1].material
        # XXX Todo: replace by pov_(Particles?)_texture_slot
        for th in pmaterial.pov_texture_slots:
            povtex = th.texture  # slot.name
            tex = bpy.data.textures[povtex]

            if (
                tex
                and th.use
                and ((tex.type == "IMAGE" and tex.image) or tex.type != "IMAGE")
                and th.use_map_color_diffuse
            ):
                textured_hair = 1
        if pmaterial.strand.use_blender_units:
            strand_start = pmaterial.strand.root_size
            strand_end = pmaterial.strand.tip_size
        else:
            try:
                # inexact pixel size, just to make radius relative to screen and object size.
                pixel_fac = pixel_relative_guess(ob)
            except ZeroDivisionError:
                # Fallback to hardwired constant value
                pixel_fac = 4500
                print("no pixel size found for stand radius, falling back to  %i" % pixel_fac)

            strand_start = pmaterial.strand.root_size / pixel_fac
            strand_end = pmaterial.strand.tip_size / pixel_fac
        strand_shape = pmaterial.strand.shape
    else:
        pmaterial = "default"  # No material assigned in blender, use default one
        strand_start = 0.01
        strand_end = 0.01
        strand_shape = 0.0
    # Set the number of particles to render count rather than 3d view display
    # p_sys.set_resolution(scene, ob, 'RENDER') # DEPRECATED
    # When you render, the entire dependency graph will be
    # evaluated at render resolution, including the particles.
    # In the viewport it will be at viewport resolution.
    # So there is no need for render engines to use this function anymore,
    # it's automatic now.
    steps = p_sys_settings.display_step
    steps = 2**steps  # or + 1 # Formerly : len(particle.hair_keys)

    total_number_of_strands = p_sys_settings.count * p_sys_settings.rendered_child_count
    # hairCounter = 0
    file.write("#declare HairArray = array[%i] {\n" % total_number_of_strands)
    for pindex in range(total_number_of_strands):

        # if particle.is_exist and particle.is_visible:
        # hairCounter += 1
        # controlPointCounter = 0
        # Each hair is represented as a separate sphere_sweep in POV-Ray.

        file.write("sphere_sweep{")
        if p_sys_settings.use_hair_bspline:
            file.write("b_spline ")
            file.write(
                "%i,\n" % (steps + 2)
            )  # +2 because the first point needs tripling to be more than a handle in POV
        else:
            file.write("linear_spline ")
            file.write("%i,\n" % steps)
        # changing world coordinates to object local coordinates by
        # multiplying with inverted matrix
        init_coord = ob.matrix_world.inverted() @ (p_sys.co_hair(ob, particle_no=pindex, step=0))
        init_coord = (init_coord[0], init_coord[1], init_coord[2])
        if (
            ob.material_slots[p_sys_settings.material - 1].material
            and ob.active_material is not None
        ):
            pmaterial = ob.material_slots[p_sys_settings.material - 1].material
            for th in pmaterial.pov_texture_slots:
                povtex = th.texture  # slot.name
                tex = bpy.data.textures[povtex]
                if tex and th.use and th.use_map_color_diffuse:
                    # treat POV textures as bitmaps
                    if (
                        tex.type == "IMAGE"
                        and tex.image
                        and th.texture_coords == "UV"
                        and ob.data.uv_textures is not None
                    ):
                        # or (
                        # tex.pov.tex_pattern_type != 'emulator'
                        # and th.texture_coords == 'UV'
                        # and ob.data.uv_textures is not None
                        # ):
                        image = tex.image
                        image_width = image.size[0]
                        image_height = image.size[1]
                        image_pixels = image.pixels[:]
                        uv_co = p_sys.uv_on_emitter(mod, p_sys.particles[pindex], pindex, 0)
                        x_co = round(uv_co[0] * (image_width - 1))
                        y_co = round(uv_co[1] * (image_height - 1))
                        pixelnumber = (image_width * y_co) + x_co
                        r = image_pixels[pixelnumber * 4]
                        g = image_pixels[pixelnumber * 4 + 1]
                        b = image_pixels[pixelnumber * 4 + 2]
                        a = image_pixels[pixelnumber * 4 + 3]
                        init_color = (r, g, b, a)
                    else:
                        # only overwrite variable for each competing texture for now
                        init_color = tex.evaluate(init_coord)
        for step in range(steps):
            coord = ob.matrix_world.inverted() @ (p_sys.co_hair(ob, particle_no=pindex, step=step))
            # for controlPoint in particle.hair_keys:
            if p_sys_settings.clump_factor:
                hair_strand_diameter = p_sys_settings.clump_factor / 200.0 * random.uniform(0.5, 1)
            elif step == 0:
                hair_strand_diameter = strand_start
            else:
                # still initialize variable
                hair_strand_diameter = strand_start
                if strand_shape == 0.0:
                    fac = step
                elif strand_shape < 0:
                    fac = pow(step, (1.0 + strand_shape))
                else:
                    fac = pow(step, (1.0 / (1.0 - strand_shape)))
                hair_strand_diameter += (
                    fac * (strand_end - strand_start) / (p_sys_settings.display_step + 1)
                )  # XXX +1 or -1 or nothing ?
            abs_hair_strand_diameter = abs(hair_strand_diameter)
            if step == 0 and p_sys_settings.use_hair_bspline:
                # Write three times the first point to compensate pov Bezier handling
                file.write(
                    "<%.6g,%.6g,%.6g>,%.7g,\n"
                    % (coord[0], coord[1], coord[2], abs_hair_strand_diameter)
                )
                file.write(
                    "<%.6g,%.6g,%.6g>,%.7g,\n"
                    % (coord[0], coord[1], coord[2], abs_hair_strand_diameter)
                )
                # Useless because particle location is the tip, not the root:
                # file.write(
                # '<%.6g,%.6g,%.6g>,%.7g'
                # % (
                # particle.location[0],
                # particle.location[1],
                # particle.location[2],
                # abs_hair_strand_diameter
                # )
                # )
                # file.write(',\n')
            # controlPointCounter += 1
            # total_number_of_strands += len(p_sys.particles)# len(particle.hair_keys)

            # Each control point is written out, along with the radius of the
            # hair at that point.
            file.write(
                "<%.6g,%.6g,%.6g>,%.7g" % (coord[0], coord[1], coord[2], abs_hair_strand_diameter)
            )

            # All coordinates except the last need a following comma.

            if step == steps - 1:
                if textured_hair:
                    # Write pigment and alpha (between Pov and Blender,
                    # alpha 0 and 1 are reversed)
                    file.write(
                        "\npigment{ color srgbf < %.3g, %.3g, %.3g, %.3g> }\n"
                        % (init_color[0], init_color[1], init_color[2], 1.0 - init_color[3])
                    )
                # End the sphere_sweep declaration for this hair
                file.write("}\n")

            else:
                file.write(",\n")
        # All but the final sphere_sweep (each array element) needs a terminating comma.
        if pindex != total_number_of_strands:
            file.write(",\n")
        else:
            file.write("\n")

    # End the array declaration.

    file.write("}\n")
    file.write("\n")

    if not textured_hair:
        # Pick up the hair material diffuse color and create a default POV-Ray hair texture.

        file.write("#ifndef (HairTexture)\n")
        file.write("  #declare HairTexture = texture {\n")
        file.write(
            "    pigment {srgbt <%s,%s,%s,%s>}\n"
            % (
                pmaterial.diffuse_color[0],
                pmaterial.diffuse_color[1],
                pmaterial.diffuse_color[2],
                (pmaterial.strand.width_fade + 0.05),
            )
        )
        file.write("  }\n")
        file.write("#end\n")
        file.write("\n")

    # Dynamically create a union of the hairstrands (or a subset of them).
    # By default use every hairstrand, commented line is for hand tweaking test renders.
    file.write("//Increasing HairStep divides the amount of hair for test renders.\n")
    file.write("#ifndef(HairStep) #declare HairStep = 1; #end\n")
    file.write("union{\n")
    file.write("  #local I = 0;\n")
    file.write("  #while (I < %i)\n" % total_number_of_strands)
    file.write("    object {HairArray[I]")
    if textured_hair:
        file.write("\n")
    else:
        file.write(" texture{HairTexture}\n")
    # Translucency of the hair:
    file.write("        hollow\n")
    file.write("        double_illuminate\n")
    file.write("        interior {\n")
    file.write("            ior 1.45\n")
    file.write("            media {\n")
    file.write("                scattering { 1, 10*<0.73, 0.35, 0.15> /*extinction 0*/ }\n")
    file.write("                absorption 10/<0.83, 0.75, 0.15>\n")
    file.write("                samples 1\n")
    file.write("                method 2\n")
    file.write("                density {cylindrical\n")
    file.write("                    color_map {\n")
    file.write("                        [0.0 rgb <0.83, 0.45, 0.35>]\n")
    file.write("                        [0.5 rgb <0.8, 0.8, 0.4>]\n")
    file.write("                        [1.0 rgb <1,1,1>]\n")
    file.write("                    }\n")
    file.write("                }\n")
    file.write("            }\n")
    file.write("        }\n")
    file.write("    }\n")

    file.write("    #local I = I + HairStep;\n")
    file.write("  #end\n")

    write_matrix(file, global_matrix @ ob.matrix_world)

    file.write("}")
    print("Totals hairstrands written: %i" % total_number_of_strands)
    print("Number of tufts (particle systems): %i" % len(ob.particle_systems))
