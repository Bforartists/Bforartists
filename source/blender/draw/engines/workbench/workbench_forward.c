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

/** \file workbench_forward.c
 *  \ingroup draw_engine
 */

#include "workbench_private.h"

#include "BIF_gl.h"

#include "BLI_alloca.h"
#include "BLI_dynstr.h"
#include "BLI_utildefines.h"

#include "BKE_node.h"
#include "BKE_particle.h"

#include "DNA_image_types.h"
#include "DNA_mesh_types.h"
#include "DNA_modifier_types.h"
#include "DNA_node_types.h"

#include "ED_uvedit.h"

#include "GPU_shader.h"
#include "GPU_texture.h"

#include "UI_resources.h"

/* *********** STATIC *********** */
static struct {
	struct GPUShader *composite_sh_cache[MAX_SHADERS];
	struct GPUShader *transparent_accum_sh_cache[MAX_SHADERS];
	struct GPUShader *object_outline_sh;
	struct GPUShader *object_outline_hair_sh;
	struct GPUShader *checker_depth_sh;

	struct GPUTexture *object_id_tx; /* ref only, not alloced */
	struct GPUTexture *transparent_accum_tx; /* ref only, not alloced */
	struct GPUTexture *transparent_revealage_tx; /* ref only, not alloced */
	struct GPUTexture *composite_buffer_tx; /* ref only, not alloced */
	int next_object_id;
	float normal_world_matrix[3][3];
} e_data = {{NULL}};

/* Shaders */
extern char datatoc_common_hair_lib_glsl[];
extern char datatoc_workbench_forward_composite_frag_glsl[];
extern char datatoc_workbench_forward_depth_frag_glsl[];
extern char datatoc_workbench_forward_transparent_accum_frag_glsl[];
extern char datatoc_workbench_data_lib_glsl[];
extern char datatoc_workbench_background_lib_glsl[];
extern char datatoc_workbench_checkerboard_depth_frag_glsl[];
extern char datatoc_workbench_object_outline_lib_glsl[];
extern char datatoc_workbench_prepass_vert_glsl[];
extern char datatoc_workbench_common_lib_glsl[];
extern char datatoc_workbench_world_light_lib_glsl[];

/* static functions */
static char *workbench_build_forward_depth_frag(void)
{
	char *str = NULL;

	DynStr *ds = BLI_dynstr_new();

	BLI_dynstr_append(ds, datatoc_workbench_common_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_forward_depth_frag_glsl);

	str = BLI_dynstr_get_cstring(ds);
	BLI_dynstr_free(ds);
	return str;
}

static char *workbench_build_forward_vert(void)
{
	char *str = NULL;

	DynStr *ds = BLI_dynstr_new();

	BLI_dynstr_append(ds, datatoc_common_hair_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_prepass_vert_glsl);

	str = BLI_dynstr_get_cstring(ds);
	BLI_dynstr_free(ds);
	return str;
}

static char *workbench_build_forward_transparent_accum_frag(void)
{
	char *str = NULL;

	DynStr *ds = BLI_dynstr_new();

	BLI_dynstr_append(ds, datatoc_workbench_data_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_common_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_world_light_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_forward_transparent_accum_frag_glsl);

	str = BLI_dynstr_get_cstring(ds);
	BLI_dynstr_free(ds);
	return str;
}

static char *workbench_build_forward_composite_frag(void)
{
	char *str = NULL;

	DynStr *ds = BLI_dynstr_new();

	BLI_dynstr_append(ds, datatoc_workbench_data_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_common_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_background_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_object_outline_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_forward_composite_frag_glsl);

	str = BLI_dynstr_get_cstring(ds);
	BLI_dynstr_free(ds);
	return str;
}

static void workbench_init_object_data(ObjectEngineData *engine_data)
{
	WORKBENCH_ObjectData *data = (WORKBENCH_ObjectData *)engine_data;
	data->object_id = ((e_data.next_object_id++) & 0xff) + 1;
}

static WORKBENCH_MaterialData *get_or_create_material_data(
        WORKBENCH_Data *vedata, Object *ob, Material *mat, Image *ima, int drawtype)
{
	WORKBENCH_StorageList *stl = vedata->stl;
	WORKBENCH_PassList *psl = vedata->psl;
	WORKBENCH_PrivateData *wpd = stl->g_data;
	WORKBENCH_MaterialData *material;
	WORKBENCH_ObjectData *engine_object_data = (WORKBENCH_ObjectData *)DRW_object_engine_data_ensure(
	        ob, &draw_engine_workbench_solid, sizeof(WORKBENCH_ObjectData), &workbench_init_object_data, NULL);
	WORKBENCH_MaterialData material_template;
	DRWShadingGroup *grp;

	/* Solid */
	workbench_material_update_data(wpd, ob, mat, &material_template);
	material_template.object_id = OBJECT_ID_PASS_ENABLED(wpd) ? engine_object_data->object_id : 1;
	material_template.drawtype = drawtype;
	material_template.ima = ima;
	uint hash = workbench_material_get_hash(&material_template);

	material = BLI_ghash_lookup(wpd->material_hash, SET_UINT_IN_POINTER(hash));
	if (material == NULL) {
		material = MEM_mallocN(sizeof(WORKBENCH_MaterialData), __func__);

		/* transparent accum */
		grp = DRW_shgroup_create(
		        drawtype == OB_SOLID ? wpd->transparent_accum_sh : wpd->transparent_accum_texture_sh,
		        psl->transparent_accum_pass);
		DRW_shgroup_uniform_block(grp, "world_block", wpd->world_ubo);
		DRW_shgroup_uniform_float(grp, "alpha", &wpd->shading.xray_alpha, 1);
		DRW_shgroup_uniform_vec4(grp, "viewvecs[0]", (float *)wpd->viewvecs, 3);
		workbench_material_set_normal_world_matrix(grp, wpd, e_data.normal_world_matrix);
		material->object_id = engine_object_data->object_id;
		copy_v4_v4(material->material_data.diffuse_color, material_template.material_data.diffuse_color);
		copy_v4_v4(material->material_data.specular_color, material_template.material_data.specular_color);
		material->material_data.roughness = material_template.material_data.roughness;
		switch (drawtype) {
			case OB_SOLID:
			{
				if (STUDIOLIGHT_ORIENTATION_VIEWNORMAL_ENABLED(wpd)) {
					BKE_studiolight_ensure_flag(wpd->studio_light, STUDIOLIGHT_EQUIRECTANGULAR_RADIANCE_GPUTEXTURE);
					DRW_shgroup_uniform_texture(grp, "matcapImage", wpd->studio_light->equirectangular_radiance_gputexture);
				}
				if (SPECULAR_HIGHLIGHT_ENABLED(wpd) || MATCAP_ENABLED(wpd)) {
					DRW_shgroup_uniform_vec2(grp, "invertedViewportSize", DRW_viewport_invert_size_get(), 1);
				}
				break;
			}

			case OB_TEXTURE:
			{
				GPUTexture *tex = GPU_texture_from_blender(ima, NULL, GL_TEXTURE_2D, false, 0.0f);
				DRW_shgroup_uniform_texture(grp, "image", tex);
				break;
			}
		}
		material->material_ubo = DRW_uniformbuffer_create(sizeof(WORKBENCH_UBO_Material), &material->material_data);
		DRW_shgroup_uniform_block(grp, "material_block", material->material_ubo);
		material->shgrp = grp;

		/* Depth */
		material->shgrp_object_outline = DRW_shgroup_create(e_data.object_outline_sh, psl->object_outline_pass);
		material->object_id = engine_object_data->object_id;
		DRW_shgroup_uniform_int(material->shgrp_object_outline, "object_id", &material->object_id, 1);
		BLI_ghash_insert(wpd->material_hash, SET_UINT_IN_POINTER(hash), material);
	}
	return material;
}

static void ensure_forward_shaders(WORKBENCH_PrivateData *wpd, int index, int drawtype, bool is_hair)
{
	if (e_data.composite_sh_cache[index] == NULL && drawtype == OB_SOLID && !is_hair) {
		char *defines = workbench_material_build_defines(wpd, drawtype, is_hair);
		char *composite_frag = workbench_build_forward_composite_frag();
		e_data.composite_sh_cache[index] = DRW_shader_create_fullscreen(composite_frag, defines);
		MEM_freeN(composite_frag);
		MEM_freeN(defines);
	}

	if (e_data.transparent_accum_sh_cache[index] == NULL) {
		char *defines = workbench_material_build_defines(wpd, drawtype, is_hair);
		char *transparent_accum_vert = workbench_build_forward_vert();
		char *transparent_accum_frag = workbench_build_forward_transparent_accum_frag();
		e_data.transparent_accum_sh_cache[index] = DRW_shader_create(
		        transparent_accum_vert, NULL,
		        transparent_accum_frag, defines);
		MEM_freeN(transparent_accum_vert);
		MEM_freeN(transparent_accum_frag);
		MEM_freeN(defines);
	}
}

static void select_forward_shaders(WORKBENCH_PrivateData *wpd)
{
	int index_solid = workbench_material_get_shader_index(wpd, OB_SOLID, false);
	int index_solid_hair = workbench_material_get_shader_index(wpd, OB_SOLID, true);
	int index_texture = workbench_material_get_shader_index(wpd, OB_TEXTURE, false);
	int index_texture_hair = workbench_material_get_shader_index(wpd, OB_TEXTURE, true);

	ensure_forward_shaders(wpd, index_solid, OB_SOLID, false);
	ensure_forward_shaders(wpd, index_solid_hair, OB_SOLID, true);
	ensure_forward_shaders(wpd, index_texture, OB_TEXTURE, false);
	ensure_forward_shaders(wpd, index_texture_hair, OB_TEXTURE, true);

	wpd->composite_sh = e_data.composite_sh_cache[index_solid];
	wpd->transparent_accum_sh = e_data.transparent_accum_sh_cache[index_solid];
	wpd->transparent_accum_hair_sh = e_data.transparent_accum_sh_cache[index_solid_hair];
	wpd->transparent_accum_texture_sh = e_data.transparent_accum_sh_cache[index_texture];
	wpd->transparent_accum_texture_hair_sh = e_data.transparent_accum_sh_cache[index_texture_hair];
}

/* public functions */
void workbench_forward_engine_init(WORKBENCH_Data *vedata)
{
	WORKBENCH_FramebufferList *fbl = vedata->fbl;
	WORKBENCH_PassList *psl = vedata->psl;
	WORKBENCH_StorageList *stl = vedata->stl;
	DefaultTextureList *dtxl = DRW_viewport_texture_list_get();
	DRWShadingGroup *grp;

	if (!stl->g_data) {
		/* Alloc transient pointers */
		stl->g_data = MEM_mallocN(sizeof(*stl->g_data), __func__);
	}
	WORKBENCH_PrivateData *wpd = stl->g_data;
	workbench_private_data_init(wpd);
	float light_direction[3];
	workbench_private_data_get_light_direction(wpd, light_direction);

	if (!e_data.next_object_id) {
		e_data.next_object_id = 1;
		memset(e_data.composite_sh_cache, 0x00, sizeof(struct GPUShader *) * MAX_SHADERS);
		memset(e_data.transparent_accum_sh_cache, 0x00, sizeof(struct GPUShader *) * MAX_SHADERS);

		char *defines = workbench_material_build_defines(wpd, OB_SOLID, false);
		char *defines_hair = workbench_material_build_defines(wpd, OB_SOLID, true);
		char *forward_vert = workbench_build_forward_vert();
		char *forward_depth_frag = workbench_build_forward_depth_frag();
		e_data.object_outline_sh = DRW_shader_create(
		        forward_vert, NULL,
		        forward_depth_frag, defines);
		e_data.object_outline_hair_sh = DRW_shader_create(
		        forward_vert, NULL,
		        forward_depth_frag, defines_hair);

		e_data.checker_depth_sh = DRW_shader_create_fullscreen(
		        datatoc_workbench_checkerboard_depth_frag_glsl, NULL);
		MEM_freeN(forward_vert);
		MEM_freeN(forward_depth_frag);
		MEM_freeN(defines);
		MEM_freeN(defines_hair);
	}
	select_forward_shaders(wpd);

	const float *viewport_size = DRW_viewport_size_get();
	const int size[2] = {(int)viewport_size[0], (int)viewport_size[1]};

	e_data.object_id_tx = DRW_texture_pool_query_2D(
	        size[0], size[1], GPU_R32UI, &draw_engine_workbench_transparent);
	e_data.transparent_accum_tx = DRW_texture_pool_query_2D(
	        size[0], size[1], GPU_RGBA16F, &draw_engine_workbench_transparent);
	e_data.transparent_revealage_tx = DRW_texture_pool_query_2D(
	        size[0], size[1], GPU_R16F, &draw_engine_workbench_transparent);
	e_data.composite_buffer_tx = DRW_texture_pool_query_2D(
	        size[0], size[1], GPU_R11F_G11F_B10F, &draw_engine_workbench_transparent);

	GPU_framebuffer_ensure_config(&fbl->object_outline_fb, {
		GPU_ATTACHMENT_TEXTURE(dtxl->depth),
		GPU_ATTACHMENT_TEXTURE(e_data.object_id_tx),
	});

	GPU_framebuffer_ensure_config(&fbl->transparent_accum_fb, {
		GPU_ATTACHMENT_NONE,
		GPU_ATTACHMENT_TEXTURE(e_data.transparent_accum_tx),
		GPU_ATTACHMENT_TEXTURE(e_data.transparent_revealage_tx),
	});

	GPU_framebuffer_ensure_config(&fbl->composite_fb, {
		GPU_ATTACHMENT_NONE,
		GPU_ATTACHMENT_TEXTURE(e_data.composite_buffer_tx),
	});

	/* Transparency Accum */
	{
		int state = DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND_OIT;
		psl->transparent_accum_pass = DRW_pass_create("Transparent Accum", state);
	}
	/* Depth */
	{
		int state = DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS;
		psl->object_outline_pass = DRW_pass_create("Object Outline Pass", state);
	}
	/* Composite */
	{
		int state = DRW_STATE_WRITE_COLOR;
		psl->composite_pass = DRW_pass_create("Composite", state);

		grp = DRW_shgroup_create(wpd->composite_sh, psl->composite_pass);
		DRW_shgroup_uniform_texture_ref(grp, "objectId", &e_data.object_id_tx);
		DRW_shgroup_uniform_texture_ref(grp, "transparentAccum", &e_data.transparent_accum_tx);
		DRW_shgroup_uniform_texture_ref(grp, "transparentRevealage", &e_data.transparent_revealage_tx);
		DRW_shgroup_uniform_block(grp, "world_block", wpd->world_ubo);
		DRW_shgroup_uniform_vec2(grp, "invertedViewportSize", DRW_viewport_invert_size_get(), 1);
		DRW_shgroup_call_add(grp, DRW_cache_fullscreen_quad_get(), NULL);
	}
	/* Checker Depth */
	{
		int state = DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_ALWAYS;
		psl->checker_depth_pass = DRW_pass_create("Checker Depth", state);
		grp = DRW_shgroup_create(e_data.checker_depth_sh, psl->checker_depth_pass);
		DRW_shgroup_call_add(grp, DRW_cache_fullscreen_quad_get(), NULL);
		DRW_shgroup_uniform_float_copy(grp, "threshold", 0.75f - wpd->shading.xray_alpha * 0.5f);
	}
}

void workbench_forward_engine_free()
{
	for (int index = 0; index < MAX_SHADERS; index++) {
		DRW_SHADER_FREE_SAFE(e_data.composite_sh_cache[index]);
		DRW_SHADER_FREE_SAFE(e_data.transparent_accum_sh_cache[index]);
	}
	DRW_SHADER_FREE_SAFE(e_data.object_outline_sh);
	DRW_SHADER_FREE_SAFE(e_data.object_outline_hair_sh);
	DRW_SHADER_FREE_SAFE(e_data.checker_depth_sh);
}

void workbench_forward_cache_init(WORKBENCH_Data *UNUSED(vedata))
{
}

static void workbench_forward_cache_populate_particles(WORKBENCH_Data *vedata, Object *ob)
{
	WORKBENCH_StorageList *stl = vedata->stl;
	WORKBENCH_PassList *psl = vedata->psl;
	WORKBENCH_PrivateData *wpd = stl->g_data;
	const DRWContextState *draw_ctx = DRW_context_state_get();

	if (ob == draw_ctx->object_edit) {
		return;
	}
	for (ModifierData *md = ob->modifiers.first; md; md = md->next) {
		if (md->type != eModifierType_ParticleSystem) {
			continue;
		}
		ParticleSystem *psys = ((ParticleSystemModifierData *)md)->psys;
		if (!psys_check_enabled(ob, psys, false)) {
			continue;
		}
		if (!DRW_check_psys_visible_within_active_context(ob, psys)) {
			continue;
		}
		ParticleSettings *part = psys->part;
		const int draw_as = (part->draw_as == PART_DRAW_REND) ? part->ren_as : part->draw_as;

		if (draw_as == PART_DRAW_PATH) {
			Image *image = NULL;
			Material *mat = give_current_material(ob, part->omat);
			int mat_drawtype = OB_SOLID;

			if (wpd->drawtype == OB_TEXTURE) {
				ED_object_get_active_image(ob, part->omat, &image, NULL, NULL, NULL);
				/* use OB_SOLID when no texture could be determined */
				if (image) {
					mat_drawtype = OB_TEXTURE;
				}
			}

			WORKBENCH_MaterialData *material = get_or_create_material_data(vedata, ob, mat, image, mat_drawtype);

			struct GPUShader *shader = (mat_drawtype == OB_SOLID)
			                           ? wpd->transparent_accum_hair_sh
			                           : wpd->transparent_accum_texture_hair_sh;
			DRWShadingGroup *shgrp = DRW_shgroup_hair_create(
			                                ob, psys, md,
			                                psl->transparent_accum_pass,
			                                shader);
			workbench_material_set_normal_world_matrix(shgrp, wpd, e_data.normal_world_matrix);
			DRW_shgroup_uniform_block(shgrp, "world_block", wpd->world_ubo);
			DRW_shgroup_uniform_block(shgrp, "material_block", material->material_ubo);
			DRW_shgroup_uniform_vec4(shgrp, "viewvecs[0]", (float *)wpd->viewvecs, 3);
			/* Hairs have lots of layer and can rapidly become the most prominent surface.
			 * So lower their alpha artificially. */
			float hair_alpha = wpd->shading.xray_alpha * 0.33f;
			DRW_shgroup_uniform_float_copy(shgrp, "alpha", hair_alpha);
			if (image) {
				GPUTexture *tex = GPU_texture_from_blender(image, NULL, GL_TEXTURE_2D, false, 0.0f);
				DRW_shgroup_uniform_texture(shgrp, "image", tex);
			}
			if (STUDIOLIGHT_ORIENTATION_VIEWNORMAL_ENABLED(wpd)) {
				BKE_studiolight_ensure_flag(wpd->studio_light, STUDIOLIGHT_EQUIRECTANGULAR_RADIANCE_GPUTEXTURE);
				DRW_shgroup_uniform_texture(shgrp, "matcapImage", wpd->studio_light->equirectangular_radiance_gputexture);
			}
			if (SPECULAR_HIGHLIGHT_ENABLED(wpd) || MATCAP_ENABLED(wpd)) {
				DRW_shgroup_uniform_vec2(shgrp, "invertedViewportSize", DRW_viewport_invert_size_get(), 1);
			}
			shgrp = DRW_shgroup_hair_create(ob, psys, md,
			                        vedata->psl->object_outline_pass,
			                        e_data.object_outline_hair_sh);
			DRW_shgroup_uniform_int(shgrp, "object_id", &material->object_id, 1);
		}
	}
}

void workbench_forward_cache_populate(WORKBENCH_Data *vedata, Object *ob)
{
	WORKBENCH_StorageList *stl = vedata->stl;
	WORKBENCH_PrivateData *wpd = stl->g_data;

	if (!DRW_object_is_renderable(ob))
		return;

	if (ob->type == OB_MESH) {
		workbench_forward_cache_populate_particles(vedata, ob);
	}

	if (!DRW_check_object_visible_within_active_context(ob)) {
		return;
	}

	if (ELEM(ob->type, OB_MESH, OB_CURVE, OB_SURF, OB_FONT, OB_MBALL)) {
		const DRWContextState *draw_ctx = DRW_context_state_get();
		const bool is_active = (ob == draw_ctx->obact);
		const bool is_sculpt_mode = is_active && (draw_ctx->object_mode & OB_MODE_SCULPT) != 0;
		bool is_drawn = false;

		WORKBENCH_MaterialData *material = get_or_create_material_data(vedata, ob, NULL, NULL, OB_SOLID);
		if (!is_sculpt_mode && wpd->drawtype == OB_TEXTURE && ELEM(ob->type, OB_MESH)) {
			const Mesh *me = ob->data;
			if (me->mloopuv) {
				const int materials_len = MAX2(1, (is_sculpt_mode ? 1 : ob->totcol));
				struct GPUMaterial **gpumat_array = BLI_array_alloca(gpumat_array, materials_len);
				struct Gwn_Batch **geom_array = me->totcol ? DRW_cache_mesh_surface_texpaint_get(ob) : NULL;
				if (materials_len > 0 && geom_array) {
					for (int i = 0; i < materials_len; i++) {
						if (geom_array[i] == NULL) {
							continue;
						}

						Material *mat = give_current_material(ob, i + 1);
						Image *image;
						ED_object_get_active_image(ob, i + 1, &image, NULL, NULL, NULL);
						/* use OB_SOLID when no texture could be determined */
						int mat_drawtype = OB_SOLID;
						if (image) {
							mat_drawtype = OB_TEXTURE;
						}
						material = get_or_create_material_data(vedata, ob, mat, image, mat_drawtype);
						DRW_shgroup_call_object_add(material->shgrp_object_outline, geom_array[i], ob);
						DRW_shgroup_call_object_add(material->shgrp, geom_array[i], ob);
					}
					is_drawn = true;
				}
			}
		}

		/* Fallback from not drawn OB_TEXTURE mode or just OB_SOLID mode */
		if (!is_drawn) {
			if ((wpd->shading.color_type != V3D_SHADING_MATERIAL_COLOR)) {
				/* No material split needed */
				struct Gwn_Batch *geom = DRW_cache_object_surface_get(ob);
				if (geom) {
					if (is_sculpt_mode) {
						DRW_shgroup_call_sculpt_add(material->shgrp_object_outline, ob, ob->obmat);
						DRW_shgroup_call_sculpt_add(material->shgrp, ob, ob->obmat);
					}
					else {
						DRW_shgroup_call_object_add(material->shgrp_object_outline, geom, ob);
						DRW_shgroup_call_object_add(material->shgrp, geom, ob);
					}
				}
			}
			else {
				const int materials_len = MAX2(1, (is_sculpt_mode ? 1 : ob->totcol));
				struct GPUMaterial **gpumat_array = BLI_array_alloca(gpumat_array, materials_len);
				for (int i = 0; i < materials_len; i++) {
					gpumat_array[i] = NULL;
				}

				struct Gwn_Batch **mat_geom = DRW_cache_object_surface_material_get(
				        ob, gpumat_array, materials_len, NULL, NULL, NULL);
				if (mat_geom) {
					for (int i = 0; i < materials_len; ++i) {
						if (mat_geom[i] == NULL) {
							continue;
						}

						Material *mat = give_current_material(ob, i + 1);
						material = get_or_create_material_data(vedata, ob, mat, NULL, OB_SOLID);
						if (is_sculpt_mode) {
							DRW_shgroup_call_sculpt_add(material->shgrp_object_outline, ob, ob->obmat);
							DRW_shgroup_call_sculpt_add(material->shgrp, ob, ob->obmat);
						}
						else {
							DRW_shgroup_call_object_add(material->shgrp_object_outline, mat_geom[i], ob);
							DRW_shgroup_call_object_add(material->shgrp, mat_geom[i], ob);
						}
					}
				}
			}
		}
	}
}

void workbench_forward_cache_finish(WORKBENCH_Data *UNUSED(vedata))
{
}

void workbench_forward_draw_background(WORKBENCH_Data *UNUSED(vedata))
{
	const float clear_depth = 1.0f;
	DefaultFramebufferList *dfbl = DRW_viewport_framebuffer_list_get();
	DRW_stats_group_start("Clear depth");
	GPU_framebuffer_bind(dfbl->default_fb);
	GPU_framebuffer_clear_depth(dfbl->default_fb, clear_depth);
	DRW_stats_group_end();
}

void workbench_forward_draw_scene(WORKBENCH_Data *vedata)
{
	WORKBENCH_PassList *psl = vedata->psl;
	WORKBENCH_StorageList *stl = vedata->stl;
	WORKBENCH_FramebufferList *fbl = vedata->fbl;
	WORKBENCH_PrivateData *wpd = stl->g_data;
	DefaultFramebufferList *dfbl = DRW_viewport_framebuffer_list_get();

	/* Write Depth + Object ID */
	const float clear_outline[4] = {0.0f};
	GPU_framebuffer_bind(fbl->object_outline_fb);
	GPU_framebuffer_clear_color(fbl->object_outline_fb, clear_outline);
	DRW_draw_pass(psl->object_outline_pass);

	if (wpd->shading.xray_alpha > 0.0) {
		const float clear_color[4] = {0.0f, 0.0f, 0.0f, 1.0f};
		GPU_framebuffer_bind(fbl->transparent_accum_fb);
		GPU_framebuffer_clear_color(fbl->transparent_accum_fb, clear_color);
		DRW_draw_pass(psl->transparent_accum_pass);
	}
	else {
		/* TODO(fclem): this is unecessary and takes up perf.
		 * Better change the composite frag shader to not use the tx. */
		const float clear_color[4] = {0.0f, 0.0f, 0.0f, 1.0f};
		GPU_framebuffer_bind(fbl->transparent_accum_fb);
		GPU_framebuffer_clear_color(fbl->transparent_accum_fb, clear_color);
	}

	/* Composite */
	GPU_framebuffer_bind(fbl->composite_fb);
	DRW_draw_pass(psl->composite_pass);

	/* Color correct */
	GPU_framebuffer_bind(dfbl->color_only_fb);
	DRW_transform_to_display(e_data.composite_buffer_tx);

	GPU_framebuffer_bind(dfbl->depth_only_fb);
	DRW_draw_pass(psl->checker_depth_pass);

	workbench_private_data_free(wpd);
}
