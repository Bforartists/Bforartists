
/*  mesh.c
 *
 *  
 * 
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

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_ID.h"
#include "DNA_curve_types.h"
#include "DNA_material_types.h"
#include "DNA_object_types.h"
#include "DNA_image_types.h"
#include "DNA_key_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"

#include "BKE_depsgraph.h"
#include "BKE_main.h"
#include "BKE_DerivedMesh.h"
#include "BKE_global.h"
#include "BKE_mesh.h"
#include "BKE_subsurf.h"
#include "BKE_displist.h"
#include "BKE_library.h"
#include "BKE_material.h"
#include "BKE_key.h"
/* these 2 are only used by conversion functions */
#include "BKE_curve.h"
/* -- */
#include "BKE_object.h"
#include "BKE_utildefines.h"
#include "BKE_bad_level_calls.h"

#include "BLI_blenlib.h"
#include "BLI_editVert.h"
#include "BLI_arithb.h"



int update_realtime_texture(TFace *tface, double time)
{
	Image *ima;
	int	inc = 0;
	float	diff;
	int	newframe;

	ima = tface->tpage;

	if (!ima)
		return 0;

	if (ima->lastupdate<0)
		ima->lastupdate = 0;

	if (ima->lastupdate>time)
		ima->lastupdate=(float)time;

	if(ima->tpageflag & IMA_TWINANIM) {
		if(ima->twend >= ima->xrep*ima->yrep) ima->twend= ima->xrep*ima->yrep-1;
		
		/* check: is the bindcode not in the array? Then free. (still to do) */
		
		diff = (float)(time-ima->lastupdate);

		inc = (int)(diff*(float)ima->animspeed);

		ima->lastupdate+=((float)inc/(float)ima->animspeed);

		newframe = ima->lastframe+inc;

		if (newframe > (int)ima->twend)
			newframe = (int)ima->twsta-1 + (newframe-ima->twend)%(ima->twend-ima->twsta);

		ima->lastframe = newframe;
	}
	return inc;
}

void unlink_mesh(Mesh *me)
{
	int a;
	
	if(me==0) return;
	
	for(a=0; a<me->totcol; a++) {
		if(me->mat[a]) me->mat[a]->id.us--;
		me->mat[a]= 0;
	}
	if(me->key) me->key->id.us--;
	me->key= 0;
	
	if(me->texcomesh) me->texcomesh= 0;
}


/* do not free mesh itself */
void free_mesh(Mesh *me)
{
	unlink_mesh(me);

	if(me->mvert) MEM_freeN(me->mvert);
	if(me->medge) MEM_freeN(me->medge);
	if(me->mface) MEM_freeN(me->mface);
	
	if(me->tface) MEM_freeN(me->tface);
	if(me->dvert) free_dverts(me->dvert, me->totvert);
	if(me->mcol) MEM_freeN(me->mcol);
	if(me->msticky) MEM_freeN(me->msticky);

	if(me->mat) MEM_freeN(me->mat);
	
	if(me->bb) MEM_freeN(me->bb);
}

void copy_dverts(MDeformVert *dst, MDeformVert *src, int copycount)
{
	/* Assumes dst is already set up */
	int i;

	if (!src || !dst)
		return;

	memcpy (dst, src, copycount * sizeof(MDeformVert));
	
	for (i=0; i<copycount; i++){
		if (src[i].dw){
			dst[i].dw = MEM_callocN (sizeof(MDeformWeight)*src[i].totweight, "copy_deformWeight");
			memcpy (dst[i].dw, src[i].dw, sizeof (MDeformWeight)*src[i].totweight);
		}
	}

}
void free_dverts(MDeformVert *dvert, int totvert)
{
	/* Instead of freeing the verts directly,
	call this function to delete any special
	vert data */
	int	i;

	if (!dvert)
		return;

	/* Free any special data from the verts */
	for (i=0; i<totvert; i++){
		if (dvert[i].dw) MEM_freeN (dvert[i].dw);
	}
	MEM_freeN (dvert);
}

Mesh *add_mesh()
{
	Mesh *me;
	
	me= alloc_libblock(&G.main->mesh, ID_ME, "Mesh");
	
	me->size[0]= me->size[1]= me->size[2]= 1.0;
	me->smoothresh= 30;
	me->texflag= AUTOSPACE;
	me->flag= ME_TWOSIDED;
	me->subdiv= 1;
	me->subdivr = 1;
	me->bb= unit_boundbox();
	
	return me;
}

Mesh *copy_mesh(Mesh *me)
{
	Mesh *men;
	int a;
	
	men= copy_libblock(me);
	
	men->mat= MEM_dupallocN(me->mat);
	for(a=0; a<men->totcol; a++) {
		id_us_plus((ID *)men->mat[a]);
	}
	id_us_plus((ID *)men->texcomesh);

	men->mvert= MEM_dupallocN(me->mvert);
	men->medge= MEM_dupallocN(me->medge);
	men->mface= MEM_dupallocN(me->mface);
	men->tface= MEM_dupallocN(me->tface);
	men->dface= NULL;

	if (me->dvert){
		men->dvert = MEM_mallocN (sizeof (MDeformVert)*me->totvert, "MDeformVert");
		copy_dverts(men->dvert, me->dvert, me->totvert);
	}

	men->mcol= MEM_dupallocN(me->mcol);
	men->msticky= MEM_dupallocN(me->msticky);
	men->texcomesh= NULL;
	men->bb= MEM_dupallocN(men->bb);
	
	men->key= copy_key(me->key);
	if(men->key) men->key->from= (ID *)men;
	
	men->decimated = NULL;

	return men;
}

void make_local_tface(Mesh *me)
{
	TFace *tface;
	Image *ima;
	int a;
	
	if(me->tface==0) return;
	
	a= me->totface;
	tface= me->tface;
	while(a--) {
		
		/* special case: ima always local immediately */
		if(tface->tpage) {
			ima= tface->tpage;
			if(ima->id.lib) {
				ima->id.lib= 0;
				ima->id.flag= LIB_LOCAL;
				new_id(0, (ID *)ima, 0);
			}
		}
		tface++;
	}
	
}

void make_local_mesh(Mesh *me)
{
	Object *ob;
	Mesh *men;
	int local=0, lib=0;

	/* - only lib users: do nothing
	    * - only local users: set flag
	    * - mixed: make copy
	    */
	
	if(me->id.lib==0) return;
	if(me->id.us==1) {
		me->id.lib= 0;
		me->id.flag= LIB_LOCAL;
		new_id(0, (ID *)me, 0);
		
		if(me->tface) make_local_tface(me);
		
		return;
	}
	
	ob= G.main->object.first;
	while(ob) {
		if( me==get_mesh(ob) ) {
			if(ob->id.lib) lib= 1;
			else local= 1;
		}
		ob= ob->id.next;
	}
	
	if(local && lib==0) {
		me->id.lib= 0;
		me->id.flag= LIB_LOCAL;
		new_id(0, (ID *)me, 0);
		
		if(me->tface) make_local_tface(me);
		
	}
	else if(local && lib) {
		men= copy_mesh(me);
		men->id.us= 0;
		
		ob= G.main->object.first;
		while(ob) {
			if( me==get_mesh(ob) ) {				
				if(ob->id.lib==0) {
					set_mesh(ob, men);
				}
			}
			ob= ob->id.next;
		}
	}
}

void boundbox_mesh(Mesh *me, float *loc, float *size)
{
	MVert *mvert;
	BoundBox *bb;
	float min[3], max[3];
	float mloc[3], msize[3];
	int a;
	
	if(me->bb==0) me->bb= MEM_callocN(sizeof(BoundBox), "boundbox");
	bb= me->bb;
	
	INIT_MINMAX(min, max);

	if (!loc) loc= mloc;
	if (!size) size= msize;
	
	mvert= me->mvert;
	for(a=0; a<me->totvert; a++, mvert++) {
		DO_MINMAX(mvert->co, min, max);
	}

	if(!me->totvert) {
		min[0] = min[1] = min[2] = -1.0f;
		max[0] = max[1] = max[2] = 1.0f;
	}

	loc[0]= (min[0]+max[0])/2.0f;
	loc[1]= (min[1]+max[1])/2.0f;
	loc[2]= (min[2]+max[2])/2.0f;
		
	size[0]= (max[0]-min[0])/2.0f;
	size[1]= (max[1]-min[1])/2.0f;
	size[2]= (max[2]-min[2])/2.0f;
	
	boundbox_set_from_min_max(bb, min, max);
}

void tex_space_mesh(Mesh *me)
{
	KeyBlock *kb;
	float *fp, loc[3], size[3], min[3], max[3];
	int a;

	boundbox_mesh(me, loc, size);

	if(me->texflag & AUTOSPACE) {
		if(me->key) {
			kb= me->key->refkey;
			if (kb) {
				
				INIT_MINMAX(min, max);
				
				fp= kb->data;
				for(a=0; a<kb->totelem; a++, fp+=3) {	
					DO_MINMAX(fp, min, max);
				}
				if(kb->totelem) {
					loc[0]= (min[0]+max[0])/2.0f; loc[1]= (min[1]+max[1])/2.0f; loc[2]= (min[2]+max[2])/2.0f;
					size[0]= (max[0]-min[0])/2.0f; size[1]= (max[1]-min[1])/2.0f; size[2]= (max[2]-min[2])/2.0f;
				}
				else {
					loc[0]= loc[1]= loc[2]= 0.0;
					size[0]= size[1]= size[2]= 0.0;
				}
				
			}
		}

		for (a=0; a<3; a++) {
			if(size[a]==0.0) size[a]= 1.0;
			else if(size[a]>0.0 && size[a]<0.00001) size[a]= 0.00001;
			else if(size[a]<0.0 && size[a]> -0.00001) size[a]= -0.00001;
		}

		VECCOPY(me->loc, loc);
		VECCOPY(me->size, size);
		me->rot[0]= me->rot[1]= me->rot[2]= 0.0;
	}
}

BoundBox *mesh_get_bb(Mesh *me)
{
	if (!me->bb) {
		tex_space_mesh(me);
	}

	return me->bb;
}

void mesh_get_texspace(Mesh *me, float *loc_r, float *rot_r, float *size_r)
{
	if (!me->bb) {
		tex_space_mesh(me);
	}

	if (loc_r) VECCOPY(loc_r, me->loc);
	if (rot_r) VECCOPY(rot_r, me->rot);
	if (size_r) VECCOPY(size_r, me->size);
}

static float *make_orco_mesh_internal(Object *ob, int render)
{
	Mesh *me = ob->data;
	float (*orcoData)[3];
	int a, totvert;
	float loc[3], size[3];
	DerivedMesh *dm;
	float (*vcos)[3] = MEM_callocN(sizeof(*vcos)*me->totvert, "orco mesh");

		/* Get appropriate vertex coordinates */

	if(me->key && me->texcomesh==0 && me->key->refkey) {
		KeyBlock *kb= me->key->refkey;
		float *fp= kb->data;
		totvert= MIN2(kb->totelem, me->totvert);

		for(a=0; a<totvert; a++, fp+=3) {
			vcos[a][0]= fp[0];
			vcos[a][1]= fp[1];
			vcos[a][2]= fp[2];
		}
	}
	else {
		Mesh *tme = me->texcomesh?me->texcomesh:me;
		MVert *mvert = tme->mvert;
		totvert = MIN2(tme->totvert, me->totvert);

		for(a=0; a<totvert; a++, mvert++) {
			vcos[a][0]= mvert->co[0];
			vcos[a][1]= mvert->co[1];
			vcos[a][2]= mvert->co[2];
		}
	}

		/* Apply orco-changing modifiers */

	if (render) {
		dm = mesh_create_derived_no_deform_render(ob, vcos);
	} else {
		dm = mesh_create_derived_no_deform(ob, vcos);
	}
	totvert = dm->getNumVerts(dm);

	orcoData = MEM_mallocN(sizeof(*orcoData)*totvert, "orcoData");
	dm->getVertCos(dm, orcoData);
	dm->release(dm);
	MEM_freeN(vcos);

	mesh_get_texspace(me, loc, NULL, size);

	for(a=0; a<totvert; a++) {
		float *co = orcoData[a];
		co[0] = (co[0]-loc[0])/size[0];
		co[1] = (co[1]-loc[1])/size[1];
		co[2] = (co[2]-loc[2])/size[2];
	}

	return (float*) orcoData;
}

float *mesh_create_orco_render(Object *ob) 
{
	return make_orco_mesh_internal(ob, 1);
}

float *mesh_create_orco(Object *ob)
{
	return make_orco_mesh_internal(ob, 0);
}

/** rotates the vertices of a face in case v[2] or v[3] (vertex index)
  * is = 0.
  * Helaas, the MFace structure has no pointer to its
  * texture face, therefore, texture can not be fixed inside
  * this function. 
  * 
  * see also blender/src/editmesh.c, fix_faceindices()

  * THIS FUNCTION WILL BE DINOSOURCE. For the moment, another hack
	is added to fix texture coordinates / vertex colors:

	void test_index_face(MFace *mface, TFace *tface, int nr)
  */

void test_index_mface(MFace *mface, int nr)
{
	int a;

	
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

	/* prevent a zero at wrong index location */
	if(nr==2) {
		if(mface->v2==0) SWAP(int, mface->v1, mface->v2);
	}
	else if(nr==3) {
		if(mface->v3==0) {
			SWAP(int, mface->v1, mface->v2);
			SWAP(int, mface->v2, mface->v3);
			
			a= mface->edcode;
			mface->edcode= 0;
			if(a & ME_V1V2) mface->edcode |= ME_V3V1;
			if(a & ME_V2V3) mface->edcode |= ME_V1V2;
			if(a & ME_V3V1) mface->edcode |= ME_V2V3;
		}
	}
	else if(nr==4) {
		if(mface->v3==0 || mface->v4==0) {
			SWAP(int, mface->v1, mface->v3);
			SWAP(int, mface->v2, mface->v4);
			a= mface->edcode;
			mface->edcode= 0;
			if(a & ME_V1V2) mface->edcode |= ME_V3V4;
			if(a & ME_V2V3) mface->edcode |= ME_V2V3;
			if(a & ME_V3V4) mface->edcode |= ME_V1V2;
			if(a & ME_V4V1) mface->edcode |= ME_V4V1;
		}
	}
}

/**	This function should die as soon as there is another mesh
	structure. Functionality is the same as

		void test_index_mface()

	but it fixes texture coordinates as well. 
*/

#define UVCOPY(t, s) memcpy(t, s, 2 * sizeof(float));
void test_index_face(MFace *mface, TFace *tface, int nr)
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

	/* prevent a zero at wrong index location */
	if(nr==2) {
		if(mface->v2==0) SWAP(int, mface->v1, mface->v2);
	}
	else if(nr==3) {
		if(mface->v3==0) {
			SWAP(int, mface->v1, mface->v2);
			SWAP(int, mface->v2, mface->v3);
			/* rotate face UV coordinates, too */
			UVCOPY(tmpuv, tface->uv[0]);
			UVCOPY(tface->uv[0], tface->uv[1]);
			UVCOPY(tface->uv[1], tface->uv[2]);
			UVCOPY(tface->uv[2], tmpuv);
			/* same with vertex colours */
			tmpcol = tface->col[0];
			tface->col[0] = tface->col[1];
			tface->col[1] = tface->col[2];
			tface->col[2] = tmpcol;

			
			a= mface->edcode;
			mface->edcode= 0;
			if(a & ME_V1V2) mface->edcode |= ME_V3V1;
			if(a & ME_V2V3) mface->edcode |= ME_V1V2;
			if(a & ME_V3V1) mface->edcode |= ME_V2V3;
		}
	}
	else if(nr==4) {
		if(mface->v3==0 || mface->v4==0) {
			SWAP(int, mface->v1, mface->v3);
			SWAP(int, mface->v2, mface->v4);
			/* swap UV coordinates */
			UVCOPY(tmpuv, tface->uv[0]);
			UVCOPY(tface->uv[0], tface->uv[2]);
			UVCOPY(tface->uv[2], tmpuv);
			UVCOPY(tmpuv, tface->uv[1]);
			UVCOPY(tface->uv[1], tface->uv[3]);
			UVCOPY(tface->uv[3], tmpuv);
			/* swap vertex colours */
			tmpcol = tface->col[0];
			tface->col[0] = tface->col[2];
			tface->col[2] = tmpcol;
			tmpcol = tface->col[1];
			tface->col[1] = tface->col[3];
			tface->col[3] = tmpcol;

			a= mface->edcode;
			mface->edcode= 0;
			if(a & ME_V1V2) mface->edcode |= ME_V3V4;
			if(a & ME_V2V3) mface->edcode |= ME_V2V3;
			if(a & ME_V3V4) mface->edcode |= ME_V1V2;
			if(a & ME_V4V1) mface->edcode |= ME_V4V1;
		}
	}
}

void flipnorm_mesh(Mesh *me)
{
	MFace *mface;
	MVert *mvert;
	int a;
	
	mvert= me->mvert;
	a= me->totvert;
	while(a--) {
		mvert->no[0]= -mvert->no[0];
		mvert->no[1]= -mvert->no[1];
		mvert->no[2]= -mvert->no[2];
		mvert++;
	}
	
	mface= me->mface;
	a= me->totface;
	while(a--) {
		if(mface->v3) {
			if(mface->v4) {
				SWAP(int, mface->v4, mface->v1);
				SWAP(int, mface->v3, mface->v2);
				test_index_mface(mface, 4);
			}
			else {
				SWAP(int, mface->v3, mface->v1);
				test_index_mface(mface, 3);
			}
		}
		mface++;
	}
}

Mesh *get_mesh(Object *ob)
{
	
	if(ob==0) return 0;
	if(ob->type==OB_MESH) return ob->data;
	else return 0;
}

void set_mesh(Object *ob, Mesh *me)
{
	Mesh *old=0;
	
	if(ob==0) return;
	
	if(ob->type==OB_MESH) {
		old= ob->data;
		old->id.us--;
		ob->data= me;
		id_us_plus((ID *)me);
	}
	
	test_object_materials((ID *)me);
}

/* ************** make edges in a Mesh, for outside of editmode */

struct edgesort {
	int v1, v2;
	int flag;
};

/* edges have to be added with lowest index first for sorting */
static void to_edgesort(struct edgesort *ed, int v1, int v2, int flag)
{
	if(v1<v2) {
		ed->v1= v1; ed->v2= v2;
	}
	else {
		ed->v1= v2; ed->v2= v1;
	}
	ed->flag= flag;
}

static int vergedgesort(const void *v1, const void *v2)
{
	const struct edgesort *x1=v1, *x2=v2;

	if( x1->v1 > x2->v1) return 1;
	else if( x1->v1 < x2->v1) return -1;
	else if( x1->v2 > x2->v2) return 1;
	else if( x1->v2 < x2->v2) return -1;
	
	return 0;
}


void make_edges(Mesh *me)
{
	MFace *mface;
	MEdge *medge;
	struct edgesort *edsort, *ed;
	int a, totedge=0, final=0;
	
	/* we put all edges in array, sort them, and detect doubles that way */
	
	for(a= me->totface, mface= me->mface; a>0; a--, mface++) {
		if(mface->v4) totedge+=4;
		else if(mface->v3) totedge+=3;
		else totedge+=1;
	}
	
	if(totedge==0) {
			/* flag that mesh has edges */
		me->medge = MEM_callocN(0, "make mesh edges");
		me->totedge = 0;
		return;
	}
	
	ed= edsort= MEM_mallocN(totedge*sizeof(struct edgesort), "edgesort");
	
	for(a= me->totface, mface= me->mface; a>0; a--, mface++) {
		
		to_edgesort(ed, mface->v1, mface->v2, mface->edcode & ME_V1V2);
		ed++;
		if(mface->v4) {
			to_edgesort(ed, mface->v2, mface->v3, mface->edcode & ME_V2V3);
			ed++;
			to_edgesort(ed, mface->v3, mface->v4, mface->edcode & ME_V3V4);
			ed++;
			to_edgesort(ed, mface->v4, mface->v1, mface->edcode & ME_V4V1);
			ed++;
		}
		else if(mface->v3) {
			to_edgesort(ed, mface->v2, mface->v3, mface->edcode & ME_V2V3);
			ed++;
			to_edgesort(ed, mface->v3, mface->v1, mface->edcode & ME_V3V1);
			ed++;
		}
	}
	
	qsort(edsort, totedge, sizeof(struct edgesort), vergedgesort);
	
	/* count final amount */
	for(a=totedge, ed=edsort; a>1; a--, ed++) {
		/* edge is unique when it differs from next edge, or is last */
		if(ed->v1 != (ed+1)->v1 || ed->v2 != (ed+1)->v2) final++;
		else {
			/* this makes sure identical edges both get draw flag */
			if(ed->flag) (ed+1)->flag= 1;
			else if((ed+1)->flag) ed->flag= 1;
		}
	}
	final++;
	
	medge= me->medge= MEM_callocN(final*sizeof(MEdge), "make mesh edges");
	me->totedge= final;
	
	for(a=totedge, ed=edsort; a>1; a--, ed++) {
		/* edge is unique when it differs from next edge, or is last */
		if(ed->v1 != (ed+1)->v1 || ed->v2 != (ed+1)->v2) {
			medge->v1= ed->v1;
			medge->v2= ed->v2;
			if(ed->flag) medge->flag= ME_EDGEDRAW;
			medge++;
		}
	}
	/* last edge */
	medge->v1= ed->v1;
	medge->v2= ed->v2;
	if(ed->flag) medge->flag= ME_EDGEDRAW;

	MEM_freeN(edsort);
}



void mball_to_mesh(ListBase *lb, Mesh *me)
{
	DispList *dl;
	MVert *mvert;
	MFace *mface;
	float *nors, *verts;
	int a, *index;
	
	dl= lb->first;
	if(dl==0) return;

	if(dl->type==DL_INDEX4) {
		me->flag= ME_NOPUNOFLIP;
		me->totvert= dl->nr;
		me->totface= dl->parts;
		
		me->mvert=mvert= MEM_callocN(dl->nr*sizeof(MVert), "mverts");
		a= dl->nr;
		nors= dl->nors;
		verts= dl->verts;
		while(a--) {
			VECCOPY(mvert->co, verts);
			mvert->no[0]= (short int)(nors[0]*32767.0);
			mvert->no[1]= (short int)(nors[1]*32767.0);
			mvert->no[2]= (short int)(nors[2]*32767.0);
			mvert++;
			nors+= 3;
			verts+= 3;
		}
		
		me->mface=mface= MEM_callocN(dl->parts*sizeof(MFace), "mface");
		a= dl->parts;
		index= dl->index;
		while(a--) {
			mface->v1= index[0];
			mface->v2= index[1];
			mface->v3= index[2];
			mface->v4= index[3];

			mface->edcode= ME_V1V2+ME_V2V3;
			mface->flag = ME_SMOOTH;
			
			mface++;
			index+= 4;
		}
	}	
}

void nurbs_to_mesh(Object *ob)
{
	Object *ob1;
	DispList *dl;
	Mesh *me;
	Curve *cu;
	MVert *mvert;
	MFace *mface;
	float *data;
	int a, b, ofs, vertcount, startvert, totvert=0, totvlak=0;
	int p1, p2, p3, p4, *index;

	cu= ob->data;

	if(ob->type==OB_CURVE) {
		/* rule: dl->type INDEX3 always as first in list */
		dl= cu->disp.first;
		if(dl->type!=DL_INDEX3) {
			curve_to_filledpoly(ob->data, &cu->nurb, &cu->disp);
		}
	}

	/* count */
	dl= cu->disp.first;
	while(dl) {
		if(dl->type==DL_SEGM) {
			totvert+= dl->parts*dl->nr;
			totvlak+= dl->parts*(dl->nr-1);
		}
		else if(dl->type==DL_POLY) {
			/* cyclic polys are filled. except when 3D */
			if(cu->flag & CU_3D) {
				totvert+= dl->parts*dl->nr;
				totvlak+= dl->parts*dl->nr;
			}
		}
		else if(dl->type==DL_SURF) {
			totvert+= dl->parts*dl->nr;
			totvlak+= (dl->parts-1+((dl->flag & 2)==2))*(dl->nr-1+(dl->flag & 1));
		}
		else if(dl->type==DL_INDEX3) {
			totvert+= dl->nr;
			totvlak+= dl->parts;
		}
		dl= dl->next;
	}
	if(totvert==0) {
		error("can't convert");
		return;
	}

	/* make mesh */
	me= add_mesh();
	me->totvert= totvert;
	me->totface= totvlak;

	me->totcol= cu->totcol;
	me->mat= cu->mat;
	cu->mat= 0;
	cu->totcol= 0;

	mvert=me->mvert= MEM_callocN(me->totvert*sizeof(MVert), "cumesh1");
	mface=me->mface= MEM_callocN(me->totface*sizeof(MFace), "cumesh2");

	/* verts and faces */
	vertcount= 0;

	dl= cu->disp.first;
	while(dl) {
		if(dl->type==DL_SEGM) {
			startvert= vertcount;
			a= dl->parts*dl->nr;
			data= dl->verts;
			while(a--) {
				VECCOPY(mvert->co, data);
				data+=3;
				vertcount++;
				mvert++;
			}

			for(a=0; a<dl->parts; a++) {
				ofs= a*dl->nr;
				for(b=1; b<dl->nr; b++) {
					mface->v1= startvert+ofs+b-1;
					mface->v2= startvert+ofs+b;
					mface->edcode= ME_V1V2;
					test_index_mface(mface, 2);
					mface++;
				}
			}

		}
		else if(dl->type==DL_POLY) {
			/* 3d polys are not filled */
			if(cu->flag & CU_3D) {
				startvert= vertcount;
				a= dl->parts*dl->nr;
				data= dl->verts;
				while(a--) {
					VECCOPY(mvert->co, data);
					data+=3;
					vertcount++;
					mvert++;
				}
	
				for(a=0; a<dl->parts; a++) {
					ofs= a*dl->nr;
					for(b=0; b<dl->nr; b++) {
						mface->v1= startvert+ofs+b;
						if(b==dl->nr-1) mface->v2= startvert+ofs;
						else mface->v2= startvert+ofs+b+1;
						mface->edcode= ME_V1V2;
						test_index_mface(mface, 2);
						mface++;
					}
				}
			}
		}
		else if(dl->type==DL_INDEX3) {
			startvert= vertcount;
			a= dl->nr;
			data= dl->verts;
			while(a--) {
				VECCOPY(mvert->co, data);
				data+=3;
				vertcount++;
				mvert++;
			}

			a= dl->parts;
			index= dl->index;
			while(a--) {
				mface->v1= startvert+index[0];
				mface->v2= startvert+index[1];
				mface->v3= startvert+index[2];
				mface->v4= 0;
	
				mface->edcode= ME_V1V2+ME_V2V3;
				test_index_mface(mface, 3);
				
				mface++;
				index+= 3;
			}
	
	
		}
		else if(dl->type==DL_SURF) {
			startvert= vertcount;
			a= dl->parts*dl->nr;
			data= dl->verts;
			while(a--) {
				VECCOPY(mvert->co, data);
				data+=3;
				vertcount++;
				mvert++;
			}

			for(a=0; a<dl->parts; a++) {

				if( (dl->flag & 2)==0 && a==dl->parts-1) break;

				if(dl->flag & 1) {			/* p2 -> p1 -> */
					p1= startvert+ dl->nr*a;	/* p4 -> p3 -> */
					p2= p1+ dl->nr-1;		/* -----> next row */
					p3= p1+ dl->nr;
					p4= p2+ dl->nr;
					b= 0;
				}
				else {
					p2= startvert+ dl->nr*a;
					p1= p2+1;
					p4= p2+ dl->nr;
					p3= p1+ dl->nr;
					b= 1;
				}
				if( (dl->flag & 2) && a==dl->parts-1) {
					p3-= dl->parts*dl->nr;
					p4-= dl->parts*dl->nr;
				}

				for(; b<dl->nr; b++) {
					mface->v1= p1;
					mface->v2= p3;
					mface->v3= p4;
					mface->v4= p2;
					mface->mat_nr= (unsigned char)dl->col;
					mface->edcode= ME_V1V2+ME_V2V3;
					test_index_mface(mface, 4);
					mface++;

					p4= p3; 
					p3++;
					p2= p1; 
					p1++;
				}
			}

		}

		dl= dl->next;
	}

	if(ob->data) {
		free_libblock(&G.main->curve, ob->data);
	}
	ob->data= me;
	ob->type= OB_MESH;
	
	/* other users */
	ob1= G.main->object.first;
	while(ob1) {
		if(ob1->data==cu) {
			ob1->type= OB_MESH;
		
			ob1->data= ob->data;
			id_us_plus((ID *)ob->data);
		}
		ob1= ob1->id.next;
	}

}

void edge_drawflags_mesh(Mesh *me)
{
	MFace *mface;
	int a;
	
	mface= me->mface;
	for(a=0; a<me->totface; a++, mface++) {
		mface->edcode= ME_V1V2|ME_V2V3|ME_V3V4|ME_V4V1;
	}
}

void tface_to_mcol(Mesh *me)
{
	TFace *tface;
	unsigned int *mcol;
	int a;
	
	me->mcol= MEM_mallocN(4*sizeof(int)*me->totface, "nepmcol");
	mcol= (unsigned int *)me->mcol;
	
	a= me->totface;
	tface= me->tface;
	while(a--) {
		memcpy(mcol, tface->col, 16);
		mcol+= 4;
		tface++;
	}
}

void mcol_to_tface(Mesh *me, int freedata)
{
	TFace *tface;
	unsigned int *mcol;
	int a;
	
	a= me->totface;
	tface= me->tface;
	mcol= (unsigned int *)me->mcol;
	while(a--) {
		memcpy(tface->col, mcol, 16);
		mcol+= 4;
		tface++;
	}
	
	if(freedata) {
		MEM_freeN(me->mcol);
		me->mcol= 0;
	}
}

void mesh_delete_material_index(Mesh *me, int index) {
	int i;

	for (i=0; i<me->totface; i++) {
		MFace *mf = &((MFace*) me->mface)[i];
		if (mf->mat_nr && mf->mat_nr>=index) 
			mf->mat_nr--;
	}
}

void mesh_set_smooth_flag(Object *meshOb, int enableSmooth) {
	Mesh *me = meshOb->data;
	int i;

	for (i=0; i<me->totface; i++) {
		MFace *mf = &((MFace*) me->mface)[i];

		if (enableSmooth) {
			mf->flag |= ME_SMOOTH;
		} else {
			mf->flag &= ~ME_SMOOTH;
		}
	}

	DAG_object_flush_update(G.scene, meshOb, OB_RECALC_DATA);
}

void mesh_calc_normals(MVert *mverts, int numVerts, MFace *mfaces, int numFaces, float **faceNors_r) 
{
	float (*tnorms)[3]= MEM_callocN(numVerts*sizeof(*tnorms), "tnorms");
	float *fnors= MEM_mallocN(sizeof(*fnors)*3*numFaces, "meshnormals");
	int i;
	
	for (i=0; i<numFaces; i++) {
		MFace *mf= &mfaces[i];

		if (mf->v3) {
			float *f_no= &fnors[i*3];

			if (mf->v4)
				CalcNormFloat4(mverts[mf->v1].co, mverts[mf->v2].co, mverts[mf->v3].co, mverts[mf->v4].co, f_no);
			else
				CalcNormFloat(mverts[mf->v1].co, mverts[mf->v2].co, mverts[mf->v3].co, f_no);
			
			VecAddf(tnorms[mf->v1], tnorms[mf->v1], f_no);
			VecAddf(tnorms[mf->v2], tnorms[mf->v2], f_no);
			VecAddf(tnorms[mf->v3], tnorms[mf->v3], f_no);
			if (mf->v4)
				VecAddf(tnorms[mf->v4], tnorms[mf->v4], f_no);
		}
	}
	for (i=0; i<numVerts; i++) {
		MVert *mv= &mverts[i];
		float *no= tnorms[i];
		
		if (Normalise(no)==0.0) {
			VECCOPY(no, mv->co);
			Normalise(no);
		}

		mv->no[0]= (short)(no[0]*32767.0);
		mv->no[1]= (short)(no[1]*32767.0);
		mv->no[2]= (short)(no[2]*32767.0);
	}
	
	MEM_freeN(tnorms);

	if (faceNors_r) {
		*faceNors_r = fnors;
	} else {
		MEM_freeN(fnors);
	}
}

float (*mesh_getVertexCos(Mesh *me, int *numVerts_r))[3]
{
	int i, numVerts = me->totvert;
	float (*cos)[3] = MEM_mallocN(sizeof(*cos)*numVerts, "vertexcos1");

	if (numVerts_r) *numVerts_r = numVerts;
	for (i=0; i<numVerts; i++) {
		VECCOPY(cos[i], me->mvert[i].co);
	}

	return cos;
}
