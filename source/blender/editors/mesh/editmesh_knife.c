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
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Joseph Eagar, Joshua Leung, Howard Trickey,
 *                 Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/mesh/editmesh_knife.c
 *  \ingroup edmesh
 */

#ifdef _MSC_VER
#  define _USE_MATH_DEFINES
#endif

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_array.h"
#include "BLI_math.h"
#include "BLI_rand.h"
#include "BLI_smallhash.h"
#include "BLI_scanfill.h"
#include "BLI_memarena.h"

#include "BKE_DerivedMesh.h"
#include "BKE_context.h"
#include "BKE_depsgraph.h"

#include "BIF_gl.h"
#include "BIF_glutil.h" /* for paint cursor */

#include "ED_screen.h"
#include "ED_space_api.h"
#include "ED_view3d.h"
#include "ED_mesh.h"

#include "WM_api.h"
#include "WM_types.h"

#include "DNA_scene_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"
#include "BKE_tessmesh.h"
#include "UI_resources.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "mesh_intern.h"

/* this code here is kindof messy. . .I might need to eventually rework it - joeedh */

#define KMAXDIST    10  /* max mouse distance from edge before not detecting it */

#define KNIFE_FLT_EPS          0.00001f
#define KNIFE_FLT_EPS_SQUARED  (KNIFE_FLT_EPS * KNIFE_FLT_EPS)

typedef struct KnifeColors {
	unsigned char line[3];
	unsigned char edge[3];
	unsigned char curpoint[3];
	unsigned char curpoint_a[4];
	unsigned char point[3];
	unsigned char point_a[4];
} KnifeColors;

/* knifetool operator */
typedef struct KnifeVert {
	BMVert *v; /* non-NULL if this is an original vert */
	ListBase edges;
	ListBase faces;

	float co[3], cageco[3], sco[3]; /* sco is screen coordinates for cageco */
	short flag, draw, isface, inspace;
} KnifeVert;

typedef struct Ref {
	struct Ref *next, *prev;
	void *ref;
} Ref;

typedef struct KnifeEdge {
	KnifeVert *v1, *v2;
	BMFace *basef; /* face to restrict face fill to */
	ListBase faces;
	int draw;

	BMEdge *e, *oe; /* non-NULL if this is an original edge */
} KnifeEdge;

typedef struct BMEdgeHit {
	KnifeEdge *kfe;
	float hit[3], cagehit[3];
	float realhit[3]; /* used in midpoint mode */
	float schit[3];
	float l; /* lambda along cut line */
	float perc; /* lambda along hit line */
	KnifeVert *v; /* set if snapped to a vert */
	BMFace *f;
} BMEdgeHit;

typedef struct KnifePosData {
	float co[3];
	float cage[3];

	/* At most one of vert, edge, or bmface should be non-NULL,
	 * saying whether the point is snapped to a vertex, edge, or in a face.
	 * If none are set, this point is in space and is_space should be true. */
	KnifeVert *vert;
	KnifeEdge *edge;
	BMFace *bmface;
	int is_space;

	int mval[2]; /* mouse screen position */
} KnifePosData;

/* struct for properties used while drawing */
typedef struct KnifeTool_OpData {
	ARegion *ar;        /* region that knifetool was activated in */
	void *draw_handle;  /* for drawing preview loop */
	ViewContext vc;
	//bContext *C;

	Object *ob;
	BMEditMesh *em;

	MemArena *arena;

	GHash *origvertmap;
	GHash *origedgemap;

	GHash *kedgefacemap;

	BMBVHTree *bmbvh;

	BLI_mempool *kverts;
	BLI_mempool *kedges;

	float vthresh;
	float ethresh;

	/* used for drag-cutting */
	BMEdgeHit *linehits;
	int totlinehit;

	/* Data for mouse-position-derived data (cur) and previous click (prev) */
	KnifePosData curr, prev;

	int totkedge, totkvert;

	BLI_mempool *refs;

	float projmat[4][4];

	KnifeColors colors;

	/* operatpr options */
	char cut_through;    /* preference, can be modified at runtime (that feature may go) */
	char only_select;    /* set on initialization */
	char select_result;  /* set on initialization */

	short is_ortho;
	float ortho_extent;
	float clipsta, clipend;

	enum {
		MODE_IDLE,
		MODE_DRAGGING,
		MODE_CONNECT,
		MODE_PANNING
	} mode;

	int snap_midpoints, prevmode, extend;
	int ignore_edge_snapping, ignore_vert_snapping;

	enum {
		ANGLE_FREE,
		ANGLE_0,
		ANGLE_45,
		ANGLE_90,
		ANGLE_135
	} angle_snapping;

	float (*cagecos)[3];
} KnifeTool_OpData;

static ListBase *knife_get_face_kedges(KnifeTool_OpData *kcd, BMFace *f);

#if 0
static void knife_input_ray_cast(KnifeTool_OpData *kcd, const int mval_i[2],
                                 float r_origin[3], float r_ray[3]);
#endif
static void knife_input_ray_segment(KnifeTool_OpData *kcd, const int mval_i[2], const float ofs,
                                    float r_origin[3], float r_dest[3]);

static void knife_update_header(bContext *C, KnifeTool_OpData *kcd)
{
	#define HEADER_LENGTH 190
	char header[HEADER_LENGTH];

	BLI_snprintf(header, HEADER_LENGTH, "LMB: define cut lines, Return/Spacebar: confirm, Esc or RMB: cancel, E: new cut, Ctrl: midpoint snap (%s), "
	             "Shift: ignore snap (%s), C: angle constrain (%s), Z: cut through (%s)",
	             kcd->snap_midpoints ? "On" : "Off",
	             kcd->ignore_edge_snapping ?  "On" : "Off",
	             kcd->angle_snapping ? "On" : "Off",
	             kcd->cut_through ? "On" : "Off");

	ED_area_headerprint(CTX_wm_area(C), header);
}


static void knife_project_v3(KnifeTool_OpData *kcd, const float co[3], float sco[3])
{
	ED_view3d_project_float_v3_m4(kcd->ar, co, sco, kcd->projmat);
}

static void knife_pos_data_clear(KnifePosData *kpd)
{
	zero_v3(kpd->co);
	zero_v3(kpd->cage);
	kpd->vert = NULL;
	kpd->edge = NULL;
	kpd->bmface = NULL;
	kpd->mval[0] = 0;
	kpd->mval[1] = 0;
}

static ListBase *knife_empty_list(KnifeTool_OpData *kcd)
{
	ListBase *lst;

	lst = BLI_memarena_alloc(kcd->arena, sizeof(ListBase));
	lst->first = lst->last = NULL;
	return lst;
}

static void knife_append_list(KnifeTool_OpData *kcd, ListBase *lst, void *elem)
{
	Ref *ref;

	ref = BLI_mempool_calloc(kcd->refs);
	ref->ref = elem;
	BLI_addtail(lst, ref);
}

static Ref *find_ref(ListBase *lb, void *ref)
{
	Ref *ref1;

	for (ref1 = lb->first; ref1; ref1 = ref1->next) {
		if (ref1->ref == ref)
			return ref1;
	}

	return NULL;
}

static KnifeEdge *new_knife_edge(KnifeTool_OpData *kcd)
{
	kcd->totkedge++;
	return BLI_mempool_calloc(kcd->kedges);
}

static void knife_add_to_vert_edges(KnifeTool_OpData *kcd, KnifeEdge *kfe)
{
	knife_append_list(kcd, &kfe->v1->edges, kfe);
	knife_append_list(kcd, &kfe->v2->edges, kfe);
}

/* Add faces of an edge to a KnifeVert's faces list.  No checks for dups. */
static void knife_add_edge_faces_to_vert(KnifeTool_OpData *kcd, KnifeVert *kfv, BMEdge *e)
{
	BMIter bmiter;
	BMFace *f;

	BM_ITER_ELEM(f, &bmiter, e, BM_FACES_OF_EDGE) {
		knife_append_list(kcd, &kfv->faces, f);
	}
}

/* Find a face in common in the two faces lists.
 * If more than one, return the first; if none, return NULL */
static BMFace *knife_find_common_face(ListBase *faces1, ListBase *faces2)
{
	Ref *ref1, *ref2;

	for (ref1 = faces1->first; ref1; ref1 = ref1->next) {
		for (ref2 = faces2->first; ref2; ref2 = ref2->next) {
			if (ref1->ref == ref2->ref)
				return (BMFace *)(ref1->ref);
		}
	}
	return NULL;
}

static KnifeVert *new_knife_vert(KnifeTool_OpData *kcd, const float co[3], float *cageco)
{
	KnifeVert *kfv = BLI_mempool_calloc(kcd->kverts);

	kcd->totkvert++;

	copy_v3_v3(kfv->co, co);
	copy_v3_v3(kfv->cageco, cageco);
	copy_v3_v3(kfv->sco, co);

	knife_project_v3(kcd, kfv->co, kfv->sco);

	return kfv;
}

/* get a KnifeVert wrapper for an existing BMVert */
static KnifeVert *get_bm_knife_vert(KnifeTool_OpData *kcd, BMVert *v)
{
	KnifeVert *kfv = BLI_ghash_lookup(kcd->origvertmap, v);

	if (!kfv) {
		BMIter bmiter;
		BMFace *f;

		kfv = new_knife_vert(kcd, v->co, kcd->cagecos[BM_elem_index_get(v)]);
		kfv->v = v;
		BLI_ghash_insert(kcd->origvertmap, v, kfv);
		BM_ITER_ELEM(f, &bmiter, v, BM_FACES_OF_VERT) {
			knife_append_list(kcd, &kfv->faces, f);
		}
	}

	return kfv;
}

/* get a KnifeEdge wrapper for an existing BMEdge */
static KnifeEdge *get_bm_knife_edge(KnifeTool_OpData *kcd, BMEdge *e)
{
	KnifeEdge *kfe = BLI_ghash_lookup(kcd->origedgemap, e);
	if (!kfe) {
		BMIter bmiter;
		BMFace *f;

		kfe = new_knife_edge(kcd);
		kfe->e = e;
		kfe->v1 = get_bm_knife_vert(kcd, e->v1);
		kfe->v2 = get_bm_knife_vert(kcd, e->v2);

		knife_add_to_vert_edges(kcd, kfe);

		BLI_ghash_insert(kcd->origedgemap, e, kfe);

		BM_ITER_ELEM(f, &bmiter, e, BM_FACES_OF_EDGE) {
			knife_append_list(kcd, &kfe->faces, f);
		}
	}

	return kfe;
}

/* User has just clicked for first time or first time after a restart (E key).
 * Copy the current position data into prev. */
static void knife_start_cut(KnifeTool_OpData *kcd)
{
	kcd->prev = kcd->curr;
	kcd->curr.is_space = 0; /*TODO: why do we do this? */

	if (kcd->prev.vert == NULL && kcd->prev.edge == NULL && is_zero_v3(kcd->prev.cage)) {
		/* Make prevcage a point on the view ray to mouse closest to a point on model: choose vertex 0 */
		float origin[3], origin_ofs[3];
		BMVert *v0;

		knife_input_ray_segment(kcd, kcd->curr.mval, 1.0f, origin, origin_ofs);
		v0 = BM_vert_at_index(kcd->em->bm, 0);
		if (v0) {
			closest_to_line_v3(kcd->prev.cage, v0->co, origin_ofs, origin);
			copy_v3_v3(kcd->prev.co, kcd->prev.cage); /*TODO: do we need this? */
			copy_v3_v3(kcd->curr.cage, kcd->prev.cage);
			copy_v3_v3(kcd->curr.co, kcd->prev.co);
		}
	}
}

static ListBase *knife_get_face_kedges(KnifeTool_OpData *kcd, BMFace *f)
{
	ListBase *lst = BLI_ghash_lookup(kcd->kedgefacemap, f);

	if (!lst) {
		BMIter bmiter;
		BMEdge *e;

		lst = knife_empty_list(kcd);

		BM_ITER_ELEM(e, &bmiter, f, BM_EDGES_OF_FACE) {
			knife_append_list(kcd, lst, get_bm_knife_edge(kcd, e));
		}

		BLI_ghash_insert(kcd->kedgefacemap, f, lst);
	}

	return lst;
}

/* finds the proper face to restrict face fill to */
static void knife_find_basef(KnifeEdge *kfe)
{
	kfe->basef = knife_find_common_face(&kfe->v1->faces, &kfe->v2->faces);
}

static void knife_edge_append_face(KnifeTool_OpData *kcd, KnifeEdge *kfe, BMFace *f)
{
	knife_append_list(kcd, knife_get_face_kedges(kcd, f), kfe);
	knife_append_list(kcd, &kfe->faces, f);
}

static KnifeVert *knife_split_edge(KnifeTool_OpData *kcd, KnifeEdge *kfe, float co[3], KnifeEdge **newkfe_out)
{
	KnifeEdge *newkfe = new_knife_edge(kcd);
	Ref *ref;
	BMFace *f;
	float perc, cageco[3], l12;

	l12 = len_v3v3(kfe->v1->co, kfe->v2->co);
	if (l12 < KNIFE_FLT_EPS) {
		copy_v3_v3(cageco, kfe->v1->cageco);
	}
	else {
		perc = len_v3v3(co, kfe->v1->co) / l12;
		interp_v3_v3v3(cageco, kfe->v1->cageco, kfe->v2->cageco, perc);
	}

	newkfe->v1 = kfe->v1;
	newkfe->v2 = new_knife_vert(kcd, co, cageco);
	newkfe->v2->draw = 1;
	if (kfe->e) {
		knife_add_edge_faces_to_vert(kcd, newkfe->v2, kfe->e);
	}
	else {
		/* kfe cuts across an existing face.
		 * If v1 and v2 are in multiple faces together (e.g., if they
		 * are in doubled polys) then this arbitrarily chooses one of them */
		f = knife_find_common_face(&kfe->v1->faces, &kfe->v2->faces);
		if (f)
			knife_append_list(kcd, &newkfe->v2->faces, f);
	}
	newkfe->basef = kfe->basef;

	ref = find_ref(&kfe->v1->edges, kfe);
	BLI_remlink(&kfe->v1->edges, ref);

	kfe->v1 = newkfe->v2;
	BLI_addtail(&kfe->v1->edges, ref);

	for (ref = kfe->faces.first; ref; ref = ref->next)
		knife_edge_append_face(kcd, newkfe, ref->ref);

	knife_add_to_vert_edges(kcd, newkfe);

	newkfe->draw = kfe->draw;
	newkfe->e = kfe->e;

	*newkfe_out = newkfe;

	return newkfe->v2;
}

/* Make a single KnifeEdge for cut from kcd->prev to kcd->curr.
 * and move cur data to prev. */
static void knife_add_single_cut(KnifeTool_OpData *kcd)
{
	KnifeEdge *kfe = new_knife_edge(kcd), *kfe2 = NULL, *kfe3 = NULL;

	if (kcd->prev.vert && kcd->prev.vert == kcd->curr.vert)
		return;
	if (kcd->prev.edge && kcd->prev.edge == kcd->curr.edge)
		return;

	kfe->draw = 1;

	if (kcd->prev.vert) {
		kfe->v1 = kcd->prev.vert;
	}
	else if (kcd->prev.edge) {
		kfe->v1 = knife_split_edge(kcd, kcd->prev.edge, kcd->prev.co, &kfe2);
	}
	else {
		kfe->v1 = new_knife_vert(kcd, kcd->prev.co, kcd->prev.co);
		kfe->v1->draw = kfe->draw = !kcd->prev.is_space;
		kfe->v1->inspace = kcd->prev.is_space;
		kfe->draw = !kcd->prev.is_space;
		kfe->v1->isface = 1;
		if (kfe->v1->draw && kcd->prev.bmface)
			knife_append_list(kcd, &kfe->v1->faces, kcd->prev.bmface);
	}

	if (kcd->curr.vert) {
		kfe->v2 = kcd->curr.vert;
	}
	else if (kcd->curr.edge) {
		kfe->v2 = knife_split_edge(kcd, kcd->curr.edge, kcd->curr.co, &kfe3);
		kcd->curr.vert = kfe->v2;
	}
	else {
		kfe->v2 = new_knife_vert(kcd, kcd->curr.co, kcd->curr.co);
		kfe->v2->draw = !kcd->curr.is_space;
		kfe->v2->isface = 1;
		kfe->v2->inspace = kcd->curr.is_space;
		if (kfe->v2->draw && kcd->curr.bmface)
			knife_append_list(kcd, &kfe->v2->faces, kcd->curr.bmface);

		if (kcd->curr.is_space)
			kfe->draw = 0;

		kcd->curr.vert = kfe->v2;
	}

	knife_find_basef(kfe);

	knife_add_to_vert_edges(kcd, kfe);

	if (kfe->basef && !find_ref(&kfe->faces, kfe->basef))
		knife_edge_append_face(kcd, kfe, kfe->basef);

	/* sanity check to make sure we're in the right edge/face lists */
	if (kcd->curr.bmface) {
		if (!find_ref(&kfe->faces, kcd->curr.bmface)) {
			knife_edge_append_face(kcd, kfe, kcd->curr.bmface);
		}

		if (kcd->prev.bmface && kcd->prev.bmface != kcd->curr.bmface) {
			if (!find_ref(&kfe->faces, kcd->prev.bmface)) {
				knife_edge_append_face(kcd, kfe, kcd->prev.bmface);
			}
		}
	}

	/* set up for next cut */
	kcd->prev = kcd->curr;
}

static int verge_linehit(const void *vlh1, const void *vlh2)
{
	const BMEdgeHit *lh1 = vlh1, *lh2 = vlh2;

	if      (lh1->l < lh2->l) return -1;
	else if (lh1->l > lh2->l) return 1;
	else return 0;
}

/* If there's a linehit connected (same face) as testi in range [firsti, lasti], return the first such, else -1.
 * If testi is out of range, look for connection to f instead, if f is non-NULL */
static int find_connected_linehit(KnifeTool_OpData *kcd, int testi, BMFace *f, int firsti, int lasti)
{
	int i;

	for (i = firsti; i <= lasti; i++) {
		if (testi >= 0 && testi < kcd->totlinehit) {
			if (knife_find_common_face(&kcd->linehits[testi].kfe->faces,
			                           &kcd->linehits[i].kfe->faces))
			{
				return i;
			}
		}
		else if (f) {
			if (find_ref(&kcd->linehits[i].kfe->faces, f))
				return i;
		}
	}
	return -1;
}

/* Sort in order of distance along cut line, but take care when distances are equal */
static void knife_sort_linehits(KnifeTool_OpData *kcd)
{
	int i, j, k, nexti, nsame;

	qsort(kcd->linehits, kcd->totlinehit, sizeof(BMEdgeHit), verge_linehit);

	/* for ranges of equal "l", swap if neccesary to make predecessor and
	 * successor faces connected to the linehits at either end of the range */
	for (i = 0; i < kcd->totlinehit - 1; i = nexti) {
		for (j = i + 1; j < kcd->totlinehit; j++) {
			if (fabsf(kcd->linehits[j].l - kcd->linehits[i].l) > KNIFE_FLT_EPS)
				break;
		}
		nexti = j;
		j--;
		nsame = j - i;
		if (nsame > 0) {
			/* find something connected to predecessor of equal range */
			k = find_connected_linehit(kcd, i - 1, kcd->prev.bmface, i, j);
			if (k != -1) {
				if (k != i) {
					SWAP(BMEdgeHit, kcd->linehits[i], kcd->linehits[k]);
				}
				i++;
				nsame--;
			}
			if (nsame > 0) {
				/* find something connected to successor of equal range */
				k = find_connected_linehit(kcd, j + 1, kcd->curr.bmface, i, j);
				if (k != -1 && k != j) {
					SWAP(BMEdgeHit, kcd->linehits[j], kcd->linehits[k]);
				}
			}
			/* rest of same range doesn't matter because we won't connect them */
		}
	}
}

static void knife_add_single_cut_through(KnifeTool_OpData *kcd, KnifeVert *v1, KnifeVert *v2, BMFace *f)
{
	KnifeEdge *kfenew;

	kfenew = new_knife_edge(kcd);
	kfenew->draw = 1;
	kfenew->basef = f;
	kfenew->v1 = v1;
	kfenew->v2 = v2;
	kfenew->draw = 1;

	knife_add_to_vert_edges(kcd, kfenew);

	if (!find_ref(&kfenew->faces, f))
		knife_edge_append_face(kcd, kfenew, f);
}

static void knife_get_vert_faces(KnifeTool_OpData *kcd, KnifeVert *kfv, BMFace *facef, ListBase *lst)
{
	BMIter bmiter;
	BMFace *f;

	if (kfv->isface && facef) {
		knife_append_list(kcd, lst, facef);
	}
	else if (kfv->v) {
		BM_ITER_ELEM (f, &bmiter, kfv->v, BM_FACES_OF_VERT) {
			knife_append_list(kcd, lst, f);
		}
	}
}

static void knife_get_edge_faces(KnifeTool_OpData *kcd, KnifeEdge *kfe, ListBase *lst)
{
	BMIter bmiter;
	BMFace *f;

	if (kfe->e) {
		BM_ITER_ELEM (f, &bmiter, kfe->e, BM_FACES_OF_EDGE) {
			knife_append_list(kcd, lst, f);
		}
	}
}

/* BMESH_TODO: add more functionality to cut-through:
 *    - cutting "in face" (e.g., holes) should cut in all faces, not just visible one
 *    - perhaps improve O(n^2) algorithm used here */
static void knife_cut_through(KnifeTool_OpData *kcd)
{
	BMEdgeHit *lh, *lh2;
	BMFace *f;
	KnifeEdge *kfe, *kfe2, *kfe3;
	KnifeVert *v1, *v2, *firstv = NULL, *lastv = NULL;
	ListBase firstfaces = {NULL, NULL}, lastfaces = {NULL, NULL};
	Ref *r, *r2;
	KnifeEdge **splitkfe;
	int i, j, found;

	if (!kcd->totlinehit) {
		/* if no linehits then no interesting back face stuff to do */
		knife_add_single_cut(kcd);
		return;
	}

	/* TODO: probably don't need to sort at all */
	qsort(kcd->linehits, kcd->totlinehit, sizeof(BMEdgeHit), verge_linehit);
	splitkfe = MEM_callocN(kcd->totlinehit * sizeof(KnifeEdge *), "knife_cut_through");

	if (kcd->prev.vert) {
		if (kcd->prev.vert == kcd->curr.vert)
			return;
		firstv = kcd->prev.vert;
		knife_get_vert_faces(kcd, firstv, kcd->prev.bmface, &firstfaces);
	}
	else if (kcd->prev.edge) {
		if (kcd->prev.edge == kcd->curr.edge)
			return;
		firstv = knife_split_edge(kcd, kcd->prev.edge, kcd->prev.co, &kfe3);
		knife_get_edge_faces(kcd, kcd->prev.edge, &firstfaces);
	}

	if (kcd->curr.vert) {
		lastv = kcd->curr.vert;
		knife_get_vert_faces(kcd, lastv, kcd->curr.bmface, &lastfaces);
	}
	else if (kcd->curr.edge) {
		lastv = knife_split_edge(kcd, kcd->curr.edge, kcd->curr.co, &kfe3);
		knife_get_edge_faces(kcd, kcd->curr.edge, &lastfaces);
	}

	if (firstv) {
		/* For each face incident to firstv,
		 * find the first following linehit (if any) sharing that face and connect */
		for (r = firstfaces.first; r; r = r->next) {
			f = r->ref;
			found = 0;
			for (j = 0, lh2 = kcd->linehits; j < kcd->totlinehit; j++, lh2++) {
				kfe2 = lh2->kfe;
				for (r2 = kfe2->faces.first; r2; r2 = r2->next) {
					if (r2->ref == f) {
						v2 = splitkfe[j] ? kfe2->v1 : knife_split_edge(kcd, kfe2, lh2->hit, &splitkfe[j]);
						knife_add_single_cut_through(kcd, firstv, v2, f);
						found = 1;
						break;
					}
				}
			}
			if (!found && lastv) {
				for (r2 = lastfaces.first; r2; r2 = r2->next) {
					if (r2->ref == f) {
						knife_add_single_cut_through(kcd, firstv, lastv, f);
						break;
					}
				}
			}
		}
	}

	for (i = 0, lh = kcd->linehits; i < kcd->totlinehit; i++, lh++) {
		kfe = lh->kfe;

		/* For each face attached to edge for this linehit,
		 * find the first following linehit (if any) sharing that face and connect */
		for (r = kfe->faces.first; r; r = r->next) {
			f = r->ref;
			found = 0;
			for (j = i + 1, lh2 = lh + 1; j < kcd->totlinehit; j++, lh2++) {
				kfe2 = lh2->kfe;
				for (r2 = kfe2->faces.first; r2; r2 = r2->next) {
					if (r2->ref == f) {
						v1 = splitkfe[i] ? kfe->v1 : knife_split_edge(kcd, kfe, lh->hit, &splitkfe[i]);
						v2 = splitkfe[j] ? kfe2->v1 : knife_split_edge(kcd, kfe2, lh2->hit, &splitkfe[j]);
						knife_add_single_cut_through(kcd, v1, v2, f);
						found = 1;
						break;
					}
				}
			}
			if (!found && lastv) {
				for (r2 = lastfaces.first; r2; r2 = r2->next) {
					if (r2->ref == f) {
						v1 = splitkfe[i] ? kfe->v1 : knife_split_edge(kcd, kfe, lh->hit, &splitkfe[i]);
						knife_add_single_cut_through(kcd, v1, lastv, f);
						break;
					}
				}
			}
		}
	}

	MEM_freeN(splitkfe);
	MEM_freeN(kcd->linehits);
	kcd->linehits = NULL;
	kcd->totlinehit = 0;

	/* set up for next cut */
	kcd->prev = kcd->curr;
}

/* User has just left-clicked after the first time.
 * Add all knife cuts implied by line from prev to curr.
 * If that line crossed edges then kcd->linehits will be non-NULL. */
static void knife_add_cut(KnifeTool_OpData *kcd)
{
	KnifePosData savcur = kcd->curr;

	if (kcd->cut_through) {
		knife_cut_through(kcd);
	}
	else if (kcd->linehits) {
		BMEdgeHit *lh, *lastlh, *firstlh;
		int i;

		knife_sort_linehits(kcd);

		lh = kcd->linehits;
		lastlh = firstlh = NULL;
		for (i = 0; i < kcd->totlinehit; i++, (lastlh = lh), lh++) {
			BMFace *f = lastlh ? lastlh->f : lh->f;

			if (lastlh && len_squared_v3v3(lastlh->hit, lh->hit) == 0.0f) {
				if (!firstlh)
					firstlh = lastlh;
				continue;
			}
			else if (lastlh && firstlh) {
				if (firstlh->v || lastlh->v) {
					KnifeVert *kfv = firstlh->v ? firstlh->v : lastlh->v;

					kcd->prev.vert = kfv;
					copy_v3_v3(kcd->prev.co, firstlh->hit);
					copy_v3_v3(kcd->prev.cage, firstlh->cagehit);
					kcd->prev.edge = NULL;
					kcd->prev.bmface = f;
					/* TODO: should we set prev.in_space = 0 ? */
				}
				lastlh = firstlh = NULL;
			}

			if (len_squared_v3v3(kcd->prev.cage, lh->realhit) < KNIFE_FLT_EPS_SQUARED)
				continue;
			if (len_squared_v3v3(kcd->curr.cage, lh->realhit) < KNIFE_FLT_EPS_SQUARED)
				continue;

			/* first linehit may be down face parallel to view */
			if (!lastlh && fabsf(lh->l) < KNIFE_FLT_EPS)
				continue;

			if (kcd->prev.is_space) {
				kcd->prev.is_space = 0;
				copy_v3_v3(kcd->prev.co, lh->hit);
				copy_v3_v3(kcd->prev.cage, lh->cagehit);
				kcd->prev.vert = NULL;
				kcd->prev.edge = lh->kfe;
				kcd->prev.bmface = lh->f;
				continue;
			}

			kcd->curr.is_space = 0;
			kcd->curr.edge = lh->kfe;
			kcd->curr.bmface = lh->f;
			kcd->curr.vert = lh->v;
			copy_v3_v3(kcd->curr.co, lh->hit);
			copy_v3_v3(kcd->curr.cage, lh->cagehit);

			/* don't draw edges down faces parallel to view */
			if (lastlh && fabsf(lastlh->l - lh->l) < KNIFE_FLT_EPS) {
				kcd->prev = kcd->curr;
				continue;
			}

			knife_add_single_cut(kcd);
		}

		if (savcur.is_space) {
			kcd->prev = savcur;
		}
		else {
			kcd->curr = savcur;
			knife_add_single_cut(kcd);
		}

		MEM_freeN(kcd->linehits);
		kcd->linehits = NULL;
		kcd->totlinehit = 0;
	}
	else {
		knife_add_single_cut(kcd);
	}
}

static void knife_finish_cut(KnifeTool_OpData *UNUSED(kcd))
{

}

static void knifetool_draw_angle_snapping(KnifeTool_OpData *kcd)
{
	bglMats mats;
	double u[3], u1[2], u2[2], v1[3], v2[3], dx, dy;
	double wminx, wminy, wmaxx, wmaxy;

	/* make u the window coords of prevcage */
	view3d_get_transformation(kcd->ar, kcd->vc.rv3d, kcd->ob, &mats);
	gluProject(kcd->prev.cage[0], kcd->prev.cage[1], kcd->prev.cage[2],
	           mats.modelview, mats.projection, mats.viewport,
	           &u[0], &u[1], &u[2]);

	/* make u1, u2 the points on window going through u at snap angle */
	wminx = kcd->ar->winrct.xmin;
	wmaxx = kcd->ar->winrct.xmin + kcd->ar->winx;
	wminy = kcd->ar->winrct.ymin;
	wmaxy = kcd->ar->winrct.ymin + kcd->ar->winy;

	switch (kcd->angle_snapping) {
		case ANGLE_0:
			u1[0] = wminx;
			u2[0] = wmaxx;
			u1[1] = u2[1] = u[1];
			break;
		case ANGLE_90:
			u1[0] = u2[0] = u[0];
			u1[1] = wminy;
			u2[1] = wmaxy;
			break;
		case ANGLE_45:
			/* clip against left or bottom */
			dx = u[0] - wminx;
			dy = u[1] - wminy;
			if (dy > dx) {
				u1[0] = wminx;
				u1[1] = u[1] - dx;
			}
			else {
				u1[0] = u[0] - dy;
				u1[1] = wminy;
			}
			/* clip against right or top */
			dx = wmaxx - u[0];
			dy = wmaxy - u[1];
			if (dy > dx) {
				u2[0] = wmaxx;
				u2[1] = u[1] + dx;
			}
			else {
				u2[0] = u[0] + dy;
				u2[1] = wmaxy;
			}
			break;
		case ANGLE_135:
			/* clip against right or bottom */
			dx = wmaxx - u[0];
			dy = u[1] - wminy;
			if (dy > dx) {
				u1[0] = wmaxx;
				u1[1] = u[1] - dx;
			}
			else {
				u1[0] = u[0] + dy;
				u1[1] = wminy;
			}
			/* clip against left or top */
			dx = u[0] - wminx;
			dy = wmaxy - u[1];
			if (dy > dx) {
				u2[0] = wminx;
				u2[1] = u[1] + dx;
			}
			else {
				u2[0] = u[0] - dy;
				u2[1] = wmaxy;
			}
			break;
		default:
			return;
	}

	/* unproject u1 and u2 back into object space */
	gluUnProject(u1[0], u1[1], 0.0,
	             mats.modelview, mats.projection, mats.viewport,
	             &v1[0], &v1[1], &v1[2]);
	gluUnProject(u2[0], u2[1], 0.0,
	             mats.modelview, mats.projection, mats.viewport,
	             &v2[0], &v2[1], &v2[2]);

	UI_ThemeColor(TH_TRANSFORM);
	glLineWidth(2.0);
	glBegin(GL_LINES);
	glVertex3dv(v1);
	glVertex3dv(v2);
	glEnd();
}

static void knife_init_colors(KnifeColors *colors)
{
	/* possible BMESH_TODO: add explicit themes or calculate these by
	 * figuring out contrasting colors with grid / edges / verts
	 * a la UI_make_axis_color */
	UI_GetThemeColor3ubv(TH_NURB_VLINE, colors->line);
	UI_GetThemeColor3ubv(TH_NURB_ULINE, colors->edge);
	UI_GetThemeColor3ubv(TH_HANDLE_SEL_VECT, colors->curpoint);
	UI_GetThemeColor3ubv(TH_HANDLE_SEL_VECT, colors->curpoint_a);
	colors->curpoint_a[3] = 102;
	UI_GetThemeColor3ubv(TH_ACTIVE_SPLINE, colors->point);
	UI_GetThemeColor3ubv(TH_ACTIVE_SPLINE, colors->point_a);
	colors->point_a[3] = 102;
}

/* modal loop selection drawing callback */
static void knifetool_draw(const bContext *C, ARegion *UNUSED(ar), void *arg)
{
	View3D *v3d = CTX_wm_view3d(C);
	KnifeTool_OpData *kcd = arg;

	if (v3d->zbuf) glDisable(GL_DEPTH_TEST);

	glPolygonOffset(1.0f, 1.0f);

	glPushMatrix();
	glMultMatrixf(kcd->ob->obmat);

	if (kcd->mode == MODE_DRAGGING) {
		if (kcd->angle_snapping != ANGLE_FREE)
			knifetool_draw_angle_snapping(kcd);

		glColor3ubv(kcd->colors.line);
		
		glLineWidth(2.0);

		glBegin(GL_LINES);
		glVertex3fv(kcd->prev.cage);
		glVertex3fv(kcd->curr.cage);
		glEnd();

		glLineWidth(1.0);
	}

	if (kcd->curr.edge) {
		glColor3ubv(kcd->colors.edge);
		glLineWidth(2.0);

		glBegin(GL_LINES);
		glVertex3fv(kcd->curr.edge->v1->cageco);
		glVertex3fv(kcd->curr.edge->v2->cageco);
		glEnd();

		glLineWidth(1.0);
	}
	else if (kcd->curr.vert) {
		glColor3ubv(kcd->colors.point);
		glPointSize(11);

		glBegin(GL_POINTS);
		glVertex3fv(kcd->curr.cage);
		glEnd();
	}

	if (kcd->curr.bmface) {
		glColor3ubv(kcd->colors.curpoint);
		glPointSize(9);

		glBegin(GL_POINTS);
		glVertex3fv(kcd->curr.cage);
		glEnd();
	}

	if (kcd->totlinehit > 0) {
		const float vthresh4 = kcd->vthresh / 4.0f;
		const float vthresh4_squared = vthresh4 * vthresh4;

		BMEdgeHit *lh;
		int i;

		glEnable(GL_BLEND);
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

		/* draw any snapped verts first */
		glColor4ubv(kcd->colors.point_a);
		glPointSize(11);
		glBegin(GL_POINTS);
		lh = kcd->linehits;
		for (i = 0; i < kcd->totlinehit; i++, lh++) {
			float sv1[3], sv2[3];

			knife_project_v3(kcd, lh->kfe->v1->cageco, sv1);
			knife_project_v3(kcd, lh->kfe->v2->cageco, sv2);
			knife_project_v3(kcd, lh->cagehit, lh->schit);

			if (len_squared_v2v2(lh->schit, sv1) < vthresh4_squared) {
				copy_v3_v3(lh->cagehit, lh->kfe->v1->cageco);
				glVertex3fv(lh->cagehit);
				lh->v = lh->kfe->v1;
			}
			else if (len_squared_v2v2(lh->schit, sv2) < vthresh4_squared) {
				copy_v3_v3(lh->cagehit, lh->kfe->v2->cageco);
				glVertex3fv(lh->cagehit);
				lh->v = lh->kfe->v2;
			}
		}
		glEnd();

		/* now draw the rest */
		glColor4ubv(kcd->colors.curpoint_a);
		glPointSize(7);
		glBegin(GL_POINTS);
		lh = kcd->linehits;
		for (i = 0; i < kcd->totlinehit; i++, lh++) {
			glVertex3fv(lh->cagehit);
		}
		glEnd();
		glDisable(GL_BLEND);
	}

	if (kcd->totkedge > 0) {
		BLI_mempool_iter iter;
		KnifeEdge *kfe;

		glLineWidth(1.0);
		glBegin(GL_LINES);

		BLI_mempool_iternew(kcd->kedges, &iter);
		for (kfe = BLI_mempool_iterstep(&iter); kfe; kfe = BLI_mempool_iterstep(&iter)) {
			if (!kfe->draw)
				continue;

			glColor3ubv(kcd->colors.line);

			glVertex3fv(kfe->v1->cageco);
			glVertex3fv(kfe->v2->cageco);
		}

		glEnd();
		glLineWidth(1.0);
	}

	if (kcd->totkvert > 0) {
		BLI_mempool_iter iter;
		KnifeVert *kfv;

		glPointSize(5.0);

		glBegin(GL_POINTS);
		BLI_mempool_iternew(kcd->kverts, &iter);
		for (kfv = BLI_mempool_iterstep(&iter); kfv; kfv = BLI_mempool_iterstep(&iter)) {
			if (!kfv->draw)
				continue;

			glColor3ubv(kcd->colors.point);

			glVertex3fv(kfv->cageco);
		}

		glEnd();
	}

	glPopMatrix();

	if (v3d->zbuf) glEnable(GL_DEPTH_TEST);
}

static float len_v3_tri_side_max(const float v1[3], const float v2[3], const float v3[3])
{
	const float s1 = len_squared_v3v3(v1, v2);
	const float s2 = len_squared_v3v3(v2, v3);
	const float s3 = len_squared_v3v3(v3, v1);

	return sqrtf(MAX3(s1, s2, s3));
}

static BMEdgeHit *knife_edge_tri_isect(KnifeTool_OpData *kcd, BMBVHTree *bmtree,
                                       const float v1[3],  const float v2[3], const float v3[3],
                                       SmallHash *ehash, bglMats *mats, int *count)
{
	BVHTree *tree2 = BLI_bvhtree_new(3, FLT_EPSILON * 4, 8, 8), *tree = BMBVH_BVHTree(bmtree);
	BMEdgeHit *edges = NULL;
	BLI_array_declare(edges);
	BVHTreeOverlap *results, *result;
	BMLoop **ls;
	float cos[9], lambda;
	unsigned int tot = 0;
	int i;

	/* for comparing distances, error of intersection depends on triangle scale.
	 * need to scale down before squaring for accurate comparison */
	const float depsilon = (FLT_EPSILON / 2.0f) * len_v3_tri_side_max(v1, v2, v3);
	const float depsilon_squared = depsilon * depsilon;

	copy_v3_v3(cos + 0, v1);
	copy_v3_v3(cos + 3, v2);
	copy_v3_v3(cos + 6, v3);

	BLI_bvhtree_insert(tree2, 0, cos, 3);
	BLI_bvhtree_balance(tree2);

	result = results = BLI_bvhtree_overlap(tree, tree2, &tot);

	for (i = 0; i < tot; i++, result++) {
		BMLoop *l1;
		BMFace *hitf;
		ListBase *lst;
		Ref *ref;

		ls = (BMLoop **)kcd->em->looptris[result->indexA];

		l1 = ls[0];
		lst = knife_get_face_kedges(kcd, l1->f);

		for (ref = lst->first; ref; ref = ref->next) {
			KnifeEdge *kfe = ref->ref;

			if (BLI_smallhash_haskey(ehash, (intptr_t)kfe)) {
				continue;  /* We already found a hit on this knife edge */
			}

			if (isect_line_tri_v3(kfe->v1->cageco, kfe->v2->cageco, v1, v2, v3, &lambda, NULL)) {
				float p[3], no[3], view[3], sp[3];

				interp_v3_v3v3(p, kfe->v1->cageco, kfe->v2->cageco, lambda);

				if (kcd->curr.vert && len_squared_v3v3(kcd->curr.vert->cageco, p) < depsilon_squared) {
					continue;
				}
				if (kcd->prev.vert && len_squared_v3v3(kcd->prev.vert->cageco, p) < depsilon_squared) {
					continue;
				}
				if (len_squared_v3v3(kcd->prev.cage, p) < depsilon_squared ||
				    len_squared_v3v3(kcd->curr.cage, p) < depsilon_squared)
				{
					continue;
				}
				if ((kcd->vc.rv3d->rflag & RV3D_CLIPPING) &&
				    ED_view3d_clipping_test(kcd->vc.rv3d, p, TRUE))
				{
					continue;
				}

				knife_project_v3(kcd, p, sp);
				ED_view3d_unproject(mats, view, sp[0], sp[1], 0.0f);
				mul_m4_v3(kcd->ob->imat, view);

				if (kcd->cut_through) {
					hitf = FALSE;
				}
				else {
					/* check if this point is visible in the viewport */
					float p1[3], lambda1;

					/* if face isn't planer, p may be behind the current tesselated tri,
					 * so move it onto that and then a little towards eye */
					if (isect_line_tri_v3(p, view, ls[0]->v->co, ls[1]->v->co, ls[2]->v->co, &lambda1, NULL)) {
						interp_v3_v3v3(p1, p, view, lambda1);
					}
					else {
						copy_v3_v3(p1, p);
					}
					sub_v3_v3(view, p1);
					normalize_v3(view);

					copy_v3_v3(no, view);
					mul_v3_fl(no, 0.003);

					/* go towards view a bit */
					add_v3_v3(p1, no);
						
					/* ray cast */
					hitf = BMBVH_RayCast(bmtree, p1, no, NULL, NULL);
				}

				/* ok, if visible add the new point */
				if (!hitf && !BLI_smallhash_haskey(ehash, (intptr_t)kfe)) {
					BMEdgeHit hit;
	
					if (len_squared_v3v3(p, kcd->curr.co) < depsilon_squared ||
					    len_squared_v3v3(p, kcd->prev.co) < depsilon_squared)
					{
						continue;
					}

					hit.kfe = kfe;
					hit.v = NULL;

					knife_find_basef(kfe);
					hit.f = kfe->basef;
					hit.perc = len_v3v3(p, kfe->v1->cageco) / len_v3v3(kfe->v1->cageco, kfe->v2->cageco);
					copy_v3_v3(hit.cagehit, p);

					interp_v3_v3v3(p, kfe->v1->co, kfe->v2->co, hit.perc);
					copy_v3_v3(hit.realhit, p);

					/* BMESH_TODO: should also snap to vertices */
					if (kcd->snap_midpoints) {
						float perc = hit.perc;

						/* select the closest from the edge endpoints or the midpoint */
						if (perc < 0.25f) {
							perc = 0.0f;
						}
						else if (perc < 0.75f) {
							perc = 0.5f;
						}
						else {
							perc = 1.0f;
						}

						interp_v3_v3v3(hit.hit, kfe->v1->co, kfe->v2->co, perc);
						interp_v3_v3v3(hit.cagehit, kfe->v1->cageco, kfe->v2->cageco, perc);
					}
					else {
						copy_v3_v3(hit.hit, p);
					}
					knife_project_v3(kcd, hit.cagehit, hit.schit);

					BLI_array_append(edges, hit);
					BLI_smallhash_insert(ehash, (intptr_t)kfe, NULL);
				}
			}
		}
	}

	if (results)
		MEM_freeN(results);

	BLI_bvhtree_free(tree2);
	*count = BLI_array_count(edges);

	return edges;
}

static void knife_bgl_get_mats(KnifeTool_OpData *UNUSED(kcd), bglMats *mats)
{
	bgl_get_mats(mats);
	//copy_m4_m4(mats->modelview, kcd->vc.rv3d->viewmat);
	//copy_m4_m4(mats->projection, kcd->vc.rv3d->winmat);
}

/* Calculate maximum excursion (doubled) from (0,0,0) of mesh */
static void calc_ortho_extent(KnifeTool_OpData *kcd)
{
	BMIter iter;
	BMVert *v;
	BMesh* bm = kcd->em->bm;
	float max_xyz = 0.0f;
	int i;

	BM_ITER_MESH(v, &iter, bm, BM_VERTS_OF_MESH) {
		for (i = 0; i < 3; i++)
			max_xyz = max_ff(max_xyz, fabs(v->co[i]));
	}
	kcd->ortho_extent = 2 * max_xyz;
}

/* Finds visible (or all, if cutting through) edges that intersects the current screen drag line */
static void knife_find_line_hits(KnifeTool_OpData *kcd)
{
	bglMats mats;
	BMEdgeHit *e1, *e2;
	SmallHash hash, *ehash = &hash;
	float v1[3], v2[3], v3[3], v4[4], s1[3], s2[3];
	int i, c1, c2;

	knife_bgl_get_mats(kcd, &mats);

	if (kcd->linehits) {
		MEM_freeN(kcd->linehits);
		kcd->linehits = NULL;
		kcd->totlinehit = 0;
	}

	copy_v3_v3(v1, kcd->prev.cage);
	copy_v3_v3(v2, kcd->curr.cage);

	/* project screen line's 3d coordinates back into 2d */
	knife_project_v3(kcd, v1, s1);
	knife_project_v3(kcd, v2, s2);

	if (len_v2v2(s1, s2) < 1)
		return;

	/* unproject screen line */
	ED_view3d_win_to_segment_clip(kcd->ar, kcd->vc.v3d, s1, v1, v3);
	ED_view3d_win_to_segment_clip(kcd->ar, kcd->vc.v3d, s2, v2, v4);

	mul_m4_v3(kcd->ob->imat, v1);
	mul_m4_v3(kcd->ob->imat, v2);
	mul_m4_v3(kcd->ob->imat, v3);
	mul_m4_v3(kcd->ob->imat, v4);

	/* numeric error, 'v1' -> 'v2', 'v2' -> 'v4' can end up being ~2000 units apart in otho mode
	 * (from ED_view3d_win_to_segment_clip() above)
	 * this gives precision error in 'knife_edge_tri_isect', rather then solving properly
	 * (which may involve using doubles everywhere!),
	 * limit the distance between these points */
	if (kcd->is_ortho) {
		if (kcd->ortho_extent == 0.0f)
			calc_ortho_extent(kcd);
		limit_dist_v3(v1, v3, kcd->ortho_extent + 10.0f);
		limit_dist_v3(v2, v4, kcd->ortho_extent + 10.0f);
	}

	BLI_smallhash_init(ehash);

	/* test two triangles of sceen line's plane */
	e1 = knife_edge_tri_isect(kcd, kcd->bmbvh, v1, v2, v3, ehash, &mats, &c1);
	e2 = knife_edge_tri_isect(kcd, kcd->bmbvh, v2, v3, v4, ehash, &mats, &c2);
	if (c1 && c2) {
		e1 = MEM_reallocN(e1, sizeof(BMEdgeHit) * (c1 + c2));
		memcpy(e1 + c1, e2, sizeof(BMEdgeHit) * c2);
		MEM_freeN(e2);
	}
	else if (c2) {
		e1 = e2;
	}

	kcd->linehits = e1;
	kcd->totlinehit = c1 + c2;

	/* find position along screen line, used for sorting */
	for (i = 0; i < kcd->totlinehit; i++) {
		BMEdgeHit *lh = e1 + i;

		lh->l = len_v2v2(lh->schit, s1) / len_v2v2(s2, s1);
	}

	BLI_smallhash_release(ehash);
}

/* this works but gives numeric problems [#33400] */
#if 0
static void knife_input_ray_cast(KnifeTool_OpData *kcd, const int mval_i[2],
                                 float r_origin[3], float r_ray[3])
{
	bglMats mats;
	float mval[2], imat[3][3];

	knife_bgl_get_mats(kcd, &mats);

	mval[0] = (float)mval_i[0];
	mval[1] = (float)mval_i[1];

	/* unproject to find view ray */
	ED_view3d_unproject(&mats, r_origin, mval[0], mval[1], 0.0f);

	if (kcd->is_ortho) {
		negate_v3_v3(r_ray, kcd->vc.rv3d->viewinv[2]);
	}
	else {
		sub_v3_v3v3(r_ray, r_origin, kcd->vc.rv3d->viewinv[3]);
	}
	normalize_v3(r_ray);

	/* transform into object space */
	invert_m4_m4(kcd->ob->imat, kcd->ob->obmat);
	copy_m3_m4(imat, kcd->ob->obmat);
	invert_m3(imat);

	mul_m4_v3(kcd->ob->imat, r_origin);
	mul_m3_v3(imat, r_ray);
}
#endif

static void knife_input_ray_segment(KnifeTool_OpData *kcd, const int mval_i[2], const float ofs,
                                    float r_origin[3], float r_origin_ofs[3])
{
	bglMats mats;
	float mval[2];

	knife_bgl_get_mats(kcd, &mats);

	mval[0] = (float)mval_i[0];
	mval[1] = (float)mval_i[1];

	/* unproject to find view ray */
	ED_view3d_unproject(&mats, r_origin,     mval[0], mval[1], 0.0f);
	ED_view3d_unproject(&mats, r_origin_ofs, mval[0], mval[1], ofs);

	/* transform into object space */
	invert_m4_m4(kcd->ob->imat, kcd->ob->obmat);

	mul_m4_v3(kcd->ob->imat, r_origin);
	mul_m4_v3(kcd->ob->imat, r_origin_ofs);
}

static BMFace *knife_find_closest_face(KnifeTool_OpData *kcd, float co[3], float cageco[3], int *is_space)
{
	BMFace *f;
	float dist = KMAXDIST;
	float origin[3];
	float origin_ofs[3];
	float ray[3];

	/* unproject to find view ray */
	knife_input_ray_segment(kcd, kcd->vc.mval, 1.0f, origin, origin_ofs);
	sub_v3_v3v3(ray, origin_ofs, origin);

	f = BMBVH_RayCast(kcd->bmbvh, origin, ray, co, cageco);

	if (is_space)
		*is_space = !f;

	if (!f) {
		/* try to use backbuffer selection method if ray casting failed */
		f = EDBM_face_find_nearest(&kcd->vc, &dist);

		/* cheat for now; just put in the origin instead
		 * of a true coordinate on the face.
		 * This just puts a point 1.0f infront of the view. */
		add_v3_v3v3(co, origin, ray);
	}

	return f;
}

/* find the 2d screen space density of vertices within a radius.  used to scale snapping
 * distance for picking edges/verts.*/
static int knife_sample_screen_density(KnifeTool_OpData *kcd, float radius)
{
	BMFace *f;
	int is_space;
	float co[3], cageco[3], sco[3];

	f = knife_find_closest_face(kcd, co, cageco, &is_space);

	if (f && !is_space) {
		ListBase *lst;
		Ref *ref;
		float dis;
		int c = 0;

		knife_project_v3(kcd, cageco, sco);

		lst = knife_get_face_kedges(kcd, f);
		for (ref = lst->first; ref; ref = ref->next) {
			KnifeEdge *kfe = ref->ref;
			int i;

			for (i = 0; i < 2; i++) {
				KnifeVert *kfv = i ? kfe->v2 : kfe->v1;

				knife_project_v3(kcd, kfv->cageco, kfv->sco);

				dis = len_v2v2(kfv->sco, sco);
				if (dis < radius) {
					if (kcd->vc.rv3d->rflag & RV3D_CLIPPING) {
						if (ED_view3d_clipping_test(kcd->vc.rv3d, kfv->cageco, TRUE) == 0) {
							c++;
						}
					}
					else {
						c++;
					}
				}
			}
		}

		return c;
	}

	return 0;
}

/* returns snapping distance for edges/verts, scaled by the density of the
 * surrounding mesh (in screen space)*/
static float knife_snap_size(KnifeTool_OpData *kcd, float maxsize)
{
	float density = (float)knife_sample_screen_density(kcd, maxsize * 2.0f);

	if (density < 1.0f)
		density = 1.0f;

	return min_ff(maxsize / (density * 0.5f), maxsize);
}

/* p is closest point on edge to the mouse cursor */
static KnifeEdge *knife_find_closest_edge(KnifeTool_OpData *kcd, float p[3], float cagep[3], BMFace **fptr, int *is_space)
{
	BMFace *f;
	float co[3], cageco[3], sco[3], maxdist = knife_snap_size(kcd, kcd->ethresh);

	if (kcd->ignore_vert_snapping)
		maxdist *= 0.5f;

	f = knife_find_closest_face(kcd, co, cageco, NULL);
	*is_space = !f;

	/* set p to co, in case we don't find anything, means a face cut */
	copy_v3_v3(p, co);
	copy_v3_v3(cagep, cageco);

	kcd->curr.bmface = f;

	if (f) {
		KnifeEdge *cure = NULL;
		ListBase *lst;
		Ref *ref;
		float dis, curdis = FLT_MAX;

		knife_project_v3(kcd, cageco, sco);

		/* look through all edges associated with this face */
		lst = knife_get_face_kedges(kcd, f);
		for (ref = lst->first; ref; ref = ref->next) {
			KnifeEdge *kfe = ref->ref;

			/* project edge vertices into screen space */
			knife_project_v3(kcd, kfe->v1->cageco, kfe->v1->sco);
			knife_project_v3(kcd, kfe->v2->cageco, kfe->v2->sco);

			dis = dist_to_line_segment_v2(sco, kfe->v1->sco, kfe->v2->sco);
			if (dis < curdis && dis < maxdist) {
				if (kcd->vc.rv3d->rflag & RV3D_CLIPPING) {
					float lambda = line_point_factor_v2(sco, kfe->v1->sco, kfe->v2->sco);
					float vec[3];

					interp_v3_v3v3(vec, kfe->v1->cageco, kfe->v2->cageco, lambda);

					if (ED_view3d_clipping_test(kcd->vc.rv3d, vec, TRUE) == 0) {
						cure = kfe;
						curdis = dis;
					}
				}
				else {
					cure = kfe;
					curdis = dis;
				}
			}
		}

		if (fptr)
			*fptr = f;

		if (cure && p) {
			if (!kcd->ignore_edge_snapping || !(cure->e)) {
				KnifeVert *edgesnap = NULL;

				if (kcd->snap_midpoints) {
					mid_v3_v3v3(p, cure->v1->co, cure->v2->co);
					mid_v3_v3v3(cagep, cure->v1->cageco, cure->v2->cageco);
				}
				else {
					float d;

					closest_to_line_segment_v3(cagep, cageco, cure->v1->cageco, cure->v2->cageco);
					d = len_v3v3(cagep, cure->v1->cageco) / len_v3v3(cure->v1->cageco, cure->v2->cageco);
					interp_v3_v3v3(p, cure->v1->co, cure->v2->co, d);
				}

				/* update mouse coordinates to the snapped-to edge's screen coordinates
				 * this is important for angle snap, which uses the previous mouse position */
				edgesnap = new_knife_vert(kcd, p, cagep);
				kcd->curr.mval[0] = (int)edgesnap->sco[0];
				kcd->curr.mval[1] = (int)edgesnap->sco[1];

			}
			else {
				return NULL;
			}
		}

		return cure;
	}

	if (fptr)
		*fptr = NULL;

	return NULL;
}

/* find a vertex near the mouse cursor, if it exists */
static KnifeVert *knife_find_closest_vert(KnifeTool_OpData *kcd, float p[3], float cagep[3], BMFace **fptr,
                                          int *is_space)
{
	BMFace *f;
	float co[3], cageco[3], sco[3], maxdist = knife_snap_size(kcd, kcd->vthresh);

	if (kcd->ignore_vert_snapping)
		maxdist *= 0.5f;

	f = knife_find_closest_face(kcd, co, cageco, is_space);

	/* set p to co, in case we don't find anything, means a face cut */
	copy_v3_v3(p, co);
	copy_v3_v3(cagep, p);
	kcd->curr.bmface = f;

	if (f) {
		ListBase *lst;
		Ref *ref;
		KnifeVert *curv = NULL;
		float dis, curdis = FLT_MAX;

		knife_project_v3(kcd, cageco, sco);

		lst = knife_get_face_kedges(kcd, f);
		for (ref = lst->first; ref; ref = ref->next) {
			KnifeEdge *kfe = ref->ref;
			int i;

			for (i = 0; i < 2; i++) {
				KnifeVert *kfv = i ? kfe->v2 : kfe->v1;

				knife_project_v3(kcd, kfv->cageco, kfv->sco);

				dis = len_v2v2(kfv->sco, sco);
				if (dis < curdis && dis < maxdist) {
					if (kcd->vc.rv3d->rflag & RV3D_CLIPPING) {
						if (ED_view3d_clipping_test(kcd->vc.rv3d, kfv->cageco, TRUE) == 0) {
							curv = kfv;
							curdis = dis;
						}
					}
					else {
						curv = kfv;
						curdis = dis;
					}
				}
			}
		}

		if (!kcd->ignore_vert_snapping || !(curv && curv->v)) {
			if (fptr)
				*fptr = f;

			if (curv && p) {
				copy_v3_v3(p, curv->co);
				copy_v3_v3(cagep, curv->cageco);

				/* update mouse coordinates to the snapped-to vertex's screen coordinates
				 * this is important for angle snap, which uses the previous mouse position */
				kcd->curr.mval[0] = (int)curv->sco[0];
				kcd->curr.mval[1] = (int)curv->sco[1];
			}

			return curv;
		}
		else {
			if (fptr)
				*fptr = f;

			return NULL;
		}
	}

	if (fptr)
		*fptr = NULL;

	return NULL;
}

static void knife_snap_angle(KnifeTool_OpData *kcd)
{
	int dx, dy;
	float w, abs_tan;

	dx = kcd->vc.mval[0] - kcd->prev.mval[0];
	dy = kcd->vc.mval[1] - kcd->prev.mval[1];
	if (dx == 0 || dy == 0)
		return;

	w = (float)dy / (float)dx;
	abs_tan = fabsf(w);
	if (abs_tan <= 0.4142f) { /* tan(22.5 degrees) = 0.4142 */
		kcd->angle_snapping = ANGLE_0;
		kcd->vc.mval[1] = kcd->prev.mval[1];
	}
	else if (abs_tan < 2.4142f) { /* tan(67.5 degrees) = 2.4142 */
		if (w > 0) {
			kcd->angle_snapping = ANGLE_45;
			kcd->vc.mval[1] = kcd->prev.mval[1] + dx;
		}
		else {
			kcd->angle_snapping = ANGLE_135;
			kcd->vc.mval[1] = kcd->prev.mval[1] - dx;
		}
	}
	else {
		kcd->angle_snapping = ANGLE_90;
		kcd->vc.mval[0] = kcd->prev.mval[0];
	}
}

/* update active knife edge/vert pointers */
static int knife_update_active(KnifeTool_OpData *kcd)
{
	if (kcd->angle_snapping != ANGLE_FREE && kcd->mode == MODE_DRAGGING)
		knife_snap_angle(kcd);

	knife_pos_data_clear(&kcd->curr);
	kcd->curr.mval[0] = kcd->vc.mval[0];
	kcd->curr.mval[1] = kcd->vc.mval[1];

	/* XXX knife_snap_angle updates the view coordinate mouse values to constrained angles,
	 * which current mouse values are set to current mouse values are then used
	 * for vertex and edge snap detection, without regard to the exact angle constraint */
	kcd->curr.vert = knife_find_closest_vert(kcd, kcd->curr.co, kcd->curr.cage, &kcd->curr.bmface, &kcd->curr.is_space);

	if (!kcd->curr.vert) {
		kcd->curr.edge = knife_find_closest_edge(kcd, kcd->curr.co, kcd->curr.cage, &kcd->curr.bmface, &kcd->curr.is_space);
	}

	/* if no hits are found this would normally default to (0, 0, 0) so instead
	 * get a point at the mouse ray closest to the previous point.
	 * Note that drawing lines in `free-space` isn't properly supported
	 * but theres no guarantee (0, 0, 0) has any geometry either - campbell */
	if (kcd->curr.vert == NULL && kcd->curr.edge == NULL) {
		float origin[3];
		float origin_ofs[3];

		knife_input_ray_segment(kcd, kcd->vc.mval, 1.0f, origin, origin_ofs);

		closest_to_line_v3(kcd->curr.cage, kcd->prev.cage, origin_ofs, origin);
	}

	if (kcd->mode == MODE_DRAGGING) {
		knife_find_line_hits(kcd);
	}
	return 1;
}

#define SCANFILL_CUTS 0
#if SCANFILL_CUTS

#define MARK            4
#define DEL             8
#define VERT_ON_EDGE    16
#define VERT_ORIG       32
#define FACE_FLIP       64
#define BOUNDARY        128
#define FACE_NEW        256

typedef struct facenet_entry {
	struct facenet_entry *next, *prev;
	KnifeEdge *kfe;
} facenet_entry;

static void rnd_offset_co(float co[3], float scale)
{
	int i;

	for (i = 0; i < 3; i++) {
		co[i] += (BLI_frand() - 0.5) * scale;
	}
}

static void remerge_faces(KnifeTool_OpData *kcd)
{
	BMesh *bm = kcd->em->bm;
	SmallHash svisit, *visit = &svisit;
	BMIter iter;
	BMFace *f;
	BMFace **stack = NULL;
	BLI_array_declare(stack);
	BMFace **faces = NULL;
	BLI_array_declare(faces);
	BMOperator bmop;
	int idx;

	BMO_op_initf(bm, &bmop, "beautify_fill faces=%ff constrain_edges=%fe", FACE_NEW, BOUNDARY);

	BMO_op_exec(bm, &bmop);
	BMO_slot_buffer_flag_enable(bm, &bmop, "geom.out", BM_FACE, FACE_NEW);

	BMO_op_finish(bm, &bmop);

	BLI_smallhash_init(visit);
	BM_ITER_MESH (f, &iter, bm, BM_FACES_OF_MESH) {
		BMIter eiter;
		BMEdge *e;
		BMFace *f2;

		if (!BMO_elem_flag_test(bm, f, FACE_NEW))
			continue;

		if (BLI_smallhash_haskey(visit, (intptr_t)f))
			continue;

		BLI_array_empty(stack);
		BLI_array_empty(faces);
		BLI_array_append(stack, f);
		BLI_smallhash_insert(visit, (intptr_t)f, NULL);

		do {
			f2 = BLI_array_pop(stack);

			BLI_array_append(faces, f2);

			BM_ITER_ELEM (e, &eiter, f2, BM_EDGES_OF_FACE) {
				BMIter fiter;
				BMFace *f3;

				if (BMO_elem_flag_test(bm, e, BOUNDARY))
					continue;

				BM_ITER_ELEM (f3, &fiter, e, BM_FACES_OF_EDGE) {
					if (!BMO_elem_flag_test(bm, f3, FACE_NEW))
						continue;
					if (BLI_smallhash_haskey(visit, (intptr_t)f3))
						continue;

					BLI_smallhash_insert(visit, (intptr_t)f3, NULL);
					BLI_array_append(stack, f3);
				}
			}
		} while (BLI_array_count(stack) > 0);

		if (BLI_array_count(faces) > 0) {
			idx = BM_elem_index_get(faces[0]);

			f2 = BM_faces_join(bm, faces, BLI_array_count(faces), TRUE);
			if (f2) {
				BMO_elem_flag_enable(bm, f2, FACE_NEW);
				BM_elem_index_set(f2, idx); /* set_dirty! *//* BMESH_TODO, check if this is valid or not */
			}
		}
	}
	/* BMESH_TODO, check if the code above validates the indices */
	/* bm->elem_index_dirty &= ~BM_FACE; */
	bm->elem_index_dirty |= BM_FACE;

	BLI_smallhash_release(visit);

	BLI_array_free(stack);
	BLI_array_free(faces);
}

/* use edgenet to fill faces.  this is a bit annoying and convoluted.*/
static void knifenet_fill_faces(KnifeTool_OpData *kcd)
{
	ScanFillContext sf_ctx;
	BMesh *bm = kcd->em->bm;
	BMIter bmiter;
	BLI_mempool_iter iter;
	BMFace *f;
	BMEdge *e;
	KnifeVert *kfv;
	KnifeEdge *kfe;
	facenet_entry *entry;
	ListBase *face_nets = MEM_callocN(sizeof(ListBase) * bm->totface, "face_nets");
	BMFace **faces = MEM_callocN(sizeof(BMFace *) * bm->totface, "faces knife");
	MemArena *arena = BLI_memarena_new(1 << 16, "knifenet_fill_faces");
	SmallHash shash;
	int i, j, k = 0, totface = bm->totface;

	BMO_push(bm, NULL);
	bmesh_edit_begin(bm, BMO_OP_FLAG_UNTAN_MULTIRES);

	/* BMESH_TODO this should be valid now, leaving here until we can ensure this - campbell */
	i = 0;
	BM_ITER_MESH (f, &bmiter, bm, BM_FACES_OF_MESH) {
		BM_elem_index_set(f, i); /* set_inline */
		faces[i] = f;
		i++;
	}
	bm->elem_index_dirty &= ~BM_FACE;

	BM_ITER_MESH (e, &bmiter, bm, BM_EDGES_OF_MESH) {
		BMO_elem_flag_enable(bm, e, BOUNDARY);
	}

	/* turn knife verts into real verts, as necessary */
	BLI_mempool_iternew(kcd->kverts, &iter);
	for (kfv = BLI_mempool_iterstep(&iter); kfv; kfv = BLI_mempool_iterstep(&iter)) {
		if (!kfv->v) {
			/* shouldn't we be at least copying the normal? - if not some comment here should explain why - campbell */
			kfv->v = BM_vert_create(bm, kfv->co, NULL);
			kfv->flag = 1;
			BMO_elem_flag_enable(bm, kfv->v, DEL);
		}
		else {
			kfv->flag = 0;
			BMO_elem_flag_enable(bm, kfv->v, VERT_ORIG);
		}

		BMO_elem_flag_enable(bm, kfv->v, MARK);
	}

	/* we want to only do changed faces.  first, go over new edges and add to
	 * face net lists.*/
	i = j = k = 0;
	BLI_mempool_iternew(kcd->kedges, &iter);
	for (kfe = BLI_mempool_iterstep(&iter); kfe; kfe = BLI_mempool_iterstep(&iter)) {
		Ref *ref;
		if (!kfe->v1 || !kfe->v2 || kfe->v1->inspace || kfe->v2->inspace)
			continue;

		i++;

		if (kfe->e && kfe->v1->v == kfe->e->v1 && kfe->v2->v == kfe->e->v2) {
			kfe->oe = kfe->e;
			continue;
		}

		j++;

		if (kfe->e) {
			kfe->oe = kfe->e;

			BMO_elem_flag_enable(bm, kfe->e, DEL);
			BMO_elem_flag_disable(bm, kfe->e, BOUNDARY);
			kfe->e = NULL;
		}

		kfe->e = BM_edge_create(bm, kfe->v1->v, kfe->v2->v, NULL, BM_CREATE_NO_DOUBLE);
		BMO_elem_flag_enable(bm, kfe->e, BOUNDARY);

		for (ref = kfe->faces.first; ref; ref = ref->next) {
			f = ref->ref;

			entry = BLI_memarena_alloc(arena, sizeof(*entry));
			entry->kfe = kfe;
			BLI_addtail(face_nets + BM_elem_index_get(f), entry);
		}
	}

	/* go over original edges, and add to faces with new geometry */
	BLI_mempool_iternew(kcd->kedges, &iter);
	for (kfe = BLI_mempool_iterstep(&iter); kfe; kfe = BLI_mempool_iterstep(&iter)) {
		Ref *ref;

		if (!kfe->v1 || !kfe->v2 || kfe->v1->inspace || kfe->v2->inspace)
			continue;
		if (!(kfe->oe && kfe->v1->v == kfe->oe->v1 && kfe->v2->v == kfe->oe->v2))
			continue;

		k++;

		BMO_elem_flag_enable(bm, kfe->e, BOUNDARY);
		kfe->oe = kfe->e;

		for (ref = kfe->faces.first; ref; ref = ref->next) {
			f = ref->ref;

			if (face_nets[BM_elem_index_get(f)].first) {
				entry = BLI_memarena_alloc(arena, sizeof(*entry));
				entry->kfe = kfe;
				BLI_addtail(face_nets + BM_elem_index_get(f), entry);
			}
		}
	}

	BLI_srand(0);

	for (i = 0; i < totface; i++) {
		SmallHash *hash = &shash;
		ScanFillFace *sf_tri;
		ScanFillVert *sf_vert, *sf_vert_last;
		int j;
		float rndscale = (KNIFE_FLT_EPS / 4.0f);

		f = faces[i];
		BLI_smallhash_init(hash);

		if (face_nets[i].first)
			BMO_elem_flag_enable(bm, f, DEL);

		BLI_scanfill_begin(&sf_ctx);

		for (entry = face_nets[i].first; entry; entry = entry->next) {
			if (!BLI_smallhash_haskey(hash, (intptr_t)entry->kfe->v1)) {
				sf_vert = BLI_scanfill_vert_add(&sf_ctx, entry->kfe->v1->v->co);
				sf_vert->poly_nr = 0;
				rnd_offset_co(sf_vert->co, rndscale);
				sf_vert->tmp.p = entry->kfe->v1->v;
				BLI_smallhash_insert(hash, (intptr_t)entry->kfe->v1, sf_vert);
			}

			if (!BLI_smallhash_haskey(hash, (intptr_t)entry->kfe->v2)) {
				sf_vert = BLI_scanfill_vert_add(&sf_ctx, entry->kfe->v2->v->co);
				sf_vert->poly_nr = 0;
				rnd_offset_co(sf_vert->co, rndscale);
				sf_vert->tmp.p = entry->kfe->v2->v;
				BLI_smallhash_insert(hash, (intptr_t)entry->kfe->v2, sf_vert);
			}
		}

		for (j = 0, entry = face_nets[i].first; entry; entry = entry->next, j++) {
			sf_vert_last = BLI_smallhash_lookup(hash, (intptr_t)entry->kfe->v1);
			sf_vert = BLI_smallhash_lookup(hash, (intptr_t)entry->kfe->v2);

			sf_vert->poly_nr++;
			sf_vert_last->poly_nr++;
		}

		for (j = 0, entry = face_nets[i].first; entry; entry = entry->next, j++) {
			sf_vert_last = BLI_smallhash_lookup(hash, (intptr_t)entry->kfe->v1);
			sf_vert = BLI_smallhash_lookup(hash, (intptr_t)entry->kfe->v2);

			if (sf_vert->poly_nr > 1 && sf_vert_last->poly_nr > 1) {
				ScanFillEdge *sf_edge;
				sf_edge = BLI_scanfill_edge_add(&sf_ctx, sf_vert_last, sf_vert);
				if (entry->kfe->oe)
					sf_edge->f = SF_EDGE_BOUNDARY;  /* mark as original boundary edge */

				BMO_elem_flag_disable(bm, entry->kfe->e->v1, DEL);
				BMO_elem_flag_disable(bm, entry->kfe->e->v2, DEL);
			}
			else {
				if (sf_vert_last->poly_nr < 2)
					BLI_remlink(&sf_ctx.fillvertbase, sf_vert_last);
				if (sf_vert->poly_nr < 2)
					BLI_remlink(&sf_ctx.fillvertbase, sf_vert);
			}
		}

		BLI_scanfill_calc(&sf_ctx, 0);

		for (sf_tri = sf_ctx.fillfacebase.first; sf_tri; sf_tri = sf_tri->next) {
			BMVert *v1 = sf_tri->v3->tmp.p, *v2 = sf_tri->v2->tmp.p, *v3 = sf_tri->v1->tmp.p;
			BMFace *f2;
			BMLoop *l_iter;
			BMVert *verts[3] = {v1, v2, v3};

			if (v1 == v2 || v2 == v3 || v1 == v3)
				continue;
			if (BM_face_exists(bm, verts, 3, &f2))
				continue;

			f2 = BM_face_create_quad_tri(bm,
			                             v1, v2, v3, NULL,
			                             NULL, FALSE);

			BMO_elem_flag_enable(bm, f2, FACE_NEW);

			l_iter = BM_FACE_FIRST_LOOP(f2);
			do {
				BMO_elem_flag_disable(bm, l_iter->e, DEL);
			} while ((l_iter = l_iter->next) != BM_FACE_FIRST_LOOP(f2));

			BMO_elem_flag_disable(bm, f2, DEL);
			BM_elem_index_set(f2, i); /* set_dirty! *//* note, not 100% sure this is dirty? need to check */

			BM_face_normal_update(f2);
			if (dot_v3v3(f->no, f2->no) < 0.0f) {
				BM_face_normal_flip(bm, f2);
			}
		}

		BLI_scanfill_end(&sf_ctx);
		BLI_smallhash_release(hash);
	}
	bm->elem_index_dirty |= BM_FACE;

	/* interpolate customdata */
	BM_ITER_MESH (f, &bmiter, bm, BM_FACES_OF_MESH) {
		BMLoop *l1;
		BMFace *f2;
		BMIter liter1;

		if (!BMO_elem_flag_test(bm, f, FACE_NEW))
			continue;

		f2 = faces[BM_elem_index_get(f)];
		if (BM_elem_index_get(f) < 0 || BM_elem_index_get(f) >= totface) {
			fprintf(stderr, "%s: face index out of range! (bmesh internal error)\n", __func__);
		}

		BM_elem_attrs_copy(bm, bm, f2, f);

		BM_ITER_ELEM (l1, &liter1, f, BM_LOOPS_OF_FACE) {
			BM_loop_interp_from_face(bm, l1, f2, TRUE, TRUE);
		}
	}

	/* merge triangles back into faces */
	remerge_faces(kcd);

	/* delete left over faces */
	BMO_op_callf(bm, BMO_FLAG_DEFAULTS, "delete geom=%ff context=%i", DEL, DEL_ONLYFACES);
	BMO_op_callf(bm, BMO_FLAG_DEFAULTS, "delete geom=%fe context=%i", DEL, DEL_EDGES);
	BMO_op_callf(bm, BMO_FLAG_DEFAULTS, "delete geom=%fv context=%i", DEL, DEL_VERTS);

	if (face_nets) 
		MEM_freeN(face_nets);
	if (faces)
		MEM_freeN(faces);
	BLI_memarena_free(arena);

	BMO_error_clear(bm); /* remerge_faces sometimes raises errors, so make sure to clear them */

	bmesh_edit_end(bm, BMO_OP_FLAG_UNTAN_MULTIRES);
	BMO_pop(bm);
}

#else  /* use direct (non-scanfill) method for cuts */

/* assuming v is on line ab, what fraction of the way is v from a to b? */
static float frac_along(const float a[3], const float b[3], const float v[3])
{
	float lab;

	lab = len_v3v3(a, b);
	if (lab == 0.0f) {
		return 0.0f;
	}
	else {
		return len_v3v3(a, v) / lab;
	}
}

/* sort list of kverts by fraction along edge e */
static void sort_by_frac_along(ListBase *lst, BMEdge *e)
{
	KnifeVert *vcur, *vprev;
	float *v1co, *v2co;
	Ref *cur = NULL, *prev = NULL, *next = NULL;

	if (lst->first == lst->last)
		return;

	v1co = e->v1->co;
	v2co = e->v2->co;

	for (cur = ((Ref *)lst->first)->next; cur; cur = next) {
		next = cur->next;
		prev = cur->prev;

		BLI_remlink(lst, cur);

		vcur = cur->ref;
		while (prev) {
			vprev = prev->ref;
			if (frac_along(v1co, v2co, vprev->co) <= frac_along(v1co, v2co, vcur->co))
				break;
			prev = prev->prev;
		}

		BLI_insertlinkafter(lst, prev, cur);
	}
}

/* The chain so far goes from an instantiated vertex to kfv (some may be reversed).
 * If possible, complete the chain to another instantiated vertex and return 1, else return 0.
 * The visited hash says which KnifeVert's have already been tried, not including kfv. */
static int find_chain_search(KnifeTool_OpData *kcd, KnifeVert *kfv, ListBase *fedges, SmallHash *visited,
                             ListBase *chain)
{
	Ref *r;
	KnifeEdge *kfe;
	KnifeVert *kfv_other;

	if (kfv->v)
		return TRUE;

	BLI_smallhash_insert(visited, (uintptr_t)kfv, NULL);
	/* Try all possible next edges. Could either go through fedges
	 * (all the KnifeEdges for the face being cut) or could go through
	 * kve->edges and restrict to cutting face and uninstantiated edges.
	 * Not clear which is better. Let's do the first. */
	for (r = fedges->first; r; r = r->next) {
		kfe = r->ref;
		kfv_other = NULL;
		if (kfe->v1 == kfv)
			kfv_other = kfe->v2;
		else if (kfe->v2 == kfv)
			kfv_other = kfe->v1;
		if (kfv_other && !BLI_smallhash_haskey(visited, (uintptr_t)kfv_other)) {
			knife_append_list(kcd, chain, kfe);
			if (find_chain_search(kcd, kfv_other, fedges, visited, chain))
				return TRUE;
			BLI_remlink(chain, chain->last);
		}
	}
	return FALSE;
}

static ListBase *find_chain_from_vertex(KnifeTool_OpData *kcd, KnifeEdge *kfe, BMVert *v, ListBase *fedges)
{
	SmallHash visited_, *visited = &visited_;
	ListBase *ans;
	int found;

	ans = knife_empty_list(kcd);
	knife_append_list(kcd, ans, kfe);
	found = 0;
	BLI_smallhash_init(visited);
	if (kfe->v1->v == v) {
		BLI_smallhash_insert(visited, (uintptr_t)(kfe->v1), NULL);
		found = find_chain_search(kcd, kfe->v2, fedges, visited, ans);
	}
	else {
		BLI_assert(kfe->v2->v == v);
		BLI_smallhash_insert(visited, (uintptr_t)(kfe->v2), NULL);
		found = find_chain_search(kcd, kfe->v1, fedges, visited, ans);
	}

	BLI_smallhash_release(visited);

	if (found)
		return ans;
	else
		return NULL;
}

/* Find a chain in fedges from one instantiated vertex to another.
 * Remove the edges in the chain from fedges and return a separate list of the chain. */
static ListBase *find_chain(KnifeTool_OpData *kcd, ListBase *fedges)
{
	Ref *r, *ref;
	KnifeEdge *kfe;
	BMVert *v1, *v2;
	ListBase *ans;

	ans = NULL;

	for (r = fedges->first; r; r = r->next) {
		kfe = r->ref;
		v1 = kfe->v1->v;
		v2 = kfe->v2->v;
		if (v1 && v2) {
			ans = knife_empty_list(kcd);
			knife_append_list(kcd, ans, kfe);
			break;
		}
		if (v1)
			ans = find_chain_from_vertex(kcd, kfe, v1, fedges);
		else if (v2)
			ans = find_chain_from_vertex(kcd, kfe, v2, fedges);
		if (ans)
			break;
	}
	if (ans) {
		BLI_assert(BLI_countlist(ans) > 0);
		for (r = ans->first; r; r = r->next) {
			ref = find_ref(fedges, r->ref);
			BLI_assert(ref != NULL);
			BLI_remlink(fedges, ref);
		}
	}
	return ans;
}

/* The hole so far goes from kfvfirst to kfv (some may be reversed).
 * If possible, complete the hole back to kfvfirst and return 1, else return 0.
 * The visited hash says which KnifeVert's have already been tried, not including kfv or kfvfirst. */
static int find_hole_search(KnifeTool_OpData *kcd, KnifeVert *kfvfirst, KnifeVert *kfv, ListBase *fedges,
                            SmallHash *visited, ListBase *hole)
{
	Ref *r;
	KnifeEdge *kfe, *kfelast;
	KnifeVert *kfv_other;

	if (kfv == kfvfirst)
		return TRUE;

	BLI_smallhash_insert(visited, (uintptr_t)kfv, NULL);
	kfelast = ((Ref *)hole->last)->ref;
	for (r = fedges->first; r; r = r->next) {
		kfe = r->ref;
		if (kfe == kfelast)
			continue;
		if (kfe->v1->v || kfe->v2->v)
			continue;
		kfv_other = NULL;
		if (kfe->v1 == kfv)
			kfv_other = kfe->v2;
		else if (kfe->v2 == kfv)
			kfv_other = kfe->v1;
		if (kfv_other && !BLI_smallhash_haskey(visited, (uintptr_t)kfv_other)) {
			knife_append_list(kcd, hole, kfe);
			if (find_hole_search(kcd, kfvfirst, kfv_other, fedges, visited, hole))
				return TRUE;
			BLI_remlink(hole, hole->last);
		}
	}
	return FALSE;
}

/* Find a hole (simple cycle with no instantiated vertices).
 * Remove the edges in the cycle from fedges and return a separate list of the cycle */
static ListBase *find_hole(KnifeTool_OpData *kcd, ListBase *fedges)
{
	ListBase *ans;
	Ref *r, *ref;
	KnifeEdge *kfe;
	SmallHash visited_, *visited = &visited_;
	int found;

	ans = NULL;
	found = FALSE;

	for (r = fedges->first; r && !found; r = r->next) {
		kfe = r->ref;
		if (kfe->v1->v || kfe->v2->v || kfe->v1 == kfe->v2)
			continue;

		BLI_smallhash_init(visited);
		ans = knife_empty_list(kcd);
		knife_append_list(kcd, ans, kfe);

		found = find_hole_search(kcd, kfe->v1, kfe->v2, fedges, visited, ans);

		BLI_smallhash_release(visited);
	}

	if (found) {
		for (r = ans->first; r; r = r->next) {
			kfe = r->ref;
			ref = find_ref(fedges, r->ref);
			if (ref)
				BLI_remlink(fedges, ref);
		}
		return ans;
	}
	else {
		return NULL;
	}
}

/* Try to find "nice" diagonals - short, and far apart from each other.
 * If found, return TRUE and make a 'main chain' going across f which uses
 * the two diagonals and one part of the hole, and a 'side chain' that
 * completes the hole. */
static int find_hole_chains(KnifeTool_OpData *kcd, ListBase *hole, BMFace *f, ListBase **mainchain,
                            ListBase **sidechain)
{
	float **fco, **hco;
	BMVert **fv;
	KnifeVert **hv;
	KnifeEdge **he;
	Ref *r;
	KnifeVert *kfv, *kfvother;
	KnifeEdge *kfe;
	ListBase *chain;
	BMVert *v;
	BMIter iter;
	int nh, nf, i, j, k, m, ax, ay, ok, sep = 0 /* Quite warnings */, bestsep;
	int besti[2], bestj[2];
	float d, bestd;

	nh = BLI_countlist(hole);
	nf = f->len;
	if (nh < 2 || nf < 3)
		return 0;

	/* Gather 2d projections of hole and face vertex coordinates.
	 * Use best-axis projection - not completely accurate, maybe revisit */
	axis_dominant_v3(&ax, &ay, f->no);
	hco = BLI_memarena_alloc(kcd->arena, nh * sizeof(float *));
	fco = BLI_memarena_alloc(kcd->arena, nf * sizeof(float *));
	hv = BLI_memarena_alloc(kcd->arena, nh * sizeof(KnifeVert *));
	fv = BLI_memarena_alloc(kcd->arena, nf * sizeof(BMVert *));
	he = BLI_memarena_alloc(kcd->arena, nh * sizeof(KnifeEdge *));

	i = 0;
	kfv = NULL;
	kfvother = NULL;
	for (r = hole->first; r; r = r->next) {
		kfe = r->ref;
		he[i] = kfe;
		if (kfvother == NULL) {
			kfv = kfe->v1;
		}
		else {
			kfv = kfvother;
			BLI_assert(kfv == kfe->v1 || kfv == kfe->v2);
		}
		hco[i] = BLI_memarena_alloc(kcd->arena, 2 * sizeof(float));
		hco[i][0] = kfv->co[ax];
		hco[i][1] = kfv->co[ay];
		hv[i] = kfv;
		kfvother = (kfe->v1 == kfv) ? kfe->v2 : kfe->v1;
		i++;
	}

	j = 0;
	BM_ITER_ELEM (v, &iter, f, BM_VERTS_OF_FACE) {
		fco[j] = BLI_memarena_alloc(kcd->arena, 2 * sizeof(float));
		fco[j][0] = v->co[ax];
		fco[j][1] = v->co[ay];
		fv[j] = v;
		j++;
	}

	/* For first diagonal  (m == 0), want shortest length.
	 * For second diagonal (m == 1), want max separation of index of hole
	 * vertex from the hole vertex used in the first diagonal, and from there
	 * want the one with shortest length not to the same vertex as the first diagonal. */
	for (m = 0; m < 2; m++) {
		besti[m] = -1;
		bestj[m] = -1;
		bestd = FLT_MAX;
		bestsep = 0;
		for (i = 0; i < nh; i++) {
			if (m == 1) {
				if (i == besti[0])
					continue;
				sep = (i + nh - besti[0]) % nh;
				sep = MIN2(sep, nh - sep);
				if (sep < bestsep)
					continue;
				bestd = FLT_MAX;
			}
			for (j = 0; j < nf; j++) {
				if (m == 1 && j == bestj[0])
					continue;
				d = len_squared_v2v2(hco[i], fco[j]);
				if (d > bestd)
					continue;

				ok = TRUE;
				for (k = 0; k < nh && ok; k++) {
					if (k == i || (k + 1) % nh == i)
						continue;
					if (isect_line_line_v2(hco[i], fco[j], hco[k], hco[(k + 1) % nh]))
						ok = FALSE;
				}
				if (!ok)
					continue;
				for (k = 0; k < nf && ok; k++) {
					if (k == j || (k + 1) % nf == j)
						continue;
					if (isect_line_line_v2(hco[i], fco[j], fco[k], fco[(k + 1) % nf]))
						ok = FALSE;
				}
				if (ok) {
					besti[m] = i;
					bestj[m] = j;
					if (m == 1)
						bestsep = sep;
					bestd = d;
				}
			}
		}
	}

	if (besti[0] != -1 && besti[1] != -1) {
		BLI_assert(besti[0] != besti[1] && bestj[0] != bestj[1]);
		kfe = new_knife_edge(kcd);
		kfe->v1 = get_bm_knife_vert(kcd, fv[bestj[0]]);
		kfe->v2 = hv[besti[0]];
		chain = knife_empty_list(kcd);
		knife_append_list(kcd, chain, kfe);
		for (i = besti[0]; i != besti[1]; i = (i + 1) % nh) {
			knife_append_list(kcd, chain, he[i]);
		}
		kfe = new_knife_edge(kcd);
		kfe->v1 = hv[besti[1]];
		kfe->v2 = get_bm_knife_vert(kcd, fv[bestj[1]]);
		knife_append_list(kcd, chain, kfe);
		*mainchain = chain;

		chain = knife_empty_list(kcd);
		for (i = besti[1]; i != besti[0]; i = (i + 1) % nh) {
			knife_append_list(kcd, chain, he[i]);
		}
		*sidechain = chain;

		return TRUE;
	}
	else {
		return FALSE;
	}
}

static int knife_edge_in_face(KnifeTool_OpData *UNUSED(kcd), KnifeEdge *kfe, BMFace *f)
{
	/* BMesh *bm = kcd->em->bm; */ /* UNUSED */
	BMVert *v1, *v2;
	BMLoop *l1, *l2, *l;
	float mid[3];
	BMIter iter;
	int v1inside, v2inside;

	if (!f)
		return FALSE;

	v1 = kfe->v1->v;
	v2 = kfe->v2->v;
	l1 = NULL;
	l2 = NULL;

	/* find out if v1 and v2, if set, are part of the face */
	BM_ITER_ELEM (l, &iter, f, BM_LOOPS_OF_FACE) {
		if (v1 && l->v == v1)
			l1 = l;
		if (v2 && l->v == v2)
			l2 = l;
	}

	/* BM_face_point_inside_test uses best-axis projection so this isn't most accurate test... */
	v1inside = l1 ? 0 : BM_face_point_inside_test(f, kfe->v1->co);
	v2inside = l2 ? 0 : BM_face_point_inside_test(f, kfe->v2->co);
	if ((l1 && v2inside) || (l2 && v1inside) || (v1inside && v2inside))
		return TRUE;
	if (l1 && l2) {
		/* Can have case where v1 and v2 are on shared chain between two faces.
		 * BM_face_legal_splits does visibility and self-intersection tests,
		 * but it is expensive and maybe a bit buggy, so use a simple
		 * "is the midpoint in the face" test */
		mid_v3_v3v3(mid, kfe->v1->co, kfe->v2->co);
		return BM_face_point_inside_test(f, mid);
	}
	return FALSE;
}

/* Split face f with KnifeEdges on chain.  f remains as one side, the face formed is put in *newface.
 * The new face will be on the left side of the chain as viewed from the normal-out side of f. */
static void knife_make_chain_cut(KnifeTool_OpData *kcd, BMFace *f, ListBase *chain, BMFace **newface)
{
	BMesh *bm = kcd->em->bm;
	KnifeEdge *kfe, *kfelast;
	BMVert *v1, *v2;
	BMFace *fnew;
	Ref *ref;
	KnifeVert *kfv, *kfvprev;
	BMLoop *lnew, *l_iter;
	int i;
	int nco = BLI_countlist(chain) - 1;
	float (*cos)[3] = BLI_array_alloca(cos, nco);
	KnifeVert **kverts = BLI_array_alloca(kverts, nco);

	kfe = ((Ref *)chain->first)->ref;
	v1 = kfe->v1->v ? kfe->v1->v : kfe->v2->v;
	kfelast = ((Ref *)chain->last)->ref;
	v2 = kfelast->v2->v ? kfelast->v2->v : kfelast->v1->v;
	BLI_assert(v1 != NULL && v2 != NULL);
	kfvprev = kfe->v1->v == v1 ? kfe->v1 : kfe->v2;
	for (ref = chain->first, i = 0; i < nco && ref != chain->last; ref = ref->next, i++) {
		kfe = ref->ref;
		BLI_assert(kfvprev == kfe->v1 || kfvprev == kfe->v2);
		kfv = kfe->v1 == kfvprev ? kfe->v2 : kfe->v1;
		copy_v3_v3(cos[i], kfv->co);
		kverts[i] = kfv;
		kfvprev = kfv;
	}
	BLI_assert(i == nco);
	lnew = NULL;
	if (nco == 0) {
		/* Want to prevent creating two-sided polygons */
		if (BM_edge_exists(v1, v2)) {
			*newface = NULL;
		}
		else {
			*newface = BM_face_split(bm, f, v1, v2, &lnew, NULL, TRUE);
		}
	}
	else {
		fnew = BM_face_split_n(bm, f, v1, v2, cos, nco, &lnew, NULL);
		*newface = fnew;

		if (fnew) {
			/* Now go through lnew chain matching up chain kv's and assign real v's to them */
			for (l_iter = lnew->next, i = 0; i < nco; l_iter = l_iter->next, i++) {
				BLI_assert(equals_v3v3(cos[i], l_iter->v->co));
				if (kcd->select_result) {
					BM_edge_select_set(bm, l_iter->e, TRUE);
				}
				kverts[i]->v = l_iter->v;
			}
		}
	}

	/* the select chain above doesnt account for the first loop */
	if (kcd->select_result) {
		if (lnew) {
			BM_edge_select_set(bm, lnew->e, TRUE);
		}
	}
}

static void knife_make_face_cuts(KnifeTool_OpData *kcd, BMFace *f, ListBase *kfedges)
{
	BMesh *bm = kcd->em->bm;
	KnifeEdge *kfe;
	BMFace *fnew, *fnew2, *fhole;
	ListBase *chain, *hole, *sidechain;
	ListBase *fnew_kfedges, *fnew2_kfedges;
	Ref *ref, *refnext;
	int count, oldcount;

	oldcount = BLI_countlist(kfedges);
	while ((chain = find_chain(kcd, kfedges)) != NULL) {
		knife_make_chain_cut(kcd, f, chain, &fnew);
		if (!fnew) {
			return;
		}

		/* Move kfedges to fnew_kfedges if they are now in fnew.
		 * The chain edges were removed already */
		fnew_kfedges = knife_empty_list(kcd);
		for (ref = kfedges->first; ref; ref = refnext) {
			kfe = ref->ref;
			refnext = ref->next;
			if (knife_edge_in_face(kcd, kfe, fnew)) {
				BLI_remlink(kfedges, ref);
				kfe->basef = fnew;
				knife_append_list(kcd, fnew_kfedges, kfe);
			}
		}
		if (fnew_kfedges->first)
			knife_make_face_cuts(kcd, fnew, fnew_kfedges);

		/* find_chain should always remove edges if it returns TRUE,
		 * but guard against infinite loop anyway */
		count = BLI_countlist(kfedges);
		if (count >= oldcount) {
			BLI_assert(!"knife find_chain infinite loop");
			return;
		}
		oldcount = count;
	}

	while ((hole = find_hole(kcd, kfedges)) != NULL) {
		if (find_hole_chains(kcd, hole, f, &chain, &sidechain)) {
			/* chain goes across f and sidechain comes back
			 * from the second last vertex to the second vertex.
			 */
			knife_make_chain_cut(kcd, f, chain, &fnew);
			if (!fnew) {
				BLI_assert(!"knife failed hole cut");
				return;
			}
			kfe = ((Ref *)sidechain->first)->ref;
			if (knife_edge_in_face(kcd, kfe, f)) {
				knife_make_chain_cut(kcd, f, sidechain, &fnew2);
				fhole = f;
			}
			else if (knife_edge_in_face(kcd, kfe, fnew)) {
				knife_make_chain_cut(kcd, fnew, sidechain, &fnew2);
				fhole = fnew2;
			}
			else {
				/* shouldn't happen except in funny edge cases */
				return;
			}
			BM_face_kill(bm, fhole);
			/* Move kfedges to either fnew or fnew2 if appropriate.
			 * The hole edges were removed already */
			fnew_kfedges = knife_empty_list(kcd);
			fnew2_kfedges = knife_empty_list(kcd);
			for (ref = kfedges->first; ref; ref = refnext) {
				kfe = ref->ref;
				refnext = ref->next;
				if (knife_edge_in_face(kcd, kfe, fnew)) {
					BLI_remlink(kfedges, ref);
					kfe->basef = fnew;
					knife_append_list(kcd, fnew_kfedges, kfe);
				}
				else if (knife_edge_in_face(kcd, kfe, fnew2)) {
					BLI_remlink(kfedges, ref);
					kfe->basef = fnew2;
					knife_append_list(kcd, fnew2_kfedges, kfe);
				}
			}
			/* We'll skip knife edges that are in the newly formed hole.
			 * (Maybe we shouldn't have made a hole in the first place?) */
			if (fnew != fhole && fnew_kfedges->first)
				knife_make_face_cuts(kcd, fnew, fnew_kfedges);
			if (fnew2 != fhole && fnew2_kfedges->first)
				knife_make_face_cuts(kcd, fnew2, fnew2_kfedges);
			if (f == fhole)
				break;
			/* find_hole should always remove edges if it returns TRUE,
			 * but guard against infinite loop anyway */
			count = BLI_countlist(kfedges);
			if (count >= oldcount) {
				BLI_assert(!"knife find_hole infinite loop");
				return;
			}
			oldcount = count;
		}
	}
}

/* Use the network of KnifeEdges and KnifeVerts accumulated to make real BMVerts and BMEdedges */
static void knife_make_cuts(KnifeTool_OpData *kcd)
{
	BMesh *bm = kcd->em->bm;
	KnifeEdge *kfe;
	KnifeVert *kfv;
	BMFace *f;
	BMEdge *e, *enew;
	ListBase *lst;
	Ref *ref;
	float pct;
	SmallHashIter hiter;
	BLI_mempool_iter iter;
	SmallHash fhash_, *fhash = &fhash_;
	SmallHash ehash_, *ehash = &ehash_;

	BLI_smallhash_init(fhash);
	BLI_smallhash_init(ehash);

	/* put list of cutting edges for a face into fhash, keyed by face */
	BLI_mempool_iternew(kcd->kedges, &iter);
	for (kfe = BLI_mempool_iterstep(&iter); kfe; kfe = BLI_mempool_iterstep(&iter)) {
		f = kfe->basef;
		if (!f || kfe->e)
			continue;
		lst = BLI_smallhash_lookup(fhash, (uintptr_t)f);
		if (!lst) {
			lst = knife_empty_list(kcd);
			BLI_smallhash_insert(fhash, (uintptr_t)f, lst);
		}
		knife_append_list(kcd, lst, kfe);
	}

	/* put list of splitting vertices for an edge into ehash, keyed by edge */
	BLI_mempool_iternew(kcd->kverts, &iter);
	for (kfv = BLI_mempool_iterstep(&iter); kfv; kfv = BLI_mempool_iterstep(&iter)) {
		if (kfv->v)
			continue;  /* already have a BMVert */
		for (ref = kfv->edges.first; ref; ref = ref->next) {
			kfe = ref->ref;
			e = kfe->e;
			if (!e)
				continue;
			lst = BLI_smallhash_lookup(ehash, (uintptr_t)e);
			if (!lst) {
				lst = knife_empty_list(kcd);
				BLI_smallhash_insert(ehash, (uintptr_t)e, lst);
			}
			/* there can be more than one kfe in kfv's list with same e */
			if (!find_ref(lst, kfv))
				knife_append_list(kcd, lst, kfv);
		}
	}

	/* split bmesh edges where needed */
	for (lst = BLI_smallhash_iternew(ehash, &hiter, (uintptr_t *)&e); lst;
	     lst = BLI_smallhash_iternext(&hiter, (uintptr_t *)&e))
	{
		sort_by_frac_along(lst, e);
		for (ref = lst->first; ref; ref = ref->next) {
			kfv = ref->ref;
			pct = frac_along(e->v1->co, e->v2->co, kfv->co);
			kfv->v = BM_edge_split(bm, e, e->v1, &enew, pct);
		}
	}

	if (kcd->only_select) {
		EDBM_flag_disable_all(kcd->em, BM_ELEM_SELECT);
	}

	/* do cuts for each face */
	for (lst = BLI_smallhash_iternew(fhash, &hiter, (uintptr_t *)&f); lst;
	     lst = BLI_smallhash_iternext(&hiter, (uintptr_t *)&f))
	{
		knife_make_face_cuts(kcd, f, lst);
	}

	BLI_smallhash_release(fhash);
	BLI_smallhash_release(ehash);
}
#endif

/* called on tool confirmation */
static void knifetool_finish(wmOperator *op)
{
	KnifeTool_OpData *kcd = op->customdata;

#if SCANFILL_CUTS
	knifenet_fill_faces(kcd);
#else
	knife_make_cuts(kcd);
#endif

	EDBM_mesh_normals_update(kcd->em);
	EDBM_update_generic(kcd->em, TRUE, TRUE);
}

/* copied from paint_image.c */
static int project_knife_view_clip(View3D *v3d, RegionView3D *rv3d, float *clipsta, float *clipend)
{
	int orth = ED_view3d_clip_range_get(v3d, rv3d, clipsta, clipend);

	if (orth) { /* only needed for ortho */
		float fac = 2.0f / ((*clipend) - (*clipsta));
		*clipsta *= fac;
		*clipend *= fac;
	}

	return orth;
}

static void knife_recalc_projmat(KnifeTool_OpData *kcd)
{
	invert_m4_m4(kcd->ob->imat, kcd->ob->obmat);
	ED_view3d_ob_project_mat_get(kcd->ar->regiondata, kcd->ob, kcd->projmat);
	//mult_m4_m4m4(kcd->projmat, kcd->vc.rv3d->winmat, kcd->vc.rv3d->viewmat);

	kcd->is_ortho = project_knife_view_clip(kcd->vc.v3d, kcd->vc.rv3d, 
	                                        &kcd->clipsta, &kcd->clipend);
}

/* called when modal loop selection is done... */
static void knifetool_exit(bContext *C, wmOperator *op)
{
	KnifeTool_OpData *kcd = op->customdata;

	if (!kcd)
		return;

	WM_cursor_restore(CTX_wm_window(C));

	/* deactivate the extra drawing stuff in 3D-View */
	ED_region_draw_cb_exit(kcd->ar->type, kcd->draw_handle);

	/* free the custom data */
	BLI_mempool_destroy(kcd->refs);
	BLI_mempool_destroy(kcd->kverts);
	BLI_mempool_destroy(kcd->kedges);

	BLI_ghash_free(kcd->origedgemap, NULL, NULL);
	BLI_ghash_free(kcd->origvertmap, NULL, NULL);
	BLI_ghash_free(kcd->kedgefacemap, NULL, NULL);

	BMBVH_FreeBVH(kcd->bmbvh);
	BLI_memarena_free(kcd->arena);

	/* tag for redraw */
	ED_region_tag_redraw(kcd->ar);

	if (kcd->cagecos)
		MEM_freeN(kcd->cagecos);

	if (kcd->linehits)
		MEM_freeN(kcd->linehits);

	/* destroy kcd itself */
	MEM_freeN(kcd);
	op->customdata = NULL;
}

static void cage_mapped_verts_callback(void *userData, int index, const float co[3],
                                       const float UNUSED(no_f[3]), const short UNUSED(no_s[3]))
{
	void **data = userData;
	BMEditMesh *em = data[0];
	float (*cagecos)[3] = data[1];
	SmallHash *hash = data[2];

	if (index >= 0 && index < em->bm->totvert && !BLI_smallhash_haskey(hash, index)) {
		BLI_smallhash_insert(hash, index, NULL);
		copy_v3_v3(cagecos[index], co);
	}
}

static void knifetool_update_mval(KnifeTool_OpData *kcd, int mval[2])
{
	knife_recalc_projmat(kcd);
	kcd->vc.mval[0] = mval[0];
	kcd->vc.mval[1] = mval[1];

	if (knife_update_active(kcd)) {
		ED_region_tag_redraw(kcd->ar);
	}
}

/* called when modal loop selection gets set up... */
static int knifetool_init(bContext *C, wmOperator *op, int UNUSED(do_cut))
{
	KnifeTool_OpData *kcd;
	Scene *scene = CTX_data_scene(C);
	Object *obedit = CTX_data_edit_object(C);
	DerivedMesh *cage, *final;
	SmallHash shash;
	void *data[3];
	const short only_select = RNA_boolean_get(op->ptr, "only_selected");

	/* alloc new customdata */
	kcd = op->customdata = MEM_callocN(sizeof(KnifeTool_OpData), "knifetool Modal Op Data");

	/* assign the drawing handle for drawing preview line... */
	kcd->ob = obedit;
	kcd->ar = CTX_wm_region(C);
	kcd->draw_handle = ED_region_draw_cb_activate(kcd->ar->type, knifetool_draw, kcd, REGION_DRAW_POST_VIEW);
	em_setup_viewcontext(C, &kcd->vc);

	kcd->em = BMEdit_FromObject(kcd->ob);

	BM_mesh_elem_index_ensure(kcd->em->bm, BM_VERT);

	cage = editbmesh_get_derived_cage_and_final(scene, obedit, kcd->em, &final, CD_MASK_DERIVEDMESH);
	kcd->cagecos = MEM_callocN(sizeof(float) * 3 * kcd->em->bm->totvert, "knife cagecos");
	data[0] = kcd->em;
	data[1] = kcd->cagecos;
	data[2] = &shash;

	BLI_smallhash_init(&shash);
	cage->foreachMappedVert(cage, cage_mapped_verts_callback, data);
	BLI_smallhash_release(&shash);

	kcd->bmbvh = BMBVH_NewBVH(kcd->em,
	                          (BMBVH_USE_CAGE | BMBVH_RETURN_ORIG) |
	                          (only_select ? BMBVH_RESPECT_SELECT : BMBVH_RESPECT_HIDDEN),
	                          scene, obedit);

	kcd->arena = BLI_memarena_new(1 << 15, "knife");
	kcd->vthresh = KMAXDIST - 1;
	kcd->ethresh = KMAXDIST;

	kcd->extend = 1;

	knife_recalc_projmat(kcd);

	ED_region_tag_redraw(kcd->ar);

	kcd->refs = BLI_mempool_create(sizeof(Ref), 1, 2048, 0);
	kcd->kverts = BLI_mempool_create(sizeof(KnifeVert), 1, 512, BLI_MEMPOOL_ALLOW_ITER);
	kcd->kedges = BLI_mempool_create(sizeof(KnifeEdge), 1, 512, BLI_MEMPOOL_ALLOW_ITER);

	kcd->origedgemap = BLI_ghash_ptr_new("knife origedgemap");
	kcd->origvertmap = BLI_ghash_ptr_new("knife origvertmap");
	kcd->kedgefacemap = BLI_ghash_ptr_new("knife origvertmap");

	/* cut all the way through the mesh if use_occlude_geometry button not pushed */
	kcd->cut_through = !RNA_boolean_get(op->ptr, "use_occlude_geometry");
	kcd->only_select = only_select;

	/* can't usefully select resulting edges in face mode */
	kcd->select_result = (kcd->em->selectmode != SCE_SELECT_FACE);

	knife_pos_data_clear(&kcd->curr);
	knife_pos_data_clear(&kcd->prev);

	knife_init_colors(&kcd->colors);

	return 1;
}

static int knifetool_cancel(bContext *C, wmOperator *op)
{
	/* this is just a wrapper around exit() */
	knifetool_exit(C, op);
	return OPERATOR_CANCELLED;
}

static int knifetool_invoke(bContext *C, wmOperator *op, wmEvent *evt)
{
	KnifeTool_OpData *kcd;

	view3d_operator_needs_opengl(C);

	if (!knifetool_init(C, op, 0))
		return OPERATOR_CANCELLED;

	/* add a modal handler for this operator - handles loop selection */
	WM_cursor_modal(CTX_wm_window(C), BC_KNIFECURSOR);
	WM_event_add_modal_handler(C, op);

	kcd = op->customdata;
	knifetool_update_mval(kcd, evt->mval);

	knife_update_header(C, kcd);

	return OPERATOR_RUNNING_MODAL;
}

enum {
	KNF_MODAL_CANCEL = 1,
	KNF_MODAL_CONFIRM,
	KNF_MODAL_MIDPOINT_ON,
	KNF_MODAL_MIDPOINT_OFF,
	KNF_MODAL_NEW_CUT,
	KNF_MODEL_IGNORE_SNAP_ON,
	KNF_MODEL_IGNORE_SNAP_OFF,
	KNF_MODAL_ADD_CUT,
	KNF_MODAL_ANGLE_SNAP_TOGGLE,
	KNF_MODAL_CUT_THROUGH_TOGGLE
};

wmKeyMap *knifetool_modal_keymap(wmKeyConfig *keyconf)
{
	static EnumPropertyItem modal_items[] = {
		{KNF_MODAL_CANCEL, "CANCEL", 0, "Cancel", ""},
		{KNF_MODAL_CONFIRM, "CONFIRM", 0, "Confirm", ""},
		{KNF_MODAL_MIDPOINT_ON, "SNAP_MIDPOINTS_ON", 0, "Snap To Midpoints On", ""},
		{KNF_MODAL_MIDPOINT_OFF, "SNAP_MIDPOINTS_OFF", 0, "Snap To Midpoints Off", ""},
		{KNF_MODEL_IGNORE_SNAP_ON, "IGNORE_SNAP_ON", 0, "Ignore Snapping On", ""},
		{KNF_MODEL_IGNORE_SNAP_OFF, "IGNORE_SNAP_OFF", 0, "Ignore Snapping Off", ""},
		{KNF_MODAL_ANGLE_SNAP_TOGGLE, "ANGLE_SNAP_TOGGLE", 0, "Toggle Angle Snapping", ""},
		{KNF_MODAL_CUT_THROUGH_TOGGLE, "CUT_THROUGH_TOGGLE", 0, "Toggle Cut Through", ""},
		{KNF_MODAL_NEW_CUT, "NEW_CUT", 0, "End Current Cut", ""},
		{KNF_MODAL_ADD_CUT, "ADD_CUT", 0, "Add Cut", ""},
		{0, NULL, 0, NULL, NULL}
	};

	wmKeyMap *keymap = WM_modalkeymap_get(keyconf, "Knife Tool Modal Map");

	/* this function is called for each spacetype, only needs to add map once */
	if (keymap && keymap->modal_items)
		return NULL;

	keymap = WM_modalkeymap_add(keyconf, "Knife Tool Modal Map", modal_items);

	/* items for modal map */
	WM_modalkeymap_add_item(keymap, ESCKEY, KM_PRESS, KM_ANY, 0, KNF_MODAL_CANCEL);
	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_PRESS, KM_ANY, 0, KNF_MODAL_ADD_CUT);
	WM_modalkeymap_add_item(keymap, RIGHTMOUSE, KM_PRESS, KM_ANY, 0, KNF_MODAL_CANCEL);
	WM_modalkeymap_add_item(keymap, RETKEY, KM_PRESS, KM_ANY, 0, KNF_MODAL_CONFIRM);
	WM_modalkeymap_add_item(keymap, PADENTER, KM_PRESS, KM_ANY, 0, KNF_MODAL_CONFIRM);
	WM_modalkeymap_add_item(keymap, SPACEKEY, KM_PRESS, KM_ANY, 0, KNF_MODAL_CONFIRM);
	WM_modalkeymap_add_item(keymap, EKEY, KM_PRESS, 0, 0, KNF_MODAL_NEW_CUT);

	WM_modalkeymap_add_item(keymap, LEFTCTRLKEY, KM_PRESS, KM_ANY, 0, KNF_MODAL_MIDPOINT_ON);
	WM_modalkeymap_add_item(keymap, LEFTCTRLKEY, KM_RELEASE, KM_ANY, 0, KNF_MODAL_MIDPOINT_OFF);
	WM_modalkeymap_add_item(keymap, RIGHTCTRLKEY, KM_PRESS, KM_ANY, 0, KNF_MODAL_MIDPOINT_ON);
	WM_modalkeymap_add_item(keymap, RIGHTCTRLKEY, KM_RELEASE, KM_ANY, 0, KNF_MODAL_MIDPOINT_OFF);

	WM_modalkeymap_add_item(keymap, LEFTSHIFTKEY, KM_PRESS, KM_ANY, 0, KNF_MODEL_IGNORE_SNAP_ON);
	WM_modalkeymap_add_item(keymap, LEFTSHIFTKEY, KM_RELEASE, KM_ANY, 0, KNF_MODEL_IGNORE_SNAP_OFF);
	WM_modalkeymap_add_item(keymap, RIGHTSHIFTKEY, KM_PRESS, KM_ANY, 0, KNF_MODEL_IGNORE_SNAP_ON);
	WM_modalkeymap_add_item(keymap, RIGHTSHIFTKEY, KM_RELEASE, KM_ANY, 0, KNF_MODEL_IGNORE_SNAP_OFF);

	WM_modalkeymap_add_item(keymap, CKEY, KM_PRESS, 0, 0, KNF_MODAL_ANGLE_SNAP_TOGGLE);
	WM_modalkeymap_add_item(keymap, ZKEY, KM_PRESS, 0, 0, KNF_MODAL_CUT_THROUGH_TOGGLE);

	WM_modalkeymap_assign(keymap, "MESH_OT_knife_tool");

	return keymap;
}

static int knifetool_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	Object *obedit = CTX_data_edit_object(C);
	KnifeTool_OpData *kcd = op->customdata;
	int do_refresh = FALSE;

	if (!obedit || obedit->type != OB_MESH || BMEdit_FromObject(obedit) != kcd->em) {
		knifetool_exit(C, op);
		ED_area_headerprint(CTX_wm_area(C), NULL);
		return OPERATOR_FINISHED;
	}

	view3d_operator_needs_opengl(C);
	ED_view3d_init_mats_rv3d(obedit, kcd->vc.rv3d);  /* needed to initialize clipping */

	if (kcd->mode == MODE_PANNING)
		kcd->mode = kcd->prevmode;

	/* handle modal keymap */
	if (event->type == EVT_MODAL_MAP) {
		switch (event->val) {
			case KNF_MODAL_CANCEL:
				/* finish */
				ED_region_tag_redraw(kcd->ar);

				knifetool_exit(C, op);
				ED_area_headerprint(CTX_wm_area(C), NULL);

				return OPERATOR_CANCELLED;
			case KNF_MODAL_CONFIRM:
				/* finish */
				ED_region_tag_redraw(kcd->ar);

				knifetool_finish(op);
				knifetool_exit(C, op);
				ED_area_headerprint(CTX_wm_area(C), NULL);

				return OPERATOR_FINISHED;
			case KNF_MODAL_MIDPOINT_ON:
				kcd->snap_midpoints = 1;

				knife_recalc_projmat(kcd);
				knife_update_active(kcd);
				knife_update_header(C, kcd);
				ED_region_tag_redraw(kcd->ar);
				do_refresh = TRUE;
				break;
			case KNF_MODAL_MIDPOINT_OFF:
				kcd->snap_midpoints = 0;

				knife_recalc_projmat(kcd);
				knife_update_active(kcd);
				knife_update_header(C, kcd);
				ED_region_tag_redraw(kcd->ar);
				do_refresh = TRUE;
				break;
			case KNF_MODEL_IGNORE_SNAP_ON:
				ED_region_tag_redraw(kcd->ar);
				kcd->ignore_vert_snapping = kcd->ignore_edge_snapping = 1;
				knife_update_header(C, kcd);
				do_refresh = TRUE;
				break;
			case KNF_MODEL_IGNORE_SNAP_OFF:
				ED_region_tag_redraw(kcd->ar);
				kcd->ignore_vert_snapping = kcd->ignore_edge_snapping = 0;
				knife_update_header(C, kcd);
				do_refresh = TRUE;
				break;
			case KNF_MODAL_ANGLE_SNAP_TOGGLE:
				kcd->angle_snapping = !kcd->angle_snapping;
				knife_update_header(C, kcd);
				do_refresh = TRUE;
				break;
			case KNF_MODAL_CUT_THROUGH_TOGGLE:
				kcd->cut_through = !kcd->cut_through;
				knife_update_header(C, kcd);
				do_refresh = TRUE;
				break;
			case KNF_MODAL_NEW_CUT:
				ED_region_tag_redraw(kcd->ar);
				knife_finish_cut(kcd);
				kcd->mode = MODE_IDLE;
				break;
			case KNF_MODAL_ADD_CUT:
				knife_recalc_projmat(kcd);

				if (kcd->mode == MODE_DRAGGING) {
					knife_add_cut(kcd);
					if (!kcd->extend) {
						knife_finish_cut(kcd);
						kcd->mode = MODE_IDLE;
					}
				}
				else if (kcd->mode != MODE_PANNING) {
					knife_start_cut(kcd);
					kcd->mode = MODE_DRAGGING;
				}

				ED_region_tag_redraw(kcd->ar);
				break;
		}
	}
	else { /* non-modal-mapped events */
		switch (event->type) {
			case WHEELUPMOUSE:
			case WHEELDOWNMOUSE:
				return OPERATOR_PASS_THROUGH;
			case MIDDLEMOUSE:
				if (event->val != KM_RELEASE) {
					if (kcd->mode != MODE_PANNING)
						kcd->prevmode = kcd->mode;
					kcd->mode = MODE_PANNING;
				}
				else {
					kcd->mode = kcd->prevmode;
				}

				ED_region_tag_redraw(kcd->ar);
				return OPERATOR_PASS_THROUGH;

			case MOUSEMOVE: /* mouse moved somewhere to select another loop */
				if (kcd->mode != MODE_PANNING) {
					knifetool_update_mval(kcd, event->mval);
				}

				break;
		}
	}

	if (do_refresh) {
		/* we don't really need to update mval,
		 * but this happens to be the best way to refresh at the moment */
		knifetool_update_mval(kcd, event->mval);
	}

	/* keep going until the user confirms */
	return OPERATOR_RUNNING_MODAL;
}

void MESH_OT_knife_tool(wmOperatorType *ot)
{
	/* description */
	ot->name = "Knife Topology Tool";
	ot->idname = "MESH_OT_knife_tool";
	ot->description = "Cut new topology";

	/* callbacks */
	ot->invoke = knifetool_invoke;
	ot->modal = knifetool_modal;
	ot->cancel = knifetool_cancel;
	ot->poll = ED_operator_editmesh_view3d;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO | OPTYPE_BLOCKING;

	RNA_def_boolean(ot->srna, "use_occlude_geometry", TRUE, "Occlude Geometry", "Only cut the front most geometry");
	RNA_def_boolean(ot->srna, "only_selected", FALSE, "Only Selected", "Only cut selected geometry");
}
