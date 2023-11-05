/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 */

#include "vk_device.hh"
#include "vk_backend.hh"
#include "vk_context.hh"
#include "vk_memory.hh"
#include "vk_state_manager.hh"
#include "vk_storage_buffer.hh"
#include "vk_texture.hh"
#include "vk_vertex_buffer.hh"

#include "BLI_math_matrix_types.hh"

#include "GHOST_C-api.h"

namespace blender::gpu {

void VKDevice::deinit()
{
  VK_ALLOCATION_CALLBACKS;
  vkDestroyCommandPool(vk_device_, vk_command_pool_, vk_allocation_callbacks);

  dummy_buffer_.free();
  if (dummy_color_attachment_.has_value()) {
    delete &(*dummy_color_attachment_).get();
    dummy_color_attachment_.reset();
  }
  sampler_.free();
  destroy_discarded_resources();
  vmaDestroyAllocator(mem_allocator_);
  mem_allocator_ = VK_NULL_HANDLE;
  debugging_tools_.deinit(vk_instance_);

  vk_instance_ = VK_NULL_HANDLE;
  vk_physical_device_ = VK_NULL_HANDLE;
  vk_device_ = VK_NULL_HANDLE;
  vk_queue_family_ = 0;
  vk_queue_ = VK_NULL_HANDLE;
  vk_physical_device_properties_ = {};
}

bool VKDevice::is_initialized() const
{
  return vk_device_ != VK_NULL_HANDLE;
}

void VKDevice::init(void *ghost_context)
{
  BLI_assert(!is_initialized());
  GHOST_GetVulkanHandles((GHOST_ContextHandle)ghost_context,
                         &vk_instance_,
                         &vk_physical_device_,
                         &vk_device_,
                         &vk_queue_family_,
                         &vk_queue_);

  init_physical_device_properties();
  init_physical_device_features();
  VKBackend::platform_init(*this);
  VKBackend::capabilities_init(*this);
  init_debug_callbacks();
  init_memory_allocator();
  init_command_pools();
  init_descriptor_pools();

  sampler_.create();

  debug::object_label(device_get(), "LogicalDevice");
  debug::object_label(queue_get(), "GenericQueue");
}

void VKDevice::init_debug_callbacks()
{
  debugging_tools_.init(vk_instance_);
}

void VKDevice::init_physical_device_properties()
{
  BLI_assert(vk_physical_device_ != VK_NULL_HANDLE);
  vkGetPhysicalDeviceProperties(vk_physical_device_, &vk_physical_device_properties_);
}

void VKDevice::init_physical_device_features()
{
  BLI_assert(vk_physical_device_ != VK_NULL_HANDLE);

  VkPhysicalDeviceFeatures2 features = {};
  features.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2;
  vk_physical_device_vulkan_11_features_.sType =
      VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_1_FEATURES;
  vk_physical_device_vulkan_12_features_.sType =
      VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_2_FEATURES;

  features.pNext = &vk_physical_device_vulkan_11_features_;
  vk_physical_device_vulkan_11_features_.pNext = &vk_physical_device_vulkan_12_features_;

  vkGetPhysicalDeviceFeatures2(vk_physical_device_, &features);
  vk_physical_device_features_ = features.features;
}

void VKDevice::init_memory_allocator()
{
  VK_ALLOCATION_CALLBACKS;
  VmaAllocatorCreateInfo info = {};
  info.vulkanApiVersion = VK_API_VERSION_1_2;
  info.physicalDevice = vk_physical_device_;
  info.device = vk_device_;
  info.instance = vk_instance_;
  info.pAllocationCallbacks = vk_allocation_callbacks;
  vmaCreateAllocator(&info, &mem_allocator_);
}

void VKDevice::init_command_pools()
{
  VK_ALLOCATION_CALLBACKS;
  VkCommandPoolCreateInfo command_pool_info = {};
  command_pool_info.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
  command_pool_info.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
  command_pool_info.queueFamilyIndex = vk_queue_family_;

  vkCreateCommandPool(vk_device_, &command_pool_info, vk_allocation_callbacks, &vk_command_pool_);
}

void VKDevice::init_descriptor_pools()
{
  descriptor_pools_.init(vk_device_);
}

void VKDevice::init_dummy_buffer(VKContext &context)
{
  if (dummy_buffer_.is_allocated()) {
    return;
  }

  dummy_buffer_.create(sizeof(float4x4),
                       GPU_USAGE_DEVICE_ONLY,
                       VK_BUFFER_USAGE_VERTEX_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT);
  dummy_buffer_.clear(context, 0);
}

void VKDevice::init_dummy_color_attachment()
{
  if (dummy_color_attachment_.has_value()) {
    return;
  }

  GPUTexture *texture = GPU_texture_create_2d(
      "dummy_attachment", 1, 1, 1, GPU_R32F, GPU_TEXTURE_USAGE_ATTACHMENT, nullptr);
  BLI_assert(texture);
  VKTexture &vk_texture = *unwrap(unwrap(texture));
  dummy_color_attachment_ = std::make_optional(std::reference_wrapper(vk_texture));
}

/* -------------------------------------------------------------------- */
/** \name Platform/driver/device information
 * \{ */

constexpr int32_t PCI_ID_NVIDIA = 0x10de;
constexpr int32_t PCI_ID_INTEL = 0x8086;
constexpr int32_t PCI_ID_AMD = 0x1002;
constexpr int32_t PCI_ID_ATI = 0x1022;

eGPUDeviceType VKDevice::device_type() const
{
  /* According to the vulkan specifications:
   *
   * If the vendor has a PCI vendor ID, the low 16 bits of vendorID must contain that PCI vendor
   * ID, and the remaining bits must be set to zero. Otherwise, the value returned must be a valid
   * Khronos vendor ID.
   */
  switch (vk_physical_device_properties_.vendorID) {
    case PCI_ID_NVIDIA:
      return GPU_DEVICE_NVIDIA;
    case PCI_ID_INTEL:
      return GPU_DEVICE_INTEL;
    case PCI_ID_AMD:
    case PCI_ID_ATI:
      return GPU_DEVICE_ATI;
    default:
      break;
  }

  return GPU_DEVICE_UNKNOWN;
}

eGPUDriverType VKDevice::driver_type() const
{
  /* It is unclear how to determine the driver type, but it is required to extract the correct
   * driver version. */
  return GPU_DRIVER_ANY;
}

std::string VKDevice::vendor_name() const
{
  /* Below 0x10000 are the PCI vendor IDs (https://pcisig.com/membership/member-companies) */
  if (vk_physical_device_properties_.vendorID < 0x10000) {
    switch (vk_physical_device_properties_.vendorID) {
      case 0x1022:
        return "Advanced Micro Devices";
      case 0x10DE:
        return "NVIDIA Corporation";
      case 0x8086:
        return "Intel Corporation";
      default:
        return std::to_string(vk_physical_device_properties_.vendorID);
    }
  }
  else {
    /* above 0x10000 should be vkVendorIDs
     * NOTE: When debug_messaging landed we can use something similar to
     * vk::to_string(vk::VendorId(properties.vendorID));
     */
    return std::to_string(vk_physical_device_properties_.vendorID);
  }
}

std::string VKDevice::driver_version() const
{
  /*
   * NOTE: this depends on the driver type and is currently incorrect. Idea is to use a default per
   * OS.
   */
  const uint32_t driver_version = vk_physical_device_properties_.driverVersion;
  switch (vk_physical_device_properties_.vendorID) {
    case PCI_ID_NVIDIA:
      return std::to_string((driver_version >> 22) & 0x3FF) + "." +
             std::to_string((driver_version >> 14) & 0xFF) + "." +
             std::to_string((driver_version >> 6) & 0xFF) + "." +
             std::to_string(driver_version & 0x3F);
    case PCI_ID_INTEL: {
      const uint32_t major = VK_VERSION_MAJOR(driver_version);
      /* When using Mesa driver we should use VK_VERSION_*. */
      if (major > 30) {
        return std::to_string((driver_version >> 14) & 0x3FFFF) + "." +
               std::to_string((driver_version & 0x3FFF));
      }
      break;
    }
    default:
      break;
  }

  return std::to_string(VK_VERSION_MAJOR(driver_version)) + "." +
         std::to_string(VK_VERSION_MINOR(driver_version)) + "." +
         std::to_string(VK_VERSION_PATCH(driver_version));
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Resource management
 * \{ */

void VKDevice::context_register(VKContext &context)
{
  contexts_.append(std::reference_wrapper(context));
}

void VKDevice::context_unregister(VKContext &context)
{
  contexts_.remove(contexts_.first_index_of(std::reference_wrapper(context)));
}
const Vector<std::reference_wrapper<VKContext>> &VKDevice::contexts_get() const
{
  return contexts_;
};

void VKDevice::discard_image(VkImage vk_image, VmaAllocation vma_allocation)
{
  discarded_images_.append(std::pair(vk_image, vma_allocation));
}

void VKDevice::discard_image_view(VkImageView vk_image_view)
{
  discarded_image_views_.append(vk_image_view);
}

void VKDevice::discard_buffer(VkBuffer vk_buffer, VmaAllocation vma_allocation)
{
  discarded_buffers_.append(std::pair(vk_buffer, vma_allocation));
}

void VKDevice::discard_render_pass(VkRenderPass vk_render_pass)
{
  discarded_render_passes_.append(vk_render_pass);
}
void VKDevice::discard_frame_buffer(VkFramebuffer vk_frame_buffer)
{
  discarded_frame_buffers_.append(vk_frame_buffer);
}

void VKDevice::destroy_discarded_resources()
{
  VK_ALLOCATION_CALLBACKS

  while (!discarded_image_views_.is_empty()) {
    VkImageView vk_image_view = discarded_image_views_.pop_last();
    vkDestroyImageView(vk_device_, vk_image_view, vk_allocation_callbacks);
  }

  while (!discarded_images_.is_empty()) {
    std::pair<VkImage, VmaAllocation> image_allocation = discarded_images_.pop_last();
    vmaDestroyImage(mem_allocator_get(), image_allocation.first, image_allocation.second);
  }

  while (!discarded_buffers_.is_empty()) {
    std::pair<VkBuffer, VmaAllocation> buffer_allocation = discarded_buffers_.pop_last();
    vmaDestroyBuffer(mem_allocator_get(), buffer_allocation.first, buffer_allocation.second);
  }

  while (!discarded_render_passes_.is_empty()) {
    VkRenderPass vk_render_pass = discarded_render_passes_.pop_last();
    vkDestroyRenderPass(vk_device_, vk_render_pass, vk_allocation_callbacks);
  }

  while (!discarded_frame_buffers_.is_empty()) {
    VkFramebuffer vk_frame_buffer = discarded_frame_buffers_.pop_last();
    vkDestroyFramebuffer(vk_device_, vk_frame_buffer, vk_allocation_callbacks);
  }
}

/** \} */

}  // namespace blender::gpu
