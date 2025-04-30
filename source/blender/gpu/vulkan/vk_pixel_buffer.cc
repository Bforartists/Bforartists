/* SPDX-FileCopyrightText: 2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 */

#include "vk_pixel_buffer.hh"

#include "vk_backend.hh"

#include "CLG_log.h"

namespace blender::gpu {

static CLG_LogRef LOG = {"gpu.vulkan"};

VKPixelBuffer::VKPixelBuffer(size_t size) : PixelBuffer(size) {}

void VKPixelBuffer::create(bool memory_export)
{
  /* Create on demand with or without memory export. When memory export is
   * enabled there is no host mapping. */
  if (buffer_initialized_ && buffer_memory_export_ == memory_export) {
    return;
  }

  if (buffer_.is_allocated()) {
    buffer_.free();
  }

  buffer_.create(size_,
                 VK_BUFFER_USAGE_TRANSFER_SRC_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT,
                 VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT,
                 VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
                 VmaAllocationCreateFlags(0),
                 memory_export);
  debug::object_label(buffer_.vk_handle(), "PixelBuffer");

  buffer_initialized_ = true;
  buffer_memory_export_ = memory_export;
  native_handle_ = GPUPixelBufferNativeHandle{};
}

void *VKPixelBuffer::map()
{
  /* Vulkan buffers are always mapped between allocation and freeing. */
  create(false);
  return buffer_.mapped_memory_get();
}

void VKPixelBuffer::unmap()
{
  /* Vulkan buffers are always mapped between allocation and freeing. */
}

GPUPixelBufferNativeHandle VKPixelBuffer::get_native_handle()
{
  /* Initialize once. */
  if (buffer_initialized_) {
    return native_handle_;
  }

  VKDevice &device = VKBackend::get().device;

  /* Functionality supported? */
#ifdef _WIN32
  if (!device.functions.vkGetMemoryWin32Handle) {
    return native_handle_;
  }
#else
  if (!device.functions.vkGetMemoryFd) {
    return native_handle_;
  }
#endif

  /* Create buffer. */
  create(true);

  /* Get device memory. */
  size_t memory_size = 0;
  VkDeviceMemory memory = buffer_.export_memory_get(memory_size);
  if (memory == nullptr) {
    CLOG_ERROR(&LOG, "Failed to get device memory for Vulkan pixel buffer");
    return native_handle_;
  }

#ifdef _WIN32
  /* Opaque Windows handle. */
  VkMemoryGetWin32HandleInfoKHR info = {};
  info.sType = VK_STRUCTURE_TYPE_MEMORY_GET_WIN32_HANDLE_INFO_KHR;
  info.pNext = nullptr;
  info.memory = memory;
  info.handleType = VK_EXTERNAL_MEMORY_HANDLE_TYPE_OPAQUE_WIN32_BIT;

  HANDLE handle = 0;
  if (device.functions.vkGetMemoryWin32Handle(device.vk_handle(), &info, &handle) != VK_SUCCESS) {
    CLOG_ERROR(&LOG, "Failed to get Windows handle for Vulkan pixel buffer");
    return native_handle_;
  }

  native_handle_.handle = int64_t(handle);
  native_handle_.size = memory_size;
#else
  /* Opaque file descriptor. */
  VkMemoryGetFdInfoKHR info = {};
  info.sType = VK_STRUCTURE_TYPE_MEMORY_GET_FD_INFO_KHR;
  info.pNext = nullptr;
  info.memory = memory;
  info.handleType = VK_EXTERNAL_MEMORY_HANDLE_TYPE_OPAQUE_FD_BIT;

  int fd = -1;
  if (device.functions.vkGetMemoryFd(device.vk_handle(), &info, &fd) != VK_SUCCESS) {
    CLOG_ERROR(&LOG, "Failed to get file descriptor for Vulkan pixel buffer");
    return native_handle_;
  }

  native_handle_.handle = int64_t(fd);
  native_handle_.size = memory_size;
#endif

  return native_handle_;
}

size_t VKPixelBuffer::get_size()
{
  return size_;
}

}  // namespace blender::gpu
