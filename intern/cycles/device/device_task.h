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
 * limitations under the License
 */

#ifndef __DEVICE_TASK_H__
#define __DEVICE_TASK_H__

#include "device_memory.h"

#include "util_function.h"
#include "util_list.h"
#include "util_task.h"

CCL_NAMESPACE_BEGIN

/* Device Task */

class Device;
class RenderBuffers;
class RenderTile;
class Tile;

class DeviceTask : public Task {
public:
	typedef enum { PATH_TRACE, TONEMAP, SHADER } Type;
	Type type;

	int x, y, w, h;
	device_ptr rgba;
	device_ptr buffer;
	int sample;
	int num_samples;
	int offset, stride;

	device_ptr shader_input;
	device_ptr shader_output;
	int shader_eval_type;
	int shader_x, shader_w;

	DeviceTask(Type type = PATH_TRACE);

	void split(list<DeviceTask>& tasks, int num);
	void split_max_size(list<DeviceTask>& tasks, int max_size);

	void update_progress(RenderTile &rtile);

	boost::function<bool(Device *device, RenderTile&)> acquire_tile;
	boost::function<void(void)> update_progress_sample;
	boost::function<void(RenderTile&)> update_tile_sample;
	boost::function<void(RenderTile&)> release_tile;
	boost::function<bool(void)> get_cancel;

	bool need_finish_queue;
	bool integrator_branched;
protected:
	double last_update_time;
};

CCL_NAMESPACE_END

#endif /* __DEVICE_TASK_H__ */

