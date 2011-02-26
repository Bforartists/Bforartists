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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) Blender Foundation
 * All rights reserved.
 *
 * Contributor(s): Daniel Genrich
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "MEM_guardedalloc.h"

#include "DNA_cloth_types.h"
#include "DNA_scene_types.h"
#include "DNA_object_types.h"
#include "DNA_meshdata_types.h"

#include "BLI_math.h"
#include "BLI_edgehash.h"
#include "BLI_utildefines.h"

#include "BKE_cdderivedmesh.h"
#include "BKE_cloth.h"
#include "BKE_effect.h"
#include "BKE_global.h"
#include "BKE_modifier.h"
#include "BKE_pointcache.h"


#ifdef _WIN32
void tstart ( void )
{}
void tend ( void )
{
}
double tval( void )
{
	return 0;
}
#else
#include <sys/time.h>
			 static struct timeval _tstart, _tend;
	 static struct timezone tz;
	 void tstart ( void )
{
	gettimeofday ( &_tstart, &tz );
}
void tend ( void )
{
	gettimeofday ( &_tend,&tz );
}
double tval(void)
{
	double t1, t2;
	t1 = ( double ) _tstart.tv_sec + ( double ) _tstart.tv_usec/ ( 1000*1000 );
	t2 = ( double ) _tend.tv_sec + ( double ) _tend.tv_usec/ ( 1000*1000 );
	return t2-t1;
}
#endif

/* Our available solvers. */
// 255 is the magic reserved number, so NEVER try to put 255 solvers in here!
// 254 = MAX!
static CM_SOLVER_DEF	solvers [] =
{
	{ "Implicit", CM_IMPLICIT, implicit_init, implicit_solver, implicit_free },
		// { "Implicit C++", CM_IMPLICITCPP, implicitcpp_init, implicitcpp_solver, implicitcpp_free },
};

/* ********** cloth engine ******* */
/* Prototypes for internal functions.
*/
static void cloth_to_object (Object *ob,  ClothModifierData *clmd, DerivedMesh *dm);
static void cloth_from_mesh ( ClothModifierData *clmd, DerivedMesh *dm );
static int cloth_from_object(Object *ob, ClothModifierData *clmd, DerivedMesh *dm, float framenr, int first);
static int cloth_build_springs ( ClothModifierData *clmd, DerivedMesh *dm );
static void cloth_apply_vgroup ( ClothModifierData *clmd, DerivedMesh *dm );


/******************************************************************************
*
* External interface called by modifier.c clothModifier functions.
*
******************************************************************************/
/**
 * cloth_init -  creates a new cloth simulation.
 *
 * 1. create object
 * 2. fill object with standard values or with the GUI settings if given
 */
void cloth_init ( ClothModifierData *clmd )
{	
	/* Initialize our new data structure to reasonable values. */
	clmd->sim_parms->gravity [0] = 0.0;
	clmd->sim_parms->gravity [1] = 0.0;
	clmd->sim_parms->gravity [2] = -9.81;
	clmd->sim_parms->structural = 15.0;
	clmd->sim_parms->shear = 15.0;
	clmd->sim_parms->bending = 0.5;
	clmd->sim_parms->Cdis = 5.0; 
	clmd->sim_parms->Cvi = 1.0;
	clmd->sim_parms->mass = 0.3f;
	clmd->sim_parms->stepsPerFrame = 5;
	clmd->sim_parms->flags = 0;
	clmd->sim_parms->solver_type = 0;
	clmd->sim_parms->preroll = 0;
	clmd->sim_parms->maxspringlen = 10;
	clmd->sim_parms->vgroup_mass = 0;
	clmd->sim_parms->avg_spring_len = 0.0;
	clmd->sim_parms->presets = 2; /* cotton as start setting */
	clmd->sim_parms->timescale = 1.0f; /* speed factor, describes how fast cloth moves */
	clmd->sim_parms->reset = 0;
	
	clmd->coll_parms->self_friction = 5.0;
	clmd->coll_parms->friction = 5.0;
	clmd->coll_parms->loop_count = 2;
	clmd->coll_parms->epsilon = 0.015f;
	clmd->coll_parms->flags = CLOTH_COLLSETTINGS_FLAG_ENABLED;
	clmd->coll_parms->collision_list = NULL;
	clmd->coll_parms->self_loop_count = 1.0;
	clmd->coll_parms->selfepsilon = 0.75;

	/* These defaults are copied from softbody.c's
	* softbody_calc_forces() function.
	*/
	clmd->sim_parms->eff_force_scale = 1000.0;
	clmd->sim_parms->eff_wind_scale = 250.0;

	// also from softbodies
	clmd->sim_parms->maxgoal = 1.0f;
	clmd->sim_parms->mingoal = 0.0f;
	clmd->sim_parms->defgoal = 0.0f;
	clmd->sim_parms->goalspring = 1.0f;
	clmd->sim_parms->goalfrict = 0.0f;
	clmd->sim_parms->velocity_smooth = 0.0f;

	if(!clmd->sim_parms->effector_weights)
		clmd->sim_parms->effector_weights = BKE_add_effector_weights(NULL);

	if(clmd->point_cache)
		clmd->point_cache->step = 1;
}

static BVHTree *bvhselftree_build_from_cloth (ClothModifierData *clmd, float epsilon)
{
	unsigned int i;
	BVHTree *bvhtree;
	Cloth *cloth;
	ClothVertex *verts;
	float co[12];

	if(!clmd)
		return NULL;

	cloth = clmd->clothObject;

	if(!cloth)
		return NULL;
	
	verts = cloth->verts;
	
	// in the moment, return zero if no faces there
	if(!cloth->numverts)
		return NULL;
	
	// create quadtree with k=26
	bvhtree = BLI_bvhtree_new(cloth->numverts, epsilon, 4, 6);
	
	// fill tree
	for(i = 0; i < cloth->numverts; i++, verts++)
	{
		VECCOPY(&co[0*3], verts->xold);
		
		BLI_bvhtree_insert(bvhtree, i, co, 1);
	}
	
	// balance tree
	BLI_bvhtree_balance(bvhtree);
	
	return bvhtree;
}

static BVHTree *bvhtree_build_from_cloth (ClothModifierData *clmd, float epsilon)
{
	unsigned int i;
	BVHTree *bvhtree;
	Cloth *cloth;
	ClothVertex *verts;
	MFace *mfaces;
	float co[12];

	if(!clmd)
		return NULL;

	cloth = clmd->clothObject;

	if(!cloth)
		return NULL;
	
	verts = cloth->verts;
	mfaces = cloth->mfaces;
	
	// in the moment, return zero if no faces there
	if(!cloth->numfaces)
		return NULL;
	
	// create quadtree with k=26
	bvhtree = BLI_bvhtree_new(cloth->numfaces, epsilon, 4, 26);
	
	// fill tree
	for(i = 0; i < cloth->numfaces; i++, mfaces++)
	{
		VECCOPY(&co[0*3], verts[mfaces->v1].xold);
		VECCOPY(&co[1*3], verts[mfaces->v2].xold);
		VECCOPY(&co[2*3], verts[mfaces->v3].xold);
		
		if(mfaces->v4)
			VECCOPY(&co[3*3], verts[mfaces->v4].xold);
		
		BLI_bvhtree_insert(bvhtree, i, co, (mfaces->v4 ? 4 : 3));
	}
	
	// balance tree
	BLI_bvhtree_balance(bvhtree);
	
	return bvhtree;
}

void bvhtree_update_from_cloth(ClothModifierData *clmd, int moving)
{	
	unsigned int i = 0;
	Cloth *cloth = clmd->clothObject;
	BVHTree *bvhtree = cloth->bvhtree;
	ClothVertex *verts = cloth->verts;
	MFace *mfaces;
	float co[12], co_moving[12];
	int ret = 0;
	
	if(!bvhtree)
		return;
	
	mfaces = cloth->mfaces;
	
	// update vertex position in bvh tree
	if(verts && mfaces)
	{
		for(i = 0; i < cloth->numfaces; i++, mfaces++)
		{
			VECCOPY(&co[0*3], verts[mfaces->v1].txold);
			VECCOPY(&co[1*3], verts[mfaces->v2].txold);
			VECCOPY(&co[2*3], verts[mfaces->v3].txold);
			
			if(mfaces->v4)
				VECCOPY(&co[3*3], verts[mfaces->v4].txold);
		
			// copy new locations into array
			if(moving)
			{
				// update moving positions
				VECCOPY(&co_moving[0*3], verts[mfaces->v1].tx);
				VECCOPY(&co_moving[1*3], verts[mfaces->v2].tx);
				VECCOPY(&co_moving[2*3], verts[mfaces->v3].tx);
				
				if(mfaces->v4)
					VECCOPY(&co_moving[3*3], verts[mfaces->v4].tx);
				
				ret = BLI_bvhtree_update_node(bvhtree, i, co, co_moving, (mfaces->v4 ? 4 : 3));
			}
			else
			{
				ret = BLI_bvhtree_update_node(bvhtree, i, co, NULL, (mfaces->v4 ? 4 : 3));
			}
			
			// check if tree is already full
			if(!ret)
				break;
		}
		
		BLI_bvhtree_update_tree(bvhtree);
	}
}

void bvhselftree_update_from_cloth(ClothModifierData *clmd, int moving)
{	
	unsigned int i = 0;
	Cloth *cloth = clmd->clothObject;
	BVHTree *bvhtree = cloth->bvhselftree;
	ClothVertex *verts = cloth->verts;
	MFace *mfaces;
	float co[12], co_moving[12];
	int ret = 0;
	
	if(!bvhtree)
		return;
	
	mfaces = cloth->mfaces;
	
	// update vertex position in bvh tree
	if(verts && mfaces)
	{
		for(i = 0; i < cloth->numverts; i++, verts++)
		{
			VECCOPY(&co[0*3], verts->txold);
			
			// copy new locations into array
			if(moving)
			{
				// update moving positions
				VECCOPY(&co_moving[0*3], verts->tx);
				
				ret = BLI_bvhtree_update_node(bvhtree, i, co, co_moving, 1);
			}
			else
			{
				ret = BLI_bvhtree_update_node(bvhtree, i, co, NULL, 1);
			}
			
			// check if tree is already full
			if(!ret)
				break;
		}
		
		BLI_bvhtree_update_tree(bvhtree);
	}
}

void cloth_clear_cache(Object *ob, ClothModifierData *clmd, float framenr)
{
	PTCacheID pid;
	
	BKE_ptcache_id_from_cloth(&pid, ob, clmd);

	// don't do anything as long as we're in editmode!
	if(pid.cache->edit && ob->mode & OB_MODE_PARTICLE_EDIT)
		return;
	
	BKE_ptcache_id_clear(&pid, PTCACHE_CLEAR_AFTER, framenr);
}

static int do_init_cloth(Object *ob, ClothModifierData *clmd, DerivedMesh *result, int framenr)
{
	PointCache *cache;

	cache= clmd->point_cache;

	/* initialize simulation data if it didn't exist already */
	if(clmd->clothObject == NULL) {	
		if(!cloth_from_object(ob, clmd, result, framenr, 1)) {
			BKE_ptcache_invalidate(cache);
			return 0;
		}
	
		if(clmd->clothObject == NULL) {
			BKE_ptcache_invalidate(cache);
			return 0;
		}
	
		implicit_set_positions(clmd);
	}

	return 1;
}

static int do_step_cloth(Object *ob, ClothModifierData *clmd, DerivedMesh *result, int framenr)
{
	ClothVertex *verts = NULL;
	Cloth *cloth;
	ListBase *effectors = NULL;
	MVert *mvert;
	unsigned int i = 0;
	int ret = 0;

	/* simulate 1 frame forward */
	cloth = clmd->clothObject;
	verts = cloth->verts;
	mvert = result->getVertArray(result);

	/* force any pinned verts to their constrained location. */
	for(i = 0; i < clmd->clothObject->numverts; i++, verts++) {
		/* save the previous position. */
		VECCOPY(verts->xold, verts->xconst);
		VECCOPY(verts->txold, verts->x);

		/* Get the current position. */
		VECCOPY(verts->xconst, mvert[i].co);
		mul_m4_v3(ob->obmat, verts->xconst);
	}

	effectors = pdInitEffectors(clmd->scene, ob, NULL, clmd->sim_parms->effector_weights);
	
	tstart();

	/* call the solver. */
	if(solvers [clmd->sim_parms->solver_type].solver)
		ret = solvers[clmd->sim_parms->solver_type].solver(ob, framenr, clmd, effectors);

	tend();

	pdEndEffectors(&effectors);

	// printf ( "%f\n", ( float ) tval() );
	
	return ret;
}

/************************************************
 * clothModifier_do - main simulation function
************************************************/
DerivedMesh *clothModifier_do(ClothModifierData *clmd, Scene *scene, Object *ob, DerivedMesh *dm)
{
	DerivedMesh *result;
	PointCache *cache;
	PTCacheID pid;
	float timescale;
	int framenr, startframe, endframe;
	int cache_result;

	clmd->scene= scene;	/* nice to pass on later :) */
	framenr= (int)scene->r.cfra;
	cache= clmd->point_cache;
	result = CDDM_copy(dm);

	BKE_ptcache_id_from_cloth(&pid, ob, clmd);
	BKE_ptcache_id_time(&pid, scene, framenr, &startframe, &endframe, &timescale);
	clmd->sim_parms->timescale= timescale;

	if(!result) {
		BKE_ptcache_invalidate(cache);
		return dm;
	}

	if(clmd->sim_parms->reset
		|| (framenr == (startframe - clmd->sim_parms->preroll) && clmd->sim_parms->preroll != 0)
		|| (clmd->clothObject && result->getNumVerts(result) != clmd->clothObject->numverts))
	{
		clmd->sim_parms->reset = 0;
		cache->flag |= PTCACHE_OUTDATED;
		BKE_ptcache_id_reset(scene, &pid, PTCACHE_RESET_OUTDATED);
		BKE_ptcache_validate(cache, 0);
		cache->last_exact= 0;
		cache->flag &= ~PTCACHE_REDO_NEEDED;
		return result;
	}
	
	// unused in the moment, calculated separately in implicit.c
	clmd->sim_parms->dt = clmd->sim_parms->timescale / clmd->sim_parms->stepsPerFrame;

	/* handle continuous simulation with the play button */
	if(BKE_ptcache_get_continue_physics() || ((clmd->sim_parms->preroll > 0) && (framenr > startframe - clmd->sim_parms->preroll) && (framenr < startframe))) {
		BKE_ptcache_invalidate(cache);

		/* do simulation */
		if(!do_init_cloth(ob, clmd, dm, framenr))
			return result;

		do_step_cloth(ob, clmd, dm, framenr);
		cloth_to_object(ob, clmd, result);

		return result;
	}

	/* simulation is only active during a specific period */
	if(framenr < startframe) {
		BKE_ptcache_invalidate(cache);
		return result;
	}
	else if(framenr > endframe) {
		framenr= endframe;
	}

	/* initialize simulation data if it didn't exist already */
	if(!do_init_cloth(ob, clmd, dm, framenr))
		return result;

	if((framenr == startframe) && (clmd->sim_parms->preroll == 0)) {
		BKE_ptcache_id_reset(scene, &pid, PTCACHE_RESET_OUTDATED);
		do_init_cloth(ob, clmd, dm, framenr);
		BKE_ptcache_validate(cache, framenr);
		cache->flag &= ~PTCACHE_REDO_NEEDED;
		return result;
	}

	/* try to read from cache */
	cache_result = BKE_ptcache_read(&pid, (float)framenr+scene->r.subframe);

	if(cache_result == PTCACHE_READ_EXACT || cache_result == PTCACHE_READ_INTERPOLATED) {
		implicit_set_positions(clmd);
		cloth_to_object (ob, clmd, result);

		BKE_ptcache_validate(cache, framenr);

		if(cache_result == PTCACHE_READ_INTERPOLATED && cache->flag & PTCACHE_REDO_NEEDED)
			BKE_ptcache_write(&pid, framenr);

		return result;
	}
	else if(cache_result==PTCACHE_READ_OLD) {
		implicit_set_positions(clmd);
	}
	else if( /*ob->id.lib ||*/ (cache->flag & PTCACHE_BAKED)) { /* 2.4x disabled lib, but this can be used in some cases, testing further - campbell */
		/* if baked and nothing in cache, do nothing */
		BKE_ptcache_invalidate(cache);
		return result;
	}

	/* if on second frame, write cache for first frame */
	if(cache->simframe == startframe && (cache->flag & PTCACHE_OUTDATED || cache->last_exact==0))
		BKE_ptcache_write(&pid, startframe);

	clmd->sim_parms->timescale *= framenr - cache->simframe;

	/* do simulation */
	BKE_ptcache_validate(cache, framenr);

	if(!do_step_cloth(ob, clmd, dm, framenr)) {
		BKE_ptcache_invalidate(cache);
	}
	else
		BKE_ptcache_write(&pid, framenr);

	cloth_to_object (ob, clmd, result);

	return result;
}

/* frees all */
void cloth_free_modifier(ClothModifierData *clmd )
{
	Cloth	*cloth = NULL;
	
	if ( !clmd )
		return;

	cloth = clmd->clothObject;

	
	if ( cloth )
	{	
		// If our solver provides a free function, call it
		if ( solvers [clmd->sim_parms->solver_type].free )
		{
			solvers [clmd->sim_parms->solver_type].free ( clmd );
		}

		// Free the verts.
		if ( cloth->verts != NULL )
			MEM_freeN ( cloth->verts );

		cloth->verts = NULL;
		cloth->numverts = 0;

		// Free the springs.
		if ( cloth->springs != NULL )
		{
			LinkNode *search = cloth->springs;
			while(search)
			{
				ClothSpring *spring = search->link;
						
				MEM_freeN ( spring );
				search = search->next;
			}
			BLI_linklist_free(cloth->springs, NULL);
		
			cloth->springs = NULL;
		}

		cloth->springs = NULL;
		cloth->numsprings = 0;

		// free BVH collision tree
		if ( cloth->bvhtree )
			BLI_bvhtree_free ( cloth->bvhtree );
		
		if ( cloth->bvhselftree )
			BLI_bvhtree_free ( cloth->bvhselftree );

		// we save our faces for collision objects
		if ( cloth->mfaces )
			MEM_freeN ( cloth->mfaces );
		
		if(cloth->edgehash)
			BLI_edgehash_free ( cloth->edgehash, NULL );
		
		
		/*
		if(clmd->clothObject->facemarks)
		MEM_freeN(clmd->clothObject->facemarks);
		*/
		MEM_freeN ( cloth );
		clmd->clothObject = NULL;
	}
}

/* frees all */
void cloth_free_modifier_extern ( ClothModifierData *clmd )
{
	Cloth	*cloth = NULL;
	if(G.rt > 0)
		printf("cloth_free_modifier_extern\n");
	
	if ( !clmd )
		return;

	cloth = clmd->clothObject;
	
	if ( cloth )
	{	
		if(G.rt > 0)
			printf("cloth_free_modifier_extern in\n");
		
		// If our solver provides a free function, call it
		if ( solvers [clmd->sim_parms->solver_type].free )
		{
			solvers [clmd->sim_parms->solver_type].free ( clmd );
		}

		// Free the verts.
		if ( cloth->verts != NULL )
			MEM_freeN ( cloth->verts );

		cloth->verts = NULL;
		cloth->numverts = 0;

		// Free the springs.
		if ( cloth->springs != NULL )
		{
			LinkNode *search = cloth->springs;
			while(search)
			{
				ClothSpring *spring = search->link;
						
				MEM_freeN ( spring );
				search = search->next;
			}
			BLI_linklist_free(cloth->springs, NULL);
		
			cloth->springs = NULL;
		}

		cloth->springs = NULL;
		cloth->numsprings = 0;

		// free BVH collision tree
		if ( cloth->bvhtree )
			BLI_bvhtree_free ( cloth->bvhtree );
		
		if ( cloth->bvhselftree )
			BLI_bvhtree_free ( cloth->bvhselftree );

		// we save our faces for collision objects
		if ( cloth->mfaces )
			MEM_freeN ( cloth->mfaces );
		
		if(cloth->edgehash)
			BLI_edgehash_free ( cloth->edgehash, NULL );
		
		
		/*
		if(clmd->clothObject->facemarks)
		MEM_freeN(clmd->clothObject->facemarks);
		*/
		MEM_freeN ( cloth );
		clmd->clothObject = NULL;
	}
}

/******************************************************************************
*
* Internal functions.
*
******************************************************************************/

/**
 * cloth_to_object - copies the deformed vertices to the object.
 *
 **/
static void cloth_to_object (Object *ob,  ClothModifierData *clmd, DerivedMesh *dm)
{
	unsigned int	i = 0;
	MVert *mvert = NULL;
	unsigned int numverts;
	Cloth *cloth = clmd->clothObject;

	if (clmd->clothObject) {
		/* inverse matrix is not uptodate... */
		invert_m4_m4(ob->imat, ob->obmat);

		mvert = CDDM_get_verts(dm);
		numverts = dm->getNumVerts(dm);

		for (i = 0; i < numverts; i++)
		{
			VECCOPY (mvert[i].co, cloth->verts[i].x);
			mul_m4_v3(ob->imat, mvert[i].co);	/* cloth is in global coords */
		}
	}
}


int cloth_uses_vgroup(ClothModifierData *clmd)
{
	return (((clmd->sim_parms->flags & CLOTH_SIMSETTINGS_FLAG_SCALING ) || 
		(clmd->sim_parms->flags & CLOTH_SIMSETTINGS_FLAG_GOAL )) && 
		((clmd->sim_parms->vgroup_mass>0) || 
		(clmd->sim_parms->vgroup_struct>0)||
		(clmd->sim_parms->vgroup_bend>0)));
}

/**
 * cloth_apply_vgroup - applies a vertex group as specified by type
 *
 **/
/* can be optimized to do all groups in one loop */
static void cloth_apply_vgroup ( ClothModifierData *clmd, DerivedMesh *dm )
{
	int i = 0;
	int j = 0;
	MDeformVert *dvert = NULL;
	Cloth *clothObj = NULL;
	int numverts;
	float goalfac = 0;
	ClothVertex *verts = NULL;

	if (!clmd || !dm) return;

	clothObj = clmd->clothObject;

	numverts = dm->getNumVerts ( dm );

	verts = clothObj->verts;
	
	if (cloth_uses_vgroup(clmd))
	{
		for ( i = 0; i < numverts; i++, verts++ )
		{	
			dvert = dm->getVertData ( dm, i, CD_MDEFORMVERT );
			if ( dvert )
			{
				for ( j = 0; j < dvert->totweight; j++ )
				{
					if (( dvert->dw[j].def_nr == (clmd->sim_parms->vgroup_mass-1)) && (clmd->sim_parms->flags & CLOTH_SIMSETTINGS_FLAG_GOAL ))
					{
						verts->goal = dvert->dw [j].weight;
						goalfac= 1.0f;
						
						/*
						// Kicking goal factor to simplify things...who uses that anyway?
						// ABS ( clmd->sim_parms->maxgoal - clmd->sim_parms->mingoal );
						*/
						
						verts->goal  = ( float ) pow ( verts->goal , 4.0f );
						if ( verts->goal >=SOFTGOALSNAP )
						{
							 verts->flags |= CLOTH_VERT_FLAG_PINNED;
						}
					}
					
					if (clmd->sim_parms->flags & CLOTH_SIMSETTINGS_FLAG_SCALING )
					{
						if( dvert->dw[j].def_nr == (clmd->sim_parms->vgroup_struct-1))
						{
							verts->struct_stiff = dvert->dw [j].weight;
							verts->shear_stiff = dvert->dw [j].weight;
						}
						
						if( dvert->dw[j].def_nr == (clmd->sim_parms->vgroup_bend-1))
						{
							verts->bend_stiff = dvert->dw [j].weight;
						}
					}
					/*
					// for later
					if( dvert->dw[j].def_nr == (clmd->sim_parms->vgroup_weight-1))
					{
						verts->mass = dvert->dw [j].weight;
					}
					*/
				}
			}
		}
	}
}

static int cloth_from_object(Object *ob, ClothModifierData *clmd, DerivedMesh *dm, float UNUSED(framenr), int first)
{
	int i = 0;
	MVert *mvert = NULL;
	ClothVertex *verts = NULL;
	float (*shapekey_rest)[3]= NULL;
	float tnull[3] = {0,0,0};
	Cloth *cloth = NULL;
	float maxdist = 0;

	// If we have a clothObject, free it. 
	if ( clmd->clothObject != NULL )
	{
		cloth_free_modifier ( clmd );
		if(G.rt > 0)
			printf("cloth_free_modifier cloth_from_object\n");
	}

	// Allocate a new cloth object.
	clmd->clothObject = MEM_callocN ( sizeof ( Cloth ), "cloth" );
	if ( clmd->clothObject )
	{
		clmd->clothObject->old_solver_type = 255;
		// clmd->clothObject->old_collision_type = 255;
		cloth = clmd->clothObject;
		clmd->clothObject->edgehash = NULL;
	}
	else if ( !clmd->clothObject )
	{
		modifier_setError ( & ( clmd->modifier ), "Out of memory on allocating clmd->clothObject." );
		return 0;
	}

	// mesh input objects need DerivedMesh
	if ( !dm )
		return 0;

	cloth_from_mesh ( clmd, dm );

	// create springs 
	clmd->clothObject->springs = NULL;
	clmd->clothObject->numsprings = -1;
	
	if( clmd->sim_parms->shapekey_rest )
		shapekey_rest = dm->getVertDataArray ( dm, CD_CLOTH_ORCO );

	mvert = dm->getVertArray ( dm );

	verts = clmd->clothObject->verts;

	// set initial values
	for ( i = 0; i < dm->getNumVerts(dm); i++, verts++ )
	{
		if(first)
		{
			copy_v3_v3( verts->x, mvert[i].co );

			mul_m4_v3( ob->obmat, verts->x );

			if( shapekey_rest ) {
				verts->xrest= shapekey_rest[i];
				mul_m4_v3( ob->obmat, verts->xrest );
			}
			else
				verts->xrest = verts->x;
		}
		
		/* no GUI interface yet */
		verts->mass = clmd->sim_parms->mass; 
		verts->impulse_count = 0;

		if ( clmd->sim_parms->flags & CLOTH_SIMSETTINGS_FLAG_GOAL )
			verts->goal= clmd->sim_parms->defgoal;
		else
			verts->goal= 0.0f;

		verts->flags = 0;
		VECCOPY ( verts->xold, verts->x );
		VECCOPY ( verts->xconst, verts->x );
		VECCOPY ( verts->txold, verts->x );
		VECCOPY ( verts->tx, verts->x );
		mul_v3_fl( verts->v, 0.0f );

		verts->impulse_count = 0;
		VECCOPY ( verts->impulse, tnull );
	}
	
	// apply / set vertex groups
	// has to be happen before springs are build!
	cloth_apply_vgroup (clmd, dm);

	if ( !cloth_build_springs ( clmd, dm ) )
	{
		cloth_free_modifier ( clmd );
		modifier_setError ( & ( clmd->modifier ), "Can't build springs." );
		printf("cloth_free_modifier cloth_build_springs\n");
		return 0;
	}
	
	for ( i = 0; i < dm->getNumVerts(dm); i++)
	{
		if((!(cloth->verts[i].flags & CLOTH_VERT_FLAG_PINNED)) && (cloth->verts[i].goal > ALMOST_ZERO))
		{
			cloth_add_spring (clmd, i, i, 0.0, CLOTH_SPRING_TYPE_GOAL);
		}
	}
	
	// init our solver
	if ( solvers [clmd->sim_parms->solver_type].init ) {
		solvers [clmd->sim_parms->solver_type].init ( ob, clmd );
	}
	
	if(!first)
		implicit_set_positions(clmd);

	clmd->clothObject->bvhtree = bvhtree_build_from_cloth ( clmd, clmd->coll_parms->epsilon );
	
	for(i = 0; i < dm->getNumVerts(dm); i++)
	{
		maxdist = MAX2(maxdist, clmd->coll_parms->selfepsilon* ( cloth->verts[i].avg_spring_len*2.0));
	}
	
	clmd->clothObject->bvhselftree = bvhselftree_build_from_cloth ( clmd, maxdist );

	return 1;
}

static void cloth_from_mesh ( ClothModifierData *clmd, DerivedMesh *dm )
{
	unsigned int numverts = dm->getNumVerts ( dm );
	unsigned int numfaces = dm->getNumFaces ( dm );
	MFace *mface = dm->getFaceArray( dm );
	unsigned int i = 0;

	/* Allocate our vertices. */
	clmd->clothObject->numverts = numverts;
	clmd->clothObject->verts = MEM_callocN ( sizeof ( ClothVertex ) * clmd->clothObject->numverts, "clothVertex" );
	if ( clmd->clothObject->verts == NULL )
	{
		cloth_free_modifier ( clmd );
		modifier_setError ( & ( clmd->modifier ), "Out of memory on allocating clmd->clothObject->verts." );
		printf("cloth_free_modifier clmd->clothObject->verts\n");
		return;
	}

	// save face information
	clmd->clothObject->numfaces = numfaces;
	clmd->clothObject->mfaces = MEM_callocN ( sizeof ( MFace ) * clmd->clothObject->numfaces, "clothMFaces" );
	if ( clmd->clothObject->mfaces == NULL )
	{
		cloth_free_modifier ( clmd );
		modifier_setError ( & ( clmd->modifier ), "Out of memory on allocating clmd->clothObject->mfaces." );
		printf("cloth_free_modifier clmd->clothObject->mfaces\n");
		return;
	}
	for ( i = 0; i < numfaces; i++ )
		memcpy ( &clmd->clothObject->mfaces[i], &mface[i], sizeof ( MFace ) );

	/* Free the springs since they can't be correct if the vertices
	* changed.
	*/
	if ( clmd->clothObject->springs != NULL )
		MEM_freeN ( clmd->clothObject->springs );

}

/***************************************************************************************
* SPRING NETWORK BUILDING IMPLEMENTATION BEGIN
***************************************************************************************/

// be carefull: implicit solver has to be resettet when using this one!
// --> only for implicit handling of this spring!
int cloth_add_spring ( ClothModifierData *clmd, unsigned int indexA, unsigned int indexB, float restlength, int spring_type)
{
	Cloth *cloth = clmd->clothObject;
	ClothSpring *spring = NULL;
	
	if(cloth)
	{
		// TODO: look if this spring is already there
		
		spring = ( ClothSpring * ) MEM_callocN ( sizeof ( ClothSpring ), "cloth spring" );
		
		if(!spring)
			return 0;
		
		spring->ij = indexA;
		spring->kl = indexB;
		spring->restlen =  restlength;
		spring->type = spring_type;
		spring->flags = 0;
		spring->stiffness = 0;
		
		cloth->numsprings++;
	
		BLI_linklist_prepend ( &cloth->springs, spring );
		
		return 1;
	}
	return 0;
}

static void cloth_free_errorsprings(Cloth *cloth, EdgeHash *UNUSED(edgehash), LinkNode **edgelist)
{
	unsigned int i = 0;
	
	if ( cloth->springs != NULL )
	{
		LinkNode *search = cloth->springs;
		while(search)
		{
			ClothSpring *spring = search->link;
						
			MEM_freeN ( spring );
			search = search->next;
		}
		BLI_linklist_free(cloth->springs, NULL);
		
		cloth->springs = NULL;
	}
	
	if(edgelist)
	{
		for ( i = 0; i < cloth->numverts; i++ )
		{
			BLI_linklist_free ( edgelist[i],NULL );
		}

		MEM_freeN ( edgelist );
	}
	
	if(cloth->edgehash)
		BLI_edgehash_free ( cloth->edgehash, NULL );
}

static int cloth_build_springs ( ClothModifierData *clmd, DerivedMesh *dm )
{
	Cloth *cloth = clmd->clothObject;
	ClothSpring *spring = NULL, *tspring = NULL, *tspring2 = NULL;
	unsigned int struct_springs = 0, shear_springs=0, bend_springs = 0;
	unsigned int i = 0;
	unsigned int numverts = (unsigned int)dm->getNumVerts ( dm );
	unsigned int numedges = (unsigned int)dm->getNumEdges ( dm );
	unsigned int numfaces = (unsigned int)dm->getNumFaces ( dm );
	MEdge *medge = dm->getEdgeArray ( dm );
	MFace *mface = dm->getFaceArray ( dm );
	int index2 = 0; // our second vertex index
	LinkNode **edgelist = NULL;
	EdgeHash *edgehash = NULL;
	LinkNode *search = NULL, *search2 = NULL;
	float temp[3];
	
	// error handling
	if ( numedges==0 )
		return 0;

	cloth->springs = NULL;

	edgelist = MEM_callocN ( sizeof ( LinkNode * ) * numverts, "cloth_edgelist_alloc" );
	
	if(!edgelist)
		return 0;
	
	for ( i = 0; i < numverts; i++ )
	{
		edgelist[i] = NULL;
	}

	if ( cloth->springs )
		MEM_freeN ( cloth->springs );

	// create spring network hash
	edgehash = BLI_edgehash_new();

	// structural springs
	for ( i = 0; i < numedges; i++ )
	{
		spring = ( ClothSpring * ) MEM_callocN ( sizeof ( ClothSpring ), "cloth spring" );

		if ( spring )
		{
			spring->ij = MIN2(medge[i].v1, medge[i].v2);
			spring->kl = MAX2(medge[i].v2, medge[i].v1);
			VECSUB ( temp, cloth->verts[spring->kl].xrest, cloth->verts[spring->ij].xrest );
			spring->restlen =  sqrt ( INPR ( temp, temp ) );
			clmd->sim_parms->avg_spring_len += spring->restlen;
			cloth->verts[spring->ij].avg_spring_len += spring->restlen;
			cloth->verts[spring->kl].avg_spring_len += spring->restlen;
			cloth->verts[spring->ij].spring_count++;
			cloth->verts[spring->kl].spring_count++;
			spring->type = CLOTH_SPRING_TYPE_STRUCTURAL;
			spring->flags = 0;
			spring->stiffness = (cloth->verts[spring->kl].struct_stiff + cloth->verts[spring->ij].struct_stiff) / 2.0;
			struct_springs++;
			
			BLI_linklist_prepend ( &cloth->springs, spring );
		}
		else
		{
			cloth_free_errorsprings(cloth, edgehash, edgelist);
			return 0;
		}
	}
	
	if(struct_springs > 0)
		clmd->sim_parms->avg_spring_len /= struct_springs;
	
	for(i = 0; i < numverts; i++)
	{
		cloth->verts[i].avg_spring_len = cloth->verts[i].avg_spring_len * 0.49 / ((float)cloth->verts[i].spring_count);
	}
	
	// shear springs
	for ( i = 0; i < numfaces; i++ )
	{
		// triangle faces already have shear springs due to structural geometry
		if ( !mface[i].v4 )
			continue; 
		
		spring = ( ClothSpring *) MEM_callocN ( sizeof ( ClothSpring ), "cloth spring" );
		
		if(!spring)
		{
			cloth_free_errorsprings(cloth, edgehash, edgelist);
			return 0;
		}

		spring->ij = MIN2(mface[i].v1, mface[i].v3);
		spring->kl = MAX2(mface[i].v3, mface[i].v1);
		VECSUB ( temp, cloth->verts[spring->kl].xrest, cloth->verts[spring->ij].xrest );
		spring->restlen =  sqrt ( INPR ( temp, temp ) );
		spring->type = CLOTH_SPRING_TYPE_SHEAR;
		spring->stiffness = (cloth->verts[spring->kl].shear_stiff + cloth->verts[spring->ij].shear_stiff) / 2.0;

		BLI_linklist_append ( &edgelist[spring->ij], spring );
		BLI_linklist_append ( &edgelist[spring->kl], spring );
		shear_springs++;

		BLI_linklist_prepend ( &cloth->springs, spring );

		
		// if ( mface[i].v4 ) --> Quad face
		spring = ( ClothSpring * ) MEM_callocN ( sizeof ( ClothSpring ), "cloth spring" );
		
		if(!spring)
		{
			cloth_free_errorsprings(cloth, edgehash, edgelist);
			return 0;
		}

		spring->ij = MIN2(mface[i].v2, mface[i].v4);
		spring->kl = MAX2(mface[i].v4, mface[i].v2);
		VECSUB ( temp, cloth->verts[spring->kl].xrest, cloth->verts[spring->ij].xrest );
		spring->restlen =  sqrt ( INPR ( temp, temp ) );
		spring->type = CLOTH_SPRING_TYPE_SHEAR;
		spring->stiffness = (cloth->verts[spring->kl].shear_stiff + cloth->verts[spring->ij].shear_stiff) / 2.0;

		BLI_linklist_append ( &edgelist[spring->ij], spring );
		BLI_linklist_append ( &edgelist[spring->kl], spring );
		shear_springs++;

		BLI_linklist_prepend ( &cloth->springs, spring );
	}
	
	if(numfaces) {
		// bending springs
		search2 = cloth->springs;
		for ( i = struct_springs; i < struct_springs+shear_springs; i++ )
		{
			if ( !search2 )
				break;

			tspring2 = search2->link;
			search = edgelist[tspring2->kl];
			while ( search )
			{
				tspring = search->link;
				index2 = ( ( tspring->ij==tspring2->kl ) ? ( tspring->kl ) : ( tspring->ij ) );
				
				// check for existing spring
				// check also if startpoint is equal to endpoint
				if ( !BLI_edgehash_haskey ( edgehash, MIN2(tspring2->ij, index2), MAX2(tspring2->ij, index2) )
				&& ( index2!=tspring2->ij ) )
				{
					spring = ( ClothSpring * ) MEM_callocN ( sizeof ( ClothSpring ), "cloth spring" );
					
					if(!spring)
					{
						cloth_free_errorsprings(cloth, edgehash, edgelist);
						return 0;
					}

					spring->ij = MIN2(tspring2->ij, index2);
					spring->kl = MAX2(tspring2->ij, index2);
					VECSUB ( temp, cloth->verts[spring->kl].xrest, cloth->verts[spring->ij].xrest );
					spring->restlen =  sqrt ( INPR ( temp, temp ) );
					spring->type = CLOTH_SPRING_TYPE_BENDING;
					spring->stiffness = (cloth->verts[spring->kl].bend_stiff + cloth->verts[spring->ij].bend_stiff) / 2.0;
					BLI_edgehash_insert ( edgehash, spring->ij, spring->kl, NULL );
					bend_springs++;

					BLI_linklist_prepend ( &cloth->springs, spring );
				}
				search = search->next;
			}
			search2 = search2->next;
		}
	}
	else if(struct_springs > 2) {
		/* bending springs for hair strands */
		/* The current algorightm only goes through the edges in order of the mesh edges list	*/
		/* and makes springs between the outer vert of edges sharing a vertice. This works just */
		/* fine for hair, but not for user generated string meshes. This could/should be later	*/
		/* extended to work with non-ordered edges so that it can be used for general "rope		*/
		/* dynamics" without the need for the vertices or edges to be ordered through the length*/
		/* of the strands. -jahka */
		search = cloth->springs;
		search2 = search->next;
		while(search && search2)
		{
			tspring = search->link;
			tspring2 = search2->link;

			if(tspring->ij == tspring2->kl) {
				spring = ( ClothSpring * ) MEM_callocN ( sizeof ( ClothSpring ), "cloth spring" );
				
				if(!spring)
				{
					cloth_free_errorsprings(cloth, edgehash, edgelist);
					return 0;
				}

				spring->ij = tspring2->ij;
				spring->kl = tspring->kl;
				VECSUB ( temp, cloth->verts[spring->kl].xrest, cloth->verts[spring->ij].xrest );
				spring->restlen =  sqrt ( INPR ( temp, temp ) );
				spring->type = CLOTH_SPRING_TYPE_BENDING;
				spring->stiffness = (cloth->verts[spring->kl].bend_stiff + cloth->verts[spring->ij].bend_stiff) / 2.0;
				bend_springs++;

				BLI_linklist_prepend ( &cloth->springs, spring );
			}
			
			search = search->next;
			search2 = search2->next;
		}
	}
	
	/* insert other near springs in edgehash AFTER bending springs are calculated (for selfcolls) */
	for ( i = 0; i < numedges; i++ ) // struct springs
		BLI_edgehash_insert ( edgehash, MIN2(medge[i].v1, medge[i].v2), MAX2(medge[i].v2, medge[i].v1), NULL );
	
	for ( i = 0; i < numfaces; i++ ) // edge springs
	{
		if(mface[i].v4)
		{
			BLI_edgehash_insert ( edgehash, MIN2(mface[i].v1, mface[i].v3), MAX2(mface[i].v3, mface[i].v1), NULL );
			
			BLI_edgehash_insert ( edgehash, MIN2(mface[i].v2, mface[i].v4), MAX2(mface[i].v2, mface[i].v4), NULL );
		}
	}
	
	
	cloth->numsprings = struct_springs + shear_springs + bend_springs;
	
	if ( edgelist )
	{
		for ( i = 0; i < numverts; i++ )
		{
			BLI_linklist_free ( edgelist[i],NULL );
		}
	
		MEM_freeN ( edgelist );
	}
	
	cloth->edgehash = edgehash;
	
	if(G.rt>0)
		printf("avg_len: %f\n",clmd->sim_parms->avg_spring_len);

	return 1;

} /* cloth_build_springs */
/***************************************************************************************
* SPRING NETWORK BUILDING IMPLEMENTATION END
***************************************************************************************/

