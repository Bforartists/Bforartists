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

/** \file eevee_private.h
 *  \ingroup DNA
 */

#ifndef __EEVEE_PRIVATE_H__
#define __EEVEE_PRIVATE_H__

struct Object;

extern struct DrawEngineType draw_engine_eevee_type;

/* Minimum UBO is 16384 bytes */
#define MAX_PROBE 128 /* TODO : find size by dividing UBO max size by probe data size */
#define MAX_GRID 64 /* TODO : find size by dividing UBO max size by grid data size */
#define MAX_PLANAR 16 /* TODO : find size by dividing UBO max size by grid data size */
#define MAX_LIGHT 128 /* TODO : find size by dividing UBO max size by light data size */
#define MAX_SHADOW_CUBE 42 /* TODO : Make this depends on GL_MAX_ARRAY_TEXTURE_LAYERS */
#define MAX_SHADOW_MAP 64
#define MAX_SHADOW_CASCADE 8
#define MAX_CASCADE_NUM 4
#define MAX_BLOOM_STEP 16

/* Only define one of these. */
// #define IRRADIANCE_SH_L2
// #define IRRADIANCE_CUBEMAP
#define IRRADIANCE_HL2

/* World shader variations */
enum {
	VAR_WORLD_BACKGROUND    = 0,
	VAR_WORLD_PROBE         = 1,
	VAR_WORLD_VOLUME        = 2,

	VAR_VOLUME_SHADOW     = (1 << 2),
	VAR_VOLUME_HOMO       = (1 << 3),
	VAR_VOLUME_LIGHT      = (1 << 4),
	VAR_VOLUME_COLOR      = (1 << 5),
};

/* Material shader variations */
enum {
	VAR_MAT_MESH     = (1 << 0),
	VAR_MAT_PROBE    = (1 << 1),
	VAR_MAT_HAIR     = (1 << 2),
	VAR_MAT_AO       = (1 << 3),
	VAR_MAT_FLAT     = (1 << 4),
	VAR_MAT_BENT     = (1 << 5),
	VAR_MAT_BLEND    = (1 << 6),
	/* Max number of variation */
	/* IMPORTANT : Leave it last and set
	 * it's value accordingly. */
	VAR_MAT_MAX      = (1 << 7),
	/* These are options that are not counted in VAR_MAT_MAX
	 * because they are not cumulative with the others above. */
	VAR_MAT_CLIP     = (1 << 8),
	VAR_MAT_HASH     = (1 << 9),
	VAR_MAT_MULT     = (1 << 10),
	VAR_MAT_SHADOW   = (1 << 11),
};

typedef struct EEVEE_PassList {
	/* Shadows */
	struct DRWPass *shadow_pass;
	struct DRWPass *shadow_cube_pass;
	struct DRWPass *shadow_cube_store_pass;
	struct DRWPass *shadow_cascade_pass;

	/* Probes */
	struct DRWPass *probe_background;
	struct DRWPass *probe_glossy_compute;
	struct DRWPass *probe_diffuse_compute;
	struct DRWPass *probe_display;
	struct DRWPass *probe_planar_downsample_ps;

	/* Effects */
	struct DRWPass *motion_blur;
	struct DRWPass *bloom_blit;
	struct DRWPass *bloom_downsample_first;
	struct DRWPass *bloom_downsample;
	struct DRWPass *bloom_upsample;
	struct DRWPass *bloom_resolve;
	struct DRWPass *dof_down;
	struct DRWPass *dof_scatter;
	struct DRWPass *dof_resolve;
	struct DRWPass *volumetric_integrate_ps;
	struct DRWPass *volumetric_resolve_ps;
	struct DRWPass *volumetric_resolve_transmit_ps;
	struct DRWPass *ssr_raytrace;
	struct DRWPass *ssr_resolve;
	struct DRWPass *color_downsample_ps;

	/* HiZ */
	struct DRWPass *minz_downlevel_ps;
	struct DRWPass *maxz_downlevel_ps;
	struct DRWPass *minz_downdepth_ps;
	struct DRWPass *maxz_downdepth_ps;
	struct DRWPass *minz_copydepth_ps;
	struct DRWPass *maxz_copydepth_ps;

	struct DRWPass *depth_pass;
	struct DRWPass *depth_pass_cull;
	struct DRWPass *depth_pass_clip;
	struct DRWPass *depth_pass_clip_cull;
	struct DRWPass *default_pass[VAR_MAT_MAX];
	struct DRWPass *material_pass;
	struct DRWPass *transparent_pass;
	struct DRWPass *background_pass;
} EEVEE_PassList;

typedef struct EEVEE_FramebufferList {
	/* Effects */
	struct GPUFrameBuffer *downsample_fb;
	struct GPUFrameBuffer *effect_fb;
	struct GPUFrameBuffer *bloom_blit_fb;
	struct GPUFrameBuffer *bloom_down_fb[MAX_BLOOM_STEP];
	struct GPUFrameBuffer *bloom_accum_fb[MAX_BLOOM_STEP-1];
	struct GPUFrameBuffer *dof_down_fb;
	struct GPUFrameBuffer *dof_scatter_far_fb;
	struct GPUFrameBuffer *dof_scatter_near_fb;
	struct GPUFrameBuffer *volumetric_fb;
	struct GPUFrameBuffer *screen_tracing_fb;

	struct GPUFrameBuffer *planarref_fb;

	struct GPUFrameBuffer *main;
	struct GPUFrameBuffer *double_buffer;
} EEVEE_FramebufferList;

typedef struct EEVEE_TextureList {
	/* Effects */
	struct GPUTexture *color_post; /* R16_G16_B16 */
	struct GPUTexture *dof_down_near; /* R16_G16_B16_A16 */
	struct GPUTexture *dof_down_far; /* R16_G16_B16_A16 */
	struct GPUTexture *dof_coc; /* R16_G16 */
	struct GPUTexture *dof_near_blur; /* R16_G16_B16_A16 */
	struct GPUTexture *dof_far_blur; /* R16_G16_B16_A16 */
	struct GPUTexture *bloom_blit; /* R16_G16_B16 */
	struct GPUTexture *bloom_downsample[MAX_BLOOM_STEP]; /* R16_G16_B16 */
	struct GPUTexture *bloom_upsample[MAX_BLOOM_STEP-1]; /* R16_G16_B16 */

	struct GPUTexture *ssr_normal_input;
	struct GPUTexture *ssr_specrough_input;

	struct GPUTexture *planar_pool;

	struct GPUTexture *maxzbuffer;

	struct GPUTexture *color; /* R16_G16_B16 */
	struct GPUTexture *color_double_buffer;
} EEVEE_TextureList;

typedef struct EEVEE_StorageList {
	/* Effects */
	struct EEVEE_EffectsInfo *effects;

	struct EEVEE_PrivateData *g_data;
} EEVEE_StorageList;

/* ************ LIGHT UBO ************* */
typedef struct EEVEE_Light {
	float position[3], dist;
	float color[3], spec;
	float spotsize, spotblend, radius, shadowid;
	float rightvec[3], sizex;
	float upvec[3], sizey;
	float forwardvec[3], lamptype;
} EEVEE_Light;

typedef struct EEVEE_ShadowCube {
	float near, far, bias, exp;
} EEVEE_ShadowCube;

typedef struct EEVEE_ShadowMap {
	float shadowmat[4][4]; /* World->Lamp->NDC->Tex : used for sampling the shadow map. */
	float near, far, bias, pad;
} EEVEE_ShadowMap;

typedef struct EEVEE_ShadowCascade {
	float shadowmat[MAX_CASCADE_NUM][4][4]; /* World->Lamp->NDC->Tex : used for sampling the shadow map. */
	float split[4];
	float bias[4];
} EEVEE_ShadowCascade;

typedef struct EEVEE_ShadowRender {
	float shadowmat[6][4][4]; /* World->Lamp->NDC : used to render the shadow map. 6 frustrum for cubemap shadow */
	float viewmat[6][4][4]; /* World->Lamp : used to render the shadow map. 6 viewmat for cubemap shadow */
	float position[3];
	float pad;
	int layer;
	float exponent;
} EEVEE_ShadowRender;

/* ************ VOLUME DATA ************ */
typedef struct EEVEE_VolumetricsInfo {
	float integration_step_count, shadow_step_count, sample_distribution, light_clamp;
	float integration_start, integration_end;
	bool use_lights, use_volume_shadows, use_colored_transmit;
} EEVEE_VolumetricsInfo;

/* ************ LIGHT DATA ************* */
typedef struct EEVEE_LampsInfo {
	int num_light, cache_num_light;
	int num_cube, cache_num_cube;
	int num_map, cache_num_map;
	int num_cascade, cache_num_cascade;
	int update_flag;
	/* List of lights in the scene. */
	/* XXX This is fragile, can get out of sync quickly. */
	struct Object *light_ref[MAX_LIGHT];
	struct Object *shadow_cube_ref[MAX_SHADOW_CUBE];
	struct Object *shadow_map_ref[MAX_SHADOW_MAP];
	struct Object *shadow_cascade_ref[MAX_SHADOW_CASCADE];
	/* UBO Storage : data used by UBO */
	struct EEVEE_Light         light_data[MAX_LIGHT];
	struct EEVEE_ShadowRender  shadow_render_data;
	struct EEVEE_ShadowCube    shadow_cube_data[MAX_SHADOW_CUBE];
	struct EEVEE_ShadowMap     shadow_map_data[MAX_SHADOW_MAP];
	struct EEVEE_ShadowCascade shadow_cascade_data[MAX_SHADOW_CASCADE];
} EEVEE_LampsInfo;

/* EEVEE_LampsInfo->update_flag */
enum {
	LIGHT_UPDATE_SHADOW_CUBE = (1 << 0),
};

/* ************ PROBE UBO ************* */
typedef struct EEVEE_LightProbe {
	float position[3], parallax_type;
	float attenuation_fac;
	float attenuation_type;
	float pad3[2];
	float attenuationmat[4][4];
	float parallaxmat[4][4];
} EEVEE_LightProbe;

typedef struct EEVEE_LightGrid {
	float mat[4][4];
	int resolution[3], offset;
	float corner[3], attenuation_scale;
	float increment_x[3], attenuation_bias; /* world space vector between 2 opposite cells */
	float increment_y[3], pad3;
	float increment_z[3], pad4;
} EEVEE_LightGrid;

typedef struct EEVEE_PlanarReflection {
	float plane_equation[4];
	float clip_vec_x[3], attenuation_scale;
	float clip_vec_y[3], attenuation_bias;
	float clip_edge_x_pos, clip_edge_x_neg;
	float clip_edge_y_pos, clip_edge_y_neg;
	float facing_scale, facing_bias, pad[2];
	float reflectionmat[4][4];
} EEVEE_PlanarReflection;

/* ************ PROBE DATA ************* */
typedef struct EEVEE_LightProbesInfo {
	int num_cube, cache_num_cube;
	int num_grid, cache_num_grid;
	int num_planar, cache_num_planar;
	int update_flag;
	int updated_bounce;
	/* Actual number of probes that have datas. */
	int num_render_cube;
	int num_render_grid;
	/* For rendering probes */
	float probemat[6][4][4];
	int layer;
	float texel_size;
	float padding_size;
	float samples_ct;
	float invsamples_ct;
	float roughness;
	float lodfactor;
	float lod_rt_max, lod_cube_max, lod_planar_max;
	int shres;
	int shnbr;
	bool specular_toggle;
	/* List of probes in the scene. */
	/* XXX This is fragile, can get out of sync quickly. */
	struct Object *probes_cube_ref[MAX_PROBE];
	struct Object *probes_grid_ref[MAX_GRID];
	struct Object *probes_planar_ref[MAX_PLANAR];
	/* UBO Storage : data used by UBO */
	struct EEVEE_LightProbe probe_data[MAX_PROBE];
	struct EEVEE_LightGrid grid_data[MAX_GRID];
	struct EEVEE_PlanarReflection planar_data[MAX_PLANAR];
} EEVEE_LightProbesInfo;

/* EEVEE_LightProbesInfo->update_flag */
enum {
	PROBE_UPDATE_CUBE = (1 << 0),
};

/* ************ EFFECTS DATA ************* */
typedef struct EEVEE_EffectsInfo {
	int enabled_effects;

	/* SSR */
	bool use_ssr;
	bool reflection_trace_full;
	float ssr_border_fac;
	float ssr_stride;
	float ssr_thickness;

	/* Ambient Occlusion */
	bool use_ao, use_bent_normals;
	float ao_dist, ao_samples, ao_factor;

	/* Motion Blur */
	float current_ndc_to_world[4][4];
	float past_world_to_ndc[4][4];
	float tmp_mat[4][4];
	int motion_blur_samples;

	/* Depth Of Field */
	float dof_near_far[2];
	float dof_params[3];
	float dof_bokeh[4];
	float dof_layer_select[2];
	int dof_target_size[2];

	/* Bloom */
	int bloom_iteration_ct;
	float source_texel_size[2];
	float blit_texel_size[2];
	float downsamp_texel_size[MAX_BLOOM_STEP][2];
	float bloom_intensity;
	float bloom_sample_scale;
	float bloom_curve_threshold[4];
	float unf_source_texel_size[2];
	struct GPUTexture *unf_source_buffer; /* pointer copy */
	struct GPUTexture *unf_base_buffer; /* pointer copy */

	/* Not alloced, just a copy of a *GPUtexture in EEVEE_TextureList. */
	struct GPUTexture *source_buffer;       /* latest updated texture */
	struct GPUFrameBuffer *target_buffer;   /* next target to render to */
} EEVEE_EffectsInfo;

enum {
	EFFECT_MOTION_BLUR         = (1 << 0),
	EFFECT_BLOOM               = (1 << 1),
	EFFECT_DOF                 = (1 << 2),
	EFFECT_VOLUMETRIC          = (1 << 3),
	EFFECT_SSR                 = (1 << 4),
	EFFECT_DOUBLE_BUFFER       = (1 << 5), /* Not really an effect but a feature */
};

/* ************** SCENE LAYER DATA ************** */
typedef struct EEVEE_SceneLayerData {
	/* Lamps */
	struct EEVEE_LampsInfo *lamps;

	struct GPUUniformBuffer *light_ubo;
	struct GPUUniformBuffer *shadow_ubo;
	struct GPUUniformBuffer *shadow_render_ubo;

	struct GPUFrameBuffer *shadow_cube_target_fb;
	struct GPUFrameBuffer *shadow_cube_fb;
	struct GPUFrameBuffer *shadow_map_fb;
	struct GPUFrameBuffer *shadow_cascade_fb;

	struct GPUTexture *shadow_depth_cube_target;
	struct GPUTexture *shadow_color_cube_target;
	struct GPUTexture *shadow_depth_cube_pool;
	struct GPUTexture *shadow_depth_map_pool;
	struct GPUTexture *shadow_depth_cascade_pool;

	struct ListBase shadow_casters; /* Shadow casters gathered during cache iteration */

	/* Probes */
	struct EEVEE_LightProbesInfo *probes;

	struct GPUUniformBuffer *probe_ubo;
	struct GPUUniformBuffer *grid_ubo;
	struct GPUUniformBuffer *planar_ubo;

	struct GPUFrameBuffer *probe_fb;
	struct GPUFrameBuffer *probe_filter_fb;

	struct GPUTexture *probe_rt;
	struct GPUTexture *probe_pool;
	struct GPUTexture *irradiance_pool;
	struct GPUTexture *irradiance_rt;

	struct ListBase probe_queue; /* List of probes to update */

	/* Volumetrics */
	struct EEVEE_VolumetricsInfo *volumetrics;
} EEVEE_SceneLayerData;

/* ************ OBJECT DATA ************ */
typedef struct EEVEE_LampEngineData {
	bool need_update;
	struct ListBase shadow_caster_list;
	void *storage; /* either EEVEE_LightData, EEVEE_ShadowCubeData, EEVEE_ShadowCascadeData */
} EEVEE_LampEngineData;

typedef struct EEVEE_LightProbeEngineData {
	bool need_update;
	bool ready_to_shade;
	int updated_cells;
	int num_cell;
	int probe_id; /* Only used for display data */
	/* For planar reflection rendering */
	float viewmat[4][4];
	float persmat[4][4];
	float planer_eq_offset[4];
	struct ListBase captured_object_list;
} EEVEE_LightProbeEngineData;

typedef struct EEVEE_ObjectEngineData {
	bool need_update;
} EEVEE_ObjectEngineData;

/* *********************************** */

typedef struct EEVEE_Data {
	void *engine_type;
	EEVEE_FramebufferList *fbl;
	EEVEE_TextureList *txl;
	EEVEE_PassList *psl;
	EEVEE_StorageList *stl;
} EEVEE_Data;

typedef struct EEVEE_PrivateData {
	struct DRWShadingGroup *shadow_shgrp;
	struct DRWShadingGroup *depth_shgrp;
	struct DRWShadingGroup *depth_shgrp_cull;
	struct DRWShadingGroup *depth_shgrp_clip;
	struct DRWShadingGroup *depth_shgrp_clip_cull;
	struct DRWShadingGroup *cube_display_shgrp;
	struct DRWShadingGroup *planar_downsample;
	struct GHash *material_hash;
	struct GHash *hair_material_hash;
	struct GPUTexture *minzbuffer;
	struct GPUTexture *ssr_hit_output;
	struct GPUTexture *ssr_pdf_output;
	struct GPUTexture *volumetric;
	struct GPUTexture *volumetric_transmit;
	float background_alpha; /* TODO find a better place for this. */
	float viewvecs[2][4];
	/* For planar probes */
	float texel_size[2];
	/* For double buffering */
	bool valid_double_buffer;
	float prev_persmat[4][4];
	float next_persmat[4][4];
} EEVEE_PrivateData; /* Transient data */

/* eevee_data.c */
EEVEE_SceneLayerData *EEVEE_scene_layer_data_get(void);
EEVEE_ObjectEngineData *EEVEE_object_data_get(Object *ob);
EEVEE_LightProbeEngineData *EEVEE_lightprobe_data_get(Object *ob);
EEVEE_LampEngineData *EEVEE_lamp_data_get(Object *ob);

/* eevee_materials.c */
struct GPUTexture *EEVEE_materials_get_util_tex(void); /* XXX */
void EEVEE_materials_init(EEVEE_StorageList *stl);
void EEVEE_materials_cache_init(EEVEE_Data *vedata);
void EEVEE_materials_cache_populate(EEVEE_Data *vedata, EEVEE_SceneLayerData *sldata, Object *ob);
void EEVEE_materials_cache_finish(EEVEE_Data *vedata);
struct GPUMaterial *EEVEE_material_world_lightprobe_get(struct Scene *scene, struct World *wo);
struct GPUMaterial *EEVEE_material_world_background_get(struct Scene *scene, struct World *wo);
struct GPUMaterial *EEVEE_material_world_volume_get(
        struct Scene *scene, struct World *wo, bool use_lights, bool use_volume_shadows, bool is_homogeneous, bool use_color_transmit);
struct GPUMaterial *EEVEE_material_mesh_get(
        struct Scene *scene, Material *ma, bool use_ao, bool use_bent_normals, bool use_blend, bool use_multiply);
struct GPUMaterial *EEVEE_material_mesh_depth_get(struct Scene *scene, Material *ma, bool use_hashed_alpha, bool is_shadow);
struct GPUMaterial *EEVEE_material_hair_get(struct Scene *scene, Material *ma, bool use_ao, bool use_bent_normals);
void EEVEE_materials_free(void);
void EEVEE_draw_default_passes(EEVEE_PassList *psl);

/* eevee_lights.c */
void EEVEE_lights_init(EEVEE_SceneLayerData *sldata);
void EEVEE_lights_cache_init(EEVEE_SceneLayerData *sldata, EEVEE_PassList *psl);
void EEVEE_lights_cache_add(EEVEE_SceneLayerData *sldata, struct Object *ob);
void EEVEE_lights_cache_shcaster_add(EEVEE_SceneLayerData *sldata, EEVEE_PassList *psl, struct Gwn_Batch *geom, float (*obmat)[4]);
void EEVEE_lights_cache_shcaster_material_add(
	EEVEE_SceneLayerData *sldata, EEVEE_PassList *psl,
	struct GPUMaterial *gpumat, struct Gwn_Batch *geom, float (*obmat)[4], float *alpha_threshold);
void EEVEE_lights_cache_finish(EEVEE_SceneLayerData *sldata);
void EEVEE_lights_update(EEVEE_SceneLayerData *sldata);
void EEVEE_draw_shadows(EEVEE_SceneLayerData *sldata, EEVEE_PassList *psl);
void EEVEE_lights_free(void);

/* eevee_lightprobes.c */
void EEVEE_lightprobes_init(EEVEE_SceneLayerData *sldata, EEVEE_Data *vedata);
void EEVEE_lightprobes_cache_init(EEVEE_SceneLayerData *sldata, EEVEE_Data *vedata);
void EEVEE_lightprobes_cache_add(EEVEE_SceneLayerData *sldata, Object *ob);
void EEVEE_lightprobes_cache_finish(EEVEE_SceneLayerData *sldata, EEVEE_Data *vedata);
void EEVEE_lightprobes_refresh(EEVEE_SceneLayerData *sldata, EEVEE_Data *vedata);
void EEVEE_lightprobes_free(void);

/* eevee_effects.c */
void EEVEE_effects_init(EEVEE_SceneLayerData *sldata, EEVEE_Data *vedata);
void EEVEE_effects_cache_init(EEVEE_SceneLayerData *sldata, EEVEE_Data *vedata);
void EEVEE_create_minmax_buffer(EEVEE_Data *vedata, struct GPUTexture *depth_src);
void EEVEE_downsample_buffer(EEVEE_Data *vedata, struct GPUFrameBuffer *fb_src, struct GPUTexture *texture_src, int level);
void EEVEE_effects_do_volumetrics(EEVEE_SceneLayerData *sldata, EEVEE_Data *vedata);
void EEVEE_effects_do_ssr(EEVEE_SceneLayerData *sldata, EEVEE_Data *vedata);
void EEVEE_draw_effects(EEVEE_Data *vedata);
void EEVEE_effects_free(void);

/* Shadow Matrix */
static const float texcomat[4][4] = { /* From NDC to TexCo */
	{0.5f, 0.0f, 0.0f, 0.0f},
	{0.0f, 0.5f, 0.0f, 0.0f},
	{0.0f, 0.0f, 0.5f, 0.0f},
	{0.5f, 0.5f, 0.5f, 1.0f}
};

/* Cubemap Matrices */
static const float cubefacemat[6][4][4] = {
	/* Pos X */
	{{0.0f, 0.0f, -1.0f, 0.0f},
	 {0.0f, -1.0f, 0.0f, 0.0f},
	 {-1.0f, 0.0f, 0.0f, 0.0f},
	 {0.0f, 0.0f, 0.0f, 1.0f}},
	/* Neg X */
	{{0.0f, 0.0f, 1.0f, 0.0f},
	 {0.0f, -1.0f, 0.0f, 0.0f},
	 {1.0f, 0.0f, 0.0f, 0.0f},
	 {0.0f, 0.0f, 0.0f, 1.0f}},
	/* Pos Y */
	{{1.0f, 0.0f, 0.0f, 0.0f},
	 {0.0f, 0.0f, -1.0f, 0.0f},
	 {0.0f, 1.0f, 0.0f, 0.0f},
	 {0.0f, 0.0f, 0.0f, 1.0f}},
	/* Neg Y */
	{{1.0f, 0.0f, 0.0f, 0.0f},
	 {0.0f, 0.0f, 1.0f, 0.0f},
	 {0.0f, -1.0f, 0.0f, 0.0f},
	 {0.0f, 0.0f, 0.0f, 1.0f}},
	/* Pos Z */
	{{1.0f, 0.0f, 0.0f, 0.0f},
	 {0.0f, -1.0f, 0.0f, 0.0f},
	 {0.0f, 0.0f, -1.0f, 0.0f},
	 {0.0f, 0.0f, 0.0f, 1.0f}},
	/* Neg Z */
	{{-1.0f, 0.0f, 0.0f, 0.0f},
	 {0.0f, -1.0f, 0.0f, 0.0f},
	 {0.0f, 0.0f, 1.0f, 0.0f},
	 {0.0f, 0.0f, 0.0f, 1.0f}},
};

#endif /* __EEVEE_PRIVATE_H__ */
