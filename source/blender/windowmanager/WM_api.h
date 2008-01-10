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
#ifndef WM_API_H
#define WM_API_H

/* dna-savable wmStructs here */
#include "DNA_windowmanager_types.h"

struct bContext;
struct wmEvent;
struct wmEventHandler;

			/* general API */
void		WM_setprefsize		(int stax, int stay, int sizx, int sizy);

void		WM_init				(struct bContext *C);
void		WM_exit				(struct bContext *C);
void		WM_main				(struct bContext *C);

			/* files */
int			WM_read_homefile	(struct bContext *C, int from_memory);
int			WM_write_homefile	(struct bContext *C, struct wmOperator *op);
void		WM_read_file		(struct bContext *C, char *name);
void		WM_write_file		(struct bContext *C, char *target);
void		WM_read_autosavefile(struct bContext *C);
void		WM_write_autosave	(struct bContext *C);

			/* mouse cursors */
void		WM_init_cursor_data	(void);
void		WM_set_cursor		(struct bContext *C, int curs);
void		WM_waitcursor		(struct bContext *C, int val);
void		WM_timecursor		(struct bContext *C, int nr);

			/* keymap and handlers */
void		WM_keymap_set_item	(ListBase *lb, char *idname, short type, 
								 short val, int modifier, short keymodifier);
void		WM_keymap_verify_item(ListBase *lb, char *idname, short type, 
								 short val, int modifier, short keymodifier);
void		WM_keymap_add_item	(ListBase *lb, char *idname, short type, 
								 short val, int modifier, short keymodifier);
struct wmEventHandler *WM_event_add_keymap_handler(ListBase *keymap, ListBase *handlers);
struct wmEventHandler *WM_event_add_modal_handler(ListBase *handlers, wmOperator *op);
void		WM_event_remove_modal_handler(ListBase *handlers, wmOperator *op);

void		WM_event_add_notifier(wmWindowManager *wm, wmWindow *window, int swinid, int type, 
								  int value);


			/* operator api, default callbacks */
			/* confirm menu + exec */
int			WM_operator_confirm		(struct bContext *C, struct wmOperator *op, struct wmEvent *event);
			/* context checks */
int			WM_operator_winactive	(struct bContext *C);

			/* operator api */
wmOperatorType *WM_operatortype_find(const char *idname);
void		WM_operatortypelist_append(ListBase *lb);

			/* OpenGL wrappers, mimicing opengl syntax */
void		wmLoadMatrix		(wmWindow *win, float mat[][4]);
void		wmGetMatrix			(wmWindow *win, float mat[][4]);
void		wmMultMatrix		(wmWindow *win, float mat[][4]);
void		wmGetSingleMatrix	(wmWindow *win, float mat[][4]);
void		wmScale				(wmWindow *win, float x, float y, float z);
void		wmLoadIdentity		(wmWindow *win);	/* note: old name clear_view_mat */

void		wmFrustum			(wmWindow *win, float x1, float x2, float y1, float y2, float n, float f);
void		wmOrtho				(wmWindow *win, float x1, float x2, float y1, float y2, float n, float f);
void		wmOrtho2			(wmWindow *win, float x1, float x2, float y1, float y2);


#endif /* WM_API_H */

