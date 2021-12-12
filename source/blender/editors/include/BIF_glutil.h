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
 * \ingroup editorui
 */

#pragma once

#include "GPU_texture.h"

#ifdef __cplusplus
extern "C" {
#endif

struct rcti;

struct ColorManagedDisplaySettings;
struct ColorManagedViewSettings;
struct ImBuf;
struct bContext;

typedef struct IMMDrawPixelsTexState {
  struct GPUShader *shader;
  unsigned int pos;
  unsigned int texco;
  bool do_shader_unbind;
} IMMDrawPixelsTexState;

/* To be used before calling immDrawPixelsTex
 * Default shader is GPU_SHADER_2D_IMAGE_COLOR
 * Returns a shader to be able to set uniforms */
/**
 * To be used before calling #immDrawPixelsTex
 * Default shader is #GPU_SHADER_2D_IMAGE_COLOR
 * You can still set uniforms with:
 * `GPU_shader_uniform_int(shader, GPU_shader_get_uniform(shader, "name"), 0);`
 */
IMMDrawPixelsTexState immDrawPixelsTexSetup(int builtin);

/**
 * #immDrawPixelsTex - Functions like a limited #glDrawPixels, but actually draws the
 * image using textures, which can be tremendously faster on low-end
 * cards, and also avoids problems with the raster position being
 * clipped when off-screen. Pixel unpacking parameters and
 * the #glPixelZoom values are _not_ respected.
 *
 * \attention Use #immDrawPixelsTexSetup before calling this function.
 *
 * \attention This routine makes many assumptions: the `rect` data
 * is expected to be in RGBA byte or float format, and the
 * model-view and projection matrices are assumed to define a
 * 1-to-1 mapping to screen space.
 */
void immDrawPixelsTex(IMMDrawPixelsTexState *state,
                      float x,
                      float y,
                      int img_w,
                      int img_h,
                      eGPUTextureFormat gpu_format,
                      bool use_filter,
                      void *rect,
                      float xzoom,
                      float yzoom,
                      const float color[4]);
void immDrawPixelsTex_clipping(IMMDrawPixelsTexState *state,
                               float x,
                               float y,
                               int img_w,
                               int img_h,
                               eGPUTextureFormat gpu_format,
                               bool use_filter,
                               void *rect,
                               float clip_min_x,
                               float clip_min_y,
                               float clip_max_x,
                               float clip_max_y,
                               float xzoom,
                               float yzoom,
                               const float color[4]);
void immDrawPixelsTexScaled(IMMDrawPixelsTexState *state,
                            float x,
                            float y,
                            int img_w,
                            int img_h,
                            eGPUTextureFormat gpu_format,
                            bool use_filter,
                            void *rect,
                            float scaleX,
                            float scaleY,
                            float xzoom,
                            float yzoom,
                            const float color[4]);
/**
 * Use the currently bound shader.
 *
 * Use #immDrawPixelsTexSetup to bind the shader you
 * want before calling #immDrawPixelsTex.
 *
 * If using a special shader double check it uses the same
 * attributes "pos" "texCoord" and uniform "image".
 *
 * If color is NULL then use white by default
 *
 * Be also aware that this function unbinds the shader when
 * it's finished.
 */
void immDrawPixelsTexScaled_clipping(IMMDrawPixelsTexState *state,
                                     float x,
                                     float y,
                                     int img_w,
                                     int img_h,
                                     eGPUTextureFormat gpu_format,
                                     bool use_filter,
                                     void *rect,
                                     float scaleX,
                                     float scaleY,
                                     float clip_min_x,
                                     float clip_min_y,
                                     float clip_max_x,
                                     float clip_max_y,
                                     float xzoom,
                                     float yzoom,
                                     const float color[4]);

/* Image buffer drawing functions, with display transform
 *
 * The view and display settings can either be specified manually,
 * or retrieved from the context with the '_ctx' variations.
 *
 * For better performance clipping coordinates can be specified so parts of the
 * image outside the view are skipped. */

void ED_draw_imbuf(struct ImBuf *ibuf,
                   float x,
                   float y,
                   bool use_filter,
                   struct ColorManagedViewSettings *view_settings,
                   struct ColorManagedDisplaySettings *display_settings,
                   float zoom_x,
                   float zoom_y);
/**
 * Draw given image buffer on a screen using GLSL for display transform.
 */
void ED_draw_imbuf_clipping(struct ImBuf *ibuf,
                            float x,
                            float y,
                            bool use_filter,
                            struct ColorManagedViewSettings *view_settings,
                            struct ColorManagedDisplaySettings *display_settings,
                            float clip_min_x,
                            float clip_min_y,
                            float clip_max_x,
                            float clip_max_y,
                            float zoom_x,
                            float zoom_y);

void ED_draw_imbuf_ctx(const struct bContext *C,
                       struct ImBuf *ibuf,
                       float x,
                       float y,
                       bool use_filter,
                       float zoom_x,
                       float zoom_y);
void ED_draw_imbuf_ctx_clipping(const struct bContext *C,
                                struct ImBuf *ibuf,
                                float x,
                                float y,
                                bool use_filter,
                                float clip_min_x,
                                float clip_min_y,
                                float clip_max_x,
                                float clip_max_y,
                                float zoom_x,
                                float zoom_y);

int ED_draw_imbuf_method(struct ImBuf *ibuf);

/**
 * Don't move to `GPU_immediate_util.h` because this uses user-prefs and isn't very low level.
 */
void immDrawBorderCorners(unsigned int pos, const struct rcti *border, float zoomx, float zoomy);

#ifdef __cplusplus
}
#endif
