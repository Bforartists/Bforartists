/**
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
 * The Original Code is Copyright (C) 2006 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): André Pinto
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef BKE_BVHUTILS_H
#define BKE_BVHUTILS_H

#include "BLI_kdopbvh.h"

/*
 * This header encapsulates necessary code to buld a BVH
 */

struct DerivedMesh;
struct MVert;
struct MFace;

/*
 * struct that kepts basic information about a BVHTree build from a mesh
 */
typedef struct BVHTreeFromMesh
{
	struct BVHTree *tree;

	/* default callbacks to bvh nearest and raycast */
	BVHTree_NearestPointCallback nearest_callback;
	BVHTree_RayCastCallback      raycast_callback;

	/* Mesh represented on this BVHTree */
	struct DerivedMesh *mesh; 

	/* Vertex array, so that callbacks have instante access to data */
	struct MVert *vert;
	struct MFace *face;

	/* radius for raycast */
	float sphere_radius;

} BVHTreeFromMesh;

/*
 * Builds a bvh tree where nodes are the vertexs of the given mesh.
 * Configures BVHTreeFromMesh.
 *
 * The tree is build in mesh space coordinates, this means special care must be made on queries
 * so that the coordinates and rays are first translated on the mesh local coordinates.
 * Reason for this is that later bvh_from_mesh_* might use a cache system and so it becames possible to reuse
 * a BVHTree.
 * 
 * free_bvhtree_from_mesh should be called when the tree is no longer needed.
 */
void bvhtree_from_mesh_verts(struct BVHTreeFromMesh *data, struct DerivedMesh *mesh, float epsilon, int tree_type, int axis);

/*
 * Builds a bvh tree where nodes are the faces of the given mesh.
 * Configures BVHTreeFromMesh.
 *
 * The tree is build in mesh space coordinates, this means special care must be made on queries
 * so that the coordinates and rays are first translated on the mesh local coordinates.
 * Reason for this is that later bvh_from_mesh_* might use a cache system and so it becames possible to reuse
 * a BVHTree.
 * 
 * free_bvhtree_from_mesh should be called when the tree is no longer needed.
 */
void bvhtree_from_mesh_faces(struct BVHTreeFromMesh *data, struct DerivedMesh *mesh, float epsilon, int tree_type, int axis);

/*
 * Frees data allocated by a call to bvhtree_from_mesh_*.
 */
void free_bvhtree_from_mesh(struct BVHTreeFromMesh *data);

#endif

