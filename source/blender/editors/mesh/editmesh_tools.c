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

/** \file blender/editors/mesh/editmesh_tools.c
 *  \ingroup edmesh
 */

#include "MEM_guardedalloc.h"

#include "DNA_key_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "RNA_define.h"
#include "RNA_access.h"

#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_rand.h"

#include "BKE_material.h"
#include "BKE_context.h"
#include "BKE_cdderivedmesh.h"
#include "BKE_depsgraph.h"
#include "BKE_object.h"
#include "BKE_report.h"
#include "BKE_texture.h"
#include "BKE_main.h"
#include "BKE_tessmesh.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_mesh.h"
#include "ED_numinput.h"
#include "ED_object.h"
#include "ED_screen.h"
#include "ED_transform.h"
#include "ED_uvedit.h"
#include "ED_view3d.h"

#include "RE_render_ext.h"

#include "UI_interface.h"

#include "mesh_intern.h"

/* allow accumulated normals to form a new direction but don't
 * accept direct opposite directions else they will cancel each other out */
static void add_normal_aligned(float nor[3], const float add[3])
{
	if (dot_v3v3(nor, add) < -0.9999f) {
		sub_v3_v3(nor, add);
	}
	else {
		add_v3_v3(nor, add);
	}
}

static int edbm_subdivide_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	int cuts = RNA_int_get(op->ptr, "number_cuts");
	float smooth = 0.292f * RNA_float_get(op->ptr, "smoothness");
	float fractal = RNA_float_get(op->ptr, "fractal") / 2.5f;
	float along_normal = RNA_float_get(op->ptr, "fractal_along_normal");

	if (RNA_boolean_get(op->ptr, "quadtri") && 
	    RNA_enum_get(op->ptr, "quadcorner") == SUBD_STRAIGHT_CUT)
	{
		RNA_enum_set(op->ptr, "quadcorner", SUBD_INNERVERT);
	}
	
	BM_mesh_esubdivide(em->bm, BM_ELEM_SELECT,
	                   smooth, fractal, along_normal,
	                   cuts,
	                   SUBDIV_SELECT_ORIG, RNA_enum_get(op->ptr, "quadcorner"),
	                   RNA_boolean_get(op->ptr, "quadtri"), TRUE,
	                   RNA_int_get(op->ptr, "seed"));

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

/* Note, these values must match delete_mesh() event values */
static EnumPropertyItem prop_mesh_cornervert_types[] = {
	{SUBD_INNERVERT,     "INNERVERT", 0,      "Inner Vert", ""},
	{SUBD_PATH,          "PATH", 0,           "Path", ""},
	{SUBD_STRAIGHT_CUT,  "STRAIGHT_CUT", 0,   "Straight Cut", ""},
	{SUBD_FAN,           "FAN", 0,            "Fan", ""},
	{0, NULL, 0, NULL, NULL}
};

void MESH_OT_subdivide(wmOperatorType *ot)
{
	PropertyRNA *prop;

	/* identifiers */
	ot->name = "Subdivide";
	ot->description = "Subdivide selected edges";
	ot->idname = "MESH_OT_subdivide";

	/* api callbacks */
	ot->exec = edbm_subdivide_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	prop = RNA_def_int(ot->srna, "number_cuts", 1, 1, INT_MAX, "Number of Cuts", "", 1, 10);
	/* avoid re-using last var because it can cause _very_ high poly meshes and annoy users (or worse crash) */
	RNA_def_property_flag(prop, PROP_SKIP_SAVE);

	RNA_def_float(ot->srna, "smoothness", 0.0f, 0.0f, FLT_MAX, "Smoothness", "Smoothness factor", 0.0f, 1.0f);

	RNA_def_boolean(ot->srna, "quadtri", 0, "Quad/Tri Mode", "Tries to prevent ngons");
	RNA_def_enum(ot->srna, "quadcorner", prop_mesh_cornervert_types, SUBD_STRAIGHT_CUT,
	             "Quad Corner Type", "How to subdivide quad corners (anything other than Straight Cut will prevent ngons)");

	RNA_def_float(ot->srna, "fractal", 0.0f, 0.0f, FLT_MAX, "Fractal", "Fractal randomness factor", 0.0f, 1000.0f);
	RNA_def_float(ot->srna, "fractal_along_normal", 0.0f, 0.0f, 1.0f, "Along Normal", "Apply fractal displacement along normal only", 0.0f, 1.0f);
	RNA_def_int(ot->srna, "seed", 0, 0, 10000, "Random Seed", "Seed for the random number generator", 0, 50);
}


void EMBM_project_snap_verts(bContext *C, ARegion *ar, Object *obedit, BMEditMesh *em)
{
	BMIter iter;
	BMVert *eve;

	BM_ITER_MESH (eve, &iter, em->bm, BM_VERTS_OF_MESH) {
		if (BM_elem_flag_test(eve, BM_ELEM_SELECT)) {
			float mval[2], vec[3], no_dummy[3];
			int dist_dummy;
			mul_v3_m4v3(vec, obedit->obmat, eve->co);
			project_float_noclip(ar, vec, mval);
			if (snapObjectsContext(C, mval, &dist_dummy, vec, no_dummy, SNAP_NOT_OBEDIT)) {
				mul_v3_m4v3(eve->co, obedit->imat, vec);
			}
		}
	}
}


/* individual face extrude */
/* will use vertex normals for extrusion directions, so *nor is unaffected */
static short edbm_extrude_discrete_faces(BMEditMesh *em, wmOperator *op, const char hflag, float *UNUSED(nor))
{
	BMOIter siter;
	BMIter liter;
	BMFace *f;
	BMLoop *l;
	BMOperator bmop;

	EDBM_op_init(em, &bmop, op, "extrude_discrete_faces faces=%hf", hflag);

	/* deselect original verts */
	EDBM_flag_disable_all(em, BM_ELEM_SELECT);

	BMO_op_exec(em->bm, &bmop);
	
	BMO_ITER (f, &siter, em->bm, &bmop, "faceout", BM_FACE) {
		BM_face_select_set(em->bm, f, TRUE);

		/* set face vertex normals to face normal */
		BM_ITER_ELEM (l, &liter, f, BM_LOOPS_OF_FACE) {
			copy_v3_v3(l->v->no, f->no);
		}
	}

	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return 0;
	}

	return 's'; // s is shrink/fatten
}

/* extrudes individual edges */
static short edbm_extrude_edges_indiv(BMEditMesh *em, wmOperator *op, const char hflag, float *UNUSED(nor))
{
	BMOperator bmop;

	EDBM_op_init(em, &bmop, op, "extrude_edge_only edges=%he", hflag);

	/* deselect original verts */
	EDBM_flag_disable_all(em, BM_ELEM_SELECT);

	BMO_op_exec(em->bm, &bmop);
	BMO_slot_buffer_hflag_enable(em->bm, &bmop, "geomout", BM_VERT | BM_EDGE, BM_ELEM_SELECT, TRUE);

	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return 0;
	}

	return 'n'; // n is normal grab
}

/* extrudes individual vertices */
static short edbm_extrude_verts_indiv(BMEditMesh *em, wmOperator *op, const char hflag, float *UNUSED(nor))
{
	BMOperator bmop;

	EDBM_op_init(em, &bmop, op, "extrude_vert_indiv verts=%hv", hflag);

	/* deselect original verts */
	BMO_slot_buffer_hflag_disable(em->bm, &bmop, "verts", BM_VERT, BM_ELEM_SELECT, TRUE);

	BMO_op_exec(em->bm, &bmop);
	BMO_slot_buffer_hflag_enable(em->bm, &bmop, "vertout", BM_VERT, BM_ELEM_SELECT, TRUE);

	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return 0;
	}

	return 'g'; // g is grab
}

static short edbm_extrude_edge(Object *obedit, BMEditMesh *em, const char hflag, float nor[3])
{
	BMesh *bm = em->bm;
	BMIter iter;
	BMOIter siter;
	BMOperator extop;
	BMEdge *edge;
	BMFace *f;
	ModifierData *md;
	BMElem *ele;
	
	BMO_op_init(bm, &extop, BMO_FLAG_DEFAULTS, "extrude_face_region");
	BMO_slot_buffer_from_enabled_hflag(bm, &extop, "edgefacein", BM_VERT | BM_EDGE | BM_FACE, hflag);

	/* If a mirror modifier with clipping is on, we need to adjust some 
	 * of the cases above to handle edges on the line of symmetry.
	 */
	md = obedit->modifiers.first;
	for (; md; md = md->next) {
		if ((md->type == eModifierType_Mirror) && (md->mode & eModifierMode_Realtime)) {
			MirrorModifierData *mmd = (MirrorModifierData *) md;
		
			if (mmd->flag & MOD_MIR_CLIPPING) {
				float mtx[4][4];
				if (mmd->mirror_ob) {
					float imtx[4][4];
					invert_m4_m4(imtx, mmd->mirror_ob->obmat);
					mult_m4_m4m4(mtx, imtx, obedit->obmat);
				}

				for (edge = BM_iter_new(&iter, bm, BM_EDGES_OF_MESH, NULL);
				     edge;
				     edge = BM_iter_step(&iter))
				{
					if (BM_elem_flag_test(edge, hflag) &&
					    BM_edge_is_boundary(edge) &&
					    BM_elem_flag_test(edge->l->f, hflag))
					{
						float co1[3], co2[3];

						copy_v3_v3(co1, edge->v1->co);
						copy_v3_v3(co2, edge->v2->co);

						if (mmd->mirror_ob) {
							mul_v3_m4v3(co1, mtx, co1);
							mul_v3_m4v3(co2, mtx, co2);
						}

						if (mmd->flag & MOD_MIR_AXIS_X) {
							if ((fabsf(co1[0]) < mmd->tolerance) &&
							    (fabsf(co2[0]) < mmd->tolerance))
							{
								BMO_slot_map_ptr_insert(bm, &extop, "exclude", edge, NULL);
							}
						}
						if (mmd->flag & MOD_MIR_AXIS_Y) {
							if ((fabsf(co1[1]) < mmd->tolerance) &&
							    (fabsf(co2[1]) < mmd->tolerance))
							{
								BMO_slot_map_ptr_insert(bm, &extop, "exclude", edge, NULL);
							}
						}
						if (mmd->flag & MOD_MIR_AXIS_Z) {
							if ((fabsf(co1[2]) < mmd->tolerance) &&
							    (fabsf(co2[2]) < mmd->tolerance))
							{
								BMO_slot_map_ptr_insert(bm, &extop, "exclude", edge, NULL);
							}
						}
					}
				}
			}
		}
	}

	EDBM_flag_disable_all(em, BM_ELEM_SELECT);

	BMO_op_exec(bm, &extop);

	zero_v3(nor);
	
	BMO_ITER (ele, &siter, bm, &extop, "geomout", BM_ALL) {
		BM_elem_select_set(bm, ele, TRUE);

		if (ele->head.htype == BM_FACE) {
			f = (BMFace *)ele;
			add_normal_aligned(nor, f->no);
		};
	}

	normalize_v3(nor);

	BMO_op_finish(bm, &extop);

	/* grab / normal constraint */
	return is_zero_v3(nor) ? 'g' : 'n';
}

static short edbm_extrude_vert(Object *obedit, BMEditMesh *em, const char hflag, float nor[3])
{
	BMIter iter;
	BMEdge *eed;
		
	/* ensure vert flags are consistent for edge selections */
	BM_ITER_MESH (eed, &iter, em->bm, BM_EDGES_OF_MESH) {
		if (BM_elem_flag_test(eed, hflag)) {
			if (hflag & BM_ELEM_SELECT) {
				BM_vert_select_set(em->bm, eed->v1, TRUE);
				BM_vert_select_set(em->bm, eed->v2, TRUE);
			}

			BM_elem_flag_enable(eed->v1, hflag & ~BM_ELEM_SELECT);
			BM_elem_flag_enable(eed->v2, hflag & ~BM_ELEM_SELECT);
		}
		else {
			if (BM_elem_flag_test(eed->v1, hflag) && BM_elem_flag_test(eed->v2, hflag)) {
				if (hflag & BM_ELEM_SELECT) {
					BM_edge_select_set(em->bm, eed, TRUE);
				}

				BM_elem_flag_enable(eed, hflag & ~BM_ELEM_SELECT);
			}
		}
	}

	return edbm_extrude_edge(obedit, em, hflag, nor);
}

static int edbm_extrude_repeat_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	RegionView3D *rv3d = CTX_wm_region_view3d(C);
		
	int steps = RNA_int_get(op->ptr, "steps");
	
	float offs = RNA_float_get(op->ptr, "offset");
	float dvec[3], tmat[3][3], bmat[3][3], nor[3] = {0.0, 0.0, 0.0};
	short a;

	/* dvec */
	normalize_v3_v3(dvec, rv3d->persinv[2]);
	mul_v3_fl(dvec, offs);

	/* base correction */
	copy_m3_m4(bmat, obedit->obmat);
	invert_m3_m3(tmat, bmat);
	mul_m3_v3(tmat, dvec);

	for (a = 0; a < steps; a++) {
		edbm_extrude_edge(obedit, em, BM_ELEM_SELECT, nor);
		//BMO_op_callf(em->bm, BMO_FLAG_DEFAULTS, "extrude_face_region edgefacein=%hef", BM_ELEM_SELECT);
		BMO_op_callf(em->bm, BMO_FLAG_DEFAULTS,
		             "translate vec=%v verts=%hv",
		             (float *)dvec, BM_ELEM_SELECT);
		//extrudeflag(obedit, em, SELECT, nor);
		//translateflag(em, SELECT, dvec);
	}
	
	EDBM_mesh_normals_update(em);

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_extrude_repeat(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Extrude Repeat Mesh";
	ot->description = "Extrude selected vertices, edges or faces repeatedly";
	ot->idname = "MESH_OT_extrude_repeat";
	
	/* api callbacks */
	ot->exec = edbm_extrude_repeat_exec;
	ot->poll = ED_operator_editmesh_view3d;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
	
	/* props */
	RNA_def_float(ot->srna, "offset", 2.0f, 0.0f, 100.0f, "Offset", "", 0.0f, FLT_MAX);
	RNA_def_int(ot->srna, "steps", 10, 0, 180, "Steps", "", 0, INT_MAX);
}

/* generic extern called extruder */
static int edbm_extrude_mesh(Scene *scene, Object *obedit, BMEditMesh *em, wmOperator *op, float *norin)
{
	short nr, transmode = 0;
	float stacknor[3] = {0.0f, 0.0f, 0.0f};
	float *nor = norin ? norin : stacknor;

	zero_v3(nor);

	if (em->selectmode & SCE_SELECT_VERTEX) {
		if (em->bm->totvertsel == 0) nr = 0;
		else if (em->bm->totvertsel == 1) nr = 4;
		else if (em->bm->totedgesel == 0) nr = 4;
		else if (em->bm->totfacesel == 0)
			nr = 3;  // pupmenu("Extrude %t|Only Edges%x3|Only Vertices%x4");
		else if (em->bm->totfacesel == 1)
			nr = 1;  // pupmenu("Extrude %t|Region %x1|Only Edges%x3|Only Vertices%x4");
		else
			nr = 1;  // pupmenu("Extrude %t|Region %x1||Individual Faces %x2|Only Edges%x3|Only Vertices%x4");
	}
	else if (em->selectmode & SCE_SELECT_EDGE) {
		if (em->bm->totedgesel == 0) nr = 0;
		
		nr = 1;
#if 0
		else if (em->totedgesel == 1) nr = 3;
		else if (em->totfacesel == 0) nr = 3;
		else if (em->totfacesel == 1)
			nr = 1;  // pupmenu("Extrude %t|Region %x1|Only Edges%x3");
		else
			nr = 1;  // pupmenu("Extrude %t|Region %x1||Individual Faces %x2|Only Edges%x3");
#endif
	}
	else {
		if (em->bm->totfacesel == 0) nr = 0;
		else if (em->bm->totfacesel == 1) nr = 1;
		else
			nr = 1;  // pupmenu("Extrude %t|Region %x1||Individual Faces %x2");
	}

	if (nr < 1) return 'g';

	if (nr == 1 && (em->selectmode & SCE_SELECT_VERTEX))
		transmode = edbm_extrude_vert(obedit, em, BM_ELEM_SELECT, nor);
	else if (nr == 1) transmode = edbm_extrude_edge(obedit, em, BM_ELEM_SELECT, nor);
	else if (nr == 4) transmode = edbm_extrude_verts_indiv(em, op, BM_ELEM_SELECT, nor);
	else if (nr == 3) transmode = edbm_extrude_edges_indiv(em, op, BM_ELEM_SELECT, nor);
	else transmode = edbm_extrude_discrete_faces(em, op, BM_ELEM_SELECT, nor);
	
	if (transmode == 0) {
		BKE_report(op->reports, RPT_ERROR, "Not a valid selection for extrude");
	}
	else {
		
		/* We need to force immediate calculation here because
		 * transform may use derived objects (which are now stale).
		 *
		 * This shouldn't be necessary, derived queries should be
		 * automatically building this data if invalid. Or something.
		 */
//		DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
		BKE_object_handle_update(scene, obedit);

		/* individual faces? */
//		BIF_TransformSetUndo("Extrude");
		if (nr == 2) {
//			initTransform(TFM_SHRINKFATTEN, CTX_NO_PET|CTX_NO_MIRROR);
//			Transform();
		}
		else {
//			initTransform(TFM_TRANSLATION, CTX_NO_PET|CTX_NO_MIRROR);
			if (transmode == 'n') {
				mul_m4_v3(obedit->obmat, nor);
				sub_v3_v3v3(nor, nor, obedit->obmat[3]);
//				BIF_setSingleAxisConstraint(nor, "along normal");
			}
//			Transform();
		}
	}
	
	return transmode;
}

/* extrude without transform */
static int edbm_extrude_region_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	
	edbm_extrude_mesh(scene, obedit, em, op, NULL);

	/* This normally happens when pushing undo but modal operators
	 * like this one don't push undo data until after modal mode is
	 * done.*/
	EDBM_mesh_normals_update(em);

	EDBM_update_generic(C, em, TRUE);
	
	return OPERATOR_FINISHED;
}

void MESH_OT_extrude_region(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Extrude Region";
	ot->idname = "MESH_OT_extrude_region";
	ot->description = "Extrude region of faces";
	
	/* api callbacks */
	//ot->invoke = mesh_extrude_region_invoke;
	ot->exec = edbm_extrude_region_exec;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Editing", "");
}

static int edbm_extrude_verts_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	float nor[3];

	edbm_extrude_verts_indiv(em, op, BM_ELEM_SELECT, nor);
	
	WM_event_add_notifier(C, NC_GEOM | ND_SELECT, obedit);
	
	return OPERATOR_FINISHED;
}

void MESH_OT_extrude_verts_indiv(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Extrude Only Vertices";
	ot->idname = "MESH_OT_extrude_verts_indiv";
	ot->description = "Extrude individual vertices only";
	
	/* api callbacks */
	ot->exec = edbm_extrude_verts_exec;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* to give to transform */
	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Editing", "");
}

static int edbm_extrude_edges_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	float nor[3];

	edbm_extrude_edges_indiv(em, op, BM_ELEM_SELECT, nor);
	
	WM_event_add_notifier(C, NC_GEOM | ND_SELECT, obedit);
	
	return OPERATOR_FINISHED;
}

void MESH_OT_extrude_edges_indiv(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Extrude Only Edges";
	ot->idname = "MESH_OT_extrude_edges_indiv";
	ot->description = "Extrude individual edges only";
	
	/* api callbacks */
	ot->exec = edbm_extrude_edges_exec;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* to give to transform */
	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Editing", "");
}

static int edbm_extrude_faces_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	float nor[3];

	edbm_extrude_discrete_faces(em, op, BM_ELEM_SELECT, nor);
	
	EDBM_update_generic(C, em, TRUE);
	
	return OPERATOR_FINISHED;
}

void MESH_OT_extrude_faces_indiv(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Extrude Individual Faces";
	ot->idname = "MESH_OT_extrude_faces_indiv";
	ot->description = "Extrude individual faces only";
	
	/* api callbacks */
	ot->exec = edbm_extrude_faces_exec;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Editing", "");
}

/* ******************** (de)select all operator **************** */

static int edbm_select_all_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	int action = RNA_enum_get(op->ptr, "action");
	
	switch (action) {
		case SEL_TOGGLE:
			EDBM_select_toggle_all(em);
			break;
		case SEL_SELECT:
			EDBM_flag_enable_all(em, BM_ELEM_SELECT);
			break;
		case SEL_DESELECT:
			EDBM_flag_disable_all(em, BM_ELEM_SELECT);
			break;
		case SEL_INVERT:
			EDBM_select_swap(em);
			EDBM_selectmode_flush(em);
			break;
	}

	WM_event_add_notifier(C, NC_GEOM | ND_SELECT, obedit);

	return OPERATOR_FINISHED;
}

void MESH_OT_select_all(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "(De)select All";
	ot->idname = "MESH_OT_select_all";
	ot->description = "(De)select all vertices, edges or faces";
	
	/* api callbacks */
	ot->exec = edbm_select_all_exec;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	WM_operator_properties_select_all(ot);
}

static int edbm_faces_select_interior_exec(bContext *C, wmOperator *UNUSED(op))
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);

	if (EDBM_select_interior_faces(em)) {
		WM_event_add_notifier(C, NC_GEOM | ND_SELECT, obedit);

		return OPERATOR_FINISHED;
	}
	else {
		return OPERATOR_CANCELLED;
	}

}

void MESH_OT_select_interior_faces(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Select Interior Faces";
	ot->idname = "MESH_OT_select_interior_faces";
	ot->description = "Select faces where all edges have more than 2 face users";

	/* api callbacks */
	ot->exec = edbm_faces_select_interior_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* *************** add-click-mesh (extrude) operator ************** */
static int edbm_dupli_extrude_cursor_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	ViewContext vc;
	BMVert *v1;
	BMIter iter;
	float min[3], max[3];
	int done = FALSE;
	short use_proj;
	
	em_setup_viewcontext(C, &vc);
	
	use_proj = ((vc.scene->toolsettings->snap_flag & SCE_SNAP) &&
	            (vc.scene->toolsettings->snap_mode == SCE_SNAP_MODE_FACE));

	INIT_MINMAX(min, max);
	
	BM_ITER_MESH (v1, &iter, vc.em->bm, BM_VERTS_OF_MESH) {
		if (BM_elem_flag_test(v1, BM_ELEM_SELECT)) {
			minmax_v3v3_v3(min, max, v1->co);
			done = TRUE;
		}
	}

	/* call extrude? */
	if (done) {
		const short rot_src = RNA_boolean_get(op->ptr, "rotate_source");
		BMEdge *eed;
		float vec[3], cent[3], mat[3][3];
		float nor[3] = {0.0, 0.0, 0.0};

		/* 2D normal calc */
		const float mval_f[2] = {(float)event->mval[0],
		                         (float)event->mval[1]};

		/* check for edges that are half selected, use for rotation */
		done = FALSE;
		BM_ITER_MESH (eed, &iter, vc.em->bm, BM_EDGES_OF_MESH) {
			if (BM_elem_flag_test(eed, BM_ELEM_SELECT)) {
				float co1[3], co2[3];
				mul_v3_m4v3(co1, vc.obedit->obmat, eed->v1->co);
				mul_v3_m4v3(co2, vc.obedit->obmat, eed->v2->co);
				project_float_noclip(vc.ar, co1, co1);
				project_float_noclip(vc.ar, co2, co2);

				/* 2D rotate by 90d while adding.
				 *  (x, y) = (y, -x)
				 *
				 * accumulate the screenspace normal in 2D,
				 * with screenspace edge length weighting the result. */
				if (line_point_side_v2(co1, co2, mval_f) >= 0.0f) {
					nor[0] +=  (co1[1] - co2[1]);
					nor[1] += -(co1[0] - co2[0]);
				}
				else {
					nor[0] +=  (co2[1] - co1[1]);
					nor[1] += -(co2[0] - co1[0]);
				}
			}
			done = TRUE;
		}

		if (done) {
			float view_vec[3], cross[3];

			/* convert the 2D nomal into 3D */
			mul_mat3_m4_v3(vc.rv3d->viewinv, nor); /* worldspace */
			mul_mat3_m4_v3(vc.obedit->imat, nor); /* local space */

			/* correct the normal to be aligned on the view plane */
			copy_v3_v3(view_vec, vc.rv3d->viewinv[2]);
			mul_mat3_m4_v3(vc.obedit->imat, view_vec);
			cross_v3_v3v3(cross, nor, view_vec);
			cross_v3_v3v3(nor, view_vec, cross);
			normalize_v3(nor);
		}
		
		/* center */
		mid_v3_v3v3(cent, min, max);
		copy_v3_v3(min, cent);

		mul_m4_v3(vc.obedit->obmat, min);  /* view space */
		view3d_get_view_aligned_coordinate(&vc, min, event->mval, TRUE);
		mul_m4_v3(vc.obedit->imat, min); // back in object space

		sub_v3_v3(min, cent);
		
		/* calculate rotation */
		unit_m3(mat);
		if (done) {
			float angle;

			normalize_v3_v3(vec, min);

			angle = angle_normalized_v3v3(vec, nor);

			if (angle != 0.0f) {
				float axis[3];

				cross_v3_v3v3(axis, nor, vec);

				/* halve the rotation if its applied twice */
				if (rot_src) {
					angle *= 0.5f;
				}

				axis_angle_to_mat3(mat, axis, angle);
			}
		}
		
		if (rot_src) {
			EDBM_op_callf(vc.em, op, "rotate verts=%hv cent=%v mat=%m3",
			              BM_ELEM_SELECT, cent, mat);

			/* also project the source, for retopo workflow */
			if (use_proj)
				EMBM_project_snap_verts(C, vc.ar, vc.obedit, vc.em);
		}

		edbm_extrude_edge(vc.obedit, vc.em, BM_ELEM_SELECT, nor);
		EDBM_op_callf(vc.em, op, "rotate verts=%hv cent=%v mat=%m3",
		              BM_ELEM_SELECT, cent, mat);
		EDBM_op_callf(vc.em, op, "translate verts=%hv vec=%v",
		              BM_ELEM_SELECT, min);
	}
	else {
		float *curs = give_cursor(vc.scene, vc.v3d);
		BMOperator bmop;
		BMOIter oiter;
		
		copy_v3_v3(min, curs);
		view3d_get_view_aligned_coordinate(&vc, min, event->mval, 0);

		invert_m4_m4(vc.obedit->imat, vc.obedit->obmat);
		mul_m4_v3(vc.obedit->imat, min); // back in object space
		
		EDBM_op_init(vc.em, &bmop, op, "create_vert co=%v", min);
		BMO_op_exec(vc.em->bm, &bmop);

		BMO_ITER (v1, &oiter, vc.em->bm, &bmop, "newvertout", BM_VERT) {
			BM_vert_select_set(vc.em->bm, v1, TRUE);
		}

		if (!EDBM_op_finish(vc.em, &bmop, op, TRUE)) {
			return OPERATOR_CANCELLED;
		}
	}

	if (use_proj)
		EMBM_project_snap_verts(C, vc.ar, vc.obedit, vc.em);

	/* This normally happens when pushing undo but modal operators
	 * like this one don't push undo data until after modal mode is
	 * done. */
	EDBM_mesh_normals_update(vc.em);

	EDBM_update_generic(C, vc.em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_dupli_extrude_cursor(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Duplicate or Extrude at 3D Cursor";
	ot->idname = "MESH_OT_dupli_extrude_cursor";
	ot->description = "Duplicate and extrude selected vertices, edges or faces towards the mouse cursor";
	
	/* api callbacks */
	ot->invoke = edbm_dupli_extrude_cursor_invoke;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	RNA_def_boolean(ot->srna, "rotate_source", 1, "Rotate Source", "Rotate initial selection giving better shape");
}

/* Note, these values must match delete_mesh() event values */
static EnumPropertyItem prop_mesh_delete_types[] = {
	{0, "VERT",      0, "Vertices", ""},
	{1,  "EDGE",      0, "Edges", ""},
	{2,  "FACE",      0, "Faces", ""},
	{3,  "EDGE_FACE", 0, "Only Edges & Faces", ""},
	{4,  "ONLY_FACE", 0, "Only Faces", ""},
	{0, NULL, 0, NULL, NULL}
};

static int edbm_delete_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	int type = RNA_enum_get(op->ptr, "type");

	if (type == 0) {
		if (!EDBM_op_callf(em, op, "delete geom=%hv context=%i", BM_ELEM_SELECT, DEL_VERTS)) /* Erase Vertices */
			return OPERATOR_CANCELLED;
	}
	else if (type == 1) {
		if (!EDBM_op_callf(em, op, "delete geom=%he context=%i", BM_ELEM_SELECT, DEL_EDGES)) /* Erase Edges */
			return OPERATOR_CANCELLED;
	}
	else if (type == 2) {
		if (!EDBM_op_callf(em, op, "delete geom=%hf context=%i", BM_ELEM_SELECT, DEL_FACES)) /* Erase Faces */
			return OPERATOR_CANCELLED;
	}
	else if (type == 3) {
		if (!EDBM_op_callf(em, op, "delete geom=%hef context=%i", BM_ELEM_SELECT, DEL_EDGESFACES)) /* Edges and Faces */
			return OPERATOR_CANCELLED;
	}
	else if (type == 4) {
		//"Erase Only Faces";
		if (!EDBM_op_callf(em, op, "delete geom=%hf context=%i",
		                   BM_ELEM_SELECT, DEL_ONLYFACES))
		{
			return OPERATOR_CANCELLED;
		}
	}

	EDBM_flag_disable_all(em, BM_ELEM_SELECT);

	EDBM_update_generic(C, em, TRUE);
	
	return OPERATOR_FINISHED;
}

void MESH_OT_delete(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Delete";
	ot->description = "Delete selected vertices, edges or faces";
	ot->idname = "MESH_OT_delete";
	
	/* api callbacks */
	ot->invoke = WM_menu_invoke;
	ot->exec = edbm_delete_exec;
	
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* props */
	ot->prop = RNA_def_enum(ot->srna, "type", prop_mesh_delete_types, 0, "Type", "Method used for deleting mesh data");
}

static int edbm_collapse_edge_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);

	if (!EDBM_op_callf(em, op, "collapse edges=%he", BM_ELEM_SELECT))
		return OPERATOR_CANCELLED;

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_edge_collapse(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Edge Collapse";
	ot->description = "Collapse selected edges";
	ot->idname = "MESH_OT_edge_collapse";

	/* api callbacks */
	ot->exec = edbm_collapse_edge_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static int edbm_collapse_edge_loop_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);

	if (!EDBM_op_callf(em, op, "dissolve_edge_loop edges=%he", BM_ELEM_SELECT))
		return OPERATOR_CANCELLED;

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_edge_collapse_loop(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Edge Collapse Loop";
	ot->description = "Collapse selected edge loops";
	ot->idname = "MESH_OT_edge_collapse_loop";

	/* api callbacks */
	ot->exec = edbm_collapse_edge_loop_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static int edbm_add_edge_face__smooth_get(BMesh *bm)
{
	BMEdge *e;
	BMIter iter;

	unsigned int vote_on_smooth[2] = {0, 0};

	BM_ITER_MESH (e, &iter, bm, BM_EDGES_OF_MESH) {
		if (BM_elem_flag_test(e, BM_ELEM_SELECT) && e->l) {
			vote_on_smooth[BM_elem_flag_test_bool(e->l->f, BM_ELEM_SMOOTH)]++;
		}
	}

	return (vote_on_smooth[0] < vote_on_smooth[1]);
}

static int edbm_add_edge_face_exec(bContext *C, wmOperator *op)
{
	BMOperator bmop;
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	const short use_smooth = edbm_add_edge_face__smooth_get(em->bm);
	/* when this is used to dissolve we could avoid this, but checking isnt too slow */

	if (!EDBM_op_init(em, &bmop, op,
	                  "contextual_create geom=%hfev mat_nr=%i use_smooth=%b",
	                  BM_ELEM_SELECT, em->mat_nr, use_smooth))
	{
		return OPERATOR_CANCELLED;
	}
	
	BMO_op_exec(em->bm, &bmop);
	BMO_slot_buffer_hflag_enable(em->bm, &bmop, "faceout", BM_FACE, BM_ELEM_SELECT, TRUE);
	BMO_slot_buffer_hflag_enable(em->bm, &bmop, "edgeout", BM_EDGE, BM_ELEM_SELECT, TRUE);

	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}

	EDBM_update_generic(C, em, TRUE);
	
	return OPERATOR_FINISHED;
}

void MESH_OT_edge_face_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Make Edge/Face";
	ot->description = "Add an edge or face to selected";
	ot->idname = "MESH_OT_edge_face_add";
	
	/* api callbacks */
	ot->exec = edbm_add_edge_face_exec;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* ************************* SEAMS AND EDGES **************** */

static int edbm_mark_seam(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *obedit = CTX_data_edit_object(C);
	Mesh *me = ((Mesh *)obedit->data);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMesh *bm = em->bm;
	BMEdge *eed;
	BMIter iter;
	int clear = RNA_boolean_get(op->ptr, "clear");
	
	/* auto-enable seams drawing */
	if (clear == 0) {
		me->drawflag |= ME_DRAWSEAMS;
	}

	if (clear) {
		BM_ITER_MESH (eed, &iter, bm, BM_EDGES_OF_MESH) {
			if (!BM_elem_flag_test(eed, BM_ELEM_SELECT) || BM_elem_flag_test(eed, BM_ELEM_HIDDEN))
				continue;
			
			BM_elem_flag_disable(eed, BM_ELEM_SEAM);
		}
	}
	else {
		BM_ITER_MESH (eed, &iter, bm, BM_EDGES_OF_MESH) {
			if (!BM_elem_flag_test(eed, BM_ELEM_SELECT) || BM_elem_flag_test(eed, BM_ELEM_HIDDEN))
				continue;
			BM_elem_flag_enable(eed, BM_ELEM_SEAM);
		}
	}

	ED_uvedit_live_unwrap(scene, obedit);
	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_mark_seam(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Mark Seam";
	ot->idname = "MESH_OT_mark_seam";
	ot->description = "(Un)mark selected edges as a seam";
	
	/* api callbacks */
	ot->exec = edbm_mark_seam;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
	
	RNA_def_boolean(ot->srna, "clear", 0, "Clear", "");
}

static int edbm_mark_sharp(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	Mesh *me = ((Mesh *)obedit->data);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMesh *bm = em->bm;
	BMEdge *eed;
	BMIter iter;
	int clear = RNA_boolean_get(op->ptr, "clear");

	/* auto-enable sharp edge drawing */
	if (clear == 0) {
		me->drawflag |= ME_DRAWSHARP;
	}

	if (!clear) {
		BM_ITER_MESH (eed, &iter, bm, BM_EDGES_OF_MESH) {
			if (!BM_elem_flag_test(eed, BM_ELEM_SELECT) || BM_elem_flag_test(eed, BM_ELEM_HIDDEN))
				continue;
			
			BM_elem_flag_disable(eed, BM_ELEM_SMOOTH);
		}
	}
	else {
		BM_ITER_MESH (eed, &iter, bm, BM_EDGES_OF_MESH) {
			if (!BM_elem_flag_test(eed, BM_ELEM_SELECT) || BM_elem_flag_test(eed, BM_ELEM_HIDDEN))
				continue;
			
			BM_elem_flag_enable(eed, BM_ELEM_SMOOTH);
		}
	}

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_mark_sharp(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Mark Sharp";
	ot->idname = "MESH_OT_mark_sharp";
	ot->description = "(Un)mark selected edges as sharp";
	
	/* api callbacks */
	ot->exec = edbm_mark_sharp;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
	
	RNA_def_boolean(ot->srna, "clear", 0, "Clear", "");
}


static int edbm_vert_connect(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMesh *bm = em->bm;
	BMOperator bmop;
	int len = 0;
	
	if (!EDBM_op_init(em, &bmop, op, "connect_verts verts=%hv", BM_ELEM_SELECT)) {
		return OPERATOR_CANCELLED;
	}
	BMO_op_exec(bm, &bmop);
	len = BMO_slot_get(&bmop, "edgeout")->len;
	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}
	
	EDBM_update_generic(C, em, TRUE);

	return len ? OPERATOR_FINISHED : OPERATOR_CANCELLED;
}

void MESH_OT_vert_connect(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Vertex Connect";
	ot->idname = "MESH_OT_vert_connect";
	ot->description = "Connect 2 vertices of a face by an edge, splitting the face in two";
	
	/* api callbacks */
	ot->exec = edbm_vert_connect;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static int edbm_edge_split_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMesh *bm = em->bm;
	BMOperator bmop;
	int len = 0;
	
	if (!EDBM_op_init(em, &bmop, op, "split_edges edges=%he", BM_ELEM_SELECT)) {
		return OPERATOR_CANCELLED;
	}
	BMO_op_exec(bm, &bmop);
	len = BMO_slot_get(&bmop, "edgeout")->len;
	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}
	
	EDBM_update_generic(C, em, TRUE);

	return len ? OPERATOR_FINISHED : OPERATOR_CANCELLED;
}

void MESH_OT_edge_split(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Edge Split";
	ot->idname = "MESH_OT_edge_split";
	ot->description = "Split selected edges so that each neighbor face gets its own copy";
	
	/* api callbacks */
	ot->exec = edbm_edge_split_exec;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/****************** add duplicate operator ***************/

static int edbm_duplicate_exec(bContext *C, wmOperator *op)
{
	Object *ob = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(ob);
	BMOperator bmop;

	EDBM_op_init(em, &bmop, op, "duplicate geom=%hvef", BM_ELEM_SELECT);
	
	BMO_op_exec(em->bm, &bmop);
	EDBM_flag_disable_all(em, BM_ELEM_SELECT);

	BMO_slot_buffer_hflag_enable(em->bm, &bmop, "newout", BM_ALL, BM_ELEM_SELECT, TRUE);

	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}

	EDBM_update_generic(C, em, TRUE);
	
	return OPERATOR_FINISHED;
}

static int edbm_duplicate_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	WM_cursor_wait(1);
	edbm_duplicate_exec(C, op);
	WM_cursor_wait(0);
	
	return OPERATOR_FINISHED;
}

void MESH_OT_duplicate(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Duplicate";
	ot->description = "Duplicate selected vertices, edges or faces";
	ot->idname = "MESH_OT_duplicate";
	
	/* api callbacks */
	ot->invoke = edbm_duplicate_invoke;
	ot->exec = edbm_duplicate_exec;
	
	ot->poll = ED_operator_editmesh;
	
	/* to give to transform */
	RNA_def_int(ot->srna, "mode", TFM_TRANSLATION, 0, INT_MAX, "Mode", "", 0, INT_MAX);
}

static int edbm_flip_normals_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	
	if (!EDBM_op_callf(em, op, "reverse_faces faces=%hf", BM_ELEM_SELECT))
		return OPERATOR_CANCELLED;
	
	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_flip_normals(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Flip Normals";
	ot->description = "Flip the direction of selected faces' normals (and of their vertices)";
	ot->idname = "MESH_OT_flip_normals";
	
	/* api callbacks */
	ot->exec = edbm_flip_normals_exec;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static const EnumPropertyItem direction_items[] = {
	{DIRECTION_CW, "CW", 0, "Clockwise", ""},
	{DIRECTION_CCW, "CCW", 0, "Counter Clockwise", ""},
	{0, NULL, 0, NULL, NULL}
};

/* only accepts 1 selected edge, or 2 selected faces */
static int edbm_edge_rotate_selected_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMOperator bmop;
	BMEdge *eed;
	BMIter iter;
	const int do_ccw = RNA_enum_get(op->ptr, "direction") == 1;
	int tot = 0;

	if (em->bm->totedgesel == 0) {
		BKE_report(op->reports, RPT_ERROR, "Select edges or face pairs for edge loops to rotate about");
		return OPERATOR_CANCELLED;
	}

	/* first see if we have two adjacent faces */
	BM_ITER_MESH (eed, &iter, em->bm, BM_EDGES_OF_MESH) {
		BM_elem_flag_disable(eed, BM_ELEM_TAG);
		if (BM_elem_flag_test(eed, BM_ELEM_SELECT)) {
			BMFace *fa, *fb;
			if (BM_edge_face_pair(eed, &fa, &fb)) {
				/* if both faces are selected we rotate between them,
				 * otherwise - rotate between 2 unselected - but not mixed */
				if (BM_elem_flag_test(fa, BM_ELEM_SELECT) == BM_elem_flag_test(fb, BM_ELEM_SELECT)) {
					BM_elem_flag_enable(eed, BM_ELEM_TAG);
					tot++;
				}
			}
		}
	}
	
	/* ok, we don't have two adjacent faces, but we do have two selected ones.
	 * that's an error condition.*/
	if (tot == 0) {
		BKE_report(op->reports, RPT_ERROR, "Could not find any selected edges that can be rotated");
		return OPERATOR_CANCELLED;
	}
	
	EDBM_op_init(em, &bmop, op, "rotate_edges edges=%he ccw=%b", BM_ELEM_TAG, do_ccw);

	/* avoids leaving old verts selected which can be a problem running multiple times,
	 * since this means the edges become selected around the face which then attempt to rotate */
	BMO_slot_buffer_hflag_disable(em->bm, &bmop, "edges", BM_EDGE, BM_ELEM_SELECT, TRUE);

	BMO_op_exec(em->bm, &bmop);
	/* edges may rotate into hidden vertices, if this does _not_ run we get an ilogical state */
	BMO_slot_buffer_hflag_disable(em->bm, &bmop, "edgeout", BM_EDGE, BM_ELEM_HIDDEN, TRUE);
	BMO_slot_buffer_hflag_enable(em->bm, &bmop, "edgeout", BM_EDGE, BM_ELEM_SELECT, TRUE);
	EDBM_selectmode_flush(em);

	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_edge_rotate(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Rotate Selected Edge";
	ot->description = "Rotate selected edge or adjoining faces";
	ot->idname = "MESH_OT_edge_rotate";

	/* api callbacks */
	ot->exec = edbm_edge_rotate_selected_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* props */
	RNA_def_enum(ot->srna, "direction", direction_items, DIRECTION_CW, "Direction", "Direction to rotate edge around");
}


static int edbm_hide_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	
	EDBM_mesh_hide(em, RNA_boolean_get(op->ptr, "unselected"));

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_hide(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Hide Selection";
	ot->idname = "MESH_OT_hide";
	ot->description = "Hide (un)selected vertices, edges or faces";
	
	/* api callbacks */
	ot->exec = edbm_hide_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
	
	/* props */
	RNA_def_boolean(ot->srna, "unselected", 0, "Unselected", "Hide unselected rather than selected");
}

static int edbm_reveal_exec(bContext *C, wmOperator *UNUSED(op))
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	
	EDBM_mesh_reveal(em);

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_reveal(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Reveal Hidden";
	ot->idname = "MESH_OT_reveal";
	ot->description = "Reveal all hidden vertices, edges and faces";
	
	/* api callbacks */
	ot->exec = edbm_reveal_exec;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static int edbm_normals_make_consistent_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	
	/* doflip has to do with bmesh_rationalize_normals, it's an internal
	 * thing */
	if (!EDBM_op_callf(em, op, "recalc_face_normals faces=%hf do_flip=%b", BM_ELEM_SELECT, TRUE))
		return OPERATOR_CANCELLED;

	if (RNA_boolean_get(op->ptr, "inside"))
		EDBM_op_callf(em, op, "reverse_faces faces=%hf", BM_ELEM_SELECT);

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_normals_make_consistent(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Make Normals Consistent";
	ot->description = "Make face and vertex normals point either outside or inside the mesh";
	ot->idname = "MESH_OT_normals_make_consistent";
	
	/* api callbacks */
	ot->exec = edbm_normals_make_consistent_exec;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
	
	RNA_def_boolean(ot->srna, "inside", 0, "Inside", "");
}



static int edbm_do_smooth_vertex_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	ModifierData *md;
	int mirrx = FALSE, mirry = FALSE, mirrz = FALSE;
	int i, repeat;
	float clipdist = 0.0f;

	int xaxis = RNA_boolean_get(op->ptr, "xaxis");
	int yaxis = RNA_boolean_get(op->ptr, "yaxis");
	int zaxis = RNA_boolean_get(op->ptr, "zaxis");

	/* mirror before smooth */
	if (((Mesh *)obedit->data)->editflag & ME_EDIT_MIRROR_X) {
		EDBM_verts_mirror_cache_begin(em, TRUE);
	}

	/* if there is a mirror modifier with clipping, flag the verts that
	 * are within tolerance of the plane(s) of reflection 
	 */
	for (md = obedit->modifiers.first; md; md = md->next) {
		if (md->type == eModifierType_Mirror && (md->mode & eModifierMode_Realtime)) {
			MirrorModifierData *mmd = (MirrorModifierData *)md;
		
			if (mmd->flag & MOD_MIR_CLIPPING) {
				if (mmd->flag & MOD_MIR_AXIS_X)
					mirrx = TRUE;
				if (mmd->flag & MOD_MIR_AXIS_Y)
					mirry = TRUE;
				if (mmd->flag & MOD_MIR_AXIS_Z)
					mirrz = TRUE;

				clipdist = mmd->tolerance;
			}
		}
	}

	repeat = RNA_int_get(op->ptr, "repeat");
	if (!repeat)
		repeat = 1;
	
	for (i = 0; i < repeat; i++) {
		if (!EDBM_op_callf(em, op,
		                   "smooth_vert verts=%hv mirror_clip_x=%b mirror_clip_y=%b mirror_clip_z=%b clipdist=%f "
		                   "use_axis_x=%b use_axis_y=%b use_axis_z=%b",
		                   BM_ELEM_SELECT, mirrx, mirry, mirrz, clipdist, xaxis, yaxis, zaxis))
		{
			return OPERATOR_CANCELLED;
		}
	}

	/* apply mirror */
	if (((Mesh *)obedit->data)->editflag & ME_EDIT_MIRROR_X) {
		EDBM_verts_mirror_apply(em, BM_ELEM_SELECT, 0);
		EDBM_verts_mirror_cache_end(em);
	}

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}	
	
void MESH_OT_vertices_smooth(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Smooth Vertex";
	ot->description = "Flatten angles of selected vertices";
	ot->idname = "MESH_OT_vertices_smooth";
	
	/* api callbacks */
	ot->exec = edbm_do_smooth_vertex_exec;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	RNA_def_int(ot->srna, "repeat", 1, 1, 100, "Number of times to smooth the mesh", "", 1, INT_MAX);
	RNA_def_boolean(ot->srna, "xaxis", 1, "X-Axis", "Smooth along the X axis");
	RNA_def_boolean(ot->srna, "yaxis", 1, "Y-Axis", "Smooth along the Y axis");
	RNA_def_boolean(ot->srna, "zaxis", 1, "Z-Axis", "Smooth along the Z axis");
}

/********************** Smooth/Solid Operators *************************/

static void mesh_set_smooth_faces(BMEditMesh *em, short smooth)
{
	BMIter iter;
	BMFace *efa;

	if (em == NULL) return;
	
	BM_ITER_MESH (efa, &iter, em->bm, BM_FACES_OF_MESH) {
		if (BM_elem_flag_test(efa, BM_ELEM_SELECT)) {
			BM_elem_flag_set(efa, BM_ELEM_SMOOTH, smooth);
		}
	}
}

static int edbm_faces_shade_smooth_exec(bContext *C, wmOperator *UNUSED(op))
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);

	mesh_set_smooth_faces(em, 1);

	EDBM_update_generic(C, em, FALSE);

	return OPERATOR_FINISHED;
}

void MESH_OT_faces_shade_smooth(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Shade Smooth";
	ot->description = "Display faces smooth (using vertex normals)";
	ot->idname = "MESH_OT_faces_shade_smooth";

	/* api callbacks */
	ot->exec = edbm_faces_shade_smooth_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static int edbm_faces_shade_flat_exec(bContext *C, wmOperator *UNUSED(op))
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);

	mesh_set_smooth_faces(em, 0);

	EDBM_update_generic(C, em, FALSE);

	return OPERATOR_FINISHED;
}

void MESH_OT_faces_shade_flat(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Shade Flat";
	ot->description = "Display faces flat";
	ot->idname = "MESH_OT_faces_shade_flat";

	/* api callbacks */
	ot->exec = edbm_faces_shade_flat_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}


/********************** UV/Color Operators *************************/

static int edbm_rotate_uvs_exec(bContext *C, wmOperator *op)
{
	Object *ob = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(ob);
	BMOperator bmop;

	/* get the direction from RNA */
	int dir = RNA_enum_get(op->ptr, "direction");

	/* initialize the bmop using EDBM api, which does various ui error reporting and other stuff */
	EDBM_op_init(em, &bmop, op, "rotate_uvs faces=%hf dir=%i", BM_ELEM_SELECT, dir);

	/* execute the operator */
	BMO_op_exec(em->bm, &bmop);

	/* finish the operator */
	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}

	EDBM_update_generic(C, em, FALSE);

	/* we succeeded */
	return OPERATOR_FINISHED;
}

static int edbm_reverse_uvs_exec(bContext *C, wmOperator *op)
{
	Object *ob = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(ob);
	BMOperator bmop;

	/* initialize the bmop using EDBM api, which does various ui error reporting and other stuff */
	EDBM_op_init(em, &bmop, op, "reverse_uvs faces=%hf", BM_ELEM_SELECT);

	/* execute the operator */
	BMO_op_exec(em->bm, &bmop);

	/* finish the operator */
	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}

	EDBM_update_generic(C, em, FALSE);

	/* we succeeded */
	return OPERATOR_FINISHED;
}

static int edbm_rotate_colors_exec(bContext *C, wmOperator *op)
{
	Object *ob = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(ob);
	BMOperator bmop;

	/* get the direction from RNA */
	int dir = RNA_enum_get(op->ptr, "direction");

	/* initialize the bmop using EDBM api, which does various ui error reporting and other stuff */
	EDBM_op_init(em, &bmop, op, "rotate_colors faces=%hf dir=%i", BM_ELEM_SELECT, dir);

	/* execute the operator */
	BMO_op_exec(em->bm, &bmop);

	/* finish the operator */
	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}

	/* dependencies graph and notification stuff */
	EDBM_update_generic(C, em, FALSE);

	/* we succeeded */
	return OPERATOR_FINISHED;
}


static int edbm_reverse_colors_exec(bContext *C, wmOperator *op)
{
	Object *ob = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(ob);
	BMOperator bmop;

	/* initialize the bmop using EDBM api, which does various ui error reporting and other stuff */
	EDBM_op_init(em, &bmop, op, "reverse_colors faces=%hf", BM_ELEM_SELECT);

	/* execute the operator */
	BMO_op_exec(em->bm, &bmop);

	/* finish the operator */
	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}

	EDBM_update_generic(C, em, FALSE);

	/* we succeeded */
	return OPERATOR_FINISHED;
}

void MESH_OT_uvs_rotate(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Rotate UVs";
	ot->idname = "MESH_OT_uvs_rotate";
	ot->description = "Rotate UV coordinates inside faces";

	/* api callbacks */
	ot->exec = edbm_rotate_uvs_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* props */
	RNA_def_enum(ot->srna, "direction", direction_items, DIRECTION_CW, "Direction", "Direction to rotate UVs around");
}

//void MESH_OT_uvs_mirror(wmOperatorType *ot)
void MESH_OT_uvs_reverse(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Reverse UVs";
	ot->idname = "MESH_OT_uvs_reverse";
	ot->description = "Flip direction of UV coordinates inside faces";

	/* api callbacks */
	ot->exec = edbm_reverse_uvs_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* props */
	//RNA_def_enum(ot->srna, "axis", axis_items, DIRECTION_CW, "Axis", "Axis to mirror UVs around");
}

void MESH_OT_colors_rotate(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Rotate Colors";
	ot->idname = "MESH_OT_colors_rotate";
	ot->description = "Rotate vertex colors inside faces";

	/* api callbacks */
	ot->exec = edbm_rotate_colors_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* props */
	RNA_def_enum(ot->srna, "direction", direction_items, DIRECTION_CCW, "Direction", "Direction to rotate edge around");
}

void MESH_OT_colors_reverse(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Reverse Colors";
	ot->idname = "MESH_OT_colors_reverse";
	ot->description = "Flip direction of vertex colors inside faces";

	/* api callbacks */
	ot->exec = edbm_reverse_colors_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* props */
	//RNA_def_enum(ot->srna, "axis", axis_items, DIRECTION_CW, "Axis", "Axis to mirror colors around");
}


static int merge_firstlast(BMEditMesh *em, int first, int uvmerge, wmOperator *wmop)
{
	BMVert *mergevert;
	BMEditSelection *ese;

	/* do sanity check in mergemenu in edit.c ?*/
	if (first == 0) {
		ese = em->bm->selected.last;
		mergevert = (BMVert *)ese->ele;
	}
	else {
		ese = em->bm->selected.first;
		mergevert = (BMVert *)ese->ele;
	}

	if (!BM_elem_flag_test(mergevert, BM_ELEM_SELECT))
		return OPERATOR_CANCELLED;
	
	if (uvmerge) {
		if (!EDBM_op_callf(em, wmop, "pointmerge_facedata verts=%hv snapv=%e", BM_ELEM_SELECT, mergevert))
			return OPERATOR_CANCELLED;
	}

	if (!EDBM_op_callf(em, wmop, "pointmerge verts=%hv merge_co=%v", BM_ELEM_SELECT, mergevert->co))
		return OPERATOR_CANCELLED;

	return OPERATOR_FINISHED;
}

static int merge_target(BMEditMesh *em, Scene *scene, View3D *v3d, Object *ob, 
                        int target, int uvmerge, wmOperator *wmop)
{
	BMIter iter;
	BMVert *v;
	float *vco = NULL, co[3], cent[3] = {0.0f, 0.0f, 0.0f};

	if (target) {
		vco = give_cursor(scene, v3d);
		copy_v3_v3(co, vco);
		mul_m4_v3(ob->imat, co);
	}
	else {
		float fac;
		int i = 0;
		BM_ITER_MESH (v, &iter, em->bm, BM_VERTS_OF_MESH) {
			if (!BM_elem_flag_test(v, BM_ELEM_SELECT))
				continue;
			add_v3_v3(cent, v->co);
			i++;
		}
		
		if (!i)
			return OPERATOR_CANCELLED;

		fac = 1.0f / (float)i;
		mul_v3_fl(cent, fac);
		copy_v3_v3(co, cent);
		vco = co;
	}

	if (!vco)
		return OPERATOR_CANCELLED;
	
	if (uvmerge) {
		if (!EDBM_op_callf(em, wmop, "average_vert_facedata verts=%hv", BM_ELEM_SELECT))
			return OPERATOR_CANCELLED;
	}

	if (!EDBM_op_callf(em, wmop, "pointmerge verts=%hv merge_co=%v", BM_ELEM_SELECT, co))
		return OPERATOR_CANCELLED;

	return OPERATOR_FINISHED;
}

static int edbm_merge_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	View3D *v3d = CTX_wm_view3d(C);
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	int status = 0, uvs = RNA_boolean_get(op->ptr, "uvs");

	switch (RNA_enum_get(op->ptr, "type")) {
		case 3:
			status = merge_target(em, scene, v3d, obedit, 0, uvs, op);
			break;
		case 4:
			status = merge_target(em, scene, v3d, obedit, 1, uvs, op);
			break;
		case 1:
			status = merge_firstlast(em, 0, uvs, op);
			break;
		case 6:
			status = merge_firstlast(em, 1, uvs, op);
			break;
		case 5:
			status = 1;
			if (!EDBM_op_callf(em, op, "collapse edges=%he", BM_ELEM_SELECT))
				status = 0;
			break;
	}

	if (!status)
		return OPERATOR_CANCELLED;

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

static EnumPropertyItem merge_type_items[] = {
	{6, "FIRST", 0, "At First", ""},
	{1, "LAST", 0, "At Last", ""},
	{3, "CENTER", 0, "At Center", ""},
	{4, "CURSOR", 0, "At Cursor", ""},
	{5, "COLLAPSE", 0, "Collapse", ""},
	{0, NULL, 0, NULL, NULL}
};

static EnumPropertyItem *merge_type_itemf(bContext *C, PointerRNA *UNUSED(ptr),  PropertyRNA *UNUSED(prop), int *free)
{	
	Object *obedit;
	EnumPropertyItem *item = NULL;
	int totitem = 0;
	
	if (!C) /* needed for docs */
		return merge_type_items;
	
	obedit = CTX_data_edit_object(C);
	if (obedit && obedit->type == OB_MESH) {
		BMEditMesh *em = BMEdit_FromObject(obedit);

		if (em->selectmode & SCE_SELECT_VERTEX) {
			if (em->bm->selected.first && em->bm->selected.last &&
			    ((BMEditSelection *)em->bm->selected.first)->htype == BM_VERT &&
			    ((BMEditSelection *)em->bm->selected.last)->htype == BM_VERT)
			{
				RNA_enum_items_add_value(&item, &totitem, merge_type_items, 6);
				RNA_enum_items_add_value(&item, &totitem, merge_type_items, 1);
			}
			else if (em->bm->selected.first && ((BMEditSelection *)em->bm->selected.first)->htype == BM_VERT) {
				RNA_enum_items_add_value(&item, &totitem, merge_type_items, 6);
			}
			else if (em->bm->selected.last && ((BMEditSelection *)em->bm->selected.last)->htype == BM_VERT) {
				RNA_enum_items_add_value(&item, &totitem, merge_type_items, 1);
			}
		}

		RNA_enum_items_add_value(&item, &totitem, merge_type_items, 3);
		RNA_enum_items_add_value(&item, &totitem, merge_type_items, 4);
		RNA_enum_items_add_value(&item, &totitem, merge_type_items, 5);
		RNA_enum_item_end(&item, &totitem);

		*free = 1;

		return item;
	}
	
	return NULL;
}

void MESH_OT_merge(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Merge";
	ot->description = "Merge selected vertices";
	ot->idname = "MESH_OT_merge";

	/* api callbacks */
	ot->exec = edbm_merge_exec;
	ot->invoke = WM_menu_invoke;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	ot->prop = RNA_def_enum(ot->srna, "type", merge_type_items, 3, "Type", "Merge method to use");
	RNA_def_enum_funcs(ot->prop, merge_type_itemf);
	RNA_def_boolean(ot->srna, "uvs", 1, "UVs", "Move UVs according to merge");
}


static int edbm_remove_doubles_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMOperator bmop;
	const float mergedist = RNA_float_get(op->ptr, "mergedist");
	int use_unselected = RNA_boolean_get(op->ptr, "use_unselected");
	int totvert_orig = em->bm->totvert;
	int count;

	if (use_unselected) {
		EDBM_op_init(em, &bmop, op,
		             "automerge verts=%hv dist=%f",
		             BM_ELEM_SELECT, mergedist);
		BMO_op_exec(em->bm, &bmop);

		if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
			return OPERATOR_CANCELLED;
		}
	}
	else {
		EDBM_op_init(em, &bmop, op,
		             "find_doubles verts=%hv dist=%f",
		             BM_ELEM_SELECT, mergedist);
		BMO_op_exec(em->bm, &bmop);

		if (!EDBM_op_callf(em, op, "weld_verts targetmap=%s", &bmop, "targetmapout")) {
			BMO_op_finish(em->bm, &bmop);
			return OPERATOR_CANCELLED;
		}

		if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
			return OPERATOR_CANCELLED;
		}
	}
	
	count = totvert_orig - em->bm->totvert;
	BKE_reportf(op->reports, RPT_INFO, "Removed %d vert%s", count, (count == 1) ? "ex" : "ices");

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_remove_doubles(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Remove Doubles";
	ot->description = "Remove duplicate vertices";
	ot->idname = "MESH_OT_remove_doubles";

	/* api callbacks */
	ot->exec = edbm_remove_doubles_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	RNA_def_float(ot->srna, "mergedist", 0.0001f, 0.000001f, 50.0f, 
	              "Merge Distance",
	              "Minimum distance between elements to merge", 0.00001, 10.0);
	RNA_def_boolean(ot->srna, "use_unselected", 0, "Unselected", "Merge selected to other unselected vertices");
}

/************************ Vertex Path Operator *************************/

typedef struct PathNode {
	/* int u; */       /* UNUSED */
	/* int visited; */ /* UNUSED */
	ListBase edges;
} PathNode;

typedef struct PathEdge {
	struct PathEdge *next, *prev;
	int v;
	float w;
} PathEdge;



static int edbm_select_vertex_path_exec(bContext *C, wmOperator *op)
{
	Object *ob = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(ob);
	BMOperator bmop;
	BMIter iter;
	BMVert *eve = NULL, *svert = NULL, *evert = NULL;
	BMEditSelection *sv, *ev;

	/* get the type from RNA */
	int type = RNA_enum_get(op->ptr, "type");

	/* first try to find vertices in edit selection */
	sv = em->bm->selected.last;
	if (sv != NULL) {
		ev = sv->prev;

		if (ev && (sv->htype == BM_VERT) && (ev->htype == BM_VERT)) {
			svert = (BMVert *)sv->ele;
			evert = (BMVert *)ev->ele;
		}
	}

	/* if those are not found, because vertices where selected by e.g.
	   border or circle select, find two selected vertices */
	if (svert == NULL) {
		BM_ITER_MESH (eve, &iter, em->bm, BM_VERTS_OF_MESH) {
			if (!BM_elem_flag_test(eve, BM_ELEM_SELECT) || BM_elem_flag_test(eve, BM_ELEM_HIDDEN))
				continue;

			if (svert == NULL) svert = eve;
			else if (evert == NULL) evert = eve;
			else {
				/* more than two vertices are selected,
				   show warning message and cancel operator */
				svert = evert = NULL;
				break;
			}
		}
	}

	if (svert == NULL || evert == NULL) {
		BKE_report(op->reports, RPT_WARNING, "Path Selection requires that two vertices be selected");
		return OPERATOR_CANCELLED;
	}

	/* initialize the bmop using EDBM api, which does various ui error reporting and other stuff */
	EDBM_op_init(em, &bmop, op, "shortest_path startv=%e endv=%e type=%i", svert, evert, type);

	/* execute the operator */
	BMO_op_exec(em->bm, &bmop);

	/* DO NOT clear the existing selection */
	/* EDBM_flag_disable_all(em, BM_ELEM_SELECT); */

	/* select the output */
	BMO_slot_buffer_hflag_enable(em->bm, &bmop, "vertout", BM_ALL, BM_ELEM_SELECT, TRUE);

	/* finish the operator */
	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}

	EDBM_selectmode_flush(em);

	EDBM_update_generic(C, em, FALSE);

	/* we succeeded */
	return OPERATOR_FINISHED;
}

void MESH_OT_select_vertex_path(wmOperatorType *ot)
{
	static const EnumPropertyItem type_items[] = {
		{VPATH_SELECT_EDGE_LENGTH, "EDGE_LENGTH", 0, "Edge Length", NULL},
		{VPATH_SELECT_TOPOLOGICAL, "TOPOLOGICAL", 0, "Topological", NULL},
		{0, NULL, 0, NULL, NULL}
	};

	/* identifiers */
	ot->name = "Select Vertex Path";
	ot->idname = "MESH_OT_select_vertex_path";
	ot->description = "Selected vertex path between two vertices";

	/* api callbacks */
	ot->exec = edbm_select_vertex_path_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	RNA_def_enum(ot->srna, "type", type_items, VPATH_SELECT_EDGE_LENGTH, "Type", "Method to compute distance");
}
/********************** Rip Operator *************************/

/************************ Shape Operators *************************/

/* BMESH_TODO this should be properly encapsulated in a bmop.  but later.*/
static void shape_propagate(BMEditMesh *em, wmOperator *op)
{
	BMIter iter;
	BMVert *eve = NULL;
	float *co;
	int i, totshape = CustomData_number_of_layers(&em->bm->vdata, CD_SHAPEKEY);

	if (!CustomData_has_layer(&em->bm->vdata, CD_SHAPEKEY)) {
		BKE_report(op->reports, RPT_ERROR, "Mesh does not have shape keys");
		return;
	}
	
	BM_ITER_MESH (eve, &iter, em->bm, BM_VERTS_OF_MESH) {
		if (!BM_elem_flag_test(eve, BM_ELEM_SELECT) || BM_elem_flag_test(eve, BM_ELEM_HIDDEN))
			continue;

		for (i = 0; i < totshape; i++) {
			co = CustomData_bmesh_get_n(&em->bm->vdata, eve->head.data, CD_SHAPEKEY, i);
			copy_v3_v3(co, eve->co);
		}
	}

#if 0
	//TAG Mesh Objects that share this data
	for (base = scene->base.first; base; base = base->next) {
		if (base->object && base->object->data == me) {
			base->object->recalc = OB_RECALC_DATA;
		}
	}
#endif
}


static int edbm_shape_propagate_to_all_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	Mesh *me = obedit->data;
	BMEditMesh *em = me->edit_btmesh;

	shape_propagate(em, op);

	EDBM_update_generic(C, em, FALSE);

	return OPERATOR_FINISHED;
}


void MESH_OT_shape_propagate_to_all(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Shape Propagate";
	ot->description = "Apply selected vertex locations to all other shape keys";
	ot->idname = "MESH_OT_shape_propagate_to_all";

	/* api callbacks */
	ot->exec = edbm_shape_propagate_to_all_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* BMESH_TODO this should be properly encapsulated in a bmop.  but later.*/
static int edbm_blend_from_shape_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	Mesh *me = obedit->data;
	Key *key = me->key;
	KeyBlock *kb = NULL;
	BMEditMesh *em = me->edit_btmesh;
	BMVert *eve;
	BMIter iter;
	float co[3], *sco;
	float blend = RNA_float_get(op->ptr, "blend");
	int shape = RNA_enum_get(op->ptr, "shape");
	int add = RNA_boolean_get(op->ptr, "add");
	int totshape;

	/* sanity check */
	totshape = CustomData_number_of_layers(&em->bm->vdata, CD_SHAPEKEY);
	if (totshape == 0 || shape < 0 || shape >= totshape)
		return OPERATOR_CANCELLED;
	
	/* get shape key - needed for finding reference shape (for add mode only) */
	if (key) {
		kb = BLI_findlink(&key->block, shape);
	}
	
	/* perform blending on selected vertices*/
	BM_ITER_MESH (eve, &iter, em->bm, BM_VERTS_OF_MESH) {
		if (!BM_elem_flag_test(eve, BM_ELEM_SELECT) || BM_elem_flag_test(eve, BM_ELEM_HIDDEN))
			continue;
		
		/* get coordinates of shapekey we're blending from */
		sco = CustomData_bmesh_get_n(&em->bm->vdata, eve->head.data, CD_SHAPEKEY, shape);
		copy_v3_v3(co, sco);
		
		if (add) {
			/* in add mode, we add relative shape key offset */
			if (kb) {
				float *rco = CustomData_bmesh_get_n(&em->bm->vdata, eve->head.data, CD_SHAPEKEY, kb->relative);
				sub_v3_v3v3(co, co, rco);
			}
			
			madd_v3_v3fl(eve->co, co, blend);
		}
		else {
			/* in blend mode, we interpolate to the shape key */
			interp_v3_v3v3(eve->co, eve->co, co, blend);
		}
	}

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

static EnumPropertyItem *shape_itemf(bContext *C, PointerRNA *UNUSED(ptr),  PropertyRNA *UNUSED(prop), int *free)
{	
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em;
	EnumPropertyItem *item = NULL;
	int totitem = 0;

	if ((obedit && obedit->type == OB_MESH) &&
	    (em = BMEdit_FromObject(obedit)) &&
	    CustomData_has_layer(&em->bm->vdata, CD_SHAPEKEY))
	{
		EnumPropertyItem tmp = {0, "", 0, "", ""};
		int a;

		for (a = 0; a < em->bm->vdata.totlayer; a++) {
			if (em->bm->vdata.layers[a].type != CD_SHAPEKEY)
				continue;

			tmp.value = totitem;
			tmp.identifier = em->bm->vdata.layers[a].name;
			tmp.name = em->bm->vdata.layers[a].name;
			/* RNA_enum_item_add sets totitem itself! */
			RNA_enum_item_add(&item, &totitem, &tmp);
		}
	}

	RNA_enum_item_end(&item, &totitem);
	*free = 1;

	return item;
}

void MESH_OT_blend_from_shape(wmOperatorType *ot)
{
	PropertyRNA *prop;
	static EnumPropertyItem shape_items[] = {{0, NULL, 0, NULL, NULL}};

	/* identifiers */
	ot->name = "Blend From Shape";
	ot->description = "Blend in shape from a shape key";
	ot->idname = "MESH_OT_blend_from_shape";

	/* api callbacks */
	ot->exec = edbm_blend_from_shape_exec;
	ot->invoke = WM_operator_props_popup;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	prop = RNA_def_enum(ot->srna, "shape", shape_items, 0, "Shape", "Shape key to use for blending");
	RNA_def_enum_funcs(prop, shape_itemf);
	RNA_def_float(ot->srna, "blend", 1.0f, -FLT_MAX, FLT_MAX, "Blend", "Blending factor", -2.0f, 2.0f);
	RNA_def_boolean(ot->srna, "add", 1, "Add", "Add rather than blend between shapes");
}

/* BMESH_TODO - some way to select on an arbitrary axis */
static int edbm_select_axis_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMEditSelection *ese = em->bm->selected.last;
	int axis = RNA_enum_get(op->ptr, "axis");
	int mode = RNA_enum_get(op->ptr, "mode"); /* -1 == aligned, 0 == neg, 1 == pos */

	if (ese == NULL || ese->htype != BM_VERT) {
		BKE_report(op->reports, RPT_WARNING, "This operator requires an active vertex (last selected)");
		return OPERATOR_CANCELLED;
	}
	else {
		BMVert *ev, *act_vert = (BMVert *)ese->ele;
		BMIter iter;
		float value = act_vert->co[axis];
		float limit =  CTX_data_tool_settings(C)->doublimit; // XXX

		if (mode == 0)
			value -= limit;
		else if (mode == 1)
			value += limit;

		BM_ITER_MESH (ev, &iter, em->bm, BM_VERTS_OF_MESH) {
			if (!BM_elem_flag_test(ev, BM_ELEM_HIDDEN)) {
				switch (mode) {
					case -1: /* aligned */
						if (fabsf(ev->co[axis] - value) < limit)
							BM_vert_select_set(em->bm, ev, TRUE);
						break;
					case 0: /* neg */
						if (ev->co[axis] > value)
							BM_vert_select_set(em->bm, ev, TRUE);
						break;
					case 1: /* pos */
						if (ev->co[axis] < value)
							BM_vert_select_set(em->bm, ev, TRUE);
						break;
				}
			}
		}
	}

	EDBM_selectmode_flush(em);
	WM_event_add_notifier(C, NC_GEOM | ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_select_axis(wmOperatorType *ot)
{
	static EnumPropertyItem axis_mode_items[] = {
		{0,  "POSITIVE", 0, "Positive Axis", ""},
		{1,  "NEGATIVE", 0, "Negative Axis", ""},
		{-1, "ALIGNED",  0, "Aligned Axis", ""},
		{0, NULL, 0, NULL, NULL}
	};

	static EnumPropertyItem axis_items_xyz[] = {
		{0, "X_AXIS", 0, "X Axis", ""},
		{1, "Y_AXIS", 0, "Y Axis", ""},
		{2, "Z_AXIS", 0, "Z Axis", ""},
		{0, NULL, 0, NULL, NULL}
	};

	/* identifiers */
	ot->name = "Select Axis";
	ot->description = "Select all data in the mesh on a single axis";
	ot->idname = "MESH_OT_select_axis";

	/* api callbacks */
	ot->exec = edbm_select_axis_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	RNA_def_enum(ot->srna, "mode", axis_mode_items, 0, "Axis Mode", "Axis side to use when selecting");
	RNA_def_enum(ot->srna, "axis", axis_items_xyz, 0, "Axis", "Select the axis to compare each vertex on");
}

static int edbm_solidify_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	Mesh *me = obedit->data;
	BMEditMesh *em = me->edit_btmesh;
	BMesh *bm = em->bm;
	BMOperator bmop;

	float thickness = RNA_float_get(op->ptr, "thickness");

	if (!EDBM_op_init(em, &bmop, op, "solidify geom=%hf thickness=%f", BM_ELEM_SELECT, thickness)) {
		return OPERATOR_CANCELLED;
	}

	/* deselect only the faces in the region to be solidified (leave wire
	 * edges and loose verts selected, as there will be no corresponding
	 * geometry selected below) */
	BMO_slot_buffer_hflag_disable(bm, &bmop, "geom", BM_FACE, BM_ELEM_SELECT, TRUE);

	/* run the solidify operator */
	BMO_op_exec(bm, &bmop);

	/* select the newly generated faces */
	BMO_slot_buffer_hflag_enable(bm, &bmop, "geomout", BM_FACE, BM_ELEM_SELECT, TRUE);

	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}


void MESH_OT_solidify(wmOperatorType *ot)
{
	PropertyRNA *prop;
	/* identifiers */
	ot->name = "Solidify";
	ot->description = "Create a solid skin by extruding, compensating for sharp angles";
	ot->idname = "MESH_OT_solidify";

	/* api callbacks */
	ot->exec = edbm_solidify_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	prop = RNA_def_float(ot->srna, "thickness", 0.01f, -FLT_MAX, FLT_MAX, "thickness", "", -10.0f, 10.0f);
	RNA_def_property_ui_range(prop, -10, 10, 0.1, 4);
}

typedef struct CutCurve {
	float x;
	float y;
} CutCurve;

/* ******************************************************************** */
/* Knife Subdivide Tool.  Subdivides edges intersected by a mouse trail
 * drawn by user.
 *
 * Currently mapped to KKey when in MeshEdit mode.
 * Usage:
 * - Hit Shift K, Select Centers or Exact
 * - Hold LMB down to draw path, hit RETKEY.
 * - ESC cancels as expected.
 *
 * Contributed by Robert Wenzlaff (Det. Thorn).
 *
 * 2.5 Revamp:
 *  - non modal (no menu before cutting)
 *  - exit on mouse release
 *  - polygon/segment drawing can become handled by WM cb later
 *
 * bmesh port version
 */

#define KNIFE_EXACT     1
#define KNIFE_MIDPOINT  2
#define KNIFE_MULTICUT  3

static EnumPropertyItem knife_items[] = {
	{KNIFE_EXACT, "EXACT", 0, "Exact", ""},
	{KNIFE_MIDPOINT, "MIDPOINTS", 0, "Midpoints", ""},
	{KNIFE_MULTICUT, "MULTICUT", 0, "Multicut", ""},
	{0, NULL, 0, NULL, NULL}
};

/* bm_edge_seg_isect() Determines if and where a mouse trail intersects an BMEdge */

static float bm_edge_seg_isect(BMEdge *e, CutCurve *c, int len, char mode,
                               struct GHash *gh, int *isected)
{
#define MAXSLOPE 100000
	float x11, y11, x12 = 0, y12 = 0, x2max, x2min, y2max;
	float y2min, dist, lastdist = 0, xdiff2, xdiff1;
	float m1, b1, m2, b2, x21, x22, y21, y22, xi;
	float yi, x1min, x1max, y1max, y1min, perc = 0;
	float  *scr;
	float threshold = 0.0;
	int i;
	
	//threshold = 0.000001; /* tolerance for vertex intersection */
	// XXX threshold = scene->toolsettings->select_thresh / 100;
	
	/* Get screen coords of verts */
	scr = BLI_ghash_lookup(gh, e->v1);
	x21 = scr[0];
	y21 = scr[1];
	
	scr = BLI_ghash_lookup(gh, e->v2);
	x22 = scr[0];
	y22 = scr[1];
	
	xdiff2 = (x22 - x21);
	if (xdiff2) {
		m2 = (y22 - y21) / xdiff2;
		b2 = ((x22 * y21) - (x21 * y22)) / xdiff2;
	}
	else {
		m2 = MAXSLOPE;  /* Verticle slope  */
		b2 = x22;
	}

	*isected = 0;

	/* check for _exact_ vertex intersection first */
	if (mode != KNIFE_MULTICUT) {
		for (i = 0; i < len; i++) {
			if (i > 0) {
				x11 = x12;
				y11 = y12;
			}
			else {
				x11 = c[i].x;
				y11 = c[i].y;
			}
			x12 = c[i].x;
			y12 = c[i].y;
			
			/* test e->v1 */
			if ((x11 == x21 && y11 == y21) || (x12 == x21 && y12 == y21)) {
				perc = 0;
				*isected = 1;
				return perc;
			}
			/* test e->v2 */
			else if ((x11 == x22 && y11 == y22) || (x12 == x22 && y12 == y22)) {
				perc = 0;
				*isected = 2;
				return perc;
			}
		}
	}
	
	/* now check for edge intersect (may produce vertex intersection as well) */
	for (i = 0; i < len; i++) {
		if (i > 0) {
			x11 = x12;
			y11 = y12;
		}
		else {
			x11 = c[i].x;
			y11 = c[i].y;
		}
		x12 = c[i].x;
		y12 = c[i].y;
		
		/* Perp. Distance from point to line */
		if (m2 != MAXSLOPE) dist = (y12 - m2 * x12 - b2);  /* /sqrt(m2 * m2 + 1); Only looking for */
		/* change in sign.  Skip extra math */
		else dist = x22 - x12;
		
		if (i == 0) lastdist = dist;
		
		/* if dist changes sign, and intersect point in edge's Bound Box */
		if ((lastdist * dist) <= 0) {
			xdiff1 = (x12 - x11); /* Equation of line between last 2 points */
			if (xdiff1) {
				m1 = (y12 - y11) / xdiff1;
				b1 = ((x12 * y11) - (x11 * y12)) / xdiff1;
			}
			else {
				m1 = MAXSLOPE;
				b1 = x12;
			}
			x2max = maxf(x21, x22) + 0.001f; /* prevent missed edges   */
			x2min = minf(x21, x22) - 0.001f; /* due to round off error */
			y2max = maxf(y21, y22) + 0.001f;
			y2min = minf(y21, y22) - 0.001f;
			
			/* Found an intersect,  calc intersect point */
			if (m1 == m2) { /* co-incident lines */
				/* cut at 50% of overlap area */
				x1max = maxf(x11, x12);
				x1min = minf(x11, x12);
				xi = (minf(x2max, x1max) + maxf(x2min, x1min)) / 2.0f;
				
				y1max = maxf(y11, y12);
				y1min = minf(y11, y12);
				yi = (minf(y2max, y1max) + maxf(y2min, y1min)) / 2.0f;
			}
			else if (m2 == MAXSLOPE) {
				xi = x22;
				yi = m1 * x22 + b1;
			}
			else if (m1 == MAXSLOPE) {
				xi = x12;
				yi = m2 * x12 + b2;
			}
			else {
				xi = (b1 - b2) / (m2 - m1);
				yi = (b1 * m2 - m1 * b2) / (m2 - m1);
			}
			
			/* Intersect inside bounding box of edge?*/
			if ((xi >= x2min) && (xi <= x2max) && (yi <= y2max) && (yi >= y2min)) {
				/* test for vertex intersect that may be 'close enough'*/
				if (mode != KNIFE_MULTICUT) {
					if (xi <= (x21 + threshold) && xi >= (x21 - threshold)) {
						if (yi <= (y21 + threshold) && yi >= (y21 - threshold)) {
							*isected = 1;
							perc = 0;
							break;
						}
					}
					if (xi <= (x22 + threshold) && xi >= (x22 - threshold)) {
						if (yi <= (y22 + threshold) && yi >= (y22 - threshold)) {
							*isected = 2;
							perc = 0;
							break;
						}
					}
				}
				if ((m2 <= 1.0f) && (m2 >= -1.0f)) perc = (xi - x21) / (x22 - x21);
				else perc = (yi - y21) / (y22 - y21);  /* lower slope more accurate */
				//isect = 32768.0 * (perc + 0.0000153); /* Percentage in 1 / 32768ths */
				
				break;
			}
		}	
		lastdist = dist;
	}
	return perc;
} 

#define MAX_CUTS 2048

static int edbm_knife_cut_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMesh *bm = em->bm;
	ARegion *ar = CTX_wm_region(C);
	BMVert *bv;
	BMIter iter;
	BMEdge *be;
	BMOperator bmop;
	CutCurve curve[MAX_CUTS];
	struct GHash *gh;
	float isect = 0.0f;
	float  *scr, co[4];
	int len = 0, isected;
	short numcuts = 1, mode = RNA_int_get(op->ptr, "type");
	
	/* edit-object needed for matrix, and ar->regiondata for projections to work */
	if (ELEM3(NULL, obedit, ar, ar->regiondata))
		return OPERATOR_CANCELLED;
	
	if (bm->totvertsel < 2) {
		//error("No edges are selected to operate on");
		return OPERATOR_CANCELLED;
	}

	/* get the cut curve */
	RNA_BEGIN(op->ptr, itemptr, "path")
	{
		RNA_float_get_array(&itemptr, "loc", (float *)&curve[len]);
		len++;
		if (len >= MAX_CUTS) {
			break;
		}
	}
	RNA_END;
	
	if (len < 2) {
		return OPERATOR_CANCELLED;
	}

	/* the floating point coordinates of verts in screen space will be stored in a hash table according to the vertices pointer */
	gh = BLI_ghash_ptr_new("knife cut exec");
	for (bv = BM_iter_new(&iter, bm, BM_VERTS_OF_MESH, NULL); bv; bv = BM_iter_step(&iter)) {
		scr = MEM_mallocN(sizeof(float) * 2, "Vertex Screen Coordinates");
		copy_v3_v3(co, bv->co);
		co[3] = 1.0f;
		mul_m4_v4(obedit->obmat, co);
		project_float(ar, co, scr);
		BLI_ghash_insert(gh, bv, scr);
	}

	if (!EDBM_op_init(em, &bmop, op, "subdivide_edges")) {
		return OPERATOR_CANCELLED;
	}

	/* store percentage of edge cut for KNIFE_EXACT here.*/
	for (be = BM_iter_new(&iter, bm, BM_EDGES_OF_MESH, NULL); be; be = BM_iter_step(&iter)) {
		if (BM_elem_flag_test(be, BM_ELEM_SELECT)) {
			isect = bm_edge_seg_isect(be, curve, len, mode, gh, &isected);
			
			if (isect != 0.0f) {
				if (mode != KNIFE_MULTICUT && mode != KNIFE_MIDPOINT) {
					BMO_slot_map_float_insert(bm, &bmop,
					                          "edgepercents",
					                          be, isect);

				}
				BMO_elem_flag_enable(bm, be, 1);
			}
			else {
				BMO_elem_flag_disable(bm, be, 1);
			}
		}
		else {
			BMO_elem_flag_disable(bm, be, 1);
		}
	}
	
	BMO_slot_buffer_from_enabled_flag(bm, &bmop, "edges", BM_EDGE, 1);

	if (mode == KNIFE_MIDPOINT) numcuts = 1;
	BMO_slot_int_set(&bmop, "numcuts", numcuts);

	BMO_slot_int_set(&bmop, "quadcornertype", SUBD_STRAIGHT_CUT);
	BMO_slot_bool_set(&bmop, "use_singleedge", FALSE);
	BMO_slot_bool_set(&bmop, "use_gridfill", FALSE);

	BMO_slot_float_set(&bmop, "radius", 0);
	
	BMO_op_exec(bm, &bmop);
	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}
	
	BLI_ghash_free(gh, NULL, (GHashValFreeFP)MEM_freeN);

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_knife_cut(wmOperatorType *ot)
{
	PropertyRNA *prop;
	
	ot->name = "Knife Cut";
	ot->description = "Cut selected edges and faces into parts";
	ot->idname = "MESH_OT_knife_cut";
	
	ot->invoke = WM_gesture_lines_invoke;
	ot->modal = WM_gesture_lines_modal;
	ot->exec = edbm_knife_cut_exec;
	
	ot->poll = EM_view3d_poll;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
	
	RNA_def_enum(ot->srna, "type", knife_items, KNIFE_EXACT, "Type", "");
	prop = RNA_def_property(ot->srna, "path", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_runtime(prop, &RNA_OperatorMousePath);
	
	/* internal */
	RNA_def_int(ot->srna, "cursor", BC_KNIFECURSOR, 0, INT_MAX, "Cursor", "", 0, INT_MAX);
}

static int mesh_separate_tagged(Main *bmain, Scene *scene, Base *base_old, BMesh *bm_old)
{
	Base *base_new;
	Object *obedit = base_old->object;
	BMesh *bm_new;

	bm_new = BM_mesh_create(&bm_mesh_allocsize_default);
	CustomData_copy(&bm_old->vdata, &bm_new->vdata, CD_MASK_BMESH, CD_CALLOC, 0);
	CustomData_copy(&bm_old->edata, &bm_new->edata, CD_MASK_BMESH, CD_CALLOC, 0);
	CustomData_copy(&bm_old->ldata, &bm_new->ldata, CD_MASK_BMESH, CD_CALLOC, 0);
	CustomData_copy(&bm_old->pdata, &bm_new->pdata, CD_MASK_BMESH, CD_CALLOC, 0);

	CustomData_bmesh_init_pool(&bm_new->vdata, bm_mesh_allocsize_default.totvert, BM_VERT);
	CustomData_bmesh_init_pool(&bm_new->edata, bm_mesh_allocsize_default.totedge, BM_EDGE);
	CustomData_bmesh_init_pool(&bm_new->ldata, bm_mesh_allocsize_default.totloop, BM_LOOP);
	CustomData_bmesh_init_pool(&bm_new->pdata, bm_mesh_allocsize_default.totface, BM_FACE);

	base_new = ED_object_add_duplicate(bmain, scene, base_old, USER_DUP_MESH);
	/* DAG_scene_sort(bmain, scene); */ /* normally would call directly after but in this case delay recalc */
	assign_matarar(base_new->object, give_matarar(obedit), *give_totcolp(obedit)); /* new in 2.5 */

	ED_base_object_select(base_new, BA_SELECT);

	BMO_op_callf(bm_old, (BMO_FLAG_DEFAULTS & ~BMO_FLAG_RESPECT_HIDE),
	             "duplicate geom=%hvef dest=%p", BM_ELEM_TAG, bm_new);
	BMO_op_callf(bm_old, (BMO_FLAG_DEFAULTS & ~BMO_FLAG_RESPECT_HIDE),
	             "delete geom=%hvef context=%i", BM_ELEM_TAG, DEL_FACES);

	/* deselect loose data - this used to get deleted,
	 * we could de-select edges and verts only, but this turns out to be less complicated
	 * since de-selecting all skips selection flushing logic */
	BM_mesh_elem_hflag_disable_all(bm_old, BM_VERT | BM_EDGE | BM_FACE, BM_ELEM_SELECT, FALSE);

	BM_mesh_normals_update(bm_new, FALSE);

	BM_mesh_bm_to_me(bm_new, base_new->object->data, FALSE);

	BM_mesh_free(bm_new);
	((Mesh *)base_new->object->data)->edit_btmesh = NULL;
	
	return TRUE;
}

static int mesh_separate_selected(Main *bmain, Scene *scene, Base *base_old, BMesh *bm_old)
{
	/* we may have tags from previous operators */
	BM_mesh_elem_hflag_disable_all(bm_old, BM_FACE | BM_EDGE | BM_VERT, BM_ELEM_TAG, FALSE);

	/* sel -> tag */
	BM_mesh_elem_hflag_enable_test(bm_old, BM_FACE | BM_EDGE | BM_VERT, BM_ELEM_TAG, TRUE, BM_ELEM_SELECT);

	return mesh_separate_tagged(bmain, scene, base_old, bm_old);
}

/* flush a hflag to from verts to edges/faces */
static void bm_mesh_hflag_flush_vert(BMesh *bm, const char hflag)
{
	BMEdge *e;
	BMLoop *l_iter;
	BMLoop *l_first;
	BMFace *f;

	BMIter eiter;
	BMIter fiter;

	int ok;

	BM_ITER_MESH (e, &eiter, bm, BM_EDGES_OF_MESH) {
		if (BM_elem_flag_test(e->v1, hflag) &&
		    BM_elem_flag_test(e->v2, hflag))
		{
			BM_elem_flag_enable(e, hflag);
		}
		else {
			BM_elem_flag_disable(e, hflag);
		}
	}
	BM_ITER_MESH (f, &fiter, bm, BM_FACES_OF_MESH) {
		ok = TRUE;
		l_iter = l_first = BM_FACE_FIRST_LOOP(f);
		do {
			if (!BM_elem_flag_test(l_iter->v, hflag)) {
				ok = FALSE;
				break;
			}
		} while ((l_iter = l_iter->next) != l_first);

		BM_elem_flag_set(f, hflag, ok);
	}
}

static int mesh_separate_material(Main *bmain, Scene *scene, Base *base_old, BMesh *bm_old)
{
	BMFace *f_cmp, *f;
	BMIter iter;
	int result = FALSE;

	while ((f_cmp = BM_iter_at_index(bm_old, BM_FACES_OF_MESH, NULL, 0))) {
		const short mat_nr = f_cmp->mat_nr;
		int tot = 0;

		BM_mesh_elem_hflag_disable_all(bm_old, BM_VERT | BM_EDGE | BM_FACE, BM_ELEM_TAG, FALSE);

		BM_ITER_MESH (f, &iter, bm_old, BM_FACES_OF_MESH) {
			if (f->mat_nr == mat_nr) {
				BMLoop *l_iter;
				BMLoop *l_first;

				BM_elem_flag_enable(f, BM_ELEM_TAG);
				l_iter = l_first = BM_FACE_FIRST_LOOP(f);
				do {
					BM_elem_flag_enable(l_iter->v, BM_ELEM_TAG);
					BM_elem_flag_enable(l_iter->e, BM_ELEM_TAG);
				} while ((l_iter = l_iter->next) != l_first);

				tot++;
			}
		}

		/* leave the current object with some materials */
		if (tot == bm_old->totface) {
			break;
		}

		/* Move selection into a separate object */
		result |= mesh_separate_tagged(bmain, scene, base_old, bm_old);
	}

	return result;
}

static int mesh_separate_loose(Main *bmain, Scene *scene, Base *base_old, BMesh *bm_old)
{
	int i;
	BMEdge *e;
	BMVert *v_seed;
	BMWalker walker;
	int result = FALSE;
	int max_iter = bm_old->totvert;

	/* Clear all selected vertices */
	BM_mesh_elem_hflag_disable_all(bm_old, BM_VERT | BM_EDGE | BM_FACE, BM_ELEM_TAG, FALSE);

	/* A "while (true)" loop should work here as each iteration should
	 * select and remove at least one vertex and when all vertices
	 * are selected the loop will break out. But guard against bad
	 * behavior by limiting iterations to the number of vertices in the
	 * original mesh.*/
	for (i = 0; i < max_iter; i++) {
		int tot = 0;
		/* Get a seed vertex to start the walk */
		v_seed = BM_iter_at_index(bm_old, BM_VERTS_OF_MESH, NULL, 0);

		/* No vertices available, can't do anything */
		if (v_seed == NULL) {
			break;
		}

		/* Select the seed explicitly, in case it has no edges */
		if (!BM_elem_flag_test(v_seed, BM_ELEM_TAG)) { BM_elem_flag_enable(v_seed, BM_ELEM_TAG); tot++; }

		/* Walk from the single vertex, selecting everything connected
		 * to it */
		BMW_init(&walker, bm_old, BMW_SHELL,
		         BMW_MASK_NOP, BMW_MASK_NOP, BMW_MASK_NOP,
		         BMW_FLAG_NOP,
		         BMW_NIL_LAY);

		e = BMW_begin(&walker, v_seed);
		for (; e; e = BMW_step(&walker)) {
			if (!BM_elem_flag_test(e->v1, BM_ELEM_TAG)) { BM_elem_flag_enable(e->v1, BM_ELEM_TAG); tot++; }
			if (!BM_elem_flag_test(e->v2, BM_ELEM_TAG)) { BM_elem_flag_enable(e->v2, BM_ELEM_TAG); tot++; }
		}
		BMW_end(&walker);

		if (bm_old->totvert == tot) {
			/* Every vertex selected, nothing to separate, work is done */
			break;
		}

		/* Flush the selection to get edge/face selections matching
		 * the vertex selection */
		bm_mesh_hflag_flush_vert(bm_old, BM_ELEM_TAG);

		/* Move selection into a separate object */
		result |= mesh_separate_tagged(bmain, scene, base_old, bm_old);
	}

	return result;
}

static int edbm_separate_exec(bContext *C, wmOperator *op)
{
	Main *bmain = CTX_data_main(C);
	Scene *scene = CTX_data_scene(C);
	int retval = 0, type = RNA_enum_get(op->ptr, "type");
	
	if (ED_operator_editmesh(C)) {
		Base *base = CTX_data_active_base(C);
		BMEditMesh *em = BMEdit_FromObject(base->object);

		/* editmode separate */
		if      (type == 0) retval = mesh_separate_selected(bmain, scene, base, em->bm);
		else if (type == 1) retval = mesh_separate_material(bmain, scene, base, em->bm);
		else if (type == 2) retval = mesh_separate_loose(bmain, scene, base, em->bm);
		else                BLI_assert(0);

		if (retval) {
			EDBM_update_generic(C, em, TRUE);
		}
	}
	else {
		if (type == 0) {
			BKE_report(op->reports, RPT_ERROR, "Selecton not supported in object mode");
			return OPERATOR_CANCELLED;
		}

		/* object mode separate */
		CTX_DATA_BEGIN(C, Base *, base_iter, selected_editable_bases)
		{
			Object *ob = base_iter->object;
			if (ob->type == OB_MESH) {
				Mesh *me = ob->data;
				if (me->id.lib == NULL) {
					BMesh *bm_old = NULL;
					int retval_iter = 0;

					bm_old = BM_mesh_create(&bm_mesh_allocsize_default);

					BM_mesh_bm_from_me(bm_old, me, FALSE, 0);

					if      (type == 1) retval_iter = mesh_separate_material(bmain, scene, base_iter, bm_old);
					else if (type == 2) retval_iter = mesh_separate_loose(bmain, scene, base_iter, bm_old);
					else                BLI_assert(0);

					if (retval_iter) {
						BM_mesh_bm_to_me(bm_old, me, FALSE);

						DAG_id_tag_update(&me->id, OB_RECALC_DATA);
						WM_event_add_notifier(C, NC_GEOM | ND_DATA, me);
					}

					BM_mesh_free(bm_old);

					retval |= retval_iter;
				}
			}
		}
		CTX_DATA_END;
	}

	if (retval) {
		/* delay depsgraph recalc until all objects are duplicated */
		DAG_scene_sort(bmain, scene);

		return OPERATOR_FINISHED;
	}

	return OPERATOR_CANCELLED;
}

/* *************** Operator: separate parts *************/

static EnumPropertyItem prop_separate_types[] = {
	{0, "SELECTED", 0, "Selection", ""},
	{1, "MATERIAL", 0, "By Material", ""},
	{2, "LOOSE", 0, "By loose parts", ""},
	{0, NULL, 0, NULL, NULL}
};

void MESH_OT_separate(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Separate";
	ot->description = "Separate selected geometry into a new mesh";
	ot->idname = "MESH_OT_separate";
	
	/* api callbacks */
	ot->invoke = WM_menu_invoke;
	ot->exec = edbm_separate_exec;
	ot->poll = ED_operator_scene_editable; /* object and editmode */
	
	/* flags */
	ot->flag = OPTYPE_UNDO;
	
	ot->prop = RNA_def_enum(ot->srna, "type", prop_separate_types, 0, "Type", "");
}


static int edbm_fill_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMOperator bmop;
	
	if (!EDBM_op_init(em, &bmop, op, "triangle_fill edges=%he", BM_ELEM_SELECT)) {
		return OPERATOR_CANCELLED;
	}
	
	BMO_op_exec(em->bm, &bmop);
	
	/* select new geometry */
	BMO_slot_buffer_hflag_enable(em->bm, &bmop, "geomout", BM_FACE | BM_EDGE, BM_ELEM_SELECT, TRUE);
	
	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}

	EDBM_update_generic(C, em, TRUE);
	
	return OPERATOR_FINISHED;

}

void MESH_OT_fill(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Fill";
	ot->idname = "MESH_OT_fill";
	ot->description = "Fill a selected edge loop with faces";

	/* api callbacks */
	ot->exec = edbm_fill_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static int edbm_beautify_fill_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);

	if (!EDBM_op_callf(em, op, "beautify_fill faces=%hf", BM_ELEM_SELECT))
		return OPERATOR_CANCELLED;

	EDBM_update_generic(C, em, TRUE);
	
	return OPERATOR_FINISHED;
}

void MESH_OT_beautify_fill(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Beautify Fill";
	ot->idname = "MESH_OT_beautify_fill";
	ot->description = "Rearrange some faces to try to get less degenerated geometry";

	/* api callbacks */
	ot->exec = edbm_beautify_fill_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/********************** Quad/Tri Operators *************************/

static int edbm_quads_convert_to_tris_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	int use_beauty = RNA_boolean_get(op->ptr, "use_beauty");

	if (!EDBM_op_callf(em, op, "triangulate faces=%hf use_beauty=%b", BM_ELEM_SELECT, use_beauty))
		return OPERATOR_CANCELLED;

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_quads_convert_to_tris(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Triangulate Faces";
	ot->idname = "MESH_OT_quads_convert_to_tris";
	ot->description = "Triangulate selected faces";

	/* api callbacks */
	ot->exec = edbm_quads_convert_to_tris_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	RNA_def_boolean(ot->srna, "use_beauty", 1, "Beauty", "Use best triangulation division (currently quads only)");
}

static int edbm_tris_convert_to_quads_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	int dosharp, douvs, dovcols, domaterials;
	float limit = RNA_float_get(op->ptr, "limit");

	dosharp = RNA_boolean_get(op->ptr, "sharp");
	douvs = RNA_boolean_get(op->ptr, "uvs");
	dovcols = RNA_boolean_get(op->ptr, "vcols");
	domaterials = RNA_boolean_get(op->ptr, "materials");

	if (!EDBM_op_callf(em, op,
	                   "join_triangles faces=%hf limit=%f cmp_sharp=%b cmp_uvs=%b cmp_vcols=%b cmp_materials=%b",
	                   BM_ELEM_SELECT, limit, dosharp, douvs, dovcols, domaterials))
	{
		return OPERATOR_CANCELLED;
	}

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

static void join_triangle_props(wmOperatorType *ot)
{
	PropertyRNA *prop;

	prop = RNA_def_float_rotation(ot->srna, "limit", 0, NULL, 0.0f, DEG2RADF(180.0f),
	                              "Max Angle", "Angle Limit", 0.0f, DEG2RADF(180.0f));
	RNA_def_property_float_default(prop, DEG2RADF(40.0f));

	RNA_def_boolean(ot->srna, "uvs", 0, "Compare UVs", "");
	RNA_def_boolean(ot->srna, "vcols", 0, "Compare VCols", "");
	RNA_def_boolean(ot->srna, "sharp", 0, "Compare Sharp", "");
	RNA_def_boolean(ot->srna, "materials", 0, "Compare Materials", "");
}

void MESH_OT_tris_convert_to_quads(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Tris to Quads";
	ot->idname = "MESH_OT_tris_convert_to_quads";
	ot->description = "Join triangles into quads";

	/* api callbacks */
	ot->exec = edbm_tris_convert_to_quads_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	join_triangle_props(ot);
}

static int edbm_dissolve_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);

	int use_verts = RNA_boolean_get(op->ptr, "use_verts");

	if (em->selectmode & SCE_SELECT_FACE) {
		if (!EDBM_op_callf(em, op, "dissolve_faces faces=%hf use_verts=%b", BM_ELEM_SELECT, use_verts))
			return OPERATOR_CANCELLED;
	}
	else if (em->selectmode & SCE_SELECT_EDGE) {
		if (!EDBM_op_callf(em, op, "dissolve_edges edges=%he use_verts=%b", BM_ELEM_SELECT, use_verts))
			return OPERATOR_CANCELLED;
	}
	else if (em->selectmode & SCE_SELECT_VERTEX) {
		if (!EDBM_op_callf(em, op, "dissolve_verts verts=%hv", BM_ELEM_SELECT))
			return OPERATOR_CANCELLED;
	}

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_dissolve(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Dissolve";
	ot->description = "Dissolve geometry";
	ot->idname = "MESH_OT_dissolve";

	/* api callbacks */
	ot->exec = edbm_dissolve_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* TODO, move dissolve into its own operator so this doesnt confuse non-dissolve options */
	RNA_def_boolean(ot->srna, "use_verts", 0, "Dissolve Verts",
	                "When dissolving faces/edges, also dissolve remaining vertices");
}

static int edbm_dissolve_limited_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMesh *bm = em->bm;
	float angle_limit = RNA_float_get(op->ptr, "angle_limit");

	char dissolve_flag;

	if (em->selectmode == SCE_SELECT_FACE) {
		/* flush selection to tags and untag edges/verts with partially selected faces */
		BMIter iter;
		BMIter liter;

		BMElem *ele;
		BMFace *f;
		BMLoop *l;

		BM_ITER_MESH (ele, &iter, bm, BM_VERTS_OF_MESH) {
			BM_elem_flag_set(ele, BM_ELEM_TAG, BM_elem_flag_test(ele, BM_ELEM_SELECT));
		}
		BM_ITER_MESH (ele, &iter, bm, BM_EDGES_OF_MESH) {
			BM_elem_flag_set(ele, BM_ELEM_TAG, BM_elem_flag_test(ele, BM_ELEM_SELECT));
		}

		BM_ITER_MESH (f, &iter, bm, BM_FACES_OF_MESH) {
			if (!BM_elem_flag_test(f, BM_ELEM_SELECT)) {
				BM_ITER_ELEM (l, &liter, f, BM_LOOPS_OF_FACE) {
					BM_elem_flag_disable(l->v, BM_ELEM_TAG);
					BM_elem_flag_disable(l->e, BM_ELEM_TAG);
				}
			}
		}

		dissolve_flag = BM_ELEM_TAG;
	}
	else {
		dissolve_flag = BM_ELEM_SELECT;
	}

	if (!EDBM_op_callf(em, op,
	                   "dissolve_limit edges=%he verts=%hv angle_limit=%f",
	                   dissolve_flag, dissolve_flag, angle_limit))
	{
		return OPERATOR_CANCELLED;
	}

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_dissolve_limited(wmOperatorType *ot)
{
	PropertyRNA *prop;

	/* identifiers */
	ot->name = "Limited Dissolve";
	ot->idname = "MESH_OT_dissolve_limited";
	ot->description = "Dissolve selected edges and verts, limited by the angle of surrounding geometry";

	/* api callbacks */
	ot->exec = edbm_dissolve_limited_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	prop = RNA_def_float_rotation(ot->srna, "angle_limit", 0, NULL, 0.0f, DEG2RADF(180.0f),
	                              "Max Angle", "Angle Limit in Degrees", 0.0f, DEG2RADF(180.0f));
	RNA_def_property_float_default(prop, DEG2RADF(15.0f));
}

static int edbm_split_exec(bContext *C, wmOperator *op)
{
	Object *ob = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(ob);
	BMOperator bmop;

	EDBM_op_init(em, &bmop, op, "split geom=%hvef use_only_faces=%b", BM_ELEM_SELECT, FALSE);
	BMO_op_exec(em->bm, &bmop);
	BM_mesh_elem_hflag_disable_all(em->bm, BM_VERT | BM_EDGE | BM_FACE, BM_ELEM_SELECT, FALSE);
	BMO_slot_buffer_hflag_enable(em->bm, &bmop, "geomout", BM_ALL, BM_ELEM_SELECT, TRUE);
	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}

	/* Geometry has changed, need to recalc normals and looptris */
	EDBM_mesh_normals_update(em);

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_split(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Split";
	ot->idname = "MESH_OT_split";
	ot->description = "Split off selected geometry from connected unselected geometry";

	/* api callbacks */
	ot->exec = edbm_split_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}


static int edbm_spin_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMesh *bm = em->bm;
	BMOperator spinop;
	float cent[3], axis[3], imat[3][3];
	float d[3] = {0.0f, 0.0f, 0.0f};
	int steps, dupli;
	float degr;

	RNA_float_get_array(op->ptr, "center", cent);
	RNA_float_get_array(op->ptr, "axis", axis);
	steps = RNA_int_get(op->ptr, "steps");
	degr = RNA_float_get(op->ptr, "degrees");
	//if (ts->editbutflag & B_CLOCKWISE)
	degr = -degr;
	dupli = RNA_boolean_get(op->ptr, "dupli");

	/* undo object transformation */
	copy_m3_m4(imat, obedit->imat);
	sub_v3_v3(cent, obedit->obmat[3]);
	mul_m3_v3(imat, cent);
	mul_m3_v3(imat, axis);

	if (!EDBM_op_init(em, &spinop, op,
	                  "spin geom=%hvef cent=%v axis=%v dvec=%v steps=%i ang=%f do_dupli=%b",
	                  BM_ELEM_SELECT, cent, axis, d, steps, degr, dupli))
	{
		return OPERATOR_CANCELLED;
	}
	BMO_op_exec(bm, &spinop);
	EDBM_flag_disable_all(em, BM_ELEM_SELECT);
	BMO_slot_buffer_hflag_enable(bm, &spinop, "lastout", BM_ALL, BM_ELEM_SELECT, TRUE);
	if (!EDBM_op_finish(em, &spinop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

/* get center and axis, in global coords */
static int edbm_spin_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	Scene *scene = CTX_data_scene(C);
	View3D *v3d = CTX_wm_view3d(C);
	RegionView3D *rv3d = ED_view3d_context_rv3d(C);

	RNA_float_set_array(op->ptr, "center", give_cursor(scene, v3d));
	RNA_float_set_array(op->ptr, "axis", rv3d->viewinv[2]);

	return edbm_spin_exec(C, op);
}

void MESH_OT_spin(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Spin";
	ot->description = "Extrude selected vertices in a circle around the cursor in indicated viewport";
	ot->idname = "MESH_OT_spin";

	/* api callbacks */
	ot->invoke = edbm_spin_invoke;
	ot->exec = edbm_spin_exec;
	ot->poll = EM_view3d_poll;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* props */
	RNA_def_int(ot->srna, "steps", 9, 0, INT_MAX, "Steps", "Steps", 0, INT_MAX);
	RNA_def_boolean(ot->srna, "dupli", 0, "Dupli", "Make Duplicates");
	RNA_def_float(ot->srna, "degrees", 90.0f, -FLT_MAX, FLT_MAX, "Degrees", "Degrees", -360.0f, 360.0f);

	RNA_def_float_vector(ot->srna, "center", 3, NULL, -FLT_MAX, FLT_MAX, "Center", "Center in global view space", -FLT_MAX, FLT_MAX);
	RNA_def_float_vector(ot->srna, "axis", 3, NULL, -1.0f, 1.0f, "Axis", "Axis in global view space", -FLT_MAX, FLT_MAX);

}

static int edbm_screw_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMesh *bm = em->bm;
	BMEdge *eed;
	BMVert *eve, *v1, *v2;
	BMIter iter, eiter;
	BMOperator spinop;
	float dvec[3], nor[3], cent[3], axis[3];
	float imat[3][3];
	int steps, turns;
	int valence;


	turns = RNA_int_get(op->ptr, "turns");
	steps = RNA_int_get(op->ptr, "steps");
	RNA_float_get_array(op->ptr, "center", cent);
	RNA_float_get_array(op->ptr, "axis", axis);

	/* undo object transformation */
	copy_m3_m4(imat, obedit->imat);
	sub_v3_v3(cent, obedit->obmat[3]);
	mul_m3_v3(imat, cent);
	mul_m3_v3(imat, axis);


	/* find two vertices with valence count == 1, more or less is wrong */
	v1 = NULL;
	v2 = NULL;
	for (eve = BM_iter_new(&iter, em->bm, BM_VERTS_OF_MESH, NULL); eve; eve = BM_iter_step(&iter)) {

		valence = 0;

		for (eed = BM_iter_new(&eiter, em->bm, BM_EDGES_OF_VERT, eve); eed; eed = BM_iter_step(&eiter)) {

			if (BM_elem_flag_test(eed, BM_ELEM_SELECT)) {
				valence++;
			}

		}

		if (valence == 1) {
			if (v1 == NULL) {
				v1 = eve;
			}
			else if (v2 == NULL) {
				v2 = eve;
			}
			else {
				v1 = NULL;
				break;
			}
		}
	}

	if (v1 == NULL || v2 == NULL) {
		BKE_report(op->reports, RPT_ERROR, "You have to select a string of connected vertices too");
		return OPERATOR_CANCELLED;
	}

	/* calculate dvec */
	sub_v3_v3v3(dvec, v1->co, v2->co);
	mul_v3_fl(dvec, 1.0f / steps);

	if (dot_v3v3(nor, dvec) > 0.000f)
		negate_v3(dvec);

	if (!EDBM_op_init(em, &spinop, op,
	                  "spin geom=%hvef cent=%v axis=%v dvec=%v steps=%i ang=%f do_dupli=%b",
	                  BM_ELEM_SELECT, cent, axis, dvec, turns * steps, 360.0f * turns, FALSE))
	{
		return OPERATOR_CANCELLED;
	}
	BMO_op_exec(bm, &spinop);
	EDBM_flag_disable_all(em, BM_ELEM_SELECT);
	BMO_slot_buffer_hflag_enable(bm, &spinop, "lastout", BM_ALL, BM_ELEM_SELECT, TRUE);
	if (!EDBM_op_finish(em, &spinop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

/* get center and axis, in global coords */
static int edbm_screw_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	Scene *scene = CTX_data_scene(C);
	View3D *v3d = CTX_wm_view3d(C);
	RegionView3D *rv3d = ED_view3d_context_rv3d(C);

	RNA_float_set_array(op->ptr, "center", give_cursor(scene, v3d));
	RNA_float_set_array(op->ptr, "axis", rv3d->viewinv[1]);

	return edbm_screw_exec(C, op);
}

void MESH_OT_screw(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Screw";
	ot->description = "Extrude selected vertices in screw-shaped rotation around the cursor in indicated viewport";
	ot->idname = "MESH_OT_screw";

	/* api callbacks */
	ot->invoke = edbm_screw_invoke;
	ot->exec = edbm_screw_exec;
	ot->poll = EM_view3d_poll;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* props */
	RNA_def_int(ot->srna, "steps", 9, 0, INT_MAX, "Steps", "Steps", 0, 256);
	RNA_def_int(ot->srna, "turns", 1, 0, INT_MAX, "Turns", "Turns", 0, 256);

	RNA_def_float_vector(ot->srna, "center", 3, NULL, -FLT_MAX, FLT_MAX,
	                     "Center", "Center in global view space", -FLT_MAX, FLT_MAX);
	RNA_def_float_vector(ot->srna, "axis", 3, NULL, -1.0f, 1.0f,
	                     "Axis", "Axis in global view space", -FLT_MAX, FLT_MAX);
}

static int edbm_select_by_number_vertices_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMFace *efa;
	BMIter iter;
	int numverts = RNA_int_get(op->ptr, "number");
	int type = RNA_enum_get(op->ptr, "type");

	BM_ITER_MESH (efa, &iter, em->bm, BM_FACES_OF_MESH) {

		int select = 0;

		if (type == 0 && efa->len < numverts) {
			select = 1;
		}
		else if (type == 1 && efa->len == numverts) {
			select = 1;
		}
		else if (type == 2 && efa->len > numverts) {
			select = 1;
		}
		else if (type == 3 && efa->len != numverts) {
			select = 1;
		}

		if (select) {
			BM_face_select_set(em->bm, efa, TRUE);
		}
	}

	EDBM_selectmode_flush(em);

	WM_event_add_notifier(C, NC_GEOM | ND_SELECT, obedit->data);
	return OPERATOR_FINISHED;
}

void MESH_OT_select_by_number_vertices(wmOperatorType *ot)
{
	static const EnumPropertyItem type_items[] = {
		{0, "LESS", 0, "Less Than", ""},
		{1, "EQUAL", 0, "Equal To", ""},
		{2, "GREATER", 0, "Greater Than", ""},
		{3, "NOTEQUAL", 0, "Not Equal To", ""},
		{0, NULL, 0, NULL, NULL}
	};

	/* identifiers */
	ot->name = "Select by Number of Vertices";
	ot->description = "Select vertices or faces by vertex count";
	ot->idname = "MESH_OT_select_by_number_vertices";
	
	/* api callbacks */
	ot->exec = edbm_select_by_number_vertices_exec;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	RNA_def_int(ot->srna, "number", 4, 3, INT_MAX, "Number of Vertices", "", 3, INT_MAX);
	RNA_def_enum(ot->srna, "type", type_items, 1, "Type", "Type of comparison to make");
}

static int edbm_select_loose_verts_exec(bContext *C, wmOperator *UNUSED(op))
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMVert *eve;
	BMEdge *eed;
	BMIter iter;

	BM_ITER_MESH (eve, &iter, em->bm, BM_VERTS_OF_MESH) {
		if (!eve->e) {
			BM_vert_select_set(em->bm, eve, TRUE);
		}
	}

	BM_ITER_MESH (eed, &iter, em->bm, BM_EDGES_OF_MESH) {
		if (!eed->l) {
			BM_edge_select_set(em->bm, eed, TRUE);
		}
	}

	EDBM_selectmode_flush(em);

	WM_event_add_notifier(C, NC_GEOM | ND_SELECT, obedit->data);
	return OPERATOR_FINISHED;
}

void MESH_OT_select_loose_verts(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Select Loose Vertices/Edges";
	ot->description = "Select vertices with no edges nor faces, and edges with no faces";
	ot->idname = "MESH_OT_select_loose_verts";

	/* api callbacks */
	ot->exec = edbm_select_loose_verts_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static int edbm_select_mirror_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	int extend = RNA_boolean_get(op->ptr, "extend");

	EDBM_select_mirrored(obedit, em, extend);
	EDBM_selectmode_flush(em);
	WM_event_add_notifier(C, NC_GEOM | ND_SELECT, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_select_mirror(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Select Mirror";
	ot->description = "Select mesh items at mirrored locations";
	ot->idname = "MESH_OT_select_mirror";

	/* api callbacks */
	ot->exec = edbm_select_mirror_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* props */
	RNA_def_boolean(ot->srna, "extend", 0, "Extend", "Extend the existing selection");
}

/******************************************************************************
 * qsort routines.
 * Now unified, for vertices/edges/faces. */

enum {
	SRT_VIEW_ZAXIS = 1,  /* Use view Z (deep) axis. */
	SRT_VIEW_XAXIS,      /* Use view X (left to right) axis. */
	SRT_CURSOR_DISTANCE, /* Use distance from element to 3D cursor. */
	SRT_MATERIAL,        /* Face only: use mat number. */
	SRT_SELECTED,        /* Move selected elements in first, without modifying 
	                      * relative order of selected and unselected elements. */
	SRT_RANDOMIZE,       /* Randomize selected elements. */
	SRT_REVERSE,         /* Reverse current order of selected elements. */
};

typedef struct BMElemSort {
	float srt; /* Sort factor */
	int org_idx; /* Original index of this element _in its mempool_ */
} BMElemSort;

static int bmelemsort_comp(const void *v1, const void *v2)
{
	const BMElemSort *x1 = v1, *x2 = v2;

	return (x1->srt > x2->srt) - (x1->srt < x2->srt);
}

/* Reorders vertices/edges/faces using a given methods. Loops are not supported. */
static void sort_bmelem_flag(Scene *scene, Object *ob,
                             View3D *v3d, RegionView3D *rv3d,
                             const int types, const int flag, const int action,
                             const int reverse, const unsigned int seed)
{
	BMEditMesh *em = BMEdit_FromObject(ob);

	BMVert *ve;
	BMEdge *ed;
	BMFace *fa;
	BMIter iter;

	/* In all five elements below, 0 = vertices, 1 = edges, 2 = faces. */
	/* Just to mark protected elements. */
	char *pblock[3] = {NULL, NULL, NULL}, *pb;
	BMElemSort *sblock[3] = {NULL, NULL, NULL}, *sb;
	int *map[3] = {NULL, NULL, NULL}, *mp;
	int totelem[3] = {0, 0, 0}, tot;
	int affected[3] = {0, 0, 0}, aff;
	int i, j;

	if (!(types && flag && action))
		return;

	if (types & BM_VERT)
		totelem[0] = em->bm->totvert;
	if (types & BM_EDGE)
		totelem[1] = em->bm->totedge;
	if (types & BM_FACE)
		totelem[2] = em->bm->totface;

	if (ELEM(action, SRT_VIEW_ZAXIS, SRT_VIEW_XAXIS)) {
		float mat[4][4];
		float fact = reverse ? -1.0 : 1.0;
		int coidx = (action == SRT_VIEW_ZAXIS) ? 2 : 0;

		mult_m4_m4m4(mat, rv3d->viewmat, ob->obmat);  /* Apply the view matrix to the object matrix. */

		if (totelem[0]) {
			pb = pblock[0] = MEM_callocN(sizeof(char) * totelem[0], "sort_bmelem vert pblock");
			sb = sblock[0] = MEM_callocN(sizeof(BMElemSort) * totelem[0], "sort_bmelem vert sblock");

			BM_ITER_MESH_INDEX (ve, &iter, em->bm, BM_VERTS_OF_MESH, i) {
				if (BM_elem_flag_test(ve, flag)) {
					float co[3];
					mul_v3_m4v3(co, mat, ve->co);

					pb[i] = FALSE;
					sb[affected[0]].org_idx = i;
					sb[affected[0]++].srt = co[coidx] * fact;
				}
				else {
					pb[i] = TRUE;
				}
			}
		}

		if (totelem[1]) {
			pb = pblock[1] = MEM_callocN(sizeof(char) * totelem[1], "sort_bmelem edge pblock");
			sb = sblock[1] = MEM_callocN(sizeof(BMElemSort) * totelem[1], "sort_bmelem edge sblock");

			BM_ITER_MESH_INDEX (ed, &iter, em->bm, BM_EDGES_OF_MESH, i) {
				if (BM_elem_flag_test(ed, flag)) {
					float co[3];
					mid_v3_v3v3(co, ed->v1->co, ed->v2->co);
					mul_m4_v3(mat, co);

					pb[i] = FALSE;
					sb[affected[1]].org_idx = i;
					sb[affected[1]++].srt = co[coidx] * fact;
				}
				else {
					pb[i] = TRUE;
				}
			}
		}

		if (totelem[2]) {
			pb = pblock[2] = MEM_callocN(sizeof(char) * totelem[2], "sort_bmelem face pblock");
			sb = sblock[2] = MEM_callocN(sizeof(BMElemSort) * totelem[2], "sort_bmelem face sblock");

			BM_ITER_MESH_INDEX (fa, &iter, em->bm, BM_FACES_OF_MESH, i) {
				if (BM_elem_flag_test(fa, flag)) {
					float co[3];
					BM_face_calc_center_mean(fa, co);
					mul_m4_v3(mat, co);

					pb[i] = FALSE;
					sb[affected[2]].org_idx = i;
					sb[affected[2]++].srt = co[coidx] * fact;
				}
				else {
					pb[i] = TRUE;
				}
			}
		}
	}

	else if (action == SRT_CURSOR_DISTANCE) {
		float cur[3];
		float mat[4][4];
		float fact = reverse ? -1.0 : 1.0;

		if (v3d && v3d->localvd)
			copy_v3_v3(cur, v3d->cursor);
		else
			copy_v3_v3(cur, scene->cursor);
		invert_m4_m4(mat, ob->obmat);
		mul_m4_v3(mat, cur);

		if (totelem[0]) {
			pb = pblock[0] = MEM_callocN(sizeof(char) * totelem[0], "sort_bmelem vert pblock");
			sb = sblock[0] = MEM_callocN(sizeof(BMElemSort) * totelem[0], "sort_bmelem vert sblock");

			BM_ITER_MESH_INDEX (ve, &iter, em->bm, BM_VERTS_OF_MESH, i) {
				if (BM_elem_flag_test(ve, flag)) {
					pb[i] = FALSE;
					sb[affected[0]].org_idx = i;
					sb[affected[0]++].srt = len_squared_v3v3(cur, ve->co) * fact;
				}
				else {
					pb[i] = TRUE;
				}
			}
		}

		if (totelem[1]) {
			pb = pblock[1] = MEM_callocN(sizeof(char) * totelem[1], "sort_bmelem edge pblock");
			sb = sblock[1] = MEM_callocN(sizeof(BMElemSort) * totelem[1], "sort_bmelem edge sblock");

			BM_ITER_MESH_INDEX (ed, &iter, em->bm, BM_EDGES_OF_MESH, i) {
				if (BM_elem_flag_test(ed, flag)) {
					float co[3];
					mid_v3_v3v3(co, ed->v1->co, ed->v2->co);

					pb[i] = FALSE;
					sb[affected[1]].org_idx = i;
					sb[affected[1]++].srt = len_squared_v3v3(cur, co) * fact;
				}
				else {
					pb[i] = TRUE;
				}
			}
		}

		if (totelem[2]) {
			pb = pblock[2] = MEM_callocN(sizeof(char) * totelem[2], "sort_bmelem face pblock");
			sb = sblock[2] = MEM_callocN(sizeof(BMElemSort) * totelem[2], "sort_bmelem face sblock");

			BM_ITER_MESH_INDEX (fa, &iter, em->bm, BM_FACES_OF_MESH, i) {
				if (BM_elem_flag_test(fa, flag)) {
					float co[3];
					BM_face_calc_center_mean(fa, co);

					pb[i] = FALSE;
					sb[affected[2]].org_idx = i;
					sb[affected[2]++].srt = len_squared_v3v3(cur, co) * fact;
				}
				else {
					pb[i] = TRUE;
				}
			}
		}
	}

	/* Faces only! */
	else if (action == SRT_MATERIAL && totelem[2]) {
		pb = pblock[2] = MEM_callocN(sizeof(char) * totelem[2], "sort_bmelem face pblock");
		sb = sblock[2] = MEM_callocN(sizeof(BMElemSort) * totelem[2], "sort_bmelem face sblock");

		BM_ITER_MESH_INDEX (fa, &iter, em->bm, BM_FACES_OF_MESH, i) {
			if (BM_elem_flag_test(fa, flag)) {
				/* Reverse materials' order, not order of faces inside each mat! */
				/* Note: cannot use totcol, as mat_nr may sometimes be greater... */
				float srt = reverse ? (float)(MAXMAT - fa->mat_nr) : (float)fa->mat_nr;
				pb[i] = FALSE;
				sb[affected[2]].org_idx = i;
				/* Multiplying with totface and adding i ensures us we keep current order for all faces of same mat. */
				sb[affected[2]++].srt = srt * ((float)totelem[2]) + ((float)i);
/*				printf("e: %d; srt: %f; final: %f\n", i, srt, srt * ((float)totface) + ((float)i));*/
			}
			else {
				pb[i] = TRUE;
			}
		}
	}

	else if (action == SRT_SELECTED) {
		int *tbuf[3] = {NULL, NULL, NULL}, *tb;

		if (totelem[0]) {
			tb = tbuf[0] = MEM_callocN(sizeof(int) * totelem[0], "sort_bmelem vert tbuf");
			mp = map[0] = MEM_callocN(sizeof(int) * totelem[0], "sort_bmelem vert map");

			BM_ITER_MESH_INDEX (ve, &iter, em->bm, BM_VERTS_OF_MESH, i) {
				if (BM_elem_flag_test(ve, flag)) {
					mp[affected[0]++] = i;
				}
				else {
					*tb = i;
					tb++;
				}
			}
		}

		if (totelem[1]) {
			tb = tbuf[1] = MEM_callocN(sizeof(int) * totelem[1], "sort_bmelem edge tbuf");
			mp = map[1] = MEM_callocN(sizeof(int) * totelem[1], "sort_bmelem edge map");

			BM_ITER_MESH_INDEX (ed, &iter, em->bm, BM_EDGES_OF_MESH, i) {
				if (BM_elem_flag_test(ed, flag)) {
					mp[affected[1]++] = i;
				}
				else {
					*tb = i;
					tb++;
				}
			}
		}

		if (totelem[2]) {
			tb = tbuf[2] = MEM_callocN(sizeof(int) * totelem[2], "sort_bmelem face tbuf");
			mp = map[2] = MEM_callocN(sizeof(int) * totelem[2], "sort_bmelem face map");

			BM_ITER_MESH_INDEX (fa, &iter, em->bm, BM_FACES_OF_MESH, i) {
				if (BM_elem_flag_test(fa, flag)) {
					mp[affected[2]++] = i;
				}
				else {
					*tb = i;
					tb++;
				}
			}
		}

		for (j = 3; j--; ) {
			int tot = totelem[j];
			int aff = affected[j];
			tb = tbuf[j];
			mp = map[j];
			if (!(tb && mp))
				continue;
			if (ELEM(aff, 0, tot)) {
				MEM_freeN(tb);
				MEM_freeN(mp);
				map[j] = NULL;
				continue;
			}
			if (reverse) {
				memcpy(tb + (tot - aff), mp, aff * sizeof(int));
			}
			else {
				memcpy(mp + aff, tb, (tot - aff) * sizeof(int));
				tb = mp;
				mp = map[j] = tbuf[j];
				tbuf[j] = tb;
			}

			/* Reverse mapping, we want an org2new one! */
			for (i = tot, tb = tbuf[j] + tot - 1; i--; tb--) {
				mp[*tb] = i;
			}
			MEM_freeN(tbuf[j]);
		}
	}

	else if (action == SRT_RANDOMIZE) {
		if (totelem[0]) {
			/* Re-init random generator for each element type, to get consistent random when
			 * enabling/disabling an element type. */
			BLI_srandom(seed);
			pb = pblock[0] = MEM_callocN(sizeof(char) * totelem[0], "sort_bmelem vert pblock");
			sb = sblock[0] = MEM_callocN(sizeof(BMElemSort) * totelem[0], "sort_bmelem vert sblock");

			BM_ITER_MESH_INDEX (ve, &iter, em->bm, BM_VERTS_OF_MESH, i) {
				if (BM_elem_flag_test(ve, flag)) {
					pb[i] = FALSE;
					sb[affected[0]].org_idx = i;
					sb[affected[0]++].srt = BLI_frand();
				}
				else {
					pb[i] = TRUE;
				}
			}
		}

		if (totelem[1]) {
			BLI_srandom(seed);
			pb = pblock[1] = MEM_callocN(sizeof(char) * totelem[1], "sort_bmelem edge pblock");
			sb = sblock[1] = MEM_callocN(sizeof(BMElemSort) * totelem[1], "sort_bmelem edge sblock");

			BM_ITER_MESH_INDEX (ed, &iter, em->bm, BM_EDGES_OF_MESH, i) {
				if (BM_elem_flag_test(ed, flag)) {
					pb[i] = FALSE;
					sb[affected[1]].org_idx = i;
					sb[affected[1]++].srt = BLI_frand();
				}
				else {
					pb[i] = TRUE;
				}
			}
		}

		if (totelem[2]) {
			BLI_srandom(seed);
			pb = pblock[2] = MEM_callocN(sizeof(char) * totelem[2], "sort_bmelem face pblock");
			sb = sblock[2] = MEM_callocN(sizeof(BMElemSort) * totelem[2], "sort_bmelem face sblock");

			BM_ITER_MESH_INDEX (fa, &iter, em->bm, BM_FACES_OF_MESH, i) {
				if (BM_elem_flag_test(fa, flag)) {
					pb[i] = FALSE;
					sb[affected[2]].org_idx = i;
					sb[affected[2]++].srt = BLI_frand();
				}
				else {
					pb[i] = TRUE;
				}
			}
		}
	}

	else if (action == SRT_REVERSE) {
		if (totelem[0]) {
			pb = pblock[0] = MEM_callocN(sizeof(char) * totelem[0], "sort_bmelem vert pblock");
			sb = sblock[0] = MEM_callocN(sizeof(BMElemSort) * totelem[0], "sort_bmelem vert sblock");

			BM_ITER_MESH_INDEX (ve, &iter, em->bm, BM_VERTS_OF_MESH, i) {
				if (BM_elem_flag_test(ve, flag)) {
					pb[i] = FALSE;
					sb[affected[0]].org_idx = i;
					sb[affected[0]++].srt = (float)-i;
				}
				else {
					pb[i] = TRUE;
				}
			}
		}

		if (totelem[1]) {
			pb = pblock[1] = MEM_callocN(sizeof(char) * totelem[1], "sort_bmelem edge pblock");
			sb = sblock[1] = MEM_callocN(sizeof(BMElemSort) * totelem[1], "sort_bmelem edge sblock");

			BM_ITER_MESH_INDEX (ed, &iter, em->bm, BM_EDGES_OF_MESH, i) {
				if (BM_elem_flag_test(ed, flag)) {
					pb[i] = FALSE;
					sb[affected[1]].org_idx = i;
					sb[affected[1]++].srt = (float)-i;
				}
				else {
					pb[i] = TRUE;
				}
			}
		}

		if (totelem[2]) {
			pb = pblock[2] = MEM_callocN(sizeof(char) * totelem[2], "sort_bmelem face pblock");
			sb = sblock[2] = MEM_callocN(sizeof(BMElemSort) * totelem[2], "sort_bmelem face sblock");

			BM_ITER_MESH_INDEX (fa, &iter, em->bm, BM_FACES_OF_MESH, i) {
				if (BM_elem_flag_test(fa, flag)) {
					pb[i] = FALSE;
					sb[affected[2]].org_idx = i;
					sb[affected[2]++].srt = (float)-i;
				}
				else {
					pb[i] = TRUE;
				}
			}
		}
	}

/*	printf("%d vertices: %d to be affected...\n", totelem[0], affected[0]);*/
/*	printf("%d edges: %d to be affected...\n", totelem[1], affected[1]);*/
/*	printf("%d faces: %d to be affected...\n", totelem[2], affected[2]);*/
	if (affected[0] == 0 && affected[1] == 0 && affected[2] == 0) {
		for (j = 3; j--; ) {
			if (pblock[j])
				MEM_freeN(pblock[j]);
			if (sblock[j])
				MEM_freeN(sblock[j]);
			if (map[j])
				MEM_freeN(map[j]);
		}
		return;
	}

	/* Sort affected elements, and populate mapping arrays, if needed. */
	for (j = 3; j--; ) {
		pb = pblock[j];
		sb = sblock[j];
		if (pb && sb && !map[j]) {
			char *p_blk;
			BMElemSort *s_blk;
			tot = totelem[j];
			aff = affected[j];

			qsort(sb, aff, sizeof(BMElemSort), bmelemsort_comp);

			mp = map[j] = MEM_mallocN(sizeof(int) * tot, "sort_bmelem map");
			p_blk = pb + tot - 1;
			s_blk = sb + aff - 1;
			for (i = tot; i--; p_blk--) {
				if (*p_blk) { /* Protected! */
					mp[i] = i;
				}
				else {
					mp[s_blk->org_idx] = i;
					s_blk--;
				}
			}
		}
		if (pb)
			MEM_freeN(pb);
		if (sb)
			MEM_freeN(sb);
	}

	BM_mesh_remap(em->bm, map[0], map[1], map[2]);
/*	DAG_id_tag_update(ob->data, 0);*/

	for (j = 3; j--; ) {
		if (map[j])
			MEM_freeN(map[j]);
	}
}

static int edbm_sort_elements_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *ob = CTX_data_edit_object(C);

	/* may be NULL */
	View3D *v3d = CTX_wm_view3d(C);
	RegionView3D *rv3d = ED_view3d_context_rv3d(C);

	int action = RNA_enum_get(op->ptr, "type");
	PropertyRNA *prop_elem_types = RNA_struct_find_property(op->ptr, "elements");
	int reverse = RNA_boolean_get(op->ptr, "reverse");
	unsigned int seed = RNA_int_get(op->ptr, "seed");
	int elem_types = 0;

	if (ELEM(action, SRT_VIEW_ZAXIS, SRT_VIEW_XAXIS)) {
		if (rv3d == NULL) {
			BKE_report(op->reports, RPT_ERROR, "View not found, can't sort by view axis");
			return OPERATOR_CANCELLED;
		}
	}

	/* If no elem_types set, use current selection mode to set it! */
	if (RNA_property_is_set(op->ptr, prop_elem_types)) {
		elem_types = RNA_property_enum_get(op->ptr, prop_elem_types);
	}
	else {
		BMEditMesh *em = BMEdit_FromObject(ob);
		if (em->selectmode & SCE_SELECT_VERTEX)
			elem_types |= BM_VERT;
		if (em->selectmode & SCE_SELECT_EDGE)
			elem_types |= BM_EDGE;
		if (em->selectmode & SCE_SELECT_FACE)
			elem_types |= BM_FACE;
		RNA_enum_set(op->ptr, "elements", elem_types);
	}

	sort_bmelem_flag(scene, ob, v3d, rv3d,
	                 elem_types, BM_ELEM_SELECT, action, reverse, seed);
	return OPERATOR_FINISHED;
}

static int edbm_sort_elements_draw_check_prop(PointerRNA *ptr, PropertyRNA *prop)
{
	const char *prop_id = RNA_property_identifier(prop);
	int action = RNA_enum_get(ptr, "type");

	/* Only show seed for randomize action! */
	if (strcmp(prop_id, "seed") == 0) {
		if (action == SRT_RANDOMIZE)
			return TRUE;
		else
			return FALSE;
	}

	/* Hide seed for reverse and randomize actions! */
	if (strcmp(prop_id, "reverse") == 0) {
		if (ELEM(action, SRT_RANDOMIZE, SRT_REVERSE))
			return FALSE;
		else
			return TRUE;
	}

	return TRUE;
}

static void edbm_sort_elements_ui(bContext *C, wmOperator *op)
{
	uiLayout *layout = op->layout;
	wmWindowManager *wm = CTX_wm_manager(C);
	PointerRNA ptr;

	RNA_pointer_create(&wm->id, op->type->srna, op->properties, &ptr);

	/* Main auto-draw call. */
	uiDefAutoButsRNA(layout, &ptr, edbm_sort_elements_draw_check_prop, '\0');
}

void MESH_OT_sort_elements(wmOperatorType *ot)
{
	static EnumPropertyItem type_items[] = {
		{SRT_VIEW_ZAXIS, "VIEW_ZAXIS", 0, "View Z Axis",
		                 "Sort selected elements from farthest to nearest one in current view"},
		{SRT_VIEW_XAXIS, "VIEW_XAXIS", 0, "View X Axis",
		                 "Sort selected elements from left to right one in current view"},
		{SRT_CURSOR_DISTANCE, "CURSOR_DISTANCE", 0, "Cursor Distance",
		                      "Sort selected elements from nearest to farthest from 3D cursor"},
		{SRT_MATERIAL, "MATERIAL", 0, "Material",
		               "Sort selected elements from smallest to greatest material index (faces only!)"},
		{SRT_SELECTED, "SELECTED", 0, "Selected",
		               "Move all selected elements in first places, preserving their relative order "
		               "(WARNING: this will affect unselected elements' indices as well!)"},
		{SRT_RANDOMIZE, "RANDOMIZE", 0, "Randomize", "Randomize order of selected elements"},
		{SRT_REVERSE, "REVERSE", 0, "Reverse", "Reverse current order of selected elements"},
		{0, NULL, 0, NULL, NULL},
	};

	static EnumPropertyItem elem_items[] = {
		{BM_VERT, "VERT", 0, "Vertices", ""},
		{BM_EDGE, "EDGE", 0, "Edges", ""},
		{BM_FACE, "FACE", 0, "Faces", ""},
		{0, NULL, 0, NULL, NULL},
	};

	/* identifiers */
	ot->name = "Sort Mesh Elements";
	ot->description = "The order of selected vertices/edges/faces is modified, based on a given method";
	ot->idname = "MESH_OT_sort_elements";

	/* api callbacks */
	ot->invoke = WM_menu_invoke;
	ot->exec = edbm_sort_elements_exec;
	ot->poll = ED_operator_editmesh;
	ot->ui = edbm_sort_elements_ui;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	ot->prop = RNA_def_enum(ot->srna, "type", type_items, 0, "Type", "Type of re-ordering operation to apply");
	RNA_def_enum_flag(ot->srna, "elements", elem_items, 0, "Elements",
	                  "Which elements to affect (vertices, edges and/or faces)");
	RNA_def_boolean(ot->srna, "reverse", FALSE, "Reverse", "Reverse the sorting effect");
	RNA_def_int(ot->srna, "seed", 0, 0, INT_MAX, "Seed", "Seed for random-based operations", 0, 255);
}

/****** end of qsort stuff ****/

static int edbm_noise_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	Material *ma;
	Tex *tex;
	BMVert *eve;
	BMIter iter;
	float fac = RNA_float_get(op->ptr, "factor");

	if (em == NULL) {
		return OPERATOR_FINISHED;
	}

	if ((ma  = give_current_material(obedit, obedit->actcol)) == NULL ||
	    (tex = give_current_material_texture(ma)) == NULL)
	{
		BKE_report(op->reports, RPT_WARNING, "Mesh has no material or texture assigned");
		return OPERATOR_FINISHED;
	}

	if (tex->type == TEX_STUCCI) {
		float b2, vec[3];
		float ofs = tex->turbul / 200.0f;
		BM_ITER_MESH (eve, &iter, em->bm, BM_VERTS_OF_MESH) {
			if (BM_elem_flag_test(eve, BM_ELEM_SELECT)) {
				b2 = BLI_hnoise(tex->noisesize, eve->co[0], eve->co[1], eve->co[2]);
				if (tex->stype) ofs *= (b2 * b2);
				vec[0] = fac * (b2 - BLI_hnoise(tex->noisesize, eve->co[0] + ofs, eve->co[1], eve->co[2]));
				vec[1] = fac * (b2 - BLI_hnoise(tex->noisesize, eve->co[0], eve->co[1] + ofs, eve->co[2]));
				vec[2] = fac * (b2 - BLI_hnoise(tex->noisesize, eve->co[0], eve->co[1], eve->co[2] + ofs));
				
				add_v3_v3(eve->co, vec);
			}
		}
	}
	else {
		BM_ITER_MESH (eve, &iter, em->bm, BM_VERTS_OF_MESH) {
			if (BM_elem_flag_test(eve, BM_ELEM_SELECT)) {
				float tin, dum;
				externtex(ma->mtex[0], eve->co, &tin, &dum, &dum, &dum, &dum, 0);
				eve->co[2] += fac * tin;
			}
		}
	}

	EDBM_mesh_normals_update(em);

	EDBM_update_generic(C, em, TRUE);

	return OPERATOR_FINISHED;
}

void MESH_OT_noise(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Noise";
	ot->description = "Use vertex coordinate as texture coordinate";
	ot->idname = "MESH_OT_noise";

	/* api callbacks */
	ot->exec = edbm_noise_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	RNA_def_float(ot->srna, "factor", 0.1f, -FLT_MAX, FLT_MAX, "Factor", "", 0.0f, 1.0f);
}

typedef struct {
	BMEditMesh *em;
	BMBackup mesh_backup;
	float *weights;
	int li;
	int mcenter[2];
	float initial_length;
	int is_modal;
	NumInput num_input;
	float shift_factor; /* The current factor when shift is pressed. Negative when shift not active. */
} BevelData;

#define HEADER_LENGTH 180

static void edbm_bevel_update_header(wmOperator *op, bContext *C)
{
	static char str[] = "Confirm: Enter/LClick, Cancel: (Esc/RMB), factor: %s, Use Dist (D): %s: Use Even (E): %s";

	char msg[HEADER_LENGTH];
	ScrArea *sa = CTX_wm_area(C);
	BevelData *opdata = op->customdata;

	if (sa) {
		char factor_str[NUM_STR_REP_LEN];
		if (hasNumInput(&opdata->num_input))
			outputNumInput(&opdata->num_input, factor_str);
		else
			BLI_snprintf(factor_str, NUM_STR_REP_LEN, "%f", RNA_float_get(op->ptr, "percent"));
		BLI_snprintf(msg, HEADER_LENGTH, str,
		             factor_str,
		             RNA_boolean_get(op->ptr, "use_dist") ? "On" : "Off",
		             RNA_boolean_get(op->ptr, "use_even") ? "On" : "Off"
		            );

		ED_area_headerprint(sa, msg);
	}
}

static void edbm_bevel_recalc_weights(wmOperator *op)
{
	float df, s, ftot;
	int i;
	int recursion = 1; /* RNA_int_get(op->ptr, "recursion"); */ /* temp removed, see comment below */
	BevelData *opdata = op->customdata;

	if (opdata->weights) {
		/* TODO should change to free only when new recursion is greater than old */
		MEM_freeN(opdata->weights);
	}
	opdata->weights = MEM_mallocN(sizeof(float) * recursion, "bevel weights");

	/* ugh, stupid math depends somewhat on angles!*/
	/* dfac = 1.0/(float)(recursion + 1); */ /* UNUSED */
	df = 1.0;
	for (i = 0, ftot = 0.0f; i < recursion; i++) {
		s = powf(df, 1.25f);

		opdata->weights[i] = s;
		ftot += s;

		df *= 2.0f;
	}

	mul_vn_fl(opdata->weights, recursion, 1.0f / (float)ftot);
}

static int edbm_bevel_init(bContext *C, wmOperator *op, int is_modal)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMIter iter;
	BMEdge *eed;
	BevelData *opdata;
	int li;
	
	if (em == NULL) {
		return 0;
	}

	op->customdata = opdata = MEM_mallocN(sizeof(BevelData), "beveldata_mesh_operator");

	BM_data_layer_add(em->bm, &em->bm->edata, CD_PROP_FLT);
	li = CustomData_number_of_layers(&em->bm->edata, CD_PROP_FLT) - 1;
	
	BM_ITER_MESH (eed, &iter, em->bm, BM_EDGES_OF_MESH) {
		float d = len_v3v3(eed->v1->co, eed->v2->co);
		float *dv = CustomData_bmesh_get_n(&em->bm->edata, eed->head.data, CD_PROP_FLT, li);
		
		*dv = d;
	}
	
	opdata->em = em;
	opdata->li = li;
	opdata->weights = NULL;
	opdata->is_modal = is_modal;
	opdata->shift_factor = -1.0f;

	initNumInput(&opdata->num_input);
	opdata->num_input.flag = NUM_NO_NEGATIVE;

	/* avoid the cost of allocating a bm copy */
	if (is_modal)
		opdata->mesh_backup = EDBM_redo_state_store(em);
	edbm_bevel_recalc_weights(op);

	return 1;
}

static int edbm_bevel_calc(bContext *C, wmOperator *op)
{
	BevelData *opdata = op->customdata;
	BMEditMesh *em = opdata->em;
	BMOperator bmop;
	int i;

	float factor = RNA_float_get(op->ptr, "percent") /*, dfac */ /* UNUSED */;
	int recursion = 1; /* RNA_int_get(op->ptr, "recursion"); */ /* temp removed, see comment below */
	const int use_even = RNA_boolean_get(op->ptr, "use_even");
	const int use_dist = RNA_boolean_get(op->ptr, "use_dist");

	/* revert to original mesh */
	if (opdata->is_modal) {
		EDBM_redo_state_restore(opdata->mesh_backup, em, FALSE);
	}

	for (i = 0; i < recursion; i++) {
		float fac = opdata->weights[recursion - i - 1] * factor;


		if (!EDBM_op_init(em, &bmop, op,
		                  "bevel geom=%hev percent=%f lengthlayer=%i use_lengths=%b use_even=%b use_dist=%b",
		                  BM_ELEM_SELECT, fac, opdata->li, TRUE, use_even, use_dist))
		{
			return 0;
		}
		
		BMO_op_exec(em->bm, &bmop);
		if (!EDBM_op_finish(em, &bmop, op, TRUE))
			return 0;
	}
	
	EDBM_mesh_normals_update(opdata->em);
	
	EDBM_update_generic(C, opdata->em, TRUE);

	return 1;
}

static void edbm_bevel_exit(bContext *C, wmOperator *op)
{
	BevelData *opdata = op->customdata;

	ScrArea *sa = CTX_wm_area(C);

	if (sa) {
		ED_area_headerprint(sa, NULL);
	}
	BM_data_layer_free_n(opdata->em->bm, &opdata->em->bm->edata, CD_PROP_FLT, opdata->li);

	if (opdata->weights)
		MEM_freeN(opdata->weights);
	if (opdata->is_modal) {
		EDBM_redo_state_free(&opdata->mesh_backup, NULL, FALSE);
	}
	MEM_freeN(opdata);
	op->customdata = NULL;
}

static int edbm_bevel_cancel(bContext *C, wmOperator *op)
{
	BevelData *opdata = op->customdata;
	if (opdata->is_modal) {
		EDBM_redo_state_free(&opdata->mesh_backup, opdata->em, TRUE);
		EDBM_update_generic(C, opdata->em, FALSE);
	}

	edbm_bevel_exit(C, op);

	/* need to force redisplay or we may still view the modified result */
	ED_region_tag_redraw(CTX_wm_region(C));
	return OPERATOR_CANCELLED;
}

/* bevel! yay!!*/
static int edbm_bevel_exec(bContext *C, wmOperator *op)
{
	if (!edbm_bevel_init(C, op, FALSE)) {
		edbm_bevel_exit(C, op);
		return OPERATOR_CANCELLED;
	}

	if (!edbm_bevel_calc(C, op)) {
		edbm_bevel_cancel(C, op);
		return OPERATOR_CANCELLED;
	}

	edbm_bevel_exit(C, op);

	return OPERATOR_FINISHED;
}

static int edbm_bevel_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	/* TODO make modal keymap (see fly mode) */
	BevelData *opdata;
	float mlen[2];

	if (!edbm_bevel_init(C, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}

	opdata = op->customdata;

	/* initialize mouse values */
	if (!calculateTransformCenter(C, V3D_CENTROID, NULL, opdata->mcenter)) {
		/* in this case the tool will likely do nothing,
		 * ideally this will never happen and should be checked for above */
		opdata->mcenter[0] = opdata->mcenter[1] = 0;
	}
	mlen[0] = opdata->mcenter[0] - event->mval[0];
	mlen[1] = opdata->mcenter[1] - event->mval[1];
	opdata->initial_length = len_v2(mlen);

	edbm_bevel_update_header(op, C);

	if (!edbm_bevel_calc(C, op)) {
		edbm_bevel_cancel(C, op);
		return OPERATOR_CANCELLED;
	}

	WM_event_add_modal_handler(C, op);

	return OPERATOR_RUNNING_MODAL;
}

static int edbm_bevel_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	BevelData *opdata = op->customdata;

	if (event->val == KM_PRESS) {
		/* Try to handle numeric inputs... */
		float factor;

		if (handleNumInput(&opdata->num_input, event)) {
			applyNumInput(&opdata->num_input, &factor);
			CLAMP(factor, 0.0f, 1.0f);
			RNA_float_set(op->ptr, "percent", factor);

			edbm_bevel_calc(C, op);
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
				float factor;
				float mdiff[2];

				mdiff[0] = opdata->mcenter[0] - event->mval[0];
				mdiff[1] = opdata->mcenter[1] - event->mval[1];

				factor = -len_v2(mdiff) / opdata->initial_length + 1.0f;

				/* Fake shift-transform... */
				if (event->shift) {
					if (opdata->shift_factor < 0.0f)
						opdata->shift_factor = RNA_float_get(op->ptr, "percent");
					factor = (factor - opdata->shift_factor) * 0.1f + opdata->shift_factor;
				}
				else if (opdata->shift_factor >= 0.0f)
					opdata->shift_factor = -1.0f;

				CLAMP(factor, 0.0f, 1.0f);

				RNA_float_set(op->ptr, "percent", factor);

				edbm_bevel_calc(C, op);
				edbm_bevel_update_header(op, C);
			}
			break;

		case LEFTMOUSE:
		case PADENTER:
		case RETKEY:
			edbm_bevel_calc(C, op);
			edbm_bevel_exit(C, op);
			return OPERATOR_FINISHED;

		case EKEY:
			if (event->val == KM_PRESS) {
				int use_even =  RNA_boolean_get(op->ptr, "use_even");
				RNA_boolean_set(op->ptr, "use_even", !use_even);

				edbm_bevel_calc(C, op);
				edbm_bevel_update_header(op, C);
			}
			break;

		case DKEY:
			if (event->val == KM_PRESS) {
				int use_dist =  RNA_boolean_get(op->ptr, "use_dist");
				RNA_boolean_set(op->ptr, "use_dist", !use_dist);

				edbm_bevel_calc(C, op);
				edbm_bevel_update_header(op, C);
			}
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
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	RNA_def_float(ot->srna, "percent", 0.0f, -FLT_MAX, FLT_MAX, "Percentage", "", 0.0f, 1.0f);
	/* XXX, disabled for 2.63 release, needs to work much better without overlap before we can give to users. */
/*	RNA_def_int(ot->srna, "recursion", 1, 1, 50, "Recursion Level", "Recursion Level", 1, 8); */

	RNA_def_boolean(ot->srna, "use_even", FALSE, "Even",     "Calculate evenly spaced bevel");
	RNA_def_boolean(ot->srna, "use_dist", FALSE, "Distance", "Interpret the percent in blender units");

}

static int edbm_bridge_edge_loops_exec(bContext *C, wmOperator *op)
{
	BMOperator bmop;
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	const int use_merge = RNA_boolean_get(op->ptr, "use_merge");
	const float merge_factor = RNA_float_get(op->ptr, "merge_factor");
	
	EDBM_op_init(em, &bmop, op,
	             "bridge_loops edges=%he use_merge=%b merge_factor=%f",
	             BM_ELEM_SELECT, use_merge, merge_factor);

	BMO_op_exec(em->bm, &bmop);

	/* when merge is used the edges are joined and remain selected */
	if (use_merge == FALSE) {
		EDBM_flag_disable_all(em, BM_ELEM_SELECT);
		BMO_slot_buffer_hflag_enable(em->bm, &bmop, "faceout", BM_FACE, BM_ELEM_SELECT, TRUE);
	}

	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;

	}
	else {
		EDBM_update_generic(C, em, TRUE);
		return OPERATOR_FINISHED;
	}
}

void MESH_OT_bridge_edge_loops(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Bridge Two Edge Loops";
	ot->description = "Make faces between two edge loops";
	ot->idname = "MESH_OT_bridge_edge_loops";
	
	/* api callbacks */
	ot->exec = edbm_bridge_edge_loops_exec;
	ot->poll = ED_operator_editmesh;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
	
	RNA_def_boolean(ot->srna, "inside", 0, "Inside", "");

	RNA_def_boolean(ot->srna, "use_merge", FALSE, "Merge", "Merge rather than creating faces");
	RNA_def_float(ot->srna, "merge_factor", 0.5f, 0.0f, 1.0f, "Merge Factor", "", 0.0f, 1.0f);
}

typedef struct {
	float old_thickness;
	float old_depth;
	int mcenter[2];
	int modify_depth;
	int is_modal;
	float initial_length;
	int shift;
	float shift_amount;
	BMBackup backup;
	BMEditMesh *em;
	NumInput num_input;
} InsetData;

static void edbm_inset_update_header(wmOperator *op, bContext *C)
{
	InsetData *opdata = op->customdata;

	static const char str[] = "Confirm: Enter/LClick, "
	                          "Cancel: (Esc/RClick), "
	                          "thickness: %s, "
	                          "depth (Ctrl to tweak): %s (%s), "
	                          "Outset (O): (%s), "
	                          "Boundary (B): (%s)";

	char msg[HEADER_LENGTH];
	ScrArea *sa = CTX_wm_area(C);

	if (sa) {
		char flts_str[NUM_STR_REP_LEN * 2];
		if (hasNumInput(&opdata->num_input))
			outputNumInput(&opdata->num_input, flts_str);
		else {
			BLI_snprintf(flts_str, NUM_STR_REP_LEN, "%f", RNA_float_get(op->ptr, "thickness"));
			BLI_snprintf(flts_str + NUM_STR_REP_LEN, NUM_STR_REP_LEN, "%f", RNA_float_get(op->ptr, "depth"));
		}
		BLI_snprintf(msg, HEADER_LENGTH, str,
		             flts_str,
		             flts_str + NUM_STR_REP_LEN,
		             opdata->modify_depth ? "On" : "Off",
		             RNA_boolean_get(op->ptr, "use_outset") ? "On" : "Off",
		             RNA_boolean_get(op->ptr, "use_boundary") ? "On" : "Off"
		            );

		ED_area_headerprint(sa, msg);
	}
}


static int edbm_inset_init(bContext *C, wmOperator *op, int is_modal)
{
	InsetData *opdata;
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);

	op->customdata = opdata = MEM_mallocN(sizeof(InsetData), "inset_operator_data");

	opdata->old_thickness = 0.01;
	opdata->old_depth = 0.0;
	opdata->modify_depth = FALSE;
	opdata->shift = FALSE;
	opdata->shift_amount = 0.0f;
	opdata->is_modal = is_modal;
	opdata->em = em;

	initNumInput(&opdata->num_input);
	opdata->num_input.idx_max = 1; /* Two elements. */

	if (is_modal)
		opdata->backup = EDBM_redo_state_store(em);

	return 1;
}

static void edbm_inset_exit(bContext *C, wmOperator *op)
{
	InsetData *opdata;
	ScrArea *sa = CTX_wm_area(C);

	opdata = op->customdata;

	if (opdata->is_modal)
		EDBM_redo_state_free(&opdata->backup, NULL, FALSE);

	if (sa) {
		ED_area_headerprint(sa, NULL);
	}
	MEM_freeN(op->customdata);
}

static int edbm_inset_cancel(bContext *C, wmOperator *op)
{
	InsetData *opdata;

	opdata = op->customdata;
	if (opdata->is_modal) {
		EDBM_redo_state_free(&opdata->backup, opdata->em, TRUE);
		EDBM_update_generic(C, opdata->em, FALSE);
	}

	edbm_inset_exit(C, op);

	/* need to force redisplay or we may still view the modified result */
	ED_region_tag_redraw(CTX_wm_region(C));
	return OPERATOR_CANCELLED;
}

static int edbm_inset_calc(bContext *C, wmOperator *op)
{
	InsetData *opdata;
	BMEditMesh *em;
	BMOperator bmop;

	int use_boundary        = RNA_boolean_get(op->ptr, "use_boundary");
	int use_even_offset     = RNA_boolean_get(op->ptr, "use_even_offset");
	int use_relative_offset = RNA_boolean_get(op->ptr, "use_relative_offset");
	float thickness         = RNA_float_get(op->ptr,   "thickness");
	float depth             = RNA_float_get(op->ptr,   "depth");
	int use_outset          = RNA_boolean_get(op->ptr, "use_outset");
	int use_select_inset    = RNA_boolean_get(op->ptr, "use_select_inset"); /* not passed onto the BMO */

	opdata = op->customdata;
	em = opdata->em;

	if (opdata->is_modal) {
		EDBM_redo_state_restore(opdata->backup, em, FALSE);
	}

	EDBM_op_init(em, &bmop, op,
	             "inset faces=%hf use_boundary=%b use_even_offset=%b use_relative_offset=%b "
	             "thickness=%f depth=%f use_outset=%b",
	             BM_ELEM_SELECT, use_boundary, use_even_offset, use_relative_offset,
	             thickness, depth, use_outset);

	BMO_op_exec(em->bm, &bmop);

	if (use_select_inset) {
		/* deselect original faces/verts */
		EDBM_flag_disable_all(em, BM_ELEM_SELECT);
		BMO_slot_buffer_hflag_enable(em->bm, &bmop, "faceout", BM_FACE, BM_ELEM_SELECT, TRUE);
	}
	else {
		BM_mesh_elem_hflag_disable_all(em->bm, BM_VERT | BM_EDGE, BM_ELEM_SELECT, FALSE);
		BMO_slot_buffer_hflag_disable(em->bm, &bmop, "faceout", BM_FACE, BM_ELEM_SELECT, FALSE);
		/* re-select faces so the verts and edges get selected too */
		BM_mesh_elem_hflag_enable_test(em->bm, BM_FACE, BM_ELEM_SELECT, TRUE, BM_ELEM_SELECT);
	}

	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return 0;
	}
	else {
		EDBM_update_generic(C, em, TRUE);
		return 1;
	}
}

static int edbm_inset_exec(bContext *C, wmOperator *op)
{
	edbm_inset_init(C, op, FALSE);

	if (!edbm_inset_calc(C, op)) {
		edbm_inset_exit(C, op);
		return OPERATOR_CANCELLED;
	}

	edbm_inset_exit(C, op);
	return OPERATOR_FINISHED;
}

static int edbm_inset_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	InsetData *opdata;
	float mlen[2];

	edbm_inset_init(C, op, TRUE);

	opdata = op->customdata;

	/* initialize mouse values */
	if (!calculateTransformCenter(C, V3D_CENTROID, NULL, opdata->mcenter)) {
		/* in this case the tool will likely do nothing,
		 * ideally this will never happen and should be checked for above */
		opdata->mcenter[0] = opdata->mcenter[1] = 0;
	}
	mlen[0] = opdata->mcenter[0] - event->mval[0];
	mlen[1] = opdata->mcenter[1] - event->mval[1];
	opdata->initial_length = len_v2(mlen);

	edbm_inset_calc(C, op);

	edbm_inset_update_header(op, C);

	WM_event_add_modal_handler(C, op);
	return OPERATOR_RUNNING_MODAL;
}

static int edbm_inset_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	InsetData *opdata = op->customdata;

	if (event->val == KM_PRESS) {
		/* Try to handle numeric inputs... */
		float amounts[2];

		if (handleNumInput(&opdata->num_input, event)) {
			applyNumInput(&opdata->num_input, amounts);
			amounts[0] = maxf(amounts[0], 0.0f);
			RNA_float_set(op->ptr, "thickness", amounts[0]);
			RNA_float_set(op->ptr, "depth", amounts[1]);

			if (edbm_inset_calc(C, op)) {
				edbm_inset_update_header(op, C);
				return OPERATOR_RUNNING_MODAL;
			}
			else {
				edbm_inset_cancel(C, op);
				return OPERATOR_CANCELLED;
			}
		}
	}

	switch (event->type) {
		case ESCKEY:
		case RIGHTMOUSE:
			edbm_inset_cancel(C, op);
			return OPERATOR_CANCELLED;

		case MOUSEMOVE:
			if (!hasNumInput(&opdata->num_input)) {
				float mdiff[2];
				float amount;

				mdiff[0] = opdata->mcenter[0] - event->mval[0];
				mdiff[1] = opdata->mcenter[1] - event->mval[1];

				if (opdata->modify_depth)
					amount = opdata->old_depth + len_v2(mdiff) / opdata->initial_length - 1.0f;
				else
					amount = opdata->old_thickness - len_v2(mdiff) / opdata->initial_length + 1.0f;

				/* Fake shift-transform... */
				if (opdata->shift)
					amount = (amount - opdata->shift_amount) * 0.1f + opdata->shift_amount;

				if (opdata->modify_depth)
					RNA_float_set(op->ptr, "depth", amount);
				else {
					amount = maxf(amount, 0.0f);
					RNA_float_set(op->ptr, "thickness", amount);
				}

				if (edbm_inset_calc(C, op))
					edbm_inset_update_header(op, C);
				else {
					edbm_inset_cancel(C, op);
					return OPERATOR_CANCELLED;
				}
			}
			break;

		case LEFTMOUSE:
		case PADENTER:
		case RETKEY:
			edbm_inset_calc(C, op);
			edbm_inset_exit(C, op);
			return OPERATOR_FINISHED;

		case LEFTSHIFTKEY:
		case RIGHTSHIFTKEY:
			if (event->val == KM_PRESS) {
				if (opdata->modify_depth)
					opdata->shift_amount = RNA_float_get(op->ptr, "depth");
				else
					opdata->shift_amount = RNA_float_get(op->ptr, "thickness");
				opdata->shift = TRUE;
			}
			else {
				opdata->shift_amount = 0.0f;
				opdata->shift = FALSE;
			}
			break;

		case LEFTCTRLKEY:
		case RIGHTCTRLKEY:
		{
			float mlen[2];

			mlen[0] = opdata->mcenter[0] - event->mval[0];
			mlen[1] = opdata->mcenter[1] - event->mval[1];

			if (event->val == KM_PRESS) {
				opdata->old_thickness = RNA_float_get(op->ptr, "thickness");
				if (opdata->shift)
					opdata->shift_amount = opdata->old_thickness;
				opdata->modify_depth = TRUE;
			}
			else {
				opdata->old_depth = RNA_float_get(op->ptr, "depth");
				if (opdata->shift)
					opdata->shift_amount = opdata->old_depth;
				opdata->modify_depth = FALSE;
			}
			opdata->initial_length = len_v2(mlen);

			edbm_inset_update_header(op, C);
			break;
		}

		case OKEY:
			if (event->val == KM_PRESS) {
				int use_outset = RNA_boolean_get(op->ptr, "use_outset");
				RNA_boolean_set(op->ptr, "use_outset", !use_outset);
				if (edbm_inset_calc(C, op)) {
					edbm_inset_update_header(op, C);
				}
				else {
					edbm_inset_cancel(C, op);
					return OPERATOR_CANCELLED;
				}
			}
			break;
		case BKEY:
			if (event->val == KM_PRESS) {
				int use_boundary = RNA_boolean_get(op->ptr, "use_boundary");
				RNA_boolean_set(op->ptr, "use_boundary", !use_boundary);
				if (edbm_inset_calc(C, op)) {
					edbm_inset_update_header(op, C);
				}
				else {
					edbm_inset_cancel(C, op);
					return OPERATOR_CANCELLED;
				}
			}
			break;
	}

	return OPERATOR_RUNNING_MODAL;
}


void MESH_OT_inset(wmOperatorType *ot)
{
	PropertyRNA *prop;

	/* identifiers */
	ot->name = "Inset Faces";
	ot->idname = "MESH_OT_inset";
	ot->description = "Inset new faces into selected faces";

	/* api callbacks */
	ot->invoke = edbm_inset_invoke;
	ot->modal = edbm_inset_modal;
	ot->exec = edbm_inset_exec;
	ot->cancel = edbm_inset_cancel;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	RNA_def_boolean(ot->srna, "use_boundary",        TRUE, "Boundary",  "Inset face boundaries");
	RNA_def_boolean(ot->srna, "use_even_offset",     TRUE, "Offset Even",      "Scale the offset to give more even thickness");
	RNA_def_boolean(ot->srna, "use_relative_offset", FALSE, "Offset Relative", "Scale the offset by surrounding geometry");

	prop = RNA_def_float(ot->srna, "thickness", 0.01f, 0.0f, FLT_MAX, "Thickness", "", 0.0f, 10.0f);
	/* use 1 rather then 10 for max else dragging the button moves too far */
	RNA_def_property_ui_range(prop, 0.0, 1.0, 0.01, 4);
	prop = RNA_def_float(ot->srna, "depth", 0.0f, -FLT_MAX, FLT_MAX, "Depth", "", -10.0f, 10.0f);
	RNA_def_property_ui_range(prop, -10.0f, 10.0f, 0.01, 4);

	RNA_def_boolean(ot->srna, "use_outset", FALSE, "Outset", "Outset rather than inset");
	RNA_def_boolean(ot->srna, "use_select_inset", TRUE, "Select Outer", "Select the new inset faces");
}

static int edbm_wireframe_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMOperator bmop;
	const int use_boundary        = RNA_boolean_get(op->ptr, "use_boundary");
	const int use_even_offset     = RNA_boolean_get(op->ptr, "use_even_offset");
	const int use_replace         = RNA_boolean_get(op->ptr, "use_replace");
	const int use_relative_offset = RNA_boolean_get(op->ptr, "use_relative_offset");
	const int use_crease          = RNA_boolean_get(op->ptr, "use_crease");
	const float thickness         = RNA_float_get(op->ptr,   "thickness");

	EDBM_op_init(em, &bmop, op,
	             "wireframe faces=%hf use_boundary=%b use_even_offset=%b use_relative_offset=%b use_crease=%b "
	             "thickness=%f",
	             BM_ELEM_SELECT, use_boundary, use_even_offset, use_relative_offset, use_crease,
	             thickness);

	BMO_op_exec(em->bm, &bmop);

	if (use_replace) {
		BM_mesh_elem_hflag_disable_all(em->bm, BM_FACE, BM_ELEM_TAG, FALSE);
		BMO_slot_buffer_hflag_enable(em->bm, &bmop, "faces", BM_FACE, BM_ELEM_TAG, FALSE);

		BMO_op_callf(em->bm, BMO_FLAG_DEFAULTS,
		             "delete geom=%hvef context=%i",
		             BM_ELEM_TAG, DEL_FACES);
	}

	BM_mesh_elem_hflag_disable_all(em->bm, BM_VERT | BM_EDGE | BM_FACE, BM_ELEM_SELECT, FALSE);
	BMO_slot_buffer_hflag_enable(em->bm, &bmop, "faceout", BM_FACE, BM_ELEM_SELECT, TRUE);

	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}
	else {
		EDBM_update_generic(C, em, TRUE);
		return OPERATOR_FINISHED;
	}
}

void MESH_OT_wireframe(wmOperatorType *ot)
{
	PropertyRNA *prop;

	/* identifiers */
	ot->name = "Wire Frame";
	ot->idname = "MESH_OT_wireframe";
	ot->description = "Inset new faces into selected faces";

	/* api callbacks */
	ot->exec = edbm_wireframe_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	RNA_def_boolean(ot->srna, "use_boundary",        TRUE,  "Boundary",        "Inset face boundaries");
	RNA_def_boolean(ot->srna, "use_even_offset",     TRUE,  "Offset Even",     "Scale the offset to give more even thickness");
	RNA_def_boolean(ot->srna, "use_relative_offset", FALSE, "Offset Relative", "Scale the offset by surrounding geometry");
	RNA_def_boolean(ot->srna, "use_crease",          FALSE, "Crease",          "Crease hub edges for improved subsurf");

	prop = RNA_def_float(ot->srna, "thickness", 0.01f, 0.0f, FLT_MAX, "Thickness", "", 0.0f, 10.0f);
	/* use 1 rather then 10 for max else dragging the button moves too far */
	RNA_def_property_ui_range(prop, 0.0, 1.0, 0.01, 4);


	RNA_def_boolean(ot->srna, "use_replace",         TRUE, "Replace", "Remove original faces");
}

static int edbm_convex_hull_exec(bContext *C, wmOperator *op)
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = BMEdit_FromObject(obedit);
	BMOperator bmop;

	EDBM_op_init(em, &bmop, op, "convex_hull input=%hvef "
	             "use_existing_faces=%b",
	             BM_ELEM_SELECT,
	             RNA_boolean_get(op->ptr, "use_existing_faces"));
	BMO_op_exec(em->bm, &bmop);

	/* Hull fails if input is coplanar */
	if (BMO_error_occurred(em->bm)) {
		EDBM_op_finish(em, &bmop, op, TRUE);
		return OPERATOR_CANCELLED;
	}

	
	/* Delete unused vertices, edges, and faces */
	if (RNA_boolean_get(op->ptr, "delete_unused")) {
		if (!EDBM_op_callf(em, op, "delete geom=%s context=%i",
		                   &bmop, "unused_geom", DEL_ONLYTAGGED))
		{
			EDBM_op_finish(em, &bmop, op, TRUE);
			return OPERATOR_CANCELLED;
		}
	}

	/* Delete hole edges/faces */
	if (RNA_boolean_get(op->ptr, "make_holes")) {
		if (!EDBM_op_callf(em, op, "delete geom=%s context=%i",
		                   &bmop, "holes_geom", DEL_ONLYTAGGED))
		{
			EDBM_op_finish(em, &bmop, op, TRUE);
			return OPERATOR_CANCELLED;
		}
	}

	/* Merge adjacent triangles */
	if (RNA_boolean_get(op->ptr, "join_triangles")) {
		if (!EDBM_op_callf(em, op, "join_triangles faces=%s limit=%f",
		                   &bmop, "geomout",
		                   RNA_float_get(op->ptr, "limit")))
		{
			EDBM_op_finish(em, &bmop, op, TRUE);
			return OPERATOR_CANCELLED;
		}
	}

	if (!EDBM_op_finish(em, &bmop, op, TRUE)) {
		return OPERATOR_CANCELLED;
	}
	else {
		EDBM_update_generic(C, em, TRUE);
		EDBM_selectmode_flush(em);
		return OPERATOR_FINISHED;
	}
}

void MESH_OT_convex_hull(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Convex Hull";
	ot->description = "Enclose selected vertices in a convex polyhedron";
	ot->idname = "MESH_OT_convex_hull";

	/* api callbacks */
	ot->exec = edbm_convex_hull_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* props */
	RNA_def_boolean(ot->srna, "delete_unused", TRUE,
	                "Delete Unused",
	                "Delete selected elements that are not used by the hull");

	RNA_def_boolean(ot->srna, "use_existing_faces", TRUE,
	                "Use Existing Faces",
	                "Skip hull triangles that are covered by a pre-existing face");

	RNA_def_boolean(ot->srna, "make_holes", FALSE,
	                "Make Holes",
	                "Delete selected faces that are used by the hull");

	RNA_def_boolean(ot->srna, "join_triangles", TRUE,
	                "Join Triangles",
	                "Merge adjacent triangles into quads");

	join_triangle_props(ot);
}
