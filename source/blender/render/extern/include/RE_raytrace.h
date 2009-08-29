/**
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
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): André Pinto.
 *
 * ***** END GPL LICENSE BLOCK *****
 * RE_raytrace.h: ray tracing api, can be used independently from the renderer. 
 */

#ifndef RE_RAYTRACE_H
#define RE_RAYTRACE_H

#ifdef __cplusplus
extern "C" {
#endif


#define RE_RAY_LCTS_MAX_SIZE	256
#define RT_USE_LAST_HIT			/* last shadow hit is reused before raycasting on whole tree */
//#define RT_USE_HINT			/* last hit object is reused before raycasting on whole tree */

#define RE_RAYCOUNTER


#ifdef RE_RAYCOUNTER

typedef struct RayCounter RayCounter;
struct RayCounter
{

	struct
	{
		unsigned long long test, hit;
		
	} faces, bb, raycast, raytrace_hint, rayshadow_last_hit;
};

/* #define RE_RC_INIT(isec, shi) (isec).count = re_rc_counter+(shi).thread */
#define RE_RC_INIT(isec, shi) (isec).raycounter = &((shi).raycounter)
void RE_RC_INFO (RayCounter *rc);
void RE_RC_MERGE(RayCounter *rc, RayCounter *tmp);
#define RE_RC_COUNT(var) (var)++

extern RayCounter re_rc_counter[];

#else

#define RE_RC_INIT(isec,shi)
#define RE_RC_INFO(rc)
#define RE_RC_MERGE(dest,src)
#define	RE_RC_COUNT(var)
	
#endif


/* Internals about raycasting structures can be found on intern/raytree.h */
typedef struct RayObject RayObject;
typedef struct Isect Isect;
typedef struct RayHint RayHint;
typedef struct RayTraceHint RayTraceHint;

struct DerivedMesh;
struct Mesh;

int  RE_rayobject_raycast(RayObject *r, Isect *i);
void RE_rayobject_add    (RayObject *r, RayObject *);
void RE_rayobject_done(RayObject *r);
void RE_rayobject_free(RayObject *r);

/* initializes an hint for optiming raycast where it is know that a ray will pass by the given BB often the origin point */
void RE_rayobject_hint_bb(RayObject *r, RayHint *hint, float *min, float *max);

/* initializes an hint for optiming raycast where it is know that a ray will be contained inside the given cone*/
/* void RE_rayobject_hint_cone(RayObject *r, RayHint *hint, float *); */

/* RayObject constructors */

RayObject* RE_rayobject_octree_create(int ocres, int size);
RayObject* RE_rayobject_instance_create(RayObject *target, float transform[][4], void *ob, void *target_ob);

RayObject* RE_rayobject_blibvh_create(int size);	/* BLI_kdopbvh.c   */
RayObject* RE_rayobject_bvh_create(int size);		/* raytrace/rayobject_bvh.c */
RayObject* RE_rayobject_vbvh_create(int size);		/* raytrace/rayobject_vbvh.c */
RayObject* RE_rayobject_qbvh_create(int size);		/* raytrace/rayobject_vbvh.c */
RayObject* RE_rayobject_svbvh_create(int size);		/* raytrace/rayobject_vbvh.c */
RayObject* RE_rayobject_bih_create(int size);		/* rayobject_bih.c */

typedef struct LCTSHint LCTSHint;
struct LCTSHint
{
	int size;
	RayObject *stack[RE_RAY_LCTS_MAX_SIZE];
};

struct RayHint
{
	union
	{
		LCTSHint lcts;
	} data;
};


/* Ray Intersection */
struct Isect
{
	float start[3];
	float vec[3];
	float labda;

	/* length of vec, configured by RE_rayobject_raycast */
	int   bv_index[6];
	float idot_axis[3];
	float dist;

/*	float end[3];			 - not used */

	float u, v;
	
	struct
	{
		void *ob;
		void *face;
	}
	hit, orig;
	
	RayObject *last_hit;	/* last hit optimization */

#ifdef RT_USE_HINT
	RayTraceHint *hint, *hit_hint;
#endif
	
	short isect;			/* which half of quad */
	short mode;				/* RE_RAY_SHADOW, RE_RAY_MIRROR, RE_RAY_SHADOW_TRA */
	int lay;				/* -1 default, set for layer lamps */
	
	int skip;				/* RE_SKIP_CULLFACE */

	float col[4];			/* RGBA for shadow_tra */

	void *userdata;
	
	RayHint *hint;
	
#ifdef RE_RAYCOUNTER
	RayCounter *raycounter;
#endif
	
};

/* ray types */
#define RE_RAY_SHADOW 0
#define RE_RAY_MIRROR 1
#define RE_RAY_SHADOW_TRA 2

/* skip options */
#define RE_SKIP_CULLFACE		(1 << 0)

/* if using this flag then *face should be a pointer to a VlakRen */
#define RE_SKIP_VLR_NEIGHBOUR	(1 << 1)

/* TODO use: FLT_MAX? */
#define RE_RAYTRACE_MAXDIST	1e33

#ifdef __cplusplus
}
#endif


#endif /*__RE_RAYTRACE_H__*/
