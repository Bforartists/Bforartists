/* SPDX-FileCopyrightText: 2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 */

#include "vk_batch.hh"

#include "vk_context.hh"
#include "vk_index_buffer.hh"
#include "vk_state_manager.hh"
#include "vk_storage_buffer.hh"
#include "vk_vertex_attribute_object.hh"
#include "vk_vertex_buffer.hh"

namespace blender::gpu {

void VKBatch::draw_setup()
{
  /* Currently the pipeline is rebuild on each draw command. Clearing the dirty flag for
   * consistency with the internals of GPU module. */
  flag &= ~GPU_BATCH_DIRTY;

  /* Finalize graphics pipeline */
  VKContext &context = *VKContext::get();
  VKStateManager &state_manager = context.state_manager_get();
  state_manager.apply_state();
  state_manager.apply_bindings();
  VKVertexAttributeObject vao;
  vao.update_bindings(context, *this);
  context.bind_graphics_pipeline(prim_type, vao);

  /* Bind geometry resources. */
  vao.bind(context);
  VKIndexBuffer *index_buffer = index_buffer_get();
  const bool draw_indexed = index_buffer != nullptr;
  if (draw_indexed) {
    index_buffer->upload_data();
    index_buffer->bind(context);
  }
}

void VKBatch::draw(int vertex_first, int vertex_count, int instance_first, int instance_count)
{
  draw_setup();

  VKContext &context = *VKContext::get();
  VKCommandBuffers &command_buffers = context.command_buffers_get();
  VKIndexBuffer *index_buffer = index_buffer_get();
  const bool draw_indexed = index_buffer != nullptr;
  if (draw_indexed) {
    command_buffers.draw_indexed(index_buffer->index_len_get(),
                                 instance_count,
                                 index_buffer->index_start_get(),
                                 vertex_first,
                                 instance_first);
  }
  else {
    command_buffers.draw(vertex_first, vertex_count, instance_first, instance_count);
  }

  command_buffers.submit();
}

void VKBatch::draw_indirect(GPUStorageBuf *indirect_buf, intptr_t offset)
{
  multi_draw_indirect(indirect_buf, 1, offset, 0);
}

void VKBatch::multi_draw_indirect(GPUStorageBuf *indirect_buf,
                                  int count,
                                  intptr_t offset,
                                  intptr_t stride)
{
  draw_setup();

  VKStorageBuffer &indirect_buffer = *unwrap(unwrap(indirect_buf));
  VKContext &context = *VKContext::get();
  const bool draw_indexed = index_buffer_get() != nullptr;
  VKCommandBuffers &command_buffers = context.command_buffers_get();
  if (draw_indexed) {
    command_buffers.draw_indexed_indirect(indirect_buffer, offset, count, stride);
  }
  else {
    command_buffers.draw_indirect(indirect_buffer, offset, count, stride);
  }

  command_buffers.submit();
}

VKVertexBuffer *VKBatch::vertex_buffer_get(int index)
{
  return unwrap(verts_(index));
}

VKVertexBuffer *VKBatch::instance_buffer_get(int index)
{
  return unwrap(inst_(index));
}

VKIndexBuffer *VKBatch::index_buffer_get()
{
  return unwrap(unwrap(elem));
}

}  // namespace blender::gpu
