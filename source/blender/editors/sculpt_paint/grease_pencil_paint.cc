/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_brush.hh"
#include "BKE_colortools.h"
#include "BKE_context.h"
#include "BKE_curves.hh"
#include "BKE_grease_pencil.h"
#include "BKE_grease_pencil.hh"
#include "BKE_material.h"
#include "BKE_scene.h"

#include "BLI_length_parameterize.hh"
#include "BLI_math_geom.h"

#include "DEG_depsgraph_query.hh"

#include "ED_grease_pencil.hh"
#include "ED_view3d.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "grease_pencil_intern.hh"

namespace blender::ed::sculpt_paint::greasepencil {

static constexpr float POINT_OVERRIDE_THRESHOLD_PX = 3.0f;
static constexpr float POINT_RESAMPLE_MIN_DISTANCE_PX = 10.0f;

static float calc_brush_radius(ViewContext *vc,
                               const Brush *brush,
                               const Scene *scene,
                               const float3 location)
{
  if (!BKE_brush_use_locked_size(scene, brush)) {
    return paint_calc_object_space_radius(vc, location, BKE_brush_size_get(scene, brush));
  }
  return BKE_brush_unprojected_radius_get(scene, brush);
}

template<typename T>
static inline void linear_interpolation(const T &a, const T &b, MutableSpan<T> dst)
{
  dst.first() = a;
  const float step = 1.0f / dst.size();
  for (const int i : dst.index_range().drop_front(1)) {
    dst[i] = bke::attribute_math::mix2(i * step, a, b);
  }
}

static float2 arithmetic_mean(Span<float2> values)
{
  return std::accumulate(values.begin(), values.end(), float2(0)) / values.size();
}

/** Sample a bezier curve at a fixed resolution and return the sampled points in an array. */
static Array<float2> sample_curve_2d(Span<float2> positions, const int64_t resolution)
{
  BLI_assert(positions.size() % 3 == 0);
  const int64_t num_handles = positions.size() / 3;
  if (num_handles == 1) {
    return Array<float2>(resolution, positions[1]);
  }
  const int64_t num_segments = num_handles - 1;
  const int64_t num_points = num_segments * resolution;

  Array<float2> points(num_points);
  const Span<float2> curve_segments = positions.drop_front(1).drop_back(1);
  threading::parallel_for(IndexRange(num_segments), 32 * resolution, [&](const IndexRange range) {
    for (const int64_t segment_i : range) {
      IndexRange segment_range(segment_i * resolution, resolution);
      bke::curves::bezier::evaluate_segment(curve_segments[segment_i * 3 + 0],
                                            curve_segments[segment_i * 3 + 1],
                                            curve_segments[segment_i * 3 + 2],
                                            curve_segments[segment_i * 3 + 3],
                                            points.as_mutable_span().slice(segment_range));
    }
  });
  return points;
}

/** Morph \a src onto \a target such that the points have the same spacing as in \a src and
 *  write the result to \a dst. */
static void morph_points_to_curve(Span<float2> src, Span<float2> target, MutableSpan<float2> dst)
{
  BLI_assert(src.size() == dst.size());
  Array<float> accumulated_lengths_src(src.size() - 1);
  length_parameterize::accumulate_lengths<float2>(src, false, accumulated_lengths_src);

  Array<float> accumulated_lengths_target(target.size() - 1);
  length_parameterize::accumulate_lengths<float2>(target, false, accumulated_lengths_target);

  Array<int> segment_indices(accumulated_lengths_src.size());
  Array<float> segment_factors(accumulated_lengths_src.size());
  length_parameterize::sample_at_lengths(
      accumulated_lengths_target, accumulated_lengths_src, segment_indices, segment_factors);

  length_parameterize::interpolate<float2>(
      target, segment_indices, segment_factors, dst.drop_back(1));
  dst.last() = src.last();
}

class PaintOperation : public GreasePencilStrokeOperation {
 private:
  /* Screen space coordinates from input samples. */
  Vector<float2> screen_space_coords_orig_;
  /* Temporary vector of curve fitted screen space coordinates per input sample from the active
   * smoothing window. */
  Vector<Vector<float2>> screen_space_curve_fitted_coords_;
  /* Screen space coordinates after smoothing. */
  Vector<float2> screen_space_smoothed_coords_;
  /* The start index of the smoothing window. */
  int active_smooth_start_index_ = 0;

  friend struct PaintOperationExecutor;

 public:
  void on_stroke_begin(const bContext &C, const InputSample &start_sample) override;
  void on_stroke_extended(const bContext &C, const InputSample &extension_sample) override;
  void on_stroke_done(const bContext &C) override;

 private:
  void simplify_stroke(bke::greasepencil::Drawing &drawing, float epsilon_px);
  void process_stroke_end(bke::greasepencil::Drawing &drawing);
};

/**
 * Utility class that actually executes the update when the stroke is updated. That's useful
 * because it avoids passing a very large number of parameters between functions.
 */
struct PaintOperationExecutor {
  Scene *scene_;
  ARegion *region_;
  GreasePencil *grease_pencil_;

  Brush *brush_;

  BrushGpencilSettings *settings_;
  float4 vertex_color_;

  bke::greasepencil::Drawing *drawing_;

  bke::greasepencil::DrawingTransforms transforms_;

  PaintOperationExecutor(const bContext &C)
  {
    scene_ = CTX_data_scene(&C);
    region_ = CTX_wm_region(&C);
    Object *object = CTX_data_active_object(&C);
    grease_pencil_ = static_cast<GreasePencil *>(object->data);

    Paint *paint = &scene_->toolsettings->gp_paint->paint;
    brush_ = BKE_paint_brush(paint);
    settings_ = brush_->gpencil_settings;

    const bool use_vertex_color = (scene_->toolsettings->gp_paint->mode ==
                                   GPPAINT_FLAG_USE_VERTEXCOLOR);
    const bool use_vertex_color_stroke = use_vertex_color && ELEM(settings_->vertex_mode,
                                                                  GPPAINT_MODE_STROKE,
                                                                  GPPAINT_MODE_BOTH);
    vertex_color_ = use_vertex_color_stroke ? float4(brush_->rgb[0],
                                                     brush_->rgb[1],
                                                     brush_->rgb[2],
                                                     settings_->vertex_factor) :
                                              float4(0.0f);

    // const bool use_vertex_color_fill = use_vertex_color && ELEM(
    //     brush->gpencil_settings->vertex_mode, GPPAINT_MODE_STROKE, GPPAINT_MODE_BOTH);

    /* The object should have an active layer. */
    BLI_assert(grease_pencil_->has_active_layer());
    bke::greasepencil::Layer &active_layer = *grease_pencil_->get_active_layer_for_write();
    const int drawing_index = active_layer.drawing_index_at(scene_->r.cfra);

    /* Drawing should exist. */
    BLI_assert(drawing_index >= 0);
    drawing_ =
        &reinterpret_cast<GreasePencilDrawing *>(grease_pencil_->drawing(drawing_index))->wrap();

    transforms_ = bke::greasepencil::DrawingTransforms(*object);
  }

  float3 screen_space_to_drawing_plane(const float2 co)
  {
    /* TODO: Use correct plane/projection. */
    float4 plane;
    plane_from_point_normal_v3(
        plane, transforms_.layer_space_to_world_space.location(), float3{0, -1, 0});
    float3 proj_point;
    ED_view3d_win_to_3d_on_plane(region_, plane, co, false, proj_point);
    return math::transform_point(transforms_.world_space_to_layer_space, proj_point);
  }

  float radius_from_input_sample(const bContext &C, const InputSample &sample)
  {
    ViewContext vc = ED_view3d_viewcontext_init(const_cast<bContext *>(&C),
                                                CTX_data_depsgraph_pointer(&C));
    float radius = calc_brush_radius(
        &vc, brush_, scene_, screen_space_to_drawing_plane(sample.mouse_position));
    if (BKE_brush_use_size_pressure(brush_)) {
      radius *= BKE_curvemapping_evaluateF(settings_->curve_sensitivity, 0, sample.pressure);
    }
    return radius;
  }

  float opacity_from_input_sample(const InputSample &sample)
  {
    float opacity = BKE_brush_alpha_get(scene_, brush_);
    if (BKE_brush_use_alpha_pressure(brush_)) {
      opacity *= BKE_curvemapping_evaluateF(settings_->curve_strength, 0, sample.pressure);
    }
    return opacity;
  }

  void process_start_sample(PaintOperation &self,
                            const bContext &C,
                            const InputSample &start_sample,
                            const int material_index)
  {
    const float2 start_coords = start_sample.mouse_position;
    const float start_radius = this->radius_from_input_sample(C, start_sample);
    const float start_opacity = this->opacity_from_input_sample(start_sample);
    const ColorGeometry4f start_vertex_color = ColorGeometry4f(vertex_color_);

    self.screen_space_coords_orig_.append(start_coords);
    self.screen_space_curve_fitted_coords_.append(Vector<float2>({start_coords}));
    self.screen_space_smoothed_coords_.append(start_coords);

    /* Resize the curves geometry so there is one more curve with a single point. */
    bke::CurvesGeometry &curves = drawing_->strokes_for_write();
    const int num_old_points = curves.points_num();
    curves.resize(curves.points_num() + 1, curves.curves_num() + 1);
    curves.offsets_for_write().last(1) = num_old_points;

    curves.positions_for_write().last() = screen_space_to_drawing_plane(start_coords);
    drawing_->radii_for_write().last() = start_radius;
    drawing_->opacities_for_write().last() = start_opacity;
    drawing_->vertex_colors_for_write().last() = start_vertex_color;

    bke::MutableAttributeAccessor attributes = curves.attributes_for_write();
    bke::SpanAttributeWriter<int> materials = attributes.lookup_or_add_for_write_span<int>(
        "material_index", ATTR_DOMAIN_CURVE);
    bke::SpanAttributeWriter<bool> cyclic = attributes.lookup_or_add_for_write_span<bool>(
        "cyclic", ATTR_DOMAIN_CURVE);
    cyclic.span.last() = false;
    materials.span.last() = material_index;

    cyclic.finish();
    materials.finish();

    curves.curve_types_for_write().last() = CURVE_TYPE_POLY;
    curves.update_curve_types();

    /* Initialize the rest of the attributes with default values. */
    Set<std::string> attributes_to_skip{{"position",
                                         "curve_type",
                                         "material_index",
                                         "cyclic",
                                         "radius",
                                         "opacity",
                                         "vertex_color"}};
    attributes.for_all(
        [&](const bke::AttributeIDRef &id, const bke::AttributeMetaData /*meta_data*/) {
          if (attributes_to_skip.contains(id.name())) {
            return true;
          }
          bke::GSpanAttributeWriter attribute = attributes.lookup_for_write_span(id);
          const CPPType &type = attribute.span.type();
          GMutableSpan new_data = attribute.span.slice(attribute.domain == ATTR_DOMAIN_POINT ?
                                                           curves.points_range().take_back(1) :
                                                           curves.curves_range().take_back(1));
          type.fill_assign_n(type.default_value(), new_data.data(), new_data.size());
          attribute.finish();
          return true;
        });

    drawing_->tag_topology_changed();
  }

  void active_smoothing(PaintOperation &self,
                        const IndexRange smooth_window,
                        MutableSpan<float3> curve_positions)
  {
    const Span<float2> coords_to_smooth = self.screen_space_coords_orig_.as_span().slice(
        smooth_window);

    /* Detect corners in the current slice of coordinates. */
    const float corner_min_radius_px = 5.0f;
    const float corner_max_radius_px = 30.0f;
    const int64_t corner_max_samples = 64;
    const float corner_angle_threshold = 0.6f;
    IndexMaskMemory memory;
    const IndexMask corner_mask = ed::greasepencil::polyline_detect_corners(
        coords_to_smooth.drop_front(1).drop_back(1),
        corner_min_radius_px,
        corner_max_radius_px,
        corner_max_samples,
        corner_angle_threshold,
        memory);

    /* Pre-blur the coordinates for the curve fitting. This generally leads to a better fit. */
    Array<float2> coords_pre_blur(smooth_window.size());
    const int pre_blur_iterations = 3;
    ed::greasepencil::gaussian_blur_1D(coords_to_smooth,
                                       pre_blur_iterations,
                                       1.0f,
                                       true,
                                       true,
                                       false,
                                       coords_pre_blur.as_mutable_span());

    /* Curve fitting. The output will be a set of handles (float2 triplets) in a flat array. */
    const float max_error_threshold_px = 5.0f;
    Array<float2> curve_points = ed::greasepencil::polyline_fit_curve(
        coords_pre_blur, max_error_threshold_px * settings_->active_smooth, corner_mask);

    /* Sampling the curve at a fixed resolution. */
    const int64_t sample_resolution = 32;
    Array<float2> sampled_curve_points = sample_curve_2d(curve_points, sample_resolution);

    /* Morphing the coordinates onto the curve. Result is stored in a temporary array. */
    Array<float2> coords_smoothed(coords_to_smooth.size());
    morph_points_to_curve(coords_to_smooth, sampled_curve_points, coords_smoothed);

    MutableSpan<float2> window_coords = self.screen_space_smoothed_coords_.as_mutable_span().slice(
        smooth_window);
    MutableSpan<float3> positions_slice = curve_positions.slice(smooth_window);
    const float converging_threshold_px = 0.1f;
    bool stop_counting_converged = false;
    int num_converged = 0;
    for (const int64_t window_i : smooth_window.index_range()) {
      /* Record the curve fitting of this point. */
      self.screen_space_curve_fitted_coords_[window_i].append(coords_smoothed[window_i]);
      Span<float2> fit_coords = self.screen_space_curve_fitted_coords_[window_i];

      /* We compare the previous arithmetic mean to the current. Going from the back to the front,
       * if a point hasn't moved by a minimum threshold, it counts as converged. */
      float2 new_pos = arithmetic_mean(fit_coords);
      if (!stop_counting_converged) {
        float2 prev_pos = window_coords[window_i];
        if (math::distance(new_pos, prev_pos) < converging_threshold_px) {
          num_converged++;
        }
        else {
          stop_counting_converged = true;
        }
      }

      /* Update the positions in the current cache. */
      window_coords[window_i] = new_pos;
      positions_slice[window_i] = screen_space_to_drawing_plane(new_pos);
    }

    /* Remove all the converged points from the active window and shrink the window accordingly. */
    if (num_converged > 0) {
      self.active_smooth_start_index_ += num_converged;
      self.screen_space_curve_fitted_coords_.remove(0, num_converged);
    }
  }

  void process_extension_sample(PaintOperation &self,
                                const bContext &C,
                                const InputSample &extension_sample)
  {
    const float2 coords = extension_sample.mouse_position;
    const float radius = this->radius_from_input_sample(C, extension_sample);
    const float opacity = this->opacity_from_input_sample(extension_sample);
    const ColorGeometry4f vertex_color = ColorGeometry4f(vertex_color_);

    bke::CurvesGeometry &curves = drawing_->strokes_for_write();
    bke::MutableAttributeAccessor attributes = curves.attributes_for_write();

    const float2 prev_coords = self.screen_space_coords_orig_.last();
    const float prev_radius = drawing_->radii().last();
    const float prev_opacity = drawing_->opacities().last();
    const ColorGeometry4f prev_vertex_color = drawing_->vertex_colors().last();

    /* Overwrite last point if it's very close. */
    if (math::distance(coords, prev_coords) < POINT_OVERRIDE_THRESHOLD_PX) {
      curves.positions_for_write().last() = screen_space_to_drawing_plane(coords);
      drawing_->radii_for_write().last() = math::max(radius, prev_radius);
      drawing_->opacities_for_write().last() = math::max(opacity, prev_opacity);
      return;
    }

    /* If the next sample is far away, we subdivide the segment to add more points. */
    int new_points_num = 1;
    const float distance_px = math::distance(coords, prev_coords);
    if (distance_px > POINT_RESAMPLE_MIN_DISTANCE_PX) {
      const int subdivisions = int(math::floor(distance_px / POINT_RESAMPLE_MIN_DISTANCE_PX)) - 1;
      new_points_num += subdivisions;
    }

    /* Resize the curves geometry. */
    curves.resize(curves.points_num() + new_points_num, curves.curves_num());
    curves.offsets_for_write().last() = curves.points_num();
    const IndexRange curve_points = curves.points_by_curve()[curves.curves_range().last()];

    /* Subdivide stroke in new_points. */
    const IndexRange new_points = curve_points.take_back(new_points_num);
    Array<float2> new_screen_space_coords(new_points_num);
    MutableSpan<float3> positions = curves.positions_for_write();
    MutableSpan<float3> new_positions = positions.slice(new_points);
    MutableSpan<float> new_radii = drawing_->radii_for_write().slice(new_points);
    MutableSpan<float> new_opacities = drawing_->opacities_for_write().slice(new_points);
    MutableSpan<ColorGeometry4f> new_vertex_colors = drawing_->vertex_colors_for_write().slice(
        new_points);
    linear_interpolation<float2>(prev_coords, coords, new_screen_space_coords);
    linear_interpolation<float>(prev_radius, radius, new_radii);
    linear_interpolation<float>(prev_opacity, opacity, new_opacities);
    linear_interpolation<ColorGeometry4f>(prev_vertex_color, vertex_color, new_vertex_colors);

    /* Update screen space buffers with new points. */
    self.screen_space_coords_orig_.extend(new_screen_space_coords);
    self.screen_space_smoothed_coords_.extend(new_screen_space_coords);
    for (float2 new_position : new_screen_space_coords) {
      self.screen_space_curve_fitted_coords_.append(Vector<float2>({new_position}));
    }

    /* Only start smoothing if there are enough points. */
    const int64_t min_active_smoothing_points_num = 8;
    const IndexRange smooth_window = self.screen_space_coords_orig_.index_range().drop_front(
        self.active_smooth_start_index_);
    if (smooth_window.size() < min_active_smoothing_points_num) {
      for (const int64_t i : new_screen_space_coords.index_range()) {
        new_positions[i] = screen_space_to_drawing_plane(new_screen_space_coords[i]);
      }
    }
    else {
      /* Active smoothing is done in a window at the end of the new stroke. */
      this->active_smoothing(self, smooth_window, positions.slice(curve_points));
    }

    /* Initialize the rest of the attributes with default values. */
    Set<std::string> attributes_to_skip{{"position", "radius", "opacity", "vertex_color"}};
    attributes.for_all([&](const bke::AttributeIDRef &id, const bke::AttributeMetaData meta_data) {
      if (attributes_to_skip.contains(id.name()) || meta_data.domain != ATTR_DOMAIN_POINT) {
        return true;
      }
      bke::GSpanAttributeWriter attribute = attributes.lookup_for_write_span(id);
      const CPPType &type = attribute.span.type();
      GMutableSpan new_data = attribute.span.slice(new_points);
      type.fill_assign_n(type.default_value(), new_data.data(), new_data.size());
      attribute.finish();
      return true;
    });
  }

  void execute(PaintOperation &self, const bContext &C, const InputSample &extension_sample)
  {
    this->process_extension_sample(self, C, extension_sample);
    drawing_->tag_topology_changed();
  }
};

void PaintOperation::on_stroke_begin(const bContext &C, const InputSample &start_sample)
{
  Scene *scene = CTX_data_scene(&C);
  Object *object = CTX_data_active_object(&C);
  GreasePencil *grease_pencil = static_cast<GreasePencil *>(object->data);

  Paint *paint = &scene->toolsettings->gp_paint->paint;
  Brush *brush = BKE_paint_brush(paint);

  BKE_curvemapping_init(brush->gpencil_settings->curve_sensitivity);
  BKE_curvemapping_init(brush->gpencil_settings->curve_strength);
  BKE_curvemapping_init(brush->gpencil_settings->curve_jitter);
  BKE_curvemapping_init(brush->gpencil_settings->curve_rand_pressure);
  BKE_curvemapping_init(brush->gpencil_settings->curve_rand_strength);
  BKE_curvemapping_init(brush->gpencil_settings->curve_rand_uv);
  BKE_curvemapping_init(brush->gpencil_settings->curve_rand_hue);
  BKE_curvemapping_init(brush->gpencil_settings->curve_rand_saturation);
  BKE_curvemapping_init(brush->gpencil_settings->curve_rand_value);

  Material *material = BKE_grease_pencil_object_material_ensure_from_active_input_brush(
      CTX_data_main(&C), object, brush);
  const int material_index = BKE_grease_pencil_object_material_index_get(object, material);

  PaintOperationExecutor executor{C};
  executor.process_start_sample(*this, C, start_sample, material_index);

  DEG_id_tag_update(&grease_pencil->id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(&C, NC_GEOM | ND_DATA, grease_pencil);
}

void PaintOperation::on_stroke_extended(const bContext &C, const InputSample &extension_sample)
{
  Object *object = CTX_data_active_object(&C);
  GreasePencil *grease_pencil = static_cast<GreasePencil *>(object->data);

  PaintOperationExecutor executor{C};
  executor.execute(*this, C, extension_sample);

  DEG_id_tag_update(&grease_pencil->id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(&C, NC_GEOM | ND_DATA, grease_pencil);
}

static float dist_to_interpolated_2d(
    float2 pos, float2 posA, float2 posB, float val, float valA, float valB)
{
  const float dist1 = math::distance_squared(posA, pos);
  const float dist2 = math::distance_squared(posB, pos);

  if (dist1 + dist2 > 1e-5f) {
    const float interpolated_val = math::interpolate(valB, valA, dist1 / (dist1 + dist2));
    return math::distance(interpolated_val, val);
  }
  return 0.0f;
}

void PaintOperation::simplify_stroke(bke::greasepencil::Drawing &drawing, const float epsilon_px)
{
  const int stroke_index = drawing.strokes().curves_range().last();
  const IndexRange points = drawing.strokes().points_by_curve()[stroke_index];
  bke::CurvesGeometry &curves = drawing.strokes_for_write();
  const VArray<float> radii = drawing.radii();

  /* Distance function for `ramer_douglas_peucker_simplify`. */
  const Span<float2> positions_2d = this->screen_space_smoothed_coords_.as_span();
  const auto dist_function = [&](int64_t first_index, int64_t last_index, int64_t index) {
    /* 2D coordinates are only stored for the current stroke, so offset the indices. */
    const float dist_position_px = dist_to_line_segment_v2(
        positions_2d[index - points.first()],
        positions_2d[first_index - points.first()],
        positions_2d[last_index - points.first()]);
    const float dist_radii_px = dist_to_interpolated_2d(positions_2d[index - points.first()],
                                                        positions_2d[first_index - points.first()],
                                                        positions_2d[last_index - points.first()],
                                                        radii[index],
                                                        radii[first_index],
                                                        radii[last_index]);
    return math::max(dist_position_px, dist_radii_px);
  };

  Array<bool> points_to_delete(curves.points_num(), false);
  int64_t total_points_to_delete = ed::greasepencil::ramer_douglas_peucker_simplify(
      points, epsilon_px, dist_function, points_to_delete.as_mutable_span());

  if (total_points_to_delete > 0) {
    IndexMaskMemory memory;
    curves.remove_points(IndexMask::from_bools(points_to_delete, memory));
  }
}

void PaintOperation::process_stroke_end(bke::greasepencil::Drawing &drawing)
{
  const int stroke_index = drawing.strokes().curves_range().last();
  const IndexRange points = drawing.strokes().points_by_curve()[stroke_index];
  bke::CurvesGeometry &curves = drawing.strokes_for_write();
  const VArray<float> radii = drawing.radii();

  /* Remove points at the end that have a radius close to 0. */
  int64_t points_to_remove = 0;
  for (int64_t index = points.last(); index >= points.first(); index--) {
    if (radii[index] < 1e-5f) {
      points_to_remove++;
    }
    else {
      break;
    }
  }
  if (points_to_remove > 0) {
    curves.resize(curves.points_num() - points_to_remove, curves.curves_num());
    curves.offsets_for_write().last() = curves.points_num();
  }
}

void PaintOperation::on_stroke_done(const bContext &C)
{
  using namespace blender::bke;
  Scene *scene = CTX_data_scene(&C);
  Object *object = CTX_data_active_object(&C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);

  /* Grease Pencil should have an active layer. */
  BLI_assert(grease_pencil.has_active_layer());
  bke::greasepencil::Layer &active_layer = *grease_pencil.get_active_layer_for_write();
  const int drawing_index = active_layer.drawing_index_at(scene->r.cfra);

  /* Drawing should exist. */
  BLI_assert(drawing_index >= 0);
  bke::greasepencil::Drawing &drawing =
      reinterpret_cast<GreasePencilDrawing *>(grease_pencil.drawing(drawing_index))->wrap();

  const float simplifiy_threshold_px = 0.5f;
  this->simplify_stroke(drawing, simplifiy_threshold_px);
  this->process_stroke_end(drawing);
  drawing.tag_topology_changed();

  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_main_add_notifier(NC_GEOM | ND_DATA, &grease_pencil.id);
}

std::unique_ptr<GreasePencilStrokeOperation> new_paint_operation()
{
  return std::make_unique<PaintOperation>();
}

}  // namespace blender::ed::sculpt_paint::greasepencil
