/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "BKE_mesh_types.hh"

/** \file
 * \ingroup bke
 */

namespace blender::bke::compare_meshes {

enum class MeshMismatch : int8_t;

/**
 * Convert the mismatch to a human-readable string for display.
 */
const char *mismatch_to_string(const MeshMismatch &mismatch);

/**
 * \brief Checks if the two meshes are different, returning the type of mismatch if any. Changes in
 * index order are detected, but treated as a mismatch.
 *
 * \details Instead of just blindly comparing the two meshes, the code tries to determine if they
 * are isomorphic. Two meshes are considered isomorphic, if, for each domain, there is a bijection
 * between the two meshes such that the bijections preserve connectivity.
 *
 * In general, determining if two graphs are isomorphic is a very difficult problem (no polynomial
 * time algorithm is known). Because we have more information than just connectivity (attributes),
 * we can compute it in a more reasonable time in most cases.
 *
 * \returns The type of mismatch that was detected, if there is any.
 */
std::optional<MeshMismatch> compare_meshes(const Mesh &mesh1, const Mesh &mesh2, float threshold);

}  // namespace blender::bke::compare_meshes
