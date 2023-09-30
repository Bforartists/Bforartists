/* SPDX-FileCopyrightText: 2020 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edgeometry
 */

#include "WM_api.hh"

#include "ED_geometry.hh"

#include "geometry_intern.hh"

/**************************** registration **********************************/

void ED_operatortypes_geometry()
{
  using namespace blender::ed::geometry;

  WM_operatortype_append(GEOMETRY_OT_attribute_add);
  WM_operatortype_append(GEOMETRY_OT_attribute_remove);
  WM_operatortype_append(GEOMETRY_OT_color_attribute_add);
  WM_operatortype_append(GEOMETRY_OT_color_attribute_remove);
  WM_operatortype_append(GEOMETRY_OT_color_attribute_render_set);
  WM_operatortype_append(GEOMETRY_OT_color_attribute_duplicate);
  WM_operatortype_append(GEOMETRY_OT_attribute_convert);
  WM_operatortype_append(GEOMETRY_OT_color_attribute_convert);
  WM_operatortype_append(GEOMETRY_OT_execute_node_group);
  WM_operatortype_append(GEOMETRY_OT_geometry_randomization);
}
