/* SPDX-FileCopyrightText: 2021 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup eevee
 *
 * World rendering with material handling. Also take care of lookdev
 * HDRI and default material.
 */

#pragma once

#include "DNA_world_types.h"

namespace blender::eevee {

class Instance;

/* -------------------------------------------------------------------- */
/** \name Default World Node-Tree
 *
 * In order to support worlds without node-tree we reuse and configure a standalone node-tree that
 * we pass for shader generation. The GPUMaterial is still stored inside the World even if
 * it does not use a node-tree.
 * \{ */

class DefaultWorldNodeTree {
 private:
  bNodeTree *ntree_;
  bNodeSocketValueRGBA *color_socket_;

 public:
  DefaultWorldNodeTree();
  ~DefaultWorldNodeTree();

  bNodeTree *nodetree_get(::World *world);
};

/** \} */

/* -------------------------------------------------------------------- */
/** \name World
 *
 * \{ */

class World {
 private:
  Instance &inst_;

  DefaultWorldNodeTree default_tree;

  /* Used to detect if world change. */
  ::World *prev_original_world = nullptr;

  /* Used when the scene doesn't have a world. */
  ::World *default_world_ = nullptr;

  ::World *default_world_get();

  void world_and_ntree_get(::World *&world, bNodeTree *&ntree);

 public:
  World(Instance &inst) : inst_(inst){};
  ~World();

  void sync();

  bool has_volume();
};

/** \} */

}  // namespace blender::eevee
