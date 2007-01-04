/**
 * $Id: 
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */


#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "MEM_guardedalloc.h"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_screen_types.h"
#include "DNA_scene_types.h"
#include "DNA_userdef_types.h"

#include "BKE_depsgraph.h"
#include "BKE_global.h"
#include "BKE_object.h"

#include "BLI_blenlib.h"
#include "BLI_dynstr.h"

#include "BKE_utildefines.h"

#include "BIF_editmesh.h"
#include "BIF_interface.h"
#include "BIF_screen.h"
#include "BIF_resources.h"
#include "BIF_toolbox.h"
#include "BIF_space.h"

#include "BDR_editcurve.h"

#include "BSE_edit.h"

#include "mydevice.h"

/* ***************** generic editmode undo system ********************* */
/*

Add this in your local code:

void undo_editmode_push(char *name, 
		void (*freedata)(void *), 			// pointer to function freeing data
		void (*to_editmode)(void *),        // data to editmode conversion
		void * (*from_editmode)(void))      // editmode to data conversion


Further exported for UI is:

void undo_editmode_step(int step);			// undo and redo
void undo_editmode_clear(void)				// free & clear all data
void undo_editmode_menu(void)				// history menu


*/
/* ********************************************************************* */

/* local prototypes --------------- */
 void undo_editmode_step(int step);	// undo and redo
 void undo_editmode_clear(void);		// free & clear all data
 void undo_editmode_menu(void);		// history menu
 void undo_editmode_push(char *name, void (*freedata)(void *), 
						void (*to_editmode)(void *),  void *(*from_editmode)(void)); 
 struct uiBlock *editmode_undohistorymenu(void *arg_unused);



#define MAXUNDONAME	64
typedef struct UndoElem {
	struct UndoElem *next, *prev;
	ID id;			// copy of editmode object ID
	Object *ob;		// pointer to edited object
	int type;		// type of edited object
	void *undodata;
	char name[MAXUNDONAME];
	void (*freedata)(void *);
	void (*to_editmode)(void *);
	void * (*from_editmode)(void);
} UndoElem;

static ListBase undobase={NULL, NULL};
static UndoElem *curundo= NULL;


/* ********************* xtern api calls ************* */

static void undo_restore(UndoElem *undo)
{
	if(undo) {
		waitcursor(1);
		undo->to_editmode(undo->undodata);	
		waitcursor(0);
	
		countall();
	}
}

/* name can be a dynamic string */
void undo_editmode_push(char *name, void (*freedata)(void *), 
		void (*to_editmode)(void *),  void *(*from_editmode)(void)) 
{
	UndoElem *uel;
	int nr;

	/* at first here was code to prevent an "original" key to be insterted twice
	   this was giving conflicts for example when mesh changed due to keys or apply */
	
	/* remove all undos after (also when curundo==NULL) */
	while(undobase.last != curundo) {
		uel= undobase.last;
		BLI_remlink(&undobase, uel);
		uel->freedata(uel->undodata);
		MEM_freeN(uel);
	}
	
	/* make new */
	curundo= uel= MEM_callocN(sizeof(UndoElem), "undo file");
	strncpy(uel->name, name, MAXUNDONAME-1);
	BLI_addtail(&undobase, uel);
	
	uel->freedata= freedata;
	uel->to_editmode= to_editmode;
	uel->from_editmode= from_editmode;
	
	/* and limit amount to the maximum */
	nr= 0;
	uel= undobase.last;
	while(uel) {
		nr++;
		if(nr==U.undosteps) break;
		uel= uel->prev;
	}
	if(uel) {
		while(undobase.first!=uel) {
			UndoElem *first= undobase.first;
			BLI_remlink(&undobase, first);
			first->freedata(first->undodata);
			MEM_freeN(first);
		}
	}

	/* copy  */
	curundo->undodata= curundo->from_editmode();
	curundo->ob= G.obedit;
	curundo->id= G.obedit->id;
	curundo->type= G.obedit->type;
}


/* helper to remove clean other objects from undo stack */
static void undo_clean_stack(void)
{
	UndoElem *uel, *next;
	int mixed= 0;
	
	/* global undo changes pointers, so we also allow identical names */
	/* side effect: when deleting/renaming object and start editing new one with same name */
	
	uel= undobase.first; 
	while(uel) {
		next= uel->next;
		
		/* for when objects are converted, renamed, or global undo changes pointers... */
		if(uel->type==G.obedit->type && strcmp(uel->id.name, G.obedit->id.name)==0) {
			uel->ob= G.obedit;
		}
		else {
			mixed= 1;
			BLI_remlink(&undobase, uel);
			uel->freedata(uel->undodata);
			MEM_freeN(uel);
		}

		uel= next;
	}
	
	if(mixed) curundo= undobase.last;
}

/* 1= an undo, -1 is a redo. we have to make sure 'curundo' remains at current situation */
void undo_editmode_step(int step)
{
	
	/* prevent undo to happen on wrong object, stack can be a mix */
	undo_clean_stack();
	
	if(step==0) {
		undo_restore(curundo);
	}
	else if(step==1) {
		
		if(curundo==NULL || curundo->prev==NULL) error("No more steps to undo");
		else {
			if(G.f & G_DEBUG) printf("undo %s\n", curundo->name);
			curundo= curundo->prev;
			undo_restore(curundo);
		}
	}
	else {
		/* curundo has to remain current situation! */
		
		if(curundo==NULL || curundo->next==NULL) error("No more steps to redo");
		else {
			undo_restore(curundo->next);
			curundo= curundo->next;
			if(G.f & G_DEBUG) printf("redo %s\n", curundo->name);
		}
	}

	DAG_object_flush_update(G.scene, G.obedit, OB_RECALC_DATA);
	allqueue(REDRAWVIEW3D, 1);
	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWIMAGE, 0);
}

void undo_editmode_clear(void)
{
	UndoElem *uel;
	
	uel= undobase.first;
	while(uel) {
		uel->freedata(uel->undodata);
		uel= uel->next;
	}
	BLI_freelistN(&undobase);
	curundo= NULL;
}

/* based on index nr it does a restore */
static void undo_number(int nr)
{
	UndoElem *uel;
	int a=1;
	
	for(uel= undobase.first; uel; uel= uel->next, a++) {
		if(a==nr) break;
	}
	curundo= uel;
	undo_editmode_step(0);
}

/* ************** for interaction with menu/pullown */

void undo_editmode_menu(void)
{
	UndoElem *uel;
	DynStr *ds= BLI_dynstr_new();
	short event;
	char *menu;

	undo_clean_stack();	// removes other objects from it
	
	BLI_dynstr_append(ds, "Editmode Undo History %t");
	
	for(uel= undobase.first; uel; uel= uel->next) {
		BLI_dynstr_append(ds, "|");
		BLI_dynstr_append(ds, uel->name);
	}
	
	menu= BLI_dynstr_get_cstring(ds);
	BLI_dynstr_free(ds);
	
	event= pupmenu_col(menu, 20);
	MEM_freeN(menu);
	
	if(event>0) undo_number(event);
}

static void do_editmode_undohistorymenu(void *arg, int event)
{
	
	if(G.obedit==NULL || event<1) return;

	if (event==1) {
		if(G.obedit->type==OB_MESH) remake_editMesh();
	}
	else undo_number(event-1);
	
	allqueue(REDRAWVIEW3D, 0);
}

uiBlock *editmode_undohistorymenu(void *arg_unused)
{
	uiBlock *block;
	UndoElem *uel;
	short yco = 20, menuwidth = 120;
	short item=2;
	
	undo_clean_stack();	// removes other objects from it

	block= uiNewBlock(&curarea->uiblocks, "view3d_edit_mesh_undohistorymenu", UI_EMBOSSP, UI_HELV, G.curscreen->mainwin);
	uiBlockSetButmFunc(block, do_editmode_undohistorymenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Undo All Changes", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	
	for(uel= undobase.first; uel; uel= uel->next, item++) {
		if (uel==curundo) uiDefBut(block, SEPR, 0, "",		0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, uel->name, 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, (float)item, "");
		if (uel==curundo) uiDefBut(block, SEPR, 0, "",		0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	}
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

void *undo_editmode_get_prev(Object *ob)
{
	UndoElem *ue= undobase.last;
	if(ue && ue->prev && ue->prev==ob) return ue->prev->undodata;
	return NULL;
}
