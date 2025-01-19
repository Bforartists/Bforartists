/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 * SPDX-FileCopyrightText: 2003-2024 Blender Authors
 * SPDX-FileCopyrightText: 2005-2006 Peter Schlaile <peter [at] schlaile [dot] de>
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 */

#include <cstring>

#include "DNA_sequence_types.h"

#include "BLI_listbase.h"

#include "SEQ_connect.hh"
#include "SEQ_effects.hh"
#include "SEQ_iterator.hh"
#include "SEQ_relations.hh"
#include "SEQ_render.hh"
#include "SEQ_time.hh"

using blender::VectorSet;

static bool strip_for_each_recursive(ListBase *seqbase, SeqForEachFunc callback, void *user_data)
{
  LISTBASE_FOREACH (Strip *, strip, seqbase) {
    if (!callback(strip, user_data)) {
      /* Callback signaled stop, return. */
      return false;
    }
    if (strip->type == STRIP_TYPE_META) {
      if (!strip_for_each_recursive(&strip->seqbase, callback, user_data)) {
        return false;
      }
    }
  }
  return true;
}

void SEQ_for_each_callback(ListBase *seqbase, SeqForEachFunc callback, void *user_data)
{
  strip_for_each_recursive(seqbase, callback, user_data);
}

VectorSet<Strip *> SEQ_query_by_reference(Strip *strip_reference,
                                          const Scene *scene,
                                          ListBase *seqbase,
                                          void strip_query_func(const Scene *scene,
                                                                Strip *strip_reference,
                                                                ListBase *seqbase,
                                                                VectorSet<Strip *> &strips))
{
  VectorSet<Strip *> strips;
  strip_query_func(scene, strip_reference, seqbase, strips);
  return strips;
}

void SEQ_iterator_set_expand(const Scene *scene,
                             ListBase *seqbase,
                             VectorSet<Strip *> &strips,
                             void strip_query_func(const Scene *scene,
                                                   Strip *strip_reference,
                                                   ListBase *seqbase,
                                                   VectorSet<Strip *> &strips))
{
  /* Collect expanded results for each sequence in provided VectorSet. */
  VectorSet<Strip *> query_matches;

  for (Strip *strip : strips) {
    query_matches.add_multiple(SEQ_query_by_reference(strip, scene, seqbase, strip_query_func));
  }

  /* Merge all expanded results in provided VectorSet. */
  strips.add_multiple(query_matches);
}

static void query_all_strips_recursive(const ListBase *seqbase, VectorSet<Strip *> &strips)
{
  LISTBASE_FOREACH (Strip *, seq, seqbase) {
    if (seq->type == STRIP_TYPE_META) {
      query_all_strips_recursive(&seq->seqbase, strips);
    }
    strips.add(seq);
  }
}

VectorSet<Strip *> SEQ_query_all_strips_recursive(const ListBase *seqbase)
{
  VectorSet<Strip *> strips;
  query_all_strips_recursive(seqbase, strips);
  return strips;
}

VectorSet<Strip *> SEQ_query_all_strips(ListBase *seqbase)
{
  VectorSet<Strip *> strips;
  LISTBASE_FOREACH (Strip *, strip, seqbase) {
    strips.add(strip);
  }
  return strips;
}

VectorSet<Strip *> SEQ_query_selected_strips(ListBase *seqbase)
{
  VectorSet<Strip *> strips;
  LISTBASE_FOREACH (Strip *, strip, seqbase) {
    if ((strip->flag & SELECT) != 0) {
      strips.add(strip);
    }
  }
  return strips;
}

static VectorSet<Strip *> query_strips_at_frame(const Scene *scene,
                                                ListBase *seqbase,
                                                const int timeline_frame)
{
  VectorSet<Strip *> strips;

  LISTBASE_FOREACH (Strip *, strip, seqbase) {
    if (SEQ_time_strip_intersects_frame(scene, strip, timeline_frame)) {
      strips.add(strip);
    }
  }
  return strips;
}

static void collection_filter_channel_up_to_incl(VectorSet<Strip *> &strips, const int channel)
{
  strips.remove_if([&](Strip *strip) { return strip->machine > channel; });
}

/* Check if seq must be rendered. This depends on whole stack in some cases, not only seq itself.
 * Order of applying these conditions is important. */
static bool must_render_strip(const VectorSet<Strip *> &strips, Strip *strip)
{
  bool strip_have_effect_in_stack = false;
  for (Strip *strip_iter : strips) {
    /* Strips is below another strip with replace blending are not rendered. */
    if (strip_iter->blend_mode == SEQ_BLEND_REPLACE && strip->machine < strip_iter->machine) {
      return false;
    }

    if ((strip_iter->type & STRIP_TYPE_EFFECT) != 0 &&
        SEQ_relation_is_effect_of_strip(strip_iter, strip))
    {
      /* Strips in same channel or higher than its effect are rendered. */
      if (strip->machine >= strip_iter->machine) {
        return true;
      }
      /* Mark that this strip has effect in stack, that is above the strip. */
      strip_have_effect_in_stack = true;
    }
  }

  /* All non-generator effects are rendered (with respect to conditions above). */
  if ((strip->type & STRIP_TYPE_EFFECT) != 0 && SEQ_effect_get_num_inputs(strip->type) != 0) {
    return true;
  }

  /* If strip has effects in stack, and all effects are above this strip, it is not rendered. */
  if (strip_have_effect_in_stack) {
    return false;
  }

  return true;
}

/* Remove strips we don't want to render from VectorSet. */
static void collection_filter_rendered_strips(VectorSet<Strip *> &strips, ListBase *channels)
{
  /* Remove sound strips and muted strips from VectorSet, because these are not rendered.
   * Function #must_render_strip() don't have to check for these strips anymore. */
  strips.remove_if([&](Strip *strip) {
    return strip->type == STRIP_TYPE_SOUND_RAM || SEQ_render_is_muted(channels, strip);
  });

  strips.remove_if([&](Strip *strip) { return !must_render_strip(strips, strip); });
}

VectorSet<Strip *> SEQ_query_rendered_strips(const Scene *scene,
                                             ListBase *channels,
                                             ListBase *seqbase,
                                             const int timeline_frame,
                                             const int displayed_channel)
{
  VectorSet strips = query_strips_at_frame(scene, seqbase, timeline_frame);
  if (displayed_channel != 0) {
    collection_filter_channel_up_to_incl(strips, displayed_channel);
  }
  collection_filter_rendered_strips(strips, channels);
  return strips;
}

VectorSet<Strip *> SEQ_query_unselected_strips(ListBase *seqbase)
{
  VectorSet<Strip *> strips;
  LISTBASE_FOREACH (Strip *, seq, seqbase) {
    if ((seq->flag & SELECT) != 0) {
      continue;
    }
    strips.add(seq);
  }
  return strips;
}

void SEQ_query_strip_effect_chain(const Scene *scene,
                                  Strip *reference_strip,
                                  ListBase *seqbase,
                                  VectorSet<Strip *> &r_strips)
{
  if (r_strips.contains(reference_strip)) {
    return; /* Strip is already in set, so all effects connected to it are as well. */
  }

  r_strips.add(reference_strip);

  /* Find all input strips for `reference_strip`. */
  if (reference_strip->type & STRIP_TYPE_EFFECT) {
    if (reference_strip->seq1) {
      SEQ_query_strip_effect_chain(scene, reference_strip->seq1, seqbase, r_strips);
    }
    if (reference_strip->seq2) {
      SEQ_query_strip_effect_chain(scene, reference_strip->seq2, seqbase, r_strips);
    }
  }

  /* Find all effect strips that have `reference_strip` as an input. */
  LISTBASE_FOREACH (Strip *, strip_test, seqbase) {
    if (strip_test->seq1 == reference_strip || strip_test->seq2 == reference_strip) {
      SEQ_query_strip_effect_chain(scene, strip_test, seqbase, r_strips);
    }
  }
}

void SEQ_query_strip_connected_and_effect_chain(const Scene *scene,
                                                Strip *reference_strip,
                                                ListBase *seqbase,
                                                VectorSet<Strip *> &r_strips)
{

  blender::Vector<Strip *> pending;
  pending.append(reference_strip);

  while (!pending.is_empty()) {
    Strip *current = pending.pop_last();

    if (r_strips.contains(current)) {
      continue;
    }

    r_strips.add(current);

    VectorSet<Strip *> connections = SEQ_get_connected_strips(current);
    for (Strip *connection : connections) {
      if (!r_strips.contains(connection)) {
        pending.append(connection);
      }
    }

    VectorSet<Strip *> effect_chain;
    SEQ_query_strip_effect_chain(scene, current, seqbase, effect_chain);
    for (Strip *effect_strip : effect_chain) {
      if (!r_strips.contains(effect_strip)) {
        pending.append(effect_strip);
      }
    }
  }
}
