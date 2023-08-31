/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "BKE_bake_items_paths.hh"
#include "BKE_bake_items_serialize.hh"
#include "BKE_geometry_set.hh"

#include "BLI_map.hh"
#include "BLI_sub_frame.hh"

struct bNodeTree;
struct NodesModifierData;
struct Main;

namespace blender::bke::sim {

enum class CacheState {
  /** The cache is up-to-date with the inputs. */
  Valid,
  /**
   * Nodes or input values have changed since the cache was created, i.e. the output would be
   * different if the simulation was run again.
   */
  Invalid,
  /** The cache has been baked and will not be invalidated by changing inputs. */
  Baked,
};

struct SimulationZoneFrameCache {
  SubFrame frame;
  Map<int, std::unique_ptr<BakeItem>> items;
  /** Used when the baked data is loaded lazily. */
  std::optional<std::string> meta_path;
};

struct SimulationZonePrevState {
  Map<int, std::unique_ptr<BakeItem>> items;
  SubFrame frame;
};

struct SimulationZoneCache {
  Vector<std::unique_ptr<SimulationZoneFrameCache>> frame_caches;
  std::optional<SimulationZonePrevState> prev_state;

  std::optional<std::string> bdata_dir;
  std::unique_ptr<BDataSharing> bdata_sharing;
  bool failed_finding_bake = false;
  CacheState cache_state = CacheState::Valid;

  void reset();
};

class ModifierSimulationCache {
 public:
  mutable std::mutex mutex;
  Map<int, std::unique_ptr<SimulationZoneCache>> cache_by_zone_id;
};

/**
 * Reset all simulation caches in the scene, for use when some fundamental change made them
 * impossible to reuse.
 */
void scene_simulation_states_reset(Scene &scene);

std::optional<bake_paths::BakePath> get_simulation_zone_bake_path(const Main &bmain,
                                                                  const Object &object,
                                                                  const NodesModifierData &nmd,
                                                                  int zone_id);
std::optional<std::string> get_modifier_simulation_bake_path(const Main &bmain,
                                                             const Object &object,
                                                             const NodesModifierData &nmd);

}  // namespace blender::bke::sim
