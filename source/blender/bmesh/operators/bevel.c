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

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"
#include "BLI_ghash.h"
#include "BLI_memarena.h"
#include "BLI_array.h"
#include "BLI_math.h"
#include "BLI_array.h"
#include "BLI_utildefines.h"
#include "BLI_smallhash.h"

#include "bmesh.h"
#include "bmesh_operators_private.h"

#define BEVEL_FLAG	1
#define BEVEL_DEL	2
#define FACE_NEW	4
#define EDGE_OLD	8
#define FACE_OLD	16
#define FACE_DONE	32
#define VERT_OLD	64
#define FACE_SPAN	128
#define FACE_HOLE	256

typedef struct LoopTag {
	BMVert *newv;
} LoopTag;

typedef struct EdgeTag {
	BMVert *newv1, *newv2;
} EdgeTag;

static void calc_corner_co(BMesh *bm, BMLoop *l, const float fac, float r_co[3],
                           const short do_dist, const short do_even)
{
	float  no[3], l_vec_prev[3], l_vec_next[3], l_co_prev[3], l_co[3], l_co_next[3], co_ofs[3];
	int is_concave;

	/* first get the prev/next verts */
	if (l->f->len > 2) {
		copy_v3_v3(l_co_prev, l->prev->v->co);
		copy_v3_v3(l_co, l->v->co);
		copy_v3_v3(l_co_next, l->next->v->co);

		/* calculate norma */
		sub_v3_v3v3(l_vec_prev, l_co_prev, l_co);
		sub_v3_v3v3(l_vec_next, l_co_next, l_co);

		cross_v3_v3v3(no, l_vec_prev, l_vec_next);
		is_concave = dot_v3v3(no, l->f->no) > 0.0f;
	}
	else {
		BMIter iter;
		BMLoop *l2;
		float up[3] = {0.0f, 0.0f, 1.0f};

		copy_v3_v3(l_co_prev, l->prev->v->co);
		copy_v3_v3(l_co, l->v->co);
		
		BM_ITER(l2, &iter, bm, BM_LOOPS_OF_VERT, l->v) {
			if (l2->f != l->f) {
				copy_v3_v3(l_co_next, BM_OtherEdgeVert(l2->e, l2->next->v)->co);
				break;
			}
		}
		
		sub_v3_v3v3(l_vec_prev, l_co_prev, l_co);
		sub_v3_v3v3(l_vec_next, l_co_next, l_co);

		cross_v3_v3v3(no, l_vec_prev, l_vec_next);
		if (dot_v3v3(no, no) == 0.0f) {
			no[0] = no[1] = 0.0f; no[2] = -1.0f;	
		}
		
		is_concave = dot_v3v3(no, up) < 0.0f;
	}


	/* now calculate the new location */
	if (do_dist) { /* treat 'fac' as distance */

		normalize_v3(l_vec_prev);
		normalize_v3(l_vec_next);

		add_v3_v3v3(co_ofs, l_vec_prev, l_vec_next);
		normalize_v3(co_ofs);

		if (do_even) {
			negate_v3(l_vec_next);
			mul_v3_fl(co_ofs, fac * shell_angle_to_dist(0.5f * angle_normalized_v3v3(l_vec_prev, l_vec_next)));
			/* negate_v3(l_vec_next); */ /* no need unless we use again */
		}
		else {
			mul_v3_fl(co_ofs, fac);
		}
	}
	else { /* treat as 'fac' as a factor (0 - 1) */

		/* not strictly necessary, balance vectors
		 * so the longer edge doesn't skew the result,
		 * gives nicer, move even output.
		 *
		 * Use the minimum rather then the middle value so skinny faces don't flip along the short axis */
		float min_fac = minf(normalize_v3(l_vec_prev), normalize_v3(l_vec_next));
		float angle = do_even ? angle_normalized_v3v3(l_vec_prev, l_vec_next) : 0.0f; /* get angle while normalized */

		mul_v3_fl(l_vec_prev, min_fac);
		mul_v3_fl(l_vec_next, min_fac);

		add_v3_v3v3(co_ofs, l_vec_prev, l_vec_next);

		/* done */
		if (do_even) {
			negate_v3(l_vec_next);
			mul_v3_fl(co_ofs, (fac * 0.5) * shell_angle_to_dist(0.5f * angle));
			/* negate_v3(l_vec_next); */ /* no need unless we use again */
		}
		else {
			mul_v3_fl(co_ofs, fac * 0.5);
		}
	}

	/* apply delta vec */
	if (is_concave)
		negate_v3(co_ofs);

	add_v3_v3v3(r_co, co_ofs, l->v->co);
}


#define ETAG_SET(e, v, nv)  (                                                 \
	(v) == (e)->v1 ?                                                          \
		(etags[BM_GetIndex((e))].newv1 = (nv)) :                              \
		(etags[BM_GetIndex((e))].newv2 = (nv))                                \
	)

#define ETAG_GET(e, v)  (                                                     \
	(v) == (e)->v1 ?                                                          \
		(etags[BM_GetIndex((e))].newv1) :                                     \
		(etags[BM_GetIndex((e))].newv2)                                       \
	)

void bmesh_bevel_exec(BMesh *bm, BMOperator *op)
{
	BMOIter siter;
	BMIter iter;
	BMEdge *e;
	BMVert *v;
	BMFace **faces = NULL, *f;
	LoopTag *tags = NULL, *tag;
	EdgeTag *etags = NULL;
	BMVert **verts = NULL;
	BMEdge **edges = NULL;
	BLI_array_declare(faces);
	BLI_array_declare(tags);
	BLI_array_declare(etags);
	BLI_array_declare(verts);
	BLI_array_declare(edges);
	SmallHash hash;
	float fac = BMO_Get_Float(op, "percent");
	const short do_even = BMO_Get_Int(op, "use_even");
	const short do_dist = BMO_Get_Int(op, "use_dist");
	int i, li, has_elens, HasMDisps = CustomData_has_layer(&bm->ldata, CD_MDISPS);
	
	has_elens = CustomData_has_layer(&bm->edata, CD_PROP_FLT) && BMO_Get_Int(op, "use_lengths");
	if (has_elens) {
		li = BMO_Get_Int(op, "lengthlayer");
	}
	
	BLI_smallhash_init(&hash);
	
	BMO_ITER(e, &siter, bm, op, "geom", BM_EDGE) {
		BMO_SetFlag(bm, e, BEVEL_FLAG|BEVEL_DEL);
		BMO_SetFlag(bm, e->v1, BEVEL_FLAG|BEVEL_DEL);
		BMO_SetFlag(bm, e->v2, BEVEL_FLAG|BEVEL_DEL);
		
		if (BM_Edge_FaceCount(e) < 2) {
			BMO_ClearFlag(bm, e, BEVEL_DEL);
			BMO_ClearFlag(bm, e->v1, BEVEL_DEL);
			BMO_ClearFlag(bm, e->v2, BEVEL_DEL);
		}
#if 0
		if (BM_Edge_FaceCount(e) == 0) {
			BMVert *verts[2] = {e->v1, e->v2};
			BMEdge *edges[2] = {e, BM_Make_Edge(bm, e->v1, e->v2, e, 0)};
			
			BMO_SetFlag(bm, edges[1], BEVEL_FLAG);
			BM_Make_Face(bm, verts, edges, 2, 0);
		}
#endif
	}
	
	BM_ITER(v, &iter, bm, BM_VERTS_OF_MESH, NULL) {
		BMO_SetFlag(bm, v, VERT_OLD);
	}

#if 0
	//a bit of cleaner code that, alas, doens't work.
	/* build edge tag */
	BM_ITER(e, &iter, bm, BM_EDGES_OF_MESH, NULL) {
		if (BMO_TestFlag(bm, e->v1, BEVEL_FLAG) || BMO_TestFlag(bm, e->v2, BEVEL_FLAG)) {
			BMIter liter;
			BMLoop *l;
			
			if (!BMO_TestFlag(bm, e, EDGE_OLD)) {
				BM_SetIndex(e, BLI_array_count(etags)); /* set_dirty! */
				BLI_array_growone(etags);
				
				BMO_SetFlag(bm, e, EDGE_OLD);
			}
			
			BM_ITER(l, &liter, bm, BM_LOOPS_OF_EDGE, e) {
				BMLoop *l2;
				BMIter liter2;
				
				if (BMO_TestFlag(bm, l->f, BEVEL_FLAG))
					continue;
			
				BM_ITER(l2, &liter2, bm, BM_LOOPS_OF_FACE, l->f) {
					BM_SetIndex(l2, BLI_array_count(tags)); /* set_loop */
					BLI_array_growone(tags);

					if (!BMO_TestFlag(bm, l2->e, EDGE_OLD)) {
						BM_SetIndex(l2->e, BLI_array_count(etags)); /* set_dirty! */
						BLI_array_growone(etags);
						
						BMO_SetFlag(bm, l2->e, EDGE_OLD);
					}
				}

				BMO_SetFlag(bm, l->f, BEVEL_FLAG);
				BLI_array_append(faces, l->f);
			}
		}
		else {
			BM_SetIndex(e, -1); /* set_dirty! */
		}
	}
#endif
	
	/* create and assign looptag structure */
	BMO_ITER(e, &siter, bm, op, "geom", BM_EDGE) {
		BMLoop *l;
		BMIter liter;

		BMO_SetFlag(bm, e->v1, BEVEL_FLAG|BEVEL_DEL);
		BMO_SetFlag(bm, e->v2, BEVEL_FLAG|BEVEL_DEL);
		
		if (BM_Edge_FaceCount(e) < 2) {
			BMO_ClearFlag(bm, e, BEVEL_DEL);
			BMO_ClearFlag(bm, e->v1, BEVEL_DEL);
			BMO_ClearFlag(bm, e->v2, BEVEL_DEL);
		}
		
		if (!BLI_smallhash_haskey(&hash, (intptr_t)e)) {
			BLI_array_growone(etags);
			BM_SetIndex(e, BLI_array_count(etags) - 1); /* set_dirty! */
			BLI_smallhash_insert(&hash, (intptr_t)e, NULL);
			BMO_SetFlag(bm, e, EDGE_OLD);
		}
		
		/* find all faces surrounding e->v1 and, e->v2 */
		for (i = 0; i < 2; i++) {
			BM_ITER(l, &liter, bm, BM_LOOPS_OF_VERT, i ? e->v2:e->v1) {
				BMLoop *l2;
				BMIter liter2;
				
				/* see if we've already processed this loop's fac */
				if (BLI_smallhash_haskey(&hash, (intptr_t)l->f))
					continue;
				
				/* create tags for all loops in l-> */
				BM_ITER(l2, &liter2, bm, BM_LOOPS_OF_FACE, l->f) {
					BLI_array_growone(tags);
					BM_SetIndex(l2, BLI_array_count(tags) - 1); /* set_loop */
					
					if (!BLI_smallhash_haskey(&hash, (intptr_t)l2->e)) {
						BLI_array_growone(etags);
						BM_SetIndex(l2->e, BLI_array_count(etags) - 1); /* set_dirty! */
						BLI_smallhash_insert(&hash, (intptr_t)l2->e, NULL);						
						BMO_SetFlag(bm, l2->e, EDGE_OLD);
					}
				}
	
				BLI_smallhash_insert(&hash, (intptr_t)l->f, NULL);
				BMO_SetFlag(bm, l->f, BEVEL_FLAG);
				BLI_array_append(faces, l->f);
			}
		}
	}

	bm->elem_index_dirty |= BM_EDGE;
	
	BM_ITER(v, &iter, bm, BM_VERTS_OF_MESH, NULL) {
		BMIter eiter;
		
		if (!BMO_TestFlag(bm, v, BEVEL_FLAG))
			continue;
		
		BM_ITER(e, &eiter, bm, BM_EDGES_OF_VERT, v) {
			if (!BMO_TestFlag(bm, e, BEVEL_FLAG) && !ETAG_GET(e, v)) {
				BMVert *v2;
				float co[3];
				
				v2 = BM_OtherEdgeVert(e, v);
				sub_v3_v3v3(co, v2->co, v->co);
				if (has_elens) {
					float elen = *(float *)CustomData_bmesh_get_n(&bm->edata, e->head.data, CD_PROP_FLT, li);

					normalize_v3(co);
					mul_v3_fl(co, elen);
				}
				
				mul_v3_fl(co, fac);
				add_v3_v3(co, v->co);
				
				v2 = BM_Make_Vert(bm, co, v);
				ETAG_SET(e, v, v2);
			}
		}
	}
	
	for (i = 0; i < BLI_array_count(faces); i++) {
		BMLoop *l;
		BMIter liter;
		
		BMO_SetFlag(bm, faces[i], FACE_OLD);
		
		BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, faces[i]) {
			float co[3];

			if (BMO_TestFlag(bm, l->e, BEVEL_FLAG)) {
				if (BMO_TestFlag(bm, l->prev->e, BEVEL_FLAG))
				{
					tag = tags + BM_GetIndex(l);
					calc_corner_co(bm, l, fac, co, do_dist, do_even);
					tag->newv = BM_Make_Vert(bm, co, l->v);
				}
				else {
					tag = tags + BM_GetIndex(l);
					tag->newv = ETAG_GET(l->prev->e, l->v);
					
					if (!tag->newv) {
						sub_v3_v3v3(co, l->prev->v->co, l->v->co);
						if (has_elens) {
							float elen = *(float *)CustomData_bmesh_get_n(&bm->edata, l->prev->e->head.data, CD_PROP_FLT, li);

							normalize_v3(co);
							mul_v3_fl(co, elen);
						}
								
						mul_v3_fl(co, fac);
						add_v3_v3(co, l->v->co);
					
						tag->newv = BM_Make_Vert(bm, co, l->v);
						
						ETAG_SET(l->prev->e, l->v, tag->newv);
					}
				}
			}
			else if (BMO_TestFlag(bm, l->v, BEVEL_FLAG)) {
				tag = tags + BM_GetIndex(l);
				tag->newv = ETAG_GET(l->e, l->v);				
		
				if (!tag->newv) {
					sub_v3_v3v3(co, l->next->v->co, l->v->co);
					if (has_elens) {
						float elen = *(float *)CustomData_bmesh_get_n(&bm->edata, l->e->head.data, CD_PROP_FLT, li);

						normalize_v3(co);
						mul_v3_fl(co, elen);
					}
					
					mul_v3_fl(co, fac);
					add_v3_v3(co, l->v->co);
			
					tag = tags + BM_GetIndex(l);
					tag->newv = BM_Make_Vert(bm, co, l->v);
					
					ETAG_SET(l->e, l->v, tag->newv);
				}					
			}
			else {
				tag = tags + BM_GetIndex(l);
				tag->newv = l->v;
				BMO_ClearFlag(bm, l->v, BEVEL_DEL);
			}
		}
	}
	
	/* create new faces inset from original face */
	for (i = 0; i < BLI_array_count(faces); i++) {
		BMLoop *l;
		BMIter liter;
		BMFace *f;
		BMVert *lastv = NULL, *firstv = NULL;

		BMO_SetFlag(bm, faces[i], BEVEL_DEL);
		
		BLI_array_empty(verts);
		BLI_array_empty(edges);
		
		BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, faces[i]) {
			BMVert *v2;
			
			tag = tags + BM_GetIndex(l);
			BLI_array_append(verts, tag->newv);
			
			if (!firstv)
				firstv = tag->newv;
			
			if (lastv) {
				e = BM_Make_Edge(bm, lastv, tag->newv, l->e, 1);
				BM_Copy_Attributes(bm, bm, l->prev->e, e);
				BLI_array_append(edges, e);
			}
			lastv = tag->newv;
			
			v2 = ETAG_GET(l->e, l->next->v);
			
			tag = tags + BM_GetIndex(l->next);
			if (!BMO_TestFlag(bm, l->e, BEVEL_FLAG) && v2 && v2 != tag->newv) {
				BLI_array_append(verts, v2);
				
				e = BM_Make_Edge(bm, lastv, v2, l->e, 1);
				BM_Copy_Attributes(bm, bm, l->e, e);
				
				BLI_array_append(edges, e);
				lastv = v2;
			}
		}
		
		e = BM_Make_Edge(bm, firstv, lastv, BM_FACE_FIRST_LOOP(faces[i])->e, 1);
		if (BM_FACE_FIRST_LOOP(faces[i])->prev->e != e) 
			BM_Copy_Attributes(bm, bm, BM_FACE_FIRST_LOOP(faces[i])->prev->e, e);
		BLI_array_append(edges, e);
		
		f = BM_Make_Ngon(bm, verts[0], verts[1], edges, BLI_array_count(edges), 0);
		if (!f) {
			printf("%s: could not make face!\n", __func__);
			continue;
		}
			
		BMO_SetFlag(bm, f, FACE_NEW);
	}

	for (i = 0; i < BLI_array_count(faces); i++) {
		BMLoop *l;
		BMIter liter;
		int j;
		
		/* create quad spans between split edge */
		BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, faces[i]) {
			BMVert *v1 = NULL, *v2 = NULL, *v3 = NULL, *v4 = NULL;
			
			if (!BMO_TestFlag(bm, l->e, BEVEL_FLAG))
				continue;
			
			v1 = tags[BM_GetIndex(l)].newv;
			v2 = tags[BM_GetIndex(l->next)].newv;
			if (l->radial_next != l) {
				v3 = tags[BM_GetIndex(l->radial_next)].newv;
				if (l->radial_next->next->v == l->next->v) {
					v4 = v3;
					v3 = tags[BM_GetIndex(l->radial_next->next)].newv;
				}
				else {
					v4 = tags[BM_GetIndex(l->radial_next->next)].newv;
				}
			}
			else {
				/* the loop is on a boundar */
				v3 = l->next->v;
				v4 = l->v;
				
				for (j = 0; j < 2; j++) {
					BMIter eiter;
					BMVert *v = j ? v4 : v3;

					BM_ITER(e, &eiter, bm, BM_EDGES_OF_VERT, v) {
						if (!BM_Vert_In_Edge(e, v3) || !BM_Vert_In_Edge(e, v4))
							continue;
						
						if (!BMO_TestFlag(bm, e, BEVEL_FLAG) && BMO_TestFlag(bm, e, EDGE_OLD)) {
							BMVert *vv;
							
							vv = ETAG_GET(e, v);
							if (!vv || BMO_TestFlag(bm, vv, BEVEL_FLAG))
								continue;
							
							if (j)
								v1 = vv;
							else
								v2 = vv;
							break;
						}
					}
				}

				BMO_ClearFlag(bm, v3, BEVEL_DEL);
				BMO_ClearFlag(bm, v4, BEVEL_DEL);
			}
			
			if (v1 != v2 && v2 != v3 && v3 != v4) {
				BMIter liter2;
				BMLoop *l2, *l3;
				BMEdge *e1, *e2;
				float d1, d2, *d3;
				
				f = BM_Make_Face_QuadTri(bm, v4, v3, v2, v1, l->f, 1);

				e1 = BM_Edge_Exist(v4, v3);
				e2 = BM_Edge_Exist(v2, v1);
				BM_Copy_Attributes(bm, bm, l->e, e1);
				BM_Copy_Attributes(bm, bm, l->e, e2);
				
				/* set edge lengths of cross edges as the average of the cross edges they're based o */
				if (has_elens) {
					/* angle happens not to be used. why? - not sure it just isnt - campbell.
					 * leave this in incase we need to use it later */
#if 0
					float ang;
#endif
					e1 = BM_Edge_Exist(v1, v4);
					e2 = BM_Edge_Exist(v2, v3);
					
					if (l->radial_next->v == l->v) {
						l2 = l->radial_next->prev;
						l3 = l->radial_next->next;
					}
					else {
						l2 = l->radial_next->next;
						l3 = l->radial_next->prev;
					}
					
					d3 = CustomData_bmesh_get_n(&bm->edata, e1->head.data, CD_PROP_FLT, li);
					d1 = *(float *)CustomData_bmesh_get_n(&bm->edata, l->prev->e->head.data, CD_PROP_FLT, li);
					d2 = *(float *)CustomData_bmesh_get_n(&bm->edata, l2->e->head.data, CD_PROP_FLT, li);
#if 0
					ang = angle_v3v3v3(l->prev->v->co, l->v->co, BM_OtherEdgeVert(l2->e, l->v)->co);
#endif
					*d3 = (d1 + d2) * 0.5f;
					
					d3 = CustomData_bmesh_get_n(&bm->edata, e2->head.data, CD_PROP_FLT, li);
					d1 = *(float *)CustomData_bmesh_get_n(&bm->edata, l->next->e->head.data, CD_PROP_FLT, li);
					d2 = *(float *)CustomData_bmesh_get_n(&bm->edata, l3->e->head.data, CD_PROP_FLT, li);
#if 0
					ang = angle_v3v3v3(BM_OtherEdgeVert(l->next->e, l->next->v)->co, l->next->v->co,
					                   BM_OtherEdgeVert(l3->e, l->next->v)->co);
#endif
					*d3 = (d1 + d2) * 0.5f;
				}

				if (!f) {
					fprintf(stderr, "%s: face index out of range! (bmesh internal error)\n", __func__);
					continue;
				}
				
				BMO_SetFlag(bm, f, FACE_NEW|FACE_SPAN);
				
				/* un-tag edges in f for deletio */
				BM_ITER(l2, &liter2, bm, BM_LOOPS_OF_FACE, f) {
					BMO_ClearFlag(bm, l2->e, BEVEL_DEL);
				}
			}
			else {
				f = NULL;
			}
		}	
	}
	
	/* fill in holes at vertices */
	BM_ITER(v, &iter, bm, BM_VERTS_OF_MESH, NULL) {
		BMIter eiter;
		BMVert *vv, *vstart = NULL, *lastv = NULL;
		SmallHash tmphash;
		int rad, insorig = 0, err = 0;

		BLI_smallhash_init(&tmphash);
				
		if (!BMO_TestFlag(bm, v, BEVEL_FLAG))
			continue;
		
		BLI_array_empty(verts);
		BLI_array_empty(edges);
		
		BM_ITER(e, &eiter, bm, BM_EDGES_OF_VERT, v) {
			BMIter liter;
			BMVert *v1 = NULL, *v2 = NULL;
			BMLoop *l;
			
			if (BM_Edge_FaceCount(e) < 2)
				insorig = 1;
			
			if (BM_GetIndex(e) == -1)
				continue;
			
			rad = 0;
			BM_ITER(l, &liter, bm, BM_LOOPS_OF_EDGE, e) {
				if (!BMO_TestFlag(bm, l->f, FACE_OLD))
					continue;
				
				rad++;
				
				tag = tags + BM_GetIndex((l->v == v) ? l : l->next);
				
				if (!v1)
					v1 = tag->newv;
				else if (!v2)
					v2 = tag->newv;
			}
			
			if (rad < 2)
				insorig = 1;
			
			if (!v1)
				v1 = ETAG_GET(e, v);
			if (!v2 || v1 == v2)
				v2 = ETAG_GET(e, v);
			
			if (v1) {
				if (!BLI_smallhash_haskey(&tmphash, (intptr_t)v1)) {
					BLI_array_append(verts, v1);
					BLI_smallhash_insert(&tmphash, (intptr_t)v1, NULL);
				}
				
				if (v2 && v1 != v2 && !BLI_smallhash_haskey(&tmphash, (intptr_t)v2)) {
					BLI_array_append(verts, v2);
					BLI_smallhash_insert(&tmphash, (intptr_t)v2, NULL);
				}
			}
		}
		
		if (!BLI_array_count(verts))
			continue;
		
		if (insorig) {
			BLI_array_append(verts, v);
			BLI_smallhash_insert(&tmphash, (intptr_t)v, NULL);
		}
		
		/* find edges that exist between vertices in verts.  this is basically
		 * a topological walk of the edges connecting them */
		vstart = vstart ? vstart : verts[0];
		vv = vstart;
		do {
			BM_ITER(e, &eiter, bm, BM_EDGES_OF_VERT, vv) {
				BMVert *vv2 = BM_OtherEdgeVert(e, vv);
				
				if (vv2 != lastv && BLI_smallhash_haskey(&tmphash, (intptr_t)vv2)) {
					/* if we've go over the same vert twice, break out of outer loop */
					if (BLI_smallhash_lookup(&tmphash, (intptr_t)vv2) != NULL) {
						e = NULL;
						err = 1;
						break;
					}
					
					/* use self pointer as ta */
					BLI_smallhash_remove(&tmphash, (intptr_t)vv2);
					BLI_smallhash_insert(&tmphash, (intptr_t)vv2, vv2);
					
					lastv = vv;
					BLI_array_append(edges, e);
					vv = vv2;
					break;
				}
			}

			if (e == NULL) {
				break;
			}
		} while (vv != vstart);
		
		if (err) {
			continue;
		}

		/* there may not be a complete loop of edges, so start again and make
		 * final edge afterwards.  in this case, the previous loop worked to
		 * find one of the two edges at the extremes. */
		if (vv != vstart) {
			/* undo previous taggin */
			for (i = 0; i < BLI_array_count(verts); i++) {
				BLI_smallhash_remove(&tmphash, (intptr_t)verts[i]);
				BLI_smallhash_insert(&tmphash, (intptr_t)verts[i], NULL);
			}

			vstart = vv;
			lastv = NULL;
			BLI_array_empty(edges);
			do {
				BM_ITER(e, &eiter, bm, BM_EDGES_OF_VERT, vv) {
					BMVert *vv2 = BM_OtherEdgeVert(e, vv);
					
					if (vv2 != lastv && BLI_smallhash_haskey(&tmphash, (intptr_t)vv2)) {
						/* if we've go over the same vert twice, break out of outer loo */
						if (BLI_smallhash_lookup(&tmphash, (intptr_t)vv2) != NULL) {
							e = NULL;
							err = 1;
							break;
						}
						
						/* use self pointer as ta */
						BLI_smallhash_remove(&tmphash, (intptr_t)vv2);
						BLI_smallhash_insert(&tmphash, (intptr_t)vv2, vv2);
						
						lastv = vv;
						BLI_array_append(edges, e);
						vv = vv2;
						break;
					}
				}
				if (e == NULL)
					break;
			} while (vv != vstart);
			
			if (!err) {
				e = BM_Make_Edge(bm, vv, vstart, NULL, 1);
				BLI_array_append(edges, e);
			}
		}
		
		if (err)
			continue;
		
		if (BLI_array_count(edges) >= 3) {
			BMFace *f;
			
			if (BM_Face_Exists(bm, verts, BLI_array_count(verts), &f))
				continue;
			
			f = BM_Make_Ngon(bm, lastv, vstart, edges, BLI_array_count(edges), 0);
			if (!f) {
				fprintf(stderr, "%s: in bevel vert fill! (bmesh internal error)\n", __func__);
			}
			else {
				BMO_SetFlag(bm, f, FACE_NEW|FACE_HOLE);
			}
		}
		BLI_smallhash_release(&tmphash);
	}
	
	/* copy over customdat */
	for (i = 0; i < BLI_array_count(faces); i++) {
		BMLoop *l;
		BMIter liter;
		BMFace *f = faces[i];
		
		BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, f) {
			BMLoop *l2;
			BMIter liter2;
			
			tag = tags + BM_GetIndex(l);
			if (!tag->newv)
				continue;
			
			BM_ITER(l2, &liter2, bm, BM_LOOPS_OF_VERT, tag->newv) {
				if (!BMO_TestFlag(bm, l2->f, FACE_NEW) || (l2->v != tag->newv && l2->v != l->v))
					continue;
				
				if (tag->newv != l->v || HasMDisps) {
					BM_Copy_Attributes(bm, bm, l->f, l2->f);
					BM_loop_interp_from_face(bm, l2, l->f, 1, 1);
				}
				else {
					BM_Copy_Attributes(bm, bm, l->f, l2->f);
					BM_Copy_Attributes(bm, bm, l, l2);
				}
				
				if (HasMDisps) {
					BMLoop *l3;
					BMIter liter3;
					
					BM_ITER(l3, &liter3, bm, BM_LOOPS_OF_FACE, l2->f) {
						BM_loop_interp_multires(bm, l3, l->f);
					}
				}
			}
		}
	}
	
	/* handle vertices along boundary edge */
	BM_ITER(v, &iter, bm, BM_VERTS_OF_MESH, NULL) {
		if (BMO_TestFlag(bm, v, VERT_OLD) && BMO_TestFlag(bm, v, BEVEL_FLAG) && !BMO_TestFlag(bm, v, BEVEL_DEL)) {
			BMLoop *l;
			BMLoop *lorig = NULL;
			BMIter liter;
			
			BM_ITER(l, &liter, bm, BM_LOOPS_OF_VERT, v) {
				// BMIter liter2;
				// BMLoop *l2 = l->v == v ? l : l->next, *l3;
				
				if (BMO_TestFlag(bm, l->f, FACE_OLD)) {
					lorig = l;
					break;
				}
			}
			
			if (!lorig)
				continue;
			
			BM_ITER(l, &liter, bm, BM_LOOPS_OF_VERT, v) {
				BMLoop *l2 = l->v == v ? l : l->next;
				
				BM_Copy_Attributes(bm, bm, lorig->f, l2->f);
				BM_Copy_Attributes(bm, bm, lorig, l2);
			}
		}
	}
#if 0
	/* clean up any remaining 2-edged face */
	BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
		if (f->len == 2) {
			BMFace *faces[2] = {f, BM_FACE_FIRST_LOOP(f)->radial_next->f};
			
			if (faces[0] == faces[1])
				BM_Kill_Face(bm, f);
			else
				BM_Join_Faces(bm, faces, 2);
		}
	}
#endif
	
	BMO_CallOpf(bm, "del geom=%fv context=%i", BEVEL_DEL, DEL_VERTS);

	/* clean up any edges that might not get properly delete */
	BM_ITER(e, &iter, bm, BM_EDGES_OF_MESH, NULL) {
		if (BMO_TestFlag(bm, e, EDGE_OLD) && !e->l)
			BMO_SetFlag(bm, e, BEVEL_DEL);
	}

	BMO_CallOpf(bm, "del geom=%fe context=%i", BEVEL_DEL, DEL_EDGES);
	BMO_CallOpf(bm, "del geom=%ff context=%i", BEVEL_DEL, DEL_FACES);
	
	BLI_smallhash_release(&hash);
	BLI_array_free(tags);
	BLI_array_free(etags);
	BLI_array_free(verts);
	BLI_array_free(edges);
	BLI_array_free(faces);
	
	BMO_Flag_To_Slot(bm, op, "face_spans", FACE_SPAN, BM_FACE);
	BMO_Flag_To_Slot(bm, op, "face_holes", FACE_HOLE, BM_FACE);
}
