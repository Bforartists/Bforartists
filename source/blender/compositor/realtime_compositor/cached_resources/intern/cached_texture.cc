/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include <cstdint>
#include <memory>

#include "BLI_array.hh"
#include "BLI_hash.hh"
#include "BLI_index_range.hh"
#include "BLI_math_vector_types.hh"
#include "BLI_task.hh"

#include "GPU_texture.h"

#include "BKE_image.h"
#include "BKE_texture.h"

#include "DNA_ID.h"
#include "DNA_scene_types.h"
#include "DNA_texture_types.h"

#include "RE_texture.h"

#include "COM_cached_texture.hh"
#include "COM_context.hh"

namespace blender::realtime_compositor {

/* --------------------------------------------------------------------
 * Cached Texture Key.
 */

CachedTextureKey::CachedTextureKey(int2 size, float2 offset, float2 scale)
    : size(size), offset(offset), scale(scale)
{
}

uint64_t CachedTextureKey::hash() const
{
  return get_default_hash_3(size, offset, scale);
}

bool operator==(const CachedTextureKey &a, const CachedTextureKey &b)
{
  return a.size == b.size && a.offset == b.offset && a.scale == b.scale;
}

/* --------------------------------------------------------------------
 * Cached Texture.
 */

CachedTexture::CachedTexture(
    Tex *texture, bool use_color_management, int2 size, float2 offset, float2 scale)
{
  ImagePool *image_pool = BKE_image_pool_new();
  BKE_texture_fetch_images_for_pool(texture, image_pool);

  Array<float4> color_pixels(size.x * size.y);
  Array<float> value_pixels(size.x * size.y);
  threading::parallel_for(IndexRange(size.y), 1, [&](const IndexRange sub_y_range) {
    for (const int64_t y : sub_y_range) {
      for (const int64_t x : IndexRange(size.x)) {
        /* Compute the coordinates in the [-1, 1] range and add 0.5 to evaluate the texture at the
         * center of pixels in case it was interpolated. */
        float2 coordinates = ((float2(x, y) + 0.5f) / float2(size)) * 2.0f - 1.0f;
        /* Note that it is expected that the offset is scaled by the scale. */
        coordinates = (coordinates + offset) * scale;
        TexResult texture_result;
        BKE_texture_get_value_ex(
            texture, coordinates, &texture_result, image_pool, use_color_management);
        color_pixels[y * size.x + x] = float4(texture_result.trgba);
        value_pixels[y * size.x + x] = texture_result.talpha ? texture_result.trgba[3] :
                                                               texture_result.tin;
      }
    }
  });

  BKE_image_pool_free(image_pool);

  color_texture_ = GPU_texture_create_2d("Cached Color Texture",
                                         size.x,
                                         size.y,
                                         1,
                                         GPU_RGBA16F,
                                         GPU_TEXTURE_USAGE_SHADER_READ,
                                         *color_pixels.data());

  value_texture_ = GPU_texture_create_2d("Cached Value Texture",
                                         size.x,
                                         size.y,
                                         1,
                                         GPU_R16F,
                                         GPU_TEXTURE_USAGE_SHADER_READ,
                                         value_pixels.data());
}

CachedTexture::~CachedTexture()
{
  GPU_texture_free(color_texture_);
  GPU_texture_free(value_texture_);
}

GPUTexture *CachedTexture::color_texture()
{
  return color_texture_;
}

GPUTexture *CachedTexture::value_texture()
{
  return value_texture_;
}

/* --------------------------------------------------------------------
 * Cached Texture Container.
 */

void CachedTextureContainer::reset()
{
  /* First, delete all cached textures that are no longer needed. */
  for (auto &cached_textures_for_id : map_.values()) {
    cached_textures_for_id.remove_if([](auto item) { return !item.value->needed; });
  }
  map_.remove_if([](auto item) { return item.value.is_empty(); });

  /* Second, reset the needed status of the remaining cached textures to false to ready them to
   * track their needed status for the next evaluation. */
  for (auto &cached_textures_for_id : map_.values()) {
    for (auto &value : cached_textures_for_id.values()) {
      value->needed = false;
    }
  }
}

CachedTexture &CachedTextureContainer::get(Context &context,
                                           Tex *texture,
                                           bool use_color_management,
                                           int2 size,
                                           float2 offset,
                                           float2 scale)
{
  const CachedTextureKey key(size, offset, scale);

  auto &cached_textures_for_id = map_.lookup_or_add_default(texture->id.name);

  /* Invalidate the cache for that texture ID if it was changed and reset the recalculate flag. */
  if (context.query_id_recalc_flag(reinterpret_cast<ID *>(texture)) & ID_RECALC_ALL) {
    cached_textures_for_id.clear();
  }

  auto &cached_texture = *cached_textures_for_id.lookup_or_add_cb(key, [&]() {
    return std::make_unique<CachedTexture>(texture, use_color_management, size, offset, scale);
  });

  cached_texture.needed = true;
  return cached_texture;
}

}  // namespace blender::realtime_compositor
