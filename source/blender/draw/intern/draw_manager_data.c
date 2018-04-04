/*
 * Copyright 2016, Blender Foundation.
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
 *
 * Contributor(s): Blender Institute
 *
 */

/** \file blender/draw/intern/draw_manager_data.c
 *  \ingroup draw
 */

#include "draw_manager.h"

#include "BKE_curve.h"
#include "BKE_global.h"
#include "BKE_mesh.h"
#include "BKE_object.h"
#include "BKE_paint.h"
#include "BKE_pbvh.h"

#include "DNA_curve_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meta_types.h"

#include "BLI_link_utils.h"
#include "BLI_mempool.h"

#include "intern/gpu_codegen.h"

struct Gwn_VertFormat *g_pos_format = NULL;

extern struct GPUUniformBuffer *view_ubo; /* draw_manager_exec.c */

/* -------------------------------------------------------------------- */

/** \name Uniform Buffer Object (DRW_uniformbuffer)
 * \{ */

GPUUniformBuffer *DRW_uniformbuffer_create(int size, const void *data)
{
	return GPU_uniformbuffer_create(size, data, NULL);
}

void DRW_uniformbuffer_update(GPUUniformBuffer *ubo, const void *data)
{
	GPU_uniformbuffer_update(ubo, data);
}

void DRW_uniformbuffer_free(GPUUniformBuffer *ubo)
{
	GPU_uniformbuffer_free(ubo);
}

/** \} */

/* -------------------------------------------------------------------- */

/** \name Uniforms (DRW_shgroup_uniform)
 * \{ */

static void drw_shgroup_uniform_create_ex(DRWShadingGroup *shgroup, int loc,
                                            DRWUniformType type, const void *value, int length, int arraysize)
{
	DRWUniform *uni = BLI_mempool_alloc(DST.vmempool->uniforms);
	uni->location = loc;
	uni->type = type;
	uni->value = value;
	uni->length = length;
	uni->arraysize = arraysize;

	BLI_LINKS_PREPEND(shgroup->uniforms, uni);
}

static void drw_shgroup_builtin_uniform(
        DRWShadingGroup *shgroup, int builtin, const void *value, int length, int arraysize)
{
	int loc = GPU_shader_get_builtin_uniform(shgroup->shader, builtin);

	if (loc != -1) {
		drw_shgroup_uniform_create_ex(shgroup, loc, DRW_UNIFORM_FLOAT, value, length, arraysize);
	}
}

static void drw_shgroup_uniform(DRWShadingGroup *shgroup, const char *name,
                                  DRWUniformType type, const void *value, int length, int arraysize)
{
	int location;
	if (ELEM(type, DRW_UNIFORM_BLOCK, DRW_UNIFORM_BLOCK_PERSIST)) {
		location = GPU_shader_get_uniform_block(shgroup->shader, name);
	}
	else {
		location = GPU_shader_get_uniform(shgroup->shader, name);
	}

	if (location == -1) {
		if (G.debug & G_DEBUG)
			fprintf(stderr, "Uniform '%s' not found!\n", name);
		/* Nice to enable eventually, for now eevee uses uniforms that might not exist. */
		// BLI_assert(0);
		return;
	}

	BLI_assert(arraysize > 0 && arraysize <= 16);
	BLI_assert(length >= 0 && length <= 16);

	drw_shgroup_uniform_create_ex(shgroup, location, type, value, length, arraysize);
}

void DRW_shgroup_uniform_texture(DRWShadingGroup *shgroup, const char *name, const GPUTexture *tex)
{
	BLI_assert(tex != NULL);
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_TEXTURE, tex, 0, 1);
}

/* Same as DRW_shgroup_uniform_texture but is garanteed to be bound if shader does not change between shgrp. */
void DRW_shgroup_uniform_texture_persistent(DRWShadingGroup *shgroup, const char *name, const GPUTexture *tex)
{
	BLI_assert(tex != NULL);
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_TEXTURE_PERSIST, tex, 0, 1);
}

void DRW_shgroup_uniform_block(DRWShadingGroup *shgroup, const char *name, const GPUUniformBuffer *ubo)
{
	BLI_assert(ubo != NULL);
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_BLOCK, ubo, 0, 1);
}

/* Same as DRW_shgroup_uniform_block but is garanteed to be bound if shader does not change between shgrp. */
void DRW_shgroup_uniform_block_persistent(DRWShadingGroup *shgroup, const char *name, const GPUUniformBuffer *ubo)
{
	BLI_assert(ubo != NULL);
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_BLOCK_PERSIST, ubo, 0, 1);
}

void DRW_shgroup_uniform_texture_ref(DRWShadingGroup *shgroup, const char *name, GPUTexture **tex)
{
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_TEXTURE_REF, tex, 0, 1);
}

void DRW_shgroup_uniform_bool(DRWShadingGroup *shgroup, const char *name, const int *value, int arraysize)
{
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_BOOL, value, 1, arraysize);
}

void DRW_shgroup_uniform_float(DRWShadingGroup *shgroup, const char *name, const float *value, int arraysize)
{
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_FLOAT, value, 1, arraysize);
}

void DRW_shgroup_uniform_vec2(DRWShadingGroup *shgroup, const char *name, const float *value, int arraysize)
{
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_FLOAT, value, 2, arraysize);
}

void DRW_shgroup_uniform_vec3(DRWShadingGroup *shgroup, const char *name, const float *value, int arraysize)
{
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_FLOAT, value, 3, arraysize);
}

void DRW_shgroup_uniform_vec4(DRWShadingGroup *shgroup, const char *name, const float *value, int arraysize)
{
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_FLOAT, value, 4, arraysize);
}

void DRW_shgroup_uniform_short_to_int(DRWShadingGroup *shgroup, const char *name, const short *value, int arraysize)
{
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_SHORT_TO_INT, value, 1, arraysize);
}

void DRW_shgroup_uniform_short_to_float(DRWShadingGroup *shgroup, const char *name, const short *value, int arraysize)
{
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_SHORT_TO_FLOAT, value, 1, arraysize);
}

void DRW_shgroup_uniform_int(DRWShadingGroup *shgroup, const char *name, const int *value, int arraysize)
{
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_INT, value, 1, arraysize);
}

void DRW_shgroup_uniform_ivec2(DRWShadingGroup *shgroup, const char *name, const int *value, int arraysize)
{
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_INT, value, 2, arraysize);
}

void DRW_shgroup_uniform_ivec3(DRWShadingGroup *shgroup, const char *name, const int *value, int arraysize)
{
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_INT, value, 3, arraysize);
}

void DRW_shgroup_uniform_mat3(DRWShadingGroup *shgroup, const char *name, const float *value)
{
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_FLOAT, value, 9, 1);
}

void DRW_shgroup_uniform_mat4(DRWShadingGroup *shgroup, const char *name, const float *value)
{
	drw_shgroup_uniform(shgroup, name, DRW_UNIFORM_FLOAT, value, 16, 1);
}

/** \} */

/* -------------------------------------------------------------------- */

/** \name Draw Call (DRW_calls)
 * \{ */

static void drw_call_calc_orco(Object *ob, float (*r_orcofacs)[3])
{
	ID *ob_data = (ob) ? ob->data : NULL;
	float *texcoloc = NULL;
	float *texcosize = NULL;
	if (ob_data != NULL) {
		switch (GS(ob_data->name)) {
			case ID_ME:
				BKE_mesh_texspace_get_reference((Mesh *)ob_data, NULL, &texcoloc, NULL, &texcosize);
				break;
			case ID_CU:
			{
				Curve *cu = (Curve *)ob_data;
				if (cu->bb == NULL || (cu->bb->flag & BOUNDBOX_DIRTY)) {
					BKE_curve_texspace_calc(cu);
				}
				texcoloc = cu->loc;
				texcosize = cu->size;
				break;
			}
			case ID_MB:
			{
				MetaBall *mb = (MetaBall *)ob_data;
				texcoloc = mb->loc;
				texcosize = mb->size;
				break;
			}
			default:
				break;
		}
	}

	if ((texcoloc != NULL) && (texcosize != NULL)) {
		mul_v3_v3fl(r_orcofacs[1], texcosize, 2.0f);
		invert_v3(r_orcofacs[1]);
		sub_v3_v3v3(r_orcofacs[0], texcoloc, texcosize);
		negate_v3(r_orcofacs[0]);
		mul_v3_v3(r_orcofacs[0], r_orcofacs[1]); /* result in a nice MADD in the shader */
	}
	else {
		copy_v3_fl(r_orcofacs[0], 0.0f);
		copy_v3_fl(r_orcofacs[1], 1.0f);
	}
}

static DRWCallState *drw_call_state_create(DRWShadingGroup *shgroup, float (*obmat)[4], Object *ob)
{
	DRWCallState *state = BLI_mempool_alloc(DST.vmempool->states);
	state->flag = 0;
	state->cache_id = 0;
	state->matflag = shgroup->matflag;

	/* Matrices */
	if (obmat != NULL) {
		copy_m4_m4(state->model, obmat);

		if (is_negative_m4(state->model)) {
			state->flag |= DRW_CALL_NEGSCALE;
		}
	}
	else {
		unit_m4(state->model);
	}

	if (ob != NULL) {
		float corner[3];
		BoundBox *bbox = BKE_object_boundbox_get(ob);
		/* Get BoundSphere center and radius from the BoundBox. */
		mid_v3_v3v3(state->bsphere.center, bbox->vec[0], bbox->vec[6]);
		mul_v3_m4v3(corner, obmat, bbox->vec[0]);
		mul_m4_v3(obmat, state->bsphere.center);
		state->bsphere.radius = len_v3v3(state->bsphere.center, corner);
	}
	else {
		/* Bypass test. */
		state->bsphere.radius = -1.0f;
	}

	/* Orco factors: We compute this at creation to not have to save the *ob_data */
	if ((state->matflag & DRW_CALL_ORCOTEXFAC) != 0) {
		drw_call_calc_orco(ob, state->orcotexfac);
		state->matflag &= ~DRW_CALL_ORCOTEXFAC;
	}

	return state;
}

static DRWCallState *drw_call_state_object(DRWShadingGroup *shgroup, float (*obmat)[4], Object *ob)
{
	if (DST.ob_state == NULL) {
		DST.ob_state = drw_call_state_create(shgroup, obmat, ob);
	}
	else {
		/* If the DRWCallState is reused, add necessary matrices. */
		DST.ob_state->matflag |= shgroup->matflag;
	}

	return DST.ob_state;
}

void DRW_shgroup_call_add(DRWShadingGroup *shgroup, Gwn_Batch *geom, float (*obmat)[4])
{
	BLI_assert(geom != NULL);
	BLI_assert(shgroup->type == DRW_SHG_NORMAL);

	DRWCall *call = BLI_mempool_alloc(DST.vmempool->calls);
	call->state = drw_call_state_create(shgroup, obmat, NULL);
	call->type = DRW_CALL_SINGLE;
	call->single.geometry = geom;
#ifdef USE_GPU_SELECT
	call->select_id = DST.select_id;
#endif

	BLI_LINKS_APPEND(&shgroup->calls, call);
}

/* These calls can be culled and are optimized for redraw */
void DRW_shgroup_call_object_add(DRWShadingGroup *shgroup, Gwn_Batch *geom, Object *ob)
{
	BLI_assert(geom != NULL);
	BLI_assert(shgroup->type == DRW_SHG_NORMAL);

	DRWCall *call = BLI_mempool_alloc(DST.vmempool->calls);
	call->state = drw_call_state_object(shgroup, ob->obmat, ob);
	call->type = DRW_CALL_SINGLE;
	call->single.geometry = geom;
#ifdef USE_GPU_SELECT
	call->select_id = DST.select_id;
#endif

	BLI_LINKS_APPEND(&shgroup->calls, call);
}

void DRW_shgroup_call_instances_add(DRWShadingGroup *shgroup, Gwn_Batch *geom, float (*obmat)[4], unsigned int *count)
{
	BLI_assert(geom != NULL);
	BLI_assert(shgroup->type == DRW_SHG_NORMAL);

	DRWCall *call = BLI_mempool_alloc(DST.vmempool->calls);
	call->state = drw_call_state_create(shgroup, obmat, NULL);
	call->type = DRW_CALL_INSTANCES;
	call->instances.geometry = geom;
	call->instances.count = count;
#ifdef USE_GPU_SELECT
	call->select_id = DST.select_id;
#endif

	BLI_LINKS_APPEND(&shgroup->calls, call);
}

/* These calls can be culled and are optimized for redraw */
void DRW_shgroup_call_object_instances_add(DRWShadingGroup *shgroup, Gwn_Batch *geom, Object *ob, unsigned int *count)
{
	BLI_assert(geom != NULL);
	BLI_assert(shgroup->type == DRW_SHG_NORMAL);

	DRWCall *call = BLI_mempool_alloc(DST.vmempool->calls);
	call->state = drw_call_state_object(shgroup, ob->obmat, ob);
	call->type = DRW_CALL_INSTANCES;
	call->instances.geometry = geom;
	call->instances.count = count;
#ifdef USE_GPU_SELECT
	call->select_id = DST.select_id;
#endif

	BLI_LINKS_APPEND(&shgroup->calls, call);
}

void DRW_shgroup_call_generate_add(
        DRWShadingGroup *shgroup,
        DRWCallGenerateFn *geometry_fn, void *user_data,
        float (*obmat)[4])
{
	BLI_assert(geometry_fn != NULL);
	BLI_assert(shgroup->type == DRW_SHG_NORMAL);

	DRWCall *call = BLI_mempool_alloc(DST.vmempool->calls);
	call->state = drw_call_state_create(shgroup, obmat, NULL);
	call->type = DRW_CALL_GENERATE;
	call->generate.geometry_fn = geometry_fn;
	call->generate.user_data = user_data;
#ifdef USE_GPU_SELECT
	call->select_id = DST.select_id;
#endif

	BLI_LINKS_APPEND(&shgroup->calls, call);
}

static void sculpt_draw_cb(
        DRWShadingGroup *shgroup,
        void (*draw_fn)(DRWShadingGroup *shgroup, Gwn_Batch *geom),
        void *user_data)
{
	Object *ob = user_data;
	PBVH *pbvh = ob->sculpt->pbvh;

	if (pbvh) {
		BKE_pbvh_draw_cb(
		        pbvh, NULL, NULL, false,
		        (void (*)(void *, Gwn_Batch *))draw_fn, shgroup);
	}
}

void DRW_shgroup_call_sculpt_add(DRWShadingGroup *shgroup, Object *ob, float (*obmat)[4])
{
	DRW_shgroup_call_generate_add(shgroup, sculpt_draw_cb, ob, obmat);
}

void DRW_shgroup_call_dynamic_add_array(DRWShadingGroup *shgroup, const void *attr[], unsigned int attr_len)
{
#ifdef USE_GPU_SELECT
	if (G.f & G_PICKSEL) {
		if (shgroup->inst_selectid == NULL) {
			shgroup->inst_selectid = DRW_instance_data_request(DST.idatalist, 1, 128);
		}

		int *select_id = DRW_instance_data_next(shgroup->inst_selectid);
		*select_id = DST.select_id;
	}
#endif

	BLI_assert(attr_len == shgroup->attribs_count);
	UNUSED_VARS_NDEBUG(attr_len);

	for (int i = 0; i < attr_len; ++i) {
		if (shgroup->instance_count == shgroup->instance_vbo->vertex_ct) {
			GWN_vertbuf_data_resize(shgroup->instance_vbo, shgroup->instance_count + 32);
		}
		GWN_vertbuf_attr_set(shgroup->instance_vbo, i, shgroup->instance_count, attr[i]);
	}

	shgroup->instance_count += 1;
}

/** \} */

/* -------------------------------------------------------------------- */

/** \name Shading Groups (DRW_shgroup)
 * \{ */

static void drw_shgroup_init(DRWShadingGroup *shgroup, GPUShader *shader)
{
	shgroup->instance_geom = NULL;
	shgroup->instance_vbo = NULL;
	shgroup->instance_count = 0;
	shgroup->uniforms = NULL;
#ifdef USE_GPU_SELECT
	shgroup->inst_selectid = NULL;
	shgroup->override_selectid = -1;
#endif
#ifndef NDEBUG
	shgroup->attribs_count = 0;
#endif

	int view_ubo_location = GPU_shader_get_uniform_block(shader, "viewBlock");

	if (view_ubo_location != -1) {
		drw_shgroup_uniform_create_ex(shgroup, view_ubo_location, DRW_UNIFORM_BLOCK_PERSIST, view_ubo, 0, 1);
	}
	else {
		/* Only here to support builtin shaders. This should not be used by engines. */
		drw_shgroup_builtin_uniform(shgroup, GWN_UNIFORM_VIEW, DST.view_data.matstate.mat[DRW_MAT_VIEW], 16, 1);
		drw_shgroup_builtin_uniform(shgroup, GWN_UNIFORM_VIEW_INV, DST.view_data.matstate.mat[DRW_MAT_VIEWINV], 16, 1);
		drw_shgroup_builtin_uniform(shgroup, GWN_UNIFORM_VIEWPROJECTION, DST.view_data.matstate.mat[DRW_MAT_PERS], 16, 1);
		drw_shgroup_builtin_uniform(shgroup, GWN_UNIFORM_VIEWPROJECTION_INV, DST.view_data.matstate.mat[DRW_MAT_PERSINV], 16, 1);
		drw_shgroup_builtin_uniform(shgroup, GWN_UNIFORM_PROJECTION, DST.view_data.matstate.mat[DRW_MAT_WIN], 16, 1);
		drw_shgroup_builtin_uniform(shgroup, GWN_UNIFORM_PROJECTION_INV, DST.view_data.matstate.mat[DRW_MAT_WININV], 16, 1);
		drw_shgroup_builtin_uniform(shgroup, GWN_UNIFORM_CAMERATEXCO, DST.view_data.viewcamtexcofac, 3, 2);
	}

	shgroup->model = GPU_shader_get_builtin_uniform(shader, GWN_UNIFORM_MODEL);
	shgroup->modelinverse = GPU_shader_get_builtin_uniform(shader, GWN_UNIFORM_MODEL_INV);
	shgroup->modelview = GPU_shader_get_builtin_uniform(shader, GWN_UNIFORM_MODELVIEW);
	shgroup->modelviewinverse = GPU_shader_get_builtin_uniform(shader, GWN_UNIFORM_MODELVIEW_INV);
	shgroup->modelviewprojection = GPU_shader_get_builtin_uniform(shader, GWN_UNIFORM_MVP);
	shgroup->normalview = GPU_shader_get_builtin_uniform(shader, GWN_UNIFORM_NORMAL);
	shgroup->normalworld = GPU_shader_get_builtin_uniform(shader, GWN_UNIFORM_WORLDNORMAL);
	shgroup->orcotexfac = GPU_shader_get_builtin_uniform(shader, GWN_UNIFORM_ORCO);
	shgroup->eye = GPU_shader_get_builtin_uniform(shader, GWN_UNIFORM_EYE);

	shgroup->matflag = 0;
	if (shgroup->modelinverse > -1)
		shgroup->matflag |= DRW_CALL_MODELINVERSE;
	if (shgroup->modelview > -1)
		shgroup->matflag |= DRW_CALL_MODELVIEW;
	if (shgroup->modelviewinverse > -1)
		shgroup->matflag |= DRW_CALL_MODELVIEWINVERSE;
	if (shgroup->modelviewprojection > -1)
		shgroup->matflag |= DRW_CALL_MODELVIEWPROJECTION;
	if (shgroup->normalview > -1)
		shgroup->matflag |= DRW_CALL_NORMALVIEW;
	if (shgroup->normalworld > -1)
		shgroup->matflag |= DRW_CALL_NORMALWORLD;
	if (shgroup->orcotexfac > -1)
		shgroup->matflag |= DRW_CALL_ORCOTEXFAC;
	if (shgroup->eye > -1)
		shgroup->matflag |= DRW_CALL_EYEVEC;
}

static void drw_shgroup_instance_init(
        DRWShadingGroup *shgroup, GPUShader *shader, Gwn_Batch *batch, Gwn_VertFormat *format)
{
	BLI_assert(shgroup->type == DRW_SHG_INSTANCE);
	BLI_assert(batch != NULL);
	BLI_assert(format != NULL);

	drw_shgroup_init(shgroup, shader);

	shgroup->instance_geom = batch;
#ifndef NDEBUG
	shgroup->attribs_count = format->attrib_ct;
#endif

	DRW_instancing_buffer_request(DST.idatalist, format, batch, shgroup,
	                              &shgroup->instance_geom, &shgroup->instance_vbo);
}

static void drw_shgroup_batching_init(
        DRWShadingGroup *shgroup, GPUShader *shader, Gwn_VertFormat *format)
{
	drw_shgroup_init(shgroup, shader);

#ifndef NDEBUG
	shgroup->attribs_count = (format != NULL) ? format->attrib_ct : 0;
#endif
	BLI_assert(format != NULL);

	Gwn_PrimType type;
	switch (shgroup->type) {
		case DRW_SHG_POINT_BATCH: type = GWN_PRIM_POINTS; break;
		case DRW_SHG_LINE_BATCH: type = GWN_PRIM_LINES; break;
		case DRW_SHG_TRIANGLE_BATCH: type = GWN_PRIM_TRIS; break;
		default: type = GWN_PRIM_NONE; BLI_assert(0); break;
	}

	DRW_batching_buffer_request(DST.idatalist, format, type, shgroup,
	                            &shgroup->batch_geom, &shgroup->batch_vbo);
}

static DRWShadingGroup *drw_shgroup_create_ex(struct GPUShader *shader, DRWPass *pass)
{
	DRWShadingGroup *shgroup = BLI_mempool_alloc(DST.vmempool->shgroups);

	BLI_LINKS_APPEND(&pass->shgroups, shgroup);

	shgroup->type = DRW_SHG_NORMAL;
	shgroup->shader = shader;
	shgroup->state_extra = 0;
	shgroup->state_extra_disable = ~0x0;
	shgroup->stencil_mask = 0;
	shgroup->calls.first = NULL;
	shgroup->calls.last = NULL;
#if 0 /* All the same in the union! */
	shgroup->batch_geom = NULL;
	shgroup->batch_vbo = NULL;

	shgroup->instance_geom = NULL;
	shgroup->instance_vbo = NULL;
#endif

#ifdef USE_GPU_SELECT
	shgroup->pass_parent = pass;
#endif

	return shgroup;
}

static DRWShadingGroup *drw_shgroup_material_create_ex(GPUPass *gpupass, DRWPass *pass)
{
	if (!gpupass) {
		/* Shader compilation error */
		return NULL;
	}

	DRWShadingGroup *grp = drw_shgroup_create_ex(GPU_pass_shader(gpupass), pass);
	return grp;
}

static DRWShadingGroup *drw_shgroup_material_inputs(DRWShadingGroup *grp, struct GPUMaterial *material)
{
	/* TODO : Ideally we should not convert. But since the whole codegen
	 * is relying on GPUPass we keep it as is for now. */

	ListBase *inputs = GPU_material_get_inputs(material);

	/* Converting dynamic GPUInput to DRWUniform */
	for (GPUInput *input = inputs->first; input; input = input->next) {
		/* Textures */
		if (input->ima) {
			double time = 0.0; /* TODO make time variable */
			GPUTexture *tex = GPU_texture_from_blender(
			        input->ima, input->iuser, input->textarget, input->image_isdata, time, 1);

			if (input->bindtex) {
				DRW_shgroup_uniform_texture(grp, input->shadername, tex);
			}
		}
		/* Color Ramps */
		else if (input->tex) {
			DRW_shgroup_uniform_texture(grp, input->shadername, input->tex);
		}
		/* Floats */
		else {
			switch (input->type) {
				case GPU_FLOAT:
				case GPU_VEC2:
				case GPU_VEC3:
				case GPU_VEC4:
					/* Should already be in the material ubo. */
					break;
				case GPU_MAT3:
					DRW_shgroup_uniform_mat3(grp, input->shadername, (float *)input->dynamicvec);
					break;
				case GPU_MAT4:
					DRW_shgroup_uniform_mat4(grp, input->shadername, (float *)input->dynamicvec);
					break;
				default:
					break;
			}
		}
	}

	GPUUniformBuffer *ubo = GPU_material_get_uniform_buffer(material);
	if (ubo != NULL) {
		DRW_shgroup_uniform_block(grp, GPU_UBO_BLOCK_NAME, ubo);
	}

	return grp;
}

Gwn_VertFormat *DRW_shgroup_instance_format_array(const DRWInstanceAttribFormat attribs[], int arraysize)
{
	Gwn_VertFormat *format = MEM_callocN(sizeof(Gwn_VertFormat), "Gwn_VertFormat");

	for (int i = 0; i < arraysize; ++i) {
		GWN_vertformat_attr_add(format, attribs[i].name,
		                        (attribs[i].type == DRW_ATTRIB_INT) ? GWN_COMP_I32 : GWN_COMP_F32,
		                        attribs[i].components,
		                        (attribs[i].type == DRW_ATTRIB_INT) ? GWN_FETCH_INT : GWN_FETCH_FLOAT);
	}
	return format;
}

DRWShadingGroup *DRW_shgroup_material_create(
        struct GPUMaterial *material, DRWPass *pass)
{
	GPUPass *gpupass = GPU_material_get_pass(material);
	DRWShadingGroup *shgroup = drw_shgroup_material_create_ex(gpupass, pass);

	if (shgroup) {
		drw_shgroup_init(shgroup, GPU_pass_shader(gpupass));
		drw_shgroup_material_inputs(shgroup, material);
	}

	return shgroup;
}

DRWShadingGroup *DRW_shgroup_material_instance_create(
        struct GPUMaterial *material, DRWPass *pass, Gwn_Batch *geom, Object *ob, Gwn_VertFormat *format)
{
	GPUPass *gpupass = GPU_material_get_pass(material);
	DRWShadingGroup *shgroup = drw_shgroup_material_create_ex(gpupass, pass);

	if (shgroup) {
		shgroup->type = DRW_SHG_INSTANCE;
		shgroup->instance_geom = geom;
		drw_call_calc_orco(ob, shgroup->instance_orcofac);
		drw_shgroup_instance_init(shgroup, GPU_pass_shader(gpupass), geom, format);
		drw_shgroup_material_inputs(shgroup, material);
	}

	return shgroup;
}

DRWShadingGroup *DRW_shgroup_material_empty_tri_batch_create(
        struct GPUMaterial *material, DRWPass *pass, int tri_count)
{
#ifdef USE_GPU_SELECT
	BLI_assert((G.f & G_PICKSEL) == 0);
#endif
	GPUPass *gpupass = GPU_material_get_pass(material);
	DRWShadingGroup *shgroup = drw_shgroup_material_create_ex(gpupass, pass);

	if (shgroup) {
		/* Calling drw_shgroup_init will cause it to call GWN_draw_primitive(). */
		drw_shgroup_init(shgroup, GPU_pass_shader(gpupass));
		shgroup->type = DRW_SHG_TRIANGLE_BATCH;
		shgroup->instance_count = tri_count * 3;
		drw_shgroup_material_inputs(shgroup, material);
	}

	return shgroup;
}

DRWShadingGroup *DRW_shgroup_create(struct GPUShader *shader, DRWPass *pass)
{
	DRWShadingGroup *shgroup = drw_shgroup_create_ex(shader, pass);
	drw_shgroup_init(shgroup, shader);
	return shgroup;
}

DRWShadingGroup *DRW_shgroup_instance_create(
        struct GPUShader *shader, DRWPass *pass, Gwn_Batch *geom, Gwn_VertFormat *format)
{
	DRWShadingGroup *shgroup = drw_shgroup_create_ex(shader, pass);
	shgroup->type = DRW_SHG_INSTANCE;
	shgroup->instance_geom = geom;
	drw_call_calc_orco(NULL, shgroup->instance_orcofac);
	drw_shgroup_instance_init(shgroup, shader, geom, format);

	return shgroup;
}

DRWShadingGroup *DRW_shgroup_point_batch_create(struct GPUShader *shader, DRWPass *pass)
{
	DRW_shgroup_instance_format(g_pos_format, {{"pos", DRW_ATTRIB_FLOAT, 3}});

	DRWShadingGroup *shgroup = drw_shgroup_create_ex(shader, pass);
	shgroup->type = DRW_SHG_POINT_BATCH;

	drw_shgroup_batching_init(shgroup, shader, g_pos_format);

	return shgroup;
}

DRWShadingGroup *DRW_shgroup_line_batch_create(struct GPUShader *shader, DRWPass *pass)
{
	DRW_shgroup_instance_format(g_pos_format, {{"pos", DRW_ATTRIB_FLOAT, 3}});

	DRWShadingGroup *shgroup = drw_shgroup_create_ex(shader, pass);
	shgroup->type = DRW_SHG_LINE_BATCH;

	drw_shgroup_batching_init(shgroup, shader, g_pos_format);

	return shgroup;
}

/* Very special batch. Use this if you position
 * your vertices with the vertex shader
 * and dont need any VBO attrib */
DRWShadingGroup *DRW_shgroup_empty_tri_batch_create(struct GPUShader *shader, DRWPass *pass, int tri_count)
{
#ifdef USE_GPU_SELECT
	BLI_assert((G.f & G_PICKSEL) == 0);
#endif
	DRWShadingGroup *shgroup = drw_shgroup_create_ex(shader, pass);

	/* Calling drw_shgroup_init will cause it to call GWN_draw_primitive(). */
	drw_shgroup_init(shgroup, shader);

	shgroup->type = DRW_SHG_TRIANGLE_BATCH;
	shgroup->instance_count = tri_count * 3;

	return shgroup;
}

/* Specify an external batch instead of adding each attrib one by one. */
void DRW_shgroup_instance_batch(DRWShadingGroup *shgroup, struct Gwn_Batch *batch)
{
	BLI_assert(shgroup->type == DRW_SHG_INSTANCE);
	BLI_assert(shgroup->instance_count == 0);
	/* You cannot use external instancing batch without a dummy format. */
	BLI_assert(shgroup->attribs_count != 0);

	shgroup->type = DRW_SHG_INSTANCE_EXTERNAL;
	drw_call_calc_orco(NULL, shgroup->instance_orcofac);
	/* PERF : This destroys the vaos cache so better check if it's necessary. */
	/* Note: This WILL break if batch->verts[0] is destroyed and reallocated
	 * at the same adress. Bindings/VAOs would remain obsolete. */
	//if (shgroup->instancing_geom->inst != batch->verts[0])
	GWN_batch_instbuf_set(shgroup->instance_geom, batch->verts[0], false);

#ifdef USE_GPU_SELECT
	shgroup->override_selectid = DST.select_id;
#endif
}

unsigned int DRW_shgroup_get_instance_count(const DRWShadingGroup *shgroup)
{
	return shgroup->instance_count;
}

/**
 * State is added to #Pass.state while drawing.
 * Use to temporarily enable draw options.
 */
void DRW_shgroup_state_enable(DRWShadingGroup *shgroup, DRWState state)
{
	shgroup->state_extra |= state;
}

void DRW_shgroup_state_disable(DRWShadingGroup *shgroup, DRWState state)
{
	shgroup->state_extra_disable &= ~state;
}

void DRW_shgroup_stencil_mask(DRWShadingGroup *shgroup, unsigned int mask)
{
	BLI_assert(mask <= 255);
	shgroup->stencil_mask = mask;
}

/** \} */

/* -------------------------------------------------------------------- */

/** \name Passes (DRW_pass)
 * \{ */

DRWPass *DRW_pass_create(const char *name, DRWState state)
{
	DRWPass *pass = BLI_mempool_alloc(DST.vmempool->passes);
	pass->state = state;
	if (G.debug_value > 20) {
		BLI_strncpy(pass->name, name, MAX_PASS_NAME);
	}

	pass->shgroups.first = NULL;
	pass->shgroups.last = NULL;

	return pass;
}

void DRW_pass_state_set(DRWPass *pass, DRWState state)
{
	pass->state = state;
}

void DRW_pass_free(DRWPass *pass)
{
	pass->shgroups.first = NULL;
	pass->shgroups.last = NULL;
}

void DRW_pass_foreach_shgroup(DRWPass *pass, void (*callback)(void *userData, DRWShadingGroup *shgrp), void *userData)
{
	for (DRWShadingGroup *shgroup = pass->shgroups.first; shgroup; shgroup = shgroup->next) {
		callback(userData, shgroup);
	}
}

typedef struct ZSortData {
	float *axis;
	float *origin;
} ZSortData;

static int pass_shgroup_dist_sort(void *thunk, const void *a, const void *b)
{
	const ZSortData *zsortdata = (ZSortData *)thunk;
	const DRWShadingGroup *shgrp_a = (const DRWShadingGroup *)a;
	const DRWShadingGroup *shgrp_b = (const DRWShadingGroup *)b;

	const DRWCall *call_a = (DRWCall *)shgrp_a->calls.first;
	const DRWCall *call_b = (DRWCall *)shgrp_b->calls.first;

	if (call_a == NULL) return -1;
	if (call_b == NULL) return -1;

	float tmp[3];
	sub_v3_v3v3(tmp, zsortdata->origin, call_a->state->model[3]);
	const float a_sq = dot_v3v3(zsortdata->axis, tmp);
	sub_v3_v3v3(tmp, zsortdata->origin, call_b->state->model[3]);
	const float b_sq = dot_v3v3(zsortdata->axis, tmp);

	if      (a_sq < b_sq) return  1;
	else if (a_sq > b_sq) return -1;
	else {
		/* If there is a depth prepass put it before */
		if ((shgrp_a->state_extra & DRW_STATE_WRITE_DEPTH) != 0) {
			return -1;
		}
		else if ((shgrp_b->state_extra & DRW_STATE_WRITE_DEPTH) != 0) {
			return  1;
		}
		else return  0;
	}
}

/* ------------------ Shading group sorting --------------------- */

#define SORT_IMPL_LINKTYPE DRWShadingGroup

#define SORT_IMPL_USE_THUNK
#define SORT_IMPL_FUNC shgroup_sort_fn_r
#include "../../blenlib/intern/list_sort_impl.h"
#undef SORT_IMPL_FUNC
#undef SORT_IMPL_USE_THUNK

#undef SORT_IMPL_LINKTYPE

/**
 * Sort Shading groups by decreasing Z of their first draw call.
 * This is usefull for order dependant effect such as transparency.
 **/
void DRW_pass_sort_shgroup_z(DRWPass *pass)
{
	float (*viewinv)[4];
	viewinv = DST.view_data.matstate.mat[DRW_MAT_VIEWINV];

	ZSortData zsortdata = {viewinv[2], viewinv[3]};

	if (pass->shgroups.first && pass->shgroups.first->next) {
		pass->shgroups.first = shgroup_sort_fn_r(pass->shgroups.first, pass_shgroup_dist_sort, &zsortdata);

		/* Find the next last */
		DRWShadingGroup *last = pass->shgroups.first;
		while ((last = last->next)) {
			/* Do nothing */
		}
		pass->shgroups.last = last;
	}
}

/** \} */
