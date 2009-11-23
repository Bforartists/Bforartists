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
* along with this program; if not, write to the Free Software  Foundation,
* Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
*
* The Original Code is Copyright (C) 2006 Blender Foundation.
* All rights reserved.
*
* The Original Code is: all of this file.
*
* Contributor(s): Ben Batt <benbatt@gmail.com>
*
* ***** END GPL LICENSE BLOCK *****
*
* Implementation of CustomData.
*
* BKE_customdata.h contains the function prototypes for this file.
*
*/ 

#include "BKE_customdata.h"
#include "BKE_utildefines.h" // CLAMP
#include "BLI_math.h"
#include "BLI_blenlib.h"
#include "BLI_linklist.h"
#include "BLI_mempool.h"
#include "BLI_cellalloc.h"

#include "DNA_customdata_types.h"
#include "DNA_listBase.h"
#include "DNA_meshdata_types.h"

#include "MEM_guardedalloc.h"

#include "bmesh.h"

#include <math.h>
#include <string.h>

/* number of layers to add when growing a CustomData object */
#define CUSTOMDATA_GROW 5

/********************* Layer type information **********************/
typedef struct LayerTypeInfo {
	int size;          /* the memory size of one element of this layer's data */
	char *structname;  /* name of the struct used, for file writing */
	int structnum;     /* number of structs per element, for file writing */
	char *defaultname; /* default layer name */

	/* a function to copy count elements of this layer's data
	 * (deep copy if appropriate)
	 * if NULL, memcpy is used
	 */
	void (*copy)(const void *source, void *dest, int count);

	/* a function to free any dynamically allocated components of this
	 * layer's data (note the data pointer itself should not be freed)
	 * size should be the size of one element of this layer's data (e.g.
	 * LayerTypeInfo.size)
	 */
	void (*free)(void *data, int count, int size);

	/* a function to interpolate between count source elements of this
	 * layer's data and store the result in dest
	 * if weights == NULL or sub_weights == NULL, they should default to 1
	 *
	 * weights gives the weight for each element in sources
	 * sub_weights gives the sub-element weights for each element in sources
	 *    (there should be (sub element count)^2 weights per element)
	 * count gives the number of elements in sources
	 */
	void (*interp)(void **sources, float *weights, float *sub_weights,
	               int count, void *dest);

    /* a function to swap the data in corners of the element */
	void (*swap)(void *data, int *corner_indices);

    /* a function to set a layer's data to default values. if NULL, the
	   default is assumed to be all zeros */
	void (*set_default)(void *data, int count);

    /* functions necassary for geometry collapse*/
	int (*equal)(void *data1, void *data2);
	void (*multiply)(void *data, float fac);
	void (*initminmax)(void *min, void *max);
	void (*add)(void *data1, void *data2);
	void (*dominmax)(void *data1, void *min, void *max);
	void (*copyvalue)(void *source, void *dest);
} LayerTypeInfo;

static void layerCopy_mdeformvert(const void *source, void *dest,
                                  int count)
{
	int i, size = sizeof(MDeformVert);

	memcpy(dest, source, count * size);

	for(i = 0; i < count; ++i) {
		MDeformVert *dvert = (MDeformVert *)((char *)dest + i * size);

		if(dvert->totweight) {
			MDeformWeight *dw = BLI_cellalloc_calloc(dvert->totweight * sizeof(*dw),
											"layerCopy_mdeformvert dw");

			memcpy(dw, dvert->dw, dvert->totweight * sizeof(*dw));
			dvert->dw = dw;
		}
		else
			dvert->dw = NULL;
	}
}

static void layerFree_mdeformvert(void *data, int count, int size)
{
	int i;

	for(i = 0; i < count; ++i) {
		MDeformVert *dvert = (MDeformVert *)((char *)data + i * size);

		if(dvert->dw) {
			BLI_cellalloc_free(dvert->dw);
			dvert->dw = NULL;
			dvert->totweight = 0;
		}
	}
}

static void linklist_free_simple(void *link)
{
	BLI_cellalloc_free(link);
}

static void layerInterp_mdeformvert(void **sources, float *weights,
                                    float *sub_weights, int count, void *dest)
{
	MDeformVert *dvert = dest;
	LinkNode *dest_dw = NULL; /* a list of lists of MDeformWeight pointers */
	LinkNode *node;
	int i, j, totweight;

	if(count <= 0) return;

	/* build a list of unique def_nrs for dest */
	totweight = 0;
	for(i = 0; i < count; ++i) {
		MDeformVert *source = sources[i];
		float interp_weight = weights ? weights[i] : 1.0f;

		for(j = 0; j < source->totweight; ++j) {
			MDeformWeight *dw = &source->dw[j];

			for(node = dest_dw; node; node = node->next) {
				MDeformWeight *tmp_dw = (MDeformWeight *)node->link;

				if(tmp_dw->def_nr == dw->def_nr) {
					tmp_dw->weight += dw->weight * interp_weight;
					break;
				}
			}

			/* if this def_nr is not in the list, add it */
			if(!node) {
				MDeformWeight *tmp_dw = BLI_cellalloc_calloc(sizeof(*tmp_dw),
				                            "layerInterp_mdeformvert tmp_dw");
				tmp_dw->def_nr = dw->def_nr;
				tmp_dw->weight = dw->weight * interp_weight;
				BLI_linklist_prepend(&dest_dw, tmp_dw);
				totweight++;
			}
		}
	}

	/* now we know how many unique deform weights there are, so realloc */
	if(dvert->dw) BLI_cellalloc_free(dvert->dw);

	if(totweight) {
		dvert->dw = BLI_cellalloc_calloc(sizeof(*dvert->dw) * totweight,
		                        "layerInterp_mdeformvert dvert->dw");
		dvert->totweight = totweight;

		for(i = 0, node = dest_dw; node; node = node->next, ++i)
			dvert->dw[i] = *((MDeformWeight *)node->link);
	}
	else
		memset(dvert, 0, sizeof(*dvert));

	BLI_linklist_free(dest_dw, linklist_free_simple);
}


static void layerInterp_msticky(void **sources, float *weights,
                                float *sub_weights, int count, void *dest)
{
	float co[2], w;
	MSticky *mst;
	int i;

	co[0] = co[1] = 0.0f;
	for(i = 0; i < count; i++) {
		w = weights ? weights[i] : 1.0f;
		mst = (MSticky*)sources[i];

		co[0] += w*mst->co[0];
		co[1] += w*mst->co[1];
	}

	mst = (MSticky*)dest;
	mst->co[0] = co[0];
	mst->co[1] = co[1];
}


static void layerCopy_tface(const void *source, void *dest, int count)
{
	const MTFace *source_tf = (const MTFace*)source;
	MTFace *dest_tf = (MTFace*)dest;
	int i;

	for(i = 0; i < count; ++i)
		dest_tf[i] = source_tf[i];
}

static void layerInterp_tface(void **sources, float *weights,
                              float *sub_weights, int count, void *dest)
{
	MTFace *tf = dest;
	int i, j, k;
	float uv[4][2];
	float *sub_weight;

	if(count <= 0) return;

	memset(uv, 0, sizeof(uv));

	sub_weight = sub_weights;
	for(i = 0; i < count; ++i) {
		float weight = weights ? weights[i] : 1;
		MTFace *src = sources[i];

		for(j = 0; j < 4; ++j) {
			if(sub_weights) {
				for(k = 0; k < 4; ++k, ++sub_weight) {
					float w = (*sub_weight) * weight;
					float *tmp_uv = src->uv[k];

					uv[j][0] += tmp_uv[0] * w;
					uv[j][1] += tmp_uv[1] * w;
				}
			} else {
				uv[j][0] += src->uv[j][0] * weight;
				uv[j][1] += src->uv[j][1] * weight;
			}
		}
	}

	*tf = *(MTFace *)sources[0];

	for(j = 0; j < 4; ++j) {
		tf->uv[j][0] = uv[j][0];
		tf->uv[j][1] = uv[j][1];
	}
}

static void layerSwap_tface(void *data, int *corner_indices)
{
	MTFace *tf = data;
	float uv[4][2];
	static const short pin_flags[4] =
	    { TF_PIN1, TF_PIN2, TF_PIN3, TF_PIN4 };
	static const char sel_flags[4] =
	    { TF_SEL1, TF_SEL2, TF_SEL3, TF_SEL4 };
	short unwrap = tf->unwrap & ~(TF_PIN1 | TF_PIN2 | TF_PIN3 | TF_PIN4);
	char flag = tf->flag & ~(TF_SEL1 | TF_SEL2 | TF_SEL3 | TF_SEL4);
	int j;

	for(j = 0; j < 4; ++j) {
		int source_index = corner_indices[j];

		uv[j][0] = tf->uv[source_index][0];
		uv[j][1] = tf->uv[source_index][1];

		// swap pinning flags around
		if(tf->unwrap & pin_flags[source_index]) {
			unwrap |= pin_flags[j];
		}

		// swap selection flags around
		if(tf->flag & sel_flags[source_index]) {
			flag |= sel_flags[j];
		}
	}

	memcpy(tf->uv, uv, sizeof(tf->uv));
	tf->unwrap = unwrap;
	tf->flag = flag;
}

static void layerDefault_tface(void *data, int count)
{
	static MTFace default_tf = {{{0, 0}, {1, 0}, {1, 1}, {0, 1}}, NULL,
	                           0, 0, TF_DYNAMIC, 0, 0};
	MTFace *tf = (MTFace*)data;
	int i;

	for(i = 0; i < count; i++)
		tf[i] = default_tf;
}

static void layerCopy_origspace_face(const void *source, void *dest, int count)
{
	const OrigSpaceFace *source_tf = (const OrigSpaceFace*)source;
	OrigSpaceFace *dest_tf = (OrigSpaceFace*)dest;
	int i;

	for(i = 0; i < count; ++i)
		dest_tf[i] = source_tf[i];
}

static void layerInterp_origspace_face(void **sources, float *weights,
							  float *sub_weights, int count, void *dest)
{
	OrigSpaceFace *osf = dest;
	int i, j, k;
	float uv[4][2];
	float *sub_weight;

	if(count <= 0) return;

	memset(uv, 0, sizeof(uv));

	sub_weight = sub_weights;
	for(i = 0; i < count; ++i) {
		float weight = weights ? weights[i] : 1;
		OrigSpaceFace *src = sources[i];

		for(j = 0; j < 4; ++j) {
			if(sub_weights) {
				for(k = 0; k < 4; ++k, ++sub_weight) {
					float w = (*sub_weight) * weight;
					float *tmp_uv = src->uv[k];

					uv[j][0] += tmp_uv[0] * w;
					uv[j][1] += tmp_uv[1] * w;
				}
			} else {
				uv[j][0] += src->uv[j][0] * weight;
				uv[j][1] += src->uv[j][1] * weight;
			}
		}
	}

	*osf = *(OrigSpaceFace *)sources[0];
	for(j = 0; j < 4; ++j) {
		osf->uv[j][0] = uv[j][0];
		osf->uv[j][1] = uv[j][1];
	}
}

static void layerSwap_origspace_face(void *data, int *corner_indices)
{
	OrigSpaceFace *osf = data;
	float uv[4][2];
	int j;

	for(j = 0; j < 4; ++j) {
		uv[j][0] = osf->uv[corner_indices[j]][0];
		uv[j][1] = osf->uv[corner_indices[j]][1];
	}
	memcpy(osf->uv, uv, sizeof(osf->uv));
}

static void layerDefault_origspace_face(void *data, int count)
{
	static OrigSpaceFace default_osf = {{{0, 0}, {1, 0}, {1, 1}, {0, 1}}};
	OrigSpaceFace *osf = (OrigSpaceFace*)data;
	int i;

	for(i = 0; i < count; i++)
		osf[i] = default_osf;
}

/* Adapted from sculptmode.c */
static void mdisps_bilinear(float out[3], float (*disps)[3], int st, float u, float v)
{
	int x, y, x2, y2;
	const int st_max = st - 1;
	float urat, vrat, uopp;
	float d[4][3], d2[2][3];

	if(u < 0)
		u = 0;
	else if(u >= st)
		u = st_max;
	if(v < 0)
		v = 0;
	else if(v >= st)
		v = st_max;

	x = floor(u);
	y = floor(v);
	x2 = x + 1;
	y2 = y + 1;

	if(x2 >= st) x2 = st_max;
	if(y2 >= st) y2 = st_max;
	
	urat = u - x;
	vrat = v - y;
	uopp = 1 - urat;

	copy_v3_v3(d[0], disps[y * st + x]);
	copy_v3_v3(d[1], disps[y * st + x2]);
	copy_v3_v3(d[2], disps[y2 * st + x]);
	copy_v3_v3(d[3], disps[y2 * st + x2]);
	mul_v3_fl(d[0], uopp);
	mul_v3_fl(d[1], urat);
	mul_v3_fl(d[2], uopp);
	mul_v3_fl(d[3], urat);

	add_v3_v3v3(d2[0], d[0], d[1]);
	add_v3_v3v3(d2[1], d[2], d[3]);
	mul_v3_fl(d2[0], 1 - vrat);
	mul_v3_fl(d2[1], vrat);

	add_v3_v3v3(out, d2[0], d2[1]);
}

static void layerSwap_mdisps(void *data, int *ci)
{
	MDisps *s = data;
	float (*d)[3] = NULL;
	int x, y, st;

	if(!(ci[0] == 2 && ci[1] == 3 && ci[2] == 0 && ci[3] == 1)) return;

	d = MEM_callocN(sizeof(float) * 3 * s->totdisp, "mdisps swap");
	st = sqrt(s->totdisp);

	for(y = 0; y < st; ++y) {
		for(x = 0; x < st; ++x) {
			copy_v3_v3(d[(st - y - 1) * st + (st - x - 1)], s->disps[y * st + x]);
		}
	}
	
	if(s->disps)
		MEM_freeN(s->disps);
	s->disps = d;
}

static void layerInterp_mdisps(void **sources, float *weights, float *sub_weights,
			       int count, void *dest)
{
	MDisps *d = dest;
	MDisps *s = NULL;
	int st, stl;
	int i, x, y;
	float crn[4][2];
	float (*sw)[4] = NULL;

	/* Initialize the destination */
	for(i = 0; i < d->totdisp; ++i) {
		float z[3] = {0,0,0};
		copy_v3_v3(d->disps[i], z);
	}

	/* For now, some restrictions on the input */
	if(count != 1 || !sub_weights) return;

	st = sqrt(d->totdisp);
	stl = st - 1;

	sw = (void*)sub_weights;
	for(i = 0; i < 4; ++i) {
		crn[i][0] = 0 * sw[i][0] + stl * sw[i][1] + stl * sw[i][2] + 0 * sw[i][3];
		crn[i][1] = 0 * sw[i][0] + 0 * sw[i][1] + stl * sw[i][2] + stl * sw[i][3];
	}

	s = sources[0];
	for(y = 0; y < st; ++y) {
		for(x = 0; x < st; ++x) {
			/* One suspects this code could be cleaner. */
			float xl = (float)x / (st - 1);
			float yl = (float)y / (st - 1);
			float mid1[2] = {crn[0][0] * (1 - xl) + crn[1][0] * xl,
					 crn[0][1] * (1 - xl) + crn[1][1] * xl};
			float mid2[2] = {crn[3][0] * (1 - xl) + crn[2][0] * xl,
					 crn[3][1] * (1 - xl) + crn[2][1] * xl};
			float mid3[2] = {mid1[0] * (1 - yl) + mid2[0] * yl,
					 mid1[1] * (1 - yl) + mid2[1] * yl};

			float srcdisp[3];

			mdisps_bilinear(srcdisp, s->disps, st, mid3[0], mid3[1]);
			copy_v3_v3(d->disps[y * st + x], srcdisp);
		}
	}
}

static void layerCopy_mdisps(const void *source, void *dest, int count)
{
	int i;
	const MDisps *s = source;
	MDisps *d = dest;

	for(i = 0; i < count; ++i) {
		if(s[i].disps) {
			d[i].disps = MEM_dupallocN(s[i].disps);
			d[i].totdisp = s[i].totdisp;
		}
		else {
			d[i].disps = NULL;
			d[i].totdisp = 0;
		}
		
	}
}

static void layerFree_mdisps(void *data, int count, int size)
{
	int i;
	MDisps *d = data;

	for(i = 0; i < count; ++i) {
		if(d[i].disps)
			MEM_freeN(d[i].disps);
		d[i].disps = NULL;
		d[i].totdisp = 0;
	}
}

/* --------- */
static void layerCopyValue_mloopcol(void *source, void *dest)
{
	MLoopCol *m1 = source, *m2 = dest;
	
	m2->r = m1->r;
	m2->g = m1->g;
	m2->b = m1->b;
	m2->a = m1->a;
}

static int layerEqual_mloopcol(void *data1, void *data2)
{
	MLoopCol *m1 = data1, *m2 = data2;
	float r, g, b, a;

	r = m1->r - m2->r;
	g = m1->g - m2->g;
	b = m1->b - m2->b;
	a = m1->a - m2->a;

	return r*r + g*g + b*b + a*a < 0.001;
}

static void layerMultiply_mloopcol(void *data, float fac)
{
	MLoopCol *m = data;

	m->r = (float)m->r * fac;
	m->g = (float)m->g * fac;
	m->b = (float)m->b * fac;
	m->a = (float)m->a * fac;
}

static void layerAdd_mloopcol(void *data1, void *data2)
{
	MLoopCol *m = data1, *m2 = data2;

	m->r += m2->r;
	m->g += m2->g;
	m->b += m2->b;
	m->a += m2->a;
}

static void layerDoMinMax_mloopcol(void *data, void *vmin, void *vmax)
{
	MLoopCol *m = data;
	MLoopCol *min = vmin, *max = vmax;

	if (m->r < min->r) min->r = m->r;
	if (m->g < min->g) min->g = m->g;
	if (m->b < min->b) min->b = m->b;
	if (m->a < min->a) min->a = m->a;
	
	if (m->r > max->r) max->r = m->r;
	if (m->g > max->g) max->g = m->g;
	if (m->b > max->b) max->b = m->b;
	if (m->a > max->a) max->a = m->a;
}

static void layerInitMinMax_mloopcol(void *vmin, void *vmax)
{
	MLoopCol *min = vmin, *max = vmax;

	min->r = 255;
	min->g = 255;
	min->b = 255;
	min->a = 255;

	max->r = 0;
	max->g = 0;
	max->b = 0;
	max->a = 0;
}

static void layerDefault_mloopcol(void *data, int count)
{
	MLoopCol default_mloopcol = {255,255,255,255};
	MLoopCol *mlcol = (MLoopCol*)data;
	int i;

	for(i = 0; i < count; i++)
		mlcol[i] = default_mloopcol;

}

static void layerInterp_mloopcol(void **sources, float *weights,
				float *sub_weights, int count, void *dest)
{
	MLoopCol *mc = dest;
	int i;
	float *sub_weight;
	struct {
		float a;
		float r;
		float g;
		float b;
	} col;
	col.a = col.r = col.g = col.b = 0;

	sub_weight = sub_weights;
	for(i = 0; i < count; ++i){
		float weight = weights ? weights[i] : 1;
		MLoopCol *src = sources[i];
		if(sub_weights){
			col.a += src->a * (*sub_weight) * weight;
			col.r += src->r * (*sub_weight) * weight;
			col.g += src->g * (*sub_weight) * weight;
			col.b += src->b * (*sub_weight) * weight;
			sub_weight++;		
		} else {
			col.a += src->a * weight;
			col.r += src->r * weight;
			col.g += src->g * weight;
			col.b += src->b * weight;
		}
	}
	
	/* Subdivide smooth or fractal can cause problems without clamping
	 * although weights should also not cause this situation */
	CLAMP(col.a, 0.0f, 255.0f);
	CLAMP(col.r, 0.0f, 255.0f);
	CLAMP(col.g, 0.0f, 255.0f);
	CLAMP(col.b, 0.0f, 255.0f);
	
	mc->a = (int)col.a;
	mc->r = (int)col.r;
	mc->g = (int)col.g;
	mc->b = (int)col.b;
}

static void layerCopyValue_mloopuv(void *source, void *dest)
{
	MLoopUV *luv1 = source, *luv2 = dest;
	
	luv2->uv[0] = luv1->uv[0];
	luv2->uv[1] = luv1->uv[1];
}

static int layerEqual_mloopuv(void *data1, void *data2)
{
	MLoopUV *luv1 = data1, *luv2 = data2;
	float u, v;

	u = luv1->uv[0] - luv2->uv[0];
	v = luv1->uv[1] - luv2->uv[1];

	return u*u + v*v < 0.00001;
}

static void layerMultiply_mloopuv(void *data, float fac)
{
	MLoopUV *luv = data;

	luv->uv[0] *= fac;
	luv->uv[1] *= fac;
}

static void layerInitMinMax_mloopuv(void *vmin, void *vmax)
{
	MLoopUV *min = vmin, *max = vmax;

	INIT_MINMAX2(min->uv, max->uv);
}

static void layerDoMinMax_mloopuv(void *data, void *vmin, void *vmax)
{
	MLoopUV *min = vmin, *max = vmax, *luv = data;

	DO_MINMAX2(luv->uv, min->uv, max->uv);
}

static void layerAdd_mloopuv(void *data1, void *data2)
{
	MLoopUV *l1 = data1, *l2 = data2;

	l1->uv[0] += l2->uv[0];
	l1->uv[1] += l2->uv[1];
}

static void layerInterp_mloopuv(void **sources, float *weights,
				float *sub_weights, int count, void *dest)
{
	MLoopUV *mluv = dest;
	int i;
	float *sub_weight;
	struct {
		float u;
		float v;
	}uv;
	uv.u = uv.v = 0.0;

	sub_weight = sub_weights;
	for(i = 0; i < count; ++i){
		float weight = weights ? weights[i] : 1;
		MLoopUV *src = sources[i];
		if(sub_weights){
			uv.u += src->uv[0] * (*sub_weight) * weight;
			uv.v += src->uv[1] * (*sub_weight) * weight;
			sub_weight++;		
		} else {
			uv.u += src->uv[0] * weight;
			uv.v += src->uv[1] * weight;
		}
	}
	mluv->uv[0] = uv.u;
	mluv->uv[1] = uv.v;
}

static void layerInterp_mcol(void **sources, float *weights,
                             float *sub_weights, int count, void *dest)
{
	MCol *mc = dest;
	int i, j, k;
	struct {
		float a;
		float r;
		float g;
		float b;
	} col[4];
	float *sub_weight;

	if(count <= 0) return;

	memset(col, 0, sizeof(col));
	
	sub_weight = sub_weights;
	for(i = 0; i < count; ++i) {
		float weight = weights ? weights[i] : 1;

		for(j = 0; j < 4; ++j) {
			if(sub_weights) {
				MCol *src = sources[i];
				for(k = 0; k < 4; ++k, ++sub_weight, ++src) {
					col[j].a += src->a * (*sub_weight) * weight;
					col[j].r += src->r * (*sub_weight) * weight;
					col[j].g += src->g * (*sub_weight) * weight;
					col[j].b += src->b * (*sub_weight) * weight;
				}
			} else {
				MCol *src = sources[i];
				col[j].a += src[j].a * weight;
				col[j].r += src[j].r * weight;
				col[j].g += src[j].g * weight;
				col[j].b += src[j].b * weight;
			}
		}
	}

	for(j = 0; j < 4; ++j) {
		
		/* Subdivide smooth or fractal can cause problems without clamping
		 * although weights should also not cause this situation */
		CLAMP(col[j].a, 0.0f, 255.0f);
		CLAMP(col[j].r, 0.0f, 255.0f);
		CLAMP(col[j].g, 0.0f, 255.0f);
		CLAMP(col[j].b, 0.0f, 255.0f);
		
		mc[j].a = (int)col[j].a;
		mc[j].r = (int)col[j].r;
		mc[j].g = (int)col[j].g;
		mc[j].b = (int)col[j].b;
	}
}

static void layerSwap_mcol(void *data, int *corner_indices)
{
	MCol *mcol = data;
	MCol col[4];
	int j;

	for(j = 0; j < 4; ++j)
		col[j] = mcol[corner_indices[j]];

	memcpy(mcol, col, sizeof(col));
}

static void layerDefault_mcol(void *data, int count)
{
	static MCol default_mcol = {255, 255, 255, 255};
	MCol *mcol = (MCol*)data;
	int i;

	for(i = 0; i < 4*count; i++)
		mcol[i] = default_mcol;
}

static void layerInterp_shapekey(void **sources, float *weights,
                             float *sub_weights, int count, void *dest)
{
	float *co = dest, *src;
	float **in = sources;
	int i, j, k;

	if(count <= 0) return;

	memset(co, 0, sizeof(float)*3);
	
	for(i = 0; i < count; ++i) {
		float weight = weights ? weights[i] : 1.0f;
		
		src = in[i];
		co[0] += src[0] * weight;
		co[1] += src[1] * weight;
		co[2] += src[2] * weight;
	}
}

const LayerTypeInfo LAYERTYPEINFO[CD_NUMTYPES] = {
	{sizeof(MVert), "MVert", 1, NULL, NULL, NULL, NULL, NULL, NULL},
	{sizeof(MSticky), "MSticky", 1, NULL, NULL, NULL, layerInterp_msticky, NULL,
	 NULL},
	{sizeof(MDeformVert), "MDeformVert", 1, NULL, layerCopy_mdeformvert,
	 layerFree_mdeformvert, layerInterp_mdeformvert, NULL, NULL},
	{sizeof(MEdge), "MEdge", 1, NULL, NULL, NULL, NULL, NULL, NULL},
	{sizeof(MFace), "MFace", 1, NULL, NULL, NULL, NULL, NULL, NULL},
	{sizeof(MTFace), "MTFace", 1, "UVTex", layerCopy_tface, NULL,
	 layerInterp_tface, layerSwap_tface, layerDefault_tface},
	/* 4 MCol structs per face */
	{sizeof(MCol)*4, "MCol", 4, "Col", NULL, NULL, layerInterp_mcol,
	 layerSwap_mcol, layerDefault_mcol},
	{sizeof(int), "", 0, NULL, NULL, NULL, NULL, NULL, NULL},
	/* 3 floats per normal vector */
	{sizeof(float)*3, "", 0, NULL, NULL, NULL, NULL, NULL, NULL},
	{sizeof(int), "", 0, NULL, NULL, NULL, NULL, NULL, NULL},
	{sizeof(MFloatProperty), "MFloatProperty",1,"Float",NULL,NULL,NULL,NULL},
	{sizeof(MIntProperty), "MIntProperty",1,"Int",NULL,NULL,NULL,NULL},
	{sizeof(MStringProperty), "MStringProperty",1,"String",NULL,NULL,NULL,NULL},
	{sizeof(OrigSpaceFace), "OrigSpaceFace", 1, "UVTex", layerCopy_origspace_face, NULL,
	 layerInterp_origspace_face, layerSwap_origspace_face, layerDefault_origspace_face},
	{sizeof(float)*3, "", 0, NULL, NULL, NULL, NULL, NULL, NULL},
	{sizeof(MTexPoly), "MTexPoly", 1, "Face Texture", NULL, NULL, NULL, NULL, NULL},
	{sizeof(MLoopUV), "MLoopUV", 1, "UV coord", NULL, NULL, layerInterp_mloopuv, NULL, NULL,
	 layerEqual_mloopuv, layerMultiply_mloopuv, layerInitMinMax_mloopuv, 
	 layerAdd_mloopuv, layerDoMinMax_mloopuv, layerCopyValue_mloopuv},
	{sizeof(MLoopCol), "MLoopCol", 1, "Col", NULL, NULL, layerInterp_mloopcol, NULL, 
	 layerDefault_mloopcol, layerEqual_mloopcol, layerMultiply_mloopcol, layerInitMinMax_mloopcol, 
	 layerAdd_mloopcol, layerDoMinMax_mloopcol, layerCopyValue_mloopcol},
	{sizeof(float)*3*4, "", 0, NULL, NULL, NULL, NULL, NULL, NULL},
	{sizeof(MDisps), "MDisps", 1, NULL, layerCopy_mdisps,
	 layerFree_mdisps, layerInterp_mdisps, layerSwap_mdisps, NULL},
	{sizeof(MCol)*4, "MCol", 4, "WeightCol", NULL, NULL, layerInterp_mcol,
	 layerSwap_mcol, layerDefault_mcol},
	{sizeof(MPoly), "MPoly", 1, "NGon Face", NULL, NULL, NULL, NULL, NULL},
	{sizeof(MLoop), "MLoop", 1, "NGon Face-Vertex", NULL, NULL, NULL, NULL, NULL},
	{sizeof(MLoopCol), "MLoopCol", 1, "WeightLoopCol", NULL, NULL, layerInterp_mloopcol, NULL, 
	 layerDefault_mloopcol, layerEqual_mloopcol, layerMultiply_mloopcol, layerInitMinMax_mloopcol, 
	 layerAdd_mloopcol, layerDoMinMax_mloopcol, layerCopyValue_mloopcol},
	{sizeof(MCol)*4, "MCol", 4, "IDCol", NULL, NULL, layerInterp_mcol,
	 layerSwap_mcol, layerDefault_mcol},
	{sizeof(MCol)*4, "MCol", 4, "TextureCol", NULL, NULL, layerInterp_mcol,
	 layerSwap_mcol, layerDefault_mcol},
	{sizeof(int), "", 0, NULL, NULL, NULL, NULL, NULL, NULL},
	{sizeof(float)*3, "", 0, "ShapeKey", NULL, NULL, layerInterp_shapekey},
};

const char *LAYERTYPENAMES[CD_NUMTYPES] = {
	"CDMVert", "CDMSticky", "CDMDeformVert", "CDMEdge", "CDMFace", "CDMTFace",
	"CDMCol", "CDOrigIndex", "CDNormal", "CDFlags","CDMFloatProperty",
	"CDMIntProperty","CDMStringProperty", "CDOrigSpace", "CDOrco", "CDMTexPoly", "CDMLoopUV",
	"CDMloopCol", "CDTangent", "CDMDisps", "CDWeightMCol", "CDMPoly", 
	"CDMLoop", "CDMLoopCol", "CDIDCol", "CDTextureCol", "CDShapeKeyIndex", "CDShapeKey"};

const CustomDataMask CD_MASK_BAREMESH =
	CD_MASK_MVERT | CD_MASK_MEDGE | CD_MASK_MFACE | CD_MASK_MLOOP | CD_MASK_MPOLY;
const CustomDataMask CD_MASK_MESH =
	CD_MASK_MVERT | CD_MASK_MEDGE | CD_MASK_MFACE |
	CD_MASK_MSTICKY | CD_MASK_MDEFORMVERT | CD_MASK_MTFACE | CD_MASK_MCOL |
	CD_MASK_PROP_FLT | CD_MASK_PROP_INT | CD_MASK_PROP_STR | CD_MASK_MDISPS |
	CD_MASK_MLOOPUV | CD_MASK_MLOOPCOL | CD_MASK_MPOLY | CD_MASK_MLOOP |
	CD_MASK_MTEXPOLY | CD_MASK_NORMAL;
const CustomDataMask CD_MASK_EDITMESH =
	CD_MASK_MSTICKY | CD_MASK_MDEFORMVERT | CD_MASK_MTFACE | CD_MASK_MLOOPUV |
	CD_MASK_MLOOPCOL | CD_MASK_MTEXPOLY | CD_MASK_SHAPE_KEYINDEX |
	CD_MASK_MCOL|CD_MASK_PROP_FLT | CD_MASK_PROP_INT | CD_MASK_PROP_STR |
	CD_MASK_MDISPS | CD_MASK_SHAPEKEY;
const CustomDataMask CD_MASK_DERIVEDMESH =
	CD_MASK_MSTICKY | CD_MASK_MDEFORMVERT | CD_MASK_MTFACE |
	CD_MASK_MCOL | CD_MASK_ORIGINDEX | CD_MASK_PROP_FLT | CD_MASK_PROP_INT |
	CD_MASK_MLOOPUV | CD_MASK_MLOOPCOL | CD_MASK_MTEXPOLY | CD_MASK_WEIGHT_MLOOPCOL |
	CD_MASK_PROP_STR | CD_MASK_ORIGSPACE | CD_MASK_ORCO | CD_MASK_TANGENT | 
	CD_MASK_WEIGHT_MCOL | CD_MASK_NORMAL;
const CustomDataMask CD_MASK_BMESH = CD_MASK_MLOOPUV | CD_MASK_MLOOPCOL | CD_MASK_MTEXPOLY |
	CD_MASK_MSTICKY | CD_MASK_MDEFORMVERT | CD_MASK_PROP_FLT | CD_MASK_PROP_INT | 
	CD_MASK_PROP_STR | CD_MASK_SHAPEKEY | CD_MASK_SHAPE_KEYINDEX;
const CustomDataMask CD_MASK_FACECORNERS =
	CD_MASK_MTFACE | CD_MASK_MCOL | CD_MASK_MTEXPOLY | CD_MASK_MLOOPUV |
	CD_MASK_MLOOPCOL;

static const LayerTypeInfo *layerType_getInfo(int type)
{
	if(type < 0 || type >= CD_NUMTYPES) return NULL;

	return &LAYERTYPEINFO[type];
}

static const char *layerType_getName(int type)
{
	if(type < 0 || type >= CD_NUMTYPES) return NULL;

	return LAYERTYPENAMES[type];
}

/********************* CustomData functions *********************/
static void customData_update_offsets(CustomData *data);

static CustomDataLayer *customData_add_layer__internal(CustomData *data,
	int type, int alloctype, void *layerdata, int totelem, const char *name);

void customData_update_typemap(CustomData *data)
{
	int i, lasttype = -1;

	for (i=0; i<CD_NUMTYPES; i++) {
		data->typemap[i] = -1;
	}

	for (i=0; i<data->totlayer; i++) {
		if (data->layers[i].type != lasttype) {
			data->typemap[data->layers[i].type] = i;
		}
		lasttype = data->layers[i].type;
	}
}

void CustomData_merge(const struct CustomData *source, struct CustomData *dest,
                      CustomDataMask mask, int alloctype, int totelem)
{
	const LayerTypeInfo *typeInfo;
	CustomDataLayer *layer, *newlayer;
	int i, type, number = 0, lasttype = -1, lastactive = 0, lastrender = 0, lastclone = 0, lastmask = 0;
	
	for(i = 0; i < source->totlayer; ++i) {
		layer = &source->layers[i];
		typeInfo = layerType_getInfo(layer->type);

		type = layer->type;

		if (type != lasttype) {
			number = 0;
			lastactive = layer->active;
			lastrender = layer->active_rnd;
			lastclone = layer->active_clone;
			lastmask = layer->active_mask;
			lasttype = type;
		}
		else
			number++;

		if(layer->flag & CD_FLAG_NOCOPY) continue;
		else if(!((int)mask & (int)(1 << (int)type))) continue;
		else if(number+1 < CustomData_number_of_layers(dest, type)) continue;

		if((alloctype == CD_ASSIGN) && (layer->flag & CD_FLAG_NOFREE))
			newlayer = customData_add_layer__internal(dest, type, CD_REFERENCE,
				layer->data, totelem, layer->name);
		else
			newlayer = customData_add_layer__internal(dest, type, alloctype,
				layer->data, totelem, layer->name);
		
		if(newlayer) {
			newlayer->active = lastactive;
			newlayer->active_rnd = lastrender;
			newlayer->active_clone = lastclone;
			newlayer->active_mask = lastmask;
		}
	}

	customData_update_typemap(dest);
}

void CustomData_copy(const struct CustomData *source, struct CustomData *dest,
                     CustomDataMask mask, int alloctype, int totelem)
{
	memset(dest, 0, sizeof(*dest));

	CustomData_merge(source, dest, mask, alloctype, totelem);
}

static void customData_free_layer__internal(CustomDataLayer *layer, int totelem)
{
	const LayerTypeInfo *typeInfo;

	if(!(layer->flag & CD_FLAG_NOFREE) && layer->data) {
		typeInfo = layerType_getInfo(layer->type);

		if(typeInfo->free)
			typeInfo->free(layer->data, totelem, typeInfo->size);

		if(layer->data)
			MEM_freeN(layer->data);
	}
}

void CustomData_free(CustomData *data, int totelem)
{
	int i;

	for(i = 0; i < data->totlayer; ++i)
		customData_free_layer__internal(&data->layers[i], totelem);

	if(data->layers)
		MEM_freeN(data->layers);
	
	memset(data, 0, sizeof(*data));
}

static void customData_update_offsets(CustomData *data)
{
	const LayerTypeInfo *typeInfo;
	int i, offset = 0;

	for(i = 0; i < data->totlayer; ++i) {
		typeInfo = layerType_getInfo(data->layers[i].type);

		data->layers[i].offset = offset;
		offset += typeInfo->size;
	}

	data->totsize = offset;
}

int CustomData_get_layer_index(const CustomData *data, int type)
{
	int i; 

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			return i;

	return -1;
}

int CustomData_get_layer_index_n(const struct CustomData *data, int type, int n)
{
	int i; 

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			return i + n;

	return -1;	
}

int CustomData_get_named_layer_index(const CustomData *data, int type, char *name)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type && strcmp(data->layers[i].name, name)==0)
			return i;

	return -1;
}

int CustomData_get_active_layer_index(const CustomData *data, int type)
{
	if (!data->totlayer)
		return -1;

	if (data->typemap[type] != -1) {
		return data->typemap[type] + data->layers[data->typemap[type]].active;
	}

	return -1;
}

int CustomData_get_render_layer_index(const CustomData *data, int type)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			return i + data->layers[i].active_rnd;

	return -1;
}

int CustomData_get_clone_layer_index(const CustomData *data, int type)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			return i + data->layers[i].active_clone;

	return -1;
}

int CustomData_get_mask_layer_index(const CustomData *data, int type)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			return i + data->layers[i].active_mask;

	return -1;
}

int CustomData_get_active_layer(const CustomData *data, int type)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			return data->layers[i].active;

	return -1;
}

int CustomData_get_render_layer(const CustomData *data, int type)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			return data->layers[i].active_rnd;

	return -1;
}

int CustomData_get_clone_layer(const CustomData *data, int type)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			return data->layers[i].active_clone;

	return -1;
}

int CustomData_get_mask_layer(const CustomData *data, int type)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			return data->layers[i].active_mask;

	return -1;
}

void CustomData_set_layer_active(CustomData *data, int type, int n)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			data->layers[i].active = n;
}

void CustomData_set_layer_render(CustomData *data, int type, int n)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			data->layers[i].active_rnd = n;
}

void CustomData_set_layer_clone(CustomData *data, int type, int n)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			data->layers[i].active_clone = n;
}

void CustomData_set_layer_mask(CustomData *data, int type, int n)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			data->layers[i].active_mask = n;
}

/* for using with an index from CustomData_get_active_layer_index and CustomData_get_render_layer_index */
void CustomData_set_layer_active_index(CustomData *data, int type, int n)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			data->layers[i].active = n-i;
}

void CustomData_set_layer_render_index(CustomData *data, int type, int n)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			data->layers[i].active_rnd = n-i;
}

void CustomData_set_layer_clone_index(CustomData *data, int type, int n)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			data->layers[i].active_clone = n-i;
}

void CustomData_set_layer_mask_index(CustomData *data, int type, int n)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			data->layers[i].active_mask = n-i;
}

void CustomData_set_layer_flag(struct CustomData *data, int type, int flag)
{
	int i;

	for(i=0; i < data->totlayer; ++i)
		if(data->layers[i].type == type)
			data->layers[i].flag |= flag;
}

static int customData_resize(CustomData *data, int amount)
{
	CustomDataLayer *tmp = MEM_callocN(sizeof(*tmp)*(data->maxlayer + amount),
                                       "CustomData->layers");
	if(!tmp) return 0;

	data->maxlayer += amount;
	if (data->layers) {
		memcpy(tmp, data->layers, sizeof(*tmp) * data->totlayer);
		MEM_freeN(data->layers);
	}
	data->layers = tmp;

	return 1;
}

static CustomDataLayer *customData_add_layer__internal(CustomData *data,
	int type, int alloctype, void *layerdata, int totelem, const char *name)
{
	const LayerTypeInfo *typeInfo= layerType_getInfo(type);
	int size = typeInfo->size * totelem, flag = 0, index = data->totlayer;
	void *newlayerdata;

	if (!typeInfo->defaultname && CustomData_has_layer(data, type))
		return &data->layers[CustomData_get_layer_index(data, type)];

	if((alloctype == CD_ASSIGN) || (alloctype == CD_REFERENCE)) {
		newlayerdata = layerdata;
	}
	else {
		newlayerdata = MEM_callocN(size, layerType_getName(type));
		if(!newlayerdata)
			return NULL;
	}

	if (alloctype == CD_DUPLICATE) {
		if(typeInfo->copy)
			typeInfo->copy(layerdata, newlayerdata, totelem);
		else
			memcpy(newlayerdata, layerdata, size);
	}
	else if (alloctype == CD_DEFAULT) {
		if(typeInfo->set_default)
			typeInfo->set_default((char*)newlayerdata, totelem);
	}
	else if (alloctype == CD_REFERENCE)
		flag |= CD_FLAG_NOFREE;

	if(index >= data->maxlayer) {
		if(!customData_resize(data, CUSTOMDATA_GROW)) {
			if(newlayerdata != layerdata)
				MEM_freeN(newlayerdata);
			return NULL;
		}
	}
	
	data->totlayer++;

	/* keep layers ordered by type */
	for( ; index > 0 && data->layers[index - 1].type > type; --index)
		data->layers[index] = data->layers[index - 1];

	data->layers[index].type = type;
	data->layers[index].flag = flag;
	data->layers[index].data = newlayerdata;

	if(name) {
		strcpy(data->layers[index].name, name);
		CustomData_set_layer_unique_name(data, index);
	}
	else
		data->layers[index].name[0] = '\0';

	if(index > 0 && data->layers[index-1].type == type) {
		data->layers[index].active = data->layers[index-1].active;
		data->layers[index].active_rnd = data->layers[index-1].active_rnd;
		data->layers[index].active_clone = data->layers[index-1].active_clone;
		data->layers[index].active_mask = data->layers[index-1].active_mask;
	} else {
		data->layers[index].active = 0;
		data->layers[index].active_rnd = 0;
		data->layers[index].active_clone = 0;
		data->layers[index].active_mask = 0;
	}
	
	customData_update_offsets(data);

	return &data->layers[index];
}

void *CustomData_add_layer(CustomData *data, int type, int alloctype,
                           void *layerdata, int totelem)
{
	CustomDataLayer *layer;
	const LayerTypeInfo *typeInfo= layerType_getInfo(type);
	
	layer = customData_add_layer__internal(data, type, alloctype, layerdata,
	                                       totelem, typeInfo->defaultname);
	customData_update_typemap(data);

	if(layer)
		return layer->data;

	return NULL;
}

/*same as above but accepts a name*/
void *CustomData_add_layer_named(CustomData *data, int type, int alloctype,
                           void *layerdata, int totelem, char *name)
{
	CustomDataLayer *layer;
	
	layer = customData_add_layer__internal(data, type, alloctype, layerdata,
	                                       totelem, name);
	customData_update_typemap(data);

	if(layer)
		return layer->data;

	return NULL;
}


int CustomData_free_layer(CustomData *data, int type, int totelem, int index)
{
	int i;
	
	if (index < 0) return 0;

	customData_free_layer__internal(&data->layers[index], totelem);

	for (i=index+1; i < data->totlayer; ++i)
		data->layers[i-1] = data->layers[i];

	data->totlayer--;

	/* if layer was last of type in array, set new active layer */
	if ((index >= data->totlayer) || (data->layers[index].type != type)) {
		i = CustomData_get_layer_index(data, type);
		
		if (i >= 0)
			for (; i < data->totlayer && data->layers[i].type == type; i++) {
				data->layers[i].active--;
				data->layers[i].active_rnd--;
				data->layers[i].active_clone--;
				data->layers[i].active_mask--;
			}
	}

	if (data->totlayer <= data->maxlayer-CUSTOMDATA_GROW)
		customData_resize(data, -CUSTOMDATA_GROW);

	customData_update_offsets(data);
	customData_update_typemap(data);

	return 1;
}

int CustomData_free_layer_active(CustomData *data, int type, int totelem)
{
	int index = 0;
	index = CustomData_get_active_layer_index(data, type);
	if (index < 0) return 0;
	return CustomData_free_layer(data, type, totelem, index);
}


void CustomData_free_layers(CustomData *data, int type, int totelem)
{
	while (CustomData_has_layer(data, type))
		CustomData_free_layer_active(data, type, totelem);
}

int CustomData_has_layer(const CustomData *data, int type)
{
	return (CustomData_get_layer_index(data, type) != -1);
}

int CustomData_number_of_layers(const CustomData *data, int type)
{
	int i, number = 0;

	for(i = 0; i < data->totlayer; i++)
		if(data->layers[i].type == type)
			number++;
	
	return number;
}

void *CustomData_duplicate_referenced_layer(struct CustomData *data, int type)
{
	CustomDataLayer *layer;
	int layer_index;

	/* get the layer index of the first layer of type */
	layer_index = CustomData_get_active_layer_index(data, type);
	if(layer_index < 0) return NULL;

	layer = &data->layers[layer_index];

	if (layer->flag & CD_FLAG_NOFREE) {
		layer->data = MEM_dupallocN(layer->data);
		layer->flag &= ~CD_FLAG_NOFREE;
	}

	return layer->data;
}

void *CustomData_duplicate_referenced_layer_named(struct CustomData *data,
                                                  int type, char *name)
{
	CustomDataLayer *layer;
	int layer_index;

	/* get the layer index of the desired layer */
	layer_index = CustomData_get_named_layer_index(data, type, name);
	if(layer_index < 0) return NULL;

	layer = &data->layers[layer_index];

	if (layer->flag & CD_FLAG_NOFREE) {
		layer->data = MEM_dupallocN(layer->data);
		layer->flag &= ~CD_FLAG_NOFREE;
	}

	return layer->data;
}

void CustomData_free_temporary(CustomData *data, int totelem)
{
	CustomDataLayer *layer;
	int i, j;

	for(i = 0, j = 0; i < data->totlayer; ++i) {
		layer = &data->layers[i];

		if (i != j)
			data->layers[j] = data->layers[i];

		if ((layer->flag & CD_FLAG_TEMPORARY) == CD_FLAG_TEMPORARY)
			customData_free_layer__internal(layer, totelem);
		else
			j++;
	}

	data->totlayer = j;

	if(data->totlayer <= data->maxlayer-CUSTOMDATA_GROW)
		customData_resize(data, -CUSTOMDATA_GROW);

	customData_update_offsets(data);
}

void CustomData_set_only_copy(const struct CustomData *data,
                              CustomDataMask mask)
{
	int i;

	for(i = 0; i < data->totlayer; ++i)
		if(!((int)mask & (int)(1 << (int)data->layers[i].type)))
			data->layers[i].flag |= CD_FLAG_NOCOPY;
}

void CustomData_copy_elements(int type, void *source, void *dest, int count)
{
	const LayerTypeInfo *typeInfo = layerType_getInfo(type);

	if (typeInfo->copy)
		typeInfo->copy(source, dest, count);
	else
		memcpy(dest, source, typeInfo->size*count);
}

void CustomData_copy_data(const CustomData *source, CustomData *dest,
                          int source_index, int dest_index, int count)
{
	const LayerTypeInfo *typeInfo;
	int src_i, dest_i;
	int src_offset;
	int dest_offset;

	/* copies a layer at a time */
	dest_i = 0;
	for(src_i = 0; src_i < source->totlayer; ++src_i) {

		/* find the first dest layer with type >= the source type
		 * (this should work because layers are ordered by type)
		 */
		while(dest_i < dest->totlayer
		      && dest->layers[dest_i].type < source->layers[src_i].type)
			++dest_i;

		/* if there are no more dest layers, we're done */
		if(dest_i >= dest->totlayer) return;

		/* if we found a matching layer, copy the data */
		if(dest->layers[dest_i].type == source->layers[src_i].type) {
			char *src_data = source->layers[src_i].data;
			char *dest_data = dest->layers[dest_i].data;

			typeInfo = layerType_getInfo(source->layers[src_i].type);

			src_offset = source_index * typeInfo->size;
			dest_offset = dest_index * typeInfo->size;

			if(typeInfo->copy)
				typeInfo->copy(src_data + src_offset,
				                dest_data + dest_offset,
				                count);
			else
				memcpy(dest_data + dest_offset,
				       src_data + src_offset,
				       count * typeInfo->size);

			/* if there are multiple source & dest layers of the same type,
			 * we don't want to copy all source layers to the same dest, so
			 * increment dest_i
			 */
			++dest_i;
		}
	}
}

void CustomData_free_elem(CustomData *data, int index, int count)
{
	int i;
	const LayerTypeInfo *typeInfo;

	for(i = 0; i < data->totlayer; ++i) {
		if(!(data->layers[i].flag & CD_FLAG_NOFREE)) {
			typeInfo = layerType_getInfo(data->layers[i].type);

			if(typeInfo->free) {
				int offset = typeInfo->size * index;

				typeInfo->free((char *)data->layers[i].data + offset,
				               count, typeInfo->size);
			}
		}
	}
}

#define SOURCE_BUF_SIZE 100

void CustomData_interp(const CustomData *source, CustomData *dest,
                       int *src_indices, float *weights, float *sub_weights,
                       int count, int dest_index)
{
	int src_i, dest_i;
	int dest_offset;
	int j;
	void *source_buf[SOURCE_BUF_SIZE];
	void **sources = source_buf;

	/* slow fallback in case we're interpolating a ridiculous number of
	 * elements
	 */
	if(count > SOURCE_BUF_SIZE)
		sources = MEM_callocN(sizeof(*sources) * count,
		                      "CustomData_interp sources");

	/* interpolates a layer at a time */
	dest_i = 0;
	for(src_i = 0; src_i < source->totlayer; ++src_i) {
		const LayerTypeInfo *typeInfo= layerType_getInfo(source->layers[src_i].type);
		if(!typeInfo->interp) continue;

		/* find the first dest layer with type >= the source type
		 * (this should work because layers are ordered by type)
		 */
		while(dest_i < dest->totlayer
		      && dest->layers[dest_i].type < source->layers[src_i].type)
			++dest_i;

		/* if there are no more dest layers, we're done */
		if(dest_i >= dest->totlayer) return;

		/* if we found a matching layer, copy the data */
		if(dest->layers[dest_i].type == source->layers[src_i].type) {
			void *src_data = source->layers[src_i].data;

			for(j = 0; j < count; ++j)
				sources[j] = (char *)src_data
							 + typeInfo->size * src_indices[j];

			dest_offset = dest_index * typeInfo->size;

			typeInfo->interp(sources, weights, sub_weights, count,
						   (char *)dest->layers[dest_i].data + dest_offset);

			/* if there are multiple source & dest layers of the same type,
			 * we don't want to copy all source layers to the same dest, so
			 * increment dest_i
			 */
			++dest_i;
		}
	}

	if(count > SOURCE_BUF_SIZE) MEM_freeN(sources);
}

void CustomData_swap(struct CustomData *data, int index, int *corner_indices)
{
	const LayerTypeInfo *typeInfo;
	int i;

	for(i = 0; i < data->totlayer; ++i) {
		typeInfo = layerType_getInfo(data->layers[i].type);

		if(typeInfo->swap) {
			int offset = typeInfo->size * index;

			typeInfo->swap((char *)data->layers[i].data + offset, corner_indices);
		}
	}
}

void *CustomData_get(const CustomData *data, int index, int type)
{
	int offset;
	int layer_index;
	
	/* get the layer index of the active layer of type */
	layer_index = CustomData_get_active_layer_index(data, type);
	if(layer_index < 0) return NULL;

	/* get the offset of the desired element */
	offset = layerType_getInfo(type)->size * index;

	return (char *)data->layers[layer_index].data + offset;
}

void *CustomData_get_n(const CustomData *data, int type, int index, int n)
{
	int layer_index;
	int offset;

	/* get the layer index of the first layer of type */
	layer_index = data->typemap[type];
	if(layer_index < 0) return NULL;
	
	offset = layerType_getInfo(type)->size * index;
	return (char *)data->layers[layer_index+n].data + offset;
}

void *CustomData_get_layer(const CustomData *data, int type)
{
	/* get the layer index of the active layer of type */
	int layer_index = CustomData_get_active_layer_index(data, type);
	if(layer_index < 0) return NULL;

	return data->layers[layer_index].data;
}

void *CustomData_get_layer_n(const CustomData *data, int type, int n)
{
	/* get the layer index of the active layer of type */
	int layer_index = CustomData_get_layer_index(data, type);
	if(layer_index < 0) return NULL;

	return data->layers[layer_index+n].data;
}

void *CustomData_get_layer_named(const struct CustomData *data, int type,
                                 char *name)
{
	int layer_index = CustomData_get_named_layer_index(data, type, name);
	if(layer_index < 0) return NULL;

	return data->layers[layer_index].data;
}

void *CustomData_set_layer(const CustomData *data, int type, void *ptr)
{
	/* get the layer index of the first layer of type */
	int layer_index = CustomData_get_active_layer_index(data, type);

	if(layer_index < 0) return NULL;

	data->layers[layer_index].data = ptr;

	return ptr;
}

void *CustomData_set_layer_n(const struct CustomData *data, int type, int n, void *ptr)
{
	/* get the layer index of the first layer of type */
	int layer_index = CustomData_get_layer_index(data, type);
	if(layer_index < 0) return NULL;

	data->layers[layer_index+n].data = ptr;

	return ptr;
}

void CustomData_set(const CustomData *data, int index, int type, void *source)
{
	void *dest = CustomData_get(data, index, type);
	const LayerTypeInfo *typeInfo = layerType_getInfo(type);

	if(!dest) return;

	if(typeInfo->copy)
		typeInfo->copy(source, dest, 1);
	else
		memcpy(dest, source, typeInfo->size);
}

/* EditMesh functions */

void CustomData_em_free_block(CustomData *data, void **block)
{
    const LayerTypeInfo *typeInfo;
    int i;

	if(!*block) return;

    for(i = 0; i < data->totlayer; ++i) {
        if(!(data->layers[i].flag & CD_FLAG_NOFREE)) {
            typeInfo = layerType_getInfo(data->layers[i].type);

            if(typeInfo->free) {
				int offset = data->layers[i].offset;
                typeInfo->free((char*)*block + offset, 1, typeInfo->size);
			}
        }
    }

	MEM_freeN(*block);
	*block = NULL;
}

static void CustomData_em_alloc_block(CustomData *data, void **block)
{
	/* TODO: optimize free/alloc */

	if (*block)
		CustomData_em_free_block(data, block);

	if (data->totsize > 0)
		*block = MEM_callocN(data->totsize, "CustomData EM block");
	else
		*block = NULL;
}

void CustomData_em_copy_data(const CustomData *source, CustomData *dest,
                            void *src_block, void **dest_block)
{
	const LayerTypeInfo *typeInfo;
	int dest_i, src_i;

	if (!*dest_block)
		CustomData_em_alloc_block(dest, dest_block);
	
	/* copies a layer at a time */
	dest_i = 0;
	for(src_i = 0; src_i < source->totlayer; ++src_i) {

		/* find the first dest layer with type >= the source type
		 * (this should work because layers are ordered by type)
		 */
		while(dest_i < dest->totlayer
		      && dest->layers[dest_i].type < source->layers[src_i].type)
			++dest_i;

		/* if there are no more dest layers, we're done */
		if(dest_i >= dest->totlayer) return;

		/* if we found a matching layer, copy the data */
		if(dest->layers[dest_i].type == source->layers[src_i].type &&
			strcmp(dest->layers[dest_i].name, source->layers[src_i].name) == 0) {
			char *src_data = (char*)src_block + source->layers[src_i].offset;
			char *dest_data = (char*)*dest_block + dest->layers[dest_i].offset;

			typeInfo = layerType_getInfo(source->layers[src_i].type);

			if(typeInfo->copy)
				typeInfo->copy(src_data, dest_data, 1);
			else
				memcpy(dest_data, src_data, typeInfo->size);

			/* if there are multiple source & dest layers of the same type,
			 * we don't want to copy all source layers to the same dest, so
			 * increment dest_i
			 */
			++dest_i;
		}
	}
}

void *CustomData_em_get(const CustomData *data, void *block, int type)
{
	int layer_index;
	
	/* get the layer index of the first layer of type */
	layer_index = CustomData_get_active_layer_index(data, type);
	if(layer_index < 0) return NULL;

	return (char *)block + data->layers[layer_index].offset;
}

void *CustomData_em_get_n(const CustomData *data, void *block, int type, int n)
{
	int layer_index;
	
	/* get the layer index of the first layer of type */
	layer_index = CustomData_get_layer_index(data, type);
	if(layer_index < 0) return NULL;

	return (char *)block + data->layers[layer_index+n].offset;
}

void CustomData_em_set(CustomData *data, void *block, int type, void *source)
{
	void *dest = CustomData_em_get(data, block, type);
	const LayerTypeInfo *typeInfo = layerType_getInfo(type);

	if(!dest) return;

	if(typeInfo->copy)
		typeInfo->copy(source, dest, 1);
	else
		memcpy(dest, source, typeInfo->size);
}

void CustomData_em_set_n(CustomData *data, void *block, int type, int n, void *source)
{
	void *dest = CustomData_em_get_n(data, block, type, n);
	const LayerTypeInfo *typeInfo = layerType_getInfo(type);

	if(!dest) return;

	if(typeInfo->copy)
		typeInfo->copy(source, dest, 1);
	else
		memcpy(dest, source, typeInfo->size);
}

void CustomData_em_interp(CustomData *data, void **src_blocks, float *weights,
                          float *sub_weights, int count, void *dest_block)
{
	int i, j;
	void *source_buf[SOURCE_BUF_SIZE];
	void **sources = source_buf;

	/* slow fallback in case we're interpolating a ridiculous number of
	 * elements
	 */
	if(count > SOURCE_BUF_SIZE)
		sources = MEM_callocN(sizeof(*sources) * count,
		                      "CustomData_interp sources");

	/* interpolates a layer at a time */
	for(i = 0; i < data->totlayer; ++i) {
		CustomDataLayer *layer = &data->layers[i];
		const LayerTypeInfo *typeInfo = layerType_getInfo(layer->type);

		if(typeInfo->interp) {
			for(j = 0; j < count; ++j)
				sources[j] = (char *)src_blocks[j] + layer->offset;

			typeInfo->interp(sources, weights, sub_weights, count,
			                  (char *)dest_block + layer->offset);
		}
	}

	if(count > SOURCE_BUF_SIZE) MEM_freeN(sources);
}

void CustomData_em_set_default(CustomData *data, void **block)
{
	const LayerTypeInfo *typeInfo;
	int i;

	if (!*block)
		CustomData_em_alloc_block(data, block);

	for(i = 0; i < data->totlayer; ++i) {
		int offset = data->layers[i].offset;

		typeInfo = layerType_getInfo(data->layers[i].type);

		if(typeInfo->set_default)
			typeInfo->set_default((char*)*block + offset, 1);
	}
}

void CustomData_to_em_block(const CustomData *source, CustomData *dest,
                            int src_index, void **dest_block)
{
	const LayerTypeInfo *typeInfo;
	int dest_i, src_i, src_offset;

	if (!*dest_block)
		CustomData_em_alloc_block(dest, dest_block);
	
	/* copies a layer at a time */
	dest_i = 0;
	for(src_i = 0; src_i < source->totlayer; ++src_i) {

		/* find the first dest layer with type >= the source type
		 * (this should work because layers are ordered by type)
		 */
		while(dest_i < dest->totlayer
		      && dest->layers[dest_i].type < source->layers[src_i].type)
			++dest_i;

		/* if there are no more dest layers, we're done */
		if(dest_i >= dest->totlayer) return;

		/* if we found a matching layer, copy the data */
		if(dest->layers[dest_i].type == source->layers[src_i].type) {
			int offset = dest->layers[dest_i].offset;
			char *src_data = source->layers[src_i].data;
			char *dest_data = (char*)*dest_block + offset;

			typeInfo = layerType_getInfo(dest->layers[dest_i].type);
			src_offset = src_index * typeInfo->size;

			if(typeInfo->copy)
				typeInfo->copy(src_data + src_offset, dest_data, 1);
			else
				memcpy(dest_data, src_data + src_offset, typeInfo->size);

			/* if there are multiple source & dest layers of the same type,
			 * we don't want to copy all source layers to the same dest, so
			 * increment dest_i
			 */
			++dest_i;
		}
	}
}

void CustomData_from_em_block(const CustomData *source, CustomData *dest,
                              void *src_block, int dest_index)
{
	const LayerTypeInfo *typeInfo;
	int dest_i, src_i, dest_offset;

	/* copies a layer at a time */
	dest_i = 0;
	for(src_i = 0; src_i < source->totlayer; ++src_i) {

		/* find the first dest layer with type >= the source type
		 * (this should work because layers are ordered by type)
		 */
		while(dest_i < dest->totlayer
		      && dest->layers[dest_i].type < source->layers[src_i].type)
			++dest_i;

		/* if there are no more dest layers, we're done */
		if(dest_i >= dest->totlayer) return;

		/* if we found a matching layer, copy the data */
		if(dest->layers[dest_i].type == source->layers[src_i].type) {
			int offset = source->layers[src_i].offset;
			char *src_data = (char*)src_block + offset;
			char *dest_data = dest->layers[dest_i].data;

			typeInfo = layerType_getInfo(dest->layers[dest_i].type);
			dest_offset = dest_index * typeInfo->size;

			if(typeInfo->copy)
				typeInfo->copy(src_data, dest_data + dest_offset, 1);
			else
				memcpy(dest_data + dest_offset, src_data, typeInfo->size);

			/* if there are multiple source & dest layers of the same type,
			 * we don't want to copy all source layers to the same dest, so
			 * increment dest_i
			 */
			++dest_i;
		}
	}

}

/*Bmesh functions*/
/*needed to convert to/from different face reps*/
void CustomData_to_bmeshpoly(CustomData *fdata, CustomData *pdata, CustomData *ldata,
			     int totloop, int totpoly)
{
	int i;
	for(i=0; i < fdata->totlayer; i++){
		if(fdata->layers[i].type == CD_MTFACE){
			CustomData_add_layer(pdata, CD_MTEXPOLY, CD_CALLOC, &(fdata->layers[i].name), totpoly);
			CustomData_add_layer(ldata, CD_MLOOPUV, CD_CALLOC, &(fdata->layers[i].name), totloop);
		}
		else if(fdata->layers[i].type == CD_MCOL)
			CustomData_add_layer(ldata, CD_MLOOPCOL, CD_CALLOC, &(fdata->layers[i].name), totloop);
	}
}
void CustomData_from_bmeshpoly(CustomData *fdata, CustomData *pdata, CustomData *ldata, int total){
	int i;
	for(i=0; i < pdata->totlayer; i++){
		if(pdata->layers[i].type == CD_MTEXPOLY)
			CustomData_add_layer(fdata, CD_MTFACE, CD_CALLOC, &(pdata->layers[i].name), total);
	}
	for(i=0; i < ldata->totlayer; i++){
		if(ldata->layers[i].type == CD_MLOOPCOL)
			CustomData_add_layer(fdata, CD_MCOL, CD_CALLOC, &(ldata->layers[i].name), total);
		if (ldata->layers[i].type == CD_WEIGHT_MLOOPCOL)
			CustomData_add_layer(fdata, CD_WEIGHT_MCOL, CD_CALLOC, &(ldata->layers[i].name), total);
	}
}


void CustomData_bmesh_init_pool(CustomData *data, int allocsize){
	if(data->totlayer)data->pool = BLI_mempool_create(data->totsize, allocsize, allocsize);
}

void CustomData_bmesh_merge(CustomData *source, CustomData *dest, 
                            int mask, int alloctype, BMesh *bm, int type)
{
	BMHeader *h;
	BMIter iter;
	CustomData destold = *dest;
	void *tmp;
	int t;
	
	CustomData_merge(source, dest, mask, alloctype, 0);
	CustomData_bmesh_init_pool(dest, 512);

	switch (type) {
		case BM_VERT:
			t = BM_VERTS_OF_MESH; break;
		case BM_EDGE:
			t = BM_EDGES_OF_MESH; break;
		case BM_LOOP:
			t = BM_LOOPS_OF_FACE; break;
		case BM_FACE:
			t = BM_FACES_OF_MESH; break;
	}

	if (t != BM_LOOPS_OF_FACE) {
		/*ensure all current elements follow new customdata layout*/
		BM_ITER(h, &iter, bm, t, NULL) {
			CustomData_bmesh_copy_data(&destold, dest, h->data, &tmp);
			CustomData_bmesh_free_block(&destold, &h->data);
			h->data = tmp;
		}
	} else {
		BMFace *f;
		BMLoop *l;
		BMIter liter;

		/*ensure all current elements follow new customdata layout*/
		BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
			BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, f) {
				CustomData_bmesh_copy_data(&destold, dest, l->head.data, &tmp);
				CustomData_bmesh_free_block(&destold, &l->head.data);
				l->head.data = tmp;
			}
		}
	}

	if (destold.pool) BLI_mempool_destroy(destold.pool);
}

void CustomData_bmesh_free_block(CustomData *data, void **block)
{
    const LayerTypeInfo *typeInfo;
    int i;

	if(!*block) return;
    for(i = 0; i < data->totlayer; ++i) {
        if(!(data->layers[i].flag & CD_FLAG_NOFREE)) {
            typeInfo = layerType_getInfo(data->layers[i].type);

            if(typeInfo->free) {
				int offset = data->layers[i].offset;
				typeInfo->free((char*)*block + offset, 1, typeInfo->size);
			}
        }
    }

	BLI_mempool_free(data->pool, *block);
	*block = NULL;
}

static void CustomData_bmesh_alloc_block(CustomData *data, void **block)
{

	if (*block)
		CustomData_bmesh_free_block(data, block);

	if (data->totsize > 0)
		*block = BLI_mempool_calloc(data->pool);
	else
		*block = NULL;
}

void CustomData_bmesh_copy_data(const CustomData *source, CustomData *dest,
                            void *src_block, void **dest_block)
{
	const LayerTypeInfo *typeInfo;
	int dest_i, src_i;

	if (!*dest_block)
		CustomData_bmesh_alloc_block(dest, dest_block);
	
	/* copies a layer at a time */
	dest_i = 0;
	for(src_i = 0; src_i < source->totlayer; ++src_i) {

		/* find the first dest layer with type >= the source type
		 * (this should work because layers are ordered by type)
		 */
		while(dest_i < dest->totlayer
		      && dest->layers[dest_i].type < source->layers[src_i].type)
			++dest_i;

		/* if there are no more dest layers, we're done */
		if(dest_i >= dest->totlayer) return;

		/* if we found a matching layer, copy the data */
		if(dest->layers[dest_i].type == source->layers[src_i].type &&
			strcmp(dest->layers[dest_i].name, source->layers[src_i].name) == 0) {
			char *src_data = (char*)src_block + source->layers[src_i].offset;
			char *dest_data = (char*)*dest_block + dest->layers[dest_i].offset;

			typeInfo = layerType_getInfo(source->layers[src_i].type);

			if(typeInfo->copy)
				typeInfo->copy(src_data, dest_data, 1);
			else
				memcpy(dest_data, src_data, typeInfo->size);

			/* if there are multiple source & dest layers of the same type,
			 * we don't want to copy all source layers to the same dest, so
			 * increment dest_i
			 */
			++dest_i;
		}
	}
}

/*Bmesh Custom Data Functions. Should replace editmesh ones with these as well, due to more effecient memory alloc*/
void *CustomData_bmesh_get(const CustomData *data, void *block, int type)
{
	int layer_index;
	
	/* get the layer index of the first layer of type */
	layer_index = CustomData_get_active_layer_index(data, type);
	if(layer_index < 0) return NULL;

	return (char *)block + data->layers[layer_index].offset;
}

void *CustomData_bmesh_get_n(const CustomData *data, void *block, int type, int n)
{
	int layer_index;
	
	/* get the layer index of the first layer of type */
	layer_index = CustomData_get_layer_index(data, type);
	if(layer_index < 0) return NULL;

	return (char *)block + data->layers[layer_index+n].offset;
}

/*gets from the layer at physical index n, note: doesn't check type.*/
void *CustomData_bmesh_get_layer_n(const CustomData *data, void *block, int n)
{
	if(n < 0 || n >= data->totlayer) return NULL;

	return (char *)block + data->layers[n].offset;
}

int CustomData_layer_has_math(struct CustomData *data, int layern)
{
	const LayerTypeInfo *typeInfo = layerType_getInfo(data->layers[layern].type);
	
	if (typeInfo->equal && typeInfo->add && typeInfo->multiply && 
	    typeInfo->initminmax && typeInfo->dominmax) return 1;
	
	return 0;
}

/*copies the "value" (e.g. mloopuv uv or mloopcol colors) from one block to
  another, while not overwriting anything else (e.g. flags)*/
void CustomData_data_copy_value(int type, void *source, void *dest)
{
	const LayerTypeInfo *typeInfo = layerType_getInfo(type);

	if(!dest) return;

	if(typeInfo->copyvalue)
		typeInfo->copyvalue(source, dest);
	else
		memcpy(dest, source, typeInfo->size);
}

int CustomData_data_equals(int type, void *data1, void *data2)
{
	const LayerTypeInfo *typeInfo = layerType_getInfo(type);

	if (typeInfo->equal)
		return typeInfo->equal(data1, data2);
	else return !memcmp(data1, data2, typeInfo->size);
}

void CustomData_data_initminmax(int type, void *min, void *max)
{
	const LayerTypeInfo *typeInfo = layerType_getInfo(type);

	if (typeInfo->initminmax)
		typeInfo->initminmax(min, max);
}


void CustomData_data_dominmax(int type, void *data, void *min, void *max)
{
	const LayerTypeInfo *typeInfo = layerType_getInfo(type);

	if (typeInfo->dominmax)
		typeInfo->dominmax(data, min, max);
}


void CustomData_data_multiply(int type, void *data, float fac)
{
	const LayerTypeInfo *typeInfo = layerType_getInfo(type);

	if (typeInfo->multiply)
		typeInfo->multiply(data, fac);
}


void CustomData_data_add(int type, void *data1, void *data2)
{
	const LayerTypeInfo *typeInfo = layerType_getInfo(type);

	if (typeInfo->add)
		typeInfo->add(data1, data2);
}

void CustomData_bmesh_set(const CustomData *data, void *block, int type, void *source)
{
	void *dest = CustomData_bmesh_get(data, block, type);
	const LayerTypeInfo *typeInfo = layerType_getInfo(type);

	if(!dest) return;

	if(typeInfo->copy)
		typeInfo->copy(source, dest, 1);
	else
		memcpy(dest, source, typeInfo->size);
}

void CustomData_bmesh_set_n(CustomData *data, void *block, int type, int n, void *source)
{
	void *dest = CustomData_bmesh_get_n(data, block, type, n);
	const LayerTypeInfo *typeInfo = layerType_getInfo(type);

	if(!dest) return;

	if(typeInfo->copy)
		typeInfo->copy(source, dest, 1);
	else
		memcpy(dest, source, typeInfo->size);
}

void CustomData_bmesh_set_layer_n(CustomData *data, void *block, int n, void *source)
{
	void *dest = CustomData_bmesh_get_layer_n(data, block, n);
	const LayerTypeInfo *typeInfo = layerType_getInfo(data->layers[n].type);

	if(!dest) return;

	if(typeInfo->copy)
		typeInfo->copy(source, dest, 1);
	else
		memcpy(dest, source, typeInfo->size);
}

void CustomData_bmesh_interp(CustomData *data, void **src_blocks, float *weights,
                          float *sub_weights, int count, void *dest_block)
{
	int i, j;
	void *source_buf[SOURCE_BUF_SIZE];
	void **sources = source_buf;

	/* slow fallback in case we're interpolating a ridiculous number of
	 * elements
	 */
	if(count > SOURCE_BUF_SIZE)
		sources = MEM_callocN(sizeof(*sources) * count,
		                      "CustomData_interp sources");

	/* interpolates a layer at a time */
	for(i = 0; i < data->totlayer; ++i) {
		CustomDataLayer *layer = &data->layers[i];
		const LayerTypeInfo *typeInfo = layerType_getInfo(layer->type);
		if(typeInfo->interp) {
			for(j = 0; j < count; ++j)
				sources[j] = (char *)src_blocks[j] + layer->offset;

			typeInfo->interp(sources, weights, sub_weights, count,
			                  (char *)dest_block + layer->offset);
		}
	}

	if(count > SOURCE_BUF_SIZE) MEM_freeN(sources);
}

void CustomData_bmesh_set_default(CustomData *data, void **block)
{
	const LayerTypeInfo *typeInfo;
	int i;

	if (!*block)
		CustomData_bmesh_alloc_block(data, block);

	for(i = 0; i < data->totlayer; ++i) {
		int offset = data->layers[i].offset;

		typeInfo = layerType_getInfo(data->layers[i].type);

		if(typeInfo->set_default)
			typeInfo->set_default((char*)*block + offset, 1);
	}
}

void CustomData_to_bmesh_block(const CustomData *source, CustomData *dest,
                            int src_index, void **dest_block)
{
	const LayerTypeInfo *typeInfo;
	int dest_i, src_i, src_offset;

	if (!*dest_block)
		CustomData_bmesh_alloc_block(dest, dest_block);
	
	/* copies a layer at a time */
	dest_i = 0;
	for(src_i = 0; src_i < source->totlayer; ++src_i) {

		/* find the first dest layer with type >= the source type
		 * (this should work because layers are ordered by type)
		 */
		while(dest_i < dest->totlayer
		      && dest->layers[dest_i].type < source->layers[src_i].type)
			++dest_i;

		/* if there are no more dest layers, we're done */
		if(dest_i >= dest->totlayer) return;

		/* if we found a matching layer, copy the data */
		if(dest->layers[dest_i].type == source->layers[src_i].type) {
			int offset = dest->layers[dest_i].offset;
			char *src_data = source->layers[src_i].data;
			char *dest_data = (char*)*dest_block + offset;

			typeInfo = layerType_getInfo(dest->layers[dest_i].type);
			src_offset = src_index * typeInfo->size;

			if(typeInfo->copy)
				typeInfo->copy(src_data + src_offset, dest_data, 1);
			else
				memcpy(dest_data, src_data + src_offset, typeInfo->size);

			/* if there are multiple source & dest layers of the same type,
			 * we don't want to copy all source layers to the same dest, so
			 * increment dest_i
			 */
			++dest_i;
		}
	}
}

void CustomData_from_bmesh_block(const CustomData *source, CustomData *dest,
                              void *src_block, int dest_index)
{
	const LayerTypeInfo *typeInfo;
	int dest_i, src_i, dest_offset;

	/* copies a layer at a time */
	dest_i = 0;
	for(src_i = 0; src_i < source->totlayer; ++src_i) {

		/* find the first dest layer with type >= the source type
		 * (this should work because layers are ordered by type)
		 */
		while(dest_i < dest->totlayer
		      && dest->layers[dest_i].type < source->layers[src_i].type)
			++dest_i;

		/* if there are no more dest layers, we're done */
		if(dest_i >= dest->totlayer) return;

		/* if we found a matching layer, copy the data */
		if(dest->layers[dest_i].type == source->layers[src_i].type) {
			int offset = source->layers[src_i].offset;
			char *src_data = (char*)src_block + offset;
			char *dest_data = dest->layers[dest_i].data;

			typeInfo = layerType_getInfo(dest->layers[dest_i].type);
			dest_offset = dest_index * typeInfo->size;

			if(typeInfo->copy)
				typeInfo->copy(src_data, dest_data + dest_offset, 1);
			else
				memcpy(dest_data + dest_offset, src_data, typeInfo->size);

			/* if there are multiple source & dest layers of the same type,
			 * we don't want to copy all source layers to the same dest, so
			 * increment dest_i
			 */
			++dest_i;
		}
	}

}

void CustomData_file_write_info(int type, char **structname, int *structnum)
{
	const LayerTypeInfo *typeInfo = layerType_getInfo(type);

	*structname = typeInfo->structname;
	*structnum = typeInfo->structnum;
}

int CustomData_sizeof(int type)
{
	const LayerTypeInfo *typeInfo = layerType_getInfo(type);

	return typeInfo->size;
}

const char *CustomData_layertype_name(int type)
{
	return layerType_getName(type);
}

static int  CustomData_is_property_layer(int type)
{
	if((type == CD_PROP_FLT) || (type == CD_PROP_INT) || (type == CD_PROP_STR))
		return 1;
	return 0;
}

void CustomData_set_layer_unique_name(CustomData *data, int index)
{
	char tempname[64];
	int number, i, type;
	char *dot, *name;
	CustomDataLayer *layer, *nlayer= &data->layers[index];
	const LayerTypeInfo *typeInfo= layerType_getInfo(nlayer->type);

	if (!typeInfo->defaultname)
		return;

	type = nlayer->type;
	name = nlayer->name;

	if (name[0] == '\0')
		BLI_strncpy(nlayer->name, typeInfo->defaultname, sizeof(nlayer->name));
	
	/* see if there is a duplicate */
	for(i=0; i<data->totlayer; i++) {
		layer = &data->layers[i];
		
		if(CustomData_is_property_layer(type)){
			if(i!=index && CustomData_is_property_layer(layer->type) && 
				strcmp(layer->name, name)==0)
					break;	
		
		}
		else{
			if(i!=index && layer->type==type && strcmp(layer->name, name)==0)
				break;
		}
	}

	if(i == data->totlayer)
		return;

	/* strip off the suffix */
	dot = strchr(nlayer->name, '.');
	if(dot) *dot=0;
	
	for(number=1; number <=999; number++) {
		sprintf(tempname, "%s.%03d", nlayer->name, number);

		for(i=0; i<data->totlayer; i++) {
			layer = &data->layers[i];
			
			if(CustomData_is_property_layer(type)){
				if(i!=index && CustomData_is_property_layer(layer->type) && 
					strcmp(layer->name, tempname)==0)

				break;
			}
			else{
				if(i!=index && layer->type==type && strcmp(layer->name, tempname)==0)
					break;
			}
		}

		if(i == data->totlayer) {
			BLI_strncpy(nlayer->name, tempname, sizeof(nlayer->name));
			return;
		}
	}	
}

int CustomData_verify_versions(struct CustomData *data, int index)
{
	const LayerTypeInfo *typeInfo;
	CustomDataLayer *layer = &data->layers[index];
	int i, keeplayer = 1;

	if (layer->type >= CD_NUMTYPES) {
		keeplayer = 0; /* unknown layer type from future version */
	}
	else {
		typeInfo = layerType_getInfo(layer->type);

		if (!typeInfo->defaultname && (index > 0) &&
			data->layers[index-1].type == layer->type)
			keeplayer = 0; /* multiple layers of which we only support one */
	}

	if (!keeplayer) {
	    for (i=index+1; i < data->totlayer; ++i)
    	    data->layers[i-1] = data->layers[i];
		data->totlayer--;
	}

	return keeplayer;
}

