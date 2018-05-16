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

/** \file eevee_volumes.c
 *  \ingroup draw_engine
 *
 * Volumetric effects rendering using frostbite approach.
 */

#include "DRW_render.h"

#include "BLI_rand.h"
#include "BLI_string_utils.h"

#include "DNA_object_force_types.h"
#include "DNA_smoke_types.h"
#include "DNA_world_types.h"

#include "BKE_global.h" /* for G.debug_value */
#include "BKE_modifier.h"
#include "BKE_mesh.h"
#include "BKE_object.h"

#include "ED_screen.h"

#include "DEG_depsgraph_query.h"

#include "eevee_private.h"
#include "GPU_draw.h"
#include "GPU_texture.h"

static struct {
	char *volumetric_common_lib;
	char *volumetric_common_lamps_lib;

	struct GPUShader *volumetric_clear_sh;
	struct GPUShader *volumetric_scatter_sh;
	struct GPUShader *volumetric_scatter_with_lamps_sh;
	struct GPUShader *volumetric_integration_sh;
	struct GPUShader *volumetric_resolve_sh;

	GPUTexture *color_src;
	GPUTexture *depth_src;

	/* List of all smoke domains rendered within this frame. */
	ListBase smoke_domains;
} e_data = {NULL}; /* Engine data */

extern char datatoc_bsdf_common_lib_glsl[];
extern char datatoc_bsdf_direct_lib_glsl[];
extern char datatoc_common_uniforms_lib_glsl[];
extern char datatoc_common_view_lib_glsl[];
extern char datatoc_octahedron_lib_glsl[];
extern char datatoc_irradiance_lib_glsl[];
extern char datatoc_lamps_lib_glsl[];
extern char datatoc_volumetric_frag_glsl[];
extern char datatoc_volumetric_geom_glsl[];
extern char datatoc_volumetric_vert_glsl[];
extern char datatoc_volumetric_resolve_frag_glsl[];
extern char datatoc_volumetric_scatter_frag_glsl[];
extern char datatoc_volumetric_integration_frag_glsl[];
extern char datatoc_volumetric_lib_glsl[];
extern char datatoc_common_fullscreen_vert_glsl[];

static void eevee_create_shader_volumes(void)
{
	e_data.volumetric_common_lib = BLI_string_joinN(
	        datatoc_common_view_lib_glsl,
	        datatoc_common_uniforms_lib_glsl,
	        datatoc_bsdf_common_lib_glsl,
	        datatoc_volumetric_lib_glsl);

	e_data.volumetric_common_lamps_lib = BLI_string_joinN(
	        datatoc_common_view_lib_glsl,
	        datatoc_common_uniforms_lib_glsl,
	        datatoc_bsdf_common_lib_glsl,
	        datatoc_bsdf_direct_lib_glsl,
	        datatoc_octahedron_lib_glsl,
	        datatoc_irradiance_lib_glsl,
	        datatoc_lamps_lib_glsl,
	        datatoc_volumetric_lib_glsl);

	e_data.volumetric_clear_sh = DRW_shader_create_with_lib(
	        datatoc_volumetric_vert_glsl,
	        datatoc_volumetric_geom_glsl,
	        datatoc_volumetric_frag_glsl,
	        e_data.volumetric_common_lib,
	        "#define VOLUMETRICS\n"
	        "#define CLEAR\n");
	e_data.volumetric_scatter_sh = DRW_shader_create_with_lib(
	        datatoc_volumetric_vert_glsl,
	        datatoc_volumetric_geom_glsl,
	        datatoc_volumetric_scatter_frag_glsl,
	        e_data.volumetric_common_lamps_lib,
	        SHADER_DEFINES
	        "#define VOLUMETRICS\n"
	        "#define VOLUME_SHADOW\n");
	e_data.volumetric_scatter_with_lamps_sh = DRW_shader_create_with_lib(
	        datatoc_volumetric_vert_glsl,
	        datatoc_volumetric_geom_glsl,
	        datatoc_volumetric_scatter_frag_glsl,
	        e_data.volumetric_common_lamps_lib,
	        SHADER_DEFINES
	        "#define VOLUMETRICS\n"
	        "#define VOLUME_LIGHTING\n"
	        "#define VOLUME_SHADOW\n");
	e_data.volumetric_integration_sh = DRW_shader_create_with_lib(
	        datatoc_volumetric_vert_glsl,
	        datatoc_volumetric_geom_glsl,
	        datatoc_volumetric_integration_frag_glsl,
	        e_data.volumetric_common_lib, NULL);
	e_data.volumetric_resolve_sh = DRW_shader_create_with_lib(
	        datatoc_common_fullscreen_vert_glsl, NULL,
	        datatoc_volumetric_resolve_frag_glsl,
	        e_data.volumetric_common_lib, NULL);
}

void EEVEE_volumes_set_jitter(EEVEE_ViewLayerData *sldata, uint current_sample)
{
	EEVEE_CommonUniformBuffer *common_data = &sldata->common_data;

	double ht_point[3];
	double ht_offset[3] = {0.0, 0.0};
	uint ht_primes[3] = {3, 7, 2};

	BLI_halton_3D(ht_primes, ht_offset, current_sample, ht_point);

	common_data->vol_jitter[0] = (float)ht_point[0];
	common_data->vol_jitter[1] = (float)ht_point[1];
	common_data->vol_jitter[2] = (float)ht_point[2];
}

int EEVEE_volumes_init(EEVEE_ViewLayerData *sldata, EEVEE_Data *vedata)
{
	EEVEE_StorageList *stl = vedata->stl;
	EEVEE_FramebufferList *fbl = vedata->fbl;
	EEVEE_TextureList *txl = vedata->txl;
	EEVEE_EffectsInfo *effects = stl->effects;
	EEVEE_CommonUniformBuffer *common_data = &sldata->common_data;

	const DRWContextState *draw_ctx = DRW_context_state_get();
	const Scene *scene_eval = DEG_get_evaluated_scene(draw_ctx->depsgraph);

	const float *viewport_size = DRW_viewport_size_get();

	BLI_listbase_clear(&e_data.smoke_domains);

	if (scene_eval->eevee.flag & SCE_EEVEE_VOLUMETRIC_ENABLED) {

		/* Shaders */
		if (!e_data.volumetric_scatter_sh) {
			eevee_create_shader_volumes();
		}

		const int tile_size = scene_eval->eevee.volumetric_tile_size;

		/* Find Froxel Texture resolution. */
		int tex_size[3];

		tex_size[0] = (int)ceilf(fmaxf(1.0f, viewport_size[0] / (float)tile_size));
		tex_size[1] = (int)ceilf(fmaxf(1.0f, viewport_size[1] / (float)tile_size));
		tex_size[2] = max_ii(scene_eval->eevee.volumetric_samples, 1);

		common_data->vol_coord_scale[0] = viewport_size[0] / (float)(tile_size * tex_size[0]);
		common_data->vol_coord_scale[1] = viewport_size[1] / (float)(tile_size * tex_size[1]);

		/* TODO compute snap to maxZBuffer for clustered rendering */

		if ((common_data->vol_tex_size[0] != tex_size[0]) ||
		    (common_data->vol_tex_size[1] != tex_size[1]) ||
		    (common_data->vol_tex_size[2] != tex_size[2]))
		{
			DRW_TEXTURE_FREE_SAFE(txl->volume_prop_scattering);
			DRW_TEXTURE_FREE_SAFE(txl->volume_prop_extinction);
			DRW_TEXTURE_FREE_SAFE(txl->volume_prop_emission);
			DRW_TEXTURE_FREE_SAFE(txl->volume_prop_phase);
			DRW_TEXTURE_FREE_SAFE(txl->volume_scatter);
			DRW_TEXTURE_FREE_SAFE(txl->volume_transmittance);
			DRW_TEXTURE_FREE_SAFE(txl->volume_scatter_history);
			DRW_TEXTURE_FREE_SAFE(txl->volume_transmittance_history);
			GPU_FRAMEBUFFER_FREE_SAFE(fbl->volumetric_fb);
			GPU_FRAMEBUFFER_FREE_SAFE(fbl->volumetric_scat_fb);
			GPU_FRAMEBUFFER_FREE_SAFE(fbl->volumetric_integ_fb);
			common_data->vol_tex_size[0] = tex_size[0];
			common_data->vol_tex_size[1] = tex_size[1];
			common_data->vol_tex_size[2] = tex_size[2];

			common_data->vol_inv_tex_size[0] = 1.0f / (float)(tex_size[0]);
			common_data->vol_inv_tex_size[1] = 1.0f / (float)(tex_size[1]);
			common_data->vol_inv_tex_size[2] = 1.0f / (float)(tex_size[2]);
		}

		/* Like frostbite's paper, 5% blend of the new frame. */
		common_data->vol_history_alpha = (txl->volume_prop_scattering == NULL) ? 0.0f : 0.95f;

		if (txl->volume_prop_scattering == NULL) {
			/* Volume properties: We evaluate all volumetric objects
			 * and store their final properties into each froxel */
			txl->volume_prop_scattering = DRW_texture_create_3D(tex_size[0], tex_size[1], tex_size[2],
			                                                    GPU_R11F_G11F_B10F, DRW_TEX_FILTER, NULL);
			txl->volume_prop_extinction = DRW_texture_create_3D(tex_size[0], tex_size[1], tex_size[2],
			                                                    GPU_R11F_G11F_B10F, DRW_TEX_FILTER, NULL);
			txl->volume_prop_emission = DRW_texture_create_3D(tex_size[0], tex_size[1], tex_size[2],
			                                                  GPU_R11F_G11F_B10F, DRW_TEX_FILTER, NULL);
			txl->volume_prop_phase = DRW_texture_create_3D(tex_size[0], tex_size[1], tex_size[2],
			                                               GPU_RG16F, DRW_TEX_FILTER, NULL);

			/* Volume scattering: We compute for each froxel the
			 * Scattered light towards the view. We also resolve temporal
			 * super sampling during this stage. */
			txl->volume_scatter = DRW_texture_create_3D(tex_size[0], tex_size[1], tex_size[2],
			                                            GPU_R11F_G11F_B10F, DRW_TEX_FILTER, NULL);
			txl->volume_transmittance = DRW_texture_create_3D(tex_size[0], tex_size[1], tex_size[2],
			                                                  GPU_R11F_G11F_B10F, DRW_TEX_FILTER, NULL);

			/* Final integration: We compute for each froxel the
			 * amount of scattered light and extinction coef at this
			 * given depth. We use theses textures as double buffer
			 * for the volumetric history. */
			txl->volume_scatter_history = DRW_texture_create_3D(tex_size[0], tex_size[1], tex_size[2],
			                                                    GPU_R11F_G11F_B10F, DRW_TEX_FILTER, NULL);
			txl->volume_transmittance_history = DRW_texture_create_3D(tex_size[0], tex_size[1], tex_size[2],
			                                                          GPU_R11F_G11F_B10F, DRW_TEX_FILTER, NULL);
		}

		/* Temporal Super sampling jitter */
		uint ht_primes[3] = {3, 7, 2};
		uint current_sample = 0;

		/* If TAA is in use do not use the history buffer. */
		bool do_taa = ((effects->enabled_effects & EFFECT_TAA) != 0);

		if (draw_ctx->evil_C != NULL) {
			struct wmWindowManager *wm = CTX_wm_manager(draw_ctx->evil_C);
			do_taa = do_taa && (ED_screen_animation_no_scrub(wm) == NULL);
		}

		if (do_taa) {
			common_data->vol_history_alpha = 0.0f;
			current_sample = effects->taa_current_sample - 1;
			effects->volume_current_sample = -1;
		}
		else {
			const uint max_sample = (ht_primes[0] * ht_primes[1] * ht_primes[2]);
			current_sample = effects->volume_current_sample = (effects->volume_current_sample + 1) % max_sample;
			if (current_sample != max_sample - 1) {
				DRW_viewport_request_redraw();
			}
		}

		EEVEE_volumes_set_jitter(sldata, current_sample);

		/* Framebuffer setup */
		GPU_framebuffer_ensure_config(&fbl->volumetric_fb, {
			GPU_ATTACHMENT_NONE,
			GPU_ATTACHMENT_TEXTURE(txl->volume_prop_scattering),
			GPU_ATTACHMENT_TEXTURE(txl->volume_prop_extinction),
			GPU_ATTACHMENT_TEXTURE(txl->volume_prop_emission),
			GPU_ATTACHMENT_TEXTURE(txl->volume_prop_phase)
		});
		GPU_framebuffer_ensure_config(&fbl->volumetric_scat_fb, {
			GPU_ATTACHMENT_NONE,
			GPU_ATTACHMENT_TEXTURE(txl->volume_scatter),
			GPU_ATTACHMENT_TEXTURE(txl->volume_transmittance)
		});
		GPU_framebuffer_ensure_config(&fbl->volumetric_integ_fb, {
			GPU_ATTACHMENT_NONE,
			GPU_ATTACHMENT_TEXTURE(txl->volume_scatter_history),
			GPU_ATTACHMENT_TEXTURE(txl->volume_transmittance_history)
		});

		float integration_start = scene_eval->eevee.volumetric_start;
		float integration_end = scene_eval->eevee.volumetric_end;
		common_data->vol_light_clamp = scene_eval->eevee.volumetric_light_clamp;
		common_data->vol_shadow_steps = (float)scene_eval->eevee.volumetric_shadow_samples;
		if ((scene_eval->eevee.flag & SCE_EEVEE_VOLUMETRIC_SHADOWS) == 0) {
			common_data->vol_shadow_steps = 0;
		}

		if (DRW_viewport_is_persp_get()) {
			float sample_distribution = scene_eval->eevee.volumetric_sample_distribution;
			sample_distribution = 4.0f * (1.00001f - sample_distribution);

			const float clip_start = common_data->view_vecs[0][2];
			/* Negate */
			float near = integration_start = min_ff(-integration_start, clip_start - 1e-4f);
			float far = integration_end = min_ff(-integration_end, near - 1e-4f);

			common_data->vol_depth_param[0] = (far - near * exp2(1.0f / sample_distribution)) / (far - near);
			common_data->vol_depth_param[1] = (1.0f - common_data->vol_depth_param[0]) / near;
			common_data->vol_depth_param[2] = sample_distribution;
		}
		else {
			const float clip_start = common_data->view_vecs[0][2];
			const float clip_end = clip_start + common_data->view_vecs[1][2];
			integration_start = min_ff(integration_end, clip_start);
			integration_end = max_ff(-integration_end, clip_end);

			common_data->vol_depth_param[0] = integration_start;
			common_data->vol_depth_param[1] = integration_end;
			common_data->vol_depth_param[2] = 1.0f / (integration_end - integration_start);
		}

		/* Disable clamp if equal to 0. */
		if (common_data->vol_light_clamp == 0.0) {
			common_data->vol_light_clamp = FLT_MAX;
		}

		common_data->vol_use_lights = (scene_eval->eevee.flag & SCE_EEVEE_VOLUMETRIC_LIGHTS) != 0;

		return EFFECT_VOLUMETRIC | EFFECT_POST_BUFFER;
	}

	/* Cleanup to release memory */
	DRW_TEXTURE_FREE_SAFE(txl->volume_prop_scattering);
	DRW_TEXTURE_FREE_SAFE(txl->volume_prop_extinction);
	DRW_TEXTURE_FREE_SAFE(txl->volume_prop_emission);
	DRW_TEXTURE_FREE_SAFE(txl->volume_prop_phase);
	DRW_TEXTURE_FREE_SAFE(txl->volume_scatter);
	DRW_TEXTURE_FREE_SAFE(txl->volume_transmittance);
	DRW_TEXTURE_FREE_SAFE(txl->volume_scatter_history);
	DRW_TEXTURE_FREE_SAFE(txl->volume_transmittance_history);
	GPU_FRAMEBUFFER_FREE_SAFE(fbl->volumetric_fb);
	GPU_FRAMEBUFFER_FREE_SAFE(fbl->volumetric_scat_fb);
	GPU_FRAMEBUFFER_FREE_SAFE(fbl->volumetric_integ_fb);

	return 0;
}

void EEVEE_volumes_cache_init(EEVEE_ViewLayerData *sldata, EEVEE_Data *vedata)
{
	EEVEE_PassList *psl = vedata->psl;
	EEVEE_StorageList *stl = vedata->stl;
	EEVEE_TextureList *txl = vedata->txl;
	EEVEE_EffectsInfo *effects = stl->effects;
	EEVEE_CommonUniformBuffer *common_data = &sldata->common_data;

	if ((effects->enabled_effects & EFFECT_VOLUMETRIC) != 0) {
		const DRWContextState *draw_ctx = DRW_context_state_get();
		Scene *scene = draw_ctx->scene;
		DRWShadingGroup *grp = NULL;

		/* Quick breakdown of the Volumetric rendering:
		 *
		 * The rendering is separated in 4 stages:
		 *
		 * - Material Parameters : we collect volume properties of
		 *   all participating media in the scene and store them in
		 *   a 3D texture aligned with the 3D frustum.
		 *   This is done in 2 passes, one that clear the texture
		 *   and/or evaluate the world volumes, and the 2nd one that
		 *   additively render object volumes.
		 *
		 * - Light Scattering : the volume properties then are sampled
		 *   and light scattering is evaluated for each cell of the
		 *   volume texture. Temporal supersampling (if enabled) occurs here.
		 *
		 * - Volume Integration : the scattered light and extinction is
		 *   integrated (accumulated) along the viewrays. The result is stored
		 *   for every cell in another texture.
		 *
		 * - Fullscreen Resolve : From the previous stage, we get two
		 *   3D textures that contains integrated scatered light and extinction
		 *   for "every" positions in the frustum. We only need to sample
		 *   them and blend the scene color with thoses factors. This also
		 *   work for alpha blended materials.
		 **/

		/* World pass is not additive as it also clear the buffer. */
		psl->volumetric_world_ps = DRW_pass_create("Volumetric World", DRW_STATE_WRITE_COLOR);

		/* World Volumetric */
		struct World *wo = scene->world;
		if (wo != NULL && wo->use_nodes && wo->nodetree) {
			struct GPUMaterial *mat = EEVEE_material_world_volume_get(scene, wo);

			grp = DRW_shgroup_material_empty_tri_batch_create(mat,
			                                                  psl->volumetric_world_ps,
			                                                  common_data->vol_tex_size[2]);

			if (grp) {
				DRW_shgroup_uniform_block(grp, "common_block", sldata->common_ubo);
			}
		}

		if (grp == NULL) {
			/* If no world or volume material is present just clear the buffer with this drawcall */
			grp = DRW_shgroup_empty_tri_batch_create(e_data.volumetric_clear_sh,
				                                     psl->volumetric_world_ps,
				                                     common_data->vol_tex_size[2]);

			DRW_shgroup_uniform_block(grp, "common_block", sldata->common_ubo);
		}

		/* Volumetric Objects */
		psl->volumetric_objects_ps = DRW_pass_create("Volumetric Properties", DRW_STATE_WRITE_COLOR |
		                                                                      DRW_STATE_ADDITIVE);

		struct GPUShader *scatter_sh = (common_data->vol_use_lights) ? e_data.volumetric_scatter_with_lamps_sh
		                                                      : e_data.volumetric_scatter_sh;
		psl->volumetric_scatter_ps = DRW_pass_create("Volumetric Scattering", DRW_STATE_WRITE_COLOR);
		grp = DRW_shgroup_empty_tri_batch_create(scatter_sh, psl->volumetric_scatter_ps,
		                                         common_data->vol_tex_size[2]);
		DRW_shgroup_uniform_texture_ref(grp, "irradianceGrid", &sldata->irradiance_pool);
		DRW_shgroup_uniform_texture_ref(grp, "shadowCubeTexture", &sldata->shadow_cube_pool);
		DRW_shgroup_uniform_texture_ref(grp, "shadowCascadeTexture", &sldata->shadow_cascade_pool);
		DRW_shgroup_uniform_texture_ref(grp, "volumeScattering", &txl->volume_prop_scattering);
		DRW_shgroup_uniform_texture_ref(grp, "volumeExtinction", &txl->volume_prop_extinction);
		DRW_shgroup_uniform_texture_ref(grp, "volumeEmission", &txl->volume_prop_emission);
		DRW_shgroup_uniform_texture_ref(grp, "volumePhase", &txl->volume_prop_phase);
		DRW_shgroup_uniform_texture_ref(grp, "historyScattering", &txl->volume_scatter_history);
		DRW_shgroup_uniform_texture_ref(grp, "historyTransmittance", &txl->volume_transmittance_history);
		DRW_shgroup_uniform_block(grp, "light_block", sldata->light_ubo);
		DRW_shgroup_uniform_block(grp, "shadow_block", sldata->shadow_ubo);
		DRW_shgroup_uniform_block(grp, "common_block", sldata->common_ubo);

		psl->volumetric_integration_ps = DRW_pass_create("Volumetric Integration", DRW_STATE_WRITE_COLOR);
		grp = DRW_shgroup_empty_tri_batch_create(e_data.volumetric_integration_sh,
		                                         psl->volumetric_integration_ps,
		                                         common_data->vol_tex_size[2]);
		DRW_shgroup_uniform_texture_ref(grp, "volumeScattering", &txl->volume_scatter);
		DRW_shgroup_uniform_texture_ref(grp, "volumeExtinction", &txl->volume_transmittance);
		DRW_shgroup_uniform_block(grp, "common_block", sldata->common_ubo);

		psl->volumetric_resolve_ps = DRW_pass_create("Volumetric Resolve", DRW_STATE_WRITE_COLOR);
		grp = DRW_shgroup_create(e_data.volumetric_resolve_sh, psl->volumetric_resolve_ps);
		DRW_shgroup_uniform_texture_ref(grp, "inScattering", &txl->volume_scatter);
		DRW_shgroup_uniform_texture_ref(grp, "inTransmittance", &txl->volume_transmittance);
		DRW_shgroup_uniform_texture_ref(grp, "inSceneColor", &e_data.color_src);
		DRW_shgroup_uniform_texture_ref(grp, "inSceneDepth", &e_data.depth_src);
		DRW_shgroup_uniform_block(grp, "common_block", sldata->common_ubo);
		DRW_shgroup_call_add(grp, DRW_cache_fullscreen_quad_get(), NULL);
	}
}

void EEVEE_volumes_cache_object_add(EEVEE_ViewLayerData *sldata, EEVEE_Data *vedata, Scene *scene, Object *ob)
{
	float *texcoloc = NULL;
	float *texcosize = NULL;
	struct ModifierData *md = NULL;
	Material *ma = give_current_material(ob, 1);

	if (ma == NULL) {
		return;
	}

	struct GPUMaterial *mat = EEVEE_material_mesh_volume_get(scene, ma);

	DRWShadingGroup *grp = DRW_shgroup_material_empty_tri_batch_create(mat, vedata->psl->volumetric_objects_ps, sldata->common_data.vol_tex_size[2]);

	/* If shader failed to compile or is currently compiling. */
	if (grp == NULL) {
		return;
	}

	/* Making sure it's updated. */
	invert_m4_m4(ob->imat, ob->obmat);

	BKE_mesh_texspace_get_reference((struct Mesh *)ob->data, NULL, &texcoloc, NULL, &texcosize);

	DRW_shgroup_uniform_block(grp, "common_block", sldata->common_ubo);
	DRW_shgroup_uniform_mat4(grp, "volumeObjectMatrix", ob->imat);
	DRW_shgroup_uniform_vec3(grp, "volumeOrcoLoc", texcoloc, 1);
	DRW_shgroup_uniform_vec3(grp, "volumeOrcoSize", texcosize, 1);

	/* Smoke Simulation */
	if (((ob->base_flag & BASE_FROMDUPLI) == 0) &&
	    (md = modifiers_findByType(ob, eModifierType_Smoke)) &&
	    (modifier_isEnabled(scene, md, eModifierMode_Realtime)))
	{
		SmokeModifierData *smd = (SmokeModifierData *)md;
		SmokeDomainSettings *sds = smd->domain;
		/* Don't show smoke before simulation starts, this could be made an option in the future. */
		const bool show_smoke = (CFRA >= sds->point_cache[0]->startframe);

		if (sds->fluid && show_smoke) {
			if (!sds->wt || !(sds->viewsettings & MOD_SMOKE_VIEW_SHOWBIG)) {
				GPU_create_smoke(smd, 0);
			}
			else if (sds->wt && (sds->viewsettings & MOD_SMOKE_VIEW_SHOWBIG)) {
				GPU_create_smoke(smd, 1);
			}
			BLI_addtail(&e_data.smoke_domains, BLI_genericNodeN(smd));
		}

		if (sds->tex != NULL) {
			DRW_shgroup_uniform_texture_ref(grp, "sampdensity", &sds->tex);
		}
		if (sds->tex_flame != NULL) {
			DRW_shgroup_uniform_texture_ref(grp, "sampflame", &sds->tex_flame);
		}

		/* Output is such that 0..1 maps to 0..1000K */
		DRW_shgroup_uniform_vec2(grp, "unftemperature", &sds->flame_ignition, 1);
	}
}

void EEVEE_volumes_compute(EEVEE_ViewLayerData *UNUSED(sldata), EEVEE_Data *vedata)
{
	EEVEE_PassList *psl = vedata->psl;
	EEVEE_TextureList *txl = vedata->txl;
	EEVEE_FramebufferList *fbl = vedata->fbl;
	EEVEE_StorageList *stl = vedata->stl;
	EEVEE_EffectsInfo *effects = stl->effects;
	if ((effects->enabled_effects & EFFECT_VOLUMETRIC) != 0) {
		DRW_stats_group_start("Volumetrics");

		/* Step 1: Participating Media Properties */
		GPU_framebuffer_bind(fbl->volumetric_fb);
		DRW_draw_pass(psl->volumetric_world_ps);
		DRW_draw_pass(psl->volumetric_objects_ps);

		/* Step 2: Scatter Light */
		GPU_framebuffer_bind(fbl->volumetric_scat_fb);
		DRW_draw_pass(psl->volumetric_scatter_ps);

		/* Step 3: Integration */
		GPU_framebuffer_bind(fbl->volumetric_integ_fb);
		DRW_draw_pass(psl->volumetric_integration_ps);

		/* Swap volume history buffers */
		SWAP(struct GPUFrameBuffer *, fbl->volumetric_scat_fb, fbl->volumetric_integ_fb);
		SWAP(GPUTexture *, txl->volume_scatter, txl->volume_scatter_history);
		SWAP(GPUTexture *, txl->volume_transmittance, txl->volume_transmittance_history);

		/* Restore */
		GPU_framebuffer_bind(fbl->main_fb);

		DRW_stats_group_end();
	}
}

void EEVEE_volumes_resolve(EEVEE_ViewLayerData *UNUSED(sldata), EEVEE_Data *vedata)
{
	EEVEE_PassList *psl = vedata->psl;
	EEVEE_TextureList *txl = vedata->txl;
	EEVEE_FramebufferList *fbl = vedata->fbl;
	EEVEE_StorageList *stl = vedata->stl;
	EEVEE_EffectsInfo *effects = stl->effects;

	if ((effects->enabled_effects & EFFECT_VOLUMETRIC) != 0) {
		DefaultTextureList *dtxl = DRW_viewport_texture_list_get();

		e_data.color_src = txl->color;
		e_data.depth_src = dtxl->depth;

		/* Step 4: Apply for opaque */
		GPU_framebuffer_bind(fbl->effect_color_fb);
		DRW_draw_pass(psl->volumetric_resolve_ps);

		/* Swap the buffers and rebind depth to the current buffer */
		SWAP(GPUFrameBuffer *, fbl->main_fb, fbl->effect_fb);
		SWAP(GPUFrameBuffer *, fbl->main_color_fb, fbl->effect_color_fb);
		SWAP(GPUTexture *, txl->color, txl->color_post);

		/* Restore */
		GPU_framebuffer_texture_detach(fbl->effect_fb, dtxl->depth);
		GPU_framebuffer_texture_attach(fbl->main_fb, dtxl->depth, 0, 0);
		GPU_framebuffer_bind(fbl->main_fb);
	}
}

void EEVEE_volumes_free_smoke_textures(void)
{
	/* Free Smoke Textures after rendering */
	for (LinkData *link = e_data.smoke_domains.first; link; link = link->next) {
		SmokeModifierData *smd = (SmokeModifierData *)link->data;
		GPU_free_smoke(smd);
	}
	BLI_freelistN(&e_data.smoke_domains);
}

void EEVEE_volumes_free(void)
{
	MEM_SAFE_FREE(e_data.volumetric_common_lib);
	MEM_SAFE_FREE(e_data.volumetric_common_lamps_lib);

	DRW_SHADER_FREE_SAFE(e_data.volumetric_clear_sh);
	DRW_SHADER_FREE_SAFE(e_data.volumetric_scatter_sh);
	DRW_SHADER_FREE_SAFE(e_data.volumetric_scatter_with_lamps_sh);
	DRW_SHADER_FREE_SAFE(e_data.volumetric_integration_sh);
	DRW_SHADER_FREE_SAFE(e_data.volumetric_resolve_sh);
}
