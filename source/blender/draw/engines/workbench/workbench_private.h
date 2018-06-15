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

/** \file workbench_private.h
 *  \ingroup draw_engine
 */

#ifndef __WORKBENCH_PRIVATE_H__
#define __WORKBENCH_PRIVATE_H__


#include "BKE_studiolight.h"

#include "DNA_image_types.h"
#include "DNA_view3d_types.h"
#include "DNA_world_types.h"

#include "DRW_render.h"


#define WORKBENCH_ENGINE "BLENDER_WORKBENCH"
#define M_GOLDEN_RATION_CONJUGATE 0.618033988749895
#define MAX_SHADERS (1 << 10)

#define OB_SOLID_ENABLED(wpd) (wpd->drawtype & OB_SOLID)
#define OB_TEXTURE_ENABLED(wpd) (wpd->drawtype & OB_TEXTURE)
#define FLAT_ENABLED(wpd) (wpd->shading.light == V3D_LIGHTING_FLAT)
#define STUDIOLIGHT_ENABLED(wpd) (wpd->shading.light == V3D_LIGHTING_STUDIO)
#define MATCAP_ENABLED(wpd) (wpd->shading.light == V3D_LIGHTING_MATCAP && OB_SOLID_ENABLED(wpd))
#define STUDIOLIGHT_ORIENTATION_WORLD_ENABLED(wpd) (STUDIOLIGHT_ENABLED(wpd) && (wpd->studio_light->flag & STUDIOLIGHT_ORIENTATION_WORLD))
#define STUDIOLIGHT_ORIENTATION_CAMERA_ENABLED(wpd) (STUDIOLIGHT_ENABLED(wpd) && (wpd->studio_light->flag & STUDIOLIGHT_ORIENTATION_CAMERA))
#define STUDIOLIGHT_ORIENTATION_VIEWNORMAL_ENABLED(wpd) (MATCAP_ENABLED(wpd) && (wpd->studio_light->flag & STUDIOLIGHT_ORIENTATION_VIEWNORMAL))
#define CAVITY_ENABLED(wpd) (wpd->shading.flag & V3D_SHADING_CAVITY)
#define SHADOW_ENABLED(wpd) (wpd->shading.flag & V3D_SHADING_SHADOW)
#define FXAA_ENABLED(wpd) (wpd->shading.flag & V3D_SHADING_EFFECT_FXAA && (!DRW_state_is_opengl_render()))
#define SPECULAR_HIGHLIGHT_ENABLED(wpd) ((wpd->shading.flag & V3D_SHADING_SPECULAR_HIGHLIGHT) && (!STUDIOLIGHT_ORIENTATION_VIEWNORMAL_ENABLED(wpd)))
#define OBJECT_ID_PASS_ENABLED(wpd) (wpd->shading.flag & V3D_SHADING_OBJECT_OUTLINE)
#define NORMAL_VIEWPORT_COMP_PASS_ENABLED(wpd) (MATCAP_ENABLED(wpd) || STUDIOLIGHT_ENABLED(wpd) || SHADOW_ENABLED(wpd) || SPECULAR_HIGHLIGHT_ENABLED(wpd))
#define NORMAL_VIEWPORT_PASS_ENABLED(wpd) (NORMAL_VIEWPORT_COMP_PASS_ENABLED(wpd) || CAVITY_ENABLED(wpd))
#define NORMAL_ENCODING_ENABLED() (true)

typedef struct WORKBENCH_FramebufferList {
	/* Deferred render buffers */
	struct GPUFrameBuffer *prepass_fb;
	struct GPUFrameBuffer *cavity_fb;
	struct GPUFrameBuffer *composite_fb;
	struct GPUFrameBuffer *effect_fb;

	/* Forward render buffers */
	struct GPUFrameBuffer *object_outline_fb;
	struct GPUFrameBuffer *transparent_accum_fb;
	struct GPUFrameBuffer *transparent_revealage_fb;
} WORKBENCH_FramebufferList;

typedef struct WORKBENCH_StorageList {
	struct WORKBENCH_PrivateData *g_data;
} WORKBENCH_StorageList;

typedef struct WORKBENCH_PassList {
	/* deferred rendering */
	struct DRWPass *prepass_pass;
	struct DRWPass *prepass_hair_pass;
	struct DRWPass *cavity_pass;
	struct DRWPass *shadow_depth_pass_pass;
	struct DRWPass *shadow_depth_pass_mani_pass;
	struct DRWPass *shadow_depth_fail_pass;
	struct DRWPass *shadow_depth_fail_mani_pass;
	struct DRWPass *shadow_depth_fail_caps_pass;
	struct DRWPass *shadow_depth_fail_caps_mani_pass;
	struct DRWPass *composite_pass;
	struct DRWPass *composite_shadow_pass;
	struct DRWPass *effect_fxaa_pass;

	/* forward rendering */
	struct DRWPass *transparent_accum_pass;
	struct DRWPass *object_outline_pass;
	struct DRWPass *depth_pass;
	struct DRWPass *checker_depth_pass;
} WORKBENCH_PassList;

typedef struct WORKBENCH_Data {
	void *engine_type;
	WORKBENCH_FramebufferList *fbl;
	DRWViewportEmptyList *txl;
	WORKBENCH_PassList *psl;
	WORKBENCH_StorageList *stl;
} WORKBENCH_Data;

typedef struct WORKBENCH_UBO_Light {
	float light_direction_vs[4];
	float specular_color[3];
	float energy;
} WORKBENCH_UBO_Light;

typedef struct WORKBENCH_UBO_World {
	float diffuse_light_x_pos[4];
	float diffuse_light_x_neg[4];
	float diffuse_light_y_pos[4];
	float diffuse_light_y_neg[4];
	float diffuse_light_z_pos[4];
	float diffuse_light_z_neg[4];
	float background_color_low[4];
	float background_color_high[4];
	float object_outline_color[4];
	float light_direction_vs[4];
	WORKBENCH_UBO_Light lights[3];
	int num_lights;
	int matcap_orientation;
	float background_alpha;
	int pad[1];
} WORKBENCH_UBO_World;
BLI_STATIC_ASSERT_ALIGN(WORKBENCH_UBO_World, 16)

typedef struct WORKBENCH_UBO_Material {
	float diffuse_color[4];
	float specular_color[4];
	float roughness;
	float pad[3];
} WORKBENCH_UBO_Material;
BLI_STATIC_ASSERT_ALIGN(WORKBENCH_UBO_Material, 16)

typedef struct WORKBENCH_PrivateData {
	struct GHash *material_hash;
	struct GPUShader *prepass_solid_sh;
	struct GPUShader *prepass_solid_hair_sh;
	struct GPUShader *prepass_texture_sh;
	struct GPUShader *prepass_texture_hair_sh;
	struct GPUShader *composite_sh;
	struct GPUShader *transparent_accum_sh;
	struct GPUShader *transparent_accum_hair_sh;
	struct GPUShader *transparent_accum_texture_sh;
	struct GPUShader *transparent_accum_texture_hair_sh;
	View3DShading shading;
	StudioLight *studio_light;
	int drawtype;
	struct GPUUniformBuffer *world_ubo;
	struct DRWShadingGroup *shadow_shgrp;
	struct DRWShadingGroup *depth_shgrp;
	WORKBENCH_UBO_World world_data;
	float shadow_multiplier;
	float cached_shadow_direction[3];
	float shadow_mat[4][4];
	float shadow_inv[4][4];
	float shadow_far_plane[4]; /* Far plane of the view frustum. */
	float shadow_near_corners[4][3]; /* Near plane corners in shadow space. */
	float shadow_near_min[3]; /* min and max of shadow_near_corners. allow fast test */
	float shadow_near_max[3];
	float shadow_near_sides[2][4]; /* This is a parallelogram, so only 2 normal and distance to the edges. */
	bool shadow_changed;

	/* Ssao */
	float winmat[4][4];
	float viewvecs[3][4];
	float ssao_params[4];
	float ssao_settings[4];
} WORKBENCH_PrivateData; /* Transient data */

typedef struct WORKBENCH_MaterialData {
	/* Solid color */
	WORKBENCH_UBO_Material material_data;
	struct GPUUniformBuffer *material_ubo;

	int object_id;
	int drawtype;
	Image *ima;

	/* Linked shgroup for drawing */
	DRWShadingGroup *shgrp;
	/* forward rendering */
	DRWShadingGroup *shgrp_object_outline;
} WORKBENCH_MaterialData;

typedef struct WORKBENCH_ObjectData {
	struct ObjectEngineData *next, *prev;
	struct DrawEngineType *engine_type;
	/* Only nested data, NOT the engine data itself. */
	ObjectEngineDataFreeCb free;
	/* Accumulated recalc flags, which corresponds to ID->recalc flags. */
	int recalc;
	/* Shadow direction in local object space. */
	float shadow_dir[3], shadow_depth;
	float shadow_min[3], shadow_max[3]; /* Min, max in shadow space */
	BoundBox shadow_bbox;
	bool shadow_bbox_dirty;

	int object_id;
} WORKBENCH_ObjectData;

/* workbench_engine.c */
void workbench_solid_materials_init(WORKBENCH_Data *vedata);
void workbench_solid_materials_cache_init(WORKBENCH_Data *vedata);
void workbench_solid_materials_cache_populate(WORKBENCH_Data *vedata, Object *ob);
void workbench_solid_materials_cache_finish(WORKBENCH_Data *vedata);
void workbench_solid_materials_draw_scene(WORKBENCH_Data *vedata);
void workbench_solid_materials_free(void);

/* workbench_deferred.c */
void workbench_deferred_engine_init(WORKBENCH_Data *vedata);
void workbench_deferred_engine_free(void);
void workbench_deferred_draw_background(WORKBENCH_Data *vedata);
void workbench_deferred_draw_scene(WORKBENCH_Data *vedata);
void workbench_deferred_cache_init(WORKBENCH_Data *vedata);
void workbench_deferred_solid_cache_populate(WORKBENCH_Data *vedata, Object *ob);
void workbench_deferred_cache_finish(WORKBENCH_Data *vedata);

/* workbench_forward.c */
void workbench_forward_engine_init(WORKBENCH_Data *vedata);
void workbench_forward_engine_free(void);
void workbench_forward_draw_background(WORKBENCH_Data *vedata);
void workbench_forward_draw_scene(WORKBENCH_Data *vedata);
void workbench_forward_cache_init(WORKBENCH_Data *vedata);
void workbench_forward_cache_populate(WORKBENCH_Data *vedata, Object *ob);
void workbench_forward_cache_finish(WORKBENCH_Data *vedata);

/* workbench_materials.c */
char *workbench_material_build_defines(WORKBENCH_PrivateData *wpd, int drawtype, bool is_hair);
void workbench_material_update_data(WORKBENCH_PrivateData *wpd, Object *ob, Material *mat, WORKBENCH_MaterialData *data);
uint workbench_material_get_hash(WORKBENCH_MaterialData *material_template);
int workbench_material_get_shader_index(WORKBENCH_PrivateData *wpd, int drawtype, bool is_hair);
void workbench_material_set_normal_world_matrix(
        DRWShadingGroup *grp, WORKBENCH_PrivateData *wpd, float persistent_matrix[3][3]);

/* workbench_studiolight.c */
void studiolight_update_world(StudioLight *sl, WORKBENCH_UBO_World *wd);
void studiolight_update_light(WORKBENCH_PrivateData *wpd, const float light_direction[3]);
bool studiolight_object_cast_visible_shadow(WORKBENCH_PrivateData *wpd, Object *ob, WORKBENCH_ObjectData *oed);
float studiolight_object_shadow_distance(WORKBENCH_PrivateData *wpd, Object *ob, WORKBENCH_ObjectData *oed);
bool studiolight_camera_in_object_shadow(WORKBENCH_PrivateData *wpd, Object *ob, WORKBENCH_ObjectData *oed);

/* workbench_data.c */
void workbench_private_data_init(WORKBENCH_PrivateData *wpd);
void workbench_private_data_free(WORKBENCH_PrivateData *wpd);
void workbench_private_data_get_light_direction(WORKBENCH_PrivateData *wpd, float light_direction[3]);

extern DrawEngineType draw_engine_workbench_solid;
extern DrawEngineType draw_engine_workbench_transparent;

#endif
