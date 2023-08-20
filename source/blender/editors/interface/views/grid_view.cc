/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edinterface
 */

#include <limits>
#include <stdexcept>

#include "BKE_icons.h"

#include "BLI_index_range.hh"

#include "WM_types.hh"

#include "UI_interface.hh"
#include "interface_intern.hh"

#include "UI_grid_view.hh"

namespace blender::ui {

/* ---------------------------------------------------------------------- */

AbstractGridView::AbstractGridView() : style_(UI_preview_tile_size_x(), UI_preview_tile_size_y())
{
}

AbstractGridViewItem &AbstractGridView::add_item(std::unique_ptr<AbstractGridViewItem> item)
{
  items_.append(std::move(item));

  AbstractGridViewItem &added_item = *items_.last();
  item_map_.add(added_item.identifier_, &added_item);
  register_item(added_item);

  return added_item;
}

/* Implementation for the base class virtual function. More specialized iterators below. */
void AbstractGridView::foreach_view_item(FunctionRef<void(AbstractViewItem &)> iter_fn) const
{
  for (const auto &item_ptr : items_) {
    iter_fn(*item_ptr);
  }
}

void AbstractGridView::foreach_item(ItemIterFn iter_fn) const
{
  for (const auto &item_ptr : items_) {
    iter_fn(*item_ptr);
  }
}

void AbstractGridView::foreach_filtered_item(ItemIterFn iter_fn) const
{
  for (const auto &item_ptr : items_) {
    if (item_ptr->is_filtered_visible_cached()) {
      iter_fn(*item_ptr);
    }
  }
}

AbstractGridViewItem *AbstractGridView::find_matching_item(
    const AbstractGridViewItem &item_to_match, const AbstractGridView &view_to_search_in) const
{
  AbstractGridViewItem *const *match = view_to_search_in.item_map_.lookup_ptr(
      item_to_match.identifier_);
  BLI_assert(!match || item_to_match.matches(**match));

  return match ? *match : nullptr;
}

void AbstractGridView::update_children_from_old(const AbstractView &old_view)
{
  const AbstractGridView &old_grid_view = dynamic_cast<const AbstractGridView &>(old_view);

  foreach_item([this, &old_grid_view](AbstractGridViewItem &new_item) {
    const AbstractGridViewItem *matching_old_item = find_matching_item(new_item, old_grid_view);
    if (!matching_old_item) {
      return;
    }

    new_item.update_from_old(*matching_old_item);
  });
}

const GridViewStyle &AbstractGridView::get_style() const
{
  return style_;
}

int AbstractGridView::get_item_count() const
{
  return items_.size();
}

int AbstractGridView::get_item_count_filtered() const
{
  if (item_count_filtered_) {
    return *item_count_filtered_;
  }

  int i = 0;
  foreach_filtered_item([&i](const auto &) { i++; });

  BLI_assert(i <= get_item_count());
  item_count_filtered_ = i;
  return i;
}

void AbstractGridView::set_tile_size(int tile_width, int tile_height)
{
  style_.tile_width = tile_width;
  style_.tile_height = tile_height;
}

GridViewStyle::GridViewStyle(int width, int height) : tile_width(width), tile_height(height) {}

/* ---------------------------------------------------------------------- */

AbstractGridViewItem::AbstractGridViewItem(StringRef identifier) : identifier_(identifier) {}

bool AbstractGridViewItem::matches(const AbstractViewItem &other) const
{
  const AbstractGridViewItem &other_grid_item = dynamic_cast<const AbstractGridViewItem &>(other);
  return identifier_ == other_grid_item.identifier_;
}

void AbstractGridViewItem::grid_tile_click_fn(bContext *C, void *but_arg1, void * /*arg2*/)
{
  uiButViewItem *view_item_but = (uiButViewItem *)but_arg1;
  AbstractGridViewItem &grid_item = reinterpret_cast<AbstractGridViewItem &>(
      *view_item_but->view_item);

  grid_item.activate(*C);
}

void AbstractGridViewItem::add_grid_tile_button(uiBlock &block)
{
  const GridViewStyle &style = get_view().get_style();
  view_item_but_ = (uiButViewItem *)uiDefBut(&block,
                                             UI_BTYPE_VIEW_ITEM,
                                             0,
                                             "",
                                             0,
                                             0,
                                             style.tile_width,
                                             style.tile_height,
                                             nullptr,
                                             0,
                                             0,
                                             0,
                                             0,
                                             "");

  view_item_but_->view_item = reinterpret_cast<uiViewItemHandle *>(this);
  UI_but_func_set(view_item_but_, grid_tile_click_fn, view_item_but_, nullptr);
}

AbstractGridView &AbstractGridViewItem::get_view() const
{
  if (UNLIKELY(!view_)) {
    throw std::runtime_error(
        "Invalid state, item must be added through AbstractGridView::add_item()");
  }
  return dynamic_cast<AbstractGridView &>(*view_);
}

/* ---------------------------------------------------------------------- */

std::unique_ptr<DropTargetInterface> AbstractGridViewItem::create_item_drop_target()
{
  return create_drop_target();
}

std::unique_ptr<GridViewItemDropTarget> AbstractGridViewItem::create_drop_target()
{
  return nullptr;
}

GridViewItemDropTarget::GridViewItemDropTarget(AbstractGridView &view) : view_(view) {}

/* ---------------------------------------------------------------------- */

/**
 * Helper for only adding layout items for grid items that are actually in view. 3 main functions:
 * - #is_item_visible(): Query if an item of a given index is visible in the view (others should be
 * skipped when building the layout).
 * - #fill_layout_before_visible(): Add empty space to the layout before a visible row is drawn, so
 *   the layout height is the same as if all items were added (important to get the correct scroll
 *   height).
 * - #fill_layout_after_visible(): Same thing, just adds empty space for after the last visible
 *   row.
 *
 * Does two assumptions:
 * - Top-to-bottom flow (ymax = 0 and ymin < 0). If that's not good enough, View2D should
 *   probably provide queries for the scroll offset.
 * - Only vertical scrolling. For horizontal scrolling, spacers would have to be added on the
 *   side(s) as well.
 */
class BuildOnlyVisibleButtonsHelper {
  const View2D &v2d_;
  const AbstractGridView &grid_view_;
  const GridViewStyle &style_;
  const int cols_per_row_ = 0;
  /* Indices of items within the view. Calculated by constructor */
  IndexRange visible_items_range_{};

 public:
  BuildOnlyVisibleButtonsHelper(const View2D &v2d,
                                const AbstractGridView &grid_view,
                                int cols_per_row);

  bool is_item_visible(int item_idx) const;
  void fill_layout_before_visible(uiBlock &block) const;
  void fill_layout_after_visible(uiBlock &block) const;

 private:
  IndexRange get_visible_range() const;
  void add_spacer_button(uiBlock &block, int row_count) const;
};

BuildOnlyVisibleButtonsHelper::BuildOnlyVisibleButtonsHelper(const View2D &v2d,
                                                             const AbstractGridView &grid_view,
                                                             const int cols_per_row)
    : v2d_(v2d), grid_view_(grid_view), style_(grid_view.get_style()), cols_per_row_(cols_per_row)
{
  visible_items_range_ = get_visible_range();
}

IndexRange BuildOnlyVisibleButtonsHelper::get_visible_range() const
{
  int first_idx_in_view = 0;

  const float scroll_ofs_y = abs(v2d_.cur.ymax - v2d_.tot.ymax);
  if (!IS_EQF(scroll_ofs_y, 0)) {
    const int scrolled_away_rows = int(scroll_ofs_y) / style_.tile_height;

    first_idx_in_view = scrolled_away_rows * cols_per_row_;
  }

  const int view_height = BLI_rcti_size_y(&v2d_.mask);
  const int count_rows_in_view = std::max(view_height / style_.tile_height, 1);
  const int max_items_in_view = (count_rows_in_view + 1) * cols_per_row_;

  BLI_assert(max_items_in_view > 0);
  return IndexRange(first_idx_in_view, max_items_in_view);
}

bool BuildOnlyVisibleButtonsHelper::is_item_visible(const int item_idx) const
{
  return visible_items_range_.contains(item_idx);
}

void BuildOnlyVisibleButtonsHelper::fill_layout_before_visible(uiBlock &block) const
{
  const int first_idx_in_view = visible_items_range_.first();
  if (first_idx_in_view < 1) {
    return;
  }
  const int tot_tiles_before_visible = first_idx_in_view;
  const int scrolled_away_rows = tot_tiles_before_visible / cols_per_row_;
  add_spacer_button(block, scrolled_away_rows);
}

void BuildOnlyVisibleButtonsHelper::fill_layout_after_visible(uiBlock &block) const
{
  const int last_item_idx = grid_view_.get_item_count_filtered() - 1;
  const int last_visible_idx = visible_items_range_.last();

  if (last_item_idx > last_visible_idx) {
    const int remaining_rows = (cols_per_row_ > 0) ? ceilf((last_item_idx - last_visible_idx) /
                                                           float(cols_per_row_)) :
                                                     0;
    BuildOnlyVisibleButtonsHelper::add_spacer_button(block, remaining_rows);
  }
}

void BuildOnlyVisibleButtonsHelper::add_spacer_button(uiBlock &block, const int row_count) const
{
  /* UI code only supports button dimensions of `signed short` size, the layout height we want to
   * fill may be bigger than that. So add multiple labels of the maximum size if necessary. */
  for (int remaining_rows = row_count; remaining_rows > 0;) {
    const short row_count_this_iter = std::min(
        std::numeric_limits<short>::max() / style_.tile_height, remaining_rows);

    uiDefBut(&block,
             UI_BTYPE_LABEL,
             0,
             "",
             0,
             0,
             UI_UNIT_X,
             row_count_this_iter * style_.tile_height,
             nullptr,
             0,
             0,
             0,
             0,
             "");
    remaining_rows -= row_count_this_iter;
  }
}

/* ---------------------------------------------------------------------- */

class GridViewLayoutBuilder {
  uiBlock &block_;

  friend class GridViewBuilder;

 public:
  GridViewLayoutBuilder(uiLayout &layout);

  void build_from_view(const AbstractGridView &grid_view, const View2D &v2d) const;

 private:
  void build_grid_tile(uiLayout &grid_layout, AbstractGridViewItem &item) const;

  uiLayout *current_layout() const;
};

GridViewLayoutBuilder::GridViewLayoutBuilder(uiLayout &layout) : block_(*uiLayoutGetBlock(&layout))
{
}

void GridViewLayoutBuilder::build_grid_tile(uiLayout &grid_layout,
                                            AbstractGridViewItem &item) const
{
  uiLayout *overlap = uiLayoutOverlap(&grid_layout);
  uiLayoutSetFixedSize(overlap, true);

  item.add_grid_tile_button(block_);
  item.build_grid_tile(*uiLayoutRow(overlap, false));
}

void GridViewLayoutBuilder::build_from_view(const AbstractGridView &grid_view,
                                            const View2D &v2d) const
{
  uiLayout *parent_layout = current_layout();

  uiLayout &layout = *uiLayoutColumn(current_layout(), true);
  const GridViewStyle &style = grid_view.get_style();

  const int cols_per_row = std::max(uiLayoutGetWidth(&layout) / style.tile_width, 1);

  BuildOnlyVisibleButtonsHelper build_visible_helper(v2d, grid_view, cols_per_row);

  build_visible_helper.fill_layout_before_visible(block_);

  int item_idx = 0;
  uiLayout *row = nullptr;
  grid_view.foreach_filtered_item([&](AbstractGridViewItem &item) {
    /* Skip if item isn't visible. */
    if (!build_visible_helper.is_item_visible(item_idx)) {
      item_idx++;
      return;
    }

    /* Start a new row for every first item in the row. */
    if ((item_idx % cols_per_row) == 0) {
      row = uiLayoutRow(&layout, true);
    }

    build_grid_tile(*row, item);
    item_idx++;
  });

  UI_block_layout_set_current(&block_, parent_layout);

  build_visible_helper.fill_layout_after_visible(block_);
}

uiLayout *GridViewLayoutBuilder::current_layout() const
{
  return block_.curlayout;
}

/* ---------------------------------------------------------------------- */

GridViewBuilder::GridViewBuilder(uiBlock & /*block*/) {}

void GridViewBuilder::build_grid_view(AbstractGridView &grid_view,
                                      const View2D &v2d,
                                      uiLayout &layout)
{
  uiBlock &block = *uiLayoutGetBlock(&layout);

  grid_view.build_items();
  grid_view.update_from_old(block);
  grid_view.change_state_delayed();

  /* Ensure the given layout is actually active. */
  UI_block_layout_set_current(&block, &layout);

  GridViewLayoutBuilder builder(layout);
  builder.build_from_view(grid_view, v2d);
}

/* ---------------------------------------------------------------------- */

PreviewGridItem::PreviewGridItem(StringRef identifier, StringRef label, int preview_icon_id)
    : AbstractGridViewItem(identifier), label(label), preview_icon_id(preview_icon_id)
{
}

void PreviewGridItem::build_grid_tile(uiLayout &layout) const
{
  const GridViewStyle &style = get_view().get_style();
  uiBlock *block = uiLayoutGetBlock(&layout);

  uiBut *but = uiDefBut(block,
                        UI_BTYPE_PREVIEW_TILE,
                        0,
                        hide_label_ ? "" : label.c_str(),
                        0,
                        0,
                        style.tile_width,
                        style.tile_height,
                        nullptr,
                        0,
                        0,
                        0,
                        0,
                        "");
  /* Draw icons that are not previews or images as normal icons with a fixed icon size. Otherwise
   * they will be upscaled to the button size. Should probably be done by the widget code. */
  const int is_preview_flag = (BKE_icon_is_preview(preview_icon_id) ||
                               BKE_icon_is_image(preview_icon_id)) ?
                                  int(UI_BUT_ICON_PREVIEW) :
                                  0;
  ui_def_but_icon(but,
                  preview_icon_id,
                  /* NOLINTNEXTLINE: bugprone-suspicious-enum-usage */
                  UI_HAS_ICON | is_preview_flag);
  UI_but_func_tooltip_label_set(but, [this](const uiBut * /*but*/) { return label; });
  but->emboss = UI_EMBOSS_NONE;
}

void PreviewGridItem::set_on_activate_fn(ActivateFn fn)
{
  activate_fn_ = fn;
}

void PreviewGridItem::set_is_active_fn(IsActiveFn fn)
{
  is_active_fn_ = fn;
}

void PreviewGridItem::hide_label()
{
  hide_label_ = true;
}

void PreviewGridItem::on_activate(bContext &C)
{
  if (activate_fn_) {
    activate_fn_(C, *this);
  }
}

std::optional<bool> PreviewGridItem::should_be_active() const
{
  if (is_active_fn_) {
    return is_active_fn_();
  }
  return std::nullopt;
}

}  // namespace blender::ui
