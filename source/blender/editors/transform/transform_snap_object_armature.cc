/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edtransform
 */

#include "BLI_math_matrix.hh"

#include "BKE_armature.h"
#include "BKE_bvhutils.h"
#include "BKE_mesh.hh"
#include "DNA_armature_types.h"

#include "ED_transform_snap_object_context.hh"

#include "ANIM_bone_collections.h"

#include "transform_snap_object.hh"

using blender::float4x4;

eSnapMode snapArmature(SnapObjectContext *sctx,
                       Object *ob_eval,
                       const float4x4 &obmat,
                       bool is_object_active)
{
  eSnapMode retval = SCE_SNAP_TO_NONE;

  if (sctx->runtime.snap_to_flag == SCE_SNAP_TO_FACE) {
    /* Currently only edge and vert. */
    return retval;
  }

  bArmature *arm = static_cast<bArmature *>(ob_eval->data);

  SnapData nearest2d(sctx, obmat);

  const bool is_editmode = arm->edbo != nullptr;

  if (is_editmode == false) {
    const BoundBox *bb = BKE_armature_boundbox_get(ob_eval);
    if (bb && !nearest2d.snap_boundbox(bb->vec[0], bb->vec[6])) {
      return retval;
    }
  }

  nearest2d.clip_planes_enable(sctx, ob_eval);

  const float *head_vec = nullptr, *tail_vec = nullptr;

  const bool is_posemode = is_object_active && (ob_eval->mode & OB_MODE_POSE);
  const bool skip_selected = (is_editmode || is_posemode) &&
                             (sctx->runtime.params.snap_target_select &
                              SCE_SNAP_TARGET_NOT_SELECTED);

  if (arm->edbo) {
    LISTBASE_FOREACH (EditBone *, eBone, arm->edbo) {
      if (ANIM_bonecoll_is_visible_editbone(arm, eBone)) {
        if (eBone->flag & BONE_HIDDEN_A) {
          /* Skip hidden bones. */
          continue;
        }

        const bool is_selected = (eBone->flag & (BONE_ROOTSEL | BONE_TIPSEL)) != 0;
        if (is_selected && skip_selected) {
          continue;
        }

        if (nearest2d.snap_edge(eBone->head, eBone->tail)) {
          head_vec = eBone->head;
          tail_vec = eBone->tail;
        }
      }
    }
  }
  else if (ob_eval->pose && ob_eval->pose->chanbase.first) {
    LISTBASE_FOREACH (bPoseChannel *, pchan, &ob_eval->pose->chanbase) {
      Bone *bone = pchan->bone;
      if (!bone || (bone->flag & (BONE_HIDDEN_P | BONE_HIDDEN_PG))) {
        /* Skip hidden bones. */
        continue;
      }

      const bool is_selected = (bone->flag & (BONE_SELECTED | BONE_ROOTSEL | BONE_TIPSEL)) != 0;
      if (is_selected && skip_selected) {
        continue;
      }

      if (nearest2d.snap_edge(pchan->pose_head, pchan->pose_tail)) {
        head_vec = pchan->pose_head;
        tail_vec = pchan->pose_tail;
      }
    }
  }

  if (nearest2d.nearest_point.index != -2) {
    retval = sctx->runtime.snap_to_flag & SCE_SNAP_TO_EDGE;
    if (retval == SCE_SNAP_TO_NONE) {
      nearest2d.nearest_point.index = -2;
    }

    if (sctx->runtime.snap_to_flag & SCE_SNAP_TO_EDGE_ENDPOINT) {
      float dist_px_sq_edge = nearest2d.nearest_point.dist_sq;
      nearest2d.nearest_point.dist_sq = sctx->ret.dist_px_sq;
      if (nearest2d.snap_point(head_vec) || nearest2d.snap_point(tail_vec)) {
        retval = SCE_SNAP_TO_EDGE_ENDPOINT;
      }
      else if (retval) {
        nearest2d.nearest_point.dist_sq = dist_px_sq_edge;
      }
    }
  }

  if (retval) {
    nearest2d.register_result(sctx, ob_eval, &arm->id);
  }
  return retval;
}
