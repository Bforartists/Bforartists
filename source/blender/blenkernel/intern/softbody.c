/*  softbody.c      
 * 
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
 * The Original Code is Copyright (C) Blender Foundation
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

/*
******
variables on the UI for now

	float mediafrict;  friction to env 
	float nodemass;	  softbody mass of *vertex* 
	float grav;        softbody amount of gravitaion to apply 
	
	float goalspring;  softbody goal springs 
	float goalfrict;   softbody goal springs friction 
	float mingoal;     quick limits for goal 
	float maxgoal;

	float inspring;	  softbody inner springs 
	float infrict;     softbody inner springs friction 

*****
*/


#include <math.h>
#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

/* types */
#include "DNA_curve_types.h"
#include "DNA_object_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_lattice_types.h"
#include "DNA_scene_types.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "BKE_displist.h"
#include "BKE_global.h"
#include "BKE_object.h"
#include "BKE_softbody.h"
#include "BKE_utildefines.h"

#include  "BIF_editdeform.h"

extern bDeformGroup *get_named_vertexgroup(Object *ob, char *name);
extern int  get_defgroup_num (Object *ob, bDeformGroup        *dg);


/* ********** soft body engine ******* */
#define SOFTGOALSNAP  0.999f 
// if bp-> goal is above make it a *forced follow original* and skip all ODE stuff for this bp
// removes *unnecessary* stiffnes from ODE system
#define HEUNWARNLIMIT 1 // 50 would be fine i think for detecting severe *stiff* stuff

float SoftHeunTol = 1.0f; // humm .. this should be calculated from sb parameters and sizes
float steptime =  1.0f/25.0f; // translate framerate to *real* time
float rescale_grav_to_framerate = 1.0f; // since unit of g is [m/sec^2] we need translation from frames to physics time
float rescale_friction_to_framerate = 1.0f; // since unit of drag is [kg/sec] we need translation from frames to physics time

/* local prototypes */
static void softbody_scale_time(float steptime);
static int get_scalar_from_named_vertexgroup(Object *ob, char *name, int vertID, float *target);
static void free_softbody_intern(SoftBody *sb);

static void softbody_scale_time(float steptime)
{
  rescale_grav_to_framerate = steptime*steptime; 
  rescale_friction_to_framerate = steptime;
}


static int count_mesh_quads(Mesh *me)
{
	int a,result = 0;
	MFace *mface= me->mface;
	
	if(mface) {
		for(a=me->totface; a>0; a--, mface++) {
			if(mface->v4) result++;
		}
	}	
	return result;
}

static void add_mesh_quad_diag_springs(Object *ob)
{
	Mesh *me= ob->data;
	MFace *mface= me->mface;
	BodyPoint *bp;
	BodySpring *bs, *bs_new;
	int a ;
	
	if (ob->soft){
		int nofquads;
		
		nofquads = count_mesh_quads(me);
		if (nofquads) {
			/* resize spring-array to hold additional quad springs */
			bs_new= MEM_callocN( (ob->soft->totspring + nofquads *2 )*sizeof(BodySpring), "bodyspring");
			memcpy(bs_new,ob->soft->bspring,(ob->soft->totspring )*sizeof(BodySpring));
			
			if(ob->soft->bspring)
				MEM_freeN(ob->soft->bspring); /* do this before reassigning the pointer  or have a 1st class memory leak */
			ob->soft->bspring = bs_new; 
			
			/* fill the tail */
			a = 0;
			bs = bs_new+ob->soft->totspring;
			bp= ob->soft->bpoint;
			if(mface ) {
				for(a=me->totface; a>0; a--, mface++) {
					if(mface->v4) {
						bs->v1= mface->v1;
						bs->v2= mface->v3;
						bs->strength= 1.0;
						bs->len= VecLenf( (bp+bs->v1)->origS, (bp+bs->v2)->origS);
						bs++;
						bs->v1= mface->v2;
						bs->v2= mface->v4;
						bs->strength= 1.0;
						bs->len= VecLenf( (bp+bs->v1)->origS, (bp+bs->v2)->origS);
						bs++;
						
					}
				}	
			}
			
            /* now we can announce new springs */
			ob->soft->totspring += nofquads *2;
		}
	}
}


static void add_bp_springlist(BodyPoint *bp,int springID)
{
	int *newlist;
	
	if (bp->springs == NULL) {
		bp->springs = MEM_callocN( sizeof(int), "bpsprings");
		bp->springs[0] = springID;
		bp->nofsprings = 1;
	}
	else {
		bp->nofsprings++;
		newlist = MEM_callocN(bp->nofsprings * sizeof(int), "bpsprings");
		memcpy(newlist,bp->springs,(bp->nofsprings-1)* sizeof(int));
		MEM_freeN(bp->springs);
		bp->springs = newlist;
		bp->springs[bp->nofsprings-1] = springID;
	}
}

/* do this once when sb is build
it is O(N^2) so scanning for springs every iteration is too expensive
*/
static void build_bps_springlist(Object *ob)
{
	SoftBody *sb= ob->soft;	// is supposed to be there
	BodyPoint *bp;	
	BodySpring *bs;	
	int a,b;
	
	if (sb==NULL) return; // paranoya check
	
	for(a=sb->totpoint, bp= sb->bpoint; a>0; a--, bp++) {
		/* scan for attached inner springs */	
		for(b=sb->totspring, bs= sb->bspring; b>0; b--, bs++) {
			if (( (sb->totpoint-a) == bs->v1) ){ 
				add_bp_springlist(bp,sb->totspring -b);
			}
			if (( (sb->totpoint-a) == bs->v2) ){ 
				add_bp_springlist(bp,sb->totspring -b);
			}
		}//for springs
		// if (bp->nofsprings) printf(" node %d has %d spring links\n",a,bp->nofsprings);
	}//for bp		
}


/* creates new softbody if didn't exist yet, makes new points and springs arrays */
/* called in mesh_to_softbody */
static void renew_softbody(Object *ob, int totpoint, int totspring)  
{
	SoftBody *sb;
	
	if(ob->soft==NULL) ob->soft= sbNew();
	else free_softbody_intern(ob->soft);
	sb= ob->soft;
	   
	if(totpoint) {
		sb->totpoint= totpoint;
		sb->totspring= totspring;
		
		sb->bpoint= MEM_mallocN( totpoint*sizeof(BodyPoint), "bodypoint");
		if(totspring) 
			sb->bspring= MEM_mallocN( totspring*sizeof(BodySpring), "bodyspring");
	}
}

/* only frees internal data */
static void free_softbody_intern(SoftBody *sb)
{
	if(sb) {
		int a;
		BodyPoint *bp;
		
		if(sb->bpoint){
			for(a=sb->totpoint, bp= sb->bpoint; a>0; a--, bp++) {
				/* free spring list */ 
				if (bp->springs != NULL) {
					MEM_freeN(bp->springs);
				}
			}
			MEM_freeN(sb->bpoint);
		}
		
		if(sb->bspring) MEM_freeN(sb->bspring);
		
		sb->totpoint= sb->totspring= 0;
		sb->bpoint= NULL;
		sb->bspring= NULL;
	}
}


/* ************ dynamics ********** */

/* aye this belongs to arith.c */
static void Vec3PlusStVec(float *v, float s, float *v1)
{
	v[0] += s*v1[0];
	v[1] += s*v1[1];
	v[2] += s*v1[2];
}


static void softbody_calc_forces(Object *ob, float dtime)
{
	SoftBody *sb= ob->soft;	// is supposed to be there
	BodyPoint  *bp;
	BodyPoint *bproot;
	BodySpring *bs;	
	float iks, ks, kd, gravity, actspringlen, forcefactor, sd[3];
	int a, b;
	
	/* clear forces */
	for(a=sb->totpoint, bp= sb->bpoint; a>0; a--, bp++) {
		bp->force[0]= bp->force[1]= bp->force[2]= 0.0;
	}
	
	gravity = sb->nodemass * sb->grav * rescale_grav_to_framerate;	
	iks  = 1.0f/(1.0f-sb->inspring)-1.0f ;/* inner spring constants function */
	bproot= sb->bpoint; /* need this for proper spring addressing */
	
	for(a=sb->totpoint, bp= sb->bpoint; a>0; a--, bp++) {
		if(bp->goal < SOFTGOALSNAP){ // ommit this bp when i snaps
			float auxvect[3]; // aux unit vector  
			float velgoal[3];
			float absvel =0, projvel= 0;
			
			/* do goal stuff */
			if(ob->softflag & OB_SB_GOAL) {
				/* true elastic goal */
				VecSubf(auxvect,bp->origT,bp->pos);
				ks  = 1.0f/(1.0f- bp->goal*sb->goalspring)-1.0f ;
				bp->force[0]= ks*(auxvect[0]);
				bp->force[1]= ks*(auxvect[1]);
				bp->force[2]= ks*(auxvect[2]);
				/* calulate damping forces generated by goals*/
				VecSubf(velgoal,bp->origS, bp->origE);
				kd =  sb->goalfrict * rescale_friction_to_framerate ;

				if (dtime > 0.0 ) { // make sure friction does not become rocket motor on time reversal
					bp->force[0]-= kd * (velgoal[0] + bp->vec[0]);
					bp->force[1]-= kd * (velgoal[1] + bp->vec[1]);
					bp->force[2]-= kd * (velgoal[2] + bp->vec[2]);
				}
				else {
					bp->force[0]-= kd * (velgoal[0] - bp->vec[0]);
					bp->force[1]-= kd * (velgoal[1] - bp->vec[1]);
					bp->force[2]-= kd * (velgoal[2] - bp->vec[2]);
				}
			}
			/* done goal stuff */
			
			
			/* gravitation */
			bp->force[2]-= gravity*sb->nodemass; /* individual mass of node here */
			
			/* friction in media */
			kd= sb->mediafrict* rescale_friction_to_framerate;  
			/* assume it to be proportional to actual velocity */
			bp->force[0]-= bp->vec[0]*kd;
			bp->force[1]-= bp->vec[1]*kd;
			bp->force[2]-= bp->vec[2]*kd;
			/* friction in media done */

			/*other forces*/
			/* this is the place where other forces can be added
			yes, constraints and collision stuff should go here too (read baraff papers on that!)
			*/
			/*other forces done*/

			/* nice things could be done with anisotropic friction
			like wind/air resistance in normal direction
			--> having a piece of cloth sailing down 
			but this needs to have a *valid* vertex normal
			*valid* means to be calulated on time axis
			hrms .. may be a rough one could be used as well .. let's see 
			*/

			if(ob->softflag & OB_SB_EDGES) {
				if (1){ /* big mesh optimization */
					/* run over attached inner spring list */	
					if (sb->bspring){ // spring list exists at all ? 
						for(b=bp->nofsprings;b>0;b--){
							bs = sb->bspring + bp->springs[b-1];
							if (( (sb->totpoint-a) == bs->v1) ){ 
								actspringlen= VecLenf( (bproot+bs->v2)->pos, bp->pos);
								VecSubf(sd,(bproot+bs->v2)->pos, bp->pos);
								Normalise(sd);

								// friction stuff V1
								VecSubf(velgoal,bp->vec,(bproot+bs->v2)->vec);
								kd = sb->infrict * rescale_friction_to_framerate ;
								absvel  = Normalise(velgoal);
								projvel = ABS(Inpf(sd,velgoal));
								kd *= absvel * projvel;
								Vec3PlusStVec(bp->force,-kd,velgoal);
								
								if(bs->len > 0.0) /* check for degenerated springs */
									forcefactor = (bs->len - actspringlen)/bs->len * iks;
								else
									forcefactor = actspringlen * iks;
								
								Vec3PlusStVec(bp->force,-forcefactor,sd);

							}
							
							if (( (sb->totpoint-a) == bs->v2) ){ 
								actspringlen= VecLenf( (bproot+bs->v1)->pos, bp->pos);
								VecSubf(sd,bp->pos,(bproot+bs->v1)->pos);
								Normalise(sd);

								// friction stuff V2
								VecSubf(velgoal,bp->vec,(bproot+bs->v1)->vec);
								kd = sb->infrict * rescale_friction_to_framerate ;
								absvel  = Normalise(velgoal);
								projvel = ABS(Inpf(sd,velgoal));
								kd *= absvel * projvel;
								Vec3PlusStVec(bp->force,-kd,velgoal);
								
								if(bs->len > 0.0)
									forcefactor = (bs->len - actspringlen)/bs->len * iks;
								else
									forcefactor = actspringlen * iks;
								Vec3PlusStVec(bp->force,+forcefactor,sd);							
							}
						}
					} //if spring list exists at all ?
				}
				else{ // this branch is not completly uptaded for friction stuff 
					/* scan for attached inner springs makes it a O(N^2) thing = bad !*/	
					/* obsolete .. but if someone wants to try the effect :) */
					for(b=sb->totspring, bs= sb->bspring; b>0; b--, bs++) {
						if (( (sb->totpoint-a) == bs->v1) ){ 
							actspringlen= VecLenf( (bproot+bs->v2)->pos, bp->pos);
							VecSubf(sd,(bproot+bs->v2)->pos, bp->pos);
							Normalise(sd);


							if(bs->len > 0.0) /* check for degenerated springs */
								forcefactor = (bs->len - actspringlen)/bs->len * iks;
							else
								forcefactor = actspringlen * iks;
							Vec3PlusStVec(bp->force,-forcefactor,sd);
						}
						
						if (( (sb->totpoint-a) == bs->v2) ){ 
							actspringlen= VecLenf( (bproot+bs->v1)->pos, bp->pos);
							VecSubf(sd,bp->pos,(bproot+bs->v1)->pos);
							Normalise(sd);
							
							if(bs->len > 0.0)
								forcefactor = (bs->len - actspringlen)/bs->len * iks;
							else
								forcefactor = actspringlen * iks;
							Vec3PlusStVec(bp->force,+forcefactor,sd);						
						}
					}// no snap
				}//for
			}// if use edges
		}	
	}
}

static void softbody_apply_forces(Object *ob, float dtime, int mode, float *err)
{
	/* time evolution */
	/* actually does an explicit euler step mode == 0 */
	/* or heun ~ 2nd order runge-kutta steps, mode 1,2 */
	SoftBody *sb= ob->soft;	// is supposed to be there
	BodyPoint *bp;
	float dx[3],dv[3];
	float timeovermass;
	float maxerr = 0.0;
	int a;
	
	if (sb->nodemass > 0.09999f) timeovermass = dtime/sb->nodemass;
	else timeovermass = dtime/0.09999f;
	
	for(a=sb->totpoint, bp= sb->bpoint; a>0; a--, bp++) {
		if(bp->goal < SOFTGOALSNAP){
			
			/* so here is dv/dt = a = sum(F_springs)/m + gravitation + some friction forces */
			/* the euler step for velocity then becomes */
			/* v(t + dt) = v(t) + a(t) * dt */ 
			bp->force[0]*= timeovermass; /* individual mass of node here */ 
			bp->force[1]*= timeovermass;
			bp->force[2]*= timeovermass;
			/* some nasty if's to have heun in here too */
			VECCOPY(dv,bp->force); 
			if (mode == 1){
				VECCOPY(bp->prevvec, bp->vec);
				VECCOPY(bp->prevdv, dv);
			}
			if (mode ==2){
				/* be optimistic and execute step */
				bp->vec[0] = bp->prevvec[0] + 0.5f * (dv[0] + bp->prevdv[0]);
				bp->vec[1] = bp->prevvec[1] + 0.5f * (dv[1] + bp->prevdv[1]);
				bp->vec[2] = bp->prevvec[2] + 0.5f * (dv[2] + bp->prevdv[2]);
				/* compare euler to heun to estimate error for step sizing */
				maxerr = MAX2(maxerr,ABS(dv[0] - bp->prevdv[0]));
				maxerr = MAX2(maxerr,ABS(dv[1] - bp->prevdv[1]));
				maxerr = MAX2(maxerr,ABS(dv[2] - bp->prevdv[2]));
			}
			else {VECADD(bp->vec, bp->vec, bp->force);}

			/* so here is dx/dt = v */
			/* the euler step for location then becomes */
			/* x(t + dt) = x(t) + v(t) * dt */ 
			
			VECCOPY(dx,bp->vec);
			dx[0]*=dtime ; 
			dx[1]*=dtime ; 
			dx[2]*=dtime ; 
			
			/* again some nasty if's to have heun in here too */
			if (mode ==1){
				VECCOPY(bp->prevpos,bp->pos);
				VECCOPY(bp->prevdx ,dx);
			}
			
			if (mode ==2){
				bp->pos[0] = bp->prevpos[0] + 0.5f * ( dx[0] + bp->prevdx[0]);
				bp->pos[1] = bp->prevpos[1] + 0.5f * ( dx[1] + bp->prevdx[1]);
				bp->pos[2] = bp->prevpos[2] + 0.5f* ( dx[2] + bp->prevdx[2]);
				maxerr = MAX2(maxerr,ABS(dx[0] - bp->prevdx[0]));
				maxerr = MAX2(maxerr,ABS(dx[1] - bp->prevdx[1]));
				maxerr = MAX2(maxerr,ABS(dx[2] - bp->prevdx[2]));
			}
			else { VECADD(bp->pos, bp->pos, dx);}
			
		}//snap
	} //for
	if (err){ /* so step size will be controlled by biggest difference in slope */
		*err = maxerr;
	}
}

/* used by heun when it overshoots */
static void softbody_restore_prev_step(Object *ob)
{
	SoftBody *sb= ob->soft;	// is supposed to be there
	BodyPoint *bp;
	int a;
	
	for(a=sb->totpoint, bp= sb->bpoint; a>0; a--, bp++) {
		VECCOPY(bp->vec, bp->prevvec);
		VECCOPY(bp->pos, bp->prevpos);
	}
}


static void softbody_apply_goalsnap(Object *ob)
{
	SoftBody *sb= ob->soft;	// is supposed to be there
	BodyPoint *bp;
	int a;
	
	for(a=sb->totpoint, bp= sb->bpoint; a>0; a--, bp++) {
		if (bp->goal >= SOFTGOALSNAP){
			VECCOPY(bp->prevpos,bp->pos);
			VECCOPY(bp->pos,bp->origT);
		}		
	}
}

/* unused */
#if 0
static void softbody_force_goal(Object *ob)
{
	SoftBody *sb= ob->soft;	// is supposed to be there
	BodyPoint *bp;
	int a;
	
	for(a=sb->totpoint, bp= sb->bpoint; a>0; a--, bp++) {		
		VECCOPY(bp->pos,bp->origT);
		bp->vec[0] = bp->origE[0] - bp->origS[0];
		bp->vec[1] = bp->origE[1] - bp->origS[1];
		bp->vec[2] = bp->origE[2] - bp->origS[2];		
	}
}
#endif

/* expects full initialized softbody */
static void interpolate_exciter(Object *ob, int timescale, int time)
{
	SoftBody *sb= ob->soft;
	BodyPoint *bp;
	float f;
	int a;

	// note: i removed Mesh usage here, softbody should remain generic! (ton)
	
	f = (float)time/(float)timescale;
	
	for(a=sb->totpoint, bp= sb->bpoint; a>0; a--, bp++) {	
		bp->origT[0] = bp->origS[0] + f*(bp->origE[0] - bp->origS[0]); 
		bp->origT[1] = bp->origS[1] + f*(bp->origE[1] - bp->origS[1]); 
		bp->origT[2] = bp->origS[2] + f*(bp->origE[2] - bp->origS[2]); 
		if (bp->goal >= SOFTGOALSNAP){
			bp->vec[0] = bp->origE[0] - bp->origS[0];
			bp->vec[1] = bp->origE[1] - bp->origS[1];
			bp->vec[2] = bp->origE[2] - bp->origS[2];
		}
	}
	
	if(ob->softflag & OB_SB_EDGES) {
		/* hrms .. do springs alter their lenght ?
		bs= ob->soft->bspring;
		bp= ob->soft->bpoint;
		for(a=0; (a<me->totedge && a < ob->soft->totspring ); a++, bs++) {
			bs->len= VecLenf( (bp+bs->v1)->origT, (bp+bs->v2)->origT);
		}
		*/
	}
}


/* ************ convertors ********** */

/*  for each object type we need;
    - xxxx_to_softbody(Object *ob)      : a full (new) copy
	- xxxx_update_softbody(Object *ob)  : update refreshes current positions
    - softbody_to_xxxx(Object *ob)      : after simulation, copy vertex locations back
*/

/* helper  call */
static int object_has_edges(Object *ob) 
{
	if(ob->type==OB_MESH) {
		Mesh *me= ob->data;
		if(me->medge) return 1;
	}
	else if(ob->type==OB_LATTICE) {
		;
	}
	
	return 0;
}

/* helper  call */
static void set_body_point(Object *ob, BodyPoint *bp, float *vec)
{
	
	VECCOPY(bp->pos, vec);
	Mat4MulVecfl(ob->obmat, bp->pos);  // yep, sofbody is global coords
	VECCOPY(bp->origS, bp->pos);
	VECCOPY(bp->origE, bp->pos);
	VECCOPY(bp->origT, bp->pos);
	
	bp->vec[0]= bp->vec[1]= bp->vec[2]= 0.0;
	bp->weight= 1.0;
	bp->goal= ob->soft->defgoal;
	
	bp->nofsprings= 0;
	bp->springs= NULL;
}


/* copy original (new) situation in softbody, as result of matrices or deform */
/* is assumed to enter function with ob->soft, but can be without points */
static void mesh_update_softbody(Object *ob)
{
	Mesh *me= ob->data;
	MVert *mvert= me->mvert;
/*	MEdge *medge= me->medge;  */ /*unused*/
	BodyPoint *bp;
	int a;
	
	/* possible after a file read... */
	if(ob->soft->totpoint!=me->totvert) sbObjectToSoftbody(ob);
	
	if(me->totvert) {
	
		bp= ob->soft->bpoint;
		for(a=0; a<me->totvert; a++, mvert++, bp++) {
 			VECCOPY(bp->origS, bp->origE);
			VECCOPY(bp->origE, mvert->co);
			Mat4MulVecfl(ob->obmat, bp->origE);
			VECCOPY(bp->origT, bp->origE);
		}
		
		if(ob->softflag & OB_SB_EDGES) {
			
			/* happens when in UI edges was set */
			if(ob->soft->bspring==NULL) 
				if(object_has_edges(ob)) sbObjectToSoftbody(ob);
		
			/* hrms .. do springs alter their lenght ? (yes, mesh keys would (ton))
			if(medge) {
				bs= ob->soft->bspring;
				bp= ob->soft->bpoint;
				for(a=0; (a<me->totedge && a < ob->soft->totspring ); a++, medge++, bs++) { 
					bs->len= VecLenf( (bp+bs->v1)->origE, (bp+bs->v2)->origE);
				}
			}
			*/
		}
	}
}


static int get_scalar_from_named_vertexgroup(Object *ob, char *name, int vertID, float *target)
/* result 0 on success, else indicates error number
-- kind of *inverse* result defintion,
-- but this way we can signal error condition to caller  
-- and yes this function must not be here but in a *vertex group module*
*/
{
	bDeformGroup *locGroup = NULL;
	MDeformVert *dv;
	int i, groupindex;
	
	locGroup = get_named_vertexgroup(ob,name);
	if(locGroup){
		/* retrieve index for that group */
		groupindex =  get_defgroup_num(ob,locGroup); 
		/* spot the vert in deform vert list at mesh */
		/* todo (coder paranoya) what if ob->data is not a mesh .. */ 
		/* hrms.. would like to have the same for lattices anyhoo */
		if (((Mesh *)ob->data)->dvert) {
			dv = ((Mesh*)ob->data)->dvert + vertID;	
			/* Lets see if this vert is in the weight group */
			for (i=0; i<dv->totweight; i++){
				if (dv->dw[i].def_nr == groupindex){
					*target= dv->dw[i].weight; /* got it ! */
					return 0;
				}
			}
		}
		return 2;
	}/*if(locGroup)*/
	return 1;
} 

/* makes totally fresh start situation */
static void mesh_to_softbody(Object *ob)
{
	SoftBody *sb;
	Mesh *me= ob->data;
	MVert *mvert= me->mvert;
	MEdge *medge= me->medge;
	BodyPoint *bp;
	BodySpring *bs;
	float goalfac;
	int a, totedge;
	
	if (ob->softflag & OB_SB_EDGES) totedge= me->totedge;
	else totedge= 0;
	
	/* renew ends with ob->soft with points and edges, also checks & makes ob->soft */
	renew_softbody(ob, me->totvert, totedge);
		
	/* we always make body points */
	sb= ob->soft;	
	bp= sb->bpoint;
	goalfac= ABS(sb->maxgoal - sb->mingoal);
	
	for(a=me->totvert; a>0; a--, mvert++, bp++) {
		
		set_body_point(ob, bp, mvert->co);
		
		if (1) { /* switch to vg scalars*/
			/* get scalar values needed  *per vertex* from vertex group functions,
			   so we can *paint* them nicly .. 
			   they are normalized [0.0..1.0] so may be we need amplitude for scale
			   which can be done by caller
			   but still .. i'd like it to go this way 
			*/ 
			int error;
			char name[32] = "SOFTGOAL";
			float temp;
			
			error = get_scalar_from_named_vertexgroup(ob, name, me->totvert - a, &temp);
			if (!error) {
				bp->goal = temp;
				
				/* works assuming goal is <0.0, 1.0> */
				bp->goal= sb->mingoal + bp->goal*goalfac;
				
			}
			/* a little ad hoc changing the goal control to be less *sharp* */
			bp->goal = (float)pow(bp->goal, 4.0f);
			
			/* to proove the concept
			this would enable per vertex *mass painting*
			strcpy(name,"SOFTMASS");
			error = get_scalar_from_named_vertexgroup(ob,name,me->totvert - a,&temp);
			if (!error) bp->mass = temp * ob->rangeofmass;
			*/



		} /* switch to vg scalars */
	}

	/* but we only optionally add body edge springs */
	if (ob->softflag & OB_SB_EDGES) {
		if(medge) {
			bs= sb->bspring;
			bp= sb->bpoint;
			for(a=me->totedge; a>0; a--, medge++, bs++) {
				bs->v1= medge->v1;
				bs->v2= medge->v2;
				bs->strength= 1.0;
				bs->len= VecLenf( (bp+bs->v1)->origS, (bp+bs->v2)->origS);
			}

		
			/* insert *diagonal* springs in quads if desired */
			if (ob->softflag & OB_SB_QUADS) {
				add_mesh_quad_diag_springs(ob);
			}

			build_bps_springlist(ob); /* big mesh optimization */
		}
	}
	
}

/* copies current sofbody position in mesh, so do this within modifier stacks! */
static void softbody_to_mesh(Object *ob)
{
	Mesh *me= ob->data;
	MVert *mvert;
	BodyPoint *bp;
	int a;

	bp= ob->soft->bpoint;
	mvert= me->mvert;
	for(a=me->totvert; a>0; a--, mvert++, bp++) {
		VECCOPY(mvert->co, bp->pos);
		Mat4MulVecfl(ob->imat, mvert->co);	// softbody is in global coords
	}

}

/* makes totally fresh start situation */
static void lattice_to_softbody(Object *ob)
{
	SoftBody *sb;
	Lattice *lt= ob->data;
	BodyPoint *bop;
	BPoint *bp;
	int a, totvert;
	
	totvert= lt->pntsu*lt->pntsv*lt->pntsw;
	
	/* renew ends with ob->soft with points and edges, also checks & makes ob->soft */
	renew_softbody(ob, totvert, 0);
	
	/* we always make body points */
	sb= ob->soft;	
	
	for(a= totvert, bp= lt->def, bop= sb->bpoint; a>0; a--, bp++, bop++) {
		set_body_point(ob, bop, bp->vec);
	}
}

/* copies current sofbody position */
static void softbody_to_lattice(Object *ob)
{
	SoftBody *sb;
	Lattice *lt= ob->data;
	BodyPoint *bop;
	BPoint *bp;
	int a, totvert;
	
	totvert= lt->pntsu*lt->pntsv*lt->pntsw;
	sb= ob->soft;	
	
	for(a= totvert, bp= lt->def, bop= sb->bpoint; a>0; a--, bp++, bop++) {
		VECCOPY(bp->vec, bop->pos);
		Mat4MulVecfl(ob->imat, bp->vec);	// softbody is in global coords
	}
}

/* copy original (new) situation in softbody, as result of matrices or deform */
/* is assumed to enter function with ob->soft, but can be without points */
static void lattice_update_softbody(Object *ob)
{
	Lattice *lt= ob->data;
	BodyPoint *bop;
	BPoint *bp;
	int a, totvert;
	
	totvert= lt->pntsu*lt->pntsv*lt->pntsw;
	
	/* possible after a file read... */
	if(ob->soft->totpoint!=totvert) sbObjectToSoftbody(ob);
	
	for(a= totvert, bp= lt->def, bop= ob->soft->bpoint; a>0; a--, bp++, bop++) {
		VECCOPY(bop->origS, bop->origE);
		VECCOPY(bop->origE, bp->vec);
		Mat4MulVecfl(ob->obmat, bop->origE);
		VECCOPY(bop->origT, bop->origE);
	}	
}


/* copies softbody result back in object */
/* only used in sbObjectStep() */
static void softbody_to_object(Object *ob)
{
	
	if(ob->soft==NULL) return;
	
	/* inverse matrix is not uptodate... */
	Mat4Invert(ob->imat, ob->obmat);
	
	switch(ob->type) {
	case OB_MESH:
		softbody_to_mesh(ob);
		break;
	case OB_LATTICE:
		softbody_to_lattice(ob);
		break;
	}
}

/* copy original (new) situation in softbody, as result of matrices or deform */
/* used in sbObjectStep() and sbObjectReset() */
/* assumes to have ob->soft, but can be entered without points */
static void object_update_softbody(Object *ob)
{
	
	switch(ob->type) {
	case OB_MESH:
		mesh_update_softbody(ob);
		break;
	case OB_LATTICE:
		lattice_update_softbody(ob);
		break;
	}
	
}



/* ************ Object level, exported functions *************** */

/* allocates and initializes general main data */
SoftBody *sbNew(void)
{
	SoftBody *sb;
	
	sb= MEM_callocN(sizeof(SoftBody), "softbody");
	
	sb->mediafrict= 0.5; 
	sb->nodemass= 1.0;
	sb->grav= 0.0; 
	
	sb->goalspring= 0.5; 
	sb->goalfrict= 0.0; 
	sb->mingoal= 0.0;  
	sb->maxgoal= 1.0;
	sb->defgoal= 0.7;
	
	sb->inspring= 0.5;
	sb->infrict= 0.5; 
	
	return sb;
}

/* frees all */
void sbFree(SoftBody *sb)
{
	free_softbody_intern(sb);
	MEM_freeN(sb);
}


/* makes totally fresh start situation */
void sbObjectToSoftbody(Object *ob)
{
	
	switch(ob->type) {
	case OB_MESH:
		mesh_to_softbody(ob);
		break;
	case OB_LATTICE:
		lattice_to_softbody(ob);
		break;
	}
	
	if(ob->soft) ob->soft->ctime= bsystem_time(ob, NULL, (float)G.scene->r.cfra, 0.0);
	ob->softflag &= ~OB_SB_REDO;
}

/* reset all motion */
void sbObjectReset(Object *ob)
{
	SoftBody *sb= ob->soft;
	BodyPoint *bp;
	int a;
	
	if(sb==NULL) return;
	sb->ctime= bsystem_time(ob, NULL, (float)G.scene->r.cfra, 0.0);
	
	object_update_softbody(ob);
	
	for(a=sb->totpoint, bp= sb->bpoint; a>0; a--, bp++) {
		// origS is previous timestep
		VECCOPY(bp->origS, bp->origE);
		VECCOPY(bp->pos, bp->origE);
		VECCOPY(bp->origT, bp->origE);
		bp->vec[0]= bp->vec[1]= bp->vec[2]= 0.0f;

		// no idea about the Heun stuff! (ton)
		VECCOPY(bp->prevpos, bp->vec);
		VECCOPY(bp->prevvec, bp->vec);
		VECCOPY(bp->prevdx, bp->vec);
		VECCOPY(bp->prevdv, bp->vec);
	}
}


/* simulates one step. framenr is in frames */
/* copies result back to object, displist */
void sbObjectStep(Object *ob, float framenr)
{
	SoftBody *sb;
	float dtime;
	int timescale,t;
	float ctime, forcetime;
	float err;

	/* remake softbody if: */
	if( (ob->softflag & OB_SB_REDO) ||		// signal after weightpainting
		(ob->soft==NULL) ||					// just to be nice we allow full init
		(ob->soft->totpoint==0) ) 			// after reading new file, or acceptable as signal to refresh
			sbObjectToSoftbody(ob);
	
	sb= ob->soft;

	/* still no points? go away */
	if(sb->totpoint==0) return;
	
	/* checking time: */
	ctime= bsystem_time(ob, NULL, framenr, 0.0);
    softbody_scale_time(steptime); // translate frames/sec and lenghts unit to SI system
	dtime= ctime - sb->ctime;
		// dtime= ABS(dtime); no no we want to go back in time with IPOs
	timescale = (int)(sb->rklimit * ABS(dtime)); 
		// bail out for negative or for large steps
	if(dtime<0.0 || dtime >= 9.9*G.scene->r.framelen) {
		sbObjectReset(ob);
		return;
	}
	
	/* the simulator */
	
	if(ABS(dtime) > 0.0) {	// note: what does this mean now? (ton)
		
		object_update_softbody(ob);
		
		if (TRUE) {	// RSOL1 always true now (ton)
			/* special case of 2nd order Runge-Kutta type AKA Heun */
			float timedone =0.0;
			/* counter for emergency brake
			 * we don't want to lock up the system if physics fail
			 */
			int loops =0 ; 
			SoftHeunTol = sb->rklimit; // humm .. this should be calculated from sb parameters and sizes

			forcetime = dtime; /* hope for integrating in one step */
			while ( (ABS(timedone) < ABS(dtime)) && (loops < 2000) )
			{
				if (ABS(dtime) > 3.0 ){
					if(G.f & G_DEBUG) printf("SB_STEPSIZE \n");
					break; // sorry but i must assume goal movement can't be interpolated any more
				}
				//set goals in time
				interpolate_exciter(ob,200,(int)(200.0*(timedone/dtime)));
				// do predictive euler step
				softbody_calc_forces(ob, forcetime);
				softbody_apply_forces(ob, forcetime, 1, NULL);
				// crop new slope values to do averaged slope step
				softbody_calc_forces(ob, forcetime);
				softbody_apply_forces(ob, forcetime, 2, &err);
				softbody_apply_goalsnap(ob);

				if (err > SoftHeunTol){ // error needs to be scaled to some quantity
					softbody_restore_prev_step(ob);
					forcetime /= 2.0;
				}
				else {
					float newtime = forcetime * 1.1f; // hope for 1.1 times better conditions in next step
					
					if (err > SoftHeunTol/2.0){ // stay with this stepsize unless err really small
						newtime = forcetime;
					}
					timedone += forcetime;
					if (forcetime > 0.0)
						forcetime = MIN2(dtime - timedone,newtime);
					else 
						forcetime = MAX2(dtime - timedone,newtime);
				}
				loops++;
			}
			// move snapped to final position
			interpolate_exciter(ob, 2, 2);
			softbody_apply_goalsnap(ob);
			
			if(G.f & G_DEBUG) {
				if (loops > HEUNWARNLIMIT) /* monitor high loop counts say 1000 after testing */
					printf("%d heun integration loops/frame \n",loops);
			}
		}
		else
        /* do brute force explicit euler */
		/* inner intagration loop */
		/* */
		// loop n times so that n*h = duration of one frame := 1
		// x(t+h) = x(t) + h*v(t);
		// v(t+h) = v(t) + h*f(x(t),t);
		for(t=1 ; t <= timescale; t++) {
			if (ABS(dtime) > 15 ) break;
			
			/* the *goal* mesh must use the n*h timing too !
			use *cheap* linear intepolation for that  */
			interpolate_exciter(ob,timescale,t);			
			if (timescale > 0 ) {
				forcetime = dtime/timescale;

				/* does not fit the concept sloving ODEs :) */
				/*			softbody_apply_goal(ob,forcetime );  */
				
				/* explicit Euler integration */
				/* we are not controling a nuclear power plant! 
				so rought *almost* physical behaviour is acceptable.
				in cases of *mild* stiffnes cranking up timscale -> decreasing stepsize *h*
				avoids instability	*/
				softbody_calc_forces(ob,forcetime);
				softbody_apply_forces(ob,forcetime,0, NULL);
				softbody_apply_goalsnap(ob);

				//	if (0){
					/* ok here comes the �berhammer
					use a semi implicit euler integration to tackle *all* stiff conditions 
					but i doubt the cost/benifit holds for most of the cases
					-- to be coded*/
				//	}
				
			}
		}
		
		/* and apply to vertices */
		 softbody_to_object(ob);
		
		sb->ctime= ctime;
	} // if(ABS(dtime) > 0.0) 
	else {
		// rule : you have asked for the current state of the softobject 
		// since dtime= ctime - ob->soft->ctime;
		// and we were not notifified about any other time changes 
		// so here it is !
		softbody_to_object(ob);
	}
}

