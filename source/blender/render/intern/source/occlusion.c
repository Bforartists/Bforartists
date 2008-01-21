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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Brecht Van Lommel.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_material_types.h"
#include "DNA_meshdata_types.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"
#include "BLI_memarena.h"
#include "BLI_threads.h"

#include "BKE_DerivedMesh.h"
#include "BKE_global.h"
#include "BKE_utildefines.h"

#include "RE_shader_ext.h"

/* local includes */
#include "occlusion.h"
#include "render_types.h"
#include "rendercore.h"
#include "renderdatabase.h"
#include "pixelshading.h"
#include "shading.h"
#include "zbuf.h"

/* ------------------------- Declarations --------------------------- */

#define INVALID_INDEX ((int)(~0))
#define INVPI 0.31830988618379069f
#define TOTCHILD 8
#define CACHE_STEP 3

typedef struct OcclusionCacheSample {
	float co[3], n[3], col[3], intensity, dist2;
	int x, y, filled;
} OcclusionCacheSample;

typedef struct OcclusionCache {
	OcclusionCacheSample *sample;
	int x, y, w, h, step;
} OcclusionCache;

typedef struct OcclusionCacheMesh {
	struct OcclusionCacheMesh *next, *prev;
	ObjectRen *obr;
	int (*face)[4];
	float (*co)[3];
	float (*col)[3];
	int totvert, totface;
} OcclusionCacheMesh;

typedef struct OccFace {
	int obi;
	int facenr;
} OccFace;

typedef struct OccNode {
	float co[3], area;
	float sh[9], dco;
	float occlusion;
	int childflag;
	union {
		//OccFace face;
		int face;
		struct OccNode *node;
	} child[TOTCHILD];
} OccNode;

typedef struct OcclusionTree {
	MemArena *arena;

	float (*co)[3];		/* temporary during build */

	OccFace *face;		/* instance and face indices */
	float *occlusion;	/* occlusion for faces */
	
	OccNode *root;

	OccNode **stack[BLENDER_MAX_THREADS];
	int maxdepth;

	int totface;

	float error;
	float distfac;

	OcclusionCache *cache;
} OcclusionTree;

/* ------------------------- Shading --------------------------- */

extern Render R; // meh

#if 0
static void occ_shade(ShadeSample *ssamp, ObjectInstanceRen *obi, VlakRen *vlr, float *rad)
{
	ShadeInput *shi= ssamp->shi;
	ShadeResult *shr= ssamp->shr;
	float l, u, v, *v1, *v2, *v3;
	
	/* init */
	if(vlr->v4) {
		shi->u= u= 0.5f;
		shi->v= v= 0.5f;
	}
	else {
		shi->u= u= 1.0f/3.0f;
		shi->v= v= 1.0f/3.0f;
	}

	/* setup render coordinates */
	v1= vlr->v1->co;
	v2= vlr->v2->co;
	v3= vlr->v3->co;
	
	/* renderco */
	l= 1.0f-u-v;
	
	shi->co[0]= l*v3[0]+u*v1[0]+v*v2[0];
	shi->co[1]= l*v3[1]+u*v1[1]+v*v2[1];
	shi->co[2]= l*v3[2]+u*v1[2]+v*v2[2];
	
	shade_input_set_triangle_i(shi, obi, vlr, 0, 1, 2);

	/* set up view vector */
	VECCOPY(shi->view, shi->co);
	Normalize(shi->view);
	
	/* cache for shadow */
	shi->samplenr++;
	
	shi->xs= 0; // TODO
	shi->ys= 0;
	
	shade_input_set_normals(shi);

	/* no normal flip */
	if(shi->flippednor)
		shade_input_flip_normals(shi);

	/* not a pretty solution, but fixes common cases */
	if(shi->obr->ob && shi->obr->ob->transflag & OB_NEG_SCALE) {
		VecMulf(shi->vn, -1.0f);
		VecMulf(shi->vno, -1.0f);
	}

	/* init material vars */
	// note, keep this synced with render_types.h
	memcpy(&shi->r, &shi->mat->r, 23*sizeof(float));
	shi->har= shi->mat->har;
	
	/* render */
	shade_input_set_shade_texco(shi);
	shade_material_loop(shi, shr); /* todo: nodes */
	
	VECCOPY(rad, shr->combined);
}

static void occ_build_shade(Render *re, OcclusionTree *tree)
{
	ShadeSample ssamp;
	ObjectInstanceRen *obi;
	VlakRen *vlr;
	int a;

	R= *re;

	/* setup shade sample with correct passes */
	memset(&ssamp, 0, sizeof(ShadeSample));
	ssamp.shi[0].lay= re->scene->lay;
	ssamp.shi[0].passflag= SCE_PASS_DIFFUSE|SCE_PASS_RGBA;
	ssamp.shi[0].combinedflag= ~(SCE_PASS_SPEC);
	ssamp.tot= 1;

	for(a=0; a<tree->totface; a++) {
		obi= &R.objectinstance[tree->face[a].obi];
		vlr= RE_findOrAddVlak(obi->obr, tree->face[a].vlr);

		occ_shade(&ssamp, obi, vlr, tree->rad[a]);
	}
}
#endif

/* ------------------------- Spherical Harmonics --------------------------- */

/* Use 2nd order SH => 9 coefficients, stored in this order:
   0 = (0,0),
   1 = (1,-1), 2 = (1,0), 3 = (1,1),
   4 = (2,-2), 5 = (2,-1), 6 = (2,0), 7 = (2,1), 8 = (2,2) */

static void sh_copy(float *shresult, float *sh)
{
	memcpy(shresult, sh, sizeof(float)*9);
}

static void sh_mul(float *sh, float f)
{
	int i;

	for(i=0; i<9; i++)
		sh[i] *= f;
}

static void sh_add(float *shresult, float *sh1, float *sh2)
{
	int i;

	for(i=0; i<9; i++)
		shresult[i]= sh1[i] + sh2[i];
}

static void sh_from_disc(float *n, float area, float *shresult)
{
	/* See formula (3) in:
	   "An Efficient Representation for Irradiance Environment Maps" */
	float sh[9], x, y, z;

	x= n[0];
	y= n[1];
	z= n[2];

	sh[0]= 0.282095f;

	sh[1]= 0.488603f*y;
	sh[2]= 0.488603f*z;
	sh[3]= 0.488603f*x;
	
	sh[4]= 1.092548f*x*y;
	sh[5]= 1.092548f*y*z;
	sh[6]= 0.315392f*(3.0f*z*z - 1.0f);
	sh[7]= 1.092548f*x*z;
	sh[8]= 0.546274f*(x*x - y*y);

	sh_mul(sh, area);
	sh_copy(shresult, sh);
}

static float sh_eval(float *sh, float *v)
{
	/* See formula (13) in:
	   "An Efficient Representation for Irradiance Environment Maps" */
	static const float c1 = 0.429043f, c2 = 0.511664f, c3 = 0.743125f;
	static const float c4 = 0.886227f, c5 = 0.247708f;
	float x, y, z, sum;

	x= v[0];
	y= v[1];
	z= v[2];

	sum= c1*sh[8]*(x*x - y*y);
	sum += c3*sh[6]*z*z;
	sum += c4*sh[0];
	sum += -c5*sh[6];
	sum += 2.0f*c1*(sh[4]*x*y + sh[7]*x*z + sh[5]*y*z);
	sum += 2.0f*c2*(sh[3]*x + sh[1]*y + sh[2]*z);

	return sum;
}

/* ------------------------------ Building --------------------------------- */

static void occ_face(const OccFace *face, float *co, float *normal, float *area)
{
	ObjectInstanceRen *obi;
	VlakRen *vlr;

	obi= &R.objectinstance[face->obi];
	vlr= RE_findOrAddVlak(obi->obr, face->facenr);
	
	if(co) {
		if(vlr->v4)
			VecLerpf(co, vlr->v1->co, vlr->v3->co, 0.5f);
		else
			CalcCent3f(co, vlr->v1->co, vlr->v2->co, vlr->v3->co);

		if(obi->flag & R_TRANSFORMED)
			Mat4MulVecfl(obi->mat, co);
	}
	
	if(normal) {
		normal[0]= -vlr->n[0];
		normal[1]= -vlr->n[1];
		normal[2]= -vlr->n[2];

		if(obi->flag & R_TRANSFORMED) {
			float xn, yn, zn, (*imat)[3]= obi->imat;

			xn= normal[0];
			yn= normal[1];
			zn= normal[2];

			normal[0]= imat[0][0]*xn + imat[0][1]*yn + imat[0][2]*zn;
			normal[1]= imat[1][0]*xn + imat[1][1]*yn + imat[1][2]*zn;
			normal[2]= imat[2][0]*xn + imat[2][1]*yn + imat[2][2]*zn;
		}
	}

	if(area) {
		/* todo: correct area for instances */
		if(vlr->v4)
			*area= AreaQ3Dfl(vlr->v1->co, vlr->v2->co, vlr->v3->co, vlr->v4->co);
		else
			*area= AreaT3Dfl(vlr->v1->co, vlr->v2->co, vlr->v3->co);
	}
}

static void occ_sum_occlusion(OcclusionTree *tree, OccNode *node)
{
	OccNode *child;
	float occ, area, totarea;
	int a, b;

	occ= 0.0f;
	totarea= 0.0f;

	for(b=0; b<TOTCHILD; b++) {
		if(node->childflag & (1<<b)) {
			a= node->child[b].face;
			occ_face(&tree->face[a], 0, 0, &area);
			occ += area*tree->occlusion[a];
			totarea += area;
		}
		else if(node->child[b].node) {
			child= node->child[b].node;
			occ_sum_occlusion(tree, child);

			occ += child->area*child->occlusion;
			totarea += child->area;
		}
	}

	if(totarea != 0.0f)
		occ /= totarea;
	
	node->occlusion= occ;
}

static int occ_find_bbox_axis(OcclusionTree *tree, int begin, int end, float *min, float *max)
{
	float len, maxlen= -1.0f;
	int a, axis = 0;

	INIT_MINMAX(min, max);

	for(a=begin; a<end; a++)
		DO_MINMAX(tree->co[a], min, max)

	for(a=0; a<3; a++) {
		len= max[a] - min[a];

		if(len > maxlen) {
			maxlen= len;
			axis= a;
		}
	}

	return axis;
}

void occ_node_from_face(OccFace *face, OccNode *node)
{
	float n[3];

	occ_face(face, node->co, n, &node->area);
	node->dco= 0.0f;
	sh_from_disc(n, node->area, node->sh);
}

static void occ_build_dco(OcclusionTree *tree, OccNode *node, float *co, float *dco)
{
	OccNode *child;
	float dist, d[3], nco[3];
	int b;

	for(b=0; b<TOTCHILD; b++) {
		if(node->childflag & (1<<b)) {
			occ_face(tree->face+node->child[b].face, nco, 0, 0);
		}
		else if(node->child[b].node) {
			child= node->child[b].node;
			occ_build_dco(tree, child, co, dco);
			VECCOPY(nco, child->co);
		}

		VECSUB(d, nco, co);
		dist= INPR(d, d);
		if(dist > *dco)
			*dco= dist;
	}
}

static void occ_build_split(OcclusionTree *tree, int begin, int end, int *split)
{
	float min[3], max[3], mid;
	int axis, a, enda;

	/* split in middle of boundbox. this seems faster than median split
	 * on complex scenes, possibly since it avoids two distant faces to
	 * be in the same node better? */
	axis= occ_find_bbox_axis(tree, begin, end, min, max);
	mid= 0.5f*(min[axis]+max[axis]);

	a= begin;
	enda= end;
	while(a<enda) {
		if(tree->co[a][axis] > mid) {
			enda--;
			SWAP(OccFace, tree->face[a], tree->face[enda]);
			SWAP(float, tree->co[a][0], tree->co[enda][0]);
			SWAP(float, tree->co[a][1], tree->co[enda][1]);
			SWAP(float, tree->co[a][2], tree->co[enda][2]);
		}
		else
			a++;
	}

	*split= enda;
}

static void occ_build_8_split(OcclusionTree *tree, int begin, int end, int *offset, int *count)
{
	/* split faces into eight groups */
	int b, splitx, splity[2], splitz[4];

	occ_build_split(tree, begin, end, &splitx);

	occ_build_split(tree, begin, splitx, &splity[0]);
	occ_build_split(tree, splitx, end, &splity[1]);

	occ_build_split(tree, begin, splity[0], &splitz[0]);
	occ_build_split(tree, splity[0], splitx, &splitz[1]);
	occ_build_split(tree, splitx, splity[1], &splitz[2]);
	occ_build_split(tree, splity[1], end, &splitz[3]);

	offset[0]= begin;
	offset[1]= splitz[0];
	offset[2]= splity[0];
	offset[3]= splitz[1];
	offset[4]= splitx;
	offset[5]= splitz[2];
	offset[6]= splity[1];
	offset[7]= splitz[3];

	for(b=0; b<7; b++)
		count[b]= offset[b+1] - offset[b];
	count[7]= end - offset[7];
}

static OccNode *occ_build_recursive(OcclusionTree *tree, int begin, int end, int depth)
{
	OccNode *node, *child, tmpnode;
	OccFace *face;
	int a, b, offset[TOTCHILD], count[TOTCHILD];

	/* keep track of maximum depth for stack */
	if(depth > tree->maxdepth)
		tree->maxdepth= depth;

	/* add a new node */
	node= BLI_memarena_alloc(tree->arena, sizeof(OccNode));
	node->occlusion= 1.0f;

	/* leaf node with only children */
	if(end - begin <= TOTCHILD) {
		for(a=begin, b=0; a<end; a++, b++) {
			face= &tree->face[a];
			node->child[b].face= a;
			node->childflag |= (1<<b);
		}
	}
	else {
		/* order faces */
		occ_build_8_split(tree, begin, end, offset, count);

		for(b=0; b<TOTCHILD; b++) {
			if(count[b] == 0) {
				node->child[b].node= NULL;
			}
			else if(count[b] == 1) {
				face= &tree->face[offset[b]];
				node->child[b].face= offset[b];
				node->childflag |= (1<<b);
			}
			else {
				child= occ_build_recursive(tree, offset[b], offset[b]+count[b], depth+1);
				node->child[b].node= child;
			}
		}
	}

	/* combine area, position and sh */
	for(b=0; b<TOTCHILD; b++) {
		if(node->childflag & (1<<b)) {
			child= &tmpnode;
			occ_node_from_face(tree->face+node->child[b].face, &tmpnode);
		}
		else {
			child= node->child[b].node;
		}

		if(child) {
			node->area += child->area;
			sh_add(node->sh, node->sh, child->sh);
			VECADDFAC(node->co, node->co, child->co, child->area);
		}
	}

	if(node->area != 0.0f)
		VecMulf(node->co, 1.0f/node->area);

	/* compute maximum distance from center */
	node->dco= 0.0f;
	occ_build_dco(tree, node, node->co, &node->dco);

	return node;
}

static void occ_build_sh_normalize(OccNode *node)
{
	/* normalize spherical harmonics to not include area, so
	 * we can clamp the dot product and then mutliply by area */
	int b;

	if(node->area != 0.0f)
		sh_mul(node->sh, 1.0f/node->area);

	for(b=0; b<TOTCHILD; b++) {
		if(node->childflag & (1<<b));
		else if(node->child[b].node)
			occ_build_sh_normalize(node->child[b].node);
	}
}

static OcclusionTree *occ_tree_build(Render *re)
{
	OcclusionTree *tree;
	ObjectInstanceRen *obi;
	ObjectRen *obr;
	VlakRen *vlr= NULL;
	int a, b, c, totface;

	/* count */
	totface= 0;
	for(obi=re->instancetable.first; obi; obi=obi->next) {
		if(obi->flag & R_TRANSFORMED)
			continue;

		obr= obi->obr;
		for(a=0; a<obr->totvlak; a++) {
			if((a & 255)==0) vlr= obr->vlaknodes[a>>8].vlak;
			else vlr++;

			if(vlr->mat->mode & MA_TRACEBLE)
				totface++;
		}
	}

	if(totface == 0)
		return NULL;
	
	tree= MEM_callocN(sizeof(OcclusionTree), "OcclusionTree");
	tree->totface= totface;

	/* parameters */
	tree->error= re->wrld.ao_approx_error;
	tree->distfac= (re->wrld.aomode & WO_AODIST)? re->wrld.aodistfac: 0.0f;

	/* allocation */
	tree->arena= BLI_memarena_new(0x8000 * sizeof(OccNode));
	BLI_memarena_use_calloc(tree->arena);

	if(re->wrld.aomode & WO_AOCACHE)
		tree->cache= MEM_callocN(sizeof(OcclusionCache)*BLENDER_MAX_THREADS, "OcclusionCache");

	tree->face= MEM_callocN(sizeof(OccFace)*totface, "OcclusionFace");
	tree->co= MEM_callocN(sizeof(float)*3*totface, "OcclusionCo");
	tree->occlusion= MEM_callocN(sizeof(float)*totface, "OcclusionOcclusion");

	/* make array of face pointers */
	for(b=0, c=0, obi=re->instancetable.first; obi; obi=obi->next, c++) {
		if(obi->flag & R_TRANSFORMED)
			continue; /* temporary to avoid slow renders with loads of duplis */

		obr= obi->obr;
		for(a=0; a<obr->totvlak; a++) {
			if((a & 255)==0) vlr= obr->vlaknodes[a>>8].vlak;
			else vlr++;

			if(vlr->mat->mode & MA_TRACEBLE) {
				tree->face[b].obi= c;
				tree->face[b].facenr= a;
				tree->occlusion[b]= 1.0f;
				occ_face(&tree->face[b], tree->co[b], NULL, NULL); 
				b++;
			}
		}
	}

	/* recurse */
	tree->root= occ_build_recursive(tree, 0, totface, 1);

#if 0
	if(tree->doindirect) {
		occ_build_shade(re, tree);
		occ_sum_occlusion(tree, tree->root);
	}
#endif
	
	MEM_freeN(tree->co);
	tree->co= NULL;

	occ_build_sh_normalize(tree->root);

	for(a=0; a<BLENDER_MAX_THREADS; a++)
		tree->stack[a]= MEM_callocN(sizeof(OccNode)*TOTCHILD*(tree->maxdepth+1), "OccStack");

	return tree;
}

static void occ_free_tree(OcclusionTree *tree)
{
	int a;

	if(tree) {
		if(tree->arena) BLI_memarena_free(tree->arena);
		for(a=0; a<BLENDER_MAX_THREADS; a++)
			if(tree->stack[a])
				MEM_freeN(tree->stack[a]);
		if(tree->occlusion) MEM_freeN(tree->occlusion);
		if(tree->face) MEM_freeN(tree->face);
		if(tree->cache) MEM_freeN(tree->cache);
		MEM_freeN(tree);
	}
}

/* ------------------------- Traversal --------------------------- */

static float occ_solid_angle(OccNode *node, float *v, float d2, float *receivenormal)
{
	float dotreceive, dotemit, invd2 = 1.0f/sqrtf(d2);
	float ev[3];

	ev[0]= -v[0]*invd2;
	ev[1]= -v[1]*invd2;
	ev[2]= -v[2]*invd2;
	dotemit= sh_eval(node->sh, ev);
	dotreceive= INPR(receivenormal, v)*invd2;

	CLAMP(dotemit, 0.0f, 1.0f);
	CLAMP(dotreceive, 0.0f, 1.0f);
	
	return ((node->area*dotemit*dotreceive)/(d2 + node->area*INVPI))*INVPI;
}

static void VecAddDir(float *result, float *v1, float *v2, float fac)
{
	result[0]= v1[0] + fac*(v2[0] - v1[0]);
	result[1]= v1[1] + fac*(v2[1] - v1[1]);
	result[2]= v1[2] + fac*(v2[2] - v1[2]);
}

static int occ_visible_quad(float *p, float *n, float *v0, float *v1, float *v2, float *q0, float *q1, float *q2, float *q3)
{
	static const float epsilon = 1e-6f;
	float c, sd[3];
	
	c= INPR(n, p);

	/* signed distances from the vertices to the plane. */
	sd[0]= INPR(n, v0) - c;
	sd[1]= INPR(n, v1) - c;
	sd[2]= INPR(n, v2) - c;

	if(fabs(sd[0]) < epsilon) sd[0] = 0.0f;
	if(fabs(sd[1]) < epsilon) sd[1] = 0.0f;
	if(fabs(sd[2]) < epsilon) sd[2] = 0.0f;

	if(sd[0] > 0) {
		if(sd[1] > 0) {
			if(sd[2] > 0) {
				// +++
				VECCOPY(q0, v0);
				VECCOPY(q1, v1);
				VECCOPY(q2, v2);
				VECCOPY(q3, q2);
			}
			else if(sd[2] < 0) {
				// ++-
				VECCOPY(q0, v0);
				VECCOPY(q1, v1);
				VecAddDir(q2, v1, v2, (sd[1]/(sd[1]-sd[2])));
				VecAddDir(q3, v0, v2, (sd[0]/(sd[0]-sd[2])));
			}
			else {
				// ++0
				VECCOPY(q0, v0);
				VECCOPY(q1, v1);
				VECCOPY(q2, v2);
				VECCOPY(q3, q2);
			}
		}
		else if(sd[1] < 0) {
			if(sd[2] > 0) {
				// +-+
				VECCOPY(q0, v0);
				VecAddDir(q1, v0, v1, (sd[0]/(sd[0]-sd[1])));
				VecAddDir(q2, v1, v2, (sd[1]/(sd[1]-sd[2])));
				VECCOPY(q3, v2);
			}
			else if(sd[2] < 0) {
				// +--
				VECCOPY(q0, v0);
				VecAddDir(q1, v0, v1, (sd[0]/(sd[0]-sd[1])));
				VecAddDir(q2, v0, v2, (sd[0]/(sd[0]-sd[2])));
				VECCOPY(q3, q2);
			}
			else {
				// +-0
				VECCOPY(q0, v0);
				VecAddDir(q1, v0, v1, (sd[0]/(sd[0]-sd[1])));
				VECCOPY(q2, v2);
				VECCOPY(q3, q2);
			}
		}
		else {
			if(sd[2] > 0) {
				// +0+
				VECCOPY(q0, v0);
				VECCOPY(q1, v1);
				VECCOPY(q2, v2);
				VECCOPY(q3, q2);
			}
			else if(sd[2] < 0) {
				// +0-
				VECCOPY(q0, v0);
				VECCOPY(q1, v1);
				VecAddDir(q2, v0, v2, (sd[0]/(sd[0]-sd[2])));
				VECCOPY(q3, q2);
			}
			else {
				// +00
				VECCOPY(q0, v0);
				VECCOPY(q1, v1);
				VECCOPY(q2, v2);
				VECCOPY(q3, q2);
			}
		}
	}
	else if(sd[0] < 0) {
		if(sd[1] > 0) {
			if(sd[2] > 0) {
				// -++
				VecAddDir(q0, v0, v1, (sd[0]/(sd[0]-sd[1])));
				VECCOPY(q1, v1);
				VECCOPY(q2, v2);
				VecAddDir(q3, v0, v2, (sd[0]/(sd[0]-sd[2])));
			}
			else if(sd[2] < 0) {
				// -+-
				VecAddDir(q0, v0, v1, (sd[0]/(sd[0]-sd[1])));
				VECCOPY(q1, v1);
				VecAddDir(q2, v1, v2, (sd[1]/(sd[1]-sd[2])));
				VECCOPY(q3, q2);
			}
			else {
				// -+0
				VecAddDir(q0, v0, v1, (sd[0]/(sd[0]-sd[1])));
				VECCOPY(q1, v1);
				VECCOPY(q2, v2);
				VECCOPY(q3, q2);
			}
		}
		else if(sd[1] < 0) {
			if(sd[2] > 0) {
				// --+
				VecAddDir(q0, v0, v2, (sd[0]/(sd[0]-sd[2])));
				VecAddDir(q1, v1, v2, (sd[1]/(sd[1]-sd[2])));
				VECCOPY(q2, v2);
				VECCOPY(q3, q2);
			}
			else if(sd[2] < 0) {
				// ---
				return 0;
			}
			else {
				// --0
				return 0;
			}
		}
		else {
			if(sd[2] > 0) {
				// -0+
				VecAddDir(q0, v0, v2, (sd[0]/(sd[0]-sd[2])));
				VECCOPY(q1, v1);
				VECCOPY(q2, v2);
				VECCOPY(q3, q2);
			}
			else if(sd[2] < 0) {
				// -0-
				return 0;
			}
			else {
				// -00
				return 0;
			}
		}
	}
	else {
		if(sd[1] > 0) {
			if(sd[2] > 0) {
				// 0++
				VECCOPY(q0, v0);
				VECCOPY(q1, v1);
				VECCOPY(q2, v2);
				VECCOPY(q3, q2);
			}
			else if(sd[2] < 0) {
				// 0+-
				VECCOPY(q0, v0);
				VECCOPY(q1, v1);
				VecAddDir(q2, v1, v2, (sd[1]/(sd[1]-sd[2])));
				VECCOPY(q3, q2);
			}
			else {
				// 0+0
				VECCOPY(q0, v0);
				VECCOPY(q1, v1);
				VECCOPY(q2, v2);
				VECCOPY(q3, q2);
			}
		}
		else if(sd[1] < 0) {
			if(sd[2] > 0) {
				// 0-+
				VECCOPY(q0, v0);
				VecAddDir(q1, v1, v2, (sd[1]/(sd[1]-sd[2])));
				VECCOPY(q2, v2);
				VECCOPY(q3, q2);
			}
			else if(sd[2] < 0) {
				// 0--
				return 0;
			}
			else {
				// 0-0
				return 0;
			}
		}
		else {
			if(sd[2] > 0) {
				// 00+
				VECCOPY(q0, v0);
				VECCOPY(q1, v1);
				VECCOPY(q2, v2);
				VECCOPY(q3, q2);
			}
			else if(sd[2] < 0) {
				// 00-
				return 0;
			}
			else {
				// 000
				return 0;
			}
		}
	}

	return 1;
}

/* altivec optimization, this works, but is unused */

#if 0
#include <Accelerate/Accelerate.h>

typedef union {
	vFloat v;
	float f[4];
} vFloatResult;

static vFloat vec_splat_float(float val)
{
	return (vFloat){val, val, val, val};
}

static float occ_quad_form_factor(float *p, float *n, float *q0, float *q1, float *q2, float *q3)
{
	vFloat vcos, rlen, vrx, vry, vrz, vsrx, vsry, vsrz, gx, gy, gz, vangle;
	vUInt8 rotate = (vUInt8){4,5,6,7,8,9,10,11,12,13,14,15,0,1,2,3};
	vFloatResult vresult;
	float result;

	/* compute r* */
	vrx = (vFloat){q0[0], q1[0], q2[0], q3[0]} - vec_splat_float(p[0]);
	vry = (vFloat){q0[1], q1[1], q2[1], q3[1]} - vec_splat_float(p[1]);
	vrz = (vFloat){q0[2], q1[2], q2[2], q3[2]} - vec_splat_float(p[2]);

	/* normalize r* */
	rlen = vec_rsqrte(vrx*vrx + vry*vry + vrz*vrz + vec_splat_float(1e-16f));
	vrx = vrx*rlen;
	vry = vry*rlen;
	vrz = vrz*rlen;

	/* rotate r* for cross and dot */
	vsrx= vec_perm(vrx, vrx, rotate);
	vsry= vec_perm(vry, vry, rotate);
	vsrz= vec_perm(vrz, vrz, rotate);

	/* cross product */
	gx = vsry*vrz - vsrz*vry;
	gy = vsrz*vrx - vsrx*vrz;
	gz = vsrx*vry - vsry*vrx;

	/* normalize */
	rlen = vec_rsqrte(gx*gx + gy*gy + gz*gz + vec_splat_float(1e-16f));
	gx = gx*rlen;
	gy = gy*rlen;
	gz = gz*rlen;

	/* angle */
	vcos = vrx*vsrx + vry*vsry + vrz*vsrz;
	vcos= vec_max(vec_min(vcos, vec_splat_float(1.0f)), vec_splat_float(-1.0f));
	vangle= vacosf(vcos);

	/* dot */
	vresult.v = (vec_splat_float(n[0])*gx +
	             vec_splat_float(n[1])*gy +
	             vec_splat_float(n[2])*gz)*vangle;

	result= (vresult.f[0] + vresult.f[1] + vresult.f[2] + vresult.f[3])*(0.5f/(float)M_PI);
	result= MAX2(result, 0.0f);

	return result;
}

#endif

/* SSE optimization, acos code doesn't work */

#if 0

#include <xmmintrin.h>

static __m128 sse_approx_acos(__m128 x)
{
	/* needs a better approximation than taylor expansion of acos, since that
	 * gives big erros for near 1.0 values, sqrt(2*x)*acos(1-x) should work
	 * better, see http://www.tom.womack.net/projects/sse-fast-arctrig.html */

	return _mm_set_ps1(1.0f);
}

static float occ_quad_form_factor(float *p, float *n, float *q0, float *q1, float *q2, float *q3)
{
	float r0[3], r1[3], r2[3], r3[3], g0[3], g1[3], g2[3], g3[3];
	float a1, a2, a3, a4, dot1, dot2, dot3, dot4, result;
	float fresult[4] __attribute__((aligned(16)));
	__m128 qx, qy, qz, rx, ry, rz, rlen, srx, sry, srz, gx, gy, gz, glen, rcos, angle, aresult;

	/* compute r */
	qx = _mm_set_ps(q3[0], q2[0], q1[0], q0[0]);
	qy = _mm_set_ps(q3[1], q2[1], q1[1], q0[1]);
	qz = _mm_set_ps(q3[2], q2[2], q1[2], q0[2]);

	rx = qx - _mm_set_ps1(p[0]);
	ry = qy - _mm_set_ps1(p[1]);
	rz = qz - _mm_set_ps1(p[2]);

	/* normalize r */
	rlen = _mm_rsqrt_ps(rx*rx + ry*ry + rz*rz + _mm_set_ps1(1e-16f));
	rx = rx*rlen;
	ry = ry*rlen;
	rz = rz*rlen;

	/* cross product */
	srx = _mm_shuffle_ps(rx, rx, _MM_SHUFFLE(0,3,2,1));
	sry = _mm_shuffle_ps(ry, ry, _MM_SHUFFLE(0,3,2,1));
	srz = _mm_shuffle_ps(rz, rz, _MM_SHUFFLE(0,3,2,1));

	gx = sry*rz - srz*ry;
	gy = srz*rx - srx*rz;
	gz = srx*ry - sry*rx;

	/* normalize g */
	glen = _mm_rsqrt_ps(gx*gx + gy*gy + gz*gz + _mm_set_ps1(1e-16f));
	gx = gx*glen;
	gy = gy*glen;
	gz = gz*glen;

	/* compute angle */
	rcos = rx*srx + ry*sry + rz*srz;
	rcos= _mm_max_ps(_mm_min_ps(rcos, _mm_set_ps1(1.0f)), _mm_set_ps1(-1.0f));

	angle = sse_approx_cos(rcos);
	aresult = (_mm_set_ps1(n[0])*gx + _mm_set_ps1(n[1])*gy + _mm_set_ps1(n[2])*gz)*angle;

	/* sum together */
    result= (fresult[0] + fresult[1] + fresult[2] + fresult[3])*(0.5f/(float)M_PI);
	result= MAX2(result, 0.0f);

	return result;
}

#endif

static float saacosf(float fac)
{
	if(fac<= -1.0f) return (float)M_PI;
	else if(fac>=1.0f) return 0.0f;
	else return acos(fac); /* acosf(fac) */
}

static void normalizef(float *n)
{
	float d;
	
	d= INPR(n, n);

	if(d > 1.0e-35F) {
		d= 1.0f/sqrt(d); /* sqrtf(d) */

		n[0] *= d; 
		n[1] *= d; 
		n[2] *= d;
	} 
}

static float occ_quad_form_factor(float *p, float *n, float *q0, float *q1, float *q2, float *q3)
{
	float r0[3], r1[3], r2[3], r3[3], g0[3], g1[3], g2[3], g3[3];
	float a1, a2, a3, a4, dot1, dot2, dot3, dot4, result;

	VECSUB(r0, q0, p);
	VECSUB(r1, q1, p);
	VECSUB(r2, q2, p);
	VECSUB(r3, q3, p);

	normalizef(r0);
	normalizef(r1);
	normalizef(r2);
	normalizef(r3);

	Crossf(g0, r1, r0); normalizef(g0);
	Crossf(g1, r2, r1); normalizef(g1);
	Crossf(g2, r3, r2); normalizef(g2);
	Crossf(g3, r0, r3); normalizef(g3);

	a1= saacosf(INPR(r0, r1));
	a2= saacosf(INPR(r1, r2));
	a3= saacosf(INPR(r2, r3));
	a4= saacosf(INPR(r3, r0));

	dot1= INPR(n, g0);
	dot2= INPR(n, g1);
	dot3= INPR(n, g2);
	dot4= INPR(n, g3);

	result= (a1*dot1 + a2*dot2 + a3*dot3 + a4*dot4)*0.5f/(float)M_PI;
	result= MAX2(result, 0.0f);

	return result;
}

float occ_form_factor(OccFace *face, float *p, float *n)
{
	ObjectInstanceRen *obi;
	VlakRen *vlr;
	float v1[3], v2[3], v3[3], v4[3], q0[3], q1[3], q2[3], q3[3], contrib= 0.0f;

	obi= &R.objectinstance[face->obi];
	vlr= RE_findOrAddVlak(obi->obr, face->facenr);

	VECCOPY(v1, vlr->v1->co);
	VECCOPY(v2, vlr->v2->co);
	VECCOPY(v3, vlr->v3->co);

	if(obi->flag & R_TRANSFORMED) {
		Mat4MulVecfl(obi->mat, v1);
		Mat4MulVecfl(obi->mat, v2);
		Mat4MulVecfl(obi->mat, v3);
	}

	if(occ_visible_quad(p, n, v1, v2, v3, q0, q1, q2, q3))
		contrib += occ_quad_form_factor(p, n, q0, q1, q2, q3);

	if(vlr->v4) {
		VECCOPY(v4, vlr->v4->co);
		if(obi->flag & R_TRANSFORMED)
			Mat4MulVecfl(obi->mat, v4);

		if(occ_visible_quad(p, n, v1, v3, v4, q0, q1, q2, q3))
			contrib += occ_quad_form_factor(p, n, q0, q1, q2, q3);
	}

	return contrib;
}

static void occ_lookup(OcclusionTree *tree, int thread, OccFace *exclude, float *pp, float *pn, float *occ, float *bentn)
{
	OccNode *node, **stack;
	OccFace *face;
	float resultocc, v[3], p[3], n[3], co[3];
	float distfac, error, d2, weight, emitarea;
	int b, totstack;

	/* init variables */
	VECCOPY(p, pp);
	VECCOPY(n, pn);
	VECADDFAC(p, p, n, 1e-4f);

	if(bentn)
		VECCOPY(bentn, n);
	
	error= tree->error;
	distfac= tree->distfac;

	resultocc= 0.0f;

	/* init stack */
	stack= tree->stack[thread];
	stack[0]= tree->root;
	totstack= 1;

	while(totstack) {
		/* pop point off the stack */
		node= stack[--totstack];

		VECSUB(v, node->co, p);
		d2= INPR(v, v) + 1e-16f;
		emitarea= MAX2(node->area, node->dco);

		if(d2*error > emitarea) {
			/* accumulate occlusion from spherical harmonics */
			weight= occ_solid_angle(node, v, d2, n);
			weight *= node->occlusion;

			if(bentn) {
				Normalize(v);
				bentn[0] -= weight*v[0];
				bentn[1] -= weight*v[1];
				bentn[2] -= weight*v[2];
			}

			if(distfac != 0.0f)
				weight /= (1.0 + distfac*d2);

			resultocc += weight;
		}
		else {
			/* traverse into children */
			for(b=0; b<TOTCHILD; b++) {
				if(node->childflag & (1<<b)) {
					face= tree->face+node->child[b].face;

					/* accumulate occlusion with face form factor */
					if(!exclude || !(face->obi == exclude->obi && face->facenr == exclude->facenr)) {
						weight= occ_form_factor(face, p, n);
						weight *= tree->occlusion[node->child[b].face];

						if(bentn || distfac != 0.0f) {
							occ_face(face, co, NULL, NULL); 
							VECSUB(v, co, p);

							if(bentn) {
								Normalize(v);
								bentn[0] -= weight*v[0];
								bentn[1] -= weight*v[1];
								bentn[2] -= weight*v[2];
							}

							if(distfac != 0.0f) {
								d2= INPR(v, v) + 1e-16f;
								weight /= (1.0 + distfac*d2);
							}
						}

						resultocc += weight;

					}
				}
				else if(node->child[b].node) {
					/* push child on the stack */
					stack[totstack++]= node->child[b].node;
				}
			}
		}
	}

	if(occ) *occ= resultocc;
}

static void occ_compute_passes(Render *re, OcclusionTree *tree, int totpass)
{
	float *occ, co[3], n[3];
	int pass, i;
	
	occ= MEM_callocN(sizeof(float)*tree->totface, "OcclusionPassOcc");

	for(pass=0; pass<totpass; pass++) {
		for(i=0; i<tree->totface; i++) {
			occ_face(&tree->face[i], co, n, NULL);
			VecMulf(n, -1.0f);
			VECADDFAC(co, co, n, 1e-8f);

			occ_lookup(tree, 0, &tree->face[i], co, n, &occ[i], NULL);
			if(re->test_break())
				break;
		}

		if(re->test_break())
			break;

		for(i=0; i<tree->totface; i++) {
			tree->occlusion[i] -= occ[i]; //MAX2(1.0f-occ[i], 0.0f);
			if(tree->occlusion[i] < 0.0f)
				tree->occlusion[i]= 0.0f;
		}

		occ_sum_occlusion(tree, tree->root);
	}

	MEM_freeN(occ);
}

static void sample_occ_tree(Render *re, OcclusionTree *tree, OccFace *exclude, float *co, float *n, int thread, int onlyshadow, float *skycol)
{
	float nn[3], bn[3], dxyview[3], fac, occ, occlusion, correction;
	int aocolor;

	aocolor= re->wrld.aocolor;
	if(onlyshadow)
		aocolor= WO_AOPLAIN;

	VECCOPY(nn, n);
	VecMulf(nn, -1.0f);

	occ_lookup(tree, thread, exclude, co, nn, &occ, (aocolor)? bn: NULL);

	correction= re->wrld.ao_approx_correction;

	occlusion= (1.0f-correction)*(1.0f-occ);
	CLAMP(occlusion, 0.0f, 1.0f);
	if(correction != 0.0f)
		occlusion += correction*exp(-occ);

	if(aocolor) {
		/* sky shading using bent normal */
		if(aocolor==WO_AOSKYCOL) {
			fac= 0.5*(1.0f+bn[0]*re->grvec[0]+ bn[1]*re->grvec[1]+ bn[2]*re->grvec[2]);
			skycol[0]= (1.0f-fac)*re->wrld.horr + fac*re->wrld.zenr;
			skycol[1]= (1.0f-fac)*re->wrld.horg + fac*re->wrld.zeng;
			skycol[2]= (1.0f-fac)*re->wrld.horb + fac*re->wrld.zenb;
		}
		else {	/* WO_AOSKYTEX */
			dxyview[0]= 1.0f;
			dxyview[1]= 1.0f;
			dxyview[2]= 0.0f;
			shadeSkyView(skycol, co, bn, dxyview);
		}

		VecMulf(skycol, occlusion);
	}
	else {
		skycol[0]= occlusion;
		skycol[1]= occlusion;
		skycol[2]= occlusion;
	}
}

/* ---------------------------- Caching ------------------------------- */

static OcclusionCacheSample *find_occ_sample(OcclusionCache *cache, int x, int y)
{
	x -= cache->x;
	y -= cache->y;

	x /= cache->step;
	y /= cache->step;
	x *= cache->step;
	y *= cache->step;

	if(x < 0 || x >= cache->w || y < 0 || y >= cache->h)
		return NULL;
	else
		return &cache->sample[y*cache->w + x];
}

static int sample_occ_cache(OcclusionTree *tree, float *co, float *n, int x, int y, int thread, float *col)
{
	OcclusionCache *cache;
	OcclusionCacheSample *samples[4], *sample;
	float wn[4], wz[4], wb[4], tx, ty, w, totw, mino, maxo;
	float d[3], dist2;
	int i, x1, y1, x2, y2;

	if(!tree->cache)
		return 0;
	
	/* first try to find a sample in the same pixel */
	cache= &tree->cache[thread];

	if(cache->sample && cache->step) {
		sample= &cache->sample[(y-cache->y)*cache->w + (x-cache->x)];
		if(sample->filled) {
			VECSUB(d, sample->co, co);
			dist2= INPR(d, d);
			if(dist2 < 0.5f*sample->dist2 && INPR(sample->n, n) > 0.98f) {
				VECCOPY(col, sample->col);
				return 1;
			}
		}
	}
	else
		return 0;

	/* try to interpolate between 4 neighbouring pixels */
	samples[0]= find_occ_sample(cache, x, y);
	samples[1]= find_occ_sample(cache, x+cache->step, y);
	samples[2]= find_occ_sample(cache, x, y+cache->step);
	samples[3]= find_occ_sample(cache, x+cache->step, y+cache->step);

	for(i=0; i<4; i++)
		if(!samples[i] || !samples[i]->filled)
			return 0;

	/* require intensities not being too different */
	mino= MIN4(samples[0]->intensity, samples[1]->intensity, samples[2]->intensity, samples[3]->intensity);
	maxo= MAX4(samples[0]->intensity, samples[1]->intensity, samples[2]->intensity, samples[3]->intensity);

	if(maxo - mino > 0.05f)
		return 0;

	/* compute weighted interpolation between samples */
	col[0]= col[1]= col[2]= 0.0f;
	totw= 0.0f;

	x1= samples[0]->x;
	y1= samples[0]->y;
	x2= samples[3]->x;
	y2= samples[3]->y;

	tx= (float)(x2 - x)/(float)(x2 - x1);
	ty= (float)(y2 - y)/(float)(y2 - y1);

	wb[3]= (1.0f-tx)*(1.0f-ty);
	wb[2]= (tx)*(1.0f-ty);
	wb[1]= (1.0f-tx)*(ty);
	wb[0]= tx*ty;

	for(i=0; i<4; i++) {
		VECSUB(d, samples[i]->co, co);
		dist2= INPR(d, d);

		wz[i]= 1.0f; //(samples[i]->dist2/(1e-4f + dist2));
		wn[i]= pow(INPR(samples[i]->n, n), 32.0f);

		w= wb[i]*wn[i]*wz[i];

		totw += w;
		col[0] += w*samples[i]->col[0];
		col[1] += w*samples[i]->col[1];
		col[2] += w*samples[i]->col[2];
	}

	if(totw >= 0.9f) {
		totw= 1.0f/totw;
		col[0] *= totw;
		col[1] *= totw;
		col[2] *= totw;
		return 1;
	}

	return 0;
}

static void sample_occ_cache_mesh(ShadeInput *shi)
{
	StrandRen *strand= shi->strand;
	OcclusionCacheMesh *mesh= strand->buffer->occlusionmesh;
	int *face, *index = RE_strandren_get_face(shi->obr, strand, 0);
	float w[4], *co1, *co2, *co3, *co4;

	if(mesh && index) {
		face= mesh->face[*index];

		co1= mesh->co[face[0]];
		co2= mesh->co[face[1]];
		co3= mesh->co[face[2]];
		co4= (face[3])? mesh->co[face[3]]: NULL;

		InterpWeightsQ3Dfl(co1, co2, co3, co4, strand->vert->co, w);

		shi->ao[0]= shi->ao[1]= shi->ao[2]= 0.0f;
		VECADDFAC(shi->ao, shi->ao, mesh->col[face[0]], w[0]);
		VECADDFAC(shi->ao, shi->ao, mesh->col[face[1]], w[1]);
		VECADDFAC(shi->ao, shi->ao, mesh->col[face[2]], w[2]);
		if(face[3])
			VECADDFAC(shi->ao, shi->ao, mesh->col[face[3]], w[3]);
	}
	else {
		shi->ao[0]= 1.0f;
		shi->ao[1]= 1.0f;
		shi->ao[2]= 1.0f;
	}
}

void *cache_occ_mesh(Render *re, ObjectRen *obr, DerivedMesh *dm, float mat[][4])
{
	OcclusionCacheMesh *mesh;
	MFace *mface;
	MVert *mvert;
	int a, totvert, totface;

	totvert= dm->getNumVerts(dm);
	totface= dm->getNumFaces(dm);

	mesh= re->occlusionmesh.last;
	if(mesh && mesh->obr->ob == obr->ob && mesh->obr->par == obr->par
		&& mesh->totvert==totvert && mesh->totface==totface)
		return mesh;

	mesh= MEM_callocN(sizeof(OcclusionCacheMesh), "OcclusionCacheMesh");
	mesh->obr= obr;
	mesh->totvert= totvert;
	mesh->totface= totface;
	mesh->co= MEM_callocN(sizeof(float)*3*mesh->totvert, "OcclusionMeshCo");
	mesh->face= MEM_callocN(sizeof(int)*4*mesh->totface, "OcclusionMeshFaces");
	mesh->col= MEM_callocN(sizeof(float)*3*mesh->totvert, "OcclusionMeshCol");

	mvert= dm->getVertArray(dm);
	for(a=0; a<mesh->totvert; a++, mvert++) {
		VECCOPY(mesh->co[a], mvert->co);
		Mat4MulVecfl(mat, mesh->co[a]);
	}

	mface= dm->getFaceArray(dm);
	for(a=0; a<mesh->totface; a++, mface++) {
		mesh->face[a][0]= mface->v1;
		mesh->face[a][1]= mface->v2;
		mesh->face[a][2]= mface->v3;
		mesh->face[a][3]= mface->v4;
	}

	BLI_addtail(&re->occlusionmesh, mesh);

	return mesh;
}

/* ------------------------- External Functions --------------------------- */

void make_occ_tree(Render *re)
{
	OcclusionCacheMesh *mesh;
	float col[3], co[3], n[3], *co1, *co2, *co3, *co4;
	int a, *face, *count;

	/* ugly, needed for occ_face */
	R= *re;

	re->i.infostr= "Occlusion preprocessing";
	re->stats_draw(&re->i);
	
	re->occlusiontree= occ_tree_build(re);
	
	if(re->occlusiontree) {
		if(re->wrld.ao_approx_passes)
			occ_compute_passes(re, re->occlusiontree, re->wrld.ao_approx_passes);

		for(mesh=re->occlusionmesh.first; mesh; mesh=mesh->next) {
			count= MEM_callocN(sizeof(int)*mesh->totvert, "OcclusionCount");

			for(a=0; a<mesh->totface; a++) {
				face= mesh->face[a];
				co1= mesh->co[face[0]];
				co2= mesh->co[face[1]];
				co3= mesh->co[face[2]];

				if(face[3]) {
					co4= mesh->co[face[3]];

					VecLerpf(co, co1, co3, 0.5f);
					CalcNormFloat4(co1, co2, co3, co4, n);
				}
				else {
					CalcCent3f(co, co1, co2, co3);
					CalcNormFloat(co1, co2, co3, n);
				}
				VecMulf(n, -1.0f);

				sample_occ_tree(re, re->occlusiontree, NULL, co, n, 0, 0, col);

				VECADD(mesh->col[face[0]], mesh->col[face[0]], col);
				count[face[0]]++;
				VECADD(mesh->col[face[1]], mesh->col[face[1]], col);
				count[face[1]]++;
				VECADD(mesh->col[face[2]], mesh->col[face[2]], col);
				count[face[2]]++;

				if(face[3]) {
					VECADD(mesh->col[face[3]], mesh->col[face[3]], col);
					count[face[3]]++;
				}
			}

			for(a=0; a<mesh->totvert; a++)
				if(count[a])
					VecMulf(mesh->col[a], 1.0f/count[a]);

			MEM_freeN(count);
		}
	}
}

void free_occ(Render *re)
{
	OcclusionCacheMesh *mesh;

	if(re->occlusiontree) {
		occ_free_tree(re->occlusiontree);
		re->occlusiontree = NULL;
	}

	for(mesh=re->occlusionmesh.first; mesh; mesh=mesh->next) {
		if(mesh->co) MEM_freeN(mesh->co);
		if(mesh->col) MEM_freeN(mesh->col);
		if(mesh->face) MEM_freeN(mesh->face);
	}

	BLI_freelistN(&re->occlusionmesh);
}

void sample_occ(Render *re, ShadeInput *shi)
{
	OcclusionTree *tree= re->occlusiontree;
	OcclusionCache *cache;
	OcclusionCacheSample *sample;
	OccFace exclude;
	int onlyshadow;

	if(tree) {
		if(shi->strand) {
			sample_occ_cache_mesh(shi);
		}
		/* try to get result from the cache if possible */
		else if(!sample_occ_cache(tree, shi->co, shi->vno, shi->xs, shi->ys, shi->thread, shi->ao)) {
			/* no luck, let's sample the occlusion */
			exclude.obi= shi->obi - re->objectinstance;
			exclude.facenr= shi->vlr->index;
			onlyshadow= (shi->mat->mode & MA_ONLYSHADOW);
			sample_occ_tree(re, tree, &exclude, shi->co, shi->vno, shi->thread, onlyshadow, shi->ao);

			if(G.rt & 32)
				shi->ao[2] *= 2.0f;

			/* fill result into sample, each time */
			if(tree->cache) {
				cache= &tree->cache[shi->thread];

				if(cache->sample && cache->step) {
					sample= &cache->sample[(shi->ys-cache->y)*cache->w + (shi->xs-cache->x)];
					VECCOPY(sample->co, shi->co);
					VECCOPY(sample->n, shi->vno);
					VECCOPY(sample->col, shi->ao);
					sample->intensity= MAX3(sample->col[0], sample->col[1], sample->col[2]);
					sample->dist2= INPR(shi->dxco, shi->dxco) + INPR(shi->dyco, shi->dyco);
					sample->filled= 1;
				}
			}
		}
	}
	else {
		shi->ao[0]= 1.0f;
		shi->ao[1]= 1.0f;
		shi->ao[2]= 1.0f;
	}
}

void cache_occ_samples(Render *re, RenderPart *pa, ShadeSample *ssamp)
{
	OcclusionTree *tree= re->occlusiontree;
	PixStr ps;
	OcclusionCache *cache;
	OcclusionCacheSample *sample;
	OccFace exclude;
	ShadeInput *shi;
	int *ro, *rp, *rz, onlyshadow;
	int x, y, step = CACHE_STEP;

	if(!tree->cache)
		return;

	cache= &tree->cache[pa->thread];
	cache->w= pa->rectx;
	cache->h= pa->recty;
	cache->x= pa->disprect.xmin;
	cache->y= pa->disprect.ymin;
	cache->step= step;
	cache->sample= MEM_callocN(sizeof(OcclusionCacheSample)*cache->w*cache->h, "OcclusionCacheSample");
	sample= cache->sample;

	ps.next= NULL;
	ps.mask= 0xFFFF;

	ro= pa->recto;
	rp= pa->rectp;
	rz= pa->rectz;

	/* compute a sample at every step pixels */
	for(y=pa->disprect.ymin; y<pa->disprect.ymax; y++) {
		for(x=pa->disprect.xmin; x<pa->disprect.xmax; x++, ro++, rp++, rz++, sample++) {
			if((((x - pa->disprect.xmin + step) % step) == 0 || x == pa->disprect.xmax-1) && (((y - pa->disprect.ymin + step) % step) == 0 || y == pa->disprect.ymax-1)) {
				if(*rp) {
					ps.obi= *ro;
					ps.facenr= *rp;
					ps.z= *rz;

					shade_samples_fill_with_ps(ssamp, &ps, x, y);
					shi= ssamp->shi;
					if(!shi->vlr)
						continue;

					onlyshadow= (shi->mat->mode & MA_ONLYSHADOW);
					exclude.obi= shi->obi - re->objectinstance;
					exclude.facenr= shi->vlr->index;
					sample_occ_tree(re, tree, &exclude, shi->co, shi->vno, shi->thread, onlyshadow, shi->ao);

					VECCOPY(sample->co, shi->co);
					VECCOPY(sample->n, shi->vno);
					VECCOPY(sample->col, shi->ao);
					sample->intensity= MAX3(sample->col[0], sample->col[1], sample->col[2]);
					sample->dist2= INPR(shi->dxco, shi->dxco) + INPR(shi->dyco, shi->dyco);
					sample->x= shi->xs;
					sample->y= shi->ys;
					sample->filled= 1;
				}

				if(re->test_break())
					break;
			}
		}
	}
}

void free_occ_samples(Render *re, RenderPart *pa)
{
	OcclusionTree *tree= re->occlusiontree;
	OcclusionCache *cache;

	if(tree->cache) {
		cache= &tree->cache[pa->thread];

		if(cache->sample)
			MEM_freeN(cache->sample);

		cache->w= 0;
		cache->h= 0;
		cache->step= 0;
	}
}

