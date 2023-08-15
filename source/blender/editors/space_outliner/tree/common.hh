/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spoutliner
 */

#pragma once

struct AnimData;
struct ListBase;

namespace blender::ed::outliner {

const char *outliner_idcode_to_plural(short idcode);

void outliner_make_object_parent_hierarchy(ListBase *lb);
bool outliner_animdata_test(const AnimData *adt);

}  // namespace blender::ed::outliner
