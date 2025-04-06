/* SPDX-FileCopyrightText: 2004 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup sequencer
 */

#include "BLI_array.hh"
#include "BLI_bounds_types.hh"
#include "BLI_math_matrix_types.hh"
#include "BLI_span.hh"

struct ListBase;
struct Scene;
struct Strip;

namespace blender::seq {

bool transform_sequence_can_be_translated(const Strip *strip);
/**
 * Used so we can do a quick check for single image seq
 * since they work a bit differently to normal image seq's (during transform).
 */
bool transform_single_image_check(const Strip *strip);
bool transform_test_overlap(const Scene *scene, ListBase *seqbasep, Strip *test);
bool transform_test_overlap_seq_seq(const Scene *scene, Strip *seq1, Strip *seq2);
void transform_translate_sequence(Scene *evil_scene, Strip *strip, int delta);
/**
 * \return 0 if there weren't enough space.
 */
bool transform_seqbase_shuffle_ex(ListBase *seqbasep,
                                  Strip *test,
                                  Scene *evil_scene,
                                  int channel_delta);
bool transform_seqbase_shuffle(ListBase *seqbasep, Strip *test, Scene *evil_scene);
bool transform_seqbase_shuffle_time(blender::Span<Strip *> strips_to_shuffle,
                                    blender::Span<Strip *> time_dependent_strips,
                                    ListBase *seqbasep,
                                    Scene *evil_scene,
                                    ListBase *markers,
                                    bool use_sync_markers);
bool transform_seqbase_shuffle_time(blender::Span<Strip *> strips_to_shuffle,
                                    ListBase *seqbasep,
                                    Scene *evil_scene,
                                    ListBase *markers,
                                    bool use_sync_markers);

void transform_handle_overlap(Scene *scene,
                              ListBase *seqbasep,
                              blender::Span<Strip *> transformed_strips,
                              blender::Span<Strip *> time_dependent_strips,
                              bool use_sync_markers);
void transform_handle_overlap(Scene *scene,
                              ListBase *seqbasep,
                              blender::Span<Strip *> transformed_strips,
                              bool use_sync_markers);
/**
 * Set strip channel. This value is clamped to valid values.
 */
void strip_channel_set(Strip *strip, int channel);
/**
 * Move strips and markers (if not locked) that start after timeline_frame by delta frames
 *
 * \param scene: Scene in which strips are located
 * \param seqbase: ListBase in which strips are located
 * \param delta: offset in frames to be applied
 * \param timeline_frame: frame on timeline from where strips are moved
 */
void transform_offset_after_frame(Scene *scene, ListBase *seqbase, int delta, int timeline_frame);

/**
 * Check if `seq` can be moved.
 * This function also checks `SeqTimelineChannel` flag.
 */
bool transform_is_locked(ListBase *channels, const Strip *strip);

/* Image transformation. */

blender::float2 image_transform_mirror_factor_get(const Strip *strip);
/**
 * Get strip transform origin offset from image center
 * NOTE: This function does not apply axis mirror.
 *
 * \param scene: Scene in which strips are located
 * \param seq: Sequence to calculate image transform origin
 */
blender::float2 image_transform_origin_offset_pixelspace_get(const Scene *scene,
                                                             const Strip *strip);
/**
 * Get 4 corner points of strip image, optionally without rotation component applied.
 * Corner vectors are in viewport space.
 *
 * \param scene: Scene in which strips are located
 * \param seq: Sequence to calculate transformed image quad
 * \param apply_rotation: Apply sequence rotation transform to the quad
 * \return array of 4 2D vectors
 */
blender::Array<blender::float2> image_transform_quad_get(const Scene *scene,
                                                         const Strip *strip,
                                                         bool apply_rotation);
/**
 * Get 4 corner points of strip image. Corner vectors are in viewport space.
 *
 * \param scene: Scene in which strips are located
 * \param seq: Sequence to calculate transformed image quad
 * \return array of 4 2D vectors
 */
blender::Array<blender::float2> image_transform_final_quad_get(const Scene *scene,
                                                               const Strip *strip);

blender::float2 image_preview_unit_to_px(const Scene *scene, blender::float2 co_src);
blender::float2 image_preview_unit_from_px(const Scene *scene, blender::float2 co_src);

/**
 * Get viewport axis aligned bounding box from a collection of sequences.
 * The collection must have one or more strips
 *
 * \param scene: Scene in which strips are located
 * \param strips: Collection of strips to get the bounding box from
 * \param apply_rotation: Include sequence rotation transform in the bounding box calculation
 * \param r_min: Minimum x and y values
 * \param r_max: Maximum x and y values
 */
blender::Bounds<blender::float2> image_transform_bounding_box_from_collection(
    Scene *scene, blender::Span<Strip *> strips, bool apply_rotation);

/**
 * Get strip image transformation matrix. Pivot point is set to correspond with viewport coordinate
 * system
 *
 * \param scene: Scene in which strips are located
 * \param seq: Strip that is used to construct the matrix
 */
blender::float3x3 image_transform_matrix_get(const Scene *scene, const Strip *strip);

}  // namespace blender::seq
