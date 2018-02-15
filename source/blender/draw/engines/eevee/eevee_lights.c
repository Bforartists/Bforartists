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

/** \file eevee_lights.c
 *  \ingroup DNA
 */

#include "DRW_render.h"

#include "BLI_dynstr.h"

#include "BKE_object.h"

#include "eevee_engine.h"
#include "eevee_private.h"

#define SHADOW_CASTER_ALLOC_CHUNK 16

static struct {
	struct GPUShader *shadow_sh;
	struct GPUShader *shadow_store_cube_sh[SHADOW_METHOD_MAX];
	struct GPUShader *shadow_store_cascade_sh[SHADOW_METHOD_MAX];
	struct GPUShader *shadow_copy_cube_sh[SHADOW_METHOD_MAX];
	struct GPUShader *shadow_copy_cascade_sh[SHADOW_METHOD_MAX];
} e_data = {NULL}; /* Engine data */

extern char datatoc_shadow_vert_glsl[];
extern char datatoc_shadow_geom_glsl[];
extern char datatoc_shadow_frag_glsl[];
extern char datatoc_shadow_store_frag_glsl[];
extern char datatoc_shadow_copy_frag_glsl[];
extern char datatoc_concentric_samples_lib_glsl[];

/* Prototype */
static void eevee_light_setup(Object *ob, EEVEE_Light *evli);

/* *********** LIGHT BITS *********** */
static void lightbits_set_single(EEVEE_LightBits *bitf, unsigned int idx, bool val)
{
	if (val) {
		bitf->fields[idx / 8] |=  (1 << (idx % 8));
	}
	else {
		bitf->fields[idx / 8] &= ~(1 << (idx % 8));
	}
}

static void lightbits_set_all(EEVEE_LightBits *bitf, bool val)
{
	memset(bitf, (val) ? 0xFF : 0x00, sizeof(EEVEE_LightBits));
}

static void lightbits_or(EEVEE_LightBits *r, const EEVEE_LightBits *v)
{
	for (int i = 0; i < MAX_LIGHTBITS_FIELDS; ++i) {
		r->fields[i] |= v->fields[i];
	}
}

static bool lightbits_get(const EEVEE_LightBits *r, unsigned int idx)
{
	return r->fields[idx / 8] & (1 << (idx % 8));
}

static void lightbits_convert(EEVEE_LightBits *r, const EEVEE_LightBits *bitf, const int *light_bit_conv_table, unsigned int table_length)
{
	for (int i = 0; i < table_length; ++i) {
		if (lightbits_get(bitf, i) != 0) {
			if (light_bit_conv_table[i] >= 0) {
				r->fields[i / 8] |= (1 << (i % 8));
			}
		}
	}
}

/* *********** FUNCTIONS *********** */

void EEVEE_lights_init(EEVEE_ViewLayerData *sldata)
{
	const unsigned int shadow_ubo_size = sizeof(EEVEE_Shadow) * MAX_SHADOW +
	                                     sizeof(EEVEE_ShadowCube) * MAX_SHADOW_CUBE +
	                                     sizeof(EEVEE_ShadowCascade) * MAX_SHADOW_CASCADE;

	const DRWContextState *draw_ctx = DRW_context_state_get();
	ViewLayer *view_layer = draw_ctx->view_layer;
	IDProperty *props = BKE_view_layer_engine_evaluated_get(view_layer, COLLECTION_MODE_NONE, RE_engine_id_BLENDER_EEVEE);

	if (!e_data.shadow_sh) {
		e_data.shadow_sh = DRW_shader_create(
		        datatoc_shadow_vert_glsl, datatoc_shadow_geom_glsl, datatoc_shadow_frag_glsl, NULL);

		DynStr *ds_frag = BLI_dynstr_new();
		BLI_dynstr_append(ds_frag, datatoc_concentric_samples_lib_glsl);
		BLI_dynstr_append(ds_frag, datatoc_shadow_store_frag_glsl);
		char *store_shadow_shader_str = BLI_dynstr_get_cstring(ds_frag);
		BLI_dynstr_free(ds_frag);

		e_data.shadow_store_cube_sh[SHADOW_ESM] = DRW_shader_create_fullscreen(
		        store_shadow_shader_str,
		        "#define ESM\n");
		e_data.shadow_store_cascade_sh[SHADOW_ESM] = DRW_shader_create_fullscreen(
		        store_shadow_shader_str,
		        "#define ESM\n"
		        "#define CSM\n");

		e_data.shadow_store_cube_sh[SHADOW_VSM] = DRW_shader_create_fullscreen(
		        store_shadow_shader_str,
		        "#define VSM\n");
		e_data.shadow_store_cascade_sh[SHADOW_VSM] = DRW_shader_create_fullscreen(
		        store_shadow_shader_str,
		        "#define VSM\n"
		        "#define CSM\n");

		MEM_freeN(store_shadow_shader_str);

		e_data.shadow_copy_cube_sh[SHADOW_ESM] = DRW_shader_create_fullscreen(
		        datatoc_shadow_copy_frag_glsl,
		        "#define ESM\n"
		        "#define COPY\n");
		e_data.shadow_copy_cascade_sh[SHADOW_ESM] = DRW_shader_create_fullscreen(
		        datatoc_shadow_copy_frag_glsl,
		        "#define ESM\n"
		        "#define COPY\n"
		        "#define CSM\n");

		e_data.shadow_copy_cube_sh[SHADOW_VSM] = DRW_shader_create_fullscreen(
		        datatoc_shadow_copy_frag_glsl,
		        "#define VSM\n"
		        "#define COPY\n");
		e_data.shadow_copy_cascade_sh[SHADOW_VSM] = DRW_shader_create_fullscreen(
		        datatoc_shadow_copy_frag_glsl,
		        "#define VSM\n"
		        "#define COPY\n"
		        "#define CSM\n");
	}

	if (!sldata->lamps) {
		sldata->lamps              = MEM_callocN(sizeof(EEVEE_LampsInfo), "EEVEE_LampsInfo");
		sldata->light_ubo          = DRW_uniformbuffer_create(sizeof(EEVEE_Light) * MAX_LIGHT, NULL);
		sldata->shadow_ubo         = DRW_uniformbuffer_create(shadow_ubo_size, NULL);
		sldata->shadow_render_ubo  = DRW_uniformbuffer_create(sizeof(EEVEE_ShadowRender), NULL);

		for (int i = 0; i < 2; ++i) {
			sldata->shcasters_buffers[i].shadow_casters = MEM_callocN(sizeof(EEVEE_ShadowCaster) * SHADOW_CASTER_ALLOC_CHUNK, "EEVEE_ShadowCaster buf");
			sldata->shcasters_buffers[i].flags = MEM_callocN(sizeof(sldata->shcasters_buffers[0].flags) * SHADOW_CASTER_ALLOC_CHUNK, "EEVEE_shcast_buffer flags buf");
			sldata->shcasters_buffers[i].alloc_count = SHADOW_CASTER_ALLOC_CHUNK;
			sldata->shcasters_buffers[i].count = 0;
		}

		sldata->lamps->shcaster_frontbuffer = &sldata->shcasters_buffers[0];
		sldata->lamps->shcaster_backbuffer = &sldata->shcasters_buffers[1];
	}

	/* Flip buffers */
	SWAP(EEVEE_ShadowCasterBuffer *, sldata->lamps->shcaster_frontbuffer, sldata->lamps->shcaster_backbuffer);

	int sh_method = BKE_collection_engine_property_value_get_int(props, "shadow_method");
	int sh_size = BKE_collection_engine_property_value_get_int(props, "shadow_size");
	int sh_high_bitdepth = BKE_collection_engine_property_value_get_int(props, "shadow_high_bitdepth");

	EEVEE_LampsInfo *linfo = sldata->lamps;
	if ((linfo->shadow_size != sh_size) ||
	    (linfo->shadow_method != sh_method) ||
	    (linfo->shadow_high_bitdepth != sh_high_bitdepth))
	{
		BLI_assert((sh_size > 0) && (sh_size <= 8192));
		DRW_TEXTURE_FREE_SAFE(sldata->shadow_pool);
		DRW_TEXTURE_FREE_SAFE(sldata->shadow_cube_target);
		DRW_TEXTURE_FREE_SAFE(sldata->shadow_cascade_target);
		DRW_TEXTURE_FREE_SAFE(sldata->shadow_cube_blur);
		DRW_TEXTURE_FREE_SAFE(sldata->shadow_cascade_blur);

		linfo->shadow_high_bitdepth = sh_high_bitdepth;
		linfo->shadow_method = sh_method;
		linfo->shadow_size = sh_size;
		linfo->shadow_render_data.stored_texel_size = 1.0 / (float)linfo->shadow_size;

		/* Compute adequate size for the cubemap render target.
		 * The 3.0f factor is here to make sure there is no under sampling between
		 * the octahedron mapping and the cubemap. */
		int new_cube_target_size = (int)ceil(sqrt((float)(sh_size * sh_size) / 6.0f) * 3.0f);

		CLAMP(new_cube_target_size, 1, 4096);

		linfo->shadow_cube_target_size = new_cube_target_size;
		linfo->shadow_render_data.cube_texel_size = 1.0 / (float)linfo->shadow_cube_target_size;
	}
}

void EEVEE_lights_cache_init(EEVEE_ViewLayerData *sldata, EEVEE_PassList *psl)
{
	EEVEE_LampsInfo *linfo = sldata->lamps;

	linfo->shcaster_frontbuffer->count = 0;
	linfo->num_light = 0;
	linfo->num_layer = 0;
	linfo->gpu_cube_ct = linfo->gpu_cascade_ct = linfo->gpu_shadow_ct = 0;
	linfo->cpu_cube_ct = linfo->cpu_cascade_ct = 0;
	memset(linfo->light_ref, 0, sizeof(linfo->light_ref));
	memset(linfo->shadow_cube_ref, 0, sizeof(linfo->shadow_cube_ref));
	memset(linfo->shadow_cascade_ref, 0, sizeof(linfo->shadow_cascade_ref));
	memset(linfo->new_shadow_id, -1, sizeof(linfo->new_shadow_id));

	/* Shadow Casters: Reset flags. */
	memset(linfo->shcaster_backbuffer->flags, (char)SHADOW_CASTER_PRUNED, linfo->shcaster_backbuffer->alloc_count);
	memset(linfo->shcaster_frontbuffer->flags, 0x00, linfo->shcaster_frontbuffer->alloc_count);

	{
		psl->shadow_cube_store_pass = DRW_pass_create("Shadow Storage Pass", DRW_STATE_WRITE_COLOR);

		DRWShadingGroup *grp = DRW_shgroup_create(
		        e_data.shadow_store_cube_sh[linfo->shadow_method], psl->shadow_cube_store_pass);
		DRW_shgroup_uniform_buffer(grp, "shadowTexture", &sldata->shadow_cube_blur);
		DRW_shgroup_uniform_block(grp, "shadow_render_block", sldata->shadow_render_ubo);
		DRW_shgroup_uniform_float(grp, "shadowFilterSize", &linfo->filter_size, 1);
		DRW_shgroup_call_add(grp, DRW_cache_fullscreen_quad_get(), NULL);
	}

	{
		psl->shadow_cascade_store_pass = DRW_pass_create("Shadow Cascade Storage Pass", DRW_STATE_WRITE_COLOR);

		DRWShadingGroup *grp = DRW_shgroup_create(
		        e_data.shadow_store_cascade_sh[linfo->shadow_method], psl->shadow_cascade_store_pass);
		DRW_shgroup_uniform_buffer(grp, "shadowTexture", &sldata->shadow_cascade_blur);
		DRW_shgroup_uniform_block(grp, "shadow_render_block", sldata->shadow_render_ubo);
		DRW_shgroup_uniform_int(grp, "cascadeId", &linfo->current_shadow_cascade, 1);
		DRW_shgroup_uniform_float(grp, "shadowFilterSize", &linfo->filter_size, 1);
		DRW_shgroup_call_add(grp, DRW_cache_fullscreen_quad_get(), NULL);
	}

	{
		psl->shadow_cube_copy_pass = DRW_pass_create("Shadow Copy Pass", DRW_STATE_WRITE_COLOR);

		DRWShadingGroup *grp = DRW_shgroup_create(
		        e_data.shadow_copy_cube_sh[linfo->shadow_method], psl->shadow_cube_copy_pass);
		DRW_shgroup_uniform_buffer(grp, "shadowTexture", &sldata->shadow_cube_target);
		DRW_shgroup_uniform_block(grp, "shadow_render_block", sldata->shadow_render_ubo);
		DRW_shgroup_uniform_float(grp, "shadowFilterSize", &linfo->filter_size, 1);
		DRW_shgroup_uniform_int(grp, "faceId", &linfo->current_shadow_face, 1);
		DRW_shgroup_call_add(grp, DRW_cache_fullscreen_quad_get(), NULL);
	}

	{
		psl->shadow_cascade_copy_pass = DRW_pass_create("Shadow Cascade Copy Pass", DRW_STATE_WRITE_COLOR);

		DRWShadingGroup *grp = DRW_shgroup_create(
		        e_data.shadow_copy_cascade_sh[linfo->shadow_method], psl->shadow_cascade_copy_pass);
		DRW_shgroup_uniform_buffer(grp, "shadowTexture", &sldata->shadow_cascade_target);
		DRW_shgroup_uniform_block(grp, "shadow_render_block", sldata->shadow_render_ubo);
		DRW_shgroup_uniform_float(grp, "shadowFilterSize", &linfo->filter_size, 1);
		DRW_shgroup_uniform_int(grp, "cascadeId", &linfo->current_shadow_cascade, 1);
		DRW_shgroup_call_add(grp, DRW_cache_fullscreen_quad_get(), NULL);
	}

	{
		psl->shadow_cube_pass = DRW_pass_create(
		        "Shadow Cube Pass",
		        DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS);
	}

	{
		psl->shadow_cascade_pass = DRW_pass_create(
		        "Shadow Cascade Pass",
		        DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS);
	}
}

void EEVEE_lights_cache_add(EEVEE_ViewLayerData *sldata, Object *ob)
{
	EEVEE_LampsInfo *linfo = sldata->lamps;

	/* Step 1 find all lamps in the scene and setup them */
	if (linfo->num_light >= MAX_LIGHT) {
		printf("Too many lamps in the scene !!!\n");
	}
	else {
		Lamp *la = (Lamp *)ob->data;
		EEVEE_Light *evli = linfo->light_data + linfo->num_light;
		eevee_light_setup(ob, evli);

		/* We do not support shadowmaps for dupli lamps. */
		if ((ob->base_flag & BASE_FROMDUPLI) != 0) {
			linfo->num_light++;
			return;
		}

		EEVEE_LampEngineData *led = EEVEE_lamp_data_ensure(ob);

		/* Save previous shadow id. */
		int prev_cube_sh_id = led->prev_cube_shadow_id;

		/* Default light without shadows */
		led->data.ld.shadow_id = -1;
		led->prev_cube_shadow_id = -1;

		if (la->mode & (LA_SHAD_BUF | LA_SHAD_RAY)) {
			if (la->type == LA_SUN) {
				int sh_nbr = 1; /* TODO : MSM */
				int cascade_nbr = MAX_CASCADE_NUM; /* TODO : Custom cascade number */

				if ((linfo->gpu_cascade_ct + sh_nbr) <= MAX_SHADOW_CASCADE) {
					/* Save Light object. */
					linfo->shadow_cascade_ref[linfo->cpu_cascade_ct] = ob;

					/* Store indices. */
					EEVEE_ShadowCascadeData *data = &led->data.scad;
					data->shadow_id = linfo->gpu_shadow_ct;
					data->cascade_id = linfo->gpu_cascade_ct;
					data->layer_id = linfo->num_layer;

					/* Increment indices. */
					linfo->gpu_shadow_ct += 1;
					linfo->gpu_cascade_ct += sh_nbr;
					linfo->num_layer += sh_nbr * cascade_nbr;

					linfo->cpu_cascade_ct += 1;
				}
			}
			else if (la->type == LA_SPOT || la->type == LA_LOCAL || la->type == LA_AREA) {
				int sh_nbr = 1; /* TODO : MSM */

				if ((linfo->gpu_cube_ct + sh_nbr) <= MAX_SHADOW_CUBE) {
					/* Save Light object. */
					linfo->shadow_cube_ref[linfo->cpu_cube_ct] = ob;

					/* For light update tracking. */
					if ((prev_cube_sh_id >= 0) &&
					    (prev_cube_sh_id < linfo->shcaster_backbuffer->count))
					{
						linfo->new_shadow_id[prev_cube_sh_id] = linfo->cpu_cube_ct;
					}
					led->prev_cube_shadow_id = linfo->cpu_cube_ct;

					/* Saving lamp bounds for later. */
					BLI_assert(linfo->cpu_cube_ct >= 0 && linfo->cpu_cube_ct < MAX_LIGHT);
					copy_v3_v3(linfo->shadow_bounds[linfo->cpu_cube_ct].center, ob->obmat[3]);
					linfo->shadow_bounds[linfo->cpu_cube_ct].radius = la->clipend;

					EEVEE_ShadowCubeData *data = &led->data.scd;
					/* Store indices. */
					data->shadow_id = linfo->gpu_shadow_ct;
					data->cube_id = linfo->gpu_cube_ct;
					data->layer_id = linfo->num_layer;

					/* Increment indices. */
					linfo->gpu_shadow_ct += 1;
					linfo->gpu_cube_ct += sh_nbr;
					linfo->num_layer += sh_nbr;

					linfo->cpu_cube_ct += 1;
				}
			}
		}

		led->data.ld.light_id = linfo->num_light;
		linfo->light_ref[linfo->num_light] = ob;
		linfo->num_light++;
	}
}

/* Add a shadow caster to the shadowpasses */
void EEVEE_lights_cache_shcaster_add(
        EEVEE_ViewLayerData *sldata, EEVEE_PassList *psl, struct Gwn_Batch *geom, float (*obmat)[4])
{
	DRWShadingGroup *grp = DRW_shgroup_instance_create(e_data.shadow_sh, psl->shadow_cube_pass, geom, NULL);
	DRW_shgroup_uniform_block(grp, "shadow_render_block", sldata->shadow_render_ubo);
	DRW_shgroup_uniform_mat4(grp, "ShadowModelMatrix", (float *)obmat);
	DRW_shgroup_set_instance_count(grp, 6);

	grp = DRW_shgroup_instance_create(e_data.shadow_sh, psl->shadow_cascade_pass, geom, NULL);
	DRW_shgroup_uniform_block(grp, "shadow_render_block", sldata->shadow_render_ubo);
	DRW_shgroup_uniform_mat4(grp, "ShadowModelMatrix", (float *)obmat);
	DRW_shgroup_set_instance_count(grp, MAX_CASCADE_NUM);
}

void EEVEE_lights_cache_shcaster_material_add(
	EEVEE_ViewLayerData *sldata, EEVEE_PassList *psl, struct GPUMaterial *gpumat,
	struct Gwn_Batch *geom, struct Object *ob, float (*obmat)[4], float *alpha_threshold)
{
	DRWShadingGroup *grp = DRW_shgroup_material_instance_create(gpumat, psl->shadow_cube_pass, geom, ob, NULL);

	if (grp == NULL) return;

	DRW_shgroup_uniform_block(grp, "shadow_render_block", sldata->shadow_render_ubo);
	DRW_shgroup_uniform_mat4(grp, "ShadowModelMatrix", (float *)obmat);

	if (alpha_threshold != NULL)
		DRW_shgroup_uniform_float(grp, "alphaThreshold", alpha_threshold, 1);

	DRW_shgroup_set_instance_count(grp, 6);

	grp = DRW_shgroup_material_instance_create(gpumat, psl->shadow_cascade_pass, geom, ob, NULL);
	DRW_shgroup_uniform_block(grp, "shadow_render_block", sldata->shadow_render_ubo);
	DRW_shgroup_uniform_mat4(grp, "ShadowModelMatrix", (float *)obmat);

	if (alpha_threshold != NULL)
		DRW_shgroup_uniform_float(grp, "alphaThreshold", alpha_threshold, 1);

	DRW_shgroup_set_instance_count(grp, MAX_CASCADE_NUM);
}

/* Make that object update shadow casting lamps inside its influence bounding box. */
void EEVEE_lights_cache_shcaster_object_add(EEVEE_ViewLayerData *sldata, Object *ob)
{
	if ((ob->base_flag & BASE_FROMDUPLI) != 0) {
		/* TODO: Special case for dupli objects because we cannot save the object pointer. */
		return;
	}

	EEVEE_ObjectEngineData *oedata = EEVEE_object_data_ensure(ob);
	EEVEE_LampsInfo *linfo = sldata->lamps;
	EEVEE_ShadowCasterBuffer *backbuffer = linfo->shcaster_backbuffer;
	EEVEE_ShadowCasterBuffer *frontbuffer = linfo->shcaster_frontbuffer;
	int past_id = oedata->shadow_caster_id;

	/* Update flags in backbuffer. */
	if (past_id > -1 && past_id < backbuffer->count) {
		backbuffer->flags[past_id] &= ~SHADOW_CASTER_PRUNED;

		if (oedata->need_update) {
			backbuffer->flags[past_id] |= SHADOW_CASTER_UPDATED;
		}
	}

	/* Update id. */
	oedata->shadow_caster_id = frontbuffer->count++;

	/* Make sure shadow_casters is big enough. */
	if (oedata->shadow_caster_id >= frontbuffer->alloc_count) {
		frontbuffer->alloc_count += SHADOW_CASTER_ALLOC_CHUNK;
		frontbuffer->shadow_casters = MEM_reallocN(frontbuffer->shadow_casters, sizeof(EEVEE_ShadowCaster) * frontbuffer->alloc_count);
		frontbuffer->flags = MEM_reallocN(frontbuffer->flags, sizeof(EEVEE_ShadowCaster) * frontbuffer->alloc_count);
	}

	EEVEE_ShadowCaster *shcaster = frontbuffer->shadow_casters + oedata->shadow_caster_id;

	if (oedata->need_update) {
		frontbuffer->flags[oedata->shadow_caster_id] = SHADOW_CASTER_UPDATED;
	}

	/* Update World AABB in frontbuffer. */
	BoundBox *bb = BKE_object_boundbox_get(ob);
	float min[3], max[3];
	INIT_MINMAX(min, max);
	for (int i = 0; i < 8; ++i) {
		float vec[3];
		copy_v3_v3(vec, bb->vec[i]);
		mul_m4_v3(ob->obmat, vec);
		minmax_v3v3_v3(min, max, vec);
	}

	EEVEE_BoundBox *aabb = &shcaster->bbox;
	add_v3_v3v3(aabb->center, min, max);
	mul_v3_fl(aabb->center, 0.5f);
	sub_v3_v3v3(aabb->halfdim, aabb->center, max);

	aabb->halfdim[0] = fabsf(aabb->halfdim[0]);
	aabb->halfdim[1] = fabsf(aabb->halfdim[1]);
	aabb->halfdim[2] = fabsf(aabb->halfdim[2]);

	oedata->need_update = false;
}

void EEVEE_lights_cache_finish(EEVEE_ViewLayerData *sldata)
{
	EEVEE_LampsInfo *linfo = sldata->lamps;
	DRWTextureFormat shadow_pool_format = DRW_TEX_R_32;

	sldata->common_data.la_num_light = linfo->num_light;

	/* Setup enough layers. */
	/* Free textures if number mismatch. */
	if (linfo->num_layer != linfo->cache_num_layer) {
		DRW_TEXTURE_FREE_SAFE(sldata->shadow_pool);
		linfo->cache_num_layer = linfo->num_layer;
		linfo->update_flag |= LIGHT_UPDATE_SHADOW_CUBE;
	}

	switch (linfo->shadow_method) {
		case SHADOW_ESM: shadow_pool_format = ((linfo->shadow_high_bitdepth) ? DRW_TEX_R_32 : DRW_TEX_R_16); break;
		case SHADOW_VSM: shadow_pool_format = ((linfo->shadow_high_bitdepth) ? DRW_TEX_RG_32 : DRW_TEX_RG_16); break;
		default:
			BLI_assert(!"Incorrect Shadow Method");
			break;
	}

	if (!sldata->shadow_cube_target) {
		/* TODO render everything on the same 2d render target using clip planes and no Geom Shader. */
		/* Cubemaps */
		sldata->shadow_cube_target = DRW_texture_create_cube(
		        linfo->shadow_cube_target_size, DRW_TEX_DEPTH_24, 0, NULL);
		sldata->shadow_cube_blur = DRW_texture_create_cube(
		        linfo->shadow_cube_target_size, shadow_pool_format, DRW_TEX_FILTER, NULL);
	}

	if (!sldata->shadow_cascade_target) {
		/* CSM */
		sldata->shadow_cascade_target = DRW_texture_create_2D_array(
		        linfo->shadow_size, linfo->shadow_size, MAX_CASCADE_NUM, DRW_TEX_DEPTH_24, 0, NULL);
		sldata->shadow_cascade_blur = DRW_texture_create_2D_array(
		        linfo->shadow_size, linfo->shadow_size, MAX_CASCADE_NUM, shadow_pool_format, DRW_TEX_FILTER, NULL);
	}

	/* Initialize Textures Array first so DRW_framebuffer_init just bind them. */
	if (!sldata->shadow_pool) {
		/* All shadows fit in this array */
		sldata->shadow_pool = DRW_texture_create_2D_array(
		        linfo->shadow_size, linfo->shadow_size, max_ff(1, linfo->num_layer),
		        shadow_pool_format, DRW_TEX_FILTER, NULL);
	}

	/* Render FB */
	DRWFboTexture tex_cascade = {&sldata->shadow_cube_target, DRW_TEX_DEPTH_24, 0};
	DRW_framebuffer_init(&sldata->shadow_target_fb, &draw_engine_eevee_type,
	                     linfo->shadow_size, linfo->shadow_size,
	                     &tex_cascade, 1);

	/* Storage FB */
	DRWFboTexture tex_pool = {&sldata->shadow_pool, shadow_pool_format, DRW_TEX_FILTER};
	DRW_framebuffer_init(&sldata->shadow_store_fb, &draw_engine_eevee_type,
	                     linfo->shadow_size, linfo->shadow_size,
	                     &tex_pool, 1);

	/* Restore */
	DRW_framebuffer_texture_detach(sldata->shadow_cube_target);

	/* Update Lamps UBOs. */
	EEVEE_lights_update(sldata);
}

/* Update buffer with lamp data */
static void eevee_light_setup(Object *ob, EEVEE_Light *evli)
{
	Lamp *la = (Lamp *)ob->data;
	float mat[4][4], scale[3], power;

	/* Position */
	copy_v3_v3(evli->position, ob->obmat[3]);

	/* Color */
	copy_v3_v3(evli->color, &la->r);

	/* Influence Radius */
	evli->dist = la->dist;

	/* Vectors */
	normalize_m4_m4_ex(mat, ob->obmat, scale);
	copy_v3_v3(evli->forwardvec, mat[2]);
	normalize_v3(evli->forwardvec);
	negate_v3(evli->forwardvec);

	copy_v3_v3(evli->rightvec, mat[0]);
	normalize_v3(evli->rightvec);

	copy_v3_v3(evli->upvec, mat[1]);
	normalize_v3(evli->upvec);

	/* Spot size & blend */
	if (la->type == LA_SPOT) {
		evli->sizex = scale[0] / scale[2];
		evli->sizey = scale[1] / scale[2];
		evli->spotsize = cosf(la->spotsize * 0.5f);
		evli->spotblend = (1.0f - evli->spotsize) * la->spotblend;
		evli->radius = max_ff(0.001f, la->area_size);
	}
	else if (la->type == LA_AREA) {
		evli->sizex = max_ff(0.0001f, la->area_size * scale[0] * 0.5f);
		if (la->area_shape == LA_AREA_RECT) {
			evli->sizey = max_ff(0.0001f, la->area_sizey * scale[1] * 0.5f);
		}
		else {
			evli->sizey = max_ff(0.0001f, la->area_size * scale[1] * 0.5f);
		}
	}
	else {
		evli->radius = max_ff(0.001f, la->area_size);
	}

	/* Make illumination power constant */
	if (la->type == LA_AREA) {
		power = 1.0f / (evli->sizex * evli->sizey * 4.0f * M_PI) * /* 1/(w*h*Pi) */
		        80.0f; /* XXX : Empirical, Fit cycles power */
	}
	else if (la->type == LA_SPOT || la->type == LA_LOCAL) {
		power = 1.0f / (4.0f * evli->radius * evli->radius * M_PI * M_PI) * /* 1/(4*r²*Pi²) */
		        M_PI * M_PI * 10.0; /* XXX : Empirical, Fit cycles power */

		/* for point lights (a.k.a radius == 0.0) */
		// power = M_PI * M_PI * 0.78; /* XXX : Empirical, Fit cycles power */
	}
	else {
		power = 1.0f / (4.0f * evli->radius * evli->radius * M_PI * M_PI) * /* 1/(r²*Pi) */
		        12.5f; /* XXX : Empirical, Fit cycles power */
	}
	mul_v3_fl(evli->color, power * la->energy);

	/* Lamp Type */
	evli->lamptype = (float)la->type;

	/* No shadow by default */
	evli->shadowid = -1.0f;
}

static void eevee_shadow_cube_setup(Object *ob, EEVEE_LampsInfo *linfo, EEVEE_LampEngineData *led)
{
	EEVEE_ShadowCubeData *sh_data = &led->data.scd;
	EEVEE_Light *evli = linfo->light_data + sh_data->light_id;
	EEVEE_Shadow *ubo_data = linfo->shadow_data + sh_data->shadow_id;
	EEVEE_ShadowCube *cube_data = linfo->shadow_cube_data + sh_data->cube_id;
	Lamp *la = (Lamp *)ob->data;

	int sh_nbr = 1; /* TODO: MSM */

	for (int i = 0; i < sh_nbr; ++i) {
		/* TODO : choose MSM sample point here. */
		copy_v3_v3(cube_data->position, ob->obmat[3]);
	}

	ubo_data->bias = 0.05f * la->bias;
	ubo_data->near = la->clipsta;
	ubo_data->far = la->clipend;
	ubo_data->exp = (linfo->shadow_method == SHADOW_VSM) ? la->bleedbias : la->bleedexp;

	evli->shadowid = (float)(sh_data->shadow_id);
	ubo_data->shadow_start = (float)(sh_data->layer_id);
	ubo_data->data_start = (float)(sh_data->cube_id);
	ubo_data->multi_shadow_count = (float)(sh_nbr);
	ubo_data->shadow_blur = la->soft * 0.02f; /* Used by translucence shadowmap blur */

	ubo_data->contact_dist = (la->mode & LA_SHAD_CONTACT) ? la->contact_dist : 0.0f;
	ubo_data->contact_bias = 0.05f * la->contact_bias;
	ubo_data->contact_spread = la->contact_spread;
	ubo_data->contact_thickness = la->contact_thickness;
}

#define LERP(t, a, b) ((a) + (t) * ((b) - (a)))

static void frustum_min_bounding_sphere(const float corners[8][4], float r_center[3], float *r_radius)
{
#if 0 /* Simple solution but waist too much space. */
	float minvec[3], maxvec[3];

	/* compute the bounding box */
	INIT_MINMAX(minvec, maxvec);
	for (int i = 0; i < 8; ++i) {
		minmax_v3v3_v3(minvec, maxvec, corners[i]);
	}

	/* compute the bounding sphere of this box */
	r_radius = len_v3v3(minvec, maxvec) * 0.5f;
	add_v3_v3v3(r_center, minvec, maxvec);
	mul_v3_fl(r_center, 0.5f);
#else
	/* Make the bouding sphere always centered on the front diagonal */
	add_v3_v3v3(r_center, corners[4], corners[7]);
	mul_v3_fl(r_center, 0.5f);
	*r_radius = len_v3v3(corners[0], r_center);

	/* Search the largest distance between the sphere center
	 * and the front plane corners. */
	for (int i = 0; i < 4; ++i) {
		float rad = len_v3v3(corners[4 + i], r_center);
		if (rad > *r_radius) {
			*r_radius = rad;
		}
	}
#endif
}

static void eevee_shadow_cascade_setup(Object *ob, EEVEE_LampsInfo *linfo, EEVEE_LampEngineData *led)
{
	Lamp *la = (Lamp *)ob->data;

	/* Camera Matrices */
	float persmat[4][4], persinv[4][4];
	float viewprojmat[4][4], projinv[4][4];
	float view_near, view_far;
	float near_v[4] = {0.0f, 0.0f, -1.0f, 1.0f};
	float far_v[4] = {0.0f, 0.0f,  1.0f, 1.0f};
	bool is_persp = DRW_viewport_is_persp_get();
	DRW_viewport_matrix_get(persmat, DRW_MAT_PERS);
	invert_m4_m4(persinv, persmat);
	/* FIXME : Get near / far from Draw manager? */
	DRW_viewport_matrix_get(viewprojmat, DRW_MAT_WIN);
	invert_m4_m4(projinv, viewprojmat);
	mul_m4_v4(projinv, near_v);
	mul_m4_v4(projinv, far_v);
	view_near = near_v[2];
	view_far = far_v[2]; /* TODO: Should be a shadow parameter */
	if (is_persp) {
		view_near /= near_v[3];
		view_far /= far_v[3];
	}

	/* Lamps Matrices */
	float viewmat[4][4], projmat[4][4];
	int sh_nbr = 1; /* TODO : MSM */
	int cascade_nbr = la->cascade_count;

	EEVEE_ShadowCascadeData *sh_data = &led->data.scad;
	EEVEE_Light *evli = linfo->light_data + sh_data->light_id;
	EEVEE_Shadow *ubo_data = linfo->shadow_data + sh_data->shadow_id;
	EEVEE_ShadowCascade *cascade_data = linfo->shadow_cascade_data + sh_data->cascade_id;

	/* The technique consists into splitting
	 * the view frustum into several sub-frustum
	 * that are individually receiving one shadow map */

	float csm_start, csm_end;

	if (is_persp) {
		csm_start = view_near;
		csm_end = max_ff(view_far, -la->cascade_max_dist);
		/* Avoid artifacts */
		csm_end = min_ff(view_near, csm_end);
	}
	else {
		csm_start = -view_far;
		csm_end = view_far;
	}

	/* init near/far */
	for (int c = 0; c < MAX_CASCADE_NUM; ++c) {
		cascade_data->split_start[c] = csm_end;
		cascade_data->split_end[c] = csm_end;
	}

	/* Compute split planes */
	float splits_start_ndc[MAX_CASCADE_NUM];
	float splits_end_ndc[MAX_CASCADE_NUM];

	{
		/* Nearest plane */
		float p[4] = {1.0f, 1.0f, csm_start, 1.0f};
		/* TODO: we don't need full m4 multiply here */
		mul_m4_v4(viewprojmat, p);
		splits_start_ndc[0] = p[2];
		if (is_persp) {
			splits_start_ndc[0] /= p[3];
		}
	}

	{
		/* Farthest plane */
		float p[4] = {1.0f, 1.0f, csm_end, 1.0f};
		/* TODO: we don't need full m4 multiply here */
		mul_m4_v4(viewprojmat, p);
		splits_end_ndc[cascade_nbr - 1] = p[2];
		if (is_persp) {
			splits_end_ndc[cascade_nbr - 1] /= p[3];
		}
	}

	cascade_data->split_start[0] = csm_start;
	cascade_data->split_end[cascade_nbr - 1] = csm_end;

	for (int c = 1; c < cascade_nbr; ++c) {
		/* View Space */
		float linear_split = LERP(((float)(c) / (float)cascade_nbr), csm_start, csm_end);
		float exp_split = csm_start * powf(csm_end / csm_start, (float)(c) / (float)cascade_nbr);

		if (is_persp) {
			cascade_data->split_start[c] = LERP(la->cascade_exponent, linear_split, exp_split);
		}
		else {
			cascade_data->split_start[c] = linear_split;
		}
		cascade_data->split_end[c - 1] = cascade_data->split_start[c];

		/* Add some overlap for smooth transition */
		cascade_data->split_start[c] = LERP(la->cascade_fade, cascade_data->split_end[c - 1],
		                                    (c > 1) ? cascade_data->split_end[c - 2] : cascade_data->split_start[0]);

		/* NDC Space */
		{
			float p[4] = {1.0f, 1.0f, cascade_data->split_start[c], 1.0f};
			/* TODO: we don't need full m4 multiply here */
			mul_m4_v4(viewprojmat, p);
			splits_start_ndc[c] = p[2];

			if (is_persp) {
				splits_start_ndc[c] /= p[3];
			}
		}

		{
			float p[4] = {1.0f, 1.0f, cascade_data->split_end[c - 1], 1.0f};
			/* TODO: we don't need full m4 multiply here */
			mul_m4_v4(viewprojmat, p);
			splits_end_ndc[c - 1] = p[2];

			if (is_persp) {
				splits_end_ndc[c - 1] /= p[3];
			}
		}
	}

	/* Set last cascade split fade distance into the first split_start. */
	float prev_split = (cascade_nbr > 1) ? cascade_data->split_end[cascade_nbr - 2] : cascade_data->split_start[0];
	cascade_data->split_start[0] = LERP(la->cascade_fade, cascade_data->split_end[cascade_nbr - 1], prev_split);

	/* For each cascade */
	for (int c = 0; c < cascade_nbr; ++c) {
		/* Given 8 frustum corners */
		float corners[8][4] = {
			/* Near Cap */
			{-1.0f, -1.0f, splits_start_ndc[c], 1.0f},
			{ 1.0f, -1.0f, splits_start_ndc[c], 1.0f},
			{-1.0f,  1.0f, splits_start_ndc[c], 1.0f},
			{ 1.0f,  1.0f, splits_start_ndc[c], 1.0f},
			/* Far Cap */
			{-1.0f, -1.0f, splits_end_ndc[c], 1.0f},
			{ 1.0f, -1.0f, splits_end_ndc[c], 1.0f},
			{-1.0f,  1.0f, splits_end_ndc[c], 1.0f},
			{ 1.0f,  1.0f, splits_end_ndc[c], 1.0f}
		};

		/* Transform them into world space */
		for (int i = 0; i < 8; ++i) {
			mul_m4_v4(persinv, corners[i]);
			mul_v3_fl(corners[i], 1.0f / corners[i][3]);
			corners[i][3] = 1.0f;
		}


		/* Project them into light space */
		invert_m4_m4(viewmat, ob->obmat);
		normalize_v3(viewmat[0]);
		normalize_v3(viewmat[1]);
		normalize_v3(viewmat[2]);

		for (int i = 0; i < 8; ++i) {
			mul_m4_v4(viewmat, corners[i]);
		}

		float center[3];
		frustum_min_bounding_sphere(corners, center, &(sh_data->radius[c]));

		/* Snap projection center to nearest texel to cancel shimmering. */
		float shadow_origin[2], shadow_texco[2];
		/* Light to texture space. */
		mul_v2_v2fl(shadow_origin, center, linfo->shadow_size / (2.0f * sh_data->radius[c]));

		/* Find the nearest texel. */
		shadow_texco[0] = round(shadow_origin[0]);
		shadow_texco[1] = round(shadow_origin[1]);

		/* Compute offset. */
		sub_v2_v2(shadow_texco, shadow_origin);
		mul_v2_fl(shadow_texco, (2.0f * sh_data->radius[c]) / linfo->shadow_size); /* Texture to light space. */

		/* Apply offset. */
		add_v2_v2(center, shadow_texco);

		/* Expand the projection to cover frustum range */
		orthographic_m4(projmat,
		                center[0] - sh_data->radius[c],
		                center[0] + sh_data->radius[c],
		                center[1] - sh_data->radius[c],
		                center[1] + sh_data->radius[c],
		                la->clipsta, la->clipend);

		mul_m4_m4m4(sh_data->viewprojmat[c], projmat, viewmat);
		mul_m4_m4m4(cascade_data->shadowmat[c], texcomat, sh_data->viewprojmat[c]);
	}

	ubo_data->bias = 0.05f * la->bias;
	ubo_data->near = la->clipsta;
	ubo_data->far = la->clipend;
	ubo_data->exp = (linfo->shadow_method == SHADOW_VSM) ? la->bleedbias : la->bleedexp;

	evli->shadowid = (float)(sh_data->shadow_id);
	ubo_data->shadow_start = (float)(sh_data->layer_id);
	ubo_data->data_start = (float)(sh_data->cascade_id);
	ubo_data->multi_shadow_count = (float)(sh_nbr);
	ubo_data->shadow_blur = la->soft * 0.02f; /* Used by translucence shadowmap blur */

	ubo_data->contact_dist = (la->mode & LA_SHAD_CONTACT) ? la->contact_dist : 0.0f;
	ubo_data->contact_bias = 0.05f * la->contact_bias;
	ubo_data->contact_spread = la->contact_spread;
	ubo_data->contact_thickness = la->contact_thickness;
}

/* Used for checking if object is inside the shadow volume. */
static bool sphere_bbox_intersect(const EEVEE_BoundSphere *bs, const EEVEE_BoundBox *bb)
{
	/* We are testing using a rougher AABB vs AABB test instead of full AABB vs Sphere. */
	/* TODO test speed with AABB vs Sphere. */
	bool x = fabsf(bb->center[0] - bs->center[0]) <= (bb->halfdim[0] + bs->radius);
	bool y = fabsf(bb->center[1] - bs->center[1]) <= (bb->halfdim[1] + bs->radius);
	bool z = fabsf(bb->center[2] - bs->center[2]) <= (bb->halfdim[2] + bs->radius);

	return x && y && z;
}

void EEVEE_lights_update(EEVEE_ViewLayerData *sldata)
{
	EEVEE_LampsInfo *linfo = sldata->lamps;
	Object *ob;
	int i;
	char *flag;
	EEVEE_ShadowCaster *shcaster;
	EEVEE_BoundSphere *bsphere;
	EEVEE_ShadowCasterBuffer *frontbuffer = linfo->shcaster_frontbuffer;
	EEVEE_ShadowCasterBuffer *backbuffer = linfo->shcaster_backbuffer;

	EEVEE_LightBits update_bits = {{0}};
	if ((linfo->update_flag & LIGHT_UPDATE_SHADOW_CUBE) != 0) {
		/* Update all lights. */
		lightbits_set_all(&update_bits, true);
	}
	else {
		/* Search for deleted shadow casters and if shcaster WAS in shadow radius. */
		/* No need to run this if we already update all lamps. */
		EEVEE_LightBits past_bits = {{0}};
		EEVEE_LightBits curr_bits = {{0}};
		shcaster = backbuffer->shadow_casters;
		flag = backbuffer->flags;
		for (i = 0; i < backbuffer->count; ++i, ++flag, ++shcaster) {
			/* If the shadowcaster has been deleted or updated. */
			if (*flag != 0) {
				/* Add the lamps that were intersecting with its BBox. */
				lightbits_or(&past_bits, &shcaster->bits);
			}
		}
		/* Convert old bits to new bits and add result to final update bits. */
		/* NOTE: This might be overkill since all lights are tagged to refresh if
		 * the light count changes. */
		lightbits_convert(&curr_bits, &past_bits, linfo->new_shadow_id, MAX_LIGHT);
		lightbits_or(&update_bits, &curr_bits);
	}

	/* Search for updates in current shadow casters. */
	shcaster = frontbuffer->shadow_casters;
	flag = frontbuffer->flags;
	for (i = 0; i < frontbuffer->count; i++, flag++, shcaster++) {
		/* Run intersection checks to fill the bitfields. */
		bsphere = linfo->shadow_bounds;
		for (int j = 0; j < linfo->cpu_cube_ct; j++, bsphere++) {
			bool iter = sphere_bbox_intersect(bsphere, &shcaster->bbox);
			lightbits_set_single(&shcaster->bits, j, iter);
		}
		/* Only add to final bits if objects has been updated. */
		if (*flag != 0) {
			lightbits_or(&update_bits, &shcaster->bits);
		}
	}

	/* Setup shadow cube in UBO and tag for update if necessary. */
	for (i = 0; (i < MAX_SHADOW_CUBE) && (ob = linfo->shadow_cube_ref[i]); i++) {
		EEVEE_LampEngineData *led = EEVEE_lamp_data_ensure(ob);

		eevee_shadow_cube_setup(ob, linfo, led);
		if (lightbits_get(&update_bits, i) != 0) {
			led->need_update = true;
		}
	}

	/* Resize shcasters buffers if too big. */
	if (frontbuffer->alloc_count - frontbuffer->count > SHADOW_CASTER_ALLOC_CHUNK) {
		frontbuffer->alloc_count  = (frontbuffer->count / SHADOW_CASTER_ALLOC_CHUNK) * SHADOW_CASTER_ALLOC_CHUNK;
		frontbuffer->alloc_count += (frontbuffer->count % SHADOW_CASTER_ALLOC_CHUNK != 0) ? SHADOW_CASTER_ALLOC_CHUNK : 0;
		frontbuffer->shadow_casters = MEM_reallocN(frontbuffer->shadow_casters, sizeof(EEVEE_ShadowCaster) * frontbuffer->alloc_count);
		frontbuffer->flags = MEM_reallocN(frontbuffer->flags, sizeof(EEVEE_ShadowCaster) * frontbuffer->alloc_count);
	}
}

/* this refresh lamps shadow buffers */
void EEVEE_draw_shadows(EEVEE_ViewLayerData *sldata, EEVEE_PassList *psl)
{
	EEVEE_LampsInfo *linfo = sldata->lamps;
	Object *ob;
	int i;
	float clear_col[4] = {FLT_MAX};

	/* Cube Shadow Maps */
	DRW_stats_group_start("Cube Shadow Maps");
	DRW_framebuffer_texture_attach(sldata->shadow_target_fb, sldata->shadow_cube_target, 0, 0);
	/* Render each shadow to one layer of the array */
	for (i = 0; (ob = linfo->shadow_cube_ref[i]) && (i < MAX_SHADOW_CUBE); i++) {
		EEVEE_LampEngineData *led = EEVEE_lamp_data_ensure(ob);
		Lamp *la = (Lamp *)ob->data;

		float cube_projmat[4][4];
		perspective_m4(cube_projmat, -la->clipsta, la->clipsta, -la->clipsta, la->clipsta, la->clipsta, la->clipend);

		if (!led->need_update) {
			continue;
		}

		EEVEE_ShadowRender *srd = &linfo->shadow_render_data;
		EEVEE_ShadowCubeData *evscd = &led->data.scd;

		srd->clip_near = la->clipsta;
		srd->clip_far = la->clipend;
		copy_v3_v3(srd->position, ob->obmat[3]);
		for (int j = 0; j < 6; j++) {
			float tmp[4][4];

			unit_m4(tmp);
			negate_v3_v3(tmp[3], ob->obmat[3]);
			mul_m4_m4m4(srd->viewmat[j], cubefacemat[j], tmp);

			mul_m4_m4m4(srd->shadowmat[j], cube_projmat, srd->viewmat[j]);
		}
		DRW_uniformbuffer_update(sldata->shadow_render_ubo, srd);

		DRW_framebuffer_bind(sldata->shadow_target_fb);
		DRW_framebuffer_clear(true, true, false, clear_col, 1.0f);

		/* Render shadow cube */
		DRW_draw_pass(psl->shadow_cube_pass);

		/* 0.001f is arbitrary, but it should be relatively small so that filter size is not too big. */
		float filter_texture_size = la->soft * 0.001f;
		float filter_pixel_size = ceil(filter_texture_size / linfo->shadow_render_data.cube_texel_size);
		linfo->filter_size = linfo->shadow_render_data.cube_texel_size * ((filter_pixel_size > 1.0f) ? 1.5f : 0.0f);

		/* TODO: OPTI: Filter all faces in one/two draw call */
		for (linfo->current_shadow_face = 0;
		     linfo->current_shadow_face < 6;
		     linfo->current_shadow_face++)
		{
			/* Copy using a small 3x3 box filter */
			DRW_framebuffer_cubeface_attach(sldata->shadow_store_fb, sldata->shadow_cube_blur, 0, linfo->current_shadow_face, 0);
			DRW_framebuffer_bind(sldata->shadow_store_fb);
			DRW_draw_pass(psl->shadow_cube_copy_pass);
			DRW_framebuffer_texture_detach(sldata->shadow_cube_blur);
		}

		/* Push it to shadowmap array */

		/* Adjust constants if concentric samples change. */
		const float max_filter_size = 7.5f;
		const float previous_box_filter_size = 9.0f; /* Dunno why but that works. */
		const int max_sample = 256;

		if (filter_pixel_size > 2.0f) {
			linfo->filter_size = linfo->shadow_render_data.cube_texel_size * max_filter_size * previous_box_filter_size;
			filter_pixel_size = max_ff(0.0f, filter_pixel_size - 3.0f);
			/* Compute number of concentric samples. Depends directly on filter size. */
			float pix_size_sqr = filter_pixel_size * filter_pixel_size;
			srd->shadow_samples_ct = min_ii(max_sample, 4 + 8 * (int)filter_pixel_size + 4 * (int)(pix_size_sqr));
		}
		else {
			linfo->filter_size = 0.0f;
			srd->shadow_samples_ct = 4;
		}
		srd->shadow_inv_samples_ct = 1.0f / (float)srd->shadow_samples_ct;
		DRW_uniformbuffer_update(sldata->shadow_render_ubo, srd);

		DRW_framebuffer_texture_layer_attach(sldata->shadow_store_fb, sldata->shadow_pool, 0, evscd->layer_id, 0);
		DRW_framebuffer_bind(sldata->shadow_store_fb);
		DRW_draw_pass(psl->shadow_cube_store_pass);

		led->need_update = false;
	}
	linfo->update_flag &= ~LIGHT_UPDATE_SHADOW_CUBE;

	DRW_framebuffer_texture_detach(sldata->shadow_cube_target);
	DRW_stats_group_end();

	/* Cascaded Shadow Maps */
	DRW_stats_group_start("Cascaded Shadow Maps");
	DRW_framebuffer_texture_attach(sldata->shadow_target_fb, sldata->shadow_cascade_target, 0, 0);
	for (i = 0; (ob = linfo->shadow_cascade_ref[i]) && (i < MAX_SHADOW_CASCADE); i++) {
		EEVEE_LampEngineData *led = EEVEE_lamp_data_ensure(ob);
		Lamp *la = (Lamp *)ob->data;

		EEVEE_ShadowCascadeData *evscd = &led->data.scad;
		EEVEE_ShadowRender *srd = &linfo->shadow_render_data;

		eevee_shadow_cascade_setup(ob, linfo, led);

		srd->clip_near = la->clipsta;
		srd->clip_far = la->clipend;
		for (int j = 0; j < la->cascade_count; ++j) {
			copy_m4_m4(srd->shadowmat[j], evscd->viewprojmat[j]);
		}
		DRW_uniformbuffer_update(sldata->shadow_render_ubo, &linfo->shadow_render_data);

		DRW_framebuffer_bind(sldata->shadow_target_fb);
		DRW_framebuffer_clear(false, true, false, NULL, 1.0);

		/* Render shadow cascades */
		DRW_draw_pass(psl->shadow_cascade_pass);

		/* TODO: OPTI: Filter all cascade in one/two draw call */
		for (linfo->current_shadow_cascade = 0;
		     linfo->current_shadow_cascade < la->cascade_count;
		     ++linfo->current_shadow_cascade)
		{
			/* 0.01f factor to convert to percentage */
			float filter_texture_size = la->soft * 0.01f / evscd->radius[linfo->current_shadow_cascade];
			float filter_pixel_size = ceil(linfo->shadow_size * filter_texture_size);

			/* Copy using a small 3x3 box filter */
			linfo->filter_size = linfo->shadow_render_data.stored_texel_size * ((filter_pixel_size > 1.0f) ? 1.0f : 0.0f);
			DRW_framebuffer_texture_layer_attach(
			        sldata->shadow_store_fb, sldata->shadow_cascade_blur, 0, linfo->current_shadow_cascade, 0);
			DRW_framebuffer_bind(sldata->shadow_store_fb);
			DRW_draw_pass(psl->shadow_cascade_copy_pass);
			DRW_framebuffer_texture_detach(sldata->shadow_cascade_blur);

			/* Push it to shadowmap array and blur more */

			/* Adjust constants if concentric samples change. */
			const float max_filter_size = 7.5f;
			const float previous_box_filter_size = 3.2f; /* Arbitrary: less banding */
			const int max_sample = 256;

			if (filter_pixel_size > 2.0f) {
				linfo->filter_size = linfo->shadow_render_data.stored_texel_size * max_filter_size * previous_box_filter_size;
				filter_pixel_size = max_ff(0.0f, filter_pixel_size - 3.0f);
				/* Compute number of concentric samples. Depends directly on filter size. */
				float pix_size_sqr = filter_pixel_size * filter_pixel_size;
				srd->shadow_samples_ct = min_ii(max_sample, 4 + 8 * (int)filter_pixel_size + 4 * (int)(pix_size_sqr));
			}
			else {
				linfo->filter_size = 0.0f;
				srd->shadow_samples_ct = 4;
			}
			srd->shadow_inv_samples_ct = 1.0f / (float)srd->shadow_samples_ct;
			DRW_uniformbuffer_update(sldata->shadow_render_ubo, &linfo->shadow_render_data);

			int layer = evscd->layer_id + linfo->current_shadow_cascade;
			DRW_framebuffer_texture_layer_attach(sldata->shadow_store_fb, sldata->shadow_pool, 0, layer, 0);
			DRW_framebuffer_bind(sldata->shadow_store_fb);
			DRW_draw_pass(psl->shadow_cascade_store_pass);
		}
	}

	DRW_framebuffer_texture_detach(sldata->shadow_cascade_target);
	DRW_stats_group_end();

	DRW_uniformbuffer_update(sldata->light_ubo, &linfo->light_data);
	DRW_uniformbuffer_update(sldata->shadow_ubo, &linfo->shadow_data); /* Update all data at once */
}

void EEVEE_lights_free(void)
{
	DRW_SHADER_FREE_SAFE(e_data.shadow_sh);
	for (int i = 0; i < SHADOW_METHOD_MAX; ++i) {
		DRW_SHADER_FREE_SAFE(e_data.shadow_store_cube_sh[i]);
		DRW_SHADER_FREE_SAFE(e_data.shadow_store_cascade_sh[i]);
		DRW_SHADER_FREE_SAFE(e_data.shadow_copy_cube_sh[i]);
		DRW_SHADER_FREE_SAFE(e_data.shadow_copy_cascade_sh[i]);
	}
}
