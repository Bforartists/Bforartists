/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edarmature
 */

#include <cstring>

#include "DNA_anim_types.h"
#include "DNA_armature_types.h"
#include "DNA_constraint_types.h"
#include "DNA_gpencil_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"

#include "BKE_action.h"
#include "BKE_armature.h"
#include "BKE_constraint.h"
#include "BKE_context.h"
#include "BKE_gpencil_modifier_legacy.h"
#include "BKE_layer.h"
#include "BKE_modifier.h"
#include "BKE_object.hh"
#include "BKE_report.h"

#include "DEG_depsgraph.hh"

#include "RNA_access.hh"
#include "RNA_define.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "ED_armature.hh"
#include "ED_keyframing.hh"
#include "ED_mesh.hh"
#include "ED_object.hh"
#include "ED_outliner.hh"
#include "ED_screen.hh"
#include "ED_select_utils.hh"
#include "ED_view3d.hh"

#include "ANIM_bone_collections.h"
#include "ANIM_bonecolor.hh"

#include "armature_intern.h"

/* utility macros for storing a temp int in the bone (selection flag) */
#define PBONE_PREV_FLAG_GET(pchan) ((void)0, POINTER_AS_INT((pchan)->temp))
#define PBONE_PREV_FLAG_SET(pchan, val) ((pchan)->temp = POINTER_FROM_INT(val))

/* ***************** Pose Select Utilities ********************* */

/* NOTE: SEL_TOGGLE is assumed to have already been handled! */
static void pose_do_bone_select(bPoseChannel *pchan, const int select_mode)
{
  /* select pchan only if selectable, but deselect works always */
  switch (select_mode) {
    case SEL_SELECT:
      if (!(pchan->bone->flag & BONE_UNSELECTABLE)) {
        pchan->bone->flag |= BONE_SELECTED;
      }
      break;
    case SEL_DESELECT:
      pchan->bone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
      break;
    case SEL_INVERT:
      if (pchan->bone->flag & BONE_SELECTED) {
        pchan->bone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
      }
      else if (!(pchan->bone->flag & BONE_UNSELECTABLE)) {
        pchan->bone->flag |= BONE_SELECTED;
      }
      break;
  }
}

void ED_pose_bone_select_tag_update(Object *ob)
{
  BLI_assert(ob->type == OB_ARMATURE);
  bArmature *arm = static_cast<bArmature *>(ob->data);
  WM_main_add_notifier(NC_OBJECT | ND_BONE_SELECT, ob);
  WM_main_add_notifier(NC_GEOM | ND_DATA, ob);

  if (arm->flag & ARM_HAS_VIZ_DEPS) {
    /* mask modifier ('armature' mode), etc. */
    DEG_id_tag_update(&ob->id, ID_RECALC_GEOMETRY);
  }

  DEG_id_tag_update(&arm->id, ID_RECALC_SELECT);
}

void ED_pose_bone_select(Object *ob, bPoseChannel *pchan, bool select, bool change_active)
{
  bArmature *arm;

  /* sanity checks */
  /* XXX: actually, we can probably still get away with no object - at most we have no updates */
  if (ELEM(nullptr, ob, ob->pose, pchan, pchan->bone)) {
    return;
  }

  arm = static_cast<bArmature *>(ob->data);

  /* can only change selection state if bone can be modified */
  if (PBONE_SELECTABLE(arm, pchan->bone)) {
    /* change selection state - activate too if selected */
    if (select) {
      pchan->bone->flag |= BONE_SELECTED;
      if (change_active) {
        arm->act_bone = pchan->bone;
      }
    }
    else {
      pchan->bone->flag &= ~BONE_SELECTED;
      if (change_active) {
        arm->act_bone = nullptr;
      }
    }

    /* TODO: select and activate corresponding vgroup? */
    ED_pose_bone_select_tag_update(ob);
  }
}

bool ED_armature_pose_select_pick_bone(const Scene *scene,
                                       ViewLayer *view_layer,
                                       View3D *v3d,
                                       Object *ob,
                                       Bone *bone,
                                       const SelectPick_Params *params)
{
  bool found = false;
  bool changed = false;

  if (ob || ob->pose) {
    if (bone && ((bone->flag & BONE_UNSELECTABLE) == 0)) {
      found = true;
    }
  }

  if (params->sel_op == SEL_OP_SET) {
    if ((found && params->select_passthrough) && (bone->flag & BONE_SELECTED)) {
      found = false;
    }
    else if (found || params->deselect_all) {
      /* Deselect everything. */
      /* Don't use 'BKE_object_pose_base_array_get_unique'
       * because we may be selecting from object mode. */
      FOREACH_VISIBLE_BASE_BEGIN (scene, view_layer, v3d, base_iter) {
        Object *ob_iter = base_iter->object;
        if ((ob_iter->type == OB_ARMATURE) && (ob_iter->mode & OB_MODE_POSE)) {
          if (ED_pose_deselect_all(ob_iter, SEL_DESELECT, true)) {
            ED_pose_bone_select_tag_update(ob_iter);
          }
        }
      }
      FOREACH_VISIBLE_BASE_END;
      changed = true;
    }
  }

  if (found) {
    BKE_view_layer_synced_ensure(scene, view_layer);
    Object *ob_act = BKE_view_layer_active_object_get(view_layer);
    BLI_assert(BKE_view_layer_edit_object_get(view_layer) == nullptr);

    /* If the bone cannot be affected, don't do anything. */
    bArmature *arm = static_cast<bArmature *>(ob->data);

    /* Since we do unified select, we don't shift+select a bone if the
     * armature object was not active yet.
     * NOTE(@ideasman42): special exception for armature mode so we can do multi-select
     * we could check for multi-select explicitly but think its fine to
     * always give predictable behavior in weight paint mode. */
    if ((ob_act == nullptr) || ((ob_act != ob) && (ob_act->mode & OB_MODE_ALL_WEIGHT_PAINT) == 0))
    {
      /* When we are entering into posemode via toggle-select,
       * from another active object - always select the bone. */
      if (params->sel_op == SEL_OP_SET) {
        /* Re-select the bone again later in this function. */
        bone->flag &= ~BONE_SELECTED;
      }
    }

    switch (params->sel_op) {
      case SEL_OP_ADD: {
        bone->flag |= (BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
        arm->act_bone = bone;
        break;
      }
      case SEL_OP_SUB: {
        bone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
        break;
      }
      case SEL_OP_XOR: {
        if (bone->flag & BONE_SELECTED) {
          /* If not active, we make it active. */
          if (bone != arm->act_bone) {
            arm->act_bone = bone;
          }
          else {
            bone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
          }
        }
        else {
          bone->flag |= (BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
          arm->act_bone = bone;
        }
        break;
      }
      case SEL_OP_SET: {
        bone->flag |= (BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
        arm->act_bone = bone;
        break;
      }
      case SEL_OP_AND: {
        BLI_assert_unreachable(); /* Doesn't make sense for picking. */
        break;
      }
    }

    if (ob_act) {
      /* In weight-paint we select the associated vertex group too. */
      if (ob_act->mode & OB_MODE_ALL_WEIGHT_PAINT) {
        if (bone == arm->act_bone) {
          ED_vgroup_select_by_name(ob_act, bone->name);
          DEG_id_tag_update(&ob_act->id, ID_RECALC_GEOMETRY);
        }
      }
      /* If there are some dependencies for visualizing armature state
       * (e.g. Mask Modifier in 'Armature' mode), force update.
       */
      else if (arm->flag & ARM_HAS_VIZ_DEPS) {
        /* NOTE: ob not ob_act here is intentional - it's the source of the
         *       bones being selected [#37247].
         */
        DEG_id_tag_update(&ob->id, ID_RECALC_GEOMETRY);
      }

      /* Tag armature for copy-on-write update (since act_bone is in armature not object). */
      DEG_id_tag_update(&arm->id, ID_RECALC_COPY_ON_WRITE);
    }

    changed = true;
  }

  return changed || found;
}

bool ED_armature_pose_select_pick_with_buffer(const Scene *scene,
                                              ViewLayer *view_layer,
                                              View3D *v3d,
                                              Base *base,
                                              const GPUSelectResult *buffer,
                                              const short hits,
                                              const SelectPick_Params *params,
                                              bool do_nearest)
{
  Object *ob = base->object;
  Bone *nearBone;

  if (!ob || !ob->pose) {
    return false;
  }

  /* Callers happen to already get the active base */
  Base *base_dummy = nullptr;
  nearBone = ED_armature_pick_bone_from_selectbuffer(
      &base, 1, buffer, hits, true, do_nearest, &base_dummy);

  return ED_armature_pose_select_pick_bone(scene, view_layer, v3d, ob, nearBone, params);
}

void ED_armature_pose_select_in_wpaint_mode(const Scene *scene,
                                            ViewLayer *view_layer,
                                            Base *base_select)
{
  BLI_assert(base_select && (base_select->object->type == OB_ARMATURE));
  BKE_view_layer_synced_ensure(scene, view_layer);
  Object *ob_active = BKE_view_layer_active_object_get(view_layer);
  BLI_assert(ob_active && (ob_active->mode & OB_MODE_ALL_WEIGHT_PAINT));

  if (ob_active->type == OB_GPENCIL_LEGACY) {
    GpencilVirtualModifierData virtual_modifier_data;
    GpencilModifierData *md = BKE_gpencil_modifiers_get_virtual_modifierlist(
        ob_active, &virtual_modifier_data);
    for (; md; md = md->next) {
      if (md->type == eGpencilModifierType_Armature) {
        ArmatureGpencilModifierData *agmd = (ArmatureGpencilModifierData *)md;
        Object *ob_arm = agmd->object;
        if (ob_arm != nullptr) {
          Base *base_arm = BKE_view_layer_base_find(view_layer, ob_arm);
          if ((base_arm != nullptr) && (base_arm != base_select) &&
              (base_arm->flag & BASE_SELECTED)) {
            ED_object_base_select(base_arm, BA_DESELECT);
          }
        }
      }
    }
  }
  else {
    VirtualModifierData virtual_modifier_data;
    ModifierData *md = BKE_modifiers_get_virtual_modifierlist(ob_active, &virtual_modifier_data);
    for (; md; md = md->next) {
      if (md->type == eModifierType_Armature) {
        ArmatureModifierData *amd = (ArmatureModifierData *)md;
        Object *ob_arm = amd->object;
        if (ob_arm != nullptr) {
          Base *base_arm = BKE_view_layer_base_find(view_layer, ob_arm);
          if ((base_arm != nullptr) && (base_arm != base_select) &&
              (base_arm->flag & BASE_SELECTED)) {
            ED_object_base_select(base_arm, BA_DESELECT);
          }
        }
      }
    }
  }
  if ((base_select->flag & BASE_SELECTED) == 0) {
    ED_object_base_select(base_select, BA_SELECT);
  }
}

bool ED_pose_deselect_all(Object *ob, int select_mode, const bool ignore_visibility)
{
  bArmature *arm = static_cast<bArmature *>(ob->data);

  /* we call this from outliner too */
  if (ob->pose == nullptr) {
    return false;
  }

  /* Determine if we're selecting or deselecting */
  if (select_mode == SEL_TOGGLE) {
    select_mode = SEL_SELECT;
    LISTBASE_FOREACH (bPoseChannel *, pchan, &ob->pose->chanbase) {
      if (ignore_visibility || PBONE_VISIBLE(arm, pchan->bone)) {
        if (pchan->bone->flag & BONE_SELECTED) {
          select_mode = SEL_DESELECT;
          break;
        }
      }
    }
  }

  /* Set the flags accordingly */
  bool changed = false;
  LISTBASE_FOREACH (bPoseChannel *, pchan, &ob->pose->chanbase) {
    /* ignore the pchan if it isn't visible or if its selection cannot be changed */
    if (ignore_visibility || PBONE_VISIBLE(arm, pchan->bone)) {
      int flag_prev = pchan->bone->flag;
      pose_do_bone_select(pchan, select_mode);
      changed = (changed || flag_prev != pchan->bone->flag);
    }
  }
  return changed;
}

static bool ed_pose_is_any_selected(Object *ob, bool ignore_visibility)
{
  bArmature *arm = static_cast<bArmature *>(ob->data);
  LISTBASE_FOREACH (bPoseChannel *, pchan, &ob->pose->chanbase) {
    if (ignore_visibility || PBONE_VISIBLE(arm, pchan->bone)) {
      if (pchan->bone->flag & BONE_SELECTED) {
        return true;
      }
    }
  }
  return false;
}

static bool ed_pose_is_any_selected_multi(Base **bases, uint bases_len, bool ignore_visibility)
{
  for (uint base_index = 0; base_index < bases_len; base_index++) {
    Object *ob_iter = bases[base_index]->object;
    if (ed_pose_is_any_selected(ob_iter, ignore_visibility)) {
      return true;
    }
  }
  return false;
}

bool ED_pose_deselect_all_multi_ex(Base **bases,
                                   uint bases_len,
                                   int select_mode,
                                   const bool ignore_visibility)
{
  if (select_mode == SEL_TOGGLE) {
    select_mode = ed_pose_is_any_selected_multi(bases, bases_len, ignore_visibility) ?
                      SEL_DESELECT :
                      SEL_SELECT;
  }

  bool changed_multi = false;
  for (uint base_index = 0; base_index < bases_len; base_index++) {
    Object *ob_iter = bases[base_index]->object;
    if (ED_pose_deselect_all(ob_iter, select_mode, ignore_visibility)) {
      ED_pose_bone_select_tag_update(ob_iter);
      changed_multi = true;
    }
  }
  return changed_multi;
}

bool ED_pose_deselect_all_multi(bContext *C, int select_mode, const bool ignore_visibility)
{
  Depsgraph *depsgraph = CTX_data_ensure_evaluated_depsgraph(C);
  ViewContext vc = ED_view3d_viewcontext_init(C, depsgraph);
  uint bases_len = 0;

  Base **bases = BKE_object_pose_base_array_get_unique(
      vc.scene, vc.view_layer, vc.v3d, &bases_len);
  bool changed_multi = ED_pose_deselect_all_multi_ex(
      bases, bases_len, select_mode, ignore_visibility);
  MEM_freeN(bases);
  return changed_multi;
}

/* ***************** Selections ********************** */

static void selectconnected_posebonechildren(Object *ob, Bone *bone, int extend)
{
  /* stop when unconnected child is encountered, or when unselectable bone is encountered */
  if (!(bone->flag & BONE_CONNECTED) || (bone->flag & BONE_UNSELECTABLE)) {
    return;
  }

  if (extend) {
    bone->flag &= ~BONE_SELECTED;
  }
  else {
    bone->flag |= BONE_SELECTED;
  }

  LISTBASE_FOREACH (Bone *, curBone, &bone->childbase) {
    selectconnected_posebonechildren(ob, curBone, extend);
  }
}

/* within active object context */
/* previously known as "selectconnected_posearmature" */
static int pose_select_connected_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
  Bone *bone, *curBone, *next = nullptr;
  const bool extend = RNA_boolean_get(op->ptr, "extend");

  view3d_operator_needs_opengl(C);

  Base *base = nullptr;
  bone = ED_armature_pick_bone(C, event->mval, !extend, &base);

  if (!bone) {
    return OPERATOR_CANCELLED;
  }

  /* Select parents */
  for (curBone = bone; curBone; curBone = next) {
    /* ignore bone if cannot be selected */
    if ((curBone->flag & BONE_UNSELECTABLE) == 0) {
      if (extend) {
        curBone->flag &= ~BONE_SELECTED;
      }
      else {
        curBone->flag |= BONE_SELECTED;
      }

      if (curBone->flag & BONE_CONNECTED) {
        next = curBone->parent;
      }
      else {
        next = nullptr;
      }
    }
    else {
      next = nullptr;
    }
  }

  /* Select children */
  LISTBASE_FOREACH (Bone *, curBone, &bone->childbase) {
    selectconnected_posebonechildren(base->object, curBone, extend);
  }

  ED_outliner_select_sync_from_pose_bone_tag(C);

  ED_pose_bone_select_tag_update(base->object);

  return OPERATOR_FINISHED;
}

static bool pose_select_linked_pick_poll(bContext *C)
{
  return (ED_operator_view3d_active(C) && ED_operator_posemode(C));
}

void POSE_OT_select_linked_pick(wmOperatorType *ot)
{
  PropertyRNA *prop;

  /* identifiers */
  ot->name = "Select Connected";
  ot->idname = "POSE_OT_select_linked_pick";
  ot->description = "Select bones linked by parent/child connections under the mouse cursor";

  /* callbacks */
  /* leave 'exec' unset */
  ot->invoke = pose_select_connected_invoke;
  ot->poll = pose_select_linked_pick_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* props */
  prop = RNA_def_boolean(ot->srna,
                         "extend",
                         false,
                         "Extend",
                         "Extend selection instead of deselecting everything first");
  RNA_def_property_flag(prop, PROP_SKIP_SAVE);
}

static int pose_select_linked_exec(bContext *C, wmOperator * /*op*/)
{
  Bone *curBone, *next = nullptr;

  CTX_DATA_BEGIN_WITH_ID (C, bPoseChannel *, pchan, visible_pose_bones, Object *, ob) {
    if ((pchan->bone->flag & BONE_SELECTED) == 0) {
      continue;
    }

    bArmature *arm = static_cast<bArmature *>(ob->data);

    /* Select parents */
    for (curBone = pchan->bone; curBone; curBone = next) {
      if (PBONE_SELECTABLE(arm, curBone)) {
        curBone->flag |= BONE_SELECTED;

        if (curBone->flag & BONE_CONNECTED) {
          next = curBone->parent;
        }
        else {
          next = nullptr;
        }
      }
      else {
        next = nullptr;
      }
    }

    /* Select children */
    LISTBASE_FOREACH (Bone *, curBone, &pchan->bone->childbase) {
      selectconnected_posebonechildren(ob, curBone, false);
    }
    ED_pose_bone_select_tag_update(ob);
  }
  CTX_DATA_END;

  ED_outliner_select_sync_from_pose_bone_tag(C);

  return OPERATOR_FINISHED;
}

void POSE_OT_select_linked(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Select Connected";
  ot->idname = "POSE_OT_select_linked";
  ot->description = "Select all bones linked by parent/child connections to the current selection";

  /* callbacks */
  ot->exec = pose_select_linked_exec;
  ot->poll = ED_operator_posemode;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* -------------------------------------- */

static int pose_de_select_all_exec(bContext *C, wmOperator *op)
{
  int action = RNA_enum_get(op->ptr, "action");

  Scene *scene = CTX_data_scene(C);
  int multipaint = scene->toolsettings->multipaint;

  if (action == SEL_TOGGLE) {
    action = CTX_DATA_COUNT(C, selected_pose_bones) ? SEL_DESELECT : SEL_SELECT;
  }

  Object *ob_prev = nullptr;

  /* Set the flags. */
  CTX_DATA_BEGIN_WITH_ID (C, bPoseChannel *, pchan, visible_pose_bones, Object *, ob) {
    bArmature *arm = static_cast<bArmature *>(ob->data);
    pose_do_bone_select(pchan, action);

    if (ob_prev != ob) {
      /* Weight-paint or mask modifiers need depsgraph updates. */
      if (multipaint || (arm->flag & ARM_HAS_VIZ_DEPS)) {
        DEG_id_tag_update(&ob->id, ID_RECALC_GEOMETRY);
      }
      /* need to tag armature for cow updates, or else selection doesn't update */
      DEG_id_tag_update(&arm->id, ID_RECALC_COPY_ON_WRITE);
      ob_prev = ob;
    }
  }
  CTX_DATA_END;

  ED_outliner_select_sync_from_pose_bone_tag(C);

  WM_event_add_notifier(C, NC_OBJECT | ND_BONE_SELECT, nullptr);

  return OPERATOR_FINISHED;
}

void POSE_OT_select_all(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "(De)select All";
  ot->idname = "POSE_OT_select_all";
  ot->description = "Toggle selection status of all bones";

  /* api callbacks */
  ot->exec = pose_de_select_all_exec;
  ot->poll = ED_operator_posemode;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  WM_operator_properties_select_all(ot);
}

/* -------------------------------------- */

static int pose_select_parent_exec(bContext *C, wmOperator * /*op*/)
{
  Object *ob = BKE_object_pose_armature_get(CTX_data_active_object(C));
  bArmature *arm = (bArmature *)ob->data;
  bPoseChannel *pchan, *parent;

  /* Determine if there is an active bone */
  pchan = CTX_data_active_pose_bone(C);
  if (pchan) {
    parent = pchan->parent;
    if ((parent) && !(parent->bone->flag & (BONE_HIDDEN_P | BONE_UNSELECTABLE))) {
      parent->bone->flag |= BONE_SELECTED;
      arm->act_bone = parent->bone;
    }
    else {
      return OPERATOR_CANCELLED;
    }
  }
  else {
    return OPERATOR_CANCELLED;
  }

  ED_outliner_select_sync_from_pose_bone_tag(C);

  ED_pose_bone_select_tag_update(ob);
  return OPERATOR_FINISHED;
}

void POSE_OT_select_parent(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Select Parent Bone";
  ot->idname = "POSE_OT_select_parent";
  ot->description = "Select bones that are parents of the currently selected bones";

  /* api callbacks */
  ot->exec = pose_select_parent_exec;
  ot->poll = ED_operator_posemode;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* -------------------------------------- */

static int pose_select_constraint_target_exec(bContext *C, wmOperator * /*op*/)
{
  int found = 0;

  CTX_DATA_BEGIN (C, bPoseChannel *, pchan, visible_pose_bones) {
    if (pchan->bone->flag & BONE_SELECTED) {
      LISTBASE_FOREACH (bConstraint *, con, &pchan->constraints) {
        ListBase targets = {nullptr, nullptr};
        if (BKE_constraint_targets_get(con, &targets)) {
          LISTBASE_FOREACH (bConstraintTarget *, ct, &targets) {
            Object *ob = ct->tar;

            /* Any armature that is also in pose mode should be selected. */
            if ((ct->subtarget[0] != '\0') && (ob != nullptr) && (ob->type == OB_ARMATURE) &&
                (ob->mode == OB_MODE_POSE))
            {
              bPoseChannel *pchanc = BKE_pose_channel_find_name(ob->pose, ct->subtarget);
              if ((pchanc) && !(pchanc->bone->flag & BONE_UNSELECTABLE)) {
                pchanc->bone->flag |= BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL;
                ED_pose_bone_select_tag_update(ob);
                found = 1;
              }
            }
          }

          BKE_constraint_targets_flush(con, &targets, true);
        }
      }
    }
  }
  CTX_DATA_END;

  if (!found) {
    return OPERATOR_CANCELLED;
  }

  ED_outliner_select_sync_from_pose_bone_tag(C);

  return OPERATOR_FINISHED;
}

void POSE_OT_select_constraint_target(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Select Constraint Target";
  ot->idname = "POSE_OT_select_constraint_target";
  ot->description = "Select bones used as targets for the currently selected bones";

  /* api callbacks */
  ot->exec = pose_select_constraint_target_exec;
  ot->poll = ED_operator_posemode;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* -------------------------------------- */

/* No need to convert to multi-objects. Just like we keep the non-active bones
 * selected we then keep the non-active objects untouched (selected/unselected). */
static int pose_select_hierarchy_exec(bContext *C, wmOperator *op)
{
  Object *ob = BKE_object_pose_armature_get(CTX_data_active_object(C));
  bArmature *arm = static_cast<bArmature *>(ob->data);
  bPoseChannel *pchan_act;
  int direction = RNA_enum_get(op->ptr, "direction");
  const bool add_to_sel = RNA_boolean_get(op->ptr, "extend");
  bool changed = false;

  pchan_act = BKE_pose_channel_active_if_bonecoll_visible(ob);
  if (pchan_act == nullptr) {
    return OPERATOR_CANCELLED;
  }

  if (direction == BONE_SELECT_PARENT) {
    if (pchan_act->parent) {
      Bone *bone_parent;
      bone_parent = pchan_act->parent->bone;

      if (PBONE_SELECTABLE(arm, bone_parent)) {
        if (!add_to_sel) {
          pchan_act->bone->flag &= ~BONE_SELECTED;
        }
        bone_parent->flag |= BONE_SELECTED;
        arm->act_bone = bone_parent;

        changed = true;
      }
    }
  }
  else { /* direction == BONE_SELECT_CHILD */
    Bone *bone_child = nullptr;
    int pass;

    /* first pass, only connected bones (the logical direct child) */
    for (pass = 0; pass < 2 && (bone_child == nullptr); pass++) {
      LISTBASE_FOREACH (bPoseChannel *, pchan_iter, &ob->pose->chanbase) {
        /* possible we have multiple children, some invisible */
        if (PBONE_SELECTABLE(arm, pchan_iter->bone)) {
          if (pchan_iter->parent == pchan_act) {
            if ((pass == 1) || (pchan_iter->bone->flag & BONE_CONNECTED)) {
              bone_child = pchan_iter->bone;
              break;
            }
          }
        }
      }
    }

    if (bone_child) {
      arm->act_bone = bone_child;

      if (!add_to_sel) {
        pchan_act->bone->flag &= ~BONE_SELECTED;
      }
      bone_child->flag |= BONE_SELECTED;

      changed = true;
    }
  }

  if (changed == false) {
    return OPERATOR_CANCELLED;
  }

  ED_outliner_select_sync_from_pose_bone_tag(C);

  ED_pose_bone_select_tag_update(ob);

  return OPERATOR_FINISHED;
}

void POSE_OT_select_hierarchy(wmOperatorType *ot)
{
  static const EnumPropertyItem direction_items[] = {
      {BONE_SELECT_PARENT, "PARENT", 0, "Select Parent", ""},
      {BONE_SELECT_CHILD, "CHILD", 0, "Select Child", ""},
      {0, nullptr, 0, nullptr, nullptr},
  };

  /* identifiers */
  ot->name = "Select Hierarchy";
  ot->idname = "POSE_OT_select_hierarchy";
  ot->description = "Select immediate parent/children of selected bones";

  /* api callbacks */
  ot->exec = pose_select_hierarchy_exec;
  ot->poll = ED_operator_posemode;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* props */
  ot->prop = RNA_def_enum(
      ot->srna, "direction", direction_items, BONE_SELECT_PARENT, "Direction", "");
  RNA_def_boolean(ot->srna, "extend", false, "Extend", "Extend the selection");
}

/* -------------------------------------- */

/* modes for select same */
enum ePose_SelectSame_Mode {
  POSE_SEL_SAME_COLLECTION = 0,
  POSE_SEL_SAME_COLOR = 1,
  POSE_SEL_SAME_KEYINGSET = 2,
};

static bool pose_select_same_color(bContext *C, const bool extend)
{
  /* Get a set of all the colors of the selected bones. */
  blender::Set<blender::animrig::BoneColor> used_colors;
  blender::Set<Object *> updated_objects;
  bool changed_any_selection = false;

  /* Old approach that we may want to reinstate behind some option at some point. This will match
   * against the colors of all selected bones, instead of just the active one. It also explains why
   * there is a set of colors to begin with.
   *
   * CTX_DATA_BEGIN (C, bPoseChannel *, pchan, selected_pose_bones) {
   *   auto color = blender::animrig::ANIM_bonecolor_posebone_get(pchan);
   *   used_colors.add(color);
   * }
   * CTX_DATA_END;
   */
  if (!extend) {
    CTX_DATA_BEGIN_WITH_ID (C, bPoseChannel *, pchan, selected_pose_bones, Object *, ob) {
      pchan->bone->flag &= ~BONE_SELECTED;
      updated_objects.add(ob);
      changed_any_selection = true;
    }
    CTX_DATA_END;
  }

  /* Use the color of the active pose bone. */
  bPoseChannel *active_pose_bone = CTX_data_active_pose_bone(C);
  auto color = blender::animrig::ANIM_bonecolor_posebone_get(active_pose_bone);
  used_colors.add(color);

  /* Select all visible bones that have the same color. */
  CTX_DATA_BEGIN_WITH_ID (C, bPoseChannel *, pchan, visible_pose_bones, Object *, ob) {
    Bone *bone = pchan->bone;
    if (bone->flag & (BONE_UNSELECTABLE | BONE_SELECTED)) {
      /* Skip bones that are unselectable or already selected. */
      continue;
    }

    auto color = blender::animrig::ANIM_bonecolor_posebone_get(pchan);
    if (!used_colors.contains(color)) {
      continue;
    }

    bone->flag |= BONE_SELECTED;
    changed_any_selection = true;
    updated_objects.add(ob);
  }
  CTX_DATA_END;

  if (!changed_any_selection) {
    return false;
  }

  for (Object *ob : updated_objects) {
    ED_pose_bone_select_tag_update(ob);
  }
  return true;
}

static bool pose_select_same_collection(bContext *C, const bool extend)
{
  bool changed_any_selection = false;
  blender::Set<Object *> updated_objects;

  /* Refuse to do anything if there is no active pose bone. */
  bPoseChannel *active_pchan = CTX_data_active_pose_bone(C);
  if (!active_pchan) {
    return false;
  }

  if (!extend) {
    /* Deselect all the bones. */
    CTX_DATA_BEGIN_WITH_ID (C, bPoseChannel *, pchan, selected_pose_bones, Object *, ob) {
      pchan->bone->flag &= ~BONE_SELECTED;
      updated_objects.add(ob);
      changed_any_selection = true;
    }
    CTX_DATA_END;
  }

  /* Build a set of bone collection names, to allow cross-Armature selection. */
  blender::Set<std::string> collection_names;
  LISTBASE_FOREACH (BoneCollectionReference *, bcoll_ref, &active_pchan->bone->runtime.collections)
  {
    collection_names.add(bcoll_ref->bcoll->name);
  }

  /* Select all bones that match any of the collection names. */
  CTX_DATA_BEGIN_WITH_ID (C, bPoseChannel *, pchan, visible_pose_bones, Object *, ob) {
    Bone *bone = pchan->bone;
    if (bone->flag & (BONE_UNSELECTABLE | BONE_SELECTED)) {
      continue;
    }

    LISTBASE_FOREACH (BoneCollectionReference *, bcoll_ref, &bone->runtime.collections) {
      if (!collection_names.contains(bcoll_ref->bcoll->name)) {
        continue;
      }

      bone->flag |= BONE_SELECTED;
      changed_any_selection = true;
      updated_objects.add(ob);
    }
  }
  CTX_DATA_END;

  for (Object *ob : updated_objects) {
    ED_pose_bone_select_tag_update(ob);
  }

  return changed_any_selection;
}

static bool pose_select_same_keyingset(bContext *C, ReportList *reports, bool extend)
{
  Scene *scene = CTX_data_scene(C);
  ViewLayer *view_layer = CTX_data_view_layer(C);
  bool changed_multi = false;
  KeyingSet *ks = ANIM_scene_get_active_keyingset(CTX_data_scene(C));

  /* sanity checks: validate Keying Set and object */
  if (ks == nullptr) {
    BKE_report(reports, RPT_ERROR, "No active Keying Set to use");
    return false;
  }
  if (ANIM_validate_keyingset(C, nullptr, ks) != 0) {
    if (ks->paths.first == nullptr) {
      if ((ks->flag & KEYINGSET_ABSOLUTE) == 0) {
        BKE_report(reports,
                   RPT_ERROR,
                   "Use another Keying Set, as the active one depends on the currently "
                   "selected items or cannot find any targets due to unsuitable context");
      }
      else {
        BKE_report(reports, RPT_ERROR, "Keying Set does not contain any paths");
      }
    }
    return false;
  }

  /* if not extending selection, deselect all selected first */
  if (extend == false) {
    CTX_DATA_BEGIN (C, bPoseChannel *, pchan, visible_pose_bones) {
      if ((pchan->bone->flag & BONE_UNSELECTABLE) == 0) {
        pchan->bone->flag &= ~BONE_SELECTED;
      }
    }
    CTX_DATA_END;
  }

  uint objects_len = 0;
  Object **objects = BKE_object_pose_array_get_unique(
      scene, view_layer, CTX_wm_view3d(C), &objects_len);

  for (uint ob_index = 0; ob_index < objects_len; ob_index++) {
    Object *ob = BKE_object_pose_armature_get(objects[ob_index]);
    bArmature *arm = static_cast<bArmature *>((ob) ? ob->data : nullptr);
    bPose *pose = (ob) ? ob->pose : nullptr;
    bool changed = false;

    /* Sanity checks. */
    if (ELEM(nullptr, ob, pose, arm)) {
      continue;
    }

    /* iterate over elements in the Keying Set, setting selection depending on whether
     * that bone is visible or not...
     */
    LISTBASE_FOREACH (KS_Path *, ksp, &ks->paths) {
      /* only items related to this object will be relevant */
      if ((ksp->id == &ob->id) && (ksp->rna_path != nullptr)) {
        bPoseChannel *pchan = nullptr;
        char boneName[sizeof(pchan->name)];
        if (!BLI_str_quoted_substr(ksp->rna_path, "bones[", boneName, sizeof(boneName))) {
          continue;
        }
        pchan = BKE_pose_channel_find_name(pose, boneName);

        if (pchan) {
          /* select if bone is visible and can be affected */
          if (PBONE_SELECTABLE(arm, pchan->bone)) {
            pchan->bone->flag |= BONE_SELECTED;
            changed = true;
          }
        }
      }
    }

    if (changed || !extend) {
      ED_pose_bone_select_tag_update(ob);
      changed_multi = true;
    }
  }
  MEM_freeN(objects);

  return changed_multi;
}

static int pose_select_grouped_exec(bContext *C, wmOperator *op)
{
  Object *ob = BKE_object_pose_armature_get(CTX_data_active_object(C));
  const ePose_SelectSame_Mode type = ePose_SelectSame_Mode(RNA_enum_get(op->ptr, "type"));
  const bool extend = RNA_boolean_get(op->ptr, "extend");
  bool changed = false;

  /* sanity check */
  if (ob->pose == nullptr) {
    return OPERATOR_CANCELLED;
  }

  /* selection types */
  switch (type) {
    case POSE_SEL_SAME_COLLECTION:
      changed = pose_select_same_collection(C, extend);
      break;

    case POSE_SEL_SAME_COLOR:
      changed = pose_select_same_color(C, extend);
      break;

    case POSE_SEL_SAME_KEYINGSET: /* Keying Set */
      changed = pose_select_same_keyingset(C, op->reports, extend);
      break;

    default:
      printf("pose_select_grouped() - Unknown selection type %d\n", type);
      break;
  }

  /* report done status */
  if (changed) {
    ED_outliner_select_sync_from_pose_bone_tag(C);

    return OPERATOR_FINISHED;
  }
  return OPERATOR_CANCELLED;
}

void POSE_OT_select_grouped(wmOperatorType *ot)
{
  static const EnumPropertyItem prop_select_grouped_types[] = {
      {POSE_SEL_SAME_COLLECTION,
       "COLLECTION",
       0,
       "Collection",
       "Same collections as the active bone"},
      {POSE_SEL_SAME_COLOR, "COLOR", 0, "Color", "Same color as the active bone"},
      {POSE_SEL_SAME_KEYINGSET,
       "KEYINGSET",
       0,
       "Keying Set",
       "All bones affected by active Keying Set"},
      {0, nullptr, 0, nullptr, nullptr},
  };

  /* identifiers */
  ot->name = "Select Grouped";
  ot->description = "Select all visible bones grouped by similar properties";
  ot->idname = "POSE_OT_select_grouped";

  /* api callbacks */
  ot->invoke = WM_menu_invoke;
  ot->exec = pose_select_grouped_exec;
  ot->poll = ED_operator_posemode; /* TODO: expand to support edit mode as well. */

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* properties */
  RNA_def_boolean(ot->srna,
                  "extend",
                  false,
                  "Extend",
                  "Extend selection instead of deselecting everything first");
  ot->prop = RNA_def_enum(ot->srna, "type", prop_select_grouped_types, 0, "Type", "");
}

/* -------------------------------------- */

/**
 * \note clone of #armature_select_mirror_exec keep in sync
 */
static int pose_select_mirror_exec(bContext *C, wmOperator *op)
{
  const Scene *scene = CTX_data_scene(C);
  ViewLayer *view_layer = CTX_data_view_layer(C);
  Object *ob_active = CTX_data_active_object(C);

  const bool is_weight_paint = (ob_active->mode & OB_MODE_WEIGHT_PAINT) != 0;
  const bool active_only = RNA_boolean_get(op->ptr, "only_active");
  const bool extend = RNA_boolean_get(op->ptr, "extend");

  uint objects_len = 0;
  Object **objects = BKE_object_pose_array_get_unique(
      scene, view_layer, CTX_wm_view3d(C), &objects_len);

  for (uint ob_index = 0; ob_index < objects_len; ob_index++) {
    Object *ob = objects[ob_index];
    bArmature *arm = static_cast<bArmature *>(ob->data);
    bPoseChannel *pchan_mirror_act = nullptr;

    LISTBASE_FOREACH (bPoseChannel *, pchan, &ob->pose->chanbase) {
      const int flag = (pchan->bone->flag & BONE_SELECTED);
      PBONE_PREV_FLAG_SET(pchan, flag);
    }

    LISTBASE_FOREACH (bPoseChannel *, pchan, &ob->pose->chanbase) {
      if (PBONE_SELECTABLE(arm, pchan->bone)) {
        bPoseChannel *pchan_mirror;
        int flag_new = extend ? PBONE_PREV_FLAG_GET(pchan) : 0;

        if ((pchan_mirror = BKE_pose_channel_get_mirrored(ob->pose, pchan->name)) &&
            PBONE_VISIBLE(arm, pchan_mirror->bone))
        {
          const int flag_mirror = PBONE_PREV_FLAG_GET(pchan_mirror);
          flag_new |= flag_mirror;

          if (pchan->bone == arm->act_bone) {
            pchan_mirror_act = pchan_mirror;
          }

          /* Skip all but the active or its mirror. */
          if (active_only && !ELEM(arm->act_bone, pchan->bone, pchan_mirror->bone)) {
            continue;
          }
        }

        pchan->bone->flag = (pchan->bone->flag & ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL)) |
                            flag_new;
      }
    }

    if (pchan_mirror_act) {
      arm->act_bone = pchan_mirror_act->bone;

      /* In weight-paint we select the associated vertex group too. */
      if (is_weight_paint) {
        ED_vgroup_select_by_name(ob_active, pchan_mirror_act->name);
        DEG_id_tag_update(&ob_active->id, ID_RECALC_GEOMETRY);
      }
    }

    WM_event_add_notifier(C, NC_OBJECT | ND_BONE_SELECT, ob);

    /* Need to tag armature for cow updates, or else selection doesn't update. */
    DEG_id_tag_update(&arm->id, ID_RECALC_COPY_ON_WRITE);
  }
  MEM_freeN(objects);

  ED_outliner_select_sync_from_pose_bone_tag(C);

  return OPERATOR_FINISHED;
}

void POSE_OT_select_mirror(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Select Mirror";
  ot->idname = "POSE_OT_select_mirror";
  ot->description = "Mirror the bone selection";

  /* api callbacks */
  ot->exec = pose_select_mirror_exec;
  ot->poll = ED_operator_posemode;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* properties */
  RNA_def_boolean(
      ot->srna, "only_active", false, "Active Only", "Only operate on the active bone");
  RNA_def_boolean(ot->srna, "extend", false, "Extend", "Extend the selection");
}
