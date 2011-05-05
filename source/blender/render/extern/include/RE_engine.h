/*
 * $Id$
 *
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
 * The Original Code is Copyright (C) 2006 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file RE_engine.h
 *  \ingroup render
 */

#ifndef RE_ENGINE_H
#define RE_ENGINE_H

#include "DNA_listBase.h"
#include "DNA_vec_types.h"
#include "RNA_types.h"

struct Render;
struct RenderEngine;
struct RenderEngineType;
struct RenderLayer;
struct RenderResult;
struct ReportList;
struct Scene;

/* External Engine */

#define RE_INTERNAL			1
#define RE_GAME				2
#define RE_DO_PREVIEW		4
#define RE_DO_ALL			8

extern ListBase R_engines;

typedef struct RenderEngineType {
	struct RenderEngineType *next, *prev;

	/* type info */
	char idname[64]; // best keep the same size as BKE_ST_MAXNAME
	char name[64];
	int flag;

	void (*render)(struct RenderEngine *engine, struct Scene *scene);
	void (*draw)(struct RenderEngine *engine, struct Scene *scene);
	void (*update)(struct RenderEngine *engine, struct Scene *scene);

	/* RNA integration */
	ExtensionRNA ext;
} RenderEngineType;

typedef struct RenderEngine {
	RenderEngineType *type;
	struct Render *re;
	ListBase fullresult;
	void *py_instance;
	int do_draw;
	int do_update;
} RenderEngine;

RenderEngine *RE_engine_create(RenderEngineType *type);
void RE_engine_free(RenderEngine *engine);

void RE_layer_load_from_file(struct RenderLayer *layer, struct ReportList *reports, const char *filename, int x, int y);
void RE_result_load_from_file(struct RenderResult *result, struct ReportList *reports, const char *filename);

LIBEXPORT struct RenderResult *RE_engine_begin_result(RenderEngine *engine, int x, int y, int w, int h);
LIBEXPORT void RE_engine_update_result(RenderEngine *engine, struct RenderResult *result);
LIBEXPORT void RE_engine_end_result(RenderEngine *engine, struct RenderResult *result);

LIBEXPORT int RE_engine_test_break(RenderEngine *engine);
LIBEXPORT void RE_engine_update_stats(RenderEngine *engine, const char *stats, const char *info);

int RE_engine_render(struct Render *re, int do_all);

void RE_engines_init(void);
void RE_engines_exit(void);

#endif /* RE_ENGINE_H */

