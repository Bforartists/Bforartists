/* SPDX-FileCopyrightText: 2011-2022 Blender Foundation
 *
 * SPDX-License-Identifier: Apache-2.0 */

#ifdef WITH_HIP

#  include "device/graphics_interop.h"
#  include "session/display_driver.h"

#  ifdef WITH_HIP_DYNLOAD
#    include "hipew.h"
#  endif

CCL_NAMESPACE_BEGIN

class HIPDevice;
class HIPDeviceQueue;

class HIPDeviceGraphicsInterop : public DeviceGraphicsInterop {
 public:
  explicit HIPDeviceGraphicsInterop(HIPDeviceQueue *queue);

  HIPDeviceGraphicsInterop(const HIPDeviceGraphicsInterop &other) = delete;
  HIPDeviceGraphicsInterop(HIPDeviceGraphicsInterop &&other) noexcept = delete;

  ~HIPDeviceGraphicsInterop() override;

  HIPDeviceGraphicsInterop &operator=(const HIPDeviceGraphicsInterop &other) = delete;
  HIPDeviceGraphicsInterop &operator=(HIPDeviceGraphicsInterop &&other) = delete;

  void set_buffer(const GraphicsInteropBuffer &interop_buffer) override;

  device_ptr map() override;
  void unmap() override;

 protected:
  HIPDeviceQueue *queue_ = nullptr;
  HIPDevice *device_ = nullptr;

  /* Native handle. */
  GraphicsInteropDevice::Type native_type_ = GraphicsInteropDevice::NONE;
  int64_t native_handle_ = 0;
  size_t native_size_ = 0;

  /* Buffer area in pixels of the corresponding PBO. */
  int64_t buffer_area_ = 0;

  /* The destination was requested to be cleared. */
  bool need_clear_ = false;

  hipGraphicsResource hip_graphics_resource_ = nullptr;
  hipDeviceptr_t hip_external_memory_ptr_ = 0;

  void free();
};

CCL_NAMESPACE_END

#endif
