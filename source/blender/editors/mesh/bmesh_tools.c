 /* $Id: bmesh_tools.c
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
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
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <math.h>
#include <float.h>

#include "MEM_guardedalloc.h"
#include "PIL_time.h"

#include "BLO_sys_types.h" // for intptr_t support

#include "DNA_mesh_types.h"
#include "DNA_material_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_view3d_types.h"
#include "DNA_key_types.h"

#include "RNA_types.h"
#include "RNA_define.h"
#include "RNA_access.h"

#include "BLI_utildefines.h"
#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_editVert.h"
#include "BLI_rand.h"
#include "BLI_ghash.h"
#include "BLI_linklist.h"
#include "BLI_heap.h"
#include "BLI_array.h"
#include "BLI_smallhash.h"

#include "BKE_material.h"
#include "BKE_context.h"
#include "BKE_customdata.h"
#include "BKE_DerivedMesh.h"
#include "BKE_cdderivedmesh.h"
#include "BKE_depsgraph.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_mesh.h"
#include "BKE_object.h"
#include "BKE_bmesh.h"
#include "BKE_report.h"
#include "BKE_tessmesh.h"
#include "BKE_texture.h"
#include "BKE_main.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_mesh.h"
#include "ED_view3d.h"
#include "ED_util.h"
#include "ED_screen.h"
#include "ED_transform.h"
#include "ED_object.h"

#include "UI_interface.h"

#include "RE_render_ext.h"

#include "mesh_intern.h"
#include "bmesh.h"

#include "editbmesh_bvh.h"

static void add_normal_aligned(float *nor, float *add)
{
	if( INPR(nor, add) < -0.9999f)
		sub_v3_v3v3(nor, nor, add);
	else
		add_v3_v3v3(nor, nor, add);
}


static int subdivide_exec(bContext *C, wmOperator *op)
{
	ToolSettings *ts = CTX_data_tool_settings(C);
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	int cuts= RNA_int_get(op->ptr,"number_cuts");
	float fractal= RNA_float_get(op->ptr, "fractal")/2.5;
	int flag= 0;

	if(fractal != 0.0f)
		flag |= B_FRACTAL;
	
	if (RNA_boolean_get(op->ptr, "quadtri") && 
	    RNA_enum_get(op->ptr, "quadcorner") == SUBD_STRAIGHT_CUT)
	{
		RNA_enum_set(op->ptr, "quadcorner", SUBD_INNERVERT);	
	}
	
	BM_esubdivideflag(obedit, em->bm, BM_SELECT, 
	                  0.0f, fractal, 
	                  ts->editbutflag|flag, 
	                  cuts, 0, RNA_enum_get(op->ptr, "quadcorner"), 
	                  RNA_boolean_get(op->ptr, "quadtri"),
	                  1, RNA_int_get(op->ptr, "seed"));

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

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
	/* identifiers */
	ot->name= "Subdivide";
	ot->description= "Subdivide selected edges.";
	ot->idname= "MESH_OT_subdivide";

	/* api callbacks */
	ot->exec= subdivide_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* properties */
	RNA_def_int(ot->srna, "number_cuts", 1, 1, 50, "Number of Cuts", "", 1, INT_MAX);

	RNA_def_boolean(ot->srna, "quadtri", 0, "Quad/Tri Mode", "Tries to prevent ngons");
	RNA_def_enum(ot->srna, "quadcorner", prop_mesh_cornervert_types, SUBD_STRAIGHT_CUT, "Quad Corner Type", "How to subdivide quad corners (anything other then Straight Cut will prevent ngons)");

	RNA_def_float(ot->srna, "fractal", 0.0, 0.0f, FLT_MAX, "Fractal", "Fractal randomness factor.", 0.0f, 1000.0f);
	RNA_def_int(ot->srna, "seed", 0, 0, 10000, "Random Seed", "Seed for the random number generator", 0, 50);
}


void EMBM_project_snap_verts(bContext *C, ARegion *ar, Object *obedit, BMEditMesh *em)
{
	BMIter iter;
	BMVert *eve;

	BM_ITER(eve, &iter, em->bm, BM_VERTS_OF_MESH, NULL) {
		if (BM_TestHFlag(eve, BM_SELECT)) {
			float mval[2], vec[3], no_dummy[3];
			int dist_dummy;
			mul_v3_m4v3(vec, obedit->obmat, eve->co);
			project_float_noclip(ar, vec, mval);
			if(snapObjectsContext(C, mval, &dist_dummy, vec, no_dummy, SNAP_NOT_OBEDIT)) {
				mul_v3_m4v3(eve->co, obedit->imat, vec);
			}
		}
	}
}


/* individual face extrude */
/* will use vertex normals for extrusion directions, so *nor is unaffected */
static short EDBM_Extrude_face_indiv(BMEditMesh *em, wmOperator *op, short flag, float *UNUSED(nor)) 
{
	BMOIter siter;
	BMIter liter;
	BMFace *f;
	BMLoop *l;
	BMOperator bmop;

	EDBM_InitOpf(em, &bmop, op, "extrude_face_indiv faces=%hf", flag);

	/*deselect original verts*/
	EDBM_clear_flag_all(em, BM_SELECT);

	BMO_Exec_Op(em->bm, &bmop);
	
	BMO_ITER(f, &siter, em->bm, &bmop, "faceout", BM_FACE) {
		BM_Select(em->bm, f, 1);

		/*set face vertex normals to face normal*/
		BM_ITER(l, &liter, em->bm, BM_LOOPS_OF_FACE, f) {
			VECCOPY(l->v->no, f->no);
		}
	}

	if (!EDBM_FinishOp(em, &bmop, op, 1)) return 0;

	return 's'; // s is shrink/fatten
}

#if 0
short EDBM_Extrude_face_indiv(BMEditMesh *em, wmOperator *op, short flag, float *nor) 
	EditVert *eve, *v1, *v2, *v3, *v4;
	EditEdge *eed;
	EditFace *efa, *nextfa;
	
	if(em==NULL) return 0;
	
	/* selected edges with 1 or more selected face become faces */
	/* selected faces each makes new faces */
	/* always remove old faces, keeps volumes manifold */
	/* select the new extrusion, deselect old */
	
	/* step 1; init, count faces in edges */
	recalc_editnormals(em);
	
	for(eve= em->verts.first; eve; eve= eve->next) eve->f1= 0;	// new select flag

	for(eed= em->edges.first; eed; eed= eed->next) {
		eed->f2= 0; // amount of unselected faces
	}
	for(efa= em->faces.first; efa; efa= efa->next) {
		if(efa->f & SELECT);
		else {
			efa->e1->f2++;
			efa->e2->f2++;
			efa->e3->f2++;
			if(efa->e4) efa->e4->f2++;
		}
	}

	/* step 2: make new faces from faces */
	for(efa= em->faces.last; efa; efa= efa->prev) {
		if(efa->f & SELECT) {
			v1= addvertlist(em, efa->v1->co, efa->v1);
			v2= addvertlist(em, efa->v2->co, efa->v2);
			v3= addvertlist(em, efa->v3->co, efa->v3);
			
			v1->f1= v2->f1= v3->f1= 1;
			VECCOPY(v1->no, efa->n);
			VECCOPY(v2->no, efa->n);
			VECCOPY(v3->no, efa->n);
			if(efa->v4) {
				v4= addvertlist(em, efa->v4->co, efa->v4); 
				v4->f1= 1;
				VECCOPY(v4->no, efa->n);
			}
			else v4= NULL;
			
			/* side faces, clockwise */
			addfacelist(em, efa->v2, v2, v1, efa->v1, efa, NULL);
			addfacelist(em, efa->v3, v3, v2, efa->v2, efa, NULL);
			if(efa->v4) {
				addfacelist(em, efa->v4, v4, v3, efa->v3, efa, NULL);
				addfacelist(em, efa->v1, v1, v4, efa->v4, efa, NULL);
			}
			else {
				addfacelist(em, efa->v1, v1, v3, efa->v3, efa, NULL);
			}
			/* top face */
			addfacelist(em, v1, v2, v3, v4, efa, NULL);
		}
	}
	
	/* step 3: remove old faces */
	efa= em->faces.first;
	while(efa) {
		nextfa= efa->next;
		if(efa->f & SELECT) {
			BLI_remlink(&em->faces, efa);
			free_editface(em, efa);
		}
		efa= nextfa;
	}

	/* step 4: redo selection */
	EM_clear_flag_all(em, SELECT);
	
	for(eve= em->verts.first; eve; eve= eve->next) {
		if(eve->f1)  eve->f |= SELECT;
	}
	
	EM_select_flush(em);
	
	return 'n';
}
#endif

/* extrudes individual edges */
static short EDBM_Extrude_edges_indiv(BMEditMesh *em, wmOperator *op, short flag, float *UNUSED(nor)) 
{
	BMOperator bmop;

	EDBM_InitOpf(em, &bmop, op, "extrude_edge_only edges=%he", flag);

	/*deselect original verts*/
	EDBM_clear_flag_all(em, BM_SELECT);

	BMO_Exec_Op(em->bm, &bmop);
	BMO_HeaderFlag_Buffer(em->bm, &bmop, "geomout", BM_SELECT, BM_VERT|BM_EDGE);

	if (!EDBM_FinishOp(em, &bmop, op, 1)) return 0;

	return 'n'; // n is normal grab
}

#if 0
/* nor is filled with constraint vector */
short EDBM_Extrude_edges_indiv(BMEditMesh *em, short flag, float *nor) 
{
	EditVert *eve;
	EditEdge *eed;
	EditFace *efa;
	
	for(eve= em->verts.first; eve; eve= eve->next) eve->tmp.v = NULL;
	for(eed= em->edges.first; eed; eed= eed->next) {
		eed->tmp.f = NULL;
		eed->f2= ((eed->f & flag)!=0);
	}
	
	set_edge_directions_f2(em, 2);

	/* sample for next loop */
	for(efa= em->faces.first; efa; efa= efa->next) {
		efa->e1->tmp.f = efa;
		efa->e2->tmp.f = efa;
		efa->e3->tmp.f = efa;
		if(efa->e4) efa->e4->tmp.f = efa;
	}
	/* make the faces */
	for(eed= em->edges.first; eed; eed= eed->next) {
		if(eed->f & flag) {
			if(eed->v1->tmp.v == NULL)
				eed->v1->tmp.v = addvertlist(em, eed->v1->co, eed->v1);
			if(eed->v2->tmp.v == NULL)
				eed->v2->tmp.v = addvertlist(em, eed->v2->co, eed->v2);

			if(eed->dir==1) 
				addfacelist(em, eed->v1, eed->v2, 
							eed->v2->tmp.v, eed->v1->tmp.v, 
							eed->tmp.f, NULL);
			else 
				addfacelist(em, eed->v2, eed->v1, 
							eed->v1->tmp.v, eed->v2->tmp.v, 
							eed->tmp.f, NULL);

			/* for transform */
			if(eed->tmp.f) {
				efa = eed->tmp.f;
				if (efa->f & SELECT) add_normal_aligned(nor, efa->n);
			}
		}
	}
	normalize_v3(nor);
	
	/* set correct selection */
	EM_clear_flag_all(em, SELECT);
	for(eve= em->verts.last; eve; eve= eve->prev) {
		if(eve->tmp.v) {
			eve->tmp.v->f |= flag;
		}
	}

	for(eed= em->edges.first; eed; eed= eed->next) {
		if(eed->v1->f & eed->v2->f & flag) eed->f |= flag;
	}
	
	if(nor[0]==0.0 && nor[1]==0.0 && nor[2]==0.0) return 'g'; // g is grab
	return 'n';  // n is for normal constraint
}
#endif

/* extrudes individual vertices */
static short EDBM_Extrude_verts_indiv(BMEditMesh *em, wmOperator *op, short flag, float *UNUSED(nor)) 
{
	BMOperator bmop;

	EDBM_InitOpf(em, &bmop, op, "extrude_vert_indiv verts=%hv", flag);

	/*deselect original verts*/
	BMO_UnHeaderFlag_Buffer(em->bm, &bmop, "verts", BM_SELECT, BM_VERT);

	BMO_Exec_Op(em->bm, &bmop);
	BMO_HeaderFlag_Buffer(em->bm, &bmop, "vertout", BM_SELECT, BM_VERT);

	if (!EDBM_FinishOp(em, &bmop, op, 1)) return 0;

	return 'g'; // g is grab
}

static short EDBM_Extrude_edge(Object *obedit, BMEditMesh *em, int flag, float *nor)
{
	BMesh *bm = em->bm;
	BMIter iter;
	BMOIter siter;
	BMOperator extop;
	BMVert *vert;
	BMEdge *edge;
	BMFace *f;
	ModifierData *md;
	BMHeader *el;
	
	BMO_Init_Op(&extop, "extrudefaceregion");
	BMO_HeaderFlag_To_Slot(bm, &extop, "edgefacein",
		               flag, BM_VERT|BM_EDGE|BM_FACE);

	/* If a mirror modifier with clipping is on, we need to adjust some 
	 * of the cases above to handle edges on the line of symmetry.
	 */
	md = obedit->modifiers.first;
	for (; md; md=md->next) {
		if (md->type==eModifierType_Mirror) {
			MirrorModifierData *mmd = (MirrorModifierData*) md;	
		
			if(mmd->flag & MOD_MIR_CLIPPING) {
				float mtx[4][4];
				if (mmd->mirror_ob) {
					float imtx[4][4];
					invert_m4_m4(imtx, mmd->mirror_ob->obmat);
					mul_m4_m4m4(mtx, obedit->obmat, imtx);
				}

				for (edge=BMIter_New(&iter,bm,BM_EDGES_OF_MESH,NULL);
				     edge; edge=BMIter_Step(&iter))
				{
					if(edge->head.flag & flag) {
						float co1[3], co2[3];

						copy_v3_v3(co1, edge->v1->co);
						copy_v3_v3(co2, edge->v2->co);

						if (mmd->mirror_ob) {
							mul_v3_m4v3(co1, mtx, co1);
							mul_v3_m4v3(co2, mtx, co2);
						}

						if (mmd->flag & MOD_MIR_AXIS_X)
							if ( (fabs(co1[0]) < mmd->tolerance) &&
								 (fabs(co2[0]) < mmd->tolerance) )
								BMO_Insert_MapPointer(bm, &extop, "exclude", edge, NULL);

						if (mmd->flag & MOD_MIR_AXIS_Y)
							if ( (fabs(co1[1]) < mmd->tolerance) &&
								 (fabs(co2[1]) < mmd->tolerance) )
								BMO_Insert_MapPointer(bm, &extop, "exclude", edge, NULL);

						if (mmd->flag & MOD_MIR_AXIS_Z)
							if ( (fabs(co1[2]) < mmd->tolerance) &&
								 (fabs(co2[2]) < mmd->tolerance) )
								BMO_Insert_MapPointer(bm, &extop, "exclude", edge, NULL);
					}
				}
			}
		}
	}

	BM_ITER(vert, &iter, bm, BM_VERTS_OF_MESH, NULL) {
		BM_Select(bm, vert, 0);
	}

	BM_ITER(edge, &iter, bm, BM_EDGES_OF_MESH, NULL) {
		BM_Select(bm, edge, 0);
	}

	BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
		BM_Select(bm, f, 0);
	}

	BMO_Exec_Op(bm, &extop);

	nor[0] = nor[1] = nor[2] = 0.0f;
	
	BMO_ITER(el, &siter, bm, &extop, "geomout", BM_ALL) {
		BM_Select(bm, el, 1);

		if (el->type == BM_FACE) {
			f = (BMFace*)el;
			add_normal_aligned(nor, f->no);
		};
	}

	normalize_v3(nor);

	BMO_Finish_Op(bm, &extop);

	if(nor[0]==0.0 && nor[1]==0.0 && nor[2]==0.0) return 'g'; // grab
	return 'n'; // normal constraint 

}
static short EDBM_Extrude_vert(Object *obedit, BMEditMesh *em, short flag, float *nor)
{
		BMIter iter;
		BMEdge *eed;
		
		/*ensure vert flags are consistent for edge selections*/
		eed = BMIter_New(&iter, em->bm, BM_EDGES_OF_MESH, NULL);
		for ( ; eed; eed=BMIter_Step(&iter)) {
			if (BM_TestHFlag(eed, flag)) {
				if (flag != BM_SELECT) {
					BM_SetHFlag(eed->v1, flag);
					BM_SetHFlag(eed->v2, flag);
				} else {
					BM_Select(em->bm, eed->v1, 1);
					BM_Select(em->bm, eed->v2, 1);
				}
			} else {
				if (BM_TestHFlag(eed->v1, flag) && BM_TestHFlag(eed->v2, flag)) {
					if (flag != BM_SELECT)
						BM_SetHFlag(eed, flag);
					else BM_Select(em->bm, eed, 1);
				}
			}
		}

		return EDBM_Extrude_edge(obedit, em, flag, nor);

}

static int extrude_repeat_mesh(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em = ((Mesh *)obedit->data)->edit_btmesh;
	RegionView3D *rv3d = CTX_wm_region_view3d(C);		
		
	int steps = RNA_int_get(op->ptr,"steps");
	
	float offs = RNA_float_get(op->ptr,"offset");
	float dvec[3], tmat[3][3], bmat[3][3], nor[3]= {0.0, 0.0, 0.0};
	short a;

	/* dvec */
	dvec[0]= rv3d->persinv[2][0];
	dvec[1]= rv3d->persinv[2][1];
	dvec[2]= rv3d->persinv[2][2];
	normalize_v3(dvec);
	dvec[0]*= offs;
	dvec[1]*= offs;
	dvec[2]*= offs;

	/* base correction */
	copy_m3_m4(bmat, obedit->obmat);
	invert_m3_m3(tmat, bmat);
	mul_m3_v3(tmat, dvec);

	for(a=0; a<steps; a++) {
		EDBM_Extrude_edge(obedit, em, BM_SELECT, nor);
		//BMO_CallOpf(em->bm, "extrudefaceregion edgefacein=%hef", BM_SELECT);
		BMO_CallOpf(em->bm, "translate vec=%v verts=%hv", (float*)dvec, BM_SELECT);
		//extrudeflag(obedit, em, SELECT, nor);
		//translateflag(em, SELECT, dvec);
	}
	
	EDBM_RecalcNormals(em);

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_extrude_repeat(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Extrude Repeat Mesh";
	ot->description= "Extrude selected vertices, edges or faces repeatedly.";
	ot->idname= "MESH_OT_extrude_repeat";
	
	/* api callbacks */
	ot->exec= extrude_repeat_mesh;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_float(ot->srna, "offset", 2.0f, 0.0f, 100.0f, "Offset", "", 0.0f, FLT_MAX);
	RNA_def_int(ot->srna, "steps", 10, 0, 180, "Steps", "", 0, INT_MAX);
}

/* generic extern called extruder */
static int EDBM_Extrude_Mesh(Scene *scene, Object *obedit, BMEditMesh *em, wmOperator *op, float *norin)
{
	short nr, transmode= 0;
	float stacknor[3] = {0.0f, 0.0f, 0.0f};
	float *nor = norin ? norin : stacknor;

	nor[0] = nor[1] = nor[2] = 0.0f;

	if(em->selectmode & SCE_SELECT_VERTEX) {
		if(em->bm->totvertsel==0) nr= 0;
		else if(em->bm->totvertsel==1) nr= 4;
		else if(em->bm->totedgesel==0) nr= 4;
		else if(em->bm->totfacesel==0) 
			nr= 3; // pupmenu("Extrude %t|Only Edges%x3|Only Vertices%x4");
		else if(em->bm->totfacesel==1)
			nr= 1; // pupmenu("Extrude %t|Region %x1|Only Edges%x3|Only Vertices%x4");
		else 
			nr= 1; // pupmenu("Extrude %t|Region %x1||Individual Faces %x2|Only Edges%x3|Only Vertices%x4");
	}
	else if(em->selectmode & SCE_SELECT_EDGE) {
		if (em->bm->totedgesel==0) nr = 0;
		
		nr = 1;
		/*else if (em->totedgesel==1) nr = 3;
		else if(em->totfacesel==0) nr = 3;
		else if(em->totfacesel==1)
			nr= 1; // pupmenu("Extrude %t|Region %x1|Only Edges%x3");
		else
			nr= 1; // pupmenu("Extrude %t|Region %x1||Individual Faces %x2|Only Edges%x3");
		*/
	}
	else {
		if (em->bm->totfacesel == 0) nr = 0;
		else if (em->bm->totfacesel == 1) nr = 1;
		else
			nr= 1; // pupmenu("Extrude %t|Region %x1||Individual Faces %x2");
	}

	if(nr<1) return 'g';

	if(nr==1 && em->selectmode & SCE_SELECT_VERTEX)	
		transmode= EDBM_Extrude_vert(obedit, em, SELECT, nor);
	else if (nr == 1) transmode= EDBM_Extrude_edge(obedit, em, SELECT, nor);
	else if(nr==4) transmode= EDBM_Extrude_verts_indiv(em, op, SELECT, nor);
	else if(nr==3) transmode= EDBM_Extrude_edges_indiv(em, op, SELECT, nor);
	else transmode= EDBM_Extrude_face_indiv(em, op, SELECT, nor);
	
	if(transmode==0) {
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
		object_handle_update(scene, obedit);

		/* individual faces? */
//		BIF_TransformSetUndo("Extrude");
		if(nr==2) {
//			initTransform(TFM_SHRINKFATTEN, CTX_NO_PET|CTX_NO_MIRROR);
//			Transform();
		}
		else {
//			initTransform(TFM_TRANSLATION, CTX_NO_PET|CTX_NO_MIRROR);
			if(transmode=='n') {
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
static int mesh_extrude_region_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh*)obedit->data)->edit_btmesh;
	
	EDBM_Extrude_Mesh(scene, obedit, em, op, NULL);
	
	WM_event_add_notifier(C, NC_GEOM|ND_SELECT, obedit);
	
	return OPERATOR_FINISHED;	
}

void MESH_OT_extrude_region(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Extrude Region";
	ot->idname= "MESH_OT_extrude_region";
	
	/* api callbacks */
	//ot->invoke= mesh_extrude_region_invoke;
	ot->exec= mesh_extrude_region_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Editing", "");
}

static int mesh_extrude_verts_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh*)obedit->data)->edit_btmesh;
	float nor[3];

	EDBM_Extrude_verts_indiv(em, op, BM_SELECT, nor);
	
	WM_event_add_notifier(C, NC_GEOM|ND_SELECT, obedit);
	
	return OPERATOR_FINISHED;	
}

void MESH_OT_extrude_verts_indiv(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Extrude Only Vertices";
	ot->idname= "MESH_OT_extrude_verts_indiv";
	
	/* api callbacks */
	ot->exec= mesh_extrude_verts_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* to give to transform */
	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Editing", "");
}

static int mesh_extrude_edges_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh*)obedit->data)->edit_btmesh;
	float nor[3];

	EDBM_Extrude_edges_indiv(em, op, BM_SELECT, nor);
	
	WM_event_add_notifier(C, NC_GEOM|ND_SELECT, obedit);
	
	return OPERATOR_FINISHED;	
}

void MESH_OT_extrude_edges_indiv(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Extrude Only Edges";
	ot->idname= "MESH_OT_extrude_edges_indiv";
	
	/* api callbacks */
	ot->exec= mesh_extrude_edges_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* to give to transform */
	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Editing", "");
}

static int mesh_extrude_faces_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh*)obedit->data)->edit_btmesh;
	float nor[3];

	EDBM_Extrude_face_indiv(em, op, BM_SELECT, nor);
	
	WM_event_add_notifier(C, NC_GEOM|ND_SELECT, obedit);
	
	return OPERATOR_FINISHED;	
}

void MESH_OT_extrude_faces_indiv(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Extrude Individual Faces";
	ot->idname= "MESH_OT_extrude_faces_indiv";
	
	/* api callbacks */
	ot->exec= mesh_extrude_faces_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Editing", "");
}

/* ******************** (de)select all operator **************** */

void EDBM_toggle_select_all(BMEditMesh *em) /* exported for UV */
{
	if(em->bm->totvertsel || em->bm->totedgesel || em->bm->totfacesel)
		EDBM_clear_flag_all(em, SELECT);
	else 
		EDBM_set_flag_all(em, SELECT);
}

static int toggle_select_all_exec(bContext *C, wmOperator *UNUSED(op))
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	
	EDBM_toggle_select_all(em);
	
	WM_event_add_notifier(C, NC_GEOM|ND_SELECT, obedit);

	return OPERATOR_FINISHED;
}

void MESH_OT_select_all(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Select/Deselect All";
	ot->idname= "MESH_OT_select_all";
	ot->description= "(de)select all vertices, edges or faces.";
	
	/* api callbacks */
	ot->exec= toggle_select_all_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/* *************** add-click-mesh (extrude) operator ************** */
/* in trunk see: 'editmesh_add.c' */
static int dupli_extrude_cursor(bContext *C, wmOperator *op, wmEvent *event)
{
	ViewContext vc;
	BMVert *v1;
	BMIter iter;
	float min[3], max[3];
	int done= 0;
	short use_proj;
	
	em_setup_viewcontext(C, &vc);
	
	use_proj= (vc.scene->toolsettings->snap_flag & SCE_SNAP) &&	(vc.scene->toolsettings->snap_mode==SCE_SNAP_MODE_FACE);

	INIT_MINMAX(min, max);
	
	BM_ITER(v1, &iter, vc.em->bm, BM_VERTS_OF_MESH, NULL) {
		if (BM_TestHFlag(v1, BM_SELECT)) {
			DO_MINMAX(v1->co, min, max);
			done= 1;
		}
	}

	/* call extrude? */
	if(done) {
		const short rot_src= RNA_boolean_get(op->ptr, "rotate_source");
		BMEdge *eed;
		float vec[3], cent[3], mat[3][3];
		float nor[3]= {0.0, 0.0, 0.0};

		/* 2D normal calc */
		float mval_f[2];

		mval_f[0]= (float)event->mval[0];
		mval_f[1]= (float)event->mval[1];

		/* check for edges that are half selected, use for rotation */
		done= 0;
		BM_ITER(eed, &iter, vc.em->bm, BM_EDGES_OF_MESH, NULL) {
			if (BM_TestHFlag(eed, BM_SELECT)) {
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
				if(line_point_side_v2(co1, co2, mval_f) >= 0.0f) {
					nor[0] +=  (co1[1] - co2[1]);
					nor[1] += -(co1[0] - co2[0]);
				}
				else {
					nor[0] +=  (co2[1] - co1[1]);
					nor[1] += -(co2[0] - co1[0]);
				}
			}
			done= 1;
		}

		if(done) {
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

		mul_m4_v3(vc.obedit->obmat, min);	// view space
		view3d_get_view_aligned_coordinate(&vc, min, event->mval, TRUE);
		mul_m4_v3(vc.obedit->imat, min); // back in object space

		sub_v3_v3(min, cent);
		
		/* calculate rotation */
		unit_m3(mat);
		if(done) {
			float dot;

			copy_v3_v3(vec, min);
			normalize_v3(vec);
			dot= INPR(vec, nor);

			if( fabs(dot)<0.999) {
				float cross[3], si, q1[4];

				cross_v3_v3v3(cross, nor, vec);
				normalize_v3(cross);
				dot= 0.5f*saacos(dot);

				/* halve the rotation if its applied twice */
				if(rot_src) dot *= 0.5f;

				si= (float)sin(dot);
				q1[0]= (float)cos(dot);
				q1[1]= cross[0]*si;
				q1[2]= cross[1]*si;
				q1[3]= cross[2]*si;
				quat_to_mat3( mat,q1);
			}
		}
		
		if(rot_src) {
			EDBM_CallOpf(vc.em, op, "rotate verts=%hv cent=%v mat=%m3",
				BM_SELECT, cent, mat);

			/* also project the source, for retopo workflow */
			if(use_proj)
				EMBM_project_snap_verts(C, vc.ar, vc.obedit, vc.em);
		}

		EDBM_Extrude_edge(vc.obedit, vc.em, SELECT, nor);
		EDBM_CallOpf(vc.em, op, "rotate verts=%hv cent=%v mat=%m3",
			BM_SELECT, cent, mat);
		EDBM_CallOpf(vc.em, op, "translate verts=%hv vec=%v",
			BM_SELECT, min);
	}
	else {
		float *curs= give_cursor(vc.scene, vc.v3d);
		BMOperator bmop;
		BMOIter oiter;
		
		copy_v3_v3(min, curs);
		view3d_get_view_aligned_coordinate(&vc, min, event->mval, 0);

		invert_m4_m4(vc.obedit->imat, vc.obedit->obmat); 
		mul_m4_v3(vc.obedit->imat, min); // back in object space
		
		EDBM_InitOpf(vc.em, &bmop, op, "makevert co=%v", min);
		BMO_Exec_Op(vc.em->bm, &bmop);

		BMO_ITER(v1, &oiter, vc.em->bm, &bmop, "newvertout", BM_VERT) {
			BM_Select(vc.em->bm, v1, 1);
		}

		if (!EDBM_FinishOp(vc.em, &bmop, op, 1))
			return OPERATOR_CANCELLED;
	}

	if(use_proj)
		EMBM_project_snap_verts(C, vc.ar, vc.obedit, vc.em);

	WM_event_add_notifier(C, NC_GEOM|ND_DATA, vc.obedit->data); 
	DAG_id_tag_update(vc.obedit->data, OB_RECALC_DATA);
	
	return OPERATOR_FINISHED;
}

void MESH_OT_dupli_extrude_cursor(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Duplicate or Extrude at 3D Cursor";
	ot->idname= "MESH_OT_dupli_extrude_cursor";
	
	/* api callbacks */
	ot->invoke= dupli_extrude_cursor;
	ot->description= "Duplicate and extrude selected vertices, edges or faces towards the mouse cursor.";
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	RNA_def_boolean(ot->srna, "rotate_source", 1, "Rotate Source", "Rotate initial selection giving better shape");
}

static int delete_mesh(bContext *C, Object *obedit, wmOperator *op, int event, Scene *UNUSED(scene))
{
	BMEditMesh *bem = ((Mesh*)obedit->data)->edit_btmesh;
	
	if(event<1) return OPERATOR_CANCELLED;

	if(event==10 ) {
		//"Erase Vertices";

		if (!EDBM_CallOpf(bem, op, "del geom=%hv context=%i", BM_SELECT, DEL_VERTS))
			return OPERATOR_CANCELLED;
	} 
	else if(event==11) {
		//"Edge Loop"
		if (!EDBM_CallOpf(bem, op, "dissolveedgeloop edges=%he", BM_SELECT))
			return OPERATOR_CANCELLED;
	}
	else if(event==7) {
		//"Dissolve"
		if (bem->selectmode & SCE_SELECT_FACE) {
			if (!EDBM_CallOpf(bem, op, "dissolvefaces faces=%hf",BM_SELECT))
				return OPERATOR_CANCELLED;
		} else if (bem->selectmode & SCE_SELECT_EDGE) {
			if (!EDBM_CallOpf(bem, op, "dissolveedges edges=%he",BM_SELECT))
				return OPERATOR_CANCELLED;
		} else if (bem->selectmode & SCE_SELECT_VERTEX) {
			if (!EDBM_CallOpf(bem, op, "dissolveverts verts=%hv",BM_SELECT))
				return OPERATOR_CANCELLED;
		}
	}
	else if(event==4) {
		//Edges and Faces
		if (!EDBM_CallOpf(bem, op, "del geom=%hef context=%i", BM_SELECT, DEL_EDGESFACES))
			return OPERATOR_CANCELLED;
	} 
	else if(event==1) {
		//"Erase Edges"
		if (!EDBM_CallOpf(bem, op, "del geom=%he context=%i", BM_SELECT, DEL_EDGES))
			return OPERATOR_CANCELLED;
	}
	else if(event==2) {
		//"Erase Faces";
		if (!EDBM_CallOpf(bem, op, "del geom=%hf context=%i", BM_SELECT, DEL_FACES))
			return OPERATOR_CANCELLED;
	}
	else if(event==5) {
		//"Erase Only Faces";
		if (!EDBM_CallOpf(bem, op, "del geom=%hf context=%d",
		                  BM_SELECT, DEL_ONLYFACES))
			return OPERATOR_CANCELLED;
	}
	
	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

/* Note, these values must match delete_mesh() event values */
static EnumPropertyItem prop_mesh_delete_types[] = {
	{7, "DISSOLVE",         0, "Dissolve", ""},
	{12, "COLLAPSE", 0, "Collapse", ""},
	{10,"VERT",		0, "Vertices", ""},
	{1, "EDGE",		0, "Edges", ""},
	{2, "FACE",		0, "Faces", ""},
	{11, "EDGE_LOOP", 0, "Edge Loop", ""},
	{4, "EDGE_FACE", 0, "Edges & Faces", ""},
	{5, "ONLY_FACE", 0, "Only Faces", ""},
	{0, NULL, 0, NULL, NULL}
};

static int delete_mesh_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em = ((Mesh*)obedit->data)->edit_btmesh;
	Scene *scene = CTX_data_scene(C);
	int type = RNA_enum_get(op->ptr, "type");
	
	if (type != 12) {
		delete_mesh(C, obedit, op, type, scene);
	} else {
		if (!EDBM_CallOpf(em, op, "collapse edges=%he", BM_SELECT))
			return OPERATOR_CANCELLED;
	}
		
	
	WM_event_add_notifier(C, NC_GEOM|ND_DATA|ND_SELECT, obedit);
	
	return OPERATOR_FINISHED;
}

void MESH_OT_delete(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Delete";
	ot->description= "Delete selected vertices, edges or faces.";
	ot->idname= "MESH_OT_delete";
	
	/* api callbacks */
	ot->invoke= WM_menu_invoke;
	ot->exec= delete_mesh_exec;
	
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/*props */
	ot->prop = RNA_def_enum(ot->srna, "type", prop_mesh_delete_types, 10, "Type", "Method used for deleting mesh data");
}


static int addedgeface_mesh_exec(bContext *C, wmOperator *op)
{
	BMOperator bmop;
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	
	if (!EDBM_InitOpf(em, &bmop, op, "contextual_create geom=%hfev", BM_SELECT))
		return OPERATOR_CANCELLED;
	
	BMO_Exec_Op(em->bm, &bmop);
	BMO_HeaderFlag_Buffer(em->bm, &bmop, "faceout", BM_SELECT, BM_FACE);

	if (!EDBM_FinishOp(em, &bmop, op, 1))
		return OPERATOR_CANCELLED;

	WM_event_add_notifier(C, NC_GEOM|ND_SELECT, obedit);
	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	
	return OPERATOR_FINISHED;
}

void MESH_OT_edge_face_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Make Edge/Face";
	ot->description= "Add an edge or face to selected.";
	ot->idname= "MESH_OT_edge_face_add";
	
	/* api callbacks */
	ot->exec= addedgeface_mesh_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
}

static EnumPropertyItem prop_mesh_edit_types[] = {
	{1, "VERT", 0, "Vertices", ""},
	{2, "EDGE", 0, "Edges", ""},
	{3, "FACE", 0, "Faces", ""},
	{0, NULL, 0, NULL, NULL}
};

static int mesh_selection_type_exec(bContext *C, wmOperator *op)
{		
	
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	int type = RNA_enum_get(op->ptr,"type");

	switch (type) {
		case 1:
			em->selectmode = SCE_SELECT_VERTEX;
			break;
		case 2:
			em->selectmode = SCE_SELECT_EDGE;
			break;
		case 3:
			em->selectmode = SCE_SELECT_FACE;
			break;
	}

	EDBM_selectmode_set(em);
	CTX_data_tool_settings(C)->selectmode = em->selectmode;

	WM_event_add_notifier(C, NC_GEOM|ND_SELECT, obedit);
	
	return OPERATOR_FINISHED;
}

static void MESH_OT_selection_type(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Selection Mode";
	ot->description= "Set the selection mode type.";
	ot->idname= "MESH_OT_selection_type";
	
	/* api callbacks */
	ot->invoke= WM_menu_invoke;
	ot->exec= mesh_selection_type_exec;
	
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_enum(ot->srna, "type", prop_mesh_edit_types, 0, "Type", "Set the mesh selection type");
	RNA_def_boolean(ot->srna, "inclusive", 0, "Inclusive", "Selects geometry around selected geometry, occording to selection mode");	
}

/* ************************* SEAMS AND EDGES **************** */

static int editbmesh_mark_seam(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	Mesh *me= ((Mesh *)obedit->data);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	BMesh *bm = em->bm;
	BMEdge *eed;
	BMIter iter;
	int clear = RNA_boolean_get(op->ptr, "clear");
	
	/* auto-enable seams drawing */
	if(clear==0) {
		me->drawflag |= ME_DRAWSEAMS;
	}

	if(clear) {
		BM_ITER(eed, &iter, bm, BM_EDGES_OF_MESH, NULL) {
			if (!BM_TestHFlag(eed, BM_SELECT) || BM_TestHFlag(eed, BM_HIDDEN))
				continue;
			
			BM_ClearHFlag(eed, BM_SEAM);
		}
	}
	else {
		BM_ITER(eed, &iter, bm, BM_EDGES_OF_MESH, NULL) {
			if (!BM_TestHFlag(eed, BM_SELECT) || BM_TestHFlag(eed, BM_HIDDEN))
				continue;
			BM_SetHFlag(eed, BM_SEAM);
		}
	}

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_mark_seam(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Mark Seam";
	ot->idname= "MESH_OT_mark_seam";
	ot->description= "(un)mark selected edges as a seam.";
	
	/* api callbacks */
	ot->exec= editbmesh_mark_seam;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	RNA_def_boolean(ot->srna, "clear", 0, "Clear", "");
}

static int editbmesh_mark_sharp(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	Mesh *me= ((Mesh *)obedit->data);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	BMesh *bm = em->bm;
	BMEdge *eed;
	BMIter iter;
	int clear = RNA_boolean_get(op->ptr, "clear");

	/* auto-enable sharp edge drawing */
	if(clear == 0) {
		me->drawflag |= ME_DRAWSHARP;
	}

	if(!clear) {
		BM_ITER(eed, &iter, bm, BM_EDGES_OF_MESH, NULL) {
			if (!BM_TestHFlag(eed, BM_SELECT) || BM_TestHFlag(eed, BM_HIDDEN))
				continue;
			
			BM_SetHFlag(eed, BM_SHARP);
		}
	} else {
		BM_ITER(eed, &iter, bm, BM_EDGES_OF_MESH, NULL) {
			if (!BM_TestHFlag(eed, BM_SELECT) || BM_TestHFlag(eed, BM_HIDDEN))
				continue;
			
			BM_ClearHFlag(eed, BM_SHARP);
		}
	}


	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_mark_sharp(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Mark Sharp";
	ot->idname= "MESH_OT_mark_sharp";
	ot->description= "(un)mark selected edges as sharp.";
	
	/* api callbacks */
	ot->exec= editbmesh_mark_sharp;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	RNA_def_boolean(ot->srna, "clear", 0, "Clear", "");
}


static int editbmesh_vert_connect(bContext *C, wmOperator *UNUSED(op))
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	BMesh *bm = em->bm;
	BMOperator bmop;
	int len = 0;
	
	BMO_InitOpf(bm, &bmop, "connectverts verts=%hv", BM_SELECT);
	BMO_Exec_Op(bm, &bmop);
	len = BMO_GetSlot(&bmop, "edgeout")->len;
	BMO_Finish_Op(bm, &bmop);
	
	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return len ? OPERATOR_FINISHED : OPERATOR_CANCELLED;
}

void MESH_OT_vert_connect(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Vertex Connect";
	ot->idname= "MESH_OT_vert_connect";
	
	/* api callbacks */
	ot->exec= editbmesh_vert_connect;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int editbmesh_edge_split(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	BMesh *bm = em->bm;
	BMOperator bmop;
	int len = 0;
	
	BMO_InitOpf(bm, &bmop, "edgesplit edges=%he numcuts=%d", BM_SELECT, RNA_int_get(op->ptr,"number_cuts"));
	BMO_Exec_Op(bm, &bmop);
	len = BMO_GetSlot(&bmop, "outsplit")->len;
	BMO_Finish_Op(bm, &bmop);
	
	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return len ? OPERATOR_FINISHED : OPERATOR_CANCELLED;
}

void MESH_OT_edge_split(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Edge Split";
	ot->idname= "MESH_OT_edge_split";
	
	/* api callbacks */
	ot->exec= editbmesh_edge_split;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	RNA_def_int(ot->srna, "number_cuts", 1, 1, 10, "Number of Cuts", "", 1, INT_MAX);
}

/****************** add duplicate operator ***************/

static int mesh_duplicate_exec(bContext *C, wmOperator *op)
{
	Object *ob= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh*)ob->data)->edit_btmesh;
	BMOperator bmop;

	EDBM_InitOpf(em, &bmop, op, "dupe geom=%hvef", BM_SELECT);
	
	BMO_Exec_Op(em->bm, &bmop);
	EDBM_clear_flag_all(em, BM_SELECT);

	BMO_HeaderFlag_Buffer(em->bm, &bmop, "newout", BM_SELECT, BM_ALL);

	if (!EDBM_FinishOp(em, &bmop, op, 1))
		return OPERATOR_CANCELLED;

	DAG_id_tag_update(ob->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, ob->data);
	
	return OPERATOR_FINISHED;
}

static int mesh_duplicate_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	WM_cursor_wait(1);
	mesh_duplicate_exec(C, op);
	WM_cursor_wait(0);
	
	return OPERATOR_FINISHED;
}

void MESH_OT_duplicate(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Duplicate";
	ot->description= "Duplicate selected vertices, edges or faces.";
	ot->idname= "MESH_OT_duplicate";
	
	/* api callbacks */
	ot->invoke= mesh_duplicate_invoke;
	ot->exec= mesh_duplicate_exec;
	
	ot->poll= ED_operator_editmesh;
	
	/* to give to transform */
	RNA_def_int(ot->srna, "mode", TFM_TRANSLATION, 0, INT_MAX, "Mode", "", 0, INT_MAX);
}

static int flip_normals(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= (((Mesh *)obedit->data))->edit_btmesh;
	
	if (!EDBM_CallOpf(em, op, "reversefaces faces=%hf", BM_SELECT))
		return OPERATOR_CANCELLED;
	
	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_flip_normals(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Flip Normals";
	ot->description= "Flip the direction of selected face's vertex and face normals";
	ot->idname= "MESH_OT_flip_normals";
	
	/* api callbacks */
	ot->exec= flip_normals;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

float *bm_get_cd_float(CustomData *cdata, void *data, int type)
{
	float *f = CustomData_bmesh_get(cdata, data, type);

	return f;
}

static const EnumPropertyItem direction_items[]= {
	{DIRECTION_CW, "CW", 0, "Clockwise", ""},
	{DIRECTION_CCW, "CCW", 0, "Counter Clockwise", ""},
	{0, NULL, 0, NULL, NULL}};

/* only accepts 1 selected edge, or 2 selected faces */
static int edge_rotate_selected(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	BMOperator bmop;
	BMEdge *eed;
	BMIter iter;
	int ccw = RNA_int_get(op->ptr, "direction") == 1; // direction == 2 when clockwise and ==1 for counter CW.
	
	if (!(em->bm->totfacesel == 2 || em->bm->totedgesel == 1)) {
		BKE_report(op->reports, RPT_ERROR, "Select one edge or two adjacent faces");
		return OPERATOR_CANCELLED;
	}

	/*first see if we have two adjacent faces*/
	BM_ITER(eed, &iter, em->bm, BM_EDGES_OF_MESH, NULL) {
		if (BM_Edge_FaceCount(eed) == 2) {
			if ((BM_TestHFlag(eed->l->f, BM_SELECT) && BM_TestHFlag(((BMLoop*)eed->l->radial_next)->f, BM_SELECT))
				 && !(BM_TestHFlag(eed->l->f, BM_HIDDEN) || BM_TestHFlag(((BMLoop*)eed->l->radial_next)->f, BM_HIDDEN)))
			{
				break;
			}
		}
	}
	
	/*ok, we don't have two adjacent faces, but we do have two selected ones.
	  that's an error condition.*/
	if (!eed && em->bm->totfacesel == 2) {
		BKE_report(op->reports, RPT_ERROR, "Select one edge or two adjacent faces");
		return OPERATOR_CANCELLED;
	}

	if (!eed) {
		BM_ITER(eed, &iter, em->bm, BM_EDGES_OF_MESH, NULL) {
			if (BM_TestHFlag(eed, BM_SELECT) && !BM_TestHFlag(eed, BM_HIDDEN))
				break;
		}
	}

	/*this should never happen*/
	if (!eed)
		return OPERATOR_CANCELLED;
	
	EDBM_InitOpf(em, &bmop, op, "edgerotate edges=%e ccw=%d", eed, ccw);
	BMO_Exec_Op(em->bm, &bmop);

	BMO_HeaderFlag_Buffer(em->bm, &bmop, "edgeout", BM_SELECT, BM_EDGE);

	if (!EDBM_FinishOp(em, &bmop, op, 1))
		return OPERATOR_CANCELLED;

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_edge_rotate(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Rotate Selected Edge";
	ot->description= "Rotate selected edge or adjoining faces.";
	ot->idname= "MESH_OT_edge_rotate";

	/* api callbacks */
	ot->exec= edge_rotate_selected;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* props */
	RNA_def_enum(ot->srna, "direction", direction_items, DIRECTION_CW, "direction", "direction to rotate edge around.");
}

/* swap is 0 or 1, if 1 it hides not selected */
void EDBM_hide_mesh(BMEditMesh *em, int swap)
{
	BMIter iter;
	BMHeader *h;
	int itermode;

	if(em==NULL) return;
	
	if (em->selectmode & SCE_SELECT_VERTEX)
		itermode = BM_VERTS_OF_MESH;
	else if (em->selectmode & SCE_SELECT_EDGE)
		itermode = BM_EDGES_OF_MESH;
	else
		itermode = BM_FACES_OF_MESH;

	BM_ITER(h, &iter, em->bm, itermode, NULL) {
		if (BM_TestHFlag(h, BM_SELECT) ^ swap)
			BM_Hide(em->bm, h, 1);
	}

	/*original hide flushing comment (OUTDATED): 
	  hide happens on least dominant select mode, and flushes up, not down! (helps preventing errors in subsurf) */
	/*  - vertex hidden, always means edge is hidden too
		- edge hidden, always means face is hidden too
		- face hidden, only set face hide
		- then only flush back down what's absolute hidden
	*/

}

static int hide_mesh_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= (((Mesh *)obedit->data))->edit_btmesh;
	
	EDBM_hide_mesh(em, RNA_boolean_get(op->ptr, "unselected"));
		
	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;	
}

void MESH_OT_hide(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Hide Selection";
	ot->idname= "MESH_OT_hide";
	
	/* api callbacks */
	ot->exec= hide_mesh_exec;
	ot->poll= ED_operator_editmesh;
	 ot->description= "Hide (un)selected vertices, edges or faces.";

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_boolean(ot->srna, "unselected", 0, "Unselected", "Hide unselected rather than selected.");
}


void EDBM_reveal_mesh(BMEditMesh *em)
{
	BMIter iter;
	BMHeader *ele;
	int i, types[3] = {BM_VERTS_OF_MESH, BM_EDGES_OF_MESH, BM_FACES_OF_MESH};
	int sels[3] = {1, !(em->selectmode & SCE_SELECT_VERTEX), !(em->selectmode & (SCE_SELECT_VERTEX | SCE_SELECT_EDGE))};

	for (i=0; i<3; i++) {
		BM_ITER(ele, &iter, em->bm, types[i], NULL) {
			if (BM_TestHFlag(ele, BM_HIDDEN)) {
				BM_Hide(em->bm, ele, 0);

				if (sels[i])
					BM_Select(em->bm, ele, 1);
			}
		}
	}

	EDBM_selectmode_flush(em);
}

static int reveal_mesh_exec(bContext *C, wmOperator *UNUSED(op))
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= (((Mesh *)obedit->data))->edit_btmesh;
	
	EDBM_reveal_mesh(em);

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;	
}

void MESH_OT_reveal(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Reveal Hidden";
	ot->idname= "MESH_OT_reveal";
	ot->description= "Reveal all hidden vertices, edges and faces.";
	
	/* api callbacks */
	ot->exec= reveal_mesh_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int normals_make_consistent_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	
	/*doflip has to do with bmesh_rationalize_normals, it's an internal
	thing*/
	if (!EDBM_CallOpf(em, op, "righthandfaces faces=%hf doflip=%d", BM_SELECT, 1))
		return OPERATOR_CANCELLED;
	
	if (RNA_boolean_get(op->ptr, "inside"))
		EDBM_CallOpf(em, op, "reversefaces faces=%hf doflip=%d", BM_SELECT, 1);

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;	
}

void MESH_OT_normals_make_consistent(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Make Normals Consistent";
	ot->description= "Make face and vertex normals point either outside or inside the mesh";
	ot->idname= "MESH_OT_normals_make_consistent";
	
	/* api callbacks */
	ot->exec= normals_make_consistent_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	RNA_def_boolean(ot->srna, "inside", 0, "Inside", "");
}



static int do_smooth_vertex(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	ModifierData *md;
	int mirrx=0, mirry=0, mirrz=0;
	int i, repeat;

	/* if there is a mirror modifier with clipping, flag the verts that
	 * are within tolerance of the plane(s) of reflection 
	 */
	for(md=obedit->modifiers.first; md; md=md->next) {
		if(md->type==eModifierType_Mirror) {
			MirrorModifierData *mmd = (MirrorModifierData*) md;	
		
			if(mmd->flag & MOD_MIR_CLIPPING) {
				if (mmd->flag & MOD_MIR_AXIS_X)
					mirrx = 1;
				if (mmd->flag & MOD_MIR_AXIS_Y)
					mirry = 1;
				if (mmd->flag & MOD_MIR_AXIS_Z)
					mirrz = 1;
			}
		}
	}

	repeat = RNA_int_get(op->ptr,"repeat");
	if (!repeat)
		repeat = 1;
	
	for (i=0; i<repeat; i++) {
		if (!EDBM_CallOpf(em, op, "vertexsmooth verts=%hv mirror_clip_x=%d mirror_clip_y=%d mirror_clip_z=%d",
				  BM_SELECT, mirrx, mirry, mirrz))
		{
			return OPERATOR_CANCELLED;
		}
	}

	//BMESH_TODO: need to handle the x-axis editing option here properly.
	//should probably make a helper function for that? I dunno.

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}	
	
void MESH_OT_vertices_smooth(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Smooth Vertex";
	ot->description= "Flatten angles of selected vertices.";
	ot->idname= "MESH_OT_vertices_smooth";
	
	/* api callbacks */
	ot->exec= do_smooth_vertex;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	RNA_def_int(ot->srna, "repeat", 1, 1, 100, "Number of times to smooth the mesh", "", 1, INT_MAX);
}


static int bm_test_exec(bContext *C, wmOperator *UNUSED(op))
{
	Object *obedit= CTX_data_edit_object(C);
	ARegion *ar = CTX_wm_region(C);
	View3D *v3d = CTX_wm_view3d(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	BMBVHTree *tree = BMBVH_NewBVH(em);
	BMIter iter;
	BMEdge *e;

	/*hide all back edges*/
	BM_ITER(e, &iter, em->bm, BM_EDGES_OF_MESH, NULL) {
		if (!BM_TestHFlag(e, BM_SELECT))
			continue;

		if (!BMBVH_EdgeVisible(tree, e, ar, v3d, obedit))
			BM_Select(em->bm, e, 0);
	}

	BMBVH_FreeBVH(tree);
	
#if 0 //uv island walker test
	BMIter iter, liter;
	BMFace *f;
	BMLoop *l, *l2;
	MLoopUV *luv;
	BMWalker walker;
	int i=0;

	BM_ITER(f, &iter, em->bm, BM_FACES_OF_MESH, NULL) {
		BM_ITER(l, &liter, em->bm, BM_LOOPS_OF_FACE, f) {
			luv = CustomData_bmesh_get(&em->bm->ldata, l->head.data, CD_MLOOPUV);
		}
	}

	BMW_Init(&walker, em->bm, BMW_UVISLAND, 0);

	BM_ITER(f, &iter, em->bm, BM_FACES_OF_MESH, NULL) {
		BM_ITER(l, &liter, em->bm, BM_LOOPS_OF_FACE, f) {
			luv = CustomData_bmesh_get(&em->bm->ldata, l->head.data, CD_MLOOPUV);
			if (luv->flag & MLOOPUV_VERTSEL) {
				l2 = BMW_Begin(&walker, l);
				for (; l2; l2=BMW_Step(&walker)) {
					luv = CustomData_bmesh_get(&em->bm->ldata, l2->head.data, CD_MLOOPUV);
					luv->flag |= MLOOPUV_VERTSEL;
				}				
			}
		}
	}

	BMW_End(&walker);
#endif
	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}	
	
void MESH_OT_bm_test(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "BMesh Test Operator";
	ot->idname= "MESH_OT_bm_test";
	
	/* api callbacks */
	ot->exec= bm_test_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	//RNA_def_int(ot->srna, "repeat", 1, 1, 100, "Number of times to smooth the mesh", "", 1, INT_MAX);
}

/********************** Smooth/Solid Operators *************************/

static void mesh_set_smooth_faces(BMEditMesh *em, short smooth)
{
	BMIter iter;
	BMFace *efa;

	if(em==NULL) return;
	
	BM_ITER(efa, &iter, em->bm, BM_FACES_OF_MESH, NULL) {
		if (BM_TestHFlag(efa, BM_SELECT)) {
			if (smooth)
				BM_SetHFlag(efa, BM_SMOOTH);
			else
				BM_ClearHFlag(efa, BM_SMOOTH);
		}
	}
}

static int mesh_faces_shade_smooth_exec(bContext *C, wmOperator *UNUSED(op))
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;

	mesh_set_smooth_faces(em, 1);

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_faces_shade_smooth(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Shade Smooth";
	 ot->description= "Display faces smooth (using vertex normals).";
	ot->idname= "MESH_OT_faces_shade_smooth";

	/* api callbacks */
	ot->exec= mesh_faces_shade_smooth_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int mesh_faces_shade_flat_exec(bContext *C, wmOperator *UNUSED(op))
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;

	mesh_set_smooth_faces(em, 0);

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_faces_shade_flat(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Shade Flat";
	ot->description= "Display faces flat.";
	ot->idname= "MESH_OT_faces_shade_flat";

	/* api callbacks */
	ot->exec= mesh_faces_shade_flat_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}


/********************** UV/Color Operators *************************/


static const EnumPropertyItem axis_items[]= {
	{OPUVC_AXIS_X, "X", 0, "X", ""},
	{OPUVC_AXIS_Y, "Y", 0, "Y", ""},
	{0, NULL, 0, NULL, NULL}};

static int mesh_rotate_uvs(bContext *C, wmOperator *op)
{
	Object *ob = CTX_data_edit_object(C);
	BMEditMesh *em = ((Mesh*)ob->data)->edit_btmesh;
	BMOperator bmop;

	/* get the direction from RNA */
	int dir = RNA_enum_get(op->ptr, "direction");

	/* initialize the bmop using EDBM api, which does various ui error reporting and other stuff */
	EDBM_InitOpf(em, &bmop, op, "meshrotateuvs faces=%hf dir=%d", BM_SELECT, dir);

	/* execute the operator */
	BMO_Exec_Op(em->bm, &bmop);

	/* finish the operator */
	if( !EDBM_FinishOp(em, &bmop, op, 1) )
		return OPERATOR_CANCELLED;


	/* dependencies graph and notification stuff */
	DAG_id_tag_update(ob->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, ob->data);
/*	DAG_id_tag_update(ob->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, ob->data);
*/
	/* we succeeded */
	return OPERATOR_FINISHED;
}

static int mesh_reverse_uvs(bContext *C, wmOperator *op)
{
	Object *ob = CTX_data_edit_object(C);
	BMEditMesh *em = ((Mesh*)ob->data)->edit_btmesh;
	BMOperator bmop;

	/* initialize the bmop using EDBM api, which does various ui error reporting and other stuff */
	EDBM_InitOpf(em, &bmop, op, "meshreverseuvs faces=%hf", BM_SELECT);

	/* execute the operator */
	BMO_Exec_Op(em->bm, &bmop);

	/* finish the operator */
	if( !EDBM_FinishOp(em, &bmop, op, 1) )
		return OPERATOR_CANCELLED;

	/* dependencies graph and notification stuff */
	DAG_id_tag_update(ob->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, ob->data);
/*	DAG_id_tag_update(ob->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, ob->data);
*/
	/* we succeeded */
	return OPERATOR_FINISHED;
}

static int mesh_rotate_colors(bContext *C, wmOperator *op)
{
	Object *ob = CTX_data_edit_object(C);
	BMEditMesh *em = ((Mesh*)ob->data)->edit_btmesh;
	BMOperator bmop;

	/* get the direction from RNA */
	int dir = RNA_enum_get(op->ptr, "direction");

	/* initialize the bmop using EDBM api, which does various ui error reporting and other stuff */
	EDBM_InitOpf(em, &bmop, op, "meshrotatecolors faces=%hf dir=%d", BM_SELECT, dir);

	/* execute the operator */
	BMO_Exec_Op(em->bm, &bmop);

	/* finish the operator */
	if( !EDBM_FinishOp(em, &bmop, op, 1) )
		return OPERATOR_CANCELLED;


	/* dependencies graph and notification stuff */
	DAG_id_tag_update(ob->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, ob->data);
/*	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT | ND_GEOM_SELECT, ob);
*/
	/* we succeeded */
	return OPERATOR_FINISHED;
}


static int mesh_reverse_colors(bContext *C, wmOperator *op)
{
	Object *ob = CTX_data_edit_object(C);
	BMEditMesh *em = ((Mesh*)ob->data)->edit_btmesh;
	BMOperator bmop;

	/* initialize the bmop using EDBM api, which does various ui error reporting and other stuff */
	EDBM_InitOpf(em, &bmop, op, "meshreversecolors faces=%hf", BM_SELECT);

	/* execute the operator */
	BMO_Exec_Op(em->bm, &bmop);

	/* finish the operator */
	if( !EDBM_FinishOp(em, &bmop, op, 1) )
		return OPERATOR_CANCELLED;

	DAG_id_tag_update(ob->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, ob->data);

	/* we succeeded */
	return OPERATOR_FINISHED;
#if 0
	Scene *scene= CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	EditMesh *em= BKE_mesh_get_editmesh((Mesh *)obedit->data);

	EditFace *efa;
	short change = 0;
	MCol tmpcol, *mcol;
	int axis= RNA_enum_get(op->ptr, "axis");

	if (!EM_vertColorCheck(em)) {
		BKE_report(op->reports, RPT_ERROR, "Mesh has no color layers");
		BKE_mesh_end_editmesh(obedit->data, em);
		return OPERATOR_CANCELLED;
	}

	for(efa=em->faces.first; efa; efa=efa->next) {
		if (efa->f & SELECT) {
			mcol = CustomData_em_get(&em->fdata, efa->data, CD_MCOL);
			if (axis == AXIS_Y) {
				tmpcol= mcol[1];
				mcol[1]= mcol[2];
				mcol[2]= tmpcol;

				if(efa->v4) {
					tmpcol= mcol[0];
					mcol[0]= mcol[3];
					mcol[3]= tmpcol;
				}
			} else {
				tmpcol= mcol[0];
				mcol[0]= mcol[1];
				mcol[1]= tmpcol;

				if(efa->v4) {
					tmpcol= mcol[2];
					mcol[2]= mcol[3];
					mcol[3]= tmpcol;
				}
			}
			change = 1;
		}
	}

	BKE_mesh_end_editmesh(obedit->data, em);

	if(!change)
		return OPERATOR_CANCELLED;

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

#endif
	return OPERATOR_FINISHED;
}

void MESH_OT_uvs_rotate(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Rotate UVs";
	ot->idname= "MESH_OT_uvs_rotate";

	/* api callbacks */
	ot->exec= mesh_rotate_uvs;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* props */
	RNA_def_enum(ot->srna, "direction", direction_items, DIRECTION_CW, "Direction", "Direction to rotate UVs around.");
}

//void MESH_OT_uvs_mirror(wmOperatorType *ot)
void MESH_OT_uvs_reverse(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Reverse UVs";
	ot->idname= "MESH_OT_uvs_reverse";

	/* api callbacks */
	ot->exec= mesh_reverse_uvs;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* props */
	//RNA_def_enum(ot->srna, "axis", axis_items, DIRECTION_CW, "Axis", "Axis to mirror UVs around.");
}

void MESH_OT_colors_rotate(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Rotate Colors";
	ot->idname= "MESH_OT_colors_rotate";

	/* api callbacks */
	ot->exec= mesh_rotate_colors;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* props */
	RNA_def_enum(ot->srna, "direction", direction_items, DIRECTION_CW, "Direction", "Direction to rotate edge around.");
}

void MESH_OT_colors_reverse(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Reverse Colors";
	ot->idname= "MESH_OT_colors_reverse";

	/* api callbacks */
	ot->exec= mesh_reverse_colors;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* props */
	//RNA_def_enum(ot->srna, "axis", axis_items, DIRECTION_CW, "Axis", "Axis to mirror colors around.");
}


static int merge_firstlast(BMEditMesh *em, int first, int uvmerge, wmOperator *wmop)
{
	BMVert *mergevert;
	BMEditSelection *ese;

	/* do sanity check in mergemenu in edit.c ?*/
	if(first == 0){
		ese = em->bm->selected.last;
		mergevert= (BMVert*)ese->data;
	}
	else{
		ese = em->bm->selected.first;
		mergevert = (BMVert*)ese->data;
	}

	if (!BM_TestHFlag(mergevert, BM_SELECT))
		return OPERATOR_CANCELLED;
	
	if (uvmerge) {
		if (!EDBM_CallOpf(em, wmop, "pointmerge_facedata verts=%hv snapv=%e", BM_SELECT, mergevert))
			return OPERATOR_CANCELLED;
	}

	if (!EDBM_CallOpf(em, wmop, "pointmerge verts=%hv mergeco=%v", BM_SELECT, mergevert->co))
		return OPERATOR_CANCELLED;

	return OPERATOR_FINISHED;
}

static int merge_target(BMEditMesh *em, Scene *scene, View3D *v3d, Object *ob, 
                        int target, int uvmerge, wmOperator *wmop)
{
	BMIter iter;
	BMVert *v;
	float *vco=NULL, co[3], cent[3] = {0.0f, 0.0f, 0.0f}, fac;
	int i;

	if (target) {
		vco = give_cursor(scene, v3d);
		VECCOPY(co, vco);
		mul_m4_v3(ob->imat, co);
	} else {
		i = 0;
		BM_ITER(v, &iter, em->bm, BM_VERTS_OF_MESH, NULL) {
			if (!BM_TestHFlag(v, BM_SELECT))
				continue;
			VECADD(cent, cent, v->co);
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
		if (!EDBM_CallOpf(em, wmop, "vert_average_facedata verts=%hv", BM_SELECT))
			return OPERATOR_CANCELLED;
	}

	if (!EDBM_CallOpf(em, wmop, "pointmerge verts=%hv mergeco=%v", BM_SELECT, co))
		return OPERATOR_CANCELLED;

	return OPERATOR_FINISHED;
}

static int merge_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	View3D *v3d = CTX_wm_view3d(C);
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	int status= 0, uvs= RNA_boolean_get(op->ptr, "uvs");

	switch(RNA_enum_get(op->ptr, "type")) {
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
			if (!EDBM_CallOpf(em, op, "collapse edges=%he", BM_SELECT))
				status = 0;
			break;
	}

	if(!status)
		return OPERATOR_CANCELLED;

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

static EnumPropertyItem merge_type_items[]= {
	{6, "FIRST", 0, "At First", ""},
	{1, "LAST", 0, "At Last", ""},
	{3, "CENTER", 0, "At Center", ""},
	{4, "CURSOR", 0, "At Cursor", ""},
	{5, "COLLAPSE", 0, "Collapse", ""},
	{0, NULL, 0, NULL, NULL}};

static EnumPropertyItem *merge_type_itemf(bContext *C, PointerRNA *UNUSED(ptr),  PropertyRNA *UNUSED(prop), int *free)
{	
	Object *obedit;
	EnumPropertyItem *item= NULL;
	int totitem= 0;
	
	if(!C) /* needed for docs */
		return merge_type_items;
	
	obedit= CTX_data_edit_object(C);
	if(obedit && obedit->type == OB_MESH) {
		BMEditMesh *em= ((Mesh*)obedit->data)->edit_btmesh;

		if(em->selectmode & SCE_SELECT_VERTEX) {
			if(em->bm->selected.first && em->bm->selected.last &&
				((BMEditSelection*)em->bm->selected.first)->type == BM_VERT && ((BMEditSelection*)em->bm->selected.last)->type == BM_VERT) {
				RNA_enum_items_add_value(&item, &totitem, merge_type_items, 6);
				RNA_enum_items_add_value(&item, &totitem, merge_type_items, 1);
			}
			else if(em->bm->selected.first && ((BMEditSelection*)em->bm->selected.first)->type == BM_VERT)
				RNA_enum_items_add_value(&item, &totitem, merge_type_items, 1);
			else if(em->bm->selected.last && ((BMEditSelection*)em->bm->selected.last)->type == BM_VERT)
				RNA_enum_items_add_value(&item, &totitem, merge_type_items, 6);
		}

		RNA_enum_items_add_value(&item, &totitem, merge_type_items, 3);
		RNA_enum_items_add_value(&item, &totitem, merge_type_items, 4);
		RNA_enum_items_add_value(&item, &totitem, merge_type_items, 5);
		RNA_enum_item_end(&item, &totitem);

		*free= 1;

		return item;
	}
	
	return NULL;
}

void MESH_OT_merge(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Merge";
	ot->idname= "MESH_OT_merge";

	/* api callbacks */
	ot->exec= merge_exec;
	ot->invoke= WM_menu_invoke;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* properties */
	ot->prop= RNA_def_enum(ot->srna, "type", merge_type_items, 3, "Type", "Merge method to use.");
	RNA_def_enum_funcs(ot->prop, merge_type_itemf);
	RNA_def_boolean(ot->srna, "uvs", 1, "UVs", "Move UVs according to merge.");
}


static int removedoublesflag_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	BMOperator bmop;
	int count;

	EDBM_InitOpf(em, &bmop, op, "finddoubles verts=%hv dist=%f", 
		BM_SELECT, RNA_float_get(op->ptr, "mergedist"));
	BMO_Exec_Op(em->bm, &bmop);

	count = BMO_CountSlotMap(em->bm, &bmop, "targetmapout");

	if (!EDBM_CallOpf(em, op, "weldverts targetmap=%s", &bmop, "targetmapout")) {
		BMO_Finish_Op(em->bm, &bmop);
		return OPERATOR_CANCELLED;
	}

	if (!EDBM_FinishOp(em, &bmop, op, 1))
		return OPERATOR_CANCELLED;

	/*we need a better way of reporting this, since this doesn't work
	  with the last operator panel correctly.
	if(count)
	{
		sprintf(msg, "Removed %d vertices", count);
		BKE_report(op->reports, RPT_INFO, msg);
	}
	*/

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_remove_doubles(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Remove Doubles";
	ot->idname= "MESH_OT_remove_doubles";

	/* api callbacks */
	ot->exec= removedoublesflag_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	RNA_def_float(ot->srna, "mergedist", 0.0001f, 0.000001f, 50.0f, 
		"Merge Distance", 
		"Minimum distance between elements to merge.", 0.00001, 10.0);
}

/************************ Vertex Path Operator *************************/

typedef struct PathNode {
	int u;
	int visited;
	ListBase edges;
} PathNode;

typedef struct PathEdge {
	struct PathEdge *next, *prev;
	int v;
	float w;
} PathEdge;



static int select_vertex_path_exec(bContext *C, wmOperator *op)
{
	Object *ob = CTX_data_edit_object(C);
	BMEditMesh *em = ((Mesh*)ob->data)->edit_btmesh;
	BMOperator bmop;
	BMEditSelection *sv, *ev;

	/* get the type from RNA */
	int type = RNA_enum_get(op->ptr, "type");

	sv = em->bm->selected.last;
	if( sv != NULL )
		ev = sv->prev;
	else return OPERATOR_CANCELLED;
	if( ev == NULL )
		return OPERATOR_CANCELLED;

	if( sv->type != BM_VERT || ev->type != BM_VERT )
		return OPERATOR_CANCELLED;

	/* initialize the bmop using EDBM api, which does various ui error reporting and other stuff */
	EDBM_InitOpf(em, &bmop, op, "vertexshortestpath startv=%e endv=%e type=%d", sv->data, ev->data, type);

	/* execute the operator */
	BMO_Exec_Op(em->bm, &bmop);

	/* DO NOT clear the existing selection */
	/* EDBM_clear_flag_all(em, BM_SELECT); */

	/* select the output */
	BMO_HeaderFlag_Buffer(em->bm, &bmop, "vertout", BM_SELECT, BM_ALL);

	/* finish the operator */
	if( !EDBM_FinishOp(em, &bmop, op, 1) )
		return OPERATOR_CANCELLED;

	EDBM_selectmode_flush(em);

	/* dependencies graph and notification stuff */
/*	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT | ND_GEOM_SELECT, ob);
*/
	DAG_id_tag_update(ob->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, ob->data);


	/* we succeeded */
	return OPERATOR_FINISHED;
#if 0
	Object *obedit= CTX_data_edit_object(C);
	EditMesh *em= BKE_mesh_get_editmesh((Mesh *)obedit->data);
	EditVert *eve, *s, *t;
	EditEdge *eed;
	EditSelection *ese;
	PathEdge *newpe, *currpe;
	PathNode *currpn;
	PathNode *Q;
	int v, *previous, pathvert, pnindex; /*pnindex redundant?*/
	int unbalanced, totnodes;
	short physical;
	float *cost;
	Heap *heap; /*binary heap for sorting pointers to PathNodes based upon a 'cost'*/

	s = t = NULL;

	ese = ((EditSelection*)em->selected.last);
	if(ese && ese->type == EDITVERT && ese->prev && ese->prev->type == EDITVERT){
		physical= pupmenu("Distance Method? %t|Edge Length%x1|Topological%x0");

		t = (EditVert*)ese->data;
		s = (EditVert*)ese->prev->data;

		/*need to find out if t is actually reachable by s....*/
		for(eve=em->verts.first; eve; eve=eve->next){
			eve->f1 = 0;
		}

		s->f1 = 1;

		unbalanced = 1;
		totnodes = 1;
		while(unbalanced){
			unbalanced = 0;
			for(eed=em->edges.first; eed; eed=eed->next){
				if(!eed->h){
					if(eed->v1->f1 && !eed->v2->f1){
							eed->v2->f1 = 1;
							totnodes++;
							unbalanced = 1;
					}
					else if(eed->v2->f1 && !eed->v1->f1){
							eed->v1->f1 = 1;
							totnodes++;
							unbalanced = 1;
					}
				}
			}
		}

		if(s->f1 && t->f1){ /* t can be reached by s */
			Q = MEM_callocN(sizeof(PathNode)*totnodes, "Path Select Nodes");
			totnodes = 0;
			for(eve=em->verts.first; eve; eve=eve->next){
				if(eve->f1){
					Q[totnodes].u = totnodes;
					Q[totnodes].edges.first = 0;
					Q[totnodes].edges.last = 0;
					Q[totnodes].visited = 0;
					eve->tmp.p = &(Q[totnodes]);
					totnodes++;
				}
				else eve->tmp.p = NULL;
			}

			for(eed=em->edges.first; eed; eed=eed->next){
				if(!eed->h){
					if(eed->v1->f1){
						currpn = ((PathNode*)eed->v1->tmp.p);

						newpe = MEM_mallocN(sizeof(PathEdge), "Path Edge");
						newpe->v = ((PathNode*)eed->v2->tmp.p)->u;
						if(physical){
								newpe->w = len_v3v3(eed->v1->co, eed->v2->co);
						}
						else newpe->w = 1;
						newpe->next = 0;
						newpe->prev = 0;
						BLI_addtail(&(currpn->edges), newpe);
					}
					if(eed->v2->f1){
						currpn = ((PathNode*)eed->v2->tmp.p);
						newpe = MEM_mallocN(sizeof(PathEdge), "Path Edge");
						newpe->v = ((PathNode*)eed->v1->tmp.p)->u;
						if(physical){
								newpe->w = len_v3v3(eed->v1->co, eed->v2->co);
						}
						else newpe->w = 1;
						newpe->next = 0;
						newpe->prev = 0;
						BLI_addtail(&(currpn->edges), newpe);
					}
				}
			}

			heap = BLI_heap_new();
			cost = MEM_callocN(sizeof(float)*totnodes, "Path Select Costs");
			previous = MEM_callocN(sizeof(int)*totnodes, "PathNode indices");

			for(v=0; v < totnodes; v++){
				cost[v] = 1000000;
				previous[v] = -1; /*array of indices*/
			}

			pnindex = ((PathNode*)s->tmp.p)->u;
			cost[pnindex] = 0;
			BLI_heap_insert(heap,  0.0f, SET_INT_IN_POINTER(pnindex));

			while( !BLI_heap_empty(heap) ){

				pnindex = GET_INT_FROM_POINTER(BLI_heap_popmin(heap));
				currpn = &(Q[pnindex]);

				if(currpn == (PathNode*)t->tmp.p) /*target has been reached....*/
					break;

				for(currpe=currpn->edges.first; currpe; currpe=currpe->next){
					if(!Q[currpe->v].visited){
						if( cost[currpe->v] > (cost[currpn->u ] + currpe->w) ){
							cost[currpe->v] = cost[currpn->u] + currpe->w;
							previous[currpe->v] = currpn->u;
							Q[currpe->v].visited = 1;
							BLI_heap_insert(heap, cost[currpe->v], SET_INT_IN_POINTER(currpe->v));
						}
					}
				}
			}

			pathvert = ((PathNode*)t->tmp.p)->u;
			while(pathvert != -1){
				for(eve=em->verts.first; eve; eve=eve->next){
					if(eve->f1){
						if( ((PathNode*)eve->tmp.p)->u == pathvert) eve->f |= SELECT;
					}
				}
				pathvert = previous[pathvert];
			}

			for(v=0; v < totnodes; v++) BLI_freelistN(&(Q[v].edges));
			MEM_freeN(Q);
			MEM_freeN(cost);
			MEM_freeN(previous);
			BLI_heap_free(heap, NULL);
			EM_select_flush(em);
		}
	}
	else {
		BKE_mesh_end_editmesh(obedit->data, em);
		BKE_report(op->reports, RPT_ERROR, "Path Selection requires that exactly two vertices be selected");
		return OPERATOR_CANCELLED;
	}

	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
	BKE_mesh_end_editmesh(obedit->data, em);
#endif
}

void MESH_OT_select_vertex_path(wmOperatorType *ot)
{
	static const EnumPropertyItem type_items[] = {
		{VPATH_SELECT_EDGE_LENGTH, "EDGE_LENGTH", 0, "Edge Length", NULL},
		{VPATH_SELECT_TOPOLOGICAL, "TOPOLOGICAL", 0, "Topological", NULL},
		{0, NULL, 0, NULL, NULL}};

	/* identifiers */
	ot->name= "Select Vertex Path";
	ot->idname= "MESH_OT_select_vertex_path";

	/* api callbacks */
	ot->exec= select_vertex_path_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* properties */
	RNA_def_enum(ot->srna, "type", type_items, VPATH_SELECT_EDGE_LENGTH, "Type", "Method to compute distance.");
}
/********************** Rip Operator *************************/

/* helper to find edge for edge_rip */
static float mesh_rip_edgedist(ARegion *ar, float mat[][4], float *co1, float *co2, const int mval[2])
{
	float vec1[3], vec2[3], mvalf[2];

	ED_view3d_project_float(ar, co1, vec1, mat);
	ED_view3d_project_float(ar, co2, vec2, mat);
	mvalf[0]= (float)mval[0];
	mvalf[1]= (float)mval[1];

	return dist_to_line_segment_v2(mvalf, vec1, vec2);
}

/* based on mouse cursor position, it defines how is being ripped */
static int mesh_rip_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	Object *obedit= CTX_data_edit_object(C);
	ARegion *ar= CTX_wm_region(C);
	View3D *v3d = CTX_wm_view3d(C);
	RegionView3D *rv3d= CTX_wm_region_view3d(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	BMOperator bmop;
	BMBVHTree *bvhtree;
	BMOIter siter;
	BMIter iter, eiter, liter;
	BMLoop *l;
	BMEdge *e, *e2, *closest = NULL;
	BMVert *v;
	int side = 0, i, singlesel = 0;
	float projectMat[4][4], fmval[3] = {event->mval[0], event->mval[1], 0.0f};
	float dist = FLT_MAX, d;

	ED_view3d_ob_project_mat_get(rv3d, obedit, projectMat);

	BM_ITER(e, &iter, em->bm, BM_EDGES_OF_MESH, NULL) {
		if (BM_TestHFlag(e, BM_SELECT))
			BM_SetIndex(e, 1);
		else BM_SetIndex(e, 0);
	}

	/*handle case of one vert selected.  identify
	  closest edge around that vert to mouse cursor,
	  then rip two adjacent edges in the vert fan.*/
	if (em->bm->totvertsel == 1 && em->bm->totedgesel == 0 && em->bm->totfacesel == 0) {
		singlesel = 1;

		/*find selected vert*/
		BM_ITER(v, &iter, em->bm, BM_VERTS_OF_MESH, NULL) {
			if (BM_TestHFlag(v, BM_SELECT))
				break;
		}

		/*this should be impossible, but sanity checks are a good thing*/
		if (!v)
			return OPERATOR_CANCELLED;

		/*find closest edge to mouse cursor*/
		e2 = NULL;
		BM_ITER(e, &iter, em->bm, BM_EDGES_OF_VERT, v) {
			d = mesh_rip_edgedist(ar, projectMat, e->v1->co, e->v2->co, event->mval);
			if (d < dist) {
				dist = d;
				e2 = e;
			}
		}

		if (!e2)
			return OPERATOR_CANCELLED;

		/*rip two adjacent edges*/
		if (BM_Edge_FaceCount(e2) == 1) {
			l = e2->l;
			e = BM_OtherFaceLoop(e2, l->f, v)->e;

			BM_SetIndex(e, 1);
			BM_SetHFlag(e, BM_SELECT);
		} else if (BM_Edge_FaceCount(e2) == 2) {
			l = e2->l;
			e = BM_OtherFaceLoop(e2, l->f, v)->e;
			BM_SetIndex(e, 1);
			BM_SetHFlag(e, BM_SELECT);
			
			l = e2->l->radial_next;
			e = BM_OtherFaceLoop(e2, l->f, v)->e;
			BM_SetIndex(e, 1);
			BM_SetHFlag(e, BM_SELECT);
		}

		dist = FLT_MAX;
	} else {
		/*expand edge selection*/
		BM_ITER(v, &iter, em->bm, BM_VERTS_OF_MESH, NULL) {
			e2 = NULL;
			i = 0;
			BM_ITER(e, &eiter, em->bm, BM_EDGES_OF_VERT, v) {
				if (BM_GetIndex(e)) {
					e2 = e;
					i++;
				}
			}
			
			if (i == 1 && e2->l) {
				l = BM_OtherFaceLoop(e2, e2->l->f, v);
				l = (BMLoop*)l->radial_next;
				l = BM_OtherFaceLoop(l->e, l->f, v);

				if (l)
					BM_Select(em->bm, l->e, 1);
			}
		}
	}

	if (!EDBM_InitOpf(em, &bmop, op, "edgesplit edges=%he", BM_SELECT)) {
		return OPERATOR_CANCELLED;
	}
	
	BMO_Exec_Op(em->bm, &bmop);

	/*build bvh tree for edge visibility tests*/
	bvhtree = BMBVH_NewBVH(em);

	for (i=0; i<2; i++) {
		BMO_ITER(e, &siter, em->bm, &bmop, i ? "edgeout2":"edgeout1", BM_EDGE) {
			float cent[3] = {0, 0, 0}, mid[4], vec[3];

			if (!BMBVH_EdgeVisible(bvhtree, e, ar, v3d, obedit) || !e->l)
				continue;

			/*method for calculating distance:
			
			  for each edge: calculate face center, then made a vector
			  from edge midpoint to face center.  offset edge midpoint
			  by a small amount along this vector.*/
			BM_ITER(l, &liter, em->bm, BM_LOOPS_OF_FACE, e->l->f) {
				add_v3_v3v3(cent, cent, l->v->co);
			}
			mul_v3_fl(cent, 1.0f/(float)e->l->f->len);

			add_v3_v3v3(mid, e->v1->co, e->v2->co);
			mul_v3_fl(mid, 0.5f);
			sub_v3_v3v3(vec, cent, mid);
			normalize_v3(vec);
			mul_v3_fl(vec, 0.01f);
			add_v3_v3v3(mid, mid, vec);

			/*yay we have our comparison point, now project it*/
			ED_view3d_project_float(ar, mid, mid, projectMat);

			vec[0] = fmval[0] - mid[0];
			vec[1] = fmval[1] - mid[1];
			d = vec[0]*vec[0] + vec[1]*vec[1];

			if (d < dist) {
				side = i;
				closest = e;
				dist = d;
			}
		}
	}
	
	EDBM_clear_flag_all(em, BM_SELECT);
	BMO_HeaderFlag_Buffer(em->bm, &bmop, side?"edgeout2":"edgeout1", BM_SELECT, BM_EDGE);

	BM_ITER(e, &iter, em->bm, BM_EDGES_OF_MESH, NULL) {
		if (BM_TestHFlag(e, BM_SELECT))
			BM_SetIndex(e, 1);
		else BM_SetIndex(e, 0);
	}

	/*constrict edge selection again*/
	BM_ITER(v, &iter, em->bm, BM_VERTS_OF_MESH, NULL) {
		e2 = NULL;
		i = 0;
		BM_ITER(e, &eiter, em->bm, BM_EDGES_OF_VERT, v) {
			if (BM_GetIndex(e)) {
				e2 = e;
				i++;
			}
		}
		
		if (i == 1)  {
			if (singlesel)
				BM_Select(em->bm, v, 0);
			else
				BM_Select(em->bm, e2, 0);
		}
	}

	EDBM_selectmode_flush(em);
	
	if (!EDBM_FinishOp(em, &bmop, op, 1)) {
		BMBVH_FreeBVH(bvhtree);
		return OPERATOR_CANCELLED;
	}
	
	BMBVH_FreeBVH(bvhtree);

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_rip(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Rip";
	ot->idname= "MESH_OT_rip";

	/* api callbacks */
	ot->invoke= mesh_rip_invoke;
	ot->poll= EM_view3d_poll;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* to give to transform */
	Transform_Properties(ot, P_PROPORTIONAL);
	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Editing", "");
}

/************************ Shape Operators *************************/

/*BMESH_TODO this should be properly encapsulated in a bmop.  but later.*/
static void shape_propagate(Object *obedit, BMEditMesh *em, wmOperator *op)
{
	BMIter iter;
	BMVert *eve = NULL;
	float *co;
	int i, totshape = CustomData_number_of_layers(&em->bm->vdata, CD_SHAPEKEY);

	if (!CustomData_has_layer(&em->bm->vdata, CD_SHAPEKEY)) {
		BKE_report(op->reports, RPT_ERROR, "Mesh does not have shape keys");
		return;
	}
	
	BM_ITER(eve, &iter, em->bm, BM_VERTS_OF_MESH, NULL) {
		if (!BM_TestHFlag(eve, BM_SELECT) || BM_TestHFlag(eve, BM_HIDDEN))
			continue;

		for (i=0; i<totshape; i++) {
			co = CustomData_bmesh_get_n(&em->bm->vdata, eve->head.data, CD_SHAPEKEY, i);
			VECCOPY(co, eve->co);
		}
	}

#if 0
	//TAG Mesh Objects that share this data
	for(base = scene->base.first; base; base = base->next){
		if(base->object && base->object->data == me){
			base->object->recalc = OB_RECALC_DATA;
		}
	}
#endif

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
}


static int shape_propagate_to_all_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	Mesh *me= obedit->data;
	BMEditMesh *em= me->edit_btmesh;

	shape_propagate(obedit, em, op);

	DAG_id_tag_update(&me->id, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, me);

	return OPERATOR_FINISHED;
}


void MESH_OT_shape_propagate_to_all(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Shape Propagate";
	ot->description= "Apply selected vertex locations to all other shape keys.";
	ot->idname= "MESH_OT_shape_propagate_to_all";

	/* api callbacks */
	ot->exec= shape_propagate_to_all_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/*BMESH_TODO this should be properly encapsulated in a bmop.  but later.*/
static int blend_from_shape_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	Mesh *me= obedit->data;
	BMEditMesh *em= me->edit_btmesh;
	BMVert *eve;
	BMIter iter;
	float co[3], *sco;
	float blend= RNA_float_get(op->ptr, "blend");
	int shape= RNA_enum_get(op->ptr, "shape");
	int add= RNA_int_get(op->ptr, "add");
	int totshape;

	/*sanity check*/
	totshape = CustomData_number_of_layers(&em->bm->vdata, CD_SHAPEKEY);
	if (totshape == 0 || shape < 0 || shape >= totshape)
		return OPERATOR_CANCELLED;

	BM_ITER(eve, &iter, em->bm, BM_VERTS_OF_MESH, NULL) {
		if (!BM_TestHFlag(eve, BM_SELECT) || BM_TestHFlag(eve, BM_HIDDEN))
			continue;

		sco = CustomData_bmesh_get_n(&em->bm->vdata, eve->head.data, CD_SHAPEKEY, shape);
		VECCOPY(co, sco);


		if(add) {
			mul_v3_fl(co, blend);
			add_v3_v3v3(eve->co, eve->co, co);
		}
		else
			interp_v3_v3v3(eve->co, eve->co, co, blend);
		
		VECCOPY(sco, co);
	}

	DAG_id_tag_update(&me->id, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, me);

	return OPERATOR_FINISHED;
}

static EnumPropertyItem *shape_itemf(bContext *C, PointerRNA *UNUSED(ptr),  PropertyRNA *UNUSED(prop), int *free)
{	
	Object *obedit= CTX_data_edit_object(C);
	Mesh *me= (obedit) ? obedit->data : NULL;
	BMEditMesh *em = me->edit_btmesh;
	EnumPropertyItem tmp= {0, "", 0, "", ""}, *item= NULL;
	int totitem= 0, a;

	if(obedit && obedit->type == OB_MESH && CustomData_has_layer(&em->bm->vdata, CD_SHAPEKEY)) {
		for (a=0; a<em->bm->vdata.totlayer; a++) {
			if (em->bm->vdata.layers[a].type != CD_SHAPEKEY)
				continue;

			tmp.value= totitem;
			tmp.identifier= em->bm->vdata.layers[a].name;
			tmp.name= em->bm->vdata.layers[a].name;
			RNA_enum_item_add(&item, &totitem, &tmp);

			totitem++;
		}
	}

	RNA_enum_item_end(&item, &totitem);
	*free= 1;

	return item;
}

void MESH_OT_blend_from_shape(wmOperatorType *ot)
{
	PropertyRNA *prop;
	static EnumPropertyItem shape_items[]= {{0, NULL, 0, NULL, NULL}};

	/* identifiers */
	ot->name= "Blend From Shape";
	ot->description= "Blend in shape from a shape key.";
	ot->idname= "MESH_OT_blend_from_shape";

	/* api callbacks */
	ot->exec= blend_from_shape_exec;
	ot->invoke= WM_operator_props_popup;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* properties */
	prop= RNA_def_enum(ot->srna, "shape", shape_items, 0, "Shape", "Shape key to use for blending.");
	RNA_def_enum_funcs(prop, shape_itemf);
	RNA_def_float(ot->srna, "blend", 1.0f, -FLT_MAX, FLT_MAX, "Blend", "Blending factor.", -2.0f, 2.0f);
	RNA_def_boolean(ot->srna, "add", 1, "Add", "Add rather then blend between shapes.");
}

/* TODO - some way to select on an arbitrary axis */
static int select_axis_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	BMEditSelection *ese = em->bm->selected.last;
	int axis= RNA_int_get(op->ptr, "axis");
	int mode= RNA_enum_get(op->ptr, "mode"); /* -1==aligned, 0==neg, 1==pos*/

	if(ese==NULL)
		return OPERATOR_CANCELLED;

	if(ese->type==BM_VERT) {
		BMVert *ev, *act_vert= (BMVert*)ese->data;
		BMIter iter;
		float value= act_vert->co[axis];
		float limit=  CTX_data_tool_settings(C)->doublimit; // XXX

		if(mode==0)
			value -= limit;
		else if (mode==1) 
			value += limit;

		BM_ITER(ev, &iter, em->bm, BM_VERTS_OF_MESH, NULL) {
			if(!BM_TestHFlag(ev, BM_HIDDEN)) {
				switch(mode) {
				case -1: /* aligned */
					if(fabs(ev->co[axis] - value) < limit)
						BM_Select(em->bm, ev, 1);
					break;
				case 0: /* neg */
					if(ev->co[axis] > value)
						BM_Select(em->bm, ev, 1);
					break;
				case 1: /* pos */
					if(ev->co[axis] < value)
						BM_Select(em->bm, ev, 1);
					break;
				}
			}
		}
	}

	EDBM_selectmode_flush(em);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_select_axis(wmOperatorType *ot)
{
	static EnumPropertyItem axis_mode_items[] = {
		{0,  "POSITIVE", 0, "Positive Axis", ""},
		{1,  "NEGATIVE", 0, "Negative Axis", ""},
		{-1, "ALIGNED",  0, "Aligned Axis", ""},
		{0, NULL, 0, NULL, NULL}};

	/* identifiers */
	ot->name= "Select Axis";
	ot->description= "Select all data in the mesh on a single axis.";
	ot->idname= "MESH_OT_select_axis";

	/* api callbacks */
	ot->exec= select_axis_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* properties */
	RNA_def_enum(ot->srna, "mode", axis_mode_items, 0, "Axis Mode", "Axis side to use when selecting");
	RNA_def_int(ot->srna, "axis", 0, 0, 2, "Axis", "Select the axis to compare each vertex on", 0, 2);
}

static int solidify_exec(bContext *UNUSED(C), wmOperator *UNUSED(op))
{
#if 0
	Object *obedit= CTX_data_edit_object(C);
	EditMesh *em= BKE_mesh_get_editmesh(((Mesh *)obedit->data));
	float nor[3] = {0,0,1};

	float thickness= RNA_float_get(op->ptr, "thickness");

	extrudeflag(obedit, em, SELECT, nor, 1);
	EM_make_hq_normals(em);
	EM_solidify(em, thickness);


	/* update vertex normals too */
	recalc_editnormals(em);

	BKE_mesh_end_editmesh(obedit->data, em);

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
#endif
	return OPERATOR_CANCELLED;
}


void MESH_OT_solidify(wmOperatorType *ot)
{
	PropertyRNA *prop;
	/* identifiers */
	ot->name= "Solidify";
	ot->description= "Create a solid skin by extruding, compensating for sharp angles.";
	ot->idname= "MESH_OT_solidify";

	/* api callbacks */
	ot->exec= solidify_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	prop= RNA_def_float(ot->srna, "thickness", 0.01f, -FLT_MAX, FLT_MAX, "thickness", "", -10.0f, 10.0f);
	RNA_def_property_ui_range(prop, -10, 10, 0.1, 4);
}

#define TRAIL_POLYLINE 1 /* For future use, They don't do anything yet */
#define TRAIL_FREEHAND 2
#define TRAIL_MIXED    3 /* (1|2) */
#define TRAIL_AUTO     4 
#define	TRAIL_MIDPOINTS 8

typedef struct CutCurve {
	float  x; 
	float  y;
} CutCurve;

/* ******************************************************************** */
/* Knife Subdivide Tool.  Subdivides edges intersected by a mouse trail
	drawn by user.
	
	Currently mapped to KKey when in MeshEdit mode.
	Usage:
		Hit Shift K, Select Centers or Exact
		Hold LMB down to draw path, hit RETKEY.
		ESC cancels as expected.
   
	Contributed by Robert Wenzlaff (Det. Thorn).

    2.5 revamp:
    - non modal (no menu before cutting)
    - exit on mouse release
    - polygon/segment drawing can become handled by WM cb later

	bmesh port version
*/

#define KNIFE_EXACT		1
#define KNIFE_MIDPOINT	2
#define KNIFE_MULTICUT	3

static EnumPropertyItem knife_items[]= {
	{KNIFE_EXACT, "EXACT", 0, "Exact", ""},
	{KNIFE_MIDPOINT, "MIDPOINTS", 0, "Midpoints", ""},
	{KNIFE_MULTICUT, "MULTICUT", 0, "Multicut", ""},
	{0, NULL, 0, NULL, NULL}
};

/* seg_intersect() Determines if and where a mouse trail intersects an EditEdge */

static float bm_seg_intersect(BMEdge *e, CutCurve *c, int len, char mode,
                              struct GHash *gh, int *isected)
{
#define MAXSLOPE 100000
	float  x11, y11, x12=0, y12=0, x2max, x2min, y2max;
	float  y2min, dist, lastdist=0, xdiff2, xdiff1;
	float  m1, b1, m2, b2, x21, x22, y21, y22, xi;
	float  yi, x1min, x1max, y1max, y1min, perc=0; 
	float  *scr;
	float  threshold = 0.0;
	int  i;
	
	//threshold = 0.000001; /*tolerance for vertex intersection*/
	// XXX	threshold = scene->toolsettings->select_thresh / 100;
	
	/* Get screen coords of verts */
	scr = BLI_ghash_lookup(gh, e->v1);
	x21=scr[0];
	y21=scr[1];
	
	scr = BLI_ghash_lookup(gh, e->v2);
	x22=scr[0];
	y22=scr[1];
	
	xdiff2=(x22-x21);  
	if (xdiff2) {
		m2=(y22-y21)/xdiff2;
		b2= ((x22*y21)-(x21*y22))/xdiff2;
	}
	else {
		m2=MAXSLOPE;  /* Verticle slope  */
		b2=x22;      
	}

	*isected = 0;

	/*check for *exact* vertex intersection first*/
	if(mode!=KNIFE_MULTICUT){
		for (i=0; i<len; i++){
			if (i>0){
				x11=x12;
				y11=y12;
			}
			else {
				x11=c[i].x;
				y11=c[i].y;
			}
			x12=c[i].x;
			y12=c[i].y;
			
			/*test e->v1*/
			if((x11 == x21 && y11 == y21) || (x12 == x21 && y12 == y21)){
				perc = 0;
				*isected = 1;
				return(perc);
			}
			/*test e->v2*/
			else if((x11 == x22 && y11 == y22) || (x12 == x22 && y12 == y22)){
				perc = 0;
				*isected = 2;
				return(perc);
			}
		}
	}
	
	/*now check for edge interesect (may produce vertex intersection as well)*/
	for (i=0; i<len; i++){
		if (i>0){
			x11=x12;
			y11=y12;
		}
		else {
			x11=c[i].x;
			y11=c[i].y;
		}
		x12=c[i].x;
		y12=c[i].y;
		
		/* Perp. Distance from point to line */
		if (m2!=MAXSLOPE) dist=(y12-m2*x12-b2);/* /sqrt(m2*m2+1); Only looking for */
			/* change in sign.  Skip extra math */	
		else dist=x22-x12;	
		
		if (i==0) lastdist=dist;
		
		/* if dist changes sign, and intersect point in edge's Bound Box*/
		if ((lastdist*dist)<=0){
			xdiff1=(x12-x11); /* Equation of line between last 2 points */
			if (xdiff1){
				m1=(y12-y11)/xdiff1;
				b1= ((x12*y11)-(x11*y12))/xdiff1;
			}
			else{
				m1=MAXSLOPE;
				b1=x12;
			}
			x2max=MAX2(x21,x22)+0.001; /* prevent missed edges   */
			x2min=MIN2(x21,x22)-0.001; /* due to round off error */
			y2max=MAX2(y21,y22)+0.001;
			y2min=MIN2(y21,y22)-0.001;
			
			/* Found an intersect,  calc intersect point */
			if (m1==m2){ /* co-incident lines */
				/* cut at 50% of overlap area*/
				x1max=MAX2(x11, x12);
				x1min=MIN2(x11, x12);
				xi= (MIN2(x2max,x1max)+MAX2(x2min,x1min))/2.0;	
				
				y1max=MAX2(y11, y12);
				y1min=MIN2(y11, y12);
				yi= (MIN2(y2max,y1max)+MAX2(y2min,y1min))/2.0;
			}			
			else if (m2==MAXSLOPE){ 
				xi=x22;
				yi=m1*x22+b1;
			}
			else if (m1==MAXSLOPE){ 
				xi=x12;
				yi=m2*x12+b2;
			}
			else {
				xi=(b1-b2)/(m2-m1);
				yi=(b1*m2-m1*b2)/(m2-m1);
			}
			
			/* Intersect inside bounding box of edge?*/
			if ((xi>=x2min)&&(xi<=x2max)&&(yi<=y2max)&&(yi>=y2min)){
				/*test for vertex intersect that may be 'close enough'*/
				if(mode!=KNIFE_MULTICUT){
					if(xi <= (x21 + threshold) && xi >= (x21 - threshold)){
						if(yi <= (y21 + threshold) && yi >= (y21 - threshold)){
							*isected = 1;
							perc = 0;
							break;
						}
					}
					if(xi <= (x22 + threshold) && xi >= (x22 - threshold)){
						if(yi <= (y22 + threshold) && yi >= (y22 - threshold)){
							*isected = 2;
							perc = 0;
							break;
						}
					}
				}
				if ((m2<=1.0)&&(m2>=-1.0)) perc = (xi-x21)/(x22-x21);	
				else perc=(yi-y21)/(y22-y21); /*lower slope more accurate*/
				//isect=32768.0*(perc+0.0000153); /* Percentage in 1/32768ths */
				
				break;
			}
		}	
		lastdist=dist;
	}
	return(perc);
} 

#define MAX_CUTS 2048

static int knife_cut_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= (((Mesh *)obedit->data))->edit_btmesh;
	BMesh *bm = em->bm;
	ARegion *ar= CTX_wm_region(C);
	BMVert *bv;
	BMIter iter;
	BMEdge *be;
	BMOperator bmop;
	CutCurve curve[MAX_CUTS];
	struct GHash *gh;
	float isect=0.0;
	float  *scr, co[4];
	int len=0, isected, i;
	short numcuts=1, mode= RNA_int_get(op->ptr, "type");
	
	/* edit-object needed for matrix, and ar->regiondata for projections to work */
	if (ELEM3(NULL, obedit, ar, ar->regiondata))
		return OPERATOR_CANCELLED;
	
	if (bm->totvertsel < 2) {
		//error("No edges are selected to operate on");
		return OPERATOR_CANCELLED;;
	}

	/* get the cut curve */
	RNA_BEGIN(op->ptr, itemptr, "path") {
		
		RNA_float_get_array(&itemptr, "loc", (float *)&curve[len]);
		len++;
		if(len>= MAX_CUTS) break;
	}
	RNA_END;
	
	if(len<2) {
		return OPERATOR_CANCELLED;
	}

	/*the floating point coordinates of verts in screen space will be stored in a hash table according to the vertices pointer*/
	gh = BLI_ghash_new(BLI_ghashutil_ptrhash, BLI_ghashutil_ptrcmp, "knife cut exec");
	for(bv=BMIter_New(&iter, bm, BM_VERTS_OF_MESH, NULL);bv;bv=BMIter_Step(&iter)){
		scr = MEM_mallocN(sizeof(float)*2, "Vertex Screen Coordinates");
		VECCOPY(co, bv->co);
		co[3]= 1.0;
		mul_m4_v4(obedit->obmat, co);
		project_float(ar, co, scr);
		BLI_ghash_insert(gh, bv, scr);
	}
	
	BMO_Init_Op(&bmop, "esubd");
	
	i = 0;
	/*store percentage of edge cut for KNIFE_EXACT here.*/
	for (be=BMIter_New(&iter, bm, BM_EDGES_OF_MESH, NULL); be; be=BMIter_Step(&iter)) {
		if( BM_Selected(bm, be) ) {
			isect= bm_seg_intersect(be, curve, len, mode, gh, &isected);
			
			if (isect != 0.0f) {
				if (mode != KNIFE_MULTICUT && mode != KNIFE_MIDPOINT) {
					BMO_Insert_MapFloat(bm, &bmop, 
				               "edgepercents",
				               be, isect);

				}
				BMO_SetFlag(bm, be, 1);
			} else BMO_ClearFlag(bm, be, 1);
		} else BMO_ClearFlag(bm, be, 1);
	}
	
	BMO_Flag_To_Slot(bm, &bmop, "edges", 1, BM_EDGE);

	if (mode == KNIFE_MIDPOINT) numcuts = 1;
	BMO_Set_Int(&bmop, "numcuts", numcuts);

	BMO_Set_Int(&bmop, "flag", B_KNIFE);
	BMO_Set_Int(&bmop, "quadcornertype", SUBD_STRAIGHT_CUT);
	BMO_Set_Int(&bmop, "singleedge", 0);
	BMO_Set_Int(&bmop, "gridfill", 0);

	BMO_Set_Float(&bmop, "radius", 0);
	
	BMO_Exec_Op(bm, &bmop);
	BMO_Finish_Op(bm, &bmop);
	
	BLI_ghash_free(gh, NULL, (GHashValFreeFP)MEM_freeN);

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_knife_cut(wmOperatorType *ot)
{
	PropertyRNA *prop;
	
	ot->name= "Knife Cut";
	ot->description= "Cut selected edges and faces into parts.";
	ot->idname= "MESH_OT_knife_cut";
	
	ot->invoke= WM_gesture_lines_invoke;
	ot->modal= WM_gesture_lines_modal;
	ot->exec= knife_cut_exec;
	
	ot->poll= EM_view3d_poll;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	RNA_def_enum(ot->srna, "type", knife_items, KNIFE_EXACT, "Type", "");
	prop= RNA_def_property(ot->srna, "path", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_runtime(prop, &RNA_OperatorMousePath);
	
	/* internal */
	RNA_def_int(ot->srna, "cursor", BC_KNIFECURSOR, 0, INT_MAX, "Cursor", "", 0, INT_MAX);
}

static int mesh_separate_selected(Main *bmain, Scene *scene, Base *editbase, wmOperator *wmop)
{
	Base *basenew;
	BMIter iter;
	BMVert *v;
	BMEdge *e;
	Object *obedit = editbase->object;
	Mesh *me = obedit->data;
	BMEditMesh *em = me->edit_btmesh;
	BMesh *bmnew;
	int allocsize[] = {512, 512, 2048, 512};
	
	if (!em)
		return OPERATOR_CANCELLED;
		
	bmnew = BM_Make_Mesh(obedit, allocsize);
	CustomData_copy(&em->bm->vdata, &bmnew->vdata, CD_MASK_BMESH, CD_CALLOC, 0);
	CustomData_copy(&em->bm->edata, &bmnew->edata, CD_MASK_BMESH, CD_CALLOC, 0);
	CustomData_copy(&em->bm->ldata, &bmnew->ldata, CD_MASK_BMESH, CD_CALLOC, 0);
	CustomData_copy(&em->bm->pdata, &bmnew->pdata, CD_MASK_BMESH, CD_CALLOC, 0);

	CustomData_bmesh_init_pool(&bmnew->vdata, allocsize[0]);
	CustomData_bmesh_init_pool(&bmnew->edata, allocsize[1]);
	CustomData_bmesh_init_pool(&bmnew->ldata, allocsize[2]);
	CustomData_bmesh_init_pool(&bmnew->pdata, allocsize[3]);
		
	basenew= ED_object_add_duplicate(bmain, scene, editbase, USER_DUP_MESH);	/* 0 = fully linked */
	assign_matarar(basenew->object, give_matarar(obedit), *give_totcolp(obedit)); /* new in 2.5 */

	ED_base_object_select(basenew, BA_DESELECT);
	
	EDBM_CallOpf(em, wmop, "dupe geom=%hvef dest=%p", BM_SELECT, bmnew);
	EDBM_CallOpf(em, wmop, "del geom=%hvef context=%i", BM_SELECT, DEL_FACES);
	
	/*clean up any loose edges*/
	BM_ITER(e, &iter, em->bm, BM_EDGES_OF_MESH, NULL) {
		if (BM_TestHFlag(e, BM_HIDDEN))
			continue;

		if (BM_Edge_FaceCount(e) != 0)
			BM_Select(em->bm, e, 0); /*deselect*/
	}
	EDBM_CallOpf(em, wmop, "del geom=%hvef context=%i", BM_SELECT, DEL_EDGES);

	/*clean up any loose verts*/
	BM_ITER(v, &iter, em->bm, BM_VERTS_OF_MESH, NULL) {
		if (BM_TestHFlag(v, BM_HIDDEN))
			continue;

		if (BM_Vert_EdgeCount(v) != 0)
			BM_Select(em->bm, v, 0); /*deselect*/
	}
	
	EDBM_CallOpf(em, wmop, "del geom=%hvef context=%i", BM_SELECT, DEL_VERTS);
	
	BM_Compute_Normals(bmnew);
	BMO_CallOpf(bmnew, "bmesh_to_mesh mesh=%p object=%p", basenew->object->data, basenew->object);
		
	BM_Free_Mesh(bmnew);
	((Mesh*)basenew->object->data)->edit_btmesh = NULL;
	
	return 1;
}

//BMESH_TODO
static int mesh_separate_material(Main *UNUSED(bmain), Scene *UNUSED(scene), Base *UNUSED(editbase), wmOperator *UNUSED(wmop))
{
	return 0;
}

//BMESH_TODO
static int mesh_separate_loose(Main *UNUSED(bmain), Scene *UNUSED(scene), Base *UNUSED(editbase), wmOperator *UNUSED(wmop))
{
	return 0;
}

static int mesh_separate_exec(bContext *C, wmOperator *op)
{
	Main *bmain = CTX_data_main(C);
	Scene *scene= CTX_data_scene(C);
	Base *base= CTX_data_active_base(C);
	int retval= 0, type= RNA_enum_get(op->ptr, "type");
	
	if(type == 0)
		retval= mesh_separate_selected(bmain, scene, base, op);
	else if(type == 1)
		retval= mesh_separate_material (bmain, scene, base, op);
	else if(type == 2)
		retval= mesh_separate_loose(bmain, scene, base, op);
	   
	if(retval) {
		DAG_id_tag_update(base->object->data, OB_RECALC_DATA);
		WM_event_add_notifier(C, NC_GEOM|ND_DATA, base->object->data);
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
	ot->name= "Separate";
	ot->description= "Separate selected geometry into a new mesh.";
	ot->idname= "MESH_OT_separate";
	
	/* api callbacks */
	ot->invoke= WM_menu_invoke;
	ot->exec= mesh_separate_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	ot->prop = RNA_def_enum(ot->srna, "type", prop_separate_types, 0, "Type", "");
}


static int fill_mesh_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	BMOperator bmop;
	
	if (!EDBM_InitOpf(em, &bmop, op, "triangle_fill edges=%he", BM_SELECT))
		return OPERATOR_CANCELLED;
	
	BMO_Exec_Op(em->bm, &bmop);
	
	/*select new geometry*/
	BMO_HeaderFlag_Buffer(em->bm, &bmop, "geomout", BM_SELECT, BM_FACE|BM_EDGE);
	
	if (!EDBM_FinishOp(em, &bmop, op, 1))
		return OPERATOR_CANCELLED;
	
	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);
	
	return OPERATOR_FINISHED;

}

void MESH_OT_fill(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Fill";
	ot->idname= "MESH_OT_fill";

	/* api callbacks */
	ot->exec= fill_mesh_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int beautify_fill_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;

	if (!EDBM_CallOpf(em, op, "beautify_fill faces=%hf", BM_SELECT))
		return OPERATOR_CANCELLED;

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);
	
	return OPERATOR_FINISHED;
}

void MESH_OT_beautify_fill(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Beautify Fill";
	ot->idname= "MESH_OT_beautify_fill";

	/* api callbacks */
	ot->exec= beautify_fill_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/********************** Quad/Tri Operators *************************/

static int quads_convert_to_tris_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;

	if (!EDBM_CallOpf(em, op, "triangulate faces=%hf", BM_SELECT))
		return OPERATOR_CANCELLED;

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_quads_convert_to_tris(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Quads to Tris";
	ot->idname= "MESH_OT_quads_convert_to_tris";

	/* api callbacks */
	ot->exec= quads_convert_to_tris_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int tris_convert_to_quads_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	int dosharp, douvs, dovcols, domaterials;
	float limit = RNA_float_get(op->ptr, "limit");

	dosharp = RNA_boolean_get(op->ptr, "sharp");
	douvs = RNA_boolean_get(op->ptr, "uvs");
	dovcols = RNA_boolean_get(op->ptr, "vcols");
	domaterials = RNA_boolean_get(op->ptr, "materials");

	if (!EDBM_CallOpf(em, op, 
		"join_triangles faces=%hf limit=%f compare_sharp=%i compare_uvs=%i compare_vcols=%i compare_materials=%i", 
		BM_SELECT, limit, dosharp, douvs, dovcols, domaterials)) 
	{
		return OPERATOR_CANCELLED;
	}

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_tris_convert_to_quads(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Tris to Quads";
	ot->idname= "MESH_OT_tris_convert_to_quads";

	/* api callbacks */
	ot->exec= tris_convert_to_quads_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	RNA_def_float(ot->srna, "limit", 40.0f, -180.0f, 180.0f, "Max Angle", "Angle Limit in Degrees", -180, 180.0f);
	
	RNA_def_boolean(ot->srna, "uvs", 0, "Compare UVs", "");
	RNA_def_boolean(ot->srna, "vcols", 0, "Compare VCols", "");
	RNA_def_boolean(ot->srna, "sharp", 0, "Compare Sharp", "");
	RNA_def_boolean(ot->srna, "materials", 0, "Compare Materials", "");

}

static int edge_flip_exec(bContext *UNUSED(C), wmOperator *UNUSED(op))
{
#if 0
	Object *obedit= CTX_data_edit_object(C);
	EditMesh *em= BKE_mesh_get_editmesh((Mesh *)obedit->data);

	edge_flip(em);

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	BKE_mesh_end_editmesh(obedit->data, em);
#endif
	return OPERATOR_FINISHED;
}

void MESH_OT_edge_flip(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Edge Flip";
	ot->idname= "MESH_OT_edge_flip";

	/* api callbacks */
	ot->exec= edge_flip_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

//BMESH_TODO
static int split_mesh(bContext *UNUSED(C), wmOperator *UNUSED(op))
{
#if 0
	Object *obedit= CTX_data_edit_object(C);
	EditMesh *em= BKE_mesh_get_editmesh((Mesh *)obedit->data);

	WM_cursor_wait(1);

	/* make duplicate first */
	adduplicateflag(em, SELECT);
	/* old faces have flag 128 set, delete them */
	delfaceflag(em, 128);
	recalc_editnormals(em);

	WM_cursor_wait(0);

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	BKE_mesh_end_editmesh(obedit->data, em);
#endif
	return OPERATOR_FINISHED;
}

void MESH_OT_split(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Split";
	ot->idname= "MESH_OT_split";

	/* api callbacks */
	ot->exec= split_mesh;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}


static int spin_mesh_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	ToolSettings *ts= CTX_data_tool_settings(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	BMesh *bm= em->bm;
	BMOperator spinop;
	float cent[3], axis[3], imat[3][3];
	float d[3] = {0.0f, 0.0f, 0.0f};
	int steps, dupli;
	float degr;
    
	RNA_float_get_array(op->ptr, "center", cent);
	RNA_float_get_array(op->ptr, "axis", axis);
	steps = RNA_int_get(op->ptr, "steps");
	degr = RNA_float_get(op->ptr, "degrees");
	if(ts->editbutflag & B_CLOCKWISE) degr= -degr;
	dupli = RNA_boolean_get(op->ptr, "dupli");
    
	/* undo object transformation */
	copy_m3_m4(imat, obedit->imat);
	sub_v3_v3(cent, obedit->obmat[3]);
	mul_m3_v3(imat, cent);
	mul_m3_v3(imat, axis);

	BMO_InitOpf(bm, &spinop,
		"spin geom=%hvef cent=%v axis=%v dvec=%v steps=%d ang=%f dupli=%d",
	BM_SELECT, cent, axis, d, steps, degr, dupli);
	BMO_Exec_Op(bm, &spinop);
	EDBM_clear_flag_all(em, BM_SELECT);
	BMO_HeaderFlag_Buffer(bm, &spinop, "lastout", BM_SELECT, BM_ALL);
	BMO_Finish_Op(bm, &spinop);

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

/* get center and axis, in global coords */
static int spin_mesh_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	Scene *scene = CTX_data_scene(C);
	View3D *v3d = CTX_wm_view3d(C);
	RegionView3D *rv3d= ED_view3d_context_rv3d(C);

	RNA_float_set_array(op->ptr, "center", give_cursor(scene, v3d));
	RNA_float_set_array(op->ptr, "axis", rv3d->viewinv[2]);

	return spin_mesh_exec(C, op);
}

void MESH_OT_spin(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Spin";
	ot->idname= "MESH_OT_spin";

	/* api callbacks */
	ot->invoke= spin_mesh_invoke;
	ot->exec= spin_mesh_exec;
	ot->poll= EM_view3d_poll;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* props */
	RNA_def_int(ot->srna, "steps", 9, 0, INT_MAX, "Steps", "Steps", 0, INT_MAX);
	RNA_def_boolean(ot->srna, "dupli", 0, "Dupli", "Make Duplicates");
	RNA_def_float(ot->srna, "degrees", 90.0f, -FLT_MAX, FLT_MAX, "Degrees", "Degrees", -360.0f, 360.0f);

	RNA_def_float_vector(ot->srna, "center", 3, NULL, -FLT_MAX, FLT_MAX, "Center", "Center in global view space", -FLT_MAX, FLT_MAX);
	RNA_def_float_vector(ot->srna, "axis", 3, NULL, -1.0f, 1.0f, "Axis", "Axis in global view space", -FLT_MAX, FLT_MAX);

}

static int screw_mesh_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	BMesh *bm= em->bm;
	BMEdge *eed;
	BMVert *eve, *v1, *v2;
	BMIter iter, eiter;
	BMOperator spinop;
	float dvec[3], nor[3], cent[3], axis[3];
	float imat[3][3];
	int steps, turns;
	int valence;


	turns= RNA_int_get(op->ptr, "turns");
	steps= RNA_int_get(op->ptr, "steps");
	RNA_float_get_array(op->ptr, "center", cent);
	RNA_float_get_array(op->ptr, "axis", axis);

	/* undo object transformation */
	copy_m3_m4(imat, obedit->imat);
	sub_v3_v3(cent, obedit->obmat[3]);
	mul_m3_v3(imat, cent);
	mul_m3_v3(imat, axis);


	/* find two vertices with valence count==1, more or less is wrong */
	v1 = NULL;
	v2 = NULL;
	for(eve = BMIter_New(&iter, em->bm, BM_VERTS_OF_MESH, NULL);
	    eve; eve = BMIter_Step(&iter)){

		valence = 0;

		for(eed = BMIter_New(&eiter, em->bm, BM_EDGES_OF_VERT, eve);
		    eed; eed = BMIter_Step(&eiter)){

			if(BM_TestHFlag(eed, BM_SELECT)){
				valence++;
			}

		}

		if(valence == 1){
			if(v1==NULL) v1 = eve;
			else if(v2==NULL) v2= eve;
			else {
				v1= NULL;
				break;
			}
		}
	}

	if(v1==NULL || v2==NULL) {
		BKE_report(op->reports, RPT_ERROR, "You have to select a string of connected vertices too");
		return OPERATOR_CANCELLED;
	}

	/* calculate dvec */
	sub_v3_v3v3(dvec, v1->co, v2->co);
	mul_v3_fl(dvec, 1.0f/steps);

	if(dot_v3v3(nor, dvec)>0.000)
		negate_v3(dvec);

	BMO_InitOpf(bm, &spinop,
		"spin geom=%hvef cent=%v axis=%v dvec=%v steps=%d ang=%f dupli=0",
	BM_SELECT, cent, axis, dvec, turns*steps, 360.0f*turns);
	BMO_Exec_Op(bm, &spinop);
	EDBM_clear_flag_all(em, BM_SELECT);
	BMO_HeaderFlag_Buffer(bm, &spinop, "lastout", BM_SELECT, BM_ALL);
	BMO_Finish_Op(bm, &spinop);

	DAG_id_tag_update(obedit->data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

/* get center and axis, in global coords */
static int screw_mesh_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	Scene *scene = CTX_data_scene(C);
	View3D *v3d = CTX_wm_view3d(C);
	RegionView3D *rv3d= ED_view3d_context_rv3d(C);

	RNA_float_set_array(op->ptr, "center", give_cursor(scene, v3d));
	RNA_float_set_array(op->ptr, "axis", rv3d->viewinv[1]);

	return screw_mesh_exec(C, op);
}

void MESH_OT_screw(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Screw";
	ot->idname= "MESH_OT_screw";

	/* api callbacks */
	ot->invoke= screw_mesh_invoke;
	ot->exec= screw_mesh_exec;
	ot->poll= EM_view3d_poll;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/*props */
	RNA_def_int(ot->srna, "steps", 9, 0, INT_MAX, "Steps", "Steps", 0, 256);
	RNA_def_int(ot->srna, "turns", 1, 0, INT_MAX, "Turns", "Turns", 0, 256);

	RNA_def_float_vector(ot->srna, "center", 3, NULL, -FLT_MAX, FLT_MAX, "Center", "Center in global view space", -FLT_MAX, FLT_MAX);
	RNA_def_float_vector(ot->srna, "axis", 3, NULL, -1.0f, 1.0f, "Axis", "Axis in global view space", -FLT_MAX, FLT_MAX);
}

static int select_by_number_vertices_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh*)obedit->data)->edit_btmesh;
	BMFace *efa;
	BMIter iter;
	int numverts= RNA_int_get(op->ptr, "number");
	int type = RNA_enum_get(op->ptr, "type");

	for(efa = BMIter_New(&iter, em->bm, BM_FACES_OF_MESH, NULL);
	    efa; efa = BMIter_Step(&iter)){

		int select = 0;

		if(type == 0 && efa->len < numverts){
			select = 1;
		}else if(type == 1 && efa->len == numverts){
			select = 1;
		}else if(type == 2 && efa->len > numverts){
			select = 1;
		}

		if(select){
			BM_Select(em->bm, efa, 1);
		}
	}

	EDBM_selectmode_flush(em);

	WM_event_add_notifier(C, NC_GEOM|ND_SELECT, obedit->data);
	return OPERATOR_FINISHED;
}

void MESH_OT_select_by_number_vertices(wmOperatorType *ot)
{
	static const EnumPropertyItem type_items[] = {
	    {0, "LESS", 0, "Less Than", ""},
	    {1, "EQUAL", 0, "Equal To", ""},
	    {2, "GREATER", 0, "Greater Than", ""},
	    {0, NULL, 0, NULL, NULL}
	};

	/* identifiers */
	ot->name= "Select by Number of Vertices";
	ot->description= "Select vertices or faces by vertex count.";
	ot->idname= "MESH_OT_select_by_number_vertices";
	
	/* api callbacks */
	ot->exec= select_by_number_vertices_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* properties */
	RNA_def_int(ot->srna, "number", 4, 3, INT_MAX, "Number of Vertices", "", 3, INT_MAX);
	RNA_def_enum(ot->srna, "type", type_items, 1, "Type", "Type of comparison to make");
}

static int select_loose_verts_exec(bContext *C, wmOperator *UNUSED(op))
{
	Object *obedit = CTX_data_edit_object(C);
	BMEditMesh *em = ((Mesh*)obedit->data)->edit_btmesh;
	BMVert *eve;
	BMEdge *eed;
	BMIter iter;

	for(eve = BMIter_New(&iter, em->bm, BM_VERTS_OF_MESH, NULL);
	    eve; eve = BMIter_Step(&iter)){

		if(!eve->e){
			BM_Select(em->bm, eve, 1);
		}
	}

	for(eed = BMIter_New(&iter, em->bm, BM_EDGES_OF_MESH, NULL);
	    eed; eed = BMIter_Step(&iter)){

		if(!eed->l){
			BM_Select(em->bm, eed, 1);
		}
	}

	EDBM_selectmode_flush(em);

	WM_event_add_notifier(C, NC_GEOM|ND_SELECT, obedit->data);
	return OPERATOR_FINISHED;
}

void MESH_OT_select_loose_verts(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Select Loose Vertices/Edges";
	ot->description = "Select vertices with edges or faces and edges with no faces";
	ot->idname = "MESH_OT_select_loose_verts";

	/* api callbacks */
	ot->exec = select_loose_verts_exec;
	ot->poll = ED_operator_editmesh;

	/* flags */
	ot->flag = OPTYPE_REGISTER|OPTYPE_UNDO;
}

#define MIRROR_THRESH	1.0f

static int select_mirror_exec(bContext *C, wmOperator *op)
{
	
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
	BMBVHTree *tree = BMBVH_NewBVH(em);
	BMVert *v1, *v2;
	BMIter iter;
	int extend= RNA_boolean_get(op->ptr, "extend");
	float mirror_co[3];

	BM_ITER(v1, &iter, em->bm, BM_VERTS_OF_MESH, NULL) {
		if (!BM_TestHFlag(v1, BM_SELECT) || BM_TestHFlag(v1, BM_HIDDEN))
			BM_SetIndex(v1, 0);
		else BM_SetIndex(v1, 1);
	}

	if (!extend)
		EDBM_clear_flag_all(em, BM_SELECT);

	BM_ITER(v1, &iter, em->bm, BM_VERTS_OF_MESH, NULL) {
		if (!BM_GetIndex(v1) || BM_TestHFlag(v1, BM_HIDDEN))
			continue;

		VECCOPY(mirror_co, v1->co);
		mirror_co[0] *= -1.0f;

		v2 = BMBVH_FindClosestVertTopo(tree, mirror_co, MIRROR_THRESH, v1);
		if (v2 && !BM_TestHFlag(v2, BM_HIDDEN))
			BM_Select(em->bm, v2, 1);
	}

	WM_event_add_notifier(C, NC_GEOM|ND_SELECT, obedit->data);
	return OPERATOR_FINISHED;
}

void MESH_OT_select_mirror(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Select Mirror";
	ot->description= "Select mesh items at mirrored locations.";
	ot->idname= "MESH_OT_select_mirror";

	/* api callbacks */
	ot->exec= select_mirror_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* props */
	RNA_def_boolean(ot->srna, "extend", 0, "Extend", "Extend the existing selection");
}

/********* qsort routines.  not sure how to make these
           work, since we aren't using linked lists for
           geometry anymore.  might need a sortof "swap"
           function for bmesh elements.           *********/

typedef struct xvertsort {
	float x;
	BMVert *v1;
} xvertsort;


static int vergxco(const void *v1, const void *v2)
{
	const xvertsort *x1=v1, *x2=v2;

	if( x1->x > x2->x ) return 1;
	else if( x1->x < x2->x) return -1;
	return 0;
}

struct facesort {
	uintptr_t x;
	struct EditFace *efa;
};

#if 0 /* UNUSED */
static int vergface(const void *v1, const void *v2)
{
	const struct facesort *x1=v1, *x2=v2;

	if( x1->x > x2->x ) return 1;
	else if( x1->x < x2->x) return -1;
	return 0;
}
#endif

// XXX is this needed?
/* called from buttons */
#if 0 /* UNUSED */
static void xsortvert_flag__doSetX(void *userData, EditVert *UNUSED(eve), int x, int UNUSED(y), int index)
{
	xvertsort *sortblock = userData;

	sortblock[index].x = x;
}
#endif

/* all verts with (flag & 'flag') are sorted */
static void xsortvert_flag(bContext *UNUSED(C), int UNUSED(flag))
{
	/*BMESH_TODO*/
#if 0 //hrm, geometry isn't in linked lists anymore. . .
	ViewContext vc;
	BMEditMesh *em;
	BMVert *eve;
	BMIter iter;
	xvertsort *sortblock;
	ListBase tbase;
	int i, amount;

	em_setup_viewcontext(C, &vc);
	em = vc.em;

	amount = em->bm->totvert;
	sortblock = MEM_callocN(sizeof(xvertsort)*amount,"xsort");
	BM_ITER(eve, &iter, em->bm, BM_VERTS_OF_MESH, NULL) {
		if(BM_TestHFlag(eve, BM_SELECT))
			sortblock[i].v1 = eve;
	}
	
	ED_view3d_init_mats_rv3d(vc.obedit, vc.rv3d);
	mesh_foreachScreenVert(&vc, xsortvert_flag__doSetX, sortblock, 0);

	qsort(sortblock, amount, sizeof(xvertsort), vergxco);

		/* make temporal listbase */
	tbase.first= tbase.last= 0;
	for (i=0; i<amount; i++) {
		eve = sortblock[i].v1;

		if (eve) {
			BLI_remlink(&vc.em->verts, eve);
			BLI_addtail(&tbase, eve);
		}
	}

	BLI_movelisttolist(&vc.em->verts, &tbase);

	MEM_freeN(sortblock);
#endif

}

static int mesh_vertices_sort_exec(bContext *C, wmOperator *UNUSED(op))
{
	xsortvert_flag(C, SELECT);
	return OPERATOR_FINISHED;
}

void MESH_OT_vertices_sort(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Vertex Sort";
	ot->description= "Sort vertex order";
	ot->idname= "MESH_OT_vertices_sort";

	/* api callbacks */
	ot->exec= mesh_vertices_sort_exec;

	ot->poll= EM_view3d_poll; /* uses view relative X axis to sort verts */

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

#if 0
/* called from buttons */
static void hashvert_flag(EditMesh *em, int flag)
{
	/* switch vertex order using hash table */
	EditVert *eve;
	struct xvertsort *sortblock, *sb, onth, *newsort;
	ListBase tbase;
	int amount, a, b;

	/* count */
	eve= em->verts.first;
	amount= 0;
	while(eve) {
		if(eve->f & flag) amount++;
		eve= eve->next;
	}
	if(amount==0) return;

	/* allocate memory */
	sb= sortblock= (struct xvertsort *)MEM_mallocN(sizeof(struct xvertsort)*amount,"sortremovedoub");
	eve= em->verts.first;
	while(eve) {
		if(eve->f & flag) {
			sb->v1= eve;
			sb++;
		}
		eve= eve->next;
	}

	BLI_srand(1);

	sb= sortblock;
	for(a=0; a<amount; a++, sb++) {
		b= (int)(amount*BLI_drand());
		if(b>=0 && b<amount) {
			newsort= sortblock+b;
			onth= *sb;
			*sb= *newsort;
			*newsort= onth;
		}
	}

	/* make temporal listbase */
	tbase.first= tbase.last= 0;
	sb= sortblock;
	while(amount--) {
		eve= sb->v1;
		BLI_remlink(&em->verts, eve);
		BLI_addtail(&tbase, eve);
		sb++;
	}

	BLI_movelisttolist(&em->verts, &tbase);

	MEM_freeN(sortblock);

}
#endif

static int mesh_vertices_randomize_exec(bContext *C, wmOperator *UNUSED(op))
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= ((Mesh *)obedit->data)->edit_btmesh;
#if 1 /*BMESH TODO*/
	(void)em;
#else
	hashvert_flag(em, SELECT);
#endif
	return OPERATOR_FINISHED;
}

void MESH_OT_vertices_randomize(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Vertex Randomize";
	ot->description= "Randomize vertex order";
	ot->idname= "MESH_OT_vertices_randomize";

	/* api callbacks */
	ot->exec= mesh_vertices_randomize_exec;

	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/******end of qsort stuff ****/


static int mesh_noise_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= (((Mesh *)obedit->data))->edit_btmesh;
	Material *ma;
	Tex *tex;
	BMVert *eve;
	BMIter iter;
	float fac= RNA_float_get(op->ptr, "factor");

	if(em==NULL) return OPERATOR_FINISHED;

	ma= give_current_material(obedit, obedit->actcol);
	if(ma==0 || ma->mtex[0]==0 || ma->mtex[0]->tex==0) {
		BKE_report(op->reports, RPT_WARNING, "Mesh has no material or texture assigned.");
		return OPERATOR_FINISHED;
	}
	tex= give_current_material_texture(ma);

	if(tex->type==TEX_STUCCI) {
		float b2, vec[3];
		float ofs= tex->turbul/200.0;
		BM_ITER(eve, &iter, em->bm, BM_VERTS_OF_MESH, NULL) {
			if (BM_TestHFlag(eve, BM_SELECT) && !BM_TestHFlag(eve, BM_HIDDEN)) {
				b2= BLI_hnoise(tex->noisesize, eve->co[0], eve->co[1], eve->co[2]);
				if(tex->stype) ofs*=(b2*b2);
				vec[0]= fac*(b2-BLI_hnoise(tex->noisesize, eve->co[0]+ofs, eve->co[1], eve->co[2]));
				vec[1]= fac*(b2-BLI_hnoise(tex->noisesize, eve->co[0], eve->co[1]+ofs, eve->co[2]));
				vec[2]= fac*(b2-BLI_hnoise(tex->noisesize, eve->co[0], eve->co[1], eve->co[2]+ofs));
				
				add_v3_v3(eve->co, vec);
			}
		}
	}
	else {
		BM_ITER(eve, &iter, em->bm, BM_VERTS_OF_MESH, NULL) {
			if (BM_TestHFlag(eve, BM_SELECT) && !BM_TestHFlag(eve, BM_HIDDEN)) {
				float tin, dum;
				externtex(ma->mtex[0], eve->co, &tin, &dum, &dum, &dum, &dum, 0);
				eve->co[2]+= fac*tin;
			}
		}
	}

	EDBM_RecalcNormals(em);

	DAG_id_tag_update(obedit->data, 0);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_noise(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Noise";
	ot->description= "Use vertex coordinate as texture coordinate";
	ot->idname= "MESH_OT_noise";

	/* api callbacks */
	ot->exec= mesh_noise_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	RNA_def_float(ot->srna, "factor", 0.1f, -FLT_MAX, FLT_MAX, "Factor", "", 0.0f, 1.0f);
}

/*bevel! yay!!*/
static int mesh_bevel_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	BMEditMesh *em= (((Mesh *)obedit->data))->edit_btmesh;
	BMIter iter;
	BMEdge *eed;
	BMOperator bmop;
	float factor= RNA_float_get(op->ptr, "percent"), fac=factor, dfac, df, s;
	/*float p2 = RNA_float_get(op->ptr, "param2");
	float p3 = RNA_float_get(op->ptr, "param3");
	float p4 = RNA_float_get(op->ptr, "param4");
	float p5 = RNA_float_get(op->ptr, "param5");*/
	int i, recursion = RNA_int_get(op->ptr, "recursion");
	float *w = NULL, ftot;
	int li;
	BLI_array_declare(w);
	
	BM_add_data_layer(em->bm, &em->bm->edata, CD_PROP_FLT);
	li = CustomData_number_of_layers(&em->bm->edata, CD_PROP_FLT)-1;
	
	BM_ITER(eed, &iter, em->bm, BM_EDGES_OF_MESH, NULL) {
		float d = len_v3v3(eed->v1->co, eed->v2->co);
		float *dv = CustomData_bmesh_get_n(&em->bm->edata, eed->head.data, CD_PROP_FLT, li);
		
		*dv = d;
	}
	
	if(em==NULL) return OPERATOR_CANCELLED;
	
	/*ugh, stupid math depends somewhat on angles!*/
	dfac = 1.0/(float)(recursion+1);
	df = 1.0;
	for (i=0, ftot=0.0f; i<recursion; i++) {
		s = pow(df, 1.25);
		
		BLI_array_append(w, s);
		ftot += s;
		
		df *= 2.0;
	}
	
	for (i=0; i<BLI_array_count(w); i++) {
		w[i] /= ftot;
	}

	fac = factor;
	for (i=0; i<BLI_array_count(w); i++) {
		fac = w[BLI_array_count(w)-i-1]*factor;

		if (!EDBM_InitOpf(em, &bmop, op, "bevel geom=%hev percent=%f lengthlayer=%i uselengths=%i", BM_SELECT, fac, li, 1))
			return OPERATOR_CANCELLED;
		
		BMO_Exec_Op(em->bm, &bmop);
		BMO_Finish_Op(em->bm, &bmop);
	}
	
	BM_free_data_layer_n(em->bm, &em->bm->edata, CD_MASK_PROP_FLT, li);
	
	BLI_array_free(w);
	EDBM_RecalcNormals(em);

	DAG_id_tag_update(obedit->data, 0);
	WM_event_add_notifier(C, NC_GEOM|ND_DATA, obedit->data);

	return OPERATOR_FINISHED;
}

void MESH_OT_bevel(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Bevel";
	ot->description= "Edge/Vertex Bevel";
	ot->idname= "MESH_OT_bevel";

	/* api callbacks */
	ot->exec= mesh_bevel_exec;
	ot->poll= ED_operator_editmesh;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	RNA_def_float(ot->srna, "percent", 0.5f, -FLT_MAX, FLT_MAX, "Percentage", "", 0.0f, 1.0f);
	RNA_def_int(ot->srna, "recursion", 1, 1, 50, "Recursion Level", "Recursion Level", 1, 8);
	//RNA_def_float(ot->srna, "param2", 1.0f, -FLT_MAX, FLT_MAX, "Parameter 2", "", -1000.0f, 1000.0f);
	//RNA_def_float(ot->srna, "param3", 0.5f, -FLT_MAX, FLT_MAX, "Parameter 3", "", -1000.0f, 1000.0f);
	//RNA_def_float(ot->srna, "param4", 0.5f, -FLT_MAX, FLT_MAX, "Parameter 4", "", -1000.0f, 1000.0f);
	//RNA_def_float(ot->srna, "param5", 0.5f, -FLT_MAX, FLT_MAX, "Parameter 5", "", -1000.0f, 1000.0f);
}

static int mesh_export_obj_exec(bContext *C, wmOperator *op)
{
	Object *ob = CTX_data_active_object(C);
	DerivedMesh *dm;
	Scene *scene = CTX_data_scene(C);
	Mesh *me;
	Main *bmain = CTX_data_main(C);
	MVert *mvert, *mv;
	MLoop *mloop, *ml;
	MPoly *mpoly, *mp;
	MTexPoly *mtexpoly;
	MLoopUV *luv, *mloopuv;
	MLoopCol *mloopcol;
	FILE *file, *matfile;
	int *face_mat_group;
	struct {Material *mat; MTexPoly poly; int end;} **matlists;
	char str[FILE_MAX], str2[FILE_MAX];
	int i, j, c, free;
	
	if (ob->type != OB_MESH) {
		BKE_report(op->reports, RPT_OPERATOR, "Only meshes can be exported");
		return OPERATOR_CANCELLED;
	}
	
	RNA_string_get(op->ptr, "filepath", str);
	
	sprintf(str2, "%s_materials.mtl", str);
	file = fopen(str, "wb");
	matfile = fopen(str2, "wb");
	
	if (!file) {
		BKE_report(op->reports, RPT_OPERATOR, "Could not open file");
		
		if (matfile)
			fclose(matfile);
		return OPERATOR_CANCELLED;
	}
	
	if (!matfile) {
		BKE_report(op->reports, RPT_OPERATOR, "Could not open material file");
		
		if (file)
			fclose(file);
		return OPERATOR_CANCELLED;
	}
	
	me = ob->data;
	if (me->edit_btmesh) {
		EDBM_LoadEditBMesh(scene, ob);
	}
	
	if (!RNA_boolean_get(op->ptr, "apply_modifiers")) {
		dm = CDDM_from_mesh(me, ob);
		free = 1;
	} else {
		dm = mesh_get_derived_final(scene, ob, CD_MASK_DERIVEDMESH);
		if (!CDDM_Check(dm)) {
			dm = CDDM_copy(dm, 0);
			free = 1;
		} else {
			free = 0;
		}
	}
	
	face_mat_group = MEM_callocN(sizeof(int)*dm->numPolyData, "face_mat_group");
	
	if (MAX2(ob->totcol, me->totcol))
		matlists = MEM_callocN(sizeof(*matlists)*MAX2(me->totcol, ob->totcol), "matlists");
	else matlists = NULL;
	
	for (i=0; i<MAX2(ob->totcol, me->totcol); i++) {
		matlists[i] = MEM_callocN(sizeof(**matlists), "matlists[i]");
		matlists[i][0].end = 1;
	}
	
	
	mvert = CDDM_get_verts(dm);
	mloop = CDDM_get_loops(dm);
	mpoly = CDDM_get_polys(dm);
	mtexpoly = CustomData_get_layer(&dm->polyData, CD_MTEXPOLY);
	mloopuv = CustomData_get_layer(&dm->loopData, CD_MLOOPUV);
	mloopcol = CustomData_get_layer(&dm->loopData, CD_MLOOPCOL);
	
	/*build material list*/
	mp = mpoly;
	for (i=0; i<dm->numPolyData; i++, (mtexpoly ? mtexpoly++ : NULL), mp++) {
		int found = 0;
		
		j = 0;
		while (!matlists[mp->mat_nr][j].end) {
			Material *mat = ob->matbits[mp->mat_nr] ? ob->mat[mp->mat_nr] : me->mat[mp->mat_nr];
			
			if (matlists[mp->mat_nr][j].mat == mat) {
				if (mtexpoly) { 
					if (matlists[mp->mat_nr][j].poly.tpage == mtexpoly->tpage) {
						found = 1;
						break;
					}
				} else {
					found = 1;
					break;
				}
			}
			j++;
		}
		
		if (!found) {
			matlists[mp->mat_nr] = MEM_reallocN(matlists[mp->mat_nr], sizeof(**matlists)*(j+2));
			
			/*add sentinal*/
			matlists[mp->mat_nr][j+1].end = 1;
			matlists[mp->mat_nr][j].end = 0;
			
			if (ob->matbits && ob->matbits[mp->mat_nr]) {
				matlists[mp->mat_nr][j].mat = ob->mat[mp->mat_nr];
			} else {
				matlists[mp->mat_nr][j].mat = me->mat[mp->mat_nr];
			}
			
			if (mtexpoly)
				matlists[mp->mat_nr][j].poly = *mtexpoly;
		}
		
		face_mat_group[i] = j;
	}

	/*write material references*/
	fprintf(file, "mtllib %s_materials.mtl\n", str);
	fprintf(file, "o %s\n", (ob->id.name+2));
	
	for (mv=mvert, i=0; i<dm->numVertData; i++, mv++) {
		fprintf(file, "v %.8f\t%.8f\t%.8f\n", mv->co[0], mv->co[1], mv->co[2]);
		fprintf(file, "vn %.5f\t%.5f\t%.5f\n", (float)mv->no[0]/65535.0f, (float)mv->no[1]/65535.0f, (float)mv->no[2]/65535.0f);
	}

	/*write texture coordinates*/
	if (mloopuv) {
		fprintf(file, "\n");
		for (mp=mpoly, i=0; i<dm->numPolyData; i++, mp++) {
			luv = mloopuv + mp->loopstart;
			for (j=0; j<mp->totloop; j++, luv++) {
				fprintf(file, "vt %.8f\t%.8f\n", luv->uv[0], luv->uv[1]);
			}
		}
	}
	
	fprintf(file, "\n");
	c = 0;
	for (mp=mpoly, i=0; i<dm->numPolyData; i++, mp++) {
		char matname[256];
		
		if (mp->flag & ME_SMOOTH) {
			fprintf(file, "s 1\n");
		} else {
			fprintf(file, "s off\n");
		}
		
		if (matlists[mp->mat_nr][face_mat_group[i]].mat && matlists[mp->mat_nr][face_mat_group[i]].poly.tpage) {
			sprintf(matname, "%s__%s", matlists[mp->mat_nr][face_mat_group[i]].mat->id.name+2, 
				matlists[mp->mat_nr][face_mat_group[i]].poly.tpage->id.name+2);
		} else if (matlists[mp->mat_nr][face_mat_group[i]].mat) {
			sprintf(matname, "%s", matlists[mp->mat_nr][face_mat_group[i]].mat->id.name+2);
		} else if (matlists[mp->mat_nr][face_mat_group[i]].poly.tpage != NULL) {
			sprintf(matname, "texture_%s", matlists[mp->mat_nr][face_mat_group[i]].poly.tpage->id.name+2);
		} else {
			sprintf(matname, "__null_material_%d_%d", mp->mat_nr, face_mat_group[mp->mat_nr]);
		}
		
		fprintf(file, "usemtl %s\n", matname);
		fprintf(file, "f ");
		
		ml = mloop + mp->loopstart;
		luv = mloopuv ? mloopuv + mp->loopstart : NULL;
		for (j=0; j<mp->totloop; j++, ml++, (luv ? luv++ : NULL), c++) {
			if (luv) {
				fprintf(file, "%d/%d ", ml->v+1, c+1);
			} else {
				fprintf(file, "%d ", ml->v+1);
			}
		}
		fprintf(file, "\n");
	}
	
	fclose(file);
	
	/*write material library*/
	fprintf(matfile, "#Blender MTL File\n\n");
	for (i=0; i<MAX2(ob->totcol, me->totcol); i++) {
		Material *mat;
		char basedir[FILE_MAX], filename[FILE_MAX], str3[FILE_MAX];
		
		j = 0;
		while (!matlists[i][j].end) {
			mat = matlists[i][j].mat;
			
			if (mat && matlists[i][j].poly.tpage) {
				fprintf(matfile, "newmtl %s__%s\n", mat->id.name+2, 
					matlists[i][j].poly.tpage->id.name+2);
			} else if (mat) {
				fprintf(matfile, "newmtl %s\n", mat->id.name+2);
			} else if (matlists[i][j].poly.tpage != NULL) {
				fprintf(matfile, "newmtl texture_%s\n", matlists[i][j].poly.tpage->id.name+2);
			} else {
				fprintf(matfile, "newmtl __null_material_%d_%d\n", i, j);
			}

			if (mat) {
				fprintf(matfile, "Kd %.6f %.6f %.6f\n", mat->r, mat->g, mat->b);
				fprintf(matfile, "Ks %.6f %.6f %.6f\n", mat->specr, mat->specg, mat->specb);
				fprintf(matfile, "Ns %.6f\n", mat->spec*1000.0f);
			} else {
				fprintf(matfile, "Kd %.6f %.6f %.6f\n", 0.45f, 0.45f, 0.45f);
				fprintf(matfile, "Ks %.6f %.6f %.6f\n", 1.0f, 0.4f, 0.1f);
				fprintf(matfile, "Ns %.6f\n", 300.0f);
			}

			fprintf(matfile, "illum 2\n");
			
			if (matlists[i][j].poly.tpage) {
				BLI_strncpy(str2, matlists[i][j].poly.tpage->name, FILE_MAX);
				BLI_strncpy(basedir, bmain->name, FILE_MAX);
				
				BLI_splitdirstring(basedir, filename);
				BLI_cleanup_file(basedir, str2); /* fix any /foo/../foo/ */
				
				if (BLI_exists(str2)) {
					char rel[3] = {0};
					
					BLI_strncpy(str3, str2, FILE_MAX);
					if (RNA_boolean_get(op->ptr, "relpaths")) {
						BLI_path_rel(str3, str);
						
						if (str3[2] != '.' && str3[2] != '/' && str3[2] != '\\') {
							rel[0] = '.';
							rel[1] = '/';
						}
					}
						
					fprintf(matfile, "map_Ka %s%s\n", rel, (str3+2*RNA_boolean_get(op->ptr, "relpaths")));
					fprintf(matfile, "map_Kd %s%s\n", rel, (str3+2*RNA_boolean_get(op->ptr, "relpaths")));
				}
			}
			
			fprintf(matfile, "\n");
			j++;
		}
	}
	
	fclose(matfile);
	
	for (i=0; i<MAX2(ob->totcol, me->totcol); i++) {
		MEM_freeN(matlists[i]);
	}
	
	if (matlists)
		MEM_freeN(matlists);
	
	if (face_mat_group)
		MEM_freeN(face_mat_group);

	if (free) {
		dm->needsFree = 1;
		dm->release(dm);
	}
	
	return OPERATOR_FINISHED;
}

static void export_obj_filesel(bContext *C, wmOperator *op, const char *path)
{
	RNA_string_set(op->ptr, "filepath", path);
	WM_event_add_fileselect(C, op); 
}


static int export_obj_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	char filename[FILE_MAX];
	
	BLI_strncpy(filename, "//untitled.obj", FILE_MAX);

	if(RNA_property_is_set(op->ptr, "filepath"))
		return mesh_export_obj_exec(C, op);
	
	export_obj_filesel(C, op, filename);

	return OPERATOR_RUNNING_MODAL;
}


void EXPORT_MESH_OT_wavefront(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Export Wavefront OBJ";
	ot->description= "Export Wavefront (obj)";
	ot->idname= "EXPORT_MESH_OT_wavefront";

	/* api callbacks */
	ot->exec= mesh_export_obj_exec;
	ot->invoke= export_obj_invoke;
	ot->poll= ED_operator_object_active;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* properties */
	WM_operator_properties_filesel(ot, FOLDERFILE|TEXTFILE, FILE_SPECIAL, FILE_SAVE, WM_FILESEL_FILEPATH);
	
	RNA_def_boolean(ot->srna, "apply_modifiers", 0, "Apply Modifiers", "Apply Modifiers");
	RNA_def_boolean(ot->srna, "relpaths", 0, "Relative Paths", "Use relative paths for textures");
}
