/* boids.c
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
 * The Original Code is Copyright (C) 2009 by Janne Karhu.
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

#include "DNA_particle_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_force.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_boid_types.h"
#include "DNA_listBase.h"

#include "BLI_rand.h"
#include "BLI_arithb.h"
#include "BLI_blenlib.h"
#include "BLI_kdtree.h"
#include "BLI_kdopbvh.h"
#include "BKE_effect.h"
#include "BKE_boids.h"
#include "BKE_particle.h"
#include "BKE_utildefines.h"
#include "BKE_modifier.h"

#include "RNA_enum_types.h"

typedef struct BoidValues {
	float max_speed, max_acc;
	float max_ave, min_speed;
	float personal_space, jump_speed;
} BoidValues;

static int apply_boid_rule(BoidBrainData *bbd, BoidRule *rule, BoidValues *val, ParticleData *pa, float fuzziness);

static int rule_none(BoidRule *rule, BoidBrainData *data, BoidValues *val, ParticleData *pa)
{
	return 0;
}

static int rule_goal_avoid(BoidRule *rule, BoidBrainData *bbd, BoidValues *val, ParticleData *pa)
{
	BoidRuleGoalAvoid *gabr = (BoidRuleGoalAvoid*) rule;
	BoidSettings *boids = bbd->part->boids;
	ParticleEffectorCache *ec;
	Object *priority_ob = NULL;
	float vec[3] = {0.0f, 0.0f, 0.0f}, loc[3] = {0.0f, 0.0f, 0.0f};
	float mul = (rule->type == eBoidRuleType_Avoid ? 1.0 : -1.0);
	float priority = 0.0f, len = 0.0f;
	int ret = 0;

	/* first find out goal/predator with highest priority */
	/* if rule->ob specified use it */
	if(gabr->ob && (rule->type != eBoidRuleType_Goal || gabr->ob != pa->stick_ob)) {
		PartDeflect *pd = gabr->ob->pd;
		float vec_to_part[3];

		if(pd && pd->forcefield == PFIELD_BOID) {
			effector_find_co(bbd->scene, pa->prev_state.co, NULL, gabr->ob, pd, loc, vec, NULL, NULL);
			
			VecSubf(vec_to_part, pa->prev_state.co, loc);

			priority = mul * pd->f_strength * effector_falloff(pd, vec, vec_to_part);
		}
		else
			priority = 1.0;

		priority = 1.0;
		priority_ob = gabr->ob;
	}
	else for(ec=bbd->psys->effectors.first; ec; ec=ec->next) {
		if(ec->type & PSYS_EC_EFFECTOR) {
			Object *eob = ec->ob;
			PartDeflect *pd = eob->pd;

			/* skip current object */
			if(rule->type == eBoidRuleType_Goal && eob == pa->stick_ob)
				continue;

			if(pd->forcefield == PFIELD_BOID && mul * pd->f_strength > 0.0f) {
				float vec_to_part[3], temp;

				effector_find_co(bbd->scene, pa->prev_state.co, NULL, eob, pd, loc, vec, NULL, NULL);
				
				VecSubf(vec_to_part, pa->prev_state.co, loc);

				temp = mul * pd->f_strength * effector_falloff(pd, vec, vec_to_part);

				if(temp == 0.0f)
					; /* do nothing */
				else if(temp > priority) {
					priority = temp;
					priority_ob = eob;
					len = VecLength(vec_to_part);
				}
				/* choose closest object with same priority */
				else if(temp == priority) {
					float len2 = VecLength(vec_to_part);

					if(len2 < len) {
						priority_ob = eob;
						len = len2;
					}
				}
			}
		}
	}

	/* then use that effector */
	if(priority > (rule->type==eBoidRuleType_Avoid ? gabr->fear_factor : 0.0f)) { /* with avoid, factor is "fear factor" */
		Object *eob = priority_ob;
		PartDeflect *pd = eob->pd;
		float vec_to_part[3];
		float surface = 0.0f;
		float nor[3];

		if(gabr->options & BRULE_GOAL_AVOID_PREDICT) {
			/* estimate future location of target */
			surface = (float)effector_find_co(bbd->scene, pa->prev_state.co, NULL, eob, pd, loc, nor, vec, NULL); 

			VecSubf(vec_to_part, pa->prev_state.co, loc);
			len = Normalize(vec_to_part);

			VecMulf(vec, len / (val->max_speed * bbd->timestep));
			VecAddf(loc, loc, vec);
			VecSubf(vec_to_part, pa->prev_state.co, loc);
		}
		else {
			surface = (float)effector_find_co(bbd->scene, pa->prev_state.co, NULL, eob, pd, loc, nor, NULL, NULL);

			VecSubf(vec_to_part, pa->prev_state.co, loc);
			len = VecLength(vec_to_part);
		}

		if(rule->type == eBoidRuleType_Goal && boids->options & BOID_ALLOW_CLIMB && surface!=0.0f) {
			if(!bbd->goal_ob || bbd->goal_priority < priority) {
				bbd->goal_ob = eob;
				VECCOPY(bbd->goal_co, loc);
				VECCOPY(bbd->goal_nor, nor);
			}
		}
		else if(rule->type == eBoidRuleType_Avoid && pa->boid->mode == eBoidMode_Climbing &&
			priority > 2.0f * gabr->fear_factor) {
			/* detach from surface and try to fly away from danger */
			VECCOPY(vec_to_part, pa->r_ve);
			VecMulf(vec_to_part, -1.0f);
		}

		VECCOPY(bbd->wanted_co, vec_to_part);
		VecMulf(bbd->wanted_co, mul);

		bbd->wanted_speed = val->max_speed * priority;

		/* with goals factor is approach velocity factor */
		if(rule->type == eBoidRuleType_Goal && boids->landing_smoothness > 0.0f) {
			float len2 = 2.0f*VecLength(pa->prev_state.vel);

			surface *= pa->size * boids->height;

			if(len2 > 0.0f && len - surface < len2) {
				len2 = (len - surface)/len2;
				bbd->wanted_speed *= pow(len2, boids->landing_smoothness);
			}
		}

		ret = 1;
	}

	return ret;
}

static int rule_avoid_collision(BoidRule *rule, BoidBrainData *bbd, BoidValues *val, ParticleData *pa)
{
	BoidRuleAvoidCollision *acbr = (BoidRuleAvoidCollision*) rule;
	KDTreeNearest *ptn = NULL;
	ParticleEffectorCache *ec;
	ParticleTarget *pt;
	float vec[3] = {0.0f, 0.0f, 0.0f}, loc[3] = {0.0f, 0.0f, 0.0f};
	float co1[3], vel1[3], co2[3], vel2[3];
	float  len, t, inp, t_min = 2.0f;
	int n, neighbors = 0, nearest = 0;
	int ret = 0;

	//check deflector objects first
	if(acbr->options & BRULE_ACOLL_WITH_DEFLECTORS) {
		ParticleCollision col;
		BVHTreeRayHit hit;
		float radius = val->personal_space * pa->size, ray_dir[3];

		VECCOPY(col.co1, pa->prev_state.co);
		VecAddf(col.co2, pa->prev_state.co, pa->prev_state.vel);
		VecSubf(ray_dir, col.co2, col.co1);
		VecMulf(ray_dir, acbr->look_ahead);
		col.t = 0.0f;
		hit.index = -1;
		hit.dist = col.ray_len = VecLength(ray_dir);

		/* find out closest deflector object */
		for(ec=bbd->psys->effectors.first; ec; ec=ec->next) {
			if(ec->type & PSYS_EC_DEFLECT) {
				Object *eob = ec->ob;

				/* don't check with current ground object */
				if(eob == pa->stick_ob)
					continue;

				col.md = ( CollisionModifierData * ) ( modifiers_findByType ( eob, eModifierType_Collision ) );
				col.ob_t = eob;

				if(col.md && col.md->bvhtree)
					BLI_bvhtree_ray_cast(col.md->bvhtree, col.co1, ray_dir, radius, &hit, particle_intersect_face, &col);
			}
		}
		/* then avoid that object */
		if(hit.index>=0) {
			/* TODO: not totally happy with this part */
			t = hit.dist/col.ray_len;

			VECCOPY(bbd->wanted_co, col.nor);

			VecMulf(bbd->wanted_co, (1.0f - t) * val->personal_space * pa->size);

			bbd->wanted_speed = sqrt(t) * VecLength(pa->prev_state.vel);

			return 1;
		}
	}

	//check boids in own system
	if(acbr->options & BRULE_ACOLL_WITH_BOIDS)
	{
		neighbors = BLI_kdtree_range_search(bbd->psys->tree, acbr->look_ahead * VecLength(pa->prev_state.vel), pa->prev_state.co, pa->prev_state.ave, &ptn);
		if(neighbors > 1) for(n=1; n<neighbors; n++) {
			VECCOPY(co1, pa->prev_state.co);
			VECCOPY(vel1, pa->prev_state.vel);
			VECCOPY(co2, (bbd->psys->particles + ptn[n].index)->prev_state.co);
			VECCOPY(vel2, (bbd->psys->particles + ptn[n].index)->prev_state.vel);

			VecSubf(loc, co1, co2);

			VecSubf(vec, vel1, vel2);
			
			inp = Inpf(vec,vec);

			/* velocities not parallel */
			if(inp != 0.0f) {
				t = -Inpf(loc, vec)/inp;
				/* cpa is not too far in the future so investigate further */
				if(t > 0.0f && t < t_min) {
					VECADDFAC(co1, co1, vel1, t);
					VECADDFAC(co2, co2, vel2, t);
					
					VecSubf(vec, co2, co1);

					len = Normalize(vec);

					/* distance of cpa is close enough */
					if(len < 2.0f * val->personal_space * pa->size) {
						t_min = t;

						VecMulf(vec, VecLength(vel1));
						VecMulf(vec, (2.0f - t)/2.0f);
						VecSubf(bbd->wanted_co, vel1, vec);
						bbd->wanted_speed = VecLength(bbd->wanted_co);
						ret = 1;
					}
				}
			}
		}
	}
	if(ptn){ MEM_freeN(ptn); ptn=NULL; }

	/* check boids in other systems */
	for(pt=bbd->psys->targets.first; pt; pt=pt->next) {
		ParticleSystem *epsys = psys_get_target_system(bbd->ob, pt);

		if(epsys) {
			neighbors = BLI_kdtree_range_search(epsys->tree, acbr->look_ahead * VecLength(pa->prev_state.vel), pa->prev_state.co, pa->prev_state.ave, &ptn);
			if(neighbors > 0) for(n=0; n<neighbors; n++) {
				VECCOPY(co1, pa->prev_state.co);
				VECCOPY(vel1, pa->prev_state.vel);
				VECCOPY(co2, (epsys->particles + ptn[n].index)->prev_state.co);
				VECCOPY(vel2, (epsys->particles + ptn[n].index)->prev_state.vel);

				VecSubf(loc, co1, co2);

				VecSubf(vec, vel1, vel2);
				
				inp = Inpf(vec,vec);

				/* velocities not parallel */
				if(inp != 0.0f) {
					t = -Inpf(loc, vec)/inp;
					/* cpa is not too far in the future so investigate further */
					if(t > 0.0f && t < t_min) {
						VECADDFAC(co1, co1, vel1, t);
						VECADDFAC(co2, co2, vel2, t);
						
						VecSubf(vec, co2, co1);

						len = Normalize(vec);

						/* distance of cpa is close enough */
						if(len < 2.0f * val->personal_space * pa->size) {
							t_min = t;

							VecMulf(vec, VecLength(vel1));
							VecMulf(vec, (2.0f - t)/2.0f);
							VecSubf(bbd->wanted_co, vel1, vec);
							bbd->wanted_speed = VecLength(bbd->wanted_co);
							ret = 1;
						}
					}
				}
			}

			if(ptn){ MEM_freeN(ptn); ptn=NULL; }
		}
	}


	if(ptn && nearest==0)
		MEM_freeN(ptn);

	return ret;
}
static int rule_separate(BoidRule *rule, BoidBrainData *bbd, BoidValues *val, ParticleData *pa)
{
	KDTreeNearest *ptn = NULL;
	ParticleTarget *pt;
	float len = 2.0f * val->personal_space * pa->size + 1.0f;
	float vec[3] = {0.0f, 0.0f, 0.0f};
	int neighbors = BLI_kdtree_range_search(bbd->psys->tree, 2.0f * val->personal_space * pa->size, pa->prev_state.co, NULL, &ptn);
	int ret = 0;

	if(neighbors > 1 && ptn[1].dist!=0.0f) {
		VecSubf(vec, pa->prev_state.co, bbd->psys->particles[ptn[1].index].state.co);
		VecMulf(vec, (2.0f * val->personal_space * pa->size - ptn[1].dist) / ptn[1].dist);
		VecAddf(bbd->wanted_co, bbd->wanted_co, vec);
		bbd->wanted_speed = val->max_speed;
		len = ptn[1].dist;
		ret = 1;
	}
	if(ptn){ MEM_freeN(ptn); ptn=NULL; }

	/* check other boid systems */
	for(pt=bbd->psys->targets.first; pt; pt=pt->next) {
		ParticleSystem *epsys = psys_get_target_system(bbd->ob, pt);

		if(epsys) {
			neighbors = BLI_kdtree_range_search(epsys->tree, 2.0f * val->personal_space * pa->size, pa->prev_state.co, NULL, &ptn);
			
			if(neighbors > 0 && ptn[0].dist < len) {
				VecSubf(vec, pa->prev_state.co, ptn[0].co);
				VecMulf(vec, (2.0f * val->personal_space * pa->size - ptn[0].dist) / ptn[1].dist);
				VecAddf(bbd->wanted_co, bbd->wanted_co, vec);
				bbd->wanted_speed = val->max_speed;
				len = ptn[0].dist;
				ret = 1;
			}

			if(ptn){ MEM_freeN(ptn); ptn=NULL; }
		}
	}
	return ret;
}
static int rule_flock(BoidRule *rule, BoidBrainData *bbd, BoidValues *val, ParticleData *pa)
{
	KDTreeNearest ptn[11];
	float vec[3] = {0.0f, 0.0f, 0.0f}, loc[3] = {0.0f, 0.0f, 0.0f};
	int neighbors = BLI_kdtree_find_n_nearest(bbd->psys->tree, 11, pa->state.co, pa->prev_state.ave, ptn);
	int n;
	int ret = 0;

	if(neighbors > 1) {
		for(n=1; n<neighbors; n++) {
			VecAddf(loc, loc, bbd->psys->particles[ptn[n].index].prev_state.co);
			VecAddf(vec, vec, bbd->psys->particles[ptn[n].index].prev_state.vel);
		}

		VecMulf(loc, 1.0f/((float)neighbors - 1.0f));
		VecMulf(vec, 1.0f/((float)neighbors - 1.0f));

		VecSubf(loc, loc, pa->prev_state.co);
		VecSubf(vec, vec, pa->prev_state.vel);

		VecAddf(bbd->wanted_co, bbd->wanted_co, vec);
		VecAddf(bbd->wanted_co, bbd->wanted_co, loc);
		bbd->wanted_speed = VecLength(bbd->wanted_co);

		ret = 1;
	}
	return ret;
}
static int rule_follow_leader(BoidRule *rule, BoidBrainData *bbd, BoidValues *val, ParticleData *pa)
{
	BoidRuleFollowLeader *flbr = (BoidRuleFollowLeader*) rule;
	float vec[3] = {0.0f, 0.0f, 0.0f}, loc[3] = {0.0f, 0.0f, 0.0f};
	float mul, len;
	int n = (flbr->queue_size <= 1) ? bbd->psys->totpart : flbr->queue_size;
	int i, ret = 0, p = pa - bbd->psys->particles;

	if(flbr->ob) {
		float vec2[3], t;

		/* first check we're not blocking the leader*/
		VecSubf(vec, flbr->loc, flbr->oloc);
		VecMulf(vec, 1.0f/bbd->timestep);

		VecSubf(loc, pa->prev_state.co, flbr->oloc);

		mul = Inpf(vec, vec);

		/* leader is not moving */
		if(mul < 0.01) {
			len = VecLength(loc);
			/* too close to leader */
			if(len < 2.0f * val->personal_space * pa->size) {
				VECCOPY(bbd->wanted_co, loc);
				bbd->wanted_speed = val->max_speed;
				return 1;
			}
		}
		else {
			t = Inpf(loc, vec)/mul;

			/* possible blocking of leader in near future */
			if(t > 0.0f && t < 3.0f) {
				VECCOPY(vec2, vec);
				VecMulf(vec2, t);

				VecSubf(vec2, loc, vec2);

				len = VecLength(vec2);

				if(len < 2.0f * val->personal_space * pa->size) {
					VECCOPY(bbd->wanted_co, vec2);
					bbd->wanted_speed = val->max_speed * (3.0f - t)/3.0f;
					return 1;
				}
			}
		}

		/* not blocking so try to follow leader */
		if(p && flbr->options & BRULE_LEADER_IN_LINE) {
			VECCOPY(vec, bbd->psys->particles[p-1].prev_state.vel);
			VECCOPY(loc, bbd->psys->particles[p-1].prev_state.co);
		}
		else {
			VECCOPY(loc, flbr->oloc);
			VecSubf(vec, flbr->loc, flbr->oloc);
			VecMulf(vec, 1.0/bbd->timestep);
		}
		
		/* fac is seconds behind leader */
		VECADDFAC(loc, loc, vec, -flbr->distance);

		VecSubf(bbd->wanted_co, loc, pa->prev_state.co);
		bbd->wanted_speed = VecLength(bbd->wanted_co);
			
		ret = 1;
	}
	else if(p % n) {
		float vec2[3], t, t_min = 3.0f;

		/* first check we're not blocking any leaders */
		for(i = 0; i< bbd->psys->totpart; i+=n){
			VECCOPY(vec, bbd->psys->particles[i].prev_state.vel);

			VecSubf(loc, pa->prev_state.co, bbd->psys->particles[i].prev_state.co);

			mul = Inpf(vec, vec);

			/* leader is not moving */
			if(mul < 0.01) {
				len = VecLength(loc);
				/* too close to leader */
				if(len < 2.0f * val->personal_space * pa->size) {
					VECCOPY(bbd->wanted_co, loc);
					bbd->wanted_speed = val->max_speed;
					return 1;
				}
			}
			else {
				t = Inpf(loc, vec)/mul;

				/* possible blocking of leader in near future */
				if(t > 0.0f && t < t_min) {
					VECCOPY(vec2, vec);
					VecMulf(vec2, t);

					VecSubf(vec2, loc, vec2);

					len = VecLength(vec2);

					if(len < 2.0f * val->personal_space * pa->size) {
						t_min = t;
						VECCOPY(bbd->wanted_co, loc);
						bbd->wanted_speed = val->max_speed * (3.0f - t)/3.0f;
						ret = 1;
					}
				}
			}
		}

		if(ret) return 1;

		/* not blocking so try to follow leader */
		if(flbr->options & BRULE_LEADER_IN_LINE) {
			VECCOPY(vec, bbd->psys->particles[p-1].prev_state.vel);
			VECCOPY(loc, bbd->psys->particles[p-1].prev_state.co);
		}
		else {
			VECCOPY(vec, bbd->psys->particles[p - p%n].prev_state.vel);
			VECCOPY(loc, bbd->psys->particles[p - p%n].prev_state.co);
		}
		
		/* fac is seconds behind leader */
		VECADDFAC(loc, loc, vec, -flbr->distance);

		VecSubf(bbd->wanted_co, loc, pa->prev_state.co);
		bbd->wanted_speed = VecLength(bbd->wanted_co);
		
		ret = 1;
	}

	return ret;
}
static int rule_average_speed(BoidRule *rule, BoidBrainData *bbd, BoidValues *val, ParticleData *pa)
{
	BoidRuleAverageSpeed *asbr = (BoidRuleAverageSpeed*)rule;
	float vec[3] = {0.0f, 0.0f, 0.0f};

	if(asbr->wander > 0.0f) {
		/* abuse pa->r_ave for wandering */
		pa->r_ave[0] += asbr->wander * (-1.0f + 2.0f * BLI_frand());
		pa->r_ave[1] += asbr->wander * (-1.0f + 2.0f * BLI_frand());
		pa->r_ave[2] += asbr->wander * (-1.0f + 2.0f * BLI_frand());

		Normalize(pa->r_ave);

		VECCOPY(vec, pa->r_ave);

		QuatMulVecf(pa->prev_state.rot, vec);

		VECCOPY(bbd->wanted_co, pa->prev_state.ave);

		VecMulf(bbd->wanted_co, 1.1f);

		VecAddf(bbd->wanted_co, bbd->wanted_co, vec);

		/* leveling */
		if(asbr->level > 0.0f) {
			Projf(vec, bbd->wanted_co, bbd->psys->part->acc);
			VecMulf(vec, asbr->level);
			VecSubf(bbd->wanted_co, bbd->wanted_co, vec);
		}
	}
	else {
		VECCOPY(bbd->wanted_co, pa->prev_state.ave);

		/* may happen at birth */
		if(Inp2f(bbd->wanted_co,bbd->wanted_co)==0.0f) {
			bbd->wanted_co[0] = 2.0f*(0.5f - BLI_frand());
			bbd->wanted_co[1] = 2.0f*(0.5f - BLI_frand());
			bbd->wanted_co[2] = 2.0f*(0.5f - BLI_frand());
		}
		
		/* leveling */
		if(asbr->level > 0.0f) {
			Projf(vec, bbd->wanted_co, bbd->psys->part->acc);
			VecMulf(vec, asbr->level);
			VecSubf(bbd->wanted_co, bbd->wanted_co, vec);
		}

	}
	bbd->wanted_speed = asbr->speed * val->max_speed;
	
	return 1;
}
static int rule_fight(BoidRule *rule, BoidBrainData *bbd, BoidValues *val, ParticleData *pa)
{
	BoidRuleFight *fbr = (BoidRuleFight*)rule;
	KDTreeNearest *ptn = NULL;
	ParticleTarget *pt;
	ParticleData *epars;
	ParticleData *enemy_pa = NULL;
	/* friends & enemies */
	float closest_enemy[3] = {0.0f,0.0f,0.0f};
	float closest_dist = fbr->distance + 1.0f;
	float f_strength = 0.0f, e_strength = 0.0f;
	float health = 0.0f;
	int n, ret = 0;

	/* calculate own group strength */
	int neighbors = BLI_kdtree_range_search(bbd->psys->tree, fbr->distance, pa->prev_state.co, NULL, &ptn);
	for(n=0; n<neighbors; n++)
		health += bbd->psys->particles[ptn[n].index].boid->health;

	f_strength += bbd->part->boids->strength * health;

	if(ptn){ MEM_freeN(ptn); ptn=NULL; }

	/* add other friendlies and calculate enemy strength and find closest enemy */
	for(pt=bbd->psys->targets.first; pt; pt=pt->next) {
		ParticleSystem *epsys = psys_get_target_system(bbd->ob, pt);
		if(epsys) {
			epars = epsys->particles;

			neighbors = BLI_kdtree_range_search(epsys->tree, fbr->distance, pa->prev_state.co, NULL, &ptn);
			
			health = 0.0f;

			for(n=0; n<neighbors; n++) {
				health += epars[ptn[n].index].boid->health;

				if(n==0 && pt->mode==PTARGET_MODE_ENEMY && ptn[n].dist < closest_dist) {
					VECCOPY(closest_enemy, ptn[n].co);
					closest_dist = ptn[n].dist;
					enemy_pa = epars + ptn[n].index;
				}
			}
			if(pt->mode==PTARGET_MODE_ENEMY)
				e_strength += epsys->part->boids->strength * health;
			else if(pt->mode==PTARGET_MODE_FRIEND)
				f_strength += epsys->part->boids->strength * health;

			if(ptn){ MEM_freeN(ptn); ptn=NULL; }
		}
	}
	/* decide action if enemy presence found */
	if(e_strength > 0.0f) {
		VecSubf(bbd->wanted_co, closest_enemy, pa->prev_state.co);

		/* attack if in range */
		if(closest_dist <= bbd->part->boids->range + pa->size + enemy_pa->size) {
			float damage = BLI_frand();
			float enemy_dir[3] = {bbd->wanted_co[0],bbd->wanted_co[1],bbd->wanted_co[2]};

			Normalize(enemy_dir);

			/* fight mode */
			bbd->wanted_speed = 0.0f;

			/* must face enemy to fight */
			if(Inpf(pa->prev_state.ave, enemy_dir)>0.5f) {
				enemy_pa->boid->health -= bbd->part->boids->strength * bbd->timestep * ((1.0f-bbd->part->boids->accuracy)*damage + bbd->part->boids->accuracy);
			}
		}
		else {
			/* approach mode */
			bbd->wanted_speed = val->max_speed;
		}

		/* check if boid doesn't want to fight */
		if(pa->boid->health/bbd->part->boids->health * bbd->part->boids->aggression < e_strength / f_strength) {
			/* decide to flee */
			if(closest_dist < fbr->flee_distance * fbr->distance) {
				VecMulf(bbd->wanted_co, -1.0f);
				bbd->wanted_speed = val->max_speed;
			}
			else { /* wait for better odds */
				bbd->wanted_speed = 0.0f;
			}
		}

		ret = 1;
	}

	return ret;
}

typedef int (*boid_rule_cb)(BoidRule *rule, BoidBrainData *data, BoidValues *val, ParticleData *pa);

static boid_rule_cb boid_rules[] = {
	rule_none,
	rule_goal_avoid,
	rule_goal_avoid,
	rule_avoid_collision,
	rule_separate,
	rule_flock,
	rule_follow_leader,
	rule_average_speed,
	rule_fight,
	//rule_help,
	//rule_protect,
	//rule_hide,
	//rule_follow_path,
	//rule_follow_wall
};

static void set_boid_values(BoidValues *val, BoidSettings *boids, ParticleData *pa)
{
	if(ELEM(pa->boid->mode, eBoidMode_OnLand, eBoidMode_Climbing)) {
		val->max_speed = boids->land_max_speed * pa->boid->health/boids->health;
		val->max_acc = boids->land_max_acc * val->max_speed;
		val->max_ave = boids->land_max_ave * M_PI * pa->boid->health/boids->health;
		val->min_speed = 0.0f; /* no minimum speed on land */
		val->personal_space = boids->land_personal_space;
		val->jump_speed = boids->land_jump_speed * pa->boid->health/boids->health;
	}
	else {
		val->max_speed = boids->air_max_speed * pa->boid->health/boids->health;
		val->max_acc = boids->air_max_acc * val->max_speed;
		val->max_ave = boids->air_max_ave * M_PI * pa->boid->health/boids->health;
		val->min_speed = boids->air_min_speed * boids->air_max_speed;
		val->personal_space = boids->air_personal_space;
		val->jump_speed = 0.0f; /* no jumping in air */
	}
}
static Object *boid_find_ground(BoidBrainData *bbd, ParticleData *pa, float *ground_co, float *ground_nor)
{
	if(pa->boid->mode == eBoidMode_Climbing) {
		SurfaceModifierData *surmd = NULL;
		float x[3], v[3];

		surmd = (SurfaceModifierData *)modifiers_findByType ( pa->stick_ob, eModifierType_Surface );

		/* take surface velocity into account */
		effector_find_co(bbd->scene, pa->state.co, surmd, NULL, NULL, x, NULL, v, NULL);
		VecAddf(x, x, v);

		/* get actual position on surface */
		effector_find_co(bbd->scene, x, surmd, NULL, NULL, ground_co, ground_nor, NULL, NULL);

		return pa->stick_ob;
	}
	else {
		float zvec[3] = {0.0f, 0.0f, 2000.0f};
		ParticleCollision col;
		BVHTreeRayHit hit;
		ParticleEffectorCache *ec;
		float radius = 0.0f, t, ray_dir[3];

		VECCOPY(col.co1, pa->state.co);
		VECCOPY(col.co2, pa->state.co);
		VecAddf(col.co1, col.co1, zvec);
		VecSubf(col.co2, col.co2, zvec);
		VecSubf(ray_dir, col.co2, col.co1);
		col.t = 0.0f;
		hit.index = -1;
		hit.dist = col.ray_len = VecLength(ray_dir);

		/* find out upmost deflector object */
		for(ec=bbd->psys->effectors.first; ec; ec=ec->next) {
			if(ec->type & PSYS_EC_DEFLECT) {
				Object *eob = ec->ob;

				col.md = ( CollisionModifierData * ) ( modifiers_findByType ( eob, eModifierType_Collision ) );
				col.ob_t = eob;

				if(col.md && col.md->bvhtree)
					BLI_bvhtree_ray_cast(col.md->bvhtree, col.co1, ray_dir, radius, &hit, particle_intersect_face, &col);
			}
		}
		/* then use that object */
		if(hit.index>=0) {
			t = hit.dist/col.ray_len;
			VecLerpf(ground_co, col.co1, col.co2, t);
			VECCOPY(ground_nor, col.nor);
			Normalize(ground_nor);
			return col.ob;
		}
		else {
			/* default to z=0 */
			VECCOPY(ground_co, pa->state.co);
			ground_co[2] = 0;
			ground_nor[0] = ground_nor[1] = 0.0f;
			ground_nor[2] = 1.0f;
			return NULL;
		}
	}
}
static int boid_rule_applies(ParticleData *pa, BoidSettings *boids, BoidRule *rule)
{
	if(rule==NULL)
		return 0;
	
	if(ELEM(pa->boid->mode, eBoidMode_OnLand, eBoidMode_Climbing) && rule->flag & BOIDRULE_ON_LAND)
		return 1;
	
	if(pa->boid->mode==eBoidMode_InAir && rule->flag & BOIDRULE_IN_AIR)
		return 1;

	return 0;
}
void boids_precalc_rules(ParticleSettings *part, float cfra)
{
	BoidState *state = part->boids->states.first;
	BoidRule *rule;
	for(; state; state=state->next) {
		for(rule = state->rules.first; rule; rule=rule->next) {
			if(rule->type==eBoidRuleType_FollowLeader) {
				BoidRuleFollowLeader *flbr = (BoidRuleFollowLeader*) rule;

				if(flbr->ob && flbr->cfra != cfra) {
					/* save object locations for velocity calculations */
					VECCOPY(flbr->oloc, flbr->loc);
					VECCOPY(flbr->loc, flbr->ob->obmat[3]);
					flbr->cfra = cfra;
				}
			}
		}
	}
}
static void boid_climb(BoidSettings *boids, ParticleData *pa, float *surface_co, float *surface_nor)
{
	float nor[3], vel[3];
	VECCOPY(nor, surface_nor);

	/* gather apparent gravity to r_ve */
	VECADDFAC(pa->r_ve, pa->r_ve, surface_nor, -1.0);
	Normalize(pa->r_ve);

	/* raise boid it's size from surface */
	VecMulf(nor, pa->size * boids->height);
	VecAddf(pa->state.co, surface_co, nor);

	/* remove normal component from velocity */
	Projf(vel, pa->state.vel, surface_nor);
	VecSubf(pa->state.vel, pa->state.vel, vel);
}
static float boid_goal_signed_dist(float *boid_co, float *goal_co, float *goal_nor)
{
	float vec[3];

	VecSubf(vec, boid_co, goal_co);

	return Inpf(vec, goal_nor);
}
/* wanted_co is relative to boid location */
static int apply_boid_rule(BoidBrainData *bbd, BoidRule *rule, BoidValues *val, ParticleData *pa, float fuzziness)
{
	if(rule==NULL)
		return 0;

	if(boid_rule_applies(pa, bbd->part->boids, rule)==0)
		return 0;

	if(boid_rules[rule->type](rule, bbd, val, pa)==0)
		return 0;

	if(fuzziness < 0.0f || VecLenCompare(bbd->wanted_co, pa->prev_state.vel, fuzziness * VecLength(pa->prev_state.vel))==0)
		return 1;
	else
		return 0;
}
static BoidState *get_boid_state(BoidSettings *boids, ParticleData *pa) {
	BoidState *state = boids->states.first;

	for(; state; state=state->next) {
		if(state->id==pa->boid->state_id)
			return state;
	}

	/* for some reason particle isn't at a valid state */
	state = boids->states.first;
	if(state)
		pa->boid->state_id = state->id;

	return state;
}
//static int boid_condition_is_true(BoidCondition *cond) {
//	/* TODO */
//	return 0;
//}

/* determines the velocity the boid wants to have */
void boid_brain(BoidBrainData *bbd, int p, ParticleData *pa)
{
	BoidRule *rule;
	BoidSettings *boids = bbd->part->boids;
	BoidValues val;
	BoidState *state = get_boid_state(boids, pa);
	//BoidCondition *cond;

	if(pa->boid->health <= 0.0f) {
		pa->alive = PARS_DYING;
		return;
	}

	//planned for near future
	//cond = state->conditions.first;
	//for(; cond; cond=cond->next) {
	//	if(boid_condition_is_true(cond)) {
	//		pa->boid->state_id = cond->state_id;
	//		state = get_boid_state(boids, pa);
	//		break; /* only first true condition is used */
	//	}
	//}

	bbd->wanted_co[0]=bbd->wanted_co[1]=bbd->wanted_co[2]=bbd->wanted_speed=0.0f;

	/* create random seed for every particle & frame */
	BLI_srandom(bbd->psys->seed + p + (int)bbd->cfra + (int)(1000*pa->r_rot[0]));

	set_boid_values(&val, bbd->part->boids, pa);

	/* go through rules */
	switch(state->ruleset_type) {
		case eBoidRulesetType_Fuzzy:
		{
			for(rule = state->rules.first; rule; rule = rule->next) {
				if(apply_boid_rule(bbd, rule, &val, pa, state->rule_fuzziness))
					break; /* only first nonzero rule that comes through fuzzy rule is applied */
			}
			break;
		}
		case eBoidRulesetType_Random:
		{
			/* use random rule for each particle (allways same for same particle though) */
			rule = BLI_findlink(&state->rules, (int)(1000.0f * pa->r_rot[1]) % BLI_countlist(&state->rules));

			apply_boid_rule(bbd, rule, &val, pa, -1.0);
		}
		case eBoidRulesetType_Average:
		{
			float wanted_co[3] = {0.0f, 0.0f, 0.0f}, wanted_speed = 0.0f;
			int n = 0;
			for(rule = state->rules.first; rule; rule=rule->next) {
				if(apply_boid_rule(bbd, rule, &val, pa, -1.0f)) {
					VecAddf(wanted_co, wanted_co, bbd->wanted_co);
					wanted_speed += bbd->wanted_speed;
					n++;
					bbd->wanted_co[0]=bbd->wanted_co[1]=bbd->wanted_co[2]=bbd->wanted_speed=0.0f;
				}
			}

			if(n > 1) {
				VecMulf(wanted_co, 1.0f/(float)n);
				wanted_speed /= (float)n;
			}

			VECCOPY(bbd->wanted_co, wanted_co);
			bbd->wanted_speed = wanted_speed;
			break;
		}

	}

	/* decide on jumping & liftoff */
	if(pa->boid->mode == eBoidMode_OnLand) {
		/* fuzziness makes boids capable of misjudgement */
		float mul = 1.0 + state->rule_fuzziness;
		
		if(boids->options & BOID_ALLOW_FLIGHT && bbd->wanted_co[2] > 0.0f) {
			float cvel[3], dir[3];

			VECCOPY(dir, pa->prev_state.ave);
			Normalize2(dir);

			VECCOPY(cvel, bbd->wanted_co);
			Normalize2(cvel);

			if(Inp2f(cvel, dir) > 0.95 / mul)
				pa->boid->mode = eBoidMode_Liftoff;
		}
		else if(val.jump_speed > 0.0f) {
			float jump_v[3];
			int jump = 0;

			/* jump to get to a location */
			if(bbd->wanted_co[2] > 0.0f) {
				float cvel[3], dir[3];
				float z_v, ground_v, cur_v;
				float len;

				VECCOPY(dir, pa->prev_state.ave);
				Normalize2(dir);

				VECCOPY(cvel, bbd->wanted_co);
				Normalize2(cvel);

				len = Vec2Length(pa->prev_state.vel);

				/* first of all, are we going in a suitable direction? */
				/* or at a suitably slow speed */
				if(Inp2f(cvel, dir) > 0.95f / mul || len <= state->rule_fuzziness) {
					/* try to reach goal at highest point of the parabolic path */
					cur_v = Vec2Length(pa->prev_state.vel);
					z_v = sasqrt(-2.0f * bbd->part->acc[2] * bbd->wanted_co[2]);
					ground_v = Vec2Length(bbd->wanted_co)*sasqrt(-0.5f * bbd->part->acc[2] / bbd->wanted_co[2]);

					len = sasqrt((ground_v-cur_v)*(ground_v-cur_v) + z_v*z_v);

					if(len < val.jump_speed * mul || bbd->part->boids->options & BOID_ALLOW_FLIGHT) {
						jump = 1;

						len = MIN2(len, val.jump_speed);

						VECCOPY(jump_v, dir);
						jump_v[2] = z_v;
						VecMulf(jump_v, ground_v);

						Normalize(jump_v);
						VecMulf(jump_v, len);
						Vec2Addf(jump_v, jump_v, pa->prev_state.vel);
					}
				}
			}

			/* jump to go faster */
			if(jump == 0 && val.jump_speed > val.max_speed && bbd->wanted_speed > val.max_speed) {
				
			}

			if(jump) {
				VECCOPY(pa->prev_state.vel, jump_v);
				pa->boid->mode = eBoidMode_Falling;
			}
		}
	}
}
/* tries to realize the wanted velocity taking all constraints into account */
void boid_body(BoidBrainData *bbd, ParticleData *pa)
{
	BoidSettings *boids = bbd->part->boids;
	BoidValues val;
	float acc[3] = {0.0f, 0.0f, 0.0f}, tan_acc[3], nor_acc[3];
	float dvec[3], bvec[3];
	float new_dir[3], new_speed;
	float old_dir[3], old_speed;
	float wanted_dir[3];
	float q[4], mat[3][3]; /* rotation */
	float ground_co[3] = {0.0f, 0.0f, 0.0f}, ground_nor[3] = {0.0f, 0.0f, 1.0f};
	float force[3] = {0.0f, 0.0f, 0.0f}, tvel[3] = {0.0f, 0.0f, 1.0f};
	float pa_mass=bbd->part->mass, dtime=bbd->dfra*bbd->timestep;
	int p = pa - bbd->psys->particles;

	set_boid_values(&val, boids, pa);

	/* make sure there's something in new velocity, location & rotation */
	copy_particle_key(&pa->state,&pa->prev_state,0);

	if(bbd->part->flag & PART_SIZEMASS)
		pa_mass*=pa->size;

	/* if boids can't fly they fall to the ground */
	if((boids->options & BOID_ALLOW_FLIGHT)==0 && ELEM(pa->boid->mode, eBoidMode_OnLand, eBoidMode_Climbing)==0 && bbd->part->acc[2] != 0.0f)
		pa->boid->mode = eBoidMode_Falling;

	if(pa->boid->mode == eBoidMode_Falling) {
		/* Falling boids are only effected by gravity. */
		acc[2] = bbd->part->acc[2];
	}
	else {
		/* figure out acceleration */
		float landing_level = 2.0f;
		float level = landing_level + 1.0f;
		float new_vel[3];

		if(pa->boid->mode == eBoidMode_Liftoff) {
			pa->boid->mode = eBoidMode_InAir;
			pa->stick_ob = boid_find_ground(bbd, pa, ground_co, ground_nor);
		}
		else if(pa->boid->mode == eBoidMode_InAir && boids->options & BOID_ALLOW_LAND) {
			/* auto-leveling & landing if close to ground */

			pa->stick_ob = boid_find_ground(bbd, pa, ground_co, ground_nor);
			
			/* level = how many particle sizes above ground */
			level = (pa->prev_state.co[2] - ground_co[2])/(2.0f * pa->size) - 0.5;

			landing_level = - boids->landing_smoothness * pa->prev_state.vel[2] * pa_mass;

			if(pa->prev_state.vel[2] < 0.0f) {
				if(level < 1.0f) {
					bbd->wanted_co[0] = bbd->wanted_co[1] = bbd->wanted_co[2] = 0.0f;
					bbd->wanted_speed = 0.0f;
					pa->boid->mode = eBoidMode_Falling;
				}
				else if(level < landing_level) {
					bbd->wanted_speed *= (level - 1.0f)/landing_level;
					bbd->wanted_co[2] *= (level - 1.0f)/landing_level;
				}
			}
		}

		VECCOPY(old_dir, pa->prev_state.ave);
		VECCOPY(wanted_dir, bbd->wanted_co);
		new_speed = Normalize(wanted_dir);

		/* first check if we have valid direction we want to go towards */
		if(new_speed == 0.0f) {
			VECCOPY(new_dir, old_dir);
		}
		else {
			float old_dir2[2], wanted_dir2[2], nor[3], angle;
			Vec2Copyf(old_dir2, old_dir);
			Normalize2(old_dir2);
			Vec2Copyf(wanted_dir2, wanted_dir);
			Normalize2(wanted_dir2);

			/* choose random direction to turn if wanted velocity */
			/* is directly behind regardless of z-coordinate */
			if(Inp2f(old_dir2, wanted_dir2) < -0.99f) {
				wanted_dir[0] = 2.0f*(0.5f - BLI_frand());
				wanted_dir[1] = 2.0f*(0.5f - BLI_frand());
				wanted_dir[2] = 2.0f*(0.5f - BLI_frand());
				Normalize(wanted_dir);
			}

			/* constrain direction with maximum angular velocity */
			angle = saacos(Inpf(old_dir, wanted_dir));
			angle = MIN2(angle, val.max_ave);

			Crossf(nor, old_dir, wanted_dir);
			VecRotToQuat(nor, angle, q);
			VECCOPY(new_dir, old_dir);
			QuatMulVecf(q, new_dir);
			Normalize(new_dir);

			/* save direction in case resulting velocity too small */
			VecRotToQuat(nor, angle*dtime, q);
			VECCOPY(pa->state.ave, old_dir);
			QuatMulVecf(q, pa->state.ave);
			Normalize(pa->state.ave);
		}

		/* constrain speed with maximum acceleration */
		old_speed = VecLength(pa->prev_state.vel);
		
		if(bbd->wanted_speed < old_speed)
			new_speed = MAX2(bbd->wanted_speed, old_speed - val.max_acc);
		else
			new_speed = MIN2(bbd->wanted_speed, old_speed + val.max_acc);

		/* combine direction and speed */
		VECCOPY(new_vel, new_dir);
		VecMulf(new_vel, new_speed);

		/* maintain minimum flying velocity if not landing */
		if(level >= landing_level) {
			float len2 = Inp2f(new_vel,new_vel);
			float root;

			len2 = MAX2(len2, val.min_speed*val.min_speed);
			root = sasqrt(new_speed*new_speed - len2);

			new_vel[2] = new_vel[2] < 0.0f ? -root : root;

			Normalize2(new_vel);
			Vec2Mulf(new_vel, sasqrt(len2));
		}

		/* finally constrain speed to max speed */
		new_speed = Normalize(new_vel);
		VecMulf(new_vel, MIN2(new_speed, val.max_speed));

		/* get acceleration from difference of velocities */
		VecSubf(acc, new_vel, pa->prev_state.vel);

		/* break acceleration to components */
		Projf(tan_acc, acc, pa->prev_state.ave);
		VecSubf(nor_acc, acc, tan_acc);
	}

	/* account for effectors */
	do_effectors(p, pa, &pa->state, bbd->scene, bbd->ob, bbd->psys, pa->state.co, force, tvel, bbd->dfra, bbd->cfra);

	if(ELEM(pa->boid->mode, eBoidMode_OnLand, eBoidMode_Climbing)) {
		float length = Normalize(force);

		length = MAX2(0.0f, length - boids->land_stick_force);

		VecMulf(force, length);
	}
	
	VecAddf(acc, acc, force);

	/* store smoothed acceleration for nice banking etc. */
	VECADDFAC(pa->boid->acc, pa->boid->acc, acc, dtime);
	VecMulf(pa->boid->acc, 1.0f / (1.0f + dtime));

	/* integrate new location & velocity */

	/* by regarding the acceleration as a force at this stage we*/
	/* can get better control allthough it's a bit unphysical	*/
	VecMulf(acc, 1.0f/pa_mass);

	VECCOPY(dvec, acc);
	VecMulf(dvec, dtime*dtime*0.5f);
	
	VECCOPY(bvec, pa->prev_state.vel);
	VecMulf(bvec, dtime);
	VecAddf(dvec, dvec, bvec);
	VecAddf(pa->state.co, pa->state.co, dvec);

	VECADDFAC(pa->state.vel, pa->state.vel, acc, dtime);

	if(pa->boid->mode != eBoidMode_InAir)
		pa->stick_ob = boid_find_ground(bbd, pa, ground_co, ground_nor);

	/* change modes, constrain movement & keep track of down vector */
	switch(pa->boid->mode) {
		case eBoidMode_InAir:
		{
			float grav[3] = {0.0f, 0.0f, bbd->part->acc[2] < 0.0f ? -1.0f : 0.0f};

			/* don't take forward acceleration into account (better banking) */
			if(Inpf(pa->boid->acc, pa->state.vel) > 0.0f) {
				Projf(dvec, pa->boid->acc, pa->state.vel);
				VecSubf(dvec, pa->boid->acc, dvec);
			}
			else {
				VECCOPY(dvec, pa->boid->acc);
			}

			/* gather apparent gravity to r_ve */
			VECADDFAC(pa->r_ve, grav, dvec, -boids->banking);
			Normalize(pa->r_ve);

			/* stick boid on goal when close enough */
			if(bbd->goal_ob && boid_goal_signed_dist(pa->state.co, bbd->goal_co, bbd->goal_nor) <= pa->size * boids->height) {
				pa->boid->mode = eBoidMode_Climbing;
				pa->stick_ob = bbd->goal_ob;
				boid_find_ground(bbd, pa, ground_co, ground_nor);
				boid_climb(boids, pa, ground_co, ground_nor);
			}
			/* land boid when belowg ground */
			else if(boids->options & BOID_ALLOW_LAND && pa->state.co[2] <= ground_co[2] + pa->size * boids->height) {
				pa->state.co[2] = ground_co[2] + pa->size * boids->height;
				pa->state.vel[2] = 0.0f;
				pa->boid->mode = eBoidMode_OnLand;
			}
			break;
		}
		case eBoidMode_Falling:
		{
			float grav[3] = {0.0f, 0.0f, bbd->part->acc[2] < 0.0f ? -1.0f : 0.0f};

			/* gather apparent gravity to r_ve */
			VECADDFAC(pa->r_ve, pa->r_ve, grav, dtime);
			Normalize(pa->r_ve);

			if(boids->options & BOID_ALLOW_LAND) {
				/* stick boid on goal when close enough */
				if(bbd->goal_ob && boid_goal_signed_dist(pa->state.co, bbd->goal_co, bbd->goal_nor) <= pa->size * boids->height) {
					pa->boid->mode = eBoidMode_Climbing;
					pa->stick_ob = bbd->goal_ob;
					boid_find_ground(bbd, pa, ground_co, ground_nor);
					boid_climb(boids, pa, ground_co, ground_nor);
				}
				/* land boid when really near ground */
				else if(pa->state.co[2] <= ground_co[2] + 1.01 * pa->size * boids->height){
					pa->state.co[2] = ground_co[2] + pa->size * boids->height;
					pa->state.vel[2] = 0.0f;
					pa->boid->mode = eBoidMode_OnLand;
				}
				/* if we're falling, can fly and want to go upwards lets fly */
				else if(boids->options & BOID_ALLOW_FLIGHT && bbd->wanted_co[2] > 0.0f)
					pa->boid->mode = eBoidMode_InAir;
			}
			else
				pa->boid->mode = eBoidMode_InAir;
			break;
		}
		case eBoidMode_Climbing:
		{
			boid_climb(boids, pa, ground_co, ground_nor);
			//float nor[3];
			//VECCOPY(nor, ground_nor);

			///* gather apparent gravity to r_ve */
			//VECADDFAC(pa->r_ve, pa->r_ve, ground_nor, -1.0);
			//Normalize(pa->r_ve);

			///* raise boid it's size from surface */
			//VecMulf(nor, pa->size * boids->height);
			//VecAddf(pa->state.co, ground_co, nor);

			///* remove normal component from velocity */
			//Projf(v, pa->state.vel, ground_nor);
			//VecSubf(pa->state.vel, pa->state.vel, v);
			break;
		}
		case eBoidMode_OnLand:
		{
			/* stick boid on goal when close enough */
			if(bbd->goal_ob && boid_goal_signed_dist(pa->state.co, bbd->goal_co, bbd->goal_nor) <= pa->size * boids->height) {
				pa->boid->mode = eBoidMode_Climbing;
				pa->stick_ob = bbd->goal_ob;
				boid_find_ground(bbd, pa, ground_co, ground_nor);
				boid_climb(boids, pa, ground_co, ground_nor);
			}
			/* ground is too far away so boid falls */
			else if(pa->state.co[2]-ground_co[2] > 1.1 * pa->size * boids->height)
				pa->boid->mode = eBoidMode_Falling;
			else {
				/* constrain to surface */
				pa->state.co[2] = ground_co[2] + pa->size * boids->height;
				pa->state.vel[2] = 0.0f;
			}

			if(boids->banking > 0.0f) {
				float grav[3];
				/* Don't take gravity's strength in to account, */
				/* otherwise amount of banking is hard to control. */
				VECCOPY(grav, ground_nor);
				VecMulf(grav, -1.0f);
				
				Projf(dvec, pa->boid->acc, pa->state.vel);
				VecSubf(dvec, pa->boid->acc, dvec);

				/* gather apparent gravity to r_ve */
				VECADDFAC(pa->r_ve, grav, dvec, -boids->banking);
				Normalize(pa->r_ve);
			}
			else {
				/* gather negative surface normal to r_ve */
				VECADDFAC(pa->r_ve, pa->r_ve, ground_nor, -1.0f);
				Normalize(pa->r_ve);
			}
			break;
		}
	}

	/* save direction to state.ave unless the boid is falling */
	/* (boids can't effect their direction when falling) */
	if(pa->boid->mode!=eBoidMode_Falling && VecLength(pa->state.vel) > 0.1*pa->size) {
		VECCOPY(pa->state.ave, pa->state.vel);
		Normalize(pa->state.ave);
	}

	/* apply damping */
	if(ELEM(pa->boid->mode, eBoidMode_OnLand, eBoidMode_Climbing))
		VecMulf(pa->state.vel, 1.0f - 0.2f*bbd->part->dampfac);

	/* calculate rotation matrix based on forward & down vectors */
	if(pa->boid->mode == eBoidMode_InAir) {
		VECCOPY(mat[0], pa->state.ave);

		Projf(dvec, pa->r_ve, pa->state.ave);
		VecSubf(mat[2], pa->r_ve, dvec);
		Normalize(mat[2]);
	}
	else {
		Projf(dvec, pa->state.ave, pa->r_ve);
		VecSubf(mat[0], pa->state.ave, dvec);
		Normalize(mat[0]);

		VECCOPY(mat[2], pa->r_ve);
	}
	VecMulf(mat[2], -1.0f);
	Crossf(mat[1], mat[2], mat[0]);
	
	/* apply rotation */
	Mat3ToQuat_is_ok(mat, q);
	QuatCopy(pa->state.rot, q);
}

BoidRule *boid_new_rule(int type)
{
	BoidRule *rule = NULL;
	if(type <= 0)
		return NULL;

	switch(type) {
		case eBoidRuleType_Goal:
		case eBoidRuleType_Avoid:
			rule = MEM_callocN(sizeof(BoidRuleGoalAvoid), "BoidRuleGoalAvoid");
			break;
		case eBoidRuleType_AvoidCollision:
			rule = MEM_callocN(sizeof(BoidRuleAvoidCollision), "BoidRuleAvoidCollision");
			((BoidRuleAvoidCollision*)rule)->look_ahead = 2.0f;
			break;
		case eBoidRuleType_FollowLeader:
			rule = MEM_callocN(sizeof(BoidRuleFollowLeader), "BoidRuleFollowLeader");
			((BoidRuleFollowLeader*)rule)->distance = 1.0f;
			break;
		case eBoidRuleType_AverageSpeed:
			rule = MEM_callocN(sizeof(BoidRuleAverageSpeed), "BoidRuleAverageSpeed");
			((BoidRuleAverageSpeed*)rule)->speed = 0.5f;
			break;
		case eBoidRuleType_Fight:
			rule = MEM_callocN(sizeof(BoidRuleFight), "BoidRuleFight");
			((BoidRuleFight*)rule)->distance = 100.0f;
			((BoidRuleFight*)rule)->flee_distance = 100.0f;
			break;
		default:
			rule = MEM_callocN(sizeof(BoidRule), "BoidRule");
			break;
	}

	rule->type = type;
	rule->flag |= BOIDRULE_IN_AIR|BOIDRULE_ON_LAND;
	strcpy(rule->name, boidrule_type_items[type-1].name);

	return rule;
}
void boid_default_settings(BoidSettings *boids)
{
	boids->air_max_speed = 10.0f;
	boids->air_max_acc = 0.5f;
	boids->air_max_ave = 0.5f;
	boids->air_personal_space = 1.0f;

	boids->land_max_speed = 5.0f;
	boids->land_max_acc = 0.5f;
	boids->land_max_ave = 0.5f;
	boids->land_personal_space = 1.0f;

	boids->options = BOID_ALLOW_FLIGHT;

	boids->landing_smoothness = 3.0f;
	boids->banking = 1.0f;
	boids->height = 1.0f;

	boids->health = 1.0f;
	boids->accuracy = 1.0f;
	boids->aggression = 2.0f;
	boids->range = 1.0f;
	boids->strength = 0.1f;
}

BoidState *boid_new_state(BoidSettings *boids)
{
	BoidState *state = MEM_callocN(sizeof(BoidState), "BoidState");

	state->id = boids->last_state_id++;
	if(state->id)
		sprintf(state->name, "State %i", state->id);
	else
		strcpy(state->name, "State");

	state->rule_fuzziness = 0.5;
	state->volume = 1.0f;
	state->channels |= ~0;

	return state;
}

BoidState *boid_duplicate_state(BoidSettings *boids, BoidState *state) {
	BoidState *staten = MEM_dupallocN(state);

	BLI_duplicatelist(&staten->rules, &state->rules);
	BLI_duplicatelist(&staten->conditions, &state->conditions);
	BLI_duplicatelist(&staten->actions, &state->actions);

	staten->id = boids->last_state_id++;

	return staten;
}
void boid_free_settings(BoidSettings *boids)
{
	if(boids) {
		BoidState *state = boids->states.first;

		for(; state; state=state->next) {
			BLI_freelistN(&state->rules);
			BLI_freelistN(&state->conditions);
			BLI_freelistN(&state->actions);
		}

		BLI_freelistN(&boids->states);

		MEM_freeN(boids);
	}
}
BoidSettings *boid_copy_settings(BoidSettings *boids)
{
	BoidSettings *nboids = NULL;

	if(boids) {
		BoidState *state;
		BoidState *nstate;

		nboids = MEM_dupallocN(boids);

		BLI_duplicatelist(&nboids->states, &boids->states);

		state = boids->states.first;
		nstate = nboids->states.first;
		for(; state; state=state->next, nstate=nstate->next) {
			BLI_duplicatelist(&nstate->rules, &state->rules);
			BLI_duplicatelist(&nstate->conditions, &state->conditions);
			BLI_duplicatelist(&nstate->actions, &state->actions);
		}
	}

	return nboids;
}
BoidState *boid_get_current_state(BoidSettings *boids)
{
	BoidState *state = boids->states.first;

	for(; state; state=state->next) {
		if(state->flag & BOIDSTATE_CURRENT)
			break;
	}

	return state;
}

