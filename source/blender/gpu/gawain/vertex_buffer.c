
// Gawain geometry batch
//
// This code is part of the Gawain library, with modifications
// specific to integration with Blender.
//
// Copyright 2016 Mike Erwin
//
// This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of
// the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

#include "vertex_buffer.h"
#include <stdlib.h>
#include <string.h>

#define KEEP_SINGLE_COPY 1

VertexBuffer* VertexBuffer_create()
	{
	VertexBuffer* verts = malloc(sizeof(VertexBuffer));
	VertexBuffer_init(verts);
	return verts;
	}

VertexBuffer* VertexBuffer_create_with_format(const VertexFormat* format)
	{
	VertexBuffer* verts = VertexBuffer_create();
	VertexFormat_copy(&verts->format, format);
	if (!format->packed)
		VertexFormat_pack(&verts->format);
	return verts;

	// this function might seem redundant, but there is potential for memory savings here...
	// TODO: implement those memory savings
	}

void VertexBuffer_init(VertexBuffer* verts)
	{
	memset(verts, 0, sizeof(VertexBuffer));
	}

void VertexBuffer_init_with_format(VertexBuffer* verts, const VertexFormat* format)
	{
	VertexBuffer_init(verts);
	VertexFormat_copy(&verts->format, format);
	if (!format->packed)
		VertexFormat_pack(&verts->format);
	}

void VertexBuffer_discard(VertexBuffer* verts)
	{
	// TODO: clean up
	}

unsigned VertexBuffer_size(const VertexBuffer* verts)
	{
	return vertex_buffer_size(&verts->format, verts->vertex_ct);
	}

void VertexBuffer_allocate_data(VertexBuffer* verts, unsigned v_ct)
	{
	VertexFormat* format = &verts->format;
	if (!format->packed)
		VertexFormat_pack(format);

	verts->vertex_ct = v_ct;

	// Data initially lives in main memory. Will be transferred to VRAM when we "prime" it.
	verts->data = malloc(VertexBuffer_size(verts));
	}

void VertexBuffer_resize_data(VertexBuffer* verts, unsigned v_ct)
	{
#if TRUST_NO_ONE
	assert(verts->vertex_ct != v_ct); // allow this?
	assert(verts->data != NULL); // has already been allocated
	assert(verts->vbo_id == 0); // has not been sent to VRAM
#endif

	verts->vertex_ct = v_ct;
	verts->data = realloc(verts->data, VertexBuffer_size(verts));
	// TODO: skip realloc if v_ct < existing vertex count
	// extra space will be reclaimed, and never sent to VRAM (see VertexBuffer_prime)
	}

void setAttrib(VertexBuffer* verts, unsigned a_idx, unsigned v_idx, const void* data)
	{
	const VertexFormat* format = &verts->format;
	const Attrib* a = format->attribs + a_idx;

#if TRUST_NO_ONE
	assert(a_idx < format->attrib_ct);
	assert(v_idx < verts->vertex_ct);
	assert(verts->data != NULL); // data must be in main mem
#endif

	memcpy((GLubyte*)verts->data + a->offset + v_idx * format->stride, data, a->sz);
	}

void fillAttrib(VertexBuffer* verts, unsigned a_idx, const void* data)
	{
	const VertexFormat* format = &verts->format;
	const Attrib* a = format->attribs + a_idx;

#if TRUST_NO_ONE
	assert(a_idx < format->attrib_ct);
#endif

	const unsigned stride = a->sz; // tightly packed input data

	fillAttribStride(verts, a_idx, stride, data);
	}

void fillAttribStride(VertexBuffer* verts, unsigned a_idx, unsigned stride, const void* data)
	{
	const VertexFormat* format = &verts->format;
	const Attrib* a = format->attribs + a_idx;

#if TRUST_NO_ONE
	assert(a_idx < format->attrib_ct);
	assert(verts->data != NULL); // data must be in main mem
#endif

	const unsigned vertex_ct = verts->vertex_ct;

	if (format->attrib_ct == 1 && stride == format->stride)
		{
		// we can copy it all at once
		memcpy(verts->data, data, vertex_ct * a->sz);
		}
	else
		{
		// we must copy it per vertex
		for (unsigned v = 0; v < vertex_ct; ++v)
			memcpy((GLubyte*)verts->data + a->offset + v * format->stride, (const GLubyte*)data + v * stride, a->sz);
		}
	}

static void VertexBuffer_prime(VertexBuffer* verts)
	{
	const VertexFormat* format = &verts->format;

	glGenBuffers(1, &verts->vbo_id);
	glBindBuffer(GL_ARRAY_BUFFER, verts->vbo_id);
	// fill with delicious data & send to GPU the first time only
	glBufferData(GL_ARRAY_BUFFER, vertex_buffer_size(format, verts->vertex_ct), verts->data, GL_STATIC_DRAW);

#if KEEP_SINGLE_COPY
	// now that GL has a copy, discard original
	free(verts->data);
	verts->data = NULL;
#endif
	}

void VertexBuffer_use(VertexBuffer* verts)
	{
	if (verts->vbo_id)
		glBindBuffer(GL_ARRAY_BUFFER, verts->vbo_id);
	else
		VertexBuffer_prime(verts);
	}
