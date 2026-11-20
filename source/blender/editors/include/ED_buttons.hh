/* SPDX-FileCopyrightText: 2013 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup editors
 */

#pragma once

#include "BLI_vector.hh"

#include "DNA_space_types.h"

namespace blender {

struct ScrArea;
struct SpaceProperties;
struct bContext;
struct PointerRNA;

namespace ui {
struct Layout;
}  // namespace ui

/**
 * Fills an array with the tab context values for the properties editor. -1 signals a separator.
 *
 * \return The total number of items in the array returned.
 */
Vector<eSpaceButtons_Context> ED_buttons_tabs_list(const SpaceProperties *sbuts,
                                                   bool apply_filter = true);
void ED_buttons_visible_tabs_menu(bContext *C, ui::Layout *layout, void * /*arg*/);
void ED_buttons_navbar_menu(bContext *C, ui::Layout *layout, void * /*arg*/);
bool ED_buttons_tab_has_search_result(SpaceProperties *sbuts, int index);

void ED_buttons_search_string_set(SpaceProperties *sbuts, const char *value);
int ED_buttons_search_string_length(SpaceProperties *sbuts);
const char *ED_buttons_search_string_get(SpaceProperties *sbuts);

bool ED_buttons_should_sync_with_outliner(const bContext *C,
                                          const SpaceProperties *sbuts,
                                          ScrArea *area);
void ED_buttons_set_context(const bContext *C,
                            SpaceProperties *sbuts,
                            PointerRNA *ptr,
                            eSpaceButtons_Context context);
/* BFA - Tear-Off Menu/Panel: the #PanelType::context value that the given tab shows, so a torn-off
 * panel can tell its tab is no longer active. Popups never run the filter in panel_add_check. */
const char *ED_buttons_tab_context_string(short mainb);
/* BFA - Tear-Off Menu/Panel: the tab that shows panels with this #PanelType::context, -1 if there
 * is none. */
int ED_buttons_tab_from_context_string(const char *context);
/**
 * BFA - Tear-Off Menu/Panel: a panel torn off the Properties editor stays when the editor changes
 * tab, but the editor only resolves context members ("light", "material", ...) for its current
 * tab. Between `begin` and `end` the editor answers as if `tab` were active, so the panel's poll,
 * its draw and the operators of its buttons find their data.
 *
 * \return false when nothing was changed: `tab` is the current tab already, or it has no data to
 * show (a Light panel with a mesh active). Only call `end` after a `begin` that returned true.
 */
bool ED_buttons_tab_override_begin(const bContext *C,
                                   SpaceProperties *sbuts,
                                   int tab,
                                   int *r_tab_prev);
/** `sbuts` may have been freed in between (an operator closed the editor or loaded a file). */
void ED_buttons_tab_override_end(const bContext *C, SpaceProperties *sbuts, int tab, int tab_prev);

}  // namespace blender
