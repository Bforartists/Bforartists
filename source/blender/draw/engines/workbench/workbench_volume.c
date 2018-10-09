/*
 * Copyright 2018, Blender Foundation.
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

/** \file workbench_volume.c
 *  \ingroup draw_engine
 */

#include "workbench_private.h"

#include "BKE_modifier.h"

#include "DNA_modifier_types.h"
#include "DNA_object_force_types.h"
#include "DNA_smoke_types.h"

#include "GPU_draw.h"

static struct {
	struct GPUShader *volume_sh;
	struct GPUShader *volume_coba_sh;
	struct GPUShader *volume_slice_sh;
	struct GPUShader *volume_slice_coba_sh;
	struct GPUTexture *dummy_tex;
	struct GPUTexture *dummy_coba_tex;
} e_data = {NULL};

extern char datatoc_workbench_volume_vert_glsl[];
extern char datatoc_workbench_volume_frag_glsl[];

void workbench_volume_engine_init(void)
{
	if (!e_data.volume_sh) {
		e_data.volume_sh = DRW_shader_create(
		        datatoc_workbench_volume_vert_glsl, NULL,
		        datatoc_workbench_volume_frag_glsl, NULL);
		e_data.volume_coba_sh = DRW_shader_create(
		        datatoc_workbench_volume_vert_glsl, NULL,
		        datatoc_workbench_volume_frag_glsl,
		        "#define USE_COBA\n");
		e_data.volume_slice_sh = DRW_shader_create(
		        datatoc_workbench_volume_vert_glsl, NULL,
		        datatoc_workbench_volume_frag_glsl,
		        "#define VOLUME_SLICE\n");
		e_data.volume_slice_coba_sh = DRW_shader_create(
		        datatoc_workbench_volume_vert_glsl, NULL,
		        datatoc_workbench_volume_frag_glsl,
		        "#define VOLUME_SLICE\n"
		        "#define USE_COBA\n");

		float pixel[4] = {0.0f, 0.0f, 0.0f, 0.0f};
		e_data.dummy_tex = GPU_texture_create_3D(1, 1, 1, GPU_RGBA8, pixel, NULL);
		e_data.dummy_coba_tex = GPU_texture_create_1D(1, GPU_RGBA8, pixel, NULL);
	}
}

void workbench_volume_engine_free(void)
{
	DRW_SHADER_FREE_SAFE(e_data.volume_sh);
	DRW_SHADER_FREE_SAFE(e_data.volume_coba_sh);
	DRW_SHADER_FREE_SAFE(e_data.volume_slice_sh);
	DRW_SHADER_FREE_SAFE(e_data.volume_slice_coba_sh);
	DRW_TEXTURE_FREE_SAFE(e_data.dummy_tex);
	DRW_TEXTURE_FREE_SAFE(e_data.dummy_coba_tex);
}

void workbench_volume_cache_init(WORKBENCH_Data *vedata)
{
	vedata->psl->volume_pass = DRW_pass_create("Volumes", DRW_STATE_WRITE_COLOR | DRW_STATE_TRANSMISSION | DRW_STATE_CULL_FRONT);
}

void workbench_volume_cache_populate(WORKBENCH_Data *vedata, Scene *scene, Object *ob, ModifierData *md)
{
	SmokeModifierData *smd = (SmokeModifierData *)md;
	SmokeDomainSettings *sds = smd->domain;
	WORKBENCH_PrivateData *wpd = vedata->stl->g_data;
	DefaultTextureList *dtxl = DRW_viewport_texture_list_get();
	DRWShadingGroup *grp = NULL;

	/* Don't show smoke before simulation starts, this could be made an option in the future. */
	if (!sds->fluid || CFRA < sds->point_cache[0]->startframe) {
		return;
	}

	wpd->volumes_do = true;
	if (sds->use_coba) {
		GPU_create_smoke_coba_field(smd);
	}
	else if (!sds->wt || !(sds->viewsettings & MOD_SMOKE_VIEW_SHOWBIG)) {
		GPU_create_smoke(smd, 0);
	}
	else if (sds->wt && (sds->viewsettings & MOD_SMOKE_VIEW_SHOWBIG)) {
		GPU_create_smoke(smd, 1);
	}

	if ((!sds->use_coba && sds->tex == NULL) ||
	    (sds->use_coba && sds->tex_field == NULL))
	{
		return;
	}

	const bool use_slice = (sds->slice_method == MOD_SMOKE_SLICE_AXIS_ALIGNED &&
	                        sds->axis_slice_method == AXIS_SLICE_SINGLE);

	if (use_slice) {
		float invviewmat[4][4];
		DRW_viewport_matrix_get(invviewmat, DRW_MAT_VIEWINV);

		const int axis = (sds->slice_axis == SLICE_AXIS_AUTO)
		                  ? axis_dominant_v3_single(invviewmat[2])
		                  : sds->slice_axis - 1;

		GPUShader *sh = (sds->use_coba) ? e_data.volume_slice_coba_sh : e_data.volume_slice_sh;
		grp = DRW_shgroup_create(sh, vedata->psl->volume_pass);
		DRW_shgroup_uniform_float_copy(grp, "slicePosition", sds->slice_depth);
		DRW_shgroup_uniform_int_copy(grp, "sliceAxis", axis);
	}
	else {
		int max_slices = max_iii(sds->res[0], sds->res[1], sds->res[2]) * sds->slice_per_voxel;

		GPUShader *sh = (sds->use_coba) ? e_data.volume_coba_sh : e_data.volume_sh;
		grp = DRW_shgroup_create(sh, vedata->psl->volume_pass);
		DRW_shgroup_uniform_vec4(grp, "viewvecs[0]", (float *)wpd->viewvecs, 3);
		DRW_shgroup_uniform_int_copy(grp, "samplesLen", max_slices);
		/* TODO FIXME : This step size is in object space but the ray itself
		 * is NOT unit length in object space so the required number of subdivisions
		 * is tricky to get. */
		DRW_shgroup_uniform_float_copy(grp, "stepLength", 8.0f / max_slices);
	}

	if (sds->use_coba) {
		DRW_shgroup_uniform_texture(grp, "densityTexture", sds->tex_field);
		DRW_shgroup_uniform_texture(grp, "transferTexture", sds->tex_coba);
	}
	else {
		DRW_shgroup_uniform_texture(grp, "densityTexture", sds->tex);
		DRW_shgroup_uniform_texture(grp, "shadowTexture", sds->tex_shadow);
		DRW_shgroup_uniform_texture(grp, "flameTexture", (sds->tex_flame) ? sds->tex_flame : e_data.dummy_tex);
		DRW_shgroup_uniform_texture(grp, "flameColorTexture", (sds->tex_flame) ? sds->tex_flame_coba : e_data.dummy_coba_tex);
	}
	DRW_shgroup_uniform_texture_ref(grp, "depthBuffer", &dtxl->depth);
	DRW_shgroup_uniform_float_copy(grp, "densityScale", 10.0f * sds->display_thickness);
	DRW_shgroup_state_disable(grp, DRW_STATE_CULL_FRONT);

	if (use_slice) {
		DRW_shgroup_call_object_add(grp, DRW_cache_quad_get(), ob);
	}
	else {
		DRW_shgroup_call_object_add(grp, DRW_cache_cube_get(), ob);
	}

	BLI_addtail(&wpd->smoke_domains, BLI_genericNodeN(smd));
}

void workbench_volume_smoke_textures_free(WORKBENCH_PrivateData *wpd)
{
	/* Free Smoke Textures after rendering */
	/* XXX This is a waste of processing and GPU bandwidth if nothing
	 * is updated. But the problem is since Textures are stored in the
	 * modifier we don't want them to take precious VRAM if the
	 * modifier is not used for display. We should share them for
	 * all viewport in a redraw at least. */
	for (LinkData *link = wpd->smoke_domains.first; link; link = link->next) {
		SmokeModifierData *smd = (SmokeModifierData *)link->data;
		GPU_free_smoke(smd);
	}
	BLI_freelistN(&wpd->smoke_domains);
}
