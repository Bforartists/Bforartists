/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_main.h"
#include "DNA_scene_types.h"
#include "RNA_access.hh"
#include "RNA_types.hh"

#include "IO_orientation.hh"

const EnumPropertyItem io_transform_axis[] = {
    {IO_AXIS_X, "X", 0, "X", "Positive X axis"},
    {IO_AXIS_Y, "Y", 0, "Y", "Positive Y axis"},
    {IO_AXIS_Z, "Z", 0, "Z", "Positive Z axis"},
    {IO_AXIS_NEGATIVE_X, "NEGATIVE_X", 0, "-X", "Negative X axis"},
    {IO_AXIS_NEGATIVE_Y, "NEGATIVE_Y", 0, "-Y", "Negative Y axis"},
    {IO_AXIS_NEGATIVE_Z, "NEGATIVE_Z", 0, "-Z", "Negative Z axis"},
    {0, nullptr, 0, nullptr, nullptr}};

void io_ui_forward_axis_update(Main * /*main*/, Scene * /*scene*/, PointerRNA *ptr)
{
  /* Both forward and up axes cannot be along the same direction. */

  int forward = RNA_enum_get(ptr, "forward_axis");
  int up = RNA_enum_get(ptr, "up_axis");
  if ((forward % 3) == (up % 3)) {
    RNA_enum_set(ptr, "up_axis", (up + 1) % 6);
  }
}

void io_ui_up_axis_update(Main * /*main*/, Scene * /*scene*/, PointerRNA *ptr)
{
  int forward = RNA_enum_get(ptr, "forward_axis");
  int up = RNA_enum_get(ptr, "up_axis");
  if ((forward % 3) == (up % 3)) {
    RNA_enum_set(ptr, "forward_axis", (forward + 1) % 6);
  }
}
