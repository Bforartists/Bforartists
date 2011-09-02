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

#include "util_map.h"
#include "util_opencl.h"
#include "util_opengl.h"
#include "util_path.h"
#include "util_time.h"

CCL_NAMESPACE_BEGIN

#define CL_MEM_PTR(p) ((cl_mem)(unsigned long)(p))

class OpenCLDevice : public Device
{
public:
	cl_context cxContext;
	cl_command_queue cqCommandQueue;
	cl_platform_id cpPlatform;
	cl_device_id cdDevice;
	cl_program cpProgram;
	cl_kernel ckPathTraceKernel;
	cl_kernel ckFilmConvertKernel;
	cl_int ciErr;
	map<string, device_vector<uchar>*> const_mem_map;
	map<string, device_memory*> mem_map;
	device_ptr null_mem;
	bool device_initialized;

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
			fprintf(stderr, "OpenCL error (%d): %s\n", err, opencl_error_string(err));
			return true;
		}

		return false;
	}

	void opencl_assert(cl_int err)
	{
		if(err != CL_SUCCESS) {
			printf("error (%d): %s\n", err, opencl_error_string(err));
#ifndef NDEBUG
			abort();
#endif
		}
	}

	OpenCLDevice(bool background_)
	{
		background = background_;
		cpPlatform = NULL;
		cxContext = NULL;
		cqCommandQueue = NULL;
		cpProgram = NULL;
		ckPathTraceKernel = NULL;
		ckFilmConvertKernel = NULL;
		null_mem = 0;
		device_initialized = false;

		vector<cl_platform_id> platform_ids;
		cl_uint num_platforms;

		/* setup device */
		ciErr = clGetPlatformIDs(0, NULL, &num_platforms);
		if(opencl_error(ciErr))
			return;

		if(num_platforms == 0) {
			fprintf(stderr, "OpenCL: no platforms found.\n");
			return;
		}

		platform_ids.resize(num_platforms);
		ciErr = clGetPlatformIDs(num_platforms, &platform_ids[0], NULL);
		if(opencl_error(ciErr))
			return;

		cpPlatform = platform_ids[0]; /* todo: pick specified platform && device */

		ciErr = clGetDeviceIDs(cpPlatform, CL_DEVICE_TYPE_ALL, 1, &cdDevice, NULL);
		if(opencl_error(ciErr))
			return;

		cxContext = clCreateContext(0, 1, &cdDevice, NULL, NULL, &ciErr);
		if(opencl_error(ciErr))
			return;

		cqCommandQueue = clCreateCommandQueue(cxContext, cdDevice, 0, &ciErr);
		if(opencl_error(ciErr))
			return;

		null_mem = (device_ptr)clCreateBuffer(cxContext, CL_MEM_READ_ONLY, 1, NULL, &ciErr);
		device_initialized = true;
	}

	bool opencl_version_check()
	{
		char version[256];
		int major, minor, req_major = 1, req_minor = 1;

		clGetPlatformInfo(cpPlatform, CL_PLATFORM_VERSION, sizeof(version), &version, NULL);

		if(sscanf(version, "OpenCL %d.%d", &major, &minor) < 2) {
			fprintf(stderr, "OpenCL: failed to parse platform version string (%s).", version);
			return false;
		}

		if(!((major == req_major && minor >= req_minor) || (major > req_major))) {
			fprintf(stderr, "OpenCL: platform version 1.1 or later required, found %d.%d\n", major, minor);
			return false;
		}

		clGetDeviceInfo(cdDevice, CL_DEVICE_OPENCL_C_VERSION, sizeof(version), &version, NULL);

		if(sscanf(version, "OpenCL C %d.%d", &major, &minor) < 2) {
			fprintf(stderr, "OpenCL: failed to parse OpenCL C version string (%s).", version);
			return false;
		}

		if(!((major == req_major && minor >= req_minor) || (major > req_major))) {
			fprintf(stderr, "OpenCL: C version 1.1 or later required, found %d.%d\n", major, minor);
			return false;
		}

		/* we don't check CL_DEVICE_VERSION since for e.g. nvidia sm 1.3 cards this is
			1.0 even if the language features are there, just limited shared memory */

		return true;
	}

	bool load_kernels()
	{
		/* verify if device was initialized */
		if(!device_initialized)
			return false;

		/* verify we have right opencl version */
		if(!opencl_version_check())
			return false;

		/* nvidia opencl cache doesn't not work correct with includes, so force recompile */
		static double recompile_trick = 0.0;
		if(recompile_trick == 0.0)
			recompile_trick = time_dt();

		/* compile source */
		string source = string_printf("#include \"kernel.cl\" // %lf\n", recompile_trick);
		size_t source_len = source.size();
		const char *source_str = source.c_str();

		string build_options = "";

		build_options += "-I " + path_get("kernel") + " -I " + path_get("util"); /* todo: escape path */
		build_options += " -Werror -cl-fast-relaxed-math -cl-strict-aliasing";

		cpProgram = clCreateProgramWithSource(cxContext, 1, &source_str, &source_len, &ciErr);
		if(opencl_error(ciErr))
			return false;

		ciErr = clBuildProgram(cpProgram, 0, NULL, build_options.c_str(), NULL, NULL);

		if(ciErr != CL_SUCCESS) {
			char *build_log;
			size_t ret_val_size;

			clGetProgramBuildInfo(cpProgram, cdDevice, CL_PROGRAM_BUILD_LOG, 0, NULL, &ret_val_size);

			build_log = new char[ret_val_size+1];
			clGetProgramBuildInfo(cpProgram, cdDevice, CL_PROGRAM_BUILD_LOG, ret_val_size, build_log, NULL);

			build_log[ret_val_size] = '\0';
			fprintf(stderr, "OpenCL build failed:\n %s\n", build_log);

			delete[] build_log;

			return false;
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
		if(null_mem)
			clReleaseMemObject(CL_MEM_PTR(null_mem));

		map<string, device_vector<uchar>*>::iterator mt;
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

	string description()
	{
		char name[1024];

		clGetDeviceInfo(cdDevice, CL_DEVICE_NAME, sizeof(name), &name, NULL);

		return string("OpenCL ") + name;
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
	}

	void mem_copy_to(device_memory& mem)
	{
		/* this is blocking */
		size_t size = mem.memory_size();
		ciErr = clEnqueueWriteBuffer(cqCommandQueue, CL_MEM_PTR(mem.device_pointer), CL_TRUE, 0, size, (void*)mem.data_pointer, 0, NULL, NULL);
		opencl_assert(ciErr);
	}

	void mem_copy_from(device_memory& mem, size_t offset, size_t size)
	{
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
		}
	}

	void const_copy_to(const char *name, void *host, size_t size)
	{
		if(const_mem_map.find(name) == const_mem_map.end()) {
			device_vector<uchar> *data = new device_vector<uchar>();
			data->copy((uchar*)host, size);

			mem_alloc(*data, MEM_READ_ONLY);
			const_mem_map[name] = data;
		}
		else {
			device_vector<uchar> *data = const_mem_map[name];
			data->copy((uchar*)host, size);
		}

		mem_copy_to(*const_mem_map[name]);
	}

	void tex_alloc(const char *name, device_memory& mem, bool interpolation, bool periodic)
	{
		mem_alloc(mem, MEM_READ_ONLY);
		mem_copy_to(mem);
		mem_map[name] = &mem;
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

	void path_trace(DeviceTask& task)
	{
		/* cast arguments to cl types */
		cl_mem d_data = CL_MEM_PTR(const_mem_map["__data"]->device_pointer);
		cl_mem d_buffer = CL_MEM_PTR(task.buffer);
		cl_mem d_rng_state = CL_MEM_PTR(task.rng_state);
		cl_int d_x = task.x;
		cl_int d_y = task.y;
		cl_int d_w = task.w;
		cl_int d_h = task.h;
		cl_int d_pass = task.pass;

		/* pass arguments */
		int narg = 0;
		ciErr = 0;

		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_data), (void*)&d_data);
		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_buffer), (void*)&d_buffer);
		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_rng_state), (void*)&d_rng_state);

#define KERNEL_TEX(type, ttype, name) \
	ciErr |= set_kernel_arg_mem(ckPathTraceKernel, &narg, #name);
#include "kernel_textures.h"

		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_pass), (void*)&d_pass);
		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_x), (void*)&d_x);
		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_y), (void*)&d_y);
		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_w), (void*)&d_w);
		ciErr |= clSetKernelArg(ckPathTraceKernel, narg++, sizeof(d_h), (void*)&d_h);

		opencl_assert(ciErr);

		size_t local_size[2] = {8, 8};
		size_t global_size[2] = {global_size_round_up(local_size[0], d_w), global_size_round_up(local_size[1], d_h)};

		/* run kernel */
		ciErr = clEnqueueNDRangeKernel(cqCommandQueue, ckPathTraceKernel, 2, NULL, global_size, local_size, 0, NULL, NULL);
		opencl_assert(ciErr);
		opencl_assert(clFinish(cqCommandQueue));
	}

	cl_int set_kernel_arg_mem(cl_kernel kernel, int *narg, const char *name)
	{
		cl_mem ptr;
		cl_int size, err = 0;

		if(mem_map.find(name) != mem_map.end()) {
			device_memory *mem = mem_map[name];
		
			ptr = CL_MEM_PTR(mem->device_pointer);
			size = mem->data_width;
		}
		else {
			/* work around NULL not working, even though the spec says otherwise */
			ptr = CL_MEM_PTR(null_mem);
			size = 1;
		}
		
		err |= clSetKernelArg(kernel, (*narg)++, sizeof(ptr), (void*)&ptr);
		opencl_assert(err);
		err |= clSetKernelArg(kernel, (*narg)++, sizeof(size), (void*)&size);
		opencl_assert(err);

		return err;
	}

	void tonemap(DeviceTask& task)
	{
		/* cast arguments to cl types */
		cl_mem d_data = CL_MEM_PTR(const_mem_map["__data"]->device_pointer);
		cl_mem d_rgba = CL_MEM_PTR(task.rgba);
		cl_mem d_buffer = CL_MEM_PTR(task.buffer);
		cl_int d_x = task.x;
		cl_int d_y = task.y;
		cl_int d_w = task.w;
		cl_int d_h = task.h;
		cl_int d_pass = task.pass;
		cl_int d_resolution = task.resolution;

		/* pass arguments */
		int narg = 0;
		ciErr = 0;

		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_data), (void*)&d_data);
		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_rgba), (void*)&d_rgba);
		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_buffer), (void*)&d_buffer);

#define KERNEL_TEX(type, ttype, name) \
	ciErr |= set_kernel_arg_mem(ckFilmConvertKernel, &narg, #name);
#include "kernel_textures.h"

		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_pass), (void*)&d_pass);
		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_resolution), (void*)&d_resolution);
		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_x), (void*)&d_x);
		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_y), (void*)&d_y);
		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_w), (void*)&d_w);
		ciErr |= clSetKernelArg(ckFilmConvertKernel, narg++, sizeof(d_h), (void*)&d_h);

		opencl_assert(ciErr);

		size_t local_size[2] = {8, 8};
		size_t global_size[2] = {global_size_round_up(local_size[0], d_w), global_size_round_up(local_size[1], d_h)};

		/* run kernel */
		ciErr = clEnqueueNDRangeKernel(cqCommandQueue, ckFilmConvertKernel, 2, NULL, global_size, local_size, 0, NULL, NULL);
		opencl_assert(ciErr);
		opencl_assert(clFinish(cqCommandQueue));
	}

	void task_add(DeviceTask& task)
	{
		if(task.type == DeviceTask::TONEMAP)
			tonemap(task);
		else if(task.type == DeviceTask::PATH_TRACE)
			path_trace(task);
	}

	void task_wait()
	{
	}

	void task_cancel()
	{
	}
};

Device *device_opencl_create(bool background)
{
	return new OpenCLDevice(background);
}

CCL_NAMESPACE_END

#endif /* WITH_OPENCL */

