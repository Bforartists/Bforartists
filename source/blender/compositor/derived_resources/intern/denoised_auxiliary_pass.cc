/* SPDX-FileCopyrightText: 2025 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#ifdef WITH_OPENIMAGEDENOISE

#  include <cstdint>
#  include <memory>

#  include "BLI_assert.h"
#  include "BLI_hash.hh"

#  include "MEM_guardedalloc.h"

#  include "GPU_state.hh"
#  include "GPU_texture.hh"

#  include "COM_context.hh"
#  include "COM_denoised_auxiliary_pass.hh"
#  include "COM_result.hh"

#  include <OpenImageDenoise/oidn.hpp>

namespace blender::compositor {

/* ------------------------------------------------------------------------------------------------
 * Denoised Auxiliary Pass Key.
 */
DenoisedAuxiliaryPassKey::DenoisedAuxiliaryPassKey(const DenoisedAuxiliaryPassType type,
                                                   const oidn::Quality quality)
    : type(type), quality(quality)
{
}

uint64_t DenoisedAuxiliaryPassKey::hash() const
{
  return get_default_hash(this->type, this->quality);
}

bool operator==(const DenoisedAuxiliaryPassKey &a, const DenoisedAuxiliaryPassKey &b)
{
  return a.type == b.type && a.quality == b.quality;
}

/* --------------------------------------------------------------------
 * Denoised Auxiliary Pass.
 */

/* A callback to cancel the filter operations by evaluating the context's is_canceled method. The
 * API specifies that true indicates the filter should continue, while false indicates it should
 * stop, so invert the condition. This callback can also be used to track progress using the given
 * n argument, but we currently don't make use of it. See OIDNProgressMonitorFunction in the API
 * for more information. */
static bool oidn_progress_monitor_function(void *user_ptr, double /*n*/)
{
  const Context *context = static_cast<const Context *>(user_ptr);
  return !context->is_canceled();
}

static const char *get_pass_name(const DenoisedAuxiliaryPassType type)
{
  switch (type) {
    case DenoisedAuxiliaryPassType::Albedo:
      return "albedo";
    case DenoisedAuxiliaryPassType::Normal:
      return "normal";
  }

  BLI_assert_unreachable();
  return "";
}

DenoisedAuxiliaryPass::DenoisedAuxiliaryPass(Context &context,
                                             const Result &pass,
                                             const DenoisedAuxiliaryPassType type,
                                             const oidn::Quality quality)
{
  /* Assign the pass data to the denoised buffer since we will be denoising in place. */
  if (context.use_gpu()) {
    GPU_memory_barrier(GPU_BARRIER_TEXTURE_UPDATE);
    this->denoised_buffer = static_cast<float *>(GPU_texture_read(pass, GPU_DATA_FLOAT, 0));
  }
  else {
    this->denoised_buffer = static_cast<float *>(MEM_dupallocN(pass.cpu_data().data()));
  }

  const int width = pass.domain().size.x;
  const int height = pass.domain().size.y;
  const int pixel_stride = sizeof(float) * 4;

  oidn::DeviceRef device = oidn::newDevice(oidn::DeviceType::CPU);
  device.commit();

  /* Denoise the pass in place, so set it to both the input and output. */
  oidn::FilterRef filter = device.newFilter("RT");
  filter.setImage(get_pass_name(type),
                  this->denoised_buffer,
                  oidn::Format::Float3,
                  width,
                  height,
                  0,
                  pixel_stride);
  filter.setImage(
      "output", this->denoised_buffer, oidn::Format::Float3, width, height, 0, pixel_stride);
  filter.set("quality", quality);
  filter.setProgressMonitorFunction(oidn_progress_monitor_function, &context);
  filter.commit();
  filter.execute();
}

DenoisedAuxiliaryPass::~DenoisedAuxiliaryPass()
{
  MEM_freeN(this->denoised_buffer);
}

/* --------------------------------------------------------------------
 * Denoised Auxiliary Pass Container.
 */

DenoisedAuxiliaryPass &DenoisedAuxiliaryPassContainer::get(Context &context,
                                                           const Result &pass,
                                                           const DenoisedAuxiliaryPassType type,
                                                           const oidn::Quality quality)
{
  const DenoisedAuxiliaryPassKey key(type, quality);

  return *map_.lookup_or_add_cb(key, [&]() {
    return std::make_unique<DenoisedAuxiliaryPass>(context, pass, type, quality);
  });
}

}  // namespace blender::compositor

#endif
