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

/** \file workbench_deferred.c
 *  \ingroup draw_engine
 */

#include "workbench_private.h"

#include "BIF_gl.h"

#include "BLI_alloca.h"
#include "BLI_dynstr.h"
#include "BLI_utildefines.h"
#include "BLI_rand.h"
#include "BLI_string_utils.h"

#include "BKE_node.h"
#include "BKE_modifier.h"
#include "BKE_object.h"
#include "BKE_particle.h"

#include "DNA_image_types.h"
#include "DNA_mesh_types.h"
#include "DNA_modifier_types.h"
#include "DNA_node_types.h"

#include "ED_uvedit.h"

#include "GPU_shader.h"
#include "GPU_texture.h"
#include "GPU_extensions.h"

#include "../eevee/eevee_lut.h" /* TODO find somewhere to share blue noise Table */

/* *********** STATIC *********** */

/* #define DEBUG_SHADOW_VOLUME */

#ifdef DEBUG_SHADOW_VOLUME
#  include "draw_debug.h"
#endif

static struct {
	struct GPUShader *prepass_sh_cache[MAX_PREPASS_SHADERS];
	struct GPUShader *composite_sh_cache[MAX_COMPOSITE_SHADERS];
	struct GPUShader *cavity_sh[MAX_CAVITY_SHADERS];
	struct GPUShader *background_sh[2];
	struct GPUShader *ghost_resolve_sh;
	struct GPUShader *shadow_fail_sh;
	struct GPUShader *shadow_fail_manifold_sh;
	struct GPUShader *shadow_pass_sh;
	struct GPUShader *shadow_pass_manifold_sh;
	struct GPUShader *shadow_caps_sh;
	struct GPUShader *shadow_caps_manifold_sh;

	struct GPUTexture *ghost_depth_tx; /* ref only, not alloced */
	struct GPUTexture *object_id_tx; /* ref only, not alloced */
	struct GPUTexture *color_buffer_tx; /* ref only, not alloced */
	struct GPUTexture *cavity_buffer_tx; /* ref only, not alloced */
	struct GPUTexture *metallic_buffer_tx; /* ref only, not alloced */
	struct GPUTexture *normal_buffer_tx; /* ref only, not alloced */
	struct GPUTexture *composite_buffer_tx; /* ref only, not alloced */

	SceneDisplay display; /* world light direction for shadows */
	int next_object_id;

	struct GPUUniformBuffer *sampling_ubo;
	struct GPUTexture *jitter_tx;
	int cached_sample_num;
} e_data = {{NULL}};

/* Shaders */
extern char datatoc_common_hair_lib_glsl[];
extern char datatoc_common_world_clip_lib_glsl[];

extern char datatoc_workbench_prepass_vert_glsl[];
extern char datatoc_workbench_prepass_frag_glsl[];
extern char datatoc_workbench_cavity_frag_glsl[];
extern char datatoc_workbench_deferred_composite_frag_glsl[];
extern char datatoc_workbench_deferred_background_frag_glsl[];
extern char datatoc_workbench_ghost_resolve_frag_glsl[];

extern char datatoc_workbench_shadow_vert_glsl[];
extern char datatoc_workbench_shadow_geom_glsl[];
extern char datatoc_workbench_shadow_caps_geom_glsl[];
extern char datatoc_workbench_shadow_debug_frag_glsl[];

extern char datatoc_workbench_background_lib_glsl[];
extern char datatoc_workbench_cavity_lib_glsl[];
extern char datatoc_workbench_common_lib_glsl[];
extern char datatoc_workbench_data_lib_glsl[];
extern char datatoc_workbench_object_outline_lib_glsl[];
extern char datatoc_workbench_curvature_lib_glsl[];
extern char datatoc_workbench_world_light_lib_glsl[];

extern char datatoc_gpu_shader_depth_only_frag_glsl[];

static char *workbench_build_composite_frag(WORKBENCH_PrivateData *wpd)
{
	char *str = NULL;

	DynStr *ds = BLI_dynstr_new();

	BLI_dynstr_append(ds, datatoc_workbench_data_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_common_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_background_lib_glsl);

	if (!FLAT_ENABLED(wpd)) {
		BLI_dynstr_append(ds, datatoc_workbench_world_light_lib_glsl);
	}
	if (OBJECT_OUTLINE_ENABLED(wpd)) {
		BLI_dynstr_append(ds, datatoc_workbench_object_outline_lib_glsl);
	}
	if (CURVATURE_ENABLED(wpd)) {
		BLI_dynstr_append(ds, datatoc_workbench_curvature_lib_glsl);
	}

	BLI_dynstr_append(ds, datatoc_workbench_deferred_composite_frag_glsl);

	str = BLI_dynstr_get_cstring(ds);
	BLI_dynstr_free(ds);
	return str;
}

static char *workbench_build_prepass_frag(void)
{
	char *str = NULL;

	DynStr *ds = BLI_dynstr_new();

	BLI_dynstr_append(ds, datatoc_workbench_data_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_common_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_prepass_frag_glsl);

	str = BLI_dynstr_get_cstring(ds);
	BLI_dynstr_free(ds);
	return str;
}

static char *workbench_build_prepass_vert(bool is_hair)
{
	char *str = NULL;
	if (!is_hair) {
		return BLI_string_joinN(
		        datatoc_common_world_clip_lib_glsl,
		        datatoc_workbench_prepass_vert_glsl);
	}

	DynStr *ds = BLI_dynstr_new();

	BLI_dynstr_append(ds, datatoc_common_hair_lib_glsl);
	BLI_dynstr_append(ds, datatoc_common_world_clip_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_prepass_vert_glsl);

	str = BLI_dynstr_get_cstring(ds);
	BLI_dynstr_free(ds);
	return str;
}

static char *workbench_build_cavity_frag(bool cavity, bool curvature, bool high_dpi)
{
	char *str = NULL;

	DynStr *ds = BLI_dynstr_new();

	if (cavity) {
		BLI_dynstr_append(ds, "#define USE_CAVITY\n");
	}
	if (curvature) {
		BLI_dynstr_append(ds, "#define USE_CURVATURE\n");
	}
	if (high_dpi) {
		BLI_dynstr_append(ds, "#define CURVATURE_OFFSET 2\n");
	}
	if (NORMAL_ENCODING_ENABLED()) {
		BLI_dynstr_append(ds, "#define WORKBENCH_ENCODE_NORMALS\n");
	}
	BLI_dynstr_append(ds, datatoc_workbench_common_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_curvature_lib_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_cavity_frag_glsl);
	BLI_dynstr_append(ds, datatoc_workbench_cavity_lib_glsl);

	str = BLI_dynstr_get_cstring(ds);
	BLI_dynstr_free(ds);
	return str;
}

static GPUShader *workbench_cavity_shader_get(bool cavity, bool curvature)
{
	const bool high_dpi = (U.pixelsize > 1.5f);
	int index = 0;
	SET_FLAG_FROM_TEST(index, cavity, 1 << 0);
	SET_FLAG_FROM_TEST(index, curvature, 1 << 1);
	SET_FLAG_FROM_TEST(index, high_dpi, 1 << 2);

	GPUShader **sh = &e_data.cavity_sh[index];
	if (*sh == NULL) {
		char *cavity_frag = workbench_build_cavity_frag(cavity, curvature, high_dpi);
		*sh = DRW_shader_create_fullscreen(cavity_frag, NULL);
		MEM_freeN(cavity_frag);
	}
	return *sh;
}

static GPUShader *ensure_deferred_prepass_shader(WORKBENCH_PrivateData *wpd, bool use_textures, bool is_hair)
{
	int index = workbench_material_get_prepass_shader_index(wpd, use_textures, is_hair);
	if (e_data.prepass_sh_cache[index] == NULL) {
		char *defines = workbench_material_build_defines(wpd, use_textures, is_hair);
		char *prepass_vert = workbench_build_prepass_vert(is_hair);
		char *prepass_frag = workbench_build_prepass_frag();
		e_data.prepass_sh_cache[index] = DRW_shader_create(
		        prepass_vert, NULL,
		        prepass_frag, defines);
		MEM_freeN(prepass_vert);
		MEM_freeN(prepass_frag);
		MEM_freeN(defines);
	}
	return e_data.prepass_sh_cache[index];
}

static GPUShader *ensure_deferred_composite_shader(WORKBENCH_PrivateData *wpd)
{
	int index = workbench_material_get_composite_shader_index(wpd);
	if (e_data.composite_sh_cache[index] == NULL) {
		char *defines = workbench_material_build_defines(wpd, false, false);
		char *composite_frag = workbench_build_composite_frag(wpd);
		e_data.composite_sh_cache[index] = DRW_shader_create_fullscreen(composite_frag, defines);
		MEM_freeN(composite_frag);
		MEM_freeN(defines);
	}
	return e_data.composite_sh_cache[index];
}

static GPUShader *ensure_background_shader(WORKBENCH_PrivateData *wpd)
{
	const int index = OBJECT_OUTLINE_ENABLED(wpd) ? 1 : 0;
	if (e_data.background_sh[index] == NULL) {
		const char *defines = (index) ? "#define V3D_SHADING_OBJECT_OUTLINE\n" : NULL;
		char *frag = BLI_string_joinN(
		        datatoc_workbench_data_lib_glsl,
		        datatoc_workbench_common_lib_glsl,
		        datatoc_workbench_background_lib_glsl,
		        datatoc_workbench_object_outline_lib_glsl,
		        datatoc_workbench_deferred_background_frag_glsl);
		e_data.background_sh[index] = DRW_shader_create_fullscreen(frag, defines);
		MEM_freeN(frag);
	}
	return e_data.background_sh[index];
}

static void select_deferred_shaders(WORKBENCH_PrivateData *wpd)
{
	wpd->prepass_solid_sh = ensure_deferred_prepass_shader(wpd, false, false);
	wpd->prepass_solid_hair_sh = ensure_deferred_prepass_shader(wpd, false, true);
	wpd->prepass_texture_sh = ensure_deferred_prepass_shader(wpd, true, false);
	wpd->prepass_texture_hair_sh = ensure_deferred_prepass_shader(wpd, true, true);
	wpd->composite_sh = ensure_deferred_composite_shader(wpd);
	wpd->background_sh = ensure_background_shader(wpd);
}

/* Using Hammersley distribution */
static float *create_disk_samples(int num_samples, int num_iterations)
{
	/* vec4 to ensure memory alignment. */
	const int total_samples = num_samples * num_iterations;
	float(*texels)[4] = MEM_mallocN(sizeof(float[4]) * total_samples, __func__);
	const float num_samples_inv = 1.0f / num_samples;

	for (int i = 0; i < total_samples; i++) {
		float it_add = (i / num_samples) * 0.499f;
		float r = fmodf((i + 0.5f + it_add) * num_samples_inv, 1.0f);
		double dphi;
		BLI_hammersley_1D(i, &dphi);

		float phi = (float)dphi * 2.0f * M_PI + it_add;
		texels[i][0] = cosf(phi);
		texels[i][1] = sinf(phi);
		/* This deliberately distribute more samples
		 * at the center of the disk (and thus the shadow). */
		texels[i][2] = r;
	}

	return (float *)texels;
}

static struct GPUTexture *create_jitter_texture(int num_samples)
{
	float jitter[64 * 64][3];
	const float num_samples_inv = 1.0f / num_samples;

	for (int i = 0; i < 64 * 64; i++) {
		float phi = blue_noise[i][0] * 2.0f * M_PI;
		/* This rotate the sample per pixels */
		jitter[i][0] = cosf(phi);
		jitter[i][1] = sinf(phi);
		/* This offset the sample along it's direction axis (reduce banding) */
		float bn = blue_noise[i][1] - 0.5f;
		CLAMP(bn, -0.499f, 0.499f); /* fix fireflies */
		jitter[i][2] = bn * num_samples_inv;
	}

	UNUSED_VARS(bsdf_split_sum_ggx, btdf_split_sum_ggx, ltc_mag_ggx, ltc_mat_ggx, ltc_disk_integral);

	return DRW_texture_create_2D(64, 64, GPU_RGB16F, DRW_TEX_FILTER | DRW_TEX_WRAP, &jitter[0][0]);
}
/* Functions */


static void workbench_init_object_data(DrawData *dd)
{
	WORKBENCH_ObjectData *data = (WORKBENCH_ObjectData *)dd;
	data->object_id = ((e_data.next_object_id++) & 0xff) + 1;
	data->shadow_bbox_dirty = true;
}

void workbench_deferred_engine_init(WORKBENCH_Data *vedata)
{
	WORKBENCH_FramebufferList *fbl = vedata->fbl;
	WORKBENCH_StorageList *stl = vedata->stl;
	WORKBENCH_PassList *psl = vedata->psl;
	DefaultTextureList *dtxl = DRW_viewport_texture_list_get();
	const DRWContextState *draw_ctx = DRW_context_state_get();

	if (!stl->g_data) {
		/* Alloc transient pointers */
		stl->g_data = MEM_callocN(sizeof(*stl->g_data), __func__);
	}
	if (!stl->effects) {
		stl->effects = MEM_callocN(sizeof(*stl->effects), __func__);
		workbench_effect_info_init(stl->effects);
	}

	if (!e_data.next_object_id) {
		memset(e_data.prepass_sh_cache,   0, sizeof(e_data.prepass_sh_cache));
		memset(e_data.composite_sh_cache, 0, sizeof(e_data.composite_sh_cache));
		e_data.next_object_id = 1;
#ifdef DEBUG_SHADOW_VOLUME
		const char *shadow_frag = datatoc_workbench_shadow_debug_frag_glsl;
#else
		const char *shadow_frag = datatoc_gpu_shader_depth_only_frag_glsl;
#endif
		/* TODO only compile on demand */
		e_data.shadow_pass_sh = DRW_shader_create(
		        datatoc_workbench_shadow_vert_glsl,
		        datatoc_workbench_shadow_geom_glsl,
		        shadow_frag,
		        "#define SHADOW_PASS\n"
		        "#define DOUBLE_MANIFOLD\n");
		e_data.shadow_pass_manifold_sh = DRW_shader_create(
		        datatoc_workbench_shadow_vert_glsl,
		        datatoc_workbench_shadow_geom_glsl,
		        shadow_frag,
		        "#define SHADOW_PASS\n");
		e_data.shadow_fail_sh = DRW_shader_create(
		        datatoc_workbench_shadow_vert_glsl,
		        datatoc_workbench_shadow_geom_glsl,
		        shadow_frag,
		        "#define SHADOW_FAIL\n"
		        "#define DOUBLE_MANIFOLD\n");
		e_data.shadow_fail_manifold_sh = DRW_shader_create(
		        datatoc_workbench_shadow_vert_glsl,
		        datatoc_workbench_shadow_geom_glsl,
		        shadow_frag,
		        "#define SHADOW_FAIL\n");
		e_data.shadow_caps_sh = DRW_shader_create(
		        datatoc_workbench_shadow_vert_glsl,
		        datatoc_workbench_shadow_caps_geom_glsl,
		        shadow_frag,
		        "#define SHADOW_FAIL\n"
		        "#define DOUBLE_MANIFOLD\n");
		e_data.shadow_caps_manifold_sh = DRW_shader_create(
		        datatoc_workbench_shadow_vert_glsl,
		        datatoc_workbench_shadow_caps_geom_glsl,
		        shadow_frag,
		        "#define SHADOW_FAIL\n");

		e_data.ghost_resolve_sh = DRW_shader_create_fullscreen(datatoc_workbench_ghost_resolve_frag_glsl, NULL);
	}
	workbench_volume_engine_init();
	workbench_fxaa_engine_init();
	workbench_taa_engine_init(vedata);

	WORKBENCH_PrivateData *wpd = stl->g_data;
	workbench_private_data_init(wpd);

	{
		const float *viewport_size = DRW_viewport_size_get();
		const int size[2] = {(int)viewport_size[0], (int)viewport_size[1]};
		const GPUTextureFormat nor_tex_format = NORMAL_ENCODING_ENABLED() ? GPU_RG16 : GPU_RGBA32F;
		const GPUTextureFormat comp_tex_format = DRW_state_is_image_render() ? GPU_RGBA16F : GPU_R11F_G11F_B10F;
		const GPUTextureFormat id_tex_format = OBJECT_ID_PASS_ENABLED(wpd) ? GPU_R32UI : GPU_R8;

		e_data.object_id_tx = NULL;
		e_data.color_buffer_tx = NULL;
		e_data.composite_buffer_tx = NULL;
		e_data.normal_buffer_tx = NULL;
		e_data.cavity_buffer_tx = NULL;

		e_data.composite_buffer_tx = DRW_texture_pool_query_2D(size[0], size[1], comp_tex_format, &draw_engine_workbench_solid);

		if (MATDATA_PASS_ENABLED(wpd) || GPU_unused_fb_slot_workaround()) {
			e_data.color_buffer_tx = DRW_texture_pool_query_2D(size[0], size[1], GPU_RGBA8, &draw_engine_workbench_solid);
		}
		if (OBJECT_ID_PASS_ENABLED(wpd) || GPU_unused_fb_slot_workaround()) {
			e_data.object_id_tx = DRW_texture_pool_query_2D(size[0], size[1], id_tex_format, &draw_engine_workbench_solid);
		}
		if (NORMAL_VIEWPORT_PASS_ENABLED(wpd)) {
			e_data.normal_buffer_tx = DRW_texture_pool_query_2D(size[0], size[1], nor_tex_format, &draw_engine_workbench_solid);
		}
		if (CAVITY_ENABLED(wpd)) {
			e_data.cavity_buffer_tx = DRW_texture_pool_query_2D(size[0], size[1], GPU_R16, &draw_engine_workbench_solid);
		}

		GPU_framebuffer_ensure_config(&fbl->prepass_fb, {
			GPU_ATTACHMENT_TEXTURE(dtxl->depth),
			GPU_ATTACHMENT_TEXTURE(e_data.color_buffer_tx),
			GPU_ATTACHMENT_TEXTURE(e_data.object_id_tx),
			GPU_ATTACHMENT_TEXTURE(e_data.normal_buffer_tx),
		});
		GPU_framebuffer_ensure_config(&fbl->cavity_fb, {
			GPU_ATTACHMENT_NONE,
			GPU_ATTACHMENT_TEXTURE(e_data.cavity_buffer_tx),
		});
		GPU_framebuffer_ensure_config(&fbl->composite_fb, {
			GPU_ATTACHMENT_TEXTURE(dtxl->depth),
			GPU_ATTACHMENT_TEXTURE(e_data.composite_buffer_tx),
		});
		GPU_framebuffer_ensure_config(&fbl->volume_fb, {
			GPU_ATTACHMENT_NONE,
			GPU_ATTACHMENT_TEXTURE(e_data.composite_buffer_tx),
		});

		if (!MATDATA_PASS_ENABLED(wpd) && !GPU_unused_fb_slot_workaround()) {
			e_data.color_buffer_tx = DRW_texture_pool_query_2D(size[0], size[1], GPU_RGBA8, &draw_engine_workbench_solid);
		}

		GPU_framebuffer_ensure_config(&fbl->effect_fb, {
			GPU_ATTACHMENT_NONE,
			GPU_ATTACHMENT_TEXTURE(e_data.color_buffer_tx),
		});

		if (OBJECT_ID_PASS_ENABLED(wpd)) {
			GPU_framebuffer_ensure_config(&fbl->id_clear_fb, {
				GPU_ATTACHMENT_NONE,
				GPU_ATTACHMENT_TEXTURE(e_data.object_id_tx),
			});
		}
	}

	{
		Scene *scene = draw_ctx->scene;
		/* AO Samples Tex */
		int num_iterations = workbench_taa_calculate_num_iterations(vedata);

		const int ssao_samples_single_iteration = scene->display.matcap_ssao_samples;
		const int ssao_samples = MIN2(num_iterations * ssao_samples_single_iteration, 500);

		if (e_data.sampling_ubo && (e_data.cached_sample_num != ssao_samples)) {
			DRW_UBO_FREE_SAFE(e_data.sampling_ubo);
			DRW_TEXTURE_FREE_SAFE(e_data.jitter_tx);
		}

		if (e_data.sampling_ubo == NULL) {
			float *samples = create_disk_samples(ssao_samples_single_iteration, num_iterations);
			e_data.jitter_tx = create_jitter_texture(ssao_samples);
			e_data.sampling_ubo = DRW_uniformbuffer_create(sizeof(float[4]) * ssao_samples, samples);
			e_data.cached_sample_num = ssao_samples;
			MEM_freeN(samples);
		}
	}

	/* Prepass */
	{
		DRWShadingGroup *grp;
		const bool do_cull = (draw_ctx->v3d && (draw_ctx->v3d->shading.flag & V3D_SHADING_BACKFACE_CULLING));

		int state = DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS_EQUAL;
		psl->prepass_pass = DRW_pass_create("Prepass", (do_cull) ? state | DRW_STATE_CULL_BACK : state);
		psl->prepass_hair_pass = DRW_pass_create("Prepass", state);

		psl->ghost_prepass_pass = DRW_pass_create("Prepass Ghost", (do_cull) ? state | DRW_STATE_CULL_BACK : state);
		psl->ghost_prepass_hair_pass = DRW_pass_create("Prepass Ghost", state);

		psl->ghost_resolve_pass = DRW_pass_create("Resolve Ghost Depth", DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_ALWAYS);
		grp = DRW_shgroup_create(e_data.ghost_resolve_sh, psl->ghost_resolve_pass);
		DRW_shgroup_uniform_texture_ref(grp, "depthBuffer", &e_data.ghost_depth_tx);
		DRW_shgroup_call_add(grp, DRW_cache_fullscreen_quad_get(), NULL);
	}

	{
		workbench_aa_create_pass(vedata, &e_data.color_buffer_tx);
	}

	if (CAVITY_ENABLED(wpd)) {
		int state = DRW_STATE_WRITE_COLOR;
		GPUShader *shader = workbench_cavity_shader_get(SSAO_ENABLED(wpd), CURVATURE_ENABLED(wpd));
		psl->cavity_pass = DRW_pass_create("Cavity", state);
		DRWShadingGroup *grp = DRW_shgroup_create(shader, psl->cavity_pass);
		DRW_shgroup_uniform_texture_ref(grp, "normalBuffer", &e_data.normal_buffer_tx);
		DRW_shgroup_uniform_block(grp, "samples_block", e_data.sampling_ubo);

		if (SSAO_ENABLED(wpd)) {
			DRW_shgroup_uniform_texture_ref(grp, "depthBuffer", &dtxl->depth);
			DRW_shgroup_uniform_vec2(grp, "invertedViewportSize", DRW_viewport_invert_size_get(), 1);
			DRW_shgroup_uniform_vec4(grp, "viewvecs[0]", (float *)wpd->viewvecs, 3);
			DRW_shgroup_uniform_vec4(grp, "ssao_params", wpd->ssao_params, 1);
			DRW_shgroup_uniform_vec4(grp, "ssao_settings", wpd->ssao_settings, 1);
			DRW_shgroup_uniform_mat4(grp, "WinMatrix", wpd->winmat);
			DRW_shgroup_uniform_texture(grp, "ssao_jitter", e_data.jitter_tx);
		}

		if (CURVATURE_ENABLED(wpd)) {
			DRW_shgroup_uniform_texture_ref(grp, "objectId", &e_data.object_id_tx);
			DRW_shgroup_uniform_vec2(grp, "curvature_settings", &wpd->world_data.curvature_ridge, 1);
		}

		DRW_shgroup_call_add(grp, DRW_cache_fullscreen_quad_get(), NULL);
	}
}

static void workbench_setup_ghost_framebuffer(WORKBENCH_FramebufferList *fbl)
{
	const float *viewport_size = DRW_viewport_size_get();
	const int size[2] = {(int)viewport_size[0], (int)viewport_size[1]};

	e_data.ghost_depth_tx = DRW_texture_pool_query_2D(size[0], size[1], GPU_DEPTH_COMPONENT24, &draw_engine_workbench_solid);

	GPU_framebuffer_ensure_config(&fbl->ghost_prepass_fb, {
		GPU_ATTACHMENT_TEXTURE(e_data.ghost_depth_tx),
		GPU_ATTACHMENT_TEXTURE(e_data.color_buffer_tx),
		GPU_ATTACHMENT_TEXTURE(e_data.object_id_tx),
		GPU_ATTACHMENT_TEXTURE(e_data.normal_buffer_tx),
	});
}

void workbench_deferred_engine_free(void)
{
	for (int index = 0; index < MAX_PREPASS_SHADERS; index++) {
		DRW_SHADER_FREE_SAFE(e_data.prepass_sh_cache[index]);
	}
	for (int index = 0; index < MAX_COMPOSITE_SHADERS; index++) {
		DRW_SHADER_FREE_SAFE(e_data.composite_sh_cache[index]);
	}
	for (int index = 0; index < MAX_CAVITY_SHADERS; ++index) {
		DRW_SHADER_FREE_SAFE(e_data.cavity_sh[index]);
	}
	DRW_SHADER_FREE_SAFE(e_data.ghost_resolve_sh);
	DRW_UBO_FREE_SAFE(e_data.sampling_ubo);
	DRW_TEXTURE_FREE_SAFE(e_data.jitter_tx);
	DRW_SHADER_FREE_SAFE(e_data.background_sh[0]);
	DRW_SHADER_FREE_SAFE(e_data.background_sh[1]);

	DRW_SHADER_FREE_SAFE(e_data.shadow_pass_sh);
	DRW_SHADER_FREE_SAFE(e_data.shadow_pass_manifold_sh);
	DRW_SHADER_FREE_SAFE(e_data.shadow_fail_sh);
	DRW_SHADER_FREE_SAFE(e_data.shadow_fail_manifold_sh);
	DRW_SHADER_FREE_SAFE(e_data.shadow_caps_sh);
	DRW_SHADER_FREE_SAFE(e_data.shadow_caps_manifold_sh);

	workbench_volume_engine_free();
	workbench_fxaa_engine_free();
	workbench_taa_engine_free();
}

static void workbench_composite_uniforms(WORKBENCH_PrivateData *wpd, DRWShadingGroup *grp)
{
	DRW_shgroup_uniform_block(grp, "world_block", wpd->world_ubo);
	if (MATDATA_PASS_ENABLED(wpd)) {
		DRW_shgroup_uniform_texture_ref(grp, "materialBuffer", &e_data.color_buffer_tx);
	}
	else {
		DRW_shgroup_uniform_vec3(grp, "materialSingleColor", wpd->shading.single_color, 1);
	}
	if (OBJECT_OUTLINE_ENABLED(wpd)) {
		DRW_shgroup_uniform_texture_ref(grp, "objectId", &e_data.object_id_tx);
	}
	if (NORMAL_VIEWPORT_COMP_PASS_ENABLED(wpd)) {
		DRW_shgroup_uniform_texture_ref(grp, "normalBuffer", &e_data.normal_buffer_tx);
	}
	if (CAVITY_ENABLED(wpd)) {
		DRW_shgroup_uniform_texture_ref(grp, "cavityBuffer", &e_data.cavity_buffer_tx);
	}
	if (SPECULAR_HIGHLIGHT_ENABLED(wpd) || STUDIOLIGHT_TYPE_MATCAP_ENABLED(wpd)) {
		DRW_shgroup_uniform_vec4(grp, "viewvecs[0]", (float *)wpd->viewvecs, 3);
	}
	if (SPECULAR_HIGHLIGHT_ENABLED(wpd) || STUDIOLIGHT_TYPE_MATCAP_ENABLED(wpd)) {
		DRW_shgroup_uniform_vec2(grp, "invertedViewportSize", DRW_viewport_invert_size_get(), 1);
	}
	if (STUDIOLIGHT_TYPE_MATCAP_ENABLED(wpd)) {
		BKE_studiolight_ensure_flag(wpd->studio_light, STUDIOLIGHT_EQUIRECT_RADIANCE_GPUTEXTURE);
		DRW_shgroup_uniform_texture(grp, "matcapImage", wpd->studio_light->equirect_radiance_gputexture);
	}
}

void workbench_deferred_cache_init(WORKBENCH_Data *vedata)
{
	WORKBENCH_StorageList *stl = vedata->stl;
	WORKBENCH_PassList *psl = vedata->psl;
	WORKBENCH_PrivateData *wpd = stl->g_data;
	DRWShadingGroup *grp;
	const DRWContextState *draw_ctx = DRW_context_state_get();

	Scene *scene = draw_ctx->scene;

	workbench_volume_cache_init(vedata);

	select_deferred_shaders(wpd);

	/* Background Pass */
	{
		psl->background_pass = DRW_pass_create(
		        "Background", DRW_STATE_WRITE_COLOR | DRW_STATE_DEPTH_EQUAL);
		grp = DRW_shgroup_create(wpd->background_sh, psl->background_pass);
		DRW_shgroup_uniform_block(grp, "world_block", wpd->world_ubo);
		DRW_shgroup_uniform_vec2(grp, "invertedViewportSize", DRW_viewport_invert_size_get(), 1);
		if (OBJECT_OUTLINE_ENABLED(wpd)) {
			DRW_shgroup_uniform_texture_ref(grp, "objectId", &e_data.object_id_tx);
		}
		DRW_shgroup_call_add(grp, DRW_cache_fullscreen_quad_get(), NULL);
	}

	/* Deferred Mix Pass */
	{
		workbench_private_data_get_light_direction(wpd, e_data.display.light_direction);
		studiolight_update_light(wpd, e_data.display.light_direction);

		float shadow_focus = scene->display.shadow_focus;
		/* Clamp to avoid overshadowing and shading errors. */
		CLAMP(shadow_focus, 0.0001f, 0.99999f);
		shadow_focus = 1.0f - shadow_focus * (1.0f - scene->display.shadow_shift);

		if (SHADOW_ENABLED(wpd)) {
			psl->composite_pass = DRW_pass_create(
			        "Composite", DRW_STATE_WRITE_COLOR | DRW_STATE_STENCIL_EQUAL | DRW_STATE_DEPTH_GREATER);
			grp = DRW_shgroup_create(wpd->composite_sh, psl->composite_pass);
			workbench_composite_uniforms(wpd, grp);
			DRW_shgroup_stencil_mask(grp, 0x00);
			DRW_shgroup_uniform_float_copy(grp, "lightMultiplier", 1.0f);
			DRW_shgroup_uniform_float(grp, "shadowMultiplier", &wpd->shadow_multiplier, 1);
			DRW_shgroup_uniform_float_copy(grp, "shadowShift", scene->display.shadow_shift);
			DRW_shgroup_uniform_float_copy(grp, "shadowFocus", shadow_focus);
			DRW_shgroup_call_add(grp, DRW_cache_fullscreen_quad_get(), NULL);

			/* Stencil Shadow passes. */
#ifdef DEBUG_SHADOW_VOLUME
			DRWState depth_pass_state = DRW_STATE_DEPTH_LESS | DRW_STATE_WRITE_COLOR | DRW_STATE_ADDITIVE;
			DRWState depth_fail_state = DRW_STATE_DEPTH_GREATER_EQUAL | DRW_STATE_WRITE_COLOR | DRW_STATE_ADDITIVE;
#else
			DRWState depth_pass_state = DRW_STATE_DEPTH_LESS | DRW_STATE_WRITE_STENCIL_SHADOW_PASS;
			DRWState depth_fail_state = DRW_STATE_DEPTH_LESS | DRW_STATE_WRITE_STENCIL_SHADOW_FAIL;
#endif
			psl->shadow_depth_pass_pass = DRW_pass_create("Shadow Pass", depth_pass_state);
			psl->shadow_depth_pass_mani_pass = DRW_pass_create("Shadow Pass Mani", depth_pass_state);
			psl->shadow_depth_fail_pass = DRW_pass_create("Shadow Fail", depth_fail_state);
			psl->shadow_depth_fail_mani_pass = DRW_pass_create("Shadow Fail Mani", depth_fail_state);
			psl->shadow_depth_fail_caps_pass = DRW_pass_create("Shadow Fail Caps", depth_fail_state);
			psl->shadow_depth_fail_caps_mani_pass = DRW_pass_create("Shadow Fail Caps Mani", depth_fail_state);

#ifndef DEBUG_SHADOW_VOLUME
			grp = DRW_shgroup_create(e_data.shadow_pass_sh, psl->shadow_depth_pass_pass);
			DRW_shgroup_stencil_mask(grp, 0xFF);
			grp = DRW_shgroup_create(e_data.shadow_pass_manifold_sh, psl->shadow_depth_pass_mani_pass);
			DRW_shgroup_stencil_mask(grp, 0xFF);
			grp = DRW_shgroup_create(e_data.shadow_fail_sh, psl->shadow_depth_fail_pass);
			DRW_shgroup_stencil_mask(grp, 0xFF);
			grp = DRW_shgroup_create(e_data.shadow_fail_manifold_sh, psl->shadow_depth_fail_mani_pass);
			DRW_shgroup_stencil_mask(grp, 0xFF);
			grp = DRW_shgroup_create(e_data.shadow_caps_sh, psl->shadow_depth_fail_caps_pass);
			DRW_shgroup_stencil_mask(grp, 0xFF);
			grp = DRW_shgroup_create(e_data.shadow_caps_manifold_sh, psl->shadow_depth_fail_caps_mani_pass);
			DRW_shgroup_stencil_mask(grp, 0xFF);

			psl->composite_shadow_pass = DRW_pass_create(
			        "Composite Shadow", DRW_STATE_WRITE_COLOR | DRW_STATE_STENCIL_NEQUAL | DRW_STATE_DEPTH_GREATER);
			grp = DRW_shgroup_create(wpd->composite_sh, psl->composite_shadow_pass);
			DRW_shgroup_stencil_mask(grp, 0x00);
			workbench_composite_uniforms(wpd, grp);
			DRW_shgroup_uniform_float(grp, "lightMultiplier", &wpd->shadow_multiplier, 1);
			DRW_shgroup_uniform_float(grp, "shadowMultiplier", &wpd->shadow_multiplier, 1);
			DRW_shgroup_uniform_float_copy(grp, "shadowShift", scene->display.shadow_shift);
			DRW_shgroup_uniform_float_copy(grp, "shadowFocus", shadow_focus);
			DRW_shgroup_call_add(grp, DRW_cache_fullscreen_quad_get(), NULL);
#endif
		}
		else {
			psl->composite_pass = DRW_pass_create(
			        "Composite", DRW_STATE_WRITE_COLOR | DRW_STATE_DEPTH_GREATER);
			grp = DRW_shgroup_create(wpd->composite_sh, psl->composite_pass);
			workbench_composite_uniforms(wpd, grp);
			DRW_shgroup_call_add(grp, DRW_cache_fullscreen_quad_get(), NULL);
		}
	}
}

static WORKBENCH_MaterialData *get_or_create_material_data(
        WORKBENCH_Data *vedata, Object *ob, Material *mat, Image *ima, int color_type, int interp)
{
	WORKBENCH_StorageList *stl = vedata->stl;
	WORKBENCH_PassList *psl = vedata->psl;
	WORKBENCH_PrivateData *wpd = stl->g_data;
	WORKBENCH_MaterialData *material;
	WORKBENCH_ObjectData *engine_object_data = (WORKBENCH_ObjectData *)DRW_drawdata_ensure(
	        &ob->id, &draw_engine_workbench_solid, sizeof(WORKBENCH_ObjectData), &workbench_init_object_data, NULL);
	WORKBENCH_MaterialData material_template;
	const bool is_ghost = (ob->dtx & OB_DRAWXRAY);

	/* Solid */
	workbench_material_update_data(wpd, ob, mat, &material_template);
	material_template.object_id = OBJECT_ID_PASS_ENABLED(wpd) ? engine_object_data->object_id : 1;
	material_template.color_type = color_type;
	material_template.ima = ima;
	material_template.interp = interp;
	uint hash = workbench_material_get_hash(&material_template, is_ghost);

	material = BLI_ghash_lookup(wpd->material_hash, POINTER_FROM_UINT(hash));
	if (material == NULL) {
		material = MEM_mallocN(sizeof(WORKBENCH_MaterialData), __func__);
		material->shgrp = DRW_shgroup_create(
		        (color_type == V3D_SHADING_TEXTURE_COLOR) ? wpd->prepass_texture_sh: wpd->prepass_solid_sh,
		        (ob->dtx & OB_DRAWXRAY) ? psl->ghost_prepass_pass : psl->prepass_pass);
		workbench_material_copy(material, &material_template);
		DRW_shgroup_stencil_mask(material->shgrp, (ob->dtx & OB_DRAWXRAY) ? 0x00 : 0xFF);
		DRW_shgroup_uniform_int(material->shgrp, "object_id", &material->object_id, 1);
		workbench_material_shgroup_uniform(wpd, material->shgrp, material, ob, true, true, interp);

		BLI_ghash_insert(wpd->material_hash, POINTER_FROM_UINT(hash), material);
	}
	return material;
}

static void workbench_cache_populate_particles(WORKBENCH_Data *vedata, Object *ob)
{
	WORKBENCH_StorageList *stl = vedata->stl;
	WORKBENCH_PassList *psl = vedata->psl;
	WORKBENCH_PrivateData *wpd = stl->g_data;

	for (ModifierData *md = ob->modifiers.first; md; md = md->next) {
		if (md->type != eModifierType_ParticleSystem) {
			continue;
		}
		ParticleSystem *psys = ((ParticleSystemModifierData *)md)->psys;
		if (!psys_check_enabled(ob, psys, false)) {
			continue;
		}
		if (!DRW_object_is_visible_psys_in_active_context(ob, psys)) {
			continue;
		}
		ParticleSettings *part = psys->part;
		const int draw_as = (part->draw_as == PART_DRAW_REND) ? part->ren_as : part->draw_as;

		if (draw_as == PART_DRAW_PATH) {
			Material *mat;
			Image *image;
			int interp;
			workbench_material_get_image_and_mat(ob, part->omat, &image, &interp, &mat);
			int color_type = workbench_material_determine_color_type(wpd, image, ob);
			WORKBENCH_MaterialData *material = get_or_create_material_data(vedata, ob, mat, image, color_type, interp);

			struct GPUShader *shader = (color_type != V3D_SHADING_TEXTURE_COLOR) ?
			        wpd->prepass_solid_hair_sh :
			        wpd->prepass_texture_hair_sh;
			DRWShadingGroup *shgrp = DRW_shgroup_hair_create(
			        ob, psys, md,
			        (ob->dtx & OB_DRAWXRAY) ? psl->ghost_prepass_hair_pass : psl->prepass_hair_pass,
			        shader);
			DRW_shgroup_stencil_mask(shgrp, (ob->dtx & OB_DRAWXRAY) ? 0x00 : 0xFF);
			DRW_shgroup_uniform_int(shgrp, "object_id", &material->object_id, 1);
			workbench_material_shgroup_uniform(wpd, shgrp, material, ob, true, true, interp);
		}
	}
}

void workbench_deferred_solid_cache_populate(WORKBENCH_Data *vedata, Object *ob)
{
	WORKBENCH_StorageList *stl = vedata->stl;
	WORKBENCH_PassList *psl = vedata->psl;
	WORKBENCH_PrivateData *wpd = stl->g_data;
	const DRWContextState *draw_ctx = DRW_context_state_get();
	Scene *scene = draw_ctx->scene;

	if (!DRW_object_is_renderable(ob))
		return;

	if (ob->type == OB_MESH) {
		workbench_cache_populate_particles(vedata, ob);
	}

	ModifierData *md;
	if (((ob->base_flag & BASE_FROM_DUPLI) == 0) &&
	    (md = modifiers_findByType(ob, eModifierType_Smoke)) &&
	    (modifier_isEnabled(scene, md, eModifierMode_Realtime)) &&
	    (((SmokeModifierData *)md)->domain != NULL))
	{
		workbench_volume_cache_populate(vedata, scene, ob, md);
		return; /* Do not draw solid in this case. */
	}

	if (!(DRW_object_visibility_in_active_context(ob) & OB_VISIBLE_SELF)) {
		return;
	}
	if (ob->dt < OB_SOLID) {
		return;
	}

	WORKBENCH_MaterialData *material;
	if (ELEM(ob->type, OB_MESH, OB_CURVE, OB_SURF, OB_FONT, OB_MBALL)) {
		const bool is_active = (ob == draw_ctx->obact);
		const bool is_sculpt_mode = is_active && (draw_ctx->object_mode & OB_MODE_SCULPT) != 0;
		const bool use_hide = is_active && DRW_object_use_hide_faces(ob);
		const int materials_len = MAX2(1, (is_sculpt_mode ? 1 : ob->totcol));
		const Mesh *me = (ob->type == OB_MESH) ? ob->data : NULL;

		if (!is_sculpt_mode && me && me->mloopuv && TEXTURE_DRAWING_ENABLED(wpd)) {
			/* Draw textured */
			struct GPUBatch **geom_array = DRW_cache_mesh_surface_texpaint_get(ob);
			for (int i = 0; i < materials_len; i++) {
				if (geom_array != NULL && geom_array[i] != NULL) {
					Material *mat;
					Image *image;
					int interp;
					workbench_material_get_image_and_mat(ob, i + 1, &image, &interp, &mat);
					int color_type = workbench_material_determine_color_type(wpd, image, ob);
					material = get_or_create_material_data(vedata, ob, mat, image, color_type, interp);
					DRW_shgroup_call_object_add(material->shgrp, geom_array[i], ob);
				}
			}
		}
		else if (ELEM(wpd->shading.color_type,
		              V3D_SHADING_SINGLE_COLOR, V3D_SHADING_OBJECT_COLOR, V3D_SHADING_RANDOM_COLOR))
		{
			/* Draw solid color */
			material = get_or_create_material_data(vedata, ob, NULL, NULL, wpd->shading.color_type, 0);
			if (is_sculpt_mode) {
				DRW_shgroup_call_sculpt_add(material->shgrp, ob, ob->obmat);
			}
			else {
				struct GPUBatch *geom = DRW_cache_object_surface_get(ob);
				if (geom) {
					DRW_shgroup_call_object_add(material->shgrp, geom, ob);
				}
			}
		}
		else {
			/* Draw material color */
			if (is_sculpt_mode) {
				/* Multiple materials are not supported in sculpt mode yet. */
				Material *mat = give_current_material(ob, 1);
				material = get_or_create_material_data(vedata, ob, mat, NULL, V3D_SHADING_MATERIAL_COLOR, 0);
				DRW_shgroup_call_sculpt_add(material->shgrp, ob, ob->obmat);
			}
			else {
				struct GPUBatch **geoms;
				struct GPUMaterial **gpumat_array = BLI_array_alloca(gpumat_array, materials_len);
				memset(gpumat_array, 0, sizeof(*gpumat_array) * materials_len);

				geoms = DRW_cache_object_surface_material_get(ob, gpumat_array, materials_len, NULL, NULL, NULL);
				for (int i = 0; i < materials_len; ++i) {
					if (geoms != NULL && geoms[i] != NULL) {
						Material *mat = give_current_material(ob, i + 1);
						material = get_or_create_material_data(vedata, ob, mat, NULL, V3D_SHADING_MATERIAL_COLOR, 0);
						DRW_shgroup_call_object_add(material->shgrp, geoms[i], ob);
					}
				}
			}
		}

		if (SHADOW_ENABLED(wpd) && (ob->display.flag & OB_SHOW_SHADOW)) {
			bool is_manifold;
			struct GPUBatch *geom_shadow = DRW_cache_object_edge_detection_get(ob, &is_manifold);
			if (geom_shadow) {
				if (is_sculpt_mode || use_hide) {
					/* Currently unsupported in sculpt mode. We could revert to the slow
					 * method in this case but I'm not sure if it's a good idea given that
					 * sculpted meshes are heavy to begin with. */
					// DRW_shgroup_call_sculpt_add(wpd->shadow_shgrp, ob, ob->obmat);
				}
				else {
					WORKBENCH_ObjectData *engine_object_data = (WORKBENCH_ObjectData *)DRW_drawdata_ensure(
					        &ob->id, &draw_engine_workbench_solid, sizeof(WORKBENCH_ObjectData), &workbench_init_object_data, NULL);

					if (studiolight_object_cast_visible_shadow(wpd, ob, engine_object_data)) {

						invert_m4_m4(ob->imat, ob->obmat);
						mul_v3_mat3_m4v3(engine_object_data->shadow_dir, ob->imat, e_data.display.light_direction);

						DRWShadingGroup *grp;
						bool use_shadow_pass_technique = !studiolight_camera_in_object_shadow(wpd, ob, engine_object_data);

						if (use_shadow_pass_technique) {
							if (is_manifold) {
								grp = DRW_shgroup_create(e_data.shadow_pass_manifold_sh, psl->shadow_depth_pass_mani_pass);
							}
							else {
								grp = DRW_shgroup_create(e_data.shadow_pass_sh, psl->shadow_depth_pass_pass);
							}
							DRW_shgroup_uniform_vec3(grp, "lightDirection", engine_object_data->shadow_dir, 1);
							DRW_shgroup_uniform_float_copy(grp, "lightDistance", 1e5f);
							DRW_shgroup_call_add(grp, geom_shadow, ob->obmat);
#ifdef DEBUG_SHADOW_VOLUME
							DRW_debug_bbox(&engine_object_data->shadow_bbox, (float[4]){1.0f, 0.0f, 0.0f, 1.0f});
#endif
						}
						else {
							float extrude_distance = studiolight_object_shadow_distance(wpd, ob, engine_object_data);

							/* TODO(fclem): only use caps if they are in the view frustum. */
							const bool need_caps = true;
							if (need_caps) {
								if (is_manifold) {
									grp = DRW_shgroup_create(e_data.shadow_caps_manifold_sh, psl->shadow_depth_fail_caps_mani_pass);
								}
								else {
									grp = DRW_shgroup_create(e_data.shadow_caps_sh, psl->shadow_depth_fail_caps_pass);
								}
								DRW_shgroup_uniform_vec3(grp, "lightDirection", engine_object_data->shadow_dir, 1);
								DRW_shgroup_uniform_float_copy(grp, "lightDistance", extrude_distance);
								DRW_shgroup_call_add(grp, DRW_cache_object_surface_get(ob), ob->obmat);
							}

							if (is_manifold) {
								grp = DRW_shgroup_create(e_data.shadow_fail_manifold_sh, psl->shadow_depth_fail_mani_pass);
							}
							else {
								grp = DRW_shgroup_create(e_data.shadow_fail_sh, psl->shadow_depth_fail_pass);
							}
							DRW_shgroup_uniform_vec3(grp, "lightDirection", engine_object_data->shadow_dir, 1);
							DRW_shgroup_uniform_float_copy(grp, "lightDistance", extrude_distance);
							DRW_shgroup_call_add(grp, geom_shadow, ob->obmat);
#ifdef DEBUG_SHADOW_VOLUME
							DRW_debug_bbox(&engine_object_data->shadow_bbox, (float[4]){0.0f, 1.0f, 0.0f, 1.0f});
#endif
						}
					}
				}
			}
		}
	}
}

void workbench_deferred_cache_finish(WORKBENCH_Data *UNUSED(vedata))
{
}

void workbench_deferred_draw_background(WORKBENCH_Data *vedata)
{
	WORKBENCH_StorageList *stl = vedata->stl;
	WORKBENCH_FramebufferList *fbl = vedata->fbl;
	WORKBENCH_PrivateData *wpd = stl->g_data;
	const float clear_depth = 1.0f;
	const float clear_color[4] = {0.0f, 0.0f, 0.0f, 0.0f};
	uint clear_stencil = 0x00;

	DRW_stats_group_start("Clear Background");

	if (OBJECT_ID_PASS_ENABLED(wpd)) {
		/* From all the color buffers, only object id needs to be cleared. */
		GPU_framebuffer_bind(fbl->id_clear_fb);
		GPU_framebuffer_clear_color(fbl->id_clear_fb, clear_color);
	}

	GPU_framebuffer_bind(fbl->prepass_fb);
	int clear_bits = GPU_DEPTH_BIT;
	SET_FLAG_FROM_TEST(clear_bits, SHADOW_ENABLED(wpd), GPU_STENCIL_BIT);
	GPU_framebuffer_clear(fbl->prepass_fb, clear_bits, clear_color, clear_depth, clear_stencil);
	DRW_stats_group_end();
}

void workbench_deferred_draw_scene(WORKBENCH_Data *vedata)
{
	WORKBENCH_PassList *psl = vedata->psl;
	WORKBENCH_StorageList *stl = vedata->stl;
	WORKBENCH_FramebufferList *fbl = vedata->fbl;
	WORKBENCH_PrivateData *wpd = stl->g_data;
	DefaultFramebufferList *dfbl = DRW_viewport_framebuffer_list_get();

	if (TAA_ENABLED(wpd)) {
		workbench_taa_draw_scene_start(vedata);
	}

	/* clear in background */
	GPU_framebuffer_bind(fbl->prepass_fb);
	DRW_draw_pass(psl->prepass_pass);
	DRW_draw_pass(psl->prepass_hair_pass);

	if (GHOST_ENABLED(psl)) {
		/* meh, late init to not request a depth buffer we won't use. */
		workbench_setup_ghost_framebuffer(fbl);

		GPU_framebuffer_bind(fbl->ghost_prepass_fb);
		GPU_framebuffer_clear_depth(fbl->ghost_prepass_fb, 1.0f);
		DRW_draw_pass(psl->ghost_prepass_pass);
		DRW_draw_pass(psl->ghost_prepass_hair_pass);

		GPU_framebuffer_bind(dfbl->depth_only_fb);
		DRW_draw_pass(psl->ghost_resolve_pass);
	}

	if (CAVITY_ENABLED(wpd)) {
		GPU_framebuffer_bind(fbl->cavity_fb);
		DRW_draw_pass(psl->cavity_pass);
	}

	if (SHADOW_ENABLED(wpd)) {
#ifdef DEBUG_SHADOW_VOLUME
		GPU_framebuffer_bind(fbl->composite_fb);
		DRW_draw_pass(psl->composite_pass);
#else
		GPU_framebuffer_bind(dfbl->depth_only_fb);
#endif
		DRW_draw_pass(psl->shadow_depth_pass_pass);
		DRW_draw_pass(psl->shadow_depth_pass_mani_pass);
		DRW_draw_pass(psl->shadow_depth_fail_pass);
		DRW_draw_pass(psl->shadow_depth_fail_mani_pass);
		DRW_draw_pass(psl->shadow_depth_fail_caps_pass);
		DRW_draw_pass(psl->shadow_depth_fail_caps_mani_pass);

		if (GHOST_ENABLED(psl)) {
			/* We need to set the stencil buffer to 0 where Ghost objects
			 * else they will get shadow and even badly shadowed. */
			DRW_pass_state_set(psl->ghost_prepass_pass, DRW_STATE_DEPTH_EQUAL | DRW_STATE_WRITE_STENCIL);
			DRW_pass_state_set(psl->ghost_prepass_hair_pass, DRW_STATE_DEPTH_EQUAL | DRW_STATE_WRITE_STENCIL);

			DRW_draw_pass(psl->ghost_prepass_pass);
			DRW_draw_pass(psl->ghost_prepass_hair_pass);
		}
#ifndef DEBUG_SHADOW_VOLUME
		GPU_framebuffer_bind(fbl->composite_fb);
		DRW_draw_pass(psl->composite_pass);
		DRW_draw_pass(psl->composite_shadow_pass);
#endif
	}
	else {
		GPU_framebuffer_bind(fbl->composite_fb);
		DRW_draw_pass(psl->composite_pass);
	}

	/* TODO(fclem): only enable when needed (when there is overlays). */
	if (GHOST_ENABLED(psl)) {
		/* In order to not draw on top of ghost objects, we clear the stencil
		 * to 0xFF and the ghost object to 0x00 and only draw overlays on top if
		 * stencil is not 0. */
		GPU_framebuffer_bind(dfbl->depth_only_fb);
		GPU_framebuffer_clear_stencil(dfbl->depth_only_fb, 0xFF);

		DRW_pass_state_set(psl->ghost_prepass_pass, DRW_STATE_DEPTH_EQUAL | DRW_STATE_WRITE_STENCIL);
		DRW_pass_state_set(psl->ghost_prepass_hair_pass, DRW_STATE_DEPTH_EQUAL | DRW_STATE_WRITE_STENCIL);

		DRW_draw_pass(psl->ghost_prepass_pass);
		DRW_draw_pass(psl->ghost_prepass_hair_pass);
	}

	GPU_framebuffer_bind(fbl->composite_fb);
	DRW_draw_pass(psl->background_pass);

	if (wpd->volumes_do) {
		GPU_framebuffer_bind(fbl->volume_fb);
		DRW_draw_pass(psl->volume_pass);
	}

	workbench_aa_draw_pass(vedata, e_data.composite_buffer_tx);
}

void workbench_deferred_draw_finish(WORKBENCH_Data *vedata)
{
	WORKBENCH_StorageList *stl = vedata->stl;
	WORKBENCH_PrivateData *wpd = stl->g_data;

	workbench_private_data_free(wpd);
	workbench_volume_smoke_textures_free(wpd);
}
