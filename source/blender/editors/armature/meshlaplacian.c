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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 * meshlaplacian.c: Algorithms using the mesh laplacian.
 */

#include <math.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_object_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_scene_types.h"

#include "BLI_math.h"
#include "BLI_edgehash.h"
#include "BLI_memarena.h"

#include "BKE_DerivedMesh.h"
#include "BKE_modifier.h"
#include "BKE_utildefines.h"

#ifdef RIGID_DEFORM
#include "BLI_editVert.h"
#include "BLI_polardecomp.h"
#endif

#include "ONL_opennl.h"

#include "BLO_sys_types.h" // for intptr_t support

#include "ED_mesh.h"

#include "meshlaplacian.h"


/* ************* XXX *************** */
static void waitcursor(int val) {}
static void progress_bar(int dummy_val, const char *dummy) {}
static void start_progress_bar() {}
static void end_progress_bar() {}
static void error(char *str) { printf("error: %s\n", str); }
/* ************* XXX *************** */


/************************** Laplacian System *****************************/

struct LaplacianSystem {
	NLContext context;	/* opennl context */

	int totvert, totface;

	float **verts;			/* vertex coordinates */
	float *varea;			/* vertex weights for laplacian computation */
	char *vpinned;			/* vertex pinning */
	int (*faces)[3];		/* face vertex indices */
	float (*fweights)[3];	/* cotangent weights per face */

	int areaweights;		/* use area in cotangent weights? */
	int storeweights;		/* store cotangent weights in fweights */
	int nlbegun;			/* nlBegin(NL_SYSTEM/NL_MATRIX) done */

	EdgeHash *edgehash;		/* edge hash for construction */

	struct HeatWeighting {
		MFace *mface;
		int totvert;
		int totface;
		float (*verts)[3];	/* vertex coordinates */
		float (*vnors)[3];	/* vertex normals */

		float (*root)[3];	/* bone root */
		float (*tip)[3];	/* bone tip */
		float (*source)[3]; /* vertex source */
		int numsource;

		float *H;			/* diagonal H matrix */
		float *p;			/* values from all p vectors */
		float *mindist;		/* minimum distance to a bone for all vertices */
		
		BVHTree   *bvhtree;	/* ray tracing acceleration structure */
		MFace     **vface;	/* a face that the vertex belongs to */
	} heat;

#ifdef RIGID_DEFORM
	struct RigidDeformation {
		EditMesh *mesh;

		float (*R)[3][3];
		float (*rhs)[3];
		float (*origco)[3];
		int thrownerror;
	} rigid;
#endif
};

/* Laplacian matrix construction */

/* Computation of these weights for the laplacian is based on:
   "Discrete Differential-Geometry Operators for Triangulated 2-Manifolds",
   Meyer et al, 2002. Section 3.5, formula (8).
   
   We do it a bit different by going over faces instead of going over each
   vertex and adjacent faces, since we don't store this adjacency. Also, the
   formulas are tweaked a bit to work for non-manifold meshes. */

static void laplacian_increase_edge_count(EdgeHash *edgehash, int v1, int v2)
{
	void **p = BLI_edgehash_lookup_p(edgehash, v1, v2);

	if(p)
		*p = (void*)((intptr_t)*p + (intptr_t)1);
	else
		BLI_edgehash_insert(edgehash, v1, v2, (void*)(intptr_t)1);
}

static int laplacian_edge_count(EdgeHash *edgehash, int v1, int v2)
{
	return (int)(intptr_t)BLI_edgehash_lookup(edgehash, v1, v2);
}

static float cotan_weight(float *v1, float *v2, float *v3)
{
	float a[3], b[3], c[3], clen;

	sub_v3_v3v3(a, v2, v1);
	sub_v3_v3v3(b, v3, v1);
	cross_v3_v3v3(c, a, b);

	clen = len_v3(c);

	if (clen == 0.0f)
		return 0.0f;
	
	return dot_v3v3(a, b)/clen;
}

static void laplacian_triangle_area(LaplacianSystem *sys, int i1, int i2, int i3)
{
	float t1, t2, t3, len1, len2, len3, area;
	float *varea= sys->varea, *v1, *v2, *v3;
	int obtuse = 0;

	v1= sys->verts[i1];
	v2= sys->verts[i2];
	v3= sys->verts[i3];

	t1= cotan_weight(v1, v2, v3);
	t2= cotan_weight(v2, v3, v1);
	t3= cotan_weight(v3, v1, v2);

	if(RAD2DEG(angle_v3v3v3(v2, v1, v3)) > 90) obtuse= 1;
	else if(RAD2DEG(angle_v3v3v3(v1, v2, v3)) > 90) obtuse= 2;
	else if(RAD2DEG(angle_v3v3v3(v1, v3, v2)) > 90) obtuse= 3;

	if (obtuse > 0) {
		area= area_tri_v3(v1, v2, v3);

		varea[i1] += (obtuse == 1)? area: area*0.5;
		varea[i2] += (obtuse == 2)? area: area*0.5;
		varea[i3] += (obtuse == 3)? area: area*0.5;
	}
	else {
		len1= len_v3v3(v2, v3);
		len2= len_v3v3(v1, v3);
		len3= len_v3v3(v1, v2);

		t1 *= len1*len1;
		t2 *= len2*len2;
		t3 *= len3*len3;

		varea[i1] += (t2 + t3)*0.25f;
		varea[i2] += (t1 + t3)*0.25f;
		varea[i3] += (t1 + t2)*0.25f;
	}
}

static void laplacian_triangle_weights(LaplacianSystem *sys, int f, int i1, int i2, int i3)
{
	float t1, t2, t3;
	float *varea= sys->varea, *v1, *v2, *v3;

	v1= sys->verts[i1];
	v2= sys->verts[i2];
	v3= sys->verts[i3];

	/* instead of *0.5 we divided by the number of faces of the edge, it still
	   needs to be verified that this is indeed the correct thing to do! */
	t1= cotan_weight(v1, v2, v3)/laplacian_edge_count(sys->edgehash, i2, i3);
	t2= cotan_weight(v2, v3, v1)/laplacian_edge_count(sys->edgehash, i3, i1);
	t3= cotan_weight(v3, v1, v2)/laplacian_edge_count(sys->edgehash, i1, i2);

	nlMatrixAdd(i1, i1, (t2+t3)*varea[i1]);
	nlMatrixAdd(i2, i2, (t1+t3)*varea[i2]);
	nlMatrixAdd(i3, i3, (t1+t2)*varea[i3]);

	nlMatrixAdd(i1, i2, -t3*varea[i1]);
	nlMatrixAdd(i2, i1, -t3*varea[i2]);

	nlMatrixAdd(i2, i3, -t1*varea[i2]);
	nlMatrixAdd(i3, i2, -t1*varea[i3]);

	nlMatrixAdd(i3, i1, -t2*varea[i3]);
	nlMatrixAdd(i1, i3, -t2*varea[i1]);

	if(sys->storeweights) {
		sys->fweights[f][0]= t1*varea[i1];
		sys->fweights[f][1]= t2*varea[i2];
		sys->fweights[f][2]= t3*varea[i3];
	}
}

LaplacianSystem *laplacian_system_construct_begin(int totvert, int totface, int lsq)
{
	LaplacianSystem *sys;

	sys= MEM_callocN(sizeof(LaplacianSystem), "LaplacianSystem");

	sys->verts= MEM_callocN(sizeof(float*)*totvert, "LaplacianSystemVerts");
	sys->vpinned= MEM_callocN(sizeof(char)*totvert, "LaplacianSystemVpinned");
	sys->faces= MEM_callocN(sizeof(int)*3*totface, "LaplacianSystemFaces");

	sys->totvert= 0;
	sys->totface= 0;

	sys->areaweights= 1;
	sys->storeweights= 0;

	/* create opennl context */
	nlNewContext();
	nlSolverParameteri(NL_NB_VARIABLES, totvert);
	if(lsq)
		nlSolverParameteri(NL_LEAST_SQUARES, NL_TRUE);

	sys->context= nlGetCurrent();

	return sys;
}

void laplacian_add_vertex(LaplacianSystem *sys, float *co, int pinned)
{
	sys->verts[sys->totvert]= co;
	sys->vpinned[sys->totvert]= pinned;
	sys->totvert++;
}

void laplacian_add_triangle(LaplacianSystem *sys, int v1, int v2, int v3)
{
	sys->faces[sys->totface][0]= v1;
	sys->faces[sys->totface][1]= v2;
	sys->faces[sys->totface][2]= v3;
	sys->totface++;
}

void laplacian_system_construct_end(LaplacianSystem *sys)
{
	int (*face)[3];
	int a, totvert=sys->totvert, totface=sys->totface;

	laplacian_begin_solve(sys, 0);

	sys->varea= MEM_callocN(sizeof(float)*totvert, "LaplacianSystemVarea");

	sys->edgehash= BLI_edgehash_new();
	for(a=0, face=sys->faces; a<sys->totface; a++, face++) {
		laplacian_increase_edge_count(sys->edgehash, (*face)[0], (*face)[1]);
		laplacian_increase_edge_count(sys->edgehash, (*face)[1], (*face)[2]);
		laplacian_increase_edge_count(sys->edgehash, (*face)[2], (*face)[0]);
	}

	if(sys->areaweights)
		for(a=0, face=sys->faces; a<sys->totface; a++, face++)
			laplacian_triangle_area(sys, (*face)[0], (*face)[1], (*face)[2]);
	
	for(a=0; a<totvert; a++) {
		if(sys->areaweights) {
			if(sys->varea[a] != 0.0f)
				sys->varea[a]= 0.5f/sys->varea[a];
		}
		else
			sys->varea[a]= 1.0f;

		/* for heat weighting */
		if(sys->heat.H)
			nlMatrixAdd(a, a, sys->heat.H[a]);
	}

	if(sys->storeweights)
		sys->fweights= MEM_callocN(sizeof(float)*3*totface, "LaplacianFWeight");
	
	for(a=0, face=sys->faces; a<totface; a++, face++)
		laplacian_triangle_weights(sys, a, (*face)[0], (*face)[1], (*face)[2]);

	MEM_freeN(sys->faces);
	sys->faces= NULL;

	if(sys->varea) {
		MEM_freeN(sys->varea);
		sys->varea= NULL;
	}

	BLI_edgehash_free(sys->edgehash, NULL);
	sys->edgehash= NULL;
}

void laplacian_system_delete(LaplacianSystem *sys)
{
	if(sys->verts) MEM_freeN(sys->verts);
	if(sys->varea) MEM_freeN(sys->varea);
	if(sys->vpinned) MEM_freeN(sys->vpinned);
	if(sys->faces) MEM_freeN(sys->faces);
	if(sys->fweights) MEM_freeN(sys->fweights);

	nlDeleteContext(sys->context);
	MEM_freeN(sys);
}

void laplacian_begin_solve(LaplacianSystem *sys, int index)
{
	int a;

	if (!sys->nlbegun) {
		nlBegin(NL_SYSTEM);

		if(index >= 0) {
			for(a=0; a<sys->totvert; a++) {
				if(sys->vpinned[a]) {
					nlSetVariable(0, a, sys->verts[a][index]);
					nlLockVariable(a);
				}
			}
		}

		nlBegin(NL_MATRIX);
		sys->nlbegun = 1;
	}
}

void laplacian_add_right_hand_side(LaplacianSystem *sys, int v, float value)
{
	nlRightHandSideAdd(0, v, value);
}

int laplacian_system_solve(LaplacianSystem *sys)
{
	nlEnd(NL_MATRIX);
	nlEnd(NL_SYSTEM);
	sys->nlbegun = 0;

	//nlPrintMatrix();

	return nlSolveAdvanced(NULL, NL_TRUE);
}

float laplacian_system_get_solution(int v)
{
	return nlGetVariable(0, v);
}

/************************* Heat Bone Weighting ******************************/
/* From "Automatic Rigging and Animation of 3D Characters"
		 Ilya Baran and Jovan Popovic, SIGGRAPH 2007 */

#define C_WEIGHT			1.0f
#define WEIGHT_LIMIT_START	0.05f
#define WEIGHT_LIMIT_END	0.025f
#define DISTANCE_EPSILON	1e-4f

typedef struct BVHCallbackUserData {
	float start[3];
	float vec[3];
	LaplacianSystem *sys;
} BVHCallbackUserData;

static void bvh_callback(void *userdata, int index, const BVHTreeRay *ray, BVHTreeRayHit *hit)
{
	BVHCallbackUserData *data = (struct BVHCallbackUserData*)userdata;
	MFace *mf = data->sys->heat.mface + index;
	float (*verts)[3] = data->sys->heat.verts;
	float lambda, uv[2], n[3], dir[3];

	mul_v3_v3fl(dir, data->vec, hit->dist);

	if(isect_ray_tri_v3(data->start, dir, verts[mf->v1], verts[mf->v2], verts[mf->v3], &lambda, uv)) {
		normal_tri_v3(n, verts[mf->v1], verts[mf->v2], verts[mf->v3]);
		if(lambda < 1.0f && dot_v3v3(n, data->vec) < -1e-5f) {
			hit->index = index;
			hit->dist *= lambda;
		}
	}

	mul_v3_v3fl(dir, data->vec, hit->dist);

	if(isect_ray_tri_v3(data->start, dir, verts[mf->v1], verts[mf->v3], verts[mf->v4], &lambda, uv)) {
		normal_tri_v3(n, verts[mf->v1], verts[mf->v3], verts[mf->v4]);
		if(lambda < 1.0f && dot_v3v3(n, data->vec) < -1e-5f) {
			hit->index = index;
			hit->dist *= lambda;
		}
	}
}

/* Raytracing for vertex to bone/vertex visibility */
static void heat_ray_tree_create(LaplacianSystem *sys)
{
	MFace *mface = sys->heat.mface;
	float (*verts)[3] = sys->heat.verts;
	int totface = sys->heat.totface;
	int totvert = sys->heat.totvert;
	int a;

	sys->heat.bvhtree = BLI_bvhtree_new(totface, 0.0f, 4, 6);
	sys->heat.vface = MEM_callocN(sizeof(MFace*)*totvert, "HeatVFaces");

	for(a=0; a<totface; a++) {
		MFace *mf = mface+a;
		float bb[6];

		INIT_MINMAX(bb, bb+3);
		DO_MINMAX(verts[mf->v1], bb, bb+3);
		DO_MINMAX(verts[mf->v2], bb, bb+3);
		DO_MINMAX(verts[mf->v3], bb, bb+3);
		if(mf->v4) {
			DO_MINMAX(verts[mf->v4], bb, bb+3);
		}

		BLI_bvhtree_insert(sys->heat.bvhtree, a, bb, 2);
		
		//Setup inverse pointers to use on isect.orig
		sys->heat.vface[mf->v1]= mf;
		sys->heat.vface[mf->v2]= mf;
		sys->heat.vface[mf->v3]= mf;
		if(mf->v4) sys->heat.vface[mf->v4]= mf;
	}

	BLI_bvhtree_balance(sys->heat.bvhtree); 
}

static int heat_ray_source_visible(LaplacianSystem *sys, int vertex, int source)
{
    BVHTreeRayHit hit;
	BVHCallbackUserData data;
	MFace *mface;
	float end[3];
	int visible;

	mface= sys->heat.vface[vertex];
	if(!mface)
		return 1;

	data.sys= sys;
	copy_v3_v3(data.start, sys->heat.verts[vertex]);

	if(sys->heat.root) /* bone */
		closest_to_line_segment_v3(end, data.start,
			sys->heat.root[source], sys->heat.tip[source]);
	else /* vertex */
		copy_v3_v3(end, sys->heat.source[source]);

	sub_v3_v3v3(data.vec, end, data.start);
	madd_v3_v3v3fl(data.start, data.start, data.vec, 1e-5);
	mul_v3_fl(data.vec, 1.0f - 2e-5);

	/* pass normalized vec + distance to bvh */
	hit.index = -1;
	hit.dist = normalize_v3(data.vec);

	visible= BLI_bvhtree_ray_cast(sys->heat.bvhtree, data.start, data.vec, 0.0f, &hit, bvh_callback, (void*)&data) == -1;

	return visible;
}

static float heat_source_distance(LaplacianSystem *sys, int vertex, int source)
{
	float closest[3], d[3], dist, cosine;
	
	/* compute euclidian distance */
	if(sys->heat.root) /* bone */
		closest_to_line_segment_v3(closest, sys->heat.verts[vertex],
			sys->heat.root[source], sys->heat.tip[source]);
	else /* vertex */
		copy_v3_v3(closest, sys->heat.source[source]);

	sub_v3_v3v3(d, sys->heat.verts[vertex], closest);
	dist= normalize_v3(d);

	/* if the vertex normal does not point along the bone, increase distance */
	cosine= INPR(d, sys->heat.vnors[vertex]);

	return dist/(0.5f*(cosine + 1.001f));
}

static int heat_source_closest(LaplacianSystem *sys, int vertex, int source)
{
	float dist;

	dist= heat_source_distance(sys, vertex, source);

	if(dist <= sys->heat.mindist[vertex]*(1.0f + DISTANCE_EPSILON))
		if(heat_ray_source_visible(sys, vertex, source))
			return 1;
		
	return 0;
}

static void heat_set_H(LaplacianSystem *sys, int vertex)
{
	float dist, mindist, h;
	int j, numclosest = 0;

	mindist= 1e10;

	/* compute minimum distance */
	for(j=0; j<sys->heat.numsource; j++) {
		dist= heat_source_distance(sys, vertex, j);

		if(dist < mindist)
			mindist= dist;
	}

	sys->heat.mindist[vertex]= mindist;

	/* count number of sources with approximately this minimum distance */
	for(j=0; j<sys->heat.numsource; j++)
		if(heat_source_closest(sys, vertex, j))
			numclosest++;

	sys->heat.p[vertex]= (numclosest > 0)? 1.0f/numclosest: 0.0f;

	/* compute H entry */
	if(numclosest > 0) {
		mindist= maxf(mindist, 1e-4f);
		h= numclosest*C_WEIGHT/(mindist*mindist);
	}
	else
		h= 0.0f;
	
	sys->heat.H[vertex]= h;
}

void heat_calc_vnormals(LaplacianSystem *sys)
{
	float fnor[3];
	int a, v1, v2, v3, (*face)[3];

	sys->heat.vnors= MEM_callocN(sizeof(float)*3*sys->totvert, "HeatVNors");

	for(a=0, face=sys->faces; a<sys->totface; a++, face++) {
		v1= (*face)[0];
		v2= (*face)[1];
		v3= (*face)[2];

		normal_tri_v3( fnor,sys->verts[v1], sys->verts[v2], sys->verts[v3]);
		
		add_v3_v3(sys->heat.vnors[v1], fnor);
		add_v3_v3(sys->heat.vnors[v2], fnor);
		add_v3_v3(sys->heat.vnors[v3], fnor);
	}

	for(a=0; a<sys->totvert; a++)
		normalize_v3(sys->heat.vnors[a]);
}

static void heat_laplacian_create(LaplacianSystem *sys)
{
	MFace *mface = sys->heat.mface, *mf;
	int totface= sys->heat.totface;
	int totvert= sys->heat.totvert;
	int a;

	/* heat specific definitions */
	sys->heat.mindist= MEM_callocN(sizeof(float)*totvert, "HeatMinDist");
	sys->heat.H= MEM_callocN(sizeof(float)*totvert, "HeatH");
	sys->heat.p= MEM_callocN(sizeof(float)*totvert, "HeatP");

	/* add verts and faces to laplacian */
	for(a=0; a<totvert; a++)
		laplacian_add_vertex(sys, sys->heat.verts[a], 0);

	for(a=0, mf=mface; a<totface; a++, mf++) {
		laplacian_add_triangle(sys, mf->v1, mf->v2, mf->v3);
		if(mf->v4)
			laplacian_add_triangle(sys, mf->v1, mf->v3, mf->v4);
	}

	/* for distance computation in set_H */
	heat_calc_vnormals(sys);

	for(a=0; a<totvert; a++)
		heat_set_H(sys, a);
}

static void heat_system_free(LaplacianSystem *sys)
{
	BLI_bvhtree_free(sys->heat.bvhtree);
	MEM_freeN(sys->heat.vface);

	MEM_freeN(sys->heat.mindist);
	MEM_freeN(sys->heat.H);
	MEM_freeN(sys->heat.p);
	MEM_freeN(sys->heat.vnors);
}

static float heat_limit_weight(float weight)
{
	float t;

	if(weight < WEIGHT_LIMIT_END) {
		return 0.0f;
	}
	else if(weight < WEIGHT_LIMIT_START) {
		t= (weight - WEIGHT_LIMIT_END)/(WEIGHT_LIMIT_START - WEIGHT_LIMIT_END);
		return t*WEIGHT_LIMIT_START;
	}
	else
		return weight;
}

void heat_bone_weighting(Object *ob, Mesh *me, float (*verts)[3], int numsource, bDeformGroup **dgrouplist, bDeformGroup **dgroupflip, float (*root)[3], float (*tip)[3], int *selected)
{
	LaplacianSystem *sys;
	MFace *mface;
	float solution, weight;
	int *vertsflipped = NULL, *mask= NULL;
	int a, totface, j, bbone, firstsegment, lastsegment, thrownerror = 0;

	/* count triangles and create mask */
	if(me->editflag & ME_EDIT_PAINT_MASK)
		mask= MEM_callocN(sizeof(int)*me->totvert, "heat_bone_weighting mask");

	for(totface=0, a=0, mface=me->mface; a<me->totface; a++, mface++) {
		totface++;
		if(mface->v4) totface++;

		if(mask && (mface->flag & ME_FACE_SEL)) {
			mask[mface->v1]= 1;
			mask[mface->v2]= 1;
			mask[mface->v3]= 1;
			if(mface->v4)
				mask[mface->v4]= 1;
		}
	}

	/* create laplacian */
	sys = laplacian_system_construct_begin(me->totvert, totface, 1);

	sys->heat.mface= me->mface;
	sys->heat.totface= me->totface;
	sys->heat.totvert= me->totvert;
	sys->heat.verts= verts;
	sys->heat.root= root;
	sys->heat.tip= tip;
	sys->heat.numsource= numsource;

	heat_ray_tree_create(sys);
	heat_laplacian_create(sys);

	laplacian_system_construct_end(sys);

	if(dgroupflip) {
		vertsflipped = MEM_callocN(sizeof(int)*me->totvert, "vertsflipped");
		for(a=0; a<me->totvert; a++)
			vertsflipped[a] = mesh_get_x_mirror_vert(ob, a);
	}

	/* compute weights per bone */
	for(j=0; j<numsource; j++) {
		if(!selected[j])
			continue;

		firstsegment= (j == 0 || dgrouplist[j-1] != dgrouplist[j]);
		lastsegment= (j == numsource-1 || dgrouplist[j] != dgrouplist[j+1]);
		bbone= !(firstsegment && lastsegment);

		/* clear weights */
		if(bbone && firstsegment) {
			for(a=0; a<me->totvert; a++) {
				if(mask && !mask[a])
					continue;

				ED_vgroup_vert_remove(ob, dgrouplist[j], a);
				if(vertsflipped && dgroupflip[j] && vertsflipped[a] >= 0)
					ED_vgroup_vert_remove(ob, dgroupflip[j], vertsflipped[a]);
			}
		}

		/* fill right hand side */
		laplacian_begin_solve(sys, -1);

		for(a=0; a<me->totvert; a++)
			if(heat_source_closest(sys, a, j))
				laplacian_add_right_hand_side(sys, a,
					sys->heat.H[a]*sys->heat.p[a]);

		/* solve */
		if(laplacian_system_solve(sys)) {
			/* load solution into vertex groups */
			for(a=0; a<me->totvert; a++) {
				if(mask && !mask[a])
					continue;

				solution= laplacian_system_get_solution(a);
				
				if(bbone) {
					if(solution > 0.0f)
						ED_vgroup_vert_add(ob, dgrouplist[j], a, solution,
							WEIGHT_ADD);
				}
				else {
					weight= heat_limit_weight(solution);
					if(weight > 0.0f)
						ED_vgroup_vert_add(ob, dgrouplist[j], a, weight,
							WEIGHT_REPLACE);
					else
						ED_vgroup_vert_remove(ob, dgrouplist[j], a);
				}

				/* do same for mirror */
				if(vertsflipped && dgroupflip[j] && vertsflipped[a] >= 0) {
					if(bbone) {
						if(solution > 0.0f)
							ED_vgroup_vert_add(ob, dgroupflip[j], vertsflipped[a],
								solution, WEIGHT_ADD);
					}
					else {
						weight= heat_limit_weight(solution);
						if(weight > 0.0f)
							ED_vgroup_vert_add(ob, dgroupflip[j], vertsflipped[a],
								weight, WEIGHT_REPLACE);
						else
							ED_vgroup_vert_remove(ob, dgroupflip[j], vertsflipped[a]);
					}
				}
			}
		}
		else if(!thrownerror) {
			error("Bone Heat Weighting:"
				" failed to find solution for one or more bones");
			thrownerror= 1;
			break;
		}

		/* remove too small vertex weights */
		if(bbone && lastsegment) {
			for(a=0; a<me->totvert; a++) {
				if(mask && !mask[a])
					continue;

				weight= ED_vgroup_vert_weight(ob, dgrouplist[j], a);
				weight= heat_limit_weight(weight);
				if(weight <= 0.0f)
					ED_vgroup_vert_remove(ob, dgrouplist[j], a);

				if(vertsflipped && dgroupflip[j] && vertsflipped[a] >= 0) {
					weight= ED_vgroup_vert_weight(ob, dgroupflip[j], vertsflipped[a]);
					weight= heat_limit_weight(weight);
					if(weight <= 0.0f)
						ED_vgroup_vert_remove(ob, dgroupflip[j], vertsflipped[a]);
				}
			}
		}
	}

	/* free */
	if(vertsflipped) MEM_freeN(vertsflipped);
	if(mask) MEM_freeN(mask);

	heat_system_free(sys);

	laplacian_system_delete(sys);
}

#ifdef RIGID_DEFORM
/********************** As-Rigid-As-Possible Deformation ******************/
/* From "As-Rigid-As-Possible Surface Modeling",
		Olga Sorkine and Marc Alexa, ESGP 2007. */

/* investigate:
   - transpose R in orthogonal
   - flipped normals and per face adding
   - move cancelling to transform, make origco pointer
*/

static LaplacianSystem *RigidDeformSystem = NULL;

static void rigid_add_half_edge_to_R(LaplacianSystem *sys, EditVert *v1, EditVert *v2, float w)
{
	float e[3], e_[3];
	int i;

	sub_v3_v3v3(e, sys->rigid.origco[v1->tmp.l], sys->rigid.origco[v2->tmp.l]);
	sub_v3_v3v3(e_, v1->co, v2->co);

	/* formula (5) */
	for (i=0; i<3; i++) {
		sys->rigid.R[v1->tmp.l][i][0] += w*e[0]*e_[i];
		sys->rigid.R[v1->tmp.l][i][1] += w*e[1]*e_[i];
		sys->rigid.R[v1->tmp.l][i][2] += w*e[2]*e_[i];
	}
}

static void rigid_add_edge_to_R(LaplacianSystem *sys, EditVert *v1, EditVert *v2, float w)
{
	rigid_add_half_edge_to_R(sys, v1, v2, w);
	rigid_add_half_edge_to_R(sys, v2, v1, w);
}

static void rigid_orthogonalize_R(float R[][3])
{
	HMatrix M, Q, S;

	copy_m4_m3(M, R);
	polar_decomp(M, Q, S);
	copy_m3_m4(R, Q);
}

static void rigid_add_half_edge_to_rhs(LaplacianSystem *sys, EditVert *v1, EditVert *v2, float w)
{
	/* formula (8) */
	float Rsum[3][3], rhs[3];

	if (sys->vpinned[v1->tmp.l])
		return;

	add_m3_m3m3(Rsum, sys->rigid.R[v1->tmp.l], sys->rigid.R[v2->tmp.l]);
	transpose_m3(Rsum);

	sub_v3_v3v3(rhs, sys->rigid.origco[v1->tmp.l], sys->rigid.origco[v2->tmp.l]);
	mul_m3_v3(Rsum, rhs);
	mul_v3_fl(rhs, 0.5f);
	mul_v3_fl(rhs, w);

	add_v3_v3(sys->rigid.rhs[v1->tmp.l], rhs);
}

static void rigid_add_edge_to_rhs(LaplacianSystem *sys, EditVert *v1, EditVert *v2, float w)
{
	rigid_add_half_edge_to_rhs(sys, v1, v2, w);
	rigid_add_half_edge_to_rhs(sys, v2, v1, w);
}

void rigid_deform_iteration()
{
	LaplacianSystem *sys= RigidDeformSystem;
	EditMesh *em;
	EditVert *eve;
	EditFace *efa;
	int a, i;

	if(!sys)
		return;
	
	nlMakeCurrent(sys->context);
	em= sys->rigid.mesh;

	/* compute R */
	memset(sys->rigid.R, 0, sizeof(float)*3*3*sys->totvert);
	memset(sys->rigid.rhs, 0, sizeof(float)*3*sys->totvert);

	for(a=0, efa=em->faces.first; efa; efa=efa->next, a++) {
		rigid_add_edge_to_R(sys, efa->v1, efa->v2, sys->fweights[a][2]);
		rigid_add_edge_to_R(sys, efa->v2, efa->v3, sys->fweights[a][0]);
		rigid_add_edge_to_R(sys, efa->v3, efa->v1, sys->fweights[a][1]);

		if(efa->v4) {
			a++;
			rigid_add_edge_to_R(sys, efa->v1, efa->v3, sys->fweights[a][2]);
			rigid_add_edge_to_R(sys, efa->v3, efa->v4, sys->fweights[a][0]);
			rigid_add_edge_to_R(sys, efa->v4, efa->v1, sys->fweights[a][1]);
		}
	}

	for(a=0, eve=em->verts.first; eve; eve=eve->next, a++) {
		rigid_orthogonalize_R(sys->rigid.R[a]);
		eve->tmp.l= a;
	}
	
	/* compute right hand sides for solving */
	for(a=0, efa=em->faces.first; efa; efa=efa->next, a++) {
		rigid_add_edge_to_rhs(sys, efa->v1, efa->v2, sys->fweights[a][2]);
		rigid_add_edge_to_rhs(sys, efa->v2, efa->v3, sys->fweights[a][0]);
		rigid_add_edge_to_rhs(sys, efa->v3, efa->v1, sys->fweights[a][1]);

		if(efa->v4) {
			a++;
			rigid_add_edge_to_rhs(sys, efa->v1, efa->v3, sys->fweights[a][2]);
			rigid_add_edge_to_rhs(sys, efa->v3, efa->v4, sys->fweights[a][0]);
			rigid_add_edge_to_rhs(sys, efa->v4, efa->v1, sys->fweights[a][1]);
		}
	}

	/* solve for positions, for X,Y and Z separately */
	for(i=0; i<3; i++) {
		laplacian_begin_solve(sys, i);

		for(a=0; a<sys->totvert; a++)
			if(!sys->vpinned[a])
				laplacian_add_right_hand_side(sys, a, sys->rigid.rhs[a][i]);

		if(laplacian_system_solve(sys)) {
			for(a=0, eve=em->verts.first; eve; eve=eve->next, a++)
				eve->co[i]= laplacian_system_get_solution(a);
		}
		else {
			if(!sys->rigid.thrownerror) {
				error("RigidDeform: failed to find solution.");
				sys->rigid.thrownerror= 1;
			}
			break;
		}
	}
}

static void rigid_laplacian_create(LaplacianSystem *sys)
{
	EditMesh *em = sys->rigid.mesh;
	EditVert *eve;
	EditFace *efa;
	int a;

	/* add verts and faces to laplacian */
	for(a=0, eve=em->verts.first; eve; eve=eve->next, a++) {
		laplacian_add_vertex(sys, eve->co, eve->pinned);
		eve->tmp.l= a;
	}

	for(efa=em->faces.first; efa; efa=efa->next) {
		laplacian_add_triangle(sys,
			efa->v1->tmp.l, efa->v2->tmp.l, efa->v3->tmp.l);
		if(efa->v4)
			laplacian_add_triangle(sys,
				efa->v1->tmp.l, efa->v3->tmp.l, efa->v4->tmp.l);
	}
}

void rigid_deform_begin(EditMesh *em)
{
	LaplacianSystem *sys;
	EditVert *eve;
	EditFace *efa;
	int a, totvert, totface;

	/* count vertices, triangles */
	for(totvert=0, eve=em->verts.first; eve; eve=eve->next)
		totvert++;

	for(totface=0, efa=em->faces.first; efa; efa=efa->next) {
		totface++;
		if(efa->v4) totface++;
	}

	/* create laplacian */
	sys = laplacian_system_construct_begin(totvert, totface, 0);

	sys->rigid.mesh= em;
	sys->rigid.R = MEM_callocN(sizeof(float)*3*3*totvert, "RigidDeformR");
	sys->rigid.rhs = MEM_callocN(sizeof(float)*3*totvert, "RigidDeformRHS");
	sys->rigid.origco = MEM_callocN(sizeof(float)*3*totvert, "RigidDeformCo");

	for(a=0, eve=em->verts.first; eve; eve=eve->next, a++)
		copy_v3_v3(sys->rigid.origco[a], eve->co);

	sys->areaweights= 0;
	sys->storeweights= 1;

	rigid_laplacian_create(sys);

	laplacian_system_construct_end(sys);

	RigidDeformSystem = sys;
}

void rigid_deform_end(int cancel)
{
	LaplacianSystem *sys = RigidDeformSystem;

	if(sys) {
		EditMesh *em = sys->rigid.mesh;
		EditVert *eve;
		int a;

		if(cancel)
			for(a=0, eve=em->verts.first; eve; eve=eve->next, a++)
				if(!eve->pinned)
					copy_v3_v3(eve->co, sys->rigid.origco[a]);

		if(sys->rigid.R) MEM_freeN(sys->rigid.R);
		if(sys->rigid.rhs) MEM_freeN(sys->rigid.rhs);
		if(sys->rigid.origco) MEM_freeN(sys->rigid.origco);

		/* free */
		laplacian_system_delete(sys);
	}

	RigidDeformSystem = NULL;
}
#endif

/************************** Harmonic Coordinates ****************************/
/* From "Harmonic Coordinates for Character Articulation",
	Pushkar Joshi, Mark Meyer, Tony DeRose, Brian Green and Tom Sanocki,
	SIGGRAPH 2007. */

#define EPSILON 0.0001f

#define MESHDEFORM_TAG_UNTYPED  0
#define MESHDEFORM_TAG_BOUNDARY 1
#define MESHDEFORM_TAG_INTERIOR 2
#define MESHDEFORM_TAG_EXTERIOR 3

#define MESHDEFORM_LEN_THRESHOLD 1e-6

#define MESHDEFORM_MIN_INFLUENCE 0.0005

static int MESHDEFORM_OFFSET[7][3] =
		{{0,0,0}, {1,0,0}, {-1,0,0}, {0,1,0}, {0,-1,0}, {0,0,1}, {0,0,-1}};

typedef struct MDefBoundIsect {
	float co[3], uvw[4];
	int nvert, v[4], facing;
	float len;
} MDefBoundIsect;

typedef struct MDefBindInfluence {
	struct MDefBindInfluence *next;
	float weight;
	int vertex;
} MDefBindInfluence;

typedef struct MeshDeformBind {
	/* grid dimensions */
	float min[3], max[3];
	float width[3], halfwidth[3];
	int size, size3;

	/* meshes */
	DerivedMesh *cagedm;
	float (*cagecos)[3];
	float (*vertexcos)[3];
	int totvert, totcagevert;

	/* grids */
	MemArena *memarena;
	MDefBoundIsect *(*boundisect)[6];
	int *semibound;
	int *tag;
	float *phi, *totalphi;

	/* mesh stuff */
	int *inside;
	float *weights;
	MDefBindInfluence **dyngrid;
	float cagemat[4][4];

	/* direct solver */
	int *varidx;
} MeshDeformBind;

typedef struct MeshDeformIsect {
	float start[3];
	float vec[3];
	float labda;

	void *face;
	int isect;
	float u, v;
	
} MeshDeformIsect;

/* ray intersection */

/* our own triangle intersection, so we can fully control the epsilons and
 * prevent corner case from going wrong*/
static int meshdeform_tri_intersect(float orig[3], float end[3], float vert0[3],
	float vert1[3], float vert2[3], float *isectco, float *uvw)
{
	float edge1[3], edge2[3], tvec[3], pvec[3], qvec[3];
	float det,inv_det, u, v, dir[3], isectdir[3];

	sub_v3_v3v3(dir, end, orig);

	/* find vectors for two edges sharing vert0 */
	sub_v3_v3v3(edge1, vert1, vert0);
	sub_v3_v3v3(edge2, vert2, vert0);

	/* begin calculating determinant - also used to calculate U parameter */
	cross_v3_v3v3(pvec, dir, edge2);

	/* if determinant is near zero, ray lies in plane of triangle */
	det = INPR(edge1, pvec);

	if (det == 0.0f)
	  return 0;
	inv_det = 1.0f / det;

	/* calculate distance from vert0 to ray origin */
	sub_v3_v3v3(tvec, orig, vert0);

	/* calculate U parameter and test bounds */
	u = INPR(tvec, pvec) * inv_det;
	if (u < -EPSILON || u > 1.0f+EPSILON)
	  return 0;

	/* prepare to test V parameter */
	cross_v3_v3v3(qvec, tvec, edge1);

	/* calculate V parameter and test bounds */
	v = INPR(dir, qvec) * inv_det;
	if (v < -EPSILON || u + v > 1.0f+EPSILON)
	  return 0;

	isectco[0]= (1.0f - u - v)*vert0[0] + u*vert1[0] + v*vert2[0];
	isectco[1]= (1.0f - u - v)*vert0[1] + u*vert1[1] + v*vert2[1];
	isectco[2]= (1.0f - u - v)*vert0[2] + u*vert1[2] + v*vert2[2];

	uvw[0]= 1.0 - u - v;
	uvw[1]= u;
	uvw[2]= v;

	/* check if it is within the length of the line segment */
	sub_v3_v3v3(isectdir, isectco, orig);

	if(INPR(dir, isectdir) < -EPSILON)
		return 0;
	
	if(INPR(dir, dir) + EPSILON < INPR(isectdir, isectdir))
		return 0;

	return 1;
}

static int meshdeform_intersect(MeshDeformBind *mdb, MeshDeformIsect *isec)
{
	MFace *mface;
	float face[4][3], co[3], uvw[3], len, nor[3], end[3];
	int f, hit, is= 0, totface;

	isec->labda= 1e10;

	mface= mdb->cagedm->getTessFaceArray(mdb->cagedm);
	totface= mdb->cagedm->getNumTessFaces(mdb->cagedm);

	add_v3_v3v3(end, isec->start, isec->vec);

	for(f=0; f<totface; f++, mface++) {
		copy_v3_v3(face[0], mdb->cagecos[mface->v1]);
		copy_v3_v3(face[1], mdb->cagecos[mface->v2]);
		copy_v3_v3(face[2], mdb->cagecos[mface->v3]);

		if(mface->v4) {
			copy_v3_v3(face[3], mdb->cagecos[mface->v4]);
			hit = meshdeform_tri_intersect(isec->start, end, face[0], face[1], face[2], co, uvw);

			if(hit) {
				normal_tri_v3( nor,face[0], face[1], face[2]);
			}
			else {
				hit= meshdeform_tri_intersect(isec->start, end, face[0], face[2], face[3], co, uvw);
				normal_tri_v3( nor,face[0], face[2], face[3]);
			}
		}
		else {
			hit= meshdeform_tri_intersect(isec->start, end, face[0], face[1], face[2], co, uvw);
			normal_tri_v3( nor,face[0], face[1], face[2]);
		}

		if(hit) {
			len= len_v3v3(isec->start, co)/len_v3v3(isec->start, end);
			if(len < isec->labda) {
				isec->labda= len;
				isec->face = mface;
				isec->isect= (INPR(isec->vec, nor) <= 0.0f);
				is= 1;
			}
		}
	}

	return is;
}

static MDefBoundIsect *meshdeform_ray_tree_intersect(MeshDeformBind *mdb, float *co1, float *co2)
{
	MDefBoundIsect *isect;
	MeshDeformIsect isec;
	float (*cagecos)[3];
	MFace *mface;
	float vert[4][3], len, end[3];
	static float epsilon[3]= {0, 0, 0}; //1e-4, 1e-4, 1e-4};

	/* setup isec */
	memset(&isec, 0, sizeof(isec));
	isec.labda= 1e10f;

	VECADD(isec.start, co1, epsilon);
	VECADD(end, co2, epsilon);
	sub_v3_v3v3(isec.vec, end, isec.start);

	if(meshdeform_intersect(mdb, &isec)) {
		len= isec.labda;
		mface=(MFace*)isec.face;

		/* create MDefBoundIsect */
		isect= BLI_memarena_alloc(mdb->memarena, sizeof(*isect));

		/* compute intersection coordinate */
		isect->co[0]= co1[0] + isec.vec[0]*len;
		isect->co[1]= co1[1] + isec.vec[1]*len;
		isect->co[2]= co1[2] + isec.vec[2]*len;

		isect->len= len_v3v3(co1, isect->co);
		if(isect->len < MESHDEFORM_LEN_THRESHOLD)
			isect->len= MESHDEFORM_LEN_THRESHOLD;

		isect->v[0]= mface->v1;
		isect->v[1]= mface->v2;
		isect->v[2]= mface->v3;
		isect->v[3]= mface->v4;
		isect->nvert= (mface->v4)? 4: 3;

		isect->facing= isec.isect;

		/* compute mean value coordinates for interpolation */
		cagecos= mdb->cagecos;
		copy_v3_v3(vert[0], cagecos[mface->v1]);
		copy_v3_v3(vert[1], cagecos[mface->v2]);
		copy_v3_v3(vert[2], cagecos[mface->v3]);
		if(mface->v4) copy_v3_v3(vert[3], cagecos[mface->v4]);
		interp_weights_poly_v3( isect->uvw,vert, isect->nvert, isect->co);

		return isect;
	}

	return NULL;
}

static int meshdeform_inside_cage(MeshDeformBind *mdb, float *co)
{
	MDefBoundIsect *isect;
	float outside[3], start[3], dir[3];
	int i, counter;

	for(i=1; i<=6; i++) {
		counter = 0;

		outside[0] = co[0] + (mdb->max[0] - mdb->min[0] + 1.0f)*MESHDEFORM_OFFSET[i][0];
		outside[1] = co[1] + (mdb->max[1] - mdb->min[1] + 1.0f)*MESHDEFORM_OFFSET[i][1];
		outside[2] = co[2] + (mdb->max[2] - mdb->min[2] + 1.0f)*MESHDEFORM_OFFSET[i][2];

		copy_v3_v3(start, co);
		sub_v3_v3v3(dir, outside, start);
		normalize_v3(dir);
		
		isect = meshdeform_ray_tree_intersect(mdb, start, outside);
		if(isect && !isect->facing)
			return 1;
	}

	return 0;
}

/* solving */

static int meshdeform_index(MeshDeformBind *mdb, int x, int y, int z, int n)
{
	int size= mdb->size;
	
	x += MESHDEFORM_OFFSET[n][0];
	y += MESHDEFORM_OFFSET[n][1];
	z += MESHDEFORM_OFFSET[n][2];

	if(x < 0 || x >= mdb->size)
		return -1;
	if(y < 0 || y >= mdb->size)
		return -1;
	if(z < 0 || z >= mdb->size)
		return -1;

	return x + y*size + z*size*size;
}

static void meshdeform_cell_center(MeshDeformBind *mdb, int x, int y, int z, int n, float *center)
{
	x += MESHDEFORM_OFFSET[n][0];
	y += MESHDEFORM_OFFSET[n][1];
	z += MESHDEFORM_OFFSET[n][2];

	center[0]= mdb->min[0] + x*mdb->width[0] + mdb->halfwidth[0];
	center[1]= mdb->min[1] + y*mdb->width[1] + mdb->halfwidth[1];
	center[2]= mdb->min[2] + z*mdb->width[2] + mdb->halfwidth[2];
}

static void meshdeform_add_intersections(MeshDeformBind *mdb, int x, int y, int z)
{
	MDefBoundIsect *isect;
	float center[3], ncenter[3];
	int i, a;

	a= meshdeform_index(mdb, x, y, z, 0);
	meshdeform_cell_center(mdb, x, y, z, 0, center);

	/* check each outgoing edge for intersection */
	for(i=1; i<=6; i++) {
		if(meshdeform_index(mdb, x, y, z, i) == -1)
			continue;

		meshdeform_cell_center(mdb, x, y, z, i, ncenter);

		isect= meshdeform_ray_tree_intersect(mdb, center, ncenter);
		if(isect) {
			mdb->boundisect[a][i-1]= isect;
			mdb->tag[a]= MESHDEFORM_TAG_BOUNDARY;
		}
	}
}

static void meshdeform_bind_floodfill(MeshDeformBind *mdb)
{
	int *stack, *tag= mdb->tag;
	int a, b, i, xyz[3], stacksize, size= mdb->size;

	stack= MEM_callocN(sizeof(int)*mdb->size3, "MeshDeformBindStack");

	/* we know lower left corner is EXTERIOR because of padding */
	tag[0]= MESHDEFORM_TAG_EXTERIOR;
	stack[0]= 0;
	stacksize= 1;

	/* floodfill exterior tag */
	while(stacksize > 0) {
		a= stack[--stacksize];

		xyz[2]= a/(size*size);
		xyz[1]= (a - xyz[2]*size*size)/size;
		xyz[0]= a - xyz[1]*size - xyz[2]*size*size;

		for(i=1; i<=6; i++) {
			b= meshdeform_index(mdb, xyz[0], xyz[1], xyz[2], i);

			if(b != -1) {
				if(tag[b] == MESHDEFORM_TAG_UNTYPED ||
				   (tag[b] == MESHDEFORM_TAG_BOUNDARY && !mdb->boundisect[a][i-1])) {
					tag[b]= MESHDEFORM_TAG_EXTERIOR;
					stack[stacksize++]= b;
				}
			}
		}
	}

	/* other cells are interior */
	for(a=0; a<size*size*size; a++)
		if(tag[a]==MESHDEFORM_TAG_UNTYPED)
			tag[a]= MESHDEFORM_TAG_INTERIOR;

#if 0
	{
		int tb, ti, te, ts;
		tb= ti= te= ts= 0;
		for(a=0; a<size*size*size; a++)
			if(tag[a]==MESHDEFORM_TAG_BOUNDARY)
				tb++;
			else if(tag[a]==MESHDEFORM_TAG_INTERIOR)
				ti++;
			else if(tag[a]==MESHDEFORM_TAG_EXTERIOR) {
				te++;

				if(mdb->semibound[a])
					ts++;
			}
		
		printf("interior %d exterior %d boundary %d semi-boundary %d\n", ti, te, tb, ts);
	}
#endif

	MEM_freeN(stack);
}

static float meshdeform_boundary_phi(MeshDeformBind *mdb, MDefBoundIsect *isect, int cagevert)
{
	int a;

	for(a=0; a<isect->nvert; a++)
		if(isect->v[a] == cagevert)
			return isect->uvw[a];
	
	return 0.0f;
}

static float meshdeform_interp_w(MeshDeformBind *mdb, float *gridvec, float *vec, int cagevert)
{
	float dvec[3], ivec[3], wx, wy, wz, result=0.0f;
	float weight, totweight= 0.0f;
	int i, a, x, y, z;

	for(i=0; i<3; i++) {
		ivec[i]= (int)gridvec[i];
		dvec[i]= gridvec[i] - ivec[i];
	}

	for(i=0; i<8; i++) {
		if(i & 1) { x= ivec[0]+1; wx= dvec[0]; }
		else { x= ivec[0]; wx= 1.0f-dvec[0]; } 

		if(i & 2) { y= ivec[1]+1; wy= dvec[1]; }
		else { y= ivec[1]; wy= 1.0f-dvec[1]; } 

		if(i & 4) { z= ivec[2]+1; wz= dvec[2]; }
		else { z= ivec[2]; wz= 1.0f-dvec[2]; } 

		CLAMP(x, 0, mdb->size-1);
		CLAMP(y, 0, mdb->size-1);
		CLAMP(z, 0, mdb->size-1);

		a= meshdeform_index(mdb, x, y, z, 0);
		weight= wx*wy*wz;
		result += weight*mdb->phi[a];
		totweight += weight;
	}

	if(totweight > 0.0f)
		result /= totweight;

	return result;
}

static void meshdeform_check_semibound(MeshDeformBind *mdb, int x, int y, int z)
{
	int i, a;

	a= meshdeform_index(mdb, x, y, z, 0);
	if(mdb->tag[a] != MESHDEFORM_TAG_EXTERIOR)
		return;

	for(i=1; i<=6; i++)
		if(mdb->boundisect[a][i-1]) 
			mdb->semibound[a]= 1;
}

static float meshdeform_boundary_total_weight(MeshDeformBind *mdb, int x, int y, int z)
{
	float weight, totweight= 0.0f;
	int i, a;

	a= meshdeform_index(mdb, x, y, z, 0);

	/* count weight for neighbour cells */
	for(i=1; i<=6; i++) {
		if(meshdeform_index(mdb, x, y, z, i) == -1)
			continue;

		if(mdb->boundisect[a][i-1])
			weight= 1.0f/mdb->boundisect[a][i-1]->len;
		else if(!mdb->semibound[a])
			weight= 1.0f/mdb->width[0];
		else
			weight= 0.0f;

		totweight += weight;
	}

	return totweight;
}

static void meshdeform_matrix_add_cell(MeshDeformBind *mdb, int x, int y, int z)
{
	MDefBoundIsect *isect;
	float weight, totweight;
	int i, a, acenter;

	acenter= meshdeform_index(mdb, x, y, z, 0);
	if(mdb->tag[acenter] == MESHDEFORM_TAG_EXTERIOR)
		return;

	nlMatrixAdd(mdb->varidx[acenter], mdb->varidx[acenter], 1.0f);
	
	totweight= meshdeform_boundary_total_weight(mdb, x, y, z);
	for(i=1; i<=6; i++) {
		a= meshdeform_index(mdb, x, y, z, i);
		if(a == -1 || mdb->tag[a] == MESHDEFORM_TAG_EXTERIOR)
			continue;

		isect= mdb->boundisect[acenter][i-1];
		if (!isect) {
			weight= (1.0f/mdb->width[0])/totweight;
			nlMatrixAdd(mdb->varidx[acenter], mdb->varidx[a], -weight);
		}
	}
}

static void meshdeform_matrix_add_rhs(MeshDeformBind *mdb, int x, int y, int z, int cagevert)
{
	MDefBoundIsect *isect;
	float rhs, weight, totweight;
	int i, a, acenter;

	acenter= meshdeform_index(mdb, x, y, z, 0);
	if(mdb->tag[acenter] == MESHDEFORM_TAG_EXTERIOR)
		return;

	totweight= meshdeform_boundary_total_weight(mdb, x, y, z);
	for(i=1; i<=6; i++) {
		a= meshdeform_index(mdb, x, y, z, i);
		if(a == -1)
			continue;

		isect= mdb->boundisect[acenter][i-1];

		if (isect) {
			weight= (1.0f/isect->len)/totweight;
			rhs= weight*meshdeform_boundary_phi(mdb, isect, cagevert);
			nlRightHandSideAdd(0, mdb->varidx[acenter], rhs);
		}
	}
}

static void meshdeform_matrix_add_semibound_phi(MeshDeformBind *mdb, int x, int y, int z, int cagevert)
{
	MDefBoundIsect *isect;
	float rhs, weight, totweight;
	int i, a;

	a= meshdeform_index(mdb, x, y, z, 0);
	if(!mdb->semibound[a])
		return;
	
	mdb->phi[a]= 0.0f;

	totweight= meshdeform_boundary_total_weight(mdb, x, y, z);
	for(i=1; i<=6; i++) {
		isect= mdb->boundisect[a][i-1];

		if (isect) {
			weight= (1.0f/isect->len)/totweight;
			rhs= weight*meshdeform_boundary_phi(mdb, isect, cagevert);
			mdb->phi[a] += rhs;
		}
	}
}

static void meshdeform_matrix_add_exterior_phi(MeshDeformBind *mdb, int x, int y, int z, int cagevert)
{
	float phi, totweight;
	int i, a, acenter;

	acenter= meshdeform_index(mdb, x, y, z, 0);
	if(mdb->tag[acenter] != MESHDEFORM_TAG_EXTERIOR || mdb->semibound[acenter])
		return;

	phi= 0.0f;
	totweight= 0.0f;
	for(i=1; i<=6; i++) {
		a= meshdeform_index(mdb, x, y, z, i);

		if(a != -1 && mdb->semibound[a]) {
			phi += mdb->phi[a];
			totweight += 1.0f;
		}
	}

	if(totweight != 0.0f)
		mdb->phi[acenter]= phi/totweight;
}

static void meshdeform_matrix_solve(MeshDeformBind *mdb)
{
	NLContext *context;
	float vec[3], gridvec[3];
	int a, b, x, y, z, totvar;
	char message[1024];

	/* setup variable indices */
	mdb->varidx= MEM_callocN(sizeof(int)*mdb->size3, "MeshDeformDSvaridx");
	for(a=0, totvar=0; a<mdb->size3; a++)
		mdb->varidx[a]= (mdb->tag[a] == MESHDEFORM_TAG_EXTERIOR)? -1: totvar++;

	if(totvar == 0) {
		MEM_freeN(mdb->varidx);
		return;
	}

	progress_bar(0, "Starting mesh deform solve");

	/* setup opennl solver */
	nlNewContext();
	context= nlGetCurrent();

	nlSolverParameteri(NL_NB_VARIABLES, totvar);
	nlSolverParameteri(NL_NB_ROWS, totvar);
	nlSolverParameteri(NL_NB_RIGHT_HAND_SIDES, 1);

	nlBegin(NL_SYSTEM);
	nlBegin(NL_MATRIX);

	/* build matrix */
	for(z=0; z<mdb->size; z++)
		for(y=0; y<mdb->size; y++)
			for(x=0; x<mdb->size; x++)
				meshdeform_matrix_add_cell(mdb, x, y, z);

	/* solve for each cage vert */
	for(a=0; a<mdb->totcagevert; a++) {
		if(a != 0) {
			nlBegin(NL_SYSTEM);
			nlBegin(NL_MATRIX);
		}

		/* fill in right hand side and solve */
		for(z=0; z<mdb->size; z++)
			for(y=0; y<mdb->size; y++)
				for(x=0; x<mdb->size; x++)
					meshdeform_matrix_add_rhs(mdb, x, y, z, a);

		nlEnd(NL_MATRIX);
		nlEnd(NL_SYSTEM);

#if 0
		nlPrintMatrix();
#endif

		if(nlSolveAdvanced(NULL, NL_TRUE)) {
			for(z=0; z<mdb->size; z++)
				for(y=0; y<mdb->size; y++)
					for(x=0; x<mdb->size; x++)
						meshdeform_matrix_add_semibound_phi(mdb, x, y, z, a);

			for(z=0; z<mdb->size; z++)
				for(y=0; y<mdb->size; y++)
					for(x=0; x<mdb->size; x++)
						meshdeform_matrix_add_exterior_phi(mdb, x, y, z, a);

			for(b=0; b<mdb->size3; b++) {
				if(mdb->tag[b] != MESHDEFORM_TAG_EXTERIOR)
					mdb->phi[b]= nlGetVariable(0, mdb->varidx[b]);
				mdb->totalphi[b] += mdb->phi[b];
			}

			if(mdb->weights) {
				/* static bind : compute weights for each vertex */
				for(b=0; b<mdb->totvert; b++) {
					if(mdb->inside[b]) {
						copy_v3_v3(vec, mdb->vertexcos[b]);
						gridvec[0]= (vec[0] - mdb->min[0] - mdb->halfwidth[0])/mdb->width[0];
						gridvec[1]= (vec[1] - mdb->min[1] - mdb->halfwidth[1])/mdb->width[1];
						gridvec[2]= (vec[2] - mdb->min[2] - mdb->halfwidth[2])/mdb->width[2];

						mdb->weights[b*mdb->totcagevert + a]= meshdeform_interp_w(mdb, gridvec, vec, a);
					}
				}
			}
			else {
				MDefBindInfluence *inf;

				/* dynamic bind */
				for(b=0; b<mdb->size3; b++) {
					if(mdb->phi[b] >= MESHDEFORM_MIN_INFLUENCE) {
						inf= BLI_memarena_alloc(mdb->memarena, sizeof(*inf));
						inf->vertex= a;
						inf->weight= mdb->phi[b];
						inf->next= mdb->dyngrid[b];
						mdb->dyngrid[b]= inf;
					}
				}
			}
		}
		else {
			error("Mesh Deform: failed to find solution.");
			break;
		}

		sprintf(message, "Mesh deform solve %d / %d       |||", a+1, mdb->totcagevert);
		progress_bar((float)(a+1)/(float)(mdb->totcagevert), message);
	}

#if 0
	/* sanity check */
	for(b=0; b<mdb->size3; b++)
		if(mdb->tag[b] != MESHDEFORM_TAG_EXTERIOR)
			if(fabs(mdb->totalphi[b] - 1.0f) > 1e-4)
				printf("totalphi deficiency [%s|%d] %d: %.10f\n",
					(mdb->tag[b] == MESHDEFORM_TAG_INTERIOR)? "interior": "boundary", mdb->semibound[b], mdb->varidx[b], mdb->totalphi[b]);
#endif
	
	/* free */
	MEM_freeN(mdb->varidx);

	nlDeleteContext(context);
}

static void harmonic_coordinates_bind(Scene *scene, MeshDeformModifierData *mmd, MeshDeformBind *mdb)
{
	MDefBindInfluence *inf;
	MDefInfluence *mdinf;
	MDefCell *cell;
	float center[3], vec[3], maxwidth, totweight;
	int a, b, x, y, z, totinside, offset;

	/* compute bounding box of the cage mesh */
	INIT_MINMAX(mdb->min, mdb->max);

	for(a=0; a<mdb->totcagevert; a++)
		DO_MINMAX(mdb->cagecos[a], mdb->min, mdb->max);

	/* allocate memory */
	mdb->size= (2<<(mmd->gridsize-1)) + 2;
	mdb->size3= mdb->size*mdb->size*mdb->size;
	mdb->tag= MEM_callocN(sizeof(int)*mdb->size3, "MeshDeformBindTag");
	mdb->phi= MEM_callocN(sizeof(float)*mdb->size3, "MeshDeformBindPhi");
	mdb->totalphi= MEM_callocN(sizeof(float)*mdb->size3, "MeshDeformBindTotalPhi");
	mdb->boundisect= MEM_callocN(sizeof(*mdb->boundisect)*mdb->size3, "MDefBoundIsect");
	mdb->semibound= MEM_callocN(sizeof(int)*mdb->size3, "MDefSemiBound");

	mdb->inside= MEM_callocN(sizeof(int)*mdb->totvert, "MDefInside");

	if(mmd->flag & MOD_MDEF_DYNAMIC_BIND)
		mdb->dyngrid= MEM_callocN(sizeof(MDefBindInfluence*)*mdb->size3, "MDefDynGrid");
	else
		mdb->weights= MEM_callocN(sizeof(float)*mdb->totvert*mdb->totcagevert, "MDefWeights");

	mdb->memarena= BLI_memarena_new(BLI_MEMARENA_STD_BUFSIZE, "harmonic coords arena");
	BLI_memarena_use_calloc(mdb->memarena);

	/* make bounding box equal size in all directions, add padding, and compute
	 * width of the cells */
	maxwidth = -1.0f;
	for(a=0; a<3; a++)
		if(mdb->max[a]-mdb->min[a] > maxwidth)
			maxwidth= mdb->max[a]-mdb->min[a];

	for(a=0; a<3; a++) {
		center[a]= (mdb->min[a]+mdb->max[a])*0.5f;
		mdb->min[a]= center[a] - maxwidth*0.5f;
		mdb->max[a]= center[a] + maxwidth*0.5f;

		mdb->width[a]= (mdb->max[a]-mdb->min[a])/(mdb->size-4);
		mdb->min[a] -= 2.1f*mdb->width[a];
		mdb->max[a] += 2.1f*mdb->width[a];

		mdb->width[a]= (mdb->max[a]-mdb->min[a])/mdb->size;
		mdb->halfwidth[a]= mdb->width[a]*0.5f;
	}

	progress_bar(0, "Setting up mesh deform system");

	totinside= 0;
	for(a=0; a<mdb->totvert; a++) {
		copy_v3_v3(vec, mdb->vertexcos[a]);
		mdb->inside[a]= meshdeform_inside_cage(mdb, vec);
		if(mdb->inside[a])
			totinside++;
	}

	/* free temporary MDefBoundIsects */
	BLI_memarena_free(mdb->memarena);
	mdb->memarena= BLI_memarena_new(BLI_MEMARENA_STD_BUFSIZE, "harmonic coords arena");

	/* start with all cells untyped */
	for(a=0; a<mdb->size3; a++)
		mdb->tag[a]= MESHDEFORM_TAG_UNTYPED;
	
	/* detect intersections and tag boundary cells */
	for(z=0; z<mdb->size; z++)
		for(y=0; y<mdb->size; y++)
			for(x=0; x<mdb->size; x++)
				meshdeform_add_intersections(mdb, x, y, z);

	/* compute exterior and interior tags */
	meshdeform_bind_floodfill(mdb);

	for(z=0; z<mdb->size; z++)
		for(y=0; y<mdb->size; y++)
			for(x=0; x<mdb->size; x++)
				meshdeform_check_semibound(mdb, x, y, z);

	/* solve */
	meshdeform_matrix_solve(mdb);

	/* assign results */
	if(mmd->flag & MOD_MDEF_DYNAMIC_BIND) {
		mmd->totinfluence= 0;
		for(a=0; a<mdb->size3; a++)
			for(inf=mdb->dyngrid[a]; inf; inf=inf->next)
				mmd->totinfluence++;

		/* convert MDefBindInfluences to smaller MDefInfluences */
		mmd->dyngrid= MEM_callocN(sizeof(MDefCell)*mdb->size3, "MDefDynGrid");
		mmd->dyninfluences= MEM_callocN(sizeof(MDefInfluence)*mmd->totinfluence, "MDefInfluence");
		offset= 0;
		for(a=0; a<mdb->size3; a++) {
			cell= &mmd->dyngrid[a];
			cell->offset= offset;

			totweight= 0.0f;
			mdinf= mmd->dyninfluences + cell->offset;
			for(inf=mdb->dyngrid[a]; inf; inf=inf->next, mdinf++) {
				mdinf->weight= inf->weight;
				mdinf->vertex= inf->vertex;
				totweight += mdinf->weight;
				cell->totinfluence++;
			}

			if(totweight > 0.0f) {
				mdinf= mmd->dyninfluences + cell->offset;
				for(b=0; b<cell->totinfluence; b++, mdinf++)
					mdinf->weight /= totweight;
			}

			offset += cell->totinfluence;
		}

		mmd->dynverts= mdb->inside;
		mmd->dyngridsize= mdb->size;
		copy_v3_v3(mmd->dyncellmin, mdb->min);
		mmd->dyncellwidth= mdb->width[0];
		MEM_freeN(mdb->dyngrid);
	}
	else {
		mmd->bindweights= mdb->weights;
		MEM_freeN(mdb->inside);
	}

	MEM_freeN(mdb->tag);
	MEM_freeN(mdb->phi);
	MEM_freeN(mdb->totalphi);
	MEM_freeN(mdb->boundisect);
	MEM_freeN(mdb->semibound);
	BLI_memarena_free(mdb->memarena);
}

#if 0
static void heat_weighting_bind(Scene *scene, DerivedMesh *dm, MeshDeformModifierData *mmd, MeshDeformBind *mdb)
{
	LaplacianSystem *sys;
	MFace *mface= dm->getTessFaceArray(dm), *mf;
	int totvert= dm->getNumVerts(dm);
	int totface= dm->getNumFaces(dm);
	float solution, weight;
	int a, tottri, j, thrownerror = 0;

	mdb->weights= MEM_callocN(sizeof(float)*mdb->totvert*mdb->totcagevert, "MDefWeights");

	/* count triangles */
	for(tottri=0, a=0, mf=mface; a<totface; a++, mf++) {
		tottri++;
		if(mf->v4) tottri++;
	}

	/* create laplacian */
	sys = laplacian_system_construct_begin(totvert, tottri, 1);

	sys->heat.mface= mface;
	sys->heat.totface= totface;
	sys->heat.totvert= totvert;
	sys->heat.verts= mdb->vertexcos;
	sys->heat.source = mdb->cagecos;
	sys->heat.numsource= mdb->totcagevert;

	heat_ray_tree_create(sys);
	heat_laplacian_create(sys);

	laplacian_system_construct_end(sys);

	/* compute weights per bone */
	for(j=0; j<mdb->totcagevert; j++) {
		/* fill right hand side */
		laplacian_begin_solve(sys, -1);

		for(a=0; a<totvert; a++)
			if(heat_source_closest(sys, a, j))
				laplacian_add_right_hand_side(sys, a,
					sys->heat.H[a]*sys->heat.p[a]);

		/* solve */
		if(laplacian_system_solve(sys)) {
			/* load solution into vertex groups */
			for(a=0; a<totvert; a++) {
				solution= laplacian_system_get_solution(a);
				
				weight= heat_limit_weight(solution);
				if(weight > 0.0f)
					mdb->weights[a*mdb->totcagevert + j] = weight;
			}
		}
		else if(!thrownerror) {
			error("Mesh Deform Heat Weighting:"
				" failed to find solution for one or more vertices");
			thrownerror= 1;
			break;
		}
	}

	/* free */
	heat_system_free(sys);
	laplacian_system_delete(sys);

	mmd->bindweights= mdb->weights;
}
#endif

void mesh_deform_bind(Scene *scene, MeshDeformModifierData *mmd, float *vertexcos, int totvert, float cagemat[][4])
{
	MeshDeformBind mdb;
	MVert *mvert;
	int a;

	waitcursor(1);
	start_progress_bar();

	memset(&mdb, 0, sizeof(MeshDeformBind));

	/* get mesh and cage mesh */
	mdb.vertexcos= MEM_callocN(sizeof(float)*3*totvert, "MeshDeformCos");
	mdb.totvert= totvert;
	
	mdb.cagedm= mesh_create_derived_no_deform(scene, mmd->object, NULL, CD_MASK_BAREMESH);
	mdb.totcagevert= mdb.cagedm->getNumVerts(mdb.cagedm);
	mdb.cagecos= MEM_callocN(sizeof(*mdb.cagecos)*mdb.totcagevert, "MeshDeformBindCos");
	copy_m4_m4(mdb.cagemat, cagemat);

	mvert= mdb.cagedm->getVertArray(mdb.cagedm);
	for(a=0; a<mdb.totcagevert; a++)
		copy_v3_v3(mdb.cagecos[a], mvert[a].co);
	for(a=0; a<mdb.totvert; a++)
		mul_v3_m4v3(mdb.vertexcos[a], mdb.cagemat, vertexcos + a*3);

	/* solve */
#if 0
	if(mmd->mode == MOD_MDEF_VOLUME)
		harmonic_coordinates_bind(scene, mmd, &mdb);
	else
		heat_weighting_bind(scene, dm, mmd, &mdb);
#else
	harmonic_coordinates_bind(scene, mmd, &mdb);
#endif

	/* assign bind variables */
	mmd->bindcagecos= (float*)mdb.cagecos;
	mmd->totvert= mdb.totvert;
	mmd->totcagevert= mdb.totcagevert;
	copy_m4_m4(mmd->bindmat, mmd->object->obmat);

	/* transform bindcagecos to world space */
	for(a=0; a<mdb.totcagevert; a++)
		mul_m4_v3(mmd->object->obmat, mmd->bindcagecos+a*3);

	/* free */
	mdb.cagedm->release(mdb.cagedm);
	MEM_freeN(mdb.vertexcos);

	/* compact weights */
	modifier_mdef_compact_influences((ModifierData*)mmd);

	end_progress_bar();
	waitcursor(0);
}

