/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 */

#include "BKE_appdir.hh"

#include "BLI_fileops.hh"
#include "BLI_hash.hh"
#include "BLI_path_utils.hh"
#include "BLI_time.h"
#ifdef _WIN32
#  include "BLI_winstuff.h"
#endif

#include "vk_shader.hh"
#include "vk_shader_compiler.hh"

namespace blender::gpu {

static std::optional<std::string> cache_dir_get()
{
  static std::optional<std::string> result = []() -> std::optional<std::string> {
    static char tmp_dir_buffer[FILE_MAX];
    /* Shader builder doesn't return the correct appdir. */
    if (!BKE_appdir_folder_caches(tmp_dir_buffer, sizeof(tmp_dir_buffer))) {
      return std::nullopt;
    }

    std::string cache_dir = std::string(tmp_dir_buffer) + "vk-spirv-cache" + SEP_STR;
    BLI_dir_create_recursive(cache_dir.c_str());
    return cache_dir;
  }();

  return result;
}

/* -------------------------------------------------------------------- */
/** \name SPIR-V disk cache
 * \{ */

struct SPIRVSidecar {
  /** Size of the SPIRV binary. */
  uint64_t spirv_size;
};

static bool read_spirv_from_disk(VKShaderModule &shader_module)
{
  if (G.debug & G_DEBUG_GPU_RENDERDOC) {
    /* RenderDoc uses spirv shaders including debug information. */
    return false;
  }
  if (!cache_dir_get().has_value()) {
    return false;
  }
  shader_module.build_sources_hash();
  std::string spirv_path = (*cache_dir_get()) + SEP_STR + shader_module.sources_hash + ".spv";
  std::string sidecar_path = (*cache_dir_get()) + SEP_STR + shader_module.sources_hash +
                             ".sidecar.bin";

  if (!BLI_exists(spirv_path.c_str()) || !BLI_exists(sidecar_path.c_str())) {
    return false;
  }

  BLI_file_touch(spirv_path.c_str());
  BLI_file_touch(sidecar_path.c_str());

  /* Read sidecar. */
  fstream sidecar_file(sidecar_path, std::ios::binary | std::ios::in | std::ios::ate);
  std::streamsize sidecar_size_on_disk = sidecar_file.tellg();
  SPIRVSidecar sidecar = {};
  if (sidecar_size_on_disk != sizeof(sidecar)) {
    return false;
  }
  sidecar_file.seekg(0, std::ios::beg);
  sidecar_file.read(reinterpret_cast<char *>(&sidecar), sizeof(sidecar));

  /* Read spirv binary. */
  fstream spirv_file(spirv_path, std::ios::binary | std::ios::in | std::ios::ate);
  std::streamsize size = spirv_file.tellg();
  if (size != sidecar.spirv_size) {
    return false;
  }
  spirv_file.seekg(0, std::ios::beg);
  shader_module.spirv_binary.resize(size / 4);
  spirv_file.read(reinterpret_cast<char *>(shader_module.spirv_binary.data()), size);
  return true;
}

static void write_spirv_to_disk(VKShaderModule &shader_module)
{
  if (G.debug & G_DEBUG_GPU_RENDERDOC) {
    return;
  }
  if (!cache_dir_get().has_value()) {
    return;
  }

  /* Write the spirv binary */
  std::string spirv_path = (*cache_dir_get()) + SEP_STR + shader_module.sources_hash + ".spv";
  size_t size = (shader_module.compilation_result.end() -
                 shader_module.compilation_result.begin()) *
                sizeof(uint32_t);
  fstream spirv_file(spirv_path, std::ios::binary | std::ios::out);
  spirv_file.write(reinterpret_cast<const char *>(shader_module.compilation_result.begin()), size);

  /* Write the sidecar */
  SPIRVSidecar sidecar = {size};
  std::string sidecar_path = (*cache_dir_get()) + SEP_STR + shader_module.sources_hash +
                             ".sidecar.bin";
  fstream sidecar_file(sidecar_path, std::ios::binary | std::ios::out);
  sidecar_file.write(reinterpret_cast<const char *>(&sidecar), sizeof(SPIRVSidecar));
}

void VKShaderCompiler::cache_dir_clear_old()
{
  if (!cache_dir_get().has_value()) {
    return;
  }

  direntry *entries = nullptr;
  uint32_t dir_len = BLI_filelist_dir_contents(cache_dir_get()->c_str(), &entries);
  for (int i : blender::IndexRange(dir_len)) {
    direntry entry = entries[i];
    if (S_ISDIR(entry.s.st_mode)) {
      continue;
    }
    const time_t ts_now = time(nullptr);
    const time_t delete_threshold = 60 /*seconds*/ * 60 /*minutes*/ * 24 /*hours*/ * 30 /*days*/;
    if (entry.s.st_mtime + delete_threshold < ts_now) {
      BLI_delete(entry.path, false, false);
    }
  }
  BLI_filelist_free(entries, dir_len);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Compilation
 * \{ */

static StringRef to_stage_name(shaderc_shader_kind stage)
{
  switch (stage) {
    case shaderc_vertex_shader:
      return "vertex";
    case shaderc_geometry_shader:
      return "geometry";
    case shaderc_fragment_shader:
      return "fragment";
    case shaderc_compute_shader:
      return "compute";

    default:
      BLI_assert_msg(false, "Do not know how to convert shaderc_shader_kind to stage name.");
      break;
  }
  return "unknown stage";
}

static bool compile_ex(shaderc::Compiler &compiler,
                       VKShader &shader,
                       shaderc_shader_kind stage,
                       VKShaderModule &shader_module)
{
  if (read_spirv_from_disk(shader_module)) {
    return true;
  }

  shaderc::CompileOptions options;
  options.SetOptimizationLevel(shaderc_optimization_level_performance);
  options.SetTargetEnvironment(shaderc_target_env_vulkan, shaderc_env_version_vulkan_1_2);
  if (G.debug & G_DEBUG_GPU_RENDERDOC) {
    options.SetOptimizationLevel(shaderc_optimization_level_zero);
    options.SetGenerateDebugInfo();
  }

  /* WORKAROUND: Qualcomm driver can crash when handling optimized SPIR-V. */
  if (GPU_type_matches(GPU_DEVICE_QUALCOMM, GPU_OS_ANY, GPU_DRIVER_ANY)) {
    options.SetOptimizationLevel(shaderc_optimization_level_zero);
  }

  std::string full_name = shader.name_get() + "_" + to_stage_name(stage);
  shader_module.compilation_result = compiler.CompileGlslToSpv(
      shader_module.combined_sources, stage, full_name.c_str(), options);
  bool compilation_succeeded = shader_module.compilation_result.GetCompilationStatus() ==
                               shaderc_compilation_status_success;
  if (compilation_succeeded) {
    write_spirv_to_disk(shader_module);
  }
  return compilation_succeeded;
}

bool VKShaderCompiler::compile_module(VKShader &shader,
                                      shaderc_shader_kind stage,
                                      VKShaderModule &shader_module)
{
  shaderc::Compiler compiler;
  return compile_ex(compiler, shader, stage, shader_module);
}

/** \} */

}  // namespace blender::gpu
