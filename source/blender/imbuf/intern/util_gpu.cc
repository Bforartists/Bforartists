/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup imbuf
 */

#include "imbuf.h"

#include "BLI_utildefines.h"
#include "MEM_guardedalloc.h"

#include "BKE_global.h"

#include "GPU_capabilities.h"
#include "GPU_state.h"
#include "GPU_texture.h"

#include "IMB_colormanagement.h"
#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

/* gpu ibuf utils */

static bool imb_is_grayscale_texture_format_compatible(const ImBuf *ibuf)
{
  if (ibuf->byte_buffer.data && !ibuf->float_buffer.data) {
    /* TODO: Support grayscale byte buffers.
     * The challenge is that Blender always stores byte images as RGBA. */
    return false;
  }

  if (ibuf->channels != 1) {
    return false;
  }

  /* Only imbufs with colorspace that do not modify the chrominance of the texture data relative
   * to the scene color space can be uploaded as single channel textures. */
  if (IMB_colormanagement_space_is_data(ibuf->float_buffer.colorspace) ||
      IMB_colormanagement_space_is_srgb(ibuf->float_buffer.colorspace) ||
      IMB_colormanagement_space_is_scene_linear(ibuf->float_buffer.colorspace))
  {
    return true;
  }
  return false;
}

static void imb_gpu_get_format(const ImBuf *ibuf,
                               bool high_bitdepth,
                               bool use_grayscale,
                               eGPUDataFormat *r_data_format,
                               eGPUTextureFormat *r_texture_format)
{
  const bool float_rect = (ibuf->float_buffer.data != nullptr);
  const bool is_grayscale = use_grayscale && imb_is_grayscale_texture_format_compatible(ibuf);

  if (float_rect) {
    /* Float. */
    const bool use_high_bitdepth = (!(ibuf->flags & IB_halffloat) && high_bitdepth);
    *r_data_format = GPU_DATA_FLOAT;
    *r_texture_format = is_grayscale ? (use_high_bitdepth ? GPU_R32F : GPU_R16F) :
                                       (use_high_bitdepth ? GPU_RGBA32F : GPU_RGBA16F);
  }
  else {
    if (IMB_colormanagement_space_is_data(ibuf->byte_buffer.colorspace) ||
        IMB_colormanagement_space_is_scene_linear(ibuf->byte_buffer.colorspace))
    {
      /* Non-color data or scene linear, just store buffer as is. */
      *r_data_format = GPU_DATA_UBYTE;
      *r_texture_format = (is_grayscale) ? GPU_R8 : GPU_RGBA8;
    }
    else if (IMB_colormanagement_space_is_srgb(ibuf->byte_buffer.colorspace)) {
      /* sRGB, store as byte texture that the GPU can decode directly. */
      *r_data_format = (is_grayscale) ? GPU_DATA_FLOAT : GPU_DATA_UBYTE;
      *r_texture_format = (is_grayscale) ? GPU_R16F : GPU_SRGB8_A8;
    }
    else {
      /* Other colorspace, store as half float texture to avoid precision loss. */
      *r_data_format = GPU_DATA_FLOAT;
      *r_texture_format = (is_grayscale) ? GPU_R16F : GPU_RGBA16F;
    }
  }
}

static const char *imb_gpu_get_swizzle(const ImBuf *ibuf)
{
  return imb_is_grayscale_texture_format_compatible(ibuf) ? "rrra" : "rgba";
}

/* Return false if no suitable format was found. */
static bool IMB_gpu_get_compressed_format(const ImBuf *ibuf, eGPUTextureFormat *r_texture_format)
{
  /* For DDS we only support data, scene linear and sRGB. Converting to
   * different colorspace would break the compression. */
  const bool use_srgb = (!IMB_colormanagement_space_is_data(ibuf->byte_buffer.colorspace) &&
                         !IMB_colormanagement_space_is_scene_linear(ibuf->byte_buffer.colorspace));

  if (ibuf->dds_data.fourcc == FOURCC_DXT1) {
    *r_texture_format = (use_srgb) ? GPU_SRGB8_A8_DXT1 : GPU_RGBA8_DXT1;
  }
  else if (ibuf->dds_data.fourcc == FOURCC_DXT3) {
    *r_texture_format = (use_srgb) ? GPU_SRGB8_A8_DXT3 : GPU_RGBA8_DXT3;
  }
  else if (ibuf->dds_data.fourcc == FOURCC_DXT5) {
    *r_texture_format = (use_srgb) ? GPU_SRGB8_A8_DXT5 : GPU_RGBA8_DXT5;
  }
  else {
    return false;
  }
  return true;
}

/**
 * Apply colormanagement and scale buffer if needed.
 * `*r_freedata` is set to true if the returned buffer need to be manually freed.
 */
static void *imb_gpu_get_data(const ImBuf *ibuf,
                              const bool do_rescale,
                              const int rescale_size[2],
                              const bool store_premultiplied,
                              bool *r_freedata)
{
  bool is_float_rect = (ibuf->float_buffer.data != nullptr);
  const bool is_grayscale = imb_is_grayscale_texture_format_compatible(ibuf);
  void *data_rect = (is_float_rect) ? (void *)ibuf->float_buffer.data :
                                      (void *)ibuf->byte_buffer.data;
  bool freedata = false;

  if (is_float_rect) {
    /* Float image is already in scene linear colorspace or non-color data by
     * convention, no colorspace conversion needed. But we do require 4 channels
     * currently. */
    if (ibuf->channels != 4 || !store_premultiplied) {
      data_rect = MEM_mallocN(sizeof(float[4]) * ibuf->x * ibuf->y, __func__);
      *r_freedata = freedata = true;

      if (data_rect == nullptr) {
        return nullptr;
      }

      IMB_colormanagement_imbuf_to_float_texture(
          (float *)data_rect, 0, 0, ibuf->x, ibuf->y, ibuf, store_premultiplied);
    }
  }
  else {
    /* Byte image is in original colorspace from the file, and may need conversion.
     *
     * We must also convert to premultiplied for correct texture interpolation
     * and consistency with float images. */
    if (IMB_colormanagement_space_is_data(ibuf->byte_buffer.colorspace)) {
      /* Non-color data, just store buffer as is. */
    }
    else if (IMB_colormanagement_space_is_srgb(ibuf->byte_buffer.colorspace) ||
             IMB_colormanagement_space_is_scene_linear(ibuf->byte_buffer.colorspace))
    {
      /* sRGB or scene linear, store as byte texture that the GPU can decode directly. */
      data_rect = MEM_mallocN(
          (is_grayscale ? sizeof(float[4]) : sizeof(uchar[4])) * ibuf->x * ibuf->y, __func__);
      *r_freedata = freedata = true;

      if (data_rect == nullptr) {
        return nullptr;
      }

      /* Texture storage of images is defined by the alpha mode of the image. The
       * downside of this is that there can be artifacts near alpha edges. However,
       * this allows us to use sRGB texture formats and preserves color values in
       * zero alpha areas, and appears generally closer to what game engines that we
       * want to be compatible with do. */
      if (is_grayscale) {
        /* Convert to byte buffer to then pack as half floats reducing the buffer size by half. */
        IMB_colormanagement_imbuf_to_float_texture(
            (float *)data_rect, 0, 0, ibuf->x, ibuf->y, ibuf, store_premultiplied);
        is_float_rect = true;
      }
      else {
        IMB_colormanagement_imbuf_to_byte_texture(
            (uchar *)data_rect, 0, 0, ibuf->x, ibuf->y, ibuf, store_premultiplied);
      }
    }
    else {
      /* Other colorspace, store as float texture to avoid precision loss. */
      data_rect = MEM_mallocN(sizeof(float[4]) * ibuf->x * ibuf->y, __func__);
      *r_freedata = freedata = true;
      is_float_rect = true;

      if (data_rect == nullptr) {
        return nullptr;
      }

      /* Texture storage of images is defined by the alpha mode of the image. The
       * downside of this is that there can be artifacts near alpha edges. However,
       * this allows us to use sRGB texture formats and preserves color values in
       * zero alpha areas, and appears generally closer to what game engines that we
       * want to be compatible with do. */
      IMB_colormanagement_imbuf_to_float_texture(
          (float *)data_rect, 0, 0, ibuf->x, ibuf->y, ibuf, store_premultiplied);
    }
  }

  if (do_rescale) {
    uint8_t *rect = (is_float_rect) ? nullptr : (uint8_t *)data_rect;
    float *rect_float = (is_float_rect) ? (float *)data_rect : nullptr;

    ImBuf *scale_ibuf = IMB_allocFromBuffer(rect, rect_float, ibuf->x, ibuf->y, 4);
    IMB_scaleImBuf(scale_ibuf, UNPACK2(rescale_size));

    if (freedata) {
      MEM_freeN(data_rect);
    }

    data_rect = (is_float_rect) ? (void *)scale_ibuf->float_buffer.data :
                                  (void *)scale_ibuf->byte_buffer.data;
    *r_freedata = freedata = true;
    /* Steal the rescaled buffer to avoid double free. */
    (void)IMB_steal_byte_buffer(scale_ibuf);
    (void)IMB_steal_float_buffer(scale_ibuf);
    IMB_freeImBuf(scale_ibuf);
  }

  /* Pack first channel data manually at the start of the buffer. */
  if (is_grayscale) {
    void *src_rect = data_rect;

    if (freedata == false) {
      data_rect = MEM_mallocN((is_float_rect ? sizeof(float) : sizeof(uchar)) * ibuf->x * ibuf->y,
                              __func__);
      *r_freedata = freedata = true;
    }

    if (data_rect == nullptr) {
      return nullptr;
    }

    int buffer_size = do_rescale ? rescale_size[0] * rescale_size[1] : ibuf->x * ibuf->y;
    if (is_float_rect) {
      for (uint64_t i = 0; i < buffer_size; i++) {
        ((float *)data_rect)[i] = ((float *)src_rect)[i * 4];
      }
    }
    else {
      for (uint64_t i = 0; i < buffer_size; i++) {
        ((uchar *)data_rect)[i] = ((uchar *)src_rect)[i * 4];
      }
    }
  }
  return data_rect;
}

GPUTexture *IMB_touch_gpu_texture(const char *name,
                                  ImBuf *ibuf,
                                  int w,
                                  int h,
                                  int layers,
                                  bool use_high_bitdepth,
                                  bool use_grayscale)
{
  eGPUDataFormat data_format;
  eGPUTextureFormat tex_format;
  imb_gpu_get_format(ibuf, use_high_bitdepth, use_grayscale, &data_format, &tex_format);

  GPUTexture *tex;
  if (layers > 0) {
    tex = GPU_texture_create_2d_array(name,
                                      w,
                                      h,
                                      layers,
                                      9999,
                                      tex_format,
                                      GPU_TEXTURE_USAGE_SHADER_READ |
                                          GPU_TEXTURE_USAGE_MIP_SWIZZLE_VIEW,
                                      nullptr);
  }
  else {
    tex = GPU_texture_create_2d(name,
                                w,
                                h,
                                9999,
                                tex_format,
                                GPU_TEXTURE_USAGE_SHADER_READ | GPU_TEXTURE_USAGE_MIP_SWIZZLE_VIEW,
                                nullptr);
  }

  GPU_texture_swizzle_set(tex, imb_gpu_get_swizzle(ibuf));
  GPU_texture_anisotropic_filter(tex, true);
  return tex;
}

void IMB_update_gpu_texture_sub(GPUTexture *tex,
                                ImBuf *ibuf,
                                int x,
                                int y,
                                int z,
                                int w,
                                int h,
                                bool use_high_bitdepth,
                                bool use_grayscale,
                                bool use_premult)
{
  const bool do_rescale = (ibuf->x != w || ibuf->y != h);
  const int size[2] = {w, h};

  eGPUDataFormat data_format;
  eGPUTextureFormat tex_format;
  imb_gpu_get_format(ibuf, use_high_bitdepth, use_grayscale, &data_format, &tex_format);

  bool freebuf = false;

  void *data = imb_gpu_get_data(ibuf, do_rescale, size, use_premult, &freebuf);

  /* Update Texture. */
  GPU_texture_update_sub(tex, data_format, data, x, y, z, w, h, 1);

  if (freebuf) {
    MEM_freeN(data);
  }
}

GPUTexture *IMB_create_gpu_texture(const char *name,
                                   ImBuf *ibuf,
                                   bool use_high_bitdepth,
                                   bool use_premult)
{
  GPUTexture *tex = nullptr;
  int size[2] = {GPU_texture_size_with_limit(ibuf->x), GPU_texture_size_with_limit(ibuf->y)};
  bool do_rescale = (ibuf->x != size[0]) || (ibuf->y != size[1]);

  /* Correct the smaller size to maintain the original aspect ratio of the image. */
  if (do_rescale && ibuf->x != ibuf->y) {
    if (size[0] > size[1]) {
      size[1] = int(ibuf->y * (float(size[0]) / ibuf->x));
    }
    else {
      size[0] = int(ibuf->x * (float(size[1]) / ibuf->y));
    }
  }

  if (ibuf->ftype == IMB_FTYPE_DDS) {
    eGPUTextureFormat compressed_format;
    if (!IMB_gpu_get_compressed_format(ibuf, &compressed_format)) {
      fprintf(stderr, "Unable to find a suitable DXT compression,");
    }
    else if (do_rescale) {
      fprintf(stderr, "Unable to load DXT image resolution,");
    }
    else if (!is_power_of_2_i(ibuf->x) || !is_power_of_2_i(ibuf->y)) {
      fprintf(stderr, "Unable to load non-power-of-two DXT image resolution,");
    }
    else {
      tex = GPU_texture_create_compressed_2d(name,
                                             ibuf->x,
                                             ibuf->y,
                                             ibuf->dds_data.nummipmaps,
                                             compressed_format,
                                             GPU_TEXTURE_USAGE_GENERAL,
                                             ibuf->dds_data.data);

      if (tex != nullptr) {
        return tex;
      }

      fprintf(stderr, "ST3C support not found,");
    }
    /* Fallback to uncompressed texture. */
    fprintf(stderr, " falling back to uncompressed.\n");
  }

  eGPUDataFormat data_format;
  eGPUTextureFormat tex_format;
  imb_gpu_get_format(ibuf, use_high_bitdepth, true, &data_format, &tex_format);

  bool freebuf = false;

  /* Create Texture. */
  tex = GPU_texture_create_2d(name,
                              UNPACK2(size),
                              9999,
                              tex_format,
                              GPU_TEXTURE_USAGE_SHADER_READ | GPU_TEXTURE_USAGE_MIP_SWIZZLE_VIEW,
                              nullptr);
  if (tex == nullptr) {
    size[0] = max_ii(1, size[0] / 2);
    size[1] = max_ii(1, size[1] / 2);
    tex = GPU_texture_create_2d(name,
                                UNPACK2(size),
                                9999,
                                tex_format,
                                GPU_TEXTURE_USAGE_SHADER_READ | GPU_TEXTURE_USAGE_MIP_SWIZZLE_VIEW,
                                nullptr);
    do_rescale = true;
  }
  BLI_assert(tex != nullptr);
  void *data = imb_gpu_get_data(ibuf, do_rescale, size, use_premult, &freebuf);
  GPU_texture_update(tex, data_format, data);

  GPU_texture_swizzle_set(tex, imb_gpu_get_swizzle(ibuf));
  GPU_texture_anisotropic_filter(tex, true);

  if (freebuf) {
    MEM_freeN(data);
  }

  return tex;
}

eGPUTextureFormat IMB_gpu_get_texture_format(const ImBuf *ibuf,
                                             bool high_bitdepth,
                                             bool use_grayscale)
{
  eGPUTextureFormat gpu_texture_format;
  eGPUDataFormat gpu_data_format;

  imb_gpu_get_format(ibuf, high_bitdepth, use_grayscale, &gpu_data_format, &gpu_texture_format);

  return gpu_texture_format;
}

void IMB_gpu_clamp_half_float(ImBuf *image_buffer)
{
  const float half_min = -65504;
  const float half_max = 65504;
  if (!image_buffer->float_buffer.data) {
    return;
  }

  float *rect_float = image_buffer->float_buffer.data;

  int rect_float_len = image_buffer->x * image_buffer->y *
                       (image_buffer->channels == 0 ? 4 : image_buffer->channels);

  for (int i = 0; i < rect_float_len; i++) {
    rect_float[i] = clamp_f(rect_float[i], half_min, half_max);
  }
}
