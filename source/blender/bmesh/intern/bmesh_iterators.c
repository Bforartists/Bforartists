#include <string.h>

#include "bmesh.h"
#include "bmesh_private.h"

/*
 * note, we have BM_Vert_AtIndex/BM_Edge_AtIndex/BM_Face_AtIndex for arrays
 */
void *BMIter_AtIndex(struct BMesh *bm, const char htype, void *data, int index)
{
	BMIter iter;
	void *val;
	int i;

	/*sanity check*/
	if (index < 0) return NULL;

	val=BMIter_New(&iter, bm, htype, data);

	i = 0;
	while (i < index) {
		val=BMIter_Step(&iter);
		i++;
	}

	return val;
}

/*
 *	BMESH ITERATOR STEP
 *
 *  Calls an iterators step fucntion to return
 *  the next element.
*/

void *BMIter_Step(BMIter *iter)
{
	return iter->step(iter);
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
*/

/*
 * VERT OF MESH CALLBACKS
 *
*/

static void vert_of_mesh_begin(BMIter *iter)
{
	BLI_mempool_iternew(iter->bm->vpool, &iter->pooliter);
}

static void *vert_of_mesh_step(BMIter *iter)
{
	return BLI_mempool_iterstep(&iter->pooliter);

}

static void edge_of_mesh_begin(BMIter *iter)
{
	BLI_mempool_iternew(iter->bm->epool, &iter->pooliter);
}

static void *edge_of_mesh_step(BMIter *iter)
{
	return BLI_mempool_iterstep(&iter->pooliter);

}

static void face_of_mesh_begin(BMIter *iter)
{
	BLI_mempool_iternew(iter->bm->fpool, &iter->pooliter);
}

static void *face_of_mesh_step(BMIter *iter)
{
	return BLI_mempool_iterstep(&iter->pooliter);

}

/*
 * EDGE OF VERT CALLBACKS
 *
*/

static void edge_of_vert_begin(BMIter *iter)
{
	init_iterator(iter);
	if(iter->vdata->e){
		iter->firstedge = iter->vdata->e;
		iter->nextedge = iter->vdata->e;
	}
}

static void *edge_of_vert_step(BMIter *iter)
{
	BMEdge *current = iter->nextedge;

	if(iter->nextedge)
		iter->nextedge = bmesh_disk_nextedge(iter->nextedge, iter->vdata);
	
	if(iter->nextedge == iter->firstedge) iter->nextedge = NULL; 

	return current;
}

/*
 * FACE OF VERT CALLBACKS
 *
*/

static void face_of_vert_begin(BMIter *iter)
{
	init_iterator(iter);
	iter->count = 0;
	if(iter->vdata->e)
		iter->count = bmesh_disk_count_facevert(iter->vdata);
	if(iter->count){
		iter->firstedge = bmesh_disk_find_first_faceedge(iter->vdata->e, iter->vdata);
		iter->nextedge = iter->firstedge;
		iter->firstloop = bmesh_radial_find_first_facevert(iter->firstedge->l, iter->vdata);
		iter->nextloop = iter->firstloop;
	}
}
static void *face_of_vert_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;

	if(iter->count && iter->nextloop) {
		iter->count--;
		iter->nextloop = bmesh_radial_find_next_facevert(iter->nextloop, iter->vdata);
		if(iter->nextloop == iter->firstloop){
			iter->nextedge = bmesh_disk_find_next_faceedge(iter->nextedge, iter->vdata);
			iter->firstloop = bmesh_radial_find_first_facevert(iter->nextedge->l, iter->vdata);
			iter->nextloop = iter->firstloop;
		}
	}
	
	if(!iter->count) iter->nextloop = NULL;

	
	if(current) return current->f;
	return NULL;
}


/*
 * LOOP OF VERT CALLBACKS
 *
*/

static void loop_of_vert_begin(BMIter *iter)
{
	init_iterator(iter);
	iter->count = 0;
	if(iter->vdata->e)
		iter->count = bmesh_disk_count_facevert(iter->vdata);
	if(iter->count){
		iter->firstedge = bmesh_disk_find_first_faceedge(iter->vdata->e, iter->vdata);
		iter->nextedge = iter->firstedge;
		iter->firstloop = bmesh_radial_find_first_facevert(iter->firstedge->l, iter->vdata);
		iter->nextloop = iter->firstloop;
	}
}
static void *loop_of_vert_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;

	if(iter->count){
		iter->count--;
		iter->nextloop = bmesh_radial_find_next_facevert(iter->nextloop, iter->vdata);
		if(iter->nextloop == iter->firstloop){
			iter->nextedge = bmesh_disk_find_next_faceedge(iter->nextedge, iter->vdata);
			iter->firstloop = bmesh_radial_find_first_facevert(iter->nextedge->l, iter->vdata);
			iter->nextloop = iter->firstloop;
		}
	}
	
	if(!iter->count) iter->nextloop = NULL;

	
	if(current) return current;
	return NULL;
}


static void loops_of_edge_begin(BMIter *iter)
{
	BMLoop *l;

	l = iter->edata->l;

	/*note sure why this sets ldata. . .*/
	init_iterator(iter);
	
	iter->firstloop = iter->nextloop = l;
}

static void *loops_of_edge_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;

	if(iter->nextloop)
		iter->nextloop = bmesh_radial_nextloop(iter->nextloop);

	if(iter->nextloop == iter->firstloop) 
		iter->nextloop = NULL;

	if(current) return current;
	return NULL;
}

static void loops_of_loop_begin(BMIter *iter)
{
	BMLoop *l;

	l = iter->ldata;

	/*note sure why this sets ldata. . .*/
	init_iterator(iter);

	iter->firstloop = l;
	iter->nextloop = bmesh_radial_nextloop(iter->firstloop);
	
	if (iter->nextloop == iter->firstloop)
		iter->nextloop = NULL;
}

static void *loops_of_loop_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;
	
	if(iter->nextloop) iter->nextloop = bmesh_radial_nextloop(iter->nextloop);

	if(iter->nextloop == iter->firstloop) iter->nextloop = NULL;
	if(current) return current;
	return NULL;
}

/*
 * FACE OF EDGE CALLBACKS
 *
*/

static void face_of_edge_begin(BMIter *iter)
{
	init_iterator(iter);
	
	if(iter->edata->l){
		iter->firstloop = iter->edata->l;
		iter->nextloop = iter->edata->l;
	}
}

static void *face_of_edge_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;

	if(iter->nextloop) iter->nextloop = bmesh_radial_nextloop(iter->nextloop);

	if(iter->nextloop == iter->firstloop) iter->nextloop = NULL;
	if(current) return current->f;
	return NULL;
}

/*
 * VERT OF FACE CALLBACKS
 *
*/

static void vert_of_face_begin(BMIter *iter)
{
	init_iterator(iter);
	iter->firstloop = iter->nextloop = ((BMLoopList*)iter->pdata->loops.first)->first;
}

static void *vert_of_face_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;

	if(iter->nextloop) iter->nextloop = iter->nextloop->next;
	if(iter->nextloop == iter->firstloop) iter->nextloop = NULL;

	if(current) return current->v;
	return NULL;
}

/*
 * EDGE OF FACE CALLBACKS
 *
*/

static void edge_of_face_begin(BMIter *iter)
{
	init_iterator(iter);
	iter->firstloop = iter->nextloop = ((BMLoopList*)iter->pdata->loops.first)->first;
}

static void *edge_of_face_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;

	if(iter->nextloop) iter->nextloop = iter->nextloop->next;
	if(iter->nextloop == iter->firstloop) iter->nextloop = NULL;
	
	if(current) return current->e;
	return NULL;
}

/*
 * LOOP OF FACE CALLBACKS
 *
*/

static void loop_of_face_begin(BMIter *iter)
{
	init_iterator(iter);
	iter->firstloop = iter->nextloop = bm_firstfaceloop(iter->pdata);
}

static void *loop_of_face_step(BMIter *iter)
{
	BMLoop *current = iter->nextloop;

	if(iter->nextloop) iter->nextloop = iter->nextloop->next;
	if(iter->nextloop == iter->firstloop) iter->nextloop = NULL;

	return current;
}

/*
 * BMESH ITERATOR INIT
 *
 * Takes a bmesh iterator structure and fills
 * it with the appropriate function pointers based
 * upon its type and then calls BMeshIter_step()
 * to return the first element of the iterator.
 *
*/
void *BMIter_New(BMIter *iter, BMesh *bm, const char htype, void *data)
{
	/* int argtype; */
	iter->htype = htype;
	iter->bm = bm;

	switch(htype){
		case BM_VERTS_OF_MESH:
			iter->begin = vert_of_mesh_begin;
			iter->step = vert_of_mesh_step;
			break;
		case BM_EDGES_OF_MESH:
			iter->begin = edge_of_mesh_begin;
			iter->step = edge_of_mesh_step;
			break;
		case BM_FACES_OF_MESH:
			iter->begin = face_of_mesh_begin;
			iter->step = face_of_mesh_step;
			break;
		case BM_EDGES_OF_VERT:
			if (!data)
				return NULL;

			iter->begin = edge_of_vert_begin;
			iter->step = edge_of_vert_step;
			iter->vdata = data;
			break;
		case BM_FACES_OF_VERT:
			if (!data)
				return NULL;

			iter->begin = face_of_vert_begin;
			iter->step = face_of_vert_step;
			iter->vdata = data;
			break;
		case BM_LOOPS_OF_VERT:
			if (!data)
				return NULL;

			iter->begin = loop_of_vert_begin;
			iter->step = loop_of_vert_step;
			iter->vdata = data;
			break;
		case BM_FACES_OF_EDGE:
			if (!data)
				return NULL;

			iter->begin = face_of_edge_begin;
			iter->step = face_of_edge_step;
			iter->edata = data;
			break;
		case BM_VERTS_OF_FACE:
			if (!data)
				return NULL;

			iter->begin = vert_of_face_begin;
			iter->step = vert_of_face_step;
			iter->pdata = data;
			break;
		case BM_EDGES_OF_FACE:
			if (!data)
				return NULL;

			iter->begin = edge_of_face_begin;
			iter->step = edge_of_face_step;
			iter->pdata = data;
			break;
		case BM_LOOPS_OF_FACE:
			if (!data)
				return NULL;

			iter->begin = loop_of_face_begin;
			iter->step = loop_of_face_step;
			iter->pdata = data;
			break;
		case BM_LOOPS_OF_LOOP:
			if (!data)
				return NULL;

			iter->begin = loops_of_loop_begin;
			iter->step = loops_of_loop_step;
			iter->ldata = data;
			break;
		case BM_LOOPS_OF_EDGE:
			if (!data)
				return NULL;

			iter->begin = loops_of_edge_begin;
			iter->step = loops_of_edge_step;
			iter->edata = data;
			break;
		default:
			break;
	}

	iter->begin(iter);
	return BMIter_Step(iter);
}
