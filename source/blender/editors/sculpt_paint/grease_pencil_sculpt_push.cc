/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_context.hh"
#include "BKE_crazyspace.hh"
#include "BKE_curves.hh"
#include "BKE_grease_pencil.hh"
#include "BKE_paint.hh"

#include "ED_grease_pencil.hh"
#include "ED_view3d.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "grease_pencil_intern.hh"
#include "paint_intern.hh"

namespace blender::ed::sculpt_paint::greasepencil {

class PushOperation : public GreasePencilStrokeOperationCommon {
 public:
  using GreasePencilStrokeOperationCommon::GreasePencilStrokeOperationCommon;

  void on_stroke_begin(const bContext &C, const InputSample &start_sample) override;
  void on_stroke_extended(const bContext &C, const InputSample &extension_sample) override;
  void on_stroke_done(const bContext & /*C*/) override {}
};

void PushOperation::on_stroke_begin(const bContext &C, const InputSample &start_sample)
{
  this->init_stroke(C, start_sample);
  this->init_auto_masking(C, start_sample);
}

void PushOperation::on_stroke_extended(const bContext &C, const InputSample &extension_sample)
{
  Paint &paint = *BKE_paint_get_active_from_context(&C);
  const Brush &brush = *BKE_paint_brush(&paint);

  this->foreach_editable_drawing_with_automask(
      C,
      [&](const GreasePencilStrokeParams &params,
          const IndexMask &point_mask,
          const DeltaProjectionFunc &projection_fn) {
        bke::crazyspace::GeometryDeformation deformation = get_drawing_deformation(params);
        Array<float2> view_positions = calculate_view_positions(params, point_mask);
        bke::CurvesGeometry &curves = params.drawing.strokes_for_write();
        MutableSpan<float3> positions = curves.positions_for_write();

        const float2 mouse_delta = this->mouse_delta(extension_sample);

        point_mask.foreach_index(GrainSize(4096), [&](const int64_t point_i) {
          const float2 &co = view_positions[point_i];
          const float influence = brush_point_influence(
              paint, brush, co, extension_sample, params.multi_frame_falloff);
          if (influence <= 0.0f) {
            return;
          }

          positions[point_i] += compute_orig_delta(
              projection_fn, deformation, point_i, mouse_delta * influence);
        });

        params.drawing.tag_positions_changed();
        return true;
      });
  this->stroke_extended(extension_sample);
}

std::unique_ptr<GreasePencilStrokeOperation> new_push_operation(const BrushStrokeMode stroke_mode)
{
  return std::make_unique<PushOperation>(stroke_mode);
}

}  // namespace blender::ed::sculpt_paint::greasepencil
