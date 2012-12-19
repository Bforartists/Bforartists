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
 * Contributor(s): Joseph Eagar, Geoffrey Bantle, Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/bmesh/intern/bmesh_queries.c
 *  \ingroup bmesh
 *
 * This file contains functions for answering common
 * Topological and geometric queries about a mesh, such
 * as, "What is the angle between these two faces?" or,
 * "How many faces are incident upon this vertex?" Tool
 * authors should use the functions in this file instead
 * of inspecting the mesh structure directly.
 */

#include "MEM_guardedalloc.h"

#include "BLI_array.h"
#include "BLI_math.h"

#include "bmesh.h"
#include "intern/bmesh_private.h"

/**
 * Returns whether or not a given vertex is
 * is part of a given edge.
 */
int BM_vert_in_edge(BMEdge *e, BMVert *v)
{
	return bmesh_vert_in_edge(e, v);
}

/**
 * \brief Other Loop in Face Sharing an Edge
 *
 * Finds the other loop that shares \a v with \a e loop in \a f.
 * <pre>
 *     +----------+
 *     |          |
 *     |    f     |
 *     |          |
 *     +----------+ <-- return the face loop of this vertex.
 *     v --> e
 *     ^     ^ <------- These vert args define direction
 *                      in the face to check.
 *                      The faces loop direction is ignored.
 * </pre>
 */
BMLoop *BM_face_other_edge_loop(BMFace *f, BMEdge *e, BMVert *v)
{
	BMLoop *l_iter;
	BMLoop *l_first;

	/* we could loop around the face too, but turns out this uses a lot
	 * more iterations (approx double with quads, many more with 5+ ngons) */
	l_iter = l_first = e->l;

	do {
		if (l_iter->e == e && l_iter->f == f) {
			break;
		}
	} while ((l_iter = l_iter->radial_next) != l_first);
	
	return l_iter->v == v ? l_iter->prev : l_iter->next;
}

/**
 * \brief Other Loop in Face Sharing a Vertex
 *
 * Finds the other loop in a face.
 *
 * This function returns a loop in \a f that shares an edge with \a v
 * The direction is defined by \a v_prev, where the return value is
 * the loop of what would be 'v_next'
 * <pre>
 *     +----------+ <-- return the face loop of this vertex.
 *     |          |
 *     |    f     |
 *     |          |
 *     +----------+
 *     v_prev --> v
 *     ^^^^^^     ^ <-- These vert args define direction
 *                      in the face to check.
 *                      The faces loop direction is ignored.
 * </pre>
 *
 * \note \a v_prev and \a v _implicitly_ define an edge.
 */
BMLoop *BM_face_other_vert_loop(BMFace *f, BMVert *v_prev, BMVert *v)
{
	BMIter liter;
	BMLoop *l_iter;

	BLI_assert(BM_edge_exists(v_prev, v) != NULL);

	BM_ITER_ELEM (l_iter, &liter, v, BM_LOOPS_OF_VERT) {
		if (l_iter->f == f) {
			break;
		}
	}

	if (l_iter) {
		if (l_iter->prev->v == v_prev) {
			return l_iter->next;
		}
		else if (l_iter->next->v == v_prev) {
			return l_iter->prev;
		}
		else {
			/* invalid args */
			BLI_assert(0);
			return NULL;
		}
	}
	else {
		/* invalid args */
		BLI_assert(0);
		return NULL;
	}
}

/**
 * \brief Other Loop in Face Sharing a Vert
 *
 * Finds the other loop that shares \a v with \a e loop in \a f.
 * <pre>
 *     +----------+ <-- return the face loop of this vertex.
 *     |          |
 *     |          |
 *     |          |
 *     +----------+ <-- This vertex defines the direction.
 *           l    v
 *           ^ <------- This loop defines both the face to search
 *                      and the edge, in combination with 'v'
 *                      The faces loop direction is ignored.
 * </pre>
 */

BMLoop *BM_loop_other_vert_loop(BMLoop *l, BMVert *v)
{
#if 0 /* works but slow */
	return BM_face_other_vert_loop(l->f, BM_edge_other_vert(l->e, v), v);
#else
	BMEdge *e = l->e;
	BMVert *v_prev = BM_edge_other_vert(e, v);
	if (l->v == v) {
		if (l->prev->v == v_prev) {
			return l->next;
		}
		else {
			BLI_assert(l->next->v == v_prev);

			return l->prev;
		}
	}
	else {
		BLI_assert(l->v == v_prev);

		if (l->prev->v == v) {
			return l->prev->prev;
		}
		else {
			BLI_assert(l->next->v == v);
			return l->next->next;
		}
	}



#endif
}

/**
 * Get the first loop of a vert. Uses the same initialization code for the first loop of the
 * iterator API
 */
BMLoop *BM_vert_find_first_loop(BMVert *v)
{
	BMEdge *e;

	if (!v || !v->e)
		return NULL;

	e = bmesh_disk_faceedge_find_first(v->e, v);

	if (!e)
		return NULL;

	return bmesh_radial_faceloop_find_first(e->l, v);
}

/**
 * Returns TRUE if the vertex is used in a given face.
 */
int BM_vert_in_face(BMFace *f, BMVert *v)
{
	BMLoop *l_iter, *l_first;

#ifdef USE_BMESH_HOLES
	BMLoopList *lst;
	for (lst = f->loops.first; lst; lst = lst->next)
#endif
	{
#ifdef USE_BMESH_HOLES
		l_iter = l_first = lst->first;
#else
		l_iter = l_first = f->l_first;
#endif
		do {
			if (l_iter->v == v) {
				return TRUE;
			}
		} while ((l_iter = l_iter->next) != l_first);
	}

	return FALSE;
}

/**
 * Compares the number of vertices in an array
 * that appear in a given face
 */
int BM_verts_in_face(BMFace *f, BMVert **varr, int len)
{
	BMLoop *l_iter, *l_first;

#ifdef USE_BMESH_HOLES
	BMLoopList *lst;
#endif

	int i, count = 0;
	
	for (i = 0; i < len; i++) {
		BM_ELEM_API_FLAG_ENABLE(varr[i], _FLAG_OVERLAP);
	}

#ifdef USE_BMESH_HOLES
	for (lst = f->loops.first; lst; lst = lst->next)
#endif
	{

#ifdef USE_BMESH_HOLES
		l_iter = l_first = lst->first;
#else
		l_iter = l_first = f->l_first;
#endif

		do {
			if (BM_ELEM_API_FLAG_TEST(l_iter->v, _FLAG_OVERLAP)) {
				count++;
			}

		} while ((l_iter = l_iter->next) != l_first);
	}

	for (i = 0; i < len; i++) {
		BM_ELEM_API_FLAG_DISABLE(varr[i], _FLAG_OVERLAP);
	}

	return count;
}

/**
 * Returns whether or not a given edge is is part of a given face.
 */
int BM_edge_in_face(BMFace *f, BMEdge *e)
{
	BMLoop *l_iter;
	BMLoop *l_first;

	l_iter = l_first = BM_FACE_FIRST_LOOP(f);

	do {
		if (l_iter->e == e) {
			return TRUE;
		}
	} while ((l_iter = l_iter->next) != l_first);

	return FALSE;
}

/**
 * Returns whether or not a given edge is is part of a given loop.
 */
int BM_edge_in_loop(BMEdge *e, BMLoop *l)
{
	return (l->e == e || l->prev->e == e);
}

/**
 * Returns whether or not two vertices are in
 * a given edge
 */
int BM_verts_in_edge(BMVert *v1, BMVert *v2, BMEdge *e)
{
	return bmesh_verts_in_edge(v1, v2, e);
}

/**
 * Given a edge and one of its vertices, returns
 * the other vertex.
 */
BMVert *BM_edge_other_vert(BMEdge *e, BMVert *v)
{
	return bmesh_edge_other_vert_get(e, v);
}

/**
 * Given a edge and a loop (assumes the edge is manifold). returns
 * the other faces loop, sharing the same vertex.
 *
 * <pre>
 * +-------------------+
 * |                   |
 * |                   |
 * |l_other <-- return |
 * +-------------------+ <-- A manifold edge between 2 faces
 * |l    e  <-- edge   |
 * |^ <-------- loop   |
 * |                   |
 * +-------------------+
 * </pre>
 */
BMLoop *BM_edge_other_loop(BMEdge *e, BMLoop *l)
{
	BMLoop *l_other;

	// BLI_assert(BM_edge_is_manifold(e));  // TOO strict, just check if we have another radial face
	BLI_assert(e->l && e->l->radial_next != e->l);
	BLI_assert(BM_vert_in_edge(e, l->v));

	l_other = (l->e == e) ? l : l->prev;
	l_other = l_other->radial_next;
	BLI_assert(l_other->e == e);

	if (l_other->v == l->v) {
		/* pass */
	}
	else if (l_other->next->v == l->v) {
		l_other = l_other->next;
	}
	else {
		BLI_assert(0);
	}

	return l_other;
}

/**
 * Utility function to step around a fan of loops,
 * using an edge to mark the previous side.
 *
 * \note all edges must be manifold,
 * once a non manifold edge is hit, return NULL.
 *
 * <pre>
 *                ,.,-->|
 *            _,-'      |
 *          ,'          | (notice how 'e_step'
 *         /            |  and 'l' define the
 *        /             |  direction the arrow
 *       |     return   |  points).
 *       |     loop --> |
 * ---------------------+---------------------
 *         ^      l --> |
 *         |            |
 *  assign e_step       |
 *                      |
 *   begin e_step ----> |
 *                      |
 * </pre>
 */

BMLoop *BM_vert_step_fan_loop(BMLoop *l, BMEdge **e_step)
{
	BMEdge *e_prev = *e_step;
	BMEdge *e_next;
	if (l->e == e_prev) {
		e_next = l->prev->e;
	}
	else if (l->prev->e == e_prev) {
		e_next = l->e;
	}
	else {
		BLI_assert(0);
		return NULL;
	}

	if (BM_edge_is_manifold(e_next)) {
		return BM_edge_other_loop((*e_step = e_next), l);
	}
	else {
		return NULL;
	}
}



/**
 * The function takes a vertex at the center of a fan and returns the opposite edge in the fan.
 * All edges in the fan must be manifold, otherwise return NULL.
 *
 * \note This could (probably) be done more effieiently.
 */
BMEdge *BM_vert_other_disk_edge(BMVert *v, BMEdge *e_first)
{
	BMLoop *l_a;
	int tot = 0;
	int i;

	BLI_assert(BM_vert_in_edge(e_first, v));

	l_a = e_first->l;
	do {
		l_a = BM_loop_other_vert_loop(l_a, v);
		l_a = BM_vert_in_edge(l_a->e, v) ? l_a : l_a->prev;
		if (BM_edge_is_manifold(l_a->e)) {
			l_a = l_a->radial_next;
		}
		else {
			return NULL;
		}

		tot++;
	} while (l_a != e_first->l);

	/* we know the total, now loop half way */
	tot /= 2;
	i = 0;

	l_a = e_first->l;
	do {
		if (i == tot) {
			l_a = BM_vert_in_edge(l_a->e, v) ? l_a : l_a->prev;
			return l_a->e;
		}

		l_a = BM_loop_other_vert_loop(l_a, v);
		l_a = BM_vert_in_edge(l_a->e, v) ? l_a : l_a->prev;
		if (BM_edge_is_manifold(l_a->e)) {
			l_a = l_a->radial_next;
		}
		/* this wont have changed from the previous loop */


		i++;
	} while (l_a != e_first->l);

	return NULL;
}

/**
 * Returms edge length
 */
float BM_edge_calc_length(BMEdge *e)
{
	return len_v3v3(e->v1->co, e->v2->co);
}

/**
 * Utility function, since enough times we have an edge
 * and want to access 2 connected faces.
 *
 * \return TRUE when only 2 faces are found.
 */
int BM_edge_face_pair(BMEdge *e, BMFace **r_fa, BMFace **r_fb)
{
	BMLoop *la, *lb;

	if ((la = e->l) &&
	    (lb = la->radial_next) &&
	    (la != lb) &&
	    (lb->radial_next == la))
	{
		*r_fa = la->f;
		*r_fb = lb->f;
		return TRUE;
	}
	else {
		*r_fa = NULL;
		*r_fb = NULL;
		return FALSE;
	}
}

/**
 * Utility function, since enough times we have an edge
 * and want to access 2 connected loops.
 *
 * \return TRUE when only 2 faces are found.
 */
int BM_edge_loop_pair(BMEdge *e, BMLoop **r_la, BMLoop **r_lb)
{
	BMLoop *la, *lb;

	if ((la = e->l) &&
	    (lb = la->radial_next) &&
	    (la != lb) &&
	    (lb->radial_next == la))
	{
		*r_la = la;
		*r_lb = lb;
		return TRUE;
	}
	else {
		*r_la = NULL;
		*r_lb = NULL;
		return FALSE;
	}
}

/**
 *	Returns the number of edges around this vertex.
 */
int BM_vert_edge_count(BMVert *v)
{
	return bmesh_disk_count(v);
}

int BM_vert_edge_count_nonwire(BMVert *v)
{
	int count = 0;
	BMIter eiter;
	BMEdge *edge;
	BM_ITER_ELEM (edge, &eiter, v, BM_EDGES_OF_VERT) {
		if (edge->l) {
			count++;
		}
	}
	return count;
}
/**
 *	Returns the number of faces around this edge
 */
int BM_edge_face_count(BMEdge *e)
{
	int count = 0;

	if (e->l) {
		BMLoop *l_iter;
		BMLoop *l_first;

		l_iter = l_first = e->l;

		do {
			count++;
		} while ((l_iter = l_iter->radial_next) != l_first);
	}

	return count;
}

/**
 * Returns the number of faces around this vert
 * length matches #BM_LOOPS_OF_VERT iterator
 */
int BM_vert_face_count(BMVert *v)
{
	return bmesh_disk_facevert_count(v);
}

/**
 * Tests whether or not the vertex is part of a wire edge.
 * (ie: has no faces attached to it)
 */
int BM_vert_is_wire(BMVert *v)
{
	if (v->e) {
		BMEdge *e_first, *e_iter;

		e_first = e_iter = v->e;
		do {
			if (e_iter->l) {
				return FALSE;
			}
		} while ((e_iter = bmesh_disk_edge_next(e_iter, v)) != e_first);

		return TRUE;
	}
	else {
		return FALSE;
	}
}

/**
 * Tests whether or not the edge is part of a wire.
 * (ie: has no faces attached to it)
 */
int BM_edge_is_wire(BMEdge *e)
{
	return (e->l) ? FALSE : TRUE;
}

/**
 * A vertex is non-manifold if it meets the following conditions:
 * 1: Loose - (has no edges/faces incident upon it).
 * 2: Joins two distinct regions - (two pyramids joined at the tip).
 * 3: Is part of a an edge with more than 2 faces.
 * 4: Is part of a wire edge.
 */
int BM_vert_is_manifold(BMVert *v)
{
	BMEdge *e, *oe;
	BMLoop *l;
	int len, count, flag;

	if (v->e == NULL) {
		/* loose vert */
		return FALSE;
	}

	/* count edges while looking for non-manifold edges */
	len = 0;
	oe = e = v->e;
	do {
		/* loose edge or edge shared by more than two faces,
		 * edges with 1 face user are OK, otherwise we could
		 * use BM_edge_is_manifold() here */
		if (e->l == NULL || bmesh_radial_length(e->l) > 2) {
			return FALSE;
		}
		len++;
	} while ((e = bmesh_disk_edge_next(e, v)) != oe);

	count = 1;
	flag = 1;
	e = NULL;
	oe = v->e;
	l = oe->l;
	while (e != oe) {
		l = (l->v == v) ? l->prev : l->next;
		e = l->e;
		count++; /* count the edges */

		if (flag && l->radial_next == l) {
			/* we've hit the edge of an open mesh, reset once */
			flag = 0;
			count = 1;
			oe = e;
			e = NULL;
			l = oe->l;
		}
		else if (l->radial_next == l) {
			/* break the loop */
			e = oe;
		}
		else {
			l = l->radial_next;
		}
	}

	if (count < len) {
		/* vert shared by multiple regions */
		return FALSE;
	}

	return TRUE;
}

/**
 * Tests whether or not this edge is manifold.
 * A manifold edge has exactly 2 faces attached to it.
 */

#if 1 /* fast path for checking manifold */
int BM_edge_is_manifold(BMEdge *e)
{
	const BMLoop *l = e->l;
	return (l && (l->radial_next != l) &&             /* not 0 or 1 face users */
	             (l->radial_next->radial_next == l)); /* 2 face users */
}
#else
int BM_edge_is_manifold(BMEdge *e)
{
	int count = BM_edge_face_count(e);
	if (count == 2) {
		return TRUE;
	}
	else {
		return FALSE;
	}
}
#endif

/**
 * Tests whether or not an edge is on the boundary
 * of a shell (has one face associated with it)
 */

#if 1 /* fast path for checking boundary */
int BM_edge_is_boundary(BMEdge *e)
{
	const BMLoop *l = e->l;
	return (l && (l->radial_next == l));
}
#else
int BM_edge_is_boundary(BMEdge *e)
{
	int count = BM_edge_face_count(e);
	if (count == 1) {
		return TRUE;
	}
	else {
		return FALSE;
	}
}
#endif

/**
 * Returns the number of faces that are adjacent to both f1 and f2,
 * \note Could be sped up a bit by not using iterators and by tagging
 * faces on either side, then count the tags rather then searching.
 */
int BM_face_share_face_count(BMFace *f1, BMFace *f2)
{
	BMIter iter1, iter2;
	BMEdge *e;
	BMFace *f;
	int count = 0;

	BM_ITER_ELEM (e, &iter1, f1, BM_EDGES_OF_FACE) {
		BM_ITER_ELEM (f, &iter2, e, BM_FACES_OF_EDGE) {
			if (f != f1 && f != f2 && BM_face_share_edge_check(f, f2))
				count++;
		}
	}

	return count;
}

/**
 * same as #BM_face_share_face_count but returns a bool
 */
int BM_face_share_face_check(BMFace *f1, BMFace *f2)
{
	BMIter iter1, iter2;
	BMEdge *e;
	BMFace *f;

	BM_ITER_ELEM (e, &iter1, f1, BM_EDGES_OF_FACE) {
		BM_ITER_ELEM (f, &iter2, e, BM_FACES_OF_EDGE) {
			if (f != f1 && f != f2 && BM_face_share_edge_check(f, f2))
				return TRUE;
		}
	}

	return FALSE;
}

/**
 *  Counts the number of edges two faces share (if any)
 */
int BM_face_share_edge_count(BMFace *f1, BMFace *f2)
{
	BMLoop *l_iter;
	BMLoop *l_first;
	int count = 0;
	
	l_iter = l_first = BM_FACE_FIRST_LOOP(f1);
	do {
		if (bmesh_radial_face_find(l_iter->e, f2)) {
			count++;
		}
	} while ((l_iter = l_iter->next) != l_first);

	return count;
}

/**
 *  Returns TRUE if the faces share an edge
 */
int BM_face_share_edge_check(BMFace *f1, BMFace *f2)
{
	BMLoop *l_iter;
	BMLoop *l_first;

	l_iter = l_first = BM_FACE_FIRST_LOOP(f1);
	do {
		if (bmesh_radial_face_find(l_iter->e, f2)) {
			return TRUE;
		}
	} while ((l_iter = l_iter->next) != l_first);

	return FALSE;
}

/**
 *	Test if e1 shares any faces with e2
 */
int BM_edge_share_face_check(BMEdge *e1, BMEdge *e2)
{
	BMLoop *l;
	BMFace *f;

	if (e1->l && e2->l) {
		l = e1->l;
		do {
			f = l->f;
			if (bmesh_radial_face_find(e2, f)) {
				return TRUE;
			}
			l = l->radial_next;
		} while (l != e1->l);
	}
	return FALSE;
}

/**
 *	Test if e1 shares any quad faces with e2
 */
int BM_edge_share_quad_check(BMEdge *e1, BMEdge *e2)
{
	BMLoop *l;
	BMFace *f;

	if (e1->l && e2->l) {
		l = e1->l;
		do {
			f = l->f;
			if (f->len == 4) {
				if (bmesh_radial_face_find(e2, f)) {
					return TRUE;
				}
			}
			l = l->radial_next;
		} while (l != e1->l);
	}
	return FALSE;
}

/**
 *	Tests to see if e1 shares a vertex with e2
 */
int BM_edge_share_vert_check(BMEdge *e1, BMEdge *e2)
{
	return (e1->v1 == e2->v1 ||
	        e1->v1 == e2->v2 ||
	        e1->v2 == e2->v1 ||
	        e1->v2 == e2->v2);
}

/**
 *	Return the shared vertex between the two edges or NULL
 */
BMVert *BM_edge_share_vert(BMEdge *e1, BMEdge *e2)
{
	if (BM_vert_in_edge(e2, e1->v1)) {
		return e1->v1;
	}
	else if (BM_vert_in_edge(e2, e1->v2)) {
		return e1->v2;
	}
	else {
		return NULL;
	}
}

/**
 * \brief Return the Loop Shared by Face and Vertex
 *
 * Finds the loop used which uses \a v in face loop \a l
 *
 * \note currently this just uses simple loop in future may be sped up
 * using radial vars
 */
BMLoop *BM_face_vert_share_loop(BMFace *f, BMVert *v)
{
	BMLoop *l_first;
	BMLoop *l_iter;

	l_iter = l_first = BM_FACE_FIRST_LOOP(f);
	do {
		if (l_iter->v == v) {
			return l_iter;
		}
	} while ((l_iter = l_iter->next) != l_first);

	return NULL;
}

/**
 * \brief Return the Loop Shared by Face and Edge
 *
 * Finds the loop used which uses \a e in face loop \a l
 *
 * \note currently this just uses simple loop in future may be sped up
 * using radial vars
 */
BMLoop *BM_face_edge_share_loop(BMFace *f, BMEdge *e)
{
	BMLoop *l_first;
	BMLoop *l_iter;

	l_iter = l_first = e->l;
	do {
		if (l_iter->f == f) {
			return l_iter;
		}
	} while ((l_iter = l_iter->radial_next) != l_first);

	return NULL;
}

/**
 * Returns the verts of an edge as used in a face
 * if used in a face at all, otherwise just assign as used in the edge.
 *
 * Useful to get a deterministic winding order when calling
 * BM_face_create_ngon() on an arbitrary array of verts,
 * though be sure to pick an edge which has a face.
 *
 * \note This is in fact quite a simple check, mainly include this function so the intent is more obvious.
 * We know these 2 verts will _always_ make up the loops edge
 */
void BM_edge_ordered_verts_ex(BMEdge *edge, BMVert **r_v1, BMVert **r_v2,
                              BMLoop *edge_loop)
{
	BLI_assert(edge_loop->e == edge);
	(void)edge; /* quiet warning in release build */
	*r_v1 = edge_loop->v;
	*r_v2 = edge_loop->next->v;
}

void BM_edge_ordered_verts(BMEdge *edge, BMVert **r_v1, BMVert **r_v2)
{
	BM_edge_ordered_verts_ex(edge, r_v1, r_v2, edge->l);
}

/**
 * Calculates the angle between the previous and next loops
 * (angle at this loops face corner).
 *
 * \return angle in radians
 */
float BM_loop_calc_face_angle(BMLoop *l)
{
	return angle_v3v3v3(l->prev->v->co,
	                    l->v->co,
	                    l->next->v->co);
}

/**
 * \brief BM_loop_calc_face_normal
 *
 * Calculate the normal at this loop corner or fallback to the face normal on straight lines.
 *
 * \param l The loop to calculate the normal at
 * \param r_normal Resulting normal
 */
void BM_loop_calc_face_normal(BMLoop *l, float r_normal[3])
{
	if (normal_tri_v3(r_normal,
	                  l->prev->v->co,
	                  l->v->co,
	                  l->next->v->co) != 0.0f)
	{
		return;
	}
	else {
		copy_v3_v3(r_normal, l->f->no);
	}
}

/**
 * \brief BM_loop_calc_face_tangent
 *
 * Calculate the tangent at this loop corner or fallback to the face normal on straight lines.
 * This vector always points inward into the face.
 *
 * \param l The loop to calculate the tangent at
 * \param r_tangent Resulting tangent
 */
void BM_loop_calc_face_tangent(BMLoop *l, float r_tangent[3])
{
	float v_prev[3];
	float v_next[3];

	sub_v3_v3v3(v_prev, l->prev->v->co, l->v->co);
	sub_v3_v3v3(v_next, l->v->co, l->next->v->co);

	normalize_v3(v_prev);
	normalize_v3(v_next);

	if (compare_v3v3(v_prev, v_next, FLT_EPSILON) == FALSE) {
		float dir[3];
		float nor[3]; /* for this purpose doesn't need to be normalized */
		add_v3_v3v3(dir, v_prev, v_next);
		cross_v3_v3v3(nor, v_prev, v_next);
		cross_v3_v3v3(r_tangent, dir, nor);
	}
	else {
		/* prev/next are the same - compare with face normal since we don't have one */
		cross_v3_v3v3(r_tangent, v_next, l->f->no);
	}

	normalize_v3(r_tangent);
}

/**
 * \brief BMESH EDGE/FACE ANGLE
 *
 *  Calculates the angle between two faces.
 *  Assumes the face normals are correct.
 *
 * \return angle in radians
 */
float BM_edge_calc_face_angle(BMEdge *e)
{
	if (BM_edge_is_manifold(e)) {
		BMLoop *l1 = e->l;
		BMLoop *l2 = e->l->radial_next;
		return angle_normalized_v3v3(l1->f->no, l2->f->no);
	}
	else {
		return DEG2RADF(90.0f);
	}
}

/**
 * \brief BMESH EDGE/FACE TANGENT
 *
 * Calculate the tangent at this loop corner or fallback to the face normal on straight lines.
 * This vector always points inward into the face.
 *
 * \brief BM_edge_calc_face_tangent
 * \param e
 * \param e_loop The loop to calculate the tangent at,
 * used to get the face and winding direction.
 * \param r_tangent The loop corner tangent to set
 */

void BM_edge_calc_face_tangent(BMEdge *e, BMLoop *e_loop, float r_tangent[3])
{
	float tvec[3];
	BMVert *v1, *v2;
	BM_edge_ordered_verts_ex(e, &v1, &v2, e_loop);

	sub_v3_v3v3(tvec, v1->co, v2->co); /* use for temp storage */
	/* note, we could average the tangents of both loops,
	 * for non flat ngons it will give a better direction */
	cross_v3_v3v3(r_tangent, tvec, e_loop->f->no);
	normalize_v3(r_tangent);
}

/**
 * \brief BMESH VERT/EDGE ANGLE
 *
 * Calculates the angle a verts 2 edges.
 *
 * \returns the angle in radians
 */
float BM_vert_calc_edge_angle(BMVert *v)
{
	BMEdge *e1, *e2;

	/* saves BM_vert_edge_count(v) and and edge iterator,
	 * get the edges and count them both at once */

	if ((e1 = v->e) &&
	    (e2 =  bmesh_disk_edge_next(e1, v)) &&
	    /* make sure we come full circle and only have 2 connected edges */
	    (e1 == bmesh_disk_edge_next(e2, v)))
	{
		BMVert *v1 = BM_edge_other_vert(e1, v);
		BMVert *v2 = BM_edge_other_vert(e2, v);

		return (float)M_PI - angle_v3v3v3(v1->co, v->co, v2->co);
	}
	else {
		return DEG2RADF(90.0f);
	}
}

/**
 * \note this isn't optimal to run on an array of verts,
 * see 'solidify_add_thickness' for a function which runs on an array.
 */
float BM_vert_calc_shell_factor(BMVert *v)
{
	BMIter iter;
	BMLoop *l;
	float accum_shell = 0.0f;
	float accum_angle = 0.0f;

	BM_ITER_ELEM (l, &iter, v, BM_LOOPS_OF_VERT) {
		const float face_angle = BM_loop_calc_face_angle(l);
		accum_shell += shell_angle_to_dist(angle_normalized_v3v3(v->no, l->f->no)) * face_angle;
		accum_angle += face_angle;
	}

	if (accum_angle != 0.0f) {
		return accum_shell / accum_angle;
	}
	else {
		return 1.0f;
	}
}
/* alternate version of #BM_vert_calc_shell_factor which only
 * uses 'hflag' faces, but falls back to all if none found. */
float BM_vert_calc_shell_factor_ex(BMVert *v, const char hflag)
{
	BMIter iter;
	BMLoop *l;
	float accum_shell = 0.0f;
	float accum_angle = 0.0f;
	int tot_sel = 0, tot = 0;

	BM_ITER_ELEM (l, &iter, v, BM_LOOPS_OF_VERT) {
		if (BM_elem_flag_test(l->f, hflag)) {  /* <-- main difference to BM_vert_calc_shell_factor! */
			const float face_angle = BM_loop_calc_face_angle(l);
			accum_shell += shell_angle_to_dist(angle_normalized_v3v3(v->no, l->f->no)) * face_angle;
			accum_angle += face_angle;
			tot_sel++;
		}
		tot++;
	}

	if (accum_angle != 0.0f) {
		return accum_shell / accum_angle;
	}
	else {
		/* other main difference from BM_vert_calc_shell_factor! */
		if (tot != 0 && tot_sel == 0) {
			/* none selected, so use all */
			return BM_vert_calc_shell_factor(v);
		}
		else {
			return 1.0f;
		}
	}
}

/**
 * \note quite an obscure function.
 * used in bmesh operators that have a relative scale options,
 */
float BM_vert_calc_mean_tagged_edge_length(BMVert *v)
{
	BMIter iter;
	BMEdge *e;
	int tot;
	float length = 0.0f;

	BM_ITER_ELEM_INDEX (e, &iter, v, BM_EDGES_OF_VERT, tot) {
		BMVert *v_other = BM_edge_other_vert(e, v);
		if (BM_elem_flag_test(v_other, BM_ELEM_TAG)) {
			length += BM_edge_calc_length(e);
		}
	}

	if (tot) {
		return length / (float)tot;
	}
	else {
		return 0.0f;
	}
}


/**
 * Returns the loop of the shortest edge in f.
 */
BMLoop *BM_face_find_shortest_loop(BMFace *f)
{
	BMLoop *shortest_loop = NULL;
	float shortest_len = FLT_MAX;

	BMLoop *l_iter;
	BMLoop *l_first;

	l_iter = l_first = BM_FACE_FIRST_LOOP(f);

	do {
		const float len = len_squared_v3v3(l_iter->v->co, l_iter->next->v->co);
		if (len <= shortest_len) {
			shortest_loop = l_iter;
			shortest_len = len;
		}
	} while ((l_iter = l_iter->next) != l_first);

	return shortest_loop;
}

/**
 * Returns the loop of the longest edge in f.
 */
BMLoop *BM_face_find_longest_loop(BMFace *f)
{
	BMLoop *longest_loop = NULL;
	float longest_len = 0.0f;

	BMLoop *l_iter;
	BMLoop *l_first;

	l_iter = l_first = BM_FACE_FIRST_LOOP(f);

	do {
		const float len = len_squared_v3v3(l_iter->v->co, l_iter->next->v->co);
		if (len >= longest_len) {
			longest_loop = l_iter;
			longest_len = len;
		}
	} while ((l_iter = l_iter->next) != l_first);

	return longest_loop;
}

/**
 * Returns the edge existing between v1 and v2, or NULL if there isn't one.
 *
 * \note multiple edges may exist between any two vertices, and therefore
 * this function only returns the first one found.
 */
BMEdge *BM_edge_exists(BMVert *v1, BMVert *v2)
{
	BMIter iter;
	BMEdge *e;

	BM_ITER_ELEM (e, &iter, v1, BM_EDGES_OF_VERT) {
		if (e->v1 == v2 || e->v2 == v2)
			return e;
	}

	return NULL;
}

/**
 * Returns an edge sharing the same vertices as this one.
 * This isn't an invalid state but tools should clean up these cases before
 * returning the mesh to the user.
 */
BMEdge *BM_edge_find_double(BMEdge *e)
{
	BMVert *v       = e->v1;
	BMVert *v_other = e->v2;

	BMEdge *e_iter;

	e_iter = e;
	while ((e_iter = bmesh_disk_edge_next(e_iter, v)) != e) {
		if (UNLIKELY(BM_vert_in_edge(e_iter, v_other))) {
			return e_iter;
		}
	}

	return NULL;
}

/**
 * Given a set of vertices \a varr, find out if
 * all those vertices overlap an existing face.
 *
 * \note Making a face here is valid but in some cases you wont want to
 * make a face thats part of another.
 *
 * \returns TRUE for overlap
 *
 */
int BM_face_exists_overlap(BMVert **varr, int len, BMFace **r_overlapface)
{
	BMIter viter;
	BMFace *f;
	int i, amount;

	for (i = 0; i < len; i++) {
		BM_ITER_ELEM (f, &viter, varr[i], BM_FACES_OF_VERT) {
			amount = BM_verts_in_face(f, varr, len);
			if (amount >= len) {
				if (r_overlapface) {
					*r_overlapface = f;
				}
				return TRUE;
			}
		}
	}

	if (r_overlapface) {
		*r_overlapface = NULL;
	}

	return FALSE;
}

/**
 * Given a set of vertices (varr), find out if
 * there is a face with exactly those vertices
 * (and only those vertices).
 */
int BM_face_exists(BMVert **varr, int len, BMFace **r_existface)
{
	BMIter viter;
	BMFace *f;
	int i, amount;

	for (i = 0; i < len; i++) {
		BM_ITER_ELEM (f, &viter, varr[i], BM_FACES_OF_VERT) {
			amount = BM_verts_in_face(f, varr, len);
			if (amount == len && amount == f->len) {
				if (r_existface) {
					*r_existface = f;
				}
				return TRUE;
			}
		}
	}

	if (r_existface) {
		*r_existface = NULL;
	}
	return FALSE;
}


/**
 * Given a set of vertices and edges (\a varr, \a earr), find out if
 * all those vertices are filled in by existing faces that _only_ use those vertices.
 *
 * This is for use in cases where creating a face is possible but would result in
 * many overlapping faces.
 *
 * An example of how this is used: when 2 tri's are selected that share an edge,
 * pressing Fkey would make a new overlapping quad (without a check like this)
 *
 * \a earr and \a varr can be in any order, however they _must_ form a closed loop.
 */
int BM_face_exists_multi(BMVert **varr, BMEdge **earr, int len)
{
	BMFace *f;
	BMEdge *e;
	BMVert *v;
	int ok;
	int tot_tag;

	BMIter fiter;
	BMIter viter;

	int i;

	for (i = 0; i < len; i++) {
		/* save some time by looping over edge faces rather then vert faces
		 * will still loop over some faces twice but not as many */
		BM_ITER_ELEM (f, &fiter, earr[i], BM_FACES_OF_EDGE) {
			BM_elem_flag_disable(f, BM_ELEM_INTERNAL_TAG);
			BM_ITER_ELEM (v, &viter, f, BM_VERTS_OF_FACE) {
				BM_elem_flag_disable(v, BM_ELEM_INTERNAL_TAG);
			}
		}

		/* clear all edge tags */
		BM_ITER_ELEM (e, &fiter, varr[i], BM_EDGES_OF_VERT) {
			BM_elem_flag_disable(e, BM_ELEM_INTERNAL_TAG);
		}
	}

	/* now tag all verts and edges in the boundary array as true so
	 * we can know if a face-vert is from our array */
	for (i = 0; i < len; i++) {
		BM_elem_flag_enable(varr[i], BM_ELEM_INTERNAL_TAG);
		BM_elem_flag_enable(earr[i], BM_ELEM_INTERNAL_TAG);
	}


	/* so! boundary is tagged, everything else cleared */


	/* 1) tag all faces connected to edges - if all their verts are boundary */
	tot_tag = 0;
	for (i = 0; i < len; i++) {
		BM_ITER_ELEM (f, &fiter, earr[i], BM_FACES_OF_EDGE) {
			if (!BM_elem_flag_test(f, BM_ELEM_INTERNAL_TAG)) {
				ok = TRUE;
				BM_ITER_ELEM (v, &viter, f, BM_VERTS_OF_FACE) {
					if (!BM_elem_flag_test(v, BM_ELEM_INTERNAL_TAG)) {
						ok = FALSE;
						break;
					}
				}

				if (ok) {
					/* we only use boundary verts */
					BM_elem_flag_enable(f, BM_ELEM_INTERNAL_TAG);
					tot_tag++;
				}
			}
			else {
				/* we already found! */
			}
		}
	}

	if (tot_tag == 0) {
		/* no faces use only boundary verts, quit early */
		return FALSE;
	}

	/* 2) loop over non-boundary edges that use boundary verts,
	 *    check each have 2 tagges faces connected (faces that only use 'varr' verts) */
	ok = TRUE;
	for (i = 0; i < len; i++) {
		BM_ITER_ELEM (e, &fiter, varr[i], BM_EDGES_OF_VERT) {

			if (/* non-boundary edge */
			    BM_elem_flag_test(e, BM_ELEM_INTERNAL_TAG) == FALSE &&
			    /* ...using boundary verts */
			    BM_elem_flag_test(e->v1, BM_ELEM_INTERNAL_TAG) == TRUE &&
			    BM_elem_flag_test(e->v2, BM_ELEM_INTERNAL_TAG) == TRUE)
			{
				int tot_face_tag = 0;
				BM_ITER_ELEM (f, &fiter, e, BM_FACES_OF_EDGE) {
					if (BM_elem_flag_test(f, BM_ELEM_INTERNAL_TAG)) {
						tot_face_tag++;
					}
				}

				if (tot_face_tag != 2) {
					ok = FALSE;
					break;
				}

			}
		}

		if (ok == FALSE) {
			break;
		}
	}

	return ok;
}

/* same as 'BM_face_exists_multi' but built vert array from edges */
int BM_face_exists_multi_edge(BMEdge **earr, int len)
{
	BMVert **varr = BLI_array_alloca(varr, len);

	int ok;
	int i, i_next;

	/* first check if verts have edges, if not we can bail out early */
	ok = TRUE;
	for (i = len - 1, i_next = 0; i_next < len; (i = i_next++)) {
		if (!(varr[i] = BM_edge_share_vert(earr[i], earr[i_next]))) {
			ok = FALSE;
			break;
		}
	}

	if (ok == FALSE) {
		BMESH_ASSERT(0);
		return FALSE;
	}

	ok = BM_face_exists_multi(varr, earr, len);

	return ok;
}

/* convenience functions for checking flags */
int BM_edge_is_any_vert_flag_test(BMEdge *e, const char hflag)
{
	return (BM_elem_flag_test(e->v1, hflag) ||
	        BM_elem_flag_test(e->v2, hflag));
}

int BM_face_is_any_vert_flag_test(BMFace *f, const char hflag)
{
	BMLoop *l_iter;
	BMLoop *l_first;

	l_iter = l_first = BM_FACE_FIRST_LOOP(f);
	do {
		if (BM_elem_flag_test(l_iter->v, hflag)) {
			return TRUE;
		}
	} while ((l_iter = l_iter->next) != l_first);
	return FALSE;
}

int BM_face_is_any_edge_flag_test(BMFace *f, const char hflag)
{
	BMLoop *l_iter;
	BMLoop *l_first;

	l_iter = l_first = BM_FACE_FIRST_LOOP(f);
	do {
		if (BM_elem_flag_test(l_iter->e, hflag)) {
			return TRUE;
		}
	} while ((l_iter = l_iter->next) != l_first);
	return FALSE;
}
