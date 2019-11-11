/*
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 */

/** \file
 * \ingroup edtransform
 */

#include "DNA_mesh_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_compiler_compat.h"
#include "BLI_ghash.h"
#include "BLI_listbase.h"
#include "BLI_math.h"

#include "BKE_context.h"
#include "BKE_layer.h"
#include "BKE_main.h"
#include "BKE_object.h"
#include "BKE_report.h"
#include "BKE_rigidbody.h"
#include "BKE_scene.h"

#include "ED_object.h"

#include "DEG_depsgraph_query.h"

#include "transform.h"
#include "transform_convert.h"

/* -------------------------------------------------------------------- */
/** \name Object Mode Custom Data
 * \{ */

typedef struct TransDataObject {

  /**
   * Object to object data transform table.
   * Don't add these to transform data because we may want to include child objects
   * which aren't being transformed.
   * - The key is object data #ID.
   * - The value is #XFormObjectData_Extra.
   */
  struct GHash *obdata_in_obmode_map;

  /**
   * Transform
   * - The key is object data #Object.
   * - The value is #XFormObjectSkipChild.
   */
  struct GHash *obchild_in_obmode_map;

} TransDataObject;

static void trans_obdata_in_obmode_free_all(TransDataObject *tdo);
static void trans_obchild_in_obmode_free_all(TransDataObject *tdo);

static void freeTransObjectCustomData(TransInfo *t,
                                      TransDataContainer *UNUSED(tc),
                                      TransCustomData *custom_data)
{
  TransDataObject *tdo = custom_data->data;
  custom_data->data = NULL;

  if (t->options & CTX_OBMODE_XFORM_OBDATA) {
    trans_obdata_in_obmode_free_all(tdo);
  }

  if (t->options & CTX_OBMODE_XFORM_SKIP_CHILDREN) {
    trans_obchild_in_obmode_free_all(tdo);
  }
  MEM_freeN(tdo);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Object Data in Object Mode
 *
 * Use to implement 'Affect Only Origins' feature.
 * We need this to be detached from transform data because,
 * unlike transforming regular objects, we need to transform the children.
 *
 * \{ */

struct XFormObjectData_Extra {
  Object *ob;
  float obmat_orig[4][4];
  struct XFormObjectData *xod;
};

static void trans_obdata_in_obmode_ensure_object(TransDataObject *tdo, Object *ob)
{
  if (tdo->obdata_in_obmode_map == NULL) {
    tdo->obdata_in_obmode_map = BLI_ghash_ptr_new(__func__);
  }

  void **xf_p;
  if (!BLI_ghash_ensure_p(tdo->obdata_in_obmode_map, ob->data, &xf_p)) {
    struct XFormObjectData_Extra *xf = MEM_mallocN(sizeof(*xf), __func__);
    copy_m4_m4(xf->obmat_orig, ob->obmat);
    xf->ob = ob;
    /* Result may be NULL, that's OK. */
    xf->xod = ED_object_data_xform_create(ob->data);
    *xf_p = xf;
  }
}

void trans_obdata_in_obmode_update_all(TransInfo *t)
{
  TransDataObject *tdo = t->custom.type.data;
  if (tdo->obdata_in_obmode_map == NULL) {
    return;
  }

  struct Main *bmain = CTX_data_main(t->context);
  BKE_scene_graph_evaluated_ensure(t->depsgraph, bmain);

  GHashIterator gh_iter;
  GHASH_ITER (gh_iter, tdo->obdata_in_obmode_map) {
    ID *id = BLI_ghashIterator_getKey(&gh_iter);
    struct XFormObjectData_Extra *xf = BLI_ghashIterator_getValue(&gh_iter);
    if (xf->xod == NULL) {
      continue;
    }

    Object *ob_eval = DEG_get_evaluated_object(t->depsgraph, xf->ob);
    float imat[4][4], dmat[4][4];
    invert_m4_m4(imat, xf->obmat_orig);
    mul_m4_m4m4(dmat, imat, ob_eval->obmat);
    invert_m4(dmat);

    ED_object_data_xform_by_mat4(xf->xod, dmat);
    if (xf->ob->type == OB_ARMATURE) {
      /* TODO: none of the current flags properly update armatures, needs investigation. */
      DEG_id_tag_update(id, 0);
    }
    else {
      DEG_id_tag_update(id, ID_RECALC_GEOMETRY);
    }
  }
}

/** Callback for #GHash free. */
static void trans_obdata_in_obmode_free_elem(void *xf_p)
{
  struct XFormObjectData_Extra *xf = xf_p;
  if (xf->xod) {
    ED_object_data_xform_destroy(xf->xod);
  }
  MEM_freeN(xf);
}

static void trans_obdata_in_obmode_free_all(TransDataObject *tdo)
{
  if (tdo->obdata_in_obmode_map != NULL) {
    BLI_ghash_free(tdo->obdata_in_obmode_map, NULL, trans_obdata_in_obmode_free_elem);
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Object Child Skip
 *
 * Don't transform unselected children, this is done using the parent inverse matrix.
 *
 * \note The complex logic here is caused by mixed selection within a single selection chain,
 * otherwise we only need #OB_SKIP_CHILD_PARENT_IS_XFORM for single objects.
 *
 * \{ */

enum {
  /**
   * The parent is transformed, this is held in place.
   */
  OB_SKIP_CHILD_PARENT_IS_XFORM = 1,
  /**
   * The same as #OB_SKIP_CHILD_PARENT_IS_XFORM,
   * however this objects parent isn't transformed directly.
   */
  OB_SKIP_CHILD_PARENT_IS_XFORM_INDIRECT = 3,
  /**
   * Use the parent invert matrix to apply transformation,
   * this is needed, because breaks in the selection chain prevents this from being transformed.
   * This is used to add the transform which would have been added
   * if there weren't breaks in the parent/child chain.
   */
  OB_SKIP_CHILD_PARENT_APPLY_TRANSFORM = 2,
};

struct XFormObjectSkipChild {
  float obmat_orig[4][4];
  float parent_obmat_orig[4][4];
  float parent_obmat_inv_orig[4][4];
  float parent_recurse_obmat_orig[4][4];
  float parentinv_orig[4][4];
  Object *ob_parent_recurse;
  int mode;
};

static void trans_obchild_in_obmode_ensure_object(TransDataObject *tdo,
                                                  Object *ob,
                                                  Object *ob_parent_recurse,
                                                  int mode)
{
  if (tdo->obchild_in_obmode_map == NULL) {
    tdo->obchild_in_obmode_map = BLI_ghash_ptr_new(__func__);
  }

  void **xf_p;
  if (!BLI_ghash_ensure_p(tdo->obchild_in_obmode_map, ob, &xf_p)) {
    struct XFormObjectSkipChild *xf = MEM_mallocN(sizeof(*xf), __func__);
    copy_m4_m4(xf->parentinv_orig, ob->parentinv);
    copy_m4_m4(xf->obmat_orig, ob->obmat);
    copy_m4_m4(xf->parent_obmat_orig, ob->parent->obmat);
    invert_m4_m4(xf->parent_obmat_inv_orig, ob->parent->obmat);
    if (ob_parent_recurse) {
      copy_m4_m4(xf->parent_recurse_obmat_orig, ob_parent_recurse->obmat);
    }
    xf->mode = mode;
    xf->ob_parent_recurse = ob_parent_recurse;
    *xf_p = xf;
  }
}

void trans_obchild_in_obmode_update_all(TransInfo *t)
{
  TransDataObject *tdo = t->custom.type.data;
  if (tdo->obchild_in_obmode_map == NULL) {
    return;
  }

  struct Main *bmain = CTX_data_main(t->context);
  BKE_scene_graph_evaluated_ensure(t->depsgraph, bmain);

  GHashIterator gh_iter;
  GHASH_ITER (gh_iter, tdo->obchild_in_obmode_map) {
    Object *ob = BLI_ghashIterator_getKey(&gh_iter);
    struct XFormObjectSkipChild *xf = BLI_ghashIterator_getValue(&gh_iter);

    /* The following blocks below assign 'dmat'. */
    float dmat[4][4];

    if (xf->mode == OB_SKIP_CHILD_PARENT_IS_XFORM) {
      /* Parent is transformed, this isn't so compensate. */
      Object *ob_parent_eval = DEG_get_evaluated_object(t->depsgraph, ob->parent);
      mul_m4_m4m4(dmat, xf->parent_obmat_inv_orig, ob_parent_eval->obmat);
      invert_m4(dmat);
    }
    else if (xf->mode == OB_SKIP_CHILD_PARENT_IS_XFORM_INDIRECT) {
      /* Calculate parent matrix (from the root transform). */
      Object *ob_parent_recurse_eval = DEG_get_evaluated_object(t->depsgraph,
                                                                xf->ob_parent_recurse);
      float parent_recurse_obmat_inv[4][4];
      invert_m4_m4(parent_recurse_obmat_inv, ob_parent_recurse_eval->obmat);
      mul_m4_m4m4(dmat, xf->parent_recurse_obmat_orig, parent_recurse_obmat_inv);
      invert_m4(dmat);
      float parent_obmat_calc[4][4];
      mul_m4_m4m4(parent_obmat_calc, dmat, xf->parent_obmat_orig);

      /* Apply to the parent inverse matrix. */
      mul_m4_m4m4(dmat, xf->parent_obmat_inv_orig, parent_obmat_calc);
      invert_m4(dmat);
    }
    else {
      BLI_assert(xf->mode == OB_SKIP_CHILD_PARENT_APPLY_TRANSFORM);
      /* Transform this - without transform data. */
      Object *ob_parent_recurse_eval = DEG_get_evaluated_object(t->depsgraph,
                                                                xf->ob_parent_recurse);
      float parent_recurse_obmat_inv[4][4];
      invert_m4_m4(parent_recurse_obmat_inv, ob_parent_recurse_eval->obmat);
      mul_m4_m4m4(dmat, xf->parent_recurse_obmat_orig, parent_recurse_obmat_inv);
      invert_m4(dmat);
      float obmat_calc[4][4];
      mul_m4_m4m4(obmat_calc, dmat, xf->obmat_orig);
      /* obmat_calc is just obmat. */

      /* Get the matrices relative to the parent. */
      float obmat_parent_relative_orig[4][4];
      float obmat_parent_relative_calc[4][4];
      float obmat_parent_relative_inv_orig[4][4];

      mul_m4_m4m4(obmat_parent_relative_orig, xf->parent_obmat_inv_orig, xf->obmat_orig);
      mul_m4_m4m4(obmat_parent_relative_calc, xf->parent_obmat_inv_orig, obmat_calc);
      invert_m4_m4(obmat_parent_relative_inv_orig, obmat_parent_relative_orig);

      /* Apply to the parent inverse matrix. */
      mul_m4_m4m4(dmat, obmat_parent_relative_calc, obmat_parent_relative_inv_orig);
    }

    mul_m4_m4m4(ob->parentinv, dmat, xf->parentinv_orig);

    DEG_id_tag_update(&ob->id, ID_RECALC_TRANSFORM);
  }
}

static void trans_obchild_in_obmode_free_all(TransDataObject *tdo)
{
  if (tdo->obchild_in_obmode_map != NULL) {
    BLI_ghash_free(tdo->obchild_in_obmode_map, NULL, MEM_freeN);
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Object Transform Creation
 *
 * Instead of transforming the selection, move the 2D/3D cursor.
 *
 * \{ */

/* *********************** Object Transform data ******************* */

/* transcribe given object into TransData for Transforming */
static void ObjectToTransData(TransInfo *t, TransData *td, Object *ob)
{
  Scene *scene = t->scene;
  bool constinv;
  bool skip_invert = false;

  if (t->mode != TFM_DUMMY && ob->rigidbody_object) {
    float rot[3][3], scale[3];
    float ctime = BKE_scene_frame_get(scene);

    /* only use rigid body transform if simulation is running,
     * avoids problems with initial setup of rigid bodies */
    if (BKE_rigidbody_check_sim_running(scene->rigidbody_world, ctime)) {

      /* save original object transform */
      copy_v3_v3(td->ext->oloc, ob->loc);

      if (ob->rotmode > 0) {
        copy_v3_v3(td->ext->orot, ob->rot);
      }
      else if (ob->rotmode == ROT_MODE_AXISANGLE) {
        td->ext->orotAngle = ob->rotAngle;
        copy_v3_v3(td->ext->orotAxis, ob->rotAxis);
      }
      else {
        copy_qt_qt(td->ext->oquat, ob->quat);
      }
      /* update object's loc/rot to get current rigid body transform */
      mat4_to_loc_rot_size(ob->loc, rot, scale, ob->obmat);
      sub_v3_v3(ob->loc, ob->dloc);
      BKE_object_mat3_to_rot(ob, rot, false); /* drot is already corrected here */
    }
  }

  /* axismtx has the real orientation */
  copy_m3_m4(td->axismtx, ob->obmat);
  normalize_m3(td->axismtx);

  td->con = ob->constraints.first;

  /* hack: temporarily disable tracking and/or constraints when getting
   * object matrix, if tracking is on, or if constraints don't need
   * inverse correction to stop it from screwing up space conversion
   * matrix later
   */
  constinv = constraints_list_needinv(t, &ob->constraints);

  /* disable constraints inversion for dummy pass */
  if (t->mode == TFM_DUMMY) {
    skip_invert = true;
  }

  /* NOTE: This is not really following copy-on-write design and we should not
   * be re-evaluating the evaluated object. But as the comment above mentioned
   * this is part of a hack.
   * More proper solution would be to make a shallow copy of the object  and
   * evaluate that, and access matrix of that evaluated copy of the object.
   * Might be more tricky than it sounds, if some logic later on accesses the
   * object matrix via td->ob->obmat. */
  Object *object_eval = DEG_get_evaluated_object(t->depsgraph, ob);
  if (skip_invert == false && constinv == false) {
    object_eval->transflag |= OB_NO_CONSTRAINTS; /* BKE_object_where_is_calc checks this */
    /* It is possible to have transform data initialization prior to a
     * complete dependency graph evaluated. Happens, for example, when
     * changing transformation mode. */
    BKE_object_tfm_copy(object_eval, ob);
    BKE_object_where_is_calc(t->depsgraph, t->scene, object_eval);
    object_eval->transflag &= ~OB_NO_CONSTRAINTS;
  }
  else {
    BKE_object_where_is_calc(t->depsgraph, t->scene, object_eval);
  }
  /* Copy newly evaluated fields to the original object, similar to how
   * active dependency graph will do it. */
  copy_m4_m4(ob->obmat, object_eval->obmat);
  /* Only copy negative scale flag, this is the only flag which is modified by
   * the BKE_object_where_is_calc(). The rest of the flags we need to keep,
   * otherwise we might loose dupli flags  (see T61787). */
  ob->transflag &= ~OB_NEG_SCALE;
  ob->transflag |= (object_eval->transflag & OB_NEG_SCALE);

  td->ob = ob;

  td->loc = ob->loc;
  copy_v3_v3(td->iloc, td->loc);

  if (ob->rotmode > 0) {
    td->ext->rot = ob->rot;
    td->ext->rotAxis = NULL;
    td->ext->rotAngle = NULL;
    td->ext->quat = NULL;

    copy_v3_v3(td->ext->irot, ob->rot);
    copy_v3_v3(td->ext->drot, ob->drot);
  }
  else if (ob->rotmode == ROT_MODE_AXISANGLE) {
    td->ext->rot = NULL;
    td->ext->rotAxis = ob->rotAxis;
    td->ext->rotAngle = &ob->rotAngle;
    td->ext->quat = NULL;

    td->ext->irotAngle = ob->rotAngle;
    copy_v3_v3(td->ext->irotAxis, ob->rotAxis);
    // td->ext->drotAngle = ob->drotAngle;          // XXX, not implemented
    // copy_v3_v3(td->ext->drotAxis, ob->drotAxis); // XXX, not implemented
  }
  else {
    td->ext->rot = NULL;
    td->ext->rotAxis = NULL;
    td->ext->rotAngle = NULL;
    td->ext->quat = ob->quat;

    copy_qt_qt(td->ext->iquat, ob->quat);
    copy_qt_qt(td->ext->dquat, ob->dquat);
  }
  td->ext->rotOrder = ob->rotmode;

  td->ext->size = ob->scale;
  copy_v3_v3(td->ext->isize, ob->scale);
  copy_v3_v3(td->ext->dscale, ob->dscale);

  copy_v3_v3(td->center, ob->obmat[3]);

  copy_m4_m4(td->ext->obmat, ob->obmat);

  /* is there a need to set the global<->data space conversion matrices? */
  if (ob->parent || constinv) {
    float obmtx[3][3], totmat[3][3], obinv[3][3];

    /* Get the effect of parenting, and/or certain constraints.
     * NOTE: some Constraints, and also Tracking should never get this
     *       done, as it doesn't work well.
     */
    BKE_object_to_mat3(ob, obmtx);
    copy_m3_m4(totmat, ob->obmat);
    invert_m3_m3(obinv, totmat);
    mul_m3_m3m3(td->smtx, obmtx, obinv);
    invert_m3_m3(td->mtx, td->smtx);
  }
  else {
    /* no conversion to/from dataspace */
    unit_m3(td->smtx);
    unit_m3(td->mtx);
  }
}

static void trans_object_base_deps_flag_prepare(ViewLayer *view_layer)
{
  for (Base *base = view_layer->object_bases.first; base; base = base->next) {
    base->object->id.tag &= ~LIB_TAG_DOIT;
  }
}

static void set_trans_object_base_deps_flag_cb(ID *id,
                                               eDepsObjectComponentType component,
                                               void *UNUSED(user_data))
{
  /* Here we only handle object IDs. */
  if (GS(id->name) != ID_OB) {
    return;
  }
  if (!ELEM(component, DEG_OB_COMP_TRANSFORM, DEG_OB_COMP_GEOMETRY)) {
    return;
  }
  id->tag |= LIB_TAG_DOIT;
}

static void flush_trans_object_base_deps_flag(Depsgraph *depsgraph, Object *object)
{
  object->id.tag |= LIB_TAG_DOIT;
  DEG_foreach_dependent_ID_component(depsgraph,
                                     &object->id,
                                     DEG_OB_COMP_TRANSFORM,
                                     DEG_FOREACH_COMPONENT_IGNORE_TRANSFORM_SOLVERS,
                                     set_trans_object_base_deps_flag_cb,
                                     NULL);
}

static void trans_object_base_deps_flag_finish(const TransInfo *t, ViewLayer *view_layer)
{

  if ((t->options & CTX_OBMODE_XFORM_OBDATA) == 0) {
    for (Base *base = view_layer->object_bases.first; base; base = base->next) {
      if (base->object->id.tag & LIB_TAG_DOIT) {
        base->flag_legacy |= BA_SNAP_FIX_DEPS_FIASCO;
      }
    }
  }
}

/* sets flags in Bases to define whether they take part in transform */
/* it deselects Bases, so we have to call the clear function always after */
static void set_trans_object_base_flags(TransInfo *t)
{
  Main *bmain = CTX_data_main(t->context);
  ViewLayer *view_layer = t->view_layer;
  View3D *v3d = t->view;
  Scene *scene = t->scene;
  Depsgraph *depsgraph = BKE_scene_get_depsgraph(bmain, scene, view_layer, true);
  /* NOTE: if Base selected and has parent selected:
   *   base->flag_legacy = BA_WAS_SEL
   */
  /* Don't do it if we're not actually going to recalculate anything. */
  if (t->mode == TFM_DUMMY) {
    return;
  }
  /* Makes sure base flags and object flags are identical. */
  BKE_scene_base_flag_to_objects(t->view_layer);
  /* Make sure depsgraph is here. */
  DEG_graph_relations_update(depsgraph, bmain, scene, view_layer);
  /* Clear all flags we need. It will be used to detect dependencies. */
  trans_object_base_deps_flag_prepare(view_layer);
  /* Traverse all bases and set all possible flags. */
  for (Base *base = view_layer->object_bases.first; base; base = base->next) {
    base->flag_legacy &= ~(BA_WAS_SEL | BA_TRANSFORM_LOCKED_IN_PLACE);
    if (BASE_SELECTED_EDITABLE(v3d, base)) {
      Object *ob = base->object;
      Object *parsel = ob->parent;
      /* If parent selected, deselect. */
      while (parsel != NULL) {
        if (parsel->base_flag & BASE_SELECTED) {
          Base *parbase = BKE_view_layer_base_find(view_layer, parsel);
          if (parbase != NULL) { /* in rare cases this can fail */
            if (BASE_SELECTED_EDITABLE(v3d, parbase)) {
              break;
            }
          }
        }
        parsel = parsel->parent;
      }
      if (parsel != NULL) {
        /* Rotation around local centers are allowed to propagate. */
        if ((t->around == V3D_AROUND_LOCAL_ORIGINS) &&
            (t->mode == TFM_ROTATION || t->mode == TFM_TRACKBALL)) {
          base->flag_legacy |= BA_TRANSFORM_CHILD;
        }
        else {
          base->flag &= ~BASE_SELECTED;
          base->flag_legacy |= BA_WAS_SEL;
        }
      }
      flush_trans_object_base_deps_flag(depsgraph, ob);
    }
  }
  /* Store temporary bits in base indicating that base is being modified
   * (directly or indirectly) by transforming objects.
   */
  trans_object_base_deps_flag_finish(t, view_layer);
}

static bool mark_children(Object *ob)
{
  if (ob->flag & (SELECT | BA_TRANSFORM_CHILD)) {
    return true;
  }

  if (ob->parent) {
    if (mark_children(ob->parent)) {
      ob->flag |= BA_TRANSFORM_CHILD;
      return true;
    }
  }

  return false;
}

static int count_proportional_objects(TransInfo *t)
{
  int total = 0;
  ViewLayer *view_layer = t->view_layer;
  View3D *v3d = t->view;
  struct Main *bmain = CTX_data_main(t->context);
  Scene *scene = t->scene;
  Depsgraph *depsgraph = BKE_scene_get_depsgraph(bmain, scene, view_layer, true);
  /* Clear all flags we need. It will be used to detect dependencies. */
  trans_object_base_deps_flag_prepare(view_layer);
  /* Rotations around local centers are allowed to propagate, so we take all objects. */
  if (!((t->around == V3D_AROUND_LOCAL_ORIGINS) &&
        (t->mode == TFM_ROTATION || t->mode == TFM_TRACKBALL))) {
    /* Mark all parents. */
    for (Base *base = view_layer->object_bases.first; base; base = base->next) {
      if (BASE_SELECTED_EDITABLE(v3d, base) && BASE_SELECTABLE(v3d, base)) {
        Object *parent = base->object->parent;
        /* flag all parents */
        while (parent != NULL) {
          parent->flag |= BA_TRANSFORM_PARENT;
          parent = parent->parent;
        }
      }
    }
    /* Mark all children. */
    for (Base *base = view_layer->object_bases.first; base; base = base->next) {
      /* all base not already selected or marked that is editable */
      if ((base->object->flag & (BA_TRANSFORM_CHILD | BA_TRANSFORM_PARENT)) == 0 &&
          (base->flag & BASE_SELECTED) == 0 &&
          (BASE_EDITABLE(v3d, base) && BASE_SELECTABLE(v3d, base))) {
        mark_children(base->object);
      }
    }
  }
  /* Flush changed flags to all dependencies. */
  for (Base *base = view_layer->object_bases.first; base; base = base->next) {
    Object *ob = base->object;
    /* If base is not selected, not a parent of selection or not a child of
     * selection and it is editable and selectable.
     */
    if ((ob->flag & (BA_TRANSFORM_CHILD | BA_TRANSFORM_PARENT)) == 0 &&
        (base->flag & BASE_SELECTED) == 0 &&
        (BASE_EDITABLE(v3d, base) && BASE_SELECTABLE(v3d, base))) {
      flush_trans_object_base_deps_flag(depsgraph, ob);
      total += 1;
    }
  }
  /* Store temporary bits in base indicating that base is being modified
   * (directly or indirectly) by transforming objects.
   */
  trans_object_base_deps_flag_finish(t, view_layer);
  return total;
}

void clear_trans_object_base_flags(TransInfo *t)
{
  ViewLayer *view_layer = t->view_layer;
  Base *base;

  for (base = view_layer->object_bases.first; base; base = base->next) {
    if (base->flag_legacy & BA_WAS_SEL) {
      ED_object_base_select(base, BA_SELECT);
    }

    base->flag_legacy &= ~(BA_WAS_SEL | BA_SNAP_FIX_DEPS_FIASCO | BA_TEMP_TAG |
                           BA_TRANSFORM_CHILD | BA_TRANSFORM_PARENT |
                           BA_TRANSFORM_LOCKED_IN_PLACE);
  }
}

void createTransObject(bContext *C, TransInfo *t)
{
  TransData *td = NULL;
  TransDataExtension *tx;
  const bool is_prop_edit = (t->flag & T_PROP_EDIT) != 0;

  set_trans_object_base_flags(t);

  TransDataContainer *tc = TRANS_DATA_CONTAINER_FIRST_SINGLE(t);

  /* count */
  tc->data_len = CTX_DATA_COUNT(C, selected_bases);

  if (!tc->data_len) {
    /* clear here, main transform function escapes too */
    clear_trans_object_base_flags(t);
    return;
  }

  if (is_prop_edit) {
    tc->data_len += count_proportional_objects(t);
  }

  td = tc->data = MEM_callocN(tc->data_len * sizeof(TransData), "TransOb");
  tx = tc->data_ext = MEM_callocN(tc->data_len * sizeof(TransDataExtension), "TransObExtension");

  TransDataObject *tdo = MEM_callocN(sizeof(*tdo), __func__);
  t->custom.type.data = tdo;
  t->custom.type.free_cb = freeTransObjectCustomData;

  CTX_DATA_BEGIN (C, Base *, base, selected_bases) {
    Object *ob = base->object;

    td->flag = TD_SELECTED;
    td->protectflag = ob->protectflag;
    td->ext = tx;
    td->ext->rotOrder = ob->rotmode;

    if (base->flag & BA_TRANSFORM_CHILD) {
      td->flag |= TD_NOCENTER;
      td->flag |= TD_NO_LOC;
    }

    /* select linked objects, but skip them later */
    if (ID_IS_LINKED(ob)) {
      td->flag |= TD_SKIP;
    }

    if (t->options & CTX_OBMODE_XFORM_OBDATA) {
      ID *id = ob->data;
      if (!id || id->lib) {
        td->flag |= TD_SKIP;
      }
      else if (BKE_object_is_in_editmode(ob)) {
        /* The object could have edit-mode data from another view-layer,
         * it's such a corner-case it can be skipped for now - Campbell. */
        td->flag |= TD_SKIP;
      }
    }

    if (t->options & CTX_OBMODE_XFORM_OBDATA) {
      if ((td->flag & TD_SKIP) == 0) {
        trans_obdata_in_obmode_ensure_object(tdo, ob);
      }
    }

    ObjectToTransData(t, td, ob);
    td->val = NULL;
    td++;
    tx++;
  }
  CTX_DATA_END;

  if (is_prop_edit) {
    ViewLayer *view_layer = t->view_layer;
    View3D *v3d = t->view;
    Base *base;

    for (base = view_layer->object_bases.first; base; base = base->next) {
      Object *ob = base->object;

      /* if base is not selected, not a parent of selection
       * or not a child of selection and it is editable and selectable */
      if ((ob->flag & (BA_TRANSFORM_CHILD | BA_TRANSFORM_PARENT)) == 0 &&
          (base->flag & BASE_SELECTED) == 0 && BASE_EDITABLE(v3d, base) &&
          BASE_SELECTABLE(v3d, base)) {
        td->protectflag = ob->protectflag;
        td->ext = tx;
        td->ext->rotOrder = ob->rotmode;

        ObjectToTransData(t, td, ob);
        td->val = NULL;
        td++;
        tx++;
      }
    }
  }

  if (t->options & CTX_OBMODE_XFORM_OBDATA) {
    GSet *objects_in_transdata = BLI_gset_ptr_new_ex(__func__, tc->data_len);
    td = tc->data;
    for (int i = 0; i < tc->data_len; i++, td++) {
      if ((td->flag & TD_SKIP) == 0) {
        BLI_gset_add(objects_in_transdata, td->ob);
      }
    }

    ViewLayer *view_layer = t->view_layer;
    View3D *v3d = t->view;

    for (Base *base = view_layer->object_bases.first; base; base = base->next) {
      Object *ob = base->object;

      /* if base is not selected, not a parent of selection
       * or not a child of selection and it is editable and selectable */
      if ((base->flag_legacy & BA_WAS_SEL) && (base->flag & BASE_SELECTED) == 0 &&
          BASE_EDITABLE(v3d, base) && BASE_SELECTABLE(v3d, base)) {

        Object *ob_parent = ob->parent;
        if (ob_parent != NULL) {
          if (!BLI_gset_haskey(objects_in_transdata, ob)) {
            bool parent_in_transdata = false;
            while (ob_parent != NULL) {
              if (BLI_gset_haskey(objects_in_transdata, ob_parent)) {
                parent_in_transdata = true;
                break;
              }
              ob_parent = ob_parent->parent;
            }
            if (parent_in_transdata) {
              trans_obdata_in_obmode_ensure_object(tdo, ob);
            }
          }
        }
      }
    }
    BLI_gset_free(objects_in_transdata, NULL);
  }

  if (t->options & CTX_OBMODE_XFORM_SKIP_CHILDREN) {

#define BASE_XFORM_INDIRECT(base) \
  ((base->flag_legacy & BA_WAS_SEL) && (base->flag & BASE_SELECTED) == 0)

    GSet *objects_in_transdata = BLI_gset_ptr_new_ex(__func__, tc->data_len);
    GHash *objects_parent_root = BLI_ghash_ptr_new_ex(__func__, tc->data_len);
    td = tc->data;
    for (int i = 0; i < tc->data_len; i++, td++) {
      if ((td->flag & TD_SKIP) == 0) {
        BLI_gset_add(objects_in_transdata, td->ob);
      }
    }

    ViewLayer *view_layer = t->view_layer;

    for (Base *base = view_layer->object_bases.first; base; base = base->next) {
      Object *ob = base->object;
      if (ob->parent != NULL) {
        if (ob->parent && !BLI_gset_haskey(objects_in_transdata, ob->parent) &&
            !BLI_gset_haskey(objects_in_transdata, ob)) {
          if (((base->flag_legacy & BA_WAS_SEL) && (base->flag & BASE_SELECTED) == 0)) {
            Base *base_parent = BKE_view_layer_base_find(view_layer, ob->parent);
            if (base_parent && !BASE_XFORM_INDIRECT(base_parent)) {
              Object *ob_parent_recurse = ob->parent;
              if (ob_parent_recurse != NULL) {
                while (ob_parent_recurse != NULL) {
                  if (BLI_gset_haskey(objects_in_transdata, ob_parent_recurse)) {
                    break;
                  }
                  ob_parent_recurse = ob_parent_recurse->parent;
                }

                if (ob_parent_recurse) {
                  trans_obchild_in_obmode_ensure_object(
                      tdo, ob, ob_parent_recurse, OB_SKIP_CHILD_PARENT_APPLY_TRANSFORM);
                  BLI_ghash_insert(objects_parent_root, ob, ob_parent_recurse);
                  base->flag_legacy |= BA_TRANSFORM_LOCKED_IN_PLACE;
                }
              }
            }
          }
        }
      }
    }

    for (Base *base = view_layer->object_bases.first; base; base = base->next) {
      Object *ob = base->object;

      if (BASE_XFORM_INDIRECT(base) || BLI_gset_haskey(objects_in_transdata, ob)) {
        /* pass. */
      }
      else if (ob->parent != NULL) {
        Base *base_parent = BKE_view_layer_base_find(view_layer, ob->parent);
        if (base_parent) {
          if (BASE_XFORM_INDIRECT(base_parent) ||
              BLI_gset_haskey(objects_in_transdata, ob->parent)) {
            trans_obchild_in_obmode_ensure_object(tdo, ob, NULL, OB_SKIP_CHILD_PARENT_IS_XFORM);
            base->flag_legacy |= BA_TRANSFORM_LOCKED_IN_PLACE;
          }
          else {
            Object *ob_parent_recurse = BLI_ghash_lookup(objects_parent_root, ob->parent);
            if (ob_parent_recurse) {
              trans_obchild_in_obmode_ensure_object(
                  tdo, ob, ob_parent_recurse, OB_SKIP_CHILD_PARENT_IS_XFORM_INDIRECT);
            }
          }
        }
      }
    }
    BLI_gset_free(objects_in_transdata, NULL);
    BLI_ghash_free(objects_parent_root, NULL, NULL);

#undef BASE_XFORM_INDIRECT
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Texture Space Transform Creation
 *
 * Instead of transforming the selection, move the 2D/3D cursor.
 *
 * \{ */

void createTransTexspace(TransInfo *t)
{
  ViewLayer *view_layer = t->view_layer;
  TransData *td;
  Object *ob;
  ID *id;
  short *texflag;

  ob = OBACT(view_layer);

  if (ob == NULL) {  // Shouldn't logically happen, but still...
    return;
  }

  id = ob->data;
  if (id == NULL || !ELEM(GS(id->name), ID_ME, ID_CU, ID_MB)) {
    BKE_report(t->reports, RPT_ERROR, "Unsupported object type for text-space transform");
    return;
  }

  if (BKE_object_obdata_is_libdata(ob)) {
    BKE_report(t->reports, RPT_ERROR, "Linked data can't text-space transform");
    return;
  }

  {
    BLI_assert(t->data_container_len == 1);
    TransDataContainer *tc = t->data_container;
    tc->data_len = 1;
    td = tc->data = MEM_callocN(sizeof(TransData), "TransTexspace");
    td->ext = tc->data_ext = MEM_callocN(sizeof(TransDataExtension), "TransTexspace");
  }

  td->flag = TD_SELECTED;
  copy_v3_v3(td->center, ob->obmat[3]);
  td->ob = ob;

  copy_m3_m4(td->mtx, ob->obmat);
  copy_m3_m4(td->axismtx, ob->obmat);
  normalize_m3(td->axismtx);
  pseudoinverse_m3_m3(td->smtx, td->mtx, PSEUDOINVERSE_EPSILON);

  if (BKE_object_obdata_texspace_get(ob, &texflag, &td->loc, &td->ext->size)) {
    ob->dtx |= OB_TEXSPACE;
    *texflag &= ~ME_AUTOSPACE;
  }

  copy_v3_v3(td->iloc, td->loc);
  copy_v3_v3(td->ext->isize, td->ext->size);
}

/** \} */
