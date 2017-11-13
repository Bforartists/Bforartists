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

/* Screen space reflections and refractions techniques.
 */

/** \file eevee_subsurface.c
 *  \ingroup draw_engine
 */

#include "DRW_render.h"

#include "BLI_dynstr.h"

#include "eevee_private.h"
#include "GPU_texture.h"

/* SSR shader variations */
enum {
	SSR_SAMPLES      = (1 << 0) | (1 << 1),
	SSR_RESOLVE      = (1 << 2),
	SSR_FULL_TRACE   = (1 << 3),
	SSR_MAX_SHADER   = (1 << 4),
};

static struct {
	/* Screen Space SubSurfaceScattering */
	struct GPUShader *sss_sh[2];
} e_data = {NULL}; /* Engine data */

extern char datatoc_effect_subsurface_frag_glsl[];

static void eevee_create_shader_subsurface(void)
{
	e_data.sss_sh[0] = DRW_shader_create_fullscreen(datatoc_effect_subsurface_frag_glsl, "#define FIRST_PASS\n");
	e_data.sss_sh[1] = DRW_shader_create_fullscreen(datatoc_effect_subsurface_frag_glsl, "#define SECOND_PASS\n");
}

int EEVEE_subsurface_init(EEVEE_SceneLayerData *UNUSED(sldata), EEVEE_Data *vedata)
{
	EEVEE_FramebufferList *fbl = vedata->fbl;
	EEVEE_TextureList *txl = vedata->txl;
	const float *viewport_size = DRW_viewport_size_get();

	const DRWContextState *draw_ctx = DRW_context_state_get();
	SceneLayer *scene_layer = draw_ctx->scene_layer;
	IDProperty *props = BKE_scene_layer_engine_evaluated_get(scene_layer, COLLECTION_MODE_NONE, RE_engine_id_BLENDER_EEVEE);

	if (BKE_collection_engine_property_value_get_bool(props, "sss_enable")) {

		/* Shaders */
		if (!e_data.sss_sh[0]) {
			eevee_create_shader_subsurface();
		}

		/* NOTE : we need another stencil because the stencil buffer is on the same texture
		 * as the depth buffer we are sampling from. This could be avoided if the stencil is
		 * a separate texture but that needs OpenGL 4.4 or ARB_texture_stencil8.
		 * OR OpenGL 4.3 / ARB_ES3_compatibility if using a renderbuffer instead */
		DRWFboTexture texs[2] = {{&txl->sss_stencil, DRW_TEX_DEPTH_24_STENCIL_8, 0},
		                         {&txl->sss_blur, DRW_TEX_RGBA_16, DRW_TEX_FILTER}};

		DRW_framebuffer_init(&fbl->sss_blur_fb, &draw_engine_eevee_type, (int)viewport_size[0], (int)viewport_size[1],
		                     texs, 2);

		DRWFboTexture tex_data = {&txl->sss_data, DRW_TEX_RGBA_16, DRW_TEX_FILTER};
		DRW_framebuffer_init(&fbl->sss_clear_fb, &draw_engine_eevee_type, (int)viewport_size[0], (int)viewport_size[1],
		                     &tex_data, 1);

		return EFFECT_SSS;
	}

	/* Cleanup to release memory */
	DRW_TEXTURE_FREE_SAFE(txl->sss_data);
	DRW_TEXTURE_FREE_SAFE(txl->sss_blur);
	DRW_TEXTURE_FREE_SAFE(txl->sss_stencil);
	DRW_FRAMEBUFFER_FREE_SAFE(fbl->sss_blur_fb);
	DRW_FRAMEBUFFER_FREE_SAFE(fbl->sss_clear_fb);

	return 0;
}

void EEVEE_subsurface_cache_init(EEVEE_SceneLayerData *UNUSED(sldata), EEVEE_Data *vedata)
{
	EEVEE_PassList *psl = vedata->psl;
	EEVEE_StorageList *stl = vedata->stl;
	EEVEE_EffectsInfo *effects = stl->effects;

	if ((effects->enabled_effects & EFFECT_SSS) != 0) {
		/** Screen Space SubSurface Scattering overview
		 * TODO
		 */
		psl->sss_blur_ps = DRW_pass_create("Blur Horiz", DRW_STATE_WRITE_COLOR | DRW_STATE_STENCIL_EQUAL);

		psl->sss_resolve_ps = DRW_pass_create("Blur Vert", DRW_STATE_WRITE_COLOR | DRW_STATE_ADDITIVE | DRW_STATE_STENCIL_EQUAL);
	}
}

void EEVEE_subsurface_add_pass(EEVEE_Data *vedata, unsigned int sss_id, struct GPUUniformBuffer *sss_profile)
{
	DefaultTextureList *dtxl = DRW_viewport_texture_list_get();
	EEVEE_TextureList *txl = vedata->txl;
	EEVEE_PassList *psl = vedata->psl;
	struct Gwn_Batch *quad = DRW_cache_fullscreen_quad_get();

	DRWShadingGroup *grp = DRW_shgroup_create(e_data.sss_sh[0], psl->sss_blur_ps);
	DRW_shgroup_uniform_vec4(grp, "viewvecs[0]", (float *)vedata->stl->g_data->viewvecs, 2);
	DRW_shgroup_uniform_texture(grp, "utilTex", EEVEE_materials_get_util_tex());
	DRW_shgroup_uniform_buffer(grp, "depthBuffer", &dtxl->depth);
	DRW_shgroup_uniform_buffer(grp, "sssData", &txl->sss_data);
	DRW_shgroup_uniform_block(grp, "sssProfile", sss_profile);
	DRW_shgroup_stencil_mask(grp, sss_id);
	DRW_shgroup_call_add(grp, quad, NULL);

	grp = DRW_shgroup_create(e_data.sss_sh[1], psl->sss_resolve_ps);
	DRW_shgroup_uniform_vec4(grp, "viewvecs[0]", (float *)vedata->stl->g_data->viewvecs, 2);
	DRW_shgroup_uniform_texture(grp, "utilTex", EEVEE_materials_get_util_tex());
	DRW_shgroup_uniform_buffer(grp, "depthBuffer", &dtxl->depth);
	DRW_shgroup_uniform_buffer(grp, "sssData", &txl->sss_blur);
	DRW_shgroup_uniform_block(grp, "sssProfile", sss_profile);
	DRW_shgroup_stencil_mask(grp, sss_id);
	DRW_shgroup_call_add(grp, quad, NULL);
}

void EEVEE_subsurface_data_render(EEVEE_SceneLayerData *UNUSED(sldata), EEVEE_Data *vedata)
{
	EEVEE_PassList *psl = vedata->psl;
	EEVEE_TextureList *txl = vedata->txl;
	EEVEE_FramebufferList *fbl = vedata->fbl;
	EEVEE_StorageList *stl = vedata->stl;
	EEVEE_EffectsInfo *effects = stl->effects;

	if ((effects->enabled_effects & EFFECT_SSS) != 0) {
		float clear[4] = {0.0f, 0.0f, 0.0f, 0.0f};
		/* Clear sss_data texture only... can this be done in a more clever way? */
		DRW_framebuffer_bind(fbl->sss_clear_fb);
		DRW_framebuffer_clear(true, false, false, clear, 0.0f);

		if ((effects->enabled_effects & EFFECT_NORMAL_BUFFER) != 0) {
			DRW_framebuffer_texture_detach(txl->ssr_normal_input);
		}
		if ((effects->enabled_effects & EFFECT_SSR) != 0) {
			DRW_framebuffer_texture_detach(txl->ssr_specrough_input);
		}
		if ((effects->enabled_effects & EFFECT_NORMAL_BUFFER) != 0) {
			DRW_framebuffer_texture_attach(fbl->main, txl->ssr_normal_input, 2, 0);
		}
		if ((effects->enabled_effects & EFFECT_SSR) != 0) {
			DRW_framebuffer_texture_attach(fbl->main, txl->ssr_specrough_input, 3, 0);
		}
		DRW_framebuffer_texture_detach(txl->sss_data);
		DRW_framebuffer_texture_attach(fbl->main, txl->sss_data, 1, 0);
		DRW_framebuffer_bind(fbl->main);

		DRW_draw_pass(psl->sss_pass);

		if ((effects->enabled_effects & EFFECT_NORMAL_BUFFER) != 0) {
			DRW_framebuffer_texture_detach(txl->ssr_normal_input);
		}
		if ((effects->enabled_effects & EFFECT_SSR) != 0) {
			DRW_framebuffer_texture_detach(txl->ssr_specrough_input);
		}
		DRW_framebuffer_texture_detach(txl->sss_data);
		if ((effects->enabled_effects & EFFECT_NORMAL_BUFFER) != 0) {
			DRW_framebuffer_texture_attach(fbl->main, txl->ssr_normal_input, 1, 0);
		}
		if ((effects->enabled_effects & EFFECT_SSR) != 0) {
			DRW_framebuffer_texture_attach(fbl->main, txl->ssr_specrough_input, 2, 0);
		}
		DRW_framebuffer_texture_attach(fbl->sss_clear_fb, txl->sss_data, 0, 0);
	}
}

void EEVEE_subsurface_compute(EEVEE_SceneLayerData *UNUSED(sldata), EEVEE_Data *vedata)
{
	EEVEE_PassList *psl = vedata->psl;
	EEVEE_FramebufferList *fbl = vedata->fbl;
	EEVEE_TextureList *txl = vedata->txl;
	EEVEE_StorageList *stl = vedata->stl;
	EEVEE_EffectsInfo *effects = stl->effects;

	if ((effects->enabled_effects & EFFECT_SSS) != 0) {
		float clear[4] = {0.0f, 0.0f, 0.0f, 0.0f};
		DefaultTextureList *dtxl = DRW_viewport_texture_list_get();

		DRW_stats_group_start("SSS");

		/* Copy stencil channel, could be avoided (see EEVEE_subsurface_init) */
		DRW_framebuffer_blit(fbl->main, fbl->sss_blur_fb, false, true);

		DRW_framebuffer_texture_detach(dtxl->depth);

		/* First horizontal pass */
		DRW_framebuffer_bind(fbl->sss_blur_fb);
		DRW_framebuffer_clear(true, false, false, clear, 0.0f);
		DRW_draw_pass(psl->sss_blur_ps);

		/* First vertical pass + Resolve */
		DRW_framebuffer_texture_detach(txl->sss_stencil);
		DRW_framebuffer_texture_attach(fbl->main, txl->sss_stencil, 0, 0);
		DRW_framebuffer_bind(fbl->main);
		DRW_draw_pass(psl->sss_resolve_ps);

		/* Restore */
		DRW_framebuffer_texture_detach(txl->sss_stencil);
		DRW_framebuffer_texture_attach(fbl->sss_blur_fb, txl->sss_stencil, 0, 0);
		DRW_framebuffer_texture_attach(fbl->main, dtxl->depth, 0, 0);

		DRW_stats_group_end();
	}
}

void EEVEE_subsurface_free(void)
{
	DRW_SHADER_FREE_SAFE(e_data.sss_sh[0]);
	DRW_SHADER_FREE_SAFE(e_data.sss_sh[1]);
}
