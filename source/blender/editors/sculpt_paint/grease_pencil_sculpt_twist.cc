/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_math_rotation.h"

#include "DNA_gpencil_legacy_types.h"

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

class TwistOperation : public GreasePencilStrokeOperationCommon {
 public:
  using GreasePencilStrokeOperationCommon::GreasePencilStrokeOperationCommon;

  void on_stroke_begin(const bContext &C, const InputSample &start_sample) override;
  void on_stroke_extended(const bContext &C, const InputSample &extension_sample) override;
  void on_stroke_done(const bContext & /*C*/) override {}
};

static float2 rotate_by_angle(const float2 &vec, const float angle)
{
  const float cos_angle = math::cos(angle);
  const float sin_angle = math::sin(angle);
  return float2(vec.x * cos_angle - vec.y * sin_angle, vec.x * sin_angle + vec.y * cos_angle);
}

void TwistOperation::on_stroke_begin(const bContext &C, const InputSample &start_sample)
{
  this->init_stroke(C, start_sample);
}

void TwistOperation::on_stroke_extended(const bContext &C, const InputSample &extension_sample)
{
  const Scene &scene = *CTX_data_scene(&C);
  Paint &paint = *BKE_paint_get_active_from_context(&C);
  const Brush &brush = *BKE_paint_brush(&paint);
  const bool invert = this->is_inverted(brush);

  const bool is_masking = GPENCIL_ANY_SCULPT_MASK(
      eGP_Sculpt_SelectMaskFlag(scene.toolsettings->gpencil_selectmode_sculpt));

  this->foreach_editable_drawing(
      C, [&](const GreasePencilStrokeParams &params, const DeltaProjectionFunc &projection_fn) {
        IndexMaskMemory selection_memory;
        const IndexMask selection = point_selection_mask(params, is_masking, selection_memory);
        if (selection.is_empty()) {
          return false;
        }

        bke::crazyspace::GeometryDeformation deformation = get_drawing_deformation(params);
        Array<float2> view_positions = calculate_view_positions(params, selection);
        bke::CurvesGeometry &curves = params.drawing.strokes_for_write();
        MutableSpan<float3> positions = curves.positions_for_write();

        const float2 mouse_pos = extension_sample.mouse_position;

        selection.foreach_index(GrainSize(4096), [&](const int64_t point_i) {
          const float2 &co = view_positions[point_i];
          const float influence = brush_point_influence(
              scene, brush, co, extension_sample, params.multi_frame_falloff);
          if (influence <= 0.0f) {
            return;
          }

          const float angle = DEG2RADF(invert ? -1.0f : 1.0f) * influence;
          const float2 radial_offset = co - mouse_pos;
          positions[point_i] += compute_orig_delta(projection_fn,
                                                   deformation,
                                                   point_i,
                                                   rotate_by_angle(radial_offset, angle) -
                                                       radial_offset);
        });

        params.drawing.tag_positions_changed();
        return true;
      });
  this->stroke_extended(extension_sample);
}

std::unique_ptr<GreasePencilStrokeOperation> new_twist_operation(const BrushStrokeMode stroke_mode)
{
  return std::make_unique<TwistOperation>(stroke_mode);
}

}  // namespace blender::ed::sculpt_paint::greasepencil
