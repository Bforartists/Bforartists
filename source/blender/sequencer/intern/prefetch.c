/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 */

/** \file
 * \ingroup bke
 */

#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_anim_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_sequence_types.h"
#include "DNA_windowmanager_types.h"

#include "BLI_listbase.h"
#include "BLI_threads.h"

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "BKE_anim_data.h"
#include "BKE_animsys.h"
#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_layer.h"
#include "BKE_lib_id.h"
#include "BKE_main.h"
#include "BKE_scene.h"

#include "DEG_depsgraph.h"
#include "DEG_depsgraph_build.h"
#include "DEG_depsgraph_debug.h"
#include "DEG_depsgraph_query.h"

#include "SEQ_prefetch.h"
#include "SEQ_render.h"
#include "SEQ_sequencer.h"

#include "image_cache.h"
#include "prefetch.h"
#include "render.h"

typedef struct PrefetchJob {
  struct PrefetchJob *next, *prev;

  struct Main *bmain;
  struct Main *bmain_eval;
  struct Scene *scene;
  struct Scene *scene_eval;
  struct Depsgraph *depsgraph;

  ThreadMutex prefetch_suspend_mutex;
  ThreadCondition prefetch_suspend_cond;

  ListBase threads;

  /* context */
  struct SeqRenderData context;
  struct SeqRenderData context_cpy;
  struct ListBase *seqbasep;
  struct ListBase *seqbasep_cpy;

  /* prefetch area */
  float cfra;
  int num_frames_prefetched;

  /* control */
  bool running;
  bool waiting;
  bool stop;
} PrefetchJob;

static bool seq_prefetch_is_playing(Main *bmain)
{
  for (bScreen *screen = bmain->screens.first; screen; screen = screen->id.next) {
    if (screen->animtimer) {
      return true;
    }
  }
  return false;
}

static bool seq_prefetch_is_scrubbing(Main *bmain)
{

  for (bScreen *screen = bmain->screens.first; screen; screen = screen->id.next) {
    if (screen->scrubbing) {
      return true;
    }
  }
  return false;
}

static PrefetchJob *seq_prefetch_job_get(Scene *scene)
{
  if (scene && scene->ed) {
    return scene->ed->prefetch_job;
  }
  return NULL;
}

bool seq_prefetch_job_is_running(Scene *scene)
{
  PrefetchJob *pfjob = seq_prefetch_job_get(scene);

  if (!pfjob) {
    return false;
  }

  return pfjob->running;
}

static bool seq_prefetch_job_is_waiting(Scene *scene)
{
  PrefetchJob *pfjob = seq_prefetch_job_get(scene);

  if (!pfjob) {
    return false;
  }

  return pfjob->waiting;
}

static Sequence *sequencer_prefetch_get_original_sequence(Sequence *seq, ListBase *seqbase)
{
  LISTBASE_FOREACH (Sequence *, seq_orig, seqbase) {
    if (STREQ(seq->name, seq_orig->name)) {
      return seq_orig;
    }

    if (seq_orig->type == SEQ_TYPE_META) {
      Sequence *match = sequencer_prefetch_get_original_sequence(seq, &seq_orig->seqbase);
      if (match != NULL) {
        return match;
      }
    }
  }

  return NULL;
}

/* for cache context swapping */
Sequence *seq_prefetch_get_original_sequence(Sequence *seq, Scene *scene)
{
  Editing *ed = scene->ed;
  return sequencer_prefetch_get_original_sequence(seq, &ed->seqbase);
}

/* for cache context swapping */
SeqRenderData *seq_prefetch_get_original_context(const SeqRenderData *context)
{
  PrefetchJob *pfjob = seq_prefetch_job_get(context->scene);

  return &pfjob->context;
}

static bool seq_prefetch_is_cache_full(Scene *scene)
{
  PrefetchJob *pfjob = seq_prefetch_job_get(scene);

  if (!seq_cache_is_full()) {
    return false;
  }

  return seq_cache_recycle_item(pfjob->scene) == false;
}

static float seq_prefetch_cfra(PrefetchJob *pfjob)
{
  return pfjob->cfra + pfjob->num_frames_prefetched;
}
static AnimationEvalContext seq_prefetch_anim_eval_context(PrefetchJob *pfjob)
{
  return BKE_animsys_eval_context_construct(pfjob->depsgraph, seq_prefetch_cfra(pfjob));
}

void seq_prefetch_get_time_range(Scene *scene, int *start, int *end)
{
  PrefetchJob *pfjob = seq_prefetch_job_get(scene);

  *start = pfjob->cfra;
  *end = seq_prefetch_cfra(pfjob);
}

static void seq_prefetch_free_depsgraph(PrefetchJob *pfjob)
{
  if (pfjob->depsgraph != NULL) {
    DEG_graph_free(pfjob->depsgraph);
  }
  pfjob->depsgraph = NULL;
  pfjob->scene_eval = NULL;
}

static void seq_prefetch_update_depsgraph(PrefetchJob *pfjob)
{
  DEG_evaluate_on_framechange(pfjob->depsgraph, seq_prefetch_cfra(pfjob));
}

static void seq_prefetch_init_depsgraph(PrefetchJob *pfjob)
{
  Main *bmain = pfjob->bmain_eval;
  Scene *scene = pfjob->scene;
  ViewLayer *view_layer = BKE_view_layer_default_render(scene);

  pfjob->depsgraph = DEG_graph_new(bmain, scene, view_layer, DAG_EVAL_RENDER);
  DEG_debug_name_set(pfjob->depsgraph, "SEQUENCER PREFETCH");

  /* Make sure there is a correct evaluated scene pointer. */
  DEG_graph_build_for_render_pipeline(pfjob->depsgraph);

  /* Update immediately so we have proper evaluated scene. */
  seq_prefetch_update_depsgraph(pfjob);

  pfjob->scene_eval = DEG_get_evaluated_scene(pfjob->depsgraph);
  pfjob->scene_eval->ed->cache_flag = 0;
}

static void seq_prefetch_update_area(PrefetchJob *pfjob)
{
  int cfra = pfjob->scene->r.cfra;

  /* rebase */
  if (cfra > pfjob->cfra) {
    int delta = cfra - pfjob->cfra;
    pfjob->cfra = cfra;
    pfjob->num_frames_prefetched -= delta;

    if (pfjob->num_frames_prefetched <= 1) {
      pfjob->num_frames_prefetched = 1;
    }
  }

  /* reset */
  if (cfra < pfjob->cfra) {
    pfjob->cfra = cfra;
    pfjob->num_frames_prefetched = 1;
  }
}

void SEQ_prefetch_stop_all(void)
{
  /*TODO(Richard): Use wm_jobs for prefetch, or pass main. */
  for (Scene *scene = G.main->scenes.first; scene; scene = scene->id.next) {
    SEQ_prefetch_stop(scene);
  }
}

/* Use also to update scene and context changes
 * This function should almost always be called by cache invalidation, not directly.
 */
void SEQ_prefetch_stop(Scene *scene)
{
  PrefetchJob *pfjob;
  pfjob = seq_prefetch_job_get(scene);

  if (!pfjob) {
    return;
  }

  pfjob->stop = true;

  while (pfjob->running) {
    BLI_condition_notify_one(&pfjob->prefetch_suspend_cond);
  }
}

static void seq_prefetch_update_context(const SeqRenderData *context)
{
  PrefetchJob *pfjob;
  pfjob = seq_prefetch_job_get(context->scene);

  SEQ_render_new_render_data(pfjob->bmain_eval,
                             pfjob->depsgraph,
                             pfjob->scene_eval,
                             context->rectx,
                             context->recty,
                             context->preview_render_size,
                             false,
                             &pfjob->context_cpy);
  pfjob->context_cpy.is_prefetch_render = true;
  pfjob->context_cpy.task_id = SEQ_TASK_PREFETCH_RENDER;

  SEQ_render_new_render_data(pfjob->bmain,
                             pfjob->depsgraph,
                             pfjob->scene,
                             context->rectx,
                             context->recty,
                             context->preview_render_size,
                             false,
                             &pfjob->context);
  pfjob->context.is_prefetch_render = false;

  /* Same ID as prefetch context, because context will be swapped, but we still
   * want to assign this ID to cache entries created in this thread.
   * This is to allow "temp cache" work correctly for both threads.
   */
  pfjob->context.task_id = SEQ_TASK_PREFETCH_RENDER;
}

static void seq_prefetch_update_scene(Scene *scene)
{
  PrefetchJob *pfjob = seq_prefetch_job_get(scene);

  if (!pfjob) {
    return;
  }

  pfjob->scene = scene;
  seq_prefetch_free_depsgraph(pfjob);
  seq_prefetch_init_depsgraph(pfjob);
}

static void seq_prefetch_resume(Scene *scene)
{
  PrefetchJob *pfjob = seq_prefetch_job_get(scene);

  if (pfjob && pfjob->waiting) {
    BLI_condition_notify_one(&pfjob->prefetch_suspend_cond);
  }
}

void seq_prefetch_free(Scene *scene)
{
  PrefetchJob *pfjob = seq_prefetch_job_get(scene);
  if (!pfjob) {
    return;
  }

  SEQ_prefetch_stop(scene);

  BLI_threadpool_remove(&pfjob->threads, pfjob);
  BLI_threadpool_end(&pfjob->threads);
  BLI_mutex_end(&pfjob->prefetch_suspend_mutex);
  BLI_condition_end(&pfjob->prefetch_suspend_cond);
  seq_prefetch_free_depsgraph(pfjob);
  BKE_main_free(pfjob->bmain_eval);
  MEM_freeN(pfjob);
  scene->ed->prefetch_job = NULL;
}

/* Skip frame if we need to render 3D scene strip. Rendering 3D scene requires main lock or setting
 * up render job that doesn't have API to do openGL renders which can be used for sequencer. */
static bool seq_prefetch_do_skip_frame(PrefetchJob *pfjob, ListBase *seqbase)
{
  float cfra = seq_prefetch_cfra(pfjob);
  Sequence *seq_arr[MAXSEQ + 1];
  int count = seq_get_shown_sequences(seqbase, cfra, 0, seq_arr);
  SeqRenderData *ctx = &pfjob->context_cpy;
  ImBuf *ibuf = NULL;

  /* Disable prefetching 3D scene strips, but check for disk cache. */
  for (int i = 0; i < count; i++) {
    if (seq_arr[i]->type == SEQ_TYPE_META &&
        seq_prefetch_do_skip_frame(pfjob, &seq_arr[i]->seqbase)) {
      return true;
    }

    if (seq_arr[i]->type == SEQ_TYPE_SCENE && (seq_arr[i]->flag & SEQ_SCENE_STRIPS) == 0) {
      int cached_types = 0;

      ibuf = seq_cache_get(ctx, seq_arr[i], cfra, SEQ_CACHE_STORE_FINAL_OUT);
      if (ibuf != NULL) {
        cached_types |= SEQ_CACHE_STORE_FINAL_OUT;
        IMB_freeImBuf(ibuf);
        ibuf = NULL;
      }

      ibuf = seq_cache_get(ctx, seq_arr[i], cfra, SEQ_CACHE_STORE_COMPOSITE);
      if (ibuf != NULL) {
        cached_types |= SEQ_CACHE_STORE_COMPOSITE;
        IMB_freeImBuf(ibuf);
        ibuf = NULL;
      }

      ibuf = seq_cache_get(ctx, seq_arr[i], cfra, SEQ_CACHE_STORE_PREPROCESSED);
      if (ibuf != NULL) {
        cached_types |= SEQ_CACHE_STORE_PREPROCESSED;
        IMB_freeImBuf(ibuf);
        ibuf = NULL;
      }

      ibuf = seq_cache_get(ctx, seq_arr[i], cfra, SEQ_CACHE_STORE_RAW);
      if (ibuf != NULL) {
        cached_types |= SEQ_CACHE_STORE_RAW;
        IMB_freeImBuf(ibuf);
        ibuf = NULL;
      }

      if ((cached_types & (SEQ_CACHE_STORE_RAW | SEQ_CACHE_STORE_PREPROCESSED)) != 0) {
        continue;
      }

      /* It is only safe to use these cache types if strip is last in stack. */
      if (i == count - 1 && (cached_types & SEQ_CACHE_STORE_FINAL_OUT) != 0) {
        continue;
      }

      return true;
    }
  }

  return false;
}

static bool seq_prefetch_need_suspend(PrefetchJob *pfjob)
{
  return seq_prefetch_is_cache_full(pfjob->scene) || seq_prefetch_is_scrubbing(pfjob->bmain) ||
         (seq_prefetch_cfra(pfjob) >= pfjob->scene->r.efra);
}

static void seq_prefetch_do_suspend(PrefetchJob *pfjob)
{
  BLI_mutex_lock(&pfjob->prefetch_suspend_mutex);
  while (seq_prefetch_need_suspend(pfjob) &&
         (pfjob->scene->ed->cache_flag & SEQ_CACHE_PREFETCH_ENABLE) && !pfjob->stop) {
    pfjob->waiting = true;
    BLI_condition_wait(&pfjob->prefetch_suspend_cond, &pfjob->prefetch_suspend_mutex);
    seq_prefetch_update_area(pfjob);
  }
  pfjob->waiting = false;
  BLI_mutex_unlock(&pfjob->prefetch_suspend_mutex);
}

static void *seq_prefetch_frames(void *job)
{
  PrefetchJob *pfjob = (PrefetchJob *)job;

  while (seq_prefetch_cfra(pfjob) <= pfjob->scene->r.efra) {
    pfjob->scene_eval->ed->prefetch_job = NULL;

    seq_prefetch_update_depsgraph(pfjob);
    AnimData *adt = BKE_animdata_from_id(&pfjob->context_cpy.scene->id);
    AnimationEvalContext anim_eval_context = seq_prefetch_anim_eval_context(pfjob);
    BKE_animsys_evaluate_animdata(
        &pfjob->context_cpy.scene->id, adt, &anim_eval_context, ADT_RECALC_ALL, false);

    /* This is quite hacky solution:
     * We need cross-reference original scene with copy for cache.
     * However depsgraph must not have this data, because it will try to kill this job.
     * Scene copy don't reference original scene. Perhaps, this could be done by depsgraph.
     * Set to NULL before return!
     */
    pfjob->scene_eval->ed->prefetch_job = pfjob;

    ListBase *seqbase = SEQ_active_seqbase_get(SEQ_editing_get(pfjob->scene, false));
    if (seq_prefetch_do_skip_frame(pfjob, seqbase)) {
      pfjob->num_frames_prefetched++;
      continue;
    }

    ImBuf *ibuf = SEQ_render_give_ibuf(&pfjob->context_cpy, seq_prefetch_cfra(pfjob), 0);
    seq_cache_free_temp_cache(pfjob->scene, pfjob->context.task_id, seq_prefetch_cfra(pfjob));
    IMB_freeImBuf(ibuf);

    /* Suspend thread if there is nothing to be prefetched. */
    seq_prefetch_do_suspend(pfjob);

    /* Avoid "collision" with main thread, but make sure to fetch at least few frames */
    if (pfjob->num_frames_prefetched > 5 &&
        (seq_prefetch_cfra(pfjob) - pfjob->scene->r.cfra) < 2) {
      break;
    }

    if (!(pfjob->scene->ed->cache_flag & SEQ_CACHE_PREFETCH_ENABLE) || pfjob->stop) {
      break;
    }

    seq_prefetch_update_area(pfjob);
    pfjob->num_frames_prefetched++;
  }

  seq_cache_free_temp_cache(pfjob->scene, pfjob->context.task_id, seq_prefetch_cfra(pfjob));
  pfjob->running = false;
  pfjob->scene_eval->ed->prefetch_job = NULL;

  return NULL;
}

static PrefetchJob *seq_prefetch_start_ex(const SeqRenderData *context, float cfra)
{
  PrefetchJob *pfjob = seq_prefetch_job_get(context->scene);

  if (!pfjob) {
    if (context->scene->ed) {
      pfjob = (PrefetchJob *)MEM_callocN(sizeof(PrefetchJob), "PrefetchJob");
      context->scene->ed->prefetch_job = pfjob;

      BLI_threadpool_init(&pfjob->threads, seq_prefetch_frames, 1);
      BLI_mutex_init(&pfjob->prefetch_suspend_mutex);
      BLI_condition_init(&pfjob->prefetch_suspend_cond);

      pfjob->bmain_eval = BKE_main_new();
      pfjob->scene = context->scene;
      seq_prefetch_init_depsgraph(pfjob);
    }
  }
  pfjob->bmain = context->bmain;

  pfjob->cfra = cfra;
  pfjob->num_frames_prefetched = 1;

  pfjob->waiting = false;
  pfjob->stop = false;
  pfjob->running = true;

  seq_prefetch_update_scene(context->scene);
  seq_prefetch_update_context(context);

  BLI_threadpool_remove(&pfjob->threads, pfjob);
  BLI_threadpool_insert(&pfjob->threads, pfjob);

  return pfjob;
}

/* Start or resume prefetching*/
void seq_prefetch_start(const SeqRenderData *context, float timeline_frame)
{
  Scene *scene = context->scene;
  Editing *ed = scene->ed;
  bool has_strips = (bool)ed->seqbasep->first;

  if (!context->is_prefetch_render && !context->is_proxy_render) {
    bool playing = seq_prefetch_is_playing(context->bmain);
    bool scrubbing = seq_prefetch_is_scrubbing(context->bmain);
    bool running = seq_prefetch_job_is_running(scene);
    seq_prefetch_resume(scene);
    /* conditions to start:
     * prefetch enabled, prefetch not running, not scrubbing,  not playing,
     * cache storage enabled, has strips to render, not rendering, not doing modal transform -
     * important, see D7820.
     */
    if ((ed->cache_flag & SEQ_CACHE_PREFETCH_ENABLE) && !running && !scrubbing && !playing &&
        ed->cache_flag & SEQ_CACHE_ALL_TYPES && has_strips && !G.is_rendering && !G.moving) {

      seq_prefetch_start_ex(context, timeline_frame);
    }
  }
}

bool SEQ_prefetch_need_redraw(Main *bmain, Scene *scene)
{
  bool playing = seq_prefetch_is_playing(bmain);
  bool scrubbing = seq_prefetch_is_scrubbing(bmain);
  bool running = seq_prefetch_job_is_running(scene);
  bool suspended = seq_prefetch_job_is_waiting(scene);

  /* force redraw, when prefetching and using cache view. */
  if (running && !playing && !suspended && scene->ed->cache_flag & SEQ_CACHE_VIEW_ENABLE) {
    return true;
  }
  /* Sometimes scrubbing flag is set when not scrubbing. In that case I want to catch "event" of
   * stopping scrubbing */
  if (scrubbing) {
    return true;
  }
  return false;
}
