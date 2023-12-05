/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 */

#include "MEM_guardedalloc.h"

#include <climits>

#include "BLI_array_utils.hh"
#include "BLI_bit_span_ops.hh"
#include "BLI_bitmap.h"
#include "BLI_bounds.hh"
#include "BLI_math_geom.h"
#include "BLI_math_matrix.h"
#include "BLI_math_vector.h"
#include "BLI_math_vector.hh"
#include "BLI_rand.h"
#include "BLI_task.h"
#include "BLI_task.hh"
#include "BLI_timeit.hh"
#include "BLI_utildefines.h"
#include "BLI_vector.hh"
#include "BLI_vector_set.hh"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"

#include "BKE_attribute.hh"
#include "BKE_ccg.h"
#include "BKE_mesh.hh"
#include "BKE_mesh_mapping.hh"
#include "BKE_paint.hh"
#include "BKE_pbvh_api.hh"
#include "BKE_subdiv_ccg.hh"

#include "DRW_pbvh.hh"

#include "PIL_time.h"

#include "bmesh.h"

#include "atomic_ops.h"

#include "pbvh_intern.hh"

using blender::BitGroupVector;
using blender::Bounds;
using blender::float3;
using blender::MutableSpan;
using blender::Span;
using blender::Vector;

#define LEAF_LIMIT 10000

/* Uncomment to test if triangles of the same face are
 * properly clustered into single nodes.
 */
//#define TEST_PBVH_FACE_SPLIT

/* Uncomment to test that faces are only assigned to one PBVHNode */
//#define VALIDATE_UNIQUE_NODE_FACES

//#define PERFCNTRS
#define STACK_FIXED_DEPTH 100

struct PBVHStack {
  PBVHNode *node;
  bool revisiting;
};

struct PBVHIter {
  PBVH *pbvh;
  blender::FunctionRef<bool(PBVHNode &)> scb;

  PBVHStack *stack;
  int stacksize;

  PBVHStack stackfixed[STACK_FIXED_DEPTH];
  int stackspace;
};

/** Create invalid bounds for use with #math::min_max. */
static Bounds<float3> negative_bounds()
{
  return {float3(std::numeric_limits<float>::max()), float3(std::numeric_limits<float>::lowest())};
}

namespace blender::bke::pbvh {

void update_node_bounds_mesh(const Span<float3> positions, PBVHNode &node)
{
  Bounds<float3> bounds = negative_bounds();
  for (const int vert : node.vert_indices) {
    math::min_max(positions[vert], bounds.min, bounds.max);
  }
  node.vb = bounds;
}

void update_node_bounds_grids(const CCGKey &key, const Span<CCGElem *> grids, PBVHNode &node)
{
  Bounds<float3> bounds = negative_bounds();
  for (const int grid : node.prim_indices) {
    for (const int i : IndexRange(key.grid_area)) {
      math::min_max(float3(CCG_elem_offset_co(&key, grids[grid], i)), bounds.min, bounds.max);
    }
  }
  node.vb = bounds;
}

void update_node_bounds_bmesh(PBVHNode &node)
{
  Bounds<float3> bounds = negative_bounds();
  for (const BMVert *vert : node.bm_unique_verts) {
    math::min_max(float3(vert->co), bounds.min, bounds.max);
  }
  for (const BMVert *vert : node.bm_other_verts) {
    math::min_max(float3(vert->co), bounds.min, bounds.max);
  }
  node.vb = bounds;
}

}  // namespace blender::bke::pbvh

/* Not recursive */
static void update_node_vb(PBVH *pbvh, PBVHNode *node)
{
  using namespace blender;
  using namespace blender::bke::pbvh;
  if (node->flag & PBVH_Leaf) {
    switch (pbvh->header.type) {
      case PBVH_FACES:
        update_node_bounds_mesh(pbvh->vert_positions, *node);
        break;
      case PBVH_GRIDS:
        update_node_bounds_grids(pbvh->gridkey, pbvh->subdiv_ccg->grids, *node);
        break;
      case PBVH_BMESH:
        update_node_bounds_bmesh(*node);
        break;
    }
  }
  else {
    node->vb = bounds::merge(pbvh->nodes[node->children_offset].vb,
                             pbvh->nodes[node->children_offset + 1].vb);
  }
}

static bool face_materials_match(const int *material_indices,
                                 const bool *sharp_faces,
                                 const int a,
                                 const int b)
{
  if (material_indices) {
    if (material_indices[a] != material_indices[b]) {
      return false;
    }
  }
  if (sharp_faces) {
    if (sharp_faces[a] != sharp_faces[b]) {
      return false;
    }
  }
  return true;
}

/* Adapted from BLI_kdopbvh.c */
/* Returns the index of the first element on the right of the partition */
static int partition_prim_indices(blender::MutableSpan<int> prim_indices,
                                  int *prim_scratch,
                                  int lo,
                                  int hi,
                                  int axis,
                                  float mid,
                                  const Span<Bounds<float3>> prim_bounds,
                                  const Span<int> prim_to_face_map)
{
  using namespace blender;
  for (int i = lo; i < hi; i++) {
    prim_scratch[i - lo] = prim_indices[i];
  }

  int lo2 = lo, hi2 = hi - 1;
  int i1 = lo, i2 = 0;

  while (i1 < hi) {
    const int face_i = prim_to_face_map[prim_scratch[i2]];
    const Bounds<float3> &bounds = prim_bounds[prim_scratch[i2]];
    const bool side = math::midpoint(bounds.min[axis], bounds.max[axis]) >= mid;

    while (i1 < hi && prim_to_face_map[prim_scratch[i2]] == face_i) {
      prim_indices[side ? hi2-- : lo2++] = prim_scratch[i2];
      i1++;
      i2++;
    }
  }

  return lo2;
}

/* Returns the index of the first element on the right of the partition */
static int partition_indices_material_faces(MutableSpan<int> indices,
                                            const Span<int> prim_to_face_map,
                                            const int *material_indices,
                                            const bool *sharp_faces,
                                            const int lo,
                                            const int hi)
{
  int i = lo, j = hi;
  for (;;) {
    const int first = prim_to_face_map[indices[lo]];
    for (;
         face_materials_match(material_indices, sharp_faces, first, prim_to_face_map[indices[i]]);
         i++)
    {
      /* pass */
    }
    for (;
         !face_materials_match(material_indices, sharp_faces, first, prim_to_face_map[indices[j]]);
         j--)
    {
      /* pass */
    }
    if (!(i < j)) {
      return i;
    }
    std::swap(indices[i], indices[j]);
    i++;
  }
}

void pbvh_grow_nodes(PBVH *pbvh, int totnode)
{
  pbvh->nodes.resize(totnode);
}

/* Add a vertex to the map, with a positive value for unique vertices and
 * a negative value for additional vertices */
static int map_insert_vert(blender::Map<int, int> &map,
                           MutableSpan<bool> vert_bitmap,
                           int *face_verts,
                           int *uniq_verts,
                           int vertex)
{
  return map.lookup_or_add_cb(vertex, [&]() {
    int value;
    if (!vert_bitmap[vertex]) {
      vert_bitmap[vertex] = true;
      value = *uniq_verts;
      (*uniq_verts)++;
    }
    else {
      value = ~(*face_verts);
      (*face_verts)++;
    }
    return value;
  });
}

/* Find vertices used by the faces in this node and update the draw buffers */
static void build_mesh_leaf_node(const Span<int> corner_verts,
                                 const Span<MLoopTri> looptris,
                                 const Span<int> looptri_faces,
                                 const bool *hide_poly,
                                 MutableSpan<bool> vert_bitmap,
                                 PBVHNode *node)
{
  node->uniq_verts = node->face_verts = 0;
  const Span<int> prim_indices = node->prim_indices;

  /* reserve size is rough guess */
  blender::Map<int, int> map;
  map.reserve(prim_indices.size());

  node->face_vert_indices.reinitialize(prim_indices.size());

  for (const int i : prim_indices.index_range()) {
    const MLoopTri &tri = looptris[prim_indices[i]];
    for (int j = 0; j < 3; j++) {
      node->face_vert_indices[i][j] = map_insert_vert(
          map, vert_bitmap, &node->face_verts, &node->uniq_verts, corner_verts[tri.tri[j]]);
    }
  }

  node->vert_indices.reinitialize(node->uniq_verts + node->face_verts);

  /* Build the vertex list, unique verts first */
  for (const blender::MapItem<int, int> item : map.items()) {
    int value = item.value;
    if (value < 0) {
      value = -value + node->uniq_verts - 1;
    }

    node->vert_indices[value] = item.key;
  }

  for (const int i : prim_indices.index_range()) {
    for (int j = 0; j < 3; j++) {
      if (node->face_vert_indices[i][j] < 0) {
        node->face_vert_indices[i][j] = -node->face_vert_indices[i][j] + node->uniq_verts - 1;
      }
    }
  }

  const bool fully_hidden = hide_poly && std::all_of(prim_indices.begin(),
                                                     prim_indices.end(),
                                                     [&](const int tri) {
                                                       return hide_poly[looptri_faces[tri]];
                                                     });
  BKE_pbvh_node_fully_hidden_set(node, fully_hidden);
  BKE_pbvh_node_mark_rebuild_draw(node);
}

static void update_vb(const Span<int> prim_indices,
                      PBVHNode *node,
                      const Span<Bounds<float3>> prim_bounds,
                      int offset,
                      int count)
{
  using namespace blender;
  node->vb = prim_bounds[prim_indices[offset]];
  for (const int i : IndexRange(offset, count).drop_front(1)) {
    node->vb = bounds::merge(node->vb, prim_bounds[prim_indices[i]]);
  }
  node->orig_vb = node->vb;
}

int BKE_pbvh_count_grid_quads(const BitGroupVector<> &grid_hidden,
                              const int *grid_indices,
                              int totgrid,
                              int gridsize,
                              int display_gridsize)
{
  const int gridarea = (gridsize - 1) * (gridsize - 1);
  if (grid_hidden.is_empty()) {
    return gridarea * totgrid;
  }

  /* grid hidden layer is present, so have to check each grid for
   * visibility */

  int depth1 = int(log2(double(gridsize) - 1.0) + DBL_EPSILON);
  int depth2 = int(log2(double(display_gridsize) - 1.0) + DBL_EPSILON);

  int skip = depth2 < depth1 ? 1 << (depth1 - depth2 - 1) : 1;

  int totquad = 0;
  for (int i = 0; i < totgrid; i++) {
    const blender::BoundedBitSpan gh = grid_hidden[grid_indices[i]];
    /* grid hidden are present, have to check each element */
    for (int y = 0; y < gridsize - skip; y += skip) {
      for (int x = 0; x < gridsize - skip; x += skip) {
        if (!paint_is_grid_face_hidden(gh, gridsize, x, y)) {
          totquad++;
        }
      }
    }
  }

  return totquad;
}

static void build_grid_leaf_node(PBVH *pbvh, PBVHNode *node)
{
  int totquads = BKE_pbvh_count_grid_quads(pbvh->subdiv_ccg->grid_hidden,
                                           node->prim_indices.data(),
                                           node->prim_indices.size(),
                                           pbvh->gridkey.grid_size,
                                           pbvh->gridkey.grid_size);
  BKE_pbvh_node_fully_hidden_set(node, (totquads == 0));
  BKE_pbvh_node_mark_rebuild_draw(node);
}

static void build_leaf(PBVH *pbvh,
                       const Span<int> corner_verts,
                       const Span<MLoopTri> looptris,
                       const Span<int> looptri_faces,
                       const bool *hide_poly,
                       int node_index,
                       const Span<Bounds<float3>> prim_bounds,
                       int offset,
                       int count)
{
  PBVHNode &node = pbvh->nodes[node_index];
  node.flag |= PBVH_Leaf;

  node.prim_indices = pbvh->prim_indices.as_span().slice(offset, count);

  /* Still need vb for searches */
  update_vb(pbvh->prim_indices, &node, prim_bounds, offset, count);

  if (!pbvh->looptri.is_empty()) {
    build_mesh_leaf_node(
        corner_verts, looptris, looptri_faces, hide_poly, pbvh->vert_bitmap, &node);
  }
  else {
    build_grid_leaf_node(pbvh, &node);
  }
}

/* Return zero if all primitives in the node can be drawn with the
 * same material (including flat/smooth shading), non-zero otherwise */
static bool leaf_needs_material_split(PBVH *pbvh,
                                      const Span<int> prim_to_face_map,
                                      const int *material_indices,
                                      const bool *sharp_faces,
                                      int offset,
                                      int count)
{
  if (count <= 1) {
    return false;
  }

  const int first = prim_to_face_map[pbvh->prim_indices[offset]];
  for (int i = offset + count - 1; i > offset; i--) {
    int prim = pbvh->prim_indices[i];
    if (!face_materials_match(material_indices, sharp_faces, first, prim_to_face_map[prim])) {
      return true;
    }
  }

  return false;
}

#ifdef TEST_PBVH_FACE_SPLIT
static void test_face_boundaries(PBVH *pbvh)
{
  int faces_num = BKE_pbvh_num_faces(pbvh);
  int *node_map = MEM_calloc_arrayN(faces_num, sizeof(int), __func__);
  for (int i = 0; i < faces_num; i++) {
    node_map[i] = -1;
  }

  for (int i = 0; i < pbvh->totnode; i++) {
    PBVHNode *node = pbvh->nodes + i;

    if (!(node->flag & PBVH_Leaf)) {
      continue;
    }

    switch (BKE_pbvh_type(pbvh)) {
      case PBVH_FACES: {
        for (int j = 0; j < node->totprim; j++) {
          int face_i = looptri_faces[node->prim_indices[j]];

          if (node_map[face_i] >= 0 && node_map[face_i] != i) {
            int old_i = node_map[face_i];
            int prim_i = node->prim_indices - pbvh->prim_indices + j;

            printf("PBVH split error; face: %d, prim_i: %d, node1: %d, node2: %d, totprim: %d\n",
                   face_i,
                   prim_i,
                   old_i,
                   i,
                   node->totprim);
          }

          node_map[face_i] = i;
        }
        break;
      }
      case PBVH_GRIDS:
        break;
      case PBVH_BMESH:
        break;
    }
  }

  MEM_SAFE_FREE(node_map);
}
#endif

/* Recursively build a node in the tree
 *
 * vb is the voxel box around all of the primitives contained in
 * this node.
 *
 * cb is the bounding box around all the centroids of the primitives
 * contained in this node
 *
 * offset and start indicate a range in the array of primitive indices
 */

static void build_sub(PBVH *pbvh,
                      const Span<int> corner_verts,
                      const Span<MLoopTri> looptris,
                      const Span<int> looptri_faces,
                      const bool *hide_poly,
                      const int *material_indices,
                      const bool *sharp_faces,
                      int node_index,
                      const Bounds<float3> *cb,
                      const Span<Bounds<float3>> prim_bounds,
                      int offset,
                      int count,
                      int *prim_scratch,
                      int depth)
{
  using namespace blender;
  const Span<int> prim_to_face_map = pbvh->header.type == PBVH_FACES ?
                                         looptri_faces :
                                         pbvh->subdiv_ccg->grid_to_face_map;
  int end;

  if (!prim_scratch) {
    prim_scratch = static_cast<int *>(MEM_malloc_arrayN(pbvh->totprim, sizeof(int), __func__));
  }

  /* Decide whether this is a leaf or not */
  const bool below_leaf_limit = count <= pbvh->leaf_limit || depth >= STACK_FIXED_DEPTH - 1;
  if (below_leaf_limit) {
    if (!leaf_needs_material_split(
            pbvh, prim_to_face_map, material_indices, sharp_faces, offset, count))
    {
      build_leaf(pbvh,
                 corner_verts,
                 looptris,
                 looptri_faces,
                 hide_poly,
                 node_index,
                 prim_bounds,
                 offset,
                 count);

      if (node_index == 0) {
        MEM_SAFE_FREE(prim_scratch);
      }

      return;
    }
  }

  /* Add two child nodes */
  pbvh->nodes[node_index].children_offset = pbvh->nodes.size();
  pbvh_grow_nodes(pbvh, pbvh->nodes.size() + 2);

  /* Update parent node bounding box */
  update_vb(pbvh->prim_indices, &pbvh->nodes[node_index], prim_bounds, offset, count);

  Bounds<float3> cb_backing;
  if (!below_leaf_limit) {
    /* Find axis with widest range of primitive centroids */
    if (!cb) {
      cb_backing = negative_bounds();
      for (int i = offset + count - 1; i >= offset; i--) {
        const int prim = pbvh->prim_indices[i];
        const float3 center = math::midpoint(prim_bounds[prim].min, prim_bounds[prim].max);
        math::min_max(center, cb_backing.min, cb_backing.max);
      }
      cb = &cb_backing;
    }
    const int axis = math::dominant_axis(cb->max - cb->min);

    /* Partition primitives along that axis */
    end = partition_prim_indices(pbvh->prim_indices,
                                 prim_scratch,
                                 offset,
                                 offset + count,
                                 axis,
                                 math::midpoint(cb->min[axis], cb->max[axis]),
                                 prim_bounds,
                                 prim_to_face_map);
  }
  else {
    /* Partition primitives by material */
    end = partition_indices_material_faces(pbvh->prim_indices,
                                           prim_to_face_map,
                                           material_indices,
                                           sharp_faces,
                                           offset,
                                           offset + count - 1);
  }

  /* Build children */
  build_sub(pbvh,
            corner_verts,
            looptris,
            looptri_faces,
            hide_poly,
            material_indices,
            sharp_faces,
            pbvh->nodes[node_index].children_offset,
            nullptr,
            prim_bounds,
            offset,
            end - offset,
            prim_scratch,
            depth + 1);
  build_sub(pbvh,
            corner_verts,
            looptris,
            looptri_faces,
            hide_poly,
            material_indices,
            sharp_faces,
            pbvh->nodes[node_index].children_offset + 1,
            nullptr,
            prim_bounds,
            end,
            offset + count - end,
            prim_scratch,
            depth + 1);

  if (node_index == 0) {
    MEM_SAFE_FREE(prim_scratch);
  }
}

static void pbvh_build(PBVH *pbvh,
                       const Span<int> corner_verts,
                       const Span<MLoopTri> looptris,
                       const Span<int> looptri_faces,
                       const bool *hide_poly,
                       const int *material_indices,
                       const bool *sharp_faces,
                       const Bounds<float3> *cb,
                       const Span<Bounds<float3>> prim_bounds,
                       int totprim)
{
  if (totprim != pbvh->totprim) {
    pbvh->totprim = totprim;
    pbvh->nodes.clear_and_shrink();

    pbvh->prim_indices.reinitialize(totprim);
    blender::array_utils::fill_index_range<int>(pbvh->prim_indices);
  }

  pbvh->nodes.resize(1);

  build_sub(pbvh,
            corner_verts,
            looptris,
            looptri_faces,
            hide_poly,
            material_indices,
            sharp_faces,
            0,
            cb,
            prim_bounds,
            0,
            totprim,
            nullptr,
            0);
}

#ifdef VALIDATE_UNIQUE_NODE_FACES
static void pbvh_validate_node_prims(PBVH *pbvh, const Span<int> looptri_faces)
{
  int totface = 0;

  if (pbvh->header.type == PBVH_BMESH) {
    return;
  }

  for (int i = 0; i < pbvh->totnode; i++) {
    PBVHNode *node = pbvh->nodes + i;

    if (!(node->flag & PBVH_Leaf)) {
      continue;
    }

    for (int j = 0; j < node->totprim; j++) {
      int face_i;

      if (pbvh->header.type == PBVH_FACES) {
        face_i = looptri_faces[node->prim_indices[j]];
      }
      else {
        face_i = BKE_subdiv_ccg_grid_to_face_index(pbvh->subdiv_ccg, node->prim_indices[j]);
      }

      totface = max_ii(totface, face_i + 1);
    }
  }

  int *facemap = (int *)MEM_malloc_arrayN(totface, sizeof(*facemap), __func__);

  for (int i = 0; i < totface; i++) {
    facemap[i] = -1;
  }

  for (int i = 0; i < pbvh->totnode; i++) {
    PBVHNode *node = pbvh->nodes + i;

    if (!(node->flag & PBVH_Leaf)) {
      continue;
    }

    for (int j = 0; j < node->totprim; j++) {
      int face_i;

      if (pbvh->header.type == PBVH_FACES) {
        face_i = looptri_faces[node->prim_indices[j]];
      }
      else {
        face_i = BKE_subdiv_ccg_grid_to_face_index(pbvh->subdiv_ccg, node->prim_indices[j]);
      }

      if (facemap[face_i] != -1 && facemap[face_i] != i) {
        printf("%s: error: face spanned multiple nodes (old: %d new: %d)\n",
               __func__,
               facemap[face_i],
               i);
      }

      facemap[face_i] = i;
    }
  }
  MEM_SAFE_FREE(facemap);
}
#endif

void BKE_pbvh_update_mesh_pointers(PBVH *pbvh, Mesh *mesh)
{
  BLI_assert(pbvh->header.type == PBVH_FACES);
  pbvh->faces = mesh->faces();
  pbvh->corner_verts = mesh->corner_verts();
  pbvh->looptri_faces = mesh->looptri_faces();
  if (!pbvh->deformed) {
    /* Deformed data not matching the original mesh are owned directly by the PBVH, and are
     * set separately by #BKE_pbvh_vert_coords_apply. */
    pbvh->vert_positions = mesh->vert_positions_for_write();
    pbvh->vert_normals = mesh->vert_normals();
    pbvh->face_normals = mesh->face_normals();
  }
}

void BKE_pbvh_build_mesh(PBVH *pbvh, Mesh *mesh)
{
  using namespace blender;
  const int totvert = mesh->totvert;
  const int looptri_num = poly_to_tri_count(mesh->faces_num, mesh->totloop);
  MutableSpan<float3> vert_positions = mesh->vert_positions_for_write();
  const blender::OffsetIndices<int> faces = mesh->faces();
  const Span<int> corner_verts = mesh->corner_verts();

  pbvh->looptri.reinitialize(looptri_num);
  blender::bke::mesh::looptris_calc(vert_positions, faces, corner_verts, pbvh->looptri);
  const Span<MLoopTri> looptris = pbvh->looptri;

  pbvh->mesh = mesh;
  pbvh->header.type = PBVH_FACES;

  BKE_pbvh_update_mesh_pointers(pbvh, mesh);
  const Span<int> looptri_faces = pbvh->looptri_faces;

  /* Those are not set in #BKE_pbvh_update_mesh_pointers because they are owned by the #PBVH. */
  pbvh->vert_bitmap = blender::Array<bool>(totvert, false);
  pbvh->totvert = totvert;

#ifdef TEST_PBVH_FACE_SPLIT
  /* Use lower limit to increase probability of
   * edge cases.
   */
  pbvh->leaf_limit = 100;
#else
  pbvh->leaf_limit = LEAF_LIMIT;
#endif

  pbvh->faces_num = mesh->faces_num;

  /* For each face, store the AABB and the AABB centroid */
  Array<Bounds<float3>> prim_bounds(looptri_num);
  const Bounds<float3> cb = threading::parallel_reduce(
      looptris.index_range(),
      1024,
      negative_bounds(),
      [&](const IndexRange range, const Bounds<float3> &init) {
        Bounds<float3> current = init;
        for (const int i : range) {
          const MLoopTri &lt = looptris[i];
          Bounds<float3> &bounds = prim_bounds[i];
          bounds = {vert_positions[corner_verts[lt.tri[0]]]};
          math::min_max(vert_positions[corner_verts[lt.tri[1]]], bounds.min, bounds.max);
          math::min_max(vert_positions[corner_verts[lt.tri[2]]], bounds.min, bounds.max);
          const float3 center = math::midpoint(prim_bounds[i].min, prim_bounds[i].max);
          math::min_max(center, current.min, current.max);
        }
        return current;
      },
      [](const Bounds<float3> &a, const Bounds<float3> &b) { return bounds::merge(a, b); });

  if (looptri_num) {
    const bool *hide_poly = static_cast<const bool *>(
        CustomData_get_layer_named(&mesh->face_data, CD_PROP_BOOL, ".hide_poly"));
    const int *material_indices = static_cast<const int *>(
        CustomData_get_layer_named(&mesh->face_data, CD_PROP_INT32, "material_index"));
    const bool *sharp_faces = (const bool *)CustomData_get_layer_named(
        &mesh->face_data, CD_PROP_BOOL, "sharp_face");
    pbvh_build(pbvh,
               corner_verts,
               looptris,
               looptri_faces,
               hide_poly,
               material_indices,
               sharp_faces,
               &cb,
               prim_bounds,
               looptri_num);

#ifdef TEST_PBVH_FACE_SPLIT
    test_face_boundaries(pbvh, looptri_faces);
#endif
  }

  /* Clear the bitmap so it can be used as an update tag later on. */
  pbvh->vert_bitmap.fill(false);

  BKE_pbvh_update_active_vcol(pbvh, mesh);

#ifdef VALIDATE_UNIQUE_NODE_FACES
  pbvh_validate_node_prims(pbvh);
#endif
}

void BKE_pbvh_build_grids(PBVH *pbvh, const CCGKey *key, Mesh *me, SubdivCCG *subdiv_ccg)
{
  using namespace blender;
  const int gridsize = key->grid_size;
  const Span<CCGElem *> grids = subdiv_ccg->grids;

  pbvh->header.type = PBVH_GRIDS;
  pbvh->gridkey = *key;
  pbvh->subdiv_ccg = subdiv_ccg;
  pbvh->faces_num = me->faces_num;

  /* Find maximum number of grids per face. */
  int max_grids = 1;
  const blender::OffsetIndices faces = me->faces();
  for (const int i : faces.index_range()) {
    max_grids = max_ii(max_grids, faces[i].size());
  }

  /* Ensure leaf limit is at least 4 so there's room
   * to split at original face boundaries.
   * Fixes #102209.
   */
  pbvh->leaf_limit = max_ii(LEAF_LIMIT / (gridsize * gridsize), max_grids);

  /* We also need the base mesh for PBVH draw. */
  pbvh->mesh = me;

  /* For each grid, store the AABB and the AABB centroid */
  Array<Bounds<float3>> prim_bounds(grids.size());
  const Bounds<float3> cb = threading::parallel_reduce(
      grids.index_range(),
      1024,
      negative_bounds(),
      [&](const IndexRange range, const Bounds<float3> &init) {
        Bounds<float3> current = init;
        for (const int i : range) {
          CCGElem *grid = grids[i];
          prim_bounds[i] = negative_bounds();
          for (const int j : IndexRange(key->grid_area)) {
            const float3 position = float3(CCG_elem_offset_co(key, grid, j));
            math::min_max(position, prim_bounds[i].min, prim_bounds[i].max);
          }
          const float3 center = math::midpoint(prim_bounds[i].min, prim_bounds[i].max);
          math::min_max(center, current.min, current.max);
        }
        return current;
      },
      [](const Bounds<float3> &a, const Bounds<float3> &b) { return bounds::merge(a, b); });

  if (!grids.is_empty()) {
    const int *material_indices = static_cast<const int *>(
        CustomData_get_layer_named(&me->face_data, CD_PROP_INT32, "material_index"));
    const bool *sharp_faces = (const bool *)CustomData_get_layer_named(
        &me->face_data, CD_PROP_BOOL, "sharp_face");
    pbvh_build(
        pbvh, {}, {}, {}, nullptr, material_indices, sharp_faces, &cb, prim_bounds, grids.size());

#ifdef TEST_PBVH_FACE_SPLIT
    test_face_boundaries(pbvh);
#endif
  }

#ifdef VALIDATE_UNIQUE_NODE_FACES
  pbvh_validate_node_prims(pbvh);
#endif
}

PBVH *BKE_pbvh_new(PBVHType type)
{
  PBVH *pbvh = MEM_new<PBVH>(__func__);
  pbvh->draw_cache_invalid = true;
  pbvh->header.type = type;

  /* Initialize this to true, instead of waiting for a draw engine
   * to set it.  Prevents a crash in draw manager instancing code.
   */
  pbvh->is_drawing = true;
  return pbvh;
}

void BKE_pbvh_free(PBVH *pbvh)
{
  for (PBVHNode &node : pbvh->nodes) {
    if (node.flag & PBVH_Leaf) {
      if (node.draw_batches) {
        blender::draw::pbvh::node_free(node.draw_batches);
      }
    }

    if (node.flag & (PBVH_Leaf | PBVH_TexLeaf)) {
      pbvh_node_pixels_free(&node);
    }
  }

  pbvh_pixels_free(pbvh);

  MEM_delete(pbvh);
}

static void pbvh_iter_begin(PBVHIter *iter, PBVH *pbvh, blender::FunctionRef<bool(PBVHNode &)> scb)
{
  iter->pbvh = pbvh;
  iter->scb = scb;

  iter->stack = iter->stackfixed;
  iter->stackspace = STACK_FIXED_DEPTH;

  iter->stack[0].node = &pbvh->nodes.first();
  iter->stack[0].revisiting = false;
  iter->stacksize = 1;
}

static void pbvh_iter_end(PBVHIter *iter)
{
  if (iter->stackspace > STACK_FIXED_DEPTH) {
    MEM_freeN(iter->stack);
  }
}

static void pbvh_stack_push(PBVHIter *iter, PBVHNode *node, bool revisiting)
{
  if (UNLIKELY(iter->stacksize == iter->stackspace)) {
    iter->stackspace *= 2;
    if (iter->stackspace != (STACK_FIXED_DEPTH * 2)) {
      iter->stack = static_cast<PBVHStack *>(
          MEM_reallocN(iter->stack, sizeof(PBVHStack) * iter->stackspace));
    }
    else {
      iter->stack = static_cast<PBVHStack *>(
          MEM_mallocN(sizeof(PBVHStack) * iter->stackspace, "PBVHStack"));
      memcpy(iter->stack, iter->stackfixed, sizeof(PBVHStack) * iter->stacksize);
    }
  }

  iter->stack[iter->stacksize].node = node;
  iter->stack[iter->stacksize].revisiting = revisiting;
  iter->stacksize++;
}

static PBVHNode *pbvh_iter_next(PBVHIter *iter, PBVHNodeFlags leaf_flag)
{
  /* purpose here is to traverse tree, visiting child nodes before their
   * parents, this order is necessary for e.g. computing bounding boxes */

  while (iter->stacksize) {
    /* pop node */
    iter->stacksize--;
    PBVHNode *node = iter->stack[iter->stacksize].node;

    /* on a mesh with no faces this can happen
     * can remove this check if we know meshes have at least 1 face */
    if (node == nullptr) {
      return nullptr;
    }

    bool revisiting = iter->stack[iter->stacksize].revisiting;

    /* revisiting node already checked */
    if (revisiting) {
      return node;
    }

    if (iter->scb && !iter->scb(*node)) {
      continue; /* don't traverse, outside of search zone */
    }

    if (node->flag & leaf_flag) {
      /* immediately hit leaf node */
      return node;
    }

    /* come back later when children are done */
    pbvh_stack_push(iter, node, true);

    /* push two child nodes on the stack */
    pbvh_stack_push(iter, &iter->pbvh->nodes[node->children_offset + 1], false);
    pbvh_stack_push(iter, &iter->pbvh->nodes[node->children_offset], false);
  }

  return nullptr;
}

static PBVHNode *pbvh_iter_next_occluded(PBVHIter *iter)
{
  while (iter->stacksize) {
    /* pop node */
    iter->stacksize--;
    PBVHNode *node = iter->stack[iter->stacksize].node;

    /* on a mesh with no faces this can happen
     * can remove this check if we know meshes have at least 1 face */
    if (node == nullptr) {
      return nullptr;
    }

    if (iter->scb && !iter->scb(*node)) {
      continue; /* don't traverse, outside of search zone */
    }

    if (node->flag & PBVH_Leaf) {
      /* immediately hit leaf node */
      return node;
    }

    pbvh_stack_push(iter, &iter->pbvh->nodes[node->children_offset + 1], false);
    pbvh_stack_push(iter, &iter->pbvh->nodes[node->children_offset], false);
  }

  return nullptr;
}

struct node_tree {
  PBVHNode *data;

  node_tree *left;
  node_tree *right;
};

static void node_tree_insert(node_tree *tree, node_tree *new_node)
{
  if (new_node->data->tmin < tree->data->tmin) {
    if (tree->left) {
      node_tree_insert(tree->left, new_node);
    }
    else {
      tree->left = new_node;
    }
  }
  else {
    if (tree->right) {
      node_tree_insert(tree->right, new_node);
    }
    else {
      tree->right = new_node;
    }
  }
}

static void traverse_tree(node_tree *tree,
                          BKE_pbvh_HitOccludedCallback hcb,
                          void *hit_data,
                          float *tmin)
{
  if (tree->left) {
    traverse_tree(tree->left, hcb, hit_data, tmin);
  }

  hcb(tree->data, hit_data, tmin);

  if (tree->right) {
    traverse_tree(tree->right, hcb, hit_data, tmin);
  }
}

static void free_tree(node_tree *tree)
{
  if (tree->left) {
    free_tree(tree->left);
    tree->left = nullptr;
  }

  if (tree->right) {
    free_tree(tree->right);
    tree->right = nullptr;
  }

  free(tree);
}

float BKE_pbvh_node_get_tmin(const PBVHNode *node)
{
  return node->tmin;
}

void BKE_pbvh_search_callback(PBVH *pbvh,
                              blender::FunctionRef<bool(PBVHNode &)> scb,
                              BKE_pbvh_HitCallback hcb,
                              void *hit_data)
{
  if (pbvh->nodes.is_empty()) {
    return;
  }
  PBVHIter iter;
  PBVHNode *node;

  pbvh_iter_begin(&iter, pbvh, scb);

  while ((node = pbvh_iter_next(&iter, PBVH_Leaf))) {
    if (node->flag & PBVH_Leaf) {
      hcb(node, hit_data);
    }
  }

  pbvh_iter_end(&iter);
}

static void BKE_pbvh_search_callback_occluded(PBVH *pbvh,
                                              blender::FunctionRef<bool(PBVHNode &)> scb,
                                              BKE_pbvh_HitOccludedCallback hcb,
                                              void *hit_data)
{
  if (pbvh->nodes.is_empty()) {
    return;
  }
  PBVHIter iter;
  PBVHNode *node;
  node_tree *tree = nullptr;

  pbvh_iter_begin(&iter, pbvh, scb);

  while ((node = pbvh_iter_next_occluded(&iter))) {
    if (node->flag & PBVH_Leaf) {
      node_tree *new_node = static_cast<node_tree *>(malloc(sizeof(node_tree)));

      new_node->data = node;

      new_node->left = nullptr;
      new_node->right = nullptr;

      if (tree) {
        node_tree_insert(tree, new_node);
      }
      else {
        tree = new_node;
      }
    }
  }

  pbvh_iter_end(&iter);

  if (tree) {
    float tmin = FLT_MAX;
    traverse_tree(tree, hcb, hit_data, &tmin);
    free_tree(tree);
  }
}

static bool update_search(PBVHNode *node, const int flag)
{
  if (node->flag & PBVH_Leaf) {
    return (node->flag & flag) != 0;
  }

  return true;
}

static void normals_calc_faces(const Span<float3> positions,
                               const blender::OffsetIndices<int> faces,
                               const Span<int> corner_verts,
                               const Span<int> mask,
                               MutableSpan<float3> face_normals)
{
  using namespace blender;
  using namespace blender::bke;
  threading::parallel_for(mask.index_range(), 512, [&](const IndexRange range) {
    for (const int i : mask.slice(range)) {
      face_normals[i] = mesh::face_normal_calc(positions, corner_verts.slice(faces[i]));
    }
  });
}

static void normals_calc_verts_simple(const blender::GroupedSpan<int> vert_to_face_map,
                                      const Span<float3> face_normals,
                                      const Span<int> mask,
                                      MutableSpan<float3> vert_normals)
{
  using namespace blender;
  threading::parallel_for(mask.index_range(), 1024, [&](const IndexRange range) {
    for (const int vert : mask.slice(range)) {
      float3 normal(0.0f);
      for (const int face : vert_to_face_map[vert]) {
        normal += face_normals[face];
      }
      vert_normals[vert] = math::normalize(normal);
    }
  });
}

static void pbvh_faces_update_normals(PBVH *pbvh, Span<PBVHNode *> nodes, Mesh &mesh)
{
  using namespace blender;
  using namespace blender::bke;
  const Span<float3> positions = pbvh->vert_positions;
  const OffsetIndices faces = mesh.faces();
  const Span<int> corner_verts = mesh.corner_verts();

  MutableSpan<bool> update_tags = pbvh->vert_bitmap;

  VectorSet<int> faces_to_update;
  for (const PBVHNode *node : nodes) {
    for (const int vert : node->vert_indices.as_span().take_front(node->uniq_verts)) {
      if (update_tags[vert]) {
        faces_to_update.add_multiple(pbvh->pmap[vert]);
      }
    }
  }

  if (faces_to_update.is_empty()) {
    return;
  }

  VectorSet<int> verts_to_update;
  threading::parallel_invoke(
      [&]() {
        if (pbvh->deformed) {
          normals_calc_faces(
              positions, faces, corner_verts, faces_to_update, pbvh->face_normals_deformed);
        }
        else {
          mesh.runtime->face_normals_cache.update([&](Vector<float3> &r_data) {
            normals_calc_faces(positions, faces, corner_verts, faces_to_update, r_data);
          });
          /* #SharedCache::update() reallocates cached vectors if they were shared initially. */
          pbvh->face_normals = mesh.runtime->face_normals_cache.data();
        }
      },
      [&]() {
        /* Update all normals connected to affected faces, even if not explicitly tagged. */
        verts_to_update.reserve(faces_to_update.size());
        for (const int face : faces_to_update) {
          verts_to_update.add_multiple(corner_verts.slice(faces[face]));
        }

        for (const int vert : verts_to_update) {
          update_tags[vert] = false;
        }
        for (PBVHNode *node : nodes) {
          node->flag &= ~PBVH_UpdateNormals;
        }
      });

  if (pbvh->deformed) {
    normals_calc_verts_simple(
        pbvh->pmap, pbvh->face_normals, verts_to_update, pbvh->vert_normals_deformed);
  }
  else {
    mesh.runtime->vert_normals_cache.update([&](Vector<float3> &r_data) {
      normals_calc_verts_simple(pbvh->pmap, pbvh->face_normals, verts_to_update, r_data);
    });
    pbvh->vert_normals = mesh.runtime->vert_normals_cache.data();
  }
}

static void node_update_bounds(PBVH &pbvh, PBVHNode &node, const PBVHNodeFlags flag)
{
  if ((flag & PBVH_UpdateBB) && (node.flag & PBVH_UpdateBB)) {
    /* don't clear flag yet, leave it for flushing later */
    /* Note that bvh usage is read-only here, so no need to thread-protect it. */
    update_node_vb(&pbvh, &node);
  }

  if ((flag & PBVH_UpdateOriginalBB) && (node.flag & PBVH_UpdateOriginalBB)) {
    node.orig_vb = node.vb;
  }

  if ((flag & PBVH_UpdateRedraw) && (node.flag & PBVH_UpdateRedraw)) {
    node.flag &= ~PBVH_UpdateRedraw;
  }
}

static void pbvh_update_BB_redraw(PBVH *pbvh, Span<PBVHNode *> nodes, int flag)
{
  using namespace blender;
  threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
    for (PBVHNode *node : nodes.slice(range)) {
      node_update_bounds(*pbvh, *node, PBVHNodeFlags(flag));
    }
  });
}

bool BKE_pbvh_get_color_layer(Mesh *me, CustomDataLayer **r_layer, eAttrDomain *r_domain)
{
  *r_layer = BKE_id_attribute_search_for_write(
      &me->id, me->active_color_attribute, CD_MASK_COLOR_ALL, ATTR_DOMAIN_MASK_COLOR);
  *r_domain = *r_layer ? BKE_id_attribute_domain(&me->id, *r_layer) : ATTR_DOMAIN_POINT;
  return *r_layer != nullptr;
}

static int pbvh_flush_bb(PBVH *pbvh, PBVHNode *node, int flag)
{
  int update = 0;

  /* Difficult to multi-thread well, we just do single threaded recursive. */
  if (node->flag & PBVH_Leaf) {
    if (flag & PBVH_UpdateBB) {
      update |= (node->flag & PBVH_UpdateBB);
      node->flag &= ~PBVH_UpdateBB;
    }

    if (flag & PBVH_UpdateOriginalBB) {
      update |= (node->flag & PBVH_UpdateOriginalBB);
      node->flag &= ~PBVH_UpdateOriginalBB;
    }

    return update;
  }

  update |= pbvh_flush_bb(pbvh, &pbvh->nodes[node->children_offset], flag);
  update |= pbvh_flush_bb(pbvh, &pbvh->nodes[node->children_offset + 1], flag);

  if (update & PBVH_UpdateBB) {
    update_node_vb(pbvh, node);
  }
  if (update & PBVH_UpdateOriginalBB) {
    node->orig_vb = node->vb;
  }

  return update;
}

void BKE_pbvh_update_bounds(PBVH *pbvh, int flag)
{
  if (pbvh->nodes.is_empty()) {
    return;
  }

  Vector<PBVHNode *> nodes = blender::bke::pbvh::search_gather(
      pbvh, [&](PBVHNode &node) { return update_search(&node, flag); });

  if (flag & (PBVH_UpdateBB | PBVH_UpdateOriginalBB | PBVH_UpdateRedraw)) {
    pbvh_update_BB_redraw(pbvh, nodes, flag);
  }

  if (flag & (PBVH_UpdateBB | PBVH_UpdateOriginalBB)) {
    pbvh_flush_bb(pbvh, &pbvh->nodes.first(), flag);
  }
}

void BKE_pbvh_update_vertex_data(PBVH *pbvh, int flag)
{
  using namespace blender;
  Vector<PBVHNode *> nodes = blender::bke::pbvh::search_gather(
      pbvh, [&](PBVHNode &node) { return update_search(&node, flag); });

  if (flag & (PBVH_UpdateColor)) {
    for (PBVHNode *node : nodes) {
      node->flag |= PBVH_UpdateRedraw | PBVH_UpdateDrawBuffers | PBVH_UpdateColor;
    }
  }
}

namespace blender::bke::pbvh {

void node_update_mask_mesh(const Span<float> mask, PBVHNode &node)
{
  const bool fully_masked = std::all_of(node.vert_indices.begin(),
                                        node.vert_indices.end(),
                                        [&](const int vert) { return mask[vert] == 1.0f; });
  const bool fully_unmasked = std::all_of(node.vert_indices.begin(),
                                          node.vert_indices.end(),
                                          [&](const int vert) { return mask[vert] <= 0.0f; });
  SET_FLAG_FROM_TEST(node.flag, fully_masked, PBVH_FullyMasked);
  SET_FLAG_FROM_TEST(node.flag, fully_unmasked, PBVH_FullyUnmasked);
  node.flag &= ~PBVH_UpdateMask;
}

static void update_mask_mesh(const Mesh &mesh, const Span<PBVHNode *> nodes)
{
  const AttributeAccessor attributes = mesh.attributes();
  const VArraySpan<float> mask = *attributes.lookup<float>(".sculpt_mask", ATTR_DOMAIN_POINT);
  if (mask.is_empty()) {
    for (PBVHNode *node : nodes) {
      node->flag &= ~PBVH_FullyMasked;
      node->flag |= PBVH_FullyUnmasked;
      node->flag &= ~PBVH_UpdateMask;
    }
    return;
  }

  threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
    for (PBVHNode *node : nodes.slice(range)) {
      node_update_mask_mesh(mask, *node);
    }
  });
}

void node_update_mask_grids(const CCGKey &key, const Span<CCGElem *> grids, PBVHNode &node)
{
  BLI_assert(key.has_mask);
  bool fully_masked = true;
  bool fully_unmasked = true;
  for (const int grid : node.prim_indices) {
    CCGElem *elem = grids[grid];
    for (const int i : IndexRange(key.grid_area)) {
      const float mask = *CCG_elem_offset_mask(&key, elem, i);
      fully_masked &= mask == 1.0f;
      fully_unmasked &= mask <= 0.0f;
    }
  }
  SET_FLAG_FROM_TEST(node.flag, fully_masked, PBVH_FullyMasked);
  SET_FLAG_FROM_TEST(node.flag, fully_unmasked, PBVH_FullyUnmasked);
  node.flag &= ~PBVH_UpdateMask;
}

static void update_mask_grids(const SubdivCCG &subdiv_ccg, const Span<PBVHNode *> nodes)
{
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
  if (!key.has_mask) {
    for (PBVHNode *node : nodes) {
      node->flag &= ~PBVH_FullyMasked;
      node->flag |= PBVH_FullyUnmasked;
      node->flag &= ~PBVH_UpdateMask;
    }
    return;
  }

  threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
    for (PBVHNode *node : nodes.slice(range)) {
      node_update_mask_grids(key, subdiv_ccg.grids, *node);
    }
  });
}

void node_update_mask_bmesh(const int mask_offset, PBVHNode &node)
{
  BLI_assert(mask_offset != -1);
  bool fully_masked = true;
  bool fully_unmasked = true;
  for (const BMVert *vert : node.bm_unique_verts) {
    fully_masked &= BM_ELEM_CD_GET_FLOAT(vert, mask_offset) == 1.0f;
    fully_unmasked &= BM_ELEM_CD_GET_FLOAT(vert, mask_offset) <= 0.0f;
  }
  for (const BMVert *vert : node.bm_other_verts) {
    fully_masked &= BM_ELEM_CD_GET_FLOAT(vert, mask_offset) == 1.0f;
    fully_unmasked &= BM_ELEM_CD_GET_FLOAT(vert, mask_offset) <= 0.0f;
  }
  SET_FLAG_FROM_TEST(node.flag, fully_masked, PBVH_FullyMasked);
  SET_FLAG_FROM_TEST(node.flag, fully_unmasked, PBVH_FullyUnmasked);
  node.flag &= ~PBVH_UpdateMask;
}

static void update_mask_bmesh(const BMesh &bm, const Span<PBVHNode *> nodes)
{
  const int offset = CustomData_get_offset_named(&bm.vdata, CD_PROP_FLOAT, ".sculpt_mask");
  if (offset == -1) {
    for (PBVHNode *node : nodes) {
      node->flag &= ~PBVH_FullyMasked;
      node->flag |= PBVH_FullyUnmasked;
      node->flag &= ~PBVH_UpdateMask;
    }
    return;
  }

  threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
    for (PBVHNode *node : nodes.slice(range)) {
      node_update_mask_bmesh(offset, *node);
    }
  });
}

}  // namespace blender::bke::pbvh

void BKE_pbvh_update_mask(PBVH *pbvh)
{
  using namespace blender::bke::pbvh;
  Vector<PBVHNode *> nodes = search_gather(
      pbvh, [&](PBVHNode &node) { return update_search(&node, PBVH_UpdateMask); });

  switch (BKE_pbvh_type(pbvh)) {
    case PBVH_FACES:
      update_mask_mesh(*pbvh->mesh, nodes);
      break;
    case PBVH_GRIDS:
      update_mask_grids(*pbvh->subdiv_ccg, nodes);
      break;
    case PBVH_BMESH:
      update_mask_bmesh(*pbvh->header.bm, nodes);
      break;
  }
}

namespace blender::bke::pbvh {

void node_update_visibility_mesh(const Span<bool> hide_vert, PBVHNode &node)
{
  BLI_assert(!hide_vert.is_empty());
  const bool fully_hidden = std::all_of(node.vert_indices.begin(),
                                        node.vert_indices.end(),
                                        [&](const int vert) { return hide_vert[vert]; });
  SET_FLAG_FROM_TEST(node.flag, fully_hidden, PBVH_FullyHidden);
  node.flag &= ~PBVH_UpdateVisibility;
}

static void pbvh_faces_node_visibility_update(const Mesh &mesh, const Span<PBVHNode *> nodes)
{
  const AttributeAccessor attributes = mesh.attributes();
  const VArraySpan<bool> hide_vert = *attributes.lookup<bool>(".hide_vert", ATTR_DOMAIN_POINT);
  if (hide_vert.is_empty()) {
    for (PBVHNode *node : nodes) {
      node->flag &= ~PBVH_FullyHidden;
      node->flag &= ~PBVH_UpdateVisibility;
    }
    return;
  }

  threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
    for (PBVHNode *node : nodes.slice(range)) {
      node_update_visibility_mesh(hide_vert, *node);
    }
  });
}

void node_update_visibility_grids(const BitGroupVector<> &grid_hidden, PBVHNode &node)
{
  BLI_assert(!grid_hidden.is_empty());
  const bool fully_hidden = std::none_of(
      node.prim_indices.begin(), node.prim_indices.end(), [&](const int grid) {
        return bits::any_bit_unset(grid_hidden[grid]);
      });
  SET_FLAG_FROM_TEST(node.flag, fully_hidden, PBVH_FullyHidden);
  node.flag &= ~PBVH_UpdateVisibility;
}

static void pbvh_grids_node_visibility_update(PBVH *pbvh, const Span<PBVHNode *> nodes)
{
  const BitGroupVector<> &grid_hidden = pbvh->subdiv_ccg->grid_hidden;
  if (grid_hidden.is_empty()) {
    for (PBVHNode *node : nodes) {
      node->flag &= ~PBVH_FullyHidden;
      node->flag &= ~PBVH_UpdateVisibility;
    }
    return;
  }

  threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
    for (PBVHNode *node : nodes.slice(range)) {
      node_update_visibility_grids(grid_hidden, *node);
    }
  });
}

void node_update_visibility_bmesh(PBVHNode &node)
{
  const bool unique_hidden = std::all_of(
      node.bm_unique_verts.begin(), node.bm_unique_verts.end(), [&](const BMVert *vert) {
        return BM_elem_flag_test(vert, BM_ELEM_HIDDEN);
      });
  const bool other_hidden = std::all_of(
      node.bm_other_verts.begin(), node.bm_other_verts.end(), [&](const BMVert *vert) {
        return BM_elem_flag_test(vert, BM_ELEM_HIDDEN);
      });
  SET_FLAG_FROM_TEST(node.flag, unique_hidden && other_hidden, PBVH_FullyHidden);
  node.flag &= ~PBVH_UpdateVisibility;
}

static void pbvh_bmesh_node_visibility_update(const Span<PBVHNode *> nodes)
{
  threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
    for (PBVHNode *node : nodes.slice(range)) {
      node_update_visibility_bmesh(*node);
    }
  });
}

}  // namespace blender::bke::pbvh

void BKE_pbvh_update_visibility(PBVH *pbvh)
{
  using namespace blender::bke::pbvh;
  Vector<PBVHNode *> nodes = search_gather(
      pbvh, [&](PBVHNode &node) { return update_search(&node, PBVH_UpdateVisibility); });

  switch (BKE_pbvh_type(pbvh)) {
    case PBVH_FACES:
      pbvh_faces_node_visibility_update(*pbvh->mesh, nodes);
      break;
    case PBVH_GRIDS:
      pbvh_grids_node_visibility_update(pbvh, nodes);
      break;
    case PBVH_BMESH:
      pbvh_bmesh_node_visibility_update(nodes);
      break;
  }
}

Bounds<float3> BKE_pbvh_redraw_BB(PBVH *pbvh)
{
  using namespace blender;
  if (pbvh->nodes.is_empty()) {
    return {};
  }
  Bounds<float3> bounds = negative_bounds();

  PBVHIter iter;
  pbvh_iter_begin(&iter, pbvh, {});
  PBVHNode *node;
  while ((node = pbvh_iter_next(&iter, PBVH_Leaf))) {
    if (node->flag & PBVH_UpdateRedraw) {
      bounds = bounds::merge(bounds, node->vb);
    }
  }
  pbvh_iter_end(&iter);

  return bounds;
}

blender::IndexMask BKE_pbvh_get_grid_updates(const PBVH *pbvh,
                                             const Span<const PBVHNode *> nodes,
                                             blender::IndexMaskMemory &memory)
{
  using namespace blender;
  const Span<int> grid_to_face_map = pbvh->subdiv_ccg->grid_to_face_map;
  /* Using a #VectorSet for index deduplication would also work, but the performance gets much
   * worse with large selections since the loop would be single-threaded. A boolean array has an
   * overhead regardless of selection size, but that is small. */
  Array<bool> faces_to_update(pbvh->faces_num, false);
  threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
    for (const PBVHNode *node : nodes.slice(range)) {
      for (const int grid : node->prim_indices) {
        faces_to_update[grid_to_face_map[grid]] = true;
      }
    }
  });
  return IndexMask::from_bools(faces_to_update, memory);
}

/***************************** PBVH Access ***********************************/

bool BKE_pbvh_has_faces(const PBVH *pbvh)
{
  if (pbvh->header.type == PBVH_BMESH) {
    return (pbvh->header.bm->totface != 0);
  }

  return (pbvh->totprim != 0);
}

Bounds<float3> BKE_pbvh_bounding_box(const PBVH *pbvh)
{
  if (pbvh->nodes.is_empty()) {
    return float3(0);
  }
  return pbvh->nodes.first().vb;
}

const CCGKey *BKE_pbvh_get_grid_key(const PBVH *pbvh)
{
  BLI_assert(pbvh->header.type == PBVH_GRIDS);
  return &pbvh->gridkey;
}

int BKE_pbvh_get_grid_num_verts(const PBVH *pbvh)
{
  BLI_assert(pbvh->header.type == PBVH_GRIDS);
  return pbvh->subdiv_ccg->grids.size() * pbvh->gridkey.grid_area;
}

int BKE_pbvh_get_grid_num_faces(const PBVH *pbvh)
{
  BLI_assert(pbvh->header.type == PBVH_GRIDS);
  return pbvh->subdiv_ccg->grids.size() * (pbvh->gridkey.grid_size - 1) *
         (pbvh->gridkey.grid_size - 1);
}

/***************************** Node Access ***********************************/

void BKE_pbvh_node_mark_update(PBVHNode *node)
{
  node->flag |= PBVH_UpdateNormals | PBVH_UpdateBB | PBVH_UpdateOriginalBB |
                PBVH_UpdateDrawBuffers | PBVH_UpdateRedraw | PBVH_RebuildPixels;
}

void BKE_pbvh_node_mark_update_mask(PBVHNode *node)
{
  node->flag |= PBVH_UpdateMask | PBVH_UpdateDrawBuffers | PBVH_UpdateRedraw;
}

void BKE_pbvh_node_mark_update_color(PBVHNode *node)
{
  node->flag |= PBVH_UpdateColor | PBVH_UpdateDrawBuffers | PBVH_UpdateRedraw;
}

void BKE_pbvh_node_mark_update_face_sets(PBVHNode *node)
{
  node->flag |= PBVH_UpdateDrawBuffers | PBVH_UpdateRedraw;
}

void BKE_pbvh_mark_rebuild_pixels(PBVH *pbvh)
{
  for (PBVHNode &node : pbvh->nodes) {
    if (node.flag & PBVH_Leaf) {
      node.flag |= PBVH_RebuildPixels;
    }
  }
}

void BKE_pbvh_node_mark_update_visibility(PBVHNode *node)
{
  node->flag |= PBVH_UpdateVisibility | PBVH_RebuildDrawBuffers | PBVH_UpdateDrawBuffers |
                PBVH_UpdateRedraw;
}

void BKE_pbvh_node_mark_rebuild_draw(PBVHNode *node)
{
  node->flag |= PBVH_RebuildDrawBuffers | PBVH_UpdateDrawBuffers | PBVH_UpdateRedraw;
}

void BKE_pbvh_node_mark_redraw(PBVHNode *node)
{
  node->flag |= PBVH_UpdateDrawBuffers | PBVH_UpdateRedraw;
}

void BKE_pbvh_node_mark_normals_update(PBVHNode *node)
{
  node->flag |= PBVH_UpdateNormals;
}

void BKE_pbvh_node_fully_hidden_set(PBVHNode *node, int fully_hidden)
{
  BLI_assert(node->flag & PBVH_Leaf);

  if (fully_hidden) {
    node->flag |= PBVH_FullyHidden;
  }
  else {
    node->flag &= ~PBVH_FullyHidden;
  }
}

bool BKE_pbvh_node_fully_hidden_get(const PBVHNode *node)
{
  return (node->flag & PBVH_Leaf) && (node->flag & PBVH_FullyHidden);
}

void BKE_pbvh_node_fully_masked_set(PBVHNode *node, int fully_masked)
{
  BLI_assert(node->flag & PBVH_Leaf);

  if (fully_masked) {
    node->flag |= PBVH_FullyMasked;
  }
  else {
    node->flag &= ~PBVH_FullyMasked;
  }
}

bool BKE_pbvh_node_fully_masked_get(const PBVHNode *node)
{
  return (node->flag & PBVH_Leaf) && (node->flag & PBVH_FullyMasked);
}

void BKE_pbvh_node_fully_unmasked_set(PBVHNode *node, int fully_masked)
{
  BLI_assert(node->flag & PBVH_Leaf);

  if (fully_masked) {
    node->flag |= PBVH_FullyUnmasked;
  }
  else {
    node->flag &= ~PBVH_FullyUnmasked;
  }
}

bool BKE_pbvh_node_fully_unmasked_get(const PBVHNode *node)
{
  return (node->flag & PBVH_Leaf) && (node->flag & PBVH_FullyUnmasked);
}

void BKE_pbvh_vert_tag_update_normal(PBVH *pbvh, PBVHVertRef vertex)
{
  BLI_assert(pbvh->header.type == PBVH_FACES);
  pbvh->vert_bitmap[vertex.i] = true;
}

void BKE_pbvh_node_get_loops(const PBVHNode *node, const int **r_loop_indices)
{
  if (r_loop_indices) {
    *r_loop_indices = node->loop_indices.data();
  }
}

int BKE_pbvh_num_faces(const PBVH *pbvh)
{
  switch (pbvh->header.type) {
    case PBVH_GRIDS:
    case PBVH_FACES:
      return pbvh->faces_num;
    case PBVH_BMESH:
      return pbvh->header.bm->totface;
  }

  BLI_assert_unreachable();
  return 0;
}

blender::Span<int> BKE_pbvh_node_get_vert_indices(const PBVHNode *node)
{
  return node->vert_indices;
}

blender::Span<int> BKE_pbvh_node_get_unique_vert_indices(const PBVHNode *node)
{
  return node->vert_indices.as_span().take_front(node->uniq_verts);
}

blender::Vector<int> BKE_pbvh_node_calc_face_indices(const PBVH &pbvh, const PBVHNode &node)
{
  Vector<int> faces;
  switch (pbvh.header.type) {
    case PBVH_FACES: {
      const Span<int> looptri_faces = pbvh.looptri_faces;
      int prev_face = -1;
      for (const int tri : node.prim_indices) {
        const int face = looptri_faces[tri];
        if (face != prev_face) {
          faces.append(face);
          prev_face = face;
        }
      }
      break;
    }
    case PBVH_GRIDS: {
      const SubdivCCG &subdiv_ccg = *pbvh.subdiv_ccg;
      int prev_face = -1;
      for (const int prim : node.prim_indices) {
        const int face = BKE_subdiv_ccg_grid_to_face_index(subdiv_ccg, prim);
        if (face != prev_face) {
          faces.append(face);
          prev_face = face;
        }
      }
      break;
    }
    case PBVH_BMESH:
      BLI_assert_unreachable();
      break;
  }

  return faces;
}

void BKE_pbvh_node_num_verts(const PBVH *pbvh,
                             const PBVHNode *node,
                             int *r_uniquevert,
                             int *r_totvert)
{
  int tot;

  switch (pbvh->header.type) {
    case PBVH_GRIDS:
      tot = node->prim_indices.size() * pbvh->gridkey.grid_area;
      if (r_totvert) {
        *r_totvert = tot;
      }
      if (r_uniquevert) {
        *r_uniquevert = tot;
      }
      break;
    case PBVH_FACES:
      if (r_totvert) {
        *r_totvert = node->uniq_verts + node->face_verts;
      }
      if (r_uniquevert) {
        *r_uniquevert = node->uniq_verts;
      }
      break;
    case PBVH_BMESH:
      tot = node->bm_unique_verts.size();
      if (r_totvert) {
        *r_totvert = tot + node->bm_other_verts.size();
      }
      if (r_uniquevert) {
        *r_uniquevert = tot;
      }
      break;
  }
}

int BKE_pbvh_node_num_unique_verts(const PBVH &pbvh, const PBVHNode &node)
{
  switch (pbvh.header.type) {
    case PBVH_GRIDS:
      return node.prim_indices.size() * pbvh.gridkey.grid_area;
    case PBVH_FACES:
      return node.uniq_verts;
    case PBVH_BMESH:
      return node.bm_unique_verts.size();
  }
  BLI_assert_unreachable();
  return 0;
}

Span<int> BKE_pbvh_node_get_grid_indices(const PBVHNode &node)
{
  return node.prim_indices;
}

Bounds<float3> BKE_pbvh_node_get_BB(const PBVHNode *node)
{
  return node->vb;
}

Bounds<float3> BKE_pbvh_node_get_original_BB(const PBVHNode *node)
{
  return node->orig_vb;
}

blender::MutableSpan<PBVHProxyNode> BKE_pbvh_node_get_proxies(PBVHNode *node)
{
  return node->proxies;
}

void BKE_pbvh_node_get_bm_orco_data(PBVHNode *node,
                                    int (**r_orco_tris)[3],
                                    int *r_orco_tris_num,
                                    float (**r_orco_coords)[3],
                                    BMVert ***r_orco_verts)
{
  *r_orco_tris = node->bm_ortri;
  *r_orco_tris_num = node->bm_tot_ortri;
  *r_orco_coords = node->bm_orco;

  if (r_orco_verts) {
    *r_orco_verts = node->bm_orvert;
  }
}

bool BKE_pbvh_node_has_vert_with_normal_update_tag(PBVH *pbvh, PBVHNode *node)
{
  BLI_assert(pbvh->header.type == PBVH_FACES);
  for (const int vert : node->vert_indices) {
    if (pbvh->vert_bitmap[vert]) {
      return true;
    }
  }
  return false;
}

/********************************* Ray-cast ***********************************/

struct RaycastData {
  IsectRayAABB_Precalc ray;
  bool original;
};

static bool ray_aabb_intersect(PBVHNode *node, RaycastData *rcd)
{
  if (rcd->original) {
    return isect_ray_aabb_v3(&rcd->ray, node->orig_vb.min, node->orig_vb.max, &node->tmin);
  }
  return isect_ray_aabb_v3(&rcd->ray, node->vb.min, node->vb.max, &node->tmin);
}

void BKE_pbvh_raycast(PBVH *pbvh,
                      BKE_pbvh_HitOccludedCallback cb,
                      void *data,
                      const float ray_start[3],
                      const float ray_normal[3],
                      bool original)
{
  RaycastData rcd;

  isect_ray_aabb_v3_precalc(&rcd.ray, ray_start, ray_normal);
  rcd.original = original;

  BKE_pbvh_search_callback_occluded(
      pbvh, [&](PBVHNode &node) { return ray_aabb_intersect(&node, &rcd); }, cb, data);
}

bool ray_face_intersection_quad(const float ray_start[3],
                                IsectRayPrecalc *isect_precalc,
                                const float t0[3],
                                const float t1[3],
                                const float t2[3],
                                const float t3[3],
                                float *depth)
{
  float depth_test;

  if ((isect_ray_tri_watertight_v3(ray_start, isect_precalc, t0, t1, t2, &depth_test, nullptr) &&
       (depth_test < *depth)) ||
      (isect_ray_tri_watertight_v3(ray_start, isect_precalc, t0, t2, t3, &depth_test, nullptr) &&
       (depth_test < *depth)))
  {
    *depth = depth_test;
    return true;
  }

  return false;
}

bool ray_face_intersection_tri(const float ray_start[3],
                               IsectRayPrecalc *isect_precalc,
                               const float t0[3],
                               const float t1[3],
                               const float t2[3],
                               float *depth)
{
  float depth_test;
  if (isect_ray_tri_watertight_v3(ray_start, isect_precalc, t0, t1, t2, &depth_test, nullptr) &&
      (depth_test < *depth))
  {
    *depth = depth_test;
    return true;
  }

  return false;
}

/* Take advantage of the fact we know this won't be an intersection.
 * Just handle ray-tri edges. */
static float dist_squared_ray_to_tri_v3_fast(const float ray_origin[3],
                                             const float ray_direction[3],
                                             const float v0[3],
                                             const float v1[3],
                                             const float v2[3],
                                             float r_point[3],
                                             float *r_depth)
{
  const float *tri[3] = {v0, v1, v2};
  float dist_sq_best = FLT_MAX;
  for (int i = 0, j = 2; i < 3; j = i++) {
    float point_test[3], depth_test = FLT_MAX;
    const float dist_sq_test = dist_squared_ray_to_seg_v3(
        ray_origin, ray_direction, tri[i], tri[j], point_test, &depth_test);
    if (dist_sq_test < dist_sq_best || i == 0) {
      copy_v3_v3(r_point, point_test);
      *r_depth = depth_test;
      dist_sq_best = dist_sq_test;
    }
  }
  return dist_sq_best;
}

bool ray_face_nearest_quad(const float ray_start[3],
                           const float ray_normal[3],
                           const float t0[3],
                           const float t1[3],
                           const float t2[3],
                           const float t3[3],
                           float *depth,
                           float *dist_sq)
{
  float dist_sq_test;
  float co[3], depth_test;

  if ((dist_sq_test = dist_squared_ray_to_tri_v3_fast(
           ray_start, ray_normal, t0, t1, t2, co, &depth_test)) < *dist_sq)
  {
    *dist_sq = dist_sq_test;
    *depth = depth_test;
    if ((dist_sq_test = dist_squared_ray_to_tri_v3_fast(
             ray_start, ray_normal, t0, t2, t3, co, &depth_test)) < *dist_sq)
    {
      *dist_sq = dist_sq_test;
      *depth = depth_test;
    }
    return true;
  }

  return false;
}

bool ray_face_nearest_tri(const float ray_start[3],
                          const float ray_normal[3],
                          const float t0[3],
                          const float t1[3],
                          const float t2[3],
                          float *depth,
                          float *dist_sq)
{
  float dist_sq_test;
  float co[3], depth_test;

  if ((dist_sq_test = dist_squared_ray_to_tri_v3_fast(
           ray_start, ray_normal, t0, t1, t2, co, &depth_test)) < *dist_sq)
  {
    *dist_sq = dist_sq_test;
    *depth = depth_test;
    return true;
  }

  return false;
}

static bool pbvh_faces_node_raycast(PBVH *pbvh,
                                    const PBVHNode *node,
                                    float (*origco)[3],
                                    const Span<int> corner_verts,
                                    const bool *hide_poly,
                                    const float ray_start[3],
                                    const float ray_normal[3],
                                    IsectRayPrecalc *isect_precalc,
                                    float *depth,
                                    PBVHVertRef *r_active_vertex,
                                    int *r_active_face_index,
                                    float *r_face_normal)
{
  const Span<float3> positions = pbvh->vert_positions;
  bool hit = false;
  float nearest_vertex_co[3] = {0.0f};

  for (const int i : node->prim_indices.index_range()) {
    const int looptri_i = node->prim_indices[i];
    const MLoopTri *lt = &pbvh->looptri[looptri_i];
    const blender::int3 face_verts = node->face_vert_indices[i];

    if (hide_poly && hide_poly[pbvh->looptri_faces[looptri_i]]) {
      continue;
    }

    const float *co[3];
    if (origco) {
      /* Intersect with backed up original coordinates. */
      co[0] = origco[face_verts[0]];
      co[1] = origco[face_verts[1]];
      co[2] = origco[face_verts[2]];
    }
    else {
      /* intersect with current coordinates */
      co[0] = positions[corner_verts[lt->tri[0]]];
      co[1] = positions[corner_verts[lt->tri[1]]];
      co[2] = positions[corner_verts[lt->tri[2]]];
    }

    if (ray_face_intersection_tri(ray_start, isect_precalc, co[0], co[1], co[2], depth)) {
      hit = true;

      if (r_face_normal) {
        normal_tri_v3(r_face_normal, co[0], co[1], co[2]);
      }

      if (r_active_vertex) {
        float location[3] = {0.0f};
        madd_v3_v3v3fl(location, ray_start, ray_normal, *depth);
        for (int j = 0; j < 3; j++) {
          /* Always assign nearest_vertex_co in the first iteration to avoid comparison against
           * uninitialized values. This stores the closest vertex in the current intersecting
           * triangle. */
          if (j == 0 ||
              len_squared_v3v3(location, co[j]) < len_squared_v3v3(location, nearest_vertex_co)) {
            copy_v3_v3(nearest_vertex_co, co[j]);
            r_active_vertex->i = corner_verts[lt->tri[j]];
            *r_active_face_index = pbvh->looptri_faces[looptri_i];
          }
        }
      }
    }
  }

  return hit;
}

static bool pbvh_grids_node_raycast(PBVH *pbvh,
                                    PBVHNode *node,
                                    float (*origco)[3],
                                    const float ray_start[3],
                                    const float ray_normal[3],
                                    IsectRayPrecalc *isect_precalc,
                                    float *depth,
                                    PBVHVertRef *r_active_vertex,
                                    int *r_active_grid_index,
                                    float *r_face_normal)
{
  const int totgrid = node->prim_indices.size();
  const int gridsize = pbvh->gridkey.grid_size;
  bool hit = false;
  float nearest_vertex_co[3] = {0.0};
  const CCGKey *gridkey = &pbvh->gridkey;
  const BitGroupVector<> &grid_hidden = pbvh->subdiv_ccg->grid_hidden;
  const Span<CCGElem *> grids = pbvh->subdiv_ccg->grids;

  for (int i = 0; i < totgrid; i++) {
    const int grid_index = node->prim_indices[i];
    CCGElem *grid = grids[grid_index];
    if (!grid) {
      continue;
    }

    for (int y = 0; y < gridsize - 1; y++) {
      for (int x = 0; x < gridsize - 1; x++) {
        /* check if grid face is hidden */
        if (!grid_hidden.is_empty()) {
          if (paint_is_grid_face_hidden(grid_hidden[grid_index], gridsize, x, y)) {
            continue;
          }
        }

        const float *co[4];
        if (origco) {
          co[0] = origco[(y + 1) * gridsize + x];
          co[1] = origco[(y + 1) * gridsize + x + 1];
          co[2] = origco[y * gridsize + x + 1];
          co[3] = origco[y * gridsize + x];
        }
        else {
          co[0] = CCG_grid_elem_co(gridkey, grid, x, y + 1);
          co[1] = CCG_grid_elem_co(gridkey, grid, x + 1, y + 1);
          co[2] = CCG_grid_elem_co(gridkey, grid, x + 1, y);
          co[3] = CCG_grid_elem_co(gridkey, grid, x, y);
        }

        if (ray_face_intersection_quad(
                ray_start, isect_precalc, co[0], co[1], co[2], co[3], depth)) {
          hit = true;

          if (r_face_normal) {
            normal_quad_v3(r_face_normal, co[0], co[1], co[2], co[3]);
          }

          if (r_active_vertex) {
            float location[3] = {0.0};
            madd_v3_v3v3fl(location, ray_start, ray_normal, *depth);

            const int x_it[4] = {0, 1, 1, 0};
            const int y_it[4] = {1, 1, 0, 0};

            for (int j = 0; j < 4; j++) {
              /* Always assign nearest_vertex_co in the first iteration to avoid comparison against
               * uninitialized values. This stores the closest vertex in the current intersecting
               * quad. */
              if (j == 0 || len_squared_v3v3(location, co[j]) <
                                len_squared_v3v3(location, nearest_vertex_co)) {
                copy_v3_v3(nearest_vertex_co, co[j]);

                r_active_vertex->i = gridkey->grid_area * grid_index +
                                     (y + y_it[j]) * gridkey->grid_size + (x + x_it[j]);
              }
            }
          }
          if (r_active_grid_index) {
            *r_active_grid_index = grid_index;
          }
        }
      }
    }

    if (origco) {
      origco += gridsize * gridsize;
    }
  }

  return hit;
}

bool BKE_pbvh_node_raycast(PBVH *pbvh,
                           PBVHNode *node,
                           float (*origco)[3],
                           bool use_origco,
                           const Span<int> corner_verts,
                           const bool *hide_poly,
                           const float ray_start[3],
                           const float ray_normal[3],
                           IsectRayPrecalc *isect_precalc,
                           float *depth,
                           PBVHVertRef *active_vertex,
                           int *active_face_grid_index,
                           float *face_normal)
{
  bool hit = false;

  if (node->flag & PBVH_FullyHidden) {
    return false;
  }

  switch (pbvh->header.type) {
    case PBVH_FACES:
      hit |= pbvh_faces_node_raycast(pbvh,
                                     node,
                                     origco,
                                     corner_verts,
                                     hide_poly,
                                     ray_start,
                                     ray_normal,
                                     isect_precalc,
                                     depth,
                                     active_vertex,
                                     active_face_grid_index,
                                     face_normal);
      break;
    case PBVH_GRIDS:
      hit |= pbvh_grids_node_raycast(pbvh,
                                     node,
                                     origco,
                                     ray_start,
                                     ray_normal,
                                     isect_precalc,
                                     depth,
                                     active_vertex,
                                     active_face_grid_index,
                                     face_normal);
      break;
    case PBVH_BMESH:
      BM_mesh_elem_index_ensure(pbvh->header.bm, BM_VERT);
      hit = pbvh_bmesh_node_raycast(node,
                                    ray_start,
                                    ray_normal,
                                    isect_precalc,
                                    depth,
                                    use_origco,
                                    active_vertex,
                                    face_normal);
      break;
  }

  return hit;
}

void BKE_pbvh_clip_ray_ortho(
    PBVH *pbvh, bool original, float ray_start[3], float ray_end[3], float ray_normal[3])
{
  if (pbvh->nodes.is_empty()) {
    return;
  }
  float rootmin_start, rootmin_end;
  Bounds<float3> bb_root;
  float bb_center[3], bb_diff[3];
  IsectRayAABB_Precalc ray;
  float ray_normal_inv[3];
  float offset = 1.0f + 1e-3f;
  const float offset_vec[3] = {1e-3f, 1e-3f, 1e-3f};

  if (original) {
    bb_root = BKE_pbvh_node_get_original_BB(&pbvh->nodes.first());
  }
  else {
    bb_root = BKE_pbvh_node_get_BB(&pbvh->nodes.first());
  }

  /* Calc rough clipping to avoid overflow later. See #109555. */
  float mat[3][3];
  axis_dominant_v3_to_m3(mat, ray_normal);
  float a[3], b[3], min[3] = {FLT_MAX, FLT_MAX, FLT_MAX}, max[3] = {FLT_MIN, FLT_MIN, FLT_MIN};

  /* Compute AABB bounds rotated along ray_normal.*/
  copy_v3_v3(a, bb_root.min);
  copy_v3_v3(b, bb_root.max);
  mul_m3_v3(mat, a);
  mul_m3_v3(mat, b);
  minmax_v3v3_v3(min, max, a);
  minmax_v3v3_v3(min, max, b);

  float cent[3];

  /* Find midpoint of aabb on ray. */
  mid_v3_v3v3(cent, bb_root.min, bb_root.max);
  float t = line_point_factor_v3(cent, ray_start, ray_end);
  interp_v3_v3v3(cent, ray_start, ray_end, t);

  /* Compute rough interval. */
  float dist = max[2] - min[2];
  madd_v3_v3v3fl(ray_start, cent, ray_normal, -dist);
  madd_v3_v3v3fl(ray_end, cent, ray_normal, dist);

  /* Slightly offset min and max in case we have a zero width node
   * (due to a plane mesh for instance), or faces very close to the bounding box boundary. */
  mid_v3_v3v3(bb_center, bb_root.max, bb_root.min);
  /* Diff should be same for both min/max since it's calculated from center. */
  sub_v3_v3v3(bb_diff, bb_root.max, bb_center);
  /* Handles case of zero width bb. */
  add_v3_v3(bb_diff, offset_vec);
  madd_v3_v3v3fl(bb_root.max, bb_center, bb_diff, offset);
  madd_v3_v3v3fl(bb_root.min, bb_center, bb_diff, -offset);

  /* Final projection of start ray. */
  isect_ray_aabb_v3_precalc(&ray, ray_start, ray_normal);
  if (!isect_ray_aabb_v3(&ray, bb_root.min, bb_root.max, &rootmin_start)) {
    return;
  }

  /* Final projection of end ray. */
  mul_v3_v3fl(ray_normal_inv, ray_normal, -1.0);
  isect_ray_aabb_v3_precalc(&ray, ray_end, ray_normal_inv);
  /* Unlikely to fail exiting if entering succeeded, still keep this here. */
  if (!isect_ray_aabb_v3(&ray, bb_root.min, bb_root.max, &rootmin_end)) {
    return;
  }

  /*
   * As a last-ditch effort to correct floating point overflow compute
   * and add an epsilon if rootmin_start == rootmin_end.
   */

  float epsilon = (std::nextafter(rootmin_start, rootmin_start + 1000.0f) - rootmin_start) *
                  5000.0f;

  if (rootmin_start == rootmin_end) {
    rootmin_start -= epsilon;
    rootmin_end += epsilon;
  }

  madd_v3_v3v3fl(ray_start, ray_start, ray_normal, rootmin_start);
  madd_v3_v3v3fl(ray_end, ray_end, ray_normal_inv, rootmin_end);
}

/* -------------------------------------------------------------------- */

struct FindNearestRayData {
  DistRayAABB_Precalc dist_ray_to_aabb_precalc;
  bool original;
};

static bool nearest_to_ray_aabb_dist_sq(PBVHNode *node, FindNearestRayData *rcd)
{
  const float *bb_min, *bb_max;

  if (rcd->original) {
    /* BKE_pbvh_node_get_original_BB */
    bb_min = node->orig_vb.min;
    bb_max = node->orig_vb.max;
  }
  else {
    /* BKE_pbvh_node_get_BB */
    bb_min = node->vb.min;
    bb_max = node->vb.max;
  }

  float co_dummy[3], depth;
  node->tmin = dist_squared_ray_to_aabb_v3(
      &rcd->dist_ray_to_aabb_precalc, bb_min, bb_max, co_dummy, &depth);
  /* Ideally we would skip distances outside the range. */
  return depth > 0.0f;
}

void BKE_pbvh_find_nearest_to_ray(PBVH *pbvh,
                                  BKE_pbvh_SearchNearestCallback cb,
                                  void *data,
                                  const float ray_start[3],
                                  const float ray_normal[3],
                                  bool original)
{
  FindNearestRayData ncd;

  dist_squared_ray_to_aabb_v3_precalc(&ncd.dist_ray_to_aabb_precalc, ray_start, ray_normal);
  ncd.original = original;

  BKE_pbvh_search_callback_occluded(
      pbvh, [&](PBVHNode &node) { return nearest_to_ray_aabb_dist_sq(&node, &ncd); }, cb, data);
}

static bool pbvh_faces_node_nearest_to_ray(PBVH *pbvh,
                                           const PBVHNode *node,
                                           float (*origco)[3],
                                           const Span<int> corner_verts,
                                           const bool *hide_poly,
                                           const float ray_start[3],
                                           const float ray_normal[3],
                                           float *depth,
                                           float *dist_sq)
{
  const Span<float3> positions = pbvh->vert_positions;
  bool hit = false;

  for (const int i : node->prim_indices.index_range()) {
    const int looptri_i = node->prim_indices[i];
    const MLoopTri *lt = &pbvh->looptri[looptri_i];
    const blender::int3 face_verts = node->face_vert_indices[i];

    if (hide_poly && hide_poly[pbvh->looptri_faces[looptri_i]]) {
      continue;
    }

    if (origco) {
      /* Intersect with backed-up original coordinates. */
      hit |= ray_face_nearest_tri(ray_start,
                                  ray_normal,
                                  origco[face_verts[0]],
                                  origco[face_verts[1]],
                                  origco[face_verts[2]],
                                  depth,
                                  dist_sq);
    }
    else {
      /* intersect with current coordinates */
      hit |= ray_face_nearest_tri(ray_start,
                                  ray_normal,
                                  positions[corner_verts[lt->tri[0]]],
                                  positions[corner_verts[lt->tri[1]]],
                                  positions[corner_verts[lt->tri[2]]],
                                  depth,
                                  dist_sq);
    }
  }

  return hit;
}

static bool pbvh_grids_node_nearest_to_ray(PBVH *pbvh,
                                           PBVHNode *node,
                                           float (*origco)[3],
                                           const float ray_start[3],
                                           const float ray_normal[3],
                                           float *depth,
                                           float *dist_sq)
{
  const int totgrid = node->prim_indices.size();
  const int gridsize = pbvh->gridkey.grid_size;
  bool hit = false;
  const BitGroupVector<> &grid_hidden = pbvh->subdiv_ccg->grid_hidden;
  const Span<CCGElem *> grids = pbvh->subdiv_ccg->grids;

  for (int i = 0; i < totgrid; i++) {
    CCGElem *grid = grids[node->prim_indices[i]];
    if (!grid) {
      continue;
    }

    for (int y = 0; y < gridsize - 1; y++) {
      for (int x = 0; x < gridsize - 1; x++) {
        /* check if grid face is hidden */
        if (!grid_hidden.is_empty()) {
          if (paint_is_grid_face_hidden(grid_hidden[node->prim_indices[i]], gridsize, x, y)) {
            continue;
          }
        }

        if (origco) {
          hit |= ray_face_nearest_quad(ray_start,
                                       ray_normal,
                                       origco[y * gridsize + x],
                                       origco[y * gridsize + x + 1],
                                       origco[(y + 1) * gridsize + x + 1],
                                       origco[(y + 1) * gridsize + x],
                                       depth,
                                       dist_sq);
        }
        else {
          hit |= ray_face_nearest_quad(ray_start,
                                       ray_normal,
                                       CCG_grid_elem_co(&pbvh->gridkey, grid, x, y),
                                       CCG_grid_elem_co(&pbvh->gridkey, grid, x + 1, y),
                                       CCG_grid_elem_co(&pbvh->gridkey, grid, x + 1, y + 1),
                                       CCG_grid_elem_co(&pbvh->gridkey, grid, x, y + 1),
                                       depth,
                                       dist_sq);
        }
      }
    }

    if (origco) {
      origco += gridsize * gridsize;
    }
  }

  return hit;
}

bool BKE_pbvh_node_find_nearest_to_ray(PBVH *pbvh,
                                       PBVHNode *node,
                                       float (*origco)[3],
                                       bool use_origco,
                                       const Span<int> corner_verts,
                                       const bool *hide_poly,
                                       const float ray_start[3],
                                       const float ray_normal[3],
                                       float *depth,
                                       float *dist_sq)
{
  bool hit = false;

  if (node->flag & PBVH_FullyHidden) {
    return false;
  }

  switch (pbvh->header.type) {
    case PBVH_FACES:
      hit |= pbvh_faces_node_nearest_to_ray(
          pbvh, node, origco, corner_verts, hide_poly, ray_start, ray_normal, depth, dist_sq);
      break;
    case PBVH_GRIDS:
      hit |= pbvh_grids_node_nearest_to_ray(
          pbvh, node, origco, ray_start, ray_normal, depth, dist_sq);
      break;
    case PBVH_BMESH:
      hit = pbvh_bmesh_node_nearest_to_ray(
          node, ray_start, ray_normal, depth, dist_sq, use_origco);
      break;
  }

  return hit;
}

enum PlaneAABBIsect {
  ISECT_INSIDE,
  ISECT_OUTSIDE,
  ISECT_INTERSECT,
};

/* Adapted from:
 * http://www.gamedev.net/community/forums/topic.asp?topic_id=512123
 * Returns true if the AABB is at least partially within the frustum
 * (ok, not a real frustum), false otherwise.
 */
static PlaneAABBIsect test_frustum_aabb(const Bounds<float3> &bounds,
                                        const PBVHFrustumPlanes *frustum)
{
  PlaneAABBIsect ret = ISECT_INSIDE;
  const float(*planes)[4] = frustum->planes;

  for (int i = 0; i < frustum->num_planes; i++) {
    float vmin[3], vmax[3];

    for (int axis = 0; axis < 3; axis++) {
      if (planes[i][axis] < 0) {
        vmin[axis] = bounds.min[axis];
        vmax[axis] = bounds.max[axis];
      }
      else {
        vmin[axis] = bounds.max[axis];
        vmax[axis] = bounds.min[axis];
      }
    }

    if (dot_v3v3(planes[i], vmin) + planes[i][3] < 0) {
      return ISECT_OUTSIDE;
    }
    if (dot_v3v3(planes[i], vmax) + planes[i][3] <= 0) {
      ret = ISECT_INTERSECT;
    }
  }

  return ret;
}

bool BKE_pbvh_node_frustum_contain_AABB(const PBVHNode *node, const PBVHFrustumPlanes *data)
{
  return test_frustum_aabb(node->vb, data) != ISECT_OUTSIDE;
}

bool BKE_pbvh_node_frustum_exclude_AABB(const PBVHNode *node, const PBVHFrustumPlanes *data)
{
  return test_frustum_aabb(node->vb, data) != ISECT_INSIDE;
}

void BKE_pbvh_update_normals(PBVH *pbvh, SubdivCCG *subdiv_ccg)
{
  using namespace blender;
  /* Update normals */
  Vector<PBVHNode *> nodes = blender::bke::pbvh::search_gather(
      pbvh, [&](PBVHNode &node) { return update_search(&node, PBVH_UpdateNormals); });

  if (pbvh->header.type == PBVH_BMESH) {
    pbvh_bmesh_normals_update(nodes);
  }
  else if (pbvh->header.type == PBVH_FACES) {
    pbvh_faces_update_normals(pbvh, nodes, *pbvh->mesh);
  }
  else if (pbvh->header.type == PBVH_GRIDS) {
    IndexMaskMemory memory;
    const IndexMask faces_to_update = BKE_pbvh_get_grid_updates(pbvh, nodes, memory);
    BKE_subdiv_ccg_update_normals(*subdiv_ccg, faces_to_update);
    for (PBVHNode *node : nodes) {
      node->flag &= ~PBVH_UpdateNormals;
    }
  }
}

static blender::draw::pbvh::PBVH_GPU_Args pbvh_draw_args_init(const Mesh &mesh,
                                                              PBVH &pbvh,
                                                              const PBVHNode &node)
{
  blender::draw::pbvh::PBVH_GPU_Args args{};

  args.pbvh_type = pbvh.header.type;

  args.face_sets_color_default = mesh.face_sets_color_default;
  args.face_sets_color_seed = mesh.face_sets_color_seed;

  args.active_color = mesh.active_color_attribute;
  args.render_color = mesh.default_color_attribute;

  switch (pbvh.header.type) {
    case PBVH_FACES:
      args.vert_data = &mesh.vert_data;
      args.loop_data = &mesh.loop_data;
      args.face_data = &mesh.face_data;
      args.me = pbvh.mesh;
      args.vert_positions = pbvh.vert_positions;
      args.corner_verts = mesh.corner_verts();
      args.corner_edges = mesh.corner_edges();
      args.mlooptri = pbvh.looptri;
      args.vert_normals = pbvh.vert_normals;
      args.face_normals = pbvh.face_normals;
      /* Retrieve data from the original mesh. Ideally that would be passed to this function to
       * make it clearer when each is used. */
      args.hide_poly = static_cast<const bool *>(
          CustomData_get_layer_named(&pbvh.mesh->face_data, CD_PROP_BOOL, ".hide_poly"));

      args.prim_indices = node.prim_indices;
      args.looptri_faces = mesh.looptri_faces();
      break;
    case PBVH_GRIDS:
      args.vert_data = &pbvh.mesh->vert_data;
      args.loop_data = &pbvh.mesh->loop_data;
      args.face_data = &pbvh.mesh->face_data;
      args.ccg_key = pbvh.gridkey;
      args.me = pbvh.mesh;
      args.grid_indices = node.prim_indices;
      args.subdiv_ccg = pbvh.subdiv_ccg;
      args.grids = pbvh.subdiv_ccg->grids;
      args.vert_normals = pbvh.vert_normals;
      break;
    case PBVH_BMESH:
      args.bm = pbvh.header.bm;
      args.vert_data = &args.bm->vdata;
      args.loop_data = &args.bm->ldata;
      args.face_data = &args.bm->pdata;
      args.bm_faces = &node.bm_faces;
      args.cd_mask_layer = CustomData_get_offset_named(
          &pbvh.header.bm->vdata, CD_PROP_FLOAT, ".sculpt_mask");

      break;
  }

  return args;
}

static void node_update_draw_buffers(const Mesh &mesh, PBVH &pbvh, PBVHNode &node)
{
  /* Create and update draw buffers. The functions called here must not
   * do any OpenGL calls. Flags are not cleared immediately, that happens
   * after GPU_pbvh_buffer_flush() which does the final OpenGL calls. */
  if (node.flag & PBVH_RebuildDrawBuffers) {
    const blender::draw::pbvh::PBVH_GPU_Args args = pbvh_draw_args_init(mesh, pbvh, node);
    node.draw_batches = blender::draw::pbvh::node_create(args);
  }

  if (node.flag & PBVH_UpdateDrawBuffers) {
    node.debug_draw_gen++;

    if (node.draw_batches) {
      const blender::draw::pbvh::PBVH_GPU_Args args = pbvh_draw_args_init(mesh, pbvh, node);
      blender::draw::pbvh::node_update(node.draw_batches, args);
    }
  }
}

void pbvh_free_draw_buffers(PBVH & /*pbvh*/, PBVHNode *node)
{
  if (node->draw_batches) {
    blender::draw::pbvh::node_free(node->draw_batches);
    node->draw_batches = nullptr;
  }
}

static void pbvh_update_draw_buffers(const Mesh &mesh,
                                     PBVH &pbvh,
                                     Span<PBVHNode *> nodes,
                                     int update_flag)
{
  using namespace blender;
  if (pbvh.header.type == PBVH_BMESH && !pbvh.header.bm) {
    /* BMesh hasn't been created yet */
    return;
  }

  if ((update_flag & PBVH_RebuildDrawBuffers) || ELEM(pbvh.header.type, PBVH_GRIDS, PBVH_BMESH)) {
    /* Free buffers uses OpenGL, so not in parallel. */
    for (PBVHNode *node : nodes) {
      if (node->flag & PBVH_RebuildDrawBuffers) {
        pbvh_free_draw_buffers(pbvh, node);
      }
      else if ((node->flag & PBVH_UpdateDrawBuffers) && node->draw_batches) {
        const draw::pbvh::PBVH_GPU_Args args = pbvh_draw_args_init(mesh, pbvh, *node);
        draw::pbvh::update_pre(node->draw_batches, args);
      }
    }
  }

  /* Parallel creation and update of draw buffers. */
  threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
    for (PBVHNode *node : nodes.slice(range)) {
      node_update_draw_buffers(mesh, pbvh, *node);
    }
  });

  /* Flush buffers uses OpenGL, so not in parallel. */
  for (PBVHNode *node : nodes) {
    if (node->flag & PBVH_UpdateDrawBuffers) {

      if (node->draw_batches) {
        draw::pbvh::node_gpu_flush(node->draw_batches);
      }
    }

    node->flag &= ~(PBVH_RebuildDrawBuffers | PBVH_UpdateDrawBuffers);
  }
}

void BKE_pbvh_draw_cb(
    const Mesh &mesh,
    PBVH *pbvh,
    bool update_only_visible,
    const PBVHFrustumPlanes &update_frustum,
    const PBVHFrustumPlanes &draw_frustum,
    const blender::FunctionRef<void(blender::draw::pbvh::PBVHBatches *batches,
                                    const blender::draw::pbvh::PBVH_GPU_Args &args)> draw_fn)
{
  using namespace blender;
  using namespace blender::bke::pbvh;
  pbvh->draw_cache_invalid = false;

  if (update_only_visible) {
    int update_flag = 0;
    Vector<PBVHNode *> nodes = search_gather(pbvh, [&](PBVHNode &node) {
      if (!BKE_pbvh_node_frustum_contain_AABB(&node, &update_frustum)) {
        return false;
      }
      update_flag |= node.flag;
      return true;
    });
    if (update_flag & (PBVH_RebuildDrawBuffers | PBVH_UpdateDrawBuffers)) {
      pbvh_update_draw_buffers(mesh, *pbvh, nodes, update_flag);
    }
  }
  else {
    /* Get all nodes with draw updates, also those outside the view. */
    Vector<PBVHNode *> nodes = search_gather(pbvh, [&](PBVHNode &node) {
      return update_search(&node, PBVH_RebuildDrawBuffers | PBVH_UpdateDrawBuffers);
    });
    pbvh_update_draw_buffers(mesh, *pbvh, nodes, PBVH_RebuildDrawBuffers | PBVH_UpdateDrawBuffers);
  }

  /* Draw visible nodes. */
  Vector<PBVHNode *> nodes = search_gather(pbvh, [&](PBVHNode &node) {
    return BKE_pbvh_node_frustum_contain_AABB(&node, &draw_frustum);
  });

  for (PBVHNode *node : nodes) {
    if (node->flag & PBVH_FullyHidden) {
      continue;
    }
    if (!node->draw_batches) {
      continue;
    }
    const draw::pbvh::PBVH_GPU_Args args = pbvh_draw_args_init(mesh, *pbvh, *node);
    draw_fn(node->draw_batches, args);
  }
}

void BKE_pbvh_draw_debug_cb(PBVH *pbvh,
                            void (*draw_fn)(PBVHNode *node,
                                            void *user_data,
                                            const float bmin[3],
                                            const float bmax[3],
                                            PBVHNodeFlags flag),
                            void *user_data)
{
  PBVHNodeFlags flag = PBVH_Leaf;

  for (PBVHNode &node : pbvh->nodes) {
    if (node.flag & PBVH_TexLeaf) {
      flag = PBVH_TexLeaf;
      break;
    }
  }

  for (PBVHNode &node : pbvh->nodes) {
    if (!(node.flag & flag)) {
      continue;
    }

    draw_fn(&node, user_data, node.vb.min, node.vb.max, node.flag);
  }
}

void BKE_pbvh_grids_update(PBVH *pbvh, const CCGKey *key)
{
  pbvh->gridkey = *key;
}

void BKE_pbvh_vert_coords_apply(PBVH *pbvh, const Span<float3> vert_positions)
{
  BLI_assert(vert_positions.size() == pbvh->totvert);

  if (!pbvh->deformed) {
    if (!pbvh->vert_positions.is_empty()) {
      /* When the PBVH is deformed, it creates a separate vertex position array that it owns
       * directly. Conceptually these copies often aren't and often adds extra indirection, but:
       *  - Sculpting shape keys, the deformations are flushed back to the keys as a separate step.
       *  - Sculpting on a deformed mesh, deformations are also flushed to original positions
       *    separately.
       *  - The PBVH currently always assumes we want to change positions, and has no way to avoid
       *    calculating normals if it's only used for painting, for example. */
      pbvh->vert_positions_deformed = pbvh->vert_positions.as_span();
      pbvh->vert_positions = pbvh->vert_positions_deformed;

      pbvh->vert_normals_deformed = pbvh->vert_normals;
      pbvh->vert_normals = pbvh->vert_normals_deformed;

      pbvh->face_normals_deformed = pbvh->face_normals;
      pbvh->face_normals = pbvh->face_normals_deformed;

      pbvh->deformed = true;
    }
  }

  if (!pbvh->vert_positions.is_empty()) {
    MutableSpan<float3> positions = pbvh->vert_positions;
    /* copy new verts coords */
    for (int a = 0; a < pbvh->totvert; a++) {
      /* no need for float comparison here (memory is exactly equal or not) */
      if (memcmp(positions[a], vert_positions[a], sizeof(float[3])) != 0) {
        positions[a] = vert_positions[a];
        BKE_pbvh_vert_tag_update_normal(pbvh, BKE_pbvh_make_vref(a));
      }
    }

    for (PBVHNode &node : pbvh->nodes) {
      BKE_pbvh_node_mark_update(&node);
    }

    BKE_pbvh_update_bounds(pbvh, PBVH_UpdateBB | PBVH_UpdateOriginalBB);
  }
}

bool BKE_pbvh_is_deformed(const PBVH *pbvh)
{
  return pbvh->deformed;
}
/* Proxies */

PBVHProxyNode &BKE_pbvh_node_add_proxy(PBVH &pbvh, PBVHNode &node)
{
  node.proxies.append_as(PBVHProxyNode{});

  /* It is fine to access pointer of the back element, since node is never handled from multiple
   * threads, and the brush handler only requests a single proxy from the node, and never holds
   * pointers to multiple proxies. */
  PBVHProxyNode &proxy_node = node.proxies.last();

  const int num_unique_verts = BKE_pbvh_node_num_unique_verts(pbvh, node);

  /* Brushes expect proxies to be zero-initialized, so that they can do additive operation to them.
   */
  proxy_node.co.resize(num_unique_verts, float3(0, 0, 0));

  return proxy_node;
}

void BKE_pbvh_node_free_proxies(PBVHNode *node)
{
  node->proxies.clear_and_shrink();
}

PBVHColorBufferNode *BKE_pbvh_node_color_buffer_get(PBVHNode *node)
{

  if (!node->color_buffer.color) {
    node->color_buffer.color = static_cast<float(*)[4]>(
        MEM_callocN(sizeof(float[4]) * node->uniq_verts, "Color buffer"));
  }
  return &node->color_buffer;
}

void BKE_pbvh_node_color_buffer_free(PBVH *pbvh)
{
  Vector<PBVHNode *> nodes = blender::bke::pbvh::search_gather(pbvh, {});

  for (PBVHNode *node : nodes) {
    MEM_SAFE_FREE(node->color_buffer.color);
  }
}

void pbvh_vertex_iter_init(PBVH *pbvh, PBVHNode *node, PBVHVertexIter *vi, int mode)
{
  vi->grid = nullptr;
  vi->no = nullptr;
  vi->fno = nullptr;
  vi->vert_positions = {};
  vi->vertex.i = 0LL;

  int uniq_verts, totvert;
  BKE_pbvh_node_num_verts(pbvh, node, &uniq_verts, &totvert);

  if (pbvh->header.type == PBVH_GRIDS) {
    vi->key = pbvh->gridkey;
    vi->grids = pbvh->subdiv_ccg->grids.data();
    vi->grid_indices = node->prim_indices.data();
    vi->totgrid = node->prim_indices.size();
    vi->gridsize = pbvh->gridkey.grid_size;
  }
  else {
    vi->key = {};
    vi->grids = nullptr;
    vi->grid_indices = nullptr;
    vi->totgrid = 1;
    vi->gridsize = 0;
  }

  if (mode == PBVH_ITER_ALL) {
    vi->totvert = totvert;
  }
  else {
    vi->totvert = uniq_verts;
  }
  vi->vert_indices = node->vert_indices.data();
  vi->vert_positions = pbvh->vert_positions;
  vi->is_mesh = !pbvh->vert_positions.is_empty();

  if (pbvh->header.type == PBVH_BMESH) {
    vi->bm_unique_verts = node->bm_unique_verts.begin();
    vi->bm_unique_verts_end = node->bm_unique_verts.end();
    vi->bm_other_verts = node->bm_other_verts.begin();
    vi->bm_other_verts_end = node->bm_other_verts.end();
    vi->bm_vdata = &pbvh->header.bm->vdata;
    vi->cd_vert_mask_offset = CustomData_get_offset_named(
        vi->bm_vdata, CD_PROP_FLOAT, ".sculpt_mask");
  }

  vi->gh.reset();
  if (vi->grids && mode == PBVH_ITER_UNIQUE) {
    vi->grid_hidden = pbvh->subdiv_ccg->grid_hidden.is_empty() ? nullptr :
                                                                 &pbvh->subdiv_ccg->grid_hidden;
  }

  vi->mask = 0.0f;
  if (pbvh->header.type == PBVH_FACES) {
    vi->vert_normals = pbvh->vert_normals;
    vi->hide_vert = static_cast<const bool *>(
        CustomData_get_layer_named(&pbvh->mesh->vert_data, CD_PROP_BOOL, ".hide_vert"));
    vi->vmask = static_cast<const float *>(
        CustomData_get_layer_named(&pbvh->mesh->vert_data, CD_PROP_FLOAT, ".sculpt_mask"));
  }
}

bool pbvh_has_mask(const PBVH *pbvh)
{
  switch (pbvh->header.type) {
    case PBVH_GRIDS:
      return (pbvh->gridkey.has_mask != 0);
    case PBVH_FACES:
      return pbvh->mesh->attributes().contains(".sculpt_mask");
    case PBVH_BMESH:
      return pbvh->header.bm &&
             (CustomData_has_layer_named(&pbvh->header.bm->vdata, CD_PROP_FLOAT, ".sculpt_mask"));
  }

  return false;
}

bool pbvh_has_face_sets(PBVH *pbvh)
{
  switch (pbvh->header.type) {
    case PBVH_GRIDS:
    case PBVH_FACES:
      return pbvh->mesh->attributes().contains(".sculpt_face_set");
    case PBVH_BMESH:
      return false;
  }

  return false;
}

void BKE_pbvh_set_frustum_planes(PBVH *pbvh, PBVHFrustumPlanes *planes)
{
  pbvh->num_planes = planes->num_planes;
  for (int i = 0; i < pbvh->num_planes; i++) {
    copy_v4_v4(pbvh->planes[i], planes->planes[i]);
  }
}

void BKE_pbvh_get_frustum_planes(const PBVH *pbvh, PBVHFrustumPlanes *planes)
{
  planes->num_planes = pbvh->num_planes;
  for (int i = 0; i < planes->num_planes; i++) {
    copy_v4_v4(planes->planes[i], pbvh->planes[i]);
  }
}

void BKE_pbvh_parallel_range_settings(TaskParallelSettings *settings,
                                      bool use_threading,
                                      int totnode)
{
  memset(settings, 0, sizeof(*settings));
  settings->use_threading = use_threading && totnode > 1;
}

Mesh *BKE_pbvh_get_mesh(PBVH *pbvh)
{
  return pbvh->mesh;
}

Span<float3> BKE_pbvh_get_vert_positions(const PBVH *pbvh)
{
  BLI_assert(pbvh->header.type == PBVH_FACES);
  return pbvh->vert_positions;
}

MutableSpan<float3> BKE_pbvh_get_vert_positions(PBVH *pbvh)
{
  BLI_assert(pbvh->header.type == PBVH_FACES);
  return pbvh->vert_positions;
}

Span<float3> BKE_pbvh_get_vert_normals(const PBVH *pbvh)
{
  BLI_assert(pbvh->header.type == PBVH_FACES);
  return pbvh->vert_normals;
}

void BKE_pbvh_subdiv_cgg_set(PBVH *pbvh, SubdivCCG *subdiv_ccg)
{
  pbvh->subdiv_ccg = subdiv_ccg;
}

bool BKE_pbvh_is_drawing(const PBVH *pbvh)
{
  return pbvh->is_drawing;
}

bool BKE_pbvh_draw_cache_invalid(const PBVH *pbvh)
{
  return pbvh->draw_cache_invalid;
}

void BKE_pbvh_is_drawing_set(PBVH *pbvh, bool val)
{
  pbvh->is_drawing = val;
}

void BKE_pbvh_node_num_loops(PBVH *pbvh, PBVHNode *node, int *r_totloop)
{
  UNUSED_VARS(pbvh);
  BLI_assert(BKE_pbvh_type(pbvh) == PBVH_FACES);

  if (r_totloop) {
    *r_totloop = node->loop_indices.size();
  }
}

void BKE_pbvh_update_active_vcol(PBVH *pbvh, Mesh *mesh)
{
  BKE_pbvh_get_color_layer(mesh, &pbvh->color_layer, &pbvh->color_domain);
}

void BKE_pbvh_pmap_set(PBVH *pbvh, const blender::GroupedSpan<int> pmap)
{
  pbvh->pmap = pmap;
}

void BKE_pbvh_ensure_node_loops(PBVH *pbvh)
{
  BLI_assert(BKE_pbvh_type(pbvh) == PBVH_FACES);

  int totloop = 0;

  /* Check if nodes already have loop indices. */
  for (PBVHNode &node : pbvh->nodes) {
    if (!(node.flag & PBVH_Leaf)) {
      continue;
    }

    if (!node.loop_indices.is_empty()) {
      return;
    }

    totloop += node.prim_indices.size() * 3;
  }

  BLI_bitmap *visit = BLI_BITMAP_NEW(totloop, __func__);

  /* Create loop indices from node loop triangles. */
  Vector<int> loop_indices;
  for (PBVHNode &node : pbvh->nodes) {
    if (!(node.flag & PBVH_Leaf)) {
      continue;
    }

    loop_indices.clear();

    for (const int i : node.prim_indices) {
      const MLoopTri &mlt = pbvh->looptri[i];

      for (int k = 0; k < 3; k++) {
        if (!BLI_BITMAP_TEST(visit, mlt.tri[k])) {
          loop_indices.append(mlt.tri[k]);
          BLI_BITMAP_ENABLE(visit, mlt.tri[k]);
        }
      }
    }

    node.loop_indices.reinitialize(loop_indices.size());
    node.loop_indices.as_mutable_span().copy_from(loop_indices);
  }

  MEM_SAFE_FREE(visit);
}

int BKE_pbvh_debug_draw_gen_get(PBVHNode *node)
{
  return node->debug_draw_gen;
}

void BKE_pbvh_sync_visibility_from_verts(PBVH *pbvh, Mesh *mesh)
{
  using namespace blender;
  using namespace blender::bke;
  switch (pbvh->header.type) {
    case PBVH_FACES: {
      BKE_mesh_flush_hidden_from_verts(mesh);
      break;
    }
    case PBVH_BMESH: {
      BMIter iter;
      BMVert *v;
      BMEdge *e;
      BMFace *f;

      BM_ITER_MESH (f, &iter, pbvh->header.bm, BM_FACES_OF_MESH) {
        BM_elem_flag_disable(f, BM_ELEM_HIDDEN);
      }

      BM_ITER_MESH (e, &iter, pbvh->header.bm, BM_EDGES_OF_MESH) {
        BM_elem_flag_disable(e, BM_ELEM_HIDDEN);
      }

      BM_ITER_MESH (v, &iter, pbvh->header.bm, BM_VERTS_OF_MESH) {
        if (!BM_elem_flag_test(v, BM_ELEM_HIDDEN)) {
          continue;
        }
        BMIter iter_l;
        BMLoop *l;

        BM_ITER_ELEM (l, &iter_l, v, BM_LOOPS_OF_VERT) {
          BM_elem_flag_enable(l->e, BM_ELEM_HIDDEN);
          BM_elem_flag_enable(l->f, BM_ELEM_HIDDEN);
        }
      }
      break;
    }
    case PBVH_GRIDS: {
      const OffsetIndices faces = mesh->faces();
      const BitGroupVector<> &grid_hidden = pbvh->subdiv_ccg->grid_hidden;
      CCGKey key = pbvh->gridkey;

      IndexMaskMemory memory;
      const IndexMask hidden_faces =
          grid_hidden.is_empty() ?
              IndexMask::from_predicate(faces.index_range(),
                                        GrainSize(1024),
                                        memory,
                                        [&](const int i) {
                                          const IndexRange face = faces[i];
                                          return std::any_of(
                                              face.begin(), face.end(), [&](const int corner) {
                                                return grid_hidden[corner][key.grid_area - 1];
                                              });
                                        }) :
              IndexMask();

      MutableAttributeAccessor attributes = mesh->attributes_for_write();
      if (hidden_faces.is_empty()) {
        attributes.remove(".hide_poly");
      }
      else {
        SpanAttributeWriter<bool> hide_poly = attributes.lookup_or_add_for_write_span<bool>(
            ".hide_poly", ATTR_DOMAIN_FACE, AttributeInitConstruct());
        hide_poly.span.fill(false);
        index_mask::masked_fill(hide_poly.span, true, hidden_faces);
        hide_poly.finish();
      }

      BKE_mesh_flush_hidden_from_faces(mesh);
      break;
    }
  }
}

namespace blender::bke::pbvh {
Vector<PBVHNode *> search_gather(PBVH *pbvh,
                                 const FunctionRef<bool(PBVHNode &)> scb,
                                 PBVHNodeFlags leaf_flag)
{
  if (pbvh->nodes.is_empty()) {
    return {};
  }

  PBVHIter iter;
  Vector<PBVHNode *> nodes;

  pbvh_iter_begin(&iter, pbvh, scb);

  PBVHNode *node;
  while ((node = pbvh_iter_next(&iter, leaf_flag))) {
    if (node->flag & leaf_flag) {
      nodes.append(node);
    }
  }

  pbvh_iter_end(&iter);
  return nodes;
}

Vector<PBVHNode *> gather_proxies(PBVH *pbvh)
{
  Vector<PBVHNode *> array;

  for (PBVHNode &node : pbvh->nodes) {
    if (!node.proxies.is_empty()) {
      array.append(&node);
    }
  }

  return array;
}
}  // namespace blender::bke::pbvh
