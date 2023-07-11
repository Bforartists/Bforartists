/* SPDX-FileCopyrightText: 2023 Blender Foundation
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edinterface
 */

#include "BKE_context.h"
#include "BKE_grease_pencil.hh"

#include "BLT_translation.h"

#include "UI_interface.h"
#include "UI_interface.hh"
#include "UI_tree_view.hh"

#include "RNA_access.h"
#include "RNA_prototypes.h"

namespace blender::ui::greasepencil {

using namespace blender::bke::greasepencil;

class LayerViewItem : public AbstractTreeViewItem {
 public:
  LayerViewItem(GreasePencil &grease_pencil, Layer &layer)
      : grease_pencil_(grease_pencil), layer_(layer)
  {
    this->label_ = layer.name();
  }

  void build_row(uiLayout &row) override
  {
    build_layer_name(row);

    uiLayout *sub = uiLayoutRow(&row, true);
    uiLayoutSetPropDecorate(sub, false);

    build_layer_buttons(*sub);
  }

  bool supports_collapsing() const override
  {
    return false;
  }

  std::optional<bool> should_be_active() const override
  {
    if (this->grease_pencil_.has_active_layer()) {
      return reinterpret_cast<GreasePencilLayer *>(&layer_) == this->grease_pencil_.active_layer;
    }
    return {};
  }

  void on_activate() override
  {
    this->grease_pencil_.set_active_layer(&layer_);
  }

  bool supports_renaming() const override
  {
    return true;
  }

  bool rename(StringRefNull new_name) override
  {
    grease_pencil_.rename_layer(layer_, new_name);
    return true;
  }

  StringRef get_rename_string() const override
  {
    return layer_.name();
  }

 private:
  GreasePencil &grease_pencil_;
  Layer &layer_;

  void build_layer_name(uiLayout &row)
  {
    uiBut *but = uiItemL_ex(
        &row, IFACE_(layer_.name().c_str()), ICON_OUTLINER_DATA_GP_LAYER, false, false);
    if (layer_.is_locked() || !layer_.parent_group().is_visible()) {
      UI_but_disable(but, "Layer is locked or not visible");
    }
  }

  void build_layer_buttons(uiLayout &row)
  {
    PointerRNA layer_ptr;
    RNA_pointer_create(&grease_pencil_.id, &RNA_GreasePencilLayer, &layer_, &layer_ptr);

    uiItemR(&row, &layer_ptr, "hide", UI_ITEM_R_ICON_ONLY, nullptr, 0);
    uiItemR(&row, &layer_ptr, "lock", UI_ITEM_R_ICON_ONLY, nullptr, 0);
  }
};

class LayerGroupViewItem : public AbstractTreeViewItem {
 public:
  LayerGroupViewItem(GreasePencil &grease_pencil, LayerGroup &group)
      : grease_pencil_(grease_pencil), group_(group)
  {
    this->disable_activatable();
    this->label_ = group_.name();
  }

  void build_row(uiLayout &row) override
  {
    build_layer_group_name(row);

    uiLayout *sub = uiLayoutRow(&row, true);
    uiLayoutSetPropDecorate(sub, false);

    build_layer_group_buttons(*sub);
  }

  bool supports_collapsing() const override
  {
    return true;
  }

  bool supports_renaming() const override
  {
    return true;
  }

  bool rename(StringRefNull new_name) override
  {
    grease_pencil_.rename_group(group_, new_name);
    return true;
  }

  StringRef get_rename_string() const override
  {
    return group_.name();
  }

 private:
  GreasePencil &grease_pencil_;
  LayerGroup &group_;

  void build_layer_group_name(uiLayout &row)
  {
    uiItemS_ex(&row, 0.8f);
    uiBut *but = uiItemL_ex(&row, IFACE_(group_.name().c_str()), ICON_FILE_FOLDER, false, false);
    if (group_.is_locked()) {
      UI_but_disable(but, "Layer Group is locked");
    }
  }

  void build_layer_group_buttons(uiLayout &row)
  {
    PointerRNA group_ptr;
    RNA_pointer_create(&grease_pencil_.id, &RNA_GreasePencilLayerGroup, &group_, &group_ptr);

    uiItemR(&row, &group_ptr, "hide", UI_ITEM_R_ICON_ONLY, nullptr, 0);
    uiItemR(&row, &group_ptr, "lock", UI_ITEM_R_ICON_ONLY, nullptr, 0);
  }
};

class LayerTreeView : public AbstractTreeView {
 public:
  explicit LayerTreeView(GreasePencil &grease_pencil) : grease_pencil_(grease_pencil) {}

  void build_tree() override;

 private:
  void build_tree_node_recursive(TreeViewOrItem &parent, TreeNode &node);
  GreasePencil &grease_pencil_;
};

void LayerTreeView::build_tree_node_recursive(TreeViewOrItem &parent, TreeNode &node)
{
  using namespace blender::bke::greasepencil;
  if (node.is_layer()) {
    LayerViewItem &item = parent.add_tree_item<LayerViewItem>(this->grease_pencil_,
                                                              node.as_layer_for_write());
    item.set_collapsed(false);
  }
  else if (node.is_group()) {
    LayerGroupViewItem &group_item = parent.add_tree_item<LayerGroupViewItem>(
        this->grease_pencil_, node.as_group_for_write());
    group_item.set_collapsed(false);
    LISTBASE_FOREACH_BACKWARD (GreasePencilLayerTreeNode *, node_, &node.as_group().children) {
      build_tree_node_recursive(group_item, node_->wrap());
    }
  }
}

void LayerTreeView::build_tree()
{
  using namespace blender::bke::greasepencil;
  LISTBASE_FOREACH_BACKWARD (
      GreasePencilLayerTreeNode *, node, &this->grease_pencil_.root_group.children)
  {
    this->build_tree_node_recursive(*this, node->wrap());
  }
}

}  // namespace blender::ui::greasepencil

void uiTemplateGreasePencilLayerTree(uiLayout *layout, bContext *C)
{
  using namespace blender;

  Object *object = CTX_data_active_object(C);
  if (!object || object->type != OB_GREASE_PENCIL) {
    return;
  }
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);

  uiBlock *block = uiLayoutGetBlock(layout);

  ui::AbstractTreeView *tree_view = UI_block_add_view(
      *block,
      "Grease Pencil Layer Tree View",
      std::make_unique<blender::ui::greasepencil::LayerTreeView>(grease_pencil));
  tree_view->set_min_rows(3);

  ui::TreeViewBuilder::build_tree_view(*tree_view, *layout);
}
