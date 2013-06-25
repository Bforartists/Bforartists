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
 * Contributor(s): Joseph Eagar, Howard Trickey, Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/mesh/editmesh_bevel.c
 *  \ingroup edmesh
 */

#include "MEM_guardedalloc.h"

#include "DNA_object_types.h"

#include "BLI_string.h"
#include "BLI_math.h"

#include "BLF_translation.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_editmesh.h"

#include "RNA_define.h"
#include "RNA_access.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_mesh.h"
#include "ED_numinput.h"
#include "ED_screen.h"
#include "ED_space_api.h"
#include "ED_transform.h"
#include "ED_view3d.h"

#include "mesh_intern.h"  /* own include */


#define MVAL_PIXEL_MARGIN  5.0f

typedef struct {
	BMEditMesh *em;
	float initial_length;
	float pixel_size;  /* use when mouse input is interpreted as spatial distance */
	bool is_modal;
	NumInput num_input;
	float shift_factor; /* The current factor when shift is pressed. Negative when shift not active. */

	/* modal only */
	int mcenter[2];
	BMBackup mesh_backup;
	void *draw_handle_pixel;
	short twtype;
} BevelData;

#define HEADER_LENGTH 180

static void edbm_bevel_update_header(wmOperator *op, bContext *C)
{
	const char *str = IFACE_("Confirm: Enter/LClick, Cancel: (Esc/RMB), Offset: %s, Segments: %d");

	char msg[HEADER_LENGTH];
	ScrArea *sa = CTX_wm_area(C);

	if (sa) {
		char offset_str[NUM_STR_REP_LEN];
		BLI_snprintf(offset_str, NUM_STR_REP_LEN, "%f", RNA_float_get(op->ptr, "offset"));
		BLI_snprintf(msg, HEADER_LENGTH, str,
		             offset_str,
		             RNA_int_get(op->ptr, "segments")
		            );

		ED_area_headerprint(sa, msg);
	}
}

static bool edbm_bevel_init(bContext *C, wmOperator *op, const bool is_modal)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BKE_editmesh_from_object(obedit);
	BevelData *opdata;

	if (em->bm->totvertsel == 0) {
		return false;
	}

	op->customdata = opdata = MEM_mallocN(sizeof(BevelData), "beveldata_mesh_operator");

	opdata->em = em;
	opdata->is_modal = is_modal;
	opdata->shift_factor = -1.0f;

	initNumInput(&opdata->num_input);
	opdata->num_input.flag = NUM_NO_NEGATIVE;

	/* avoid the cost of allocating a bm copy */
	if (is_modal) {
		View3D *v3d = CTX_wm_view3d(C);
		ARegion *ar = CTX_wm_region(C);

		opdata->mesh_backup = EDBM_redo_state_store(em);
		opdata->draw_handle_pixel = ED_region_draw_cb_activate(ar->type, ED_region_draw_mouse_line_cb, opdata->mcenter, REGION_DRAW_POST_PIXEL);
		G.moving = G_TRANSFORM_EDIT;
		opdata->twtype = v3d->twtype;
		v3d->twtype = 0;
	}

	return true;
}

static bool edbm_bevel_calc(wmOperator *op)
{
	BevelData *opdata = op->customdata;
	BMEditMesh *em = opdata->em;
	BMOperator bmop;
	const float offset = RNA_float_get(op->ptr, "offset");
	const int segments = RNA_int_get(op->ptr, "segments");
	const bool vertex_only = RNA_boolean_get(op->ptr, "vertex_only");

	/* revert to original mesh */
	if (opdata->is_modal) {
		EDBM_redo_state_restore(opdata->mesh_backup, em, false);
	}

	EDBM_op_init(em, &bmop, op,
	             "bevel geom=%hev offset=%f segments=%i vertex_only=%b",
	             BM_ELEM_SELECT, offset, segments, vertex_only);

	BMO_op_exec(em->bm, &bmop);

	if (offset != 0.0f) {
		/* not essential, but we may have some loose geometry that
		 * won't get bevel'd and better not leave it selected */
		EDBM_flag_disable_all(em, BM_ELEM_SELECT);
		BMO_slot_buffer_hflag_enable(em->bm, bmop.slots_out, "faces.out", BM_FACE, BM_ELEM_SELECT, true);
	}

	/* no need to de-select existing geometry */
	if (!EDBM_op_finish(em, &bmop, op, true))
		return false;

	EDBM_mesh_normals_update(opdata->em);

	EDBM_update_generic(opdata->em, true, true);

	return true;
}

static void edbm_bevel_exit(bContext *C, wmOperator *op)
{
	BevelData *opdata = op->customdata;

	ScrArea *sa = CTX_wm_area(C);

	if (sa) {
		ED_area_headerprint(sa, NULL);
	}

	if (opdata->is_modal) {
		View3D *v3d = CTX_wm_view3d(C);
		ARegion *ar = CTX_wm_region(C);
		EDBM_redo_state_free(&opdata->mesh_backup, NULL, false);
		ED_region_draw_cb_exit(ar->type, opdata->draw_handle_pixel);
		v3d->twtype = opdata->twtype;
		G.moving = 0;
	}
	MEM_freeN(opdata);
	op->customdata = NULL;
}

static int edbm_bevel_cancel(bContext *C, wmOperator *op)
{
	BevelData *opdata = op->customdata;
	if (opdata->is_modal) {
		EDBM_redo_state_free(&opdata->mesh_backup, opdata->em, true);
		EDBM_update_generic(opdata->em, false, true);
	}

	edbm_bevel_exit(C, op);

	/* need to force redisplay or we may still view the modified result */
	ED_region_tag_redraw(CTX_wm_region(C));
	return OPERATOR_CANCELLED;
}

/* bevel! yay!!*/
static int edbm_bevel_exec(bContext *C, wmOperator *op)
{
	if (!edbm_bevel_init(C, op, false)) {
		return OPERATOR_CANCELLED;
	}

	if (!edbm_bevel_calc(op)) {
		edbm_bevel_cancel(C, op);
		return OPERATOR_CANCELLED;
	}

	edbm_bevel_exit(C, op);

	return OPERATOR_FINISHED;
}

static int edbm_bevel_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
	/* TODO make modal keymap (see fly mode) */
	RegionView3D *rv3d = CTX_wm_region_view3d(C);
	BevelData *opdata;
	float mlen[2];
	float center_3d[3];

	if (!edbm_bevel_init(C, op, true)) {
		return OPERATOR_CANCELLED;
	}

	opdata = op->customdata;

	/* initialize mouse values */
	if (!calculateTransformCenter(C, V3D_CENTROID, center_3d, opdata->mcenter)) {
		/* in this case the tool will likely do nothing,
		 * ideally this will never happen and should be checked for above */
		opdata->mcenter[0] = opdata->mcenter[1] = 0;
	}
	mlen[0] = opdata->mcenter[0] - event->mval[0];
	mlen[1] = opdata->mcenter[1] - event->mval[1];
	opdata->initial_length = len_v2(mlen);
	opdata->pixel_size = rv3d ? ED_view3d_pixel_size(rv3d, center_3d) : 1.0f;

	edbm_bevel_update_header(op, C);

	if (!edbm_bevel_calc(op)) {
		edbm_bevel_cancel(C, op);
		return OPERATOR_CANCELLED;
	}

	WM_event_add_modal_handler(C, op);

	return OPERATOR_RUNNING_MODAL;
}

static float edbm_bevel_mval_factor(wmOperator *op, const wmEvent *event)
{
	BevelData *opdata = op->customdata;
	int use_dist = true;
	float mdiff[2];
	float factor;

	mdiff[0] = opdata->mcenter[0] - event->mval[0];
	mdiff[1] = opdata->mcenter[1] - event->mval[1];

	if (use_dist) {
		factor = ((len_v2(mdiff) - MVAL_PIXEL_MARGIN) - opdata->initial_length) * opdata->pixel_size;
	}
	else {
		factor = (len_v2(mdiff) - MVAL_PIXEL_MARGIN) / opdata->initial_length;
		factor = factor - 1.0f;  /* a different kind of buffer where nothing happens */
	}

	/* Fake shift-transform... */
	if (event->shift) {
		if (opdata->shift_factor < 0.0f) {
			opdata->shift_factor = RNA_float_get(op->ptr, "offset");
		}
		factor = (factor - opdata->shift_factor) * 0.1f + opdata->shift_factor;
	}
	else if (opdata->shift_factor >= 0.0f)
		opdata->shift_factor = -1.0f;

	/* clamp differently based on distance/factor */
	if (use_dist) {
		if (factor < 0.0f) factor = 0.0f;
	}
	else {
		CLAMP(factor, 0.0f, 1.0f);
	}

	return factor;
}

static int edbm_bevel_modal(bContext *C, wmOperator *op, const wmEvent *event)
{
	BevelData *opdata = op->customdata;
	int segments = RNA_int_get(op->ptr, "segments");

	if (event->val == KM_PRESS) {
		/* Try to handle numeric inputs... */

		if (handleNumInput(&opdata->num_input, event)) {
			float value = RNA_float_get(op->ptr, "offset");
			applyNumInput(&opdata->num_input, &value);
			RNA_float_set(op->ptr, "offset", value);
			edbm_bevel_calc(op);
			edbm_bevel_update_header(op, C);
			return OPERATOR_RUNNING_MODAL;
		}
	}

	switch (event->type) {
		case ESCKEY:
		case RIGHTMOUSE:
			edbm_bevel_cancel(C, op);
			return OPERATOR_CANCELLED;

		case MOUSEMOVE:
			if (!hasNumInput(&opdata->num_input)) {
				const float factor = edbm_bevel_mval_factor(op, event);
				RNA_float_set(op->ptr, "offset", factor);

				edbm_bevel_calc(op);
				edbm_bevel_update_header(op, C);
			}
			break;

		case LEFTMOUSE:
		case PADENTER:
		case RETKEY:
			edbm_bevel_calc(op);
			edbm_bevel_exit(C, op);
			return OPERATOR_FINISHED;

		case WHEELUPMOUSE:  /* change number of segments */
		case PADPLUSKEY:
			if (event->val == KM_RELEASE)
				break;

			segments++;
			RNA_int_set(op->ptr, "segments", segments);
			edbm_bevel_calc(op);
			edbm_bevel_update_header(op, C);
			break;

		case WHEELDOWNMOUSE:  /* change number of segments */
		case PADMINUS:
			if (event->val == KM_RELEASE)
				break;

			segments = max_ii(segments - 1, 1);
			RNA_int_set(op->ptr, "segments", segments);
			edbm_bevel_calc(op);
			edbm_bevel_update_header(op, C);
			break;
	}

	return OPERATOR_RUNNING_MODAL;
}

void MESH_OT_bevel(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Bevel";
	ot->description = "Edge Bevel";
	ot->idname = "MESH_OT_bevel";

	/* api callbacks */
	ot->exec = edbm_bevel_exec;
	ot->invoke = edbm_bevel_invoke;
	ot->modal = edbm_bevel_modal;
	ot->cancel = edbm_bevel_cancel;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO | OPTYPE_GRAB_POINTER | OPTYPE_BLOCKING;

	RNA_def_float(ot->srna, "offset", 0.0f, -FLT_MAX, FLT_MAX, "Offset", "", 0.0f, 1.0f);
	RNA_def_int(ot->srna, "segments", 1, 1, 50, "Segments", "Segments for curved edge", 1, 8);
	RNA_def_boolean(ot->srna, "vertex_only", false, "Vertex only", "Bevel only vertices");
}
