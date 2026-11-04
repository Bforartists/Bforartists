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

#include <cmath>
#include <cstring>
#include <optional>
#include <string>

#include "DNA_ID.h"
#include "DNA_screen_types.h"
#include "DNA_space_enums.h"
#include "DNA_windowmanager_types.h"
#include "DNA_workspace_types.h"

#include "BLI_listbase.hh"
#include "BLI_math_vector_c.hh"
#include "BLI_string.hh"
#include "BLI_threads.hh"
#include "BLI_vector.hh"

#include "BKE_context.hh"
#include "BKE_idprop.hh"
#include "BKE_main.hh"
#include "BKE_screen.hh"
#include "BKE_wm_runtime.hh"
#include "BKE_workspace.hh"

#include "ED_screen.hh"

#include "RNA_access.hh"

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
/** Restored per window in one pass. What's left waits for the next one. */
static constexpr int TEAR_OFF_RESTORE_MAX = 64;
/** A position beyond this isn't a position. */
static constexpr float TEAR_OFF_POSITION_MAX = 100000.0f;

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

/* Never #IDP_group_lookup_string, which trusts the data: a file can hold a string with no end. */
static std::optional<std::string> read_string(const IDProperty &entry,
                                              const char *name,
                                              const int max_len)
{
  const IDProperty *prop = IDP_GetPropertyFromGroup(&entry, name);
  if (prop == nullptr || prop->type != IDP_STRING || prop->subtype == IDP_STRING_SUB_BYTE) {
    return std::nullopt;
  }
  const char *str = static_cast<const char *>(prop->data.pointer);
  if (str == nullptr || prop->len < 1 || prop->len > max_len ||
      std::memchr(str, '\0', size_t(prop->len)) == nullptr)
  {
    return std::nullopt;
  }
  return std::string(str);
}

/* Python writes floats as doubles, and either is fine here. */
static std::optional<float> read_float(const IDProperty &entry, const char *name)
{
  const IDProperty *prop = IDP_GetPropertyFromGroup(&entry, name);
  if (prop == nullptr || !ELEM(prop->type, IDP_FLOAT, IDP_DOUBLE)) {
    return std::nullopt;
  }
  const float value = (prop->type == IDP_FLOAT) ? IDP_float_get(prop) : float(IDP_double_get(prop));
  if (!std::isfinite(value) || std::abs(value) > TEAR_OFF_POSITION_MAX) {
    return std::nullopt;
  }
  return value;
}

/** What an entry holds, as plain values. The list can change while a pin is being created. */
struct EntryData {
  std::string kind;
  std::string idname;
  bool from_region = false;
  int winid = 0;
  int space = 0;
  int region = -1;
  int area_index = -1;
  std::string mode;
  float x = 0.0f;
  float y = 0.0f;
  bool collapsed = false;
  float height = 0.0f;
  float scroll = 0.0f;
};

/* False if this isn't what a known version writes. */
static bool entry_read(const IDProperty &entry, EntryData &r_data)
{
  const std::optional<std::string> kind = read_string(entry, "kind", 16);
  const std::optional<int> winid = IDP_group_lookup_int(entry, "winid");
  const std::optional<int> space = IDP_group_lookup_int(entry, "space");
  const std::optional<int> region = IDP_group_lookup_int(entry, "region");
  const std::optional<int> area_index = IDP_group_lookup_int(entry, "area_index");
  const std::optional<std::string> mode = read_string(entry, "mode", 64);
  const std::optional<float> x = read_float(entry, "x");
  const std::optional<float> y = read_float(entry, "y");
  const std::optional<bool> collapsed = IDP_group_lookup_bool(entry, "collapsed");
  const std::optional<float> height = read_float(entry, "height");
  const std::optional<float> scroll = read_float(entry, "scroll");
  if (!(kind && winid && space && region && area_index && mode && x && y && collapsed && height &&
        scroll))
  {
    return false;
  }
  /* Zero and -1 are real values: no area, and no region. */
  if (*space < 0 || *space >= SPACE_TYPE_NUM || *region < -1 || *region >= RGN_TYPE_NUM ||
      *area_index < -1 || *height < 0.0f)
  {
    return false;
  }
  r_data.kind = *kind;
  r_data.winid = *winid;
  r_data.space = *space;
  r_data.region = *region;
  r_data.area_index = *area_index;
  r_data.mode = *mode;
  r_data.x = *x;
  r_data.y = *y;
  r_data.collapsed = *collapsed;
  r_data.height = *height;
  r_data.scroll = *scroll;
  if (ELEM(r_data.kind, "MENU", "PANEL")) {
    const std::optional<std::string> idname = read_string(entry, "idname", MAX_NAME);
    if (!idname) {
      return false;
    }
    r_data.idname = *idname;
  }
  if (r_data.kind == "PANEL") {
    const std::optional<bool> from_region = IDP_group_lookup_bool(entry, "from_region");
    if (!from_region) {
      return false;
    }
    r_data.from_region = *from_region;
  }
  return true;
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
/** \name Pins That Close Without Being Removed
 * \{ */

/* Null if the workspace's properties can't be trusted. A list of the wrong type goes, as nothing
 * could read it. */
static IDProperty *list_ensure(WorkSpace *workspace)
{
  IDProperty *root = IDP_ID_system_properties_ensure(&workspace->id);
  if (!group_is_sound(root)) {
    return nullptr;
  }
  IDProperty *list = IDP_GetPropertyFromGroup(root, TEAR_OFF_LIST_KEY);
  if (list && !group_is_sound(list)) {
    IDP_FreeFromGroup(root, list);
    list = nullptr;
  }
  if (list == nullptr) {
    list = idprop::create_group(TEAR_OFF_LIST_KEY).release();
    IDP_AddToGroup(root, list);
  }
  return list;
}

/* A file with no pins has no list. */
static void list_free_if_empty(WorkSpace *workspace, IDProperty *list)
{
  if (list->len == 0) {
    IDP_FreeFromGroup(IDP_ID_system_properties_get(&workspace->id), list);
  }
}

/* An entry can have any name in a file, so the next counter isn't always free. */
static int list_next_index(const IDProperty *list)
{
  int index = list->len;
  while (IDP_GetPropertyFromGroup(list, std::to_string(index))) {
    index++;
  }
  return index;
}

void tear_off_store_closing_all(Main *bmain, wmWindowManager *wm)
{
  for (WorkSpace &workspace : bmain->workspaces) {
    if (!workspace_has_open_pins(wm, &workspace)) {
      continue;
    }
    if (IDProperty *list = list_ensure(&workspace)) {
      int index = list_next_index(list);
      entries_add_open_pins(bmain, wm, &workspace, list, index);
      list_free_if_empty(&workspace, list);
    }
  }
}

void tear_off_store_closing_one(Main *bmain, const wmWindow *win, const PopupBlockHandle *handle)
{
  /* The workspace can be on its way out, with the handle not yet told. */
  if (WM_window_is_temp_screen(win) ||
      BLI_findindex(&bmain->workspaces, handle->tear_off_workspace) == -1)
  {
    return;
  }
  IDProperty *list = list_ensure(handle->tear_off_workspace);
  if (list == nullptr) {
    return;
  }
  if (IDProperty *entry = entry_create(bmain, *win, *handle, list_next_index(list))) {
    IDP_AddToGroup(list, entry);
    /* Pins close newest first, because that's the order handlers run in. Oldest first on the list
     * means they stack as they did. */
    BLI_remlink(&list->data.group, entry);
    BLI_addhead(&list->data.group, entry);
  }
  list_free_if_empty(handle->tear_off_workspace, list);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Restoring
 * \{ */

void tear_off_restore_tag(wmWindowManager *wm)
{
  wm->runtime->tear_off_restore_pending = true;
}

/* The source editor in the window's current screen, as #tear_off_context_ensure finds it: the one
 * it came from if that's still the same type, or else the first of the type. */
static bool entry_area_resolve(const wmWindow &win,
                               const bScreen &screen,
                               const EntryData &data,
                               ScrArea **r_area,
                               ARegion **r_region)
{
  *r_area = nullptr;
  *r_region = nullptr;
  if (data.space == 0) {
    return true;
  }
  ScrArea *found = nullptr;
  if (data.area_index >= 0) {
    ScrArea *area = static_cast<ScrArea *>(BLI_findlink(&screen.areabase, data.area_index));
    if (area && area->spacetype == data.space) {
      found = area;
    }
  }
  if (found == nullptr) {
    ED_screen_areas_iter (&win, &screen, area) {
      if (area->spacetype == data.space) {
        found = area;
        break;
      }
    }
  }
  if (found == nullptr) {
    return false;
  }
  *r_area = found;
  if (data.region == -1) {
    return true;
  }
  /* A pin with a space type and no region would count as having no source. */
  *r_region = BKE_area_find_region_type(found, data.region);
  return *r_region != nullptr;
}

/* The type must belong to this editor or be registered by name. The all-spaces fallback of
 * #tear_off_paneltype_find is for pins made in the session: a file naming a panel of another
 * editor could crash its C poll. */
static bool entry_panel_type_exists(const ARegion *region, const std::string &idname)
{
  if (region && region->runtime->type) {
    for (const PanelType &pt : region->runtime->type->paneltypes) {
      if (idname == pt.idname) {
        return true;
      }
    }
  }
  return WM_paneltype_find(idname.c_str(), true) != nullptr;
}

/* Sets the handle's fields. Direct, as the setter of the collapsed state would overwrite the
 * position. The refresh that #tear_off_handle_init tagged moves it there before anything draws. */
static void entry_apply(const EntryData &data,
                        wmWindow *win,
                        PopupBlockHandle *handle)
{
  handle->tear_off_user_height = data.height;
  /* Scale free floats, rounded, which stay exact at the same scale. A live scale change works
   * differently on purpose, as it starts from a position already on the screen. */
  handle->scrolloffset = data.scroll * UI_SCALE_FAC;
  handle->tear_off_collapsed = data.collapsed;
  handle->tear_off_pin_xy[0] = int(std::round(data.x * UI_SCALE_FAC));
  handle->tear_off_pin_xy[1] = WM_window_native_pixel_size(win)[1] -
                               int(std::round(data.y * UI_SCALE_FAC));
  copy_v2_v2_int(handle->popup_create_vars.event_xy, handle->tear_off_pin_xy);
  if (data.collapsed) {
    Block *block = handle->region->runtime->uiblocks.first();
    if (block) {
      tear_off_clamp_to_window(win, handle, block, handle->region);
    }
  }
}

/* With the window, area and region of the entry in the context. A failure stays on the list. */
static bool entry_pin_create(bContext *C, wmWindow *win, const EntryData &data, ARegion *region)
{
  const char *ot_name = nullptr;
  const char *idname_prop = nullptr;
  if (data.kind == "MENU") {
    /* No poll guard in a menu's first layout, unlike a panel's. */
    MenuType *mt = WM_menutype_find(data.idname.c_str(), true);
    if (mt == nullptr || !WM_menutype_poll(C, mt)) {
      return false;
    }
    ot_name = "WM_OT_menu_tear_off";
    idname_prop = "menu_idname";
  }
  else if (data.kind == "PANEL" && !data.from_region) {
    if (!entry_panel_type_exists(region, data.idname)) {
      return false;
    }
    ot_name = "WM_OT_panel_tear_off";
    idname_prop = "panel_idname";
  }
  else {
    return false;
  }

  wmOperatorType *ot = WM_operatortype_find(ot_name, true);
  if (ot == nullptr) {
    return false;
  }
  const PopupBlockHandle *newest = tear_off_newest_popup(win);
  PointerRNA props = WM_operator_properties_create_ptr(ot);
  RNA_string_set(&props, idname_prop, data.idname.c_str());
  /* The region variants would force the window region. */
  WM_operator_name_call_ptr(C, ot, wm::OpCallContext::ExecDefault, &props, nullptr);
  WM_operator_properties_free(&props);

  /* The operators don't return the handle. */
  PopupBlockHandle *handle = tear_off_newest_popup(win);
  if (handle == nullptr || handle == newest || !handle->is_tear_off) {
    return false;
  }
  entry_apply(data, win, handle);
  return true;
}

/* A pin returns to the window it was in, if that window is showing its workspace. */
static bool entry_prefers_other_window(const wmWindowManager &wm,
                                       const wmWindow &win,
                                       const WorkSpace *workspace,
                                       const EntryData &data)
{
  if (data.winid == win.winid) {
    return false;
  }
  for (const wmWindow &other : wm.windows) {
    if (other.winid == data.winid) {
      return WM_window_get_active_workspace(&other) == workspace;
    }
  }
  return false;
}

static void workspace_restore(bContext *C,
                              wmWindowManager *wm,
                              wmWindow *win,
                              WorkSpace *workspace,
                              const bScreen &screen)
{
  IDProperty *root = IDP_ID_system_properties_get(&workspace->id);
  IDProperty *list = IDP_GetPropertyFromGroup(root, TEAR_OFF_LIST_KEY);

  /* Names, because the list can change while a pin is being created. */
  Vector<std::string> names;
  for (const IDProperty &entry : list->data.group) {
    if (names.size() == TEAR_OFF_RESTORE_MAX) {
      break;
    }
    names.append(entry.name);
  }

  for (const std::string &name : names) {
    IDProperty *entry = IDP_GetPropertyFromGroup(list, name);
    if (entry == nullptr || !group_is_sound(entry)) {
      continue;
    }
    const std::optional<int> version = IDP_group_lookup_int(*entry, "version");
    if (version.value_or(0) != TEAR_OFF_ENTRY_VERSION) {
      continue;
    }
    EntryData data;
    if (!entry_read(*entry, data)) {
      IDP_FreeFromGroup(list, entry);
      continue;
    }
    if (entry_prefers_other_window(*wm, *win, workspace, data)) {
      continue;
    }
    ScrArea *area;
    ARegion *region;
    if (!entry_area_resolve(*win, screen, data, &area, &region)) {
      continue;
    }
    CTX_wm_area_set(C, area);
    CTX_wm_region_set(C, region);
    /* It waits for its mode. A pin with no source ignores the mode, as #tear_off_is_visible does. */
    const bool mode_matches = data.space == 0 || data.mode.empty() ||
                              data.mode == CTX_data_mode_string(C);
    if (mode_matches && entry_pin_create(C, win, data, region)) {
      list = IDP_GetPropertyFromGroup(root, TEAR_OFF_LIST_KEY);
      if (IDProperty *entry_now = list ? IDP_GetPropertyFromGroup(list, name) : nullptr) {
        IDP_FreeFromGroup(list, entry_now);
      }
    }
    CTX_wm_area_set(C, nullptr);
    CTX_wm_region_set(C, nullptr);
    if (list == nullptr) {
      return;
    }
  }
  list_free_if_empty(workspace, list);
}

/* The workspace's list if it has one that can be read. */
static bool workspace_has_entries(WorkSpace *workspace)
{
  const IDProperty *root = IDP_ID_system_properties_get(&workspace->id);
  if (root == nullptr || !group_is_sound(root)) {
    return false;
  }
  const IDProperty *list = IDP_GetPropertyFromGroup(root, TEAR_OFF_LIST_KEY);
  return list && group_is_sound(list) && list->len > 0;
}

void tear_off_restore_pending_run(bContext *C, wmWindowManager *wm)
{
  if (!wm->runtime->tear_off_restore_pending) {
    return;
  }
  wm->runtime->tear_off_restore_pending = false;
  if (G.background || !tear_off_enabled()) {
    return;
  }
  for (wmWindow &win : wm->windows) {
    if (win.runtime->ghostwin == nullptr || WM_window_is_temp_screen(&win)) {
      continue;
    }
    WorkSpace *workspace = WM_window_get_active_workspace(&win);
    bScreen *screen = WM_window_get_active_screen(&win);
    if (workspace == nullptr || screen == nullptr || !workspace_has_entries(workspace)) {
      continue;
    }
    /* They wait for the splash and such, or they'd land on top of it. */
    if (wm->runtime->is_interface_locked || screen_has_blocking_popup(screen)) {
      wm->runtime->tear_off_restore_pending = true;
      continue;
    }
    CTX_wm_window_set(C, &win);
    ED_screen_ensure_updated(C, wm, &win);
    workspace_restore(C, wm, &win, workspace, *screen);
  }
  CTX_wm_window_set(C, nullptr);
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
