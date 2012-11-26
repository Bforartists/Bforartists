/*
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
 * Contributor(s): Joseph Eagar.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/bmesh/operators/bmo_subdivide.c
 *  \ingroup bmesh
 */

#include "MEM_guardedalloc.h"

#include "BLI_math.h"
#include "BLI_rand.h"
#include "BLI_array.h"
#include "BLI_noise.h"

#include "BKE_customdata.h"

#include "DNA_object_types.h"

#include "bmesh.h"
#include "intern/bmesh_private.h"

#include "intern/bmesh_operators_private.h" /* own include */

#include "bmo_subdivide.h" /* own include */

/* flags for all elements share a common bitfield space */
#define SUBD_SPLIT	1

#define EDGE_PERCENT	2

/* I don't think new faces are flagged, currently, but
 * better safe than sorry. */
#define FACE_CUSTOMFILL	4
#define ELE_INNER	8
#define ELE_SPLIT	16

/* see bug [#32665], 0.00005 means a we get face splits at a little under 1.0 degrees */
#define FLT_FACE_SPLIT_EPSILON 0.00005f

/*
 * NOTE: beauty has been renamed to flag!
 */

/* generic subdivision rules:
 *
 * - two selected edges in a face should make a link
 *   between them.
 *
 * - one edge should do, what? make pretty topology, or just
 *   split the edge only?
 */

/* connects face with smallest len, which I think should always be correct for
 * edge subdivision */
static BMEdge *connect_smallest_face(BMesh *bm, BMVert *v1, BMVert *v2, BMFace **r_nf)
{
	BMIter iter, iter2;
	BMVert *v;
	BMLoop *nl;
	BMFace *face, *curf = NULL;

	/* this isn't the best thing in the world.  it doesn't handle cases where there's
	 * multiple faces yet.  that might require a convexity test to figure out which
	 * face is "best" and who knows what for non-manifold conditions. */
	for (face = BM_iter_new(&iter, bm, BM_FACES_OF_VERT, v1); face; face = BM_iter_step(&iter)) {
		for (v = BM_iter_new(&iter2, bm, BM_VERTS_OF_FACE, face); v; v = BM_iter_step(&iter2)) {
			if (v == v2) {
				if (!curf || face->len < curf->len) curf = face;
			}
		}
	}

	if (curf) {
		face = BM_face_split(bm, curf, v1, v2, &nl, NULL, FALSE);
		
		if (r_nf) *r_nf = face;
		return nl ? nl->e : NULL;
	}

	return NULL;
}
/* calculates offset for co, based on fractal, sphere or smooth settings  */
static void alter_co(BMesh *bm, BMVert *v, BMEdge *UNUSED(origed), const SubDParams *params, float perc,
                     BMVert *vsta, BMVert *vend)
{
	float tvec[3], prev_co[3], fac;
	float *co = NULL;
	int i, totlayer = CustomData_number_of_layers(&bm->vdata, CD_SHAPEKEY);
	
	BM_vert_normal_update_all(v);

	co = CustomData_bmesh_get_n(&bm->vdata, v->head.data, CD_SHAPEKEY, params->origkey);
	copy_v3_v3(co, v->co);
	copy_v3_v3(prev_co, co);

	if (UNLIKELY(params->use_sphere)) { /* subdivide sphere */
		normalize_v3(co);
		mul_v3_fl(co, params->smooth);
	}
	else if (params->use_smooth) {
		/* we calculate an offset vector vec1[], to be added to *co */
		float len, nor[3], nor1[3], nor2[3], smooth = params->smooth;

		sub_v3_v3v3(nor, vsta->co, vend->co);
		len = 0.5f * normalize_v3(nor);

		copy_v3_v3(nor1, vsta->no);
		copy_v3_v3(nor2, vend->no);

		/* cosine angle */
		fac = dot_v3v3(nor, nor1);
		mul_v3_v3fl(tvec, nor1, fac);

		/* cosine angle */
		fac = -dot_v3v3(nor, nor2);
		madd_v3_v3fl(tvec, nor2, fac);

		/* falloff for multi subdivide */
		smooth *= sqrtf(fabsf(1.0f - 2.0f * fabsf(0.5f - perc)));

		mul_v3_fl(tvec, smooth * len);

		add_v3_v3(co, tvec);
	}

	if (params->use_fractal) {
		float len = len_v3v3(vsta->co, vend->co);
		float normal[3] = {0.0f, 0.0f, 0.0f}, co2[3], base1[3], base2[3];

		fac = params->fractal * len;

		mid_v3_v3v3(normal, vsta->no, vend->no);
		ortho_basis_v3v3_v3(base1, base2, normal);

		add_v3_v3v3(co2, v->co, params->off);
		mul_v3_fl(co2, 10.0f);

		tvec[0] = fac * (BLI_gTurbulence(1.0, co2[0], co2[1], co2[2], 15, 0, 2) - 0.5f);
		tvec[1] = fac * (BLI_gTurbulence(1.0, co2[1], co2[0], co2[2], 15, 0, 2) - 0.5f);
		tvec[2] = fac * (BLI_gTurbulence(1.0, co2[1], co2[2], co2[0], 15, 0, 2) - 0.5f);

		/* add displacement */
		madd_v3_v3fl(co, normal, tvec[0]);
		madd_v3_v3fl(co, base1, tvec[1] * (1.0f - params->along_normal));
		madd_v3_v3fl(co, base2, tvec[2] * (1.0f - params->along_normal));
	}

	/* apply the new difference to the rest of the shape keys,
	 * note that this dosn't take rotations into account, we _could_ support
	 * this by getting the normals and coords for each shape key and
	 * re-calculate the smooth value for each but this is quite involved.
	 * for now its ok to simply apply the difference IMHO - campbell */
	sub_v3_v3v3(tvec, prev_co, co);

	for (i = 0; i < totlayer; i++) {
		if (params->origkey != i) {
			co = CustomData_bmesh_get_n(&bm->vdata, v->head.data, CD_SHAPEKEY, i);
			sub_v3_v3(co, tvec);
		}
	}

}

/* assumes in the edge is the correct interpolated vertices already */
/* percent defines the interpolation, rad and flag are for special options */
/* results in new vertex with correct coordinate, vertex normal and weight group info */
static BMVert *bm_subdivide_edge_addvert(BMesh *bm, BMEdge *edge, BMEdge *oedge,
                                         const SubDParams *params, float percent,
                                         float percent2,
                                         BMEdge **out, BMVert *vsta, BMVert *vend)
{
	BMVert *ev;
	
	ev = BM_edge_split(bm, edge, edge->v1, out, percent);

	BMO_elem_flag_enable(bm, ev, ELE_INNER);

	/* offset for smooth or sphere or fractal */
	alter_co(bm, ev, oedge, params, percent2, vsta, vend);

#if 0 //BMESH_TODO
	/* clip if needed by mirror modifier */
	if (edge->v1->f2) {
		if (edge->v1->f2 & edge->v2->f2 & 1) {
			co[0] = 0.0f;
		}
		if (edge->v1->f2 & edge->v2->f2 & 2) {
			co[1] = 0.0f;
		}
		if (edge->v1->f2 & edge->v2->f2 & 4) {
			co[2] = 0.0f;
		}
	}
#endif
	
	interp_v3_v3v3(ev->no, vsta->no, vend->no, percent2);
	normalize_v3(ev->no);

	return ev;
}

static BMVert *subdivideedgenum(BMesh *bm, BMEdge *edge, BMEdge *oedge,
                                int curpoint, int totpoint, const SubDParams *params,
                                BMEdge **newe, BMVert *vsta, BMVert *vend)
{
	BMVert *ev;
	float percent, percent2 = 0.0f;

	if (BMO_elem_flag_test(bm, edge, EDGE_PERCENT) && totpoint == 1) {
		percent = BMO_slot_map_float_get(params->slot_edgepercents, edge);
	}
	else {
		percent = 1.0f / (float)(totpoint + 1 - curpoint);
		percent2 = (float)(curpoint + 1) / (float)(totpoint + 1);

	}
	
	ev = bm_subdivide_edge_addvert(bm, edge, oedge, params, percent,
	                               percent2, newe, vsta, vend);
	return ev;
}

static void bm_subdivide_multicut(BMesh *bm, BMEdge *edge, const SubDParams *params,
                                  BMVert *vsta, BMVert *vend)
{
	BMEdge *eed = edge, *newe, temp = *edge;
	BMVert *v, ov1 = *edge->v1, ov2 = *edge->v2, *v1 = edge->v1, *v2 = edge->v2;
	int i, numcuts = params->numcuts;

	temp.v1 = &ov1;
	temp.v2 = &ov2;
	
	for (i = 0; i < numcuts; i++) {
		v = subdivideedgenum(bm, eed, &temp, i, params->numcuts, params, &newe, vsta, vend);

		BMO_elem_flag_enable(bm, v, SUBD_SPLIT);
		BMO_elem_flag_enable(bm, eed, SUBD_SPLIT);
		BMO_elem_flag_enable(bm, newe, SUBD_SPLIT);

		BMO_elem_flag_enable(bm, v, ELE_SPLIT);
		BMO_elem_flag_enable(bm, eed, ELE_SPLIT);
		BMO_elem_flag_enable(bm, newe, SUBD_SPLIT);

		BM_CHECK_ELEMENT(v);
		if (v->e) BM_CHECK_ELEMENT(v->e);
		if (v->e && v->e->l) BM_CHECK_ELEMENT(v->e->l->f);
	}
	
	alter_co(bm, v1, &temp, params, 0, &ov1, &ov2);
	alter_co(bm, v2, &temp, params, 1.0, &ov1, &ov2);
}

/* note: the patterns are rotated as necessary to
 * match the input geometry.  they're based on the
 * pre-split state of the  face */

/**
 * <pre>
 *  v3---------v2
 *  |          |
 *  |          |
 *  |          |
 *  |          |
 *  v4---v0---v1
 * </pre>
 */
static void quad_1edge_split(BMesh *bm, BMFace *UNUSED(face),
                             BMVert **verts, const SubDParams *params)
{
	BMFace *nf;
	int i, add, numcuts = params->numcuts;

	/* if it's odd, the middle face is a quad, otherwise it's a triangle */
	if ((numcuts % 2) == 0) {
		add = 2;
		for (i = 0; i < numcuts; i++) {
			if (i == numcuts / 2) {
				add -= 1;
			}
			connect_smallest_face(bm, verts[i], verts[numcuts + add], &nf);
		}
	}
	else {
		add = 2;
		for (i = 0; i < numcuts; i++) {
			connect_smallest_face(bm, verts[i], verts[numcuts + add], &nf);
			if (i == numcuts / 2) {
				add -= 1;
				connect_smallest_face(bm, verts[i], verts[numcuts + add], &nf);
			}
		}

	}
}

static const SubDPattern quad_1edge = {
	{1, 0, 0, 0},
	quad_1edge_split,
	4,
};


/**
 * <pre>
 *  v6--------v5
 *  |          |
 *  |          |v4s
 *  |          |v3s
 *  |   s  s   |
 *  v7-v0--v1-v2
 * </pre>
 */
static void quad_2edge_split_path(BMesh *bm, BMFace *UNUSED(face), BMVert **verts,
                                  const SubDParams *params)
{
	BMFace *nf;
	int i, numcuts = params->numcuts;
	
	for (i = 0; i < numcuts; i++) {
		connect_smallest_face(bm, verts[i], verts[numcuts + (numcuts - i)], &nf);
	}
	connect_smallest_face(bm, verts[numcuts * 2 + 3], verts[numcuts * 2 + 1], &nf);
}

static const SubDPattern quad_2edge_path = {
	{1, 1, 0, 0},
	quad_2edge_split_path,
	4,
};

/**
 * <pre>
 *  v6--------v5
 *  |          |
 *  |          |v4s
 *  |          |v3s
 *  |   s  s   |
 *  v7-v0--v1-v2
 * </pre>
 */
static void quad_2edge_split_innervert(BMesh *bm, BMFace *UNUSED(face), BMVert **verts,
                                       const SubDParams *params)
{
	BMFace *nf;
	BMVert *v, *lastv;
	BMEdge *e, *ne, olde;
	int i, numcuts = params->numcuts;
	
	lastv = verts[numcuts];

	for (i = numcuts - 1; i >= 0; i--) {
		e = connect_smallest_face(bm, verts[i], verts[numcuts + (numcuts - i)], &nf);

		olde = *e;
		v = bm_subdivide_edge_addvert(bm, e, &olde, params, 0.5f, 0.5f, &ne, e->v1, e->v2);

		if (i != numcuts - 1) {
			connect_smallest_face(bm, lastv, v, &nf);
		}

		lastv = v;
	}

	connect_smallest_face(bm, lastv, verts[numcuts * 2 + 2], &nf);
}

static const SubDPattern quad_2edge_innervert = {
	{1, 1, 0, 0},
	quad_2edge_split_innervert,
	4,
};

/**
 * <pre>
 *  v6--------v5
 *  |          |
 *  |          |v4s
 *  |          |v3s
 *  |   s  s   |
 *  v7-v0--v1-v2
 * </pre>
 */
static void quad_2edge_split_fan(BMesh *bm, BMFace *UNUSED(face), BMVert **verts,
                                 const SubDParams *params)
{
	BMFace *nf;
	/* BMVert *v; */               /* UNUSED */
	/* BMVert *lastv = verts[2]; */ /* UNUSED */
	/* BMEdge *e, *ne; */          /* UNUSED */
	int i, numcuts = params->numcuts;

	for (i = 0; i < numcuts; i++) {
		connect_smallest_face(bm, verts[i], verts[numcuts * 2 + 2], &nf);
		connect_smallest_face(bm, verts[numcuts + (numcuts - i)], verts[numcuts * 2 + 2], &nf);
	}
}

static const SubDPattern quad_2edge_fan = {
	{1, 1, 0, 0},
	quad_2edge_split_fan,
	4,
};

/**
 * <pre>
 *      s   s
 *  v8--v7--v6-v5
 *  |          |
 *  |          v4 s
 *  |          |
 *  |          v3 s
 *  |   s  s   |
 *  v9-v0--v1-v2
 * </pre>
 */
static void quad_3edge_split(BMesh *bm, BMFace *UNUSED(face), BMVert **verts,
                             const SubDParams *params)
{
	BMFace *nf;
	int i, add = 0, numcuts = params->numcuts;
	
	for (i = 0; i < numcuts; i++) {
		if (i == numcuts / 2) {
			if (numcuts % 2 != 0) {
				connect_smallest_face(bm, verts[numcuts - i - 1 + add], verts[i + numcuts + 1], &nf);
			}
			add = numcuts * 2 + 2;
		}
		connect_smallest_face(bm, verts[numcuts - i - 1 + add], verts[i + numcuts + 1], &nf);
	}

	for (i = 0; i < numcuts / 2 + 1; i++) {
		connect_smallest_face(bm, verts[i], verts[(numcuts - i) + numcuts * 2 + 1], &nf);
	}
}

static const SubDPattern quad_3edge = {
	{1, 1, 1, 0},
	quad_3edge_split,
	4,
};

/**
 * <pre>
 *            v8--v7-v6--v5
 *            |     s    |
 *            |v9 s     s|v4
 * first line |          |   last line
 *            |v10s s   s|v3
 *            v11-v0--v1-v2
 *
 *            it goes from bottom up
 * </pre>
 */
static void quad_4edge_subdivide(BMesh *bm, BMFace *UNUSED(face), BMVert **verts,
                                 const SubDParams *params)
{
	BMFace *nf;
	BMVert *v, *v1, *v2;
	BMEdge *e, *ne, temp;
	BMVert **lines;
	int numcuts = params->numcuts;
	int i, j, a, b, s = numcuts + 2 /* , totv = numcuts * 4 + 4 */;

	lines = MEM_callocN(sizeof(BMVert *) * (numcuts + 2) * (numcuts + 2), "q_4edge_split");
	/* build a 2-dimensional array of verts,
	 * containing every vert (and all new ones)
	 * in the face */

	/* first line */
	for (i = 0; i < numcuts + 2; i++) {
		lines[i] = verts[numcuts * 3 + 2 + (numcuts - i + 1)];
	}

	/* last line */
	for (i = 0; i < numcuts + 2; i++) {
		lines[(s - 1) * s + i] = verts[numcuts + i];
	}
	
	/* first and last members of middle lines */
	for (i = 0; i < numcuts; i++) {
		a = i;
		b = numcuts + 1 + numcuts + 1 + (numcuts - i - 1);
		
		e = connect_smallest_face(bm, verts[a], verts[b], &nf);
		if (!e)
			continue;

		BMO_elem_flag_enable(bm, e, ELE_INNER);
		BMO_elem_flag_enable(bm, nf, ELE_INNER);

		
		v1 = lines[(i + 1) * s] = verts[a];
		v2 = lines[(i + 1) * s + s - 1] = verts[b];
		
		temp = *e;
		for (a = 0; a < numcuts; a++) {
			v = subdivideedgenum(bm, e, &temp, a, numcuts, params, &ne,
			                     v1, v2);

			BMESH_ASSERT(v != NULL);

			BMO_elem_flag_enable(bm, ne, ELE_INNER);
			lines[(i + 1) * s + a + 1] = v;
		}
	}

	for (i = 1; i < numcuts + 2; i++) {
		for (j = 1; j < numcuts + 1; j++) {
			a = i * s + j;
			b = (i - 1) * s + j;
			e = connect_smallest_face(bm, lines[a], lines[b], &nf);
			if (!e)
				continue;

			BMO_elem_flag_enable(bm, e, ELE_INNER);
			BMO_elem_flag_enable(bm, nf, ELE_INNER);
		}
	}

	MEM_freeN(lines);
}

/**
 * <pre>
 *        v3
 *       / \
 *      /   \
 *     /     \
 *    /       \
 *   /         \
 *  v4--v0--v1--v2
 *      s    s
 * </pre>
 */
static void tri_1edge_split(BMesh *bm, BMFace *UNUSED(face), BMVert **verts,
                            const SubDParams *params)
{
	BMFace *nf;
	int i, numcuts = params->numcuts;
	
	for (i = 0; i < numcuts; i++) {
		connect_smallest_face(bm, verts[i], verts[numcuts + 1], &nf);
	}
}

static const SubDPattern tri_1edge = {
	{1, 0, 0},
	tri_1edge_split,
	3,
};

/**
 * <pre>
 *         v5
 *        / \
 *   s v6/---\ v4 s
 *      / \ / \
 *  sv7/---v---\ v3 s
 *    /  \/  \/ \
 *   v8--v0--v1--v2
 *      s    s
 * </pre>
 */
static void tri_3edge_subdivide(BMesh *bm, BMFace *UNUSED(face), BMVert **verts,
                                const SubDParams *params)
{
	BMFace *nf;
	BMEdge *e, *ne, temp;
	BMVert ***lines, *v, ov1, ov2;
	void *stackarr[1];
	int i, j, a, b, numcuts = params->numcuts;
	
	/* number of verts in each lin */
	lines = MEM_callocN(sizeof(void *) * (numcuts + 2), "triangle vert table");
	
	lines[0] = (BMVert **) stackarr;
	lines[0][0] = verts[numcuts * 2 + 1];
	
	lines[numcuts + 1] = MEM_callocN(sizeof(void *) * (numcuts + 2), "triangle vert table 2");
	for (i = 0; i < numcuts; i++) {
		lines[numcuts + 1][i + 1] = verts[i];
	}
	lines[numcuts + 1][0] = verts[numcuts * 3 + 2];
	lines[numcuts + 1][numcuts + 1] = verts[numcuts];

	for (i = 0; i < numcuts; i++) {
		lines[i + 1] = MEM_callocN(sizeof(void *) * (2 + i), "triangle vert table row");
		a = numcuts * 2 + 2 + i;
		b = numcuts + numcuts - i;
		e = connect_smallest_face(bm, verts[a], verts[b], &nf);
		if (!e) goto cleanup;

		BMO_elem_flag_enable(bm, e, ELE_INNER);
		BMO_elem_flag_enable(bm, nf, ELE_INNER);

		lines[i + 1][0] = verts[a];
		lines[i + 1][i + 1] = verts[b];
		
		temp = *e;
		ov1 = *verts[a];
		ov2 = *verts[b];
		temp.v1 = &ov1;
		temp.v2 = &ov2;
		for (j = 0; j < i; j++) {
			v = subdivideedgenum(bm, e, &temp, j, i, params, &ne,
			                     verts[a], verts[b]);
			lines[i + 1][j + 1] = v;

			BMO_elem_flag_enable(bm, ne, ELE_INNER);
		}
	}
	
	/**
	 * <pre>
	 *         v5
	 *        / \
	 *   s v6/---\ v4 s
	 *      / \ / \
	 *  sv7/---v---\ v3 s
	 *    /  \/  \/ \
	 *   v8--v0--v1--v2
	 *      s    s
	 * </pre>
	 */
	for (i = 1; i < numcuts + 1; i++) {
		for (j = 0; j < i; j++) {
			e = connect_smallest_face(bm, lines[i][j], lines[i + 1][j + 1], &nf);

			BMO_elem_flag_enable(bm, e, ELE_INNER);
			BMO_elem_flag_enable(bm, nf, ELE_INNER);

			e = connect_smallest_face(bm, lines[i][j + 1], lines[i + 1][j + 1], &nf);

			BMO_elem_flag_enable(bm, e, ELE_INNER);
			BMO_elem_flag_enable(bm, nf, ELE_INNER);
		}
	}

cleanup:
	for (i = 1; i < numcuts + 2; i++) {
		if (lines[i]) MEM_freeN(lines[i]);
	}

	MEM_freeN(lines);
}

static const SubDPattern tri_3edge = {
	{1, 1, 1},
	tri_3edge_subdivide,
	3,
};


static const SubDPattern quad_4edge = {
	{1, 1, 1, 1},
	quad_4edge_subdivide,
	4,
};

static const SubDPattern *patterns[] = {
	NULL,  /* quad single edge pattern is inserted here */
	NULL,  /* quad corner vert pattern is inserted here */
	NULL,  /* tri single edge pattern is inserted here */
	NULL,
	&quad_3edge,
	NULL,
};

#define PATTERNS_TOT  (sizeof(patterns) / sizeof(void *))

typedef struct SubDFaceData {
	BMVert *start;
	const SubDPattern *pat;
	int totedgesel;  /* only used if pat was NULL, e.g. no pattern was found */
	BMFace *face;
} SubDFaceData;

void bmo_subdivide_edges_exec(BMesh *bm, BMOperator *op)
{
	BMOpSlot *einput;
	const SubDPattern *pat;
	SubDParams params;
	SubDFaceData *facedata = NULL;
	BLI_array_declare(facedata);
	BMIter viter, fiter, liter;
	BMVert *v, **verts = NULL;
	BMEdge *edge;
	BMEdge **edges = NULL;
	BLI_array_declare(edges);
	BMLoop *(*loops_split)[2] = NULL;
	BLI_array_declare(loops_split);
	BMLoop **loops = NULL;
	BLI_array_declare(loops);
	BMLoop *nl, *l;
	BMFace *face;
	BLI_array_declare(verts);
	float smooth, fractal, along_normal;
	int use_sphere, cornertype, use_singleedge, use_gridfill;
	int skey, seed, i, j, matched, a, b, numcuts, totesel;
	
	BMO_slot_buffer_flag_enable(bm, op->slots_in, "edges", BM_EDGE, SUBD_SPLIT);
	
	numcuts = BMO_slot_int_get(op->slots_in, "cuts");
	seed = BMO_slot_int_get(op->slots_in, "seed");
	smooth = BMO_slot_float_get(op->slots_in, "smooth");
	fractal = BMO_slot_float_get(op->slots_in, "fractal");
	along_normal = BMO_slot_float_get(op->slots_in, "along_normal");
	cornertype = BMO_slot_int_get(op->slots_in, "quad_corner_type");

	use_singleedge = BMO_slot_bool_get(op->slots_in, "use_singleedge");
	use_gridfill   = BMO_slot_bool_get(op->slots_in, "use_gridfill");
	use_sphere     = BMO_slot_bool_get(op->slots_in, "use_sphere");
	
	BLI_srandom(seed);
	
	patterns[1] = NULL;
	/* straight cut is patterns[1] == NULL */
	switch (cornertype) {
		case SUBD_PATH:
			patterns[1] = &quad_2edge_path;
			break;
		case SUBD_INNERVERT:
			patterns[1] = &quad_2edge_innervert;
			break;
		case SUBD_FAN:
			patterns[1] = &quad_2edge_fan;
			break;
	}
	
	if (use_singleedge) {
		patterns[0] = &quad_1edge;
		patterns[2] = &tri_1edge;
	}
	else {
		patterns[0] = NULL;
		patterns[2] = NULL;
	}

	if (use_gridfill) {
		patterns[3] = &quad_4edge;
		patterns[5] = &tri_3edge;
	}
	else {
		patterns[3] = NULL;
		patterns[5] = NULL;
	}
	
	/* add a temporary shapekey layer to store displacements on current geometry */
	BM_data_layer_add(bm, &bm->vdata, CD_SHAPEKEY);
	skey = CustomData_number_of_layers(&bm->vdata, CD_SHAPEKEY) - 1;
	
	BM_ITER_MESH (v, &viter, bm, BM_VERTS_OF_MESH) {
		float *co = CustomData_bmesh_get_n(&bm->vdata, v->head.data, CD_SHAPEKEY, skey);
		copy_v3_v3(co, v->co);
	}

	/* first go through and tag edges */
	BMO_slot_buffer_from_enabled_flag(bm, op, op->slots_in, "edges", BM_EDGE, SUBD_SPLIT);

	params.numcuts = numcuts;
	params.op = op;
	params.slot_edgepercents   = BMO_slot_get(op->slots_in, "edgepercents");
	params.slot_custompatterns = BMO_slot_get(op->slots_in, "custompatterns");
	params.smooth = smooth;
	params.seed = seed;
	params.fractal = fractal;
	params.along_normal = along_normal;
	params.use_smooth  = (smooth  != 0.0f);
	params.use_fractal = (fractal != 0.0f);
	params.use_sphere  = use_sphere;
	params.origkey = skey;
	params.off[0] = (float)BLI_drand() * 200.0f;
	params.off[1] = (float)BLI_drand() * 200.0f;
	params.off[2] = (float)BLI_drand() * 200.0f;
	
	BMO_slot_map_to_flag(bm, op->slots_in, "custompatterns",
	                     BM_FACE, FACE_CUSTOMFILL);

	BMO_slot_map_to_flag(bm, op->slots_in, "edgepercents",
	                     BM_EDGE, EDGE_PERCENT);


	BM_ITER_MESH (face, &fiter, bm, BM_FACES_OF_MESH) {
		BMEdge *e1 = NULL, *e2 = NULL;
		float vec1[3], vec2[3];

		/* figure out which pattern to use */

		BLI_array_empty(edges);
		BLI_array_empty(verts);

		BLI_array_grow_items(edges, face->len);
		BLI_array_grow_items(verts, face->len);

		matched = 0;

		totesel = 0;
		BM_ITER_ELEM_INDEX (nl, &liter, face, BM_LOOPS_OF_FACE, i) {
			edges[i] = nl->e;
			verts[i] = nl->v;

			if (BMO_elem_flag_test(bm, edges[i], SUBD_SPLIT)) {
				if (!e1) e1 = edges[i];
				else     e2 = edges[i];

				totesel++;
			}
		}

		/* make sure the two edges have a valid angle to each other */
		if (totesel == 2 && BM_edge_share_vert_check(e1, e2)) {
			sub_v3_v3v3(vec1, e1->v2->co, e1->v1->co);
			sub_v3_v3v3(vec2, e2->v2->co, e2->v1->co);
			normalize_v3(vec1);
			normalize_v3(vec2);

			if (fabsf(dot_v3v3(vec1, vec2)) > 1.0f - FLT_FACE_SPLIT_EPSILON) {
				totesel = 0;
			}
		}

		if (BMO_elem_flag_test(bm, face, FACE_CUSTOMFILL)) {
			pat = BMO_slot_map_data_get(params.slot_custompatterns, face);
			for (i = 0; i < pat->len; i++) {
				matched = 1;
				for (j = 0; j < pat->len; j++) {
					a = (j + i) % pat->len;
					if ((!!BMO_elem_flag_test(bm, edges[a], SUBD_SPLIT)) != (!!pat->seledges[j])) {
						matched = 0;
						break;
					}
				}
				if (matched) {
					BLI_array_grow_one(facedata);
					b = BLI_array_count(facedata) - 1;
					facedata[b].pat = pat;
					facedata[b].start = verts[i];
					facedata[b].face = face;
					facedata[b].totedgesel = totesel;
					BMO_elem_flag_enable(bm, face, SUBD_SPLIT);
					break;
				}
			}

			/* obvously don't test for other patterns matching */
			continue;
		}

		for (i = 0; i < PATTERNS_TOT; i++) {
			pat = patterns[i];
			if (!pat) {
				continue;
			}

			if (pat->len == face->len) {
				for (a = 0; a < pat->len; a++) {
					matched = 1;
					for (b = 0; b < pat->len; b++) {
						j = (b + a) % pat->len;
						if ((!!BMO_elem_flag_test(bm, edges[j], SUBD_SPLIT)) != (!!pat->seledges[b])) {
							matched = 0;
							break;
						}
					}
					if (matched) {
						break;
					}
				}
				if (matched) {
					BLI_array_grow_one(facedata);
					j = BLI_array_count(facedata) - 1;

					BMO_elem_flag_enable(bm, face, SUBD_SPLIT);

					facedata[j].pat = pat;
					facedata[j].start = verts[a];
					facedata[j].face = face;
					facedata[j].totedgesel = totesel;
					break;
				}
			}

		}
		
		if (!matched && totesel) {
			BLI_array_grow_one(facedata);
			j = BLI_array_count(facedata) - 1;
			
			BMO_elem_flag_enable(bm, face, SUBD_SPLIT);
			facedata[j].totedgesel = totesel;
			facedata[j].face = face;
		}
	}

	einput = BMO_slot_get(op->slots_in, "edges");

	/* go through and split edges */
	for (i = 0; i < einput->len; i++) {
		edge = einput->data.buf[i];
		bm_subdivide_multicut(bm, edge, &params, edge->v1, edge->v2);
	}

	/* copy original-geometry displacements to current coordinates */
	BM_ITER_MESH (v, &viter, bm, BM_VERTS_OF_MESH) {
		float *co = CustomData_bmesh_get_n(&bm->vdata, v->head.data, CD_SHAPEKEY, skey);
		copy_v3_v3(v->co, co);
	}

	i = 0;
	for (i = 0; i < BLI_array_count(facedata); i++) {
		face = facedata[i].face;

		/* figure out which pattern to use */
		BLI_array_empty(verts);

		pat = facedata[i].pat;

		if (!pat && facedata[i].totedgesel == 2) {
			int vlen;
			
			/* ok, no pattern.  we still may be able to do something */
			BLI_array_empty(loops);
			BLI_array_empty(loops_split);

			/* for case of two edges, connecting them shouldn't be too hard */
			BLI_array_grow_items(loops, face->len);
			BM_ITER_ELEM_INDEX (l, &liter, face, BM_LOOPS_OF_FACE, a) {
				loops[a] = l;
			}
			
			vlen = BLI_array_count(loops);

			/* find the boundary of one of the split edges */
			for (a = 1; a < vlen; a++) {
				if (!BMO_elem_flag_test(bm, loops[a - 1]->v, ELE_INNER) &&
				    BMO_elem_flag_test(bm, loops[a]->v, ELE_INNER))
				{
					break;
				}
			}
			
			if (BMO_elem_flag_test(bm, loops[(a + numcuts + 1) % vlen]->v, ELE_INNER)) {
				b = (a + numcuts + 1) % vlen;
			}
			else {
				/* find the boundary of the other edge. */
				for (j = 0; j < vlen; j++) {
					b = (j + a + numcuts + 1) % vlen;
					if (!BMO_elem_flag_test(bm, loops[b == 0 ? vlen - 1 : b - 1]->v, ELE_INNER) &&
					    BMO_elem_flag_test(bm, loops[b]->v, ELE_INNER))
					{
						break;
					}
				}
			}
			
			b += numcuts - 1;

			BLI_array_grow_items(loops_split, numcuts);
			for (j = 0; j < numcuts; j++) {
				int ok = TRUE;

				/* Check for special case: [#32500]
				 * This edge pair could be used by more then one face,
				 * in this case it used to (2.63), split both faces along the same verts
				 * while it could be calculated which face should do the split,
				 * it's ambiguous, so in this case we're better off to skip them as exceptional cases
				 * and not try to be clever guessing which face to cut up.
				 *
				 * To avoid this case we need to check:
				 * Do the verts of each share a face besides the one we are subdividing,
				 *  (but not connect to make an edge of that face).
				 */
				{
					BMLoop *other_loop;
					BMIter other_fiter;
					BM_ITER_ELEM (other_loop, &other_fiter, loops[a]->v, BM_LOOPS_OF_VERT) {
						if (other_loop->f != face) {
							if (BM_vert_in_face(other_loop->f, loops[b]->v)) {
								/* we assume that these verts are not making an edge in the face */
								BLI_assert(other_loop->prev->v != loops[a]->v);
								BLI_assert(other_loop->next->v != loops[a]->v);

								ok = FALSE;
								break;
							}
						}
					}
				}


				if (ok == TRUE) {
					loops_split[j][0] = loops[a];
					loops_split[j][1] = loops[b];
				}
				else {
					loops_split[j][0] = NULL;
					loops_split[j][1] = NULL;
				}

				b = (b - 1) % vlen;
				a = (a + 1) % vlen;
			}
			
			/* Since these are newly created vertices, we don't need to worry about them being legal,
			 * ... though there are some cases we _should_ check for
			 * - concave corner of an ngon.
			 * - 2 edges being used in 2+ ngons.
			 */
//			BM_face_legal_splits(bm, face, loops_split, BLI_array_count(loops_split));

			for (j = 0; j < BLI_array_count(loops_split); j++) {
				if (loops_split[j][0]) {
					BLI_assert(BM_edge_exists(loops_split[j][0]->v, loops_split[j][1]->v) == FALSE);

					/* BMFace *nf = */ /* UNUSED */
					BM_face_split(bm, face, loops_split[j][0]->v, loops_split[j][1]->v, &nl, NULL, FALSE);
				}
			}

			continue;
		}
		else if (!pat) {
			continue;
		}

		a = 0;
		BM_ITER_ELEM_INDEX (nl, &liter, face, BM_LOOPS_OF_FACE, j) {
			if (nl->v == facedata[i].start) {
				a = j + 1;
				break;
			}
		}

		BLI_array_grow_items(verts, face->len);

		BM_ITER_ELEM_INDEX (nl, &liter, face, BM_LOOPS_OF_FACE, j) {
			b = (j - a + face->len) % face->len;
			verts[b] = nl->v;
		}

		BM_CHECK_ELEMENT(face);
		pat->connectexec(bm, face, verts, &params);
	}

	/* copy original-geometry displacements to current coordinates */
	BM_ITER_MESH (v, &viter, bm, BM_VERTS_OF_MESH) {
		float *co = CustomData_bmesh_get_n(&bm->vdata, v->head.data, CD_SHAPEKEY, skey);
		copy_v3_v3(v->co, co);
	}

	BM_data_layer_free_n(bm, &bm->vdata, CD_SHAPEKEY, skey);
	
	if (facedata) BLI_array_free(facedata);
	if (edges) BLI_array_free(edges);
	if (verts) BLI_array_free(verts);
	BLI_array_free(loops_split);
	BLI_array_free(loops);

	BMO_slot_buffer_from_enabled_flag(bm, op, op->slots_out, "geom_inner.out", BM_ALL, ELE_INNER);
	BMO_slot_buffer_from_enabled_flag(bm, op, op->slots_out, "geom_split.out", BM_ALL, ELE_SPLIT);
	
	BMO_slot_buffer_from_enabled_flag(bm, op, op->slots_out, "geom.out", BM_ALL, ELE_INNER | ELE_SPLIT | SUBD_SPLIT);
}

/* editmesh-emulating function */
void BM_mesh_esubdivide(BMesh *bm, const char edge_hflag,
                        float smooth, float fractal, float along_normal,
                        int numcuts,
                        int seltype, int cornertype,
                        const short use_singleedge, const short use_gridfill,
                        int seed)
{
	BMOperator op;
	
	/* use_sphere isnt exposed here since its only used for new primitives */
	BMO_op_initf(bm, &op, BMO_FLAG_DEFAULTS,
	             "subdivide_edges edges=%he "
	             "smooth=%f fractal=%f along_normal=%f "
	             "cuts=%i "
	             "quad_corner_type=%i "
	             "use_singleedge=%b use_gridfill=%b "
	             "seed=%i",
	             edge_hflag,
	             smooth, fractal, along_normal,
	             numcuts,
	             cornertype,
	             use_singleedge, use_gridfill,
	             seed);
	
	BMO_op_exec(bm, &op);
	
	if (seltype == SUBDIV_SELECT_INNER) {
		BMOIter iter;
		BMElem *ele;

		for (ele = BMO_iter_new(&iter, op.slots_out, "geom_inner.out", BM_EDGE | BM_VERT); ele; ele = BMO_iter_step(&iter)) {
			BM_elem_select_set(bm, ele, TRUE);
		}
	}
	else if (seltype == SUBDIV_SELECT_LOOPCUT) {
		BMOIter iter;
		BMElem *ele;
		
		/* deselect input */
		BM_mesh_elem_hflag_disable_all(bm, BM_VERT | BM_EDGE | BM_FACE, BM_ELEM_SELECT, FALSE);

		for (ele = BMO_iter_new(&iter, op.slots_out, "geom_inner.out", BM_EDGE | BM_VERT); ele; ele = BMO_iter_step(&iter)) {
			BM_elem_select_set(bm, ele, TRUE);

			if (ele->head.htype == BM_VERT) {
				BMEdge *e;
				BMIter eiter;

				BM_ITER_ELEM (e, &eiter, ele, BM_EDGES_OF_VERT) {
					if (!BM_elem_flag_test(e, BM_ELEM_SELECT) &&
					     BM_elem_flag_test(e->v1, BM_ELEM_SELECT) &&
					     BM_elem_flag_test(e->v2, BM_ELEM_SELECT))
					{
						BM_edge_select_set(bm, e, TRUE);
					}
					else if (BM_elem_flag_test(e, BM_ELEM_SELECT) &&
					         (!BM_elem_flag_test(e->v1, BM_ELEM_SELECT) ||
					          !BM_elem_flag_test(e->v2, BM_ELEM_SELECT)))
					{
						BM_edge_select_set(bm, e, FALSE);
					}
				}
			}
		}
	}

	BMO_op_finish(bm, &op);
}

void bmo_bisect_edges_exec(BMesh *bm, BMOperator *op)
{
	BMOIter siter;
	BMEdge *e;
	SubDParams params = {0};
	int skey;
	
	params.numcuts = BMO_slot_int_get(op->slots_in, "cuts");
	params.op = op;
	params.slot_edgepercents = BMO_slot_get(op->slots_in, "edgepercents");
	
	BM_data_layer_add(bm, &bm->vdata, CD_SHAPEKEY);
	skey = CustomData_number_of_layers(&bm->vdata, CD_SHAPEKEY) - 1;
	
	params.origkey = skey;

	/* go through and split edges */
	BMO_ITER (e, &siter, op->slots_in, "edges", BM_EDGE) {
		bm_subdivide_multicut(bm, e, &params, e->v1, e->v2);
	}

	BMO_slot_buffer_from_enabled_flag(bm, op, op->slots_out, "geom_split.out", BM_ALL, ELE_SPLIT);

	BM_data_layer_free_n(bm, &bm->vdata, CD_SHAPEKEY, skey);
}
