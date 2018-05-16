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

/** \file eevee_engine.c
 *  \ingroup draw_engine
 */

#include "DRW_render.h"

#include "BLI_dynstr.h"
#include "BLI_rand.h"

#include "BKE_object.h"
#include "BKE_global.h" /* for G.debug_value */
#include "BKE_screen.h"

#include "DNA_world_types.h"

#include "ED_screen.h"

#include "GPU_material.h"
#include "GPU_glew.h"

#include "eevee_engine.h"
#include "eevee_private.h"

#define EEVEE_ENGINE "BLENDER_EEVEE"

extern GlobalsUboStorage ts;

/* *********** FUNCTIONS *********** */

static void eevee_engine_init(void *ved)
{
	EEVEE_Data *vedata = (EEVEE_Data *)ved;
	EEVEE_TextureList *txl = vedata->txl;
	EEVEE_FramebufferList *fbl = vedata->fbl;
	EEVEE_StorageList *stl = ((EEVEE_Data *)vedata)->stl;
	EEVEE_ViewLayerData *sldata = EEVEE_view_layer_data_ensure();
	DefaultTextureList *dtxl = DRW_viewport_texture_list_get();

	const DRWContextState *draw_ctx = DRW_context_state_get();
	View3D *v3d = draw_ctx->v3d;
	RegionView3D *rv3d = draw_ctx->rv3d;
	Object *camera = (rv3d->persp == RV3D_CAMOB) ? v3d->camera : NULL;

	if (!stl->g_data) {
		/* Alloc transient pointers */
		stl->g_data = MEM_callocN(sizeof(*stl->g_data), __func__);
	}
	stl->g_data->background_alpha = DRW_state_draw_background() ? 1.0f : 0.0f;
	stl->g_data->valid_double_buffer = (txl->color_double_buffer != NULL);

	/* Main Buffer */
	DRW_texture_ensure_fullscreen_2D(&txl->color, GPU_RGBA16F, DRW_TEX_FILTER | DRW_TEX_MIPMAP);

	GPU_framebuffer_ensure_config(&fbl->main_fb, {
		GPU_ATTACHMENT_TEXTURE(dtxl->depth),
		GPU_ATTACHMENT_TEXTURE(txl->color),
		GPU_ATTACHMENT_LEAVE,
		GPU_ATTACHMENT_LEAVE,
		GPU_ATTACHMENT_LEAVE,
		GPU_ATTACHMENT_LEAVE
	});

	GPU_framebuffer_ensure_config(&fbl->main_color_fb, {
		GPU_ATTACHMENT_NONE,
		GPU_ATTACHMENT_TEXTURE(txl->color)
	});

	if (sldata->common_ubo == NULL) {
		sldata->common_ubo = DRW_uniformbuffer_create(sizeof(sldata->common_data), &sldata->common_data);
	}
	if (sldata->clip_ubo == NULL) {
		sldata->clip_ubo = DRW_uniformbuffer_create(sizeof(sldata->clip_data), &sldata->clip_data);
	}

	/* EEVEE_effects_init needs to go first for TAA */
	EEVEE_effects_init(sldata, vedata, camera);
	EEVEE_materials_init(sldata, stl, fbl);
	EEVEE_lights_init(sldata);
	EEVEE_lightprobes_init(sldata, vedata);

	if ((stl->effects->taa_current_sample > 1) && !DRW_state_is_image_render()) {
		/* XXX otherwise it would break the other engines. */
		DRW_viewport_matrix_override_unset_all();
	}
}

static void eevee_cache_init(void *vedata)
{
	EEVEE_ViewLayerData *sldata = EEVEE_view_layer_data_ensure();

	EEVEE_bloom_cache_init(sldata, vedata);
	EEVEE_depth_of_field_cache_init(sldata, vedata);
	EEVEE_effects_cache_init(sldata, vedata);
	EEVEE_lightprobes_cache_init(sldata, vedata);
	EEVEE_lights_cache_init(sldata, vedata);
	EEVEE_materials_cache_init(sldata, vedata);
	EEVEE_motion_blur_cache_init(sldata, vedata);
	EEVEE_occlusion_cache_init(sldata, vedata);
	EEVEE_screen_raytrace_cache_init(sldata, vedata);
	EEVEE_subsurface_cache_init(sldata, vedata);
	EEVEE_temporal_sampling_cache_init(sldata, vedata);
	EEVEE_volumes_cache_init(sldata, vedata);
}

static void eevee_cache_populate(void *vedata, Object *ob)
{
	EEVEE_ViewLayerData *sldata = EEVEE_view_layer_data_ensure();

	const DRWContextState *draw_ctx = DRW_context_state_get();
	const bool is_active = (ob == draw_ctx->obact);
	if (is_active) {
		if (DRW_object_is_mode_shade(ob) == true) {
			return;
		}
	}

	if (DRW_check_object_visible_within_active_context(ob) == false) {
		return;
	}

	if (ELEM(ob->type, OB_MESH, OB_CURVE, OB_SURF, OB_FONT)) {
		bool cast_shadow;

		EEVEE_materials_cache_populate(vedata, sldata, ob, &cast_shadow);

		if (cast_shadow) {
			EEVEE_lights_cache_shcaster_object_add(sldata, ob);
		}
	}
	else if (ob->type == OB_LIGHTPROBE) {
		if ((ob->base_flag & BASE_FROMDUPLI) != 0) {
			/* TODO: Special case for dupli objects because we cannot save the object pointer. */
		}
		else {
			EEVEE_lightprobes_cache_add(sldata, ob);
		}
	}
	else if (ob->type == OB_LAMP) {
		EEVEE_lights_cache_add(sldata, ob);
	}
}

static void eevee_cache_finish(void *vedata)
{
	EEVEE_ViewLayerData *sldata = EEVEE_view_layer_data_ensure();

	EEVEE_materials_cache_finish(vedata);
	EEVEE_lights_cache_finish(sldata);
	EEVEE_lightprobes_cache_finish(sldata, vedata);
}

/* As renders in an HDR offscreen buffer, we need draw everything once
 * during the background pass. This way the other drawing callback between
 * the background and the scene pass are visible.
 * Note: we could break it up in two passes using some depth test
 * to reduce the fillrate */
static void eevee_draw_background(void *vedata)
{
	EEVEE_PassList *psl = ((EEVEE_Data *)vedata)->psl;
	EEVEE_TextureList *txl = ((EEVEE_Data *)vedata)->txl;
	EEVEE_StorageList *stl = ((EEVEE_Data *)vedata)->stl;
	EEVEE_FramebufferList *fbl = ((EEVEE_Data *)vedata)->fbl;
	EEVEE_EffectsInfo *effects = stl->effects;
	EEVEE_ViewLayerData *sldata = EEVEE_view_layer_data_ensure();

	/* Default framebuffer and texture */
	DefaultTextureList *dtxl = DRW_viewport_texture_list_get();
	DefaultFramebufferList *dfbl = DRW_viewport_framebuffer_list_get();

	/* Sort transparents before the loop. */
	DRW_pass_sort_shgroup_z(psl->transparent_pass);

	/* Number of iteration: needed for all temporal effect (SSR, volumetrics)
	 * when using opengl render. */
	int loop_ct = (DRW_state_is_image_render() &&
	               (stl->effects->enabled_effects & (EFFECT_VOLUMETRIC | EFFECT_SSR)) != 0) ? 4 : 1;

	while (loop_ct--) {
		float clear_col[4] = {0.0f, 0.0f, 0.0f, 0.0f};
		float clear_depth = 1.0f;
		uint clear_stencil = 0xFF;
		uint primes[3] = {2, 3, 7};
		double offset[3] = {0.0, 0.0, 0.0};
		double r[3];

		bool taa_use_reprojection = (stl->effects->enabled_effects & EFFECT_TAA_REPROJECT) != 0;

		if (DRW_state_is_image_render() ||
		    taa_use_reprojection ||
		    ((stl->effects->enabled_effects & EFFECT_TAA) != 0))
		{
			int samp = taa_use_reprojection
			            ? stl->effects->taa_reproject_sample + 1
			            : stl->effects->taa_current_sample;
			BLI_halton_3D(primes, offset, samp, r);
			EEVEE_update_noise(psl, fbl, r);
			EEVEE_volumes_set_jitter(sldata, samp - 1);
			EEVEE_materials_init(sldata, stl, fbl);
		}
		/* Copy previous persmat to UBO data */
		copy_m4_m4(sldata->common_data.prev_persmat, stl->effects->prev_persmat);

		if (((stl->effects->enabled_effects & EFFECT_TAA) != 0) &&
		    (stl->effects->taa_current_sample > 1) &&
		    !DRW_state_is_image_render() &&
		    !taa_use_reprojection)
		{
			DRW_viewport_matrix_override_set(stl->effects->overide_persmat, DRW_MAT_PERS);
			DRW_viewport_matrix_override_set(stl->effects->overide_persinv, DRW_MAT_PERSINV);
			DRW_viewport_matrix_override_set(stl->effects->overide_winmat, DRW_MAT_WIN);
			DRW_viewport_matrix_override_set(stl->effects->overide_wininv, DRW_MAT_WININV);
		}

		/* Refresh Probes */
		DRW_stats_group_start("Probes Refresh");
		EEVEE_lightprobes_refresh(sldata, vedata);
		/* Probes refresh can have reset the current sample. */
		if (stl->effects->taa_current_sample == 1) {
			DRW_viewport_matrix_override_unset_all();
		}
		EEVEE_lightprobes_refresh_planar(sldata, vedata);
		DRW_stats_group_end();

		/* Update common buffer after probe rendering. */
		DRW_uniformbuffer_update(sldata->common_ubo, &sldata->common_data);

		/* Refresh shadows */
		DRW_stats_group_start("Shadows");
		EEVEE_draw_shadows(sldata, psl);
		DRW_stats_group_end();

		GPU_framebuffer_bind(fbl->main_fb);
		GPUFrameBufferBits clear_bits = GPU_DEPTH_BIT;
		clear_bits |= (DRW_state_draw_background()) ? 0 : GPU_COLOR_BIT;
		clear_bits |= ((stl->effects->enabled_effects & EFFECT_SSS) != 0) ? GPU_STENCIL_BIT : 0;
		GPU_framebuffer_clear(fbl->main_fb, clear_bits, clear_col, clear_depth, clear_stencil);

		/* Depth prepass */
		DRW_stats_group_start("Prepass");
		DRW_draw_pass(psl->depth_pass);
		DRW_draw_pass(psl->depth_pass_cull);
		DRW_stats_group_end();

		/* Create minmax texture */
		DRW_stats_group_start("Main MinMax buffer");
		EEVEE_create_minmax_buffer(vedata, dtxl->depth, -1);
		DRW_stats_group_end();

		EEVEE_occlusion_compute(sldata, vedata, dtxl->depth, -1);
		EEVEE_volumes_compute(sldata, vedata);

		/* Shading pass */
		DRW_stats_group_start("Shading");
		if (DRW_state_draw_background()) {
			DRW_draw_pass(psl->background_pass);
		}
		EEVEE_draw_default_passes(psl);
		DRW_draw_pass(psl->material_pass);
		EEVEE_subsurface_data_render(sldata, vedata);
		DRW_stats_group_end();

		/* Effects pre-transparency */
		EEVEE_subsurface_compute(sldata, vedata);
		EEVEE_reflection_compute(sldata, vedata);
		EEVEE_occlusion_draw_debug(sldata, vedata);
		DRW_draw_pass(psl->probe_display);
		EEVEE_refraction_compute(sldata, vedata);

		/* Opaque refraction */
		DRW_stats_group_start("Opaque Refraction");
		DRW_draw_pass(psl->refract_depth_pass);
		DRW_draw_pass(psl->refract_depth_pass_cull);
		DRW_draw_pass(psl->refract_pass);
		DRW_stats_group_end();

		/* Volumetrics Resolve Opaque */
		EEVEE_volumes_resolve(sldata, vedata);

		/* Transparent */
		DRW_draw_pass(psl->transparent_pass);

		/* Post Process */
		DRW_stats_group_start("Post FX");
		EEVEE_draw_effects(sldata, vedata);
		DRW_stats_group_end();

		if ((stl->effects->taa_current_sample > 1) && !DRW_state_is_image_render()) {
			DRW_viewport_matrix_override_unset_all();
		}
	}

	/* Tonemapping and transfer result to default framebuffer. */
	GPU_framebuffer_bind(dfbl->default_fb);
	DRW_transform_to_display(stl->effects->final_tx);

	/* Debug : Ouput buffer to view. */
	switch (G.debug_value) {
		case 1:
			if (txl->maxzbuffer) DRW_transform_to_display(txl->maxzbuffer);
			break;
		case 2:
			if (effects->ssr_pdf_output) DRW_transform_to_display(effects->ssr_pdf_output);
			break;
		case 3:
			if (effects->ssr_normal_input) DRW_transform_to_display(effects->ssr_normal_input);
			break;
		case 4:
			if (effects->ssr_specrough_input) DRW_transform_to_display(effects->ssr_specrough_input);
			break;
		case 5:
			if (txl->color_double_buffer) DRW_transform_to_display(txl->color_double_buffer);
			break;
		case 6:
			if (effects->gtao_horizons_debug) DRW_transform_to_display(effects->gtao_horizons_debug);
			break;
		case 7:
			if (effects->gtao_horizons) DRW_transform_to_display(effects->gtao_horizons);
			break;
		case 8:
			if (effects->sss_data) DRW_transform_to_display(effects->sss_data);
			break;
		case 9:
			if (effects->velocity_tx) DRW_transform_to_display(effects->velocity_tx);
			break;
		default:
			break;
	}

	EEVEE_volumes_free_smoke_textures();

	stl->g_data->view_updated = false;
}

static void eevee_view_update(void *vedata)
{
	EEVEE_StorageList *stl = ((EEVEE_Data *)vedata)->stl;
	if (stl->g_data) {
		stl->g_data->view_updated = true;
	}
}

static void eevee_id_object_update(void *UNUSED(vedata), Object *object)
{
	/* This is a bit mask of components which update is to be ignored. */
	const int ignore_updates = ID_RECALC_COLLECTIONS;
	const int allowed_updates = ~ignore_updates;
	EEVEE_LightProbeEngineData *ped = EEVEE_lightprobe_data_get(object);
	if (ped != NULL && (ped->engine_data.recalc & allowed_updates) != 0) {
		ped->need_full_update = true;
		ped->engine_data.recalc = 0;
	}
	EEVEE_LampEngineData *led = EEVEE_lamp_data_get(object);
	if (led != NULL && (led->engine_data.recalc & allowed_updates) != 0) {
		led->need_update = true;
		led->engine_data.recalc = 0;
	}
	EEVEE_ObjectEngineData *oedata = EEVEE_object_data_get(object);
	if (oedata != NULL && (oedata->engine_data.recalc & allowed_updates) != 0) {
		oedata->need_update = true;
		oedata->engine_data.recalc = 0;
	}
}

static void eevee_id_update(void *vedata, ID *id)
{
	/* Handle updates based on ID type. */
	switch (GS(id->name)) {
		case ID_OB:
			eevee_id_object_update(vedata, (Object *)id);
			break;
		default:
			/* pass */
			break;
	}
}

static void eevee_render_to_image(void *vedata, RenderEngine *engine, struct RenderLayer *render_layer, const rcti *rect)
{
	const DRWContextState *draw_ctx = DRW_context_state_get();
	EEVEE_render_init(vedata, engine, draw_ctx->depsgraph);

	DRW_render_object_iter(vedata, engine, draw_ctx->depsgraph, EEVEE_render_cache);

	/* Actually do the rendering. */
	EEVEE_render_draw(vedata, engine, render_layer, rect);
}

static void eevee_engine_free(void)
{
	EEVEE_bloom_free();
	EEVEE_depth_of_field_free();
	EEVEE_effects_free();
	EEVEE_lightprobes_free();
	EEVEE_lights_free();
	EEVEE_materials_free();
	EEVEE_mist_free();
	EEVEE_motion_blur_free();
	EEVEE_occlusion_free();
	EEVEE_screen_raytrace_free();
	EEVEE_subsurface_free();
	EEVEE_temporal_sampling_free();
	EEVEE_volumes_free();
}

static void eevee_layer_collection_settings_create(RenderEngine *UNUSED(engine), IDProperty *props)
{
	BLI_assert(props &&
	           props->type == IDP_GROUP &&
	           props->subtype == IDP_GROUP_SUB_ENGINE_RENDER);
	UNUSED_VARS_NDEBUG(props);
}

static void eevee_view_layer_settings_create(RenderEngine *UNUSED(engine), IDProperty *props)
{
	BLI_assert(props &&
	           props->type == IDP_GROUP &&
	           props->subtype == IDP_GROUP_SUB_ENGINE_RENDER);
	UNUSED_VARS_NDEBUG(props);
}

static const DrawEngineDataSize eevee_data_size = DRW_VIEWPORT_DATA_SIZE(EEVEE_Data);

DrawEngineType draw_engine_eevee_type = {
	NULL, NULL,
	N_("Eevee"),
	&eevee_data_size,
	&eevee_engine_init,
	&eevee_engine_free,
	&eevee_cache_init,
	&eevee_cache_populate,
	&eevee_cache_finish,
	&eevee_draw_background,
	NULL, /* Everything is drawn in the background pass (see comment on function) */
	&eevee_view_update,
	&eevee_id_update,
	&eevee_render_to_image,
};

RenderEngineType DRW_engine_viewport_eevee_type = {
	NULL, NULL,
	EEVEE_ENGINE, N_("Eevee"), RE_INTERNAL | RE_USE_SHADING_NODES | RE_USE_PREVIEW,
	NULL, &DRW_render_to_image, NULL, NULL, NULL, NULL,
	&EEVEE_render_update_passes,
	&eevee_layer_collection_settings_create,
	&eevee_view_layer_settings_create,
	&draw_engine_eevee_type,
	{NULL, NULL, NULL}
};


#undef EEVEE_ENGINE
