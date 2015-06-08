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

#ifndef __DEVICE_H__
#define __DEVICE_H__

#include <stdlib.h>

#include "device_memory.h"
#include "device_task.h"

#include "util_list.h"
#include "util_stats.h"
#include "util_string.h"
#include "util_thread.h"
#include "util_types.h"
#include "util_vector.h"

CCL_NAMESPACE_BEGIN

class Progress;
class RenderTile;

/* Device Types */

enum DeviceType {
	DEVICE_NONE,
	DEVICE_CPU,
	DEVICE_OPENCL,
	DEVICE_CUDA,
	DEVICE_NETWORK,
	DEVICE_MULTI
};

class DeviceInfo {
public:
	DeviceType type;
	string description;
	string id;
	int num;
	bool display_device;
	bool advanced_shading;
	bool pack_images;
	bool extended_images; /* flag for GPU and Multi device */
	bool use_split_kernel; /* Denotes if the device is going to run cycles using split-kernel */
	vector<DeviceInfo> multi_devices;

	DeviceInfo()
	{
		type = DEVICE_CPU;
		id = "CPU";
		num = 0;
		display_device = false;
		advanced_shading = true;
		pack_images = false;
		extended_images = false;
		use_split_kernel = false;
	}
};

class DeviceRequestedFeatures {
public:
	/* Use experimental feature set. */
	bool experimental;

	/* Maximum number of closures in shader trees. */
	int max_closure;

	/* Selective nodes compilation. */

	/* Identifier of a node group up to which all the nodes needs to be
	 * compiled in. Nodes from higher group indices will be ignores.
	 */
	int max_nodes_group;

	/* Features bitfield indicating which features from the requested group
	 * will be compiled in. Nodes which corresponds to features which are not
	 * in this bitfield will be ignored even if they're in the requested group.
	 */
	int nodes_features;

	/* BVH/sampling kernel features. */
	bool use_hair;
	bool use_object_motion;
	bool use_camera_motion;

	DeviceRequestedFeatures()
	{
		/* TODO(sergey): Find more meaningful defaults. */
		experimental = false;
		max_closure = 0;
		max_nodes_group = 0;
		nodes_features = 0;
		use_hair = false;
		use_object_motion = false;
		use_camera_motion = false;
	}

	bool modified(const DeviceRequestedFeatures& requested_features)
	{
		return !(experimental == requested_features.experimental &&
		         max_closure == requested_features.max_closure &&
		         max_nodes_group == requested_features.max_nodes_group &&
		         nodes_features == requested_features.nodes_features);
	}
};

/* Device */

struct DeviceDrawParams {
	function<void(void)> bind_display_space_shader_cb;
	function<void(void)> unbind_display_space_shader_cb;
};

class Device {
protected:
	Device(DeviceInfo& info_, Stats &stats_, bool background) : background(background), vertex_buffer(0), info(info_), stats(stats_) {}

	bool background;
	string error_msg;

	/* used for real time display */
	unsigned int vertex_buffer;

public:
	virtual ~Device();

	/* info */
	DeviceInfo info;
	virtual const string& error_message() { return error_msg; }
	bool have_error() { return !error_message().empty(); }

	/* statistics */
	Stats &stats;

	/* regular memory */
	virtual void mem_alloc(device_memory& mem, MemoryType type) = 0;
	virtual void mem_copy_to(device_memory& mem) = 0;
	virtual void mem_copy_from(device_memory& mem,
		int y, int w, int h, int elem) = 0;
	virtual void mem_zero(device_memory& mem) = 0;
	virtual void mem_free(device_memory& mem) = 0;

	/* constant memory */
	virtual void const_copy_to(const char *name, void *host, size_t size) = 0;

	/* texture memory */
	virtual void tex_alloc(const char * /*name*/,
	                       device_memory& /*mem*/,
	                       InterpolationType interpolation = INTERPOLATION_NONE,
	                       bool periodic = false)
	{
		(void)interpolation;  /* Ignored. */
		(void)periodic;  /* Ignored. */
	};
	virtual void tex_free(device_memory& /*mem*/) {};

	/* pixel memory */
	virtual void pixels_alloc(device_memory& mem);
	virtual void pixels_copy_from(device_memory& mem, int y, int w, int h);
	virtual void pixels_free(device_memory& mem);

	/* open shading language, only for CPU device */
	virtual void *osl_memory() { return NULL; }

	/* load/compile kernels, must be called before adding tasks */ 
	virtual bool load_kernels(
	        const DeviceRequestedFeatures& /*requested_features*/)
	{ return true; }

	/* tasks */
	virtual int get_split_task_count(DeviceTask& task) = 0;
	virtual void task_add(DeviceTask& task) = 0;
	virtual void task_wait() = 0;
	virtual void task_cancel() = 0;
	
	/* opengl drawing */
	virtual void draw_pixels(device_memory& mem, int y, int w, int h,
		int dx, int dy, int width, int height, bool transparent,
		const DeviceDrawParams &draw_params);

#ifdef WITH_NETWORK
	/* networking */
	void server_run();
#endif

	/* multi device */
	virtual void map_tile(Device * /*sub_device*/, RenderTile& /*tile*/) {}
	virtual int device_number(Device * /*sub_device*/) { return 0; }

	/* static */
	static Device *create(DeviceInfo& info, Stats &stats, bool background = true);

	static DeviceType type_from_string(const char *name);
	static string string_from_type(DeviceType type);
	static vector<DeviceType>& available_types();
	static vector<DeviceInfo>& available_devices();
	static string device_capabilities();
};

CCL_NAMESPACE_END

#endif /* __DEVICE_H__ */

