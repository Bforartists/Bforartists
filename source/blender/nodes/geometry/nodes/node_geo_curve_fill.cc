/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_array.hh"
#include "BLI_delaunay_2d.h"
#include "BLI_math_vector_types.hh"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"

#include "BKE_curves.hh"
#include "BKE_grease_pencil.hh"
#include "BKE_instances.hh"
#include "BKE_mesh.hh"

#include "BLI_task.hh"

#include "NOD_rna_define.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_curve_fill_cc {

NODE_STORAGE_FUNCS(NodeGeometryCurveFill)

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>("Curve").supported_type(
      {GeometryComponent::Type::Curve, GeometryComponent::Type::GreasePencil});
  b.add_output<decl::Geometry>("Mesh");
}

static void node_layout(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiItemR(layout, ptr, "mode", UI_ITEM_R_EXPAND, nullptr, ICON_NONE);
}

static void node_init(bNodeTree * /*tree*/, bNode *node)
{
  NodeGeometryCurveFill *data = MEM_cnew<NodeGeometryCurveFill>(__func__);

  data->mode = GEO_NODE_CURVE_FILL_MODE_TRIANGULATED;
  node->storage = data;
}

static meshintersect::CDT_result<double> do_cdt(const bke::CurvesGeometry &curves,
                                                const CDT_output_type output_type)
{
  const OffsetIndices points_by_curve = curves.evaluated_points_by_curve();
  const Span<float3> positions = curves.evaluated_positions();

  meshintersect::CDT_input<double> input;
  input.need_ids = false;
  input.vert.reinitialize(points_by_curve.total_size());
  input.face.reinitialize(curves.curves_num());

  for (const int i_curve : curves.curves_range()) {
    const IndexRange points = points_by_curve[i_curve];

    for (const int i : points) {
      input.vert[i] = double2(positions[i].x, positions[i].y);
    }

    input.face[i_curve].resize(points.size());
    MutableSpan<int> face_verts = input.face[i_curve];
    for (const int i : face_verts.index_range()) {
      face_verts[i] = points[i];
    }
  }
  meshintersect::CDT_result<double> result = delaunay_2d_calc(input, output_type);
  return result;
}

/* Converts the CDT result into a Mesh. */
static Mesh *cdt_to_mesh(const meshintersect::CDT_result<double> &result)
{
  const int vert_len = result.vert.size();
  const int edge_len = result.edge.size();
  const int face_len = result.face.size();
  int loop_len = 0;
  for (const Vector<int> &face : result.face) {
    loop_len += face.size();
  }

  Mesh *mesh = BKE_mesh_new_nomain(vert_len, edge_len, face_len, loop_len);
  MutableSpan<float3> positions = mesh->vert_positions_for_write();
  mesh->edges_for_write().copy_from(result.edge.as_span().cast<int2>());
  MutableSpan<int> face_offsets = mesh->face_offsets_for_write();
  MutableSpan<int> corner_verts = mesh->corner_verts_for_write();

  for (const int i : IndexRange(result.vert.size())) {
    positions[i] = float3(float(result.vert[i].x), float(result.vert[i].y), 0.0f);
  }
  int i_loop = 0;
  for (const int i : IndexRange(result.face.size())) {
    face_offsets[i] = i_loop;
    for (const int j : result.face[i].index_range()) {
      corner_verts[i_loop] = result.face[i][j];
      i_loop++;
    }
  }

  /* The delaunay triangulation doesn't seem to return all of the necessary edges, even in
   * triangulation mode. */
  BKE_mesh_calc_edges(mesh, true, false);
  BKE_mesh_smooth_flag_set(mesh, false);
  return mesh;
}

static void curve_fill_calculate(GeometrySet &geometry_set, const GeometryNodeCurveFillMode mode)
{
  const CDT_output_type output_type = (mode == GEO_NODE_CURVE_FILL_MODE_NGONS) ?
                                          CDT_CONSTRAINTS_VALID_BMESH_WITH_HOLES :
                                          CDT_INSIDE_WITH_HOLES;
  if (geometry_set.has_curves()) {
    const Curves &curves_id = *geometry_set.get_curves();
    const bke::CurvesGeometry &curves = curves_id.geometry.wrap();
    if (curves.curves_num() > 0) {
      const meshintersect::CDT_result<double> results = do_cdt(curves, output_type);
      Mesh *mesh = cdt_to_mesh(results);
      geometry_set.replace_mesh(mesh);
    }
    geometry_set.replace_curves(nullptr);
  }

  if (geometry_set.has_grease_pencil()) {
    using namespace blender::bke::greasepencil;
    const GreasePencil &grease_pencil = *geometry_set.get_grease_pencil();
    Vector<Mesh *> mesh_by_layer(grease_pencil.layers().size(), nullptr);
    for (const int layer_index : grease_pencil.layers().index_range()) {
      const Drawing *drawing = get_eval_grease_pencil_layer_drawing(grease_pencil, layer_index);
      if (drawing == nullptr) {
        continue;
      }
      const bke::CurvesGeometry &src_curves = drawing->strokes();
      if (src_curves.curves_num() == 0) {
        continue;
      }
      const meshintersect::CDT_result<double> results = do_cdt(src_curves, output_type);
      mesh_by_layer[layer_index] = cdt_to_mesh(results);
    }
    if (!mesh_by_layer.is_empty()) {
      InstancesComponent &instances_component =
          geometry_set.get_component_for_write<InstancesComponent>();
      bke::Instances *instances = instances_component.get_for_write();
      if (instances == nullptr) {
        instances = new bke::Instances();
        instances_component.replace(instances);
      }
      for (Mesh *mesh : mesh_by_layer) {
        if (!mesh) {
          /* Add an empty reference so the number of layers and instances match.
           * This makes it easy to reconstruct the layers afterwards and keep their attributes.
           * Although in this particular case we don't propagate the attributes. */
          const int handle = instances->add_reference(bke::InstanceReference());
          instances->add_instance(handle, float4x4::identity());
          continue;
        }
        GeometrySet temp_set = GeometrySet::from_mesh(mesh);
        const int handle = instances->add_reference(bke::InstanceReference{temp_set});
        instances->add_instance(handle, float4x4::identity());
      }
    }
    geometry_set.replace_grease_pencil(nullptr);
  }
}

static void node_geo_exec(GeoNodeExecParams params)
{
  GeometrySet geometry_set = params.extract_input<GeometrySet>("Curve");

  const NodeGeometryCurveFill &storage = node_storage(params.node());
  const GeometryNodeCurveFillMode mode = (GeometryNodeCurveFillMode)storage.mode;

  geometry_set.modify_geometry_sets(
      [&](GeometrySet &geometry_set) { curve_fill_calculate(geometry_set, mode); });

  params.set_output("Mesh", std::move(geometry_set));
}

static void node_rna(StructRNA *srna)
{
  static const EnumPropertyItem mode_items[] = {
      {GEO_NODE_CURVE_FILL_MODE_TRIANGULATED, "TRIANGLES", 0, "Triangles", ""},
      {GEO_NODE_CURVE_FILL_MODE_NGONS, "NGONS", 0, "N-gons", ""},
      {0, nullptr, 0, nullptr, nullptr},
  };

  RNA_def_node_enum(srna,
                    "mode",
                    "Mode",
                    "",
                    mode_items,
                    NOD_storage_enum_accessors(mode),
                    GEO_NODE_CURVE_FILL_MODE_TRIANGULATED);
}

static void node_register()
{
  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_FILL_CURVE, "Fill Curve", NODE_CLASS_GEOMETRY);

  ntype.initfunc = node_init;
  node_type_storage(
      &ntype, "NodeGeometryCurveFill", node_free_standard_storage, node_copy_standard_storage);
  ntype.declare = node_declare;
  ntype.geometry_node_execute = node_geo_exec;
  ntype.draw_buttons = node_layout;
  nodeRegisterType(&ntype);

  node_rna(ntype.rna_ext.srna);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_geo_curve_fill_cc
