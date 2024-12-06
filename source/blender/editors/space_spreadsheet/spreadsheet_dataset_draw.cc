/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include <fmt/format.h>

#include "BLI_string.h"

#include "DNA_collection_types.h"
#include "DNA_curves_types.h"
#include "DNA_mesh_types.h"
#include "DNA_pointcloud_types.h"
#include "DNA_space_types.h"
#include "DNA_windowmanager_types.h"

#include "BKE_context.hh"
#include "BKE_curves.hh"
#include "BKE_geometry_set_instances.hh"
#include "BKE_grease_pencil.hh"
#include "BKE_instances.hh"
#include "BKE_volume.hh"

#include "RNA_access.hh"
#include "RNA_prototypes.hh"

#include "UI_interface.hh"
#include "UI_tree_view.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "BLT_translation.hh"

#include "ED_outliner.hh"

#include "spreadsheet_data_source_geometry.hh"
#include "spreadsheet_dataset_draw.hh"
#include "spreadsheet_intern.hh"

namespace blender::ed::spreadsheet {

class GeometryDataSetTreeView;
class GeometryInstancesTreeView;

struct GeometryDataIdentifier {
  bke::GeometryComponent::Type component_type;
  std::optional<int> layer_index;
  std::optional<bke::AttrDomain> domain;
};

static void draw_row_suffix(ui::AbstractTreeViewItem &view_item, const StringRefNull str)
{
  /* Using the tree row button instead of a separate right aligned button gives padding
   * to the right side of the number, which it didn't have with the button. */
  UI_but_hint_drawstr_set(reinterpret_cast<uiBut *>(view_item.view_item_button()), str.c_str());
}

static void draw_count(ui::AbstractTreeViewItem &view_item, const int count)
{
  char element_count[BLI_STR_FORMAT_INT32_DECIMAL_UNIT_SIZE];
  BLI_str_format_decimal_unit(element_count, count);
  draw_row_suffix(view_item, element_count);
}

static StringRefNull mesh_domain_to_label(const bke::AttrDomain domain)
{
  switch (domain) {
    case bke::AttrDomain::Point:
      return IFACE_("Vertex");
    case bke::AttrDomain::Edge:
      return IFACE_("Edge");
    case bke::AttrDomain::Face:
      return IFACE_("Face");
    case bke::AttrDomain::Corner:
      return IFACE_("Face Corner");
    default:
      BLI_assert_unreachable();
      return "";
  }
}

static StringRefNull curves_domain_to_label(const bke::AttrDomain domain)
{
  switch (domain) {
    case bke::AttrDomain::Point:
      return IFACE_("Control Point");
    case bke::AttrDomain::Curve:
      return IFACE_("Spline");
    default:
      BLI_assert_unreachable();
      return "";
  }
}

static BIFIconID mesh_domain_to_icon(const bke::AttrDomain domain)
{
  switch (domain) {
    case bke::AttrDomain::Point:
      return ICON_VERTEXSEL;
    case bke::AttrDomain::Edge:
      return ICON_EDGESEL;
    case bke::AttrDomain::Face:
      return ICON_FACESEL;
    case bke::AttrDomain::Corner:
      return ICON_FACE_CORNER;
    default:
      BLI_assert_unreachable();
      return ICON_NONE;
  }
}

static BIFIconID curves_domain_to_icon(const bke::AttrDomain domain)
{
  switch (domain) {
    case bke::AttrDomain::Point:
      return ICON_CURVE_BEZCIRCLE;
    case bke::AttrDomain::Curve:
      return ICON_CURVE_PATH;
    default:
      BLI_assert_unreachable();
      return ICON_NONE;
  }
}

class InstancesTreeViewItem : public ui::AbstractTreeViewItem {
 public:
  GeometryInstancesTreeView &get_tree() const;

  void get_parent_instance_ids(Vector<SpreadsheetInstanceID> &r_instance_ids) const;

  void on_activate(bContext &C) override;

  std::optional<bool> should_be_active() const override;
};

class RootGeometryViewItem : public InstancesTreeViewItem {
 public:
  RootGeometryViewItem(const bke::GeometrySet &geometry)
  {
    label_ = geometry.name.empty() ? IFACE_("(Geometry)") : geometry.name;
  }

  void build_row(uiLayout &row) override
  {
    uiItemL(&row, label_, ICON_GEOMETRY_SET);
  }
};

class InstanceReferenceViewItem : public InstancesTreeViewItem {
 private:
  const bke::InstanceReference &reference_;
  int reference_index_;
  int user_count_;

 public:
  InstanceReferenceViewItem(const bke::Instances &instances, const int reference_index)
      : reference_(instances.references()[reference_index]), reference_index_(reference_index)
  {
    label_ = std::to_string(reference_index);
    user_count_ = instances.reference_user_counts()[reference_index];
  }

  void build_row(uiLayout &row) override
  {
    const int icon = get_instance_reference_icon(reference_);
    StringRefNull name = reference_.name();
    if (name.is_empty()) {
      name = IFACE_("(Geometry)");
    }
    uiItemL(&row, name, icon);
    draw_count(*this, user_count_);
  }

  int reference_index() const
  {
    return reference_index_;
  }
};

class GeometryInstancesTreeView : public ui::AbstractTreeView {
 private:
  bke::GeometrySet root_geometry_set_;
  SpaceSpreadsheet &sspreadsheet_;
  bScreen &screen_;

  friend class InstancesTreeViewItem;

 public:
  GeometryInstancesTreeView(bke::GeometrySet geometry_set, const bContext &C)
      : root_geometry_set_(std::move(geometry_set)),
        sspreadsheet_(*CTX_wm_space_spreadsheet(&C)),
        screen_(*CTX_wm_screen(&C))
  {
  }

  void build_tree() override
  {
    auto &root_item = this->add_tree_item<RootGeometryViewItem>(root_geometry_set_);
    root_item.uncollapse_by_default();
    if (const bke::Instances *instances = root_geometry_set_.get_instances()) {
      this->build_tree_for_instances(root_item, *instances);
    }
  }

  void build_tree_for_instances(ui::TreeViewItemContainer &parent, const bke::Instances &instances)
  {
    const Span<bke::InstanceReference> references = instances.references();
    for (const int reference_i : references.index_range()) {
      auto &reference_item = parent.add_tree_item<InstanceReferenceViewItem>(instances,
                                                                             reference_i);
      const bke::InstanceReference &reference = references[reference_i];
      bke::GeometrySet reference_geometry;
      reference.to_geometry_set(reference_geometry);
      if (const bke::Instances *child_instances = reference_geometry.get_instances()) {
        this->build_tree_for_instances(reference_item, *child_instances);
      }
    }
  }
};

class DataSetViewItem : public ui::AbstractTreeViewItem {
 public:
  GeometryDataSetTreeView &get_tree() const;

  void on_activate(bContext &C) override;

  std::optional<bool> should_be_active() const override;

  /** Get information about which part of a geometry this item corresponds to. */
  virtual std::optional<GeometryDataIdentifier> get_geometry_data_id() const
  {
    return std::nullopt;
  }
};

class MeshViewItem : public DataSetViewItem {
 public:
  MeshViewItem()
  {
    label_ = IFACE_("Mesh");
  }

  void build_row(uiLayout &row) override
  {
    uiItemL(&row, label_, ICON_MESH_DATA);
  }
};

class MeshDomainViewItem : public DataSetViewItem {
 private:
  const Mesh *mesh_;
  bke::AttrDomain domain_;

 public:
  MeshDomainViewItem(const Mesh *mesh, const bke::AttrDomain domain) : mesh_(mesh), domain_(domain)
  {
    label_ = mesh_domain_to_label(domain);
  }

  std::optional<GeometryDataIdentifier> get_geometry_data_id() const override
  {
    return GeometryDataIdentifier{bke::GeometryComponent::Type::Mesh, std::nullopt, domain_};
  }

  void build_row(uiLayout &row) override
  {
    const BIFIconID icon = mesh_domain_to_icon(domain_);
    uiItemL(&row, label_, icon);

    const int count = mesh_ ? mesh_->attributes().domain_size(domain_) : 0;
    draw_count(*this, count);
  }
};

class CurvesViewItem : public DataSetViewItem {
 public:
  CurvesViewItem()
  {
    label_ = IFACE_("Curve");
  }

  void build_row(uiLayout &row) override
  {
    uiItemL(&row, label_, ICON_CURVE_DATA);
  }
};

class CurvesDomainViewItem : public DataSetViewItem {
 private:
  const Curves *curves_;
  bke::AttrDomain domain_;

 public:
  CurvesDomainViewItem(const Curves *curves, const bke::AttrDomain domain)
      : curves_(curves), domain_(domain)
  {
    label_ = curves_domain_to_label(domain);
  }

  std::optional<GeometryDataIdentifier> get_geometry_data_id() const override
  {
    return GeometryDataIdentifier{bke::GeometryComponent::Type::Curve, std::nullopt, domain_};
  }

  void build_row(uiLayout &row) override
  {
    const BIFIconID icon = curves_domain_to_icon(domain_);
    uiItemL(&row, label_, icon);

    const int count = curves_ ? curves_->geometry.wrap().attributes().domain_size(domain_) : 0;
    draw_count(*this, count);
  }
};

class GreasePencilViewItem : public DataSetViewItem {
 public:
  GreasePencilViewItem()
  {
    label_ = IFACE_("Grease Pencil");
  }

  void build_row(uiLayout &row) override
  {
    uiItemL(&row, label_, ICON_OUTLINER_DATA_GREASEPENCIL);
  }
};

class GreasePencilLayersViewItem : public DataSetViewItem {
 private:
  const GreasePencil *grease_pencil_;

 public:
  GreasePencilLayersViewItem(const GreasePencil *grease_pencil) : grease_pencil_(grease_pencil)
  {
    label_ = IFACE_("Layer");
  }

  std::optional<GeometryDataIdentifier> get_geometry_data_id() const override
  {
    return GeometryDataIdentifier{
        bke::GeometryComponent::Type::GreasePencil, std::nullopt, bke::AttrDomain::Layer};
  }

  void build_row(uiLayout &row) override
  {
    const int count = grease_pencil_ ? grease_pencil_->layers().size() : 0;
    uiItemL(&row, label_, ICON_OUTLINER_DATA_GP_LAYER);
    draw_count(*this, count);
  }
};

class GreasePencilLayerViewItem : public DataSetViewItem {
 private:
  const bke::greasepencil::Layer &layer_;

 public:
  GreasePencilLayerViewItem(const GreasePencil &grease_pencil, const int layer_index)
      : layer_(grease_pencil.layer(layer_index))
  {
    label_ = std::to_string(layer_index);
  }

  void build_row(uiLayout &row) override
  {
    StringRefNull name = layer_.name();
    if (name.is_empty()) {
      name = IFACE_("(Layer)");
    }
    uiItemL(&row, name, ICON_CURVE_DATA);
  }
};

class GreasePencilLayerCurvesDomainViewItem : public DataSetViewItem {
 private:
  const GreasePencil &grease_pencil_;
  int layer_index_;
  bke::AttrDomain domain_;

 public:
  GreasePencilLayerCurvesDomainViewItem(const GreasePencil &grease_pencil,
                                        const int layer_index,
                                        const bke::AttrDomain domain)
      : grease_pencil_(grease_pencil), layer_index_(layer_index), domain_(domain)
  {
    label_ = curves_domain_to_label(domain);
  }

  std::optional<GeometryDataIdentifier> get_geometry_data_id() const override
  {
    return GeometryDataIdentifier{
        bke::GeometryComponent::Type::GreasePencil, layer_index_, domain_};
  }

  void build_row(uiLayout &row) override
  {
    const BIFIconID icon = curves_domain_to_icon(domain_);
    uiItemL(&row, label_, icon);

    const bke::greasepencil::Drawing *drawing = grease_pencil_.get_eval_drawing(
        grease_pencil_.layer(layer_index_));
    const int count = drawing ? drawing->strokes().attributes().domain_size(domain_) : 0;
    draw_count(*this, count);
  }
};

class PointCloudViewItem : public DataSetViewItem {
 public:
  PointCloudViewItem()
  {
    label_ = IFACE_("Point Cloud");
  }

  void build_row(uiLayout &row) override
  {
    uiItemL(&row, label_, ICON_POINTCLOUD_DATA);
  }
};

class PointsViewItem : public DataSetViewItem {
 private:
  const PointCloud *pointcloud_;

 public:
  PointsViewItem(const PointCloud *pointcloud) : pointcloud_(pointcloud)
  {
    label_ = IFACE_("Point");
  }

  std::optional<GeometryDataIdentifier> get_geometry_data_id() const override
  {
    return GeometryDataIdentifier{
        bke::GeometryComponent::Type::PointCloud, std::nullopt, bke::AttrDomain::Point};
  }

  void build_row(uiLayout &row) override
  {
    uiItemL(&row, label_, ICON_POINTCLOUD_POINT);
    const int count = pointcloud_ ? pointcloud_->totpoint : 0;
    draw_count(*this, count);
  }
};

class VolumeGridsViewItem : public DataSetViewItem {
 private:
  const Volume *volume_;

 public:
  VolumeGridsViewItem(const Volume *volume) : volume_(volume)
  {
    label_ = IFACE_("Volume Grids");
  }

  std::optional<GeometryDataIdentifier> get_geometry_data_id() const override
  {
    return GeometryDataIdentifier{
        bke::GeometryComponent::Type::Volume, std::nullopt, std::nullopt};
  }

  void build_row(uiLayout &row) override
  {
    uiItemL(&row, label_, ICON_VOLUME_DATA);
    const int count = volume_ ? BKE_volume_num_grids(volume_) : 0;
    draw_count(*this, count);
  }
};

class InstancesViewItem : public DataSetViewItem {
 private:
  const bke::Instances *instances_;

 public:
  InstancesViewItem(const bke::Instances *instances) : instances_(instances)
  {
    label_ = IFACE_("Instances");
  }

  std::optional<GeometryDataIdentifier> get_geometry_data_id() const override
  {
    return GeometryDataIdentifier{
        bke::GeometryComponent::Type::Instance, std::nullopt, bke::AttrDomain::Instance};
  }

  void build_row(uiLayout &row) override
  {
    uiItemL(&row, label_, ICON_EMPTY_AXIS);
    const int count = instances_ ? instances_->instances_num() : 0;
    draw_count(*this, count);
  }
};

class GeometryDataSetTreeView : public ui::AbstractTreeView {
 private:
  bke::GeometrySet geometry_set_;
  SpaceSpreadsheet &sspreadsheet_;
  bScreen &screen_;

  friend class DataSetViewItem;

 public:
  GeometryDataSetTreeView(bke::GeometrySet geometry_set, const bContext &C)
      : geometry_set_(std::move(geometry_set)),
        sspreadsheet_(*CTX_wm_space_spreadsheet(&C)),
        screen_(*CTX_wm_screen(&C))
  {
  }

  void build_tree() override
  {
    this->build_tree_for_geometry(geometry_set_, *this);
  }

  void build_tree_for_geometry(const bke::GeometrySet &geometry, ui::TreeViewItemContainer &parent)
  {
    const Mesh *mesh = geometry.get_mesh();
    this->build_tree_for_mesh(mesh, parent);

    const Curves *curves = geometry.get_curves();
    this->build_tree_for_curves(curves, parent);

    const GreasePencil *grease_pencil = geometry.get_grease_pencil();
    this->build_tree_for_grease_pencil(grease_pencil, parent);

    const PointCloud *pointcloud = geometry.get_pointcloud();
    this->build_tree_for_pointcloud(pointcloud, parent);

    const Volume *volume = geometry.get_volume();
    this->build_tree_for_volume(volume, parent);

    const bke::Instances *instances = geometry.get_instances();
    this->build_tree_for_instances(instances, parent);
  }

  void build_tree_for_mesh(const Mesh *mesh, ui::TreeViewItemContainer &parent)
  {
    auto &mesh_item = parent.add_tree_item<MeshViewItem>();
    mesh_item.uncollapse_by_default();
    mesh_item.add_tree_item<MeshDomainViewItem>(mesh, bke::AttrDomain::Point);
    mesh_item.add_tree_item<MeshDomainViewItem>(mesh, bke::AttrDomain::Edge);
    mesh_item.add_tree_item<MeshDomainViewItem>(mesh, bke::AttrDomain::Face);
    mesh_item.add_tree_item<MeshDomainViewItem>(mesh, bke::AttrDomain::Corner);
  }

  void build_tree_for_curves(const Curves *curves, ui::TreeViewItemContainer &parent)
  {
    auto &curves_item = parent.add_tree_item<CurvesViewItem>();
    curves_item.uncollapse_by_default();
    curves_item.add_tree_item<CurvesDomainViewItem>(curves, bke::AttrDomain::Point);
    curves_item.add_tree_item<CurvesDomainViewItem>(curves, bke::AttrDomain::Curve);
  }

  void build_tree_for_grease_pencil(const GreasePencil *grease_pencil,
                                    ui::TreeViewItemContainer &parent)
  {
    auto &grease_pencil_item = parent.add_tree_item<GreasePencilViewItem>();
    grease_pencil_item.uncollapse_by_default();
    auto &layers_item = grease_pencil_item.add_tree_item<GreasePencilLayersViewItem>(
        grease_pencil);
    if (!grease_pencil) {
      return;
    }
    const Span<const bke::greasepencil::Layer *> layers = grease_pencil->layers();
    for (const int layer_i : layers.index_range()) {
      auto &layer_item = layers_item.add_tree_item<GreasePencilLayerViewItem>(*grease_pencil,
                                                                              layer_i);
      layer_item.add_tree_item<GreasePencilLayerCurvesDomainViewItem>(
          *grease_pencil, layer_i, bke::AttrDomain::Point);
      layer_item.add_tree_item<GreasePencilLayerCurvesDomainViewItem>(
          *grease_pencil, layer_i, bke::AttrDomain::Curve);
    }
  }

  void build_tree_for_pointcloud(const PointCloud *pointcloud, ui::TreeViewItemContainer &parent)
  {
    auto &pointcloud_item = parent.add_tree_item<PointCloudViewItem>();
    pointcloud_item.uncollapse_by_default();
    pointcloud_item.add_tree_item<PointsViewItem>(pointcloud);
  }

  void build_tree_for_volume(const Volume *volume, ui::TreeViewItemContainer &parent)
  {
    parent.add_tree_item<VolumeGridsViewItem>(volume);
  }

  void build_tree_for_instances(const bke::Instances *instances, ui::TreeViewItemContainer &parent)
  {
    parent.add_tree_item<InstancesViewItem>(instances);
  }
};

GeometryDataSetTreeView &DataSetViewItem::get_tree() const
{
  return static_cast<GeometryDataSetTreeView &>(this->get_tree_view());
}

GeometryInstancesTreeView &InstancesTreeViewItem::get_tree() const
{
  return static_cast<GeometryInstancesTreeView &>(this->get_tree_view());
}

void InstancesTreeViewItem::get_parent_instance_ids(
    Vector<SpreadsheetInstanceID> &r_instance_ids) const
{
  if (auto *reference_item = dynamic_cast<const InstanceReferenceViewItem *>(this)) {
    r_instance_ids.append({reference_item->reference_index()});
  }
  this->foreach_parent([&](const ui::AbstractTreeViewItem &item) {
    if (auto *reference_item = dynamic_cast<const InstanceReferenceViewItem *>(&item)) {
      r_instance_ids.append({reference_item->reference_index()});
    }
  });
  std::reverse(r_instance_ids.begin(), r_instance_ids.end());
}

std::optional<bool> InstancesTreeViewItem::should_be_active() const
{
  GeometryInstancesTreeView &tree_view = this->get_tree();
  SpaceSpreadsheet &sspreadsheet = tree_view.sspreadsheet_;

  Vector<SpreadsheetInstanceID> instance_ids;
  this->get_parent_instance_ids(instance_ids);
  if (sspreadsheet.instance_ids_num != instance_ids.size()) {
    return false;
  }
  for (const int i : instance_ids.index_range()) {
    const SpreadsheetInstanceID &a = sspreadsheet.instance_ids[i];
    const SpreadsheetInstanceID &b = instance_ids[i];
    if (a.reference_index != b.reference_index) {
      return false;
    }
  }
  return true;
}

void InstancesTreeViewItem::on_activate(bContext &C)
{
  Vector<SpreadsheetInstanceID> instance_ids;
  this->get_parent_instance_ids(instance_ids);

  SpaceSpreadsheet &sspreadsheet = *CTX_wm_space_spreadsheet(&C);

  MEM_SAFE_FREE(sspreadsheet.instance_ids);
  sspreadsheet.instance_ids = MEM_cnew_array<SpreadsheetInstanceID>(instance_ids.size(), __func__);
  sspreadsheet.instance_ids_num = instance_ids.size();
  initialized_copy_n(instance_ids.data(), instance_ids.size(), sspreadsheet.instance_ids);

  WM_main_add_notifier(NC_SPACE | ND_SPACE_SPREADSHEET, nullptr);
}

void DataSetViewItem::on_activate(bContext &C)
{
  std::optional<GeometryDataIdentifier> data_id = this->get_geometry_data_id();
  if (!data_id) {
    this->foreach_item_recursive([&](const ui::AbstractTreeViewItem &item) {
      if (data_id) {
        return;
      }
      if (auto *data_set_view_item = dynamic_cast<const DataSetViewItem *>(&item)) {
        data_id = data_set_view_item->get_geometry_data_id();
      }
    });
    if (!data_id) {
      return;
    }
  }

  bScreen &screen = *CTX_wm_screen(&C);
  SpaceSpreadsheet &sspreadsheet = *CTX_wm_space_spreadsheet(&C);

  sspreadsheet.geometry_component_type = uint8_t(data_id->component_type);
  if (data_id->domain) {
    sspreadsheet.attribute_domain = uint8_t(*data_id->domain);
  }
  if (data_id->layer_index) {
    sspreadsheet.active_layer_index = *data_id->layer_index;
  }
  PointerRNA ptr = RNA_pointer_create(&screen.id, &RNA_SpaceSpreadsheet, &sspreadsheet);
  /* These updates also make sure that the attribute domain is set properly based on the
   * component type. */
  RNA_property_update(&C, &ptr, RNA_struct_find_property(&ptr, "attribute_domain"));
  RNA_property_update(&C, &ptr, RNA_struct_find_property(&ptr, "geometry_component_type"));
}

std::optional<bool> DataSetViewItem::should_be_active() const
{
  GeometryDataSetTreeView &tree_view = this->get_tree();
  SpaceSpreadsheet &sspreadsheet = tree_view.sspreadsheet_;

  const std::optional<GeometryDataIdentifier> data_id = this->get_geometry_data_id();
  if (!data_id) {
    return false;
  }
  if (bke::GeometryComponent::Type(sspreadsheet.geometry_component_type) !=
      data_id->component_type)
  {
    return false;
  }
  if (data_id->domain) {
    if (bke::AttrDomain(sspreadsheet.attribute_domain) != data_id->domain) {
      return false;
    }
  }
  if (data_id->layer_index) {
    if (sspreadsheet.active_layer_index != *data_id->layer_index) {
      return false;
    }
  }
  return true;
}

void spreadsheet_data_set_panel_draw(const bContext *C, Panel *panel)
{
  const SpaceSpreadsheet *sspreadsheet = CTX_wm_space_spreadsheet(C);
  Object *object = spreadsheet_get_object_eval(sspreadsheet, CTX_data_depsgraph_pointer(C));
  if (!object) {
    return;
  }
  uiLayout *layout = panel->layout;

  uiBlock *block = uiLayoutGetBlock(layout);

  UI_block_layout_set_current(block, layout);
  const bke::GeometrySet root_geometry = spreadsheet_get_display_geometry_set(sspreadsheet,
                                                                              object);

  if (uiLayout *panel = uiLayoutPanel(C, layout, "instance tree", false, IFACE_("Geometry"))) {
    ui::AbstractTreeView *tree_view = UI_block_add_view(
        *block,
        "Instances Tree View",
        std::make_unique<GeometryInstancesTreeView>(root_geometry, *C));
    tree_view->set_context_menu_title("Instance");
    ui::TreeViewBuilder::build_tree_view(*C, *tree_view, *panel, {}, false);
  }
  if (uiLayout *panel = uiLayoutPanel(
          C, layout, "geometry_domain_tree_view", false, IFACE_("Domain")))
  {
    bke::GeometrySet instance_geometry = get_geometry_set_for_instance_ids(
        root_geometry, {sspreadsheet->instance_ids, sspreadsheet->instance_ids_num});
    ui::AbstractTreeView *tree_view = UI_block_add_view(
        *block,
        "Data Set Tree View",
        std::make_unique<GeometryDataSetTreeView>(std::move(instance_geometry), *C));
    tree_view->set_context_menu_title("Domain");
    ui::TreeViewBuilder::build_tree_view(*C, *tree_view, *panel, {}, false);
  }
}

}  // namespace blender::ed::spreadsheet
