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

/* main mesh editing routines. please note that 'vlak' is used here to denote a 'face'. */
/* at that time for me a face was something at the frontside of a human head! (ton) */

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

#include "PIL_time.h"

#include "MTC_matrixops.h"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_screen_types.h"
#include "DNA_key_types.h"
#include "DNA_scene_types.h"
#include "DNA_view3d_types.h"
#include "DNA_material_types.h"
#include "DNA_texture_types.h"
#include "DNA_userdef_types.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_editVert.h"
#include "BLI_rand.h"


#include "BKE_utildefines.h"
#include "BKE_key.h"
#include "BKE_object.h"
#include "BKE_texture.h"
#include "BKE_displist.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_mesh.h"

#include "BIF_gl.h"
#include "BIF_graphics.h"
#include "BIF_editkey.h"
#include "BIF_space.h"
#include "BIF_toolbox.h"
#include "BIF_screen.h"
#include "BIF_interface.h"
#include "BIF_editmesh.h"
#include "BIF_mywindow.h"
#include "BIF_resources.h"
#include "BIF_glutil.h"
#include "BIF_cursors.h"

#include "BSE_view.h"
#include "BSE_edit.h"
#include "BSE_trans_types.h"

#include "BDR_drawobject.h"
#include "BDR_editobject.h"
#include "BDR_editface.h"
#include "BDR_vpaint.h"

#include "mydevice.h"
#include "blendef.h"
#include "nla.h"		/* For __NLA : Important - Do not remove! */
#include "render.h"

#include "GHOST_C-api.h"
#include "winlay.h"

#ifdef WIN32
	#ifndef snprintf
		#define snprintf  _snprintf
	#endif
#endif

/****/

static float convex(float *v1, float *v2, float *v3, float *v4);

/* EditMesh Undo */
void make_editMesh_real(Mesh *me);
void load_editMesh_real(Mesh *me, int);
/****/


/* extern ListBase fillvertbase, filledgebase; */ /* scanfill.c, in
    the lib... already in BLI_blenlib.h */


extern short editbutflag;

static float icovert[12][3] = {
	{0,0,-200}, 
	{144.72, -105.144,-89.443},
	{-55.277, -170.128,-89.443}, 
	{-178.885,0,-89.443},
	{-55.277,170.128,-89.443}, 
	{144.72,105.144,-89.443},
	{55.277,-170.128,89.443},
	{-144.72,-105.144,89.443},
	{-144.72,105.144,89.443},
	{55.277,170.128,89.443},
	{178.885,0,89.443},
	{0,0,200}
};
static short icovlak[20][3] = {
	{1,0,2},
	{1,0,5},
	{2,0,3},
	{3,0,4},
	{4,0,5},
	{1,5,10},
	{2,1,6},
	{3,2,7},
	{4,3,8},
	{5,4,9},
	{10,1,6},
	{6,2,7},
	{7,3,8},
	{8,4,9},
	{9,5,10},
	{6,10,11},
	{7,6,11},
	{8,7,11},
	{9,8,11},
	{10,9,11}
};

/* DEFINES */
#define UVCOPY(t, s) memcpy(t, s, 2 * sizeof(float));

#define TEST_EDITMESH	if(G.obedit==0) return; \
						if( (G.vd->lay & G.obedit->lay)==0 ) return;

#define FACE_MARKCLEAR(f) (f->f1 = 1)

/* ***************** HASH ********************* */

/* HASH struct quickly finding of edges */
struct HashEdge {
	struct EditEdge *eed;
	struct HashEdge *next;
};

struct HashEdge *hashedgetab=NULL;

/********* qsort routines *********/


struct xvertsort {
	float x;
	EditVert *v1;
};

/* Functions */
static int vergxco(const void *v1, const void *v2)
{
	const struct xvertsort *x1=v1, *x2=v2;

	if( x1->x > x2->x ) return 1;
	else if( x1->x < x2->x) return -1;
	return 0;
}

struct vlaksort {
	long x;
	struct EditVlak *evl;
};


static int vergvlak(const void *v1, const void *v2)
{
	const struct vlaksort *x1=v1, *x2=v2;
	
	if( x1->x > x2->x ) return 1;
	else if( x1->x < x2->x) return -1;
	return 0;
}


/* ************ ADD / REMOVE / FIND ****************** */

#define EDHASH(a, b)	( (a)*256 + (b) )
#define EDHASHSIZE	65536

EditVert *addvertlist(float *vec)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	static unsigned char hashnr= 0;

	eve= calloc(sizeof(EditVert), 1);
	BLI_addtail(&em->verts, eve);
	
	if(vec) VECCOPY(eve->co, vec);

	eve->hash= hashnr++;

	/* new verts get keyindex of -1 since they did not
	 * have a pre-editmode vertex order
	 */
	eve->keyindex = -1;
	return eve;
}

EditEdge *findedgelist(EditVert *v1, EditVert *v2)
{
	EditVert *v3;
	struct HashEdge *he;

	if(hashedgetab==0) {
		hashedgetab= MEM_callocN(EDHASHSIZE*sizeof(struct HashEdge), "hashedgetab");
	}
	
	/* swap ? */
	if( (long)v1 > (long)v2) {
		v3= v2; 
		v2= v1; 
		v1= v3;
	}
	
	he= hashedgetab + EDHASH(v1->hash, v2->hash);
	
	while(he) {
		
		if(he->eed && he->eed->v1==v1 && he->eed->v2==v2) return he->eed;
		
		he= he->next;
	}
	return 0;
}

static void insert_hashedge(EditEdge *eed)
{
	/* assuming that eed is not in the list yet, and that a find has been done before */
	
	struct HashEdge *first, *he;

	first= hashedgetab + EDHASH(eed->v1->hash, eed->v2->hash);

	if( first->eed==0 ) {
		first->eed= eed;
	}
	else {
		he= (struct HashEdge *)malloc(sizeof(struct HashEdge)); 
		he->eed= eed;
		he->next= first->next;
		first->next= he;
	}
}

static void remove_hashedge(EditEdge *eed)
{
	/* assuming eed is in the list */
	
	struct HashEdge *first, *he, *prev=NULL;


	he=first= hashedgetab + EDHASH(eed->v1->hash, eed->v2->hash);

	while(he) {
		if(he->eed == eed) {
			/* remove from list */
			if(he==first) {
				if(first->next) {
					he= first->next;
					first->eed= he->eed;
					first->next= he->next;
					free(he);
				}
				else he->eed= 0;
			}
			else {
				prev->next= he->next;
				free(he);
			}
			return;
		}
		prev= he;
		he= he->next;
	}
}

void free_hashedgetab(void)
{
	struct HashEdge *he, *first, *hen;
	int a;
	
	if(hashedgetab) {
	
		first= hashedgetab;
		for(a=0; a<EDHASHSIZE; a++, first++) {
			he= first->next;
			while(he) {
				hen= he->next;
				free(he);
				he= hen;
			}
		}
		MEM_freeN(hashedgetab);
		hashedgetab= 0;
	}
}

EditEdge *addedgelist(EditVert *v1, EditVert *v2, EditEdge *example)
{
	EditMesh *em = G.editMesh;
	EditVert *v3;
	EditEdge *eed;
	int swap= 0;
	
	if(v1==v2) return NULL;
	if(v1==NULL || v2==NULL) return NULL;

	/* swap ? */
	if(v1>v2) {
		v3= v2; 
		v2= v1; 
		v1= v3;
		swap= 1;
	}
	
	/* find in hashlist */
	eed= findedgelist(v1, v2);
	
	if(eed==NULL) {

		eed= (EditEdge *)calloc(sizeof(EditEdge), 1);
		eed->v1= v1;
		eed->v2= v2;
		BLI_addtail(&em->edges, eed);
		eed->dir= swap;
		insert_hashedge(eed);
	}

	/* copy crease data, seam flag? */
	if(example) {
		eed->crease = example->crease;
	}

	return eed;
}

static void free_editvert (EditVert *eve)
{
	if (eve->dw) MEM_freeN (eve->dw);
	free (eve);
}

void remedge(EditEdge *eed)
{
	EditMesh *em = G.editMesh;

	BLI_remlink(&em->edges, eed);
	remove_hashedge(eed);
}

static void free_editedge(EditEdge *eed)
{
	free(eed);
}

static void free_editvlak(EditVlak *evl)
{
	free(evl);
}

static void free_vertlist(ListBase *edve) 
{
	EditVert *eve, *next;

	if (!edve) return;

	eve= edve->first;
	while(eve) {
		next= eve->next;
		free_editvert(eve);
		eve= next;
	}
	edve->first= edve->last= NULL;
}

static void free_edgelist(ListBase *lb)
{
	EditEdge *eed, *next;
	
	eed= lb->first;
	while(eed) {
		next= eed->next;
		free_editedge(eed);
		eed= next;
	}
	lb->first= lb->last= NULL;
}

static void free_vlaklist(ListBase *lb)
{
	EditVlak *evl, *next;
	
	evl= lb->first;
	while(evl) {
		next= evl->next;
		free_editvlak(evl);
		evl= next;
	}
	lb->first= lb->last= NULL;
}

EditVlak *addvlaklist(EditVert *v1, EditVert *v2, EditVert *v3, EditVert *v4, EditVlak *example)
{
	EditMesh *em = G.editMesh;
	EditVlak *evl;
	EditEdge *e1, *e2=0, *e3=0, *e4=0;
	

	/* add face to list and do the edges */
	e1= addedgelist(v1, v2, example?example->e1:NULL);
	e2= addedgelist(v2, v3, example?example->e2:NULL);
	if(v4) e3= addedgelist(v3, v4, example?example->e3:NULL); 
	else e3= addedgelist(v3, v1, example?example->e3:NULL);
	if(v4) e4= addedgelist(v4, v1, example?example->e4:NULL);
	
	if(v1==v2 || v2==v3 || v1==v3) return NULL;
	if(e2==0) return NULL;

	evl= (EditVlak *)calloc(sizeof(EditVlak), 1);
	evl->v1= v1;
	evl->v2= v2;
	evl->v3= v3;
	evl->v4= v4;

	evl->e1= e1;
	evl->e2= e2;
	evl->e3= e3;
	evl->e4= e4;

	if(example) {
		evl->mat_nr= example->mat_nr;
		evl->tf= example->tf;
		evl->flag= example->flag;
	}
	else { 
		if (G.obedit && G.obedit->actcol)
			evl->mat_nr= G.obedit->actcol-1;
		default_uv(evl->tf.uv, 1.0);

		/* Initialize colors */
		evl->tf.col[0]= evl->tf.col[1]= evl->tf.col[2]= evl->tf.col[3]= vpaint_get_current_col();
	}
	
	BLI_addtail(&em->faces, evl);

	if(evl->v4) CalcNormFloat4(v1->co, v2->co, v3->co, v4->co, evl->n);
	else CalcNormFloat(v1->co, v2->co, v3->co, evl->n);

	return evl;
}

/* ********* end add / new / find */

static int comparevlak(EditVlak *vl1, EditVlak *vl2)
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

static int exist_vlak(EditVert *v1, EditVert *v2, EditVert *v3, EditVert *v4)
{
	EditMesh *em = G.editMesh;
	EditVlak *evl, evltest;
	
	evltest.v1= v1;
	evltest.v2= v2;
	evltest.v3= v3;
	evltest.v4= v4;
	
	evl= em->faces.first;
	while(evl) {
		if(comparevlak(&evltest, evl)) return 1;
		evl= evl->next;
	}
	return 0;
}


static int vlakselectedOR(EditVlak *evl, int flag)
{
	
	if(evl->v1->f & flag) return 1;
	if(evl->v2->f & flag) return 1;
	if(evl->v3->f & flag) return 1;
	if(evl->v4 && (evl->v4->f & 1)) return 1;
	return 0;
}

int vlakselectedAND(EditVlak *evl, int flag)
{
	if(evl->v1->f & flag) {
		if(evl->v2->f & flag) {
			if(evl->v3->f & flag) {
				if(evl->v4) {
					if(evl->v4->f & flag) return 1;
				}
				else return 1;
			}
		}
	}
	return 0;
}

void recalc_editnormals(void)
{
	EditMesh *em = G.editMesh;
	EditVlak *evl;

	evl= em->faces.first;
	while(evl) {
		if(evl->v4) CalcNormFloat4(evl->v1->co, evl->v2->co, evl->v3->co, evl->v4->co, evl->n);
		else CalcNormFloat(evl->v1->co, evl->v2->co, evl->v3->co, evl->n);
		evl= evl->next;
	}
}

static void flipvlak(EditVlak *evl)
{
	if(evl->v4) {
		SWAP(EditVert *, evl->v2, evl->v4);
		SWAP(EditEdge *, evl->e1, evl->e4);
		SWAP(EditEdge *, evl->e2, evl->e3);
		SWAP(unsigned int, evl->tf.col[1], evl->tf.col[3]);
		SWAP(float, evl->tf.uv[1][0], evl->tf.uv[3][0]);
		SWAP(float, evl->tf.uv[1][1], evl->tf.uv[3][1]);
	}
	else {
		SWAP(EditVert *, evl->v2, evl->v3);
		SWAP(EditEdge *, evl->e1, evl->e3);
		SWAP(unsigned int, evl->tf.col[1], evl->tf.col[2]);
		evl->e2->dir= 1-evl->e2->dir;
		SWAP(float, evl->tf.uv[1][0], evl->tf.uv[2][0]);
		SWAP(float, evl->tf.uv[1][1], evl->tf.uv[2][1]);
	}
	if(evl->v4) CalcNormFloat4(evl->v1->co, evl->v2->co, evl->v3->co, evl->v4->co, evl->n);
	else CalcNormFloat(evl->v1->co, evl->v2->co, evl->v3->co, evl->n);
}


void flip_editnormals(void)
{
	EditMesh *em = G.editMesh;
	EditVlak *evl;
	
	evl= em->faces.first;
	while(evl) {
		if( vlakselectedAND(evl, 1) ) {
			flipvlak(evl);
		}
		evl= evl->next;
	}
}

/* ************************ IN & OUT ***************************** */

static void edge_normal_compare(EditEdge *eed, EditVlak *evl1)
{
	EditVlak *evl2;
	float cent1[3], cent2[3];
	float inp;
	
	evl2= (EditVlak *)eed->vn;
	if(evl1==evl2) return;
	
	inp= evl1->n[0]*evl2->n[0] + evl1->n[1]*evl2->n[1] + evl1->n[2]*evl2->n[2];
	if(inp<0.999 && inp >-0.999) eed->f= 1;
		
	if(evl1->v4) CalcCent4f(cent1, evl1->v1->co, evl1->v2->co, evl1->v3->co, evl1->v4->co);
	else CalcCent3f(cent1, evl1->v1->co, evl1->v2->co, evl1->v3->co);
	if(evl2->v4) CalcCent4f(cent2, evl2->v1->co, evl2->v2->co, evl2->v3->co, evl2->v4->co);
	else CalcCent3f(cent2, evl2->v1->co, evl2->v2->co, evl2->v3->co);
	
	VecSubf(cent1, cent2, cent1);
	Normalise(cent1);
	inp= cent1[0]*evl1->n[0] + cent1[1]*evl1->n[1] + cent1[2]*evl1->n[2]; 

	if(inp < -0.001 ) eed->f1= 1;
}

static void edge_drawflags(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed, *e1, *e2, *e3, *e4;
	EditVlak *evl;
	
	/* - count number of times edges are used in faces: 0 en 1 time means draw edge
	 * - edges more than 1 time used: in *vn is pointer to first face
	 * - check all faces, when normal differs to much: draw (flag becomes 1)
	 */

	/* later on: added flags for 'cylinder' and 'sphere' intersection tests in old
	   game engine (2.04)
	 */
	
	recalc_editnormals();
	
	/* init */
	eve= em->verts.first;
	while(eve) {
		eve->f1= 1;		/* during test it's set at zero */
		eve= eve->next;
	}
	eed= em->edges.first;
	while(eed) {
		eed->f= eed->f1= 0;
		eed->vn= 0;
		eed= eed->next;
	}

	evl= em->faces.first;
	while(evl) {
		e1= evl->e1;
		e2= evl->e2;
		e3= evl->e3;
		e4= evl->e4;
		if(e1->f<3) e1->f+= 1;
		if(e2->f<3) e2->f+= 1;
		if(e3->f<3) e3->f+= 1;
		if(e4 && e4->f<3) e4->f+= 1;
		
		if(e1->vn==0) e1->vn= (EditVert *)evl;
		if(e2->vn==0) e2->vn= (EditVert *)evl;
		if(e3->vn==0) e3->vn= (EditVert *)evl;
		if(e4 && e4->vn==0) e4->vn= (EditVert *)evl;
		
		evl= evl->next;
	}

	if(G.f & G_ALLEDGES) {
		evl= em->faces.first;
		while(evl) {
			if(evl->e1->f>=2) evl->e1->f= 1;
			if(evl->e2->f>=2) evl->e2->f= 1;
			if(evl->e3->f>=2) evl->e3->f= 1;
			if(evl->e4 && evl->e4->f>=2) evl->e4->f= 1;
			
			evl= evl->next;
		}		
	}	
	else {
		
		/* handle single-edges for 'test cylinder flag' (old engine) */
		
		eed= em->edges.first;
		while(eed) {
			if(eed->f==1) eed->f1= 1;
			eed= eed->next;
		}

		/* all faces, all edges with flag==2: compare normal */
		evl= em->faces.first;
		while(evl) {
			if(evl->e1->f==2) edge_normal_compare(evl->e1, evl);
			if(evl->e2->f==2) edge_normal_compare(evl->e2, evl);
			if(evl->e3->f==2) edge_normal_compare(evl->e3, evl);
			if(evl->e4 && evl->e4->f==2) edge_normal_compare(evl->e4, evl);
			
			evl= evl->next;
		}
		
		/* sphere collision flag */
		
		eed= em->edges.first;
		while(eed) {
			if(eed->f1!=1) {
				eed->v1->f1= eed->v2->f1= 0;
			}
			eed= eed->next;
		}
		
	}
}

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
	EditVlak *evl;	
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
	evl= em->faces.first;
	while(evl) {
		VecSubf(n1, evl->v2->co, evl->v1->co);
		VecSubf(n2, evl->v3->co, evl->v2->co);
		Normalise(n1);
		Normalise(n2);

		if(evl->v4==0) {
			VecSubf(n3, evl->v1->co, evl->v3->co);
			Normalise(n3);
			
			co[0]= saacos(-n3[0]*n1[0]-n3[1]*n1[1]-n3[2]*n1[2]);
			co[1]= saacos(-n1[0]*n2[0]-n1[1]*n2[1]-n1[2]*n2[2]);
			co[2]= saacos(-n2[0]*n3[0]-n2[1]*n3[1]-n2[2]*n3[2]);
			
		}
		else {
			VecSubf(n3, evl->v4->co, evl->v3->co);
			VecSubf(n4, evl->v1->co, evl->v4->co);
			Normalise(n3);
			Normalise(n4);
			
			co[0]= saacos(-n4[0]*n1[0]-n4[1]*n1[1]-n4[2]*n1[2]);
			co[1]= saacos(-n1[0]*n2[0]-n1[1]*n2[1]-n1[2]*n2[2]);
			co[2]= saacos(-n2[0]*n3[0]-n2[1]*n3[1]-n2[2]*n3[2]);
			co[3]= saacos(-n3[0]*n4[0]-n3[1]*n4[1]-n3[2]*n4[2]);
		}
		
		temp= evl->v1->no;
		if(testflip && contrpuntnorm(evl->n, temp) ) co[0]= -co[0];
		temp[0]+= co[0]*evl->n[0];
		temp[1]+= co[0]*evl->n[1];
		temp[2]+= co[0]*evl->n[2];
		
		temp= evl->v2->no;
		if(testflip && contrpuntnorm(evl->n, temp) ) co[1]= -co[1];
		temp[0]+= co[1]*evl->n[0];
		temp[1]+= co[1]*evl->n[1];
		temp[2]+= co[1]*evl->n[2];
		
		temp= evl->v3->no;
		if(testflip && contrpuntnorm(evl->n, temp) ) co[2]= -co[2];
		temp[0]+= co[2]*evl->n[0];
		temp[1]+= co[2]*evl->n[1];
		temp[2]+= co[2]*evl->n[2];
		
		if(evl->v4) {
			temp= evl->v4->no;
			if(testflip && contrpuntnorm(evl->n, temp) ) co[3]= -co[3];
			temp[0]+= co[3]*evl->n[0];
			temp[1]+= co[3]*evl->n[1];
			temp[2]+= co[3]*evl->n[2];
		}
		
		evl= evl->next;
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
	evl= em->faces.first;
	while(evl) {
		evl->f=0;			

		if(testflip) {
			f1= evl->v1->no;
			f2= evl->v2->no;
			f3= evl->v3->no;
			
			fac1= evl->n[0]*f1[0] + evl->n[1]*f1[1] + evl->n[2]*f1[2];
			if(fac1<0.0) {
				evl->f = ME_FLIPV1;
			}
			fac2= evl->n[0]*f2[0] + evl->n[1]*f2[1] + evl->n[2]*f2[2];
			if(fac2<0.0) {
				evl->f += ME_FLIPV2;
			}
			fac3= evl->n[0]*f3[0] + evl->n[1]*f3[1] + evl->n[2]*f3[2];
			if(fac3<0.0) {
				evl->f += ME_FLIPV3;
			}
			if(evl->v4) {
				f4= evl->v4->no;
				fac4= evl->n[0]*f4[0] + evl->n[1]*f4[1] + evl->n[2]*f4[2];
				if(fac4<0.0) {
					evl->f += ME_FLIPV4;
				}
			}
		}
		/* projection for cubemap! */
		xn= fabs(evl->n[0]);
		yn= fabs(evl->n[1]);
		zn= fabs(evl->n[2]);
		
		if(zn>xn && zn>yn) evl->f += ME_PROJXY;
		else if(yn>xn && yn>zn) evl->f += ME_PROJXZ;
		else evl->f += ME_PROJYZ;
		
		evl= evl->next;
	}
}

void free_editMesh(void)
{
	
	EditMesh *em = G.editMesh;
	if(em->verts.first) free_vertlist(&em->verts);
	if(em->edges.first) free_edgelist(&em->edges);
	if(em->faces.first) free_vlaklist(&em->faces);
	free_hashedgetab();
	G.totvert= G.totface= 0;
}

void make_editMesh(void)
{
	Mesh *me;	

	me= get_mesh(G.obedit);
	if (me != G.undo_last_data) {
		G.undo_edit_level= -1;
		G.undo_edit_highest= -1;
		if (G.undo_clear) G.undo_clear();
		G.undo_last_data= me;
		G.undo_clear= undo_clear_mesh;
	}
	make_editMesh_real(me);
}

void make_editMesh_real(Mesh *me)
{
	EditMesh *em = G.editMesh;
	MFace *mface;
	TFace *tface;
	MVert *mvert;
	KeyBlock *actkey=0;
	EditVert *eve, **evlist, *eve1, *eve2, *eve3, *eve4;
	EditVlak *evl;
	EditEdge *eed;
	int tot, a;

	if(G.obedit==NULL) return;

	/* because of reload */
	free_editMesh();
	
	G.totvert= tot= me->totvert;

	if(tot==0) {
		countall();
		return;
	}
	
	waitcursor(1);

	/* keys? */
	if(me->key) {
		actkey= me->key->block.first;
		while(actkey) {
			if(actkey->flag & SELECT) break;
			actkey= actkey->next;
		}
	}

	if(actkey) {
		key_to_mesh(actkey, me);
		tot= actkey->totelem;
	}

	/* make editverts */
	mvert= me->mvert;

	evlist= (EditVert **)MEM_mallocN(tot*sizeof(void *),"evlist");
	for(a=0; a<tot; a++, mvert++) {
		eve= addvertlist(mvert->co);
		evlist[a]= eve;
		
		// face select sets selection in next loop
		if( (G.f & G_FACESELECT)==0 )
			eve->f |= (mvert->flag & 1);
		
		if (mvert->flag & ME_HIDE) eve->h= 1;		
		eve->no[0]= mvert->no[0]/32767.0;
		eve->no[1]= mvert->no[1]/32767.0;
		eve->no[2]= mvert->no[2]/32767.0;

		/* lets overwrite the keyindex of the editvert
		 * with the order it used to be in before
		 * editmode
		 */
		eve->keyindex = a;

#ifdef __NLA

		if (me->dvert){
			eve->totweight = me->dvert[a].totweight;
			if (me->dvert[a].dw){
				eve->dw = MEM_callocN (sizeof(MDeformWeight) * me->dvert[a].totweight, "deformWeight");
				memcpy (eve->dw, me->dvert[a].dw, sizeof(MDeformWeight) * me->dvert[a].totweight);
			}
		}

#endif
	}

	if(actkey && actkey->totelem!=me->totvert);
	else {
		unsigned int *mcol;
		
		/* make edges */
		if(me->medge) {
			MEdge *medge= me->medge;
			
			for(a=0; a<me->totedge; a++, medge++) {
				eed= addedgelist(evlist[medge->v1], evlist[medge->v2], NULL);
				eed->crease= ((float)medge->crease)/255.0;
			}

		}
		
		/* make faces */
		mface= me->mface;
		tface= me->tface;
		mcol= (unsigned int *)me->mcol;
		
		for(a=0; a<me->totface; a++, mface++) {
			eve1= evlist[mface->v1];
			eve2= evlist[mface->v2];
			if(mface->v3) eve3= evlist[mface->v3]; else eve3= NULL;
			if(mface->v4) eve4= evlist[mface->v4]; else eve4= NULL;
			
			evl= addvlaklist(eve1, eve2, eve3, eve4, NULL);

			if(evl) {
			
				if(mcol) memcpy(evl->tf.col, mcol, 4*sizeof(int));

				if(me->tface) {
					evl->tf= *tface;

					if( tface->flag & TF_SELECT) {
						if(G.f & G_FACESELECT) {
							eve1->f |= 1;
							eve2->f |= 1;
							if(eve3) eve3->f |= 1;
							if(eve4) eve4->f |= 1;
						}
					}
				}
			
				evl->mat_nr= mface->mat_nr;
				evl->flag= mface->flag;
			}

			if(me->tface) tface++;
			if(mcol) mcol+=4;
		}
	}
	
	/* intrr: needed because of hidden vertices imported from Mesh */
	
	eed= em->edges.first;
	while(eed) {
		if(eed->v1->h || eed->v2->h) eed->h= 1;
		else eed->h= 0;
		eed= eed->next;
	}	
	
	MEM_freeN(evlist);
	
	countall();
	
	if (mesh_uses_displist(me))
		makeDispList(G.obedit);
	
	waitcursor(0);
}

/** Rotates MFace and UVFace vertices in case the last
  * vertex index is = 0. 
  * This function is a hack and may only be called in the
  * conversion from EditMesh to Mesh data.
  * This function is similar to test_index_mface in
  * blenkernel/intern/mesh.c. 
  * To not clutter the blenkernel code with more bad level
  * calls/structures, this function resides here.
  */


static void fix_faceindices(MFace *mface, EditVlak *evl, int nr)
{
	int a;
	float tmpuv[2];
	unsigned int tmpcol;

	/* first test if the face is legal */

	if(mface->v3 && mface->v3==mface->v4) {
		mface->v4= 0;
		nr--;
	}
	if(mface->v2 && mface->v2==mface->v3) {
		mface->v3= mface->v4;
		mface->v4= 0;
		nr--;
	}
	if(mface->v1==mface->v2) {
		mface->v2= mface->v3;
		mface->v3= mface->v4;
		mface->v4= 0;
		nr--;
	}

	/* prevent a zero index value at the wrong location */
	if(nr==2) {
		if(mface->v2==0) SWAP(int, mface->v1, mface->v2);
	}
	else if(nr==3) {
		if(mface->v3==0) {
			SWAP(int, mface->v1, mface->v2);
			SWAP(int, mface->v2, mface->v3);
			/* rotate face UV coordinates, too */
			UVCOPY(tmpuv, evl->tf.uv[0]);
			UVCOPY(evl->tf.uv[0], evl->tf.uv[1]);
			UVCOPY(evl->tf.uv[1], evl->tf.uv[2]);
			UVCOPY(evl->tf.uv[2], tmpuv);
			/* same with vertex colours */
			tmpcol = evl->tf.col[0];
			evl->tf.col[0] = evl->tf.col[1];
			evl->tf.col[1] = evl->tf.col[2];
			evl->tf.col[2] = tmpcol;

			
			a= mface->edcode;
			mface->edcode= 0;
			if(a & ME_V1V2) mface->edcode |= ME_V3V1;
			if(a & ME_V2V3) mface->edcode |= ME_V1V2;
			if(a & ME_V3V1) mface->edcode |= ME_V2V3;
			
			a= mface->puno;
			mface->puno &= ~15;
			if(a & ME_FLIPV1) mface->puno |= ME_FLIPV2;
			if(a & ME_FLIPV2) mface->puno |= ME_FLIPV3;
			if(a & ME_FLIPV3) mface->puno |= ME_FLIPV1;

		}
	}
	else if(nr==4) {
		if(mface->v3==0 || mface->v4==0) {
			SWAP(int, mface->v1, mface->v3);
			SWAP(int, mface->v2, mface->v4);
			/* swap UV coordinates */
			UVCOPY(tmpuv, evl->tf.uv[0]);
			UVCOPY(evl->tf.uv[0], evl->tf.uv[2]);
			UVCOPY(evl->tf.uv[2], tmpuv);
			UVCOPY(tmpuv, evl->tf.uv[1]);
			UVCOPY(evl->tf.uv[1], evl->tf.uv[3]);
			UVCOPY(evl->tf.uv[3], tmpuv);
			/* swap vertex colours */
			tmpcol = evl->tf.col[0];
			evl->tf.col[0] = evl->tf.col[2];
			evl->tf.col[2] = tmpcol;
			tmpcol = evl->tf.col[1];
			evl->tf.col[1] = evl->tf.col[3];
			evl->tf.col[3] = tmpcol;

			a= mface->edcode;
			mface->edcode= 0;
			if(a & ME_V1V2) mface->edcode |= ME_V3V4;
			if(a & ME_V2V3) mface->edcode |= ME_V2V3;
			if(a & ME_V3V4) mface->edcode |= ME_V1V2;
			if(a & ME_V4V1) mface->edcode |= ME_V4V1;

			a= mface->puno;
			mface->puno &= ~15;
			if(a & ME_FLIPV1) mface->puno |= ME_FLIPV3;
			if(a & ME_FLIPV2) mface->puno |= ME_FLIPV4;
			if(a & ME_FLIPV3) mface->puno |= ME_FLIPV1;
			if(a & ME_FLIPV4) mface->puno |= ME_FLIPV2;

		}
	}
}



/* load from EditMode to Mesh */

void load_editMesh()
{
	Mesh *me;

	waitcursor(1);
	countall();
	me= get_mesh(G.obedit);
       
	load_editMesh_real(me, 0);
}


void load_editMesh_real(Mesh *me, int undo)
{
	EditMesh *em = G.editMesh;
	MVert *mvert, *oldverts;
	MEdge *medge=NULL;
	MFace *mface;
	MSticky *ms;
	KeyBlock *actkey=NULL, *currkey;
	EditVert *eve;
	EditVlak *evl;
	EditEdge *eed;
	float *fp, *newkey, *oldkey, nor[3];
	int i, a, ototvert, totedge=0;
#ifdef __NLA
	MDeformVert *dvert;
	int	usedDvert = 0;
#endif

	/* this one also tests of edges are not in faces: */
	/* eed->f==0: not in face, f==1: draw it */
	/* eed->f1 : flag for dynaface (cylindertest, old engine) */
	/* eve->f1 : flag for dynaface (sphere test, old engine) */
	edge_drawflags();
	
	/* WATCH IT: in evl->f is punoflag (for vertex normal) */
	vertexnormals( (me->flag & ME_NOPUNOFLIP)==0 );
		
	eed= em->edges.first;
	while(eed) {
		totedge++;
		if(me->medge==NULL && (eed->f==0)) G.totface++;
		eed= eed->next;
	}
	
	/* new Vertex block */
	if(G.totvert==0) mvert= NULL;
	else mvert= MEM_callocN(G.totvert*sizeof(MVert), "loadeditMesh vert");

	/* new Edge block */
	if(me->medge && totedge) {
		medge= MEM_callocN(totedge*sizeof(MEdge), "loadeditMesh edge");
	}
	
	/* new Face block */
	if(G.totface==0) mface= NULL;
	else mface= MEM_callocN(G.totface*sizeof(MFace), "loadeditMesh face");
	

#ifdef __NLA
	if (G.totvert==0) dvert= NULL;
	else dvert = MEM_callocN(G.totvert*sizeof(MDeformVert), "loadeditMesh3");

	if (me->dvert) free_dverts(me->dvert, me->totvert);
	me->dvert=dvert;
#endif		


	/* lets save the old verts just in case we are actually working on
	 * a key ... we now do processing of the keys at the end */
	oldverts = me->mvert;
	ototvert= me->totvert;

	/* put new data in Mesh */
	me->mvert= mvert;
	me->totvert= G.totvert;

	if(me->medge) MEM_freeN(me->medge);
	me->medge= medge;
	if(medge) me->totedge= totedge; else me->totedge= 0;
	
	if(me->mface) MEM_freeN(me->mface);
	me->mface= mface;
	me->totface= G.totface;
		
	/* the vertices, abuse ->vn as counter */
	eve= em->verts.first;
	a= 0;

	while(eve) {
		VECCOPY(mvert->co, eve->co);
		mvert->mat_nr= 255;  /* what was this for, halos? */
		
		/* vertex normal */
		VECCOPY(nor, eve->no);
		VecMulf(nor, 32767.0);
		VECCOPY(mvert->no, nor);
#ifdef __NLA
		/* NEW VERSION */
		if (dvert){
			dvert->totweight=eve->totweight;
			if (eve->dw){
				dvert->dw = MEM_callocN (sizeof(MDeformWeight)*eve->totweight,
										 "deformWeight");
				memcpy (dvert->dw, eve->dw, 
						sizeof(MDeformWeight)*eve->totweight);
				usedDvert++;
			}
		}
#endif

		eve->vn= (EditVert *)(long)(a++);  /* counter */
			
		mvert->flag= 0;
			
		mvert->flag= 0;
		if(eve->f1==1) mvert->flag |= ME_SPHERETEST;
		mvert->flag |= (eve->f & 1);
		if (eve->h) mvert->flag |= ME_HIDE;			
			
		eve= eve->next;
		mvert++;
#ifdef __NLA
		dvert++;
#endif
	}
	
#ifdef __NLA
	/* If we didn't actually need the dverts, get rid of them */
	if (!usedDvert){
		free_dverts(me->dvert, G.totvert);
		me->dvert=NULL;
	}
#endif

	/* the edges */
	if(medge) {
		eed= em->edges.first;
		while(eed) {
			medge->v1= (unsigned int) eed->v1->vn;
			medge->v2= (unsigned int) eed->v2->vn;
			if(eed->f<2) medge->flag = ME_EDGEDRAW;
			medge->crease= (char)(255.0*eed->crease);
			
			medge++;
			eed= eed->next;
		}
	}

	/* the faces */
	evl= em->faces.first;
	i = 0;
	while(evl) {
		mface= &((MFace *) me->mface)[i];
		
		mface->v1= (unsigned int) evl->v1->vn;
		mface->v2= (unsigned int) evl->v2->vn;
		mface->v3= (unsigned int) evl->v3->vn;
		if(evl->v4) mface->v4= (unsigned int) evl->v4->vn;
			
		mface->mat_nr= evl->mat_nr;
		mface->puno= evl->f;
		mface->flag= evl->flag;
			
		/* mat_nr in vertex */
		if(me->totcol>1) {
			mvert= me->mvert+mface->v1;
			if(mvert->mat_nr == (char)255) mvert->mat_nr= mface->mat_nr;
			mvert= me->mvert+mface->v2;
			if(mvert->mat_nr == (char)255) mvert->mat_nr= mface->mat_nr;
			mvert= me->mvert+mface->v3;
			if(mvert->mat_nr == (char)255) mvert->mat_nr= mface->mat_nr;
			if(mface->v4) {
				mvert= me->mvert+mface->v4;
				if(mvert->mat_nr == (char)255) mvert->mat_nr= mface->mat_nr;
			}
		}
			
		/* watch: evl->e1->f==0 means loose edge */ 
			
		if(evl->e1->f==1) {
			mface->edcode |= ME_V1V2; 
			evl->e1->f= 2;
		}			
		if(evl->e2->f==1) {
			mface->edcode |= ME_V2V3; 
			evl->e2->f= 2;
		}
		if(evl->e3->f==1) {
			if(evl->v4) {
				mface->edcode |= ME_V3V4;
			}
			else {
				mface->edcode |= ME_V3V1;
			}
			evl->e3->f= 2;
		}
		if(evl->e4 && evl->e4->f==1) {
			mface->edcode |= ME_V4V1; 
			evl->e4->f= 2;
		}


		/* no index '0' at location 3 or 4 */
		if(evl->v4) fix_faceindices(mface, evl, 4);
		else fix_faceindices(mface, evl, 3);
			
		i++;
		evl= evl->next;
	}
		
	/* add loose edges as a face */
	if(medge==NULL) {
		eed= em->edges.first;
		while(eed) {
			if( eed->f==0 ) {
				mface= &((MFace *) me->mface)[i];
				mface->v1= (unsigned int) eed->v1->vn;
				mface->v2= (unsigned int) eed->v2->vn;
				test_index_mface(mface, 2);
				mface->edcode= ME_V1V2;
				i++;
			}
			eed= eed->next;
		}
	}
	
	tex_space_mesh(me);

	/* tface block, always when undo even when it wasnt used, 
	   this because of empty me pointer */
	if( (me->tface || undo) && me->totface ) {
		TFace *tfn, *tf;
			
		tf=tfn= MEM_callocN(sizeof(TFace)*me->totface, "tface");
		evl= em->faces.first;
		while(evl) {
				
			*tf= evl->tf;
				
			if(G.f & G_FACESELECT) {
				if( vlakselectedAND(evl, 1) ) tf->flag |= TF_SELECT;
				else tf->flag &= ~TF_SELECT;
			}
				
			tf++;
			evl= evl->next;
		}
		/* if undo, me was empty */
		if(me->tface) MEM_freeN(me->tface);
		me->tface= tfn;
	}
	else if(me->tface) {
		MEM_freeN(me->tface);
		me->tface= NULL;
	}
		
	/* mcol: same as tface... */
	if( (me->mcol || undo) && me->totface) {
		unsigned int *mcn, *mc;

		mc=mcn= MEM_mallocN(4*sizeof(int)*me->totface, "mcol");
		evl= em->faces.first;
		while(evl) {
			memcpy(mc, evl->tf.col, 4*sizeof(int));
				
			mc+=4;
			evl= evl->next;
		}
		if(me->mcol) MEM_freeN(me->mcol);
			me->mcol= (MCol *)mcn;
	}
	else if(me->mcol) {
		MEM_freeN(me->mcol);
		me->mcol= 0;
	}


	/* are there keys? */
	if(me->key) {

		/* find the active key */
		actkey= me->key->block.first;
		while(actkey) {
			if(actkey->flag & SELECT) break;
			actkey= actkey->next;
		}

		/* Lets reorder the key data so that things line up roughly
		 * with the way things were before editmode */
		currkey = me->key->block.first;
		while(currkey) {
			
			fp= newkey= MEM_callocN(me->key->elemsize*G.totvert,  "currkey->data");
			oldkey = currkey->data;

			eve= em->verts.first;

			i = 0;
			mvert = me->mvert;
			while(eve) {
				if (eve->keyindex >= 0) { // old vertex
					if(currkey == actkey) {
						if (actkey == me->key->refkey) {
							VECCOPY(fp, mvert->co);
						}
						else {
							VECCOPY(fp, mvert->co);
							if(oldverts) {
								VECCOPY(mvert->co, oldverts[eve->keyindex].co);
							}
						}
					}
					else {
						if(oldkey) {
							VECCOPY(fp, oldkey + 3 * eve->keyindex);
						}
					}
				}
				else {
					VECCOPY(fp, mvert->co);
				}
				fp+= 3;
				++i;
				++mvert;
				eve= eve->next;
			}
			currkey->totelem= G.totvert;
			if(currkey->data) MEM_freeN(currkey->data);
			currkey->data = newkey;
			
			currkey= currkey->next;
		}

	}

	if(oldverts) MEM_freeN(oldverts);

	if(actkey) do_spec_key(me->key);
	
	/* te be sure: clear ->vn pointers */
	eve= em->verts.first;
	while(eve) {
		eve->vn= 0;
		eve= eve->next;
	}

	/* displists of all users, including this one */
	freedisplist(&me->disp);
	freedisplist(&G.obedit->disp);
	
	/* sticky */
	if(me->msticky) {
		if (ototvert<me->totvert) {
			ms= MEM_callocN(me->totvert*sizeof(MSticky), "msticky");
			memcpy(ms, me->msticky, ototvert*sizeof(MSticky));
			MEM_freeN(me->msticky);
			me->msticky= ms;
			error("Sticky was too small");
		}
	}
	waitcursor(0);
}

void remake_editMesh(void)
{
	undo_push_mesh("Undo all changes");
	make_editMesh();
	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
}

/* *********************  TOOLS  ********************* */



void make_sticky(void)
{
	Object *ob;
	Base *base;
	MVert *mvert;
	Mesh *me;
	MSticky *ms;
	float ho[4], mat[4][4];
	int a;
	
	if(G.scene->camera==0) return;
	
	if(G.obedit) {
		error("Unable to make sticky in Edit Mode");
		return;
	}
	base= FIRSTBASE;
	while(base) {
		if TESTBASELIB(base) {
			if(base->object->type==OB_MESH) {
				ob= base->object;
				
				me= ob->data;
				mvert= me->mvert;
				if(me->msticky) MEM_freeN(me->msticky);
				me->msticky= MEM_mallocN(me->totvert*sizeof(MSticky), "sticky");
				
				/* like convert to render data */		
				R.r= G.scene->r;
				R.r.xsch= (R.r.size*R.r.xsch)/100;
				R.r.ysch= (R.r.size*R.r.ysch)/100;
				
				R.afmx= R.r.xsch/2;
				R.afmy= R.r.ysch/2;
				
				R.ycor= ( (float)R.r.yasp)/( (float)R.r.xasp);
		
				R.rectx= R.r.xsch; 
				R.recty= R.r.ysch;
				R.xstart= -R.afmx; 
				R.ystart= -R.afmy;
				R.xend= R.xstart+R.rectx-1;
				R.yend= R.ystart+R.recty-1;
		
				where_is_object(G.scene->camera);
				Mat4CpyMat4(R.viewinv, G.scene->camera->obmat);
				Mat4Ortho(R.viewinv);
				Mat4Invert(R.viewmat, R.viewinv);
				
				RE_setwindowclip(1, -1);
		
				where_is_object(ob);
				Mat4MulMat4(mat, ob->obmat, R.viewmat);
		
				ms= me->msticky;
				for(a=0; a<me->totvert; a++, ms++, mvert++) {
					VECCOPY(ho, mvert->co);
					Mat4MulVecfl(mat, ho);
					RE_projectverto(ho, ho);
					ms->co[0]= ho[0]/ho[3];
					ms->co[1]= ho[1]/ho[3];
				}
			}
		}
		base= base->next;
	}
	allqueue(REDRAWBUTSEDIT, 0);
}

void fasterdraw(void)
{
	Base *base;
	Mesh *me;
	MFace *mface;
	int toggle, a;

	if(G.obedit) return;

	/* reset flags */
	me= G.main->mesh.first;
	while(me) {
		me->flag &= ~ME_ISDONE;
		me= me->id.next;
	}

	base= FIRSTBASE;
	while(base) {
		if( TESTBASELIB(base) && (base->object->type==OB_MESH)) {
			me= base->object->data;
			if(me->id.lib==0 && (me->flag & ME_ISDONE)==0) {
				me->flag |= ME_ISDONE;
				mface= me->mface;
				toggle= 0;
				for(a=0; a<me->totface; a++) {
					if( (mface->edcode & ME_V1V2) && ( (toggle++) & 1) ) {
						mface->edcode-= ME_V1V2;
					}
					if( (mface->edcode & ME_V2V3) && ( (toggle++) & 1)) {
						mface->edcode-= ME_V2V3;
					}
					if( (mface->edcode & ME_V3V1) && ( (toggle++) & 1)) {
						mface->edcode-= ME_V3V1;
					}
					if( (mface->edcode & ME_V4V1) && ( (toggle++) & 1)) {
						mface->edcode-= ME_V4V1;
					}
					if( (mface->edcode & ME_V3V4) && ( (toggle++) & 1)) {
						mface->edcode-= ME_V3V4;
					}
					mface++;
				}
			}
		}
		base= base->next;
	}

	/* important?: reset flags again */
	me= G.main->mesh.first;
	while(me) {
		me->flag &= ~ME_ISDONE;
		me= me->id.next;
	}

	allqueue(REDRAWVIEW3D, 0);
}

void slowerdraw(void)		/* reset fasterdraw */
{
	Base *base;
	Mesh *me;
	MFace *mface;
	int a;

	if(G.obedit) return;

	base= FIRSTBASE;
	while(base) {
		if( TESTBASELIB(base) && (base->object->type==OB_MESH)) {
			me= base->object->data;
			if(me->id.lib==0) {
				
				mface= me->mface;
				
				for(a=0; a<me->totface; a++) {
				
					mface->edcode |= ME_V1V2|ME_V2V3;
					mface++;
				}
			}
		}
		base= base->next;
	}

	allqueue(REDRAWVIEW3D, 0);
}


void convert_to_triface(int all)
{
	EditMesh *em = G.editMesh;
	EditVlak *evl, *evln, *next;
	
	undo_push_mesh("Convert Quads to Triangles");
	
	evl= em->faces.first;
	while(evl) {
		next= evl->next;
		if(evl->v4) {
			if(all || vlakselectedAND(evl, 1) ) {
				
				evln= addvlaklist(evl->v1, evl->v2, evl->v3, 0, evl);
				evln= addvlaklist(evl->v1, evl->v3, evl->v4, 0, evl);

				evln->tf.uv[1][0]= evln->tf.uv[2][0];
				evln->tf.uv[1][1]= evln->tf.uv[2][1];
				evln->tf.uv[2][0]= evln->tf.uv[3][0];
				evln->tf.uv[2][1]= evln->tf.uv[3][1];
				
				evln->tf.col[1]= evln->tf.col[2];
				evln->tf.col[2]= evln->tf.col[3];
				
				BLI_remlink(&em->faces, evl);
				free_editvlak(evl);
			}
		}
		evl= next;
	}
	
}


void deselectall_mesh(void)	/* toggle */
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	int a;
	
	if(G.obedit->lay & G.vd->lay) {
		a= 0;
		eve= em->verts.first;
		while(eve) {
			if(eve->f & 1) {
				a= 1;
				break;
			}
			eve= eve->next;
		}
		
		if (a) undo_push_mesh("Deselect All");
		else undo_push_mesh("Select All");
		
		eve= em->verts.first;
		while(eve) {
			if(eve->h==0) {
				if(a) eve->f&= -2;
				else eve->f|= 1;
			}
			eve= eve->next;
		}
	}
	countall();
	allqueue(REDRAWVIEW3D, 0);
}


void righthandfaces(int select)	/* makes faces righthand turning */
{
	EditMesh *em = G.editMesh;
	EditEdge *eed, *ed1, *ed2, *ed3, *ed4;
	EditVlak *evl, *startvl;
	float maxx, nor[3], cent[3];
	int totsel, found, foundone, direct, turn, tria_nr;

   /* based at a select-connected to witness loose objects */

	/* count per edge the amount of faces */

	/* find the ultimate left, front, upper face (not manhattan dist!!) */
	/* also evaluate both triangle cases in quad, since these can be non-flat */

	/* put normal to the outside, and set the first direction flags in edges */

	/* then check the object, and set directions / direction-flags: but only for edges with 1 or 2 faces */
	/* this is in fact the 'select connected' */
	
	/* in case (selected) faces were not done: start over with 'find the ultimate ...' */

	waitcursor(1);
	
	eed= em->edges.first;
	while(eed) {
		eed->f= 0;
		eed->f1= 0;
		eed= eed->next;
	}

	/* count faces and edges */
	totsel= 0;
	evl= em->faces.first;
	while(evl) {
		if(select==0 || vlakselectedAND(evl, 1) ) {
			evl->f= 1;
			totsel++;
			evl->e1->f1++;
			evl->e2->f1++;
			evl->e3->f1++;
			if(evl->v4) evl->e4->f1++;
		}
		else evl->f= 0;

		evl= evl->next;
	}

	while(totsel>0) {
		/* from the outside to the inside */

		evl= em->faces.first;
		startvl= NULL;
		maxx= -1.0e10;
		tria_nr= 0;

		while(evl) {
			if(evl->f) {
				CalcCent3f(cent, evl->v1->co, evl->v2->co, evl->v3->co);
				cent[0]= cent[0]*cent[0] + cent[1]*cent[1] + cent[2]*cent[2];
				
				if(cent[0]>maxx) {
					maxx= cent[0];
					startvl= evl;
					tria_nr= 0;
				}
				if(evl->v4) {
					CalcCent3f(cent, evl->v1->co, evl->v3->co, evl->v4->co);
					cent[0]= cent[0]*cent[0] + cent[1]*cent[1] + cent[2]*cent[2];
					
					if(cent[0]>maxx) {
						maxx= cent[0];
						startvl= evl;
						tria_nr= 1;
					}
				}
			}
			evl= evl->next;
		}
		
		/* set first face correct: calc normal */
		
		if(tria_nr==1) {
			CalcNormFloat(startvl->v1->co, startvl->v3->co, startvl->v4->co, nor);
			CalcCent3f(cent, startvl->v1->co, startvl->v3->co, startvl->v4->co);
		} else {
			CalcNormFloat(startvl->v1->co, startvl->v2->co, startvl->v3->co, nor);
			CalcCent3f(cent, startvl->v1->co, startvl->v2->co, startvl->v3->co);
		}
		/* first normal is oriented this way or the other */
		if(select) {
			if(select==2) {
				if(cent[0]*nor[0]+cent[1]*nor[1]+cent[2]*nor[2] > 0.0) flipvlak(startvl);
			}
			else {
				if(cent[0]*nor[0]+cent[1]*nor[1]+cent[2]*nor[2] < 0.0) flipvlak(startvl);
			}
		}
		else if(cent[0]*nor[0]+cent[1]*nor[1]+cent[2]*nor[2] < 0.0) flipvlak(startvl);


		eed= startvl->e1;
		if(eed->v1==startvl->v1) eed->f= 1; 
		else eed->f= 2;
		
		eed= startvl->e2;
		if(eed->v1==startvl->v2) eed->f= 1; 
		else eed->f= 2;
		
		eed= startvl->e3;
		if(eed->v1==startvl->v3) eed->f= 1; 
		else eed->f= 2;
		
		eed= startvl->e4;
		if(eed) {
			if(eed->v1==startvl->v4) eed->f= 1; 
			else eed->f= 2;
		}
		
		startvl->f= 0;
		totsel--;

		/* test normals */
		found= 1;
		direct= 1;
		while(found) {
			found= 0;
			if(direct) evl= em->faces.first;
			else evl= em->faces.last;
			while(evl) {
				if(evl->f) {
					turn= 0;
					foundone= 0;

					ed1= evl->e1;
					ed2= evl->e2;
					ed3= evl->e3;
					ed4= evl->e4;

					if(ed1->f) {
						if(ed1->v1==evl->v1 && ed1->f==1) turn= 1;
						if(ed1->v2==evl->v1 && ed1->f==2) turn= 1;
						foundone= 1;
					}
					else if(ed2->f) {
						if(ed2->v1==evl->v2 && ed2->f==1) turn= 1;
						if(ed2->v2==evl->v2 && ed2->f==2) turn= 1;
						foundone= 1;
					}
					else if(ed3->f) {
						if(ed3->v1==evl->v3 && ed3->f==1) turn= 1;
						if(ed3->v2==evl->v3 && ed3->f==2) turn= 1;
						foundone= 1;
					}
					else if(ed4 && ed4->f) {
						if(ed4->v1==evl->v4 && ed4->f==1) turn= 1;
						if(ed4->v2==evl->v4 && ed4->f==2) turn= 1;
						foundone= 1;
					}

					if(foundone) {
						found= 1;
						totsel--;
						evl->f= 0;

						if(turn) {
							if(ed1->v1==evl->v1) ed1->f= 2; 
							else ed1->f= 1;
							if(ed2->v1==evl->v2) ed2->f= 2; 
							else ed2->f= 1;
							if(ed3->v1==evl->v3) ed3->f= 2; 
							else ed3->f= 1;
							if(ed4) {
								if(ed4->v1==evl->v4) ed4->f= 2; 
								else ed4->f= 1;
							}

							flipvlak(evl);

						}
						else {
							if(ed1->v1== evl->v1) ed1->f= 1; 
							else ed1->f= 2;
							if(ed2->v1==evl->v2) ed2->f= 1; 
							else ed2->f= 2;
							if(ed3->v1==evl->v3) ed3->f= 1; 
							else ed3->f= 2;
							if(ed4) {
								if(ed4->v1==evl->v4) ed4->f= 1; 
								else ed4->f= 2;
							}
						}
					}
				}
				if(direct) evl= evl->next;
				else evl= evl->prev;
			}
			direct= 1-direct;
		}
	}

	recalc_editnormals();
	
	makeDispList(G.obedit);
	
	waitcursor(0);
}

static EditVert *findnearestvert(short sel)
{
	EditMesh *em = G.editMesh;
	/* if sel==1 the vertices with flag==1 get a disadvantage */
	EditVert *eve,*act=0;
	static EditVert *acto=0;
	short dist=100,temp,mval[2];

	if(em->verts.first==0) return 0;

	/* do projection */
	calc_meshverts_ext();	/* drawobject.c */
	
	/* we count from acto->next to last, and from first to acto */
	/* does acto exist? */
	eve= em->verts.first;
	while(eve) {
		if(eve==acto) break;
		eve= eve->next;
	}
	if(eve==0) acto= em->verts.first;

	if(acto==0) return 0;

	/* is there an indicated vertex? part 1 */
	getmouseco_areawin(mval);
	eve= acto->next;
	while(eve) {
		if(eve->h==0) {
			temp= abs(mval[0]- eve->xs)+ abs(mval[1]- eve->ys);
			if( (eve->f & 1)==sel ) temp+=5;
			if(temp<dist) {
				act= eve;
				dist= temp;
				if(dist<4) break;
			}
		}
		eve= eve->next;
	}
	/* is there an indicated vertex? part 2 */
	if(dist>3) {
		eve= em->verts.first;
		while(eve) {
			if(eve->h==0) {
				temp= abs(mval[0]- eve->xs)+ abs(mval[1]- eve->ys);
				if( (eve->f & 1)==sel ) temp+=5;
				if(temp<dist) {
					act= eve;
					if(temp<4) break;
					dist= temp;
				}
				if(eve== acto) break;
			}
			eve= eve->next;
		}
	}

	acto= act;
	return act;
}


static EditEdge *findnearestedge()
{
	EditMesh *em = G.editMesh;
	EditEdge *closest, *eed;
	EditVert *eve;
	short found=0, mval[2];
	float distance[2], v1[2], v2[2], mval2[2];
	
	if(em->edges.first==0) return NULL;
	else eed=em->edges.first;	
	
	/* reset flags */	
	for(eve=em->verts.first; eve; eve=eve->next){
		eve->f &= ~2;
	}	
		
	calc_meshverts_ext_f2();     	/*sets (eve->f & 2) for vertices that aren't visible*/
	getmouseco_areawin(mval);
	closest=NULL;
	
	mval2[0] = (float)mval[0];
	mval2[1] = (float)mval[1];
	
	eed=em->edges.first;
	/*compare the distance to the rest of the edges and find the closest one*/
	while(eed) {
		/* Are both vertices of the edge ofscreen or either of them hidden? then don't select the edge*/
		if( !((eed->v1->f & 2) && (eed->v2->f & 2)) && (eed->v1->h==0 && eed->v2->h==0)){
			v1[0] = eed->v1->xs;
			v1[1] = eed->v1->ys;
			v2[0] = eed->v2->xs;
			v2[1] = eed->v2->ys;
			
			distance[1] = PdistVL2Dfl(mval2, v1, v2);
			
			if(distance[1]<50){
				/*do we have to compare it to other distances? */    			
				if(found) {
					if (distance[1]<distance[0]){
						distance[0]=distance[1];
						/*save the current closest edge*/
						closest=eed;  	
					}
				} else {
					distance[0]=distance[1];
					closest=eed;
					found=1;
				}
			}
		}
		eed= eed->next;
	}
	
	/* reset flags */	
	for(eve=em->verts.first; eve; eve=eve->next){
		eve->f &= ~2;
	}
	
	if(found) return closest;
	else return 0;
}

/* does the same as findnearestedge but both vertices of the edge should be on screen*/
static EditEdge *findnearestvisibleedge()
{
	EditMesh *em = G.editMesh;
	EditEdge *closest, *eed;
	EditVert *eve;
	short found=0, mval[2];
	float distance[2], v1[2], v2[2], mval2[2];
		
	if(em->edges.first==0) return NULL;
	else eed=em->edges.first;	
	
	/* reset flags */	
	for(eve=em->verts.first; eve; eve=eve->next){
		eve->f &= ~2;
	}	
	calc_meshverts_ext_f2();     	/*sets (eve->f & 2) for vertices that aren't visible*/
	
	closest=NULL;
	getmouseco_areawin(mval);
	
	mval2[0] = (float)mval[0];    	/* cast to float because of the pdist function only taking floats...*/
	mval2[1] = (float)mval[1];
	
	eed=em->edges.first;
	while(eed) {      					/* compare the distance to the rest of the edges and find the closest one*/
		if( !((eed->v1->f | eed->v2->f) & 2) && (eed->v1->h==0 && eed->v2->h==0) ){ 	/* only return edges with both vertices on screen */
			v1[0] = eed->v1->xs;  			
			v1[1] = eed->v1->ys;
			v2[0] = eed->v2->xs;
			v2[1] = eed->v2->ys;
			
			distance[1] = PdistVL2Dfl(mval2, v1, v2);
			
			if(distance[1]<50){    			/* TODO: make this maximum selecting distance selectable (the same with vertice select?) */
				if(found) {              	/*do we have to compare it to other distances? */
					if (distance[1]<distance[0]){
						distance[0]=distance[1];
						closest=eed;  	/*save the current closest edge*/
					}
				} else {
					distance[0]=distance[1];
					closest=eed;
					found=1;
				}
			}
		}
		eed= eed->next;
	}
	
	/* reset flags */	
	for(eve=em->verts.first; eve; eve=eve->next){
		eve->f &= ~2;
	}
	
	if(found) return closest;
	else return 0;
}

#if 0
/* this is a template function to demonstrate a loop with drawing...
   it is a temporal mode, so use with wisdom! if you can avoid, always better. (ton)
*/
void loop(int mode)
{
	EditEdge *eed;
	int mousemove= 1;

	while(mousemove) {
		/* uses callback mechanism to draw it all in current area */
		scrarea_do_windraw(curarea); 
		
		/* do your stuff */
		eed= findnearestedge();
		
		/* set window matrix to perspective, default an area returns with buttons transform */
		persp(PERSP_VIEW);
		/* make a copy, for safety */
		glPushMatrix();
		/* multiply with the object transformation */
		mymultmatrix(G.obedit->obmat);
		
		/* draw */
		if(eed) {
			glColor3ub(255, 255, 0);
			glBegin(GL_LINES);
			glVertex3fv(eed->v1->co);
			glVertex3fv(eed->v2->co);
			glEnd();
		}
		
		/* restore matrix transform */
		glPopMatrix();
		
		headerprint("We are now in evil edge select mode. Press any key to exit");
		
		/* this also verifies other area/windows for clean swap */
		screen_swapbuffers();
		
		/* testing for user input... */
		while(qtest()) {
			unsigned short val;
			short event= extern_qread(&val);	// extern_qread stores important events for the mainloop to handle 

			/* val==0 on key-release event */
			if(val && event!=MOUSEY && event!=MOUSEX) {
				mousemove= 0;
			}
		}
		/* sleep 0.01 second to prevent overload in this poor loop */
		PIL_sleep_ms(10);	
		
	}
	
	/* send event to redraw this window, does header too */
	addqueue(curarea->win, REDRAW, 1); 
}
#endif

/* 
functionality: various loop functions
parameters: mode tells the function what it should do with the loop:
		LOOP_SELECT = select
		LOOP_CUT = cut in half
*/	

void loopoperations(char mode)
{
	EditMesh *em = G.editMesh;
	EditVert* look = NULL;

	EditEdge *start, *eed, *opposite,*currente, *oldstart;
	EditEdge **tagged = NULL,**taggedsrch = NULL,*close;

	EditVlak *evl,**percentfacesloop = NULL, *currentvl,  *formervl;	

	short lastface=0, foundedge=0, c=0, tri=0, side=1, totface=0, searching=1, event=0, noface=1;
	short skip,nextpos,percentfaces;

	int i=0,ect=0,j=0,k=0,cut,smooth,timesthrough=0,inset = 0;

	float percentcut, outcut;

	char mesg[100];

	if ((G.obedit==0) || (em->faces.first==0)) return;
	
	if(mode==LOOP_CUT)undo_push_mesh("Face Loop Subdivide");
	else if(mode==LOOP_SELECT)undo_push_mesh("Select Face Loop");	

	SetBlenderCursor(BC_VLOOPCURSOR);

	start=NULL;
	oldstart=NULL;

	while(searching){
		
		/* reset variables */
		start=eed=opposite=currente=0;
		evl=currentvl=formervl=0;
		side=noface=1;
		lastface=foundedge=c=tri=totface=0;		
				
		start=findnearestvisibleedge();
				
		/* If the edge doesn't belong to a face, it's not a valid starting edge */
		if(start){
			start->f |= 16;
			evl=em->faces.first;
			while(evl){
				if(evl->e1->f & 16){					
					noface=0;
					evl->e1->f &= ~16;
				}
				else if(evl->e2->f & 16){					
					noface=0;
					evl->e2->f &= ~16;
				}
				else if(evl->e3->f & 16){					
					noface=0;
					evl->e3->f &= ~16;
				}
				else if(evl->e4 && (evl->e4->f & 16)){					
					noface=0;
					evl->e4->f &= ~16;
				}
				
				evl=evl->next;
			}			
		}				
				
		/* Did we find anything that is selectable? */
		if(start && !noface && (oldstart==NULL || start!=oldstart)){
					
			/* If we stay in the neighbourhood of this edge, we don't have to recalculate the loop everytime*/
			oldstart=start;	
			
			/* Clear flags */
			for(eed=em->edges.first; eed; eed=eed->next){			
				eed->f &= ~(2|4|8|32|64);
				eed->v1->f &= ~(2|8|16);
				eed->v2->f &= ~(2|8|16);				
			}
			
			for(evl= em->faces.first; evl; evl=evl->next){			
				evl->f &= ~(4|8);
				totface++;				
			}
					
			/* Tag the starting edge */
			start->f |= (2|4|8|64);				
			start->v1->f |= 2;
			start->v2->f |= 2;		
			
			currente=start;						
			
			/*-----Limit the Search----- */
			while(!lastface && c<totface+1){
				
				/*----------Get Loop------------------------*/
				tri=foundedge=lastface=0;													
				evl= em->faces.first;		
				while(evl && !foundedge && !tri){
									
					if(!(evl->v4)){	/* Exception for triangular faces */
						
						if((evl->e1->f | evl->e2->f | evl->e3->f) & 2){
							if(!(evl->f & 4)){								
								tri=1;
								currentvl=evl;
								if(side==1) evl->f |= 4;
							}
						}						
					}
					else{
						
						if((evl->e1->f | evl->e2->f | evl->e3->f | evl->e4->f) & 2){
							
							if(c==0){	/* just pick a face, doesn't matter wich side of the edge we go to */
								if(!(evl->f & 4)){
									
									if(!(evl->e1->v1->f & 2) && !(evl->e1->v2->f & 2)){
										if(evl->e1->v1->h==0 && evl->e1->v2->h==0){
											opposite=evl->e1;														
											foundedge=1;
										}
									}
									else if(!(evl->e2->v1->f & 2) && !(evl->e2->v2->f & 2)){
										if(evl->e2->v1->h==0 && evl->e2->v2->h==0){
											opposite=evl->e2;
											foundedge=1;
										}
									}
									else if(!(evl->e3->v1->f & 2) && !(evl->e3->v2->f & 2)){
										if(evl->e3->v1->h==0 && evl->e3->v2->h==0){
											opposite=evl->e3;
											foundedge=1;
										}
									}
									else if(!(evl->e4->v1->f & 2) && !(evl->e4->v2->f & 2)){
										if(evl->e4->v1->h==0 && evl->e4->v2->h==0){
											opposite=evl->e4;
											foundedge=1;
										}
									}
									
									if(foundedge){
										currentvl=evl;
										formervl=evl;
									
										/* mark this side of the edge so we know in which direction we went */
										if(side==1) evl->f |= 4;
									}
								}
							}
							else {	
								if(evl!=formervl){	/* prevent going backwards in the loop */
								
									if(!(evl->e1->v1->f & 2) && !(evl->e1->v2->f & 2)){
										if(evl->e1->v1->h==0 && evl->e1->v2->h==0){
											opposite=evl->e1;														
											foundedge=1;
										}
									}
									else if(!(evl->e2->v1->f & 2) && !(evl->e2->v2->f & 2)){
										if(evl->e2->v1->h==0 && evl->e2->v2->h==0){
											opposite=evl->e2;
											foundedge=1;
										}
									}
									else if(!(evl->e3->v1->f & 2) && !(evl->e3->v2->f & 2)){
										if(evl->e3->v1->h==0 && evl->e3->v2->h==0){
											opposite=evl->e3;
											foundedge=1;
										}
									}
									else if(!(evl->e4->v1->f & 2) && !(evl->e4->v2->f & 2)){
										if(evl->e4->v1->h==0 && evl->e4->v2->h==0){
											opposite=evl->e4;
											foundedge=1;
										}
									}
									
									currentvl=evl;
								}
							}
						}
					}
				evl=evl->next;
				}
				/*----------END Get Loop------------------------*/
				
			
				/*----------Decisions-----------------------------*/
				if(foundedge){
					/* mark the edge and face as done */					
					currente->f |= 8;
					currentvl->f |= 8;

					if(opposite->f & 4) lastface=1;	/* found the starting edge! close loop */								
					else{
						/* un-set the testflags */
						currente->f &= ~2;
						currente->v1->f &= ~2;
						currente->v2->f &= ~2;							
						
						/* set the opposite edge to be the current edge */				
						currente=opposite;							
						
						/* set the current face to be the FORMER face (to prevent going backwards in the loop) */
						formervl=currentvl;
						
						/* set the testflags */
						currente->f |= 2;
						currente->v1->f |= 2;
						currente->v2->f |= 2;			
					}
					c++;
				}
				else{	
					/* un-set the testflags */
					currente->f &= ~2;
					currente->v1->f &= ~2;
					currente->v2->f &= ~2;
					
					/* mark the edge and face as done */
					currente->f |= 8;
					currentvl->f |= 8;
					
					
												
					/* is the the first time we've ran out of possible faces?
					*  try to start from the beginning but in the opposite direction go as far as possible
					*/				
					if(side==1){						
						if(tri)tri=0;
						currente=start;
						currente->f |= 2;
						currente->v1->f |= 2;
						currente->v2->f |= 2;					
						side++;
						c=0;
					}
					else lastface=1;
				}				
				/*----------END Decisions-----------------------------*/
				
			}
			/*-----END Limit the Search----- */
			
			
			/*------------- Preview lines--------------- */
			
			/* uses callback mechanism to draw it all in current area */
			scrarea_do_windraw(curarea);			
			
			/* set window matrix to perspective, default an area returns with buttons transform */
			persp(PERSP_VIEW);
			/* make a copy, for safety */
			glPushMatrix();
			/* multiply with the object transformation */
			mymultmatrix(G.obedit->obmat);
			
			glColor3ub(255, 255, 0);
			
			if(mode==LOOP_SELECT){
				evl= em->faces.first;
				while(evl){
					if(evl->f & 8){
						
						if(!(evl->e1->f & 8)){
							glBegin(GL_LINES);							
							glVertex3fv(evl->e1->v1->co);
							glVertex3fv(evl->e1->v2->co);
							glEnd();	
						}
						
						if(!(evl->e2->f & 8)){
							glBegin(GL_LINES);							
							glVertex3fv(evl->e2->v1->co);
							glVertex3fv(evl->e2->v2->co);
							glEnd();	
						}
						
						if(!(evl->e3->f & 8)){
							glBegin(GL_LINES);							
							glVertex3fv(evl->e3->v1->co);
							glVertex3fv(evl->e3->v2->co);
							glEnd();	
						}
						
						if(evl->e4){
							if(!(evl->e4->f & 8)){
								glBegin(GL_LINES);							
								glVertex3fv(evl->e4->v1->co);
								glVertex3fv(evl->e4->v2->co);
								glEnd();	
							}
						}
					}
					evl=evl->next;
				}
			}
				
			if(mode==LOOP_CUT){
				evl= em->faces.first;
				while(evl){
					if(evl->f & 8){
						float cen[2][3];
						int a=0;						
						
						evl->v1->f &= ~8;
						evl->v2->f &= ~8;
						evl->v3->f &= ~8;
						if(evl->v4)evl->v4->f &= ~8;
					
						if(evl->e1->f & 8){
							cen[a][0]= (evl->e1->v1->co[0] + evl->e1->v2->co[0])/2.0;
							cen[a][1]= (evl->e1->v1->co[1] + evl->e1->v2->co[1])/2.0;
							cen[a][2]= (evl->e1->v1->co[2] + evl->e1->v2->co[2])/2.0;
							
							evl->e1->v1->f |= 8;
							evl->e1->v2->f |= 8;
							
							a++;
						}
						if((evl->e2->f & 8) && a!=2){
							cen[a][0]= (evl->e2->v1->co[0] + evl->e2->v2->co[0])/2.0;
							cen[a][1]= (evl->e2->v1->co[1] + evl->e2->v2->co[1])/2.0;
							cen[a][2]= (evl->e2->v1->co[2] + evl->e2->v2->co[2])/2.0;
							
							evl->e2->v1->f |= 8;
							evl->e2->v2->f |= 8;
							
							a++;
						}
						if((evl->e3->f & 8) && a!=2){
							cen[a][0]= (evl->e3->v1->co[0] + evl->e3->v2->co[0])/2.0;
							cen[a][1]= (evl->e3->v1->co[1] + evl->e3->v2->co[1])/2.0;
							cen[a][2]= (evl->e3->v1->co[2] + evl->e3->v2->co[2])/2.0;
							
							evl->e3->v1->f |= 8;
							evl->e3->v2->f |= 8;
							
							a++;
						}
						
						if(evl->e4){
							if((evl->e4->f & 8) && a!=2){
								cen[a][0]= (evl->e4->v1->co[0] + evl->e4->v2->co[0])/2.0;
								cen[a][1]= (evl->e4->v1->co[1] + evl->e4->v2->co[1])/2.0;
								cen[a][2]= (evl->e4->v1->co[2] + evl->e4->v2->co[2])/2.0;
								
								evl->e4->v1->f |= 8;
								evl->e4->v2->f |= 8;
							
								a++;
							}
						}
						else{	/* if it's a triangular face, set the remaining vertex as the cutcurve coordinate */														
								if(!(evl->v1->f & 8) && evl->v1->h==0){
									cen[a][0]= evl->v1->co[0];
									cen[a][1]= evl->v1->co[1];
									cen[a][2]= evl->v1->co[2];
									a++;								
								}
								else if(!(evl->v2->f & 8) && evl->v2->h==0){
									cen[a][0]= evl->v2->co[0];
									cen[a][1]= evl->v2->co[1];
									cen[a][2]= evl->v2->co[2];	
									a++;
								}
								else if(!(evl->v3->f & 8) && evl->v3->h==0){
									cen[a][0]= evl->v3->co[0];
									cen[a][1]= evl->v3->co[1];
									cen[a][2]= evl->v3->co[2];
									a++;									
								}							
						}
						
						if(a==2){
							glBegin(GL_LINES);
							
							glVertex3fv(cen[0]);
							glVertex3fv(cen[1]);	
												
							glEnd();
						}						
					}
					evl=evl->next;
				}
				
				eed=em->edges.first; 
				while(eed){
					if(eed->f & 64){
						glBegin(GL_LINES);
						glColor3ub(200, 255, 200);
						glVertex3fv(eed->v1->co);
						glVertex3fv(eed->v2->co);
						glEnd();
						eed=0;
					}else{
						eed = eed->next;
					}
				}		
			}
			
			/* restore matrix transform */
			glPopMatrix();
			
			headerprint("LMB to confirm, RMB to cancel");
			
			/* this also verifies other area/windows for clean swap */
			screen_swapbuffers();
			
			/*--------- END Preview Lines------------*/
				
		}/*if(start!=NULL){ */
		
		while(qtest()) {
			unsigned short val=0;			
			event= extern_qread(&val);	/* extern_qread stores important events for the mainloop to handle */

			/* val==0 on key-release event */
			if(val && (event==ESCKEY || event==RIGHTMOUSE || event==LEFTMOUSE || event==RETKEY || event == MIDDLEMOUSE)){
				searching=0;
			}
		}	
		
	}/*while(event!=ESCKEY && event!=RIGHTMOUSE && event!=LEFTMOUSE && event!=RETKEY){*/
	
	/*----------Select Loop------------*/
	if(mode==LOOP_SELECT && start!=NULL && ((event==LEFTMOUSE || event==RETKEY) || event == MIDDLEMOUSE || event == BKEY)){
				
		/* If this is a unmodified select, clear the selection */
		if(!(G.qual & LR_SHIFTKEY) && !(G.qual & LR_ALTKEY)){
			for(evl= em->faces.first;evl;evl=evl->next){
				evl->v1->f &= !1;
				evl->v2->f &= !1;
				evl->v3->f &= !1;
				if(evl->v4)evl->v4->f &= !1;			
			}
		}
		/* Alt was not pressed, so add to the selection */
		if(!(G.qual & LR_ALTKEY)){
			for(evl= em->faces.first;evl;evl=evl->next){
				if(evl->f & 8){
					evl->v1->f |= 1;
					evl->v2->f |= 1;
					evl->v3->f |= 1;
					if(evl->v4)evl->v4->f |= 1;
				}
			}
		}
		/* alt was pressed, so subtract from the selection */
		else
		{
			for(evl= em->faces.first;evl;evl=evl->next){
				if(evl->f & 8){
					evl->v1->f &= !1;
					evl->v2->f &= !1;
					evl->v3->f &= !1;
					if(evl->v4)evl->v4->f &= !1;
				}
			}
		}
	
	}
	/*----------END Select Loop------------*/
	
	/*----------Cut Loop---------------*/			
	if(mode==LOOP_CUT && start!=NULL && (event==LEFTMOUSE || event==RETKEY)){
		
		/* count the number of edges in the loop */		
		for(eed=em->edges.first; eed; eed = eed->next){
			if(eed->f & 8)
				ect++;
		}		
		
		tagged = MEM_mallocN(ect*sizeof(EditEdge*), "tagged");
		taggedsrch = MEM_mallocN(ect*sizeof(EditEdge*), "taggedsrch");
		for(i=0;i<ect;i++)
		{
			tagged[i] = NULL;
			taggedsrch[i] = NULL;
		}
		ect = 0;
		for(eed=em->edges.first; eed; eed = eed->next){
			if(eed->f & 8)
			{
				if(eed->h==0){
					eed->v1->f |= 1;
					eed->v2->f |= 1;
					tagged[ect] = eed;
					eed->f &= ~(32);
					ect++;
				}
			}			
		}
		taggedsrch[0] = tagged[0];

		while(timesthrough < 2)
		{
			i=0;
			while(i < ect){/*Look at the members of the search array to line up cuts*/
				if(taggedsrch[i]==NULL)break;
				for(j=0;j<ect;j++){			 /*Look through the list of tagged verts for connected edges*/
					int addededge = 0;
					if(taggedsrch[i]->f & 32)        /*If this edgee is marked as flipped, use vert 2*/
						look = taggedsrch[i]->v2;
					else							 /*else use vert 1*/
						look = taggedsrch[i]->v1;

					if(taggedsrch[i] == tagged[j])
						continue;  /*If we are looking at the same edge, skip it*/
	
					skip = 0;
					for(k=0;k<ect;k++)	{
						if(taggedsrch[k] == NULL)	/*go to empty part of search list without finding*/
							break;							
						if(tagged[j] == taggedsrch[k]){		/*We found a match already in the list*/
							skip = 1;
							break;
						}
					}
					if(skip)
						continue;
					nextpos = 0;
					if(findedgelist(look,tagged[j]->v2)){
						while(nextpos < ect){ /*Find the first open spot in the search array*/
							if(taggedsrch[nextpos] == NULL){
								taggedsrch[nextpos] = tagged[j]; /*put tagged[j] in it*/
								taggedsrch[nextpos]->f |= 32;
								addededge = 1;
								break;
							}
							else
								nextpos++;
						}
					} /* End else if connected to vert 2*/
					else if(findedgelist(look,tagged[j]->v1)){   /*If our vert is connected to vert 1 */
						while(nextpos < ect){ /*Find the first open spot in the search array */
							if(taggedsrch[nextpos] == NULL){
								taggedsrch[nextpos] = tagged[j]; /*put tagged[j] in it*/
								addededge = 1;
								break;
							}
							else 
								nextpos++;
						}
					}

					if(addededge)
					{
						break;
					}					
				}/* End Outer For (j)*/
				i++;
			} /* End while(j<ect)*/
			timesthrough++;
		} /*end while timesthrough */
		percentcut = 0.50;
		searching = 1;
		cut   = 1;
		smooth = 0;
		close = NULL;


		/* Count the Number of Faces in the selected loop*/
		percentfaces = 0;
		for(evl= em->faces.first; evl ;evl=evl->next){
			if(evl->f & 8)
			 {
				percentfaces++;	
			 }
		}
			
		/* create a dynamic array for those face pointers */
		percentfacesloop = MEM_mallocN(percentfaces*sizeof(EditVlak*), "percentage");

		/* put those faces in the array */
		i=0;
		for(evl= em->faces.first; evl ;evl=evl->next){
			 if(evl->f & 8)
			 {
				percentfacesloop[i] = evl;	
				i++;
			 }
		}

		while(searching){
			
			/* For the % calculation */
			short mval[2];			
			float labda, rc[2], len, slen=0.0;
			float v1[2], v2[2], v3[2];

			/*------------- Percent Cut Preview Lines--------------- */
			scrarea_do_windraw(curarea);			
			persp(PERSP_VIEW);
			glPushMatrix();
			mymultmatrix(G.obedit->obmat);
			glColor3ub(0, 255, 255);
				
			/*Put the preview lines where they should be for the percentage selected.*/

			for(i=0;i<percentfaces;i++){
				evl = percentfacesloop[i];
				for(eed = em->edges.first; eed; eed=eed->next){
					if(eed->f & 64){	/* color the starting edge */			
						glBegin(GL_LINES);
												
						glColor3ub(200, 255, 200);
						glVertex3fv(eed->v1->co);					
						glVertex3fv(eed->v2->co);
						
						glEnd();

						glPointSize(5);
						glBegin(GL_POINTS);
						glColor3ub(255,0,255);
						
						if(eed->f & 32)
							glVertex3fv(eed->v2->co);			
						else
							glVertex3fv(eed->v1->co);
						glEnd();


						/*Get Starting Edge Length*/
						slen = sqrt((eed->v1->co[0]-eed->v2->co[0])*(eed->v1->co[0]-eed->v2->co[0])+
									(eed->v1->co[1]-eed->v2->co[1])*(eed->v1->co[1]-eed->v2->co[1])+
									(eed->v1->co[2]-eed->v2->co[2])*(eed->v1->co[2]-eed->v2->co[2]));
					}
				}
				
				if(!inset){
					glColor3ub(0,255,255);
					if(evl->f & 8)
					{
						float cen[2][3];
						int a=0;					
						
						evl->v1->f &= ~8;
						evl->v2->f &= ~8;
						evl->v3->f &= ~8;
						if(evl->v4)evl->v4->f &= ~8;
						
						if(evl->e1->f & 8){
							float pct;
							if(evl->e1->f & 32)
								pct = 1-percentcut;
							else
								pct = percentcut;
							cen[a][0]= evl->e1->v1->co[0] - ((evl->e1->v1->co[0] - evl->e1->v2->co[0]) * (pct));
							cen[a][1]= evl->e1->v1->co[1] - ((evl->e1->v1->co[1] - evl->e1->v2->co[1]) * (pct));
							cen[a][2]= evl->e1->v1->co[2] - ((evl->e1->v1->co[2] - evl->e1->v2->co[2]) * (pct));
							evl->e1->v1->f |= 8;
							evl->e1->v2->f |= 8;
							a++;
						}
						if((evl->e2->f & 8) && a!=2)
						{
							float pct;
							if(evl->e2->f & 32)
								pct = 1-percentcut;
							else
								pct = percentcut;
							cen[a][0]= evl->e2->v1->co[0] - ((evl->e2->v1->co[0] - evl->e2->v2->co[0]) * (pct));
							cen[a][1]= evl->e2->v1->co[1] - ((evl->e2->v1->co[1] - evl->e2->v2->co[1]) * (pct));
							cen[a][2]= evl->e2->v1->co[2] - ((evl->e2->v1->co[2] - evl->e2->v2->co[2]) * (pct));

							evl->e2->v1->f |= 8;
							evl->e2->v2->f |= 8;
							
							a++;
						}
						if((evl->e3->f & 8) && a!=2){
							float pct;
							if(evl->e3->f & 32)
								pct = 1-percentcut;
							else
								pct = percentcut;
							cen[a][0]= evl->e3->v1->co[0] - ((evl->e3->v1->co[0] - evl->e3->v2->co[0]) * (pct));
							cen[a][1]= evl->e3->v1->co[1] - ((evl->e3->v1->co[1] - evl->e3->v2->co[1]) * (pct));
							cen[a][2]= evl->e3->v1->co[2] - ((evl->e3->v1->co[2] - evl->e3->v2->co[2]) * (pct));

							evl->e3->v1->f |= 8;
							evl->e3->v2->f |= 8;
							
							a++;
						}
							
						if(evl->e4){
							if((evl->e4->f & 8) && a!=2){
								float pct;
								if(evl->e4->f & 32)
									pct = 1-percentcut;
								else
									pct = percentcut;
								cen[a][0]= evl->e4->v1->co[0] - ((evl->e4->v1->co[0] - evl->e4->v2->co[0]) * (pct));
								cen[a][1]= evl->e4->v1->co[1] - ((evl->e4->v1->co[1] - evl->e4->v2->co[1]) * (pct));
								cen[a][2]= evl->e4->v1->co[2] - ((evl->e4->v1->co[2] - evl->e4->v2->co[2]) * (pct));

								evl->e4->v1->f |= 8;
								evl->e4->v2->f |= 8;
							
								a++;
							}
						}
						else {	/* if it's a triangular face, set the remaining vertex as the cutcurve coordinate */
							if(!(evl->v1->f & 8) && evl->v1->h==0){
								cen[a][0]= evl->v1->co[0];
								cen[a][1]= evl->v1->co[1];
								cen[a][2]= evl->v1->co[2];
								a++;								
							}
							else if(!(evl->v2->f & 8) && evl->v2->h==0){
								cen[a][0]= evl->v2->co[0];
								cen[a][1]= evl->v2->co[1];
								cen[a][2]= evl->v2->co[2];
								a++;								
							}
							else if(!(evl->v3->f & 8) && evl->v3->h==0){
								cen[a][0]= evl->v3->co[0];
								cen[a][1]= evl->v3->co[1];
								cen[a][2]= evl->v3->co[2];
								a++;													
							}
						}
						
						if(a==2){
							glBegin(GL_LINES);
							
							glVertex3fv(cen[0]);
							glVertex3fv(cen[1]);	
												
							glEnd();
						}	
					}
				}/* end preview line drawing */			
				else{
					glColor3ub(0,128,255);
					if(evl->f & 8)
					{
						float cen[2][3];
						int a=0;					
						
						evl->v1->f &= ~8;
						evl->v2->f &= ~8;
						evl->v3->f &= ~8;
						if(evl->v4)evl->v4->f &= ~8;
						
						if(evl->e1->f & 8){							
							float nlen,npct;
							
							nlen = sqrt((evl->e1->v1->co[0] - evl->e1->v2->co[0])*(evl->e1->v1->co[0] - evl->e1->v2->co[0])+
										(evl->e1->v1->co[1] - evl->e1->v2->co[1])*(evl->e1->v1->co[1] - evl->e1->v2->co[1])+
										(evl->e1->v1->co[2] - evl->e1->v2->co[2])*(evl->e1->v1->co[2] - evl->e1->v2->co[2]));
							npct = (percentcut*slen)/nlen;
							if(npct >= 1) npct = 1;
							if(evl->e1->f & 32)	npct = 1-npct;

							cen[a][0]= evl->e1->v1->co[0] - ((evl->e1->v1->co[0] - evl->e1->v2->co[0]) * (npct));
							cen[a][1]= evl->e1->v1->co[1] - ((evl->e1->v1->co[1] - evl->e1->v2->co[1]) * (npct));
							cen[a][2]= evl->e1->v1->co[2] - ((evl->e1->v1->co[2] - evl->e1->v2->co[2]) * (npct));

							evl->e1->f1 = 32768*(npct);
							evl->e1->v1->f |= 8;
							evl->e1->v2->f |= 8;
							a++;
						}
						if((evl->e2->f & 8) && a!=2)
						{
							float nlen,npct;
							
							nlen = sqrt((evl->e2->v1->co[0] - evl->e2->v2->co[0])*(evl->e2->v1->co[0] - evl->e2->v2->co[0])+
										(evl->e2->v1->co[1] - evl->e2->v2->co[1])*(evl->e2->v1->co[1] - evl->e2->v2->co[1])+
										(evl->e2->v1->co[2] - evl->e2->v2->co[2])*(evl->e2->v1->co[2] - evl->e2->v2->co[2]));
							npct = (percentcut*slen)/nlen;
							if(npct >= 1) npct = 1;
							if(evl->e2->f & 32)	npct = 1-npct;

							cen[a][0]= evl->e2->v1->co[0] - ((evl->e2->v1->co[0] - evl->e2->v2->co[0]) * (npct));
							cen[a][1]= evl->e2->v1->co[1] - ((evl->e2->v1->co[1] - evl->e2->v2->co[1]) * (npct));
							cen[a][2]= evl->e2->v1->co[2] - ((evl->e2->v1->co[2] - evl->e2->v2->co[2]) * (npct));

							evl->e2->f1 = 32768*(npct);								
							evl->e2->v1->f |= 8;
							evl->e2->v2->f |= 8;
							a++;
						}
						if((evl->e3->f & 8) && a!=2){
							float nlen,npct;
							
							nlen = sqrt((evl->e3->v1->co[0] - evl->e3->v2->co[0])*(evl->e3->v1->co[0] - evl->e3->v2->co[0])+
										(evl->e3->v1->co[1] - evl->e3->v2->co[1])*(evl->e3->v1->co[1] - evl->e3->v2->co[1])+
										(evl->e3->v1->co[2] - evl->e3->v2->co[2])*(evl->e3->v1->co[2] - evl->e3->v2->co[2]));
							npct = (percentcut*slen)/nlen;
							if(npct >= 1) npct = 1;
							if(evl->e3->f & 32)	npct = 1-npct;

							cen[a][0]= evl->e3->v1->co[0] - ((evl->e3->v1->co[0] - evl->e3->v2->co[0]) * (npct));
							cen[a][1]= evl->e3->v1->co[1] - ((evl->e3->v1->co[1] - evl->e3->v2->co[1]) * (npct));
							cen[a][2]= evl->e3->v1->co[2] - ((evl->e3->v1->co[2] - evl->e3->v2->co[2]) * (npct));

							evl->e3->f1 = 32768*(npct);								
							evl->e3->v1->f |= 8;
							evl->e3->v2->f |= 8;
							a++;
						}
							
						if(evl->e4){
							if((evl->e4->f & 8) && a!=2){
								float nlen,npct;
								
								nlen = sqrt((evl->e4->v1->co[0] - evl->e4->v2->co[0])*(evl->e4->v1->co[0] - evl->e4->v2->co[0])+
											(evl->e4->v1->co[1] - evl->e4->v2->co[1])*(evl->e4->v1->co[1] - evl->e4->v2->co[1])+
											(evl->e4->v1->co[2] - evl->e4->v2->co[2])*(evl->e4->v1->co[2] - evl->e4->v2->co[2]));
							npct = (percentcut*slen)/nlen;
							if(npct >= 1) npct = 1;
							if(evl->e4->f & 32)	npct = 1-npct;

								cen[a][0]= evl->e4->v1->co[0] - ((evl->e4->v1->co[0] - evl->e4->v2->co[0]) * (npct));
								cen[a][1]= evl->e4->v1->co[1] - ((evl->e4->v1->co[1] - evl->e4->v2->co[1]) * (npct));
								cen[a][2]= evl->e4->v1->co[2] - ((evl->e4->v1->co[2] - evl->e4->v2->co[2]) * (npct));

								evl->e4->f1 = 32768*(npct);									
								evl->e4->v1->f |= 8;
								evl->e4->v2->f |= 8;
								a++;
							}
						}
						else {	/* if it's a triangular face, set the remaining vertex as the cutcurve coordinate */
							if(!(evl->v1->f & 8) && evl->v1->h==0){
								cen[a][0]= evl->v1->co[0];
								cen[a][1]= evl->v1->co[1];
								cen[a][2]= evl->v1->co[2];
								a++;								
							}
							else if(!(evl->v2->f & 8) && evl->v2->h==0){
								cen[a][0]= evl->v2->co[0];
								cen[a][1]= evl->v2->co[1];
								cen[a][2]= evl->v2->co[2];
								a++;								
							}
							else if(!(evl->v3->f & 8) && evl->v3->h==0){
								cen[a][0]= evl->v3->co[0];
								cen[a][1]= evl->v3->co[1];
								cen[a][2]= evl->v3->co[2];
								a++;													
							}
						}
						
						if(a==2){
							glBegin(GL_LINES);
							
							glVertex3fv(cen[0]);
							glVertex3fv(cen[1]);	
												
							glEnd();
						}	
					}
				}
			}
			/* restore matrix transform */
	
			glPopMatrix();

			/*--------- END Preview Lines------------*/
			while(qtest()) 
			{
				unsigned short val=0;			
				event= extern_qread(&val);	/* extern_qread stores important events for the mainloop to handle */
				/* val==0 on key-release event */
		
				if(val && (event==SKEY))
				{
					if(smooth)smooth = 0;
					else smooth = 1;
				}

				if(val && (event==PKEY))
				{
					if(inset)inset = 0;
					else inset = 1;
				}

				if(val && (event==FKEY))
				{
						int ct;
						for(ct = 0; ct < ect; ct++){
							if(tagged[ct]->f & 32) 
								tagged[ct]->f &= ~32;
							else
								tagged[ct]->f |= 32;
						}
				}

				if(val && (event == MIDDLEMOUSE))
				{
					cut = 2;
					searching=0;
				}
				else if(val && (event==LEFTMOUSE || event==RETKEY))
				{
					searching=0;
				}

				if(val && (event==ESCKEY || event==RIGHTMOUSE ))
				{
					searching=0;
					cut = 0;
				}
				
			}			
			

			/* Determine the % on wich the loop should be cut */
			getmouseco_areawin(mval);			
			v1[0]=(float)mval[0];
			v1[1]=(float)mval[1];
			
			v2[0]=(float)start->v1->xs;
			v2[1]=(float)start->v1->ys;
			
			v3[0]=(float)start->v2->xs;
			v3[1]=(float)start->v2->ys;
			
			rc[0]= v3[0]-v2[0];
			rc[1]= v3[1]-v2[1];
			len= rc[0]*rc[0]+ rc[1]*rc[1];
				
			labda= ( rc[0]*(v1[0]-v2[0]) + rc[1]*(v1[1]-v2[1]) )/len;


			if(labda<=0.0) labda=0.0;
			else if(labda>=1.0)labda=1.0;
						
			percentcut=labda;		
			
			if(start->f & 32)
				percentcut = 1.0-percentcut;

		if(cut == 2){
			percentcut = 0.5;
		}

		if (G.qual & LR_SHIFTKEY){

			percentcut = (int)(percentcut*100.0)/100.0;	
		}
		else if (G.qual & LR_CTRLKEY)
			percentcut = (int)(percentcut*10.0)/10.0;		
	
		outcut = (percentcut*100.0);

		/* Build the Header Line */ 

		if(inset)
			sprintf(mesg,"Cut: %0.2f%% ",slen*percentcut);
		else
			sprintf(mesg,"Cut: %0.2f%% ",outcut);
		

		if(smooth)
			sprintf(mesg,"%s| (f)lip side | (s)mooth on  |",mesg);
		else
			sprintf(mesg,"%s| (f)lip side | (s)mooth off |",mesg);

		if(inset)
			sprintf(mesg,"%s (p)roportional on ",mesg);
		else
			sprintf(mesg,"%s (p)roportional off",mesg);
		
		headerprint(mesg);

		screen_swapbuffers();		
	}			
	
	if(cut){
		/* Now that we have selected a cut %, mark the edges for cutting. */
		if(!inset){
			for(eed = em->edges.first; eed; eed=eed->next){		
			   		if(percentcut == 1.0)
						percentcut = 0.9999;
					else if(percentcut == 0.0)
						percentcut = 0.0001;
					if(eed->f & 8){
						if(eed->f & 32)/* Need to offset by a const. (0.5/32768) for consistant roundoff */
							eed->f1 = 32768*(1.0-percentcut - 0.0000153);
						else
							eed->f1 = 32768*(percentcut + 0.0000153);
					}				
			}
		}
	/*-------------------------------------*/

			if(smooth)
				subdivideflag(8, 0, B_KNIFE | B_PERCENTSUBD | B_SMOOTH); /* B_KNIFE tells subdivide that edgeflags are already set */
			else
				subdivideflag(8, 0, B_KNIFE | B_PERCENTSUBD); /* B_KNIFE tells subdivide that edgeflags are already set */
			
			for(eed = em->edges.first; eed; eed=eed->next){							
				if(eed->v1->f & 16) eed->v1->f |= 1;
				else eed->v1->f &= ~1;
				
				if(eed->v2->f & 16) eed->v2->f |= 1;
				else eed->v2->f &= ~1;
			}			
		}
	}
	/*----------END Cut Loop-----------------------------*/

	

	/* Clear flags */		
	for(eed = em->edges.first; eed; eed=eed->next){	
		eed->f &= ~(2|4|8|32|64);
		eed->v1->f &= ~(2|16);
		eed->v2->f &= ~(2|16);		
	}
	
	for(evl= em->faces.first; evl; evl=evl->next){
		evl->f &= ~(4|8);
	}
	
	countall();

	if(tagged)
		MEM_freeN(tagged);
	if(taggedsrch)
		MEM_freeN(taggedsrch);
	if(percentfacesloop)
		MEM_freeN(percentfacesloop);
	
	/* send event to redraw this window, does header too */	
	SetBlenderCursor(SYSCURSOR);
	addqueue(curarea->win, REDRAW, 1); 
}

void edge_select(void)
{
	EditMesh *em = G.editMesh;
	EditEdge *closest=0;
	
	closest=findnearestedge();	
	
	if(closest){         /* Did we find anything that is selectable?*/

		if( (G.qual & LR_SHIFTKEY)==0) {
			EditVert *eve;			
			
			undo_push_mesh("Select Edge");
			/* deselectall */
			for(eve= em->verts.first; eve; eve= eve->next) eve->f&= ~1;

			/* select edge */
			closest->v1->f |= 1;
			closest->v2->f |= 1;
		}
		else {
			/*  both of the vertices are selected: deselect both*/
			if((closest->v1->f & 1) && (closest->v2->f & 1) ){  
				closest->v1->f &= ~1;
				closest->v2->f &= ~1;
			}
			else { 
				/* select both */
				closest->v1->f |= 1;
				closest->v2->f |= 1;
			}
		}
		countall();
		allqueue(REDRAWVIEW3D, 0);
	}
}

static void draw_vertices_special(int mode, EditVert *act) /* teken = draw */
{
	/* (only this view, no other windows) */
	/* hackish routine for visual speed:
	 * mode 0: deselect the selected ones, draw them, except act
	 * mode 1: only draw act
	 */
	EditMesh *em = G.editMesh;
	EditVert *eve;
	float size= BIF_GetThemeValuef(TH_VERTEX_SIZE);
	char col[3];
	
	glPointSize(size);

	persp(PERSP_VIEW);
	glPushMatrix();
	mymultmatrix(G.obedit->obmat);

	if(mode==0) {
		BIF_ThemeColor(TH_VERTEX);
		
		/* set zbuffer on, its default off outside main drawloops */
		if(G.vd->drawtype > OB_WIRE) {
			G.zbuf= 1;
			glEnable(GL_DEPTH_TEST);
		}

		glBegin(GL_POINTS);
		eve= (EditVert *)em->verts.first;
		while(eve) {
			if(eve->h==0) {
				if(eve!=act && (eve->f & 1)) {
					eve->f -= 1;
					glVertex3fv(eve->co);
				}
			}
			eve= eve->next;
		}
		glEnd();
		
		glDisable(GL_DEPTH_TEST);
		G.zbuf= 0;
	}
	
	/* draw active vertex */
	if(act->f & 1) BIF_GetThemeColor3ubv(TH_VERTEX_SELECT, col);
	else BIF_GetThemeColor3ubv(TH_VERTEX, col);
	
	glColor3ub(col[0], col[1], col[2]);

	glBegin(GL_POINTS);
	glVertex3fv(act->co);
	glEnd();
	
	glPointSize(1.0);
	glPopMatrix();

	
}

void mouse_mesh(void)
{
	EditVert *act=0;

	if(G.qual & LR_ALTKEY) {
		if (G.qual & LR_CTRLKEY) edge_select();
	}
	else {
	
		act= findnearestvert(1);
		if(act) {
			
			glDrawBuffer(GL_FRONT);

			undo_push_mesh("Select Vertex");

			if( (act->f & 1)==0) act->f+= 1;
			else if(G.qual & LR_SHIFTKEY) act->f-= 1;

			if((G.qual & LR_SHIFTKEY)==0) {
				draw_vertices_special(0, act);
			}
			else draw_vertices_special(1, act);

			countall();

			glFlush();
			glDrawBuffer(GL_BACK);
			
			/* signal that frontbuf differs from back */
			curarea->win_swap= WIN_FRONT_OK;
			
			if(G.f & (G_FACESELECT|G_DRAWFACES|G_DRAWEDGES)) {
				/* update full view later on */
				allqueue(REDRAWVIEW3D, 0);
			}
			else allqueue(REDRAWVIEW3D, curarea->win);	// all windows except this one
		}
	
		rightmouse_transform();
	}
}

static void selectconnectedAll(void)
{
	EditMesh *em = G.editMesh;
	EditVert *v1,*v2;
	EditEdge *eed;
	short flag=1,toggle=0;

	if(em->edges.first==0) return;
	
	undo_push_mesh("Select Connected (All)");

	while(flag==1) {
		flag= 0;
		toggle++;
		if(toggle & 1) eed= em->edges.first;
		else eed= em->edges.last;
		while(eed) {
			v1= eed->v1;
			v2= eed->v2;
			if(eed->h==0) {
				if(v1->f & 1) {
					if( (v2->f & 1)==0 ) {
						v2->f |= 1;
						flag= 1;
					}
				}
				else if(v2->f & 1) {
					if( (v1->f & 1)==0 ) {
						v1->f |= 1;
						flag= 1;
					}
				}
			}
			if(toggle & 1) eed= eed->next;
			else eed= eed->prev;
		}
	}
	countall();

	allqueue(REDRAWVIEW3D, 0);

}

void selectconnected_mesh(int qual)
{
	EditMesh *em = G.editMesh;
	EditVert *eve,*v1,*v2,*act= 0;
	EditEdge *eed;
	short flag=1,sel,toggle=0;

	if(em->edges.first==0) return;

	if(qual & LR_CTRLKEY) {
		selectconnectedAll();
		return;
	}

	sel= 3;
	if(qual & LR_SHIFTKEY) sel=2;
	
	act= findnearestvert(sel-2);
	if(act==0) {
		error("Nothing indicated ");
		return;
	}
	
	undo_push_mesh("Select Linked");
	/* clear test flags */
	eve= em->verts.first;
	while(eve) {
		eve->f&= ~2;
		eve= eve->next;
	}
	act->f= (act->f & ~3) | sel;

	while(flag==1) {
		flag= 0;
		toggle++;
		if(toggle & 1) eed= em->edges.first;
		else eed= em->edges.last;
		while(eed) {
			v1= eed->v1;
			v2= eed->v2;
			if(eed->h==0) {
				if(v1->f & 2) {
					if( (v2->f & 2)==0 ) {
						v2->f= (v2->f & ~3) | sel;
						flag= 1;
					}
				}
				else if(v2->f & 2) {
					if( (v1->f & 2)==0 ) {
						v1->f= (v1->f & ~3) | sel;
						flag= 1;
					}
				}
			}
			if(toggle & 1) eed= eed->next;
			else eed= eed->prev;
		}
	}
	countall();
	
	allqueue(REDRAWVIEW3D, 0);
}


short extrudeflag(short flag,short type)
{
	/* when type=1 old extrusion faces are removed (for spin etc) */
	/* all verts with (flag & 'flag'): extrude */
	/* from old verts, 'flag' is cleared, in new ones it is set */
	EditMesh *em = G.editMesh;
	EditVert *eve, *v1, *v2, *v3, *v4, *nextve;
	EditEdge *eed, *e1, *e2, *e3, *e4, *nexted;
	EditVlak *evl, *evl2, *nextvl;
	short sel=0, deloud= 0, smooth= 0;

	if(G.obedit==0 || get_mesh(G.obedit)==0) return 0;

	/* clear vert flag f1, we use this to detext a loose selected vertice */
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
			eed->f= 1;
			eed->v1->f1= 0;
			eed->v2->f1= 0;
		}
		else eed->f= 0;
		
		eed->f1= 1;		/* this indicates it is an 'old' edge (in this routine we make new ones) */
		
		eed= eed->next;
	}

	/* we set a flag in all selected faces, and increase the associated edge counters */

	evl= em->faces.first;
	while(evl) {
		evl->f= 0;

		if (evl->flag & ME_SMOOTH) {
			if (vlakselectedOR(evl, 1)) smooth= 1;
		}
		
		if(vlakselectedAND(evl, flag)) {
			e1= evl->e1;
			e2= evl->e2;
			e3= evl->e3;
			e4= evl->e4;

			if(e1->f < 3) e1->f++;
			if(e2->f < 3) e2->f++;
			if(e3->f < 3) e3->f++;
			if(e4 && e4->f < 3) e4->f++;
			evl->f= 1;
		}
		else if(vlakselectedOR(evl, flag)) {
			e1= evl->e1;
			e2= evl->e2;
			e3= evl->e3;
			e4= evl->e4;
			
			if( (e1->v1->f & flag) && (e1->v2->f & flag) ) e1->f1= 2;
			if( (e2->v1->f & flag) && (e2->v2->f & flag) ) e2->f1= 2;
			if( (e3->v1->f & flag) && (e3->v2->f & flag) ) e3->f1= 2;
			if( e4 && (e4->v1->f & flag) && (e4->v2->f & flag) ) e4->f1= 2;
		}
		
		evl= evl->next;
	}

	/* set direction of edges */
	evl= em->faces.first;
	while(evl) {
		if(evl->f== 0) {
			if(evl->e1->f==2) {
				if(evl->e1->v1 == evl->v1) evl->e1->dir= 0;
				else evl->e1->dir= 1;
			}
			if(evl->e2->f==2) {
				if(evl->e2->v1 == evl->v2) evl->e2->dir= 0;
				else evl->e2->dir= 1;
			}
			if(evl->e3->f==2) {
				if(evl->e3->v1 == evl->v3) evl->e3->dir= 0;
				else evl->e3->dir= 1;
			}
			if(evl->e4 && evl->e4->f==2) {
				if(evl->e4->v1 == evl->v4) evl->e4->dir= 0;
				else evl->e4->dir= 1;
			}
		}
		evl= evl->next;
	}	


	/* the current state now is:
		eve->f1==1: loose selected vertex 

		eed->f==0 : edge is not selected, no extrude
		eed->f==1 : edge selected, is not part of a face, extrude
		eed->f==2 : edge selected, is part of 1 face, extrude
		eed->f==3 : edge selected, is part of more faces, no extrude
		
		eed->f1==0: new edge
		eed->f1==1: edge selected, is part of selected face, when eed->f==3: remove
		eed->f1==2: edge selected, is not part of a selected face
					
		evl->f==1 : duplicate this face
	*/

	/* copy all selected vertices, */
	/* write pointer to new vert in old struct at eve->vn */
	eve= em->verts.last;
	while(eve) {
		eve->f&= ~128;  /* clear, for later test for loose verts */
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

	/* all edges with eed->f==1 or eed->f==2 become faces */
	/* if deloud==1 then edges with eed->f>2 are removed */
	eed= em->edges.last;
	while(eed) {
		nexted= eed->prev;
		if( eed->f<3) {
			eed->v1->f|=128;  /* = no loose vert! */
			eed->v2->f|=128;
		}
		if( (eed->f==1 || eed->f==2) ) {
			if(eed->f1==2) deloud=1;
			
			if(eed->dir==1) evl2= addvlaklist(eed->v1, eed->v2, eed->v2->vn, eed->v1->vn, NULL);
			else evl2= addvlaklist(eed->v2, eed->v1, eed->v1->vn, eed->v2->vn, NULL);
			if (smooth) evl2->flag |= ME_SMOOTH;
			
			/* new edges, needs copied from old edge. actually we should find face that has this edge */
			evl2->e1->crease= eed->crease;
			evl2->e2->crease= eed->crease;
			evl2->e3->crease= eed->crease;
			if(evl2->e4) evl2->e4->crease= eed->crease;
		}

		eed= nexted;
	}
	if(deloud) {
		eed= em->edges.first;
		while(eed) {
			nexted= eed->next;
			if(eed->f==3 && eed->f1==1) {
				remedge(eed);
				free_editedge(eed);
			}
			eed= nexted;
		}
	}
	/* duplicate faces, if necessart remove old ones  */
	evl= em->faces.first;
	while(evl) {
		nextvl= evl->next;
		if(evl->f & 1) {
		
			v1= evl->v1->vn;
			v2= evl->v2->vn;
			v3= evl->v3->vn;
			if(evl->v4) v4= evl->v4->vn; else v4= 0;
			
			evl2= addvlaklist(v1, v2, v3, v4, evl);
			
			if(deloud) {
				BLI_remlink(&em->faces, evl);
				free_editvlak(evl);
			}
			if (smooth) evl2->flag |= ME_SMOOTH;			
		}
		evl= nextvl;
	}
	/* for all vertices with eve->vn!=0 
		if eve->f1==1: make edge
		if flag!=128 : if deloud==1: remove
	*/
	eve= em->verts.last;
	while(eve) {
		nextve= eve->prev;
		if(eve->vn) {
			if(eve->f1==1) addedgelist(eve, eve->vn, NULL);
			else if( (eve->f & 128)==0) {
				if(deloud) {
					BLI_remlink(&em->verts,eve);
					free_editvert(eve);
					eve= NULL;
				}
			}
		}
		if(eve) eve->f&= ~128;
		
		eve= nextve;
	}

	return 1;
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

short removedoublesflag(short flag, float limit)		/* return amount */
{
	EditMesh *em = G.editMesh;
	/* all verts with (flag & 'flag') are being evaluated */
	EditVert *eve, *v1, *nextve;
	EditEdge *eed, *e1, *nexted;
	EditVlak *evl, *nextvl;
	struct xvertsort *sortblock, *sb, *sb1;
	struct vlaksort *vlsortblock, *vsb, *vsb1;
	float dist;
	int a, b, test, aantal;

	/* flag 128 is cleared, count */
	eve= em->verts.first;
	aantal= 0;
	while(eve) {
		eve->f&= ~128;
		if(eve->f & flag) aantal++;
		eve= eve->next;
	}
	if(aantal==0) return 0;

	/* allocate memory and qsort */
	sb= sortblock= (struct xvertsort *)MEM_mallocN(sizeof(struct xvertsort)*aantal,"sortremovedoub");
	eve= em->verts.first;
	while(eve) {
		if(eve->f & flag) {
			sb->x= eve->co[0]+eve->co[1]+eve->co[2];
			sb->v1= eve;
			sb++;
		}
		eve= eve->next;
	}
	qsort(sortblock, aantal, sizeof(struct xvertsort), vergxco);

	/* test for doubles */
	sb= sortblock;
	for(a=0; a<aantal; a++) {
		eve= sb->v1;
		if( (eve->f & 128)==0 ) {
			sb1= sb+1;
			for(b=a+1; b<aantal; b++) {
				/* first test: simpel dist */
				dist= sb1->x - sb->x;
				if(dist > limit) break;
				
				/* second test: is vertex allowed */
				v1= sb1->v1;
				if( (v1->f & 128)==0 ) {
					
					dist= fabs(v1->co[0]-eve->co[0]);
					if(dist<=limit) {
						dist= fabs(v1->co[1]-eve->co[1]);
						if(dist<=limit) {
							dist= fabs(v1->co[2]-eve->co[2]);
							if(dist<=limit) {
								v1->f|= 128;
								v1->vn= eve;
							}
						}
					}
				}
				sb1++;
			}
		}
		sb++;
	}
	MEM_freeN(sortblock);

	/* test edges and insert again */
	eed= em->edges.first;
	while(eed) {
		eed->f= 0;
		eed= eed->next;
	}
	eed= em->edges.last;
	while(eed) {
		nexted= eed->prev;

		if(eed->f==0) {
			if( (eed->v1->f & 128) || (eed->v2->f & 128) ) {
				remedge(eed);

				if(eed->v1->f & 128) eed->v1= eed->v1->vn;
				if(eed->v2->f & 128) eed->v2= eed->v2->vn;

				e1= addedgelist(eed->v1, eed->v2, eed);
				
				if(e1) e1->f= 1;
				if(e1!=eed) free_editedge(eed);
			}
		}
		eed= nexted;
	}

	/* first count amount of test faces */
	evl= (struct EditVlak *)em->faces.first;
	aantal= 0;
	while(evl) {
		evl->f= 0;
		if(evl->v1->f & 128) evl->f= 1;
		else if(evl->v2->f & 128) evl->f= 1;
		else if(evl->v3->f & 128) evl->f= 1;
		else if(evl->v4 && (evl->v4->f & 128)) evl->f= 1;
		
		if(evl->f==1) aantal++;
		evl= evl->next;
	}

	/* test faces for double vertices, and if needed remove them */
	evl= (struct EditVlak *)em->faces.first;
	while(evl) {
		nextvl= evl->next;
		if(evl->f==1) {
			
			if(evl->v1->f & 128) evl->v1= evl->v1->vn;
			if(evl->v2->f & 128) evl->v2= evl->v2->vn;
			if(evl->v3->f & 128) evl->v3= evl->v3->vn;
			if(evl->v4 && (evl->v4->f & 128)) evl->v4= evl->v4->vn;
		
			test= 0;
			if(evl->v1==evl->v2) test+=1;
			if(evl->v2==evl->v3) test+=2;
			if(evl->v3==evl->v1) test+=4;
			if(evl->v4==evl->v1) test+=8;
			if(evl->v3==evl->v4) test+=16;
			if(evl->v2==evl->v4) test+=32;
			
			if(test) {
				if(evl->v4) {
					if(test==1 || test==2) {
						evl->v2= evl->v3;
						evl->v3= evl->v4;
						evl->v4= 0;
						test= 0;
					}
					else if(test==8 || test==16) {
						evl->v4= 0;
						test= 0;
					}
					else {
						BLI_remlink(&em->faces, evl);
						free_editvlak(evl);
						aantal--;
					}
				}
				else {
					BLI_remlink(&em->faces, evl);
					free_editvlak(evl);
					aantal--;
				}
			}
			
			if(test==0) {
				/* set edge pointers */
				evl->e1= findedgelist(evl->v1, evl->v2);
				evl->e2= findedgelist(evl->v2, evl->v3);
				if(evl->v4==0) {
					evl->e3= findedgelist(evl->v3, evl->v1);
					evl->e4= 0;
				}
				else {
					evl->e3= findedgelist(evl->v3, evl->v4);
					evl->e4= findedgelist(evl->v4, evl->v1);
				}
			}
		}
		evl= nextvl;
	}

	/* double faces: sort block */
	/* count again, now all selected faces */
	aantal= 0;
	evl= em->faces.first;
	while(evl) {
		evl->f= 0;
		if(vlakselectedAND(evl, 1)) {
			evl->f= 1;
			aantal++;
		}
		evl= evl->next;
	}

	if(aantal) {
		/* double faces: sort block */
		vsb= vlsortblock= MEM_mallocN(sizeof(struct vlaksort)*aantal, "sortremovedoub");
		evl= em->faces.first;
		while(evl) {
			if(evl->f & 1) {
				if(evl->v4) vsb->x= (long) MIN4( (long)evl->v1, (long)evl->v2, (long)evl->v3, (long)evl->v4);
				else vsb->x= (long) MIN3( (long)evl->v1, (long)evl->v2, (long)evl->v3);

				vsb->evl= evl;
				vsb++;
			}
			evl= evl->next;
		}
		
		qsort(vlsortblock, aantal, sizeof(struct vlaksort), vergvlak);
			
		vsb= vlsortblock;
		for(a=0; a<aantal; a++) {
			evl= vsb->evl;
			if( (evl->f & 128)==0 ) {
				vsb1= vsb+1;

				for(b=a+1; b<aantal; b++) {
				
					/* first test: same pointer? */
					if(vsb->x != vsb1->x) break;
					
					/* second test: is test permitted? */
					evl= vsb1->evl;
					if( (evl->f & 128)==0 ) {
						if( comparevlak(evl, vsb->evl)) evl->f |= 128;
						
					}
					vsb1++;
				}
			}
			vsb++;
		}
		
		MEM_freeN(vlsortblock);
		
		/* remove double faces */
		evl= (struct EditVlak *)em->faces.first;
		while(evl) {
			nextvl= evl->next;
			if(evl->f & 128) {
				BLI_remlink(&em->faces, evl);
				free_editvlak(evl);
			}
			evl= nextvl;
		}
	}
	
	/* remove double vertices */
	a= 0;
	eve= (struct EditVert *)em->verts.first;
	while(eve) {
		nextve= eve->next;
		if(eve->f & flag) {
			if(eve->f & 128) {
				a++;
				BLI_remlink(&em->verts, eve);
				free_editvert(eve);
			}
		}
		eve= nextve;
	}
	return a;	/* amount */
}

void xsortvert_flag(int flag)
{
	EditMesh *em = G.editMesh;
	/* all verts with (flag & 'flag') are sorted */
	EditVert *eve;
	struct xvertsort *sortblock, *sb;
	ListBase tbase;
	int aantal;
	
	/* count */
	eve= em->verts.first;
	aantal= 0;
	while(eve) {
		if(eve->f & flag) aantal++;
		eve= eve->next;
	}
	if(aantal==0) return;

	undo_push_mesh("Xsort");
	
	/* allocate memory and sort */
	sb= sortblock= (struct xvertsort *)MEM_mallocN(sizeof(struct xvertsort)*aantal,"sortremovedoub");
	eve= em->verts.first;
	while(eve) {
		if(eve->f & flag) {
			sb->x= eve->xs;
			sb->v1= eve;
			sb++;
		}
		eve= eve->next;
	}
	qsort(sortblock, aantal, sizeof(struct xvertsort), vergxco);
	
	/* make temporal listbase */
	tbase.first= tbase.last= 0;
	sb= sortblock;
	while(aantal--) {
		eve= sb->v1;
		BLI_remlink(&em->verts, eve);
		BLI_addtail(&tbase, eve);
		sb++;
	}
	
	addlisttolist(&em->verts, &tbase);
	
	MEM_freeN(sortblock);
}


void hashvert_flag(int flag)
{
	/* switch vertex order using hash table */
	EditMesh *em = G.editMesh;
	EditVert *eve;
	struct xvertsort *sortblock, *sb, onth, *newsort;
	ListBase tbase;
	int aantal, a, b;
	
	/* count */
	eve= em->verts.first;
	aantal= 0;
	while(eve) {
		if(eve->f & flag) aantal++;
		eve= eve->next;
	}
	if(aantal==0) return;
	
	undo_push_mesh("Hash");

	/* allocate memory */
	sb= sortblock= (struct xvertsort *)MEM_mallocN(sizeof(struct xvertsort)*aantal,"sortremovedoub");
	eve= em->verts.first;
	while(eve) {
		if(eve->f & flag) {
			sb->v1= eve;
			sb++;
		}
		eve= eve->next;
	}

	BLI_srand(1);
	
	sb= sortblock;
	for(a=0; a<aantal; a++, sb++) {
		b= aantal*BLI_drand();
		if(b>=0 && b<aantal) {
			newsort= sortblock+b;
			onth= *sb;
			*sb= *newsort;
			*newsort= onth;
		}
	}

	/* make temporal listbase */
	tbase.first= tbase.last= 0;
	sb= sortblock;
	while(aantal--) {
		eve= sb->v1;
		BLI_remlink(&em->verts, eve);
		BLI_addtail(&tbase, eve);
		sb++;
	}
	
	addlisttolist(&em->verts, &tbase);
	
	MEM_freeN(sortblock);
}

static unsigned int cpack_fact(unsigned int col1, unsigned int col2, float fact)
{
	char *cp1, *cp2, *cp;
	unsigned int col=0;
	float fact1;
	
	fact1=1-fact; /*result is fact% col1 and (1-fact) % col2 */
		
	cp1= (char *)&col1;
	cp2= (char *)&col2;
	cp=  (char *)&col;
	
	cp[0]= fact*cp1[0]+fact1*cp2[0];
	cp[1]= fact*cp1[1]+fact1*cp2[1];
	cp[2]= fact*cp1[2]+fact1*cp2[2];
	cp[3]= fact*cp1[3]+fact1*cp2[3];
	
	return col;
}


static void uv_half(float *uv, float *uv1, float *uv2)
{
	uv[0]= (uv1[0]+uv2[0])/2.0;
	uv[1]= (uv1[1]+uv2[1])/2.0;
	
}

static void uv_quart(float *uv, float *uv1)
{
	uv[0]= (uv1[0]+uv1[2]+uv1[4]+uv1[6])/4.0;
	uv[1]= (uv1[1]+uv1[3]+uv1[5]+uv1[7])/4.0;
}

static void set_wuv(int tot, EditVlak *evl, int v1, int v2, int v3, int v4)
{
	/* this weird function only to be used for subdivide, the 'w' in the name has no meaning! */
	float *uv, uvo[4][2];
	unsigned int *col, colo[4], col1, col2;
	int a, v;
						/* Numbers corespond to verts (corner points), 	*/
						/* edge->vn's (center edges), the Center 	*/
	memcpy(uvo, evl->tf.uv, sizeof(uvo));	/* And the quincunx points of a face 		*/
	uv= evl->tf.uv[0];                            /* as shown here:     				*/
	                                              /*           2         5          1   */
	memcpy(colo, evl->tf.col, sizeof(colo));      /*               10         13        */
	col= evl->tf.col;                             /*           6         9          8   */
                                                  /*               11         12        */
	if(tot==4) {                                  /*           3         7          4   */
		for(a=0; a<4; a++, uv+=2, col++) {
			if(a==0) v= v1;
			else if(a==1) v= v2;
			else if(a==2) v= v3;
			else v= v4;
			
			if(a==3 && v4==0) break;
			
			if(v<=4) {
				uv[0]= uvo[v-1][0];
				uv[1]= uvo[v-1][1];
				*col= colo[v-1];
			}
			else if(v==8) {
				uv_half(uv, uvo[3], uvo[0]);
				*col= cpack_fact(colo[3], colo[0], 0.5);
			}
			else if(v==9) {
				uv_quart(uv, uvo[0]);
				col1= cpack_fact(colo[1], colo[0], 0.5);
				col2= cpack_fact(colo[2], colo[3], 0.5);
				*col= cpack_fact(col1, col2, 0.5);
			}
			/* Cases for adjacent edge square subdivide  Real voodoo */
			/* 1/2 closest corner + 1/4 adjacent corners */
			else if (v==10){ /* case test==3 in subdivideflag() */	
				uv[0]=(2*uvo[1][0]+uvo[0][0]+uvo[2][0])/4;
				uv[1]=(2*uvo[1][1]+uvo[0][1]+uvo[2][1])/4;
				col1= cpack_fact(colo[1], colo[0], 0.75);
				col2= cpack_fact(colo[2], colo[3], 0.75);
				*col= cpack_fact(col1, col2, 0.75);	
			}
			else if (v==11) { /* case of test==6 */
				uv[0]=(2*uvo[2][0]+uvo[1][0]+uvo[3][0])/4;
				uv[1]=(2*uvo[2][1]+uvo[1][1]+uvo[3][1])/4;
				col1= cpack_fact(colo[1], colo[0], 0.75);
				col2= cpack_fact(colo[2], colo[3], 0.75);
				*col= cpack_fact(col1, col2, 0.25);	
			}
			else if (v==12) { /* case of test==12 */
				uv[0]=(2*uvo[3][0]+uvo[2][0]+uvo[0][0])/4;
				uv[1]=(2*uvo[3][1]+uvo[2][1]+uvo[0][1])/4;
				col1= cpack_fact(colo[1], colo[0], 0.25);
				col2= cpack_fact(colo[2], colo[3], 0.25);
				*col= cpack_fact(col1, col2, 0.25);
			}
			else if (v==13) { /* case of test==9 */
				uv[0]=(2*uvo[0][0]+uvo[1][0]+uvo[3][0])/4;
				uv[1]=(2*uvo[0][1]+uvo[1][1]+uvo[3][1])/4;
				col1= cpack_fact(colo[1], colo[0], 0.25);
				col2= cpack_fact(colo[2], colo[3], 0.25);
				*col= cpack_fact(col1, col2, 0.75);
			}
			/* default for consecutive verts*/
			else { 
				uv_half(uv, uvo[v-5], uvo[v-4]);
				*col= cpack_fact(colo[v-5], colo[v-4], 0.5);
			}
		}
	}
	else {
		for(a=0; a<3; a++, uv+=2, col++) {
			if(a==0) v= v1;
			else if(a==1) v= v2;
			else v= v3;
		
			if(v<=4) {
				uv[0]= uvo[v-1][0];
				uv[1]= uvo[v-1][1];
				*col= colo[v-1];
			}
			else if(v==7) {
				uv_half(uv, uvo[2], uvo[0]);
				*col= cpack_fact(colo[2], colo[0], 0.5);
			}
			else {
				uv_half(uv, uvo[v-5], uvo[v-4]);
				*col= cpack_fact(colo[v-5], colo[v-4], 0.5);
			}
		}
	}
}

static EditVert *vert_from_number(EditVlak *evl, int nr)
{
	switch(nr) {
	case 0:
		return 0;
	case 1:
		return evl->v1;
	case 2:
		return evl->v2;
	case 3:
		return evl->v3;
	case 4:
		return evl->v4;
	case 5:
		return evl->e1->vn;
	case 6:
		return evl->e2->vn;
	case 7:
		return evl->e3->vn;
	case 8:
		return evl->e4->vn;
	}
	
	return NULL;
}

static void addvlak_subdiv(EditVlak *evl, int val1, int val2, int val3, int val4, EditVert *eve)
{
	EditVlak *w;
	EditVert *v1, *v2, *v3, *v4;
	
	if(val1>=9) v1= eve;
	else v1= vert_from_number(evl, val1);
	
	if(val2>=9) v2= eve;
	else v2= vert_from_number(evl, val2);

	if(val3>=9) v3= eve;
	else v3= vert_from_number(evl, val3);

	if(val4>=9) v4= eve;
	else v4= vert_from_number(evl, val4);
	
	w= addvlaklist(v1, v2, v3, v4, evl);
	if(w) {
		if(evl->v4) set_wuv(4, w, val1, val2, val3, val4);
		else set_wuv(3, w, val1, val2, val3, val4);
	}
}

static float smoothperc= 0.0;

static void smooth_subdiv_vec(float *v1, float *v2, float *n1, float *n2, float *vec)
{
	float len, fac, nor[3], nor1[3], nor2[3];
	
	VecSubf(nor, v1, v2);
	len= 0.5*Normalise(nor);

	VECCOPY(nor1, n1);
	VECCOPY(nor2, n2);

	/* cosine angle */
	fac= nor[0]*nor1[0] + nor[1]*nor1[1] + nor[2]*nor1[2] ;
	
	vec[0]= fac*nor1[0];
	vec[1]= fac*nor1[1];
	vec[2]= fac*nor1[2];

	/* cosine angle */
	fac= -nor[0]*nor2[0] - nor[1]*nor2[1] - nor[2]*nor2[2] ;
	
	vec[0]+= fac*nor2[0];
	vec[1]+= fac*nor2[1];
	vec[2]+= fac*nor2[2];

	vec[0]*= smoothperc*len;
	vec[1]*= smoothperc*len;
	vec[2]*= smoothperc*len;
}

static void smooth_subdiv_quad(EditVlak *evl, float *vec)
{
	
	float nor1[3], nor2[3];
	float vec1[3], vec2[3];
	float cent[3];
	
	/* vlr->e1->vn is new vertex inbetween v1 / v2 */
	
	VecMidf(nor1, evl->v1->no, evl->v2->no);
	Normalise(nor1);
	VecMidf(nor2, evl->v3->no, evl->v4->no);
	Normalise(nor2);

	smooth_subdiv_vec( evl->e1->vn->co, evl->e3->vn->co, nor1, nor2, vec1);

	VecMidf(nor1, evl->v2->no, evl->v3->no);
	Normalise(nor1);
	VecMidf(nor2, evl->v4->no, evl->v1->no);
	Normalise(nor2);

	smooth_subdiv_vec( evl->e2->vn->co, evl->e4->vn->co, nor1, nor2, vec2);

	VecAddf(vec1, vec1, vec2);

	CalcCent4f(cent, evl->v1->co,  evl->v2->co,  evl->v3->co,  evl->v4->co);
	VecAddf(vec, cent, vec1);
}

void subdivideflag(int flag, float rad, int beauty)
{
	EditMesh *em = G.editMesh;
	/* subdivide all with (vertflag & flag) */
	/* if rad>0.0 it's a 'sphere' subdivide */
	/* if rad<0.0 it's a fractal subdivide */
	extern float doublimit;
	EditVert *eve;
	EditEdge *eed, *e1, *e2, *e3, *e4, *nexted;
	EditVlak *evl;
	float fac, vec[3], vec1[3], len1, len2, len3, percent;
	short test;
	
	if(beauty & B_SMOOTH) {
		short perc= 100;

		if(button(&perc, 10, 500, "Percentage:")==0) return;
		
		smoothperc= 0.292*perc/100.0;
	}

	/* edgeflags */
	eed= em->edges.first;
	while((eed) && !(beauty & B_KNIFE)) {	
		if( (eed->v1->f & flag) && (eed->v2->f & flag) ) eed->f= flag;
		else eed->f= 0;	
		eed= eed->next;
	}
	
	/* if beauty: test for area and clear edge flags of 'ugly' edges */
	if(beauty & B_BEAUTY) {
		evl= em->faces.first;
		while(evl) {
			if( vlakselectedAND(evl, flag) ) {
				if(evl->v4) {
				
					/* area */
					len1= AreaQ3Dfl(evl->v1->co, evl->v2->co, evl->v3->co, evl->v4->co);
					if(len1 <= doublimit) {
						evl->e1->f = 0;
						evl->e2->f = 0;
						evl->e3->f = 0;
						evl->e4->f = 0;
					}
					else {
						len1= VecLenf(evl->v1->co, evl->v2->co) + VecLenf(evl->v3->co, evl->v4->co);
						len2= VecLenf(evl->v2->co, evl->v3->co) + VecLenf(evl->v1->co, evl->v4->co);
						
						if(len1 < len2) {
							evl->e1->f = 0;
							evl->e3->f = 0;
						}
						else if(len1 > len2) {
							evl->e2->f = 0;
							evl->e4->f = 0;
						}
					}
				}
				else {
					/* area */
					len1= AreaT3Dfl(evl->v1->co, evl->v2->co, evl->v3->co);
					if(len1 <= doublimit) {
						evl->e1->f = 0;
						evl->e2->f = 0;
						evl->e3->f = 0;
					}
					else {
						len1= VecLenf(evl->v1->co, evl->v2->co) ;
						len2= VecLenf(evl->v2->co, evl->v3->co) ;
						len3= VecLenf(evl->v3->co, evl->v1->co) ;
						
						if(len1<len2 && len1<len3) {
							evl->e1->f = 0;
						}
						else if(len2<len3 && len2<len1) {
							evl->e2->f = 0;
						}
						else if(len3<len2 && len3<len1) {
							evl->e3->f = 0;
						}
					}
				}
			}
			evl= evl->next;
		}
	}

	if(beauty & B_SMOOTH) {
		
		vertexnormals(0);		/* no1*/
			
	}
	
	/* make new normal and put in edge, clear flag! needed for face creation part below */
	eed= em->edges.first;
	while(eed) {
		if(eed->f & flag) {
			/* Subdivide percentage is stored in 1/32768ths in eed->f1 */
			if (beauty & B_PERCENTSUBD) percent=(float)(eed->f1)/32768.0;
			else percent=0.5;
			
			vec[0]= (1-percent)*eed->v1->co[0] + percent*eed->v2->co[0];
			vec[1]= (1-percent)*eed->v1->co[1] + percent*eed->v2->co[1];
			vec[2]= (1-percent)*eed->v1->co[2] + percent*eed->v2->co[2];

			if(rad > 0.0) {   /* subdivide sphere */
				Normalise(vec);
				vec[0]*= rad;
				vec[1]*= rad;
				vec[2]*= rad;
			}
			else if(rad< 0.0) {  /* fractal subdivide */
				fac= rad* VecLenf(eed->v1->co, eed->v2->co);
				vec1[0]= fac*BLI_drand();
				vec1[1]= fac*BLI_drand();
				vec1[2]= fac*BLI_drand();
				VecAddf(vec, vec, vec1);
			}
			
			if(beauty & B_SMOOTH) {
				smooth_subdiv_vec(eed->v1->co, eed->v2->co, eed->v1->no, eed->v2->no, vec1);
				VecAddf(vec, vec, vec1);
			}
			
			eed->vn= addvertlist(vec);
			eed->vn->f= eed->v1->f;

		}
		else eed->vn= 0;
		
		eed->f= 0; /* needed! */
		
		eed= eed->next;
	}

	/* test all faces for subdivide edges, there are 8 or 16 cases (ugh)! */

	evl= em->faces.last;
	while(evl) {
		if( vlakselectedOR(evl, flag) ) {
			e1= evl->e1;
			e2= evl->e2;
			e3= evl->e3;
			e4= evl->e4;

			test= 0;
			if(e1 && e1->vn) { 
				test+= 1; 
				e1->f= 1;
			}
			if(e2 && e2->vn) { 
				test+= 2; 
				e2->f= 1;
			}
			if(e3 && e3->vn) { 
				test+= 4; 
				e3->f= 1;
			}
			if(e4 && e4->vn) { 
				test+= 8; 
				e4->f= 1;
			}
			if(test) {
				if(evl->v4==0) {  /* All the permutations of 3 edges*/
					if((test & 3)==3) addvlak_subdiv(evl, 2, 2+4, 1+4, 0, 0);
					if((test & 6)==6) addvlak_subdiv(evl, 3, 3+4, 2+4, 0, 0);
					if((test & 5)==5) addvlak_subdiv(evl, 1, 1+4, 3+4, 0, 0);

					if(test==7) {  /* four new faces, old face renews */
						evl->v1= e1->vn;
						evl->v2= e2->vn;
						evl->v3= e3->vn;
						set_wuv(3, evl, 1+4, 2+4, 3+4, 0);
					}
					else if(test==3) {
						addvlak_subdiv(evl, 1+4, 2+4, 3, 0, 0);
						evl->v2= e1->vn;
						set_wuv(3, evl, 1, 1+4, 3, 0);
					}
					else if(test==6) {
						addvlak_subdiv(evl, 2+4, 3+4, 1, 0, 0);
						evl->v3= e2->vn;
						set_wuv(3, evl, 1, 2, 2+4, 0);
					}
					else if(test==5) {
						addvlak_subdiv(evl, 3+4, 1+4, 2, 0, 0);
						evl->v1= e3->vn;
						set_wuv(3, evl, 3+4, 2, 3, 0);
					}
					else if(test==1) {
						addvlak_subdiv(evl, 1+4, 2, 3, 0, 0);
						evl->v2= e1->vn;
						set_wuv(3, evl, 1, 1+4, 3, 0);
					}
					else if(test==2) {
						addvlak_subdiv(evl, 2+4, 3, 1, 0, 0);
						evl->v3= e2->vn;
						set_wuv(3, evl, 1, 2, 2+4, 0);
					}
					else if(test==4) {
						addvlak_subdiv(evl, 3+4, 1, 2, 0, 0);
						evl->v1= e3->vn;
						set_wuv(3, evl, 3+4, 2, 3, 0);
					}
					evl->e1= addedgelist(evl->v1, evl->v2, evl->e1);
					evl->e2= addedgelist(evl->v2, evl->v3, evl->e2);
					evl->e3= addedgelist(evl->v3, evl->v1, evl->e3);
					
				}
				else {  /* All the permutations of 4 faces */
					if(test==15) {
						/* add a new point in center */
						CalcCent4f(vec, evl->v1->co, evl->v2->co, evl->v3->co, evl->v4->co);
						
						if(beauty & B_SMOOTH) {
							smooth_subdiv_quad(evl, vec);	/* adds */
						}
						eve= addvertlist(vec);
						
						eve->f |= flag;
						
						addvlak_subdiv(evl, 2, 2+4, 9, 1+4, eve);
						addvlak_subdiv(evl, 3, 3+4, 9, 2+4, eve);
						addvlak_subdiv(evl, 4, 4+4, 9, 3+4, eve);

						evl->v2= e1->vn;
						evl->v3= eve;
						evl->v4= e4->vn;
						set_wuv(4, evl, 1, 1+4, 9, 4+4);
					}
					else { 
						if(((test & 3)==3)&&(test!=3)) addvlak_subdiv(evl, 1+4, 2, 2+4, 0, 0);
						if(((test & 6)==6)&&(test!=6)) addvlak_subdiv(evl, 2+4, 3, 3+4, 0, 0);
						if(((test & 12)==12)&&(test!=12)) addvlak_subdiv(evl, 3+4, 4, 4+4, 0, 0);
						if(((test & 9)==9)&&(test!=9)) addvlak_subdiv(evl, 4+4, 1, 1+4, 0, 0);
						
						if(test==1) { /* Edge 1 has new vert */
							addvlak_subdiv(evl, 1+4, 2, 3, 0, 0);
							addvlak_subdiv(evl, 1+4, 3, 4, 0, 0);
							evl->v2= e1->vn;
							evl->v3= evl->v4;
							evl->v4= 0;
							set_wuv(4, evl, 1, 1+4, 4, 0);
						}
						else if(test==2) { /* Edge 2 has new vert */
							addvlak_subdiv(evl, 2+4, 3, 4, 0, 0);
							addvlak_subdiv(evl, 2+4, 4, 1, 0, 0);
							evl->v3= e2->vn;
							evl->v4= 0;
							set_wuv(4, evl, 1, 2, 2+4, 0);
						}
						else if(test==4) { /* Edge 3 has new vert */
							addvlak_subdiv(evl, 3+4, 4, 1, 0, 0);
							addvlak_subdiv(evl, 3+4, 1, 2, 0, 0);
							evl->v1= evl->v2;
							evl->v2= evl->v3;
							evl->v3= e3->vn;
							evl->v4= 0;
							set_wuv(4, evl, 2, 3, 3+4, 0);
						}
						else if(test==8) { /* Edge 4 has new vert */
							addvlak_subdiv(evl, 4+4, 1, 2, 0, 0);
							addvlak_subdiv(evl, 4+4, 2, 3, 0, 0);
							evl->v1= evl->v3;
							evl->v2= evl->v4;
							evl->v3= e4->vn;
							evl->v4= 0;
							set_wuv(4, evl, 3, 4, 4+4, 0);
						}
						else if(test==3) { /*edge 1&2 */
							/* make new vert in center of new edge */	
							vec[0]=(e1->vn->co[0]+e2->vn->co[0])/2;
							vec[1]=(e1->vn->co[1]+e2->vn->co[1])/2;
							vec[2]=(e1->vn->co[2]+e2->vn->co[2])/2;
							eve= addvertlist(vec);
							eve->f |= flag;
							/* Add new faces */
							addvlak_subdiv(evl, 4, 10, 2+4, 3, eve);
							addvlak_subdiv(evl, 4, 1, 1+4, 10, eve);	
							/* orig face becomes small corner */
							evl->v1=e1->vn;
							//evl->v2=evl->v2;
							evl->v3=e2->vn;
							evl->v4=eve;
							
							set_wuv(4, evl, 1+4, 2, 2+4, 10);
						}
						else if(test==6) { /* 2&3 */
							/* make new vert in center of new edge */	
							vec[0]=(e2->vn->co[0]+e3->vn->co[0])/2;
							vec[1]=(e2->vn->co[1]+e3->vn->co[1])/2;
							vec[2]=(e2->vn->co[2]+e3->vn->co[2])/2;
							eve= addvertlist(vec);
							eve->f |= flag;
							/*New faces*/
							addvlak_subdiv(evl, 1, 11, 3+4, 4, eve);
							addvlak_subdiv(evl, 1, 2, 2+4, 11, eve);
							/* orig face becomes small corner */
							evl->v1=e2->vn;
							evl->v2=evl->v3;
							evl->v3=e3->vn;
							evl->v4=eve;
							
							set_wuv(4, evl, 2+4, 3, 3+4, 11);
						}
						else if(test==12) { /* 3&4 */
							/* make new vert in center of new edge */	
							vec[0]=(e3->vn->co[0]+e4->vn->co[0])/2;
							vec[1]=(e3->vn->co[1]+e4->vn->co[1])/2;
							vec[2]=(e3->vn->co[2]+e4->vn->co[2])/2;
							eve= addvertlist(vec);
							eve->f |= flag;
							/*New Faces*/
							addvlak_subdiv(evl, 2, 12, 4+4, 1, eve);
							addvlak_subdiv(evl, 2, 3, 3+4, 12, eve); 
							/* orig face becomes small corner */
							evl->v1=e3->vn;
							evl->v2=evl->v4;
							evl->v3=e4->vn;
							evl->v4=eve;
							
							set_wuv(4, evl, 3+4, 4, 4+4, 12);
						}
						else if(test==9) { /* 4&1 */
							/* make new vert in center of new edge */	
							vec[0]=(e1->vn->co[0]+e4->vn->co[0])/2;
							vec[1]=(e1->vn->co[1]+e4->vn->co[1])/2;
							vec[2]=(e1->vn->co[2]+e4->vn->co[2])/2;
							eve= addvertlist(vec);
							eve->f |= flag;
							/*New Faces*/
							addvlak_subdiv(evl, 3, 13, 1+4, 2, eve);
							addvlak_subdiv(evl, 3, 4,  4+4, 13, eve);
							/* orig face becomes small corner */
							evl->v2=evl->v1;
							evl->v1=e4->vn;
							evl->v3=e1->vn;
							evl->v4=eve;
							
							set_wuv(4, evl, 4+4, 1, 1+4, 13);
						}
						else if(test==5) { /* 1&3 */
							addvlak_subdiv(evl, 1+4, 2, 3, 3+4, 0);
							evl->v2= e1->vn;
							evl->v3= e3->vn;
							set_wuv(4, evl, 1, 1+4, 3+4, 4);
						}
						else if(test==10) { /* 2&4 */
							addvlak_subdiv(evl, 2+4, 3, 4, 4+4, 0);
							evl->v3= e2->vn;
							evl->v4= e4->vn;
							set_wuv(4, evl, 1, 2, 2+4, 4+4);
						}/* Unfortunately, there is no way to avoid tris on 1 or 3 edges*/
						else if(test==7) { /*1,2&3 */
							addvlak_subdiv(evl, 1+4, 2+4, 3+4, 0, 0);
							evl->v2= e1->vn;
							evl->v3= e3->vn;
							set_wuv(4, evl, 1, 1+4, 3+4, 4);
						}
						
						else if(test==14) { /* 2,3&4 */
							addvlak_subdiv(evl, 2+4, 3+4, 4+4, 0, 0);
							evl->v3= e2->vn;
							evl->v4= e4->vn;
							set_wuv(4, evl, 1, 2, 2+4, 4+4);
						}
						else if(test==13) {/* 1,3&4 */
							addvlak_subdiv(evl, 3+4, 4+4, 1+4, 0, 0);
							evl->v4= e3->vn;
							evl->v1= e1->vn;
							set_wuv(4, evl, 1+4, 3, 3, 3+4);
						}
						else if(test==11) { /* 1,2,&4 */
							addvlak_subdiv(evl, 4+4, 1+4, 2+4, 0, 0);
							evl->v1= e4->vn;
							evl->v2= e2->vn;
							set_wuv(4, evl, 4+4, 2+4, 3, 4);
						}
					}
					evl->e1= addedgelist(evl->v1, evl->v2, evl->e1);
					evl->e2= addedgelist(evl->v2, evl->v3, evl->e2);					
					if(evl->v4) evl->e3= addedgelist(evl->v3, evl->v4, evl->e3);
					else evl->e3= addedgelist(evl->v3, evl->v1, evl->e3);
					if(evl->v4) evl->e4= addedgelist(evl->v4, evl->v1, evl->e4);
					else evl->e4= NULL;
				}
			}
		}
		evl= evl->prev;
	}

	/* remove all old edges, if needed make new ones */
	eed= em->edges.first;
	while(eed) {
		nexted= eed->next;
		if( eed->vn ) {
			eed->vn->f |= 16;			
			if(eed->f==0) {  /* not used in face */				
				addedgelist(eed->v1, eed->vn, eed);
				addedgelist(eed->vn, eed->v2, eed);
			}						
			remedge(eed);
			free_editedge(eed);
		}
		eed= nexted;
	}
	countall();
	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
}

void adduplicateflag(int flag)
{
	EditMesh *em = G.editMesh;
	/* old verts have flag 128 set, and flag 'flag' cleared
	   new verts have flag 'flag' set */
	EditVert *eve, *v1, *v2, *v3, *v4;
	EditEdge *eed;
	EditVlak *evl;

	/* vertices first */
	eve= em->verts.last;
	while(eve) {
		eve->f&= ~128;
		if(eve->f & flag) {
			v1= addvertlist(eve->co);
			v1->f= eve->f;
			eve->f-= flag;
			eve->f|= 128;
			eve->vn= v1;
#ifdef __NLA
			/* >>>>> FIXME: Copy deformation weight ? */
			v1->totweight = eve->totweight;
			if (eve->totweight){
				v1->dw = MEM_mallocN (eve->totweight * sizeof(MDeformWeight), "deformWeight");
				memcpy (v1->dw, eve->dw, eve->totweight * sizeof(MDeformWeight));
			}
			else
				v1->dw=NULL;
#endif
		}
		eve= eve->prev;
	}
	eed= em->edges.first;
	while(eed) {
		if( (eed->v1->f & 128) && (eed->v2->f & 128) ) {
			v1= eed->v1->vn;
			v2= eed->v2->vn;
			addedgelist(v1, v2, eed);
		}
		eed= eed->next;
	}

	/* then dupicate faces */
	evl= em->faces.first;
	while(evl) {
		if( (evl->v1->f & 128) && (evl->v2->f & 128) && (evl->v3->f & 128) ) {
			if(evl->v4) {
				if(evl->v4->f & 128) {
					v1= evl->v1->vn;
					v2= evl->v2->vn;
					v3= evl->v3->vn;
					v4= evl->v4->vn;
					addvlaklist(v1, v2, v3, v4, evl);
				}
			}
			else {
				v1= evl->v1->vn;
				v2= evl->v2->vn;
				v3= evl->v3->vn;
				addvlaklist(v1, v2, v3, 0, evl);
			}
		}
		evl= evl->next;
	}
}

static void delvlakflag(int flag)
{
	EditMesh *em = G.editMesh;
	/* delete all faces with 'flag', including edges and loose vertices */
	/* in vertices the 'flag' is cleared */
	EditVert *eve,*nextve;
	EditEdge *eed, *nexted;
	EditVlak *evl,*nextvl;

	eed= em->edges.first;
	while(eed) {
		eed->f= 0;
		eed= eed->next;
	}

	evl= em->faces.first;
	while(evl) {
		nextvl= evl->next;
		if(vlakselectedAND(evl, flag)) {
			
			evl->e1->f= 1;
			evl->e2->f= 1;
			evl->e3->f= 1;
			if(evl->e4) {
				evl->e4->f= 1;
			}
								
			BLI_remlink(&em->faces, evl);
			free_editvlak(evl);
		}
		evl= nextvl;
	}
	/* all faces with 1, 2 (3) vertices selected: make sure we keep the edges */
	evl= em->faces.first;
	while(evl) {
		evl->e1->f= 0;
		evl->e2->f= 0;
		evl->e3->f= 0;
		if(evl->e4) {
			evl->e4->f= 0;
		}

		evl= evl->next;
	}
	
	/* test all edges for vertices with 'flag', and clear */
	eed= em->edges.first;
	while(eed) {
		nexted= eed->next;
		if(eed->f==1) {
			remedge(eed);
			free_editedge(eed);
		}
		else if( (eed->v1->f & flag) || (eed->v2->f & flag) ) {
			eed->v1->f&= ~flag;
			eed->v2->f&= ~flag;
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

void extrude_mesh(void)
{
	short a;

	TEST_EDITMESH

	if(okee("Extrude")==0) return;
	
	waitcursor(1);
	undo_push_mesh("Extrude");
	
	a= extrudeflag(1,1);
	waitcursor(0);
	if(a==0) {
		error("No valid vertices are selected");
	}
	else {
		countall();  /* for G.totvert in calc_meshverts() */
		calc_meshverts();
		transform('d');
	}

}

void adduplicate_mesh(void)
{

	TEST_EDITMESH

	waitcursor(1);
	undo_push_mesh("Duplicate");
	adduplicateflag(1);
	waitcursor(0);
	countall();  /* for G.totvert in calc_meshverts() */
	transform('d');
}

void split_mesh(void)
{

	TEST_EDITMESH

	if(okee(" Split ")==0) return;

	waitcursor(1);
	undo_push_mesh("Split");
	/* make duplicate first */
	adduplicateflag(1);
	/* old faces have 3x flag 128 set, delete them */
	delvlakflag(128);

	waitcursor(0);

	countall();
	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
}


void separatemenu(void)
{
	short event;

	event = pupmenu("Separate (No undo!) %t|Selected%x1|All Loose Parts%x2");
	
	if (event==0) return;
	waitcursor(1);
	
	switch (event) {

		case 1: 
	    		separate_mesh();		    
	    		break;
		case 2:	    	    	    
			separate_mesh_loose();	    	    
			break;
	}
	waitcursor(0);
}


void separate_mesh(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve, *v1;
	EditEdge *eed, *e1;
	EditVlak *evl, *vl1;
	Object *oldob;
	Mesh *me, *men;
	Base *base, *oldbase;
	ListBase edve, eded, edvl;
	float trans[9];
	int ok, flag;
	
	TEST_EDITMESH	

	waitcursor(1);
	
	me= get_mesh(G.obedit);
	if(me->key) {
		error("Can't separate with vertex keys");
		return;
	}
	
	/* we are going to abuse the system as follows:
	 * 1. add a duplicate object: this will be the new one, we remember old pointer
	 * 2: then do a split if needed.
	 * 3. put apart: all NOT selected verts, edges, faces
	 * 4. call loadobeditdata(): this will be the new object
	 * 5. freelist en oude verts, eds, vlakken weer terughalen
	 */
	
	/* make only obedit selected */
	base= FIRSTBASE;
	while(base) {
		if(base->lay & G.vd->lay) {
			if(base->object==G.obedit) base->flag |= SELECT;
			else base->flag &= ~SELECT;
		}
		base= base->next;
	}
	
	/* testen for split */
	ok= 0;
	eed= em->edges.first;
	while(eed) {
		flag= (eed->v1->f & 1)+(eed->v2->f & 1);
		if(flag==1) {
			ok= 1;
			break;
		}
		eed= eed->next;
	}
	if(ok) {
		/* SPLIT: first make duplicate */
		adduplicateflag(1);
		/* SPLIT: old faces have 3x flag 128 set, delete these ones */
		delvlakflag(128);
	}
	
	/* set apart: everything that is not selected */
	edve.first= edve.last= eded.first= eded.last= edvl.first= edvl.last= 0;
	eve= em->verts.first;
	while(eve) {
		v1= eve->next;
		if((eve->f & 1)==0) {
			BLI_remlink(&em->verts, eve);
			BLI_addtail(&edve, eve);
		}
		eve= v1;
	}
	eed= em->edges.first;
	while(eed) {
		e1= eed->next;
		if( (eed->v1->f & 1)==0 || (eed->v2->f & 1)==0 ) {
			BLI_remlink(&em->edges, eed);
			BLI_addtail(&eded, eed);
		}
		eed= e1;
	}
	evl= em->faces.first;
	while(evl) {
		vl1= evl->next;
		if( (evl->v1->f & 1)==0 || (evl->v2->f & 1)==0 || (evl->v3->f & 1)==0 ) {
			BLI_remlink(&em->faces, evl);
			BLI_addtail(&edvl, evl);
		}
		evl= vl1;
	}
	
	oldob= G.obedit;
	oldbase= BASACT;
	
	trans[0]=trans[1]=trans[2]=trans[3]=trans[4]=trans[5]= 0.0;
	trans[6]=trans[7]=trans[8]= 1.0;
	G.qual |= LR_ALTKEY;	/* patch to make sure we get a linked duplicate */
	adduplicate(trans);
	G.qual &= ~LR_ALTKEY;
	
	G.obedit= BASACT->object;	/* basact was set in adduplicate()  */

	men= copy_mesh(me);
	set_mesh(G.obedit, men);
	/* because new mesh is a copy: reduce user count */
	men->id.us--;
	
	load_editMesh();
	
	BASACT->flag &= ~SELECT;
	
	makeDispList(G.obedit);
	free_editMesh();
	
	em->verts= edve;
	em->edges= eded;
	em->faces= edvl;
	
	/* hashedges are freed now, make new! */
	eed= em->edges.first;
	while(eed) {
		if( findedgelist(eed->v1, eed->v2)==NULL )
			insert_hashedge(eed);
		eed= eed->next;
	}
	
	G.obedit= oldob;
	BASACT= oldbase;
	BASACT->flag |= SELECT;
	
	waitcursor(0);

	countall();
	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);

}

void separate_mesh_loose(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve, *v1;
	EditEdge *eed, *e1;
	EditVlak *evl, *vl1;
	Object *oldob;
	Mesh *me, *men;
	Base *base, *oldbase;
	ListBase edve, eded, edvl;
	float trans[9];
	int ok, vertsep=0, flag;	
	short done=0, check=1;
		
	TEST_EDITMESH
	waitcursor(1);	
	
	/* we are going to abuse the system as follows:
	 * 1. add a duplicate object: this will be the new one, we remember old pointer
	 * 2: then do a split if needed.
	 * 3. put apart: all NOT selected verts, edges, faces
	 * 4. call loadobeditdata(): this will be the new object
	 * 5. freelist en oude verts, eds, vlakken weer terughalen
	 */
			
	
			
	while(!done){		
		vertsep=check=1;
		
		countall();
		
		me= get_mesh(G.obedit);
		if(me->key) {
			error("Can't separate a mesh with vertex keys");
			return;
		}		
		
		/* make only obedit selected */
		base= FIRSTBASE;
		while(base) {
			if(base->lay & G.vd->lay) {
				if(base->object==G.obedit) base->flag |= SELECT;
				else base->flag &= ~SELECT;
			}
			base= base->next;
		}		
		
		/*--------- Select connected-----------*/		
		//sel= 3;
		/* clear test flags */
		eve= em->verts.first;
		while(eve) {
			eve->f&= ~1;			
			eve= eve->next;
		}
		
		/* Select a random vert to start with */
		eve= em->verts.first;
		eve->f |= 1;
		
		while(check==1) {
			check= 0;			
			eed= em->edges.first;			
			while(eed) {				
				if(eed->h==0) {
					if(eed->v1->f & 1) {
						if( (eed->v2->f & 1)==0 ) {
							eed->v2->f |= 1;
							vertsep++;
							check= 1;
						}
					}
					else if(eed->v2->f & 1) {
						if( (eed->v1->f & 1)==0 ) {
							eed->v1->f |= 1;
							vertsep++;
							check= 1;
						}
					}
				}
				eed= eed->next;				
			}
		}		
		/*----------End of select connected--------*/
		
		
		/* If the amount of vertices that is about to be split == the total amount 
		   of verts in the mesh, it means that there is only 1 unconnected object, so we don't have to separate
		*/
		if(G.totvert==vertsep)done=1;				
		else{			
			/* Test for splitting: Separate selected */
			ok= 0;
			eed= em->edges.first;
			while(eed) {
				flag= (eed->v1->f & 1)+(eed->v2->f & 1);
				if(flag==1) {
					ok= 1;
					break;
				}
				eed= eed->next;
			}
			if(ok) {
				/* SPLIT: first make duplicate */
				adduplicateflag(1);
				/* SPLIT: old faces have 3x flag 128 set, delete these ones */
				delvlakflag(128);
			}	
			
			
			
			/* set apart: everything that is not selected */
			edve.first= edve.last= eded.first= eded.last= edvl.first= edvl.last= 0;
			eve= em->verts.first;
			while(eve) {
				v1= eve->next;
				if((eve->f & 1)==0) {
					BLI_remlink(&em->verts, eve);
					BLI_addtail(&edve, eve);
				}
				eve= v1;
			}
			eed= em->edges.first;
			while(eed) {
				e1= eed->next;
				if( (eed->v1->f & 1)==0 || (eed->v2->f & 1)==0 ) {
					BLI_remlink(&em->edges, eed);
					BLI_addtail(&eded, eed);
				}
				eed= e1;
			}
			evl= em->faces.first;
			while(evl) {
				vl1= evl->next;
				if( (evl->v1->f & 1)==0 || (evl->v2->f & 1)==0 || (evl->v3->f & 1)==0 ) {
					BLI_remlink(&em->faces, evl);
					BLI_addtail(&edvl, evl);
				}
				evl= vl1;
			}
			
			oldob= G.obedit;
			oldbase= BASACT;
			
			trans[0]=trans[1]=trans[2]=trans[3]=trans[4]=trans[5]= 0.0;
			trans[6]=trans[7]=trans[8]= 1.0;
			G.qual |= LR_ALTKEY;	/* patch to make sure we get a linked duplicate */
			adduplicate(trans);
			G.qual &= ~LR_ALTKEY;
			
			G.obedit= BASACT->object;	/* basact was set in adduplicate()  */
		
			men= copy_mesh(me);
			set_mesh(G.obedit, men);
			/* because new mesh is a copy: reduce user count */
			men->id.us--;
			
			load_editMesh();
			
			BASACT->flag &= ~SELECT;
			
			makeDispList(G.obedit);
			free_editMesh();
			
			em->verts= edve;
			em->edges= eded;
			em->faces= edvl;
			
			/* hashedges are freed now, make new! */
			eed= em->edges.first;
			while(eed) {
				if( findedgelist(eed->v1, eed->v2)==NULL )
					insert_hashedge(eed);
				eed= eed->next;
			}
			
			G.obedit= oldob;
			BASACT= oldbase;
			BASACT->flag |= SELECT;	
					
		}		
	}
	
	/* unselect the vertices that we (ab)used for the separation*/
	eve= em->verts.first;
	while(eve) {
		eve->f&= ~1;			
		eve= eve->next;
	}
	
	waitcursor(0);
	countall();
	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);	
}


void extrude_repeat_mesh(int steps, float offs)
{
	float dvec[3], tmat[3][3], bmat[3][3];
	short a,ok;

	TEST_EDITMESH
	waitcursor(1);
	
	undo_push_mesh("Extrude Repeat");

	/* dvec */
	dvec[0]= G.vd->persinv[2][0];
	dvec[1]= G.vd->persinv[2][1];
	dvec[2]= G.vd->persinv[2][2];
	Normalise(dvec);
	dvec[0]*= offs;
	dvec[1]*= offs;
	dvec[2]*= offs;

	/* base correction */
	Mat3CpyMat4(bmat, G.obedit->obmat);
	Mat3Inv(tmat, bmat);
	Mat3MulVecfl(tmat, dvec);

	for(a=0;a<steps;a++) {
		ok= extrudeflag(1,1);
		if(ok==0) {
			error("No valid vertices are selected");
			break;
		}
		translateflag(1, dvec);
	}

	countall();
	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
	waitcursor(0);
}

void spin_mesh(int steps,int degr,float *dvec, int mode)
{
	EditMesh *em = G.editMesh;
	EditVert *eve,*nextve;
	float *curs, si,n[3],q[4],cmat[3][3],imat[3][3], tmat[3][3];
	float cent[3],bmat[3][3];
	float phi;
	short a,ok;

	TEST_EDITMESH
	
	waitcursor(1);
	
	undo_push_mesh("Spin");

	/* imat and centre and size */
	Mat3CpyMat4(bmat, G.obedit->obmat);
	Mat3Inv(imat,bmat);

	curs= give_cursor();
	VECCOPY(cent, curs);
	cent[0]-= G.obedit->obmat[3][0];
	cent[1]-= G.obedit->obmat[3][1];
	cent[2]-= G.obedit->obmat[3][2];
	Mat3MulVecfl(imat, cent);

	phi= degr*M_PI/360.0;
	phi/= steps;
	if(editbutflag & B_CLOCKWISE) phi= -phi;

	if(dvec) {
		n[0]=n[1]= 0.0;
		n[2]= 1.0;
	} else {
		n[0]= G.vd->viewinv[2][0];
		n[1]= G.vd->viewinv[2][1];
		n[2]= G.vd->viewinv[2][2];
		Normalise(n);
	}

	q[0]= cos(phi);
	si= sin(phi);
	q[1]= n[0]*si;
	q[2]= n[1]*si;
	q[3]= n[2]*si;
	QuatToMat3(q, cmat);

	Mat3MulMat3(tmat,cmat,bmat);
	Mat3MulMat3(bmat,imat,tmat);

	if(mode==0) if(editbutflag & B_KEEPORIG) adduplicateflag(1);
	ok= 1;

	for(a=0;a<steps;a++) {
		if(mode==0) ok= extrudeflag(1,1);
		else adduplicateflag(1);
		if(ok==0) {
			error("No valid vertices are selected");
			break;
		}
		rotateflag(1, cent, bmat);
		if(dvec) {
			Mat3MulVecfl(bmat,dvec);
			translateflag(1,dvec);
		}
	}

	waitcursor(0);
	if(ok==0) {
		/* no vertices or only loose ones selected, remove duplicates */
		eve= em->verts.first;
		while(eve) {
			nextve= eve->next;
			if(eve->f & 1) {
				BLI_remlink(&em->verts,eve);
				free_editvert(eve);
			}
			eve= nextve;
		}
	}
	countall();
	recalc_editnormals();
	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
}

void screw_mesh(int steps,int turns)
{
	EditMesh *em = G.editMesh;
	EditVert *eve,*v1=0,*v2=0;
	EditEdge *eed;
	float dvec[3], nor[3];

	TEST_EDITMESH

	/* first condition: we need frontview! */
	if(G.vd->view!=1) {
		error("Must be in Front View");
		return;
	}
	
	undo_push_mesh("Screw");
	
	/* clear flags */
	eve= em->verts.first;
	while(eve) {
		eve->f1= 0;
		eve= eve->next;
	}
	/* edges set flags in verts */
	eed= em->edges.first;
	while(eed) {
		if(eed->v1->f & 1) {
			if(eed->v2->f & 1) {
				/* watch: f1 is a byte */
				if(eed->v1->f1<2) eed->v1->f1++;
				if(eed->v2->f1<2) eed->v2->f1++;
			}
		}
		eed= eed->next;
	}
	/* find two vertices with eve->f1==1, more or less is wrong */
	eve= em->verts.first;
	while(eve) {
		if(eve->f1==1) {
			if(v1==0) v1= eve;
			else if(v2==0) v2= eve;
			else {
				v1=0;
				break;
			}
		}
		eve= eve->next;
	}
	if(v1==0 || v2==0) {
		error("No curve is selected");
		return;
	}

	/* calculate dvec */
	dvec[0]= ( (v1->co[0]- v2->co[0]) )/(steps);
	dvec[1]= ( (v1->co[1]- v2->co[1]) )/(steps);
	dvec[2]= ( (v1->co[2]- v2->co[2]) )/(steps);

	VECCOPY(nor, G.obedit->obmat[2]);

	if(nor[0]*dvec[0]+nor[1]*dvec[1]+nor[2]*dvec[2]>0.000) {
		dvec[0]= -dvec[0];
		dvec[1]= -dvec[1];
		dvec[2]= -dvec[2];
	}

	spin_mesh(turns*steps, turns*360, dvec, 0);

}

void selectswap_mesh(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;

	eve= em->verts.first;
	while(eve) {
		if(eve->h==0) {
			if(eve->f & 1) eve->f&= ~1;
			else eve->f|= 1;
		}
		eve= eve->next;
	}
	countall();
	allqueue(REDRAWVIEW3D, 0);

}

/* *******************************  ADD  ********************* */

void addvert_mesh(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve,*v1=0;
	float *curs, mat[3][3],imat[3][3];

	TEST_EDITMESH

	Mat3CpyMat4(mat, G.obedit->obmat);
	Mat3Inv(imat, mat);

	v1= em->verts.first;
	while(v1) {
		if(v1->f & 1) break;
		v1= v1->next;
	}
	eve= v1;	/* prevent there are more selected */
	while(eve) {
		eve->f&= ~1;
		eve= eve->next;
	}

	eve= addvertlist(0);
	
	curs= give_cursor();
	VECCOPY(eve->co, curs);
	eve->xs= G.vd->mx;
	eve->ys= G.vd->my;
	VecSubf(eve->co, eve->co, G.obedit->obmat[3]);

	Mat3MulVecfl(imat, eve->co);
	eve->f= 1;

	if(v1) {
		addedgelist(v1, eve, NULL);
		v1->f= 0;
	}
	countall();
	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
	
	while(get_mbut()&R_MOUSE);

}

void addedgevlak_mesh(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve, *neweve[4];
	EditVlak *evl;
	float con1, con2, con3;
	short aantal=0;

	if( (G.vd->lay & G.obedit->lay)==0 ) return;

	/* how many selected ? */
	eve= em->verts.first;
	while(eve) {
		if(eve->f & 1) {
			aantal++;
			if(aantal>4) break;			
			neweve[aantal-1]= eve;
		}
		eve= eve->next;
	}
	if(aantal==2) {
		addedgelist(neweve[0], neweve[1], NULL);
		allqueue(REDRAWVIEW3D, 0);
		makeDispList(G.obedit);
		return;
	}
	if(aantal<2 || aantal>4) {
		error("Incorrect number of vertices to make edge/face");
		return;
	}

	evl= NULL; // check later

	if(aantal==3) {
		if(exist_vlak(neweve[0], neweve[1], neweve[2], 0)==0) {
			
			evl= addvlaklist(neweve[0], neweve[1], neweve[2], 0, NULL);

		}
		else error("The selected vertices already form a face");
	}
	else if(aantal==4) {
		if(exist_vlak(neweve[0], neweve[1], neweve[2], neweve[3])==0) {
		
			con1= convex(neweve[0]->co, neweve[1]->co, neweve[2]->co, neweve[3]->co);
			con2= convex(neweve[0]->co, neweve[2]->co, neweve[3]->co, neweve[1]->co);
			con3= convex(neweve[0]->co, neweve[3]->co, neweve[1]->co, neweve[2]->co);

			if(con1>=con2 && con1>=con3)
				evl= addvlaklist(neweve[0], neweve[1], neweve[2], neweve[3], NULL);
			else if(con2>=con1 && con2>=con3)
				evl= addvlaklist(neweve[0], neweve[2], neweve[3], neweve[1], NULL);
			else 
				evl= addvlaklist(neweve[0], neweve[2], neweve[1], neweve[3], NULL);

		}
		else error("The selected vertices already form a face");
	}
	
	if(evl) {	// now we're calculating direction of normal
		float inp;	
		/* dot product view mat with normal, should give info! */
	
		CalcNormFloat(evl->v1->co, evl->v2->co, evl->v3->co, evl->n);

					inp= evl->n[0]*G.vd->viewmat[0][2] + evl->n[1]*G.vd->viewmat[1][2] + evl->n[2]*G.vd->viewmat[2][2];

		if(inp < 0.0) flipvlak(evl);
	}
	
	countall();
	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
}

static void erase_edges(ListBase *l)
{
	EditEdge *ed, *nexted;
	
	ed = (EditEdge *) l->first;
	while(ed) {
		nexted= ed->next;
		if( (ed->v1->f & 1) || (ed->v2->f & 1) ) {
			remedge(ed);
			free_editedge(ed);
		}
		ed= nexted;
	}
}

static void erase_faces(ListBase *l)
{
	EditVlak *f, *nextf;

	f = (EditVlak *) l->first;

	while(f) {
		nextf= f->next;
		if( vlakselectedOR(f, 1) ) {
			BLI_remlink(l, f);
			free_editvlak(f);
		}
		f = nextf;
	}
}	

static void erase_vertices(ListBase *l)
{
	EditVert *v, *nextv;

	v = (EditVert *) l->first;
	while(v) {
		nextv= v->next;
		if(v->f & 1) {
			BLI_remlink(l, v);
			free_editvert(v);
		}
		v = nextv;
	}
}

void delete_mesh(void)
{
	EditMesh *em = G.editMesh;
	EditVlak *evl, *nextvl;
	EditVert *eve,*nextve;
	EditEdge *eed,*nexted;
	short event;
	int count;

	TEST_EDITMESH
	
	event= pupmenu("Erase %t|Vertices%x10|Edges%x1|Faces%x2|All%x3|Edges & Faces%x4|Only Faces%x5");
	if(event<1) return;

	if(event==10 ) {
		undo_push_mesh("Erase Vertices");
		erase_edges(&em->edges);
		erase_faces(&em->faces);
		erase_vertices(&em->verts);
	} 
	else if(event==4) {
		undo_push_mesh("Erase Edges & Faces");
		evl= em->faces.first;
		while(evl) {
			nextvl= evl->next;
			/* delete only faces with 2 or more vertices selected */
			count= 0;
			if(evl->v1->f & 1) count++;
			if(evl->v2->f & 1) count++;
			if(evl->v3->f & 1) count++;
			if(evl->v4 && (evl->v4->f & 1)) count++;
			if(count>1) {
				BLI_remlink(&em->faces, evl);
				free_editvlak(evl);
			}
			evl= nextvl;
		}
		eed= em->edges.first;
		while(eed) {
			nexted= eed->next;
			if( (eed->v1->f & 1) && (eed->v2->f & 1) ) {
				remedge(eed);
				free_editedge(eed);
			}
			eed= nexted;
		}
		evl= em->faces.first;
		while(evl) {
			nextvl= evl->next;
			event=0;
			if( evl->v1->f & 1) event++;
			if( evl->v2->f & 1) event++;
			if( evl->v3->f & 1) event++;
			if(evl->v4 && (evl->v4->f & 1)) event++;
			
			if(event>1) {
				BLI_remlink(&em->faces, evl);
				free_editvlak(evl);
			}
			evl= nextvl;
		}
	} 
	else if(event==1) {
		undo_push_mesh("Erase Edges");
		eed= em->edges.first;
		while(eed) {
			nexted= eed->next;
			if( (eed->v1->f & 1) && (eed->v2->f & 1) ) {
				remedge(eed);
				free_editedge(eed);
			}
			eed= nexted;
		}
		evl= em->faces.first;
		while(evl) {
			nextvl= evl->next;
			event=0;
			if( evl->v1->f & 1) event++;
			if( evl->v2->f & 1) event++;
			if( evl->v3->f & 1) event++;
			if(evl->v4 && (evl->v4->f & 1)) event++;
			
			if(event>1) {
				BLI_remlink(&em->faces, evl);
				free_editvlak(evl);
			}
			evl= nextvl;
		}
		/* to remove loose vertices: */
		eed= em->edges.first;
		while(eed) {
			if( eed->v1->f & 1) eed->v1->f-=1;
			if( eed->v2->f & 1) eed->v2->f-=1;
			eed= eed->next;
		}
		eve= em->verts.first;
		while(eve) {
			nextve= eve->next;
			if(eve->f & 1) {
				BLI_remlink(&em->verts,eve);
				free_editvert(eve);
			}
			eve= nextve;
		}

	}
	else if(event==2) {
		undo_push_mesh("Erase Faces");
		delvlakflag(1);
	}
	else if(event==3) {
		undo_push_mesh("Erase All");
		if(em->verts.first) free_vertlist(&em->verts);
		if(em->edges.first) free_edgelist(&em->edges);
		if(em->faces.first) free_vlaklist(&em->faces);
	}
	else if(event==5) {
		undo_push_mesh("Erase Only Faces");
		evl= em->faces.first;
		while(evl) {
			nextvl= evl->next;
			if(vlakselectedAND(evl, 1)) {
				BLI_remlink(&em->faces, evl);
				free_editvlak(evl);
			}
			evl= nextvl;
		}
	}

	countall();
	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
}



void add_primitiveMesh(int type)
{
	EditMesh *em = G.editMesh;
	Mesh *me;
	EditVert *eve, *v1=NULL, *v2, *v3, *v4=NULL, *vtop, *vdown;
	float *curs, d, dia, phi, phid, cent[3], vec[3], imat[3][3], mat[3][3];
	float q[4], cmat[3][3];
	static short tot=32, seg=32, subdiv=2;
	short a, b, ext=0, fill=0, totoud, newob=0;
	
	if(G.scene->id.lib) return;

	/* this function also comes from an info window */
	if ELEM(curarea->spacetype, SPACE_VIEW3D, SPACE_INFO); else return;
	if(G.vd==0) return;

	check_editmode(OB_MESH);
	
	G.f &= ~(G_VERTEXPAINT+G_FACESELECT+G_TEXTUREPAINT);
	setcursor_space(SPACE_VIEW3D, CURSOR_STD);

	/* if no obedit: new object and enter editmode */
	if(G.obedit==0) {
		/* add_object actually returns an object ! :-)
		But it also stores the added object struct in
		G.scene->basact->object (BASACT->object) */

		add_object_draw(OB_MESH);

		G.obedit= BASACT->object;
		
		where_is_object(G.obedit);
		
		make_editMesh();
		setcursor_space(SPACE_VIEW3D, CURSOR_EDIT);
		newob= 1;
	}
	me= G.obedit->data;
	
	/* deselectall */
	eve= em->verts.first;
	while(eve) {
		if(eve->f & 1) eve->f&= ~1;
		eve= eve->next;
	}

	totoud= tot; /* store, and restore when cube/plane */
	
	/* imat and centre and size */
	Mat3CpyMat4(mat, G.obedit->obmat);

	curs= give_cursor();
	VECCOPY(cent, curs);
	cent[0]-= G.obedit->obmat[3][0];
	cent[1]-= G.obedit->obmat[3][1];
	cent[2]-= G.obedit->obmat[3][2];

	if(type!= 11) {
		Mat3CpyMat4(imat, G.vd->viewmat);
		Mat3MulVecfl(imat, cent);
		Mat3MulMat3(cmat, imat, mat);
		Mat3Inv(imat,cmat);
	} else {
		Mat3Inv(imat, mat);
	}
	
	/* ext==extrudeflag, tot==amount of vertices in basis */

	switch(type) {
	case 0:		/* plane */
		tot= 4;
		ext= 0;
		fill= 1;
		if(newob) rename_id((ID *)G.obedit, "Plane");
		if(newob) rename_id((ID *)me, "Plane");
		break;
	case 1:		/* cube  */
		tot= 4;
		ext= 1;
		fill= 1;
		if(newob) rename_id((ID *)G.obedit, "Cube");
		if(newob) rename_id((ID *)me, "Cube");
		break;
	case 4:		/* circle  */
		if(button(&tot,3,100,"Vertices:")==0) return;
		ext= 0;
		fill= 0;
		if(newob) rename_id((ID *)G.obedit, "Circle");
		if(newob) rename_id((ID *)me, "Circle");
		break;
	case 5:		/* cylinder  */
		if(button(&tot,3,100,"Vertices:")==0) return;
		ext= 1;
		fill= 1;
		if(newob) rename_id((ID *)G.obedit, "Cylinder");
		if(newob) rename_id((ID *)me, "Cylinder");
		break;
	case 6:		/* tube  */
		if(button(&tot,3,100,"Vertices:")==0) return;
		ext= 1;
		fill= 0;
		if(newob) rename_id((ID *)G.obedit, "Tube");
		if(newob) rename_id((ID *)me, "Tube");
		break;
	case 7:		/* cone  */
		if(button(&tot,3,100,"Vertices:")==0) return;
		ext= 0;
		fill= 1;
		if(newob) rename_id((ID *)G.obedit, "Cone");
		if(newob) rename_id((ID *)me, "Cone");
		break;
	case 10:	/* grid */
		if(button(&tot,2,100,"X res:")==0) return;
		if(button(&seg,2,100,"Y res:")==0) return;
		if(newob) rename_id((ID *)G.obedit, "Grid");
		if(newob) rename_id((ID *)me, "Grid");
		break;
	case 11:	/* UVsphere */
		if(button(&seg,3,100,"Segments:")==0) return;
		if(button(&tot,3,100,"Rings:")==0) return;
		if(newob) rename_id((ID *)G.obedit, "Sphere");
		if(newob) rename_id((ID *)me, "Sphere");
		break;
	case 12:	/* Icosphere */
		if(button(&subdiv,1,5,"Subdivision:")==0) return;
		if(newob) rename_id((ID *)G.obedit, "Sphere");
		if(newob) rename_id((ID *)me, "Sphere");
		break;
	case 13:	/* Monkey */
		if(newob) rename_id((ID *)G.obedit, "Suzanne");
		if(newob) rename_id((ID *)me, "Suzanne");
		break;
	}

	dia= sqrt(2.0)*G.vd->grid;
	d= -G.vd->grid;
	phid= 2*M_PI/tot;
	phi= .25*M_PI;


	if(type<10) {	/* all types except grid, sphere... */
		if(ext==0 && type!=7) d= 0;
	
		/* vertices */
		vtop= vdown= v1= v2= 0;
		for(b=0; b<=ext; b++) {
			for(a=0; a<tot; a++) {
				
				vec[0]= cent[0]+dia*sin(phi);
				vec[1]= cent[1]+dia*cos(phi);
				vec[2]= cent[2]+d;
				
				Mat3MulVecfl(imat, vec);
				eve= addvertlist(vec);
				eve->f= 1;
				if(a==0) {
					if(b==0) v1= eve;
					else v2= eve;
				}
				phi+=phid;
			}
			d= -d;
		}
		/* centre vertices */
		if(fill && type>1) {
			VECCOPY(vec,cent);
			vec[2]-= -d;
			Mat3MulVecfl(imat,vec);
			vdown= addvertlist(vec);
			if(ext || type==7) {
				VECCOPY(vec,cent);
				vec[2]-= d;
				Mat3MulVecfl(imat,vec);
				vtop= addvertlist(vec);
			}
		} else {
			vdown= v1;
			vtop= v2;
		}
		if(vtop) vtop->f= 1;
		if(vdown) vdown->f= 1;
	
		/* top and bottom face */
		if(fill) {
			if(tot==4 && (type==0 || type==1)) {
				v3= v1->next->next;
				if(ext) v4= v2->next->next;
				
				addvlaklist(v3, v1->next, v1, v3->next, NULL);
				if(ext) addvlaklist(v2, v2->next, v4, v4->next, NULL);
				
			}
			else {
				v3= v1;
				v4= v2;
				for(a=1; a<tot; a++) {
					addvlaklist(vdown, v3, v3->next, 0, NULL);
					v3= v3->next;
					if(ext) {
						addvlaklist(vtop, v4, v4->next, 0, NULL);
						v4= v4->next;
					}
				}
				if(type>1) {
					addvlaklist(vdown, v3, v1, 0, NULL);
					if(ext) addvlaklist(vtop, v4, v2, 0, NULL);
				}
			}
		}
		else if(type==4) {  /* we need edges for a circle */
			v3= v1;
			for(a=1;a<tot;a++) {
				addedgelist(v3, v3->next, NULL);
				v3= v3->next;
			}
			addedgelist(v3, v1, NULL);
		}
		/* side faces */
		if(ext) {
			v3= v1;
			v4= v2;
			for(a=1; a<tot; a++) {
				addvlaklist(v3, v3->next, v4->next, v4, NULL);
				v3= v3->next;
				v4= v4->next;
			}
			addvlaklist(v3, v1, v2, v4, NULL);
		}
		else if(type==7) { /* cone */
			v3= v1;
			for(a=1; a<tot; a++) {
				addvlaklist(vtop, v3->next, v3, 0, NULL);
				v3= v3->next;
			}
			addvlaklist(vtop, v1, v3, 0, NULL);
		}
		
		if(type<2) tot= totoud;
		
	}
	else if(type==10) {	/*  grid */
		/* clear flags */
		eve= em->verts.first;
		while(eve) {
			eve->f= 0;
			eve= eve->next;
		}
		dia= G.vd->grid;
		/* one segment first: de X as */
		phi= -1.0; 
		phid= 2.0/((float)tot-1);
		for(a=0;a<tot;a++) {
			vec[0]= cent[0]+dia*phi;
			vec[1]= cent[1]- dia;
			vec[2]= cent[2];
			Mat3MulVecfl(imat,vec);
			eve= addvertlist(vec);
			eve->f= 1+2+4;
			if (a) addedgelist(eve->prev, eve, NULL);
			phi+=phid;
		}
		/* extrude and translate */
		vec[0]= vec[2]= 0.0;
		vec[1]= dia*phid;
		Mat3MulVecfl(imat, vec);
		for(a=0;a<seg-1;a++) {
			extrudeflag(2,0);
			translateflag(2, vec);
		}
	}
	else if(type==11) {	/*  UVsphere */
		float tmat[3][3];
		
		/* clear all flags */
		eve= em->verts.first;
		while(eve) {
			eve->f= 0;
			eve= eve->next;
		}
		
		/* one segment first */
		phi= 0; 
		phid/=2;
		for(a=0; a<=tot; a++) {
			vec[0]= cent[0]+dia*sin(phi);
			vec[1]= cent[1];
			vec[2]= cent[2]+dia*cos(phi);
			Mat3MulVecfl(imat,vec);
			eve= addvertlist(vec);
			eve->f= 1+2+4;
			if(a==0) v1= eve;
			else addedgelist(eve->prev, eve, NULL);
			phi+= phid;
		}
		
		/* extrude and rotate */
		phi= M_PI/seg;
		q[0]= cos(phi);
		q[3]= sin(phi);
		q[1]=q[2]= 0;
		QuatToMat3(q, cmat);
		Mat3MulMat3(tmat, cmat, mat);
		Mat3MulMat3(cmat, imat, tmat);
		
		for(a=0; a<seg; a++) {
			extrudeflag(2, 0);
			rotateflag(2, v1->co, cmat);
		}
		removedoublesflag(4, 0.0001);
	}
	else if(type==12) {	/* Icosphere */
		EditVert *eva[12];

		/* clear all flags */
		eve= em->verts.first;
		while(eve) {
			eve->f= 0;
			eve= eve->next;
		}
		dia/=200;
		for(a=0;a<12;a++) {
			vec[0]= dia*icovert[a][0];
			vec[1]= dia*icovert[a][1];
			vec[2]= dia*icovert[a][2];
			eva[a]= addvertlist(vec);
			eva[a]->f= 1+2;
		}
		for(a=0;a<20;a++) {
			v1= eva[ icovlak[a][0] ];
			v2= eva[ icovlak[a][1] ];
			v3= eva[ icovlak[a][2] ];
			addvlaklist(v1, v2, v3, 0, NULL);
		}

		dia*=200;
		for(a=1; a<subdiv; a++) subdivideflag(2, dia, 0);
		/* and now do imat */
		eve= em->verts.first;
		while(eve) {
			if(eve->f & 2) {
				VecAddf(eve->co,eve->co,cent);
				Mat3MulVecfl(imat,eve->co);
			}
			eve= eve->next;
		}
	} else if (type==13) {	/* Monkey */
		extern int monkeyo, monkeynv, monkeynf;
		extern signed char monkeyf[][4];
		extern signed char monkeyv[][3];
		EditVert **tv= MEM_mallocN(sizeof(*tv)*monkeynv*2, "tv");
		int i;

		for (i=0; i<monkeynv; i++) {
			float v[3];
			v[0]= (monkeyv[i][0]+127)/128.0, v[1]= monkeyv[i][1]/128.0, v[2]= monkeyv[i][2]/128.0;
			tv[i]= addvertlist(v);
			tv[monkeynv+i]= (fabs(v[0]= -v[0])<0.001)?tv[i]:addvertlist(v);
		}
		for (i=0; i<monkeynf; i++) {
			addvlaklist(tv[monkeyf[i][0]+i-monkeyo], tv[monkeyf[i][1]+i-monkeyo], tv[monkeyf[i][2]+i-monkeyo], (monkeyf[i][3]!=monkeyf[i][2])?tv[monkeyf[i][3]+i-monkeyo]:NULL, NULL);
			addvlaklist(tv[monkeynv+monkeyf[i][2]+i-monkeyo], tv[monkeynv+monkeyf[i][1]+i-monkeyo], tv[monkeynv+monkeyf[i][0]+i-monkeyo], (monkeyf[i][3]!=monkeyf[i][2])?tv[monkeynv+monkeyf[i][3]+i-monkeyo]:NULL, NULL);
		}

		MEM_freeN(tv);
	}
	
	if(type!=0 && type!=10) righthandfaces(1);
	countall();

	allqueue(REDRAWINFO, 1); 	/* 1, because header->win==0! */	
	allqueue(REDRAWALL, 0);
	makeDispList(G.obedit);

	if (type==13) notice("Oooh Oooh Oooh");
}

void vertexsmooth(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;
	float *adror, *adr, fac;
	float fvec[3];
	int teller=0;

	if(G.obedit==0) return;

	/* count */
	eve= em->verts.first;
	while(eve) {
		if(eve->f & 1) teller++;
		eve= eve->next;
	}
	if(teller==0) return;
	
	undo_push_mesh("Smooth");

	adr=adror= (float *)MEM_callocN(3*sizeof(float *)*teller, "vertsmooth");
	eve= em->verts.first;
	while(eve) {
		if(eve->f & 1) {
			eve->vn= (EditVert *)adr;
			eve->f1= 0;
			adr+= 3;
		}
		eve= eve->next;
	}
	
	eed= em->edges.first;
	while(eed) {
		if( (eed->v1->f & 1) || (eed->v2->f & 1) ) {
			fvec[0]= (eed->v1->co[0]+eed->v2->co[0])/2.0;
			fvec[1]= (eed->v1->co[1]+eed->v2->co[1])/2.0;
			fvec[2]= (eed->v1->co[2]+eed->v2->co[2])/2.0;
			
			if((eed->v1->f & 1) && eed->v1->f1<255) {
				eed->v1->f1++;
				VecAddf((float *)eed->v1->vn, (float *)eed->v1->vn, fvec);
			}
			if((eed->v2->f & 1) && eed->v2->f1<255) {
				eed->v2->f1++;
				VecAddf((float *)eed->v2->vn, (float *)eed->v2->vn, fvec);
			}
		}
		eed= eed->next;
	}

	eve= em->verts.first;
	while(eve) {
		if(eve->f & 1) {
			if(eve->f1) {
				adr= (float *)eve->vn;
				fac= 0.5/(float)eve->f1;
				
				eve->co[0]= 0.5*eve->co[0]+fac*adr[0];
				eve->co[1]= 0.5*eve->co[1]+fac*adr[1];
				eve->co[2]= 0.5*eve->co[2]+fac*adr[2];
			}
			eve->vn= 0;
		}
		eve= eve->next;
	}
	MEM_freeN(adror);

	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
}

void vertexnoise(void)
{
	EditMesh *em = G.editMesh;
	extern float Tin;
	Material *ma;
	Tex *tex;
	EditVert *eve;
	float b2, ofs, vec[3];

	if(G.obedit==0) return;
	
	undo_push_mesh("Noise");
	
	ma= give_current_material(G.obedit, G.obedit->actcol);
	if(ma==0 || ma->mtex[0]==0 || ma->mtex[0]->tex==0) {
		return;
	}
	tex= ma->mtex[0]->tex;
	
	ofs= tex->turbul/200.0;
	
	eve= (struct EditVert *)em->verts.first;
	while(eve) {
		if(eve->f & 1) {
			
			if(tex->type==TEX_STUCCI) {
				
				b2= BLI_hnoise(tex->noisesize, eve->co[0], eve->co[1], eve->co[2]);
				if(tex->stype) ofs*=(b2*b2);
				vec[0]= 0.2*(b2-BLI_hnoise(tex->noisesize, eve->co[0]+ofs, eve->co[1], eve->co[2]));
				vec[1]= 0.2*(b2-BLI_hnoise(tex->noisesize, eve->co[0], eve->co[1]+ofs, eve->co[2]));
				vec[2]= 0.2*(b2-BLI_hnoise(tex->noisesize, eve->co[0], eve->co[1], eve->co[2]+ofs));
				
				VecAddf(eve->co, eve->co, vec);
			}
			else {
				
				externtex(ma->mtex[0], eve->co);
			
				eve->co[2]+= 0.05*Tin;
			}
		}
		eve= eve->next;
	}

	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
}

void hide_mesh(int swap)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;

	if(G.obedit==0) return;

	if(swap) {
		eve= em->verts.first;
		while(eve) {
			if((eve->f & 1)==0) {
				eve->xs= 3200;
				eve->h= 1;
			}
			eve= eve->next;
		}
	}
	else {
		eve= em->verts.first;
		while(eve) {
			if(eve->f & 1) {
				eve->f-=1;
				eve->xs= 3200;
				eve->h= 1;
			}
			eve= eve->next;
		}
	}
	eed= em->edges.first;
	while(eed) {
		if(eed->v1->h || eed->v2->h) eed->h= 1;
		else eed->h= 0;
		eed= eed->next;
	}

	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
}


void reveal_mesh(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;

	if(G.obedit==0) return;

	eve= em->verts.first;
	while(eve) {
		if(eve->h) {
			eve->h= 0;
			eve->f|=1;
		}
		eve= eve->next;
	}

	eed= em->edges.first;
	while(eed) {
		eed->h= 0;
		eed= eed->next;
	}

	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
}

static float convex(float *v1, float *v2, float *v3, float *v4)
{
	float cross[3], test[3];
	float inpr;
	
	CalcNormFloat(v1, v2, v3, cross);
	CalcNormFloat(v1, v3, v4, test);

	inpr= cross[0]*test[0]+cross[1]*test[1]+cross[2]*test[2];

	return inpr;
}

/* returns vertices of two adjacent triangles forming a quad 
   - can be righthand or lefthand

			4-----3
			|\    |
			| \ 2 | <- evl1
			|  \  | 
	  evl-> | 1 \ | 
			|    \| 
			1-----2

*/
#define VTEST(face, num, other) \
	(face->v##num != other->v1 && face->v##num != other->v2 && face->v##num != other->v3) 

static void givequadverts(EditVlak *evl, EditVlak *evl1, EditVert **v1, EditVert **v2, EditVert **v3, EditVert **v4, float **uv, unsigned int *col)
{
	if VTEST(evl, 1, evl1) {
	//if(evl->v1!=evl1->v1 && evl->v1!=evl1->v2 && evl->v1!=evl1->v3) {
		*v1= evl->v1;
		*v2= evl->v2;
		uv[0] = evl->tf.uv[0];
		uv[1] = evl->tf.uv[1];
		col[0] = evl->tf.col[0];
		col[1] = evl->tf.col[1];
	}
	else if VTEST(evl, 2, evl1) {
	//else if(evl->v2!=evl1->v1 && evl->v2!=evl1->v2 && evl->v2!=evl1->v3) {
		*v1= evl->v2;
		*v2= evl->v3;
		uv[0] = evl->tf.uv[1];
		uv[1] = evl->tf.uv[2];
		col[0] = evl->tf.col[1];
		col[1] = evl->tf.col[2];
	}
	else if VTEST(evl, 3, evl1) {
	// else if(evl->v3!=evl1->v1 && evl->v3!=evl1->v2 && evl->v3!=evl1->v3) {
		*v1= evl->v3;
		*v2= evl->v1;
		uv[0] = evl->tf.uv[2];
		uv[1] = evl->tf.uv[0];
		col[0] = evl->tf.col[2];
		col[1] = evl->tf.col[0];
	}
	
	if VTEST(evl1, 1, evl) {
	// if(evl1->v1!=evl->v1 && evl1->v1!=evl->v2 && evl1->v1!=evl->v3) {
		*v3= evl1->v1;
		uv[2] = evl1->tf.uv[0];
		col[2] = evl1->tf.col[0];

		*v4= evl1->v2;
		uv[3] = evl1->tf.uv[1];
		col[3] = evl1->tf.col[1];
/*
if(evl1->v2== *v2) {
			*v4= evl1->v3;
			uv[3] = evl1->tf.uv[2];
		} else {
			*v4= evl1->v2;
			uv[3] = evl1->tf.uv[1];
		}	
		*/
	}
	else if VTEST(evl1, 2, evl) {
	// else if(evl1->v2!=evl->v1 && evl1->v2!=evl->v2 && evl1->v2!=evl->v3) {
		*v3= evl1->v2;
		uv[2] = evl1->tf.uv[1];
		col[2] = evl1->tf.col[1];

		*v4= evl1->v3;
		uv[3] = evl1->tf.uv[2];
		col[3] = evl1->tf.col[2];
/*
if(evl1->v3== *v2) {
			*v4= evl1->v1;
			uv[3] = evl1->tf.uv[0];
		} else {	
			*v4= evl1->v3;
			uv[3] = evl1->tf.uv[2];
		}	
		*/
	}
	else if VTEST(evl1, 3, evl) {
	// else if(evl1->v3!=evl->v1 && evl1->v3!=evl->v2 && evl1->v3!=evl->v3) {
		*v3= evl1->v3;
		uv[2] = evl1->tf.uv[2];
		col[2] = evl1->tf.col[2];

		*v4= evl1->v1;
		uv[3] = evl1->tf.uv[0];
		col[3] = evl1->tf.col[0];
/*
if(evl1->v1== *v2) {
			*v4= evl1->v2;
			uv[3] = evl1->tf.uv[3];
		} else {	
			*v4= evl1->v1;
			uv[3] = evl1->tf.uv[0];
		}	
		*/
	}
	else {
		pupmenu("Wanna crash?%t|Yes Please!%x1");
		return;
	}
	
}



/* Helper functions for edge/quad edit features*/

static void untag_edges(EditVlak *f)
{
	f->e1->f = 0;
	f->e2->f = 0;
	if (f->e3) f->e3->f = 0;
	if (f->e4) f->e4->f = 0;
}

#if 0
static void mark_clear_edges(EditVlak *f)
{
	f->e1->f1 = 1;
	f->e2->f1 = 1;
	if (f->e3) f->e3->f1 = 1;
	if (f->e4) f->e4->f1 = 1;
}
#endif

static int count_edges(EditEdge *ed)
{
	int totedge = 0;
	while(ed) {
		ed->vn= 0;
		if( (ed->v1->f & 1) && (ed->v2->f & 1) ) totedge++;
		ed= ed->next;
	}
	return totedge;
}

/** remove and free list of tagged edges */
static void free_tagged_edgelist(EditEdge *eed)
{
	EditEdge *nexted;

	while(eed) {
		nexted= eed->next;
		if(eed->f1) {
			remedge(eed);
			free_editedge(eed);
		}
		eed= nexted;
	}	
}	
/** remove and free list of tagged faces */

static void free_tagged_facelist(EditVlak *evl)
{	
	EditMesh *em = G.editMesh;
	EditVlak *nextvl;

	while(evl) {
		nextvl= evl->next;
		if(evl->f1) {
			BLI_remlink(&em->faces, evl);
			free_editvlak(evl);
		}
		evl= nextvl;
	}
}	

typedef EditVlak *EVPtr;
typedef EVPtr EVPTuple[2];

/** builds EVPTuple array evla of face tuples (in fact pointers to EditVlaks)
    sharing one edge.
	arguments: selected edge list, face list.
	Edges will also be tagged accordingly (see eed->f)          */

static int collect_quadedges(EVPTuple *evla, EditEdge *eed, EditVlak *evl)
{
	int i = 0;
	EditEdge *e1, *e2, *e3;
	EVPtr *evp;

	/* run through edges, if selected, set pointer edge-> facearray */
	while(eed) {
		eed->f= 0;
		eed->f1= 0;
		if( (eed->v1->f & 1) && (eed->v2->f & 1) ) {
			eed->vn= (EditVert *) (&evla[i]);
			i++;
		}
		eed= eed->next;
	}
		
	
	/* find edges pointing to 2 faces by procedure:
	
	- run through faces and their edges, increase
	  face counter e->f for each face 
	*/

	while(evl) {
		evl->f1= 0;
		if(evl->v4==0) {  /* if triangle */
			if(vlakselectedAND(evl, 1)) {
				
				e1= evl->e1;
				e2= evl->e2;
				e3= evl->e3;
				if(e1->f<3) {
					if(e1->f<2) {
						evp= (EVPtr *) e1->vn;
						evp[(int)e1->f]= evl;
					}
					e1->f+= 1;
				}
				if(e2->f<3) {
					if(e2->f<2) {
						evp= (EVPtr *) e2->vn;
						evp[(int)e2->f]= evl;
					}
					e2->f+= 1;
				}
				if(e3->f<3) {
					if(e3->f<2) {
						evp= (EVPtr *) e3->vn;
						evp[(int)e3->f]= evl;
					}
					e3->f+= 1;
				}
			}
		}
		evl= evl->next;
	}
	return i;
}


void join_triangles(void)
{
	EditMesh *em = G.editMesh;
	EditVert *v1, *v2, *v3, *v4;
	EditVlak *evl, *w;
	EVPTuple *evlar;
	EVPtr *evla;
	EditEdge *eed, *nexted;
	int totedge, ok;
	float *uv[4];
	unsigned int col[4];


	totedge = count_edges(em->edges.first);
	if(totedge==0) return;

	undo_push_mesh("Convert Triangles to Quads");
	
	evlar= (EVPTuple *) MEM_callocN(totedge * sizeof(EVPTuple), "jointris");

	ok = collect_quadedges(evlar, em->edges.first, em->faces.first);
	if (G.f & G_DEBUG) {
		printf("Edges selected: %d\n", ok);
	}	

	eed= em->edges.first;
	while(eed) {
		nexted= eed->next;
		
		if(eed->f==2) {  /* points to 2 faces */
			
			evla= (EVPtr *) eed->vn;
			
			/* don't do it if flagged */

			ok= 1;
			evl= evla[0];
			if(evl->e1->f1 || evl->e2->f1 || evl->e3->f1) ok= 0;
			evl= evla[1];
			if(evl->e1->f1 || evl->e2->f1 || evl->e3->f1) ok= 0;
			
			if(ok) {
				/* test convex */
				givequadverts(evla[0], evla[1], &v1, &v2, &v3, &v4, uv, col);

/*
		4-----3        4-----3
		|\    |        |     |
		| \ 1 |        |     |
		|  \  |  ->    |     |	
		| 0 \ |        |     | 
		|    \|        |     |
		1-----2        1-----2
*/
				/* make new faces */
				if( convex(v1->co, v2->co, v3->co, v4->co) > 0.01) {
					if(exist_vlak(v1, v2, v3, v4)==0) {
						w = addvlaklist(v1, v2, v3, v4, evla[0]);
						untag_edges(w);

						UVCOPY(w->tf.uv[0], uv[0]);
						UVCOPY(w->tf.uv[1], uv[1]);
						UVCOPY(w->tf.uv[2], uv[2]);
						UVCOPY(w->tf.uv[3], uv[3]);

						memcpy(w->tf.col, col, sizeof(w->tf.col));
					}
					/* tag as to-be-removed */
					FACE_MARKCLEAR(evla[0]);
					FACE_MARKCLEAR(evla[1]);
					eed->f1 = 1; 
				} /* endif test convex */
			}
		}
		eed= nexted;
	}
	free_tagged_edgelist(em->edges.first);
	free_tagged_facelist(em->faces.first);

	MEM_freeN(evlar);
	
	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);

}

/* quick hack, basically a copy of beauty_fill */
void edge_flip(void)
{
	EditMesh *em = G.editMesh;
	EditVert *v1, *v2, *v3, *v4;
	EditEdge *eed, *nexted;
	EditVlak *evl, *w;
	//void **evlar, **evla;
	EVPTuple *evlar;
	EVPtr *evla;

	float *uv[4];
	unsigned int col[4];

	int totedge, ok;
	
	/* - all selected edges with two faces
	 * - find the faces: store them in edges (using datablock)
	 * - per edge: - test convex
	 *			   - test edge: flip?
						- if true: remedge,  addedge, all edges at the edge get new face pointers
	 */

	totedge = count_edges(em->edges.first);
	if(totedge==0) return;

	undo_push_mesh("Flip Triangle Edges");
	
	/* temporary array for : edge -> face[1], face[2] */
	evlar= (EVPTuple *) MEM_callocN(totedge * sizeof(EVPTuple), "edgeflip");

	ok = collect_quadedges(evlar, em->edges.first, em->faces.first);
	
	eed= em->edges.first;
	while(eed) {
		nexted= eed->next;
		
		if(eed->f==2) {  /* points to 2 faces */
			
			evla= (EVPtr *) eed->vn;
			
			/* don't do it if flagged */

			ok= 1;
			evl= evla[0];
			if(evl->e1->f1 || evl->e2->f1 || evl->e3->f1) ok= 0;
			evl= evla[1];
			if(evl->e1->f1 || evl->e2->f1 || evl->e3->f1) ok= 0;
			
			if(ok) {
				/* test convex */
				givequadverts(evla[0], evla[1], &v1, &v2, &v3, &v4, uv, col);

/*
		4-----3        4-----3
		|\    |        |    /|
		| \ 1 |        | 1 / |
		|  \  |  ->    |  /  |	
		| 0 \ |        | / 0 | 
		|    \|        |/    |
		1-----2        1-----2
*/
				/* make new faces */
				if (v1 && v2 && v3){
					if( convex(v1->co, v2->co, v3->co, v4->co) > 0.01) {
						if(exist_vlak(v1, v2, v3, v4)==0) {
							w = addvlaklist(v1, v2, v3, 0, evla[1]);
							
							untag_edges(w);

							UVCOPY(w->tf.uv[0], uv[0]);
							UVCOPY(w->tf.uv[1], uv[1]);
							UVCOPY(w->tf.uv[2], uv[2]);

							w->tf.col[0] = col[0]; w->tf.col[1] = col[1]; w->tf.col[2] = col[2]; 
							
							w = addvlaklist(v1, v3, v4, 0, evla[1]);
							untag_edges(w);

							UVCOPY(w->tf.uv[0], uv[0]);
							UVCOPY(w->tf.uv[1], uv[2]);
							UVCOPY(w->tf.uv[2], uv[3]);

							w->tf.col[0] = col[0]; w->tf.col[1] = col[2]; w->tf.col[2] = col[3]; 
							
							/* erase old faces and edge */
						}
						/* tag as to-be-removed */
						FACE_MARKCLEAR(evla[1]);
						FACE_MARKCLEAR(evla[0]);
						eed->f1 = 1; 
						
					} /* endif test convex */
				}
			}
		}
		eed= nexted;
	}

	/* clear tagged edges and faces: */
	free_tagged_edgelist(em->edges.first);
	free_tagged_facelist(em->faces.first);
		
	MEM_freeN(evlar);
	
	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
}
						
void beauty_fill(void)
{
	EditMesh *em = G.editMesh;
    EditVert *v1, *v2, *v3, *v4;
    EditEdge *eed, *nexted;
    EditEdge dia1, dia2;
    EditVlak *evl, *w;
    // void **evlar, **evla;
    EVPTuple *evlar;
    EVPtr *evla;
    float *uv[4];
    unsigned int col[4];
    float len1, len2, len3, len4, len5, len6, opp1, opp2, fac1, fac2;
    int totedge, ok, notbeauty=8, onedone;

	/* - all selected edges with two faces
		* - find the faces: store them in edges (using datablock)
		* - per edge: - test convex
		*			   - test edge: flip?
		*               - if true: remedge,  addedge, all edges at the edge get new face pointers
		*/
	
    totedge = count_edges(em->edges.first);
    if(totedge==0) return;

    if(okee("Beauty fill")==0) return;
    
    undo_push_mesh("Beauty Fill");

    /* temp block with face pointers */
    evlar= (EVPTuple *) MEM_callocN(totedge * sizeof(EVPTuple), "beautyfill");

    while (notbeauty) {
        notbeauty--;

        ok = collect_quadedges(evlar, em->edges.first, em->faces.first);

        /* there we go */
        onedone= 0;

        eed= em->edges.first;
        while(eed) {
            nexted= eed->next;

            if(eed->f==2) {

                evla = (EVPtr *) eed->vn;

                /* none of the faces should be treated before */
                ok= 1;
                evl= evla[0];
                if(evl->e1->f1 || evl->e2->f1 || evl->e3->f1) ok= 0;
                evl= evla[1];
                if(evl->e1->f1 || evl->e2->f1 || evl->e3->f1) ok= 0;

                if(ok) {
                    /* test convex */
                    givequadverts(evla[0], evla[1], &v1, &v2, &v3, &v4, uv, col);
                    if( convex(v1->co, v2->co, v3->co, v4->co) > -0.5) {

                        /* test edges */
                        if( ((long)v1) > ((long)v3) ) {
                            dia1.v1= v3;
                            dia1.v2= v1;
                        }
                        else {
                            dia1.v1= v1;
                            dia1.v2= v3;
                        }

                        if( ((long)v2) > ((long)v4) ) {
                            dia2.v1= v4;
                            dia2.v2= v2;
                        }
                        else {
                            dia2.v1= v2;
                            dia2.v2= v4;
                        }

                        /* testing rule:
                         * the area divided by the total edge lengths
                         */

                        len1= VecLenf(v1->co, v2->co);
                        len2= VecLenf(v2->co, v3->co);
                        len3= VecLenf(v3->co, v4->co);
                        len4= VecLenf(v4->co, v1->co);
                        len5= VecLenf(v1->co, v3->co);
                        len6= VecLenf(v2->co, v4->co);

                        opp1= AreaT3Dfl(v1->co, v2->co, v3->co);
                        opp2= AreaT3Dfl(v1->co, v3->co, v4->co);

                        fac1= opp1/(len1+len2+len5) + opp2/(len3+len4+len5);

                        opp1= AreaT3Dfl(v2->co, v3->co, v4->co);
                        opp2= AreaT3Dfl(v2->co, v4->co, v1->co);

                        fac2= opp1/(len2+len3+len6) + opp2/(len4+len1+len6);

                        ok= 0;
                        if(fac1 > fac2) {
                            if(dia2.v1==eed->v1 && dia2.v2==eed->v2) {
                                eed->f1= 1;
                                evl= evla[0];
                                evl->f1= 1;
                                evl= evla[1];
                                evl->f1= 1;

                                w= addvlaklist(v1, v2, v3, 0, evl);

								UVCOPY(w->tf.uv[0], uv[0]);
								UVCOPY(w->tf.uv[1], uv[1]);
								UVCOPY(w->tf.uv[2], uv[2]);

                                w->tf.col[0] = col[0]; w->tf.col[1] = col[1]; w->tf.col[2] = col[2];
                                w= addvlaklist(v1, v3, v4, 0, evl);

								UVCOPY(w->tf.uv[0], uv[0]);
								UVCOPY(w->tf.uv[1], uv[2]);
								UVCOPY(w->tf.uv[2], uv[3]);

                                w->tf.col[0] = col[0]; w->tf.col[1] = col[2]; w->tf.col[2] = col[3];

                                onedone= 1;
                            }
                        }
                        else if(fac1 < fac2) {
                            if(dia1.v1==eed->v1 && dia1.v2==eed->v2) {
                                eed->f1= 1;
                                evl= evla[0];
                                evl->f1= 1;
                                evl= evla[1];
                                evl->f1= 1;

                                w= addvlaklist(v2, v3, v4, 0, evl);

								UVCOPY(w->tf.uv[0], uv[1]);
								UVCOPY(w->tf.uv[1], uv[3]);
								UVCOPY(w->tf.uv[2], uv[4]);

                                w= addvlaklist(v1, v2, v4, 0, evl);

								UVCOPY(w->tf.uv[0], uv[0]);
								UVCOPY(w->tf.uv[1], uv[1]);
								UVCOPY(w->tf.uv[2], uv[3]);

                                onedone= 1;
                            }
                        }
                    }
                }

            }
            eed= nexted;
        }

        free_tagged_edgelist(em->edges.first);
        free_tagged_facelist(em->faces.first);

        if(onedone==0) break;
    }

    MEM_freeN(evlar);

    allqueue(REDRAWVIEW3D, 0);
    makeDispList(G.obedit);
}

/** tests whether selected mesh objects have tfaces */
static int testSelected_TfaceMesh(void)
{
	Base *base;
	Mesh *me;

	base = FIRSTBASE;
	while (base) {
		if TESTBASE(base) {
			if(base->object->type==OB_MESH) {
				me= base->object->data;
				if (me->tface) 
					return 1;
			}		
		}			
		base= base->next;
	}	
	return 0;
}	

void join_mesh(void)
{
	Base *base, *nextb;
	Object *ob;
	Material **matar, *ma;
	Mesh *me;
	MVert *mvert, *mvertmain;
	MEdge *medge = NULL, *medgemain;
	MFace *mface = NULL, *mfacemain;
	TFace *tface = NULL, *tfacemain;
	unsigned int *mcol=NULL, *mcolmain;
	float imat[4][4], cmat[4][4];
	int a, b, totcol, totedge=0, totvert=0, totface=0, ok=0, vertofs, map[MAXMAT];
	int hasedges=0;
#ifdef __NLA
	int	i, j, index, haskey=0;
	bDeformGroup *dg, *odg;
	MDeformVert *dvert, *dvertmain;
#endif
	
	if(G.obedit) return;
	
	ob= OBACT;
	if(!ob || ob->type!=OB_MESH) return;
	
	/* count */
	base= FIRSTBASE;
	while(base) {
		if TESTBASE(base) {
			if(base->object->type==OB_MESH) {
				me= base->object->data;
				totvert+= me->totvert;
				totface+= me->totface;
				if(me->medge) hasedges= 1;

				if(base->object == ob) ok= 1;

				if(me->key) {
					haskey= 1;
					break;
				}
			}
		}
		base= base->next;
	}
	
	if(haskey) {
		error("Can't join meshes with vertex keys");
		return;
	}
	/* that way the active object is always selected */ 
	if(ok==0) return;
	
	if(totvert==0 || totvert>MESH_MAX_VERTS) return;
	
	if(okee("Join selected meshes")==0) return;


	/* if needed add edges to other meshes */
	if(hasedges) {
		for(base= FIRSTBASE; base; base= base->next) {
			if TESTBASE(base) {
				if(base->object->type==OB_MESH) {
					me= base->object->data;
					if(me->medge==NULL) make_edges(me);
					totedge += me->totedge;
				}
			}
		}
	}
	
	/* new material indices and material array */
	matar= MEM_callocN(sizeof(void *)*MAXMAT, "join_mesh");
	totcol= ob->totcol;
	
	/* obact materials in new main array, is nicer start! */
	for(a=1; a<=ob->totcol; a++) {
		matar[a-1]= give_current_material(ob, a);
		id_us_plus((ID *)matar[a-1]);
		/* increase id->us : will be lowered later */
	}
	
	base= FIRSTBASE;
	while(base) {
		if TESTBASE(base) {
			if(ob!=base->object && base->object->type==OB_MESH) {
				me= base->object->data;
#ifdef __NLA
				// Join this object's vertex groups to the base one's
				for (dg=base->object->defbase.first; dg; dg=dg->next){
					/* See if this group exists in the object */
					for (odg=ob->defbase.first; odg; odg=odg->next){
						if (!strcmp(odg->name, dg->name)){
							break;
						}
					}
					if (!odg){
						odg = MEM_callocN (sizeof(bDeformGroup), "deformGroup");
						memcpy (odg, dg, sizeof(bDeformGroup));
						BLI_addtail(&ob->defbase, odg);
					}

				}
				if (ob->defbase.first && ob->actdef==0)
					ob->actdef=1;
#endif
				if(me->totvert) {
					for(a=1; a<=base->object->totcol; a++) {
						ma= give_current_material(base->object, a);
						if(ma) {
							for(b=0; b<totcol; b++) {
								if(ma == matar[b]) break;
							}
							if(b==totcol) {
								matar[b]= ma;
								ma->id.us++;
								totcol++;
							}
							if(totcol>=MAXMAT-1) break;
						}
					}
				}
			}
			if(totcol>=MAXMAT-1) break;
		}
		base= base->next;
	}

	me= ob->data;
	mvert= mvertmain= MEM_mallocN(totvert*sizeof(MVert), "joinmesh vert");

	if(totedge) medge= medgemain= MEM_callocN(totedge*sizeof(MEdge), "joinmesh edge");
	else medgemain= NULL;
	
	if (totface) mface= mfacemain= MEM_mallocN(totface*sizeof(MFace), "joinmesh face");
	else mfacemain= NULL;

	if(me->mcol) mcol= mcolmain= MEM_callocN(totface*4*sizeof(int), "joinmesh mcol");
	else mcolmain= NULL;

	/* if active object doesn't have Tfaces, but one in the selection does,
	   make TFaces for active, so we don't lose texture information in the
	   join process */
	if(me->tface || testSelected_TfaceMesh()) tface= tfacemain= MEM_callocN(totface*4*sizeof(TFace), "joinmesh4");
	else tfacemain= NULL;

#ifdef __NLA
	if(me->dvert)
		dvert= dvertmain= MEM_callocN(totvert*sizeof(MDeformVert), "joinmesh5");
	else dvert=dvertmain= NULL;
#endif

	vertofs= 0;
	
	/* inverse transorm all selected meshes in this object */
	Mat4Invert(imat, ob->obmat);
	
	base= FIRSTBASE;
	while(base) {
		nextb= base->next;
		if TESTBASE(base) {
			if(base->object->type==OB_MESH) {
				
				me= base->object->data;
				
				if(me->totvert) {
					
					memcpy(mvert, me->mvert, me->totvert*sizeof(MVert));
					
#ifdef __NLA
					copy_dverts(dvert, me->dvert, me->totvert);

					/* NEW VERSION */
					if (dvertmain){
						for (i=0; i<me->totvert; i++){
							for (j=0; j<dvert[i].totweight; j++){
								//	Find the old vertex group
								odg = BLI_findlink (&base->object->defbase, dvert[i].dw[j].def_nr);
								if(odg) {
									//	Search for a match in the new object
									for (dg=ob->defbase.first, index=0; dg; dg=dg->next, index++){
										if (!strcmp(dg->name, odg->name)){
											dvert[i].dw[j].def_nr = index;
											break;
										}
									}
								}
							}
						}
						dvert+=me->totvert;
					}

#endif
					if(base->object != ob) {
						/* watch this: switch matmul order really goes wrong */
						Mat4MulMat4(cmat, base->object->obmat, imat);
						
						a= me->totvert;
						while(a--) {
							Mat4MulVecfl(cmat, mvert->co);
							mvert++;
						}
					}
					else mvert+= me->totvert;
					
					if(mcolmain) {
						if(me->mcol) memcpy(mcol, me->mcol, me->totface*4*4);
						mcol+= 4*me->totface;
					}
				}
				if(me->totface) {
				
					/* make mapping for materials */
					memset(map, 0, 4*MAXMAT);
					for(a=1; a<=base->object->totcol; a++) {
						ma= give_current_material(base->object, a);
						if(ma) {
							for(b=0; b<totcol; b++) {
								if(ma == matar[b]) {
									map[a-1]= b;
									break;
								}
							}
						}
					}

					memcpy(mface, me->mface, me->totface*sizeof(MFace));
					
					a= me->totface;
					while(a--) {
						mface->v1+= vertofs;
						mface->v2+= vertofs;
						if(mface->v3) mface->v3+= vertofs;
						if(mface->v4) mface->v4+= vertofs;
						
						mface->mat_nr= map[(int)mface->mat_nr];
						
						mface++;
					}
					
					if(tfacemain) {
						if(me->tface) memcpy(tface, me->tface, me->totface*sizeof(TFace));
						tface+= me->totface;
					}
					
				}
				
				if(me->totedge) {
					memcpy(medge, me->medge, me->totedge*sizeof(MEdge));
					
					a= me->totedge;
					while(a--) {
						medge->v1+= vertofs;
						medge->v2+= vertofs;
						medge++;
					}
				}
				
				vertofs+= me->totvert;
				
				if(base->object!=ob) {
					free_and_unlink_base(base);
				}
			}
		}
		base= nextb;
	}
	
	me= ob->data;
	
	if(me->mvert) MEM_freeN(me->mvert);
	me->mvert= mvertmain;

	if(me->medge) MEM_freeN(me->medge);
	me->medge= medgemain;

	if(me->mface) MEM_freeN(me->mface);
	me->mface= mfacemain;

#ifdef __NLA
	if(me->dvert) free_dverts(me->dvert, me->totvert);
	me->dvert = dvertmain;
#endif

	if(me->mcol) MEM_freeN(me->mcol);
	me->mcol= (MCol *)mcolmain;
	
	if(me->tface) MEM_freeN(me->tface);
	me->tface= tfacemain;
	
	me->totvert= totvert;
	me->totedge= totedge;
	me->totface= totface;
	
	/* old material array */
	for(a=1; a<=ob->totcol; a++) {
		ma= ob->mat[a-1];
		if(ma) ma->id.us--;
	}
	for(a=1; a<=me->totcol; a++) {
		ma= me->mat[a-1];
		if(ma) ma->id.us--;
	}
	if(ob->mat) MEM_freeN(ob->mat);
	if(me->mat) MEM_freeN(me->mat);
	ob->mat= me->mat= 0;
	
	if(totcol) {
		me->mat= matar;
		ob->mat= MEM_callocN(sizeof(void *)*totcol, "join obmatar");
	}
	else MEM_freeN(matar);
	
	ob->totcol= me->totcol= totcol;
	ob->colbits= 0;
	
	/* other mesh users */
	test_object_materials((ID *)me);
	
	enter_editmode();
	exit_editmode(1);
	
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSSHADING, 0);
	makeDispList(G.obedit);

}

void clever_numbuts_mesh(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	
	eve= em->verts.first;
	while(eve) {
		if(eve->f & 1) break;
		eve= eve->next;
	}
	if(eve==0) return;

	add_numbut(0, NUM|FLO, "LocX:", -G.vd->far, G.vd->far, eve->co, 0);
	add_numbut(1, NUM|FLO, "LocY:", -G.vd->far, G.vd->far, eve->co+1, 0);
	add_numbut(2, NUM|FLO, "LocZ:", -G.vd->far, G.vd->far, eve->co+2, 0);
	
	do_clever_numbuts("Active Vertex", 3, REDRAW);
}


static void permutate(void *list, int num, int size, int *index)
{
	void *buf;
	int len;
	int i;

	len = num * size;

	buf = MEM_mallocN(len, "permutate");
	memcpy(buf, list, len);
	
	for (i = 0; i < num; i++) {
		memcpy((char *)list + (i * size), (char *)buf + (index[i] * size), size);
	}
	MEM_freeN(buf);
}

static MVert *mvertbase;
static MFace *mfacebase;

static int verg_mface(const void *v1, const void *v2)
{
	MFace *x1, *x2;

	MVert *ve1, *ve2;
	int i1, i2;

	i1 = ((int *) v1)[0];
	i2 = ((int *) v2)[0];
	
	x1 = mfacebase + i1;
	x2 = mfacebase + i2;

	ve1= mvertbase+x1->v1;
	ve2= mvertbase+x2->v1;
	
	if( ve1->co[2] > ve2->co[2] ) return 1;
	else if( ve1->co[2] < ve2->co[2]) return -1;
	return 0;
}


void sort_faces(void)
{
	Object *ob= OBACT;
	Mesh *me;
	
	int i, *index;
	
	if(ob==0) return;
	if(G.obedit) return;
	if(ob->type!=OB_MESH) return;
	
	if(okee("Sort faces in Z axis")==0) return;
	me= ob->data;
	if(me->totface==0) return;

/*	create index list */
	index = (int *) MEM_mallocN(sizeof(int) * me->totface, "sort faces");
	for (i = 0; i < me->totface; i++) {
		index[i] = i;
	}
	mvertbase= me->mvert;
	mfacebase = me->mface;

/* sort index list instead of faces itself 
   and apply this permutation to the face list plus
   to the texture faces */
	qsort(index, me->totface, sizeof(int), verg_mface);

	permutate(mfacebase, me->totface, sizeof(MFace), index);
	if (me->tface) 
		permutate(me->tface, me->totface, sizeof(TFace), index);

	MEM_freeN(index);

	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
}

void vertices_to_sphere(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	Object *ob= OBACT;
	float *curs, len, vec[3], cent[3], fac, facm, imat[3][3], bmat[3][3];
	int tot;
	short perc=100;
	
	if(ob==0) return;
	TEST_EDITMESH
	
	if(button(&perc, 1, 100, "Percentage:")==0) return;
	
	undo_push_mesh("To Sphere");
	
	fac= perc/100.0;
	facm= 1.0-fac;
	
	Mat3CpyMat4(bmat, ob->obmat);
	Mat3Inv(imat, bmat);

	/* centre */
	curs= give_cursor();
	cent[0]= curs[0]-ob->obmat[3][0];
	cent[1]= curs[1]-ob->obmat[3][1];
	cent[2]= curs[2]-ob->obmat[3][2];
	Mat3MulVecfl(imat, cent);

	len= 0.0;
	tot= 0;
	eve= em->verts.first;
	while(eve) {
		if(eve->f & 1) {
			tot++;
			len+= VecLenf(cent, eve->co);
		}
		eve= eve->next;
	}
	len/=tot;
	
	if(len==0.0) len= 10.0;
	
	eve= em->verts.first;
	while(eve) {
		if(eve->f & 1) {
			vec[0]= eve->co[0]-cent[0];
			vec[1]= eve->co[1]-cent[1];
			vec[2]= eve->co[2]-cent[2];
			
			Normalise(vec);
			
			eve->co[0]= fac*(cent[0]+vec[0]*len) + facm*eve->co[0];
			eve->co[1]= fac*(cent[1]+vec[1]*len) + facm*eve->co[1];
			eve->co[2]= fac*(cent[2]+vec[2]*len) + facm*eve->co[2];
			
		}
		eve= eve->next;
	}
	
	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
}

/* Got this from scanfill.c. You will need to juggle around the
 * callbacks for the scanfill.c code a bit for this to work. */
void fill_mesh(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve,*v1;
	EditEdge *eed,*e1,*nexted;
	EditVlak *evl,*nextvl;
	short ok;

	if(G.obedit==0 || (G.obedit->type!=OB_MESH)) return;

	waitcursor(1);

	undo_push_mesh("Fill");

	/* copy all selected vertices */
	eve= em->verts.first;
	while(eve) {
		if(eve->f & 1) {
			v1= BLI_addfillvert(eve->co);
			eve->vn= v1;
			v1->vn= eve;
			v1->h= 0;
		}
		eve= eve->next;
	}
	/* copy all selected edges */
	eed= em->edges.first;
	while(eed) {
		if( (eed->v1->f & 1) && (eed->v2->f & 1) ) {
			e1= BLI_addfilledge(eed->v1->vn, eed->v2->vn);
			e1->v1->h++; 
			e1->v2->h++;
		}
		eed= eed->next;
	}
	/* from all selected faces: remove vertices and edges verwijderen to prevent doubles */
	/* all edges add values, faces subtract,
	   then remove edges with vertices ->h<2 */
	evl= em->faces.first;
	ok= 0;
	while(evl) {
		nextvl= evl->next;
		if( vlakselectedAND(evl, 1) ) {
			evl->v1->vn->h--;
			evl->v2->vn->h--;
			evl->v3->vn->h--;
			if(evl->v4) evl->v4->vn->h--;
			ok= 1;
			
		}
		evl= nextvl;
	}
	if(ok) {	/* there are faces selected */
		eed= filledgebase.first;
		while(eed) {
			nexted= eed->next;
			if(eed->v1->h<2 || eed->v2->h<2) {
				BLI_remlink(&filledgebase,eed);
			}
			eed= nexted;
		}
	}

	/* to make edgefill work */
	BLI_setScanFillObjectRef(G.obedit);
	BLI_setScanFillColourRef(&G.obedit->actcol);

	ok= BLI_edgefill(0);

	/* printf("time: %d\n",(clock()-tijd)/1000); */

	if(ok) {
		evl= fillvlakbase.first;
		while(evl) {
			addvlaklist(evl->v1->vn, evl->v2->vn, evl->v3->vn, 0, evl);
			evl= evl->next;
		}
	}
	/* else printf("fill error\n"); */

	BLI_end_edgefill();

	waitcursor(0);

	countall();
	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
}

/* ***************** */

/* this one for NOT in editmode 

(only used by external modules, that is, until now by the 
python NMesh module) 

TODO: Probably it's better to convert the mesh into a EditMesh, call
vertexnormals() and convert it back to a Mesh again.

*/

void vertexnormals_mesh(Mesh *me, float *extverts)
{
	MVert *mvert;
	MFace *mface;
	float n1[3], n2[3], n3[3], n4[3], co[4], fac1, fac2, fac3, fac4, *temp;
	float *f1, *f2, *f3, *f4, xn, yn, zn, *normals;
	float *v1, *v2, *v3, *v4, len, vnor[3];
	int a, testflip;

	if(me->totvert==0) return;

	testflip= (me->flag & ME_NOPUNOFLIP)==0;
	if((me->flag & ME_TWOSIDED)==0) testflip= 0;	/* large angles */
	
	if(me->totface==0) {
		/* fake vertex normals for 'halopuno' (render option) */
		mvert= me->mvert;
		for(a=0; a<me->totvert; a++, mvert++) {
			VECCOPY(n1, mvert->co);
			Normalise(n1);
			mvert->no[0]= 32767.0*n1[0];
			mvert->no[1]= 32767.0*n1[1];
			mvert->no[2]= 32767.0*n1[2];
		}
		return;
	}

	normals= MEM_callocN(me->totvert*3*sizeof(float), "normals");
	
	/* calculate cosine angles, and add to vertex normal */
	mface= me->mface;
	mvert= me->mvert;
	for(a=0; a<me->totface; a++, mface++) {
		
		if(mface->v3==0) continue;
		
		if(extverts) {
			v1= extverts+3*mface->v1;
			v2= extverts+3*mface->v2;
			v3= extverts+3*mface->v3;
			v4= extverts+3*mface->v4;
		}
		else {		
			v1= (mvert+mface->v1)->co;
			v2= (mvert+mface->v2)->co;
			v3= (mvert+mface->v3)->co;
			v4= (mvert+mface->v4)->co;
		}
		
		VecSubf(n1, v2, v1);
		VecSubf(n2, v3, v2);
		Normalise(n1);
		Normalise(n2);

		if(mface->v4==0) {
			VecSubf(n3, v1, v3);
			Normalise(n3);
			
			co[0]= saacos(-n3[0]*n1[0]-n3[1]*n1[1]-n3[2]*n1[2]);
			co[1]= saacos(-n1[0]*n2[0]-n1[1]*n2[1]-n1[2]*n2[2]);
			co[2]= saacos(-n2[0]*n3[0]-n2[1]*n3[1]-n2[2]*n3[2]);
			
		}
		else {
			VecSubf(n3, v4, v3);
			VecSubf(n4, v1, v4);
			Normalise(n3);
			Normalise(n4);

			co[0]= saacos(-n4[0]*n1[0]-n4[1]*n1[1]-n4[2]*n1[2]);
			co[1]= saacos(-n1[0]*n2[0]-n1[1]*n2[1]-n1[2]*n2[2]);
			co[2]= saacos(-n2[0]*n3[0]-n2[1]*n3[1]-n2[2]*n3[2]);
			co[3]= saacos(-n3[0]*n4[0]-n3[1]*n4[1]-n3[2]*n4[2]);
		}
		
		CalcNormFloat(v1, v2, v3, vnor);
		
		temp= normals+3*mface->v1;
		if(testflip && contrpuntnorm(vnor, temp) ) co[0]= -co[0];
		temp[0]+= co[0]*vnor[0];
		temp[1]+= co[0]*vnor[1];
		temp[2]+= co[0]*vnor[2];
		
		temp= normals+3*mface->v2;
		if(testflip && contrpuntnorm(vnor, temp) ) co[1]= -co[1];
		temp[0]+= co[1]*vnor[0];
		temp[1]+= co[1]*vnor[1];
		temp[2]+= co[1]*vnor[2];
		
		temp= normals+3*mface->v3;
		if(testflip && contrpuntnorm(vnor, temp) ) co[2]= -co[2];
		temp[0]+= co[2]*vnor[0];
		temp[1]+= co[2]*vnor[1];
		temp[2]+= co[2]*vnor[2];
		
		if(mface->v4) {
			temp= normals+3*mface->v4;
			if(testflip && contrpuntnorm(vnor, temp) ) co[3]= -co[3];
			temp[0]+= co[3]*vnor[0];
			temp[1]+= co[3]*vnor[1];
			temp[2]+= co[3]*vnor[2];
		}
	}

	/* normalize vertex normals */
	mvert= me->mvert;
	for(a=0; a<me->totvert; a++, mvert++) {
		len= Normalise(normals+3*a);
		if(len!=0.0) {
			VECCOPY(n1, normals+3*a);
			Normalise(n1);

			mvert->no[0]= 32767.0*n1[0];
			mvert->no[1]= 32767.0*n1[1];
			mvert->no[2]= 32767.0*n1[2];
		}
	}
	
	/* vertex normal flipping flags, for during render */
	mface= me->mface;
	mvert= me->mvert;
	for(a=0; a<me->totface; a++, mface++) {
		mface->puno=0;			
		
		if(mface->v3==0) continue;
		
		if(extverts) {
			v1= extverts+3*mface->v1;
			v2= extverts+3*mface->v2;
			v3= extverts+3*mface->v3;
		}
		else {		
			v1= (mvert+mface->v1)->co;
			v2= (mvert+mface->v2)->co;
			v3= (mvert+mface->v3)->co;
		}

		CalcNormFloat(v1, v2, v3, vnor);

		if(testflip) {
			f1= normals + 3*mface->v1;
			f2= normals + 3*mface->v2;
			f3= normals + 3*mface->v3;

			fac1= vnor[0]*f1[0] + vnor[1]*f1[1] + vnor[2]*f1[2];
			if(fac1<0.0) {
				mface->puno = ME_FLIPV1;
			}
			fac2= vnor[0]*f2[0] + vnor[1]*f2[1] + vnor[2]*f2[2];
			if(fac2<0.0) {
				mface->puno += ME_FLIPV2;
			}
			fac3= vnor[0]*f3[0] + vnor[1]*f3[1] + vnor[2]*f3[2];
			if(fac3<0.0) {
				mface->puno += ME_FLIPV3;
			}
			if(mface->v4) {
				f4= normals + 3*mface->v4;
				fac4= vnor[0]*f4[0] + vnor[1]*f4[1] + vnor[2]*f4[2];
				if(fac4<0.0) {
					mface->puno += ME_FLIPV4;
				}
			}
		}
		/* proj for cubemap! */
		xn= fabs(vnor[0]);
		yn= fabs(vnor[1]);
		zn= fabs(vnor[2]);
		
		if(zn>xn && zn>yn) mface->puno += ME_PROJXY;
		else if(yn>xn && yn>zn) mface->puno += ME_PROJXZ;
		else mface->puno += ME_PROJYZ;
		
	}
	
	MEM_freeN(normals);
}

/***/

static int editmesh_nfaces_selected(void)
{
	EditMesh *em = G.editMesh;
	EditVlak *evl;
	int count= 0;

	for (evl= em->faces.first; evl; evl= evl->next)
		if (vlakselectedAND(evl, SELECT))
			count++;

	return count;
}

static int editmesh_nvertices_selected(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	int count= 0;

	for (eve= em->verts.first; eve; eve= eve->next)
		if (eve->f & SELECT)
			count++;

	return count;
}

static void editmesh_calc_selvert_center(float cent_r[3])
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	int nsel= 0;

	cent_r[0]= cent_r[1]= cent_r[0]= 0.0;

	for (eve= em->verts.first; eve; eve= eve->next) {
		if (eve->f & SELECT) {
			cent_r[0]+= eve->co[0];
			cent_r[1]+= eve->co[1];
			cent_r[2]+= eve->co[2];
			nsel++;
		}
	}

	if (nsel) {
		cent_r[0]/= nsel;
		cent_r[1]/= nsel;
		cent_r[2]/= nsel;
	}
}

static int tface_is_selected(TFace *tf)
{
	return (!(tf->flag & TF_HIDE) && (tf->flag & TF_SELECT));
}

static int faceselect_nfaces_selected(Mesh *me)
{
	int i, count= 0;

	for (i=0; i<me->totface; i++) {
		MFace *mf= ((MFace*) me->mface) + i;
		TFace *tf= ((TFace*) me->tface) + i;

		if (mf->v3 && tface_is_selected(tf))
			count++;
	}

	return count;
}

	/* XXX, code for both these functions should be abstract,
	 * then unified, then written for other things (like objects,
	 * which would use same as vertices method), then added
	 * to interface! Hoera! - zr
	 */
void faceselect_align_view_to_selected(View3D *v3d, Mesh *me, int axis)
{
	if (!faceselect_nfaces_selected(me)) {
		error("No faces selected.");
	} else {
		float norm[3];
		int i;

		norm[0]= norm[1]= norm[2]= 0.0;
		for (i=0; i<me->totface; i++) {
			MFace *mf= ((MFace*) me->mface) + i;
			TFace *tf= ((TFace*) me->tface) + i;
	
			if (mf->v3 && tface_is_selected(tf)) {
				float *v1, *v2, *v3, fno[3];

				v1= me->mvert[mf->v1].co;
				v2= me->mvert[mf->v2].co;
				v3= me->mvert[mf->v3].co;
				if (mf->v4) {
					float *v4= me->mvert[mf->v4].co;
					CalcNormFloat4(v1, v2, v3, v4, fno);
				} else {
					CalcNormFloat(v1, v2, v3, fno);
				}

				norm[0]+= fno[0];
				norm[1]+= fno[1];
				norm[2]+= fno[2];
			}
		}

		view3d_align_axis_to_vector(v3d, axis, norm);
	}
}

void editmesh_align_view_to_selected(View3D *v3d, int axis)
{
	EditMesh *em = G.editMesh;
	int nselverts= editmesh_nvertices_selected();

	if (nselverts<3) {
		if (nselverts==0) {
			error("No faces or vertices selected.");
		} else {
			error("At least one face or three vertices must be selected.");
		}
	} else if (editmesh_nfaces_selected()) {
		float norm[3];
		EditVlak *evl;

		norm[0]= norm[1]= norm[2]= 0.0;
		for (evl= em->faces.first; evl; evl= evl->next) {
			if (vlakselectedAND(evl, SELECT)) {
				float fno[3];
				if (evl->v4) CalcNormFloat4(evl->v1->co, evl->v2->co, evl->v3->co, evl->v4->co, fno);
				else CalcNormFloat(evl->v1->co, evl->v2->co, evl->v3->co, fno);
						/* XXX, fixme, should be flipped intp a 
						 * consistent direction. -zr
						 */
				norm[0]+= fno[0];
				norm[1]+= fno[1];
				norm[2]+= fno[2];
			}
		}

		Mat4Mul3Vecfl(G.obedit->obmat, norm);
		view3d_align_axis_to_vector(v3d, axis, norm);
	} else {
		float cent[3], norm[3];
		EditVert *eve, *leve= NULL;

		norm[0]= norm[1]= norm[2]= 0.0;
		editmesh_calc_selvert_center(cent);
		for (eve= em->verts.first; eve; eve= eve->next) {
			if (eve->f & SELECT) {
				if (leve) {
					float tno[3];
					CalcNormFloat(cent, leve->co, eve->co, tno);
					
						/* XXX, fixme, should be flipped intp a 
						 * consistent direction. -zr
						 */
					norm[0]+= tno[0];
					norm[1]+= tno[1];
					norm[2]+= tno[2];
				}
				leve= eve;
			}
		}

		Mat4Mul3Vecfl(G.obedit->obmat, norm);
		view3d_align_axis_to_vector(v3d, axis, norm);
	}
}

/*  

Read a trail of mouse coords and return them as an array of CutCurve structs
len returns number of mouse coords read before commiting with RETKEY   
It is up to the caller to free the block when done with it,

this doesn't belong here.....
 */

CutCurve *get_mouse_trail(int *len, char mode){

	CutCurve *curve,*temp;
	short event, val, ldown=0, restart=0, rubberband=0;
	short  mval[2], lockaxis=0, lockx=0, locky=0, lastx=0, lasty=0;
	int i=0, j, blocks=1, lasti=0;
	
	*len=0;
	curve=(CutCurve *)MEM_callocN(1024*sizeof(CutCurve), "MouseTrail");

	if (!curve) {
		printf("failed to allocate memory in get_mouse_trail()\n");
		return(NULL);
	}
	mywinset(curarea->win);
	glDrawBuffer(GL_FRONT);
	
	headerprint("LMB to draw, Enter to finish, ESC to abort.");

	persp(PERSP_WIN);
	
	glColor3ub(200, 200, 0);
	
	while(TRUE) {
		
		event=extern_qread(&val);	/* Enter or RMB indicates finish */
		if(val) {
			if(event==RETKEY || event==PADENTER) break;
		}
		
		if( event==ESCKEY || event==RIGHTMOUSE ) {
			if (curve) MEM_freeN(curve);
			*len=0;
			glFlush();
			glDrawBuffer(GL_BACK);
			return(NULL);
			break;
		}	
		
		if (rubberband)  { /* rubberband mode, undraw last rubberband */
			glLineWidth(2.0);
			sdrawXORline(curve[i-1].x, curve[i-1].y,mval[0], mval[1]); 
			glLineWidth(1.0);
			glFlush();
			rubberband=0;
		}
		
		getmouseco_areawin(mval);
		
		if (lockaxis==1) mval[1]=locky;
		if (lockaxis==2) mval[0]=lockx;
		
		if ( ((i==0) || (mval[0]!=curve[i-1].x) || (mval[1]!=curve[i-1].y))
			&& (get_mbut() & L_MOUSE) ){ /* record changes only, if LMB down */
			
			lastx=curve[i].x=mval[0];
			lasty=curve[i].y=mval[1];
			
			lockaxis=0;
			
			i++; 
			
			ldown=1;
			if (restart) { 
				for(j=1;j<i;j++) sdrawXORline(curve[j-1].x, curve[j-1].y, curve[j].x, curve[j].y);
				if (rubberband) sdrawXORline(curve[j].x, curve[j].y, mval[0], mval[1]);
				glFlush();
				rubberband=0;
				lasti=i=0;
				restart=0;
				ldown=0;
			}
		}
		
		if ((event==MIDDLEMOUSE)&&(get_mbut()&M_MOUSE)&&(i)){/*MMB Down*/
		/*determine which axis to lock to, or clear if locked */
			if (lockaxis) lockaxis=0;
			else if (abs(curve[i-1].x-mval[0]) > abs(curve[i-1].y-mval[1])) lockaxis=1;
			else lockaxis=2;
			
			if (lockaxis) {
				lockx=lastx;
				locky=lasty;
			}
		}
		
		if ((i>1)&&(i!=lasti)) {  /*Draw recorded part of curve */
			sdrawline(curve[i-2].x, curve[i-2].y, curve[i-1].x, curve[i-1].y);
			glFlush();
		}
		
		if ((i==lasti)&&(i>0)) { /*Draw rubberband */
			glLineWidth(2.0);
			sdrawXORline(curve[i-1].x, curve[i-1].y,mval[0], mval[1]);
			glLineWidth(1.0);
			glFlush();
			rubberband=1;
		}
		lasti=i;

		if (i>=blocks*1024) { /* reallocate data if out of room */
			temp=curve;
			curve=(CutCurve *)MEM_callocN((blocks+1)*1024*sizeof(CutCurve), "MouseTrail");
			if (!curve) {
				printf("failed to re-allocate memory in get_mouse_trail()\n");
				return(NULL);
			}
			memcpy(curve, temp, blocks*1024*sizeof(CutCurve));
			blocks++;
			MEM_freeN(temp);
		}
	}

	glFlush();
	glDrawBuffer(GL_BACK);
	persp(PERSP_VIEW);

	*len=i;

	return(curve);
}

/* ******************************************************************** */
/* Knife Subdivide Tool.  Subdivides edges intersected by a mouse trail
	drawn by user.
	
	Currently mapped to KKey when in MeshEdit mode.
	Usage:
		Hit Shift K, Select Centers or Exact
		Hold LMB down to draw path, hit RETKEY.
		ESC cancels as expected.
   
	Contributed by Robert Wenzlaff (Det. Thorn).
*/

void KnifeSubdivide(char mode){
	EditMesh *em = G.editMesh;
	int oldcursor, len=0;
	short isect=0;
	CutCurve *curve;		
	EditEdge *eed; 
	Window *win;	
	
	if (G.obedit==0) return;

	if (editmesh_nvertices_selected() < 2) {
		error("No edges are selected to operate on");
		return;
	}

	if (mode==KNIFE_PROMPT) {
		short val= pupmenu("Cut Type %t|Exact Line%x1|Midpoints%x2");
		if(val<1) return;
		mode= val;	// warning, mode is char, pupmenu returns -1 with ESC
	}

	undo_push_mesh("Knife");
	
	calc_meshverts_ext();  /*Update screen coords for current window */
	
	/* Set a knife cursor here */
	oldcursor=get_cursor();

	win=winlay_get_active_window();
	
	SetBlenderCursor(BC_KNIFECURSOR);
	
	curve=get_mouse_trail(&len, TRAIL_MIXED);
	
	if (curve && len && mode){
		eed= em->edges.first;		
		while(eed) {	
			if((eed->v1->f&1)&&(eed->v2->f&1)){
				isect=seg_intersect(eed, curve, len);
				if (isect) eed->f=1;
				else eed->f=0;
				eed->f1=isect;
				//printf("isect=%i\n", isect);
			}
			else {
				eed->f=0;
				eed->f1=0;
			}
			eed= eed->next;
		}
		
		if (mode==1) subdivideflag(1, 0, B_KNIFE|B_PERCENTSUBD);
		else if (mode==2) subdivideflag(1, 0, B_KNIFE);
		
		eed=em->edges.first;
		while(eed){
			eed->f=0;
			eed->f1=0;
			eed=eed->next;
		}	
	}
	/* Return to old cursor and flags...*/
	
	addqueue(curarea->win,  REDRAW, 0);
	window_set_cursor(win, oldcursor);
	if (curve) MEM_freeN(curve);
}

/* seg_intersect() Determines if and where a mouse trail intersects an EditEdge */

short seg_intersect(EditEdge *e, CutCurve *c, int len){
#define MAXSLOPE 100000
	short isect=0;
	float  x11, y11, x12=0, y12=0, x2max, x2min, y2max;
	float  y2min, dist, lastdist=0, xdiff2, xdiff1;
	float  m1, b1, m2, b2, x21, x22, y21, y22, xi;
	float  yi, x1min, x1max, y1max, y1min, perc=0; 
	float  scr[2], co[4];
	int  i;
	
	/* Get screen coords of verts (v->xs and v->ys clip if off screen */
	VECCOPY(co, e->v1->co);
	co[3]= 1.0;
	Mat4MulVec4fl(G.obedit->obmat, co);
	project_float(co, scr);
	x21=scr[0];
	y21=scr[1];
	
	VECCOPY(co, e->v2->co);
	co[3]= 1.0;
	Mat4MulVec4fl(G.obedit->obmat, co);
	project_float(co, scr);
	x22=scr[0];
	y22=scr[1];
	
	xdiff2=(x22-x21);  
	if (xdiff2) {
		m2=(y22-y21)/xdiff2;
		b2= ((x22*y21)-(x21*y22))/xdiff2;
	}
	else {
		m2=MAXSLOPE;  /* Verticle slope  */
		b2=x22;      
	}
	for (i=0; i<len; i++){
		if (i>0){
			x11=x12;
			y11=y12;
		}
		else {
			x11=c[i].x;
			y11=c[i].y;
		}
		x12=c[i].x;
		y12=c[i].y;

		/* Perp. Distance from point to line */
		if (m2!=MAXSLOPE) dist=(y12-m2*x12-b2);/* /sqrt(m2*m2+1); Only looking for */
						       /* change in sign.  Skip extra math */	
		else dist=x22-x12;	
		
		if (i==0) lastdist=dist;
		
		/* if dist changes sign, and intersect point in edge's Bound Box*/
		if ((lastdist*dist)<=0){
			xdiff1=(x12-x11); /* Equation of line between last 2 points */
			if (xdiff1){
				m1=(y12-y11)/xdiff1;
				b1= ((x12*y11)-(x11*y12))/xdiff1;
			}
			else{
				m1=MAXSLOPE;
				b1=x12;
			}
			x2max=MAX2(x21,x22)+0.001; /* prevent missed edges   */
			x2min=MIN2(x21,x22)-0.001; /* due to round off error */
			y2max=MAX2(y21,y22)+0.001;
			y2min=MIN2(y21,y22)-0.001;
			
			/* Found an intersect,  calc intersect point */
			if (m1==m2){ 		/* co-incident lines */
						/* cut at 50% of overlap area*/
				x1max=MAX2(x11, x12);
				x1min=MIN2(x11, x12);
				xi= (MIN2(x2max,x1max)+MAX2(x2min,x1min))/2.0;	
				
				y1max=MAX2(y11, y12);
				y1min=MIN2(y11, y12);
				yi= (MIN2(y2max,y1max)+MAX2(y2min,y1min))/2.0;
			}			
			else if (m2==MAXSLOPE){ 
				xi=x22;
				yi=m1*x22+b1;
			}
			else if (m1==MAXSLOPE){ 
				xi=x12;
				yi=m2*x12+b2;
			}
			else {
				xi=(b1-b2)/(m2-m1);
				yi=(b1*m2-m1*b2)/(m2-m1);
			}
			
			/* Intersect inside bounding box of edge?*/
			if ((xi>=x2min)&&(xi<=x2max)&&(yi<=y2max)&&(yi>=y2min)){
				if ((m2<=1.0)&&(m2>=-1.0)) perc = (xi-x21)/(x22-x21);	
				else perc=(yi-y21)/(y22-y21); /*lower slope more accurate*/
				isect=32768.0*(perc+0.0000153); /* Percentage in 1/32768ths */
				break;
			}
		}	
		lastdist=dist;
	}
	return(isect);
} 


void LoopMenu(){ /* Called by KKey */

	short ret;
	
	ret=pupmenu("Loop/Cut Menu %t|Face Loop Select %x1|Face Loop Cut %x2|"
				"Knife (Exact) %x3|Knife (Midpoints)%x4|");
				
	switch (ret){
		case 1:
			loopoperations(LOOP_SELECT);
			break;
		case 2:
			loopoperations(LOOP_CUT);
			break;
		case 3: 
			KnifeSubdivide(KNIFE_EXACT);
			break;
		case 4:
			KnifeSubdivide(KNIFE_MIDPOINT);
	}

}

/*********************** EDITMESH UNDO ********************************/
/* Mesh Edit undo by Alexander Ewring,                                */
/* ported by Robert Wenzlaff                                          */
/*                                                                    */
/* Any meshedit function wishing to create an undo step, calls        */
/*     undo_push_mesh("menu_name_of_step");                           */

Mesh *undo_new_mesh(void)
{
       return(MEM_callocN(sizeof(Mesh), "undo_mesh"));
}

void undo_free_mesh(Mesh *me)
{
       if(me->mat) MEM_freeN(me->mat);
       if(me->orco) MEM_freeN(me->orco);
       if(me->mface) MEM_freeN(me->mface);
       if(me->tface) MEM_freeN(me->tface);
       if(me->mvert) MEM_freeN(me->mvert);
       if(me->dvert) free_dverts(me->dvert, me->totvert);
       if(me->mcol) MEM_freeN(me->mcol);
       if(me->msticky) MEM_freeN(me->msticky);
       if(me->bb) MEM_freeN(me->bb);
       if(me->disp.first) freedisplist(&me->disp);
       MEM_freeN(me);
}


void undo_push_mesh(char *name)
{
       Mesh *me;
       int i;

       countall();

       G.undo_edit_level++;

       if (G.undo_edit_level<0) {
               printf("undo: ERROR: G.undo_edit_level negative\n");
               return;
       }


       if (G.undo_edit[G.undo_edit_level].datablock != 0) {
               undo_free_mesh(G.undo_edit[G.undo_edit_level].datablock);
       }
       if (strcmp(name, "U")!=0) {
               for (i=G.undo_edit_level+1; i<(U.undosteps-1); i++) {
                       if (G.undo_edit[i].datablock != 0) {
                               undo_free_mesh(G.undo_edit[i].datablock);
                               G.undo_edit[i].datablock= 0;
                       }
               }
               G.undo_edit_highest= G.undo_edit_level;
       }

       me= undo_new_mesh();

       if (G.undo_edit_level>=U.undosteps) {
               G.undo_edit_level--;
               undo_free_mesh((Mesh*)G.undo_edit[0].datablock);
               G.undo_edit[0].datablock= 0;
               for (i=0; i<(U.undosteps-1); i++) {
                       G.undo_edit[i]= G.undo_edit[i+1];
               }
       }

       if (strcmp(name, "U")!=0) strcpy(G.undo_edit[G.undo_edit_level].name, name);
       //printf("undo: saving block: %d [%s]\n", G.undo_edit_level, G.undo_edit[G.undo_edit_level].name);

       G.undo_edit[G.undo_edit_level].datablock= (void*)me;
       load_editMesh_real(me, 1);
}

void undo_pop_mesh(int steps)  /* steps == 1 is one step */
{
       if (G.undo_edit_level > (steps-2)) {
		undo_push_mesh("U");
		G.undo_edit_level-= steps;
//printf("undo: restoring block: %d [%s]\n", G.undo_edit_level, G.undo_edit[G.undo_edit_level].name);    -
               make_editMesh_real((Mesh*)G.undo_edit[G.undo_edit_level].datablock);
               allqueue(REDRAWVIEW3D, 0);
               makeDispList(G.obedit);
               G.undo_edit_level--;
       } else error("No more steps to undo");
}


void undo_redo_mesh(void)
{
       if ( (G.undo_edit[G.undo_edit_level+2].datablock) &&
            ( (G.undo_edit_level+1) <= G.undo_edit_highest ) ) {
               G.undo_edit_level++;
               //printf("redo: restoring block: %d [%s]\n", G.undo_edit_level+1, G.undo_edit[G.undo_edit_level+1].name);-
               make_editMesh_real((Mesh*)G.undo_edit[G.undo_edit_level+1].datablock);
               allqueue(REDRAWVIEW3D, 0);
               makeDispList(G.obedit);
       } else error("No more steps to redo");
}

void undo_clear_mesh(void)
{
       int i;
       Mesh *me;

       for (i=0; i<=UNDO_EDIT_MAX; i++) {
               me= (Mesh*) G.undo_edit[i].datablock;
               if (me) {
                       //printf("undo: freeing %d\n", i);
                       undo_free_mesh(me);
                       G.undo_edit[i].datablock= 0;
               }
       }
}

void undo_menu_mesh(void)
{
	short event=66;
	int i;
	char menu[2080], temp[64];

	TEST_EDITMESH

	strcpy(menu, "Undo %t|%l");
	strcat(menu, "|All changes%x1|%l");
	
	for (i=G.undo_edit_level; i>=0; i--) {
			snprintf(temp, 64, "|%s%%x%d", G.undo_edit[i].name, i+2);
			strcat(menu, temp);
	}

	event=pupmenu_col(menu, 20);

	if(event<1) return;

	if (event==1) remake_editMesh();
	else undo_pop_mesh(G.undo_edit_level-event+3);
}

/******************* BEVEL CODE STARTS HERE ********************/

void bevel_displace_vec(float *midvec, float *v1, float *v2, float *v3, float d, float no[3])
{
	float a[3], c[3], n_a[3], n_c[3], mid[3], ac, ac2, fac;

	VecSubf(a, v1, v2);
	VecSubf(c, v3, v2);

	Crossf(n_a, a, no);
	Normalise(n_a);
	Crossf(n_c, no, c);
	Normalise(n_c);

	Normalise(a);
	Normalise(c);
	ac = Inpf(a, c);

	if (ac == 1 || ac == -1) {
		midvec[0] = midvec[1] = midvec[2] = 0;
		return;
	}
	ac2 = ac * ac;
	fac = sqrt((ac2 + 2*ac + 1)/(1 - ac2) + 1);
	VecAddf(mid, n_c, n_a);
	Normalise(mid);
	VecMulf(mid, d * fac);
	VecAddf(mid, mid, v2);
	VecCopyf(midvec, mid);
}

/*	Finds the new point using the sinus law to extrapolate a triangle
	Lots of sqrts which would not be good for a real time algo
	Using the mid  point of the extrapolation of both sides 
	Useless for coplanar quads, but that doesn't happen too often */
void fix_bevel_wrap(float *midvec, float *v1, float *v2, float *v3, float *v4, float d, float no[3]) {
	float a[3], b[3], c[3], l_a, l_b, l_c, s_a, s_b, s_c, Pos1[3], Pos2[3], Dir[3];

	VecSubf(a, v3, v2);
	l_a = Normalise(a);
	VecSubf(b, v4, v3);
	Normalise(b);
	VecSubf(c, v1, v2);
	Normalise(c);

	s_b = Inpf(a, c);
	s_b = sqrt(1 - (s_b * s_b));
	s_a = Inpf(b, c);
	s_a = sqrt(1 - (s_a * s_a));
	VecMulf(a, -1);
	s_c = Inpf(a, b);
	s_c = sqrt(1 - (s_c * s_c));

	l_b = s_b * l_a / s_a;
	l_c = s_c * l_a / s_a;

	VecMulf(b, l_b);
	VecMulf(c, l_c);

	VecAddf(Pos1, v2, c);
	VecAddf(Pos2, v3, b);

	VecAddf(Dir, Pos1, Pos2);
	VecMulf(Dir, 0.5);

	bevel_displace_vec(midvec, v3, Dir, v2, d, no);

}


char detect_wrap(float *o_v1, float *o_v2, float *v1, float *v2, float *no) {
	float o_a[3], a[3], o_c[3], c[3];

	VecSubf(o_a, o_v1, o_v2);
	VecSubf(a, v1, v2);

	Crossf(o_c, o_a, no);
	Crossf(c, a, no);

	if (Inpf(c, o_c) <= 0)
		return 1;
	else
		return 0;
}

// Detects and fix a quad wrapping after the resize
// Arguments are the orginal verts followed by the final verts and then the bevel size and the normal
void fix_bevel_quad_wrap(float *o_v1, float *o_v2, float *o_v3, float *o_v4, float *v1, float *v2, float *v3, float *v4, float d, float *no) {
	float vec[3];
	char wrap[4];
	
	// Quads can wrap partially. Watch out
	wrap[0] = detect_wrap(o_v1, o_v2, v1, v2, no); // Edge 1-2
	wrap[1] = detect_wrap(o_v2, o_v3, v2, v3, no); // Edge 2-3
	wrap[2] = detect_wrap(o_v3, o_v4, v3, v4, no); // Edge 3-4
	wrap[3] = detect_wrap(o_v4, o_v1, v4, v1, no); // Edge 4-1

	// Edge 1 inverted
	if (wrap[0] == 1 && wrap[1] == 0 && wrap[2] == 0 && wrap[3] == 0) {
		fix_bevel_wrap(vec, o_v2, o_v3, o_v4, o_v1, d, no);
		VECCOPY(v1, vec);
		VECCOPY(v2, vec);
	}
	// Edge 2 inverted
	else if (wrap[0] == 0 && wrap[1] == 1 && wrap[2] == 0 && wrap[3] == 0) {
		fix_bevel_wrap(vec, o_v3, o_v4, o_v1, o_v2, d, no);
		VECCOPY(v2, vec);
		VECCOPY(v3, vec);
	}
	// Edge 3 inverted
	else if (wrap[0] == 0 && wrap[1] == 0 && wrap[2] == 1 && wrap[3] == 0) {
		fix_bevel_wrap(vec, o_v4, o_v1, o_v2, o_v3, d, no);
		VECCOPY(v3, vec);
		VECCOPY(v4, vec);
	}
	// Edge 4 inverted
	else if (wrap[0] == 0 && wrap[1] == 0 && wrap[2] == 0 && wrap[3] == 1) {
		fix_bevel_wrap(vec, o_v1, o_v2, o_v3, o_v4, d, no);
		VECCOPY(v4, vec);
		VECCOPY(v1, vec);
	}
	// Edge 2 and 4 inverted
	else if (wrap[0] == 0 && wrap[1] == 1 && wrap[2] == 0 && wrap[3] == 1) {
		VecAddf(vec, v2, v3);
		VecMulf(vec, 0.5);
		VECCOPY(v2, vec);
		VECCOPY(v3, vec);
		VecAddf(vec, v1, v4);
		VecMulf(vec, 0.5);
		VECCOPY(v1, vec);
		VECCOPY(v4, vec);
	}
	// Edge 1 and 3 inverted
	else if (wrap[0] == 1 && wrap[1] == 0 && wrap[2] == 1 && wrap[3] == 0) {
		VecAddf(vec, v1, v2);
		VecMulf(vec, 0.5);
		VECCOPY(v1, vec);
		VECCOPY(v2, vec);
		VecAddf(vec, v3, v4);
		VecMulf(vec, 0.5);
		VECCOPY(v3, vec);
		VECCOPY(v4, vec);
	}
	// Totally inverted
	else if (wrap[0] == 1 && wrap[1] == 1 && wrap[2] == 1 && wrap[3] == 1) {
		VecAddf(vec, v1, v2);
		VecAddf(vec, vec, v3);
		VecAddf(vec, vec, v4);
		VecMulf(vec, 0.25);
		VECCOPY(v1, vec);
		VECCOPY(v2, vec);
		VECCOPY(v3, vec);
		VECCOPY(v4, vec);
	}

}

// Detects and fix a tri wrapping after the resize
// Arguments are the orginal verts followed by the final verts and the normal
// Triangles cannot wrap partially (not in this situation
void fix_bevel_tri_wrap(float *o_v1, float *o_v2, float *o_v3, float *v1, float *v2, float *v3, float *no) {
	if (detect_wrap(o_v1, o_v2, v1, v2, no)) {
		float vec[3];
		VecAddf(vec, o_v1, o_v2);
		VecAddf(vec, vec, o_v3);
		VecMulf(vec, 1.0/3.0);
		VECCOPY(v1, vec);
		VECCOPY(v2, vec);
		VECCOPY(v3, vec);
	}
}

void bevel_shrink_faces(float d, int flag)
{
	EditMesh *em = G.editMesh;
	EditVlak *evl;
	float vec[3], no[3], v1[3], v2[3], v3[3], v4[3];

	/* move edges of all faces with evl->f1 & flag closer towards their centres */
	evl= em->faces.first;
	while (evl) {
		if (evl->f1 & flag) {
			VECCOPY(v1, evl->v1->co);
			VECCOPY(v2, evl->v2->co);			
			VECCOPY(v3, evl->v3->co);	
			VECCOPY(no, evl->n);
			if (evl->v4 == NULL) {
				bevel_displace_vec(vec, v1, v2, v3, d, no);
				VECCOPY(evl->v2->co, vec);
				bevel_displace_vec(vec, v2, v3, v1, d, no);
				VECCOPY(evl->v3->co, vec);		
				bevel_displace_vec(vec, v3, v1, v2, d, no);
				VECCOPY(evl->v1->co, vec);

				fix_bevel_tri_wrap(v1, v2, v3, evl->v1->co, evl->v2->co, evl->v3->co, no);
			} else {
				VECCOPY(v4, evl->v4->co);
				bevel_displace_vec(vec, v1, v2, v3, d, no);
				VECCOPY(evl->v2->co, vec);
				bevel_displace_vec(vec, v2, v3, v4, d, no);
				VECCOPY(evl->v3->co, vec);		
				bevel_displace_vec(vec, v3, v4, v1, d, no);
				VECCOPY(evl->v4->co, vec);		
				bevel_displace_vec(vec, v4, v1, v2, d, no);
				VECCOPY(evl->v1->co, vec);

				fix_bevel_quad_wrap(v1, v2, v3, v4, evl->v1->co, evl->v2->co, evl->v3->co, evl->v4->co, d, no);
			}
		}
		evl= evl->next;
	}	
}

void bevel_shrink_draw(float d, int flag)
{
	EditMesh *em = G.editMesh;
	EditVlak *evl;
	float vec[3], no[3], v1[3], v2[3], v3[3], v4[3], fv1[3], fv2[3], fv3[3], fv4[3];

	/* move edges of all faces with evl->f1 & flag closer towards their centres */
	evl= em->faces.first;
	while (evl) {
		VECCOPY(v1, evl->v1->co);
		VECCOPY(v2, evl->v2->co);			
		VECCOPY(v3, evl->v3->co);	
		VECCOPY(no, evl->n);
		if (evl->v4 == NULL) {
			bevel_displace_vec(vec, v1, v2, v3, d, no);
			VECCOPY(fv2, vec);
			bevel_displace_vec(vec, v2, v3, v1, d, no);
			VECCOPY(fv3, vec);		
			bevel_displace_vec(vec, v3, v1, v2, d, no);
			VECCOPY(fv1, vec);

			fix_bevel_tri_wrap(v1, v2, v3, fv1, fv2, fv3, no);

			glBegin(GL_LINES);
			glVertex3fv(fv1);
			glVertex3fv(fv2);
			glEnd();						
			glBegin(GL_LINES);
			glVertex3fv(fv2);
			glVertex3fv(fv3);
			glEnd();						
			glBegin(GL_LINES);
			glVertex3fv(fv1);
			glVertex3fv(fv3);
			glEnd();						
		} else {
			VECCOPY(v4, evl->v4->co);
			bevel_displace_vec(vec, v4, v1, v2, d, no);
			VECCOPY(fv1, vec);
			bevel_displace_vec(vec, v1, v2, v3, d, no);
			VECCOPY(fv2, vec);
			bevel_displace_vec(vec, v2, v3, v4, d, no);
			VECCOPY(fv3, vec);		
			bevel_displace_vec(vec, v3, v4, v1, d, no);
			VECCOPY(fv4, vec);		

			fix_bevel_quad_wrap(v1, v2, v3, v4, fv1, fv2, fv3, fv4, d, no);

			glBegin(GL_LINES);
			glVertex3fv(fv1);
			glVertex3fv(fv2);
			glEnd();						
			glBegin(GL_LINES);
			glVertex3fv(fv2);
			glVertex3fv(fv3);
			glEnd();						
			glBegin(GL_LINES);
			glVertex3fv(fv3);
			glVertex3fv(fv4);
			glEnd();						
			glBegin(GL_LINES);
			glVertex3fv(fv1);
			glVertex3fv(fv4);
			glEnd();						
		}
		evl= evl->next;
	}	
}

void bevel_mesh(float bsize, int allfaces)
{
	EditMesh *em = G.editMesh;
//#define BEV_DEBUG
/* Enables debug printfs and assigns material indices: */
/* 2 = edge quad                                       */
/* 3 = fill polygon (vertex clusters)                  */

	EditVlak *evl, *example; //, *nextvl;
	EditEdge *eed, *eed2;
	EditVert *neweve[1024], *eve, *eve2, *eve3, *v1, *v2, *v3, *v4; //, *eve4;
	float con1, con2, con3;
	//short found4,  search;
	//float f1, f2, f3, f4;
	float cent[3], min[3], max[3];
	int a, b, c;
	float limit= 0.001;

	waitcursor(1);

	removedoublesflag(1, limit);

	/* tag all original faces */
	evl= em->faces.first;
	while (evl) {
		if (vlakselectedAND(evl, 1)||allfaces) {
			evl->f1= 1;
			evl->v1->f |= 128;
			evl->v2->f |= 128;
			evl->v3->f |= 128;
			if (evl->v4) evl->v4->f |= 128;			
		}
		evl->v1->f &= ~64;
		evl->v2->f &= ~64;
		evl->v3->f &= ~64;
		if (evl->v4) evl->v4->f &= ~64;		

		evl= evl->next;
	}

#ifdef BEV_DEBUG
	fprintf(stderr,"bevel_mesh: split\n");
#endif
	
	evl= em->faces.first;
	while (evl) {
		if (evl->f1 & 1) {
			evl->f1-= 1;
			v1= addvertlist(evl->v1->co);
			v1->f= evl->v1->f & ~128;
   			evl->v1->vn= v1;
#ifdef __NLA
   			v1->totweight = evl->v1->totweight;
   			if (evl->v1->totweight){
   				v1->dw = MEM_mallocN (evl->v1->totweight * sizeof(MDeformWeight), "deformWeight");
   				memcpy (v1->dw, evl->v1->dw, evl->v1->totweight * sizeof(MDeformWeight));
   			}
   			else
   				v1->dw=NULL;
#endif
			v1= addvertlist(evl->v2->co);
			v1->f= evl->v2->f & ~128;
   			evl->v2->vn= v1;
#ifdef __NLA
   			v1->totweight = evl->v2->totweight;
   			if (evl->v2->totweight){
   				v1->dw = MEM_mallocN (evl->v2->totweight * sizeof(MDeformWeight), "deformWeight");
   				memcpy (v1->dw, evl->v2->dw, evl->v2->totweight * sizeof(MDeformWeight));
   			}
   			else
   				v1->dw=NULL;
#endif
			v1= addvertlist(evl->v3->co);
			v1->f= evl->v3->f & ~128;
   			evl->v3->vn= v1;
#ifdef __NLA
   			v1->totweight = evl->v3->totweight;
   			if (evl->v3->totweight){
   				v1->dw = MEM_mallocN (evl->v3->totweight * sizeof(MDeformWeight), "deformWeight");
   				memcpy (v1->dw, evl->v3->dw, evl->v3->totweight * sizeof(MDeformWeight));
   			}
   			else
   				v1->dw=NULL;
#endif
			if (evl->v4) {
				v1= addvertlist(evl->v4->co);
				v1->f= evl->v4->f & ~128;
	   			evl->v4->vn= v1;
#ifdef __NLA
	   			v1->totweight = evl->v4->totweight;
	   			if (evl->v4->totweight){
	   				v1->dw = MEM_mallocN (evl->v4->totweight * sizeof(MDeformWeight), "deformWeight");
	   				memcpy (v1->dw, evl->v4->dw, evl->v4->totweight * sizeof(MDeformWeight));
	   			}
	   			else
	   				v1->dw=NULL;
#endif
			}

   			addedgelist(evl->e1->v1->vn, evl->e1->v2->vn, evl->e1);
   			addedgelist(evl->e2->v1->vn,evl->e2->v2->vn, evl->e2);   			
   			addedgelist(evl->e3->v1->vn,evl->e3->v2->vn, evl->e3);   			
   			if (evl->e4) addedgelist(evl->e4->v1->vn,evl->e4->v2->vn, evl->e4);  

   			if(evl->v4) {
				v1= evl->v1->vn;
				v2= evl->v2->vn;
				v3= evl->v3->vn;
				v4= evl->v4->vn;
				addvlaklist(v1, v2, v3, v4, evl);
   			} else {
   				v1= evl->v1->vn;
   				v2= evl->v2->vn;
   				v3= evl->v3->vn;
   				addvlaklist(v1, v2, v3, 0, evl);
   			}

			evl= evl-> next;
		} else {
			evl= evl->next;
		}
	}
	
	delvlakflag(128);

	/* tag all faces for shrink*/
	evl= em->faces.first;
	while (evl) {
		if (vlakselectedAND(evl, 1)||allfaces) {
			evl->f1= 2;
		}
		evl= evl->next;
	}

#ifdef BEV_DEBUG
	fprintf(stderr,"bevel_mesh: make edge quads\n");
#endif

	/* find edges that are on each other and make quads between them */

	eed= em->edges.first;
	while(eed) {
		eed->f= eed->f1= 0;
		if ( ((eed->v1->f & eed->v2->f) & 1) || allfaces) eed->f1 |= 4;	/* original edges */
		eed->vn= 0;
		eed= eed->next;
	}

	eed= em->edges.first;
	while (eed) {
		if ( ((eed->f1 & 2)==0) && (eed->f1 & 4) ) {
			eed2= em->edges.first;
			while (eed2) {
				if ( (eed2 != eed) && ((eed2->f1 & 2)==0) && (eed->f1 & 4) ) {
					if (
					   (eed->v1 != eed2->v1) &&
					   (eed->v1 != eed2->v2) &&					   
					   (eed->v2 != eed2->v1) &&
					   (eed->v2 != eed2->v2) &&	(
					   ( VecCompare(eed->v1->co, eed2->v1->co, limit) &&
						 VecCompare(eed->v2->co, eed2->v2->co, limit) ) ||
					   ( VecCompare(eed->v1->co, eed2->v2->co, limit) &&
						 VecCompare(eed->v2->co, eed2->v1->co, limit) ) ) )
						{
						
#ifdef BEV_DEBUG						
						fprintf(stderr, "bevel_mesh: edge quad\n");
#endif						
						
						eed->f1 |= 2;	/* these edges are finished */
						eed2->f1 |= 2;
						
						example= NULL;
						evl= em->faces.first;	/* search example vlak (for mat_nr, ME_SMOOTH, ...) */
						while (evl) {
							if ( (evl->e1 == eed) ||
							     (evl->e2 == eed) ||
							     (evl->e3 == eed) ||
							     (evl->e4 && (evl->e4 == eed)) ) {
							    example= evl;
								evl= NULL;
							}
							if (evl) evl= evl->next;
						}
						
						neweve[0]= eed->v1; neweve[1]= eed->v2;
						neweve[2]= eed2->v1; neweve[3]= eed2->v2;
						
						if(exist_vlak(neweve[0], neweve[1], neweve[2], neweve[3])==0) {
							evl= NULL;

							if (VecCompare(eed->v1->co, eed2->v2->co, limit)) {
								evl= addvlaklist(neweve[0], neweve[1], neweve[2], neweve[3], example);
							} else {
								evl= addvlaklist(neweve[0], neweve[2], neweve[3], neweve[1], example);
							}
						
							if(evl) {
								float inp;	
								CalcNormFloat(evl->v1->co, evl->v2->co, evl->v3->co, evl->n);
								inp= evl->n[0]*G.vd->viewmat[0][2] + evl->n[1]*G.vd->viewmat[1][2] + evl->n[2]*G.vd->viewmat[2][2];
								if(inp < 0.0) flipvlak(evl);
#ifdef BEV_DEBUG
								evl->mat_nr= 1;
#endif
							} else fprintf(stderr,"bevel_mesh: error creating face\n");
						}
						eed2= NULL;
					}
				}
				if (eed2) eed2= eed2->next;
			}
		}
		eed= eed->next;
	}

	eed= em->edges.first;
	while(eed) {
		eed->f= eed->f1= 0;
		eed->f1= 0;
		eed->v1->f1 &= ~1;
		eed->v2->f1 &= ~1;		
		eed->vn= 0;
		eed= eed->next;
	}

#ifdef BEV_DEBUG
	fprintf(stderr,"bevel_mesh: find clusters\n");
#endif	

	/* Look for vertex clusters */

	eve= em->verts.first;
	while (eve) {
		eve->f &= ~(64|128);
		eve->vn= NULL;
		eve= eve->next;
	}
	
	/* eve->f: 128: first vertex in a list (->vn) */
	/*          64: vertex is in a list */
	
	eve= em->verts.first;
	while (eve) {
		eve2= em->verts.first;
		eve3= NULL;
		while (eve2) {
			if ((eve2 != eve) && ((eve2->f & (64|128))==0)) {
				if (VecCompare(eve->co, eve2->co, limit)) {
					if ((eve->f & (128|64)) == 0) {
						/* fprintf(stderr,"Found vertex cluster:\n  *\n  *\n"); */
						eve->f |= 128;
						eve->vn= eve2;
						eve3= eve2;
					} else if ((eve->f & 64) == 0) {
						/* fprintf(stderr,"  *\n"); */
						if (eve3) eve3->vn= eve2;
						eve2->f |= 64;
						eve3= eve2;
					}
				}
			}
			eve2= eve2->next;
			if (!eve2) {
				if (eve3) eve3->vn= NULL;
			}
		}
		eve= eve->next;
	}

#ifdef BEV_DEBUG
	fprintf(stderr,"bevel_mesh: shrink faces\n");
#endif	

	bevel_shrink_faces(bsize, 2);

#ifdef BEV_DEBUG
	fprintf(stderr,"bevel_mesh: fill clusters\n");
#endif
	
	/* Make former vertex clusters faces */

	eve= em->verts.first;
	while (eve) {
		eve->f &= ~64;
		eve= eve->next;
	}

	eve= em->verts.first;
	while (eve) {
		if (eve->f & 128) {
			eve->f &= ~128;
			a= 0;
			neweve[a]= eve;
			eve2= eve->vn;
			while (eve2) {
				a++;
				neweve[a]= eve2;
				eve2= eve2->vn;
			}
			a++;
			evl= NULL;
			if (a>=3) {
				example= NULL;
				evl= em->faces.first;	/* search example vlak */
				while (evl) {
					if ( (evl->v1 == neweve[0]) ||
					     (evl->v2 == neweve[0]) ||
					     (evl->v3 == neweve[0]) ||
					     (evl->v4 && (evl->v4 == neweve[0])) ) {
					    example= evl;
						evl= NULL;
					}
					if (evl) evl= evl->next;
				}
#ifdef BEV_DEBUG				
				fprintf(stderr,"bevel_mesh: Making %d-gon\n", a);
#endif				
				if (a>4) {
					cent[0]= cent[1]= cent[2]= 0.0;				
					INIT_MINMAX(min, max);				
					for (b=0; b<a; b++) {
						VecAddf(cent, cent, neweve[b]->co);
						DO_MINMAX(neweve[b]->co, min, max);
					}
					cent[0]= (min[0]+max[0])/2;
					cent[1]= (min[1]+max[1])/2;
					cent[2]= (min[2]+max[2])/2;
					eve2= addvertlist(cent);
					eve2->f |= 1;
					eed= em->edges.first;
					while (eed) {
						c= 0;
						for (b=0; b<a; b++) 
							if ((neweve[b]==eed->v1) || (neweve[b]==eed->v2)) c++;
						if (c==2) {
							if(exist_vlak(eed->v1, eed->v2, eve2, 0)==0) {
								evl= addvlaklist(eed->v1, eed->v2, eve2, 0, example);
#ifdef BEV_DEBUG
								evl->mat_nr= 2;
#endif								
							}
						}
						eed= eed->next;
					}
				} else if (a==4) {
					if(exist_vlak(neweve[0], neweve[1], neweve[2], neweve[3])==0) {
						con1= convex(neweve[0]->co, neweve[1]->co, neweve[2]->co, neweve[3]->co);
						con2= convex(neweve[0]->co, neweve[2]->co, neweve[3]->co, neweve[1]->co);
						con3= convex(neweve[0]->co, neweve[3]->co, neweve[1]->co, neweve[2]->co);
						if(con1>=con2 && con1>=con3)
							evl= addvlaklist(neweve[0], neweve[1], neweve[2], neweve[3], example);
						else if(con2>=con1 && con2>=con3)
							evl= addvlaklist(neweve[0], neweve[2], neweve[3], neweve[1], example);
						else 
							evl= addvlaklist(neweve[0], neweve[2], neweve[1], neweve[3], example);
					}				
				}
				else if (a==3) {
					if(exist_vlak(neweve[0], neweve[1], neweve[2], 0)==0)
						evl= addvlaklist(neweve[0], neweve[1], neweve[2], 0, example);
				}
				if(evl) {
					float inp;	
					CalcNormFloat(neweve[0]->co, neweve[1]->co, neweve[2]->co, evl->n);
					inp= evl->n[0]*G.vd->viewmat[0][2] + evl->n[1]*G.vd->viewmat[1][2] + evl->n[2]*G.vd->viewmat[2][2];
					if(inp < 0.0) flipvlak(evl);
#ifdef BEV_DEBUG
						evl->mat_nr= 2;
#endif												
				}				
			}
		}
		eve= eve->next;
	}

	eve= em->verts.first;
	while (eve) {
		eve->f1= 0;
		eve->f &= ~(128|64);
		eve->vn= NULL;
		eve= eve->next;
	}
	
	recalc_editnormals();
	waitcursor(0);
	countall();
	allqueue(REDRAWVIEW3D, 0);
	makeDispList(G.obedit);
	
	removedoublesflag(1, limit);

#undef BEV_DEBUG
}

void bevel_mesh_recurs(float bsize, short recurs, int allfaces) 
{
	float d;
	short nr;

	d= bsize;
	for (nr=0; nr<recurs; nr++) {
		bevel_mesh(d, allfaces);
		if (nr==0) d /= 3; else d /= 2;
	}
}

void bevel_menu()
{
	char Finished = 0, Canceled = 0, str[100], Recalc = 0;
	short mval[2], oval[2], curval[2], event = 0, recurs = 1, nr;
	float vec[3], d, drawd=0.0, centre[3], fac = 1;

	getmouseco_areawin(mval);
	oval[0] = mval[0]; oval[1] = mval[1];

	// Silly hackish code to initialise the variable (warning if not done)
	// while still drawing in the first iteration (and without using another variable)
	curval[0] = mval[0] + 1; curval[1] = mval[1] + 1;

	window_to_3d(centre, mval[0], mval[1]);

	if(button(&recurs, 1, 4, "Recursion:")==0) return;

	for (nr=0; nr<recurs-1; nr++) {
		if (nr==0) fac += 1.0/3.0; else fac += 1.0/(3 * nr * 2.0);
	}

	SetBlenderCursor(SYSCURSOR);

	while (Finished == 0)
	{
		getmouseco_areawin(mval);
		if (mval[0] != curval[0] || mval[1] != curval[1] || (Recalc == 1))
		{
			Recalc = 0;
			curval[0] = mval[0];
			curval[1] = mval[1];

			window_to_3d(vec, mval[0]-oval[0], mval[1]-oval[1]);
			d = Normalise(vec) / 10;


			drawd = d * fac;
			if (G.qual & LR_CTRLKEY)
				drawd = (float) floor(drawd * 10.0)/10.0;
			if (G.qual & LR_SHIFTKEY)
				drawd /= 10;

			/*------------- Preview lines--------------- */
			
			/* uses callback mechanism to draw it all in current area */
			scrarea_do_windraw(curarea);			
			
			/* set window matrix to perspective, default an area returns with buttons transform */
			persp(PERSP_VIEW);
			/* make a copy, for safety */
			glPushMatrix();
			/* multiply with the object transformation */
			mymultmatrix(G.obedit->obmat);
			
			glColor3ub(255, 255, 0);

			// PREVIEW CODE GOES HERE
			bevel_shrink_draw(drawd, 2);

			/* restore matrix transform */
			glPopMatrix();
			
			sprintf(str, "Bevel Size: %.4f        LMB to confirm, RMB to cancel, SPACE to input directly.", drawd);
			headerprint(str);

			/* this also verifies other area/windows for clean swap */
			screen_swapbuffers();

			persp(PERSP_WIN);
			
			glDrawBuffer(GL_FRONT);
			
			BIF_ThemeColor(TH_WIRE);

			setlinestyle(3);
			glBegin(GL_LINE_STRIP); 
				glVertex2sv(mval); 
				glVertex2sv(oval); 
			glEnd();
			setlinestyle(0);
			
			persp(PERSP_VIEW);
			glFlush(); // flush display for frontbuffer
			glDrawBuffer(GL_BACK);
		}
		while(qtest()) {
			unsigned short val=0;			
			event= extern_qread(&val);	// extern_qread stores important events for the mainloop to handle 

			/* val==0 on key-release event */
			if(val && (event==ESCKEY || event==RIGHTMOUSE || event==LEFTMOUSE || event==RETKEY || event==ESCKEY)){
				if (event==RIGHTMOUSE || event==ESCKEY)
					Canceled = 1;
				Finished = 1;
			}
			else if (val && event==SPACEKEY) {
				if (fbutton(&d, 0.000, 10.000, 10, 0, "Width:")!=0) {
					drawd = d * fac;
					Finished = 1;
				}
			}
			else if (val) {
				/* On any other keyboard event, recalc */
				Recalc = 1;
			}

		}	
	}
	if (Canceled==0) {
		SetBlenderCursor(BC_WAITCURSOR);
		undo_push_mesh("Bevel");
		bevel_mesh_recurs(drawd/fac, recurs, 1);
		righthandfaces(1);
		SetBlenderCursor(SYSCURSOR);
	}
}

void select_non_manifold(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;
	EditVlak *evl;

	/* Selects isolated verts, and edges that do not have 2 neighboring
	 * faces
	 */


	eve= em->verts.first;
	while(eve) {
		/* this will count how many edges are connected
		 * to this vert */
		eve->f1= 0;
		eve= eve->next;
	}

	eed= em->edges.first;
	while(eed) {
		/* this will count how many faces are connected to
		 * this edge */
		eed->f1= 0;
		/* increase edge count for verts */
		++eed->v1->f1;
		++eed->v2->f1;
		eed= eed->next;
	}

	evl= em->faces.first;
	while(evl) {
		/* increase face count for edges */
		++evl->e1->f1;
		++evl->e2->f1;
		++evl->e3->f1;
		if (evl->e4)
			++evl->e4->f1;			
		evl= evl->next;
	}

	/* select verts that are attached to an edge that does not
	 * have 2 neighboring faces */
	eed= em->edges.first;
	while(eed) {
		if (eed->f1 != 2) {
			if (!eed->v1->h) eed->v1->f |= 1;
			if (!eed->v2->h) eed->v2->f |= 1;
		}
		eed= eed->next;
	}

	/* select isolated verts */
	eve= em->verts.first;
	while(eve) {
		if (eve->f1 == 0) {
			if (!eve->h) eve->f |= 1;
		}
		eve= eve->next;
	}

	countall();
	addqueue(curarea->win,  REDRAW, 0);

}

void select_more(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;

	eve= em->verts.first;
	while(eve) {
		eve->f1 = 0;
		eve= eve->next;
	}

	eed= em->edges.first;
	while(eed) {
		if (eed->v1->f & 1)
			eed->v2->f1 = 1;
		if (eed->v2->f & 1)
			eed->v1->f1 = 1;

		eed= eed->next;
	}

	eve= em->verts.first;
	while(eve) {
		if (eve->f1 == 1)
			if (!eve->h) eve->f |= 1;

		eve= eve->next;
	}

	countall();
	addqueue(curarea->win,  REDRAW, 0);
}

void select_less(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;
	EditVlak *evl;

	/* eve->f1 & 1 => isolated   */
	/* eve->f1 & 2 => on an edge */
	/* eve->f1 & 4 => shares edge with a deselected vert */ 
	/* eve->f1 & 8 => at most one neighbor */ 

	eve= em->verts.first;
	while(eve) {
		/* assume vert is isolated unless proven otherwise, */
		/* assume at most one neighbor too */
		eve->f1 = 1 | 8;

		eve= eve->next;
	}

	eed= em->edges.first;
	while(eed) {
		/* this will count how many faces are connected to
		 * this edge */
		eed->f1= 0;

		/* if vert wasn't isolated, it now has more than one neighbor */
		if (~eed->v1->f1 & 1) eed->v1->f1 &= ~8;
		if (~eed->v2->f1 & 1) eed->v2->f1 &= ~8;

		/* verts on edge are clearly not isolated */
		eed->v1->f1 &= ~1;
		eed->v2->f1 &= ~1;

		/* if one of the verts on the edge is deselected, 
		 * deselect the other */
		if ( !(eed->v1->h) && (~eed->v1->f & 1) )
			eed->v2->f1 |= 4;
		if ( !(eed->v2->h) && (~eed->v2->f & 1) )
			eed->v1->f1 |= 4;

		eed= eed->next;
	}

	evl= em->faces.first;
	while(evl) {
		/* increase face count for edges */
		++evl->e1->f1;
		++evl->e2->f1;
		++evl->e3->f1;
		if (evl->e4)
			++evl->e4->f1;			

		evl= evl->next;
	}

	eed= em->edges.first;
	while(eed) {
		/* if the edge has only one neighboring face, then
		 * deselect attached verts */
		if (eed->f1 == 1) {
			eed->v1->f1 |= 2;
			eed->v2->f1 |= 2;
		}

		eed= eed->next;
	}

	/* deselect verts */
	eve= em->verts.first;
	while(eve) {
		if (eve->f1) {
			eve->f &= ~1;
		}

		eve= eve->next;
	}

	countall();
	allqueue(REDRAWVIEW3D, 0);
}


void selectrandom_mesh(void) /* randomly selects a user-set % of vertices */
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	int newsel = 0; /* to decide whether to redraw or not */
	short randfac = 50;

	if(G.obedit==0) return;

	/* Get the percentage of vertices to randomly select as 'randfac' */
	if(button(&randfac,0, 100,"Percentage:")==0) return;
		
	if(G.obedit->lay & G.vd->lay) {
		eve= em->verts.first;
		while(eve) {
			BLI_srand( BLI_rand() ); /* random seed */
			if ( (BLI_frand() * 100) < randfac) {
					eve->f |= SELECT;
					newsel = 1;
			} else {
				/* Deselect other vertices
				 *
				 * - Commenting this out makes it add to the selection, 
				 * rather than replace it.
				 * eve->f &= ~SELECT;
				 */
			}
			eve= eve->next;
		}
		countall();
		allqueue(REDRAWVIEW3D, 0);
	}
}

short edgeFaces(EditEdge *e){
	EditMesh *em = G.editMesh;
	EditVlak *search=NULL;
	short count = 0;
	
	search = em->faces.first;
	while(search){
		if((search->e1 == e || search->e2 == e) || (search->e3 == e || search->e4 == e)) 
			count++;
	search = search->next;
	}
	return count;	
}

/* this utility function checks to see if 2 edit edges share a face,
	returns 1 if they do
	returns 0 if they do not, or if the function is passed the same edge 2 times
*/
short sharesFace(EditEdge* e1, EditEdge* e2)
{
	EditMesh *em = G.editMesh;
	EditVlak *search=NULL;
	search = em->faces.first;
	if (e1 == e2){
		return 0 ;
	}
	while(search){
		if(
			((search->e1 == e1 || search->e2 == e1) || (search->e3 == e1 || search->e4 == e1)) &&
			((search->e1 == e2 || search->e2 == e2) || (search->e3 == e2 || search->e4 == e2))
			) {
			return 1;
		}
		search = search->next;
	}
	return 0;
}
/* This function selects a vertex loop based on a each succesive edge having a valance of 4
   and not sharing a face with the previous edge */
    
void vertex_loop_select() 
{
	EditMesh *em = G.editMesh;
	EditVert *v1=NULL,*v2=NULL;
	EditEdge *search=NULL,*startEdge=NULL,*valSearch = NULL,*nearest = NULL,*compEdge;
	EditEdge *EdgeVal[5] = {NULL,NULL,NULL,NULL,NULL};
	short numEdges=0,curEdge = 0,looking = 1,edgeValCount = 0,i=0,looped = 0,choosing = 1,event,noloop=0,cancel=0, val;
	short protect = 0;
	short mvalo[2] = {0,0}, mval[2];

	undo_push_mesh("Select Vertex Loop");
	SetBlenderCursor(BC_VLOOPCURSOR);
	for(search=em->edges.first;search;search=search->next)
		numEdges++;

	/* start with v1 and go in one direction. */
	while(choosing){
		getmouseco_areawin(mval);
		if (mval[0] != mvalo[0] || mval[1] != mvalo[1]) {

			mvalo[0] = mval[0];
			mvalo[1] = mval[1];

			scrarea_do_windraw(curarea);
			nearest = findnearestedge();
			if (nearest && edgeFaces(nearest)==2) {
				for(search = em->edges.first;search;search=search->next)
					search->f &= ~32;
					
				compEdge = startEdge = nearest;
				nearest->f |= 32;
				curEdge = 0;
				v1 = startEdge->v1;
				v2 = startEdge->v2;
				looking = 1;
				while(looking){
					if(protect++ > numEdges) break;
					if(edgeFaces(compEdge) != 2) break;
					/*Find Edges that have v1*/
					edgeValCount = -1;
					EdgeVal[0] = EdgeVal[1] = EdgeVal[2] = NULL;
					
					for(valSearch = em->edges.first;valSearch;valSearch = valSearch->next){
						if(valSearch->v1 == v1 || valSearch->v2 == v1){
							if(valSearch != compEdge){
								if((valSearch->v1->h == 0) && (valSearch->v2->h == 0)){
									if(edgeFaces(valSearch) == 2){
										edgeValCount++;							
										EdgeVal[edgeValCount] = valSearch;
									}
								}
							}
						}
						if(edgeValCount == 3)break;
					}
					/* Check that there was a valance of 4*/
					if(edgeValCount != 2){
						noloop = 1;
						looking = 0;
						break;
					}
					else{
					/* There were 3 edges, so find the one that does not share the previous edge */
						for(i=0;i<3;i++){
							if(sharesFace(compEdge,EdgeVal[i]) == 0){
								/* We went all the way around the loop */
								if(EdgeVal[i] == nearest){
									looking = 0;
									looped = 1;
									break;
								}
								else{
									/* we are still in the loop, so add the next edge*/
									curEdge++;
									EdgeVal[i]->f |= 32;
									compEdge = EdgeVal[i];
									if(compEdge->v1 == v1)
										v1 = compEdge->v2;
									else
										v1 = compEdge->v1;
								}
							}
						}
					}
				}	
				compEdge = nearest;
				looking = 1;
				protect = 0;
				while(looking/* && !looped*/){
					if(protect++ > numEdges) break;
					if(edgeFaces(compEdge) != 2) break;
					/*Find Edges that have v1*/
					edgeValCount = -1;
					EdgeVal[0] = EdgeVal[1] = EdgeVal[2] = NULL;
					
					for(valSearch = em->edges.first;valSearch;valSearch = valSearch->next){
						if(valSearch->v1 == v2 || valSearch->v2 == v2){
							if(valSearch != compEdge){
								if((valSearch->v1->h == 0) && (valSearch->v2->h == 0)){
									if(edgeFaces(valSearch) == 2){
										edgeValCount++;							
										EdgeVal[edgeValCount] = valSearch;
									}
								}
							}
						}
						if(edgeValCount == 3)break;
					}
					/* Check that there was a valance of 4*/
					if(edgeValCount != 2){
						noloop = 1;
						looking = 0;
						break;
					}
					else{
					/* There were 3 edges, so find the one that does not share the previous edge */
						for(i=0;i<3;i++){
							if(sharesFace(compEdge,EdgeVal[i]) == 0){
								/* We went all the way around the loop */
								if(EdgeVal[i] == nearest){
									looking = 0;
									looped = 1;
									break;
								}
								else{
									/* we are still in the loop, so add the next edge*/
									curEdge++;
									EdgeVal[i]->f |= 32;
									compEdge = EdgeVal[i];
									if(compEdge->v1 == v2)
										v2 = compEdge->v2;
									else
										v2 = compEdge->v1;
								}
							}
						}
					}
				}
				/* set up for opengl drawing in the 3d window */
				persp(PERSP_VIEW);
				glPushMatrix();
				mymultmatrix(G.obedit->obmat);
				glColor3ub(0, 255, 255);
				for(search = em->edges.first;search;search= search->next){
					if(search->f & 32){
						glBegin(GL_LINES);			
						glVertex3f(search->v1->co[0],search->v1->co[1],search->v1->co[2]);
						glVertex3f(search->v2->co[0],search->v2->co[1],search->v2->co[2]);
						glEnd();
					}
				}		

				glPopMatrix();
			}
		}

		screen_swapbuffers();

		while(qtest()) 
		{
			val=0;
			event= extern_qread(&val);
			if(val && ((event==LEFTMOUSE || event==RETKEY) || event == MIDDLEMOUSE))
			{
				if (nearest==NULL)
					cancel = 1;
				choosing=0;
				break;
			}
			if(val && (event==ESCKEY || event==RIGHTMOUSE ))
			{
				choosing=0;
				cancel = 1;
				break;
			}
			if(val && (event==BKEY && G.qual==LR_ALTKEY ))
			{			
				
				SetBlenderCursor(SYSCURSOR);
				loopoperations(LOOP_SELECT);
				return;
			}
		}
	}
	if(!cancel){
		/* If this is a unmodified select, clear the selection */
		if(!(G.qual & LR_SHIFTKEY) && !(G.qual & LR_ALTKEY)){
			for(search = em->edges.first;search;search= search->next){
				search->v1->f &= !1;
				search->v2->f &= !1;
			}
		}
		/* Alt was not pressed, so add to the selection */
		if(!(G.qual & LR_ALTKEY)){
			for(search = em->edges.first;search;search= search->next){
				if(search->f & 32){
					search->v1->f |= 1;
					search->v2->f |= 1;
				}
				search->f &= ~32;
			}
		}
		/* alt was pressed, so subtract from the selection */
		else
		{
			for(search = em->edges.first;search;search= search->next){
				if(search->f & 32){
					search->v1->f &= !1;
					search->v2->f &= !1;
				}
				search->f &= ~32;
			}
		}
	}
	else
		undo_pop_mesh(1);
	addqueue(curarea->win, REDRAW, 1); 
	SetBlenderCursor(SYSCURSOR);
	return;
}

void editmesh_select_by_material(int index) {
	EditMesh *em = G.editMesh;
	EditVlak *evl;
	
	for (evl=em->faces.first; evl; evl= evl->next) {
		if (evl->mat_nr==index) {
			if(evl->v1->h==0) evl->v1->f |= 1;
			if(evl->v2->h==0) evl->v2->f |= 1;
			if(evl->v3->h==0) evl->v3->f |= 1;
			if(evl->v4 && evl->v4->h==0) evl->v4->f |= 1;
		}
	}
}

void editmesh_deselect_by_material(int index) {
	EditMesh *em = G.editMesh;
	EditVlak *evl;
	
	for (evl=em->faces.first; evl; evl= evl->next) {
		if (evl->mat_nr==index) {
			if(evl->v1->h==0) evl->v1->f &= ~1;
			if(evl->v2->h==0) evl->v2->f &= ~1;
			if(evl->v3->h==0) evl->v3->f &= ~1;
			if(evl->v4 && evl->v4->h==0) evl->v4->f &= ~1;
		}
	}
}
