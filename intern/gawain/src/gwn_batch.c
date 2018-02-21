
// Gawain geometry batch
//
// This code is part of the Gawain library, with modifications
// specific to integration with Blender.
//
// Copyright 2016 Mike Erwin
//
// This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of
// the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

#include "gwn_batch.h"
#include "gwn_buffer_id.h"
#include "gwn_vertex_array_id.h"
#include "gwn_primitive_private.h"
#include <stdlib.h>
#include <string.h>

// necessary functions from matrix API
extern void gpuBindMatrices(const Gwn_ShaderInterface* shaderface);

static void batch_update_program_bindings(Gwn_Batch* batch, unsigned int v_first);

static void Batch_vao_cache_clear(Gwn_Batch* batch)
	{
	if (batch->is_dynamic_vao_count)
		{
		for (int i = 0; i < batch->dynamic_vaos.count; ++i)
			{
			if (batch->dynamic_vaos.vao_ids[i])
				GWN_vao_free(batch->dynamic_vaos.vao_ids[i], batch->context);
			if (batch->dynamic_vaos.interfaces[i])
				GWN_shaderinterface_remove_batch_ref((Gwn_ShaderInterface *)batch->dynamic_vaos.interfaces[i], batch);
			}
		free(batch->dynamic_vaos.interfaces);
		free(batch->dynamic_vaos.vao_ids);
		}
	else
		{
		for (int i = 0; i < GWN_BATCH_VAO_STATIC_LEN; ++i)
			{
			if (batch->static_vaos.vao_ids[i])
				GWN_vao_free(batch->static_vaos.vao_ids[i], batch->context);
			if (batch->static_vaos.interfaces[i])
				GWN_shaderinterface_remove_batch_ref((Gwn_ShaderInterface *)batch->static_vaos.interfaces[i], batch);
			}
		}

	batch->is_dynamic_vao_count = false;
	for (int i = 0; i < GWN_BATCH_VAO_STATIC_LEN; ++i)
		{
		batch->static_vaos.vao_ids[i] = 0;
		batch->static_vaos.interfaces[i] = NULL;
		}
	}

Gwn_Batch* GWN_batch_create_ex(
        Gwn_PrimType prim_type, Gwn_VertBuf* verts, Gwn_IndexBuf* elem,
        unsigned owns_flag)
	{
	Gwn_Batch* batch = calloc(1, sizeof(Gwn_Batch));

	GWN_batch_init_ex(batch, prim_type, verts, elem, owns_flag);

	return batch;
	}

void GWN_batch_init_ex(
        Gwn_Batch* batch, Gwn_PrimType prim_type, Gwn_VertBuf* verts, Gwn_IndexBuf* elem,
        unsigned owns_flag)
	{
#if TRUST_NO_ONE
	assert(verts != NULL);
#endif

	batch->verts[0] = verts;
	for (int v = 1; v < GWN_BATCH_VBO_MAX_LEN; ++v)
		batch->verts[v] = NULL;
	batch->inst = NULL;
	batch->elem = elem;
	batch->gl_prim_type = convert_prim_type_to_gl(prim_type);
	batch->phase = GWN_BATCH_READY_TO_DRAW;
	batch->is_dynamic_vao_count = false;
	batch->owns_flag = owns_flag;
	batch->free_callback = NULL;
	}

// This will share the VBOs with the new batch
Gwn_Batch* GWN_batch_duplicate(Gwn_Batch* batch_src)
	{
	Gwn_Batch* batch = GWN_batch_create_ex(GWN_PRIM_POINTS, batch_src->verts[0], batch_src->elem, 0);

	batch->gl_prim_type = batch_src->gl_prim_type;
	for (int v = 1; v < GWN_BATCH_VBO_MAX_LEN; ++v)
		batch->verts[v] = batch_src->verts[v];

	return batch;
	}

void GWN_batch_discard(Gwn_Batch* batch)
	{
	if (batch->owns_flag & GWN_BATCH_OWNS_INDEX)
		GWN_indexbuf_discard(batch->elem);

	if (batch->owns_flag & GWN_BATCH_OWNS_INSTANCES)
		GWN_vertbuf_discard(batch->inst);

	if ((batch->owns_flag & ~GWN_BATCH_OWNS_INDEX) != 0)
		{
		for (int v = 0; v < GWN_BATCH_VBO_MAX_LEN; ++v)
			{
			if (batch->verts[v] == NULL)
				break;
			if (batch->owns_flag & (1 << v))
				GWN_vertbuf_discard(batch->verts[v]);
			}
		}

	Batch_vao_cache_clear(batch);

	if (batch->free_callback)
		batch->free_callback(batch, batch->callback_data);

	free(batch);
	}

void GWN_batch_callback_free_set(Gwn_Batch* batch, void (*callback)(Gwn_Batch*, void*), void* user_data)
	{
	batch->free_callback = callback;
	batch->callback_data = user_data;
	}

void GWN_batch_instbuf_set(Gwn_Batch* batch, Gwn_VertBuf* inst, bool own_vbo)
	{
#if TRUST_NO_ONE
	assert(inst != NULL);
#endif
	// redo the bindings
	Batch_vao_cache_clear(batch);

	if (batch->inst != NULL && (batch->owns_flag & GWN_BATCH_OWNS_INSTANCES))
		GWN_vertbuf_discard(batch->inst);

	batch->inst = inst;

	if (own_vbo)
		batch->owns_flag |= GWN_BATCH_OWNS_INSTANCES;
	else
		batch->owns_flag &= ~GWN_BATCH_OWNS_INSTANCES;
	}

int GWN_batch_vertbuf_add_ex(
        Gwn_Batch* batch, Gwn_VertBuf* verts,
        bool own_vbo)
	{
	for (unsigned v = 0; v < GWN_BATCH_VBO_MAX_LEN; ++v)
		{
		if (batch->verts[v] == NULL)
			{
#if TRUST_NO_ONE
			// for now all VertexBuffers must have same vertex_ct
			assert(verts->vertex_ct == batch->verts[0]->vertex_ct);
			// in the near future we will enable instanced attribs which have their own vertex_ct
#endif
			batch->verts[v] = verts;
			// TODO: mark dirty so we can keep attrib bindings up-to-date
			if (own_vbo)
				batch->owns_flag |= (1 << v);
			return v;
			}
		}
	
	// we only make it this far if there is no room for another Gwn_VertBuf
#if TRUST_NO_ONE
	assert(false);
#endif
	return -1;
	}

void GWN_batch_program_set(Gwn_Batch* batch, GLuint program, const Gwn_ShaderInterface* shaderface)
	{
#if TRUST_NO_ONE
	assert(glIsProgram(shaderface->program));
	assert(batch->program_in_use == 0);
#endif

	batch->vao_id = 0;
	batch->program = program;
	batch->interface = shaderface;


	// Search through cache
	if (batch->is_dynamic_vao_count)
		{
		for (int i = 0; i < batch->dynamic_vaos.count && batch->vao_id == 0; ++i)
			if (batch->dynamic_vaos.interfaces[i] == shaderface)
				batch->vao_id = batch->dynamic_vaos.vao_ids[i];
		}
	else
		{
		for (int i = 0; i < GWN_BATCH_VAO_STATIC_LEN && batch->vao_id == 0; ++i)
			if (batch->static_vaos.interfaces[i] == shaderface)
				batch->vao_id = batch->static_vaos.vao_ids[i];
		}

	if (batch->vao_id == 0)
		{
		if (batch->context == NULL)
			batch->context = GWN_context_active_get();
#if TRUST_NO_ONE && 0 // disabled until we use a separate single context for UI.
		else // Make sure you are not trying to draw this batch in another context.
			assert(batch->context == GWN_context_active_get());
#endif
		// Cache miss, time to add a new entry!
		if (!batch->is_dynamic_vao_count)
			{
			int i; // find first unused slot
			for (i = 0; i < GWN_BATCH_VAO_STATIC_LEN; ++i)
				if (batch->static_vaos.vao_ids[i] == 0)
					break;

			if (i < GWN_BATCH_VAO_STATIC_LEN)
				{
				batch->static_vaos.interfaces[i] = shaderface;
				batch->static_vaos.vao_ids[i] = batch->vao_id = GWN_vao_alloc();
				}
			else
				{
				// Not enough place switch to dynamic.
				batch->is_dynamic_vao_count = true;
				// Erase previous entries, they will be added back if drawn again.
				for (int j = 0; j < GWN_BATCH_VAO_STATIC_LEN; ++j)
					{
					GWN_shaderinterface_remove_batch_ref((Gwn_ShaderInterface*)batch->static_vaos.interfaces[j], batch);
					GWN_vao_free(batch->static_vaos.vao_ids[j], batch->context);
					}
				// Init dynamic arrays and let the branch below set the values.
				batch->dynamic_vaos.count = GWN_BATCH_VAO_DYN_ALLOC_COUNT;
				batch->dynamic_vaos.interfaces = calloc(batch->dynamic_vaos.count, sizeof(Gwn_ShaderInterface*));
				batch->dynamic_vaos.vao_ids = calloc(batch->dynamic_vaos.count, sizeof(GLuint));
				}
			}

		if (batch->is_dynamic_vao_count)
			{
			int i; // find first unused slot
			for (i = 0; i < batch->dynamic_vaos.count; ++i)
				if (batch->dynamic_vaos.vao_ids[i] == 0)
					break;

			if (i == batch->dynamic_vaos.count)
				{
				// Not enough place, realloc the array.
				i = batch->dynamic_vaos.count;
				batch->dynamic_vaos.count += GWN_BATCH_VAO_DYN_ALLOC_COUNT;
				batch->dynamic_vaos.interfaces = realloc(batch->dynamic_vaos.interfaces, sizeof(Gwn_ShaderInterface*) * batch->dynamic_vaos.count);
				batch->dynamic_vaos.vao_ids = realloc(batch->dynamic_vaos.vao_ids, sizeof(GLuint) * batch->dynamic_vaos.count);
				memset(batch->dynamic_vaos.interfaces + i, 0, sizeof(Gwn_ShaderInterface*) * GWN_BATCH_VAO_DYN_ALLOC_COUNT);
				memset(batch->dynamic_vaos.vao_ids + i, 0, sizeof(GLuint) * GWN_BATCH_VAO_DYN_ALLOC_COUNT);
				}

			batch->dynamic_vaos.interfaces[i] = shaderface;
			batch->dynamic_vaos.vao_ids[i] = batch->vao_id = GWN_vao_alloc();
			}

		GWN_shaderinterface_add_batch_ref((Gwn_ShaderInterface*)shaderface, batch);

		// We just got a fresh VAO we need to initialize it.
		glBindVertexArray(batch->vao_id);
		batch_update_program_bindings(batch, 0);
		glBindVertexArray(0);
		}

	GWN_batch_program_use_begin(batch); // hack! to make Batch_Uniform* simpler
	}

// fclem : hack !
// we need this because we don't want to unbind the shader between drawcalls
// but we still want the correct shader to be bound outside the draw manager
void GWN_batch_program_unset(Gwn_Batch* batch)
	{
	batch->program_in_use = false;
	}

void GWN_batch_remove_interface_ref(Gwn_Batch* batch, const Gwn_ShaderInterface* interface)
	{
	if (batch->is_dynamic_vao_count)
		{
		for (int i = 0; i < batch->dynamic_vaos.count; ++i)
			{
			if (batch->dynamic_vaos.interfaces[i] == interface)
				{
				GWN_vao_free(batch->dynamic_vaos.vao_ids[i], batch->context);
				batch->dynamic_vaos.vao_ids[i] = 0;
				batch->dynamic_vaos.interfaces[i] = NULL;
				break; // cannot have duplicates
				}
			}
		}
	else
		{
		int i;
		for (i = 0; i < GWN_BATCH_VAO_STATIC_LEN; ++i)
			{
			if (batch->static_vaos.interfaces[i] == interface)
				{
				GWN_vao_free(batch->static_vaos.vao_ids[i], batch->context);
				batch->static_vaos.vao_ids[i] = 0;
				batch->static_vaos.interfaces[i] = NULL;
				break; // cannot have duplicates
				}
			}
		}
	}

static void create_bindings(Gwn_VertBuf* verts, const Gwn_ShaderInterface* interface, unsigned int v_first, const bool use_instancing)
	{
	const Gwn_VertFormat* format = &verts->format;

	const unsigned attrib_ct = format->attrib_ct;
	const unsigned stride = format->stride;

	GWN_vertbuf_use(verts);

	for (unsigned a_idx = 0; a_idx < attrib_ct; ++a_idx)
		{
		const Gwn_VertAttr* a = format->attribs + a_idx;

		const GLvoid* pointer = (const GLubyte*)0 + a->offset + v_first * stride;

		for (unsigned n_idx = 0; n_idx < a->name_ct; ++n_idx)
			{
			const Gwn_ShaderInput* input = GWN_shaderinterface_attr(interface, a->name[n_idx]);

			if (input == NULL) continue;

			if (a->comp_ct == 16 || a->comp_ct == 12 || a->comp_ct == 8)
				{
#if TRUST_NO_ONE
				assert(a->fetch_mode == GWN_FETCH_FLOAT);
				assert(a->gl_comp_type == GL_FLOAT);
#endif
				for (int i = 0; i < a->comp_ct / 4; ++i)
					{
					glEnableVertexAttribArray(input->location + i);
					glVertexAttribDivisor(input->location + i, (use_instancing) ? 1 : 0);
					glVertexAttribPointer(input->location + i, 4, a->gl_comp_type, GL_FALSE, stride,
					                      (const GLubyte*)pointer + i * 16);
					}
				}
			else
				{
				glEnableVertexAttribArray(input->location);
				glVertexAttribDivisor(input->location, (use_instancing) ? 1 : 0);

				switch (a->fetch_mode)
					{
					case GWN_FETCH_FLOAT:
					case GWN_FETCH_INT_TO_FLOAT:
						glVertexAttribPointer(input->location, a->comp_ct, a->gl_comp_type, GL_FALSE, stride, pointer);
						break;
					case GWN_FETCH_INT_TO_FLOAT_UNIT:
						glVertexAttribPointer(input->location, a->comp_ct, a->gl_comp_type, GL_TRUE, stride, pointer);
						break;
					case GWN_FETCH_INT:
						glVertexAttribIPointer(input->location, a->comp_ct, a->gl_comp_type, stride, pointer);
					}
				}
			}
		}
	}

static void batch_update_program_bindings(Gwn_Batch* batch, unsigned int v_first)
	{
	for (int v = 0; v < GWN_BATCH_VBO_MAX_LEN && batch->verts[v] != NULL; ++v)
		create_bindings(batch->verts[v], batch->interface, (batch->inst) ? 0 : v_first, false);

	if (batch->inst)
		create_bindings(batch->inst, batch->interface, v_first, true);

	if (batch->elem)
		GWN_indexbuf_use(batch->elem);
	}

void GWN_batch_program_use_begin(Gwn_Batch* batch)
	{
	// NOTE: use_program & done_using_program are fragile, depend on staying in sync with
	//       the GL context's active program. use_program doesn't mark other programs as "not used".
	// TODO: make not fragile (somehow)

	if (!batch->program_in_use)
		{
		glUseProgram(batch->program);
		batch->program_in_use = true;
		}
	}

void GWN_batch_program_use_end(Gwn_Batch* batch)
	{
	if (batch->program_in_use)
		{
		glUseProgram(0);
		batch->program_in_use = false;
		}
	}

#if TRUST_NO_ONE
  #define GET_UNIFORM const Gwn_ShaderInput* uniform = GWN_shaderinterface_uniform(batch->interface, name); assert(uniform);
#else
  #define GET_UNIFORM const Gwn_ShaderInput* uniform = GWN_shaderinterface_uniform(batch->interface, name);
#endif

void GWN_batch_uniform_1i(Gwn_Batch* batch, const char* name, int value)
	{
	GET_UNIFORM
	glUniform1i(uniform->location, value);
	}

void GWN_batch_uniform_1b(Gwn_Batch* batch, const char* name, bool value)
	{
	GET_UNIFORM
	glUniform1i(uniform->location, value ? GL_TRUE : GL_FALSE);
	}

void GWN_batch_uniform_2f(Gwn_Batch* batch, const char* name, float x, float y)
	{
	GET_UNIFORM
	glUniform2f(uniform->location, x, y);
	}

void GWN_batch_uniform_3f(Gwn_Batch* batch, const char* name, float x, float y, float z)
	{
	GET_UNIFORM
	glUniform3f(uniform->location, x, y, z);
	}

void GWN_batch_uniform_4f(Gwn_Batch* batch, const char* name, float x, float y, float z, float w)
	{
	GET_UNIFORM
	glUniform4f(uniform->location, x, y, z, w);
	}

void GWN_batch_uniform_1f(Gwn_Batch* batch, const char* name, float x)
	{
	GET_UNIFORM
	glUniform1f(uniform->location, x);
	}

void GWN_batch_uniform_2fv(Gwn_Batch* batch, const char* name, const float data[2])
	{
	GET_UNIFORM
	glUniform2fv(uniform->location, 1, data);
	}

void GWN_batch_uniform_3fv(Gwn_Batch* batch, const char* name, const float data[3])
	{
	GET_UNIFORM
	glUniform3fv(uniform->location, 1, data);
	}

void GWN_batch_uniform_4fv(Gwn_Batch* batch, const char* name, const float data[4])
	{
	GET_UNIFORM
	glUniform4fv(uniform->location, 1, data);
	}

void GWN_batch_draw(Gwn_Batch* batch)
	{
#if TRUST_NO_ONE
	assert(batch->phase == GWN_BATCH_READY_TO_DRAW);
	assert(batch->verts[0]->vbo_id != 0);
#endif
	GWN_batch_program_use_begin(batch);
	gpuBindMatrices(batch->interface); // external call.

	GWN_batch_draw_range_ex(batch, 0, 0, false);

	GWN_batch_program_use_end(batch);
	}

void GWN_batch_draw_range_ex(Gwn_Batch* batch, int v_first, int v_count, bool force_instance)
	{
#if TRUST_NO_ONE
	assert(!(force_instance && (batch->inst == NULL)) || v_count > 0); // we cannot infer length if force_instance
#endif

	// If using offset drawing, use the default VAO and redo bindings.
	if (v_first != 0)
		{
		glBindVertexArray(GWN_vao_default());
		batch_update_program_bindings(batch, v_first);
		}
	else
		glBindVertexArray(batch->vao_id);

	if (force_instance || batch->inst)
		{
		// Infer length if vertex count is not given
		if (v_count == 0)
			v_count = batch->inst->vertex_ct;

		if (batch->elem)
			{
			const Gwn_IndexBuf* el = batch->elem;

#if GWN_TRACK_INDEX_RANGE
			glDrawElementsInstancedBaseVertex(batch->gl_prim_type, el->index_ct, el->gl_index_type, 0, v_count, el->base_index);
#else
			glDrawElementsInstanced(batch->gl_prim_type, el->index_ct, GL_UNSIGNED_INT, 0, v_count);
#endif
			}
		else
			glDrawArraysInstanced(batch->gl_prim_type, 0, batch->verts[0]->vertex_ct, v_count);
		}
	else
		{
		// Infer length if vertex count is not given
		if (v_count == 0)
			v_count = (batch->elem) ? batch->elem->index_ct : batch->verts[0]->vertex_ct;

		if (batch->elem)
			{
			const Gwn_IndexBuf* el = batch->elem;

#if GWN_TRACK_INDEX_RANGE
			if (el->base_index)
				glDrawRangeElementsBaseVertex(batch->gl_prim_type, el->min_index, el->max_index, v_count, el->gl_index_type, 0, el->base_index);
			else
				glDrawRangeElements(batch->gl_prim_type, el->min_index, el->max_index, v_count, el->gl_index_type, 0);
#else
			glDrawElements(batch->gl_prim_type, v_count, GL_UNSIGNED_INT, 0);
#endif
			}
		else
			glDrawArrays(batch->gl_prim_type, 0, v_count);
		}


	glBindVertexArray(0);
	}

// just draw some vertices and let shader place them where we want.
void GWN_draw_primitive(Gwn_PrimType prim_type, int v_count)
	{
	// we cannot draw without vao ... annoying ...
	glBindVertexArray(GWN_vao_default());

	GLenum type = convert_prim_type_to_gl(prim_type);
	glDrawArrays(type, 0, v_count);

	glBindVertexArray(0);
	}
