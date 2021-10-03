/*
 * Copyright 2021 Blender Foundation
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

#include "integrator/path_trace_display.h"

#include "render/buffers.h"

#include "util/util_logging.h"

CCL_NAMESPACE_BEGIN

PathTraceDisplay::PathTraceDisplay(unique_ptr<DisplayDriver> driver) : driver_(move(driver))
{
}

void PathTraceDisplay::reset(const BufferParams &buffer_params)
{
  thread_scoped_lock lock(mutex_);

  const DisplayDriver::Params old_params = params_;

  params_.full_offset = make_int2(buffer_params.full_x, buffer_params.full_y);
  params_.full_size = make_int2(buffer_params.full_width, buffer_params.full_height);
  params_.size = make_int2(buffer_params.width, buffer_params.height);

  /* If the parameters did change tag texture as unusable. This avoids drawing old texture content
   * in an updated configuration of the viewport. For example, avoids drawing old frame when render
   * border did change.
   * If the parameters did not change, allow drawing the current state of the texture, which will
   * not count as an up-to-date redraw. This will avoid flickering when doping camera navigation by
   * showing a previously rendered frame for until the new one is ready. */
  if (old_params.modified(params_)) {
    texture_state_.is_usable = false;
  }

  texture_state_.is_outdated = true;
}

void PathTraceDisplay::mark_texture_updated()
{
  texture_state_.is_outdated = false;
  texture_state_.is_usable = true;
}

/* --------------------------------------------------------------------
 * Update procedure.
 */

bool PathTraceDisplay::update_begin(int texture_width, int texture_height)
{
  DCHECK(!update_state_.is_active);

  if (update_state_.is_active) {
    LOG(ERROR) << "Attempt to re-activate update process.";
    return false;
  }

  /* Get parameters within a mutex lock, to avoid reset() modifying them at the same time.
   * The update itself is non-blocking however, for better performance and to avoid
   * potential deadlocks due to locks held by the subclass. */
  DisplayDriver::Params params;
  {
    thread_scoped_lock lock(mutex_);
    params = params_;
    texture_state_.size = make_int2(texture_width, texture_height);
  }

  if (!driver_->update_begin(params, texture_width, texture_height)) {
    LOG(ERROR) << "PathTraceDisplay implementation could not begin update.";
    return false;
  }

  update_state_.is_active = true;

  return true;
}

void PathTraceDisplay::update_end()
{
  DCHECK(update_state_.is_active);

  if (!update_state_.is_active) {
    LOG(ERROR) << "Attempt to deactivate inactive update process.";
    return;
  }

  driver_->update_end();

  update_state_.is_active = false;
}

int2 PathTraceDisplay::get_texture_size() const
{
  return texture_state_.size;
}

/* --------------------------------------------------------------------
 * Texture update from CPU buffer.
 */

void PathTraceDisplay::copy_pixels_to_texture(
    const half4 *rgba_pixels, int texture_x, int texture_y, int pixels_width, int pixels_height)
{
  DCHECK(update_state_.is_active);

  if (!update_state_.is_active) {
    LOG(ERROR) << "Attempt to copy pixels data outside of PathTraceDisplay update.";
    return;
  }

  mark_texture_updated();

  /* This call copies pixels to a mapped texture buffer which is typically much cheaper from CPU
   * time point of view than to copy data directly to a texture.
   *
   * The possible downside of this approach is that it might require a higher peak memory when
   * doing partial updates of the texture (although, in practice even partial updates might peak
   * with a full-frame buffer stored on the CPU if the GPU is currently occupied). */
  half4 *mapped_rgba_pixels = map_texture_buffer();
  if (!mapped_rgba_pixels) {
    return;
  }

  const int texture_width = texture_state_.size.x;
  const int texture_height = texture_state_.size.y;

  if (texture_x == 0 && texture_y == 0 && pixels_width == texture_width &&
      pixels_height == texture_height) {
    const size_t size_in_bytes = sizeof(half4) * texture_width * texture_height;
    memcpy(mapped_rgba_pixels, rgba_pixels, size_in_bytes);
  }
  else {
    const half4 *rgba_row = rgba_pixels;
    half4 *mapped_rgba_row = mapped_rgba_pixels + texture_y * texture_width + texture_x;
    for (int y = 0; y < pixels_height;
         ++y, rgba_row += pixels_width, mapped_rgba_row += texture_width) {
      memcpy(mapped_rgba_row, rgba_row, sizeof(half4) * pixels_width);
    }
  }

  unmap_texture_buffer();
}

/* --------------------------------------------------------------------
 * Texture buffer mapping.
 */

half4 *PathTraceDisplay::map_texture_buffer()
{
  DCHECK(!texture_buffer_state_.is_mapped);
  DCHECK(update_state_.is_active);

  if (texture_buffer_state_.is_mapped) {
    LOG(ERROR) << "Attempt to re-map an already mapped texture buffer.";
    return nullptr;
  }

  if (!update_state_.is_active) {
    LOG(ERROR) << "Attempt to copy pixels data outside of PathTraceDisplay update.";
    return nullptr;
  }

  half4 *mapped_rgba_pixels = driver_->map_texture_buffer();

  if (mapped_rgba_pixels) {
    texture_buffer_state_.is_mapped = true;
  }

  return mapped_rgba_pixels;
}

void PathTraceDisplay::unmap_texture_buffer()
{
  DCHECK(texture_buffer_state_.is_mapped);

  if (!texture_buffer_state_.is_mapped) {
    LOG(ERROR) << "Attempt to unmap non-mapped texture buffer.";
    return;
  }

  texture_buffer_state_.is_mapped = false;

  mark_texture_updated();
  driver_->unmap_texture_buffer();
}

/* --------------------------------------------------------------------
 * Graphics interoperability.
 */

DisplayDriver::GraphicsInterop PathTraceDisplay::graphics_interop_get()
{
  DCHECK(!texture_buffer_state_.is_mapped);
  DCHECK(update_state_.is_active);

  if (texture_buffer_state_.is_mapped) {
    LOG(ERROR)
        << "Attempt to use graphics interoperability mode while the texture buffer is mapped.";
    return DisplayDriver::GraphicsInterop();
  }

  if (!update_state_.is_active) {
    LOG(ERROR) << "Attempt to use graphics interoperability outside of PathTraceDisplay update.";
    return DisplayDriver::GraphicsInterop();
  }

  /* Assume that interop will write new values to the texture. */
  mark_texture_updated();

  return driver_->graphics_interop_get();
}

void PathTraceDisplay::graphics_interop_activate()
{
  driver_->graphics_interop_activate();
}

void PathTraceDisplay::graphics_interop_deactivate()
{
  driver_->graphics_interop_deactivate();
}

/* --------------------------------------------------------------------
 * Drawing.
 */

void PathTraceDisplay::clear()
{
  driver_->clear();
}

bool PathTraceDisplay::draw()
{
  /* Get parameters within a mutex lock, to avoid reset() modifying them at the same time.
   * The drawing itself is non-blocking however, for better performance and to avoid
   * potential deadlocks due to locks held by the subclass. */
  DisplayDriver::Params params;
  bool is_usable;
  bool is_outdated;

  {
    thread_scoped_lock lock(mutex_);
    params = params_;
    is_usable = texture_state_.is_usable;
    is_outdated = texture_state_.is_outdated;
  }

  if (is_usable) {
    driver_->draw(params);
  }

  return !is_outdated;
}

CCL_NAMESPACE_END
