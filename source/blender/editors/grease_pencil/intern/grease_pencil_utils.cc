/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edgreasepencil
 */

#include "BKE_attribute.hh"
#include "BKE_brush.hh"
#include "BKE_context.hh"
#include "BKE_grease_pencil.hh"
#include "BKE_material.h"
#include "BKE_scene.h"

#include "BLI_bit_span_ops.hh"
#include "BLI_bit_vector.hh"
#include "BLI_math_geom.h"
#include "BLI_math_vector.hh"
#include "BLI_vector_set.hh"

#include "DNA_brush_types.h"
#include "DNA_material_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_view3d_types.h"

#include "ED_curves.hh"
#include "ED_grease_pencil.hh"
#include "ED_view3d.hh"

namespace blender::ed::greasepencil {

DrawingPlacement::DrawingPlacement(const Scene &scene,
                                   const ARegion &region,
                                   const View3D &view3d,
                                   const Object &object)
    : region_(&region), view3d_(&view3d), transforms_(object)
{
  /* Initialize DrawingPlacementPlane from toolsettings. */
  switch (scene.toolsettings->gp_sculpt.lock_axis) {
    case GP_LOCKAXIS_VIEW:
      plane_ = DrawingPlacementPlane::View;
      break;
    case GP_LOCKAXIS_Y:
      plane_ = DrawingPlacementPlane::Front;
      placement_normal_ = float3(0, 1, 0);
      break;
    case GP_LOCKAXIS_X:
      plane_ = DrawingPlacementPlane::Side;
      placement_normal_ = float3(1, 0, 0);
      break;
    case GP_LOCKAXIS_Z:
      plane_ = DrawingPlacementPlane::Top;
      placement_normal_ = float3(0, 0, 1);
      break;
    case GP_LOCKAXIS_CURSOR: {
      plane_ = DrawingPlacementPlane::Cursor;
      float3x3 mat;
      BKE_scene_cursor_rot_to_mat3(&scene.cursor, mat.ptr());
      placement_normal_ = mat * float3(0, 0, 1);
      break;
    }
  }
  /* Initialize DrawingPlacementDepth from toolsettings. */
  switch (scene.toolsettings->gpencil_v3d_align) {
    case GP_PROJECT_VIEWSPACE:
      depth_ = DrawingPlacementDepth::ObjectOrigin;
      placement_loc_ = transforms_.layer_space_to_world_space.location();
      break;
    case (GP_PROJECT_VIEWSPACE | GP_PROJECT_CURSOR):
      depth_ = DrawingPlacementDepth::Cursor;
      placement_loc_ = float3(scene.cursor.location);
      break;
    case (GP_PROJECT_VIEWSPACE | GP_PROJECT_DEPTH_VIEW):
      depth_ = DrawingPlacementDepth::Surface;
      surface_offset_ = scene.toolsettings->gpencil_surface_offset;
      /* Default to view placement with the object origin if we don't hit a surface. */
      placement_loc_ = transforms_.layer_space_to_world_space.location();
      break;
    case (GP_PROJECT_VIEWSPACE | GP_PROJECT_DEPTH_STROKE):
      depth_ = DrawingPlacementDepth::NearestStroke;
      /* Default to view placement with the object origin if we don't hit a stroke. */
      placement_loc_ = transforms_.layer_space_to_world_space.location();
      break;
  }

  if (ELEM(plane_,
           DrawingPlacementPlane::Front,
           DrawingPlacementPlane::Side,
           DrawingPlacementPlane::Top,
           DrawingPlacementPlane::Cursor) &&
      ELEM(depth_, DrawingPlacementDepth::ObjectOrigin, DrawingPlacementDepth::Cursor))
  {
    plane_from_point_normal_v3(placement_plane_, placement_loc_, placement_normal_);
  }
}

DrawingPlacement::~DrawingPlacement()
{
  if (depth_cache_ != nullptr) {
    ED_view3d_depths_free(depth_cache_);
  }
}

bool DrawingPlacement::use_project_to_surface() const
{
  return depth_ == DrawingPlacementDepth::Surface;
}

bool DrawingPlacement::use_project_to_nearest_stroke() const
{
  return depth_ == DrawingPlacementDepth::NearestStroke;
}

void DrawingPlacement::cache_viewport_depths(Depsgraph *depsgraph, ARegion *region, View3D *view3d)
{
  const eV3DDepthOverrideMode mode = (depth_ == DrawingPlacementDepth::Surface) ?
                                         V3D_DEPTH_NO_GPENCIL :
                                         V3D_DEPTH_GPENCIL_ONLY;
  ED_view3d_depth_override(depsgraph, region, view3d, nullptr, mode, &this->depth_cache_);
}

void DrawingPlacement::set_origin_to_nearest_stroke(const float2 co)
{
  BLI_assert(depth_cache_ != nullptr);
  float depth;
  if (ED_view3d_depth_read_cached(depth_cache_, int2(co), 4, &depth)) {
    float3 origin;
    ED_view3d_depth_unproject_v3(region_, int2(co), depth, origin);

    placement_loc_ = origin;
  }
  else {
    /* If nothing was hit, use origin. */
    placement_loc_ = transforms_.layer_space_to_world_space.location();
  }
  plane_from_point_normal_v3(placement_plane_, placement_loc_, placement_normal_);
}

float3 DrawingPlacement::project(const float2 co) const
{
  float3 proj_point;
  if (depth_ == DrawingPlacementDepth::Surface) {
    /* Project using the viewport depth cache. */
    BLI_assert(depth_cache_ != nullptr);
    float depth;
    if (ED_view3d_depth_read_cached(depth_cache_, int2(co), 4, &depth)) {
      ED_view3d_depth_unproject_v3(region_, int2(co), depth, proj_point);
      float3 normal;
      ED_view3d_depth_read_cached_normal(region_, depth_cache_, int2(co), normal);
      proj_point += normal * surface_offset_;
    }
    /* If we didn't hit anything, use the view plane for placement. */
    else {
      ED_view3d_win_to_3d(view3d_, region_, placement_loc_, co, proj_point);
    }
  }
  else {
    if (ELEM(plane_,
             DrawingPlacementPlane::Front,
             DrawingPlacementPlane::Side,
             DrawingPlacementPlane::Top,
             DrawingPlacementPlane::Cursor))
    {
      ED_view3d_win_to_3d_on_plane(region_, placement_plane_, co, false, proj_point);
    }
    else if (plane_ == DrawingPlacementPlane::View) {
      ED_view3d_win_to_3d(view3d_, region_, placement_loc_, co, proj_point);
    }
  }
  return math::transform_point(transforms_.world_space_to_layer_space, proj_point);
}

void DrawingPlacement::project(const Span<float2> src, MutableSpan<float3> dst) const
{
  threading::parallel_for(src.index_range(), 1024, [&](const IndexRange range) {
    for (const int i : range) {
      dst[i] = this->project(src[i]);
    }
  });
}

static float3 drawing_origin(const Scene *scene, const Object *object, char align_flag)
{
  BLI_assert(object != nullptr && object->type == OB_GREASE_PENCIL);
  if (align_flag & GP_PROJECT_VIEWSPACE) {
    if (align_flag & GP_PROJECT_CURSOR) {
      return float3(scene->cursor.location);
    }
    /* Use the object location. */
    return float3(object->object_to_world[3]);
  }
  return float3(scene->cursor.location);
}

static float3 screen_space_to_3d(
    const Scene *scene, const ARegion *region, const View3D *v3d, const Object *object, float2 co)
{
  float3 origin = drawing_origin(scene, object, scene->toolsettings->gpencil_v3d_align);
  float3 r_co;
  ED_view3d_win_to_3d(v3d, region, origin, co, r_co);
  return r_co;
}

float brush_radius_world_space(bContext &C, int x, int y)
{
  ARegion *region = CTX_wm_region(&C);
  View3D *v3d = CTX_wm_view3d(&C);
  Scene *scene = CTX_data_scene(&C);
  Object *object = CTX_data_active_object(&C);
  Brush *brush = scene->toolsettings->gp_paint->paint.brush;

  /* Default radius. */
  float radius = 2.0f;
  if (brush == nullptr || object->type != OB_GREASE_PENCIL) {
    return radius;
  }

  /* Use an (arbitrary) screen space offset in the x direction to measure the size. */
  const int x_offest = 64;
  const float brush_size = float(BKE_brush_size_get(scene, brush));

  /* Get two 3d coordinates to measure the distance from. */
  const float2 screen1(x, y);
  const float2 screen2(x + x_offest, y);
  const float3 pos1 = screen_space_to_3d(scene, region, v3d, object, screen1);
  const float3 pos2 = screen_space_to_3d(scene, region, v3d, object, screen2);

  /* Clip extreme zoom level (and avoid division by zero). */
  const float distance = math::max(math::distance(pos1, pos2), 0.001f);

  /* Calculate the radius of the brush in world space. */
  radius = (1.0f / distance) * (brush_size / 64.0f);

  return radius;
}

static Array<int> get_frame_numbers_for_layer(const bke::greasepencil::Layer &layer,
                                              const int current_frame,
                                              const bool use_multi_frame_editing)
{
  Vector<int> frame_numbers({current_frame});
  if (use_multi_frame_editing) {
    for (const auto [frame_number, frame] : layer.frames().items()) {
      if (frame_number != current_frame && frame.is_selected()) {
        frame_numbers.append_unchecked(frame_number);
      }
    }
  }
  return frame_numbers.as_span();
}

Array<MutableDrawingInfo> retrieve_editable_drawings(const Scene &scene,
                                                     GreasePencil &grease_pencil)
{
  using namespace blender::bke::greasepencil;
  const int current_frame = scene.r.cfra;
  const ToolSettings *toolsettings = scene.toolsettings;
  const bool use_multi_frame_editing = (toolsettings->gpencil_flags &
                                        GP_USE_MULTI_FRAME_EDITING) != 0;

  Vector<MutableDrawingInfo> editable_drawings;
  Span<const Layer *> layers = grease_pencil.layers();
  for (const int layer_i : layers.index_range()) {
    const Layer &layer = *layers[layer_i];
    if (!layer.is_editable()) {
      continue;
    }
    const Array<int> frame_numbers = get_frame_numbers_for_layer(
        layer, current_frame, use_multi_frame_editing);
    for (const int frame_number : frame_numbers) {
      if (Drawing *drawing = grease_pencil.get_editable_drawing_at(layer, frame_number)) {
        editable_drawings.append({*drawing, layer_i, frame_number});
      }
    }
  }

  return editable_drawings.as_span();
}

Array<DrawingInfo> retrieve_visible_drawings(const Scene &scene, const GreasePencil &grease_pencil)
{
  using namespace blender::bke::greasepencil;
  const int current_frame = scene.r.cfra;
  const ToolSettings *toolsettings = scene.toolsettings;
  const bool use_multi_frame_editing = (toolsettings->gpencil_flags &
                                        GP_USE_MULTI_FRAME_EDITING) != 0;

  Vector<DrawingInfo> visible_drawings;
  Span<const Layer *> layers = grease_pencil.layers();
  for (const int layer_i : layers.index_range()) {
    const Layer &layer = *layers[layer_i];
    if (!layer.is_visible()) {
      continue;
    }
    const Array<int> frame_numbers = get_frame_numbers_for_layer(
        layer, current_frame, use_multi_frame_editing);
    for (const int frame_number : frame_numbers) {
      if (const Drawing *drawing = grease_pencil.get_drawing_at(layer, frame_number)) {
        visible_drawings.append({*drawing, layer_i, frame_number});
      }
    }
  }

  return visible_drawings.as_span();
}

static VectorSet<int> get_editable_material_indices(Object &object)
{
  BLI_assert(object.type == OB_GREASE_PENCIL);
  VectorSet<int> editable_material_indices;
  for (const int mat_i : IndexRange(object.totcol)) {
    Material *material = BKE_object_material_get(&object, mat_i + 1);
    /* The editable materials are unlocked and not hidden. */
    if (material != nullptr && material->gp_style != nullptr &&
        (material->gp_style->flag & GP_MATERIAL_LOCKED) == 0 &&
        (material->gp_style->flag & GP_MATERIAL_HIDE) == 0)
    {
      editable_material_indices.add_new(mat_i);
    }
  }
  return editable_material_indices;
}

static VectorSet<int> get_hidden_material_indices(Object &object)
{
  BLI_assert(object.type == OB_GREASE_PENCIL);
  VectorSet<int> hidden_material_indices;
  for (const int mat_i : IndexRange(object.totcol)) {
    Material *material = BKE_object_material_get(&object, mat_i + 1);
    if (material != nullptr && material->gp_style != nullptr &&
        (material->gp_style->flag & GP_MATERIAL_HIDE) != 0)
    {
      hidden_material_indices.add_new(mat_i);
    }
  }
  return hidden_material_indices;
}

IndexMask retrieve_editable_strokes(Object &object,
                                    const bke::greasepencil::Drawing &drawing,
                                    IndexMaskMemory &memory)
{
  using namespace blender;

  /* Get all the editable material indices */
  VectorSet<int> editable_material_indices = get_editable_material_indices(object);
  if (editable_material_indices.is_empty()) {
    return {};
  }

  const bke::CurvesGeometry &curves = drawing.strokes();
  const IndexRange curves_range = drawing.strokes().curves_range();
  const bke::AttributeAccessor attributes = curves.attributes();

  const VArray<int> materials = *attributes.lookup<int>("material_index", bke::AttrDomain::Curve);
  if (!materials) {
    /* If the attribute does not exist then the default is the first material. */
    if (editable_material_indices.contains(0)) {
      return curves_range;
    }
    return {};
  }
  /* Get all the strokes that have their material unlocked. */
  return IndexMask::from_predicate(
      curves_range, GrainSize(4096), memory, [&](const int64_t curve_i) {
        const int material_index = materials[curve_i];
        return editable_material_indices.contains(material_index);
      });
}

IndexMask retrieve_editable_points(Object &object,
                                   const bke::greasepencil::Drawing &drawing,
                                   IndexMaskMemory &memory)
{
  /* Get all the editable material indices */
  VectorSet<int> editable_material_indices = get_editable_material_indices(object);
  if (editable_material_indices.is_empty()) {
    return {};
  }

  const bke::CurvesGeometry &curves = drawing.strokes();
  const IndexRange points_range = drawing.strokes().points_range();
  const bke::AttributeAccessor attributes = curves.attributes();

  /* Propagate the material index to the points. */
  const VArray<int> materials = *attributes.lookup<int>("material_index", bke::AttrDomain::Point);
  if (!materials) {
    /* If the attribute does not exist then the default is the first material. */
    if (editable_material_indices.contains(0)) {
      return points_range;
    }
    return {};
  }
  /* Get all the points that are part of a stroke with an unlocked material. */
  return IndexMask::from_predicate(
      points_range, GrainSize(4096), memory, [&](const int64_t point_i) {
        const int material_index = materials[point_i];
        return editable_material_indices.contains(material_index);
      });
}

IndexMask retrieve_editable_elements(Object &object,
                                     const bke::greasepencil::Drawing &drawing,
                                     const bke::AttrDomain selection_domain,
                                     IndexMaskMemory &memory)
{
  if (selection_domain == bke::AttrDomain::Curve) {
    return ed::greasepencil::retrieve_editable_strokes(object, drawing, memory);
  }
  else if (selection_domain == bke::AttrDomain::Point) {
    return ed::greasepencil::retrieve_editable_points(object, drawing, memory);
  }
  return {};
}

IndexMask retrieve_visible_strokes(Object &object,
                                   const bke::greasepencil::Drawing &drawing,
                                   IndexMaskMemory &memory)
{
  using namespace blender;

  /* Get all the hidden material indices. */
  VectorSet<int> hidden_material_indices = get_hidden_material_indices(object);

  if (hidden_material_indices.is_empty()) {
    return drawing.strokes().curves_range();
  }

  const bke::CurvesGeometry &curves = drawing.strokes();
  const IndexRange curves_range = drawing.strokes().curves_range();
  const bke::AttributeAccessor attributes = curves.attributes();

  /* Get all the strokes that have their material visible. */
  const VArray<int> materials = *attributes.lookup_or_default<int>(
      "material_index", bke::AttrDomain::Curve, -1);
  return IndexMask::from_predicate(
      curves_range, GrainSize(4096), memory, [&](const int64_t curve_i) {
        const int material_index = materials[curve_i];
        return !hidden_material_indices.contains(material_index);
      });
}

IndexMask retrieve_editable_and_selected_strokes(Object &object,
                                                 const bke::greasepencil::Drawing &drawing,
                                                 IndexMaskMemory &memory)
{
  using namespace blender;

  const bke::CurvesGeometry &curves = drawing.strokes();
  const IndexRange curves_range = drawing.strokes().curves_range();

  const IndexMask editable_strokes = retrieve_editable_strokes(object, drawing, memory);
  const IndexMask selected_strokes = ed::curves::retrieve_selected_curves(curves, memory);

  BitVector<> editable_strokes_bits(curves.curves_num(), false);
  editable_strokes.to_bits(editable_strokes_bits);
  BitVector<> selected_strokes_bits(curves.curves_num(), false);
  selected_strokes.to_bits(selected_strokes_bits);

  editable_strokes_bits &= selected_strokes_bits;
  return IndexMask::from_bits(curves_range, editable_strokes_bits, memory);
}

IndexMask retrieve_editable_and_selected_points(Object &object,
                                                const bke::greasepencil::Drawing &drawing,
                                                IndexMaskMemory &memory)
{
  const bke::CurvesGeometry &curves = drawing.strokes();
  const IndexRange points_range = drawing.strokes().points_range();

  const IndexMask editable_points = retrieve_editable_points(object, drawing, memory);
  const IndexMask selected_points = ed::curves::retrieve_selected_points(curves, memory);

  BitVector<> editable_points_bits(curves.points_num(), false);
  editable_points.to_bits(editable_points_bits);
  BitVector<> selected_points_bits(curves.points_num(), false);
  selected_points.to_bits(selected_points_bits);

  editable_points_bits &= selected_points_bits;
  return IndexMask::from_bits(points_range, editable_points_bits, memory);
}

IndexMask retrieve_editable_and_selected_elements(Object &object,
                                                  const bke::greasepencil::Drawing &drawing,
                                                  const bke::AttrDomain selection_domain,
                                                  IndexMaskMemory &memory)
{
  if (selection_domain == bke::AttrDomain::Curve) {
    return ed::greasepencil::retrieve_editable_and_selected_strokes(object, drawing, memory);
  }
  else if (selection_domain == bke::AttrDomain::Point) {
    return ed::greasepencil::retrieve_editable_and_selected_points(object, drawing, memory);
  }
  return {};
}

}  // namespace blender::ed::greasepencil
