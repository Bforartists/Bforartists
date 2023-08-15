/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edgreasepencil
 */

#include "ED_grease_pencil.hh"

void ED_operatortypes_grease_pencil()
{
  ED_operatortypes_grease_pencil_draw();
  ED_operatortypes_grease_pencil_frames();
  ED_operatortypes_grease_pencil_layers();
  ED_operatortypes_grease_pencil_select();
  ED_operatortypes_grease_pencil_edit();
}
