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
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_idprop.h"

#include "WM_api.h"
#include "WM_types.h"
#include "wm_window.h"
#include "wm_event_system.h"
#include "wm_event_types.h"
#include "wm.h"

#include "ED_screen.h"

/* ****************************************************** */

#define MAX_OP_REGISTERED	32

void wm_operator_free(wmOperator *op)
{
	if(op->properties) {
		IDP_FreeProperty(op->properties);
		
		/* This need change, when the idprop code only
		 * need call IDP_FreeProperty. (check BKE_idprop.h) */
		MEM_freeN(op->properties);
		op->properties= NULL;
	}

	if(op->ptr)
		MEM_freeN(op->ptr);

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
		wm_operator_free(opt);
		tot--;
	}
}


/* ****************************************** */

void wm_check(bContext *C)
{
	
	/* wm context */
	if(C->wm==NULL) C->wm= G.main->wm.first;
	if(C->wm==NULL) return;
	if(C->wm->windows.first==NULL) return;
	
	/* case: no open windows at all, for old file reads */
	wm_window_add_ghostwindows(C->wm);
	
	/* case: fileread */
	if(C->wm->initialized==0) {
		
		wm_window_keymap(C->wm);
		ED_spacetypes_keymap(C->wm);
		
		ED_screens_initialize(C->wm);
		C->wm->initialized= 1;
	}
}

/* on startup, it adds all data, for matching */
void wm_add_default(bContext *C)
{
	wmWindowManager *wm= alloc_libblock(&G.main->wm, ID_WM, "WinMan");
	wmWindow *win;
	
	C->wm= wm;
	
	win= wm_window_new(C);
	win->screen= C->screen;
	wm->winactive= win;
	wm_window_make_drawable(C, win); 
}


/* context is allowed to be NULL, do not free wm itself (library.c) */
void wm_close_and_free(bContext *C, wmWindowManager *wm)
{
	wmWindow *win;
	wmOperator *op;
	wmReport *report;
	wmKeyMap *km;
	
	while((win= wm->windows.first)) {
		BLI_remlink(&wm->windows, win);
		wm_window_free(C, win);
	}
	
	while((op= wm->operators.first)) {
		BLI_remlink(&wm->operators, op);
		wm_operator_free(op);
	}

	while((report= wm->reports.first)) {
		BLI_remlink(&wm->reports, report);
		wm_report_free(report);
	}

	while((km= wm->keymaps.first)) {
		BLI_freelistN(&km->keymap);
		BLI_remlink(&wm->keymaps, km);
		MEM_freeN(km);
	}
	
	BLI_freelistN(&wm->queue);
	
	if(C && C->wm==wm) C->wm= NULL;
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
		/* WM_init has assigned to ghost the bContext already */
		wm_window_process_events(1); 
		
		/* per window, all events to the window, screen, area and region handlers */
		wm_event_do_handlers(C);
		
		/* events have left notes about changes, we handle and cache it */
		wm_event_do_notifiers(C);
		
		/* execute cached changes draw */
		wm_draw_update(C);
	}
}


