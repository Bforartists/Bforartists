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

#include "DEG_depsgraph_query.h"

#include "node_geometry_util.hh"

namespace blender::nodes {

static void geo_node_set_position_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>("Geometry");
  b.add_input<decl::Vector>("Position");
  b.add_input<decl::Bool>("Selection").default_value(true);
  b.add_output<decl::Geometry>("Geometry");
}

static void set_position_in_component(GeometryComponent &component,
                                      const Field<bool> &selection_field,
                                      const Field<float3> &position_field)
{
  GeometryComponentFieldContext field_context{component, ATTR_DOMAIN_POINT};
  const int domain_size = component.attribute_domain_size(ATTR_DOMAIN_POINT);

  fn::FieldEvaluator selection_evaluator{field_context, domain_size};
  selection_evaluator.add(selection_field);
  selection_evaluator.evaluate();
  const IndexMask selection = selection_evaluator.get_evaluated_as_mask(0);

  OutputAttribute_Typed<float3> positions = component.attribute_try_get_for_output<float3>(
      "position", ATTR_DOMAIN_POINT, {0, 0, 0});
  fn::FieldEvaluator position_evaluator{field_context, &selection};
  position_evaluator.add_with_destination(position_field, positions.varray());
  position_evaluator.evaluate();
  positions.save();
}

static void geo_node_set_position_exec(GeoNodeExecParams params)
{
  GeometrySet geometry = params.extract_input<GeometrySet>("Geometry");
  geometry = geometry_set_realize_instances(geometry);
  Field<bool> selection_field = params.extract_input<Field<bool>>("Selection");
  Field<float3> position_field = params.extract_input<Field<float3>>("Position");

  for (const GeometryComponentType type :
       {GEO_COMPONENT_TYPE_MESH, GEO_COMPONENT_TYPE_POINT_CLOUD, GEO_COMPONENT_TYPE_CURVE}) {
    if (geometry.has(type)) {
      set_position_in_component(
          geometry.get_component_for_write(type), selection_field, position_field);
    }
  }

  params.set_output("Geometry", std::move(geometry));
}

}  // namespace blender::nodes

void register_node_type_geo_set_position()
{
  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_SET_POSITION, "Set Position", NODE_CLASS_GEOMETRY, 0);
  ntype.geometry_node_execute = blender::nodes::geo_node_set_position_exec;
  ntype.declare = blender::nodes::geo_node_set_position_declare;
  nodeRegisterType(&ntype);
}
