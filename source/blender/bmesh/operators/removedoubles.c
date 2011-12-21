#include "MEM_guardedalloc.h"

#include "DNA_meshdata_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BLI_utildefines.h"

#include "BLI_math.h"
#include "BLI_ghash.h"
#include "BLI_array.h"
#include "BLI_utildefines.h"

#include "bmesh.h"
#include "mesh_intern.h"
#include "bmesh_private.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BL(ptr) ((BMLoop*)(ptr))

static void remdoubles_splitface(BMFace *f, BMesh *bm, BMOperator *op)
{
	BMIter liter;
	BMLoop *l;
	BMVert *v2, *doub;
	int split=0;

	BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, f) {
		v2 = BMO_Get_MapPointer(bm, op, "targetmap", l->v);
		/*ok: if v2 is NULL (e.g. not in the map) then it's
		      a target vert, otherwise it's a double*/
		if (v2 && BM_Vert_In_Face(f, v2) && v2 != BL(l->prev)->v 
		    && v2 != BL(l->next)->v)
		{
			doub = l->v;
			split = 1;
			break;
		}
	}

	if (split && doub != v2) {
		BMLoop *nl;
		BMFace *f2 = BM_Split_Face(bm, f, doub, v2, &nl, NULL);

		remdoubles_splitface(f, bm, op);
		remdoubles_splitface(f2, bm, op);
	}
}

#define ELE_DEL		1
#define EDGE_COL	2
#define FACE_MARK	2

#if 0
int remdoubles_face_overlaps(BMesh *bm, BMVert **varr, 
			     int len, BMFace *exclude, 
			     BMFace **overlapface)
{
	BMIter vertfaces;
	BMFace *f;
	int i, amount;

	if (overlapface) *overlapface = NULL;

	for(i=0; i < len; i++) {
		f = BMIter_New(&vertfaces, bm, BM_FACES_OF_VERT, varr[i] );
		while(f) {
			amount = BM_Verts_In_Face(bm, f, varr, len);
			if(amount >= len) {
				if (overlapface) *overlapface = f;
				return 1;				
			}
			f = BMIter_Step(&vertfaces);
		}
	}
	return 0;
}
#endif

void bmesh_weldverts_exec(BMesh *bm, BMOperator *op)
{
	BMIter iter, liter;
	BMVert *v, *v2;
	BMEdge *e, *e2, **edges = NULL;
	BLI_array_declare(edges);
	BMLoop *l, *l2, **loops = NULL;
	BLI_array_declare(loops);
	BMFace *f, *f2;
	int a, b;

	BM_ITER(v, &iter, bm, BM_VERTS_OF_MESH, NULL) {
		if ((v2= BMO_Get_MapPointer(bm, op, "targetmap", v))) {
			BMO_SetFlag(bm, v, ELE_DEL);

			/* merge the vertex flags, else we get randomly selected/unselected verts */
			BM_MergeHFlag(v, v2);
		}
	}

	BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
		remdoubles_splitface(f, bm, op);
	}
	
	BM_ITER(e, &iter, bm, BM_EDGES_OF_MESH, NULL) {
		if (BMO_TestFlag(bm, e->v1, ELE_DEL) || BMO_TestFlag(bm, e->v2, ELE_DEL)) {
			v = BMO_Get_MapPointer(bm, op, "targetmap", e->v1);
			v2 = BMO_Get_MapPointer(bm, op, "targetmap", e->v2);
			
			if (!v) v = e->v1;
			if (!v2) v2 = e->v2;

			if (v == v2)
				BMO_SetFlag(bm, e, EDGE_COL);
			else if (!BM_Edge_Exist(v, v2))
				BM_Make_Edge(bm, v, v2, e, 1);

			BMO_SetFlag(bm, e, ELE_DEL);
		}
	}

	/* BMESH_TODO, stop abusing face index here */
	BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
		BM_SetIndex(f, 0); /* set_dirty! */
		BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, f) {
			if (BMO_TestFlag(bm, l->v, ELE_DEL))
				BMO_SetFlag(bm, f, FACE_MARK|ELE_DEL);
			if (BMO_TestFlag(bm, l->e, EDGE_COL)) 
				BM_SetIndex(f, BM_GetIndex(f)+1); /* set_dirty! */
		}
	}
	bm->elem_index_dirty |= BM_FACE;

	BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
		if (!BMO_TestFlag(bm, f, FACE_MARK))
			continue;

		if (f->len - BM_GetIndex(f) < 3) {
			BMO_SetFlag(bm, f, ELE_DEL);
			continue;
		}

		BLI_array_empty(edges);
		BLI_array_empty(loops);
		a = 0;
		BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, f) {
			v = l->v;
			v2 = BL(l->next)->v;
			if (BMO_TestFlag(bm, v, ELE_DEL)) 
				v = BMO_Get_MapPointer(bm, op, "targetmap", v);
			if (BMO_TestFlag(bm, v2, ELE_DEL)) 
				v2 = BMO_Get_MapPointer(bm, op, "targetmap", v2);
			
			e2 = v != v2 ? BM_Edge_Exist(v, v2) : NULL;
			if (e2) {
				for (b=0; b<a; b++) {
					if (edges[b] == e2)
						break;
				}
				if (b != a)
					continue;

				BLI_array_growone(edges);
				BLI_array_growone(loops);

				edges[a] = e2;
				loops[a] = l;

				a++;
			}
		}
		
		if (BLI_array_count(loops) < 3)
			continue;
		v = loops[0]->v;
		v2 = loops[1]->v;

		if (BMO_TestFlag(bm, v, ELE_DEL)) 
			v = BMO_Get_MapPointer(bm, op, "targetmap", v);
		if (BMO_TestFlag(bm, v2, ELE_DEL)) 
			v2 = BMO_Get_MapPointer(bm, op, "targetmap", v2);
		
		f2 = BM_Make_Ngon(bm, v, v2, edges, a, 1);
		if (f2 && (f2 != f)) {
			BM_Copy_Attributes(bm, bm, f, f2);

			a = 0;
			BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, f2) {
				l2 = loops[a];
				BM_Copy_Attributes(bm, bm, l2, l);

				a++;
			}
		}
	}

	BMO_CallOpf(bm, "del geom=%fvef context=%i", ELE_DEL, DEL_ONLYTAGGED);

	BLI_array_free(edges);
	BLI_array_free(loops);
}

static int vergaverco(const void *e1, const void *e2)
{
	const BMVert *v1 = *(void**)e1, *v2 = *(void**)e2;
	float x1 = v1->co[0] + v1->co[1] + v1->co[2];
	float x2 = v2->co[0] + v2->co[1] + v2->co[2];

	if (x1 > x2) return 1;
	else if (x1 < x2) return -1;
	else return 0;
}

#define VERT_TESTED	1
#define VERT_DOUBLE	2
#define VERT_TARGET	4
#define VERT_KEEP	8
#define VERT_MARK	16
#define VERT_IN		32

#define EDGE_MARK	1

void bmesh_pointmerge_facedata_exec(BMesh *bm, BMOperator *op)
{
	BMOIter siter;
	BMIter iter;
	BMVert *v, *snapv;
	BMLoop *l, *firstl = NULL;
	float fac;
	int i, tot;

	snapv = BMO_IterNew(&siter, bm, op, "snapv", BM_VERT);	
	tot = BM_Vert_FaceCount(snapv);

	if (!tot)
		return;

	fac = 1.0f / tot;
	BM_ITER(l, &iter, bm, BM_LOOPS_OF_VERT, snapv) {
		if (!firstl) {
			firstl = l;
		}
		
		for (i=0; i<bm->ldata.totlayer; i++) {
			if (CustomData_layer_has_math(&bm->ldata, i)) {
				int type = bm->ldata.layers[i].type;
				void *e1, *e2;

				e1 = CustomData_bmesh_get_layer_n(&bm->ldata, firstl->head.data, i); 
				e2 = CustomData_bmesh_get_layer_n(&bm->ldata, l->head.data, i);
				
				CustomData_data_multiply(type, e2, fac);

				if (l != firstl)
					CustomData_data_add(type, e1, e2);
			}
		}
	}

	BMO_ITER(v, &siter, bm, op, "verts", BM_VERT) {
		BM_ITER(l, &iter, bm, BM_LOOPS_OF_VERT, v) {
			if (l == firstl) 
				continue;

			CustomData_bmesh_copy_data(&bm->ldata, &bm->ldata, firstl->head.data, &l->head.data);
		}
	}
}

void bmesh_vert_average_facedata_exec(BMesh *bm, BMOperator *op)
{
	BMOIter siter;
	BMIter iter;
	BMVert *v;
	BMLoop *l /* , *firstl = NULL */;
	CDBlockBytes min, max;
	void *block;
	int i, type;

	for (i=0; i<bm->ldata.totlayer; i++) {
		if (!CustomData_layer_has_math(&bm->ldata, i))
			continue;
		
		type = bm->ldata.layers[i].type;
		CustomData_data_initminmax(type, &min, &max);

		BMO_ITER(v, &siter, bm, op, "verts", BM_VERT) {
			BM_ITER(l, &iter, bm, BM_LOOPS_OF_VERT, v) {
				block = CustomData_bmesh_get_layer_n(&bm->ldata, l->head.data, i);
				CustomData_data_dominmax(type, block, &min, &max);	
			}
		}

		CustomData_data_multiply(type, &min, 0.5f);
		CustomData_data_multiply(type, &max, 0.5f);
		CustomData_data_add(type, &min, &max);

		BMO_ITER(v, &siter, bm, op, "verts", BM_VERT) {
			BM_ITER(l, &iter, bm, BM_LOOPS_OF_VERT, v) {
				block = CustomData_bmesh_get_layer_n(&bm->ldata, l->head.data, i);
				CustomData_data_copy_value(type, &min, block);
			}
		}
	}
}

void bmesh_pointmerge_exec(BMesh *bm, BMOperator *op)
{
	BMOperator weldop;
	BMOIter siter;
	BMVert *v, *snapv = NULL;
	float vec[3];
	
	BMO_Get_Vec(op, "mergeco", vec);

	//BMO_CallOpf(bm, "collapse_uvs edges=%s", op, "edges");
	BMO_Init_Op(bm, &weldop, "weldverts");
	
	BMO_ITER(v, &siter, bm, op, "verts", BM_VERT) {
		if (!snapv) {
			snapv = v;
			copy_v3_v3(snapv->co, vec);
		} else {
			BMO_Insert_MapPointer(bm, &weldop, "targetmap", v, snapv);
		}		
	}

	BMO_Exec_Op(bm, &weldop);
	BMO_Finish_Op(bm, &weldop);
}

void bmesh_collapse_exec(BMesh *bm, BMOperator *op)
{
	BMOperator weldop;
	BMWalker walker;
	BMIter iter;
	BMEdge *e, **edges = NULL;
	BLI_array_declare(edges);
	float min[3], max[3];
	int i, tot;
	
	BMO_CallOpf(bm, "collapse_uvs edges=%s", op, "edges");
	BMO_Init_Op(bm, &weldop, "weldverts");

	BMO_Flag_Buffer(bm, op, "edges", EDGE_MARK, BM_EDGE);	
	BMW_Init(&walker, bm, BMW_SHELL,  0,EDGE_MARK,0,0,  BMW_NIL_LAY);

	BM_ITER(e, &iter, bm, BM_EDGES_OF_MESH, NULL) {
		if (!BMO_TestFlag(bm, e, EDGE_MARK))
			continue;

		e = BMW_Begin(&walker, e->v1);
		BLI_array_empty(edges);

		INIT_MINMAX(min, max);
		for (tot=0; e; tot++, e=BMW_Step(&walker)) {
			BLI_array_growone(edges);
			edges[tot] = e;

			DO_MINMAX(e->v1->co, min, max);
			DO_MINMAX(e->v2->co, min, max);
		}

		add_v3_v3v3(min, min, max);
		mul_v3_fl(min, 0.5f);

		/*snap edges to a point.  for initial testing purposes anyway.*/
		for (i=0; i<tot; i++) {
			copy_v3_v3(edges[i]->v1->co, min);
			copy_v3_v3(edges[i]->v2->co, min);
			
			if (edges[i]->v1 != edges[0]->v1)
				BMO_Insert_MapPointer(bm, &weldop, "targetmap", edges[i]->v1, edges[0]->v1);			
			if (edges[i]->v2 != edges[0]->v1)
				BMO_Insert_MapPointer(bm, &weldop, "targetmap", edges[i]->v2, edges[0]->v1);
		}
	}
	
	BMO_Exec_Op(bm, &weldop);
	BMO_Finish_Op(bm, &weldop);

	BMW_End(&walker);
	BLI_array_free(edges);
}

/*uv collapse function*/
static void bmesh_collapsecon_do_layer(BMesh *bm, BMOperator *op, int layer)
{
	BMIter iter, liter;
	BMFace *f;
	BMLoop *l, *l2;
	BMWalker walker;
	void **blocks = NULL;
	BLI_array_declare(blocks);
	CDBlockBytes min, max;
	int i, tot, type = bm->ldata.layers[layer].type;

	BMO_Clear_Flag_All(bm, op, BM_ALL, 65535);

	BMO_Flag_Buffer(bm, op, "edges", EDGE_MARK, BM_EDGE);
	BMW_Init(&walker, bm, BMW_LOOPDATA_ISLAND, 0,EDGE_MARK,0,0, layer);

	BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
		BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, f) {
			if (BMO_TestFlag(bm, l->e, EDGE_MARK)) {
				/*walk*/
				BLI_array_empty(blocks);
				tot = 0;
				l2 = BMW_Begin(&walker, l);

				CustomData_data_initminmax(type, &min, &max);
				for (tot=0; l2; tot++, l2=BMW_Step(&walker)) {
					BLI_array_growone(blocks);
					blocks[tot] = CustomData_bmesh_get_layer_n(&bm->ldata, l2->head.data, layer);
					CustomData_data_dominmax(type, blocks[tot], &min, &max);
				}

				if (tot) {
					CustomData_data_multiply(type, &min, 0.5f);
					CustomData_data_multiply(type, &max, 0.5f);
					CustomData_data_add(type, &min, &max);

					/*snap CD (uv, vcol) points to their centroid*/
					for (i=0; i<tot; i++) {
						CustomData_data_copy_value(type, &min, blocks[i]);
					}
				}
			}
		}
	}

	BMW_End(&walker);
	BLI_array_free(blocks);
}

void bmesh_collapsecon_exec(BMesh *bm, BMOperator *op)
{
	int i;

	for (i=0; i<bm->ldata.totlayer; i++) {
		if (CustomData_layer_has_math(&bm->ldata, i))
			bmesh_collapsecon_do_layer(bm, op, i);
	}
}

void bmesh_finddoubles_common(BMesh *bm, BMOperator *op, BMOperator *optarget, const char *targetmapname)
{
	BMOIter oiter;
	BMVert *v, *v2;
	BMVert **verts=NULL;
	BLI_array_declare(verts);
	float dist, dist3;
	int i, j, len, keepvert = 0;

	dist = BMO_Get_Float(op, "dist");
	dist3 = dist * 3.0f;

	i = 0;
	BMO_ITER(v, &oiter, bm, op, "verts", BM_VERT) {
		BLI_array_growone(verts);
		verts[i++] = v;
	}

	/* Test whether keepverts arg exists and is non-empty */
	if (BMO_HasSlot(op, "keepverts")) {
		keepvert = BMO_IterNew(&oiter, bm, op, "keepverts", BM_VERT) != NULL;
	}

	/*sort by vertex coordinates added together*/
	qsort(verts, BLI_array_count(verts), sizeof(void*), vergaverco);

	/* Flag keepverts */
	if (keepvert) {
		BMO_Flag_Buffer(bm, op, "keepverts", VERT_KEEP, BM_VERT);
	}

	len = BLI_array_count(verts);
	for (i=0; i<len; i++) {
		v = verts[i];
		if (BMO_TestFlag(bm, v, VERT_DOUBLE)) continue;
		
		for (j=i+1; j<len; j++) {
			v2 = verts[j];

			/* Compare sort values of the verts using 3x tolerance (allowing for the tolerance
			   on each of the three axes). This avoids the more expensive length comparison
			   for most vertex pairs. */
			if ((v2->co[0]+v2->co[1]+v2->co[2])-(v->co[0]+v->co[1]+v->co[2]) > dist3)
				break;

			if (keepvert) {
				if (BMO_TestFlag(bm, v2, VERT_KEEP) == BMO_TestFlag(bm, v, VERT_KEEP))
					continue;
			}

			if (compare_len_v3v3(v->co, v2->co, dist)) {

				/* If one vert is marked as keep, make sure it will be the target */
				if (BMO_TestFlag(bm, v2, VERT_KEEP)) {
					SWAP(BMVert *, v, v2);
				}

				BMO_SetFlag(bm, v2, VERT_DOUBLE);
				BMO_SetFlag(bm, v, VERT_TARGET);
			
				BMO_Insert_MapPointer(bm, optarget, targetmapname, v2, v);
			}
		}
	}

	BLI_array_free(verts);
}

void bmesh_removedoubles_exec(BMesh *bm, BMOperator *op)
{
	BMOperator weldop;

	BMO_Init_Op(bm, &weldop, "weldverts");
	bmesh_finddoubles_common(bm, op, &weldop, "targetmap");
	BMO_Exec_Op(bm, &weldop);
	BMO_Finish_Op(bm, &weldop);
}


void bmesh_finddoubles_exec(BMesh *bm, BMOperator *op)
{
	bmesh_finddoubles_common(bm, op, op, "targetmapout");
}

void bmesh_automerge_exec(BMesh *bm, BMOperator *op)
{
	BMOperator findop, weldop;
	BMIter viter;
	BMVert *v;

	/* The "verts" input sent to this op is the set of verts that
	   can be merged away into any other verts. Mark all other verts
	   as VERT_KEEP. */
	BMO_Flag_Buffer(bm, op, "verts", VERT_IN, BM_VERT);
	BM_ITER(v, &viter, bm, BM_VERTS_OF_MESH, NULL) {
		if (!BMO_TestFlag(bm, v, VERT_IN)) {
			BMO_SetFlag(bm, v, VERT_KEEP);
		}
	}

	/* Search for doubles among all vertices, but only merge non-VERT_KEEP
	   vertices into VERT_KEEP vertices. */
	BMO_InitOpf(bm, &findop, "finddoubles verts=%av keepverts=%fv", VERT_KEEP);
	BMO_CopySlot(op, &findop, "dist", "dist");
	BMO_Exec_Op(bm, &findop);

	/* weld the vertices */
	BMO_Init_Op(bm, &weldop, "weldverts");
	BMO_CopySlot(&findop, &weldop, "targetmapout", "targetmap");
	BMO_Exec_Op(bm, &weldop);

	BMO_Finish_Op(bm, &findop);
	BMO_Finish_Op(bm, &weldop);
}
