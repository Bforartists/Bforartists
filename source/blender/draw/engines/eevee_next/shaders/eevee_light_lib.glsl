/* SPDX-FileCopyrightText: 2022-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma BLENDER_REQUIRE(draw_math_geom_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_ltc_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_light_iter_lib.glsl)

/* Attenuation cutoff needs to be the same in the shadow loop and the light eval loop. */
#define LIGHT_ATTENUATION_THRESHOLD 1e-6

/* ---------------------------------------------------------------------- */
/** \name Light Functions
 * \{ */

struct LightVector {
  /* World space light vector. From the shading point to the light center. Normalized. */
  vec3 L;
  /* Distance from the shading point to the light center. */
  float dist;
};

LightVector light_vector_get(LightData light, const bool is_directional, vec3 P)
{
  LightVector lv;
  if (is_directional) {
    lv.L = light._back;
    lv.dist = 1.0;
  }
  else {
    lv.L = light._position - P;
    float inv_distance = inversesqrt(length_squared(lv.L));
    lv.L *= inv_distance;
    lv.dist = 1.0 / inv_distance;
  }
  return lv;
}

/* Light vector to the closest point in the light shape. */
LightVector light_shape_vector_get(LightData light, const bool is_directional, vec3 P)
{
  if (!is_directional && is_area_light(light.type)) {
    vec3 L = P - light._position;
    vec2 closest_point = vec2(dot(light._right, L), dot(light._up, L));
    vec2 max_pos = vec2(light._area_size_x, light._area_size_y);
    closest_point /= max_pos;

    if (light.type == LIGHT_ELLIPSE) {
      closest_point /= max(1.0, length(closest_point));
    }
    else {
      closest_point = clamp(closest_point, -1.0, 1.0);
    }
    closest_point *= max_pos;

    vec3 L_prime = light._right * closest_point.x + light._up * closest_point.y;

    L = L_prime - L;
    float inv_distance = inversesqrt(length_squared(L));
    LightVector lv;
    lv.L = L * inv_distance;
    lv.dist = 1.0 / inv_distance;
    return lv;
  }
  /* TODO(@fclem): other light shape? */
  return light_vector_get(light, is_directional, P);
}

/* Rotate vector to light's local space. Does not translate. */
vec3 light_world_to_local(LightData light, vec3 L)
{
  /* Avoid relying on compiler to optimize this.
   * vec3 lL = transpose(mat3(light.object_mat)) * L; */
  vec3 lL;
  lL.x = dot(light.object_mat[0].xyz, L);
  lL.y = dot(light.object_mat[1].xyz, L);
  lL.z = dot(light.object_mat[2].xyz, L);
  return lL;
}

/* Transform position from light's local space to world space. Does translation. */
vec3 light_local_position_to_world(LightData light, vec3 lP)
{
  return mat3(light.object_mat) * lP + light._position;
}

/* From Frostbite PBR Course
 * Distance based attenuation
 * http://www.frostbite.com/wp-content/uploads/2014/11/course_notes_moving_frostbite_to_pbr.pdf */
float light_influence_attenuation(float dist, float inv_sqr_influence)
{
  float factor = square(dist) * inv_sqr_influence;
  float fac = saturate(1.0 - square(factor));
  return square(fac);
}

float light_spot_attenuation(LightData light, vec3 L)
{
  vec3 lL = light_world_to_local(light, L);
  float ellipse = inversesqrt(1.0 + length_squared(lL.xy * light.spot_size_inv / lL.z));
  float spotmask = smoothstep(0.0, 1.0, ellipse * light._spot_mul + light._spot_bias);
  return spotmask * step(0.0, -dot(L, -light._back));
}

float light_attenuation_common(LightData light, const bool is_directional, vec3 L)
{
  if (is_directional) {
    return 1.0;
  }
  if (light.type == LIGHT_SPOT) {
    return light_spot_attenuation(light, L);
  }
  if (is_area_light(light.type)) {
    return step(0.0, -dot(L, -light._back));
  }
  return 1.0;
}

/**
 * Fade light influence when surface is not facing the light.
 * L is normalized vector to light shape center.
 * Ng is ideally the geometric normal.
 */
float light_attenuation_facing(LightData light, vec3 L, vec3 Ng, bool use_subsurface)
{
  if (use_subsurface) {
    return 1.0;
  }
  /* TODO(fclem): Take into consideration the light radius. */
  return float(dot(L, Ng) > 0.0);
}

float light_attenuation_surface(
    LightData light, const bool is_directional, vec3 Ng, bool use_subsurface, LightVector lv)
{
  /* TODO(fclem): add cutoff attenuation when back-facing. For now do nothing with Ng. */
  return light_attenuation_common(light, is_directional, lv.L) *
         light_attenuation_facing(light, lv.L, Ng, use_subsurface) *
         light_influence_attenuation(lv.dist, light.influence_radius_invsqr_surface);
}

float light_attenuation_volume(LightData light, const bool is_directional, LightVector lv)
{
  return light_attenuation_common(light, is_directional, lv.L) *
         light_influence_attenuation(lv.dist, light.influence_radius_invsqr_volume);
}

/* Cheaper alternative than evaluating the LTC.
 * The result needs to be multiplied by BSDF or Phase Function. */
float light_point_light(LightData light, const bool is_directional, LightVector lv)
{
  if (is_directional) {
    return 1.0;
  }
  /* Using "Point Light Attenuation Without Singularity" from Cem Yuksel
   * http://www.cemyuksel.com/research/pointlightattenuation/pointlightattenuation.pdf
   * http://www.cemyuksel.com/research/pointlightattenuation/
   */
  float d_sqr = square(lv.dist);
  float r_sqr = light.radius_squared;
  /* Using reformulation that has better numerical precision. */
  float power = 2.0 / (d_sqr + r_sqr + lv.dist * sqrt(d_sqr + r_sqr));

  if (is_area_light(light.type)) {
    /* Modulate by light plane orientation / solid angle. */
    power *= saturate(dot(light._back, lv.L));
  }
  return power;
}

/**
 * Return the radius of the disk at the sphere origin spanning the same solid angle as the sphere
 * from a given distance.
 * Assumes `distance_to_sphere > sphere_radius`.
 */
float light_sphere_disk_radius(float sphere_radius, float distance_to_sphere)
{
  /* The sine of the half-angle spanned by a sphere light is equal to the tangent of the
   * half-angle spanned by a disk light with the same radius. */
  return sphere_radius * inversesqrt(1.0 - square(sphere_radius / distance_to_sphere));
}

float light_ltc(
    sampler2DArray utility_tx, LightData light, vec3 N, vec3 V, LightVector lv, vec4 ltc_mat)
{
  if (light.type == LIGHT_POINT && lv.dist < light._radius) {
    /* Inside the sphere light, integrate over the hemisphere. */
    return 1.0;
  }

  if (light.type == LIGHT_RECT) {
    vec3 corners[4];
    corners[0] = light._right * light._area_size_x + light._up * -light._area_size_y;
    corners[1] = light._right * light._area_size_x + light._up * light._area_size_y;
    corners[2] = -corners[0];
    corners[3] = -corners[1];

    vec3 L = lv.L * lv.dist;
    corners[0] += L;
    corners[1] += L;
    corners[2] += L;
    corners[3] += L;

    ltc_transform_quad(N, V, ltc_matrix(ltc_mat), corners);

    return ltc_evaluate_quad(utility_tx, corners, vec3(0.0, 0.0, 1.0));
  }
  else {
    vec3 Px = light._right;
    vec3 Py = light._up;

    if (!is_area_light(light.type)) {
      make_orthonormal_basis(lv.L, Px, Py);
    }

    vec2 size = vec2(light._area_size_x, light._area_size_y);
    if (light.type == LIGHT_POINT) {
      /* The sine of the half-angle spanned by a sphere light is equal to the tangent of the
       * half-angle spanned by a disk light with the same radius. */
      size = vec2(light_sphere_disk_radius(light._radius, lv.dist));
    }
    vec3 points[3];
    points[0] = Px * -size.x + Py * -size.y;
    points[1] = Px * size.x + Py * -size.y;
    points[2] = -points[0];

    vec3 L = lv.L * lv.dist;
    points[0] += L;
    points[1] += L;
    points[2] += L;

    return ltc_evaluate_disk(utility_tx, N, V, ltc_matrix(ltc_mat), points);
  }
}

#ifdef SSS_TRANSMITTANCE
float sample_transmittance_profile(float u)
{
  return utility_tx_sample(utility_tx, vec2(u, 0.0), UTIL_SSS_TRANSMITTANCE_PROFILE_LAYER).r;
}

vec3 light_translucent(const bool is_directional,
                       LightData light,
                       vec3 N,
                       LightVector lv,
                       vec3 sss_radius,
                       float delta)
{
  /* TODO(fclem): We should compute the power at the entry point. */
  /* NOTE(fclem): we compute the light attenuation using the light vector but the transmittance
   * using the shadow depth delta. */
  float power = light_point_light(light, is_directional, lv);
  /* Do not add more energy on front faces. Also apply lambertian BSDF. */
  power *= max(0.0, dot(-N, lv.L)) * M_1_PI;

  sss_radius *= SSS_TRANSMIT_LUT_RADIUS;
  vec3 channels_co = saturate(delta / sss_radius) * SSS_TRANSMIT_LUT_SCALE + SSS_TRANSMIT_LUT_BIAS;

  vec3 translucency;
  translucency.x = (sss_radius.x > 0.0) ? sample_transmittance_profile(channels_co.x) : 0.0;
  translucency.y = (sss_radius.y > 0.0) ? sample_transmittance_profile(channels_co.y) : 0.0;
  translucency.z = (sss_radius.z > 0.0) ? sample_transmittance_profile(channels_co.z) : 0.0;
  return translucency * power;
}
#endif

/** \} */
