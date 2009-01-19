/**
 * $Id$
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <math.h>
#include <string.h>

#ifdef WIN32
#include <io.h>
#else
#include <unistd.h>
#endif   

#include "MEM_guardedalloc.h"

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "MTC_matrixops.h"

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_brush_types.h"
#include "DNA_cloth_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_object_force.h"
#include "DNA_particle_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_view3d_types.h"
#include "DNA_userdef_types.h"

#include "BKE_armature.h"
#include "BKE_DerivedMesh.h"
#include "BKE_cloth.h"
#include "BKE_context.h"
#include "BKE_customdata.h"
#include "BKE_depsgraph.h"
#include "BKE_deform.h"
#include "BKE_displist.h"
#include "BKE_global.h"
#include "BKE_mesh.h"
#include "BKE_modifier.h"
#include "BKE_multires.h"
#include "BKE_object.h"
#include "BKE_utildefines.h"

#include "WM_api.h"
#include "WM_types.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "ED_mesh.h"
#include "ED_object.h"
#include "ED_screen.h"
#include "ED_util.h"
#include "ED_view3d.h"

#include "view3d_intern.h"

	/* vp->mode */
#define VP_MIX	0
#define VP_ADD	1
#define VP_SUB	2
#define VP_MUL	3
#define VP_BLUR	4
#define VP_LIGHTEN	5
#define VP_DARKEN	6

#define MAXINDEX	512000

/* XXX */
static void BIF_undo_push() {}
static void error() {}

static VPaint *new_vpaint(int wpaint)
{
	VPaint *vp= MEM_callocN(sizeof(VPaint), "VPaint");
	
	vp->r= 1.0f;
	vp->g= 1.0f;
	vp->b= 1.0f;
	vp->a= 0.2f;
	vp->size= 25.0f;
	vp->gamma= vp->mul= 1.0f;
	
	vp->flag= VP_AREA+VP_SOFT+VP_SPRAY;
	
	if(wpaint) {
		vp->weight= 1.0f;
		vp->a= 1.0f;
		vp->flag= VP_AREA+VP_SOFT;
	}
	return vp;
}

static int *get_indexarray(void)
{
	return MEM_mallocN(sizeof(int)*MAXINDEX + 2, "vertexpaint");
}


/* in contradiction to cpack drawing colors, the MCOL colors (vpaint colors) are per byte! 
   so not endian sensitive. Mcol = ABGR!!! so be cautious with cpack calls */

unsigned int rgba_to_mcol(float r, float g, float b, float a)
{
	int ir, ig, ib, ia;
	unsigned int col;
	char *cp;
	
	ir= floor(255.0*r);
	if(ir<0) ir= 0; else if(ir>255) ir= 255;
	ig= floor(255.0*g);
	if(ig<0) ig= 0; else if(ig>255) ig= 255;
	ib= floor(255.0*b);
	if(ib<0) ib= 0; else if(ib>255) ib= 255;
	ia= floor(255.0*a);
	if(ia<0) ia= 0; else if(ia>255) ia= 255;
	
	cp= (char *)&col;
	cp[0]= ia;
	cp[1]= ib;
	cp[2]= ig;
	cp[3]= ir;
	
	return col;
	
}

static unsigned int vpaint_get_current_col(VPaint *vp)
{
	return rgba_to_mcol(vp->r, vp->g, vp->b, 1.0f);
}

void do_shared_vertexcol(Mesh *me)
{
	/* if no mcol: do not do */
	/* if tface: only the involved faces, otherwise all */
	MFace *mface;
	MTFace *tface;
	int a;
	short *scolmain, *scol;
	char *mcol;
	
	if(me->mcol==0 || me->totvert==0 || me->totface==0) return;
	
	scolmain= MEM_callocN(4*sizeof(short)*me->totvert, "colmain");
	
	tface= me->mtface;
	mface= me->mface;
	mcol= (char *)me->mcol;
	for(a=me->totface; a>0; a--, mface++, mcol+=16) {
		if((tface && tface->mode & TF_SHAREDCOL) || (G.f & G_FACESELECT)==0) {
			scol= scolmain+4*mface->v1;
			scol[0]++; scol[1]+= mcol[1]; scol[2]+= mcol[2]; scol[3]+= mcol[3];
			scol= scolmain+4*mface->v2;
			scol[0]++; scol[1]+= mcol[5]; scol[2]+= mcol[6]; scol[3]+= mcol[7];
			scol= scolmain+4*mface->v3;
			scol[0]++; scol[1]+= mcol[9]; scol[2]+= mcol[10]; scol[3]+= mcol[11];
			if(mface->v4) {
				scol= scolmain+4*mface->v4;
				scol[0]++; scol[1]+= mcol[13]; scol[2]+= mcol[14]; scol[3]+= mcol[15];
			}
		}
		if(tface) tface++;
	}
	
	a= me->totvert;
	scol= scolmain;
	while(a--) {
		if(scol[0]>1) {
			scol[1]/= scol[0];
			scol[2]/= scol[0];
			scol[3]/= scol[0];
		}
		scol+= 4;
	}
	
	tface= me->mtface;
	mface= me->mface;
	mcol= (char *)me->mcol;
	for(a=me->totface; a>0; a--, mface++, mcol+=16) {
		if((tface && tface->mode & TF_SHAREDCOL) || (G.f & G_FACESELECT)==0) {
			scol= scolmain+4*mface->v1;
			mcol[1]= scol[1]; mcol[2]= scol[2]; mcol[3]= scol[3];
			scol= scolmain+4*mface->v2;
			mcol[5]= scol[1]; mcol[6]= scol[2]; mcol[7]= scol[3];
			scol= scolmain+4*mface->v3;
			mcol[9]= scol[1]; mcol[10]= scol[2]; mcol[11]= scol[3];
			if(mface->v4) {
				scol= scolmain+4*mface->v4;
				mcol[13]= scol[1]; mcol[14]= scol[2]; mcol[15]= scol[3];
			}
		}
		if(tface) tface++;
	}

	MEM_freeN(scolmain);
}

void make_vertexcol(Scene *scene, int shade)	/* single ob */
{
	Object *ob;
	Mesh *me;

	if(scene->obedit) {
		error("Unable to perform function in Edit Mode");
		return;
	}
	
	ob= OBACT;
	if(!ob || ob->id.lib) return;
	me= get_mesh(ob);
	if(me==0) return;

	/* copies from shadedisplist to mcol */
	if(!me->mcol) {
		CustomData_add_layer(&me->fdata, CD_MCOL, CD_CALLOC, NULL, me->totface);
		mesh_update_customdata_pointers(me);
	}

	if(shade)
		shadeMeshMCol(scene, ob, me);
	else
		memset(me->mcol, 255, 4*sizeof(MCol)*me->totface);
	
// XXX	if (me->mr) multires_load_cols(me);
	
	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	
}

static void copy_vpaint_prev(VPaint *vp, unsigned int *mcol, int tot)
{
	if(vp->vpaint_prev) {
		MEM_freeN(vp->vpaint_prev);
		vp->vpaint_prev= NULL;
	}
	vp->tot= tot;	
	
	if(mcol==NULL || tot==0) return;
	
	vp->vpaint_prev= MEM_mallocN(4*sizeof(int)*tot, "vpaint_prev");
	memcpy(vp->vpaint_prev, mcol, 4*sizeof(int)*tot);
	
}

static void copy_wpaint_prev (VPaint *wp, MDeformVert *dverts, int dcount)
{
	if (wp->wpaint_prev) {
		free_dverts(wp->wpaint_prev, wp->tot);
		wp->wpaint_prev= NULL;
	}
	
	if(dverts && dcount) {
		
		wp->wpaint_prev = MEM_mallocN (sizeof(MDeformVert)*dcount, "wpaint prev");
		wp->tot = dcount;
		copy_dverts (wp->wpaint_prev, dverts, dcount);
	}
}


void clear_vpaint(Scene *scene)
{
	Mesh *me;
	Object *ob;
	unsigned int *to, paintcol;
	int a;
	
	if((G.f & G_VERTEXPAINT)==0) return;

	ob= OBACT;
	me= get_mesh(ob);
	if(!ob || ob->id.lib) return;

	if(me==0 || me->mcol==0 || me->totface==0) return;

	paintcol= vpaint_get_current_col(scene->toolsettings->vpaint);

	to= (unsigned int *)me->mcol;
	a= 4*me->totface;
	while(a--) {
		*to= paintcol;
		to++; 
	}
	BIF_undo_push("Clear vertex colors");
	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	
}

void clear_vpaint_selectedfaces(Scene *scene)
{
	Mesh *me;
	MFace *mf;
	Object *ob;
	unsigned int paintcol, *mcol;
	int i;

	ob= OBACT;
	me= get_mesh(ob);
	if(me==0 || me->totface==0) return;

	if(!me->mcol)
		make_vertexcol(scene, 0);

	paintcol= vpaint_get_current_col(scene->toolsettings->vpaint);

	mf = me->mface;
	mcol = (unsigned int*)me->mcol;
	for (i = 0; i < me->totface; i++, mf++, mcol+=4) {
		if (mf->flag & ME_FACE_SEL) {
			mcol[0] = paintcol;
			mcol[1] = paintcol;
			mcol[2] = paintcol;
			mcol[3] = paintcol;
		}
	}
	
	BIF_undo_push("Clear vertex colors");
	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
}


/* fills in the selected faces with the current weight and vertex group */
void clear_wpaint_selectedfaces(Scene *scene)
{
	VPaint *wp= scene->toolsettings->wpaint;
	float paintweight= wp->weight;
	Mesh *me;
	MFace *mface;
	Object *ob;
	MDeformWeight *dw, *uw;
	int *indexar;
	int index, vgroup;
	unsigned int faceverts[5]={0,0,0,0,0};
	unsigned char i;
	int vgroup_mirror= -1;
	
	ob= OBACT;
	me= ob->data;
	if(me==0 || me->totface==0 || me->dvert==0 || !me->mface) return;
	
	indexar= get_indexarray();
	for(index=0, mface=me->mface; index<me->totface; index++, mface++) {
		if((mface->flag & ME_FACE_SEL)==0)
			indexar[index]= 0;
		else
			indexar[index]= index+1;
	}
	
	vgroup= ob->actdef-1;
	
	/* directly copied from weight_paint, should probaby split into a seperate function */
	/* if mirror painting, find the other group */		
	if(wp->flag & VP_MIRROR_X) {
		bDeformGroup *defgroup= BLI_findlink(&ob->defbase, ob->actdef-1);
		if(defgroup) {
			bDeformGroup *curdef;
			int actdef= 0;
			char name[32];

			BLI_strncpy(name, defgroup->name, 32);
			bone_flip_name(name, 0);		/* 0 = don't strip off number extensions */
			
			for (curdef = ob->defbase.first; curdef; curdef=curdef->next, actdef++)
				if (!strcmp(curdef->name, name))
					break;
			if(curdef==NULL) {
				int olddef= ob->actdef;	/* tsk, add_defgroup sets the active defgroup */
				curdef= add_defgroup_name (ob, name);
				ob->actdef= olddef;
			}
			
			if(curdef && curdef!=defgroup)
				vgroup_mirror= actdef;
		}
	}
	/* end copy from weight_paint*/
	
	copy_wpaint_prev(wp, me->dvert, me->totvert);
	
	for(index=0; index<me->totface; index++) {
		if(indexar[index] && indexar[index]<=me->totface) {
			mface= me->mface + (indexar[index]-1);
			/* just so we can loop through the verts */
			faceverts[0]= mface->v1;
			faceverts[1]= mface->v2;
			faceverts[2]= mface->v3;
			faceverts[3]= mface->v4;
			for (i=0; i<3 || faceverts[i]; i++) {
				if(!((me->dvert+faceverts[i])->flag)) {
					dw= verify_defweight(me->dvert+faceverts[i], vgroup);
					if(dw) {
						uw= verify_defweight(wp->wpaint_prev+faceverts[i], vgroup);
						uw->weight= dw->weight; /* set the undo weight */
						dw->weight= paintweight;
						
						if(wp->flag & VP_MIRROR_X) {	/* x mirror painting */
							int j= mesh_get_x_mirror_vert(ob, faceverts[i]);
							if(j>=0) {
								/* copy, not paint again */
								if(vgroup_mirror != -1) {
									dw= verify_defweight(me->dvert+j, vgroup_mirror);
									uw= verify_defweight(wp->wpaint_prev+j, vgroup_mirror);
								} else {
									dw= verify_defweight(me->dvert+j, vgroup);
									uw= verify_defweight(wp->wpaint_prev+j, vgroup);
								}
								uw->weight= dw->weight; /* set the undo weight */
								dw->weight= paintweight;
							}
						}
					}
					(me->dvert+faceverts[i])->flag= 1;
				}
			}
		}
	}
	
	index=0;
	while (index<me->totvert) {
		(me->dvert+index)->flag= 0;
		index++;
	}
	
	MEM_freeN(indexar);
	copy_wpaint_prev(wp, NULL, 0);

	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	BIF_undo_push("Set vertex weight");
}


void vpaint_dogamma(Scene *scene)
{
	VPaint *vp= scene->toolsettings->vpaint;
	Mesh *me;
	Object *ob;
	float igam, fac;
	int a, temp;
	char *cp, gamtab[256];

	if((G.f & G_VERTEXPAINT)==0) return;

	ob= OBACT;
	me= get_mesh(ob);
	if(me==0 || me->mcol==0 || me->totface==0) return;

	igam= 1.0/vp->gamma;
	for(a=0; a<256; a++) {
		
		fac= ((float)a)/255.0;
		fac= vp->mul*pow( fac, igam);
		
		temp= 255.9*fac;
		
		if(temp<=0) gamtab[a]= 0;
		else if(temp>=255) gamtab[a]= 255;
		else gamtab[a]= temp;
	}

	a= 4*me->totface;
	cp= (char *)me->mcol;
	while(a--) {
		
		cp[1]= gamtab[ cp[1] ];
		cp[2]= gamtab[ cp[2] ];
		cp[3]= gamtab[ cp[3] ];
		
		cp+= 4;
	}
}

/* used for both 3d view and image window */
void sample_vpaint(Scene *scene, ARegion *ar)	/* frontbuf */
{
	VPaint *vp= scene->toolsettings->vpaint;
	unsigned int col;
	int x, y;
	short mval[2];
	char *cp;
	
//	getmouseco_areawin(mval);
	x= mval[0]; y= mval[1];
	
	if(x<0 || y<0) return;
	if(x>=ar->winx || y>=ar->winy) return;
	
	x+= ar->winrct.xmin;
	y+= ar->winrct.ymin;
	
	glReadBuffer(GL_FRONT);
	glReadPixels(x, y, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, &col);
	glReadBuffer(GL_BACK);

	cp = (char *)&col;
	
	if(G.f & (G_VERTEXPAINT|G_WEIGHTPAINT)) {
		vp->r= cp[0]/255.0f;
		vp->g= cp[1]/255.0f;
		vp->b= cp[2]/255.0f;
	}
	else {
		Brush *brush= scene->toolsettings->imapaint.brush;

		if(brush) {
			brush->rgb[0]= cp[0]/255.0f;
			brush->rgb[1]= cp[1]/255.0f;
			brush->rgb[2]= cp[2]/255.0f;

		}
	}

}

static unsigned int mcol_blend(unsigned int col1, unsigned int col2, int fac)
{
	char *cp1, *cp2, *cp;
	int mfac;
	unsigned int col=0;
	
	if(fac==0) return col1;
	if(fac>=255) return col2;

	mfac= 255-fac;
	
	cp1= (char *)&col1;
	cp2= (char *)&col2;
	cp=  (char *)&col;
	
	cp[0]= 255;
	cp[1]= (mfac*cp1[1]+fac*cp2[1])/255;
	cp[2]= (mfac*cp1[2]+fac*cp2[2])/255;
	cp[3]= (mfac*cp1[3]+fac*cp2[3])/255;
	
	return col;
}

static unsigned int mcol_add(unsigned int col1, unsigned int col2, int fac)
{
	char *cp1, *cp2, *cp;
	int temp;
	unsigned int col=0;
	
	if(fac==0) return col1;
	
	cp1= (char *)&col1;
	cp2= (char *)&col2;
	cp=  (char *)&col;
	
	cp[0]= 255;
	temp= cp1[1] + ((fac*cp2[1])/255);
	if(temp>254) cp[1]= 255; else cp[1]= temp;
	temp= cp1[2] + ((fac*cp2[2])/255);
	if(temp>254) cp[2]= 255; else cp[2]= temp;
	temp= cp1[3] + ((fac*cp2[3])/255);
	if(temp>254) cp[3]= 255; else cp[3]= temp;
	
	return col;
}

static unsigned int mcol_sub(unsigned int col1, unsigned int col2, int fac)
{
	char *cp1, *cp2, *cp;
	int temp;
	unsigned int col=0;
	
	if(fac==0) return col1;
	
	cp1= (char *)&col1;
	cp2= (char *)&col2;
	cp=  (char *)&col;
	
	cp[0]= 255;
	temp= cp1[1] - ((fac*cp2[1])/255);
	if(temp<0) cp[1]= 0; else cp[1]= temp;
	temp= cp1[2] - ((fac*cp2[2])/255);
	if(temp<0) cp[2]= 0; else cp[2]= temp;
	temp= cp1[3] - ((fac*cp2[3])/255);
	if(temp<0) cp[3]= 0; else cp[3]= temp;
	
	return col;
}

static unsigned int mcol_mul(unsigned int col1, unsigned int col2, int fac)
{
	char *cp1, *cp2, *cp;
	int mfac;
	unsigned int col=0;
	
	if(fac==0) return col1;

	mfac= 255-fac;
	
	cp1= (char *)&col1;
	cp2= (char *)&col2;
	cp=  (char *)&col;
	
	/* first mul, then blend the fac */
	cp[0]= 255;
	cp[1]= (mfac*cp1[1] + fac*((cp2[1]*cp1[1])/255)  )/255;
	cp[2]= (mfac*cp1[2] + fac*((cp2[2]*cp1[2])/255)  )/255;
	cp[3]= (mfac*cp1[3] + fac*((cp2[3]*cp1[3])/255)  )/255;

	
	return col;
}

static unsigned int mcol_lighten(unsigned int col1, unsigned int col2, int fac)
{
	char *cp1, *cp2, *cp;
	int mfac;
	unsigned int col=0;
	
	if(fac==0) return col1;
	if(fac>=255) return col2;

	mfac= 255-fac;
	
	cp1= (char *)&col1;
	cp2= (char *)&col2;
	cp=  (char *)&col;
	
	/* See if are lighter, if so mix, else dont do anything.
	if the paint col is darker then the original, then ignore */
	if (cp1[1]+cp1[2]+cp1[3] > cp2[1]+cp2[2]+cp2[3])
		return col1;
	
	cp[0]= 255;
	cp[1]= (mfac*cp1[1]+fac*cp2[1])/255;
	cp[2]= (mfac*cp1[2]+fac*cp2[2])/255;
	cp[3]= (mfac*cp1[3]+fac*cp2[3])/255;
	
	return col;
}

static unsigned int mcol_darken(unsigned int col1, unsigned int col2, int fac)
{
	char *cp1, *cp2, *cp;
	int mfac;
	unsigned int col=0;
	
	if(fac==0) return col1;
	if(fac>=255) return col2;

	mfac= 255-fac;
	
	cp1= (char *)&col1;
	cp2= (char *)&col2;
	cp=  (char *)&col;
	
	/* See if were darker, if so mix, else dont do anything.
	if the paint col is brighter then the original, then ignore */
	if (cp1[1]+cp1[2]+cp1[3] < cp2[1]+cp2[2]+cp2[3])
		return col1;
	
	cp[0]= 255;
	cp[1]= (mfac*cp1[1]+fac*cp2[1])/255;
	cp[2]= (mfac*cp1[2]+fac*cp2[2])/255;
	cp[3]= (mfac*cp1[3]+fac*cp2[3])/255;
	return col;
}

static void vpaint_blend(VPaint *vp, unsigned int *col, unsigned int *colorig, unsigned int paintcol, int alpha)
{

	if(vp->mode==VP_MIX || vp->mode==VP_BLUR) *col= mcol_blend( *col, paintcol, alpha);
	else if(vp->mode==VP_ADD) *col= mcol_add( *col, paintcol, alpha);
	else if(vp->mode==VP_SUB) *col= mcol_sub( *col, paintcol, alpha);
	else if(vp->mode==VP_MUL) *col= mcol_mul( *col, paintcol, alpha);
	else if(vp->mode==VP_LIGHTEN) *col= mcol_lighten( *col, paintcol, alpha);
	else if(vp->mode==VP_DARKEN) *col= mcol_darken( *col, paintcol, alpha);
	
	/* if no spray, clip color adding with colorig & orig alpha */
	if((vp->flag & VP_SPRAY)==0) {
		unsigned int testcol=0, a;
		char *cp, *ct, *co;
		
		alpha= (int)(255.0*vp->a);
		
		if(vp->mode==VP_MIX || vp->mode==VP_BLUR) testcol= mcol_blend( *colorig, paintcol, alpha);
		else if(vp->mode==VP_ADD) testcol= mcol_add( *colorig, paintcol, alpha);
		else if(vp->mode==VP_SUB) testcol= mcol_sub( *colorig, paintcol, alpha);
		else if(vp->mode==VP_MUL) testcol= mcol_mul( *colorig, paintcol, alpha);
		else if(vp->mode==VP_LIGHTEN)  testcol= mcol_lighten( *colorig, paintcol, alpha);
		else if(vp->mode==VP_DARKEN)   testcol= mcol_darken( *colorig, paintcol, alpha);
		
		cp= (char *)col;
		ct= (char *)&testcol;
		co= (char *)colorig;
		
		for(a=0; a<4; a++) {
			if( ct[a]<co[a] ) {
				if( cp[a]<ct[a] ) cp[a]= ct[a];
				else if( cp[a]>co[a] ) cp[a]= co[a];
			}
			else {
				if( cp[a]<co[a] ) cp[a]= co[a];
				else if( cp[a]>ct[a] ) cp[a]= ct[a];
			}
		}
	}
}


static int sample_backbuf_area(ViewContext *vc, int *indexar, int totface, int x, int y, float size)
{
	struct ImBuf *ibuf;
	int a, tot=0, index;
	
	if(totface+4>=MAXINDEX) return 0;
	
	if(size>64.0) size= 64.0;
	
	ibuf= view3d_read_backbuf(vc, x-size, y-size, x+size, y+size);
	if(ibuf) {
		unsigned int *rt= ibuf->rect;

		memset(indexar, 0, sizeof(int)*totface+4);	/* plus 2! first element is total, +2 was giving valgrind errors, +4 seems ok */
		
		size= ibuf->x*ibuf->y;
		while(size--) {
				
			if(*rt) {
				index= WM_framebuffer_to_index(*rt);
				if(index>0 && index<=totface)
					indexar[index] = 1;
			}
		
			rt++;
		}
		
		for(a=1; a<=totface; a++) {
			if(indexar[a]) indexar[tot++]= a;
		}

		IMB_freeImBuf(ibuf);
	}
	
	return tot;
}

static int calc_vp_alpha_dl(VPaint *vp, ViewContext *vc, float vpimat[][3], float *vert_nor, short *mval)
{
	float fac, dx, dy;
	int alpha;
	short vertco[2];
	
	if(vp->flag & VP_SOFT) {
	 	project_short_noclip(vc->ar, vert_nor, vertco);
		dx= mval[0]-vertco[0];
		dy= mval[1]-vertco[1];
		
		fac= sqrt(dx*dx + dy*dy);
		if(fac > vp->size) return 0;
		if(vp->flag & VP_HARD)
			alpha= 255;
		else
			alpha= 255.0*vp->a*(1.0-fac/vp->size);
	}
	else {
		alpha= 255.0*vp->a;
	}

	if(vp->flag & VP_NORMALS) {
		float *no= vert_nor+3;
		
			/* transpose ! */
		fac= vpimat[2][0]*no[0]+vpimat[2][1]*no[1]+vpimat[2][2]*no[2];
		if(fac>0.0) {
			dx= vpimat[0][0]*no[0]+vpimat[0][1]*no[1]+vpimat[0][2]*no[2];
			dy= vpimat[1][0]*no[0]+vpimat[1][1]*no[1]+vpimat[1][2]*no[2];
			
			alpha*= fac/sqrt(dx*dx + dy*dy + fac*fac);
		}
		else return 0;
	}
	
	return alpha;
}

static void wpaint_blend(VPaint *wp, MDeformWeight *dw, MDeformWeight *uw, float alpha, float paintval)
{
	
	if(dw==NULL || uw==NULL) return;
	
	if(wp->mode==VP_MIX || wp->mode==VP_BLUR)
		dw->weight = paintval*alpha + dw->weight*(1.0-alpha);
	else if(wp->mode==VP_ADD)
		dw->weight += paintval*alpha;
	else if(wp->mode==VP_SUB) 
		dw->weight -= paintval*alpha;
	else if(wp->mode==VP_MUL) 
		/* first mul, then blend the fac */
		dw->weight = ((1.0-alpha) + alpha*paintval)*dw->weight;
	else if(wp->mode==VP_LIGHTEN) {
		if (dw->weight < paintval)
			dw->weight = paintval*alpha + dw->weight*(1.0-alpha);
	} else if(wp->mode==VP_DARKEN) {
		if (dw->weight > paintval)
			dw->weight = paintval*alpha + dw->weight*(1.0-alpha);
	}
	CLAMP(dw->weight, 0.0f, 1.0f);
	
	/* if no spray, clip result with orig weight & orig alpha */
	if((wp->flag & VP_SPRAY)==0) {
		float testw=0.0f;
		
		alpha= wp->a;
		if(wp->mode==VP_MIX || wp->mode==VP_BLUR)
			testw = paintval*alpha + uw->weight*(1.0-alpha);
		else if(wp->mode==VP_ADD)
			testw = uw->weight + paintval*alpha;
		else if(wp->mode==VP_SUB) 
			testw = uw->weight - paintval*alpha;
		else if(wp->mode==VP_MUL) 
			/* first mul, then blend the fac */
			testw = ((1.0-alpha) + alpha*paintval)*uw->weight;		
		else if(wp->mode==VP_LIGHTEN) {
			if (uw->weight < paintval)
				testw = paintval*alpha + uw->weight*(1.0-alpha);
			else
				testw = uw->weight;
		} else if(wp->mode==VP_DARKEN) {
			if (uw->weight > paintval)
				testw = paintval*alpha + uw->weight*(1.0-alpha);
			else
				testw = uw->weight;
		}
		CLAMP(testw, 0.0f, 1.0f);
		
		if( testw<uw->weight ) {
			if(dw->weight < testw) dw->weight= testw;
			else if(dw->weight > uw->weight) dw->weight= uw->weight;
		}
		else {
			if(dw->weight > testw) dw->weight= testw;
			else if(dw->weight < uw->weight) dw->weight= uw->weight;
		}
	}
	
}

/* ----------------------------------------------------- */

/* used for 3d view, on active object, assumes me->dvert exists */
/* if mode==1: */
/*     samples cursor location, and gives menu with vertex groups to activate */
/* else */
/*     sets wp->weight to the closest weight value to vertex */
/*     note: we cant sample frontbuf, weight colors are interpolated too unpredictable */
void sample_wpaint(Scene *scene, ARegion *ar, View3D *v3d, int mode)
{
	ViewContext vc;
	VPaint *wp= scene->toolsettings->wpaint;
	Object *ob= OBACT;
	Mesh *me= get_mesh(ob);
	int index;
	short mval[2], sco[2];

	if (!me) return;
	
//	getmouseco_areawin(mval);
	index= view3d_sample_backbuf(&vc, mval[0], mval[1]);
	
	if(index && index<=me->totface) {
		MFace *mface;
		
		mface= ((MFace *)me->mface) + index-1;
		
		if(mode==1) {	/* sampe which groups are in here */
			MDeformVert *dv;
			int a, totgroup;
			
			totgroup= BLI_countlist(&ob->defbase);
			if(totgroup) {
				int totmenu=0;
				int *groups=MEM_callocN(totgroup*sizeof(int), "groups");
				
				dv= me->dvert+mface->v1;
				for(a=0; a<dv->totweight; a++) {
					if (dv->dw[a].def_nr<totgroup)
						groups[dv->dw[a].def_nr]= 1;
				}
				dv= me->dvert+mface->v2;
				for(a=0; a<dv->totweight; a++) {
					if (dv->dw[a].def_nr<totgroup)
						groups[dv->dw[a].def_nr]= 1;
				}
				dv= me->dvert+mface->v3;
				for(a=0; a<dv->totweight; a++) {
					if (dv->dw[a].def_nr<totgroup)
						groups[dv->dw[a].def_nr]= 1;
				}
				if(mface->v4) {
					dv= me->dvert+mface->v4;
					for(a=0; a<dv->totweight; a++) {
						if (dv->dw[a].def_nr<totgroup)
							groups[dv->dw[a].def_nr]= 1;
					}
				}
				for(a=0; a<totgroup; a++)
					if(groups[a]) totmenu++;
				
				if(totmenu==0) {
					//notice("No Vertex Group Selected");
				}
				else {
					bDeformGroup *dg;
					short val;
					char item[40], *str= MEM_mallocN(40*totmenu+40, "menu");
					
					strcpy(str, "Vertex Groups %t");
					for(a=0, dg=ob->defbase.first; dg && a<totgroup; a++, dg= dg->next) {
						if(groups[a]) {
							sprintf(item, "|%s %%x%d", dg->name, a);
							strcat(str, item);
						}
					}
					
					val= 0; // XXX pupmenu(str);
					if(val>=0) {
						ob->actdef= val+1;
						DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
					}
					MEM_freeN(str);
				}
				MEM_freeN(groups);
			}
//			else notice("No Vertex Groups in Object");
		}
		else {
			DerivedMesh *dm;
			MDeformWeight *dw;
			float w1, w2, w3, w4, co[3], fac;
			
			dm = mesh_get_derived_final(scene, ob, CD_MASK_BAREMESH);
			if(dm->getVertCo==NULL) {
				//notice("Not supported yet");
			}
			else {
				/* calc 3 or 4 corner weights */
				dm->getVertCo(dm, mface->v1, co);
				project_short_noclip(ar, co, sco);
				w1= ((mval[0]-sco[0])*(mval[0]-sco[0]) + (mval[1]-sco[1])*(mval[1]-sco[1]));
				
				dm->getVertCo(dm, mface->v2, co);
				project_short_noclip(ar, co, sco);
				w2= ((mval[0]-sco[0])*(mval[0]-sco[0]) + (mval[1]-sco[1])*(mval[1]-sco[1]));
				
				dm->getVertCo(dm, mface->v3, co);
				project_short_noclip(ar, co, sco);
				w3= ((mval[0]-sco[0])*(mval[0]-sco[0]) + (mval[1]-sco[1])*(mval[1]-sco[1]));
				
				if(mface->v4) {
					dm->getVertCo(dm, mface->v4, co);
					project_short_noclip(ar, co, sco);
					w4= ((mval[0]-sco[0])*(mval[0]-sco[0]) + (mval[1]-sco[1])*(mval[1]-sco[1]));
				}
				else w4= 1.0e10;
				
				fac= MIN4(w1, w2, w3, w4);
				if(w1==fac) {
					dw= get_defweight(me->dvert+mface->v1, ob->actdef-1);
					if(dw) wp->weight= dw->weight; else wp->weight= 0.0f;
				}
				else if(w2==fac) {
					dw= get_defweight(me->dvert+mface->v2, ob->actdef-1);
					if(dw) wp->weight= dw->weight; else wp->weight= 0.0f;
				}
				else if(w3==fac) {
					dw= get_defweight(me->dvert+mface->v3, ob->actdef-1);
					if(dw) wp->weight= dw->weight; else wp->weight= 0.0f;
				}
				else if(w4==fac) {
					if(mface->v4) {
						dw= get_defweight(me->dvert+mface->v4, ob->actdef-1);
						if(dw) wp->weight= dw->weight; else wp->weight= 0.0f;
					}
				}
			}
			dm->release(dm);
		}		
		
	}
	
}

static void do_weight_paint_vertex(VPaint *wp, Object *ob, int index, int alpha, float paintweight, int vgroup_mirror)
{
	Mesh *me= ob->data;
	MDeformWeight *dw, *uw;
	int vgroup= ob->actdef-1;
	
	if(wp->flag & VP_ONLYVGROUP) {
		dw= get_defweight(me->dvert+index, vgroup);
		uw= get_defweight(wp->wpaint_prev+index, vgroup);
	}
	else {
		dw= verify_defweight(me->dvert+index, vgroup);
		uw= verify_defweight(wp->wpaint_prev+index, vgroup);
	}
	if(dw==NULL || uw==NULL)
		return;
	
	wpaint_blend(wp, dw, uw, (float)alpha/255.0, paintweight);
	
	if(wp->flag & VP_MIRROR_X) {	/* x mirror painting */
		int j= mesh_get_x_mirror_vert(ob, index);
		if(j>=0) {
			/* copy, not paint again */
			if(vgroup_mirror != -1)
				uw= verify_defweight(me->dvert+j, vgroup_mirror);
			else
				uw= verify_defweight(me->dvert+j, vgroup);
				
			uw->weight= dw->weight;
		}
	}
}


/* *************** set wpaint operator ****************** */
/* retrieve whether cursor should be set or operator should be done */
static int wp_poll(bContext *C)
{
	if(G.f & G_WEIGHTPAINT) {
		ScrArea *sa= CTX_wm_area(C);
		if(sa->spacetype==SPACE_VIEW3D) {
			ARegion *ar= CTX_wm_region(C);
			if(ar->regiontype==RGN_TYPE_WINDOW)
				return 1;
		}
	}
	return 0;
}

static void wp_drawcursor(bContext *C, int x, int y)
{
	ToolSettings *ts= CTX_data_tool_settings(C);
	
	glTranslatef((float)x, (float)y, 0.0f);
	
	glColor4ub(200, 200, 255, 128);
	glEnable( GL_LINE_SMOOTH );
	glEnable(GL_BLEND);
	glutil_draw_lined_arc(0.0, M_PI*2.0, ts->wpaint->size, 40);
	glDisable(GL_BLEND);
	glDisable( GL_LINE_SMOOTH );
	
	glTranslatef((float)-x, (float)-y, 0.0f);
}

static int set_wpaint(bContext *C, wmOperator *op)		/* toggle */
{		
	Object *ob= CTX_data_active_object(C);
	Scene *scene= CTX_data_scene(C);
	VPaint *wp= scene->toolsettings->wpaint;
	Mesh *me;
	
	me= get_mesh(ob);
	if(ob->id.lib || me==NULL) return OPERATOR_CANCELLED;
	
	if(me && me->totface>=MAXINDEX) {
		error("Maximum number of faces: %d", MAXINDEX-1);
		G.f &= ~G_WEIGHTPAINT;
		return OPERATOR_CANCELLED;
	}
	
	if(G.f & G_WEIGHTPAINT) G.f &= ~G_WEIGHTPAINT;
	else G.f |= G_WEIGHTPAINT;
	
	
	/* Weightpaint works by overriding colors in mesh,
		* so need to make sure we recalc on enter and
		* exit (exit needs doing regardless because we
				* should redeform).
		*/
	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	
	if(G.f & G_WEIGHTPAINT) {
		Object *par;
		
		if(wp==NULL)
			wp= scene->toolsettings->wpaint= new_vpaint(1);
		
		wp->paintcursor = WM_paint_cursor_activate(CTX_wm_manager(C), wp_poll, wp_drawcursor);
		
		mesh_octree_table(ob, NULL, NULL, 's');
		
		/* verify if active weight group is also active bone */
		par= modifiers_isDeformedByArmature(ob);
		if(par && (par->flag & OB_POSEMODE)) {
			bPoseChannel *pchan;
			for(pchan= par->pose->chanbase.first; pchan; pchan= pchan->next)
				if(pchan->bone->flag & BONE_ACTIVE)
					break;
				if(pchan)
					vertexgroup_select_by_name(ob, pchan->name);
		}
	}
	else {
		if(wp)
			WM_paint_cursor_end(CTX_wm_manager(C), wp->paintcursor);
		
		mesh_octree_table(ob, NULL, NULL, 'e');
	}
	
	WM_event_add_notifier(C, NC_SCENE|ND_MODE, ob);
	
	return OPERATOR_FINISHED;
}

void VIEW3D_OT_wpaint_toggle(wmOperatorType *ot)
{
	
	/* identifiers */
	ot->name= "Weight Paint Mode";
	ot->idname= "VIEW3D_OT_wpaint_toggle";
	
	/* api callbacks */
	ot->exec= set_wpaint;
	ot->poll= ED_operator_object_active;
	
}

/* ************ weight paint operator ********** */

struct WPaintData {
	ViewContext vc;
	int *indexar;
	int vgroup_mirror;
	float *vertexcosnos;
	float wpimat[3][3];
};

static void wpaint_exit(bContext *C, wmOperator *op)
{
	ToolSettings *ts= CTX_data_tool_settings(C);
	Object *ob= CTX_data_active_object(C);
	struct WPaintData *wpd= op->customdata;
	
	if(wpd->vertexcosnos)
		MEM_freeN(wpd->vertexcosnos);
	MEM_freeN(wpd->indexar);
	
	/* frees prev buffer */
	copy_wpaint_prev(ts->wpaint, NULL, 0);
	
	/* and particles too */
	if(ob->particlesystem.first) {
		ParticleSystem *psys;
		int i;
		
		for(psys= ob->particlesystem.first; psys; psys= psys->next) {
			for(i=0; i<PSYS_TOT_VG; i++) {
				if(psys->vgroup[i]==ob->actdef) {
					psys->recalc |= PSYS_RECALC_HAIR;
					break;
				}
			}
		}
	}
	
	DAG_object_flush_update(CTX_data_scene(C), ob, OB_RECALC_DATA);
	
	ED_undo_push(C, "Weight Paint");
	
	MEM_freeN(wpd);
	op->customdata= NULL;
}


static int wpaint_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	ToolSettings *ts= CTX_data_tool_settings(C);
	VPaint *wp= ts->wpaint;
	
	switch(event->type) {
		case LEFTMOUSE:
			if(event->val==0) { /* release */
				wpaint_exit(C, op);
				return OPERATOR_FINISHED;
			}
			/* pass on, first press gets painted too */
			
		case MOUSEMOVE: 
		{
			struct WPaintData *wpd= op->customdata;
			ViewContext *vc= &wpd->vc;
			Object *ob= vc->obact;
			Mesh *me= ob->data;
			float mat[4][4];
			float paintweight= wp->weight;
			int *indexar= wpd->indexar;
			int totindex, index, alpha, totw;
			short mval[2];
			
			view3d_operator_needs_opengl(C);
			
			/* load projection matrix */
			wmMultMatrix(ob->obmat);
			wmGetSingleMatrix(mat);
			wmLoadMatrix(wpd->vc.rv3d->viewmat);
			
			MTC_Mat4SwapMat4(wpd->vc.rv3d->persmat, mat);
			
			mval[0]= event->x - vc->ar->winrct.xmin;
			mval[1]= event->y - vc->ar->winrct.ymin;
			
			/* which faces are involved */
			if(wp->flag & VP_AREA) {
				totindex= sample_backbuf_area(vc, indexar, me->totface, mval[0], mval[1], wp->size);
			}
			else {
				indexar[0]= view3d_sample_backbuf(vc, mval[0], mval[1]);
				if(indexar[0]) totindex= 1;
				else totindex= 0;
			}
			
			if(wp->flag & VP_COLINDEX) {
				for(index=0; index<totindex; index++) {
					if(indexar[index] && indexar[index]<=me->totface) {
						MFace *mface= ((MFace *)me->mface) + (indexar[index]-1);
						
						if(mface->mat_nr!=ob->actcol-1) {
							indexar[index]= 0;
						}
					}					
				}
			}
			
			if((G.f & G_FACESELECT) && me->mface) {
				for(index=0; index<totindex; index++) {
					if(indexar[index] && indexar[index]<=me->totface) {
						MFace *mface= ((MFace *)me->mface) + (indexar[index]-1);
						
						if((mface->flag & ME_FACE_SEL)==0) {
							indexar[index]= 0;
						}
					}					
				}
			}
			
			/* make sure each vertex gets treated only once */
			/* and calculate filter weight */
			totw= 0;
			if(wp->mode==VP_BLUR) 
				paintweight= 0.0f;
			else
				paintweight= wp->weight;
			
			for(index=0; index<totindex; index++) {
				if(indexar[index] && indexar[index]<=me->totface) {
					MFace *mface= me->mface + (indexar[index]-1);
					
					(me->dvert+mface->v1)->flag= 1;
					(me->dvert+mface->v2)->flag= 1;
					(me->dvert+mface->v3)->flag= 1;
					if(mface->v4) (me->dvert+mface->v4)->flag= 1;
					
					if(wp->mode==VP_BLUR) {
						MDeformWeight *dw, *(*dw_func)(MDeformVert *, int) = verify_defweight;
						
						if(wp->flag & VP_ONLYVGROUP)
							dw_func= get_defweight;
						
						dw= dw_func(me->dvert+mface->v1, ob->actdef-1);
						if(dw) {paintweight+= dw->weight; totw++;}
						dw= dw_func(me->dvert+mface->v2, ob->actdef-1);
						if(dw) {paintweight+= dw->weight; totw++;}
						dw= dw_func(me->dvert+mface->v3, ob->actdef-1);
						if(dw) {paintweight+= dw->weight; totw++;}
						if(mface->v4) {
							dw= dw_func(me->dvert+mface->v4, ob->actdef-1);
							if(dw) {paintweight+= dw->weight; totw++;}
						}
					}
				}
			}
			
			if(wp->mode==VP_BLUR) 
				paintweight/= (float)totw;
			
			for(index=0; index<totindex; index++) {
				
				if(indexar[index] && indexar[index]<=me->totface) {
					MFace *mface= me->mface + (indexar[index]-1);
					
					if((me->dvert+mface->v1)->flag) {
						alpha= calc_vp_alpha_dl(wp, vc, wpd->wpimat, wpd->vertexcosnos+6*mface->v1, mval);
						if(alpha) {
							do_weight_paint_vertex(wp, ob, mface->v1, alpha, paintweight, wpd->vgroup_mirror);
						}
						(me->dvert+mface->v1)->flag= 0;
					}
					
					if((me->dvert+mface->v2)->flag) {
						alpha= calc_vp_alpha_dl(wp, vc, wpd->wpimat, wpd->vertexcosnos+6*mface->v2, mval);
						if(alpha) {
							do_weight_paint_vertex(wp, ob, mface->v2, alpha, paintweight, wpd->vgroup_mirror);
						}
						(me->dvert+mface->v2)->flag= 0;
					}
					
					if((me->dvert+mface->v3)->flag) {
						alpha= calc_vp_alpha_dl(wp, vc, wpd->wpimat, wpd->vertexcosnos+6*mface->v3, mval);
						if(alpha) {
							do_weight_paint_vertex(wp, ob, mface->v3, alpha, paintweight, wpd->vgroup_mirror);
						}
						(me->dvert+mface->v3)->flag= 0;
					}
					
					if((me->dvert+mface->v4)->flag) {
						if(mface->v4) {
							alpha= calc_vp_alpha_dl(wp, vc, wpd->wpimat, wpd->vertexcosnos+6*mface->v4, mval);
							if(alpha) {
								do_weight_paint_vertex(wp, ob, mface->v4, alpha, paintweight, wpd->vgroup_mirror);
							}
							(me->dvert+mface->v4)->flag= 0;
						}
					}
				}
			}
			
			MTC_Mat4SwapMat4(vc->rv3d->persmat, mat);
			
			DAG_object_flush_update(vc->scene, ob, OB_RECALC_DATA);
			ED_region_tag_redraw(vc->ar);
		}
	}

	return OPERATOR_RUNNING_MODAL;
}

static int wpaint_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	Scene *scene= CTX_data_scene(C);
	ToolSettings *ts= CTX_data_tool_settings(C);
	VPaint *wp= ts->wpaint;
	Object *ob= CTX_data_active_object(C);
	struct WPaintData *wpd;
	Mesh *me;
	float mat[4][4], imat[4][4];
	
	if(scene->obedit) return OPERATOR_CANCELLED;
	// XXX	if(multires_level1_test()) return;
	
	me= get_mesh(ob);
	if(me==NULL || me->totface==0) return OPERATOR_CANCELLED;
	
	/* if nothing was added yet, we make dverts and a vertex deform group */
	if (!me->dvert)
		create_dverts(&me->id);
	
	/* make customdata storage */
	op->customdata= wpd= MEM_callocN(sizeof(struct WPaintData), "WPaintData");
	view3d_set_viewcontext(C, &wpd->vc);
	wpd->vgroup_mirror= -1;
	
	//	if(qual & LR_CTRLKEY) {
	//		sample_wpaint(scene, ar, v3d, 0);
	//		return;
	//	}
	//	if(qual & LR_SHIFTKEY) {
	//		sample_wpaint(scene, ar, v3d, 1);
	//		return;
	//	}
	
	/* ALLOCATIONS! no return after this line */
	/* painting on subsurfs should give correct points too, this returns me->totvert amount */
	wpd->vertexcosnos= mesh_get_mapped_verts_nors(scene, ob);
	wpd->indexar= get_indexarray();
	copy_wpaint_prev(wp, me->dvert, me->totvert);
	
	/* this happens on a Bone select, when no vgroup existed yet */
	if(ob->actdef<=0) {
		Object *modob;
		if((modob = modifiers_isDeformedByArmature(ob))) {
			bPoseChannel *pchan;
			for(pchan= modob->pose->chanbase.first; pchan; pchan= pchan->next)
				if(pchan->bone->flag & SELECT)
					break;
			if(pchan) {
				bDeformGroup *dg= get_named_vertexgroup(ob, pchan->name);
				if(dg==NULL)
					dg= add_defgroup_name(ob, pchan->name);	/* sets actdef */
				else
					ob->actdef= get_defgroup_num(ob, dg);
			}
		}
	}
	if(ob->defbase.first==NULL) {
		add_defgroup(ob);
	}	
	
	//	if(ob->lay & v3d->lay); else error("Active object is not in this layer");
	
	/* imat for normals */
	Mat4MulMat4(mat, ob->obmat, wpd->vc.rv3d->viewmat);
	Mat4Invert(imat, mat);
	Mat3CpyMat4(wpd->wpimat, imat);
	
	/* if mirror painting, find the other group */
	if(wp->flag & VP_MIRROR_X) {
		bDeformGroup *defgroup= BLI_findlink(&ob->defbase, ob->actdef-1);
		if(defgroup) {
			bDeformGroup *curdef;
			int actdef= 0;
			char name[32];
			
			BLI_strncpy(name, defgroup->name, 32);
			bone_flip_name(name, 0);		/* 0 = don't strip off number extensions */
			
			for (curdef = ob->defbase.first; curdef; curdef=curdef->next, actdef++)
				if (!strcmp(curdef->name, name))
					break;
			if(curdef==NULL) {
				int olddef= ob->actdef;	/* tsk, add_defgroup sets the active defgroup */
				curdef= add_defgroup_name (ob, name);
				ob->actdef= olddef;
			}
			
			if(curdef && curdef!=defgroup)
				wpd->vgroup_mirror= actdef;
		}
	}
	
	/* do paint once for click only paint */
	wpaint_modal(C, op, event);
	
	/* add modal handler */
	WM_event_add_modal_handler(C, &CTX_wm_window(C)->handlers, op);
	
	return OPERATOR_RUNNING_MODAL;
}

void VIEW3D_OT_wpaint(wmOperatorType *ot)
{
	
	/* identifiers */
	ot->name= "Weight Paint";
	ot->idname= "VIEW3D_OT_wpaint";
	
	/* api callbacks */
	ot->invoke= wpaint_invoke;
	ot->modal= wpaint_modal;
	/* ot->exec= vpaint_exec; <-- needs stroke property */
	ot->poll= wp_poll;
	
}


/* ************ set / clear vertex paint mode ********** */

/* retrieve whether cursor should be set or operator should be done */
static int vp_poll(bContext *C)
{
	if(G.f & G_VERTEXPAINT) {
		ScrArea *sa= CTX_wm_area(C);
		if(sa->spacetype==SPACE_VIEW3D) {
			ARegion *ar= CTX_wm_region(C);
			if(ar->regiontype==RGN_TYPE_WINDOW)
				return 1;
		}
	}
	return 0;
}

static void vp_drawcursor(bContext *C, int x, int y)
{
	ToolSettings *ts= CTX_data_tool_settings(C);
	
	glTranslatef((float)x, (float)y, 0.0f);
	
	glColor4ub(255, 255, 255, 128);
	glEnable( GL_LINE_SMOOTH );
	glEnable(GL_BLEND);
	glutil_draw_lined_arc(0.0, M_PI*2.0, ts->vpaint->size, 40);
	glDisable(GL_BLEND);
	glDisable( GL_LINE_SMOOTH );
	
	glTranslatef((float)-x, (float)-y, 0.0f);
}

static int set_vpaint(bContext *C, wmOperator *op)		/* toggle */
{	
	Object *ob= CTX_data_active_object(C);
	Scene *scene= CTX_data_scene(C);
	VPaint *vp= scene->toolsettings->vpaint;
	Mesh *me;
	
	if(object_data_is_libdata(ob)) {
		G.f &= ~G_VERTEXPAINT;
		return OPERATOR_FINISHED;
	}
	
	me= get_mesh(ob);
	
	if(me && me->totface>=MAXINDEX) {
		error("Maximum number of faces: %d", MAXINDEX-1);
		G.f &= ~G_VERTEXPAINT;
		return OPERATOR_FINISHED;
	}
	
	if(me && me->mcol==NULL) make_vertexcol(scene, 0);
	
	/* toggle: end vpaint */
	if(G.f & G_VERTEXPAINT) {
		
		G.f &= ~G_VERTEXPAINT;
		
		if(vp) {
			WM_paint_cursor_end(CTX_wm_manager(C), vp->paintcursor);
			vp->paintcursor= NULL;
		}
	}
	else {
		
		G.f |= G_VERTEXPAINT;
		/* Turn off weight painting */
		if (G.f & G_WEIGHTPAINT)
			set_wpaint(C, op);
		
		if(vp==NULL)
			vp= scene->toolsettings->vpaint= new_vpaint(0);
		
		vp->paintcursor = WM_paint_cursor_activate(CTX_wm_manager(C), vp_poll, vp_drawcursor);
	}
	
	if (me)
		/* update modifier stack for mapping requirements */
		DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	
	WM_event_add_notifier(C, NC_SCENE|ND_MODE, ob);
	
	return OPERATOR_FINISHED;
}

void VIEW3D_OT_vpaint_toggle(wmOperatorType *ot)
{
	
	/* identifiers */
	ot->name= "Vertex Paint Mode";
	ot->idname= "VIEW3D_OT_vpaint_toggle";
	
	/* api callbacks */
	ot->exec= set_vpaint;
	ot->poll= ED_operator_object_active;
	
}



/* ********************** vertex paint operator ******************* */

/* Implementation notes:

Operator->invoke()
  - validate context (add mcol)
  - create customdata storage
  - call paint once (mouse click)
  - add modal handler 

Operator->modal()
  - for every mousemove, apply vertex paint
  - exit on mouse release, free customdata
    (return OPERATOR_FINISHED also removes handler and operator)

For future:
  - implement a stroke event (or mousemove with past positons)
  - revise whether op->customdata should be added in object, in set_vpaint

*/

struct VPaintData {
	ViewContext vc;
	unsigned int paintcol;
	int *indexar;
	float *vertexcosnos;
	float vpimat[3][3];
};

static void vpaint_exit(bContext *C, wmOperator *op)
{
	ToolSettings *ts= CTX_data_tool_settings(C);
	struct VPaintData *vpd= op->customdata;
	
	if(vpd->vertexcosnos)
		MEM_freeN(vpd->vertexcosnos);
	MEM_freeN(vpd->indexar);
	
	/* frees prev buffer */
	copy_vpaint_prev(ts->vpaint, NULL, 0);
	
	ED_undo_push(C, "Vertex Paint");
	
	MEM_freeN(vpd);
	op->customdata= NULL;
}

static int vpaint_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	ToolSettings *ts= CTX_data_tool_settings(C);
	VPaint *vp= ts->vpaint;
	
	switch(event->type) {
		case LEFTMOUSE:
			if(event->val==0) { /* release */
				vpaint_exit(C, op);
				return OPERATOR_FINISHED;
			}
			/* pass on, first press gets painted too */
			
		case MOUSEMOVE: 
		{
			struct VPaintData *vpd= op->customdata;
			ViewContext *vc= &vpd->vc;
			Object *ob= vc->obact;
			Mesh *me= ob->data;
			float mat[4][4];
			int *indexar= vpd->indexar;
			int totindex, index;
			short mval[2];
			
			view3d_operator_needs_opengl(C);
			
			/* load projection matrix */
			wmMultMatrix(ob->obmat);
			wmGetSingleMatrix(mat);
			wmLoadMatrix(vc->rv3d->viewmat);
			
			mval[0]= event->x - vc->ar->winrct.xmin;
			mval[1]= event->y - vc->ar->winrct.ymin;
				
			/* which faces are involved */
			if(vp->flag & VP_AREA) {
				totindex= sample_backbuf_area(vc, indexar, me->totface, mval[0], mval[1], vp->size);
			}
			else {
				indexar[0]= view3d_sample_backbuf(vc, mval[0], mval[1]);
				if(indexar[0]) totindex= 1;
				else totindex= 0;
			}
			
			MTC_Mat4SwapMat4(vc->rv3d->persmat, mat);
			
			if(vp->flag & VP_COLINDEX) {
				for(index=0; index<totindex; index++) {
					if(indexar[index] && indexar[index]<=me->totface) {
						MFace *mface= ((MFace *)me->mface) + (indexar[index]-1);
						
						if(mface->mat_nr!=ob->actcol-1) {
							indexar[index]= 0;
						}
					}					
				}
			}
			if((G.f & G_FACESELECT) && me->mface) {
				for(index=0; index<totindex; index++) {
					if(indexar[index] && indexar[index]<=me->totface) {
						MFace *mface= ((MFace *)me->mface) + (indexar[index]-1);
						
						if((mface->flag & ME_FACE_SEL)==0)
							indexar[index]= 0;
					}					
				}
			}
			
			for(index=0; index<totindex; index++) {
				
				if(indexar[index] && indexar[index]<=me->totface) {
					MFace *mface= ((MFace *)me->mface) + (indexar[index]-1);
					unsigned int *mcol=	  ( (unsigned int *)me->mcol) + 4*(indexar[index]-1);
					unsigned int *mcolorig= ( (unsigned int *)vp->vpaint_prev) + 4*(indexar[index]-1);
					int alpha;
					
					if(vp->mode==VP_BLUR) {
						unsigned int fcol1= mcol_blend( mcol[0], mcol[1], 128);
						if(mface->v4) {
							unsigned int fcol2= mcol_blend( mcol[2], mcol[3], 128);
							vpd->paintcol= mcol_blend( fcol1, fcol2, 128);
						}
						else {
							vpd->paintcol= mcol_blend( mcol[2], fcol1, 170);
						}
						
					}
					
					alpha= calc_vp_alpha_dl(vp, vc, vpd->vpimat, vpd->vertexcosnos+6*mface->v1, mval);
					if(alpha) vpaint_blend(vp, mcol, mcolorig, vpd->paintcol, alpha);
					
					alpha= calc_vp_alpha_dl(vp, vc, vpd->vpimat, vpd->vertexcosnos+6*mface->v2, mval);
					if(alpha) vpaint_blend(vp, mcol+1, mcolorig+1, vpd->paintcol, alpha);
					
					alpha= calc_vp_alpha_dl(vp, vc, vpd->vpimat, vpd->vertexcosnos+6*mface->v3, mval);
					if(alpha) vpaint_blend(vp, mcol+2, mcolorig+2, vpd->paintcol, alpha);
					
					if(mface->v4) {
						alpha= calc_vp_alpha_dl(vp, vc, vpd->vpimat, vpd->vertexcosnos+6*mface->v4, mval);
						if(alpha) vpaint_blend(vp, mcol+3, mcolorig+3, vpd->paintcol, alpha);
					}
				}
			}
						
			MTC_Mat4SwapMat4(vc->rv3d->persmat, mat);
			
			do_shared_vertexcol(me);
			
			ED_region_tag_redraw(vc->ar);
			
			DAG_object_flush_update(vc->scene, ob, OB_RECALC_DATA);
		}
		break;
	}	

	return OPERATOR_RUNNING_MODAL;
}

static int vpaint_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	ToolSettings *ts= CTX_data_tool_settings(C);
	VPaint *vp= ts->vpaint;
	struct VPaintData *vpd;
	Object *ob= CTX_data_active_object(C);
	Mesh *me;
	float mat[4][4], imat[4][4];
	
	/* context checks could be a poll() */
	me= get_mesh(ob);
	if(me==NULL || me->totface==0) return OPERATOR_CANCELLED;
	
	if(me->mcol==NULL) make_vertexcol(CTX_data_scene(C), 0);
	if(me->mcol==NULL) return OPERATOR_CANCELLED;
	
	/* make customdata storage */
	op->customdata= vpd= MEM_callocN(sizeof(struct VPaintData), "VPaintData");
	view3d_set_viewcontext(C, &vpd->vc);
	
	vpd->vertexcosnos= mesh_get_mapped_verts_nors(vpd->vc.scene, ob);
	vpd->indexar= get_indexarray();
	vpd->paintcol= vpaint_get_current_col(vp);
	
	/* for filtering */
	copy_vpaint_prev(vp, (unsigned int *)me->mcol, me->totface);
	
	/* some old cruft to sort out later */
	Mat4MulMat4(mat, ob->obmat, vpd->vc.rv3d->viewmat);
	Mat4Invert(imat, mat);
	Mat3CpyMat4(vpd->vpimat, imat);
	
	/* do paint once for click only paint */
	vpaint_modal(C, op, event);
	
	/* add modal handler */
	WM_event_add_modal_handler(C, &CTX_wm_window(C)->handlers, op);
	
	return OPERATOR_RUNNING_MODAL;
}

void VIEW3D_OT_vpaint(wmOperatorType *ot)
{
	
	/* identifiers */
	ot->name= "Vertex Paint";
	ot->idname= "VIEW3D_OT_vpaint";
	
	/* api callbacks */
	ot->invoke= vpaint_invoke;
	ot->modal= vpaint_modal;
	/* ot->exec= vpaint_exec; <-- needs stroke property */
	ot->poll= vp_poll;
	
}


