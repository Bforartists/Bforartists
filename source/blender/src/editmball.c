/**
 * $Id$
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

#include <string.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifdef WIN32
#include "BLI_winstuff.h"
#endif
#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "DNA_screen_types.h"
#include "DNA_meta_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_view3d_types.h"

#include "BKE_utildefines.h"
#include "BKE_displist.h"
#include "BKE_global.h"
#include "BKE_object.h"

#include "BIF_gl.h"
#include "BIF_graphics.h"
#include "BIF_screen.h"
#include "BIF_toolbox.h"
#include "BIF_space.h"
#include "BIF_editmode_undo.h"

#include "BDR_editobject.h"
#include "BDR_editmball.h"

#include "BSE_edit.h"
#include "BSE_view.h"

#include "blendef.h"
#include "mydevice.h"

extern short editbutflag;

ListBase editelems= {0, 0};
MetaElem *lastelem;

void make_editMball()
{
	MetaBall *mb;
	MetaElem *ml, *newmb;

	BLI_freelistN(&editelems);
	lastelem= 0;
	
	mb= G.obedit->data;
	ml= mb->elems.first;
	
	while(ml) {
		newmb= MEM_dupallocN(ml);
		BLI_addtail(&editelems, newmb);
		if(ml->flag & SELECT) lastelem= newmb;
		
		ml= ml->next;
	}

	allqueue(REDRAWBUTSEDIT, 0);

	countall();
}

void load_editMball()
{
	/* load mball in object */
	MetaBall *mb;
	MetaElem *ml, *newml;

	if(G.obedit==0) return;
	
	mb= G.obedit->data;
	BLI_freelistN(&(mb->elems));


	ml= editelems.first;
	while(ml) {
		newml= MEM_dupallocN(ml);
		BLI_addtail(&(mb->elems), newml);
		
		ml= ml->next;
	}
}

void add_primitiveMball(int dummy_argument)
{
	MetaElem *ml;
	float *curs, mat[3][3], cent[3], imat[3][3], cmat[3][3];

	if(G.scene->id.lib) return;

	/* this function also comes from an info window */
	if ELEM(curarea->spacetype, SPACE_VIEW3D, SPACE_INFO); else return;
	
	check_editmode(OB_MBALL);

	/* if no obedit: new object and enter editmode */
	if(G.obedit==0) {
		add_object_draw(OB_MBALL);
		base_init_from_view3d(BASACT, G.vd);
		G.obedit= BASACT->object;
		
		where_is_object(G.obedit);

		make_editMball();
		setcursor_space(SPACE_VIEW3D, CURSOR_EDIT);
	}
	
	/* deselect */
	ml= editelems.first;
	while(ml) {
		ml->flag &= ~SELECT;
		ml= ml->next;
	}
	
	/* imat and centre and size */
	Mat3CpyMat4(mat, G.obedit->obmat);

	curs= give_cursor();
	VECCOPY(cent, curs);
	cent[0]-= G.obedit->obmat[3][0];
	cent[1]-= G.obedit->obmat[3][1];
	cent[2]-= G.obedit->obmat[3][2];

	Mat3CpyMat4(imat, G.vd->viewmat);
	Mat3MulVecfl(imat, cent);
	Mat3MulMat3(cmat, imat, mat);
	Mat3Inv(imat,cmat);
	
	Mat3MulVecfl(imat, cent);

	ml= MEM_callocN(sizeof(MetaElem), "metaelem");
	BLI_addtail(&editelems, ml);

	ml->x= cent[0];
	ml->y= cent[1];
	ml->z= cent[2];
	ml->rad= 2.0;
	ml->lay= 1;
	ml->s= 2.0;
	ml->flag= SELECT;

        switch(dummy_argument) {
                case 1:
                        ml->type = MB_BALL;
                        ml->expx= ml->expy= ml->expz= 1.0;
                        break;
                case 2:
                        ml->type = MB_TUBE;
                        ml->expx= ml->expy= ml->expz= 1.0;
                        break;
                case 3:
                        ml->type = MB_PLANE;
                        ml->expx= ml->expy= ml->expz= 1.0;
                        break;
                case 4:
                        ml->type = MB_ELIPSOID;
                        ml->expx= 1.2f;
                        ml->expy= 0.8f;
                        ml->expz= 1.0;
                        break;
                case 5:
                        ml->type = MB_CUBE;
                        ml->expx= ml->expy= ml->expz= 1.0;
                        break;
                default:
                        break;
        }
	
	lastelem= ml;
	
	allqueue(REDRAWALL, 0);
	makeDispList(G.obedit);
	BIF_undo_push("Add MetaElem");
}

void deselectall_mball()
{
	MetaElem *ml;
	int sel= 0;
	
	ml= editelems.first;
	while(ml) {
		if(ml->flag & SELECT) break;
		ml= ml->next;
	}

	if(ml) sel= 1;

	ml= editelems.first;
	while(ml) {
		if(sel) ml->flag &= ~SELECT;
		else ml->flag |= SELECT;
		ml= ml->next;
	}
	allqueue(REDRAWVIEW3D, 0);
//	BIF_undo_push("Deselect MetaElem");
}

void mouse_mball()
{
	static MetaElem *startelem=0;
	MetaElem *ml, *act=0;
	int a, hits;
	unsigned int buffer[MAXPICKBUF];
	
	hits= selectprojektie(buffer, 0, 0, 0, 0);

	/* does startelem exist? */
	ml= editelems.first;
	while(ml) {
		if(ml==startelem) break;
		ml= ml->next;
	}
	if(ml==0) startelem= editelems.first;
	
	if(hits>0) {
		ml= startelem;
		while(ml) {
			/* if(base->lay & G.vd->lay) { */
			
				for(a=0; a<hits; a++) {
					/* index converted for gl stuff */
					if(ml->selcol==buffer[ 4 * a + 3 ]) act= ml;
				}
			/* } */
			
			if(act) break;
			
			ml= ml->next;
			if(ml==0) ml= editelems.first;
			if(ml==startelem) break;
		}
		if(act) {
			if((G.qual & LR_SHIFTKEY)==0) {
				deselectall_mball();
				if(act->flag & SELECT) deselectall_mball();
				act->flag |= SELECT;
			}
			else {
				if(act->flag & SELECT) {
					act->flag &= ~SELECT;
				}
				else act->flag |= SELECT;
			}
			lastelem= act;
			allqueue(REDRAWVIEW3D, 0);
			allqueue(REDRAWBUTSEDIT, 0);
		}
	}
	rightmouse_transform();
}

void adduplicate_mball()
{
	MetaElem *ml, *newml;
	
	ml= editelems.last;
	while(ml) {
		if(ml->flag & SELECT) {
			newml= MEM_dupallocN(ml);
			BLI_addtail(&editelems, newml);
			lastelem= newml;
			ml->flag &= ~SELECT;
		}
		ml= ml->prev;
	}
	
	transform('g');
	allqueue(REDRAWBUTSEDIT, 0);
}

/* Delete all selected MetaElems (not MetaBall) */
void delete_mball()
{
	MetaElem *ml, *next;
	
	if(okee("Erase selected")==0) return;
	
	ml= editelems.first;
	while(ml) {
		next= ml->next;
		if(ml->flag & SELECT) {
			if(lastelem==ml) lastelem= 0;
			BLI_remlink(&editelems, ml);
			MEM_freeN(ml);
		}
		ml= next;
	}
	
	makeDispList(G.obedit);
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);

	BIF_undo_push("Delete MetaElem");
}

/* free all MetaElems from ListBase */
void freeMetaElemlist(ListBase *lb)
{
	MetaElem *ml, *next;

	if(lb==NULL) return;

	ml= lb->first;
	while(ml){
		next= ml->next;
		BLI_remlink(lb, ml);
		MEM_freeN(ml);
		ml= next;
	}

	lb->first= lb->last= NULL;
	
}

/*  ************* undo for MetaBalls ************* */

static void undoMball_to_editMball(void *lbv)
{
	ListBase *lb= lbv;
	MetaElem *ml, *newml;
	unsigned int nr, lastmlnr= 0;

	/* we try to restore lastelem, which used in for example in button window */
	for(ml= editelems.first; ml; ml= ml->next, lastmlnr++)
		if(lastelem==ml) break;

	freeMetaElemlist(&editelems);

	/* copy 'undo' MetaElems to 'edit' MetaElems */
	ml= lb->first;
	while(ml){
		newml= MEM_dupallocN(ml);
		BLI_addtail(&editelems, newml);
		ml= ml->next;
	}
	
	for(nr=0, lastelem= editelems.first; lastelem; lastelem= lastelem->next, nr++)
		if(nr==lastmlnr) break;
	
}

static void *editMball_to_undoMball(void)
{
	ListBase *lb;
	MetaElem *ml, *newml;

	/* allocate memory for undo ListBase */
	lb= MEM_callocN(sizeof(ListBase), "listbase undo");
	lb->first= lb->last= NULL;
	
	/* copy contents of current ListBase to the undo ListBase */
	ml= editelems.first;
	while(ml){
		newml= MEM_dupallocN(ml);
		BLI_addtail(lb, newml);
		ml= ml->next;
	}
	
	return lb;
}

/* free undo ListBase of MetaElems */
static void free_undoMball(void *lbv)
{
	ListBase *lb= lbv;
	
	freeMetaElemlist(lb);
	MEM_freeN(lb);
}

/* this is undo system for MetaBalls */
void undo_push_mball(char *name)
{
	undo_editmode_push(name, free_undoMball, undoMball_to_editMball, editMball_to_undoMball);
}
