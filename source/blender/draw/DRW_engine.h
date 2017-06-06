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

/** \file DRW_engine.h
 *  \ingroup draw
 */

#ifndef __DRW_ENGINE_H__
#define __DRW_ENGINE_H__

struct ARegion;
struct CollectionEngineSettings;
struct Depsgraph;
struct DRWPass;
struct Material;
struct Scene;
struct DrawEngineType;
struct IDProperty;
struct bContext;
struct Object;
struct SceneLayer;
struct ViewContext;
struct ViewportEngineData;
struct View3D;
struct rcti;
struct GPUOffScreen;

#include "BLI_sys_types.h"  /* for bool */

/* Buffer and textures used by the viewport by default */
typedef struct DefaultFramebufferList {
	struct GPUFrameBuffer *default_fb;
} DefaultFramebufferList;

typedef struct DefaultTextureList {
	struct GPUTexture *color;
	struct GPUTexture *depth;
} DefaultTextureList;

void DRW_engines_register(void);
void DRW_engines_free(void);

void DRW_engine_register(struct DrawEngineType *draw_engine_type);
void DRW_engine_viewport_data_size_get(
        const void *engine_type,
        int *r_fbl_len, int *r_txl_len, int *r_psl_len, int *r_stl_len);

void DRW_draw_view(const struct bContext *C);

void DRW_draw_render_loop_ex(
        struct Depsgraph *graph,
        struct ARegion *ar, struct View3D *v3d,
        const struct bContext *evil_C);
void DRW_draw_render_loop(
        struct Depsgraph *graph,
        struct ARegion *ar, struct View3D *v3d);
void DRW_draw_render_loop_offscreen(
        struct Depsgraph *graph,
        struct ARegion *ar, struct View3D *v3d,
        struct GPUOffScreen *ofs);
void DRW_draw_select_loop(
        struct Depsgraph *graph,
        struct ARegion *ar, struct View3D *v3d,
        bool use_obedit_skip, bool use_nearest, const struct rcti *rect);
void DRW_draw_depth_loop(
        struct Depsgraph *graph,
        struct ARegion *ar, struct View3D *v3d);

/* This is here because GPUViewport needs it */
void DRW_pass_free(struct DRWPass *pass);

/* Mode engines initialization */
void OBJECT_collection_settings_create(struct IDProperty *properties);
void EDIT_MESH_collection_settings_create(struct IDProperty *properties);
void EDIT_ARMATURE_collection_settings_create(struct IDProperty *properties);
void PAINT_WEIGHT_collection_settings_create(struct IDProperty *properties);
void PAINT_VERTEX_collection_settings_create(struct IDProperty *properties);

#endif /* __DRW_ENGINE_H__ */
