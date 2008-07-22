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

/* bitset stuff */
//TODO: should move this to other generic lib files?
typedef char* BitSet;
#define bitset_memsize(size)		(sizeof(char)*((size+7)>>3))

#define bitset_new(size,name)		((BitSet)MEM_callocN( bitset_memsize(size) , name))
#define bitset_free(set)			(MEM_freeN((void*)set))

#define bitset_get(set,index)	((set)[(index)>>3] & (1 << ((index)&0x7)))
#define bitset_set(set,index)	((set)[(index)>>3] |= (1 << ((index)&0x7)))
#define bitset_unset(set,index)	((set)[(index)>>3] &= ~(1 << ((index)&0x7)))


/* SpaceTransform stuff */
//TODO: should move to other generic space?
struct Object;

typedef struct SpaceTransform
{
	float local2target[4][4];
	float target2local[4][4];

} SpaceTransform;

void space_transform_setup(SpaceTransform *data, struct Object *local, struct Object *target);

void space_transform_apply (const SpaceTransform *data, float *co);
void space_transform_invert(const SpaceTransform *data, float *co);

void space_transform_apply_normal (const SpaceTransform *data, float *co);
void space_transform_invert_normal(const SpaceTransform *data, float *co);

/* BVH from mesh */
#include "BLI_kdopbvh.h"

struct DerivedMesh;
struct MVert;
struct MFace;

//struct that kepts basic information about a BVHTree build from a mesh
typedef struct BVHTreeFromMesh
{
	struct BVHTree *tree;

	//Callbacks
	BVHTree_NearestPointCallback nearest_callback;
	BVHTree_RayCastCallback      raycast_callback;
	
	//Mesh represented on this BVH
	struct DerivedMesh *mesh;
	struct MVert *vert;
	struct MFace *face;

	//radius for sphere cast
	float sphere_radius;

} BVHTreeFromMesh;

// Builds a bvh tree where nodes are the vertexs of the given mesh. And configures BVHMesh if one given.
struct BVHTree* bvhtree_from_mesh_verts(struct BVHTreeFromMesh *data, struct DerivedMesh *mesh, float epsilon, int tree_type, int axis);

// Builds a bvh tree where nodes are the faces of the given mesh. And configures BVHMesh if one is given.
struct BVHTree* bvhtree_from_mesh_faces(struct BVHTreeFromMesh *data, struct DerivedMesh *mesh, float epsilon, int tree_type, int axis);




/* Shrinkwrap stuff */
struct Object;
struct DerivedMesh;
struct ShrinkwrapModifierData;
struct BVHTree;



typedef struct ShrinkwrapCalcData
{
	ShrinkwrapModifierData *smd;	//shrinkwrap modifier data

	struct Object *ob;				//object we are applying shrinkwrap to
	struct DerivedMesh *original;	//mesh before shrinkwrap (TODO clean this variable.. we don't really need it)
	struct BVHTree *original_tree;	//BVHTree build with the original mesh (to be used on kept volume)
	struct BVHMeshCallbackUserdata *callback;

	struct DerivedMesh *final;		//initially a copy of original mesh.. mesh thats going to be shrinkwrapped

	struct DerivedMesh *target;		//mesh we are shrinking to
	
	SpaceTransform local2target;

	float keptDist;					//Distance to kept from target (units are in local space)
	//float *weights;				//weights of vertexs
	BitSet moved;					//BitSet indicating if vertex has moved

} ShrinkwrapCalcData;

void shrinkwrap_calc_nearest_vertex(ShrinkwrapCalcData *data);
void shrinkwrap_calc_normal_projection(ShrinkwrapCalcData *data);
void shrinkwrap_calc_nearest_surface_point(ShrinkwrapCalcData *data);

struct DerivedMesh *shrinkwrapModifier_do(struct ShrinkwrapModifierData *smd, struct Object *ob, struct DerivedMesh *dm, int useRenderParams, int isFinalCalc);


#endif


