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
 * The Original Code is Copyright (C) 2004 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

/*

editmesh_lib: generic (no UI, no menus) operations/evaluators for editmesh data

*/

#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifdef WIN32
#include "BLI_winstuff.h"
#endif
#include "MEM_guardedalloc.h"


#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_editVert.h"

#include "BKE_global.h"
#include "BKE_mesh.h"
#include "BKE_utildefines.h"

#include "BIF_editmesh.h"

#include "editmesh.h"


/* ********* Selection ************ */

void EM_select_face(EditFace *efa, int sel)
{
	if(sel) {
		efa->f |= SELECT;
		efa->e1->f |= SELECT;
		efa->e2->f |= SELECT;
		efa->e3->f |= SELECT;
		if(efa->e4) efa->e4->f |= SELECT;
		efa->v1->f |= SELECT;
		efa->v2->f |= SELECT;
		efa->v3->f |= SELECT;
		if(efa->v4) efa->v4->f |= SELECT;
	}
	else {
		efa->f &= ~SELECT;
		efa->e1->f &= ~SELECT;
		efa->e2->f &= ~SELECT;
		efa->e3->f &= ~SELECT;
		if(efa->e4) efa->e4->f &= ~SELECT;
		efa->v1->f &= ~SELECT;
		efa->v2->f &= ~SELECT;
		efa->v3->f &= ~SELECT;
		if(efa->v4) efa->v4->f &= ~SELECT;
	}
}

void EM_select_edge(EditEdge *eed, int sel)
{
	if(sel) {
		eed->f |= SELECT;
		eed->v1->f |= SELECT;
		eed->v2->f |= SELECT;
	}
	else {
		eed->f &= ~SELECT;
		eed->v1->f &= ~SELECT;
		eed->v2->f &= ~SELECT;
	}
}

int faceselectedOR(EditFace *efa, int flag)
{
	
	if(efa->v1->f & flag) return 1;
	if(efa->v2->f & flag) return 1;
	if(efa->v3->f & flag) return 1;
	if(efa->v4 && (efa->v4->f & 1)) return 1;
	return 0;
}

// replace with (efa->f & SELECT)
int faceselectedAND(EditFace *efa, int flag)
{
	if(efa->v1->f & flag) {
		if(efa->v2->f & flag) {
			if(efa->v3->f & flag) {
				if(efa->v4) {
					if(efa->v4->f & flag) return 1;
				}
				else return 1;
			}
		}
	}
	return 0;
}


int EM_nfaces_selected(void)
{
	EditMesh *em = G.editMesh;
	EditFace *efa;
	int count= 0;

	for (efa= em->faces.first; efa; efa= efa->next)
		if (efa->f & SELECT)
			count++;

	return count;
}

int EM_nvertices_selected(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	int count= 0;

	for (eve= em->verts.first; eve; eve= eve->next)
		if (eve->f & SELECT)
			count++;

	return count;
}

void EM_clear_flag_all(int flag)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;
	EditFace *efa;
	
	for (eve= em->verts.first; eve; eve= eve->next) eve->f &= ~flag;
	for (eed= em->edges.first; eed; eed= eed->next) eed->f &= ~flag;
	for (efa= em->faces.first; efa; efa= efa->next) efa->f &= ~flag;
	
}

void EM_set_flag_all(int flag)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;
	EditFace *efa;
	
	for (eve= em->verts.first; eve; eve= eve->next) eve->f |= flag;
	for (eed= em->edges.first; eed; eed= eed->next) eed->f |= flag;
	for (efa= em->faces.first; efa; efa= efa->next) efa->f |= flag;
	
}

/* flush to edges & faces */

/*  this based on coherent selected vertices, for example when adding new
    objects. call clear_flag_all() before you select vertices to be sure it ends OK!
	
*/

void EM_select_flush(void)
{
	EditMesh *em = G.editMesh;
	EditEdge *eed;
	EditFace *efa;
	
	for(eed= em->edges.first; eed; eed= eed->next) {
		if(eed->v1->f & eed->v2->f & SELECT) eed->f |= SELECT;
	}
	for(efa= em->faces.first; efa; efa= efa->next) {
		if(efa->v4) {
			if(efa->v1->f & efa->v2->f & efa->v3->f & efa->v4->f & SELECT ) efa->f |= SELECT;
		}
		else {
			if(efa->v1->f & efa->v2->f & efa->v3->f & SELECT ) efa->f |= SELECT;
		}
	}
}

/* flush to edges & faces */

/* based on select mode it selects edges/faces 
   assumed is that verts/edges/faces were properly selected themselves
   with the calls above
*/

void EM_selectmode_flush(void)
{
	EditMesh *em = G.editMesh;
	EditEdge *eed;
	EditFace *efa;
	
	// flush to edges & faces
	if(G.scene->selectmode & SCE_SELECT_VERTEX) {
		for(eed= em->edges.first; eed; eed= eed->next) {
			if(eed->v1->f & eed->v2->f & SELECT) eed->f |= SELECT;
			else eed->f &= ~SELECT;
		}
		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->v4) {
				if(efa->v1->f & efa->v2->f & efa->v3->f & efa->v4->f & SELECT) efa->f |= SELECT;
				else efa->f &= ~SELECT;
			}
			else {
				if(efa->v1->f & efa->v2->f & efa->v3->f & SELECT) efa->f |= SELECT;
				else efa->f &= ~SELECT;
			}
		}
	}
	// flush to faces
	else if(G.scene->selectmode & SCE_SELECT_EDGE) {
		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->e4) {
				if(efa->e1->f & efa->e2->f & efa->e3->f & efa->e4->f & SELECT) efa->f |= SELECT;
				else efa->f &= ~SELECT;
			}
			else {
				if(efa->e1->f & efa->e2->f & efa->e3->f & SELECT) efa->f |= SELECT;
				else efa->f &= ~SELECT;
			}
		}
	}

	// make sure selected faces have selected edges too, for extrude (hack?)
	else if(G.scene->selectmode & SCE_SELECT_FACE) {
		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->f & SELECT) {
				efa->e1->f |= SELECT;
				efa->e2->f |= SELECT;
				efa->e3->f |= SELECT;
				if(efa->e4) efa->e4->f |= SELECT;
			}
		}
	}
}

/* when switching select mode, makes sure selection is consistant for editing */
/* also for paranoia checks to make sure edge or face mode works */
void EM_selectmode_set(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;
	EditFace *efa;

	if(G.scene->selectmode & SCE_SELECT_VERTEX) {
		/* vertices -> edges -> faces */
		EM_select_flush();
	}
	else if(G.scene->selectmode & SCE_SELECT_EDGE) {
		/* deselect vertices, and select again based on edge select */
		for(eve= em->verts.first; eve; eve= eve->next) eve->f &= ~SELECT;
		for(eed= em->edges.first; eed; eed= eed->next) 
			if(eed->f & SELECT) EM_select_edge(eed, 1);
		/* selects faces based on edge status */
		EM_selectmode_flush();
	}
	else if(G.scene->selectmode == SCE_SELECT_FACE) {
		/* deselect eges, and select again based on face select */
		for(eed= em->edges.first; eed; eed= eed->next) EM_select_edge(eed, 0);
		for(efa= em->faces.first; efa; efa= efa->next) 
			if(efa->f & SELECT) EM_select_face(efa, 1);
	}
}


/* ********  EXTRUDE ********* */

static void set_edge_directions(void)
{
	EditMesh *em= G.editMesh;
	EditFace *efa= em->faces.first;
	
	while(efa) {
		// non selected face
		if(efa->f== 0) {
			if(efa->e1->f) {
				if(efa->e1->v1 == efa->v1) efa->e1->dir= 0;
				else efa->e1->dir= 1;
			}
			if(efa->e2->f) {
				if(efa->e2->v1 == efa->v2) efa->e2->dir= 0;
				else efa->e2->dir= 1;
			}
			if(efa->e3->f) {
				if(efa->e3->v1 == efa->v3) efa->e3->dir= 0;
				else efa->e3->dir= 1;
			}
			if(efa->e4 && efa->e4->f) {
				if(efa->e4->v1 == efa->v4) efa->e4->dir= 0;
				else efa->e4->dir= 1;
			}
		}
		efa= efa->next;
	}	
}

static short extrudeflag_edge(short flag)
{
	/* all select edges/faces: extrude */
	/* old select is cleared, in new ones it is set */
	EditMesh *em = G.editMesh;
	EditVert *eve, *nextve;
	EditEdge *eed, *nexted;
	EditFace *efa, *nextfa;
	float nor[3]={0.0, 0.0, 0.0};
	short del_old= 0;
	
	if(G.obedit==0 || get_mesh(G.obedit)==0) return 0;
	
	/* selected edges with 0 or 1 selected face become faces */
	/* selected faces generate new faces */

	/* if *one* selected face has edge with unselected face; remove old selected faces */
	
	/* if selected edge is not used anymore; remove */
	/* if selected vertex is not used anymore: remove */
	
	/* select the new extrusion, deselect old */
	
	
	/* step 1; init, count faces in edges */
	recalc_editnormals();
	
	for(eve= em->verts.first; eve; eve= eve->next) {
		eve->vn= NULL;
		eve->f1= 0;
	}

	for(eed= em->edges.first; eed; eed= eed->next) {
		eed->f1= 0; // amount of selected faces
		eed->f2= 0; // amount of unselected faces
		if(eed->f & SELECT) {
			eed->v1->f1= 1; // we call this 'selected vertex' now
			eed->v2->f1= 1;
		}
	}
	for(efa= em->faces.first; efa; efa= efa->next) {
		if(efa->f & SELECT) {
			efa->e1->f1++;
			efa->e2->f1++;
			efa->e3->f1++;
			if(efa->e4) efa->e4->f1++;
		}
		else {
			efa->e1->f2++;
			efa->e2->f2++;
			efa->e3->f2++;
			if(efa->e4) efa->e4->f2++;
		}
	}
	
	set_edge_directions();
	
	/* step 2: make new faces from edges */
	for(eed= em->edges.last; eed; eed= eed->prev) {
		if(eed->f & SELECT) {
			if(eed->f1<2) {
				if(eed->v1->vn==NULL)
					eed->v1->vn= addvertlist(eed->v1->co);
				if(eed->v2->vn==NULL)
					eed->v2->vn= addvertlist(eed->v2->co);
					
				if(eed->dir==1) addfacelist(eed->v1, eed->v2, eed->v2->vn, eed->v1->vn, NULL);
				else addfacelist(eed->v2, eed->v1, eed->v1->vn, eed->v2->vn, NULL);
			}
		}
	}
	
	/* step 3: make new faces from faces */
	for(efa= em->faces.last; efa; efa= efa->prev) {
		if(efa->f & SELECT) {
			if(efa->v1->vn==NULL) efa->v1->vn= addvertlist(efa->v1->co);
			if(efa->v2->vn==NULL) efa->v2->vn= addvertlist(efa->v2->co);
			if(efa->v3->vn==NULL) efa->v3->vn= addvertlist(efa->v3->co);
			if(efa->v4 && efa->v4->vn==NULL) efa->v4->vn= addvertlist(efa->v4->co);
			
			if(efa->v4)
				addfacelist(efa->v1->vn, efa->v2->vn, efa->v3->vn, efa->v4->vn, efa);
			else
				addfacelist(efa->v1->vn, efa->v2->vn, efa->v3->vn, NULL, efa);
	
			/* if *one* selected face has edge with unselected face; remove old selected faces */
			if(efa->e1->f2 || efa->e2->f2 || efa->e3->f2 || (efa->e4 && efa->e4->f2))
				del_old= 1;
				
			/* for transform */
			VecAddf(nor, nor, efa->n);
		}
	}
	
	if(del_old) {
		/* step 4: remove old faces, if del_old */
		efa= em->faces.first;
		while(efa) {
			nextfa= efa->next;
			if(efa->f & SELECT) {
				BLI_remlink(&em->faces, efa);
				free_editface(efa);
			}
			efa= nextfa;
		}
	
		/* step 5: remove selected unused edges */
		/* start tagging again */
		for(eed= em->edges.first; eed; eed= eed->next) eed->f1=0;
		for(efa= em->faces.first; efa; efa= efa->next) {
			efa->e1->f1= 1;
			efa->e2->f1= 1;
			efa->e3->f1= 1;
			if(efa->e4) efa->e4->f1= 1;
		}
		/* remove */
		eed= em->edges.first; 
		while(eed) {
			nexted= eed->next;
			if(eed->f & SELECT) {
				if(eed->f1==0) {
					remedge(eed);
					free_editedge(eed);
				}
			}
			eed= nexted;
		}
	
		/* step 6: remove selected unused vertices */
		for(eed= em->edges.first; eed; eed= eed->next) 
			eed->v1->f1= eed->v2->f1= 0;
		
		eve= em->verts.first;
		while(eve) {
			nextve= eve->next;
			if(eve->f1) {
				// hack... but we need it for step 7, redoing selection
				if(eve->vn) eve->vn->vn= eve->vn;
				
				BLI_remlink(&em->verts, eve);
				free_editvert(eve);
			}
			eve= nextve;
		}
	}
	
	/* step 7: redo selection */
	EM_clear_flag_all(SELECT);

	Normalise(nor);	// translation normal grab
	
	for(eve= em->verts.first; eve; eve= eve->next) {
		if(eve->vn) {
			eve->vn->f |= SELECT;
			VECCOPY(eve->vn->no, nor);
		}
	}

	EM_select_flush();
	
	return 1;
}

short extrudeflag_vert(short flag)
{
	/* all verts/edges/faces with (f & 'flag'): extrude */
	/* from old verts, 'flag' is cleared, in new ones it is set */
	EditMesh *em = G.editMesh;
	EditVert *eve, *v1, *v2, *v3, *v4, *nextve;
	EditEdge *eed, *e1, *e2, *e3, *e4, *nexted;
	EditFace *efa, *efa2, *nextvl;
	float nor[3]={0.0, 0.0, 0.0};
	short sel=0, del_old= 0, smooth= 0;

	if(G.obedit==0 || get_mesh(G.obedit)==0) return 0;

	/* clear vert flag f1, we use this to detect a loose selected vertice */
	eve= em->verts.first;
	while(eve) {
		if(eve->f & flag) eve->f1= 1;
		else eve->f1= 0;
		eve= eve->next;
	}
	/* clear edges counter flag, if selected we set it at 1 */
	eed= em->edges.first;
	while(eed) {
		if( (eed->v1->f & flag) && (eed->v2->f & flag) ) {
			eed->f2= 1;
			eed->v1->f1= 0;
			eed->v2->f1= 0;
		}
		else eed->f2= 0;
		
		eed->f1= 1;		/* this indicates it is an 'old' edge (in this routine we make new ones) */
		
		eed= eed->next;
	}

	/* we set a flag in all selected faces, and increase the associated edge counters */

	efa= em->faces.first;
	while(efa) {
		efa->f1= 0;

		if (efa->flag & ME_SMOOTH) {
			if (faceselectedOR(efa, 1)) smooth= 1;
		}
		
		if(faceselectedAND(efa, flag)) {
			e1= efa->e1;
			e2= efa->e2;
			e3= efa->e3;
			e4= efa->e4;

			if(e1->f2 < 3) e1->f2++;
			if(e2->f2 < 3) e2->f2++;
			if(e3->f2 < 3) e3->f2++;
			if(e4 && e4->f2 < 3) e4->f2++;
			
			efa->f1= 1;
		}
		else if(faceselectedOR(efa, flag)) {
			e1= efa->e1;
			e2= efa->e2;
			e3= efa->e3;
			e4= efa->e4;
			
			if( (e1->v1->f & flag) && (e1->v2->f & flag) ) e1->f1= 2;
			if( (e2->v1->f & flag) && (e2->v2->f & flag) ) e2->f1= 2;
			if( (e3->v1->f & flag) && (e3->v2->f & flag) ) e3->f1= 2;
			if( e4 && (e4->v1->f & flag) && (e4->v2->f & flag) ) e4->f1= 2;
		}
		
		efa= efa->next;
	}

	set_edge_directions();

	/* the current state now is:
		eve->f1==1: loose selected vertex 

		eed->f2==0 : edge is not selected, no extrude
		eed->f2==1 : edge selected, is not part of a face, extrude
		eed->f2==2 : edge selected, is part of 1 face, extrude
		eed->f2==3 : edge selected, is part of more faces, no extrude
		
		eed->f1==0: new edge
		eed->f1==1: edge selected, is part of selected face, when eed->f==3: remove
		eed->f1==2: edge selected, part of a partially selected face
					
		efa->f1==1 : duplicate this face
	*/

	/* copy all selected vertices, */
	/* write pointer to new vert in old struct at eve->vn */
	eve= em->verts.last;
	while(eve) {
		eve->f &= ~128;  /* clear, for later test for loose verts */
		if(eve->f & flag) {
			sel= 1;
			v1= addvertlist(0);
			
			VECCOPY(v1->co, eve->co);
			v1->f= eve->f;
			eve->f-= flag;
			eve->vn= v1;
		}
		else eve->vn= 0;
		eve= eve->prev;
	}

	if(sel==0) return 0;

	/* all edges with eed->f2==1 or eed->f2==2 become faces */
	
	/* if del_old==1 then extrude is in partial geometry, to keep it manifold.
					 verts with f1==0 and (eve->f & 128)==0) are removed
	                 edges with eed->f2>2 are removed
					 faces with efa->f1 are removed
	   if del_old==0 the extrude creates a volume.
	*/
	
	eed= em->edges.last;
	while(eed) {
		nexted= eed->prev;
		if( eed->f2<3) {
			eed->v1->f |= 128;  /* = no loose vert! */
			eed->v2->f |= 128;
		}
		if( (eed->f2==1 || eed->f2==2) ) {
			if(eed->f1==2) del_old= 1;
			
			if(eed->dir==1) efa2= addfacelist(eed->v1, eed->v2, eed->v2->vn, eed->v1->vn, NULL);
			else efa2= addfacelist(eed->v2, eed->v1, eed->v1->vn, eed->v2->vn, NULL);
			if (smooth) efa2->flag |= ME_SMOOTH;

			/* Needs smarter adaption of existing creases.
			 * If addedgelist is used, make sure seams are set to 0 on these
			 * new edges, since we do not want to add any seams on extrusion.
			 */
			efa2->e1->crease= eed->crease;
			efa2->e2->crease= eed->crease;
			efa2->e3->crease= eed->crease;
			if(efa2->e4) efa2->e4->crease= eed->crease;
		}

		eed= nexted;
	}
	if(del_old) {
		eed= em->edges.first;
		while(eed) {
			nexted= eed->next;
			if(eed->f2==3 && eed->f1==1) {
				remedge(eed);
				free_editedge(eed);
			}
			eed= nexted;
		}
	}
	/* duplicate faces, if necessary remove old ones  */
	efa= em->faces.first;
	while(efa) {
		nextvl= efa->next;
		if(efa->f1 & 1) {
		
			v1= efa->v1->vn;
			v2= efa->v2->vn;
			v3= efa->v3->vn;
			if(efa->v4) v4= efa->v4->vn; else v4= 0;
			
			efa2= addfacelist(v1, v2, v3, v4, efa);
			
			/* for transform */
			VecAddf(nor, nor, efa->n);

			if(del_old) {
				BLI_remlink(&em->faces, efa);
				free_editface(efa);
			}
			if (smooth) efa2->flag |= ME_SMOOTH;			
		}
		efa= nextvl;
	}
	
	Normalise(nor);	// for grab
	
	/* for all vertices with eve->vn!=0 
		if eve->f1==1: make edge
		if flag!=128 : if del_old==1: remove
	*/
	eve= em->verts.last;
	while(eve) {
		nextve= eve->prev;
		if(eve->vn) {
			if(eve->f1==1) addedgelist(eve, eve->vn, NULL);
			else if( (eve->f & 128)==0) {
				if(del_old) {
					BLI_remlink(&em->verts,eve);
					free_editvert(eve);
					eve= NULL;
				}
			}
		}
		if(eve) {
			if(eve->f & flag) {
				VECCOPY(eve->no, nor);
			}
			eve->f &= ~128;
		}
		eve= nextve;
	}
	// since its vertex select mode now, it also deselects higher order
	EM_selectmode_flush();

	return 1;
}

/* generic extrude */
short extrudeflag(short flag)
{
	if(G.scene->selectmode & SCE_SELECT_VERTEX)
		return extrudeflag_vert(flag);
	else 
		return extrudeflag_edge(flag);
		
}

void rotateflag(short flag, float *cent, float rotmat[][3])
{
	/* all verts with (flag & 'flag') rotate */
	EditMesh *em = G.editMesh;
	EditVert *eve;

	eve= em->verts.first;
	while(eve) {
		if(eve->f & flag) {
			eve->co[0]-=cent[0];
			eve->co[1]-=cent[1];
			eve->co[2]-=cent[2];
			Mat3MulVecfl(rotmat,eve->co);
			eve->co[0]+=cent[0];
			eve->co[1]+=cent[1];
			eve->co[2]+=cent[2];
		}
		eve= eve->next;
	}
}

void translateflag(short flag, float *vec)
{
	/* all verts with (flag & 'flag') translate */
	EditMesh *em = G.editMesh;
	EditVert *eve;

	eve= em->verts.first;
	while(eve) {
		if(eve->f & flag) {
			eve->co[0]+=vec[0];
			eve->co[1]+=vec[1];
			eve->co[2]+=vec[2];
		}
		eve= eve->next;
	}
}

void adduplicateflag(int flag)
{
	EditMesh *em = G.editMesh;
	/* old selection has flag 128 set, and flag 'flag' cleared
	   new selection has flag 'flag' set */
	EditVert *eve, *v1, *v2, *v3, *v4;
	EditEdge *eed, *newed;
	EditFace *efa, *newfa;

	EM_clear_flag_all(128);
	EM_selectmode_set();	// paranoia check, selection now is consistant

	/* vertices first */
	for(eve= em->verts.last; eve; eve= eve->prev) {

		if(eve->f & flag) {
			v1= addvertlist(eve->co);
			
			v1->f= eve->f;
			eve->f-= flag;
			eve->f|= 128;
			
			eve->vn= v1;

			/* >>>>> FIXME: Copy deformation weight ? */
			v1->totweight = eve->totweight;
			if (eve->totweight){
				v1->dw = MEM_mallocN (eve->totweight * sizeof(MDeformWeight), "deformWeight");
				memcpy (v1->dw, eve->dw, eve->totweight * sizeof(MDeformWeight));
			}
			else
				v1->dw=NULL;
		}
	}
	
	/* copy edges */
	for(eed= em->edges.last; eed; eed= eed->prev) {
		if( eed->f & flag ) {
			v1= eed->v1->vn;
			v2= eed->v2->vn;
			newed= addedgelist(v1, v2, eed);
			
			newed->f= eed->f;
			eed->f -= flag;
			eed->f |= 128;
		}
	}

	/* then dupicate faces */
	for(efa= em->faces.last; efa; efa= efa->prev) {
		if(efa->f & flag) {
			v1= efa->v1->vn;
			v2= efa->v2->vn;
			v3= efa->v3->vn;
			if(efa->v4) v4= efa->v4->vn; else v4= NULL;
			newfa= addfacelist(v1, v2, v3, v4, efa);
			
			newfa->f= efa->f;
			efa->f -= flag;
			efa->f |= 128;
		}
	}
}

void delfaceflag(int flag)
{
	EditMesh *em = G.editMesh;
	/* delete all faces with 'flag', including edges and loose vertices */
	/* in remaining vertices/edges 'flag' is cleared */
	EditVert *eve,*nextve;
	EditEdge *eed, *nexted;
	EditFace *efa,*nextvl;

	for(eed= em->edges.first; eed; eed= eed->next) eed->f2= 0;

	/* delete faces */
	efa= em->faces.first;
	while(efa) {
		nextvl= efa->next;
		if(efa->f & flag) {
			
			efa->e1->f2= 1;
			efa->e2->f2= 1;
			efa->e3->f2= 1;
			if(efa->e4) {
				efa->e4->f2= 1;
			}
								
			BLI_remlink(&em->faces, efa);
			free_editface(efa);
		}
		efa= nextvl;
	}
	
	/* all remaining faces: make sure we keep the edges */
	for(efa= em->faces.first; efa; efa= efa->next) {
		efa->e1->f2= 0;
		efa->e2->f2= 0;
		efa->e3->f2= 0;
		if(efa->e4) {
			efa->e4->f2= 0;
		}
	}
	
	/* remove tagged edges, and clear remaining ones */
	eed= em->edges.first;
	while(eed) {
		nexted= eed->next;
		
		if(eed->f2==1) {
			remedge(eed);
			free_editedge(eed);
		}
		else {
			eed->f &= ~flag;
			eed->v1->f &= ~flag;
			eed->v2->f &= ~flag;
		}
		eed= nexted;
	}
	
	/* vertices with 'flag' now are the loose ones, and will be removed */
	eve= em->verts.first;
	while(eve) {
		nextve= eve->next;
		if(eve->f & flag) {
			BLI_remlink(&em->verts, eve);
			free_editvert(eve);
		}
		eve= nextve;
	}

}

/* ********************* */

static int contrpuntnorm(float *n, float *puno)  /* dutch: check vertex normal */
{
	float inp;

	inp= n[0]*puno[0]+n[1]*puno[1]+n[2]*puno[2];

	/* angles 90 degrees: dont flip */
	if(inp> -0.000001) return 0;

	return 1;
}


void vertexnormals(int testflip)
{
	EditMesh *em = G.editMesh;
	Mesh *me;
	EditVert *eve;
	EditFace *efa;	
	float n1[3], n2[3], n3[3], n4[3], co[4], fac1, fac2, fac3, fac4, *temp;
	float *f1, *f2, *f3, *f4, xn, yn, zn;
	float len;
	
	if(G.obedit && G.obedit->type==OB_MESH) {
		me= G.obedit->data;
		if((me->flag & ME_TWOSIDED)==0) testflip= 0;
	}

	if(G.totvert==0) return;

	if(G.totface==0) {
		/* fake vertex normals for 'halo puno'! */
		eve= em->verts.first;
		while(eve) {
			VECCOPY(eve->no, eve->co);
			Normalise( (float *)eve->no);
			eve= eve->next;
		}
		return;
	}

	/* clear normals */	
	eve= em->verts.first;
	while(eve) {
		eve->no[0]= eve->no[1]= eve->no[2]= 0.0;
		eve= eve->next;
	}
	
	/* calculate cosine angles and add to vertex normal */
	efa= em->faces.first;
	while(efa) {
		VecSubf(n1, efa->v2->co, efa->v1->co);
		VecSubf(n2, efa->v3->co, efa->v2->co);
		Normalise(n1);
		Normalise(n2);

		if(efa->v4==0) {
			VecSubf(n3, efa->v1->co, efa->v3->co);
			Normalise(n3);
			
			co[0]= saacos(-n3[0]*n1[0]-n3[1]*n1[1]-n3[2]*n1[2]);
			co[1]= saacos(-n1[0]*n2[0]-n1[1]*n2[1]-n1[2]*n2[2]);
			co[2]= saacos(-n2[0]*n3[0]-n2[1]*n3[1]-n2[2]*n3[2]);
			
		}
		else {
			VecSubf(n3, efa->v4->co, efa->v3->co);
			VecSubf(n4, efa->v1->co, efa->v4->co);
			Normalise(n3);
			Normalise(n4);
			
			co[0]= saacos(-n4[0]*n1[0]-n4[1]*n1[1]-n4[2]*n1[2]);
			co[1]= saacos(-n1[0]*n2[0]-n1[1]*n2[1]-n1[2]*n2[2]);
			co[2]= saacos(-n2[0]*n3[0]-n2[1]*n3[1]-n2[2]*n3[2]);
			co[3]= saacos(-n3[0]*n4[0]-n3[1]*n4[1]-n3[2]*n4[2]);
		}
		
		temp= efa->v1->no;
		if(testflip && contrpuntnorm(efa->n, temp) ) co[0]= -co[0];
		temp[0]+= co[0]*efa->n[0];
		temp[1]+= co[0]*efa->n[1];
		temp[2]+= co[0]*efa->n[2];
		
		temp= efa->v2->no;
		if(testflip && contrpuntnorm(efa->n, temp) ) co[1]= -co[1];
		temp[0]+= co[1]*efa->n[0];
		temp[1]+= co[1]*efa->n[1];
		temp[2]+= co[1]*efa->n[2];
		
		temp= efa->v3->no;
		if(testflip && contrpuntnorm(efa->n, temp) ) co[2]= -co[2];
		temp[0]+= co[2]*efa->n[0];
		temp[1]+= co[2]*efa->n[1];
		temp[2]+= co[2]*efa->n[2];
		
		if(efa->v4) {
			temp= efa->v4->no;
			if(testflip && contrpuntnorm(efa->n, temp) ) co[3]= -co[3];
			temp[0]+= co[3]*efa->n[0];
			temp[1]+= co[3]*efa->n[1];
			temp[2]+= co[3]*efa->n[2];
		}
		
		efa= efa->next;
	}

	/* normalise vertex normals */
	eve= em->verts.first;
	while(eve) {
		len= Normalise(eve->no);
		if(len==0.0) {
			VECCOPY(eve->no, eve->co);
			Normalise( eve->no);
		}
		eve= eve->next;
	}
	
	/* vertex normal flip-flags for shade (render) */
	efa= em->faces.first;
	while(efa) {
		efa->puno=0;			

		if(testflip) {
			f1= efa->v1->no;
			f2= efa->v2->no;
			f3= efa->v3->no;
			
			fac1= efa->n[0]*f1[0] + efa->n[1]*f1[1] + efa->n[2]*f1[2];
			if(fac1<0.0) {
				efa->puno = ME_FLIPV1;
			}
			fac2= efa->n[0]*f2[0] + efa->n[1]*f2[1] + efa->n[2]*f2[2];
			if(fac2<0.0) {
				efa->puno += ME_FLIPV2;
			}
			fac3= efa->n[0]*f3[0] + efa->n[1]*f3[1] + efa->n[2]*f3[2];
			if(fac3<0.0) {
				efa->puno += ME_FLIPV3;
			}
			if(efa->v4) {
				f4= efa->v4->no;
				fac4= efa->n[0]*f4[0] + efa->n[1]*f4[1] + efa->n[2]*f4[2];
				if(fac4<0.0) {
					efa->puno += ME_FLIPV4;
				}
			}
		}
		/* projection for cubemap! */
		xn= fabs(efa->n[0]);
		yn= fabs(efa->n[1]);
		zn= fabs(efa->n[2]);
		
		if(zn>xn && zn>yn) efa->puno += ME_PROJXY;
		else if(yn>xn && yn>zn) efa->puno += ME_PROJXZ;
		else efa->puno += ME_PROJYZ;
		
		efa= efa->next;
	}
}

void flipface(EditFace *efa)
{
	if(efa->v4) {
		SWAP(EditVert *, efa->v2, efa->v4);
		SWAP(EditEdge *, efa->e1, efa->e4);
		SWAP(EditEdge *, efa->e2, efa->e3);
		SWAP(unsigned int, efa->tf.col[1], efa->tf.col[3]);
		SWAP(float, efa->tf.uv[1][0], efa->tf.uv[3][0]);
		SWAP(float, efa->tf.uv[1][1], efa->tf.uv[3][1]);
	}
	else {
		SWAP(EditVert *, efa->v2, efa->v3);
		SWAP(EditEdge *, efa->e1, efa->e3);
		SWAP(unsigned int, efa->tf.col[1], efa->tf.col[2]);
		efa->e2->dir= 1-efa->e2->dir;
		SWAP(float, efa->tf.uv[1][0], efa->tf.uv[2][0]);
		SWAP(float, efa->tf.uv[1][1], efa->tf.uv[2][1]);
	}
	if(efa->v4) CalcNormFloat4(efa->v1->co, efa->v2->co, efa->v3->co, efa->v4->co, efa->n);
	else CalcNormFloat(efa->v1->co, efa->v2->co, efa->v3->co, efa->n);
}


void flip_editnormals(void)
{
	EditMesh *em = G.editMesh;
	EditFace *efa;
	
	efa= em->faces.first;
	while(efa) {
		if( faceselectedAND(efa, 1) ) {
			flipface(efa);
		}
		efa= efa->next;
	}
}

/* does face centers too */
void recalc_editnormals(void)
{
	EditMesh *em = G.editMesh;
	EditFace *efa;

	efa= em->faces.first;
	while(efa) {
		if(efa->v4) {
			CalcNormFloat4(efa->v1->co, efa->v2->co, efa->v3->co, efa->v4->co, efa->n);
			CalcCent4f(efa->cent, efa->v1->co, efa->v2->co, efa->v3->co, efa->v4->co);
		}
		else {
			CalcNormFloat(efa->v1->co, efa->v2->co, efa->v3->co, efa->n);
			CalcCent3f(efa->cent, efa->v1->co, efa->v2->co, efa->v3->co);
		}
		efa= efa->next;
	}
}



int compareface(EditFace *vl1, EditFace *vl2)
{
	EditVert *v1, *v2, *v3, *v4;
	
	if(vl1->v4 && vl2->v4) {
		v1= vl2->v1;
		v2= vl2->v2;
		v3= vl2->v3;
		v4= vl2->v4;
		
		if(vl1->v1==v1 || vl1->v2==v1 || vl1->v3==v1 || vl1->v4==v1) {
			if(vl1->v1==v2 || vl1->v2==v2 || vl1->v3==v2 || vl1->v4==v2) {
				if(vl1->v1==v3 || vl1->v2==v3 || vl1->v3==v3 || vl1->v4==v3) {
					if(vl1->v1==v4 || vl1->v2==v4 || vl1->v3==v4 || vl1->v4==v4) {
						return 1;
					}
				}
			}
		}
	}
	else if(vl1->v4==0 && vl2->v4==0) {
		v1= vl2->v1;
		v2= vl2->v2;
		v3= vl2->v3;

		if(vl1->v1==v1 || vl1->v2==v1 || vl1->v3==v1) {
			if(vl1->v1==v2 || vl1->v2==v2 || vl1->v3==v2) {
				if(vl1->v1==v3 || vl1->v2==v3 || vl1->v3==v3) {
					return 1;
				}
			}
		}
	}

	return 0;
}

int exist_face(EditVert *v1, EditVert *v2, EditVert *v3, EditVert *v4)
{
	EditMesh *em = G.editMesh;
	EditFace *efa, efatest;
	
	efatest.v1= v1;
	efatest.v2= v2;
	efatest.v3= v3;
	efatest.v4= v4;
	
	efa= em->faces.first;
	while(efa) {
		if(compareface(&efatest, efa)) return 1;
		efa= efa->next;
	}
	return 0;
}


float convex(float *v1, float *v2, float *v3, float *v4)
{
	float cross[3], test[3];
	float inpr;
	
	CalcNormFloat(v1, v2, v3, cross);
	CalcNormFloat(v1, v3, v4, test);

	inpr= cross[0]*test[0]+cross[1]*test[1]+cross[2]*test[2];

	return inpr;
}


