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

#ifndef __BMESH_ITERATORS_H__
#define __BMESH_ITERATORS_H__

/** \file blender/bmesh/intern/bmesh_iterators.h
 *  \ingroup bmesh
 */

/**
 * \brief BMesh Iterators
 *
 * The functions and structures in this file
 * provide a unified method for iterating over
 * the elements of a mesh and answering simple
 * adjacency queries. Tool authors should use
 * the iterators provided in this file instead
 * of inspecting the structure directly.
 *
 */

#include "BLI_mempool.h"

/* Defines for passing to BM_iter_new.
 *
 * "OF" can be substituted for "around"
 * so BM_VERTS_OF_FACE means "vertices
 * around a face."
 */

/* these iterator over all elements of a specific
 * type in the mesh.
 *
 * be sure to keep 'bm_iter_itype_htype_map' in sync with any changes
 */
typedef enum BMIterType {
	BM_VERTS_OF_MESH = 1,
	BM_EDGES_OF_MESH = 2,
	BM_FACES_OF_MESH = 3,
	/* these are topological iterators. */
	BM_EDGES_OF_VERT = 4,
	BM_FACES_OF_VERT = 5,
	BM_LOOPS_OF_VERT = 6,
	BM_VERTS_OF_EDGE = 7, /* just v1, v2: added so py can use generalized sequencer wrapper */
	BM_FACES_OF_EDGE = 8,
	BM_VERTS_OF_FACE = 9,
	BM_EDGES_OF_FACE = 10,
	BM_LOOPS_OF_FACE = 11,
	/* returns elements from all boundaries, and returns
	 * the first element at the end to flag that we're entering
	 * a different face hole boundary*/
	BM_ALL_LOOPS_OF_FACE = 12,
	/* iterate through loops around this loop, which are fetched
	 * from the other faces in the radial cycle surrounding the
	 * input loop's edge.*/
	BM_LOOPS_OF_LOOP = 13,
	BM_LOOPS_OF_EDGE = 14
} BMIterType;

#define BM_ITYPE_MAX 15

/* the iterator htype for each iterator */
extern const char bm_iter_itype_htype_map[BM_ITYPE_MAX];

#define BM_ITER_MESH(ele, iter, bm, itype) \
	for (ele = BM_iter_new(iter, bm, itype, NULL); ele; ele = BM_iter_step(iter))

#define BM_ITER_MESH_INDEX(ele, iter, bm, itype, indexvar) \
	for (ele = BM_iter_new(iter, bm, itype, NULL), indexvar = 0; ele; ele = BM_iter_step(iter), (indexvar)++)

#define BM_ITER_ELEM(ele, iter, data, itype) \
	for (ele = BM_iter_new(iter, NULL, itype, data); ele; ele = BM_iter_step(iter))

#define BM_ITER_ELEM_INDEX(ele, iter, data, itype, indexvar) \
	for (ele = BM_iter_new(iter, NULL, itype, data), indexvar = 0; ele; ele = BM_iter_step(iter), (indexvar)++)

/* Iterator Structure */
/* note: some of these vars are not used,
 * so they have beem commented to save stack space since this struct is used all over */
typedef struct BMIter {
	BLI_mempool_iter pooliter;

	BMVert /* *v_first, *v_next, */ *vdata;
	BMEdge *e_first, *e_next, *edata;
	BMLoop *l_first, *l_next, *ldata;
	BMFace /* *f_first, *f_next, */ *pdata;
	BMesh *bm;
	void (*begin)(struct BMIter *iter);
	void *(*step)(struct BMIter *iter);
	/*
	union {
		void       *p;
		int         i;
		long        l;
		float       f;
	} filter;
	*/
	int count;  /* note, only some iterators set this, don't rely on it */
	char itype;
} BMIter;

void   *BM_iter_at_index(BMesh *bm, const char itype, void *data, int index)
#ifdef __GNUC__
__attribute__((warn_unused_result))
#endif
;
int     BM_iter_as_array(BMesh *bm, const char itype, void *data, void **array, const int len);
void   *BM_iter_as_arrayN(BMesh *bm, const char itype, void *data, int *r_len)
#ifdef __GNUC__
__attribute__((warn_unused_result))
#endif
;
int     BM_iter_elem_count_flag(const char itype, void *data, const char hflag, const short value);
int     BM_iter_mesh_count_flag(const char itype, BMesh *bm, const char hflag, const short value);

/* private for bmesh_iterators_inline.c */
void  bmiter__vert_of_mesh_begin(struct BMIter *iter);
void *bmiter__vert_of_mesh_step(struct BMIter *iter);
void  bmiter__edge_of_mesh_begin(struct BMIter *iter);
void *bmiter__edge_of_mesh_step(struct BMIter *iter);
void  bmiter__face_of_mesh_begin(struct BMIter *iter);
void *bmiter__face_of_mesh_step(struct BMIter *iter);
void  bmiter__edge_of_vert_begin(struct BMIter *iter);
void *bmiter__edge_of_vert_step(struct BMIter *iter);
void  bmiter__face_of_vert_begin(struct BMIter *iter);
void *bmiter__face_of_vert_step(struct BMIter *iter);
void  bmiter__loop_of_vert_begin(struct BMIter *iter);
void *bmiter__loop_of_vert_step(struct BMIter *iter);
void  bmiter__loops_of_edge_begin(struct BMIter *iter);
void *bmiter__loops_of_edge_step(struct BMIter *iter);
void  bmiter__loops_of_loop_begin(struct BMIter *iter);
void *bmiter__loops_of_loop_step(struct BMIter *iter);
void  bmiter__face_of_edge_begin(struct BMIter *iter);
void *bmiter__face_of_edge_step(struct BMIter *iter);
void  bmiter__vert_of_edge_begin(struct BMIter *iter);
void *bmiter__vert_of_edge_step(struct BMIter *iter);
void  bmiter__vert_of_face_begin(struct BMIter *iter);
void *bmiter__vert_of_face_step(struct BMIter *iter);
void  bmiter__edge_of_face_begin(struct BMIter *iter);
void *bmiter__edge_of_face_step(struct BMIter *iter);
void  bmiter__loop_of_face_begin(struct BMIter *iter);
void *bmiter__loop_of_face_step(struct BMIter *iter);

#include "intern/bmesh_iterators_inline.h"

#endif /* __BMESH_ITERATORS_H__ */
