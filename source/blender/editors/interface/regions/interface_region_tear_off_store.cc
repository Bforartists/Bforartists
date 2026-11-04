/* SPDX-FileCopyrightText: 2026 Bforartists Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edinterface
 *
 * BFA - Tear-Off Menu/Panel: pinned tear-offs in the file and the startup file. They're stored on
 * their workspace as a system property, so Blender decides where they come from: with Load UI on
 * from the file's workspaces, and off from the ones the session keeps. That property needs no DNA
 * change or versioning. Blender doesn't show it, and keeps it when it saves.
 *
 * In the session, the list on a workspace only holds what's still to restore. The open pins are the
 * truth, and they join the list only for the length of a file write, see #TearOffSaveScope.
 */

#include <string>

#include "DNA_ID.h"
#include "DNA_screen_types.h"
#include "DNA_windowmanager_types.h"
#include "DNA_workspace_types.h"

#include "BLI_listbase.hh"
#include "BLI_string.hh"
#include "BLI_threads.hh"
#include "BLI_vector.hh"

#include "BKE_context.hh"
#include "BKE_idprop.hh"
#include "BKE_main.hh"
#include "BKE_screen.hh"
#include "BKE_workspace.hh"

#include "WM_api.hh"

#include "UI_interface_c.hh"

#include "interface_intern.hh"
#include "wm_event_system.hh"

namespace blender::ui {

namespace idprop = bke::idprop;

/** The key on #ID::system_properties. A group of groups named by a counter, oldest first, because
 * an #IDP_IDPARRAY can't remove from the middle. */
static constexpr const char *TEAR_OFF_LIST_KEY = "bfa_tear_offs";
/** Raise this when a field changes meaning. An entry with another number is kept unread. */
static constexpr int TEAR_OFF_ENTRY_VERSION = 1;

/* -------------------------------------------------------------------- */
/** \name Reading File Data
 * \{ */

/* A file can hold anything. A group's lookups need its name map, and a duplicate name can hang a
 * removal in a release build, so this comes before any lookup or removal on file data. */
static bool group_is_sound(const IDProperty *prop)
{
  if (prop->type != IDP_GROUP) {
    return false;
  }
  if (prop->len == 0) {
    return BLI_listbase_is_empty(&prop->data.group);
  }
  return prop->data.children_map && prop->data.children_map->children.size() == prop->len;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Writing Entries
 * \{ */

static void field_add(IDProperty *entry, const char *name, const int value)
{
  IDP_AddToGroup(entry, idprop::create(name, int32_t(value)).release());
}

static void field_add(IDProperty *entry, const char *name, const float value)
{
  IDP_AddToGroup(entry, idprop::create(name, value).release());
}

static void field_add(IDProperty *entry, const char *name, const char *value)
{
  IDP_AddToGroup(entry, idprop::create(name, StringRefNull(value)).release());
}

static void field_add_bool(IDProperty *entry, const char *name, const bool value)
{
  IDP_AddToGroup(entry, idprop::create_bool(name, value).release());
}

/* The editor it came from, in the screen this workspace has in this window. There can be two of a
 * type. -1 means the first match, as #tear_off_context_ensure does. */
static int entry_area_index(const wmWindow &win, const PopupBlockHandle &handle)
{
  const WorkSpaceLayout *layout = BKE_workspace_active_layout_for_workspace_get(
      win.workspace_hook, handle.tear_off_workspace);
  const bScreen *screen = layout ? BKE_workspace_layout_screen_get(layout) : nullptr;
  return (screen && handle.ctx_area) ? BLI_findindex(&screen->areabase, handle.ctx_area) : -1;
}

/**
 * Null if it can't be stored: an enum whose ID is already gone has no name to find it by, and a
 * popover with no panel type has nothing to recreate.
 */
static IDProperty *entry_create(Main *bmain,
                                const wmWindow &win,
                                const PopupBlockHandle &handle,
                                const int index)
{
  const char *panel_idname = tear_off_panel_idname(&handle);
  auto entry = idprop::create_group(std::to_string(index));

  if (handle.tear_off_enum_source) {
    field_add(entry.get(), "kind", "ENUM");
    if (!enum_tear_off_store(handle.tear_off_enum_source, bmain, entry.get())) {
      return nullptr;
    }
  }
  else if (panel_idname) {
    field_add(entry.get(), "kind", "PANEL");
    field_add(entry.get(), "idname", panel_idname);
    field_add_bool(entry.get(), "from_region", handle.tear_off_from_region);
    field_add(entry.get(), "width", handle.tear_off_width);
    field_add(entry.get(), "width_default", handle.tear_off_width_default);
    field_add(entry.get(), "width_chrome", handle.tear_off_width_chrome);
  }
  else if (handle.menu_idname[0] != '\0') {
    field_add(entry.get(), "kind", "MENU");
    field_add(entry.get(), "idname", handle.menu_idname);
  }
  else {
    return nullptr;
  }

  /* Without UI scale, so it means the same at another scale. The height counts from the window's
   * top, so a shorter window keeps a pin near the top. */
  const int win_height = WM_window_native_pixel_size(&win)[1];
  const float scale = (handle.tear_off_scale_fac > 0.0f) ? handle.tear_off_scale_fac :
                                                           UI_SCALE_FAC;
  field_add(entry.get(), "version", TEAR_OFF_ENTRY_VERSION);
  field_add(entry.get(), "winid", win.winid);
  field_add(entry.get(), "space", int(handle.tear_off_spacetype));
  field_add(entry.get(), "region", handle.tear_off_ctx_region_type);
  field_add(entry.get(), "area_index", entry_area_index(win, handle));
  /* A string, because the enum's numbers can change in any merge. */
  field_add(entry.get(), "mode", CTX_data_mode_string_from_enum(handle.tear_off_mode));
  field_add(entry.get(), "x", float(handle.tear_off_pin_xy[0]) / UI_SCALE_FAC);
  field_add(entry.get(), "y", float(win_height - handle.tear_off_pin_xy[1]) / UI_SCALE_FAC);
  field_add_bool(entry.get(), "collapsed", handle.tear_off_collapsed);
  field_add(entry.get(), "height", handle.tear_off_user_height);
  field_add(entry.get(), "scroll", handle.scrolloffset / scale);
  return entry.release();
}

/* Temporary windows, such as Preferences, don't count. Nothing there could bring a pin back, so it
 * would be saved again forever. Added after `index` entries, oldest first. */
static void entries_add_open_pins(Main *bmain,
                                  wmWindowManager *wm,
                                  const WorkSpace *workspace,
                                  IDProperty *list,
                                  int &index)
{
  for (wmWindow &win : wm->windows) {
    if (WM_window_is_temp_screen(&win)) {
      continue;
    }
    /* New handlers go at the head, so the oldest pin is last. */
    for (wmEventHandler *handler = win.runtime->modalhandlers.last(); handler;
         handler = handler->prev)
    {
      const PopupBlockHandle *handle = tear_off_from_handler(handler);
      if (handle == nullptr || handle->tear_off_workspace != workspace) {
        continue;
      }
      if (IDProperty *entry = entry_create(bmain, win, *handle, index)) {
        IDP_AddToGroup(list, entry);
        index++;
      }
    }
  }
}

static bool workspace_has_open_pins(wmWindowManager *wm, const WorkSpace *workspace)
{
  for (wmWindow &win : wm->windows) {
    if (WM_window_is_temp_screen(&win)) {
      continue;
    }
    for (wmEventHandler &handler : win.runtime->modalhandlers) {
      const PopupBlockHandle *handle = tear_off_from_handler(&handler);
      if (handle && handle->tear_off_workspace == workspace) {
        return true;
      }
    }
  }
  return false;
}

/* Copied under a new counter, because the names in a list can collide with new ones. An unknown
 * version is kept as it is, for the Bforartists that wrote it. */
static void entries_copy(const IDProperty *from, IDProperty *to, int &index)
{
  for (const IDProperty &entry : from->data.group) {
    if (!group_is_sound(&entry)) {
      continue;
    }
    IDProperty *copy = IDP_CopyProperty(&entry);
    STRNCPY(copy->name, std::to_string(index).c_str());
    IDP_AddToGroup(to, copy);
    index++;
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Saving
 * \{ */

struct TearOffSaveScope::Data {
  struct Swap {
    WorkSpace *workspace;
    /** The list as the session has it, off the workspace for the length of the write. */
    IDProperty *list;
  };
  Vector<Swap> swaps;
};

TearOffSaveScope::TearOffSaveScope(Main *bmain, wmWindowManager *wm)
{
  /* #wm_file_write allows for other threads, and popups don't. */
  if (wm == nullptr || !BLI_thread_is_main()) {
    return;
  }
  for (WorkSpace &workspace : bmain->workspaces) {
    if (!workspace_has_open_pins(wm, &workspace)) {
      continue;
    }
    IDProperty *root = IDP_ID_system_properties_ensure(&workspace.id);
    if (!group_is_sound(root)) {
      continue;
    }
    auto list = idprop::create_group(TEAR_OFF_LIST_KEY);
    int index = 0;
    IDProperty *list_session = IDP_GetPropertyFromGroup(root, TEAR_OFF_LIST_KEY);
    if (list_session) {
      if (group_is_sound(list_session)) {
        entries_copy(list_session, list.get(), index);
      }
      IDP_RemoveFromGroup(root, list_session);
    }
    entries_add_open_pins(bmain, wm, &workspace, list.get(), index);
    IDP_AddToGroup(root, list.release());

    if (data_ == nullptr) {
      data_ = MEM_new<Data>(__func__);
    }
    data_->swaps.append({&workspace, list_session});
  }
}

TearOffSaveScope::~TearOffSaveScope()
{
  if (data_ == nullptr) {
    return;
  }
  for (const Data::Swap &swap : data_->swaps) {
    IDProperty *root = IDP_ID_system_properties_get(&swap.workspace->id);
    IDP_FreeFromGroup(root, IDP_GetPropertyFromGroup(root, TEAR_OFF_LIST_KEY));
    if (swap.list) {
      IDP_AddToGroup(root, swap.list);
    }
  }
  MEM_delete(data_);
}

/** \} */

}  // namespace blender::ui
