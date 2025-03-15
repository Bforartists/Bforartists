/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 * SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup imbuf
 */

#include "BLI_rect.h"
#include "BLI_task.hh"

#include "IMB_filter.hh"
#include "IMB_imbuf.hh"
#include "IMB_imbuf_types.hh"

#include "IMB_colormanagement.hh"
#include "IMB_colormanagement_intern.hh"

#include "MEM_guardedalloc.h"

/* -------------------------------------------------------------------- */

/** \name Generic Buffer Conversion
 * \{ */

MINLINE void ushort_to_byte_v4(uchar b[4], const ushort us[4])
{
  b[0] = unit_ushort_to_uchar(us[0]);
  b[1] = unit_ushort_to_uchar(us[1]);
  b[2] = unit_ushort_to_uchar(us[2]);
  b[3] = unit_ushort_to_uchar(us[3]);
}

MINLINE uchar ftochar(float value)
{
  return unit_float_to_uchar_clamp(value);
}

MINLINE void ushort_to_byte_dither_v4(uchar b[4], const ushort us[4], float dither, int x, int y)
{
#define USHORTTOFLOAT(val) (float(val) / 65535.0f)
  float dither_value = dither_random_value(x, y) * 0.0033f * dither;

  b[0] = ftochar(dither_value + USHORTTOFLOAT(us[0]));
  b[1] = ftochar(dither_value + USHORTTOFLOAT(us[1]));
  b[2] = ftochar(dither_value + USHORTTOFLOAT(us[2]));
  b[3] = unit_ushort_to_uchar(us[3]);

#undef USHORTTOFLOAT
}

MINLINE void float_to_byte_dither_v4(uchar b[4], const float f[4], float dither, int x, int y)
{
  float dither_value = dither_random_value(x, y) * 0.0033f * dither;

  b[0] = ftochar(dither_value + f[0]);
  b[1] = ftochar(dither_value + f[1]);
  b[2] = ftochar(dither_value + f[2]);
  b[3] = unit_float_to_uchar_clamp(f[3]);
}

bool IMB_alpha_affects_rgb(const ImBuf *ibuf)
{
  return ibuf && (ibuf->flags & IB_alphamode_channel_packed) == 0;
}

void IMB_buffer_byte_from_float(uchar *rect_to,
                                const float *rect_from,
                                int channels_from,
                                float dither,
                                int profile_to,
                                int profile_from,
                                bool predivide,
                                int width,
                                int height,
                                int stride_to,
                                int stride_from,
                                int start_y)
{
  float tmp[4];
  int x, y;

  /* we need valid profiles */
  BLI_assert(profile_to != IB_PROFILE_NONE);
  BLI_assert(profile_from != IB_PROFILE_NONE);

  for (y = 0; y < height; y++) {
    if (channels_from == 1) {
      /* single channel input */
      const float *from = rect_from + size_t(stride_from) * y;
      uchar *to = rect_to + size_t(stride_to) * y * 4;

      for (x = 0; x < width; x++, from++, to += 4) {
        to[0] = to[1] = to[2] = to[3] = unit_float_to_uchar_clamp(from[0]);
      }
    }
    else if (channels_from == 3) {
      /* RGB input */
      const float *from = rect_from + size_t(stride_from) * y * 3;
      uchar *to = rect_to + size_t(stride_to) * y * 4;

      if (profile_to == profile_from) {
        /* no color space conversion */
        for (x = 0; x < width; x++, from += 3, to += 4) {
          rgb_float_to_uchar(to, from);
          to[3] = 255;
        }
      }
      else if (profile_to == IB_PROFILE_SRGB) {
        /* convert from linear to sRGB */
        for (x = 0; x < width; x++, from += 3, to += 4) {
          linearrgb_to_srgb_v3_v3(tmp, from);
          rgb_float_to_uchar(to, tmp);
          to[3] = 255;
        }
      }
      else if (profile_to == IB_PROFILE_LINEAR_RGB) {
        /* convert from sRGB to linear */
        for (x = 0; x < width; x++, from += 3, to += 4) {
          srgb_to_linearrgb_v3_v3(tmp, from);
          rgb_float_to_uchar(to, tmp);
          to[3] = 255;
        }
      }
    }
    else if (channels_from == 4) {
      /* RGBA input */
      const float *from = rect_from + size_t(stride_from) * y * 4;
      uchar *to = rect_to + size_t(stride_to) * y * 4;

      if (profile_to == profile_from) {
        /* no color space conversion */
        if (dither && predivide) {
          float straight[4];
          for (x = 0; x < width; x++, from += 4, to += 4) {
            premul_to_straight_v4_v4(straight, from);
            float_to_byte_dither_v4(to, straight, dither, x, y + start_y);
          }
        }
        else if (dither) {
          for (x = 0; x < width; x++, from += 4, to += 4) {
            float_to_byte_dither_v4(to, from, dither, x, y + start_y);
          }
        }
        else if (predivide) {
          for (x = 0; x < width; x++, from += 4, to += 4) {
            premul_float_to_straight_uchar(to, from);
          }
        }
        else {
          for (x = 0; x < width; x++, from += 4, to += 4) {
            rgba_float_to_uchar(to, from);
          }
        }
      }
      else if (profile_to == IB_PROFILE_SRGB) {
        /* convert from linear to sRGB */
        ushort us[4];
        float straight[4];

        if (dither && predivide) {
          for (x = 0; x < width; x++, from += 4, to += 4) {
            premul_to_straight_v4_v4(straight, from);
            linearrgb_to_srgb_ushort4(us, from);
            ushort_to_byte_dither_v4(to, us, dither, x, y + start_y);
          }
        }
        else if (dither) {
          for (x = 0; x < width; x++, from += 4, to += 4) {
            linearrgb_to_srgb_ushort4(us, from);
            ushort_to_byte_dither_v4(to, us, dither, x, y + start_y);
          }
        }
        else if (predivide) {
          for (x = 0; x < width; x++, from += 4, to += 4) {
            premul_to_straight_v4_v4(straight, from);
            linearrgb_to_srgb_ushort4(us, from);
            ushort_to_byte_v4(to, us);
          }
        }
        else {
          for (x = 0; x < width; x++, from += 4, to += 4) {
            linearrgb_to_srgb_ushort4(us, from);
            ushort_to_byte_v4(to, us);
          }
        }
      }
      else if (profile_to == IB_PROFILE_LINEAR_RGB) {
        /* convert from sRGB to linear */
        if (dither && predivide) {
          for (x = 0; x < width; x++, from += 4, to += 4) {
            srgb_to_linearrgb_predivide_v4(tmp, from);
            float_to_byte_dither_v4(to, tmp, dither, x, y + start_y);
          }
        }
        else if (dither) {
          for (x = 0; x < width; x++, from += 4, to += 4) {
            srgb_to_linearrgb_v4(tmp, from);
            float_to_byte_dither_v4(to, tmp, dither, x, y + start_y);
          }
        }
        else if (predivide) {
          for (x = 0; x < width; x++, from += 4, to += 4) {
            srgb_to_linearrgb_predivide_v4(tmp, from);
            rgba_float_to_uchar(to, tmp);
          }
        }
        else {
          for (x = 0; x < width; x++, from += 4, to += 4) {
            srgb_to_linearrgb_v4(tmp, from);
            rgba_float_to_uchar(to, tmp);
          }
        }
      }
    }
  }
}

void IMB_buffer_byte_from_float_mask(uchar *rect_to,
                                     const float *rect_from,
                                     int channels_from,
                                     float dither,
                                     bool predivide,
                                     int width,
                                     int height,
                                     int stride_to,
                                     int stride_from,
                                     char *mask)
{
  int x, y;

  for (y = 0; y < height; y++) {
    if (channels_from == 1) {
      /* single channel input */
      const float *from = rect_from + size_t(stride_from) * y;
      uchar *to = rect_to + size_t(stride_to) * y * 4;

      for (x = 0; x < width; x++, from++, to += 4) {
        if (*mask++ == FILTER_MASK_USED) {
          to[0] = to[1] = to[2] = to[3] = unit_float_to_uchar_clamp(from[0]);
        }
      }
    }
    else if (channels_from == 3) {
      /* RGB input */
      const float *from = rect_from + size_t(stride_from) * y * 3;
      uchar *to = rect_to + size_t(stride_to) * y * 4;

      for (x = 0; x < width; x++, from += 3, to += 4) {
        if (*mask++ == FILTER_MASK_USED) {
          rgb_float_to_uchar(to, from);
          to[3] = 255;
        }
      }
    }
    else if (channels_from == 4) {
      /* RGBA input */
      const float *from = rect_from + size_t(stride_from) * y * 4;
      uchar *to = rect_to + size_t(stride_to) * y * 4;

      if (dither && predivide) {
        float straight[4];
        for (x = 0; x < width; x++, from += 4, to += 4) {
          if (*mask++ == FILTER_MASK_USED) {
            premul_to_straight_v4_v4(straight, from);
            float_to_byte_dither_v4(to, straight, dither, x, y);
          }
        }
      }
      else if (dither) {
        for (x = 0; x < width; x++, from += 4, to += 4) {
          if (*mask++ == FILTER_MASK_USED) {
            float_to_byte_dither_v4(to, from, dither, x, y);
          }
        }
      }
      else if (predivide) {
        for (x = 0; x < width; x++, from += 4, to += 4) {
          if (*mask++ == FILTER_MASK_USED) {
            premul_float_to_straight_uchar(to, from);
          }
        }
      }
      else {
        for (x = 0; x < width; x++, from += 4, to += 4) {
          if (*mask++ == FILTER_MASK_USED) {
            rgba_float_to_uchar(to, from);
          }
        }
      }
    }
  }
}

void IMB_buffer_float_from_byte(float *rect_to,
                                const uchar *rect_from,
                                int profile_to,
                                int profile_from,
                                bool predivide,
                                int width,
                                int height,
                                int stride_to,
                                int stride_from)
{
  float tmp[4];
  int x, y;

  /* we need valid profiles */
  BLI_assert(profile_to != IB_PROFILE_NONE);
  BLI_assert(profile_from != IB_PROFILE_NONE);

  /* RGBA input */
  for (y = 0; y < height; y++) {
    const uchar *from = rect_from + size_t(stride_from) * y * 4;
    float *to = rect_to + size_t(stride_to) * y * 4;

    if (profile_to == profile_from) {
      /* no color space conversion */
      for (x = 0; x < width; x++, from += 4, to += 4) {
        rgba_uchar_to_float(to, from);
      }
    }
    else if (profile_to == IB_PROFILE_LINEAR_RGB) {
      /* convert sRGB to linear */
      if (predivide) {
        for (x = 0; x < width; x++, from += 4, to += 4) {
          srgb_to_linearrgb_uchar4_predivide(to, from);
        }
      }
      else {
        for (x = 0; x < width; x++, from += 4, to += 4) {
          srgb_to_linearrgb_uchar4(to, from);
        }
      }
    }
    else if (profile_to == IB_PROFILE_SRGB) {
      /* convert linear to sRGB */
      if (predivide) {
        for (x = 0; x < width; x++, from += 4, to += 4) {
          rgba_uchar_to_float(tmp, from);
          linearrgb_to_srgb_predivide_v4(to, tmp);
        }
      }
      else {
        for (x = 0; x < width; x++, from += 4, to += 4) {
          rgba_uchar_to_float(tmp, from);
          linearrgb_to_srgb_v4(to, tmp);
        }
      }
    }
  }
}

void IMB_buffer_float_from_float(float *rect_to,
                                 const float *rect_from,
                                 int channels_from,
                                 int profile_to,
                                 int profile_from,
                                 bool predivide,
                                 int width,
                                 int height,
                                 int stride_to,
                                 int stride_from)
{
  int x, y;

  /* we need valid profiles */
  BLI_assert(profile_to != IB_PROFILE_NONE);
  BLI_assert(profile_from != IB_PROFILE_NONE);

  if (channels_from == 1) {
    /* single channel input */
    for (y = 0; y < height; y++) {
      const float *from = rect_from + size_t(stride_from) * y;
      float *to = rect_to + size_t(stride_to) * y * 4;

      for (x = 0; x < width; x++, from++, to += 4) {
        to[0] = to[1] = to[2] = to[3] = from[0];
      }
    }
  }
  else if (channels_from == 3) {
    /* RGB input */
    for (y = 0; y < height; y++) {
      const float *from = rect_from + size_t(stride_from) * y * 3;
      float *to = rect_to + size_t(stride_to) * y * 4;

      if (profile_to == profile_from) {
        /* no color space conversion */
        for (x = 0; x < width; x++, from += 3, to += 4) {
          copy_v3_v3(to, from);
          to[3] = 1.0f;
        }
      }
      else if (profile_to == IB_PROFILE_LINEAR_RGB) {
        /* convert from sRGB to linear */
        for (x = 0; x < width; x++, from += 3, to += 4) {
          srgb_to_linearrgb_v3_v3(to, from);
          to[3] = 1.0f;
        }
      }
      else if (profile_to == IB_PROFILE_SRGB) {
        /* convert from linear to sRGB */
        for (x = 0; x < width; x++, from += 3, to += 4) {
          linearrgb_to_srgb_v3_v3(to, from);
          to[3] = 1.0f;
        }
      }
    }
  }
  else if (channels_from == 4) {
    /* RGBA input */
    for (y = 0; y < height; y++) {
      const float *from = rect_from + size_t(stride_from) * y * 4;
      float *to = rect_to + size_t(stride_to) * y * 4;

      if (profile_to == profile_from) {
        /* same profile, copy */
        memcpy(to, from, sizeof(float) * size_t(4) * width);
      }
      else if (profile_to == IB_PROFILE_LINEAR_RGB) {
        /* convert to sRGB to linear */
        if (predivide) {
          for (x = 0; x < width; x++, from += 4, to += 4) {
            srgb_to_linearrgb_predivide_v4(to, from);
          }
        }
        else {
          for (x = 0; x < width; x++, from += 4, to += 4) {
            srgb_to_linearrgb_v4(to, from);
          }
        }
      }
      else if (profile_to == IB_PROFILE_SRGB) {
        /* convert from linear to sRGB */
        if (predivide) {
          for (x = 0; x < width; x++, from += 4, to += 4) {
            linearrgb_to_srgb_predivide_v4(to, from);
          }
        }
        else {
          for (x = 0; x < width; x++, from += 4, to += 4) {
            linearrgb_to_srgb_v4(to, from);
          }
        }
      }
    }
  }
}

void IMB_buffer_float_from_float_threaded(float *rect_to,
                                          const float *rect_from,
                                          int channels_from,
                                          int profile_to,
                                          int profile_from,
                                          bool predivide,
                                          int width,
                                          int height,
                                          int stride_to,
                                          int stride_from)
{
  using namespace blender;
  threading::parallel_for(IndexRange(height), 64, [&](const IndexRange y_range) {
    int64_t offset_from = y_range.first() * stride_from * channels_from;
    int64_t offset_to = y_range.first() * stride_to * 4;
    IMB_buffer_float_from_float(rect_to + offset_to,
                                rect_from + offset_from,
                                channels_from,
                                profile_to,
                                profile_from,
                                predivide,
                                width,
                                y_range.size(),
                                stride_to,
                                stride_from);
  });
}

void IMB_buffer_float_from_float_mask(float *rect_to,
                                      const float *rect_from,
                                      int channels_from,
                                      int width,
                                      int height,
                                      int stride_to,
                                      int stride_from,
                                      char *mask)
{
  int x, y;

  if (channels_from == 1) {
    /* single channel input */
    for (y = 0; y < height; y++) {
      const float *from = rect_from + size_t(stride_from) * y;
      float *to = rect_to + size_t(stride_to) * y * 4;

      for (x = 0; x < width; x++, from++, to += 4) {
        if (*mask++ == FILTER_MASK_USED) {
          to[0] = to[1] = to[2] = to[3] = from[0];
        }
      }
    }
  }
  else if (channels_from == 3) {
    /* RGB input */
    for (y = 0; y < height; y++) {
      const float *from = rect_from + size_t(stride_from) * y * 3;
      float *to = rect_to + size_t(stride_to) * y * 4;

      for (x = 0; x < width; x++, from += 3, to += 4) {
        if (*mask++ == FILTER_MASK_USED) {
          copy_v3_v3(to, from);
          to[3] = 1.0f;
        }
      }
    }
  }
  else if (channels_from == 4) {
    /* RGBA input */
    for (y = 0; y < height; y++) {
      const float *from = rect_from + size_t(stride_from) * y * 4;
      float *to = rect_to + size_t(stride_to) * y * 4;

      for (x = 0; x < width; x++, from += 4, to += 4) {
        if (*mask++ == FILTER_MASK_USED) {
          copy_v4_v4(to, from);
        }
      }
    }
  }
}

void IMB_buffer_byte_from_byte(uchar *rect_to,
                               const uchar *rect_from,
                               int profile_to,
                               int profile_from,
                               bool predivide,
                               int width,
                               int height,
                               int stride_to,
                               int stride_from)
{
  float tmp[4];
  int x, y;

  /* we need valid profiles */
  BLI_assert(profile_to != IB_PROFILE_NONE);
  BLI_assert(profile_from != IB_PROFILE_NONE);

  /* always RGBA input */
  for (y = 0; y < height; y++) {
    const uchar *from = rect_from + size_t(stride_from) * y * 4;
    uchar *to = rect_to + size_t(stride_to) * y * 4;

    if (profile_to == profile_from) {
      /* same profile, copy */
      memcpy(to, from, sizeof(uchar[4]) * width);
    }
    else if (profile_to == IB_PROFILE_LINEAR_RGB) {
      /* convert to sRGB to linear */
      if (predivide) {
        for (x = 0; x < width; x++, from += 4, to += 4) {
          rgba_uchar_to_float(tmp, from);
          srgb_to_linearrgb_predivide_v4(tmp, tmp);
          rgba_float_to_uchar(to, tmp);
        }
      }
      else {
        for (x = 0; x < width; x++, from += 4, to += 4) {
          rgba_uchar_to_float(tmp, from);
          srgb_to_linearrgb_v4(tmp, tmp);
          rgba_float_to_uchar(to, tmp);
        }
      }
    }
    else if (profile_to == IB_PROFILE_SRGB) {
      /* convert from linear to sRGB */
      if (predivide) {
        for (x = 0; x < width; x++, from += 4, to += 4) {
          rgba_uchar_to_float(tmp, from);
          linearrgb_to_srgb_predivide_v4(tmp, tmp);
          rgba_float_to_uchar(to, tmp);
        }
      }
      else {
        for (x = 0; x < width; x++, from += 4, to += 4) {
          rgba_uchar_to_float(tmp, from);
          linearrgb_to_srgb_v4(tmp, tmp);
          rgba_float_to_uchar(to, tmp);
        }
      }
    }
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name ImBuf Conversion
 * \{ */

void IMB_byte_from_float(ImBuf *ibuf)
{
  /* verify we have a float buffer */
  if (ibuf->float_buffer.data == nullptr) {
    return;
  }

  /* create byte rect if it didn't exist yet */
  if (ibuf->byte_buffer.data == nullptr) {
    if (IMB_alloc_byte_pixels(ibuf, false) == 0) {
      return;
    }
  }

  const char *from_colorspace = (ibuf->float_buffer.colorspace == nullptr) ?
                                    IMB_colormanagement_role_colorspace_name_get(
                                        COLOR_ROLE_SCENE_LINEAR) :
                                    ibuf->float_buffer.colorspace->name;
  const char *to_colorspace = (ibuf->byte_buffer.colorspace == nullptr) ?
                                  IMB_colormanagement_role_colorspace_name_get(
                                      COLOR_ROLE_DEFAULT_BYTE) :
                                  ibuf->byte_buffer.colorspace->name;

  float *buffer = static_cast<float *>(MEM_dupallocN(ibuf->float_buffer.data));

  /* first make float buffer in byte space */
  const bool predivide = IMB_alpha_affects_rgb(ibuf);
  IMB_colormanagement_transform_float(
      buffer, ibuf->x, ibuf->y, ibuf->channels, from_colorspace, to_colorspace, predivide);

  /* convert from float's premul alpha to byte's straight alpha */
  if (IMB_alpha_affects_rgb(ibuf)) {
    IMB_unpremultiply_rect_float(buffer, ibuf->channels, ibuf->x, ibuf->y);
  }

  /* convert float to byte */
  IMB_buffer_byte_from_float(ibuf->byte_buffer.data,
                             buffer,
                             ibuf->channels,
                             ibuf->dither,
                             IB_PROFILE_SRGB,
                             IB_PROFILE_SRGB,
                             false,
                             ibuf->x,
                             ibuf->y,
                             ibuf->x,
                             ibuf->x);

  MEM_freeN(buffer);

  /* ensure user flag is reset */
  ibuf->userflags &= ~IB_RECT_INVALID;
}

void IMB_float_from_byte_ex(ImBuf *dst, const ImBuf *src, const rcti *region_to_update)
{
  BLI_assert_msg(dst->float_buffer.data != nullptr,
                 "Destination buffer should have a float buffer assigned.");
  BLI_assert_msg(src->byte_buffer.data != nullptr,
                 "Source buffer should have a byte buffer assigned.");
  BLI_assert_msg(dst->x == src->x, "Source and destination buffer should have the same dimension");
  BLI_assert_msg(dst->y == src->y, "Source and destination buffer should have the same dimension");
  BLI_assert_msg(dst->channels = 4, "Destination buffer should have 4 channels.");
  BLI_assert_msg(region_to_update->xmin >= 0,
                 "Region to update should be clipped to the given buffers.");
  BLI_assert_msg(region_to_update->ymin >= 0,
                 "Region to update should be clipped to the given buffers.");
  BLI_assert_msg(region_to_update->xmax <= dst->x,
                 "Region to update should be clipped to the given buffers.");
  BLI_assert_msg(region_to_update->ymax <= dst->y,
                 "Region to update should be clipped to the given buffers.");

  float *rect_float = dst->float_buffer.data;
  rect_float += (region_to_update->xmin + region_to_update->ymin * dst->x) * 4;
  uchar *rect = src->byte_buffer.data;
  rect += (region_to_update->xmin + region_to_update->ymin * dst->x) * 4;
  const int region_width = BLI_rcti_size_x(region_to_update);
  const int region_height = BLI_rcti_size_y(region_to_update);

  /* Convert byte buffer to float buffer without color or alpha conversion. */
  IMB_buffer_float_from_byte(rect_float,
                             rect,
                             IB_PROFILE_SRGB,
                             IB_PROFILE_SRGB,
                             false,
                             region_width,
                             region_height,
                             src->x,
                             dst->x);

  /* Perform color space conversion from rect color space to linear. */
  float *float_ptr = rect_float;
  for (int i = 0; i < region_height; i++) {
    IMB_colormanagement_colorspace_to_scene_linear(
        float_ptr, region_width, 1, dst->channels, src->byte_buffer.colorspace, false);
    float_ptr += 4 * dst->x;
  }

  /* Perform alpha conversion. */
  if (IMB_alpha_affects_rgb(src)) {
    float_ptr = rect_float;
    for (int i = 0; i < region_height; i++) {
      IMB_premultiply_rect_float(float_ptr, dst->channels, region_width, 1);
      float_ptr += 4 * dst->x;
    }
  }
}

void IMB_float_from_byte(ImBuf *ibuf)
{
  /* verify if we byte and float buffers */
  if (ibuf->byte_buffer.data == nullptr) {
    return;
  }

  /* allocate float buffer outside of image buffer,
   * so work-in-progress color space conversion doesn't
   * interfere with other parts of blender
   */
  float *rect_float = ibuf->float_buffer.data;
  if (rect_float == nullptr) {
    rect_float = MEM_calloc_arrayN<float>(4 * IMB_get_pixel_count(ibuf), "IMB_float_from_byte");

    if (rect_float == nullptr) {
      return;
    }

    ibuf->channels = 4;

    IMB_assign_float_buffer(ibuf, rect_float, IB_TAKE_OWNERSHIP);
  }

  rcti region_to_update;
  BLI_rcti_init(&region_to_update, 0, ibuf->x, 0, ibuf->y);
  IMB_float_from_byte_ex(ibuf, ibuf, &region_to_update);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Color to Gray-Scale
 * \{ */

void IMB_color_to_bw(ImBuf *ibuf)
{
  float *rct_fl = ibuf->float_buffer.data;
  uchar *rct = ibuf->byte_buffer.data;
  size_t i;

  if (rct_fl) {
    if (ibuf->channels >= 3) {
      for (i = IMB_get_pixel_count(ibuf); i > 0; i--, rct_fl += ibuf->channels) {
        rct_fl[0] = rct_fl[1] = rct_fl[2] = IMB_colormanagement_get_luminance(rct_fl);
      }
    }
  }

  if (rct) {
    for (i = IMB_get_pixel_count(ibuf); i > 0; i--, rct += 4) {
      rct[0] = rct[1] = rct[2] = IMB_colormanagement_get_luminance_byte(rct);
    }
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Alter Saturation
 * \{ */

void IMB_saturation(ImBuf *ibuf, float sat)
{
  using namespace blender;

  const size_t pixel_count = IMB_get_pixel_count(ibuf);
  if (ibuf->byte_buffer.data != nullptr) {
    threading::parallel_for(IndexRange(pixel_count), 64 * 1024, [&](IndexRange range) {
      uchar *ptr = ibuf->byte_buffer.data + range.first() * 4;
      float rgb[3];
      float hsv[3];
      for ([[maybe_unused]] const int64_t i : range) {
        rgb_uchar_to_float(rgb, ptr);
        rgb_to_hsv_v(rgb, hsv);
        hsv_to_rgb(hsv[0], hsv[1] * sat, hsv[2], rgb + 0, rgb + 1, rgb + 2);
        rgb_float_to_uchar(ptr, rgb);
        ptr += 4;
      }
    });
  }

  if (ibuf->float_buffer.data != nullptr && ibuf->channels >= 3) {
    threading::parallel_for(IndexRange(pixel_count), 64 * 1024, [&](IndexRange range) {
      const int channels = ibuf->channels;
      float *ptr = ibuf->float_buffer.data + range.first() * channels;
      float hsv[3];
      for ([[maybe_unused]] const int64_t i : range) {
        rgb_to_hsv_v(ptr, hsv);
        hsv_to_rgb(hsv[0], hsv[1] * sat, hsv[2], ptr + 0, ptr + 1, ptr + 2);
        ptr += channels;
      }
    });
  }
}

/** \} */
