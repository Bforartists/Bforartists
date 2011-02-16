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
 * The Original Code is Copyright (C) 2007 by Janne Karhu.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"

#include "DNA_scene_types.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_modifier.h"
#include "BKE_particle.h"
#include "BKE_pointcache.h"
#include "BKE_report.h"
#include "BKE_scene.h"
 

#include "ED_particle.h"

#include "WM_api.h"
#include "WM_types.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "physics_intern.h"

static int cache_break_test(void *UNUSED(cbd)) {
	return G.afbreek==1;
}
static int ptcache_bake_all_poll(bContext *C)
{
	Scene *scene= CTX_data_scene(C);

	if(!scene)
		return 0;
	
	return 1;
}

static int ptcache_poll(bContext *C)
{
	PointerRNA ptr= CTX_data_pointer_get_type(C, "point_cache", &RNA_PointCache);
	return (ptr.data && ptr.id.data);
}

void bake_console_progress(void *UNUSED(arg), int nr)
{
	printf("\rbake: %3i%%", nr);
	fflush(stdout);
}

void bake_console_progress_end(void *UNUSED(arg))
{
	printf("\rbake: done!\n");
}

static int ptcache_bake_all_exec(bContext *C, wmOperator *op)
{
	Main *bmain = CTX_data_main(C);
	Scene *scene= CTX_data_scene(C);
	wmWindow *win = G.background ? NULL : CTX_wm_window(C);
	PTCacheBaker baker;

	baker.main = bmain;
	baker.scene = scene;
	baker.pid = NULL;
	baker.bake = RNA_boolean_get(op->ptr, "bake");
	baker.render = 0;
	baker.anim_init = 0;
	baker.quick_step = 1;
	baker.break_test = cache_break_test;
	baker.break_data = NULL;

	/* Disabled for now as this doesn't work properly,
	 * and pointcache baking will be reimplemented with
	 * the job system soon anyways. */
	if (win) {
		baker.progressbar = (void (*)(void *, int))WM_timecursor;
		baker.progressend = (void (*)(void *))WM_cursor_restore;
		baker.progresscontext = win;
	} else {
		baker.progressbar = bake_console_progress;
		baker.progressend = bake_console_progress_end;
		baker.progresscontext = NULL;
	}

	BKE_ptcache_bake(&baker);

	WM_event_add_notifier(C, NC_SCENE|ND_FRAME, scene);
	WM_event_add_notifier(C, NC_OBJECT|ND_POINTCACHE, NULL);

	return OPERATOR_FINISHED;
}
static int ptcache_free_bake_all_exec(bContext *C, wmOperator *UNUSED(op))
{
	Scene *scene= CTX_data_scene(C);
	Base *base;
	PTCacheID *pid;
	ListBase pidlist;

	for(base=scene->base.first; base; base= base->next) {
		BKE_ptcache_ids_from_object(&pidlist, base->object, scene, MAX_DUPLI_RECUR);

		for(pid=pidlist.first; pid; pid=pid->next) {
			pid->cache->flag &= ~PTCACHE_BAKED;
		}
		
		BLI_freelistN(&pidlist);
		
		WM_event_add_notifier(C, NC_OBJECT|ND_POINTCACHE, base->object);
	}

	WM_event_add_notifier(C, NC_SCENE|ND_FRAME, scene);

	return OPERATOR_FINISHED;
}

void PTCACHE_OT_bake_all(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Bake All Physics";
	ot->idname= "PTCACHE_OT_bake_all";
	
	/* api callbacks */
	ot->exec= ptcache_bake_all_exec;
	ot->poll= ptcache_bake_all_poll;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	RNA_def_boolean(ot->srna, "bake", 1, "Bake", "");
}
void PTCACHE_OT_free_bake_all(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Free All Physics Bakes";
	ot->idname= "PTCACHE_OT_free_bake_all";
	
	/* api callbacks */
	ot->exec= ptcache_free_bake_all_exec;
	ot->poll= ptcache_bake_all_poll;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}
static int ptcache_bake_exec(bContext *C, wmOperator *op)
{
	Main *bmain = CTX_data_main(C);
	Scene *scene = CTX_data_scene(C);
	wmWindow *win = G.background ? NULL : CTX_wm_window(C);
	PointerRNA ptr= CTX_data_pointer_get_type(C, "point_cache", &RNA_PointCache);
	Object *ob= ptr.id.data;
	PointCache *cache= ptr.data;
	PTCacheBaker baker;
	PTCacheID *pid;
	ListBase pidlist;

	BKE_ptcache_ids_from_object(&pidlist, ob, scene, MAX_DUPLI_RECUR);
	
	for(pid=pidlist.first; pid; pid=pid->next) {
		if(pid->cache == cache)
			break;
	}

	baker.main = bmain;
	baker.scene = scene;
	baker.pid = pid;
	baker.bake = RNA_boolean_get(op->ptr, "bake");
	baker.render = 0;
	baker.anim_init = 0;
	baker.quick_step = 1;
	baker.break_test = cache_break_test;
	baker.break_data = NULL;

	/* Disabled for now as this doesn't work properly,
	 * and pointcache baking will be reimplemented with
	 * the job system soon anyways. */
	if (win) {
		baker.progressbar = (void (*)(void *, int))WM_timecursor;
		baker.progressend = (void (*)(void *))WM_cursor_restore;
		baker.progresscontext = win;
	} else {
		printf("\n"); /* empty first line before console reports */
		baker.progressbar = bake_console_progress;
		baker.progressend = bake_console_progress_end;
		baker.progresscontext = NULL;
	}

	BKE_ptcache_bake(&baker);

	BLI_freelistN(&pidlist);

	WM_event_add_notifier(C, NC_SCENE|ND_FRAME, scene);
	WM_event_add_notifier(C, NC_OBJECT|ND_POINTCACHE, ob);

	return OPERATOR_FINISHED;
}
static int ptcache_free_bake_exec(bContext *C, wmOperator *UNUSED(op))
{
	PointerRNA ptr= CTX_data_pointer_get_type(C, "point_cache", &RNA_PointCache);
	PointCache *cache= ptr.data;
	Object *ob= ptr.id.data;

	if(cache->edit) {
		if(!cache->edit->edited || 1) {// XXX okee("Lose changes done in particle mode?")) {
			PE_free_ptcache_edit(cache->edit);
			cache->edit = NULL;
			cache->flag &= ~PTCACHE_BAKED;
		}
	}
	else
		cache->flag &= ~PTCACHE_BAKED;
	
	WM_event_add_notifier(C, NC_OBJECT|ND_POINTCACHE, ob);

	return OPERATOR_FINISHED;
}
static int ptcache_bake_from_cache_exec(bContext *C, wmOperator *UNUSED(op))
{
	PointerRNA ptr= CTX_data_pointer_get_type(C, "point_cache", &RNA_PointCache);
	PointCache *cache= ptr.data;
	Object *ob= ptr.id.data;
	
	cache->flag |= PTCACHE_BAKED;
	
	WM_event_add_notifier(C, NC_OBJECT|ND_POINTCACHE, ob);

	return OPERATOR_FINISHED;
}
void PTCACHE_OT_bake(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Bake Physics";
	ot->idname= "PTCACHE_OT_bake";
	
	/* api callbacks */
	ot->exec= ptcache_bake_exec;
	ot->poll= ptcache_poll;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	RNA_def_boolean(ot->srna, "bake", 0, "Bake", "");
}
void PTCACHE_OT_free_bake(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Free Physics Bake";
	ot->idname= "PTCACHE_OT_free_bake";
	
	/* api callbacks */
	ot->exec= ptcache_free_bake_exec;
	ot->poll= ptcache_poll;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}
void PTCACHE_OT_bake_from_cache(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Bake From Cache";
	ot->idname= "PTCACHE_OT_bake_from_cache";
	
	/* api callbacks */
	ot->exec= ptcache_bake_from_cache_exec;
	ot->poll= ptcache_poll;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int ptcache_add_new_exec(bContext *C, wmOperator *UNUSED(op))
{
	Scene *scene = CTX_data_scene(C);
	PointerRNA ptr= CTX_data_pointer_get_type(C, "point_cache", &RNA_PointCache);
	Object *ob= ptr.id.data;
	PointCache *cache= ptr.data;
	PTCacheID *pid;
	ListBase pidlist;

	BKE_ptcache_ids_from_object(&pidlist, ob, scene, MAX_DUPLI_RECUR);
	
	for(pid=pidlist.first; pid; pid=pid->next) {
		if(pid->cache == cache) {
			*(pid->cache_ptr) = BKE_ptcache_add(pid->ptcaches);
			break;
		}
	}

	BLI_freelistN(&pidlist);

	WM_event_add_notifier(C, NC_SCENE|ND_FRAME, scene);
	WM_event_add_notifier(C, NC_OBJECT|ND_POINTCACHE, ob);

	return OPERATOR_FINISHED;
}
static int ptcache_remove_exec(bContext *C, wmOperator *UNUSED(op))
{
	PointerRNA ptr= CTX_data_pointer_get_type(C, "point_cache", &RNA_PointCache);
	Scene *scene= CTX_data_scene(C);
	Object *ob= ptr.id.data;
	PointCache *cache= ptr.data;
	PTCacheID *pid;
	ListBase pidlist;

	BKE_ptcache_ids_from_object(&pidlist, ob, scene, MAX_DUPLI_RECUR);
	
	for(pid=pidlist.first; pid; pid=pid->next) {
		if(pid->cache == cache) {
			if(pid->ptcaches->first == pid->ptcaches->last)
				continue; /* don't delete last cache */

			BLI_remlink(pid->ptcaches, pid->cache);
			BKE_ptcache_free(pid->cache);
			*(pid->cache_ptr) = pid->ptcaches->first;

			break;
		}
	}

	BLI_freelistN(&pidlist);
	
	WM_event_add_notifier(C, NC_OBJECT|ND_POINTCACHE, ob);

	return OPERATOR_FINISHED;
}
void PTCACHE_OT_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add new cache";
	ot->idname= "PTCACHE_OT_add";
	
	/* api callbacks */
	ot->exec= ptcache_add_new_exec;
	ot->poll= ptcache_poll; // ptcache_bake_all_poll;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}
void PTCACHE_OT_remove(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Delete current cache";
	ot->idname= "PTCACHE_OT_remove";
	
	/* api callbacks */
	ot->exec= ptcache_remove_exec;
	ot->poll= ptcache_poll;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

