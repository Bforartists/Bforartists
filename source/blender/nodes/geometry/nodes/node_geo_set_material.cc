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

#include "node_geometry_util.hh"

#include "UI_interface.h"
#include "UI_resources.h"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_volume_types.h"

#include "BKE_material.h"

namespace blender::nodes {

static void geo_node_set_material_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>(N_("Geometry"))
      .supported_type({GEO_COMPONENT_TYPE_MESH, GEO_COMPONENT_TYPE_VOLUME});
  b.add_input<decl::Bool>(N_("Selection")).default_value(true).hide_value().supports_field();
  b.add_input<decl::Material>(N_("Material")).hide_label();
  b.add_output<decl::Geometry>(N_("Geometry"));
}

static void assign_material_to_faces(Mesh &mesh, const IndexMask selection, Material *material)
{
  int new_material_index = -1;
  for (const int i : IndexRange(mesh.totcol)) {
    Material *other_material = mesh.mat[i];
    if (other_material == material) {
      new_material_index = i;
      break;
    }
  }
  if (new_material_index == -1) {
    /* Append a new material index. */
    new_material_index = mesh.totcol;
    BKE_id_material_eval_assign(&mesh.id, new_material_index + 1, material);
  }

  mesh.mpoly = (MPoly *)CustomData_duplicate_referenced_layer(&mesh.pdata, CD_MPOLY, mesh.totpoly);
  for (const int i : selection) {
    MPoly &poly = mesh.mpoly[i];
    poly.mat_nr = new_material_index;
  }
}

static void geo_node_set_material_exec(GeoNodeExecParams params)
{
  Material *material = params.extract_input<Material *>("Material");
  const Field<bool> selection_field = params.extract_input<Field<bool>>("Selection");

  GeometrySet geometry_set = params.extract_input<GeometrySet>("Geometry");

  bool volume_selection_warning = false;
  geometry_set.modify_geometry_sets([&](GeometrySet &geometry_set) {
    if (geometry_set.has<MeshComponent>()) {
      MeshComponent &mesh_component = geometry_set.get_component_for_write<MeshComponent>();
      Mesh *mesh = mesh_component.get_for_write();
      if (mesh != nullptr) {
        GeometryComponentFieldContext field_context{mesh_component, ATTR_DOMAIN_FACE};

        fn::FieldEvaluator selection_evaluator{field_context, mesh->totpoly};
        selection_evaluator.add(selection_field);
        selection_evaluator.evaluate();
        const IndexMask selection = selection_evaluator.get_evaluated_as_mask(0);

        assign_material_to_faces(*mesh, selection, material);
      }
    }
    if (geometry_set.has_volume()) {
      Volume &volume = *geometry_set.get_volume_for_write();

      if (selection_field.node().depends_on_input()) {
        volume_selection_warning = true;
      }

      BKE_id_material_eval_assign(&volume.id, 1, material);
    }
  });

  if (volume_selection_warning) {
    /* Only add the warning once, even if there are many unique volume instances. */
    params.error_message_add(
        NodeWarningType::Info,
        TIP_("Volumes only support a single material; selection input can not be a field"));
  }

  params.set_output("Geometry", std::move(geometry_set));
}

}  // namespace blender::nodes

void register_node_type_geo_set_material()
{
  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_SET_MATERIAL, "Set Material", NODE_CLASS_GEOMETRY, 0);
  ntype.declare = blender::nodes::geo_node_set_material_declare;
  ntype.geometry_node_execute = blender::nodes::geo_node_set_material_exec;
  nodeRegisterType(&ntype);
}
