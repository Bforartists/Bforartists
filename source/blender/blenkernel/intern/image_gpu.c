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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 */

/** \file
 * \ingroup bke
 */

#include "MEM_guardedalloc.h"

#include "BLI_boxpack_2d.h"
#include "BLI_linklist.h"
#include "BLI_listbase.h"
#include "BLI_threads.h"

#include "DNA_image_types.h"
#include "DNA_userdef_types.h"

#include "IMB_colormanagement.h"
#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_main.h"

#include "GPU_capabilities.h"
#include "GPU_state.h"
#include "GPU_texture.h"

#include "PIL_time.h"

/* Prototypes. */
static void gpu_free_unused_buffers(void);
static void image_free_gpu(Image *ima, const bool immediate);

/* -------------------------------------------------------------------- */
/** \name UDIM gpu texture
 * \{ */

static bool is_over_resolution_limit(int w, int h)
{
  return (w > GPU_texture_size_with_limit(w) || h > GPU_texture_size_with_limit(h));
}

static int smaller_power_of_2_limit(int num)
{
  return power_of_2_min_i(GPU_texture_size_with_limit(num));
}

static GPUTexture *gpu_texture_create_tile_mapping(Image *ima, const int multiview_eye)
{
  GPUTexture *tilearray = ima->gputexture[TEXTARGET_2D_ARRAY][multiview_eye];

  if (tilearray == NULL) {
    return 0;
  }

  float array_w = GPU_texture_width(tilearray);
  float array_h = GPU_texture_height(tilearray);

  ImageTile *last_tile = (ImageTile *)ima->tiles.last;
  /* Tiles are sorted by number. */
  int max_tile = last_tile->tile_number - 1001;

  /* create image */
  int width = max_tile + 1;
  float *data = (float *)MEM_callocN(width * 8 * sizeof(float), __func__);
  for (int i = 0; i < width; i++) {
    data[4 * i] = -1.0f;
  }
  LISTBASE_FOREACH (ImageTile *, tile, &ima->tiles) {
    int i = tile->tile_number - 1001;
    data[4 * i] = tile->runtime.tilearray_layer;

    float *tile_info = &data[4 * width + 4 * i];
    tile_info[0] = tile->runtime.tilearray_offset[0] / array_w;
    tile_info[1] = tile->runtime.tilearray_offset[1] / array_h;
    tile_info[2] = tile->runtime.tilearray_size[0] / array_w;
    tile_info[3] = tile->runtime.tilearray_size[1] / array_h;
  }

  GPUTexture *tex = GPU_texture_create_1d_array(ima->id.name + 2, width, 2, 1, GPU_RGBA32F, data);
  GPU_texture_mipmap_mode(tex, false, false);

  MEM_freeN(data);

  return tex;
}

typedef struct PackTile {
  FixedSizeBoxPack boxpack;
  ImageTile *tile;
  float pack_score;
} PackTile;

static int compare_packtile(const void *a, const void *b)
{
  const PackTile *tile_a = (const PackTile *)a;
  const PackTile *tile_b = (const PackTile *)b;

  return tile_a->pack_score < tile_b->pack_score;
}

static GPUTexture *gpu_texture_create_tile_array(Image *ima, ImBuf *main_ibuf)
{
  int arraywidth = 0, arrayheight = 0;
  ListBase boxes = {NULL};

  LISTBASE_FOREACH (ImageTile *, tile, &ima->tiles) {
    ImageUser iuser;
    BKE_imageuser_default(&iuser);
    iuser.tile = tile->tile_number;
    ImBuf *ibuf = BKE_image_acquire_ibuf(ima, &iuser, NULL);

    if (ibuf) {
      PackTile *packtile = (PackTile *)MEM_callocN(sizeof(PackTile), __func__);
      packtile->tile = tile;
      packtile->boxpack.w = ibuf->x;
      packtile->boxpack.h = ibuf->y;

      if (is_over_resolution_limit(packtile->boxpack.w, packtile->boxpack.h)) {
        packtile->boxpack.w = smaller_power_of_2_limit(packtile->boxpack.w);
        packtile->boxpack.h = smaller_power_of_2_limit(packtile->boxpack.h);
      }
      arraywidth = max_ii(arraywidth, packtile->boxpack.w);
      arrayheight = max_ii(arrayheight, packtile->boxpack.h);

      /* We sort the tiles by decreasing size, with an additional penalty term
       * for high aspect ratios. This improves packing efficiency. */
      float w = packtile->boxpack.w, h = packtile->boxpack.h;
      packtile->pack_score = max_ff(w, h) / min_ff(w, h) * w * h;

      BKE_image_release_ibuf(ima, ibuf, NULL);
      BLI_addtail(&boxes, packtile);
    }
  }

  BLI_assert(arraywidth > 0 && arrayheight > 0);

  BLI_listbase_sort(&boxes, compare_packtile);
  int arraylayers = 0;
  /* Keep adding layers until all tiles are packed. */
  while (boxes.first != NULL) {
    ListBase packed = {NULL};
    BLI_box_pack_2d_fixedarea(&boxes, arraywidth, arrayheight, &packed);
    BLI_assert(packed.first != NULL);

    LISTBASE_FOREACH (PackTile *, packtile, &packed) {
      ImageTile *tile = packtile->tile;
      int *tileoffset = tile->runtime.tilearray_offset;
      int *tilesize = tile->runtime.tilearray_size;

      tileoffset[0] = packtile->boxpack.x;
      tileoffset[1] = packtile->boxpack.y;
      tilesize[0] = packtile->boxpack.w;
      tilesize[1] = packtile->boxpack.h;
      tile->runtime.tilearray_layer = arraylayers;
    }

    BLI_freelistN(&packed);
    arraylayers++;
  }

  const bool use_high_bitdepth = (ima->flag & IMA_HIGH_BITDEPTH);
  /* Create Texture without content. */
  GPUTexture *tex = IMB_touch_gpu_texture(
      ima->id.name + 2, main_ibuf, arraywidth, arrayheight, arraylayers, use_high_bitdepth);

  /* Upload each tile one by one. */
  LISTBASE_FOREACH (ImageTile *, tile, &ima->tiles) {
    int tilelayer = tile->runtime.tilearray_layer;
    int *tileoffset = tile->runtime.tilearray_offset;
    int *tilesize = tile->runtime.tilearray_size;

    if (tilesize[0] == 0 || tilesize[1] == 0) {
      continue;
    }

    ImageUser iuser;
    BKE_imageuser_default(&iuser);
    iuser.tile = tile->tile_number;
    ImBuf *ibuf = BKE_image_acquire_ibuf(ima, &iuser, NULL);

    if (ibuf) {
      const bool store_premultiplied = ibuf->rect_float ? (ima->alpha_mode != IMA_ALPHA_STRAIGHT) :
                                                          (ima->alpha_mode == IMA_ALPHA_PREMUL);
      IMB_update_gpu_texture_sub(tex,
                                 ibuf,
                                 UNPACK2(tileoffset),
                                 tilelayer,
                                 UNPACK2(tilesize),
                                 use_high_bitdepth,
                                 store_premultiplied);
    }

    BKE_image_release_ibuf(ima, ibuf, NULL);
  }

  if (GPU_mipmap_enabled()) {
    GPU_texture_generate_mipmap(tex);
    GPU_texture_mipmap_mode(tex, true, true);
    if (ima) {
      ima->gpuflag |= IMA_GPU_MIPMAP_COMPLETE;
    }
  }
  else {
    GPU_texture_mipmap_mode(tex, false, true);
  }

  return tex;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Regular gpu texture
 * \{ */

static GPUTexture **get_image_gpu_texture_ptr(Image *ima,
                                              eGPUTextureTarget textarget,
                                              const int multiview_eye)
{
  const bool in_range = (textarget >= 0) && (textarget < TEXTARGET_COUNT);
  BLI_assert(in_range);

  if (in_range) {
    return &(ima->gputexture[textarget][multiview_eye]);
  }
  return NULL;
}

static GPUTexture *image_gpu_texture_error_create(eGPUTextureTarget textarget)
{
  fprintf(stderr, "GPUTexture: Blender Texture Not Loaded!\n");
  switch (textarget) {
    case TEXTARGET_2D_ARRAY:
      return GPU_texture_create_error(2, true);
    case TEXTARGET_TILE_MAPPING:
      return GPU_texture_create_error(1, true);
    case TEXTARGET_2D:
    default:
      return GPU_texture_create_error(2, false);
  }
}

static GPUTexture *image_get_gpu_texture(Image *ima,
                                         ImageUser *iuser,
                                         ImBuf *ibuf,
                                         eGPUTextureTarget textarget)
{
  if (ima == NULL) {
    return NULL;
  }

  /* Free any unused GPU textures, since we know we are in a thread with OpenGL
   * context and might as well ensure we have as much space free as possible. */
  gpu_free_unused_buffers();

  /* currently, gpu refresh tagging is used by ima sequences */
  if (ima->gpuflag & IMA_GPU_REFRESH) {
    image_free_gpu(ima, true);
    ima->gpuflag &= ~IMA_GPU_REFRESH;
  }

  /* Tag as in active use for garbage collector. */
  BKE_image_tag_time(ima);

  /* Test if we already have a texture. */
  GPUTexture **tex = get_image_gpu_texture_ptr(ima, textarget, iuser ? iuser->multiview_eye : 0);
  if (*tex) {
    return *tex;
  }

  /* Check if we have a valid image. If not, we return a dummy
   * texture with zero bind-code so we don't keep trying. */
  ImageTile *tile = BKE_image_get_tile(ima, 0);
  if (tile == NULL || tile->ok == 0) {
    *tex = image_gpu_texture_error_create(textarget);
    return *tex;
  }

  /* check if we have a valid image buffer */
  ImBuf *ibuf_intern = ibuf;
  if (ibuf_intern == NULL) {
    ibuf_intern = BKE_image_acquire_ibuf(ima, iuser, NULL);
    if (ibuf_intern == NULL) {
      *tex = image_gpu_texture_error_create(textarget);
      return *tex;
    }
  }

  if (textarget == TEXTARGET_2D_ARRAY) {
    *tex = gpu_texture_create_tile_array(ima, ibuf_intern);
  }
  else if (textarget == TEXTARGET_TILE_MAPPING) {
    *tex = gpu_texture_create_tile_mapping(ima, iuser ? iuser->multiview_eye : 0);
  }
  else {
    const bool use_high_bitdepth = (ima->flag & IMA_HIGH_BITDEPTH);
    const bool store_premultiplied = ibuf_intern->rect_float ?
                                         (ima ? (ima->alpha_mode != IMA_ALPHA_STRAIGHT) : false) :
                                         (ima ? (ima->alpha_mode == IMA_ALPHA_PREMUL) : true);

    *tex = IMB_create_gpu_texture(
        ima->id.name + 2, ibuf_intern, use_high_bitdepth, store_premultiplied);

    GPU_texture_wrap_mode(*tex, true, false);

    if (GPU_mipmap_enabled()) {
      GPU_texture_generate_mipmap(*tex);
      if (ima) {
        ima->gpuflag |= IMA_GPU_MIPMAP_COMPLETE;
      }
      GPU_texture_mipmap_mode(*tex, true, true);
    }
    else {
      GPU_texture_mipmap_mode(*tex, false, true);
    }
  }

  /* if `ibuf` was given, we don't own the `ibuf_intern` */
  if (ibuf == NULL) {
    BKE_image_release_ibuf(ima, ibuf_intern, NULL);
  }

  GPU_texture_orig_size_set(*tex, ibuf_intern->x, ibuf_intern->y);

  return *tex;
}

GPUTexture *BKE_image_get_gpu_texture(Image *image, ImageUser *iuser, ImBuf *ibuf)
{
  return image_get_gpu_texture(image, iuser, ibuf, TEXTARGET_2D);
}

GPUTexture *BKE_image_get_gpu_tiles(Image *image, ImageUser *iuser, ImBuf *ibuf)
{
  return image_get_gpu_texture(image, iuser, ibuf, TEXTARGET_2D_ARRAY);
}

GPUTexture *BKE_image_get_gpu_tilemap(Image *image, ImageUser *iuser, ImBuf *ibuf)
{
  return image_get_gpu_texture(image, iuser, ibuf, TEXTARGET_TILE_MAPPING);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Delayed GPU texture free
 *
 * Image datablocks can be deleted by any thread, but there may not be any active OpenGL context.
 * In that case we push them into a queue and free the buffers later.
 * \{ */

static LinkNode *gpu_texture_free_queue = NULL;
static ThreadMutex gpu_texture_queue_mutex = BLI_MUTEX_INITIALIZER;

static void gpu_free_unused_buffers(void)
{
  if (gpu_texture_free_queue == NULL) {
    return;
  }

  BLI_mutex_lock(&gpu_texture_queue_mutex);

  while (gpu_texture_free_queue != NULL) {
    GPUTexture *tex = BLI_linklist_pop(&gpu_texture_free_queue);
    GPU_texture_free(tex);
  }

  BLI_mutex_unlock(&gpu_texture_queue_mutex);
}

void BKE_image_free_unused_gpu_textures()
{
  if (BLI_thread_is_main()) {
    gpu_free_unused_buffers();
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Deletion
 * \{ */

static void image_free_gpu(Image *ima, const bool immediate)
{
  for (int eye = 0; eye < 2; eye++) {
    for (int i = 0; i < TEXTARGET_COUNT; i++) {
      if (ima->gputexture[i][eye] != NULL) {
        if (immediate) {
          GPU_texture_free(ima->gputexture[i][eye]);
        }
        else {
          BLI_mutex_lock(&gpu_texture_queue_mutex);
          BLI_linklist_prepend(&gpu_texture_free_queue, ima->gputexture[i][eye]);
          BLI_mutex_unlock(&gpu_texture_queue_mutex);
        }

        ima->gputexture[i][eye] = NULL;
      }
    }
  }

  ima->gpuflag &= ~IMA_GPU_MIPMAP_COMPLETE;
}

void BKE_image_free_gputextures(Image *ima)
{
  image_free_gpu(ima, BLI_thread_is_main());
}

void BKE_image_free_all_gputextures(Main *bmain)
{
  if (bmain) {
    LISTBASE_FOREACH (Image *, ima, &bmain->images) {
      BKE_image_free_gputextures(ima);
    }
  }
}

/* same as above but only free animated images */
void BKE_image_free_anim_gputextures(Main *bmain)
{
  if (bmain) {
    LISTBASE_FOREACH (Image *, ima, &bmain->images) {
      if (BKE_image_is_animated(ima)) {
        BKE_image_free_gputextures(ima);
      }
    }
  }
}

void BKE_image_free_old_gputextures(Main *bmain)
{
  static int lasttime = 0;
  int ctime = (int)PIL_check_seconds_timer();

  /*
   * Run garbage collector once for every collecting period of time
   * if textimeout is 0, that's the option to NOT run the collector
   */
  if (U.textimeout == 0 || ctime % U.texcollectrate || ctime == lasttime) {
    return;
  }

  /* of course not! */
  if (G.is_rendering) {
    return;
  }

  lasttime = ctime;

  LISTBASE_FOREACH (Image *, ima, &bmain->images) {
    if ((ima->flag & IMA_NOCOLLECT) == 0 && ctime - ima->lastused > U.textimeout) {
      /* If it's in GL memory, deallocate and set time tag to current time
       * This gives textures a "second chance" to be used before dying. */
      if (BKE_image_has_opengl_texture(ima)) {
        BKE_image_free_gputextures(ima);
        ima->lastused = ctime;
      }
      /* Otherwise, just kill the buffers */
      else {
        BKE_image_free_buffers(ima);
      }
    }
  }
}
/** \} */

/* -------------------------------------------------------------------- */
/** \name Paint Update
 * \{ */

static ImBuf *update_do_scale(uchar *rect,
                              float *rect_float,
                              int *x,
                              int *y,
                              int *w,
                              int *h,
                              int limit_w,
                              int limit_h,
                              int full_w,
                              int full_h)
{
  /* Partial update with scaling. */
  float xratio = limit_w / (float)full_w;
  float yratio = limit_h / (float)full_h;

  int part_w = *w, part_h = *h;

  /* Find sub coordinates in scaled image. Take ceiling because we will be
   * losing 1 pixel due to rounding errors in x,y. */
  *x *= xratio;
  *y *= yratio;
  *w = (int)ceil(xratio * (*w));
  *h = (int)ceil(yratio * (*h));

  /* ...but take back if we are over the limit! */
  if (*x + *w > limit_w) {
    (*w)--;
  }
  if (*y + *h > limit_h) {
    (*h)--;
  }

  /* Scale pixels. */
  ImBuf *ibuf = IMB_allocFromBuffer((uint *)rect, rect_float, part_w, part_h, 4);
  IMB_scaleImBuf(ibuf, *w, *h);

  return ibuf;
}

static void gpu_texture_update_scaled(GPUTexture *tex,
                                      uchar *rect,
                                      float *rect_float,
                                      int full_w,
                                      int full_h,
                                      int x,
                                      int y,
                                      int layer,
                                      const int *tile_offset,
                                      const int *tile_size,
                                      int w,
                                      int h)
{
  ImBuf *ibuf;
  if (layer > -1) {
    ibuf = update_do_scale(
        rect, rect_float, &x, &y, &w, &h, tile_size[0], tile_size[1], full_w, full_h);

    /* Shift to account for tile packing. */
    x += tile_offset[0];
    y += tile_offset[1];
  }
  else {
    /* Partial update with scaling. */
    int limit_w = smaller_power_of_2_limit(full_w);
    int limit_h = smaller_power_of_2_limit(full_h);

    ibuf = update_do_scale(rect, rect_float, &x, &y, &w, &h, limit_w, limit_h, full_w, full_h);
  }

  void *data = (ibuf->rect_float) ? (void *)(ibuf->rect_float) : (void *)(ibuf->rect);
  eGPUDataFormat data_format = (ibuf->rect_float) ? GPU_DATA_FLOAT : GPU_DATA_UNSIGNED_BYTE;

  GPU_texture_update_sub(tex, data_format, data, x, y, layer, w, h, 1);

  IMB_freeImBuf(ibuf);
}

static void gpu_texture_update_unscaled(GPUTexture *tex,
                                        uchar *rect,
                                        float *rect_float,
                                        int x,
                                        int y,
                                        int layer,
                                        const int tile_offset[2],
                                        int w,
                                        int h,
                                        int tex_stride,
                                        int tex_offset)
{
  if (layer > -1) {
    /* Shift to account for tile packing. */
    x += tile_offset[0];
    y += tile_offset[1];
  }

  void *data = (rect_float) ? (void *)(rect_float + tex_offset) : (void *)(rect + tex_offset);
  eGPUDataFormat data_format = (rect_float) ? GPU_DATA_FLOAT : GPU_DATA_UNSIGNED_BYTE;

  /* Partial update without scaling. Stride and offset are used to copy only a
   * subset of a possible larger buffer than what we are updating. */
  GPU_unpack_row_length_set(tex_stride);

  GPU_texture_update_sub(tex, data_format, data, x, y, layer, w, h, 1);
  /* Restore default. */
  GPU_unpack_row_length_set(0);
}

static void gpu_texture_update_from_ibuf(
    GPUTexture *tex, Image *ima, ImBuf *ibuf, ImageTile *tile, int x, int y, int w, int h)
{
  bool scaled;
  if (tile != NULL) {
    int *tilesize = tile->runtime.tilearray_size;
    scaled = (ibuf->x != tilesize[0]) || (ibuf->y != tilesize[1]);
  }
  else {
    scaled = is_over_resolution_limit(ibuf->x, ibuf->y);
  }

  if (scaled) {
    /* Extra padding to account for bleed from neighboring pixels. */
    const int padding = 4;
    const int xmax = min_ii(x + w + padding, ibuf->x);
    const int ymax = min_ii(y + h + padding, ibuf->y);
    x = max_ii(x - padding, 0);
    y = max_ii(y - padding, 0);
    w = xmax - x;
    h = ymax - y;
  }

  /* Get texture data pointers. */
  float *rect_float = ibuf->rect_float;
  uchar *rect = (uchar *)ibuf->rect;
  int tex_stride = ibuf->x;
  int tex_offset = ibuf->channels * (y * ibuf->x + x);

  if (rect_float == NULL) {
    /* Byte pixels. */
    if (!IMB_colormanagement_space_is_data(ibuf->rect_colorspace)) {
      const bool compress_as_srgb = !IMB_colormanagement_space_is_scene_linear(
          ibuf->rect_colorspace);

      rect = (uchar *)MEM_mallocN(sizeof(uchar[4]) * w * h, __func__);
      if (rect == NULL) {
        return;
      }

      tex_stride = w;
      tex_offset = 0;

      /* Convert to scene linear with sRGB compression, and premultiplied for
       * correct texture interpolation. */
      const bool store_premultiplied = (ima->alpha_mode == IMA_ALPHA_PREMUL);
      IMB_colormanagement_imbuf_to_byte_texture(
          rect, x, y, w, h, ibuf, compress_as_srgb, store_premultiplied);
    }
  }
  else {
    /* Float pixels. */
    const bool store_premultiplied = (ima->alpha_mode != IMA_ALPHA_STRAIGHT);

    if (ibuf->channels != 4 || scaled || !store_premultiplied) {
      rect_float = (float *)MEM_mallocN(sizeof(float[4]) * w * h, __func__);
      if (rect_float == NULL) {
        return;
      }

      tex_stride = w;
      tex_offset = 0;

      IMB_colormanagement_imbuf_to_float_texture(
          rect_float, x, y, w, h, ibuf, store_premultiplied);
    }
  }

  if (scaled) {
    /* Slower update where we first have to scale the input pixels. */
    if (tile != NULL) {
      int *tileoffset = tile->runtime.tilearray_offset;
      int *tilesize = tile->runtime.tilearray_size;
      int tilelayer = tile->runtime.tilearray_layer;
      gpu_texture_update_scaled(
          tex, rect, rect_float, ibuf->x, ibuf->y, x, y, tilelayer, tileoffset, tilesize, w, h);
    }
    else {
      gpu_texture_update_scaled(
          tex, rect, rect_float, ibuf->x, ibuf->y, x, y, -1, NULL, NULL, w, h);
    }
  }
  else {
    /* Fast update at same resolution. */
    if (tile != NULL) {
      int *tileoffset = tile->runtime.tilearray_offset;
      int tilelayer = tile->runtime.tilearray_layer;
      gpu_texture_update_unscaled(
          tex, rect, rect_float, x, y, tilelayer, tileoffset, w, h, tex_stride, tex_offset);
    }
    else {
      gpu_texture_update_unscaled(
          tex, rect, rect_float, x, y, -1, NULL, w, h, tex_stride, tex_offset);
    }
  }

  /* Free buffers if needed. */
  if (rect && rect != (uchar *)ibuf->rect) {
    MEM_freeN(rect);
  }
  if (rect_float && rect_float != ibuf->rect_float) {
    MEM_freeN(rect_float);
  }

  if (GPU_mipmap_enabled()) {
    GPU_texture_generate_mipmap(tex);
  }
  else {
    ima->gpuflag &= ~IMA_GPU_MIPMAP_COMPLETE;
  }

  GPU_texture_unbind(tex);
}

/* Partial update of texture for texture painting. This is often much
 * quicker than fully updating the texture for high resolution images. */
void BKE_image_update_gputexture(Image *ima, ImageUser *iuser, int x, int y, int w, int h)
{
  ImBuf *ibuf = BKE_image_acquire_ibuf(ima, iuser, NULL);
  ImageTile *tile = BKE_image_get_tile_from_iuser(ima, iuser);

  if ((ibuf == NULL) || (w == 0) || (h == 0)) {
    /* Full reload of texture. */
    BKE_image_free_gputextures(ima);
  }

  GPUTexture *tex = ima->gputexture[TEXTARGET_2D][0];
  /* Check if we need to update the main gputexture. */
  if (tex != NULL && tile == ima->tiles.first) {
    gpu_texture_update_from_ibuf(tex, ima, ibuf, NULL, x, y, w, h);
  }

  /* Check if we need to update the array gputexture. */
  tex = ima->gputexture[TEXTARGET_2D_ARRAY][0];
  if (tex != NULL) {
    gpu_texture_update_from_ibuf(tex, ima, ibuf, tile, x, y, w, h);
  }

  BKE_image_release_ibuf(ima, ibuf, NULL);
}

/* these two functions are called on entering and exiting texture paint mode,
 * temporary disabling/enabling mipmapping on all images for quick texture
 * updates with glTexSubImage2D. images that didn't change don't have to be
 * re-uploaded to OpenGL */
void BKE_image_paint_set_mipmap(Main *bmain, bool mipmap)
{
  LISTBASE_FOREACH (Image *, ima, &bmain->images) {
    if (BKE_image_has_opengl_texture(ima)) {
      if (ima->gpuflag & IMA_GPU_MIPMAP_COMPLETE) {
        for (int eye = 0; eye < 2; eye++) {
          for (int a = 0; a < TEXTARGET_COUNT; a++) {
            if (ELEM(a, TEXTARGET_2D, TEXTARGET_2D_ARRAY)) {
              GPUTexture *tex = ima->gputexture[a][eye];
              if (tex != NULL) {
                GPU_texture_mipmap_mode(tex, mipmap, true);
              }
            }
          }
        }
      }
      else {
        BKE_image_free_gputextures(ima);
      }
    }
    else {
      ima->gpuflag &= ~IMA_GPU_MIPMAP_COMPLETE;
    }
  }
}

/** \} */
