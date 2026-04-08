/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup bke
 */

#include <xxhash.h>

namespace blender {

struct IDProperty;

namespace bke::idprop {

/**
 * Hash the value of the given IDProperty recursively. This only hashes the actual values, not e.g.
 * the ui data.
 */
void hash(const IDProperty &base_prop, XXH3_state_t *hash_state);

}  // namespace bke::idprop
}  // namespace blender
