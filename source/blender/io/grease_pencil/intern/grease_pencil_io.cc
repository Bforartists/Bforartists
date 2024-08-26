/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_color.hh"
#include "BLI_math_matrix.hh"
#include "BLI_math_vector.h"

#include "BKE_attribute.hh"
#include "BKE_camera.h"
#include "BKE_context.hh"
#include "BKE_crazyspace.hh"
#include "BKE_curves.hh"
#include "BKE_gpencil_legacy.h"
#include "BKE_grease_pencil.hh"
#include "BKE_layer.hh"
#include "BKE_material.h"
#include "BKE_scene.hh"

#include "BLI_math_vector.hh"
#include "DNA_grease_pencil_types.h"
#include "DNA_material_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_view3d_types.h"

#include "DEG_depsgraph_query.hh"

#include "GEO_resample_curves.hh"

#include "ED_grease_pencil.hh"
#include "ED_object.hh"
#include "ED_view3d.hh"

#include "UI_view2d.hh"

#include "grease_pencil_io_intern.hh"
#include <optional>

/** \file
 * \ingroup bgrease_pencil
 */

namespace blender::io::grease_pencil {

static float get_average(const Span<float> values)
{
  return values.is_empty() ? 0.0f :
                             std::accumulate(values.begin(), values.end(), 0.0f) / values.size();
}

static ColorGeometry4f get_average(const Span<ColorGeometry4f> values)
{
  if (values.is_empty()) {
    return ColorGeometry4f(nullptr);
  }
  /* ColorGeometry4f does not support arithmetic directly. */
  Span<float4> rgba_values = values.cast<float4>();
  float4 avg_rgba = std::accumulate(rgba_values.begin(), rgba_values.end(), float4(0)) /
                    values.size();
  return ColorGeometry4f(avg_rgba);
}

static std::optional<float> try_get_constant_value(const VArray<float> values,
                                                   const float epsilon = 1e-5f)
{
  if (values.is_empty()) {
    return std::nullopt;
  }
  const float first_value = values.first();
  const std::optional<float> first_value_opt = std::make_optional(first_value);
  return threading::parallel_reduce(
      values.index_range().drop_front(1),
      4096,
      first_value_opt,
      [&](const IndexRange range, const std::optional<float> /*value*/) -> std::optional<float> {
        for (const int i : range) {
          if (math::abs(values[i] - first_value) > epsilon) {
            return std::nullopt;
          }
        }
        return first_value_opt;
      },
      [&](const std::optional<float> a, const std::optional<float> b) {
        return (a && b) ? first_value_opt : std::nullopt;
      });
}

IOContext::IOContext(bContext &C,
                     const ARegion *region,
                     const View3D *v3d,
                     const RegionView3D *rv3d,
                     ReportList *reports)
    : reports(reports),
      C(C),
      region(region),
      v3d(v3d),
      rv3d(rv3d),
      scene(CTX_data_scene(&C)),
      depsgraph(CTX_data_depsgraph_pointer(&C))
{
}

GreasePencilImporter::GreasePencilImporter(const IOContext &context, const ImportParams &params)
    : context_(context), params_(params)
{
}

Object *GreasePencilImporter::create_object(const StringRefNull name)
{
  const float3 cur_loc = context_.scene->cursor.location;
  const float3 rot = float3(0.0f);
  const ushort local_view_bits = (context_.v3d && context_.v3d->localvd) ?
                                     context_.v3d->local_view_uid :
                                     ushort(0);

  Object *ob_gpencil = blender::ed::object::add_type(
      &context_.C, OB_GREASE_PENCIL, name.c_str(), cur_loc, rot, false, local_view_bits);

  return ob_gpencil;
}

int GreasePencilImporter::create_material(const StringRefNull name,
                                          const bool stroke,
                                          const bool fill)
{
  const ColorGeometry4f default_stroke_color = {0.0f, 0.0f, 0.0f, 1.0f};
  const ColorGeometry4f default_fill_color = {0.5f, 0.5f, 0.5f, 1.0f};
  int mat_index = BKE_gpencil_object_material_index_get_by_name(object_, name.c_str());
  /* Stroke and Fill material. */
  if (mat_index == -1) {
    Main *bmain = CTX_data_main(&context_.C);
    int new_idx;
    Material *mat_gp = BKE_gpencil_object_material_new(bmain, object_, name.c_str(), &new_idx);
    MaterialGPencilStyle *gp_style = mat_gp->gp_style;
    gp_style->flag &= ~GP_MATERIAL_STROKE_SHOW;
    gp_style->flag &= ~GP_MATERIAL_FILL_SHOW;

    copy_v4_v4(gp_style->stroke_rgba, default_stroke_color);
    copy_v4_v4(gp_style->fill_rgba, default_fill_color);
    if (stroke) {
      gp_style->flag |= GP_MATERIAL_STROKE_SHOW;
    }
    if (fill) {
      gp_style->flag |= GP_MATERIAL_FILL_SHOW;
    }
    mat_index = object_->totcol - 1;
  }

  return mat_index;
}

GreasePencilExporter::GreasePencilExporter(const IOContext &context, const ExportParams &params)
    : context_(context), params_(params)
{
}

constexpr const char *attr_material_index = "material_index";

static IndexMask get_visible_strokes(const Object &object,
                                     const bke::greasepencil::Drawing &drawing,
                                     IndexMaskMemory &memory)
{
  const bke::CurvesGeometry &strokes = drawing.strokes();
  const bke::AttributeAccessor attributes = strokes.attributes();
  const VArray<int> materials = *attributes.lookup<int>(attr_material_index,
                                                        bke::AttrDomain::Curve);

  auto is_visible_curve = [&](const int curve_i) {
    /* Check if stroke can be drawn. */
    const IndexRange points = strokes.points_by_curve()[curve_i];
    if (points.size() < 2) {
      return false;
    }

    /* Check if the material is visible. */
    const Material *material = BKE_object_material_get(const_cast<Object *>(&object),
                                                       materials[curve_i] + 1);
    const MaterialGPencilStyle *gp_style = material ? material->gp_style : nullptr;
    const bool is_hidden_material = (gp_style->flag & GP_MATERIAL_HIDE);
    const bool is_stroke_material = (gp_style->flag & GP_MATERIAL_STROKE_SHOW);
    if (gp_style == nullptr || is_hidden_material || !is_stroke_material) {
      return false;
    }

    return true;
  };

  return IndexMask::from_predicate(
      strokes.curves_range(), GrainSize(512), memory, is_visible_curve);
}

static std::optional<Bounds<float2>> compute_drawing_bounds(
    const ARegion &region,
    const RegionView3D &rv3d,
    const Object &object,
    const Object &object_eval,
    const int layer_index,
    const int frame_number,
    const bke::greasepencil::Drawing &drawing)
{
  using bke::greasepencil::Drawing;
  using bke::greasepencil::Layer;

  std::optional<Bounds<float2>> drawing_bounds = std::nullopt;

  BLI_assert(object.type == OB_GREASE_PENCIL);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object.data);
  if (!grease_pencil.has_active_layer()) {
    return drawing_bounds;
  }

  const Layer &layer = *grease_pencil.layers()[layer_index];
  const float4x4 layer_to_world = layer.to_world_space(object);
  const bke::crazyspace::GeometryDeformation deformation =
      bke::crazyspace::get_evaluated_grease_pencil_drawing_deformation(
          &object_eval, object, layer_index, frame_number);
  const VArray<float> radii = drawing.radii();
  const bke::CurvesGeometry &strokes = drawing.strokes();

  IndexMaskMemory curve_mask_memory;
  const IndexMask curve_mask = get_visible_strokes(object, drawing, curve_mask_memory);

  curve_mask.foreach_index(GrainSize(512), [&](const int curve_i) {
    const IndexRange points = strokes.points_by_curve()[curve_i];
    /* Check if stroke can be drawn. */
    if (points.size() < 2) {
      return;
    }

    for (const int point_i : points) {
      const float3 pos_world = math::transform_point(layer_to_world,
                                                     deformation.positions[point_i]);
      float2 screen_co;
      eV3DProjStatus result = ED_view3d_project_float_global(
          &region, pos_world, screen_co, V3D_PROJ_TEST_NOP);
      if (result == V3D_PROJ_RET_OK) {
        const float pixels = radii[point_i] / ED_view3d_pixel_size(&rv3d, pos_world);

        std::optional<Bounds<float2>> point_bounds = Bounds<float2>(screen_co);
        point_bounds->pad(pixels);
        drawing_bounds = bounds::merge(drawing_bounds, point_bounds);
      }
    }
  });

  return drawing_bounds;
}

static std::optional<Bounds<float2>> compute_objects_bounds(
    const ARegion &region,
    const RegionView3D &rv3d,
    const Depsgraph &depsgraph,
    const Span<GreasePencilExporter::ObjectInfo> objects,
    const int frame_number)
{
  using bke::greasepencil::Drawing;
  using bke::greasepencil::Layer;
  using ObjectInfo = GreasePencilExporter::ObjectInfo;

  constexpr float gap = 10.0f;

  std::optional<Bounds<float2>> full_bounds = std::nullopt;

  for (const ObjectInfo &info : objects) {
    const Object *object_eval = DEG_get_evaluated_object(&depsgraph, info.object);
    const GreasePencil &grease_pencil_eval = *static_cast<GreasePencil *>(object_eval->data);

    for (const int layer_index : grease_pencil_eval.layers().index_range()) {
      const Layer &layer = *grease_pencil_eval.layers()[layer_index];
      const Drawing *drawing = grease_pencil_eval.get_drawing_at(layer, frame_number);
      if (drawing == nullptr) {
        continue;
      }

      std::optional<Bounds<float2>> layer_bounds = compute_drawing_bounds(
          region, rv3d, *info.object, *object_eval, layer_index, frame_number, *drawing);

      full_bounds = bounds::merge(full_bounds, layer_bounds);
    }
  }

  /* Add small gap. */
  full_bounds->pad(gap);

  return full_bounds;
}

static float4x4 persmat_from_camera_object(Scene &scene)
{
  /* Ensure camera switch is applied. */
  BKE_scene_camera_switch_update(&scene);

  /* Calculate camera matrix. */
  Object *cam_ob = scene.camera;
  if (cam_ob == nullptr) {
    /* XXX not sure when this could ever happen if v3d camera is not null,
     * conditions are from GPv2 and not explained anywhere. */
    return float4x4::identity();
  }

  /* Set up parameters. */
  CameraParams params;
  BKE_camera_params_init(&params);
  BKE_camera_params_from_object(&params, cam_ob);

  /* Compute matrix, view-plane, etc. */
  BKE_camera_params_compute_viewplane(
      &params, scene.r.xsch, scene.r.ysch, scene.r.xasp, scene.r.yasp);
  BKE_camera_params_compute_matrix(&params);

  float4x4 viewmat = math::invert(cam_ob->object_to_world());
  return float4x4(params.winmat) * viewmat;
}

void GreasePencilExporter::prepare_render_params(Scene &scene, const int frame_number)
{
  const bool use_camera_view = (context_.rv3d->persp == RV3D_CAMOB) &&
                               (context_.v3d->camera != nullptr);

  /* Camera rectangle. */
  if (use_camera_view) {
    rctf camera_rect;
    ED_view3d_calc_camera_border(&scene,
                                 context_.depsgraph,
                                 context_.region,
                                 context_.v3d,
                                 context_.rv3d,
                                 &camera_rect,
                                 true);
    render_rect_ = {{camera_rect.xmin, camera_rect.ymin}, {camera_rect.xmax, camera_rect.ymax}};
    camera_persmat_ = persmat_from_camera_object(scene);
  }
  else {
    Vector<ObjectInfo> objects = this->retrieve_objects();
    std::optional<Bounds<float2>> full_bounds = compute_objects_bounds(
        *context_.region, *context_.rv3d, *context_.depsgraph, objects, frame_number);
    render_rect_ = full_bounds ? *full_bounds : Bounds<float2>{float2(0.0f), float2(0.0f)};
    camera_persmat_ = std::nullopt;
  }
}

ColorGeometry4f GreasePencilExporter::compute_average_stroke_color(
    const Material &material, const Span<ColorGeometry4f> vertex_colors)
{
  const MaterialGPencilStyle &gp_style = *material.gp_style;

  const ColorGeometry4f material_color = ColorGeometry4f(gp_style.stroke_rgba);
  const ColorGeometry4f avg_vertex_color = get_average(vertex_colors);
  return math::interpolate(material_color, avg_vertex_color, avg_vertex_color.a);
}

float GreasePencilExporter::compute_average_stroke_opacity(const Span<float> opacities)
{
  return get_average(opacities);
}

std::optional<float> GreasePencilExporter::try_get_uniform_point_width(
    const RegionView3D &rv3d, const Span<float3> world_positions, const Span<float> radii)
{
  VArray<float> widths = VArray<float>::ForFunc(world_positions.size(), [&](const int index) {
    const float3 &pos = world_positions[index];
    const float radius = radii[index];
    return 2.0f * radius * ED_view3d_pixel_size(&rv3d, pos);
  });
  return try_get_constant_value(widths);
}

Vector<GreasePencilExporter::ObjectInfo> GreasePencilExporter::retrieve_objects() const
{
  using SelectMode = ExportParams::SelectMode;

  Scene &scene = *CTX_data_scene(&context_.C);
  ViewLayer *view_layer = CTX_data_view_layer(&context_.C);
  const float3 camera_z_axis = float3(context_.rv3d->viewinv[2]);

  BKE_view_layer_synced_ensure(&scene, view_layer);

  Vector<ObjectInfo> objects;
  auto add_object = [&](Object *object) {
    if (object == nullptr || object->type != OB_GREASE_PENCIL) {
      return;
    }

    const float3 position = object->object_to_world().location();

    /* Save z-depth from view to sort from back to front. */
    const bool use_ortho_depth = camera_persmat_ || !context_.rv3d->is_persp;
    const float depth = use_ortho_depth ? math::dot(camera_z_axis, position) :
                                          -ED_view3d_calc_zfac(context_.rv3d, position);
    objects.append({object, depth});
  };

  switch (params_.select_mode) {
    case SelectMode::Active:
      add_object(params_.object);
      break;
    case SelectMode::Selected:
      LISTBASE_FOREACH (Base *, base, BKE_view_layer_object_bases_get(view_layer)) {
        if (base->flag & BASE_SELECTED) {
          add_object(base->object);
        }
      }
      break;
    case SelectMode::Visible:
      LISTBASE_FOREACH (Base *, base, BKE_view_layer_object_bases_get(view_layer)) {
        add_object(base->object);
      }
      break;
  }

  /* Sort list of objects from point of view. */
  std::sort(objects.begin(), objects.end(), [](const ObjectInfo &info1, const ObjectInfo &info2) {
    return info1.depth < info2.depth;
  });

  return objects;
}

void GreasePencilExporter::foreach_stroke_in_layer(const Object &object,
                                                   const bke::greasepencil::Layer &layer,
                                                   const bke::greasepencil::Drawing &drawing,
                                                   WriteStrokeFn stroke_fn)
{
  using bke::greasepencil::Drawing;

  const float4x4 layer_to_world = layer.to_world_space(object);
  const float4x4 viewmat = float4x4(context_.rv3d->viewmat);
  const float4x4 layer_to_view = viewmat * layer_to_world;

  const bke::CurvesGeometry &curves = drawing.strokes();
  const bke::AttributeAccessor attributes = curves.attributes();
  /* Curve attributes. */
  const OffsetIndices points_by_curve = curves.points_by_curve();
  const VArray<bool> cyclic = curves.cyclic();
  const VArraySpan<int> material_indices = *attributes.lookup_or_default<int>(
      "material_index", bke::AttrDomain::Curve, 0);
  const VArraySpan<ColorGeometry4f> fill_colors = drawing.fill_colors();
  const VArray<int8_t> start_caps = *attributes.lookup_or_default<int8_t>(
      "start_cap", bke::AttrDomain::Curve, GP_STROKE_CAP_TYPE_ROUND);
  const VArray<int8_t> end_caps = *attributes.lookup_or_default<int8_t>(
      "end_cap", bke::AttrDomain::Curve, 0);
  /* Point attributes. */
  const Span<float3> positions = curves.positions();
  const VArraySpan<float> radii = drawing.radii();
  const VArraySpan<float> opacities = drawing.opacities();
  const VArraySpan<ColorGeometry4f> vertex_colors = drawing.vertex_colors();

  Array<float3> world_positions(positions.size());
  threading::parallel_for(positions.index_range(), 4096, [&](const IndexRange range) {
    for (const int i : range) {
      world_positions[i] = math::transform_point(layer_to_world, positions[i]);
    }
  });

  for (const int i_curve : curves.curves_range()) {
    const IndexRange points = points_by_curve[i_curve];
    if (points.size() < 2) {
      continue;
    }

    const bool is_cyclic = cyclic[i_curve];
    const int material_index = material_indices[i_curve];
    const Material *material = BKE_object_material_get(const_cast<Object *>(&object),
                                                       material_index + 1);
    BLI_assert(material->gp_style != nullptr);
    if (material->gp_style->flag & GP_MATERIAL_HIDE) {
      continue;
    }
    const bool is_stroke_material = material->gp_style->flag & GP_MATERIAL_STROKE_SHOW;
    const bool is_fill_material = material->gp_style->flag & GP_MATERIAL_FILL_SHOW;

    /* Fill. */
    if (is_fill_material && params_.export_fill_materials) {
      const ColorGeometry4f material_fill_color = ColorGeometry4f(material->gp_style->fill_rgba);
      const ColorGeometry4f fill_color = math::interpolate(
          material_fill_color, fill_colors[i_curve], fill_colors[i_curve].a);
      stroke_fn(positions.slice(points),
                is_cyclic,
                fill_color,
                layer.opacity,
                std::nullopt,
                false,
                false);
    }

    /* Stroke. */
    if (is_stroke_material && params_.export_stroke_materials) {
      const ColorGeometry4f stroke_color = compute_average_stroke_color(
          *material, vertex_colors.slice(points));
      const float stroke_opacity = compute_average_stroke_opacity(opacities.slice(points)) *
                                   layer.opacity;
      const std::optional<float> uniform_width = params_.use_uniform_width ?
                                                     try_get_uniform_point_width(
                                                         *context_.rv3d,
                                                         world_positions.as_span().slice(points),
                                                         radii.slice(points)) :
                                                     std::nullopt;
      if (uniform_width) {
        const GreasePencilStrokeCapType start_cap = GreasePencilStrokeCapType(start_caps[i_curve]);
        const GreasePencilStrokeCapType end_cap = GreasePencilStrokeCapType(end_caps[i_curve]);
        const bool round_cap = start_cap == GP_STROKE_CAP_TYPE_ROUND ||
                               end_cap == GP_STROKE_CAP_TYPE_ROUND;

        stroke_fn(positions.slice(points),
                  is_cyclic,
                  stroke_color,
                  stroke_opacity,
                  uniform_width,
                  round_cap,
                  false);
      }
      else {
        const IndexMask single_curve_mask = IndexRange::from_single(i_curve);

        constexpr int corner_subdivisions = 3;
        constexpr float outline_radius = 0.0f;
        constexpr float outline_offset = 0.0f;
        bke::CurvesGeometry outline = ed::greasepencil::create_curves_outline(drawing,
                                                                              single_curve_mask,
                                                                              layer_to_view,
                                                                              corner_subdivisions,
                                                                              outline_radius,
                                                                              outline_offset,
                                                                              material_index);

        /* Sample the outline stroke. */
        if (params_.outline_resample_length > 0.0f) {
          VArray<float> resample_lengths = VArray<float>::ForSingle(
              params_.outline_resample_length, curves.curves_num());
          outline = geometry::resample_to_length(outline, single_curve_mask, resample_lengths);
        }

        const OffsetIndices outline_points_by_curve = outline.points_by_curve();
        const Span<float3> outline_positions = outline.positions();

        for (const int i_outline_curve : outline.curves_range()) {
          const IndexRange outline_points = outline_points_by_curve[i_outline_curve];
          /* Use stroke color to fill the outline. */
          stroke_fn(outline_positions.slice(outline_points),
                    true,
                    stroke_color,
                    stroke_opacity,
                    std::nullopt,
                    false,
                    true);
        }
      }
    }
  }
}

float2 GreasePencilExporter::project_to_screen(const float4x4 &transform,
                                               const float3 &position) const
{
  const float3 world_pos = math::transform_point(transform, position);

  if (camera_persmat_) {
    /* Use camera render space. */
    return (float2(math::project_point(*camera_persmat_, world_pos)) + 1.0f) / 2.0f *
           float2(render_rect_.size());
  }

  /* Use 3D view screen space. */
  float2 screen_co;
  if (ED_view3d_project_float_global(context_.region, world_pos, screen_co, V3D_PROJ_TEST_NOP) ==
      V3D_PROJ_RET_OK)
  {
    if (!ELEM(V2D_IS_CLIPPED, screen_co.x, screen_co.y)) {
      /* Apply offset and scale. */
      return screen_co - render_rect_.min;
    }
  }

  return float2(V2D_IS_CLIPPED);
}

}  // namespace blender::io::grease_pencil
