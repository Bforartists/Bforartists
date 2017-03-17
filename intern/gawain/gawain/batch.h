
// Gawain geometry batch
//
// This code is part of the Gawain library, with modifications
// specific to integration with Blender.
//
// Copyright 2016 Mike Erwin
//
// This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of
// the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

#pragma once

#include "vertex_buffer.h"
#include "element.h"

typedef enum {
	READY_TO_FORMAT,
	READY_TO_BUILD,
	BUILDING,
	READY_TO_DRAW
} BatchPhase;

#define BATCH_MAX_VBO_CT 3

typedef struct Batch {
	// geometry
	VertexBuffer* verts[BATCH_MAX_VBO_CT]; // verts[0] is required, others can be NULL
	ElementList* elem; // NULL if element list not needed
	PrimitiveType prim_type;

	// book-keeping
	GLuint vao_id; // remembers all geometry state (vertex attrib bindings & element buffer)
	BatchPhase phase;
	bool program_dirty;
	bool program_in_use;

	// state
	GLuint program;
} Batch;

Batch* Batch_create(PrimitiveType, VertexBuffer*, ElementList*);
void Batch_init(Batch*, PrimitiveType, VertexBuffer*, ElementList*);

void Batch_discard(Batch*); // verts & elem are not discarded
void Batch_discard_all(Batch*); // including verts & elem

int Batch_add_VertexBuffer(Batch*, VertexBuffer*);

void Batch_set_program(Batch*, GLuint program);
// Entire batch draws with one shader program, but can be redrawn later with another program.
// Vertex shader's inputs must be compatible with the batch's vertex format.

void Batch_use_program(Batch*); // call before Batch_Uniform (temp hack?)
void Batch_done_using_program(Batch*);

void Batch_Uniform1i(Batch*, const char* name, int value);
void Batch_Uniform1b(Batch*, const char* name, bool value);
void Batch_Uniform1f(Batch*, const char* name, float value);
void Batch_Uniform2f(Batch*, const char* name, float x, float y);
void Batch_Uniform3f(Batch*, const char* name, float x, float y, float z);
void Batch_Uniform4f(Batch*, const char* name, float x, float y, float z, float w);
void Batch_Uniform3fv(Batch*, const char* name, const float data[3]);
void Batch_Uniform4fv(Batch*, const char* name, const float data[4]);

void Batch_draw(Batch*);


// clement : temp stuff
void Batch_draw_stupid(Batch*);
void Batch_draw_stupid_instanced(Batch*, unsigned int instance_vbo, int instance_count,
                                 int attrib_nbr, int attrib_stride, int attrib_loc[16], int attrib_size[16]);






#if 0 // future plans

// Can multiple batches share a VertexBuffer? Use ref count?


// We often need a batch with its own data, to be created and discarded together.
// WithOwn variants reduce number of system allocations.

typedef struct {
	Batch batch;
	VertexBuffer verts; // link batch.verts to this
} BatchWithOwnVertexBuffer;

typedef struct {
	Batch batch;
	ElementList elem; // link batch.elem to this
} BatchWithOwnElementList;

typedef struct {
	Batch batch;
	ElementList elem; // link batch.elem to this
	VertexBuffer verts; // link batch.verts to this
} BatchWithOwnVertexBufferAndElementList;

Batch* create_BatchWithOwnVertexBuffer(PrimitiveType, VertexFormat*, unsigned v_ct, ElementList*);
Batch* create_BatchWithOwnElementList(PrimitiveType, VertexBuffer*, unsigned prim_ct);
Batch* create_BatchWithOwnVertexBufferAndElementList(PrimitiveType, VertexFormat*, unsigned v_ct, unsigned prim_ct);
// verts: shared, own
// elem: none, shared, own
Batch* create_BatchInGeneral(PrimitiveType, VertexBufferStuff, ElementListStuff);

#endif // future plans
