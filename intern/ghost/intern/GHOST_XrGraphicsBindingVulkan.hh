/* SPDX-FileCopyrightText: 2025 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup GHOST
 */

#include <list>

#define VMA_VULKAN_VERSION 1002000  // Vulkan 1.2
#include "vk_mem_alloc.h"

#include "GHOST_ContextVK.hh"
#include "GHOST_IXrGraphicsBinding.hh"
#include "GHOST_Types.h"

class GHOST_XrGraphicsBindingVulkan : public GHOST_IXrGraphicsBinding {
 public:
  ~GHOST_XrGraphicsBindingVulkan() override;

  /**
   * Check the version requirements to use OpenXR with the Vulkan backend.
   */
  bool checkVersionRequirements(GHOST_Context &ghost_ctx,
                                XrInstance instance,
                                XrSystemId system_id,
                                std::string *r_requirement_info) const override;

  void initFromGhostContext(GHOST_Context &ghost_ctx,
                            XrInstance instance,
                            XrSystemId system_id) override;
  std::optional<int64_t> chooseSwapchainFormat(const std::vector<int64_t> &runtime_formats,
                                               GHOST_TXrSwapchainFormat &r_format,
                                               bool &r_is_srgb_format) const override;
  std::vector<XrSwapchainImageBaseHeader *> createSwapchainImages(uint32_t image_count) override;

  void submitToSwapchainImage(XrSwapchainImageBaseHeader &swapchain_image,
                              const GHOST_XrDrawViewInfo &draw_info) override;

  bool needsUpsideDownDrawing(GHOST_Context &ghost_ctx) const override;

 private:
  GHOST_ContextVK *m_ghost_ctx = nullptr;

  VkInstance m_vk_instance = VK_NULL_HANDLE;
  VkPhysicalDevice m_vk_physical_device = VK_NULL_HANDLE;
  uint32_t m_graphics_queue_family = 0;
  VkQueue m_vk_queue = VK_NULL_HANDLE;
  VkDevice m_vk_device = VK_NULL_HANDLE;
  VmaAllocator m_vma_allocator = VK_NULL_HANDLE;
  VmaAllocation m_vk_buffer_allocation = VK_NULL_HANDLE;
  VkBuffer m_vk_buffer = VK_NULL_HANDLE;
  VmaAllocationInfo m_vk_buffer_allocation_info = {};
  GHOST_TVulkanXRModes m_data_transfer_mode = GHOST_kVulkanXRModeCPU;

  std::list<std::vector<XrSwapchainImageVulkan2KHR>> m_image_cache;
  VkCommandPool m_vk_command_pool = VK_NULL_HANDLE;

  GHOST_TVulkanXRModes choseDataTransferMode();
  void submitToSwapchainImageCpu(XrSwapchainImageVulkan2KHR &swapchain_image,
                                 const GHOST_XrDrawViewInfo &draw_info);
  void submitToSwapchainImageFd(XrSwapchainImageVulkan2KHR &swapchain_image,
                                const GHOST_XrDrawViewInfo &draw_info);

  /**
   * Single VkCommandBuffer that is used for all views/swap-chains.
   *
   * This can be improved by having a single command buffer per swap-chain image.
   */
  VkCommandBuffer m_vk_command_buffer = VK_NULL_HANDLE;

  static PFN_xrGetVulkanGraphicsRequirements2KHR s_xrGetVulkanGraphicsRequirements2KHR_fn;
  static PFN_xrGetVulkanGraphicsDevice2KHR s_xrGetVulkanGraphicsDevice2KHR_fn;
  static PFN_xrCreateVulkanInstanceKHR s_xrCreateVulkanInstanceKHR_fn;
  static PFN_xrCreateVulkanDeviceKHR s_xrCreateVulkanDeviceKHR_fn;
};
