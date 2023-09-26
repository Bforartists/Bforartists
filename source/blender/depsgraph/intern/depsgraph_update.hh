/* SPDX-FileCopyrightText: 2013 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup depsgraph
 */

#pragma once

struct DEGEditorUpdateContext;
struct ID;

namespace blender::deg {

void deg_editors_id_update(const DEGEditorUpdateContext *update_ctx, ID *id);

void deg_editors_scene_update(const DEGEditorUpdateContext *update_ctx, bool updated);

}  // namespace blender::deg
