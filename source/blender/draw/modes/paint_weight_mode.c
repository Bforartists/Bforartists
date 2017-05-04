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

/** \file blender/draw/modes/paint_weight_mode.c
 *  \ingroup draw
 */

#include "DRW_engine.h"
#include "DRW_render.h"

/* If builtin shaders are needed */
#include "GPU_shader.h"

#include "draw_common.h"

#include "draw_mode_engines.h"

#include "DNA_mesh_types.h"

#include "BKE_mesh.h"

extern struct GPUUniformBuffer *globals_ubo; /* draw_common.c */
extern struct GlobalsUboStorage ts; /* draw_common.c */

/* *********** LISTS *********** */

typedef struct PAINT_WEIGHT_PassList {
	struct DRWPass *weight_faces;
	struct DRWPass *wire_overlay;
	struct DRWPass *face_overlay;
	struct DRWPass *vert_overlay;
} PAINT_WEIGHT_PassList;

typedef struct PAINT_WEIGHT_StorageList {
	struct PAINT_WEIGHT_PrivateData *g_data;
} PAINT_WEIGHT_StorageList;

typedef struct PAINT_WEIGHT_Data {
	void *engine_type;
	DRWViewportEmptyList *fbl;
	DRWViewportEmptyList *txl;
	PAINT_WEIGHT_PassList *psl;
	PAINT_WEIGHT_StorageList *stl;
} PAINT_WEIGHT_Data;

/* *********** STATIC *********** */

static struct {
	struct GPUShader *weight_face_shader;
	struct GPUShader *flat_overlay_shader;
	struct GPUShader *vert_overlay_shader;
	int actdef;
} e_data = {NULL}; /* Engine data */

typedef struct PAINT_WEIGHT_PrivateData {
	DRWShadingGroup *fweights_shgrp;
	DRWShadingGroup *lwire_shgrp;
	DRWShadingGroup *face_shgrp;
	DRWShadingGroup *vert_shgrp;
} PAINT_WEIGHT_PrivateData;

/* *********** FUNCTIONS *********** */

static void PAINT_WEIGHT_engine_init(void *UNUSED(vedata))
{
	const DRWContextState *draw_ctx = DRW_context_state_get();

	if (e_data.actdef != draw_ctx->sl->basact->object->actdef) {
		e_data.actdef = draw_ctx->sl->basact->object->actdef;

		BKE_mesh_batch_cache_dirty(draw_ctx->sl->basact->object->data, BKE_MESH_BATCH_DIRTY_PAINT);
	}

	if (!e_data.weight_face_shader) {
		e_data.weight_face_shader = GPU_shader_get_builtin_shader(GPU_SHADER_SIMPLE_LIGHTING_SMOOTH_COLOR_ALPHA);
	}

	if (!e_data.flat_overlay_shader) {
		e_data.flat_overlay_shader = GPU_shader_get_builtin_shader(GPU_SHADER_3D_FLAT_COLOR);
	}

	if (!e_data.vert_overlay_shader) {
		e_data.vert_overlay_shader = GPU_shader_get_builtin_shader(GPU_SHADER_3D_POINT_FIXED_SIZE_VARYING_COLOR);
	}
}

static float world_light;

static void PAINT_WEIGHT_cache_init(void *vedata)
{
	PAINT_WEIGHT_PassList *psl = ((PAINT_WEIGHT_Data *)vedata)->psl;
	PAINT_WEIGHT_StorageList *stl = ((PAINT_WEIGHT_Data *)vedata)->stl;

	if (!stl->g_data) {
		/* Alloc transient pointers */
		stl->g_data = MEM_mallocN(sizeof(*stl->g_data), __func__);
	}

	{
		/* Create a pass */
		psl->weight_faces = DRW_pass_create("Weight Pass", DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS);

		stl->g_data->fweights_shgrp = DRW_shgroup_create(e_data.weight_face_shader, psl->weight_faces);

		static float light[3] = {-0.3f, 0.5f, 1.0f};
		static float alpha = 1.0f;
		DRW_shgroup_uniform_vec3(stl->g_data->fweights_shgrp, "light", light, 1);
		DRW_shgroup_uniform_float(stl->g_data->fweights_shgrp, "alpha", &alpha, 1);
		DRW_shgroup_uniform_float(stl->g_data->fweights_shgrp, "global", &world_light, 1);
	}

	{
		psl->wire_overlay = DRW_pass_create("Wire Pass", DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS);

		stl->g_data->lwire_shgrp = DRW_shgroup_create(e_data.flat_overlay_shader, psl->wire_overlay);
	}

	{
		psl->face_overlay = DRW_pass_create("Wire Pass", DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS | DRW_STATE_BLEND);

		stl->g_data->face_shgrp = DRW_shgroup_create(e_data.flat_overlay_shader, psl->face_overlay);
	}

	{
		psl->vert_overlay = DRW_pass_create("Wire Pass", DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS);

		stl->g_data->vert_shgrp = DRW_shgroup_create(e_data.vert_overlay_shader, psl->vert_overlay);
	}
}

static void PAINT_WEIGHT_cache_populate(void *vedata, Object *ob)
{
	PAINT_WEIGHT_StorageList *stl = ((PAINT_WEIGHT_Data *)vedata)->stl;
	const DRWContextState *draw_ctx = DRW_context_state_get();
	SceneLayer *sl = draw_ctx->sl;

	if (ob->type == OB_MESH && ob == sl->basact->object) {
		IDProperty *ces_mode_pw = BKE_object_collection_engine_get(ob, COLLECTION_MODE_PAINT_WEIGHT, "");
		bool use_wire = BKE_collection_engine_property_value_get_bool(ces_mode_pw, "use_wire");
		char flag = ((Mesh *)ob->data)->editflag;
		struct Batch *geom;

		world_light = BKE_collection_engine_property_value_get_bool(ces_mode_pw, "use_shading") ? 0.5f : 1.0f;

		geom = DRW_cache_mesh_surface_weights_get(ob);
		DRW_shgroup_call_add(stl->g_data->fweights_shgrp, geom, ob->obmat);

		if (flag & ME_EDIT_PAINT_FACE_SEL || use_wire) {
			geom = DRW_cache_mesh_edges_paint_overlay_get(ob, use_wire, flag & ME_EDIT_PAINT_FACE_SEL, false);
			DRW_shgroup_call_add(stl->g_data->lwire_shgrp, geom, ob->obmat);
		}

		if (flag & ME_EDIT_PAINT_FACE_SEL) {
			geom = DRW_cache_mesh_faces_weight_overlay_get(ob);
			DRW_shgroup_call_add(stl->g_data->face_shgrp, geom, ob->obmat);
		}

		if (flag & ME_EDIT_PAINT_VERT_SEL) {
			geom = DRW_cache_mesh_verts_weight_overlay_get(ob);
			DRW_shgroup_call_add(stl->g_data->vert_shgrp, geom, ob->obmat);
		}
	}
}

static void PAINT_WEIGHT_draw_scene(void *vedata)
{
	PAINT_WEIGHT_PassList *psl = ((PAINT_WEIGHT_Data *)vedata)->psl;

	DRW_draw_pass(psl->weight_faces);
	DRW_draw_pass(psl->face_overlay);
	DRW_draw_pass(psl->wire_overlay);
	DRW_draw_pass(psl->vert_overlay);
}

static void PAINT_WEIGHT_engine_free(void)
{
}

void PAINT_WEIGHT_collection_settings_create(IDProperty *properties)
{
	BLI_assert(properties &&
	           properties->type == IDP_GROUP &&
	           properties->subtype == IDP_GROUP_SUB_MODE_PAINT_WEIGHT);

	BKE_collection_engine_property_add_bool(properties, "use_shading", true);
	BKE_collection_engine_property_add_bool(properties, "use_wire", false);
}

static const DrawEngineDataSize PAINT_WEIGHT_data_size = DRW_VIEWPORT_DATA_SIZE(PAINT_WEIGHT_Data);

DrawEngineType draw_engine_paint_weight_type = {
	NULL, NULL,
	N_("PaintWeightMode"),
	&PAINT_WEIGHT_data_size,
	&PAINT_WEIGHT_engine_init,
	&PAINT_WEIGHT_engine_free,
	&PAINT_WEIGHT_cache_init,
	&PAINT_WEIGHT_cache_populate,
	NULL,
	NULL,
	&PAINT_WEIGHT_draw_scene
};
