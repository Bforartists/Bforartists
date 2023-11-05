/* SPDX-FileCopyrightText: 2004 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup sequencer
 */

struct ListBase;
struct Scene;
struct Sequence;
struct SeqCollection;

void seq_update_sound_bounds_recursive(const struct Scene *scene, struct Sequence *metaseq);

/* Describes gap between strips in timeline. */
typedef struct GapInfo {
  int gap_start_frame; /* Start frame of the gap. */
  int gap_length;      /* Length of the gap. */
  bool gap_exists;     /* False if there are no gaps. */
} GapInfo;

/**
 * Find first gap between strips after initial_frame and describe it by filling data of r_gap_info
 *
 * \param scene: Scene in which strips are located.
 * \param seqbase: ListBase in which strips are located.
 * \param initial_frame: frame on timeline from where gaps are searched for.
 * \param r_gap_info: data structure describing gap, that will be filled in by this function.
 */
void seq_time_gap_info_get(const struct Scene *scene,
                           struct ListBase *seqbase,
                           int initial_frame,
                           struct GapInfo *r_gap_info);
void seq_time_effect_range_set(const struct Scene *scene, Sequence *seq);
/**
 * Update strip `startdisp` and `enddisp` (n-input effects have no length to calculate these).
 */
void seq_time_update_effects_strip_range(const struct Scene *scene, struct SeqCollection *effects);
void seq_time_translate_handles(const struct Scene *scene, struct Sequence *seq, const int offset);
float seq_time_media_playback_rate_factor_get(const struct Scene *scene,
                                              const struct Sequence *seq);
int seq_time_strip_original_content_length_get(const struct Scene *scene,
                                               const struct Sequence *seq);
float seq_retiming_evaluate(const struct Sequence *seq, const float frame_index);
