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

#include <stdlib.h>

#include "buffers.h"
#include "device.h"

#include "util_debug.h"
#include "util_foreach.h"
#include "util_hash.h"
#include "util_image.h"
#include "util_math.h"
#include "util_opengl.h"
#include "util_time.h"
#include "util_types.h"

CCL_NAMESPACE_BEGIN

/* Buffer Params */

BufferParams::BufferParams()
{
	width = 0;
	height = 0;

	full_x = 0;
	full_y = 0;
	full_width = 0;
	full_height = 0;

	Pass::add(PASS_COMBINED, passes);
}

void BufferParams::get_offset_stride(int& offset, int& stride)
{
	offset = -(full_x + full_y*width);
	stride = width;
}

bool BufferParams::modified(const BufferParams& params)
{
	return !(full_x == params.full_x
		&& full_y == params.full_y
		&& width == params.width
		&& height == params.height
		&& full_width == params.full_width
		&& full_height == params.full_height
		&& Pass::equals(passes, params.passes));
}

int BufferParams::get_passes_size()
{
	int size = 0;

	foreach(Pass& pass, passes)
		size += pass.components;
	
	return align_up(size, 4);
}

/* Render Buffer Task */

RenderTile::RenderTile()
{
	x = 0;
	y = 0;
	w = 0;
	h = 0;

	start_sample = 0;
	num_samples = 0;
	resolution = 0;

	offset = 0;
	stride = 0;

	buffer = 0;
	rng_state = 0;
	rgba = 0;

	buffers = NULL;
}

/* Render Buffers */

RenderBuffers::RenderBuffers(Device *device_)
{
	device = device_;
}

RenderBuffers::~RenderBuffers()
{
	device_free();
}

void RenderBuffers::device_free()
{
	if(buffer.device_pointer) {
		device->mem_free(buffer);
		buffer.clear();
	}

	if(rng_state.device_pointer) {
		device->mem_free(rng_state);
		rng_state.clear();
	}
}

void RenderBuffers::reset(Device *device, BufferParams& params_)
{
	params = params_;

	/* free existing buffers */
	device_free();
	
	/* allocate buffer */
	buffer.resize(params.width*params.height*params.get_passes_size());
	device->mem_alloc(buffer, MEM_READ_WRITE);
	device->mem_zero(buffer);

	/* allocate rng state */
	rng_state.resize(params.width, params.height);

	uint *init_state = rng_state.resize(params.width, params.height);
	int x, y, width = params.width, height = params.height;
	
	for(x = 0; x < width; x++)
		for(y = 0; y < height; y++)
			init_state[x + y*width] = hash_int_2d(params.full_x+x, params.full_y+y);

	device->mem_alloc(rng_state, MEM_READ_WRITE);
	device->mem_copy_to(rng_state);
}

bool RenderBuffers::copy_from_device()
{
	if(!buffer.device_pointer)
		return false;

	device->mem_copy_from(buffer, 0, params.width, params.height, params.get_passes_size()*sizeof(float));

	return true;
}

bool RenderBuffers::get_pass(PassType type, float exposure, int sample, int components, float *pixels)
{
	int pass_offset = 0;

	foreach(Pass& pass, params.passes) {
		if(pass.type != type) {
			pass_offset += pass.components;
			continue;
		}

		float *in = (float*)buffer.data_pointer + pass_offset;
		int pass_stride = params.get_passes_size();

		float scale = (pass.filter)? 1.0f/(float)sample: 1.0f;
		float scale_exposure = (pass.exposure)? scale*exposure: scale;

		int size = params.width*params.height;

		if(components == 1) {
			assert(pass.components == components);

			/* scalar */
			if(type == PASS_DEPTH) {
				for(int i = 0; i < size; i++, in += pass_stride, pixels++) {
					float f = *in;
					pixels[0] = (f == 0.0f)? 1e10f: f*scale_exposure;
				}
			}
			else {
				for(int i = 0; i < size; i++, in += pass_stride, pixels++) {
					float f = *in;
					pixels[0] = f*scale_exposure;
				}
			}
		}
		else if(components == 3) {
			assert(pass.components == 4);

			if(pass.divide_type != PASS_NONE) {
				/* RGB lighting passes that need to divide out color */
				pass_offset = 0;
				foreach(Pass& color_pass, params.passes) {
					if(color_pass.type == pass.divide_type)
						break;
					pass_offset += color_pass.components;
				}

				float *in_divide = (float*)buffer.data_pointer + pass_offset;

				for(int i = 0; i < size; i++, in += pass_stride, in_divide += pass_stride, pixels += 3) {
					float3 f = make_float3(in[0], in[1], in[2]);
					float3 f_divide = make_float3(in_divide[0], in_divide[1], in_divide[2]);

					f = safe_divide_color(f*exposure, f_divide);

					pixels[0] = f.x;
					pixels[1] = f.y;
					pixels[2] = f.z;
				}
			}
			else {
				/* RGB/vector */
				for(int i = 0; i < size; i++, in += pass_stride, pixels += 3) {
					float3 f = make_float3(in[0], in[1], in[2]);

					pixels[0] = f.x*scale_exposure;
					pixels[1] = f.y*scale_exposure;
					pixels[2] = f.z*scale_exposure;
				}
			}
		}
		else if(components == 4) {
			assert(pass.components == components);

			/* RGBA */
			if(type == PASS_SHADOW) {
				for(int i = 0; i < size; i++, in += pass_stride, pixels += 4) {
					float4 f = make_float4(in[0], in[1], in[2], in[3]);
					float invw = (f.w > 0.0f)? 1.0f/f.w: 1.0f;

					pixels[0] = f.x*invw;
					pixels[1] = f.y*invw;
					pixels[2] = f.z*invw;
					pixels[3] = 1.0f;
				}
			}
			else if(type == PASS_MOTION) {
				/* need to normalize by number of samples accumulated for motion */
				pass_offset = 0;
				foreach(Pass& color_pass, params.passes) {
					if(color_pass.type == PASS_MOTION_WEIGHT)
						break;
					pass_offset += color_pass.components;
				}

				float *in_weight = (float*)buffer.data_pointer + pass_offset;

				for(int i = 0; i < size; i++, in += pass_stride, in_weight += pass_stride, pixels += 4) {
					float4 f = make_float4(in[0], in[1], in[2], in[3]);
					float w = in_weight[0];
					float invw = (w > 0.0f)? 1.0f/w: 0.0f;

					pixels[0] = f.x*invw;
					pixels[1] = f.y*invw;
					pixels[2] = f.z*invw;
					pixels[3] = f.w*invw;
				}
			}
			else {
				for(int i = 0; i < size; i++, in += pass_stride, pixels += 4) {
					float4 f = make_float4(in[0], in[1], in[2], in[3]);

					pixels[0] = f.x*scale_exposure;
					pixels[1] = f.y*scale_exposure;
					pixels[2] = f.z*scale_exposure;

					/* clamp since alpha might be > 1.0 due to russian roulette */
					pixels[3] = clamp(f.w*scale, 0.0f, 1.0f);
				}
			}
		}

		return true;
	}

	return false;
}

/* Display Buffer */

DisplayBuffer::DisplayBuffer(Device *device_)
{
	device = device_;
	draw_width = 0;
	draw_height = 0;
	transparent = true; /* todo: determine from background */
}

DisplayBuffer::~DisplayBuffer()
{
	device_free();
}

void DisplayBuffer::device_free()
{
	if(rgba.device_pointer) {
		device->pixels_free(rgba);
		rgba.clear();
	}
}

void DisplayBuffer::reset(Device *device, BufferParams& params_)
{
	draw_width = 0;
	draw_height = 0;

	params = params_;

	/* free existing buffers */
	device_free();

	/* allocate display pixels */
	rgba.resize(params.width, params.height);
	device->pixels_alloc(rgba);
}

void DisplayBuffer::draw_set(int width, int height)
{
	assert(width <= params.width && height <= params.height);

	draw_width = width;
	draw_height = height;
}

void DisplayBuffer::draw(Device *device)
{
	if(draw_width != 0 && draw_height != 0) {
		glPushMatrix();
		glTranslatef(params.full_x, params.full_y, 0.0f);

		device->draw_pixels(rgba, 0, draw_width, draw_height, 0, params.width, params.height, transparent);

		glPopMatrix();
	}
}

bool DisplayBuffer::draw_ready()
{
	return (draw_width != 0 && draw_height != 0);
}

void DisplayBuffer::write(Device *device, const string& filename)
{
	int w = draw_width;
	int h = draw_height;

	if(w == 0 || h == 0)
		return;

	/* read buffer from device */
	device->pixels_copy_from(rgba, 0, w, h);

	/* write image */
	ImageOutput *out = ImageOutput::create(filename);
	ImageSpec spec(w, h, 4, TypeDesc::UINT8);
	int scanlinesize = w*4*sizeof(uchar);

	out->open(filename, spec);

	/* conversion for different top/bottom convention */
	out->write_image(TypeDesc::UINT8,
		(uchar*)rgba.data_pointer + (h-1)*scanlinesize,
		AutoStride,
		-scanlinesize,
		AutoStride);

	out->close();

	delete out;
}

CCL_NAMESPACE_END

