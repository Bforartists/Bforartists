/*
 * $Id: callbacks.c 37799 2011-06-24 23:14:26Z gsrb3d $
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
 * Contributor(s): Blender Foundation (2011)
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "BLI_utildefines.h"
#include "BLI_listbase.h"
#include "BLI_callbacks.h"

#include "MEM_guardedalloc.h"

static ListBase callback_slots[BLI_CB_EVT_TOT]= {{NULL}};

void BLI_exec_cb(struct Main *main, struct ID *self, eCbEvent evt)
{
	ListBase *lb= &callback_slots[evt];
	bCallbackFuncStore *funcstore;

	for(funcstore= (bCallbackFuncStore *)lb->first; funcstore; funcstore= (bCallbackFuncStore *)funcstore->next) {
		funcstore->func(main, self, funcstore->arg);
	}
}

void BLI_add_cb(bCallbackFuncStore *funcstore, eCbEvent evt)
{
	ListBase *lb= &callback_slots[evt];
	BLI_addtail(lb, funcstore);
}

void BLI_cb_init(void)
{
	/* do nothing */
}

/* call on application exit */
void BLI_cb_finalize(void)
{
	eCbEvent evt;
	for(evt= 0; evt < BLI_CB_EVT_TOT; evt++) {
		ListBase *lb= &callback_slots[evt];
		bCallbackFuncStore *funcstore;
		bCallbackFuncStore *funcstore_next;
		for(funcstore= (bCallbackFuncStore *)lb->first; funcstore; funcstore= funcstore_next) {
			funcstore_next= (bCallbackFuncStore *)funcstore->next;
			BLI_remlink(lb, funcstore);
			if(funcstore->alloc) {
				MEM_freeN(funcstore);
			}
		}
	}
}
