/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2022 Blender Foundation */

/** \file
 * \ingroup gpu
 */

#include "vk_index_buffer.hh"
#include "vk_shader.hh"
#include "vk_shader_interface.hh"

namespace blender::gpu {

void VKIndexBuffer::ensure_updated()
{
  if (is_subrange_) {
    src_->upload_data();
    return;
  }

  VKContext &context = *VKContext::get();
  if (!buffer_.is_allocated()) {
    allocate(context);
  }

  if (data_ != nullptr) {
    buffer_.update(data_);
    MEM_SAFE_FREE(data_);
  }
}

void VKIndexBuffer::upload_data()
{
  ensure_updated();
}

void VKIndexBuffer::bind(VKContext &context)
{
  context.command_buffer_get().bind(*this, to_vk_index_type(index_type_));
}

void VKIndexBuffer::bind_as_ssbo(uint binding)
{
  ensure_updated();

  VKContext &context = *VKContext::get();
  VKShader *shader = static_cast<VKShader *>(context.shader);
  const VKShaderInterface &shader_interface = shader->interface_get();
  const VKDescriptorSet::Location location = shader_interface.descriptor_set_location(
      shader::ShaderCreateInfo::Resource::BindType::STORAGE_BUFFER, binding);
  shader->pipeline_get().descriptor_set_get().bind_as_ssbo(*this, location);
}

void VKIndexBuffer::read(uint32_t *data) const
{
  VKContext &context = *VKContext::get();
  VKCommandBuffer &command_buffer = context.command_buffer_get();
  command_buffer.submit();

  buffer_.read(data);
}

void VKIndexBuffer::update_sub(uint /*start*/, uint /*len*/, const void * /*data*/) {}

void VKIndexBuffer::strip_restart_indices() {}

void VKIndexBuffer::allocate(VKContext &context)
{
  GPUUsageType usage = data_ == nullptr ? GPU_USAGE_DEVICE_ONLY : GPU_USAGE_STATIC;
  buffer_.create(context,
                 size_get(),
                 usage,
                 static_cast<VkBufferUsageFlagBits>(VK_BUFFER_USAGE_STORAGE_BUFFER_BIT |
                                                    VK_BUFFER_USAGE_INDEX_BUFFER_BIT));
  debug::object_label(&context, buffer_.vk_handle(), "IndexBuffer");
}

}  // namespace blender::gpu
