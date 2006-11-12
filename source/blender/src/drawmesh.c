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
#include <math.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_edgehash.h"

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "DNA_image_types.h"
#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_property_types.h"
#include "DNA_scene_types.h"
#include "DNA_view3d_types.h"

#include "BKE_bmfont.h"
#include "BKE_displist.h"
#include "BKE_DerivedMesh.h"
#include "BKE_effect.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_mesh.h"
#include "BKE_object.h"
#include "BKE_property.h"
#include "BKE_utildefines.h"

#include "BIF_resources.h"
#include "BIF_gl.h"
#include "BIF_glutil.h"
#include "BIF_mywindow.h"
#include "BIF_resources.h"

#include "BDR_editface.h"
#include "BDR_vpaint.h"
#include "BDR_drawmesh.h"

#include "BSE_drawview.h"

#include "blendef.h"
#include "nla.h"

//#include "glext.h"
/* some local functions */
#if defined(GL_EXT_texture_object) && (!defined(__sun__) || (!defined(__sun))) && !defined(__APPLE__) && !defined(__linux__) && !defined(WIN32)
	#define glBindTexture(A,B)     glBindTextureEXT(A,B)
	#define glGenTextures(A,B)     glGenTexturesEXT(A,B)
	#define glDeleteTextures(A,B)  glDeleteTexturesEXT(A,B)
	#define glPolygonOffset(A,B)  glPolygonOffsetEXT(A,B)

#else

/* #define GL_FUNC_ADD_EXT					GL_FUNC_ADD */
/* #define GL_FUNC_REVERSE_SUBTRACT_EXT	GL_FUNC_REVERSE_SUBTRACT */
/* #define GL_POLYGON_OFFSET_EXT			GL_POLYGON_OFFSET */

#endif

	/* (n&(n-1)) zeros the least significant bit of n */
static int is_pow2(int num) {
	return ((num)&(num-1))==0;
}
static int smaller_pow2(int num) {
	while (!is_pow2(num))
		num= num&(num-1);
	return num;	
}

static int fCurtile=0, fCurmode=0,fCurtileXRep=0,fCurtileYRep=0;
static Image *fCurpage=0;
static short fTexwindx, fTexwindy, fTexwinsx, fTexwinsy;
static int fDoMipMap = 1;
static int fLinearMipMap = 0;

/* local prototypes --------------- */
void update_realtime_textures(void);


/*  static int source, dest; also not used */

/**
 * Enables or disable mipmapping for realtime images.
 * @param mipmap Turn mipmapping on (mipmap!=0) or off (mipmap==0).
 */
void set_mipmap(int mipmap)
{
	if (fDoMipMap != (mipmap != 0)) {
		free_all_realtime_images();
		fDoMipMap = mipmap != 0;
	}
}


/**
 * Returns the current setting for mipmapping.
 */
int get_mipmap(void)
{
	return fDoMipMap;
}

/**
 * Enables or disable linear mipmap setting for realtime images (textures).
 * Note that this will will destroy all texture bindings in OpenGL.
 * @see free_realtime_image()
 * @param mipmap Turn linear mipmapping on (linear!=0) or off (linear==0).
 */
void set_linear_mipmap(int linear)
{
	if (fLinearMipMap != (linear != 0)) {
		free_all_realtime_images();
		fLinearMipMap = linear != 0;
	}
}

/**
 * Returns the current setting for linear mipmapping.
 */
int get_linear_mipmap(void)
{
	return fLinearMipMap;
}


/**
 * Resets the realtime image cache variables.
 */
void clear_realtime_image_cache()
{
	fCurpage = NULL;
	fCurtile = 0;
	fCurmode = 0;
	fCurtileXRep = 0;
	fCurtileYRep = 0;
}

/* REMEMBER!  Changes here must go into my_set_tpage() as well */
int set_tpage(TFace *tface)
{	
	static int alphamode= -1;
	static TFace *lasttface= 0;
	Image *ima;
	unsigned int *rect=NULL, *bind;
	int tpx=0, tpy=0, tilemode, tileXRep,tileYRep;
	
	/* disable */
	if(tface==0) {
		if(lasttface==0) return 0;
		
		lasttface= 0;
		fCurtile= 0;
		fCurpage= 0;
		if(fCurmode!=0) {
			glMatrixMode(GL_TEXTURE);
			glLoadIdentity();
			glMatrixMode(GL_MODELVIEW);
		}
		fCurmode= 0;
		fCurtileXRep=0;
		fCurtileYRep=0;
		alphamode= -1;
		
		glDisable(GL_BLEND);
		glDisable(GL_TEXTURE_2D);
		glDisable(GL_TEXTURE_GEN_S);
		glDisable(GL_TEXTURE_GEN_T);

		return 0;
	}
	lasttface= tface;

	if( alphamode != tface->transp) {
		alphamode= tface->transp;

		if(alphamode) {
			glEnable(GL_BLEND);
			
			if(alphamode==TF_ADD) {
				glBlendFunc(GL_ONE, GL_ONE);
			/* 	glBlendEquationEXT(GL_FUNC_ADD_EXT); */
			}
			else if(alphamode==TF_ALPHA) {
				glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
			/* 	glBlendEquationEXT(GL_FUNC_ADD_EXT); */
			}
			/* else { */
			/* 	glBlendFunc(GL_ONE, GL_ONE); */
			/* 	glBlendEquationEXT(GL_FUNC_REVERSE_SUBTRACT_EXT); */
			/* } */
		}
		else glDisable(GL_BLEND);
	}

	ima= tface->tpage;

	/* Enable or disable reflection mapping */
	if (ima && (ima->flag & IMA_REFLECT)){

//		glActiveTextureARB(GL_TEXTURE0_ARB);
		glTexGeni(GL_S, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP);
		glTexGeni(GL_T, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP);

		glEnable(GL_TEXTURE_GEN_S);
		glEnable(GL_TEXTURE_GEN_T);

		/* Handle multitexturing here */
	}
	else{
		glDisable(GL_TEXTURE_GEN_S);
		glDisable(GL_TEXTURE_GEN_T);
	}

	tilemode= tface->mode & TF_TILES;
	tileXRep = 0;
	tileYRep = 0;
	if (ima)
	{
		tileXRep = ima->xrep;
		tileYRep = ima->yrep;
	}


	if(ima==fCurpage && fCurtile==tface->tile && tilemode==fCurmode && fCurtileXRep==tileXRep && fCurtileYRep == tileYRep) return ima!=0;

	if(tilemode!=fCurmode || fCurtileXRep!=tileXRep || fCurtileYRep != tileYRep)
	{
		glMatrixMode(GL_TEXTURE);
		glLoadIdentity();
		
		if(tilemode && ima!=0)
			glScalef(ima->xrep, ima->yrep, 1.0);

		glMatrixMode(GL_MODELVIEW);
	}

	if(ima==0 || ima->ok==0) {
		glDisable(GL_TEXTURE_2D);
		
		fCurtile= tface->tile;
		fCurpage= 0;
		fCurmode= tilemode;
		fCurtileXRep = tileXRep;
		fCurtileYRep = tileYRep;

		return 0;
	}

	if(ima->ibuf==0) {
		load_image(ima, IB_rect, G.sce, G.scene->r.cfra);

		if(ima->ibuf==0) {
			ima->ok= 0;

			fCurtile= tface->tile;
			fCurpage= 0;
			fCurmode= tilemode;
			fCurtileXRep = tileXRep;
			fCurtileYRep = tileYRep;
			
			glDisable(GL_TEXTURE_2D);
			return 0;
		}
	}

	if ((ima->ibuf->rect==NULL) && ima->ibuf->rect_float)
		IMB_rect_from_float(ima->ibuf);

	if(ima->tpageflag & IMA_TWINANIM) fCurtile= ima->lastframe;
	else fCurtile= tface->tile;

	if(tilemode) {

		if(ima->repbind==0) make_repbind(ima);
		
		if(fCurtile>=ima->totbind) fCurtile= 0;
		
		/* this happens when you change repeat buttons */
		if(ima->repbind) bind= ima->repbind+fCurtile;
		else bind= &ima->bindcode;
		
		if(*bind==0) {
			
			fTexwindx= ima->ibuf->x/ima->xrep;
			fTexwindy= ima->ibuf->y/ima->yrep;
			
			if(fCurtile>=ima->xrep*ima->yrep) fCurtile= ima->xrep*ima->yrep-1;
	
			fTexwinsy= fCurtile / ima->xrep;
			fTexwinsx= fCurtile - fTexwinsy*ima->xrep;
	
			fTexwinsx*= fTexwindx;
			fTexwinsy*= fTexwindy;
	
			tpx= fTexwindx;
			tpy= fTexwindy;

			rect= ima->ibuf->rect + fTexwinsy*ima->ibuf->x + fTexwinsx;
		}
	}
	else {
		bind= &ima->bindcode;
		
		if(*bind==0) {
			tpx= ima->ibuf->x;
			tpy= ima->ibuf->y;
			rect= ima->ibuf->rect;
		}
	}

	if(*bind==0) {
		int rectw= tpx, recth= tpy;
		unsigned int *tilerect= NULL, *scalerect= NULL;

		/*
		 * Maarten:
		 * According to Ton this code is not needed anymore. It was used only
		 * in really old Blenders.
		 * Reevan:
		 * Actually it is needed for backwards compatibility.  Simpledemo 6 does not display correctly without it.
		 */
#if 1
		if (tilemode) {
			int y;
				
			tilerect= MEM_mallocN(rectw*recth*sizeof(*tilerect), "tilerect");
			for (y=0; y<recth; y++) {
				unsigned int *rectrow= &rect[y*ima->ibuf->x];
				unsigned int *tilerectrow= &tilerect[y*rectw];
					
				memcpy(tilerectrow, rectrow, tpx*sizeof(*rectrow));
			}
				
			rect= tilerect;
		}
#endif
		if (!is_pow2(rectw) || !is_pow2(recth)) {
			rectw= smaller_pow2(rectw);
			recth= smaller_pow2(recth);
			
			scalerect= MEM_mallocN(rectw*recth*sizeof(*scalerect), "scalerect");
			gluScaleImage(GL_RGBA, tpx, tpy, GL_UNSIGNED_BYTE, rect, rectw, recth, GL_UNSIGNED_BYTE, scalerect);
			rect= scalerect;
		}

		glGenTextures(1, (GLuint *)bind);
		
		if((G.f & G_DEBUG) || !*bind) {
			GLenum error = glGetError();
			printf("Texture: %s\n", ima->id.name+2);
			printf("name: %d, tpx: %d\n", *bind, tpx);
			printf("tile: %d, mode: %d\n", fCurtile, tilemode);
			if (error)
				printf("error: %s\n", gluErrorString(error));
		}
		glBindTexture( GL_TEXTURE_2D, *bind);

		if (!fDoMipMap)
		{
			glTexImage2D(GL_TEXTURE_2D, 0,  GL_RGBA,  rectw, recth, 0, GL_RGBA, GL_UNSIGNED_BYTE, rect);
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
		} else
		{
			int minfilter= fLinearMipMap?GL_LINEAR_MIPMAP_LINEAR:GL_LINEAR_MIPMAP_NEAREST;
			
			gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, rectw, recth, GL_RGBA, GL_UNSIGNED_BYTE, rect);
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, minfilter);
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
		}

		glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
			
		if (tilerect)
			MEM_freeN(tilerect);
		if (scalerect)
			MEM_freeN(scalerect);
	}
	else glBindTexture( GL_TEXTURE_2D, *bind);
	
	tag_image_time(ima);

	glEnable(GL_TEXTURE_2D);

	fCurpage= ima;
	fCurmode= tilemode;
	fCurtileXRep = tileXRep;
	fCurtileYRep = tileYRep;

	return 1;
}

void update_realtime_image(Image *ima, int x, int y, int w, int h)
{
	if (ima->repbind || fDoMipMap || !ima->bindcode || !ima->ibuf ||
		(!is_pow2(ima->ibuf->x) || !is_pow2(ima->ibuf->y)) ||
		(w == 0) || (h == 0)) {
		/* these special cases require full reload still */
		free_realtime_image(ima);
	}
	else {
		int row_length = glaGetOneInteger(GL_UNPACK_ROW_LENGTH);
		int skip_pixels = glaGetOneInteger(GL_UNPACK_SKIP_PIXELS);
		int skip_rows = glaGetOneInteger(GL_UNPACK_SKIP_ROWS);

		if ((ima->ibuf->rect==NULL) && ima->ibuf->rect_float)
			IMB_rect_from_float(ima->ibuf);

		glBindTexture(GL_TEXTURE_2D, ima->bindcode);

		glPixelStorei(GL_UNPACK_ROW_LENGTH, ima->ibuf->x);
		glPixelStorei(GL_UNPACK_SKIP_PIXELS, x);
		glPixelStorei(GL_UNPACK_SKIP_ROWS, y);

		glTexSubImage2D(GL_TEXTURE_2D, 0, x, y, w, h, GL_RGBA,
			GL_UNSIGNED_BYTE, ima->ibuf->rect);

		glPixelStorei(GL_UNPACK_ROW_LENGTH, row_length);
		glPixelStorei(GL_UNPACK_SKIP_PIXELS, skip_pixels);
		glPixelStorei(GL_UNPACK_SKIP_ROWS, skip_rows);
	}
}

void free_realtime_image(Image *ima)
{
	if(ima->bindcode) {
		glDeleteTextures(1, (GLuint *)&ima->bindcode);
		ima->bindcode= 0;
	}
	if(ima->repbind) {
		glDeleteTextures(ima->totbind, (GLuint *)ima->repbind);
	
		MEM_freeN(ima->repbind);
		ima->repbind= NULL;
	}
}

void free_all_realtime_images(void)
{
	Image* ima;

	ima= G.main->image.first;
	while(ima) {
		free_realtime_image(ima);
		ima= ima->id.next;
	}
}

void make_repbind(Image *ima)
{
	if(ima==0 || ima->ibuf==0) return;

	if(ima->repbind) {
		glDeleteTextures(ima->totbind, (GLuint *)ima->repbind);
		MEM_freeN(ima->repbind);
		ima->repbind= 0;
	}
	ima->totbind= ima->xrep*ima->yrep;
	if(ima->totbind>1) {
		ima->repbind= MEM_callocN(sizeof(int)*ima->totbind, "repbind");
	}
}

void update_realtime_textures()
{
	Image *ima;
	
	ima= G.main->image.first;
	while(ima) {
		if(ima->tpageflag & IMA_TWINANIM) {
			if(ima->twend >= ima->xrep*ima->yrep) ima->twend= ima->xrep*ima->yrep-1;
		
			/* check: is bindcode not in the array? Free. (to do) */
			
			ima->lastframe++;
			if(ima->lastframe > ima->twend) ima->lastframe= ima->twsta;
			
		}
		ima= ima->id.next;
	}
}

/***/

	/* Flags for marked edges */
enum {
	eEdge_Visible = (1<<0),
	eEdge_Select = (1<<1),
	eEdge_Active = (1<<2),
	eEdge_SelectAndActive = (1<<3),
	eEdge_ActiveFirst = (1<<4),
	eEdge_ActiveLast = (1<<5)
};

	/* Creates a hash of edges to flags indicating
	 * adjacent tface select/active/etc flags.
	 */
static void get_marked_edge_info__orFlags(EdgeHash *eh, int v0, int v1, int flags)
{
	int *flags_p;

	if (!BLI_edgehash_haskey(eh, v0, v1)) {
		BLI_edgehash_insert(eh, v0, v1, 0);
	}

	flags_p = (int*) BLI_edgehash_lookup_p(eh, v0, v1);
	*flags_p |= flags;
}

EdgeHash *get_tface_mesh_marked_edge_info(Mesh *me)
{
	EdgeHash *eh = BLI_edgehash_new();
	int i;

	for (i=0; i<me->totface; i++) {
		MFace *mf = &me->mface[i];
		TFace *tf = &me->tface[i];
		
		if (mf->v3) {
			if (!(tf->flag&TF_HIDE)) {
				unsigned int flags = eEdge_Visible;
				if (tf->flag&TF_SELECT) flags |= eEdge_Select;
				if (tf->flag&TF_ACTIVE) {
					flags |= eEdge_Active;
					if (tf->flag&TF_SELECT) flags |= eEdge_SelectAndActive;
				}

				get_marked_edge_info__orFlags(eh, mf->v1, mf->v2, flags);
				get_marked_edge_info__orFlags(eh, mf->v2, mf->v3, flags);
				if (mf->v4) {
					get_marked_edge_info__orFlags(eh, mf->v3, mf->v4, flags);
					get_marked_edge_info__orFlags(eh, mf->v4, mf->v1, flags);
				} else {
					get_marked_edge_info__orFlags(eh, mf->v3, mf->v1, flags);
				}

				if (tf->flag&TF_ACTIVE) {
					get_marked_edge_info__orFlags(eh, mf->v1, mf->v2, eEdge_ActiveFirst);
					get_marked_edge_info__orFlags(eh, mf->v1, mf->v4?mf->v4:mf->v3, eEdge_ActiveLast);
				}
			}
		}
	}

	return eh;
}


static int draw_tfaces3D__setHiddenOpts(void *userData, int index)
{
	struct { Mesh *me; EdgeHash *eh; } *data = userData;
	MEdge *med = &data->me->medge[index];
	unsigned int flags = (int) BLI_edgehash_lookup(data->eh, med->v1, med->v2);

	if((G.f & G_DRAWSEAMS) && (med->flag&ME_SEAM)) {
		return 0;
	} else if(G.f & G_DRAWEDGES){ 
		if (G.f&G_HIDDENEDGES) {
			return 1;
		} else {
			return (flags & eEdge_Visible);
		}
	} else {
		return (flags & eEdge_Select);
	}
}
static int draw_tfaces3D__setSeamOpts(void *userData, int index)
{
	struct { Mesh *me; EdgeHash *eh; } *data = userData;
	MEdge *med = &data->me->medge[index];
	unsigned int flags = (int) BLI_edgehash_lookup(data->eh, med->v1, med->v2);

	if (med->flag&ME_SEAM) {
		if (G.f&G_HIDDENEDGES) {
			return 1;
		} else {
			return (flags & eEdge_Visible);
		}
	} else {
		return 0;
	}
}
static int draw_tfaces3D__setSelectOpts(void *userData, int index)
{
	struct { Mesh *me; EdgeHash *eh; } *data = userData;
	MEdge *med = &data->me->medge[index];
	unsigned int flags = (int) BLI_edgehash_lookup(data->eh, med->v1, med->v2);

	return flags & eEdge_Select;
}
static int draw_tfaces3D__setActiveOpts(void *userData, int index)
{
	struct { Mesh *me; EdgeHash *eh; } *data = userData;
	MEdge *med = &data->me->medge[index];
	unsigned int flags = (int) BLI_edgehash_lookup(data->eh, med->v1, med->v2);

	if (flags & eEdge_Active) {
		if (flags & eEdge_ActiveLast) {
			glColor3ub(255, 0, 0);
		} else if (flags & eEdge_ActiveFirst) {
			glColor3ub(0, 255, 0);
		} else if (flags & eEdge_SelectAndActive) {
			glColor3ub(255, 255, 0);
		} else {
			glColor3ub(255, 0, 255);
		}

		return 1;
	} else {
		return 0;
	}
}
static int draw_tfaces3D__drawFaceOpts(void *userData, int index)
{
	Mesh *me = (Mesh*)userData;

	if (me->tface) {
		TFace *tface = &me->tface[index];
		if (!(tface->flag&TF_HIDE) && (tface->flag&TF_SELECT))
			return 2; /* Don't set color */
		else
			return 0;
	} else
		return 0;
}
static void draw_tfaces3D(Object *ob, Mesh *me, DerivedMesh *dm)
{
	struct { Mesh *me; EdgeHash *eh; } data;

	data.me = me;
	data.eh = get_tface_mesh_marked_edge_info(me);

	glEnable(GL_DEPTH_TEST);
	glDisable(GL_LIGHTING);
	bglPolygonOffset(1.0);

		/* Draw (Hidden) Edges */
	BIF_ThemeColor(TH_EDGE_FACESEL);
	dm->drawMappedEdges(dm, draw_tfaces3D__setHiddenOpts, &data);

		/* Draw Seams */
	if(G.f & G_DRAWSEAMS) {
		BIF_ThemeColor(TH_EDGE_SEAM);
		glLineWidth(2);

		dm->drawMappedEdges(dm, draw_tfaces3D__setSeamOpts, &data);

		glLineWidth(1);
	}

		/* Draw Selected Faces */
	if(G.f & G_DRAWFACES) {
		glEnable(GL_BLEND);
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
		BIF_ThemeColor4(TH_FACE_SELECT);

		dm->drawMappedFacesTex(dm, draw_tfaces3D__drawFaceOpts, (void*)me);

		glDisable(GL_BLEND);
	}
	
	bglPolygonOffset(1.0);

		/* Draw Stippled Outline for selected faces */
	glColor3ub(255, 255, 255);
	setlinestyle(1);
	dm->drawMappedEdges(dm, draw_tfaces3D__setSelectOpts, &data);
	setlinestyle(0);

	dm->drawMappedEdges(dm, draw_tfaces3D__setActiveOpts, &data);

	bglPolygonOffset(0.0);	// resets correctly now, even after calling accumulated offsets

	BLI_edgehash_free(data.eh, NULL);
}

static int set_gl_light(Object *ob)
{
	Base *base;
	Lamp *la;
	int count;
	/* float zero[4]= {0.0, 0.0, 0.0, 0.0};  */
	float vec[4];
	
	vec[3]= 1.0;
	
	for(count=0; count<8; count++) glDisable(GL_LIGHT0+count);
	
	count= 0;
	
	base= FIRSTBASE;
	while(base) {
		if(base->object->type==OB_LAMP ) {
			if(base->lay & G.vd->lay) {
				if(base->lay & ob->lay) 
				{
					la= base->object->data;
					
					glPushMatrix();
					glLoadMatrixf((float *)G.vd->viewmat);
					
					where_is_object_simul(base->object);
					VECCOPY(vec, base->object->obmat[3]);
					
					if(la->type==LA_SUN) {
						vec[0]= base->object->obmat[2][0];
						vec[1]= base->object->obmat[2][1];
						vec[2]= base->object->obmat[2][2];
						vec[3]= 0.0;
						glLightfv(GL_LIGHT0+count, GL_POSITION, vec); 
					}
					else {
						vec[3]= 1.0;
						glLightfv(GL_LIGHT0+count, GL_POSITION, vec); 
						glLightf(GL_LIGHT0+count, GL_CONSTANT_ATTENUATION, 1.0);
						glLightf(GL_LIGHT0+count, GL_LINEAR_ATTENUATION, la->att1/la->dist);
						/* post 2.25 engine supports quad lights */
						glLightf(GL_LIGHT0+count, GL_QUADRATIC_ATTENUATION, la->att2/(la->dist*la->dist));
						
						if(la->type==LA_SPOT) {
							vec[0]= -base->object->obmat[2][0];
							vec[1]= -base->object->obmat[2][1];
							vec[2]= -base->object->obmat[2][2];
							glLightfv(GL_LIGHT0+count, GL_SPOT_DIRECTION, vec);
							glLightf(GL_LIGHT0+count, GL_SPOT_CUTOFF, la->spotsize/2.0);
							glLightf(GL_LIGHT0+count, GL_SPOT_EXPONENT, 128.0*la->spotblend);
						}
						else glLightf(GL_LIGHT0+count, GL_SPOT_CUTOFF, 180.0);
					}
					
					vec[0]= la->energy*la->r;
					vec[1]= la->energy*la->g;
					vec[2]= la->energy*la->b;
					vec[3]= 1.0;
					glLightfv(GL_LIGHT0+count, GL_DIFFUSE, vec); 
					glLightfv(GL_LIGHT0+count, GL_SPECULAR, vec);//zero); 
					glEnable(GL_LIGHT0+count);
					
					glPopMatrix();					
					
					count++;
					if(count>7) break;
				}
			}
		}
		base= base->next;
	}

	return count;
}

static Material *give_current_material_or_def(Object *ob, int matnr)
{
	extern Material defmaterial;	// render module abuse...
	Material *ma= give_current_material(ob, matnr);

	return ma?ma:&defmaterial;
}

static int set_draw_settings_cached(int clearcache, int textured, TFace *texface, int lit, Object *litob, int litmatnr, int doublesided)
{
	static int c_textured;
	static int c_lit;
	static int c_doublesided;
	static TFace *c_texface;
	static Object *c_litob;
	static int c_litmatnr;
	static int c_badtex;

	if (clearcache) {
		c_textured= c_lit= c_doublesided= -1;
		c_texface= (TFace*) -1;
		c_litob= (Object*) -1;
		c_litmatnr= -1;
		c_badtex= 0;
	}

	if (texface) {
		lit = lit && (lit==-1 || texface->mode&TF_LIGHT);
		textured = textured && (texface->mode&TF_TEX);
		doublesided = texface->mode&TF_TWOSIDE;
	} else {
		textured = 0;
	}

	if (doublesided!=c_doublesided) {
		if (doublesided) glDisable(GL_CULL_FACE);
		else glEnable(GL_CULL_FACE);

		c_doublesided= doublesided;
	}

	if (textured!=c_textured || texface!=c_texface) {
		if (textured ) {
			c_badtex= !set_tpage(texface);
		} else {
			set_tpage(0);
			c_badtex= 0;
		}
		c_textured= textured;
		c_texface= texface;
	}

	if (c_badtex) lit= 0;
	if (lit!=c_lit || litob!=c_litob || litmatnr!=c_litmatnr) {
		if (lit) {
			Material *ma= give_current_material_or_def(litob, litmatnr+1);
			float spec[4];

			spec[0]= ma->spec*ma->specr;
			spec[1]= ma->spec*ma->specg;
			spec[2]= ma->spec*ma->specb;
			spec[3]= 1.0;

			glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, spec);
			glColorMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE);
			glEnable(GL_LIGHTING);
			glEnable(GL_COLOR_MATERIAL);
		}
		else {
			glDisable(GL_LIGHTING); 
			glDisable(GL_COLOR_MATERIAL);
		}
		c_lit= lit;
		c_litob= litob;
		c_litmatnr= litmatnr;
	}

	return c_badtex;
}

/* Icky globals, fix with userdata parameter */

static Object *g_draw_tface_mesh_ob = NULL;
static int g_draw_tface_mesh_islight = 0;
static int g_draw_tface_mesh_istex = 0;
static unsigned char g_draw_tface_mesh_obcol[4];

static int draw_tface__set_draw(TFace *tface, int matnr)
{
	if (tface && ((tface->flag&TF_HIDE) || (tface->mode&TF_INVISIBLE))) return 0;

	if (set_draw_settings_cached(0, g_draw_tface_mesh_istex, tface, g_draw_tface_mesh_islight, g_draw_tface_mesh_ob, matnr, TF_TWOSIDE)) {
		glColor3ub(0xFF, 0x00, 0xFF);
		return 2; /* Don't set color */
	} else if (tface && tface->mode&TF_OBCOL) {
		glColor3ubv(g_draw_tface_mesh_obcol);
		return 2; /* Don't set color */
	} else if (!tface) {
		Material *ma= give_current_material(g_draw_tface_mesh_ob, matnr+1);
		if(ma) glColor3f(ma->r, ma->g, ma->b);
		else glColor3f(0.5, 0.5, 0.5);
		return 1; /* Set color from mcol if available */
	} else {
		return 1; /* Set color from tface */
	}
}

static int draw_tface_mapped__set_draw(void *userData, int index)
{
	Mesh *me = (Mesh*)userData;
	TFace *tface = (me->tface)? &me->tface[index]: NULL;
	int matnr = me->mface[index].mat_nr;

	return draw_tface__set_draw(tface, matnr);
}

void draw_tface_mesh(Object *ob, Mesh *me, int dt)
/* maximum dt (drawtype): exactly according values that have been set */
{
	unsigned char obcol[4];
	int a;
	short istex, solidtex=0;
	DerivedMesh *dm;
	int dmNeedsFree;
	
	if(me==NULL) return;

	dm = mesh_get_derived_final(ob, &dmNeedsFree);

	glShadeModel(GL_SMOOTH);

	/* option to draw solid texture with default lights */
	if(dt>OB_WIRE && G.vd->drawtype==OB_SOLID) {
		solidtex= 1;
		g_draw_tface_mesh_islight= -1;
	}
	else
		g_draw_tface_mesh_islight= set_gl_light(ob);
	
	obcol[0]= CLAMPIS(ob->col[0]*255, 0, 255);
	obcol[1]= CLAMPIS(ob->col[1]*255, 0, 255);
	obcol[2]= CLAMPIS(ob->col[2]*255, 0, 255);
	obcol[3]= CLAMPIS(ob->col[3]*255, 0, 255);
	
	/* first all texture polys */
	
	if(ob->transflag & OB_NEG_SCALE) glFrontFace(GL_CW);
	else glFrontFace(GL_CCW);
	
	glCullFace(GL_BACK); glEnable(GL_CULL_FACE);
	if(solidtex || G.vd->drawtype==OB_TEXTURE) istex= 1;
	else istex= 0;

	g_draw_tface_mesh_ob = ob;
	g_draw_tface_mesh_istex = istex;
	memcpy(g_draw_tface_mesh_obcol, obcol, sizeof(obcol));
	set_draw_settings_cached(1, 0, 0, 0, 0, 0, 0);

	if(dt > OB_SOLID || g_draw_tface_mesh_islight==-1) {
		TFace *tface= me->tface;
		MFace *mface= me->mface;
		bProperty *prop = get_property(ob, "Text");
		int editing= (G.f & (G_VERTEXPAINT+G_FACESELECT+G_TEXTUREPAINT+G_WEIGHTPAINT)) && (ob==((G.scene->basact) ? (G.scene->basact->object) : 0));
		int start, totface;

#ifdef WITH_VERSE
		if(me->vnode) {
			/* verse-blender doesn't support uv mapping of textures yet */
			dm->drawFacesTex(dm, NULL);
		}
		else if(ob==OBACT && (G.f & G_FACESELECT) && me && me->tface)
#else
		if(ob==OBACT && (G.f & G_FACESELECT) && me && me->tface)
#endif
			dm->drawMappedFacesTex(dm, draw_tface_mapped__set_draw, (void*)me);
		else
			dm->drawFacesTex(dm, draw_tface__set_draw);

		start = 0;
		totface = me->totface;

		if (!editing && prop && tface) {
			int dmNeedsFree;
			DerivedMesh *dm = mesh_get_derived_deform(ob, &dmNeedsFree);

			tface+= start;
			for (a=start; a<totface; a++, tface++) {
				MFace *mf= &mface[a];
				int mode= tface->mode;
				int matnr= mf->mat_nr;
				int mf_smooth= mf->flag & ME_SMOOTH;

				if (!(tface->flag&TF_HIDE) && !(mode&TF_INVISIBLE) && (mode&TF_BMFONT)) {
					int badtex= set_draw_settings_cached(0, g_draw_tface_mesh_istex, tface, g_draw_tface_mesh_islight, g_draw_tface_mesh_ob, matnr, TF_TWOSIDE);
					float v1[3], v2[3], v3[3], v4[3];
					char string[MAX_PROPSTRING];
					int characters, index;
					Image *ima;
					float curpos;

					if (badtex)
						continue;

					dm->getVertCo(dm, mf->v1, v1);
					dm->getVertCo(dm, mf->v2, v2);
					dm->getVertCo(dm, mf->v3, v3);
					if (mf->v4) dm->getVertCo(dm, mf->v4, v4);

					// The BM_FONT handling code is duplicated in the gameengine
					// Search for 'Frank van Beek' ;-)
					// string = "Frank van Beek";

					set_property_valstr(prop, string);
					characters = strlen(string);
					
					ima = tface->tpage;
					if (ima == NULL) {
						characters = 0;
					}

					if (!mf_smooth) {
						float nor[3];

						CalcNormFloat(v1, v2, v3, nor);

						glNormal3fv(nor);
					}

					curpos= 0.0;
					glBegin(mf->v4?GL_QUADS:GL_TRIANGLES);
					for (index = 0; index < characters; index++) {
						float centerx, centery, sizex, sizey, transx, transy, movex, movey, advance;
						int character = string[index];
						char *cp= NULL;

						// lets calculate offset stuff
						// space starts at offset 1
						// character = character - ' ' + 1;
						
						matrixGlyph(ima->ibuf, character, & centerx, &centery, &sizex, &sizey, &transx, &transy, &movex, &movey, &advance);
						movex+= curpos;

						if (tface->mode & TF_OBCOL) glColor3ubv(obcol);
						else cp= (char *)&(tface->col[0]);

						glTexCoord2f((tface->uv[0][0] - centerx) * sizex + transx, (tface->uv[0][1] - centery) * sizey + transy);
						if (cp) glColor3ub(cp[3], cp[2], cp[1]);
						glVertex3f(sizex * v1[0] + movex, sizey * v1[1] + movey, v1[2]);
						
						glTexCoord2f((tface->uv[1][0] - centerx) * sizex + transx, (tface->uv[1][1] - centery) * sizey + transy);
						if (cp) glColor3ub(cp[7], cp[6], cp[5]);
						glVertex3f(sizex * v2[0] + movex, sizey * v2[1] + movey, v2[2]);
			
						glTexCoord2f((tface->uv[2][0] - centerx) * sizex + transx, (tface->uv[2][1] - centery) * sizey + transy);
						if (cp) glColor3ub(cp[11], cp[10], cp[9]);
						glVertex3f(sizex * v3[0] + movex, sizey * v3[1] + movey, v3[2]);
			
						if(mf->v4) {
							glTexCoord2f((tface->uv[3][0] - centerx) * sizex + transx, (tface->uv[3][1] - centery) * sizey + transy);
							if (cp) glColor3ub(cp[15], cp[14], cp[13]);
							glVertex3f(sizex * v4[0] + movex, sizey * v4[1] + movey, v4[2]);
						}

						curpos+= advance;
					}
					glEnd();
				}
			}

			if (dmNeedsFree) dm->release(dm);
		}

		/* switch off textures */
		set_tpage(0);
	}
	glShadeModel(GL_FLAT);
	glDisable(GL_CULL_FACE);
	
	if(ob==OBACT && (G.f & G_FACESELECT) && me && me->tface) {
		draw_tfaces3D(ob, me, dm);
	}
	
		/* XXX, bad patch - default_gl_light() calls
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
	default_gl_light();
	glPopMatrix();
	
	glFrontFace(GL_CCW);

	if(dt > OB_SOLID && !(ob==OBACT && (G.f & G_FACESELECT) && me && me->tface)) {
		if(ob->flag & SELECT) {
			BIF_ThemeColor((ob==OBACT)?TH_ACTIVE:TH_SELECT);
		} else {
			BIF_ThemeColor(TH_WIRE);
		}
		dm->drawLooseEdges(dm);
	}
}

void init_realtime_GL(void)
{		
	glMatrixMode(GL_TEXTURE);
	glLoadIdentity();
	glMatrixMode(GL_MODELVIEW);

}

