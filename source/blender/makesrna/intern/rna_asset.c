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
 * \ingroup RNA
 */

#include <stdlib.h>

#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "DNA_asset_types.h"
#include "DNA_defs.h"
#include "DNA_space_types.h"

#include "rna_internal.h"

#ifdef RNA_RUNTIME

#  include "BKE_asset.h"
#  include "BKE_idprop.h"

#  include "BLI_listbase.h"

#  include "ED_asset.h"

#  include "RNA_access.h"

static AssetTag *rna_AssetMetaData_tag_new(AssetMetaData *asset_data,
                                           ReportList *reports,
                                           const char *name,
                                           bool skip_if_exists)
{
  AssetTag *tag = NULL;

  if (skip_if_exists) {
    struct AssetTagEnsureResult result = BKE_asset_metadata_tag_ensure(asset_data, name);

    if (!result.is_new) {
      BKE_reportf(
          reports, RPT_WARNING, "Tag '%s' already present for given asset", result.tag->name);
      /* Report, but still return valid item. */
    }
    tag = result.tag;
  }
  else {
    tag = BKE_asset_metadata_tag_add(asset_data, name);
  }

  return tag;
}

static void rna_AssetMetaData_tag_remove(AssetMetaData *asset_data,
                                         ReportList *reports,
                                         PointerRNA *tag_ptr)
{
  AssetTag *tag = tag_ptr->data;
  if (BLI_findindex(&asset_data->tags, tag) == -1) {
    BKE_reportf(reports, RPT_ERROR, "Tag '%s' not found in given asset", tag->name);
    return;
  }

  BKE_asset_metadata_tag_remove(asset_data, tag);
  RNA_POINTER_INVALIDATE(tag_ptr);
}

static IDProperty **rna_AssetMetaData_idprops(PointerRNA *ptr)
{
  AssetMetaData *asset_data = ptr->data;
  return &asset_data->properties;
}

static void rna_AssetMetaData_description_get(PointerRNA *ptr, char *value)
{
  AssetMetaData *asset_data = ptr->data;

  if (asset_data->description) {
    strcpy(value, asset_data->description);
  }
  else {
    value[0] = '\0';
  }
}

static int rna_AssetMetaData_description_length(PointerRNA *ptr)
{
  AssetMetaData *asset_data = ptr->data;
  return asset_data->description ? strlen(asset_data->description) : 0;
}

static void rna_AssetMetaData_description_set(PointerRNA *ptr, const char *value)
{
  AssetMetaData *asset_data = ptr->data;

  if (asset_data->description) {
    MEM_freeN(asset_data->description);
  }

  if (value[0]) {
    asset_data->description = BLI_strdup(value);
  }
  else {
    asset_data->description = NULL;
  }
}

static void rna_AssetMetaData_active_tag_range(
    PointerRNA *ptr, int *min, int *max, int *softmin, int *softmax)
{
  const AssetMetaData *asset_data = ptr->data;
  *min = *softmin = 0;
  *max = *softmax = MAX2(asset_data->tot_tags - 1, 0);
}

static PointerRNA rna_AssetHandle_file_data_get(PointerRNA *ptr)
{
  AssetHandle *asset_handle = ptr->data;
  return rna_pointer_inherit_refine(ptr, &RNA_FileSelectEntry, asset_handle->file_data);
}

static void rna_AssetHandle_get_full_library_path(
    // AssetHandle *asset,
    bContext *C,
    FileDirEntry *asset_file,
    AssetLibraryReference *library,
    char r_result[/*FILE_MAX_LIBEXTRA*/])
{
  AssetHandle asset = {.file_data = asset_file};
  ED_asset_handle_get_full_library_path(C, library, &asset, r_result);
}

static PointerRNA rna_AssetHandle_local_id_get(PointerRNA *ptr)
{
  const AssetHandle *asset = ptr->data;
  ID *id = ED_assetlist_asset_local_id_get(asset);
  return rna_pointer_inherit_refine(ptr, &RNA_ID, id);
}

static void rna_AssetHandle_file_data_set(PointerRNA *ptr,
                                          PointerRNA value,
                                          struct ReportList *UNUSED(reports))
{
  AssetHandle *asset_handle = ptr->data;
  asset_handle->file_data = value.data;
}

int rna_asset_library_reference_get(const AssetLibraryReference *library)
{
  return ED_asset_library_reference_to_enum_value(library);
}

void rna_asset_library_reference_set(AssetLibraryReference *library, int value)
{
  *library = ED_asset_library_reference_from_enum_value(value);
}

const EnumPropertyItem *rna_asset_library_reference_itemf(bContext *UNUSED(C),
                                                          PointerRNA *UNUSED(ptr),
                                                          PropertyRNA *UNUSED(prop),
                                                          bool *r_free)
{
  const EnumPropertyItem predefined_items[] = {
      /* For the future. */
      // {ASSET_REPO_BUNDLED, "BUNDLED", 0, "Bundled", "Show the default user assets"},
      {ASSET_LIBRARY_LOCAL,
       "LOCAL",
       ICON_BLENDER,
       "Current File",
       "Show the assets currently available in this Blender session"},
      {0, NULL, 0, NULL, NULL},
  };

  EnumPropertyItem *item = NULL;
  int totitem = 0;

  /* Add separator if needed. */
  if (!BLI_listbase_is_empty(&U.asset_libraries)) {
    const EnumPropertyItem sepr = {0, "", 0, "Custom", NULL};
    RNA_enum_item_add(&item, &totitem, &sepr);
  }

  int i = 0;
  for (bUserAssetLibrary *user_library = U.asset_libraries.first; user_library;
       user_library = user_library->next, i++) {
    /* Note that the path itself isn't checked for validity here. If an invalid library path is
     * used, the Asset Browser can give a nice hint on what's wrong. */
    const bool is_valid = (user_library->name[0] && user_library->path[0]);
    if (!is_valid) {
      continue;
    }

    /* Use library path as description, it's a nice hint for users. */
    EnumPropertyItem tmp = {ASSET_LIBRARY_CUSTOM + i,
                            user_library->name,
                            ICON_NONE,
                            user_library->name,
                            user_library->path};
    RNA_enum_item_add(&item, &totitem, &tmp);
  }

  if (totitem) {
    const EnumPropertyItem sepr = {0, "", 0, "Built-in", NULL};
    RNA_enum_item_add(&item, &totitem, &sepr);
  }

  /* Add predefined items. */
  RNA_enum_items_add(&item, &totitem, predefined_items);

  RNA_enum_item_end(&item, &totitem);
  *r_free = true;
  return item;
}

#else

static void rna_def_asset_tag(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "AssetTag", NULL);
  RNA_def_struct_ui_text(srna, "Asset Tag", "User defined tag (name token)");

  prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
  RNA_def_property_string_maxlength(prop, MAX_NAME);
  RNA_def_property_ui_text(prop, "Name", "The identifier that makes up this tag");
  RNA_def_struct_name_property(srna, prop);
}

static void rna_def_asset_tags_api(BlenderRNA *brna, PropertyRNA *cprop)
{
  StructRNA *srna;

  FunctionRNA *func;
  PropertyRNA *parm;

  RNA_def_property_srna(cprop, "AssetTags");
  srna = RNA_def_struct(brna, "AssetTags", NULL);
  RNA_def_struct_sdna(srna, "AssetMetaData");
  RNA_def_struct_ui_text(srna, "Asset Tags", "Collection of custom asset tags");

  /* Tag collection */
  func = RNA_def_function(srna, "new", "rna_AssetMetaData_tag_new");
  RNA_def_function_ui_description(func, "Add a new tag to this asset");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  parm = RNA_def_string(func, "name", NULL, MAX_NAME, "Name", "");
  RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
  parm = RNA_def_boolean(func,
                         "skip_if_exists",
                         false,
                         "Skip if Exists",
                         "Do not add a new tag if one of the same type already exists");
  /* return type */
  parm = RNA_def_pointer(func, "tag", "AssetTag", "", "New tag");
  RNA_def_function_return(func, parm);

  func = RNA_def_function(srna, "remove", "rna_AssetMetaData_tag_remove");
  RNA_def_function_ui_description(func, "Remove an existing tag from this asset");
  RNA_def_function_flag(func, FUNC_USE_REPORTS);
  /* tag to remove */
  parm = RNA_def_pointer(func, "tag", "AssetTag", "", "Removed tag");
  RNA_def_parameter_flags(parm, PROP_NEVER_NULL, PARM_REQUIRED | PARM_RNAPTR);
  RNA_def_parameter_clear_flags(parm, PROP_THICK_WRAP, 0);
}

static void rna_def_asset_data(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "AssetMetaData", NULL);
  RNA_def_struct_ui_text(srna, "Asset Data", "Additional data stored for an asset data-block");
  //  RNA_def_struct_ui_icon(srna, ICON_ASSET); /* TODO: Icon doesn't exist!. */
  /* The struct has custom properties, but no pointer properties to other IDs! */
  RNA_def_struct_idprops_func(srna, "rna_AssetMetaData_idprops");
  RNA_def_struct_flag(srna, STRUCT_NO_DATABLOCK_IDPROPERTIES); /* Mandatory! */

  prop = RNA_def_property(srna, "description", PROP_STRING, PROP_NONE);
  RNA_def_property_string_funcs(prop,
                                "rna_AssetMetaData_description_get",
                                "rna_AssetMetaData_description_length",
                                "rna_AssetMetaData_description_set");
  RNA_def_property_ui_text(
      prop, "Description", "A description of the asset to be displayed for the user");

  prop = RNA_def_property(srna, "tags", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_struct_type(prop, "AssetTag");
  RNA_def_property_flag(prop, PROP_EDITABLE);
  RNA_def_property_ui_text(prop,
                           "Tags",
                           "Custom tags (name tokens) for the asset, used for filtering and "
                           "general asset management");
  rna_def_asset_tags_api(brna, prop);

  prop = RNA_def_property(srna, "active_tag", PROP_INT, PROP_NONE);
  RNA_def_property_int_funcs(prop, NULL, NULL, "rna_AssetMetaData_active_tag_range");
  RNA_def_property_ui_text(prop, "Active Tag", "Index of the tag set for editing");
}

static void rna_def_asset_handle_api(StructRNA *srna)
{
  FunctionRNA *func;
  PropertyRNA *parm;

  func = RNA_def_function(srna, "get_full_library_path", "rna_AssetHandle_get_full_library_path");
  RNA_def_function_flag(func, FUNC_USE_CONTEXT);
  /* TODO temporarily static function, for until .py can receive the asset handle from context
   * properly. `asset_file_handle` should go away too then. */
  RNA_def_function_flag(func, FUNC_NO_SELF);
  parm = RNA_def_pointer(func, "asset_file_handle", "FileSelectEntry", "", "");
  RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
  parm = RNA_def_pointer(func,
                         "asset_library",
                         "AssetLibraryReference",
                         "",
                         "The asset library containing the given asset, only valid if the asset "
                         "library is external (i.e. not the \"Current File\" one");
  RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
  parm = RNA_def_string(func, "result", NULL, FILE_MAX_LIBEXTRA, "result", "");
  RNA_def_parameter_flags(parm, PROP_THICK_WRAP, 0);
  RNA_def_function_output(func, parm);
}

static void rna_def_asset_handle(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "AssetHandle", "PropertyGroup");
  RNA_def_struct_ui_text(srna, "Asset Handle", "Reference to some asset");

  /* TODO why is this editable? There probably shouldn't be a setter. */
  prop = RNA_def_property(srna, "file_data", PROP_POINTER, PROP_NONE);
  RNA_def_property_flag(prop, PROP_EDITABLE);
  RNA_def_property_struct_type(prop, "FileSelectEntry");
  RNA_def_property_pointer_funcs(
      prop, "rna_AssetHandle_file_data_get", "rna_AssetHandle_file_data_set", NULL, NULL);
  RNA_def_property_ui_text(prop, "File Entry", "File data used to refer to the asset");

  prop = RNA_def_property(srna, "local_id", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "ID");
  RNA_def_property_pointer_funcs(prop, "rna_AssetHandle_local_id_get", NULL, NULL, NULL);
  RNA_def_property_ui_text(prop,
                           "",
                           "The local data-block this asset represents; only valid if that is a "
                           "data-block in this file");
  RNA_def_property_flag(prop, PROP_HIDDEN);

  rna_def_asset_handle_api(srna);
}

static void rna_def_asset_library_reference(BlenderRNA *brna)
{
  StructRNA *srna = RNA_def_struct(brna, "AssetLibraryReference", NULL);
  RNA_def_struct_ui_text(
      srna, "Asset Library Reference", "Identifier to refere to the asset library");
}

/**
 * \note the UI text and updating has to be set by the caller.
 */
PropertyRNA *rna_def_asset_library_reference_common(struct StructRNA *srna,
                                                    const char *get,
                                                    const char *set)
{
  PropertyRNA *prop = RNA_def_property(srna, "active_asset_library", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, DummyRNA_NULL_items);
  RNA_def_property_enum_funcs(prop, get, set, "rna_asset_library_reference_itemf");

  return prop;
}

void RNA_def_asset(BlenderRNA *brna)
{
  RNA_define_animate_sdna(false);

  rna_def_asset_tag(brna);
  rna_def_asset_data(brna);
  rna_def_asset_library_reference(brna);
  rna_def_asset_handle(brna);

  RNA_define_animate_sdna(true);
}

#endif
