/*
 * Adapted from code copyright 2009-2010 NVIDIA Corporation
 * Modifications Copyright 2011, Blender Foundation.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef __BVH_H__
#define __BVH_H__

#include "bvh/bvh_params.h"
#include "util/util_array.h"
#include "util/util_types.h"
#include "util/util_vector.h"

CCL_NAMESPACE_BEGIN

class BoundBox;
class BVHNode;
class BVHParams;
class Device;
class DeviceScene;
class Geometry;
class LeafNode;
class Object;
class Progress;
class Stats;

#define BVH_ALIGN 4096
#define TRI_NODE_SIZE 3
/* Packed BVH
 *
 * BVH stored as it will be used for traversal on the rendering device. */

struct PackedBVH {
  /* BVH nodes storage, one node is 4x int4, and contains two bounding boxes,
   * and child, triangle or object indexes depending on the node type */
  array<int4> nodes;
  /* BVH leaf nodes storage. */
  array<int4> leaf_nodes;
  /* object index to BVH node index mapping for instances */
  array<int> object_node;
  /* Mapping from primitive index to index in triangle array. */
  array<uint> prim_tri_index;
  /* Continuous storage of triangle vertices. */
  array<float4> prim_tri_verts;
  /* primitive type - triangle or strand */
  array<int> prim_type;
  /* visibility visibilitys for primitives */
  array<uint> prim_visibility;
  /* mapping from BVH primitive index to true primitive index, as primitives
   * may be duplicated due to spatial splits. -1 for instances. */
  array<int> prim_index;
  /* mapping from BVH primitive index, to the object id of that primitive. */
  array<int> prim_object;
  /* Time range of BVH primitive. */
  array<float2> prim_time;

  /* index of the root node. */
  int root_index;

  PackedBVH()
  {
    root_index = 0;
  }
};

/* BVH */

class BVH {
 public:
  BVHParams params;
  vector<Geometry *> geometry;
  vector<Object *> objects;

  static BVH *create(const BVHParams &params,
                     const vector<Geometry *> &geometry,
                     const vector<Object *> &objects,
                     Device *device);
  virtual ~BVH()
  {
  }

 protected:
  BVH(const BVHParams &params,
      const vector<Geometry *> &geometry,
      const vector<Object *> &objects);
};

CCL_NAMESPACE_END

#endif /* __BVH_H__ */
