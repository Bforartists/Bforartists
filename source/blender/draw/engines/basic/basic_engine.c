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

/** \file basic_engine.h
 *  \ingroup draw_engine
 *
 * Simple engine for drawing color and/or depth.
 * When we only need simple flat shaders.
 */

#include "DRW_render.h"

#include "BKE_icons.h"
#include "BKE_idprop.h"
#include "BKE_main.h"

#include "GPU_shader.h"

#include "basic_engine.h"
/* Shaders */

#define BASIC_ENGINE "BLENDER_BASIC"

/* we may want this later? */
#define USE_DEPTH

/* *********** LISTS *********** */

/* GPUViewport.storage
 * Is freed everytime the viewport engine changes */
typedef struct BASIC_Storage {
	int dummy;
} BASIC_Storage;

typedef struct BASIC_StorageList {
	struct BASIC_Storage *storage;
	struct BASIC_PrivateData *g_data;
} BASIC_StorageList;

typedef struct BASIC_FramebufferList {
	/* default */
	struct GPUFrameBuffer *default_fb;
	/* engine specific */
#ifdef USE_DEPTH
	struct GPUFrameBuffer *dupli_depth;
#endif
} BASIC_FramebufferList;

typedef struct BASIC_TextureList {
	/* default */
	struct GPUTexture *color;
#ifdef USE_DEPTH
	struct GPUTexture *depth;
	/* engine specific */
	struct GPUTexture *depth_dup;
#endif
} BASIC_TextureList;

typedef struct BASIC_PassList {
#ifdef USE_DEPTH
	struct DRWPass *depth_pass;
	struct DRWPass *depth_pass_cull;
#endif
	struct DRWPass *color_pass;
} BASIC_PassList;

typedef struct BASIC_Data {
	void *engine_type;
	BASIC_FramebufferList *fbl;
	BASIC_TextureList *txl;
	BASIC_PassList *psl;
	BASIC_StorageList *stl;
} BASIC_Data;

/* *********** STATIC *********** */

static struct {
#ifdef USE_DEPTH
	/* Depth Pre Pass */
	struct GPUShader *depth_sh;
#endif
	/* Shading Pass */
	struct GPUShader *color_sh;
} e_data = {NULL}; /* Engine data */

typedef struct BASIC_PrivateData {
#ifdef USE_DEPTH
	DRWShadingGroup *depth_shgrp;
	DRWShadingGroup *depth_shgrp_cull;
#endif
	DRWShadingGroup *color_shgrp;
} BASIC_PrivateData; /* Transient data */

/* Functions */

static void BASIC_engine_init(void *vedata)
{
	BASIC_StorageList *stl = ((BASIC_Data *)vedata)->stl;
	BASIC_TextureList *txl = ((BASIC_Data *)vedata)->txl;
	BASIC_FramebufferList *fbl = ((BASIC_Data *)vedata)->fbl;

#ifdef USE_DEPTH
	/* Depth prepass */
	if (!e_data.depth_sh) {
		e_data.depth_sh = DRW_shader_create_3D_depth_only();
	}
#endif

	/* Shading pass */
	if (!e_data.color_sh) {
		e_data.color_sh = GPU_shader_get_builtin_shader(GPU_SHADER_3D_UNIFORM_COLOR);
	}

	if (!stl->storage) {
		stl->storage = MEM_callocN(sizeof(BASIC_Storage), "BASIC_Storage");
	}

#ifdef USE_DEPTH
	if (DRW_state_is_fbo()) {
		const float *viewport_size = DRW_viewport_size_get();
		DRWFboTexture tex = {&txl->depth_dup, DRW_TEX_DEPTH_24, 0};
		DRW_framebuffer_init(&fbl->dupli_depth, &draw_engine_basic_type,
		                     (int)viewport_size[0], (int)viewport_size[1],
		                     &tex, 1);
	}
#endif
}

static void BASIC_cache_init(void *vedata)
{
	BASIC_PassList *psl = ((BASIC_Data *)vedata)->psl;
	BASIC_StorageList *stl = ((BASIC_Data *)vedata)->stl;

	if (!stl->g_data) {
		/* Alloc transient pointers */
		stl->g_data = MEM_mallocN(sizeof(*stl->g_data), __func__);
	}

#ifdef USE_DEPTH
	/* Depth Pass */
	{
		psl->depth_pass = DRW_pass_create("Depth Pass", DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS);
		stl->g_data->depth_shgrp = DRW_shgroup_create(e_data.depth_sh, psl->depth_pass);

		psl->depth_pass_cull = DRW_pass_create(
		        "Depth Pass Cull",
		        DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS | DRW_STATE_CULL_BACK);
		stl->g_data->depth_shgrp_cull = DRW_shgroup_create(e_data.depth_sh, psl->depth_pass_cull);
	}
#endif

	/* Color Pass */
	{
		psl->color_pass = DRW_pass_create("Color Pass", DRW_STATE_WRITE_COLOR | DRW_STATE_DEPTH_EQUAL);
		stl->g_data->color_shgrp = DRW_shgroup_create(e_data.color_sh, psl->color_pass);
	}
}

static void BASIC_cache_populate(void *vedata, Object *ob)
{
	BASIC_StorageList *stl = ((BASIC_Data *)vedata)->stl;

	if (!DRW_object_is_renderable(ob))
		return;

	struct Gwn_Batch *geom = DRW_cache_object_surface_get(ob);
	if (geom) {
		bool do_cull = false;  /* TODO (we probably wan't to take this from the viewport?) */
#ifdef USE_DEPTH
		/* Depth Prepass */
		DRW_shgroup_call_add((do_cull) ? stl->g_data->depth_shgrp_cull : stl->g_data->depth_shgrp, geom, ob->obmat);
#endif
		/* Shading */
		DRW_shgroup_call_add(stl->g_data->color_shgrp, geom, ob->obmat);
	}
}

static void BASIC_cache_finish(void *vedata)
{
	BASIC_StorageList *stl = ((BASIC_Data *)vedata)->stl;

	UNUSED_VARS(stl);
}

static void BASIC_draw_scene(void *vedata)
{

	BASIC_PassList *psl = ((BASIC_Data *)vedata)->psl;
	BASIC_FramebufferList *fbl = ((BASIC_Data *)vedata)->fbl;
	DefaultFramebufferList *dfbl = DRW_viewport_framebuffer_list_get();

#ifdef USE_DEPTH
	/* Pass 1 : Depth pre-pass */
	DRW_draw_pass(psl->depth_pass);
	DRW_draw_pass(psl->depth_pass_cull);

	/* Pass 2 : Duplicate depth */
	/* Unless we go for deferred shading we need this to avoid manual depth test and artifacts */
	if (DRW_state_is_fbo()) {
		DRW_framebuffer_blit(dfbl->default_fb, fbl->dupli_depth, true);
	}
#endif

	/* Pass 3 : Shading */
	DRW_draw_pass(psl->color_pass);
}

static void BASIC_engine_free(void)
{
	/* all shaders are builtin */
}

static const DrawEngineDataSize BASIC_data_size = DRW_VIEWPORT_DATA_SIZE(BASIC_Data);

DrawEngineType draw_engine_basic_type = {
	NULL, NULL,
	N_("Basic"),
	&BASIC_data_size,
	&BASIC_engine_init,
	&BASIC_engine_free,
	&BASIC_cache_init,
	&BASIC_cache_populate,
	&BASIC_cache_finish,
	NULL,
	&BASIC_draw_scene
};

/* Note: currently unused, we may want to register so we can see this when debugging the view. */

RenderEngineType DRW_engine_viewport_basic_type = {
	NULL, NULL,
	BASIC_ENGINE, N_("Basic"), RE_INTERNAL,
	NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
	&draw_engine_basic_type,
	{NULL, NULL, NULL}
};


#undef BASIC_ENGINE
