/* SPDX-FileCopyrightText: 2020 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "editors/sculpt_paint/brushes/types.hh"

#include "BLI_array_utils.hh"
#include "BLI_enumerable_thread_specific.hh"
#include "BLI_math_matrix.h"
#include "BLI_math_matrix.hh"
#include "BLI_math_rotation.h"
#include "BLI_math_vector_types.hh"
#include "BLI_span.hh"
#include "BLI_task.h"

#include "DNA_brush_types.h"
#include "DNA_object_types.h"

#include "BKE_ccg.hh"
#include "BKE_mesh.hh"
#include "BKE_paint.hh"
#include "BKE_pbvh_api.hh"
#include "BKE_subdiv_ccg.hh"

#include "GPU_immediate.hh"
#include "GPU_matrix.hh"

#include "bmesh.hh"

#include <cmath>
#include <cstdlib>

#include "editors/sculpt_paint/mesh_brush_common.hh"
#include "editors/sculpt_paint/sculpt_intern.hh"

namespace blender::ed::sculpt_paint {

struct ScrapeSampleData {
  std::array<float3, 2> area_cos;
  std::array<float3, 2> area_nos;
  std::array<int, 2> area_count;
};

struct LocalData {
  Vector<float3> positions;
  Vector<float3> local_positions;
  Vector<float> factors;
  Vector<float> distances;
  Vector<float3> translations;
};

static ScrapeSampleData join_samples(const ScrapeSampleData &a, const ScrapeSampleData &b)
{
  ScrapeSampleData joined = a;

  joined.area_cos[0] = a.area_cos[0] + b.area_cos[0];
  joined.area_cos[1] = a.area_cos[1] + b.area_cos[1];

  joined.area_nos[0] = a.area_nos[0] + b.area_nos[0];
  joined.area_nos[1] = a.area_nos[1] + b.area_nos[1];

  joined.area_count[0] = a.area_count[0] + b.area_count[0];
  joined.area_count[1] = a.area_count[1] + b.area_count[1];
  return joined;
}

BLI_NOINLINE static void transform_positions(const Span<float3> src,
                                             const float4x4 &transform,
                                             const MutableSpan<float3> dst)
{
  BLI_assert(src.size() == dst.size());

  for (const int i : src.index_range()) {
    dst[i] = math::transform_point(transform, src[i]);
  }
}

BLI_NOINLINE static void filter_plane_side_factors(const Span<float3> positions,
                                                   const Span<float3> local_positions,
                                                   const std::array<float4, 2> &scrape_planes,
                                                   const MutableSpan<float> factors)
{
  BLI_assert(positions.size() == local_positions.size());
  BLI_assert(positions.size() == factors.size());

  for (const int i : local_positions.index_range()) {
    const bool plane_index = local_positions[i][0] <= 0.0f;
    if (plane_point_side_v3(scrape_planes[plane_index], positions[i]) <= 0.0f) {
      factors[i] = 0.0f;
    }
  }
}

BLI_NOINLINE static void calc_distances(const Span<float3> local_positions,
                                        const MutableSpan<float> distances)
{
  BLI_assert(local_positions.size() == distances.size());

  for (const int i : local_positions.index_range()) {
    /* Deform the local space along the Y axis to avoid artifacts on curved strokes. */
    /* This produces a not round brush tip. */
    float3 local = local_positions[i];
    local[1] *= 2.0f;
    distances[i] = math::length(local);
  }
}

BLI_NOINLINE static void calc_translations(const Span<float3> positions,
                                           const Span<float3> local_positions,
                                           const std::array<float4, 2> &scrape_planes,
                                           const MutableSpan<float3> translations)
{
  for (const int i : positions.index_range()) {
    const bool plane_index = local_positions[i][0] <= 0.0f;
    float3 closest;
    closest_to_plane_normalized_v3(closest, scrape_planes[plane_index], positions[i]);
    translations[i] = closest - positions[i];
  }
}

static void calc_multiplane_scrape_surface_task(Object &object,
                                                const Brush &brush,
                                                const float4x4 &mat,
                                                PBVHNode &node,
                                                ScrapeSampleData &sample)
{
  SculptSession &ss = *object.sculpt;

  PBVHVertexIter vd;

  SculptBrushTest test;
  SculptBrushTestFn sculpt_brush_test_sq_fn = SCULPT_brush_test_init_with_falloff_shape(
      ss, test, brush.falloff_shape);
  const int thread_id = BLI_task_parallel_thread_id(nullptr);

  /* Apply the brush normal radius to the test before sampling. */
  float test_radius = sqrtf(test.radius_squared);
  test_radius *= brush.normal_radius_factor;
  test.radius_squared = test_radius * test_radius;

  auto_mask::NodeData automask_data = auto_mask::node_begin(
      object, ss.cache->automasking.get(), node);

  BKE_pbvh_vertex_iter_begin (*ss.pbvh, &node, vd, PBVH_ITER_UNIQUE) {
    if (!sculpt_brush_test_sq_fn(test, vd.co)) {
      continue;
    }
    const float3 local_co = math::transform_point(mat, float3(vd.co));
    const float3 normal = vd.no ? float3(vd.no) : float3(vd.fno);

    auto_mask::node_update(automask_data, vd);

    /* Use the brush falloff to weight the sampled normals. */
    const float fade = SCULPT_brush_strength_factor(ss,
                                                    brush,
                                                    vd.co,
                                                    sqrtf(test.dist),
                                                    vd.no,
                                                    vd.fno,
                                                    vd.mask,
                                                    vd.vertex,
                                                    thread_id,
                                                    &automask_data);

    /* Sample the normal and area of the +X and -X axis individually. */
    const bool plane_index = local_co[0] <= 0.0f;
    sample.area_nos[plane_index] += normal * fade;
    sample.area_cos[plane_index] += vd.co;
    sample.area_count[plane_index]++;
    BKE_pbvh_vertex_iter_end;
  }
}

static void calc_faces(const Sculpt &sd,
                       const Brush &brush,
                       const float4x4 &mat,
                       const std::array<float4, 2> &scrape_planes,
                       const float angle,
                       const float strength,
                       const Span<float3> positions_eval,
                       const Span<float3> vert_normals,
                       const PBVHNode &node,
                       Object &object,
                       LocalData &tls,
                       const MutableSpan<float3> positions_orig)
{
  SculptSession &ss = *object.sculpt;
  const StrokeCache &cache = *ss.cache;
  Mesh &mesh = *static_cast<Mesh *>(object.data);

  const Span<int> verts = bke::pbvh::node_unique_verts(node);

  tls.positions.reinitialize(verts.size());
  MutableSpan<float3> positions = tls.positions;
  array_utils::gather(positions_eval, verts, positions);

  tls.factors.reinitialize(verts.size());
  const MutableSpan<float> factors = tls.factors;
  fill_factor_from_hide_and_mask(mesh, verts, factors);
  filter_region_clip_factors(ss, positions, factors);
  if (brush.flag & BRUSH_FRONTFACE) {
    calc_front_face(cache.view_normal, vert_normals, verts, factors);
  }
  if (cache.automasking) {
    auto_mask::calc_vert_factors(object, *cache.automasking, node, verts, factors);
  }

  tls.distances.reinitialize(verts.size());
  const MutableSpan<float> distances = tls.distances;
  /* NOTE: The distances are not used from this call, it's only used for filtering. */
  calc_distance_falloff(
      ss, positions, eBrushFalloffShape(brush.falloff_shape), distances, factors);

  tls.local_positions.reinitialize(verts.size());
  MutableSpan<float3> local_positions = tls.local_positions;
  transform_positions(positions, mat, local_positions);

  if (angle >= 0.0f) {
    filter_plane_side_factors(positions, local_positions, scrape_planes, factors);
  }

  calc_distances(local_positions, distances);

  apply_hardness_to_distances(cache, distances);
  calc_brush_strength_factors(cache, brush, distances, factors);

  tls.translations.reinitialize(verts.size());
  MutableSpan<float3> translations = tls.translations;
  calc_translations(positions, local_positions, scrape_planes, translations);

  filter_plane_trim_limit_factors(brush, cache, translations, factors);

  scale_factors(factors, strength);
  scale_translations(translations, factors);

  write_translations(sd, object, positions_eval, verts, translations, positions_orig);
}

static void calc_grids(const Sculpt &sd,
                       const Brush &brush,
                       const float4x4 &mat,
                       const std::array<float4, 2> &scrape_planes,
                       const float angle,
                       const float strength,
                       const PBVHNode &node,
                       Object &object,
                       LocalData &tls)
{
  SculptSession &ss = *object.sculpt;
  const StrokeCache &cache = *ss.cache;
  SubdivCCG &subdiv_ccg = *ss.subdiv_ccg;
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);

  const Span<int> grids = bke::pbvh::node_grid_indices(node);
  const int grid_verts_num = grids.size() * key.grid_area;

  tls.positions.reinitialize(grid_verts_num);
  MutableSpan<float3> positions = tls.positions;
  gather_grids_positions(subdiv_ccg, grids, positions);

  tls.factors.reinitialize(grid_verts_num);
  const MutableSpan<float> factors = tls.factors;
  fill_factor_from_hide_and_mask(subdiv_ccg, grids, factors);
  filter_region_clip_factors(ss, positions, factors);
  if (brush.flag & BRUSH_FRONTFACE) {
    calc_front_face(cache.view_normal, subdiv_ccg, grids, factors);
  }
  if (cache.automasking) {
    auto_mask::calc_grids_factors(object, *cache.automasking, node, grids, factors);
  }

  tls.distances.reinitialize(grid_verts_num);
  const MutableSpan<float> distances = tls.distances;
  /* NOTE: The distances are not used from this call, it's only used for filtering. */
  calc_distance_falloff(
      ss, positions, eBrushFalloffShape(brush.falloff_shape), distances, factors);

  tls.local_positions.reinitialize(grid_verts_num);
  MutableSpan<float3> local_positions = tls.local_positions;
  transform_positions(positions, mat, local_positions);

  if (angle >= 0.0f) {
    filter_plane_side_factors(positions, local_positions, scrape_planes, factors);
  }

  calc_distances(local_positions, distances);

  apply_hardness_to_distances(cache, distances);
  calc_brush_strength_factors(cache, brush, distances, factors);

  tls.translations.reinitialize(grid_verts_num);
  MutableSpan<float3> translations = tls.translations;
  calc_translations(positions, local_positions, scrape_planes, translations);

  filter_plane_trim_limit_factors(brush, cache, translations, factors);

  scale_factors(factors, strength);
  scale_translations(translations, factors);

  clip_and_lock_translations(sd, ss, positions, translations);
  apply_translations(translations, grids, subdiv_ccg);
}

static void calc_bmesh(const Sculpt &sd,
                       const Brush &brush,
                       const float4x4 &mat,
                       const std::array<float4, 2> &scrape_planes,
                       const float angle,
                       const float strength,
                       PBVHNode &node,
                       Object &object,
                       LocalData &tls)
{
  SculptSession &ss = *object.sculpt;
  const StrokeCache &cache = *ss.cache;

  const Set<BMVert *, 0> &verts = BKE_pbvh_bmesh_node_unique_verts(&node);

  tls.positions.reinitialize(verts.size());
  MutableSpan<float3> positions = tls.positions;
  gather_bmesh_positions(verts, positions);

  tls.factors.reinitialize(verts.size());
  const MutableSpan<float> factors = tls.factors;
  fill_factor_from_hide_and_mask(*ss.bm, verts, factors);
  filter_region_clip_factors(ss, positions, factors);
  if (brush.flag & BRUSH_FRONTFACE) {
    calc_front_face(cache.view_normal, verts, factors);
  }
  if (cache.automasking) {
    auto_mask::calc_vert_factors(object, *cache.automasking, node, verts, factors);
  }

  tls.distances.reinitialize(verts.size());
  const MutableSpan<float> distances = tls.distances;
  /* NOTE: The distances are not used from this call, it's only used for filtering. */
  calc_distance_falloff(
      ss, positions, eBrushFalloffShape(brush.falloff_shape), distances, factors);

  tls.local_positions.reinitialize(verts.size());
  MutableSpan<float3> local_positions = tls.local_positions;
  transform_positions(positions, mat, local_positions);

  if (angle >= 0.0f) {
    filter_plane_side_factors(positions, local_positions, scrape_planes, factors);
  }

  calc_distances(local_positions, distances);

  apply_hardness_to_distances(cache, distances);
  calc_brush_strength_factors(cache, brush, distances, factors);

  tls.translations.reinitialize(verts.size());
  MutableSpan<float3> translations = tls.translations;
  calc_translations(positions, local_positions, scrape_planes, translations);

  filter_plane_trim_limit_factors(brush, cache, translations, factors);

  scale_factors(factors, strength);
  scale_translations(translations, factors);

  clip_and_lock_translations(sd, ss, positions, translations);
  apply_translations(translations, verts);
}

void do_multiplane_scrape_brush(const Sculpt &sd, Object &object, const Span<PBVHNode *> nodes)
{
  SculptSession &ss = *object.sculpt;
  const Brush &brush = *BKE_paint_brush_for_read(&sd.paint);

  const bool flip = (ss.cache->bstrength < 0.0f);
  const float radius = flip ? -ss.cache->radius : ss.cache->radius;
  const float offset = SCULPT_brush_plane_offset_get(sd, ss);
  const float displace = -radius * offset;

  float3 area_no_sp;
  float3 area_co;
  calc_brush_plane(brush, object, nodes, area_no_sp, area_co);

  float3 area_no;
  if (brush.sculpt_plane != SCULPT_DISP_DIR_AREA || (brush.flag & BRUSH_ORIGINAL_NORMAL)) {
    area_no = calc_area_normal(brush, object, nodes).value_or(float3(0));
  }
  else {
    area_no = area_no_sp;
  }

  /* Delay the first daub because grab delta is not setup. */
  if (SCULPT_stroke_is_first_brush_step_of_symmetry_pass(*ss.cache)) {
    ss.cache->multiplane_scrape_angle = 0.0f;
    return;
  }

  if (is_zero_v3(ss.cache->grab_delta_symmetry)) {
    return;
  }

  area_co = area_no_sp * ss.cache->scale * displace;

  /* Init brush local space matrix. */
  float4x4 mat = float4x4::identity();
  mat.x_axis() = math::cross(area_no, ss.cache->grab_delta_symmetry);
  mat.y_axis() = math::cross(area_no, mat.x_axis());
  mat.z_axis() = area_no;
  mat.location() = ss.cache->location;
  /* NOTE: #math::normalize behaves differently for some reason. */
  normalize_m4(mat.ptr());
  mat = math::invert(mat);

  /* Update matrix for the cursor preview. */
  if (ss.cache->mirror_symmetry_pass == 0 && ss.cache->radial_symmetry_pass == 0) {
    ss.cache->stroke_local_mat = mat;
  }

  /* Dynamic mode. */

  if (brush.flag2 & BRUSH_MULTIPLANE_SCRAPE_DYNAMIC) {
    /* Sample the individual normal and area center of the two areas at both sides of the cursor.
     */
    const ScrapeSampleData sample = threading::parallel_reduce(
        nodes.index_range(),
        1,
        ScrapeSampleData{},
        [&](const IndexRange range, ScrapeSampleData sample) {
          for (const int i : range) {
            calc_multiplane_scrape_surface_task(object, brush, mat, *nodes[i], sample);
          }
          return sample;
        },
        join_samples);

    /* Use the area center of both planes to detect if we are sculpting along a concave or convex
     * edge. */
    const std::array<float3, 2> sampled_plane_co{
        sample.area_cos[0] * 1.0f / float(sample.area_count[0]),
        sample.area_cos[1] * 1.0f / float(sample.area_count[1])};
    const float3 mid_co = math::midpoint(sampled_plane_co[0], sampled_plane_co[1]);

    /* Calculate the scrape planes angle based on the sampled normals. */
    const std::array<float3, 2> sampled_plane_normals{
        math::normalize(sample.area_nos[0] * 1.0f / float(sample.area_count[0])),
        math::normalize(sample.area_nos[1] * 1.0f / float(sample.area_count[1]))};

    float sampled_angle = angle_v3v3(sampled_plane_normals[0], sampled_plane_normals[1]);
    const std::array<float3, 2> sampled_cv{area_no, ss.cache->location - mid_co};

    sampled_angle += DEG2RADF(brush.multiplane_scrape_angle) * ss.cache->pressure;

    /* Invert the angle if we are sculpting along a concave edge. */
    if (math::dot(sampled_cv[0], sampled_cv[1]) < 0.0f) {
      sampled_angle = -sampled_angle;
    }

    /* In dynamic mode, set the angle to 0 when inverting the brush, so you can trim plane
     * surfaces without changing the brush. */
    if (flip) {
      sampled_angle = 0.0f;
    }
    else {
      area_co = ss.cache->location;
    }

    /* Interpolate between the previous and new sampled angles to avoid artifacts when if angle
     * difference between two samples is too big. */
    ss.cache->multiplane_scrape_angle = math::interpolate(
        RAD2DEGF(sampled_angle), ss.cache->multiplane_scrape_angle, 0.2f);
  }
  else {
    /* Standard mode: Scrape with the brush property fixed angle. */
    area_co = ss.cache->location;
    ss.cache->multiplane_scrape_angle = brush.multiplane_scrape_angle;
    if (flip) {
      ss.cache->multiplane_scrape_angle *= -1.0f;
    }
  }

  /* Calculate the final left and right scrape planes. */
  float3 plane_no;
  float3 plane_no_rot;
  const float3 y_axis(0.0f, 1.0f, 0.0f);
  const float4x4 mat_inv = math::invert(mat);

  std::array<float4, 2> multiplane_scrape_planes;

  mul_v3_mat3_m4v3(plane_no, mat.ptr(), area_no);
  rotate_v3_v3v3fl(
      plane_no_rot, plane_no, y_axis, DEG2RADF(-ss.cache->multiplane_scrape_angle * 0.5f));
  mul_v3_mat3_m4v3(plane_no, mat_inv.ptr(), plane_no_rot);
  normalize_v3(plane_no);
  plane_from_point_normal_v3(multiplane_scrape_planes[1], area_co, plane_no);

  mul_v3_mat3_m4v3(plane_no, mat.ptr(), area_no);
  rotate_v3_v3v3fl(
      plane_no_rot, plane_no, y_axis, DEG2RADF(ss.cache->multiplane_scrape_angle * 0.5f));
  mul_v3_mat3_m4v3(plane_no, mat_inv.ptr(), plane_no_rot);
  normalize_v3(plane_no);
  plane_from_point_normal_v3(multiplane_scrape_planes[0], area_co, plane_no);

  const float strength = std::abs(ss.cache->bstrength);

  threading::EnumerableThreadSpecific<LocalData> all_tls;
  switch (BKE_pbvh_type(*object.sculpt->pbvh)) {
    case PBVH_FACES: {
      Mesh &mesh = *static_cast<Mesh *>(object.data);
      const PBVH &pbvh = *ss.pbvh;
      const Span<float3> positions_eval = BKE_pbvh_get_vert_positions(pbvh);
      const Span<float3> vert_normals = BKE_pbvh_get_vert_normals(pbvh);
      MutableSpan<float3> positions_orig = mesh.vert_positions_for_write();
      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        /* Isolate because of thread local variables and multithreading inside #calc_faces. */
        threading::isolate_task([&]() {
          for (const int i : range) {
            calc_faces(sd,
                       brush,
                       mat,
                       multiplane_scrape_planes,
                       ss.cache->multiplane_scrape_angle,
                       strength,
                       positions_eval,
                       vert_normals,
                       *nodes[i],
                       object,
                       tls,
                       positions_orig);
            BKE_pbvh_node_mark_positions_update(nodes[i]);
          }
        });
      });
      break;
    }
    case PBVH_GRIDS:
      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        for (const int i : range) {
          calc_grids(sd,
                     brush,
                     mat,
                     multiplane_scrape_planes,
                     ss.cache->multiplane_scrape_angle,
                     strength,
                     *nodes[i],
                     object,
                     tls);
        }
      });
      break;
    case PBVH_BMESH:
      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        for (const int i : range) {
          calc_bmesh(sd,
                     brush,
                     mat,
                     multiplane_scrape_planes,
                     ss.cache->multiplane_scrape_angle,
                     strength,
                     *nodes[i],
                     object,
                     tls);
        }
      });
      break;
  }
}

void multiplane_scrape_preview_draw(const uint gpuattr,
                                    const Brush &brush,
                                    const SculptSession &ss,
                                    const float outline_col[3],
                                    const float outline_alpha)
{
  if (!(brush.flag2 & BRUSH_MULTIPLANE_SCRAPE_PLANES_PREVIEW)) {
    return;
  }

  float4x4 local_mat_inv = math::invert(ss.cache->stroke_local_mat);
  GPU_matrix_mul(local_mat_inv.ptr());
  float angle = ss.cache->multiplane_scrape_angle;
  if (ss.cache->pen_flip || ss.cache->invert) {
    angle = -angle;
  }

  float offset = ss.cache->radius * 0.25f;

  const float3 p{0.0f, 0.0f, ss.cache->radius};
  const float3 y_axis{0.0f, 1.0f, 0.0f};
  float3 p_l;
  float3 p_r;
  const float3 area_center(0);
  rotate_v3_v3v3fl(p_r, p, y_axis, DEG2RADF((angle + 180) * 0.5f));
  rotate_v3_v3v3fl(p_l, p, y_axis, DEG2RADF(-(angle + 180) * 0.5f));

  immBegin(GPU_PRIM_LINES, 14);
  immVertex3f(gpuattr, area_center[0], area_center[1] + offset, area_center[2]);
  immVertex3f(gpuattr, p_r[0], p_r[1] + offset, p_r[2]);
  immVertex3f(gpuattr, area_center[0], area_center[1] + offset, area_center[2]);
  immVertex3f(gpuattr, p_l[0], p_l[1] + offset, p_l[2]);

  immVertex3f(gpuattr, area_center[0], area_center[1] - offset, area_center[2]);
  immVertex3f(gpuattr, p_r[0], p_r[1] - offset, p_r[2]);
  immVertex3f(gpuattr, area_center[0], area_center[1] - offset, area_center[2]);
  immVertex3f(gpuattr, p_l[0], p_l[1] - offset, p_l[2]);

  immVertex3f(gpuattr, area_center[0], area_center[1] - offset, area_center[2]);
  immVertex3f(gpuattr, area_center[0], area_center[1] + offset, area_center[2]);

  immVertex3f(gpuattr, p_r[0], p_r[1] - offset, p_r[2]);
  immVertex3f(gpuattr, p_r[0], p_r[1] + offset, p_r[2]);

  immVertex3f(gpuattr, p_l[0], p_l[1] - offset, p_l[2]);
  immVertex3f(gpuattr, p_l[0], p_l[1] + offset, p_l[2]);

  immEnd();

  immUniformColor3fvAlpha(outline_col, outline_alpha * 0.1f);
  immBegin(GPU_PRIM_TRIS, 12);
  immVertex3f(gpuattr, area_center[0], area_center[1] + offset, area_center[2]);
  immVertex3f(gpuattr, p_r[0], p_r[1] + offset, p_r[2]);
  immVertex3f(gpuattr, p_r[0], p_r[1] - offset, p_r[2]);
  immVertex3f(gpuattr, area_center[0], area_center[1] + offset, area_center[2]);
  immVertex3f(gpuattr, area_center[0], area_center[1] - offset, area_center[2]);
  immVertex3f(gpuattr, p_r[0], p_r[1] - offset, p_r[2]);

  immVertex3f(gpuattr, area_center[0], area_center[1] + offset, area_center[2]);
  immVertex3f(gpuattr, p_l[0], p_l[1] + offset, p_l[2]);
  immVertex3f(gpuattr, p_l[0], p_l[1] - offset, p_l[2]);
  immVertex3f(gpuattr, area_center[0], area_center[1] + offset, area_center[2]);
  immVertex3f(gpuattr, area_center[0], area_center[1] - offset, area_center[2]);
  immVertex3f(gpuattr, p_l[0], p_l[1] - offset, p_l[2]);

  immEnd();
}

}  // namespace blender::ed::sculpt_paint
