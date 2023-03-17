/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2001-2002 NaN Holding BV. All rights reserved. */

/** \file
 * \ingroup spseq
 */

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_math.h"

#include "DNA_anim_types.h"
#include "DNA_scene_types.h"

#include "BKE_context.h"
#include "BKE_report.h"
#include "BKE_scene.h"

#include "SEQ_iterator.h"
#include "SEQ_relations.h"
#include "SEQ_retiming.h"
#include "SEQ_retiming.hh"
#include "SEQ_sequencer.h"
#include "SEQ_time.h"
#include "SEQ_transform.h"

#include "WM_api.h"

#include "RNA_define.h"

#include "UI_interface.h"
#include "UI_view2d.h"

#include "DEG_depsgraph.h"

/* Own include. */
#include "sequencer_intern.h"

using blender::MutableSpan;

static bool retiming_poll(bContext *C)
{
  if (!sequencer_edit_poll(C)) {
    return false;
  }

  const Editing *ed = SEQ_editing_get(CTX_data_scene(C));
  Sequence *seq = ed->act_seq;

  if (seq != nullptr && !SEQ_retiming_is_allowed(seq)) {
    CTX_wm_operator_poll_msg_set(C, "This strip type can not be retimed");
    return false;
  }
  return true;
}

static void retiming_handle_overlap(Scene *scene, Sequence *seq)
{
  ListBase *seqbase = SEQ_active_seqbase_get(SEQ_editing_get(scene));
  SeqCollection *strips = SEQ_collection_create(__func__);
  SEQ_collection_append_strip(seq, strips);
  SeqCollection *dependant = SEQ_collection_create(__func__);
  SEQ_collection_expand(scene, seqbase, strips, SEQ_query_strip_effect_chain);
  SEQ_collection_remove_strip(seq, dependant);
  SEQ_transform_handle_overlap(scene, seqbase, strips, dependant, true);
  SEQ_collection_free(strips);
  SEQ_collection_free(dependant);
}

/*-------------------------------------------------------------------- */
/** \name Retiming Reset
 * \{ */

static int sequencer_retiming_reset_exec(bContext *C, wmOperator * /* op */)
{
  Scene *scene = CTX_data_scene(C);
  const Editing *ed = SEQ_editing_get(scene);
  Sequence *seq = ed->act_seq;

  SEQ_retiming_data_clear(seq);

  retiming_handle_overlap(scene, seq);
  WM_event_add_notifier(C, NC_SCENE | ND_SEQUENCER, scene);
  return OPERATOR_FINISHED;
}

void SEQUENCER_OT_retiming_reset(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Reset Retiming";
  ot->description = "Reset strip retiming";
  ot->idname = "SEQUENCER_OT_retiming_reset";

  /* api callbacks */
  ot->exec = sequencer_retiming_reset_exec;
  ot->poll = retiming_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Retiming Move Handle
 * \{ */

static SeqRetimingHandle *closest_retiming_handle_get(const bContext *C,
                                                      const Sequence *seq,
                                                      const float mouse_x)
{
  const View2D *v2d = UI_view2d_fromcontext(C);
  const Scene *scene = CTX_data_scene(C);
  int best_distance = INT_MAX;
  SeqRetimingHandle *closest_handle = nullptr;

  const float distance_threshold = UI_view2d_region_to_view_x(v2d, 10);
  const float mouse_x_view = UI_view2d_region_to_view_x(v2d, mouse_x);

  for (int i = 0; i < SEQ_retiming_handles_count(seq); i++) {
    SeqRetimingHandle *handle = seq->retiming_handles + i;
    const int distance = round_fl_to_int(
        fabsf(SEQ_retiming_handle_timeline_frame_get(scene, seq, handle) - mouse_x_view));

    if (distance < distance_threshold && distance < best_distance) {
      best_distance = distance;
      closest_handle = handle;
    }
  }
  return closest_handle;
}

static int sequencer_retiming_handle_move_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
  Scene *scene = CTX_data_scene(C);
  const Editing *ed = SEQ_editing_get(scene);
  Sequence *seq = ed->act_seq;

  int handle_index = 0;
  if (RNA_struct_property_is_set(op->ptr, "handle_index")) {
    handle_index = RNA_int_get(op->ptr, "handle_index");
  }

  /* Ensure retiming handle at left handle position. This way user gets more predictable result
   * when strips have offsets. */
  const int left_handle_frame = SEQ_time_left_handle_frame_get(scene, seq);
  if (SEQ_retiming_add_handle(scene, seq, left_handle_frame) != nullptr) {
    handle_index++; /* Advance index, because new handle was created. */
  }

  MutableSpan handles = SEQ_retiming_handles_get(seq);
  SeqRetimingHandle *handle = nullptr;
  if (RNA_struct_property_is_set(op->ptr, "handle_index")) {
    BLI_assert(handle_index < handles.size());
    handle = &handles[handle_index];
  }
  else {
    handle = closest_retiming_handle_get(C, seq, event->mval[0]);
  }

  if (handle == nullptr) {
    BKE_report(op->reports, RPT_ERROR, "No handle available");
    return OPERATOR_CANCELLED;
  }

  op->customdata = handle;
  WM_event_add_modal_handler(C, op);
  return OPERATOR_RUNNING_MODAL;
}

static int sequencer_retiming_handle_move_modal(bContext *C, wmOperator *op, const wmEvent *event)
{
  Scene *scene = CTX_data_scene(C);
  const ARegion *region = CTX_wm_region(C);
  const View2D *v2d = &region->v2d;
  const Editing *ed = SEQ_editing_get(scene);
  Sequence *seq = ed->act_seq;

  switch (event->type) {
    case MOUSEMOVE: {
      float mouse_x = UI_view2d_region_to_view_x(v2d, event->mval[0]);
      int offset = 0;

      SeqRetimingHandle *handle = (SeqRetimingHandle *)op->customdata;
      SeqRetimingHandle *handle_prev = handle - 1;

      /* Limit retiming handle movement. */
      int xmin = SEQ_retiming_handle_timeline_frame_get(scene, seq, handle_prev) + 1;
      mouse_x = max_ff(xmin, mouse_x);
      offset = mouse_x - SEQ_retiming_handle_timeline_frame_get(scene, seq, handle);

      SEQ_retiming_offset_handle(scene, seq, handle, offset);

      SEQ_relations_invalidate_cache_raw(scene, seq);
      WM_event_add_notifier(C, NC_SCENE | ND_SEQUENCER, scene);
      return OPERATOR_RUNNING_MODAL;
    }
    case LEFTMOUSE:
    case EVT_RETKEY:
    case EVT_SPACEKEY: {
      retiming_handle_overlap(scene, seq);
      DEG_id_tag_update(&scene->id, ID_RECALC_SEQUENCER_STRIPS);
      WM_event_add_notifier(C, NC_SCENE | ND_SEQUENCER, scene);
      return OPERATOR_FINISHED;
    }

    case EVT_ESCKEY:
    case RIGHTMOUSE: {
      WM_event_add_notifier(C, NC_SCENE | ND_SEQUENCER, scene);
      return OPERATOR_CANCELLED;
    }
  }
  return OPERATOR_RUNNING_MODAL;
}

void SEQUENCER_OT_retiming_handle_move(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Move Retiming Handle";
  ot->description = "Move retiming handle";
  ot->idname = "SEQUENCER_OT_retiming_handle_move";

  /* api callbacks */
  ot->invoke = sequencer_retiming_handle_move_invoke;
  ot->modal = sequencer_retiming_handle_move_modal;
  ot->poll = retiming_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  PropertyRNA *prop = RNA_def_int(ot->srna,
                                  "handle_index",
                                  0,
                                  0,
                                  INT_MAX,
                                  "Handle Index",
                                  "Index of handle to be moved",
                                  0,
                                  INT_MAX);
  RNA_def_property_flag(prop, PROP_HIDDEN);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Retiming Add Handle
 * \{ */

static int sequesequencer_retiming_handle_add_exec(bContext *C, wmOperator *op)
{
  Scene *scene = CTX_data_scene(C);
  const Editing *ed = SEQ_editing_get(scene);
  Sequence *seq = ed->act_seq;

  SEQ_retiming_data_ensure(seq);

  float timeline_frame;
  if (RNA_struct_property_is_set(op->ptr, "timeline_frame")) {
    timeline_frame = RNA_int_get(op->ptr, "timeline_frame");
  }
  else {
    timeline_frame = BKE_scene_frame_get(scene);
  }

  bool inserted = false;
  const float end_frame = seq->start + SEQ_time_strip_length_get(scene, seq);
  if (seq->start < timeline_frame && end_frame > timeline_frame) {
    SEQ_retiming_add_handle(scene, seq, timeline_frame);
    inserted = true;
  }

  WM_event_add_notifier(C, NC_SCENE | ND_SEQUENCER, scene);

  return inserted ? OPERATOR_FINISHED : OPERATOR_PASS_THROUGH;
}

void SEQUENCER_OT_retiming_handle_add(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Add Retiming Handle";
  ot->description = "Add retiming Handle";
  ot->idname = "SEQUENCER_OT_retiming_handle_add";

  /* api callbacks */
  ot->exec = sequesequencer_retiming_handle_add_exec;
  ot->poll = retiming_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_int(ot->srna,
              "timeline_frame",
              0,
              0,
              INT_MAX,
              "Timeline Frame",
              "Frame where handle will be added",
              0,
              INT_MAX);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Retiming Remove Handle
 * \{ */

static int sequencer_retiming_handle_remove_exec(bContext *C, wmOperator *op)
{
  Scene *scene = CTX_data_scene(C);
  const Editing *ed = SEQ_editing_get(scene);
  Sequence *seq = ed->act_seq;

  SeqRetimingHandle *handle = (SeqRetimingHandle *)op->customdata;
  SEQ_retiming_remove_handle(seq, handle);
  SEQ_relations_invalidate_cache_raw(scene, seq);
  WM_event_add_notifier(C, NC_SCENE | ND_SEQUENCER, scene);
  return OPERATOR_FINISHED;
}

static int sequencer_retiming_handle_remove_invoke(bContext *C,
                                                   wmOperator *op,
                                                   const wmEvent *event)
{
  const Scene *scene = CTX_data_scene(C);
  const Editing *ed = SEQ_editing_get(scene);
  const Sequence *seq = ed->act_seq;

  if (seq == nullptr) {
    return OPERATOR_CANCELLED;
  }

  MutableSpan handles = SEQ_retiming_handles_get(seq);
  SeqRetimingHandle *handle = nullptr;

  if (RNA_struct_property_is_set(op->ptr, "handle_index")) {
    const int handle_index = RNA_int_get(op->ptr, "handle_index");
    BLI_assert(handle_index < handles.size());
    handle = &handles[handle_index];
  }
  else {
    handle = closest_retiming_handle_get(C, seq, event->mval[0]);
  }

  if (handle == nullptr) {
    BKE_report(op->reports, RPT_ERROR, "No handle available");
    return OPERATOR_CANCELLED;
  }

  op->customdata = handle;
  return sequencer_retiming_handle_remove_exec(C, op);
}

void SEQUENCER_OT_retiming_handle_remove(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Remove Retiming Handle";
  ot->description = "Remove retiming handle";
  ot->idname = "SEQUENCER_OT_retiming_handle_remove";

  /* api callbacks */
  ot->invoke = sequencer_retiming_handle_remove_invoke;
  ot->exec = sequencer_retiming_handle_remove_exec;
  ot->poll = retiming_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* properties */
  PropertyRNA *prop = RNA_def_int(ot->srna,
                                  "handle_index",
                                  0,
                                  0,
                                  INT_MAX,
                                  "Handle Index",
                                  "Index of handle to be removed",
                                  0,
                                  INT_MAX);
  RNA_def_property_flag(prop, PROP_HIDDEN);
}

/** \} */
