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

#include "BKE_spline.hh"
#include "node_geometry_util.hh"

static bNodeSocketTemplate geo_node_curve_length_in[] = {
    {SOCK_GEOMETRY, N_("Curve")},
    {-1, ""},
};

static bNodeSocketTemplate geo_node_curve_length_out[] = {
    {SOCK_FLOAT, N_("Length")},
    {-1, ""},
};

namespace blender::nodes {

static void geo_node_curve_length_exec(GeoNodeExecParams params)
{
  GeometrySet curve_set = params.extract_input<GeometrySet>("Curve");
  curve_set = bke::geometry_set_realize_instances(curve_set);
  if (!curve_set.has_curve()) {
    params.set_output("Length", 0.0f);
    return;
  }
  const CurveEval &curve = *curve_set.get_curve_for_read();
  float length = 0.0f;
  for (const SplinePtr &spline : curve.splines()) {
    length += spline->length();
  }
  params.set_output("Length", length);
}

}  // namespace blender::nodes

void register_node_type_geo_curve_length()
{
  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_CURVE_LENGTH, "Curve Length", NODE_CLASS_GEOMETRY, 0);
  node_type_socket_templates(&ntype, geo_node_curve_length_in, geo_node_curve_length_out);
  ntype.geometry_node_execute = blender::nodes::geo_node_curve_length_exec;
  nodeRegisterType(&ntype);
}
