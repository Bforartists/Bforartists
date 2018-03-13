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

/** \file blender/draw/intern/draw_manager_shader.c
 *  \ingroup draw
 */

#include "draw_manager.h"

#include "DNA_world_types.h"
#include "DNA_material_types.h"

#include "BLI_listbase.h"
#include "BLI_string.h"
#include "BLI_string_utils.h"
#include "BLI_threads.h"
#include "BLI_task.h"

#include "BKE_global.h"
#include "BKE_main.h"

#include "GPU_shader.h"
#include "GPU_material.h"

#include "WM_api.h"
#include "WM_types.h"

extern char datatoc_gpu_shader_2D_vert_glsl[];
extern char datatoc_gpu_shader_3D_vert_glsl[];
extern char datatoc_gpu_shader_fullscreen_vert_glsl[];


/* -------------------------------------------------------------------- */

/** \name Deferred Compilation (DRW_deferred)
 *
 * Since compiling shader can take a long time, we do it in a non blocking
 * manner in another thread.
 *
 * \{ */

typedef struct DRWDeferredShader {
	struct DRWDeferredShader *prev, *next;

	GPUMaterial *mat;
	char *vert, *geom, *frag, *defs;
} DRWDeferredShader;

typedef struct DRWShaderCompiler {
	ListBase queue; /* DRWDeferredShader */
	SpinLock list_lock;

	DRWDeferredShader *mat_compiling;
	ThreadMutex compilation_lock;

	void *ogl_context;

	int shaders_done; /* To compute progress. */
} DRWShaderCompiler;

static void drw_deferred_shader_free(DRWDeferredShader *dsh)
{
	/* Make sure it is not queued before freeing. */
	MEM_SAFE_FREE(dsh->vert);
	MEM_SAFE_FREE(dsh->geom);
	MEM_SAFE_FREE(dsh->frag);
	MEM_SAFE_FREE(dsh->defs);

	MEM_freeN(dsh);
}

static void drw_deferred_shader_queue_free(ListBase *queue)
{
	DRWDeferredShader *dsh;
	while((dsh = BLI_pophead(queue))) {
		drw_deferred_shader_free(dsh);
	}
}

static void drw_deferred_shader_compilation_exec(void *custom_data, short *stop, short *do_update, float *progress)
{
	DRWShaderCompiler *comp = (DRWShaderCompiler *)custom_data;

	WM_opengl_context_activate(comp->ogl_context);

	while (true) {
		BLI_spin_lock(&comp->list_lock);

		if (*stop != 0) {
			/* We don't want user to be able to cancel the compilation
			 * but wm can kill the task if we are closing blender. */
			BLI_spin_unlock(&comp->list_lock);
			break;
		}

		/* Pop tail because it will be less likely to lock the main thread
		 * if all GPUMaterials are to be freed (see DRW_deferred_shader_remove()). */
		comp->mat_compiling = BLI_poptail(&comp->queue);
		if (comp->mat_compiling == NULL) {
			/* No more Shader to compile. */
			BLI_spin_unlock(&comp->list_lock);
			break;
		}

		comp->shaders_done++;
		int total = BLI_listbase_count(&comp->queue) + comp->shaders_done;

		BLI_mutex_lock(&comp->compilation_lock);
		BLI_spin_unlock(&comp->list_lock);

		/* Do the compilation. */
		GPU_material_generate_pass(
		        comp->mat_compiling->mat,
		        comp->mat_compiling->vert,
		        comp->mat_compiling->geom,
		        comp->mat_compiling->frag,
		        comp->mat_compiling->defs);

		*progress = (float)comp->shaders_done / (float)total;
		*do_update = true;

		BLI_mutex_unlock(&comp->compilation_lock);

		drw_deferred_shader_free(comp->mat_compiling);
	}

	WM_opengl_context_release(comp->ogl_context);
}

static void drw_deferred_shader_compilation_free(void *custom_data)
{
	DRWShaderCompiler *comp = (DRWShaderCompiler *)custom_data;

	drw_deferred_shader_queue_free(&comp->queue);

	BLI_spin_end(&comp->list_lock);
	BLI_mutex_end(&comp->compilation_lock);

	WM_opengl_context_dispose(comp->ogl_context);

	MEM_freeN(comp);
}

static void drw_deferred_shader_add(
        GPUMaterial *mat, const char *vert, const char *geom, const char *frag_lib, const char *defines)
{
	/* Do not deferre the compilation if we are rendering for image. */
	if (DRW_state_is_image_render()) {
		/* Double checking that this GPUMaterial is not going to be
		 * compiled by another thread. */
		DRW_deferred_shader_remove(mat);
		GPU_material_generate_pass(mat, vert, geom, frag_lib, defines);
		return;
	}

	DRWDeferredShader *dsh = MEM_callocN(sizeof(DRWDeferredShader), "Deferred Shader");

	dsh->mat = mat;
	if (vert)     dsh->vert = BLI_strdup(vert);
	if (geom)     dsh->geom = BLI_strdup(geom);
	if (frag_lib) dsh->frag = BLI_strdup(frag_lib);
	if (defines)  dsh->defs = BLI_strdup(defines);

	BLI_assert(DST.draw_ctx.evil_C);
	wmWindowManager *wm = CTX_wm_manager(DST.draw_ctx.evil_C);
	wmWindow *win = CTX_wm_window(DST.draw_ctx.evil_C);
	Scene *scene = DST.draw_ctx.scene;

	/* Get the running job or a new one if none is running. Can only have one job per type & owner.  */
	wmJob *wm_job = WM_jobs_get(wm, win, scene, "Shaders Compilation",
	                            WM_JOB_PROGRESS | WM_JOB_SUSPEND, WM_JOB_TYPE_SHADER_COMPILATION);

	DRWShaderCompiler *old_comp = (DRWShaderCompiler *)WM_jobs_customdata_get(wm_job);

	DRWShaderCompiler *comp = MEM_callocN(sizeof(DRWShaderCompiler), "DRWShaderCompiler");
	BLI_spin_init(&comp->list_lock);
	BLI_mutex_init(&comp->compilation_lock);

	if (old_comp) {
		BLI_spin_lock(&old_comp->list_lock);
		BLI_movelisttolist(&comp->queue, &old_comp->queue);
		BLI_spin_unlock(&old_comp->list_lock);
	}

	BLI_addtail(&comp->queue, dsh);

	/* Create one context per task. */
	comp->ogl_context = WM_opengl_context_create();
	WM_opengl_context_activate(DST.ogl_context);

	WM_jobs_customdata_set(wm_job, comp, drw_deferred_shader_compilation_free);
	WM_jobs_timer(wm_job, 0.1, NC_MATERIAL | ND_SHADING_DRAW, 0);
	WM_jobs_callbacks(wm_job, drw_deferred_shader_compilation_exec, NULL, NULL, NULL);
	WM_jobs_start(wm, wm_job);
}

void DRW_deferred_shader_remove(GPUMaterial *mat)
{
	Scene *scene = GPU_material_scene(mat);

	for (wmWindowManager *wm = G.main->wm.first; wm; wm = wm->id.next) {
		if (WM_jobs_test(wm, scene, WM_JOB_TYPE_SHADER_COMPILATION) == false) {
			/* No job running, do not create a new one by calling WM_jobs_get. */
			continue;
		}
		for (wmWindow *win = wm->windows.first; win; win = win->next) {
			wmJob *wm_job = WM_jobs_get(wm, win, scene, "Shaders Compilation",
			                            WM_JOB_PROGRESS | WM_JOB_SUSPEND, WM_JOB_TYPE_SHADER_COMPILATION);

			DRWShaderCompiler *comp = (DRWShaderCompiler *)WM_jobs_customdata_get(wm_job);
			if (comp != NULL) {
				BLI_spin_lock(&comp->list_lock);
				DRWDeferredShader *dsh;
				dsh = (DRWDeferredShader *)BLI_findptr(&comp->queue, mat, offsetof(DRWDeferredShader, mat));
				if (dsh) {
					BLI_remlink(&comp->queue, dsh);
				}

				/* Wait for compilation to finish */
				if (comp->mat_compiling != NULL) {
					if (comp->mat_compiling->mat == mat) {
						BLI_mutex_lock(&comp->compilation_lock);
						BLI_mutex_unlock(&comp->compilation_lock);
					}
				}
				BLI_spin_unlock(&comp->list_lock);

				if (dsh) {
					drw_deferred_shader_free(dsh);
				}
			}
		}
	}
}

/** \} */

/* -------------------------------------------------------------------- */

GPUShader *DRW_shader_create(const char *vert, const char *geom, const char *frag, const char *defines)
{
	return GPU_shader_create(vert, frag, geom, NULL, defines);
}

GPUShader *DRW_shader_create_with_lib(
        const char *vert, const char *geom, const char *frag, const char *lib, const char *defines)
{
	GPUShader *sh;
	char *vert_with_lib = NULL;
	char *frag_with_lib = NULL;
	char *geom_with_lib = NULL;

	vert_with_lib = BLI_string_joinN(lib, vert);
	frag_with_lib = BLI_string_joinN(lib, frag);
	if (geom) {
		geom_with_lib = BLI_string_joinN(lib, geom);
	}

	sh = GPU_shader_create(vert_with_lib, frag_with_lib, geom_with_lib, NULL, defines);

	MEM_freeN(vert_with_lib);
	MEM_freeN(frag_with_lib);
	if (geom) {
		MEM_freeN(geom_with_lib);
	}

	return sh;
}

GPUShader *DRW_shader_create_2D(const char *frag, const char *defines)
{
	return GPU_shader_create(datatoc_gpu_shader_2D_vert_glsl, frag, NULL, NULL, defines);
}

GPUShader *DRW_shader_create_3D(const char *frag, const char *defines)
{
	return GPU_shader_create(datatoc_gpu_shader_3D_vert_glsl, frag, NULL, NULL, defines);
}

GPUShader *DRW_shader_create_fullscreen(const char *frag, const char *defines)
{
	return GPU_shader_create(datatoc_gpu_shader_fullscreen_vert_glsl, frag, NULL, NULL, defines);
}

GPUShader *DRW_shader_create_3D_depth_only(void)
{
	return GPU_shader_get_builtin_shader(GPU_SHADER_3D_DEPTH_ONLY);
}

GPUMaterial *DRW_shader_find_from_world(World *wo, const void *engine_type, int options)
{
	GPUMaterial *mat = GPU_material_from_nodetree_find(&wo->gpumaterial, engine_type, options);
	if (DRW_state_is_image_render()) {
		if (mat != NULL && GPU_material_status(mat) == GPU_MAT_QUEUED) {
			/* XXX Hack : we return NULL so that the engine will call DRW_shader_create_from_XXX
			 * with the shader code and we will resume the compilation from there. */
			return NULL;
		}
	}
	return mat;
}

GPUMaterial *DRW_shader_find_from_material(Material *ma, const void *engine_type, int options)
{
	GPUMaterial *mat = GPU_material_from_nodetree_find(&ma->gpumaterial, engine_type, options);
	if (DRW_state_is_image_render()) {
		if (mat != NULL && GPU_material_status(mat) == GPU_MAT_QUEUED) {
			/* XXX Hack : we return NULL so that the engine will call DRW_shader_create_from_XXX
			 * with the shader code and we will resume the compilation from there. */
			return NULL;
		}
	}
	return mat;
}

GPUMaterial *DRW_shader_create_from_world(
        struct Scene *scene, World *wo, const void *engine_type, int options,
        const char *vert, const char *geom, const char *frag_lib, const char *defines)
{
	GPUMaterial *mat = NULL;
	if (DRW_state_is_image_render()) {
		mat = GPU_material_from_nodetree_find(&wo->gpumaterial, engine_type, options);
	}

	if (mat == NULL) {
		mat = GPU_material_from_nodetree(
		        scene, wo->nodetree, &wo->gpumaterial, engine_type, options,
		        vert, geom, frag_lib, defines, true);
	}

	drw_deferred_shader_add(mat, vert, geom, frag_lib, defines);

	return mat;
}

GPUMaterial *DRW_shader_create_from_material(
        struct Scene *scene, Material *ma, const void *engine_type, int options,
        const char *vert, const char *geom, const char *frag_lib, const char *defines)
{
	GPUMaterial *mat = NULL;
	if (DRW_state_is_image_render()) {
		mat = GPU_material_from_nodetree_find(&ma->gpumaterial, engine_type, options);
	}

	if (mat == NULL) {
		mat = GPU_material_from_nodetree(
		        scene, ma->nodetree, &ma->gpumaterial, engine_type, options,
		        vert, geom, frag_lib, defines, true);
	}

	drw_deferred_shader_add(mat, vert, geom, frag_lib, defines);

	return mat;
}

void DRW_shader_free(GPUShader *shader)
{
	GPU_shader_free(shader);
}
