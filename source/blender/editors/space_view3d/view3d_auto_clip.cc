/* SPDX-FileCopyrightText: 2026 Bforartists Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spview3d
 *
 * BFA - Auto Clipping.
 *
 * The clipping range of each region is computed before every redraw, in two cases:
 *
 * - Free view with #V3D_AUTO_CLIP: the selected objects can be seen as close as possible. The
 *   near and far distances follow the view distance, keeping the same depth precision whatever
 *   the zoom, and the far distance always contains the selected objects.
 * - Looking through a camera with #CAM_AUTO_CLIP: the range fits what the camera sees, from the
 *   nearest to the furthest visible object, measured along the view axis.
 *
 * The clip start/end of the 3D view and of the camera are never modified by the computation: the
 * range is stored in the runtime of the region and read by #BKE_camera_params_from_view3d, so the
 * values of the user are used again when the option is turned off, and renders are not affected.
 * Only #VIEW3D_OT_camera_clip_from_auto, run by the user, copies the range of the camera view to
 * the clipping of the camera.
 */

#include <algorithm>
#include <bit>
#include <cfloat>
#include <cstring>

#include "DNA_camera_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_view3d_types.h"

#include "BLI_listbase.hh"
#include "BLI_math_base_c.hh"
#include "BLI_math_matrix.hh"
#include "BLI_math_matrix_c.hh"
#include "BLI_math_rotation_c.hh"
#include "BLI_math_vector.hh"
#include "BLI_math_vector_c.hh"
#include "BLI_time.hh"
#include "BLI_utildefines.hh"

#include "MEM_guardedalloc.h"

#include "BKE_camera.h"
#include "BKE_context.hh"
#include "BKE_geometry_set.hh"
#include "BKE_global.hh"
#include "BKE_layer.hh"
#include "BKE_library.hh"
#include "BKE_object.hh"
#include "BKE_object_types.hh"
#include "BKE_report.hh"
#include "BKE_scene.hh"
#include "BKE_screen.hh"
#include "BKE_view3d_runtime.hh"

#include "DEG_depsgraph.hh"
#include "DEG_depsgraph_query.hh"

#include "RNA_access.hh"
#include "RNA_prototypes.hh"

#include "UI_interface_c.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "ED_screen.hh"
#include "ED_view3d.hh"

#include "view3d_intern.hh" /* own include */

namespace blender {

/**
 * The near distance is this fraction of the view distance (from the view to its pivot), and the
 * far distance is at least this many times it. At the default view distance (15) this gives about
 * the default clipping of Blender (0.01 to 1000), and the same depth precision at any zoom.
 */
static constexpr float AUTO_CLIP_NEAR_FACTOR = 0.001f;
static constexpr float AUTO_CLIP_FAR_FACTOR = 100.0f;
/** Margin applied to the bounds of what must be seen, so it never touches the far plane. */
static constexpr float AUTO_CLIP_FAR_MARGIN = 1.1f;
/**
 * Looking through a camera, the near plane is this fraction of the depth of the nearest object:
 * the bounds are exact, this absorbs the objects that moved since the last computation (heavy
 * scenes are not computed on every redraw) and the objects entering the frustum.
 */
static constexpr float AUTO_CLIP_CAMERA_NEAR_MARGIN = 0.5f;
/**
 * Largest far/near ratio allowed, to keep enough depth buffer precision.
 * When the scene would exceed it (zoomed in very close to one object while another one is very
 * far away) the far plane is brought closer, never the near plane: what is next to the viewer
 * must not be clipped, while what is very far away appears again when moving back.
 */
static constexpr float AUTO_CLIP_MAX_RATIO = 1.0e7f;
/**
 * Limits of the automatic distances: the RNA minimum of `clip_start`, and a far distance that
 * keeps the projection matrix precise.
 */
static constexpr float AUTO_CLIP_MIN_NEAR = 1.0e-6f;
static constexpr float AUTO_CLIP_MAX_FAR = 1.0e8f;
/**
 * Computing the camera range again must not slow down heavy scenes: the next computation is not
 * allowed before this many times the duration of the last one has passed, which keeps its cost
 * under 1 / AUTO_CLIP_CAMERA_COST_RATIO of the time. For a light scene that delay is far below a
 * frame, so the range is then always up to date.
 */
static constexpr double AUTO_CLIP_CAMERA_COST_RATIO = 20.0;

/* -------------------------------------------------------------------- */
/** \name Shared Helpers
 * \{ */

/**
 * What decides which objects are visible in the 3D view (local view, local collections, object
 * types): the cached bounds are computed again when it changes.
 */
static void auto_clip_visibility_key_get(const View3D *v3d, uint32_t r_key[3])
{
  r_key[0] = uint32_t(v3d->local_view_uid) | (v3d->localvd ? (1u << 16) : 0u) |
             ((v3d->flag & V3D_LOCAL_COLLECTIONS) ? (1u << 17) : 0u);
  r_key[1] = uint32_t(v3d->object_type_exclude_viewport);
  r_key[2] = uint32_t(v3d->local_collections_uid);
}

/**
 * Local space bounds of an object. Objects without data bounds (empties, lights...) get a box
 * around their origin, like #BKE_object_minmax.
 */
static Bounds<float3> auto_clip_object_bounds_get(const Object *ob)
{
  if (const std::optional<Bounds<float3>> bounds = BKE_object_boundbox_get(ob)) {
    return *bounds;
  }
  const float size = (ob->type == OB_EMPTY) ? ob->empty_drawsize : 1.0f;
  return Bounds<float3>(float3(-size), float3(size));
}

/**
 * False for infinity and NaN. The exponent is tested directly: Blender is built with `/fp:fast`
 * (and `-ffast-math` elsewhere), where the compiler may assume there are no such values and
 * remove `std::isfinite`.
 */
static bool auto_clip_is_finite(const float value)
{
  constexpr uint32_t exponent_mask = 0x7F800000u;
  return (std::bit_cast<uint32_t>(value) & exponent_mask) != exponent_mask;
}

static bool auto_clip_is_finite(const float3 &v)
{
  return auto_clip_is_finite(v.x) && auto_clip_is_finite(v.y) && auto_clip_is_finite(v.z);
}

static float3 auto_clip_box_corner(const Bounds<float3> &box, const int index)
{
  return float3((index & 1) ? box.max.x : box.min.x,
                (index & 2) ? box.max.y : box.min.y,
                (index & 4) ? box.max.z : box.min.z);
}

/**
 * Add to \a min and \a max the bounds of the instances of an object (collection instances,
 * geometry nodes, particles...), which are not part of the bounds of the object itself. They are
 * the bounds of all the instances together, so larger than needed for a camera: the range is
 * wider, never narrower. \return false when the object makes no instances.
 */
static bool auto_clip_instances_minmax(Depsgraph *depsgraph, Object *ob, float3 &min, float3 &max)
{
  /* Cheap test first: listing the instances of an object is not. */
  const bke::GeometrySet *geometry = ob->runtime->geometry_set_eval;
  if ((ob->transflag & OB_DUPLI) == 0 && !(geometry && geometry->has_instances())) {
    return false;
  }
  return BKE_object_minmax_dupli(depsgraph, ob, min, max, false);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Free View: Selected Objects
 * \{ */

/**
 * Update the world space bounds of the selected objects, with their instances, if they are out of
 * date: only after a depsgraph evaluation (which every selection, transform or edit triggers) or a
 * change of what the 3D view shows. Navigating reuses them, so it costs nothing.
 */
static void auto_clip_selection_update(Depsgraph *depsgraph,
                                       const View3D *v3d,
                                       bke::RegionView3DRuntime::AutoClipSelection &cache)
{
  const uint64_t update_count = DEG_get_update_count(depsgraph);
  uint32_t visibility_key[3];
  auto_clip_visibility_key_get(v3d, visibility_key);
  if (cache.cached && cache.depsgraph == depsgraph && cache.update_count == update_count &&
      std::equal(std::begin(visibility_key), std::end(visibility_key), cache.visibility_key))
  {
    return;
  }

  ViewLayer *view_layer_eval = DEG_get_evaluated_view_layer(depsgraph);
  if (view_layer_eval == nullptr || !BKE_view_layer_is_synced(*view_layer_eval)) {
    /* Not ready: no bounds, try again at the next redraw. */
    cache.cached = false;
    cache.has_bounds = false;
    return;
  }

  float3 min, max;
  INIT_MINMAX(min, max);
  cache.has_bounds = false;
  for (Base &base_eval : *BKE_view_layer_object_bases_get(view_layer_eval)) {
    if (!BASE_SELECTED(v3d, &base_eval)) {
      continue;
    }
    /* All the corners: the bounds of a rotated object are not given by two of them. */
    const Bounds<float3> box = auto_clip_object_bounds_get(base_eval.object);
    for (const int i : IndexRange(8)) {
      math::min_max(
          math::transform_point(base_eval.object->object_to_world(), auto_clip_box_corner(box, i)),
          min,
          max);
    }
    auto_clip_instances_minmax(depsgraph, base_eval.object, min, max);
    cache.has_bounds = true;
  }
  copy_v3_v3(cache.min, min);
  copy_v3_v3(cache.max, max);

  cache.depsgraph = depsgraph;
  cache.update_count = update_count;
  std::copy(std::begin(visibility_key), std::end(visibility_key), cache.visibility_key);
  cache.cached = true;
}

/**
 * Distance from \a point to the furthest corner of the bounds of the selected objects, zero when
 * nothing is selected. Exact for the box, unlike its bounding sphere which is much larger for a
 * flat or elongated selection.
 */
static float auto_clip_selection_far_get(const bke::RegionView3DRuntime::AutoClipSelection &cache,
                                         const float3 &point)
{
  if (!cache.has_bounds) {
    return 0.0f;
  }
  const Bounds<float3> box(float3(cache.min), float3(cache.max));
  float far = 0.0f;
  for (const int i : IndexRange(8)) {
    far = std::max(far, math::distance(point, auto_clip_box_corner(box, i)));
  }
  return far;
}

/**
 * Compute the range of a free view (not looking through a camera), in the format of
 * #View3D::clip_start and #View3D::clip_end.
 */
static void auto_clip_free_view_calc(Depsgraph *depsgraph,
                                     const View3D *v3d,
                                     RegionView3D *rv3d,
                                     float *r_clip_start,
                                     float *r_clip_end)
{
  /* Not `rv3d->is_persp`: it is only updated when the projection matrix is computed, after this
   * function, so it is still the previous one right after switching perspective/orthographic. */
  const bool is_persp = (rv3d->persp == RV3D_PERSP);
  const float dist = std::max(rv3d->dist, AUTO_CLIP_MIN_NEAR);

  /* View origin in world space (see `view3d_viewmatrix_set`): moved back by `dist` from the
   * pivot in perspective, on the pivot in orthographic. */
  float3 view_origin = -float3(rv3d->ofs);
  if (is_persp) {
    float quat_inv[4];
    float3 back(0.0f, 0.0f, dist);
    invert_qt_qt_normalized(quat_inv, rv3d->viewquat);
    mul_qt_v3(quat_inv, back);
    view_origin += back;
  }

  /* Far distance needed by the view: everything around the pivot, and the selected objects. */
  bke::RegionView3DRuntime::AutoClipSelection &selection = rv3d->runtime->auto_clip_selection;
  auto_clip_selection_update(depsgraph, v3d, selection);
  const float far_selection = auto_clip_selection_far_get(selection, view_origin);
  const float far_auto = std::min(
      std::max(dist * AUTO_CLIP_FAR_FACTOR, far_selection * AUTO_CLIP_FAR_MARGIN),
      AUTO_CLIP_MAX_FAR);

  if (!is_persp) {
    /* Orthographic views use a range centered on the view, `[-clip_end / 2, clip_end / 2]`,
     * and do not use `clip_start`. */
    *r_clip_start = v3d->clip_start;
    *r_clip_end = far_auto * 2.0f;
    return;
  }

  const float near = std::max(dist * AUTO_CLIP_NEAR_FACTOR, AUTO_CLIP_MIN_NEAR);
  *r_clip_start = near;
  *r_clip_end = std::min(far_auto, near * AUTO_CLIP_MAX_RATIO);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Camera View: Visible Objects
 * \{ */

/**
 * The frustum of the camera in camera space (x right, y up, looking along -z), as depth `d = -z`
 * dependent bounds: `min_a + min_b * d <= (x, y) <= max_a + max_b * d`. A perspective frustum
 * has `a = 0` and `b` the tangents of its angles, an orthographic one has `b = 0`.
 */
struct AutoClipFrustum {
  float2 min_a, min_b, max_a, max_b;
};

static_assert(sizeof(AutoClipFrustum) == sizeof(float[8]), "copied as part of the cache key");

/** Smallest and largest depth of what is seen, accumulated over the objects. */
struct AutoClipDepthRange {
  float near = FLT_MAX;
  float far = 0.0f;
  /** Depths that are not finite (an object so large that the computation overflows) are ignored.
   */
  void add(const float depth)
  {
    if (auto_clip_is_finite(depth)) {
      near = std::min(near, depth);
      far = std::max(far, depth);
    }
  }
  bool is_empty() const
  {
    return far <= 0.0f;
  }
};

/** Number of inequalities (depth and the four sides of the frustum) a point must satisfy. */
static constexpr int AUTO_CLIP_FRUSTUM_PLANES = 5;

/** Inequalities `values[i] >= 0` that a point of camera space satisfies when inside the frustum.
 */
static void auto_clip_frustum_values(const AutoClipFrustum &frustum,
                                     const float3 &p,
                                     float r_values[AUTO_CLIP_FRUSTUM_PLANES])
{
  const float d = -p.z;
  r_values[0] = d;
  r_values[1] = p.x - (frustum.min_a.x + frustum.min_b.x * d);
  r_values[2] = (frustum.max_a.x + frustum.max_b.x * d) - p.x;
  r_values[3] = p.y - (frustum.min_a.y + frustum.min_b.y * d);
  r_values[4] = (frustum.max_a.y + frustum.max_b.y * d) - p.y;
}

/**
 * Add to \a range the depths of the vertices of the part of a box inside the frustum. The
 * extremes of the depth over that convex part are on its vertices, which are:
 * - the ends of the edges of the box clipped by the frustum (covers the corners of the box that
 *   are inside, and the points where its edges cross the sides of the frustum),
 * - the points where the four edges of the frustum cross the box, found by intersecting the
 *   line of each of them with the box in its own space.
 * A box containing the camera adds a nearest depth of zero: nothing is known about what is
 * around the camera.
 *
 * \param camera_from_box: Transform of the space of \a box to camera space.
 */
static void auto_clip_box_depth_range(const float4x4 &camera_from_box,
                                      const Bounds<float3> &box,
                                      const AutoClipFrustum &frustum,
                                      AutoClipDepthRange &range)
{
  float values[8][AUTO_CLIP_FRUSTUM_PLANES];
  float depth_max = -FLT_MAX;
  for (const int i : IndexRange(8)) {
    const float3 corner = math::transform_point(camera_from_box, auto_clip_box_corner(box, i));
    /* An infinite or NaN corner (object scaled to infinity...) would corrupt the whole range. */
    if (!auto_clip_is_finite(corner)) {
      return;
    }
    auto_clip_frustum_values(frustum, corner, values[i]);
    depth_max = std::max(depth_max, values[i][0]);
  }
  /* Entirely behind the camera. */
  if (depth_max <= 0.0f) {
    return;
  }

  /* Edges: the sides of the box are the pairs of corners that differ by one bit of the index. */
  for (const int i : IndexRange(8)) {
    for (const int bit : {1, 2, 4}) {
      if (i & bit) {
        continue;
      }
      const int j = i | bit;
      /* Liang-Barsky: every inequality is linear along the edge. */
      float t_min = 0.0f, t_max = 1.0f;
      for (const int k : IndexRange(AUTO_CLIP_FRUSTUM_PLANES)) {
        const float v0 = values[i][k], v1 = values[j][k];
        if (v0 < 0.0f && v1 < 0.0f) {
          t_max = -1.0f;
          break;
        }
        if (v0 < 0.0f) {
          t_min = std::max(t_min, v0 / (v0 - v1));
        }
        else if (v1 < 0.0f) {
          t_max = std::min(t_max, v0 / (v0 - v1));
        }
      }
      if (t_min <= t_max) {
        range.add(math::interpolate(values[i][0], values[j][0], t_min));
        range.add(math::interpolate(values[i][0], values[j][0], t_max));
      }
    }
  }

  /* The four edges of the frustum, as lines `origin + d * direction` of camera space. A box
   * without volume (an axis with a zero scale) cannot be inverted: its edges, above, are all
   * there is of it. */
  bool is_invertible = false;
  const float4x4 box_from_camera = math::invert(camera_from_box, is_invertible);
  if (!is_invertible) {
    return;
  }
  for (const int corner : IndexRange(4)) {
    const bool use_max_x = (corner & 1) != 0, use_max_y = (corner & 2) != 0;
    const float3 origin_camera(use_max_x ? frustum.max_a.x : frustum.min_a.x,
                               use_max_y ? frustum.max_a.y : frustum.min_a.y,
                               0.0f);
    const float3 direction_camera(use_max_x ? frustum.max_b.x : frustum.min_b.x,
                                  use_max_y ? frustum.max_b.y : frustum.min_b.y,
                                  -1.0f);
    const float3 origin = math::transform_point(box_from_camera, origin_camera);
    const float3 direction = math::transform_direction(box_from_camera, direction_camera);
    /* The inverse of a matrix with an extreme scale may overflow. */
    if (!auto_clip_is_finite(origin) || !auto_clip_is_finite(direction)) {
      continue;
    }

    /* Slabs: the interval of depths where the line is inside the box. */
    float d_enter = -FLT_MAX, d_exit = FLT_MAX;
    for (const int axis : IndexRange(3)) {
      if (math::abs(direction[axis]) < 1.0e-20f) {
        if (origin[axis] < box.min[axis] || origin[axis] > box.max[axis]) {
          d_exit = -1.0f;
        }
        continue;
      }
      const float d0 = (box.min[axis] - origin[axis]) / direction[axis];
      const float d1 = (box.max[axis] - origin[axis]) / direction[axis];
      d_enter = std::max(d_enter, std::min(d0, d1));
      d_exit = std::min(d_exit, std::max(d0, d1));
    }
    /* An interval still at its initial values was not bounded by any slab: nothing was measured.
     */
    if (d_enter <= d_exit && d_exit >= 0.0f && d_enter > -FLT_MAX && d_exit < FLT_MAX) {
      range.add(std::max(d_enter, 0.0f));
      range.add(d_exit);
    }
  }
}

/** Frustum of the region in camera space, with the same parameters as the projection matrix. */
static AutoClipFrustum auto_clip_frustum_get(const Depsgraph *depsgraph,
                                             const View3D *v3d,
                                             const ARegion *region,
                                             const RegionView3D *rv3d)
{
  CameraParams params;
  BKE_camera_params_init(&params);
  BKE_camera_params_from_view3d(&params, depsgraph, v3d, rv3d);
  BKE_camera_params_compute_viewplane(&params, region->winx, region->winy, 1.0f, 1.0f);

  const float2 min(params.viewplane.xmin, params.viewplane.ymin);
  const float2 max(params.viewplane.xmax, params.viewplane.ymax);
  AutoClipFrustum frustum;
  if (params.is_ortho) {
    frustum = {min, float2(0.0f), max, float2(0.0f)};
  }
  else {
    /* The view plane is the one at the near distance. */
    const float near = std::max(params.clip_start, AUTO_CLIP_MIN_NEAR);
    frustum = {float2(0.0f), min / near, float2(0.0f), max / near};
  }
  if (rv3d->rflag & RV3D_FLIP_X) {
    /* Mirrored view: x is negated. */
    frustum = {float2(-frustum.max_a.x, frustum.min_a.y),
               float2(-frustum.max_b.x, frustum.min_b.y),
               float2(-frustum.min_a.x, frustum.max_a.y),
               float2(-frustum.min_b.x, frustum.max_b.y)};
  }
  return frustum;
}

/** The view matrix of the camera view, the same as `obmat_to_viewmat`. */
static float4x4 auto_clip_camera_from_world_get(const Object *camera_eval, const RegionView3D *rv3d)
{
  float4x4 world_from_camera;
  normalize_m4_m4(world_from_camera.ptr(), camera_eval->object_to_world().ptr());
  if (rv3d->camroll != 0.0f) {
    rotate_m4(world_from_camera.ptr(), 'Z', -rv3d->camroll);
  }
  return math::invert(world_from_camera);
}

/**
 * Accumulate in \a range the depth of the visible objects inside the frustum.
 * \return false when the view layer is not ready (nothing is accumulated).
 */
static bool auto_clip_camera_depth_range_calc(Depsgraph *depsgraph,
                                              const View3D *v3d,
                                              const float4x4 &camera_from_world,
                                              const AutoClipFrustum &frustum,
                                              AutoClipDepthRange &range)
{
  ViewLayer *view_layer_eval = DEG_get_evaluated_view_layer(depsgraph);
  if (view_layer_eval == nullptr || !BKE_view_layer_is_synced(*view_layer_eval)) {
    return false;
  }

  for (Base &base_eval : *BKE_view_layer_object_bases_get(view_layer_eval)) {
    Object *ob = base_eval.object;
    if (!BASE_VISIBLE(v3d, &base_eval)) {
      continue;
    }
    /* Objects that are only displayed for editing, not geometry that hides the scene. Empties
     * are only used for the instances they make. */
    if (ELEM(ob->type, OB_CAMERA, OB_LAMP, OB_SPEAKER, OB_LIGHTPROBE)) {
      continue;
    }
    if (ob->type != OB_EMPTY) {
      auto_clip_box_depth_range(camera_from_world * ob->object_to_world(),
                                auto_clip_object_bounds_get(ob),
                                frustum,
                                range);
    }
    float3 min, max;
    INIT_MINMAX(min, max);
    if (auto_clip_instances_minmax(depsgraph, ob, min, max)) {
      auto_clip_box_depth_range(camera_from_world, Bounds<float3>(min, max), frustum, range);
    }
  }
  return true;
}

/**
 * Update the depth range of what the camera of the view sees, if it is out of date. The result
 * is in \a cache.
 */
static void auto_clip_camera_update(Depsgraph *depsgraph,
                                    const View3D *v3d,
                                    const ARegion *region,
                                    const RegionView3D *rv3d,
                                    const Object *camera_eval,
                                    bke::RegionView3DRuntime::AutoClipCamera &cache)
{
  const float4x4 camera_from_world = auto_clip_camera_from_world_get(camera_eval, rv3d);
  const AutoClipFrustum frustum = auto_clip_frustum_get(depsgraph, v3d, region, rv3d);

  float view_key[24];
  memcpy(view_key, camera_from_world.ptr(), sizeof(float[16]));
  memcpy(view_key + 16, &frustum, sizeof(float[8]));
  const uint64_t update_count = DEG_get_update_count(depsgraph);
  uint32_t visibility_key[3];
  auto_clip_visibility_key_get(v3d, visibility_key);

  const bool same_scene = cache.cached && cache.depsgraph == depsgraph &&
                          std::equal(std::begin(visibility_key),
                                     std::end(visibility_key),
                                     cache.visibility_key);
  if (same_scene && cache.update_count == update_count &&
      std::equal(std::begin(view_key), std::end(view_key), cache.view_key))
  {
    return;
  }
  /* Only the camera or the scene changed: the previous range is a good enough approximation
   * while the delay since the last computation has not passed, the margins absorb the change. */
  const double time_start = BLI_time_now_seconds();
  if (same_scene && time_start < cache.next_update_time) {
    /* A redraw that comes late is not guaranteed (the camera stopped moving): ask for one, a
     * region cannot tag itself while it is drawn. It only repeats during the delay, which is
     * short as it is a multiple of the duration of the computation. */
    WM_main_add_notifier(NC_SPACE | ND_SPACE_VIEW3D, nullptr);
    return;
  }

  AutoClipDepthRange range;
  if (!auto_clip_camera_depth_range_calc(depsgraph, v3d, camera_from_world, frustum, range)) {
    /* Not ready, try again at the next redraw. */
    cache.cached = false;
    cache.has_range = false;
    return;
  }

  cache.depsgraph = depsgraph;
  cache.update_count = update_count;
  std::copy(std::begin(visibility_key), std::end(visibility_key), cache.visibility_key);
  std::copy(std::begin(view_key), std::end(view_key), cache.view_key);
  cache.has_range = !range.is_empty();
  cache.near_depth = cache.has_range ? range.near : 0.0f;
  cache.far_depth = range.far;
  cache.cached = true;
  cache.next_update_time = time_start +
                           (BLI_time_now_seconds() - time_start) * AUTO_CLIP_CAMERA_COST_RATIO;
}

/**
 * The clipping of the camera, from the nearest and furthest depth of what it sees: margins around
 * them, within the ratio the depth precision allows.
 */
static void auto_clip_camera_clip_from_depths(const float near_depth,
                                              const float far_depth,
                                              float *r_clip_start,
                                              float *r_clip_end)
{
  const float far = std::min(far_depth * AUTO_CLIP_FAR_MARGIN, AUTO_CLIP_MAX_FAR);
  /* A nearest depth of zero means the camera is inside an object: nothing is known about what is
   * near it, so the nearest distance the precision allows. */
  const float near = (near_depth > 0.0f) ?
                         std::max(near_depth * AUTO_CLIP_CAMERA_NEAR_MARGIN, AUTO_CLIP_MIN_NEAR) :
                         std::max(far / AUTO_CLIP_MAX_RATIO, AUTO_CLIP_MIN_NEAR);
  *r_clip_start = near;
  *r_clip_end = std::min(far, near * AUTO_CLIP_MAX_RATIO);
}

/**
 * Compute the range of the camera view, in the format of the clipping of the camera. When
 * the camera sees nothing the clipping of the camera is kept.
 */
static void auto_clip_camera_view_calc(Depsgraph *depsgraph,
                                       const View3D *v3d,
                                       const ARegion *region,
                                       RegionView3D *rv3d,
                                       const Object *camera_eval,
                                       float *r_clip_start,
                                       float *r_clip_end)
{
  const Camera *camera = id_cast<const Camera *>(camera_eval->data);
  bke::RegionView3DRuntime::AutoClipCamera &cache = rv3d->runtime->auto_clip_camera;
  auto_clip_camera_update(depsgraph, v3d, region, rv3d, camera_eval, cache);
  if (!cache.has_range) {
    *r_clip_start = camera->clip_start;
    *r_clip_end = camera->clip_end;
    return;
  }

  auto_clip_camera_clip_from_depths(cache.near_depth, cache.far_depth, r_clip_start, r_clip_end);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Update Before Drawing
 * \{ */

/**
 * True if the part of the sidebar showing the clipping is on screen: the sidebar is open and
 * the category of the View panel is the active one (or the categories are not used).
 */
static bool auto_clip_sidebar_is_showing_clip(ARegion *region_ui)
{
  if (region_ui->flag & RGN_FLAG_HIDDEN) {
    return false;
  }
  if (region_ui->runtime->panels_category.is_empty()) {
    return true;
  }
  const char *category = ui::panel_category_active_get(region_ui, false);
  return category == nullptr || STREQ(category, "View");
}

/**
 * Redraw the sidebar after the range of \a region changed. In quad view every region has its own
 * clipping but the sidebar only shows the one of the main region (the one of
 * `SpaceView3D.region_3d`), so the other regions must not refresh it: they would do it on every
 * redraw for nothing. The sidebar lays its panels out again on every redraw, so this also
 * covers the change from Clip Near / Clip Far to the computed range and back.
 */
static void auto_clip_sidebar_redraw(const bContext *C, const View3D *v3d, const ARegion *region)
{
  ScrArea *area = CTX_wm_area(C);
  if (region != ED_view3d_area_main_region(area, v3d)) {
    return;
  }
  ARegion *region_ui = BKE_area_find_region_type(area, RGN_TYPE_UI);
  if (region_ui == nullptr || !auto_clip_sidebar_is_showing_clip(region_ui)) {
    return;
  }
  ED_region_tag_redraw(region_ui);
}

/**
 * Redraw the Properties editors: the button of the camera, that copies the range of the camera
 * view to its clipping, is enabled or not depending on whether that range exists. They do not
 * redraw when the 3D viewport computes it, which happens after the notifier of the change.
 */
static void auto_clip_properties_redraw(const bContext *C)
{
  for (ScrArea &area : CTX_wm_screen(C)->areabase) {
    if (area.spacetype == SPACE_PROPERTIES) {
      ED_area_tag_redraw(&area);
    }
  }
}

/**
 * Compute the clipping range of the region, in the format of the clipping of the 3D view in a
 * free view and of the camera in camera view. \return false when no automatic clipping applies.
 */
static bool auto_clip_calc(const bContext *C,
                           const View3D *v3d,
                           const ARegion *region,
                           RegionView3D *rv3d,
                           float *r_clip_start,
                           float *r_clip_end)
{
  if (rv3d->persp == RV3D_CAMOB) {
    /* The option is on the data of the camera: look at it before anything else, so the cost is
     * nil for the cameras that do not use it. */
    const Object *camera = v3d->camera;
    if (camera == nullptr || camera->type != OB_CAMERA ||
        (id_cast<const Camera *>(camera->data)->flag & CAM_AUTO_CLIP) == 0)
    {
      return false;
    }
    Depsgraph *depsgraph = CTX_data_expect_evaluated_depsgraph(C);
    auto_clip_camera_view_calc(depsgraph,
                               v3d,
                               region,
                               rv3d,
                               DEG_get_evaluated(depsgraph, camera),
                               r_clip_start,
                               r_clip_end);
    return true;
  }

  if ((v3d->flag2 & V3D_AUTO_CLIP) == 0) {
    return false;
  }
  auto_clip_free_view_calc(
      CTX_data_expect_evaluated_depsgraph(C), v3d, rv3d, r_clip_start, r_clip_end);
  return true;
}

void view3d_auto_clip_update(const bContext *C, ARegion *region)
{
  const View3D *v3d = CTX_wm_view3d(C);
  RegionView3D *rv3d = static_cast<RegionView3D *>(region->regiondata);
  bke::RegionView3DRuntime &runtime = *rv3d->runtime;
  const bool was_valid = runtime.auto_clip_valid;
  const bool was_camera_view = runtime.auto_clip_camera_view;

  float clip_start, clip_end;
  if (!auto_clip_calc(C, v3d, region, rv3d, &clip_start, &clip_end)) {
    /* The clipping of the 3D view or of the camera is used, report no computed value. */
    if (was_valid) {
      runtime.auto_clip_valid = false;
      runtime.auto_clip_camera_view = false;
      auto_clip_sidebar_redraw(C, v3d, region);
    }
    if (was_camera_view) {
      auto_clip_properties_redraw(C);
    }
    return;
  }

  runtime.auto_clip_camera_view = (rv3d->persp == RV3D_CAMOB);
  if (runtime.auto_clip_camera_view != was_camera_view) {
    auto_clip_properties_redraw(C);
  }

  /* Ignore tiny differences: avoids needless redraws of the sidebar. */
  if (was_valid && compare_ff_relative(runtime.auto_clip_start, clip_start, FLT_EPSILON, 64) &&
      compare_ff_relative(runtime.auto_clip_end, clip_end, FLT_EPSILON, 64))
  {
    return;
  }

  /* The clipping of the 3D view and of the camera is never written: they keep the values of the
   * user. */
  runtime.auto_clip_start = clip_start;
  runtime.auto_clip_end = clip_end;
  runtime.auto_clip_valid = true;
  auto_clip_sidebar_redraw(C, v3d, region);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Apply the Computed Range to the Camera
 * \{ */

/** The 3D viewport looking through a camera, with the range computed for it. */
struct AutoClipCameraView {
  View3D *v3d;
  ARegion *region;
  RegionView3D *rv3d;
};

/**
 * Find a 3D viewport looking through \a camera with a computed range. The camera of the
 * Properties editor is not looked through by its own area, so the screen is searched.
 * \return false when there is none.
 */
static bool view3d_camera_auto_clip_find(const bContext *C,
                                         const Camera *camera,
                                         AutoClipCameraView &r_view)
{
  bScreen *screen = CTX_wm_screen(C);
  if (screen == nullptr) {
    return false;
  }
  for (ScrArea &area : screen->areabase) {
    if (area.spacetype != SPACE_VIEW3D) {
      continue;
    }
    View3D *v3d = area.spacedata.first_as<View3D>();
    if (v3d->camera == nullptr || v3d->camera->type != OB_CAMERA ||
        id_cast<const Camera *>(v3d->camera->data) != camera)
    {
      continue;
    }
    for (ARegion &region : area.regionbase) {
      if (region.regiontype != RGN_TYPE_WINDOW || region.regiondata == nullptr) {
        continue;
      }
      RegionView3D *rv3d = static_cast<RegionView3D *>(region.regiondata);
      if (!rv3d->runtime->auto_clip_camera_view) {
        continue;
      }
      r_view = {v3d, &region, rv3d};
      return true;
    }
  }
  return false;
}

/** Write the clipping of the camera, within the same limits as the properties. */
static void view3d_camera_clip_set(Camera *camera, const float clip_start, const float clip_end)
{
  camera->clip_start = std::max(clip_start, 1.0e-6f);
  camera->clip_end = std::max(clip_end, camera->clip_start);

  DEG_id_tag_update(&camera->id, ID_RECALC_SYNC_TO_EVAL);
  WM_main_add_notifier(NC_OBJECT | ND_DRAW, camera);
}

/**
 * Range over the frames rendered, from the start to the end of the scene: the nearest and
 * furthest depth seen by the camera at any of them. It is computed in a job, as the scene is
 * evaluated at every frame, which can be long.
 */
struct AutoClipAnimationJob {
  wmWindowManager *wm = nullptr;
  wmOperator *op = nullptr;
  Depsgraph *depsgraph = nullptr;
  Scene *scene = nullptr;
  Camera *camera = nullptr;
  AutoClipCameraView view = {};
  /** Set when the result was written to the camera, read by the modal operator. */
  bool *r_applied = nullptr;

  /** Accumulated over the frames. */
  AutoClipDepthRange total;
  /** False when the view layer was not ready at a frame, the result is then not used. */
  bool is_ready = true;
};

/**
 * Evaluate the scene at every frame rendered and accumulate the depth range in \a job, then
 * evaluate the current frame again. With a \a worker_status it reports the progress and stops
 * when asked to (Esc, or the cancel button), without one it runs to the end.
 */
static void auto_clip_animation_range_calc(AutoClipAnimationJob &job,
                                           wmJobWorkerStatus *worker_status)
{
  Scene *scene = job.scene;
  const int frame_original = scene->r.cfra;
  const float subframe_original = scene->r.subframe;
  const int frame_step = std::max(int(scene->r.frame_step), 1);
  const int frames_count = (scene->r.efra - scene->r.sfra) / frame_step + 1;

  int frames_done = 0;
  for (int frame = scene->r.sfra; frame <= scene->r.efra; frame += frame_step) {
    if (worker_status != nullptr && (worker_status->stop || G.is_break)) {
      break;
    }
    scene->r.cfra = frame;
    scene->r.subframe = 0.0f;
    BKE_scene_graph_update_for_newframe(job.depsgraph);

    const Object *camera_eval = DEG_get_evaluated(job.depsgraph, job.view.v3d->camera);
    if (camera_eval == nullptr) {
      job.is_ready = false;
      break;
    }
    const float4x4 camera_from_world = auto_clip_camera_from_world_get(camera_eval,
                                                                       job.view.rv3d);
    const AutoClipFrustum frustum = auto_clip_frustum_get(
        job.depsgraph, job.view.v3d, job.view.region, job.view.rv3d);
    AutoClipDepthRange range;
    if (!auto_clip_camera_depth_range_calc(
            job.depsgraph, job.view.v3d, camera_from_world, frustum, range))
    {
      job.is_ready = false;
      break;
    }
    if (!range.is_empty()) {
      job.total.add(range.near);
      job.total.add(range.far);
    }

    frames_done++;
    if (worker_status != nullptr) {
      worker_status->progress = float(frames_done) / float(frames_count);
      worker_status->do_update = true;
    }
  }

  scene->r.cfra = frame_original;
  scene->r.subframe = subframe_original;
  BKE_scene_graph_update_for_newframe(job.depsgraph);
}

/** Write the result to the camera. \return false when the camera sees nothing. */
static bool auto_clip_animation_result_apply(AutoClipAnimationJob &job)
{
  if (!job.is_ready) {
    BKE_report(job.op->reports, RPT_WARNING, "The scene could not be evaluated, try again");
    return false;
  }
  if (job.total.is_empty()) {
    BKE_report(job.op->reports, RPT_WARNING, "The camera sees nothing during the animation");
    return false;
  }
  float clip_start, clip_end;
  auto_clip_camera_clip_from_depths(job.total.near, job.total.far, &clip_start, &clip_end);
  view3d_camera_clip_set(job.camera, clip_start, clip_end);
  return true;
}

/** Main thread, before the worker starts: lock the interface, the scene is evaluated at other
 * frames meanwhile. */
static void auto_clip_animation_initjob(void *customdata)
{
  AutoClipAnimationJob &job = *static_cast<AutoClipAnimationJob *>(customdata);
  G.is_rendering = true;
  G.is_break = false;
  WM_locked_interface_set(job.wm, true);
}

static void auto_clip_animation_startjob(void *customdata, wmJobWorkerStatus *worker_status)
{
  AutoClipAnimationJob &job = *static_cast<AutoClipAnimationJob *>(customdata);
  worker_status->progress = 0.0f;
  worker_status->do_update = true;
  auto_clip_animation_range_calc(job, worker_status);
  worker_status->progress = 1.0f;
  worker_status->do_update = true;
}

static void auto_clip_animation_endjob(void *customdata)
{
  AutoClipAnimationJob &job = *static_cast<AutoClipAnimationJob *>(customdata);
  WM_locked_interface_set(job.wm, false);
  G.is_rendering = false;
}

static void auto_clip_animation_completed(void *customdata)
{
  AutoClipAnimationJob &job = *static_cast<AutoClipAnimationJob *>(customdata);
  *job.r_applied = auto_clip_animation_result_apply(job);
}

static Camera *view3d_camera_clip_from_auto_camera_get(const bContext *C)
{
  return static_cast<Camera *>(CTX_data_pointer_get_type(C, "camera", RNA_Camera).data);
}

static bool view3d_camera_clip_from_auto_poll(bContext *C)
{
  const Camera *camera = view3d_camera_clip_from_auto_camera_get(C);
  if (camera == nullptr || !ID_IS_EDITABLE(&camera->id) || (camera->flag & CAM_AUTO_CLIP) == 0) {
    return false;
  }
  AutoClipCameraView view;
  return view3d_camera_auto_clip_find(C, camera, view);
}

/** The button of the camera uses the frames chosen in the menu next to it. */
static bool view3d_camera_clip_from_auto_use_animation(const Camera *camera)
{
  return (camera->flag & CAM_AUTO_CLIP_ANIMATION) != 0;
}

static wmOperatorStatus view3d_camera_clip_from_auto_exec(bContext *C, wmOperator *op)
{
  Camera *camera = view3d_camera_clip_from_auto_camera_get(C);
  AutoClipCameraView view;
  if (camera == nullptr || !view3d_camera_auto_clip_find(C, camera, view)) {
    return OPERATOR_CANCELLED;
  }

  if (view3d_camera_clip_from_auto_use_animation(camera)) {
    /* Without an interface (a script): all the frames, without progress. */
    AutoClipAnimationJob job;
    job.op = op;
    job.depsgraph = CTX_data_ensure_evaluated_depsgraph(C);
    job.scene = CTX_data_scene(C);
    job.camera = camera;
    job.view = view;
    auto_clip_animation_range_calc(job, nullptr);
    return auto_clip_animation_result_apply(job) ? OPERATOR_FINISHED : OPERATOR_CANCELLED;
  }

  view3d_camera_clip_set(
      camera, view.rv3d->runtime->auto_clip_start, view.rv3d->runtime->auto_clip_end);
  return OPERATOR_FINISHED;
}

static wmOperatorStatus view3d_camera_clip_from_auto_invoke(bContext *C,
                                                            wmOperator *op,
                                                            const wmEvent * /*event*/)
{
  Camera *camera = view3d_camera_clip_from_auto_camera_get(C);
  AutoClipCameraView view;
  if (camera == nullptr || !view3d_camera_auto_clip_find(C, camera, view)) {
    return OPERATOR_CANCELLED;
  }
  if (!view3d_camera_clip_from_auto_use_animation(camera)) {
    return view3d_camera_clip_from_auto_exec(C, op);
  }

  wmWindowManager *wm = CTX_wm_manager(C);
  Scene *scene = CTX_data_scene(C);
  bool *applied = MEM_new<bool>(__func__, false);
  op->customdata = applied;

  AutoClipAnimationJob *job = MEM_new<AutoClipAnimationJob>(__func__);
  job->wm = wm;
  job->op = op;
  job->depsgraph = CTX_data_ensure_evaluated_depsgraph(C);
  job->scene = scene;
  job->camera = camera;
  job->view = view;
  job->r_applied = applied;

  /* A progress bar and a cancel button in the status bar, Esc cancels too. */
  wmJob *wm_job = WM_jobs_get(wm,
                              CTX_wm_window(C),
                              scene,
                              "Computing the camera clipping...",
                              WM_JOB_PROGRESS,
                              WM_JOB_TYPE_CAMERA_CLIP_FROM_AUTO);
  WM_jobs_customdata_set(
      wm_job, job, [](void *job) { MEM_delete(static_cast<AutoClipAnimationJob *>(job)); });
  WM_jobs_timer(wm_job, 0.1, 0, NC_OBJECT | ND_DRAW);
  WM_jobs_callbacks_ex(wm_job,
                       auto_clip_animation_startjob,
                       auto_clip_animation_initjob,
                       nullptr,
                       auto_clip_animation_endjob,
                       auto_clip_animation_completed,
                       nullptr);
  WM_jobs_start(wm, wm_job);

  WM_event_add_modal_handler(C, op);
  return OPERATOR_RUNNING_MODAL;
}

static wmOperatorStatus view3d_camera_clip_from_auto_modal(bContext *C,
                                                           wmOperator *op,
                                                           const wmEvent * /*event*/)
{
  if (WM_jobs_has_running(
          CTX_wm_manager(C), CTX_data_scene(C), WM_JOB_TYPE_CAMERA_CLIP_FROM_AUTO))
  {
    return OPERATOR_PASS_THROUGH;
  }
  /* Finished or cancelled: only a finished one changed the camera (and is an undo step). */
  const bool applied = *static_cast<bool *>(op->customdata);
  MEM_delete(static_cast<bool *>(op->customdata));
  op->customdata = nullptr;
  return (applied ? OPERATOR_FINISHED : OPERATOR_CANCELLED) | OPERATOR_PASS_THROUGH;
}

void VIEW3D_OT_camera_clip_from_auto(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Apply Auto Clipping to Camera";
  ot->description =
      "Copy the clipping computed by Auto Clipping in the 3D Viewport to the Clip Near and "
      "Clip Far of the camera, used to render";
  ot->idname = "VIEW3D_OT_camera_clip_from_auto";

  /* API callbacks. */
  ot->exec = view3d_camera_clip_from_auto_exec;
  ot->invoke = view3d_camera_clip_from_auto_invoke;
  ot->modal = view3d_camera_clip_from_auto_modal;
  ot->poll = view3d_camera_clip_from_auto_poll;

  /* flags: not registered, running it again from the redo panel would evaluate the animation
   * again. */
  ot->flag = OPTYPE_UNDO;
}

/** \} */

}  // namespace blender
