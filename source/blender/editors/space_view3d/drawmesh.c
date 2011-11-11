/*
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
 * Contributor(s): Blender Foundation, full update, glsl support
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_view3d/drawmesh.c
 *  \ingroup spview3d
 */

#include <string.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"
#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_edgehash.h"
#include "BLI_editVert.h"
#include "BLI_utildefines.h"

#include "DNA_material_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_property_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_view3d_types.h"
#include "DNA_windowmanager_types.h"

#include "BKE_DerivedMesh.h"
#include "BKE_effect.h"
#include "BKE_image.h"
#include "BKE_material.h"
#include "BKE_paint.h"
#include "BKE_property.h"
#include "BKE_tessmesh.h"
#include "BKE_scene.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "UI_resources.h"

#include "GPU_buffers.h"
#include "GPU_extensions.h"
#include "GPU_draw.h"
#include "GPU_material.h"

#include "ED_mesh.h"
#include "ED_uvedit.h"

#include "view3d_intern.h"	// own include

/**************************** Face Select Mode *******************************/

/* Flags for marked edges */
enum {
	eEdge_Visible = (1<<0),
	eEdge_Select = (1<<1),
};

/* Creates a hash of edges to flags indicating selected/visible */
static void get_marked_edge_info__orFlags(EdgeHash *eh, int v0, int v1, int flags)
{
	int *flags_p;

	if(!BLI_edgehash_haskey(eh, v0, v1))
		BLI_edgehash_insert(eh, v0, v1, NULL);

	flags_p = (int*) BLI_edgehash_lookup_p(eh, v0, v1);
	*flags_p |= flags;
}

static EdgeHash *get_tface_mesh_marked_edge_info(Mesh *me)
{
	EdgeHash *eh = BLI_edgehash_new();
	MFace *mf;
	int i;
	
	for(i=0; i<me->totface; i++) {
		mf = &me->mface[i];

		if(!(mf->flag & ME_HIDE)) {
			unsigned int flags = eEdge_Visible;
			if(mf->flag & ME_FACE_SEL) flags |= eEdge_Select;

			get_marked_edge_info__orFlags(eh, mf->v1, mf->v2, flags);
			get_marked_edge_info__orFlags(eh, mf->v2, mf->v3, flags);

			if(mf->v4) {
				get_marked_edge_info__orFlags(eh, mf->v3, mf->v4, flags);
				get_marked_edge_info__orFlags(eh, mf->v4, mf->v1, flags);
			}
			else
				get_marked_edge_info__orFlags(eh, mf->v3, mf->v1, flags);
		}
	}

	return eh;
}


static int draw_mesh_face_select__setHiddenOpts(void *userData, int index)
{
	struct { Mesh *me; EdgeHash *eh; } *data = userData;
	Mesh *me= data->me;
	MEdge *med = &me->medge[index];
	uintptr_t flags = (intptr_t) BLI_edgehash_lookup(data->eh, med->v1, med->v2);

	if(me->drawflag & ME_DRAWEDGES) { 
		if(me->drawflag & ME_HIDDENEDGES)
			return 1;
		else
			return (flags & eEdge_Visible);
	}
	else
		return (flags & eEdge_Select);
}

static int draw_mesh_face_select__setSelectOpts(void *userData, int index)
{
	struct { Mesh *me; EdgeHash *eh; } *data = userData;
	MEdge *med = &data->me->medge[index];
	uintptr_t flags = (intptr_t) BLI_edgehash_lookup(data->eh, med->v1, med->v2);

	return flags & eEdge_Select;
}

/* draws unselected */
static int draw_mesh_face_select__drawFaceOptsInv(void *userData, int index)
{
	Mesh *me = (Mesh*)userData;

	MFace *mface = &me->mface[index];
	if(!(mface->flag&ME_HIDE) && !(mface->flag&ME_FACE_SEL))
		return 2; /* Don't set color */
	else
		return 0;
}

static void draw_mesh_face_select(RegionView3D *rv3d, Mesh *me, DerivedMesh *dm)
{
	struct { Mesh *me; EdgeHash *eh; } data;

	data.me = me;
	data.eh = get_tface_mesh_marked_edge_info(me);

	glEnable(GL_DEPTH_TEST);
	glDisable(GL_LIGHTING);
	bglPolygonOffset(rv3d->dist, 1.0);

	/* Draw (Hidden) Edges */
	setlinestyle(1);
	UI_ThemeColor(TH_EDGE_FACESEL);
	dm->drawMappedEdges(dm, draw_mesh_face_select__setHiddenOpts, &data);
	setlinestyle(0);

	/* Draw Selected Faces */
	if(me->drawflag & ME_DRAWFACES) {
		glEnable(GL_BLEND);
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
		/* dull unselected faces so as not to get in the way of seeing color */
		glColor4ub(96, 96, 96, 64);
		dm->drawMappedFacesTex(dm, draw_mesh_face_select__drawFaceOptsInv, (void*)me);
		
		glDisable(GL_BLEND);
	}
	
	bglPolygonOffset(rv3d->dist, 1.0);

		/* Draw Stippled Outline for selected faces */
	glColor3ub(255, 255, 255);
	setlinestyle(1);
	dm->drawMappedEdges(dm, draw_mesh_face_select__setSelectOpts, &data);
	setlinestyle(0);

	bglPolygonOffset(rv3d->dist, 0.0);	// resets correctly now, even after calling accumulated offsets

	BLI_edgehash_free(data.eh, NULL);
}

/***************************** Texture Drawing ******************************/

static Material *give_current_material_or_def(Object *ob, int matnr)
{
	extern Material defmaterial;	// render module abuse...
	Material *ma= give_current_material(ob, matnr);

	return ma?ma:&defmaterial;
}

/* Icky globals, fix with userdata parameter */

static struct TextureDrawState {
	Object *ob;
	int islit, istex;
	int color_profile;
	unsigned char obcol[4];
} Gtexdraw = {NULL, 0, 0, 0, {0, 0, 0, 0}};

static int set_draw_settings_cached(int clearcache, MTFace *texface, Material *ma, struct TextureDrawState gtexdraw)
{
	static Material *c_ma;
	static int c_textured;
	static MTFace *c_texface;
	static int c_backculled;
	static int c_badtex;
	static int c_lit;

	Object *litob = NULL; //to get mode to turn off mipmap in painting mode
	int backculled = GEMAT_BACKCULL;
	int alphablend = 0;
	int textured = 0;
	int lit = 0;
	
	if (clearcache) {
		c_textured= c_lit= c_backculled= -1;
		c_texface= (MTFace*) -1;
		c_badtex= 0;
	} else {
		textured = gtexdraw.istex;
		litob = gtexdraw.ob;
	}

	/* convert number of lights into boolean */
	if (gtexdraw.islit) lit = 1;

	if (ma) {
		alphablend = ma->game.alpha_blend;
		if (ma->mode & MA_SHLESS) lit = 0;
		backculled = ma->game.flag & GEMAT_BACKCULL;
	}

	if (texface) {
		textured = textured && (texface->tpage);

		/* no material, render alpha if texture has depth=32 */
		if (!ma && BKE_image_has_alpha(texface->tpage))
			alphablend = GPU_BLEND_ALPHA;
	}

	else
		textured = 0;

	if (backculled!=c_backculled) {
		if (backculled) glEnable(GL_CULL_FACE);
		else glDisable(GL_CULL_FACE);

		c_backculled= backculled;
	}

	if (textured!=c_textured || texface!=c_texface) {
		if (textured ) {
			c_badtex= !GPU_set_tpage(texface, !(litob->mode & OB_MODE_TEXTURE_PAINT), alphablend);
		} else {
			GPU_set_tpage(NULL, 0, 0);
			c_badtex= 0;
		}
		c_textured= textured;
		c_texface= texface;
	}

	if (c_badtex) lit= 0;
	if (lit!=c_lit || ma!=c_ma) {
		if (lit) {
			float spec[4];
			if (!ma)ma= give_current_material_or_def(NULL, 0); //default material

			spec[0]= ma->spec*ma->specr;
			spec[1]= ma->spec*ma->specg;
			spec[2]= ma->spec*ma->specb;
			spec[3]= 1.0;

			glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, spec);
			glColorMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE);
			glMateriali(GL_FRONT_AND_BACK, GL_SHININESS, CLAMPIS(ma->har, 0, 128));
			glEnable(GL_LIGHTING);
			glEnable(GL_COLOR_MATERIAL);
		}
		else {
			glDisable(GL_LIGHTING); 
			glDisable(GL_COLOR_MATERIAL);
		}
		c_lit= lit;
	}

	return c_badtex;
}

static void draw_textured_begin(Scene *scene, View3D *v3d, RegionView3D *rv3d, Object *ob)
{
	unsigned char obcol[4];
	int istex, solidtex;

	// XXX scene->obedit warning

	/* texture draw is abused for mask selection mode, do this so wire draw
	 * with face selection in weight paint is not lit. */
	if((v3d->drawtype <= OB_WIRE) && (ob->mode & OB_MODE_WEIGHT_PAINT)) {
		solidtex= FALSE;
		Gtexdraw.islit= 0;
	}
	else if(v3d->drawtype==OB_SOLID || ((ob->mode & OB_MODE_EDIT) && v3d->drawtype!=OB_TEXTURE)) {
		/* draw with default lights in solid draw mode and edit mode */
		solidtex= TRUE;
		Gtexdraw.islit= -1;
	}
	else {
		/* draw with lights in the scene otherwise */
		solidtex= FALSE;
		Gtexdraw.islit= GPU_scene_object_lights(scene, ob, v3d->lay, rv3d->viewmat, !rv3d->is_persp);
	}
	
	obcol[0]= CLAMPIS(ob->col[0]*255, 0, 255);
	obcol[1]= CLAMPIS(ob->col[1]*255, 0, 255);
	obcol[2]= CLAMPIS(ob->col[2]*255, 0, 255);
	obcol[3]= CLAMPIS(ob->col[3]*255, 0, 255);
	
	glCullFace(GL_BACK); glEnable(GL_CULL_FACE);
	if(solidtex || v3d->drawtype==OB_TEXTURE) istex= 1;
	else istex= 0;

	Gtexdraw.ob = ob;
	Gtexdraw.istex = istex;
	Gtexdraw.color_profile = scene->r.color_mgt_flag & R_COLOR_MANAGEMENT;
	memcpy(Gtexdraw.obcol, obcol, sizeof(obcol));
	set_draw_settings_cached(1, NULL, NULL, Gtexdraw);
	glShadeModel(GL_SMOOTH);
}

static void draw_textured_end(void)
{
	/* switch off textures */
	GPU_set_tpage(NULL, 0, 0);

	glShadeModel(GL_FLAT);
	glDisable(GL_CULL_FACE);

	/* XXX, bad patch - GPU_default_lights() calls
	 * glLightfv(GL_LIGHT_POSITION, ...) which
	 * is transformed by the current matrix... we
	 * need to make sure that matrix is identity.
	 * 
	 * It would be better if drawmesh.c kept track
	 * of and restored the light settings it changed.
	 *  - zr
	 */
	glPushMatrix();
	glLoadIdentity();	
	GPU_default_lights();
	glPopMatrix();
}

static int draw_tface__set_draw_legacy(MTFace *tface, int has_mcol, int matnr)
{
	Material *ma= give_current_material(Gtexdraw.ob, matnr+1);
	int validtexture=0;

	if (ma && (ma->game.flag & GEMAT_INVISIBLE)) return 0;

	validtexture = set_draw_settings_cached(0, tface, ma, Gtexdraw);

	if (tface && validtexture) {
		glColor3ub(0xFF, 0x00, 0xFF);
		return 2; /* Don't set color */
	} else if (ma && ma->shade_flag&MA_OBCOLOR) {
		glColor3ubv(Gtexdraw.obcol);
		return 2; /* Don't set color */
	} else if (!has_mcol) {
		if (tface) glColor3f(1.0, 1.0, 1.0);
		else {
			if(ma) {
				float col[3];
				if(Gtexdraw.color_profile) linearrgb_to_srgb_v3_v3(col, &ma->r);
				else copy_v3_v3(col, &ma->r);
				
				glColor3fv(col);
			}
			else glColor3f(1.0, 1.0, 1.0);
		}
		return 2; /* Don't set color */
	} else {
		return 1; /* Set color from mcol */
	}
}

static int draw_mcol__set_draw_legacy(MTFace *UNUSED(tface), int has_mcol, int UNUSED(matnr))
{
	if (has_mcol) return 1;
	else return 2;
}

static int draw_tface__set_draw(MTFace *tface, int has_mcol, int matnr)
{
	Material *ma= give_current_material(Gtexdraw.ob, matnr+1);

	if (ma && (ma->game.flag & GEMAT_INVISIBLE)) return 0;

	if (tface && set_draw_settings_cached(0, tface, ma, Gtexdraw)) {
		return 2; /* Don't set color */
	} else if (tface && tface->mode&TF_OBCOL) {
		return 2; /* Don't set color */
	} else if (!has_mcol) {
		return 1; /* Don't set color */
	} else {
		return 1; /* Set color from mcol */
	}
}
static void add_tface_color_layer(DerivedMesh *dm)
{
	MTFace *tface = DM_get_face_data_layer(dm, CD_MTFACE);
	MFace *mface = dm->getTessFaceArray(dm);
	MCol *finalCol;
	int i,j;
	MCol *mcol = dm->getTessFaceDataArray(dm, CD_WEIGHT_MCOL);
	if(!mcol)
		mcol = dm->getTessFaceDataArray(dm, CD_MCOL);

	finalCol = MEM_mallocN(sizeof(MCol)*4*dm->getNumTessFaces(dm),"add_tface_color_layer");
	for(i=0;i<dm->getNumTessFaces(dm);i++) {
		Material *ma= give_current_material(Gtexdraw.ob, mface[i].mat_nr+1);

		if (ma && (ma->game.flag&GEMAT_INVISIBLE)) {
			if( mcol )
				memcpy(&finalCol[i*4],&mcol[i*4],sizeof(MCol)*4);
			else
				for(j=0;j<4;j++) {
					finalCol[i*4+j].b = 255;
					finalCol[i*4+j].g = 255;
					finalCol[i*4+j].r = 255;
				}
		}
		else if (tface && mface && set_draw_settings_cached(0, tface, ma, Gtexdraw)) {
			for(j=0;j<4;j++) {
				finalCol[i*4+j].b = 255;
				finalCol[i*4+j].g = 0;
				finalCol[i*4+j].r = 255;
			}
		} else if (tface && tface->mode&TF_OBCOL) {
			for(j=0;j<4;j++) {
				finalCol[i*4+j].b = FTOCHAR(Gtexdraw.obcol[0]);
				finalCol[i*4+j].g = FTOCHAR(Gtexdraw.obcol[1]);
				finalCol[i*4+j].r = FTOCHAR(Gtexdraw.obcol[2]);
			}
		} else if (!mcol) {
			if (tface) {
				for(j=0;j<4;j++) {
					finalCol[i*4+j].b = 255;
					finalCol[i*4+j].g = 255;
					finalCol[i*4+j].r = 255;
				}
			}
			else {
				float col[3];
				Material *ma= give_current_material(Gtexdraw.ob, mface[i].mat_nr+1);
				
				if(ma) {
					if(Gtexdraw.color_profile) linearrgb_to_srgb_v3_v3(col, &ma->r);
					else copy_v3_v3(col, &ma->r);
					
					for(j=0;j<4;j++) {
						finalCol[i*4+j].b = FTOCHAR(col[0]);
						finalCol[i*4+j].g = FTOCHAR(col[1]);
						finalCol[i*4+j].r = FTOCHAR(col[2]);
					}
				}
				else
					for(j=0;j<4;j++) {
						finalCol[i*4+j].b = 255;
						finalCol[i*4+j].g = 255;
						finalCol[i*4+j].r = 255;
					}
			}
		} else {
			for(j=0;j<4;j++) {
				finalCol[i*4+j].r = mcol[i*4+j].r;
				finalCol[i*4+j].g = mcol[i*4+j].g;
				finalCol[i*4+j].b = mcol[i*4+j].b;
			}
		}
	}
	CustomData_add_layer( &dm->faceData, CD_TEXTURE_MCOL, CD_ASSIGN, finalCol, dm->numFaceData );
}

static int draw_tface_mapped__set_draw(void *userData, int index)
{
	Mesh *me = (Mesh*)userData;
	MTexPoly *tpoly = (me->mtpoly)? &me->mtpoly[index]: NULL;
	MPoly *mpoly = (me->mpoly)? &me->mpoly[index]: NULL;
	MTFace mtf;
	int matnr = me->mpoly[index].mat_nr;

	if (mpoly && mpoly->flag&ME_HIDE) return 0;

	memset(&mtf, 0, sizeof(mtf));
	if (tpoly) {
		mtf.flag = tpoly->flag;
		mtf.tpage = tpoly->tpage;
		mtf.transp = tpoly->transp;
		mtf.mode = tpoly->mode;
		mtf.tile = tpoly->tile;
		mtf.unwrap = tpoly->unwrap;
	}

	return draw_tface__set_draw(&mtf, (me->mcol != NULL), matnr);
}

static int draw_em_tf_mapped__set_draw(void *userData, int index)
{
	struct {BMEditMesh *em; short has_mcol; short has_mtface;} *data = userData;
	BMEditMesh *em = data->em;
	BMFace *efa= EDBM_get_face_for_index(em, index);

	if (efa==NULL || BM_TestHFlag(efa, BM_HIDDEN)) {
		return 0;
	}
	else {
		MTFace mtf= {{{0}}};
		int matnr = efa->mat_nr;

		if (data->has_mtface) {
			MTexPoly *tpoly = CustomData_bmesh_get(&em->bm->pdata, efa->head.data, CD_MTEXPOLY);
			mtf.flag = tpoly->flag;
			mtf.tpage = tpoly->tpage;
			mtf.transp = tpoly->transp;
			mtf.mode = tpoly->mode;
			mtf.tile = tpoly->tile;
			mtf.unwrap = tpoly->unwrap;

		}

		return draw_tface__set_draw_legacy(&mtf, data->has_mcol, matnr);
	}
}

static int wpaint__setSolidDrawOptions(void *userData, int index, int *drawSmooth_r)
{
	Mesh *me = (Mesh*)userData;

	if (me->mat && me->mface) {
		Material *ma= me->mat[me->mface[index].mat_nr];
		if (ma && (ma->game.flag & GEMAT_INVISIBLE)) {
			return 0;
		}
	}

	*drawSmooth_r = 1;
	return 1;
}

static void draw_mesh_text(Scene *scene, Object *ob, int glsl)
{
	Mesh *me = ob->data;
	DerivedMesh *ddm;
	MFace *mf, *mface= me->mface;
	MTFace *tface= me->mtface;
	MCol *mcol= me->mcol;	/* why does mcol exist? */
	bProperty *prop = get_ob_property(ob, "Text");
	GPUVertexAttribs gattribs;
	int a, totface= me->totface;

	/* don't draw without tfaces */
	if(!tface)
		return;

	/* don't draw when editing */
	if(ob->mode & OB_MODE_EDIT)
		return;
	else if(ob==OBACT)
		if(paint_facesel_test(ob) || paint_vertsel_test(ob))
			return;

	ddm = mesh_get_derived_deform(scene, ob, CD_MASK_BAREMESH);

	for(a=0, mf=mface; a<totface; a++, tface++, mf++) {
		short matnr= mf->mat_nr;
		int mf_smooth= mf->flag & ME_SMOOTH;
		Material *mat = me->mat[matnr];
		int mode= mat->game.flag;

		if (!(mode&GEMAT_INVISIBLE) && (mode&GEMAT_TEXT)) {
			float v1[3], v2[3], v3[3], v4[3];
			char string[MAX_PROPSTRING];
			int characters, i, glattrib= -1, badtex= 0;

			if(glsl) {
				GPU_enable_material(matnr+1, &gattribs);

				for(i=0; i<gattribs.totlayer; i++) {
					if(gattribs.layer[i].type == CD_MTFACE) {
						glattrib = gattribs.layer[i].glindex;
						break;
					}
				}
			}
			else {
				badtex = set_draw_settings_cached(0, tface, mat, Gtexdraw);
				if (badtex) {
					if (mcol) mcol+=4;
					continue;
				}
			}

			ddm->getVertCo(ddm, mf->v1, v1);
			ddm->getVertCo(ddm, mf->v2, v2);
			ddm->getVertCo(ddm, mf->v3, v3);
			if (mf->v4) ddm->getVertCo(ddm, mf->v4, v4);

			// The BM_FONT handling is in the gpu module, shared with the
			// game engine, was duplicated previously

			set_property_valstr(prop, string);
			characters = strlen(string);
			
			if(!BKE_image_get_ibuf(tface->tpage, NULL))
				characters = 0;

			if (!mf_smooth) {
				float nor[3];

				normal_tri_v3( nor,v1, v2, v3);

				glNormal3fv(nor);
			}

			GPU_render_text(tface, mode, string, characters,
				(unsigned int*)mcol, v1, v2, v3, (mf->v4? v4: NULL), glattrib);
		}
		if (mcol) {
			mcol+=4;
		}
	}

	ddm->release(ddm);
}

void draw_mesh_textured_old(Scene *scene, View3D *v3d, RegionView3D *rv3d, Object *ob, DerivedMesh *dm, int draw_flags)
{
	Mesh *me= ob->data;
	
	/* correct for negative scale */
	if(ob->transflag & OB_NEG_SCALE) glFrontFace(GL_CW);
	else glFrontFace(GL_CCW);
	
	/* draw the textured mesh */
	draw_textured_begin(scene, v3d, rv3d, ob);

	glColor4f(1.0f,1.0f,1.0f,1.0f);

	if(ob->mode & OB_MODE_EDIT) {
		struct {BMEditMesh *em; short has_mcol; short has_mtface;} data;

		data.em= me->edit_btmesh;
		data.has_mcol= CustomData_has_layer(&me->edit_btmesh->bm->ldata, CD_MLOOPCOL);
		data.has_mtface= CustomData_has_layer(&me->edit_btmesh->bm->pdata, CD_MTEXPOLY);

		dm->drawMappedFacesTex(dm, draw_em_tf_mapped__set_draw, &data);
	}
	else if(draw_flags & DRAW_FACE_SELECT) {
		if(ob->mode & OB_MODE_WEIGHT_PAINT)
			dm->drawMappedFaces(dm, wpaint__setSolidDrawOptions, me, 1, GPU_enable_material, NULL);
		else
			dm->drawMappedFacesTex(dm, me->mface ? draw_tface_mapped__set_draw : NULL, me);
	}
	else {
		if(GPU_buffer_legacy(dm)) {
			if (draw_flags & DRAW_DYNAMIC_PAINT_PREVIEW)
				dm->drawFacesTex(dm, draw_mcol__set_draw_legacy);
			else 
				dm->drawFacesTex(dm, draw_tface__set_draw_legacy);
		}
		else {
			if(!CustomData_has_layer(&dm->faceData,CD_TEXTURE_MCOL))
				add_tface_color_layer(dm);

			dm->drawFacesTex(dm, draw_tface__set_draw);
		}
	}

	/* draw game engine text hack */
	if(get_ob_property(ob, "Text")) 
		draw_mesh_text(scene, ob, 0);

	draw_textured_end();
	
	/* draw edges and selected faces over textured mesh */
	if(!(ob == scene->obedit) && (draw_flags & DRAW_FACE_SELECT))
		draw_mesh_face_select(rv3d, me, dm);

	/* reset from negative scale correction */
	glFrontFace(GL_CCW);
	
	/* in editmode, the blend mode needs to be set incase it was ADD */
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
}

/************************** NEW SHADING NODES ********************************/

typedef struct TexMatCallback {
	Scene *scene;
	Object *ob;
	Mesh *me;
	DerivedMesh *dm;
} TexMatCallback;

static void tex_mat_set_material_cb(void *UNUSED(userData), int mat_nr, void *attribs)
{
	/* all we have to do here is simply enable the GLSL material, but note
	   that the GLSL code will give different result depending on the drawtype,
	   in texture draw mode it will output the active texture node, in material
	   draw mode it will show the full material. */
	GPU_enable_material(mat_nr, attribs);
}

static void tex_mat_set_texture_cb(void *userData, int mat_nr, void *attribs)
{
	/* texture draw mode without GLSL */
	TexMatCallback *data= (TexMatCallback*)userData;
	GPUVertexAttribs *gattribs = attribs;
	Image *ima;
	ImageUser *iuser;
	bNode *node;
	int texture_set= 0;

	/* draw image texture if we find one */
	if(ED_object_get_active_image(data->ob, mat_nr, &ima, &iuser, &node)) {
		/* get openl texture */
		int mipmap= 1;
		int bindcode= (ima)? GPU_verify_image(ima, iuser, 0, 0, mipmap): 0;
		float zero[4] = {0.0f, 0.0f, 0.0f, 0.0f};

		if(bindcode) {
			NodeTexBase *texbase= node->storage;

			/* disable existing material */
			GPU_disable_material();
			glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, zero);
			glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, zero);
			glMateriali(GL_FRONT_AND_BACK, GL_SHININESS, 0);

			/* bind texture */
			glEnable(GL_COLOR_MATERIAL);
			glEnable(GL_TEXTURE_2D);

			glBindTexture(GL_TEXTURE_2D, ima->bindcode);
			glColor3f(1.0f, 1.0f, 1.0f);

			glMatrixMode(GL_TEXTURE);
			glLoadMatrixf(texbase->tex_mapping.mat);
			glMatrixMode(GL_MODELVIEW);

			/* use active UV texture layer */
			memset(gattribs, 0, sizeof(*gattribs));

			gattribs->layer[0].type= CD_MTFACE;
			gattribs->layer[0].name[0]= '\0';
			gattribs->layer[0].gltexco= 1;
			gattribs->totlayer= 1;

			texture_set= 1;
		}
	}

	if(!texture_set) {
		glMatrixMode(GL_TEXTURE);
		glLoadIdentity();
		glMatrixMode(GL_MODELVIEW);

		/* disable texture */
		glDisable(GL_TEXTURE_2D);
		glDisable(GL_COLOR_MATERIAL);

		/* draw single color */
		GPU_enable_material(mat_nr, attribs);
	}
}

static int tex_mat_set_face_mesh_cb(void *userData, int index)
{
	/* faceselect mode face hiding */
	TexMatCallback *data= (TexMatCallback*)userData;
	Mesh *me = (Mesh*)data->me;
	MFace *mface = &me->mface[index];

	return !(mface->flag & ME_HIDE);
}

static int tex_mat_set_face_editmesh_cb(void *userData, int index)
{
	/* editmode face hiding */
	TexMatCallback *data= (TexMatCallback*)userData;
	Mesh *me = (Mesh*)data->me;
	BMFace *efa= EDBM_get_face_for_index(me->edit_btmesh, index);

	return !BM_TestHFlag(efa, BM_HIDDEN);
}

void draw_mesh_textured(Scene *scene, View3D *v3d, RegionView3D *rv3d, Object *ob, DerivedMesh *dm, int draw_flags)
{
	if((!scene_use_new_shading_nodes(scene)) || (draw_flags & DRAW_DYNAMIC_PAINT_PREVIEW)) {
		draw_mesh_textured_old(scene, v3d, rv3d, ob, dm, draw_flags);
		return;
	}

	/* set opengl state for negative scale & color */
	if(ob->transflag & OB_NEG_SCALE) glFrontFace(GL_CW);
	else glFrontFace(GL_CCW);

	glEnable(GL_LIGHTING);

	if(ob->mode & OB_MODE_WEIGHT_PAINT) {
		/* weight paint mode exception */
		int useColors= 1;

		dm->drawMappedFaces(dm, wpaint__setSolidDrawOptions,
			ob->data, useColors, GPU_enable_material, NULL);
	}
	else {
		Mesh *me= ob->data;
		TexMatCallback data = {scene, ob, me, dm};
		int (*set_face_cb)(void*, int);
		int glsl;
		
		/* face hiding callback depending on mode */
		if(ob == scene->obedit)
			set_face_cb= tex_mat_set_face_editmesh_cb;
		else if(draw_flags & DRAW_FACE_SELECT)
			set_face_cb= tex_mat_set_face_mesh_cb;
		else
			set_face_cb= NULL;

		/* test if we can use glsl */
		glsl= (v3d->drawtype == OB_MATERIAL) && GPU_glsl_support();

		GPU_begin_object_materials(v3d, rv3d, scene, ob, glsl, NULL);

		if(glsl) {
			/* draw glsl */
			dm->drawMappedFacesMat(dm,
				tex_mat_set_material_cb,
				set_face_cb, &data);
		}
		else {
			float zero[4] = {0.0f, 0.0f, 0.0f, 0.0f};

			/* draw textured */
			glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, zero);
			glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, zero);
			glMateriali(GL_FRONT_AND_BACK, GL_SHININESS, 0);

			dm->drawMappedFacesMat(dm,
				tex_mat_set_texture_cb,
				set_face_cb, &data);
		}

		GPU_end_object_materials();
	}

	/* reset opengl state */
	glDisable(GL_COLOR_MATERIAL);
	glDisable(GL_TEXTURE_2D);
	glDisable(GL_LIGHTING);
	glBindTexture(GL_TEXTURE_2D, 0);
	glFrontFace(GL_CCW);

	glMatrixMode(GL_TEXTURE);
	glLoadIdentity();
	glMatrixMode(GL_MODELVIEW);

	/* faceselect mode drawing over textured mesh */
	if(!(ob == scene->obedit) && (draw_flags & DRAW_FACE_SELECT))
		draw_mesh_face_select(rv3d, ob->data, dm);
}

