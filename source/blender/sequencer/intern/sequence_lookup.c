/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2021 Blender Foundation. All rights reserved. */

/** \file
 * \ingroup sequencer
 */

#include "SEQ_sequencer.h"

#include "DNA_listBase.h"
#include "DNA_scene_types.h"
#include "DNA_sequence_types.h"

#include "SEQ_iterator.h"

#include "BLI_ghash.h"
#include "BLI_string.h"
#include "BLI_sys_types.h"
#include "BLI_threads.h"
#include <string.h>

#include "MEM_guardedalloc.h"

static ThreadMutex lookup_lock = BLI_MUTEX_INITIALIZER;

typedef struct SequenceLookup {
  GHash *by_name;
  eSequenceLookupTag tag;
} SequenceLookup;

static void seq_sequence_lookup_init(struct SequenceLookup *lookup)
{
  lookup->by_name = BLI_ghash_str_new(__func__);
  lookup->tag |= SEQ_LOOKUP_TAG_INVALID;
}

static void seq_sequence_lookup_build(const struct Scene *scene, struct SequenceLookup *lookup)
{
  SeqCollection *all_strips = SEQ_query_all_strips_recursive(&scene->ed->seqbase);
  Sequence *seq;
  SEQ_ITERATOR_FOREACH (seq, all_strips) {
    BLI_ghash_insert(lookup->by_name, seq->name + 2, seq);
  }
  SEQ_collection_free(all_strips);
  lookup->tag &= ~SEQ_LOOKUP_TAG_INVALID;
}

static SequenceLookup *seq_sequence_lookup_new(void)
{
  SequenceLookup *lookup = MEM_callocN(sizeof(SequenceLookup), __func__);
  seq_sequence_lookup_init(lookup);
  return lookup;
}

static void seq_sequence_lookup_free(struct SequenceLookup **lookup)
{
  if (*lookup == NULL) {
    return;
  }

  BLI_ghash_free((*lookup)->by_name, NULL, NULL);
  (*lookup)->by_name = NULL;
  MEM_freeN(*lookup);
  *lookup = NULL;
}

static void seq_sequence_lookup_rebuild(const struct Scene *scene, struct SequenceLookup **lookup)
{
  seq_sequence_lookup_free(lookup);
  *lookup = seq_sequence_lookup_new();
  seq_sequence_lookup_build(scene, *lookup);
}

static bool seq_sequence_lookup_is_valid(const struct SequenceLookup *lookup)
{
  return (lookup->tag & SEQ_LOOKUP_TAG_INVALID) == 0;
}

static void seq_sequence_lookup_update_if_needed(const struct Scene *scene,
                                                 struct SequenceLookup **lookup)
{
  if (!scene->ed) {
    return;
  }
  if (*lookup && seq_sequence_lookup_is_valid(*lookup)) {
    return;
  }

  seq_sequence_lookup_rebuild(scene, lookup);
}

void SEQ_sequence_lookup_free(const Scene *scene)
{
  BLI_assert(scene->ed);
  BLI_mutex_lock(&lookup_lock);
  SequenceLookup *lookup = scene->ed->runtime.sequence_lookup;
  seq_sequence_lookup_free(&lookup);
  BLI_mutex_unlock(&lookup_lock);
}

Sequence *SEQ_sequence_lookup_by_name(const Scene *scene, const char *key)
{
  BLI_assert(scene->ed);
  BLI_mutex_lock(&lookup_lock);
  seq_sequence_lookup_update_if_needed(scene, &scene->ed->runtime.sequence_lookup);
  SequenceLookup *lookup = scene->ed->runtime.sequence_lookup;
  Sequence *seq = BLI_ghash_lookup(lookup->by_name, key);
  BLI_mutex_unlock(&lookup_lock);
  return seq;
}

void SEQ_sequence_lookup_tag(const Scene *scene, eSequenceLookupTag tag)
{
  if (!scene->ed) {
    return;
  }

  BLI_mutex_lock(&lookup_lock);
  SequenceLookup *lookup = scene->ed->runtime.sequence_lookup;
  if (lookup != NULL) {
    lookup->tag |= tag;
  }
  BLI_mutex_unlock(&lookup_lock);
}
