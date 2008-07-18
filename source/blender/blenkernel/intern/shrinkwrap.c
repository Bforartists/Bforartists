/**
 * shrinkwrap.c
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
 * Contributor(s): André Pinto
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#include <string.h>
#include <float.h>
#include <math.h>
#include <memory.h>
#include <stdio.h>
#include <time.h>

#include "DNA_object_types.h"
#include "DNA_modifier_types.h"
#include "DNA_meshdata_types.h"

#include "BKE_shrinkwrap.h"
#include "BKE_DerivedMesh.h"
#include "BKE_utildefines.h"
#include "BKE_deform.h"
#include "BKE_cdderivedmesh.h"
#include "BKE_global.h"

#include "BLI_arithb.h"
#include "BLI_kdtree.h"
#include "BLI_kdopbvh.h"

#include "RE_raytrace.h"
#include "MEM_guardedalloc.h"


/* Util macros */
#define TO_STR(a)	#a
#define JOIN(a,b)	a##b

#define OUT_OF_MEMORY()	((void)printf("Shrinkwrap: Out of memory\n"))

/* Benchmark macros */
#if 1

#define BENCH(a)	\
	do {			\
		clock_t _clock_init = clock();	\
		(a);							\
		printf("%s: %fms\n", #a, (float)(clock()-_clock_init)*1000/CLOCKS_PER_SEC);	\
	} while(0)

#define BENCH_VAR(name)		clock_t JOIN(_bench_step,name) = 0, JOIN(_bench_total,name) = 0
#define BENCH_BEGIN(name)	JOIN(_bench_step, name) = clock()
#define BENCH_END(name)		JOIN(_bench_total,name) += clock() - JOIN(_bench_step,name)
#define BENCH_RESET(name)	JOIN(_bench_total, name) = 0
#define BENCH_REPORT(name)	printf("%s: %fms\n", TO_STR(name), JOIN(_bench_total,name)*1000.0f/CLOCKS_PER_SEC)

#else

#define BENCH(a)	(a)
#define BENCH_VAR(name)
#define BENCH_BEGIN(name)
#define BENCH_END(name)
#define BENCH_RESET(name)
#define BENCH_REPORT(name)

#endif

typedef void ( *Shrinkwrap_ForeachVertexCallback) (DerivedMesh *target, float *co, float *normal);

static float nearest_point_in_tri_surface(const float *point, const float *v0, const float *v1, const float *v2, float *nearest);
static float ray_intersect_plane(const float *point, const float *dir, const float *plane_point, const float *plane_normal);


/* ray - triangle */
#define ISECT_EPSILON 1e-6
static float ray_tri_intersection(const BVHTreeRay *ray, const float m_dist, const float *v0, const float *v1, const float *v2)
{
	float dist;

	if(RayIntersectsTriangle(ray->origin, ray->direction, v0, v1, v2, &dist, NULL))
		return dist;

	return FLT_MAX;
}

static float sphereray_tri_intersection(const BVHTreeRay *ray, float radius, const float m_dist, const float *v0, const float *v1, const float *v2)
{
	
	float idist;
	float p1[3];
	float plane_normal[3], hit_point[3];

	CalcNormFloat((float*)v0, (float*)v1, (float*)v2, plane_normal);

	VECADDFAC( p1, ray->origin, ray->direction, m_dist);
	if(SweepingSphereIntersectsTriangleUV(ray->origin, p1, radius, v0, v1, v2, &idist, &hit_point))
	{
		return idist * m_dist;
	}

	return FLT_MAX;
}

/* Space transform */
void space_transform_setup(SpaceTransform *data, struct Object *local, struct Object *target)
{
	Mat4Invert(target->imat, target->obmat); //Invserse might be outdated
	Mat4MulSerie(data->local2target, target->imat, local->obmat, 0, 0, 0, 0, 0, 0);
	Mat4Invert(data->target2local, data->local2target);
}

void space_transform_apply(/* const */ SpaceTransform *data, float *co)
{
	VecMat4MulVecfl(co, data->local2target, co);
//	Mat4Mul3Vecfl(data->local2target, co);
}

void space_transform_invert(/* const */SpaceTransform *data, float *co)
{
	VecMat4MulVecfl(co, data->target2local, co);
//	Mat4Mul3Vecfl(data->target2local, co);
}

void space_transform_apply_normal(/* const */ SpaceTransform *data, float *no)
{
	Mat4Mul3Vecfl(data->local2target, no);
	Normalize(no); // TODO: could we just determine de scale value from the matrix?
}

void space_transform_invert_normal(/* const */ SpaceTransform *data, float *no)
{
	Mat4Mul3Vecfl(data->target2local, no);
	Normalize(no); // TODO: could we just determine de scale value from the matrix?
}


/*
 * BVH tree from mesh vertices
 */
typedef struct BVHMeshCallbackUserdata
{
	//Mesh represented on this BVH
	DerivedMesh *mesh;
	MVert *vert;
	MFace *face;

	//radius for sphere cast
	float sphere_radius;

} BVHMeshCallbackUserdata;


static void bvhtree_meshcallbackdata_init(BVHMeshCallbackUserdata *data, DerivedMesh *mesh, float cast_radius)
{
	data->mesh = mesh;
	data->vert = mesh->getVertDataArray(mesh, CD_MVERT);
	data->face = mesh->getFaceDataArray(mesh, CD_MFACE);
	data->sphere_radius = cast_radius;
}

/*
 * Builds a bvh tree.. where nodes are the vertexs of the given mesh
 */
static BVHTree* bvhtree_from_mesh_verts(DerivedMesh *mesh, float epsilon, int tree_type, int axis)
{
	int i;
	int numVerts= mesh->getNumVerts(mesh);
	MVert *vert	= mesh->getVertDataArray(mesh, CD_MVERT);

	BVHTree *tree = BLI_bvhtree_new(numVerts, epsilon, tree_type, axis);
	if(tree != NULL)
	{
		for(i = 0; i < numVerts; i++)
			BLI_bvhtree_insert(tree, i, vert[i].co, 1);

		BLI_bvhtree_balance(tree);
	}

	return tree;
}

/*
 * Builds a bvh tree.. where nodes are the faces of the given mesh. Quads are splitted in 2 triangles
 */
static BVHTree* bvhtree_from_mesh_tri(DerivedMesh *mesh, float epsilon, int tree_type, int axis)
{
	int i;
	int numFaces= mesh->getNumFaces(mesh), totFaces;
	MVert *vert	= mesh->getVertDataArray(mesh, CD_MVERT);
	MFace *face = mesh->getFaceDataArray(mesh, CD_MFACE);
	BVHTree *tree= NULL;

	/* Count needed faces */
	for(totFaces=numFaces, i=0; i<numFaces; i++)
		if(face[i].v4) totFaces++;

	/* Create a bvh-tree of the given target */
	tree = BLI_bvhtree_new(totFaces, epsilon, tree_type, axis);
	if(tree != NULL)
	{
		for(i = 0; i < numFaces; i++)
		{
			float co[3][3];

			VECCOPY(co[0], vert[ face[i].v1 ].co);
			VECCOPY(co[1], vert[ face[i].v2 ].co);
			VECCOPY(co[2], vert[ face[i].v3 ].co);
			BLI_bvhtree_insert(tree, 2*i, co[0], 3);
			if(face[i].v4)
			{
				/* second face is v1,v3,v4 */
				VECCOPY(co[1], vert[ face[i].v3 ].co);
				VECCOPY(co[2], vert[ face[i].v4 ].co);
				BLI_bvhtree_insert(tree, 2*i+1, co[0], 3);
			}
		}

		BLI_bvhtree_balance(tree);
	}

	return tree;
}

/*
 * Builds a bvh tree.. where nodes are the faces of the given mesh.
 */
static BVHTree* bvhtree_from_mesh_faces(DerivedMesh *mesh, float epsilon, int tree_type, int axis)
{
	int i;
	int numFaces= mesh->getNumFaces(mesh);
	MVert *vert	= mesh->getVertDataArray(mesh, CD_MVERT);
	MFace *face = mesh->getFaceDataArray(mesh, CD_MFACE);
	BVHTree *tree= NULL;

	/* Count needed faces */

	/* Create a bvh-tree of the given target */
	tree = BLI_bvhtree_new(numFaces, epsilon, tree_type, axis);
	if(tree != NULL)
	{
		for(i = 0; i < numFaces; i++)
		{
			float co[4][3];

			VECCOPY(co[0], vert[ face[i].v1 ].co);
			VECCOPY(co[1], vert[ face[i].v2 ].co);
			VECCOPY(co[2], vert[ face[i].v3 ].co);
			if(face[i].v4)
				VECCOPY(co[3], vert[ face[i].v4 ].co);

			BLI_bvhtree_insert(tree, i, co[0], face[i].v4 ? 4 : 3);
		}

		BLI_bvhtree_balance(tree);
	}

	return tree;
}

/*
 * Loads the coordinates of the requested tri
 */
static void bvhtree_from_mesh_get_tri(BVHMeshCallbackUserdata* userdata, int index, float **v0, float **v1, float **v2)
{
	const BVHMeshCallbackUserdata *data = (BVHMeshCallbackUserdata*) userdata;
	MVert *vert	= data->vert;
	MFace *face = data->face + index / 2;

	if(index & 1)
		*v0 = vert[ face->v1 ].co, *v1 = vert[ face->v3 ].co, *v2 = vert[ face->v4 ].co;
	else
		*v0 = vert[ face->v1 ].co, *v1 = vert[ face->v2 ].co, *v2 = vert[ face->v3 ].co;
}

/*
 * Callback to bvh tree nearest point. The tree must bust have been built using bvhtree_from_mesh_tri.
 * userdata must be a BVHMeshCallbackUserdata built from the same mesh as the tree.
 */
static float mesh_tri_nearest_point(void *userdata, int index, const float *co, float *nearest)
{
	float *t0, *t1, *t2;

	bvhtree_from_mesh_get_tri( (BVHMeshCallbackUserdata*)userdata, index, &t0, &t1, &t2);
	return nearest_point_in_tri_surface(co,t0, t1, t2, nearest);
}


/*
 * Callback to bvh tree raycast. The tree must bust have been built using bvhtree_from_mesh_tri.
 * userdata must be a BVHMeshCallbackUserdata built from the same mesh as the tree.
 */
static float mesh_tri_spherecast(void *userdata, int index, const BVHTreeRay *ray, BVHTreeRayHit *hit)
{
	float dist;
	float *t0, *t1, *t2;

	bvhtree_from_mesh_get_tri( (BVHMeshCallbackUserdata*)userdata, index, &t0, &t1, &t2);

	if(((BVHMeshCallbackUserdata*)userdata)->sphere_radius == 0.0f)
		dist = ray_tri_intersection(ray, hit->dist, t0, t1, t2);
	else
		dist = sphereray_tri_intersection(ray, ((BVHMeshCallbackUserdata*)userdata)->sphere_radius, hit->dist, t0, t1, t2);

	if(dist >= 0 && dist < hit->dist)
	{
		hit->index = index;
		hit->dist = dist;
		VECADDFAC(hit->co, ray->origin, ray->direction, dist);
	}
	return dist;
}

/*
 * Callback to bvh tree raycast. The tree must bust have been built using bvhtree_from_mesh_faces.
 * userdata must be a BVHMeshCallbackUserdata built from the same mesh as the tree.
 */
static float mesh_faces_spherecast(void *userdata, int index, const BVHTreeRay *ray, BVHTreeRayHit *hit)
{
	const BVHMeshCallbackUserdata *data = (BVHMeshCallbackUserdata*) userdata;
	MVert *vert	= data->vert;
	MFace *face = data->face + index;

	float *t0, *t1, *t2, *t3;
	t0 = vert[ face->v1 ].co;
	t1 = vert[ face->v2 ].co;
	t2 = vert[ face->v3 ].co;
	t3 = face->v4 ? vert[ face->v4].co : NULL;

	
	do
	{	
		float dist;
		if(data->sphere_radius == 0.0f)
			dist = ray_tri_intersection(ray, hit->dist, t0, t1, t2);
		else
			dist = sphereray_tri_intersection(ray, data->sphere_radius, hit->dist, t0, t1, t2);

		if(dist >= 0 && dist < hit->dist)
		{
			hit->index = index;
			hit->dist = dist;
			VECADDFAC(hit->co, ray->origin, ray->direction, dist);

			CalcNormFloat(t0, t1, t2, hit->no);
		}

		t1 = t2;
		t2 = t3;
		t3 = NULL;

	} while(t2);

	return hit->dist;
}

/*
 * Raytree from mesh
 */
static MVert *raytree_from_mesh_verts = NULL;
static MFace *raytree_from_mesh_faces = NULL;

static int raytree_check_always(Isect *is, int ob, RayFace *face)
{
	return TRUE;
}

static void raytree_from_mesh_get_coords(RayFace *face, float **v1, float **v2, float **v3, float **v4)
{
	MFace *mface= raytree_from_mesh_faces + (int)face/2 - 1 ;

	if(face == (RayFace*)(-1))
	{
		*v1 = NULL;
		*v2 = NULL;
		*v3 = NULL;
		*v4 = NULL;
		return;
	}

	//Nasty quad splitting
	if(((int)face) & 1)	// we want the 2 triangle of the quad
	{
		*v1= raytree_from_mesh_verts[mface->v1].co;
		*v2= raytree_from_mesh_verts[mface->v3].co;
		*v3= raytree_from_mesh_verts[mface->v4].co;
		*v4= NULL;
	}
	else
	{
		*v1= raytree_from_mesh_verts[mface->v1].co;
		*v2= raytree_from_mesh_verts[mface->v2].co;
		*v3= raytree_from_mesh_verts[mface->v3].co;
		*v4= NULL;
	}
}

/*
 * Creates a raytree from the given mesh
 * No copy of the mesh is done, so it must exist and remain
 * imutable as long the tree is intended to be used
 *
 * No more than 1 raytree can exist.. since this code uses a static variable
 * to pass data to raytree_from_mesh_get_coords
 */
static RayTree* raytree_create_from_mesh(DerivedMesh *mesh)
{
	int i;
	float min[3], max[3];

	RayTree*tree= NULL;

	int numFaces= mesh->getNumFaces(mesh);
	MFace *face = mesh->getFaceDataArray(mesh, CD_MFACE);
	int numVerts= mesh->getNumVerts(mesh);

	//Initialize static vars
	raytree_from_mesh_verts = mesh->getVertDataArray(mesh, CD_MVERT);
	raytree_from_mesh_faces = face;


	//calculate bounding box
	INIT_MINMAX(min, max);

	for(i=0; i<numVerts; i++)
		DO_MINMAX(raytree_from_mesh_verts[i].co, min, max);
	
	tree = RE_ray_tree_create(64, numFaces, min, max, raytree_from_mesh_get_coords, raytree_check_always, NULL, NULL);
	if(tree == NULL)
		return NULL;

	//Add faces to the RayTree (RayTree uses face=0, with some special value to setup things)
	for(i=1; i<=numFaces; i++)
	{
		RE_ray_tree_add_face(tree, 0, (RayFace*)(i*2) );

		 //Theres some nasty thing with non-coplanar quads (that I can't find the issue)
		 //so we split quads (an odd numbered face represents the second triangle of the quad)
		if(face[i-1].v4)
			RE_ray_tree_add_face(tree, 0, (RayFace*)(i*2+1));
	}

	RE_ray_tree_done(tree);

	return tree;
}

static void free_raytree_from_mesh(RayTree *tree)
{
	raytree_from_mesh_verts = NULL;
	RE_ray_tree_free(tree);
}

/*
 * Cast a ray on the specified direction
 * Returns the distance the ray must travel until intersect something
 * Returns FLT_MAX in case of nothing intersection
 * if facenormal is given, it will be overwritted with the normal of the face the ray collided with
 */
static float raytree_cast_ray(RayTree *tree, const float *coord, const float *direction, float *facenormal)
{
	Isect isec;
	float *v1, *v2, *v3, *v4;

	/* Setup intersection */
	isec.mode		= RE_RAY_MIRROR; /* We want closest intersection */
	isec.lay		= -1;
	isec.face_last	= NULL;
	isec.faceorig	= (RayFace*)(-1);
	isec.labda		= 1e10f;

	VECCOPY(isec.start, coord);
	VECCOPY(isec.vec, direction);
	VECADDFAC(isec.end, isec.start, isec.vec, isec.labda);

	if(!RE_ray_tree_intersect(tree, &isec))
		return FLT_MAX;

	if(facenormal)
	{
		raytree_from_mesh_get_coords( isec.face, &v1, &v2, &v3, &v4);
		CalcNormFloat(v1, v2, v3, facenormal);
	}

	isec.labda = ABS(isec.labda);
	VECADDFAC(isec.end, isec.start, isec.vec, isec.labda);
	return VecLenf((float*)coord, (float*)isec.end);
}

/*
 * Returns the squared distance between two given points
 */
static float squared_dist(const float *a, const float *b)
{
	float tmp[3];
	VECSUB(tmp, a, b);
	return INPR(tmp, tmp);
}

/*
 *
 */
static void derivedmesh_mergeNearestPoints(DerivedMesh *dm, float mdist, BitSet skipVert)
{
	if(mdist > 0.0f)
	{
		int i, j, merged;
		int	numVerts = dm->getNumVerts(dm);
		int *translate_vert = MEM_mallocN( sizeof(int)*numVerts, "merge points array");

		MVert *vert = dm->getVertDataArray(dm, CD_MVERT);

		if(!translate_vert) return;

		merged = 0;
		for(i=0; i<numVerts; i++)
		{
			translate_vert[i] = i;

			if(skipVert && bitset_get(skipVert, i)) continue;

			for(j = 0; j<i; j++)
			{
				if(skipVert && bitset_get(skipVert, j)) continue;
				if(squared_dist(vert[i].co, vert[j].co) < mdist)
				{
					translate_vert[i] = j;
					merged++;
					break;
				}
			}
		}

		//some vertexs were merged.. recalculate structure (edges and faces)
		if(merged > 0)
		{
			int	numFaces = dm->getNumFaces(dm);
			int freeVert;
			MFace *face = dm->getFaceDataArray(dm, CD_MFACE);


			//Adjust vertexs using the translation_table.. only translations to back indexs are allowed
			//which means t[i] <= i must always verify
			for(i=0, freeVert = 0; i<numVerts; i++)
			{
				if(translate_vert[i] == i)
				{
					memcpy(&vert[freeVert], &vert[i], sizeof(*vert));
					translate_vert[i] = freeVert++;
				}
				else translate_vert[i] = translate_vert[ translate_vert[i] ];
			}

			CDDM_lower_num_verts(dm, numVerts - merged);

			for(i=0; i<numFaces; i++)
			{
				MFace *f = face+i;
				f->v1 = translate_vert[f->v1];
				f->v2 = translate_vert[f->v2];
				f->v3 = translate_vert[f->v3];
				//TODO be carefull with vertexs v4 being translated to 0
				f->v4 = translate_vert[f->v4];
			}

			//TODO: maybe update edges could be done outside this function
			CDDM_calc_edges(dm);
			//CDDM_calc_normals(dm);
		}

		if(translate_vert) MEM_freeN( translate_vert );
	}
}


/*
 * This calculates the distance (in dir units) that the ray must travel to intersect plane
 * It can return negative values
 *
 * TODO theres probably something like this on blender code
 *
 * Returns FLT_MIN in parallel case
 */
static float ray_intersect_plane(const float *point, const float *dir, const float *plane_point, const float *plane_normal)
{
		float pp[3];
		float a, pp_dist;

		a = INPR(dir, plane_normal);

		if(fabs(a) < 1e-5f) return FLT_MIN;

		VECSUB(pp, point, plane_point);
		pp_dist = INPR(pp, plane_normal);

		return -pp_dist/a;
}

/*
 * This calculates the distance from point to the plane
 * Distance is negative if point is on the back side of plane
 */
static float point_plane_distance(const float *point, const float *plane_point, const float *plane_normal)
{
	float pp[3];
	VECSUB(pp, point, plane_point);
	return INPR(pp, plane_normal);
}
static float choose_nearest(const float v0[2], const float v1[2], const float point[2], float closest[2])
{
	float d[2][2], sdist[2];
	VECSUB2D(d[0], v0, point);
	VECSUB2D(d[1], v1, point);

	sdist[0] = d[0][0]*d[0][0] + d[0][1]*d[0][1];
	sdist[1] = d[1][0]*d[1][0] + d[1][1]*d[1][1];

	if(sdist[0] < sdist[1])
	{
		if(closest)
			VECCOPY2D(closest, v0);
		return sdist[0];
	}
	else
	{
		if(closest)
			VECCOPY2D(closest, v1);
		return sdist[1];
	}
}
/*
 * calculates the closest point between point-tri (2D)
 * returns that tri must be right-handed
 * Returns square distance
 */
static float closest_point_in_tri2D(const float point[2], /*const*/ float tri[3][2], float closest[2])
{
	float edge_di[2];
	float v_point[2];
	float proj[2];					//point projected over edge-dir, edge-normal (witouth normalized edge)
	const float *v0 = tri[2], *v1;
	float edge_slen, d;				//edge squared length
	int i;
	const float *nearest_vertex = NULL;


	//for each edge
	for(i=0, v0=tri[2], v1=tri[0]; i < 3; v0=tri[i++], v1=tri[i])
	{
		VECSUB2D(edge_di,    v1, v0);
		VECSUB2D(v_point, point, v0);

		proj[1] =  v_point[0]*edge_di[1] - v_point[1]*edge_di[0];	//dot product with edge normal

		//point inside this edge
		if(proj[1] < 0)
			continue;

		proj[0] = v_point[0]*edge_di[0] + v_point[1]*edge_di[1];

		//closest to this edge is v0
		if(proj[0] < 0)
		{
 			if(nearest_vertex == NULL || nearest_vertex == v0)
				nearest_vertex = v0;
			else
			{
				//choose nearest
				return choose_nearest(nearest_vertex, v0, point, closest);
			}
			i++;	//We can skip next edge
			continue;
		}

		edge_slen = edge_di[0]*edge_di[0] + edge_di[1]*edge_di[1];	//squared edge len
		//closest to this edge is v1
		if(proj[0] > edge_slen)
		{
 			if(nearest_vertex == NULL || nearest_vertex == v1)
				nearest_vertex = v1;
			else
			{
				return choose_nearest(nearest_vertex, v1, point, closest);
			}
			continue;
		}

		//nearest is on this edge
		d= proj[1] / edge_slen;
		closest[0] = point[0] - edge_di[1] * d;
		closest[1] = point[1] + edge_di[0] * d;

		return proj[1]*proj[1]/edge_slen;
	}

	if(nearest_vertex)
	{
		VECSUB2D(v_point, nearest_vertex, point);
		VECCOPY2D(closest, nearest_vertex);
		return v_point[0]*v_point[0] + v_point[1]*v_point[1];
	}
	else
	{
		VECCOPY(closest, point);	//point is already inside
		return 0.0f;
	}
}

/*
 * Returns the square of the minimum distance between the point and a triangle surface
 * If nearest is not NULL the nearest surface point is written on it
 */
static float nearest_point_in_tri_surface(const float *point, const float *v0, const float *v1, const float *v2, float *nearest)
{
	//Lets solve the 2D problem (closest point-tri)
	float normal_dist, plane_sdist, plane_offset;
	float du[3], dv[3], dw[3];	//orthogonal axis (du=(v0->v1), dw=plane normal)

	float p_2d[2], tri_2d[3][2], nearest_2d[2];

	CalcNormFloat((float*)v0, (float*)v1, (float*)v2, dw);

	//point-plane distance and calculate axis
	normal_dist = point_plane_distance(point, v0, dw);

	VECSUB(du, v1, v0);
	Normalize(du);
	Crossf(dv, dw, du);
	plane_offset = INPR(v0, dw);

	//project stuff to 2d
	tri_2d[0][0] = INPR(du, v0);
	tri_2d[0][1] = INPR(dv, v0);

	tri_2d[1][0] = INPR(du, v1);
	tri_2d[1][1] = INPR(dv, v1);

	tri_2d[2][0] = INPR(du, v2);
	tri_2d[2][1] = INPR(dv, v2);

	p_2d[0] = INPR(du, point);
	p_2d[1] = INPR(dv, point);

	//we always have a right-handed tri
	//this should always happen because of the way normal is calculated
	plane_sdist = closest_point_in_tri2D(p_2d, tri_2d, nearest_2d);

	//project back to 3d
	if(nearest)
	{
		nearest[0] = du[0]*nearest_2d[0] + dv[0] * nearest_2d[1] + dw[0] * plane_offset;
		nearest[1] = du[1]*nearest_2d[0] + dv[1] * nearest_2d[1] + dw[1] * plane_offset;
		nearest[2] = du[2]*nearest_2d[0] + dv[2] * nearest_2d[1] + dw[2] * plane_offset;
	}

	return plane_sdist + normal_dist*normal_dist;
}



/*
 * Shrink to nearest surface point on target mesh
 */
static void bruteforce_shrinkwrap_calc_nearest_surface_point(DerivedMesh *target, float *co, float *unused)
{
	float minDist = FLT_MAX;
	float orig_co[3];

	int i;
	int	numFaces = target->getNumFaces(target);
	MVert *vert = target->getVertDataArray(target, CD_MVERT);
	MFace *face = target->getFaceDataArray(target, CD_MFACE);

	VECCOPY(orig_co, co);	

	for (i = 0; i < numFaces; i++)
	{
		float *v0, *v1, *v2, *v3;

		v0 = vert[ face[i].v1 ].co;
		v1 = vert[ face[i].v2 ].co;
		v2 = vert[ face[i].v3 ].co;
		v3 = face[i].v4 ? vert[ face[i].v4 ].co : 0;

		while(v2)
		{
			float dist;
			float tmp[3];

			dist = nearest_point_in_tri_surface(orig_co, v0, v1, v2, tmp);

			if(dist < minDist)
			{
				minDist = dist;
				VECCOPY(co, tmp);
			}

			v1 = v2;
			v2 = v3;
			v3 = 0;
		}
	}
}

/*
 * Projects the vertex on the normal direction over the target mesh
 */
static void bruteforce_shrinkwrap_calc_normal_projection(DerivedMesh *target, float *co, float *vnormal)
{
	//TODO: this should use raycast code probably existent in blender
	float minDist = FLT_MAX;
	float orig_co[3];

	int i;
	int	numFaces = target->getNumFaces(target);
	MVert *vert = target->getVertDataArray(target, CD_MVERT);
	MFace *face = target->getFaceDataArray(target, CD_MFACE);

	VECCOPY(orig_co, co);

	for (i = 0; i < numFaces; i++)
	{
		float *v0, *v1, *v2, *v3;

		v0 = vert[ face[i].v1 ].co;
		v1 = vert[ face[i].v2 ].co;
		v2 = vert[ face[i].v3 ].co;
		v3 = face[i].v4 ? vert[ face[i].v4 ].co : 0;

		while(v2)
		{
			float dist;
			float pnormal[3];

			CalcNormFloat(v0, v1, v2, pnormal);
			dist =  ray_intersect_plane(orig_co, vnormal, v0, pnormal);

			if(fabs(dist) < minDist)
			{
				float tmp[3], nearest[3];
				VECADDFAC(tmp, orig_co, vnormal, dist);

				if( fabs(nearest_point_in_tri_surface(tmp, v0, v1, v2, nearest)) < 0.0001)
				{
					minDist = fabs(dist);
					VECCOPY(co, nearest);
				}
			}
			v1 = v2;
			v2 = v3;
			v3 = 0;
		}
	}
}

/*
 * Shrink to nearest vertex on target mesh
 */
static void bruteforce_shrinkwrap_calc_nearest_vertex(DerivedMesh *target, float *co, float *unused)
{
	float minDist = FLT_MAX;
	float orig_co[3];

	int i;
	int	numVerts = target->getNumVerts(target);
	MVert *vert = target->getVertDataArray(target, CD_MVERT);

	VECCOPY(orig_co, co);

	for (i = 0; i < numVerts; i++)
	{
		float sdist = squared_dist( orig_co, vert[i].co);
		
		if(sdist < minDist)
		{
			minDist = sdist;
			VECCOPY(co, vert[i].co);
		}
	}
}


static void shrinkwrap_calc_foreach_vertex(ShrinkwrapCalcData *calc, Shrinkwrap_ForeachVertexCallback callback)
{
	int i;
	int vgroup		= get_named_vertexgroup_num(calc->ob, calc->smd->vgroup_name);
	int	numVerts	= 0;

	MDeformVert *dvert = NULL;
	MVert		*vert  = NULL;

	numVerts = calc->final->getNumVerts(calc->final);
	dvert = calc->final->getVertDataArray(calc->final, CD_MDEFORMVERT);
	vert  = calc->final->getVertDataArray(calc->final, CD_MVERT);

	//Shrink (calculate each vertex final position)
	for(i = 0; i<numVerts; i++)
	{
		float weight = vertexgroup_get_vertex_weight(dvert, i, vgroup);

		float final[3]; //Coords relative to target
		float normal[3];
		float dist;

		if(weight == 0.0f) continue;	//Skip vertexs where we have no influence

		VECCOPY(final, vert[i].co);
		space_transform_apply(&calc->local2target, final);

		//We also need to apply the rotation to normal
		if(calc->smd->shrinkType == MOD_SHRINKWRAP_NORMAL)
		{
			NormalShortToFloat(normal, vert[i].no);
			space_transform_apply_normal(&calc->local2target, normal);
		}
		(callback)(calc->target, final, normal);

		space_transform_invert(&calc->local2target, final);

		dist = VecLenf(vert[i].co, final);
		if(dist > 1e-5) weight *= (dist - calc->keptDist)/dist;
		VecLerpf(vert[i].co, vert[i].co, final, weight);	//linear interpolation
	}
}


/*
 * This function removes Unused faces, vertexs and edges from calc->target
 *
 * This function may modify calc->final. As so no data retrieved from
 * it before the call to this function  can be considered valid
 * In case it creates a new DerivedMesh, the old calc->final is freed
 */
//TODO memory checks on allocs
static void shrinkwrap_removeUnused(ShrinkwrapCalcData *calc)
{
	int i, t;

	DerivedMesh *old = calc->final, *new = NULL;
	MFace *new_face = NULL;
	MVert *new_vert  = NULL;

	int numVerts= old->getNumVerts(old);
	MVert *vert = old->getVertDataArray(old, CD_MVERT);

	int	numFaces= old->getNumFaces(old);
	MFace *face = old->getFaceDataArray(old, CD_MFACE);

	BitSet moved_verts = calc->moved;

	//Arrays to translate to new vertexs indexs
	int *vert_index = (int*)MEM_callocN(sizeof(int)*(numVerts), "shrinkwrap used verts");
	BitSet used_faces = bitset_new(numFaces, "shrinkwrap used faces");
	int numUsedFaces = 0;


	//calculate which vertexs need to be used
	//even unmoved vertices might need to be used if theres a face that needs it
	//calc real number of faces, and vertices
	//Count used faces
	for(i=0; i<numFaces; i++)
	{
		char res = 0;
		if(bitset_get(moved_verts, face[i].v1)) res++;
		if(bitset_get(moved_verts, face[i].v2)) res++;
		if(bitset_get(moved_verts, face[i].v3)) res++;
		if(face[i].v4 && bitset_get(moved_verts, face[i].v4)) res++;

		//Ignore a face were not a single vertice moved
		if(res == 0) continue;


		//Only 1 vertice moved.. (if its a quad.. remove the vertice oposite to it)
		if(res == 1 && face[i].v4)
		{
			if(bitset_get(moved_verts, face[i].v1))
			{
				//remove vertex 3
				face[i].v3 = face[i].v4;
			}
			else if(bitset_get(moved_verts, face[i].v2))
			{
				//remove vertex 4
			}
			else if(bitset_get(moved_verts, face[i].v3))
			{
				//remove vertex 1
				face[i].v1 = face[i].v4;
			}
			else if(bitset_get(moved_verts, face[i].v4))
			{
				//remove vertex 2
				face[i].v2 = face[i].v3;
				face[i].v3 = face[i].v4;
			}

			face[i].v4 = 0;	//this quad turned on a tri
		}
		
/*
		if(face[i].v4 && res == 3)
		{
			if(!bitset_get(moved_verts, face[i].v1))
			{
				face[i].v1 = face[i].v4;
			}
			else if(!bitset_get(moved_verts, face[i].v2))
			{
				face[i].v2 = face[i].v3;
				face[i].v3 = face[i].v4;
			}
			else if(!bitset_get(moved_verts, face[i].v3))
			{
				face[i].v3 = face[i].v4;
			}

			face[i].v4 = 0;	//this quad turned on a tri
		}
*/

		bitset_set(used_faces, i);	//Mark face to maintain
		numUsedFaces++;

		//Mark vertices are needed
		vert_index[face[i].v1] = 1;
		vert_index[face[i].v2] = 1;
		vert_index[face[i].v3] = 1;
		if(face[i].v4) vert_index[face[i].v4] = 1;
	}

	//DP: Accumulate vertexs indexs.. (will calculate the new vertex index with a 1 offset)
	for(i=1; i<numVerts; i++)
		vert_index[i] += vert_index[i-1];
		
	
	//Start creating the clean mesh
	new = CDDM_new(vert_index[numVerts-1], 0, numUsedFaces);

	//Copy vertexs (unused are are removed)
	new_vert  = new->getVertDataArray(new, CD_MVERT);
	for(i=0, t=0; i<numVerts; i++)
	{
		
		if(vert_index[i] != t)
		{
			t = vert_index[i];
			memcpy(new_vert++, vert+i, sizeof(MVert));

			if(bitset_get(moved_verts, i))
				bitset_set(moved_verts, t-1);
			else
				bitset_unset(moved_verts, t-1);
		}
	}

	//Copy faces
	new_face = new->getFaceDataArray(new, CD_MFACE);
	for(i=0, t=0; i<numFaces; i++)
	{
		if(bitset_get(used_faces, i))
		{
			memcpy(new_face, face+i, sizeof(MFace));
			//update vertices indexs
			new_face->v1 = vert_index[new_face->v1]-1;
			new_face->v2 = vert_index[new_face->v2]-1;
			new_face->v3 = vert_index[new_face->v3]-1;
			if(new_face->v4)
			{
				new_face->v4 = vert_index[new_face->v4]-1;

				//Ups translated vertex ended on 0 .. TODO fix this
				if(new_face->v4 == 0)
				{
				}
			}			
			new_face++;
		}
	}

	//Free memory
	bitset_free(used_faces);
	MEM_freeN(vert_index);
	old->release(old);

	//Update edges
	CDDM_calc_edges(new);
	CDDM_calc_normals(new);

	calc->final = new;
}


void shrinkwrap_projectToCutPlane(ShrinkwrapCalcData *calc_data)
{
	if(calc_data->smd->cutPlane && calc_data->moved)
	{
		int i;
		int unmoved = 0;
		int numVerts= 0;
		MVert *vert = NULL;
		MVert *vert_unmoved = NULL;

		ShrinkwrapCalcData calc;
		memcpy(&calc, calc_data, sizeof(calc));

		calc.moved = 0;

		if(calc.smd->cutPlane)
		{
			calc.target = (DerivedMesh *)calc.smd->cutPlane->derivedFinal;

			if(!calc.target)
			{
				return;
			}

			space_transform_setup(&calc.local2target, calc.ob, calc.smd->cutPlane);
			calc.keptDist = 0;
		}


		//Make a mesh with the points we want to project
		numVerts = calc_data->final->getNumVerts(calc_data->final);

		unmoved = 0;
		for(i=0; i<numVerts; i++)
			if(!bitset_get(calc_data->moved, i))
				unmoved++;

		calc.final = CDDM_new(unmoved, 0, 0);
		if(!calc.final) return;


		vert = calc_data->final->getVertDataArray(calc_data->final, CD_MVERT);
		vert_unmoved = calc.final->getVertDataArray(calc.final, CD_MVERT);

		for(i=0; i<numVerts; i++)
			if(!bitset_get(calc_data->moved, i))
				memcpy(vert_unmoved++, vert+i, sizeof(*vert_unmoved));

		//use shrinkwrap projection
		shrinkwrap_calc_normal_projection(&calc);

		//Copy the points back to the mesh
		vert = calc_data->final->getVertDataArray(calc_data->final, CD_MVERT);
		vert_unmoved = calc.final->getVertDataArray(calc.final, CD_MVERT);
		for(i=0; i<numVerts; i++)
			if(!bitset_get(calc_data->moved, i))
				memcpy(vert+i, vert_unmoved++, sizeof(*vert_unmoved) );

		//free memory
		calc.final->release(calc.final);
	}	

}


/* Main shrinkwrap function */
DerivedMesh *shrinkwrapModifier_do(ShrinkwrapModifierData *smd, Object *ob, DerivedMesh *dm, int useRenderParams, int isFinalCalc)
{

	ShrinkwrapCalcData calc;
	memset(&calc, 0, sizeof(calc));

	//Init Shrinkwrap calc data
	calc.smd = smd;

	calc.ob = ob;
	calc.original = dm;
	calc.final = CDDM_copy(calc.original);

	if(!calc.final)
	{
		OUT_OF_MEMORY();
		return dm;
	}

	if(smd->target)
	{
		calc.target = (DerivedMesh *)smd->target->derivedFinal;

		if(!calc.target)
		{
			printf("Target derived mesh is null! :S\n");
		}

		//TODO there might be several "bugs" on non-uniform scales matrixs.. because it will no longer be nearest surface, not sphere projection
		//because space has been deformed
		space_transform_setup(&calc.local2target, ob, smd->target);

		calc.keptDist = smd->keptDist;	//TODO: smd->keptDist is in global units.. must change to local
	}

	//Projecting target defined - lets work!
	if(calc.target)
	{

		printf("Shrinkwrap (%s)%d over (%s)%d\n",
			calc.ob->id.name,			calc.final->getNumVerts(calc.final),
			calc.smd->target->id.name,	calc.target->getNumVerts(calc.target)
		);


		switch(smd->shrinkType)
		{
			case MOD_SHRINKWRAP_NEAREST_SURFACE:
				BENCH(shrinkwrap_calc_nearest_surface_point(&calc));
//				BENCH(shrinkwrap_calc_foreach_vertex(&calc, bruteforce_shrinkwrap_calc_nearest_surface_point));
			break;

			case MOD_SHRINKWRAP_NORMAL:

				if(calc.smd->shrinkOpts & MOD_SHRINKWRAP_REMOVE_UNPROJECTED_FACES)
				calc.moved = bitset_new( calc.final->getNumVerts(calc.final), "shrinkwrap bitset data");


//				BENCH(shrinkwrap_calc_normal_projection_raytree(&calc));
//				calc.final->release( calc.final );
//				calc.final = CDDM_copy(calc.original);

				BENCH(shrinkwrap_calc_normal_projection(&calc));
//				BENCH(shrinkwrap_calc_foreach_vertex(&calc, bruteforce_shrinkwrap_calc_normal_projection));

				if(calc.moved)
				{
					//Adjust vertxs that didn't moved (project to cut plane)
					shrinkwrap_projectToCutPlane(&calc);

					//Destroy faces, edges and stuff
					shrinkwrap_removeUnused(&calc);

					//Merge points that didn't moved
					derivedmesh_mergeNearestPoints(calc.final, calc.smd->mergeDist, calc.moved);
					bitset_free(calc.moved);
				}
			break;

			case MOD_SHRINKWRAP_NEAREST_VERTEX:

				BENCH(shrinkwrap_calc_nearest_vertex(&calc));
//				BENCH(shrinkwrap_calc_foreach_vertex(&calc, bruteforce_shrinkwrap_calc_nearest_vertex));
			break;
		}

	}

	CDDM_calc_normals(calc.final);

	return calc.final;
}


/*
 * Shrinkwrap to the nearest vertex
 *
 * it builds a kdtree of vertexs we can attach to and then
 * for each vertex on performs a nearest vertex search on the tree
 */
void shrinkwrap_calc_nearest_vertex(ShrinkwrapCalcData *calc)
{
	int i;
	int vgroup		= get_named_vertexgroup_num(calc->ob, calc->smd->vgroup_name);
	float tmp_co[3];

	BVHTree *tree	= NULL;
	BVHTreeNearest nearest;

	int	numVerts;
	MVert *vert = NULL;
	MDeformVert *dvert = NULL;

	BENCH_VAR(query);


	BENCH(tree = bvhtree_from_mesh_verts(calc->target, 0.0, 2, 6));
	if(tree == NULL) return OUT_OF_MEMORY();

	//Setup nearest
	nearest.index = -1;
	nearest.dist = FLT_MAX;


	//Find the nearest vertex 
	numVerts= calc->final->getNumVerts(calc->final);
	vert	= calc->final->getVertDataArray(calc->final, CD_MVERT);	
	dvert	= calc->final->getVertDataArray(calc->final, CD_MDEFORMVERT);

	BENCH_BEGIN(query);
	for(i=0; i<numVerts; i++)
	{
		int index;
		float weight = vertexgroup_get_vertex_weight(dvert, i, vgroup);
		if(weight == 0.0f) continue;

		VECCOPY(tmp_co, vert[i].co);
		space_transform_apply(&calc->local2target, tmp_co);

		if(nearest.index != -1)
		{
			nearest.dist = squared_dist(tmp_co, nearest.nearest);
		}
		else nearest.dist = FLT_MAX;

		index = BLI_bvhtree_find_nearest(tree, tmp_co, &nearest, NULL, NULL);

		if(index != -1)
		{
			float dist;

			space_transform_invert(&calc->local2target, tmp_co);
			dist = VecLenf(vert[i].co, tmp_co);
			if(dist > 1e-5) weight *= (dist - calc->keptDist)/dist;
			VecLerpf(vert[i].co, vert[i].co, tmp_co, weight);	//linear interpolation
		}
	}
	BENCH_END(query);
	BENCH_REPORT(query);

	BLI_bvhtree_free(tree);
}

/*
 * Shrinkwrap projecting vertexs allong their normals over the target
 *
 * it builds a RayTree from the target mesh and then performs a
 * raycast for each vertex (ray direction = normal)
 */
/*
void shrinkwrap_calc_normal_projection_raytree(ShrinkwrapCalcData *calc)
{
	int i;
	int vgroup		= get_named_vertexgroup_num(calc->ob, calc->smd->vgroup_name);
	char use_normal = calc->smd->shrinkOpts;
	RayTree *target = NULL;

	int	numVerts;
	MVert *vert = NULL;
	MDeformVert *dvert = NULL;
	float tmp_co[3], tmp_no[3];

	if( (use_normal & (MOD_SHRINKWRAP_ALLOW_INVERTED_NORMAL | MOD_SHRINKWRAP_ALLOW_DEFAULT_NORMAL)) == 0)
		return;	//Nothing todo

	//setup raytracing
	BENCH(target = raytree_create_from_mesh(calc->target));
	if(target == NULL) return OUT_OF_MEMORY();



	//Project each vertex along normal
	numVerts= calc->final->getNumVerts(calc->final);
	vert	= calc->final->getVertDataArray(calc->final, CD_MVERT);	
	dvert	= calc->final->getVertDataArray(calc->final, CD_MDEFORMVERT);

	for(i=0; i<numVerts; i++)
	{
		float dist = FLT_MAX;
		float weight = vertexgroup_get_vertex_weight(dvert, i, vgroup);
		float face_normal[3];
		if(weight == 0.0f) continue;

		//Transform coordinates local->target
		VecMat4MulVecfl(tmp_co, calc->local2target, vert[i].co);

		NormalShortToFloat(tmp_no, vert[i].no);
		Mat4Mul3Vecfl(calc->local2target, tmp_no);	//Watch out for scaling on normal
		Normalize(tmp_no);							//(TODO: do we really needed a unit-len normal? and we could know the scale factor before hand?)

		if(use_normal & MOD_SHRINKWRAP_ALLOW_DEFAULT_NORMAL)
		{
			dist = raytree_cast_ray(target, tmp_co, tmp_no, face_normal);

			if((calc->smd->shrinkOpts & MOD_SHRINKWRAP_CULL_TARGET_FRONTFACE) && INPR(tmp_no, face_normal) < 0)
				dist = FLT_MAX;
			if((calc->smd->shrinkOpts & MOD_SHRINKWRAP_CULL_TARGET_BACKFACE) && INPR(tmp_no, face_normal) > 0)
				dist = FLT_MAX;
		}

		if(use_normal & MOD_SHRINKWRAP_ALLOW_INVERTED_NORMAL)
		{
			float inv[3]; // = {-tmp_no[0], -tmp_no[1], -tmp_no[2]};
			float tdist;

			inv[0] = -tmp_no[0];
			inv[1] = -tmp_no[1];
			inv[2] = -tmp_no[2];

			tdist = raytree_cast_ray(target, tmp_co, inv, 0);

			if((calc->smd->shrinkOpts & MOD_SHRINKWRAP_CULL_TARGET_FRONTFACE) && INPR(tmp_no, face_normal) < 0)
				tdist = FLT_MAX;
			if((calc->smd->shrinkOpts & MOD_SHRINKWRAP_CULL_TARGET_BACKFACE) && INPR(tmp_no, face_normal) > 0)
				tdist = FLT_MAX;

			if(ABS(tdist) < ABS(dist))
				dist = -tdist;
		}

		if(ABS(dist) != FLT_MAX)
		{
			float dist_t;

			VECADDFAC(tmp_co, tmp_co, tmp_no, dist);
			VecMat4MulVecfl(tmp_co, calc->target2local, tmp_co);

			dist_t = VecLenf(vert[i].co, tmp_co);
			if(dist_t > 1e-5) weight *= (dist_t - calc->keptDist)/dist_t;
			VecLerpf(vert[i].co, vert[i].co, tmp_co, weight);	//linear interpolation

			if(calc->moved)
				bitset_set(calc->moved, i);
		}

	}

	free_raytree_from_mesh(target);
}
*/


/*
 * This function raycast a single vertex and updates the hit if the "hit" is considered valid.
 * Returns TRUE if "hit" was updated.
 * Opts control whether an hit is valid or not
 * Supported options are:
 *	MOD_SHRINKWRAP_CULL_TARGET_FRONTFACE (front faces hits are ignored)
 *	MOD_SHRINKWRAP_CULL_TARGET_BACKFACE (back faces hits are ignored)
 */
static int normal_projection_project_vertex(char options, const float *vert, const float *dir,/* const */ SpaceTransform *transf, BVHTree *tree, BVHTreeRayHit *hit, BVHTree_RayCastCallback callback, BVHMeshCallbackUserdata *userdata)
{
	float tmp_co[3], tmp_no[3];
	BVHTreeRayHit hit_tmp;
	memcpy( &hit_tmp, hit, sizeof(hit_tmp) );

	//Apply space transform (TODO readjust dist)
	if(transf)
	{
		VECCOPY( tmp_co, vert );
		space_transform_apply( transf, tmp_co );
		vert = tmp_co;

		VECCOPY( tmp_no, dir );
		space_transform_apply_normal( transf, tmp_no );
		dir = tmp_no;
	}

	hit_tmp.index = -1;

	BLI_bvhtree_ray_cast(tree, vert, dir, &hit_tmp, callback, userdata);

	if(hit_tmp.index != -1)
	{
		float dot = INPR( dir, hit_tmp.no);

		if(((options & MOD_SHRINKWRAP_CULL_TARGET_FRONTFACE) && dot < 0)
		|| ((options & MOD_SHRINKWRAP_CULL_TARGET_BACKFACE) && dot > 0))
			return FALSE; //Ignore hit


		//Inverting space transform (TODO readjust dist)
		if(transf)
		{
			space_transform_invert( transf, hit_tmp.co );
			space_transform_invert_normal( transf, hit_tmp.no );
		}

		memcpy(hit, &hit_tmp, sizeof(hit_tmp) );
		return TRUE;
	}
	return FALSE;
}


void shrinkwrap_calc_normal_projection(ShrinkwrapCalcData *calc)
{
	int i;
	int vgroup		= get_named_vertexgroup_num(calc->ob, calc->smd->vgroup_name);
	char use_normal = calc->smd->shrinkOpts;

	//setup raytracing
	BVHTree *tree	= NULL;
	BVHTreeRayHit hit;
	BVHMeshCallbackUserdata userdata;
	BVHTree_RayCastCallback callback = NULL;


	//cutTree
	BVHTree *limit_tree = NULL;
	BVHMeshCallbackUserdata limit_userdata;
	BVHTree_RayCastCallback limit_callback = NULL;
	SpaceTransform local2cut;


	int	numVerts;
	MVert *vert = NULL;
	MDeformVert *dvert = NULL;

	if( (use_normal & (MOD_SHRINKWRAP_ALLOW_INVERTED_NORMAL | MOD_SHRINKWRAP_ALLOW_DEFAULT_NORMAL)) == 0)
		return;	//Nothing todo

	BENCH(tree = bvhtree_from_mesh_faces(calc->target, calc->keptDist, 4, 6));
	if(tree == NULL) return OUT_OF_MEMORY();
	bvhtree_meshcallbackdata_init(&userdata, calc->target, calc->keptDist);
	callback = mesh_faces_spherecast;

	if(calc->smd->cutPlane)
	{
		DerivedMesh * limit_mesh = (DerivedMesh *)calc->smd->cutPlane->derivedFinal;
		if(limit_mesh)
		{
			BENCH(limit_tree = bvhtree_from_mesh_faces(limit_mesh, 0.0, 4, 6));
			bvhtree_meshcallbackdata_init(&limit_userdata, limit_mesh, 0.0);
			limit_callback = mesh_faces_spherecast;

			space_transform_setup( &local2cut, calc->ob, calc->smd->cutPlane);
		}
		else printf("CutPlane finalDerived mesh is null\n");
	}


	//Project each vertex along normal
	numVerts= calc->final->getNumVerts(calc->final);
	vert	= calc->final->getVertDataArray(calc->final, CD_MVERT);	
	dvert	= calc->final->getVertDataArray(calc->final, CD_MDEFORMVERT);

	for(i=0; i<numVerts; i++)
	{
		float tmp_co[3], tmp_no[3];
		float lim = 1000;		//TODO: we should use FLT_MAX here, but sweepsphere code isnt prepared for that
		float weight = vertexgroup_get_vertex_weight(dvert, i, vgroup);

		if(weight == 0.0f) continue;

		VECCOPY(tmp_co, vert[i].co);
		NormalShortToFloat(tmp_no, vert[i].no);


		hit.index = -1;
		hit.dist = lim;

/*		if(limit_tree)
		{
			normal_projection_project_vertex(0, tmp_co, tmp_no, &local2cut, limit_tree, &hit, callback, &userdata);
		}
*/
		if(use_normal & MOD_SHRINKWRAP_ALLOW_DEFAULT_NORMAL)
		{
			normal_projection_project_vertex(calc->smd->shrinkOpts, tmp_co, tmp_no, &calc->local2target, tree, &hit, callback, &userdata);
		}


		if(use_normal & MOD_SHRINKWRAP_ALLOW_INVERTED_NORMAL)
		{
			float inv_no[3] = { -tmp_no[0], -tmp_no[1], -tmp_no[2] };
			normal_projection_project_vertex(calc->smd->shrinkOpts, tmp_co, inv_no, &calc->local2target, tree, &hit, callback, &userdata);
		}


		if(hit.index != -1)
		{
			VecLerpf(vert[i].co, vert[i].co, hit.co, weight);	//linear interpolation

			if(calc->moved)
				bitset_set(calc->moved, i);
		}
	}

	BLI_bvhtree_free(tree);

	if(limit_tree)
		BLI_bvhtree_free(limit_tree);
}

/*
 * Shrinkwrap moving vertexs to the nearest surface point on the target
 *
 * it builds a BVHTree from the target mesh and then performs a
 * NN matchs for each vertex
 */
void shrinkwrap_calc_nearest_surface_point(ShrinkwrapCalcData *calc)
{
	int i;
	int vgroup		= get_named_vertexgroup_num(calc->ob, calc->smd->vgroup_name);
	float tmp_co[3];

	BVHTree *tree	= NULL;
	BVHTreeNearest nearest;
	BVHMeshCallbackUserdata userdata;

	int	numVerts;
	MVert *vert = NULL;
	MDeformVert *dvert = NULL;


	//Create a bvh-tree of the given target
	tree = bvhtree_from_mesh_tri(calc->target, 0.0, 2, 6);
	if(tree == NULL) return OUT_OF_MEMORY();
	bvhtree_meshcallbackdata_init(&userdata, calc->target, 0.0);

	//Setup nearest
	nearest.index = -1;
	nearest.dist = FLT_MAX;


	//Find the nearest vertex 
	numVerts= calc->final->getNumVerts(calc->final);
	vert	= calc->final->getVertDataArray(calc->final, CD_MVERT);	
	dvert	= calc->final->getVertDataArray(calc->final, CD_MDEFORMVERT);

	for(i=0; i<numVerts; i++)
	{
		int index;
		float weight = vertexgroup_get_vertex_weight(dvert, i, vgroup);
		if(weight == 0.0f) continue;

		VECCOPY(tmp_co, vert[i].co);
		space_transform_apply(&calc->local2target, tmp_co);

		if(nearest.index != -1)
		{
			nearest.dist = squared_dist(tmp_co, nearest.nearest);
		}
		else nearest.dist = FLT_MAX;

		index = BLI_bvhtree_find_nearest(tree, tmp_co, &nearest, mesh_tri_nearest_point, &userdata);

		if(index != -1)
		{
			if(calc->smd->shrinkOpts & MOD_SHRINKWRAP_KEPT_ABOVE_SURFACE)
			{
				float *t0, *t1, *t2;
				float surface_normal[3], tmp[3];
				bvhtree_from_mesh_get_tri(&userdata, index, &t0, &t1, &t2);
				CalcNormFloat(t0, t1, t2, surface_normal);
				VECSUB(tmp, vert[i].co, t0 );
				VECADDFAC(tmp_co, nearest.nearest, surface_normal, calc->keptDist);

			}
			else
			{
				float dist = VecLenf(tmp_co, nearest.nearest);
				VecLerpf(tmp_co, tmp_co, nearest.nearest, (dist - calc->keptDist)/dist);	//linear interpolation
			}
			space_transform_invert(&calc->local2target, tmp_co);
			VecLerpf(vert[i].co, vert[i].co, tmp_co, weight);	//linear interpolation
		}
	}

	BLI_bvhtree_free(tree);
}

