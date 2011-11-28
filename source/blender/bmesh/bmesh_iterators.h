/*
 * BMESH ITERATORS
 * 
 * The functions and structures in this file 
 * provide a unified method for iterating over 
 * the elements of a mesh and answering simple
 * adjacency queries. Tool authors should use
 * the iterators provided in this file instead
 * of inspecting the structure directly.
 *
*/

#ifndef BM_ITERATORS_H
#define BM_ITERATORS_H

#include "BLI_mempool.h"

/*Defines for passing to BMIter_New.
 
 "OF" can be substituted for "around"
  so BM_VERTS_OF_FACE means "vertices
  around a face."
 */

/*these iterator over all elements of a specific
  type in the mesh.*/
#define BM_VERTS_OF_MESH 			1
#define BM_EDGES_OF_MESH 			2
#define BM_FACES_OF_MESH 			3

/*these are topological iterators.*/
#define BM_EDGES_OF_VERT 			4
#define BM_FACES_OF_VERT 			5
#define BM_LOOPS_OF_VERT			6
#define BM_FACES_OF_EDGE 			7
#define BM_VERTS_OF_FACE 			8
#define BM_EDGES_OF_FACE 			9
#define BM_LOOPS_OF_FACE 			10
/*returns elements from all boundaries, and returns 
the first element at the end to flag that we're entering 
a different face hole boundary*/
#define BM_ALL_LOOPS_OF_FACE		11

/*iterate through loops around this loop, which are fetched
  from the other faces in the radial cycle surrounding the
  input loop's edge.*/
#define BM_LOOPS_OF_LOOP		12
#define BM_LOOPS_OF_EDGE		13

#define BM_ITER(ele, iter, bm, type, data) \
	ele = BMIter_New(iter, bm, type, data); \
	for ( ; ele; ele=BMIter_Step(iter))

#define BM_ITER_INDEX(ele, iter, bm, type, data, indexvar) \
	ele = BMIter_New(iter, bm, type, data); \
	for (indexvar=0; ele; indexvar++, ele=BMIter_Step(iter))

/*Iterator Structure*/
typedef struct BMIter {
	BLI_mempool_iter pooliter;

	struct BMVert *firstvert, *nextvert, *vdata;
	struct BMEdge *firstedge, *nextedge, *edata;
	struct BMLoop *firstloop, *nextloop, *ldata, *l;
	struct BMFace *firstpoly, *nextpoly, *pdata;
	struct BMesh *bm;
	void (*begin)(struct BMIter *iter);
	void *(*step)(struct BMIter *iter);
	union{
		void		*p;
		int			i;
		long		l;
		float		f;
	} filter;
	int htype, count;
}BMIter;

void *BMIter_AtIndex(struct BMesh *bm, const char htype, void *data, int index);

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
void  bmiter__vert_of_face_begin(struct BMIter *iter);
void *bmiter__vert_of_face_step(struct BMIter *iter);
void  bmiter__edge_of_face_begin(struct BMIter *iter);
void *bmiter__edge_of_face_step(struct BMIter *iter);
void  bmiter__loop_of_face_begin(struct BMIter *iter);
void *bmiter__loop_of_face_step(struct BMIter *iter);

#include "intern/bmesh_iterators_inline.c"

#endif
