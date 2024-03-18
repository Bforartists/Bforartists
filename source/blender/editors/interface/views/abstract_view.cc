/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edinterface
 */

#include "interface_intern.hh"

#include "UI_abstract_view.hh"

using namespace blender;

namespace blender::ui {

void AbstractView::register_item(AbstractViewItem &item)
{
  /* Actually modifies the item, not the view.  But for the public API it "feels" a bit nicer to
   * have the view base class register the items, rather than setting the view on the item. */
  item.view_ = this;
}

/* ---------------------------------------------------------------------- */
/** \name View Reconstruction
 * \{ */

bool AbstractView::is_reconstructed() const
{
  return is_reconstructed_;
}

void AbstractView::update_from_old(uiBlock &new_block)
{
  uiBlock *old_block = new_block.oldblock;
  if (!old_block) {
    is_reconstructed_ = true;
    return;
  }

  uiViewHandle *old_view_handle = ui_block_view_find_matching_in_old_block(
      &new_block, reinterpret_cast<uiViewHandle *>(this));
  if (old_view_handle == nullptr) {
    /* Initial construction, nothing to update. */
    is_reconstructed_ = true;
    return;
  }

  AbstractView &old_view = reinterpret_cast<AbstractView &>(*old_view_handle);

  /* Update own persistent data. */
  /* Keep the rename buffer persistent while renaming! The rename button uses the buffer's
   * pointer to identify itself over redraws. */
  rename_buffer_ = std::move(old_view.rename_buffer_);
  old_view.rename_buffer_ = nullptr;

  update_children_from_old(old_view);

  /* Finished (re-)constructing the tree. */
  is_reconstructed_ = true;
}

/** \} */

/* ---------------------------------------------------------------------- */
/** \name State Management
 * \{ */

void AbstractView::change_state_delayed()
{
  BLI_assert_msg(
      is_reconstructed(),
      "These state changes are supposed to be delayed until reconstruction is completed");

/* Debug-only sanity check: Ensure only one item requests to be active. */
#ifndef NDEBUG
  bool has_active = false;
  foreach_view_item([&has_active](AbstractViewItem &item) {
    if (item.should_be_active().value_or(false)) {
      BLI_assert_msg(
          !has_active,
          "Only one view item should ever return true for its `should_be_active()` method");
      has_active = true;
    }
  });
#endif

  foreach_view_item([](AbstractViewItem &item) { item.change_state_delayed(); });
}

/** \} */

/* ---------------------------------------------------------------------- */
/** \name Default implementations of virtual functions
 * \{ */

std::unique_ptr<DropTargetInterface> AbstractView::create_drop_target()
{
  /* There's no drop target (and hence no drop support) by default. */
  return nullptr;
}

bool AbstractView::listen(const wmNotifier & /*notifier*/) const
{
  /* Nothing by default. */
  return false;
}

bool AbstractView::begin_filtering(const bContext & /*C*/) const
{
  return false;
}

void AbstractView::draw_overlays(const ARegion & /*region*/) const
{
  /* Nothing by default. */
}

/** \} */

/* ---------------------------------------------------------------------- */
/** \name Renaming
 * \{ */

bool AbstractView::is_renaming() const
{
  return rename_buffer_ != nullptr;
}

bool AbstractView::begin_renaming()
{
  if (is_renaming()) {
    return false;
  }

  rename_buffer_ = std::make_unique<decltype(rename_buffer_)::element_type>();
  return true;
}

void AbstractView::end_renaming()
{
  BLI_assert(is_renaming());
  rename_buffer_ = nullptr;
}

Span<char> AbstractView::get_rename_buffer() const
{
  return *rename_buffer_;
}
MutableSpan<char> AbstractView::get_rename_buffer()
{
  return *rename_buffer_;
}

std::optional<rcti> AbstractView::get_bounds() const
{
  return bounds_;
}

/** \} */

}  // namespace blender::ui

/* ---------------------------------------------------------------------- */
/** \name General API functions
 * \{ */

namespace blender::ui {

std::unique_ptr<DropTargetInterface> view_drop_target(uiViewHandle *view_handle)
{
  AbstractView &view = reinterpret_cast<AbstractView &>(*view_handle);
  return view.create_drop_target();
}

}  // namespace blender::ui

bool UI_view_begin_filtering(const bContext *C, const uiViewHandle *view_handle)
{
  const ui::AbstractView &view = reinterpret_cast<const ui::AbstractView &>(*view_handle);
  return view.begin_filtering(*C);
}

/** \} */
