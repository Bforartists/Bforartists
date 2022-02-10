/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_task.hh"
#include "BLI_timeit.hh"

#include "BKE_pointcloud.h"
#include "BKE_spline.hh"

#include "UI_interface.h"
#include "UI_resources.h"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_legacy_curve_endpoints_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>(N_("Geometry"));
  b.add_output<decl::Geometry>(N_("Start Points"));
  b.add_output<decl::Geometry>(N_("End Points"));
}

/**
 * Evaluate splines in parallel to speed up the rest of the node's execution.
 */
static void evaluate_splines(Span<SplinePtr> splines)
{
  threading::parallel_for_each(splines, [](const SplinePtr &spline) {
    /* These functions fill the corresponding caches on each spline. */
    spline->evaluated_positions();
    spline->evaluated_tangents();
    spline->evaluated_normals();
    spline->evaluated_lengths();
  });
}

/**
 * \note Use attributes from the curve component rather than the attribute data directly on the
 * attribute storage to allow reading the virtual spline attributes like "cyclic" and "resolution".
 */
static void copy_spline_domain_attributes(const CurveComponent &curve_component,
                                          Span<int> offsets,
                                          PointCloudComponent &points)
{
  curve_component.attribute_foreach(
      [&](const AttributeIDRef &attribute_id, const AttributeMetaData &meta_data) {
        if (meta_data.domain != ATTR_DOMAIN_CURVE) {
          return true;
        }
        GVArray spline_attribute = curve_component.attribute_get_for_read(
            attribute_id, ATTR_DOMAIN_CURVE, meta_data.data_type);

        OutputAttribute result_attribute = points.attribute_try_get_for_output_only(
            attribute_id, ATTR_DOMAIN_POINT, meta_data.data_type);
        GMutableSpan result = result_attribute.as_span();

        /* Only copy the attributes of splines in the offsets. */
        for (const int i : offsets.index_range()) {
          spline_attribute.get(offsets[i], result[i]);
        }

        result_attribute.save();
        return true;
      });
}

/**
 * Get the offsets for the splines whose endpoints we want to output.
 * Filter those which are cyclic, or that evaluate to empty.
 * Could be easily adapted to include a selection argument to support attribute selection.
 */
static blender::Vector<int> get_endpoint_spline_offsets(Span<SplinePtr> splines)
{
  blender::Vector<int> spline_offsets;
  spline_offsets.reserve(splines.size());

  for (const int i : splines.index_range()) {
    if (!(splines[i]->is_cyclic() || splines[i]->evaluated_points_size() == 0)) {
      spline_offsets.append(i);
    }
  }

  return spline_offsets;
}

/**
 * Copy the endpoint attributes from the correct positions at the splines at the offsets to
 * the start and end attributes.
 */
static void copy_endpoint_attributes(Span<SplinePtr> splines,
                                     Span<int> offsets,
                                     CurveToPointsResults &start_data,
                                     CurveToPointsResults &end_data)
{
  threading::parallel_for(offsets.index_range(), 64, [&](IndexRange range) {
    for (const int i : range) {
      const Spline &spline = *splines[offsets[i]];

      /* Copy the start and end point data over. */
      start_data.positions[i] = spline.evaluated_positions().first();
      start_data.tangents[i] = spline.evaluated_tangents().first();
      start_data.normals[i] = spline.evaluated_normals().first();
      start_data.radii[i] = spline.radii().first();
      start_data.tilts[i] = spline.tilts().first();

      end_data.positions[i] = spline.evaluated_positions().last();
      end_data.tangents[i] = spline.evaluated_tangents().last();
      end_data.normals[i] = spline.evaluated_normals().last();
      end_data.radii[i] = spline.radii().last();
      end_data.tilts[i] = spline.tilts().last();

      /* Copy the point attribute data over. */
      for (const auto item : start_data.point_attributes.items()) {
        const AttributeIDRef attribute_id = item.key;
        GMutableSpan point_span = item.value;

        BLI_assert(spline.attributes.get_for_read(attribute_id));
        GSpan spline_span = *spline.attributes.get_for_read(attribute_id);
        spline_span.type().copy_assign(spline_span[0], point_span[i]);
      }

      for (const auto item : end_data.point_attributes.items()) {
        const AttributeIDRef attribute_id = item.key;
        GMutableSpan point_span = item.value;

        BLI_assert(spline.attributes.get_for_read(attribute_id));
        GSpan spline_span = *spline.attributes.get_for_read(attribute_id);
        spline_span.type().copy_assign(spline_span[spline.size() - 1], point_span[i]);
      }
    }
  });
}

static void node_geo_exec(GeoNodeExecParams params)
{
  GeometrySet geometry_set = params.extract_input<GeometrySet>("Geometry");

  geometry_set = geometry::realize_instances_legacy(geometry_set);

  if (!geometry_set.has_curve()) {
    params.set_default_remaining_outputs();
    return;
  }

  const CurveComponent &curve_component = *geometry_set.get_component_for_read<CurveComponent>();
  const CurveEval &curve = *curve_component.get_for_read();
  const Span<SplinePtr> splines = curve.splines();
  curve.assert_valid_point_attributes();

  evaluate_splines(splines);

  const Vector<int> offsets = get_endpoint_spline_offsets(splines);
  const int total_size = offsets.size();

  if (total_size == 0) {
    params.set_default_remaining_outputs();
    return;
  }

  GeometrySet start_result = GeometrySet::create_with_pointcloud(
      BKE_pointcloud_new_nomain(total_size));
  GeometrySet end_result = GeometrySet::create_with_pointcloud(
      BKE_pointcloud_new_nomain(total_size));
  PointCloudComponent &start_point_component =
      start_result.get_component_for_write<PointCloudComponent>();
  PointCloudComponent &end_point_component =
      end_result.get_component_for_write<PointCloudComponent>();

  CurveToPointsResults start_attributes = curve_to_points_create_result_attributes(
      start_point_component, curve);
  CurveToPointsResults end_attributes = curve_to_points_create_result_attributes(
      end_point_component, curve);

  copy_endpoint_attributes(splines, offsets.as_span(), start_attributes, end_attributes);
  copy_spline_domain_attributes(curve_component, offsets.as_span(), start_point_component);
  curve_create_default_rotation_attribute(
      start_attributes.tangents, start_attributes.normals, start_attributes.rotations);
  curve_create_default_rotation_attribute(
      end_attributes.tangents, end_attributes.normals, end_attributes.rotations);

  /* The default radius is way too large for points, divide by 10. */
  for (float &radius : start_attributes.radii) {
    radius *= 0.1f;
  }
  for (float &radius : end_attributes.radii) {
    radius *= 0.1f;
  }

  params.set_output("Start Points", std::move(start_result));
  params.set_output("End Points", std::move(end_result));
}

}  // namespace blender::nodes::node_geo_legacy_curve_endpoints_cc

void register_node_type_geo_legacy_curve_endpoints()
{
  namespace file_ns = blender::nodes::node_geo_legacy_curve_endpoints_cc;

  static bNodeType ntype;

  geo_node_type_base(
      &ntype, GEO_NODE_LEGACY_CURVE_ENDPOINTS, "Curve Endpoints", NODE_CLASS_GEOMETRY);
  ntype.declare = file_ns::node_declare;
  ntype.geometry_node_execute = file_ns::node_geo_exec;

  nodeRegisterType(&ntype);
}
