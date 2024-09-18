/* SPDX-FileCopyrightText: 2018 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 */

#pragma once

#include <memory>

#include "BLI_array.hh"
#include "BLI_bit_group_vector.hh"
#include "BLI_bit_span_ops.hh"
#include "BLI_index_mask_fwd.hh"
#include "BLI_offset_indices.hh"
#include "BLI_span.hh"
#include "BLI_sys_types.h"
#include "BLI_utility_mixins.hh"
#include "BLI_vector.hh"

#include "BKE_ccg.hh"

struct Mesh;
namespace blender::bke::subdiv {
struct Subdiv;
}

/* --------------------------------------------------------------------
 * Masks.
 */

/* Functor which evaluates mask value at a given (u, v) of given ptex face. */
struct SubdivCCGMaskEvaluator {
  float (*eval_mask)(SubdivCCGMaskEvaluator *mask_evaluator,
                     int ptex_face_index,
                     float u,
                     float v);

  /* Free the data, not the evaluator itself. */
  void (*free)(SubdivCCGMaskEvaluator *mask_evaluator);

  void *user_data;
};

/* Return true if mesh has mask and evaluator can be used. */
bool BKE_subdiv_ccg_mask_init_from_paint(SubdivCCGMaskEvaluator *mask_evaluator, const Mesh *mesh);

/* --------------------------------------------------------------------
 * SubdivCCG.
 */

struct SubdivToCCGSettings {
  /* Resolution at which regular ptex (created for quad face) are being
   * evaluated. This defines how many vertices final mesh will have: every
   * regular ptex has resolution^2 vertices. Special (irregular, or ptex
   * created for a corner of non-quad face) will have resolution of
   * `resolution - 1`. */
  int resolution;
  /* Denotes which extra layers to be added to CCG elements. */
  bool need_normal;
  bool need_mask;
};

struct SubdivCCGCoord {
  /* Index of the grid within SubdivCCG::grids array. */
  int grid_index;

  /* Coordinate within the grid. */
  short x, y;

  /* Returns the coordinate for the index in an array sized to contain all grid vertices (including
   * duplicates). */
  inline static SubdivCCGCoord from_index(const CCGKey &key, int index)
  {
    const int grid_index = index / key.grid_area;
    const int index_in_grid = index - grid_index * key.grid_area;

    SubdivCCGCoord coord{};
    coord.grid_index = grid_index;
    coord.x = index_in_grid % key.grid_size;
    coord.y = index_in_grid / key.grid_size;

    return coord;
  }

  /* Returns the index for the coordinate in an array sized to contain all grid vertices (including
   * duplicates). */
  int to_index(const CCGKey &key) const
  {
    return key.grid_area * this->grid_index +
           CCG_grid_xy_to_index(key.grid_size, this->x, this->y);
  }
};

/* Definition of an edge which is adjacent to at least one of the faces. */
struct SubdivCCGAdjacentEdge {
  int num_adjacent_faces;
  /* Indexed by adjacent face index, then by point index on the edge.
   * points to a coordinate into the grids. */
  SubdivCCGCoord **boundary_coords;
};

/* Definition of a vertex which is adjacent to at least one of the faces. */
struct SubdivCCGAdjacentVertex {
  int num_adjacent_faces;
  /* Indexed by adjacent face index, points to a coordinate in the grids. */
  SubdivCCGCoord *corner_coords;
};

/* Representation of subdivision surface which uses CCG grids. */
struct SubdivCCG : blender::NonCopyable {
  /* This is a subdivision surface this CCG was created for.
   *
   * TODO(sergey): Make sure the whole descriptor is valid, including all the
   * displacement attached to the surface. */
  blender::bke::subdiv::Subdiv *subdiv = nullptr;
  /* A level at which geometry was subdivided. This is what defines grid
   * resolution. It is NOT the topology refinement level. */
  int level = -1;
  /* Resolution of grid. All grids have matching resolution, and resolution
   * is same as ptex created for non-quad faces. */
  int grid_size = -1;
  /** The number of vertices in each grid (grid_size ^2). */
  int grid_area = -1;
  /** The number of grids (face corners) in the geometry (#faces.total_size()). */
  int grids_num = -1;
  /**
   * Positions represent limit surface, with displacement applied. The vertices in each grid are
   * stored in contiguous chunks of size #grid_area in the same order.
   */
  blender::Array<blender::float3> positions;
  /** Vertex normals with the same indexing as #positions. */
  blender::Array<blender::float3> normals;
  /** Optional mask values with the same indexing as #positions. */
  blender::Array<float> masks;

  /* Faces from which grids are emitted. Owned by base mesh. */
  blender::OffsetIndices<int> faces;
  /* The face in #faces for each grid. Owned by base mesh (See #Mesh::corner_to_face_map()). */
  blender::Span<int> grid_to_face_map;

  /* Edges which are adjacent to faces.
   * Used for faster grid stitching, at the cost of extra memory.
   */
  blender::Array<SubdivCCGAdjacentEdge> adjacent_edges;

  /* Vertices which are adjacent to faces
   * Used for faster grid stitching, at the cost of extra memory.
   */
  blender::Array<SubdivCCGAdjacentVertex> adjacent_verts;

  /** Store the visibility of the items in each grid. If empty, everything is visible. */
  blender::BitGroupVector<> grid_hidden;

  /* TODO(sergey): Consider adding some accessors to a "decoded" geometry,
   * to make integration with draw manager and such easy.
   */

  /* TODO(sergey): Consider adding CD layers here, so we can draw final mesh
   * from grids, and have UVs and such work.
   */

  /* Integration with sculpting. */
  /* TODO(sergey): Is this really best way to go? Kind of annoying to have
   * such use-related flags in a more or less generic structure. */
  struct {
    /* Corresponds to MULTIRES_COORDS_MODIFIED. */
    bool coords = false;
    /* Corresponds to MULTIRES_HIDDEN_MODIFIED. */
    bool hidden = false;
  } dirty;

  /* Cached values, are not supposed to be accessed directly. */
  struct {
    /* Indexed by face, indicates index of the first grid which corresponds to the face. */
    blender::Array<int> start_face_grid_index;
  } cache_;

  ~SubdivCCG();
};

/* Create CCG representation of subdivision surface.
 *
 * NOTE: CCG stores dense vertices in a grid-like storage. There is no edges or
 * faces information's for the high-poly surface.
 *
 * NOTE: Subdiv is expected to be refined and ready for evaluation.
 * NOTE: CCG becomes an owner of subdiv.
 *
 * TODO(sergey): Allow some user-counter or more explicit control over who owns
 * the Subdiv. The goal should be to allow viewport GL Mesh and CCG to share
 * same Subsurf without conflicts. */
std::unique_ptr<SubdivCCG> BKE_subdiv_to_ccg(blender::bke::subdiv::Subdiv &subdiv,
                                             const SubdivToCCGSettings &settings,
                                             const Mesh &coarse_mesh,
                                             SubdivCCGMaskEvaluator *mask_evaluator);

/* Helper function, creates Mesh structure which is properly setup to use
 * grids.
 */
Mesh *BKE_subdiv_to_ccg_mesh(blender::bke::subdiv::Subdiv &subdiv,
                             const SubdivToCCGSettings &settings,
                             const Mesh &coarse_mesh);

/* Create a key for accessing grid elements at a given level. */
CCGKey BKE_subdiv_ccg_key(const SubdivCCG &subdiv_ccg, int level);
CCGKey BKE_subdiv_ccg_key_top_level(const SubdivCCG &subdiv_ccg);

/* Recalculate all normals based on grid element coordinates. */
void BKE_subdiv_ccg_recalc_normals(SubdivCCG &subdiv_ccg);

/* Update normals of affected faces. */
void BKE_subdiv_ccg_update_normals(SubdivCCG &subdiv_ccg, const blender::IndexMask &face_mask);

/* Average grid coordinates and normals along the grid boundaries. */
void BKE_subdiv_ccg_average_grids(SubdivCCG &subdiv_ccg);

/* Similar to above, but only updates given faces. */
void BKE_subdiv_ccg_average_stitch_faces(SubdivCCG &subdiv_ccg,
                                         const blender::IndexMask &face_mask);

/* Get geometry counters at the current subdivision level. */
void BKE_subdiv_ccg_topology_counters(const SubdivCCG &subdiv_ccg,
                                      int &r_num_vertices,
                                      int &r_num_edges,
                                      int &r_num_faces,
                                      int &r_num_loops);

struct SubdivCCGNeighbors {
  blender::Vector<SubdivCCGCoord, 256> coords;
  int num_duplicates;

  blender::Span<SubdivCCGCoord> unique() const
  {
    return this->coords.as_span().drop_back(num_duplicates);
  }

  blender::Span<SubdivCCGCoord> duplicates() const
  {
    return this->coords.as_span().take_back(num_duplicates);
  }
};

void BKE_subdiv_ccg_print_coord(const char *message, const SubdivCCGCoord &coord);
bool BKE_subdiv_ccg_check_coord_valid(const SubdivCCG &subdiv_ccg, const SubdivCCGCoord &coord);

/* CCG element neighbors.
 *
 * Neighbors are considered:
 *
 * - For an inner elements of a grid other elements which are sharing same row or column (4
 *   neighbor elements in total).
 *
 * - For the corner element a single neighboring element on every adjacent edge, single from
 *   every grid.
 *
 * - For the boundary element two neighbor elements on the boundary (from same grid) and one
 *   element inside of every neighboring grid. */

/* Get actual neighbors of the given coordinate.
 *
 * If include_duplicates is true, vertices in other grids that match
 * the current vertex are added at the end of the coords array. */
void BKE_subdiv_ccg_neighbor_coords_get(const SubdivCCG &subdiv_ccg,
                                        const SubdivCCGCoord &coord,
                                        bool include_duplicates,
                                        SubdivCCGNeighbors &r_neighbors);

inline int BKE_subdiv_ccg_grid_to_face_index(const SubdivCCG &subdiv_ccg, const int grid_index)
{
  return subdiv_ccg.grid_to_face_map[grid_index];
}

void BKE_subdiv_ccg_eval_limit_point(const SubdivCCG &subdiv_ccg,
                                     const SubdivCCGCoord &coord,
                                     float r_point[3]);
void BKE_subdiv_ccg_eval_limit_positions(const SubdivCCG &subdiv_ccg,
                                         const CCGKey &key,
                                         int grid_index,
                                         blender::MutableSpan<blender::float3> r_limit_positions);

enum SubdivCCGAdjacencyType {
  SUBDIV_CCG_ADJACENT_NONE,
  SUBDIV_CCG_ADJACENT_VERTEX,
  SUBDIV_CCG_ADJACENT_EDGE,
};

/* Returns if a grid coordinates is adjacent to a coarse mesh edge, vertex or nothing. If it is
 * adjacent to an edge, r_v1 and r_v2 will be set to the two vertices of that edge. If it is
 * adjacent to a vertex, r_v1 and r_v2 will be the index of that vertex. */
SubdivCCGAdjacencyType BKE_subdiv_ccg_coarse_mesh_adjacency_info_get(
    const SubdivCCG &subdiv_ccg,
    const SubdivCCGCoord &coord,
    blender::Span<int> corner_verts,
    blender::OffsetIndices<int> faces,
    int &r_v1,
    int &r_v2);

/* Determines if a given grid coordinate is on a coarse mesh boundary. */
bool BKE_subdiv_ccg_coord_is_mesh_boundary(blender::OffsetIndices<int> faces,
                                           blender::Span<int> corner_verts,
                                           blender::BitSpan boundary_verts,
                                           const SubdivCCG &subdiv_ccg,
                                           SubdivCCGCoord coord);

/* Get array which is indexed by face index and contains index of a first grid of the face.
 *
 * The "ensure" version allocates the mapping if it's not known yet and stores it in the subdiv_ccg
 * descriptor. This function is NOT safe for threading.
 *
 * The "get" version simply returns cached array. */
const int *BKE_subdiv_ccg_start_face_grid_index_ensure(SubdivCCG &subdiv_ccg);
const int *BKE_subdiv_ccg_start_face_grid_index_get(const SubdivCCG &subdiv_ccg);

blender::BitGroupVector<> &BKE_subdiv_ccg_grid_hidden_ensure(SubdivCCG &subdiv_ccg);
void BKE_subdiv_ccg_grid_hidden_free(SubdivCCG &subdiv_ccg);

template<typename Fn>
inline void BKE_subdiv_ccg_foreach_visible_grid_vert(const CCGKey &key,
                                                     const blender::BitGroupVector<> &grid_hidden,
                                                     const int grid,
                                                     const Fn &fn)
{
  if (grid_hidden.is_empty()) {
    for (const int i : blender::IndexRange(key.grid_area)) {
      fn(i);
    }
  }
  else {
    blender::bits::foreach_0_index(grid_hidden[grid], fn);
  }
}

namespace blender::bke::ccg {

/** Find the range of vertices in the entire geometry that are part of a single grid. */
inline IndexRange grid_range(const int grid_area, const int grid)
{
  return IndexRange(grid * grid_area, grid_area);
}
inline IndexRange grid_range(const CCGKey &key, const int grid)
{
  return grid_range(key.grid_area, grid);
}

/** Find the range of vertices in the entire geometry that are part of a single face. */
inline IndexRange face_range(const OffsetIndices<int> faces, const int grid_area, const int face)
{
  const IndexRange corners = faces[face];
  return IndexRange(corners.start() * grid_area, corners.size() * grid_area);
}
inline IndexRange face_range(const OffsetIndices<int> faces, const CCGKey &key, const int face)
{
  return face_range(faces, key.grid_area, face);
}

/** Find the vertex index in the entire geometry at a specific coordinate in a specific grid. */
inline int grid_xy_to_vert(const CCGKey &key, const int grid, const int x, const int y)
{
  return key.grid_area * grid + CCG_grid_xy_to_index(key.grid_size, x, y);
}

}  // namespace blender::bke::ccg
