/* SPDX-License-Identifier: GPL-2.0-or-later */

#include <algorithm>

#include "curves_sculpt_intern.hh"

#include "BLI_float4x4.hh"
#include "BLI_index_mask_ops.hh"
#include "BLI_kdtree.h"
#include "BLI_rand.hh"
#include "BLI_vector.hh"

#include "PIL_time.h"

#include "DEG_depsgraph.h"

#include "BKE_attribute_math.hh"
#include "BKE_brush.h"
#include "BKE_bvhutils.h"
#include "BKE_context.h"
#include "BKE_curves.hh"
#include "BKE_mesh.h"
#include "BKE_mesh_runtime.h"
#include "BKE_paint.h"

#include "DNA_brush_enums.h"
#include "DNA_brush_types.h"
#include "DNA_curves_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"

#include "ED_screen.h"
#include "ED_view3d.h"

/**
 * The code below uses a suffix naming convention to indicate the coordinate space:
 * cu: Local space of the curves object that is being edited.
 * wo: World space.
 * re: 2D coordinates within the region.
 */

namespace blender::ed::sculpt_paint {

using blender::bke::CurvesGeometry;

class DeleteOperation : public CurvesSculptStrokeOperation {
 private:
  float2 brush_pos_prev_re_;

  CurvesBrush3D brush_3d_;

  friend struct DeleteOperationExecutor;

 public:
  void on_stroke_extended(bContext *C, const StrokeExtension &stroke_extension) override;
};

struct DeleteOperationExecutor {
  DeleteOperation *self_ = nullptr;
  bContext *C_ = nullptr;
  Depsgraph *depsgraph_ = nullptr;
  Scene *scene_ = nullptr;
  Object *object_ = nullptr;
  ARegion *region_ = nullptr;
  View3D *v3d_ = nullptr;
  RegionView3D *rv3d_ = nullptr;

  Curves *curves_id_ = nullptr;
  CurvesGeometry *curves_ = nullptr;

  CurvesSculpt *curves_sculpt_ = nullptr;
  Brush *brush_ = nullptr;
  float brush_radius_re_;

  float2 brush_pos_re_;
  float2 brush_pos_prev_re_;

  float4x4 curves_to_world_mat_;
  float4x4 world_to_curves_mat_;

  void execute(DeleteOperation &self, bContext *C, const StrokeExtension &stroke_extension)
  {
    BLI_SCOPED_DEFER([&]() { self.brush_pos_prev_re_ = stroke_extension.mouse_position; });

    self_ = &self;
    C_ = C;
    depsgraph_ = CTX_data_depsgraph_pointer(C);
    scene_ = CTX_data_scene(C);
    object_ = CTX_data_active_object(C);
    region_ = CTX_wm_region(C);
    v3d_ = CTX_wm_view3d(C);
    rv3d_ = CTX_wm_region_view3d(C);

    curves_id_ = static_cast<Curves *>(object_->data);
    curves_ = &CurvesGeometry::wrap(curves_id_->geometry);

    curves_sculpt_ = scene_->toolsettings->curves_sculpt;
    brush_ = BKE_paint_brush(&curves_sculpt_->paint);
    brush_radius_re_ = BKE_brush_size_get(scene_, brush_);

    brush_pos_re_ = stroke_extension.mouse_position;
    brush_pos_prev_re_ = stroke_extension.is_first ? stroke_extension.mouse_position :
                                                     self.brush_pos_prev_re_;

    curves_to_world_mat_ = object_->obmat;
    world_to_curves_mat_ = curves_to_world_mat_.inverted();

    const eBrushFalloffShape falloff_shape = static_cast<eBrushFalloffShape>(
        brush_->falloff_shape);

    if (stroke_extension.is_first) {
      if (falloff_shape == PAINT_FALLOFF_SHAPE_SPHERE) {
        this->initialize_spherical_brush_reference_point();
      }
    }

    if (falloff_shape == PAINT_FALLOFF_SHAPE_TUBE) {
      this->delete_projected();
    }
    else if (falloff_shape == PAINT_FALLOFF_SHAPE_SPHERE) {
      this->delete_spherical();
    }
    else {
      BLI_assert_unreachable();
    }

    DEG_id_tag_update(&curves_id_->id, ID_RECALC_GEOMETRY);
    ED_region_tag_redraw(region_);
  }

  void delete_projected()
  {
    float4x4 projection;
    ED_view3d_ob_project_mat_get(rv3d_, object_, projection.values);

    Span<float3> positions_cu = curves_->positions();

    /* Find indices of curves that have to be removed. */
    Vector<int64_t> indices;
    const IndexMask curves_to_remove = index_mask_ops::find_indices_based_on_predicate(
        curves_->curves_range(), 512, indices, [&](const int curve_i) {
          const IndexRange point_range = curves_->points_for_curve(curve_i);
          for (const int segment_i : IndexRange(point_range.size() - 1)) {
            const float3 pos1_cu = positions_cu[point_range[segment_i]];
            const float3 pos2_cu = positions_cu[point_range[segment_i + 1]];

            float2 pos1_re, pos2_re;
            ED_view3d_project_float_v2_m4(region_, pos1_cu, pos1_re, projection.values);
            ED_view3d_project_float_v2_m4(region_, pos2_cu, pos2_re, projection.values);

            const float dist = dist_seg_seg_v2(
                pos1_re, pos2_re, brush_pos_prev_re_, brush_pos_re_);
            if (dist <= brush_radius_re_) {
              return true;
            }
          }
          return false;
        });

    curves_->remove_curves(curves_to_remove);
  }

  void delete_spherical()
  {
    Span<float3> positions_cu = curves_->positions();

    float4x4 projection;
    ED_view3d_ob_project_mat_get(rv3d_, object_, projection.values);

    float3 brush_start_wo, brush_end_wo;
    ED_view3d_win_to_3d(v3d_,
                        region_,
                        curves_to_world_mat_ * self_->brush_3d_.position_cu,
                        brush_pos_prev_re_,
                        brush_start_wo);
    ED_view3d_win_to_3d(v3d_,
                        region_,
                        curves_to_world_mat_ * self_->brush_3d_.position_cu,
                        brush_pos_re_,
                        brush_end_wo);
    const float3 brush_start_cu = world_to_curves_mat_ * brush_start_wo;
    const float3 brush_end_cu = world_to_curves_mat_ * brush_end_wo;

    const float brush_radius_cu = self_->brush_3d_.radius_cu;
    const float brush_radius_sq_cu = pow2f(brush_radius_cu);

    Vector<int64_t> indices;
    const IndexMask curves_to_remove = index_mask_ops::find_indices_based_on_predicate(
        curves_->curves_range(), 512, indices, [&](const int curve_i) {
          const IndexRange points = curves_->points_for_curve(curve_i);
          for (const int segment_i : IndexRange(points.size() - 1)) {
            const float3 pos1_cu = positions_cu[points[segment_i]];
            const float3 pos2_cu = positions_cu[points[segment_i] + 1];

            float3 closest_segment_cu, closest_brush_cu;
            isect_seg_seg_v3(pos1_cu,
                             pos2_cu,
                             brush_start_cu,
                             brush_end_cu,
                             closest_segment_cu,
                             closest_brush_cu);
            const float distance_to_brush_sq_cu = math::distance_squared(closest_segment_cu,
                                                                         closest_brush_cu);
            if (distance_to_brush_sq_cu > brush_radius_sq_cu) {
              continue;
            }
            return true;
          }
          return false;
        });

    curves_->remove_curves(curves_to_remove);
  }

  void initialize_spherical_brush_reference_point()
  {
    std::optional<CurvesBrush3D> brush_3d = sample_curves_3d_brush(
        *C_, *object_, brush_pos_re_, brush_radius_re_);
    if (brush_3d.has_value()) {
      self_->brush_3d_ = *brush_3d;
    }
  }
};

void DeleteOperation::on_stroke_extended(bContext *C, const StrokeExtension &stroke_extension)
{
  DeleteOperationExecutor executor;
  executor.execute(*this, C, stroke_extension);
}

std::unique_ptr<CurvesSculptStrokeOperation> new_delete_operation()
{
  return std::make_unique<DeleteOperation>();
}

}  // namespace blender::ed::sculpt_paint
