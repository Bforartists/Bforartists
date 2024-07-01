/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup animrig
 *
 * \brief Internal C++ functions to deal with Actions, Bindings, and their runtime data.
 */

#pragma once

#include "BLI_vector.hh"

struct ID;

namespace blender::animrig {

/**
 * Not placed in the 'internal' namespace, as this type is forward-declared in
 * DNA_action_types.h, and that shouldn't reference the internal namespace.
 */
class BindingRuntime {
 public:
  /**
   * Cache of pointers to the IDs that are animated by this binding.
   *
   * Note that this is a vector for simplicity, as the majority of the bindings
   * will have zero or one user. Semantically it's treated as a set: order
   * doesn't matter, and it has no duplicate entries.
   *
   * \note This is NOT thread-safe.
   */
  Vector<ID *> users;
};

namespace internal {

/**
 * Rebuild the BindingRuntime::users cache of all Bindings in all Actions.
 *
 * The reason that all binding users are re-cached at once is two-fold:
 *
 * 1. Regardless of how many binding caches are rebuilt, this function will need
 *    to loop over all IDs anyway.
 * 2. Deletion of IDs may be hard to detect otherwise. This is a bit of a weak
 *    argument, as if this is not implemented properly (i.e. not un-assigning
 *    the Action first), the 'dirty' flag will also not be set, and thus a
 *    rebuild will not be triggered. In any case, because the rebuild is global,
 *    any subsequent call at least ensures correctness even with such bugs.
 */
void rebuild_binding_user_cache(Main &bmain);

}  // namespace internal

}  // namespace blender::animrig
