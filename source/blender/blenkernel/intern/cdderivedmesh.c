/*
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
* along with this program; if not, write to the Free Software  Foundation,
* Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
*
* The Original Code is Copyright (C) 2006 Blender Foundation.
* All rights reserved.
*
* The Original Code is: all of this file.
*
* Contributor(s): Ben Batt <benbatt@gmail.com>
*
* ***** END GPL LICENSE BLOCK *****
*
* Implementation of CDDerivedMesh.
*
* BKE_cdderivedmesh.h contains the function prototypes for this file.
*
*/

/** \file blender/blenkernel/intern/cdderivedmesh.c
 *  \ingroup bke
 */
 
#include "GL/glew.h"

#include "BLI_blenlib.h"
#include "BLI_edgehash.h"
#include "BLI_editVert.h"
#include "BLI_math.h"
#include "BLI_pbvh.h"
#include "BLI_utildefines.h"

#include "BKE_cdderivedmesh.h"
#include "BKE_global.h"
#include "BKE_mesh.h"
#include "BKE_paint.h"


#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_curve_types.h" /* for Curve */

#include "MEM_guardedalloc.h"

#include "GPU_buffers.h"
#include "GPU_draw.h"
#include "GPU_extensions.h"
#include "GPU_material.h"

#include <string.h>
#include <limits.h>
#include <math.h>

typedef struct {
	DerivedMesh dm;

	/* these point to data in the DerivedMesh custom data layers,
	   they are only here for efficiency and convenience **/
	MVert *mvert;
	MEdge *medge;
	MFace *mface;

	/* Cached */
	struct PBVH *pbvh;
	int pbvh_draw;

	/* Mesh connectivity */
	struct ListBase *fmap;
	struct IndexNode *fmap_mem;
} CDDerivedMesh;

/**************** DerivedMesh interface functions ****************/
static int cdDM_getNumVerts(DerivedMesh *dm)
{
	return dm->numVertData;
}

static int cdDM_getNumEdges(DerivedMesh *dm)
{
	return dm->numEdgeData;
}

static int cdDM_getNumFaces(DerivedMesh *dm)
{
	return dm->numFaceData;
}

static void cdDM_getVert(DerivedMesh *dm, int index, MVert *vert_r)
{
	CDDerivedMesh *cddm = (CDDerivedMesh *)dm;
	*vert_r = cddm->mvert[index];
}

static void cdDM_getEdge(DerivedMesh *dm, int index, MEdge *edge_r)
{
	CDDerivedMesh *cddm = (CDDerivedMesh *)dm;
	*edge_r = cddm->medge[index];
}

static void cdDM_getFace(DerivedMesh *dm, int index, MFace *face_r)
{
	CDDerivedMesh *cddm = (CDDerivedMesh *)dm;
	*face_r = cddm->mface[index];
}

static void cdDM_copyVertArray(DerivedMesh *dm, MVert *vert_r)
{
	CDDerivedMesh *cddm = (CDDerivedMesh *)dm;
	memcpy(vert_r, cddm->mvert, sizeof(*vert_r) * dm->numVertData);
}

static void cdDM_copyEdgeArray(DerivedMesh *dm, MEdge *edge_r)
{
	CDDerivedMesh *cddm = (CDDerivedMesh *)dm;
	memcpy(edge_r, cddm->medge, sizeof(*edge_r) * dm->numEdgeData);
}

static void cdDM_copyFaceArray(DerivedMesh *dm, MFace *face_r)
{
	CDDerivedMesh *cddm = (CDDerivedMesh *)dm;
	memcpy(face_r, cddm->mface, sizeof(*face_r) * dm->numFaceData);
}

static void cdDM_getMinMax(DerivedMesh *dm, float min_r[3], float max_r[3])
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	int i;

	if (dm->numVertData) {
		for (i=0; i<dm->numVertData; i++) {
			DO_MINMAX(cddm->mvert[i].co, min_r, max_r);
		}
	} else {
		min_r[0] = min_r[1] = min_r[2] = max_r[0] = max_r[1] = max_r[2] = 0.0;
	}
}

static void cdDM_getVertCo(DerivedMesh *dm, int index, float co_r[3])
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;

	VECCOPY(co_r, cddm->mvert[index].co);
}

static void cdDM_getVertCos(DerivedMesh *dm, float (*cos_r)[3])
{
	MVert *mv = CDDM_get_verts(dm);
	int i;

	for(i = 0; i < dm->numVertData; i++, mv++)
		VECCOPY(cos_r[i], mv->co);
}

static void cdDM_getVertNo(DerivedMesh *dm, int index, float no_r[3])
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	normal_short_to_float_v3(no_r, cddm->mvert[index].no);
}

static ListBase *cdDM_getFaceMap(Object *ob, DerivedMesh *dm)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;

	if(!cddm->fmap && ob->type == OB_MESH) {
		Mesh *me= ob->data;

		create_vert_face_map(&cddm->fmap, &cddm->fmap_mem, me->mface,
					 me->totvert, me->totface);
	}

	return cddm->fmap;
}

static int can_pbvh_draw(Object *ob, DerivedMesh *dm)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	Mesh *me= ob->data;
	int deformed= 0;

	/* active modifiers means extra deformation, which can't be handled correct
	   on bith of PBVH and sculpt "layer" levels, so use PBVH only for internal brush
	   stuff and show final DerivedMesh so user would see actual object shape */
	deformed|= ob->sculpt->modifiers_active;

	/* as in case with modifiers, we can't synchronize deformation made against
	   PBVH and non-locked keyblock, so also use PBVH only for brushes and
	   final DM to give final result to user */
	deformed|= ob->sculpt->kb && (ob->shapeflag&OB_SHAPE_LOCK) == 0;

	if(deformed)
		return 0;

	return (cddm->mvert == me->mvert) || ob->sculpt->kb;
}

static struct PBVH *cdDM_getPBVH(Object *ob, DerivedMesh *dm)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;

	if(!ob) {
		cddm->pbvh= NULL;
		return NULL;
	}

	if(!ob->sculpt)
		return NULL;
	if(ob->sculpt->pbvh) {
		cddm->pbvh= ob->sculpt->pbvh;
		cddm->pbvh_draw = can_pbvh_draw(ob, dm);
	}

	/* always build pbvh from original mesh, and only use it for drawing if
	   this derivedmesh is just original mesh. it's the multires subsurf dm
	   that this is actually for, to support a pbvh on a modified mesh */
	if(!cddm->pbvh && ob->type == OB_MESH) {
		SculptSession *ss= ob->sculpt;
		Mesh *me= ob->data;
		cddm->pbvh = BLI_pbvh_new();
		cddm->pbvh_draw = can_pbvh_draw(ob, dm);
		BLI_pbvh_build_mesh(cddm->pbvh, me->mface, me->mvert,
				   me->totface, me->totvert);

		if(ss->modifiers_active && ob->derivedDeform) {
			DerivedMesh *deformdm= ob->derivedDeform;
			float (*vertCos)[3];
			int totvert;

			totvert= deformdm->getNumVerts(deformdm);
			vertCos= MEM_callocN(3*totvert*sizeof(float), "cdDM_getPBVH vertCos");
			deformdm->getVertCos(deformdm, vertCos);
			BLI_pbvh_apply_vertCos(cddm->pbvh, vertCos);
			MEM_freeN(vertCos);
		}
	}

	return cddm->pbvh;
}

/* update vertex normals so that drawing smooth faces works during sculpt
   TODO: proper fix is to support the pbvh in all drawing modes */
static void cdDM_update_normals_from_pbvh(DerivedMesh *dm)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	float (*face_nors)[3];

	if(!cddm->pbvh || !cddm->pbvh_draw || !dm->numFaceData)
		return;

	face_nors = CustomData_get_layer(&dm->faceData, CD_NORMAL);

	BLI_pbvh_update(cddm->pbvh, PBVH_UpdateNormals, face_nors);
}

static void cdDM_drawVerts(DerivedMesh *dm)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	MVert *mv = cddm->mvert;
	int i;

	if( GPU_buffer_legacy(dm) ) {
		glBegin(GL_POINTS);
		for(i = 0; i < dm->numVertData; i++, mv++)
			glVertex3fv(mv->co);
		glEnd();
	}
	else {	/* use OpenGL VBOs or Vertex Arrays instead for better, faster rendering */
		GPU_vertex_setup(dm);
		if( !GPU_buffer_legacy(dm) ) {
			if(dm->drawObject->tot_triangle_point)
				glDrawArrays(GL_POINTS,0, dm->drawObject->tot_triangle_point);
			else
				glDrawArrays(GL_POINTS,0, dm->drawObject->tot_loose_point);
		}
		GPU_buffer_unbind();
	}
}

static void cdDM_drawUVEdges(DerivedMesh *dm)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	MFace *mf = cddm->mface;
	MTFace *tf = DM_get_face_data_layer(dm, CD_MTFACE);
	int i;

	if(mf) {
		if( GPU_buffer_legacy(dm) ) {
			glBegin(GL_LINES);
			for(i = 0; i < dm->numFaceData; i++, mf++, tf++) {
				if(!(mf->flag&ME_HIDE)) {
					glVertex2fv(tf->uv[0]);
					glVertex2fv(tf->uv[1]);

					glVertex2fv(tf->uv[1]);
					glVertex2fv(tf->uv[2]);

					if(!mf->v4) {
						glVertex2fv(tf->uv[2]);
						glVertex2fv(tf->uv[0]);
					} else {
						glVertex2fv(tf->uv[2]);
						glVertex2fv(tf->uv[3]);

						glVertex2fv(tf->uv[3]);
						glVertex2fv(tf->uv[0]);
					}
				}
			}
			glEnd();
		}
		else {
			int prevstart = 0;
			int prevdraw = 1;
			int draw = 1;
			int curpos = 0;

			GPU_uvedge_setup(dm);
			if( !GPU_buffer_legacy(dm) ) {
				for(i = 0; i < dm->numFaceData; i++, mf++) {
					if(!(mf->flag&ME_HIDE)) {
						draw = 1;
					} 
					else {
						draw = 0;
					}
					if( prevdraw != draw ) {
						if( prevdraw > 0 && (curpos-prevstart) > 0) {
							glDrawArrays(GL_LINES,prevstart,curpos-prevstart);
						}
						prevstart = curpos;
					}
					if( mf->v4 ) {
						curpos += 8;
					}
					else {
						curpos += 6;
					}
					prevdraw = draw;
				}
				if( prevdraw > 0 && (curpos-prevstart) > 0 ) {
					glDrawArrays(GL_LINES,prevstart,curpos-prevstart);
				}
			}
			GPU_buffer_unbind();
		}
	}
}

static void cdDM_drawEdges(DerivedMesh *dm, int drawLooseEdges, int drawAllEdges)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	MVert *mvert = cddm->mvert;
	MEdge *medge = cddm->medge;
	int i;
	
	if( GPU_buffer_legacy(dm) ) {
		DEBUG_VBO( "Using legacy code. cdDM_drawEdges\n" );
		glBegin(GL_LINES);
		for(i = 0; i < dm->numEdgeData; i++, medge++) {
			if((drawAllEdges || (medge->flag&ME_EDGEDRAW))
			   && (drawLooseEdges || !(medge->flag&ME_LOOSEEDGE))) {
				glVertex3fv(mvert[medge->v1].co);
				glVertex3fv(mvert[medge->v2].co);
			}
		}
		glEnd();
	}
	else {	/* use OpenGL VBOs or Vertex Arrays instead for better, faster rendering */
		int prevstart = 0;
		int prevdraw = 1;
		int draw = 1;

		GPU_edge_setup(dm);
		if( !GPU_buffer_legacy(dm) ) {
			for(i = 0; i < dm->numEdgeData; i++, medge++) {
				if((drawAllEdges || (medge->flag&ME_EDGEDRAW))
				   && (drawLooseEdges || !(medge->flag&ME_LOOSEEDGE))) {
					draw = 1;
				} 
				else {
					draw = 0;
				}
				if( prevdraw != draw ) {
					if( prevdraw > 0 && (i-prevstart) > 0 ) {
						GPU_buffer_draw_elements( dm->drawObject->edges, GL_LINES, prevstart*2, (i-prevstart)*2  );
					}
					prevstart = i;
				}
				prevdraw = draw;
			}
			if( prevdraw > 0 && (i-prevstart) > 0 ) {
				GPU_buffer_draw_elements( dm->drawObject->edges, GL_LINES, prevstart*2, (i-prevstart)*2  );
			}
		}
		GPU_buffer_unbind();
	}
}

static void cdDM_drawLooseEdges(DerivedMesh *dm)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	MVert *mvert = cddm->mvert;
	MEdge *medge = cddm->medge;
	int i;

	if( GPU_buffer_legacy(dm) ) {
		DEBUG_VBO( "Using legacy code. cdDM_drawLooseEdges\n" );
		glBegin(GL_LINES);
		for(i = 0; i < dm->numEdgeData; i++, medge++) {
			if(medge->flag&ME_LOOSEEDGE) {
				glVertex3fv(mvert[medge->v1].co);
				glVertex3fv(mvert[medge->v2].co);
			}
		}
		glEnd();
	}
	else {	/* use OpenGL VBOs or Vertex Arrays instead for better, faster rendering */
		int prevstart = 0;
		int prevdraw = 1;
		int draw = 1;

		GPU_edge_setup(dm);
		if( !GPU_buffer_legacy(dm) ) {
			for(i = 0; i < dm->numEdgeData; i++, medge++) {
				if(medge->flag&ME_LOOSEEDGE) {
					draw = 1;
				} 
				else {
					draw = 0;
				}
				if( prevdraw != draw ) {
					if( prevdraw > 0 && (i-prevstart) > 0) {
						GPU_buffer_draw_elements( dm->drawObject->edges, GL_LINES, prevstart*2, (i-prevstart)*2  );
					}
					prevstart = i;
				}
				prevdraw = draw;
			}
			if( prevdraw > 0 && (i-prevstart) > 0 ) {
				GPU_buffer_draw_elements( dm->drawObject->edges, GL_LINES, prevstart*2, (i-prevstart)*2  );
			}
		}
		GPU_buffer_unbind();
	}
}

static void cdDM_drawFacesSolid(DerivedMesh *dm,
				float (*partial_redraw_planes)[4],
				int UNUSED(fast), int (*setMaterial)(int, void *attribs))
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	MVert *mvert = cddm->mvert;
	MFace *mface = cddm->mface;
	float *nors= dm->getFaceDataArray(dm, CD_NORMAL);
	int a, glmode = -1, shademodel = -1, matnr = -1, drawCurrentMat = 1;

#define PASSVERT(index) {						\
	if(shademodel == GL_SMOOTH) {				\
		short *no = mvert[index].no;			\
		glNormal3sv(no);						\
	}											\
	glVertex3fv(mvert[index].co);	\
}

	if(cddm->pbvh && cddm->pbvh_draw) {
		if(dm->numFaceData) {
			float (*face_nors)[3] = CustomData_get_layer(&dm->faceData, CD_NORMAL);

			/* should be per face */
			if(!setMaterial(mface->mat_nr+1, NULL))
				return;

			glShadeModel((mface->flag & ME_SMOOTH)? GL_SMOOTH: GL_FLAT);
			BLI_pbvh_draw(cddm->pbvh, partial_redraw_planes, face_nors, (mface->flag & ME_SMOOTH));
			glShadeModel(GL_FLAT);
		}

		return;
	}

	if( GPU_buffer_legacy(dm) ) {
		DEBUG_VBO( "Using legacy code. cdDM_drawFacesSolid\n" );
		glBegin(glmode = GL_QUADS);
		for(a = 0; a < dm->numFaceData; a++, mface++) {
			int new_glmode, new_matnr, new_shademodel;

			new_glmode = mface->v4?GL_QUADS:GL_TRIANGLES;
			new_matnr = mface->mat_nr + 1;
			new_shademodel = (mface->flag & ME_SMOOTH)?GL_SMOOTH:GL_FLAT;
			
			if(new_glmode != glmode || new_matnr != matnr
			   || new_shademodel != shademodel) {
				glEnd();

				drawCurrentMat = setMaterial(matnr = new_matnr, NULL);

				glShadeModel(shademodel = new_shademodel);
				glBegin(glmode = new_glmode);
			} 
			
			if(drawCurrentMat) {
				if(shademodel == GL_FLAT) {
					if (nors) {
						glNormal3fv(nors);
					}
					else {
						/* TODO make this better (cache facenormals as layer?) */
						float nor[3];
						if(mface->v4) {
							normal_quad_v3( nor,mvert[mface->v1].co, mvert[mface->v2].co, mvert[mface->v3].co, mvert[mface->v4].co);
						} else {
							normal_tri_v3( nor,mvert[mface->v1].co, mvert[mface->v2].co, mvert[mface->v3].co);
						}
						glNormal3fv(nor);
					}
				}

				PASSVERT(mface->v1);
				PASSVERT(mface->v2);
				PASSVERT(mface->v3);
				if(mface->v4) {
					PASSVERT(mface->v4);
				}
			}

			if(nors) nors += 3;
		}
		glEnd();
	}
	else {	/* use OpenGL VBOs or Vertex Arrays instead for better, faster rendering */
		GPU_vertex_setup( dm );
		GPU_normal_setup( dm );
		if( !GPU_buffer_legacy(dm) ) {
			glShadeModel(GL_SMOOTH);
			for( a = 0; a < dm->drawObject->totmaterial; a++ ) {
				if( setMaterial(dm->drawObject->materials[a].mat_nr+1, NULL) )
					glDrawArrays(GL_TRIANGLES, dm->drawObject->materials[a].start,
						     dm->drawObject->materials[a].totpoint);
			}
		}
		GPU_buffer_unbind( );
	}

#undef PASSVERT
	glShadeModel(GL_FLAT);
}

static void cdDM_drawFacesColored(DerivedMesh *dm, int useTwoSided, unsigned char *col1, unsigned char *col2)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	int a, glmode;
	unsigned char *cp1, *cp2;
	MVert *mvert = cddm->mvert;
	MFace *mface = cddm->mface;

	cp1 = col1;
	if(col2) {
		cp2 = col2;
	} else {
		cp2 = NULL;
		useTwoSided = 0;
	}

	/* there's a conflict here... twosided colors versus culling...? */
	/* defined by history, only texture faces have culling option */
	/* we need that as mesh option builtin, next to double sided lighting */
	if(col2) {
		glEnable(GL_CULL_FACE);
	}

	cdDM_update_normals_from_pbvh(dm);

	if( GPU_buffer_legacy(dm) ) {
		DEBUG_VBO( "Using legacy code. cdDM_drawFacesColored\n" );
		glShadeModel(GL_SMOOTH);
		glBegin(glmode = GL_QUADS);
		for(a = 0; a < dm->numFaceData; a++, mface++, cp1 += 16) {
			int new_glmode = mface->v4?GL_QUADS:GL_TRIANGLES;

			if(new_glmode != glmode) {
				glEnd();
				glBegin(glmode = new_glmode);
			}
				
			glColor3ubv(cp1+0);
			glVertex3fv(mvert[mface->v1].co);
			glColor3ubv(cp1+4);
			glVertex3fv(mvert[mface->v2].co);
			glColor3ubv(cp1+8);
			glVertex3fv(mvert[mface->v3].co);
			if(mface->v4) {
				glColor3ubv(cp1+12);
				glVertex3fv(mvert[mface->v4].co);
			}
				
			if(useTwoSided) {
				glColor3ubv(cp2+8);
				glVertex3fv(mvert[mface->v3].co );
				glColor3ubv(cp2+4);
				glVertex3fv(mvert[mface->v2].co );
				glColor3ubv(cp2+0);
				glVertex3fv(mvert[mface->v1].co );
				if(mface->v4) {
					glColor3ubv(cp2+12);
					glVertex3fv(mvert[mface->v4].co );
				}
			}
			if(col2) cp2 += 16;
		}
		glEnd();
	}
	else { /* use OpenGL VBOs or Vertex Arrays instead for better, faster rendering */
		GPU_color4_upload(dm,cp1);
		GPU_vertex_setup(dm);
		GPU_color_setup(dm);
		if( !GPU_buffer_legacy(dm) ) {
			glShadeModel(GL_SMOOTH);
			glDrawArrays(GL_TRIANGLES, 0, dm->drawObject->tot_triangle_point);

			if( useTwoSided ) {
				GPU_color4_upload(dm,cp2);
				GPU_color_setup(dm);
				glCullFace(GL_FRONT);
				glDrawArrays(GL_TRIANGLES, 0, dm->drawObject->tot_triangle_point);
				glCullFace(GL_BACK);
			}
		}
		GPU_buffer_unbind();
	}

	glShadeModel(GL_FLAT);
	glDisable(GL_CULL_FACE);
}

static void cdDM_drawFacesTex_common(DerivedMesh *dm,
			   int (*drawParams)(MTFace *tface, MCol *mcol, int matnr),
			   int (*drawParamsMapped)(void *userData, int index),
			   void *userData) 
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	MVert *mv = cddm->mvert;
	MFace *mf = DM_get_face_data_layer(dm, CD_MFACE);
	MCol *realcol = dm->getFaceDataArray(dm, CD_TEXTURE_MCOL);
	float *nors= dm->getFaceDataArray(dm, CD_NORMAL);
	MTFace *tf = DM_get_face_data_layer(dm, CD_MTFACE);
	int i, j, orig, *index = DM_get_face_data_layer(dm, CD_ORIGINDEX);
	int startFace = 0, lastFlag = 0xdeadbeef;
	MCol *mcol = dm->getFaceDataArray(dm, CD_WEIGHT_MCOL);
	if(!mcol)
		mcol = dm->getFaceDataArray(dm, CD_MCOL);

	cdDM_update_normals_from_pbvh(dm);

	if( GPU_buffer_legacy(dm) ) {
		DEBUG_VBO( "Using legacy code. cdDM_drawFacesTex_common\n" );
		for(i = 0; i < dm->numFaceData; i++, mf++) {
			MVert *mvert;
			int flag;
			unsigned char *cp = NULL;

			if(drawParams) {
				flag = drawParams(tf? &tf[i]: NULL, mcol? &mcol[i*4]: NULL, mf->mat_nr);
			}
			else {
				if(index) {
					orig = *index++;
					if(orig == ORIGINDEX_NONE)		{ if(nors) nors += 3; continue; }
					if(drawParamsMapped) flag = drawParamsMapped(userData, orig);
					else	{ if(nors) nors += 3; continue; }
				}
				else
					if(drawParamsMapped) flag = drawParamsMapped(userData, i);
					else	{ if(nors) nors += 3; continue; }
			}
			
			if(flag != 0) {
				if (flag==1 && mcol)
					cp= (unsigned char*) &mcol[i*4];

				if(!(mf->flag&ME_SMOOTH)) {
					if (nors) {
						glNormal3fv(nors);
					}
					else {
						float nor[3];
						if(mf->v4) {
							normal_quad_v3( nor,mv[mf->v1].co, mv[mf->v2].co, mv[mf->v3].co, mv[mf->v4].co);
						} else {
							normal_tri_v3( nor,mv[mf->v1].co, mv[mf->v2].co, mv[mf->v3].co);
						}
						glNormal3fv(nor);
					}
				}

				glBegin(mf->v4?GL_QUADS:GL_TRIANGLES);
				if(tf) glTexCoord2fv(tf[i].uv[0]);
				if(cp) glColor3ub(cp[3], cp[2], cp[1]);
				mvert = &mv[mf->v1];
				if(mf->flag&ME_SMOOTH) glNormal3sv(mvert->no);
				glVertex3fv(mvert->co);
					
				if(tf) glTexCoord2fv(tf[i].uv[1]);
				if(cp) glColor3ub(cp[7], cp[6], cp[5]);
				mvert = &mv[mf->v2];
				if(mf->flag&ME_SMOOTH) glNormal3sv(mvert->no);
				glVertex3fv(mvert->co);

				if(tf) glTexCoord2fv(tf[i].uv[2]);
				if(cp) glColor3ub(cp[11], cp[10], cp[9]);
				mvert = &mv[mf->v3];
				if(mf->flag&ME_SMOOTH) glNormal3sv(mvert->no);
				glVertex3fv(mvert->co);

				if(mf->v4) {
					if(tf) glTexCoord2fv(tf[i].uv[3]);
					if(cp) glColor3ub(cp[15], cp[14], cp[13]);
					mvert = &mv[mf->v4];
					if(mf->flag&ME_SMOOTH) glNormal3sv(mvert->no);
					glVertex3fv(mvert->co);
				}
				glEnd();
			}
			
			if(nors) nors += 3;
		}
	} else { /* use OpenGL VBOs or Vertex Arrays instead for better, faster rendering */
		MCol *col = realcol;
		if(!col)
			col = mcol;

		GPU_vertex_setup( dm );
		GPU_normal_setup( dm );
		GPU_uv_setup( dm );
		if( col != NULL ) {
			/*if( realcol && dm->drawObject->colType == CD_TEXTURE_MCOL )  {
				col = 0;
			} else if( mcol && dm->drawObject->colType == CD_MCOL ) {
				col = 0;
			}
			
			if( col != 0 ) {*/
				unsigned char *colors = MEM_mallocN(dm->getNumFaces(dm)*4*3*sizeof(unsigned char), "cdDM_drawFacesTex_common");
				for( i=0; i < dm->getNumFaces(dm); i++ ) {
					for( j=0; j < 4; j++ ) {
						colors[i*12+j*3] = col[i*4+j].r;
						colors[i*12+j*3+1] = col[i*4+j].g;
						colors[i*12+j*3+2] = col[i*4+j].b;
					}
				}
				GPU_color3_upload(dm,colors);
				MEM_freeN(colors);
				if(realcol)
					dm->drawObject->colType = CD_TEXTURE_MCOL;
				else if(mcol)
					dm->drawObject->colType = CD_MCOL;
			//}
			GPU_color_setup( dm );
		}

		if( !GPU_buffer_legacy(dm) ) {
			/* warning!, this logic is incorrect, see bug [#27175]
			 * firstly, there are no checks for changes in context, such as texface image.
			 * secondly, drawParams() sets the GL context, so checking if there is a change
			 * from lastFlag is too late once glDrawArrays() runs, since drawing the arrays
			 * will use the modified, OpenGL settings.
			 * 
			 * However its tricky to fix this without duplicating the internal logic
			 * of drawParams(), perhaps we need an argument like...
			 * drawParams(..., keep_gl_state_but_return_when_changed) ?.
			 *
			 * We could also just disable VBO's here, since texface may be deprecated - campbell.
			 */
			
			glShadeModel( GL_SMOOTH );
			lastFlag = 0;
			for(i = 0; i < dm->drawObject->tot_triangle_point/3; i++) {
				int actualFace = dm->drawObject->triangle_to_mface[i];
				int flag = 1;

				if(drawParams) {
					flag = drawParams(tf? &tf[actualFace]: NULL, mcol? &mcol[actualFace*4]: NULL, mf[actualFace].mat_nr);
				}
				else {
					if(index) {
						orig = index[actualFace];
						if(orig == ORIGINDEX_NONE) continue;
						if(drawParamsMapped)
							flag = drawParamsMapped(userData, orig);
					}
					else
						if(drawParamsMapped)
							flag = drawParamsMapped(userData, actualFace);
				}
				if( flag != lastFlag ) {
					if( startFace < i ) {
						if( lastFlag != 0 ) { /* if the flag is 0 it means the face is hidden or invisible */
							if (lastFlag==1 && col)
								GPU_color_switch(1);
							else
								GPU_color_switch(0);
							glDrawArrays(GL_TRIANGLES,startFace*3,(i-startFace)*3);
						}
					}
					lastFlag = flag;
					startFace = i;
				}
			}
			if( startFace < dm->drawObject->tot_triangle_point/3 ) {
				if( lastFlag != 0 ) { /* if the flag is 0 it means the face is hidden or invisible */
					if (lastFlag==1 && col)
						GPU_color_switch(1);
					else
						GPU_color_switch(0);
					glDrawArrays(GL_TRIANGLES, startFace*3, dm->drawObject->tot_triangle_point - startFace*3);
				}
			}
		}

		GPU_buffer_unbind();
		glShadeModel( GL_FLAT );
	}
}

static void cdDM_drawFacesTex(DerivedMesh *dm, int (*setDrawOptions)(MTFace *tface, MCol *mcol, int matnr))
{
	cdDM_drawFacesTex_common(dm, setDrawOptions, NULL, NULL);
}

static void cdDM_drawMappedFaces(DerivedMesh *dm, int (*setDrawOptions)(void *userData, int index, int *drawSmooth_r), void *userData, int useColors, int (*setMaterial)(int, void *attribs),
			int (*compareDrawOptions)(void *userData, int cur_index, int next_index))
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	MVert *mv = cddm->mvert;
	MFace *mf = cddm->mface;
	MCol *mc;
	float *nors= dm->getFaceDataArray(dm, CD_NORMAL);
	int i, orig, *index = DM_get_face_data_layer(dm, CD_ORIGINDEX);

	mc = DM_get_face_data_layer(dm, CD_ID_MCOL);
	if(!mc)
		mc = DM_get_face_data_layer(dm, CD_WEIGHT_MCOL);
	if(!mc)
		mc = DM_get_face_data_layer(dm, CD_MCOL);

	cdDM_update_normals_from_pbvh(dm);

	/* back-buffer always uses legacy since VBO's would need the
	 * color array temporarily overwritten for drawing, then reset. */
	if( GPU_buffer_legacy(dm) || G.f & G_BACKBUFSEL) {
		DEBUG_VBO( "Using legacy code. cdDM_drawMappedFaces\n" );
		for(i = 0; i < dm->numFaceData; i++, mf++) {
			int drawSmooth = (mf->flag & ME_SMOOTH);
			int draw= 1;

			orig= (index==NULL) ? i : *index++;
			
			if(orig == ORIGINDEX_NONE)
				draw= setMaterial(mf->mat_nr + 1, NULL);
			else if (setDrawOptions != NULL)
				draw= setDrawOptions(userData, orig, &drawSmooth);

			if(draw) {
				unsigned char *cp = NULL;

				if(useColors && mc)
					cp = (unsigned char *)&mc[i * 4];

				glShadeModel(drawSmooth?GL_SMOOTH:GL_FLAT);
				glBegin(mf->v4?GL_QUADS:GL_TRIANGLES);

				if (!drawSmooth) {
					if (nors) {
						glNormal3fv(nors);
					}
					else {
						float nor[3];
						if(mf->v4) {
							normal_quad_v3( nor,mv[mf->v1].co, mv[mf->v2].co, mv[mf->v3].co, mv[mf->v4].co);
						} else {
							normal_tri_v3( nor,mv[mf->v1].co, mv[mf->v2].co, mv[mf->v3].co);
						}
						glNormal3fv(nor);
					}

					if(cp) glColor3ub(cp[3], cp[2], cp[1]);
					glVertex3fv(mv[mf->v1].co);
					if(cp) glColor3ub(cp[7], cp[6], cp[5]);
					glVertex3fv(mv[mf->v2].co);
					if(cp) glColor3ub(cp[11], cp[10], cp[9]);
					glVertex3fv(mv[mf->v3].co);
					if(mf->v4) {
						if(cp) glColor3ub(cp[15], cp[14], cp[13]);
						glVertex3fv(mv[mf->v4].co);
					}
				} else {
					if(cp) glColor3ub(cp[3], cp[2], cp[1]);
					glNormal3sv(mv[mf->v1].no);
					glVertex3fv(mv[mf->v1].co);
					if(cp) glColor3ub(cp[7], cp[6], cp[5]);
					glNormal3sv(mv[mf->v2].no);
					glVertex3fv(mv[mf->v2].co);
					if(cp) glColor3ub(cp[11], cp[10], cp[9]);
					glNormal3sv(mv[mf->v3].no);
					glVertex3fv(mv[mf->v3].co);
					if(mf->v4) {
						if(cp) glColor3ub(cp[15], cp[14], cp[13]);
						glNormal3sv(mv[mf->v4].no);
						glVertex3fv(mv[mf->v4].co);
					}
				}

				glEnd();
			}
			
			if (nors) nors += 3;
		}
	}
	else { /* use OpenGL VBOs or Vertex Arrays instead for better, faster rendering */
		int prevstart = 0;
		GPU_vertex_setup(dm);
		GPU_normal_setup(dm);
		if( useColors && mc )
			GPU_color_setup(dm);
		if( !GPU_buffer_legacy(dm) ) {
			int tottri = dm->drawObject->tot_triangle_point/3;
			glShadeModel(GL_SMOOTH);
			
			if(tottri == 0) {
				/* avoid buffer problems in following code */
			}
			if(setDrawOptions == NULL) {
				/* just draw the entire face array */
				glDrawArrays(GL_TRIANGLES, 0, (tottri-1) * 3);
			}
			else {
				/* we need to check if the next material changes */
				int next_actualFace= dm->drawObject->triangle_to_mface[0];
				
				for( i = 0; i < tottri; i++ ) {
					//int actualFace = dm->drawObject->triangle_to_mface[i];
					int actualFace = next_actualFace;
					MFace *mface= mf + actualFace;
					int drawSmooth= (mface->flag & ME_SMOOTH);
					int draw = 1;
					int flush = 0;

					if(i != tottri-1)
						next_actualFace= dm->drawObject->triangle_to_mface[i+1];

					orig= (index==NULL) ? actualFace : index[actualFace];

					if(orig == ORIGINDEX_NONE)
						draw= setMaterial(mface->mat_nr + 1, NULL);
					else if (setDrawOptions != NULL)
						draw= setDrawOptions(userData, orig, &drawSmooth);
	
					/* Goal is to draw as long of a contiguous triangle
					   array as possible, so draw when we hit either an
					   invisible triangle or at the end of the array */

					/* flush buffer if current triangle isn't drawable or it's last triangle... */
					flush= !draw || i == tottri - 1;

					/* ... or when material setting is dissferent  */
					flush|= mf[actualFace].mat_nr != mf[next_actualFace].mat_nr;

					if(!flush && compareDrawOptions) {
						int next_orig= (index==NULL) ? next_actualFace : index[next_actualFace];

						/* also compare draw options and flush buffer if they're different
						   need for face selection highlight in edit mode */
						flush|= compareDrawOptions(userData, orig, next_orig) == 0;
					}

					if(flush) {
						int first= prevstart*3;
						int count= (i-prevstart+(draw ? 1 : 0))*3; /* Add one to the length if we're drawing at the end of the array */

						if(count)
							glDrawArrays(GL_TRIANGLES, first, count);

						prevstart = i + 1;
					}
				}
			}

			glShadeModel(GL_FLAT);
		}
		GPU_buffer_unbind();
	}
}

static void cdDM_drawMappedFacesTex(DerivedMesh *dm, int (*setDrawOptions)(void *userData, int index), void *userData)
{
	cdDM_drawFacesTex_common(dm, NULL, setDrawOptions, userData);
}

static void cddm_draw_attrib_vertex(DMVertexAttribs *attribs, MVert *mvert, int a, int index, int vert, int smoothnormal)
{
	int b;

	/* orco texture coordinates */
	if(attribs->totorco) {
		if(attribs->orco.glTexco)
			glTexCoord3fv(attribs->orco.array[index]);
		else
			glVertexAttrib3fvARB(attribs->orco.glIndex, attribs->orco.array[index]);
	}

	/* uv texture coordinates */
	for(b = 0; b < attribs->tottface; b++) {
		MTFace *tf = &attribs->tface[b].array[a];

		if(attribs->tface[b].glTexco)
			glTexCoord2fv(tf->uv[vert]);
		else
			glVertexAttrib2fvARB(attribs->tface[b].glIndex, tf->uv[vert]);
	}

	/* vertex colors */
	for(b = 0; b < attribs->totmcol; b++) {
		MCol *cp = &attribs->mcol[b].array[a*4 + vert];
		GLubyte col[4];
		col[0]= cp->b; col[1]= cp->g; col[2]= cp->r; col[3]= cp->a;
		glVertexAttrib4ubvARB(attribs->mcol[b].glIndex, col);
	}

	/* tangent for normal mapping */
	if(attribs->tottang) {
		float *tang = attribs->tang.array[a*4 + vert];
		glVertexAttrib4fvARB(attribs->tang.glIndex, tang);
	}

	/* vertex normal */
	if(smoothnormal)
		glNormal3sv(mvert[index].no);
	
	/* vertex coordinate */
	glVertex3fv(mvert[index].co);
}

static void cdDM_drawMappedFacesGLSL(DerivedMesh *dm, int (*setMaterial)(int, void *attribs), int (*setDrawOptions)(void *userData, int index), void *userData)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	GPUVertexAttribs gattribs;
	DMVertexAttribs attribs;
	MVert *mvert = cddm->mvert;
	MFace *mface = cddm->mface;
	/* MTFace *tf = dm->getFaceDataArray(dm, CD_MTFACE); */ /* UNUSED */
	float (*nors)[3] = dm->getFaceDataArray(dm, CD_NORMAL);
	int a, b, dodraw, matnr, new_matnr;
	int orig, *index = dm->getFaceDataArray(dm, CD_ORIGINDEX);

	cdDM_update_normals_from_pbvh(dm);

	matnr = -1;
	dodraw = 0;

	glShadeModel(GL_SMOOTH);

	if( GPU_buffer_legacy(dm) || setDrawOptions != NULL ) {
		DEBUG_VBO( "Using legacy code. cdDM_drawMappedFacesGLSL\n" );
		memset(&attribs, 0, sizeof(attribs));

		glBegin(GL_QUADS);

		for(a = 0; a < dm->numFaceData; a++, mface++) {
			const int smoothnormal = (mface->flag & ME_SMOOTH);
			new_matnr = mface->mat_nr + 1;

			if(new_matnr != matnr) {
				glEnd();

				dodraw = setMaterial(matnr = new_matnr, &gattribs);
				if(dodraw)
					DM_vertex_attributes_from_gpu(dm, &gattribs, &attribs);

				glBegin(GL_QUADS);
			}

			if(!dodraw) {
				continue;
			}
			else if(setDrawOptions) {
				orig = (index)? index[a]: a;

				if(orig == ORIGINDEX_NONE) {
					/* since the material is set by setMaterial(), faces with no
					 * origin can be assumed to be generated by a modifier */ 
					
					/* continue */
				}
				else if(!setDrawOptions(userData, orig))
					continue;
			}

			if(!smoothnormal) {
				if(nors) {
					glNormal3fv(nors[a]);
				}
				else {
					/* TODO ideally a normal layer should always be available */
					float nor[3];
					if(mface->v4) {
						normal_quad_v3( nor,mvert[mface->v1].co, mvert[mface->v2].co, mvert[mface->v3].co, mvert[mface->v4].co);
					} else {
						normal_tri_v3( nor,mvert[mface->v1].co, mvert[mface->v2].co, mvert[mface->v3].co);
					}
					glNormal3fv(nor);
				}
			}

			cddm_draw_attrib_vertex(&attribs, mvert, a, mface->v1, 0, smoothnormal);
			cddm_draw_attrib_vertex(&attribs, mvert, a, mface->v2, 1, smoothnormal);
			cddm_draw_attrib_vertex(&attribs, mvert, a, mface->v3, 2, smoothnormal);

			if(mface->v4)
				cddm_draw_attrib_vertex(&attribs, mvert, a, mface->v4, 3, smoothnormal);
			else
				cddm_draw_attrib_vertex(&attribs, mvert, a, mface->v3, 2, smoothnormal);
		}
		glEnd();
	}
	else {
		GPUBuffer *buffer = NULL;
		char *varray = NULL;
		int numdata = 0, elementsize = 0, offset;
		int start = 0, numfaces = 0 /* , prevdraw = 0 */ /* UNUSED */, curface = 0;
		int i;

		MFace *mf = mface;
		GPUAttrib datatypes[GPU_MAX_ATTRIB]; /* TODO, messing up when switching materials many times - [#21056]*/
		memset(&attribs, 0, sizeof(attribs));

		GPU_vertex_setup(dm);
		GPU_normal_setup(dm);

		if( !GPU_buffer_legacy(dm) ) {
			for( i = 0; i < dm->drawObject->tot_triangle_point/3; i++ ) {

				a = dm->drawObject->triangle_to_mface[i];

				mface = mf + a;
				new_matnr = mface->mat_nr + 1;

				if(new_matnr != matnr ) {
					numfaces = curface - start;
					if( numfaces > 0 ) {

						if( dodraw ) {

							if( numdata != 0 ) {

								GPU_buffer_unlock(buffer);

								GPU_interleaved_attrib_setup(buffer,datatypes,numdata);
							}

							glDrawArrays(GL_TRIANGLES,start*3,numfaces*3);

							if( numdata != 0 ) {

								GPU_buffer_free(buffer);

								buffer = NULL;
							}

						}
					}
					numdata = 0;
					start = curface;
					/* prevdraw = dodraw; */ /* UNUSED */
					dodraw = setMaterial(matnr = new_matnr, &gattribs);
					if(dodraw) {
						DM_vertex_attributes_from_gpu(dm, &gattribs, &attribs);

						if(attribs.totorco) {
							datatypes[numdata].index = attribs.orco.glIndex;
							datatypes[numdata].size = 3;
							datatypes[numdata].type = GL_FLOAT;
							numdata++;
						}
						for(b = 0; b < attribs.tottface; b++) {
							datatypes[numdata].index = attribs.tface[b].glIndex;
							datatypes[numdata].size = 2;
							datatypes[numdata].type = GL_FLOAT;
							numdata++;
						}	
						for(b = 0; b < attribs.totmcol; b++) {
							datatypes[numdata].index = attribs.mcol[b].glIndex;
							datatypes[numdata].size = 4;
							datatypes[numdata].type = GL_UNSIGNED_BYTE;
							numdata++;
						}	
						if(attribs.tottang) {
							datatypes[numdata].index = attribs.tang.glIndex;
							datatypes[numdata].size = 4;
							datatypes[numdata].type = GL_FLOAT;
							numdata++;
						}
						if( numdata != 0 ) {
							elementsize = GPU_attrib_element_size( datatypes, numdata );
							buffer = GPU_buffer_alloc( elementsize*dm->drawObject->tot_triangle_point);
							if( buffer == NULL ) {
								GPU_buffer_unbind();
								dm->drawObject->legacy = 1;
								return;
							}
							varray = GPU_buffer_lock_stream(buffer);
							if( varray == NULL ) {
								GPU_buffer_unbind();
								GPU_buffer_free(buffer);
								dm->drawObject->legacy = 1;
								return;
							}
						}
						else {
							/* if the buffer was set, dont use it again.
							 * prevdraw was assumed true but didnt run so set to false - [#21036] */
							/* prevdraw= 0; */ /* UNUSED */
							buffer= NULL;
						}
					}
				}
				if(!dodraw) {
					continue;
				}

				if( numdata != 0 ) {
					offset = 0;
					if(attribs.totorco) {
						VECCOPY((float *)&varray[elementsize*curface*3],(float *)attribs.orco.array[mface->v1]);
						VECCOPY((float *)&varray[elementsize*curface*3+elementsize],(float *)attribs.orco.array[mface->v2]);
						VECCOPY((float *)&varray[elementsize*curface*3+elementsize*2],(float *)attribs.orco.array[mface->v3]);
						offset += sizeof(float)*3;
					}
					for(b = 0; b < attribs.tottface; b++) {
						MTFace *tf = &attribs.tface[b].array[a];
						VECCOPY2D((float *)&varray[elementsize*curface*3+offset],tf->uv[0]);
						VECCOPY2D((float *)&varray[elementsize*curface*3+offset+elementsize],tf->uv[1]);

						VECCOPY2D((float *)&varray[elementsize*curface*3+offset+elementsize*2],tf->uv[2]);
						offset += sizeof(float)*2;
					}
					for(b = 0; b < attribs.totmcol; b++) {
						MCol *cp = &attribs.mcol[b].array[a*4 + 0];
						GLubyte col[4];
						col[0]= cp->b; col[1]= cp->g; col[2]= cp->r; col[3]= cp->a;
						QUATCOPY((unsigned char *)&varray[elementsize*curface*3+offset], col);
						cp = &attribs.mcol[b].array[a*4 + 1];
						col[0]= cp->b; col[1]= cp->g; col[2]= cp->r; col[3]= cp->a;
						QUATCOPY((unsigned char *)&varray[elementsize*curface*3+offset+elementsize], col);
						cp = &attribs.mcol[b].array[a*4 + 2];
						col[0]= cp->b; col[1]= cp->g; col[2]= cp->r; col[3]= cp->a;
						QUATCOPY((unsigned char *)&varray[elementsize*curface*3+offset+elementsize*2], col);
						offset += sizeof(unsigned char)*4;
					}	
					if(attribs.tottang) {
						float *tang = attribs.tang.array[a*4 + 0];
						QUATCOPY((float *)&varray[elementsize*curface*3+offset], tang);
						tang = attribs.tang.array[a*4 + 1];
						QUATCOPY((float *)&varray[elementsize*curface*3+offset+elementsize], tang);
						tang = attribs.tang.array[a*4 + 2];
						QUATCOPY((float *)&varray[elementsize*curface*3+offset+elementsize*2], tang);
						offset += sizeof(float)*4;
					}
					(void)offset;
				}
				curface++;
				if(mface->v4) {
					if( numdata != 0 ) {
						offset = 0;
						if(attribs.totorco) {
							VECCOPY((float *)&varray[elementsize*curface*3],(float *)attribs.orco.array[mface->v3]);
							VECCOPY((float *)&varray[elementsize*curface*3+elementsize],(float *)attribs.orco.array[mface->v4]);
							VECCOPY((float *)&varray[elementsize*curface*3+elementsize*2],(float *)attribs.orco.array[mface->v1]);
							offset += sizeof(float)*3;
						}
						for(b = 0; b < attribs.tottface; b++) {
							MTFace *tf = &attribs.tface[b].array[a];
							VECCOPY2D((float *)&varray[elementsize*curface*3+offset],tf->uv[2]);
							VECCOPY2D((float *)&varray[elementsize*curface*3+offset+elementsize],tf->uv[3]);
							VECCOPY2D((float *)&varray[elementsize*curface*3+offset+elementsize*2],tf->uv[0]);
							offset += sizeof(float)*2;
						}
						for(b = 0; b < attribs.totmcol; b++) {
							MCol *cp = &attribs.mcol[b].array[a*4 + 2];
							GLubyte col[4];
							col[0]= cp->b; col[1]= cp->g; col[2]= cp->r; col[3]= cp->a;
							QUATCOPY((unsigned char *)&varray[elementsize*curface*3+offset], col);
							cp = &attribs.mcol[b].array[a*4 + 3];
							col[0]= cp->b; col[1]= cp->g; col[2]= cp->r; col[3]= cp->a;
							QUATCOPY((unsigned char *)&varray[elementsize*curface*3+offset+elementsize], col);
							cp = &attribs.mcol[b].array[a*4 + 0];
							col[0]= cp->b; col[1]= cp->g; col[2]= cp->r; col[3]= cp->a;
							QUATCOPY((unsigned char *)&varray[elementsize*curface*3+offset+elementsize*2], col);
							offset += sizeof(unsigned char)*4;
						}	
						if(attribs.tottang) {
							float *tang = attribs.tang.array[a*4 + 2];
							QUATCOPY((float *)&varray[elementsize*curface*3+offset], tang);
							tang = attribs.tang.array[a*4 + 3];
							QUATCOPY((float *)&varray[elementsize*curface*3+offset+elementsize], tang);
							tang = attribs.tang.array[a*4 + 0];
							QUATCOPY((float *)&varray[elementsize*curface*3+offset+elementsize*2], tang);
							offset += sizeof(float)*4;
						}
						(void)offset;
					}
					curface++;
					i++;
				}
			}
			numfaces = curface - start;
			if( numfaces > 0 ) {
				if( dodraw ) {
					if( numdata != 0 ) {
						GPU_buffer_unlock(buffer);
						GPU_interleaved_attrib_setup(buffer,datatypes,numdata);
					}
					glDrawArrays(GL_TRIANGLES,start*3,(curface-start)*3);
				}
			}
			GPU_buffer_unbind();
		}
		GPU_buffer_free(buffer);
	}

	glShadeModel(GL_FLAT);
}

static void cdDM_drawFacesGLSL(DerivedMesh *dm, int (*setMaterial)(int, void *attribs))
{
	dm->drawMappedFacesGLSL(dm, setMaterial, NULL, NULL);
}

static void cdDM_drawMappedFacesMat(DerivedMesh *dm,
	void (*setMaterial)(void *userData, int, void *attribs),
	int (*setFace)(void *userData, int index), void *userData)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	GPUVertexAttribs gattribs;
	DMVertexAttribs attribs;
	MVert *mvert = cddm->mvert;
	MFace *mf = cddm->mface;
	float (*nors)[3] = dm->getFaceDataArray(dm, CD_NORMAL);
	int a, matnr, new_matnr;
	int orig, *index = dm->getFaceDataArray(dm, CD_ORIGINDEX);

	cdDM_update_normals_from_pbvh(dm);

	matnr = -1;

	glShadeModel(GL_SMOOTH);

	memset(&attribs, 0, sizeof(attribs));

	glBegin(GL_QUADS);

	for(a = 0; a < dm->numFaceData; a++, mf++) {
		const int smoothnormal = (mf->flag & ME_SMOOTH);

		/* material */
		new_matnr = mf->mat_nr + 1;

		if(new_matnr != matnr) {
			glEnd();

			setMaterial(userData, matnr = new_matnr, &gattribs);
			DM_vertex_attributes_from_gpu(dm, &gattribs, &attribs);

			glBegin(GL_QUADS);
		}

		/* skipping faces */
		if(setFace) {
			orig = (index)? index[a]: a;

			if(orig != ORIGINDEX_NONE && !setFace(userData, orig))
				continue;
		}

		/* smooth normal */
		if(!smoothnormal) {
			if(nors) {
				glNormal3fv(nors[a]);
			}
			else {
				/* TODO ideally a normal layer should always be available */
				float nor[3];

				if(mf->v4)
					normal_quad_v3( nor,mvert[mf->v1].co, mvert[mf->v2].co, mvert[mf->v3].co, mvert[mf->v4].co);
				else
					normal_tri_v3( nor,mvert[mf->v1].co, mvert[mf->v2].co, mvert[mf->v3].co);

				glNormal3fv(nor);
			}
		}

		/* vertices */
		cddm_draw_attrib_vertex(&attribs, mvert, a, mf->v1, 0, smoothnormal);
		cddm_draw_attrib_vertex(&attribs, mvert, a, mf->v2, 1, smoothnormal);
		cddm_draw_attrib_vertex(&attribs, mvert, a, mf->v3, 2, smoothnormal);

		if(mf->v4)
			cddm_draw_attrib_vertex(&attribs, mvert, a, mf->v4, 3, smoothnormal);
		else
			cddm_draw_attrib_vertex(&attribs, mvert, a, mf->v3, 2, smoothnormal);
	}
	glEnd();

	glShadeModel(GL_FLAT);
}

static void cdDM_drawMappedEdges(DerivedMesh *dm, int (*setDrawOptions)(void *userData, int index), void *userData)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	MVert *vert = cddm->mvert;
	MEdge *edge = cddm->medge;
	int i, orig, *index = DM_get_edge_data_layer(dm, CD_ORIGINDEX);

	glBegin(GL_LINES);
	for(i = 0; i < dm->numEdgeData; i++, edge++) {
		if(index) {
			orig = *index++;
			if(setDrawOptions && orig == ORIGINDEX_NONE) continue;
		}
		else
			orig = i;

		if(!setDrawOptions || setDrawOptions(userData, orig)) {
			glVertex3fv(vert[edge->v1].co);
			glVertex3fv(vert[edge->v2].co);
		}
	}
	glEnd();
}

static void cdDM_foreachMappedVert(
						   DerivedMesh *dm,
						   void (*func)(void *userData, int index, float *co,
										float *no_f, short *no_s),
						   void *userData)
{
	MVert *mv = CDDM_get_verts(dm);
	int i, orig, *index = DM_get_vert_data_layer(dm, CD_ORIGINDEX);

	for(i = 0; i < dm->numVertData; i++, mv++) {
		if(index) {
			orig = *index++;
			if(orig == ORIGINDEX_NONE) continue;
			func(userData, orig, mv->co, NULL, mv->no);
		}
		else
			func(userData, i, mv->co, NULL, mv->no);
	}
}

static void cdDM_foreachMappedEdge(
						   DerivedMesh *dm,
						   void (*func)(void *userData, int index,
										float *v0co, float *v1co),
						   void *userData)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*) dm;
	MVert *mv = cddm->mvert;
	MEdge *med = cddm->medge;
	int i, orig, *index = DM_get_edge_data_layer(dm, CD_ORIGINDEX);

	for(i = 0; i < dm->numEdgeData; i++, med++) {
		if (index) {
			orig = *index++;
			if(orig == ORIGINDEX_NONE) continue;
			func(userData, orig, mv[med->v1].co, mv[med->v2].co);
		}
		else
			func(userData, i, mv[med->v1].co, mv[med->v2].co);
	}
}

static void cdDM_foreachMappedFaceCenter(
						   DerivedMesh *dm,
						   void (*func)(void *userData, int index,
										float *cent, float *no),
						   void *userData)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*)dm;
	MVert *mv = cddm->mvert;
	MFace *mf = cddm->mface;
	int i, orig, *index = DM_get_face_data_layer(dm, CD_ORIGINDEX);

	for(i = 0; i < dm->numFaceData; i++, mf++) {
		float cent[3];
		float no[3];

		if (index) {
			orig = *index++;
			if(orig == ORIGINDEX_NONE) continue;
		}
		else
			orig = i;

		VECCOPY(cent, mv[mf->v1].co);
		add_v3_v3(cent, mv[mf->v2].co);
		add_v3_v3(cent, mv[mf->v3].co);

		if (mf->v4) {
			normal_quad_v3( no,mv[mf->v1].co, mv[mf->v2].co, mv[mf->v3].co, mv[mf->v4].co);
			add_v3_v3(cent, mv[mf->v4].co);
			mul_v3_fl(cent, 0.25f);
		} else {
			normal_tri_v3( no,mv[mf->v1].co, mv[mf->v2].co, mv[mf->v3].co);
			mul_v3_fl(cent, 0.33333333333f);
		}

		func(userData, orig, cent, no);
	}
}

static void cdDM_free_internal(CDDerivedMesh *cddm)
{
	if(cddm->fmap) MEM_freeN(cddm->fmap);
	if(cddm->fmap_mem) MEM_freeN(cddm->fmap_mem);
}

static void cdDM_release(DerivedMesh *dm)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*)dm;

	if (DM_release(dm)) {
		cdDM_free_internal(cddm);
		MEM_freeN(cddm);
	}
}

/**************** CDDM interface functions ****************/
static CDDerivedMesh *cdDM_create(const char *desc)
{
	CDDerivedMesh *cddm;
	DerivedMesh *dm;

	cddm = MEM_callocN(sizeof(*cddm), desc);
	dm = &cddm->dm;

	dm->getMinMax = cdDM_getMinMax;

	dm->getNumVerts = cdDM_getNumVerts;
	dm->getNumFaces = cdDM_getNumFaces;
	dm->getNumEdges = cdDM_getNumEdges;

	dm->getVert = cdDM_getVert;
	dm->getEdge = cdDM_getEdge;
	dm->getFace = cdDM_getFace;
	dm->copyVertArray = cdDM_copyVertArray;
	dm->copyEdgeArray = cdDM_copyEdgeArray;
	dm->copyFaceArray = cdDM_copyFaceArray;
	dm->getVertData = DM_get_vert_data;
	dm->getEdgeData = DM_get_edge_data;
	dm->getFaceData = DM_get_face_data;
	dm->getVertDataArray = DM_get_vert_data_layer;
	dm->getEdgeDataArray = DM_get_edge_data_layer;
	dm->getFaceDataArray = DM_get_face_data_layer;

	dm->getVertCos = cdDM_getVertCos;
	dm->getVertCo = cdDM_getVertCo;
	dm->getVertNo = cdDM_getVertNo;

	dm->getPBVH = cdDM_getPBVH;
	dm->getFaceMap = cdDM_getFaceMap;

	dm->drawVerts = cdDM_drawVerts;

	dm->drawUVEdges = cdDM_drawUVEdges;
	dm->drawEdges = cdDM_drawEdges;
	dm->drawLooseEdges = cdDM_drawLooseEdges;
	dm->drawMappedEdges = cdDM_drawMappedEdges;

	dm->drawFacesSolid = cdDM_drawFacesSolid;
	dm->drawFacesColored = cdDM_drawFacesColored;
	dm->drawFacesTex = cdDM_drawFacesTex;
	dm->drawFacesGLSL = cdDM_drawFacesGLSL;
	dm->drawMappedFaces = cdDM_drawMappedFaces;
	dm->drawMappedFacesTex = cdDM_drawMappedFacesTex;
	dm->drawMappedFacesGLSL = cdDM_drawMappedFacesGLSL;
	dm->drawMappedFacesMat = cdDM_drawMappedFacesMat;

	dm->foreachMappedVert = cdDM_foreachMappedVert;
	dm->foreachMappedEdge = cdDM_foreachMappedEdge;
	dm->foreachMappedFaceCenter = cdDM_foreachMappedFaceCenter;

	dm->release = cdDM_release;

	return cddm;
}

DerivedMesh *CDDM_new(int numVerts, int numEdges, int numFaces)
{
	CDDerivedMesh *cddm = cdDM_create("CDDM_new dm");
	DerivedMesh *dm = &cddm->dm;

	DM_init(dm, DM_TYPE_CDDM, numVerts, numEdges, numFaces);

	CustomData_add_layer(&dm->vertData, CD_ORIGINDEX, CD_CALLOC, NULL, numVerts);
	CustomData_add_layer(&dm->edgeData, CD_ORIGINDEX, CD_CALLOC, NULL, numEdges);
	CustomData_add_layer(&dm->faceData, CD_ORIGINDEX, CD_CALLOC, NULL, numFaces);

	CustomData_add_layer(&dm->vertData, CD_MVERT, CD_CALLOC, NULL, numVerts);
	CustomData_add_layer(&dm->edgeData, CD_MEDGE, CD_CALLOC, NULL, numEdges);
	CustomData_add_layer(&dm->faceData, CD_MFACE, CD_CALLOC, NULL, numFaces);

	cddm->mvert = CustomData_get_layer(&dm->vertData, CD_MVERT);
	cddm->medge = CustomData_get_layer(&dm->edgeData, CD_MEDGE);
	cddm->mface = CustomData_get_layer(&dm->faceData, CD_MFACE);

	return dm;
}

DerivedMesh *CDDM_from_mesh(Mesh *mesh, Object *UNUSED(ob))
{
	CDDerivedMesh *cddm = cdDM_create("CDDM_from_mesh dm");
	DerivedMesh *dm = &cddm->dm;
	CustomDataMask mask = CD_MASK_MESH & (~CD_MASK_MDISPS);
	int alloctype;

	/* this does a referenced copy, with an exception for fluidsim */

	DM_init(dm, DM_TYPE_CDDM, mesh->totvert, mesh->totedge, mesh->totface);

	dm->deformedOnly = 1;

	alloctype= CD_REFERENCE;

	CustomData_merge(&mesh->vdata, &dm->vertData, mask, alloctype,
					 mesh->totvert);
	CustomData_merge(&mesh->edata, &dm->edgeData, mask, alloctype,
					 mesh->totedge);
	CustomData_merge(&mesh->fdata, &dm->faceData, mask, alloctype,
					 mesh->totface);

	cddm->mvert = CustomData_get_layer(&dm->vertData, CD_MVERT);
	cddm->medge = CustomData_get_layer(&dm->edgeData, CD_MEDGE);
	cddm->mface = CustomData_get_layer(&dm->faceData, CD_MFACE);

	return dm;
}

DerivedMesh *CDDM_from_editmesh(EditMesh *em, Mesh *UNUSED(me))
{
	DerivedMesh *dm = CDDM_new(BLI_countlist(&em->verts),
							   BLI_countlist(&em->edges),
							   BLI_countlist(&em->faces));
	CDDerivedMesh *cddm = (CDDerivedMesh*)dm;
	EditVert *eve;
	EditEdge *eed;
	EditFace *efa;
	MVert *mvert = cddm->mvert;
	MEdge *medge = cddm->medge;
	MFace *mface = cddm->mface;
	int i, *index;

	dm->deformedOnly = 1;

	CustomData_merge(&em->vdata, &dm->vertData, CD_MASK_DERIVEDMESH,
					 CD_CALLOC, dm->numVertData);
	/* CustomData_merge(&em->edata, &dm->edgeData, CD_MASK_DERIVEDMESH,
					 CD_CALLOC, dm->numEdgeData); */
	CustomData_merge(&em->fdata, &dm->faceData, CD_MASK_DERIVEDMESH,
					 CD_CALLOC, dm->numFaceData);

	/* set eve->hash to vert index */
	for(i = 0, eve = em->verts.first; eve; eve = eve->next, ++i)
		eve->tmp.l = i;

	/* Need to be able to mark loose edges */
	for(eed = em->edges.first; eed; eed = eed->next) {
		eed->f2 = 0;
	}
	for(efa = em->faces.first; efa; efa = efa->next) {
		efa->e1->f2 = 1;
		efa->e2->f2 = 1;
		efa->e3->f2 = 1;
		if(efa->e4) efa->e4->f2 = 1;
	}

	index = dm->getVertDataArray(dm, CD_ORIGINDEX);
	for(i = 0, eve = em->verts.first; i < dm->numVertData;
		i++, eve = eve->next, index++) {
		MVert *mv = &mvert[i];

		VECCOPY(mv->co, eve->co);

		normal_float_to_short_v3(mv->no, eve->no);
		mv->bweight = (unsigned char) (eve->bweight * 255.0f);

		mv->flag = 0;

		*index = i;

		CustomData_from_em_block(&em->vdata, &dm->vertData, eve->data, i);
	}

	index = dm->getEdgeDataArray(dm, CD_ORIGINDEX);
	for(i = 0, eed = em->edges.first; i < dm->numEdgeData;
		i++, eed = eed->next, index++) {
		MEdge *med = &medge[i];

		med->v1 = eed->v1->tmp.l;
		med->v2 = eed->v2->tmp.l;
		med->crease = (unsigned char) (eed->crease * 255.0f);
		med->bweight = (unsigned char) (eed->bweight * 255.0f);
		med->flag = ME_EDGEDRAW|ME_EDGERENDER;
		
		if(eed->seam) med->flag |= ME_SEAM;
		if(eed->sharp) med->flag |= ME_SHARP;
		if(!eed->f2) med->flag |= ME_LOOSEEDGE;

		*index = i;

		/* CustomData_from_em_block(&em->edata, &dm->edgeData, eed->data, i); */
	}

	index = dm->getFaceDataArray(dm, CD_ORIGINDEX);
	for(i = 0, efa = em->faces.first; i < dm->numFaceData;
		i++, efa = efa->next, index++) {
		MFace *mf = &mface[i];

		mf->v1 = efa->v1->tmp.l;
		mf->v2 = efa->v2->tmp.l;
		mf->v3 = efa->v3->tmp.l;
		mf->v4 = efa->v4 ? efa->v4->tmp.l : 0;
		mf->mat_nr = efa->mat_nr;
		mf->flag = efa->flag;

		*index = i;

		CustomData_from_em_block(&em->fdata, &dm->faceData, efa->data, i);
		test_index_face(mf, &dm->faceData, i, efa->v4?4:3);
	}

	return dm;
}

DerivedMesh *CDDM_from_curve(Object *ob)
{
	return CDDM_from_curve_customDB(ob, &ob->disp);
}

DerivedMesh *CDDM_from_curve_customDB(Object *ob, ListBase *dispbase)
{
	DerivedMesh *dm;
	CDDerivedMesh *cddm;
	MVert *allvert;
	MEdge *alledge;
	MFace *allface;
	int totvert, totedge, totface;

	if (nurbs_to_mdata_customdb(ob, dispbase, &allvert, &totvert, &alledge,
		&totedge, &allface, &totface) != 0) {
		/* Error initializing mdata. This often happens when curve is empty */
		return CDDM_new(0, 0, 0);
	}

	dm = CDDM_new(totvert, totedge, totface);
	dm->deformedOnly = 1;

	cddm = (CDDerivedMesh*)dm;

	memcpy(cddm->mvert, allvert, totvert*sizeof(MVert));
	memcpy(cddm->medge, alledge, totedge*sizeof(MEdge));
	memcpy(cddm->mface, allface, totface*sizeof(MFace));

	MEM_freeN(allvert);
	MEM_freeN(alledge);
	MEM_freeN(allface);

	return dm;
}

DerivedMesh *CDDM_copy(DerivedMesh *source)
{
	CDDerivedMesh *cddm = cdDM_create("CDDM_copy cddm");
	DerivedMesh *dm = &cddm->dm;
	int numVerts = source->numVertData;
	int numEdges = source->numEdgeData;
	int numFaces = source->numFaceData;

	/* ensure these are created if they are made on demand */
	source->getVertDataArray(source, CD_ORIGINDEX);
	source->getEdgeDataArray(source, CD_ORIGINDEX);
	source->getFaceDataArray(source, CD_ORIGINDEX);

	/* this initializes dm, and copies all non mvert/medge/mface layers */
	DM_from_template(dm, source, DM_TYPE_CDDM, numVerts, numEdges, numFaces);
	dm->deformedOnly = source->deformedOnly;

	CustomData_copy_data(&source->vertData, &dm->vertData, 0, 0, numVerts);
	CustomData_copy_data(&source->edgeData, &dm->edgeData, 0, 0, numEdges);
	CustomData_copy_data(&source->faceData, &dm->faceData, 0, 0, numFaces);

	/* now add mvert/medge/mface layers */
	cddm->mvert = source->dupVertArray(source);
	cddm->medge = source->dupEdgeArray(source);
	cddm->mface = source->dupFaceArray(source);

	CustomData_add_layer(&dm->vertData, CD_MVERT, CD_ASSIGN, cddm->mvert, numVerts);
	CustomData_add_layer(&dm->edgeData, CD_MEDGE, CD_ASSIGN, cddm->medge, numEdges);
	CustomData_add_layer(&dm->faceData, CD_MFACE, CD_ASSIGN, cddm->mface, numFaces);

	return dm;
}

/* note, the CD_ORIGINDEX layers are all 0, so if there is a direct
 * relationship betwen mesh data this needs to be set by the caller. */
DerivedMesh *CDDM_from_template(DerivedMesh *source,
								int numVerts, int numEdges, int numFaces)
{
	CDDerivedMesh *cddm = cdDM_create("CDDM_from_template dest");
	DerivedMesh *dm = &cddm->dm;

	/* ensure these are created if they are made on demand */
	source->getVertDataArray(source, CD_ORIGINDEX);
	source->getEdgeDataArray(source, CD_ORIGINDEX);
	source->getFaceDataArray(source, CD_ORIGINDEX);

	/* this does a copy of all non mvert/medge/mface layers */
	DM_from_template(dm, source, DM_TYPE_CDDM, numVerts, numEdges, numFaces);

	/* now add mvert/medge/mface layers */
	CustomData_add_layer(&dm->vertData, CD_MVERT, CD_CALLOC, NULL, numVerts);
	CustomData_add_layer(&dm->edgeData, CD_MEDGE, CD_CALLOC, NULL, numEdges);
	CustomData_add_layer(&dm->faceData, CD_MFACE, CD_CALLOC, NULL, numFaces);

	if(!CustomData_get_layer(&dm->vertData, CD_ORIGINDEX))
		CustomData_add_layer(&dm->vertData, CD_ORIGINDEX, CD_CALLOC, NULL, numVerts);
	if(!CustomData_get_layer(&dm->edgeData, CD_ORIGINDEX))
		CustomData_add_layer(&dm->edgeData, CD_ORIGINDEX, CD_CALLOC, NULL, numEdges);
	if(!CustomData_get_layer(&dm->faceData, CD_ORIGINDEX))
		CustomData_add_layer(&dm->faceData, CD_ORIGINDEX, CD_CALLOC, NULL, numFaces);

	cddm->mvert = CustomData_get_layer(&dm->vertData, CD_MVERT);
	cddm->medge = CustomData_get_layer(&dm->edgeData, CD_MEDGE);
	cddm->mface = CustomData_get_layer(&dm->faceData, CD_MFACE);

	return dm;
}

void CDDM_apply_vert_coords(DerivedMesh *dm, float (*vertCoords)[3])
{
	CDDerivedMesh *cddm = (CDDerivedMesh*)dm;
	MVert *vert;
	int i;

	/* this will just return the pointer if it wasn't a referenced layer */
	vert = CustomData_duplicate_referenced_layer(&dm->vertData, CD_MVERT);
	cddm->mvert = vert;

	for(i = 0; i < dm->numVertData; ++i, ++vert)
		VECCOPY(vert->co, vertCoords[i]);
}

void CDDM_apply_vert_normals(DerivedMesh *dm, short (*vertNormals)[3])
{
	CDDerivedMesh *cddm = (CDDerivedMesh*)dm;
	MVert *vert;
	int i;

	/* this will just return the pointer if it wasn't a referenced layer */
	vert = CustomData_duplicate_referenced_layer(&dm->vertData, CD_MVERT);
	cddm->mvert = vert;

	for(i = 0; i < dm->numVertData; ++i, ++vert)
		copy_v3_v3_short(vert->no, vertNormals[i]);
}

void CDDM_calc_normals(DerivedMesh *dm)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*)dm;
	float (*face_nors)[3];

	if(dm->numVertData == 0) return;

	/* we don't want to overwrite any referenced layers */
	cddm->mvert = CustomData_duplicate_referenced_layer(&dm->vertData, CD_MVERT);

	/* make a face normal layer if not present */
	face_nors = CustomData_get_layer(&dm->faceData, CD_NORMAL);
	if(!face_nors)
		face_nors = CustomData_add_layer(&dm->faceData, CD_NORMAL, CD_CALLOC,
										 NULL, dm->numFaceData);

	/* calculate face normals */
	mesh_calc_normals(cddm->mvert, dm->numVertData, CDDM_get_faces(dm), dm->numFaceData, face_nors);
}

void CDDM_calc_edges(DerivedMesh *dm)
{
	CDDerivedMesh *cddm = (CDDerivedMesh*)dm;
	CustomData edgeData;
	EdgeHashIterator *ehi;
	MFace *mf = cddm->mface;
	MEdge *med;
	EdgeHash *eh = BLI_edgehash_new();
	int i, *index, numEdges, maxFaces = dm->numFaceData;

	for (i = 0; i < maxFaces; i++, mf++) {
		if (!BLI_edgehash_haskey(eh, mf->v1, mf->v2))
			BLI_edgehash_insert(eh, mf->v1, mf->v2, NULL);
		if (!BLI_edgehash_haskey(eh, mf->v2, mf->v3))
			BLI_edgehash_insert(eh, mf->v2, mf->v3, NULL);
		
		if (mf->v4) {
			if (!BLI_edgehash_haskey(eh, mf->v3, mf->v4))
				BLI_edgehash_insert(eh, mf->v3, mf->v4, NULL);
			if (!BLI_edgehash_haskey(eh, mf->v4, mf->v1))
				BLI_edgehash_insert(eh, mf->v4, mf->v1, NULL);
		} else {
			if (!BLI_edgehash_haskey(eh, mf->v3, mf->v1))
				BLI_edgehash_insert(eh, mf->v3, mf->v1, NULL);
		}
	}

	numEdges = BLI_edgehash_size(eh);

	/* write new edges into a temporary CustomData */
	memset(&edgeData, 0, sizeof(edgeData));
	CustomData_add_layer(&edgeData, CD_MEDGE, CD_CALLOC, NULL, numEdges);
	CustomData_add_layer(&edgeData, CD_ORIGINDEX, CD_CALLOC, NULL, numEdges);

	ehi = BLI_edgehashIterator_new(eh);
	med = CustomData_get_layer(&edgeData, CD_MEDGE);
	index = CustomData_get_layer(&edgeData, CD_ORIGINDEX);
	for(i = 0; !BLI_edgehashIterator_isDone(ehi);
		BLI_edgehashIterator_step(ehi), ++i, ++med, ++index) {
		BLI_edgehashIterator_getKey(ehi, (int*)&med->v1, (int*)&med->v2);

		med->flag = ME_EDGEDRAW|ME_EDGERENDER;
		*index = ORIGINDEX_NONE;
	}
	BLI_edgehashIterator_free(ehi);

	/* free old CustomData and assign new one */
	CustomData_free(&dm->edgeData, dm->numEdgeData);
	dm->edgeData = edgeData;
	dm->numEdgeData = numEdges;

	cddm->medge = CustomData_get_layer(&dm->edgeData, CD_MEDGE);

	BLI_edgehash_free(eh, NULL);
}

void CDDM_lower_num_verts(DerivedMesh *dm, int numVerts)
{
	if (numVerts < dm->numVertData)
		CustomData_free_elem(&dm->vertData, numVerts, dm->numVertData-numVerts);

	dm->numVertData = numVerts;
}

void CDDM_lower_num_edges(DerivedMesh *dm, int numEdges)
{
	if (numEdges < dm->numEdgeData)
		CustomData_free_elem(&dm->edgeData, numEdges, dm->numEdgeData-numEdges);

	dm->numEdgeData = numEdges;
}

void CDDM_lower_num_faces(DerivedMesh *dm, int numFaces)
{
	if (numFaces < dm->numFaceData)
		CustomData_free_elem(&dm->faceData, numFaces, dm->numFaceData-numFaces);

	dm->numFaceData = numFaces;
}

MVert *CDDM_get_vert(DerivedMesh *dm, int index)
{
	return &((CDDerivedMesh*)dm)->mvert[index];
}

MEdge *CDDM_get_edge(DerivedMesh *dm, int index)
{
	return &((CDDerivedMesh*)dm)->medge[index];
}

MFace *CDDM_get_face(DerivedMesh *dm, int index)
{
	return &((CDDerivedMesh*)dm)->mface[index];
}

MVert *CDDM_get_verts(DerivedMesh *dm)
{
	return ((CDDerivedMesh*)dm)->mvert;
}

MEdge *CDDM_get_edges(DerivedMesh *dm)
{
	return ((CDDerivedMesh*)dm)->medge;
}

MFace *CDDM_get_faces(DerivedMesh *dm)
{
	return ((CDDerivedMesh*)dm)->mface;
}

