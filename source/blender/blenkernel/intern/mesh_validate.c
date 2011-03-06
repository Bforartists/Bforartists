/*
 * $Id$
 *
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
 * The Original Code is Copyright (C) 2011 Blender Foundation.
 * All rights reserved.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenkernel/intern/mesh_validate.c
 *  \ingroup bke
 */


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"

#include "BLO_sys_types.h"

#include "BLI_utildefines.h"
#include "BLI_edgehash.h"

#include "BKE_DerivedMesh.h"

#include "MEM_guardedalloc.h"

#include "BKE_mesh.h"

#define SELECT 1

typedef union {
	uint32_t verts[2];
	int64_t edval;
} EdgeUUID;

typedef struct SortFace {
//	unsigned int	v[4];
	EdgeUUID		es[4];
	unsigned int	index;
} SortFace;

static void edge_store_assign(uint32_t verts[2],  const uint32_t v1, const uint32_t v2)
{
	if(v1 < v2) {
		verts[0]= v1;
		verts[1]= v2;
	}
	else {
		verts[0]= v2;
		verts[1]= v1;
	}
}

static void edge_store_from_mface_quad(EdgeUUID es[4], MFace *mf)
{
	edge_store_assign(es[0].verts, mf->v1, mf->v2);
	edge_store_assign(es[1].verts, mf->v2, mf->v3);
	edge_store_assign(es[2].verts, mf->v3, mf->v4);
	edge_store_assign(es[3].verts, mf->v4, mf->v1);
}

static void edge_store_from_mface_tri(EdgeUUID es[3], MFace *mf)
{
	edge_store_assign(es[0].verts, mf->v1, mf->v2);
	edge_store_assign(es[1].verts, mf->v2, mf->v3);
	edge_store_assign(es[2].verts, mf->v3, mf->v1);
	es[3].verts[0] = es[3].verts[1] = UINT_MAX;
}

static int int64_cmp(const void *v1, const void *v2)
{
	const int64_t x1= *(const int64_t *)v1;
	const int64_t x2= *(const int64_t *)v2;

	if( x1 > x2 ) return 1;
	else if( x1 < x2 ) return -1;
	return 0;
}

static int search_face_cmp(const void *v1, const void *v2)
{
	const SortFace *sfa= v1, *sfb= v2;

	if	(sfa->es[0].edval > sfb->es[0].edval) return 1;
	else if	(sfa->es[0].edval < sfb->es[0].edval) return -1;

	else if	(sfa->es[1].edval > sfb->es[1].edval) return 1;
	else if	(sfa->es[1].edval < sfb->es[1].edval) return -1;

	else if	(sfa->es[2].edval > sfb->es[2].edval) return 1;
	else if	(sfa->es[2].edval < sfb->es[2].edval) return -1;

	else if	(sfa->es[3].edval > sfb->es[3].edval) return 1;
	else if	(sfa->es[3].edval < sfb->es[3].edval) return -1;
	else										  return 0;

}

int BKE_mesh_validate_arrays(Mesh *me, MVert *UNUSED(mverts), unsigned int totvert, MEdge *medges, unsigned int totedge, MFace *mfaces, unsigned int totface, const short do_verbose, const short do_fixes)
{
#	define PRINT if(do_verbose) printf
#	define REMOVE_EDGE_TAG(_med) { _med->v2= _med->v1; do_edge_free= 1; }
#	define REMOVE_FACE_TAG(_mf) { _mf->v3=0; do_face_free= 1; }

//	MVert *mv;
	MEdge *med;
	MFace *mf;
	MFace *mf_prev;
	unsigned int i;

	int do_face_free= FALSE;
	int do_edge_free= FALSE;

	int do_edge_recalc= FALSE;

	EdgeHash *edge_hash = BLI_edgehash_new();

	SortFace *sort_faces= MEM_callocN(sizeof(SortFace) * totface, "search faces");
	SortFace *sf;
	SortFace *sf_prev;
	unsigned int totsortface= 0;

	BLI_assert(!(do_fixes && me == NULL));

	PRINT("ED_mesh_validate: verts(%d), edges(%d), faces(%d)\n", totvert, totedge, totface);

	if(totedge == 0 && totface != 0) {
		PRINT("    locical error, %d faces and 0 edges\n", totface);
		do_edge_recalc= TRUE;
	}

	for(i=0, med= medges; i<totedge; i++, med++) {
		int remove= FALSE;
		if(med->v1 == med->v2) {
			PRINT("    edge %d: has matching verts, both %d\n", i, med->v1);
			remove= do_fixes;
		}
		if(med->v1 >= totvert) {
			PRINT("    edge %d: v1 index out of range, %d\n", i, med->v1);
			remove= do_fixes;
		}
		if(med->v2 >= totvert) {
			PRINT("    edge %d: v2 index out of range, %d\n", i, med->v2);
			remove= do_fixes;
		}

		if(BLI_edgehash_haskey(edge_hash, med->v1, med->v2)) {
			PRINT("    edge %d: is a duplicate of, %d\n", i, GET_INT_FROM_POINTER(BLI_edgehash_lookup(edge_hash, med->v1, med->v2)));
			remove= do_fixes;
		}

		if(remove == FALSE){
			BLI_edgehash_insert(edge_hash, med->v1, med->v2, SET_INT_IN_POINTER(i));
		}
		else {
			REMOVE_EDGE_TAG(med);
		}
	}

	for(i=0, mf=mfaces, sf=sort_faces; i<totface; i++, mf++) {
		int remove= FALSE;
		int fidx;
		unsigned int fv[4];

		fidx = mf->v4 ? 3:2;
		do {
			fv[fidx]= *(&(mf->v1) + fidx);
			if(fv[fidx] >= totvert) {
				PRINT("    face %d: 'v%d' index out of range, %d\n", i, fidx + 1, fv[fidx]);
				remove= do_fixes;
			}
		} while (fidx--);

		if(remove == FALSE) {
			if(mf->v4) {
				if(mf->v1 == mf->v2) { PRINT("    face %d: verts invalid, v1/v2 both %d\n", i, mf->v1); remove= do_fixes; }
				if(mf->v1 == mf->v3) { PRINT("    face %d: verts invalid, v1/v3 both %d\n", i, mf->v1); remove= do_fixes;  }
				if(mf->v1 == mf->v4) { PRINT("    face %d: verts invalid, v1/v4 both %d\n", i, mf->v1); remove= do_fixes;  }

				if(mf->v2 == mf->v3) { PRINT("    face %d: verts invalid, v2/v3 both %d\n", i, mf->v2); remove= do_fixes;  }
				if(mf->v2 == mf->v4) { PRINT("    face %d: verts invalid, v2/v4 both %d\n", i, mf->v2); remove= do_fixes;  }

				if(mf->v3 == mf->v4) { PRINT("    face %d: verts invalid, v3/v4 both %d\n", i, mf->v3); remove= do_fixes;  }
			}
			else {
				if(mf->v1 == mf->v2) { PRINT("    faceT %d: verts invalid, v1/v2 both %d\n", i, mf->v1); remove= do_fixes; }
				if(mf->v1 == mf->v3) { PRINT("    faceT %d: verts invalid, v1/v3 both %d\n", i, mf->v1); remove= do_fixes; }

				if(mf->v2 == mf->v3) { PRINT("    faceT %d: verts invalid, v2/v3 both %d\n", i, mf->v2); remove= do_fixes; }
			}

			if(remove == FALSE) {
				if(totedge) {
					if(mf->v4) {
						if(!BLI_edgehash_haskey(edge_hash, mf->v1, mf->v2)) { PRINT("    face %d: edge v1/v2 (%d,%d) is missing egde data\n", i, mf->v1, mf->v2); do_edge_recalc= TRUE; }
						if(!BLI_edgehash_haskey(edge_hash, mf->v2, mf->v3)) { PRINT("    face %d: edge v2/v3 (%d,%d) is missing egde data\n", i, mf->v2, mf->v3); do_edge_recalc= TRUE; }
						if(!BLI_edgehash_haskey(edge_hash, mf->v3, mf->v4)) { PRINT("    face %d: edge v3/v4 (%d,%d) is missing egde data\n", i, mf->v3, mf->v4); do_edge_recalc= TRUE; }
						if(!BLI_edgehash_haskey(edge_hash, mf->v4, mf->v1)) { PRINT("    face %d: edge v4/v1 (%d,%d) is missing egde data\n", i, mf->v4, mf->v1); do_edge_recalc= TRUE; }
					}
					else {
						if(!BLI_edgehash_haskey(edge_hash, mf->v1, mf->v2)) { PRINT("    face %d: edge v1/v2 (%d,%d) is missing egde data\n", i, mf->v1, mf->v2); do_edge_recalc= TRUE; }
						if(!BLI_edgehash_haskey(edge_hash, mf->v2, mf->v3)) { PRINT("    face %d: edge v2/v3 (%d,%d) is missing egde data\n", i, mf->v2, mf->v3); do_edge_recalc= TRUE; }
						if(!BLI_edgehash_haskey(edge_hash, mf->v3, mf->v1)) { PRINT("    face %d: edge v3/v1 (%d,%d) is missing egde data\n", i, mf->v3, mf->v1); do_edge_recalc= TRUE; }
					}
				}

				sf->index = i;

				if(mf->v4) {
					edge_store_from_mface_quad(sf->es, mf);

					qsort(sf->es, 4, sizeof(int64_t), int64_cmp);
				}
				else {
					edge_store_from_mface_tri(sf->es, mf);
					qsort(sf->es, 3, sizeof(int64_t), int64_cmp);
				}

				totsortface++;
				sf++;
			}
		}
		if(remove) {
			REMOVE_FACE_TAG(mf);
		}
	}

	qsort(sort_faces, totsortface, sizeof(SortFace), search_face_cmp);

	sf= sort_faces;
	sf_prev= sf;
	sf++;

	for(i=1; i<totsortface; i++, sf++) {
		int remove= FALSE;
		/* on a valid mesh, code below will never run */
		if(memcmp(sf->es, sf_prev->es, sizeof(sf_prev->es)) == 0) {
			mf= mfaces + sf->index;

			if(do_verbose) {
				mf_prev= mfaces + sf_prev->index;
				if(mf->v4) {
					PRINT("    face %d & %d: are duplicates (%d,%d,%d,%d) (%d,%d,%d,%d)\n", sf->index, sf_prev->index, mf->v1, mf->v2, mf->v3, mf->v4, mf_prev->v1, mf_prev->v2, mf_prev->v3, mf_prev->v4);
				}
				else {
					PRINT("    face %d & %d: are duplicates (%d,%d,%d) (%d,%d,%d)\n", sf->index, sf_prev->index, mf->v1, mf->v2, mf->v3, mf_prev->v1, mf_prev->v2, mf_prev->v3);
				}
			}

			remove= do_fixes;
		}
		else {
			sf_prev= sf;
		}

		if(remove) {
			REMOVE_FACE_TAG(mf);
		}
	}

	BLI_edgehash_free(edge_hash, NULL);
	MEM_freeN(sort_faces);

	PRINT("BKE_mesh_validate: finished\n\n");

#	 undef PRINT
#	 undef REMOVE_EDGE_TAG
#	 undef REMOVE_FACE_TAG

	if(me) {
		if(do_face_free) {
			mesh_strip_loose_faces(me);
		}

		if (do_edge_free) {
			mesh_strip_loose_edges(me);
		}

		if(do_fixes && do_edge_recalc) {
			BKE_mesh_calc_edges(me, TRUE);
		}
	}

	return (do_face_free || do_edge_free || do_edge_recalc);
}

int BKE_mesh_validate(Mesh *me, int do_verbose)
{
	printf("MESH: %s\n", me->id.name+2);
	return BKE_mesh_validate_arrays(me, me->mvert, me->totvert, me->medge, me->totedge, me->mface, me->totface, do_verbose, TRUE);
}

int BKE_mesh_validate_dm(DerivedMesh *dm)
{
	return BKE_mesh_validate_arrays(NULL, dm->getVertArray(dm), dm->getNumVerts(dm), dm->getEdgeArray(dm), dm->getNumEdges(dm), dm->getFaceArray(dm), dm->getNumFaces(dm), TRUE, FALSE);
}

void BKE_mesh_calc_edges(Mesh *mesh, int update)
{
	CustomData edata;
	EdgeHashIterator *ehi;
	MFace *mf = mesh->mface;
	MEdge *med, *med_orig;
	EdgeHash *eh = BLI_edgehash_new();
	int i, totedge, totface = mesh->totface;

	if(mesh->totedge==0)
		update= 0;

	if(update) {
		/* assume existing edges are valid
		 * useful when adding more faces and generating edges from them */
		med= mesh->medge;
		for(i= 0; i<mesh->totedge; i++, med++)
			BLI_edgehash_insert(eh, med->v1, med->v2, med);
	}

	for (i = 0; i < totface; i++, mf++) {
		if (!BLI_edgehash_haskey(eh, mf->v1, mf->v2))
			BLI_edgehash_insert(eh, mf->v1, mf->v2, NULL);
		if (!BLI_edgehash_haskey(eh, mf->v2, mf->v3))
			BLI_edgehash_insert(eh, mf->v2, mf->v3, NULL);

		if (mf->v4) {
			if (!BLI_edgehash_haskey(eh, mf->v3, mf->v4))
				BLI_edgehash_insert(eh, mf->v3, mf->v4, NULL);
			if (!BLI_edgehash_haskey(eh, mf->v4, mf->v1))
				BLI_edgehash_insert(eh, mf->v4, mf->v1, NULL);
		} else {
			if (!BLI_edgehash_haskey(eh, mf->v3, mf->v1))
				BLI_edgehash_insert(eh, mf->v3, mf->v1, NULL);
		}
	}

	totedge = BLI_edgehash_size(eh);

	/* write new edges into a temporary CustomData */
	memset(&edata, 0, sizeof(edata));
	CustomData_add_layer(&edata, CD_MEDGE, CD_CALLOC, NULL, totedge);

	ehi = BLI_edgehashIterator_new(eh);
	med = CustomData_get_layer(&edata, CD_MEDGE);
	for(i = 0; !BLI_edgehashIterator_isDone(ehi);
		BLI_edgehashIterator_step(ehi), ++i, ++med) {

		if(update && (med_orig=BLI_edgehashIterator_getValue(ehi))) {
			*med= *med_orig; /* copy from the original */
		} else {
			BLI_edgehashIterator_getKey(ehi, (int*)&med->v1, (int*)&med->v2);
			med->flag = ME_EDGEDRAW|ME_EDGERENDER|SELECT; /* select for newly created meshes which are selected [#25595] */
		}
	}
	BLI_edgehashIterator_free(ehi);

	/* free old CustomData and assign new one */
	CustomData_free(&mesh->edata, mesh->totedge);
	mesh->edata = edata;
	mesh->totedge = totedge;

	mesh->medge = CustomData_get_layer(&mesh->edata, CD_MEDGE);

	BLI_edgehash_free(eh, NULL);
}
