/*
 * ***** BEGIN GPL LICENSE BLOCK *****
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
 * Copyright 2016, Blender Foundation.
 * Contributor(s): Blender Institute
 *
 * ***** END GPL LICENSE BLOCK *****
 *
 */

/** \file blender/draw/modes/edit_curve_mode.c
 *  \ingroup draw
 */

#include "DRW_engine.h"
#include "DRW_render.h"

#include "DNA_curve_types.h"
#include "DNA_view3d_types.h"

#include "BKE_object.h"

/* If builtin shaders are needed */
#include "GPU_shader.h"
#include "GPU_batch.h"

#include "draw_common.h"

#include "draw_mode_engines.h"

/* If needed, contains all global/Theme colors
 * Add needed theme colors / values to DRW_globals_update() and update UBO
 * Not needed for constant color. */

extern char datatoc_common_globals_lib_glsl[];
extern char datatoc_edit_curve_overlay_loosevert_vert_glsl[];
extern char datatoc_edit_curve_overlay_normals_vert_glsl[];
extern char datatoc_edit_curve_overlay_handle_vert_glsl[];
extern char datatoc_edit_curve_overlay_handle_geom_glsl[];

extern char datatoc_gpu_shader_point_varying_color_frag_glsl[];
extern char datatoc_gpu_shader_3D_smooth_color_frag_glsl[];
extern char datatoc_gpu_shader_uniform_color_frag_glsl[];

/* *********** LISTS *********** */
/* All lists are per viewport specific datas.
 * They are all free when viewport changes engines
 * or is free itself. Use EDIT_CURVE_engine_init() to
 * initialize most of them and EDIT_CURVE_cache_init()
 * for EDIT_CURVE_PassList */

typedef struct EDIT_CURVE_PassList {
	struct DRWPass *wire_pass;
	struct DRWPass *overlay_edge_pass;
	struct DRWPass *overlay_vert_pass;
} EDIT_CURVE_PassList;

typedef struct EDIT_CURVE_StorageList {
	struct CustomStruct *block;
	struct EDIT_CURVE_PrivateData *g_data;
} EDIT_CURVE_StorageList;

typedef struct EDIT_CURVE_Data {
	void *engine_type; /* Required */
	DRWViewportEmptyList *fbl;
	DRWViewportEmptyList *txl;
	EDIT_CURVE_PassList *psl;
	EDIT_CURVE_StorageList *stl;
} EDIT_CURVE_Data;

/* *********** STATIC *********** */

static struct {
	GPUShader *wire_sh;
	GPUShader *wire_normals_sh;
	GPUShader *overlay_edge_sh;  /* handles and nurbs control cage */
	GPUShader *overlay_vert_sh;
} e_data = {NULL}; /* Engine data */

typedef struct EDIT_CURVE_PrivateData {
	/* resulting curve as 'wire' for curves (and optionally normals) */
	DRWShadingGroup *wire_shgrp;
	DRWShadingGroup *wire_normals_shgrp;

	DRWShadingGroup *overlay_edge_shgrp;
	DRWShadingGroup *overlay_vert_shgrp;

	int show_handles;
} EDIT_CURVE_PrivateData; /* Transient data */

/* *********** FUNCTIONS *********** */

/* Init Textures, Framebuffers, Storage and Shaders.
 * It is called for every frames.
 * (Optional) */
static void EDIT_CURVE_engine_init(void *UNUSED(vedata))
{
	if (!e_data.wire_sh) {
		e_data.wire_sh = GPU_shader_get_builtin_shader(GPU_SHADER_3D_UNIFORM_COLOR);
	}

	if (!e_data.wire_normals_sh) {
		e_data.wire_normals_sh = DRW_shader_create(
		        datatoc_edit_curve_overlay_normals_vert_glsl, NULL,
		        datatoc_gpu_shader_uniform_color_frag_glsl, NULL);
	}

	if (!e_data.overlay_edge_sh) {
		e_data.overlay_edge_sh = DRW_shader_create_with_lib(
		        datatoc_edit_curve_overlay_handle_vert_glsl,
		        datatoc_edit_curve_overlay_handle_geom_glsl,
		        datatoc_gpu_shader_3D_smooth_color_frag_glsl,
		        datatoc_common_globals_lib_glsl, NULL);
	}

	if (!e_data.overlay_vert_sh) {
		e_data.overlay_vert_sh = DRW_shader_create_with_lib(
		        datatoc_edit_curve_overlay_loosevert_vert_glsl, NULL,
		        datatoc_gpu_shader_point_varying_color_frag_glsl,
		        datatoc_common_globals_lib_glsl, NULL);
	}
}

/* Here init all passes and shading groups
 * Assume that all Passes are NULL */
static void EDIT_CURVE_cache_init(void *vedata)
{
	EDIT_CURVE_PassList *psl = ((EDIT_CURVE_Data *)vedata)->psl;
	EDIT_CURVE_StorageList *stl = ((EDIT_CURVE_Data *)vedata)->stl;
	const DRWContextState *draw_ctx = DRW_context_state_get();
	View3D *v3d = draw_ctx->v3d;

	if (!stl->g_data) {
		/* Alloc transient pointers */
		stl->g_data = MEM_callocN(sizeof(*stl->g_data), __func__);
	}

	stl->g_data->show_handles = (v3d->overlay.edit_flag & V3D_OVERLAY_EDIT_CU_HANDLES) != 0;

	{
		DRWShadingGroup *grp;

		/* Center-Line (wire) */
		psl->wire_pass = DRW_pass_create(
		        "Curve Wire",
		        DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS_EQUAL | DRW_STATE_WIRE);

		grp = DRW_shgroup_create(e_data.wire_sh, psl->wire_pass);
		DRW_shgroup_uniform_vec4(grp, "color", G_draw.block.colorWireEdit, 1);
		stl->g_data->wire_shgrp = grp;


		grp = DRW_shgroup_create(e_data.wire_normals_sh, psl->wire_pass);
		DRW_shgroup_uniform_vec4(grp, "color", G_draw.block.colorWireEdit, 1);
		DRW_shgroup_uniform_float_copy(grp, "normalSize", v3d->overlay.normals_length);
		stl->g_data->wire_normals_shgrp = grp;

		psl->overlay_edge_pass = DRW_pass_create(
		        "Curve Handle Overlay",
		        DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND);

		grp = DRW_shgroup_create(e_data.overlay_edge_sh, psl->overlay_edge_pass);
		DRW_shgroup_uniform_block(grp, "globalsBlock", G_draw.block_ubo);
		DRW_shgroup_uniform_vec2(grp, "viewportSize", DRW_viewport_size_get(), 1);
		DRW_shgroup_uniform_bool(grp, "showCurveHandles", &stl->g_data->show_handles, 1);
		stl->g_data->overlay_edge_shgrp = grp;


		psl->overlay_vert_pass = DRW_pass_create(
		        "Curve Vert Overlay",
		        DRW_STATE_WRITE_COLOR | DRW_STATE_POINT);

		grp = DRW_shgroup_create(e_data.overlay_vert_sh, psl->overlay_vert_pass);
		DRW_shgroup_uniform_block(grp, "globalsBlock", G_draw.block_ubo);
		stl->g_data->overlay_vert_shgrp = grp;
	}
}

/* Add geometry to shadingGroups. Execute for each objects */
static void EDIT_CURVE_cache_populate(void *vedata, Object *ob)
{
	EDIT_CURVE_StorageList *stl = ((EDIT_CURVE_Data *)vedata)->stl;
	const DRWContextState *draw_ctx = DRW_context_state_get();
	View3D *v3d = draw_ctx->v3d;

	if (ob->type == OB_CURVE) {
		if (BKE_object_is_in_editmode(ob)) {
			Curve *cu = ob->data;
			/* Get geometry cache */
			struct GPUBatch *geom;

			geom = DRW_cache_curve_edge_wire_get(ob);
			DRW_shgroup_call_add(stl->g_data->wire_shgrp, geom, ob->obmat);

			if ((cu->flag & CU_3D) && (v3d->overlay.edit_flag & V3D_OVERLAY_EDIT_CU_NORMALS) != 0) {
				static uint instance_len = 2;
				geom = DRW_cache_curve_edge_normal_get(ob);
				DRW_shgroup_call_instances_add(stl->g_data->wire_normals_shgrp, geom, ob->obmat, &instance_len);
			}

			geom = DRW_cache_curve_edge_overlay_get(ob);
			if (geom) {
				DRW_shgroup_call_add(stl->g_data->overlay_edge_shgrp, geom, ob->obmat);
			}

			geom = DRW_cache_curve_vert_overlay_get(ob, stl->g_data->show_handles);
			DRW_shgroup_call_add(stl->g_data->overlay_vert_shgrp, geom, ob->obmat);
		}
	}

	if (ob->type == OB_SURF) {
		if (BKE_object_is_in_editmode(ob)) {
			struct GPUBatch *geom = DRW_cache_curve_edge_overlay_get(ob);
			DRW_shgroup_call_add(stl->g_data->overlay_edge_shgrp, geom, ob->obmat);

			geom = DRW_cache_curve_vert_overlay_get(ob, false);
			DRW_shgroup_call_add(stl->g_data->overlay_vert_shgrp, geom, ob->obmat);
		}
	}
}

/* Draw time ! Control rendering pipeline from here */
static void EDIT_CURVE_draw_scene(void *vedata)
{
	EDIT_CURVE_PassList *psl = ((EDIT_CURVE_Data *)vedata)->psl;

	/* Default framebuffer and texture */
	DefaultFramebufferList *dfbl = DRW_viewport_framebuffer_list_get();
	DefaultTextureList *dtxl = DRW_viewport_texture_list_get();

	if (!DRW_pass_is_empty(psl->wire_pass)) {
		MULTISAMPLE_SYNC_ENABLE(dfbl, dtxl);

		DRW_draw_pass(psl->wire_pass);

		MULTISAMPLE_SYNC_DISABLE(dfbl, dtxl)
	}

	/* Thoses passes don't write to depth and are AA'ed using other tricks. */
	DRW_draw_pass(psl->overlay_edge_pass);
	DRW_draw_pass(psl->overlay_vert_pass);
}

/* Cleanup when destroying the engine.
 * This is not per viewport ! only when quitting blender.
 * Mostly used for freeing shaders */
static void EDIT_CURVE_engine_free(void)
{
	DRW_SHADER_FREE_SAFE(e_data.wire_normals_sh);
	DRW_SHADER_FREE_SAFE(e_data.overlay_edge_sh);
	DRW_SHADER_FREE_SAFE(e_data.overlay_vert_sh);
}

static const DrawEngineDataSize EDIT_CURVE_data_size = DRW_VIEWPORT_DATA_SIZE(EDIT_CURVE_Data);

DrawEngineType draw_engine_edit_curve_type = {
	NULL, NULL,
	N_("EditCurveMode"),
	&EDIT_CURVE_data_size,
	&EDIT_CURVE_engine_init,
	&EDIT_CURVE_engine_free,
	&EDIT_CURVE_cache_init,
	&EDIT_CURVE_cache_populate,
	NULL,
	NULL, /* draw_background but not needed by mode engines */
	&EDIT_CURVE_draw_scene,
	NULL,
	NULL,
};
