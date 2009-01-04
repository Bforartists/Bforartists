/**
 * BKE_shrinkwrap.h
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
 * The Original Code is Copyright (C) Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef BKE_SHRINKWRAP_H
#define BKE_SHRINKWRAP_H

/* mesh util */

//TODO: move this somewhere else
#include "BKE_customdata.h"
struct DerivedMesh;
struct Object;

/* SpaceTransform stuff */
/*
 * TODO: move this somewhere else
 *
 * this structs encapsulates all needed data to convert between 2 coordinate spaces
 * (where conversion can be represented by a matrix multiplication)
 *
 * This is used to reduce the number of arguments to pass to functions that need to perform
 * this kind of operation and make it easier for the coder, as he/she doenst needs to recode
 * the matrix calculation.
 *
 * A SpaceTransform is initialized using:
 *   space_transform_setup( &data,  ob1, ob2 )
 *
 * After that the following calls can be used:
 *   space_transform_apply (&data, co); //converts a coordinate in ob1 coords space to the corresponding ob2 coords
 *   space_transform_invert(&data, co); //converts a coordinate in ob2 coords space to the corresponding ob1 coords
 *
 *	//Same Concept as space_transform_apply and space_transform_invert, but no is normalized after conversion
 *   space_transform_apply_normal (&data, &no);
 *   space_transform_invert_normal(&data, &no);
 *
 */


typedef struct SpaceTransform
{
	float local2target[4][4];
	float target2local[4][4];

} SpaceTransform;

void space_transform_from_matrixs(struct SpaceTransform *data, float local[4][4], float target[4][4]);
void space_transform_apply(const struct SpaceTransform *data, float *co);
void space_transform_invert(const struct SpaceTransform *data, float *co);

#define space_transform_setup(data, local, target) space_transform_from_matrixs(data, (local)->obmat, (target)->obmat)

/* Shrinkwrap stuff */
#include "BKE_bvhutils.h"

/*
 * Shrinkwrap is composed by a set of functions and options that define the type of shrink.
 *
 * 3 modes are available:
 *    - Nearest vertex
 *	  - Nearest surface
 *    - Normal projection
 *
 * ShrinkwrapCalcData encapsulates all needed data for shrinkwrap functions.
 * (So that you dont have to pass an enormous ammount of arguments to functions)
 */

struct Object;
struct Scene;
struct DerivedMesh;
struct ShrinkwrapModifierData;
struct MDeformVert;
struct BVHTree;


typedef struct ShrinkwrapCalcData
{
	ShrinkwrapModifierData *smd;	//shrinkwrap modifier data

	struct Object *ob;				//object we are applying shrinkwrap to
	struct DerivedMesh *original;	//mesh before shrinkwrap

	float (*vertexCos)[3];			//vertexs being shrinkwraped
	int numVerts;

	struct MDeformVert* dvert;			//Pointer to mdeform array
	int vgroup;						//Vertex group num

	struct DerivedMesh *target;		//mesh we are shrinking to	
	SpaceTransform local2target;	//transform to move bettwem local and target space

	float keepDist;					//Distance to kept from target (units are in local space)

} ShrinkwrapCalcData;

void shrinkwrapModifier_deform(struct ShrinkwrapModifierData *smd, struct Scene *scene, struct Object *ob, struct DerivedMesh *dm, float (*vertexCos)[3], int numVerts);

/*
 * NULL initializers to local data
 */
#define NULL_ShrinkwrapCalcData	{NULL, }
#define NULL_BVHTreeFromMesh	{NULL, }
#define NULL_BVHTreeRayHit		{NULL, }
#define NULL_BVHTreeNearest		{0, }


#endif

