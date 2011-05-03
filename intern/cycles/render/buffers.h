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

#ifndef __BUFFERS_H__
#define __BUFFERS_H__

#include "device_memory.h"

#include "util_string.h"
#include "util_thread.h"
#include "util_types.h"

CCL_NAMESPACE_BEGIN

class Device;
struct float4;

/* Render Buffers */

class RenderBuffers {
public:
	/* buffer dimensions */
	int width, height;
	/* float buffer */
	device_vector<float4> buffer;
	/* random number generator state */
	device_vector<uint> rng_state;
	/* mutex, must be locked manually by callers */
	thread_mutex mutex;

	RenderBuffers(Device *device);
	~RenderBuffers();

	void reset(Device *device, int width, int height);

protected:
	void device_free();

	Device *device;
};

/* Display Buffer
 *
 * The buffer used for drawing during render, filled by tonemapping the render
 * buffers and converting to uchar4 storage. */

class DisplayBuffer {
public:
	/* buffer dimensions */
	int width, height;
	/* dimensions for how much of the buffer is actually ready for display.
	   with progressive render we can be using only a subset of the buffer.
	   if these are zero, it means nothing can be drawn yet */
	int draw_width, draw_height;
	/* byte buffer for tonemapped result */
	device_vector<uchar4> rgba;
	/* mutex, must be locked manually by callers */
	thread_mutex mutex;

	DisplayBuffer(Device *device);
	~DisplayBuffer();

	void reset(Device *device, int width, int height);
	void write(Device *device, const string& filename);

	void draw_set(int width, int height);
	void draw(Device *device);
	bool draw_ready();

protected:
	void device_free();

	Device *device;
};

CCL_NAMESPACE_END

#endif /* __BUFFERS_H__ */

