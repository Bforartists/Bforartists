/* SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include <optional>

#include "curves_sculpt_intern.h"

#include "BLI_math_vector.hh"

#include "BKE_curves.hh"

struct ARegion;
struct RegionView3D;
struct Object;

namespace blender::ed::sculpt_paint {

using bke::CurvesGeometry;

struct StrokeExtension {
  bool is_first;
  float2 mouse_position;
};

/**
 * Base class for stroke based operations in curves sculpt mode.
 */
class CurvesSculptStrokeOperation {
 public:
  virtual ~CurvesSculptStrokeOperation() = default;
  virtual void on_stroke_extended(bContext *C, const StrokeExtension &stroke_extension) = 0;
};

std::unique_ptr<CurvesSculptStrokeOperation> new_add_operation();
std::unique_ptr<CurvesSculptStrokeOperation> new_comb_operation();
std::unique_ptr<CurvesSculptStrokeOperation> new_delete_operation();
std::unique_ptr<CurvesSculptStrokeOperation> new_snake_hook_operation();

struct CurvesBrush3D {
  float3 position_cu;
  float radius_cu;
};

/**
 * Find 3d brush position based on cursor position for curves sculpting.
 */
std::optional<CurvesBrush3D> sample_curves_3d_brush(bContext &C,
                                                    Object &curves_object,
                                                    const float2 &brush_pos_re,
                                                    float brush_radius_re);

}  // namespace blender::ed::sculpt_paint
