/* SPDX-License-Identifier: Apache-2.0 */

#pragma once

#include "IO_wavefront_obj.h"

namespace blender::io::obj {

struct OBJExportParamsDefault {
  OBJExportParams params;
  OBJExportParamsDefault()
  {
    params.filepath[0] = '\0';
    params.blen_filepath = "";
    params.export_animation = false;
    params.start_frame = 0;
    params.end_frame = 1;

    params.forward_axis = OBJ_AXIS_NEGATIVE_Z_FORWARD;
    params.up_axis = OBJ_AXIS_Y_UP;
    params.scaling_factor = 1.f;

    params.apply_modifiers = true;
    params.export_eval_mode = DAG_EVAL_VIEWPORT;
    params.export_selected_objects = false;
    params.export_uv = true;
    params.export_normals = true;
    params.export_materials = true;
    params.export_triangulated_mesh = false;
    params.export_curves_as_nurbs = false;

    params.export_object_groups = false;
    params.export_material_groups = false;
    params.export_vertex_groups = false;
    params.export_smooth_groups = true;
    params.smooth_groups_bitflags = false;
  }
};

}  // namespace blender::io::obj
