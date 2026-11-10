/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup RNA
 */

#include "BLT_translation.hh"

#include "BKE_attribute.hh"
#include "BKE_node.hh"

#include "RNA_enum_types.hh"

#include "UI_interface_c.hh"

#include "rna_internal.hh"
#include "rna_nodetree_common.hh"

namespace blender {

static const EnumPropertyItem rna_node_geometry_curve_handle_type_items[] = {
    {GEO_NODE_CURVE_HANDLE_FREE,
     "FREE",
     ICON_HANDLE_FREE,
     "Free",
     "The handle can be moved anywhere, and does not influence the point's other handle"},
    {GEO_NODE_CURVE_HANDLE_AUTO,
     "AUTO",
     ICON_HANDLE_AUTO,
     "Auto",
     "The location is automatically calculated to be smooth"},
    {GEO_NODE_CURVE_HANDLE_VECTOR,
     "VECTOR",
     ICON_HANDLE_VECTOR,
     "Vector",
     "The location is calculated to point to the next/previous control point"},
    {GEO_NODE_CURVE_HANDLE_ALIGN,
     "ALIGN",
     ICON_HANDLE_ALIGNED,
     "Align",
     "The location is constrained to point in the opposite direction as the other handle"},
    {0, nullptr, 0, nullptr, nullptr}};

const EnumPropertyItem rna_enum_node_geometry_curve_handle_side_items[] = {
    {GEO_NODE_CURVE_HANDLE_LEFT, "LEFT", ICON_NONE, "Left", "Use the left handles"},
    {GEO_NODE_CURVE_HANDLE_RIGHT, "RIGHT", ICON_NONE, "Right", "Use the right handles"},
    {0, nullptr, 0, nullptr, nullptr}};

const EnumPropertyItem rna_enum_node_grease_pencil_merge_mode_items[] = {
    {GEO_NODE_MERGE_LAYERS_BY_NAME,
     "MERGE_BY_NAME",
     0,
     "By Name",
     "Combine all layers which have the same name"},
    {GEO_NODE_MERGE_LAYERS_BY_ID,
     "MERGE_BY_ID",
     0,
     "By Group ID",
     "Provide a custom group ID for each layer and all layers with the same ID will be merged "
     "into one"},
    {0, nullptr, 0, nullptr, nullptr},
};

const EnumPropertyItem rna_enum_node_grease_pencil_stroke_type_items[] = {
    {GEO_NODE_GREASE_PENCIL_STROKE,
     "STROKE",
     ICON_GP_DRAW_STROKE,
     "Stroke",
     "Set the color and opacity for the points of the stroke"},
    {GEO_NODE_GREASE_PENCIL_FILL,
     "FILL",
     ICON_GP_DRAW_FILL,
     "Fill",
     "Set the color and opacity for the stroke fills"},
    {GEO_NODE_GREASE_PENCIL_BOTH,
     "BOTH",
     ICON_GP_DRAW_BOTH,
     "Both",
     "Set the color and opacity for stroke points and fills together"},
    {0, nullptr, 0, nullptr, nullptr},
};

}  // namespace blender

#ifdef RNA_RUNTIME

#  include "NOD_geo_bake.hh"
#  include "NOD_geo_capture_attribute.hh"
#  include "NOD_geo_closure_to_list.hh"
#  include "NOD_geo_combine_list.hh"
#  include "NOD_geo_field_to_grid.hh"
#  include "NOD_geo_field_to_list.hh"
#  include "NOD_geo_foreach_geometry_element.hh"
#  include "NOD_geo_index_switch.hh"
#  include "NOD_geo_menu_switch.hh"
#  include "NOD_geo_rasterize_points.hh"
#  include "NOD_geo_repeat.hh"
#  include "NOD_geo_viewer.hh"

namespace blender {

using nodes::BakeItemsAccessor;
using nodes::CaptureAttributeItemsAccessor;
using nodes::ClosureToListItemsAccessor;
using nodes::CombineListItemsAccessor;
using nodes::FieldToGridItemsAccessor;
using nodes::FieldToListItemsAccessor;
using nodes::ForeachGeometryElementGenerationItemsAccessor;
using nodes::ForeachGeometryElementInputItemsAccessor;
using nodes::ForeachGeometryElementMainItemsAccessor;
using nodes::GeoViewerItemsAccessor;
using nodes::IndexSwitchItemsAccessor;
using nodes::MenuSwitchItemsAccessor;
using nodes::RasterizePointsItemsAccessor;
using nodes::RepeatItemsAccessor;
using nodes::SimulationItemsAccessor;

static bool generic_attribute_type_supported(const EnumPropertyItem *item)
{
  return ELEM(item->value,
              CD_PROP_FLOAT,
              CD_PROP_FLOAT2,
              CD_PROP_FLOAT3,
              CD_PROP_COLOR,
              CD_PROP_BOOL,
              CD_PROP_INT32,
              CD_PROP_BYTE_COLOR,
              CD_PROP_QUATERNION,
              CD_PROP_FLOAT4X4);
}

static bool generic_attribute_type_supported_with_socket(const EnumPropertyItem *item)
{
  return generic_attribute_type_supported(item) &&
         !ELEM(item->value, CD_PROP_BYTE_COLOR, CD_PROP_FLOAT2);
}

static const EnumPropertyItem *rna_GeometryNodeAttributeType_type_with_socket_itemf(
    bContext * /*C*/, PointerRNA * /*ptr*/, PropertyRNA * /*prop*/, bool *r_free)
{
  *r_free = true;
  return itemf_function_check(rna_enum_attribute_type_items,
                              generic_attribute_type_supported_with_socket);
}

static const EnumPropertyItem *rna_GeometryNodeAttributeDomain_attribute_domain_itemf(
    bContext * /*C*/, PointerRNA * /*ptr*/, PropertyRNA * /*prop*/, bool *r_free)
{
  EnumPropertyItem *item_array = nullptr;
  int items_len = 0;

  for (const EnumPropertyItem *item = rna_enum_attribute_domain_items; item->identifier != nullptr;
       item++)
  {
    RNA_enum_item_add(&item_array, &items_len, item);
  }
  RNA_enum_item_end(&item_array, &items_len);

  *r_free = true;
  return item_array;
}

/** Similar to #rna_NodeSocket_structure_type_item_filter. */
static const EnumPropertyItem *rna_GeometryNodeClosureToListItem_structure_type_itemf(
    bContext * /*C*/, PointerRNA *ptr, PropertyRNA * /*prop*/, bool *r_free)
{
  const bNodeTree *ntree = reinterpret_cast<const bNodeTree *>(ptr->owner_id);
  const auto &item = *static_cast<const GeometryNodeClosureToListItem *>(ptr->data);
  const auto socket_type = eNodeSocketDatatype(item.socket_type);

  if (!ntree) {
    return rna_enum_dummy_NULL_items;
  }
  const bool is_geometry_nodes = ntree->type == NTREE_GEOMETRY;
  const bool supports_fields = is_geometry_nodes &&
                               nodes::socket_type_supports_fields(socket_type);
  const bool supports_grids = is_geometry_nodes && nodes::socket_type_supports_grids(socket_type);
  /* Lists of lists are sort of arbitrarily not supported yet. */
  const bool supports_lists = false;

  *r_free = true;
  EnumPropertyItem *items = nullptr;
  int items_count = 0;

  for (const EnumPropertyItem *item = rna_enum_node_socket_structure_type_items; item->identifier;
       item++)
  {
    switch (NodeSocketInterfaceStructureType(item->value)) {
      case NodeSocketInterfaceStructureType::Single: {
        RNA_enum_item_add(&items, &items_count, item);
        break;
      }
      case NodeSocketInterfaceStructureType::Auto: {
        break;
      }
      case NodeSocketInterfaceStructureType::Dynamic: {
        if (supports_fields || supports_grids) {
          RNA_enum_item_add(&items, &items_count, item);
        }
        break;
      }
      case NodeSocketInterfaceStructureType::Field: {
        if (supports_fields) {
          RNA_enum_item_add(&items, &items_count, item);
        }
        break;
      }
      case NodeSocketInterfaceStructureType::Grid: {
        if (supports_grids) {
          RNA_enum_item_add(&items, &items_count, item);
        }
        break;
      }
      case NodeSocketInterfaceStructureType::List: {
        if (supports_lists) {
          RNA_enum_item_add(&items, &items_count, item);
        }
        break;
      }
    }
  }
  RNA_enum_item_end(&items, &items_count);
  return items;
}

static IndexSwitchItem *rna_NodeIndexSwitchItems_new(ID *id, bNode *node, Main *bmain)
{
  IndexSwitchItem *new_item = nodes::socket_items::add_item<IndexSwitchItemsAccessor>(*node);

  bNodeTree *ntree = reinterpret_cast<bNodeTree *>(id);
  BKE_ntree_update_tag_node_property(ntree, node);
  BKE_main_ensure_invariants(*bmain, ntree->id);
  WM_main_add_notifier(NC_NODE | NA_EDITED, ntree);

  return new_item;
}

static NodeGeometryRasterizePointsItem *rna_NodeGeometryRasterizePointsItems_new(ID *id,
                                                                                 bNode *node,
                                                                                 Main *bmain,
                                                                                 const char *name)
{
  NodeGeometryRasterizePointsItem *new_item =
      nodes::socket_items::add_item_with_name<RasterizePointsItemsAccessor>(*node, name);

  bNodeTree *ntree = reinterpret_cast<bNodeTree *>(id);
  BKE_ntree_update_tag_node_property(ntree, node);
  BKE_main_ensure_invariants(*bmain, ntree->id);
  WM_main_add_notifier(NC_NODE | NA_EDITED, ntree);

  return new_item;
}

static CombineListItem *rna_NodeCombineListItems_new(ID *id, bNode *node, Main *bmain)
{
  CombineListItem *new_item = nodes::socket_items::add_item<CombineListItemsAccessor>(*node);

  bNodeTree *ntree = reinterpret_cast<bNodeTree *>(id);
  BKE_ntree_update_tag_node_property(ntree, node);
  BKE_main_ensure_invariants(*bmain, ntree->id);
  WM_main_add_notifier(NC_NODE | NA_EDITED, ntree);

  return new_item;
}

/* The same as #grid_socket_type_items_filter_fn. */
static const EnumPropertyItem *rna_NodeFieldToGridItem_data_type_itemf(bContext * /*C*/,
                                                                       PointerRNA * /*ptr*/,
                                                                       PropertyRNA * /*prop*/,
                                                                       bool *r_free)
{
  *r_free = true;
  return itemf_function_check(
      rna_enum_node_socket_data_type_items, [](const EnumPropertyItem *item) {
        return nodes::socket_type_supports_grids(eNodeSocketDatatype(item->value));
      });
}

static const EnumPropertyItem *rna_NodeGeometryCaptureAttributeItem_data_type_itemf(
    bContext * /*C*/, PointerRNA * /*ptr*/, PropertyRNA * /*prop*/, bool *r_free)
{
  *r_free = true;
  /* See #attribute_type_type_with_socket_fn. */
  return itemf_function_check(rna_enum_attribute_type_items, [](const EnumPropertyItem *item) {
    return ELEM(item->value,
                CD_PROP_FLOAT,
                CD_PROP_FLOAT3,
                CD_PROP_COLOR,
                CD_PROP_BOOL,
                CD_PROP_INT32,
                CD_PROP_QUATERNION,
                CD_PROP_FLOAT4X4);
  });
}

static NodeEnumItem *rna_NodeMenuSwitchItems_new(ID *id,
                                                 bNode *node,
                                                 Main *bmain,
                                                 const char *name)
{
  NodeEnumItem *new_item = nodes::socket_items::add_item_with_name<MenuSwitchItemsAccessor>(*node,
                                                                                            name);

  bNodeTree *ntree = reinterpret_cast<bNodeTree *>(id);
  BKE_ntree_update_tag_node_property(ntree, node);
  BKE_main_ensure_invariants(*bmain, ntree->id);
  WM_main_add_notifier(NC_NODE | NA_EDITED, ntree);

  return new_item;
}

static PointerRNA rna_NodeMenuSwitch_enum_definition_get(PointerRNA *ptr)
{
  /* Return node itself. The data is now directly available on the node and does not have to be
   * accessed through "enum_definition". */
  return *ptr;
}

static int rna_MergeLayers_mode_get(PointerRNA *ptr)
{
  bNode *node = ptr->data_as<bNode>();
  const bNodeSocket *socket = bke::node_find_socket(*node, SOCK_IN, "Mode"_ustr);
  return socket->default_value_typed<bNodeSocketValueMenu>()->value;
}

static void rna_MergeLayers_mode_set(PointerRNA *ptr, int value)
{
  bNode *node = ptr->data_as<bNode>();
  bNodeSocket *socket = bke::node_find_socket(*node, SOCK_IN, "Mode"_ustr);
  socket->default_value_typed<bNodeSocketValueMenu>()->value = value;
}

static int rna_SetGreasePencilColor_mode_get(PointerRNA *ptr)
{
  bNode *node = ptr->data_as<bNode>();
  const bNodeSocket *socket = bke::node_find_socket(*node, SOCK_IN, "Mode"_ustr);
  return socket->default_value_typed<bNodeSocketValueMenu>()->value;
}

static void rna_SetGreasePencilColor_mode_set(PointerRNA *ptr, int value)
{
  bNode *node = ptr->data_as<bNode>();
  bNodeSocket *socket = bke::node_find_socket(*node, SOCK_IN, "Mode"_ustr);
  socket->default_value_typed<bNodeSocketValueMenu>()->value = value;
}

static int rna_SetGreasePencilDepth_depth_order_get(PointerRNA *ptr)
{
  bNode *node = ptr->data_as<bNode>();
  const bNodeSocket *socket = bke::node_find_socket(*node, SOCK_IN, "Depth Order"_ustr);
  return socket->default_value_typed<bNodeSocketValueMenu>()->value;
}

static void rna_SetGreasePencilDepth_depth_order_set(PointerRNA *ptr, int value)
{
  bNode *node = ptr->data_as<bNode>();
  bNodeSocket *socket = bke::node_find_socket(*node, SOCK_IN, "Depth Order"_ustr);
  socket->default_value_typed<bNodeSocketValueMenu>()->value = value;
}

}  // namespace blender

#else

namespace blender {

static void def_geo_image_texture(BlenderRNA * /*brna*/, StructRNA *srna)
{
  static const EnumPropertyItem fn_tex_prop_interpolation_items[] = {
      {SHD_INTERP_LINEAR, "Linear", 0, "Linear", "Linear interpolation"},
      {SHD_INTERP_CLOSEST, "Closest", 0, "Closest", "No interpolation (sample closest texel)"},
      {SHD_INTERP_CUBIC, "Cubic", 0, "Cubic", "Cubic interpolation"},
      {0, nullptr, 0, nullptr, nullptr},
  };

  PropertyRNA *prop;

  RNA_def_struct_sdna_from(srna, "NodeGeometryImageTexture", "storage");

  prop = RNA_def_property(srna, "interpolation", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, fn_tex_prop_interpolation_items);
  RNA_def_property_ui_text(prop, "Interpolation", "Method for smoothing values between pixels");
  RNA_def_property_update(prop, 0, "rna_Node_update");

  prop = RNA_def_property(srna, "extension", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, prop_image_extension);
  RNA_def_property_ui_text(
      prop, "Extension", "How the image is extrapolated past its original bounds");
  RNA_def_property_translation_context(prop, BLT_I18NCONTEXT_ID_IMAGE);
  RNA_def_property_update(prop, 0, "rna_Node_update");
}

static void rna_def_geo_gizmo_transform(BlenderRNA * /*brna*/, StructRNA *srna)
{
  PropertyRNA *prop;

  RNA_def_struct_sdna_from(srna, "NodeGeometryTransformGizmo", "storage");

  prop = RNA_def_property(srna, "use_translation_x", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, nullptr, "flag", GEO_NODE_TRANSFORM_GIZMO_USE_TRANSLATION_X);
  RNA_def_property_boolean_default(prop, true);
  RNA_def_property_ui_text(prop, "Use Translation X", nullptr);
  RNA_def_property_update(prop, 0, "rna_Node_update");

  prop = RNA_def_property(srna, "use_translation_y", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, nullptr, "flag", GEO_NODE_TRANSFORM_GIZMO_USE_TRANSLATION_Y);
  RNA_def_property_boolean_default(prop, true);
  RNA_def_property_ui_text(prop, "Use Translation Y", nullptr);
  RNA_def_property_update(prop, 0, "rna_Node_update");

  prop = RNA_def_property(srna, "use_translation_z", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, nullptr, "flag", GEO_NODE_TRANSFORM_GIZMO_USE_TRANSLATION_Z);
  RNA_def_property_boolean_default(prop, true);
  RNA_def_property_ui_text(prop, "Use Translation Z", nullptr);
  RNA_def_property_update(prop, 0, "rna_Node_update");

  prop = RNA_def_property(srna, "use_rotation_x", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, nullptr, "flag", GEO_NODE_TRANSFORM_GIZMO_USE_ROTATION_X);
  RNA_def_property_boolean_default(prop, true);
  RNA_def_property_ui_text(prop, "Use Rotation X", nullptr);
  RNA_def_property_update(prop, 0, "rna_Node_update");

  prop = RNA_def_property(srna, "use_rotation_y", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, nullptr, "flag", GEO_NODE_TRANSFORM_GIZMO_USE_ROTATION_Y);
  RNA_def_property_boolean_default(prop, true);
  RNA_def_property_ui_text(prop, "Use Rotation Y", nullptr);
  RNA_def_property_update(prop, 0, "rna_Node_update");

  prop = RNA_def_property(srna, "use_rotation_z", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, nullptr, "flag", GEO_NODE_TRANSFORM_GIZMO_USE_ROTATION_Z);
  RNA_def_property_boolean_default(prop, true);
  RNA_def_property_ui_text(prop, "Use Rotation Z", nullptr);
  RNA_def_property_update(prop, 0, "rna_Node_update");

  prop = RNA_def_property(srna, "use_scale_x", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, nullptr, "flag", GEO_NODE_TRANSFORM_GIZMO_USE_SCALE_X);
  RNA_def_property_boolean_default(prop, true);
  RNA_def_property_ui_text(prop, "Use Scale X", nullptr);
  RNA_def_property_update(prop, 0, "rna_Node_update");

  prop = RNA_def_property(srna, "use_scale_y", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, nullptr, "flag", GEO_NODE_TRANSFORM_GIZMO_USE_SCALE_Y);
  RNA_def_property_boolean_default(prop, true);
  RNA_def_property_ui_text(prop, "Use Scale Y", nullptr);
  RNA_def_property_update(prop, 0, "rna_Node_update");

  prop = RNA_def_property(srna, "use_scale_z", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, nullptr, "flag", GEO_NODE_TRANSFORM_GIZMO_USE_SCALE_Z);
  RNA_def_property_boolean_default(prop, true);
  RNA_def_property_ui_text(prop, "Use Scale Z", nullptr);
  RNA_def_property_update(prop, 0, "rna_Node_update");
}

static void def_geo_curve_sample(BlenderRNA * /*brna*/, StructRNA *srna)
{
  static EnumPropertyItem mode_items[] = {
      {GEO_NODE_CURVE_SAMPLE_FACTOR,
       "FACTOR",
       0,
       "Factor",
       "Find sample positions on the curve using a factor of its total length"},
      {GEO_NODE_CURVE_SAMPLE_LENGTH,
       "LENGTH",
       0,
       "Length",
       "Find sample positions on the curve using a distance from its beginning"},
      {0, nullptr, 0, nullptr, nullptr},
  };

  RNA_def_struct_sdna_from(srna, "NodeGeometryCurveSample", "storage");

  PropertyRNA *prop;
  prop = RNA_def_property(srna, "mode", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, mode_items);
  RNA_def_property_ui_text(prop, "Mode", "Method for sampling input");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_socket_update");

  prop = RNA_def_property(srna, "use_all_curves", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_ui_text(prop,
                           "All Curves",
                           "Sample lengths based on the total length of all curves, rather than "
                           "using a length inside each selected curve");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_socket_update");

  prop = RNA_def_property(srna, "data_type", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, rna_enum_attribute_type_items);
  RNA_def_property_enum_funcs(
      prop, nullptr, nullptr, "rna_GeometryNodeAttributeType_type_with_socket_itemf");
  RNA_def_property_enum_default(prop, CD_PROP_FLOAT);
  RNA_def_property_ui_text(prop, "Data Type", "");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_socket_update");
}

static void def_geo_distribute_points_on_faces(BlenderRNA * /*brna*/, StructRNA *srna)
{
  PropertyRNA *prop;

  static const EnumPropertyItem rna_node_geometry_distribute_points_on_faces_mode_items[] = {
      {GEO_NODE_POINT_DISTRIBUTE_POINTS_ON_FACES_RANDOM,
       "RANDOM",
       0,
       "Random",
       "Distribute points randomly on the surface"},
      {GEO_NODE_POINT_DISTRIBUTE_POINTS_ON_FACES_POISSON,
       "POISSON",
       0,
       "Poisson Disk",
       "Distribute the points randomly on the surface while taking a minimum distance between "
       "points into account"},
      {0, nullptr, 0, nullptr, nullptr},
  };

  prop = RNA_def_property(srna, "distribute_method", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_sdna(prop, nullptr, "custom1");
  RNA_def_property_enum_items(prop, rna_node_geometry_distribute_points_on_faces_mode_items);
  RNA_def_property_enum_default(prop, GEO_NODE_POINT_DISTRIBUTE_POINTS_ON_FACES_RANDOM);
  RNA_def_property_ui_text(prop, "Distribution Method", "Method to use for scattering points");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_socket_update");

  prop = RNA_def_property(srna, "use_legacy_normal", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, nullptr, "custom2", 1);
  RNA_def_property_ui_text(prop,
                           "Legacy Normal",
                           "Output the normal and rotation values that have been output "
                           "before the node started taking smooth normals into account");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_socket_update");
}

static void def_geo_curve_set_handle_type(BlenderRNA * /*brna*/, StructRNA *srna)
{
  PropertyRNA *prop;

  RNA_def_struct_sdna_from(srna, "NodeGeometryCurveSetHandles", "storage");

  prop = RNA_def_property(srna, "handle_type", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_sdna(prop, nullptr, "handle_type");
  RNA_def_property_ui_text(prop, "Handle Type", "");
  RNA_def_property_enum_items(prop, rna_node_geometry_curve_handle_type_items);
  RNA_def_property_enum_default(prop, GEO_NODE_CURVE_HANDLE_AUTO);
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_socket_update");

  prop = RNA_def_property(srna, "mode", PROP_ENUM, PROP_NONE);
  RNA_def_property_flag(prop, PROP_ENUM_FLAG);
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_enum_items(prop, rna_enum_node_geometry_curve_handle_side_items);
  RNA_def_property_enum_default(prop, GEO_NODE_CURVE_HANDLE_LEFT | GEO_NODE_CURVE_HANDLE_RIGHT);
  RNA_def_property_ui_text(prop, "Mode", "Whether to update left and right handles");
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_socket_update");
}

static void def_geo_simulation_input(BlenderRNA *brna, StructRNA *srna)
{
  RNA_def_struct_sdna_from(srna, "NodeGeometrySimulationInput", "storage");

  def_common_zone_input(brna, srna);
}

static void def_geo_repeat_input(BlenderRNA *brna, StructRNA *srna)
{
  RNA_def_struct_sdna_from(srna, "NodeGeometryRepeatInput", "storage");

  def_common_zone_input(brna, srna);
}

static void def_geo_foreach_geometry_element_input(BlenderRNA *brna, StructRNA *srna)
{
  RNA_def_struct_sdna_from(srna, "NodeGeometryForeachGeometryElementInput", "storage");

  def_common_zone_input(brna, srna);
}

static void rna_def_geo_simulation_state_item(BlenderRNA *brna)
{
  PropertyRNA *prop;

  StructRNA *srna = RNA_def_struct(brna, "SimulationStateItem", nullptr);
  RNA_def_struct_ui_text(srna, "Simulation Item", "");
  RNA_def_struct_sdna(srna, "NodeSimulationItem");

  rna_def_node_item_array_socket_item_common(srna, "SimulationItemsAccessor", true);

  prop = RNA_def_property(srna, "attribute_domain", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, rna_enum_attribute_domain_items);
  RNA_def_property_enum_funcs(
      prop, nullptr, nullptr, "rna_GeometryNodeAttributeDomain_attribute_domain_itemf");
  RNA_def_property_ui_text(
      prop,
      "Attribute Domain",
      "Domain where the field is captured if it is not already an attribute-field");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(
      prop, NC_NODE | NA_EDITED, "rna_Node_ItemArray_item_update<SimulationItemsAccessor>");
}

static void rna_def_geo_simulation_state_items(BlenderRNA *brna)
{
  StructRNA *srna;

  srna = RNA_def_struct(brna, "NodeGeometrySimulationOutputItems", nullptr);
  RNA_def_struct_sdna(srna, "bNode");
  RNA_def_struct_ui_text(srna, "Items", "Collection of simulation items");

  rna_def_node_item_array_new_with_socket_and_name(
      srna, "SimulationStateItem", "SimulationItemsAccessor");
  rna_def_node_item_array_common_functions(srna, "SimulationStateItem", "SimulationItemsAccessor");
}

static void def_geo_simulation_output(BlenderRNA *brna, StructRNA *srna)
{
  PropertyRNA *prop;

  rna_def_geo_simulation_state_item(brna);
  rna_def_geo_simulation_state_items(brna);

  RNA_def_struct_sdna_from(srna, "NodeGeometrySimulationOutput", "storage");

  prop = RNA_def_property(srna, "state_items", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, nullptr, "items", "items_num");
  RNA_def_property_struct_type(prop, "SimulationStateItem");
  RNA_def_property_ui_text(prop, "Items", "");
  RNA_def_property_srna(prop, "NodeGeometrySimulationOutputItems");

  prop = RNA_def_property(srna, "active_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, nullptr, "active_index");
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "active_item", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "SimulationStateItem");
  RNA_def_property_pointer_funcs(prop,
                                 "rna_Node_ItemArray_active_get<SimulationItemsAccessor>",
                                 "rna_Node_ItemArray_active_set<SimulationItemsAccessor>",
                                 nullptr,
                                 nullptr);
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_NO_DEG_UPDATE);
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_update(prop, NC_NODE, nullptr);
}

static void def_geo_merge_layers(BlenderRNA * /*brna*/, StructRNA *srna)
{
  PropertyRNA *prop = RNA_def_property(srna, "mode", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, rna_enum_node_grease_pencil_merge_mode_items);
  RNA_def_property_ui_text(prop, "Mode", "Determines how to choose which layers are merged");
  RNA_def_property_enum_funcs(
      prop, "rna_MergeLayers_mode_get", "rna_MergeLayers_mode_set", nullptr);
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_update");
  RNA_def_property_deprecated(prop, "Replaced by '.inputs[\"Mode\"]'.", 503, 600);
}

static void def_geo_set_grease_pencil_color(BlenderRNA * /*brna*/, StructRNA *srna)
{
  PropertyRNA *prop = RNA_def_property(srna, "mode", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, rna_enum_node_grease_pencil_stroke_type_items);
  RNA_def_property_ui_text(prop, "Mode", "Set the color and opacity for strokes or fills");
  RNA_def_property_enum_funcs(
      prop, "rna_SetGreasePencilColor_mode_get", "rna_SetGreasePencilColor_mode_set", nullptr);
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_update");
  RNA_def_property_deprecated(prop, "Replaced by '.inputs[\"Mode\"]'.", 503, 600);
}

static void def_geo_set_grease_pencil_depth(BlenderRNA * /*brna*/, StructRNA *srna)
{
  PropertyRNA *prop = RNA_def_property(srna, "depth_order", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, rna_enum_stroke_depth_order_items);
  RNA_def_property_ui_text(prop, "Depth Order", "");
  RNA_def_property_enum_funcs(prop,
                              "rna_SetGreasePencilDepth_depth_order_get",
                              "rna_SetGreasePencilDepth_depth_order_set",
                              nullptr);
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_update");
  RNA_def_property_deprecated(prop, "Replaced by '.inputs[\"Depth Order\"]'.", 503, 600);
}

static void rna_def_geo_repeat_item(BlenderRNA *brna)
{
  StructRNA *srna = RNA_def_struct(brna, "RepeatItem", nullptr);
  RNA_def_struct_ui_text(srna, "Repeat Item", "");
  RNA_def_struct_sdna(srna, "NodeRepeatItem");

  rna_def_node_item_array_socket_item_common(srna, "RepeatItemsAccessor", true);
}

static void rna_def_geo_repeat_items(BlenderRNA *brna)
{
  StructRNA *srna;

  srna = RNA_def_struct(brna, "NodeGeometryRepeatOutputItems", nullptr);
  RNA_def_struct_sdna(srna, "bNode");
  RNA_def_struct_ui_text(srna, "Items", "Collection of repeat items");

  rna_def_node_item_array_new_with_socket_and_name(srna, "RepeatItem", "RepeatItemsAccessor");
  rna_def_node_item_array_common_functions(srna, "RepeatItem", "RepeatItemsAccessor");
}

static void def_geo_repeat_output(BlenderRNA *brna, StructRNA *srna)
{
  PropertyRNA *prop;

  rna_def_geo_repeat_item(brna);
  rna_def_geo_repeat_items(brna);

  RNA_def_struct_sdna_from(srna, "NodeGeometryRepeatOutput", "storage");

  prop = RNA_def_property(srna, "repeat_items", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, nullptr, "items", "items_num");
  RNA_def_property_struct_type(prop, "RepeatItem");
  RNA_def_property_ui_text(prop, "Items", "");
  RNA_def_property_srna(prop, "NodeGeometryRepeatOutputItems");

  prop = RNA_def_property(srna, "active_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, nullptr, "active_index");
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "active_item", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "RepeatItem");
  RNA_def_property_pointer_funcs(prop,
                                 "rna_Node_ItemArray_active_get<RepeatItemsAccessor>",
                                 "rna_Node_ItemArray_active_set<RepeatItemsAccessor>",
                                 nullptr,
                                 nullptr);
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_NO_DEG_UPDATE);
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "inspection_index", PROP_INT, PROP_NONE);
  RNA_def_property_ui_range(prop, 0, INT32_MAX, 1, -1);
  RNA_def_property_ui_text(prop,
                           "Inspection Index",
                           "Iteration index that is used by inspection features like the viewer "
                           "node or socket inspection");
  RNA_def_property_update(prop, NC_NODE, "rna_Node_update");
}

static void rna_def_geo_viewer_item(BlenderRNA *brna)
{
  PropertyRNA *prop;

  StructRNA *srna = RNA_def_struct(brna, "NodeGeometryViewerItem", nullptr);
  RNA_def_struct_ui_text(srna, "Viewer Item", "");
  RNA_def_struct_sdna(srna, "NodeGeometryViewerItem");

  rna_def_node_item_array_socket_item_common(srna, "GeoViewerItemsAccessor", true);

  prop = RNA_def_property(srna, "auto_remove", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, nullptr, "flag", NODE_GEO_VIEWER_ITEM_FLAG_AUTO_REMOVE);
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_ui_text(
      prop, "Auto Remove", "Remove the item automatically when it is unlinked");
  RNA_def_property_update(
      prop, NC_NODE | NA_EDITED, "rna_Node_ItemArray_item_update<GeoViewerItemsAccessor>");
}

static void rna_def_geo_viewer_items(BlenderRNA *brna)
{
  StructRNA *srna = RNA_def_struct(brna, "NodeGeometryViewerItems", nullptr);
  RNA_def_struct_sdna(srna, "bNode");
  RNA_def_struct_ui_text(srna, "Items", "Collection of viewer items");

  rna_def_node_item_array_new_with_socket_and_name(
      srna, "NodeGeometryViewerItem", "GeoViewerItemsAccessor");
  rna_def_node_item_array_common_functions(
      srna, "NodeGeometryViewerItem", "GeoViewerItemsAccessor");
}

static void rna_def_geo_viewer(BlenderRNA *brna, StructRNA *srna)
{
  PropertyRNA *prop;

  rna_def_geo_viewer_item(brna);
  rna_def_geo_viewer_items(brna);

  prop = RNA_def_property(srna, "ui_shortcut", PROP_INT, PROP_NONE);
  RNA_def_property_int_sdna(prop, nullptr, "custom1");
  RNA_def_property_int_funcs(prop, nullptr, "rna_Node_Viewer_shortcut_node_set", nullptr);
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_override_flag(prop, PROPOVERRIDE_IGNORE);
  RNA_def_property_int_default(prop, NODE_VIEWER_SHORTCUT_NONE);
  RNA_def_property_update(prop, NC_NODE | ND_DISPLAY, nullptr);

  RNA_def_struct_sdna_from(srna, "NodeGeometryViewer", "storage");

  prop = RNA_def_property(srna, "viewer_items", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, nullptr, "items", "items_num");
  RNA_def_property_struct_type(prop, "NodeGeometryViewerItem");
  RNA_def_property_ui_text(prop, "Viewer Items", "");
  RNA_def_property_srna(prop, "NodeGeometryViewerItems");

  prop = RNA_def_property(srna, "active_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, nullptr, "active_index");
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "active_item", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "NodeGeometryViewerItem");
  RNA_def_property_ui_text(prop, "Active Item", "");
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_NO_DEG_UPDATE);
  RNA_def_property_pointer_funcs(prop,
                                 "rna_Node_ItemArray_active_get<GeoViewerItemsAccessor>",
                                 "rna_Node_ItemArray_active_set<GeoViewerItemsAccessor>",
                                 nullptr,
                                 nullptr);

  prop = RNA_def_property(srna, "domain", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, rna_enum_attribute_domain_with_auto_items);
  RNA_def_property_enum_default(prop, int(bke::AttrDomainSelection::Auto));
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_ui_text(prop, "Domain", "Domain to evaluate fields on");
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_update");
}

static void rna_def_geo_foreach_geometry_element_input_item(BlenderRNA *brna)
{
  StructRNA *srna = RNA_def_struct(brna, "ForeachGeometryElementInputItem", nullptr);
  RNA_def_struct_ui_text(srna, "For Each Geometry Element Item", "");
  RNA_def_struct_sdna(srna, "NodeForeachGeometryElementInputItem");

  rna_def_node_item_array_socket_item_common(
      srna, "ForeachGeometryElementInputItemsAccessor", true);
}

static void rna_def_geo_foreach_geometry_element_input_items(BlenderRNA *brna)
{
  StructRNA *srna;

  srna = RNA_def_struct(brna, "NodeGeometryForeachGeometryElementInputItems", nullptr);
  RNA_def_struct_sdna(srna, "bNode");
  RNA_def_struct_ui_text(srna, "Input Items", "Collection of input items");

  rna_def_node_item_array_new_with_socket_and_name(
      srna, "ForeachGeometryElementInputItem", "ForeachGeometryElementInputItemsAccessor");
  rna_def_node_item_array_common_functions(
      srna, "ForeachGeometryElementInputItem", "ForeachGeometryElementInputItemsAccessor");
}

static void rna_def_geo_foreach_geometry_element_main_item(BlenderRNA *brna)
{
  StructRNA *srna;

  srna = RNA_def_struct(brna, "ForeachGeometryElementMainItem", nullptr);
  RNA_def_struct_ui_text(srna, "For Each Geometry Element Item", "");
  RNA_def_struct_sdna(srna, "NodeForeachGeometryElementMainItem");

  rna_def_node_item_array_socket_item_common(
      srna, "ForeachGeometryElementMainItemsAccessor", true);
}

static void rna_def_geo_foreach_geometry_element_main_items(BlenderRNA *brna)
{
  StructRNA *srna;

  srna = RNA_def_struct(brna, "NodeGeometryForeachGeometryElementMainItems", nullptr);
  RNA_def_struct_sdna(srna, "bNode");
  RNA_def_struct_ui_text(srna, "Main Items", "Collection of main items");

  rna_def_node_item_array_new_with_socket_and_name(
      srna, "ForeachGeometryElementMainItem", "ForeachGeometryElementMainItemsAccessor");
  rna_def_node_item_array_common_functions(
      srna, "ForeachGeometryElementMainItem", "ForeachGeometryElementMainItemsAccessor");
}

static void rna_def_geo_foreach_geometry_element_generation_item(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "ForeachGeometryElementGenerationItem", nullptr);
  RNA_def_struct_ui_text(srna, "For Each Geometry Element Item", "");
  RNA_def_struct_sdna(srna, "NodeForeachGeometryElementGenerationItem");

  rna_def_node_item_array_socket_item_common(
      srna, "ForeachGeometryElementGenerationItemsAccessor", true);

  prop = RNA_def_property(srna, "domain", PROP_ENUM, PROP_NONE);
  RNA_def_property_ui_text(prop, "Domain", "Domain that the field is evaluated on");
  RNA_def_property_enum_items(prop, rna_enum_attribute_domain_items);
  RNA_def_property_update(
      prop,
      NC_NODE | NA_EDITED,
      "rna_Node_ItemArray_item_update<ForeachGeometryElementGenerationItemsAccessor>");
}

static void rna_def_geo_foreach_geometry_element_generation_items(BlenderRNA *brna)
{
  StructRNA *srna;

  srna = RNA_def_struct(brna, "NodeGeometryForeachGeometryElementGenerationItems", nullptr);
  RNA_def_struct_sdna(srna, "bNode");
  RNA_def_struct_ui_text(srna, "Generation Items", "Collection of generation items");

  rna_def_node_item_array_new_with_socket_and_name(
      srna,
      "ForeachGeometryElementGenerationItem",
      "ForeachGeometryElementGenerationItemsAccessor");
  rna_def_node_item_array_common_functions(srna,
                                           "ForeachGeometryElementGenerationItem",
                                           "ForeachGeometryElementGenerationItemsAccessor");
}

static void def_geo_foreach_geometry_element_output(BlenderRNA *brna, StructRNA *srna)
{
  PropertyRNA *prop;

  rna_def_geo_foreach_geometry_element_input_item(brna);
  rna_def_geo_foreach_geometry_element_input_items(brna);

  rna_def_geo_foreach_geometry_element_main_item(brna);
  rna_def_geo_foreach_geometry_element_main_items(brna);

  rna_def_geo_foreach_geometry_element_generation_items(brna);
  rna_def_geo_foreach_geometry_element_generation_item(brna);

  RNA_def_struct_sdna_from(srna, "NodeGeometryForeachGeometryElementOutput", "storage");

  prop = RNA_def_property(srna, "input_items", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, nullptr, "input_items.items", "input_items.items_num");
  RNA_def_property_struct_type(prop, "ForeachGeometryElementInputItem");
  RNA_def_property_srna(prop, "NodeGeometryForeachGeometryElementInputItems");

  prop = RNA_def_property(srna, "main_items", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, nullptr, "main_items.items", "main_items.items_num");
  RNA_def_property_struct_type(prop, "ForeachGeometryElementMainItem");
  RNA_def_property_srna(prop, "NodeGeometryForeachGeometryElementMainItems");

  prop = RNA_def_property(srna, "generation_items", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(
      prop, nullptr, "generation_items.items", "generation_items.items_num");
  RNA_def_property_struct_type(prop, "ForeachGeometryElementGenerationItem");
  RNA_def_property_srna(prop, "NodeGeometryForeachGeometryElementGenerationItems");

  prop = RNA_def_property(srna, "active_input_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, nullptr, "input_items.active_index");
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "active_generation_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, nullptr, "generation_items.active_index");
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "active_main_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, nullptr, "main_items.active_index");
  RNA_def_property_ui_text(prop, "Active Main Item Index", "Index of the active item");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "domain", PROP_ENUM, PROP_NONE);
  RNA_def_property_ui_text(prop, "Domain", "Geometry domain that is iterated over");
  RNA_def_property_enum_items(prop, rna_enum_attribute_domain_items);
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_update");

  prop = RNA_def_property(srna, "inspection_index", PROP_INT, PROP_NONE);
  RNA_def_property_ui_range(prop, 0, INT32_MAX, 1, -1);
  RNA_def_property_ui_text(prop,
                           "Inspection Index",
                           "Iteration index that is used by inspection features like the viewer "
                           "node or socket inspection");
  RNA_def_property_update(prop, NC_NODE, "rna_Node_update");
}

static void rna_def_geo_capture_attribute_item(BlenderRNA *brna)
{
  StructRNA *srna = RNA_def_struct(brna, "NodeGeometryCaptureAttributeItem", nullptr);
  RNA_def_struct_ui_text(srna, "Capture Attribute Item", "");
  RNA_def_struct_sdna(srna, "NodeGeometryAttributeCaptureItem");

  rna_def_node_item_array_socket_item_common(srna, "CaptureAttributeItemsAccessor", false);
  PropertyRNA *prop = RNA_def_property(srna, "data_type", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, rna_enum_attribute_type_items);
  RNA_def_property_enum_funcs(
      prop, nullptr, nullptr, "rna_NodeGeometryCaptureAttributeItem_data_type_itemf");
  RNA_def_property_ui_text(prop, "Data Type", "");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(
      prop, NC_NODE | NA_EDITED, "rna_Node_ItemArray_item_update<CaptureAttributeItemsAccessor>");
}

static void rna_def_geo_capture_attribute_items(BlenderRNA *brna)
{
  StructRNA *srna = RNA_def_struct(brna, "NodeGeometryCaptureAttributeItems", nullptr);
  RNA_def_struct_ui_text(srna, "Items", "Collection of capture attribute items");
  RNA_def_struct_sdna(srna, "bNode");

  rna_def_node_item_array_new_with_socket_and_name(
      srna, "NodeGeometryCaptureAttributeItem", "CaptureAttributeItemsAccessor");
  rna_def_node_item_array_common_functions(
      srna, "NodeGeometryCaptureAttributeItem", "CaptureAttributeItemsAccessor");
}

static void rna_def_geo_capture_attribute(BlenderRNA *brna, StructRNA *srna)
{
  PropertyRNA *prop;

  rna_def_geo_capture_attribute_item(brna);
  rna_def_geo_capture_attribute_items(brna);

  RNA_def_struct_sdna_from(srna, "NodeGeometryAttributeCapture", "storage");

  prop = RNA_def_property(srna, "capture_items", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, nullptr, "capture_items", "capture_items_num");
  RNA_def_property_struct_type(prop, "NodeGeometryCaptureAttributeItem");
  RNA_def_property_ui_text(prop, "Items", "");
  RNA_def_property_srna(prop, "NodeGeometryCaptureAttributeItems");

  prop = RNA_def_property(srna, "active_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, nullptr, "active_index");
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "active_item", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "NodeGeometryCaptureAttributeItem");
  RNA_def_property_pointer_funcs(prop,
                                 "rna_Node_ItemArray_active_get<CaptureAttributeItemsAccessor>",
                                 "rna_Node_ItemArray_active_set<CaptureAttributeItemsAccessor>",
                                 nullptr,
                                 nullptr);
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_NO_DEG_UPDATE);
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "domain", PROP_ENUM, PROP_NONE);
  RNA_def_property_ui_text(prop, "Domain", "Which domain to store the data in");
  RNA_def_property_enum_items(prop, rna_enum_attribute_domain_items);
  RNA_def_property_enum_funcs(
      prop, nullptr, nullptr, "rna_GeometryNodeAttributeDomain_attribute_domain_itemf");
  RNA_def_property_update(prop, NC_NODE, "rna_Node_update");
}

static void rna_def_geo_bake_item(BlenderRNA *brna)
{
  PropertyRNA *prop;

  StructRNA *srna = RNA_def_struct(brna, "NodeGeometryBakeItem", nullptr);
  RNA_def_struct_ui_text(srna, "Bake Item", "");

  rna_def_node_item_array_socket_item_common(srna, "BakeItemsAccessor", true);

  prop = RNA_def_property(srna, "attribute_domain", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, rna_enum_attribute_domain_items);
  RNA_def_property_enum_funcs(
      prop, nullptr, nullptr, "rna_GeometryNodeAttributeDomain_attribute_domain_itemf");
  RNA_def_property_ui_text(
      prop,
      "Attribute Domain",
      "Domain where the field is captured if it is not already an attribute-field");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(
      prop, NC_NODE | NA_EDITED, "rna_Node_ItemArray_item_update<BakeItemsAccessor>");

  prop = RNA_def_property(srna, "is_attribute", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, nullptr, "flag", GEO_NODE_BAKE_ITEM_IS_ATTRIBUTE);
  RNA_def_property_ui_text(prop, "Is Attribute", "Bake item is an attribute stored on a geometry");
  RNA_def_property_update(
      prop, NC_NODE | NA_EDITED, "rna_Node_ItemArray_item_update<BakeItemsAccessor>");
}

static void rna_def_geo_bake_items(BlenderRNA *brna)
{
  StructRNA *srna;

  srna = RNA_def_struct(brna, "NodeGeometryBakeItems", nullptr);
  RNA_def_struct_sdna(srna, "bNode");
  RNA_def_struct_ui_text(srna, "Items", "Collection of bake items");

  rna_def_node_item_array_new_with_socket_and_name(
      srna, "NodeGeometryBakeItem", "BakeItemsAccessor");
  rna_def_node_item_array_common_functions(srna, "NodeGeometryBakeItem", "BakeItemsAccessor");
}

static void rna_def_geo_bake(BlenderRNA *brna, StructRNA *srna)
{
  PropertyRNA *prop;

  rna_def_geo_bake_item(brna);
  rna_def_geo_bake_items(brna);

  RNA_def_struct_sdna_from(srna, "NodeGeometryBake", "storage");

  prop = RNA_def_property(srna, "bake_items", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, nullptr, "items", "items_num");
  RNA_def_property_struct_type(prop, "NodeGeometryBakeItem");
  RNA_def_property_ui_text(prop, "Items", "");
  RNA_def_property_srna(prop, "NodeGeometryBakeItems");

  prop = RNA_def_property(srna, "active_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, nullptr, "active_index");
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "active_item", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "NodeGeometryBakeItem");
  RNA_def_property_pointer_funcs(prop,
                                 "rna_Node_ItemArray_active_get<BakeItemsAccessor>",
                                 "rna_Node_ItemArray_active_set<BakeItemsAccessor>",
                                 nullptr,
                                 nullptr);
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_NO_DEG_UPDATE);
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_update(prop, NC_NODE, nullptr);
}

static void rna_def_rasterize_points_item(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  static const EnumPropertyItem type_items[] = {
      {GEO_NODE_RASTERIZE_POINTS_ITEM_TYPE_SCALAR,
       "SCALAR",
       0,
       "Scalar",
       "Rasterize a scalar attribute"},
      {GEO_NODE_RASTERIZE_POINTS_ITEM_TYPE_VECTOR,
       "VECTOR",
       0,
       "Vector",
       "Rasterize a vector attribute"},
      {0, nullptr, 0, nullptr, nullptr},
  };

  srna = RNA_def_struct(brna, "NodeGeometryRasterizePointsItem", nullptr);
  RNA_def_struct_ui_text(srna, "Rasterize Points Item", "");
  RNA_def_struct_sdna(srna, "NodeGeometryRasterizePointsItem");

  prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
  RNA_def_property_string_funcs(
      prop, nullptr, nullptr, "rna_Node_ItemArray_item_name_set<RasterizePointsItemsAccessor>");
  RNA_def_property_ui_text(prop, "Name", "");
  RNA_def_struct_name_property(srna, prop);
  RNA_def_property_update(
      prop, NC_NODE | NA_EDITED, "rna_Node_ItemArray_item_update<RasterizePointsItemsAccessor>");

  prop = RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, type_items);
  RNA_def_property_ui_text(prop, "Type", "");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(
      prop, NC_NODE | NA_EDITED, "rna_Node_ItemArray_item_update<RasterizePointsItemsAccessor>");
}

static void rna_def_geo_rasterize_points_items(BlenderRNA *brna)
{
  StructRNA *srna;
  FunctionRNA *func;
  PropertyRNA *parm;

  srna = RNA_def_struct(brna, "NodeGeometryRasterizePointsItems", nullptr);
  RNA_def_struct_sdna(srna, "bNode");
  RNA_def_struct_ui_text(srna, "Items", "Collection of grid items");

  func = RNA_def_function(srna, "new", "rna_NodeGeometryRasterizePointsItems_new");
  RNA_def_function_ui_description(func, "Add an a new point attribute item");
  RNA_def_function_flag(func, FUNC_USE_SELF_ID | FUNC_USE_MAIN);
  parm = RNA_def_string(func, "name", nullptr, MAX_NAME, "Name", "");
  RNA_def_parameter_flags(parm, PropertyFlag(0), PARM_REQUIRED);
  /* return value */
  parm = RNA_def_pointer(func, "item", "NodeGeometryRasterizePointsItem", "Item", "New item");
  RNA_def_parameter_flags(parm, PROP_NEVER_NULL, ParameterFlag(0));
  RNA_def_function_return(func, parm);

  rna_def_node_item_array_common_functions(
      srna, "NodeGeometryRasterizePointsItem", "RasterizePointsItemsAccessor");
}

static void def_geo_rasterize_points(BlenderRNA *brna, StructRNA *srna)
{
  PropertyRNA *prop;

  rna_def_rasterize_points_item(brna);
  rna_def_geo_rasterize_points_items(brna);

  RNA_def_struct_sdna_from(srna, "NodeGeometryRasterizePoints", "storage");

  prop = RNA_def_property(srna, "rasterize_items", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, nullptr, "items", "items_num");
  RNA_def_property_struct_type(prop, "NodeGeometryRasterizePointsItem");
  RNA_def_property_ui_text(prop, "Items", "");
  RNA_def_property_srna(prop, "NodeGeometryRasterizePointsItems");

  prop = RNA_def_property(srna, "active_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, nullptr, "active_index");
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "active_item", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "NodeGeometryRasterizePointsItem");
  RNA_def_property_pointer_funcs(prop,
                                 "rna_Node_ItemArray_active_get<RasterizePointsItemsAccessor>",
                                 "rna_Node_ItemArray_active_set<RasterizePointsItemsAccessor>",
                                 nullptr,
                                 nullptr);
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_NO_DEG_UPDATE);
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_update(prop, NC_NODE, nullptr);
}

static void rna_def_index_switch_item(BlenderRNA *brna)
{
  PropertyRNA *prop;

  StructRNA *srna = RNA_def_struct(brna, "IndexSwitchItem", nullptr);
  RNA_def_struct_ui_text(srna, "Index Switch Item", "");
  RNA_def_struct_sdna(srna, "IndexSwitchItem");

  prop = RNA_def_property(srna, "identifier", PROP_INT, PROP_NONE);
  RNA_def_property_ui_range(prop, 0, INT32_MAX, 1, -1);
  RNA_def_property_ui_text(prop, "Identifier", "Consistent identifier used for the item");
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_update(prop, NC_NODE, "rna_Node_update");
}

static void rna_def_geo_index_switch_items(BlenderRNA *brna)
{
  StructRNA *srna;
  FunctionRNA *func;
  PropertyRNA *parm;

  srna = RNA_def_struct(brna, "NodeIndexSwitchItems", nullptr);
  RNA_def_struct_sdna(srna, "bNode");
  RNA_def_struct_ui_text(srna, "Items", "Collection of index_switch items");

  func = RNA_def_function(srna, "new", "rna_NodeIndexSwitchItems_new");
  RNA_def_function_ui_description(func, "Add an item at the end");
  RNA_def_function_flag(func, FUNC_USE_SELF_ID | FUNC_USE_MAIN);
  /* Return value. */
  parm = RNA_def_pointer(func, "item", "IndexSwitchItem", "Item", "New item");
  RNA_def_parameter_flags(parm, PROP_NEVER_NULL, ParameterFlag(0));
  RNA_def_function_return(func, parm);

  rna_def_node_item_array_common_functions(srna, "IndexSwitchItem", "IndexSwitchItemsAccessor");
}

static void def_geo_index_switch(BlenderRNA *brna, StructRNA *srna)
{
  PropertyRNA *prop;

  rna_def_index_switch_item(brna);
  rna_def_geo_index_switch_items(brna);

  RNA_def_struct_sdna_from(srna, "NodeIndexSwitch", "storage");

  prop = RNA_def_property(srna, "index_switch_items", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, nullptr, "items", "items_num");
  RNA_def_property_struct_type(prop, "IndexSwitchItem");
  RNA_def_property_ui_text(prop, "Items", "");
  RNA_def_property_srna(prop, "NodeIndexSwitchItems");
}

static void rna_def_combine_list_item(BlenderRNA *brna)
{
  PropertyRNA *prop;

  StructRNA *srna = RNA_def_struct(brna, "CombineListItem", nullptr);
  RNA_def_struct_ui_text(srna, "Combine List Item", "");
  RNA_def_struct_sdna(srna, "CombineListItem");

  prop = RNA_def_property(srna, "identifier", PROP_INT, PROP_NONE);
  RNA_def_property_ui_range(prop, 0, INT32_MAX, 1, -1);
  RNA_def_property_ui_text(prop, "Identifier", "Consistent identifier used for the item");
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_update(prop, NC_NODE, "rna_Node_update");
}

static void rna_def_geo_combine_list_items(BlenderRNA *brna)
{
  StructRNA *srna;
  FunctionRNA *func;
  PropertyRNA *parm;

  srna = RNA_def_struct(brna, "NodeCombineListItems", nullptr);
  RNA_def_struct_sdna(srna, "bNode");
  RNA_def_struct_ui_text(srna, "Items", "Collection of combine list items");

  func = RNA_def_function(srna, "new", "rna_NodeCombineListItems_new");
  RNA_def_function_ui_description(func, "Add an item at the end");
  RNA_def_function_flag(func, FUNC_USE_SELF_ID | FUNC_USE_MAIN);

  parm = RNA_def_pointer(func, "item", "CombineListItem", "Item", "New item");
  RNA_def_function_return(func, parm);

  rna_def_node_item_array_common_functions(srna, "CombineListItem", "CombineListItemsAccessor");
}

static void def_geo_combine_list(BlenderRNA *brna, StructRNA *srna)
{
  PropertyRNA *prop;

  rna_def_combine_list_item(brna);
  rna_def_geo_combine_list_items(brna);

  RNA_def_struct_sdna_from(srna, "NodeCombineList", "storage");

  prop = RNA_def_property(srna, "combine_list_items", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, nullptr, "items", "items_num");
  RNA_def_property_struct_type(prop, "CombineListItem");
  RNA_def_property_ui_text(prop, "Items", "");
  RNA_def_property_srna(prop, "NodeCombineListItems");
}

static void rna_def_geo_field_to_grid_item(BlenderRNA *brna)
{
  PropertyRNA *prop;

  StructRNA *srna = RNA_def_struct(brna, "GeometryNodeFieldToGridItem", nullptr);
  RNA_def_struct_ui_text(srna, "Field to Grid Item", "");
  RNA_def_struct_sdna(srna, "GeometryNodeFieldToGridItem");

  rna_def_node_item_array_socket_item_common(srna, "FieldToGridItemsAccessor", false);
  prop = RNA_def_property(srna, "data_type", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, rna_enum_node_socket_data_type_items);
  RNA_def_property_enum_funcs(prop, nullptr, nullptr, "rna_NodeFieldToGridItem_data_type_itemf");
  RNA_def_property_ui_text(prop, "Data Type", "");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(
      prop, NC_NODE | NA_EDITED, "rna_Node_ItemArray_item_update<FieldToGridItemsAccessor>");

  prop = RNA_def_property(srna, "identifier", PROP_INT, PROP_NONE);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
}

static void rna_def_geo_field_to_grid_items(BlenderRNA *brna)
{
  StructRNA *srna = RNA_def_struct(brna, "GeometryNodeFieldToGridItems", nullptr);
  RNA_def_struct_ui_text(srna, "Items", "Collection of field to grid items");
  RNA_def_struct_sdna(srna, "bNode");

  rna_def_node_item_array_new_with_socket_and_name(
      srna, "GeometryNodeFieldToGridItem", "FieldToGridItemsAccessor");
  rna_def_node_item_array_common_functions(
      srna, "GeometryNodeFieldToGridItem", "FieldToGridItemsAccessor");
}

static void rna_def_geo_closure_to_list_item(BlenderRNA *brna)
{
  PropertyRNA *prop;

  StructRNA *srna = RNA_def_struct(brna, "GeometryNodeClosureToListItem", nullptr);
  RNA_def_struct_ui_text(srna, "Closure to List Item", "");
  RNA_def_struct_sdna(srna, "GeometryNodeClosureToListItem");

  rna_def_node_item_array_socket_item_common(srna, "ClosureToListItemsAccessor", true);

  prop = RNA_def_property(srna, "structure_type", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, rna_enum_node_socket_structure_type_items);
  RNA_def_property_enum_funcs(
      prop, nullptr, nullptr, "rna_GeometryNodeClosureToListItem_structure_type_itemf");

  prop = RNA_def_property(srna, "identifier", PROP_INT, PROP_NONE);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
}

static void rna_def_geo_closure_to_list_items(BlenderRNA *brna)
{
  StructRNA *srna = RNA_def_struct(brna, "GeometryNodeClosureToListItems", nullptr);
  RNA_def_struct_ui_text(srna, "Items", "Collection of closure to list items");
  RNA_def_struct_sdna(srna, "bNode");

  rna_def_node_item_array_new_with_socket_and_name(
      srna, "GeometryNodeClosureToListItem", "ClosureToListItemsAccessor");
  rna_def_node_item_array_common_functions(
      srna, "GeometryNodeClosureToListItem", "ClosureToListItemsAccessor");
}

static void def_geo_closure_to_list(BlenderRNA *brna, StructRNA *srna)
{
  PropertyRNA *prop;

  rna_def_geo_closure_to_list_item(brna);
  rna_def_geo_closure_to_list_items(brna);

  RNA_def_struct_sdna_from(srna, "GeometryNodeClosureToList", "storage");

  prop = RNA_def_property(srna, "list_items", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, nullptr, "items", "items_num");
  RNA_def_property_struct_type(prop, "GeometryNodeClosureToListItem");
  RNA_def_property_ui_text(prop, "Items", "");
  RNA_def_property_srna(prop, "GeometryNodeClosureToListItems");

  prop = RNA_def_property(srna, "active_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, nullptr, "active_index");
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "active_item", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "GeometryNodeClosureToListItem");
  RNA_def_property_pointer_funcs(prop,
                                 "rna_Node_ItemArray_active_get<ClosureToListItemsAccessor>",
                                 "rna_Node_ItemArray_active_set<ClosureToListItemsAccessor>",
                                 nullptr,
                                 nullptr);
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_NO_DEG_UPDATE);
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_update(prop, NC_NODE, nullptr);
}

static void def_geo_field_to_grid(BlenderRNA *brna, StructRNA *srna)
{
  PropertyRNA *prop;

  rna_def_geo_field_to_grid_item(brna);
  rna_def_geo_field_to_grid_items(brna);

  RNA_def_struct_sdna_from(srna, "GeometryNodeFieldToGrid", "storage");

  prop = RNA_def_property(srna, "grid_items", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, nullptr, "items", "items_num");
  RNA_def_property_struct_type(prop, "GeometryNodeFieldToGridItem");
  RNA_def_property_ui_text(prop, "Items", "");
  RNA_def_property_srna(prop, "GeometryNodeFieldToGridItems");

  prop = RNA_def_property(srna, "active_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, nullptr, "active_index");
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "active_item", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "GeometryNodeFieldToGridItem");
  RNA_def_property_pointer_funcs(prop,
                                 "rna_Node_ItemArray_active_get<FieldToGridItemsAccessor>",
                                 "rna_Node_ItemArray_active_set<FieldToGridItemsAccessor>",
                                 nullptr,
                                 nullptr);
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_NO_DEG_UPDATE);
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "data_type", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, rna_enum_node_socket_data_type_items);
  RNA_def_property_enum_funcs(prop, nullptr, nullptr, "rna_NodeFieldToGridItem_data_type_itemf");
  RNA_def_property_ui_text(prop, "Data Type", "Data type for topology grid");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_socket_update");
}

static void rna_def_geo_field_to_list_item(BlenderRNA *brna)
{
  PropertyRNA *prop;

  StructRNA *srna = RNA_def_struct(brna, "GeometryNodeFieldToListItem", nullptr);
  RNA_def_struct_ui_text(srna, "Field to List Item", "");
  RNA_def_struct_sdna(srna, "GeometryNodeFieldToListItem");

  rna_def_node_item_array_socket_item_common(srna, "FieldToListItemsAccessor", true);

  prop = RNA_def_property(srna, "identifier", PROP_INT, PROP_NONE);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
}

static void rna_def_geo_field_to_list_items(BlenderRNA *brna)
{
  StructRNA *srna = RNA_def_struct(brna, "GeometryNodeFieldToListItems", nullptr);
  RNA_def_struct_ui_text(srna, "Items", "Collection of field to list items");
  RNA_def_struct_sdna(srna, "bNode");

  rna_def_node_item_array_new_with_socket_and_name(
      srna, "GeometryNodeFieldToListItem", "FieldToListItemsAccessor");
  rna_def_node_item_array_common_functions(
      srna, "GeometryNodeFieldToListItem", "FieldToListItemsAccessor");
}

static void def_geo_field_to_list(BlenderRNA *brna, StructRNA *srna)
{
  PropertyRNA *prop;

  rna_def_geo_field_to_list_item(brna);
  rna_def_geo_field_to_list_items(brna);

  RNA_def_struct_sdna_from(srna, "GeometryNodeFieldToList", "storage");

  prop = RNA_def_property(srna, "list_items", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, nullptr, "items", "items_num");
  RNA_def_property_struct_type(prop, "GeometryNodeFieldToListItem");
  RNA_def_property_ui_text(prop, "Items", "");
  RNA_def_property_srna(prop, "GeometryNodeFieldToListItems");

  prop = RNA_def_property(srna, "active_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, nullptr, "active_index");
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_flag(prop, PROP_NO_DEG_UPDATE);
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "active_item", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "GeometryNodeFieldToListItem");
  RNA_def_property_pointer_funcs(prop,
                                 "rna_Node_ItemArray_active_get<FieldToListItemsAccessor>",
                                 "rna_Node_ItemArray_active_set<FieldToListItemsAccessor>",
                                 nullptr,
                                 nullptr);
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_NO_DEG_UPDATE);
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_update(prop, NC_NODE, nullptr);
}

static void def_geo_curve_handle_type_selection(BlenderRNA * /*brna*/, StructRNA *srna)
{
  PropertyRNA *prop;

  RNA_def_struct_sdna_from(srna, "NodeGeometryCurveSelectHandles", "storage");

  prop = RNA_def_property(srna, "handle_type", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_sdna(prop, nullptr, "handle_type");
  RNA_def_property_ui_text(prop, "Handle Type", "");
  RNA_def_property_enum_items(prop, rna_node_geometry_curve_handle_type_items);
  RNA_def_property_enum_default(prop, GEO_NODE_CURVE_HANDLE_AUTO);
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_socket_update");

  prop = RNA_def_property(srna, "mode", PROP_ENUM, PROP_NONE);
  RNA_def_property_flag(prop, PROP_ENUM_FLAG);
  RNA_def_property_enum_items(prop, rna_enum_node_geometry_curve_handle_side_items);
  RNA_def_property_enum_default(prop, GEO_NODE_CURVE_HANDLE_LEFT | GEO_NODE_CURVE_HANDLE_RIGHT);
  RNA_def_property_ui_text(prop, "Mode", "Whether to check the type of left and right handles");
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_socket_update");
}

static void def_geo_sample_index(BlenderRNA * /*brna*/, StructRNA *srna)
{
  PropertyRNA *prop;

  RNA_def_struct_sdna_from(srna, "NodeGeometrySampleIndex", "storage");

  prop = RNA_def_property(srna, "data_type", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, rna_enum_attribute_type_items);
  RNA_def_property_enum_funcs(
      prop, nullptr, nullptr, "rna_GeometryNodeAttributeType_type_with_socket_itemf");
  RNA_def_property_enum_default(prop, CD_PROP_FLOAT);
  RNA_def_property_ui_text(prop, "Data Type", "");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_socket_update");

  prop = RNA_def_property(srna, "domain", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, rna_enum_attribute_domain_items);
  RNA_def_property_enum_funcs(
      prop, nullptr, nullptr, "rna_GeometryNodeAttributeDomain_attribute_domain_itemf");
  RNA_def_property_enum_default(prop, int(bke::AttrDomain::Point));
  RNA_def_property_ui_text(prop, "Domain", "");
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_update");

  prop = RNA_def_property(srna, "clamp", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_ui_text(prop,
                           "Clamp",
                           "Clamp the indices to the size of the attribute domain instead of "
                           "outputting a default value for invalid indices");
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_update");
}

static void def_geo_input_material(BlenderRNA * /*brna*/, StructRNA *srna)
{
  PropertyRNA *prop;

  prop = RNA_def_property(srna, "material", PROP_POINTER, PROP_NONE);
  RNA_def_property_pointer_sdna(prop, nullptr, "id");
  RNA_def_property_struct_type(prop, "Material");
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_ID_REFCOUNT);
  RNA_def_property_override_flag(prop, PROPOVERRIDE_OVERRIDABLE_LIBRARY);
  RNA_def_property_ui_text(prop, "Material", "");
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_update");
}

static void def_geo_input_collection(BlenderRNA * /*brna*/, StructRNA *srna)
{
  PropertyRNA *prop;

  prop = RNA_def_property(srna, "collection", PROP_POINTER, PROP_NONE);
  RNA_def_property_pointer_sdna(prop, nullptr, "id");
  RNA_def_property_struct_type(prop, "Collection");
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_ID_REFCOUNT);
  RNA_def_property_override_flag(prop, PROPOVERRIDE_OVERRIDABLE_LIBRARY);
  RNA_def_property_ui_text(prop, "Collection", "");
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_update");
}

static void def_geo_input_font(BlenderRNA * /*brna*/, StructRNA *srna)
{
  PropertyRNA *prop;

  prop = RNA_def_property(srna, "font", PROP_POINTER, PROP_NONE);
  RNA_def_property_pointer_sdna(prop, nullptr, "id");
  RNA_def_property_struct_type(prop, "VectorFont");
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_ID_REFCOUNT);
  RNA_def_property_override_flag(prop, PROPOVERRIDE_OVERRIDABLE_LIBRARY);
  RNA_def_property_ui_text(prop, "Font", "");
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_update");
}

static void def_geo_input_normal(BlenderRNA * /*brna*/, StructRNA *srna)
{
  PropertyRNA *prop = RNA_def_property(srna, "legacy_corner_normals", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, nullptr, "custom1", 1);
  RNA_def_property_ui_text(
      prop,
      "Flat Corner Normals",
      "Always use face normals for the face corner domain, matching old behavior of the node");
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_update");
}

static void def_geo_input_object(BlenderRNA * /*brna*/, StructRNA *srna)
{
  PropertyRNA *prop;

  prop = RNA_def_property(srna, "object", PROP_POINTER, PROP_NONE);
  RNA_def_property_pointer_sdna(prop, nullptr, "id");
  RNA_def_property_struct_type(prop, "Object");
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_ID_REFCOUNT);
  RNA_def_property_override_flag(prop, PROPOVERRIDE_OVERRIDABLE_LIBRARY);
  RNA_def_property_ui_text(prop, "Object", "");
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_update");
}

static void def_geo_image(BlenderRNA * /*brna*/, StructRNA *srna)
{
  PropertyRNA *prop;

  prop = RNA_def_property(srna, "image", PROP_POINTER, PROP_NONE);
  RNA_def_property_pointer_sdna(prop, nullptr, "id");
  RNA_def_property_struct_type(prop, "Image");
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_ID_REFCOUNT);
  RNA_def_property_ui_text(prop, "Image", "");
  RNA_def_property_update(prop, NC_NODE | NA_EDITED, "rna_Node_update");
  RNA_def_property_pointer_funcs(
      prop, nullptr, nullptr, nullptr, "rna_Image_no_renderresult_or_viewer_poll");
}

static void rna_def_geo_menu_switch_item(BlenderRNA *brna)
{
  PropertyRNA *prop;

  StructRNA *srna = RNA_def_struct(brna, "NodeEnumItem", nullptr);
  RNA_def_struct_ui_text(srna, "Enum Item", "");

  prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
  RNA_def_property_string_funcs(
      prop, nullptr, nullptr, "rna_Node_ItemArray_item_name_set<MenuSwitchItemsAccessor>");
  RNA_def_property_ui_text(prop, "Name", "");
  RNA_def_struct_name_property(srna, prop);
  RNA_def_property_update(
      prop, NC_NODE | NA_EDITED, "rna_Node_ItemArray_item_update<MenuSwitchItemsAccessor>");

  prop = RNA_def_property(srna, "description", PROP_STRING, PROP_NONE);
  RNA_def_property_string_sdna(prop, nullptr, "description");
  RNA_def_property_ui_text(prop, "Description", "");
  RNA_def_property_update(
      prop, NC_NODE | NA_EDITED, "rna_Node_ItemArray_item_update<MenuSwitchItemsAccessor>");
}

static void rna_def_geo_menu_switch_items(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *parm;
  FunctionRNA *func;

  srna = RNA_def_struct(brna, "NodeMenuSwitchItems", nullptr);
  RNA_def_struct_sdna(srna, "bNode");
  RNA_def_struct_ui_text(
      srna, "Enum Definition Items", "Collection of items that make up an enum");

  func = RNA_def_function(srna, "new", "rna_NodeMenuSwitchItems_new");
  RNA_def_function_ui_description(func, "Add an a new enum item");
  RNA_def_function_flag(func, FUNC_USE_SELF_ID | FUNC_USE_MAIN);
  parm = RNA_def_string(func, "name", nullptr, MAX_NAME, "Name", "");
  RNA_def_parameter_flags(parm, PropertyFlag(0), PARM_REQUIRED);
  /* return value */
  parm = RNA_def_pointer(func, "item", "NodeEnumItem", "Item", "New item");
  RNA_def_parameter_flags(parm, PROP_NEVER_NULL, ParameterFlag(0));
  RNA_def_function_return(func, parm);

  rna_def_node_item_array_common_functions(srna, "NodeEnumItem", "MenuSwitchItemsAccessor");
}

static void def_geo_menu_switch(BlenderRNA *brna, StructRNA *srna)
{
  PropertyRNA *prop;

  rna_def_geo_menu_switch_item(brna);
  rna_def_geo_menu_switch_items(brna);

  RNA_def_struct_sdna_from(srna, "NodeMenuSwitch", "storage");

  prop = RNA_def_property(srna, "enum_items", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(
      prop, nullptr, "enum_definition.items_array", "enum_definition.items_num");
  RNA_def_property_struct_type(prop, "NodeEnumItem");
  RNA_def_property_ui_text(prop, "Items", "");
  RNA_def_property_srna(prop, "NodeMenuSwitchItems");

  prop = RNA_def_property(srna, "active_index", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, nullptr, "enum_definition.active_index");
  RNA_def_property_ui_text(prop, "Active Item Index", "Index of the active item");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_NODE, nullptr);

  prop = RNA_def_property(srna, "active_item", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "NodeEnumItem");
  RNA_def_property_pointer_funcs(prop,
                                 "rna_Node_ItemArray_active_get<MenuSwitchItemsAccessor>",
                                 "rna_Node_ItemArray_active_set<MenuSwitchItemsAccessor>",
                                 nullptr,
                                 nullptr);
  RNA_def_property_flag(prop, PROP_EDITABLE);
  RNA_def_property_ui_text(prop, "Active Item", "Active item");
  RNA_def_property_update(prop, NC_NODE, nullptr);

  /* This exists only for backward compatibility. */
  prop = RNA_def_property(srna, "enum_definition", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "Node");
  RNA_def_property_pointer_funcs(
      prop, "rna_NodeMenuSwitch_enum_definition_get", nullptr, nullptr, nullptr);
  RNA_def_property_override_flag(prop, PROPOVERRIDE_NO_COMPARISON);
  RNA_def_property_ui_text(prop,
                           "Enum Definition (deprecated)",
                           "The enum definition can now be accessed directly on the node. This "
                           "exists for backward compatibility.");
}

void RNA_def_nodes_geometry(BlenderRNA *brna)
{
  /* BFA - override node type icons: Blender's helper plus an icon argument, the icon is always
   * set so nodes without a BFA icon show none. */
  const auto define = [&](const char *base_name,
                          const char *struct_name,
                          void (*func)(BlenderRNA *, StructRNA *) = nullptr,
                          const int ui_icon = ICON_NONE) {
    StructRNA *srna = define_specific_node(brna, struct_name, base_name);
    if (func) {
      func(brna, srna);
    }
    RNA_def_struct_ui_icon(srna, ui_icon);
  };

  /* clang-format off */

  define("GeometryNode", "GeometryNodeAccumulateField", nullptr, ICON_ACCUMULATE);
  define("GeometryNode", "GeometryNodeAttributeDomainSize", nullptr, ICON_DOMAIN_SIZE);
  define("GeometryNode", "GeometryNodeAttributeStatistic", nullptr, ICON_ATTRIBUTE_STATISTIC);
  define("GeometryNode", "GeometryNodeBake", rna_def_geo_bake, ICON_BAKE);
  define("GeometryNode", "GeometryNodeBlurAttribute", nullptr, ICON_BLUR_ATTRIBUTE);
  define("GeometryNode", "GeometryNodeBoneInfo", nullptr, ICON_BONE_DATA);
  define("GeometryNode", "GeometryNodeBoundBox", nullptr, ICON_PIVOT_BOUNDBOX);
  define("GeometryNode", "GeometryNodeCameraInfo", nullptr, ICON_CAMERA_DATA);
  define("GeometryNode", "GeometryNodeCaptureAttribute", rna_def_geo_capture_attribute, ICON_ATTRIBUTE_CAPTURE);
  define("GeometryNode", "GeometryNodeClosureToList", def_geo_closure_to_list, ICON_NODE_CLOSURETOLIST);
  define("GeometryNode", "GeometryNodeClusterByConnected", nullptr, ICON_NODE_CLUSTERBYCONNECTED);
  define("GeometryNode", "GeometryNodeClusterByDistance", nullptr, ICON_NODE_CLUSTERBYDISTANCE);
  define("GeometryNode", "GeometryNodeCollectionChildren", nullptr, ICON_COLLECTION_CHILDREN);
  define("GeometryNode", "GeometryNodeCollectionInfo", nullptr, ICON_COLLECTION_INFO);
  define("GeometryNode", "GeometryNodeConstructCurves", nullptr, ICON_NODE_CONSTRUCT_CURVES); /*BFA - icon*/
  define("GeometryNode", "GeometryNodeConvexHull", nullptr, ICON_CONVEXHULL);
  define("GeometryNode", "GeometryNodeCornersOfEdge", nullptr, ICON_CORNERS_OF_EDGE);
  define("GeometryNode", "GeometryNodeCornersOfFace", nullptr, ICON_CORNERS_OF_FACE);
  define("GeometryNode", "GeometryNodeCornersOfVertex", nullptr, ICON_CORNERS_OF_VERTEX);
  define("GeometryNode", "GeometryNodeCubeGridTopology", nullptr, ICON_CUBE_GRID_TOPOLOGY);
  define("GeometryNode", "GeometryNodeCurveArc", nullptr, ICON_CURVE_ARC);
  define("GeometryNode", "GeometryNodeCurveEndpointSelection", nullptr, ICON_SELECT_LAST);
  define("GeometryNode", "GeometryNodeCurveHandleTypeSelection", def_geo_curve_handle_type_selection, ICON_SELECT_HANDLETYPE);
  define("GeometryNode", "GeometryNodeCurveLength", nullptr, ICON_PARTICLEBRUSH_LENGTH);
  define("GeometryNode", "GeometryNodeCurveOfPoint", nullptr, ICON_CURVE_OF_POINT);
  define("GeometryNode", "GeometryNodeCurvePrimitiveBezierSegment", nullptr, ICON_CURVE_BEZCURVE);
  define("GeometryNode", "GeometryNodeCurvePrimitiveCircle", nullptr, ICON_CURVE_BEZCIRCLE);
  define("GeometryNode", "GeometryNodeCurvePrimitiveLine", nullptr, ICON_CURVE_LINE);
  define("GeometryNode", "GeometryNodeCurvePrimitiveQuadrilateral", nullptr, ICON_CURVE_QUADRILATERAL);
  define("GeometryNode", "GeometryNodeCurveQuadraticBezier", nullptr, ICON_CURVE_NCURVE);
  define("GeometryNode", "GeometryNodeCurveSetHandles", def_geo_curve_set_handle_type, ICON_HANDLE_AUTO);
  define("GeometryNode", "GeometryNodeCurveSpiral", nullptr, ICON_CURVE_SPIRAL);
  define("GeometryNode", "GeometryNodeCurveSplineType", nullptr, ICON_SPLINE_TYPE);
  define("GeometryNode", "GeometryNodeCurveStar", nullptr, ICON_CURVE_STAR);
  define("GeometryNode", "GeometryNodeCurvesToGreasePencil", nullptr, ICON_OUTLINER_OB_GREASEPENCIL);
  define("GeometryNode", "GeometryNodeCurveToMesh", nullptr, ICON_OUTLINER_OB_MESH);
  define("GeometryNode", "GeometryNodeCurveToPoints", nullptr, ICON_POINTCLOUD_DATA);
  define("GeometryNode", "GeometryNodeDeformCurvesOnSurface", nullptr, ICON_DEFORM_CURVES);
  define("GeometryNode", "GeometryNodeDelaunayTriangulation");
  define("GeometryNode", "GeometryNodeDeleteGeometry", nullptr, ICON_DELETE);
  define("GeometryNode", "GeometryNodeDistributePointsInGrid", nullptr, ICON_NODE_DISTRIBUTEPOINTSINGRID);
  define("GeometryNode", "GeometryNodeDistributePointsInVolume", nullptr, ICON_VOLUME_DISTRIBUTE);
  define("GeometryNode", "GeometryNodeDistributePointsOnFaces", def_geo_distribute_points_on_faces, ICON_POINT_DISTRIBUTE);
  define("GeometryNode", "GeometryNodeDualMesh", nullptr, ICON_DUAL_MESH);
  define("GeometryNode", "GeometryNodeDuplicateElements", nullptr, ICON_DUPLICATE);
  define("GeometryNode", "GeometryNodeEdgePathsToCurves", nullptr, ICON_EDGE_PATHS_TO_CURVES);
  define("GeometryNode", "GeometryNodeEdgePathsToSelection", nullptr, ICON_EDGE_PATH_TO_SELECTION);
  define("GeometryNode", "GeometryNodeEdgesOfCorner", nullptr, ICON_EDGES_OF_CORNER);
  define("GeometryNode", "GeometryNodeEdgesOfVertex", nullptr, ICON_EDGES_OF_VERTEX);
  define("GeometryNode", "GeometryNodeEdgesToFaceGroups", nullptr, ICON_FACEGROUP);
  define("GeometryNode", "GeometryNodeExtrudeMesh", nullptr, ICON_EXTRUDE_REGION);
  define("GeometryNode", "GeometryNodeFaceOfCorner", nullptr, ICON_FACE_OF_CORNER);
  define("GeometryNode", "GeometryNodeFieldAtIndex", nullptr, ICON_NODE_FIELDATINDEX);
  define("GeometryNode", "GeometryNodeFieldAverage", nullptr, ICON_AVERAGE);
  define("GeometryNode", "GeometryNodeFieldMinAndMax", nullptr, ICON_MINMAX);
  define("GeometryNode", "GeometryNodeFieldOnDomain", nullptr, ICON_FIELD_DOMAIN);
  define("GeometryNode", "GeometryNodeFieldToGrid", def_geo_field_to_grid, ICON_NODE_FIELDTOGRID);
  define("GeometryNode", "GeometryNodeFieldToList", def_geo_field_to_list, ICON_NODE_FIELDTOLIST);
  define("GeometryNode", "GeometryNodeFieldVariance", nullptr, ICON_VARIANCE);
  define("GeometryNode", "GeometryNodeFillCurve", nullptr, ICON_CURVE_FILL);
  define("GeometryNode", "GeometryNodeFilletCurve", nullptr, ICON_CURVE_FILLET);
  define("GeometryNode", "GeometryNodeFilterList", nullptr, ICON_NODE_FILTERLIST);
  define("GeometryNode", "GeometryNodeFlipFaces", nullptr, ICON_FLIP_NORMALS);
  define("GeometryNode", "GeometryNodeForeachGeometryElementInput", def_geo_foreach_geometry_element_input, ICON_FOR_EACH);
  define("GeometryNode", "GeometryNodeForeachGeometryElementOutput", def_geo_foreach_geometry_element_output, ICON_FOR_EACH);
  define("GeometryNode", "GeometryNodeGeometryToInstance", nullptr, ICON_GEOMETRY_INSTANCE);
  define("GeometryNode", "GeometryNodeGetAttributeNames", nullptr, ICON_GET_ATTRIBUTE_NAMES); /*BFA - icon*/
  define("GeometryNode", "GeometryNodeGetGeometryBundle", nullptr, ICON_NODE_BUNDLE_GET);
  define("GeometryNode", "GeometryNodeGetGeometryComponent", nullptr, ICON_NODE_GETGEOMETRYCOMPONENT);
  define("GeometryNode", "GeometryNodeGetGridNames", nullptr, ICON_NODE_GET_GRID_NAMES); /*BFA - icon*/
  define("GeometryNode", "GeometryNodeGetNamedGrid", nullptr, ICON_NODE_GET_NAMED_GRID);
  define("GeometryNode", "GeometryNodeGizmoDial", nullptr, ICON_DIAL_GIZMO);
  define("GeometryNode", "GeometryNodeGizmoLinear", nullptr, ICON_LINEAR_GIZMO);
  define("GeometryNode", "GeometryNodeGizmoTransform", rna_def_geo_gizmo_transform, ICON_TRANSFORM_GIZMO);
  define("GeometryNode", "GeometryNodeGreasePencilColor", nullptr, ICON_NODE_GP_COLOR);
  define("GeometryNode", "GeometryNodeGreasePencilDrawTime", nullptr, ICON_NODE_GP_DRAWTIME);
  define("GeometryNode", "GeometryNodeGreasePencilFillID", nullptr, ICON_NODE_GP_FILLID);
  define("GeometryNode", "GeometryNodeGreasePencilOpacity", nullptr, ICON_GP_OPACITY);
  define("GeometryNode", "GeometryNodeGreasePencilStrokeSoftness", nullptr, ICON_NODE_GP_STROKESOFTNESS);
  define("GeometryNode", "GeometryNodeGreasePencilStrokeVisibility", nullptr, ICON_NODE_GP_STROKEVISIBILITY);
  define("GeometryNode", "GeometryNodeGreasePencilToCurves", nullptr, ICON_OUTLINER_OB_CURVES);
  define("GeometryNode", "GeometryNodeGridAdvect", nullptr, ICON_NODE_ADVECTGRID);
  define("GeometryNode", "GeometryNodeGridCurl", nullptr, ICON_NODE_GRIDCURL);
  define("GeometryNode", "GeometryNodeGridDeactivateVoxels", nullptr, ICON_NODE_DEACTIVATE_VOXEL);
  define("GeometryNode", "GeometryNodeGridDilateAndErode", nullptr, ICON_NODE_GRIDERODE);
  define("GeometryNode", "GeometryNodeGridDivergence", nullptr, ICON_NODE_GRIDDIVERGENCE);
  define("GeometryNode", "GeometryNodeGridGradient", nullptr, ICON_NODE_GRIDGRADIENT);
  define("GeometryNode", "GeometryNodeGridInfo", nullptr, ICON_NODE_GRID_INFO);
  define("GeometryNode", "GeometryNodeGridLaplacian", nullptr, ICON_NODE_GRIDLAPLACIAN);
  define("GeometryNode", "GeometryNodeGridMean", nullptr, ICON_NODE_GRIDMEAN);
  define("GeometryNode", "GeometryNodeGridMedian", nullptr, ICON_NODE_GRIDMEDIAN);
  define("GeometryNode", "GeometryNodeGridPrune", nullptr, ICON_NODE_PRUNEGRID);
  define("GeometryNode", "GeometryNodeGridClip", nullptr, ICON_CLIPPINGBORDER);
  define("GeometryNode", "GeometryNodeGridSolvePoisson", nullptr, ICON_NODE_GRIDSOLVEPOISSON); /*BFA - icon*/
  define("GeometryNode", "GeometryNodeGridToMesh", nullptr, ICON_NODE_GRIDTOMESH);
  define("GeometryNode", "GeometryNodeGridToPoints", nullptr, ICON_MESH_TO_POINTS);
  define("GeometryNode", "GeometryNodeGridTopologyBoolean", nullptr, ICON_NODE_GRIDTOPLOGYBOOLEAN);
  define("GeometryNode", "GeometryNodeGridVoxelize", nullptr, ICON_NODE_VOXELIZEGRID);
  define("GeometryNode", "GeometryNodeImageInfo", nullptr, ICON_IMAGE_INFO);
  define("GeometryNode", "GeometryNodeImageTexture", def_geo_image_texture, ICON_IMAGE_DATA);
  define("GeometryNode", "GeometryNodeImportCSV", nullptr, ICON_LOAD_CSV);
  define("GeometryNode", "GeometryNodeImportOBJ", nullptr, ICON_LOAD_OBJ);
  define("GeometryNode", "GeometryNodeImportPLY", nullptr, ICON_LOAD_PLY);
  define("GeometryNode", "GeometryNodeImportSPZ", nullptr, ICON_LOAD_SPZ); /*BFA - icon*/
  define("GeometryNode", "GeometryNodeImportSTL", nullptr, ICON_LOAD_STL);
  define("GeometryNode", "GeometryNodeImportText", nullptr, ICON_FILE_TEXT);
  define("GeometryNode", "GeometryNodeImportVDB", nullptr, ICON_FILE_VOLUME);
  define("GeometryNode", "GeometryNodeIndexOfNearest", nullptr, ICON_INDEX_OF_NEAREST);
  define("GeometryNode", "GeometryNodeCombineList", def_geo_combine_list, ICON_NODE_COMBINE_LIST); /*BFA - icon*/
  define("GeometryNode", "GeometryNodeIndexSwitch", def_geo_index_switch, ICON_INDEX_SWITCH);
  define("GeometryNode", "GeometryNodeInputActiveCamera", nullptr, ICON_VIEW_SWITCHTOCAM);
  define("GeometryNode", "GeometryNodeInputCollection", def_geo_input_collection, ICON_OUTLINER_COLLECTION);
  define("GeometryNode", "GeometryNodeInputCurveHandlePositions", nullptr, ICON_CURVE_HANDLE_POSITIONS);
  define("GeometryNode", "GeometryNodeInputCurveTilt", nullptr, ICON_CURVE_TILT);
  define("GeometryNode", "GeometryNodeInputEdgeSmooth", nullptr, ICON_SHADING_EDGE_SMOOTH);
  define("GeometryNode", "GeometryNodeInputFont", def_geo_input_font, ICON_FONT_DATA);
  define("GeometryNode", "GeometryNodeInputID", nullptr, ICON_GET_ID);
  define("GeometryNode", "GeometryNodeInputImage", def_geo_image, ICON_FILE_IMAGE);
  define("GeometryNode", "GeometryNodeInputIndex", nullptr, ICON_INDEX);
  define("GeometryNode", "GeometryNodeInputInstanceBounds", nullptr, ICON_INSTANCE_BOUNDS);
  define("GeometryNode", "GeometryNodeInputInstanceReference", nullptr, ICON_NODE_INSTANCEREFERENCE);
  define("GeometryNode", "GeometryNodeInputInstanceRotation", nullptr, ICON_INSTANCE_ROTATE);
  define("GeometryNode", "GeometryNodeInputInstanceScale", nullptr, ICON_INSTANCE_SCALE);
  define("GeometryNode", "GeometryNodeInputMaterial", def_geo_input_material, ICON_NODE_MATERIAL);
  define("GeometryNode", "GeometryNodeInputMaterialIndex", nullptr, ICON_MATERIAL_INDEX);
  define("GeometryNode", "GeometryNodeInputMeshEdgeAngle", nullptr, ICON_EDGE_ANGLE);
  define("GeometryNode", "GeometryNodeInputMeshEdgeNeighbors", nullptr, ICON_EDGE_NEIGHBORS);
  define("GeometryNode", "GeometryNodeInputMeshEdgeVertices", nullptr, ICON_EDGE_VERTICES);
  define("GeometryNode", "GeometryNodeInputMeshFaceArea", nullptr, ICON_FACEREGIONS);
  define("GeometryNode", "GeometryNodeInputMeshFaceIsPlanar", nullptr, ICON_PLANAR);
  define("GeometryNode", "GeometryNodeInputMeshFaceNeighbors", nullptr, ICON_FACE_NEIGHBORS);
  define("GeometryNode", "GeometryNodeInputMeshIsland", nullptr, ICON_UV_ISLANDSEL);
  define("GeometryNode", "GeometryNodeInputMeshVertexNeighbors", nullptr, ICON_VERTEX_NEIGHBORS);
  define("GeometryNode", "GeometryNodeInputNamedAttribute", nullptr, ICON_NAMED_ATTRIBUTE);
  define("GeometryNode", "GeometryNodeInputNamedLayerSelection", nullptr, ICON_NAMED_LAYER_SELECTION);
  define("GeometryNode", "GeometryNodeInputNormal", def_geo_input_normal, ICON_RECALC_NORMALS);
  define("GeometryNode", "GeometryNodeInputObject", def_geo_input_object, ICON_OBJECT_DATA);
  define("GeometryNode", "GeometryNodeInputPosition", nullptr, ICON_POSITION);
  define("GeometryNode", "GeometryNodeInputRadius", nullptr, ICON_RADIUS);
  define("GeometryNode", "GeometryNodeInputSceneTime", nullptr, ICON_TIME);
  define("GeometryNode", "GeometryNodeInputShadeSmooth", nullptr, ICON_SHADING_SMOOTH);
  define("GeometryNode", "GeometryNodeInputShortestEdgePaths", nullptr, ICON_SELECT_SHORTESTPATH);
  define("GeometryNode", "GeometryNodeInputSplineCyclic", nullptr, ICON_IS_SPLINE_CYCLIC);
  define("GeometryNode", "GeometryNodeInputSplineResolution", nullptr, ICON_SPLINE_RESOLUTION);
  define("GeometryNode", "GeometryNodeInputTangent", nullptr, ICON_CURVE_TANGENT);
  define("GeometryNode", "GeometryNodeInputVoxelIndex", nullptr, ICON_NODE_VOXEL_INDEX);
  define("GeometryNode", "GeometryNodeInstanceOnPoints", nullptr, ICON_POINT_INSTANCE);
  define("GeometryNode", "GeometryNodeInstancesToPoints", nullptr, ICON_INSTANCES_TO_POINTS);
  define("GeometryNode", "GeometryNodeInstanceTransform", nullptr, ICON_INSTANCE_TRANSFORM_GET);
  define("GeometryNode", "GeometryNodeInterpolateCurves", nullptr, ICON_INTERPOLATE_CURVE);
  define("GeometryNode", "GeometryNodeIsViewport", nullptr, ICON_VIEW);
  define("GeometryNode", "GeometryNodeJoinGeometry", nullptr, ICON_JOIN);
  define("GeometryNode", "GeometryNodeListGetItem", nullptr, ICON_GET_LIST_ITEM);
  define("GeometryNode", "GeometryNodeListLength", nullptr, ICON_NODE_LISTLENGTH);
  define("GeometryNode", "GeometryNodeGeometryMaterials", nullptr, ICON_NODE_GEOMETRY_MATERIALS); /*BFA - icon*/
  define("GeometryNode", "GeometryNodeMaterialSelection", nullptr, ICON_SELECT_BY_MATERIAL);
  define("GeometryNode", "GeometryNodeMenuSwitch", def_geo_menu_switch, ICON_MENU_SWITCH);
  define("GeometryNode", "GeometryNodeMergeByDistance", nullptr, ICON_REMOVE_DOUBLES);
  define("GeometryNode", "GeometryNodeMergeLayers", def_geo_merge_layers, ICON_MERGE);
  define("GeometryNode", "GeometryNodeMergePoints", nullptr, ICON_MERGE_CENTER);
  define("GeometryNode", "GeometryNodeMeshBevel", nullptr, ICON_BEVEL);
  define("GeometryNode", "GeometryNodeMeshBoolean", nullptr, ICON_MOD_BOOLEAN);
  define("GeometryNode", "GeometryNodeMeshCircle", nullptr, ICON_MESH_CIRCLE);
  define("GeometryNode", "GeometryNodeMeshCone", nullptr, ICON_MESH_CONE);
  define("GeometryNode", "GeometryNodeMeshCube", nullptr, ICON_MESH_CUBE);
  define("GeometryNode", "GeometryNodeMeshCylinder", nullptr, ICON_MESH_CYLINDER);
  define("GeometryNode", "GeometryNodeMeshFaceSetBoundaries", nullptr, ICON_SELECT_BOUNDARY);
  define("GeometryNode", "GeometryNodeMeshGrid", nullptr, ICON_MESH_GRID);
  define("GeometryNode", "GeometryNodeMeshIcoSphere", nullptr, ICON_MESH_ICOSPHERE);
  define("GeometryNode", "GeometryNodeMeshLine", nullptr, ICON_MESH_LINE);
  define("GeometryNode", "GeometryNodeMeshToCurve", nullptr, ICON_OUTLINER_OB_CURVE);
  define("GeometryNode", "GeometryNodeMeshToDensityGrid", nullptr, ICON_NODE_MESHTODENSITYGRID);
  define("GeometryNode", "GeometryNodeMeshToPoints", nullptr, ICON_MESH_TO_POINTS);
  define("GeometryNode", "GeometryNodeMeshToSDFGrid", nullptr, ICON_NODE_MESHTOSDFGRID);
  define("GeometryNode", "GeometryNodeMeshToVolume", nullptr, ICON_MESH_TO_VOLUME);
  define("GeometryNode", "GeometryNodeMeshUVSphere", nullptr, ICON_MESH_UVSPHERE);
  define("GeometryNode", "GeometryNodeNURBSOrder", nullptr, ICON_NODE_NURBS_ORDER);
  define("GeometryNode", "GeometryNodeNURBSWeight", nullptr, ICON_NODE_NURBS_WEIGHT);
  define("GeometryNode", "GeometryNodeObjectInfo", nullptr, ICON_NODE_OBJECTINFO);
  define("GeometryNode", "GeometryNodeOffsetCornerInFace", nullptr, ICON_OFFSET_CORNER_IN_FACE);
  define("GeometryNode", "GeometryNodeOffsetPointInCurve", nullptr, ICON_OFFSET_POINT_IN_CURVE);
  define("GeometryNode", "GeometryNodePoints", nullptr, ICON_DECORATE);
  define("GeometryNode", "GeometryNodePointsOfCurve", nullptr, ICON_POINT_OF_CURVE);
  define("GeometryNode", "GeometryNodePointsSetType", nullptr, ICON_POINTS_SET_TYPE); /*BFA - icon*/
  define("GeometryNode", "GeometryNodePointsToCurves", nullptr, ICON_POINTS_TO_CURVES);
  define("GeometryNode", "GeometryNodePointsToSDFGrid", nullptr, ICON_NODE_POINTSTOSDFGRID);
  define("GeometryNode", "GeometryNodePointsToVertices", nullptr, ICON_POINTS_TO_VERTICES);
  define("GeometryNode", "GeometryNodePointsToVolume", nullptr, ICON_POINT_TO_VOLUME);
  define("GeometryNode", "GeometryNodeProximity", nullptr, ICON_GEOMETRY_PROXIMITY);
  define("GeometryNode", "GeometryNodeRasterizePoints", def_geo_rasterize_points, ICON_RASTERIZE_POINTS); /*BFA - icon*/
  define("GeometryNode", "GeometryNodeRaycast", nullptr, ICON_RAYCAST);
  define("GeometryNode", "GeometryNodeRealizeInstances", nullptr, ICON_MOD_INSTANCE);
  define("GeometryNode", "GeometryNodeRemoveAttribute", nullptr, ICON_ATTRIBUTE_REMOVE);
  define("GeometryNode", "GeometryNodeRenameAttribute", nullptr, ICON_RENAME);
  define("GeometryNode", "GeometryNodeRepeatInput", def_geo_repeat_input, ICON_REPEAT);
  define("GeometryNode", "GeometryNodeRepeatOutput", def_geo_repeat_output, ICON_REPEAT);
  define("GeometryNode", "GeometryNodeReplaceMaterial", nullptr, ICON_MATERIAL_REPLACE);
  define("GeometryNode", "GeometryNodeResampleCurve", nullptr, ICON_CURVE_RESAMPLE);
  define("GeometryNode", "GeometryNodeReverseCurve", nullptr, ICON_SWITCH_DIRECTION);
  define("GeometryNode", "GeometryNodeRotateInstances", nullptr, ICON_ROTATE_INSTANCE);
  define("GeometryNode", "GeometryNodeSampleCurve", def_geo_curve_sample, ICON_CURVE_SAMPLE);
  define("GeometryNode", "GeometryNodeSampleGrid", nullptr, ICON_NODE_SAMPLEGRID);
  define("GeometryNode", "GeometryNodeSampleGridIndex", nullptr, ICON_NODE_SAMPLEGRIDINDEX);
  define("GeometryNode", "GeometryNodeSampleIndex", def_geo_sample_index, ICON_SAMPLE_INDEX);
  define("GeometryNode", "GeometryNodeSampleNearest", nullptr, ICON_SAMPLE_NEAREST);
  define("GeometryNode", "GeometryNodeSampleNearestSurface", nullptr, ICON_SAMPLE_NEAREST_SURFACE);
  define("GeometryNode", "GeometryNodeSampleSoundFrequencies", nullptr, ICON_PLAY_SOUND);
  define("GeometryNode", "GeometryNodeSampleUVSurface", nullptr, ICON_SAMPLE_UV_SURFACE);
  define("GeometryNode", "GeometryNodeScaleElements", nullptr, ICON_TRANSFORM_SCALE);
  define("GeometryNode", "GeometryNodeScaleInstances", nullptr, ICON_SCALE_INSTANCE);
  define("GeometryNode", "GeometryNodeSDFGridBoolean", nullptr, ICON_NODE_SDFGRIDBOOLEAN);
  define("GeometryNode", "GeometryNodeSDFGridFillet", nullptr, ICON_NODE_SDFGRIDFILLET);
  define("GeometryNode", "GeometryNodeSDFGridLaplacian", nullptr, ICON_NODE_SDFGRIDLAPLACIAN);
  define("GeometryNode", "GeometryNodeSDFGridMean", nullptr, ICON_NODE_SDFGRIDMEAN);
  define("GeometryNode", "GeometryNodeSDFGridMeanCurvature", nullptr, ICON_NODE_SDFGRIDMEAN_CURVATURE);
  define("GeometryNode", "GeometryNodeSDFGridMedian", nullptr, ICON_NODE_SDFGRIDMEDIAN);
  define("GeometryNode", "GeometryNodeSDFGridOffset", nullptr, ICON_NODE_SDFGRIDOFFSET);
  define("GeometryNode", "GeometryNodeSelfObject", nullptr, ICON_SELF_OBJECT);
  define("GeometryNode", "GeometryNodeSeparateComponents", nullptr, ICON_SEPARATE);
  define("GeometryNode", "GeometryNodeSeparateGeometry", nullptr, ICON_SEPARATE_GEOMETRY);
  define("GeometryNode", "GeometryNodeSetCurveHandlePositions", nullptr, ICON_SET_CURVE_HANDLE_POSITIONS);
  define("GeometryNode", "GeometryNodeSetCurveNormal", nullptr, ICON_CURVE_NORMAL);
  define("GeometryNode", "GeometryNodeSetCurveRadius", nullptr, ICON_SET_CURVE_RADIUS);
  define("GeometryNode", "GeometryNodeSetCurveTilt", nullptr, ICON_SET_CURVE_TILT);
  define("GeometryNode", "GeometryNodeSetGeometryBundle", nullptr, ICON_NODE_BUNDLE_SET);
  define("GeometryNode", "GeometryNodeSetGeometryName", nullptr, ICON_GEOMETRY_NAME);
  define("GeometryNode", "GeometryNodeSetGreasePencilColor", def_geo_set_grease_pencil_color, ICON_NODE_GP_SETCOLOR);
  define("GeometryNode", "GeometryNodeSetGreasePencilDepth", def_geo_set_grease_pencil_depth, ICON_DEPTH);
  define("GeometryNode", "GeometryNodeSetGreasePencilSoftness", nullptr, ICON_FALLOFFSTROKE);
  define("GeometryNode", "GeometryNodeSetGridBackground", nullptr, ICON_NODE_SETGRIDBACKGROUND);
  define("GeometryNode", "GeometryNodeSetGridTransform", nullptr, ICON_NODE_SETGRIDTRANSFORM);
  define("GeometryNode", "GeometryNodeSetID", nullptr, ICON_SET_ID);
  define("GeometryNode", "GeometryNodeSetInstanceTransform", nullptr, ICON_INSTANCE_TRANSFORM);
  define("GeometryNode", "GeometryNodeSetMaterial", nullptr, ICON_MATERIAL_ADD);
  define("GeometryNode", "GeometryNodeSetMaterialIndex", nullptr, ICON_SET_MATERIAL_INDEX);
  define("GeometryNode", "GeometryNodeSetMeshNormal", nullptr, ICON_SET_SMOOTH);
  define("GeometryNode", "GeometryNodeSetNURBSOrder", nullptr, ICON_NODE_SET_NURBS_ORDER);
  define("GeometryNode", "GeometryNodeSetNURBSWeight", nullptr, ICON_NODE_SET_NURBS_WEIGHT);
  define("GeometryNode", "GeometryNodeSetPointRadius", nullptr, ICON_SET_CURVE_RADIUS);
  define("GeometryNode", "GeometryNodeSetPosition", nullptr, ICON_SET_POSITION);
  define("GeometryNode", "GeometryNodeSetShadeSmooth", nullptr, ICON_SET_SHADE_SMOOTH);
  define("GeometryNode", "GeometryNodeSetSplineCyclic", nullptr, ICON_TOGGLE_CYCLIC);
  define("GeometryNode", "GeometryNodeSetSplineResolution", nullptr, ICON_SET_SPLINE_RESOLUTION);
  define("GeometryNode", "GeometryNodeSimulationInput", def_geo_simulation_input, ICON_TIME);
  define("GeometryNode", "GeometryNodeSimulationOutput", def_geo_simulation_output, ICON_TIME);
  define("GeometryNode", "GeometryNodeSortElements", nullptr, ICON_SORTSIZE);
  define("GeometryNode", "GeometryNodeSortList", nullptr, ICON_NODE_SORTLIST);
  define("GeometryNode", "GeometryNodeSplineLength", nullptr, ICON_SPLINE_LENGTH);
  define("GeometryNode", "GeometryNodeSplineParameter", nullptr, ICON_CURVE_PARAMETER);
  define("GeometryNode", "GeometryNodeSplitEdges", nullptr, ICON_SPLITEDGE);
  define("GeometryNode", "GeometryNodeSplitToInstances", nullptr, ICON_SPLIT_TO_INSTANCES);
  define("GeometryNode", "GeometryNodeStoreNamedAttribute", nullptr, ICON_ATTRIBUTE_STORE);
  define("GeometryNode", "GeometryNodeStoreNamedGrid", nullptr, ICON_NODE_STORENAMEDGRID);
  define("GeometryNode", "GeometryNodeStringJoin", nullptr, ICON_STRING_JOIN);
  define("GeometryNode", "GeometryNodeStringToCurves", nullptr, ICON_STRING_TO_CURVE);
  define("GeometryNode", "GeometryNodeSubdivideCurve", nullptr, ICON_SUBDIVIDE_EDGES);
  define("GeometryNode", "GeometryNodeSubdivideMesh", nullptr, ICON_SUBDIVIDE_MESH);
  define("GeometryNode", "GeometryNodeSubdivisionSurface", nullptr, ICON_SUBDIVIDE_EDGES);
  define("GeometryNode", "GeometryNodeSwitch", nullptr, ICON_SWITCH);
  define("GeometryNode", "GeometryNodeTagFilter", nullptr, ICON_TAG_FILTER); /*BFA - icon*/
  define("GeometryNode", "GeometryNodeTool3DCursor", nullptr, ICON_CURSOR);
  define("GeometryNode", "GeometryNodeToolActiveElement", nullptr, ICON_ACTIVE_ELEMENT);
  define("GeometryNode", "GeometryNodeToolFaceSet", nullptr, ICON_FACE_SET);
  define("GeometryNode", "GeometryNodeToolMousePosition", nullptr, ICON_MOUSE_POSITION);
  define("GeometryNode", "GeometryNodeToolSelection", nullptr, ICON_RESTRICT_SELECT_OFF);
  define("GeometryNode", "GeometryNodeToolSetFaceSet", nullptr, ICON_SET_FACE_SET);
  define("GeometryNode", "GeometryNodeToolSetSelection", nullptr, ICON_SET_SELECTION);
  define("GeometryNode", "GeometryNodeTransform", nullptr, ICON_NODE_TRANSFORM);
  define("GeometryNode", "GeometryNodeTranslateInstances", nullptr, ICON_TRANSLATE_INSTANCE);
  define("GeometryNode", "GeometryNodeTransferAttributes", nullptr, ICON_ATTRIBUTE_TRANSFER); /*BFA - icon*/
  define("GeometryNode", "GeometryNodeTriangulate", nullptr, ICON_MOD_TRIANGULATE);
  define("GeometryNode", "GeometryNodeTrimCurve", nullptr, ICON_CURVE_TRIM);
  define("GeometryNode", "GeometryNodeUVPackIslands", nullptr, ICON_PACKISLAND);
  define("GeometryNode", "GeometryNodeUVTangent", nullptr, ICON_NODE_UVTANGENT);
  define("GeometryNode", "GeometryNodeUVUnwrap", nullptr, ICON_UNWRAP_ABF);
  define("GeometryNode", "GeometryNodeVertexOfCorner", nullptr, ICON_VERTEX_OF_CORNER);
  define("GeometryNode", "GeometryNodeViewer", rna_def_geo_viewer, ICON_NODE_VIEWER);
  define("GeometryNode", "GeometryNodeViewportTransform", nullptr, ICON_VIEWPORT_TRANSFORM);
  define("GeometryNode", "GeometryNodeVolumeCube", nullptr, ICON_VOLUME_CUBE);
  define("GeometryNode", "GeometryNodeVolumeToMesh", nullptr, ICON_VOLUME_TO_MESH);
  define("GeometryNode", "GeometryNodeWarning", nullptr, ICON_ERROR);
  define("GeometryNode", "GeometryNodeXPBDSolver", nullptr, ICON_NODE_XPBD_SOLVER); /*BFA - icon*/
  define("GeometryNode", "GeometryNodeGroup", def_group, ICON_NONE); /* bfa - don't need 2 nodegroups icons */

  /* clang-format on */
}

}  // namespace blender

#endif
