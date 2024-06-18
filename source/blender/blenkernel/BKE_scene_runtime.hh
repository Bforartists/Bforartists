/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "BLI_map.hh"
#include "BLI_timeit.hh"
#include "BLI_utility_mixins.hh"

struct Depsgraph;

namespace blender::bke {

/* Runtime data specific to the compositing trees. */
class CompositorRuntime {
 public:
  /* Per-node instance total execution time for the corresponding node, during the last tree
   * evaluation. */
  Map<bNodeInstanceKey, timeit::Nanoseconds> per_node_execution_time;

  /* A dependency graph used for interactive compositing. This is initialized the first time it is
   * needed, and then kept persistent for the lifetime of the scene. This is done to allow the
   * compositor to track changes to resources its uses as well as reduce the overhead of creating
   * the dependency graph every time it executes. */
  Depsgraph *preview_depsgraph = nullptr;

  ~CompositorRuntime();
};

class SceneRuntime : NonCopyable, NonMovable {
 public:
  CompositorRuntime compositor;
};

}  // namespace blender::bke
