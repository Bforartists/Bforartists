/*
 * Copyright 2011-2013 Blender Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "device.h"
#include "device_intern.h"

#include "buffers.h"

#ifdef WITH_CUDA_DYNLOAD
#  include "cuew.h"
#else
#  include "util_opengl.h"
#  include <cuda.h>
#  include <cudaGL.h>
#endif
#include "util_debug.h"
#include "util_logging.h"
#include "util_map.h"
#include "util_md5.h"
#include "util_opengl.h"
#include "util_path.h"
#include "util_string.h"
#include "util_system.h"
#include "util_types.h"
#include "util_time.h"

/* use feature-adaptive kernel compilation.
 * Requires CUDA toolkit to be installed and currently only works on Linux.
 */
/* #define KERNEL_USE_ADAPTIVE */

CCL_NAMESPACE_BEGIN

#ifndef WITH_CUDA_DYNLOAD

/* Transparently implement some functions, so majority of the file does not need
 * to worry about difference between dynamically loaded and linked CUDA at all.
 */

namespace {

const char *cuewErrorString(CUresult result)
{
	/* We can only give error code here without major code duplication, that
	 * should be enough since dynamic loading is only being disabled by folks
	 * who knows what they're doing anyway.
	 *
	 * NOTE: Avoid call from several threads.
	 */
	static string error;
	error = string_printf("%d", result);
	return error.c_str();
}

const char *cuewCompilerPath(void)
{
	return CYCLES_CUDA_NVCC_EXECUTABLE;
}

int cuewCompilerVersion(void)
{
	return (CUDA_VERSION / 100) + (CUDA_VERSION % 100 / 10);
}

}  /* namespace */
#endif  /* WITH_CUDA_DYNLOAD */

class CUDADevice : public Device
{
public:
	DedicatedTaskPool task_pool;
	CUdevice cuDevice;
	CUcontext cuContext;
	CUmodule cuModule;
	map<device_ptr, bool> tex_interp_map;
	int cuDevId;
	int cuDevArchitecture;
	bool first_error;
	bool use_texture_storage;

	struct PixelMem {
		GLuint cuPBO;
		CUgraphicsResource cuPBOresource;
		GLuint cuTexId;
		int w, h;
	};

	map<device_ptr, PixelMem> pixel_mem_map;

	CUdeviceptr cuda_device_ptr(device_ptr mem)
	{
		return (CUdeviceptr)mem;
	}

	static bool have_precompiled_kernels()
	{
		string cubins_path = path_get("lib");
		return path_exists(cubins_path);
	}

/*#ifdef NDEBUG
#define cuda_abort()
#else
#define cuda_abort() abort()
#endif*/
	void cuda_error_documentation()
	{
		if(first_error) {
			fprintf(stderr, "\nRefer to the Cycles GPU rendering documentation for possible solutions:\n");
			fprintf(stderr, "http://www.blender.org/manual/render/cycles/gpu_rendering.html\n\n");
			first_error = false;
		}
	}

#define cuda_assert(stmt) \
	{ \
		CUresult result = stmt; \
		\
		if(result != CUDA_SUCCESS) { \
			string message = string_printf("CUDA error: %s in %s", cuewErrorString(result), #stmt); \
			if(error_msg == "") \
				error_msg = message; \
			fprintf(stderr, "%s\n", message.c_str()); \
			/*cuda_abort();*/ \
			cuda_error_documentation(); \
		} \
	} (void)0

	bool cuda_error_(CUresult result, const string& stmt)
	{
		if(result == CUDA_SUCCESS)
			return false;

		string message = string_printf("CUDA error at %s: %s", stmt.c_str(), cuewErrorString(result));
		if(error_msg == "")
			error_msg = message;
		fprintf(stderr, "%s\n", message.c_str());
		cuda_error_documentation();
		return true;
	}

#define cuda_error(stmt) cuda_error_(stmt, #stmt)

	void cuda_error_message(const string& message)
	{
		if(error_msg == "")
			error_msg = message;
		fprintf(stderr, "%s\n", message.c_str());
		cuda_error_documentation();
	}

	void cuda_push_context()
	{
		cuda_assert(cuCtxSetCurrent(cuContext));
	}

	void cuda_pop_context()
	{
		cuda_assert(cuCtxSetCurrent(NULL));
	}

	CUDADevice(DeviceInfo& info, Stats &stats, bool background_)
	: Device(info, stats, background_)
	{
		first_error = true;
		background = background_;
		use_texture_storage = true;

		cuDevId = info.num;
		cuDevice = 0;
		cuContext = 0;

		/* intialize */
		if(cuda_error(cuInit(0)))
			return;

		/* setup device and context */
		if(cuda_error(cuDeviceGet(&cuDevice, cuDevId)))
			return;

		CUresult result;

		if(background) {
			result = cuCtxCreate(&cuContext, 0, cuDevice);
		}
		else {
			result = cuGLCtxCreate(&cuContext, 0, cuDevice);

			if(result != CUDA_SUCCESS) {
				result = cuCtxCreate(&cuContext, 0, cuDevice);
				background = true;
			}
		}

		if(cuda_error_(result, "cuCtxCreate"))
			return;

		int major, minor;
		cuDeviceComputeCapability(&major, &minor, cuDevId);
		cuDevArchitecture = major*100 + minor*10;

		/* In order to use full 6GB of memory on Titan cards, use arrays instead
		 * of textures. On earlier cards this seems slower, but on Titan it is
		 * actually slightly faster in tests. */
		use_texture_storage = (cuDevArchitecture < 300);

		cuda_pop_context();
	}

	~CUDADevice()
	{
		task_pool.stop();

		cuda_assert(cuCtxDestroy(cuContext));
	}

	bool support_device(const DeviceRequestedFeatures& /*requested_features*/)
	{
		int major, minor;
		cuDeviceComputeCapability(&major, &minor, cuDevId);

		/* We only support sm_20 and above */
		if(major < 2) {
			cuda_error_message(string_printf("CUDA device supported only with compute capability 2.0 or up, found %d.%d.", major, minor));
			return false;
		}

		return true;
	}

	string compile_kernel(const DeviceRequestedFeatures& requested_features)
	{
		/* compute cubin name */
		int major, minor;
		cuDeviceComputeCapability(&major, &minor, cuDevId);
		string cubin;

		/* attempt to use kernel provided with blender */
		cubin = path_get(string_printf("lib/kernel_sm_%d%d.cubin", major, minor));
		VLOG(1) << "Testing for pre-compiled kernel " << cubin;
		if(path_exists(cubin)) {
			VLOG(1) << "Using precompiled kernel";
			return cubin;
		}

		/* not found, try to use locally compiled kernel */
		string kernel_path = path_get("kernel");
		string md5 = path_files_md5_hash(kernel_path);

#ifdef KERNEL_USE_ADAPTIVE
		string feature_build_options = requested_features.get_build_options();
		string device_md5 = util_md5_string(feature_build_options);
		cubin = string_printf("cycles_kernel_%s_sm%d%d_%s.cubin",
		                      device_md5.c_str(),
		                      major, minor,
		                      md5.c_str());
#else
		(void)requested_features;
		cubin = string_printf("cycles_kernel_sm%d%d_%s.cubin", major, minor, md5.c_str());
#endif

		cubin = path_user_get(path_join("cache", cubin));
		VLOG(1) << "Testing for locally compiled kernel " << cubin;
		/* if exists already, use it */
		if(path_exists(cubin)) {
			VLOG(1) << "Using locally compiled kernel";
			return cubin;
		}

#ifdef _WIN32
		if(have_precompiled_kernels()) {
			if(major < 2)
				cuda_error_message(string_printf("CUDA device requires compute capability 2.0 or up, found %d.%d. Your GPU is not supported.", major, minor));
			else
				cuda_error_message(string_printf("CUDA binary kernel for this graphics card compute capability (%d.%d) not found.", major, minor));
			return "";
		}
#endif

		/* if not, find CUDA compiler */
		const char *nvcc = cuewCompilerPath();

		if(nvcc == NULL) {
			cuda_error_message("CUDA nvcc compiler not found. Install CUDA toolkit in default location.");
			return "";
		}

		int cuda_version = cuewCompilerVersion();
		VLOG(1) << "Found nvcc " << nvcc << ", CUDA version " << cuda_version;

		if(cuda_version == 0) {
			cuda_error_message("CUDA nvcc compiler version could not be parsed.");
			return "";
		}
		if(cuda_version < 60) {
			printf("Unsupported CUDA version %d.%d detected, you need CUDA 7.5.\n", cuda_version/10, cuda_version%10);
			return "";
		}
		else if(cuda_version != 75)
			printf("CUDA version %d.%d detected, build may succeed but only CUDA 7.5 is officially supported.\n", cuda_version/10, cuda_version%10);

		/* compile */
		string kernel = path_join(kernel_path, path_join("kernels", path_join("cuda", "kernel.cu")));
		string include = kernel_path;
		const int machine = system_cpu_bits();

		double starttime = time_dt();
		printf("Compiling CUDA kernel ...\n");

		path_create_directories(cubin);

		string command = string_printf("\"%s\" -arch=sm_%d%d -m%d --cubin \"%s\" "
			"-o \"%s\" --ptxas-options=\"-v\" --use_fast_math -I\"%s\" "
			"-DNVCC -D__KERNEL_CUDA_VERSION__=%d",
			nvcc, major, minor, machine, kernel.c_str(), cubin.c_str(), include.c_str(), cuda_version);

#ifdef KERNEL_USE_ADAPTIVE
		command += " " + feature_build_options;
#endif

		const char* extra_cflags = getenv("CYCLES_CUDA_EXTRA_CFLAGS");
		if(extra_cflags) {
			command += string(" ") + string(extra_cflags);
		}

#ifdef WITH_CYCLES_DEBUG
		command += " -D__KERNEL_DEBUG__";
#endif

		printf("%s\n", command.c_str());

		if(system(command.c_str()) == -1) {
			cuda_error_message("Failed to execute compilation command, see console for details.");
			return "";
		}

		/* verify if compilation succeeded */
		if(!path_exists(cubin)) {
			cuda_error_message("CUDA kernel compilation failed, see console for details.");
			return "";
		}

		printf("Kernel compilation finished in %.2lfs.\n", time_dt() - starttime);

		return cubin;
	}

	bool load_kernels(const DeviceRequestedFeatures& requested_features)
	{
		/* check if cuda init succeeded */
		if(cuContext == 0)
			return false;

		/* check if GPU is supported */
		if(!support_device(requested_features))
			return false;

		/* get kernel */
		string cubin = compile_kernel(requested_features);

		if(cubin == "")
			return false;

		/* open module */
		cuda_push_context();

		string cubin_data;
		CUresult result;

		if(path_read_text(cubin, cubin_data))
			result = cuModuleLoadData(&cuModule, cubin_data.c_str());
		else
			result = CUDA_ERROR_FILE_NOT_FOUND;

		if(cuda_error_(result, "cuModuleLoad"))
			cuda_error_message(string_printf("Failed loading CUDA kernel %s.", cubin.c_str()));

		cuda_pop_context();

		return (result == CUDA_SUCCESS);
	}

	void mem_alloc(device_memory& mem, MemoryType /*type*/)
	{
		cuda_push_context();
		CUdeviceptr device_pointer;
		size_t size = mem.memory_size();
		cuda_assert(cuMemAlloc(&device_pointer, size));
		mem.device_pointer = (device_ptr)device_pointer;
		mem.device_size = size;
		stats.mem_alloc(size);
		cuda_pop_context();
	}

	void mem_copy_to(device_memory& mem)
	{
		cuda_push_context();
		if(mem.device_pointer)
			cuda_assert(cuMemcpyHtoD(cuda_device_ptr(mem.device_pointer), (void*)mem.data_pointer, mem.memory_size()));
		cuda_pop_context();
	}

	void mem_copy_from(device_memory& mem, int y, int w, int h, int elem)
	{
		size_t offset = elem*y*w;
		size_t size = elem*w*h;

		cuda_push_context();
		if(mem.device_pointer) {
			cuda_assert(cuMemcpyDtoH((uchar*)mem.data_pointer + offset,
			                         (CUdeviceptr)(mem.device_pointer + offset), size));
		}
		else {
			memset((char*)mem.data_pointer + offset, 0, size);
		}
		cuda_pop_context();
	}

	void mem_zero(device_memory& mem)
	{
		memset((void*)mem.data_pointer, 0, mem.memory_size());

		cuda_push_context();
		if(mem.device_pointer)
			cuda_assert(cuMemsetD8(cuda_device_ptr(mem.device_pointer), 0, mem.memory_size()));
		cuda_pop_context();
	}

	void mem_free(device_memory& mem)
	{
		if(mem.device_pointer) {
			cuda_push_context();
			cuda_assert(cuMemFree(cuda_device_ptr(mem.device_pointer)));
			cuda_pop_context();

			mem.device_pointer = 0;

			stats.mem_free(mem.device_size);
			mem.device_size = 0;
		}
	}

	void const_copy_to(const char *name, void *host, size_t size)
	{
		CUdeviceptr mem;
		size_t bytes;

		cuda_push_context();
		cuda_assert(cuModuleGetGlobal(&mem, &bytes, cuModule, name));
		//assert(bytes == size);
		cuda_assert(cuMemcpyHtoD(mem, host, size));
		cuda_pop_context();
	}

	void tex_alloc(const char *name,
	               device_memory& mem,
	               InterpolationType interpolation,
	               ExtensionType extension)
	{
		VLOG(1) << "Texture allocate: " << name << ", " << mem.memory_size() << " bytes.";

		string bind_name = name;
		if(mem.data_depth > 1) {
			/* Kernel uses different bind names for 2d and 3d float textures,
			 * so we have to adjust couple of things here.
			 */
			vector<string> tokens;
			string_split(tokens, name, "_");
			bind_name = string_printf("__tex_image_%s3d_%s",
			                          tokens[2].c_str(),
			                          tokens[3].c_str());
		}

		/* determine format */
		CUarray_format_enum format;
		size_t dsize = datatype_size(mem.data_type);
		size_t size = mem.memory_size();
		bool use_texture = (interpolation != INTERPOLATION_NONE) || use_texture_storage;

		if(use_texture) {

			switch(mem.data_type) {
				case TYPE_UCHAR: format = CU_AD_FORMAT_UNSIGNED_INT8; break;
				case TYPE_UINT: format = CU_AD_FORMAT_UNSIGNED_INT32; break;
				case TYPE_INT: format = CU_AD_FORMAT_SIGNED_INT32; break;
				case TYPE_FLOAT: format = CU_AD_FORMAT_FLOAT; break;
				default: assert(0); return;
			}

			CUtexref texref = NULL;

			cuda_push_context();
			cuda_assert(cuModuleGetTexRef(&texref, cuModule, bind_name.c_str()));

			if(!texref) {
				cuda_pop_context();
				return;
			}

			if(interpolation != INTERPOLATION_NONE) {
				CUarray handle = NULL;

				if(mem.data_depth > 1) {
					CUDA_ARRAY3D_DESCRIPTOR desc;

					desc.Width = mem.data_width;
					desc.Height = mem.data_height;
					desc.Depth = mem.data_depth;
					desc.Format = format;
					desc.NumChannels = mem.data_elements;
					desc.Flags = 0;

					cuda_assert(cuArray3DCreate(&handle, &desc));
				}
				else {
					CUDA_ARRAY_DESCRIPTOR desc;

					desc.Width = mem.data_width;
					desc.Height = mem.data_height;
					desc.Format = format;
					desc.NumChannels = mem.data_elements;

					cuda_assert(cuArrayCreate(&handle, &desc));
				}

				if(!handle) {
					cuda_pop_context();
					return;
				}

				if(mem.data_depth > 1) {
					CUDA_MEMCPY3D param;
					memset(&param, 0, sizeof(param));
					param.dstMemoryType = CU_MEMORYTYPE_ARRAY;
					param.dstArray = handle;
					param.srcMemoryType = CU_MEMORYTYPE_HOST;
					param.srcHost = (void*)mem.data_pointer;
					param.srcPitch = mem.data_width*dsize*mem.data_elements;
					param.WidthInBytes = param.srcPitch;
					param.Height = mem.data_height;
					param.Depth = mem.data_depth;

					cuda_assert(cuMemcpy3D(&param));
				}
				if(mem.data_height > 1) {
					CUDA_MEMCPY2D param;
					memset(&param, 0, sizeof(param));
					param.dstMemoryType = CU_MEMORYTYPE_ARRAY;
					param.dstArray = handle;
					param.srcMemoryType = CU_MEMORYTYPE_HOST;
					param.srcHost = (void*)mem.data_pointer;
					param.srcPitch = mem.data_width*dsize*mem.data_elements;
					param.WidthInBytes = param.srcPitch;
					param.Height = mem.data_height;

					cuda_assert(cuMemcpy2D(&param));
				}
				else
					cuda_assert(cuMemcpyHtoA(handle, 0, (void*)mem.data_pointer, size));

				cuda_assert(cuTexRefSetArray(texref, handle, CU_TRSA_OVERRIDE_FORMAT));

				if(interpolation == INTERPOLATION_CLOSEST) {
					cuda_assert(cuTexRefSetFilterMode(texref, CU_TR_FILTER_MODE_POINT));
				}
				else if(interpolation == INTERPOLATION_LINEAR) {
					cuda_assert(cuTexRefSetFilterMode(texref, CU_TR_FILTER_MODE_LINEAR));
				}
				else {/* CUBIC and SMART are unsupported for CUDA */
					cuda_assert(cuTexRefSetFilterMode(texref, CU_TR_FILTER_MODE_LINEAR));
				}
				cuda_assert(cuTexRefSetFlags(texref, CU_TRSF_NORMALIZED_COORDINATES));

				mem.device_pointer = (device_ptr)handle;
				mem.device_size = size;

				stats.mem_alloc(size);
			}
			else {
				cuda_pop_context();

				mem_alloc(mem, MEM_READ_ONLY);
				mem_copy_to(mem);

				cuda_push_context();

				cuda_assert(cuTexRefSetAddress(NULL, texref, cuda_device_ptr(mem.device_pointer), size));
				cuda_assert(cuTexRefSetFilterMode(texref, CU_TR_FILTER_MODE_POINT));
				cuda_assert(cuTexRefSetFlags(texref, CU_TRSF_READ_AS_INTEGER));
			}

			switch(extension) {
				case EXTENSION_REPEAT:
					cuda_assert(cuTexRefSetAddressMode(texref, 0, CU_TR_ADDRESS_MODE_WRAP));
					cuda_assert(cuTexRefSetAddressMode(texref, 1, CU_TR_ADDRESS_MODE_WRAP));
					break;
				case EXTENSION_EXTEND:
					cuda_assert(cuTexRefSetAddressMode(texref, 0, CU_TR_ADDRESS_MODE_CLAMP));
					cuda_assert(cuTexRefSetAddressMode(texref, 1, CU_TR_ADDRESS_MODE_CLAMP));
					break;
				case EXTENSION_CLIP:
					cuda_assert(cuTexRefSetAddressMode(texref, 0, CU_TR_ADDRESS_MODE_BORDER));
					cuda_assert(cuTexRefSetAddressMode(texref, 1, CU_TR_ADDRESS_MODE_BORDER));
					break;
				default:
					assert(0);
			}
			cuda_assert(cuTexRefSetFormat(texref, format, mem.data_elements));

			cuda_pop_context();
		}
		else {
			mem_alloc(mem, MEM_READ_ONLY);
			mem_copy_to(mem);

			cuda_push_context();

			CUdeviceptr cumem;
			size_t cubytes;

			cuda_assert(cuModuleGetGlobal(&cumem, &cubytes, cuModule, bind_name.c_str()));

			if(cubytes == 8) {
				/* 64 bit device pointer */
				uint64_t ptr = mem.device_pointer;
				cuda_assert(cuMemcpyHtoD(cumem, (void*)&ptr, cubytes));
			}
			else {
				/* 32 bit device pointer */
				uint32_t ptr = (uint32_t)mem.device_pointer;
				cuda_assert(cuMemcpyHtoD(cumem, (void*)&ptr, cubytes));
			}

			cuda_pop_context();
		}

		tex_interp_map[mem.device_pointer] = (interpolation != INTERPOLATION_NONE);
	}

	void tex_free(device_memory& mem)
	{
		if(mem.device_pointer) {
			if(tex_interp_map[mem.device_pointer]) {
				cuda_push_context();
				cuArrayDestroy((CUarray)mem.device_pointer);
				cuda_pop_context();

				tex_interp_map.erase(tex_interp_map.find(mem.device_pointer));
				mem.device_pointer = 0;

				stats.mem_free(mem.device_size);
				mem.device_size = 0;
			}
			else {
				tex_interp_map.erase(tex_interp_map.find(mem.device_pointer));
				mem_free(mem);
			}
		}
	}

	void path_trace(RenderTile& rtile, int sample, bool branched)
	{
		if(have_error())
			return;

		cuda_push_context();

		CUfunction cuPathTrace;
		CUdeviceptr d_buffer = cuda_device_ptr(rtile.buffer);
		CUdeviceptr d_rng_state = cuda_device_ptr(rtile.rng_state);

		/* get kernel function */
		if(branched) {
			cuda_assert(cuModuleGetFunction(&cuPathTrace, cuModule, "kernel_cuda_branched_path_trace"));
		}
		else {
			cuda_assert(cuModuleGetFunction(&cuPathTrace, cuModule, "kernel_cuda_path_trace"));
		}

		if(have_error())
			return;

		/* pass in parameters */
		void *args[] = {&d_buffer,
		                &d_rng_state,
		                &sample,
		                &rtile.x,
		                &rtile.y,
		                &rtile.w,
		                &rtile.h,
		                &rtile.offset,
		                &rtile.stride};

		/* launch kernel */
		int threads_per_block;
		cuda_assert(cuFuncGetAttribute(&threads_per_block, CU_FUNC_ATTRIBUTE_MAX_THREADS_PER_BLOCK, cuPathTrace));

		/*int num_registers;
		cuda_assert(cuFuncGetAttribute(&num_registers, CU_FUNC_ATTRIBUTE_NUM_REGS, cuPathTrace));

		printf("threads_per_block %d\n", threads_per_block);
		printf("num_registers %d\n", num_registers);*/

		int xthreads = (int)sqrt((float)threads_per_block);
		int ythreads = (int)sqrt((float)threads_per_block);
		int xblocks = (rtile.w + xthreads - 1)/xthreads;
		int yblocks = (rtile.h + ythreads - 1)/ythreads;

		cuda_assert(cuFuncSetCacheConfig(cuPathTrace, CU_FUNC_CACHE_PREFER_L1));

		cuda_assert(cuLaunchKernel(cuPathTrace,
		                           xblocks , yblocks, 1, /* blocks */
		                           xthreads, ythreads, 1, /* threads */
		                           0, 0, args, 0));

		cuda_assert(cuCtxSynchronize());

		cuda_pop_context();
	}

	void film_convert(DeviceTask& task, device_ptr buffer, device_ptr rgba_byte, device_ptr rgba_half)
	{
		if(have_error())
			return;

		cuda_push_context();

		CUfunction cuFilmConvert;
		CUdeviceptr d_rgba = map_pixels((rgba_byte)? rgba_byte: rgba_half);
		CUdeviceptr d_buffer = cuda_device_ptr(buffer);

		/* get kernel function */
		if(rgba_half) {
			cuda_assert(cuModuleGetFunction(&cuFilmConvert, cuModule, "kernel_cuda_convert_to_half_float"));
		}
		else {
			cuda_assert(cuModuleGetFunction(&cuFilmConvert, cuModule, "kernel_cuda_convert_to_byte"));
		}


		float sample_scale = 1.0f/(task.sample + 1);

		/* pass in parameters */
		void *args[] = {&d_rgba,
		                &d_buffer,
		                &sample_scale,
		                &task.x,
		                &task.y,
		                &task.w,
		                &task.h,
		                &task.offset,
		                &task.stride};

		/* launch kernel */
		int threads_per_block;
		cuda_assert(cuFuncGetAttribute(&threads_per_block, CU_FUNC_ATTRIBUTE_MAX_THREADS_PER_BLOCK, cuFilmConvert));

		int xthreads = (int)sqrt((float)threads_per_block);
		int ythreads = (int)sqrt((float)threads_per_block);
		int xblocks = (task.w + xthreads - 1)/xthreads;
		int yblocks = (task.h + ythreads - 1)/ythreads;

		cuda_assert(cuFuncSetCacheConfig(cuFilmConvert, CU_FUNC_CACHE_PREFER_L1));

		cuda_assert(cuLaunchKernel(cuFilmConvert,
		                           xblocks , yblocks, 1, /* blocks */
		                           xthreads, ythreads, 1, /* threads */
		                           0, 0, args, 0));

		unmap_pixels((rgba_byte)? rgba_byte: rgba_half);

		cuda_pop_context();
	}

	void shader(DeviceTask& task)
	{
		if(have_error())
			return;

		cuda_push_context();

		CUfunction cuShader;
		CUdeviceptr d_input = cuda_device_ptr(task.shader_input);
		CUdeviceptr d_output = cuda_device_ptr(task.shader_output);
		CUdeviceptr d_output_luma = cuda_device_ptr(task.shader_output_luma);

		/* get kernel function */
		if(task.shader_eval_type >= SHADER_EVAL_BAKE) {
			cuda_assert(cuModuleGetFunction(&cuShader, cuModule, "kernel_cuda_bake"));
		}
		else {
			cuda_assert(cuModuleGetFunction(&cuShader, cuModule, "kernel_cuda_shader"));
		}

		/* do tasks in smaller chunks, so we can cancel it */
		const int shader_chunk_size = 65536;
		const int start = task.shader_x;
		const int end = task.shader_x + task.shader_w;
		int offset = task.offset;

		bool canceled = false;
		for(int sample = 0; sample < task.num_samples && !canceled; sample++) {
			for(int shader_x = start; shader_x < end; shader_x += shader_chunk_size) {
				int shader_w = min(shader_chunk_size, end - shader_x);

				/* pass in parameters */
				void *args[8];
				int arg = 0;
				args[arg++] = &d_input;
				args[arg++] = &d_output;
				if(task.shader_eval_type < SHADER_EVAL_BAKE) {
					args[arg++] = &d_output_luma;
				}
				args[arg++] = &task.shader_eval_type;
				if(task.shader_eval_type >= SHADER_EVAL_BAKE) {
					args[arg++] = &task.shader_filter;
				}
				args[arg++] = &shader_x;
				args[arg++] = &shader_w;
				args[arg++] = &offset;
				args[arg++] = &sample;

				/* launch kernel */
				int threads_per_block;
				cuda_assert(cuFuncGetAttribute(&threads_per_block, CU_FUNC_ATTRIBUTE_MAX_THREADS_PER_BLOCK, cuShader));

				int xblocks = (shader_w + threads_per_block - 1)/threads_per_block;

				cuda_assert(cuFuncSetCacheConfig(cuShader, CU_FUNC_CACHE_PREFER_L1));
				cuda_assert(cuLaunchKernel(cuShader,
				                           xblocks , 1, 1, /* blocks */
				                           threads_per_block, 1, 1, /* threads */
				                           0, 0, args, 0));

				cuda_assert(cuCtxSynchronize());

				if(task.get_cancel()) {
					canceled = false;
					break;
				}
			}

			task.update_progress(NULL);
		}

		cuda_pop_context();
	}

	CUdeviceptr map_pixels(device_ptr mem)
	{
		if(!background) {
			PixelMem pmem = pixel_mem_map[mem];
			CUdeviceptr buffer;
			
			size_t bytes;
			cuda_assert(cuGraphicsMapResources(1, &pmem.cuPBOresource, 0));
			cuda_assert(cuGraphicsResourceGetMappedPointer(&buffer, &bytes, pmem.cuPBOresource));
			
			return buffer;
		}

		return cuda_device_ptr(mem);
	}

	void unmap_pixels(device_ptr mem)
	{
		if(!background) {
			PixelMem pmem = pixel_mem_map[mem];

			cuda_assert(cuGraphicsUnmapResources(1, &pmem.cuPBOresource, 0));
		}
	}

	void pixels_alloc(device_memory& mem)
	{
		if(!background) {
			PixelMem pmem;

			pmem.w = mem.data_width;
			pmem.h = mem.data_height;

			cuda_push_context();

			glGenBuffers(1, &pmem.cuPBO);
			glBindBuffer(GL_PIXEL_UNPACK_BUFFER, pmem.cuPBO);
			if(mem.data_type == TYPE_HALF)
				glBufferData(GL_PIXEL_UNPACK_BUFFER, pmem.w*pmem.h*sizeof(GLhalf)*4, NULL, GL_DYNAMIC_DRAW);
			else
				glBufferData(GL_PIXEL_UNPACK_BUFFER, pmem.w*pmem.h*sizeof(uint8_t)*4, NULL, GL_DYNAMIC_DRAW);
			
			glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0);
			
			glGenTextures(1, &pmem.cuTexId);
			glBindTexture(GL_TEXTURE_2D, pmem.cuTexId);
			if(mem.data_type == TYPE_HALF)
				glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA16F_ARB, pmem.w, pmem.h, 0, GL_RGBA, GL_HALF_FLOAT, NULL);
			else
				glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, pmem.w, pmem.h, 0, GL_RGBA, GL_UNSIGNED_BYTE, NULL);
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
			glBindTexture(GL_TEXTURE_2D, 0);
			
			CUresult result = cuGraphicsGLRegisterBuffer(&pmem.cuPBOresource, pmem.cuPBO, CU_GRAPHICS_MAP_RESOURCE_FLAGS_NONE);

			if(result == CUDA_SUCCESS) {
				cuda_pop_context();

				mem.device_pointer = pmem.cuTexId;
				pixel_mem_map[mem.device_pointer] = pmem;

				mem.device_size = mem.memory_size();
				stats.mem_alloc(mem.device_size);

				return;
			}
			else {
				/* failed to register buffer, fallback to no interop */
				glDeleteBuffers(1, &pmem.cuPBO);
				glDeleteTextures(1, &pmem.cuTexId);

				cuda_pop_context();

				background = true;
			}
		}

		Device::pixels_alloc(mem);
	}

	void pixels_copy_from(device_memory& mem, int y, int w, int h)
	{
		if(!background) {
			PixelMem pmem = pixel_mem_map[mem.device_pointer];

			cuda_push_context();

			glBindBuffer(GL_PIXEL_UNPACK_BUFFER, pmem.cuPBO);
			uchar *pixels = (uchar*)glMapBuffer(GL_PIXEL_UNPACK_BUFFER, GL_READ_ONLY);
			size_t offset = sizeof(uchar)*4*y*w;
			memcpy((uchar*)mem.data_pointer + offset, pixels + offset, sizeof(uchar)*4*w*h);
			glUnmapBuffer(GL_PIXEL_UNPACK_BUFFER);
			glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0);

			cuda_pop_context();

			return;
		}

		Device::pixels_copy_from(mem, y, w, h);
	}

	void pixels_free(device_memory& mem)
	{
		if(mem.device_pointer) {
			if(!background) {
				PixelMem pmem = pixel_mem_map[mem.device_pointer];

				cuda_push_context();

				cuda_assert(cuGraphicsUnregisterResource(pmem.cuPBOresource));
				glDeleteBuffers(1, &pmem.cuPBO);
				glDeleteTextures(1, &pmem.cuTexId);

				cuda_pop_context();

				pixel_mem_map.erase(pixel_mem_map.find(mem.device_pointer));
				mem.device_pointer = 0;

				stats.mem_free(mem.device_size);
				mem.device_size = 0;

				return;
			}

			Device::pixels_free(mem);
		}
	}

	void draw_pixels(device_memory& mem, int y, int w, int h, int dx, int dy, int width, int height, bool transparent,
		const DeviceDrawParams &draw_params)
	{
		if(!background) {
			PixelMem pmem = pixel_mem_map[mem.device_pointer];
			float *vpointer;

			cuda_push_context();

			/* for multi devices, this assumes the inefficient method that we allocate
			 * all pixels on the device even though we only render to a subset */
			size_t offset = 4*y*w;

			if(mem.data_type == TYPE_HALF)
				offset *= sizeof(GLhalf);
			else
				offset *= sizeof(uint8_t);

			glBindBuffer(GL_PIXEL_UNPACK_BUFFER, pmem.cuPBO);
			glBindTexture(GL_TEXTURE_2D, pmem.cuTexId);
			if(mem.data_type == TYPE_HALF)
				glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, w, h, GL_RGBA, GL_HALF_FLOAT, (void*)offset);
			else
				glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE, (void*)offset);
			glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0);
			
			glEnable(GL_TEXTURE_2D);
			
			if(transparent) {
				glEnable(GL_BLEND);
				glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA);
			}

			glColor3f(1.0f, 1.0f, 1.0f);

			if(draw_params.bind_display_space_shader_cb) {
				draw_params.bind_display_space_shader_cb();
			}

			if(!vertex_buffer)
				glGenBuffers(1, &vertex_buffer);

			glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer);
			/* invalidate old contents - avoids stalling if buffer is still waiting in queue to be rendered */
			glBufferData(GL_ARRAY_BUFFER, 16 * sizeof(float), NULL, GL_STREAM_DRAW);

			vpointer = (float *)glMapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY);

			if(vpointer) {
				/* texture coordinate - vertex pair */
				vpointer[0] = 0.0f;
				vpointer[1] = 0.0f;
				vpointer[2] = dx;
				vpointer[3] = dy;

				vpointer[4] = (float)w/(float)pmem.w;
				vpointer[5] = 0.0f;
				vpointer[6] = (float)width + dx;
				vpointer[7] = dy;

				vpointer[8] = (float)w/(float)pmem.w;
				vpointer[9] = (float)h/(float)pmem.h;
				vpointer[10] = (float)width + dx;
				vpointer[11] = (float)height + dy;

				vpointer[12] = 0.0f;
				vpointer[13] = (float)h/(float)pmem.h;
				vpointer[14] = dx;
				vpointer[15] = (float)height + dy;

				glUnmapBuffer(GL_ARRAY_BUFFER);
			}

			glTexCoordPointer(2, GL_FLOAT, 4 * sizeof(float), 0);
			glVertexPointer(2, GL_FLOAT, 4 * sizeof(float), (char *)NULL + 2 * sizeof(float));

			glEnableClientState(GL_VERTEX_ARRAY);
			glEnableClientState(GL_TEXTURE_COORD_ARRAY);

			glDrawArrays(GL_TRIANGLE_FAN, 0, 4);

			glDisableClientState(GL_TEXTURE_COORD_ARRAY);
			glDisableClientState(GL_VERTEX_ARRAY);

			glBindBuffer(GL_ARRAY_BUFFER, 0);

			if(draw_params.unbind_display_space_shader_cb) {
				draw_params.unbind_display_space_shader_cb();
			}

			if(transparent)
				glDisable(GL_BLEND);
			
			glBindTexture(GL_TEXTURE_2D, 0);
			glDisable(GL_TEXTURE_2D);

			cuda_pop_context();

			return;
		}

		Device::draw_pixels(mem, y, w, h, dx, dy, width, height, transparent, draw_params);
	}

	void thread_run(DeviceTask *task)
	{
		if(task->type == DeviceTask::PATH_TRACE) {
			RenderTile tile;
			
			bool branched = task->integrator_branched;
			
			/* keep rendering tiles until done */
			while(task->acquire_tile(this, tile)) {
				int start_sample = tile.start_sample;
				int end_sample = tile.start_sample + tile.num_samples;

				for(int sample = start_sample; sample < end_sample; sample++) {
					if(task->get_cancel()) {
						if(task->need_finish_queue == false)
							break;
					}

					path_trace(tile, sample, branched);

					tile.sample = sample + 1;

					task->update_progress(&tile);
				}

				task->release_tile(tile);
			}
		}
		else if(task->type == DeviceTask::SHADER) {
			shader(*task);

			cuda_push_context();
			cuda_assert(cuCtxSynchronize());
			cuda_pop_context();
		}
	}

	class CUDADeviceTask : public DeviceTask {
	public:
		CUDADeviceTask(CUDADevice *device, DeviceTask& task)
		: DeviceTask(task)
		{
			run = function_bind(&CUDADevice::thread_run, device, this);
		}
	};

	int get_split_task_count(DeviceTask& /*task*/)
	{
		return 1;
	}

	void task_add(DeviceTask& task)
	{
		if(task.type == DeviceTask::FILM_CONVERT) {
			/* must be done in main thread due to opengl access */
			film_convert(task, task.buffer, task.rgba_byte, task.rgba_half);

			cuda_push_context();
			cuda_assert(cuCtxSynchronize());
			cuda_pop_context();
		}
		else {
			task_pool.push(new CUDADeviceTask(this, task));
		}
	}

	void task_wait()
	{
		task_pool.wait();
	}

	void task_cancel()
	{
		task_pool.cancel();
	}
};

bool device_cuda_init(void)
{
#ifdef WITH_CUDA_DYNLOAD
	static bool initialized = false;
	static bool result = false;

	if(initialized)
		return result;

	initialized = true;
	int cuew_result = cuewInit();
	if(cuew_result == CUEW_SUCCESS) {
		VLOG(1) << "CUEW initialization succeeded";
		if(CUDADevice::have_precompiled_kernels()) {
			VLOG(1) << "Found precompiled kernels";
			result = true;
		}
#ifndef _WIN32
		else if(cuewCompilerPath() != NULL) {
			VLOG(1) << "Found CUDA compiler " << cuewCompilerPath();
			result = true;
		}
		else {
			VLOG(1) << "Neither precompiled kernels nor CUDA compiler wad found,"
			        << " unable to use CUDA";
		}
#endif
	}
	else {
		VLOG(1) << "CUEW initialization failed: "
		        << ((cuew_result == CUEW_ERROR_ATEXIT_FAILED)
		            ? "Error setting up atexit() handler"
		            : "Error opening the library");
	}

	return result;
#else  /* WITH_CUDA_DYNLOAD */
	return true;
#endif /* WITH_CUDA_DYNLOAD */
}

Device *device_cuda_create(DeviceInfo& info, Stats &stats, bool background)
{
	return new CUDADevice(info, stats, background);
}

void device_cuda_info(vector<DeviceInfo>& devices)
{
	CUresult result;
	int count = 0;

	result = cuInit(0);
	if(result != CUDA_SUCCESS) {
		if(result != CUDA_ERROR_NO_DEVICE)
			fprintf(stderr, "CUDA cuInit: %s\n", cuewErrorString(result));
		return;
	}

	result = cuDeviceGetCount(&count);
	if(result != CUDA_SUCCESS) {
		fprintf(stderr, "CUDA cuDeviceGetCount: %s\n", cuewErrorString(result));
		return;
	}
	
	vector<DeviceInfo> display_devices;

	for(int num = 0; num < count; num++) {
		char name[256];
		int attr;

		if(cuDeviceGetName(name, 256, num) != CUDA_SUCCESS)
			continue;

		int major, minor;
		cuDeviceComputeCapability(&major, &minor, num);
		if(major < 2) {
			continue;
		}

		DeviceInfo info;

		info.type = DEVICE_CUDA;
		info.description = string(name);
		info.id = string_printf("CUDA_%d", num);
		info.num = num;

		info.advanced_shading = (major >= 2);
		info.extended_images = (major >= 3);
		info.pack_images = false;

		/* if device has a kernel timeout, assume it is used for display */
		if(cuDeviceGetAttribute(&attr, CU_DEVICE_ATTRIBUTE_KERNEL_EXEC_TIMEOUT, num) == CUDA_SUCCESS && attr == 1) {
			info.display_device = true;
			display_devices.push_back(info);
		}
		else
			devices.push_back(info);
	}

	if(!display_devices.empty())
		devices.insert(devices.end(), display_devices.begin(), display_devices.end());
}

string device_cuda_capabilities(void)
{
	CUresult result = cuInit(0);
	if(result != CUDA_SUCCESS) {
		if(result != CUDA_ERROR_NO_DEVICE) {
			return string("Error initializing CUDA: ") + cuewErrorString(result);
		}
		return "No CUDA device found\n";
	}

	int count;
	result = cuDeviceGetCount(&count);
	if(result != CUDA_SUCCESS) {
		return string("Error getting devices: ") + cuewErrorString(result);
	}

	string capabilities = "";
	for(int num = 0; num < count; num++) {
		char name[256];
		if(cuDeviceGetName(name, 256, num) != CUDA_SUCCESS) {
			continue;
		}
		capabilities += string("\t") + name + "\n";
		int value;
#define GET_ATTR(attr) \
		{ \
			if(cuDeviceGetAttribute(&value, \
			                        CU_DEVICE_ATTRIBUTE_##attr, \
			                        num) == CUDA_SUCCESS) \
			{ \
				capabilities += string_printf("\t\tCU_DEVICE_ATTRIBUTE_" #attr "\t\t\t%d\n", \
				                              value); \
			} \
		} (void)0
		/* TODO(sergey): Strip all attributes which are not useful for us
		 * or does not depend on the driver.
		 */
		GET_ATTR(MAX_THREADS_PER_BLOCK);
		GET_ATTR(MAX_BLOCK_DIM_X);
		GET_ATTR(MAX_BLOCK_DIM_Y);
		GET_ATTR(MAX_BLOCK_DIM_Z);
		GET_ATTR(MAX_GRID_DIM_X);
		GET_ATTR(MAX_GRID_DIM_Y);
		GET_ATTR(MAX_GRID_DIM_Z);
		GET_ATTR(MAX_SHARED_MEMORY_PER_BLOCK);
		GET_ATTR(SHARED_MEMORY_PER_BLOCK);
		GET_ATTR(TOTAL_CONSTANT_MEMORY);
		GET_ATTR(WARP_SIZE);
		GET_ATTR(MAX_PITCH);
		GET_ATTR(MAX_REGISTERS_PER_BLOCK);
		GET_ATTR(REGISTERS_PER_BLOCK);
		GET_ATTR(CLOCK_RATE);
		GET_ATTR(TEXTURE_ALIGNMENT);
		GET_ATTR(GPU_OVERLAP);
		GET_ATTR(MULTIPROCESSOR_COUNT);
		GET_ATTR(KERNEL_EXEC_TIMEOUT);
		GET_ATTR(INTEGRATED);
		GET_ATTR(CAN_MAP_HOST_MEMORY);
		GET_ATTR(COMPUTE_MODE);
		GET_ATTR(MAXIMUM_TEXTURE1D_WIDTH);
		GET_ATTR(MAXIMUM_TEXTURE2D_WIDTH);
		GET_ATTR(MAXIMUM_TEXTURE2D_HEIGHT);
		GET_ATTR(MAXIMUM_TEXTURE3D_WIDTH);
		GET_ATTR(MAXIMUM_TEXTURE3D_HEIGHT);
		GET_ATTR(MAXIMUM_TEXTURE3D_DEPTH);
		GET_ATTR(MAXIMUM_TEXTURE2D_LAYERED_WIDTH);
		GET_ATTR(MAXIMUM_TEXTURE2D_LAYERED_HEIGHT);
		GET_ATTR(MAXIMUM_TEXTURE2D_LAYERED_LAYERS);
		GET_ATTR(MAXIMUM_TEXTURE2D_ARRAY_WIDTH);
		GET_ATTR(MAXIMUM_TEXTURE2D_ARRAY_HEIGHT);
		GET_ATTR(MAXIMUM_TEXTURE2D_ARRAY_NUMSLICES);
		GET_ATTR(SURFACE_ALIGNMENT);
		GET_ATTR(CONCURRENT_KERNELS);
		GET_ATTR(ECC_ENABLED);
		GET_ATTR(TCC_DRIVER);
		GET_ATTR(MEMORY_CLOCK_RATE);
		GET_ATTR(GLOBAL_MEMORY_BUS_WIDTH);
		GET_ATTR(L2_CACHE_SIZE);
		GET_ATTR(MAX_THREADS_PER_MULTIPROCESSOR);
		GET_ATTR(ASYNC_ENGINE_COUNT);
		GET_ATTR(UNIFIED_ADDRESSING);
		GET_ATTR(MAXIMUM_TEXTURE1D_LAYERED_WIDTH);
		GET_ATTR(MAXIMUM_TEXTURE1D_LAYERED_LAYERS);
		GET_ATTR(CAN_TEX2D_GATHER);
		GET_ATTR(MAXIMUM_TEXTURE2D_GATHER_WIDTH);
		GET_ATTR(MAXIMUM_TEXTURE2D_GATHER_HEIGHT);
		GET_ATTR(MAXIMUM_TEXTURE3D_WIDTH_ALTERNATE);
		GET_ATTR(MAXIMUM_TEXTURE3D_HEIGHT_ALTERNATE);
		GET_ATTR(MAXIMUM_TEXTURE3D_DEPTH_ALTERNATE);
		GET_ATTR(TEXTURE_PITCH_ALIGNMENT);
		GET_ATTR(MAXIMUM_TEXTURECUBEMAP_WIDTH);
		GET_ATTR(MAXIMUM_TEXTURECUBEMAP_LAYERED_WIDTH);
		GET_ATTR(MAXIMUM_TEXTURECUBEMAP_LAYERED_LAYERS);
		GET_ATTR(MAXIMUM_SURFACE1D_WIDTH);
		GET_ATTR(MAXIMUM_SURFACE2D_WIDTH);
		GET_ATTR(MAXIMUM_SURFACE2D_HEIGHT);
		GET_ATTR(MAXIMUM_SURFACE3D_WIDTH);
		GET_ATTR(MAXIMUM_SURFACE3D_HEIGHT);
		GET_ATTR(MAXIMUM_SURFACE3D_DEPTH);
		GET_ATTR(MAXIMUM_SURFACE1D_LAYERED_WIDTH);
		GET_ATTR(MAXIMUM_SURFACE1D_LAYERED_LAYERS);
		GET_ATTR(MAXIMUM_SURFACE2D_LAYERED_WIDTH);
		GET_ATTR(MAXIMUM_SURFACE2D_LAYERED_HEIGHT);
		GET_ATTR(MAXIMUM_SURFACE2D_LAYERED_LAYERS);
		GET_ATTR(MAXIMUM_SURFACECUBEMAP_WIDTH);
		GET_ATTR(MAXIMUM_SURFACECUBEMAP_LAYERED_WIDTH);
		GET_ATTR(MAXIMUM_SURFACECUBEMAP_LAYERED_LAYERS);
		GET_ATTR(MAXIMUM_TEXTURE1D_LINEAR_WIDTH);
		GET_ATTR(MAXIMUM_TEXTURE2D_LINEAR_WIDTH);
		GET_ATTR(MAXIMUM_TEXTURE2D_LINEAR_HEIGHT);
		GET_ATTR(MAXIMUM_TEXTURE2D_LINEAR_PITCH);
		GET_ATTR(MAXIMUM_TEXTURE2D_MIPMAPPED_WIDTH);
		GET_ATTR(MAXIMUM_TEXTURE2D_MIPMAPPED_HEIGHT);
		GET_ATTR(COMPUTE_CAPABILITY_MAJOR);
		GET_ATTR(COMPUTE_CAPABILITY_MINOR);
		GET_ATTR(MAXIMUM_TEXTURE1D_MIPMAPPED_WIDTH);
		GET_ATTR(STREAM_PRIORITIES_SUPPORTED);
		GET_ATTR(GLOBAL_L1_CACHE_SUPPORTED);
		GET_ATTR(LOCAL_L1_CACHE_SUPPORTED);
		GET_ATTR(MAX_SHARED_MEMORY_PER_MULTIPROCESSOR);
		GET_ATTR(MAX_REGISTERS_PER_MULTIPROCESSOR);
		GET_ATTR(MANAGED_MEMORY);
		GET_ATTR(MULTI_GPU_BOARD);
		GET_ATTR(MULTI_GPU_BOARD_GROUP_ID);
#undef GET_ATTR
		capabilities += "\n";
	}

	return capabilities;
}

CCL_NAMESPACE_END
