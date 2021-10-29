/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 */

#include "BLI_task.hh"

#include "node_geometry_util.hh"

namespace blender::nodes {

static void geo_node_scale_instances_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>(N_("Instances")).only_instances();
  b.add_input<decl::Bool>(N_("Selection")).default_value(true).hide_value().supports_field();
  b.add_input<decl::Vector>(N_("Scale"))
      .subtype(PROP_XYZ)
      .default_value({1, 1, 1})
      .supports_field();
  b.add_input<decl::Vector>(N_("Center")).subtype(PROP_TRANSLATION).supports_field();
  b.add_input<decl::Bool>(N_("Local Space")).default_value(true).supports_field();
  b.add_output<decl::Geometry>(N_("Instances"));
};

static void scale_instances(GeoNodeExecParams &params, InstancesComponent &instances_component)
{
  GeometryComponentFieldContext field_context{instances_component, ATTR_DOMAIN_POINT};

  fn::FieldEvaluator selection_evaluator{field_context, instances_component.instances_amount()};
  selection_evaluator.add(params.extract_input<Field<bool>>("Selection"));
  selection_evaluator.evaluate();
  const IndexMask selection = selection_evaluator.get_evaluated_as_mask(0);

  fn::FieldEvaluator transforms_evaluator{field_context, &selection};
  transforms_evaluator.add(params.extract_input<Field<float3>>("Scale"));
  transforms_evaluator.add(params.extract_input<Field<float3>>("Center"));
  transforms_evaluator.add(params.extract_input<Field<bool>>("Local Space"));
  transforms_evaluator.evaluate();
  const VArray<float3> &scales = transforms_evaluator.get_evaluated<float3>(0);
  const VArray<float3> &pivots = transforms_evaluator.get_evaluated<float3>(1);
  const VArray<bool> &local_spaces = transforms_evaluator.get_evaluated<bool>(2);

  MutableSpan<float4x4> instance_transforms = instances_component.instance_transforms();

  threading::parallel_for(selection.index_range(), 512, [&](IndexRange range) {
    for (const int i_selection : range) {
      const int i = selection[i_selection];
      const float3 pivot = pivots[i];
      float4x4 &instance_transform = instance_transforms[i];

      if (local_spaces[i]) {
        instance_transform *= float4x4::from_location(pivot);
        rescale_m4(instance_transform.values, scales[i]);
        instance_transform *= float4x4::from_location(-pivot);
      }
      else {
        const float4x4 original_transform = instance_transform;
        instance_transform = float4x4::from_location(pivot);
        rescale_m4(instance_transform.values, scales[i]);
        instance_transform *= float4x4::from_location(-pivot);
        instance_transform *= original_transform;
      }
    }
  });
}

static void geo_node_scale_instances_exec(GeoNodeExecParams params)
{
  GeometrySet geometry_set = params.extract_input<GeometrySet>("Instances");
  if (geometry_set.has_instances()) {
    InstancesComponent &instances = geometry_set.get_component_for_write<InstancesComponent>();
    scale_instances(params, instances);
  }
  params.set_output("Instances", std::move(geometry_set));
}

}  // namespace blender::nodes

void register_node_type_geo_scale_instances()
{
  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_SCALE_INSTANCES, "Scale Instances", NODE_CLASS_GEOMETRY, 0);
  ntype.geometry_node_execute = blender::nodes::geo_node_scale_instances_exec;
  ntype.declare = blender::nodes::geo_node_scale_instances_declare;
  nodeRegisterType(&ntype);
}
