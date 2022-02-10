/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2016 Blender Foundation. All rights reserved. */

/** \file
 * \ingroup depsgraph
 */

#pragma once

struct Base;
struct ID;
struct Main;
struct Object;
struct bPoseChannel;

namespace blender {
namespace deg {

struct Depsgraph;
class DepsgraphBuilderCache;

class DepsgraphBuilder {
 public:
  virtual ~DepsgraphBuilder() = default;

  virtual bool need_pull_base_into_graph(Base *base);

  virtual bool check_pchan_has_bbone(Object *object, const bPoseChannel *pchan);
  virtual bool check_pchan_has_bbone_segments(Object *object, const bPoseChannel *pchan);
  virtual bool check_pchan_has_bbone_segments(Object *object, const char *bone_name);

 protected:
  /* NOTE: The builder does NOT take ownership over any of those resources. */
  DepsgraphBuilder(Main *bmain, Depsgraph *graph, DepsgraphBuilderCache *cache);

  /* State which never changes, same for the whole builder time. */
  Main *bmain_;
  Depsgraph *graph_;
  DepsgraphBuilderCache *cache_;
};

bool deg_check_id_in_depsgraph(const Depsgraph *graph, ID *id_orig);
bool deg_check_base_in_depsgraph(const Depsgraph *graph, Base *base);
void deg_graph_build_finalize(Main *bmain, Depsgraph *graph);

}  // namespace deg
}  // namespace blender
