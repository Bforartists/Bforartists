/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * Copyright 2021, Blender Foundation.
 */

/** \file
 * \ingroup draw_engine
 */

#pragma once

#include "BKE_image_partial_update.hh"

#include "IMB_imbuf_types.h"

#include "image_batches.hh"
#include "image_private.hh"
#include "image_wrappers.hh"

namespace blender::draw::image_engine {

constexpr float EPSILON_UV_BOUNDS = 0.00001f;

/**
 * \brief Screen space method using a single texture spawning the whole screen.
 */
struct OneTextureMethod {
  IMAGE_InstanceData *instance_data;

  OneTextureMethod(IMAGE_InstanceData *instance_data) : instance_data(instance_data)
  {
  }

  /** \brief Update the texture slot uv and screen space bounds. */
  void update_screen_space_bounds(const ARegion *region)
  {
    /* Create a single texture that covers the visible screen space. */
    BLI_rctf_init(
        &instance_data->texture_infos[0].clipping_bounds, 0, region->winx, 0, region->winy);
    instance_data->texture_infos[0].visible = true;

    /* Mark the other textures as invalid. */
    for (int i = 1; i < SCREEN_SPACE_DRAWING_MODE_TEXTURE_LEN; i++) {
      BLI_rctf_init_minmax(&instance_data->texture_infos[i].clipping_bounds);
      instance_data->texture_infos[i].visible = false;
    }
  }

  void update_uv_bounds(const ARegion *region)
  {
    TextureInfo &info = instance_data->texture_infos[0];
    if (!BLI_rctf_compare(&info.uv_bounds, &region->v2d.cur, EPSILON_UV_BOUNDS)) {
      info.uv_bounds = region->v2d.cur;
      info.dirty = true;
    }

    /* Mark the other textures as invalid. */
    for (int i = 1; i < SCREEN_SPACE_DRAWING_MODE_TEXTURE_LEN; i++) {
      BLI_rctf_init_minmax(&instance_data->texture_infos[i].clipping_bounds);
    }
  }
};

using namespace blender::bke::image::partial_update;

template<typename TextureMethod> class ScreenSpaceDrawingMode : public AbstractDrawingMode {
 private:
  DRWPass *create_image_pass() const
  {
    /* Write depth is needed for background overlay rendering. Near depth is used for
     * transparency checker and Far depth is used for indicating the image size. */
    DRWState state = static_cast<DRWState>(DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH |
                                           DRW_STATE_DEPTH_ALWAYS | DRW_STATE_BLEND_ALPHA_PREMUL);
    return DRW_pass_create("Image", state);
  }

  void add_shgroups(const IMAGE_InstanceData *instance_data) const
  {
    const ShaderParameters &sh_params = instance_data->sh_params;
    GPUShader *shader = IMAGE_shader_image_get();

    DRWShadingGroup *shgrp = DRW_shgroup_create(shader, instance_data->passes.image_pass);
    DRW_shgroup_uniform_vec2_copy(shgrp, "farNearDistances", sh_params.far_near);
    DRW_shgroup_uniform_vec4_copy(shgrp, "shuffle", sh_params.shuffle);
    DRW_shgroup_uniform_int_copy(shgrp, "drawFlags", sh_params.flags);
    DRW_shgroup_uniform_bool_copy(shgrp, "imgPremultiplied", sh_params.use_premul_alpha);
    DRW_shgroup_uniform_vec2_copy(shgrp, "maxUv", instance_data->max_uv);
    float image_mat[4][4];
    unit_m4(image_mat);
    for (int i = 0; i < SCREEN_SPACE_DRAWING_MODE_TEXTURE_LEN; i++) {
      const TextureInfo &info = instance_data->texture_infos[i];
      if (!info.visible) {
        continue;
      }

      DRWShadingGroup *shgrp_sub = DRW_shgroup_create_sub(shgrp);
      DRW_shgroup_uniform_texture_ex(shgrp_sub, "imageTexture", info.texture, GPU_SAMPLER_DEFAULT);
      DRW_shgroup_call_obmat(shgrp_sub, info.batch, image_mat);
    }
  }

  /**
   * \brief Update GPUTextures for drawing the image.
   *
   * GPUTextures that are marked dirty are rebuild. GPUTextures that aren't marked dirty are
   * updated with changed region of the image.
   */
  void update_textures(IMAGE_InstanceData &instance_data,
                       Image *image,
                       ImageUser *image_user) const
  {
    PartialUpdateChecker<ImageTileData> checker(
        image, image_user, instance_data.partial_update.user);
    PartialUpdateChecker<ImageTileData>::CollectResult changes = checker.collect_changes();

    switch (changes.get_result_code()) {
      case ePartialUpdateCollectResult::FullUpdateNeeded:
        instance_data.mark_all_texture_slots_dirty();
        break;
      case ePartialUpdateCollectResult::NoChangesDetected:
        break;
      case ePartialUpdateCollectResult::PartialChangesDetected:
        /* Partial update when wrap repeat is enabled is not supported. */
        if (instance_data.flags.do_tile_drawing) {
          instance_data.mark_all_texture_slots_dirty();
        }
        else {
          do_partial_update(changes, instance_data);
        }
        break;
    }
    do_full_update_for_dirty_textures(instance_data, image_user);
  }

  void do_partial_update(PartialUpdateChecker<ImageTileData>::CollectResult &iterator,
                         IMAGE_InstanceData &instance_data) const
  {
    while (iterator.get_next_change() == ePartialUpdateIterResult::ChangeAvailable) {
      /* Quick exit when tile_buffer isn't availble. */
      if (iterator.tile_data.tile_buffer == nullptr) {
        continue;
      }
      ensure_float_buffer(*iterator.tile_data.tile_buffer);
      const float tile_width = static_cast<float>(iterator.tile_data.tile_buffer->x);
      const float tile_height = static_cast<float>(iterator.tile_data.tile_buffer->y);

      for (int i = 0; i < SCREEN_SPACE_DRAWING_MODE_TEXTURE_LEN; i++) {
        const TextureInfo &info = instance_data.texture_infos[i];
        /* Dirty images will receive a full update. No need to do a partial one now. */
        if (info.dirty) {
          continue;
        }
        if (!info.visible) {
          continue;
        }
        GPUTexture *texture = info.texture;
        const float texture_width = GPU_texture_width(texture);
        const float texture_height = GPU_texture_height(texture);
        // TODO
        // early bound check.
        ImageTileWrapper tile_accessor(iterator.tile_data.tile);
        float tile_offset_x = static_cast<float>(tile_accessor.get_tile_x_offset());
        float tile_offset_y = static_cast<float>(tile_accessor.get_tile_y_offset());
        rcti *changed_region_in_texel_space = &iterator.changed_region.region;
        rctf changed_region_in_uv_space;
        BLI_rctf_init(&changed_region_in_uv_space,
                      static_cast<float>(changed_region_in_texel_space->xmin) /
                              static_cast<float>(iterator.tile_data.tile_buffer->x) +
                          tile_offset_x,
                      static_cast<float>(changed_region_in_texel_space->xmax) /
                              static_cast<float>(iterator.tile_data.tile_buffer->x) +
                          tile_offset_x,
                      static_cast<float>(changed_region_in_texel_space->ymin) /
                              static_cast<float>(iterator.tile_data.tile_buffer->y) +
                          tile_offset_y,
                      static_cast<float>(changed_region_in_texel_space->ymax) /
                              static_cast<float>(iterator.tile_data.tile_buffer->y) +
                          tile_offset_y);
        rctf changed_overlapping_region_in_uv_space;
        const bool region_overlap = BLI_rctf_isect(
            &info.uv_bounds, &changed_region_in_uv_space, &changed_overlapping_region_in_uv_space);
        if (!region_overlap) {
          continue;
        }
        // convert the overlapping region to texel space and to ss_pixel space...
        // TODO: first convert to ss_pixel space as integer based. and from there go back to texel
        // space. But perhaps this isn't needed and we could use an extraction offset somehow.
        rcti gpu_texture_region_to_update;
        BLI_rcti_init(&gpu_texture_region_to_update,
                      floor((changed_overlapping_region_in_uv_space.xmin - info.uv_bounds.xmin) *
                            texture_width / BLI_rctf_size_x(&info.uv_bounds)),
                      floor((changed_overlapping_region_in_uv_space.xmax - info.uv_bounds.xmin) *
                            texture_width / BLI_rctf_size_x(&info.uv_bounds)),
                      ceil((changed_overlapping_region_in_uv_space.ymin - info.uv_bounds.ymin) *
                           texture_height / BLI_rctf_size_y(&info.uv_bounds)),
                      ceil((changed_overlapping_region_in_uv_space.ymax - info.uv_bounds.ymin) *
                           texture_height / BLI_rctf_size_y(&info.uv_bounds)));

        rcti tile_region_to_extract;
        BLI_rcti_init(
            &tile_region_to_extract,
            floor((changed_overlapping_region_in_uv_space.xmin - tile_offset_x) * tile_width),
            floor((changed_overlapping_region_in_uv_space.xmax - tile_offset_x) * tile_width),
            ceil((changed_overlapping_region_in_uv_space.ymin - tile_offset_y) * tile_height),
            ceil((changed_overlapping_region_in_uv_space.ymax - tile_offset_y) * tile_height));

        // Create an image buffer with a size
        // extract and scale into an imbuf
        const int texture_region_width = BLI_rcti_size_x(&gpu_texture_region_to_update);
        const int texture_region_height = BLI_rcti_size_y(&gpu_texture_region_to_update);

        ImBuf extracted_buffer;
        IMB_initImBuf(
            &extracted_buffer, texture_region_width, texture_region_height, 32, IB_rectfloat);

        int offset = 0;
        ImBuf *tile_buffer = iterator.tile_data.tile_buffer;
        for (int y = gpu_texture_region_to_update.ymin; y < gpu_texture_region_to_update.ymax;
             y++) {
          float yf = y / (float)texture_height;
          float v = info.uv_bounds.ymax * yf + info.uv_bounds.ymin * (1.0 - yf) - tile_offset_y;
          for (int x = gpu_texture_region_to_update.xmin; x < gpu_texture_region_to_update.xmax;
               x++) {
            float xf = x / (float)texture_width;
            float u = info.uv_bounds.xmax * xf + info.uv_bounds.xmin * (1.0 - xf) - tile_offset_x;
            nearest_interpolation_color(tile_buffer,
                                        nullptr,
                                        &extracted_buffer.rect_float[offset * 4],
                                        u * tile_buffer->x,
                                        v * tile_buffer->y);
            offset++;
          }
        }

        GPU_texture_update_sub(texture,
                               GPU_DATA_FLOAT,
                               extracted_buffer.rect_float,
                               gpu_texture_region_to_update.xmin,
                               gpu_texture_region_to_update.ymin,
                               0,
                               extracted_buffer.x,
                               extracted_buffer.y,
                               0);
        imb_freerectImbuf_all(&extracted_buffer);
      }
    }
  }

  void do_full_update_for_dirty_textures(IMAGE_InstanceData &instance_data,
                                         const ImageUser *image_user) const
  {
    for (int i = 0; i < SCREEN_SPACE_DRAWING_MODE_TEXTURE_LEN; i++) {
      TextureInfo &info = instance_data.texture_infos[i];
      if (!info.dirty) {
        continue;
      }
      if (!info.visible) {
        continue;
      }
      do_full_update_gpu_texture(info, instance_data, image_user);
    }
  }

  void do_full_update_gpu_texture(TextureInfo &info,
                                  IMAGE_InstanceData &instance_data,
                                  const ImageUser *image_user) const
  {

    ImBuf texture_buffer;
    const int texture_width = GPU_texture_width(info.texture);
    const int texture_height = GPU_texture_height(info.texture);
    IMB_initImBuf(&texture_buffer, texture_width, texture_height, 0, IB_rectfloat);
    ImageUser tile_user = {0};
    if (image_user) {
      tile_user = *image_user;
    }

    void *lock;

    Image *image = instance_data.image;
    LISTBASE_FOREACH (ImageTile *, image_tile_ptr, &image->tiles) {
      const ImageTileWrapper image_tile(image_tile_ptr);
      tile_user.tile = image_tile.get_tile_number();

      ImBuf *tile_buffer = BKE_image_acquire_ibuf(image, &tile_user, &lock);
      if (tile_buffer == nullptr) {
        /* Couldn't load the image buffer of the tile. */
        continue;
      }
      do_full_update_texture_slot(instance_data, info, texture_buffer, *tile_buffer, image_tile);
      BKE_image_release_ibuf(image, tile_buffer, lock);
    }
    GPU_texture_update(info.texture, GPU_DATA_FLOAT, texture_buffer.rect_float);
    imb_freerectImbuf_all(&texture_buffer);
  }

  /**
   * \brief Ensure that the float buffer of the given image buffer is available.
   */
  void ensure_float_buffer(ImBuf &image_buffer) const
  {
    if (image_buffer.rect_float == nullptr) {
      IMB_float_from_rect(&image_buffer);
    }
  }

  void do_full_update_texture_slot(const IMAGE_InstanceData &instance_data,
                                   const TextureInfo &texture_info,
                                   ImBuf &texture_buffer,
                                   ImBuf &tile_buffer,
                                   const ImageTileWrapper &image_tile) const
  {
    const int texture_width = texture_buffer.x;
    const int texture_height = texture_buffer.y;
    ensure_float_buffer(tile_buffer);

    /* IMB_transform works in a non-consistent space. This should be documented or fixed!.
     * Construct a variant of the info_uv_to_texture that adds the texel space
     * transformation.*/
    float uv_to_texel[4][4];
    copy_m4_m4(uv_to_texel, instance_data.ss_to_texture);
    float scale[3] = {static_cast<float>(texture_width) / static_cast<float>(tile_buffer.x),
                      static_cast<float>(texture_height) / static_cast<float>(tile_buffer.y),
                      1.0f};
    rescale_m4(uv_to_texel, scale);
    uv_to_texel[3][0] += image_tile.get_tile_x_offset() / BLI_rctf_size_x(&texture_info.uv_bounds);
    uv_to_texel[3][1] += image_tile.get_tile_y_offset() / BLI_rctf_size_y(&texture_info.uv_bounds);
    uv_to_texel[3][0] *= texture_width;
    uv_to_texel[3][1] *= texture_height;
    invert_m4(uv_to_texel);

    rctf crop_rect;
    rctf *crop_rect_ptr = nullptr;
    eIMBTransformMode transform_mode;
    if (instance_data.flags.do_tile_drawing) {
      transform_mode = IMB_TRANSFORM_MODE_WRAP_REPEAT;
    }
    else {
      BLI_rctf_init(&crop_rect, 0.0, tile_buffer.x, 0.0, tile_buffer.y);
      crop_rect_ptr = &crop_rect;
      transform_mode = IMB_TRANSFORM_MODE_CROP_SRC;
    }

    IMB_transform(&tile_buffer,
                  &texture_buffer,
                  transform_mode,
                  IMB_FILTER_NEAREST,
                  uv_to_texel,
                  crop_rect_ptr);
  }

 public:
  void cache_init(IMAGE_Data *vedata) const override
  {
    IMAGE_InstanceData *instance_data = vedata->instance_data;
    instance_data->passes.image_pass = create_image_pass();
  }

  void cache_image(IMAGE_Data *vedata, Image *image, ImageUser *iuser) const override
  {
    const DRWContextState *draw_ctx = DRW_context_state_get();
    IMAGE_InstanceData *instance_data = vedata->instance_data;
    TextureMethod method(instance_data);

    instance_data->partial_update.ensure_image(image);
    instance_data->max_uv_update();
    instance_data->clear_dirty_flag();

    // Step: Find out which screen space textures are needed to draw on the screen. Remove the
    // screen space textures that aren't needed.
    const ARegion *region = draw_ctx->region;
    method.update_screen_space_bounds(region);
    method.update_uv_bounds(region);

    // Step: Update the GPU textures based on the changes in the image.
    instance_data->update_gpu_texture_allocations();
    update_textures(*instance_data, image, iuser);

    // Step: Add the GPU textures to the shgroup.
    instance_data->update_batches();
    add_shgroups(instance_data);
  }

  void draw_finish(IMAGE_Data *UNUSED(vedata)) const override
  {
  }

  void draw_scene(IMAGE_Data *vedata) const override
  {
    IMAGE_InstanceData *instance_data = vedata->instance_data;

    DefaultFramebufferList *dfbl = DRW_viewport_framebuffer_list_get();
    GPU_framebuffer_bind(dfbl->default_fb);
    static float clear_col[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    GPU_framebuffer_clear_color_depth(dfbl->default_fb, clear_col, 1.0);

    DRW_view_set_active(instance_data->view);
    DRW_draw_pass(instance_data->passes.image_pass);
    DRW_view_set_active(nullptr);
  }
};  // namespace clipping

}  // namespace blender::draw::image_engine
