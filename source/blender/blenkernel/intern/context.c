/**
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation (2008).
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "MEM_guardedalloc.h"

#include "DNA_listBase.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_windowmanager_types.h"

#include "RNA_access.h"

#include "BLI_listbase.h"

#include "BKE_context.h"
#include "BKE_main.h"
#include "BKE_report.h"
#include "BKE_screen.h"

#include <string.h>

/* struct */

struct bContext {
	bContextTask task;
	ReportList *reports;
	int thread;

	/* windowmanager context */
	struct {
		struct wmWindowManager *manager;
		struct wmWindow *window;
		struct bScreen *screen;
		struct ScrArea *area;
		struct ARegion *region;
		struct uiBlock *block;

		bContextDataCallback screen_cb;
		bContextDataCallback area_cb;
		bContextDataCallback region_cb;
		bContextDataCallback block_cb;
	} wm;
	
	/* data context */
	struct {
		struct Main *main;
		struct Scene *scene;

		int recursion;
	} data;
	
	/* data evaluation */
	struct {
		int render;
	} eval;
};

/* context */

bContext *CTX_create()
{
	bContext *C;
	
	C= MEM_callocN(sizeof(bContext), "bContext");

	C->task= CTX_UNDEFINED;
	C->thread= 0;

	return C;
}

bContext *CTX_copy(const bContext *C, int thread)
{
	bContext *newC;

	if(C->task != CTX_UNDEFINED)
		BKE_report(C->reports, RPT_ERROR_INVALID_CONTEXT, "CTX_copy not allowed for this task");
	
	newC= MEM_dupallocN((void*)C);
	newC->thread= thread;

	return newC;
}

int CTX_thread(const bContext *C)
{
	return C->thread;
}

void CTX_free(bContext *C)
{
	MEM_freeN(C);
}

/* context task and reports */

bContextTask CTX_task(const bContext *C)
{
	return C->task;
}

void CTX_task_set(bContext *C, bContextTask task)
{
	C->task= task;
}

ReportList *CTX_reports(const bContext *C)
{
	return C->reports;
}

void CTX_reports_set(bContext *C, ReportList *reports)
{
	C->reports= reports;
}

/* window manager context */

wmWindowManager *CTX_wm_manager(const bContext *C)
{
	return C->wm.manager;
}

wmWindow *CTX_wm_window(const bContext *C)
{
	return C->wm.window;
}

bScreen *CTX_wm_screen(const bContext *C)
{
	return C->wm.screen;
}

ScrArea *CTX_wm_area(const bContext *C)
{
	return C->wm.area;
}

SpaceLink *CTX_wm_space_data(const bContext *C)
{
	return (C->wm.area)? C->wm.area->spacedata.first: NULL;
}

ARegion *CTX_wm_region(const bContext *C)
{
	return C->wm.region;
}

void *CTX_wm_region_data(const bContext *C)
{
	return (C->wm.region)? C->wm.region->regiondata: NULL;
}

struct uiBlock *CTX_wm_ui_block(const bContext *C)
{
	return C->wm.block;
}

void CTX_wm_manager_set(bContext *C, wmWindowManager *wm)
{
	C->wm.manager= wm;
}

void CTX_wm_window_set(bContext *C, wmWindow *win)
{
	C->wm.window= win;
	C->wm.screen= (win)? win->screen: NULL;
	C->data.scene= (C->wm.screen)? C->wm.screen->scene: NULL;
	C->wm.screen_cb= (C->wm.screen)? C->wm.screen->context: NULL;
}

void CTX_wm_screen_set(bContext *C, bScreen *screen)
{
	C->wm.screen= screen;
	C->data.scene= (C->wm.screen)? C->wm.screen->scene: NULL;
	C->wm.screen_cb= (C->wm.screen)? C->wm.screen->context: NULL;
}

void CTX_wm_area_set(bContext *C, ScrArea *area)
{
	C->wm.area= area;
	C->wm.area_cb= (area && area->type)? area->type->context: NULL;
}

void CTX_wm_region_set(bContext *C, ARegion *region)
{
	C->wm.region= region;
	C->wm.region_cb= (region && region->type)? region->type->context: NULL;
}

void CTX_wm_ui_block_set(bContext *C, struct uiBlock *block, bContextDataCallback cb)
{
	C->wm.block= block;
	C->wm.block_cb= cb;
}

/* data context utility functions */

struct bContextDataMember {
	StructRNA *rna;
	const char *name;
	int collection;
};

struct bContextDataResult {
	void *pointer;
	ListBase list;
};

static int ctx_data_get(bContext *C, const bContextDataMember *member, bContextDataResult *result)
{
	int done= 0, recursion= C->data.recursion;

	memset(result, 0, sizeof(bContextDataResult));

	/* we check recursion to ensure that we do not get infinite
	 * loops requesting data from ourselfs in a context callback */
	if(!done && recursion < 1 && C->wm.block_cb) {
		C->data.recursion= 1;
		done= C->wm.block_cb(C, member, result);
	}
	if(!done && recursion < 2 && C->wm.region_cb) {
		C->data.recursion= 2;
		done= C->wm.region_cb(C, member, result);
	}
	if(!done && recursion < 3 && C->wm.area_cb) {
		C->data.recursion= 3;
		done= C->wm.area_cb(C, member, result);
	}
	if(!done && recursion < 4 && C->wm.screen_cb) {
		C->data.recursion= 4;
		done= C->wm.screen_cb(C, member, result);
	}

	C->data.recursion= recursion;

	return done;
}

static void *ctx_data_pointer_get(const bContext *C, const bContextDataMember *member)
{
	bContextDataResult result;

	if(ctx_data_get((bContext*)C, member, &result))
		return result.pointer;

	return NULL;
}

static int ctx_data_pointer_verify(const bContext *C, const bContextDataMember *member, void **pointer)
{
	bContextDataResult result;

	if(ctx_data_get((bContext*)C, member, &result)) {
		*pointer= result.pointer;
		return 1;
	}
	else {
		*pointer= NULL;
		return 0;
	}
}

static int ctx_data_collection_get(const bContext *C, const bContextDataMember *member, ListBase *list)
{
	bContextDataResult result;

	if(ctx_data_get((bContext*)C, member, &result)) {
		*list= result.list;
		return 1;
	}

	return 0;
}

void CTX_data_pointer_set(bContextDataResult *result, void *data)
{
	result->pointer= data;
}

void CTX_data_list_add(bContextDataResult *result, void *data)
{
	LinkData *link;
	
	link= MEM_callocN(sizeof(LinkData), "LinkData");
	link->data= data;

	BLI_addtail(&result->list, link);
}

/* data context */

Main *CTX_data_main(const bContext *C)
{
	Main *bmain;

	if(ctx_data_pointer_verify(C, CTX_data_main, (void*)&bmain))
		return bmain;
	else
		return C->data.main;
}

void CTX_data_main_set(bContext *C, Main *bmain)
{
	C->data.main= bmain;
}

Scene *CTX_data_scene(const bContext *C)
{
	Scene *scene;

	if(ctx_data_pointer_verify(C, CTX_data_scene, (void*)&scene))
		return scene;
	else
		return C->data.scene;
}

void CTX_data_scene_set(bContext *C, Scene *scene)
{
	C->data.scene= scene;
}

ToolSettings *CTX_data_tool_settings(const bContext *C)
{
	Scene *scene = CTX_data_scene(C);

	if(scene)
		return scene->toolsettings;
	else
		return NULL;
}

int CTX_data_selected_objects(const bContext *C, ListBase *list)
{
	return ctx_data_collection_get(C, CTX_data_selected_objects, list);
}

int CTX_data_selected_bases(const bContext *C, ListBase *list)
{
	return ctx_data_collection_get(C, CTX_data_selected_bases, list);
}

struct Object *CTX_data_active_object(const bContext *C)
{
	return ctx_data_pointer_get(C, CTX_data_active_object);
}

struct Base *CTX_data_active_base(const bContext *C)
{
	return ctx_data_pointer_get(C, CTX_data_active_base);
}

struct Object *CTX_data_edit_object(const bContext *C)
{
	return ctx_data_pointer_get(C, CTX_data_edit_object);
}

struct EditMesh *CTX_data_edit_mesh(const bContext *C)
{
	return ctx_data_pointer_get(C, CTX_data_edit_mesh);
}

ListBase *CTX_data_edit_armature(const bContext *C)
{
	return ctx_data_pointer_get(C, CTX_data_edit_armature);
}

/* data evaluation */

float CTX_eval_frame(const bContext *C)
{
	return (C->data.scene)? C->data.scene->r.cfra: 0.0f;
}

int CTX_eval_render_resolution(const bContext *C)
{
	return C->eval.render;
}

void CTX_eval_render_resolution_set(bContext *C, int render)
{
	C->eval.render= render;
}

