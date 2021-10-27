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
 * \ingroup edasset
 */

#include "BKE_asset.h"
#include "BKE_asset_catalog.hh"
#include "BKE_asset_library.hh"
#include "BKE_context.h"
#include "BKE_lib_id.h"
#include "BKE_main.h"
#include "BKE_report.h"

#include "BLI_string_ref.hh"
#include "BLI_vector.hh"

#include "ED_asset.h"
#include "ED_asset_catalog.hh"
/* XXX needs access to the file list, should all be done via the asset system in future. */
#include "ED_fileselect.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

using namespace blender;

/* -------------------------------------------------------------------- */

using PointerRNAVec = blender::Vector<PointerRNA>;

/**
 * Return the IDs to operate on as PointerRNA vector. Either a single one ("id" context member) or
 * multiple ones ("selected_ids" context member).
 */
static PointerRNAVec asset_operation_get_ids_from_context(const bContext *C)
{
  PointerRNAVec ids;

  PointerRNA idptr = CTX_data_pointer_get_type(C, "id", &RNA_ID);
  if (idptr.data) {
    /* Single ID. */
    ids.append(idptr);
  }
  else {
    ListBase list;
    CTX_data_selected_ids(C, &list);
    LISTBASE_FOREACH (CollectionPointerLink *, link, &list) {
      ids.append(link->ptr);
    }
    BLI_freelistN(&list);
  }

  return ids;
}

/**
 * Information about what's contained in a #PointerRNAVec, returned by
 * #asset_operation_get_id_vec_stats_from_context().
 */
struct IDVecStats {
  bool has_asset = false;
  bool has_supported_type = false;
  bool is_single = false;
};

/**
 * Helper to report stats about the IDs in context. Operator polls use this, also to report a
 * helpful disabled hint to the user.
 */
static IDVecStats asset_operation_get_id_vec_stats_from_context(const bContext *C)
{
  PointerRNAVec pointers = asset_operation_get_ids_from_context(C);
  IDVecStats stats;

  stats.is_single = pointers.size() == 1;

  for (PointerRNA &ptr : pointers) {
    BLI_assert(RNA_struct_is_ID(ptr.type));

    ID *id = static_cast<ID *>(ptr.data);
    if (ED_asset_type_is_supported(id)) {
      stats.has_supported_type = true;
    }
    if (ID_IS_ASSET(id)) {
      stats.has_asset = true;
    }
  }

  return stats;
}

static const char *asset_operation_unsupported_type_msg(const bool is_single)
{
  const char *msg_single =
      "Data-block does not support asset operations - must be "
      "a " ED_ASSET_TYPE_IDS_NON_EXPERIMENTAL_UI_STRING;
  const char *msg_multiple =
      "No data-block selected that supports asset operations - select at least "
      "one " ED_ASSET_TYPE_IDS_NON_EXPERIMENTAL_UI_STRING;
  return is_single ? msg_single : msg_multiple;
}

/* -------------------------------------------------------------------- */

class AssetMarkHelper {
 public:
  void operator()(const bContext &C, PointerRNAVec &ids);

  void reportResults(ReportList &reports) const;
  bool wasSuccessful() const;

 private:
  struct Stats {
    int tot_created = 0;
    int tot_already_asset = 0;
    ID *last_id = nullptr;
  };

  Stats stats;
};

void AssetMarkHelper::operator()(const bContext &C, PointerRNAVec &ids)
{
  for (PointerRNA &ptr : ids) {
    BLI_assert(RNA_struct_is_ID(ptr.type));

    ID *id = static_cast<ID *>(ptr.data);
    if (id->asset_data) {
      stats.tot_already_asset++;
      continue;
    }

    if (ED_asset_mark_id(id)) {
      ED_asset_generate_preview(&C, id);

      stats.last_id = id;
      stats.tot_created++;
    }
  }
}

bool AssetMarkHelper::wasSuccessful() const
{
  return stats.tot_created > 0;
}

void AssetMarkHelper::reportResults(ReportList &reports) const
{
  /* User feedback on failure. */
  if (!wasSuccessful()) {
    if (stats.tot_already_asset > 0) {
      BKE_report(&reports,
                 RPT_ERROR,
                 "Selected data-blocks are already assets (or do not support use as assets)");
    }
    else {
      BKE_report(&reports,
                 RPT_ERROR,
                 "No data-blocks to create assets for found (or do not support use as assets)");
    }
  }
  /* User feedback on success. */
  else if (stats.tot_created == 1) {
    /* If only one data-block: Give more useful message by printing asset name. */
    BKE_reportf(&reports, RPT_INFO, "Data-block '%s' is now an asset", stats.last_id->name + 2);
  }
  else {
    BKE_reportf(&reports, RPT_INFO, "%i data-blocks are now assets", stats.tot_created);
  }
}

static int asset_mark_exec(bContext *C, wmOperator *op)
{
  PointerRNAVec ids = asset_operation_get_ids_from_context(C);

  AssetMarkHelper mark_helper;
  mark_helper(*C, ids);
  mark_helper.reportResults(*op->reports);

  if (!mark_helper.wasSuccessful()) {
    return OPERATOR_CANCELLED;
  }

  WM_main_add_notifier(NC_ID | NA_EDITED, nullptr);
  WM_main_add_notifier(NC_ASSET | NA_ADDED, nullptr);

  return OPERATOR_FINISHED;
}

static bool asset_mark_poll(bContext *C)
{
  IDVecStats ctx_stats = asset_operation_get_id_vec_stats_from_context(C);

  if (!ctx_stats.has_supported_type) {
    CTX_wm_operator_poll_msg_set(C, asset_operation_unsupported_type_msg(ctx_stats.is_single));
    return false;
  }

  return true;
}

static void ASSET_OT_mark(wmOperatorType *ot)
{
  ot->name = "Mark as Asset";
  ot->description =
      "Enable easier reuse of selected data-blocks through the Asset Browser, with the help of "
      "customizable metadata (like previews, descriptions and tags)";
  ot->idname = "ASSET_OT_mark";

  ot->exec = asset_mark_exec;
  ot->poll = asset_mark_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* -------------------------------------------------------------------- */

class AssetClearHelper {
  const bool set_fake_user_;

 public:
  AssetClearHelper(const bool set_fake_user) : set_fake_user_(set_fake_user)
  {
  }

  void operator()(PointerRNAVec &ids);

  void reportResults(const bContext *C, ReportList &reports) const;
  bool wasSuccessful() const;

 private:
  struct Stats {
    int tot_cleared = 0;
    ID *last_id = nullptr;
  };

  Stats stats;
};

void AssetClearHelper::operator()(PointerRNAVec &ids)
{
  for (PointerRNA &ptr : ids) {
    BLI_assert(RNA_struct_is_ID(ptr.type));

    ID *id = static_cast<ID *>(ptr.data);
    if (!id->asset_data) {
      continue;
    }

    if (!ED_asset_clear_id(id)) {
      continue;
    }

    if (set_fake_user_) {
      id_fake_user_set(id);
    }

    stats.tot_cleared++;
    stats.last_id = id;
  }
}

void AssetClearHelper::reportResults(const bContext *C, ReportList &reports) const
{
  if (!wasSuccessful()) {
    bool is_valid;
    /* Dedicated error message for when there is an active asset detected, but it's not an ID local
     * to this file. Helps users better understanding what's going on. */
    if (AssetHandle active_asset = CTX_wm_asset_handle(C, &is_valid);
        is_valid && !ED_asset_handle_get_local_id(&active_asset)) {
      BKE_report(&reports,
                 RPT_ERROR,
                 "No asset data-blocks from the current file selected (assets must be stored in "
                 "the current file to be able to edit or clear them)");
    }
    else {
      BKE_report(&reports, RPT_ERROR, "No asset data-blocks selected/focused");
    }
  }
  else if (stats.tot_cleared == 1) {
    /* If only one data-block: Give more useful message by printing asset name. */
    BKE_reportf(
        &reports, RPT_INFO, "Data-block '%s' is no asset anymore", stats.last_id->name + 2);
  }
  else {
    BKE_reportf(&reports, RPT_INFO, "%i data-blocks are no assets anymore", stats.tot_cleared);
  }
}

bool AssetClearHelper::wasSuccessful() const
{
  return stats.tot_cleared > 0;
}

static int asset_clear_exec(bContext *C, wmOperator *op)
{
  PointerRNAVec ids = asset_operation_get_ids_from_context(C);

  const bool set_fake_user = RNA_boolean_get(op->ptr, "set_fake_user");
  AssetClearHelper clear_helper(set_fake_user);
  clear_helper(ids);
  clear_helper.reportResults(C, *op->reports);

  if (!clear_helper.wasSuccessful()) {
    return OPERATOR_CANCELLED;
  }

  WM_main_add_notifier(NC_ID | NA_EDITED, nullptr);
  WM_main_add_notifier(NC_ASSET | NA_REMOVED, nullptr);

  return OPERATOR_FINISHED;
}

static bool asset_clear_poll(bContext *C)
{
  IDVecStats ctx_stats = asset_operation_get_id_vec_stats_from_context(C);

  if (!ctx_stats.has_asset) {
    const char *msg_single = "Data-block is not marked as asset";
    const char *msg_multiple = "No data-block selected that is marked as asset";
    CTX_wm_operator_poll_msg_set(C, ctx_stats.is_single ? msg_single : msg_multiple);
    return false;
  }
  if (!ctx_stats.has_supported_type) {
    CTX_wm_operator_poll_msg_set(C, asset_operation_unsupported_type_msg(ctx_stats.is_single));
    return false;
  }

  return true;
}

static char *asset_clear_get_description(struct bContext *UNUSED(C),
                                         struct wmOperatorType *UNUSED(op),
                                         struct PointerRNA *values)
{
  const bool set_fake_user = RNA_boolean_get(values, "set_fake_user");
  if (!set_fake_user) {
    return nullptr;
  }

  return BLI_strdup(
      "Delete all asset metadata, turning the selected asset data-blocks back into normal "
      "data-blocks, and set Fake User to ensure the data-blocks will still be saved");
}

static void ASSET_OT_clear(wmOperatorType *ot)
{
  ot->name = "Clear Asset";
  ot->description =
      "Delete all asset metadata and turn the selected asset data-blocks back into normal "
      "data-blocks";
  ot->get_description = asset_clear_get_description;
  ot->idname = "ASSET_OT_clear";

  ot->exec = asset_clear_exec;
  ot->poll = asset_clear_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(ot->srna,
                  "set_fake_user",
                  false,
                  "Set Fake User",
                  "Ensure the data-block is saved, even when it is no longer marked as asset");
}

/* -------------------------------------------------------------------- */

static bool asset_list_refresh_poll(bContext *C)
{
  const AssetLibraryReference *library = CTX_wm_asset_library_ref(C);
  if (!library) {
    return false;
  }

  return ED_assetlist_storage_has_list_for_library(library);
}

static int asset_list_refresh_exec(bContext *C, wmOperator *UNUSED(unused))
{
  const AssetLibraryReference *library = CTX_wm_asset_library_ref(C);
  ED_assetlist_clear(library, C);
  return OPERATOR_FINISHED;
}

static void ASSET_OT_list_refresh(struct wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Refresh Asset List";
  ot->description = "Trigger a reread of the assets";
  ot->idname = "ASSET_OT_list_refresh";

  /* api callbacks */
  ot->exec = asset_list_refresh_exec;
  ot->poll = asset_list_refresh_poll;
}

/* -------------------------------------------------------------------- */

static bool asset_catalog_operator_poll(bContext *C)
{
  const SpaceFile *sfile = CTX_wm_space_file(C);
  return sfile && ED_fileselect_active_asset_library_get(sfile);
}

static int asset_catalog_new_exec(bContext *C, wmOperator *op)
{
  SpaceFile *sfile = CTX_wm_space_file(C);
  struct AssetLibrary *asset_library = ED_fileselect_active_asset_library_get(sfile);
  char *parent_path = RNA_string_get_alloc(op->ptr, "parent_path", nullptr, 0, nullptr);

  blender::bke::AssetCatalog *new_catalog = ED_asset_catalog_add(
      asset_library, "Catalog", parent_path);

  if (sfile) {
    ED_fileselect_activate_asset_catalog(sfile, new_catalog->catalog_id);
  }

  MEM_freeN(parent_path);

  WM_event_add_notifier_ex(
      CTX_wm_manager(C), CTX_wm_window(C), NC_ASSET | ND_ASSET_CATALOGS, nullptr);

  return OPERATOR_FINISHED;
}

static void ASSET_OT_catalog_new(struct wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "New Asset Catalog";
  ot->description = "Create a new catalog to put assets in";
  ot->idname = "ASSET_OT_catalog_new";

  /* api callbacks */
  ot->exec = asset_catalog_new_exec;
  ot->poll = asset_catalog_operator_poll;

  RNA_def_string(ot->srna,
                 "parent_path",
                 nullptr,
                 0,
                 "Parent Path",
                 "Optional path defining the location to put the new catalog under");
}

static int asset_catalog_delete_exec(bContext *C, wmOperator *op)
{
  SpaceFile *sfile = CTX_wm_space_file(C);
  struct AssetLibrary *asset_library = ED_fileselect_active_asset_library_get(sfile);
  char *catalog_id_str = RNA_string_get_alloc(op->ptr, "catalog_id", nullptr, 0, nullptr);
  bke::CatalogID catalog_id;
  if (!BLI_uuid_parse_string(&catalog_id, catalog_id_str)) {
    return OPERATOR_CANCELLED;
  }

  ED_asset_catalog_remove(asset_library, catalog_id);

  MEM_freeN(catalog_id_str);

  WM_event_add_notifier_ex(
      CTX_wm_manager(C), CTX_wm_window(C), NC_ASSET | ND_ASSET_CATALOGS, nullptr);

  return OPERATOR_FINISHED;
}

static void ASSET_OT_catalog_delete(struct wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Delete Asset Catalog";
  ot->description =
      "Remove an asset catalog from the asset library (contained assets will not be affected and "
      "show up as unassigned)";
  ot->idname = "ASSET_OT_catalog_delete";

  /* api callbacks */
  ot->exec = asset_catalog_delete_exec;
  ot->poll = asset_catalog_operator_poll;

  RNA_def_string(ot->srna, "catalog_id", nullptr, 0, "Catalog ID", "ID of the catalog to delete");
}

static bke::AssetCatalogService *get_catalog_service(bContext *C)
{
  const SpaceFile *sfile = CTX_wm_space_file(C);
  if (!sfile) {
    return nullptr;
  }

  AssetLibrary *asset_lib = ED_fileselect_active_asset_library_get(sfile);
  return BKE_asset_library_get_catalog_service(asset_lib);
}

static int asset_catalog_undo_exec(bContext *C, wmOperator * /*op*/)
{
  bke::AssetCatalogService *catalog_service = get_catalog_service(C);
  if (!catalog_service) {
    return OPERATOR_CANCELLED;
  }

  catalog_service->undo();
  WM_event_add_notifier(C, NC_SPACE | ND_SPACE_ASSET_PARAMS, nullptr);
  return OPERATOR_FINISHED;
}

static bool asset_catalog_undo_poll(bContext *C)
{
  const bke::AssetCatalogService *catalog_service = get_catalog_service(C);
  return catalog_service && catalog_service->is_undo_possbile();
}

static void ASSET_OT_catalog_undo(struct wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Undo Catalog Edits";
  ot->description = "Undo the last edit to the asset catalogs";
  ot->idname = "ASSET_OT_catalog_undo";

  /* api callbacks */
  ot->exec = asset_catalog_undo_exec;
  ot->poll = asset_catalog_undo_poll;
}

static int asset_catalog_redo_exec(bContext *C, wmOperator * /*op*/)
{
  bke::AssetCatalogService *catalog_service = get_catalog_service(C);
  if (!catalog_service) {
    return OPERATOR_CANCELLED;
  }

  catalog_service->redo();
  WM_event_add_notifier(C, NC_SPACE | ND_SPACE_ASSET_PARAMS, nullptr);
  return OPERATOR_FINISHED;
}

static bool asset_catalog_redo_poll(bContext *C)
{
  const bke::AssetCatalogService *catalog_service = get_catalog_service(C);
  return catalog_service && catalog_service->is_redo_possbile();
}

static void ASSET_OT_catalog_redo(struct wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Redo Catalog Edits";
  ot->description = "Redo the last undone edit to the asset catalogs";
  ot->idname = "ASSET_OT_catalog_redo";

  /* api callbacks */
  ot->exec = asset_catalog_redo_exec;
  ot->poll = asset_catalog_redo_poll;
}

static int asset_catalog_undo_push_exec(bContext *C, wmOperator * /*op*/)
{
  bke::AssetCatalogService *catalog_service = get_catalog_service(C);
  if (!catalog_service) {
    return OPERATOR_CANCELLED;
  }

  catalog_service->undo_push();
  return OPERATOR_FINISHED;
}

static bool asset_catalog_undo_push_poll(bContext *C)
{
  return get_catalog_service(C) != nullptr;
}

static void ASSET_OT_catalog_undo_push(struct wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Store undo snapshot for asset catalog edits";
  ot->description = "Store the current state of the asset catalogs in the undo buffer";
  ot->idname = "ASSET_OT_catalog_undo_push";

  /* api callbacks */
  ot->exec = asset_catalog_undo_push_exec;
  ot->poll = asset_catalog_undo_push_poll;

  /* Generally artists don't need to find & use this operator, it's meant for scripts only. */
  ot->flag = OPTYPE_INTERNAL;
}

/* -------------------------------------------------------------------- */

static bool asset_catalogs_save_poll(bContext *C)
{
  if (!asset_catalog_operator_poll(C)) {
    return false;
  }

  const Main *bmain = CTX_data_main(C);
  if (!bmain->name[0]) {
    CTX_wm_operator_poll_msg_set(C, "Cannot save asset catalogs before the Blender file is saved");
    return false;
  }

  if (!BKE_asset_library_has_any_unsaved_catalogs()) {
    CTX_wm_operator_poll_msg_set(C, "No changes to be saved");
    return false;
  }

  return true;
}

static int asset_catalogs_save_exec(bContext *C, wmOperator * /*op*/)
{
  const SpaceFile *sfile = CTX_wm_space_file(C);
  ::AssetLibrary *asset_library = ED_fileselect_active_asset_library_get(sfile);

  ED_asset_catalogs_save_from_main_path(asset_library, CTX_data_main(C));

  WM_event_add_notifier_ex(
      CTX_wm_manager(C), CTX_wm_window(C), NC_ASSET | ND_ASSET_CATALOGS, nullptr);

  return OPERATOR_FINISHED;
}

static void ASSET_OT_catalogs_save(struct wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Save Asset Catalogs";
  ot->description =
      "Make any edits to any catalogs permanent by writing the current set up to the asset "
      "library";
  ot->idname = "ASSET_OT_catalogs_save";

  /* api callbacks */
  ot->exec = asset_catalogs_save_exec;
  ot->poll = asset_catalogs_save_poll;
}

/* -------------------------------------------------------------------- */

void ED_operatortypes_asset(void)
{
  WM_operatortype_append(ASSET_OT_mark);
  WM_operatortype_append(ASSET_OT_clear);

  WM_operatortype_append(ASSET_OT_catalog_new);
  WM_operatortype_append(ASSET_OT_catalog_delete);
  WM_operatortype_append(ASSET_OT_catalogs_save);
  WM_operatortype_append(ASSET_OT_catalog_undo);
  WM_operatortype_append(ASSET_OT_catalog_redo);
  WM_operatortype_append(ASSET_OT_catalog_undo_push);

  WM_operatortype_append(ASSET_OT_list_refresh);
}
