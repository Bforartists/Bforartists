/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2022 Blender Foundation. All rights reserved. */

/** \file
 * \ingroup gpu
 */
#include "vk_shader.hh"
#include "vk_shader_interface.hh"
#include "vk_vertex_buffer.hh"

#include "vk_storage_buffer.hh"

namespace blender::gpu {

void VKStorageBuffer::update(const void *data)
{
  if (!buffer_.is_allocated()) {
    VKContext &context = *VKContext::get();
    allocate(context);
  }
  buffer_.update(data);
}

void VKStorageBuffer::allocate(VKContext &context)
{
  buffer_.create(context,
                 size_in_bytes_,
                 usage_,
                 static_cast<VkBufferUsageFlagBits>(VK_BUFFER_USAGE_STORAGE_BUFFER_BIT |
                                                    VK_BUFFER_USAGE_TRANSFER_DST_BIT));
}

void VKStorageBuffer::bind(int slot)
{
  VKContext &context = *VKContext::get();
  if (!buffer_.is_allocated()) {
    allocate(context);
  }
  VKShader *shader = static_cast<VKShader *>(context.shader);
  const VKShaderInterface &shader_interface = shader->interface_get();
  const VKDescriptorSet::Location location = shader_interface.descriptor_set_location(
      shader::ShaderCreateInfo::Resource::BindType::STORAGE_BUFFER, slot);
  shader->pipeline_get().descriptor_set_get().bind(*this, location);
}

void VKStorageBuffer::unbind()
{
}

void VKStorageBuffer::clear(uint32_t clear_value)
{
  VKContext &context = *VKContext::get();
  if (!buffer_.is_allocated()) {
    allocate(context);
  }
  buffer_.clear(context, clear_value);
}

void VKStorageBuffer::copy_sub(VertBuf * /*src*/,
                               uint /*dst_offset*/,
                               uint /*src_offset*/,
                               uint /*copy_size*/)
{
}

void VKStorageBuffer::read(void *data)
{
  VKContext &context = *VKContext::get();
  if (!buffer_.is_allocated()) {
    allocate(context);
  }

  VKCommandBuffer &command_buffer = context.command_buffer_get();
  command_buffer.submit();

  buffer_.read(data);
}

}  // namespace blender::gpu
