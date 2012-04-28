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
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 *
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_view3d/view3d_buttons.c
 *  \ingroup spview3d
 */


#include <string.h>
#include <stdio.h>
#include <math.h>
#include <float.h>

#include "DNA_armature_types.h"
#include "DNA_curve_types.h"
#include "DNA_lattice_types.h"
#include "DNA_meta_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "MEM_guardedalloc.h"

#include "BLF_translation.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"
#include "BLI_rand.h"
#include "BLI_utildefines.h"

#include "BKE_action.h"
#include "BKE_context.h"
#include "BKE_curve.h"
#include "BKE_customdata.h"
#include "BKE_depsgraph.h"
#include "BKE_main.h"
#include "BKE_mesh.h"
#include "BKE_screen.h"
#include "BKE_tessmesh.h"
#include "BKE_deform.h"
#include "BKE_object.h"

#include "WM_api.h"
#include "WM_types.h"

#include "RNA_access.h"

#include "ED_armature.h"
#include "ED_gpencil.h"
#include "ED_mesh.h"
#include "ED_screen.h"
#include "ED_transform.h"
#include "ED_curve.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "view3d_intern.h"  /* own include */


/* ******************* view3d space & buttons ************** */
#define B_NOP       		1
#define B_REDR      		2
#define B_OBJECTPANELMEDIAN 1008

/* temporary struct for storing transform properties */
typedef struct {
	float ob_eul[4];   /* used for quat too... */
	float ob_scale[3]; /* need temp space due to linked values */
	float ob_dims[3];
	short link_scale;
	float ve_median[7];
	int curdef;
	float *defweightp;
} TransformProperties;

/* Helper function to compute a median changed value,
 * when the value should be clamped in [0.0, 1.0].
 * Returns either 0.0, 1.0 (both can be applied directly), a positive scale factor
 * for scale down, or a negative one for scale up.
 */
static float compute_scale_factor(const float ve_median, const float median)
{
	if (ve_median <= 0.0f)
		return 0.0f;
	else if (ve_median >= 1.0f)
		return 1.0f;
	else {
		/* Scale value to target median. */
		float median_new = ve_median;
		float median_orig = ve_median - median; /* Previous median value. */

		/* In case of floating point error. */
		CLAMP(median_orig, 0.0f, 1.0f);
		CLAMP(median_new, 0.0f, 1.0f);

		if (median_new <= median_orig) {
			/* Scale down. */
			return median_new / median_orig;
		}
		else {
			/* Scale up, negative to indicate it... */
			return -(1.0f - median_new) / (1.0f - median_orig);
		}
	}
}

/* is used for both read and write... */
static void v3d_editvertex_buts(uiLayout *layout, View3D *v3d, Object *ob, float lim)
{
	uiBlock *block = (layout) ? uiLayoutAbsoluteBlock(layout) : NULL;
	MDeformVert *dvert = NULL;
	TransformProperties *tfp;
	float median[7], ve_median[7];
	int tot, totw, totweight, totedge, totradius;
	char defstr[320];
	PointerRNA radius_ptr;

	median[0] = median[1] = median[2] = median[3] = median[4] = median[5] = median[6] = 0.0;
	tot = totw = totweight = totedge = totradius = 0;
	defstr[0] = 0;

	/* make sure we got storage */
	if (v3d->properties_storage == NULL)
		v3d->properties_storage = MEM_callocN(sizeof(TransformProperties), "TransformProperties");
	tfp = v3d->properties_storage;

	if (ob->type == OB_MESH) {
		Mesh *me = ob->data;
		BMEditMesh *em = me->edit_btmesh;
		BMesh *bm = em->bm;
		BMVert *eve, *evedef = NULL;
		BMEdge *eed;
		BMIter iter;

		BM_ITER_MESH (eve, &iter, bm, BM_VERTS_OF_MESH) {
			if (BM_elem_flag_test(eve, BM_ELEM_SELECT)) {
				evedef = eve;
				tot++;
				add_v3_v3(median, eve->co);
			}
		}

		BM_ITER_MESH (eed, &iter, bm, BM_EDGES_OF_MESH) {
			if (BM_elem_flag_test(eed, BM_ELEM_SELECT)) {
				float *f;

				totedge++;
				f = (float *)CustomData_bmesh_get(&bm->edata, eed->head.data, CD_CREASE);
				median[3] += f ? *f : 0.0f;

				f = (float *)CustomData_bmesh_get(&bm->edata, eed->head.data, CD_BWEIGHT);
				median[6] += f ? *f : 0.0f;
			}
		}

		/* check for defgroups */
		if (evedef)
			dvert = CustomData_bmesh_get(&bm->vdata, evedef->head.data, CD_MDEFORMVERT);
		if (tot == 1 && dvert && dvert->totweight) {
			bDeformGroup *dg;
			int i, max = 1, init = 1;
			char str[320];

			for (i = 0; i < dvert->totweight; i++) {
				dg = BLI_findlink(&ob->defbase, dvert->dw[i].def_nr);
				if (dg) {
					max += BLI_snprintf(str, sizeof(str), "%s %%x%d|", dg->name, dvert->dw[i].def_nr);
					if (max < sizeof(str)) strcat(defstr, str);
				}

				if (tfp->curdef == dvert->dw[i].def_nr) {
					init = 0;
					tfp->defweightp = &dvert->dw[i].weight;
				}
			}

			if (init) { /* needs new initialized */
				tfp->curdef = dvert->dw[0].def_nr;
				tfp->defweightp = &dvert->dw[0].weight;
			}
		}
	}
	else if (ob->type == OB_CURVE || ob->type == OB_SURF) {
		Curve *cu = ob->data;
		Nurb *nu;
		BPoint *bp;
		BezTriple *bezt;
		int a;
		ListBase *nurbs = BKE_curve_editNurbs_get(cu);
		StructRNA *seltype = NULL;
		void *selp = NULL;

		nu = nurbs->first;
		while (nu) {
			if (nu->type == CU_BEZIER) {
				bezt = nu->bezt;
				a = nu->pntsu;
				while (a--) {
					if (bezt->f2 & SELECT) {
						add_v3_v3(median, bezt->vec[1]);
						tot++;
						median[4] += bezt->weight;
						totweight++;
						median[5] += bezt->radius;
						totradius++;
						selp = bezt;
						seltype = &RNA_BezierSplinePoint;
					}
					else {
						if (bezt->f1 & SELECT) {
							add_v3_v3(median, bezt->vec[0]);
							tot++;
						}
						if (bezt->f3 & SELECT) {
							add_v3_v3(median, bezt->vec[2]);
							tot++;
						}
					}
					bezt++;
				}
			}
			else {
				bp = nu->bp;
				a = nu->pntsu * nu->pntsv;
				while (a--) {
					if (bp->f1 & SELECT) {
						add_v3_v3(median, bp->vec);
						median[3] += bp->vec[3];
						totw++;
						tot++;
						median[4] += bp->weight;
						totweight++;
						median[5] += bp->radius;
						totradius++;
						selp = bp;
						seltype = &RNA_SplinePoint;
					}
					bp++;
				}
			}
			nu = nu->next;
		}

		if (totradius == 1)
			RNA_pointer_create(&cu->id, seltype, selp, &radius_ptr);
	}
	else if (ob->type == OB_LATTICE) {
		Lattice *lt = ob->data;
		BPoint *bp;
		int a;

		a = lt->editlatt->latt->pntsu * lt->editlatt->latt->pntsv * lt->editlatt->latt->pntsw;
		bp = lt->editlatt->latt->def;
		while (a--) {
			if (bp->f1 & SELECT) {
				add_v3_v3(median, bp->vec);
				tot++;
				median[4] += bp->weight;
				totweight++;
			}
			bp++;
		}
	}

	if (tot == 0) {
		uiDefBut(block, LABEL, 0, IFACE_("Nothing selected"), 0, 130, 200, 20, NULL, 0, 0, 0, 0, "");
		return;
	}
	median[0] /= (float)tot;
	median[1] /= (float)tot;
	median[2] /= (float)tot;
	if (totedge) {
		median[3] /= (float)totedge;
		median[6] /= (float)totedge;
	}
	else if (totw)
		median[3] /= (float)totw;
	if (totweight)
		median[4] /= (float)totweight;
	if (totradius)
		median[5] /= (float)totradius;

	if (v3d->flag & V3D_GLOBAL_STATS)
		mul_m4_v3(ob->obmat, median);

	if (block) { /* buttons */
		uiBut *but;
		int yi = 200;
		const int buth = 20 * UI_DPI_ICON_FAC;
		const int but_margin = 2;

		memcpy(tfp->ve_median, median, sizeof(tfp->ve_median));

		uiBlockBeginAlign(block);
		if (tot == 1) {
			uiDefBut(block, LABEL, 0, IFACE_("Vertex:"), 0, yi -= buth, 200, buth, NULL, 0, 0, 0, 0, "");
		}
		else {
			uiDefBut(block, LABEL, 0, IFACE_("Median:"), 0, yi -= buth, 200, buth, NULL, 0, 0, 0, 0, "");
		}

		uiBlockBeginAlign(block);

		/* Should be no need to translate these. */
		but = uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "X:", 0, yi -= buth, 200, buth,
		                &(tfp->ve_median[0]), -lim, lim, 10, RNA_TRANSLATION_PREC_DEFAULT, "");
		uiButSetUnitType(but, PROP_UNIT_LENGTH);
		but = uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Y:", 0, yi -= buth, 200, buth,
		                &(tfp->ve_median[1]), -lim, lim, 10, RNA_TRANSLATION_PREC_DEFAULT, "");
		uiButSetUnitType(but, PROP_UNIT_LENGTH);
		but = uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "Z:",0, yi -= buth, 200, buth,
		                &(tfp->ve_median[2]), -lim, lim, 10, RNA_TRANSLATION_PREC_DEFAULT, "");
		uiButSetUnitType(but, PROP_UNIT_LENGTH);

		if (totw == tot) {
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, "W:", 0, yi -= buth, 200, buth,
			          &(tfp->ve_median[3]), 0.01, 100.0, 1, 3, "");
		}

		uiBlockBeginAlign(block);
		uiDefButBitS(block, TOG, V3D_GLOBAL_STATS, B_REDR, IFACE_("Global"),
		             0, yi -= buth + but_margin, 100, buth,
		             &v3d->flag, 0, 0, 0, 0, "Displays global values");
		uiDefButBitS(block, TOGN, V3D_GLOBAL_STATS, B_REDR, IFACE_("Local"),
		             100, yi, 100, buth,
		             &v3d->flag, 0, 0, 0, 0, "Displays local values");
		uiBlockEndAlign(block);

		if (totweight == 1) {
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, IFACE_("Weight:"),
			          0, yi -= buth + but_margin, 200, buth,
			          &(tfp->ve_median[4]), 0.0, 1.0, 1, 3, TIP_("Weight used for SoftBody Goal"));
		}
		else if (totweight > 1) {
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, IFACE_("Mean Weight:"),
			          0, yi -= buth, 200, buth,
			          &(tfp->ve_median[4]), 0.0, 1.0, 1, 3, TIP_("Weight used for SoftBody Goal"));
		}

		if (totradius == 1) {
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, IFACE_("Radius:"),
			          0, yi -= buth + but_margin, 200, buth,
			          &(tfp->ve_median[5]), 0.0, 100.0, 1, 3, TIP_("Radius of curve control points"));
		}
		else if (totradius > 1) {
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, IFACE_("Mean Radius:"),
			          0, yi -= buth + but_margin, 200, buth,
			          &(tfp->ve_median[5]), 0.0, 100.0, 1, 3, TIP_("Radius of curve control points"));
		}

		if (totedge == 1) {
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, IFACE_("Crease:"),
			          0, yi -= buth + but_margin, 200, buth,
			          &(tfp->ve_median[3]), 0.0, 1.0, 1, 3, TIP_("Weight used by SubSurf modifier"));
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, IFACE_("Bevel Weight:"),
			          0, yi -= buth + but_margin, 200, buth,
			          &(tfp->ve_median[6]), 0.0, 1.0, 1, 3, TIP_("Weight used by Bevel modifier"));
		}
		else if (totedge > 1) {
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, IFACE_("Mean Crease:"),
			          0, yi -= buth + but_margin, 200, buth,
			          &(tfp->ve_median[3]), 0.0, 1.0, 1, 3, TIP_("Weight used by SubSurf modifier"));
			uiDefButF(block, NUM, B_OBJECTPANELMEDIAN, IFACE_("Mean Bevel Weight:"),
			          0, yi -= buth + but_margin, 200, buth,
			          &(tfp->ve_median[6]), 0.0, 1.0, 1, 3, TIP_("Weight used by Bevel modifier"));
		}

		uiBlockEndAlign(block);
		uiBlockEndAlign(block);

	}
	else { /* apply */
		memcpy(ve_median, tfp->ve_median, sizeof(tfp->ve_median));

		if (v3d->flag & V3D_GLOBAL_STATS) {
			invert_m4_m4(ob->imat, ob->obmat);
			mul_m4_v3(ob->imat, median);
			mul_m4_v3(ob->imat, ve_median);
		}
		sub_v3_v3v3(median, ve_median, median);
		median[3] = ve_median[3] - median[3];
		median[4] = ve_median[4] - median[4];
		median[5] = ve_median[5] - median[5];
		median[6] = ve_median[6] - median[6];

		if (ob->type == OB_MESH) {
			Mesh *me = ob->data;
			BMEditMesh *em = me->edit_btmesh;
			BMesh *bm = em->bm;
			BMVert *eve;
			BMIter iter;

			if (len_v3(median) > 0.000001f) {

				BM_ITER_MESH (eve, &iter, bm, BM_VERTS_OF_MESH) {
					if (BM_elem_flag_test(eve, BM_ELEM_SELECT)) {
						add_v3_v3(eve->co, median);
					}
				}

				EDBM_mesh_normals_update(em);
			}

			if (median[3] != 0.0f) {
				BMEdge *eed;
				const float sca = compute_scale_factor(ve_median[3], median[3]);

				if (ELEM(sca, 0.0f, 1.0f)) {
					BM_ITER_MESH (eed, &iter, bm, BM_EDGES_OF_MESH) {
						if (BM_elem_flag_test(eed, BM_ELEM_SELECT)) {
							float *crease = (float *)CustomData_bmesh_get(&bm->edata, eed->head.data, CD_CREASE);
							if (crease) {
								*crease = sca;
							}
						}
					}
				}
				else if (sca > 0.0f) {
					BM_ITER_MESH (eed, &iter, bm, BM_EDGES_OF_MESH) {
						if (BM_elem_flag_test(eed, BM_ELEM_SELECT) && !BM_elem_flag_test(eed, BM_ELEM_HIDDEN)) {
							float *crease = (float *)CustomData_bmesh_get(&bm->edata, eed->head.data, CD_CREASE);
							if (crease) {
								*crease *= sca;
								CLAMP(*crease, 0.0f, 1.0f);
							}
						}
					}
				}
				else {
					BM_ITER_MESH (eed, &iter, bm, BM_EDGES_OF_MESH) {
						if (BM_elem_flag_test(eed, BM_ELEM_SELECT) && !BM_elem_flag_test(eed, BM_ELEM_HIDDEN)) {
							float *crease = (float *)CustomData_bmesh_get(&bm->edata, eed->head.data, CD_CREASE);
							if (crease) {
								*crease = 1.0f + ((1.0f - *crease) * sca);
								CLAMP(*crease, 0.0f, 1.0f);
							}
						}
					}
				}
			}

			if (median[6] != 0.0f) {
				BMEdge *eed;
				const float sca = compute_scale_factor(ve_median[6], median[6]);

				if (ELEM(sca, 0.0f, 1.0f)) {
					BM_ITER_MESH (eed, &iter, bm, BM_EDGES_OF_MESH) {
						if (BM_elem_flag_test(eed, BM_ELEM_SELECT)) {
							float *bweight = (float *)CustomData_bmesh_get(&bm->edata, eed->head.data, CD_BWEIGHT);
							if (bweight) {
								*bweight = sca;
							}
						}
					}
				}
				else if (sca > 0.0f) {
					BM_ITER_MESH (eed, &iter, bm, BM_EDGES_OF_MESH) {
						if (BM_elem_flag_test(eed, BM_ELEM_SELECT) && !BM_elem_flag_test(eed, BM_ELEM_HIDDEN)) {
							float *bweight = (float *)CustomData_bmesh_get(&bm->edata, eed->head.data, CD_BWEIGHT);
							if (bweight) {
								*bweight *= sca;
								CLAMP(*bweight, 0.0f, 1.0f);
							}
						}
					}
				}
				else {
					BM_ITER_MESH (eed, &iter, bm, BM_EDGES_OF_MESH) {
						if (BM_elem_flag_test(eed, BM_ELEM_SELECT) && !BM_elem_flag_test(eed, BM_ELEM_HIDDEN)) {
							float *bweight = (float *)CustomData_bmesh_get(&bm->edata, eed->head.data, CD_BWEIGHT);
							if (bweight) {
								*bweight = 1.0f + ((1.0f - *bweight) * sca);
								CLAMP(*bweight, 0.0f, 1.0f);
							}
						}
					}
				}
			}
			EDBM_mesh_normals_update(em);
		}
		else if (ELEM(ob->type, OB_CURVE, OB_SURF)) {
			Curve *cu = ob->data;
			Nurb *nu;
			BPoint *bp;
			BezTriple *bezt;
			int a;
			ListBase *nurbs = BKE_curve_editNurbs_get(cu);
			const float scale_w = compute_scale_factor(ve_median[4], median[4]);

			nu = nurbs->first;
			while (nu) {
				if (nu->type == CU_BEZIER) {
					bezt = nu->bezt;
					a = nu->pntsu;
					while (a--) {
						if (bezt->f2 & SELECT) {
							add_v3_v3(bezt->vec[0], median);
							add_v3_v3(bezt->vec[1], median);
							add_v3_v3(bezt->vec[2], median);

							if (median[4] != 0.0f) {
								if (ELEM(scale_w, 0.0f, 1.0f)) {
									bezt->weight = scale_w;
								}
								else {
									bezt->weight = scale_w > 0.0f ? bezt->weight * scale_w :
									                                1.0f + ((1.0f - bezt->weight) * scale_w);
									CLAMP(bezt->weight, 0.0f, 1.0f);
								}
							}

							bezt->radius += median[5];
						}
						else {
							if (bezt->f1 & SELECT) {
								add_v3_v3(bezt->vec[0], median);
							}
							if (bezt->f3 & SELECT) {
								add_v3_v3(bezt->vec[2], median);
							}
						}
						bezt++;
					}
				}
				else {
					bp = nu->bp;
					a = nu->pntsu * nu->pntsv;
					while (a--) {
						if (bp->f1 & SELECT) {
							add_v3_v3(bp->vec, median);
							bp->vec[3] += median[3];

							if (median[4] != 0.0f) {
								if (ELEM(scale_w, 0.0f, 1.0f)) {
									bp->weight = scale_w;
								}
								else {
									bp->weight = scale_w > 0.0f ? bp->weight * scale_w :
									                              1.0f + ((1.0f - bp->weight) * scale_w);
									CLAMP(bp->weight, 0.0f, 1.0f);
								}
							}

							bp->radius += median[5];
						}
						bp++;
					}
				}
				BKE_nurb_test2D(nu);
				BKE_nurb_handles_test(nu); /* test for bezier too */

				nu = nu->next;
			}
		}
		else if (ob->type == OB_LATTICE) {
			Lattice *lt = ob->data;
			BPoint *bp;
			int a;
			const float scale_w = compute_scale_factor(ve_median[4], median[4]);

			a = lt->editlatt->latt->pntsu * lt->editlatt->latt->pntsv * lt->editlatt->latt->pntsw;
			bp = lt->editlatt->latt->def;
			while (a--) {
				if (bp->f1 & SELECT) {
					add_v3_v3(bp->vec, median);

					if (median[4] != 0.0f) {
						if (ELEM(scale_w, 0.0f, 1.0f)) {
							bp->weight = scale_w;
						}
						else {
							bp->weight = scale_w > 0.0f ? bp->weight * scale_w :
							                              1.0f + ((1.0f - bp->weight) * scale_w);
							CLAMP(bp->weight, 0.0f, 1.0f);
						}
					}
				}
				bp++;
			}
		}

/*		ED_undo_push(C, "Transform properties"); */
	}
}
#define B_VGRP_PNL_COPY 1
#define B_VGRP_PNL_NORMALIZE 2
#define B_VGRP_PNL_EDIT_SINGLE 8 /* or greater */
#define B_VGRP_PNL_COPY_SINGLE 16384 /* or greater */

static void act_vert_def(Object *ob, BMVert **eve, MDeformVert **dvert)
{
	if (ob && ob->mode & OB_MODE_EDIT && ob->type == OB_MESH && ob->defbase.first) {
		Mesh *me = ob->data;
		BMEditMesh *em = me->edit_btmesh;
		BMEditSelection *ese = (BMEditSelection *)em->bm->selected.last;

		if (ese && ese->htype == BM_VERT) {
			*eve = (BMVert *)ese->ele;
			*dvert = CustomData_bmesh_get(&em->bm->vdata, (*eve)->head.data, CD_MDEFORMVERT);
			return;
		}
	}

	*eve = NULL;
	*dvert = NULL;
}

static void editvert_mirror_update(Object *ob, BMVert *eve, int def_nr, int index)
{
	Mesh *me = ob->data;
	BMEditMesh *em = me->edit_btmesh;
	BMVert *eve_mirr;

	eve_mirr = editbmesh_get_x_mirror_vert(ob, em, eve, eve->co, index);

	if (eve_mirr && eve_mirr != eve) {
		MDeformVert *dvert_src = CustomData_bmesh_get(&em->bm->vdata, eve->head.data, CD_MDEFORMVERT);
		MDeformVert *dvert_dst = CustomData_bmesh_get(&em->bm->vdata, eve_mirr->head.data, CD_MDEFORMVERT);
		if (dvert_dst) {
			if (def_nr == -1) {
				/* all vgroups, add groups where neded  */
				int flip_map_len;
				int *flip_map = defgroup_flip_map(ob, &flip_map_len, TRUE);
				defvert_sync_mapped(dvert_dst, dvert_src, flip_map, flip_map_len, TRUE);
				MEM_freeN(flip_map);
			}
			else {
				/* single vgroup */
				MDeformWeight *dw = defvert_verify_index(dvert_dst, defgroup_flip_index(ob, def_nr, 1));
				if (dw) {
					dw->weight = defvert_find_weight(dvert_src, def_nr);
				}
			}
		}
	}
}

static void vgroup_adjust_active(Object *ob, int def_nr)
{
	BMVert *eve_act;
	MDeformVert *dvert_act;

	act_vert_def(ob, &eve_act, &dvert_act);

	if (dvert_act) {
		if (((Mesh *)ob->data)->editflag & ME_EDIT_MIRROR_X)
			editvert_mirror_update(ob, eve_act, def_nr, -1);
	}
}

static void vgroup_copy_active_to_sel(Object *ob)
{
	BMVert *eve_act;
	MDeformVert *dvert_act;

	act_vert_def(ob, &eve_act, &dvert_act);

	if (dvert_act == NULL) {
		return;
	}
	else {
		Mesh *me = ob->data;
		BMEditMesh *em = me->edit_btmesh;
		BMIter iter;
		BMVert *eve;
		MDeformVert *dvert;
		int index = 0;

		BM_ITER_MESH (eve, &iter, em->bm, BM_VERTS_OF_MESH) {
			if (BM_elem_flag_test(eve, BM_ELEM_SELECT) && eve != eve_act) {
				dvert = CustomData_bmesh_get(&em->bm->vdata, eve->head.data, CD_MDEFORMVERT);
				if (dvert) {
					defvert_copy(dvert, dvert_act);

					if (me->editflag & ME_EDIT_MIRROR_X)
						editvert_mirror_update(ob, eve, -1, index);

				}
			}

			index++;
		}
	}
}

static void vgroup_copy_active_to_sel_single(Object *ob, const int def_nr)
{
	BMVert *eve_act;
	MDeformVert *dv_act;

	act_vert_def(ob, &eve_act, &dv_act);

	if (dv_act == NULL) {
		return;
	}
	else {
		Mesh *me = ob->data;
		BMEditMesh *em = me->edit_btmesh;
		BMIter iter;
		BMVert *eve;
		MDeformVert *dv;
		MDeformWeight *dw;
		float weight_act;
		int index = 0;

		dw = defvert_find_index(dv_act, def_nr);

		if (dw == NULL)
			return;

		weight_act = dw->weight;

		eve = BM_iter_new(&iter, em->bm, BM_VERTS_OF_MESH, NULL);
		for (index = 0; eve; eve = BM_iter_step(&iter), index++) {
			if (BM_elem_flag_test(eve, BM_ELEM_SELECT) && eve != eve_act) {
				dv = CustomData_bmesh_get(&em->bm->vdata, eve->head.data, CD_MDEFORMVERT);
				dw = defvert_find_index(dv, def_nr);
				if (dw) {
					dw->weight = weight_act;

					if (me->editflag & ME_EDIT_MIRROR_X) {
						editvert_mirror_update(ob, eve, -1, index);
					}
				}
			}
		}

		if (me->editflag & ME_EDIT_MIRROR_X) {
			editvert_mirror_update(ob, eve_act, -1, -1);
		}
	}
}

static void vgroup_normalize_active(Object *ob)
{
	BMVert *eve_act;
	MDeformVert *dvert_act;

	act_vert_def(ob, &eve_act, &dvert_act);

	if (dvert_act == NULL)
		return;

	defvert_normalize(dvert_act);

	if (((Mesh *)ob->data)->editflag & ME_EDIT_MIRROR_X)
		editvert_mirror_update(ob, eve_act, -1, -1);
}

static void do_view3d_vgroup_buttons(bContext *C, void *UNUSED(arg), int event)
{
	Scene *scene = CTX_data_scene(C);
	Object *ob = OBACT;

	/* XXX TODO Use operators? */
	if (event == B_VGRP_PNL_NORMALIZE) {
		vgroup_normalize_active(ob);
	}
	else if (event == B_VGRP_PNL_COPY) {
		vgroup_copy_active_to_sel(ob);
	}
	else if (event >= B_VGRP_PNL_COPY_SINGLE) {
		vgroup_copy_active_to_sel_single(ob, event - B_VGRP_PNL_COPY_SINGLE);
	}
	else if (event >= B_VGRP_PNL_EDIT_SINGLE) {
		vgroup_adjust_active(ob, event - B_VGRP_PNL_EDIT_SINGLE);
	}

#if 0 /* TODO */
	if (((Mesh *)ob->data)->editflag & ME_EDIT_MIRROR_X)
		ED_vgroup_mirror(ob, 1, 1, 0);
#endif

	/* default for now */
	DAG_id_tag_update(&ob->id, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_GEOM | ND_DATA, ob->data);
}

static int view3d_panel_vgroup_poll(const bContext *C, PanelType *UNUSED(pt))
{
	Scene *scene = CTX_data_scene(C);
	Object *ob = OBACT;
	BMVert *eve_act;
	MDeformVert *dvert_act;

	act_vert_def(ob, &eve_act, &dvert_act);

	return dvert_act ? dvert_act->totweight : 0;
}


static void view3d_panel_vgroup(const bContext *C, Panel *pa)
{
	uiBlock *block = uiLayoutAbsoluteBlock(pa->layout);
	Scene *scene = CTX_data_scene(C);
	Object *ob = OBACT;

	BMVert *eve;
	MDeformVert *dv;

	act_vert_def(ob, &eve, &dv);

	if (dv && dv->totweight) {
		uiLayout *col;
		bDeformGroup *dg;
		MDeformWeight *dw = dv->dw;
		unsigned int i;
		int yco = 0;

		uiBlockSetHandleFunc(block, do_view3d_vgroup_buttons, NULL);

		col = uiLayoutColumn(pa->layout, 0);
		block = uiLayoutAbsoluteBlock(col);

		uiBlockBeginAlign(block);

		for (i = dv->totweight; i != 0; i--, dw++) {
			dg = BLI_findlink(&ob->defbase, dw->def_nr);
			if (dg) {
				uiDefButF(block, NUM, B_VGRP_PNL_EDIT_SINGLE + dw->def_nr, dg->name, 0, yco, 180, 20,
				          &dw->weight, 0.0, 1.0, 1, 3, "");
				uiDefBut(block, BUT, B_VGRP_PNL_COPY_SINGLE + dw->def_nr, "C", 180, yco, 20, 20,
				         NULL, 0, 0, 0, 0, TIP_("Copy this group's weight to other selected verts"));
				yco -= 20;
			}
		}
		yco -= 2;

		uiBlockEndAlign(block);
		uiBlockBeginAlign(block);
		uiDefBut(block, BUT, B_VGRP_PNL_NORMALIZE, IFACE_("Normalize"), 0, yco, 100, 20,
		         NULL, 0, 0, 0, 0, TIP_("Normalize active vertex weights"));
		uiDefBut(block, BUT, B_VGRP_PNL_COPY, IFACE_("Copy"), 100, yco, 100, 20,
		         NULL, 0, 0, 0, 0, TIP_("Copy active vertex to other seleted verts"));
		uiBlockEndAlign(block);
	}
}

static void v3d_transform_butsR(uiLayout *layout, PointerRNA *ptr)
{
	uiLayout *split, *colsub;

	split = uiLayoutSplit(layout, 0.8, 0);

	if (ptr->type == &RNA_PoseBone) {
		PointerRNA boneptr;
		Bone *bone;

		boneptr = RNA_pointer_get(ptr, "bone");
		bone = boneptr.data;
		uiLayoutSetActive(split, !(bone->parent && bone->flag & BONE_CONNECTED));
	}
	colsub = uiLayoutColumn(split, 1);
	uiItemR(colsub, ptr, "location", 0, NULL, ICON_NONE);
	colsub = uiLayoutColumn(split, 1);
	uiItemL(colsub, "", ICON_NONE);
	uiItemR(colsub, ptr, "lock_location", UI_ITEM_R_TOGGLE | UI_ITEM_R_ICON_ONLY, "", ICON_NONE);

	split = uiLayoutSplit(layout, 0.8, 0);

	switch (RNA_enum_get(ptr, "rotation_mode")) {
		case ROT_MODE_QUAT: /* quaternion */
			colsub = uiLayoutColumn(split, 1);
			uiItemR(colsub, ptr, "rotation_quaternion", 0, IFACE_("Rotation"), ICON_NONE);
			colsub = uiLayoutColumn(split, 1);
			uiItemR(colsub, ptr, "lock_rotations_4d", UI_ITEM_R_TOGGLE, IFACE_("4L"), ICON_NONE);
			if (RNA_boolean_get(ptr, "lock_rotations_4d"))
				uiItemR(colsub, ptr, "lock_rotation_w", UI_ITEM_R_TOGGLE + UI_ITEM_R_ICON_ONLY, "", ICON_NONE);
			else
				uiItemL(colsub, "", ICON_NONE);
			uiItemR(colsub, ptr, "lock_rotation", UI_ITEM_R_TOGGLE | UI_ITEM_R_ICON_ONLY, "", ICON_NONE);
			break;
		case ROT_MODE_AXISANGLE: /* axis angle */
			colsub = uiLayoutColumn(split, 1);
			uiItemR(colsub, ptr, "rotation_axis_angle", 0, IFACE_("Rotation"), ICON_NONE);
			colsub = uiLayoutColumn(split, 1);
			uiItemR(colsub, ptr, "lock_rotations_4d", UI_ITEM_R_TOGGLE, IFACE_("4L"), ICON_NONE);
			if (RNA_boolean_get(ptr, "lock_rotations_4d"))
				uiItemR(colsub, ptr, "lock_rotation_w", UI_ITEM_R_TOGGLE | UI_ITEM_R_ICON_ONLY, "", ICON_NONE);
			else
				uiItemL(colsub, "", ICON_NONE);
			uiItemR(colsub, ptr, "lock_rotation", UI_ITEM_R_TOGGLE | UI_ITEM_R_ICON_ONLY, "", ICON_NONE);
			break;
		default: /* euler rotations */
			colsub = uiLayoutColumn(split, 1);
			uiItemR(colsub, ptr, "rotation_euler", 0, IFACE_("Rotation"), ICON_NONE);
			colsub = uiLayoutColumn(split, 1);
			uiItemL(colsub, "", ICON_NONE);
			uiItemR(colsub, ptr, "lock_rotation", UI_ITEM_R_TOGGLE | UI_ITEM_R_ICON_ONLY, "", ICON_NONE);
			break;
	}
	uiItemR(layout, ptr, "rotation_mode", 0, "", ICON_NONE);

	split = uiLayoutSplit(layout, 0.8, 0);
	colsub = uiLayoutColumn(split, 1);
	uiItemR(colsub, ptr, "scale", 0, NULL, ICON_NONE);
	colsub = uiLayoutColumn(split, 1);
	uiItemL(colsub, "", ICON_NONE);
	uiItemR(colsub, ptr, "lock_scale", UI_ITEM_R_TOGGLE | UI_ITEM_R_ICON_ONLY, "", ICON_NONE);

	if (ptr->type == &RNA_Object) {
		Object *ob = ptr->data;
		/* dimensions and material support just happen to be the same checks
		 * later we may want to add dimensions for lattice, armature etc too */
		if (OB_TYPE_SUPPORT_MATERIAL(ob->type)) {
			uiItemR(layout, ptr, "dimensions", 0, NULL, ICON_NONE);
		}
	}
}

static void v3d_posearmature_buts(uiLayout *layout, Object *ob)
{
	bPoseChannel *pchan;
	PointerRNA pchanptr;
	uiLayout *col;

	pchan = get_active_posechannel(ob);

	if (!pchan) {
		uiItemL(layout, IFACE_("No Bone Active"), ICON_NONE);
		return;
	}

	RNA_pointer_create(&ob->id, &RNA_PoseBone, pchan, &pchanptr);

	col = uiLayoutColumn(layout, 0);

	/* XXX: RNA buts show data in native types (i.e. quats, 4-component axis/angle, etc.)
	 * but old-school UI shows in eulers always. Do we want to be able to still display in Eulers?
	 * Maybe needs RNA/ui options to display rotations as different types... */
	v3d_transform_butsR(col, &pchanptr);
}

static void v3d_editarmature_buts(uiLayout *layout, Object *ob)
{
	bArmature *arm = ob->data;
	EditBone *ebone;
	uiLayout *col;
	PointerRNA eboneptr;

	ebone = arm->act_edbone;

	if (!ebone || (ebone->layer & arm->layer) == 0) {
		uiItemL(layout, IFACE_("Nothing selected"), ICON_NONE);
		return;
	}

	RNA_pointer_create(&arm->id, &RNA_EditBone, ebone, &eboneptr);

	col = uiLayoutColumn(layout, 0);
	uiItemR(col, &eboneptr, "head", 0, NULL, ICON_NONE);
	if (ebone->parent && ebone->flag & BONE_CONNECTED) {
		PointerRNA parptr = RNA_pointer_get(&eboneptr, "parent");
		uiItemR(col, &parptr, "tail_radius", 0, IFACE_("Radius (Parent)"), ICON_NONE);
	}
	else {
		uiItemR(col, &eboneptr, "head_radius", 0, IFACE_("Radius"), ICON_NONE);
	}

	uiItemR(col, &eboneptr, "tail", 0, NULL, ICON_NONE);
	uiItemR(col, &eboneptr, "tail_radius", 0, IFACE_("Radius"), ICON_NONE);

	uiItemR(col, &eboneptr, "roll", 0, NULL, ICON_NONE);
	uiItemR(col, &eboneptr, "envelope_distance", 0, IFACE_("Envelope"), ICON_NONE);
}

static void v3d_editmetaball_buts(uiLayout *layout, Object *ob)
{
	PointerRNA mbptr, ptr;
	MetaBall *mball = ob->data;
	uiLayout *col;

	if (!mball || !(mball->lastelem))
		return;

	RNA_pointer_create(&mball->id, &RNA_MetaBall, mball, &mbptr);

	RNA_pointer_create(&mball->id, &RNA_MetaElement, mball->lastelem, &ptr);

	col = uiLayoutColumn(layout, 0);
	uiItemR(col, &ptr, "co", 0, NULL, ICON_NONE);

	uiItemR(col, &ptr, "radius", 0, NULL, ICON_NONE);
	uiItemR(col, &ptr, "stiffness", 0, NULL, ICON_NONE);

	uiItemR(col, &ptr, "type", 0, NULL, ICON_NONE);

	col = uiLayoutColumn(layout, 1);
	switch (RNA_enum_get(&ptr, "type")) {
		case MB_BALL:
			break;
		case MB_CUBE:
			uiItemL(col, IFACE_("Size:"), ICON_NONE);
			uiItemR(col, &ptr, "size_x", 0, "X", ICON_NONE);
			uiItemR(col, &ptr, "size_y", 0, "Y", ICON_NONE);
			uiItemR(col, &ptr, "size_z", 0, "Z", ICON_NONE);
			break;
		case MB_TUBE:
			uiItemL(col, IFACE_("Size:"), ICON_NONE);
			uiItemR(col, &ptr, "size_x", 0, "X", ICON_NONE);
			break;
		case MB_PLANE:
			uiItemL(col, IFACE_("Size:"), ICON_NONE);
			uiItemR(col, &ptr, "size_x", 0, "X", ICON_NONE);
			uiItemR(col, &ptr, "size_y", 0, "Y", ICON_NONE);
			break;
		case MB_ELIPSOID:
			uiItemL(col, IFACE_("Size:"), ICON_NONE);
			uiItemR(col, &ptr, "size_x", 0, "X", ICON_NONE);
			uiItemR(col, &ptr, "size_y", 0, "Y", ICON_NONE);
			uiItemR(col, &ptr, "size_z", 0, "Z", ICON_NONE);
			break;
	}
}

static void do_view3d_region_buttons(bContext *C, void *UNUSED(index), int event)
{
	Scene *scene = CTX_data_scene(C);
	View3D *v3d = CTX_wm_view3d(C);
	Object *ob = OBACT;

	switch (event) {

		case B_REDR:
			ED_area_tag_redraw(CTX_wm_area(C));
			return; /* no notifier! */

		case B_OBJECTPANELMEDIAN:
			if (ob) {
				v3d_editvertex_buts(NULL, v3d, ob, 1.0);
				DAG_id_tag_update(&ob->id, OB_RECALC_DATA);
			}
			break;
	}

	/* default for now */
	WM_event_add_notifier(C, NC_SPACE | ND_SPACE_VIEW3D, v3d);
}

static void view3d_panel_object(const bContext *C, Panel *pa)
{
	uiBlock *block;
	Scene *scene = CTX_data_scene(C);
	Object *obedit = CTX_data_edit_object(C);
	View3D *v3d = CTX_wm_view3d(C);
	Object *ob = OBACT;
	PointerRNA obptr;
	uiLayout *col;
	float lim;

	if (ob == NULL)
		return;

	lim = 10000.0f * MAX2(1.0f, v3d->grid);

	block = uiLayoutGetBlock(pa->layout);
	uiBlockSetHandleFunc(block, do_view3d_region_buttons, NULL);

	col = uiLayoutColumn(pa->layout, 0);
	/* row = uiLayoutRow(col, 0); */ /* UNUSED */
	RNA_id_pointer_create(&ob->id, &obptr);

	if (ob == obedit) {
		if (ob->type == OB_ARMATURE)
			v3d_editarmature_buts(col, ob);
		else if (ob->type == OB_MBALL)
			v3d_editmetaball_buts(col, ob);
		else
			v3d_editvertex_buts(col, v3d, ob, lim);
	}
	else if (ob->mode & OB_MODE_POSE) {
		v3d_posearmature_buts(col, ob);
	}
	else {
		v3d_transform_butsR(col, &obptr);
	}
}

void view3d_buttons_register(ARegionType *art)
{
	PanelType *pt;

	pt = MEM_callocN(sizeof(PanelType), "spacetype view3d panel object");
	strcpy(pt->idname, "VIEW3D_PT_object");
	strcpy(pt->label, "Transform");
	pt->draw = view3d_panel_object;
	BLI_addtail(&art->paneltypes, pt);

	pt = MEM_callocN(sizeof(PanelType), "spacetype view3d panel gpencil");
	strcpy(pt->idname, "VIEW3D_PT_gpencil");
	strcpy(pt->label, "Grease Pencil");
	pt->draw = gpencil_panel_standard;
	BLI_addtail(&art->paneltypes, pt);

	pt = MEM_callocN(sizeof(PanelType), "spacetype view3d panel vgroup");
	strcpy(pt->idname, "VIEW3D_PT_vgroup");
	strcpy(pt->label, "Vertex Groups");
	pt->draw = view3d_panel_vgroup;
	pt->poll = view3d_panel_vgroup_poll;
	BLI_addtail(&art->paneltypes, pt);
}

static int view3d_properties(bContext *C, wmOperator *UNUSED(op))
{
	ScrArea *sa = CTX_wm_area(C);
	ARegion *ar = view3d_has_buttons_region(sa);

	if (ar)
		ED_region_toggle_hidden(C, ar);

	return OPERATOR_FINISHED;
}

void VIEW3D_OT_properties(wmOperatorType *ot)
{
	ot->name = "Properties";
	ot->description = "Toggles the properties panel display";
	ot->idname = "VIEW3D_OT_properties";

	ot->exec = view3d_properties;
	ot->poll = ED_operator_view3d_active;

	/* flags */
	ot->flag = 0;
}
