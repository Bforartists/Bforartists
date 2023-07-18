/* SPDX-FileCopyrightText: 2023 Blender Foundation
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_collection.h"
#include "BKE_curves.hh"
#include "BKE_simulation_state.hh"
#include "BKE_simulation_state_serialize.hh"

#include "DNA_modifier_types.h"
#include "DNA_node_types.h"
#include "DNA_pointcloud_types.h"

#include "BLI_binary_search.hh"
#include "BLI_fileops.hh"
#include "BLI_hash_md5.h"
#include "BLI_path_util.h"
#include "BLI_string_utils.h"

#include "MOD_nodes.hh"

namespace blender::bke::sim {

GeometrySimulationStateItem::GeometrySimulationStateItem(GeometrySet geometry)
    : geometry(std::move(geometry))
{
}

PrimitiveSimulationStateItem::PrimitiveSimulationStateItem(const CPPType &type, const void *value)
    : type_(type)
{
  value_ = MEM_mallocN_aligned(type.size(), type.alignment(), __func__);
  type.copy_construct(value, value_);
}

PrimitiveSimulationStateItem::~PrimitiveSimulationStateItem()
{
  type_.destruct(value_);
  MEM_freeN(value_);
}

StringSimulationStateItem::StringSimulationStateItem(std::string value) : value_(std::move(value))
{
}

void ModifierSimulationCache::try_discover_bake(const StringRefNull absolute_bake_dir)
{
  if (failed_finding_bake_) {
    return;
  }

  char meta_dir[FILE_MAX];
  BLI_path_join(meta_dir, sizeof(meta_dir), absolute_bake_dir.c_str(), "meta");
  char bdata_dir[FILE_MAX];
  BLI_path_join(bdata_dir, sizeof(bdata_dir), absolute_bake_dir.c_str(), "bdata");

  if (!BLI_is_dir(meta_dir) || !BLI_is_dir(bdata_dir)) {
    failed_finding_bake_ = true;
    return;
  }

  direntry *dir_entries = nullptr;
  const int dir_entries_num = BLI_filelist_dir_contents(meta_dir, &dir_entries);
  BLI_SCOPED_DEFER([&]() { BLI_filelist_free(dir_entries, dir_entries_num); });

  if (dir_entries_num == 0) {
    failed_finding_bake_ = true;
    return;
  }

  this->reset();

  {
    std::lock_guard lock(states_at_frames_mutex_);

    for (const int i : IndexRange(dir_entries_num)) {
      const direntry &dir_entry = dir_entries[i];
      const StringRefNull dir_entry_path = dir_entry.path;
      if (!dir_entry_path.endswith(".json")) {
        continue;
      }
      char modified_file_name[FILE_MAX];
      STRNCPY(modified_file_name, dir_entry.relname);
      BLI_string_replace_char(modified_file_name, '_', '.');

      const SubFrame frame = std::stof(modified_file_name);

      auto new_state_at_frame = std::make_unique<ModifierSimulationStateAtFrame>();
      new_state_at_frame->frame = frame;
      new_state_at_frame->state.bdata_dir_ = bdata_dir;
      new_state_at_frame->state.meta_path_ = dir_entry.path;
      new_state_at_frame->state.owner_ = this;
      states_at_frames_.append(std::move(new_state_at_frame));
    }

    bdata_sharing_ = std::make_unique<BDataSharing>();
    this->cache_state = CacheState::Baked;
  }
}

static int64_t find_state_at_frame(
    const Span<std::unique_ptr<ModifierSimulationStateAtFrame>> states, const SubFrame &frame)
{
  const int64_t i = binary_search::find_predicate_begin(
      states, [&](const auto &item) { return item->frame >= frame; });
  if (i == states.size()) {
    return -1;
  }
  return i;
}

static int64_t find_state_at_frame_exact(
    const Span<std::unique_ptr<ModifierSimulationStateAtFrame>> states, const SubFrame &frame)
{
  const int64_t i = find_state_at_frame(states, frame);
  if (i == -1) {
    return -1;
  }
  if (states[i]->frame != frame) {
    return -1;
  }
  return i;
}

bool ModifierSimulationCache::has_state_at_frame(const SubFrame &frame) const
{
  std::lock_guard lock(states_at_frames_mutex_);
  return find_state_at_frame_exact(states_at_frames_, frame) != -1;
}

bool ModifierSimulationCache::has_states() const
{
  std::lock_guard lock(states_at_frames_mutex_);
  return !states_at_frames_.is_empty();
}

const ModifierSimulationState *ModifierSimulationCache::get_state_at_exact_frame(
    const SubFrame &frame) const
{
  std::lock_guard lock(states_at_frames_mutex_);
  const int64_t i = find_state_at_frame_exact(states_at_frames_, frame);
  if (i == -1) {
    return nullptr;
  }
  return &states_at_frames_[i]->state;
}

ModifierSimulationState &ModifierSimulationCache::get_state_at_frame_for_write(
    const SubFrame &frame)
{
  std::lock_guard lock(states_at_frames_mutex_);
  const int64_t i = find_state_at_frame_exact(states_at_frames_, frame);
  if (i != -1) {
    return states_at_frames_[i]->state;
  }

  if (!states_at_frames_.is_empty()) {
    BLI_assert(frame > states_at_frames_.last()->frame);
  }

  states_at_frames_.append(std::make_unique<ModifierSimulationStateAtFrame>());
  states_at_frames_.last()->frame = frame;
  states_at_frames_.last()->state.owner_ = this;
  return states_at_frames_.last()->state;
}

StatesAroundFrame ModifierSimulationCache::get_states_around_frame(const SubFrame &frame) const
{
  std::lock_guard lock(states_at_frames_mutex_);
  const int64_t i = find_state_at_frame(states_at_frames_, frame);
  StatesAroundFrame states_around_frame{};
  if (i == -1) {
    if (!states_at_frames_.is_empty() && states_at_frames_.last()->frame < frame) {
      states_around_frame.prev = states_at_frames_.last().get();
    }
    return states_around_frame;
  }
  if (states_at_frames_[i]->frame == frame) {
    states_around_frame.current = states_at_frames_[i].get();
  }
  if (i > 0) {
    states_around_frame.prev = states_at_frames_[i - 1].get();
  }
  if (i < states_at_frames_.size() - 2) {
    states_around_frame.next = states_at_frames_[i + 1].get();
  }
  return states_around_frame;
}

SimulationZoneState *ModifierSimulationState::get_zone_state(const SimulationZoneID &zone_id)
{
  std::lock_guard lock{mutex_};
  if (auto *ptr = zone_states_.lookup_ptr(zone_id)) {
    return ptr->get();
  }
  return nullptr;
}

const SimulationZoneState *ModifierSimulationState::get_zone_state(
    const SimulationZoneID &zone_id) const
{
  std::lock_guard lock{mutex_};
  if (auto *ptr = zone_states_.lookup_ptr(zone_id)) {
    return ptr->get();
  }
  return nullptr;
}

SimulationZoneState &ModifierSimulationState::get_zone_state_for_write(
    const SimulationZoneID &zone_id)
{
  std::lock_guard lock{mutex_};
  return *zone_states_.lookup_or_add_cb(zone_id,
                                        []() { return std::make_unique<SimulationZoneState>(); });
}

void ModifierSimulationState::ensure_bake_loaded(const bNodeTree &ntree) const
{
  std::scoped_lock lock{mutex_};
  if (bake_loaded_) {
    return;
  }
  if (!meta_path_ || !bdata_dir_) {
    return;
  }

  const std::shared_ptr<io::serialize::Value> io_root_value = io::serialize::read_json_file(
      *meta_path_);
  if (!io_root_value) {
    return;
  }
  const DictionaryValue *io_root = io_root_value->as_dictionary_value();
  if (!io_root) {
    return;
  }

  const DiskBDataReader bdata_reader{*bdata_dir_};
  deserialize_modifier_simulation_state(ntree,
                                        *io_root,
                                        bdata_reader,
                                        *owner_->bdata_sharing_,
                                        const_cast<ModifierSimulationState &>(*this));
  bake_loaded_ = true;
}

void ModifierSimulationCache::reset()
{
  std::lock_guard lock(states_at_frames_mutex_);
  states_at_frames_.clear();
  bdata_sharing_.reset();
  this->realtime_cache.current_state.reset();
  this->realtime_cache.prev_state.reset();
  this->cache_state = CacheState::Valid;
}

void scene_simulation_states_reset(Scene &scene)
{
  FOREACH_SCENE_OBJECT_BEGIN (&scene, ob) {
    LISTBASE_FOREACH (ModifierData *, md, &ob->modifiers) {
      if (md->type != eModifierType_Nodes) {
        continue;
      }
      NodesModifierData *nmd = reinterpret_cast<NodesModifierData *>(md);
      nmd->runtime->simulation_cache->reset();
    }
  }
  FOREACH_SCENE_OBJECT_END;
}

}  // namespace blender::bke::sim
