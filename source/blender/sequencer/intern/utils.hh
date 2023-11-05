/* SPDX-FileCopyrightText: 2004 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup sequencer
 */

struct ListBase;
struct Scene;

bool sequencer_seq_generates_image(struct Sequence *seq);
void seq_open_anim_file(struct Scene *scene, struct Sequence *seq, bool openfile);
Sequence *SEQ_get_meta_by_seqbase(struct ListBase *seqbase_main, struct ListBase *meta_seqbase);
