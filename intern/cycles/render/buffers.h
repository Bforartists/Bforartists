/*
 * Copyright 2011-2013 Blender Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef __BUFFERS_H__
#define __BUFFERS_H__

#include "device/device_memory.h"

#include "render/film.h"

#include "kernel/kernel_types.h"

#include "util/util_half.h"
#include "util/util_string.h"
#include "util/util_thread.h"
#include "util/util_types.h"

CCL_NAMESPACE_BEGIN

class Device;
struct DeviceDrawParams;
struct float4;

/* Buffer Parameters
 * Size of render buffer and how it fits in the full image (border render). */

class BufferParams {
 public:
  /* width/height of the physical buffer */
  int width;
  int height;

  /* offset into and width/height of the full buffer */
  int full_x;
  int full_y;
  int full_width;
  int full_height;

  /* passes */
  vector<Pass> passes;
  bool denoising_data_pass;
  /* If only some light path types should be target, an additional pass is needed. */
  bool denoising_clean_pass;
  /* When we're prefiltering the passes during rendering, we need to keep both the
   * original and the prefiltered data around because neighboring tiles might still
   * need the original data. */
  bool denoising_prefiltered_pass;

  /* functions */
  BufferParams();

  void get_offset_stride(int &offset, int &stride);
  bool modified(const BufferParams &params);
  int get_passes_size();
  int get_denoising_offset();
  int get_denoising_prefiltered_offset();
};

/* Render Buffers */

class RenderBuffers {
 public:
  /* buffer parameters */
  BufferParams params;

  /* float buffer */
  device_vector<float> buffer;
  bool map_neighbor_copied;
  double render_time;

  explicit RenderBuffers(Device *device);
  ~RenderBuffers();

  void reset(BufferParams &params);
  void zero();

  bool copy_from_device();
  bool get_pass_rect(
      const string &name, float exposure, int sample, int components, float *pixels);
  bool get_denoising_pass_rect(
      int offset, float exposure, int sample, int components, float *pixels);
  bool set_pass_rect(PassType type, int components, float *pixels, int samples);
};

/* Display Buffer
 *
 * The buffer used for drawing during render, filled by converting the render
 * buffers to byte of half float storage */

class DisplayBuffer {
 public:
  /* buffer parameters */
  BufferParams params;
  /* dimensions for how much of the buffer is actually ready for display.
   * with progressive render we can be using only a subset of the buffer.
   * if these are zero, it means nothing can be drawn yet */
  int draw_width, draw_height;
  /* draw alpha channel? */
  bool transparent;
  /* use half float? */
  bool half_float;
  /* byte buffer for converted result */
  device_pixels<uchar4> rgba_byte;
  device_pixels<half4> rgba_half;

  DisplayBuffer(Device *device, bool linear = false);
  ~DisplayBuffer();

  void reset(BufferParams &params);

  void draw_set(int width, int height);
  void draw(Device *device, const DeviceDrawParams &draw_params);
  bool draw_ready();
};

/* Render Tile
 * Rendering task on a buffer */

class RenderTile {
 public:
  typedef enum { PATH_TRACE = (1 << 0), BAKE = (1 << 1), DENOISE = (1 << 2) } Task;

  Task task;
  int x, y, w, h;
  int start_sample;
  int num_samples;
  int sample;
  int resolution;
  int offset;
  int stride;
  int tile_index;

  device_ptr buffer;
  int device_size;

  typedef enum { NO_STEALING = 0, CAN_BE_STOLEN = 1, WAS_STOLEN = 2 } StealingState;
  StealingState stealing_state;

  RenderBuffers *buffers;

  RenderTile();

  int4 bounds() const
  {
    return make_int4(x,      /* xmin */
                     y,      /* ymin */
                     x + w,  /* xmax */
                     y + h); /* ymax */
  }
};

/* Render Tile Neighbors
 * Set of neighboring tiles used for denoising. Tile order:
 *  0 1 2
 *  3 4 5
 *  6 7 8 */

class RenderTileNeighbors {
 public:
  static const int SIZE = 9;
  static const int CENTER = 4;

  RenderTile tiles[SIZE];
  RenderTile target;

  RenderTileNeighbors(const RenderTile &center)
  {
    tiles[CENTER] = center;
  }

  int4 bounds() const
  {
    return make_int4(tiles[3].x,               /* xmin */
                     tiles[1].y,               /* ymin */
                     tiles[5].x + tiles[5].w,  /* xmax */
                     tiles[7].y + tiles[7].h); /* ymax */
  }

  void set_bounds_from_center()
  {
    tiles[3].x = tiles[CENTER].x;
    tiles[1].y = tiles[CENTER].y;
    tiles[5].x = tiles[CENTER].x + tiles[CENTER].w;
    tiles[7].y = tiles[CENTER].y + tiles[CENTER].h;
  }
};

CCL_NAMESPACE_END

#endif /* __BUFFERS_H__ */
