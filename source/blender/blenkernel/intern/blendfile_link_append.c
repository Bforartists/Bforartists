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
 * \ingroup bke
 *
 * High level `.blend` file link/append code,
 * including linking/appending several IDs from different libraries, handling instantiations of
 * collections/objects/object-data in current scene.
 */

#include <stdlib.h>
#include <string.h>

#include "CLG_log.h"

#include "MEM_guardedalloc.h"

#include "DNA_ID.h"
#include "DNA_collection_types.h"
#include "DNA_key_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"

#include "BLI_bitmap.h"
#include "BLI_blenlib.h"
#include "BLI_ghash.h"
#include "BLI_linklist.h"
#include "BLI_math.h"
#include "BLI_memarena.h"
#include "BLI_utildefines.h"

#include "BLT_translation.h"

#include "BKE_idtype.h"
#include "BKE_key.h"
#include "BKE_layer.h"
#include "BKE_lib_id.h"
#include "BKE_lib_override.h"
#include "BKE_lib_query.h"
#include "BKE_lib_remap.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_object.h"
#include "BKE_report.h"
#include "BKE_rigidbody.h"
#include "BKE_scene.h"

#include "BKE_blendfile_link_append.h"

#include "BLO_readfile.h"
#include "BLO_writefile.h"

static CLG_LogRef LOG = {"bke.blendfile_link_append"};

/* -------------------------------------------------------------------- */
/** \name Link/append context implementation and public management API.
 * \{ */

typedef struct BlendfileLinkAppendContextItem {
  /** Name of the ID (without the heading two-chars IDcode). */
  char *name;
  /** All libs (from BlendfileLinkAppendContext.libraries) to try to load this ID from. */
  BLI_bitmap *libraries;
  /** ID type. */
  short idcode;

  /** Type of action to perform on this item, and general status tag information.
   *  NOTE: Mostly used by append post-linking processing. */
  char action;
  char tag;

  /** Newly linked ID (NULL until it has been successfully linked). */
  ID *new_id;
  /** Library ID from which the #new_id has been linked (NULL until it has been successfully
   * linked). */
  Library *source_library;
  /** Opaque user data pointer. */
  void *userdata;
} BlendfileLinkAppendContextItem;

/* A blendfile library entry in the `libraries` list of #BlendfileLinkAppendContext. */
typedef struct BlendfileLinkAppendContextLibrary {
  char *path;               /* Absolute .blend file path. */
  BlendHandle *blo_handle;  /* Blend file handle, if any. */
  bool blo_handle_is_owned; /* Whether the blend file handle is owned, or borrowed. */
  /* The blendfile report associated with the `blo_handle`, if owned. */
  BlendFileReadReport bf_reports;
} BlendfileLinkAppendContextLibrary;

typedef struct BlendfileLinkAppendContext {
  /** List of library paths to search IDs in. */
  LinkNodePair libraries;
  /** List of all ID to try to link from #libraries. */
  LinkNodePair items;
  int num_libraries;
  int num_items;
  /** Linking/appending parameters. Including `bmain`, `scene`, `viewlayer` and `view3d`. */
  LibraryLink_Params *params;

  /** Allows to easily find an existing items from an ID pointer. */
  GHash *new_id_to_item;

  /** Runtime info used by append code to manage re-use of already appended matching IDs. */
  GHash *library_weak_reference_mapping;

  /** Embedded blendfile and its size, if needed. */
  const void *blendfile_mem;
  size_t blendfile_memsize;

  /** Internal 'private' data */
  MemArena *memarena;
} BlendfileLinkAppendContext;

typedef struct BlendfileLinkAppendContextCallBack {
  BlendfileLinkAppendContext *lapp_context;
  BlendfileLinkAppendContextItem *item;
  ReportList *reports;

} BlendfileLinkAppendContextCallBack;

/* Actions to apply to an item (i.e. linked ID). */
enum {
  LINK_APPEND_ACT_UNSET = 0,
  LINK_APPEND_ACT_KEEP_LINKED,
  LINK_APPEND_ACT_REUSE_LOCAL,
  LINK_APPEND_ACT_MAKE_LOCAL,
  LINK_APPEND_ACT_COPY_LOCAL,
};

/* Various status info about an item (i.e. linked ID). */
enum {
  /* An indirectly linked ID. */
  LINK_APPEND_TAG_INDIRECT = 1 << 0,
};

static BlendHandle *link_append_context_library_blohandle_ensure(
    BlendfileLinkAppendContext *lapp_context,
    BlendfileLinkAppendContextLibrary *lib_context,
    ReportList *reports)
{
  if (reports != NULL) {
    lib_context->bf_reports.reports = reports;
  }

  char *libname = lib_context->path;
  BlendHandle *blo_handle = lib_context->blo_handle;
  if (blo_handle == NULL) {
    if (STREQ(libname, BLO_EMBEDDED_STARTUP_BLEND)) {
      blo_handle = BLO_blendhandle_from_memory(lapp_context->blendfile_mem,
                                               (int)lapp_context->blendfile_memsize,
                                               &lib_context->bf_reports);
    }
    else {
      blo_handle = BLO_blendhandle_from_file(libname, &lib_context->bf_reports);
    }
    lib_context->blo_handle = blo_handle;
    lib_context->blo_handle_is_owned = true;
  }

  return blo_handle;
}

static void link_append_context_library_blohandle_release(
    BlendfileLinkAppendContext *UNUSED(lapp_context),
    BlendfileLinkAppendContextLibrary *lib_context)
{
  if (lib_context->blo_handle_is_owned && lib_context->blo_handle != NULL) {
    BLO_blendhandle_close(lib_context->blo_handle);
    lib_context->blo_handle = NULL;
  }
}

/** Allocate and initialize a new context to link/append datablocks.
 *
 *  \param flag: A combination of #eFileSel_Params_Flag from DNA_space_types.h & #eBLOLibLinkFlags
 * from BLO_readfile.h
 */
BlendfileLinkAppendContext *BKE_blendfile_link_append_context_new(LibraryLink_Params *params)
{
  MemArena *ma = BLI_memarena_new(BLI_MEMARENA_STD_BUFSIZE, __func__);
  BlendfileLinkAppendContext *lapp_context = BLI_memarena_calloc(ma, sizeof(*lapp_context));

  lapp_context->params = params;
  lapp_context->memarena = ma;

  return lapp_context;
}

/** Free a link/append context. */
void BKE_blendfile_link_append_context_free(BlendfileLinkAppendContext *lapp_context)
{
  if (lapp_context->new_id_to_item != NULL) {
    BLI_ghash_free(lapp_context->new_id_to_item, NULL, NULL);
  }

  for (LinkNode *liblink = lapp_context->libraries.list; liblink != NULL;
       liblink = liblink->next) {
    BlendfileLinkAppendContextLibrary *lib_context = liblink->link;
    link_append_context_library_blohandle_release(lapp_context, lib_context);
  }

  BLI_assert(lapp_context->library_weak_reference_mapping == NULL);

  BLI_memarena_free(lapp_context->memarena);
}

/** Set or clear flags in given \a lapp_context.
 *
 * \param do_set: Set the given \a flag if true, clear it otherwise.
 */
void BKE_blendfile_link_append_context_flag_set(BlendfileLinkAppendContext *lapp_context,
                                                const int flag,
                                                const bool do_set)
{
  if (do_set) {
    lapp_context->params->flag |= flag;
  }
  else {
    lapp_context->params->flag &= ~flag;
  }
}

/** Store reference to a Blender's embedded memfile into the context.
 *
 * \note This is required since embedded startup blender file is handled in `ED` module, which
 * cannot be linked in BKE code.
 */
void BKE_blendfile_link_append_context_embedded_blendfile_set(
    BlendfileLinkAppendContext *lapp_context, const void *blendfile_mem, int blendfile_memsize)
{
  BLI_assert_msg(lapp_context->blendfile_mem == NULL,
                 "Please explicitly clear reference to an embedded blender memfile before "
                 "setting a new one");
  lapp_context->blendfile_mem = blendfile_mem;
  lapp_context->blendfile_memsize = (size_t)blendfile_memsize;
}

/** Clear reference to Blender's embedded startup file into the context. */
void BKE_blendfile_link_append_context_embedded_blendfile_clear(
    BlendfileLinkAppendContext *lapp_context)
{
  lapp_context->blendfile_mem = NULL;
  lapp_context->blendfile_memsize = 0;
}

/** Add a new source library to search for items to be linked to the given link/append context.
 *
 * \param libname: the absolute path to the library blend file.
 * \param blo_handle: the blend file handle of the library, NULL is not available. Note that this
 *                    is only borrowed for linking purpose, no releasing or other management will
 *                    be performed by #BKE_blendfile_link_append code on it.
 *
 * \note *Never* call BKE_blendfile_link_append_context_library_add() after having added some
 * items. */
void BKE_blendfile_link_append_context_library_add(BlendfileLinkAppendContext *lapp_context,
                                                   const char *libname,
                                                   BlendHandle *blo_handle)
{
  BLI_assert(lapp_context->items.list == NULL);

  BlendfileLinkAppendContextLibrary *lib_context = BLI_memarena_calloc(lapp_context->memarena,
                                                                       sizeof(*lib_context));

  size_t len = strlen(libname) + 1;
  char *libpath = BLI_memarena_alloc(lapp_context->memarena, len);
  BLI_strncpy(libpath, libname, len);

  lib_context->path = libpath;
  lib_context->blo_handle = blo_handle;
  lib_context->blo_handle_is_owned = (blo_handle == NULL);

  BLI_linklist_append_arena(&lapp_context->libraries, lib_context, lapp_context->memarena);
  lapp_context->num_libraries++;
}

/** Add a new item (datablock name and idcode) to be searched and linked/appended from libraries
 * associated to the given context.
 *
 * \param userdata: an opaque user-data pointer stored in generated link/append item. */
/* TODO: Add a more friendly version of this that combines it with the call to
 * #BKE_blendfile_link_append_context_item_library_index_enable to enable the added item for all
 * added library sources. */
BlendfileLinkAppendContextItem *BKE_blendfile_link_append_context_item_add(
    BlendfileLinkAppendContext *lapp_context,
    const char *idname,
    const short idcode,
    void *userdata)
{
  BlendfileLinkAppendContextItem *item = BLI_memarena_calloc(lapp_context->memarena,
                                                             sizeof(*item));
  size_t len = strlen(idname) + 1;

  item->name = BLI_memarena_alloc(lapp_context->memarena, len);
  BLI_strncpy(item->name, idname, len);
  item->idcode = idcode;
  item->libraries = BLI_BITMAP_NEW_MEMARENA(lapp_context->memarena, lapp_context->num_libraries);

  item->new_id = NULL;
  item->action = LINK_APPEND_ACT_UNSET;
  item->userdata = userdata;

  BLI_linklist_append_arena(&lapp_context->items, item, lapp_context->memarena);
  lapp_context->num_items++;

  return item;
}

/** Search for all ID matching given `id_types_filter` in given `library_index`, and add them to
 * the list of items to process.
 *
 * \note #BKE_blendfile_link_append_context_library_add should never be called on the same
 *`lapp_context` after this function.
 *
 * \param id_types_filter: A set of `FILTER_ID` bitflags, the types of IDs to add to the items
 *                         list.
 * \param library_index: The index of the library to look into, in given `lapp_context`.
 *
 * \return The number of items found and added to the list, or `BLENDFILE_LINK_APPEND_INVALID` if
 *         it could not open the .blend file.
 */
int BKE_blendfile_link_append_context_item_idtypes_from_library_add(
    BlendfileLinkAppendContext *lapp_context,
    ReportList *reports,
    const uint64_t id_types_filter,
    const int library_index)
{
  int id_num = 0;
  int id_code_iter = 0;
  short id_code;

  LinkNode *lib_context_link = BLI_linklist_find(lapp_context->libraries.list, library_index);
  BlendfileLinkAppendContextLibrary *lib_context = lib_context_link->link;
  BlendHandle *blo_handle = link_append_context_library_blohandle_ensure(
      lapp_context, lib_context, reports);

  if (blo_handle == NULL) {
    return BLENDFILE_LINK_APPEND_INVALID;
  }

  const bool use_assets_only = (lapp_context->params->flag & FILE_ASSETS_ONLY) != 0;

  while ((id_code = BKE_idtype_idcode_iter_step(&id_code_iter))) {
    if (!BKE_idtype_idcode_is_linkable(id_code) ||
        (id_types_filter != 0 &&
         (BKE_idtype_idcode_to_idfilter(id_code) & id_types_filter) == 0)) {
      continue;
    }

    int id_names_num;
    LinkNode *id_names_list = BLO_blendhandle_get_datablock_names(
        blo_handle, id_code, use_assets_only, &id_names_num);

    for (LinkNode *link_next = NULL; id_names_list != NULL; id_names_list = link_next) {
      link_next = id_names_list->next;

      char *id_name = id_names_list->link;
      BlendfileLinkAppendContextItem *item = BKE_blendfile_link_append_context_item_add(
          lapp_context, id_name, id_code, NULL);
      BKE_blendfile_link_append_context_item_library_index_enable(
          lapp_context, item, library_index);

      MEM_freeN(id_name);
      MEM_freeN(id_names_list);
    }

    id_num += id_names_num;
  }

  return id_num;
}

/** Enable search of the given \a item into the library stored at given index in the link/append
 * context. */
void BKE_blendfile_link_append_context_item_library_index_enable(
    BlendfileLinkAppendContext *UNUSED(lapp_context),
    BlendfileLinkAppendContextItem *item,
    const int library_index)
{
  BLI_BITMAP_ENABLE(item->libraries, library_index);
}

/** Check if given link/append context is empty (has no items to process) or not. */
bool BKE_blendfile_link_append_context_is_empty(struct BlendfileLinkAppendContext *lapp_context)
{
  return lapp_context->num_items == 0;
}

void *BKE_blendfile_link_append_context_item_userdata_get(
    BlendfileLinkAppendContext *UNUSED(lapp_context), BlendfileLinkAppendContextItem *item)
{
  return item->userdata;
}

ID *BKE_blendfile_link_append_context_item_newid_get(
    BlendfileLinkAppendContext *UNUSED(lapp_context), BlendfileLinkAppendContextItem *item)
{
  return item->new_id;
}

short BKE_blendfile_link_append_context_item_idcode_get(
    struct BlendfileLinkAppendContext *UNUSED(lapp_context),
    struct BlendfileLinkAppendContextItem *item)
{
  return item->idcode;
}

/** Iterate over all (or a subset) of the items listed in given #BlendfileLinkAppendContext, and
 * call the `callback_function` on them.
 *
 * \param flag: Control which type of items to process (see
 * #eBlendfileLinkAppendForeachItemFlag enum flags).
 * \param userdata: An opaque void pointer passed to the `callback_function`.
 */
void BKE_blendfile_link_append_context_item_foreach(
    struct BlendfileLinkAppendContext *lapp_context,
    BKE_BlendfileLinkAppendContexteItemFunction callback_function,
    const eBlendfileLinkAppendForeachItemFlag flag,
    void *userdata)
{
  for (LinkNode *itemlink = lapp_context->items.list; itemlink; itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;

    if ((flag & BKE_BLENDFILE_LINK_APPEND_FOREACH_ITEM_FLAG_DO_DIRECT) == 0 &&
        (item->tag & LINK_APPEND_TAG_INDIRECT) == 0) {
      continue;
    }
    if ((flag & BKE_BLENDFILE_LINK_APPEND_FOREACH_ITEM_FLAG_DO_INDIRECT) == 0 &&
        (item->tag & LINK_APPEND_TAG_INDIRECT) != 0) {
      continue;
    }

    if (!callback_function(lapp_context, item, userdata)) {
      break;
    }
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Library link/append helper functions.
 *
 * \{ */

/* Struct gathering all required data to handle instantiation of loose data-blocks. */
typedef struct LooseDataInstantiateContext {
  BlendfileLinkAppendContext *lapp_context;

  /* The collection in which to add loose collections/objects. */
  Collection *active_collection;
} LooseDataInstantiateContext;

static bool object_in_any_scene(Main *bmain, Object *ob)
{
  LISTBASE_FOREACH (Scene *, sce, &bmain->scenes) {
    if (BKE_scene_object_find(sce, ob)) {
      return true;
    }
  }

  return false;
}

static bool object_in_any_collection(Main *bmain, Object *ob)
{
  LISTBASE_FOREACH (Collection *, collection, &bmain->collections) {
    if (BKE_collection_has_object(collection, ob)) {
      return true;
    }
  }

  LISTBASE_FOREACH (Scene *, scene, &bmain->scenes) {
    if (scene->master_collection != NULL &&
        BKE_collection_has_object(scene->master_collection, ob)) {
      return true;
    }
  }

  return false;
}

static ID *loose_data_instantiate_process_check(LooseDataInstantiateContext *instantiate_context,
                                                BlendfileLinkAppendContextItem *item)
{
  BlendfileLinkAppendContext *lapp_context = instantiate_context->lapp_context;
  /* In linking case, we always want to handle instantiation. */
  if (lapp_context->params->flag & FILE_LINK) {
    return item->new_id;
  }

  /* We consider that if we either kept it linked, or re-used already local data, instantiation
   * status of those should not be modified. */
  if (!ELEM(item->action, LINK_APPEND_ACT_COPY_LOCAL, LINK_APPEND_ACT_MAKE_LOCAL)) {
    return NULL;
  }

  ID *id = item->new_id;
  if (id == NULL) {
    return NULL;
  }

  if (item->action == LINK_APPEND_ACT_COPY_LOCAL) {
    BLI_assert(ID_IS_LINKED(id));
    id = id->newid;
    if (id == NULL) {
      return NULL;
    }

    BLI_assert(!ID_IS_LINKED(id));
    return id;
  }

  BLI_assert(!ID_IS_LINKED(id));
  return id;
}

static void loose_data_instantiate_ensure_active_collection(
    LooseDataInstantiateContext *instantiate_context)
{

  BlendfileLinkAppendContext *lapp_context = instantiate_context->lapp_context;
  Main *bmain = instantiate_context->lapp_context->params->bmain;
  Scene *scene = instantiate_context->lapp_context->params->context.scene;
  ViewLayer *view_layer = instantiate_context->lapp_context->params->context.view_layer;

  /* Find or add collection as needed. */
  if (instantiate_context->active_collection == NULL) {
    if (lapp_context->params->flag & FILE_ACTIVE_COLLECTION) {
      LayerCollection *lc = BKE_layer_collection_get_active(view_layer);
      instantiate_context->active_collection = lc->collection;
    }
    else {
      if (lapp_context->params->flag & FILE_LINK) {
        instantiate_context->active_collection = BKE_collection_add(
            bmain, scene->master_collection, DATA_("Linked Data"));
      }
      else {
        instantiate_context->active_collection = BKE_collection_add(
            bmain, scene->master_collection, DATA_("Appended Data"));
      }
    }
  }
}

static void loose_data_instantiate_object_base_instance_init(Main *bmain,
                                                             Collection *collection,
                                                             Object *ob,
                                                             ViewLayer *view_layer,
                                                             const View3D *v3d,
                                                             const int flag,
                                                             bool set_active)
{
  /* Auto-select and appending. */
  if ((flag & FILE_AUTOSELECT) && ((flag & FILE_LINK) == 0)) {
    /* While in general the object should not be manipulated,
     * when the user requests the object to be selected, ensure it's visible and selectable. */
    ob->visibility_flag &= ~(OB_HIDE_VIEWPORT | OB_HIDE_SELECT);
  }

  BKE_collection_object_add(bmain, collection, ob);

  Base *base = BKE_view_layer_base_find(view_layer, ob);

  if (v3d != NULL) {
    base->local_view_bits |= v3d->local_view_uuid;
  }

  if (flag & FILE_AUTOSELECT) {
    /* All objects that use #FILE_AUTOSELECT must be selectable (unless linking data). */
    BLI_assert((base->flag & BASE_SELECTABLE) || (flag & FILE_LINK));
    if (base->flag & BASE_SELECTABLE) {
      base->flag |= BASE_SELECTED;
    }
  }

  if (set_active) {
    view_layer->basact = base;
  }

  BKE_scene_object_base_flag_sync_from_base(base);
}

/* Tag obdata that actually need to be instantiated (those referenced by an object do not, since
 * the object will be instantiated instead if needed. */
static void loose_data_instantiate_obdata_preprocess(
    LooseDataInstantiateContext *instantiate_context)
{
  BlendfileLinkAppendContext *lapp_context = instantiate_context->lapp_context;
  LinkNode *itemlink;

  /* First pass on obdata to enable their instantiation by default, then do a second pass on
   * objects to clear it for any obdata already in use. */
  for (itemlink = lapp_context->items.list; itemlink; itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;
    ID *id = loose_data_instantiate_process_check(instantiate_context, item);
    if (id == NULL) {
      continue;
    }
    const ID_Type idcode = GS(id->name);
    if (!OB_DATA_SUPPORT_ID(idcode)) {
      continue;
    }

    id->tag |= LIB_TAG_DOIT;
  }
  for (itemlink = lapp_context->items.list; itemlink; itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;
    ID *id = item->new_id;
    if (id == NULL || GS(id->name) != ID_OB) {
      continue;
    }

    Object *ob = (Object *)id;
    Object *new_ob = (Object *)id->newid;
    if (ob->data != NULL) {
      ((ID *)(ob->data))->tag &= ~LIB_TAG_DOIT;
    }
    if (new_ob != NULL && new_ob->data != NULL) {
      ((ID *)(new_ob->data))->tag &= ~LIB_TAG_DOIT;
    }
  }
}

/* Test whether some ancestor collection is also tagged for instantiation (return true) or not
 * (return false). */
static bool loose_data_instantiate_collection_parents_check_recursive(Collection *collection)
{
  for (CollectionParent *parent_collection = collection->parents.first; parent_collection != NULL;
       parent_collection = parent_collection->next) {
    if ((parent_collection->collection->id.tag & LIB_TAG_DOIT) != 0) {
      return true;
    }
    if (loose_data_instantiate_collection_parents_check_recursive(parent_collection->collection)) {
      return true;
    }
  }
  return false;
}

static void loose_data_instantiate_collection_process(
    LooseDataInstantiateContext *instantiate_context)
{
  BlendfileLinkAppendContext *lapp_context = instantiate_context->lapp_context;
  Main *bmain = lapp_context->params->bmain;
  Scene *scene = lapp_context->params->context.scene;
  ViewLayer *view_layer = lapp_context->params->context.view_layer;
  const View3D *v3d = lapp_context->params->context.v3d;

  const bool do_append = (lapp_context->params->flag & FILE_LINK) == 0;
  const bool do_instantiate_as_empty = (lapp_context->params->flag &
                                        BLO_LIBLINK_COLLECTION_INSTANCE) != 0;

  /* NOTE: For collections we only view_layer-instantiate duplicated collections that have
   * non-instantiated objects in them.
   * NOTE: Also avoid view-layer-instantiating of collections children of other instantiated
   * collections. This is why we need two passes here. */
  LinkNode *itemlink;
  for (itemlink = lapp_context->items.list; itemlink; itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;
    ID *id = loose_data_instantiate_process_check(instantiate_context, item);
    if (id == NULL || GS(id->name) != ID_GR) {
      continue;
    }

    /* Forced instantiation of indirectly appended collections is not wanted. Users can now
     * easily instantiate collections (and their objects) as needed by themselves. See T67032. */
    /* We need to check that objects in that collections are already instantiated in a scene.
     * Otherwise, it's better to add the collection to the scene's active collection, than to
     * instantiate its objects in active scene's collection directly. See T61141.
     *
     * NOTE: We only check object directly into that collection, not recursively into its
     * children.
     */
    Collection *collection = (Collection *)id;
    /* Always consider adding collections directly selected by the user. */
    bool do_add_collection = (item->tag & LINK_APPEND_TAG_INDIRECT) == 0;
    /* In linking case, do not enforce instantiating non-directly linked collections/objects.
     * This avoids cluttering the ViewLayers, user can instantiate themselves specific collections
     * or objects easily from the Outliner if needed. */
    if (!do_add_collection && do_append) {
      LISTBASE_FOREACH (CollectionObject *, coll_ob, &collection->gobject) {
        Object *ob = coll_ob->ob;
        if (!object_in_any_scene(bmain, ob)) {
          do_add_collection = true;
          break;
        }
      }
    }
    if (do_add_collection) {
      collection->id.tag |= LIB_TAG_DOIT;
    }
  }

  /* Second loop to actually instantiate collections tagged as such in first loop, unless some of
   * their ancestor is also instantiated in case this is not an empty-instantiation. */
  for (itemlink = lapp_context->items.list; itemlink; itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;
    ID *id = loose_data_instantiate_process_check(instantiate_context, item);
    if (id == NULL || GS(id->name) != ID_GR) {
      continue;
    }

    Collection *collection = (Collection *)id;
    bool do_add_collection = (id->tag & LIB_TAG_DOIT) != 0;

    /* When instantiated into view-layer, do not add collections if one of their parents is also
     * instantiated. In case of empty-instantiation though, instantiation of all user-selected
     * collections is the desired behavior. */
    if (!do_add_collection ||
        (!do_instantiate_as_empty &&
         loose_data_instantiate_collection_parents_check_recursive(collection))) {
      continue;
    }

    loose_data_instantiate_ensure_active_collection(instantiate_context);
    Collection *active_collection = instantiate_context->active_collection;

    /* In case user requested instantiation of collections as empties, do so for the one they
     * explicitly selected (originally directly linked IDs) only. */
    if (do_instantiate_as_empty && (item->tag & LINK_APPEND_TAG_INDIRECT) == 0) {
      /* BKE_object_add(...) messes with the selection. */
      Object *ob = BKE_object_add_only_object(bmain, OB_EMPTY, collection->id.name + 2);
      ob->type = OB_EMPTY;
      ob->empty_drawsize = U.collection_instance_empty_size;

      const bool set_selected = (lapp_context->params->flag & FILE_AUTOSELECT) != 0;
      /* TODO: why is it OK to make this active here but not in other situations?
       * See other callers of #object_base_instance_init */
      const bool set_active = set_selected;
      loose_data_instantiate_object_base_instance_init(
          bmain, active_collection, ob, view_layer, v3d, lapp_context->params->flag, set_active);

      /* Assign the collection. */
      ob->instance_collection = collection;
      id_us_plus(&collection->id);
      ob->transflag |= OB_DUPLICOLLECTION;
      copy_v3_v3(ob->loc, scene->cursor.location);
    }
    else {
      /* Add collection as child of active collection. */
      BKE_collection_child_add(bmain, active_collection, collection);

      if ((lapp_context->params->flag & FILE_AUTOSELECT) != 0) {
        LISTBASE_FOREACH (CollectionObject *, coll_ob, &collection->gobject) {
          Object *ob = coll_ob->ob;
          Base *base = BKE_view_layer_base_find(view_layer, ob);
          if (base) {
            base->flag |= BASE_SELECTED;
            BKE_scene_object_base_flag_sync_from_base(base);
          }
        }
      }
    }
  }
}

static void loose_data_instantiate_object_process(LooseDataInstantiateContext *instantiate_context)
{
  BlendfileLinkAppendContext *lapp_context = instantiate_context->lapp_context;
  Main *bmain = lapp_context->params->bmain;
  ViewLayer *view_layer = lapp_context->params->context.view_layer;
  const View3D *v3d = lapp_context->params->context.v3d;

  /* Do NOT make base active here! screws up GUI stuff,
   * if you want it do it at the editor level. */
  const bool object_set_active = false;

  /* NOTE: For objects we only view_layer-instantiate duplicated objects that are not yet used
   * anywhere. */
  LinkNode *itemlink;
  for (itemlink = lapp_context->items.list; itemlink; itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;
    ID *id = loose_data_instantiate_process_check(instantiate_context, item);
    if (id == NULL || GS(id->name) != ID_OB) {
      continue;
    }

    Object *ob = (Object *)id;

    if (object_in_any_collection(bmain, ob)) {
      continue;
    }

    loose_data_instantiate_ensure_active_collection(instantiate_context);
    Collection *active_collection = instantiate_context->active_collection;

    CLAMP_MIN(ob->id.us, 0);
    ob->mode = OB_MODE_OBJECT;

    loose_data_instantiate_object_base_instance_init(bmain,
                                                     active_collection,
                                                     ob,
                                                     view_layer,
                                                     v3d,
                                                     lapp_context->params->flag,
                                                     object_set_active);
  }
}

static void loose_data_instantiate_obdata_process(LooseDataInstantiateContext *instantiate_context)
{
  BlendfileLinkAppendContext *lapp_context = instantiate_context->lapp_context;
  Main *bmain = lapp_context->params->bmain;
  Scene *scene = lapp_context->params->context.scene;
  ViewLayer *view_layer = lapp_context->params->context.view_layer;
  const View3D *v3d = lapp_context->params->context.v3d;

  /* Do NOT make base active here! screws up GUI stuff,
   * if you want it do it at the editor level. */
  const bool object_set_active = false;

  LinkNode *itemlink;
  for (itemlink = lapp_context->items.list; itemlink; itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;
    ID *id = loose_data_instantiate_process_check(instantiate_context, item);
    if (id == NULL) {
      continue;
    }
    const ID_Type idcode = GS(id->name);
    if (!OB_DATA_SUPPORT_ID(idcode)) {
      continue;
    }
    if ((id->tag & LIB_TAG_DOIT) == 0) {
      continue;
    }

    loose_data_instantiate_ensure_active_collection(instantiate_context);
    Collection *active_collection = instantiate_context->active_collection;

    const int type = BKE_object_obdata_to_type(id);
    BLI_assert(type != -1);
    Object *ob = BKE_object_add_only_object(bmain, type, id->name + 2);
    ob->data = id;
    id_us_plus(id);
    BKE_object_materials_test(bmain, ob, ob->data);

    loose_data_instantiate_object_base_instance_init(bmain,
                                                     active_collection,
                                                     ob,
                                                     view_layer,
                                                     v3d,
                                                     lapp_context->params->flag,
                                                     object_set_active);

    copy_v3_v3(ob->loc, scene->cursor.location);

    id->tag &= ~LIB_TAG_DOIT;
  }
}

static void loose_data_instantiate_object_rigidbody_postprocess(
    LooseDataInstantiateContext *instantiate_context)
{
  BlendfileLinkAppendContext *lapp_context = instantiate_context->lapp_context;
  Main *bmain = lapp_context->params->bmain;

  LinkNode *itemlink;
  /* Add rigid body objects and constraints to current RB world(s). */
  for (itemlink = lapp_context->items.list; itemlink; itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;
    ID *id = loose_data_instantiate_process_check(instantiate_context, item);
    if (id == NULL || GS(id->name) != ID_OB) {
      continue;
    }
    BKE_rigidbody_ensure_local_object(bmain, (Object *)id);
  }
}

static void loose_data_instantiate(LooseDataInstantiateContext *instantiate_context)
{
  if (instantiate_context->lapp_context->params->context.scene == NULL) {
    /* In some cases, like the asset drag&drop e.g., the caller code manages instantiation itself.
     */
    return;
  }

  BlendfileLinkAppendContext *lapp_context = instantiate_context->lapp_context;
  const bool do_obdata = (lapp_context->params->flag & BLO_LIBLINK_OBDATA_INSTANCE) != 0;

  /* First pass on obdata to enable their instantiation by default, then do a second pass on
   * objects to clear it for any obdata already in use. */
  if (do_obdata) {
    loose_data_instantiate_obdata_preprocess(instantiate_context);
  }

  /* First do collections, then objects, then obdata. */
  loose_data_instantiate_collection_process(instantiate_context);
  loose_data_instantiate_object_process(instantiate_context);
  if (do_obdata) {
    loose_data_instantiate_obdata_process(instantiate_context);
  }

  loose_data_instantiate_object_rigidbody_postprocess(instantiate_context);
}

static void new_id_to_item_mapping_add(BlendfileLinkAppendContext *lapp_context,
                                       ID *id,
                                       BlendfileLinkAppendContextItem *item)
{
  BLI_ghash_insert(lapp_context->new_id_to_item, id, item);

  /* This ensures that if a liboverride reference is also linked/used by some other appended
   * data, it gets a local copy instead of being made directly local, so that the liboverride
   * references remain valid (i.e. linked data). */
  if (ID_IS_OVERRIDE_LIBRARY_REAL(id)) {
    id->override_library->reference->tag |= LIB_TAG_PRE_EXISTING;
  }
}

/* Generate a mapping between newly linked IDs and their items, and tag linked IDs used as
 * liboverride references as already existing. */
static void new_id_to_item_mapping_create(BlendfileLinkAppendContext *lapp_context)
{
  lapp_context->new_id_to_item = BLI_ghash_new(
      BLI_ghashutil_ptrhash, BLI_ghashutil_ptrcmp, __func__);
  for (LinkNode *itemlink = lapp_context->items.list; itemlink; itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;
    ID *id = item->new_id;
    if (id == NULL) {
      continue;
    }

    new_id_to_item_mapping_add(lapp_context, id, item);
  }
}

static int foreach_libblock_link_append_callback(LibraryIDLinkCallbackData *cb_data)
{
  /* NOTE: It is important to also skip liboverride references here, as those should never be made
   * local. */
  if (cb_data->cb_flag & (IDWALK_CB_EMBEDDED | IDWALK_CB_INTERNAL | IDWALK_CB_LOOPBACK |
                          IDWALK_CB_OVERRIDE_LIBRARY_REFERENCE)) {
    return IDWALK_RET_NOP;
  }

  BlendfileLinkAppendContextCallBack *data = cb_data->user_data;
  ID *id = *cb_data->id_pointer;

  if (id == NULL) {
    return IDWALK_RET_NOP;
  }

  if (!BKE_idtype_idcode_is_linkable(GS(id->name))) {
    /* While we do not want to add non-linkable ID (shape keys...) to the list of linked items,
     * unfortunately they can use fully linkable valid IDs too, like actions. Those need to be
     * processed, so we need to recursively deal with them here. */
    /* NOTE: Since we are by-passing checks in `BKE_library_foreach_ID_link` by manually calling it
     * recursively, we need to take care of potential recursion cases ourselves (e.g.animdata of
     * shape-key referencing the shape-key itself). */
    if (id != cb_data->id_self) {
      BKE_library_foreach_ID_link(
          cb_data->bmain, id, foreach_libblock_link_append_callback, data, IDWALK_NOP);
    }
    return IDWALK_RET_NOP;
  }

  /* In linking case, we always consider all linked IDs, even indirectly ones, for instantiation,
   * so we need to add them all to the items list.
   *
   * In appending case, when `do_recursive` is false, we only make local IDs from same
   * library(-ies) as the initially directly linked ones.
   *
   * NOTE: Since in append case, linked IDs are also fully skipped during instantiation step (see
   * #append_loose_data_instantiate_process_check), we can avoid adding them to the items list
   * completely. */
  const bool do_link = (data->lapp_context->params->flag & FILE_LINK) != 0;
  const bool do_recursive = (data->lapp_context->params->flag & BLO_LIBLINK_APPEND_RECURSIVE) !=
                                0 ||
                            do_link;
  if (!do_recursive && cb_data->id_owner->lib != id->lib) {
    return IDWALK_RET_NOP;
  }

  BlendfileLinkAppendContextItem *item = BLI_ghash_lookup(data->lapp_context->new_id_to_item, id);
  if (item == NULL) {
    item = BKE_blendfile_link_append_context_item_add(
        data->lapp_context, id->name, GS(id->name), NULL);
    item->new_id = id;
    item->source_library = id->lib;
    /* Since we did not have an item for that ID yet, we know user did not selected it explicitly,
     * it was rather linked indirectly. This info is important for instantiation of collections. */
    item->tag |= LINK_APPEND_TAG_INDIRECT;
    /* In linking case we already know what we want to do with those items. */
    if (do_link) {
      item->action = LINK_APPEND_ACT_KEEP_LINKED;
    }
    new_id_to_item_mapping_add(data->lapp_context, id, item);
  }

  /* NOTE: currently there is no need to do anything else here, but in the future this would be
   * the place to add specific per-usage decisions on how to append an ID. */

  return IDWALK_RET_NOP;
}

/** \} */

/** \name Library link/append code.
 * \{ */

/** Perform append operation, using modern ID usage looper to detect which ID should be kept
 * linked, made local, duplicated as local, re-used from local etc.
 *
 * The IDs processed by this functions are the one that have been linked by a previous call to
 * #BKE_blendfile_link on the same `lapp_context`. */
void BKE_blendfile_append(BlendfileLinkAppendContext *lapp_context, ReportList *reports)
{
  if (lapp_context->num_items == 0) {
    /* Nothing to append. */
    return;
  }

  Main *bmain = lapp_context->params->bmain;

  BLI_assert((lapp_context->params->flag & FILE_LINK) == 0);

  const bool set_fakeuser = (lapp_context->params->flag & BLO_LIBLINK_APPEND_SET_FAKEUSER) != 0;
  const bool do_reuse_local_id = (lapp_context->params->flag &
                                  BLO_LIBLINK_APPEND_LOCAL_ID_REUSE) != 0;

  const int make_local_common_flags = LIB_ID_MAKELOCAL_FULL_LIBRARY |
                                      ((lapp_context->params->flag &
                                        BLO_LIBLINK_APPEND_ASSET_DATA_CLEAR) != 0 ?
                                           LIB_ID_MAKELOCAL_ASSET_DATA_CLEAR :
                                           0);

  LinkNode *itemlink;

  new_id_to_item_mapping_create(lapp_context);
  lapp_context->library_weak_reference_mapping = BKE_main_library_weak_reference_create(bmain);

  /* NOTE: Since we append items for IDs not already listed (i.e. implicitly linked indirect
   * dependencies), this list will grow and we will process those IDs later, leading to a flatten
   * recursive processing of all the linked dependencies. */
  for (itemlink = lapp_context->items.list; itemlink; itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;
    ID *id = item->new_id;
    if (id == NULL) {
      continue;
    }
    BLI_assert(item->userdata == NULL);

    /* Linked IDs should never be marked as needing post-processing (instantiation of loose
     * objects etc.).
     * NOTE: This is a developer test check, can be removed once we get rid of instantiation code
     * in BLO completely.*/
    BLI_assert((id->tag & LIB_TAG_DOIT) == 0);

    ID *existing_local_id = BKE_idtype_idcode_append_is_reusable(GS(id->name)) ?
                                BKE_main_library_weak_reference_search_item(
                                    lapp_context->library_weak_reference_mapping,
                                    id->lib->filepath,
                                    id->name) :
                                NULL;

    if (item->action != LINK_APPEND_ACT_UNSET) {
      /* Already set, pass. */
    }
    if (GS(id->name) == ID_OB && ((Object *)id)->proxy_from != NULL) {
      CLOG_INFO(&LOG, 3, "Appended ID '%s' is proxified, keeping it linked...", id->name);
      item->action = LINK_APPEND_ACT_KEEP_LINKED;
    }
    else if (do_reuse_local_id && existing_local_id != NULL) {
      CLOG_INFO(&LOG, 3, "Appended ID '%s' as a matching local one, re-using it...", id->name);
      item->action = LINK_APPEND_ACT_REUSE_LOCAL;
      item->userdata = existing_local_id;
    }
    else if (id->tag & LIB_TAG_PRE_EXISTING) {
      CLOG_INFO(&LOG, 3, "Appended ID '%s' was already linked, need to copy it...", id->name);
      item->action = LINK_APPEND_ACT_COPY_LOCAL;
    }
    else {
      CLOG_INFO(&LOG, 3, "Appended ID '%s' will be made local...", id->name);
      item->action = LINK_APPEND_ACT_MAKE_LOCAL;
    }

    /* Only check dependencies if we are not keeping linked data, nor re-using existing local data.
     */
    if (!ELEM(item->action, LINK_APPEND_ACT_KEEP_LINKED, LINK_APPEND_ACT_REUSE_LOCAL)) {
      BlendfileLinkAppendContextCallBack cb_data = {
          .lapp_context = lapp_context, .item = item, .reports = reports};
      BKE_library_foreach_ID_link(
          bmain, id, foreach_libblock_link_append_callback, &cb_data, IDWALK_NOP);
    }

    /* If we found a matching existing local id but are not re-using it, we need to properly clear
     * its weak reference to linked data. */
    if (existing_local_id != NULL &&
        !ELEM(item->action, LINK_APPEND_ACT_KEEP_LINKED, LINK_APPEND_ACT_REUSE_LOCAL)) {
      BKE_main_library_weak_reference_remove_item(lapp_context->library_weak_reference_mapping,
                                                  id->lib->filepath,
                                                  id->name,
                                                  existing_local_id);
    }
  }

  /* Effectively perform required operation on every linked ID. */
  for (itemlink = lapp_context->items.list; itemlink; itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;
    ID *id = item->new_id;
    if (id == NULL) {
      continue;
    }

    ID *local_appended_new_id = NULL;
    char lib_filepath[FILE_MAX];
    BLI_strncpy(lib_filepath, id->lib->filepath, sizeof(lib_filepath));
    char lib_id_name[MAX_ID_NAME];
    BLI_strncpy(lib_id_name, id->name, sizeof(lib_id_name));

    switch (item->action) {
      case LINK_APPEND_ACT_COPY_LOCAL:
        BKE_lib_id_make_local(bmain, id, make_local_common_flags | LIB_ID_MAKELOCAL_FORCE_COPY);
        local_appended_new_id = id->newid;
        break;
      case LINK_APPEND_ACT_MAKE_LOCAL:
        BKE_lib_id_make_local(bmain,
                              id,
                              make_local_common_flags | LIB_ID_MAKELOCAL_FORCE_LOCAL |
                                  LIB_ID_MAKELOCAL_OBJECT_NO_PROXY_CLEARING);
        BLI_assert(id->newid == NULL);
        local_appended_new_id = id;
        break;
      case LINK_APPEND_ACT_KEEP_LINKED:
        /* Nothing to do here. */
        break;
      case LINK_APPEND_ACT_REUSE_LOCAL:
        /* We only need to set `newid` to ID found in previous loop, for proper remapping. */
        ID_NEW_SET(id, item->userdata);
        /* This is not a 'new' local appended id, do not set `local_appended_new_id` here. */
        break;
      case LINK_APPEND_ACT_UNSET:
        CLOG_ERROR(
            &LOG, "Unexpected unset append action for '%s' ID, assuming 'keep link'", id->name);
        break;
      default:
        BLI_assert(0);
    }

    if (local_appended_new_id != NULL) {
      if (BKE_idtype_idcode_append_is_reusable(GS(local_appended_new_id->name))) {
        BKE_main_library_weak_reference_add_item(lapp_context->library_weak_reference_mapping,
                                                 lib_filepath,
                                                 lib_id_name,
                                                 local_appended_new_id);
      }

      if (set_fakeuser) {
        if (!ELEM(GS(local_appended_new_id->name), ID_OB, ID_GR)) {
          /* Do not set fake user on objects nor collections (instancing). */
          id_fake_user_set(local_appended_new_id);
        }
      }
    }
  }

  BKE_main_library_weak_reference_destroy(lapp_context->library_weak_reference_mapping);
  lapp_context->library_weak_reference_mapping = NULL;

  /* Remap IDs as needed. */
  for (itemlink = lapp_context->items.list; itemlink; itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;

    if (item->action == LINK_APPEND_ACT_KEEP_LINKED) {
      continue;
    }

    ID *id = item->new_id;
    if (id == NULL) {
      continue;
    }
    if (ELEM(item->action, LINK_APPEND_ACT_COPY_LOCAL, LINK_APPEND_ACT_REUSE_LOCAL)) {
      BLI_assert(ID_IS_LINKED(id));
      id = id->newid;
      if (id == NULL) {
        continue;
      }
    }

    BLI_assert(!ID_IS_LINKED(id));

    BKE_libblock_relink_to_newid(bmain, id, 0);
  }

  /* Remove linked IDs when a local existing data has been reused instead. */
  BKE_main_id_tag_all(bmain, LIB_TAG_DOIT, false);
  for (itemlink = lapp_context->items.list; itemlink; itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;

    if (item->action != LINK_APPEND_ACT_REUSE_LOCAL) {
      continue;
    }

    ID *id = item->new_id;
    if (id == NULL) {
      continue;
    }
    BLI_assert(ID_IS_LINKED(id));
    BLI_assert(id->newid != NULL);

    id->tag |= LIB_TAG_DOIT;
    item->new_id = id->newid;
  }
  BKE_id_multi_tagged_delete(bmain);

  /* Instantiate newly created (duplicated) IDs as needed. */
  LooseDataInstantiateContext instantiate_context = {.lapp_context = lapp_context,
                                                     .active_collection = NULL};
  loose_data_instantiate(&instantiate_context);

  /* Attempt to deal with object proxies.
   *
   * NOTE: Copied from `BKE_library_make_local`, but this is not really working (as in, not
   * producing any useful result in any known use case), neither here nor in
   * `BKE_library_make_local` currently.
   * Proxies are end of life anyway, so not worth spending time on this. */
  for (itemlink = lapp_context->items.list; itemlink; itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;

    if (item->action != LINK_APPEND_ACT_COPY_LOCAL) {
      continue;
    }

    ID *id = item->new_id;
    if (id == NULL) {
      continue;
    }
    BLI_assert(ID_IS_LINKED(id));

    /* Attempt to re-link copied proxy objects. This allows appending of an entire scene
     * from another blend file into this one, even when that blend file contains proxified
     * armatures that have local references. Since the proxified object needs to be linked
     * (not local), this will only work when the "Localize all" checkbox is disabled.
     * TL;DR: this is a dirty hack on top of an already weak feature (proxies). */
    if (GS(id->name) == ID_OB && ((Object *)id)->proxy != NULL) {
      Object *ob = (Object *)id;
      Object *ob_new = (Object *)id->newid;
      bool is_local = false, is_lib = false;

      /* Proxies only work when the proxified object is linked-in from a library. */
      if (!ID_IS_LINKED(ob->proxy)) {
        CLOG_WARN(&LOG,
                  "Proxy object %s will lose its link to %s, because the "
                  "proxified object is local",
                  id->newid->name,
                  ob->proxy->id.name);
        continue;
      }

      BKE_library_ID_test_usages(bmain, id, &is_local, &is_lib);

      /* We can only switch the proxy'ing to a made-local proxy if it is no longer
       * referred to from a library. Not checking for local use; if new local proxy
       * was not used locally would be a nasty bug! */
      if (is_local || is_lib) {
        CLOG_WARN(&LOG,
                  "Made-local proxy object %s will lose its link to %s, "
                  "because the linked-in proxy is referenced (is_local=%i, is_lib=%i)",
                  id->newid->name,
                  ob->proxy->id.name,
                  is_local,
                  is_lib);
      }
      else {
        /* we can switch the proxy'ing from the linked-in to the made-local proxy.
         * BKE_object_make_proxy() shouldn't be used here, as it allocates memory that
         * was already allocated by object_make_local() (which called BKE_object_copy). */
        ob_new->proxy = ob->proxy;
        ob_new->proxy_group = ob->proxy_group;
        ob_new->proxy_from = ob->proxy_from;
        ob_new->proxy->proxy_from = ob_new;
        ob->proxy = ob->proxy_from = ob->proxy_group = NULL;
      }
    }
  }

  BKE_main_id_newptr_and_tag_clear(bmain);
}

/** Perform linking operation on all items added to given `lapp_context`. */
void BKE_blendfile_link(BlendfileLinkAppendContext *lapp_context, ReportList *reports)
{
  if (lapp_context->num_items == 0) {
    /* Nothing to be linked. */
    return;
  }

  BLI_assert(lapp_context->num_libraries != 0);

  Main *mainl;
  Library *lib;

  LinkNode *liblink, *itemlink;
  int lib_idx, item_idx;

  for (lib_idx = 0, liblink = lapp_context->libraries.list; liblink;
       lib_idx++, liblink = liblink->next) {
    BlendfileLinkAppendContextLibrary *lib_context = liblink->link;
    char *libname = lib_context->path;
    BlendHandle *blo_handle = link_append_context_library_blohandle_ensure(
        lapp_context, lib_context, reports);

    if (blo_handle == NULL) {
      /* Unlikely since we just browsed it, but possible
       * Error reports will have been made by BLO_blendhandle_from_file() */
      continue;
    }

    /* here appending/linking starts */

    mainl = BLO_library_link_begin(&blo_handle, libname, lapp_context->params);
    lib = mainl->curlib;
    BLI_assert(lib);
    UNUSED_VARS_NDEBUG(lib);

    if (mainl->versionfile < 250) {
      BKE_reportf(reports,
                  RPT_WARNING,
                  "Linking or appending from a very old .blend file format (%d.%d), no animation "
                  "conversion will "
                  "be done! You may want to re-save your lib file with current Blender",
                  mainl->versionfile,
                  mainl->subversionfile);
    }

    /* For each lib file, we try to link all items belonging to that lib,
     * and tag those successful to not try to load them again with the other libs. */
    for (item_idx = 0, itemlink = lapp_context->items.list; itemlink;
         item_idx++, itemlink = itemlink->next) {
      BlendfileLinkAppendContextItem *item = itemlink->link;
      ID *new_id;

      if (!BLI_BITMAP_TEST(item->libraries, lib_idx)) {
        continue;
      }

      new_id = BLO_library_link_named_part(
          mainl, &blo_handle, item->idcode, item->name, lapp_context->params);

      if (new_id) {
        /* If the link is successful, clear item's libs 'todo' flags.
         * This avoids trying to link same item with other libraries to come. */
        BLI_bitmap_set_all(item->libraries, false, lapp_context->num_libraries);
        item->new_id = new_id;
        item->source_library = new_id->lib;
      }
    }

    BLO_library_link_end(mainl, &blo_handle, lapp_context->params);
    link_append_context_library_blohandle_release(lapp_context, lib_context);
  }

  /* Instantiate newly linked IDs as needed, if no append is scheduled. */
  if ((lapp_context->params->flag & FILE_LINK) != 0 &&
      lapp_context->params->context.scene != NULL) {
    new_id_to_item_mapping_create(lapp_context);
    /* NOTE: Since we append items for IDs not already listed (i.e. implicitly linked indirect
     * dependencies), this list will grow and we will process those IDs later, leading to a flatten
     * recursive processing of all the linked dependencies. */
    for (itemlink = lapp_context->items.list; itemlink; itemlink = itemlink->next) {
      BlendfileLinkAppendContextItem *item = itemlink->link;
      ID *id = item->new_id;
      if (id == NULL) {
        continue;
      }
      BLI_assert(item->userdata == NULL);

      /* Linked IDs should never be marked as needing post-processing (instantiation of loose
       * objects etc.).
       * NOTE: This is developer test check, can be removed once we get rid of instantiation code
       * in BLO completely.*/
      BLI_assert((id->tag & LIB_TAG_DOIT) == 0);

      BlendfileLinkAppendContextCallBack cb_data = {
          .lapp_context = lapp_context, .item = item, .reports = reports};
      BKE_library_foreach_ID_link(lapp_context->params->bmain,
                                  id,
                                  foreach_libblock_link_append_callback,
                                  &cb_data,
                                  IDWALK_NOP);
    }

    LooseDataInstantiateContext instantiate_context = {.lapp_context = lapp_context,
                                                       .active_collection = NULL};
    loose_data_instantiate(&instantiate_context);
  }
}

/** \} */

/** \name Library relocating code.
 * \{ */

static void blendfile_library_relocate_remap(Main *bmain,
                                             ID *old_id,
                                             ID *new_id,
                                             ReportList *reports,
                                             const bool do_reload,
                                             const short remap_flags)
{
  BLI_assert(old_id);
  if (do_reload) {
    /* Since we asked for placeholders in case of missing IDs,
     * we expect to always get a valid one. */
    BLI_assert(new_id);
  }
  if (new_id) {
    CLOG_INFO(&LOG,
              4,
              "Before remap of %s, old_id users: %d, new_id users: %d",
              old_id->name,
              old_id->us,
              new_id->us);
    BKE_libblock_remap_locked(bmain, old_id, new_id, remap_flags);

    if (old_id->flag & LIB_FAKEUSER) {
      id_fake_user_clear(old_id);
      id_fake_user_set(new_id);
    }

    CLOG_INFO(&LOG,
              4,
              "After remap of %s, old_id users: %d, new_id users: %d",
              old_id->name,
              old_id->us,
              new_id->us);

    /* In some cases, new_id might become direct link, remove parent of library in this case. */
    if (new_id->lib->parent && (new_id->tag & LIB_TAG_INDIRECT) == 0) {
      if (do_reload) {
        BLI_assert_unreachable(); /* Should not happen in 'pure' reload case... */
      }
      new_id->lib->parent = NULL;
    }
  }

  if (old_id->us > 0 && new_id && old_id->lib == new_id->lib) {
    /* Note that this *should* not happen - but better be safe than sorry in this area,
     * at least until we are 100% sure this cannot ever happen.
     * Also, we can safely assume names were unique so far,
     * so just replacing '.' by '~' should work,
     * but this does not totally rules out the possibility of name collision. */
    size_t len = strlen(old_id->name);
    size_t dot_pos;
    bool has_num = false;

    for (dot_pos = len; dot_pos--;) {
      char c = old_id->name[dot_pos];
      if (c == '.') {
        break;
      }
      if (c < '0' || c > '9') {
        has_num = false;
        break;
      }
      has_num = true;
    }

    if (has_num) {
      old_id->name[dot_pos] = '~';
    }
    else {
      len = MIN2(len, MAX_ID_NAME - 7);
      BLI_strncpy(&old_id->name[len], "~000", 7);
    }

    id_sort_by_name(which_libbase(bmain, GS(old_id->name)), old_id, NULL);

    BKE_reportf(
        reports,
        RPT_WARNING,
        "Lib Reload: Replacing all references to old data-block '%s' by reloaded one failed, "
        "old one (%d remaining users) had to be kept and was renamed to '%s'",
        new_id->name,
        old_id->us,
        old_id->name);
  }
}

/** Try to relocate all linked IDs added to `lapp_context`, belonging to the given `library`.
 *
 * This function searches for matching IDs (type and name) in all libraries added to the given
 * `lapp_context`.
 *
 * Typical usages include:
 *  * Relocating a library:
 *    - Add the new target library path to `lapp_context`.
 *    - Add all IDs from the library to relocate to `lapp_context`
 *    - Mark the new target library to be considered for each ID.
 *    - Call this function.
 *
 *  * Searching for (e.g.missing) linked IDs in a set or sub-set of libraries:
 *    - Add all potential library sources paths to `lapp_context`.
 *    - Add all IDs to search for to `lapp_context`.
 *    - Mark which libraries should be considered for each ID.
 *    - Call this function. */
void BKE_blendfile_library_relocate(BlendfileLinkAppendContext *lapp_context,
                                    ReportList *reports,
                                    Library *library,
                                    const bool do_reload)
{
  ListBase *lbarray[INDEX_ID_MAX];
  int lba_idx;

  LinkNode *itemlink;
  int item_idx;

  Main *bmain = lapp_context->params->bmain;

  /* All override rules need to be up to date, since there will be no do_version here, otherwise
   * older, now-invalid rules might be applied and likely fail, or some changes might be missing,
   * etc. See T93353. */
  BKE_lib_override_library_main_operations_create(bmain, true);

  /* Remove all IDs to be reloaded from Main. */
  lba_idx = set_listbasepointers(bmain, lbarray);
  while (lba_idx--) {
    ID *id = lbarray[lba_idx]->first;
    const short idcode = id ? GS(id->name) : 0;

    if (!id || !BKE_idtype_idcode_is_linkable(idcode)) {
      /* No need to reload non-linkable datatypes,
       * those will get relinked with their 'users ID'. */
      continue;
    }

    for (; id; id = id->next) {
      if (id->lib == library) {
        BlendfileLinkAppendContextItem *item;

        /* We remove it from current Main, and add it to items to link... */
        /* Note that non-linkable IDs (like e.g. shapekeys) are also explicitly linked here... */
        BLI_remlink(lbarray[lba_idx], id);
        /* Usual special code for ShapeKeys snowflakes... */
        Key *old_key = BKE_key_from_id(id);
        if (old_key != NULL) {
          BLI_remlink(which_libbase(bmain, GS(old_key->id.name)), &old_key->id);
        }

        item = BKE_blendfile_link_append_context_item_add(lapp_context, id->name + 2, idcode, id);
        BLI_bitmap_set_all(item->libraries, true, (size_t)lapp_context->num_libraries);

        CLOG_INFO(&LOG, 4, "Datablock to seek for: %s", id->name);
      }
    }
  }

  if (lapp_context->num_items == 0) {
    /* Early out in case there is nothing to do. */
    return;
  }

  BKE_main_id_tag_all(bmain, LIB_TAG_PRE_EXISTING, true);

  /* We do not want any instantiation here! */
  BKE_blendfile_link(lapp_context, reports);

  BKE_main_lock(bmain);

  /* We add back old id to bmain.
   * We need to do this in a first, separated loop, otherwise some of those may not be handled by
   * ID remapping, which means they would still reference old data to be deleted... */
  for (item_idx = 0, itemlink = lapp_context->items.list; itemlink;
       item_idx++, itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;
    ID *old_id = item->userdata;

    BLI_assert(old_id);
    BLI_addtail(which_libbase(bmain, GS(old_id->name)), old_id);

    /* Usual special code for ShapeKeys snowflakes... */
    Key *old_key = BKE_key_from_id(old_id);
    if (old_key != NULL) {
      BLI_addtail(which_libbase(bmain, GS(old_key->id.name)), &old_key->id);
    }
  }

  /* Since our (old) reloaded IDs were removed from main, the user count done for them in linking
   * code is wrong, we need to redo it here after adding them back to main. */
  BKE_main_id_refcount_recompute(bmain, false);

  /* Note that in reload case, we also want to replace indirect usages. */
  const short remap_flags = ID_REMAP_SKIP_NEVER_NULL_USAGE |
                            ID_REMAP_NO_INDIRECT_PROXY_DATA_USAGE |
                            (do_reload ? 0 : ID_REMAP_SKIP_INDIRECT_USAGE);
  for (item_idx = 0, itemlink = lapp_context->items.list; itemlink;
       item_idx++, itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;
    ID *old_id = item->userdata;
    ID *new_id = item->new_id;

    blendfile_library_relocate_remap(bmain, old_id, new_id, reports, do_reload, remap_flags);
    if (new_id == NULL) {
      continue;
    }
    /* Usual special code for ShapeKeys snowflakes... */
    Key **old_key_p = BKE_key_from_id_p(old_id);
    if (old_key_p == NULL) {
      continue;
    }
    Key *old_key = *old_key_p;
    Key *new_key = BKE_key_from_id(new_id);
    if (old_key != NULL) {
      *old_key_p = NULL;
      id_us_min(&old_key->id);
      blendfile_library_relocate_remap(
          bmain, &old_key->id, &new_key->id, reports, do_reload, remap_flags);
      *old_key_p = old_key;
      id_us_plus_no_lib(&old_key->id);
    }
  }

  BKE_main_unlock(bmain);

  for (item_idx = 0, itemlink = lapp_context->items.list; itemlink;
       item_idx++, itemlink = itemlink->next) {
    BlendfileLinkAppendContextItem *item = itemlink->link;
    ID *old_id = item->userdata;

    if (old_id->us == 0) {
      BKE_id_free(bmain, old_id);
    }
  }

  /* Some datablocks can get reloaded/replaced 'silently' because they are not linkable
   * (shape keys e.g.), so we need another loop here to clear old ones if possible. */
  lba_idx = set_listbasepointers(bmain, lbarray);
  while (lba_idx--) {
    ID *id, *id_next;
    for (id = lbarray[lba_idx]->first; id; id = id_next) {
      id_next = id->next;
      /* XXX That check may be a bit to generic/permissive? */
      if (id->lib && (id->flag & LIB_TAG_PRE_EXISTING) && id->us == 0) {
        BKE_id_free(bmain, id);
      }
    }
  }

  /* Get rid of no more used libraries... */
  BKE_main_id_tag_idcode(bmain, ID_LI, LIB_TAG_DOIT, true);
  lba_idx = set_listbasepointers(bmain, lbarray);
  while (lba_idx--) {
    ID *id;
    for (id = lbarray[lba_idx]->first; id; id = id->next) {
      if (id->lib) {
        id->lib->id.tag &= ~LIB_TAG_DOIT;
      }
    }
  }
  Library *lib, *lib_next;
  for (lib = which_libbase(bmain, ID_LI)->first; lib; lib = lib_next) {
    lib_next = lib->id.next;
    if (lib->id.tag & LIB_TAG_DOIT) {
      id_us_clear_real(&lib->id);
      if (lib->id.us == 0) {
        BKE_id_free(bmain, (ID *)lib);
      }
    }
  }

  /* Update overrides of reloaded linked data-blocks. */
  ID *id;
  FOREACH_MAIN_ID_BEGIN (bmain, id) {
    if (ID_IS_LINKED(id) || !ID_IS_OVERRIDE_LIBRARY_REAL(id) ||
        (id->tag & LIB_TAG_PRE_EXISTING) == 0) {
      continue;
    }
    if ((id->override_library->reference->tag & LIB_TAG_PRE_EXISTING) == 0) {
      BKE_lib_override_library_update(bmain, id);
    }
  }
  FOREACH_MAIN_ID_END;

  /* Resync overrides if needed. */
  if (!USER_EXPERIMENTAL_TEST(&U, no_override_auto_resync)) {
    BKE_lib_override_library_main_resync(bmain,
                                         lapp_context->params->context.scene,
                                         lapp_context->params->context.view_layer,
                                         &(struct BlendFileReadReport){
                                             .reports = reports,
                                         });
    /* We need to rebuild some of the deleted override rules (for UI feedback purpose). */
    BKE_lib_override_library_main_operations_create(bmain, true);
  }

  BKE_main_collection_sync(bmain);
}

/** \} */
