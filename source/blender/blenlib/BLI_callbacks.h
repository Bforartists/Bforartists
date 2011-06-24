/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): mar 2001 Nzc
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenlib/BLI_callbacks.h
 *  \ingroup bli
 */


#ifndef BLI_CALLBACKS_H
#define BLI_CALLBACKS_H

struct bContext;
struct Main;
struct ID;

typedef enum {
	BLI_CB_EVT_RENDER_PRE,
	BLI_CB_EVT_RENDER_POST,
	BLI_CB_EVT_LOAD_PRE,
	BLI_CB_EVT_LOAD_POST,
	BLI_CB_EVT_SAVE_PRE,
	BLI_CB_EVT_SAVE_POST,
	BLI_CB_EVT_TOT
} eCbEvent;


typedef struct {
	struct bCallbackFuncStore *next, *prev;
	void (* func)(struct Main *, struct ID *, void *arg);
	void *arg;
	short alloc;
} bCallbackFuncStore;


void BLI_exec_cb(struct Main *main, struct ID *self, eCbEvent evt);
void BLI_add_cb(bCallbackFuncStore *funcstore, eCbEvent evt);

#endif


void BLI_cb_init(void);
void BLI_cb_finalize(void);


/* This is blenlib internal only, unrelated to above */
void callLocalErrorCallBack(const char* msg);
