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

/** \file blender/bmesh/intern/bmesh_iterators.c
 *  \ingroup bmesh
 *
 * Functions to abstract looping over bmesh data structures.
 *
 * See: bmesh_iterators_inlin.c too, some functions are here for speed reasons.
 */

#include <string.h>

#include "bmesh.h"
#include "bmesh_private.h"

/*
 * note, we have BM_Vert_AtIndex/BM_Edge_AtIndex/BM_Face_AtIndex for arrays
 */
void *BMIter_AtIndex(struct BMesh *bm, const char itype, void *data, int index)
{
	BMIter iter;
	void *val;
	int i;

	/* sanity check */
	if (index < 0) {
		return NULL;
	}

	val = BMIter_New(&iter, bm, itype, data);

	i = 0;
	while (i < index) {
		val = BMIter_Step(&iter);
		i++;
	}

	return val;
}


/*
 * ITERATOR AS ARRAY
 *
 * Sometimes its convenient to get the iterator as an array
 * to avoid multiple calls to BMIter_AtIndex.
 */

int BMIter_AsArray(struct BMesh *bm, const char type, void *data, void **array, const int len)
{
	int i = 0;

	/* sanity check */
	if (len > 0) {

		BMIter iter;
		void *val;

		BM_ITER(val, &iter, bm, type, data) {
			array[i] = val;
			i++;
			if (i == len) {
				return len;
			}
		}
	}

	return i;
}


/*
 * INIT ITERATOR
 *
 * Clears the internal state of an iterator
 * For begin() callbacks.
 *
 */

static void init_iterator(BMIter *iter)
{
	iter->firstvert = iter->nextvert = NULL;
	iter->firstedge = iter->nextedge = NULL;
	iter->firstloop = iter->nextloop = NULL;
	iter->firstpoly = iter->nextpoly = NULL;
	iter->ldata = NULL;
}

/*
 * Notes on iterator implementation:
 *
 * Iterators keep track of the next element
 * in a sequence. When a step() callback is
 * invoked the current value of 'next' is stored
 * to be returned later and the next variable is
 * incremented.
 *
 * When the end of a sequence is
 * reached, next should always equal NULL
 *
 * The 'bmiter__' prefix is used because these are used in
 * bmesh_iterators_inine.c but should otherwise be seen as
 * private.
 */

/*
 * VERT OF MESH CALLBACKS
 *
 */

void bmiter__vert_of_mesh_begin(BMIter *iter)
{
	BLI_mempool_iternew(iter->bm->vpool, &iter->pooliter);
}

void  *bmiter__vert_of_mesh_step(BMIter *iter)
{
	return BLI_mempool_iterstep(&iter->pooliter);

}

void  bmiter__edge_of_mesh_begin(BMIter *iter)
{
	BLI_mempool_iternew(iter->bm->epool, &iter->pooliter);
}

void  *bmiter__edge_of_mesh_step(BMIter *iter)
{
	return BLI_mempool_iterstep(&iter->pooliter);

}

void  bmiter__face_of_mesh_begin(BMIter *iter)
{
	BLI_mempool_iternew(iter->bm->fpool, &iter->pooliter);
}

void  *bmiter__face_of_mesh_step(BMIter *iter)
{
	return BLI_mempool_iterstep(&iter->pooliter);

}

/*
 * EDGE OF VERT CALLBACKS
 *
 */

void  bmiter__edge_of_vert_begin(BMIter *iter)
{
	init_iterator(iter);
	if (iter->vdata->e) {
		iter->firstedge = iter->vdata->e;
		iter->nextedge = iter->vdata->e;
	}
}

void  *bmiter__edge_of_vert_step(BMIter *iter)
{
	BMEdge *current = iter->nextedge;

	if (iter->nextedge)
		iter->nextedge = bmesh_disk_nextedge(iter->nextedge, iter->vdata);
	
	if (iter->nextedge == iter->firstedge) iter->nextedge = NULL;

	return current;
}

/*
 * FACE OF VERT CALLBACKS
 *
 */

void  bmiter__face_of_vert_begin(BMIter *iter)
{
	init_iterator(iter);
	iter->count = 0;
	if (iter->vdata->e)
		iter->count = bmesh_disk_count_facevert(iter->vdata);
	if (iter->count) {
		iter->firstedge = bmesh_disk_find_first_faceedge(iter->vdata->e, iter->vdata);
		iter->nextedge = iter->firstedge;
		iter->firstloop = bmesh_radial_find_first_facevert(iter->firstedge->l, iter->vdata);
		iter->nextloop = iter->firstloop;
	}
}
void  *bmiter__face_of_vert_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;

	if (iter->count && iter->nextloop) {
		iter->count--;
		iter->nextloop = bmesh_radial_find_next_facevert(iter->nextloop, iter->vdata);
		if (iter->nextloop == iter->firstloop) {
			iter->nextedge = bmesh_disk_find_next_faceedge(iter->nextedge, iter->vdata);
			iter->firstloop = bmesh_radial_find_first_facevert(iter->nextedge->l, iter->vdata);
			iter->nextloop = iter->firstloop;
		}
	}
	
	if (!iter->count) iter->nextloop = NULL;

	return current ? current->f : NULL;
}


/*
 * LOOP OF VERT CALLBACKS
 *
 */

void  bmiter__loop_of_vert_begin(BMIter *iter)
{
	init_iterator(iter);
	iter->count = 0;
	if (iter->vdata->e)
		iter->count = bmesh_disk_count_facevert(iter->vdata);
	if (iter->count) {
		iter->firstedge = bmesh_disk_find_first_faceedge(iter->vdata->e, iter->vdata);
		iter->nextedge = iter->firstedge;
		iter->firstloop = bmesh_radial_find_first_facevert(iter->firstedge->l, iter->vdata);
		iter->nextloop = iter->firstloop;
	}
}
void  *bmiter__loop_of_vert_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;

	if (iter->count) {
		iter->count--;
		iter->nextloop = bmesh_radial_find_next_facevert(iter->nextloop, iter->vdata);
		if (iter->nextloop == iter->firstloop) {
			iter->nextedge = bmesh_disk_find_next_faceedge(iter->nextedge, iter->vdata);
			iter->firstloop = bmesh_radial_find_first_facevert(iter->nextedge->l, iter->vdata);
			iter->nextloop = iter->firstloop;
		}
	}
	
	if (!iter->count) iter->nextloop = NULL;

	
	if (current) return current;
	return NULL;
}


void  bmiter__loops_of_edge_begin(BMIter *iter)
{
	BMLoop *l;

	l = iter->edata->l;

	/* note sure why this sets ldata ... */
	init_iterator(iter);
	
	iter->firstloop = iter->nextloop = l;
}

void  *bmiter__loops_of_edge_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;

	if (iter->nextloop)
		iter->nextloop = bmesh_radial_nextloop(iter->nextloop);

	if (iter->nextloop == iter->firstloop)
		iter->nextloop = NULL;

	if (current) return current;
	return NULL;
}

void  bmiter__loops_of_loop_begin(BMIter *iter)
{
	BMLoop *l;

	l = iter->ldata;

	/* note sure why this sets ldata ... */
	init_iterator(iter);

	iter->firstloop = l;
	iter->nextloop = bmesh_radial_nextloop(iter->firstloop);
	
	if (iter->nextloop == iter->firstloop)
		iter->nextloop = NULL;
}

void  *bmiter__loops_of_loop_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;
	
	if (iter->nextloop) iter->nextloop = bmesh_radial_nextloop(iter->nextloop);

	if (iter->nextloop == iter->firstloop) iter->nextloop = NULL;
	if (current) return current;
	return NULL;
}

/*
 * FACE OF EDGE CALLBACKS
 *
 */

void  bmiter__face_of_edge_begin(BMIter *iter)
{
	init_iterator(iter);
	
	if (iter->edata->l) {
		iter->firstloop = iter->edata->l;
		iter->nextloop = iter->edata->l;
	}
}

void  *bmiter__face_of_edge_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;

	if (iter->nextloop) iter->nextloop = bmesh_radial_nextloop(iter->nextloop);

	if (iter->nextloop == iter->firstloop) iter->nextloop = NULL;

	return current ? current->f : NULL;
}

/*
 * VERT OF FACE CALLBACKS
 *
 */

void  bmiter__vert_of_face_begin(BMIter *iter)
{
	init_iterator(iter);
	iter->firstloop = iter->nextloop = ((BMLoopList *)iter->pdata->loops.first)->first;
}

void  *bmiter__vert_of_face_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;

	if (iter->nextloop) iter->nextloop = iter->nextloop->next;
	if (iter->nextloop == iter->firstloop) iter->nextloop = NULL;

	return current ? current->v : NULL;
}

/*
 * EDGE OF FACE CALLBACKS
 *
 */

void  bmiter__edge_of_face_begin(BMIter *iter)
{
	init_iterator(iter);
	iter->firstloop = iter->nextloop = ((BMLoopList *)iter->pdata->loops.first)->first;
}

void  *bmiter__edge_of_face_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;

	if (iter->nextloop) iter->nextloop = iter->nextloop->next;
	if (iter->nextloop == iter->firstloop) iter->nextloop = NULL;
	
	return current ? current->e : NULL;
}

/*
 * LOOP OF FACE CALLBACKS
 *
 */

void  bmiter__loop_of_face_begin(BMIter *iter)
{
	init_iterator(iter);
	iter->firstloop = iter->nextloop = bm_firstfaceloop(iter->pdata);
}

void  *bmiter__loop_of_face_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;

	if (iter->nextloop) iter->nextloop = iter->nextloop->next;
	if (iter->nextloop == iter->firstloop) iter->nextloop = NULL;

	return current;
}
