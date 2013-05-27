/*
 * Copyright 2011, Blender Foundation.
 *
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
 */

#ifdef WITH_OPENCL

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "device.h"
#include "device_intern.h"

#include "buffers.h"

#include "util_foreach.h"
#include "util_map.h"
#include "util_math.h"
#include "util_md5.h"
#include "util_opencl.h"
#include "util_opengl.h"
#include "util_path.h"
#include "util_time.h"

CCL_NAMESPACE_BEGIN

#define CL_MEM_PTR(p) ((cl_mem)(uintptr_t)(p))

static cl_device_type opencl_device_type()
{
	char *device = getenv("CYCLES_OPENCL_TEST");

	if(device) {
		if(strcmp(device, "ALL") == 0)
			return CL_DEVICE_TYPE_ALL;
		else if(strcmp(device, "DEFAULT") == 0)
			return CL_DEVICE_TYPE_DEFAULT;
		else if(strcmp(device, "CPU") == 0)
			return CL_DEVICE_TYPE_CPU;
		else if(strcmp(device, "GPU") == 0)
			return CL_DEVICE_TYPE_GPU;
		else if(strcmp(device, "ACCELERATOR") == 0)
			return CL_DEVICE_TYPE_ACCELERATOR;
	}

	return CL_DEVICE_TYPE_ALL;
}

static bool opencl_kernel_use_debug()
{
	return (getenv("CYCLES_OPENCL_DEBUG") != NULL);
}

static bool opencl_kernel_use_advanced_shading(const string& platform)
{
	/* keep this in sync with kernel_types.h! */
	if(platform == "NVIDIA CUDA")
		return false;
	else if(platform == "Apple")
		return false;
	else if(platform == "AMD Accelerated Parallel Processing")
		return false;
	else if(platform == "Intel(R) OpenCL")
		return true;

	return false;
}

static string opencl_kernel_build_options(const string& platform, const string *debug_src = NULL)
{
	string build_options = " -cl-fast-relaxed-math ";

	if(platform == "NVIDIA CUDA")
		build_options += "-D__KERNEL_OPENCL_NVIDIA__ -cl-nv-maxrregcount=24 -cl-nv-verbose ";

	else if(platform == "Apple")
		build_options += "-D__KERNEL_OPENCL_APPLE__ -Wno-missing-prototypes ";

	else if(platform == "AMD Accelerated Parallel Processing")
		build_options += "-D__KERNEL_OPENCL_AMD__ ";

	else if(platform == "Intel(R) OpenCL") {
		build_options += "-D__KERNEL_OPENCL_INTEL_CPU__";

		/* options for gdb source level kernel debugging. this segfaults on linux currently */
		if(opencl_kernel_use_debug() && debug_src)
			build_options += "-g -s \"" + *debug_src + "\"";
	}

	if(opencl_kernel_use_debug())
		build_options += "-D__KERNEL_OPENCL_DEBUG__ ";

	if (opencl_kernel_use_advanced_shading(platform))
		build_options += "-D__KERNEL_OPENCL_NEED_ADVANCED_SHADING__ ";
	
	return build_options;
}

class OpenCLDevice : public Device
{
public:
	TaskPool task_pool;
	cl_context cxContext;
	cl_command_queue cqCommandQueue;
	cl_platform_id cpPlatform;
	cl_device_id cdDevice;
	cl_program cpProgram;
	cl_kernel ckPathTraceKernel;
	cl_kernel ckFilmConvertKernel;
	cl_int ciErr;

	typedef map<string, device_vector<uchar>*> ConstMemMap;
	typedef map<string, device_ptr> MemMap;

	ConstMemMap const_mem_map;
	MemMap mem_map;
	device_ptr null_mem;

	bool device_initialized;
	string platform_name;

	const char *opencl_error_string(cl_int err)
	{
		switch (err) {
			case CL_SUCCESS: return "Success!";
			case CL_DEVICE_NOT_FOUND: return "Device not found.";
			case CL_DEVICE_NOT_AVAILABLE: return "Device not available";
			case CL_COMPILER_NOT_AVAILABLE: return "Compiler not available";
			case CL_MEM_OBJECT_ALLOCATION_FAILURE: return "Memory object allocation failure";
			case CL_OUT_OF_RESOURCES: return "Out of resources";
			case CL_OUT_OF_HOST_MEMORY: return "Out of host memory";
			case CL_PROFILING_INFO_NOT_AVAILABLE: return "Profiling information not available";
			case CL_MEM_COPY_OVERLAP: return "Memory copy overlap";
			case CL_IMAGE_FORMAT_MISMATCH: return "Image format mismatch";
			case CL_IMAGE_FORMAT_NOT_SUPPORTED: return "Image format not supported";
			case CL_BUILD_PROGRAM_FAILURE: return "Program build failure";
			case CL_MAP_FAILURE: return "Map failure";
			case CL_INVALID_VALUE: return "Invalid value";
			case CL_INVALID_DEVICE_TYPE: return "Invalid device type";
			case CL_INVALID_PLATFORM: return "Invalid platform";
			case CL_INVALID_DEVICE: return "Invalid device";
			case CL_INVALID_CONTEXT: return "Invalid context";
			case CL_INVALID_QUEUE_PROPERTIES: return "Invalid queue properties";
			case CL_INVALID_COMMAND_QUEUE: return "Invalid command queue";
			case CL_INVALID_HOST_PTR: return "Invalid host pointer";
			case CL_INVALID_MEM_OBJECT: return "Invalid memory object";
			case CL_INVALID_IMAGE_FORMAT_DESCRIPTOR: return "Invalid image format descriptor";
			case CL_INVALID_IMAGE_SIZE: return "Invalid image size";
			case CL_INVALID_SAMPLER: return "Invalid sampler";
			case CL_INVALID_BINARY: return "Invalid binary";
			case CL_INVALID_BUILD_OPTIONS: return "Invalid build options";
			case CL_INVALID_PROGRAM: return "Invalid program";
			case CL_INVALID_PROGRAM_EXECUTABLE: return "Invalid program executable";
			case CL_INVALID_KERNEL_NAME: return "Invalid kernel name";
			case CL_INVALID_KERNEL_DEFINITION: return "Invalid kernel definition";
			case CL_INVALID_KERNEL: return "Invalid kernel";
			case CL_INVALID_ARG_INDEX: return "Invalid argument index";
			case CL_INVALID_ARG_VALUE: return "Invalid argument value";
			case CL_INVALID_ARG_SIZE: return "Invalid argument size";
			case CL_INVALID_KERNEL_ARGS: return "Invalid kernel arguments";
			case CL_INVALID_WORK_DIMENSION: return "Invalid work dimension";
			case CL_INVALID_WORK_GROUP_SIZE: return "Invalid work group size";
			case CL_INVALID_WORK_ITEM_SIZE: return "Invalid work item size";
			case CL_INVALID_GLOBAL_OFFSET: return "Invalid global offset";
			case CL_INVALID_EVENT_WAIT_LIST: return "Invalid event wait list";
			case CL_INVALID_EVENT: return "Invalid event";
			case CL_INVALID_OPERATION: return "Invalid operation";
			case CL_INVALID_GL_OBJECT: return "Invalid OpenGL object";
			case CL_INVALID_BUFFER_SIZE: return "Invalid buffer size";
			case CL_INVALID_MIP_LEVEL: return "Invalid mip-map level";
			default: return "Unknown";
		}
	}

	bool opencl_error(cl_int err)
	{
		if(err != CL_SUCCESS) {
			string message = string_printf("OpenCL error (%d): %s", err, opencl_error_string(err));
			if(error_msg == "")
				error_msg = message;
			fprintf(stderr, "%s\n", message.c_str());
			return true;
		}

		return false;
	}

	void opencl_error(const string& message)
	{
		if(error_msg == "")
			error_msg = message;
		fprintf(stderr, "%s\n", message.c_str());
	}

	void opencl_assert(cl_int err)
	{
		if(err != CL_SUCCESS) {
			string message = string_printf("OpenCL error (%d): %s", err, opencl_error_string(err));
			if(error_msg == "")
				error_msg = message;
			fprintf(stderr, "%s\n", message.c_str());
#ifndef NDEBUG
			abort();
#endif
		}
	}

	OpenCLDevice(DeviceInfo& info, Stats &stats, bool background_)
	  : Device(stats)
	{
		background = background_;
		cpPlatform = NULL;
		cdDevice = NULL;
		cxContext = NULL;
		cqCommandQueue = NULL;
		cpProgram = NULL;
		ckPathTraceKernel = NULL;
		ckFilmConvertKernel = NULL;
		null_mem = 0;
		device_initialized = false;

		/* setup platform */
		cl_uint num_platforms;

		ciErr = clGetPlatformIDs(0, NULL, &num_platforms);
		if(opencl_error(ciErr))
			return;

		if(num_platforms == 0) {
			opencl_error("OpenCL: no platforms found.");
			return;
		}

		vector<cl_platform_id> platforms(num_platforms, NULL);

		ciErr = clGetPlatformIDs(num_platforms, &platforms[0], NULL);
		if(opencl_error(ciErr))
			return;

		int num_base = 0;
		int total_devices = 0;

		for (int platform = 0; platform < num_platforms; platform++) {
			cl_uint num_devices;

			if(opencl_error(clGetDeviceIDs(platforms[platform], opencl_device_type(), 0, NULL, &num_devices)))
				return;

			total_devices += num_devices;

			if(info.num - num_base >= num_devices) {
				/* num doesn't refer to a device in this platform */
				num_base += num_devices;
				continue;
			}

			/* device is in this platform */
			cpPlatform = platforms[platform];

			/* get devices */
			vector<cl_device_id> device_ids(num_devices, NULL);

			if(opencl_error(clGetDeviceIDs(cpPlatform, opencl_device_type(), num_devices, &device_ids[0], NULL)))
				return;

			cdDevice = device_ids[info.num - num_base];

			char name[256];
			clGetPlatformInfo(cpPlatform, CL_PLATFORM_NAME, sizeof(name), &name, NULL);
			platform_name = name;

			break;
		}

		if(total_devices == 0) {
			opencl_error("OpenCL: no devices found.");
			return;
		}
		else if (!cdDevice) {
			opencl_error("OpenCL: specified device not found.");
			return;
		}

		/* Create context properties array to specify platform */
		const cl_context_properties context_props[] = {
			CL_CONTEXT_PLATFORM, (cl_context_properties)cpPlatform,
			0, 0
		};

		/* create context */
		cxContext = clCreateContext(context_props, 1, &cdDevice, NULL, NULL, &ciErr);
		if(opencl_error(ciErr))
			return;

		cqCommandQueue = clCreateCommandQueue(cxContext, cdDevice, 0, &ciErr);
		if(opencl_error(ciErr))
			return;

		null_mem = (device_ptr)clCreateBuffer(cxContext, CL_MEM_READ_ONLY, 1, NULL, &ciErr);
		if(opencl_error(ciErr))
			return;

		device_initialized = true;
	}

	bool opencl_version_check()
	{
		char version[256];

		int major, minor, req_major = 1, req_minor = 1;

		clGetPlatformInfo(cpPlatform, CL_PLATFORM_VERSION, sizeof(version), &version, NULL);

		if(sscanf(version, "OpenCL %d.%d", &major, &minor) < 2) {
			opencl_error(string_printf("OpenCL: failed to parse platform version string (%s).", version));
			return false;
		}

		if(!((major == req_major && minor >= req_minor) || (major > req_major))) {
			opencl_error(string_printf("OpenCL: platform version 1.1 or later required, found %d.%d", major, minor));
			return false;
		}

		clGetDeviceInfo(cdDevice, CL_DEVICE_OPENCL_C_VERSION, sizeof(version), &version, NULL);

		if(sscanf(version, "OpenCL C %d.%d", &major, &minor) < 2) {
			opencl_error(string_printf("OpenCL: failed to parse OpenCL C version string (%s).", version));
			return false;
		}

		if(!((major == req_major && minor >= req_minor) || (major > req_major))) {
			opencl_error(string_printf("OpenCL: C version 1.1 or later required, found %d.%d", major, minor));
			return false;
		}

		return true;
	}

	bool load_binary(const string& kernel_path, const string& clbin, const string *debug_src = NULL)
	{
		/* read binary into memory */
		vector<uint8_t> binary;

		if(!path_read_binary(clbin, binary)) {
			opencl_error(string_printf("OpenCL failed to read cached binary %s.", clbin.c_str()));
			return false;
		}

		/* create program */
		cl_int status;
		size_t size = binary.size();
		const uint8_t *bytes = &binary[0];

		cpProgram = clCreateProgramWithBinary(cxContext, 1, &cdDevice,
			&size, &bytes, &status, &ciErr);

		if(opencl_error(status) || opencl_error(ciErr)) {
			opencl_error(string_printf("OpenCL failed create program from cached binary %s.", clbin.c_str()));
			return false;
		}

		if(!build_kernel(kernel_path, debug_src))
			return false;

		return true;
	}

	bool save_binary(const string& clbin)
	{
		size_t size = 0;
		clGetProgramInfo(cpProgram, CL_PROGRAM_BINARY_SIZES, sizeof(size_t), &size, NULL);

		if(!size)
			return false;

		vector<uint8_t> binary(size);
		uint8_t *bytes = &binary[0];

		clGetProgramInfo(cpProgram, CL_PROGRAM_BINARIES, sizeof(uint8_t*), &bytes, NULL);

		if(!path_write_binary(clbin, binary)) {
			opencl_error(string_printf("OpenCL failed to write cached binary %s.", clbin.c_str()));
			return false;
		}

		return true;
	}

	bool build_kernel(const string& kernel_path, const string *debug_src = NULL)
	{
		string build_options = opencl_kernel_build_options(platform_name, debug_src);
	
		ciErr = clBuildProgram(cpProgram, 0, NULL, build_options.c_str(), NULL, NULL);

		/* show warnings even if build is successful */
		size_t ret_val_size = 0;

		clGetProgramBuildInfo(cpProgram, cdDevice, CL_PROGRAM_BUILD_LOG, 0, NULL, &ret_val_size);

		if(ret_val_size > 1) {
			vector<char> build_log(ret_val_size+1);
			clGetProgramBuildInfo(cpProgram, cdDevice, CL_PROGRAM_BUILD_LOG, ret_val_size, &build_log[0], NULL);

			build_log[ret_val_size] = '\0';
			fprintf(stderr, "OpenCL kernel build output:\n");
			fprintf(stderr, "%s\n", &build_log[0]);
		}

		if(ciErr != CL_SUCCESS) {
			opencl_error("OpenCL build failed: errors in console");
			return false;
		}

		return true;
	}

	bool compile_kernel(const string& kernel_path, const string& kernel_md5, const string *debug_src = NULL)
	{
		/* we compile kernels consisting of many files. unfortunately opencl
		 * kernel caches do not seem to recognize changes in included files.
		 * so we force recompile on changes by adding the md5 hash of all files */
		string source = "#include \"kernel.cl\" // " + kernel_md5 + "\n";
		source = path_source_replace_includes(source, kernel_path);

		if (debug_src)
			path_write_text(*debug_src, source);

		size_t source_len = source.size();
		const char *source_str = source.c_str();

		cpProgram = clCreateProgramWithSource(cxContext, 1, &source_str, &source_len, &ciErr);

		if(opencl_error(ciErr))
			return false;

		double starttime = time_dt();
		printf("Compiling OpenCL kernel ...\n");

		if(!build_kernel(kernel_path, debug_src))
			return false;

		printf("Kernel compilation finished in %.2lfs.\n", time_dt() - starttime);

		return true;
	}

	string device_md5_hash()
	{
		MD5Hash md5;
		char version[256], driver[256], name[256], vendor[256];

		clGetPlatformInfo(cpPlatform, CL_PLATFORM_VENDOR, sizeof(vendor), &vendor, NULL);
		clGetDeviceInfo(cdDevice, CL_DEVICE_VERSION, sizeof(version), &version, NULL);
		clGetDeviceInfo(cdDevice, CL_DEVICE_NAME, sizeof(name), &name, NULL);
		clGetDeviceInfo(cdDevice, CL_DRIVER_VERSION, sizeof(driver), &driver, NULL);

		md5.append((uint8_t*)vendor, strlen(vendor));
		md5.append((uint8_t*)version, strlen(version));
		md5.append((uint8_t*)name, strlen(name));
		md5.append((uint8_t*)driver, strlen(driver));

		string options = opencl_kernel_build_options(platform_name);
		md5.append((uint8_t*)options.c_str(), options.size());

		return md5.get_hex();
	}

	bool load_kernels(bool experimental)
	{
		/* verify if device was initialized */
		if(!device_initialized) {
			fprintf(stderr, "OpenCL: failed to initialize device.\n");
			return false;
		}

		/* verify we have right opencl version */
		if(!opencl_version_check())
			return false;

		/* md5 hash to detect changes */
		string kernel_path = path_get("kernel");
		string kernel_md5 = path_files_md5_hash(kernel_path);
		string device_md5 = device_md5_hash();

		/* path to cached binary */
		string clbin = string_printf("cycles_kernel_%s_%s.clbin", device_md5.c_str(), kernel_md5.c_str());
		clbin = path_user_get(path_join("cache", clbin));

		/* path to preprocessed source for debugging */
		string clsrc, *debug_src = NULL;
		
		if (opencl_kernel_use_debug()) {
			clsrc = string_printf("cycles_kernel_%s_%s.cl", device_md5.c_str(), kernel_md5.c_str());
			clsrc = path_user_get(path_join("cache", clsrc));
			debug_src = &clsrc;
		}

		/* if exists already, try use it */
		if(path_exists(clbin) && load_binary(kernel_path, clbin, debug_src)) {
			/* kernel loaded from binary */
		}
		else {
			/* if does not exist or loading binary failed, compile kernel */
			if(!compile_kernel(kernel_path, kernel_md5, debug_src))
				return false;

			/* save binary for reuse */
			save_binary(clbin);
		}

		/* find kernels */
		ckPathTraceKernel = clCreateKernel(cpProgram, "kernel_ocl_path_trace", &ciErr);
		if(opencl_error(ciErr))
			return false;

		ckFilmConvertKernel = clCreateKernel(cpProgram, "kernel_ocl_tonemap", &ciErr);
		if(opencl_error(ciErr))
			return false;

		return true;
	}

	~OpenCLDevice()
	{
		task_pool.stop();

		if(null_mem)
			clReleaseMemObject(CL_MEM_PTR(null_mem));

		ConstMemMap::iterator mt;
		for(mt = const_mem_map.begin(); mt != const_mem_map.end(); mt++) {
			mem_free(*(mt->second));
			delete mt->second;
		}

		if(ckPathTraceKernel)
			clReleaseKernel(ckPathTraceKernel);  
		if(ckFilmConvertKernel)
			clReleaseKernel(ckFilmConvertKernel);  
		if(cpProgram)
			clReleaseProgram(cpProgram);
		if(cqCommandQueue)
			clReleaseCommandQueue(cqCommandQueue);
		if(cxContext)
			clReleaseContext(cxContext);
	}

	void mem_alloc(device_memory& mem, MemoryType type)
	{
		size_t size = mem.memory_size();

		if(type == MEM_READ_ONLY)
			mem.device_pointer = (device_ptr)clCreateBuffer(cxContext, CL_MEM_READ_ONLY, size, NULL, &ciErr);
		else if(type == MEM_WRITE_ONLY)
			mem.device_pointer = (device_ptr)clCreateBuffer(cxContext, CL_MEM_WRITE_ONLY, size, NULL, &ciErr);
		else
			mem.device_pointer = (device_ptr)clCreateBuffer(cxContext, CL_MEM_READ_WRITE, size, NULL, &ciErr);

		opencl_assert(ciErr);

		stats.mem_alloc(size);
	}

	void mem_copy_to(device_memory& mem)
	{
		/* this is blocking */
		size_t size = mem.memory_size();
		ciErr = clEnqueueWriteBuffer(cqCommandQueue, CL_MEM_PTR(mem.device_pointer), CL_TRUE, 0, size, (void*)mem.data_pointer, 0, NULL, NULL);
		opencl_assert(ciErr);
	}

	void mem_copy_from(device_memory& mem, int y, int w, int h, int elem)
	{
		size_t offset = elem*y*w;
		size_t size = elem*w*h;

		ciErr = clEnqueueReadBuffer(cqCommandQueue, CL_MEM_PTR(mem.device_pointer), CL_TRUE, offset, size, (uchar*)mem.data_pointer + offset, 0, NULL, NULL);
		opencl_assert(ciErr);
	}

	void mem_zero(device_memory& mem)
	{
		if(mem.device_pointer) {
			memset((void*)mem.data_pointer, 0, mem.memory_size());
			mem_copy_to(mem);
		}
	}

	void mem_free(device_memory& mem)
	{
		if(mem.device_pointer) {
			ciErr = clReleaseMemObject(CL_MEM_PTR(mem.device_pointer));
			mem.device_pointer = 0;
			opencl_assert(ciErr);

			stats.mem_free(mem.memory_size());
		}
	}

	void const_copy_to(const char *name, void *host, size_t size)
	{
		ConstMemMap::iterator i = const_mem_map.find(name);

		if(i == const_mem_map.end()) {
			device_vector<uchar> *data = new device_vector<uchar>();
			data->copy((uchar*)host, size);

			mem_alloc(*data, MEM_READ_ONLY);
			i = const_mem_map.insert(ConstMemMap::value_type(name, data)).first;
		}
		else {
			device_vector<uchar> *data = i->second;
			data->copy((uchar*)host, size);
		}

		mem_copy_to(*i->second);
	}

	void tex_alloc(const char *name, device_memory& mem, bool interpolation, bool periodic)
	{
		mem_alloc(mem, MEM_READ_ONLY);
		mem_copy_to(mem);
		assert(mem_map.find(name) == mem_map.end());
		mem_map.insert(MemMap::value_type(name, mem.device_pointer));
	}

	void tex_free(device_memory& mem)
	{
		if(mem.data_pointer)
			mem_free(mem);
	}

	size_t global_size_round_up(int group_size, int global_size)
	{
		int r = global_size % group_size;
		return global_size + ((r == 0)? 0: group_size - r);
	}

	void enqueue_kernel(cl_kernel kernel, size_t w, size_t h)
	{
		size_t workgroup_size, max_work_items[3];

		clGetKernelWorkGroupInfo(kernel, cdDevice,
			CL_KERNEL_WORK_GROUP_SIZE, sizeof(size_t), &workgroup_size, NULL);
		clGetDeviceInfo(cdDevice,
			CL_DEVICE_MAX_WORK_ITEM_SIZES, sizeof(size_t)*3, max_work_items, NULL);
	
		/* try to divide evenly over 2 dimensions */
		size_t sqrt_workgroup_size = max(sqrt((double)workgroup_size), 1.0);
		size_t local_size[2] = {sqrt_workgroup_size, sqrt_workgroup_size};

		/* some implementations have max size 1 on 2nd dimension */
		if (local_size[1] > max_work_items[1]) {
			local_size[0] = workgroup_size/max_work_items[1];
			local_size[1] = max_work_items[1];
		}

		size_t global_size[2] = {global_size_round_up(local_size[0], w), global_size_round_up(local_size[1], h)};

		/* run kernel */
		ciErr = clEnqueueNDRangeKernel(cqCommandQueue, kernel, 2, NULL, global_size, local_size, 0, NULL, NULL);
		opencl_assert(ciErr);
		opencl_assert(clFinish(cqCommandQueue));
	}

	void path_trace(RenderTile& rtile, int sample)
	{
		/* cast arguments to cl types */
		cl_mem d_data = CL_MEM_PTR(const_mem_map["__data"]->device_pointer);
		cl_mem d_buffer = CL_MEM_PTR(rtile.buffer);
		cl_mem d_rng_state = CL_MEM_PTR(rtile.rng_state);
		cl_int d_x = rtile.x;
		cl_int d_y = rtile.y;
		cl_int d_w = rtile.w;
		cl_int d_h = rtile.h;
		cl_int d_sample = sample;
		cl_int d_offset = rtile.offset;
		cl_int d_stride = rtile.stride;

		/* sample arguments */
		cl_uint narg = 0;
		ciErr = 0;

		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_data), (void*)&d_data);
		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_buffer), (void*)&d_buffer);
		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_rng_state), (void*)&d_rng_state);

#define KERNEL_TEX(type, ttype, name) \
	ciErr |= set_kernel_arg_mem(ckPathTraceKernel, &narg, #name);
#include "kernel_textures.h"

		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_sample), (void*)&d_sample);
		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_x), (void*)&d_x);
		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_y), (void*)&d_y);
		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_w), (void*)&d_w);
		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_h), (void*)&d_h);
		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_offset), (void*)&d_offset);
		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_stride), (void*)&d_stride);

		opencl_assert(ciErr);

		enqueue_kernel(ckPathTraceKernel, d_w, d_h);
	}

	cl_int set_kernel_arg_mem(cl_kernel kernel, cl_uint *narg, const char *name)
	{
		cl_mem ptr;
		cl_int err = 0;

		MemMap::iterator i = mem_map.find(name);
		if(i != mem_map.end()) {
			ptr = CL_MEM_PTR(i->second);
		}
		else {
			/* work around NULL not working, even though the spec says otherwise */
			ptr = CL_MEM_PTR(null_mem);
		}
		
		err |= clSetKernelArg(kernel, (*narg)++, sizeof(ptr), (void*)&ptr);
		opencl_assert(err);

		return err;
	}

	void tonemap(DeviceTask& task, device_ptr buffer, device_ptr rgba)
	{
		/* cast arguments to cl types */
		cl_mem d_data = CL_MEM_PTR(const_mem_map["__data"]->device_pointer);
		cl_mem d_rgba = CL_MEM_PTR(rgba);
		cl_mem d_buffer = CL_MEM_PTR(buffer);
		cl_int d_x = task.x;
		cl_int d_y = task.y;
		cl_int d_w = task.w;
		cl_int d_h = task.h;
		cl_int d_sample = task.sample;
		cl_int d_offset = task.offset;
		cl_int d_stride = task.stride;

		/* sample arguments */
		cl_uint narg = 0;
		ciErr = 0;

		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_data), (void*)&d_data);
		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_rgba), (void*)&d_rgba);
		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_buffer), (void*)&d_buffer);

#define KERNEL_TEX(type, ttype, name) \
	ciErr |= set_kernel_arg_mem(ckFilmConvertKernel, &narg, #name);
#include "kernel_textures.h"

		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_sample), (void*)&d_sample);
		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_x), (void*)&d_x);
		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_y), (void*)&d_y);
		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_w), (void*)&d_w);
		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_h), (void*)&d_h);
		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_offset), (void*)&d_offset);
		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_stride), (void*)&d_stride);

		opencl_assert(ciErr);

		enqueue_kernel(ckFilmConvertKernel, d_w, d_h);
	}

	void thread_run(DeviceTask *task)
	{
		if(task->type == DeviceTask::TONEMAP) {
			tonemap(*task, task->buffer, task->rgba);
		}
		else if(task->type == DeviceTask::PATH_TRACE) {
			RenderTile tile;
			
			/* keep rendering tiles until done */
			while(task->acquire_tile(this, tile)) {
				int start_sample = tile.start_sample;
				int end_sample = tile.start_sample + tile.num_samples;

				for(int sample = start_sample; sample < end_sample; sample++) {
					if (task->get_cancel()) {
						if(task->need_finish_queue == false)
							break;
					}

					path_trace(tile, sample);

					tile.sample = sample + 1;

					task->update_progress(tile);
				}

				task->release_tile(tile);
			}
		}
	}

	class OpenCLDeviceTask : public DeviceTask {
	public:
		OpenCLDeviceTask(OpenCLDevice *device, DeviceTask& task)
		: DeviceTask(task)
		{
			run = function_bind(&OpenCLDevice::thread_run, device, this);
		}
	};

	void task_add(DeviceTask& task)
	{
		task_pool.push(new OpenCLDeviceTask(this, task));
	}

	void task_wait()
	{
		task_pool.wait_work();
	}

	void task_cancel()
	{
		task_pool.cancel();
	}
};

Device *device_opencl_create(DeviceInfo& info, Stats &stats, bool background)
{
	return new OpenCLDevice(info, stats, background);
}

void device_opencl_info(vector<DeviceInfo>& devices)
{
	vector<cl_device_id> device_ids;
	cl_uint num_devices = 0;
	vector<cl_platform_id> platform_ids;
	cl_uint num_platforms = 0;

	/* get devices */
	if(clGetPlatformIDs(0, NULL, &num_platforms) != CL_SUCCESS || num_platforms == 0)
		return;
	
	platform_ids.resize(num_platforms);

	if(clGetPlatformIDs(num_platforms, &platform_ids[0], NULL) != CL_SUCCESS)
		return;

	/* devices are numbered consecutively across platforms */
	int num_base = 0;

	for (int platform = 0; platform < num_platforms; platform++, num_base += num_devices) {
		num_devices = 0;
		if(clGetDeviceIDs(platform_ids[platform], opencl_device_type(), 0, NULL, &num_devices) != CL_SUCCESS || num_devices == 0)
			continue;

		device_ids.resize(num_devices);

		if(clGetDeviceIDs(platform_ids[platform], opencl_device_type(), num_devices, &device_ids[0], NULL) != CL_SUCCESS)
			continue;

		char pname[256];
		clGetPlatformInfo(platform_ids[platform], CL_PLATFORM_NAME, sizeof(pname), &pname, NULL);
		string platform_name = pname;

		/* add devices */
		for(int num = 0; num < num_devices; num++) {
			cl_device_id device_id = device_ids[num];
			char name[1024] = "\0";

			if(clGetDeviceInfo(device_id, CL_DEVICE_NAME, sizeof(name), &name, NULL) != CL_SUCCESS)
				continue;

			DeviceInfo info;

			info.type = DEVICE_OPENCL;
			info.description = string(name);
			info.num = num_base + num;
			info.id = string_printf("OPENCL_%d", info.num);
			/* we don't know if it's used for display, but assume it is */
			info.display_device = true;
			info.advanced_shading = opencl_kernel_use_advanced_shading(platform_name);
			info.pack_images = true;

			devices.push_back(info);
		}
	}
}

CCL_NAMESPACE_END

#endif /* WITH_OPENCL */

