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


/* Internals about raycasting structures can be found on intern/raytree.h */
typedef struct RayObject RayObject;
typedef struct Isect Isect;
struct DerivedMesh;
struct Mesh;

int  RayObject_raycast(RayObject *r, Isect *i);
void RayObject_add    (RayObject *r, RayObject *);
void RayObject_done(RayObject *r);
void RayObject_free(RayObject *r);

/* RayObject constructors */
RayObject* RayObject_octree_create(int ocres, int size);

//RayObject* RayObject_derivedmesh_create(struct DerivedMesh*, void *ob);
RayObject* RayObject_mesh_create(struct Mesh*, void *ob);

/* Ray Intersection */
struct Isect
{
	float start[3];
	float vec[3];
/*	float end[3];			 - not used */

	float labda, u, v;
	
	struct
	{
		void *ob;
		void *face;
/*		RayObject *obj; */
	}
	hit, orig;
	
	RayObject *last_hit;	/* last hit optimization */
	
	short isect;			/* which half of quad */
	short mode;				/* RE_RAY_SHADOW, RE_RAY_MIRROR, RE_RAY_SHADOW_TRA */
	int lay;				/* -1 default, set for layer lamps */
	
	int skip;				/* RE_SKIP_CULLFACE */

	float col[4];			/* RGBA for shadow_tra */
	
	void *userdata;
};

/* ray types */
#define RE_RAY_SHADOW 0
#define RE_RAY_MIRROR 1
#define RE_RAY_SHADOW_TRA 2

/* skip options */
#define RE_SKIP_CULLFACE	1

/* TODO use: FLT_MAX? */
#define RE_RAYTRACE_MAXDIST	1e33


#endif /*__RE_RAYTRACE_H__*/
