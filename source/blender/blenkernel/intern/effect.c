/*  effect.c
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

#include <math.h>
#include <stdlib.h>

#include "MEM_guardedalloc.h"
#include "DNA_listBase.h"
#include "DNA_effect_types.h"
#include "DNA_object_types.h"
#include "DNA_object_force.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_material_types.h"
#include "DNA_curve_types.h"
#include "DNA_key_types.h"
#include "DNA_texture_types.h"
#include "DNA_scene_types.h"
#include "DNA_lattice_types.h"
#include "DNA_ipo_types.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_rand.h"

#include "BKE_action.h"
#include "BKE_bad_level_calls.h"
#include "BKE_blender.h"
#include "BKE_constraint.h"
#include "BKE_deform.h"
#include "BKE_displist.h"
#include "BKE_DerivedMesh.h"
#include "BKE_effect.h"
#include "BKE_global.h"
#include "BKE_ipo.h"
#include "BKE_key.h"
#include "BKE_lattice.h"
#include "BKE_mesh.h"
#include "BKE_material.h"
#include "BKE_main.h"
#include "BKE_object.h"
#include "BKE_screen.h"
#include "BKE_utildefines.h"

#include "render.h"  // externtex, bad level call (ton)


#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

Effect *add_effect(int type)
{
	Effect *eff=0;
	PartEff *paf;
	WaveEff *wav;
	int a;
	
	switch(type) {
	case EFF_PARTICLE:
		paf= MEM_callocN(sizeof(PartEff), "neweff");
		eff= (Effect *)paf;
		
		paf->sta= 1.0;
		paf->end= 100.0;
		paf->lifetime= 50.0;
		for(a=0; a<PAF_MAXMULT; a++) {
			paf->life[a]= 50.0;
			paf->child[a]= 4;
			paf->mat[a]= 1;
		}
		
		paf->totpart= 1000;
		paf->totkey= 8;
		paf->staticstep= 5;
		paf->defvec[2]= 1.0f;
		paf->nabla= 0.05f;
		
		break;
		
	case EFF_WAVE:
		wav= MEM_callocN(sizeof(WaveEff), "neweff");
		eff= (Effect *)wav;
		
		wav->flag |= (WAV_X+WAV_Y+WAV_CYCL);
		
		wav->height= 0.5f;
		wav->width= 1.5f;
		wav->speed= 0.5f;
		wav->narrow= 1.5f;
		wav->lifetime= 0.0f;
		wav->damp= 10.0f;
		
		break;
	}
	
	eff->type= eff->buttype= type;
	eff->flag |= SELECT;
	
	return eff;
}

void free_effect(Effect *eff)
{
	PartEff *paf;
	
	if(eff->type==EFF_PARTICLE) {
		paf= (PartEff *)eff;
		if(paf->keys) MEM_freeN(paf->keys);
	}
	MEM_freeN(eff);	
}


void free_effects(ListBase *lb)
{
	Effect *eff;
	
	eff= lb->first;
	while(eff) {
		BLI_remlink(lb, eff);
		free_effect(eff);
		eff= lb->first;
	}
}

Effect *copy_effect(Effect *eff) 
{
	Effect *effn;

	effn= MEM_dupallocN(eff);
	if(effn->type==EFF_PARTICLE) ((PartEff *)effn)->keys= 0;

	return effn;	
}

void copy_act_effect(Object *ob)
{
	/* return a copy of the active effect */
	Effect *effn, *eff;
	
	eff= ob->effect.first;
	while(eff) {
		if(eff->flag & SELECT) {
			
			effn= copy_effect(eff);
			BLI_addtail(&ob->effect, effn);
			
			eff->flag &= ~SELECT;
			return;
			
		}
		eff= eff->next;
	}
	
	/* when it comes here: add new effect */
	eff= add_effect(EFF_PARTICLE);
	BLI_addtail(&ob->effect, eff);
			
}

void copy_effects(ListBase *lbn, ListBase *lb)
{
	Effect *eff, *effn;

	lbn->first= lbn->last= 0;

	eff= lb->first;
	while(eff) {
		effn= copy_effect(eff);
		BLI_addtail(lbn, effn);
		
		eff= eff->next;
	}
	
}

void deselectall_eff(Object *ob)
{
	Effect *eff= ob->effect.first;
	
	while(eff) {
		eff->flag &= ~SELECT;
		eff= eff->next;
	}
}

/* ***************** PARTICLES ***************** */

Particle *new_particle(PartEff *paf)
{
	static Particle *pa;
	static int cur;

	/* we agree: when paf->keys==0: alloc */	
	if(paf->keys==0) {
		pa= paf->keys= MEM_callocN( paf->totkey*paf->totpart*sizeof(Particle), "particlekeys" );
		cur= 0;
	}
	else {
		if(cur && cur<paf->totpart) pa+=paf->totkey;
		cur++;
	}
	return pa;
}

PartEff *give_parteff(Object *ob)
{
	PartEff *paf;
	
	paf= ob->effect.first;
	while(paf) {
		if(paf->type==EFF_PARTICLE) return paf;
		paf= paf->next;
	}
	return 0;
}

void where_is_particle(PartEff *paf, Particle *pa, float ctime, float *vec)
{
	Particle *p[4];
	float dt, t[4];
	int a;
	
	if(paf->totkey==1) {
		VECCOPY(vec, pa->co);
		return;
	}
	
	/* first find the first particlekey */
	a= (int)((paf->totkey-1)*(ctime-pa->time)/pa->lifetime);
	if(a>=paf->totkey) a= paf->totkey-1;
	else if(a<0) a= 0;
	
	pa+= a;
	
	if(a>0) p[0]= pa-1; else p[0]= pa;
	p[1]= pa;
	
	if(a+1<paf->totkey) p[2]= pa+1; else p[2]= pa;
	if(a+2<paf->totkey) p[3]= pa+2; else p[3]= p[2];
	
	if(p[1]==p[2]) dt= 0.0;
	else dt= (ctime-p[1]->time)/(p[2]->time - p[1]->time);

	if(paf->flag & PAF_BSPLINE) set_four_ipo(dt, t, KEY_BSPLINE);
	else set_four_ipo(dt, t, KEY_CARDINAL);

	vec[0]= t[0]*p[0]->co[0] + t[1]*p[1]->co[0] + t[2]*p[2]->co[0] + t[3]*p[3]->co[0];
	vec[1]= t[0]*p[0]->co[1] + t[1]*p[1]->co[1] + t[2]*p[2]->co[1] + t[3]*p[3]->co[1];
	vec[2]= t[0]*p[0]->co[2] + t[1]*p[1]->co[2] + t[2]*p[2]->co[2] + t[3]*p[3]->co[2];

}

void particle_tex(MTex *mtex, PartEff *paf, float *co, float *no)
{				
	float tin, tr, tg, tb, ta;
	float old;
	
	externtex(mtex, co, &tin, &tr, &tg, &tb, &ta);

	if(paf->texmap==PAF_TEXINT) {
		tin*= paf->texfac;
		no[0]+= tin*paf->defvec[0];
		no[1]+= tin*paf->defvec[1];
		no[2]+= tin*paf->defvec[2];
	}
	else if(paf->texmap==PAF_TEXRGB) {
		no[0]+= (tr-0.5f)*paf->texfac;
		no[1]+= (tg-0.5f)*paf->texfac;
		no[2]+= (tb-0.5f)*paf->texfac;
	}
	else {	/* PAF_TEXGRAD */
		
		old= tin;
		co[0]+= paf->nabla;
		externtex(mtex, co, &tin, &tr, &tg, &tb, &ta);
		no[0]+= (old-tin)*paf->texfac;
		
		co[0]-= paf->nabla;
		co[1]+= paf->nabla;
		externtex(mtex, co, &tin, &tr, &tg, &tb, &ta);
		no[1]+= (old-tin)*paf->texfac;
		
		co[1]-= paf->nabla;
		co[2]+= paf->nabla;
		externtex(mtex, co, &tin, &tr, &tg, &tb, &ta);
		no[2]+= (old-tin)*paf->texfac;
		
	}
}

static int linetriangle(float p1[3], float p2[3], float v0[3], float v1[3], float v2[3], float *labda)
{
	float p[3], s[3], d[3], e1[3], e2[3], q[3];
	float a, f, u, v;
	
	VECSUB(e1, v1, v0);
	VECSUB(e2, v2, v0);
	VECSUB(d, p2, p1);
	
	Crossf(p, d, e2);
	a = INPR(e1, p);
	if ((a > -0.000001) && (a < 0.000001)) return 0;
	f = 1.0f/a;
	
	VECSUB(s, p1, v0);
	
	Crossf(q, s, e1);
	*labda = f * INPR(e2, q);
	if ((*labda < 0.0)||(*labda > 1.0)) return 0;
	
	u = f * INPR(s, p);
	if ((u < 0.0)||(u > 1.0)) return 0;
	
	v = f * INPR(d, q);
	if ((v < 0.0)||((u + v) > 1.0)) return 0;
	
	return 1;
}

/*  -------- pdDoEffector() --------
    generic force/speed system, now used for particles and softbodies
	opco		= global coord, as input
    force		= force accumulator
    speed		= speed accumulator
    cur_time	= in frames
    par_layer	= layer the caller is in

*/
void pdDoEffector(float *opco, float *force, float *speed, float cur_time, unsigned int par_layer,unsigned int flags)
{
/*
	Modifies the force on a particle according to its
	relation with the effector object
	Different kind of effectors include:
		Forcefields: Gravity-like attractor
		(force power is related to the inverse of distance to the power of a falloff value)
		Vortex fields: swirling effectors
		(particles rotate around Z-axis of the object. otherwise, same relation as)
		(Forcefields, but this is not done through a force/acceleration)
	
*/
	Object *ob;
	Base *base;
	PartDeflect *pd;
	float vect_to_vert[3];
	float force_vec[3];
	float f_force, distance;
	float *obloc;
	float force_val, ffall_val;
	short cur_frame;

	/* Cycle through objects, get total of (1/(gravity_strength * dist^gravity_power)) */
	/* Check for min distance here? (yes would be cool to add that, ton) */
	
	for(base = G.scene->base.first; base; base= base->next) {
		if( (base->lay & par_layer) && base->object->pd) {
			ob= base->object;
			pd= ob->pd;
			
			/* checking if to continue or not */
			if(pd->forcefield==0) continue;
			
			/* Get IPO force strength and fall off values here */
			if (has_ipo_code(ob->ipo, OB_PD_FSTR))
				force_val = IPO_GetFloatValue(ob->ipo, OB_PD_FSTR, cur_time);
			else 
				force_val = pd->f_strength;
			
			if (has_ipo_code(ob->ipo, OB_PD_FFALL)) 
				ffall_val = IPO_GetFloatValue(ob->ipo, OB_PD_FFALL, cur_time);
			else 
				ffall_val = pd->f_power;
			
			
			/* Need to set r.cfra for paths (investigate, ton) (uses ob->ctime now, ton) */
			if(ob->ctime!=cur_time) {
				cur_frame = G.scene->r.cfra;
				G.scene->r.cfra = (short)cur_time;
				where_is_object_time(ob, cur_time);
				G.scene->r.cfra = cur_frame;
			}
			
			/* use center of object for distance calculus */
			obloc= ob->obmat[3];
			VECSUB(vect_to_vert, obloc, opco);
			distance = VecLength(vect_to_vert);
			
			if((pd->flag & PFIELD_USEMAX) && distance>pd->maxdist)
				;	/* don't do anything */
			else if(pd->forcefield == PFIELD_WIND) {
				VECCOPY(force_vec, ob->obmat[2]);
				
				/* wind works harder perpendicular to normal, would be nice for softbody later (ton) */
				
				/* Limit minimum distance to vertex so that */
				/* the force is not too big */
				if (distance < 0.001) distance = 0.001f;
				f_force = (force_val)*(1/(1000 * (float)pow((double)distance, (double)ffall_val)));
				if(flags &&PE_WIND_AS_SPEED){
				speed[0] -= (force_vec[0] * f_force );
				speed[1] -= (force_vec[1] * f_force );
				speed[2] -= (force_vec[2] * f_force );
				}
				else{
				force[0] += force_vec[0]*f_force;
				force[1] += force_vec[1]*f_force;
				force[2] += force_vec[2]*f_force;
				}
			}
			else if(pd->forcefield == PFIELD_FORCE) {
				
				/* only use center of object */
				obloc= ob->obmat[3];

				/* Now calculate the gravitational force */
				VECSUB(vect_to_vert, obloc, opco);
				distance = VecLength(vect_to_vert);

				/* Limit minimum distance to vertex so that */
				/* the force is not too big */
				if (distance < 0.001) distance = 0.001f;
				f_force = (force_val)*(1/(1000 * (float)pow((double)distance, (double)ffall_val)));
				force[0] += (vect_to_vert[0] * f_force );
				force[1] += (vect_to_vert[1] * f_force );
				force[2] += (vect_to_vert[2] * f_force );

			}
			else if(pd->forcefield == PFIELD_VORTEX) {

				/* only use center of object */
				obloc= ob->obmat[3];

				/* Now calculate the vortex force */
				VECSUB(vect_to_vert, obloc, opco);
				distance = VecLength(vect_to_vert);

				Crossf(force_vec, ob->obmat[2], vect_to_vert);
				Normalise(force_vec);

				/* Limit minimum distance to vertex so that */
				/* the force is not too big */
				if (distance < 0.001) distance = 0.001f;
				f_force = (force_val)*(1/(100 * (float)pow((double)distance, (double)ffall_val)));
				speed[0] -= (force_vec[0] * f_force );
				speed[1] -= (force_vec[1] * f_force );
				speed[2] -= (force_vec[2] * f_force );

			}
		}
	}
}

static void cache_object_vertices(Object *ob)
{
	Mesh *me;
	MVert *mvert;
	float *fp;
	int a;
	
	me= ob->data;
	if(me->totvert==0) return;

	fp= ob->sumohandle= MEM_mallocN(3*sizeof(float)*me->totvert, "cache particles");
	mvert= me->mvert;
	a= me->totvert;
	while(a--) {
		VECCOPY(fp, mvert->co);
		Mat4MulVecfl(ob->obmat, fp);
		mvert++;
		fp+= 3;
	}
}

int pdDoDeflection(float opco[3], float npco[3], float opno[3],
        float npno[3], float life, float force[3], int def_depth,
        float cur_time, unsigned int par_layer, int *last_object,
		int *last_face, int *same_face)
{
	/* Particle deflection code */
	/* The code is in two sections: the first part checks whether a particle has            */
	/* intersected a face of a deflector mesh, given its old and new co-ords, opco and npco */
	/* and which face it hit first                                                          */
	/* The second part calculates the new co-ordinates given that collision and updates     */
	/* the new co-ordinates accordingly */
	Base *base;
	Object *ob, *deflection_object = NULL;
	Mesh *def_mesh;
	MFace *mface, *deflection_face = NULL;
	float *v1, *v2, *v3, *v4, *vcache=NULL;
	float nv1[3], nv2[3], nv3[3], nv4[3], edge1[3], edge2[3];
	float dv1[3], dv2[3], dv3[3];
	float vect_to_int[3], refl_vel[3];
	float d_intersect_co[3], d_intersect_vect[3], d_nvect[3], d_i_co_above[3];
	float forcec[3];
	float k_point3, dist_to_plane;
	float first_dist, ref_plane_mag;
	float dk_plane=0, dk_point1=0;
	float icalctop, icalcbot, n_mag;
	float mag_iv, x_m,y_m,z_m;
	float damping, perm_thresh;
	float perm_val, rdamp_val;
	int a, deflected=0, deflected_now=0;
	float t,t2, min_t;
	float mat[3][3], obloc[3];
	short cur_frame;
	float time_before, time_after;
	float force_mag_norm;
	int d_object=0, d_face=0, ds_object=0, ds_face=0;

	first_dist = 200000;
	min_t = 200000;

	/* The first part of the code, finding the first intersected face*/
	base= G.scene->base.first;
	while (base) {
		/*Only proceed for mesh object in same layer */
		if(base->object->type==OB_MESH && (base->lay & par_layer)) {
			ob= base->object;
			/* only with deflecting set */
			if(ob->pd && ob->pd->deflect) {
				def_mesh= ob->data;
			
				d_object = d_object + 1;

				d_face = d_face + 1;
				mface= def_mesh->mface;
				a = def_mesh->totface;
				
				
				if(ob->parent==NULL && ob->ipo==NULL) {	// static
					if(ob->sumohandle==NULL) cache_object_vertices(ob);
					vcache= ob->sumohandle;
				}
				else {
					/*Find out where the object is at this time*/
					cur_frame = G.scene->r.cfra;
					G.scene->r.cfra = (short)cur_time;
					where_is_object_time(ob, cur_time);
					G.scene->r.cfra = cur_frame;
					
					/*Pass the values from ob->obmat to mat*/
					/*and the location values to obloc           */
					Mat3CpyMat4(mat,ob->obmat);
					obloc[0] = ob->obmat[3][0];
					obloc[1] = ob->obmat[3][1];
					obloc[2] = ob->obmat[3][2];
					vcache= NULL;

				}
				
				while (a--) {

					if(vcache) {
						v1= vcache+ 3*(mface->v1);
						VECCOPY(nv1, v1);
						v1= vcache+ 3*(mface->v2);
						VECCOPY(nv2, v1);
						v1= vcache+ 3*(mface->v3);
						VECCOPY(nv3, v1);
						v1= vcache+ 3*(mface->v4);
						VECCOPY(nv4, v1);
					}
					else {
						/* Calculate the global co-ordinates of the vertices*/
						v1= (def_mesh->mvert+(mface->v1))->co;
						v2= (def_mesh->mvert+(mface->v2))->co;
						v3= (def_mesh->mvert+(mface->v3))->co;
						v4= (def_mesh->mvert+(mface->v4))->co;
	
						VECCOPY(nv1, v1);
						VECCOPY(nv2, v2);
						VECCOPY(nv3, v3);
						VECCOPY(nv4, v4);
	
						/*Apply the objects deformation matrix*/
						Mat3MulVecfl(mat, nv1);
						Mat3MulVecfl(mat, nv2);
						Mat3MulVecfl(mat, nv3);
						Mat3MulVecfl(mat, nv4);
	
						VECADD(nv1, nv1, obloc);
						VECADD(nv2, nv2, obloc);
						VECADD(nv3, nv3, obloc);
						VECADD(nv4, nv4, obloc);
					}
					
					deflected_now = 0;

						
						
//					t= 0.5;	// this is labda of line, can use it optimize quad intersection
// sorry but no .. see below (BM)					
					if( linetriangle(opco, npco, nv1, nv2, nv3, &t) ) {
						if (t < min_t) {
							deflected = 1;
							deflected_now = 1;
						}
					}
//					else if (mface->v4 && (t>=0.0 && t<=1.0)) {
// no, you can't skip testing the other triangle
// it might give a smaller t on (close to) the edge .. this is numerics not esoteric maths :)
// note: the 2 triangles don't need to share a plane ! (BM)
					if (mface->v4) {
						if( linetriangle(opco, npco, nv1, nv3, nv4, &t2) ) {
							if (t2 < min_t) {
								deflected = 1;
								deflected_now = 2;
							}
	  					}
					}
					
					if ((deflected_now > 0) && ((t < min_t) ||(t2 < min_t))) {
                    	min_t = t;
                    	ds_object = d_object;
						ds_face = d_face;
						deflection_object = ob;
						deflection_face = mface;
						if (deflected_now==1) {
                    	min_t = t;
							VECCOPY(dv1, nv1);
							VECCOPY(dv2, nv2);
							VECCOPY(dv3, nv3);
						}
						else {
                    	min_t = t2;
							VECCOPY(dv1, nv1);
							VECCOPY(dv2, nv3);
							VECCOPY(dv3, nv4);
						}
					}
					mface++;
				}
			}
		}
		base = base->next;
	}


	/* Here's the point to do the permeability calculation */
	/* Set deflected to 0 if a random number is below the value */
	/* Get the permeability IPO here*/
	if (deflected) {
		
		if (has_ipo_code(deflection_object->ipo, OB_PD_PERM)) 
			perm_val = IPO_GetFloatValue(deflection_object->ipo, OB_PD_PERM, cur_time);
		else 
			perm_val = deflection_object->pd->pdef_perm;

		perm_thresh =  (float)BLI_drand() - perm_val;
		if (perm_thresh < 0 ) {
			deflected = 0;
		}
	}

	/* Now for the second part of the deflection code - work out the new speed */
	/* and position of the particle if a collision occurred */
	if (deflected) {
    	VECSUB(edge1, dv1, dv2);
		VECSUB(edge2, dv3, dv2);
		Crossf(d_nvect, edge2, edge1);
		n_mag = Normalise(d_nvect);
		dk_plane = INPR(d_nvect, nv1);
		dk_point1 = INPR(d_nvect,opco);

		VECSUB(d_intersect_vect, npco, opco);

		d_intersect_co[0] = opco[0] + (min_t * (npco[0] - opco[0]));
		d_intersect_co[1] = opco[1] + (min_t * (npco[1] - opco[1]));
		d_intersect_co[2] = opco[2] + (min_t * (npco[2] - opco[2]));
		
		d_i_co_above[0] = (d_intersect_co[0] + (0.001f * d_nvect[0]));
		d_i_co_above[1] = (d_intersect_co[1] + (0.001f * d_nvect[1]));
		d_i_co_above[2] = (d_intersect_co[2] + (0.001f * d_nvect[2]));
		mag_iv = Normalise(d_intersect_vect);
		VECCOPY(npco, d_intersect_co);
		
		VECSUB(vect_to_int, opco, d_intersect_co);
		first_dist = Normalise(vect_to_int);

		/* Work out the lengths of time before and after collision*/
		time_before = (life*(first_dist / (mag_iv)));
		time_after =  (life*((mag_iv - first_dist) / (mag_iv)));

		/* We have to recalculate what the speed would have been at the */
		/* point of collision, not the key frame time */
		npno[0]= opno[0] + time_before*force[0];
		npno[1]= opno[1] + time_before*force[1];
		npno[2]= opno[2] + time_before*force[2];


		/* Reflect the speed vector in the face */
		x_m = (2 * npno[0] * d_nvect[0]);
		y_m = (2 * npno[1] * d_nvect[1]);
		z_m = (2 * npno[2] * d_nvect[2]);
		refl_vel[0] = npno[0] - (d_nvect[0] * (x_m + y_m + z_m));
		refl_vel[1] = npno[1] - (d_nvect[1] * (x_m + y_m + z_m));
		refl_vel[2] = npno[2] - (d_nvect[2] * (x_m + y_m + z_m));

		/*A random variation in the damping factor........ */
		/*Get the IPO values for damping here*/
		
		if (has_ipo_code(deflection_object->ipo, OB_PD_SDAMP)) 
			damping = IPO_GetFloatValue(deflection_object->ipo, OB_PD_SDAMP, cur_time);
		else 
			damping = deflection_object->pd->pdef_damp;
		
		if (has_ipo_code(deflection_object->ipo, OB_PD_RDAMP)) 
			rdamp_val = IPO_GetFloatValue(deflection_object->ipo, OB_PD_RDAMP, cur_time);
		else 
			rdamp_val = deflection_object->pd->pdef_rdamp;

		damping = damping + ((1 - damping) * ((float)BLI_drand()*rdamp_val));
		damping = damping * damping;
        ref_plane_mag = INPR(refl_vel,d_nvect);

		if (damping > 0.999) damping = 0.999f;

		/* Now add in the damping force - only damp in the direction of */
		/* the faces normal vector */
		npno[0] = (refl_vel[0] - (d_nvect[0] * ref_plane_mag * damping));
		npno[1] = (refl_vel[1] - (d_nvect[1] * ref_plane_mag * damping));
		npno[2] = (refl_vel[2] - (d_nvect[2] * ref_plane_mag * damping));

		/* Now reset opno */
		VECCOPY(opno,npno);
		VECCOPY(forcec, force);

		/* If the particle has bounced more than four times on the same */
		/* face within this cycle (depth > 4, same face > 4 )           */
		/* Then set the force to be only that component of the force    */
		/* in the same direction as the face normal                     */
		/* i.e. subtract the component of the force in the direction    */
		/* of the face normal from the actual force                     */
		if ((ds_object == *last_object) && (ds_face == *last_face)) {
			/* Increment same_face */
			*same_face = *same_face + 1;
			if ((*same_face > 3) && (def_depth > 3)) {
            	force_mag_norm = INPR(forcec, d_nvect);
            	forcec[0] = forcec[0] - (d_nvect[0] * force_mag_norm);
                forcec[1] = forcec[1] - (d_nvect[1] * force_mag_norm);
                forcec[2] = forcec[2] - (d_nvect[2] * force_mag_norm);
			}
		}
		else *same_face = 1;

		*last_object = ds_object;
		*last_face = ds_face;

		/* We have the particles speed at the point of collision    */
		/* Now we want the particles speed at the current key frame */

		npno[0]= npno[0] + time_after*forcec[0];
		npno[1]= npno[1] + time_after*forcec[1];
		npno[2]= npno[2] + time_after*forcec[2];

		/* Now we have to recalculate pa->co for the remainder*/
		/* of the time since the intersect*/
		npco[0]= npco[0] + time_after*npno[0];
		npco[1]= npco[1] + time_after*npno[1];
		npco[2]= npco[2] + time_after*npno[2];

		/* And set the old co-ordinates back to the point just above the intersection */
		VECCOPY(opco, d_i_co_above);

		/* Finally update the time */
		life = time_after;
		cur_time += time_before;

		/* The particle may have fallen through the face again by now!!*/
		/* So check if the particle has changed sides of the plane compared*/
		/* the co-ordinates at the last keyframe*/
		/* But only do this as a last resort, if we've got to the end of the */
		/* number of collisions allowed */
		if (def_depth==9) {
			k_point3 = INPR(d_nvect,npco);
			if (((dk_plane > k_point3) && (dk_plane < dk_point1))||((dk_plane < k_point3) && (dk_plane > dk_point1))) {

				/* Yup, the pesky particle may have fallen through a hole!!! */
                /* So we'll cheat a bit and move the particle along the normal vector */
                /* until it's just the other side of the plane */
                icalctop = (dk_plane - d_nvect[0]*npco[0] - d_nvect[1]*npco[1] - d_nvect[2]*npco[2]);
                icalcbot = (d_nvect[0]*d_nvect[0] + d_nvect[1]*d_nvect[1] + d_nvect[2]*d_nvect[2]);
                dist_to_plane = icalctop / icalcbot;

                /*  Now just increase the distance a little to place */
                /* the point the other side of the plane */
                dist_to_plane *= 1.1f;
                npco[0]= npco[0] + (dist_to_plane * d_nvect[0]);
                npco[1]= npco[1] + (dist_to_plane * d_nvect[1]);
                npco[2]= npco[2] + (dist_to_plane * d_nvect[2]);

			}
		}
	}
	return deflected;
}

void make_particle_keys(int depth, int nr, PartEff *paf, Particle *part, float *force, int deform, MTex *mtex, unsigned int par_layer)
{
	Particle *pa, *opa = NULL;
	float damp, deltalife, life;
	float cur_time;
	float opco[3], opno[3], npco[3], npno[3], new_force[3], new_speed[3];
	int b, rt1, rt2, deflected, deflection, finish_defs, def_count;
	int last_ob, last_fc, same_fc;

	damp= 1.0f-paf->damp;
	pa= part;

	/* start speed: random */
	if(paf->randfac!=0.0) {
		pa->no[0]+= (float)(paf->randfac*( BLI_drand() -0.5));
		pa->no[1]+= (float)(paf->randfac*( BLI_drand() -0.5));
		pa->no[2]+= (float)(paf->randfac*( BLI_drand() -0.5));
	}

	/* start speed: texture */
	if(mtex && paf->texfac!=0.0) {
		particle_tex(mtex, paf, pa->co, pa->no);
	}

	if(paf->totkey>1) deltalife= pa->lifetime/(paf->totkey-1);
	else deltalife= pa->lifetime;

	opa= pa;
	pa++;

	b= paf->totkey-1;
	while(b--) {
		/* new time */
		pa->time= opa->time+deltalife;

		/* set initial variables                                */
		opco[0] = opa->co[0];
		opco[1] = opa->co[1];
		opco[2] = opa->co[2];

		new_force[0] = force[0];
		new_force[1] = force[1];
		new_force[2] = force[2];
		new_speed[0] = 0.0;
		new_speed[1] = 0.0;
		new_speed[2] = 0.0;

		/* Check force field */
		cur_time = pa->time;
		pdDoEffector(opco, new_force, new_speed, cur_time, par_layer,0);

		/* new location */
		pa->co[0]= opa->co[0] + deltalife * (opa->no[0] + new_speed[0] + 0.5f*new_force[0]);
		pa->co[1]= opa->co[1] + deltalife * (opa->no[1] + new_speed[1] + 0.5f*new_force[1]);
		pa->co[2]= opa->co[2] + deltalife * (opa->no[2] + new_speed[2] + 0.5f*new_force[2]);

		/* new speed */
		pa->no[0]= opa->no[0] + deltalife*new_force[0];
		pa->no[1]= opa->no[1] + deltalife*new_force[1];
		pa->no[2]= opa->no[2] + deltalife*new_force[2];

		/* Particle deflection code                             */
		deflection = 0;
		finish_defs = 1;
		def_count = 0;

		VECCOPY(opno, opa->no);
		VECCOPY(npco, pa->co);
		VECCOPY(npno, pa->no);

		life = deltalife;
		cur_time -= deltalife;

		last_ob = -1;
		last_fc = -1;
		same_fc = 0;

		/* First call the particle deflection check for the particle moving   */
		/* between the old co-ordinates and the new co-ordinates              */
		/* If a deflection occurs, call the code again, this time between the */
		/* intersection point and the updated new co-ordinates                */
		/* Bail out if we've done the calculation 10 times - this seems ok     */
        /* for most scenes I've tested */
		while (finish_defs) {
			deflected =  pdDoDeflection(opco, npco, opno, npno, life, new_force,
							def_count, cur_time, par_layer,
							&last_ob, &last_fc, &same_fc);
			if (deflected) {
				def_count = def_count + 1;
				deflection = 1;
				if (def_count==10) finish_defs = 0;
			}
			else {
				finish_defs = 0;
			}
		}

		/* Only update the particle positions and speed if we had a deflection */
		if (deflection) {
			pa->co[0] = npco[0];
			pa->co[1] = npco[1];
			pa->co[2] = npco[2];
			pa->no[0] = npno[0];
			pa->no[1] = npno[1];
			pa->no[2] = npno[2];
		}


		/* speed: texture */
		if(mtex && paf->texfac!=0.0) {
			particle_tex(mtex, paf, pa->co, pa->no);
		}
		if(damp!=1.0) {
			pa->no[0]*= damp;
			pa->no[1]*= damp;
			pa->no[2]*= damp;
		}
	


		opa= pa;
		pa++;
		/* opa is used later on too! */
	}

	if(deform) {
		/* deform all keys */
		pa= part;
		b= paf->totkey;
		while(b--) {
			calc_latt_deform(pa->co);
			pa++;
		}
	}
	
	/* the big multiplication */
	if(depth<PAF_MAXMULT && paf->mult[depth]!=0.0) {
		
		/* new 'child' emerges from an average 'mult' part from 
			the particles */
		damp = (float)nr;
		rt1= (int)(damp*paf->mult[depth]);
		rt2= (int)((damp+1.0)*paf->mult[depth]);
		if(rt1!=rt2) {
			
			for(b=0; b<paf->child[depth]; b++) {
				pa= new_particle(paf);
				*pa= *opa;
				pa->lifetime= paf->life[depth];
				if(paf->randlife!=0.0) {
					pa->lifetime*= 1.0f+ (float)(paf->randlife*( BLI_drand() - 0.5));
				}
				pa->mat_nr= paf->mat[depth];

				make_particle_keys(depth+1, b, paf, pa, force, deform, mtex, par_layer);
			}
		}
	}
}

void init_mv_jit(float *jit, int num,int seed2)
{
	float *jit2, x, rad1, rad2, rad3;
	int i, num2;

	if(num==0) return;

	rad1= (float)(1.0/sqrt((float)num));
	rad2= (float)(1.0/((float)num));
	rad3= (float)sqrt((float)num)/((float)num);

	BLI_srand(31415926 + num + seed2);
	x= 0;
        num2 = 2 * num;
	for(i=0; i<num2; i+=2) {
	
		jit[i]= x+ (float)(rad1*(0.5-BLI_drand()));
		jit[i+1]= ((float)i/2)/num +(float)(rad1*(0.5-BLI_drand()));
		
		jit[i]-= (float)floor(jit[i]);
		jit[i+1]-= (float)floor(jit[i+1]);
		
		x+= rad3;
		x -= (float)floor(x);
	}

	jit2= MEM_mallocN(12 + 2*sizeof(float)*num, "initjit");

	for (i=0 ; i<4 ; i++) {
		RE_jitterate1(jit, jit2, num, rad1);
		RE_jitterate1(jit, jit2, num, rad1);
		RE_jitterate2(jit, jit2, num, rad2);
	}
	MEM_freeN(jit2);
}


static void give_mesh_mvert(Mesh *me, DispListMesh *dlm, int nr, float *co, short *no, int seed2)
{
	static float *jit=0;
	static int jitlevel=1;
	MVert *mvert, *mvertbase=NULL;
	MFace *mface, *mfacebase=NULL;
	float u, v, *v1, *v2, *v3, *v4;
	int totface=0, totvert=0, curface, curjit;
	short *n1, *n2, *n3, *n4;
	
	/* signal */
	if(me==0) {
		if(jit) MEM_freeN(jit);
		jit= 0;
		return;
	}
	
	if(dlm) {
		mvertbase= dlm->mvert;
		mfacebase= dlm->mface;
		totface= dlm->totface;
		totvert= dlm->totvert;
	}
	
	if(totvert==0) {
		mvertbase= me->mvert;
		mfacebase= me->mface;
		totface= me->totface;
		totvert= me->totvert;
	}
	
	if(totface==0 || nr<totvert) {
		mvert= mvertbase + (nr % totvert);
		VECCOPY(co, mvert->co);
		VECCOPY(no, mvert->no);
	}
	else {

		nr-= totvert;
		
		if(jit==0) {
			jitlevel= nr/totface;
			if(jitlevel==0) jitlevel= 1;
			if(jitlevel>100) jitlevel= 100;

			jit= MEM_callocN(2+ jitlevel*2*sizeof(float), "jit");
			init_mv_jit(jit, jitlevel,seed2);
			
		}

		curjit= nr/totface;
		curjit= curjit % jitlevel;

		curface= nr % totface;
		
		mface= mfacebase;
		mface+= curface;

		v1= (mvertbase+(mface->v1))->co;
		v2= (mvertbase+(mface->v2))->co;
		n1= (mvertbase+(mface->v1))->no;
		n2= (mvertbase+(mface->v2))->no;
		if(mface->v3==0) {
			v3= (mvertbase+(mface->v2))->co;
			v4= (mvertbase+(mface->v1))->co;
			n3= (mvertbase+(mface->v2))->no;
			n4= (mvertbase+(mface->v1))->no;
		}
		else if(mface->v4==0) {
			v3= (mvertbase+(mface->v3))->co;
			v4= (mvertbase+(mface->v1))->co;
			n3= (mvertbase+(mface->v3))->no;
			n4= (mvertbase+(mface->v1))->no;
		}
		else {
			v3= (mvertbase+(mface->v3))->co;
			v4= (mvertbase+(mface->v4))->co;
			n3= (mvertbase+(mface->v3))->no;
			n4= (mvertbase+(mface->v4))->no;
		}

		u= jit[2*curjit];
		v= jit[2*curjit+1];

		co[0]= (float)((1.0-u)*(1.0-v)*v1[0] + (1.0-u)*(v)*v2[0] + (u)*(v)*v3[0] + (u)*(1.0-v)*v4[0]);
		co[1]= (float)((1.0-u)*(1.0-v)*v1[1] + (1.0-u)*(v)*v2[1] + (u)*(v)*v3[1] + (u)*(1.0-v)*v4[1]);
		co[2]= (float)((1.0-u)*(1.0-v)*v1[2] + (1.0-u)*(v)*v2[2] + (u)*(v)*v3[2] + (u)*(1.0-v)*v4[2]);
		
		no[0]= (short)((1.0-u)*(1.0-v)*n1[0] + (1.0-u)*(v)*n2[0] + (u)*(v)*n3[0] + (u)*(1.0-v)*n4[0]);
		no[1]= (short)((1.0-u)*(1.0-v)*n1[1] + (1.0-u)*(v)*n2[1] + (u)*(v)*n3[1] + (u)*(1.0-v)*n4[1]);
		no[2]= (short)((1.0-u)*(1.0-v)*n1[2] + (1.0-u)*(v)*n2[2] + (u)*(v)*n3[2] + (u)*(1.0-v)*n4[2]);
		
	}
}


void build_particle_system(Object *ob)
{
	Base *base;
	Object *par;
	PartEff *paf;
	Particle *pa;
	Mesh *me;
	MTex *mtexmove=0;
	Material *ma;
	DispListMesh *dlm;
	int dmNeedsFree;
	DerivedMesh *dm;
	float framelenont, ftime, dtime, force[3], imat[3][3], vec[3];
	float fac, prevobmat[4][4], sfraont, co[3];
	int deform=0, a, cur, cfraont, cfralast, totpart, totvert;
	short no[3];

	if(ob->type!=OB_MESH) return;
	me= ob->data;
	if(me->totvert==0) return;

	ma= give_current_material(ob, 1);
	if(ma) {
		mtexmove= ma->mtex[7];
	}

	paf= give_parteff(ob);
	if(paf==NULL) return;

	waitcursor(1);

	disable_speed_curve(1);

	/* generate all particles */
	if(paf->keys) MEM_freeN(paf->keys);
	paf->keys= NULL;
	new_particle(paf);

	/* reset deflector cache, sumohandle is free, but its still sorta abuse... (ton) */
	for(base= G.scene->base.first; base; base= base->next) {
		base->object->sumohandle= NULL;
	}

	cfraont= G.scene->r.cfra;
	cfralast= -1000;
	framelenont= G.scene->r.framelen;
	G.scene->r.framelen= 1.0;
	sfraont= ob->sf;
	ob->sf= 0.0;

	/* mult generations? */
	totpart= paf->totpart;
	for(a=0; a<PAF_MAXMULT; a++) {
		if(paf->mult[a]!=0.0) {
			/* interessant formula! this way after 'x' generations the total is paf->totpart */
			totpart= (int)(totpart / (1.0+paf->mult[a]*paf->child[a]));
		}
		else break;
	}

	ftime= paf->sta;
	dtime= (paf->end - paf->sta)/totpart;

	/* remember full hierarchy */
	par= ob;
	while(par) {
		pushdata(par, sizeof(Object));
		par= par->parent;
	}
	
	/* for static particles, calculate system on current frame */
	if(ma) do_mat_ipo(ma);

	/* set it all at first frame */
	G.scene->r.cfra= cfralast= (int)floor(ftime);
	par= ob;
	while(par) {
		/* do_ob_ipo(par); */
		do_ob_key(par);
		par= par->parent;
	}
	
	if((paf->flag & PAF_STATIC)==0) {
		if(ma) do_mat_ipo(ma);	// nor for static
		
		where_is_object(ob);
		Mat4CpyMat4(prevobmat, ob->obmat);
		Mat4Invert(ob->imat, ob->obmat);
		Mat3CpyMat4(imat, ob->imat);
	}
	else {
		Mat4One(prevobmat);
		Mat3One(imat);
	}
	
	BLI_srand(paf->seed);
	
	/* otherwise it goes way too fast */
	force[0]= paf->force[0]*0.05f;
	force[1]= paf->force[1]*0.05f;
	force[2]= paf->force[2]*0.05f;
	
	if( paf->flag & PAF_STATIC ) deform= 0;
	else {
		deform= (ob->parent && ob->parent->type==OB_LATTICE);
		if(deform) init_latt_deform(ob->parent, 0);
	}
	
	/* init */
	
		/* this call returns NULL during editmode, just ignore it and
		 * particles should be recalc'd on exit.
		 */
	dm = mesh_get_derived_final(ob, &dmNeedsFree);
	if (!dm) {
		waitcursor(0);
		return;
	}

	dlm = dm->convertToDispListMesh(dm);
	totvert = dlm->totvert;

	give_mesh_mvert(me, dlm, totpart, co, no, paf->seed);
	
	if(G.f & G_DEBUG) {
		printf("\n");
		printf("Calculating particles......... \n");
	}
	for(a=0; a<totpart; a++, ftime+=dtime) {
		
		pa= new_particle(paf);
		pa->time= ftime;
		
		if(G.f & G_DEBUG) {
			int b, c;
			
			c = totpart/100;
			if (c==0){
				c = 1;
			}

			b=(a%c);
			if (b==0) {
				printf("\r Particle: %d / %d ", a, totpart);
				fflush(stdout);
			}
		}
		/* set ob at correct time */
		
		if((paf->flag & PAF_STATIC)==0) {

			cur= (int)floor(ftime) + 1 ;		/* + 1 has a reason: (obmat/prevobmat) otherwise comet-tails start too late */
			if(cfralast != cur) {
				G.scene->r.cfra= cfralast= cur;
	
				/* added later: blur? */
				bsystem_time(ob, ob->parent, (float)G.scene->r.cfra, 0.0);

				par= ob;
				while(par) {
					/* do_ob_ipo(par); */
					par->ctime= -1234567.0;
					do_ob_key(par);
					if(par->type==OB_ARMATURE) {
						do_all_actions(par);	// only does this object actions
//						clear_object_constraint_status(par);	// mysterious call, otherwise do_actions doesnt work???
					}
					par= par->parent;
				}
				if(ma) do_mat_ipo(ma);
				Mat4CpyMat4(prevobmat, ob->obmat);
				where_is_object(ob);
				Mat4Invert(ob->imat, ob->obmat);
				Mat3CpyMat4(imat, ob->imat);
			}
		}
		/* get coordinates */
		if(paf->flag & PAF_FACE) give_mesh_mvert(me, dlm, a, co, no, paf->seed);
		else {
			if (totvert) {
				VECCOPY(co, dlm->mvert[a%totvert].co);
				VECCOPY(no, dlm->mvert[a%totvert].no);
			} else {
				co[0] = co[1] = co[2] = 0.0f;
				no[0] = no[1] = no[2] = 0;
			}
		}
		
		VECCOPY(pa->co, co);
		
		if(paf->flag & PAF_STATIC);
		else {
			Mat4MulVecfl(ob->obmat, pa->co);
		
			VECCOPY(vec, co);
			Mat4MulVecfl(prevobmat, vec);
			
			/* first start speed: object */
			VECSUB(pa->no, pa->co, vec);
			VecMulf(pa->no, paf->obfac);
			
			/* calculate the correct inter-frame */	
			fac= (ftime- (float)floor(ftime));
			pa->co[0]= fac*pa->co[0] + (1.0f-fac)*vec[0];
			pa->co[1]= fac*pa->co[1] + (1.0f-fac)*vec[1];
			pa->co[2]= fac*pa->co[2] + (1.0f-fac)*vec[2];
		}

		/* start speed: normal */
		if(paf->normfac!=0.0) {
				/* transpose ! */
			vec[0]= imat[0][0]*no[0] + imat[0][1]*no[1] + imat[0][2]*no[2];
			vec[1]= imat[1][0]*no[0] + imat[1][1]*no[1] + imat[1][2]*no[2];
			vec[2]= imat[2][0]*no[0] + imat[2][1]*no[1] + imat[2][2]*no[2];		
		
			Normalise(vec);
			VecMulf(vec, paf->normfac);
			VECADD(pa->no, pa->no, vec);
		}
		pa->lifetime= paf->lifetime;
		if(paf->randlife!=0.0) {
			pa->lifetime*= 1.0f+ (float)(paf->randlife*( BLI_drand() - 0.5));
		}
		pa->mat_nr= 1;
		
		make_particle_keys(0, a, paf, pa, force, deform, mtexmove, ob->lay);
	}
	
	if(G.f & G_DEBUG) {
		printf("\r Particle: %d / %d \n", totpart, totpart);
		fflush(stdout);
	}	
	if(deform) end_latt_deform();
		
	/* restore */
	G.scene->r.cfra= cfraont;
	G.scene->r.framelen= framelenont;
	give_mesh_mvert(0, 0, 0, 0, 0,paf->seed);

	/* put hierarchy back */
	par= ob;
	while(par) {
		popfirst(par);
		/* do not do ob->ipo: keep insertkey */
		do_ob_key(par);
		
		if(par->type==OB_ARMATURE) {
			do_all_actions(par);	// only does this object actions
//			clear_object_constraint_status(par);	// mysterious call, otherwise do_actions doesnt work???
		}
		par= par->parent;
	}

	/* reset deflector cache */
	for(base= G.scene->base.first; base; base= base->next) {
		if(base->object->sumohandle) {
			MEM_freeN(base->object->sumohandle);
			base->object->sumohandle= NULL;
		}
	}

	/* restore: AFTER popfirst */
	ob->sf= sfraont;

	if(ma) do_mat_ipo(ma);	// set back on current time
	disable_speed_curve(0);
	
	waitcursor(0);

	displistmesh_free(dlm);
	if (dmNeedsFree) dm->release(dm);
}

/* ************* WAVE **************** */

void init_wave_deform(WaveEff *wav) {
	wav->minfac= (float)(1.0/exp(wav->width*wav->narrow*wav->width*wav->narrow));
	if(wav->damp==0) wav->damp= 10.0f;
}

void calc_wave_deform(WaveEff *wav, float ctime, float *co)
{
	/* co is in local coords */
	float lifefac, x, y, amplit;
	
	/* actually this should not happen */
	if((wav->flag & (WAV_X+WAV_Y))==0) return;	

	lifefac= wav->height;
	
	if( wav->lifetime!=0.0) {
		x= ctime - wav->timeoffs;
		if(x>wav->lifetime) {
			
			lifefac= x-wav->lifetime;
			
			if(lifefac > wav->damp) lifefac= 0.0;
			else lifefac= (float)(wav->height*(1.0 - sqrt(lifefac/wav->damp)));
		}
	}
	if(lifefac==0.0) return;

	x= co[0]-wav->startx;
	y= co[1]-wav->starty;

	if(wav->flag & WAV_X) {
		if(wav->flag & WAV_Y) amplit= (float)sqrt( (x*x + y*y));
		else amplit= x;
	}
	else amplit= y;
	
	/* this way it makes nice circles */
	amplit-= (ctime-wav->timeoffs)*wav->speed;

	if(wav->flag & WAV_CYCL) {
		amplit = (float)fmod(amplit-wav->width, 2.0*wav->width) + wav->width;
	}

	/* GAUSSIAN */
	
	if(amplit> -wav->width && amplit<wav->width) {
	
		amplit = amplit*wav->narrow;
		amplit= (float)(1.0/exp(amplit*amplit) - wav->minfac);

		co[2]+= lifefac*amplit;
	}
}

int SoftBodyDetectCollision(float opco[3], float npco[3], float colco[3],
							float facenormal[3], float *damp, float force[3], int mode,
							float cur_time, unsigned int par_layer,struct Object *vertexowner)
{
	Base *base;
	Object *ob, *deflection_object = NULL;
	Mesh *def_mesh;
	MFace *mface, *deflection_face = NULL;
	float *v1, *v2, *v3, *v4, *vcache=NULL;
	float mat[3][3];
	float nv1[3], nv2[3], nv3[3], nv4[3], edge1[3], edge2[3],d_nvect[3], obloc[3];
	float dv1[3], dv2[3], dv3[3];
	float facedist,n_mag,t,t2, min_t,force_mag_norm;
	int a, deflected=0, deflected_now=0;
	short cur_frame;
	int d_object=0, d_face=0, ds_object=0, ds_face=0;
	
	// i'm going to rearrange it to declaration rules when WIP is finished (BM)
	float innerfacethickness = -0.5f;
	float outerfacethickness = 0.2f;
	float ee = 5.0f;
	float ff = 0.1f;
	float fa;
	
	min_t = 200000;
	
	/* The first part of the code, finding the first intersected face*/
	base= G.scene->base.first;
	while (base) {
		/*Only proceed for mesh object in same layer */
		if(base->object->type==OB_MESH && (base->lay & par_layer)) {
			ob= base->object;
			if((vertexowner) && (ob == vertexowner)){ 
			/* if vertexowner is given 
				* we don't want to check collision with owner object */ 
				base = base->next;
				continue;
			}
			/* only with deflecting set */
			if(ob->pd && ob->pd->deflect) {
				def_mesh= ob->data;
				
				d_object = d_object + 1;
				
				d_face = d_face + 1;
				mface= def_mesh->mface;
				a = def_mesh->totface;
				/* need to have user control for that since it depends on model scale */
				
				innerfacethickness =-ob->pd->pdef_sbift;
				outerfacethickness =ob->pd->pdef_sboft;
				fa = (ff*outerfacethickness-outerfacethickness);
				fa *= fa;
				fa = 1.0f/fa;
				
				if(ob->parent==NULL && ob->ipo==NULL) {	// static
					if(ob->sumohandle==NULL) cache_object_vertices(ob);
					vcache= ob->sumohandle;
				}
				else {
					/*Find out where the object is at this time*/
					cur_frame = G.scene->r.cfra;
					G.scene->r.cfra = (short)cur_time;
					where_is_object_time(ob, cur_time);
					G.scene->r.cfra = cur_frame;
					
					/*Pass the values from ob->obmat to mat*/
					/*and the location values to obloc           */
					Mat3CpyMat4(mat,ob->obmat);
					obloc[0] = ob->obmat[3][0];
					obloc[1] = ob->obmat[3][1];
					obloc[2] = ob->obmat[3][2];
					/* not cachable */
					vcache= NULL;
					
				}
				
				while (a--) {
					
					if(vcache) {
						v1= vcache+ 3*(mface->v1);
						VECCOPY(nv1, v1);
						v1= vcache+ 3*(mface->v2);
						VECCOPY(nv2, v1);
						v1= vcache+ 3*(mface->v3);
						VECCOPY(nv3, v1);
						v1= vcache+ 3*(mface->v4);
						VECCOPY(nv4, v1);
					}
					else {
						/* Calculate the global co-ordinates of the vertices*/
						v1= (def_mesh->mvert+(mface->v1))->co;
						v2= (def_mesh->mvert+(mface->v2))->co;
						v3= (def_mesh->mvert+(mface->v3))->co;
						v4= (def_mesh->mvert+(mface->v4))->co;
						
						VECCOPY(nv1, v1);
						VECCOPY(nv2, v2);
						VECCOPY(nv3, v3);
						VECCOPY(nv4, v4);
						
						/*Apply the objects deformation matrix*/
						Mat3MulVecfl(mat, nv1);
						Mat3MulVecfl(mat, nv2);
						Mat3MulVecfl(mat, nv3);
						Mat3MulVecfl(mat, nv4);
						
						VECADD(nv1, nv1, obloc);
						VECADD(nv2, nv2, obloc);
						VECADD(nv3, nv3, obloc);
						VECADD(nv4, nv4, obloc);
					}
					
					deflected_now = 0;
					
					if (mode == 1){ // face intrusion test
						// switch origin to be nv2
						VECSUB(edge1, nv1, nv2);
						VECSUB(edge2, nv3, nv2);
						VECSUB(dv1,opco,nv2); // abuse dv1 to have vertex in question at *origin* of triangle
						
						Crossf(d_nvect, edge2, edge1);
						n_mag = Normalise(d_nvect);
						facedist = Inpf(dv1,d_nvect);
						
						if ((facedist > innerfacethickness) && (facedist < outerfacethickness)){		
							dv2[0] = opco[0] - 2.0f*facedist*d_nvect[0];
							dv2[1] = opco[1] - 2.0f*facedist*d_nvect[1];
							dv2[2] = opco[2] - 2.0f*facedist*d_nvect[2];
							if ( linetriangle( opco, dv2, nv1, nv2, nv3, &t)){
								force_mag_norm =(float)exp(-ee*facedist);
								if (facedist > outerfacethickness*ff)
									force_mag_norm =(float)force_mag_norm*fa*(facedist - outerfacethickness)*(facedist - outerfacethickness);
								
								force[0] += force_mag_norm*d_nvect[0] ;
								force[1] += force_mag_norm*d_nvect[1] ;
								force[2] += force_mag_norm*d_nvect[2] ;
								*damp=ob->pd->pdef_sbdamp;
								deflected = 2;
							}
						}		
						if (mface->v4){ // quad
							// switch origin to be nv4
							VECSUB(edge1, nv3, nv4);
							VECSUB(edge2, nv1, nv4);
							VECSUB(dv1,opco,nv4); // abuse dv1 to have vertex in question at *origin* of triangle
							
							Crossf(d_nvect, edge2, edge1);
							n_mag = Normalise(d_nvect);
							facedist = Inpf(dv1,d_nvect);
							
							if ((facedist > innerfacethickness) && (facedist < outerfacethickness)){
								dv2[0] = opco[0] - 2.0f*facedist*d_nvect[0];
								dv2[1] = opco[1] - 2.0f*facedist*d_nvect[1];
								dv2[2] = opco[2] - 2.0f*facedist*d_nvect[2];
								if ( linetriangle( opco, dv2, nv1, nv3, nv4, &t)){
									force_mag_norm =(float)exp(-ee*facedist);
									if (facedist > outerfacethickness*ff)
										force_mag_norm =(float)force_mag_norm*fa*(facedist - outerfacethickness)*(facedist - outerfacethickness);
									
									force[0] += force_mag_norm*d_nvect[0] ;
									force[1] += force_mag_norm*d_nvect[1] ;
									force[2] += force_mag_norm*d_nvect[2] ;
									*damp=ob->pd->pdef_sbdamp;
									deflected = 2;
								}
							}
							
						}
					}
					if (mode == 2){ // edge intrusion test
						
						
						//t= 0.5;	// this is labda of line, can use it optimize quad intersection
						// sorry but no .. see below (BM)					
						if( linetriangle(opco, npco, nv1, nv2, nv3, &t) ) {
							if (t < min_t) {
								deflected = 1;
								deflected_now = 1;
							}
						}
						//					else if (mface->v4 && (t>=0.0 && t<=1.0)) {
						// no, you can't skip testing the other triangle
						// it might give a smaller t on (close to) the edge .. this is numerics not esoteric maths :)
						// note: the 2 triangles don't need to share a plane ! (BM)
						if (mface->v4) {
							if( linetriangle(opco, npco, nv1, nv3, nv4, &t2) ) {
								if (t2 < min_t) {
									deflected = 1;
									deflected_now = 2;
								}
							}
						}
						
						if ((deflected_now > 0) && ((t < min_t) ||(t2 < min_t))) {
							min_t = t;
							ds_object = d_object;
							ds_face = d_face;
							deflection_object = ob;
							deflection_face = mface;
							if (deflected_now==1) {
								min_t = t;
								VECCOPY(dv1, nv1);
								VECCOPY(dv2, nv2);
								VECCOPY(dv3, nv3);
							}
							else {
								min_t = t2;
								VECCOPY(dv1, nv1);
								VECCOPY(dv2, nv3);
								VECCOPY(dv3, nv4);
							}
						}
					}  
					mface++;
				}
			}
		}
		base = base->next;
	} // while (base)
	
	if (mode == 1){ // face 
		return deflected;
	}
	
	if (mode == 2){ // edge intrusion test
		if (deflected) {
			VECSUB(edge1, dv1, dv2);
			VECSUB(edge2, dv3, dv2);
			Crossf(d_nvect, edge2, edge1);
			n_mag = Normalise(d_nvect);
			// return point of intersection
			colco[0] = opco[0] + (min_t * (npco[0] - opco[0]));
			colco[1] = opco[1] + (min_t * (npco[1] - opco[1]));
			colco[2] = opco[2] + (min_t * (npco[2] - opco[2]));
			
			VECCOPY(facenormal,d_nvect);					
		}
	}
	return deflected;
}

