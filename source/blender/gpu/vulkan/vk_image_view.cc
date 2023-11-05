/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 */

#include "vk_image_view.hh"
#include "vk_backend.hh"
#include "vk_debug.hh"
#include "vk_device.hh"
#include "vk_memory.hh"
#include "vk_texture.hh"

namespace blender::gpu {

static VkFormat to_non_srgb_format(const VkFormat format)
{
  switch (format) {
    case VK_FORMAT_R8G8B8_SRGB:
      return VK_FORMAT_R8G8B8_UNORM;
    case VK_FORMAT_R8G8B8A8_SRGB:
      return VK_FORMAT_R8G8B8A8_UNORM;

    default:
      break;
  }
  return format;
}

VKImageView::VKImageView(VKTexture &texture,
                         eImageViewUsage usage,
                         IndexRange layer_range,
                         IndexRange mip_range,
                         bool use_stencil,
                         bool use_srgb,
                         StringRefNull name)
{
  const VkImageAspectFlags allowed_bits = VK_IMAGE_ASPECT_COLOR_BIT |
                                          (use_stencil ? VK_IMAGE_ASPECT_STENCIL_BIT :
                                                         VK_IMAGE_ASPECT_DEPTH_BIT);
  VkImageAspectFlags image_aspect = to_vk_image_aspect_flag_bits(texture.format_get()) &
                                    allowed_bits;

  vk_format_ = to_vk_format(texture.format_get());
  if (texture.format_flag_get() & GPU_FORMAT_SRGB && !use_srgb) {
    vk_format_ = to_non_srgb_format(vk_format_);
  }

  VK_ALLOCATION_CALLBACKS
  VkImageViewCreateInfo image_view_info = {};
  image_view_info.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
  image_view_info.image = texture.vk_image_handle();
  image_view_info.viewType = to_vk_image_view_type(texture.type_get(), usage);
  image_view_info.format = vk_format_;
  image_view_info.components = texture.vk_component_mapping_get();
  image_view_info.subresourceRange.aspectMask = image_aspect;
  image_view_info.subresourceRange.baseMipLevel = mip_range.first();
  image_view_info.subresourceRange.levelCount = mip_range.size();
  image_view_info.subresourceRange.baseArrayLayer = layer_range.first();
  image_view_info.subresourceRange.layerCount = layer_range.size();

  const VKDevice &device = VKBackend::get().device_get();
  vkCreateImageView(
      device.device_get(), &image_view_info, vk_allocation_callbacks, &vk_image_view_);
  debug::object_label(vk_image_view_, name.c_str());
}

VKImageView::VKImageView(VKImageView &&other)
{
  vk_image_view_ = other.vk_image_view_;
  other.vk_image_view_ = VK_NULL_HANDLE;
  vk_format_ = other.vk_format_;
  other.vk_format_ = VK_FORMAT_UNDEFINED;
}

VKImageView::~VKImageView()
{
  if (vk_image_view_ != VK_NULL_HANDLE) {
    VKDevice &device = VKBackend::get().device_get();
    device.discard_image_view(vk_image_view_);
    vk_image_view_ = VK_NULL_HANDLE;
  }
  vk_format_ = VK_FORMAT_UNDEFINED;
}

}  // namespace blender::gpu
