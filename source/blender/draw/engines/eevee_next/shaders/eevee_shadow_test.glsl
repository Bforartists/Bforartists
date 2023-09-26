/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/* Directive for resetting the line numbering so the failing tests lines can be printed.
 * This conflict with the shader compiler error logging scheme.
 * Comment out for correct compilation error line. */
#line 5

#pragma BLENDER_REQUIRE(gpu_shader_utildefines_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_math_matrix_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_math_vector_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_shadow_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_test_lib.glsl)

#define TEST(a, b) if (true)

void main()
{
  TEST(eevee_shadow, DirectionalClipmapLevel)
  {
    LightData light;
    light.type = LIGHT_SUN;
    light.clipmap_lod_min = -5;
    light.clipmap_lod_max = 8;
    light._clipmap_lod_bias = 0.0;
    float fac = float(SHADOW_TILEMAP_RES - 1) / float(SHADOW_TILEMAP_RES);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * 0.0)), light.clipmap_lod_min);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * 0.49)), 1);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * 0.5)), 1);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * 0.51)), 1);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * 0.99)), 2);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * 1.0)), 2);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * 1.01)), 2);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * 12.5)), 6);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * 12.51)), 6);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * 15.9999)), 6);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * 16.0)), 6);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * 16.00001)), 6);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * 5000.0)), light.clipmap_lod_max);
    /* Produces NaN / Inf, Undefined behavior. */
    // EXPECT_EQ(shadow_directional_level(light, vec3(FLT_MAX)), light.clipmap_lod_max);
  }

  TEST(eevee_shadow, DirectionalCascadeLevel)
  {
    LightData light;
    light.type = LIGHT_SUN_ORTHO;
    light.clipmap_lod_min = 2;
    light.clipmap_lod_max = 8;
    light._clipmap_origin_x = 0.0;
    light._clipmap_origin_y = 0.0;
    float half_size = exp2(float(light.clipmap_lod_min - 1));
    light._clipmap_lod_bias = light.clipmap_lod_min - 1;
    float fac = float(SHADOW_TILEMAP_RES - 1) / float(SHADOW_TILEMAP_RES);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * half_size * 0.0, 0.0, 0.0)), 2);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * half_size * 0.5, 0.0, 0.0)), 2);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * half_size * 1.0, 0.0, 0.0)), 3);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * half_size * 1.5, 0.0, 0.0)), 3);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * half_size * 2.0, 0.0, 0.0)), 4);
    EXPECT_EQ(shadow_directional_level(light, vec3(fac * 5000.0)), light.clipmap_lod_max);
    /* Produces NaN / Inf, Undefined behavior. */
    // EXPECT_EQ(shadow_directional_level(light, vec3(FLT_MAX)), light.clipmap_lod_max);
  }

  TEST(eevee_shadow, DirectionalClipmapCoordinates)
  {
    ShadowCoordinates coords;
    vec3 lP, camera_lP;

    LightData light;
    light.type = LIGHT_SUN;
    light.clipmap_lod_min = 0; /* Range [-0.5..0.5]. */
    light.clipmap_lod_max = 2; /* Range [-2..2]. */
    light.tilemap_index = light.clipmap_lod_min;
    light._position = vec3(0.0);
    light._clipmap_origin_x = 0.0;
    light._clipmap_origin_y = 0.0;
    light._clipmap_lod_bias = 0;

    float lod_min_tile_size = exp2(float(light.clipmap_lod_min)) / float(SHADOW_TILEMAP_RES);
    float lod_max_half_size = exp2(float(light.clipmap_lod_max)) / 2.0;

    camera_lP = vec3(0.0, 0.0, 0.0);
    /* Follows ShadowDirectional::end_sync(). */
    light.clipmap_base_offset = ivec2(round(camera_lP.xy / lod_min_tile_size));
    EXPECT_EQ(light.clipmap_base_offset, ivec2(0));

    /* Test UVs and tile mapping. */

    lP = vec3(1e-5, 1e-5, 0.0);
    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tilemap_index, 0);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2));
    EXPECT_NEAR(coords.uv, vec2(SHADOW_TILEMAP_RES / 2), 1e-3);

    lP = vec3(-1e-5, -1e-5, 0.0);
    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tilemap_index, 0);
    EXPECT_EQ(coords.tile_coord, ivec2((SHADOW_TILEMAP_RES / 2) - 1));
    EXPECT_NEAR(coords.uv, vec2(SHADOW_TILEMAP_RES / 2), 1e-3);

    lP = vec3(-0.5, -0.5, 0.0); /* Min of first LOD. */
    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tilemap_index, 0);
    EXPECT_EQ(coords.tile_coord, ivec2(0));
    EXPECT_NEAR(coords.uv, vec2(0), 1e-3);

    lP = vec3(0.5, 0.5, 0.0); /* Max of first LOD. */
    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tilemap_index, 0);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES - 1));
    EXPECT_NEAR(coords.uv, vec2(SHADOW_TILEMAP_RES), 1e-3);

    /* Test clip-map level selection. */

    camera_lP = vec3(2.0, 2.0, 0.0);
    /* Follows ShadowDirectional::end_sync(). */
    light.clipmap_base_offset = ivec2(round(camera_lP.xy / lod_min_tile_size));
    EXPECT_EQ(light.clipmap_base_offset, ivec2(32));

    lP = vec3(2.00001, 2.00001, 0.0);
    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tilemap_index, 0);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2));
    EXPECT_NEAR(coords.uv, vec2(SHADOW_TILEMAP_RES / 2), 1e-3);

    lP = vec3(1.50001, 1.50001, 0.0);
    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tilemap_index, 1);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 4));
    EXPECT_NEAR(coords.uv, vec2(SHADOW_TILEMAP_RES / 4), 1e-3);

    lP = vec3(1.00001, 1.00001, 0.0);
    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tilemap_index, 2);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 4));
    EXPECT_NEAR(coords.uv, vec2(SHADOW_TILEMAP_RES / 4), 1e-3);

    lP = vec3(-0.0001, -0.0001, 0.0); /* Out of bounds. */
    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tilemap_index, 2);
    EXPECT_EQ(coords.tile_coord, ivec2(0));
    EXPECT_NEAR(coords.uv, vec2(0), 1e-3);

    /* Test clip-map offset. */

    light.clipmap_base_offset = ivec2(31, 1);
    lP = vec3(2.0001, 0.0001, 0.0);

    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2) + ivec2(1, -1));

    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2) + ivec2(1, 0));

    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2) + ivec2(1, 0));

    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2) + ivec2(1, 0));

    /* Test clip-map negative offsets. */

    light.clipmap_base_offset = ivec2(-31, -1);
    lP = vec3(-2.0001, -0.0001, 0.0);

    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2 - 1) + ivec2(-1, 1));

    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2 - 1) + ivec2(-1, 0));

    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2 - 1) + ivec2(-1, 0));

    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2 - 1) + ivec2(-1, 0));
  }

  TEST(eevee_shadow, DirectionalCascadeCoordinates)
  {
    ShadowCoordinates coords;
    vec3 lP, camera_lP;

    LightData light;
    light.type = LIGHT_SUN_ORTHO;
    light.clipmap_lod_min = 0; /* Range [-0.5..0.5]. */
    light.clipmap_lod_max = 2; /* 3 tile-maps. */
    light.tilemap_index = 1;
    light._position = vec3(0.0);
    light._clipmap_lod_bias = light.clipmap_lod_min - 1;
    light._clipmap_origin_x = 0.0;
    light._clipmap_origin_y = 0.0;
    float lod_tile_size = exp2(float(light.clipmap_lod_min)) / float(SHADOW_TILEMAP_RES);
    float lod_half_size = exp2(float(light.clipmap_lod_min)) / 2.0;
    float narrowing = float(SHADOW_TILEMAP_RES - 1) / float(SHADOW_TILEMAP_RES);

    camera_lP = vec3(0.0, 0.0, 0.0);
    int level_range_size = light.clipmap_lod_max - light.clipmap_lod_min + 1;
    vec2 farthest_tilemap_center = vec2(lod_half_size * float(level_range_size - 1), 0.0);
    light.clipmap_base_offset = floatBitsToInt(
        vec2(lod_half_size / float(level_range_size - 1), 0.0));

    /* Test UVs and tile mapping. */

    lP = vec3(1e-8, 1e-8, 0.0);
    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tilemap_index, 1);
    EXPECT_EQ(coords.lod_relative, 0);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2));
    EXPECT_NEAR(coords.uv, vec2(SHADOW_TILEMAP_RES / 2), 1e-3);

    lP = vec3(lod_half_size * narrowing - 1e-5, 1e-8, 0.0);
    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tilemap_index, 1);
    EXPECT_EQ(coords.lod_relative, 0);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES - 1, SHADOW_TILEMAP_RES / 2));
    EXPECT_NEAR(coords.uv, vec2(float(SHADOW_TILEMAP_RES) - 0.5, SHADOW_TILEMAP_RES / 2), 1e-3);

    lP = vec3(lod_half_size + 1e-5, 1e-5, 0.0);
    coords = shadow_directional_coordinates(light, lP);
    EXPECT_EQ(coords.tilemap_index, 2);
    EXPECT_EQ(coords.lod_relative, 0);
    EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES - 1, SHADOW_TILEMAP_RES / 2));
    EXPECT_NEAR(coords.uv, vec2(SHADOW_TILEMAP_RES, SHADOW_TILEMAP_RES / 2), 1e-3);

    // lP = vec3(-0.5, -0.5, 0.0); /* Min of first LOD. */
    // coords = shadow_directional_coordinates(light, lP);
    // EXPECT_EQ(coords.tilemap_index, 0);
    // EXPECT_EQ(coords.tile_coord, ivec2(0));
    // EXPECT_NEAR(coords.uv, vec2(0), 1e-3);

    // lP = vec3(0.5, 0.5, 0.0); /* Max of first LOD. */
    // coords = shadow_directional_coordinates(light, lP);
    // EXPECT_EQ(coords.tilemap_index, 0);
    // EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES - 1));
    // EXPECT_NEAR(coords.uv, vec2(SHADOW_TILEMAP_RES), 1e-3);

    /* Test clip-map level selection. */

    // camera_lP = vec3(2.0, 2.0, 0.0);
    /* Follows ShadowDirectional::end_sync(). */
    // light.clipmap_base_offset = ivec2(round(camera_lP.xy / lod_min_tile_size));
    // EXPECT_EQ(light.clipmap_base_offset, ivec2(32));

    // lP = vec3(2.00001, 2.00001, 0.0);
    // coords = shadow_directional_coordinates(light, lP);
    // EXPECT_EQ(coords.tilemap_index, 0);
    // EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2));
    // EXPECT_NEAR(coords.uv, vec2(SHADOW_TILEMAP_RES / 2), 1e-3);

    // lP = vec3(1.50001, 1.50001, 0.0);
    // coords = shadow_directional_coordinates(light, lP);
    // EXPECT_EQ(coords.tilemap_index, 1);
    // EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 4));
    // EXPECT_NEAR(coords.uv, vec2(SHADOW_TILEMAP_RES / 4), 1e-3);

    // lP = vec3(1.00001, 1.00001, 0.0);
    // coords = shadow_directional_coordinates(light, lP);
    // EXPECT_EQ(coords.tilemap_index, 2);
    // EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 4));
    // EXPECT_NEAR(coords.uv, vec2(SHADOW_TILEMAP_RES / 4), 1e-3);

    // lP = vec3(-0.0001, -0.0001, 0.0); /* Out of bounds. */
    // coords = shadow_directional_coordinates(light, lP);
    // EXPECT_EQ(coords.tilemap_index, 2);
    // EXPECT_EQ(coords.tile_coord, ivec2(0));
    // EXPECT_NEAR(coords.uv, vec2(0), 1e-3);

    /* Test clip-map offset. */

    // light.clipmap_base_offset = ivec2(31, 1);
    // lP = vec3(2.0001, 0.0001, 0.0);

    // coords = shadow_directional_coordinates(light, lP);
    // EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2) + ivec2(1, -1));

    // coords = shadow_directional_coordinates(light, lP);
    // EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2) + ivec2(1, 0));

    // coords = shadow_directional_coordinates(light, lP);
    // EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2) + ivec2(1, 0));

    // coords = shadow_directional_coordinates(light, lP);
    // EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2) + ivec2(1, 0));

    /* Test clip-map negative offsets. */

    // light.clipmap_base_offset = ivec2(-31, -1);
    // lP = vec3(-2.0001, -0.0001, 0.0);

    // coords = shadow_directional_coordinates(light, lP);
    // EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2 - 1) + ivec2(-1, 1));

    // coords = shadow_directional_coordinates(light, lP);
    // EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2 - 1) + ivec2(-1, 0));

    // coords = shadow_directional_coordinates(light, lP);
    // EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2 - 1) + ivec2(-1, 0));

    // coords = shadow_directional_coordinates(light, lP);
    // EXPECT_EQ(coords.tile_coord, ivec2(SHADOW_TILEMAP_RES / 2 - 1) + ivec2(-1, 0));
  }
}
