/**
 * BME_structure.c    jan 2007
 *
 *	Low level routines for manipulating the BMesh structure.
 *
 * $Id: BME_structure.c,v 1.00 2007/01/17 17:42:01 Briggs Exp $
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.	
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
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Geoffrey Bantle.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include <limits.h>
#include "MEM_guardedalloc.h"

#include "DNA_listBase.h"
#include "BKE_utildefines.h"
#include "BKE_bmesh.h"
#include "BLI_blenlib.h"
#include "BLI_linklist.h"
#include "BLI_ghash.h"

#include "BKE_customdata.h"
/**
 *	MISC utility functions.
 *
 */
 
int BME_vert_in_edge(BME_Edge *e, BME_Vert *v){
	if(e->v1 == v || e->v2 == v) return 1;
	return 0;
}
int BME_verts_in_edge(BME_Vert *v1, BME_Vert *v2, BME_Edge *e){
	if(e->v1 == v1 && e->v2 == v2) return 1;
	else if(e->v1 == v2 && e->v2 == v1) return 1;
	return 0;
}

BME_Vert *BME_edge_getothervert(BME_Edge *e, BME_Vert *v){	
	if(e->v1 == v) return e->v2;
	else if(e->v2 == v) return e->v1;
	return NULL;
}

int BME_edge_swapverts(BME_Edge *e, BME_Vert *orig, BME_Vert *new){
	if(e->v1 == orig){ 
		e->v1 = new;
		e->d1.next = NULL;
		e->d1.prev = NULL;
		return 1;
	}
	else if(e->v2 == orig){
		e->v2 = new;
		e->d2.next = NULL;
		e->d2.prev = NULL;
		return 1;
	}
	return 0;
}

/**
 *	ALLOCATION/DEALLOCATION FUNCTIONS
 */

BME_Vert *BME_addvertlist(BME_Mesh *bm, BME_Vert *example){
	BME_Vert *v=NULL;
	v = MEM_callocN(sizeof(BME_Vert), "BME Vertex");
	BLI_addtail(&(bm->verts), v);
	v->EID = bm->nextv;
	bm->nextv++;
	bm->totvert++;

	if(example)
		VECCOPY(v->co,example->co);
	//if(example)
	//	CustomData_em_copy_data(&bm->vdata, &bm->vdata, example->data, &v->data);
	//else
	//	CustomData_em_set_default(&bm->vdata, &v->data);

	return v;
}
BME_Edge *BME_addedgelist(BME_Mesh *bm, BME_Vert *v1, BME_Vert *v2, BME_Edge *example){
	BME_Edge *e=NULL;
	e = MEM_callocN(sizeof(BME_Edge), "BME_Edge");
	e->v1 = v1;
	e->v2 = v2;
	e->d1.data = e;
	e->d2.data = e;
	e->EID = bm->nexte;
	bm->nexte++;
	bm->totedge++;
	BLI_addtail(&(bm->edges), e);
	
	//if(example)
	//	CustomData_em_copy_data(&bm->edata, &bm->edata, example->data, &e->data);
	//else
	//	CustomData_em_set_default(&bm->edata, &e->data);


	return e;
}
BME_Loop *BME_create_loop(BME_Mesh *bm, BME_Vert *v, BME_Edge *e, BME_Poly *f, BME_Loop *example){
	/*allocate a BME_Loop and add it to the loophash*/
	BME_Loop *l=NULL;
	BME_CycleNode *loopnode = MEM_callocN(sizeof(BME_CycleNode),"BME Loop Reference");
	l = MEM_callocN(sizeof(BME_Loop), "BME_Loop");
	l->radial.data = l;
	l->v = v;
	l->e = e;
	l->f = f;
	l->EID = bm->nextl;
	l->gref = loopnode;
	loopnode->data = l;
	BLI_addtail(&(bm->loops),loopnode);
	bm->nextl++;
	bm->totloop++;
	

/*	if(example)
		BME_CustomData_copy_data(&bm->ldata, &bm->ldata, example->data, &l->data);
	else
		BME_CustomData_set_default(&bm->ldata, &l->data);
*/
	return l;
}

BME_Poly *BME_addpolylist(BME_Mesh *bm, BME_Poly *example){
	BME_Poly *f = NULL;
	f= MEM_callocN(sizeof(BME_Poly),"BME_Poly");
	BLI_addtail(&(bm->polys),f);
	f->EID = bm->nextp;
	bm->nextp++;
	bm->totpoly++;

	//if(example)
	//	CustomData_em_copy_data(&bm->pdata, &bm->pdata, example->data, &f->data);
	//else
	//	CustomData_em_set_default(&bm->pdata, &f->data);


	return f;
}

/*	free functions dont do much *yet*. When per-vertex, per-edge and per-face/faceloop
	data is added though these will be needed.
*/
void BME_free_vert(BME_Mesh *bm, BME_Vert *v){
	bm->totvert--;
	//CustomData_em_free_block(&bm->vdata, &v->data);
	MEM_freeN(v);
}
void BME_free_edge(BME_Mesh *bm, BME_Edge *e){
	bm->totedge--;
	//CustomData_em_free_block(&bm->edata, &e->data);
	MEM_freeN(e);
}
void BME_free_poly(BME_Mesh *bm, BME_Poly *f){
	bm->totpoly--;
	//CustomData_em_free_block(&bm->pdata, &f->data);
	MEM_freeN(f);
}
void BME_delete_loop(BME_Mesh *bm, BME_Loop *l){
	bm->totloop--;
	//CustomData_em_free_block(&bm->ldata, &l->data);
	MEM_freeN(l);
}
void BME_free_loop(BME_Mesh *bm, BME_Loop *l){
	BME_CycleNode *loopref = l->gref;
	BLI_freelinkN(&(bm->loops),loopref);
	BME_delete_loop(bm,l);
}


/**
 *	BMESH CYCLES
 *
 *	Cycles are circular doubly linked lists that form the basis of adjacency
 *	information in the BME modeller. Full adjacency relations can be derived
 *	from examining these cycles very quickly. Although each cycle is a double
 *  circular linked list, each one is considered to have a 'base' or 'head',
 *	and care must be taken by Euler code when modifying the contents of a cycle.
 *
 *	The contents of this file are split into two parts. First there are the 
 *	BME_cycle family of functions which are generic circular double linked list 
 *	procedures. The second part contains higher level procedures for supporting 
 *	modification of specific cycle types.
 *
 *	The three cycles explicitly stored in the BMesh data structure are as follows:
 *
 *	1: The Disk Cycle - A circle of edges around a vertex
 *     Base: vertex->edge pointer.
 *	   
 *     This cycle is the most complicated in terms of its structure. Each BME_Edge contains	
 *	   two BME_CycleNode structures to keep track of that edge's membership in the disk cycle
 *	   of each of its vertices. However for any given vertex it may be the first in some edges
 *	   in its disk cycle and the second for others. The BME_disk_XXX family of functions contain
 *	   some nice utilities for navigating disk cycles in a way that hides this detail from the 
 *	   tool writer.
 *
 *		Note that the disk cycle is completley independant from face data. One advantage of this
 *		is that wire edges are fully integrated into the topology database. Another is that the 
 *	    the disk cycle has no problems dealing with non-manifold conditions involving faces.
 *
 *		Functions relating to this cycle:
 *		
 *			BME_disk_append_edge
 *			BME_disk_remove_edge
 *			BME_disk_nextedge
 *			BME_disk_getpointer
 *
 *	2: The Radial Cycle - A circle of face edges (BME_Loop) around an edge
 *	   Base: edge->loop->radial structure.
 *
 *		The radial cycle is similar to the radial cycle in the radial edge data structure.*
 *		Unlike the radial edge however, the radial cycle does not require a large amount of memory 
 *		to store non-manifold conditions since BMesh does not keep track of region/shell
 *		information.
 *		
 *		Functions relating to this cycle:
 *			
 *			BME_radial_append
 *			BME_radial_remove_loop
 *			BME_radial_nextloop
 *			BME_radial_find_face
 *		
 *
 *	3: The Loop Cycle - A circle of face edges around a polygon.
 *     Base: polygon->loopbase.
 *
 *	   The loop cycle keeps track of a faces vertices and edges. It should be noted that the
 *     direction of a loop cycle is either CW or CCW depending on the face normal, and is 
 *     not oriented to the faces editedges. 
 *
 *		Functions relating to this cycle:
 *		
 *			BME_cycle_XXX family of functions.
 *
 *	
 *	Note that the order of elements in all cycles except the loop cycle is undefined. This 
 *  leads to slightly increased seek time for deriving some adjacency relations, however the 
 *  advantage is that no intrinsic properties of the data structures are dependant upon the 
 *  cycle order and all non-manifold conditions are represented trivially.
 *
*/
 
 
void BME_cycle_append(void *h, void *nt)
{
	BME_CycleNode *oldtail, *head, *newtail;
	
	head = (BME_CycleNode*)h;
	newtail = (BME_CycleNode*)nt;
	
	if(head->next == NULL){
		head->next = newtail;
		head->prev = newtail;
		newtail->next = head;
		newtail->prev = head;
	}
	else{
		oldtail = head->prev;
		oldtail->next = newtail;
		newtail->next = head;
		newtail->prev = oldtail;
		head->prev = newtail;
		
	}
}

/**
 *			BME_cycle_length
 *
 *	Count the nodes in a cycle.
 *
 *  Returns -
 *	Integer
 */

int BME_cycle_length(void *h){
	
	int len = 0;
	BME_CycleNode *head, *curnode;
	head = (BME_CycleNode*)h;
	
	if(head){ 
		len = 1;
		for(curnode = head->next; curnode != head; curnode=curnode->next){ 
			if(len == INT_MAX){ //check for infinite loop/corrupted cycle
					return -1;
			}
			len++;
		}
	}
	return len;
}


/**
 *			BME_cycle_remove
 *
 *	Removes a node from a cycle.
 *
 *  Returns -
 *	1 for success, 0 for failure.
 */

int BME_cycle_remove(void *h, void *remn)
{
	int i, len;
	BME_CycleNode *head, *remnode, *curnode;
	
	head = (BME_CycleNode*)h;
	remnode = (BME_CycleNode*)remn;
	len = BME_cycle_length(h);
	
	if(len == 1 && head == remnode){
		head->next = NULL;
		head->prev = NULL;
		return 1;
	}
	else{
		for(i=0, curnode = head; i < len; curnode = curnode->next){
			if(curnode == remnode){
				remnode->prev->next = remnode->next;
				remnode->next->prev = remnode->prev;
				/*zero out remnode pointers, important!*/
				//remnode->next = NULL;
				//remnode->prev = NULL;
				return 1;
		
			}
		}
	}
	return 0;
}

/**
 *			BME_cycle_validate
 *
 *	Validates a cycle. Takes as an argument the expected length of the cycle and
 *	a pointer to the cycle head or base.
 *
 *
 *  Returns -
 *	1 for success, 0 for failure.
 */

int BME_cycle_validate(int len, void *h){
	int i;
	BME_CycleNode *curnode, *head;
	head = (BME_CycleNode*)h;
	
	/*forward validation*/
	for(i = 0, curnode = head; i < len; i++, curnode = curnode->next);
	if(curnode != head) return 0;
	
	/*reverse validation*/
	for(i = 0, curnode = head; i < len; i++, curnode = curnode->prev);
	if(curnode != head) return 0;
	
	return 1;
}

/*Begin Disk Cycle routines*/

/**
 *			BME_disk_nextedge
 *
 *	Find the next edge in a disk cycle
 *
 *  Returns -
 *	Pointer to the next edge in the disk cycle for the vertex v.
 */
 
BME_Edge *BME_disk_nextedge(BME_Edge *e, BME_Vert *v)
{	
	if(BME_vert_in_edge(e, v)){
		if(e->v1 == v) return e->d1.next->data;
		else if(e->v2 == v) return e->d2.next->data;
	}
	return NULL;
}

/**
 *			BME_disk_getpointer
 *
 *	Given an edge and one of its vertices, find the apporpriate CycleNode
 *
 *  Returns -
 *	Pointer to BME_CycleNode.
 */
BME_CycleNode *BME_disk_getpointer(BME_Edge *e, BME_Vert *v){
	/*returns pointer to the cycle node for the appropriate vertex in this disk*/
	if(e->v1 == v) return &(e->d1);
	else if (e->v2 == v) return &(e->d2);
	return NULL;
}

/**
 *			BME_disk_append_edge
 *
 *	Appends edge to the end of a vertex disk cycle.
 *
 *  Returns -
 *	1 for success, 0 for failure
 */

int BME_disk_append_edge(BME_Edge *e, BME_Vert *v)
{ 
	
	BME_CycleNode *base, *tail;
	
	if(BME_vert_in_edge(e, v) == 0) return 0; /*check to make sure v is in e*/
	
	/*check for loose vert first*/
	if(v->edge == NULL){
		v->edge = e;
		base = tail = BME_disk_getpointer(e, v);
		BME_cycle_append(base, tail); /*circular reference is ok!*/
		return 1;
	}
	
	/*insert e at the end of disk cycle and make it the new v->edge*/
	base = BME_disk_getpointer(v->edge, v);
	tail = BME_disk_getpointer(e, v);
	BME_cycle_append(base, tail);
	return 1;
}

/**
 *			BME_disk_remove_edge
 *
 *	Removes an edge from a disk cycle. If the edge to be removed is
 *	at the base of the cycle, the next edge becomes the new base.
 *
 *
 *  Returns -
 *	Nothing
 */

void BME_disk_remove_edge(BME_Edge *e, BME_Vert *v)
{
	BME_CycleNode *base, *remnode;
	BME_Edge *newbase;
	int len;
	
	base = BME_disk_getpointer(v->edge, v);
	remnode = BME_disk_getpointer(e, v);
	
	/*first deal with v->edge pointer...*/
	len = BME_cycle_length(base);
	if(len == 1) newbase = NULL;
	else if(v->edge == e) newbase = base->next-> data;
	else newbase = v->edge;
	
	/*remove and rebase*/
	BME_cycle_remove(base, remnode);
	v->edge = newbase;
}

/**
 *			BME_disk_next_edgeflag
 *
 *	Searches the disk cycle of v, starting with e, for the 
 *  next edge that has either eflag or tflag.
 *
 *	BME_Edge pointer.
 */

BME_Edge *BME_disk_next_edgeflag(BME_Edge *e, BME_Vert *v, int eflag, int tflag){
	
	BME_CycleNode *diskbase;
	BME_Edge *curedge;
	int len, ok;
	
	if(eflag && tflag) return NULL;
	
	ok = BME_vert_in_edge(e,v);
	if(ok){
		diskbase = BME_disk_getpointer(e, v);
		len = BME_cycle_length(diskbase);
		curedge = BME_disk_nextedge(e,v);
		while(curedge != e){
			if(tflag){
				if(curedge->tflag1 == tflag) return curedge;
			}
			else if(eflag){
				if(curedge->eflag1 == eflag) return curedge;
			}
			curedge = BME_disk_nextedge(curedge, v);
		}
	}
	return NULL;
}

/**
 *			BME_disk_count_edgeflag
 *
 *	Counts number of edges in this verts disk cycle which have 
 *	either eflag or tflag (but not both!)
 *
 *  Returns -
 *	Integer.
 */

int BME_disk_count_edgeflag(BME_Vert *v, int eflag, int tflag){
	BME_CycleNode *diskbase;
	BME_Edge *curedge;
	int i, len=0, count=0;
	
	if(v->edge){
		if(eflag && tflag) return 0; /*tflag and eflag are reserved for different functions!*/
		diskbase = BME_disk_getpointer(v->edge, v);
		len = BME_cycle_length(diskbase);
		
		for(i = 0, curedge=v->edge; i<len; i++){
			if(tflag){
				if(curedge->tflag1 == tflag) count++;
			}
			else if(eflag){
				if(curedge->eflag1 == eflag) count++;
			}
			curedge = BME_disk_nextedge(curedge, v);
		}
	}
	return count;
}

int BME_disk_hasedge(BME_Vert *v, BME_Edge *e){
	BME_CycleNode *diskbase;
	BME_Edge *curedge;
	int i, len=0;
	
	if(v->edge){
		diskbase = BME_disk_getpointer(v->edge,v);
		len = BME_cycle_length(diskbase);
		
		for(i = 0, curedge=v->edge; i<len; i++){
			if(curedge == e) return 1;
			else curedge=BME_disk_nextedge(curedge, v);
		}
	}
	return 0;
}
/*end disk cycle routines*/

BME_Loop *BME_radial_nextloop(BME_Loop *l){
	return (BME_Loop*)(l->radial.next->data);
}

void BME_radial_append(BME_Edge *e, BME_Loop *l){
	if(e->loop == NULL) e->loop = l;
	BME_cycle_append(&(e->loop->radial), &(l->radial));
}

void BME_radial_remove_loop(BME_Loop *l, BME_Edge *e)
{
	BME_Loop *newbase;
	int len;
	
	/*deal with edge->loop pointer*/
	len = BME_cycle_length(&(e->loop->radial));
	if(len == 1) newbase = NULL;
	else if(e->loop == l) newbase = e->loop->radial.next->data;
	else newbase = e->loop;
	
	/*remove and rebase*/
	BME_cycle_remove(&(e->loop->radial), &(l->radial));
	e->loop = newbase;
}

int BME_radial_find_face(BME_Edge *e,BME_Poly *f)
{
		
	BME_Loop *curloop;
	int i, len;
	
	len = BME_cycle_length(&(e->loop->radial));
	for(i = 0, curloop = e->loop; i < len; i++, curloop = curloop->radial.next->data){
		if(curloop->f == f) return 1;
	}
	return 0;
}

struct BME_Loop *BME_loop_find_loop(struct BME_Poly *f, struct BME_Vert *v) {
	BME_Loop *l;
	int i, len;
	
	len = BME_cycle_length(f->loopbase);
	for (i = 0, l=f->loopbase; i < len; i++, l=l->next) {
		if (l->v == v) return l;
	}
	return NULL;
}
