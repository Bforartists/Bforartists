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

editmesh_mods.c, UI level access, no geometry changes 

*/

#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "MTC_matrixops.h"

#include "DNA_mesh_types.h"
#include "DNA_material_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_texture_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_view3d_types.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_editVert.h"
#include "BLI_rand.h"

#include "BKE_displist.h"
#include "BKE_depsgraph.h"
#include "BKE_DerivedMesh.h"
#include "BKE_global.h"
#include "BKE_mesh.h"
#include "BKE_material.h"
#include "BKE_texture.h"
#include "BKE_utildefines.h"

#include "BIF_editmesh.h"
#include "BIF_resources.h"
#include "BIF_gl.h"
#include "BIF_glutil.h"
#include "BIF_graphics.h"
#include "BIF_interface.h"
#include "BIF_meshtools.h"
#include "BIF_mywindow.h"
#include "BIF_resources.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_toolbox.h"

#include "BDR_drawobject.h"
#include "BDR_editobject.h"

#include "BSE_drawview.h"
#include "BSE_edit.h"
#include "BSE_view.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "RE_render_ext.h"  // externtex

#include "mydevice.h"
#include "blendef.h"

#include "editmesh.h"


/* ****************************** MIRROR **************** */

void EM_select_mirrored(void)
{
	if(G.scene->selectmode & SCE_SELECT_VERTEX) {
		EditMesh *em = G.editMesh;
		EditVert *eve, *v1;
		
		for(eve= em->verts.first; eve; eve= eve->next) {
			if(eve->f & SELECT) {
				v1= editmesh_get_x_mirror_vert(G.obedit, eve->co);
				if(v1) {
					eve->f &= ~SELECT;
					v1->f |= SELECT;
				}
			}
		}
	}
}

/* ****************************** SELECTION ROUTINES **************** */

unsigned int em_solidoffs=0, em_wireoffs=0, em_vertoffs=0;	// set in drawobject.c ... for colorindices

static void check_backbuf(void)
{
	if(G.vd->flag & V3D_NEEDBACKBUFDRAW) {
		backdrawview3d(0);
	}
}

/* samples a single pixel (copied from vpaint) */
static unsigned int sample_backbuf(int x, int y)
{
	unsigned int col;
	
	if(x>=curarea->winx || y>=curarea->winy) return 0;
	x+= curarea->winrct.xmin;
	y+= curarea->winrct.ymin;
	
	check_backbuf(); // actually not needed for apple

#ifdef __APPLE__
	glReadBuffer(GL_AUX0);
#endif
	glReadPixels(x,  y, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE,  &col);
	glReadBuffer(GL_BACK);	
	
	if(G.order==B_ENDIAN) SWITCH_INT(col);
	
	return framebuffer_to_index(col);
}

/* reads full rect, converts indices */
struct ImBuf *read_backbuf(short xmin, short ymin, short xmax, short ymax)
{
	unsigned int *dr, *rd;
	struct ImBuf *ibuf, *ibuf1;
	int a;
	short xminc, yminc, xmaxc, ymaxc, xs, ys;
	
	/* clip */
	if(xmin<0) xminc= 0; else xminc= xmin;
	if(xmax>=curarea->winx) xmaxc= curarea->winx-1; else xmaxc= xmax;
	if(xminc > xmaxc) return NULL;

	if(ymin<0) yminc= 0; else yminc= ymin;
	if(ymax>=curarea->winy) ymaxc= curarea->winy-1; else ymaxc= ymax;
	if(yminc > ymaxc) return NULL;
	
	ibuf= IMB_allocImBuf((xmaxc-xminc+1),(ymaxc-yminc+1),32,IB_rect,0);

	check_backbuf(); // actually not needed for apple
	
#ifdef __APPLE__
	glReadBuffer(GL_AUX0);
#endif
	glReadPixels(curarea->winrct.xmin+xminc, curarea->winrct.ymin+yminc, (xmaxc-xminc+1), (ymaxc-yminc+1), GL_RGBA, GL_UNSIGNED_BYTE, ibuf->rect);
	glReadBuffer(GL_BACK);	

	if(G.order==B_ENDIAN) IMB_convert_rgba_to_abgr(ibuf);

	a= (xmaxc-xminc+1)*(ymaxc-yminc+1);
	dr= ibuf->rect;
	while(a--) {
		if(*dr) *dr= framebuffer_to_index(*dr);
		dr++;
	}
	
	/* put clipped result back, if needed */
	if(xminc==xmin && xmaxc==xmax && yminc==ymin && ymaxc==ymax) return ibuf;
	ibuf1= IMB_allocImBuf( (xmax-xmin+1),(ymax-ymin+1),32,IB_rect,0);
	rd= ibuf->rect;
	dr= ibuf1->rect;
		
	for(ys= ymin; ys<=ymax; ys++) {
		for(xs= xmin; xs<=xmax; xs++, dr++) {
			if( xs>=xminc && xs<=xmaxc && ys>=yminc && ys<=ymaxc) {
				*dr= *rd;
				rd++;
			}
		}
	}
	IMB_freeImBuf(ibuf);
	return ibuf1;
}


/* smart function to sample a rect spiralling outside, nice for backbuf selection */
static unsigned int sample_backbuf_rect(short mval[2], int size, unsigned int min, unsigned int max, short *dist)
{
	struct ImBuf *buf;
	unsigned int *bufmin, *bufmax, *tbuf;
	int minx, miny;
	int a, b, rc, nr, amount, dirvec[4][2];
	short distance=0;
	unsigned int index = 0;
	
	amount= (size-1)/2;

	minx = mval[0]-(amount+1);
	miny = mval[1]-(amount+1);
	buf = read_backbuf(minx, miny, minx+size-1, miny+size-1);
	if (!buf) return 0;

	rc= 0;
	
	dirvec[0][0]= 1; dirvec[0][1]= 0;
	dirvec[1][0]= 0; dirvec[1][1]= -size;
	dirvec[2][0]= -1; dirvec[2][1]= 0;
	dirvec[3][0]= 0; dirvec[3][1]= size;
	
	bufmin = buf->rect;
	tbuf = buf->rect;
	bufmax = buf->rect + size*size;
	tbuf+= amount*size+ amount;
	
	for(nr=1; nr<=size; nr++) {
		
		for(a=0; a<2; a++) {
			for(b=0; b<nr; b++, distance++) {
				if (*tbuf && *tbuf>=min && *tbuf<max) {
					*dist= (short) sqrt( (float)distance ); // XXX, this distance is wrong - zr
					index = *tbuf - min+1; // messy yah, but indices start at 1
					goto exit;
				}
				
				tbuf+= (dirvec[rc][0]+dirvec[rc][1]);
				
				if(tbuf<bufmin || tbuf>=bufmax) {
					goto exit;
				}
			}
			rc++;
			rc &= 3;
		}
	}

exit:
	IMB_freeImBuf(buf);
	return index;
}

/* facilities for border select and circle select */
static char *selbuf= NULL;

/* opengl doesn't support concave... */
static void draw_triangulated(short mcords[][2], short tot)
{
	ListBase lb={NULL, NULL};
	DispList *dl;
	float *fp;
	int a;
	
	/* make displist */
	dl= MEM_callocN(sizeof(DispList), "poly disp");
	dl->type= DL_POLY;
	dl->parts= 1;
	dl->nr= tot;
	dl->verts= fp=  MEM_callocN(tot*3*sizeof(float), "poly verts");
	BLI_addtail(&lb, dl);
	
	for(a=0; a<tot; a++, fp+=3) {
		fp[0]= (float)mcords[a][0];
		fp[1]= (float)mcords[a][1];
	}
	
	/* do the fill */
	filldisplist(&lb, &lb);

	/* do the draw */
	dl= lb.first;	// filldisplist adds in head of list
	if(dl->type==DL_INDEX3) {
		int *index;
		
		a= dl->parts;
		fp= dl->verts;
		index= dl->index;
		glBegin(GL_TRIANGLES);
		while(a--) {
			glVertex3fv(fp+3*index[0]);
			glVertex3fv(fp+3*index[1]);
			glVertex3fv(fp+3*index[2]);
			index+= 3;
		}
		glEnd();
	}
	
	freedisplist(&lb);
}


/* reads rect, and builds selection array for quick lookup */
/* returns if all is OK */
int EM_init_backbuf_border(short xmin, short ymin, short xmax, short ymax)
{
	struct ImBuf *buf;
	unsigned int *dr;
	int a;
	
	if(G.obedit==NULL || G.vd->drawtype<OB_SOLID || (G.vd->flag & V3D_ZBUF_SELECT)==0) return 0;
	if(em_vertoffs==0) return 0;
	
	buf= read_backbuf(xmin, ymin, xmax, ymax);
	if(buf==NULL) return 0;

	dr = buf->rect;
	
	/* build selection lookup */
	selbuf= MEM_callocN(em_vertoffs+1, "selbuf");
	
	a= (xmax-xmin+1)*(ymax-ymin+1);
	while(a--) {
		if(*dr>0 && *dr<=em_vertoffs) 
			selbuf[*dr]= 1;
		dr++;
	}
	IMB_freeImBuf(buf);
	return 1;
}

int EM_check_backbuf(unsigned int index)
{
	if(selbuf==NULL) return 1;
	if(index>0 && index<=em_vertoffs)
		return selbuf[index];
	return 0;
}

void EM_free_backbuf(void)
{
	if(selbuf) MEM_freeN(selbuf);
	selbuf= NULL;
}

/* mcords is a polygon mask
   - grab backbuffer,
   - draw with black in backbuffer, 
   - grab again and compare
   returns 'OK' 
*/
int EM_mask_init_backbuf_border(short mcords[][2], short tot, short xmin, short ymin, short xmax, short ymax)
{
	unsigned int *dr, *drm;
	struct ImBuf *buf, *bufmask;
	int a;
	
	/* method in use for face selecting too */
	if(G.obedit==NULL) {
		if(G.f & G_FACESELECT);
		else return 0;
	}
	else if(G.vd->drawtype<OB_SOLID || (G.vd->flag & V3D_ZBUF_SELECT)==0) return 0;

	if(em_vertoffs==0) return 0;
	
	buf= read_backbuf(xmin, ymin, xmax, ymax);
	if(buf==NULL) return 0;

	dr = buf->rect;

	/* draw the mask */
#ifdef __APPLE__
	glDrawBuffer(GL_AUX0);
#endif
	glDisable(GL_DEPTH_TEST);
	
	persp(PERSP_WIN);
	glColor3ub(0, 0, 0);
	
	/* yah, opengl doesn't do concave... tsk! */
 	draw_triangulated(mcords, tot);	
	
	glBegin(GL_LINE_LOOP);	// for zero sized masks, lines
	for(a=0; a<tot; a++) glVertex2s(mcords[a][0], mcords[a][1]);
	glEnd();
	
	persp(PERSP_VIEW);
	glFinish();	// to be sure readpixels sees mask
	
	glDrawBuffer(GL_BACK);
	
	/* grab mask */
	bufmask= read_backbuf(xmin, ymin, xmax, ymax);
	drm = bufmask->rect;
	if(bufmask==NULL) return 0; // only when mem alloc fails, go crash somewhere else!
	
	/* build selection lookup */
	selbuf= MEM_callocN(em_vertoffs+1, "selbuf");
	
	a= (xmax-xmin+1)*(ymax-ymin+1);
	while(a--) {
		if(*dr>0 && *dr<=em_vertoffs && *drm==0) selbuf[*dr]= 1;
		dr++; drm++;
	}
	IMB_freeImBuf(buf);
	IMB_freeImBuf(bufmask);
	return 1;
	
}

/* circle shaped sample area */
int EM_init_backbuf_circle(short xs, short ys, short rads)
{
	struct ImBuf *buf;
	unsigned int *dr;
	short xmin, ymin, xmax, ymax, xc, yc;
	int radsq;
	
	/* method in use for face selecting too */
	if(G.obedit==NULL) {
		if(G.f & G_FACESELECT);
		else return 0;
	}
	else if(G.vd->drawtype<OB_SOLID || (G.vd->flag & V3D_ZBUF_SELECT)==0) return 0;
	if(em_vertoffs==0) return 0;
	
	xmin= xs-rads; xmax= xs+rads;
	ymin= ys-rads; ymax= ys+rads;
	buf= read_backbuf(xmin, ymin, xmax, ymax);
	if(buf==NULL) return 0;

	dr = buf->rect;
	
	/* build selection lookup */
	selbuf= MEM_callocN(em_vertoffs+1, "selbuf");
	radsq= rads*rads;
	for(yc= -rads; yc<=rads; yc++) {
		for(xc= -rads; xc<=rads; xc++, dr++) {
			if(xc*xc + yc*yc < radsq) {
				if(*dr>0 && *dr<=em_vertoffs) selbuf[*dr]= 1;
			}
		}
	}

	IMB_freeImBuf(buf);
	return 1;
	
}

static void findnearestvert__doClosest(void *userData, EditVert *eve, int x, int y, int index)
{
	struct { short mval[2], pass, select; int dist, lastIndex, closestIndex; EditVert *closest; } *data = userData;

	if (data->pass==0) {
		if (index<=data->lastIndex)
			return;
	} else {
		if (index>data->lastIndex)
			return;
	}

	if (data->dist>3) {
		int temp = abs(data->mval[0] - x) + abs(data->mval[1]- y);
		if ((eve->f&1)==data->select) temp += 5;

		if (temp<data->dist) {
			data->dist = temp;
			data->closest = eve;
			data->closestIndex = index;
		}
	}
}
static EditVert *findnearestvert(short *dist, short sel)
{
	short mval[2];

	getmouseco_areawin(mval);
		
	if(G.vd->drawtype>OB_WIRE && (G.vd->flag & V3D_ZBUF_SELECT)) {
		short distance;
		unsigned int index = sample_backbuf_rect(mval, 50, em_wireoffs, 0xFFFFFF, &distance);
		EditVert *eve = BLI_findlink(&G.editMesh->verts, index-1);

		if (eve && distance < *dist) {
			*dist = distance;
			return eve;
		} else {
			return NULL;
		}
	}
	else {
		struct { short mval[2], pass, select; int dist, lastIndex, closestIndex; EditVert *closest; } data;
		static int lastSelectedIndex=0;
		static EditVert *lastSelected=NULL;

		if (lastSelected && BLI_findlink(&G.editMesh->verts, lastSelectedIndex)!=lastSelected) {
			lastSelectedIndex = 0;
			lastSelected = NULL;
		}

		data.lastIndex = lastSelectedIndex;
		data.mval[0] = mval[0];
		data.mval[1] = mval[1];
		data.select = sel;
		data.dist = *dist;
		data.closest = NULL;
		data.closestIndex = 0;

		data.pass = 0;
		mesh_foreachScreenVert(findnearestvert__doClosest, &data, 1);

		if (data.dist>3) {
			data.pass = 1;
			mesh_foreachScreenVert(findnearestvert__doClosest, &data, 1);
		}

		*dist = data.dist;
		lastSelected = data.closest;
		lastSelectedIndex = data.closestIndex;

		return data.closest;
	}
}

/* returns labda for closest distance v1 to line-piece v2-v3 */
static float labda_PdistVL2Dfl( float *v1, float *v2, float *v3) 
{
	float rc[2], len;
	
	rc[0]= v3[0]-v2[0];
	rc[1]= v3[1]-v2[1];
	len= rc[0]*rc[0]+ rc[1]*rc[1];
	if(len==0.0f)
		return 0.0f;
	
	return ( rc[0]*(v1[0]-v2[0]) + rc[1]*(v1[1]-v2[1]) )/len;
}

/* note; uses G.vd, so needs active 3d window */
static void findnearestedge__doClosest(void *userData, EditEdge *eed, int x0, int y0, int x1, int y1, int index)
{
	struct { float mval[2]; short dist; EditEdge *closest; } *data = userData;
	float v1[2], v2[2];
	short distance;
		
	v1[0] = x0;
	v1[1] = y0;
	v2[0] = x1;
	v2[1] = y1;
		
	distance= PdistVL2Dfl(data->mval, v1, v2);
		
	if(eed->f & SELECT) distance+=5;
	if(distance < data->dist) {
		if(G.vd->flag & V3D_CLIPPING) {
			float labda= labda_PdistVL2Dfl(data->mval, v1, v2);
			float vec[3];

			vec[0]= eed->v1->co[0] + labda*(eed->v2->co[0] - eed->v1->co[0]);
			vec[1]= eed->v1->co[1] + labda*(eed->v2->co[1] - eed->v1->co[1]);
			vec[2]= eed->v1->co[2] + labda*(eed->v2->co[2] - eed->v1->co[2]);
			Mat4MulVecfl(G.obedit->obmat, vec);

			if(view3d_test_clipping(G.vd, vec)==0) {
				data->dist = distance;
				data->closest = eed;
			}
		}
		else {
			data->dist = distance;
			data->closest = eed;
		}
	}
}
EditEdge *findnearestedge(short *dist)
{
	short mval[2];
		
	getmouseco_areawin(mval);

	if(G.vd->drawtype>OB_WIRE && (G.vd->flag & V3D_ZBUF_SELECT)) {
		short distance;
		unsigned int index = sample_backbuf_rect(mval, 50, em_solidoffs, em_wireoffs, &distance);
		EditEdge *eed = BLI_findlink(&G.editMesh->edges, index-1);

		if (eed && distance<*dist) {
			*dist = distance;
			return eed;
		} else {
			return NULL;
		}
	}
	else {
		struct { float mval[2]; short dist; EditEdge *closest; } data;

		data.mval[0] = mval[0];
		data.mval[1] = mval[1];
		data.dist = *dist;
		data.closest = NULL;

		mesh_foreachScreenEdge(findnearestedge__doClosest, &data, 2);

		*dist = data.dist;
		return data.closest;
	}
}

static void findnearestface__getDistance(void *userData, EditFace *efa, int x, int y, int index)
{
	struct { short mval[2], dist; EditFace *toFace; } *data = userData;

	if (efa==data->toFace) {
		short temp = abs(data->mval[0]-x) + abs(data->mval[1]-y);

		if (temp<data->dist)
			data->dist = temp;
	}
}
static void findnearestface__doClosest(void *userData, EditFace *efa, int x, int y, int index)
{
	struct { short mval[2], pass, dist; int lastIndex, closestIndex; EditFace *closest; } *data = userData;

	if (data->pass==0) {
		if (index<=data->lastIndex)
			return;
	} else {
		if (index>data->lastIndex)
			return;
	}

	if (data->dist>3) {
		short temp = abs(data->mval[0]-x) + abs(data->mval[1]-y);

		if (temp<data->dist) {
			data->dist = temp;
			data->closest = efa;
			data->closestIndex = index;
		}
	}
}
static EditFace *findnearestface(short *dist)
{
	short mval[2];

	getmouseco_areawin(mval);

	if(G.vd->drawtype>OB_WIRE && (G.vd->flag & V3D_ZBUF_SELECT)) {
		unsigned int index = sample_backbuf(mval[0], mval[1]);
		EditFace *efa = BLI_findlink(&G.editMesh->faces, index-1);

		if (efa) {
			struct { short mval[2], dist; EditFace *toFace; } data;

			data.mval[0] = mval[0];
			data.mval[1] = mval[1];
			data.dist = 0x7FFF;		// largest short
			data.toFace = efa;

			mesh_foreachScreenFace(findnearestface__getDistance, &data);

			if(G.scene->selectmode == SCE_SELECT_FACE || data.dist<*dist) {	// only faces, no dist check
				*dist= data.dist;
				return efa;
			}
		}
		
		return NULL;
	}
	else {
		struct { short mval[2], pass, dist; int lastIndex, closestIndex; EditFace *closest; } data;
		static int lastSelectedIndex=0;
		static EditFace *lastSelected=NULL;

		if (lastSelected && BLI_findlink(&G.editMesh->faces, lastSelectedIndex)!=lastSelected) {
			lastSelectedIndex = 0;
			lastSelected = NULL;
		}

		data.lastIndex = lastSelectedIndex;
		data.mval[0] = mval[0];
		data.mval[1] = mval[1];
		data.dist = *dist;
		data.closest = NULL;
		data.closestIndex = 0;

		data.pass = 0;
		mesh_foreachScreenFace(findnearestface__doClosest, &data);

		if (data.dist>3) {
			data.pass = 1;
			mesh_foreachScreenFace(findnearestface__doClosest, &data);
		}

		*dist = data.dist;
		lastSelected = data.closest;
		lastSelectedIndex = data.closestIndex;

		return data.closest;
	}
}

/* for interactivity, frontbuffer draw in current window */
static void draw_dm_mapped_vert__mapFunc(void *theVert, int index, float *co, float *no_f, short *no_s)
{
	if (EM_get_vert_for_index(index)==theVert) {
		bglVertex3fv(co);
	}
}
static void draw_dm_mapped_vert(DerivedMesh *dm, EditVert *eve)
{
	EM_init_index_arrays(1, 0, 0);
	bglBegin(GL_POINTS);
	dm->foreachMappedVert(dm, draw_dm_mapped_vert__mapFunc, eve);
	bglEnd();
	EM_free_index_arrays();
}

static int draw_dm_mapped_edge__setDrawOptions(void *theEdge, int index)
{
	return EM_get_edge_for_index(index)==theEdge;
}
static void draw_dm_mapped_edge(DerivedMesh *dm, EditEdge *eed)
{
	EM_init_index_arrays(0, 1, 0);
	dm->drawMappedEdges(dm, draw_dm_mapped_edge__setDrawOptions, eed);
	EM_free_index_arrays();
}

static void draw_dm_mapped_face_center__mapFunc(void *theFace, int index, float *cent, float *no)
{
	if (EM_get_face_for_index(index)==theFace) {
		bglVertex3fv(cent);
	}
}
static void draw_dm_mapped_face_center(DerivedMesh *dm, EditFace *efa)
{
	EM_init_index_arrays(0, 0, 1);
	bglBegin(GL_POINTS);
	dm->foreachMappedFaceCenter(dm, draw_dm_mapped_face_center__mapFunc, efa);
	bglEnd();
	EM_free_index_arrays();
}

static void unified_select_draw(EditVert *eve, EditEdge *eed, EditFace *efa)
{
	int dmNeedsFree;
	DerivedMesh *dm = editmesh_get_derived_cage(&dmNeedsFree);

	glDrawBuffer(GL_FRONT);

	persp(PERSP_VIEW);
	
	if(G.vd->flag & V3D_CLIPPING)
		view3d_set_clipping(G.vd);
	
	glPushMatrix();
	mymultmatrix(G.obedit->obmat);
	
	/* face selected */
	if(efa) {
		if(G.scene->selectmode & SCE_SELECT_VERTEX) {
			glPointSize(BIF_GetThemeValuef(TH_VERTEX_SIZE));
			
			if(efa->f & SELECT) BIF_ThemeColor(TH_VERTEX_SELECT);
			else BIF_ThemeColor(TH_VERTEX);
			
			bglBegin(GL_POINTS);
			bglVertex3fv(efa->v1->co);
			bglVertex3fv(efa->v2->co);
			bglVertex3fv(efa->v3->co);
			if(efa->v4) bglVertex3fv(efa->v4->co);
			bglEnd();
		}

		if(G.scene->selectmode & (SCE_SELECT_EDGE|SCE_SELECT_FACE)) {
			if(efa->fgonf==0) {
				BIF_ThemeColor((efa->f & SELECT)?TH_EDGE_SELECT:TH_WIRE);
	
				draw_dm_mapped_edge(dm, efa->e1);
				draw_dm_mapped_edge(dm, efa->e2);
				draw_dm_mapped_edge(dm, efa->e3);
				if (efa->e4) {
					draw_dm_mapped_edge(dm, efa->e4);
				}
			}
		}
		
		if(G.scene->selectmode & SCE_SELECT_FACE) {
			if(efa->fgonf==0) {
				glPointSize(BIF_GetThemeValuef(TH_FACEDOT_SIZE));
				BIF_ThemeColor((efa->f & SELECT)?TH_FACE_DOT:TH_WIRE);

				draw_dm_mapped_face_center(dm, efa);
			}
		}
	}
	/* edge selected */
	if(eed) {
		if(G.scene->selectmode & (SCE_SELECT_EDGE|SCE_SELECT_FACE)) {
			BIF_ThemeColor((eed->f & SELECT)?TH_EDGE_SELECT:TH_WIRE);

			draw_dm_mapped_edge(dm, eed);
		}
		if(G.scene->selectmode & SCE_SELECT_VERTEX) {
			glPointSize(BIF_GetThemeValuef(TH_VERTEX_SIZE));
			
			BIF_ThemeColor((eed->f & SELECT)?TH_VERTEX_SELECT:TH_VERTEX);
			
			draw_dm_mapped_vert(dm, eed->v1);
			draw_dm_mapped_vert(dm, eed->v2);
		}
	}
	if(eve) {
		if(G.scene->selectmode & SCE_SELECT_VERTEX) {
			glPointSize(BIF_GetThemeValuef(TH_VERTEX_SIZE));
			
			BIF_ThemeColor((eve->f & SELECT)?TH_VERTEX_SELECT:TH_VERTEX);
			
			draw_dm_mapped_vert(dm, eve);
		}
	}

	glPointSize(1.0);
	glPopMatrix();

	glFlush();
	glDrawBuffer(GL_BACK);

	if(G.vd->flag & V3D_CLIPPING)
		view3d_clr_clipping();
	
	/* signal that frontbuf differs from back */
	curarea->win_swap= WIN_FRONT_OK;

	if (dmNeedsFree) {
		dm->release(dm);
	}
}


/* best distance based on screen coords. 
   use g.scene->selectmode to define how to use 
   selected vertices and edges get disadvantage
   return 1 if found one
*/
static int unified_findnearest(EditVert **eve, EditEdge **eed, EditFace **efa) 
{
	short dist= 75;
	
	*eve= NULL;
	*eed= NULL;
	*efa= NULL;
	
	if(G.scene->selectmode & SCE_SELECT_VERTEX)
		*eve= findnearestvert(&dist, SELECT);
	if(G.scene->selectmode & SCE_SELECT_FACE)
		*efa= findnearestface(&dist);

	dist-= 20;	// since edges select lines, we give dots advantage of 20 pix
	if(G.scene->selectmode & SCE_SELECT_EDGE)
		*eed= findnearestedge(&dist);

	/* return only one of 3 pointers, for frontbuffer redraws */
	if(*eed) {
		*efa= NULL; *eve= NULL;
	}
	else if(*efa) {
		*eve= NULL;
	}
	
	return (*eve || *eed || *efa);
}

/* ****************  LOOP SELECTS *************** */

/* selects quads in loop direction of indicated edge */
/* only flush over edges with valence <= 2 */
void faceloop_select(EditEdge *startedge, int select)
{
	EditMesh *em = G.editMesh;
	EditEdge *eed;
	EditFace *efa;
	int looking= 1;
	
	/* in eed->f1 we put the valence (amount of faces in edge) */
	/* in eed->f2 we put tagged flag as correct loop */
	/* in efa->f1 we put tagged flag as correct to select */

	for(eed= em->edges.first; eed; eed= eed->next) {
		eed->f1= 0;
		eed->f2= 0;
	}
	for(efa= em->faces.first; efa; efa= efa->next) {
		efa->f1= 0;
		if(efa->h==0) {
			efa->e1->f1++;
			efa->e2->f1++;
			efa->e3->f1++;
			if(efa->e4) efa->e4->f1++;
		}
	}
	
	// tag startedge OK
	startedge->f2= 1;
	
	while(looking) {
		looking= 0;
		
		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->e4 && efa->f1==0) {	// not done quad
				if(efa->e1->f1<=2 && efa->e2->f1<=2 && efa->e3->f1<=2 && efa->e4->f1<=2) { // valence ok

					// if edge tagged, select opposing edge and mark face ok
					if(efa->e1->f2) {
						efa->e3->f2= 1;
						efa->f1= 1;
						looking= 1;
					}
					else if(efa->e2->f2) {
						efa->e4->f2= 1;
						efa->f1= 1;
						looking= 1;
					}
					if(efa->e3->f2) {
						efa->e1->f2= 1;
						efa->f1= 1;
						looking= 1;
					}
					if(efa->e4->f2) {
						efa->e2->f2= 1;
						efa->f1= 1;
						looking= 1;
					}
				}
			}
		}
	}
	
	/* (de)select the faces */
	if(select!=2) {
		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->f1) EM_select_face(efa, select);
		}
	}
}


/* helper for edgeloop_select, checks for eed->f2 tag in faces */
static int edge_not_in_tagged_face(EditEdge *eed)
{
	EditMesh *em = G.editMesh;
	EditFace *efa;
	
	for(efa= em->faces.first; efa; efa= efa->next) {
		if(efa->h==0) {
			if(efa->e1==eed || efa->e2==eed || efa->e3==eed || efa->e4==eed) {	// edge is in face
				if(efa->e1->f2 || efa->e2->f2 || efa->e3->f2 || (efa->e4 && efa->e4->f2)) {	// face is tagged
					return 0;
				}
			}
		}
	}
	return 1;
}

/* selects or deselects edges that:
- if edges has 2 faces:
	- has vertices with valence of 4
	- not shares face with previous edge
- if edge has 1 face:
	- has vertices with valence 4
	- not shares face with previous edge
	- but also only 1 face
- if edge no face:
	- has vertices with valence 2
*/
static void edgeloop_select(EditEdge *starteed, int select)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;
	EditFace *efa;
	int looking= 1;
	
	/* in f1 we put the valence (amount of edges in a vertex, or faces in edge) */
	/* in eed->f2 and efa->f1 we put tagged flag as correct loop */
	for(eve= em->verts.first; eve; eve= eve->next) {
		eve->f1= 0;
		eve->f2= 0;
	}
	for(eed= em->edges.first; eed; eed= eed->next) {
		eed->f1= 0;
		eed->f2= 0;
		if((eed->h & 1)==0) {	// fgon edges add to valence too
			eed->v1->f1++; eed->v2->f1++;
		}
	}
	for(efa= em->faces.first; efa; efa= efa->next) {
		efa->f1= 0;
		if(efa->h==0) {
			efa->e1->f1++;
			efa->e2->f1++;
			efa->e3->f1++;
			if(efa->e4) efa->e4->f1++;
		}
	}
	
	/* looped edges & vertices get tagged f2 */
	starteed->f2= 1;
	if(starteed->v1->f1<5) starteed->v1->f2= 1;
	if(starteed->v2->f1<5) starteed->v2->f2= 1;
	/* sorry, first edge isnt even ok */
	if(starteed->v1->f2==0 && starteed->v2->f2==0) looking= 0;
	
	while(looking) {
		looking= 0;
		
		/* find correct valence edges which are not tagged yet, but connect to tagged one */
		for(eed= em->edges.first; eed; eed= eed->next) {
			if(eed->h==0 && eed->f2==0) { // edge not hidden, not tagged
				if( (eed->v1->f1<5 && eed->v1->f2) || (eed->v2->f1<5 && eed->v2->f2)) { // valence of vertex OK, and is tagged
					/* new edge is not allowed to be in face with tagged edge */
					if(edge_not_in_tagged_face(eed)) {
						if(eed->f1==starteed->f1) {	// same amount of faces
							looking= 1;
							eed->f2= 1;
							if(eed->v2->f1<5) eed->v2->f2= 1;
							if(eed->v1->f1<5) eed->v1->f2= 1;
						}
					}
				}
			}
		}
	}
	/* and we do the select */
	for(eed= em->edges.first; eed; eed= eed->next) {
		if(eed->f2) EM_select_edge(eed, select);
	}
}

/* 
   Almostly exactly the same code as faceloop select
*/
static void edgering_select(EditEdge *startedge, int select){
	EditMesh *em = G.editMesh;
	EditEdge *eed;
	EditFace *efa;
	int looking= 1;
	
	/* in eed->f1 we put the valence (amount of faces in edge) */
	/* in eed->f2 we put tagged flag as correct loop */
	/* in efa->f1 we put tagged flag as correct to select */

	for(eed= em->edges.first; eed; eed= eed->next) {
		eed->f1= 0;
		eed->f2= 0;
	}
	for(efa= em->faces.first; efa; efa= efa->next) {
		efa->f1= 0;
		if(efa->h==0) {
			efa->e1->f1++;
			efa->e2->f1++;
			efa->e3->f1++;
			if(efa->e4) efa->e4->f1++;
		}
	}
	
	// tag startedge OK
	startedge->f2= 1;
	
	while(looking) {
		looking= 0;
		
		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->e4 && efa->f1==0) {	// not done quad
				if(efa->e1->f1<=2 && efa->e2->f1<=2 && efa->e3->f1<=2 && efa->e4->f1<=2) { // valence ok

					// if edge tagged, select opposing edge and mark face ok
					if(efa->e1->f2) {
						efa->e3->f2= 1;
						efa->f1= 1;
						looking= 1;
					}
					else if(efa->e2->f2) {
						efa->e4->f2= 1;
						efa->f1= 1;
						looking= 1;
					}
					if(efa->e3->f2) {
						efa->e1->f2= 1;
						efa->f1= 1;
						looking= 1;
					}
					if(efa->e4->f2) {
						efa->e2->f2= 1;
						efa->f1= 1;
						looking= 1;
					}
				}
			}
		}
	}
	
	/* (de)select the edges */
	for(eed= em->edges.first; eed; eed= eed->next) {
    		if(eed->f2) EM_select_edge(eed, select);
	}
}
/* ***************** MAIN MOUSE SELECTION ************** */

// just to have the functions nice together
static void mouse_mesh_loop(void)
{
	EditEdge *eed;
	short dist= 50;
	
	eed= findnearestedge(&dist);
	if(eed) {
		
		if((G.qual & LR_SHIFTKEY)==0) EM_clear_flag_all(SELECT);
		
		if((eed->f & SELECT)==0) EM_select_edge(eed, 1);
		else if(G.qual & LR_SHIFTKEY) EM_select_edge(eed, 0);

		if(G.scene->selectmode & SCE_SELECT_FACE) {
			faceloop_select(eed, eed->f & SELECT);
		}
		else if(G.scene->selectmode & SCE_SELECT_EDGE) {
            if(G.qual == (LR_CTRLKEY | LR_ALTKEY) || G.qual == (LR_CTRLKEY | LR_ALTKEY |LR_SHIFTKEY))
    			edgering_select(eed, eed->f & SELECT);
            else if(G.qual & LR_ALTKEY)
    			edgeloop_select(eed, eed->f & SELECT);
		}
        else if(G.scene->selectmode & SCE_SELECT_VERTEX) {
            if(G.qual == (LR_CTRLKEY | LR_ALTKEY) || G.qual == (LR_CTRLKEY | LR_ALTKEY |LR_SHIFTKEY))
    			edgering_select(eed, eed->f & SELECT);
            else if(G.qual & LR_ALTKEY)
    			edgeloop_select(eed, eed->f & SELECT);
		}

		/* frontbuffer draw of last selected only */
		unified_select_draw(NULL, eed, NULL);
		
		EM_selectmode_flush();
		countall();
		
		allqueue(REDRAWVIEW3D, 0);
	}
}


/* here actual select happens */
void mouse_mesh(void)
{
	EditVert *eve;
	EditEdge *eed;
	EditFace *efa;
	
	if(G.qual & LR_ALTKEY) mouse_mesh_loop();
	else if(unified_findnearest(&eve, &eed, &efa)) {
		
		if((G.qual & LR_SHIFTKEY)==0) EM_clear_flag_all(SELECT);
		
		if(efa) {
			
			if( (efa->f & SELECT)==0 ) {
				EM_select_face_fgon(efa, 1);
			}
			else if(G.qual & LR_SHIFTKEY) {
				EM_select_face_fgon(efa, 0);
			}
		}
		else if(eed) {
			if((eed->f & SELECT)==0) {
				EM_select_edge(eed, 1);
			}
			else if(G.qual & LR_SHIFTKEY) {
				EM_select_edge(eed, 0);
			}
		}
		else if(eve) {
			if((eve->f & SELECT)==0) eve->f |= SELECT;
			else if(G.qual & LR_SHIFTKEY) eve->f &= ~SELECT;
		}
		
		/* frontbuffer draw of last selected only */
		unified_select_draw(eve, eed, efa);
	
		EM_selectmode_flush();
		countall();

		allqueue(REDRAWVIEW3D, 0);
	}

	rightmouse_transform();
}


static void selectconnectedAll(void)
{
	EditMesh *em = G.editMesh;
	EditVert *v1,*v2;
	EditEdge *eed;
	short done=1, toggle=0;

	if(em->edges.first==0) return;
	
	while(done==1) {
		done= 0;
		
		toggle++;
		if(toggle & 1) eed= em->edges.first;
		else eed= em->edges.last;
		
		while(eed) {
			v1= eed->v1;
			v2= eed->v2;
			if(eed->h==0) {
				if(v1->f & SELECT) {
					if( (v2->f & SELECT)==0 ) {
						v2->f |= SELECT;
						done= 1;
					}
				}
				else if(v2->f & SELECT) {
					if( (v1->f & SELECT)==0 ) {
						v1->f |= SELECT;
						done= 1;
					}
				}
			}
			if(toggle & 1) eed= eed->next;
			else eed= eed->prev;
		}
	}

	/* now use vertex select flag to select rest */
	EM_select_flush();
	
	countall();

	allqueue(REDRAWVIEW3D, 0);
	BIF_undo_push("Select Connected (All)");
}

void selectconnected_mesh(int qual)
{
	EditMesh *em = G.editMesh;
	EditVert *eve, *v1, *v2;
	EditEdge *eed;
	EditFace *efa;
	short done=1, sel, toggle=0;

	if(em->edges.first==0) return;

	if(qual & LR_CTRLKEY) {
		selectconnectedAll();
		return;
	}

	
	if( unified_findnearest(&eve, &eed, &efa)==0 ) {
		error("Nothing indicated ");
		return;
	}
	
	sel= 1;
	if(qual & LR_SHIFTKEY) sel=0;

	/* clear test flags */
	for(v1= em->verts.first; v1; v1= v1->next) v1->f1= 0;
	
	/* start vertex/face/edge */
	if(eve) eve->f1= 1;
	else if(eed) eed->v1->f1= eed->v2->f1= 1;
	else efa->v1->f1= efa->v2->f1= efa->v3->f1= 1;
	
	/* set flag f1 if affected */
	while(done==1) {
		done= 0;
		toggle++;
		
		if(toggle & 1) eed= em->edges.first;
		else eed= em->edges.last;
		
		while(eed) {
			v1= eed->v1;
			v2= eed->v2;
			
			if(eed->h==0) {
				if(v1->f1 && v2->f1==0) {
					v2->f1= 1;
					done= 1;
				}
				else if(v1->f1==0 && v2->f1) {
					v1->f1= 1;
					done= 1;
				}
			}
			
			if(toggle & 1) eed= eed->next;
			else eed= eed->prev;
		}
	}
	
	/* now use vertex f1 flag to select/deselect */
	for(eed= em->edges.first; eed; eed= eed->next) {
		if(eed->v1->f1 && eed->v2->f1) 
			EM_select_edge(eed, sel);
	}
	for(efa= em->faces.first; efa; efa= efa->next) {
		if(efa->v1->f1 && efa->v2->f1 && efa->v3->f1 && (efa->v4==NULL || efa->v4->f1)) 
			EM_select_face(efa, sel);
	}
	/* no flush needed, connected geometry is done */
	
	countall();
	
	allqueue(REDRAWVIEW3D, 0);
	BIF_undo_push("Select Linked");
	
}

/* swap is 0 or 1, if 1 it hides not selected */
void hide_mesh(int swap)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;
	EditFace *efa;
	int a;
	
	if(G.obedit==0) return;

	/* hide happens on least dominant select mode, and flushes up, not down! (helps preventing errors in subsurf) */
	/*  - vertex hidden, always means edge is hidden too
		- edge hidden, always means face is hidden too
		- face hidden, only set face hide
		- then only flush back down what's absolute hidden
	*/
	if(G.scene->selectmode & SCE_SELECT_VERTEX) {
		for(eve= em->verts.first; eve; eve= eve->next) {
			if((eve->f & SELECT)!=swap) {
				eve->f &= ~SELECT;
				eve->h= 1;
			}
		}
	
		for(eed= em->edges.first; eed; eed= eed->next) {
			if(eed->v1->h || eed->v2->h) {
				eed->h |= 1;
				eed->f &= ~SELECT;
			}
		}
	
		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->e1->h || efa->e2->h || efa->e3->h || (efa->e4 && efa->e4->h)) {
				efa->h= 1;
				efa->f &= ~SELECT;
			}
		}
	}
	else if(G.scene->selectmode & SCE_SELECT_EDGE) {

		for(eed= em->edges.first; eed; eed= eed->next) {
			if((eed->f & SELECT)!=swap) {
				eed->h |= 1;
				EM_select_edge(eed, 0);
			}
		}

		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->e1->h || efa->e2->h || efa->e3->h || (efa->e4 && efa->e4->h)) {
				efa->h= 1;
				efa->f &= ~SELECT;
			}
		}
	}
	else {

		for(efa= em->faces.first; efa; efa= efa->next) {
			if((efa->f & SELECT)!=swap) {
				efa->h= 1;
				EM_select_face(efa, 0);
			}
		}
	}
	
	/* flush down, only whats 100% hidden */
	for(eve= em->verts.first; eve; eve= eve->next) eve->f1= 0;
	for(eed= em->edges.first; eed; eed= eed->next) eed->f1= 0;
	
	if(G.scene->selectmode & SCE_SELECT_FACE) {
		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->h) a= 1; else a= 2;
			efa->e1->f1 |= a;
			efa->e2->f1 |= a;
			efa->e3->f1 |= a;
			if(efa->e4) efa->e4->f1 |= a;
		}
	}
	
	if(G.scene->selectmode >= SCE_SELECT_EDGE) {
		for(eed= em->edges.first; eed; eed= eed->next) {
			if(eed->f1==1) eed->h |= 1;
			if(eed->h & 1) a= 1; else a= 2;
			eed->v1->f1 |= a;
			eed->v2->f1 |= a;
		}
	}

	if(G.scene->selectmode >= SCE_SELECT_VERTEX) {
		for(eve= em->verts.first; eve; eve= eve->next) {
			if(eve->f1==1) eve->h= 1;
		}
	}
		
	allqueue(REDRAWVIEW3D, 0);
	DAG_object_flush_update(G.scene, G.obedit, OB_RECALC_DATA);	
	BIF_undo_push("Hide");
}


void reveal_mesh(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;
	EditFace *efa;
	
	if(G.obedit==0) return;

	for(eve= em->verts.first; eve; eve= eve->next) {
		if(eve->h) {
			eve->h= 0;
			eve->f |= SELECT;
		}
	}
	for(eed= em->edges.first; eed; eed= eed->next) {
		if(eed->h & 1) {
			eed->h &= ~1;
			if(G.scene->selectmode & SCE_SELECT_VERTEX); 
			else EM_select_edge(eed, 1);
		}
	}
	for(efa= em->faces.first; efa; efa= efa->next) {
		if(efa->h) {
			efa->h= 0;
			if(G.scene->selectmode & (SCE_SELECT_EDGE|SCE_SELECT_VERTEX)); 
			else EM_select_face(efa, 1);
		}
	}

	EM_fgon_flags();	// redo flags and indices for fgons
	EM_selectmode_flush();
	countall();

	allqueue(REDRAWVIEW3D, 0);
	DAG_object_flush_update(G.scene, G.obedit, OB_RECALC_DATA);	
	BIF_undo_push("Reveal");
}

void select_faces_by_numverts(int numverts)
{
	EditMesh *em = G.editMesh;
	EditFace *efa;

	/* Selects isolated verts, and edges that do not have 2 neighboring
	 * faces
	 */
	
	if(G.scene->selectmode!=SCE_SELECT_FACE) {
		error("Only works in face selection mode");
		return;
	}

	efa= em->faces.first;
	while(efa) {
		if (efa->e4) {
			EM_select_face(efa, (numverts==4) );
		}
		else if (efa->e3) {
			EM_select_face(efa, (numverts==3) );
		}
		else 
			EM_select_face(efa, (numverts!=3) && (numverts!=4) );
		efa= efa->next;
	}

	countall();
	addqueue(curarea->win,  REDRAW, 0);

	if (numverts==3)
		BIF_undo_push("Select Triangles");
	else if (numverts==4)
		BIF_undo_push("Select Quads");
	else
		BIF_undo_push("Select non-Triangles/Quads");
}

void select_sharp_edges(void)
{
	/* Find edges that have exactly two neighboring faces,
	 * check the angle between those faces, and if angle is
	 * small enough, select the edge
	 */
	EditMesh *em = G.editMesh;
	EditEdge *eed;
	EditFace *efa;
	EditFace **efa1;
	EditFace **efa2;
	long edgecount = 0, i;
	static short sharpness = 135;
	float fsharpness;

	if(G.scene->selectmode==SCE_SELECT_FACE) {
		error("Doesn't work in face selection mode");
		return;
	}

	if(button(&sharpness,0, 180,"Max Angle:")==0) return;
	/* if faces are at angle 'sharpness', then the face normals
	 * are at angle 180.0 - 'sharpness' (convert to radians too)
	 */
	fsharpness = ((180.0 - sharpness) * M_PI) / 180.0;

	i=0;
	/* count edges, use tmp.l  */
	eed= em->edges.first;
	while(eed) {
		edgecount++;
		eed->tmp.l = i;
		eed= eed->next;
		++i;
	}

	/* for each edge, we want a pointer to two adjacent faces */
	efa1 = MEM_callocN(edgecount*sizeof(EditFace *), 
					   "pairs of edit face pointers");
	efa2 = MEM_callocN(edgecount*sizeof(EditFace *), 
					   "pairs of edit face pointers");

#define face_table_edge(eed) { \
		i = eed->tmp.l; \
		if (i != -1) { \
			if (efa1[i]) { \
				if (efa2[i]) { \
					/* invalidate, edge has more than two neighbors */ \
					eed->tmp.l = -1; \
				} \
				else { \
					efa2[i] = efa; \
				} \
			} \
			else { \
				efa1[i] = efa; \
			} \
		} \
	}

	/* find the adjacent faces of each edge, we want only two */
	efa= em->faces.first;
	while(efa) {
		face_table_edge(efa->e1);
		face_table_edge(efa->e2);
		face_table_edge(efa->e3);
		if (efa->e4) {
			face_table_edge(efa->e4);
		}
		efa= efa->next;
	}

#undef face_table_edge

	eed = em->edges.first;
	while(eed) {
		i = eed->tmp.l;
		if (i != -1) { 
			/* edge has two or less neighboring faces */
			if ( (efa1[i]) && (efa2[i]) ) { 
				/* edge has exactly two neighboring faces, check angle */
				float angle;
				angle = saacos(efa1[i]->n[0]*efa2[i]->n[0] +
							   efa1[i]->n[1]*efa2[i]->n[1] +
							   efa1[i]->n[2]*efa2[i]->n[2]);
				if (fabs(angle) >= fsharpness)
					EM_select_edge(eed, 1);
			}
		}

		eed= eed->next;
	}

	MEM_freeN(efa1);
	MEM_freeN(efa2);

	countall();
	addqueue(curarea->win,  REDRAW, 0);
	BIF_undo_push("Select Sharp Edges");
}

void select_linked_flat_faces(void)
{
	/* Find faces that are linked to selected faces that are 
	 * relatively flat (angle between faces is higher than
	 * specified angle)
	 */
	EditMesh *em = G.editMesh;
	EditEdge *eed;
	EditFace *efa;
	EditFace **efa1;
	EditFace **efa2;
	long edgecount = 0, i, faceselcount=0, faceselcountold=0;
	static short sharpness = 135;
	float fsharpness;

	if(G.scene->selectmode!=SCE_SELECT_FACE) {
		error("Only works in face selection mode");
		return;
	}

	if(button(&sharpness,0, 180,"Min Angle:")==0) return;
	/* if faces are at angle 'sharpness', then the face normals
	 * are at angle 180.0 - 'sharpness' (convert to radians too)
	 */
	fsharpness = ((180.0 - sharpness) * M_PI) / 180.0;

	i=0;
	/* count edges, use tmp.l */
	eed= em->edges.first;
	while(eed) {
		edgecount++;
		eed->tmp.l = i;
		eed= eed->next;
		++i;
	}

	/* for each edge, we want a pointer to two adjacent faces */
	efa1 = MEM_callocN(edgecount*sizeof(EditFace *), 
					   "pairs of edit face pointers");
	efa2 = MEM_callocN(edgecount*sizeof(EditFace *), 
					   "pairs of edit face pointers");

#define face_table_edge(eed) { \
		i = eed->tmp.l; \
		if (i != -1) { \
			if (efa1[i]) { \
				if (efa2[i]) { \
					/* invalidate, edge has more than two neighbors */ \
					eed->tmp.l = -1; \
				} \
				else { \
					efa2[i] = efa; \
				} \
			} \
			else { \
				efa1[i] = efa; \
			} \
		} \
	}

	/* find the adjacent faces of each edge, we want only two */
	efa= em->faces.first;
	while(efa) {
		face_table_edge(efa->e1);
		face_table_edge(efa->e2);
		face_table_edge(efa->e3);
		if (efa->e4) {
			face_table_edge(efa->e4);
		}

		/* while were at it, count the selected faces */
		if (efa->f & SELECT) ++faceselcount;

		efa= efa->next;
	}

#undef face_table_edge

	eed= em->edges.first;
	while(eed) {
		i = eed->tmp.l;
		if (i != -1) { 
			/* edge has two or less neighboring faces */
			if ( (efa1[i]) && (efa2[i]) ) { 
				/* edge has exactly two neighboring faces, check angle */
				float angle;
				angle = saacos(efa1[i]->n[0]*efa2[i]->n[0] +
							   efa1[i]->n[1]*efa2[i]->n[1] +
							   efa1[i]->n[2]*efa2[i]->n[2]);
				/* invalidate: edge too sharp */
				if (fabs(angle) >= fsharpness)
					eed->tmp.l = -1;
			}
			else {
				/* invalidate: less than two neighbors */
				eed->tmp.l = -1;
			}
		}

		eed= eed->next;
	}

#define select_flat_neighbor(eed) { \
				i = eed->tmp.l; \
				if (i!=-1) { \
					if (! (efa1[i]->f & SELECT) ) { \
						EM_select_face(efa1[i], 1); \
						++faceselcount; \
					} \
					if (! (efa2[i]->f & SELECT) ) { \
						EM_select_face(efa2[i], 1); \
						++faceselcount; \
					} \
				} \
	}

	while (faceselcount != faceselcountold) {
		faceselcountold = faceselcount;

		efa= em->faces.first;
		while(efa) {
			if (efa->f & SELECT) {
				select_flat_neighbor(efa->e1);
				select_flat_neighbor(efa->e2);
				select_flat_neighbor(efa->e3);
				if (efa->e4) {
					select_flat_neighbor(efa->e4);
				}
			}
			efa= efa->next;
		}
	}

#undef select_flat_neighbor

	MEM_freeN(efa1);
	MEM_freeN(efa2);

	countall();
	addqueue(curarea->win,  REDRAW, 0);
	BIF_undo_push("Select Linked Flat Faces");
}

void select_non_manifold(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;
	EditFace *efa;

	/* Selects isolated verts, and edges that do not have 2 neighboring
	 * faces
	 */
	
	if(G.scene->selectmode==SCE_SELECT_FACE) {
		error("Doesn't work in face selection mode");
		return;
	}

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

	efa= em->faces.first;
	while(efa) {
		/* increase face count for edges */
		++efa->e1->f1;
		++efa->e2->f1;
		++efa->e3->f1;
		if (efa->e4)
			++efa->e4->f1;			
		efa= efa->next;
	}

	/* select verts that are attached to an edge that does not
	 * have 2 neighboring faces */
	eed= em->edges.first;
	while(eed) {
		if (eed->h==0 && eed->f1 != 2) {
			EM_select_edge(eed, 1);
		}
		eed= eed->next;
	}

	/* select isolated verts */
	eve= em->verts.first;
	while(eve) {
		if (eve->f1 == 0) {
			if (!eve->h) eve->f |= SELECT;
		}
		eve= eve->next;
	}

	countall();
	addqueue(curarea->win,  REDRAW, 0);
	BIF_undo_push("Select Non Manifold");
}

void selectswap_mesh(void) /* UI level */
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;
	EditFace *efa;
	
	if(G.scene->selectmode & SCE_SELECT_VERTEX) {

		for(eve= em->verts.first; eve; eve= eve->next) {
			if(eve->h==0) {
				if(eve->f & SELECT) eve->f &= ~SELECT;
				else eve->f|= SELECT;
			}
		}
	}
	else if(G.scene->selectmode & SCE_SELECT_EDGE) {
		for(eed= em->edges.first; eed; eed= eed->next) {
			if(eed->h==0) {
				EM_select_edge(eed, !(eed->f & SELECT));
			}
		}
	}
	else {
		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->h==0) {
				EM_select_face(efa, !(efa->f & SELECT));
			}
		}
	}

	EM_selectmode_flush();
	
	countall();
	allqueue(REDRAWVIEW3D, 0);

	BIF_undo_push("Select Swap");
	
}

void deselectall_mesh(void)	 /* this toggles!!!, UI level */
{
	
	if(G.obedit->lay & G.vd->lay) {

		if( EM_nvertices_selected() ) {
			EM_clear_flag_all(SELECT);
			BIF_undo_push("Deselect All");
		}
		else  {
			EM_set_flag_all(SELECT);
			BIF_undo_push("Select All");
		}
		
		countall();
		allqueue(REDRAWVIEW3D, 0);
	}
}

void select_more(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;
	EditFace *efa;
	
	for(eve= em->verts.first; eve; eve= eve->next) {
		if(eve->f & SELECT) eve->f1= 1;
		else eve->f1 = 0;
	}
	
	/* set f1 flags in vertices to select 'more' */
	for(eed= em->edges.first; eed; eed= eed->next) {
		if(eed->h==0) {
			if (eed->v1->f & SELECT)
				eed->v2->f1 = 1;
			if (eed->v2->f & SELECT)
				eed->v1->f1 = 1;
		}
	}

	/* new selected edges, but not in facemode */
	if(G.scene->selectmode <= SCE_SELECT_EDGE) {
		
		for(eed= em->edges.first; eed; eed= eed->next) {
			if(eed->h==0) {
				if(eed->v1->f1 && eed->v2->f1) EM_select_edge(eed, 1);
			}
		}
	}
	/* new selected faces */
	for(efa= em->faces.first; efa; efa= efa->next) {
		if(efa->h==0) {
			if(efa->v1->f1 && efa->v2->f1 && efa->v3->f1 && (efa->v4==NULL || efa->v4->f1)) 
				EM_select_face(efa, 1);
		}
	}

	countall();
	addqueue(curarea->win,  REDRAW, 0);
	BIF_undo_push("Select More");
}

void select_less(void)
{
	EditMesh *em = G.editMesh;
	EditEdge *eed;
	EditFace *efa;

	if(G.scene->selectmode <= SCE_SELECT_EDGE) {
		/* eed->f1 == 1:  edge with a selected and deselected vert */ 

		for(eed= em->edges.first; eed; eed= eed->next) {
			eed->f1= 0;
			if(eed->h==0) {
				
				if ( !(eed->v1->f & SELECT) && (eed->v2->f & SELECT) ) 
					eed->f1= 1;
				if ( (eed->v1->f & SELECT) && !(eed->v2->f & SELECT) ) 
					eed->f1= 1;
			}
		}
		
		/* deselect edges with flag set */
		for(eed= em->edges.first; eed; eed= eed->next) {
			if (eed->h==0 && eed->f1 == 1) {
				EM_select_edge(eed, 0);
			}
		}
		EM_deselect_flush();
		
	}
	else {
		/* deselect faces with 1 or more deselect edges */
		/* eed->f1 == mixed selection edge */
		for(eed= em->edges.first; eed; eed= eed->next) eed->f1= 0;

		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->h==0) {
				if(efa->f & SELECT) {
					efa->e1->f1 |= 1;
					efa->e2->f1 |= 1;
					efa->e3->f1 |= 1;
					if(efa->e4) efa->e4->f1 |= 1;
				}
				else {
					efa->e1->f1 |= 2;
					efa->e2->f1 |= 2;
					efa->e3->f1 |= 2;
					if(efa->e4) efa->e4->f1 |= 2;
				}
			}
		}
		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->h==0) {
				if(efa->e1->f1==3 || efa->e2->f1==3 || efa->e3->f1==3 || (efa->e4 && efa->e4->f1==3)) { 
					EM_select_face(efa, 0);
				}
			}
		}
		EM_selectmode_flush();
		
	}
	
	countall();
	allqueue(REDRAWVIEW3D, 0);
}


void selectrandom_mesh(void) /* randomly selects a user-set % of vertices/edges/faces */
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;
	EditFace *efa;
	short randfac = 50;

	if(G.obedit==NULL || (G.obedit->lay & G.vd->lay)==0) return;

	/* Get the percentage of vertices to randomly select as 'randfac' */
	if(button(&randfac,0, 100,"Percentage:")==0) return;

	BLI_srand( BLI_rand() ); /* random seed */
	
	if(G.scene->selectmode & SCE_SELECT_VERTEX) {
		for(eve= em->verts.first; eve; eve= eve->next) {
			if(eve->h==0) {
				if ( (BLI_frand() * 100) < randfac) 
					eve->f |= SELECT;
			}
		}
	}
	else if(G.scene->selectmode & SCE_SELECT_EDGE) {
		for(eed= em->edges.first; eed; eed= eed->next) {
			if(eed->h==0) {
				if ( (BLI_frand() * 100) < randfac) 
					EM_select_edge(eed, 1);
			}
		}
	}
	else {
		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->h==0) {
				if ( (BLI_frand() * 100) < randfac) 
					EM_select_face(efa, 1);
			}
		}
	}
	
	EM_selectmode_flush();

	countall();
	allqueue(REDRAWVIEW3D, 0);
}

void editmesh_select_by_material(int index) 
{
	EditMesh *em = G.editMesh;
	EditFace *efa;
	
	for (efa=em->faces.first; efa; efa= efa->next) {
		if (efa->mat_nr==index) {
			EM_select_face(efa, 1);
		}
	}

	EM_selectmode_flush();
}

void editmesh_deselect_by_material(int index) 
{
	EditMesh *em = G.editMesh;
	EditFace *efa;
	
	for (efa=em->faces.first; efa; efa= efa->next) {
		if (efa->mat_nr==index) {
			EM_select_face(efa, 0);
		}
	}

	EM_selectmode_flush();
}

void EM_selectmode_menu(void)
{
	int val;
	
	if(G.scene->selectmode & SCE_SELECT_VERTEX) pupmenu_set_active(1);
	else if(G.scene->selectmode & SCE_SELECT_EDGE) pupmenu_set_active(2);
	else pupmenu_set_active(3);
	
	val= pupmenu("Select Mode%t|Vertices|Edges|Faces");
	if(val>0) {
		if(val==1) G.scene->selectmode= SCE_SELECT_VERTEX;
		else if(val==2) G.scene->selectmode= SCE_SELECT_EDGE;
		else G.scene->selectmode= SCE_SELECT_FACE;
	
		EM_selectmode_set(); // when mode changes
		allqueue(REDRAWVIEW3D, 1);
	}
}

/* ************************* SEAMS AND EDGES **************** */

void editmesh_mark_seam(int clear)
{
	EditMesh *em= G.editMesh;
	EditEdge *eed;

	/* auto-enable seams drawing */
	if(clear==0) {
		if(!(G.f & G_DRAWSEAMS)) {
			G.f |= G_DRAWSEAMS;
			allqueue(REDRAWBUTSEDIT, 0);
		}
	}

	if(clear) {
		eed= em->edges.first;
		while(eed) {
			if((eed->h==0) && (eed->f & SELECT)) {
				eed->seam = 0;
			}
			eed= eed->next;
		}
		BIF_undo_push("Mark Seam");
	}
	else {
		eed= em->edges.first;
		while(eed) {
			if((eed->h==0) && (eed->f & SELECT)) {
				eed->seam = 1;
			}
			eed= eed->next;
		}
		BIF_undo_push("Clear Seam");
	}

	allqueue(REDRAWVIEW3D, 0);
}

void Edge_Menu() {
	short ret;

	ret= pupmenu("Edge Specials%t|Mark Seam %x1|Clear Seam %x2|Rotate Edge CW%x3|Rotate Edge CCW%x4|Loopcut%x6|Edge Slide%x5");

	switch(ret)
	{
	case 1:
		editmesh_mark_seam(0);
		break;
	case 2:
		editmesh_mark_seam(1);
		break;
	case 3:
		edge_rotate_selected(2);
		break;
	case 4:
		edge_rotate_selected(1);
		break;
	case 5:
		EdgeSlide(0,0.0);
    		BIF_undo_push("EdgeSlide");
		break;
	case 6:
        	CutEdgeloop(1);
		BIF_undo_push("Loopcut New");
		break;
	}
}


/* **************** NORMALS ************** */

void righthandfaces(int select)	/* makes faces righthand turning */
{
	EditMesh *em = G.editMesh;
	EditEdge *eed, *ed1, *ed2, *ed3, *ed4;
	EditFace *efa, *startvl;
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
		eed->f2= 0;		// edge direction
		eed->f1= 0;		// counter
		eed= eed->next;
	}

	/* count faces and edges */
	totsel= 0;
	efa= em->faces.first;
	while(efa) {
		if(select==0 || (efa->f & SELECT) ) {
			efa->f1= 1;
			totsel++;
			efa->e1->f1++;
			efa->e2->f1++;
			efa->e3->f1++;
			if(efa->v4) efa->e4->f1++;
		}
		else efa->f1= 0;

		efa= efa->next;
	}

	while(totsel>0) {
		/* from the outside to the inside */

		efa= em->faces.first;
		startvl= NULL;
		maxx= -1.0e10;
		tria_nr= 0;

		while(efa) {
			if(efa->f1) {
				CalcCent3f(cent, efa->v1->co, efa->v2->co, efa->v3->co);
				cent[0]= cent[0]*cent[0] + cent[1]*cent[1] + cent[2]*cent[2];
				
				if(cent[0]>maxx) {
					maxx= cent[0];
					startvl= efa;
					tria_nr= 0;
				}
				if(efa->v4) {
					CalcCent3f(cent, efa->v1->co, efa->v3->co, efa->v4->co);
					cent[0]= cent[0]*cent[0] + cent[1]*cent[1] + cent[2]*cent[2];
					
					if(cent[0]>maxx) {
						maxx= cent[0];
						startvl= efa;
						tria_nr= 1;
					}
				}
			}
			efa= efa->next;
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
				if(cent[0]*nor[0]+cent[1]*nor[1]+cent[2]*nor[2] > 0.0) flipface(startvl);
			}
			else {
				if(cent[0]*nor[0]+cent[1]*nor[1]+cent[2]*nor[2] < 0.0) flipface(startvl);
			}
		}
		else if(cent[0]*nor[0]+cent[1]*nor[1]+cent[2]*nor[2] < 0.0) flipface(startvl);


		eed= startvl->e1;
		if(eed->v1==startvl->v1) eed->f2= 1; 
		else eed->f2= 2;
		
		eed= startvl->e2;
		if(eed->v1==startvl->v2) eed->f2= 1; 
		else eed->f2= 2;
		
		eed= startvl->e3;
		if(eed->v1==startvl->v3) eed->f2= 1; 
		else eed->f2= 2;
		
		eed= startvl->e4;
		if(eed) {
			if(eed->v1==startvl->v4) eed->f2= 1; 
			else eed->f2= 2;
		}
		
		startvl->f1= 0;
		totsel--;

		/* test normals */
		found= 1;
		direct= 1;
		while(found) {
			found= 0;
			if(direct) efa= em->faces.first;
			else efa= em->faces.last;
			while(efa) {
				if(efa->f1) {
					turn= 0;
					foundone= 0;

					ed1= efa->e1;
					ed2= efa->e2;
					ed3= efa->e3;
					ed4= efa->e4;

					if(ed1->f2) {
						if(ed1->v1==efa->v1 && ed1->f2==1) turn= 1;
						if(ed1->v2==efa->v1 && ed1->f2==2) turn= 1;
						foundone= 1;
					}
					else if(ed2->f2) {
						if(ed2->v1==efa->v2 && ed2->f2==1) turn= 1;
						if(ed2->v2==efa->v2 && ed2->f2==2) turn= 1;
						foundone= 1;
					}
					else if(ed3->f2) {
						if(ed3->v1==efa->v3 && ed3->f2==1) turn= 1;
						if(ed3->v2==efa->v3 && ed3->f2==2) turn= 1;
						foundone= 1;
					}
					else if(ed4 && ed4->f2) {
						if(ed4->v1==efa->v4 && ed4->f2==1) turn= 1;
						if(ed4->v2==efa->v4 && ed4->f2==2) turn= 1;
						foundone= 1;
					}

					if(foundone) {
						found= 1;
						totsel--;
						efa->f1= 0;

						if(turn) {
							if(ed1->v1==efa->v1) ed1->f2= 2; 
							else ed1->f2= 1;
							if(ed2->v1==efa->v2) ed2->f2= 2; 
							else ed2->f2= 1;
							if(ed3->v1==efa->v3) ed3->f2= 2; 
							else ed3->f2= 1;
							if(ed4) {
								if(ed4->v1==efa->v4) ed4->f2= 2; 
								else ed4->f2= 1;
							}

							flipface(efa);

						}
						else {
							if(ed1->v1== efa->v1) ed1->f2= 1; 
							else ed1->f2= 2;
							if(ed2->v1==efa->v2) ed2->f2= 1; 
							else ed2->f2= 2;
							if(ed3->v1==efa->v3) ed3->f2= 1; 
							else ed3->f2= 2;
							if(ed4) {
								if(ed4->v1==efa->v4) ed4->f2= 1; 
								else ed4->f2= 2;
							}
						}
					}
				}
				if(direct) efa= efa->next;
				else efa= efa->prev;
			}
			direct= 1-direct;
		}
	}

	recalc_editnormals();
	
	DAG_object_flush_update(G.scene, G.obedit, OB_RECALC_DATA);
	
	waitcursor(0);
}


/* ********** ALIGN WITH VIEW **************** */


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

	for (i=0; i<me->totface; i++)
		if (tface_is_selected(&me->tface[i]))
			count++;

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
	
			if (tface_is_selected(tf)) {
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
	int nselverts= EM_nvertices_selected();
	float norm[3]={0.0, 0.0, 0.0}; /* used for storing the mesh normal */
	
	if (nselverts==0) {
		error("No faces or vertices selected.");
	} else if (EM_nfaces_selected()) {
		EditFace *efa;
		for (efa= em->faces.first; efa; efa= efa->next) {
			if (faceselectedAND(efa, SELECT)) {
				float fno[3];
				if (efa->v4) CalcNormFloat4(efa->v1->co, efa->v2->co, efa->v3->co, efa->v4->co, fno);
				else CalcNormFloat(efa->v1->co, efa->v2->co, efa->v3->co, fno);
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
	} else if (nselverts>2) {
		float cent[3];
		EditVert *eve, *leve= NULL;

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
	} else if (nselverts==2) { /* Align view to edge (or 2 verts) */ 
		EditVert *eve, *leve= NULL;

		for (eve= em->verts.first; eve; eve= eve->next) {
			if (eve->f & SELECT) {
				if (leve) {
					norm[0]= leve->co[0] - eve->co[0];
					norm[1]= leve->co[1] - eve->co[1];
					norm[2]= leve->co[2] - eve->co[2];
					break; /* we know there are only 2 verts so no need to keep looking */
				}
				leve= eve;
			}
		}
		Mat4Mul3Vecfl(G.obedit->obmat, norm);
		view3d_align_axis_to_vector(v3d, axis, norm);
	} else if (nselverts==1) { /* Align view to vert normal */ 
		EditVert *eve;

		for (eve= em->verts.first; eve; eve= eve->next) {
			if (eve->f & SELECT) {
				norm[0]= eve->no[0];
				norm[1]= eve->no[1];
				norm[2]= eve->no[2];
				break; /* we know this is the only selected vert, so no need to keep looking */
			}
		}
		Mat4Mul3Vecfl(G.obedit->obmat, norm);
		view3d_align_axis_to_vector(v3d, axis, norm);
	}
} 

/* **************** VERTEX DEFORMS *************** */

void vertexsmooth(void)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;
	float *adror, *adr, fac;
	float fvec[3];
	int teller=0;
	ModifierData *md= G.obedit->modifiers.first;

	if(G.obedit==0) return;

	/* count */
	eve= em->verts.first;
	while(eve) {
		if(eve->f & SELECT) teller++;
		eve= eve->next;
	}
	if(teller==0) return;
	
	adr=adror= (float *)MEM_callocN(3*sizeof(float *)*teller, "vertsmooth");
	eve= em->verts.first;
	while(eve) {
		if(eve->f & SELECT) {
			eve->tmp.fp = adr;
			eve->f1= 0;
			eve->f2= 0;
			adr+= 3;
		}
		eve= eve->next;
	}

	/* if there is a mirror modifier with clipping, flag the verts that
	 * are within tolerance of the plane(s) of reflection 
	 */
	for (; md; md=md->next) {
		if (md->type==eModifierType_Mirror) {
			MirrorModifierData *mmd = (MirrorModifierData*) md;	
		
			if(mmd->flag & MOD_MIR_CLIPPING) {
				for (eve= em->verts.first; eve; eve= eve->next) {
					if(eve->f & SELECT) {

						switch(mmd->axis){
							case 0:
								if (fabs(eve->co[0]) < mmd->tolerance)
									eve->f2 |= 1;
								break;
							case 1:
								if (fabs(eve->co[1]) < mmd->tolerance)
									eve->f2 |= 2;
								break;
							case 2:
								if (fabs(eve->co[2]) < mmd->tolerance)
									eve->f2 |= 4;
								break;
						}
					}
				}
			}
		}
	}
	
	eed= em->edges.first;
	while(eed) {
		if( (eed->v1->f & SELECT) || (eed->v2->f & SELECT) ) {
			fvec[0]= (eed->v1->co[0]+eed->v2->co[0])/2.0;
			fvec[1]= (eed->v1->co[1]+eed->v2->co[1])/2.0;
			fvec[2]= (eed->v1->co[2]+eed->v2->co[2])/2.0;
			
			if((eed->v1->f & SELECT) && eed->v1->f1<255) {
				eed->v1->f1++;
				VecAddf(eed->v1->tmp.fp, eed->v1->tmp.fp, fvec);
			}
			if((eed->v2->f & SELECT) && eed->v2->f1<255) {
				eed->v2->f1++;
				VecAddf(eed->v2->tmp.fp, eed->v2->tmp.fp, fvec);
			}
		}
		eed= eed->next;
	}

	eve= em->verts.first;
	while(eve) {
		if(eve->f & SELECT) {
			if(eve->f1) {
				adr = eve->tmp.fp;
				fac= 0.5/(float)eve->f1;
				
				eve->co[0]= 0.5*eve->co[0]+fac*adr[0];
				eve->co[1]= 0.5*eve->co[1]+fac*adr[1];
				eve->co[2]= 0.5*eve->co[2]+fac*adr[2];

				/* clip if needed by mirror modifier */
				if (eve->f2) {
					if (eve->f2 & 1) {
						eve->co[0]= 0.0f;
					}
					if (eve->f2 & 2) {
						eve->co[1]= 0.0f;
					}
					if (eve->f2 & 4) {
						eve->co[2]= 0.0f;
					}
				}
			}
			eve->tmp.fp= 0;
		}
		eve= eve->next;
	}
	MEM_freeN(adror);

	recalc_editnormals();

	allqueue(REDRAWVIEW3D, 0);
	DAG_object_flush_update(G.scene, G.obedit, OB_RECALC_DATA);
	BIF_undo_push("Vertex Smooth");
}

void vertexnoise(void)
{
	EditMesh *em = G.editMesh;
	Material *ma;
	Tex *tex;
	EditVert *eve;
	float b2, ofs, vec[3];

	if(G.obedit==0) return;
	
	ma= give_current_material(G.obedit, G.obedit->actcol);
	if(ma==0 || ma->mtex[0]==0 || ma->mtex[0]->tex==0) {
		return;
	}
	tex= ma->mtex[0]->tex;
	
	ofs= tex->turbul/200.0;
	
	eve= (struct EditVert *)em->verts.first;
	while(eve) {
		if(eve->f & SELECT) {
			
			if(tex->type==TEX_STUCCI) {
				
				b2= BLI_hnoise(tex->noisesize, eve->co[0], eve->co[1], eve->co[2]);
				if(tex->stype) ofs*=(b2*b2);
				vec[0]= 0.2*(b2-BLI_hnoise(tex->noisesize, eve->co[0]+ofs, eve->co[1], eve->co[2]));
				vec[1]= 0.2*(b2-BLI_hnoise(tex->noisesize, eve->co[0], eve->co[1]+ofs, eve->co[2]));
				vec[2]= 0.2*(b2-BLI_hnoise(tex->noisesize, eve->co[0], eve->co[1], eve->co[2]+ofs));
				
				VecAddf(eve->co, eve->co, vec);
			}
			else {
				float tin, dum;
				externtex(ma->mtex[0], eve->co, &tin, &dum, &dum, &dum, &dum);
				eve->co[2]+= 0.05*tin;
			}
		}
		eve= eve->next;
	}

	recalc_editnormals();
	allqueue(REDRAWVIEW3D, 0);
	DAG_object_flush_update(G.scene, G.obedit, OB_RECALC_DATA);
	BIF_undo_push("Vertex Noise");
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
		if(eve->f & SELECT) {
			tot++;
			len+= VecLenf(cent, eve->co);
		}
		eve= eve->next;
	}
	len/=tot;
	
	if(len==0.0) len= 10.0;
	
	eve= em->verts.first;
	while(eve) {
		if(eve->f & SELECT) {
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
	
	recalc_editnormals();
	allqueue(REDRAWVIEW3D, 0);
	DAG_object_flush_update(G.scene, G.obedit, OB_RECALC_DATA);
	BIF_undo_push("To Sphere");
}

