/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spseq
 */

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_span.hh"

#include "DNA_anim_types.h"
#include "DNA_sequence_types.h"

#include "BKE_context.h"
#include "BKE_fcurve.h"
#include "BKE_scene.h"

#include "BLF_api.h"

#include "GPU_batch.h"
#include "GPU_batch_utils.h"
#include "GPU_immediate.h"
#include "GPU_immediate_util.h"
#include "GPU_matrix.h"
#include "GPU_select.h"
#include "GPU_state.h"

#include "RNA_access.hh"
#include "RNA_define.hh"
#include "RNA_enum_types.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "ED_keyframes_draw.hh"
#include "ED_keyframes_keylist.hh"
#include "ED_screen.hh"
#include "ED_sequencer.hh"
#include "ED_view3d.hh"

#include "UI_interface.hh"
#include "UI_interface_icons.hh"
#include "UI_resources.hh"
#include "UI_view2d.hh"

#include "SEQ_iterator.hh"
#include "SEQ_retiming.hh"
#include "SEQ_sequencer.hh"
#include "SEQ_time.hh"

/* Own include. */
#include "sequencer_intern.hh"

#define KEY_SIZE (10 * U.pixelsize)
#define KEY_CENTER (UI_view2d_view_to_region_y(v2d, strip_y_rescale(seq, 0.0f)) + 4 + KEY_SIZE / 2)

bool retiming_keys_are_visible(const bContext *C)
{
  const SpaceSeq *sseq = CTX_wm_space_seq(C);
  return (sseq->timeline_overlay.flag & SEQ_TIMELINE_SHOW_STRIP_RETIMING) != 0;
}

static float strip_y_rescale(const Sequence *seq, const float y_value)
{
  const float y_range = SEQ_STRIP_OFSTOP - SEQ_STRIP_OFSBOTTOM;
  return (y_value * y_range) + seq->machine + SEQ_STRIP_OFSBOTTOM;
}

static float key_x_get(const Scene *scene, const Sequence *seq, const SeqRetimingKey *key)
{
  if (SEQ_retiming_is_last_key(seq, key)) {
    return SEQ_retiming_key_timeline_frame_get(scene, seq, key) + 1;
  }
  return SEQ_retiming_key_timeline_frame_get(scene, seq, key);
}

static float pixels_to_view_width(const bContext *C, const float width)
{
  const View2D *v2d = UI_view2d_fromcontext(C);
  float scale_x = UI_view2d_view_to_region_x(v2d, 1) - UI_view2d_view_to_region_x(v2d, 0.0f);
  return width / scale_x;
}

static float pixels_to_view_height(const bContext *C, const float height)
{
  const View2D *v2d = UI_view2d_fromcontext(C);
  float scale_y = UI_view2d_view_to_region_y(v2d, 1) - UI_view2d_view_to_region_y(v2d, 0.0f);
  return height / scale_y;
}

static float strip_start_screenspace_get(const bContext *C, const Sequence *seq)
{
  const View2D *v2d = UI_view2d_fromcontext(C);
  const Scene *scene = CTX_data_scene(C);
  return UI_view2d_view_to_region_x(v2d, SEQ_time_left_handle_frame_get(scene, seq));
}

static float strip_end_screenspace_get(const bContext *C, const Sequence *seq)
{
  const View2D *v2d = UI_view2d_fromcontext(C);
  const Scene *scene = CTX_data_scene(C);
  return UI_view2d_view_to_region_x(v2d, SEQ_time_right_handle_frame_get(scene, seq));
}

static rctf strip_box_get(const bContext *C, const Sequence *seq)
{
  const View2D *v2d = UI_view2d_fromcontext(C);
  rctf rect;
  rect.xmin = strip_start_screenspace_get(C, seq);
  rect.xmax = strip_end_screenspace_get(C, seq);
  rect.ymin = UI_view2d_view_to_region_y(v2d, strip_y_rescale(seq, 0));
  rect.ymax = UI_view2d_view_to_region_y(v2d, strip_y_rescale(seq, 1));
  return rect;
}

blender::Vector<Sequence *> sequencer_visible_strips_get(const bContext *C)
{
  const View2D *v2d = UI_view2d_fromcontext(C);
  const Scene *scene = CTX_data_scene(C);
  const Editing *ed = SEQ_editing_get(CTX_data_scene(C));
  blender::Vector<Sequence *> strips;

  LISTBASE_FOREACH (Sequence *, seq, ed->seqbasep) {
    if (min_ii(SEQ_time_left_handle_frame_get(scene, seq), SEQ_time_start_frame_get(seq)) >
        v2d->cur.xmax)
    {
      continue;
    }
    if (max_ii(SEQ_time_right_handle_frame_get(scene, seq),
               SEQ_time_content_end_frame_get(scene, seq)) < v2d->cur.xmin)
    {
      continue;
    }
    if (seq->machine + 1.0f < v2d->cur.ymin) {
      continue;
    }
    if (seq->machine > v2d->cur.ymax) {
      continue;
    }
    strips.append(seq);
  }
  return strips;
}

/** Size in pixels. */
#define RETIME_KEY_MOUSEOVER_THRESHOLD (16.0f * UI_SCALE_FAC)

static rctf keys_box_get(const bContext *C, const Sequence *seq)
{
  const View2D *v2d = UI_view2d_fromcontext(C);
  rctf rect = strip_box_get(C, seq);
  rect.ymax = KEY_CENTER + KEY_SIZE / 2;
  rect.ymin = KEY_CENTER - KEY_SIZE / 2;
  rect.xmax += RETIME_KEY_MOUSEOVER_THRESHOLD;
  rect.xmin -= RETIME_KEY_MOUSEOVER_THRESHOLD;
  return rect;
}

int left_fake_key_frame_get(const bContext *C, const Sequence *seq)
{
  const Scene *scene = CTX_data_scene(C);
  const int content_start = SEQ_time_start_frame_get(seq);
  return max_ii(content_start, SEQ_time_left_handle_frame_get(scene, seq));
}

int right_fake_key_frame_get(const bContext *C, const Sequence *seq)
{
  const Scene *scene = CTX_data_scene(C);
  const int content_end = SEQ_time_content_end_frame_get(scene, seq);
  return min_ii(content_end, SEQ_time_right_handle_frame_get(scene, seq));
}

static bool retiming_fake_key_is_clicked(const bContext *C,
                                         const Sequence *seq,
                                         const int key_timeline_frame,
                                         const int mval[2])
{
  const View2D *v2d = UI_view2d_fromcontext(C);

  rctf box = keys_box_get(C, seq);
  if (!BLI_rctf_isect_pt(&box, mval[0], mval[1])) {
    return false;
  }

  const float key_pos = UI_view2d_view_to_region_x(v2d, key_timeline_frame);
  const float distance = fabs(key_pos - mval[0]);
  return distance < RETIME_KEY_MOUSEOVER_THRESHOLD;
}

SeqRetimingKey *try_to_realize_virtual_key(const bContext *C, Sequence *seq, const int mval[2])
{
  Scene *scene = CTX_data_scene(C);
  SeqRetimingKey *key = nullptr;

  if (retiming_fake_key_is_clicked(C, seq, left_fake_key_frame_get(C, seq), mval)) {
    SEQ_retiming_data_ensure(seq);
    int frame = SEQ_time_left_handle_frame_get(scene, seq);
    key = SEQ_retiming_add_key(scene, seq, frame);
  }
  if (retiming_fake_key_is_clicked(C, seq, right_fake_key_frame_get(C, seq), mval)) {
    SEQ_retiming_data_ensure(seq);
    const int frame = SEQ_time_right_handle_frame_get(scene, seq);
    key = SEQ_retiming_add_key(scene, seq, frame);
  }

  return key;
}

static SeqRetimingKey *mouse_over_key_get_from_strip(const bContext *C,
                                                     const Sequence *seq,
                                                     const int mval[2])
{
  const Scene *scene = CTX_data_scene(C);
  const View2D *v2d = UI_view2d_fromcontext(C);

  int best_distance = INT_MAX;
  SeqRetimingKey *best_key = nullptr;

  for (SeqRetimingKey &key : SEQ_retiming_keys_get(seq)) {
    int distance = round_fl_to_int(
        fabsf(UI_view2d_view_to_region_x(v2d, key_x_get(scene, seq, &key)) - mval[0]));

    if (distance < RETIME_KEY_MOUSEOVER_THRESHOLD && distance < best_distance) {
      best_distance = distance;
      best_key = &key;
    }
  }

  return best_key;
}

SeqRetimingKey *retiming_mousover_key_get(const bContext *C, const int mval[2], Sequence **r_seq)
{
  for (Sequence *seq : sequencer_visible_strips_get(C)) {

    rctf box = keys_box_get(C, seq);
    if (!BLI_rctf_isect_pt(&box, mval[0], mval[1])) {
      continue;
    }

    if (r_seq != nullptr) {
      *r_seq = seq;
    }

    SeqRetimingKey *key = mouse_over_key_get_from_strip(C, seq, mval);

    if (key == nullptr) {
      continue;
    }

    return key;
  }

  return nullptr;
}

/* -------------------------------------------------------------------- */
/** \name Retiming Key
 * \{ */

static void retime_key_draw(const bContext *C, const Sequence *seq, const SeqRetimingKey *key)
{
  const Scene *scene = CTX_data_scene(C);
  const float key_x = key_x_get(scene, seq, key);

  const View2D *v2d = UI_view2d_fromcontext(C);
  const rctf strip_box = strip_box_get(C, seq);
  if (!BLI_rctf_isect_x(&strip_box, UI_view2d_view_to_region_x(v2d, key_x))) {
    return; /* Key out of the strip bounds. */
  }

  GPUVertFormat *format = immVertexFormat();
  KeyframeShaderBindings sh_bindings;

  sh_bindings.pos_id = GPU_vertformat_attr_add(format, "pos", GPU_COMP_F32, 2, GPU_FETCH_FLOAT);
  sh_bindings.size_id = GPU_vertformat_attr_add(format, "size", GPU_COMP_F32, 1, GPU_FETCH_FLOAT);
  sh_bindings.color_id = GPU_vertformat_attr_add(
      format, "color", GPU_COMP_U8, 4, GPU_FETCH_INT_TO_FLOAT_UNIT);
  sh_bindings.outline_color_id = GPU_vertformat_attr_add(
      format, "outlineColor", GPU_COMP_U8, 4, GPU_FETCH_INT_TO_FLOAT_UNIT);
  sh_bindings.flags_id = GPU_vertformat_attr_add(format, "flags", GPU_COMP_U32, 1, GPU_FETCH_INT);

  GPU_blend(GPU_BLEND_ALPHA);
  GPU_program_point_size(true);
  immBindBuiltinProgram(GPU_SHADER_KEYFRAME_SHAPE);
  immUniform1f("outline_scale", 1.0f);
  immUniform2f("ViewportSize", BLI_rcti_size_x(&v2d->mask) + 1, BLI_rcti_size_y(&v2d->mask) + 1);
  immBegin(GPU_PRIM_POINTS, 1);

  eBezTriple_KeyframeType key_type = BEZT_KEYTYPE_KEYFRAME;
  if (SEQ_retiming_key_is_freeze_frame(key)) {
    key_type = BEZT_KEYTYPE_BREAKDOWN;
  }
  if (SEQ_retiming_key_is_transition_type(key)) {
    key_type = BEZT_KEYTYPE_MOVEHOLD;
  }

  const bool is_selected = SEQ_retiming_selection_contains(SEQ_editing_get(scene), key);
  const int size = KEY_SIZE;
  const float bottom = KEY_CENTER;

  /* Ensure, that key is always inside of strip. */
  const float right_pos_max = UI_view2d_view_to_region_x(
                                  v2d, SEQ_time_right_handle_frame_get(scene, seq)) -
                              (size / 2);
  const float left_pos_min = UI_view2d_view_to_region_x(
                                 v2d, SEQ_time_left_handle_frame_get(scene, seq)) +
                             (size / 2);
  float key_position = UI_view2d_view_to_region_x(v2d, key_x);
  CLAMP(key_position, left_pos_min, right_pos_max);
  const float alpha = SEQ_retiming_data_is_editable(seq) ? 1.0f : 0.3f;

  draw_keyframe_shape(key_position,
                      bottom,
                      size,
                      is_selected && SEQ_retiming_data_is_editable(seq),
                      key_type,
                      KEYFRAME_SHAPE_BOTH,
                      alpha,
                      &sh_bindings,
                      0,
                      0);
  immEnd();
  GPU_program_point_size(false);
  immUnbindProgram();
  GPU_blend(GPU_BLEND_NONE);
}

static void draw_continuity(const bContext *C, const Sequence *seq, const SeqRetimingKey *key)
{
  const View2D *v2d = UI_view2d_fromcontext(C);
  const Scene *scene = CTX_data_scene(C);
  const Editing *ed = SEQ_editing_get(scene);

  if (key_x_get(scene, seq, key) == SEQ_time_left_handle_frame_get(scene, seq) ||
      key->strip_frame_index == 0)
  {
    return;
  }

  const float left_handle_position = UI_view2d_view_to_region_x(
      v2d, SEQ_time_left_handle_frame_get(scene, seq));
  const float right_handle_position = UI_view2d_view_to_region_x(
      v2d, SEQ_time_right_handle_frame_get(scene, seq));

  float key_position = UI_view2d_view_to_region_x(v2d, key_x_get(scene, seq, key));
  float prev_key_position = UI_view2d_view_to_region_x(v2d, key_x_get(scene, seq, key - 1));
  prev_key_position = max_ff(prev_key_position, left_handle_position);
  key_position = min_ff(key_position, right_handle_position);

  const int size = KEY_SIZE;
  const float y_center = KEY_CENTER;

  const float width_fac = 0.5f;
  const float bottom = y_center - size * width_fac;
  const float top = y_center + size * width_fac;

  GPU_blend(GPU_BLEND_ALPHA);
  uint pos = GPU_vertformat_attr_add(immVertexFormat(), "pos", GPU_COMP_F32, 2, GPU_FETCH_FLOAT);
  immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);

  if (SEQ_retiming_data_is_editable(seq) &&
      (SEQ_retiming_selection_contains(ed, key) || SEQ_retiming_selection_contains(ed, key - 1)))
  {
    immUniform4f("color", 0.65f, 0.5f, 0.2f, 1.0f);
  }
  else {
    immUniform4f("color", 0.0f, 0.0f, 0.0f, 0.1f);
  }
  immRectf(pos, prev_key_position, bottom, key_position, top);
  immUnbindProgram();
  GPU_blend(GPU_BLEND_NONE);
}

/* If there are no keys, draw fake keys and create real key when they are selected. */
/* TODO: would be nice to draw continuity between fake keys. */
static void fake_keys_draw(const bContext *C, Sequence *seq)
{
  if (!SEQ_retiming_is_active(seq) && !SEQ_retiming_data_is_editable(seq)) {
    return;
  }

  const Scene *scene = CTX_data_scene(C);
  const int left_key_frame = left_fake_key_frame_get(C, seq);
  const int right_key_frame = right_fake_key_frame_get(C, seq);

  if (SEQ_retiming_key_get_by_timeline_frame(scene, seq, left_key_frame) == nullptr) {
    SeqRetimingKey fake_key;
    fake_key.strip_frame_index = left_key_frame - SEQ_time_start_frame_get(seq);
    fake_key.flag = 0;
    retime_key_draw(C, seq, &fake_key);
  }

  if (SEQ_retiming_key_get_by_timeline_frame(scene, seq, right_key_frame) == nullptr) {
    SeqRetimingKey fake_key;
    fake_key.strip_frame_index = right_key_frame - SEQ_time_start_frame_get(seq);
    fake_key.flag = 0;
    retime_key_draw(C, seq, &fake_key);
  }
}

static void retime_keys_draw(const bContext *C)
{
  const Scene *scene = CTX_data_scene(C);
  if (scene->ed == nullptr) {
    return;
  }

  if (!retiming_keys_are_visible(C)) {
    return;
  }

  wmOrtho2_region_pixelspace(CTX_wm_region(C));

  for (Sequence *seq : sequencer_visible_strips_get(C)) {
    if (!SEQ_retiming_is_allowed(seq)) {
      continue;
    }

    for (const SeqRetimingKey &key : SEQ_retiming_keys_get(seq)) {
      draw_continuity(C, seq, &key);
    }

    fake_keys_draw(C, seq);
    for (const SeqRetimingKey &key : SEQ_retiming_keys_get(seq)) {
      retime_key_draw(C, seq, &key);
    }
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Retiming Speed Label
 * \{ */

static size_t label_str_get(const Sequence *seq,
                            const SeqRetimingKey *key,
                            char *r_label_str,
                            const size_t label_str_maxncpy)
{
  const SeqRetimingKey *next_key = key + 1;
  if (SEQ_retiming_key_is_transition_start(key)) {
    const float prev_speed = SEQ_retiming_key_speed_get(seq, key);
    const float next_speed = SEQ_retiming_key_speed_get(seq, next_key + 1);
    return BLI_snprintf_rlen(r_label_str,
                             label_str_maxncpy,
                             "%d%% - %d%%",
                             round_fl_to_int(prev_speed * 100.0f),
                             round_fl_to_int(next_speed * 100.0f));
  }
  const float speed = SEQ_retiming_key_speed_get(seq, next_key);
  return BLI_snprintf_rlen(
      r_label_str, label_str_maxncpy, "%d%%", round_fl_to_int(speed * 100.0f));
}

static bool label_rect_get(const bContext *C,
                           const Sequence *seq,
                           const SeqRetimingKey *key,
                           char *label_str,
                           const size_t label_len,
                           rctf *rect)
{
  const Scene *scene = CTX_data_scene(C);
  const SeqRetimingKey *next_key = key + 1;
  const float width = pixels_to_view_width(C, BLF_width(BLF_default(), label_str, label_len));
  const float height = pixels_to_view_height(C, BLF_height(BLF_default(), label_str, label_len));

  const float xmin = max_ff(SEQ_time_left_handle_frame_get(scene, seq),
                            key_x_get(scene, seq, key));
  const float xmax = min_ff(SEQ_time_right_handle_frame_get(scene, seq),
                            key_x_get(scene, seq, next_key));

  rect->xmin = (xmin + xmax - width) / 2;
  rect->xmax = rect->xmin + width;
  rect->ymin = strip_y_rescale(seq, 0) + pixels_to_view_height(C, 5);
  rect->ymax = rect->ymin + height;

  return width < xmax - xmin - pixels_to_view_width(C, KEY_SIZE);
}

static void retime_speed_text_draw(const bContext *C,
                                   const Sequence *seq,
                                   const SeqRetimingKey *key)
{
  if (SEQ_retiming_is_last_key(seq, key)) {
    return;
  }

  const Scene *scene = CTX_data_scene(C);
  const int start_frame = SEQ_time_left_handle_frame_get(scene, seq);
  const int end_frame = SEQ_time_right_handle_frame_get(scene, seq);

  const SeqRetimingKey *next_key = key + 1;
  if (key_x_get(scene, seq, next_key) < start_frame || key_x_get(scene, seq, key) > end_frame) {
    return; /* Label out of strip bounds. */
  }

  char label_str[40];
  rctf label_rect;
  size_t label_len = label_str_get(seq, key, label_str, sizeof(label_str));

  if (!label_rect_get(C, seq, key, label_str, label_len, &label_rect)) {
    return; /* Not enough space to draw the label. */
  }

  uchar col[4] = {255, 255, 255, 255};
  if ((seq->flag & SELECT) == 0) {
    memset(col, 0, sizeof(col));
    col[3] = 255;
  }

  UI_view2d_text_cache_add(
      UI_view2d_fromcontext(C), label_rect.xmin, label_rect.ymin, label_str, label_len, col);
}

static void retime_speed_draw(const bContext *C)
{
  const Scene *scene = CTX_data_scene(C);
  if (scene->ed == nullptr) {
    return;
  }

  if (!retiming_keys_are_visible(C)) {
    return;
  }

  const View2D *v2d = UI_view2d_fromcontext(C);

  wmOrtho2_region_pixelspace(CTX_wm_region(C));
  GPU_blend(GPU_BLEND_ALPHA);
  GPU_vertformat_attr_add(immVertexFormat(), "pos", GPU_COMP_F32, 2, GPU_FETCH_FLOAT);
  immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);

  for (const Sequence *seq : sequencer_visible_strips_get(C)) {
    for (const SeqRetimingKey &key : SEQ_retiming_keys_get(seq)) {
      retime_speed_text_draw(C, seq, &key);
    }
  }

  immUnbindProgram();
  GPU_blend(GPU_BLEND_NONE);

  UI_view2d_text_cache_draw(CTX_wm_region(C));
  UI_view2d_view_ortho(v2d); /* 'UI_view2d_text_cache_draw()' messes up current view. */
}

/** \} */

void sequencer_draw_retiming(const bContext *C)
{
  retime_keys_draw(C);
  retime_speed_draw(C);
}
