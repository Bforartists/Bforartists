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
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * Contributors: 2004/2005/2006 Blender Foundation, full recode
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <math.h>
#include <string.h>

/* external modules: */
#include "MEM_guardedalloc.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"
#include "BLI_threads.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"        /* for rectcpy */

#include "DNA_group_types.h"
#include "DNA_image_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_texture_types.h"

#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_global.h"
#include "BKE_image.h"   // BKE_write_ibuf 
#include "BKE_texture.h"
#include "BKE_utildefines.h"

#include "MTC_matrixops.h"

/* this module */
#include "render_types.h"
#include "renderpipeline.h"
#include "envmap.h"
#include "rendercore.h" 
#include "renderdatabase.h" 
#include "texture.h"
#include "zbuf.h"
#include "initrender.h"


/* ------------------------------------------------------------------------- */

static void envmap_split_ima(EnvMap *env)
{
	ImBuf *ibuf;
	Image *ima;
/*  	extern rectcpy(); */
	int dx, part;
	
	BKE_free_envmapdata(env);	
	
	dx= env->ima->ibuf->y;
	dx/= 2;
	if(3*dx != env->ima->ibuf->x) {
		printf("Incorrect envmap size\n");
		env->ok= 0;
		env->ima->ok= 0;
	}
	else {
		for(part=0; part<6; part++) {
			ibuf= IMB_allocImBuf(dx, dx, 24, IB_rect, 0);
			ima= MEM_callocN(sizeof(Image), "image");
			ima->ibuf= ibuf;
			ima->ok= 1;
			env->cube[part]= ima;
		}
		IMB_rectcpy(env->cube[0]->ibuf, env->ima->ibuf, 
			0, 0, 0, 0, dx, dx);
		IMB_rectcpy(env->cube[1]->ibuf, env->ima->ibuf, 
			0, 0, dx, 0, dx, dx);
		IMB_rectcpy(env->cube[2]->ibuf, env->ima->ibuf, 
			0, 0, 2*dx, 0, dx, dx);
		IMB_rectcpy(env->cube[3]->ibuf, env->ima->ibuf, 
			0, 0, 0, dx, dx, dx);
		IMB_rectcpy(env->cube[4]->ibuf, env->ima->ibuf, 
			0, 0, dx, dx, dx, dx);
		IMB_rectcpy(env->cube[5]->ibuf, env->ima->ibuf, 
			0, 0, 2*dx, dx, dx, dx);
		env->ok= 2;
	}
}

/* ------------------------------------------------------------------------- */
/* ****************** RENDER ********************** */

/* copy current render */
static Render *envmap_render_copy(Render *re, EnvMap *env)
{
	Render *envre;
	int cuberes;
	
	envre= RE_NewRender("Envmap");
	
	env->lastsize= re->r.size;
	cuberes = (env->cuberes * re->r.size) / 100;
	cuberes &= 0xFFFC;
	
	/* set up renderdata */
	envre->r= re->r;
	envre->r.mode &= ~(R_BORDER | R_PANORAMA | R_ORTHO | R_MBLUR);
	envre->r.layers.first= envre->r.layers.last= NULL;
	envre->r.filtertype= 0;
	envre->r.xparts= envre->r.yparts= 2;
	envre->r.bufflag= 0;
	envre->r.size= 100;
	envre->r.yasp= envre->r.xasp= 1;
	
	RE_InitState(envre, &re->r, cuberes, cuberes, NULL);
	envre->scene= re->scene;	/* unsure about this... */

	/* view stuff in env render */
	envre->ycor= 1.0; 
	envre->clipsta= env->clipsta;	/* render_scene_set_window() respects this for now */
	envre->clipend= env->clipend;
	
	RE_SetCamera(envre, env->object);
	
	/* callbacks */
	envre->display_draw= re->display_draw;
	envre->test_break= re->test_break;
	
	/* and for the evil stuff; copy the database... */
	envre->totvlak= re->totvlak;
	envre->totvert= re->totvert;
	envre->tothalo= re->tothalo;
	envre->totlamp= re->totlamp;
	envre->lights= re->lights;
	envre->vertnodeslen= re->vertnodeslen;
	envre->vertnodes= re->vertnodes;
	envre->blohalen= re->blohalen;
	envre->bloha= re->bloha;
	envre->blovllen= re->blovllen;
	envre->blovl= re->blovl;
	envre->oc= re->oc;
	
	return envre;
}

static void envmap_free_render_copy(Render *envre)
{

	envre->totvlak= 0;
	envre->totvert= 0;
	envre->tothalo= 0;
	envre->totlamp= 0;
	envre->lights.first= envre->lights.last= NULL;
	envre->vertnodeslen= 0;
	envre->vertnodes= NULL;
	envre->blohalen= 0;
	envre->bloha= NULL;
	envre->blovllen= 0;
	envre->blovl= NULL;
	envre->oc.adrbranch= NULL;
	envre->oc.adrnode= NULL;
	
	RE_FreeRender(envre);
}

/* ------------------------------------------------------------------------- */

static void envmap_transmatrix(float mat[][4], int part)
{
	float tmat[4][4], eul[3], rotmat[4][4];
	
	eul[0]= eul[1]= eul[2]= 0.0;
	
	if(part==0) {			/* neg z */
		;
	} else if(part==1) {	/* pos z */
		eul[0]= M_PI;
	} else if(part==2) {	/* pos y */
		eul[0]= M_PI/2.0;
	} else if(part==3) {	/* neg x */
		eul[0]= M_PI/2.0;
		eul[2]= M_PI/2.0;
	} else if(part==4) {	/* neg y */
		eul[0]= M_PI/2.0;
		eul[2]= M_PI;
	} else {				/* pos x */
		eul[0]= M_PI/2.0;
		eul[2]= -M_PI/2.0;
	}
	
	MTC_Mat4CpyMat4(tmat, mat);
	EulToMat4(eul, rotmat);
	MTC_Mat4MulSerie(mat, tmat, rotmat,
					 0,   0,    0,
					 0,   0,    0);
}

/* ------------------------------------------------------------------------- */

static void env_rotate_scene(Render *re, float mat[][4], int mode)
{
	GroupObject *go;
	VlakRen *vlr = NULL;
	VertRen *ver = NULL;
	LampRen *lar = NULL;
	HaloRen *har = NULL;
	float xn, yn, zn, imat[3][3], pmat[4][4], smat[4][4], tmat[4][4], cmat[3][3];
	int a;
	
	if(mode==0) {
		MTC_Mat4Invert(tmat, mat);
		MTC_Mat3CpyMat4(imat, tmat);
	}
	else {
		MTC_Mat4CpyMat4(tmat, mat);
		MTC_Mat3CpyMat4(imat, mat);
	}
	
	for(a=0; a<re->totvert; a++) {
		if((a & 255)==0) ver= RE_findOrAddVert(re, a);
		else ver++;
		
		MTC_Mat4MulVecfl(tmat, ver->co);
		
		xn= ver->n[0];
		yn= ver->n[1];
		zn= ver->n[2];
		/* no transpose ! */
		ver->n[0]= imat[0][0]*xn+imat[1][0]*yn+imat[2][0]*zn;
		ver->n[1]= imat[0][1]*xn+imat[1][1]*yn+imat[2][1]*zn;
		ver->n[2]= imat[0][2]*xn+imat[1][2]*yn+imat[2][2]*zn;
		Normalise(ver->n);
	}
	
	for(a=0; a<re->tothalo; a++) {
		if((a & 255)==0) har= re->bloha[a>>8];
		else har++;
	
		MTC_Mat4MulVecfl(tmat, har->co);
	}
		
	for(a=0; a<re->totvlak; a++) {
		if((a & 255)==0) vlr= re->blovl[a>>8];
		else vlr++;
		
		xn= vlr->n[0];
		yn= vlr->n[1];
		zn= vlr->n[2];
		/* no transpose ! */
		vlr->n[0]= imat[0][0]*xn+imat[1][0]*yn+imat[2][0]*zn;
		vlr->n[1]= imat[0][1]*xn+imat[1][1]*yn+imat[2][1]*zn;
		vlr->n[2]= imat[0][2]*xn+imat[1][2]*yn+imat[2][2]*zn;
		Normalise(vlr->n);
	}
	
	set_normalflags(re);
	
	for(go=re->lights.first; go; go= go->next) {
		lar= go->lampren;
		
		/* removed here some horrible code of someone in NaN who tried to fix
		   prototypes... just solved by introducing a correct cmat[3][3] instead
		   of using smat. this works, check square spots in reflections  (ton) */
		Mat3CpyMat3(cmat, lar->imat); 
		Mat3MulMat3(lar->imat, cmat, imat); 

		MTC_Mat3MulVecfl(imat, lar->vec);
		MTC_Mat4MulVecfl(tmat, lar->co);

		lar->sh_invcampos[0]= -lar->co[0];
		lar->sh_invcampos[1]= -lar->co[1];
		lar->sh_invcampos[2]= -lar->co[2];
		MTC_Mat3MulVecfl(lar->imat, lar->sh_invcampos);
		lar->sh_invcampos[2]*= lar->sh_zfac;
		
		if(lar->shb) {
			if(mode==1) {
				MTC_Mat4Invert(pmat, mat);
				MTC_Mat4MulMat4(smat, pmat, lar->shb->viewmat);
				MTC_Mat4MulMat4(lar->shb->persmat, smat, lar->shb->winmat);
			}
			else MTC_Mat4MulMat4(lar->shb->persmat, lar->shb->viewmat, lar->shb->winmat);
		}
	}
	
}

/* ------------------------------------------------------------------------- */

static void env_layerflags(Render *re, unsigned int notlay)
{
	VlakRen *vlr = NULL;
	int a;
	
	for(a=0; a<re->totvlak; a++) {
		if((a & 255)==0) vlr= re->blovl[a>>8];
		else vlr++;
		if(vlr->lay & notlay) vlr->flag &= ~R_VISIBLE;
	}
}

static void env_hideobject(Render *re, Object *ob)
{
	VlakRen *vlr = NULL;
	int a;
	
	for(a=0; a<re->totvlak; a++) {
		if((a & 255)==0) vlr= re->blovl[a>>8];
		else vlr++;
		if(vlr->ob == ob) vlr->flag &= ~R_VISIBLE;
	}
}

/* ------------------------------------------------------------------------- */

static void env_set_imats(Render *re)
{
	Base *base;
	float mat[4][4];
	
	base= G.scene->base.first;
	while(base) {
		MTC_Mat4MulMat4(mat, base->object->obmat, re->viewmat);
		MTC_Mat4Invert(base->object->imat, mat);
		
		base= base->next;
	}

}	

/* ------------------------------------------------------------------------- */

static void render_envmap(Render *re, EnvMap *env)
{
	/* only the cubemap and planar map is implemented */
	Render *envre;
	ImBuf *ibuf;
	Image *ima;
	float orthmat[4][4];
	float oldviewinv[4][4], mat[4][4], tmat[4][4];
	short part;
	
	/* need a recalc: ortho-render has no correct viewinv */
	MTC_Mat4Invert(oldviewinv, re->viewmat);

	envre= envmap_render_copy(re, env);
	
	/* precalc orthmat for object */
	MTC_Mat4CpyMat4(orthmat, env->object->obmat);
	MTC_Mat4Ortho(orthmat);
	
	/* need imat later for texture imat */
	MTC_Mat4MulMat4(mat, orthmat, re->viewmat);
	MTC_Mat4Invert(tmat, mat);
	MTC_Mat3CpyMat4(env->obimat, tmat);

	for(part=0; part<6; part++) {
		if(env->type==ENV_PLANE && part!=1)
			continue;
		
		re->display_clear(envre->result);
		
		MTC_Mat4CpyMat4(tmat, orthmat);
		envmap_transmatrix(tmat, part);
		MTC_Mat4Invert(mat, tmat);
		/* mat now is the camera 'viewmat' */

		MTC_Mat4CpyMat4(envre->viewmat, mat);
		MTC_Mat4CpyMat4(envre->viewinv, tmat);
		
		/* we have to correct for the already rotated vertexcoords */
		MTC_Mat4MulMat4(tmat, oldviewinv, envre->viewmat);
		MTC_Mat4Invert(env->imat, tmat);
		
		env_rotate_scene(envre, tmat, 1);
		init_render_world(envre);
		project_renderdata(envre, projectverto, 0, 0);
		env_layerflags(envre, env->notlay);
		env_hideobject(envre, env->object);
		env_set_imats(envre);
				
		if(re->test_break()==0) {
			RE_TileProcessor(envre, 0);
		}
		
		/* rotate back */
		env_rotate_scene(envre, tmat, 0);

		if(re->test_break()==0) {
			RenderLayer *rl= envre->result->layers.first;
			
			ibuf= IMB_allocImBuf(envre->rectx, envre->recty, 24, IB_rect, 0);
			ibuf->rect_float= rl->rectf;
			IMB_rect_from_float(ibuf);
			ibuf->rect_float= NULL;
				
			ima= MEM_callocN(sizeof(Image), "image");
			
			ima->ibuf= ibuf;
			ima->ok= 1;
			env->cube[part]= ima;
		}
		
		if(re->test_break()) break;

	}
	
	if(re->test_break()) BKE_free_envmapdata(env);
	else {
		if(envre->r.mode & R_OSA) env->ok= ENV_OSA;
		else env->ok= ENV_NORMAL;
		env->lastframe= G.scene->r.cfra;	/* hurmf */
	}
	
	/* restore */
	envmap_free_render_copy(envre);
	env_set_imats(re);

}

/* ------------------------------------------------------------------------- */

void make_envmaps(Render *re)
{
	Tex *tex;
	int do_init= 0, depth= 0, trace;
	
	if (!(re->r.mode & R_ENVMAP)) return;
	
	/* we dont raytrace, disabling the flag will cause ray_transp render solid */
	trace= (re->r.mode & R_RAYTRACE);
	re->r.mode &= ~R_RAYTRACE;

	re->i.infostr= "Creating Environment maps";
	re->stats_draw(&re->i);
	
	/* 5 = hardcoded max recursion level */
	while(depth<5) {
		tex= G.main->tex.first;
		while(tex) {
			if(tex->id.us && tex->type==TEX_ENVMAP) {
				if(tex->env && tex->env->object) {
					if(tex->env->object->lay & G.scene->lay) {
						if(tex->env->stype!=ENV_LOAD) {
							
							/* decide if to render an envmap (again) */
							if(tex->env->depth >= depth) {
								
								/* set 'recalc' to make sure it does an entire loop of recalcs */
								
								if(tex->env->ok) {
										/* free when OSA, and old one isn't OSA */
									if((re->r.mode & R_OSA) && tex->env->ok==ENV_NORMAL) 
										BKE_free_envmapdata(tex->env);
										/* free when size larger */
									else if(tex->env->lastsize < re->r.size) 
										BKE_free_envmapdata(tex->env);
										/* free when env is in recalcmode */
									else if(tex->env->recalc)
										BKE_free_envmapdata(tex->env);
								}
								
								if(tex->env->ok==0 && depth==0) tex->env->recalc= 1;
								
								if(tex->env->ok==0) {
									do_init= 1;
									render_envmap(re, tex->env);
									
									if(depth==tex->env->depth) tex->env->recalc= 0;
								}
							}
						}
					}
				}
			}
			tex= tex->id.next;
		}
		depth++;
	}

	if(do_init) {
		re->display_init(re->result);
		re->display_clear(re->result);
		// re->flag |= R_REDRAW_PRV;
	}	
	// restore
	re->r.mode |= trace;

}

/* ------------------------------------------------------------------------- */

static int envcube_isect(float *vec, float *answ)
{
	float labda;
	int face;
	
	/* which face */
	if( vec[2]<=-fabs(vec[0]) && vec[2]<=-fabs(vec[1]) ) {
		face= 0;
		labda= -1.0/vec[2];
		answ[0]= labda*vec[0];
		answ[1]= labda*vec[1];
	}
	else if( vec[2]>=fabs(vec[0]) && vec[2]>=fabs(vec[1]) ) {
		face= 1;
		labda= 1.0/vec[2];
		answ[0]= labda*vec[0];
		answ[1]= -labda*vec[1];
	}
	else if( vec[1]>=fabs(vec[0]) ) {
		face= 2;
		labda= 1.0/vec[1];
		answ[0]= labda*vec[0];
		answ[1]= labda*vec[2];
	}
	else if( vec[0]<=-fabs(vec[1]) ) {
		face= 3;
		labda= -1.0/vec[0];
		answ[0]= labda*vec[1];
		answ[1]= labda*vec[2];
	}
	else if( vec[1]<=-fabs(vec[0]) ) {
		face= 4;
		labda= -1.0/vec[1];
		answ[0]= -labda*vec[0];
		answ[1]= labda*vec[2];
	}
	else {
		face= 5;
		labda= 1.0/vec[0];
		answ[0]= -labda*vec[1];
		answ[1]= labda*vec[2];
	}
	answ[0]= 0.5+0.5*answ[0];
	answ[1]= 0.5+0.5*answ[1];
	return face;
}

/* ------------------------------------------------------------------------- */

static void set_dxtdyt(float *dxts, float *dyts, float *dxt, float *dyt, int face)
{
	if(face==2 || face==4) {
		dxts[0]= dxt[0];
		dyts[0]= dyt[0];
		dxts[1]= dxt[2];
		dyts[1]= dyt[2];
	}
	else if(face==3 || face==5) {
		dxts[0]= dxt[1];
		dxts[1]= dxt[2];
		dyts[0]= dyt[1];
		dyts[1]= dyt[2];
	}
	else {
		dxts[0]= dxt[0];
		dyts[0]= dyt[0];
		dxts[1]= dxt[1];
		dyts[1]= dyt[1];
	}
}

/* ------------------------------------------------------------------------- */

int envmaptex(Tex *tex, float *texvec, float *dxt, float *dyt, int osatex, TexResult *texres)
{
	extern Render R;				/* only in this call */
	/* texvec should be the already reflected normal */
	EnvMap *env;
	Image *ima;
	float fac, vec[3], sco[3], dxts[3], dyts[3];
	int face, face1;
	
	env= tex->env;
	if(env==NULL || (env->stype!=ENV_LOAD && env->object==NULL)) {
		texres->tin= 0.0;
		return 0;
	}
	if(env->stype==ENV_LOAD) {
		env->ima= tex->ima;
		if(env->ima && env->ima->ok) {
			// Now thread safe
			BLI_lock_thread(LOCK_MALLOC);
			if(env->ima->ibuf==NULL) ima_ibuf_is_nul(tex, tex->ima);
			if(env->ima->ok && env->ok==0) envmap_split_ima(env);
			BLI_unlock_thread(LOCK_MALLOC);
		}
	}

	if(env->ok==0) {
		
		texres->tin= 0.0;
		return 0;
	}
	
	/* rotate to envmap space, if object is set */
	VECCOPY(vec, texvec);
	if(env->object) MTC_Mat3MulVecfl(env->obimat, vec);
	else MTC_Mat4Mul3Vecfl(R.viewinv, vec);
	
	face= envcube_isect(vec, sco);
	if(env->type==ENV_PLANE)
		ima= env->cube[1];
	else
		ima= env->cube[face];
	
	if(osatex) {
		if(env->object) {
			MTC_Mat3MulVecfl(env->obimat, dxt);
			MTC_Mat3MulVecfl(env->obimat, dyt);
		}
		else {
			MTC_Mat4Mul3Vecfl(R.viewinv, dxt);
			MTC_Mat4Mul3Vecfl(R.viewinv, dyt);
		}
		set_dxtdyt(dxts, dyts, dxt, dyt, face);
		imagewraposa(tex, ima, sco, dxts, dyts, texres);
		
		/* edges? */
		
		if(texres->ta<1.0) {
			TexResult texr1, texr2;
	
			texr1.nor= texr2.nor= NULL;

			VecAddf(vec, vec, dxt);
			face1= envcube_isect(vec, sco);
			VecSubf(vec, vec, dxt);
			
			if(face!=face1) {
				if(env->type==ENV_CUBE)
					ima= env->cube[face1];
				
				set_dxtdyt(dxts, dyts, dxt, dyt, face1);
				imagewraposa(tex, ima, sco, dxts, dyts, &texr1);
			}
			else texr1.tr= texr1.tg= texr1.tb= texr1.ta= 0.0;
			
			/* here was the nasty bug! results were not zero-ed. FPE! */
			
			VecAddf(vec, vec, dyt);
			face1= envcube_isect(vec, sco);
			VecSubf(vec, vec, dyt);
			
			if(face!=face1) {
				if(env->type==ENV_CUBE)
					ima= env->cube[face1];
				set_dxtdyt(dxts, dyts, dxt, dyt, face1);
				imagewraposa(tex, ima, sco, dxts, dyts, &texr2);
			}
			else texr2.tr= texr2.tg= texr2.tb= texr2.ta= 0.0;
			
			fac= (texres->ta+texr1.ta+texr2.ta);
			if(fac!=0.0) {
				fac= 1.0/fac;
				
				texres->tr= fac*(texres->ta*texres->tr + texr1.ta*texr1.tr + texr2.ta*texr2.tr );
				texres->tg= fac*(texres->ta*texres->tg + texr1.ta*texr1.tg + texr2.ta*texr2.tg );
				texres->tb= fac*(texres->ta*texres->tb + texr1.ta*texr1.tb + texr2.ta*texr2.tb );
			}
			texres->ta= 1.0;
		}
	}
	else {
		imagewrap(tex, ima, sco, texres);
	}
	
	return 1;
}

/* ------------------------------------------------------------------------- */

/* eof */
