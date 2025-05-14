/* SPDX-FileCopyrightText: 2025 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup sequencer
 */

#include "BLI_map.hh"
#include "BLI_mutex.hh"

#include "DNA_scene_types.h"
#include "DNA_sequence_types.h"

#include "IMB_imbuf.hh"

#include "SEQ_relations.hh"
#include "SEQ_render.hh"
#include "SEQ_time.hh"

#include "final_image_cache.hh"
#include "prefetch.hh"

namespace blender::seq {

static Mutex final_image_cache_mutex;

struct FinalImageCache {
  /* Key is {timeline frame, view ID}. */
  Map<std::pair<int, int>, ImBuf *> map_;

  ~FinalImageCache()
  {
    clear();
  }

  void clear()
  {
    for (ImBuf *item : map_.values()) {
      IMB_freeImBuf(item);
    }
    map_.clear();
  }
};

static FinalImageCache *ensure_final_image_cache(Scene *scene)
{
  FinalImageCache **cache = &scene->ed->runtime.final_image_cache;
  if (*cache == nullptr) {
    *cache = MEM_new<FinalImageCache>(__func__);
  }
  return *cache;
}

static FinalImageCache *query_final_image_cache(const Scene *scene)
{
  if (scene == nullptr || scene->ed == nullptr) {
    return nullptr;
  }
  return scene->ed->runtime.final_image_cache;
}

ImBuf *final_image_cache_get(Scene *scene, float timeline_frame, int view_id)
{
  const std::pair<int, int> key = {int(math::round(timeline_frame)), view_id};

  ImBuf *res = nullptr;
  {
    std::lock_guard lock(final_image_cache_mutex);
    FinalImageCache *cache = query_final_image_cache(scene);
    if (cache == nullptr) {
      return nullptr;
    }
    res = cache->map_.lookup_default(key, nullptr);
  }

  if (res) {
    IMB_refImBuf(res);
  }
  return res;
}

void final_image_cache_put(Scene *scene, float timeline_frame, int view_id, ImBuf *image)
{
  const std::pair<int, int> key = {int(math::round(timeline_frame)), view_id};

  IMB_refImBuf(image);

  std::lock_guard lock(final_image_cache_mutex);
  FinalImageCache *cache = ensure_final_image_cache(scene);

  cache->map_.add_or_modify(
      key,
      [&](ImBuf **value) { *value = image; },
      [&](ImBuf **existing) {
        if (*existing) {
          IMB_freeImBuf(*existing);
        }
        *existing = image;
      });
}

void final_image_cache_invalidate_frame_range(Scene *scene,
                                              const float timeline_frame_start,
                                              const float timeline_frame_end)
{
  std::lock_guard lock(final_image_cache_mutex);
  FinalImageCache *cache = query_final_image_cache(scene);
  if (cache == nullptr) {
    return;
  }

  const int key_start = int(math::floor(timeline_frame_start));
  const int key_end = int(math::ceil(timeline_frame_end));

  for (auto it = cache->map_.items().begin(); it != cache->map_.items().end(); it++) {
    const int key = (*it).key.first;
    if (key >= key_start && key <= key_end) {
      IMB_freeImBuf((*it).value);
      cache->map_.remove(it);
    }
  }
}

void final_image_cache_clear(Scene *scene)
{
  std::lock_guard lock(final_image_cache_mutex);
  FinalImageCache *cache = query_final_image_cache(scene);
  if (cache != nullptr) {
    scene->ed->runtime.final_image_cache->clear();
  }
}

void final_image_cache_destroy(Scene *scene)
{
  std::lock_guard lock(final_image_cache_mutex);
  FinalImageCache *cache = query_final_image_cache(scene);
  if (cache != nullptr) {
    BLI_assert(cache == scene->ed->runtime.final_image_cache);
    MEM_delete(scene->ed->runtime.final_image_cache);
    scene->ed->runtime.final_image_cache = nullptr;
  }
}

void final_image_cache_iterate(Scene *scene,
                               void *userdata,
                               void callback_iter(void *userdata, int timeline_frame))
{
  std::lock_guard lock(final_image_cache_mutex);
  FinalImageCache *cache = query_final_image_cache(scene);
  if (cache == nullptr) {
    return;
  }
  for (std::pair<int, int> frame_view : cache->map_.keys()) {
    callback_iter(userdata, frame_view.first);
  }
}

size_t final_image_cache_calc_memory_size(const Scene *scene)
{
  std::lock_guard lock(final_image_cache_mutex);
  FinalImageCache *cache = query_final_image_cache(scene);
  if (cache == nullptr) {
    return 0;
  }
  size_t size = 0;
  for (ImBuf *frame : cache->map_.values()) {
    size += IMB_get_size_in_memory(frame);
  }
  return size;
}

size_t final_image_cache_get_image_count(const Scene *scene)
{
  std::lock_guard lock(final_image_cache_mutex);
  FinalImageCache *cache = query_final_image_cache(scene);
  if (cache == nullptr) {
    return 0;
  }
  return cache->map_.size();
}

bool final_image_cache_evict(Scene *scene)
{
  std::lock_guard lock(final_image_cache_mutex);
  FinalImageCache *cache = query_final_image_cache(scene);
  if (cache == nullptr) {
    return false;
  }

  /* Find which entry to remove -- we pick the one that is furthest from the current frame,
   * biasing the ones that are behind the current frame.
   *
   * However, do not try to evict entries from the current prefetch job range -- we need to
   * be able to fully fill the cache from prefetching, and then actually stop the job when it
   * is full and no longer can evict anything. */
  int cur_prefetch_start = std::numeric_limits<int>::min();
  int cur_prefetch_end = std::numeric_limits<int>::min();
  seq_prefetch_get_time_range(scene, &cur_prefetch_start, &cur_prefetch_end);

  const int cur_frame = scene->r.cfra;
  std::pair<int, int> best_key = {};
  ImBuf *best_item = nullptr;
  int best_score = 0;
  for (const auto &item : cache->map_.items()) {
    const int item_frame = item.key.first;
    if (item_frame >= cur_prefetch_start && item_frame <= cur_prefetch_end) {
      continue; /* Within active prefetch range, do not try to remove it. */
    }

    /* Score for removal is distance to current frame; 2x that if behind current frame. */
    int score = 0;
    if (item_frame < cur_frame) {
      score = (cur_frame - item_frame) * 2;
    }
    else if (item_frame > cur_frame) {
      score = item_frame - cur_frame;
    }
    if (score > best_score) {
      best_key = item.key;
      best_item = item.value;
      best_score = score;
    }
  }

  /* Remove if we found one. */
  if (best_item != nullptr) {
    IMB_freeImBuf(best_item);
    cache->map_.remove(best_key);
    return true;
  }

  /* Did not find anything to remove. */
  return false;
}

}  // namespace blender::seq
