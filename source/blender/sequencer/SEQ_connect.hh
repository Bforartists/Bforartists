/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup sequencer
 */

#include "BLI_vector_set.hh"

struct Strip;
struct ListBase;

namespace blender::seq {

void connections_duplicate(ListBase *connections_dst, ListBase *connections_src);

/**
 * Disconnect the strip(s) from any connections with other strips. This function also
 * frees the allocated memory as necessary. Returns false if any of the strips were not already
 * connected.
 */
bool disconnect(Strip *strip);
bool disconnect(blender::VectorSet<Strip *> &strip_list);

/**
 * Ensure that the strip has only bidirectional connections (expected behavior).
 */
void cut_one_way_connections(Strip *strip);

/**
 * Connect strips so that they may be selected together. Any connections the
 * strips already have will be severed before reconnection.
 */
void connect(Strip *seq1, Strip *seq2);
void connect(blender::VectorSet<Strip *> &strip_list);

/**
 * Returns a list of strips that the `seq` is connected to.
 * NOTE: This does not include `seq` itself.
 * This list is empty if `seq` is not connected.
 */
blender::VectorSet<Strip *> get_connected_strips(const Strip *strip);

/**
 * Check whether a strip has any connections.
 */
bool is_strip_connected(const Strip *strip);

/**
 * Check whether the list of strips are a single connection "group", that is, they are all
 * connected to each other and there are no outside connections.
 */
bool are_strips_connected_together(blender::VectorSet<Strip *> &strip_list);

}  // namespace blender::seq
