/* SPDX-FileCopyrightText: 2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 */

#include "vk_index_buffer.hh"
#include "vk_shader.hh"
#include "vk_shader_interface.hh"
#include "vk_state_manager.hh"

namespace blender::gpu {

void VKIndexBuffer::ensure_updated()
{
  if (is_subrange_) {
    src_->upload_data();
    return;
  }

  if (!buffer_.is_allocated()) {
    allocate();
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
  context.command_buffers_get().bind(buffer_with_offset(), to_vk_index_type(index_type_));
}

void VKIndexBuffer::bind_as_ssbo(uint binding)
{
  VKContext::get()->state_manager_get().storage_buffer_bind(*this, binding);
}

void VKIndexBuffer::bind(int binding, shader::ShaderCreateInfo::Resource::BindType bind_type)
{
  BLI_assert(bind_type == shader::ShaderCreateInfo::Resource::BindType::STORAGE_BUFFER);
  ensure_updated();

  VKContext &context = *VKContext::get();
  VKShader *shader = static_cast<VKShader *>(context.shader);
  const VKShaderInterface &shader_interface = shader->interface_get();
  const std::optional<VKDescriptorSet::Location> location =
      shader_interface.descriptor_set_location(bind_type, binding);
  if (location) {
    shader->pipeline_get().descriptor_set_get().bind_as_ssbo(*this, *location);
  }
}

void VKIndexBuffer::read(uint32_t *data) const
{
  VKContext &context = *VKContext::get();
  context.flush();

  buffer_.read(data);
}

void VKIndexBuffer::update_sub(uint /*start*/, uint /*len*/, const void * /*data*/)
{
  NOT_YET_IMPLEMENTED
}

void VKIndexBuffer::strip_restart_indices()
{
  NOT_YET_IMPLEMENTED
}

void VKIndexBuffer::allocate()
{
  GPUUsageType usage = data_ == nullptr ? GPU_USAGE_DEVICE_ONLY : GPU_USAGE_STATIC;
  buffer_.create(
      size_get(), usage, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_INDEX_BUFFER_BIT);
  debug::object_label(buffer_.vk_handle(), "IndexBuffer");
}

VKBufferWithOffset VKIndexBuffer::buffer_with_offset()
{
  VKIndexBuffer *src = unwrap(src_);
  VKBufferWithOffset result{is_subrange_ ? src->buffer_ : buffer_, index_start_};

  BLI_assert_msg(is_subrange_ || result.offset == 0,
                 "According to design index_start should always be zero when index buffer isn't "
                 "a subrange");

  return result;
}

}  // namespace blender::gpu
