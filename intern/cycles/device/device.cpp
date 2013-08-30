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

#include <stdlib.h>
#include <string.h>

#include "device.h"
#include "device_intern.h"

#include "util_cuda.h"
#include "util_debug.h"
#include "util_foreach.h"
#include "util_math.h"
#include "util_opencl.h"
#include "util_opengl.h"
#include "util_time.h"
#include "util_types.h"
#include "util_vector.h"

CCL_NAMESPACE_BEGIN

/* Device */

void Device::pixels_alloc(device_memory& mem)
{
	mem_alloc(mem, MEM_READ_WRITE);
}

void Device::pixels_copy_from(device_memory& mem, int y, int w, int h)
{
	if(mem.data_type == TYPE_HALF)
		mem_copy_from(mem, y, w, h, sizeof(half4));
	else
		mem_copy_from(mem, y, w, h, sizeof(uchar4));
}

void Device::pixels_free(device_memory& mem)
{
	mem_free(mem);
}

void Device::draw_pixels(device_memory& rgba, int y, int w, int h, int dy, int width, int height, bool transparent)
{
	pixels_copy_from(rgba, y, w, h);

	GLuint texid;
	glGenTextures(1, &texid);
	glBindTexture(GL_TEXTURE_2D, texid);
	if(rgba.data_type == TYPE_HALF)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA16F_ARB, w, h, 0, GL_RGBA, GL_HALF_FLOAT, (void*)rgba.data_pointer);
	else
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, (void*)rgba.data_pointer);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);

	glEnable(GL_TEXTURE_2D);
	
	if(transparent) {
		glEnable(GL_BLEND);
		glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA);
	}

	glColor3f(1.0f, 1.0f, 1.0f);

	glPushMatrix();
	glTranslatef(0.0f, (float)dy, 0.0f);

	glBegin(GL_QUADS);
	
	glTexCoord2f(0.0f, 0.0f);
	glVertex2f(0.0f, 0.0f);
	glTexCoord2f(1.0f, 0.0f);
	glVertex2f((float)width, 0.0f);
	glTexCoord2f(1.0f, 1.0f);
	glVertex2f((float)width, (float)height);
	glTexCoord2f(0.0f, 1.0f);
	glVertex2f(0.0f, (float)height);

	glEnd();

	glPopMatrix();

	if(transparent)
		glDisable(GL_BLEND);

	glBindTexture(GL_TEXTURE_2D, 0);
	glDisable(GL_TEXTURE_2D);
	glDeleteTextures(1, &texid);
}

Device *Device::create(DeviceInfo& info, Stats &stats, bool background)
{
	Device *device;

	switch(info.type) {
		case DEVICE_CPU:
			device = device_cpu_create(info, stats);
			break;
#ifdef WITH_CUDA
		case DEVICE_CUDA:
			if(cuLibraryInit())
				device = device_cuda_create(info, stats, background);
			else
				device = NULL;
			break;
#endif
#ifdef WITH_MULTI
		case DEVICE_MULTI:
			device = device_multi_create(info, stats, background);
			break;
#endif
#ifdef WITH_NETWORK
		case DEVICE_NETWORK:
			device = device_network_create(info, stats, "127.0.0.1");
			break;
#endif
#ifdef WITH_OPENCL
		case DEVICE_OPENCL:
			if(clLibraryInit())
				device = device_opencl_create(info, stats, background);
			else
				device = NULL;
			break;
#endif
		default:
			return NULL;
	}

	if(device)
		device->info = info;

	return device;
}

DeviceType Device::type_from_string(const char *name)
{
	if(strcmp(name, "cpu") == 0)
		return DEVICE_CPU;
	else if(strcmp(name, "cuda") == 0)
		return DEVICE_CUDA;
	else if(strcmp(name, "opencl") == 0)
		return DEVICE_OPENCL;
	else if(strcmp(name, "network") == 0)
		return DEVICE_NETWORK;
	else if(strcmp(name, "multi") == 0)
		return DEVICE_MULTI;
	
	return DEVICE_NONE;
}

string Device::string_from_type(DeviceType type)
{
	if(type == DEVICE_CPU)
		return "cpu";
	else if(type == DEVICE_CUDA)
		return "cuda";
	else if(type == DEVICE_OPENCL)
		return "opencl";
	else if(type == DEVICE_NETWORK)
		return "network";
	else if(type == DEVICE_MULTI)
		return "multi";
	
	return "";
}

vector<DeviceType>& Device::available_types()
{
	static vector<DeviceType> types;
	static bool types_init = false;

	if(!types_init) {
		types.push_back(DEVICE_CPU);

#ifdef WITH_CUDA
		if(cuLibraryInit())
			types.push_back(DEVICE_CUDA);
#endif

#ifdef WITH_OPENCL
		if(clLibraryInit())
			types.push_back(DEVICE_OPENCL);
#endif

#ifdef WITH_NETWORK
		types.push_back(DEVICE_NETWORK);
#endif
#ifdef WITH_MULTI
		types.push_back(DEVICE_MULTI);
#endif

		types_init = true;
	}

	return types;
}

vector<DeviceInfo>& Device::available_devices()
{
	static vector<DeviceInfo> devices;
	static bool devices_init = false;

	if(!devices_init) {
#ifdef WITH_CUDA
		if(cuLibraryInit())
			device_cuda_info(devices);
#endif

#ifdef WITH_OPENCL
		if(clLibraryInit())
			device_opencl_info(devices);
#endif

#ifdef WITH_MULTI
		device_multi_info(devices);
#endif

		device_cpu_info(devices);

#ifdef WITH_NETWORK
		device_network_info(devices);
#endif

		devices_init = true;
	}

	return devices;
}

CCL_NAMESPACE_END

