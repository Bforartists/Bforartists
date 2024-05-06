/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

struct ThicknessIsect {
  /* Normal at the intersection point on the sphere. */
  vec3 hit_N;
  /* Position of the intersection point on the sphere. */
  vec3 hit_P;
};

/**
 * Model sub-surface ray interaction with a sphere of the given diameter tangent to the shading
 * point. This allows to model 2 refraction events quite cheaply.
 * Assumes N and L are normalized.
 * Everything is relative to the entrance shading point.
 */
ThicknessIsect thickness_sphere_intersect(float diameter, vec3 N, vec3 L)
{
  ThicknessIsect isect;
  float cos_alpha = dot(L, -N);
  isect.hit_N = normalize(N + L * (cos_alpha * 2.0));
  isect.hit_P = L * (cos_alpha * diameter);
  return isect;
}

/**
 * Model sub-surface ray interaction with an infinite plane of the given diameter tangent to the
 * shading point. This allows to model 2 refraction events quite cheaply.
 * Assumes N and L are normalized.
 * Everything is relative to the entrance shading point.
 */
ThicknessIsect thickness_plane_intersect(float plane_distance, vec3 N, vec3 L)
{
  ThicknessIsect isect;
  float distance_from_shading_plane = dot(L, -N);
  isect.hit_N = -N;
  isect.hit_P = L * (plane_distance / distance_from_shading_plane);
  return isect;
}

ThicknessIsect thickness_shape_intersect(float thickness, vec3 N, vec3 L)
{
  if (thickness < 0.0) {
    return thickness_plane_intersect(-thickness, N, L);
  }
  return thickness_sphere_intersect(thickness, N, L);
}
