/*
 * ***** BEGIN GPL LICENSE BLOCK *****
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
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s):
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file GPU_viewport.h
 *  \ingroup gpu
 */

#ifndef __GPU_VIEWPORT_H__
#define __GPU_VIEWPORT_H__

#include <stdbool.h>

#include "DNA_vec_types.h"

#include "GPU_framebuffer.h"
#include "GPU_texture.h"

#define GPU_INFO_SIZE 512 /* IMA_MAX_RENDER_TEXT */

typedef struct GPUViewport GPUViewport;

/* All FramebufferLists are just the same pointers with different names */
typedef struct FramebufferList {
	struct GPUFrameBuffer *framebuffers[0];
} FramebufferList;

typedef struct TextureList {
	struct GPUTexture *textures[0];
} TextureList;

typedef struct PassList {
	struct DRWPass *passes[0];
} PassList;

typedef struct StorageList {
	void *storage[0]; /* custom structs from the engine */
} StorageList;

typedef struct ViewportEngineData {
	void *engine_type;

	FramebufferList *fbl;
	TextureList *txl;
	PassList *psl;
	StorageList *stl;
	char info[GPU_INFO_SIZE];

	/* we may want to put this elsewhere */
	struct DRWTextStore *text_draw_cache;

	/* Profiling data */
	double init_time;
	double cache_time;
	double render_time;
	double background_time;
} ViewportEngineData;

typedef struct ViewportEngineData_Info {
	int fbl_len;
	int txl_len;
	int psl_len;
	int stl_len;
} ViewportEngineData_Info;

GPUViewport *GPU_viewport_create(void);
void GPU_viewport_bind(GPUViewport *viewport, const rcti *rect);
void GPU_viewport_unbind(GPUViewport *viewport);
void GPU_viewport_free(GPUViewport *viewport);

GPUViewport *GPU_viewport_create_from_offscreen(struct GPUOffScreen *ofs);
void GPU_viewport_clear_from_offscreen(GPUViewport *viewport);

void *GPU_viewport_engine_data_create(GPUViewport *viewport, void *engine_type);
void *GPU_viewport_engine_data_get(GPUViewport *viewport, void *engine_type);
void *GPU_viewport_framebuffer_list_get(GPUViewport *viewport);
void *GPU_viewport_texture_list_get(GPUViewport *viewport);
void  GPU_viewport_size_get(const GPUViewport *viewport, int size[2]);
void  GPU_viewport_size_set(GPUViewport *viewport, const int size[2]);

bool GPU_viewport_cache_validate(GPUViewport *viewport, unsigned int hash);

/* debug */
bool GPU_viewport_debug_depth_create(GPUViewport *viewport, int width, int height, char err_out[256]);
void GPU_viewport_debug_depth_free(GPUViewport *viewport);
void GPU_viewport_debug_depth_store(GPUViewport *viewport, const int x, const int y);
void GPU_viewport_debug_depth_draw(GPUViewport *viewport, const float znear, const float zfar);
bool GPU_viewport_debug_depth_is_valid(GPUViewport *viewport);
int GPU_viewport_debug_depth_width(const GPUViewport *viewport);
int GPU_viewport_debug_depth_height(const GPUViewport *viewport);

#endif // __GPU_VIEWPORT_H__
