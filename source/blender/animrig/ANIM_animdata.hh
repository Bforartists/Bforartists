/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup animrig
 *
 * \brief Functions to work with AnimData.
 */

#pragma once

#include "BLI_string_ref.hh"
#include "BLI_vector.hh"

struct ID;
struct Main;

struct AnimData;
struct FCurve;
struct bAction;

namespace blender::animrig {

class Action;

/**
 * Get (or add relevant data to be able to do so) the Active Action for the given
 * Animation Data block, given an ID block where the Animation Data should reside.
 */
bAction *id_action_ensure(Main *bmain, ID *id);

/**
 * Delete the F-Curve from the given AnimData block (if possible),
 * as appropriate according to animation context.
 */
void animdata_fcurve_delete(AnimData *adt, FCurve *fcu);

/**
 * Unlink the action from animdata if it's empty.
 *
 * If the action has no F-Curves, unlink it from AnimData if it did not
 * come from a NLA Strip being tweaked.
 */
bool animdata_remove_empty_action(AnimData *adt);

/**
 * Build a Vector of IDs that are related to the given ID. Related things are e.g. Object<->Data,
 * Mesh<->Material and so on. The exact relationships are defined per ID type. Only relationships
 * of 1:1 are traced. The case of multiple users for 1 ID is treated as not related.
 * The returned Vector always contains the passed ID as the first index as such will never be
 * empty.
 */
Vector<ID *> find_related_ids(Main &bmain, ID &id);

/**
 * Compatibility helper function for `BKE_animadata_fcurve_find_by_rna_path()`.
 *
 * Searches each layer (top to bottom) to find an FCurve that matches the given
 * RNA path & index.
 *
 * \see BKE_animadata_fcurve_find_by_rna_path
 *
 * \note The returned FCurve should NOT be used for keyframe manipulation. Its
 * existence is an indicator for "this property is animated".
 *
 * \note This function assumes that `adt->action` actually points to a layered
 * Action. It is a bug to call this with a legacy Action, or without one.
 *
 * This function should probably be limited to the active layer (for the given
 * property, once pinning to layers is there), so that the "this is keyed" color
 * is more accurate.
 *
 * Again, this is just to hook up the layered Action to the old Blender UI code.
 */
const FCurve *fcurve_find_by_rna_path(const AnimData &adt,
                                      StringRefNull rna_path,
                                      int array_index);

}  // namespace blender::animrig
