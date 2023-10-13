/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 */

#pragma once

#include "BLI_utility_mixins.hh"
#include "BLI_vector.hh"

#include "vk_buffer.hh"
#include "vk_common.hh"
#include "vk_debug.hh"
#include "vk_descriptor_pools.hh"
#include "vk_sampler.hh"

namespace blender::gpu {
class VKBackend;

struct VKWorkarounds {
  /**
   * Some devices don't support pixel formats that are aligned to 24 and 48 bits.
   * In this case we need to use a different texture format.
   *
   * If set to true we should work around this issue by using a different texture format.
   */
  bool not_aligned_pixel_formats = false;

  /**
   * Is the workaround for devices that don't support
   * #VkPhysicalDeviceVulkan12Features::shaderOutputViewportIndex enabled.
   */
  bool shader_output_viewport_index = false;

  /**
   * Is the workaround for devices that don't support
   * #VkPhysicalDeviceVulkan12Features::shaderOutputLayer enabled.
   */
  bool shader_output_layer = false;
};

class VKDevice : public NonCopyable {
 private:
  /** Copies of the handles owned by the GHOST context. */
  VkInstance vk_instance_ = VK_NULL_HANDLE;
  VkPhysicalDevice vk_physical_device_ = VK_NULL_HANDLE;
  VkDevice vk_device_ = VK_NULL_HANDLE;
  uint32_t vk_queue_family_ = 0;
  VkQueue vk_queue_ = VK_NULL_HANDLE;
  VkCommandPool vk_command_pool_ = VK_NULL_HANDLE;

  /* Dummy sampler for now. */
  VKSampler sampler_;

  /**
   * Available Contexts for this device.
   *
   * Device keeps track of each contexts. When buffers/images are freed they need to be removed
   * from all contexts state managers.
   *
   * The contexts inside this list aren't owned by the VKDevice. Caller of `GPU_context_create`
   * holds the ownership.
   */
  Vector<std::reference_wrapper<VKContext>> contexts_;

  /** Allocator used for texture and buffers and other resources. */
  VmaAllocator mem_allocator_ = VK_NULL_HANDLE;
  VKDescriptorPools descriptor_pools_;

  /** Limits of the device linked to this context. */
  VkPhysicalDeviceProperties vk_physical_device_properties_ = {};
  /** Features support. */
  VkPhysicalDeviceFeatures vk_physical_device_features_ = {};
  VkPhysicalDeviceVulkan11Features vk_physical_device_vulkan_11_features_ = {};
  VkPhysicalDeviceVulkan12Features vk_physical_device_vulkan_12_features_ = {};

  /** Functions of vk_ext_debugutils for this device/instance. */
  debug::VKDebuggingTools debugging_tools_;

  /* Workarounds */
  VKWorkarounds workarounds_;

  /** Buffer to bind to unbound resource locations. */
  VKBuffer dummy_buffer_;
  std::optional<std::reference_wrapper<VKTexture>> dummy_color_attachment_;

  Vector<std::pair<VkImage, VmaAllocation>> discarded_images_;
  Vector<std::pair<VkBuffer, VmaAllocation>> discarded_buffers_;
  Vector<VkRenderPass> discarded_render_passes_;
  Vector<VkFramebuffer> discarded_frame_buffers_;
  Vector<VkImageView> discarded_image_views_;

 public:
  VkPhysicalDevice physical_device_get() const
  {
    return vk_physical_device_;
  }

  const VkPhysicalDeviceProperties &physical_device_properties_get() const
  {
    return vk_physical_device_properties_;
  }

  const VkPhysicalDeviceFeatures &physical_device_features_get() const
  {
    return vk_physical_device_features_;
  }

  const VkPhysicalDeviceVulkan11Features &physical_device_vulkan_11_features_get() const
  {
    return vk_physical_device_vulkan_11_features_;
  }

  const VkPhysicalDeviceVulkan12Features &physical_device_vulkan_12_features_get() const
  {
    return vk_physical_device_vulkan_12_features_;
  }

  VkInstance instance_get() const
  {
    return vk_instance_;
  };

  VkDevice device_get() const
  {
    return vk_device_;
  }

  VkQueue queue_get() const
  {
    return vk_queue_;
  }

  VKDescriptorPools &descriptor_pools_get()
  {
    return descriptor_pools_;
  }

  const uint32_t *queue_family_ptr_get() const
  {
    return &vk_queue_family_;
  }

  VmaAllocator mem_allocator_get() const
  {
    return mem_allocator_;
  }

  debug::VKDebuggingTools &debugging_tools_get()
  {
    return debugging_tools_;
  }

  const debug::VKDebuggingTools &debugging_tools_get() const
  {
    return debugging_tools_;
  }

  const VKSampler &sampler_get() const
  {
    return sampler_;
  }

  const VkCommandPool vk_command_pool_get() const
  {
    return vk_command_pool_;
  }

  bool is_initialized() const;
  void init(void *ghost_context);
  /**
   * Initialize a dummy buffer that can be bound for missing attributes.
   *
   * Dummy buffer can only be initialized after the command buffer of the context is retrieved.
   */
  void init_dummy_buffer(VKContext &context);
  void init_dummy_color_attachment();
  void deinit();

  eGPUDeviceType device_type() const;
  eGPUDriverType driver_type() const;
  std::string vendor_name() const;
  std::string driver_version() const;

  const VKWorkarounds &workarounds_get() const
  {
    return workarounds_;
  }

  /* -------------------------------------------------------------------- */
  /** \name Resource management
   * \{ */

  void context_register(VKContext &context);
  void context_unregister(VKContext &context);
  const Vector<std::reference_wrapper<VKContext>> &contexts_get() const;

  const VKBuffer &dummy_buffer_get() const
  {
    return dummy_buffer_;
  }

  VKTexture &dummy_color_attachment_get() const
  {
    BLI_assert(dummy_color_attachment_.has_value());
    return (*dummy_color_attachment_).get();
  }

  void discard_image(VkImage vk_image, VmaAllocation vma_allocation);
  void discard_image_view(VkImageView vk_image_view);
  void discard_buffer(VkBuffer vk_buffer, VmaAllocation vma_allocation);
  void discard_render_pass(VkRenderPass vk_render_pass);
  void discard_frame_buffer(VkFramebuffer vk_framebuffer);
  void destroy_discarded_resources();

  /** \} */

 private:
  void init_physical_device_properties();
  void init_physical_device_features();
  void init_debug_callbacks();
  void init_memory_allocator();
  void init_command_pools();
  void init_descriptor_pools();

  /* During initialization the backend requires access to update the workarounds. */
  friend VKBackend;
};

}  // namespace blender::gpu
