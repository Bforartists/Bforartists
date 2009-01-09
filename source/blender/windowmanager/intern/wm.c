/**
 * $Id:
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
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "DNA_windowmanager_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"

#include "BKE_blender.h"
#include "BKE_context.h"
#include "BKE_idprop.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_report.h"

#include "WM_api.h"
#include "WM_types.h"
#include "wm_window.h"
#include "wm_event_system.h"
#include "wm_event_types.h"
#include "wm.h"

#include "ED_screen.h"

#include "RNA_types.h"

/* ****************************************************** */

#define MAX_OP_REGISTERED	32

void WM_operator_free(wmOperator *op)
{
	if(op->ptr) {
		op->properties= op->ptr->data;
		MEM_freeN(op->ptr);
	}

	if(op->properties) {
		IDP_FreeProperty(op->properties);
		MEM_freeN(op->properties);
	}

	if(op->reports) {
		BKE_reports_clear(op->reports);
		MEM_freeN(op->reports);
	}

	MEM_freeN(op);
}

/* all operations get registered in the windowmanager here */
/* called on event handling by event_system.c */
void wm_operator_register(wmWindowManager *wm, wmOperator *op)
{
	int tot;

	BLI_addtail(&wm->operators, op);
	tot= BLI_countlist(&wm->operators);
	
	while(tot>MAX_OP_REGISTERED) {
		wmOperator *opt= wm->operators.first;
		BLI_remlink(&wm->operators, opt);
		WM_operator_free(opt);
		tot--;
	}
}


/* ****************************************** */

void wm_check(bContext *C)
{
	wmWindowManager *wm= CTX_wm_manager(C);
	
	/* wm context */
	if(CTX_wm_manager(C)==NULL) {
		wm= CTX_data_main(C)->wm.first;
		CTX_wm_manager_set(C, wm);
	}
	if(wm==NULL) return;
	if(wm->windows.first==NULL) return;
	
	/* case: no open windows at all, for old file reads */
	wm_window_add_ghostwindows(wm);
	
	/* case: fileread */
	if(wm->initialized==0) {
		
		wm_window_keymap(wm);
		ED_spacetypes_keymap(wm);
		
		ED_screens_initialize(wm);
		wm->initialized= 1;
	}
}

/* on startup, it adds all data, for matching */
void wm_add_default(bContext *C)
{
	wmWindowManager *wm= alloc_libblock(&CTX_data_main(C)->wm, ID_WM, "WinMan");
	wmWindow *win;
	
	CTX_wm_manager_set(C, wm);
	
	win= wm_window_new(C);
	win->screen= CTX_wm_screen(C); /* XXX from window? */
	wm->winactive= win;
	wm_window_make_drawable(C, win); 
}


/* context is allowed to be NULL, do not free wm itself (library.c) */
void wm_close_and_free(bContext *C, wmWindowManager *wm)
{
	wmWindow *win;
	wmOperator *op;
	wmKeyMap *km;
	wmKeymapItem *kmi;
	
	while((win= wm->windows.first)) {
		BLI_remlink(&wm->windows, win);
		wm_window_free(C, win);
	}
	
	while((op= wm->operators.first)) {
		BLI_remlink(&wm->operators, op);
		WM_operator_free(op);
	}

	while((km= wm->keymaps.first)) {
		for(kmi=km->keymap.first; kmi; kmi=kmi->next) {
			if(kmi->ptr) {
				WM_operator_properties_free(kmi->ptr);
				MEM_freeN(kmi->ptr);
			}
		}

		BLI_freelistN(&km->keymap);
		BLI_remlink(&wm->keymaps, km);
		MEM_freeN(km);
	}
	
	BLI_freelistN(&wm->queue);
	
	BLI_freelistN(&wm->paintcursors);
	
	if(C && CTX_wm_manager(C)==wm) CTX_wm_manager_set(C, NULL);
}

void wm_close_and_free_all(bContext *C, ListBase *wmlist)
{
	wmWindowManager *wm;
	
	while((wm=wmlist->first)) {
		wm_close_and_free(C, wm);
		BLI_remlink(wmlist, wm);
		MEM_freeN(wm);
	}
}

void WM_main(bContext *C)
{
	while(1) {
		
		/* get events from ghost, handle window events, add to window queues */
		wm_window_process_events(C); 
		
		/* per window, all events to the window, screen, area and region handlers */
		wm_event_do_handlers(C);
		
		/* events have left notes about changes, we handle and cache it */
		wm_event_do_notifiers(C);
		
		/* execute cached changes draw */
		wm_draw_update(C);
	}
}


