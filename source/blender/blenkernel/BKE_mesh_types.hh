/* SPDX-FileCopyrightText: 2020 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup bke
 */

#include <mutex>

#include "BLI_array.hh"
#include "BLI_bit_vector.hh"
#include "BLI_bounds_types.hh"
#include "BLI_implicit_sharing.hh"
#include "BLI_math_vector_types.hh"
#include "BLI_shared_cache.hh"
#include "BLI_vector.hh"

#include "DNA_customdata_types.h"
#include "DNA_meshdata_types.h"

struct BVHCache;
struct Mesh;
struct MLoopTri;
struct ShrinkwrapBoundaryData;
struct SubdivCCG;
struct SubsurfRuntimeData;
namespace blender::bke {
struct EditMeshData;
}

/** #MeshRuntime.wrapper_type */
enum eMeshWrapperType {
  /** Use mesh data (#Mesh.vert_positions(), #Mesh.medge, #Mesh.corner_verts(), #Mesh.faces()). */
  ME_WRAPPER_TYPE_MDATA = 0,
  /** Use edit-mesh data (#Mesh.edit_mesh, #MeshRuntime.edit_data). */
  ME_WRAPPER_TYPE_BMESH = 1,
  /** Use subdivision mesh data (#MeshRuntime.mesh_eval). */
  ME_WRAPPER_TYPE_SUBD = 2,
};

namespace blender::bke {

/**
 * The complexity requirement of attribute domains needed to process normals.
 * See #Mesh::normals_domain().
 */
enum class MeshNormalDomain : int8_t {
  /**
   * The mesh is completely smooth shaded; either all faces or edges are sharp.
   * Only #Mesh::face_normals() is necessary. This case is generally the best
   * for performance, since no mixing is necessary and multithreading is simple.
   */
  Face,
  /**
   * The mesh is completely smooth shaded; there are no sharp face or edges. Only
   * #Mesh::vert_normals() is necessary. Calculating face normals is still necessary though,
   * since they have to be mixed to become vertex normals.
   */
  Point,
  /**
   * The mesh has mixed smooth and sharp shading. In order to split the normals on each side of
   * sharp edges, they need to be processed per-face-corner. Normals can be retrieved with
   * #Mesh::corner_normals().
   */
  Corner,
};

/**
 * Cache of a mesh's loose edges, accessed with #Mesh::loose_edges(). *
 */
struct LooseGeomCache {
  /**
   * A bitmap set to true for each loose element, false if the element is used by any face.
   * Allocated only if there is at least one loose element.
   */
  blender::BitVector<> is_loose_bits;
  /**
   * The number of loose elements. If zero, the #is_loose_bits shouldn't be accessed.
   * If less than zero, the cache has been accessed in an invalid way
   * (i.e.directly instead of through #Mesh::loose_edges()).
   */
  int count = -1;
};

struct LooseEdgeCache : public LooseGeomCache {
};
struct LooseVertCache : public LooseGeomCache {
};

struct MeshRuntime {
  /* Evaluated mesh for objects which do not have effective modifiers.
   * This mesh is used as a result of modifier stack evaluation.
   * Since modifier stack evaluation is threaded on object level we need some synchronization. */
  Mesh *mesh_eval = nullptr;
  std::mutex eval_mutex;

  /** Needed to ensure some thread-safety during render data pre-processing. */
  std::mutex render_mutex;

  /** Implicit sharing user count for #Mesh::face_offset_indices. */
  const ImplicitSharingInfo *face_offsets_sharing_info;

  /**
   * A cache of bounds shared between data-blocks with unchanged positions. When changing positions
   * affect the bounds, the cache is "un-shared" with other geometries. See #SharedCache comments.
   */
  SharedCache<Bounds<float3>> bounds_cache;

  /** Lazily initialized SoA data from the #edit_mesh field in #Mesh. */
  EditMeshData *edit_data = nullptr;

  /**
   * Data used to efficiently draw the mesh in the viewport, especially useful when
   * the same mesh is used in many objects or instances. See `draw_cache_impl_mesh.cc`.
   */
  void *batch_cache = nullptr;

  /** Cache for derived triangulation of the mesh, accessed with #Mesh::looptris(). */
  SharedCache<Array<MLoopTri>> looptris_cache;
  /** Cache for triangle to original face index map, accessed with #Mesh::looptri_faces(). */
  SharedCache<Array<int>> looptri_faces_cache;

  /** Cache for BVH trees generated for the mesh. Defined in 'BKE_bvhutil.c' */
  BVHCache *bvh_cache = nullptr;

  /** Cache of non-manifold boundary data for Shrink-wrap Target Project. */
  ShrinkwrapBoundaryData *shrinkwrap_data = nullptr;

  /** Needed in case we need to lazily initialize the mesh. */
  CustomData_MeshMasks cd_mask_extra = {};

  SubdivCCG *subdiv_ccg = nullptr;
  int subdiv_ccg_tot_level = 0;

  /** Set by modifier stack if only deformed from original. */
  bool deformed_only = false;
  /**
   * Copied from edit-mesh (hint, draw with edit-mesh data when true).
   *
   * Modifiers that edit the mesh data in-place must set this to false
   * (most #eModifierTypeType_NonGeometrical modifiers). Otherwise the edit-mesh
   * data will be used for drawing, missing changes from modifiers. See #79517.
   */
  bool is_original_bmesh = false;

  /** #eMeshWrapperType and others. */
  eMeshWrapperType wrapper_type = ME_WRAPPER_TYPE_MDATA;
  /**
   * A type mask from wrapper_type,
   * in case there are differences in finalizing logic between types.
   */
  eMeshWrapperType wrapper_type_finalize = ME_WRAPPER_TYPE_MDATA;

  /**
   * Settings for lazily evaluating the subdivision on the CPU if needed. These are
   * set in the modifier when GPU subdivision can be performed, and owned by the by
   * the modifier in the object.
   */
  SubsurfRuntimeData *subsurf_runtime_data = nullptr;

  /** Caches for lazily computed normals. */
  SharedCache<Vector<float3>> vert_normals_cache;
  SharedCache<Vector<float3>> face_normals_cache;
  SharedCache<Vector<float3>> corner_normals_cache;

  /**
   * Cache of offsets for vert to face/corner maps. The same offsets array is used to group
   * indices for both the vertex to face and vertex to corner maps.
   */
  SharedCache<Array<int>> vert_to_face_offset_cache;
  /** Cache of indices for vert to face map. */
  SharedCache<Array<int>> vert_to_face_map_cache;
  /** Cache of indices for vert to corner map. */
  SharedCache<Array<int>> vert_to_corner_map_cache;
  /** Cache of face indices for each face corner. */
  SharedCache<Array<int>> corner_to_face_map_cache;
  /** Cache of data about edges not used by faces. See #Mesh::loose_edges(). */
  SharedCache<LooseEdgeCache> loose_edges_cache;
  /** Cache of data about vertices not used by edges. See #Mesh::loose_verts(). */
  SharedCache<LooseVertCache> loose_verts_cache;
  /** Cache of data about vertices not used by faces. See #Mesh::verts_no_face(). */
  SharedCache<LooseVertCache> verts_no_face_cache;

  /**
   * A bit vector the size of the number of vertices, set to true for the center vertices of
   * subdivided faces. The values are set by the subdivision surface modifier and used by
   * drawing code instead of face center face dots. Otherwise this will be empty.
   */
  BitVector<> subsurf_face_dot_tags;

  /**
   * A bit vector the size of the number of edges, set to true for edges that should be drawn in
   * the viewport. Created by the "Optimal Display" feature of the subdivision surface modifier.
   * Otherwise it will be empty.
   */
  BitVector<> subsurf_optimal_display_edges;

  MeshRuntime() = default;
  ~MeshRuntime();

  MEM_CXX_CLASS_ALLOC_FUNCS("MeshRuntime")
};

}  // namespace blender::bke
