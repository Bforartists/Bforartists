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

/** \file blender/bmesh/operators/bmo_dupe.c
 *  \ingroup bmesh
 *
 * Duplicate, Split, Split operators.
 */

#include "MEM_guardedalloc.h"

#include "BLI_array.h"
#include "BLI_math.h"

#include "bmesh.h"

#include "intern/bmesh_operators_private.h" /* own include */

/* local flag define */
#define DUPE_INPUT      1 /* input from operator */
#define DUPE_NEW        2
#define DUPE_DONE       4
// #define DUPE_MAPPED     8 // UNUSED

/**
 * COPY VERTEX
 *
 * Copy an existing vertex from one bmesh to another.
 */
static BMVert *copy_vertex(BMesh *source_mesh, BMVert *source_vertex, BMesh *target_mesh, GHash *vhash)
{
	BMVert *target_vertex = NULL;

	/* Create a new vertex */
	target_vertex = BM_vert_create(target_mesh, source_vertex->co, NULL, BM_CREATE_SKIP_CD);
	
	/* Insert new vertex into the vert hash */
	BLI_ghash_insert(vhash, source_vertex, target_vertex);
	
	/* Copy attributes */
	BM_elem_attrs_copy(source_mesh, target_mesh, source_vertex, target_vertex);
	
	/* Set internal op flags */
	BMO_elem_flag_enable(target_mesh, target_vertex, DUPE_NEW);
	
	return target_vertex;
}

/**
 * COPY EDGE
 *
 * Copy an existing edge from one bmesh to another.
 */
static BMEdge *copy_edge(BMOperator *op,
                         BMOpSlot *slot_boundarymap_out,
                         BMesh *source_mesh,
                         BMEdge *source_edge, BMesh *target_mesh,
                         GHash *vhash, GHash *ehash)
{
	BMEdge *target_edge = NULL;
	BMVert *target_vert1, *target_vert2;
	BMFace *face;
	BMIter fiter;
	int rlen;

	/* see if any of the neighboring faces are
	 * not being duplicated.  in that case,
	 * add it to the new/old map. */
	rlen = 0;
	for (face = BM_iter_new(&fiter, source_mesh, BM_FACES_OF_EDGE, source_edge);
	     face;
	     face = BM_iter_step(&fiter))
	{
		if (BMO_elem_flag_test(source_mesh, face, DUPE_INPUT)) {
			rlen++;
		}
	}

	/* Lookup v1 and v2 */
	target_vert1 = BLI_ghash_lookup(vhash, source_edge->v1);
	target_vert2 = BLI_ghash_lookup(vhash, source_edge->v2);
	
	/* Create a new edge */
	target_edge = BM_edge_create(target_mesh, target_vert1, target_vert2, NULL, BM_CREATE_SKIP_CD);
	
	/* add to new/old edge map if necassary */
	if (rlen < 2) {
		/* not sure what non-manifold cases of greater then three
		 * radial should do. */
		BMO_slot_map_elem_insert(op, slot_boundarymap_out, source_edge, target_edge);
	}

	/* Insert new edge into the edge hash */
	BLI_ghash_insert(ehash, source_edge, target_edge);
	
	/* Copy attributes */
	BM_elem_attrs_copy(source_mesh, target_mesh, source_edge, target_edge);
	
	/* Set internal op flags */
	BMO_elem_flag_enable(target_mesh, target_edge, DUPE_NEW);
	
	return target_edge;
}

/**
 * COPY FACE
 *
 * Copy an existing face from one bmesh to another.
 */
static BMFace *copy_face(BMOperator *op,
                         BMOpSlot *slot_facemap_out,
                         BMesh *source_mesh,
                         BMFace *source_face, BMesh *target_mesh,
                         GHash *vhash, GHash *ehash)
{
	/* BMVert *target_vert1, *target_vert2; */ /* UNUSED */
	BMVert **vtar = BLI_array_alloca(vtar, source_face->len);
	BMEdge **edar = BLI_array_alloca(edar, source_face->len);
	BMLoop *source_loop, *target_loop;
	BMFace *target_face = NULL;
	BMIter iter, iter2;
	int i;
	
	/* lookup the first and second vert */
#if 0 /* UNUSED */
	target_vert1 = BLI_ghash_lookup(vhash, BM_iter_new(&iter, source_mesh, BM_VERTS_OF_FACE, source_face));
	target_vert2 = BLI_ghash_lookup(vhash, BM_iter_step(&iter));
#else
	BM_iter_new(&iter, source_mesh, BM_VERTS_OF_FACE, source_face);
	BM_iter_step(&iter);
#endif

	/* lookup edge */
	BM_ITER_ELEM_INDEX (source_loop, &iter, source_face, BM_LOOPS_OF_FACE, i) {
		vtar[i] = BLI_ghash_lookup(vhash, source_loop->v);
		edar[i] = BLI_ghash_lookup(ehash, source_loop->e);
	}

	/* create new face */
	target_face = BM_face_create(target_mesh, vtar, edar, source_face->len, BM_CREATE_SKIP_CD);
	BMO_slot_map_elem_insert(op, slot_facemap_out, source_face, target_face);
	BMO_slot_map_elem_insert(op, slot_facemap_out, target_face, source_face);

	BM_elem_attrs_copy(source_mesh, target_mesh, source_face, target_face);

	/* mark the face for output */
	BMO_elem_flag_enable(target_mesh, target_face, DUPE_NEW);
	
	/* copy per-loop custom data */
	BM_ITER_ELEM (source_loop, &iter, source_face, BM_LOOPS_OF_FACE) {
		BM_ITER_ELEM (target_loop, &iter2, target_face, BM_LOOPS_OF_FACE) {
			if (BLI_ghash_lookup(vhash, source_loop->v) == target_loop->v) {
				BM_elem_attrs_copy(source_mesh, target_mesh, source_loop, target_loop);
				break;
			}
		}
	}

	return target_face;
}

/**
 * COPY MESH
 *
 * Internal Copy function.
 */
static void bmo_mesh_copy(BMOperator *op, BMesh *bm_src, BMesh *bm_dst)
{

	BMVert *v = NULL, *v2;
	BMEdge *e = NULL;
	BMFace *f = NULL;
	
	BMIter viter, eiter, fiter;
	GHash *vhash, *ehash;

	BMOpSlot *slot_boundary_map_out = BMO_slot_get(op->slots_out, "boundary_map.out");
	BMOpSlot *slot_face_map_out     = BMO_slot_get(op->slots_out, "face_map.out");
	BMOpSlot *slot_isovert_map_out  = BMO_slot_get(op->slots_out, "isovert_map.out");

	/* initialize pointer hashes */
	vhash = BLI_ghash_ptr_new("bmesh dupeops v");
	ehash = BLI_ghash_ptr_new("bmesh dupeops e");

	/* duplicate flagged vertices */
	BM_ITER_MESH (v, &viter, bm_src, BM_VERTS_OF_MESH) {
		if (BMO_elem_flag_test(bm_src, v, DUPE_INPUT) &&
		    !BMO_elem_flag_test(bm_src, v, DUPE_DONE))
		{
			BMIter iter;
			bool isolated = true;

			v2 = copy_vertex(bm_src, v, bm_dst, vhash);

			BM_ITER_ELEM (f, &iter, v, BM_FACES_OF_VERT) {
				if (BMO_elem_flag_test(bm_src, f, DUPE_INPUT)) {
					isolated = false;
					break;
				}
			}

			if (isolated) {
				BM_ITER_ELEM (e, &iter, v, BM_EDGES_OF_VERT) {
					if (BMO_elem_flag_test(bm_src, e, DUPE_INPUT)) {
						isolated = false;
						break;
					}
				}
			}

			if (isolated) {
				BMO_slot_map_elem_insert(op, slot_isovert_map_out, v, v2);
			}

			BMO_elem_flag_enable(bm_src, v, DUPE_DONE);
		}
	}

	/* now we dupe all the edges */
	BM_ITER_MESH (e, &eiter, bm_src, BM_EDGES_OF_MESH) {
		if (BMO_elem_flag_test(bm_src, e, DUPE_INPUT) &&
		    !BMO_elem_flag_test(bm_src, e, DUPE_DONE))
		{
			/* make sure that verts are copied */
			if (!BMO_elem_flag_test(bm_src, e->v1, DUPE_DONE)) {
				copy_vertex(bm_src, e->v1, bm_dst, vhash);
				BMO_elem_flag_enable(bm_src, e->v1, DUPE_DONE);
			}
			if (!BMO_elem_flag_test(bm_src, e->v2, DUPE_DONE)) {
				copy_vertex(bm_src, e->v2, bm_dst, vhash);
				BMO_elem_flag_enable(bm_src, e->v2, DUPE_DONE);
			}
			/* now copy the actual edge */
			copy_edge(op, slot_boundary_map_out, bm_src, e, bm_dst, vhash, ehash);
			BMO_elem_flag_enable(bm_src, e, DUPE_DONE);
		}
	}

	/* first we dupe all flagged faces and their elements from source */
	BM_ITER_MESH (f, &fiter, bm_src, BM_FACES_OF_MESH) {
		if (BMO_elem_flag_test(bm_src, f, DUPE_INPUT)) {
			/* vertex pass */
			BM_ITER_ELEM (v, &viter, f, BM_VERTS_OF_FACE) {
				if (!BMO_elem_flag_test(bm_src, v, DUPE_DONE)) {
					copy_vertex(bm_src, v, bm_dst, vhash);
					BMO_elem_flag_enable(bm_src, v, DUPE_DONE);
				}
			}

			/* edge pass */
			BM_ITER_ELEM (e, &eiter, f, BM_EDGES_OF_FACE) {
				if (!BMO_elem_flag_test(bm_src, e, DUPE_DONE)) {
					copy_edge(op, slot_boundary_map_out, bm_src, e, bm_dst, vhash, ehash);
					BMO_elem_flag_enable(bm_src, e, DUPE_DONE);
				}
			}

			copy_face(op, slot_face_map_out, bm_src, f, bm_dst, vhash, ehash);
			BMO_elem_flag_enable(bm_src, f, DUPE_DONE);
		}
	}
	
	/* free pointer hashes */
	BLI_ghash_free(vhash, NULL, NULL);
	BLI_ghash_free(ehash, NULL, NULL);
}

/**
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
 */
void bmo_duplicate_exec(BMesh *bm, BMOperator *op)
{
	BMOperator *dupeop = op;
	BMesh *bm2 = BMO_slot_ptr_get(op->slots_in, "dest");
	
	if (!bm2)
		bm2 = bm;

	/* flag input */
	BMO_slot_buffer_flag_enable(bm, dupeop->slots_in, "geom", BM_ALL_NOLOOP, DUPE_INPUT);

	/* use the internal copy function */
	bmo_mesh_copy(dupeop, bm, bm2);
	
	/* Output */
	/* First copy the input buffers to output buffers - original data */
	BMO_slot_copy(dupeop, slots_in,  "geom",
	              dupeop, slots_out, "geom_orig.out");

	/* Now alloc the new output buffers */
	BMO_slot_buffer_from_enabled_flag(bm, dupeop, dupeop->slots_out, "geom.out", BM_ALL_NOLOOP, DUPE_NEW);
}

#if 0 /* UNUSED */
/* executes the duplicate operation, feeding elements of
 * type flag etypeflag and header flag flag to it.  note,
 * to get more useful information (such as the mapping from
 * original to new elements) you should run the dupe op manually */
void BMO_dupe_from_flag(BMesh *bm, int htype, const char hflag)
{
	BMOperator dupeop;

	BMO_op_init(bm, &dupeop, "duplicate");
	BMO_slot_buffer_from_enabled_hflag(bm, &dupeop, "geom", htype, hflag);

	BMO_op_exec(bm, &dupeop);
	BMO_op_finish(bm, &dupeop);
}
#endif

/**
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
 */
void bmo_split_exec(BMesh *bm, BMOperator *op)
{
#define SPLIT_INPUT 1

	BMOperator *splitop = op;
	BMOperator dupeop;
	BMOperator delop;
	const bool use_only_faces = BMO_slot_bool_get(op->slots_in, "use_only_faces");

	/* initialize our sub-operator */
	BMO_op_init(bm, &dupeop, op->flag, "duplicate");
	BMO_op_init(bm, &delop, op->flag, "delete");
	
	BMO_slot_copy(splitop, slots_in, "geom",
	              &dupeop, slots_in, "geom");
	BMO_op_exec(bm, &dupeop);
	
	BMO_slot_buffer_flag_enable(bm, splitop->slots_in, "geom", BM_ALL_NOLOOP, SPLIT_INPUT);

	if (use_only_faces) {
		BMVert *v;
		BMEdge *e;
		BMFace *f;
		BMIter iter, iter2;
		int found;

		/* make sure to remove edges and verts we don't need */
		for (e = BM_iter_new(&iter, bm, BM_EDGES_OF_MESH, NULL); e; e = BM_iter_step(&iter)) {
			found = 0;
			f = BM_iter_new(&iter2, bm, BM_FACES_OF_EDGE, e);
			for ( ; f; f = BM_iter_step(&iter2)) {
				if (!BMO_elem_flag_test(bm, f, SPLIT_INPUT)) {
					found = 1;
					break;
				}
			}
			if (!found) {
				BMO_elem_flag_enable(bm, e, SPLIT_INPUT);
			}
		}

		for (v = BM_iter_new(&iter, bm, BM_VERTS_OF_MESH, NULL); v; v = BM_iter_step(&iter)) {
			found = 0;
			e = BM_iter_new(&iter2, bm, BM_EDGES_OF_VERT, v);
			for ( ; e; e = BM_iter_step(&iter2)) {
				if (!BMO_elem_flag_test(bm, e, SPLIT_INPUT)) {
					found = 1;
					break;
				}
			}
			if (!found) {
				BMO_elem_flag_enable(bm, v, SPLIT_INPUT);
			}
		}
	}

	/* connect outputs of dupe to delete, exluding keep geometry */
	BMO_slot_int_set(delop.slots_in, "context", DEL_FACES);
	BMO_slot_buffer_from_enabled_flag(bm, &delop, delop.slots_in, "geom", BM_ALL_NOLOOP, SPLIT_INPUT);
	
	BMO_op_exec(bm, &delop);

	/* now we make our outputs by copying the dupe output */
	BMO_slot_copy(&dupeop, slots_out, "geom.out",
	              splitop, slots_out, "geom.out");

	BMO_slot_copy(&dupeop, slots_out, "boundary_map.out",
	              splitop, slots_out, "boundary_map.out");

	BMO_slot_copy(&dupeop, slots_out, "isovert_map.out",
	              splitop, slots_out, "isovert_map.out");


	/* cleanup */
	BMO_op_finish(bm, &delop);
	BMO_op_finish(bm, &dupeop);

#undef SPLIT_INPUT
}


void bmo_delete_exec(BMesh *bm, BMOperator *op)
{
#define DEL_INPUT 1

	BMOperator *delop = op;

	/* Mark Buffer */
	BMO_slot_buffer_flag_enable(bm, delop->slots_in, "geom", BM_ALL_NOLOOP, DEL_INPUT);

	BMO_remove_tagged_context(bm, DEL_INPUT, BMO_slot_int_get(op->slots_in, "context"));

#undef DEL_INPUT
}

/**
 * Spin Operator
 *
 * Extrude or duplicate geometry a number of times,
 * rotating and possibly translating after each step
 */
void bmo_spin_exec(BMesh *bm, BMOperator *op)
{
	BMOperator dupop, extop;
	float cent[3], dvec[3];
	float axis[3];
	float rmat[3][3];
	float phi;
	int steps, do_dupli, a, usedvec;

	BMO_slot_vec_get(op->slots_in, "cent", cent);
	BMO_slot_vec_get(op->slots_in, "axis", axis);
	normalize_v3(axis);
	BMO_slot_vec_get(op->slots_in, "dvec", dvec);
	usedvec = !is_zero_v3(dvec);
	steps    = BMO_slot_int_get(op->slots_in,   "steps");
	phi      = BMO_slot_float_get(op->slots_in, "angle") / steps;
	do_dupli = BMO_slot_bool_get(op->slots_in,  "use_duplicate");

	axis_angle_normalized_to_mat3(rmat, axis, phi);

	BMO_slot_copy(op, slots_in,  "geom",
	              op, slots_out, "geom_last.out");
	for (a = 0; a < steps; a++) {
		if (do_dupli) {
			BMO_op_initf(bm, &dupop, op->flag, "duplicate geom=%S", op, "geom_last.out");
			BMO_op_exec(bm, &dupop);
			BMO_op_callf(bm, op->flag,
			             "rotate cent=%v matrix=%m3 space=%s verts=%S",
			             cent, rmat, op, "space", &dupop, "geom.out");
			BMO_slot_copy(&dupop, slots_out, "geom.out",
			              op,     slots_out, "geom_last.out");
			BMO_op_finish(bm, &dupop);
		}
		else {
			BMO_op_initf(bm, &extop, op->flag, "extrude_face_region geom=%S",
			             op, "geom_last.out");
			BMO_op_exec(bm, &extop);
			BMO_op_callf(bm, op->flag,
			             "rotate cent=%v matrix=%m3 space=%s verts=%S",
			             cent, rmat, op, "space", &extop, "geom.out");
			BMO_slot_copy(&extop, slots_out, "geom.out",
			              op,     slots_out, "geom_last.out");
			BMO_op_finish(bm, &extop);
		}

		if (usedvec) {
			mul_m3_v3(rmat, dvec);
			BMO_op_callf(bm, op->flag,
			             "translate vec=%v space=%s verts=%S",
			             dvec, op, "space", op, "geom_last.out");
		}
	}
}
