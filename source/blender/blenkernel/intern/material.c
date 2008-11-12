
/*  material.c
 *
 * 
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

#include <string.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_curve_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meta_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_texture_types.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"		

#include "BKE_blender.h"
#include "BKE_displist.h"
#include "BKE_global.h"
#include "BKE_icons.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_mesh.h"
#include "BKE_node.h"
#include "BKE_utildefines.h"

#ifndef DISABLE_PYTHON
#include "BPY_extern.h"
#endif

#include "GPU_material.h"

/* used in UI and render */
Material defmaterial;

/* called on startup, creator.c */
void init_def_material(void)
{
	init_material(&defmaterial);
}

/* not material itself */
void free_material(Material *ma)
{
	MTex *mtex;
	int a;

#ifndef DISABLE_PYTHON
	BPY_free_scriptlink(&ma->scriptlink);
#endif
	
	for(a=0; a<MAX_MTEX; a++) {
		mtex= ma->mtex[a];
		if(mtex && mtex->tex) mtex->tex->id.us--;
		if(mtex) MEM_freeN(mtex);
	}
	
	if(ma->ramp_col) MEM_freeN(ma->ramp_col);
	if(ma->ramp_spec) MEM_freeN(ma->ramp_spec);
	
	BKE_previewimg_free(&ma->preview);
	BKE_icon_delete((struct ID*)ma);
	ma->id.icon_id = 0;
	
	/* is no lib link block, but material extension */
	if(ma->nodetree) {
		ntreeFreeTree(ma->nodetree);
		MEM_freeN(ma->nodetree);
	}

	if(ma->gpumaterial.first)
		GPU_material_free(ma);
}

void init_material(Material *ma)
{
	ma->r= ma->g= ma->b= ma->ref= 0.8;
	ma->specr= ma->specg= ma->specb= 1.0;
	ma->mirr= ma->mirg= ma->mirb= 1.0;
	ma->spectra= 1.0;
	ma->amb= 0.5;
	ma->alpha= 1.0;
	ma->spec= ma->hasize= 0.5;
	ma->har= 50;
	ma->starc= ma->ringc= 4;
	ma->linec= 12;
	ma->flarec= 1;
	ma->flaresize= ma->subsize= 1.0;
	ma->flareboost= 1;
	ma->seed2= 6;
	ma->friction= 0.5;
	ma->refrac= 4.0;
	ma->roughness= 0.5;
	ma->param[0]= 0.5;
	ma->param[1]= 0.1;
	ma->param[2]= 0.5;
	ma->param[3]= 0.1;
	ma->rms= 0.1;
	ma->darkness= 1.0;	
	
	ma->strand_sta= ma->strand_end= 1.0f;
	
	ma->ang= 1.0;
	ma->ray_depth= 2;
	ma->ray_depth_tra= 2;
	ma->fresnel_mir= 0.0;
	ma->fresnel_tra= 0.0;
	ma->fresnel_tra_i= 1.25;
	ma->fresnel_mir_i= 1.25;
	ma->tx_limit= 0.0;
	ma->tx_falloff= 1.0;
	ma->shad_alpha= 1.0f;
	
	ma->gloss_mir = ma->gloss_tra= 1.0;
	ma->samp_gloss_mir = ma->samp_gloss_tra= 18;
	ma->adapt_thresh_mir = ma->adapt_thresh_tra = 0.005;
	ma->dist_mir = 0.0;
	ma->fadeto_mir = MA_RAYMIR_FADETOSKY;
	
	ma->rampfac_col= 1.0;
	ma->rampfac_spec= 1.0;
	ma->pr_lamp= 3;			/* two lamps, is bits */
	ma->pr_type= MA_SPHERE;

	ma->sss_radius[0]= 1.0f;
	ma->sss_radius[1]= 1.0f;
	ma->sss_radius[2]= 1.0f;
	ma->sss_col[0]= 0.8f;
	ma->sss_col[1]= 0.8f;
	ma->sss_col[2]= 0.8f;
	ma->sss_error= 0.05f;
	ma->sss_scale= 0.1f;
	ma->sss_ior= 1.3f;
	ma->sss_colfac= 1.0f;
	ma->sss_texfac= 0.0f;
	ma->sss_front= 1.0f;
	ma->sss_back= 1.0f;

	ma->mode= MA_TRACEBLE|MA_SHADBUF|MA_SHADOW|MA_RADIO|MA_RAYBIAS|MA_TANGENT_STR;

	ma->preview = NULL;
}

Material *add_material(char *name)
{
	Material *ma;

	ma= alloc_libblock(&G.main->mat, ID_MA, name);
	
	init_material(ma);
	
	return ma;	
}

Material *copy_material(Material *ma)
{
	Material *man;
	int a;
	
	man= copy_libblock(ma);
	
	id_us_plus((ID *)man->ipo);
	id_us_plus((ID *)man->group);
	
	
	for(a=0; a<MAX_MTEX; a++) {
		if(ma->mtex[a]) {
			man->mtex[a]= MEM_mallocN(sizeof(MTex), "copymaterial");
			memcpy(man->mtex[a], ma->mtex[a], sizeof(MTex));
			id_us_plus((ID *)man->mtex[a]->tex);
		}
	}

#ifndef DISABLE_PYTHON	
	BPY_copy_scriptlink(&ma->scriptlink);
#endif
	
	if(ma->ramp_col) man->ramp_col= MEM_dupallocN(ma->ramp_col);
	if(ma->ramp_spec) man->ramp_spec= MEM_dupallocN(ma->ramp_spec);
	
	if (ma->preview) man->preview = BKE_previewimg_copy(ma->preview);

	if(ma->nodetree) {
		man->nodetree= ntreeCopyTree(ma->nodetree, 0);	/* 0 == full new tree */
	}

	man->gpumaterial.first= man->gpumaterial.last= NULL;
	
	return man;
}

void make_local_material(Material *ma)
{
	Object *ob;
	Mesh *me;
	Curve *cu;
	MetaBall *mb;
	Material *man;
	int a, local=0, lib=0;

	/* - only lib users: do nothing
	    * - only local users: set flag
	    * - mixed: make copy
	    */
	
	if(ma->id.lib==0) return;
	if(ma->id.us==1) {
		ma->id.lib= 0;
		ma->id.flag= LIB_LOCAL;
		new_id(0, (ID *)ma, 0);
		for(a=0; a<MAX_MTEX; a++) {
			if(ma->mtex[a]) id_lib_extern((ID *)ma->mtex[a]->tex);
		}
		
		return;
	}
	
	/* test objects */
	ob= G.main->object.first;
	while(ob) {
		if(ob->mat) {
			for(a=0; a<ob->totcol; a++) {
				if(ob->mat[a]==ma) {
					if(ob->id.lib) lib= 1;
					else local= 1;
				}
			}
		}
		ob= ob->id.next;
	}
	/* test meshes */
	me= G.main->mesh.first;
	while(me) {
		if(me->mat) {
			for(a=0; a<me->totcol; a++) {
				if(me->mat[a]==ma) {
					if(me->id.lib) lib= 1;
					else local= 1;
				}
			}
		}
		me= me->id.next;
	}
	/* test curves */
	cu= G.main->curve.first;
	while(cu) {
		if(cu->mat) {
			for(a=0; a<cu->totcol; a++) {
				if(cu->mat[a]==ma) {
					if(cu->id.lib) lib= 1;
					else local= 1;
				}
			}
		}
		cu= cu->id.next;
	}
	/* test mballs */
	mb= G.main->mball.first;
	while(mb) {
		if(mb->mat) {
			for(a=0; a<mb->totcol; a++) {
				if(mb->mat[a]==ma) {
					if(mb->id.lib) lib= 1;
					else local= 1;
				}
			}
		}
		mb= mb->id.next;
	}
	
	if(local && lib==0) {
		ma->id.lib= 0;
		ma->id.flag= LIB_LOCAL;
		
		for(a=0; a<MAX_MTEX; a++) {
			if(ma->mtex[a]) id_lib_extern((ID *)ma->mtex[a]->tex);
		}
		
		new_id(0, (ID *)ma, 0);
	}
	else if(local && lib) {
		
		man= copy_material(ma);
		man->id.us= 0;
		
		/* do objects */
		ob= G.main->object.first;
		while(ob) {
			if(ob->mat) {
				for(a=0; a<ob->totcol; a++) {
					if(ob->mat[a]==ma) {
						if(ob->id.lib==0) {
							ob->mat[a]= man;
							man->id.us++;
							ma->id.us--;
						}
					}
				}
			}
			ob= ob->id.next;
		}
		/* do meshes */
		me= G.main->mesh.first;
		while(me) {
			if(me->mat) {
				for(a=0; a<me->totcol; a++) {
					if(me->mat[a]==ma) {
						if(me->id.lib==0) {
							me->mat[a]= man;
							man->id.us++;
							ma->id.us--;
						}
					}
				}
			}
			me= me->id.next;
		}
		/* do curves */
		cu= G.main->curve.first;
		while(cu) {
			if(cu->mat) {
				for(a=0; a<cu->totcol; a++) {
					if(cu->mat[a]==ma) {
						if(cu->id.lib==0) {
							cu->mat[a]= man;
							man->id.us++;
							ma->id.us--;
						}
					}
				}
			}
			cu= cu->id.next;
		}
		/* do mballs */
		mb= G.main->mball.first;
		while(mb) {
			if(mb->mat) {
				for(a=0; a<mb->totcol; a++) {
					if(mb->mat[a]==ma) {
						if(mb->id.lib==0) {
							mb->mat[a]= man;
							man->id.us++;
							ma->id.us--;
						}
					}
				}
			}
			mb= mb->id.next;
		}
	}
}

Material ***give_matarar(Object *ob)
{
	Mesh *me;
	Curve *cu;
	MetaBall *mb;
	
	if(ob->type==OB_MESH) {
		me= ob->data;
		return &(me->mat);
	}
	else if ELEM3(ob->type, OB_CURVE, OB_FONT, OB_SURF) {
		cu= ob->data;
		return &(cu->mat);
	}
	else if(ob->type==OB_MBALL) {
		mb= ob->data;
		return &(mb->mat);
	}
	return NULL;
}

short *give_totcolp(Object *ob)
{
	Mesh *me;
	Curve *cu;
	MetaBall *mb;
	
	if(ob->type==OB_MESH) {
		me= ob->data;
		return &(me->totcol);
	}
	else if ELEM3(ob->type, OB_CURVE, OB_FONT, OB_SURF) {
		cu= ob->data;
		return &(cu->totcol);
	}
	else if(ob->type==OB_MBALL) {
		mb= ob->data;
		return &(mb->totcol);
	}
	return NULL;
}

Material *give_current_material(Object *ob, int act)
{
	Material ***matarar, *ma;
	short *totcolp;
	
	if(ob==NULL) return NULL;
	
	/* if object cannot have material, totcolp==NULL */
	totcolp= give_totcolp(ob);
	if(totcolp==NULL || ob->totcol==0) return NULL;
	
	if(act>ob->totcol) act= ob->totcol;
	else if(act<=0) act= 1;

	if( BTST(ob->colbits, act-1) ) {	/* in object */
		ma= ob->mat[act-1];
	}
	else {								/* in data */

		/* check for inconsistancy */
		if(*totcolp < ob->totcol)
			ob->totcol= *totcolp;
		if(act>ob->totcol) act= ob->totcol;

		matarar= give_matarar(ob);
		
		if(matarar && *matarar) ma= (*matarar)[act-1];
		else ma= 0;
		
	}
	
	return ma;
}

ID *material_from(Object *ob, int act)
{

	if(ob==0) return 0;

	if(ob->totcol==0) return ob->data;
	if(act==0) act= 1;

	if( BTST(ob->colbits, act-1) ) return (ID *)ob;
	else return ob->data;
}

/* GS reads the memory pointed at in a specific ordering. There are,
 * however two definitions for it. I have jotted them down here, both,
 * but I think the first one is actually used. The thing is that
 * big-endian systems might read this the wrong way round. OTOH, we
 * constructed the IDs that are read out with this macro explicitly as
 * well. I expect we'll sort it out soon... */

/* from blendef: */
#define GS(a)	(*((short *)(a)))

/* from misc_util: flip the bytes from x  */
/*  #define GS(x) (((unsigned char *)(x))[0] << 8 | ((unsigned char *)(x))[1]) */

void test_object_materials(ID *id)
{
	/* make the ob mat-array same size as 'ob->data' mat-array */
	Object *ob;
	Mesh *me;
	Curve *cu;
	MetaBall *mb;
	Material **newmatar;
	int totcol=0;

	if(id==0) return;

	if( GS(id->name)==ID_ME ) {
		me= (Mesh *)id;
		totcol= me->totcol;
	}
	else if( GS(id->name)==ID_CU ) {
		cu= (Curve *)id;
		totcol= cu->totcol;
	}
	else if( GS(id->name)==ID_MB ) {
		mb= (MetaBall *)id;
		totcol= mb->totcol;
	}
	else return;

	ob= G.main->object.first;
	while(ob) {
		
		if(ob->data==id) {
		
			if(totcol==0) {
				if(ob->totcol) {
					MEM_freeN(ob->mat);
					ob->mat= 0;
				}
			}
			else if(ob->totcol<totcol) {
				newmatar= MEM_callocN(sizeof(void *)*totcol, "newmatar");
				if(ob->totcol) {
					memcpy(newmatar, ob->mat, sizeof(void *)*ob->totcol);
					MEM_freeN(ob->mat);
				}
				ob->mat= newmatar;
			}
			ob->totcol= totcol;
			if(ob->totcol && ob->actcol==0) ob->actcol= 1;
			if(ob->actcol>ob->totcol) ob->actcol= ob->totcol;
		}
		ob= ob->id.next;
	}
}


void assign_material(Object *ob, Material *ma, int act)
{
	Material *mao, **matar, ***matarar;
	short *totcolp;

	if(act>MAXMAT) return;
	if(act<1) act= 1;
	
	/* test arraylens */
	
	totcolp= give_totcolp(ob);
	matarar= give_matarar(ob);
	
	if(totcolp==0 || matarar==0) return;
	
	if( act > *totcolp) {
		matar= MEM_callocN(sizeof(void *)*act, "matarray1");
		if( *totcolp) {
			memcpy(matar, *matarar, sizeof(void *)*( *totcolp ));
			MEM_freeN(*matarar);
		}
		*matarar= matar;
		*totcolp= act;
	}
	
	if(act > ob->totcol) {
		matar= MEM_callocN(sizeof(void *)*act, "matarray2");
		if( ob->totcol) {
			memcpy(matar, ob->mat, sizeof(void *)*( ob->totcol ));
			MEM_freeN(ob->mat);
		}
		ob->mat= matar;
		ob->totcol= act;
	}
	
	/* do it */

	if( BTST(ob->colbits, act-1) ) {	/* in object */
		mao= ob->mat[act-1];
		if(mao) mao->id.us--;
		ob->mat[act-1]= ma;
	}
	else {	/* in data */
		mao= (*matarar)[act-1];
		if(mao) mao->id.us--;
		(*matarar)[act-1]= ma;
	}
	id_us_plus((ID *)ma);
	test_object_materials(ob->data);
}

int find_material_index(Object *ob, Material *ma)
{
	Material ***matarar;
	short a, *totcolp;
	
	if(ma==NULL) return 0;
	
	totcolp= give_totcolp(ob);
	matarar= give_matarar(ob);
	
	if(totcolp==NULL || matarar==NULL) return 0;
	
	for(a=0; a<*totcolp; a++)
		if((*matarar)[a]==ma)
		   break;
	if(a<*totcolp)
		return a+1;
	return 0;	   
}

void new_material_to_objectdata(Object *ob)
{
	Material *ma;
	
	if(ob==0) return;
	if(ob->totcol>=MAXMAT) return;
	
	ma= give_current_material(ob, ob->actcol);
	if(ma==NULL)
		ma= add_material("Material");
	else
		ma= copy_material(ma);
	
	ma->id.us= 0; /* eeh... */
	
	if(ob->actcol) {
		if( BTST(ob->colbits, ob->actcol-1) ) {
			ob->colbits= BSET(ob->colbits, ob->totcol);
		}
	}
	
	assign_material(ob, ma, ob->totcol+1);
	ob->actcol= ob->totcol;
}

static void do_init_render_material(Material *ma, int r_mode, float *amb)
{
	MTex *mtex;
	int a, needuv=0, needtang=0;
	
	if(ma->flarec==0) ma->flarec= 1;

	/* add all texcoflags from mtex, texco and mapto were cleared in advance */
	for(a=0; a<MAX_MTEX; a++) {
		
		/* separate tex switching */
		if(ma->septex & (1<<a)) continue;

		mtex= ma->mtex[a];
		if(mtex && mtex->tex && mtex->tex->type) {
			
			ma->texco |= mtex->texco;
			ma->mapto |= mtex->mapto;
			if(r_mode & R_OSA) {
				if ELEM3(mtex->tex->type, TEX_IMAGE, TEX_PLUGIN, TEX_ENVMAP) ma->texco |= TEXCO_OSA;
			}
			
			if(ma->texco & (TEXCO_ORCO|TEXCO_REFL|TEXCO_NORM|TEXCO_STRAND|TEXCO_STRESS)) needuv= 1;
			else if(ma->texco & (TEXCO_GLOB|TEXCO_UV|TEXCO_OBJECT|TEXCO_SPEED)) needuv= 1;
			else if(ma->texco & (TEXCO_LAVECTOR|TEXCO_VIEW|TEXCO_STICKY)) needuv= 1;

			if((ma->mapto & MAP_NORM) && (mtex->normapspace == MTEX_NSPACE_TANGENT))
				needtang= 1;
		}
	}

	if(needtang) ma->mode |= MA_NORMAP_TANG;
	else ma->mode &= ~MA_NORMAP_TANG;
	
	if(r_mode & R_RADIO)
		if(ma->mode & MA_RADIO) needuv= 1;
	
	if(ma->mode & (MA_VERTEXCOL|MA_VERTEXCOLP|MA_FACETEXTURE)) {
		needuv= 1;
		if(r_mode & R_OSA) ma->texco |= TEXCO_OSA;		/* for texfaces */
	}
	if(needuv) ma->texco |= NEED_UV;
	
	/* since the raytracer doesnt recalc O structs for each ray, we have to preset them all */
	if(r_mode & R_RAYTRACE) {
		if(ma->mode & (MA_RAYMIRROR|MA_RAYTRANSP|MA_SHADOW_TRA)) { 
			ma->texco |= NEED_UV|TEXCO_ORCO|TEXCO_REFL|TEXCO_NORM;
			if(r_mode & R_OSA) ma->texco |= TEXCO_OSA;
		}
	}
	
	if(amb) {
		ma->ambr= ma->amb*amb[0];
		ma->ambg= ma->amb*amb[1];
		ma->ambb= ma->amb*amb[2];
	}	
	/* will become or-ed result of all node modes */
	ma->mode_l= ma->mode;
	ma->mode_l &= ~MA_SHLESS;

	if(ma->strand_surfnor > 0.0f)
		ma->mode_l |= MA_STR_SURFDIFF;
}

static void init_render_nodetree(bNodeTree *ntree, Material *basemat, int r_mode, float *amb)
{
	bNode *node;
	
	for(node=ntree->nodes.first; node; node= node->next) {
		if(node->id) {
			if(GS(node->id->name)==ID_MA) {
				Material *ma= (Material *)node->id;
				if(ma!=basemat) {
					do_init_render_material(ma, r_mode, amb);
					basemat->texco |= ma->texco;
					basemat->mode_l |= ma->mode_l;
				}
			}
			else if(node->type==NODE_GROUP)
				init_render_nodetree((bNodeTree *)node->id, basemat, r_mode, amb);
		}
	}
	/* parses the geom+tex nodes */
	ntreeShaderGetTexcoMode(ntree, r_mode, &basemat->texco, &basemat->mode_l);
}

void init_render_material(Material *mat, int r_mode, float *amb)
{
	
	do_init_render_material(mat, r_mode, amb);
	
	if(mat->nodetree && mat->use_nodes) {
		init_render_nodetree(mat->nodetree, mat, r_mode, amb);
		
		ntreeBeginExecTree(mat->nodetree); /* has internal flag to detect it only does it once */
	}
}

void init_render_materials(int r_mode, float *amb)
{
	Material *ma;
	
	/* clear these flags before going over materials, to make sure they
	 * are cleared only once, otherwise node materials contained in other
	 * node materials can go wrong */
	for(ma= G.main->mat.first; ma; ma= ma->id.next) {
		if(ma->id.us) {
			ma->texco= 0;
			ma->mapto= 0;
		}
	}

	/* two steps, first initialize, then or the flags for layers */
	for(ma= G.main->mat.first; ma; ma= ma->id.next) {
		/* is_used flag comes back in convertblender.c */
		ma->flag &= ~MA_IS_USED;
		if(ma->id.us) 
			init_render_material(ma, r_mode, amb);
	}
	
	do_init_render_material(&defmaterial, r_mode, amb);
}

/* only needed for nodes now */
void end_render_material(Material *mat)
{
	if(mat && mat->nodetree && mat->use_nodes)
		ntreeEndExecTree(mat->nodetree); /* has internal flag to detect it only does it once */
}

void end_render_materials(void)
{
	Material *ma;
	for(ma= G.main->mat.first; ma; ma= ma->id.next)
		if(ma->id.us) 
			end_render_material(ma);
}

static int material_in_nodetree(bNodeTree *ntree, Material *mat)
{
	bNode *node;

	for(node=ntree->nodes.first; node; node= node->next) {
		if(node->id && GS(node->id->name)==ID_MA) {
			if(node->id==(ID*)mat)
				return 1;
		}
		else if(node->type==NODE_GROUP)
			if(material_in_nodetree((bNodeTree*)node->id, mat))
				return 1;
	}

	return 0;
}

int material_in_material(Material *parmat, Material *mat)
{
	if(parmat==mat)
		return 1;
	else if(parmat->nodetree && parmat->use_nodes)
		return material_in_nodetree(parmat->nodetree, mat);
	else
		return 0;
}
	
/* ****************** */

char colname_array[125][20]= {
"Black","DarkRed","HalfRed","Red","Red",
"DarkGreen","DarkOlive","Brown","Chocolate","OrangeRed",
"HalfGreen","GreenOlive","DryOlive","Goldenrod","DarkOrange",
"LightGreen","Chartreuse","YellowGreen","Yellow","Gold",
"Green","LawnGreen","GreenYellow","LightOlive","Yellow",
"DarkBlue","DarkPurple","HotPink","VioletPink","RedPink",
"SlateGray","DarkGrey","PalePurple","IndianRed","Tomato",
"SeaGreen","PaleGreen","GreenKhaki","LightBrown","LightSalmon",
"SpringGreen","PaleGreen","MediumOlive","YellowBrown","LightGold",
"LightGreen","LightGreen","LightGreen","GreenYellow","PaleYellow",
"HalfBlue","DarkSky","HalfMagenta","VioletRed","DeepPink",
"SteelBlue","SkyBlue","Orchid","LightHotPink","HotPink",
"SeaGreen","SlateGray","MediumGrey","Burlywood","LightPink",
"SpringGreen","Aquamarine","PaleGreen","Khaki","PaleOrange",
"SpringGreen","SeaGreen","PaleGreen","PaleWhite","YellowWhite",
"LightBlue","Purple","MediumOrchid","Magenta","Magenta",
"RoyalBlue","SlateBlue","MediumOrchid","Orchid","Magenta",
"DeepSkyBlue","LightSteelBlue","LightSkyBlue","Violet","LightPink",
"Cyan","DarkTurquoise","SkyBlue","Grey","Snow",
"Mint","Mint","Aquamarine","MintCream","Ivory",
"Blue","Blue","DarkMagenta","DarkOrchid","Magenta",
"SkyBlue","RoyalBlue","LightSlateBlue","MediumOrchid","Magenta",
"DodgerBlue","SteelBlue","MediumPurple","PalePurple","Plum",
"DeepSkyBlue","PaleBlue","LightSkyBlue","PalePurple","Thistle",
"Cyan","ColdBlue","PaleTurquoise","GhostWhite","White"
};

void automatname(Material *ma)
{
	int nr, r, g, b;
	float ref;
	
	if(ma==0) return;
	if(ma->mode & MA_SHLESS) ref= 1.0;
	else ref= ma->ref;
	
	r= (int)(4.99*(ref*ma->r));
	g= (int)(4.99*(ref*ma->g));
	b= (int)(4.99*(ref*ma->b));
	nr= r + 5*g + 25*b;
	if(nr>124) nr= 124;
	new_id(&G.main->mat, (ID *)ma, colname_array[nr]);
	
}


void delete_material_index()
{
	Material *mao, ***matarar;
	Object *ob, *obt;
	Curve *cu;
	Nurb *nu;
	short *totcolp;
	int a, actcol;
	
	if(G.obedit) {
		//XXX error("Unable to perform function in EditMode");
		return;
	}
	ob= ((G.scene->basact)? (G.scene->basact->object) : 0) ;
	if(ob==0 || ob->totcol==0) return;
	
	/* take a mesh/curve/mball as starting point, remove 1 index,
	 * AND with all objects that share the ob->data
	 * 
	 * after that check indices in mesh/curve/mball!!!
	 */
	
	totcolp= give_totcolp(ob);
	matarar= give_matarar(ob);

	/* we delete the actcol */
	if(ob->totcol) {
		mao= (*matarar)[ob->actcol-1];
		if(mao) mao->id.us--;
	}
	
	for(a=ob->actcol; a<ob->totcol; a++) {
		(*matarar)[a-1]= (*matarar)[a];
	}
	(*totcolp)--;
	
	if(*totcolp==0) {
		MEM_freeN(*matarar);
		*matarar= 0;
	}
	
	actcol= ob->actcol;
	obt= G.main->object.first;
	while(obt) {
	
		if(obt->data==ob->data) {
			
			/* WATCH IT: do not use actcol from ob or from obt (can become zero) */
			mao= obt->mat[actcol-1];
			if(mao) mao->id.us--;
		
			for(a=actcol; a<obt->totcol; a++) obt->mat[a-1]= obt->mat[a];
			obt->totcol--;
			if(obt->actcol > obt->totcol) obt->actcol= obt->totcol;
			
			if(obt->totcol==0) {
				MEM_freeN(obt->mat);
				obt->mat= 0;
			}
		}
		obt= obt->id.next;
	}

	/* check indices from mesh */

	if(ob->type==OB_MESH) {
		Mesh *me= get_mesh(ob);
		mesh_delete_material_index(me, actcol-1);
		freedisplist(&ob->disp);
	}
	else if ELEM(ob->type, OB_CURVE, OB_SURF) {
		cu= ob->data;
		nu= cu->nurb.first;
		
		while(nu) {
			if(nu->mat_nr && nu->mat_nr>=actcol-1) {
				nu->mat_nr--;
				if (ob->type == OB_CURVE) nu->charidx--;
			}
			nu= nu->next;
		}
		freedisplist(&ob->disp);
	}
}


/* r g b = current value, col = new value, fac==0 is no change */
/* if g==NULL, it only does r channel */
void ramp_blend(int type, float *r, float *g, float *b, float fac, float *col)
{
	float tmp, facm= 1.0-fac;
	
	switch (type) {
		case MA_RAMP_BLEND:
			*r = facm*(*r) + fac*col[0];
			if(g) {
				*g = facm*(*g) + fac*col[1];
				*b = facm*(*b) + fac*col[2];
			}
				break;
		case MA_RAMP_ADD:
			*r += fac*col[0];
			if(g) {
				*g += fac*col[1];
				*b += fac*col[2];
			}
				break;
		case MA_RAMP_MULT:
			*r *= (facm + fac*col[0]);
			if(g) {
				*g *= (facm + fac*col[1]);
				*b *= (facm + fac*col[2]);
			}
				break;
		case MA_RAMP_SCREEN:
			*r = 1.0 - (facm + fac*(1.0 - col[0])) * (1.0 - *r);
			if(g) {
				*g = 1.0 - (facm + fac*(1.0 - col[1])) * (1.0 - *g);
				*b = 1.0 - (facm + fac*(1.0 - col[2])) * (1.0 - *b);
			}
				break;
		case MA_RAMP_OVERLAY:
			if(*r < 0.5f)
				*r *= (facm + 2.0f*fac*col[0]);
			else
				*r = 1.0 - (facm + 2.0f*fac*(1.0 - col[0])) * (1.0 - *r);
			if(g) {
				if(*g < 0.5f)
					*g *= (facm + 2.0f*fac*col[1]);
				else
					*g = 1.0 - (facm + 2.0f*fac*(1.0 - col[1])) * (1.0 - *g);
				if(*b < 0.5f)
					*b *= (facm + 2.0f*fac*col[2]);
				else
					*b = 1.0 - (facm + 2.0f*fac*(1.0 - col[2])) * (1.0 - *b);
			}
				break;
		case MA_RAMP_SUB:
			*r -= fac*col[0];
			if(g) {
				*g -= fac*col[1];
				*b -= fac*col[2];
			}
				break;
		case MA_RAMP_DIV:
			if(col[0]!=0.0)
				*r = facm*(*r) + fac*(*r)/col[0];
			if(g) {
				if(col[1]!=0.0)
					*g = facm*(*g) + fac*(*g)/col[1];
				if(col[2]!=0.0)
					*b = facm*(*b) + fac*(*b)/col[2];
			}
				break;
		case MA_RAMP_DIFF:
			*r = facm*(*r) + fac*fabs(*r-col[0]);
			if(g) {
				*g = facm*(*g) + fac*fabs(*g-col[1]);
				*b = facm*(*b) + fac*fabs(*b-col[2]);
			}
				break;
		case MA_RAMP_DARK:
			tmp= fac*col[0];
			if(tmp < *r) *r= tmp; 
				if(g) {
					tmp= fac*col[1];
					if(tmp < *g) *g= tmp; 
					tmp= fac*col[2];
					if(tmp < *b) *b= tmp; 
				}
					break;
		case MA_RAMP_LIGHT:
			tmp= fac*col[0];
			if(tmp > *r) *r= tmp; 
				if(g) {
					tmp= fac*col[1];
					if(tmp > *g) *g= tmp; 
					tmp= fac*col[2];
					if(tmp > *b) *b= tmp; 
				}
					break;	
		case MA_RAMP_DODGE:			
			
				
			if(*r !=0.0){
				tmp = 1.0 - fac*col[0];
				if(tmp <= 0.0)
					*r = 1.0;
				else if ((tmp = (*r) / tmp)> 1.0)
					*r = 1.0;
				else 
					*r = tmp;
			}
			if(g) {
				if(*g !=0.0){
					tmp = 1.0 - fac*col[1];
					if(tmp <= 0.0 )
						*g = 1.0;
					else if ((tmp = (*g) / tmp) > 1.0 )
						*g = 1.0;
					else
						*g = tmp;
				}
				if(*b !=0.0){
					tmp = 1.0 - fac*col[2];
					if(tmp <= 0.0)
						*b = 1.0;
					else if ((tmp = (*b) / tmp) > 1.0 )
						*b = 1.0;
					else
						*b = tmp;
				}

			}
				break;	
		case MA_RAMP_BURN:
			
			tmp = facm + fac*col[0];
			
			if(tmp <= 0.0)
				*r = 0.0;
			else if (( tmp = (1.0 - (1.0 - (*r)) / tmp )) < 0.0)
			        *r = 0.0;
			else if (tmp > 1.0)
				*r=1.0;
			else 
				*r = tmp; 

			if(g) {
				tmp = facm + fac*col[1];
				if(tmp <= 0.0)
					*g = 0.0;
				else if (( tmp = (1.0 - (1.0 - (*g)) / tmp )) < 0.0 )
			        	*g = 0.0;
				else if(tmp >1.0)
					*g=1.0;
				else
					*g = tmp;
			        	
			        tmp = facm + fac*col[2];
			        if(tmp <= 0.0)
					*b = 0.0;
				else if (( tmp = (1.0 - (1.0 - (*b)) / tmp )) < 0.0  )
			        	*b = 0.0;
				else if(tmp >1.0)
					*b= 1.0;
				else
					*b = tmp;
			}
				break;
		case MA_RAMP_HUE:		
			if(g){
				float rH,rS,rV;
				float colH,colS,colV; 
				float tmpr,tmpg,tmpb;
				rgb_to_hsv(col[0],col[1],col[2],&colH,&colS,&colV);
				if(colS!=0 ){
					rgb_to_hsv(*r,*g,*b,&rH,&rS,&rV);
					hsv_to_rgb( colH , rS, rV, &tmpr, &tmpg, &tmpb);
					*r = facm*(*r) + fac*tmpr;  
					*g = facm*(*g) + fac*tmpg; 
					*b = facm*(*b) + fac*tmpb;
				}
			}
				break;
		case MA_RAMP_SAT:		
			if(g){
				float rH,rS,rV;
				float colH,colS,colV;
				rgb_to_hsv(*r,*g,*b,&rH,&rS,&rV);
				if(rS!=0){
					rgb_to_hsv(col[0],col[1],col[2],&colH,&colS,&colV);
					hsv_to_rgb( rH, (facm*rS +fac*colS), rV, r, g, b);
				}
			}
				break;
		case MA_RAMP_VAL:		
			if(g){
				float rH,rS,rV;
				float colH,colS,colV;
				rgb_to_hsv(*r,*g,*b,&rH,&rS,&rV);
				rgb_to_hsv(col[0],col[1],col[2],&colH,&colS,&colV);
				hsv_to_rgb( rH, rS, (facm*rV +fac*colV), r, g, b);
			}
				break;
		case MA_RAMP_COLOR:		
			if(g){
				float rH,rS,rV;
				float colH,colS,colV;
				float tmpr,tmpg,tmpb;
				rgb_to_hsv(col[0],col[1],col[2],&colH,&colS,&colV);
				if(colS!=0){
					rgb_to_hsv(*r,*g,*b,&rH,&rS,&rV);
					hsv_to_rgb( colH, colS, rV, &tmpr, &tmpg, &tmpb);
					*r = facm*(*r) + fac*tmpr;
					*g = facm*(*g) + fac*tmpg;
					*b = facm*(*b) + fac*tmpb;
				}
			}
				break;
	}
	
}


