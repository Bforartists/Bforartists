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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * Contributors: Matt Ebb
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <math.h>
#include <stdlib.h>
#include <stdio.h>

#include "MEM_guardedalloc.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"
#include "BLI_kdopbvh.h"

#include "BKE_DerivedMesh.h"
#include "BKE_global.h"
#include "BKE_lattice.h"
#include "BKE_main.h"
#include "BKE_object.h"
#include "BKE_particle.h"
#include "BKE_texture.h"

#include "DNA_texture_types.h"
#include "DNA_particle_types.h"

#include "render_types.h"
#include "renderdatabase.h"
#include "texture.h"

/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */
/* defined in pipeline.c, is hardcopy of active dynamic allocated Render */
/* only to be used here in this file, it's for speed */
extern struct Render R;
/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */


static int point_data_used(PointDensity *pd)
{
	int pd_bitflag = 0;
	
	if ((pd->noise_influence == TEX_PD_NOISE_VEL) || (pd->color_source == TEX_PD_COLOR_PARTVEL) || (pd->color_source == TEX_PD_COLOR_PARTSPEED))
		pd_bitflag |= POINT_DATA_VEL;
	if ((pd->noise_influence == TEX_PD_NOISE_AGE) || (pd->color_source == TEX_PD_COLOR_PARTAGE)) 
		pd_bitflag |= POINT_DATA_LIFE;
		
	return pd_bitflag;
}


/* additional data stored alongside the point density BVH, 
 * accessible by point index number to retrieve other information 
 * such as particle velocity or lifetime */
static void alloc_point_data(PointDensity *pd, int total_particles, int point_data_used)
{
	int data_size = 0;
	
	if (point_data_used & POINT_DATA_VEL) {
		/* store 3 channels of velocity data */
		data_size += 3;
	}
	if (point_data_used & POINT_DATA_LIFE) {
		/* store 1 channel of lifetime data */
		data_size += 1;
	}

	if (data_size)
		pd->point_data = MEM_mallocN(sizeof(float)*data_size*total_particles, "particle point data");
}

static void pointdensity_cache_psys(Render *re, PointDensity *pd, Object *ob, ParticleSystem *psys)
{
	DerivedMesh* dm;
	ParticleKey state;
	ParticleData *pa=NULL;
	float cfra=bsystem_time(ob,(float)G.scene->r.cfra,0.0);
	int i, childexists;
	int total_particles, offset=0;
	int data_used = point_data_used(pd);
	float partco[3];
	float obview[4][4];
	
	
	/* init everything */
	if (!psys || !ob || !pd) return;
	
	Mat4MulMat4(obview, re->viewinv, ob->obmat);
	
	/* Just to create a valid rendering context for particles */
	psys_render_set(ob, psys, re->viewmat, re->winmat, re->winx, re->winy, 0);
	
	dm = mesh_create_derived_render(ob,CD_MASK_BAREMESH|CD_MASK_MTFACE|CD_MASK_MCOL);
	
	if ( !psys_check_enabled(ob, psys)) {
		psys_render_restore(ob, psys);
		return;
	}
	
	/* in case ob->imat isn't up-to-date */
	Mat4Invert(ob->imat, ob->obmat);
	
	total_particles = psys->totpart+psys->totchild;
	psys->lattice=psys_get_lattice(ob,psys);
	
	pd->point_tree = BLI_bvhtree_new(total_particles, 0.0, 4, 6);
	alloc_point_data(pd, total_particles, data_used);
	pd->totpoints = total_particles;
	if (data_used & POINT_DATA_VEL) offset = pd->totpoints*3;
	
	if (psys->totchild > 0 && !(psys->part->draw & PART_DRAW_PARENT))
		childexists = 1;
	
	for (i=0, pa=psys->particles; i < total_particles; i++, pa++) {

		state.time = cfra;
		if(psys_get_particle_state(ob, psys, i, &state, 0)) {
			
			VECCOPY(partco, state.co);
			
			if (pd->psys_cache_space == TEX_PD_OBJECTSPACE)
				Mat4MulVecfl(ob->imat, partco);
			else if (pd->psys_cache_space == TEX_PD_OBJECTLOC) {
				float obloc[3];
				VECCOPY(obloc, ob->loc);
				VecSubf(partco, partco, obloc);
			} else {
				/* TEX_PD_WORLDSPACE */
			}
			
			BLI_bvhtree_insert(pd->point_tree, i, partco, 1);
			
			if (data_used & POINT_DATA_VEL) {
				pd->point_data[i*3 + 0] = state.vel[0];
				pd->point_data[i*3 + 1] = state.vel[1];
				pd->point_data[i*3 + 2] = state.vel[2];
			} 
			if (data_used & POINT_DATA_LIFE) {
				float pa_time;
				
				if (i < psys->totpart) {
					pa_time = (cfra - pa->time)/pa->lifetime;
				} else {
					ChildParticle *cpa= (psys->child + i) - psys->totpart;
					pa_time = psys_get_child_time(psys, cpa, cfra);
				}
				
				pd->point_data[offset + i] = pa_time;
			}
		}
	}
	
	BLI_bvhtree_balance(pd->point_tree);
	dm->release(dm);
	
	if(psys->lattice){
		end_latt_deform();
		psys->lattice=0;
	}
	
	psys_render_restore(ob, psys);
}


static void pointdensity_cache_object(Render *re, PointDensity *pd, ObjectRen *obr)
{
	int i;
	
	if (!obr || !pd) return;
	if(!obr->vertnodes) return;
	
	/* in case ob->imat isn't up-to-date */
	Mat4Invert(obr->ob->imat, obr->ob->obmat);
	
	pd->point_tree = BLI_bvhtree_new(obr->totvert, 0.0, 4, 6);
	pd->totpoints = obr->totvert;
	
	for(i=0; i<obr->totvert; i++) {
		float ver_co[3];
		VertRen *ver= RE_findOrAddVert(obr, i);
		
		VECCOPY(ver_co, ver->co);
		Mat4MulVecfl(re->viewinv, ver_co);
		
		if (pd->ob_cache_space == TEX_PD_OBJECTSPACE) {
			Mat4MulVecfl(obr->ob->imat, ver_co);
		} else if (pd->psys_cache_space == TEX_PD_OBJECTLOC) {
			VecSubf(ver_co, ver_co, obr->ob->loc);
		} else {
			/* TEX_PD_WORLDSPACE */
		}
		
		BLI_bvhtree_insert(pd->point_tree, i, ver_co, 1);
	}
	
	BLI_bvhtree_balance(pd->point_tree);

}
static void cache_pointdensity(Render *re, Tex *tex)
{
	PointDensity *pd = tex->pd;

	if (pd->point_tree) {
		BLI_bvhtree_free(pd->point_tree);
		pd->point_tree = NULL;
	}
	
	if (pd->source == TEX_PD_PSYS) {
		ParticleSystem *psys;
		Object *ob = pd->object;
		int i;
		
		if (!ob) return;
		
		for(psys=ob->particlesystem.first, i=0; i< pd->psysindex-1; i++)
			psys= psys->next;
		
		if (!psys) return;
		
		pointdensity_cache_psys(re, pd, ob, psys);
	}
	else if (pd->source == TEX_PD_OBJECT) {
		Object *ob = pd->object;
		ObjectRen *obr;
		int found=0;

		/* find the obren that corresponds to the object */
		for (obr=re->objecttable.first; obr; obr=obr->next) {
			if (obr->ob == ob) {
				found=1;
				break;
			}
		}
		if (!found) return;
		
		pointdensity_cache_object(re, pd, obr);
	}
}

static void free_pointdensity(Render *re, Tex *tex)
{
	PointDensity *pd = tex->pd;

	if (pd->point_tree) {
		BLI_bvhtree_free(pd->point_tree);
		pd->point_tree = NULL;
	}

	if (pd->point_data) {
		MEM_freeN(pd->point_data);
		pd->point_data = NULL;
	}
	pd->totpoints = 0;
}



void make_pointdensities(Render *re)
{
	Tex *tex;
	
	if(re->scene->r.scemode & R_PREVIEWBUTS)
		return;
	
	re->i.infostr= "Caching Point Densities";
	re->stats_draw(&re->i);

	for (tex= G.main->tex.first; tex; tex= tex->id.next) {
		if(tex->id.us && tex->type==TEX_POINTDENSITY) {
			cache_pointdensity(re, tex);
		}
	}
	
	re->i.infostr= NULL;
	re->stats_draw(&re->i);
}

void free_pointdensities(Render *re)
{
	Tex *tex;
	
	if(re->scene->r.scemode & R_PREVIEWBUTS)
		return;
	
	for (tex= G.main->tex.first; tex; tex= tex->id.next) {
		if(tex->id.us && tex->type==TEX_POINTDENSITY) {
			free_pointdensity(re, tex);
		}
	}
}

typedef struct PointDensityRangeData
{
    float *density;
    float squared_radius;
    float *point_data;
	float *vec;
	float softness;
    short falloff_type;
	short noise_influence;
	float *age;
	int point_data_used;
	int offset;
} PointDensityRangeData;

void accum_density(void *userdata, int index, float squared_dist)
{
	PointDensityRangeData *pdr = (PointDensityRangeData *)userdata;
	const float dist = (pdr->squared_radius - squared_dist) / pdr->squared_radius * 0.5f;
	float density;
	
	if (pdr->falloff_type == TEX_PD_FALLOFF_STD)
		density = dist;
	else if (pdr->falloff_type == TEX_PD_FALLOFF_SMOOTH)
		density = 3.0f*dist*dist - 2.0f*dist*dist*dist;
	else if (pdr->falloff_type == TEX_PD_FALLOFF_SOFT)
		density = pow(dist, pdr->softness);
	else if (pdr->falloff_type == TEX_PD_FALLOFF_CONSTANT)
		density = pdr->squared_radius;
	else if (pdr->falloff_type == TEX_PD_FALLOFF_ROOT)
		density = sqrt(dist);
	
	if (pdr->point_data_used & POINT_DATA_VEL) {
		pdr->vec[0] += pdr->point_data[index*3 + 0]; //* density;
		pdr->vec[1] += pdr->point_data[index*3 + 1]; //* density;
		pdr->vec[2] += pdr->point_data[index*3 + 2]; //* density;
	}
	if (pdr->point_data_used & POINT_DATA_LIFE) {
		*pdr->age += pdr->point_data[pdr->offset + index]; // * density;
	}
	
	*pdr->density += density;
}


static void init_pointdensityrangedata(PointDensity *pd, PointDensityRangeData *pdr, float *density, float *vec, float *age)
{
	pdr->squared_radius = pd->radius*pd->radius;
	pdr->density = density;
	pdr->point_data = pd->point_data;
	pdr->falloff_type = pd->falloff_type;
	pdr->vec = vec;
	pdr->age = age;
	pdr->softness = pd->falloff_softness;
	pdr->noise_influence = pd->noise_influence;
	pdr->point_data_used = point_data_used(pd);
	pdr->offset = (pdr->point_data_used & POINT_DATA_VEL)?pd->totpoints*3:0;
}


int pointdensitytex(Tex *tex, float *texvec, TexResult *texres)
{
	int retval = TEX_INT+TEX_RGB;
	PointDensity *pd = tex->pd;
	PointDensityRangeData pdr;
	float density=0.0f, age=0.0f, time=0.0f;
	float vec[3] = {0.0f, 0.0f, 0.0f}, co[3];
	float col[4];
	float turb, noise_fac;
	int num=0;
	
	if ((!pd) || (!pd->point_tree)) {
		texres->tin = 0.0f;
		return 0;
	}
	
	init_pointdensityrangedata(pd, &pdr, &density, vec, &age);
	noise_fac = pd->noise_fac * 0.5f;	/* better default */
	
	VECCOPY(co, texvec);
	
	if (point_data_used(pd)) {
		/* does a BVH lookup to find accumulated density and additional point data *
		 * stores particle velocity vector in 'vec', and particle lifetime in 'time' */
		num = BLI_bvhtree_range_query(pd->point_tree, co, pd->radius, accum_density, &pdr);
		if (num > 0) {
			age /= num;
			VecMulf(vec, 1.0f/num);
		}
	}
	
	if (pd->flag & TEX_PD_TURBULENCE) {
	
		if (pd->noise_influence == TEX_PD_NOISE_AGE) {
			turb = BLI_turbulence(pd->noise_size, texvec[0]+age, texvec[1]+age, texvec[2]+age, pd->noise_depth);
		}
		else if (pd->noise_influence == TEX_PD_NOISE_TIME) {
			time = R.cfra / (float)R.r.efra;
			turb = BLI_turbulence(pd->noise_size, texvec[0]+time, texvec[1]+time, texvec[2]+time, pd->noise_depth);
		}
		else {
			turb = BLI_turbulence(pd->noise_size, texvec[0]+vec[0], texvec[1]+vec[1], texvec[2]+vec[2], pd->noise_depth);
		}

		turb -= 0.5f;	/* re-center 0.0-1.0 range around 0 to prevent offsetting result */
		
		/* now we have an offset coordinate to use for the density lookup */
		co[0] = texvec[0] + noise_fac * turb;
		co[1] = texvec[1] + noise_fac * turb;
		co[2] = texvec[2] + noise_fac * turb;
		
		/* reset and prepare for a new BVH query with the perturbed coordinates */
		density = vec[0] = vec[1] = vec[2] = 0.0f;
	}

	num = BLI_bvhtree_range_query(pd->point_tree, co, pd->radius, accum_density, &pdr);
	if (num > 0) {
		age /= num;
		VecMulf(vec, 1.0f/num);
	}
	
	texres->tin = density;
	BRICONT;
	
	switch (pd->color_source) {
		case TEX_PD_COLOR_PARTAGE:
			if (pd->coba) {
				if (do_colorband(pd->coba, age, col)) {
					texres->talpha= 1;
					QUATCOPY(&texres->tr, col);
					texres->tin *= texres->ta;
				}
			}
			break;
		case TEX_PD_COLOR_PARTSPEED:
		{
			float speed = VecLength(vec) * pd->speed_scale;
			
			if (pd->coba) {
				if (do_colorband(pd->coba, speed, col)) {
					texres->talpha= 1;	
					QUATCOPY(&texres->tr, col);
					texres->tin *= texres->ta;
				}
			}
			break;
		}
		case TEX_PD_COLOR_PARTVEL:
			VecMulf(vec, pd->speed_scale);
			VECCOPY(&texres->tr, vec);
			texres->ta = 1.0f;
			break;
		case TEX_PD_COLOR_CONSTANT:
		default:
			texres->tr = texres->tg = texres->tb = texres->ta = 1.0f;
			break;
	}
	BRICONTRGB;
	
	return retval;
	
	/*
	if (texres->nor!=NULL) {
		texres->nor[0] = texres->nor[1] = texres->nor[2] = 0.0f;
	}
	*/
}
