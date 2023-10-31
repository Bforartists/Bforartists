/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_attribute_math.hh"
#include "BKE_mesh.hh"
#include "BKE_mesh_sample.hh"
#include "BKE_type_conversions.hh"

#include "NOD_rna_define.hh"
#include "NOD_socket_search_link.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "GEO_reverse_uv_sampler.hh"

#include "RNA_enum_types.hh"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_sample_uv_surface_cc {

using geometry::ReverseUVSampler;

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>("Mesh").supported_type(GeometryComponent::Type::Mesh);

  b.add_input<decl::Float>("Value", "Value_Float").hide_value().field_on_all();
  b.add_input<decl::Int>("Value", "Value_Int").hide_value().field_on_all();
  b.add_input<decl::Vector>("Value", "Value_Vector").hide_value().field_on_all();
  b.add_input<decl::Color>("Value", "Value_Color").hide_value().field_on_all();
  b.add_input<decl::Bool>("Value", "Value_Bool").hide_value().field_on_all();
  b.add_input<decl::Rotation>("Value", "Value_Rotation").hide_value().field_on_all();

  b.add_input<decl::Vector>("Source UV Map")
      .hide_value()
      .field_on_all()
      .description("The mesh UV map to sample. Should not have overlapping faces");
  b.add_input<decl::Vector>("Sample UV")
      .supports_field()
      .description("The coordinates to sample within the UV map");

  b.add_output<decl::Float>("Value", "Value_Float").dependent_field({8});
  b.add_output<decl::Int>("Value", "Value_Int").dependent_field({8});
  b.add_output<decl::Vector>("Value", "Value_Vector").dependent_field({8});
  b.add_output<decl::Color>("Value", "Value_Color").dependent_field({8});
  b.add_output<decl::Bool>("Value", "Value_Bool").dependent_field({8});
  b.add_output<decl::Rotation>("Value", "Value_Rotation").dependent_field({8});

  b.add_output<decl::Bool>("Is Valid")
      .dependent_field({8})
      .description("Whether the node could find a single face to sample at the UV coordinate");
}

static void node_layout(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiItemR(layout, ptr, "data_type", UI_ITEM_NONE, "", ICON_NONE);
}

static void node_init(bNodeTree * /*tree*/, bNode *node)
{
  node->custom1 = CD_PROP_FLOAT;
}

static void node_update(bNodeTree *ntree, bNode *node)
{
  const eCustomDataType data_type = eCustomDataType(node->custom1);

  bNodeSocket *in_socket_mesh = static_cast<bNodeSocket *>(node->inputs.first);
  bNodeSocket *in_socket_float = in_socket_mesh->next;
  bNodeSocket *in_socket_int32 = in_socket_float->next;
  bNodeSocket *in_socket_vector = in_socket_int32->next;
  bNodeSocket *in_socket_color4f = in_socket_vector->next;
  bNodeSocket *in_socket_bool = in_socket_color4f->next;
  bNodeSocket *in_socket_quat = in_socket_bool->next;

  bke::nodeSetSocketAvailability(ntree, in_socket_vector, data_type == CD_PROP_FLOAT3);
  bke::nodeSetSocketAvailability(ntree, in_socket_float, data_type == CD_PROP_FLOAT);
  bke::nodeSetSocketAvailability(ntree, in_socket_color4f, data_type == CD_PROP_COLOR);
  bke::nodeSetSocketAvailability(ntree, in_socket_bool, data_type == CD_PROP_BOOL);
  bke::nodeSetSocketAvailability(ntree, in_socket_int32, data_type == CD_PROP_INT32);
  bke::nodeSetSocketAvailability(ntree, in_socket_quat, data_type == CD_PROP_QUATERNION);

  bNodeSocket *out_socket_float = static_cast<bNodeSocket *>(node->outputs.first);
  bNodeSocket *out_socket_int32 = out_socket_float->next;
  bNodeSocket *out_socket_vector = out_socket_int32->next;
  bNodeSocket *out_socket_color4f = out_socket_vector->next;
  bNodeSocket *out_socket_bool = out_socket_color4f->next;
  bNodeSocket *out_socket_quat = out_socket_bool->next;

  bke::nodeSetSocketAvailability(ntree, out_socket_vector, data_type == CD_PROP_FLOAT3);
  bke::nodeSetSocketAvailability(ntree, out_socket_float, data_type == CD_PROP_FLOAT);
  bke::nodeSetSocketAvailability(ntree, out_socket_color4f, data_type == CD_PROP_COLOR);
  bke::nodeSetSocketAvailability(ntree, out_socket_bool, data_type == CD_PROP_BOOL);
  bke::nodeSetSocketAvailability(ntree, out_socket_int32, data_type == CD_PROP_INT32);
  bke::nodeSetSocketAvailability(ntree, out_socket_quat, data_type == CD_PROP_QUATERNION);
}

static void node_gather_link_searches(GatherLinkSearchOpParams &params)
{
  const NodeDeclaration &declaration = *params.node_type().static_declaration;
  search_link_ops_for_declarations(params, declaration.inputs.as_span().take_back(2));
  search_link_ops_for_declarations(params, declaration.inputs.as_span().take_front(1));
  search_link_ops_for_declarations(params, declaration.outputs.as_span().take_back(1));

  const std::optional<eCustomDataType> type = bke::socket_type_to_custom_data_type(
      eNodeSocketDatatype(params.other_socket().type));
  if (type && *type != CD_PROP_STRING) {
    /* The input and output sockets have the same name. */
    params.add_item(IFACE_("Value"), [type](LinkSearchOpParams &params) {
      bNode &node = params.add_node("GeometryNodeSampleUVSurface");
      node.custom1 = *type;
      params.update_and_connect_available_socket(node, "Value");
    });
  }
}

class ReverseUVSampleFunction : public mf::MultiFunction {
  GeometrySet source_;
  Field<float2> src_uv_map_field_;

  std::optional<bke::MeshFieldContext> source_context_;
  std::unique_ptr<FieldEvaluator> source_evaluator_;
  VArraySpan<float2> source_uv_map_;

  std::optional<ReverseUVSampler> reverse_uv_sampler_;

 public:
  ReverseUVSampleFunction(GeometrySet geometry, Field<float2> src_uv_map_field)
      : source_(std::move(geometry)), src_uv_map_field_(std::move(src_uv_map_field))
  {
    source_.ensure_owns_direct_data();
    this->evaluate_source();

    static const mf::Signature signature = []() {
      mf::Signature signature;
      mf::SignatureBuilder builder{"Sample UV Surface", signature};
      builder.single_input<float2>("Sample UV");
      builder.single_output<bool>("Is Valid", mf::ParamFlag::SupportsUnusedOutput);
      builder.single_output<int>("Triangle Index", mf::ParamFlag::SupportsUnusedOutput);
      builder.single_output<float3>("Barycentric Weights", mf::ParamFlag::SupportsUnusedOutput);
      return signature;
    }();
    this->set_signature(&signature);
  }

  void call(const IndexMask &mask, mf::Params params, mf::Context /*context*/) const override
  {
    const VArraySpan<float2> sample_uvs = params.readonly_single_input<float2>(0, "Sample UV");
    MutableSpan<bool> is_valid = params.uninitialized_single_output_if_required<bool>(1,
                                                                                      "Is Valid");
    MutableSpan<int> tri_index = params.uninitialized_single_output_if_required<int>(
        2, "Triangle Index");
    MutableSpan<float3> bary_weights = params.uninitialized_single_output_if_required<float3>(
        3, "Barycentric Weights");

    mask.foreach_index([&](const int i) {
      const ReverseUVSampler::Result result = reverse_uv_sampler_->sample(sample_uvs[i]);
      if (!is_valid.is_empty()) {
        is_valid[i] = result.type == ReverseUVSampler::ResultType::Ok;
      }
      if (!tri_index.is_empty()) {
        tri_index[i] = result.looptri_index;
      }
      if (!bary_weights.is_empty()) {
        bary_weights[i] = result.bary_weights;
      }
    });
  }

 private:
  void evaluate_source()
  {
    const Mesh &mesh = *source_.get_mesh();
    source_context_.emplace(bke::MeshFieldContext{mesh, ATTR_DOMAIN_CORNER});
    source_evaluator_ = std::make_unique<FieldEvaluator>(*source_context_, mesh.totloop);
    source_evaluator_->add(src_uv_map_field_);
    source_evaluator_->evaluate();
    source_uv_map_ = source_evaluator_->get_evaluated<float2>(0);

    reverse_uv_sampler_.emplace(source_uv_map_, mesh.looptris());
  }
};

static GField get_input_attribute_field(GeoNodeExecParams &params, const eCustomDataType data_type)
{
  switch (data_type) {
    case CD_PROP_FLOAT:
      return params.extract_input<GField>("Value_Float");
    case CD_PROP_FLOAT3:
      return params.extract_input<GField>("Value_Vector");
    case CD_PROP_COLOR:
      return params.extract_input<GField>("Value_Color");
    case CD_PROP_BOOL:
      return params.extract_input<GField>("Value_Bool");
    case CD_PROP_INT32:
      return params.extract_input<GField>("Value_Int");
    case CD_PROP_QUATERNION:
      return params.extract_input<GField>("Value_Rotation");
    default:
      BLI_assert_unreachable();
  }
  return {};
}

static void output_attribute_field(GeoNodeExecParams &params, GField field)
{
  switch (bke::cpp_type_to_custom_data_type(field.cpp_type())) {
    case CD_PROP_FLOAT: {
      params.set_output("Value_Float", field);
      break;
    }
    case CD_PROP_FLOAT3: {
      params.set_output("Value_Vector", field);
      break;
    }
    case CD_PROP_COLOR: {
      params.set_output("Value_Color", field);
      break;
    }
    case CD_PROP_BOOL: {
      params.set_output("Value_Bool", field);
      break;
    }
    case CD_PROP_INT32: {
      params.set_output("Value_Int", field);
      break;
    }
    case CD_PROP_QUATERNION: {
      params.set_output("Value_Rotation", field);
      break;
    }
    default:
      break;
  }
}

static void node_geo_exec(GeoNodeExecParams params)
{
  GeometrySet geometry = params.extract_input<GeometrySet>("Mesh");
  const eCustomDataType data_type = eCustomDataType(params.node().custom1);
  const Mesh *mesh = geometry.get_mesh();
  if (mesh == nullptr) {
    params.set_default_remaining_outputs();
    return;
  }
  if (mesh->faces_num == 0 && mesh->totvert != 0) {
    params.error_message_add(NodeWarningType::Error, TIP_("The source mesh must have faces"));
    params.set_default_remaining_outputs();
    return;
  }

  /* Do reverse sampling of the UV map first. */
  const bke::DataTypeConversions &conversions = bke::get_implicit_type_conversions();
  const CPPType &float2_type = CPPType::get<float2>();
  Field<float2> source_uv_map = conversions.try_convert(
      params.extract_input<Field<float3>>("Source UV Map"), float2_type);
  Field<float2> sample_uvs = conversions.try_convert(
      params.extract_input<Field<float3>>("Sample UV"), float2_type);
  auto uv_op = FieldOperation::Create(
      std::make_shared<ReverseUVSampleFunction>(geometry, std::move(source_uv_map)),
      {std::move(sample_uvs)});
  params.set_output("Is Valid", Field<bool>(uv_op, 0));

  /* Use the output of the UV sampling to interpolate the mesh attribute. */
  GField field = get_input_attribute_field(params, data_type);
  auto sample_op = FieldOperation::Create(
      std::make_shared<bke::mesh_surface_sample::BaryWeightSampleFn>(std::move(geometry),
                                                                     std::move(field)),
      {Field<int>(uv_op, 1), Field<float3>(uv_op, 2)});
  output_attribute_field(params, GField(sample_op, 0));
}

static void node_rna(StructRNA *srna)
{
  RNA_def_node_enum(srna,
                    "data_type",
                    "Data Type",
                    "",
                    rna_enum_attribute_type_items,
                    NOD_inline_enum_accessors(custom1),
                    CD_PROP_FLOAT,
                    enums::attribute_type_type_with_socket_fn);
}

static void node_register()
{
  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_SAMPLE_UV_SURFACE, "Sample UV Surface", NODE_CLASS_GEOMETRY);
  ntype.initfunc = node_init;
  ntype.updatefunc = node_update;
  ntype.declare = node_declare;
  ntype.geometry_node_execute = node_geo_exec;
  ntype.draw_buttons = node_layout;
  ntype.gather_link_search_ops = node_gather_link_searches;
  nodeRegisterType(&ntype);

  node_rna(ntype.rna_ext.srna);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_geo_sample_uv_surface_cc
