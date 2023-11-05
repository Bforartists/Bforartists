/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edcurves
 */

#include "BLI_path_util.h"
#include "BLI_string.h"

#include "ED_curves.hh"
#include "ED_object.hh"
#include "ED_screen.hh"
#include "ED_select_utils.hh"
#include "ED_view3d.hh"

#include "WM_api.hh"

#include "BKE_asset.h"
#include "BKE_attribute_math.hh"
#include "BKE_compute_contexts.hh"
#include "BKE_context.h"
#include "BKE_curves.hh"
#include "BKE_editmesh.h"
#include "BKE_geometry_set.hh"
#include "BKE_layer.h"
#include "BKE_lib_id.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_mesh.hh"
#include "BKE_mesh_wrapper.hh"
#include "BKE_node_runtime.hh"
#include "BKE_object.hh"
#include "BKE_pointcloud.h"
#include "BKE_report.h"
#include "BKE_screen.hh"

#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "DEG_depsgraph.hh"
#include "DEG_depsgraph_build.hh"
#include "DEG_depsgraph_query.hh"

#include "RNA_access.hh"
#include "RNA_define.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "ED_asset.hh"
#include "ED_asset_menu_utils.hh"
#include "ED_geometry.hh"
#include "ED_mesh.hh"
#include "ED_sculpt.hh"

#include "BLT_translation.h"

#include "FN_lazy_function_execute.hh"

#include "NOD_geometry_nodes_execute.hh"
#include "NOD_geometry_nodes_lazy_function.hh"

#include "AS_asset_catalog.hh"
#include "AS_asset_catalog_path.hh"
#include "AS_asset_catalog_tree.hh"
#include "AS_asset_library.hh"
#include "AS_asset_representation.hh"

#include "geometry_intern.hh"

namespace blender::ed::geometry {

/* -------------------------------------------------------------------- */
/** \name Operator
 * \{ */

static const bNodeTree *get_asset_or_local_node_group(const bContext &C,
                                                      PointerRNA &ptr,
                                                      ReportList *reports)
{
  Main &bmain = *CTX_data_main(&C);
  if (bNodeTree *group = reinterpret_cast<bNodeTree *>(
          WM_operator_properties_id_lookup_from_name_or_session_uuid(&bmain, &ptr, ID_NT)))
  {
    return group;
  }

  const asset_system::AssetRepresentation *asset =
      asset::operator_asset_reference_props_get_asset_from_all_library(C, ptr, reports);
  if (!asset) {
    return nullptr;
  }
  return reinterpret_cast<bNodeTree *>(asset::asset_local_id_ensure_imported(bmain, *asset));
}

static const bNodeTree *get_node_group(const bContext &C, PointerRNA &ptr, ReportList *reports)
{
  const bNodeTree *group = get_asset_or_local_node_group(C, ptr, reports);
  if (!group) {
    return nullptr;
  }
  if (group->type != NTREE_GEOMETRY) {
    if (reports) {
      BKE_report(reports, RPT_ERROR, "Asset is not a geometry node group");
    }
    return nullptr;
  }
  return group;
}

class OperatorComputeContext : public ComputeContext {
 private:
  static constexpr const char *s_static_type = "OPERATOR";

  std::string operator_name_;

 public:
  OperatorComputeContext(std::string operator_name)
      : ComputeContext(s_static_type, nullptr), operator_name_(std::move(operator_name))
  {
    hash_.mix_in(s_static_type, strlen(s_static_type));
    hash_.mix_in(operator_name_.data(), operator_name_.size());
  }

 private:
  void print_current_in_line(std::ostream &stream) const override
  {
    stream << "Operator: " << operator_name_;
  }
};

/**
 * Geometry nodes currently requires working on "evaluated" data-blocks (rather than "original"
 * data-blocks that are part of a #Main data-base). This could change in the future, but for now,
 * we need to create evaluated copies of geometry before passing it to geometry nodes. Implicit
 * sharing lets us avoid copying attribute data though.
 */
static bke::GeometrySet get_original_geometry_eval_copy(Object &object)
{
  switch (object.type) {
    case OB_CURVES: {
      Curves *curves = BKE_curves_copy_for_eval(static_cast<const Curves *>(object.data));
      return bke::GeometrySet::from_curves(curves);
    }
    case OB_POINTCLOUD: {
      PointCloud *points = BKE_pointcloud_copy_for_eval(
          static_cast<const PointCloud *>(object.data));
      return bke::GeometrySet::from_pointcloud(points);
    }
    case OB_MESH: {
      const Mesh *mesh = static_cast<const Mesh *>(object.data);
      if (mesh->edit_mesh) {
        Mesh *mesh_copy = BKE_mesh_wrapper_from_editmesh(mesh->edit_mesh, nullptr, mesh);
        BKE_mesh_wrapper_ensure_mdata(mesh_copy);
        Mesh *final_copy = BKE_mesh_copy_for_eval(mesh_copy);
        BKE_id_free(nullptr, mesh_copy);
        return bke::GeometrySet::from_mesh(final_copy);
      }
      return bke::GeometrySet::from_mesh(BKE_mesh_copy_for_eval(mesh));
    }
    default:
      return {};
  }
}

static void store_result_geometry(
    const wmOperator &op, Main &bmain, Scene &scene, Object &object, bke::GeometrySet geometry)
{
  geometry.ensure_owns_direct_data();
  switch (object.type) {
    case OB_CURVES: {
      Curves &curves = *static_cast<Curves *>(object.data);
      Curves *new_curves = geometry.get_curves_for_write();
      if (!new_curves) {
        curves.geometry.wrap() = {};
        break;
      }

      /* Anonymous attributes shouldn't be available on the applied geometry. */
      new_curves->geometry.wrap().attributes_for_write().remove_anonymous();

      curves.geometry.wrap() = std::move(new_curves->geometry.wrap());
      BKE_object_material_from_eval_data(&bmain, &object, &new_curves->id);
      break;
    }
    case OB_POINTCLOUD: {
      PointCloud &points = *static_cast<PointCloud *>(object.data);
      PointCloud *new_points =
          geometry.get_component_for_write<bke::PointCloudComponent>().release();
      if (!new_points) {
        CustomData_free(&points.pdata, points.totpoint);
        points.totpoint = 0;
        break;
      }

      /* Anonymous attributes shouldn't be available on the applied geometry. */
      new_points->attributes_for_write().remove_anonymous();

      BKE_object_material_from_eval_data(&bmain, &object, &new_points->id);
      BKE_pointcloud_nomain_to_pointcloud(new_points, &points);
      break;
    }
    case OB_MESH: {
      Mesh &mesh = *static_cast<Mesh *>(object.data);

      if (object.mode == OB_MODE_SCULPT) {
        ED_sculpt_undo_geometry_begin(&object, &op);
      }

      Mesh *new_mesh = geometry.get_component_for_write<bke::MeshComponent>().release();
      if (!new_mesh) {
        BKE_mesh_clear_geometry(&mesh);
      }
      else {
        /* Anonymous attributes shouldn't be available on the applied geometry. */
        new_mesh->attributes_for_write().remove_anonymous();

        BKE_object_material_from_eval_data(&bmain, &object, &new_mesh->id);
        BKE_mesh_nomain_to_mesh(new_mesh, &mesh, &object);
      }

      if (object.mode == OB_MODE_EDIT) {
        EDBM_mesh_make(&object, scene.toolsettings->selectmode, true);
        BKE_editmesh_looptri_and_normals_calc(mesh.edit_mesh);
      }
      else if (object.mode == OB_MODE_SCULPT) {
        ED_sculpt_undo_geometry_end(&object);
      }
      break;
    }
  }
}

/**
 * Create a dependency graph referencing all data-blocks used by the tree, and all selected
 * objects. Adding the selected objects is necessary because they are currently compared by pointer
 * to other evaluated objects inside of geometry nodes.
 */
static Depsgraph *build_depsgraph_from_indirect_ids(Main &bmain,
                                                    Scene &scene,
                                                    ViewLayer &view_layer,
                                                    const bNodeTree &node_tree_orig,
                                                    const Span<const Object *> objects,
                                                    const IDProperty &properties)
{
  Set<ID *> ids_for_relations;
  bool needs_own_transform_relation = false;
  nodes::find_node_tree_dependencies(
      node_tree_orig, ids_for_relations, needs_own_transform_relation);
  IDP_foreach_property(
      &const_cast<IDProperty &>(properties),
      IDP_TYPE_FILTER_ID,
      [](IDProperty *property, void *user_data) {
        if (ID *id = IDP_Id(property)) {
          static_cast<Set<ID *> *>(user_data)->add(id);
        }
      },
      &ids_for_relations);

  Vector<const ID *> ids;
  ids.append(&node_tree_orig.id);
  ids.extend(objects.cast<const ID *>());
  ids.insert(ids.size(), ids_for_relations.begin(), ids_for_relations.end());

  Depsgraph *depsgraph = DEG_graph_new(&bmain, &scene, &view_layer, DAG_EVAL_VIEWPORT);
  DEG_graph_build_from_ids(depsgraph, const_cast<ID **>(ids.data()), ids.size());
  return depsgraph;
}

static IDProperty *replace_inputs_evaluated_data_blocks(const IDProperty &op_properties,
                                                        const Depsgraph &depsgraph)
{
  /* We just create a temporary copy, so don't adjust data-block user count. */
  IDProperty *properties = IDP_CopyProperty_ex(&op_properties, LIB_ID_CREATE_NO_USER_REFCOUNT);
  IDP_foreach_property(
      properties,
      IDP_TYPE_FILTER_ID,
      [](IDProperty *property, void *user_data) {
        if (ID *id = IDP_Id(property)) {
          Depsgraph *depsgraph = static_cast<Depsgraph *>(user_data);
          property->data.pointer = DEG_get_evaluated_id(depsgraph, id);
        }
      },
      &const_cast<Depsgraph &>(depsgraph));
  return properties;
}

static int run_node_group_exec(bContext *C, wmOperator *op)
{
  Main *bmain = CTX_data_main(C);
  Scene *scene = CTX_data_scene(C);
  ViewLayer *view_layer = CTX_data_view_layer(C);
  Object *active_object = CTX_data_active_object(C);
  if (!active_object) {
    return OPERATOR_CANCELLED;
  }
  if (active_object->mode == OB_MODE_OBJECT) {
    return OPERATOR_CANCELLED;
  }
  const eObjectMode mode = eObjectMode(active_object->mode);

  const bNodeTree *node_tree_orig = get_node_group(*C, *op->ptr, op->reports);
  if (!node_tree_orig) {
    return OPERATOR_CANCELLED;
  }

  uint objects_len = 0;
  Object **objects = BKE_view_layer_array_from_objects_in_mode_unique_data(
      scene, view_layer, CTX_wm_view3d(C), &objects_len, mode);
  BLI_SCOPED_DEFER([&]() { MEM_SAFE_FREE(objects); });

  Depsgraph *depsgraph = build_depsgraph_from_indirect_ids(
      *bmain, *scene, *view_layer, *node_tree_orig, {objects, objects_len}, *op->properties);
  DEG_evaluate_on_refresh(depsgraph);
  BLI_SCOPED_DEFER([&]() { DEG_graph_free(depsgraph); });

  const bNodeTree *node_tree = reinterpret_cast<const bNodeTree *>(
      DEG_get_evaluated_id(depsgraph, const_cast<ID *>(&node_tree_orig->id)));

  const nodes::GeometryNodesLazyFunctionGraphInfo *lf_graph_info =
      nodes::ensure_geometry_nodes_lazy_function_graph(*node_tree);
  if (lf_graph_info == nullptr) {
    BKE_report(op->reports, RPT_ERROR, "Cannot evaluate node group");
    return OPERATOR_CANCELLED;
  }

  if (!node_tree->group_output_node()) {
    BKE_report(op->reports, RPT_ERROR, "Node group must have a group output node");
    return OPERATOR_CANCELLED;
  }

  IDProperty *properties = replace_inputs_evaluated_data_blocks(*op->properties, *depsgraph);
  BLI_SCOPED_DEFER([&]() { IDP_FreeProperty_ex(properties, false); });

  OperatorComputeContext compute_context(op->type->idname);

  for (Object *object : Span(objects, objects_len)) {
    if (!ELEM(object->type, OB_CURVES, OB_POINTCLOUD, OB_MESH)) {
      continue;
    }
    nodes::GeoNodesOperatorData operator_eval_data{};
    operator_eval_data.depsgraph = depsgraph;
    operator_eval_data.self_object = DEG_get_evaluated_object(depsgraph, object);
    operator_eval_data.scene = DEG_get_evaluated_scene(depsgraph);

    bke::GeometrySet geometry_orig = get_original_geometry_eval_copy(*object);

    bke::GeometrySet new_geometry = nodes::execute_geometry_nodes_on_geometry(
        *node_tree,
        properties,
        compute_context,
        std::move(geometry_orig),
        [&](nodes::GeoNodesLFUserData &user_data) {
          user_data.operator_data = &operator_eval_data;
          user_data.log_socket_values = false;
        });

    store_result_geometry(*op, *bmain, *scene, *object, std::move(new_geometry));

    DEG_id_tag_update(static_cast<ID *>(object->data), ID_RECALC_GEOMETRY);
    WM_event_add_notifier(C, NC_GEOM | ND_DATA, object->data);
  }

  return OPERATOR_FINISHED;
}

static int run_node_group_invoke(bContext *C, wmOperator *op, const wmEvent * /*event*/)
{
  const bNodeTree *node_tree = get_node_group(*C, *op->ptr, op->reports);
  if (!node_tree) {
    return OPERATOR_CANCELLED;
  }

  nodes::update_input_properties_from_node_tree(*node_tree, op->properties, true, *op->properties);
  nodes::update_output_properties_from_node_tree(*node_tree, op->properties, *op->properties);

  return run_node_group_exec(C, op);
}

static std::string run_node_group_get_description(bContext *C,
                                                  wmOperatorType * /*ot*/,
                                                  PointerRNA *ptr)
{
  const asset_system::AssetRepresentation *asset =
      asset::operator_asset_reference_props_get_asset_from_all_library(*C, *ptr, nullptr);
  if (!asset) {
    return "";
  }
  if (!asset->get_metadata().description) {
    return "";
  }
  return asset->get_metadata().description;
}

static void add_attribute_search_or_value_buttons(uiLayout *layout,
                                                  PointerRNA *md_ptr,
                                                  const bNodeTreeInterfaceSocket &socket)
{
  bNodeSocketType *typeinfo = nodeSocketTypeFind(socket.socket_type);
  const eNodeSocketDatatype socket_type = eNodeSocketDatatype(typeinfo->type);

  char socket_id_esc[MAX_NAME * 2];
  BLI_str_escape(socket_id_esc, socket.identifier, sizeof(socket_id_esc));
  const std::string rna_path = "[\"" + std::string(socket_id_esc) + "\"]";
  const std::string rna_path_use_attribute = "[\"" + std::string(socket_id_esc) +
                                             nodes::input_use_attribute_suffix() + "\"]";
  const std::string rna_path_attribute_name = "[\"" + std::string(socket_id_esc) +
                                              nodes::input_attribute_name_suffix() + "\"]";

  /* We're handling this manually in this case. */
  uiLayoutSetPropDecorate(layout, false);

  uiLayout *split = uiLayoutSplit(layout, 0.4f, false);
  uiLayout *name_row = uiLayoutRow(split, false);
  uiLayoutSetAlignment(name_row, UI_LAYOUT_ALIGN_RIGHT);

  const bool use_attribute = RNA_boolean_get(md_ptr, rna_path_use_attribute.c_str());
  if (socket_type == SOCK_BOOLEAN && !use_attribute) {
    uiItemL(name_row, "", ICON_NONE);
  }
  else {
    uiItemL(name_row, socket.name ? socket.name : "", ICON_NONE);
  }

  uiLayout *prop_row = uiLayoutRow(split, true);
  if (socket_type == SOCK_BOOLEAN) {
    uiLayoutSetPropSep(prop_row, false);
    uiLayoutSetAlignment(prop_row, UI_LAYOUT_ALIGN_EXPAND);
  }

  if (use_attribute) {
    /* TODO: Add attribute search. */
    uiItemR(prop_row, md_ptr, rna_path_attribute_name.c_str(), UI_ITEM_NONE, "", ICON_NONE);
  }
  else {
    const char *name = socket_type == SOCK_BOOLEAN ? (socket.name ? socket.name : "") : "";
    uiItemR(prop_row, md_ptr, rna_path.c_str(), UI_ITEM_NONE, name, ICON_NONE);
  }

  uiItemR(
      prop_row, md_ptr, rna_path_use_attribute.c_str(), UI_ITEM_R_ICON_ONLY, "", ICON_SPREADSHEET);
}

static void draw_property_for_socket(const bNodeTree &node_tree,
                                     uiLayout *layout,
                                     IDProperty *op_properties,
                                     PointerRNA *bmain_ptr,
                                     PointerRNA *op_ptr,
                                     const bNodeTreeInterfaceSocket &socket,
                                     const int socket_index)
{
  bNodeSocketType *typeinfo = nodeSocketTypeFind(socket.socket_type);
  const eNodeSocketDatatype socket_type = eNodeSocketDatatype(typeinfo->type);

  /* The property should be created in #MOD_nodes_update_interface with the correct type. */
  IDProperty *property = IDP_GetPropertyFromGroup(op_properties, socket.identifier);

  /* IDProperties can be removed with python, so there could be a situation where
   * there isn't a property for a socket or it doesn't have the correct type. */
  if (property == nullptr || !nodes::id_property_type_matches_socket(socket, *property)) {
    return;
  }

  char socket_id_esc[MAX_NAME * 2];
  BLI_str_escape(socket_id_esc, socket.identifier, sizeof(socket_id_esc));

  char rna_path[sizeof(socket_id_esc) + 4];
  SNPRINTF(rna_path, "[\"%s\"]", socket_id_esc);

  uiLayout *row = uiLayoutRow(layout, true);
  uiLayoutSetPropDecorate(row, false);

  /* Use #uiItemPointerR to draw pointer properties because #uiItemR would not have enough
   * information about what type of ID to select for editing the values. This is because
   * pointer IDProperties contain no information about their type. */
  const char *name = socket.name ? socket.name : "";
  switch (socket_type) {
    case SOCK_OBJECT:
      uiItemPointerR(row, op_ptr, rna_path, bmain_ptr, "objects", name, ICON_OBJECT_DATA);
      break;
    case SOCK_COLLECTION:
      uiItemPointerR(
          row, op_ptr, rna_path, bmain_ptr, "collections", name, ICON_OUTLINER_COLLECTION);
      break;
    case SOCK_MATERIAL:
      uiItemPointerR(row, op_ptr, rna_path, bmain_ptr, "materials", name, ICON_MATERIAL);
      break;
    case SOCK_TEXTURE:
      uiItemPointerR(row, op_ptr, rna_path, bmain_ptr, "textures", name, ICON_TEXTURE);
      break;
    case SOCK_IMAGE:
      uiItemPointerR(row, op_ptr, rna_path, bmain_ptr, "images", name, ICON_IMAGE);
      break;
    default:
      if (nodes::input_has_attribute_toggle(node_tree, socket_index)) {
        add_attribute_search_or_value_buttons(row, op_ptr, socket);
      }
      else {
        uiItemR(row, op_ptr, rna_path, UI_ITEM_NONE, name, ICON_NONE);
      }
  }
  if (!nodes::input_has_attribute_toggle(node_tree, socket_index)) {
    uiItemL(row, "", ICON_BLANK1);
  }
}

static void run_node_group_ui(bContext *C, wmOperator *op)
{
  uiLayout *layout = op->layout;
  uiLayoutSetPropSep(layout, true);
  uiLayoutSetPropDecorate(layout, false);
  Main *bmain = CTX_data_main(C);
  PointerRNA bmain_ptr = RNA_main_pointer_create(bmain);

  const bNodeTree *node_tree = get_node_group(*C, *op->ptr, nullptr);
  if (!node_tree) {
    return;
  }

  node_tree->ensure_interface_cache();
  int input_index = 0;
  for (const bNodeTreeInterfaceSocket *io_socket : node_tree->interface_inputs()) {
    draw_property_for_socket(
        *node_tree, layout, op->properties, &bmain_ptr, op->ptr, *io_socket, input_index);
    ++input_index;
  }
}

static bool run_node_ui_poll(wmOperatorType * /*ot*/, PointerRNA *ptr)
{
  bool result = false;
  RNA_STRUCT_BEGIN (ptr, prop) {
    int flag = RNA_property_flag(prop);
    if ((flag & PROP_HIDDEN) == 0) {
      result = true;
      break;
    }
  }
  RNA_STRUCT_END;
  return result;
}

static std::string run_node_group_get_name(wmOperatorType * /*ot*/, PointerRNA *ptr)
{
  int len;
  char *local_name = RNA_string_get_alloc(ptr, "name", nullptr, 0, &len);
  BLI_SCOPED_DEFER([&]() { MEM_SAFE_FREE(local_name); })
  if (len > 0) {
    return std::string(local_name, len);
  }
  char *library_asset_identifier = RNA_string_get_alloc(
      ptr, "relative_asset_identifier", nullptr, 0, &len);
  BLI_SCOPED_DEFER([&]() { MEM_SAFE_FREE(library_asset_identifier); })
  StringRef ref(library_asset_identifier, len);
  return ref.drop_prefix(ref.find_last_of(SEP_STR) + 1);
}

void GEOMETRY_OT_execute_node_group(wmOperatorType *ot)
{
  ot->name = "Run Node Group";
  ot->idname = __func__;
  ot->description = "Execute a node group on geometry";

  /* A proper poll is not possible, since it doesn't have access to the operator's properties. */
  ot->invoke = run_node_group_invoke;
  ot->exec = run_node_group_exec;
  ot->get_description = run_node_group_get_description;
  ot->ui = run_node_group_ui;
  ot->ui_poll = run_node_ui_poll;
  ot->get_name = run_node_group_get_name;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  asset::operator_asset_reference_props_register(*ot->srna);
  WM_operator_properties_id_lookup(ot, true);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Menu
 * \{ */

static bool asset_menu_poll(const bContext *C, MenuType * /*mt*/)
{
  return CTX_wm_view3d(C);
}

static GeometryNodeAssetTraitFlag asset_flag_for_context(const eContextObjectMode ctx_mode)
{
  switch (ctx_mode) {
    case CTX_MODE_EDIT_MESH:
      return (GEO_NODE_ASSET_TOOL | GEO_NODE_ASSET_EDIT | GEO_NODE_ASSET_MESH);
    case CTX_MODE_EDIT_CURVES:
      return (GEO_NODE_ASSET_TOOL | GEO_NODE_ASSET_EDIT | GEO_NODE_ASSET_CURVE);
    case CTX_MODE_EDIT_POINT_CLOUD:
      return (GEO_NODE_ASSET_TOOL | GEO_NODE_ASSET_EDIT | GEO_NODE_ASSET_POINT_CLOUD);
    case CTX_MODE_SCULPT:
      return (GEO_NODE_ASSET_TOOL | GEO_NODE_ASSET_SCULPT | GEO_NODE_ASSET_MESH);
    case CTX_MODE_SCULPT_CURVES:
      return (GEO_NODE_ASSET_TOOL | GEO_NODE_ASSET_SCULPT | GEO_NODE_ASSET_CURVE);
    default:
      BLI_assert_unreachable();
      return GeometryNodeAssetTraitFlag(0);
  }
}

static asset::AssetItemTree *get_static_item_tree(const eContextObjectMode mode)
{
  switch (mode) {
    case CTX_MODE_EDIT_MESH: {
      static asset::AssetItemTree tree;
      return &tree;
    }
    case CTX_MODE_EDIT_CURVES: {
      static asset::AssetItemTree tree;
      return &tree;
    }
    case CTX_MODE_EDIT_POINT_CLOUD: {
      static asset::AssetItemTree tree;
      return &tree;
    }
    case CTX_MODE_SCULPT: {
      static asset::AssetItemTree tree;
      return &tree;
    }
    case CTX_MODE_SCULPT_CURVES: {
      static asset::AssetItemTree tree;
      return &tree;
    }
    default:
      return nullptr;
  }
}

static asset::AssetItemTree *get_static_item_tree(const bContext &C)
{
  return get_static_item_tree(eContextObjectMode(CTX_data_mode_enum(&C)));
}

void clear_operator_asset_trees()
{
  for (const int mode : IndexRange(CTX_MODE_NUM)) {
    if (asset::AssetItemTree *tree = get_static_item_tree(eContextObjectMode(mode)))
      *tree = {};
  }
}

static asset::AssetItemTree build_catalog_tree(const bContext &C)
{
  const eContextObjectMode ctx_mode = eContextObjectMode(CTX_data_mode_enum(&C));
  AssetFilterSettings type_filter{};
  type_filter.id_types = FILTER_ID_NT;
  const GeometryNodeAssetTraitFlag flag = asset_flag_for_context(ctx_mode);
  auto meta_data_filter = [&](const AssetMetaData &meta_data) {
    const IDProperty *tree_type = BKE_asset_metadata_idprop_find(&meta_data, "type");
    if (tree_type == nullptr || IDP_Int(tree_type) != NTREE_GEOMETRY) {
      return false;
    }
    const IDProperty *traits_flag = BKE_asset_metadata_idprop_find(
        &meta_data, "geometry_node_asset_traits_flag");
    if (traits_flag == nullptr || (IDP_Int(traits_flag) & flag) != flag) {
      return false;
    }
    return true;
  };
  const AssetLibraryReference library = asset_system::all_library_reference();
  return asset::build_filtered_all_catalog_tree(library, C, type_filter, meta_data_filter);
}

/**
 * Avoid adding a separate root catalog when the assets have already been added to one of the
 * builtin menus. The need to define the builtin menu labels here is non-ideal. We don't have
 * any UI introspection that can do this though.
 */
static Set<std::string> get_builtin_menus(const ObjectType object_type, const eObjectMode mode)
{
  Set<std::string> menus;
  switch (object_type) {
    case OB_CURVES:
      menus.add_new("View");
      menus.add_new("Select");
      menus.add_new("Curves");
      break;
    case OB_POINTCLOUD:
      menus.add_new("View");
      menus.add_new("Select");
      menus.add_new("Point Cloud");
      break;
    case OB_MESH:
      switch (mode) {
        case OB_MODE_EDIT:
          menus.add_new("View");
          menus.add_new("Select");
          menus.add_new("Add");
          menus.add_new("Mesh");
          menus.add_new("Mesh/Extrude");
          menus.add_new("Mesh/Clean Up");
          menus.add_new("Mesh/Delete");
          menus.add_new("Mesh/Merge");
          menus.add_new("Mesh/Normals");
          menus.add_new("Mesh/Shading");
          menus.add_new("Mesh/Split");
          menus.add_new("Mesh/Weights");
          menus.add_new("Vertex");
          menus.add_new("Edge");
          menus.add_new("Face");
          menus.add_new("Face/Face Data");
          menus.add_new("UV");
          break;
        case OB_MODE_SCULPT:
          menus.add_new("View");
          menus.add_new("Sculpt");
          menus.add_new("Mask");
          menus.add_new("Face Sets");
          break;
        case OB_MODE_VERTEX_PAINT:
          menus.add_new("View");
          menus.add_new("Paint");
          break;
        case OB_MODE_WEIGHT_PAINT:
          menus.add_new("View");
          menus.add_new("Weights");
          break;
        default:
          break;
      }
    default:
      break;
  }
  return menus;
}

static void catalog_assets_draw(const bContext *C, Menu *menu)
{
  bScreen &screen = *CTX_wm_screen(C);
  const Object *active_object = CTX_data_active_object(C);
  if (!active_object) {
    return;
  }
  asset::AssetItemTree *tree = get_static_item_tree(*C);
  if (!tree) {
    return;
  }
  const PointerRNA menu_path_ptr = CTX_data_pointer_get(C, "asset_catalog_path");
  if (RNA_pointer_is_null(&menu_path_ptr)) {
    return;
  }
  const auto &menu_path = *static_cast<const asset_system::AssetCatalogPath *>(menu_path_ptr.data);
  const Span<asset_system::AssetRepresentation *> assets = tree->assets_per_path.lookup(menu_path);
  asset_system::AssetCatalogTreeItem *catalog_item = tree->catalogs.find_item(menu_path);
  BLI_assert(catalog_item != nullptr);

  uiLayout *layout = menu->layout;
  bool add_separator = true;

  wmOperatorType *ot = WM_operatortype_find("GEOMETRY_OT_execute_node_group", true);
  for (const asset_system::AssetRepresentation *asset : assets) {
    if (add_separator) {
      uiItemS(layout);
      add_separator = false;
    }
    PointerRNA props_ptr;
    uiItemFullO_ptr(layout,
                    ot,
                    IFACE_(asset->get_name().c_str()),
                    ICON_NONE,
                    nullptr,
                    WM_OP_INVOKE_REGION_WIN,
                    UI_ITEM_NONE,
                    &props_ptr);
    asset::operator_asset_reference_props_set(*asset, props_ptr);
  }

  const Set<std::string> builtin_menus = get_builtin_menus(ObjectType(active_object->type),
                                                           eObjectMode(active_object->mode));

  asset_system::AssetLibrary *all_library = ED_assetlist_library_get_once_available(
      asset_system::all_library_reference());
  if (!all_library) {
    return;
  }

  catalog_item->foreach_child([&](asset_system::AssetCatalogTreeItem &item) {
    if (builtin_menus.contains_as(item.catalog_path().str())) {
      return;
    }
    if (add_separator) {
      uiItemS(layout);
      add_separator = false;
    }
    asset::draw_menu_for_catalog(
        screen, *all_library, item, "GEO_MT_node_operator_catalog_assets", *layout);
  });
}

MenuType node_group_operator_assets_menu()
{
  MenuType type{};
  STRNCPY(type.idname, "GEO_MT_node_operator_catalog_assets");
  type.poll = asset_menu_poll;
  type.draw = catalog_assets_draw;
  type.listener = asset::asset_reading_region_listen_fn;
  type.flag = MenuTypeFlag::ContextDependent;
  return type;
}

static bool unassigned_local_poll(const bContext &C)
{
  Main &bmain = *CTX_data_main(&C);
  const GeometryNodeAssetTraitFlag flag = asset_flag_for_context(
      eContextObjectMode(CTX_data_mode_enum(&C)));

  LISTBASE_FOREACH (const bNodeTree *, group, &bmain.nodetrees) {
    /* Assets are displayed in other menus, and non-local data-blocks aren't added to this menu. */
    if (group->id.library_weak_reference || group->id.asset_data) {
      continue;
    }
    if (!group->geometry_node_asset_traits ||
        (group->geometry_node_asset_traits->flag & flag) != flag) {
      continue;
    }
    return true;
  }
  return false;
}

static void catalog_assets_draw_unassigned(const bContext *C, Menu *menu)
{
  asset::AssetItemTree *tree = get_static_item_tree(*C);
  if (!tree) {
    return;
  }
  uiLayout *layout = menu->layout;
  wmOperatorType *ot = WM_operatortype_find("GEOMETRY_OT_execute_node_group", true);
  for (const asset_system::AssetRepresentation *asset : tree->unassigned_assets) {
    PointerRNA props_ptr;
    uiItemFullO_ptr(layout,
                    ot,
                    IFACE_(asset->get_name().c_str()),
                    ICON_NONE,
                    nullptr,
                    WM_OP_INVOKE_REGION_WIN,
                    UI_ITEM_NONE,
                    &props_ptr);
    asset::operator_asset_reference_props_set(*asset, props_ptr);
  }

  const GeometryNodeAssetTraitFlag flag = asset_flag_for_context(
      eContextObjectMode(CTX_data_mode_enum(C)));

  bool first = true;
  bool add_separator = !tree->unassigned_assets.is_empty();
  Main &bmain = *CTX_data_main(C);
  LISTBASE_FOREACH (const bNodeTree *, group, &bmain.nodetrees) {
    /* Assets are displayed in other menus, and non-local data-blocks aren't added to this menu. */
    if (group->id.library_weak_reference || group->id.asset_data) {
      continue;
    }
    if (!group->geometry_node_asset_traits ||
        (group->geometry_node_asset_traits->flag & flag) != flag) {
      continue;
    }

    if (add_separator) {
      uiItemS(layout);
      add_separator = false;
    }
    if (first) {
      uiItemL(layout, IFACE_("Non-Assets"), ICON_NONE);
      first = false;
    }

    PointerRNA props_ptr;
    uiItemFullO_ptr(layout,
                    ot,
                    group->id.name + 2,
                    ICON_NONE,
                    nullptr,
                    WM_OP_INVOKE_REGION_WIN,
                    UI_ITEM_NONE,
                    &props_ptr);
    WM_operator_properties_id_lookup_set_from_id(&props_ptr, &group->id);
    /* Also set the name so it can be used for #run_node_group_get_name. */
    RNA_string_set(&props_ptr, "name", group->id.name + 2);
  }
}

MenuType node_group_operator_assets_menu_unassigned()
{
  MenuType type{};
  STRNCPY(type.idname, "GEO_MT_node_operator_unassigned");
  type.poll = asset_menu_poll;
  type.draw = catalog_assets_draw_unassigned;
  type.listener = asset::asset_reading_region_listen_fn;
  type.flag = MenuTypeFlag::ContextDependent;
  type.description = N_(
      "Tool node group assets not assigned to a catalog.\n"
      "Catalogs can be assigned in the Asset Browser");
  return type;
}

void ui_template_node_operator_asset_menu_items(uiLayout &layout,
                                                const bContext &C,
                                                const StringRef catalog_path)
{
  bScreen &screen = *CTX_wm_screen(&C);
  asset::AssetItemTree *tree = get_static_item_tree(C);
  if (!tree) {
    return;
  }
  const asset_system::AssetCatalogTreeItem *item = tree->catalogs.find_item(catalog_path);
  if (!item) {
    return;
  }
  asset_system::AssetLibrary *all_library = ED_assetlist_library_get_once_available(
      asset_system::all_library_reference());
  if (!all_library) {
    return;
  }
  PointerRNA path_ptr = asset::persistent_catalog_path_rna_pointer(screen, *all_library, *item);
  if (path_ptr.data == nullptr) {
    return;
  }
  uiLayout *col = uiLayoutColumn(&layout, false);
  uiLayoutSetContextPointer(col, "asset_catalog_path", &path_ptr);
  uiItemMContents(col, "GEO_MT_node_operator_catalog_assets");
}

void ui_template_node_operator_asset_root_items(uiLayout &layout, const bContext &C)
{
  bScreen &screen = *CTX_wm_screen(&C);
  const Object *active_object = CTX_data_active_object(&C);
  if (!active_object) {
    return;
  }
  asset::AssetItemTree *tree = get_static_item_tree(C);
  if (!tree) {
    return;
  }
  if (tree->assets_per_path.size() == 0) {
    *tree = build_catalog_tree(C);
  }

  asset_system::AssetLibrary *all_library = ED_assetlist_library_get_once_available(
      asset_system::all_library_reference());
  if (!all_library) {
    return;
  }

  const Set<std::string> builtin_menus = get_builtin_menus(ObjectType(active_object->type),
                                                           eObjectMode(active_object->mode));

  tree->catalogs.foreach_root_item([&](asset_system::AssetCatalogTreeItem &item) {
    if (!builtin_menus.contains_as(item.catalog_path().str())) {
      asset::draw_menu_for_catalog(
          screen, *all_library, item, "GEO_MT_node_operator_catalog_assets", layout);
    }
  });

  if (!tree->unassigned_assets.is_empty() || unassigned_local_poll(C)) {
    uiItemM(&layout, "GEO_MT_node_operator_unassigned", "", ICON_FILE_HIDDEN);
  }
}

/** \} */

}  // namespace blender::ed::geometry
