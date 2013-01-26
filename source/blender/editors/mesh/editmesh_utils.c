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
 * The Original Code is Copyright (C) 2004 by Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Joseph Eagar
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/mesh/editmesh_utils.c
 *  \ingroup edmesh
 */

#include "MEM_guardedalloc.h"

#include "DNA_mesh_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BLI_math.h"

#include "BKE_DerivedMesh.h"
#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_key.h"
#include "BKE_mesh.h"
#include "BKE_report.h"
#include "BKE_tessmesh.h"

#include "BKE_object.h"  /* XXX. only for EDBM_mesh_ensure_valid_dm_hack() which will be removed */

#include "WM_api.h"
#include "WM_types.h"

#include "ED_mesh.h"
#include "ED_util.h"


#include "mesh_intern.h"

/* mesh backup implementation. This would greatly benefit from some sort of binary diffing
 * just as the undo stack would. So leaving this as an interface for further work */

BMBackup EDBM_redo_state_store(BMEditMesh *em)
{
	BMBackup backup;
	backup.bmcopy = BM_mesh_copy(em->bm);
	return backup;
}

void EDBM_redo_state_restore(BMBackup backup, BMEditMesh *em, int recalctess)
{
	BMesh *tmpbm;
	if (!em || !backup.bmcopy)
		return;

	BM_mesh_data_free(em->bm);
	tmpbm = BM_mesh_copy(backup.bmcopy);
	*em->bm = *tmpbm;
	MEM_freeN(tmpbm);
	tmpbm = NULL;

	if (recalctess)
		BMEdit_RecalcTessellation(em);
}

void EDBM_redo_state_free(BMBackup *backup, BMEditMesh *em, int recalctess)
{
	if (em && backup->bmcopy) {
		BM_mesh_data_free(em->bm);
		*em->bm = *backup->bmcopy;
	}
	else if (backup->bmcopy) {
		BM_mesh_data_free(backup->bmcopy);
	}

	if (backup->bmcopy)
		MEM_freeN(backup->bmcopy);
	backup->bmcopy = NULL;

	if (recalctess && em)
		BMEdit_RecalcTessellation(em);
}

/* hack to workaround multiple operators being called within the same event loop without an update
 * see: [#31811] */
void EDBM_mesh_ensure_valid_dm_hack(Scene *scene, BMEditMesh *em)
{
	if ((((ID *)em->ob->data)->flag & LIB_ID_RECALC) ||
	    (em->ob->recalc & OB_RECALC_DATA))
	{
		em->ob->recalc |= OB_RECALC_DATA;  /* since we may not have done selection flushing */
		BKE_object_handle_update(scene, em->ob);
	}
}

void EDBM_mesh_normals_update(BMEditMesh *em)
{
	BM_mesh_normals_update(em->bm, TRUE);
}

void EDBM_mesh_clear(BMEditMesh *em)
{
	/* clear bmesh */
	BM_mesh_clear(em->bm);
	
	/* free derived meshes */
	if (em->derivedCage) {
		em->derivedCage->needsFree = 1;
		em->derivedCage->release(em->derivedCage);
	}
	if (em->derivedFinal && em->derivedFinal != em->derivedCage) {
		em->derivedFinal->needsFree = 1;
		em->derivedFinal->release(em->derivedFinal);
	}
	
	em->derivedCage = em->derivedFinal = NULL;
	
	/* free tessellation data */
	em->tottri = 0;
	if (em->looptris) 
		MEM_freeN(em->looptris);
}

void EDBM_stats_update(BMEditMesh *em)
{
	const char iter_types[3] = {BM_VERTS_OF_MESH,
	                            BM_EDGES_OF_MESH,
	                            BM_FACES_OF_MESH};

	BMIter iter;
	BMElem *ele;
	int *tots[3];
	int i;

	tots[0] = &em->bm->totvertsel;
	tots[1] = &em->bm->totedgesel;
	tots[2] = &em->bm->totfacesel;
	
	em->bm->totvertsel = em->bm->totedgesel = em->bm->totfacesel = 0;

	for (i = 0; i < 3; i++) {
		ele = BM_iter_new(&iter, em->bm, iter_types[i], NULL);
		for ( ; ele; ele = BM_iter_step(&iter)) {
			if (BM_elem_flag_test(ele, BM_ELEM_SELECT)) {
				(*tots[i])++;
			}
		}
	}
}

int EDBM_op_init(BMEditMesh *em, BMOperator *bmop, wmOperator *op, const char *fmt, ...)
{
	BMesh *bm = em->bm;
	va_list list;

	va_start(list, fmt);

	if (!BMO_op_vinitf(bm, bmop, BMO_FLAG_DEFAULTS, fmt, list)) {
		BKE_reportf(op->reports, RPT_ERROR, "Parse error in %s", __func__);
		va_end(list);
		return 0;
	}
	
	if (!em->emcopy)
		em->emcopy = BMEdit_Copy(em);
	em->emcopyusers++;

	va_end(list);

	return 1;
}


/* returns 0 on error, 1 on success.  executes and finishes a bmesh operator */
int EDBM_op_finish(BMEditMesh *em, BMOperator *bmop, wmOperator *op, const int report)
{
	const char *errmsg;
	
	BMO_op_finish(em->bm, bmop);

	if (BMO_error_get(em->bm, &errmsg, NULL)) {
		BMEditMesh *emcopy = em->emcopy;

		if (report) {
			BKE_report(op->reports, RPT_ERROR, errmsg);
		}

		EDBM_mesh_free(em);
		*em = *emcopy;

		MEM_freeN(emcopy);
		em->emcopyusers = 0;
		em->emcopy = NULL;

		/* when copying, tessellation isn't to for faster copying,
		 * but means we need to re-tessellate here */
		if (em->looptris == NULL) {
			BMEdit_RecalcTessellation(em);
		}

		return FALSE;
	}
	else {
		em->emcopyusers--;
		if (em->emcopyusers < 0) {
			printf("warning: em->emcopyusers was less then zero.\n");
		}

		if (em->emcopyusers <= 0) {
			BMEdit_Free(em->emcopy);
			MEM_freeN(em->emcopy);
			em->emcopy = NULL;
		}

		return TRUE;
	}
}

int EDBM_op_callf(BMEditMesh *em, wmOperator *op, const char *fmt, ...)
{
	BMesh *bm = em->bm;
	BMOperator bmop;
	va_list list;

	va_start(list, fmt);

	if (!BMO_op_vinitf(bm, &bmop, BMO_FLAG_DEFAULTS, fmt, list)) {
		BKE_reportf(op->reports, RPT_ERROR, "Parse error in %s", __func__);
		va_end(list);
		return 0;
	}

	if (!em->emcopy)
		em->emcopy = BMEdit_Copy(em);
	em->emcopyusers++;

	BMO_op_exec(bm, &bmop);

	va_end(list);
	return EDBM_op_finish(em, &bmop, op, TRUE);
}

int EDBM_op_call_and_selectf(BMEditMesh *em, wmOperator *op, const char *select_slot_out, const char *fmt, ...)
{
	BMOpSlot *slot_select_out;
	BMesh *bm = em->bm;
	BMOperator bmop;
	va_list list;
	char hflag;

	va_start(list, fmt);

	if (!BMO_op_vinitf(bm, &bmop, BMO_FLAG_DEFAULTS, fmt, list)) {
		BKE_reportf(op->reports, RPT_ERROR, "Parse error in %s", __func__);
		va_end(list);
		return 0;
	}

	if (!em->emcopy)
		em->emcopy = BMEdit_Copy(em);
	em->emcopyusers++;

	BMO_op_exec(bm, &bmop);

	slot_select_out = BMO_slot_get(bmop.slots_out, select_slot_out);
	hflag = slot_select_out->slot_subtype.elem & BM_ALL_NOLOOP;

	BM_mesh_elem_hflag_disable_all(em->bm, BM_VERT | BM_EDGE | BM_FACE, BM_ELEM_SELECT, FALSE);

	BMO_slot_buffer_hflag_enable(em->bm, bmop.slots_out, select_slot_out, hflag, BM_ELEM_SELECT, TRUE);

	va_end(list);
	return EDBM_op_finish(em, &bmop, op, TRUE);
}

int EDBM_op_call_silentf(BMEditMesh *em, const char *fmt, ...)
{
	BMesh *bm = em->bm;
	BMOperator bmop;
	va_list list;

	va_start(list, fmt);

	if (!BMO_op_vinitf(bm, &bmop, BMO_FLAG_DEFAULTS, fmt, list)) {
		va_end(list);
		return 0;
	}

	if (!em->emcopy)
		em->emcopy = BMEdit_Copy(em);
	em->emcopyusers++;

	BMO_op_exec(bm, &bmop);

	va_end(list);
	return EDBM_op_finish(em, &bmop, NULL, FALSE);
}

void EDBM_selectmode_to_scene(bContext *C)
{
	Scene *scene = CTX_data_scene(C);
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);

	if (!em)
		return;

	scene->toolsettings->selectmode = em->selectmode;

	/* Request redraw of header buttons (to show new select mode) */
	WM_event_add_notifier(C, NC_SCENE | ND_TOOLSETTINGS, scene);
}

void EDBM_mesh_make(ToolSettings *ts, Scene *UNUSED(scene), Object *ob)
{
	Mesh *me = ob->data;
	BMesh *bm;

	if (UNLIKELY(!me->mpoly && me->totface)) {
		BKE_mesh_convert_mfaces_to_mpolys(me);
	}

	bm = BKE_mesh_to_bmesh(me, ob);

	if (me->edit_btmesh) {
		/* this happens when switching shape keys */
		EDBM_mesh_free(me->edit_btmesh);
		MEM_freeN(me->edit_btmesh);
	}

	/* currently executing operators re-tessellates, so we can avoid doing here
	 * but at some point it may need to be added back. */
#if 0
	me->edit_btmesh = BMEdit_Create(bm, TRUE);
#else
	me->edit_btmesh = BMEdit_Create(bm, FALSE);
#endif

	me->edit_btmesh->selectmode = me->edit_btmesh->bm->selectmode = ts->selectmode;
	me->edit_btmesh->mat_nr = (ob->actcol > 0) ? ob->actcol - 1 : 0;

	me->edit_btmesh->ob = ob;
}

void EDBM_mesh_load(Object *ob)
{
	Mesh *me = ob->data;
	BMesh *bm = me->edit_btmesh->bm;

	BM_mesh_bm_to_me(bm, me, FALSE);

#ifdef USE_TESSFACE_DEFAULT
	BKE_mesh_tessface_calc(me);
#endif
}

/**
 * Should only be called on the active editmesh, otherwise call #BMEdit_Free
 */
void EDBM_mesh_free(BMEditMesh *em)
{
	/* These tables aren't used yet, so it's not strictly necessary
	 * to 'end' them (with 'e' param) but if someone tries to start
	 * using them, having these in place will save a lot of pain */
	mesh_octree_table(NULL, NULL, NULL, 'e');
	mesh_mirrtopo_table(NULL, 'e');

	BMEdit_Free(em);
}


void EDBM_index_arrays_ensure(BMEditMesh *em, const char htype)
{
	/* assume if the array is non-null then its valid and no need to recalc */
	const char htype_needed = ((em->vert_index ? 0 : BM_VERT) |
	                           (em->edge_index ? 0 : BM_EDGE) |
	                           (em->face_index ? 0 : BM_FACE)) & htype;

	BLI_assert((htype & ~BM_ALL_NOLOOP) == 0);

	/* in debug mode double check we didn't need to recalculate */
	BLI_assert(EDBM_index_arrays_check(em) == TRUE);

	if (htype_needed & BM_VERT) {
		em->vert_index = MEM_mallocN(sizeof(void **) * em->bm->totvert, "em->vert_index");
	}
	if (htype_needed & BM_EDGE) {
		em->edge_index = MEM_mallocN(sizeof(void **) * em->bm->totedge, "em->edge_index");
	}
	if (htype_needed & BM_FACE) {
		em->face_index = MEM_mallocN(sizeof(void **) * em->bm->totface, "em->face_index");
	}

#pragma omp parallel sections if (em->bm->totvert + em->bm->totedge + em->bm->totface >= BM_OMP_LIMIT)
	{
#pragma omp section
		{
			if (htype_needed & BM_VERT) {
				BM_iter_as_array(em->bm, BM_VERTS_OF_MESH, NULL, (void **)em->vert_index, em->bm->totvert);
			}
		}
#pragma omp section
		{
			if (htype_needed & BM_EDGE) {
				BM_iter_as_array(em->bm, BM_EDGES_OF_MESH, NULL, (void **)em->edge_index, em->bm->totedge);
			}
		}
#pragma omp section
		{
			if (htype_needed & BM_FACE) {
				BM_iter_as_array(em->bm, BM_FACES_OF_MESH, NULL, (void **)em->face_index, em->bm->totface);
			}
		}
	}
}

/* use EDBM_index_arrays_ensure where possible to avoid full rebuild */
void EDBM_index_arrays_init(BMEditMesh *em, const char htype)
{
	BLI_assert((htype & ~BM_ALL_NOLOOP) == 0);

	/* force recalc */
	EDBM_index_arrays_free(em);
	EDBM_index_arrays_ensure(em, htype);
}

void EDBM_index_arrays_free(BMEditMesh *em)
{
	if (em->vert_index) {
		MEM_freeN(em->vert_index);
		em->vert_index = NULL;
	}

	if (em->edge_index) {
		MEM_freeN(em->edge_index);
		em->edge_index = NULL;
	}

	if (em->face_index) {
		MEM_freeN(em->face_index);
		em->face_index = NULL;
	}
}

/* debug check only - no need to optimize */
#ifndef NDEBUG
int EDBM_index_arrays_check(BMEditMesh *em)
{
	BMIter iter;
	BMElem *ele;
	int i;

	if (em->vert_index) {
		BM_ITER_MESH_INDEX (ele, &iter, em->bm, BM_VERTS_OF_MESH, i) {
			if (ele != (BMElem *)em->vert_index[i]) {
				return FALSE;
			}
		}
	}

	if (em->edge_index) {
		BM_ITER_MESH_INDEX (ele, &iter, em->bm, BM_EDGES_OF_MESH, i) {
			if (ele != (BMElem *)em->edge_index[i]) {
				return FALSE;
			}
		}
	}

	if (em->face_index) {
		BM_ITER_MESH_INDEX (ele, &iter, em->bm, BM_FACES_OF_MESH, i) {
			if (ele != (BMElem *)em->face_index[i]) {
				return FALSE;
			}
		}
	}

	return TRUE;
}
#endif

BMVert *EDBM_vert_at_index(BMEditMesh *em, int index)
{
	return em->vert_index && index < em->bm->totvert ? em->vert_index[index] : NULL;
}

BMEdge *EDBM_edge_at_index(BMEditMesh *em, int index)
{
	return em->edge_index && index < em->bm->totedge ? em->edge_index[index] : NULL;
}

BMFace *EDBM_face_at_index(BMEditMesh *em, int index)
{
	return (em->face_index && index < em->bm->totface && index >= 0) ? em->face_index[index] : NULL;
}

void EDBM_selectmode_flush_ex(BMEditMesh *em, const short selectmode)
{
	BM_mesh_select_mode_flush_ex(em->bm, selectmode);
}

void EDBM_selectmode_flush(BMEditMesh *em)
{
	EDBM_selectmode_flush_ex(em, em->selectmode);
}

void EDBM_deselect_flush(BMEditMesh *em)
{
	/* function below doesnt use. just do this to keep the values in sync */
	em->bm->selectmode = em->selectmode;
	BM_mesh_deselect_flush(em->bm);
}


void EDBM_select_flush(BMEditMesh *em)
{
	/* function below doesnt use. just do this to keep the values in sync */
	em->bm->selectmode = em->selectmode;
	BM_mesh_select_flush(em->bm);
}

void EDBM_select_more(BMEditMesh *em)
{
	BMOperator bmop;
	int use_faces = em->selectmode == SCE_SELECT_FACE;

	BMO_op_initf(em->bm, &bmop, BMO_FLAG_DEFAULTS,
	             "region_extend geom=%hvef use_constrict=%b use_faces=%b",
	             BM_ELEM_SELECT, FALSE, use_faces);
	BMO_op_exec(em->bm, &bmop);
	/* don't flush selection in edge/vertex mode  */
	BMO_slot_buffer_hflag_enable(em->bm, bmop.slots_out, "geom.out", BM_ALL_NOLOOP, BM_ELEM_SELECT, use_faces ? TRUE : FALSE);
	BMO_op_finish(em->bm, &bmop);

	EDBM_selectmode_flush(em);
}

void EDBM_select_less(BMEditMesh *em)
{
	BMOperator bmop;
	int use_faces = em->selectmode == SCE_SELECT_FACE;

	BMO_op_initf(em->bm, &bmop, BMO_FLAG_DEFAULTS,
	             "region_extend geom=%hvef use_constrict=%b use_faces=%b",
	             BM_ELEM_SELECT, TRUE, use_faces);
	BMO_op_exec(em->bm, &bmop);
	/* don't flush selection in edge/vertex mode  */
	BMO_slot_buffer_hflag_disable(em->bm, bmop.slots_out, "geom.out", BM_ALL_NOLOOP, BM_ELEM_SELECT, use_faces ? TRUE : FALSE);
	BMO_op_finish(em->bm, &bmop);

	EDBM_selectmode_flush(em);
}

void EDBM_flag_disable_all(BMEditMesh *em, const char hflag)
{
	BM_mesh_elem_hflag_disable_all(em->bm, BM_VERT | BM_EDGE | BM_FACE, hflag, FALSE);
}

void EDBM_flag_enable_all(BMEditMesh *em, const char hflag)
{
	BM_mesh_elem_hflag_enable_all(em->bm, BM_VERT | BM_EDGE | BM_FACE, hflag, TRUE);
}

/**************-------------- Undo ------------*****************/

/* for callbacks */

static void *getEditMesh(bContext *C)
{
	Object *obedit = CTX_data_edit_object(C);
	if (obedit && obedit->type == OB_MESH) {
		Mesh *me = obedit->data;
		return me->edit_btmesh;
	}
	return NULL;
}

typedef struct UndoMesh {
	Mesh me;
	int selectmode;

	/** \note
	 * this isn't a prefect solution, if you edit keys and change shapes this works well (fixing [#32442]),
	 * but editing shape keys, going into object mode, removing or changing their order,
	 * then go back into editmode and undo will give issues - where the old index will be out of sync
	 * with the new object index.
	 *
	 * There are a few ways this could be made to work but for now its a known limitation with mixing
	 * object and editmode operations - Campbell */
	int shapenr;
} UndoMesh;

/* undo simply makes copies of a bmesh */
static void *editbtMesh_to_undoMesh(void *emv, void *obdata)
{
	BMEditMesh *em = emv;
	Mesh *obme = obdata;
	
	UndoMesh *um = MEM_callocN(sizeof(UndoMesh), "undo Mesh");
	
	/* make sure shape keys work */
	um->me.key = obme->key ? BKE_key_copy_nolib(obme->key) : NULL;

	/* BM_mesh_validate(em->bm); */ /* for troubleshooting */

	BM_mesh_bm_to_me(em->bm, &um->me, FALSE);

	um->selectmode = em->selectmode;
	um->shapenr = em->bm->shapenr;

	return um;
}

static void undoMesh_to_editbtMesh(void *umv, void *em_v, void *UNUSED(obdata))
{
	BMEditMesh *em = em_v, *em_tmp;
	Object *ob = em->ob;
	UndoMesh *um = umv;
	BMesh *bm;

	ob->shapenr = em->bm->shapenr = um->shapenr;

	EDBM_mesh_free(em);

	bm = BM_mesh_create(&bm_mesh_allocsize_default);

	BM_mesh_bm_from_me(bm, &um->me, FALSE, ob->shapenr);

	/* face normals need recalculation since we are not calling through an operator */
	BM_mesh_normals_update(bm, TRUE);

	em_tmp = BMEdit_Create(bm, TRUE);
	*em = *em_tmp;
	
	em->selectmode = um->selectmode;
	bm->selectmode = um->selectmode;
	em->ob = ob;

	MEM_freeN(em_tmp);
}

static void free_undo(void *me_v)
{
	Mesh *me = me_v;
	if (me->key) {
		BKE_key_free(me->key);
		MEM_freeN(me->key);
	}

	BKE_mesh_free(me, FALSE);
	MEM_freeN(me);
}

/* and this is all the undo system needs to know */
void undo_push_mesh(bContext *C, const char *name)
{
	/* em->ob gets out of date and crashes on mesh undo,
	 * this is an easy way to ensure its OK
	 * though we could investigate the matter further. */
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	em->ob = obedit;

	undo_editmode_push(C, name, getEditMesh, free_undo, undoMesh_to_editbtMesh, editbtMesh_to_undoMesh, NULL);
}

/**
 * Return a new UVVertMap from the editmesh
 */
UvVertMap *EDBM_uv_vert_map_create(BMEditMesh *em, bool use_select, const float limit[2])
{
	BMVert *ev;
	BMFace *efa;
	BMLoop *l;
	BMIter iter, liter;
	/* vars from original func */
	UvVertMap *vmap;
	UvMapVert *buf;
	/* MTexPoly *tf; */ /* UNUSED */
	MLoopUV *luv;
	unsigned int a;
	int totverts, i, totuv;
	const int cd_loop_uv_offset = CustomData_get_offset(&em->bm->ldata, CD_MLOOPUV);

	BM_mesh_elem_index_ensure(em->bm, BM_VERT | BM_FACE);
	
	totverts = em->bm->totvert;
	totuv = 0;

	/* generate UvMapVert array */
	BM_ITER_MESH (efa, &iter, em->bm, BM_FACES_OF_MESH) {
		if ((use_select == false) || BM_elem_flag_test(efa, BM_ELEM_SELECT)) {
			totuv += efa->len;
		}
	}

	if (totuv == 0) {
		return NULL;
	}
	vmap = (UvVertMap *)MEM_callocN(sizeof(*vmap), "UvVertMap");
	if (!vmap) {
		return NULL;
	}

	vmap->vert = (UvMapVert **)MEM_callocN(sizeof(*vmap->vert) * totverts, "UvMapVert_pt");
	buf = vmap->buf = (UvMapVert *)MEM_callocN(sizeof(*vmap->buf) * totuv, "UvMapVert");

	if (!vmap->vert || !vmap->buf) {
		BKE_mesh_uv_vert_map_free(vmap);
		return NULL;
	}
	
	a = 0;
	BM_ITER_MESH (efa, &iter, em->bm, BM_FACES_OF_MESH) {
		if ((use_select == false) || BM_elem_flag_test(efa, BM_ELEM_SELECT)) {
			i = 0;
			BM_ITER_ELEM (l, &liter, efa, BM_LOOPS_OF_FACE) {
				buf->tfindex = i;
				buf->f = a;
				buf->separate = 0;
				
				buf->next = vmap->vert[BM_elem_index_get(l->v)];
				vmap->vert[BM_elem_index_get(l->v)] = buf;
				
				buf++;
				i++;
			}
		}

		a++;
	}
	
	/* sort individual uvs for each vert */
	a = 0;
	BM_ITER_MESH (ev, &iter, em->bm, BM_VERTS_OF_MESH) {
		UvMapVert *newvlist = NULL, *vlist = vmap->vert[a];
		UvMapVert *iterv, *v, *lastv, *next;
		float *uv, *uv2, uvdiff[2];

		while (vlist) {
			v = vlist;
			vlist = vlist->next;
			v->next = newvlist;
			newvlist = v;

			efa = EDBM_face_at_index(em, v->f);
			/* tf = CustomData_bmesh_get(&em->bm->pdata, efa->head.data, CD_MTEXPOLY); */ /* UNUSED */
			
			l = BM_iter_at_index(em->bm, BM_LOOPS_OF_FACE, efa, v->tfindex);
			luv = BM_ELEM_CD_GET_VOID_P(l, cd_loop_uv_offset);
			uv = luv->uv;
			
			lastv = NULL;
			iterv = vlist;

			while (iterv) {
				next = iterv->next;
				efa = EDBM_face_at_index(em, iterv->f);
				/* tf = CustomData_bmesh_get(&em->bm->pdata, efa->head.data, CD_MTEXPOLY); */ /* UNUSED */
				
				l = BM_iter_at_index(em->bm, BM_LOOPS_OF_FACE, efa, iterv->tfindex);
				luv = BM_ELEM_CD_GET_VOID_P(l, cd_loop_uv_offset);
				uv2 = luv->uv;
				
				sub_v2_v2v2(uvdiff, uv2, uv);

				if (fabsf(uvdiff[0]) < limit[0] && fabsf(uvdiff[1]) < limit[1]) {
					if (lastv) lastv->next = next;
					else vlist = next;
					iterv->next = newvlist;
					newvlist = iterv;
				}
				else {
					lastv = iterv;
				}

				iterv = next;
			}

			newvlist->separate = 1;
		}

		vmap->vert[a] = newvlist;
		a++;
	}

	return vmap;
}


UvMapVert *EDBM_uv_vert_map_at_index(UvVertMap *vmap, unsigned int v)
{
	return vmap->vert[v];
}

/* from editmesh_lib.c in trunk */


/* A specialized vert map used by stitch operator */
UvElementMap *EDBM_uv_element_map_create(BMEditMesh *em, int selected, int do_islands)
{
	BMVert *ev;
	BMFace *efa;
	BMLoop *l;
	BMIter iter, liter;
	/* vars from original func */
	UvElementMap *element_map;
	UvElement *buf;
	UvElement *islandbuf;
	/* island number for faces */
	int *island_number;

	MLoopUV *luv;
	int totverts, i, totuv, j, nislands = 0, islandbufsize = 0;

	unsigned int *map;
	BMFace **stack;
	int stacksize = 0;

	const int cd_loop_uv_offset = CustomData_get_offset(&em->bm->ldata, CD_MLOOPUV);

	BM_mesh_elem_index_ensure(em->bm, BM_VERT | BM_FACE);

	totverts = em->bm->totvert;
	totuv = 0;

	island_number = MEM_mallocN(sizeof(*stack) * em->bm->totface, "uv_island_number_face");
	if (!island_number) {
		return NULL;
	}

	/* generate UvElement array */
	BM_ITER_MESH (efa, &iter, em->bm, BM_FACES_OF_MESH) {
		if (!selected || BM_elem_flag_test(efa, BM_ELEM_SELECT)) {
			totuv += efa->len;
		}
	}

	if (totuv == 0) {
		MEM_freeN(island_number);
		return NULL;
	}
	element_map = (UvElementMap *)MEM_callocN(sizeof(*element_map), "UvElementMap");
	if (!element_map) {
		MEM_freeN(island_number);
		return NULL;
	}
	element_map->totalUVs = totuv;
	element_map->vert = (UvElement **)MEM_callocN(sizeof(*element_map->vert) * totverts, "UvElementVerts");
	buf = element_map->buf = (UvElement *)MEM_callocN(sizeof(*element_map->buf) * totuv, "UvElement");

	if (!element_map->vert || !element_map->buf) {
		EDBM_uv_element_map_free(element_map);
		MEM_freeN(island_number);
		return NULL;
	}

	j = 0;
	BM_ITER_MESH (efa, &iter, em->bm, BM_FACES_OF_MESH) {
		island_number[j++] = INVALID_ISLAND;
		if (!selected || BM_elem_flag_test(efa, BM_ELEM_SELECT)) {
			BM_ITER_ELEM_INDEX (l, &liter, efa, BM_LOOPS_OF_FACE, i) {
				buf->l = l;
				buf->separate = 0;
				buf->island = INVALID_ISLAND;
				buf->tfindex = i;

				buf->next = element_map->vert[BM_elem_index_get(l->v)];
				element_map->vert[BM_elem_index_get(l->v)] = buf;

				buf++;
			}
		}
	}

	/* sort individual uvs for each vert */
	i = 0;
	BM_ITER_MESH (ev, &iter, em->bm, BM_VERTS_OF_MESH) {
		UvElement *newvlist = NULL, *vlist = element_map->vert[i];
		UvElement *iterv, *v, *lastv, *next;
		float *uv, *uv2, uvdiff[2];

		while (vlist) {
			v = vlist;
			vlist = vlist->next;
			v->next = newvlist;
			newvlist = v;

			l = v->l;
			luv = BM_ELEM_CD_GET_VOID_P(l, cd_loop_uv_offset);
			uv = luv->uv;

			lastv = NULL;
			iterv = vlist;

			while (iterv) {
				next = iterv->next;

				l = iterv->l;
				luv = BM_ELEM_CD_GET_VOID_P(l, cd_loop_uv_offset);
				uv2 = luv->uv;

				sub_v2_v2v2(uvdiff, uv2, uv);

				if (fabsf(uvdiff[0]) < STD_UV_CONNECT_LIMIT && fabsf(uvdiff[1]) < STD_UV_CONNECT_LIMIT) {
					if (lastv) lastv->next = next;
					else vlist = next;
					iterv->next = newvlist;
					newvlist = iterv;
				}
				else {
					lastv = iterv;
				}

				iterv = next;
			}

			newvlist->separate = 1;
		}

		element_map->vert[i] = newvlist;
		i++;
	}

	if (do_islands) {
		/* map holds the map from current vmap->buf to the new, sorted map */
		map = MEM_mallocN(sizeof(*map) * totuv, "uvelement_remap");
		stack = MEM_mallocN(sizeof(*stack) * em->bm->totface, "uv_island_face_stack");
		islandbuf = MEM_callocN(sizeof(*islandbuf) * totuv, "uvelement_island_buffer");

		/* at this point, every UvElement in vert points to a UvElement sharing the same vertex. Now we should sort uv's in islands. */
		for (i = 0; i < totuv; i++) {
			if (element_map->buf[i].island == INVALID_ISLAND) {
				element_map->buf[i].island = nislands;
				stack[0] = element_map->buf[i].l->f;
				island_number[BM_elem_index_get(stack[0])] = nislands;
				stacksize = 1;

				while (stacksize > 0) {
					efa = stack[--stacksize];

					BM_ITER_ELEM (l, &liter, efa, BM_LOOPS_OF_FACE) {
						UvElement *element, *initelement = element_map->vert[BM_elem_index_get(l->v)];

						for (element = initelement; element; element = element->next) {
							if (element->separate)
								initelement = element;

							if (element->l->f == efa) {
								/* found the uv corresponding to our face and vertex. Now fill it to the buffer */
								element->island = nislands;
								map[element - element_map->buf] = islandbufsize;
								islandbuf[islandbufsize].l = element->l;
								islandbuf[islandbufsize].separate = element->separate;
								islandbuf[islandbufsize].tfindex = element->tfindex;
								islandbuf[islandbufsize].island =  nislands;
								islandbufsize++;

								for (element = initelement; element; element = element->next) {
									if (element->separate && element != initelement)
										break;

									if (island_number[BM_elem_index_get(element->l->f)] == INVALID_ISLAND) {
										stack[stacksize++] = element->l->f;
										island_number[BM_elem_index_get(element->l->f)] = nislands;
									}
								}
								break;
							}
						}
					}
				}

				nislands++;
			}
		}

		/* remap */
		for (i = 0; i < em->bm->totvert; i++) {
			/* important since we may do selection only. Some of these may be NULL */
			if (element_map->vert[i])
				element_map->vert[i] = &islandbuf[map[element_map->vert[i] - element_map->buf]];
		}

		element_map->islandIndices = MEM_callocN(sizeof(*element_map->islandIndices) * nislands, "UvElementMap_island_indices");
		if (!element_map->islandIndices) {
			MEM_freeN(islandbuf);
			MEM_freeN(stack);
			MEM_freeN(map);
			EDBM_uv_element_map_free(element_map);
			MEM_freeN(island_number);
		}

		j = 0;
		for (i = 0; i < totuv; i++) {
			UvElement *element = element_map->buf[i].next;
			if (element == NULL)
				islandbuf[map[i]].next = NULL;
			else
				islandbuf[map[i]].next = &islandbuf[map[element - element_map->buf]];

			if (islandbuf[i].island != j) {
				j++;
				element_map->islandIndices[j] = i;
			}
		}

		MEM_freeN(element_map->buf);

		element_map->buf = islandbuf;
		element_map->totalIslands = nislands;
		MEM_freeN(stack);
		MEM_freeN(map);
	}
	MEM_freeN(island_number);

	return element_map;
}

void EDBM_uv_vert_map_free(UvVertMap *vmap)
{
	if (vmap) {
		if (vmap->vert) MEM_freeN(vmap->vert);
		if (vmap->buf) MEM_freeN(vmap->buf);
		MEM_freeN(vmap);
	}
}

void EDBM_uv_element_map_free(UvElementMap *element_map)
{
	if (element_map) {
		if (element_map->vert) MEM_freeN(element_map->vert);
		if (element_map->buf) MEM_freeN(element_map->buf);
		if (element_map->islandIndices) MEM_freeN(element_map->islandIndices);
		MEM_freeN(element_map);
	}
}

UvElement *ED_uv_element_get(UvElementMap *map, BMFace *efa, BMLoop *l)
{
	UvElement *element;

	element = map->vert[BM_elem_index_get(l->v)];

	for (; element; element = element->next)
		if (element->l->f == efa)
			return element;

	return NULL;
}

/* last_sel, use em->act_face otherwise get the last selected face in the editselections
 * at the moment, last_sel is mainly useful for making sure the space image dosnt flicker */
MTexPoly *EDBM_mtexpoly_active_get(BMEditMesh *em, BMFace **r_act_efa, int sloppy, int selected)
{
	BMFace *efa = NULL;
	
	if (!EDBM_mtexpoly_check(em))
		return NULL;
	
	efa = BM_active_face_get(em->bm, sloppy, selected);

	if (efa) {
		if (r_act_efa) *r_act_efa = efa;
		return CustomData_bmesh_get(&em->bm->pdata, efa->head.data, CD_MTEXPOLY);
	}

	if (r_act_efa) *r_act_efa = NULL;
	return NULL;
}

/* can we edit UV's for this mesh?*/
int EDBM_mtexpoly_check(BMEditMesh *em)
{
	/* some of these checks could be a touch overkill */
	return em && em->bm->totface && CustomData_has_layer(&em->bm->pdata, CD_MTEXPOLY) &&
	       CustomData_has_layer(&em->bm->ldata, CD_MLOOPUV);
}

int EDBM_vert_color_check(BMEditMesh *em)
{
	/* some of these checks could be a touch overkill */
	return em && em->bm->totface && CustomData_has_layer(&em->bm->ldata, CD_MLOOPCOL);
}

static BMVert *cache_mirr_intptr_as_bmvert(intptr_t *index_lookup, int index)
{
	intptr_t eve_i = index_lookup[index];
	return (eve_i == -1) ? NULL : (BMVert *)eve_i;
}

/**
 * [note: I've decided to use ideasman's code for non-editmode stuff, but since
 *  it has a big "not for editmode!" disclaimer, I'm going to keep what I have here
 *  - joeedh]
 *
 * x-mirror editing api.  usage:
 *
 *  EDBM_verts_mirror_cache_begin(em);
 *  ...
 *  ...
 *  BM_ITER_MESH (v, &iter, em->bm, BM_VERTS_OF_MESH) {
 *     mirrorv = EDBM_verts_mirror_get(em, v);
 *  }
 *  ...
 *  ...
 *  EDBM_verts_mirror_cache_end(em);
 *
 * \note why do we only allow x axis mirror editing?
 */

/* BM_SEARCH_MAXDIST is too big, copied from 2.6x MOC_THRESH, should become a
 * preference */
#define BM_SEARCH_MAXDIST_MIRR 0.00002f
#define BM_CD_LAYER_ID "__mirror_index"
void EDBM_verts_mirror_cache_begin(BMEditMesh *em, const short use_select)
{
	Mesh *me = (Mesh *)em->ob->data;
	BMesh *bm = em->bm;
	BMIter iter;
	BMVert *v;
	int li, topo = 0;

	/* one or the other is used depending if topo is enabled */
	struct BMBVHTree *tree = NULL;
	MirrTopoStore_t mesh_topo_store = {NULL, -1, -1, -1};

	if (me && (me->editflag & ME_EDIT_MIRROR_TOPO)) {
		topo = 1;
	}

	EDBM_index_arrays_ensure(em, BM_VERT);

	if (!CustomData_get_layer_named(&bm->vdata, CD_PROP_INT, BM_CD_LAYER_ID)) {
		BM_data_layer_add_named(bm, &bm->vdata, CD_PROP_INT, BM_CD_LAYER_ID);
	}

	li = CustomData_get_named_layer_index(&bm->vdata, CD_PROP_INT, BM_CD_LAYER_ID);

	bm->vdata.layers[li].flag |= CD_FLAG_TEMPORARY;

	BM_mesh_elem_index_ensure(bm, BM_VERT);

	if (topo) {
		ED_mesh_mirrtopo_init(me, -1, &mesh_topo_store, TRUE);
	}
	else {
		tree = BMBVH_NewBVH(em, 0, NULL, NULL);
	}

	BM_ITER_MESH (v, &iter, bm, BM_VERTS_OF_MESH) {

		/* temporary for testing, check for selection */
		if (use_select && !BM_elem_flag_test(v, BM_ELEM_SELECT)) {
			/* do nothing */
		}
		else {
			BMVert *mirr;
			int *idx = CustomData_bmesh_get_layer_n(&bm->vdata, v->head.data, li);

			if (topo) {
				mirr = cache_mirr_intptr_as_bmvert(mesh_topo_store.index_lookup, BM_elem_index_get(v));
			}
			else {
				float co[3] = {-v->co[0], v->co[1], v->co[2]};
				mirr = BMBVH_FindClosestVert(tree, co, BM_SEARCH_MAXDIST_MIRR);
			}

			if (mirr && mirr != v) {
				*idx = BM_elem_index_get(mirr);
				idx = CustomData_bmesh_get_layer_n(&bm->vdata, mirr->head.data, li);
				*idx = BM_elem_index_get(v);
			}
			else {
				*idx = -1;
			}
		}

	}


	if (topo) {
		ED_mesh_mirrtopo_free(&mesh_topo_store);
	}
	else {
		BMBVH_FreeBVH(tree);
	}

	em->mirror_cdlayer = li;
}

BMVert *EDBM_verts_mirror_get(BMEditMesh *em, BMVert *v)
{
	int *mirr = CustomData_bmesh_get_layer_n(&em->bm->vdata, v->head.data, em->mirror_cdlayer);

	BLI_assert(em->mirror_cdlayer != -1); /* invalid use */

	if (mirr && *mirr >= 0 && *mirr < em->bm->totvert) {
		if (!em->vert_index) {
			printf("err: should only be called between "
			       "EDBM_verts_mirror_cache_begin and EDBM_verts_mirror_cache_end");
			return NULL;
		}

		return em->vert_index[*mirr];
	}

	return NULL;
}

void EDBM_verts_mirror_cache_clear(BMEditMesh *em, BMVert *v)
{
	int *mirr = CustomData_bmesh_get_layer_n(&em->bm->vdata, v->head.data, em->mirror_cdlayer);

	BLI_assert(em->mirror_cdlayer != -1); /* invalid use */

	if (mirr) {
		*mirr = -1;
	}
}

void EDBM_verts_mirror_cache_end(BMEditMesh *em)
{
	em->mirror_cdlayer = -1;
}

void EDBM_verts_mirror_apply(BMEditMesh *em, const int sel_from, const int sel_to)
{
	BMIter iter;
	BMVert *v;

	BLI_assert(em->vert_index != NULL);

	BM_ITER_MESH (v, &iter, em->bm, BM_VERTS_OF_MESH) {
		if (BM_elem_flag_test(v, BM_ELEM_SELECT) == sel_from) {
			BMVert *mirr = EDBM_verts_mirror_get(em, v);
			if (mirr) {
				if (BM_elem_flag_test(mirr, BM_ELEM_SELECT) == sel_to) {
					copy_v3_v3(mirr->co, v->co);
					mirr->co[0] *= -1.0f;
				}
			}
		}
	}
}


/* swap is 0 or 1, if 1 it hides not selected */
void EDBM_mesh_hide(BMEditMesh *em, int swap)
{
	BMIter iter;
	BMElem *ele;
	int itermode;

	if (em == NULL) return;

	if (em->selectmode & SCE_SELECT_VERTEX)
		itermode = BM_VERTS_OF_MESH;
	else if (em->selectmode & SCE_SELECT_EDGE)
		itermode = BM_EDGES_OF_MESH;
	else
		itermode = BM_FACES_OF_MESH;

	BM_ITER_MESH (ele, &iter, em->bm, itermode) {
		if (BM_elem_flag_test(ele, BM_ELEM_SELECT) ^ swap)
			BM_elem_hide_set(em->bm, ele, TRUE);
	}

	EDBM_selectmode_flush(em);

	/* original hide flushing comment (OUTDATED):
	 * hide happens on least dominant select mode, and flushes up, not down! (helps preventing errors in subsurf) */
	/* - vertex hidden, always means edge is hidden too
	 * - edge hidden, always means face is hidden too
	 * - face hidden, only set face hide
	 * - then only flush back down what's absolute hidden
	 */
}


void EDBM_mesh_reveal(BMEditMesh *em)
{
	const char iter_types[3] = {BM_VERTS_OF_MESH,
	                            BM_EDGES_OF_MESH,
	                            BM_FACES_OF_MESH};

	int sels[3] = {(em->selectmode & SCE_SELECT_VERTEX),
	               (em->selectmode & SCE_SELECT_EDGE),
	               (em->selectmode & SCE_SELECT_FACE), };
	int i;

	/* Use tag flag to remember what was hidden before all is revealed.
	 * BM_ELEM_HIDDEN --> BM_ELEM_TAG */
#pragma omp parallel for schedule(dynamic) if (em->bm->totvert + em->bm->totedge + em->bm->totface >= BM_OMP_LIMIT)
	for (i = 0; i < 3; i++) {
		BMIter iter;
		BMElem *ele;

		BM_ITER_MESH (ele, &iter, em->bm, iter_types[i]) {
			BM_elem_flag_set(ele, BM_ELEM_TAG, BM_elem_flag_test(ele, BM_ELEM_HIDDEN));
		}
	}

	/* Reveal everything */
	EDBM_flag_disable_all(em, BM_ELEM_HIDDEN);

	/* Select relevant just-revealed elements */
	for (i = 0; i < 3; i++) {
		BMIter iter;
		BMElem *ele;

		if (!sels[i]) {
			continue;
		}

		BM_ITER_MESH (ele, &iter, em->bm, iter_types[i]) {
			if (BM_elem_flag_test(ele, BM_ELEM_TAG)) {
				BM_elem_select_set(em->bm, ele, TRUE);
			}
		}
	}

	EDBM_selectmode_flush(em);

	/* hidden faces can have invalid normals */
	EDBM_mesh_normals_update(em);
}

/* so many tools call these that we better make it a generic function.
 */
void EDBM_update_generic(BMEditMesh *em, const bool do_tessface, const bool is_destructive)
{
	Object *ob = em->ob;
	/* order of calling isn't important */
	DAG_id_tag_update(ob->data, OB_RECALC_DATA);
	WM_main_add_notifier(NC_GEOM | ND_DATA, ob->data);

	if (do_tessface) {
		BMEdit_RecalcTessellation(em);
	}

	if (is_destructive) {
		EDBM_index_arrays_free(em);
	}
	else {
		/* in debug mode double check we didn't need to recalculate */
		BLI_assert(EDBM_index_arrays_check(em) == TRUE);
	}
}
