#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"

#include "BLI_ghash.h"
#include "BLI_memarena.h"
#include "BLI_blenlib.h"
#include "BLI_array.h"
#include "BLI_math.h"

#include "bmesh.h"
#include "bmesh_operators_private.h"

/*local flag defines*/
#define DUPE_INPUT		1 /*input from operator*/
#define DUPE_NEW		2
#define DUPE_DONE		4
#define DUPE_MAPPED		8

/*
 *  COPY VERTEX
 *
 *   Copy an existing vertex from one bmesh to another.
 *
*/
static BMVert *copy_vertex(BMesh *source_mesh, BMVert *source_vertex, BMesh *target_mesh, GHash *vhash)
{
	BMVert *target_vertex = NULL;

	/*Create a new vertex*/
	target_vertex = BM_Make_Vert(target_mesh, source_vertex->co,  NULL);
	
	/*Insert new vertex into the vert hash*/
	BLI_ghash_insert(vhash, source_vertex, target_vertex);	
	
	/*Copy attributes*/
	BM_Copy_Attributes(source_mesh, target_mesh, source_vertex, target_vertex);
	
	/*Set internal op flags*/
	BMO_SetFlag(target_mesh, (BMHeader*)target_vertex, DUPE_NEW);
	
	return target_vertex;
}

/*
 * COPY EDGE
 *
 * Copy an existing edge from one bmesh to another.
 *
*/
static BMEdge *copy_edge(BMOperator *op, BMesh *source_mesh,
			 BMEdge *source_edge, BMesh *target_mesh,
			 GHash *vhash, GHash *ehash)
{
	BMEdge *target_edge = NULL;
	BMVert *target_vert1, *target_vert2;
	BMFace *face;
	BMIter fiter;
	int rlen;

	/*see if any of the neighboring faces are
	  not being duplicated.  in that case,
	  add it to the new/old map.*/
	rlen = 0;
	for (face=BMIter_New(&fiter,source_mesh, BM_FACES_OF_EDGE,source_edge);
		face; face=BMIter_Step(&fiter)) {
		if (BMO_TestFlag(source_mesh, face, DUPE_INPUT)) {
			rlen++;
		}
	}

	/*Lookup v1 and v2*/
	target_vert1 = BLI_ghash_lookup(vhash, source_edge->v1);
	target_vert2 = BLI_ghash_lookup(vhash, source_edge->v2);
	
	/*Create a new edge*/
	target_edge = BM_Make_Edge(target_mesh, target_vert1, target_vert2, NULL, 0);
	
	/*add to new/old edge map if necassary*/
	if (rlen < 2) {
		/*not sure what non-manifold cases of greater then three
		  radial should do.*/
		BMO_Insert_MapPointer(source_mesh,op, "boundarymap",
			source_edge, target_edge);
	}

	/*Insert new edge into the edge hash*/
	BLI_ghash_insert(ehash, source_edge, target_edge);	
	
	/*Copy attributes*/
	BM_Copy_Attributes(source_mesh, target_mesh, source_edge, target_edge);
	
	/*Set internal op flags*/
	BMO_SetFlag(target_mesh, (BMHeader*)target_edge, DUPE_NEW);
	
	return target_edge;
}

/*
 * COPY FACE
 *
 *  Copy an existing face from one bmesh to another.
 *
*/
static BMFace *copy_face(BMOperator *op, BMesh *source_mesh,
                         BMFace *source_face, BMesh *target_mesh, 
                         BMVert **vtar, BMEdge **edar, GHash *vhash, GHash *ehash)
{
	BMVert *target_vert1, *target_vert2;
	BMLoop *source_loop, *target_loop;
	BMFace *target_face = NULL;
	BMIter iter, iter2;
	int i;
	
	/*lookup the first and second verts*/
	target_vert1 = BLI_ghash_lookup(vhash, BMIter_New(&iter, source_mesh, BM_VERTS_OF_FACE, source_face));
	target_vert2 = BLI_ghash_lookup(vhash, BMIter_Step(&iter));
	
	/*lookup edges*/
	for (i=0,source_loop=BMIter_New(&iter, source_mesh, BM_LOOPS_OF_FACE, source_face); 
		     source_loop; source_loop=BMIter_Step(&iter), i++) {
		vtar[i] = BLI_ghash_lookup(vhash, source_loop->v);
		edar[i] = BLI_ghash_lookup(ehash, source_loop->e);
	}
	
	/*create new face*/
	target_face = BM_Make_Face(target_mesh, vtar, edar, source_face->len, 0);
	BMO_Insert_MapPointer(source_mesh, op, 
	         "facemap", source_face, target_face);
	BMO_Insert_MapPointer(source_mesh, op, 
	         "facemap", target_face, source_face);

	BM_Copy_Attributes(source_mesh, target_mesh, source_face, target_face);

	/*mark the face for output*/
	BMO_SetFlag(target_mesh, (BMHeader*)target_face, DUPE_NEW);
	
	/*copy per-loop custom data*/
	BM_ITER(source_loop, &iter, source_mesh, BM_LOOPS_OF_FACE, source_face) {
		BM_ITER(target_loop, &iter2, target_mesh, BM_LOOPS_OF_FACE, target_face) {
			if (BLI_ghash_lookup(vhash, source_loop->v) == target_loop->v) {
				BM_Copy_Attributes(source_mesh, target_mesh, source_loop, target_loop);
				break;
			}
		}
	}

	return target_face;
}

/*
 * COPY MESH
 *
 * Internal Copy function.
 */
static void copy_mesh(BMOperator *op, BMesh *source, BMesh *target)
{

	BMVert *v = NULL, *v2, **vtar = NULL;
	BMEdge *e = NULL, **edar = NULL;
	BMFace *f = NULL;
	
	BMIter verts;
	BMIter edges;
	BMIter faces;
	
	GHash *vhash;
	GHash *ehash;
	
	int maxlength = 0;

	/*initialize pointer hashes*/
	vhash = BLI_ghash_new(BLI_ghashutil_ptrhash, BLI_ghashutil_ptrcmp, "bmesh dupeops v");
	ehash = BLI_ghash_new(BLI_ghashutil_ptrhash, BLI_ghashutil_ptrcmp, "bmesh dupeops e");
	
	/*initialize edge pointer array*/
	for(f = BMIter_New(&faces, source, BM_FACES_OF_MESH, source); f; f = BMIter_Step(&faces)){
		if(f->len > maxlength) maxlength = f->len;
	}
	edar = MEM_callocN(sizeof(BMEdge*) * maxlength, "BM copy mesh edge pointer array");
	vtar = MEM_callocN(sizeof(BMVert*) * maxlength, "BM copy mesh vert pointer array");
	
	for(v = BMIter_New(&verts, source, BM_VERTS_OF_MESH, source); v; v = BMIter_Step(&verts)){
		if(BMO_TestFlag(source, (BMHeader*)v, DUPE_INPUT) && (!BMO_TestFlag(source, (BMHeader*)v, DUPE_DONE))){
			BMIter iter;
			int iso = 1;

			v2 = copy_vertex(source, v, target, vhash);

			BM_ITER(f, &iter, source, BM_FACES_OF_VERT, v) {
				if (BMO_TestFlag(source, f, DUPE_INPUT)) {
					iso = 0;
					break;
				}
			}

			if (iso) {
				BM_ITER(e, &iter, source, BM_EDGES_OF_VERT, v) {
					if (BMO_TestFlag(source, e, DUPE_INPUT)) {
						iso = 0;
						break;
					}
				}
			}
			
			if (iso) 
				BMO_Insert_MapPointer(source, op, "isovertmap", v, v2);

			BMO_SetFlag(source, (BMHeader*)v, DUPE_DONE);
		}
	}

	/*now we dupe all the edges*/
	for(e = BMIter_New(&edges, source, BM_EDGES_OF_MESH, source); e; e = BMIter_Step(&edges)){
		if(BMO_TestFlag(source, (BMHeader*)e, DUPE_INPUT) && (!BMO_TestFlag(source, (BMHeader*)e, DUPE_DONE))){
			/*make sure that verts are copied*/
			if(!BMO_TestFlag(source, (BMHeader*)e->v1, DUPE_DONE)) {
				copy_vertex(source, e->v1, target, vhash);
				BMO_SetFlag(source, (BMHeader*)e->v1, DUPE_DONE);
			}
			if(!BMO_TestFlag(source, (BMHeader*)e->v2, DUPE_DONE)) {
				copy_vertex(source, e->v2, target, vhash);
				BMO_SetFlag(source, (BMHeader*)e->v2, DUPE_DONE);
			}
			/*now copy the actual edge*/
			copy_edge(op, source, e, target,  vhash,  ehash);			
			BMO_SetFlag(source, (BMHeader*)e, DUPE_DONE); 
		}
	}

	/*first we dupe all flagged faces and their elements from source*/
	for(f = BMIter_New(&faces, source, BM_FACES_OF_MESH, source); f; f= BMIter_Step(&faces)){
		if(BMO_TestFlag(source, (BMHeader*)f, DUPE_INPUT)){
			/*vertex pass*/
			for(v = BMIter_New(&verts, source, BM_VERTS_OF_FACE, f); v; v = BMIter_Step(&verts)){
				if(!BMO_TestFlag(source, (BMHeader*)v, DUPE_DONE)){ 
					copy_vertex(source,v, target, vhash);
					BMO_SetFlag(source, (BMHeader*)v, DUPE_DONE);
				}
			}

			/*edge pass*/
			for(e = BMIter_New(&edges, source, BM_EDGES_OF_FACE, f); e; e = BMIter_Step(&edges)){
				if(!BMO_TestFlag(source, (BMHeader*)e, DUPE_DONE)){
					copy_edge(op, source, e, target,  vhash,  ehash);
					BMO_SetFlag(source, (BMHeader*)e, DUPE_DONE);
				}
			}
			copy_face(op, source, f, target, vtar, edar, vhash, ehash);
			BMO_SetFlag(source, (BMHeader*)f, DUPE_DONE);
		}
	}
	
	/*free pointer hashes*/
	BLI_ghash_free(vhash, NULL, NULL);
	BLI_ghash_free(ehash, NULL, NULL);	

	/*free edge pointer array*/
	if (edar) {
		MEM_freeN(edar);
	}
	/*free vert pointer array*/
	if (vtar) {
		MEM_freeN(vtar);
	}
}

/*
 * Duplicate Operator
 *
 * Duplicates verts, edges and faces of a mesh.
 *
 * INPUT SLOTS:
 *
 * BMOP_DUPE_VINPUT: Buffer containing pointers to mesh vertices to be duplicated
 * BMOP_DUPE_EINPUT: Buffer containing pointers to mesh edges to be duplicated
 * BMOP_DUPE_FINPUT: Buffer containing pointers to mesh faces to be duplicated
 *
 * OUTPUT SLOTS:
 * 
 * BMOP_DUPE_VORIGINAL: Buffer containing pointers to the original mesh vertices
 * BMOP_DUPE_EORIGINAL: Buffer containing pointers to the original mesh edges
 * BMOP_DUPE_FORIGINAL: Buffer containing pointers to the original mesh faces
 * BMOP_DUPE_VNEW: Buffer containing pointers to the new mesh vertices
 * BMOP_DUPE_ENEW: Buffer containing pointers to the new mesh edges
 * BMOP_DUPE_FNEW: Buffer containing pointers to the new mesh faces
 *
*/

void dupeop_exec(BMesh *bm, BMOperator *op)
{
	BMOperator *dupeop = op;
	BMesh *bm2 = BMO_Get_Pnt(op, "dest");
	
	if (!bm2)
		bm2 = bm;
		
	/*flag input*/
	BMO_Flag_Buffer(bm, dupeop, "geom", DUPE_INPUT, BM_ALL);

	/*use the internal copy function*/
	copy_mesh(dupeop, bm, bm2);
	
	/*Output*/
	/*First copy the input buffers to output buffers - original data*/
	BMO_CopySlot(dupeop, dupeop, "geom", "origout");

	/*Now alloc the new output buffers*/
	BMO_Flag_To_Slot(bm, dupeop, "newout", DUPE_NEW, BM_ALL);
}

/*executes the duplicate operation, feeding elements of 
  type flag etypeflag and header flag flag to it.  note,
  to get more useful information (such as the mapping from
  original to new elements) you should run the dupe op manually.*/
void BMOP_DupeFromFlag(BMesh *bm, int etypeflag, int flag)
{
	BMOperator dupeop;

	BMO_Init_Op(&dupeop, "dupe");
	BMO_HeaderFlag_To_Slot(bm, &dupeop, "geom", flag, etypeflag);

	BMO_Exec_Op(bm, &dupeop);
	BMO_Finish_Op(bm, &dupeop);
}

/*
 * Split Operator
 *
 * Duplicates verts, edges and faces of a mesh but also deletes the originals.
 *
 * INPUT SLOTS:
 *
 * BMOP_DUPE_VINPUT: Buffer containing pointers to mesh vertices to be split
 * BMOP_DUPE_EINPUT: Buffer containing pointers to mesh edges to be split
 * BMOP_DUPE_FINPUT: Buffer containing pointers to mesh faces to be split
 *
 * OUTPUT SLOTS:
 * 
 * BMOP_DUPE_VOUTPUT: Buffer containing pointers to the split mesh vertices
 * BMOP_DUPE_EOUTPUT: Buffer containing pointers to the split mesh edges
 * BMOP_DUPE_FOUTPUT: Buffer containing pointers to the split mesh faces
 *
*/

#define SPLIT_INPUT	1
void splitop_exec(BMesh *bm, BMOperator *op)
{
	BMOperator *splitop = op;
	BMOperator dupeop;
	BMOperator delop;
	BMVert *v;
	BMEdge *e;
	BMFace *f;
	BMIter iter, iter2;
	int found;

	/*initialize our sub-operators*/
	BMO_Init_Op(&dupeop, "dupe");
	BMO_Init_Op(&delop, "del");
	
	BMO_CopySlot(splitop, &dupeop, "geom", "geom");
	BMO_Exec_Op(bm, &dupeop);
	
	BMO_Flag_Buffer(bm, splitop, "geom", SPLIT_INPUT, BM_ALL);

	/*make sure to remove edges and verts we don't need.*/
	for (e= BMIter_New(&iter, bm, BM_EDGES_OF_MESH, NULL);e;e=BMIter_Step(&iter)) {
		found = 0;
		f = BMIter_New(&iter2, bm, BM_FACES_OF_EDGE, e);
		for (; f; f=BMIter_Step(&iter2)) {
			if (!BMO_TestFlag(bm, f, SPLIT_INPUT)) {
				found = 1;
				break;
			}
		}
		if (!found) BMO_SetFlag(bm, e, SPLIT_INPUT);
	}
	
	for (v= BMIter_New(&iter, bm, BM_VERTS_OF_MESH, NULL);v;v=BMIter_Step(&iter)) {
		found = 0;
		e = BMIter_New(&iter2, bm, BM_EDGES_OF_VERT, v);
		for (; e; e=BMIter_Step(&iter2)) {
			if (!BMO_TestFlag(bm, e, SPLIT_INPUT)) {
				found = 1;
				break;
			}
		}
		if (!found) BMO_SetFlag(bm, v, SPLIT_INPUT);

	}

	/*connect outputs of dupe to delete, exluding keep geometry*/
	BMO_Set_Int(&delop, "context", DEL_FACES);
	BMO_Flag_To_Slot(bm, &delop, "geom", SPLIT_INPUT, BM_ALL);
	
	BMO_Exec_Op(bm, &delop);

	/*now we make our outputs by copying the dupe outputs*/
	BMO_CopySlot(&dupeop, splitop, "newout", "geomout");
	BMO_CopySlot(&dupeop, splitop, "boundarymap",
	             "boundarymap");
	BMO_CopySlot(&dupeop, splitop, "isovertmap",
	             "isovertmap");
	
	/*cleanup*/
	BMO_Finish_Op(bm, &delop);
	BMO_Finish_Op(bm, &dupeop);
}

#define DEL_INPUT		1
#define DEL_WIREVERT	2

static void delete_verts(BMesh *bm);
static void delete_context(BMesh *bm, int type);

void delop_exec(BMesh *bm, BMOperator *op)
{
	BMOperator *delop = op;

	/*Mark Buffers*/
	BMO_Flag_Buffer(bm, delop, "geom", DEL_INPUT, BM_ALL);

	delete_context(bm, BMO_Get_Int(op, "context"));
}

static void delete_verts(BMesh *bm)
{
	BMVert *v;
	BMEdge *e;
	BMLoop *f;
	
	BMIter verts;
	BMIter edges;
	BMIter faces;
	
	for(v = BMIter_New(&verts, bm, BM_VERTS_OF_MESH, bm); v; v = BMIter_Step(&verts)){
		if(BMO_TestFlag(bm, (BMHeader*)v, DEL_INPUT)) {
			/*Visit edges*/
			for(e = BMIter_New(&edges, bm, BM_EDGES_OF_VERT, v); e; e = BMIter_Step(&edges))
				BMO_SetFlag(bm, (BMHeader*)e, DEL_INPUT);
			/*Visit faces*/
			for(f = BMIter_New(&faces, bm, BM_FACES_OF_VERT, v); f; f = BMIter_Step(&faces))
				BMO_SetFlag(bm, (BMHeader*)f, DEL_INPUT);
		}
	}

	BM_remove_tagged_faces(bm, DEL_INPUT);
	BM_remove_tagged_edges(bm, DEL_INPUT);
	BM_remove_tagged_verts(bm, DEL_INPUT);
}

static void delete_edges(BMesh *bm){
	BMEdge *e;
	BMFace *f;
	
	BMIter edges;
	BMIter faces;

	for(e = BMIter_New(&edges, bm, BM_EDGES_OF_MESH, bm); e; e = BMIter_Step(&edges)){
		if(BMO_TestFlag(bm, (BMHeader*)e, DEL_INPUT)) {
			for(f = BMIter_New(&faces, bm, BM_FACES_OF_EDGE, e); f; f = BMIter_Step(&faces)){
					BMO_SetFlag(bm, (BMHeader*)f, DEL_INPUT);
			}
		}
	}
	BM_remove_tagged_faces(bm, DEL_INPUT);
	BM_remove_tagged_edges(bm, DEL_INPUT);
}

/*you need to make remove tagged verts/edges/faces
	api functions that take a filter callback.....
	and this new filter type will be for opstack flags.
	This is because the BM_remove_taggedXXX functions bypass iterator API.
		 -Ops dont care about 'UI' considerations like selection state, hide state, ect. If you want to work on unhidden selections for instance,
		 copy output from a 'select context' operator to another operator....
*/

/*Break this into smaller functions*/

static void delete_context(BMesh *bm, int type){
	BMVert *v;
	BMEdge *e;
	BMFace *f;

	BMIter verts;
	BMIter edges;
	BMIter faces;
	
	if(type == DEL_VERTS) delete_verts(bm);
	else if(type == DEL_EDGES){
		/*flush down to verts*/
		for(e = BMIter_New(&edges, bm, BM_EDGES_OF_MESH, bm); e; e = BMIter_Step(&edges)){
			if(BMO_TestFlag(bm, (BMHeader*)e, DEL_INPUT)){
				BMO_SetFlag(bm, (BMHeader*)(e->v1), DEL_INPUT);
				BMO_SetFlag(bm, (BMHeader*)(e->v2), DEL_INPUT);
			}
		}
		delete_edges(bm);
		/*remove loose vertices*/
		for(v = BMIter_New(&verts, bm, BM_VERTS_OF_MESH, bm); v; v = BMIter_Step(&verts)){
			if(BMO_TestFlag(bm, (BMHeader*)v, DEL_INPUT) && (!(v->e)))
				BMO_SetFlag(bm, (BMHeader*)v, DEL_WIREVERT);
		}
		BM_remove_tagged_verts(bm, DEL_WIREVERT);
	}
	else if(type == DEL_EDGESFACES) delete_edges(bm);
	else if(type == DEL_ONLYFACES) BM_remove_tagged_faces(bm, DEL_INPUT);
	else if (type == DEL_ONLYTAGGED) {
		BM_remove_tagged_faces(bm, DEL_INPUT);
		BM_remove_tagged_edges(bm, DEL_INPUT);
		BM_remove_tagged_verts(bm, DEL_INPUT);
	} else if(type == DEL_FACES){
		/*go through and mark all edges and all verts of all faces for delete*/
		for(f = BMIter_New(&faces, bm, BM_FACES_OF_MESH, bm); f; f = BMIter_Step(&faces)){
			if(BMO_TestFlag(bm, (BMHeader*)f, DEL_INPUT)){
				for(e = BMIter_New(&edges, bm, BM_EDGES_OF_FACE, f); e; e = BMIter_Step(&edges))
					BMO_SetFlag(bm, (BMHeader*)e, DEL_INPUT);
				for(v = BMIter_New(&verts, bm, BM_VERTS_OF_FACE, f); v; v = BMIter_Step(&verts))
					BMO_SetFlag(bm, (BMHeader*)v, DEL_INPUT);
			}
		}
		/*now go through and mark all remaining faces all edges for keeping.*/
		for(f = BMIter_New(&faces, bm, BM_FACES_OF_MESH, bm); f; f = BMIter_Step(&faces)){
			if(!BMO_TestFlag(bm, (BMHeader*)f, DEL_INPUT)){
				for(e = BMIter_New(&edges, bm, BM_EDGES_OF_FACE, f); e; e= BMIter_Step(&edges)){
					BMO_ClearFlag(bm, (BMHeader*)e, DEL_INPUT);
				}
				for(v = BMIter_New(&verts, bm, BM_VERTS_OF_FACE, f); v; v= BMIter_Step(&verts)){
					BMO_ClearFlag(bm, (BMHeader*)v, DEL_INPUT);
				}
			}
		}
		/*also mark all the vertices of remaining edges for keeping.*/
		for(e = BMIter_New(&edges, bm, BM_EDGES_OF_MESH, bm); e; e = BMIter_Step(&edges)){
			if(!BMO_TestFlag(bm, (BMHeader*)e, DEL_INPUT)){
				BMO_ClearFlag(bm, (BMHeader*)e->v1, DEL_INPUT);
				BMO_ClearFlag(bm, (BMHeader*)e->v2, DEL_INPUT);
			}
		}
		/*now delete marked faces*/
		BM_remove_tagged_faces(bm, DEL_INPUT);
		/*delete marked edges*/
		BM_remove_tagged_edges(bm, DEL_INPUT);
		/*remove loose vertices*/
		BM_remove_tagged_verts(bm, DEL_INPUT);
	}
	/*does this option even belong in here?*/
	else if(type == DEL_ALL){
		for(f = BMIter_New(&faces, bm, BM_FACES_OF_MESH, bm); f; f = BMIter_Step(&faces))
			BMO_SetFlag(bm, (BMHeader*)f, DEL_INPUT);
		for(e = BMIter_New(&edges, bm, BM_EDGES_OF_MESH, bm); e; e = BMIter_Step(&edges))
			BMO_SetFlag(bm, (BMHeader*)e, DEL_INPUT);
		for(v = BMIter_New(&verts, bm, BM_VERTS_OF_MESH, bm); v; v = BMIter_Step(&verts))
			BMO_SetFlag(bm, (BMHeader*)v, DEL_INPUT);
		
		BM_remove_tagged_faces(bm, DEL_INPUT);
		BM_remove_tagged_edges(bm, DEL_INPUT);
		BM_remove_tagged_verts(bm, DEL_INPUT);
	}
}

/*
 * Spin Operator
 *
 * Extrude or duplicate geometry a number of times,
 * rotating and possibly translating after each step
*/

void spinop_exec(BMesh *bm, BMOperator *op)
{
    BMOperator dupop, extop;
	float cent[3], dvec[3];
	float axis[3] = {0.0f, 0.0f, 1.0f};
	float q[4];
	float rmat[3][3];
	float phi, si;
	int steps, dupli, a, usedvec;

	BMO_Get_Vec(op, "cent", cent);
	BMO_Get_Vec(op, "axis", axis);
	normalize_v3(axis);
	BMO_Get_Vec(op, "dvec", dvec);
	usedvec = !is_zero_v3(dvec);
	steps = BMO_Get_Int(op, "steps");
	phi = BMO_Get_Float(op, "ang")*(float)M_PI/(360.0f*steps);
	dupli = BMO_Get_Int(op, "dupli");

	si = (float)sin(phi);
	q[0] = (float)cos(phi);
	q[1] = axis[0]*si;
	q[2] = axis[1]*si;
	q[3] = axis[2]*si;
	quat_to_mat3(rmat, q);

	BMO_CopySlot(op, op, "geom", "lastout");
	for(a=0; a<steps; a++) {
		if(dupli) {
			BMO_InitOpf(bm, &dupop, "dupe geom=%s", op, "lastout");
			BMO_Exec_Op(bm, &dupop);
			BMO_CallOpf(bm, "rotate cent=%v mat=%m3 verts=%s",
				cent, rmat, &dupop, "newout");
			BMO_CopySlot(&dupop, op, "newout", "lastout");
			BMO_Finish_Op(bm, &dupop);
		} else {
			BMO_InitOpf(bm, &extop, "extrudefaceregion edgefacein=%s",
				op, "lastout");
			BMO_Exec_Op(bm, &extop);
			BMO_CallOpf(bm, "rotate cent=%v mat=%m3 verts=%s",
				cent, rmat, &extop, "geomout");
			BMO_CopySlot(&extop, op, "geomout", "lastout");
			BMO_Finish_Op(bm, &extop);
		}

		if(usedvec)
			BMO_CallOpf(bm, "translate vec=%v verts=%s", dvec, op, "lastout");
	}
}
