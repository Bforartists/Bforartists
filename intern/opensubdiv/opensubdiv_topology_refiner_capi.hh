/* SPDX-FileCopyrightText: 2018 Blender Foundation
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include <cstdint>  // for bool

#include "opensubdiv_capi_type.hh"

struct OpenSubdiv_Converter;
struct OpenSubdiv_TopologyRefinerImpl;

// Those settings don't really belong to OpenSubdiv's topology refiner, but
// we are keeping track of them on our side of topology refiner. This is to
// make it possible to ensure we are not trying to abuse same OpenSubdiv's
// topology refiner with different subdivision levels or with different
// adaptive settings.
struct OpenSubdiv_TopologyRefinerSettings {
  bool is_adaptive;
  int level;
};

// C-style wrapper around actual topology refiner.
//
// The only purpose is to allow C-only code to access C++ implementation of the
// topology refiner.
struct OpenSubdiv_TopologyRefiner {
  // Query subdivision level the refiner is created for.
  int (*getSubdivisionLevel)(const OpenSubdiv_TopologyRefiner *topology_refiner);
  bool (*getIsAdaptive)(const OpenSubdiv_TopologyRefiner *topology_refiner);

  // NOTE: All queries are querying base level.
  //
  // TODO(sergey): Consider making it more obvious in function naming,
  // but since it's unlikely (or at least, will be uncommon use) for API
  // which queries final geometry, we should be fine with this name for
  // now.

  //////////////////////////////////////////////////////////////////////////////
  // Query basic topology information from base level.

  int (*getNumVertices)(const OpenSubdiv_TopologyRefiner *topology_refiner);
  int (*getNumEdges)(const OpenSubdiv_TopologyRefiner *topology_refiner);
  int (*getNumFaces)(const OpenSubdiv_TopologyRefiner *topology_refiner);

  int (*getNumFaceVertices)(const OpenSubdiv_TopologyRefiner *topology_refiner,
                            const int face_index);
  void (*getFaceVertices)(const OpenSubdiv_TopologyRefiner *topology_refiner,
                          const int face_index,
                          int *face_vertices_indices);

  int (*getNumFaceEdges)(const OpenSubdiv_TopologyRefiner *topology_refiner, const int face_index);
  void (*getFaceEdges)(const OpenSubdiv_TopologyRefiner *topology_refiner,
                       const int face_index,
                       int *face_edges_indices);
  void (*getEdgeVertices)(const OpenSubdiv_TopologyRefiner *topology_refiner,
                          const int edge_index,
                          int edge_vertices_indices[2]);

  int (*getNumVertexEdges)(const OpenSubdiv_TopologyRefiner *topology_refiner,
                           const int vertex_index);
  void (*getVertexEdges)(const OpenSubdiv_TopologyRefiner *topology_refiner,
                         const int vertex_index,
                         int *vertex_edges_indices);

  //////////////////////////////////////////////////////////////////////////////
  // PTex face geometry queries.

  // Ptex face corresponds to OpenSubdiv's internal "patch" and to Blender's
  // subdivision grid. The rule commes as:
  // - Triangle face consist of 3 ptex faces, ordered in the order of
  //   face-vertices.
  // - Quad face consists of a single ptex face.
  // - N-gons (similar to triangle) consists of N ptex faces, ordered same
  //   way as for triangle.
  int (*getNumFacePtexFaces)(const OpenSubdiv_TopologyRefiner *topology_refiner,
                             const int face_index);
  int (*getNumPtexFaces)(const OpenSubdiv_TopologyRefiner *topology_refiner);

  // Initialize a per-base-face offset measured in ptex face indices.
  //
  // Basically, face_ptex_offset[base_face_index] is a total number of ptex
  // faces created for bases faces [0 .. base_face_index - 1].
  //
  // The array must contain at least total number of ptex faces elements.
  void (*fillFacePtexIndexOffset)(const OpenSubdiv_TopologyRefiner *topology_refiner,
                                  int *face_ptex_index_offset);

  //////////////////////////////////////////////////////////////////////////////
  // Face-varying data.

  // Number of face-varying channels (or how they are called in Blender layers).
  int (*getNumFVarChannels)(const OpenSubdiv_TopologyRefiner *topology_refiner);
  // Get face-varying interpolation type.
  OpenSubdiv_FVarLinearInterpolation (*getFVarLinearInterpolation)(
      const OpenSubdiv_TopologyRefiner *topology_refiner);
  // Get total number of face-varying values in a particular channel.
  int (*getNumFVarValues)(const OpenSubdiv_TopologyRefiner *topology_refiner, const int channel);
  // Get face-varying value indices associated with a particular face.
  //
  // This is an array of indices inside of face-varying array, array elements
  // are aligned with face corners (or loops in Blender terminology).
  const int *(*getFaceFVarValueIndices)(const OpenSubdiv_TopologyRefiner *topology_refiner,
                                        const int face_index,
                                        const int channel);

  //////////////////////////////////////////////////////////////////////////////
  // Internal use.

  // Implementation of the topology refiner.
  OpenSubdiv_TopologyRefinerImpl *impl;
};

// NOTE: Will return NULL in cases of bad topology.
// NOTE: Mesh without faces is considered a bad topology.
OpenSubdiv_TopologyRefiner *openSubdiv_createTopologyRefinerFromConverter(
    OpenSubdiv_Converter *converter, const OpenSubdiv_TopologyRefinerSettings *settings);

void openSubdiv_deleteTopologyRefiner(OpenSubdiv_TopologyRefiner *topology_refiner);

// Compare given topology refiner with converter. Returns truth if topology
// refiner matches given converter, false otherwise.
//
// This allows users to construct converter (which is supposed to be cheap)
// and compare with existing refiner before going into more computationally
// complicated parts of subdivision process.
bool openSubdiv_topologyRefinerCompareWithConverter(
    const OpenSubdiv_TopologyRefiner *topology_refiner, const OpenSubdiv_Converter *converter);
