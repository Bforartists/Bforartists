/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "BLI_array.hh"
#include "BLI_bit_span.hh"
#include "BLI_math_matrix_types.hh"
#include "BLI_math_vector_types.hh"
#include "BLI_offset_indices.hh"
#include "BLI_set.hh"
#include "BLI_span.hh"
#include "BLI_vector.hh"

#include "BKE_subdiv_ccg.hh"

#include "DNA_brush_enums.h"

#include "sculpt_intern.hh"

/**
 * This file contains common operations useful for the implementation of various different brush
 * tools. The design goals of the API are to always operate on more than one data element at a
 * time, to avoid unnecessary branching for constants, favor cache-friendly access patterns, enable
 * use of SIMD, and provide opportunities to avoid work where possible.
 *
 * API function arguments should favor passing raw data references rather than general catch-all
 * storage structs in order to clarify the scope of each function, structure the work around the
 * required data, and limit redundant data storage.
 *
 * Many functions calculate "factors" which describe how strong the brush influence should be
 * between 0 and 1. Most functions multiply with the existing factor value rather than assigning a
 * new value from scratch.
 */

struct BMesh;
struct BMVert;
struct BMFace;
struct Brush;
struct Mesh;
struct Object;
struct Sculpt;
struct SculptSession;
struct SubdivCCG;
struct SubdivCCGCoord;
struct SubdivCCGNeighbors;
namespace blender {
namespace bke::pbvh {
class Node;
class Tree;
}  // namespace bke::pbvh
}  // namespace blender

namespace blender::ed::sculpt_paint {
struct StrokeCache;

namespace auto_mask {
struct Cache;
};

void scale_translations(MutableSpan<float3> translations, Span<float> factors);
void scale_translations(MutableSpan<float3> translations, float factor);
void scale_factors(MutableSpan<float> factors, float strength);
void scale_factors(MutableSpan<float> factors, Span<float> strengths);
void translations_from_offset_and_factors(const float3 &offset,
                                          Span<float> factors,
                                          MutableSpan<float3> r_translations);

/**
 * For brushes that calculate an averaged new position instead of generating a new translation
 * vector.
 */
void translations_from_new_positions(Span<float3> new_positions,
                                     Span<int> verts,
                                     Span<float3> old_positions,
                                     MutableSpan<float3> translations);
void translations_from_new_positions(Span<float3> new_positions,
                                     Span<float3> old_positions,
                                     MutableSpan<float3> translations);

void transform_positions(Span<float3> src, const float4x4 &transform, MutableSpan<float3> dst);
void transform_positions(const float4x4 &transform, MutableSpan<float3> positions);

/** Gather data from an array aligned with all geometry vertices. */
template<typename T> void gather_data_mesh(Span<T> src, Span<int> indices, MutableSpan<T> dst);
template<typename T>
MutableSpan<T> gather_data_mesh(const Span<T> src, const Span<int> indices, Vector<T> &dst)
{
  dst.resize(indices.size());
  gather_data_mesh(src, indices, dst.as_mutable_span());
  return dst;
}
template<typename T>
void gather_data_grids(const SubdivCCG &subdiv_ccg,
                       Span<T> src,
                       Span<int> grids,
                       MutableSpan<T> node_data);
template<typename T>
MutableSpan<T> gather_data_grids(const SubdivCCG &subdiv_ccg,
                                 const Span<T> src,
                                 const Span<int> grids,
                                 Vector<T> &dst)
{
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
  dst.resize(grids.size() * key.grid_area);
  gather_data_grids(subdiv_ccg, src, grids, dst.as_mutable_span());
  return dst;
}

template<typename T>
void gather_data_bmesh(Span<T> src, const Set<BMVert *, 0> &verts, MutableSpan<T> node_data);
template<typename T>
MutableSpan<T> gather_data_bmesh(const Span<T> src, const Set<BMVert *, 0> &verts, Vector<T> &dst)
{
  dst.resize(verts.size());
  gather_data_bmesh(src, verts, dst.as_mutable_span());
  return dst;
}

/** Scatter data from an array of the node's data to the referenced geometry vertices. */
template<typename T> void scatter_data_mesh(Span<T> src, Span<int> indices, MutableSpan<T> dst);
template<typename T>
void scatter_data_grids(const SubdivCCG &subdiv_ccg,
                        Span<T> node_data,
                        Span<int> grids,
                        MutableSpan<T> dst);
template<typename T>
void scatter_data_bmesh(Span<T> node_data, const Set<BMVert *, 0> &verts, MutableSpan<T> dst);

/**
 * Note on the various positions arrays:
 * - positions_orig: Positions owned by the original mesh. Not the same as `positions_eval` if
 *   there are deform modifiers.
 * - positions_eval: Positions after procedural deformation, used to build the
 * blender::bke::pbvh::Tree. Translations are built for these values, then applied to
 * `positions_orig`.
 */

/** Fill the output array with all positions in the geometry referenced by the indices. */
void gather_grids_positions(const CCGKey &key,
                            Span<CCGElem *> elems,
                            Span<int> grids,
                            MutableSpan<float3> positions);
inline MutableSpan<float3> gather_grids_positions(const SubdivCCG &subdiv_ccg,
                                                  const Span<int> grids,
                                                  Vector<float3> &positions)
{
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
  positions.resize(key.grid_area * grids.size());
  gather_grids_positions(key, subdiv_ccg.grids, grids, positions);
  return positions;
}
void gather_bmesh_positions(const Set<BMVert *, 0> &verts, MutableSpan<float3> positions);
inline MutableSpan<float3> gather_bmesh_positions(const Set<BMVert *, 0> &verts,
                                                  Vector<float3> &positions)
{
  positions.resize(verts.size());
  gather_bmesh_positions(verts, positions.as_mutable_span());
  return positions;
}

/** Fill the output array with all normals in the grids referenced by the indices. */
void gather_grids_normals(const SubdivCCG &subdiv_ccg,
                          Span<int> grids,
                          MutableSpan<float3> normals);
void gather_bmesh_normals(const Set<BMVert *, 0> &verts, MutableSpan<float3> normals);

/**
 * Calculate initial influence factors based on vertex visibility.
 */
void fill_factor_from_hide(const Mesh &mesh, Span<int> vert_indices, MutableSpan<float> r_factors);
void fill_factor_from_hide(const SubdivCCG &subdiv_ccg,
                           Span<int> grids,
                           MutableSpan<float> r_factors);
void fill_factor_from_hide(const Set<BMVert *, 0> &verts, MutableSpan<float> r_factors);

/**
 * Calculate initial influence factors based on vertex visibility and masking.
 */
void fill_factor_from_hide_and_mask(const Mesh &mesh,
                                    Span<int> vert_indices,
                                    MutableSpan<float> r_factors);
void fill_factor_from_hide_and_mask(const SubdivCCG &subdiv_ccg,
                                    Span<int> grids,
                                    MutableSpan<float> r_factors);
void fill_factor_from_hide_and_mask(const BMesh &bm,
                                    const Set<BMVert *, 0> &verts,
                                    MutableSpan<float> r_factors);

/**
 * Disable brush influence when vertex normals point away from the view.
 */
void calc_front_face(const float3 &view_normal, Span<float3> normals, MutableSpan<float> factors);
void calc_front_face(const float3 &view_normal,
                     Span<float3> vert_normals,
                     Span<int> vert_indices,
                     MutableSpan<float> factors);
void calc_front_face(const float3 &view_normal,
                     const SubdivCCG &subdiv_ccg,
                     Span<int> grids,
                     MutableSpan<float> factors);
void calc_front_face(const float3 &view_normal,
                     const Set<BMVert *, 0> &verts,
                     MutableSpan<float> factors);
void calc_front_face(const float3 &view_normal,
                     const Set<BMFace *, 0> &faces,
                     MutableSpan<float> factors);

/**
 * When the 3D view's clipping planes are enabled, brushes shouldn't have any effect on vertices
 * outside of the planes, because they're not visible. This function disables the factors for those
 * vertices.
 */
void filter_region_clip_factors(const SculptSession &ss,
                                Span<float3> vert_positions,
                                Span<int> verts,
                                MutableSpan<float> factors);
void filter_region_clip_factors(const SculptSession &ss,
                                Span<float3> positions,
                                MutableSpan<float> factors);

/**
 * Calculate distances based on the distance from the brush cursor and various other settings.
 * Also ignore vertices that are too far from the cursor.
 */
void calc_brush_distances(const SculptSession &ss,
                          Span<float3> vert_positions,
                          Span<int> vert_indices,
                          eBrushFalloffShape falloff_shape,
                          MutableSpan<float> r_distances);
void calc_brush_distances(const SculptSession &ss,
                          Span<float3> positions,
                          eBrushFalloffShape falloff_shape,
                          MutableSpan<float> r_distances);
void calc_brush_distances_squared(const SculptSession &ss,
                                  Span<float3> vert_positions,
                                  Span<int> vert_indices,
                                  eBrushFalloffShape falloff_shape,
                                  MutableSpan<float> r_distances);
void calc_brush_distances_squared(const SculptSession &ss,
                                  Span<float3> positions,
                                  eBrushFalloffShape falloff_shape,
                                  MutableSpan<float> r_distances);

/** Set the factor to zero for all distances greater than the radius. */
void filter_distances_with_radius(float radius, Span<float> distances, MutableSpan<float> factors);

/**
 * Calculate distances based on a "square" brush tip falloff and ignore vertices that are too far
 * away.
 */
void calc_brush_cube_distances(const Brush &brush,
                               const float4x4 &mat,
                               Span<float3> positions,
                               Span<int> verts,
                               MutableSpan<float> r_distances,
                               MutableSpan<float> factors);
void calc_brush_cube_distances(const Brush &brush,
                               const float4x4 &mat,
                               Span<float3> positions,
                               MutableSpan<float> r_distances,
                               MutableSpan<float> factors);

/**
 * Scale the distances based on the brush radius and the cached "hardness" setting, which increases
 * the strength of the effect for vertices towards the outside of the radius.
 */
void apply_hardness_to_distances(float radius, float hardness, MutableSpan<float> distances);
inline void apply_hardness_to_distances(const StrokeCache &cache,
                                        const MutableSpan<float> distances)
{
  apply_hardness_to_distances(cache.radius, cache.hardness, distances);
}

/**
 * Modify the factors based on distances to the brush cursor, using various brush settings.
 */
void calc_brush_strength_factors(const StrokeCache &cache,
                                 const Brush &brush,
                                 Span<float> distances,
                                 MutableSpan<float> factors);

/**
 * Modify brush influence factors to include sampled texture values.
 */
void calc_brush_texture_factors(const SculptSession &ss,
                                const Brush &brush,
                                Span<float3> vert_positions,
                                Span<int> vert_indices,
                                MutableSpan<float> factors);
void calc_brush_texture_factors(const SculptSession &ss,
                                const Brush &brush,
                                Span<float3> positions,
                                MutableSpan<float> factors);

namespace auto_mask {

/**
 * Calculate all auto-masking influence on each vertex.
 */
void calc_vert_factors(const Depsgraph &depsgraph,
                       const Object &object,
                       const Cache &cache,
                       const bke::pbvh::MeshNode &node,
                       Span<int> verts,
                       MutableSpan<float> factors);
inline void calc_vert_factors(const Depsgraph &depsgraph,
                              const Object &object,
                              const Cache *cache,
                              const bke::pbvh::MeshNode &node,
                              Span<int> verts,
                              MutableSpan<float> factors)
{
  if (cache == nullptr) {
    return;
  }
  calc_vert_factors(depsgraph, object, *cache, node, verts, factors);
}
void calc_grids_factors(const Depsgraph &depsgraph,
                        const Object &object,
                        const Cache &cache,
                        const bke::pbvh::GridsNode &node,
                        Span<int> grids,
                        MutableSpan<float> factors);
inline void calc_grids_factors(const Depsgraph &depsgraph,
                               const Object &object,
                               const Cache *cache,
                               const bke::pbvh::GridsNode &node,
                               Span<int> grids,
                               MutableSpan<float> factors)
{
  if (cache == nullptr) {
    return;
  }
  calc_grids_factors(depsgraph, object, *cache, node, grids, factors);
}
void calc_vert_factors(const Depsgraph &depsgraph,
                       const Object &object,
                       const Cache &cache,
                       const bke::pbvh::BMeshNode &node,
                       const Set<BMVert *, 0> &verts,
                       MutableSpan<float> factors);
inline void calc_vert_factors(const Depsgraph &depsgraph,
                              const Object &object,
                              const Cache *cache,
                              const bke::pbvh::BMeshNode &node,
                              const Set<BMVert *, 0> &verts,
                              MutableSpan<float> factors)
{
  if (cache == nullptr) {
    return;
  }
  calc_vert_factors(depsgraph, object, *cache, node, verts, factors);
}

/**
 * Calculate all auto-masking influence on each face.
 */
void calc_face_factors(const Depsgraph &depsgraph,
                       const Object &object,
                       OffsetIndices<int> faces,
                       Span<int> corner_verts,
                       const Cache &cache,
                       const bke::pbvh::MeshNode &node,
                       Span<int> face_indices,
                       MutableSpan<float> factors);

}  // namespace auto_mask

/**
 * Many brushes end up calculating translations from the original positions. Instead of applying
 * these directly to the modified values, it's helpful to process them separately to easily
 * calculate various effects like clipping. After they are processed, this function can be used to
 * simply add them to the final vertex positions.
 */
void apply_translations(Span<float3> translations, Span<int> verts, MutableSpan<float3> positions);
void apply_translations(Span<float3> translations, Span<int> grids, SubdivCCG &subdiv_ccg);
void apply_translations(Span<float3> translations, const Set<BMVert *, 0> &verts);

/** Align the translations with plane normal. */
void project_translations(MutableSpan<float3> translations, const float3 &plane);

/**
 * Cancel out translations already applied over the course of the operation from the new
 * translations. This is used for tools that calculate new positions based on the original
 * positions for the entirety of an operation. Conceptually this is the same as resetting the
 * positions before each step of the operation, but combining that into the same loop should be
 * preferable for performance.
 */
void reset_translations_to_original(MutableSpan<float3> translations,
                                    Span<float3> positions,
                                    Span<float3> orig_positions);

/**
 * Rotate translations to account for rotations from procedural deformation.
 *
 * \todo Don't invert `deform_imats` on object evaluation. Instead just invert them on-demand in
 * brush implementations. This would be better because only the inversions required for affected
 * vertices would be necessary.
 */
void apply_crazyspace_to_translations(Span<float3x3> deform_imats,
                                      Span<int> verts,
                                      MutableSpan<float3> translations);

/**
 * Modify translations based on sculpt mode axis locking and mirroring clipping.
 */
void clip_and_lock_translations(const Sculpt &sd,
                                const SculptSession &ss,
                                Span<float3> positions,
                                Span<int> verts,
                                MutableSpan<float3> translations);
void clip_and_lock_translations(const Sculpt &sd,
                                const SculptSession &ss,
                                Span<float3> positions,
                                MutableSpan<float3> translations);

/**
 * Applying final positions to shape keys is non-trivial because the mesh positions and the active
 * shape key positions must be kept in sync, and shape keys dependent on the active key must also
 * be modified.
 */
void update_shape_keys(Object &object,
                       const Mesh &mesh,
                       const KeyBlock &active_key,
                       Span<int> verts,
                       Span<float3> translations,
                       Span<float3> positions_orig);

/**
 * Write the new translated positions to the original mesh, taking into account inverse
 * deformation from modifiers, axis locking, and clipping. Flush the deformation to shape keys as
 * well.
 */
void write_translations(const Depsgraph &depsgraph,
                        const Sculpt &sd,
                        Object &object,
                        Span<float3> positions_eval,
                        Span<int> verts,
                        MutableSpan<float3> translations,
                        MutableSpan<float3> positions_orig);

/**
 * Creates OffsetIndices based on each node's unique vertex count, allowing for easy slicing of a
 * new array.
 */
OffsetIndices<int> create_node_vert_offsets(const Span<bke::pbvh::MeshNode> nodes,
                                            const IndexMask &nodes_mask,
                                            Array<int> &node_data);
OffsetIndices<int> create_node_vert_offsets(const CCGKey &key,
                                            const Span<bke::pbvh::GridsNode> nodes,
                                            const IndexMask &nodes_mask,
                                            Array<int> &node_data);
OffsetIndices<int> create_node_vert_offsets_bmesh(const Span<bke::pbvh::BMeshNode> nodes,
                                                  const IndexMask &nodes_mask,
                                                  Array<int> &node_data);

/**
 * Find vertices connected to the indexed vertices across faces.
 *
 * Does not handle boundary vertices differently, so this method is generally inappropriate for
 * functions that are related to coordinates. See #calc_vert_neighbors_interior
 *
 * \note A vector allocated per element is typically not a good strategy for performance because
 * of each vector's 24 byte overhead, non-contiguous memory, and the possibility of further heap
 * allocations. However, it's done here for now for two reasons:
 *  1. In typical quad meshes there are just 4 neighbors, which fit in the inline buffer.
 *  2. We want to avoid using edges, and the remaining topology map we have access to is the
 *     vertex to face map. That requires deduplication when building the neighbors, which
 *     requires some intermediate data structure like a vector anyway.
 */
void calc_vert_neighbors(OffsetIndices<int> faces,
                         Span<int> corner_verts,
                         GroupedSpan<int> vert_to_face,
                         Span<bool> hide_poly,
                         Span<int> verts,
                         MutableSpan<Vector<int>> result);
void calc_vert_neighbors(const SubdivCCG &subdiv_ccg,
                         Span<int> grids,
                         MutableSpan<Vector<SubdivCCGCoord>> result);
void calc_vert_neighbors(Set<BMVert *, 0> verts, MutableSpan<Vector<BMVert *>> result);

/**
 * Find vertices connected to the indexed vertices across faces. For boundary vertices (stored in
 * the \a boundary_verts argument), only include other boundary vertices. Also skip connectivity
 * across hidden faces and skip neighbors of corner vertices.
 *
 * \note See #calc_vert_neighbors for information on why we use a Vector per element.
 */
void calc_vert_neighbors_interior(OffsetIndices<int> faces,
                                  Span<int> corner_verts,
                                  GroupedSpan<int> vert_to_face,
                                  BitSpan boundary_verts,
                                  Span<bool> hide_poly,
                                  Span<int> verts,
                                  MutableSpan<Vector<int>> result);
void calc_vert_neighbors_interior(OffsetIndices<int> faces,
                                  Span<int> corner_verts,
                                  BitSpan boundary_verts,
                                  const SubdivCCG &subdiv_ccg,
                                  Span<int> grids,
                                  MutableSpan<Vector<SubdivCCGCoord>> result);
void calc_vert_neighbors_interior(const Set<BMVert *, 0> &verts,
                                  MutableSpan<Vector<BMVert *>> result);

/** Find the translation from each vertex position to the closest point on the plane. */
void calc_translations_to_plane(Span<float3> vert_positions,
                                Span<int> verts,
                                const float4 &plane,
                                MutableSpan<float3> translations);
void calc_translations_to_plane(Span<float3> positions,
                                const float4 &plane,
                                MutableSpan<float3> translations);

/** Ignores verts outside of a symmetric area defined by a pivot point. */
void filter_verts_outside_symmetry_area(Span<float3> positions,
                                        const float3 &pivot,
                                        ePaintSymmetryFlags symm,
                                        MutableSpan<float> factors);

/** Ignore points that fall below the "plane trim" threshold for the brush. */
void filter_plane_trim_limit_factors(const Brush &brush,
                                     const StrokeCache &cache,
                                     Span<float3> translations,
                                     MutableSpan<float> factors);

/** Ignore points below the plane. */
void filter_below_plane_factors(Span<float3> vert_positions,
                                Span<int> verts,
                                const float4 &plane,
                                MutableSpan<float> factors);
void filter_below_plane_factors(Span<float3> positions,
                                const float4 &plane,
                                MutableSpan<float> factors);

/* Ignore points above the plane. */
void filter_above_plane_factors(Span<float3> vert_positions,
                                Span<int> verts,
                                const float4 &plane,
                                MutableSpan<float> factors);
void filter_above_plane_factors(Span<float3> positions,
                                const float4 &plane,
                                MutableSpan<float> factors);

}  // namespace blender::ed::sculpt_paint
