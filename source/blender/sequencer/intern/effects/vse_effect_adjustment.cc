/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup sequencer
 */

#include "DNA_sequence_types.h"

#include "SEQ_channels.hh"
#include "SEQ_relations.hh"
#include "SEQ_render.hh"
#include "SEQ_time.hh"
#include "SEQ_utils.hh"

#include "effects.hh"
#include "render.hh"

/* No effect inputs for adjustment, we use #give_ibuf_seq. */
static int num_inputs_adjustment()
{
  return 0;
}

static StripEarlyOut early_out_adjustment(const Sequence * /*seq*/, float /*fac*/)
{
  return StripEarlyOut::NoInput;
}

static ImBuf *do_adjustment_impl(const SeqRenderData *context, Sequence *seq, float timeline_frame)
{
  Editing *ed;
  ImBuf *i = nullptr;

  ed = context->scene->ed;

  ListBase *seqbasep = SEQ_get_seqbase_by_seq(context->scene, seq);
  ListBase *channels = SEQ_get_channels_by_seq(&ed->seqbase, &ed->channels, seq);

  /* Clamp timeline_frame to strip range so it behaves as if it had "still frame" offset (last
   * frame is static after end of strip). This is how most strips behave. This way transition
   * effects that doesn't overlap or speed effect can't fail rendering outside of strip range. */
  timeline_frame = clamp_i(timeline_frame,
                           SEQ_time_left_handle_frame_get(context->scene, seq),
                           SEQ_time_right_handle_frame_get(context->scene, seq) - 1);

  if (seq->machine > 1) {
    i = seq_render_give_ibuf_seqbase(
        context, timeline_frame, seq->machine - 1, channels, seqbasep);
  }

  /* Found nothing? so let's work the way up the meta-strip stack, so
   * that it is possible to group a bunch of adjustment strips into
   * a meta-strip and have that work on everything below the meta-strip. */

  if (!i) {
    Sequence *meta;

    meta = SEQ_find_metastrip_by_sequence(&ed->seqbase, nullptr, seq);

    if (meta) {
      i = do_adjustment_impl(context, meta, timeline_frame);
    }
  }

  return i;
}

static ImBuf *do_adjustment(const SeqRenderData *context,
                            Sequence *seq,
                            float timeline_frame,
                            float /*fac*/,
                            ImBuf * /*ibuf1*/,
                            ImBuf * /*ibuf2*/)
{
  ImBuf *out;
  Editing *ed;

  ed = context->scene->ed;

  if (!ed) {
    return nullptr;
  }

  out = do_adjustment_impl(context, seq, timeline_frame);

  return out;
}

void adjustment_effect_get_handle(SeqEffectHandle &rval)
{
  rval.num_inputs = num_inputs_adjustment;
  rval.early_out = early_out_adjustment;
  rval.execute = do_adjustment;
}
