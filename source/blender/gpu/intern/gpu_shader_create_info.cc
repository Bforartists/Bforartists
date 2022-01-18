/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2021 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup gpu
 *
 * Descriptor type used to define shader structure, resources and interfaces.
 */

#include "BLI_map.hh"
#include "BLI_set.hh"
#include "BLI_string_ref.hh"

#include "GPU_shader.h"
#include "GPU_texture.h"

#include "gpu_shader_create_info.hh"
#include "gpu_shader_create_info_private.hh"

#undef GPU_SHADER_INTERFACE_INFO
#undef GPU_SHADER_CREATE_INFO

namespace blender::gpu::shader {

using CreateInfoDictionnary = Map<StringRef, ShaderCreateInfo *>;
using InterfaceDictionnary = Map<StringRef, StageInterfaceInfo *>;

static CreateInfoDictionnary *g_create_infos = nullptr;
static InterfaceDictionnary *g_interfaces = nullptr;

void ShaderCreateInfo::finalize()
{
  if (finalized_) {
    return;
  }
  finalized_ = true;

  for (auto &info_name : additional_infos_) {
    const ShaderCreateInfo &info = *reinterpret_cast<const ShaderCreateInfo *>(
        gpu_shader_create_info_get(info_name.c_str()));

    /* Recursive. */
    const_cast<ShaderCreateInfo &>(info).finalize();

    interface_names_size_ += info.interface_names_size_;

    vertex_inputs_.extend(info.vertex_inputs_);
    fragment_outputs_.extend(info.fragment_outputs_);
    vertex_out_interfaces_.extend(info.vertex_out_interfaces_);
    geometry_out_interfaces_.extend(info.geometry_out_interfaces_);

    push_constants_.extend(info.push_constants_);
    defines_.extend(info.defines_);

    batch_resources_.extend(info.batch_resources_);
    pass_resources_.extend(info.pass_resources_);
    typedef_sources_.extend(info.typedef_sources_);

    if (info.local_group_size_[0] != 0) {
      BLI_assert(local_group_size_[0] == 0);
      for (int i = 0; i < 3; i++) {
        local_group_size_[i] = info.local_group_size_[i];
      }
    }
    if (!info.vertex_source_.is_empty()) {
      BLI_assert(vertex_source_.is_empty());
      vertex_source_ = info.vertex_source_;
    }
    if (!info.geometry_source_.is_empty()) {
      BLI_assert(geometry_source_.is_empty());
      geometry_source_ = info.geometry_source_;
    }
    if (!info.fragment_source_.is_empty()) {
      BLI_assert(fragment_source_.is_empty());
      fragment_source_ = info.fragment_source_;
    }
    if (!info.compute_source_.is_empty()) {
      BLI_assert(compute_source_.is_empty());
      compute_source_ = info.compute_source_;
    }

    do_static_compilation_ = do_static_compilation_ || info.do_static_compilation_;
  }
}

}  // namespace blender::gpu::shader

using namespace blender::gpu::shader;

void gpu_shader_create_info_init()
{
  g_create_infos = new CreateInfoDictionnary();
  g_interfaces = new InterfaceDictionnary();

#define GPU_SHADER_INTERFACE_INFO(_interface, _inst_name) \
  auto *ptr_##_interface = new StageInterfaceInfo(#_interface, _inst_name); \
  auto &_interface = *ptr_##_interface; \
  g_interfaces->add_new(#_interface, ptr_##_interface); \
  _interface

#define GPU_SHADER_CREATE_INFO(_info) \
  auto *ptr_##_info = new ShaderCreateInfo(#_info); \
  auto &_info = *ptr_##_info; \
  g_create_infos->add_new(#_info, ptr_##_info); \
  _info

/* Declare, register and construct the infos. */
#include "gpu_shader_create_info_list.hh"

/* Baked shader data appended to create infos. */
/* TODO(jbakker): should call a function with a callback. so we could switch implementations. We
 * cannot compile bf_gpu twice.*/
#ifdef GPU_RUNTIME
#  include "gpu_shader_baked.hh"
#endif

  /* TEST */
  // gpu_shader_create_info_compile_all();
}

void gpu_shader_create_info_exit()
{
  for (auto *value : g_create_infos->values()) {
    delete value;
  }
  delete g_create_infos;

  for (auto *value : g_interfaces->values()) {
    delete value;
  }
  delete g_interfaces;
}

bool gpu_shader_create_info_compile_all()
{
  for (ShaderCreateInfo *info : g_create_infos->values()) {
    if (info->do_static_compilation_) {
      // printf("Compiling %s: ... \n", info->name_.c_str());
      GPUShader *shader = GPU_shader_create_from_info(
          reinterpret_cast<const GPUShaderCreateInfo *>(info));
      if (shader == nullptr) {
        printf("Compilation %s Failed\n", info->name_.c_str());
        return false;
      }
      GPU_shader_free(shader);
      // printf("Success\n");
    }
  }
  return true;
}

/* Runtime create infos are not registered in the dictionary and cannot be searched. */
const GPUShaderCreateInfo *gpu_shader_create_info_get(const char *info_name)
{
  ShaderCreateInfo *info = g_create_infos->lookup(info_name);
  return reinterpret_cast<const GPUShaderCreateInfo *>(info);
}
