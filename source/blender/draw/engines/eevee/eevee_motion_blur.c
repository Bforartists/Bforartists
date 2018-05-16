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

/** \file eevee_motion_blur.c
 *  \ingroup draw_engine
 *
 * Gather all screen space effects technique such as Bloom, Motion Blur, DoF, SSAO, SSR, ...
 */

#include "DRW_render.h"

#include "BKE_global.h" /* for G.debug_value */
#include "BKE_camera.h"
#include "BKE_object.h"
#include "BKE_animsys.h"
#include "BKE_screen.h"

#include "DNA_anim_types.h"
#include "DNA_camera_types.h"
#include "DNA_screen_types.h"

#include "ED_screen.h"

#include "DEG_depsgraph.h"
#include "DEG_depsgraph_query.h"

#include "eevee_private.h"
#include "GPU_texture.h"

static struct {
	/* Motion Blur */
	struct GPUShader *motion_blur_sh;
} e_data = {NULL}; /* Engine data */

extern char datatoc_effect_motion_blur_frag_glsl[];

static void eevee_motion_blur_camera_get_matrix_at_time(
        Scene *scene,
        ARegion *ar, RegionView3D *rv3d, View3D *v3d,
        Object *camera,
        float time,
        float r_mat[4][4])
{
	float obmat[4][4];

	/* HACK */
	Object cam_cpy; Camera camdata_cpy;
	memcpy(&cam_cpy, camera, sizeof(cam_cpy));
	memcpy(&camdata_cpy, camera->data, sizeof(camdata_cpy));
	cam_cpy.data = &camdata_cpy;

	const DRWContextState *draw_ctx = DRW_context_state_get();

	/* Past matrix */
	/* FIXME : This is a temporal solution that does not take care of parent animations */
	/* Recalc Anim manualy */
	BKE_animsys_evaluate_animdata(scene, &cam_cpy.id, cam_cpy.adt, time, ADT_RECALC_ALL);
	BKE_animsys_evaluate_animdata(scene, &camdata_cpy.id, camdata_cpy.adt, time, ADT_RECALC_ALL);
	BKE_object_where_is_calc_time(draw_ctx->depsgraph, scene, &cam_cpy, time);

	/* Compute winmat */
	CameraParams params;
	BKE_camera_params_init(&params);

	if (v3d != NULL) {
		BKE_camera_params_from_view3d(&params, draw_ctx->depsgraph, v3d, rv3d);
		BKE_camera_params_compute_viewplane(&params, ar->winx, ar->winy, 1.0f, 1.0f);
	}
	else {
		BKE_camera_params_from_object(&params, &cam_cpy);
		BKE_camera_params_compute_viewplane(&params, scene->r.xsch, scene->r.ysch, scene->r.xasp, scene->r.yasp);
	}

	BKE_camera_params_compute_matrix(&params);

	/* FIXME Should be done per view (MULTIVIEW) */
	normalize_m4_m4(obmat, cam_cpy.obmat);
	invert_m4(obmat);
	mul_m4_m4m4(r_mat, params.winmat, obmat);
}

static void eevee_create_shader_motion_blur(void)
{
	e_data.motion_blur_sh = DRW_shader_create_fullscreen(datatoc_effect_motion_blur_frag_glsl, NULL);
}

int EEVEE_motion_blur_init(EEVEE_ViewLayerData *UNUSED(sldata), EEVEE_Data *vedata, Object *camera)
{
	EEVEE_StorageList *stl = vedata->stl;
	EEVEE_EffectsInfo *effects = stl->effects;

	const DRWContextState *draw_ctx = DRW_context_state_get();
	const Scene *scene_eval = DEG_get_evaluated_scene(draw_ctx->depsgraph);
	Scene *scene = draw_ctx->scene;

	View3D *v3d = draw_ctx->v3d;
	RegionView3D *rv3d = draw_ctx->rv3d;
	ARegion *ar = draw_ctx->ar;

	if (scene_eval->eevee.flag & SCE_EEVEE_MOTION_BLUR_ENABLED) {
		/* Update Motion Blur Matrices */
		if (camera) {
			float persmat[4][4];
			float ctime = BKE_scene_frame_get(scene_eval);
			float delta = scene_eval->eevee.motion_blur_shutter;
			Object *camera_object = DEG_get_evaluated_object(draw_ctx->depsgraph, camera);

			/* Current matrix */
			eevee_motion_blur_camera_get_matrix_at_time(scene,
			                                            ar, rv3d, v3d,
			                                            camera_object,
			                                            ctime,
			                                            effects->current_ndc_to_world);

			/* Viewport Matrix */
			DRW_viewport_matrix_get(persmat, DRW_MAT_PERS);

			/* Only continue if camera is not being keyed */
			if (DRW_state_is_image_render() ||
			    compare_m4m4(persmat, effects->current_ndc_to_world, 0.0001f))
			{
				/* Past matrix */
				eevee_motion_blur_camera_get_matrix_at_time(scene,
				                                            ar, rv3d, v3d,
				                                            camera_object,
				                                            ctime - delta,
				                                            effects->past_world_to_ndc);

#if 0       /* for future high quality blur */
				/* Future matrix */
				eevee_motion_blur_camera_get_matrix_at_time(scene,
				                                            ar, rv3d, v3d,
				                                            camera_object,
				                                            ctime + delta,
				                                            effects->future_world_to_ndc);
#endif
				invert_m4(effects->current_ndc_to_world);

				effects->motion_blur_samples = scene_eval->eevee.motion_blur_samples;

				if (!e_data.motion_blur_sh) {
					eevee_create_shader_motion_blur();
				}

				return EFFECT_MOTION_BLUR | EFFECT_POST_BUFFER;
			}
		}
	}

	return 0;
}

void EEVEE_motion_blur_cache_init(EEVEE_ViewLayerData *UNUSED(sldata), EEVEE_Data *vedata)
{
	EEVEE_PassList *psl = vedata->psl;
	EEVEE_StorageList *stl = vedata->stl;
	EEVEE_EffectsInfo *effects = stl->effects;
	DefaultTextureList *dtxl = DRW_viewport_texture_list_get();

	struct Gwn_Batch *quad = DRW_cache_fullscreen_quad_get();

	if ((effects->enabled_effects & EFFECT_MOTION_BLUR) != 0) {
		psl->motion_blur = DRW_pass_create("Motion Blur", DRW_STATE_WRITE_COLOR);

		DRWShadingGroup *grp = DRW_shgroup_create(e_data.motion_blur_sh, psl->motion_blur);
		DRW_shgroup_uniform_int(grp, "samples", &effects->motion_blur_samples, 1);
		DRW_shgroup_uniform_mat4(grp, "currInvViewProjMatrix", effects->current_ndc_to_world);
		DRW_shgroup_uniform_mat4(grp, "pastViewProjMatrix", effects->past_world_to_ndc);
		DRW_shgroup_uniform_texture_ref(grp, "colorBuffer", &effects->source_buffer);
		DRW_shgroup_uniform_texture_ref(grp, "depthBuffer", &dtxl->depth);
		DRW_shgroup_call_add(grp, quad, NULL);
	}
}

void EEVEE_motion_blur_draw(EEVEE_Data *vedata)
{
	EEVEE_PassList *psl = vedata->psl;
	EEVEE_TextureList *txl = vedata->txl;
	EEVEE_FramebufferList *fbl = vedata->fbl;
	EEVEE_StorageList *stl = vedata->stl;
	EEVEE_EffectsInfo *effects = stl->effects;

	/* Motion Blur */
	if ((effects->enabled_effects & EFFECT_MOTION_BLUR) != 0) {
		GPU_framebuffer_bind(effects->target_buffer);
		DRW_draw_pass(psl->motion_blur);
		SWAP_BUFFERS();
	}
}

void EEVEE_motion_blur_free(void)
{
	DRW_SHADER_FREE_SAFE(e_data.motion_blur_sh);
}
