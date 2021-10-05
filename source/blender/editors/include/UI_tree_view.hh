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

/** \file
 * \ingroup editorui
 */

#pragma once

#include <functional>
#include <memory>
#include <string>

#include "BLI_function_ref.hh"
#include "BLI_vector.hh"

#include "UI_resources.h"

struct bContext;
struct PointerRNA;
struct uiBlock;
struct uiBut;
struct uiButTreeRow;
struct uiLayout;
struct wmEvent;
struct wmDrag;

namespace blender::ui {

class AbstractTreeView;
class AbstractTreeViewItem;

/* ---------------------------------------------------------------------- */
/** \name Tree-View Item Container
 * \{ */

/**
 * Helper base class to expose common child-item data and functionality to both #AbstractTreeView
 * and #AbstractTreeViewItem.
 *
 * That means this type can be used whenever either a #AbstractTreeView or a
 * #AbstractTreeViewItem is needed.
 */
class TreeViewItemContainer {
  friend class AbstractTreeView;
  friend class AbstractTreeViewItem;

  /* Private constructor, so only the friends above can create this! */
  TreeViewItemContainer() = default;

 protected:
  Vector<std::unique_ptr<AbstractTreeViewItem>> children_;
  /** Adding the first item to the root will set this, then it's passed on to all children. */
  TreeViewItemContainer *root_ = nullptr;
  /** Pointer back to the owning item. */
  AbstractTreeViewItem *parent_ = nullptr;

 public:
  enum class IterOptions {
    None = 0,
    SkipCollapsed = 1 << 0,

    /* Keep ENUM_OPERATORS() below updated! */
  };
  using ItemIterFn = FunctionRef<void(AbstractTreeViewItem &)>;

  /**
   * Convenience wrapper taking the arguments needed to construct an item of type \a ItemT. Calls
   * the version just below.
   */
  template<class ItemT, typename... Args> ItemT &add_tree_item(Args &&...args)
  {
    static_assert(std::is_base_of<AbstractTreeViewItem, ItemT>::value,
                  "Type must derive from and implement the AbstractTreeViewItem interface");

    return dynamic_cast<ItemT &>(
        add_tree_item(std::make_unique<ItemT>(std::forward<Args>(args)...)));
  }

  AbstractTreeViewItem &add_tree_item(std::unique_ptr<AbstractTreeViewItem> item);

 protected:
  void foreach_item_recursive(ItemIterFn iter_fn, IterOptions options = IterOptions::None) const;
};

ENUM_OPERATORS(TreeViewItemContainer::IterOptions,
               TreeViewItemContainer::IterOptions::SkipCollapsed);

/** \} */

/* ---------------------------------------------------------------------- */
/** \name Tree-View Builders
 * \{ */

class TreeViewBuilder {
  uiBlock &block_;

 public:
  TreeViewBuilder(uiBlock &block);

  void build_tree_view(AbstractTreeView &tree_view);
};

class TreeViewLayoutBuilder {
  uiBlock &block_;

  friend TreeViewBuilder;

 public:
  void build_row(AbstractTreeViewItem &item) const;
  uiBlock &block() const;
  uiLayout *current_layout() const;

 private:
  /* Created through #TreeViewBuilder. */
  TreeViewLayoutBuilder(uiBlock &block);
};

/** \} */

/* ---------------------------------------------------------------------- */
/** \name Tree-View Base Class
 * \{ */

class AbstractTreeView : public TreeViewItemContainer {
  friend TreeViewBuilder;
  friend TreeViewLayoutBuilder;

  bool is_reconstructed_ = false;

 public:
  virtual ~AbstractTreeView() = default;

  void foreach_item(ItemIterFn iter_fn, IterOptions options = IterOptions::None) const;

  /** Check if the tree is fully (re-)constructed. That means, both #build_tree() and
   * #update_from_old() have finished. */
  bool is_reconstructed() const;

 protected:
  virtual void build_tree() = 0;

 private:
  /** Match the tree-view against an earlier version of itself (if any) and copy the old UI state
   * (e.g. collapsed, active, selected) to the new one. See
   * #AbstractTreeViewItem.update_from_old(). */
  void update_from_old(uiBlock &new_block);
  static void update_children_from_old_recursive(const TreeViewItemContainer &new_items,
                                                 const TreeViewItemContainer &old_items);
  static AbstractTreeViewItem *find_matching_child(const AbstractTreeViewItem &lookup_item,
                                                   const TreeViewItemContainer &items);
  /** Items may want to do additional work when state changes. But these state changes can only be
   * reliably detected after the tree was reconstructed (see #is_reconstructed()). So this is done
   * delayed. */
  void change_state_delayed();
  void build_layout_from_tree(const TreeViewLayoutBuilder &builder);
};

/** \} */

/* ---------------------------------------------------------------------- */
/** \name Tree-View Item Type
 * \{ */

/** \brief Abstract base class for defining a customizable tree-view item.
 *
 * The tree-view item defines how to build its data into a tree-row. There are implementations for
 * common layouts, e.g. #BasicTreeViewItem.
 * It also stores state information that needs to be persistent over redraws, like the collapsed
 * state.
 */
class AbstractTreeViewItem : public TreeViewItemContainer {
  friend class AbstractTreeView;

 public:
  using IsActiveFn = std::function<bool()>;

 private:
  bool is_open_ = false;
  bool is_active_ = false;

  IsActiveFn is_active_fn_;

 protected:
  /** This label is used for identifying an item (together with its parent's labels). */
  std::string label_{};

 public:
  virtual ~AbstractTreeViewItem() = default;

  virtual void build_row(uiLayout &row) = 0;

  virtual void on_activate();
  virtual void is_active(IsActiveFn is_active_fn);
  virtual bool on_drop(const wmDrag &drag);
  virtual bool can_drop(const wmDrag &drag) const;
  /** Custom text to display when dragging over a tree item. Should explain what happens when
   * dropping the data onto this item. Will only be used if #AbstractTreeViewItem::can_drop()
   * returns true, so the implementing override doesn't have to check that again.
   * The returned value must be a translated string. */
  virtual std::string drop_tooltip(const bContext &C,
                                   const wmDrag &drag,
                                   const wmEvent &event) const;

  /** Copy persistent state (e.g. is-collapsed flag, selection, etc.) from a matching item of
   * the last redraw to this item. If sub-classes introduce more advanced state they should
   * override this and make it update their state accordingly. */
  virtual void update_from_old(const AbstractTreeViewItem &old);
  /** Compare this item to \a other to check if they represent the same data. This is critical for
   * being able to recognize an item from a previous redraw, to be able to keep its state (e.g.
   * open/closed, active, etc.). Items are only matched if their parents also match.
   * By default this just matches the items names/labels (if their parents match!). If that isn't
   * good enough for a sub-class, that can override it. */
  virtual bool matches(const AbstractTreeViewItem &other) const;

  const AbstractTreeView &get_tree_view() const;
  int count_parents() const;
  void deactivate();
  /** Must not be called before the tree was reconstructed (see #is_reconstructed()). Otherwise we
   * can't be sure about the item state. */
  bool is_active() const;
  void toggle_collapsed();
  /** Must not be called before the tree was reconstructed (see #is_reconstructed()). Otherwise we
   * can't be sure about the item state. */
  bool is_collapsed() const;
  void set_collapsed(bool collapsed);
  bool is_collapsible() const;
  void ensure_parents_uncollapsed();

 protected:
  /** Activates this item, deactivates other items, calls the #AbstractTreeViewItem::on_activate()
   * function and ensures this item's parents are not collapsed (so the item is visible).
   * Must not be called before the tree was reconstructed (see #is_reconstructed()). Otherwise we
   * can't be sure about the current item state and may call state-change update functions
   * incorrectly. */
  void activate();

 private:
  /** See #AbstractTreeView::change_state_delayed() */
  void change_state_delayed();
};

/** \} */

/* ---------------------------------------------------------------------- */
/** \name Predefined Tree-View Item Types
 *
 *  Common, Basic Tree-View Item Types.
 * \{ */

/**
 * The most basic type, just a label with an icon.
 */
class BasicTreeViewItem : public AbstractTreeViewItem {
 public:
  using ActivateFn = std::function<void(BasicTreeViewItem &new_active)>;
  BIFIconID icon;

  BasicTreeViewItem(StringRef label, BIFIconID icon = ICON_NONE);

  void build_row(uiLayout &row) override;
  void on_activate(ActivateFn fn);

 protected:
  /** Created in the #build() function. */
  uiButTreeRow *tree_row_but_ = nullptr;
  /** Optionally passed to the #BasicTreeViewItem constructor. Called when activating this tree
   * view item. This way users don't have to sub-class #BasicTreeViewItem, just to implement
   * custom activation behavior (a common thing to do). */
  ActivateFn activate_fn_;

  uiBut *button();
  BIFIconID get_draw_icon() const;

 private:
  static void tree_row_click_fn(struct bContext *C, void *arg1, void *arg2);

  void on_activate() override;
};

/** \} */

}  // namespace blender::ui
