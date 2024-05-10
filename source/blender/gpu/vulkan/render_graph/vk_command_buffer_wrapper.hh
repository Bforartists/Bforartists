/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 */

#pragma once

#include "vk_common.hh"

namespace blender::gpu::render_graph {
class VKCommandBufferInterface {
 public:
  VKCommandBufferInterface() {}
  virtual ~VKCommandBufferInterface() = default;

  virtual void begin_recording() = 0;
  virtual void end_recording() = 0;
  virtual void submit_with_cpu_synchronization() = 0;
  virtual void wait_for_cpu_synchronization() = 0;

  virtual void bind_pipeline(VkPipelineBindPoint pipeline_bind_point, VkPipeline pipeline) = 0;
  virtual void bind_descriptor_sets(VkPipelineBindPoint pipeline_bind_point,
                                    VkPipelineLayout layout,
                                    uint32_t first_set,
                                    uint32_t descriptor_set_count,
                                    const VkDescriptorSet *p_descriptor_sets,
                                    uint32_t dynamic_offset_count,
                                    const uint32_t *p_dynamic_offsets) = 0;
  virtual void bind_index_buffer(VkBuffer buffer, VkDeviceSize offset, VkIndexType index_type) = 0;
  virtual void bind_vertex_buffers(uint32_t first_binding,
                                   uint32_t binding_count,
                                   const VkBuffer *p_buffers,
                                   const VkDeviceSize *p_offsets) = 0;
  virtual void draw(uint32_t vertex_count,
                    uint32_t instance_count,
                    uint32_t first_vertex,
                    uint32_t first_instance) = 0;
  virtual void draw_indexed(uint32_t index_count,
                            uint32_t instance_count,
                            uint32_t first_index,
                            int32_t vertex_offset,
                            uint32_t first_instance) = 0;
  virtual void draw_indirect(VkBuffer buffer,
                             VkDeviceSize offset,
                             uint32_t draw_count,
                             uint32_t stride) = 0;
  virtual void draw_indexed_indirect(VkBuffer buffer,
                                     VkDeviceSize offset,
                                     uint32_t draw_count,
                                     uint32_t stride) = 0;
  virtual void dispatch(uint32_t group_count_x,
                        uint32_t group_count_y,
                        uint32_t group_count_z) = 0;
  virtual void dispatch_indirect(VkBuffer buffer, VkDeviceSize offset) = 0;
  virtual void copy_buffer(VkBuffer src_buffer,
                           VkBuffer dst_buffer,
                           uint32_t region_count,
                           const VkBufferCopy *p_regions) = 0;
  virtual void copy_image(VkImage src_image,
                          VkImageLayout src_image_layout,
                          VkImage dst_image,
                          VkImageLayout dst_image_layout,
                          uint32_t region_count,
                          const VkImageCopy *p_regions) = 0;
  virtual void blit_image(VkImage src_image,
                          VkImageLayout src_image_layout,
                          VkImage dst_image,
                          VkImageLayout dst_image_layout,
                          uint32_t region_count,
                          const VkImageBlit *p_regions,
                          VkFilter filter) = 0;
  virtual void copy_buffer_to_image(VkBuffer src_buffer,
                                    VkImage dst_image,
                                    VkImageLayout dst_image_layout,
                                    uint32_t region_count,
                                    const VkBufferImageCopy *p_regions) = 0;
  virtual void copy_image_to_buffer(VkImage src_image,
                                    VkImageLayout src_image_layout,
                                    VkBuffer dst_buffer,
                                    uint32_t region_count,
                                    const VkBufferImageCopy *p_regions) = 0;
  virtual void fill_buffer(VkBuffer dst_buffer,
                           VkDeviceSize dst_offset,
                           VkDeviceSize size,
                           uint32_t data) = 0;
  virtual void clear_color_image(VkImage image,
                                 VkImageLayout image_layout,
                                 const VkClearColorValue *p_color,
                                 uint32_t range_count,
                                 const VkImageSubresourceRange *p_ranges) = 0;
  virtual void clear_depth_stencil_image(VkImage image,
                                         VkImageLayout image_layout,
                                         const VkClearDepthStencilValue *p_depth_stencil,
                                         uint32_t range_count,
                                         const VkImageSubresourceRange *p_ranges) = 0;
  virtual void clear_attachments(uint32_t attachment_count,
                                 const VkClearAttachment *p_attachments,
                                 uint32_t rect_count,
                                 const VkClearRect *p_rects) = 0;
  virtual void pipeline_barrier(VkPipelineStageFlags src_stage_mask,
                                VkPipelineStageFlags dst_stage_mask,
                                VkDependencyFlags dependency_flags,
                                uint32_t memory_barrier_count,
                                const VkMemoryBarrier *p_memory_barriers,
                                uint32_t buffer_memory_barrier_count,
                                const VkBufferMemoryBarrier *p_buffer_memory_barriers,
                                uint32_t image_memory_barrier_count,
                                const VkImageMemoryBarrier *p_image_memory_barriers) = 0;
  virtual void push_constants(VkPipelineLayout layout,
                              VkShaderStageFlags stage_flags,
                              uint32_t offset,
                              uint32_t size,
                              const void *p_values) = 0;
  virtual void begin_rendering(const VkRenderingInfo *p_rendering_info) = 0;
  virtual void end_rendering() = 0;
};

class VKCommandBufferWrapper : public VKCommandBufferInterface {
 private:
  VkCommandPoolCreateInfo vk_command_pool_create_info_;
  VkCommandBufferAllocateInfo vk_command_buffer_allocate_info_;
  VkCommandBufferBeginInfo vk_command_buffer_begin_info_;
  VkFenceCreateInfo vk_fence_create_info_;
  VkSubmitInfo vk_submit_info_;

  VkCommandPool vk_command_pool_ = VK_NULL_HANDLE;
  VkCommandBuffer vk_command_buffer_ = VK_NULL_HANDLE;
  VkFence vk_fence_ = VK_NULL_HANDLE;

 public:
  VKCommandBufferWrapper();
  virtual ~VKCommandBufferWrapper();

  void begin_recording() override;
  void end_recording() override;
  void submit_with_cpu_synchronization() override;
  void wait_for_cpu_synchronization() override;

  void bind_pipeline(VkPipelineBindPoint pipeline_bind_point, VkPipeline pipeline) override;
  void bind_descriptor_sets(VkPipelineBindPoint pipeline_bind_point,
                            VkPipelineLayout layout,
                            uint32_t first_set,
                            uint32_t descriptor_set_count,
                            const VkDescriptorSet *p_descriptor_sets,
                            uint32_t dynamic_offset_count,
                            const uint32_t *p_dynamic_offsets) override;
  void bind_index_buffer(VkBuffer buffer, VkDeviceSize offset, VkIndexType index_type) override;
  void bind_vertex_buffers(uint32_t first_binding,
                           uint32_t binding_count,
                           const VkBuffer *p_buffers,
                           const VkDeviceSize *p_offsets) override;
  void draw(uint32_t vertex_count,
            uint32_t instance_count,
            uint32_t first_vertex,
            uint32_t first_instance) override;
  void draw_indexed(uint32_t index_count,
                    uint32_t instance_count,
                    uint32_t first_index,
                    int32_t vertex_offset,
                    uint32_t first_instance) override;
  void draw_indirect(VkBuffer buffer,
                     VkDeviceSize offset,
                     uint32_t draw_count,
                     uint32_t stride) override;
  void draw_indexed_indirect(VkBuffer buffer,
                             VkDeviceSize offset,
                             uint32_t draw_count,
                             uint32_t stride) override;
  void dispatch(uint32_t group_count_x, uint32_t group_count_y, uint32_t group_count_z) override;
  void dispatch_indirect(VkBuffer buffer, VkDeviceSize offset) override;
  void copy_buffer(VkBuffer src_buffer,
                   VkBuffer dst_buffer,
                   uint32_t region_count,
                   const VkBufferCopy *p_regions) override;
  void copy_image(VkImage src_image,
                  VkImageLayout src_image_layout,
                  VkImage dst_image,
                  VkImageLayout dst_image_layout,
                  uint32_t region_count,
                  const VkImageCopy *p_regions) override;
  void blit_image(VkImage src_image,
                  VkImageLayout src_image_layout,
                  VkImage dst_image,
                  VkImageLayout dst_image_layout,
                  uint32_t region_count,
                  const VkImageBlit *p_regions,
                  VkFilter filter) override;
  void copy_buffer_to_image(VkBuffer src_buffer,
                            VkImage dst_image,
                            VkImageLayout dst_image_layout,
                            uint32_t region_count,
                            const VkBufferImageCopy *p_regions) override;
  void copy_image_to_buffer(VkImage src_image,
                            VkImageLayout src_image_layout,
                            VkBuffer dst_buffer,
                            uint32_t region_count,
                            const VkBufferImageCopy *p_regions) override;
  void fill_buffer(VkBuffer dst_buffer,
                   VkDeviceSize dst_offset,
                   VkDeviceSize size,
                   uint32_t data) override;
  void clear_color_image(VkImage image,
                         VkImageLayout image_layout,
                         const VkClearColorValue *p_color,
                         uint32_t range_count,
                         const VkImageSubresourceRange *p_ranges) override;
  void clear_depth_stencil_image(VkImage image,
                                 VkImageLayout image_layout,
                                 const VkClearDepthStencilValue *p_depth_stencil,
                                 uint32_t range_count,
                                 const VkImageSubresourceRange *p_ranges) override;
  void clear_attachments(uint32_t attachment_count,
                         const VkClearAttachment *p_attachments,
                         uint32_t rect_count,
                         const VkClearRect *p_rects) override;
  void pipeline_barrier(VkPipelineStageFlags src_stage_mask,
                        VkPipelineStageFlags dst_stage_mask,
                        VkDependencyFlags dependency_flags,
                        uint32_t memory_barrier_count,
                        const VkMemoryBarrier *p_memory_barriers,
                        uint32_t buffer_memory_barrier_count,
                        const VkBufferMemoryBarrier *p_buffer_memory_barriers,
                        uint32_t image_memory_barrier_count,
                        const VkImageMemoryBarrier *p_image_memory_barriers) override;
  void push_constants(VkPipelineLayout layout,
                      VkShaderStageFlags stage_flags,
                      uint32_t offset,
                      uint32_t size,
                      const void *p_values) override;
  void begin_rendering(const VkRenderingInfo *p_rendering_info) override;
  void end_rendering() override;
};

}  // namespace blender::gpu::render_graph
