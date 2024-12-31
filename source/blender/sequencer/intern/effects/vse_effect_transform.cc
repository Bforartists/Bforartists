/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup sequencer
 */

#include "BLI_math_rotation.h"

#include "DNA_sequence_types.h"
#include "DNA_space_types.h"

#include "IMB_imbuf.hh"
#include "IMB_interp.hh"

#include "SEQ_proxy.hh"
#include "SEQ_render.hh"

#include "effects.hh"

using namespace blender;

static void init_transform_effect(Sequence *seq)
{
  if (seq->effectdata) {
    MEM_freeN(seq->effectdata);
  }

  seq->effectdata = MEM_callocN(sizeof(TransformVars), "transformvars");

  TransformVars *transform = (TransformVars *)seq->effectdata;

  transform->ScalexIni = 1.0f;
  transform->ScaleyIni = 1.0f;

  transform->xIni = 0.0f;
  transform->yIni = 0.0f;

  transform->rotIni = 0.0f;

  transform->interpolation = 1;
  transform->percent = 1;
  transform->uniform_scale = 0;
}

static int num_inputs_transform()
{
  return 1;
}

static void free_transform_effect(Sequence *seq, const bool /*do_id_user*/)
{
  MEM_SAFE_FREE(seq->effectdata);
}

static void copy_transform_effect(Sequence *dst, const Sequence *src, const int /*flag*/)
{
  dst->effectdata = MEM_dupallocN(src->effectdata);
}

static void transform_image(int x,
                            int y,
                            int start_line,
                            int total_lines,
                            const ImBuf *ibuf,
                            ImBuf *out,
                            float scale_x,
                            float scale_y,
                            float translate_x,
                            float translate_y,
                            float rotate,
                            int interpolation)
{
  /* Rotate */
  float s = sinf(rotate);
  float c = cosf(rotate);

  float4 *dst_fl = reinterpret_cast<float4 *>(out->float_buffer.data);
  uchar4 *dst_ch = reinterpret_cast<uchar4 *>(out->byte_buffer.data);

  size_t offset = size_t(x) * start_line;
  for (int yi = start_line; yi < start_line + total_lines; yi++) {
    for (int xi = 0; xi < x; xi++) {
      /* Translate point. */
      float xt = xi - translate_x;
      float yt = yi - translate_y;

      /* Rotate point with center ref. */
      float xr = c * xt + s * yt;
      float yr = -s * xt + c * yt;

      /* Scale point with center ref. */
      xt = xr / scale_x;
      yt = yr / scale_y;

      /* Undo reference center point. */
      xt += (x / 2.0f);
      yt += (y / 2.0f);

      /* interpolate */
      switch (interpolation) {
        case 0:
          if (dst_fl) {
            dst_fl[offset] = imbuf::interpolate_nearest_border_fl(ibuf, xt, yt);
          }
          else {
            dst_ch[offset] = imbuf::interpolate_nearest_border_byte(ibuf, xt, yt);
          }
          break;
        case 1:
          if (dst_fl) {
            dst_fl[offset] = imbuf::interpolate_bilinear_border_fl(ibuf, xt, yt);
          }
          else {
            dst_ch[offset] = imbuf::interpolate_bilinear_border_byte(ibuf, xt, yt);
          }
          break;
        case 2:
          if (dst_fl) {
            dst_fl[offset] = imbuf::interpolate_cubic_bspline_fl(ibuf, xt, yt);
          }
          else {
            dst_ch[offset] = imbuf::interpolate_cubic_bspline_byte(ibuf, xt, yt);
          }
          break;
      }
      offset++;
    }
  }
}

static void do_transform_effect(const SeqRenderData *context,
                                Sequence *seq,
                                float /*timeline_frame*/,
                                float /*fac*/,
                                const ImBuf *ibuf1,
                                const ImBuf * /*ibuf2*/,
                                int start_line,
                                int total_lines,
                                ImBuf *out)
{
  TransformVars *transform = (TransformVars *)seq->effectdata;
  float scale_x, scale_y, translate_x, translate_y, rotate_radians;

  /* Scale */
  if (transform->uniform_scale) {
    scale_x = scale_y = transform->ScalexIni;
  }
  else {
    scale_x = transform->ScalexIni;
    scale_y = transform->ScaleyIni;
  }

  int x = context->rectx;
  int y = context->recty;

  /* Translate */
  if (!transform->percent) {
    /* Compensate text size for preview render size. */
    double proxy_size_comp = context->scene->r.size / 100.0;
    if (context->preview_render_size != SEQ_RENDER_SIZE_SCENE) {
      proxy_size_comp = SEQ_rendersize_to_scale_factor(context->preview_render_size);
    }

    translate_x = transform->xIni * proxy_size_comp + (x / 2.0f);
    translate_y = transform->yIni * proxy_size_comp + (y / 2.0f);
  }
  else {
    translate_x = x * (transform->xIni / 100.0f) + (x / 2.0f);
    translate_y = y * (transform->yIni / 100.0f) + (y / 2.0f);
  }

  /* Rotate */
  rotate_radians = DEG2RADF(transform->rotIni);

  transform_image(x,
                  y,
                  start_line,
                  total_lines,
                  ibuf1,
                  out,
                  scale_x,
                  scale_y,
                  translate_x,
                  translate_y,
                  rotate_radians,
                  transform->interpolation);
}

void transform_effect_get_handle(SeqEffectHandle &rval)
{
  rval.multithreaded = true;
  rval.init = init_transform_effect;
  rval.num_inputs = num_inputs_transform;
  rval.free = free_transform_effect;
  rval.copy = copy_transform_effect;
  rval.execute_slice = do_transform_effect;
}
