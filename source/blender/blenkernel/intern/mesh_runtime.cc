/* SPDX-FileCopyrightText: 2005 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 */

#include "atomic_ops.h"

#include "MEM_guardedalloc.h"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"

#include "BLI_array_utils.hh"
#include "BLI_math_geom.h"
#include "BLI_task.hh"
#include "BLI_timeit.hh"

#include "BKE_bvhutils.h"
#include "BKE_editmesh_cache.hh"
#include "BKE_lib_id.h"
#include "BKE_mesh.hh"
#include "BKE_mesh_mapping.hh"
#include "BKE_mesh_runtime.hh"
#include "BKE_shrinkwrap.h"
#include "BKE_subdiv_ccg.hh"

using blender::float3;
using blender::MutableSpan;
using blender::Span;

/* -------------------------------------------------------------------- */
/** \name Mesh Runtime Struct Utils
 * \{ */

namespace blender::bke {

static void free_mesh_eval(MeshRuntime &mesh_runtime)
{
  if (mesh_runtime.mesh_eval != nullptr) {
    mesh_runtime.mesh_eval->edit_mesh = nullptr;
    BKE_id_free(nullptr, mesh_runtime.mesh_eval);
    mesh_runtime.mesh_eval = nullptr;
  }
}

static void free_subdiv_ccg(MeshRuntime &mesh_runtime)
{
  /* TODO(sergey): Does this really belong here? */
  if (mesh_runtime.subdiv_ccg != nullptr) {
    BKE_subdiv_ccg_destroy(mesh_runtime.subdiv_ccg);
    mesh_runtime.subdiv_ccg = nullptr;
  }
}

static void free_bvh_cache(MeshRuntime &mesh_runtime)
{
  if (mesh_runtime.bvh_cache) {
    bvhcache_free(mesh_runtime.bvh_cache);
    mesh_runtime.bvh_cache = nullptr;
  }
}

static void free_batch_cache(MeshRuntime &mesh_runtime)
{
  if (mesh_runtime.batch_cache) {
    BKE_mesh_batch_cache_free(mesh_runtime.batch_cache);
    mesh_runtime.batch_cache = nullptr;
  }
}

MeshRuntime::~MeshRuntime()
{
  free_mesh_eval(*this);
  free_subdiv_ccg(*this);
  free_bvh_cache(*this);
  free_batch_cache(*this);
  if (this->shrinkwrap_data) {
    BKE_shrinkwrap_boundary_data_free(this->shrinkwrap_data);
  }
}

static int reset_bits_and_count(MutableBitSpan bits, const Span<int> indices_to_reset)
{
  int count = bits.size();
  for (const int vert : indices_to_reset) {
    if (bits[vert]) {
      bits[vert].reset();
      count--;
    }
  }
  return count;
}

static void bit_vector_with_reset_bits_or_empty(const Span<int> indices_to_reset,
                                                const int indexed_elems_num,
                                                BitVector<> &r_bits,
                                                int &r_count)
{
  r_bits.resize(0);
  r_bits.resize(indexed_elems_num, true);
  r_count = reset_bits_and_count(r_bits, indices_to_reset);
  if (r_count == 0) {
    r_bits.clear_and_shrink();
  }
}

/**
 * If there are no loose edges and no loose vertices, all vertices are used by faces.
 */
static void try_tag_verts_no_face_none(const Mesh &mesh)
{
  if (!mesh.runtime->loose_edges_cache.is_cached() || mesh.loose_edges().count > 0) {
    return;
  }
  if (!mesh.runtime->loose_verts_cache.is_cached() || mesh.loose_verts().count > 0) {
    return;
  }
  mesh.runtime->verts_no_face_cache.ensure([&](LooseVertCache &r_data) {
    r_data.is_loose_bits.clear_and_shrink();
    r_data.count = 0;
  });
}

}  // namespace blender::bke

blender::Span<int> Mesh::corner_to_face_map() const
{
  using namespace blender;
  this->runtime->corner_to_face_map_cache.ensure([&](Array<int> &r_data) {
    const OffsetIndices faces = this->faces();
    r_data = bke::mesh::build_loop_to_face_map(faces);
  });
  return this->runtime->corner_to_face_map_cache.data();
}

blender::OffsetIndices<int> Mesh::vert_to_face_map_offsets() const
{
  using namespace blender;
  this->runtime->vert_to_face_offset_cache.ensure([&](Array<int> &r_data) {
    r_data = Array<int>(this->totvert + 1, 0);
    offset_indices::build_reverse_offsets(this->corner_verts(), r_data);
  });
  return OffsetIndices<int>(this->runtime->vert_to_face_offset_cache.data());
}

blender::GroupedSpan<int> Mesh::vert_to_face_map() const
{
  using namespace blender;
  const OffsetIndices offsets = this->vert_to_face_map_offsets();
  this->runtime->vert_to_face_map_cache.ensure([&](Array<int> &r_data) {
    r_data.reinitialize(this->totloop);
    if (this->runtime->vert_to_corner_map_cache.is_cached() &&
        this->runtime->corner_to_face_map_cache.is_cached())
    {
      /* The vertex to face cache can be built from the vertex to face corner
       * and face corner to face maps if they are both already cached. */
      array_utils::gather(this->runtime->corner_to_face_map_cache.data().as_span(),
                          this->runtime->vert_to_corner_map_cache.data().as_span(),
                          r_data.as_mutable_span());
    }
    else {
      bke::mesh::build_vert_to_face_indices(this->faces(), this->corner_verts(), offsets, r_data);
    }
  });
  return {offsets, this->runtime->vert_to_face_map_cache.data()};
}

blender::GroupedSpan<int> Mesh::vert_to_corner_map() const
{
  using namespace blender;
  const OffsetIndices offsets = this->vert_to_face_map_offsets();
  this->runtime->vert_to_corner_map_cache.ensure([&](Array<int> &r_data) {
    r_data = bke::mesh::build_vert_to_corner_indices(this->corner_verts(), offsets);
  });
  return {offsets, this->runtime->vert_to_corner_map_cache.data()};
}

const blender::bke::LooseVertCache &Mesh::loose_verts() const
{
  using namespace blender::bke;
  this->runtime->loose_verts_cache.ensure([&](LooseVertCache &r_data) {
    const Span<int> verts = this->edges().cast<int>();
    bit_vector_with_reset_bits_or_empty(verts, this->totvert, r_data.is_loose_bits, r_data.count);
  });
  return this->runtime->loose_verts_cache.data();
}

const blender::bke::LooseVertCache &Mesh::verts_no_face() const
{
  using namespace blender::bke;
  this->runtime->verts_no_face_cache.ensure([&](LooseVertCache &r_data) {
    const Span<int> verts = this->corner_verts();
    bit_vector_with_reset_bits_or_empty(verts, this->totvert, r_data.is_loose_bits, r_data.count);
  });
  return this->runtime->verts_no_face_cache.data();
}

const blender::bke::LooseEdgeCache &Mesh::loose_edges() const
{
  using namespace blender::bke;
  this->runtime->loose_edges_cache.ensure([&](LooseEdgeCache &r_data) {
    const Span<int> edges = this->corner_edges();
    bit_vector_with_reset_bits_or_empty(edges, this->totedge, r_data.is_loose_bits, r_data.count);
  });
  return this->runtime->loose_edges_cache.data();
}

void Mesh::tag_loose_verts_none() const
{
  using namespace blender::bke;
  this->runtime->loose_verts_cache.ensure([&](LooseVertCache &r_data) {
    r_data.is_loose_bits.clear_and_shrink();
    r_data.count = 0;
  });
  try_tag_verts_no_face_none(*this);
}

void Mesh::tag_loose_edges_none() const
{
  using namespace blender::bke;
  this->runtime->loose_edges_cache.ensure([&](LooseEdgeCache &r_data) {
    r_data.is_loose_bits.clear_and_shrink();
    r_data.count = 0;
  });
  try_tag_verts_no_face_none(*this);
}

blender::Span<MLoopTri> Mesh::looptris() const
{
  this->runtime->looptris_cache.ensure([&](blender::Array<MLoopTri> &r_data) {
    const Span<float3> positions = this->vert_positions();
    const blender::OffsetIndices faces = this->faces();
    const Span<int> corner_verts = this->corner_verts();

    r_data.reinitialize(poly_to_tri_count(faces.size(), corner_verts.size()));

    if (BKE_mesh_face_normals_are_dirty(this)) {
      blender::bke::mesh::looptris_calc(positions, faces, corner_verts, r_data);
    }
    else {
      blender::bke::mesh::looptris_calc_with_normals(
          positions, faces, corner_verts, this->face_normals(), r_data);
    }
  });

  return this->runtime->looptris_cache.data();
}

blender::Span<int> Mesh::looptri_faces() const
{
  using namespace blender;
  this->runtime->looptri_faces_cache.ensure([&](blender::Array<int> &r_data) {
    const OffsetIndices faces = this->faces();
    r_data.reinitialize(poly_to_tri_count(faces.size(), this->totloop));
    bke::mesh::looptris_calc_face_indices(faces, r_data);
  });
  return this->runtime->looptri_faces_cache.data();
}

int BKE_mesh_runtime_looptri_len(const Mesh *mesh)
{
  /* Allow returning the size without calculating the cache. */
  return poly_to_tri_count(mesh->faces_num, mesh->totloop);
}

void BKE_mesh_runtime_verttri_from_looptri(MVertTri *r_verttri,
                                           const int *corner_verts,
                                           const MLoopTri *looptri,
                                           int looptri_num)
{
  for (int i = 0; i < looptri_num; i++) {
    r_verttri[i].tri[0] = corner_verts[looptri[i].tri[0]];
    r_verttri[i].tri[1] = corner_verts[looptri[i].tri[1]];
    r_verttri[i].tri[2] = corner_verts[looptri[i].tri[2]];
  }
}

bool BKE_mesh_runtime_ensure_edit_data(Mesh *mesh)
{
  if (mesh->runtime->edit_data != nullptr) {
    return false;
  }
  mesh->runtime->edit_data = MEM_new<blender::bke::EditMeshData>(__func__);
  return true;
}

void BKE_mesh_runtime_clear_cache(Mesh *mesh)
{
  using namespace blender::bke;
  free_mesh_eval(*mesh->runtime);
  free_batch_cache(*mesh->runtime);
  MEM_delete(mesh->runtime->edit_data);
  mesh->runtime->edit_data = nullptr;
  BKE_mesh_runtime_clear_geometry(mesh);
}

void BKE_mesh_runtime_clear_geometry(Mesh *mesh)
{
  /* Tagging shared caches dirty will free the allocated data if there is only one user. */
  free_bvh_cache(*mesh->runtime);
  free_subdiv_ccg(*mesh->runtime);
  mesh->runtime->bounds_cache.tag_dirty();
  mesh->runtime->vert_to_face_offset_cache.tag_dirty();
  mesh->runtime->vert_to_face_map_cache.tag_dirty();
  mesh->runtime->vert_to_corner_map_cache.tag_dirty();
  mesh->runtime->corner_to_face_map_cache.tag_dirty();
  mesh->runtime->vert_normals_cache.tag_dirty();
  mesh->runtime->face_normals_cache.tag_dirty();
  mesh->runtime->loose_edges_cache.tag_dirty();
  mesh->runtime->loose_verts_cache.tag_dirty();
  mesh->runtime->verts_no_face_cache.tag_dirty();
  mesh->runtime->looptris_cache.tag_dirty();
  mesh->runtime->looptri_faces_cache.tag_dirty();
  mesh->runtime->subsurf_face_dot_tags.clear_and_shrink();
  mesh->runtime->subsurf_optimal_display_edges.clear_and_shrink();
  if (mesh->runtime->shrinkwrap_data) {
    BKE_shrinkwrap_boundary_data_free(mesh->runtime->shrinkwrap_data);
    mesh->runtime->shrinkwrap_data = nullptr;
  }
}

void BKE_mesh_tag_edges_split(Mesh *mesh)
{
  /* Triangulation didn't change because vertex positions and loop vertex indices didn't change. */
  free_bvh_cache(*mesh->runtime);
  mesh->runtime->vert_normals_cache.tag_dirty();
  free_subdiv_ccg(*mesh->runtime);
  mesh->runtime->vert_to_face_offset_cache.tag_dirty();
  mesh->runtime->vert_to_face_map_cache.tag_dirty();
  mesh->runtime->vert_to_corner_map_cache.tag_dirty();
  if (mesh->runtime->loose_edges_cache.is_cached() &&
      mesh->runtime->loose_edges_cache.data().count != 0)
  {
    mesh->runtime->loose_edges_cache.tag_dirty();
  }
  if (mesh->runtime->loose_verts_cache.is_cached() &&
      mesh->runtime->loose_verts_cache.data().count != 0)
  {
    mesh->runtime->loose_verts_cache.tag_dirty();
  }
  if (mesh->runtime->verts_no_face_cache.is_cached() &&
      mesh->runtime->verts_no_face_cache.data().count != 0)
  {
    mesh->runtime->verts_no_face_cache.tag_dirty();
  }
  mesh->runtime->subsurf_face_dot_tags.clear_and_shrink();
  mesh->runtime->subsurf_optimal_display_edges.clear_and_shrink();
  if (mesh->runtime->shrinkwrap_data) {
    BKE_shrinkwrap_boundary_data_free(mesh->runtime->shrinkwrap_data);
    mesh->runtime->shrinkwrap_data = nullptr;
  }
}

void BKE_mesh_tag_sharpness_changed(Mesh *mesh)
{
  mesh->runtime->corner_normals_cache.tag_dirty();
}

void BKE_mesh_tag_face_winding_changed(Mesh *mesh)
{
  mesh->runtime->vert_normals_cache.tag_dirty();
  mesh->runtime->face_normals_cache.tag_dirty();
  mesh->runtime->corner_normals_cache.tag_dirty();
  mesh->runtime->vert_to_corner_map_cache.tag_dirty();
}

void BKE_mesh_tag_positions_changed(Mesh *mesh)
{
  mesh->runtime->vert_normals_cache.tag_dirty();
  mesh->runtime->face_normals_cache.tag_dirty();
  mesh->runtime->corner_normals_cache.tag_dirty();
  BKE_mesh_tag_positions_changed_no_normals(mesh);
}

void BKE_mesh_tag_positions_changed_no_normals(Mesh *mesh)
{
  free_bvh_cache(*mesh->runtime);
  mesh->runtime->looptris_cache.tag_dirty();
  mesh->runtime->bounds_cache.tag_dirty();
}

void BKE_mesh_tag_positions_changed_uniformly(Mesh *mesh)
{
  /* The normals and triangulation didn't change, since all verts moved by the same amount. */
  free_bvh_cache(*mesh->runtime);
  mesh->runtime->bounds_cache.tag_dirty();
}

void BKE_mesh_tag_topology_changed(Mesh *mesh)
{
  BKE_mesh_runtime_clear_geometry(mesh);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Mesh Batch Cache Callbacks
 * \{ */

/* Draw Engine */

void (*BKE_mesh_batch_cache_dirty_tag_cb)(Mesh *me, eMeshBatchDirtyMode mode) = nullptr;
void (*BKE_mesh_batch_cache_free_cb)(void *batch_cache) = nullptr;

void BKE_mesh_batch_cache_dirty_tag(Mesh *me, eMeshBatchDirtyMode mode)
{
  if (me->runtime->batch_cache) {
    BKE_mesh_batch_cache_dirty_tag_cb(me, mode);
  }
}
void BKE_mesh_batch_cache_free(void *batch_cache)
{
  BKE_mesh_batch_cache_free_cb(batch_cache);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Mesh Runtime Validation
 * \{ */

#ifndef NDEBUG

bool BKE_mesh_runtime_is_valid(Mesh *me_eval)
{
  const bool do_verbose = true;
  const bool do_fixes = false;

  bool is_valid = true;
  bool changed = true;

  if (do_verbose) {
    printf("MESH: %s\n", me_eval->id.name + 2);
  }

  MutableSpan<float3> positions = me_eval->vert_positions_for_write();
  MutableSpan<blender::int2> edges = me_eval->edges_for_write();
  MutableSpan<int> face_offsets = me_eval->face_offsets_for_write();
  MutableSpan<int> corner_verts = me_eval->corner_verts_for_write();
  MutableSpan<int> corner_edges = me_eval->corner_edges_for_write();

  is_valid &= BKE_mesh_validate_all_customdata(
      &me_eval->vert_data,
      me_eval->totvert,
      &me_eval->edge_data,
      me_eval->totedge,
      &me_eval->loop_data,
      me_eval->totloop,
      &me_eval->face_data,
      me_eval->faces_num,
      false, /* setting mask here isn't useful, gives false positives */
      do_verbose,
      do_fixes,
      &changed);

  is_valid &= BKE_mesh_validate_arrays(
      me_eval,
      reinterpret_cast<float(*)[3]>(positions.data()),
      positions.size(),
      edges.data(),
      edges.size(),
      static_cast<MFace *>(CustomData_get_layer_for_write(
          &me_eval->fdata_legacy, CD_MFACE, me_eval->totface_legacy)),
      me_eval->totface_legacy,
      corner_verts.data(),
      corner_edges.data(),
      corner_verts.size(),
      face_offsets.data(),
      me_eval->faces_num,
      me_eval->deform_verts_for_write().data(),
      do_verbose,
      do_fixes,
      &changed);

  BLI_assert(changed == false);

  return is_valid;
}

#endif /* NDEBUG */

/** \} */
