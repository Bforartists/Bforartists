/* SPDX-FileCopyrightText: 2024 Blender Authors. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup animrig
 */

#include "ANIM_action.hh"

namespace blender {

struct ID;
struct NlaStrip;

namespace animrig::nla {

/**
 * Assign the Action to this NLA strip.
 *
 * Similar to animrig::assign_action(), this tries to find a suitable slot.
 *
 * \see animrig::assign_action
 *
 * \returns whether the assignment was ok.
 */
bool assign_action(NlaStrip &strip, Action &action, ID &animated_id);

void unassign_action(NlaStrip &strip, ID &animated_id);

/**
 * Assign a slot to the NLA strip.
 *
 * The strip should already have an Action assigned to it, and the given Slot should belong to that
 * Action.
 *
 * \param slot_to_assign: the slot to assign, or nullptr to un-assign the current slot.
 */
ActionSlotAssignmentResult assign_action_slot(NlaStrip &strip,
                                              Slot *slot_to_assign,
                                              ID &animated_id);

ActionSlotAssignmentResult assign_action_slot_handle(NlaStrip &strip,
                                                     slot_handle_t slot_handle,
                                                     ID &animated_id);

/**
 * Keyframing function taking the NLA into account.
 *
 * Inserts a key into the given FCurve with the current value of the PropertyRNA remapped through
 * the NLA stack.
 *
 * With the removal of the NLA any calls to this can be redirected to
 * animrig::insert_keyframe_direct.
 *
 * \warning This bypasses all animation layer and strip logic. Use with caution. If unsure, use
 * `insert_keyframes` instead.
 */
bool insert_keyframe_direct(ReportList *reports,
                            PointerRNA ptr,
                            PropertyRNA *prop,
                            FCurve *fcu,
                            const AnimationEvalContext *anim_eval_context,
                            eBezTriple_KeyframeType keytype,
                            NlaKeyframingContext *nla_context,
                            eInsertKeyFlags flag);
}  // namespace animrig::nla
}  // namespace blender
