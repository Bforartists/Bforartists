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
 * Contributor(s): Joseph Eagar, Aleksandr Mokhov, Howard Trickey
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/bmesh/operators/bmo_bevel.c
 *  \ingroup bmesh
 */

#include "MEM_guardedalloc.h"

#include "BLI_array.h"
#include "BLI_math.h"
#include "BLI_memarena.h"

#include "BKE_customdata.h"

#include "bmesh.h"

#include "intern/bmesh_operators_private.h" /* own include */

/* experemental - Campbell */
// #define USE_ALTERNATE_ADJ

#define BEVEL_FLAG      1
#define EDGE_SELECTED   2

#define BEVEL_EPSILON  1e-6

/* Constructed vertex, sometimes later instantiated as BMVert */
typedef struct NewVert {
	BMVert *v;
	float co[3];
} NewVert;

struct BoundVert;

/* Data for one end of an edge involved in a bevel */
typedef struct EdgeHalf {
	struct EdgeHalf *next, *prev;   /* in CCW order */
	BMEdge *e;                  /* original mesh edge */
	int isbev;                  /* is this edge beveled? */
	int isrev;                  /* is e->v2 the vertex at this end? */
	int seg;                    /* how many segments for the bevel */
	float offset;               /* offset for this edge */
	BMFace *fprev;              /* face between this edge and previous, if any */
	BMFace *fnext;              /* face between this edge and next, if any */
	struct BoundVert *leftv;    /* left boundary vert (looking along edge to end) */
	struct BoundVert *rightv;   /* right boundary vert, if beveled */
} EdgeHalf;

/* An element in a cyclic boundary of a Vertex Mesh (VMesh) */
typedef struct BoundVert {
	struct BoundVert *next, *prev;  /* in CCW order */
	int index;          /* used for vmesh indexing */
	NewVert nv;
	EdgeHalf *efirst;   /* first of edges attached here: in CCW order */
	EdgeHalf *elast;
	EdgeHalf *ebev;     /* beveled edge whose left side is attached here, if any */
} BoundVert;

/* Mesh structure replacing a vertex */
typedef struct VMesh {
	enum {
		M_NONE,         /* no polygon mesh needed */
		M_POLY,         /* a simple polygon */
		M_ADJ,          /* "adjacent edges" mesh pattern */
		M_CROSS,        /* "cross edges" mesh pattern */
		M_TRI_FAN,      /* a simple polygon - fan filled */
		M_QUAD_STRIP,   /* a simple polygon - cut into paralelle strips */
	} mesh_kind;
	int count;          /* number of vertices in the boundary */
	int seg;            /* common # of segments for segmented edges */
	BoundVert *boundstart;      /* start of boundary double-linked list */
	NewVert *mesh;          /* allocated array - size and structure depends on kind */
} VMesh;

/* Data for a vertex involved in a bevel */
typedef struct BevVert {
	BMVert *v;          /* original mesh vertex */
	int edgecount;          /* total number of edges around the vertex */
	int selcount;           /* number of selected edges around the vertex */
	EdgeHalf *edges;        /* array of size edgecount; CCW order from vertex normal side */
	VMesh *vmesh;           /* mesh structure for replacing vertex */
} BevVert;

/*
 * Bevel parameters and state
 */
typedef struct BevelParams {
	/* hash of BevVert for each vertex involved in bevel
	 * GHash: (key=(BMVert *), value=(BevVert *)) */
	GHash    *vert_hash;
	MemArena *mem_arena;    /* use for all allocs while bevel runs, if we need to free we can switch to mempool */

	float offset;           /* blender units to offset each side of a beveled edge */
	int seg;                /* number of segments in beveled edge profile */
} BevelParams;

//#include "bevdebug.c"

/* Make a new BoundVert of the given kind, insert it at the end of the circular linked
 * list with entry point bv->boundstart, and return it. */
static BoundVert *add_new_bound_vert(MemArena *mem_arena, VMesh *vm, const float co[3])
{
	BoundVert *ans = (BoundVert *)BLI_memarena_alloc(mem_arena, sizeof(BoundVert));

	copy_v3_v3(ans->nv.co, co);
	if (!vm->boundstart) {
		ans->index = 0;
		vm->boundstart = ans;
		ans->next = ans->prev = ans;
	}
	else {
		BoundVert *tail = vm->boundstart->prev;
		ans->index = tail->index + 1;
		ans->prev = tail;
		ans->next = vm->boundstart;
		tail->next = ans;
		vm->boundstart->prev = ans;
	}
	vm->count++;
	return ans;
}

/* Mesh verts are indexed (i, j, k) where
 * i = boundvert index (0 <= i < nv)
 * j = ring index (0 <= j <= ns2)
 * k = segment index (0 <= k <= ns)
 * Not all of these are used, and some will share BMVerts */
static NewVert *mesh_vert(VMesh *vm, int i, int j, int k)
{
	int nj = (vm->seg / 2) + 1;
	int nk = vm->seg + 1;

	return &vm->mesh[i * nk * nj  + j * nk + k];
}

static void create_mesh_bmvert(BMesh *bm, VMesh *vm, int i, int j, int k, BMVert *eg)
{
	NewVert *nv = mesh_vert(vm, i, j, k);
	nv->v = BM_vert_create(bm, nv->co, eg);
}

static void copy_mesh_vert(VMesh *vm, int ito, int jto, int kto,
                           int ifrom, int jfrom, int kfrom)
{
	NewVert *nvto, *nvfrom;

	nvto = mesh_vert(vm, ito, jto, kto);
	nvfrom = mesh_vert(vm, ifrom, jfrom, kfrom);
	nvto->v = nvfrom->v;
	copy_v3_v3(nvto->co, nvfrom->co);
}

/* find the EdgeHalf in bv's array that has edge bme */
static EdgeHalf *find_edge_half(BevVert *bv, BMEdge *bme)
{
	int i;

	for (i = 0; i < bv->edgecount; i++) {
		if (bv->edges[i].e == bme)
			return &bv->edges[i];
	}
	return NULL;
}

/* Return the next EdgeHalf after from_e that is beveled.
 * If from_e is NULL, find the first beveled edge. */
static EdgeHalf *next_bev(BevVert *bv, EdgeHalf *from_e)
{
	EdgeHalf *e;

	if (from_e == NULL)
		from_e = &bv->edges[bv->edgecount - 1];
	e = from_e;
	do {
		if (e->isbev) {
			return e;
		}
	} while ((e = e->next) != from_e);
	return NULL;
}

/* find the BevVert corresponding to BMVert bmv */
static BevVert *find_bevvert(BevelParams *bp, BMVert *bmv)
{
	return BLI_ghash_lookup(bp->vert_hash, bmv);
}

/* Return a good respresentative face (for materials, etc.) for faces
 * created around/near BoundVert v */
static BMFace *boundvert_rep_face(BoundVert *v)
{
	BMFace *fans = NULL;
	BMFace *firstf = NULL;
	BMEdge *e1, *e2;
	BMFace *f1, *f2;
	BMIter iter1, iter2;

	BLI_assert(v->efirst != NULL && v->elast != NULL);
	e1 = v->efirst->e;
	e2 = v->elast->e;
	BM_ITER_ELEM (f1, &iter1, e1, BM_FACES_OF_EDGE) {
		if (!firstf)
			firstf = f1;
		BM_ITER_ELEM (f2, &iter2, e2, BM_FACES_OF_EDGE) {
			if (f1 == f2) {
				fans = f1;
				break;
			}
		}
	}
	if (!fans)
		fans = firstf;

	return fans;
}

/* Make ngon from verts alone.
 * Make sure to properly copy face attributes and do custom data interpolation from
 * example face, facerep. */
static BMFace *bev_create_ngon(BMesh *bm, BMVert **vert_arr, int totv, BMFace *facerep)
{
	BMIter iter;
	BMLoop *l;
	BMFace *f;

	if (totv == 3) {
		f = BM_face_create_quad_tri(bm,
		                            vert_arr[0], vert_arr[1], vert_arr[2], NULL, facerep, 0);
	}
	else if (totv == 4) {
		f = BM_face_create_quad_tri(bm,
		                            vert_arr[0], vert_arr[1], vert_arr[2], vert_arr[3], facerep, 0);
	}
	else {
		int i;
		BMEdge *e;
		BMEdge **ee = NULL;
		BLI_array_staticdeclare(ee, 30);

		for (i = 0; i < totv; i++) {
			e = BM_edge_create(bm, vert_arr[i], vert_arr[(i + 1) % totv], NULL, TRUE);
			BLI_array_append(ee, e);
		}
		f = BM_face_create_ngon(bm, vert_arr[0], vert_arr[1], ee, totv, FALSE);
		BLI_array_free(ee);
	}
	if (facerep && f) {
		int has_mdisps = CustomData_has_layer(&bm->ldata, CD_MDISPS);
		BM_elem_attrs_copy(bm, bm, facerep, f);
		BM_ITER_ELEM (l, &iter, f, BM_LOOPS_OF_FACE) {
			BM_loop_interp_from_face(bm, l, facerep, TRUE, TRUE);
			if (has_mdisps)
				BM_loop_interp_multires(bm, l, facerep);
		}
	}
	return f;
}

static BMFace *bev_create_quad_tri(BMesh *bm, BMVert *v1, BMVert *v2, BMVert *v3, BMVert *v4,
                                   BMFace *facerep)
{
	BMVert *varr[4];

	varr[0] = v1;
	varr[1] = v2;
	varr[2] = v3;
	varr[3] = v4;
	return bev_create_ngon(bm, varr, v4 ? 4 : 3, facerep);
}

/*
 * Calculate the meeting point between the offset edges for e1 and e2, putting answer in meetco.
 * e1 and e2 share vertex v and face f (may be NULL) and viewed from the normal side of
 * the bevel vertex,  e1 precedes e2 in CCW order.
 * If on_right is true, offset edge is on right of both edges, where e1 enters v and
 * e2 leave it. If on_right is false, then the offset edge is on the left.
 * When offsets are equal, the new point is on the edge bisector, with length offset/sin(angle/2),
 * but if the offsets are not equal (allowing for this, as bevel modifier has edge weights that may
 * lead to different offsets) then meeting point can be found be intersecting offset lines.
 */
static void offset_meet(EdgeHalf *e1, EdgeHalf *e2, BMVert *v, BMFace *f,
                        int on_right, float meetco[3])
{
	float dir1[3], dir2[3], norm_v[3], norm_perp1[3], norm_perp2[3],
	      off1a[3], off1b[3], off2a[3], off2b[3], isect2[3];

	/* get direction vectors for two offset lines */
	sub_v3_v3v3(dir1, v->co, BM_edge_other_vert(e1->e, v)->co);
	sub_v3_v3v3(dir2, BM_edge_other_vert(e2->e, v)->co, v->co);

	/* get normal to plane where meet point should be */
	cross_v3_v3v3(norm_v, dir2, dir1);
	normalize_v3(norm_v);
	if (!on_right)
		negate_v3(norm_v);
	if (is_zero_v3(norm_v)) {
		/* special case: e1 and e2 are parallel; put offset point perp to both, from v.
		 * need to find a suitable plane.
		 * if offsets are different, we're out of luck: just use e1->offset */
		if (f)
			copy_v3_v3(norm_v, f->no);
		else
			copy_v3_v3(norm_v, v->no);
		cross_v3_v3v3(norm_perp1, dir1, norm_v);
		normalize_v3(norm_perp1);
		copy_v3_v3(off1a, v->co);
		madd_v3_v3fl(off1a, norm_perp1, e1->offset);
		copy_v3_v3(meetco, off1a);
	}
	else {
		/* get vectors perp to each edge, perp to norm_v, and pointing into face */
		if (f) {
			copy_v3_v3(norm_v, f->no);
			normalize_v3(norm_v);
		}
		cross_v3_v3v3(norm_perp1, dir1, norm_v);
		cross_v3_v3v3(norm_perp2, dir2, norm_v);
		normalize_v3(norm_perp1);
		normalize_v3(norm_perp2);

		/* get points that are offset distances from each line, then another point on each line */
		copy_v3_v3(off1a, v->co);
		madd_v3_v3fl(off1a, norm_perp1, e1->offset);
		add_v3_v3v3(off1b, off1a, dir1);
		copy_v3_v3(off2a, v->co);
		madd_v3_v3fl(off2a, norm_perp2, e2->offset);
		add_v3_v3v3(off2b, off2a, dir2);

		/* intersect the lines; by construction they should be on the same plane and not parallel */
		if (!isect_line_line_v3(off1a, off1b, off2a, off2b, meetco, isect2)) {
			BLI_assert(!"offset_meet failure");
			copy_v3_v3(meetco, off1a);  /* just to do something */
		}
	}
}

/* Like offset_meet, but here f1 and f2 must not be NULL and give the
 * planes in which to run the offset lines.  They may not meet exactly,
 * but the line intersection routine will find the closest approach point. */
static void offset_in_two_planes(EdgeHalf *e1, EdgeHalf *e2, BMVert *v,
                                 BMFace *f1, BMFace *f2, float meetco[3])
{
	float dir1[3], dir2[3], norm_perp1[3], norm_perp2[3],
	      off1a[3], off1b[3], off2a[3], off2b[3], isect2[3];

	BLI_assert(f1 != NULL && f2 != NULL);

	/* get direction vectors for two offset lines */
	sub_v3_v3v3(dir1, v->co, BM_edge_other_vert(e1->e, v)->co);
	sub_v3_v3v3(dir2, BM_edge_other_vert(e2->e, v)->co, v->co);

	/* get directions into offset planes */
	cross_v3_v3v3(norm_perp1, dir1, f1->no);
	normalize_v3(norm_perp1);
	cross_v3_v3v3(norm_perp2, dir2, f2->no);
	normalize_v3(norm_perp2);

	/* get points that are offset distances from each line, then another point on each line */
	copy_v3_v3(off1a, v->co);
	madd_v3_v3fl(off1a, norm_perp1, e1->offset);
	add_v3_v3v3(off1b, off1a, dir1);
	copy_v3_v3(off2a, v->co);
	madd_v3_v3fl(off2a, norm_perp2, e2->offset);
	add_v3_v3v3(off2b, off2a, dir2);

	if (fabs(angle_v3v3(dir1, dir2)) < BEVEL_EPSILON) {
		/* lines are parallel; off1a is a good meet point */
		copy_v3_v3(meetco, off1a);
	}
	else if (!isect_line_line_v3(off1a, off1b, off2a, off2b, meetco, isect2)) {
		/* another test says they are parallel */
		copy_v3_v3(meetco, off1a);
	}
}

/* Offset by e->offset in plane with normal plane_no, on left if left==TRUE,
 * else on right.  If no is NULL, choose an arbitrary plane different
 * from eh's direction. */
static void offset_in_plane(EdgeHalf *e, const float plane_no[3], int left, float r[3])
{
	float dir[3], no[3];
	BMVert *v;

	v = e->isrev ? e->e->v1 : e->e->v2;

	sub_v3_v3v3(dir, BM_edge_other_vert(e->e, v)->co, v->co);
	normalize_v3(dir);
	if (plane_no) {
		copy_v3_v3(no, plane_no);
	}
	else {
		zero_v3(no);
		if (fabs(dir[0]) < fabs(dir[1]))
			no[0] = 1.0f;
		else
			no[1] = 1.0f;
	}
	if (left)
		cross_v3_v3v3(r, no, dir);
	else
		cross_v3_v3v3(r, dir, no);
	normalize_v3(r);
	mul_v3_fl(r, e->offset);
}

/* Calculate coordinates of a point a distance d from v on e->e and return it in slideco */
static void slide_dist(EdgeHalf *e, BMVert *v, float d, float slideco[3])
{
	float dir[3], len;

	sub_v3_v3v3(dir, v->co, BM_edge_other_vert(e->e, v)->co);
	len = len_v3(dir);
	normalize_v3(dir);
	if (d > len)
		d = len - (float)(50 * BEVEL_EPSILON);
	copy_v3_v3(slideco, v->co);
	madd_v3_v3fl(slideco, dir, -d);
}

#ifndef USE_ALTERNATE_ADJ
/* Calculate the point on e where line (co_a, co_b) comes closest to and return it in projco */
static void project_to_edge(BMEdge *e, const float co_a[3], const float co_b[3], float projco[3])
{
	float otherco[3];

	if (!isect_line_line_v3(e->v1->co, e->v2->co, co_a, co_b, projco, otherco)) {
		BLI_assert(!"project meet failure");
		copy_v3_v3(projco, e->v1->co);
	}
}
#endif

/* return 1 if a and b are in CCW order on the normal side of f,
 * and -1 if they are reversed, and 0 if there is no shared face f */
static int bev_ccw_test(BMEdge *a, BMEdge *b, BMFace *f)
{
	BMLoop *la, *lb;

	if (!f)
		return 0;
	la = BM_face_edge_share_loop(f, a);
	lb = BM_face_edge_share_loop(f, b);
	if (!la || !lb)
		return 0;
	return lb->next == la ? 1 : -1;
}

#ifdef USE_ALTERNATE_ADJ

static void vmesh_cent(VMesh *vm, float r_cent[3])
{
	BoundVert *v;
	int tot = 0;
	zero_v3(r_cent);

	v = vm->boundstart;
	do {
		add_v3_v3(r_cent, v->nv.co);
		tot++;
	} while ((v = v->next) != vm->boundstart);
	mul_v3_fl(r_cent, 1.0f / (float)tot);
}

/**
 *
 * This example shows a tri fan of quads,
 * but could be an NGon fan of quads too.
 * <pre>
 *      The whole triangle   X
 *      represents the      / \
 *      new bevel face.    /   \
 *                        /     \
 *       Split into      /       \
 *       a quad fan.    /         \
 *                     /           \
 *                    /             \
 *                   /               \
 *          co_prev +-.             .-+
 *                 /   `-._     _.-'   \
 *                / co_cent`-+-'        \
 *               /           |           \
 * Quad of      /            |            \
 * interest -- / ---> X      |             \
 *            /              |              \
 *           /               |               \
 *          /         co_next|                \
 * co_orig +-----------------+-----------------+
 *
 *         For each quad, calcualte UV's based on the following:
 *           U = k    / (vm->seg * 2)
 *           V = ring / (vm->seg * 2)
 *           quad = (co_orig, co_prev, co_cent, co_next)
 *           ... note that co_cent is the same for all quads in the fan.
 * </pre>
 *
 */

static void get_point_on_round_edge(EdgeHalf *e, int ring, int k,
                                    float quad[4][3],
                                    float r_co[3])
{
	const float n = e->seg;
	const float uv[2] = {(ring / n) * 2.0f, (k / n) * 2.0f};

	interp_bilinear_quad_v3(quad, uv[0], uv[1], r_co);
}

#else  /* USE_ALTERNATE_ADJ */

/*
 * calculation of points on the round profile
 * r - result, coordinate of point on round profile
 * method:
 * Inscribe a circle in angle va - v -vb
 * such that it touches the arms at offset from v.
 * Rotate the center-va segment by (i/n) of the
 * angle va - center -vb, and put the endpoint
 * of that segment in r.
 */
static void get_point_on_round_profile(float r_co[3], float offset, int k, int count,
                                       const float va[3], const float v[3], const float vb[3])
{
	float vva[3], vvb[3], angle, center[3], rv[3], axis[3], co[3];

	sub_v3_v3v3(vva, va, v);
	sub_v3_v3v3(vvb, vb, v);
	normalize_v3(vva);
	normalize_v3(vvb);
	angle = angle_v3v3(vva, vvb);

	add_v3_v3v3(center, vva, vvb);
	normalize_v3(center);
	mul_v3_fl(center, offset * (1.0f / cosf(0.5f * angle)));
	add_v3_v3(center, v);           /* coordinates of the center of the inscribed circle */


	sub_v3_v3v3(rv, va, center);    /* radius vector */


	sub_v3_v3v3(co, v, center);
	cross_v3_v3v3(axis, rv, co);    /* calculate axis */

	sub_v3_v3v3(vva, va, center);
	sub_v3_v3v3(vvb, vb, center);
	angle = angle_v3v3(vva, vvb);

	rotate_v3_v3v3fl(co, rv, axis, angle * (float)k / (float)count);

	add_v3_v3(co, center);
	copy_v3_v3(r_co, co);
}

/*
 * Find the point (/n) of the way around the round profile for e,
 * where start point is va, midarc point is vmid, and end point is vb.
 * Return the answer in profileco.
 * Method:
 * Adjust va and vb (along edge direction) so that they are perpendicular
 * to edge at v, then use get_point_on_round_profile, then project
 * back onto original va - vmid - vb plane.
 * If va, vmid, and vb are all on the same plane, just interpolate between va and vb.
 */
static void get_point_on_round_edge(EdgeHalf *e, int k,
                                    const float va[3], const float vmid[3], const float vb[3],
                                    float r_co[3])
{
	float vva[3], vvb[3],  point[3], dir[3], vaadj[3], vbadj[3], p2[3], pn[3];
	int n = e->seg;

	sub_v3_v3v3(vva, va, vmid);
	sub_v3_v3v3(vvb, vb, vmid);
	if (e->isrev)
		sub_v3_v3v3(dir, e->e->v1->co, e->e->v2->co);
	else
		sub_v3_v3v3(dir, e->e->v2->co, e->e->v1->co);
	normalize_v3(dir);
	if (fabsf(angle_v3v3(vva, vvb) - (float)M_PI) > (float)BEVEL_EPSILON) {
		copy_v3_v3(vaadj, va);
		madd_v3_v3fl(vaadj, dir, -len_v3(vva) * cosf(angle_v3v3(vva, dir)));
		copy_v3_v3(vbadj, vb);
		madd_v3_v3fl(vbadj, dir, -len_v3(vvb) * cosf(angle_v3v3(vvb, dir)));

		get_point_on_round_profile(point, e->offset, k, n, vaadj, vmid, vbadj);

		add_v3_v3v3(p2, point, dir);
		cross_v3_v3v3(pn, vva, vvb);
		if (!isect_line_plane_v3(r_co, point, p2, vmid, pn, 0)) {
			/* TODO: track down why this sometimes fails */
			copy_v3_v3(r_co, point);
		}
	}
	else {
		/* planar case */
		interp_v3_v3v3(r_co, va, vb, (float)k / (float)n);
	}
}

#endif  /* !USE_ALTERNATE_ADJ */

/* Make a circular list of BoundVerts for bv, each of which has the coordinates
 * of a vertex on the the boundary of the beveled vertex bv->v.
 * Also decide on the mesh pattern that will be used inside the boundary.
 * Doesn't make the actual BMVerts */
static void build_boundary(MemArena *mem_arena, BevVert *bv)
{
	EdgeHalf *efirst, *e;
	BoundVert *v;
	VMesh *vm;
	float co[3], *no;
	float lastd;

	e = efirst = next_bev(bv, NULL);
	vm = bv->vmesh;

	BLI_assert(bv->edgecount >= 2);  /* since bevel edges incident to 2 faces */

	if (bv->edgecount == 2 && bv->selcount == 1) {
		/* special case: beveled edge meets non-beveled one at valence 2 vert */
		no = e->fprev ? e->fprev->no : (e->fnext ? e->fnext->no : NULL);
		offset_in_plane(e, no, TRUE, co);
		v = add_new_bound_vert(mem_arena, vm, co);
		v->efirst = v->elast = v->ebev = e;
		e->leftv = v;
		no = e->fnext ? e->fnext->no : (e->fprev ? e->fprev->no : NULL);
		offset_in_plane(e, no, FALSE, co);
		v = add_new_bound_vert(mem_arena, vm, co);
		v->efirst = v->elast = e;
		e->rightv = v;
		/* make artifical extra point along unbeveled edge, and form triangle */
		slide_dist(e->next, bv->v, e->offset, co);
		v = add_new_bound_vert(mem_arena, vm, co);
		v->efirst = v->elast = e->next;
		vm->mesh_kind = M_POLY;
		return;
	}

	lastd = e->offset;
	vm->boundstart = NULL;
	do {
		if (e->isbev) {
			/* handle only left side of beveled edge e here: next iteration should do right side */
			if (e->prev->isbev) {
				BLI_assert(e->prev != e);  /* see: wire edge special case */
				offset_meet(e->prev, e, bv->v, e->fprev, TRUE, co);
				v = add_new_bound_vert(mem_arena, vm, co);
				v->efirst = e->prev;
				v->elast = v->ebev = e;
				e->leftv = v;
				e->prev->rightv = v;
			}
			else {
				/* e->prev is not beveled */
				if (e->prev->prev->isbev) {
					BLI_assert(e->prev->prev != e); /* see: edgecount 2, selcount 1 case */
					/* find meet point between e->prev->prev and e and attach e->prev there */
					/* TODO: fix case when one or both faces in following are NULL */
					offset_in_two_planes(e->prev->prev, e, bv->v,
					                     e->prev->prev->fnext, e->fprev, co);
					v = add_new_bound_vert(mem_arena, vm, co);
					v->efirst = e->prev->prev;
					v->elast = v->ebev = e;
					e->leftv = v;
					e->prev->leftv = v;
					e->prev->prev->rightv = v;
				}
				else {
					/* neither e->prev nor e->prev->prev are beveled: make on-edge on e->prev */
					offset_meet(e->prev, e, bv->v, e->fprev, TRUE, co);
					v = add_new_bound_vert(mem_arena, vm, co);
					v->efirst = e->prev;
					v->elast = v->ebev = e;
					e->leftv = v;
					e->prev->leftv = v;
				}
			}
			lastd = len_v3v3(bv->v->co, v->nv.co);
		}
		else {
			/* e is not beveled */
			if (e->next->isbev) {
				/* next iteration will place e between beveled previous and next edges */
				/* do nothing... */
			}
			else if (e->prev->isbev) {
				/* on-edge meet between e->prev and e */
				offset_meet(e->prev, e, bv->v, e->fprev, TRUE, co);
				v = add_new_bound_vert(mem_arena, vm, co);
				v->efirst = e->prev;
				v->elast = e;
				e->leftv = v;
				e->prev->rightv = v;
			}
			else {
				/* None of e->prev, e, e->next are beveled.
				 * could either leave alone or add slide points to make
				 * one polygon around bv->v.  For now, we choose latter.
				 * Could slide to make an even bevel plane but for now will
				 * just use last distance a meet point moved from bv->v. */
				slide_dist(e, bv->v, lastd, co);
				v = add_new_bound_vert(mem_arena, vm, co);
				v->efirst = v->elast = e;
				e->leftv = v;
			}
		}
	} while ((e = e->next) != efirst);

	BLI_assert(vm->count >= 2);
	if (vm->count == 2 && bv->edgecount == 3) {
		vm->mesh_kind = M_NONE;
	}
	else if (efirst->seg == 1 || bv->selcount == 1) {
		if (vm->count == 3 && bv->selcount == 1) {
			vm->mesh_kind = M_TRI_FAN;
		}
		else {
			vm->mesh_kind = M_POLY;
		}
	}
	else {
		if (bv->selcount == 2) {
			vm->mesh_kind = M_QUAD_STRIP;
		}
		else {
			vm->mesh_kind = M_ADJ;
		}
	}
	/* TODO: if vm->count == 4 and bv->selcount == 4, use M_CROSS pattern */
}

/*
 * Given that the boundary is built and the boundary BMVerts have been made,
 * calculate the positions of the interior mesh points for the M_ADJ pattern,
 * then make the BMVerts and the new faces. */
static void bevel_build_rings(BMesh *bm, BevVert *bv)
{
	int k, ring, i, n, ns, ns2, nn;
	VMesh *vm = bv->vmesh;
	BoundVert *v, *vprev, *vnext;
	NewVert *nv, *nvprev, *nvnext;
	BMVert *bmv, *bmv1, *bmv2, *bmv3, *bmv4;
	BMFace *f;
	float co[3], coa[3], cob[3], midco[3];

#ifdef USE_ALTERNATE_ADJ
	/* ordered as follows (orig, prev, center, next)*/
	float quad[4][3];
	/* the rest are initialized inline, this remains the same for all */
	vmesh_cent(vm, quad[2]);
#endif

	n = vm->count;
	ns = vm->seg;
	ns2 = ns / 2;
	BLI_assert(n > 2 && ns > 1);
	/* Make initial rings, going between points on neighbors.
	 * After this loop, will have coords for all (i, r, k) where
	 * BoundVert for i has a bevel, 0 <= r <= ns2, 0 <= k <= ns */
	for (ring = 1; ring <= ns2; ring++) {
		v = vm->boundstart;

		do {
			i = v->index;
			if (v->ebev) {
				/* get points coords of points a and b, on outer rings
				 * of prev and next edges, k away from this edge */
				vprev = v->prev;
				vnext = v->next;

				if (vprev->ebev)
					nvprev = mesh_vert(vm, vprev->index, 0, ns - ring);
				else
					nvprev = mesh_vert(vm, vprev->index, 0, ns);
				copy_v3_v3(coa, nvprev->co);
				nv = mesh_vert(vm, i, ring, 0);
				copy_v3_v3(nv->co, coa);
				nv->v = nvprev->v;

				if (vnext->ebev)
					nvnext = mesh_vert(vm, vnext->index, 0, ring);
				else
					nvnext = mesh_vert(vm, vnext->index, 0, 0);
				copy_v3_v3(cob, nvnext->co);
				nv = mesh_vert(vm, i, ring, ns);
				copy_v3_v3(nv->co, cob);
				nv->v = nvnext->v;

#ifdef USE_ALTERNATE_ADJ
				copy_v3_v3(quad[0], v->nv.co);
				mid_v3_v3v3(quad[1], v->nv.co, v->prev->nv.co);
				/* quad[2] is set */
				mid_v3_v3v3(quad[3], v->nv.co, v->next->nv.co);
#endif

#ifdef USE_ALTERNATE_ADJ
				for (k = 1; k < ns; k++) {
					get_point_on_round_edge(v->ebev, ring, k, quad, co);
					copy_v3_v3(mesh_vert(vm, i, ring, k)->co, co);
				}
#else
				/* TODO: better calculation of new midarc point? */
				project_to_edge(v->ebev->e, coa, cob, midco);

				for (k = 1; k < ns; k++) {
					get_point_on_round_edge(v->ebev, k, coa, midco, cob, co);
					copy_v3_v3(mesh_vert(vm, i, ring, k)->co, co);
				}
#endif
			}
		} while ((v = v->next) != vm->boundstart);
	}

	/* Now make sure cross points of rings share coordinates and vertices.
	 * After this loop, will have BMVerts for all (i, r, k) where
	 * i is for a BoundVert that is beveled and has either a predecessor or
	 * successor BoundVert beveled too, and
	 * for odd ns: 0 <= r <= ns2, 0 <= k <= ns
	 * for even ns: 0 <= r < ns2, 0 <= k <= ns except k=ns2 */
	v = vm->boundstart;
	do {
		i = v->index;
		if (v->ebev) {
			vprev = v->prev;
			vnext = v->next;
			if (vprev->ebev) {
				for (ring = 1; ring <= ns2; ring++) {
					for (k = 1; k <= ns2; k++) {
						if (ns % 2 == 0 && (k == ns2 || ring == ns2))
							continue;  /* center line is special case: do after the rest are done */
						nv = mesh_vert(vm, i, ring, k);
						nvprev = mesh_vert(vm, vprev->index, k, ns - ring);
						mid_v3_v3v3(co, nv->co, nvprev->co);
#ifndef USE_ALTERNATE_ADJ
						copy_v3_v3(nv->co, co);
#endif
						BLI_assert(nv->v == NULL && nvprev->v == NULL);
						create_mesh_bmvert(bm, vm, i, ring, k, bv->v);
						copy_mesh_vert(vm, vprev->index, k, ns - ring, i, ring, k);
					}
				}
				if (!vprev->prev->ebev) {
					for (ring = 1; ring <= ns2; ring++) {
						for (k = 1; k <= ns2; k++) {
							if (ns % 2 == 0 && (k == ns2 || ring == ns2))
								continue;
							create_mesh_bmvert(bm, vm, vprev->index, ring, k, bv->v);
						}
					}
				}
				if (!vnext->ebev) {
					for (ring = 1; ring <= ns2; ring++) {
						for (k = ns - ns2; k < ns; k++) {
							if (ns % 2 == 0 && (k == ns2 || ring == ns2))
								continue;
							create_mesh_bmvert(bm, vm, i, ring, k, bv->v);
						}
					}
				}
			}
		}
	} while ((v = v->next) != vm->boundstart);

	if (ns % 2 == 0) {
		/* Do special case center lines.
		 * This loop makes verts for (i, ns2, k) for 1 <= k <= ns-1, k!=ns2
		 * and for (i, r, ns2) for 1 <= r <= ns2-1,
		 * whenever i is in a sequence of at least two beveled verts */
		v = vm->boundstart;
		do {
			i = v->index;
			if (v->ebev) {
				vprev = v->prev;
				vnext = v->next;
				for (k = 1; k < ns2; k++) {
					nv = mesh_vert(vm, i, k, ns2);
					if (vprev->ebev)
						nvprev = mesh_vert(vm, vprev->index, ns2, ns - k);
					if (vnext->ebev)
						nvnext = mesh_vert(vm, vnext->index, ns2, k);
					if (vprev->ebev && vnext->ebev) {
						mid_v3_v3v3v3(co, nvprev->co, nv->co, nvnext->co);
#ifndef USE_ALTERNATE_ADJ
						copy_v3_v3(nv->co, co);
#endif
						create_mesh_bmvert(bm, vm, i, k, ns2, bv->v);
						copy_mesh_vert(vm, vprev->index, ns2, ns - k, i, k, ns2);
						copy_mesh_vert(vm, vnext->index, ns2, k, i, k, ns2);

					}
					else if (vprev->ebev) {
						mid_v3_v3v3(co, nvprev->co, nv->co);
#ifndef USE_ALTERNATE_ADJ
						copy_v3_v3(nv->co, co);
#endif
						create_mesh_bmvert(bm, vm, i, k, ns2, bv->v);
						copy_mesh_vert(vm, vprev->index, ns2, ns - k, i, k, ns2);

						create_mesh_bmvert(bm, vm, i, ns2, ns - k, bv->v);
					}
					else if (vnext->ebev) {
						mid_v3_v3v3(co, nv->co, nvnext->co);
#ifndef USE_ALTERNATE_ADJ
						copy_v3_v3(nv->co, co);
#endif
						create_mesh_bmvert(bm, vm, i, k, ns2, bv->v);
						copy_mesh_vert(vm, vnext->index, ns2, k, i, k, ns2);

						create_mesh_bmvert(bm, vm, i, ns2, k, bv->v);
					}
				}
			}
		} while ((v = v->next) != vm->boundstart);

		/* center point need to be average of all centers of rings */
		/* TODO: this is wrong if not all verts have ebev: could have
		 * several disconnected sections of mesh. */
		zero_v3(midco);
		nn = 0;
		v = vm->boundstart;
		do {
			i = v->index;
			if (v->ebev) {
				nv = mesh_vert(vm, i, ns2, ns2);
				add_v3_v3(midco, nv->co);
				nn++;
			}
		} while ((v = v->next) != vm->boundstart);
		mul_v3_fl(midco, 1.0f / nn);
		bmv = BM_vert_create(bm, midco, NULL);
		v = vm->boundstart;
		do {
			i = v->index;
			if (v->ebev) {
				nv = mesh_vert(vm, i, ns2, ns2);
				copy_v3_v3(nv->co, midco);
				nv->v = bmv;
			}
		} while ((v = v->next) != vm->boundstart);
	}

	/* Make the ring quads */
	for (ring = 0; ring < ns2; ring++) {
		v = vm->boundstart;
		do {
			i = v->index;
			f = boundvert_rep_face(v);
			if (v->ebev && (v->prev->ebev || v->next->ebev)) {
				for (k = 0; k < ns2 + (ns % 2); k++) {
					bmv1 = mesh_vert(vm, i, ring, k)->v;
					bmv2 = mesh_vert(vm, i, ring, k + 1)->v;
					bmv3 = mesh_vert(vm, i, ring + 1, k + 1)->v;
					bmv4 = mesh_vert(vm, i, ring + 1, k)->v;
					BLI_assert(bmv1 && bmv2 && bmv3 && bmv4);
					if (bmv3 == bmv4 || bmv1 == bmv4)
						bmv4 = NULL;
					bev_create_quad_tri(bm, bmv1, bmv2, bmv3, bmv4, f);
				}
			}
			else if (v->prev->ebev && v->prev->prev->ebev) {
				/* finish off a sequence of beveled edges */
				i = v->prev->index;
				f = boundvert_rep_face(v->prev);
				for (k = ns2 + (ns % 2); k < ns; k++) {
					bmv1 = mesh_vert(vm, i, ring, k)->v;
					bmv2 = mesh_vert(vm, i, ring, k + 1)->v;
					bmv3 = mesh_vert(vm, i, ring + 1, k + 1)->v;
					bmv4 = mesh_vert(vm, i, ring + 1, k)->v;
					BLI_assert(bmv1 && bmv2 && bmv3 && bmv4);
					if (bmv2 == bmv3) {
						bmv3 = bmv4;
						bmv4 = NULL;
					}
					bev_create_quad_tri(bm, bmv1, bmv2, bmv3, bmv4, f);
				}
			}
		} while ((v = v->next) != vm->boundstart);
	}

	/* Make center ngon if odd number of segments and fully beveled */
	if (ns % 2 == 1 && vm->count == bv->selcount) {
		BMVert **vv = NULL;
		BLI_array_declare(vv);

		v = vm->boundstart;
		do {
			i = v->index;
			BLI_assert(v->ebev);
			BLI_array_append(vv, mesh_vert(vm, i, ns2, ns2)->v);
		} while ((v = v->next) != vm->boundstart);
		f = boundvert_rep_face(vm->boundstart);
		bev_create_ngon(bm, vv, BLI_array_count(vv), f);

		BLI_array_free(vv);
	}

	/* Make 'rest-of-vmesh' polygon if not fully beveled */
	if (vm->count > bv->selcount) {
		int j;
		BMVert **vv = NULL;
		BLI_array_declare(vv);

		v = vm->boundstart;
		f = boundvert_rep_face(v);
		j = 0;
		do {
			i = v->index;
			if (v->ebev) {
				if (!v->prev->ebev) {
					for (k = 0; k < ns2; k++) {
						bmv1 = mesh_vert(vm, i, ns2, k)->v;
						if (!bmv1)
							bmv1 = mesh_vert(vm, i, 0, k)->v;
						if (!(j > 0 && bmv1 == vv[j - 1])) {
							BLI_assert(bmv1 != NULL);
							BLI_array_append(vv, bmv1);
							j++;
						}
					}
				}
				bmv1 = mesh_vert(vm, i, ns2, ns2)->v;
				if (!bmv1)
					bmv1 = mesh_vert(vm, i, 0, ns2)->v;
				if (!(j > 0 && bmv1 == vv[j - 1])) {
					BLI_assert(bmv1 != NULL);
					BLI_array_append(vv, bmv1);
					j++;
				}
				if (!v->next->ebev) {
					for (k = ns - ns2; k < ns; k++) {
						bmv1 = mesh_vert(vm, i, ns2, k)->v;
						if (!bmv1)
							bmv1 = mesh_vert(vm, i, 0, k)->v;
						if (!(j > 0 && bmv1 == vv[j - 1])) {
							BLI_assert(bmv1 != NULL);
							BLI_array_append(vv, bmv1);
							j++;
						}
					}
				}
			}
			else {
				BLI_assert(mesh_vert(vm, i, 0, 0)->v != NULL);
				BLI_array_append(vv, mesh_vert(vm, i, 0, 0)->v);
				j++;
			}
		} while ((v = v->next) != vm->boundstart);
		if (vv[0] == vv[j - 1])
			j--;
		bev_create_ngon(bm, vv, j, f);

		BLI_array_free(vv);
	}
}

static BMFace *bevel_build_poly_ex(BMesh *bm, BevVert *bv)
{
	BMFace *f;
	int n, k;
	VMesh *vm = bv->vmesh;
	BoundVert *v;
	BMVert **vv = NULL;
	BLI_array_declare(vv);

	v = vm->boundstart;
	n = 0;
	do {
		/* accumulate vertices for vertex ngon */
		BLI_array_append(vv, v->nv.v);
		n++;
		if (v->ebev && v->ebev->seg > 1) {
			for (k = 1; k < v->ebev->seg; k++) {
				BLI_array_append(vv, mesh_vert(vm, v->index, 0, k)->v);
				n++;
			}
		}
	} while ((v = v->next) != vm->boundstart);
	if (n > 2) {
		f = bev_create_ngon(bm, vv, n, boundvert_rep_face(v));
	}
	else {
		f = NULL;
	}
	BLI_array_free(vv);
	return f;
}

static void bevel_build_poly(BMesh *bm, BevVert *bv)
{
	bevel_build_poly_ex(bm, bv);
}

static void bevel_build_trifan(BMesh *bm, BevVert *bv)
{
	BMFace *f;
	BLI_assert(next_bev(bv, NULL)->seg == 1 || bv->selcount == 1);

	f = bevel_build_poly_ex(bm, bv);

	if (f) {
		/* we have a polygon which we know starts at the previous vertex, make it into a fan */
		BMLoop *l_fan = BM_FACE_FIRST_LOOP(f)->prev;
		BMVert *v_fan = l_fan->v;

		while (f->len > 3) {
			BMLoop *l_new;
			BMFace *f_new;
			BLI_assert(v_fan == l_fan->v);
			f_new = BM_face_split(bm, f, l_fan->v, l_fan->next->next->v, &l_new, NULL, FALSE);

			if (f_new->len > f->len) {
				f = f_new;
				if      (l_new->v       == v_fan) { l_fan = l_new; }
				else if (l_new->next->v == v_fan) { l_fan = l_new->next; }
				else if (l_new->prev->v == v_fan) { l_fan = l_new->prev; }
				else { BLI_assert(0); }
			}
			else {
				if      (l_fan->v       == v_fan) { l_fan = l_fan; }
				else if (l_fan->next->v == v_fan) { l_fan = l_fan->next; }
				else if (l_fan->prev->v == v_fan) { l_fan = l_fan->prev; }
				else { BLI_assert(0); }
			}
		}
	}
}

static void bevel_build_quadstrip(BMesh *bm, BevVert *bv)
{
	BMFace *f;
	BLI_assert(bv->selcount == 2);

	f = bevel_build_poly_ex(bm, bv);

	if (f) {
		/* we have a polygon which we know starts at this vertex, make it into strips */
		BMVert *v_first = bv->vmesh->boundstart->efirst->next->next->leftv->nv.v;  /* magic? */
		//BMLoop *l_start = BM_FACE_FIRST_LOOP(f);
		BMLoop *l_start = BM_face_vert_share_loop(f, v_first);
		BMLoop *l_a = l_start->prev, *l_a_step;
		BMLoop *l_b = l_start->next, *l_b_step;

		while (f->len > 4) {
			// BMLoop *l_new;
			BMFace *f_new;
			BLI_assert(l_a->f == f);
			BLI_assert(l_b->f == f);

			l_a_step = l_a->prev;
			l_b_step = l_b->next;

			f_new = BM_face_split(bm, f, l_a->v, l_b->v, NULL, NULL, FALSE);

			if (f_new->len > f->len) {
				f = f_new;
			}

			l_a = l_a_step;
			l_b = l_b_step;
		}
	}
}

/* Given that the boundary is built, now make the actual BMVerts
 * for the boundary and the interior of the vertex mesh. */
static void build_vmesh(MemArena *mem_arena, BMesh *bm, BevVert *bv)
{
	VMesh *vm = bv->vmesh;
	BoundVert *v, *weld1, *weld2;
	int n, ns, ns2, i, k, weld;
	float *va, *vb, co[3];

#ifdef USE_ALTERNATE_ADJ
	/* ordered as follows (orig, prev, center, next)*/
	float quad[4][3];
#else
	float midco[3];
#endif

#ifdef USE_ALTERNATE_ADJ
	/* the rest are initialized inline, this remains the same for all */
	vmesh_cent(vm, quad[2]);
#endif

	n = vm->count;
	ns = vm->seg;
	ns2 = ns / 2;

	vm->mesh = (NewVert *)BLI_memarena_alloc(mem_arena, n * (ns2 + 1) * (ns + 1) * sizeof(NewVert));

	/* special case: two beveled ends welded together */
	weld = (bv->selcount == 2) && (vm->count == 2);
	weld1 = weld2 = NULL;   /* will hold two BoundVerts involved in weld */

	/* make (i, 0, 0) mesh verts for all i */
	v = vm->boundstart;
	do {
		i = v->index;
		copy_v3_v3(mesh_vert(vm, i, 0, 0)->co, v->nv.co);
		create_mesh_bmvert(bm, vm, i, 0, 0, bv->v);
		v->nv.v = mesh_vert(vm, i, 0, 0)->v;
		if (weld && v->ebev) {
			if (!weld1)
				weld1 = v;
			else
				weld2 = v;
		}
	} while ((v = v->next) != vm->boundstart);

	/* copy other ends to (i, 0, ns) for all i, and fill in profiles for beveled edges */
	v = vm->boundstart;
	do {

#ifdef USE_ALTERNATE_ADJ
		copy_v3_v3(quad[0], v->nv.co);
		mid_v3_v3v3(quad[1], v->nv.co, v->prev->nv.co);
		/* quad[2] is set */
		mid_v3_v3v3(quad[3], v->nv.co, v->next->nv.co);
#endif

		i = v->index;
		copy_mesh_vert(vm, i, 0, ns, v->next->index, 0, 0);
		if (v->ebev) {
#ifdef USE_ALTERNATE_ADJ
			for (k = 1; k < ns; k++) {
				get_point_on_round_edge(v->ebev, 0, k, quad, co);
				copy_v3_v3(mesh_vert(vm, i, 0, k)->co, co);
				if (!weld)
					create_mesh_bmvert(bm, vm, i, 0, k, bv->v);
			}
#else
			va = mesh_vert(vm, i, 0, 0)->co;
			vb = mesh_vert(vm, i, 0, ns)->co;
			project_to_edge(v->ebev->e, va, vb, midco);
			for (k = 1; k < ns; k++) {
				get_point_on_round_edge(v->ebev, k, va, midco, vb, co);
				copy_v3_v3(mesh_vert(vm, i, 0, k)->co, co);
				if (!weld)
					create_mesh_bmvert(bm, vm, i, 0, k, bv->v);
			}
#endif
		}
	} while ((v = v->next) != vm->boundstart);

	if (weld) {
		vm->mesh_kind = M_NONE;
		for (k = 1; k < ns; k++) {
			va = mesh_vert(vm, weld1->index, 0, k)->co;
			vb = mesh_vert(vm, weld2->index, 0, ns - k)->co;
			mid_v3_v3v3(co, va, vb);
			copy_v3_v3(mesh_vert(vm, weld1->index, 0, k)->co, co);
			create_mesh_bmvert(bm, vm, weld1->index, 0, k, bv->v);
		}
		for (k = 1; k < ns; k++)
			copy_mesh_vert(vm, weld2->index, 0, ns - k, weld1->index, 0, k);
	}

	if (vm->mesh_kind == M_ADJ)
		bevel_build_rings(bm, bv);
	else if (vm->mesh_kind == M_POLY)
		bevel_build_poly(bm, bv);
	else if (vm->mesh_kind == M_TRI_FAN)
		bevel_build_trifan(bm, bv);
	else if (vm->mesh_kind == M_QUAD_STRIP)
		bevel_build_quadstrip(bm, bv);
}

/*
 * Construction around the vertex
 */
static void bevel_vert_construct(BMesh *bm, BevelParams *bp, BMVert *v)
{
	BMEdge *bme;
	BevVert *bv;
	BMEdge *bme2, *unflagged_bme;
	BMFace *f;
	BMIter iter, iter2;
	EdgeHalf *e;
	int i, ntot, found_shared_face, ccw_test_sum;
	int nsel = 0;

	/* Gather input selected edges.
	 * Only bevel selected edges that have exactly two incident faces.
	 */

	BM_ITER_ELEM (bme, &iter, v, BM_EDGES_OF_VERT) {
		if (BM_elem_flag_test(bme, BM_ELEM_TAG)) {
			if (BM_edge_is_manifold(bme)) {
				BMO_elem_flag_enable(bm, bme, EDGE_SELECTED);
				nsel++;
			}
		}
	}

	if (nsel == 0)
		return;

	ntot = BM_vert_edge_count(v);
	bv = (BevVert *)BLI_memarena_alloc(bp->mem_arena, (sizeof(BevVert)));
	bv->v = v;
	bv->edgecount = ntot;
	bv->selcount = nsel;
	bv->edges = (EdgeHalf *)BLI_memarena_alloc(bp->mem_arena, ntot * sizeof(EdgeHalf));
	bv->vmesh = (VMesh *)BLI_memarena_alloc(bp->mem_arena, sizeof(VMesh));
	bv->vmesh->seg = bp->seg;
	BLI_ghash_insert(bp->vert_hash, v, bv);

	/* add edges to bv->edges in order that keeps adjacent edges sharing
	 * a face, if possible */
	i = 0;
	bme = v->e;
	BMO_elem_flag_enable(bm, bme, BEVEL_FLAG);
	e = &bv->edges[0];
	e->e = bme;
	for (i = 0; i < ntot; i++) {
		if (i > 0) {
			/* find an unflagged edge bme2 that shares a face f with previous bme */
			found_shared_face = 0;
			unflagged_bme = NULL;
			BM_ITER_ELEM (bme2, &iter, v, BM_EDGES_OF_VERT) {
				if (BMO_elem_flag_test(bm, bme2, BEVEL_FLAG))
					continue;
				if (!unflagged_bme)
					unflagged_bme = bme2;
				BM_ITER_ELEM (f, &iter2, bme2, BM_FACES_OF_EDGE) {
					if (BM_face_edge_share_loop(f, bme)) {
						found_shared_face = 1;
						break;
					}
				}
				if (found_shared_face)
					break;
			}
			e = &bv->edges[i];
			if (found_shared_face) {
				e->e = bme2;
				e->fprev = f;
				bv->edges[i - 1].fnext = f;
			}
			else {
				e->e = unflagged_bme;
			}
		}
		bme = e->e;
		BMO_elem_flag_enable(bm, bme, BEVEL_FLAG);
		if (BMO_elem_flag_test(bm, bme, EDGE_SELECTED)) {
			e->isbev = 1;
			e->seg = bp->seg;
		}
		else {
			e->isbev = 0;
			e->seg = 0;
		}
		e->isrev = (bme->v2 == v);
		e->offset = e->isbev ? bp->offset : 0.0f;
	}
	/* find wrap-around shared face */
	BM_ITER_ELEM (f, &iter2, bme, BM_FACES_OF_EDGE) {
		if (BM_face_edge_share_loop(f, bv->edges[0].e)) {
			if (bv->edges[0].fnext == f)
				continue;   /* if two shared faces, want the other one now */
			bv->edges[ntot - 1].fnext = f;
			bv->edges[0].fprev = f;
			break;
		}
	}

	/* remove BEVEL_FLAG now that we are finished with it*/
	for (i = 0; i < ntot; i++)
		BMO_elem_flag_disable(bm, bv->edges[i].e, BEVEL_FLAG);

	/* if edge array doesn't go CCW around vertex from average normal side,
	 * reverse the array, being careful to reverse face pointers too */
	if (ntot > 1) {
		ccw_test_sum = 0;
		for (i = 0; i < ntot; i++)
			ccw_test_sum += bev_ccw_test(bv->edges[i].e, bv->edges[(i + 1) % ntot].e,
			                             bv->edges[i].fnext);
		if (ccw_test_sum < 0) {
			for (i = 0; i <= (ntot / 2) - 1; i++) {
				SWAP(EdgeHalf, bv->edges[i], bv->edges[ntot - i - 1]);
				SWAP(BMFace *, bv->edges[i].fprev, bv->edges[i].fnext);
				SWAP(BMFace *, bv->edges[ntot - i - 1].fprev, bv->edges[ntot - i - 1].fnext);
			}
			if (ntot % 2 == 1) {
				i = ntot / 2;
				SWAP(BMFace *, bv->edges[i].fprev,  bv->edges[i].fnext);
			}
		}
	}

	for (i = 0; i < ntot; i++) {
		e = &bv->edges[i];
		e->next = &bv->edges[(i + 1) % ntot];
		e->prev = &bv->edges[(i + ntot - 1) % ntot];
	}

	build_boundary(bp->mem_arena, bv);
	build_vmesh(bp->mem_arena, bm, bv);
}

/* Face f has at least one beveled vertex.  Rebuild f */
static void rebuild_polygon(BMesh *bm, BevelParams *bp, BMFace *f)
{
	BMIter liter;
	BMLoop *l, *lprev;
	BevVert *bv;
	BoundVert *v, *vstart, *vend;
	EdgeHalf *e, *eprev;
	VMesh *vm;
	int i, k;
	BMVert *bmv;
	BMVert **vv = NULL;
	BLI_array_declare(vv);

	BM_ITER_ELEM (l, &liter, f, BM_LOOPS_OF_FACE) {
		bv = find_bevvert(bp, l->v);
		if (bv) {
			lprev = l->prev;
			e = find_edge_half(bv, l->e);
			eprev = find_edge_half(bv, lprev->e);
			BLI_assert(e != NULL && eprev != NULL);
			vstart = eprev->leftv;
			if (e->isbev)
				vend = e->rightv;
			else
				vend = e->leftv;
			v = vstart;
			vm = bv->vmesh;
			BLI_array_append(vv, v->nv.v);
			while (v != vend) {
				if (vm->mesh_kind == M_NONE && v->ebev && v->ebev->seg > 1 && v->ebev != e && v->ebev != eprev) {
					/* case of 3rd face opposite a beveled edge, with no vmesh */
					i = v->index;
					e = v->ebev;
					for (k = 1; k < e->seg; k++) {
						bmv = mesh_vert(vm, i, 0, k)->v;
						BLI_array_append(vv, bmv);
					}
				}
				v = v->prev;
				BLI_array_append(vv, v->nv.v);
			}
		}
		else {
			BLI_array_append(vv, l->v);
		}
	}
	bev_create_ngon(bm, vv, BLI_array_count(vv), f);
	BLI_array_free(vv);
}

/* All polygons touching v need rebuilding because beveling v has made new vertices */
static void bevel_rebuild_existing_polygons(BMesh *bm, BevelParams *bp, BMVert *v)
{
	void    *faces_stack[BM_DEFAULT_ITER_STACK_SIZE];
	int      faces_len, f_index;
	BMFace **faces = BM_iter_as_arrayN(bm, BM_FACES_OF_VERT, v, &faces_len,
	                                   faces_stack, BM_DEFAULT_ITER_STACK_SIZE);

	if (LIKELY(faces != NULL)) {
		for (f_index = 0; f_index < faces_len; f_index++) {
			BMFace *f = faces[f_index];
			rebuild_polygon(bm, bp, f);
			BM_face_kill(bm, f);
		}

		if (faces != (BMFace **)faces_stack) {
			MEM_freeN(faces);
		}
	}
}



/*
 * Build the polygons along the selected Edge
 */
static void bevel_build_edge_polygons(BMesh *bm, BevelParams *bp, BMEdge *bme)
{
	BevVert *bv1, *bv2;
	BMVert *bmv1, *bmv2, *bmv3, *bmv4, *bmv1i, *bmv2i, *bmv3i, *bmv4i;
	VMesh *vm1, *vm2;
	EdgeHalf *e1, *e2;
	BMFace *f1, *f2, *f;
	int k, nseg, i1, i2;

	if (!BM_edge_is_manifold(bme))
		return;

	bv1 = find_bevvert(bp, bme->v1);
	bv2 = find_bevvert(bp, bme->v2);

	BLI_assert(bv1 && bv2);

	e1 = find_edge_half(bv1, bme);
	e2 = find_edge_half(bv2, bme);

	BLI_assert(e1 && e2);

	/*   v4             v3
	 *    \            /
	 *     e->v1 - e->v2
	 *    /            \
	 *   v1             v2
	 */
	nseg = e1->seg;
	BLI_assert(nseg > 0 && nseg == e2->seg);

	bmv1 = e1->leftv->nv.v;
	bmv4 = e1->rightv->nv.v;
	bmv2 = e2->rightv->nv.v;
	bmv3 = e2->leftv->nv.v;

	BLI_assert(bmv1 && bmv2 && bmv3 && bmv4);

	f1 = boundvert_rep_face(e1->leftv);
	f2 = boundvert_rep_face(e1->rightv);

	if (nseg == 1) {
		bev_create_quad_tri(bm, bmv1, bmv2, bmv3, bmv4, f1);
	}
	else {
		i1 = e1->leftv->index;
		i2 = e2->leftv->index;
		vm1 = bv1->vmesh;
		vm2 = bv2->vmesh;
		bmv1i = bmv1;
		bmv2i = bmv2;
		for (k = 1; k <= nseg; k++) {
			bmv4i = mesh_vert(vm1, i1, 0, k)->v;
			bmv3i = mesh_vert(vm2, i2, 0, nseg - k)->v;
			f = (k <= nseg / 2 + (nseg % 2)) ? f1 : f2;
			bev_create_quad_tri(bm, bmv1i, bmv2i, bmv3i, bmv4i, f);
			bmv1i = bmv4i;
			bmv2i = bmv3i;
		}
	}
}

void bmo_bevel_exec(BMesh *bm, BMOperator *op)
{
	BMIter iter;
	BMOIter siter;
	BMVert *v;
	BMEdge *e;
	BevelParams bp = {NULL};

	bp.offset = BMO_slot_float_get(op, "offset");
	bp.seg = BMO_slot_int_get(op, "segments");

	if (bp.offset > 0) {
		/* primary alloc */
		bp.vert_hash = BLI_ghash_ptr_new(__func__);
		bp.mem_arena = BLI_memarena_new((1 << 16), __func__);
		BLI_memarena_use_calloc(bp.mem_arena);

		/* first flush 'geom' into flags, this makes it possible to check connected data */
		BM_mesh_elem_hflag_disable_all(bm, BM_VERT | BM_EDGE, BM_ELEM_TAG, FALSE);

		BMO_ITER (v, &siter, bm, op, "geom", BM_VERT | BM_EDGE) {
			BM_elem_flag_enable(v, BM_ELEM_TAG);
		}

		/* The analysis of the input vertices and execution additional constructions */
		BM_ITER_MESH (v, &iter, bm, BM_VERTS_OF_MESH) {
			if (BM_elem_flag_test(v, BM_ELEM_TAG)) {
				bevel_vert_construct(bm, &bp, v);
			}
		}

		/* Build polygons for edges */
		BM_ITER_MESH (e, &iter, bm, BM_EDGES_OF_MESH) {
			if (BM_elem_flag_test(e, BM_ELEM_TAG)) {
				bevel_build_edge_polygons(bm, &bp, e);
			}
		}

		BM_ITER_MESH (v, &iter, bm, BM_VERTS_OF_MESH) {
			if (BM_elem_flag_test(v, BM_ELEM_TAG)) {
				bevel_rebuild_existing_polygons(bm, &bp, v);
			}
		}

		BM_ITER_MESH (v, &iter, bm, BM_VERTS_OF_MESH) {
			if (BM_elem_flag_test(v, BM_ELEM_TAG)) {
				if (find_bevvert(&bp, v)) {
					BM_vert_kill(bm, v);
				}
			}
		}

		/* primary free */
		BLI_ghash_free(bp.vert_hash, NULL, NULL);
		BLI_memarena_free(bp.mem_arena);
	}
}
