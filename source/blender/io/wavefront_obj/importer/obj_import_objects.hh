/* SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup obj
 */

#pragma once

#include "BKE_lib_id.h"

#include "BLI_math_vec_types.hh"
#include "BLI_vector.hh"
#include "BLI_vector_set.hh"

#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"

namespace blender::io::obj {

/**
 * List of all vertex and UV vertex coordinates in an OBJ file accessible to any
 * Geometry instance at any time.
 */
struct GlobalVertices {
  Vector<float3> vertices;
  Vector<float2> uv_vertices;
  Vector<float3> vertex_normals;
};

/**
 * Keeps track of the vertices that belong to other Geometries.
 * Needed only for MLoop.v and MEdge.v1 which needs vertex indices ranging from (0 to total
 * vertices in the mesh) as opposed to the other OBJ indices ranging from (0 to total vertices
 * in the global list).
 */
struct VertexIndexOffset {
 private:
  int offset_ = 0;

 public:
  void set_index_offset(const int64_t total_vertices)
  {
    offset_ = total_vertices;
  }
  int64_t get_index_offset() const
  {
    return offset_;
  }
};

/**
 * A face's corner in an OBJ file. In Blender, it translates to a mloop vertex.
 */
struct PolyCorner {
  /* These indices range from zero to total vertices in the OBJ file. */
  int vert_index;
  /* -1 is to indicate absence of UV vertices. Only < 0 condition should be checked since
   * it can be less than -1 too. */
  int uv_vert_index = -1;
  int vertex_normal_index = -1;
};

struct PolyElem {
  std::string vertex_group;
  std::string material_name;
  bool shaded_smooth = false;
  Vector<PolyCorner> face_corners;
};

/**
 * Contains data for one single NURBS curve in the OBJ file.
 */
struct NurbsElement {
  /**
   * For curves, groups may be used to specify multiple splines in the same curve object.
   * It may also serve as the name of the curve if not specified explicitly.
   */
  std::string group_;
  int degree = 0;
  /**
   * Indices into the global list of vertex coordinates. Must be non-negative.
   */
  Vector<int> curv_indices;
  /* Values in the parm u/v line in a curve definition. */
  Vector<float> parm;
};

enum eGeometryType {
  GEOM_MESH = OB_MESH,
  GEOM_CURVE = OB_CURVES_LEGACY,
};

struct Geometry {
  eGeometryType geom_type_ = GEOM_MESH;
  std::string geometry_name_;
  VectorSet<std::string> material_names_;
  /**
   * Indices in the vector range from zero to total vertices in a geometry.
   * Values range from zero to total coordinates in the global list.
   */
  Vector<int> vertex_indices_;
  /** Edges written in the file in addition to (or even without polygon) elements. */
  Vector<MEdge> edges_;
  Vector<PolyElem> face_elements_;
  bool has_vertex_normals_ = false;
  bool use_vertex_groups_ = false;
  NurbsElement nurbs_element_;
  int total_loops_ = 0;
};

}  // namespace blender::io::obj
