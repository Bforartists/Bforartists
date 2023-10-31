/* SPDX-FileCopyrightText: 2013 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edmesh
 */

#include "DNA_curve_types.h"
#include "DNA_object_types.h"

#include "BLI_linklist.h"
#include "BLI_listbase.h"
#include "BLI_math_vector.h"

#include "BKE_context.h"
#include "BKE_curve.h"
#include "BKE_customdata.h"
#include "BKE_editmesh.h"
#include "BKE_layer.h"
#include "BKE_lib_id.h"
#include "BKE_mesh.hh"
#include "BKE_mesh_runtime.hh"
#include "BKE_object.hh"
#include "BKE_report.h"

#include "DEG_depsgraph.hh"
#include "DEG_depsgraph_query.hh"

#include "RNA_access.hh"
#include "RNA_define.hh"

#include "MEM_guardedalloc.h"

#include "WM_types.hh"

#include "ED_mesh.hh"
#include "ED_screen.hh"
#include "ED_view3d.hh"

#include "mesh_intern.h" /* own include */

static LinkNode *knifeproject_poly_from_object(const bContext *C, Object *ob, LinkNode *polys)
{
  Depsgraph *depsgraph = CTX_data_ensure_evaluated_depsgraph(C);
  ARegion *region = CTX_wm_region(C);
  const Mesh *me_eval;
  bool me_eval_needs_free;

  if (ob->type == OB_MESH || ob->runtime.data_eval) {
    const Object *ob_eval = DEG_get_evaluated_object(depsgraph, ob);
    me_eval = BKE_object_get_evaluated_mesh(ob_eval);
    me_eval_needs_free = false;
  }
  else if (ELEM(ob->type, OB_FONT, OB_CURVES_LEGACY, OB_SURF)) {
    const Object *ob_eval = DEG_get_evaluated_object(depsgraph, ob);
    me_eval = BKE_mesh_new_nomain_from_curve(ob_eval);
    me_eval_needs_free = true;
  }
  else {
    me_eval = nullptr;
  }

  if (me_eval) {
    ListBase nurbslist = {nullptr, nullptr};
    float projmat[4][4];

    BKE_mesh_to_curve_nurblist(me_eval, &nurbslist, 0); /* wire */
    BKE_mesh_to_curve_nurblist(me_eval, &nurbslist, 1); /* boundary */

    ED_view3d_ob_project_mat_get(static_cast<RegionView3D *>(region->regiondata), ob, projmat);

    if (nurbslist.first) {
      LISTBASE_FOREACH (Nurb *, nu, &nurbslist) {
        if (nu->bp) {
          int a;
          BPoint *bp;
          bool is_cyclic = (nu->flagu & CU_NURB_CYCLIC) != 0;
          float(*mval)[2] = static_cast<float(*)[2]>(
              MEM_mallocN(sizeof(*mval) * (nu->pntsu + is_cyclic), __func__));

          for (bp = nu->bp, a = 0; a < nu->pntsu; a++, bp++) {
            ED_view3d_project_float_v2_m4(region, bp->vec, mval[a], projmat);
          }
          if (is_cyclic) {
            copy_v2_v2(mval[a], mval[0]);
          }

          BLI_linklist_prepend(&polys, mval);
        }
      }
    }

    BKE_nurbList_free(&nurbslist);

    if (me_eval_needs_free) {
      BKE_id_free(nullptr, (ID *)me_eval);
    }
  }

  return polys;
}

static int knifeproject_exec(bContext *C, wmOperator *op)
{
  Scene *scene = CTX_data_scene(C);
  const bool cut_through = RNA_boolean_get(op->ptr, "cut_through");

  LinkNode *polys = nullptr;

  CTX_DATA_BEGIN (C, Object *, ob, selected_objects) {
    if (BKE_object_is_in_editmode(ob)) {
      continue;
    }
    polys = knifeproject_poly_from_object(C, ob, polys);
  }
  CTX_DATA_END;

  if (polys == nullptr) {
    BKE_report(op->reports,
               RPT_ERROR,
               "No other selected objects have wire or boundary edges to use for projection");
    return OPERATOR_CANCELLED;
  }

  ViewContext vc = em_setup_viewcontext(C);

  uint objects_len;
  Object **objects = BKE_view_layer_array_from_objects_in_edit_mode_unique_data(
      vc.scene, vc.view_layer, vc.v3d, &objects_len);

  EDBM_mesh_knife(&vc, objects, objects_len, polys, true, cut_through);

  for (uint ob_index = 0; ob_index < objects_len; ob_index++) {
    Object *obedit = objects[ob_index];
    ED_view3d_viewcontext_init_object(&vc, obedit);
    BMEditMesh *em = BKE_editmesh_from_object(obedit);

    /* select only tagged faces */
    BM_mesh_elem_hflag_disable_all(em->bm, BM_VERT | BM_EDGE | BM_FACE, BM_ELEM_SELECT, false);

    EDBM_selectmode_disable(scene, em, SCE_SELECT_VERTEX, SCE_SELECT_EDGE);

    BM_mesh_elem_hflag_enable_test(em->bm, BM_FACE, BM_ELEM_SELECT, true, false, BM_ELEM_TAG);

    BM_mesh_select_mode_flush(em->bm);
  }
  MEM_freeN(objects);

  BLI_linklist_freeN(polys);

  return OPERATOR_FINISHED;
}

void MESH_OT_knife_project(wmOperatorType *ot)
{
  /* description */
  ot->name = "Knife Project";
  ot->idname = "MESH_OT_knife_project";
  ot->description = "Use other objects outlines and boundaries to project knife cuts";

  /* callbacks */
  ot->exec = knifeproject_exec;
  ot->poll = ED_operator_editmesh_region_view3d;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO | OPTYPE_BLOCKING;

  /* parameters */
  RNA_def_boolean(ot->srna,
                  "cut_through",
                  false,
                  "Cut Through",
                  "Cut through all faces, not just visible ones");
}
