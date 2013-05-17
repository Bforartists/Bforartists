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
 * The Original Code is Copyright (C) 2013 by Campbell Barton.
 * All rights reserved.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/bmesh/intern/bmesh_edgeloop.c
 *  \ingroup bmesh
 *
 * Generic utility functions for getting edge loops from a mesh.
 */

#include "MEM_guardedalloc.h"

#include "BLI_math_vector.h"
#include "BLI_listbase.h"
#include "BLI_mempool.h"

#include "bmesh.h"

#include "bmesh_edgeloop.h"  /* own include */

typedef struct BMEdgeLoopStore {
	struct BMEdgeLoopStore *next, *prev;
	ListBase verts;
	int flag;
	int len;
	/* optional values  to calc */
	float co[3], no[3];
} BMEdgeLoopStore;

#define BM_EDGELOOP_IS_CLOSED (1 << 0)


/* -------------------------------------------------------------------- */
/* BM_mesh_edgeloops_find & Util Functions  */

static int bm_vert_other_tag(BMVert *v, BMVert *v_prev,
                             BMEdge **r_e)
{
	BMIter iter;
	BMEdge *e, *e_next;
	unsigned int count = 0;

	BM_ITER_ELEM (e, &iter, v, BM_EDGES_OF_VERT) {
		if (BM_elem_flag_test(e, BM_ELEM_INTERNAL_TAG)) {
			BMVert *v_other = BM_edge_other_vert(e, v);
			if (v_other != v_prev) {
				e_next = e;
				count++;
			}
		}
	}

	*r_e = e_next;
	return count;
}

/**
 * \return success
 */
static bool bm_loop_build(BMEdgeLoopStore *el_store, BMVert *v_prev, BMVert *v, int dir)
{
	void (*add_fn)(ListBase *, void *) = dir == 1 ? BLI_addhead : BLI_addtail;
	BMEdge *e_next;
	BMVert *v_next;
	BMVert *v_first = v;

	BLI_assert(ABS(dir) == 1);

	if (!BM_elem_flag_test(v, BM_ELEM_INTERNAL_TAG)) {
		return true;
	}

	while (v) {
		LinkData *node = MEM_callocN(sizeof(*node), __func__);
		int count;
		node->data = v;
		add_fn(&el_store->verts, node);
		el_store->len++;
		BM_elem_flag_disable(v, BM_ELEM_INTERNAL_TAG);

		count = bm_vert_other_tag(v, v_prev, &e_next);
		if (count == 1) {
			v_next = BM_edge_other_vert(e_next, v);
			BM_elem_flag_disable(e_next, BM_ELEM_INTERNAL_TAG);
			if (UNLIKELY(v_next == v_first)) {
				el_store->flag |= BM_EDGELOOP_IS_CLOSED;
				v_next = NULL;
			}
		}
		else if (count == 0) {
			/* pass */
			v_next = NULL;
		}
		else {
			v_next = NULL;
			return false;
		}

		v_prev = v;
		v = v_next;
	}

	return true;
}

/**
 * \return listbase of listbases, each linking to a vertex.
 */
int BM_mesh_edgeloops_find(BMesh *bm, ListBase *r_eloops,
                           bool (*test_fn)(BMEdge *, void *user_data), void *user_data)
{
	BMIter iter;
	BMEdge *e;
	BMVert *v;
	int count = 0;

	BM_ITER_MESH (v, &iter, bm, BM_VERTS_OF_MESH) {
		BM_elem_flag_disable(v, BM_ELEM_INTERNAL_TAG);
	}

	/* first flush edges to tags, and tag verts */
	BM_ITER_MESH (e, &iter, bm, BM_EDGES_OF_MESH) {
		if (test_fn(e, user_data)) {
			BM_elem_flag_enable(e,     BM_ELEM_INTERNAL_TAG);
			BM_elem_flag_enable(e->v1, BM_ELEM_INTERNAL_TAG);
			BM_elem_flag_enable(e->v2, BM_ELEM_INTERNAL_TAG);
		}
		else {
			BM_elem_flag_disable(e, BM_ELEM_INTERNAL_TAG);
		}
	}

	BM_ITER_MESH (e, &iter, bm, BM_EDGES_OF_MESH) {
		if (BM_elem_flag_test(e, BM_ELEM_INTERNAL_TAG)) {
			BMEdgeLoopStore *el_store = MEM_callocN(sizeof(BMEdgeLoopStore), __func__);

			/* add both directions */
			if (bm_loop_build(el_store, e->v1, e->v2,  1) &&
			    bm_loop_build(el_store, e->v2, e->v1, -1) &&
			    el_store->len > 1)
			{
				BLI_addtail(r_eloops, el_store);
				BM_elem_flag_disable(e, BM_ELEM_INTERNAL_TAG);
				count++;
			}
			else {
				BM_edgeloop_free(el_store);
			}
		}
	}
	return count;
}


/* -------------------------------------------------------------------- */
/* BM_mesh_edgeloops_find_path & Util Functions  */

/**
 * Find s single, open edge loop - given 2 vertices.
 * Add to
 */
struct VertStep {
	struct VertStep *next, *prev;
	BMVert *v;
};

static void vs_add(BLI_mempool *vs_pool, ListBase *lb,
                   BMVert *v, BMEdge *e_prev, const int iter_tot)
{
	struct VertStep *vs_new = BLI_mempool_alloc(vs_pool);
	vs_new->v = v;

	BM_elem_index_set(v, iter_tot);

	/* This edge stores a direct path back to the original vertex so we can
	 * backtrack without having to store an array of previous verts. */

	/* WARNING - setting the edge is not common practice
	 * but currently harmless, take care. */
	BLI_assert(BM_vert_in_edge(e_prev, v));
	v->e = e_prev;

	BLI_addtail(lb, vs_new);
}

static bool bm_loop_path_build_step(BLI_mempool *vs_pool, ListBase *lb, const int dir, BMVert *v_match[2])
{
	ListBase lb_tmp = {NULL, NULL};
	struct VertStep *vs, *vs_next;
	BLI_assert(ABS(dir) == 1);

	for (vs = lb->first; vs; vs = vs_next) {
		BMIter iter;
		BMEdge *e;
		/* these values will be the same every iteration */
		const int vs_iter_tot  = BM_elem_index_get(vs->v);
		const int vs_iter_next = vs_iter_tot + dir;

		vs_next = vs->next;

		BM_ITER_ELEM (e, &iter, vs->v, BM_EDGES_OF_VERT) {
			if (BM_elem_flag_test(e, BM_ELEM_INTERNAL_TAG)) {
				BMVert *v_next = BM_edge_other_vert(e, vs->v);
				const int v_next_index = BM_elem_index_get(v_next);
				/* not essential to clear flag but prevents more checking next time round */
				BM_elem_flag_disable(e, BM_ELEM_INTERNAL_TAG);
				if (v_next_index == 0) {
					vs_add(vs_pool, &lb_tmp, v_next, e, vs_iter_next);
				}
				else if ((dir < 0) == (v_next_index < 0)) {
					/* on the same side - do nothing */
				}
				else {
					/* we have met out match! (vertices from differnt sides meet) */
					if (dir == 1) {
						v_match[0] = vs->v;
						v_match[1] = v_next;
					}
					else {
						v_match[0] = v_next;
						v_match[1] = vs->v;
					}
					/* normally we would manage memory of remaining items in (lb, lb_tmp),
					 * but search is done, vs_pool will get destroyed immediately */
					return true;
				}
			}
		}

		BLI_mempool_free(vs_pool, vs);
	}

	/* lb is now full of free'd items, overwrite */
	*lb = lb_tmp;

	return (lb->first != NULL);
}

bool BM_mesh_edgeloops_find_path(BMesh *bm, ListBase *r_eloops,
                                 bool (*test_fn)(BMEdge *, void *user_data), void *user_data,
                                 BMVert *v_src, BMVert *v_dst)
{
	BMIter iter;
	BMEdge *e;

	BLI_assert(v_src != v_dst);

	{
		BMVert *v;
		BM_ITER_MESH (v, &iter, bm, BM_VERTS_OF_MESH) {
			BM_elem_index_set(v, 0);
		}
	}
	bm->elem_index_dirty |= BM_VERT;

	/* first flush edges to tags, and tag verts */
	if (test_fn) {
		BM_ITER_MESH (e, &iter, bm, BM_EDGES_OF_MESH) {
			if (test_fn(e, user_data)) {
				BM_elem_flag_enable(e,     BM_ELEM_INTERNAL_TAG);
				BM_elem_flag_enable(e->v1, BM_ELEM_INTERNAL_TAG);
				BM_elem_flag_enable(e->v2, BM_ELEM_INTERNAL_TAG);
			}
			else {
				BM_elem_flag_disable(e, BM_ELEM_INTERNAL_TAG);
			}
		}
	}
	else {
		BM_ITER_MESH (e, &iter, bm, BM_EDGES_OF_MESH) {
			BM_elem_flag_enable(e,     BM_ELEM_INTERNAL_TAG);
			BM_elem_flag_enable(e->v1, BM_ELEM_INTERNAL_TAG);
			BM_elem_flag_enable(e->v2, BM_ELEM_INTERNAL_TAG);
		}
	}

	/* prime the lists and begin search */
	{
		BMVert *v_match[2] = {NULL, NULL};
		ListBase lb_src = {NULL, NULL};
		ListBase lb_dst = {NULL, NULL};
		BLI_mempool *vs_pool = BLI_mempool_create(sizeof(struct VertStep), 1, 512, 0);

		/* edge args are dummy */
		vs_add(vs_pool, &lb_src, v_src, v_src->e,  1);
		vs_add(vs_pool, &lb_dst, v_dst, v_dst->e, -1);

		do {
			if ((bm_loop_path_build_step(vs_pool, &lb_src, 1, v_match) == false) || v_match[0]) {
				break;
			}
			if ((bm_loop_path_build_step(vs_pool, &lb_dst, -1, v_match) == false) || v_match[0]) {
				break;
			}
		} while (true);

		BLI_mempool_destroy(vs_pool);

		if (v_match[0]) {
			BMEdgeLoopStore *el_store = MEM_callocN(sizeof(BMEdgeLoopStore), __func__);
			BMVert *v;

			/* build loop from edge pointers */
			v = v_match[0];
			while (true) {
				LinkData *node = MEM_callocN(sizeof(*node), __func__);
				node->data = v;
				BLI_addhead(&el_store->verts, node);
				el_store->len++;
				if (v == v_src) {
					break;
				}
				v = BM_edge_other_vert(v->e, v);
			}

			v = v_match[1];
			while (true) {
				LinkData *node = MEM_callocN(sizeof(*node), __func__);
				node->data = v;
				BLI_addtail(&el_store->verts, node);
				el_store->len++;
				if (v == v_dst) {
					break;
				}
				v = BM_edge_other_vert(v->e, v);
			}


			BLI_addtail(r_eloops, el_store);

			return true;
		}
	}

	return false;
}


/* -------------------------------------------------------------------- */
/* BM_mesh_edgeloops_xxx utility function */

void BM_mesh_edgeloops_free(ListBase *eloops)
{
	BMEdgeLoopStore *el_store;
	while ((el_store = eloops->first)) {
		BLI_remlink(eloops, el_store);
		BM_edgeloop_free(el_store);
	}
}

void BM_mesh_edgeloops_calc_center(BMesh *bm, ListBase *eloops)
{
	BMEdgeLoopStore *el_store;
	for (el_store = eloops->first; el_store; el_store = el_store->next) {
		BM_edgeloop_calc_center(bm, el_store);
	}
}

void BM_mesh_edgeloops_calc_normal(BMesh *bm, ListBase *eloops)
{
	BMEdgeLoopStore *el_store;
	for (el_store = eloops->first; el_store; el_store = el_store->next) {
		BM_edgeloop_calc_normal(bm, el_store);
	}
}

void BM_mesh_edgeloops_calc_order(BMesh *UNUSED(bm), ListBase *eloops, const bool use_normals)
{
	ListBase eloops_ordered = {NULL};
	BMEdgeLoopStore *el_store;
	float cent[3];
	int tot = 0;
	zero_v3(cent);
	/* assumes we calculated centers already */
	for (el_store = eloops->first; el_store; el_store = el_store->next, tot++) {
		add_v3_v3(cent, el_store->co);
	}
	mul_v3_fl(cent, 1.0f / (float)tot);

	/* find far outest loop */
	{
		BMEdgeLoopStore *el_store_best = NULL;
		float len_best = -1.0f;
		for (el_store = eloops->first; el_store; el_store = el_store->next) {
			const float len = len_squared_v3v3(cent, el_store->co);
			if (len > len_best) {
				len_best = len;
				el_store_best = el_store;
			}
		}

		BLI_remlink(eloops, el_store_best);
		BLI_addtail(&eloops_ordered, el_store_best);
	}

	/* not so efficient re-ordering */
	while (eloops->first) {
		BMEdgeLoopStore *el_store_best = NULL;
		const float *co = ((BMEdgeLoopStore *)eloops_ordered.last)->co;
		const float *no = ((BMEdgeLoopStore *)eloops_ordered.last)->no;
		float len_best = FLT_MAX;
		for (el_store = eloops->first; el_store; el_store = el_store->next) {
			float len;
			if (use_normals) {
				/* scale the length by how close the loops are to pointing at eachother */
				float dir[3];
				sub_v3_v3v3(dir, co, el_store->co);
				len = normalize_v3(dir);
				len = len * ((1.0f - fabsf(dot_v3v3(dir, no))) +
				             (1.0f - fabsf(dot_v3v3(dir, el_store->no))));
			}
			else {
				len = len_squared_v3v3(co, el_store->co);
			}

			if (len < len_best) {
				len_best = len;
				el_store_best = el_store;
			}
		}

		BLI_remlink(eloops, el_store_best);
		BLI_addtail(&eloops_ordered, el_store_best);
	}

	*eloops = eloops_ordered;
}

/* -------------------------------------------------------------------- */
/* BM_edgeloop_*** functions */

BMEdgeLoopStore *BM_edgeloop_copy(BMEdgeLoopStore *el_store)
{
	BMEdgeLoopStore *el_store_copy = MEM_mallocN(sizeof(*el_store), __func__);
	*el_store_copy = *el_store;
	BLI_duplicatelist(&el_store_copy->verts, &el_store->verts);
	return el_store_copy;
}

void BM_edgeloop_free(BMEdgeLoopStore *el_store)
{
	BLI_freelistN(&el_store->verts);
	MEM_freeN(el_store);
}

bool BM_edgeloop_is_closed(BMEdgeLoopStore *el_store)
{
	return (el_store->flag & BM_EDGELOOP_IS_CLOSED) != 0;
}

ListBase *BM_edgeloop_verts_get(BMEdgeLoopStore *el_store)
{
	return &el_store->verts;
}

int BM_edgeloop_length_get(BMEdgeLoopStore *el_store)
{
	return el_store->len;
}

const float *BM_edgeloop_normal_get(struct BMEdgeLoopStore *el_store)
{
	return el_store->no;
}

const float *BM_edgeloop_center_get(struct BMEdgeLoopStore *el_store)
{
	return el_store->co;
}


#define NODE_AS_CO(n) ((BMVert *)((LinkData *)n)->data)->co

void BM_edgeloop_calc_center(BMesh *UNUSED(bm), BMEdgeLoopStore *el_store)
{
	LinkData *node_curr = el_store->verts.last;
	LinkData *node_prev = ((LinkData *)el_store->verts.last)->prev;
	LinkData *node_first = el_store->verts.first;
	LinkData *node_next = node_first;

	float const *v_prev = NODE_AS_CO(node_prev);
	float const *v_curr = NODE_AS_CO(node_curr);
	float const *v_next = NODE_AS_CO(node_next);

	float totw = 0.0f;
	float w_prev;

	zero_v3(el_store->co);

	w_prev = len_v3v3(v_prev, v_curr);
	do {
		const float w_curr = len_v3v3(v_curr, v_next);
		const float w = (w_curr + w_prev);
		madd_v3_v3fl(el_store->co, v_curr, w);
		totw += w;
		w_prev = w_curr;


		node_prev = node_curr;
		node_curr = node_next;
		node_next = node_next->next;

		if (node_next == NULL) {
			break;
		}
		v_prev = v_curr;
		v_curr = v_next;
		v_next = NODE_AS_CO(node_next);
	} while (1);

	if (totw != 0.0f)
		mul_v3_fl(el_store->co, 1.0f / (float) totw);

}

void BM_edgeloop_calc_normal(BMesh *UNUSED(bm), BMEdgeLoopStore *el_store)
{
	LinkData *node_curr = el_store->verts.first;
	float const *v_prev = NODE_AS_CO(el_store->verts.last);
	float const *v_curr = NODE_AS_CO(node_curr);

	/* Newell's Method */
	do {
		add_newell_cross_v3_v3v3(el_store->no, v_prev, v_curr);

		if ((node_curr = node_curr->next)) {
			v_prev = v_curr;
			v_curr = NODE_AS_CO(node_curr);
		}
		else {
			break;
		}
	} while (true);

	if (UNLIKELY(normalize_v3(el_store->no) == 0.0f)) {
		el_store->no[2] = 1.0f; /* other axis set to 0.0 */
	}
}


void BM_edgeloop_flip(BMesh *UNUSED(bm), BMEdgeLoopStore *el_store)
{
	negate_v3(el_store->no);
	BLI_reverselist(&el_store->verts);
}

void BM_edgeloop_expand(BMesh *UNUSED(bm), BMEdgeLoopStore *el_store, int el_store_len)
{
	/* first double until we are more then half as big */
	while ((el_store->len * 2) < el_store_len) {
		LinkData *node_curr = el_store->verts.first;
		while (node_curr) {
			LinkData *node_curr_copy = MEM_dupallocN(node_curr);
			BLI_insertlinkafter(&el_store->verts, node_curr, node_curr_copy);
			el_store->len++;
			node_curr = node_curr_copy->next;
		}
	}

	if (el_store->len < el_store_len) {
		const int step = max_ii(1, el_store->len / (el_store->len % el_store_len));
		LinkData *node_first = el_store->verts.first;
		LinkData *node_curr = node_first;

		do {
			LinkData *node_curr_init = node_curr;
			LinkData *node_curr_copy;
			int i = 0;
			LISTBASE_CIRCULAR_FORWARD_BEGIN (&el_store->verts, node_curr, node_curr_init) {
				if (i++ < step) {
					break;
				}
			}
			LISTBASE_CIRCULAR_FORWARD_END (&el_store->verts, node_curr, node_curr_init);

			node_curr_copy = MEM_dupallocN(node_curr);
			BLI_insertlinkafter(&el_store->verts, node_curr, node_curr_copy);
			el_store->len++;
			node_curr = node_curr_copy->next;
		} while (el_store->len < el_store_len);
	}

	BLI_assert(el_store->len == el_store_len);
}

bool BM_edgeloop_overlap_check(struct BMEdgeLoopStore *el_store_a, struct BMEdgeLoopStore *el_store_b)
{
	LinkData *node;

	/* init */
	for (node = el_store_a->verts.first; node; node = node->next) {
		BM_elem_flag_disable((BMVert *)node->data, BM_ELEM_INTERNAL_TAG);
	}
	for (node = el_store_b->verts.first; node; node = node->next) {
		BM_elem_flag_enable((BMVert *)node->data, BM_ELEM_INTERNAL_TAG);
	}

	/* check 'a' */
	for (node = el_store_a->verts.first; node; node = node->next) {
		if (BM_elem_flag_test((BMVert *)node->data, BM_ELEM_INTERNAL_TAG)) {
			return true;
		}
	}
	return false;
}
