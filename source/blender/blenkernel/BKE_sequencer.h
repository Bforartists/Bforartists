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
 * The Original Code is Copyright (C) 2004 Blender Foundation.
 * All rights reserved.
 */

#ifndef __BKE_SEQUENCER_H__
#define __BKE_SEQUENCER_H__

/** \file
 * \ingroup bke
 */

#ifdef __cplusplus
extern "C" {
#endif

struct Depsgraph;
struct Editing;
struct GPUOffScreen;
struct GSet;
struct ImBuf;
struct Main;
struct Mask;
struct ReportList;
struct Scene;
struct Sequence;
struct SequenceModifierData;
struct Stereo3dFormat;
struct StripColorBalance;
struct StripElem;
struct TextVars;
struct bContext;
struct bSound;

struct SeqIndexBuildContext;

#define EARLY_NO_INPUT -1
#define EARLY_DO_EFFECT 0
#define EARLY_USE_INPUT_1 1
#define EARLY_USE_INPUT_2 2

/* sequence iterator */

typedef struct SeqIterator {
  struct Sequence **array;
  int tot, cur;

  struct Sequence *seq;
  int valid;
} SeqIterator;

void BKE_sequence_iterator_begin(struct Editing *ed, SeqIterator *iter, bool use_pointer);
void BKE_sequence_iterator_next(SeqIterator *iter);
void BKE_sequence_iterator_end(SeqIterator *iter);

#define SEQP_BEGIN(_ed, _seq) \
  { \
    SeqIterator iter_macro; \
    for (BKE_sequence_iterator_begin(_ed, &iter_macro, true); iter_macro.valid; \
         BKE_sequence_iterator_next(&iter_macro)) { \
      _seq = iter_macro.seq;

#define SEQ_BEGIN(ed, _seq) \
  { \
    SeqIterator iter_macro; \
    for (BKE_sequence_iterator_begin(ed, &iter_macro, false); iter_macro.valid; \
         BKE_sequence_iterator_next(&iter_macro)) { \
      _seq = iter_macro.seq;

#define SEQ_END \
  } \
  BKE_sequence_iterator_end(&iter_macro); \
  } \
  ((void)0)

typedef enum eSeqTaskId {
  SEQ_TASK_MAIN_RENDER,
  SEQ_TASK_PREFETCH_RENDER,
} eSeqTaskId;

typedef struct SeqRenderData {
  struct Main *bmain;
  struct Depsgraph *depsgraph;
  struct Scene *scene;
  int rectx;
  int recty;
  int preview_render_size;
  int for_render;
  int motion_blur_samples;
  float motion_blur_shutter;
  bool skip_cache;
  bool is_proxy_render;
  bool is_prefetch_render;
  int view_id;
  /* ID of task for asigning temp cache entries to particular task(thread, etc.) */
  eSeqTaskId task_id;

  /* special case for OpenGL render */
  struct GPUOffScreen *gpu_offscreen;
  // int gpu_samples;
  // bool gpu_full_samples;
} SeqRenderData;

void BKE_sequencer_new_render_data(struct Main *bmain,
                                   struct Depsgraph *depsgraph,
                                   struct Scene *scene,
                                   int rectx,
                                   int recty,
                                   int preview_render_size,
                                   int for_render,
                                   SeqRenderData *r_context);

int BKE_sequencer_cmp_time_startdisp(const void *a, const void *b);

/* Wipe effect */
enum {
  DO_SINGLE_WIPE,
  DO_DOUBLE_WIPE,
  /* DO_BOX_WIPE, */   /* UNUSED */
  /* DO_CROSS_WIPE, */ /* UNUSED */
  DO_IRIS_WIPE,
  DO_CLOCK_WIPE,
};

struct SeqEffectHandle {
  bool multithreaded;
  bool supports_mask;

  /* constructors & destructor */
  /* init is _only_ called on first creation */
  void (*init)(struct Sequence *seq);

  /* number of input strips needed
   * (called directly after construction) */
  int (*num_inputs)(void);

  /* load is called first time after readblenfile in
   * get_sequence_effect automatically */
  void (*load)(struct Sequence *seqconst);

  /* duplicate */
  void (*copy)(struct Sequence *dst, struct Sequence *src, const int flag);

  /* destruct */
  void (*free)(struct Sequence *seq, const bool do_id_user);

  /* returns: -1: no input needed,
   * 0: no early out,
   * 1: out = ibuf1,
   * 2: out = ibuf2 */
  int (*early_out)(struct Sequence *seq, float facf0, float facf1);

  /* stores the y-range of the effect IPO */
  void (*store_icu_yrange)(struct Sequence *seq, short adrcode, float *ymin, float *ymax);

  /* stores the default facf0 and facf1 if no IPO is present */
  void (*get_default_fac)(struct Sequence *seq, float cfra, float *facf0, float *facf1);

  /* execute the effect
   * sequence effects are only required to either support
   * float-rects or byte-rects
   * (mixed cases are handled one layer up...) */

  struct ImBuf *(*execute)(const SeqRenderData *context,
                           struct Sequence *seq,
                           float cfra,
                           float facf0,
                           float facf1,
                           struct ImBuf *ibuf1,
                           struct ImBuf *ibuf2,
                           struct ImBuf *ibuf3);

  struct ImBuf *(*init_execution)(const SeqRenderData *context,
                                  struct ImBuf *ibuf1,
                                  struct ImBuf *ibuf2,
                                  struct ImBuf *ibuf3);

  void (*execute_slice)(const SeqRenderData *context,
                        struct Sequence *seq,
                        float cfra,
                        float facf0,
                        float facf1,
                        struct ImBuf *ibuf1,
                        struct ImBuf *ibuf2,
                        struct ImBuf *ibuf3,
                        int start_line,
                        int total_lines,
                        struct ImBuf *out);
};

/* ********************* prototypes *************** */

/* **********************************************************************
 * sequencer.c
 *
 * sequencer render functions
 * ********************************************************************** */
double BKE_sequencer_rendersize_to_scale_factor(int size);

struct ImBuf *BKE_sequencer_give_ibuf(const SeqRenderData *context, float cfra, int chanshown);
struct ImBuf *BKE_sequencer_give_ibuf_direct(const SeqRenderData *context,
                                             float cfra,
                                             struct Sequence *seq);
struct ImBuf *BKE_sequencer_give_ibuf_seqbase(const SeqRenderData *context,
                                              float cfra,
                                              int chan_shown,
                                              struct ListBase *seqbasep);
struct ImBuf *BKE_sequencer_effect_execute_threaded(struct SeqEffectHandle *sh,
                                                    const SeqRenderData *context,
                                                    struct Sequence *seq,
                                                    float cfra,
                                                    float facf0,
                                                    float facf1,
                                                    struct ImBuf *ibuf1,
                                                    struct ImBuf *ibuf2,
                                                    struct ImBuf *ibuf3);

/* **********************************************************************
 * sequencer.c
 *
 * sequencer color space functions
 * ********************************************************************** */

void BKE_sequencer_imbuf_to_sequencer_space(struct Scene *scene,
                                            struct ImBuf *ibuf,
                                            bool make_float);
void BKE_sequencer_imbuf_from_sequencer_space(struct Scene *scene, struct ImBuf *ibuf);
void BKE_sequencer_pixel_from_sequencer_space_v4(struct Scene *scene, float pixel[4]);

/* **********************************************************************
 * sequencer scene functions
 * ********************************************************************** */
struct Editing *BKE_sequencer_editing_get(struct Scene *scene, bool alloc);
struct Editing *BKE_sequencer_editing_ensure(struct Scene *scene);
void BKE_sequencer_editing_free(struct Scene *scene, const bool do_id_user);

void BKE_sequencer_sort(struct Scene *scene);

struct Sequence *BKE_sequencer_from_elem(ListBase *seqbase, struct StripElem *se);
struct Sequence *BKE_sequencer_active_get(struct Scene *scene);
int BKE_sequencer_active_get_pair(struct Scene *scene,
                                  struct Sequence **seq_act,
                                  struct Sequence **seq_other);
void BKE_sequencer_active_set(struct Scene *scene, struct Sequence *seq);
struct Mask *BKE_sequencer_mask_get(struct Scene *scene);

/* apply functions recursively */
int BKE_sequencer_base_recursive_apply(struct ListBase *seqbase,
                                       int (*apply_func)(struct Sequence *seq, void *),
                                       void *arg);
int BKE_sequencer_recursive_apply(struct Sequence *seq,
                                  int (*apply_func)(struct Sequence *, void *),
                                  void *arg);

/* maintenance functions, mostly for RNA */
/* extern  */

void BKE_sequencer_free_clipboard(void);

void BKE_sequencer_base_clipboard_pointers_free(struct ListBase *seqbase);
void BKE_sequencer_base_clipboard_pointers_store(struct Main *bmain, struct ListBase *seqbase);
void BKE_sequencer_base_clipboard_pointers_restore(struct ListBase *seqbase, struct Main *bmain);

void BKE_sequence_free(struct Scene *scene, struct Sequence *seq, const bool do_clean_animdata);
void BKE_sequence_free_anim(struct Sequence *seq);
const char *BKE_sequence_give_name(struct Sequence *seq);
ListBase *BKE_sequence_seqbase_get(struct Sequence *seq, int *r_offset);
void BKE_sequence_calc(struct Scene *scene, struct Sequence *seq);
void BKE_sequence_calc_disp(struct Scene *scene, struct Sequence *seq);
void BKE_sequence_reload_new_file(struct Main *bmain,
                                  struct Scene *scene,
                                  struct Sequence *seq,
                                  const bool lock_range);
int BKE_sequencer_evaluate_frame(struct Scene *scene, int cfra);
int BKE_sequencer_get_shown_sequences(struct ListBase *seqbasep,
                                      int cfra,
                                      int chanshown,
                                      struct Sequence **seq_arr_out);

struct StripElem *BKE_sequencer_give_stripelem(struct Sequence *seq, int cfra);

/* intern */
void BKE_sequencer_update_changed_seq_and_deps(struct Scene *scene,
                                               struct Sequence *changed_seq,
                                               int len_change,
                                               int ibuf_change);
bool BKE_sequencer_input_have_to_preprocess(const SeqRenderData *context,
                                            struct Sequence *seq,
                                            float cfra);

bool BKE_sequencer_proxy_rebuild_context(struct Main *bmain,
                                         struct Depsgraph *depsgraph,
                                         struct Scene *scene,
                                         struct Sequence *seq,
                                         struct GSet *file_list,
                                         ListBase *queue);
void BKE_sequencer_proxy_rebuild(struct SeqIndexBuildContext *context,
                                 short *stop,
                                 short *do_update,
                                 float *num_frames_prefetched);
void BKE_sequencer_proxy_rebuild_finish(struct SeqIndexBuildContext *context, bool stop);

void BKE_sequencer_proxy_set(struct Sequence *seq, bool value);
/* **********************************************************************
 * seqcache.c
 *
 * Sequencer memory cache management functions
 * ********************************************************************** */

#define SEQ_CACHE_COST_MAX 10.0f

struct ImBuf *BKE_sequencer_cache_get(const SeqRenderData *context,
                                      struct Sequence *seq,
                                      float cfra,
                                      int type,
                                      bool skip_disk_cache);
void BKE_sequencer_cache_put(const SeqRenderData *context,
                             struct Sequence *seq,
                             float cfra,
                             int type,
                             struct ImBuf *nval,
                             float cost,
                             bool skip_disk_cache);
bool BKE_sequencer_cache_put_if_possible(const SeqRenderData *context,
                                         struct Sequence *seq,
                                         float cfra,
                                         int type,
                                         struct ImBuf *nval,
                                         float cost,
                                         bool skip_disk_cache);
bool BKE_sequencer_cache_recycle_item(struct Scene *scene);
void BKE_sequencer_cache_free_temp_cache(struct Scene *scene, short id, int cfra);
void BKE_sequencer_cache_destruct(struct Scene *scene);
void BKE_sequencer_cache_cleanup_all(struct Main *bmain);
void BKE_sequencer_cache_cleanup(struct Scene *scene);
void BKE_sequencer_cache_cleanup_sequence(struct Scene *scene,
                                          struct Sequence *seq,
                                          struct Sequence *seq_changed,
                                          int invalidate_types,
                                          bool force_seq_changed_range);
void BKE_sequencer_cache_iterate(struct Scene *scene,
                                 void *userdata,
                                 bool callback_init(void *userdata, size_t item_count),
                                 bool callback_iter(void *userdata,
                                                    struct Sequence *seq,
                                                    int cfra,
                                                    int cache_type,
                                                    float cost));
bool BKE_sequencer_cache_is_full(struct Scene *scene);

/* **********************************************************************
 * seqprefetch.c
 *
 * Sequencer frame prefetching
 * ********************************************************************** */

void BKE_sequencer_prefetch_start(const SeqRenderData *context, float cfra, float cost);
void BKE_sequencer_prefetch_stop_all(void);
void BKE_sequencer_prefetch_stop(struct Scene *scene);
void BKE_sequencer_prefetch_free(struct Scene *scene);
bool BKE_sequencer_prefetch_need_redraw(struct Main *bmain, struct Scene *scene);
bool BKE_sequencer_prefetch_job_is_running(struct Scene *scene);
void BKE_sequencer_prefetch_get_time_range(struct Scene *scene, int *start, int *end);
SeqRenderData *BKE_sequencer_prefetch_get_original_context(const SeqRenderData *context);
struct Sequence *BKE_sequencer_prefetch_get_original_sequence(struct Sequence *seq,
                                                              struct Scene *scene);

/* **********************************************************************
 * seqeffects.c
 *
 * Sequencer effect strip management functions
 *  **********************************************************************
 */

/* intern */
struct SeqEffectHandle BKE_sequence_get_blend(struct Sequence *seq);
void BKE_sequence_effect_speed_rebuild_map(struct Scene *scene, struct Sequence *seq, bool force);
float BKE_sequencer_speed_effect_target_frame_get(const SeqRenderData *context,
                                                  struct Sequence *seq,
                                                  float cfra,
                                                  int input);

/* extern */
struct SeqEffectHandle BKE_sequence_get_effect(struct Sequence *seq);
int BKE_sequence_effect_get_num_inputs(int seq_type);
int BKE_sequence_effect_get_supports_mask(int seq_type);
void BKE_sequencer_text_font_unload(struct TextVars *data, const bool do_id_user);
void BKE_sequencer_text_font_load(struct TextVars *data, const bool do_id_user);

/* **********************************************************************
 * Sequencer editing functions
 * **********************************************************************
 */

/* for transform but also could use elsewhere */
int BKE_sequence_tx_get_final_left(struct Sequence *seq, bool metaclip);
int BKE_sequence_tx_get_final_right(struct Sequence *seq, bool metaclip);
void BKE_sequence_tx_set_final_left(struct Sequence *seq, int val);
void BKE_sequence_tx_set_final_right(struct Sequence *seq, int val);
void BKE_sequence_tx_handle_xlimits(struct Sequence *seq, int leftflag, int rightflag);
bool BKE_sequence_tx_test(struct Sequence *seq);
bool BKE_sequence_tx_fullupdate_test(struct Sequence *seq);
bool BKE_sequence_single_check(struct Sequence *seq);
void BKE_sequence_single_fix(struct Sequence *seq);
bool BKE_sequence_test_overlap(struct ListBase *seqbasep, struct Sequence *test);
void BKE_sequence_translate(struct Scene *scene, struct Sequence *seq, int delta);
void BKE_sequence_sound_init(struct Scene *scene, struct Sequence *seq);
const struct Sequence *BKE_sequencer_foreground_frame_get(const struct Scene *scene, int frame);
struct ListBase *BKE_sequence_seqbase(struct ListBase *seqbase, struct Sequence *seq);
struct Sequence *BKE_sequence_metastrip(ListBase *seqbase /* = ed->seqbase */,
                                        struct Sequence *meta /* = NULL */,
                                        struct Sequence *seq);

void BKE_sequencer_offset_animdata(struct Scene *scene, struct Sequence *seq, int ofs);
void BKE_sequencer_dupe_animdata(struct Scene *scene, const char *name_src, const char *name_dst);
bool BKE_sequence_base_shuffle_ex(struct ListBase *seqbasep,
                                  struct Sequence *test,
                                  struct Scene *evil_scene,
                                  int channel_delta);
bool BKE_sequence_base_shuffle(struct ListBase *seqbasep,
                               struct Sequence *test,
                               struct Scene *evil_scene);
bool BKE_sequence_base_shuffle_time(ListBase *seqbasep,
                                    struct Scene *evil_scene,
                                    ListBase *markers,
                                    const bool use_sync_markers);
bool BKE_sequence_base_isolated_sel_check(struct ListBase *seqbase);
void BKE_sequencer_free_imbuf(struct Scene *scene, struct ListBase *seqbasep, bool for_render);
struct Sequence *BKE_sequence_dupli_recursive(const struct Scene *scene_src,
                                              struct Scene *scene_dst,
                                              struct ListBase *new_seq_list,
                                              struct Sequence *seq,
                                              int dupe_flag);
int BKE_sequence_swap(struct Sequence *seq_a, struct Sequence *seq_b, const char **error_str);

bool BKE_sequence_check_depend(struct Sequence *seq, struct Sequence *cur);
void BKE_sequence_invalidate_cache_raw(struct Scene *scene, struct Sequence *seq);
void BKE_sequence_invalidate_cache_preprocessed(struct Scene *scene, struct Sequence *seq);
void BKE_sequence_invalidate_cache_composite(struct Scene *scene, struct Sequence *seq);
void BKE_sequence_invalidate_dependent(struct Scene *scene, struct Sequence *seq);
void BKE_sequence_invalidate_scene_strips(struct Main *bmain, struct Scene *scene_target);
void BKE_sequence_invalidate_movieclip_strips(struct Main *bmain, struct MovieClip *clip_target);
void BKE_sequence_invalidate_cache_in_range(struct Scene *scene,
                                            struct Sequence *seq,
                                            struct Sequence *range_mask,
                                            int invalidate_types);

void BKE_sequencer_update_sound_bounds_all(struct Scene *scene);
void BKE_sequencer_update_sound_bounds(struct Scene *scene, struct Sequence *seq);
void BKE_sequencer_update_muting(struct Editing *ed);
void BKE_sequencer_update_sound(struct Scene *scene, struct bSound *sound);

void BKE_sequencer_refresh_sound_length(struct Main *bmain, struct Scene *scene);

void BKE_sequence_base_unique_name_recursive(ListBase *seqbasep, struct Sequence *seq);
void BKE_sequence_base_dupli_recursive(const struct Scene *scene_src,
                                       struct Scene *scene_dst,
                                       struct ListBase *nseqbase,
                                       const struct ListBase *seqbase,
                                       int dupe_flag,
                                       const int flag);
bool BKE_sequence_is_valid_check(struct Sequence *seq);

void BKE_sequencer_clear_scene_in_allseqs(struct Main *bmain, struct Scene *sce);

struct Sequence *BKE_sequence_get_by_name(struct ListBase *seqbase,
                                          const char *name,
                                          bool recursive);

/* api for adding new sequence strips */
typedef struct SeqLoadInfo {
  int start_frame;
  int end_frame;
  int channel;
  int flag; /* use sound, replace sel */
  int type;
  int len;         /* only for image strips */
  char path[1024]; /* 1024 = FILE_MAX */

  /* multiview */
  char views_format;
  struct Stereo3dFormat *stereo3d_format;

  /* return values */
  char name[64];
  struct Sequence *seq_sound; /* for movie's */
  int tot_success;
  int tot_error;
} SeqLoadInfo;

/* SeqLoadInfo.flag */
#define SEQ_LOAD_REPLACE_SEL (1 << 0)
#define SEQ_LOAD_FRAME_ADVANCE (1 << 1)
#define SEQ_LOAD_MOVIE_SOUND (1 << 2)
#define SEQ_LOAD_SOUND_CACHE (1 << 3)
#define SEQ_LOAD_SYNC_FPS (1 << 4)
#define SEQ_LOAD_SOUND_MONO (1 << 5)

/* seq_dupli' flags */
#define SEQ_DUPE_UNIQUE_NAME (1 << 0)
#define SEQ_DUPE_CONTEXT (1 << 1)
#define SEQ_DUPE_ANIM (1 << 2)
#define SEQ_DUPE_ALL (1 << 3) /* otherwise only selected are copied */
#define SEQ_DUPE_IS_RECURSIVE_CALL (1 << 4)

/* use as an api function */
typedef struct Sequence *(*SeqLoadFn)(struct bContext *, ListBase *, struct SeqLoadInfo *);

struct Sequence *BKE_sequence_alloc(ListBase *lb, int cfra, int machine, int type);

void BKE_sequence_alpha_mode_from_extension(struct Sequence *seq);
void BKE_sequence_init_colorspace(struct Sequence *seq);

float BKE_sequence_get_fps(struct Scene *scene, struct Sequence *seq);
float BKE_sequencer_give_stripelem_index(struct Sequence *seq, float cfra);

/* RNA enums, just to be more readable */
enum {
  SEQ_SIDE_NONE = 0,
  SEQ_SIDE_LEFT,
  SEQ_SIDE_RIGHT,
  SEQ_SIDE_BOTH,
  SEQ_SIDE_NO_CHANGE,
};
int BKE_sequencer_find_next_prev_edit(struct Scene *scene,
                                      int cfra,
                                      const short side,
                                      const bool do_skip_mute,
                                      const bool do_center,
                                      const bool do_unselected);

struct Sequence *BKE_sequencer_add_image_strip(struct bContext *C,
                                               ListBase *seqbasep,
                                               struct SeqLoadInfo *seq_load);
struct Sequence *BKE_sequencer_add_sound_strip(struct bContext *C,
                                               ListBase *seqbasep,
                                               struct SeqLoadInfo *seq_load);
struct Sequence *BKE_sequencer_add_movie_strip(struct bContext *C,
                                               ListBase *seqbasep,
                                               struct SeqLoadInfo *seq_load);

/* copy/paste */
extern ListBase seqbase_clipboard;
extern int seqbase_clipboard_frame;

/* modifiers */
typedef struct SequenceModifierTypeInfo {
  /* default name for the modifier */
  char name[64]; /* MAX_NAME */

  /* DNA structure name used on load/save filed */
  char struct_name[64]; /* MAX_NAME */

  /* size of modifier data structure, used by allocation */
  int struct_size;

  /* data initialization */
  void (*init_data)(struct SequenceModifierData *smd);

  /* free data used by modifier,
   * only modifier-specific data should be freed, modifier descriptor would
   * be freed outside of this callback
   */
  void (*free_data)(struct SequenceModifierData *smd);

  /* copy data from one modifier to another */
  void (*copy_data)(struct SequenceModifierData *smd, struct SequenceModifierData *target);

  /* apply modifier on a given image buffer */
  void (*apply)(struct SequenceModifierData *smd, struct ImBuf *ibuf, struct ImBuf *mask);
} SequenceModifierTypeInfo;

const struct SequenceModifierTypeInfo *BKE_sequence_modifier_type_info_get(int type);

struct SequenceModifierData *BKE_sequence_modifier_new(struct Sequence *seq,
                                                       const char *name,
                                                       int type);
bool BKE_sequence_modifier_remove(struct Sequence *seq, struct SequenceModifierData *smd);
void BKE_sequence_modifier_clear(struct Sequence *seq);
void BKE_sequence_modifier_free(struct SequenceModifierData *smd);
void BKE_sequence_modifier_unique_name(struct Sequence *seq, struct SequenceModifierData *smd);
struct SequenceModifierData *BKE_sequence_modifier_find_by_name(struct Sequence *seq,
                                                                const char *name);
struct ImBuf *BKE_sequence_modifier_apply_stack(const SeqRenderData *context,
                                                struct Sequence *seq,
                                                struct ImBuf *ibuf,
                                                int cfra);
void BKE_sequence_modifier_list_copy(struct Sequence *seqn, struct Sequence *seq);

int BKE_sequence_supports_modifiers(struct Sequence *seq);

/* internal filters */
struct ImBuf *BKE_sequencer_render_mask_input(const SeqRenderData *context,
                                              int mask_input_type,
                                              struct Sequence *mask_sequence,
                                              struct Mask *mask_id,
                                              int cfra,
                                              int fra_offset,
                                              bool make_float);
void BKE_sequencer_color_balance_apply(struct StripColorBalance *cb,
                                       struct ImBuf *ibuf,
                                       float mul,
                                       bool make_float,
                                       struct ImBuf *mask_input);

void BKE_sequencer_all_free_anim_ibufs(struct Scene *scene, int cfra);
bool BKE_sequencer_check_scene_recursion(struct Scene *scene, struct ReportList *reports);

#ifdef __cplusplus
}
#endif

#endif /* __BKE_SEQUENCER_H__ */
