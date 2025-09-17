/* SPDX-FileCopyrightText: 2025 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup sequencer
 */

#include "BLI_array.hh"
#include "BLI_math_geom.h"

#include "BLT_translation.hh"

#include "DNA_sequence_types.h"

#include "IMB_colormanagement.hh"

#include "SEQ_modifier.hh"

#include "UI_interface.hh"
#include "UI_interface_layout.hh"

#include "RNA_access.hh"

#include "modifier.hh"
#include "render.hh"

namespace blender::seq {

struct AvgLogLum {
  const SequencerTonemapModifierData *tmmd;
  float al;
  float auto_key;
  float lav;
  float3 cav;
  float igm;
};

static void tonemapmodifier_init_data(StripModifierData *smd)
{
  SequencerTonemapModifierData *tmmd = (SequencerTonemapModifierData *)smd;
  /* Same as tone-map compositor node. */
  tmmd->type = SEQ_TONEMAP_RD_PHOTORECEPTOR;
  tmmd->key = 0.18f;
  tmmd->offset = 1.0f;
  tmmd->gamma = 1.0f;
  tmmd->intensity = 0.0f;
  tmmd->contrast = 0.0f;
  tmmd->adaptation = 1.0f;
  tmmd->correction = 0.0f;
}

/* Convert chunk of float image pixels to scene linear space, in-place. */
static void pixels_to_scene_linear_float(const ColorSpace *colorspace,
                                         float4 *pixels,
                                         int64_t count)
{
  IMB_colormanagement_colorspace_to_scene_linear(
      (float *)(pixels), int(count), 1, 4, colorspace, false);
}

/* Convert chunk of byte image pixels to scene linear space, into a destination array. */
static void pixels_to_scene_linear_byte(const ColorSpace *colorspace,
                                        const uchar *pixels,
                                        float4 *dst,
                                        int64_t count)
{
  const uchar *bptr = pixels;
  float4 *dst_ptr = dst;
  for (int64_t i = 0; i < count; i++) {
    straight_uchar_to_premul_float(*dst_ptr, bptr);
    bptr += 4;
    dst_ptr++;
  }
  IMB_colormanagement_colorspace_to_scene_linear(
      (float *)dst, int(count), 1, 4, colorspace, false);
}

static void scene_linear_to_image_chunk_float(ImBuf *ibuf, IndexRange range)
{
  const ColorSpace *colorspace = ibuf->float_buffer.colorspace;
  float4 *fptr = reinterpret_cast<float4 *>(ibuf->float_buffer.data);
  IMB_colormanagement_scene_linear_to_colorspace(
      (float *)(fptr + range.first()), int(range.size()), 1, 4, colorspace);
}

static void scene_linear_to_image_chunk_byte(float4 *src, ImBuf *ibuf, IndexRange range)
{
  const ColorSpace *colorspace = ibuf->byte_buffer.colorspace;
  IMB_colormanagement_scene_linear_to_colorspace(
      (float *)src, int(range.size()), 1, 4, colorspace);
  const float4 *src_ptr = src;
  uchar *bptr = ibuf->byte_buffer.data;
  for (const int64_t idx : range) {
    premul_float_to_straight_uchar(bptr + idx * 4, *src_ptr);
    src_ptr++;
  }
}

static void tonemap_simple(float4 *scene_linear,
                           ImBuf *mask,
                           IndexRange range,
                           const AvgLogLum &avg)
{
  const float4 *mask_float = mask != nullptr ? (const float4 *)mask->float_buffer.data : nullptr;
  const uchar4 *mask_byte = mask != nullptr ? (const uchar4 *)mask->byte_buffer.data : nullptr;

  int64_t index = 0;
  for (const int64_t pixel_index : range) {
    float4 input = scene_linear[index];

    /* Apply correction. */
    float3 pixel = input.xyz() * avg.al;
    float3 d = pixel + avg.tmmd->offset;
    pixel.x /= (d.x == 0.0f) ? 1.0f : d.x;
    pixel.y /= (d.y == 0.0f) ? 1.0f : d.y;
    pixel.z /= (d.z == 0.0f) ? 1.0f : d.z;
    const float igm = avg.igm;
    if (igm != 0.0f) {
      pixel.x = powf(math::max(pixel.x, 0.0f), igm);
      pixel.y = powf(math::max(pixel.y, 0.0f), igm);
      pixel.z = powf(math::max(pixel.z, 0.0f), igm);
    }

    /* Apply mask. */
    if (mask != nullptr) {
      float3 msk(1.0f);
      if (mask_byte != nullptr) {
        rgb_uchar_to_float(msk, mask_byte[pixel_index]);
      }
      else if (mask_float != nullptr) {
        msk = mask_float[pixel_index].xyz();
      }
      pixel = math::interpolate(input.xyz(), pixel, msk);
    }

    scene_linear[index] = float4(pixel.x, pixel.y, pixel.z, input.w);
    index++;
  }
}

static void tonemap_rd_photoreceptor(float4 *scene_linear,
                                     ImBuf *mask,
                                     IndexRange range,
                                     const AvgLogLum &avg)
{
  const float4 *mask_float = mask != nullptr ? (const float4 *)mask->float_buffer.data : nullptr;
  const uchar4 *mask_byte = mask != nullptr ? (const uchar4 *)mask->byte_buffer.data : nullptr;

  const float f = expf(-avg.tmmd->intensity);
  const float m = (avg.tmmd->contrast > 0.0f) ? avg.tmmd->contrast :
                                                (0.3f + 0.7f * powf(avg.auto_key, 1.4f));
  const float ic = 1.0f - avg.tmmd->correction, ia = 1.0f - avg.tmmd->adaptation;

  int64_t index = 0;
  for (const int64_t pixel_index : range) {
    float4 input = scene_linear[index];

    /* Apply correction. */
    float3 pixel = input.xyz();
    const float L = IMB_colormanagement_get_luminance(pixel);
    float I_l = pixel.x + ic * (L - pixel.x);
    float I_g = avg.cav.x + ic * (avg.lav - avg.cav.x);
    float I_a = I_l + ia * (I_g - I_l);
    pixel.x /= std::max(pixel.x + powf(f * I_a, m), 1.0e-30f);
    I_l = pixel.y + ic * (L - pixel.y);
    I_g = avg.cav.y + ic * (avg.lav - avg.cav.y);
    I_a = I_l + ia * (I_g - I_l);
    pixel.y /= std::max(pixel.y + powf(f * I_a, m), 1.0e-30f);
    I_l = pixel.z + ic * (L - pixel.z);
    I_g = avg.cav.z + ic * (avg.lav - avg.cav.z);
    I_a = I_l + ia * (I_g - I_l);
    pixel.z /= std::max(pixel.z + powf(f * I_a, m), 1.0e-30f);

    /* Apply mask. */
    if (mask != nullptr) {
      float3 msk(1.0f);
      if (mask_byte != nullptr) {
        rgb_uchar_to_float(msk, mask_byte[pixel_index]);
      }
      else if (mask_float != nullptr) {
        msk = mask_float[pixel_index].xyz();
      }
      pixel = math::interpolate(input.xyz(), pixel, msk);
    }

    scene_linear[index] = float4(pixel.x, pixel.y, pixel.z, input.w);
    index++;
  }
}

static bool is_point_inside_quad(const StripScreenQuad &quad, int x, int y)
{
  float2 pt(x + 0.5f, y + 0.5f);
  return isect_point_quad_v2(pt, quad.v0, quad.v1, quad.v2, quad.v3);
}

struct AreaLuminance {
  int64_t pixel_count = 0;
  double sum = 0.0f;
  float3 color_sum = {0, 0, 0};
  double log_sum = 0.0;
  float min = FLT_MAX;
  float max = -FLT_MAX;
};

static void tonemap_calc_chunk_luminance(const StripScreenQuad &quad,
                                         const bool all_pixels_inside_quad,
                                         const int width,
                                         const IndexRange y_range,
                                         const float4 *scene_linear,
                                         AreaLuminance &r_lum)
{
  for (const int y : y_range) {
    for (int x = 0; x < width; x++) {
      if (all_pixels_inside_quad || is_point_inside_quad(quad, x, y)) {
        float4 pixel = *scene_linear;
        r_lum.pixel_count++;
        float L = IMB_colormanagement_get_luminance(pixel);
        r_lum.sum += L;
        r_lum.color_sum.x += pixel.x;
        r_lum.color_sum.y += pixel.y;
        r_lum.color_sum.z += pixel.z;
        r_lum.log_sum += logf(math::max(L, 0.0f) + 1e-5f);
        r_lum.max = math::max(r_lum.max, L);
        r_lum.min = math::min(r_lum.min, L);
      }
      scene_linear++;
    }
  }
}

static AreaLuminance tonemap_calc_input_luminance(const StripScreenQuad &quad, const ImBuf *ibuf)
{
  /* Pixels outside the pre-transform strip area are ignored for luminance calculations.
   * If strip area covers whole image, we can trivially accept all pixels. */
  const bool all_pixels_inside_quad = is_point_inside_quad(quad, 0, 0) &&
                                      is_point_inside_quad(quad, ibuf->x - 1, 0) &&
                                      is_point_inside_quad(quad, 0, ibuf->y - 1) &&
                                      is_point_inside_quad(quad, ibuf->x - 1, ibuf->y - 1);

  AreaLuminance lum;
  lum = threading::parallel_reduce(
      IndexRange(ibuf->y),
      32,
      lum,
      /* Calculate luminance for a chunk. */
      [&](const IndexRange y_range, const AreaLuminance &init) {
        AreaLuminance lum = init;
        const int64_t chunk_size = y_range.size() * ibuf->x;
        /* For float images, convert to scene-linear in place. The rest
         * of tone-mapper can then continue with scene-linear values. */
        if (ibuf->float_buffer.data != nullptr) {
          float4 *fptr = reinterpret_cast<float4 *>(ibuf->float_buffer.data);
          fptr += y_range.first() * ibuf->x;
          pixels_to_scene_linear_float(ibuf->float_buffer.colorspace, fptr, chunk_size);
          tonemap_calc_chunk_luminance(quad, all_pixels_inside_quad, ibuf->x, y_range, fptr, lum);
        }
        else {
          const uchar *bptr = ibuf->byte_buffer.data + y_range.first() * ibuf->x * 4;
          Array<float4> scene_linear(chunk_size);
          pixels_to_scene_linear_byte(
              ibuf->byte_buffer.colorspace, bptr, scene_linear.data(), chunk_size);
          tonemap_calc_chunk_luminance(
              quad, all_pixels_inside_quad, ibuf->x, y_range, scene_linear.data(), lum);
        }
        return lum;
      },
      /* Reduce luminance results. */
      [&](const AreaLuminance &a, const AreaLuminance &b) {
        AreaLuminance res;
        res.pixel_count = a.pixel_count + b.pixel_count;
        res.sum = a.sum + b.sum;
        res.color_sum = a.color_sum + b.color_sum;
        res.log_sum = a.log_sum + b.log_sum;
        res.min = math::min(a.min, b.min);
        res.max = math::max(a.max, b.max);
        return res;
      });
  return lum;
}

static void tonemapmodifier_apply(const StripScreenQuad &quad,
                                  StripModifierData *smd,
                                  ImBuf *ibuf,
                                  ImBuf *mask)
{
  const SequencerTonemapModifierData *tmmd = (const SequencerTonemapModifierData *)smd;

  AreaLuminance lum = tonemap_calc_input_luminance(quad, ibuf);
  if (lum.pixel_count == 0) {
    return; /* Strip is zero size or off-screen. */
  }

  AvgLogLum data;
  data.tmmd = tmmd;
  data.lav = lum.sum / lum.pixel_count;
  data.cav.x = lum.color_sum.x / lum.pixel_count;
  data.cav.y = lum.color_sum.y / lum.pixel_count;
  data.cav.z = lum.color_sum.z / lum.pixel_count;
  float maxl = log(double(lum.max) + 1e-5f);
  float minl = log(double(lum.min) + 1e-5f);
  float avl = lum.log_sum / lum.pixel_count;
  data.auto_key = (maxl > minl) ? ((maxl - avl) / (maxl - minl)) : 1.0f;
  float al = exp(double(avl));
  data.al = (al == 0.0f) ? 0.0f : (tmmd->key / al);
  data.igm = (tmmd->gamma == 0.0f) ? 1.0f : (1.0f / tmmd->gamma);

  threading::parallel_for(
      IndexRange(int64_t(ibuf->x) * ibuf->y), 64 * 1024, [&](IndexRange range) {
        if (ibuf->float_buffer.data != nullptr) {
          /* Float pixels: no need for temporary storage. Luminance calculation already converted
           * data to scene linear. */
          float4 *pixels = (float4 *)(ibuf->float_buffer.data) + range.first();
          if (tmmd->type == SEQ_TONEMAP_RD_PHOTORECEPTOR) {
            tonemap_rd_photoreceptor(pixels, mask, range, data);
          }
          else {
            BLI_assert(tmmd->type == SEQ_TONEMAP_RH_SIMPLE);
            tonemap_simple(pixels, mask, range, data);
          }
          scene_linear_to_image_chunk_float(ibuf, range);
        }
        else {
          /* Byte pixels: temporary storage for scene linear pixel values. */
          Array<float4> scene_linear(range.size());
          pixels_to_scene_linear_byte(ibuf->byte_buffer.colorspace,
                                      ibuf->byte_buffer.data + range.first() * 4,
                                      scene_linear.data(),
                                      range.size());
          if (tmmd->type == SEQ_TONEMAP_RD_PHOTORECEPTOR) {
            tonemap_rd_photoreceptor(scene_linear.data(), mask, range, data);
          }
          else {
            BLI_assert(tmmd->type == SEQ_TONEMAP_RH_SIMPLE);
            tonemap_simple(scene_linear.data(), mask, range, data);
          }
          scene_linear_to_image_chunk_byte(scene_linear.data(), ibuf, range);
        }
      });
}

static void tonemapmodifier_panel_draw(const bContext *C, Panel *panel)
{
  uiLayout *layout = panel->layout;
  PointerRNA *ptr = UI_panel_custom_data_get(panel);

  const int tonemap_type = RNA_enum_get(ptr, "tonemap_type");

  layout->use_property_split_set(true);

  uiLayout &col = layout->column(false);
  col.prop(ptr, "tonemap_type", UI_ITEM_NONE, std::nullopt, ICON_NONE);
  if (tonemap_type == SEQ_TONEMAP_RD_PHOTORECEPTOR) {
    col.prop(ptr, "intensity", UI_ITEM_NONE, std::nullopt, ICON_NONE);
    col.prop(ptr, "contrast", UI_ITEM_NONE, std::nullopt, ICON_NONE);
    col.prop(ptr, "adaptation", UI_ITEM_NONE, std::nullopt, ICON_NONE);
    col.prop(ptr, "correction", UI_ITEM_NONE, std::nullopt, ICON_NONE);
  }
  else if (tonemap_type == SEQ_TONEMAP_RH_SIMPLE) {
    col.prop(ptr, "key", UI_ITEM_NONE, std::nullopt, ICON_NONE);
    col.prop(ptr, "offset", UI_ITEM_NONE, std::nullopt, ICON_NONE);
    col.prop(ptr, "gamma", UI_ITEM_NONE, std::nullopt, ICON_NONE);
  }
  else {
    BLI_assert_unreachable();
  }

  if (uiLayout *mask_input_layout = layout->panel_prop(
          C, ptr, "open_mask_input_panel", IFACE_("Mask Input")))
  {
    draw_mask_input_type_settings(C, mask_input_layout, ptr);
  }
}

static void tonemapmodifier_register(ARegionType *region_type)
{
  modifier_panel_register(region_type, eSeqModifierType_Tonemap, tonemapmodifier_panel_draw);
}

StripModifierTypeInfo seqModifierType_Tonemap = {
    /*idname*/ "Tonemap",
    /*name*/ CTX_N_(BLT_I18NCONTEXT_ID_SEQUENCE, "Tonemap"),
    /*struct_name*/ "SequencerTonemapModifierData",
    /*struct_size*/ sizeof(SequencerTonemapModifierData),
    /*init_data*/ tonemapmodifier_init_data,
    /*free_data*/ nullptr,
    /*copy_data*/ nullptr,
    /*apply*/ tonemapmodifier_apply,
    /*panel_register*/ tonemapmodifier_register,
    /*blend_write*/ nullptr,
    /*blend_read*/ nullptr,
};

};  // namespace blender::seq
