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
 *
 * The Original Code is Copyright (C) 2016 by Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup bke
 */

#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_ID.h"
#include "DNA_object_types.h"

#include "DEG_depsgraph.h"

#include "BKE_armature.h"
#include "BKE_lib_id.h"
#include "BKE_lib_override.h"
#include "BKE_lib_remap.h"
#include "BKE_main.h"

#include "BLI_ghash.h"
#include "BLI_listbase.h"
#include "BLI_string.h"
#include "BLI_task.h"
#include "BLI_utildefines.h"

#include "RNA_access.h"
#include "RNA_types.h"

#define OVERRIDE_AUTO_CHECK_DELAY 0.2 /* 200ms between auto-override checks. */
//#define DEBUG_OVERRIDE_TIMEIT

#ifdef DEBUG_OVERRIDE_TIMEIT
#  include "PIL_time_utildefines.h"
#endif

static void lib_override_library_property_copy(IDOverrideLibraryProperty *op_dst,
                                               IDOverrideLibraryProperty *op_src);
static void lib_override_library_property_operation_copy(
    IDOverrideLibraryPropertyOperation *opop_dst, IDOverrideLibraryPropertyOperation *opop_src);

static void lib_override_library_property_clear(IDOverrideLibraryProperty *op);
static void lib_override_library_property_operation_clear(
    IDOverrideLibraryPropertyOperation *opop);

/* Temp, for until library override is ready and tested enough to go 'public',
 * we hide it by default in UI and such. */
static bool _lib_override_library_enabled = true;

void BKE_lib_override_library_enable(const bool do_enable)
{
  _lib_override_library_enabled = do_enable;
}

bool BKE_lib_override_library_is_enabled()
{
  return _lib_override_library_enabled;
}

/** Initialize empty overriding of \a reference_id by \a local_id. */
IDOverrideLibrary *BKE_lib_override_library_init(ID *local_id, ID *reference_id)
{
  /* If reference_id is NULL, we are creating an override template for purely local data.
   * Else, reference *must* be linked data. */
  BLI_assert(reference_id == NULL || reference_id->lib != NULL);
  BLI_assert(local_id->override_library == NULL);

  ID *ancestor_id;
  for (ancestor_id = reference_id; ancestor_id != NULL && ancestor_id->override_library != NULL &&
                                   ancestor_id->override_library->reference != NULL;
       ancestor_id = ancestor_id->override_library->reference) {
    /* pass */
  }

  if (ancestor_id != NULL && ancestor_id->override_library != NULL) {
    /* Original ID has a template, use it! */
    BKE_lib_override_library_copy(local_id, ancestor_id, true);
    if (local_id->override_library->reference != reference_id) {
      id_us_min(local_id->override_library->reference);
      local_id->override_library->reference = reference_id;
      id_us_plus(local_id->override_library->reference);
    }
    return local_id->override_library;
  }

  /* Else, generate new empty override. */
  local_id->override_library = MEM_callocN(sizeof(*local_id->override_library), __func__);
  local_id->override_library->reference = reference_id;
  id_us_plus(local_id->override_library->reference);
  local_id->tag &= ~LIB_TAG_OVERRIDE_LIBRARY_REFOK;
  /* TODO do we want to add tag or flag to referee to mark it as such? */
  return local_id->override_library;
}

/** Shalow or deep copy of a whole override from \a src_id to \a dst_id. */
void BKE_lib_override_library_copy(ID *dst_id, const ID *src_id, const bool do_full_copy)
{
  BLI_assert(src_id->override_library != NULL);

  if (dst_id->override_library != NULL) {
    if (src_id->override_library == NULL) {
      BKE_lib_override_library_free(&dst_id->override_library, true);
      return;
    }
    else {
      BKE_lib_override_library_clear(dst_id->override_library, true);
    }
  }
  else if (src_id->override_library == NULL) {
    return;
  }
  else {
    BKE_lib_override_library_init(dst_id, NULL);
  }

  /* Source is already overriding data, we copy it but reuse its reference for dest ID.
   * otherwise, source is only an override template, it then becomes reference of dest ID. */
  dst_id->override_library->reference = src_id->override_library->reference ?
                                            src_id->override_library->reference :
                                            (ID *)src_id;
  id_us_plus(dst_id->override_library->reference);

  if (do_full_copy) {
    BLI_duplicatelist(&dst_id->override_library->properties,
                      &src_id->override_library->properties);
    for (IDOverrideLibraryProperty *op_dst = dst_id->override_library->properties.first,
                                   *op_src = src_id->override_library->properties.first;
         op_dst;
         op_dst = op_dst->next, op_src = op_src->next) {
      lib_override_library_property_copy(op_dst, op_src);
    }
  }

  dst_id->tag &= ~LIB_TAG_OVERRIDE_LIBRARY_REFOK;
}

/** Clear any overriding data from given \a override. */
void BKE_lib_override_library_clear(IDOverrideLibrary *override, const bool do_id_user)
{
  BLI_assert(override != NULL);

  if (override->runtime != NULL) {
    BLI_ghash_clear(override->runtime, NULL, NULL);
  }

  LISTBASE_FOREACH (IDOverrideLibraryProperty *, op, &override->properties) {
    lib_override_library_property_clear(op);
  }
  BLI_freelistN(&override->properties);

  if (do_id_user) {
    id_us_min(override->reference);
    /* override->storage should never be refcounted... */
  }
}

/** Free given \a override. */
void BKE_lib_override_library_free(struct IDOverrideLibrary **override, const bool do_id_user)
{
  BLI_assert(*override != NULL);

  if ((*override)->runtime != NULL) {
    BLI_ghash_free((*override)->runtime, NULL, NULL);
    (*override)->runtime = NULL;
  }

  BKE_lib_override_library_clear(*override, do_id_user);
  MEM_freeN(*override);
  *override = NULL;
}

static ID *lib_override_library_create_from(Main *bmain, ID *reference_id)
{
  ID *local_id;

  if (!BKE_id_copy(bmain, reference_id, (ID **)&local_id)) {
    return NULL;
  }
  id_us_min(local_id);

  BKE_lib_override_library_init(local_id, reference_id);

  return local_id;
}

/** Create an overridden local copy of linked reference. */
ID *BKE_lib_override_library_create_from_id(Main *bmain,
                                            ID *reference_id,
                                            const bool do_tagged_remap)
{
  BLI_assert(reference_id != NULL);
  BLI_assert(reference_id->lib != NULL);

  ID *local_id = lib_override_library_create_from(bmain, reference_id);

  if (do_tagged_remap) {
    ID *other_id;
    FOREACH_MAIN_ID_BEGIN (bmain, other_id) {
      if ((other_id->tag & LIB_TAG_DOIT) != 0 && other_id->lib == NULL) {
        /* Note that using ID_REMAP_SKIP_INDIRECT_USAGE below is superfluous, as we only remap
         * local IDs usages anyway... */
        BKE_libblock_relink_ex(bmain,
                               other_id,
                               reference_id,
                               local_id,
                               ID_REMAP_SKIP_INDIRECT_USAGE | ID_REMAP_SKIP_OVERRIDE_LIBRARY);
      }
    }
    FOREACH_MAIN_ID_END;
  }

  return local_id;
}

/**
 * Create overridden local copies of all tagged data-blocks in given Main.
 *
 * \note Set id->newid of overridden libs with newly created overrides,
 * caller is responsible to clean those pointers before/after usage as needed.
 *
 * \note By default, it will only remap newly created local overriding data-blocks between
 * themselves, to avoid 'enforcing' those overrides into all other usages of the linked data in
 * main. You can add more local IDs to be remapped to use new overriding ones by setting their
 * LIB_TAG_DOIT tag.
 *
 * \return \a true on success, \a false otherwise.
 */
bool BKE_lib_override_library_create_from_tag(Main *bmain)
{
  ID *reference_id;
  bool ret = true;

  ListBase todo_ids = {NULL};
  LinkData *todo_id_iter;

  /* Get all IDs we want to override. */
  FOREACH_MAIN_ID_BEGIN (bmain, reference_id) {
    if ((reference_id->tag & LIB_TAG_DOIT) != 0 && reference_id->lib != NULL) {
      todo_id_iter = MEM_callocN(sizeof(*todo_id_iter), __func__);
      todo_id_iter->data = reference_id;
      BLI_addtail(&todo_ids, todo_id_iter);
    }
  }
  FOREACH_MAIN_ID_END;

  /* Override the IDs. */
  for (todo_id_iter = todo_ids.first; todo_id_iter != NULL; todo_id_iter = todo_id_iter->next) {
    reference_id = todo_id_iter->data;
    if ((reference_id->newid = lib_override_library_create_from(bmain, reference_id)) == NULL) {
      ret = false;
    }
    else {
      /* We also tag the new IDs so that in next step we can remap their pointers too. */
      reference_id->newid->tag |= LIB_TAG_DOIT;
    }
  }

  /* Only remap new local ID's pointers, we don't want to force our new overrides onto our whole
   * existing linked IDs usages. */
  for (todo_id_iter = todo_ids.first; todo_id_iter != NULL; todo_id_iter = todo_id_iter->next) {
    ID *other_id;
    reference_id = todo_id_iter->data;

    if (reference_id->newid == NULL) {
      continue;
    }

    /* Still checking the whole Main, that way we can tag other local IDs as needing to be remapped
     * to use newly created overriding IDs, if needed. */
    FOREACH_MAIN_ID_BEGIN (bmain, other_id) {
      if ((other_id->tag & LIB_TAG_DOIT) != 0 && other_id->lib == NULL) {
        ID *local_id = reference_id->newid;
        /* Note that using ID_REMAP_SKIP_INDIRECT_USAGE below is superfluous, as we only remap
         * local IDs usages anyway... */
        BKE_libblock_relink_ex(bmain,
                               other_id,
                               reference_id,
                               local_id,
                               ID_REMAP_SKIP_INDIRECT_USAGE | ID_REMAP_SKIP_OVERRIDE_LIBRARY);
      }
    }
    FOREACH_MAIN_ID_END;
  }

  BLI_freelistN(&todo_ids);

  return ret;
}

/* We only build override GHash on request. */
BLI_INLINE IDOverrideLibraryRuntime *override_library_rna_path_mapping_ensure(
    IDOverrideLibrary *override)
{
  if (override->runtime == NULL) {
    override->runtime = BLI_ghash_new(
        BLI_ghashutil_strhash_p_murmur, BLI_ghashutil_strcmp, __func__);
    for (IDOverrideLibraryProperty *op = override->properties.first; op != NULL; op = op->next) {
      BLI_ghash_insert(override->runtime, op->rna_path, op);
    }
  }

  return override->runtime;
}

/**
 * Find override property from given RNA path, if it exists.
 */
IDOverrideLibraryProperty *BKE_lib_override_library_property_find(IDOverrideLibrary *override,
                                                                  const char *rna_path)
{
  IDOverrideLibraryRuntime *override_runtime = override_library_rna_path_mapping_ensure(override);
  return BLI_ghash_lookup(override_runtime, rna_path);
}

/**
 * Find override property from given RNA path, or create it if it does not exist.
 */
IDOverrideLibraryProperty *BKE_lib_override_library_property_get(IDOverrideLibrary *override,
                                                                 const char *rna_path,
                                                                 bool *r_created)
{
  IDOverrideLibraryProperty *op = BKE_lib_override_library_property_find(override, rna_path);

  if (op == NULL) {
    op = MEM_callocN(sizeof(IDOverrideLibraryProperty), __func__);
    op->rna_path = BLI_strdup(rna_path);
    BLI_addtail(&override->properties, op);

    IDOverrideLibraryRuntime *override_runtime = override_library_rna_path_mapping_ensure(
        override);
    BLI_ghash_insert(override_runtime, op->rna_path, op);

    if (r_created) {
      *r_created = true;
    }
  }
  else if (r_created) {
    *r_created = false;
  }

  return op;
}

void lib_override_library_property_copy(IDOverrideLibraryProperty *op_dst,
                                        IDOverrideLibraryProperty *op_src)
{
  op_dst->rna_path = BLI_strdup(op_src->rna_path);
  BLI_duplicatelist(&op_dst->operations, &op_src->operations);

  for (IDOverrideLibraryPropertyOperation *opop_dst = op_dst->operations.first,
                                          *opop_src = op_src->operations.first;
       opop_dst;
       opop_dst = opop_dst->next, opop_src = opop_src->next) {
    lib_override_library_property_operation_copy(opop_dst, opop_src);
  }
}

void lib_override_library_property_clear(IDOverrideLibraryProperty *op)
{
  BLI_assert(op->rna_path != NULL);

  MEM_freeN(op->rna_path);

  LISTBASE_FOREACH (IDOverrideLibraryPropertyOperation *, opop, &op->operations) {
    lib_override_library_property_operation_clear(opop);
  }
  BLI_freelistN(&op->operations);
}

/**
 * Remove and free given \a override_property from given ID \a override.
 */
void BKE_lib_override_library_property_delete(IDOverrideLibrary *override,
                                              IDOverrideLibraryProperty *override_property)
{
  if (override->runtime != NULL) {
    BLI_ghash_remove(override->runtime, override_property->rna_path, NULL, NULL);
  }
  lib_override_library_property_clear(override_property);
  BLI_freelinkN(&override->properties, override_property);
}

/**
 * Find override property operation from given sub-item(s), if it exists.
 */
IDOverrideLibraryPropertyOperation *BKE_lib_override_library_property_operation_find(
    IDOverrideLibraryProperty *override_property,
    const char *subitem_refname,
    const char *subitem_locname,
    const int subitem_refindex,
    const int subitem_locindex,
    const bool strict,
    bool *r_strict)
{
  IDOverrideLibraryPropertyOperation *opop;
  const int subitem_defindex = -1;

  if (r_strict) {
    *r_strict = true;
  }

  if (subitem_locname != NULL) {
    opop = BLI_findstring_ptr(&override_property->operations,
                              subitem_locname,
                              offsetof(IDOverrideLibraryPropertyOperation, subitem_local_name));

    if (opop == NULL) {
      return NULL;
    }

    if (subitem_refname == NULL || opop->subitem_reference_name == NULL) {
      return subitem_refname == opop->subitem_reference_name ? opop : NULL;
    }
    return (subitem_refname != NULL && opop->subitem_reference_name != NULL &&
            STREQ(subitem_refname, opop->subitem_reference_name)) ?
               opop :
               NULL;
  }

  if (subitem_refname != NULL) {
    opop = BLI_findstring_ptr(
        &override_property->operations,
        subitem_refname,
        offsetof(IDOverrideLibraryPropertyOperation, subitem_reference_name));

    if (opop == NULL) {
      return NULL;
    }

    if (subitem_locname == NULL || opop->subitem_local_name == NULL) {
      return subitem_locname == opop->subitem_local_name ? opop : NULL;
    }
    return (subitem_locname != NULL && opop->subitem_local_name != NULL &&
            STREQ(subitem_locname, opop->subitem_local_name)) ?
               opop :
               NULL;
  }

  if ((opop = BLI_listbase_bytes_find(
           &override_property->operations,
           &subitem_locindex,
           sizeof(subitem_locindex),
           offsetof(IDOverrideLibraryPropertyOperation, subitem_local_index)))) {
    return ELEM(subitem_refindex, -1, opop->subitem_reference_index) ? opop : NULL;
  }

  if ((opop = BLI_listbase_bytes_find(
           &override_property->operations,
           &subitem_refindex,
           sizeof(subitem_refindex),
           offsetof(IDOverrideLibraryPropertyOperation, subitem_reference_index)))) {
    return ELEM(subitem_locindex, -1, opop->subitem_local_index) ? opop : NULL;
  }

  /* index == -1 means all indices, that is valid fallback in case we requested specific index. */
  if (!strict && (subitem_locindex != subitem_defindex) &&
      (opop = BLI_listbase_bytes_find(
           &override_property->operations,
           &subitem_defindex,
           sizeof(subitem_defindex),
           offsetof(IDOverrideLibraryPropertyOperation, subitem_local_index)))) {
    if (r_strict) {
      *r_strict = false;
    }
    return opop;
  }

  return NULL;
}

/**
 * Find override property operation from given sub-item(s), or create it if it does not exist.
 */
IDOverrideLibraryPropertyOperation *BKE_lib_override_library_property_operation_get(
    IDOverrideLibraryProperty *override_property,
    const short operation,
    const char *subitem_refname,
    const char *subitem_locname,
    const int subitem_refindex,
    const int subitem_locindex,
    const bool strict,
    bool *r_strict,
    bool *r_created)
{
  IDOverrideLibraryPropertyOperation *opop = BKE_lib_override_library_property_operation_find(
      override_property,
      subitem_refname,
      subitem_locname,
      subitem_refindex,
      subitem_locindex,
      strict,
      r_strict);

  if (opop == NULL) {
    opop = MEM_callocN(sizeof(IDOverrideLibraryPropertyOperation), __func__);
    opop->operation = operation;
    if (subitem_locname) {
      opop->subitem_local_name = BLI_strdup(subitem_locname);
    }
    if (subitem_refname) {
      opop->subitem_reference_name = BLI_strdup(subitem_refname);
    }
    opop->subitem_local_index = subitem_locindex;
    opop->subitem_reference_index = subitem_refindex;

    BLI_addtail(&override_property->operations, opop);

    if (r_created) {
      *r_created = true;
    }
  }
  else if (r_created) {
    *r_created = false;
  }

  return opop;
}

void lib_override_library_property_operation_copy(IDOverrideLibraryPropertyOperation *opop_dst,
                                                  IDOverrideLibraryPropertyOperation *opop_src)
{
  if (opop_src->subitem_reference_name) {
    opop_dst->subitem_reference_name = BLI_strdup(opop_src->subitem_reference_name);
  }
  if (opop_src->subitem_local_name) {
    opop_dst->subitem_local_name = BLI_strdup(opop_src->subitem_local_name);
  }
}

void lib_override_library_property_operation_clear(IDOverrideLibraryPropertyOperation *opop)
{
  if (opop->subitem_reference_name) {
    MEM_freeN(opop->subitem_reference_name);
  }
  if (opop->subitem_local_name) {
    MEM_freeN(opop->subitem_local_name);
  }
}

/**
 * Remove and free given \a override_property_operation from given ID \a override_property.
 */
void BKE_lib_override_library_property_operation_delete(
    IDOverrideLibraryProperty *override_property,
    IDOverrideLibraryPropertyOperation *override_property_operation)
{
  lib_override_library_property_operation_clear(override_property_operation);
  BLI_freelinkN(&override_property->operations, override_property_operation);
}

/**
 * Validate that required data for a given operation are available.
 */
bool BKE_lib_override_library_property_operation_operands_validate(
    struct IDOverrideLibraryPropertyOperation *override_property_operation,
    struct PointerRNA *ptr_dst,
    struct PointerRNA *ptr_src,
    struct PointerRNA *ptr_storage,
    struct PropertyRNA *prop_dst,
    struct PropertyRNA *prop_src,
    struct PropertyRNA *prop_storage)
{
  switch (override_property_operation->operation) {
    case IDOVERRIDE_LIBRARY_OP_NOOP:
      return true;
    case IDOVERRIDE_LIBRARY_OP_ADD:
      ATTR_FALLTHROUGH;
    case IDOVERRIDE_LIBRARY_OP_SUBTRACT:
      ATTR_FALLTHROUGH;
    case IDOVERRIDE_LIBRARY_OP_MULTIPLY:
      if (ptr_storage == NULL || ptr_storage->data == NULL || prop_storage == NULL) {
        BLI_assert(!"Missing data to apply differential override operation.");
        return false;
      }
      ATTR_FALLTHROUGH;
    case IDOVERRIDE_LIBRARY_OP_INSERT_AFTER:
      ATTR_FALLTHROUGH;
    case IDOVERRIDE_LIBRARY_OP_INSERT_BEFORE:
      ATTR_FALLTHROUGH;
    case IDOVERRIDE_LIBRARY_OP_REPLACE:
      if ((ptr_dst == NULL || ptr_dst->data == NULL || prop_dst == NULL) ||
          (ptr_src == NULL || ptr_src->data == NULL || prop_src == NULL)) {
        BLI_assert(!"Missing data to apply override operation.");
        return false;
      }
  }

  return true;
}

/**
 * Check that status of local data-block is still valid against current reference one.
 *
 * It means that all overridable, but not overridden, properties' local values must be equal to
 * reference ones. Clears #LIB_TAG_OVERRIDE_OK if they do not.
 *
 * This is typically used to detect whether some property has been changed in local and a new
 * #IDOverrideProperty (of #IDOverridePropertyOperation) has to be added.
 *
 * \return true if status is OK, false otherwise. */
bool BKE_lib_override_library_status_check_local(Main *bmain, ID *local)
{
  BLI_assert(local->override_library != NULL);

  ID *reference = local->override_library->reference;

  if (reference == NULL) {
    /* This is an override template, local status is always OK! */
    return true;
  }

  BLI_assert(GS(local->name) == GS(reference->name));

  if (GS(local->name) == ID_OB) {
    /* Our beloved pose's bone cross-data pointers... Usually, depsgraph evaluation would ensure
     * this is valid, but in some cases (like hidden collections etc.) this won't be the case, so
     * we need to take care of this ourselves. */
    Object *ob_local = (Object *)local;
    if (ob_local->data != NULL && ob_local->type == OB_ARMATURE && ob_local->pose != NULL &&
        ob_local->pose->flag & POSE_RECALC) {
      BKE_pose_rebuild(bmain, ob_local, ob_local->data, true);
    }
  }

  /* Note that reference is assumed always valid, caller has to ensure that itself. */

  PointerRNA rnaptr_local, rnaptr_reference;
  RNA_id_pointer_create(local, &rnaptr_local);
  RNA_id_pointer_create(reference, &rnaptr_reference);

  if (!RNA_struct_override_matches(bmain,
                                   &rnaptr_local,
                                   &rnaptr_reference,
                                   NULL,
                                   0,
                                   local->override_library,
                                   RNA_OVERRIDE_COMPARE_IGNORE_NON_OVERRIDABLE |
                                       RNA_OVERRIDE_COMPARE_IGNORE_OVERRIDDEN,
                                   NULL)) {
    local->tag &= ~LIB_TAG_OVERRIDE_LIBRARY_REFOK;
    return false;
  }

  return true;
}

/**
 * Check that status of reference data-block is still valid against current local one.
 *
 * It means that all non-overridden properties' local values must be equal to reference ones.
 * Clears LIB_TAG_OVERRIDE_OK if they do not.
 *
 * This is typically used to detect whether some reference has changed and local
 * needs to be updated against it.
 *
 * \return true if status is OK, false otherwise. */
bool BKE_lib_override_library_status_check_reference(Main *bmain, ID *local)
{
  BLI_assert(local->override_library != NULL);

  ID *reference = local->override_library->reference;

  if (reference == NULL) {
    /* This is an override template, reference is virtual, so its status is always OK! */
    return true;
  }

  BLI_assert(GS(local->name) == GS(reference->name));

  if (reference->override_library && (reference->tag & LIB_TAG_OVERRIDE_LIBRARY_REFOK) == 0) {
    if (!BKE_lib_override_library_status_check_reference(bmain, reference)) {
      /* If reference is also override of another data-block, and its status is not OK,
       * then this override is not OK either.
       * Note that this should only happen when reloading libraries... */
      local->tag &= ~LIB_TAG_OVERRIDE_LIBRARY_REFOK;
      return false;
    }
  }

  if (GS(local->name) == ID_OB) {
    /* Our beloved pose's bone cross-data pointers... Usually, depsgraph evaluation would ensure
     * this is valid, but in some cases (like hidden collections etc.) this won't be the case, so
     * we need to take care of this ourselves. */
    Object *ob_local = (Object *)local;
    if (ob_local->data != NULL && ob_local->type == OB_ARMATURE && ob_local->pose != NULL &&
        ob_local->pose->flag & POSE_RECALC) {
      BKE_pose_rebuild(bmain, ob_local, ob_local->data, true);
    }
  }

  PointerRNA rnaptr_local, rnaptr_reference;
  RNA_id_pointer_create(local, &rnaptr_local);
  RNA_id_pointer_create(reference, &rnaptr_reference);

  if (!RNA_struct_override_matches(bmain,
                                   &rnaptr_local,
                                   &rnaptr_reference,
                                   NULL,
                                   0,
                                   local->override_library,
                                   RNA_OVERRIDE_COMPARE_IGNORE_OVERRIDDEN,
                                   NULL)) {
    local->tag &= ~LIB_TAG_OVERRIDE_LIBRARY_REFOK;
    return false;
  }

  return true;
}

/**
 * Compares local and reference data-blocks and create new override operations as needed,
 * or reset to reference values if overriding is not allowed.
 *
 * \note Defining override operations is only mandatory before saving a `.blend` file on disk
 * (not for undo!).
 * Knowing that info at runtime is only useful for UI/UX feedback.
 *
 * \note This is by far the biggest operation (the more time-consuming) of the three so far,
 * since it has to go over all properties in depth (all overridable ones at least).
 * Generating diff values and applying overrides are much cheaper.
 *
 * \return true if new overriding op was created, or some local data was reset. */
bool BKE_lib_override_library_operations_create(Main *bmain, ID *local)
{
  BLI_assert(local->override_library != NULL);
  const bool is_template = (local->override_library->reference == NULL);
  bool ret = false;

  if (!is_template) {
    /* Do not attempt to generate overriding rules from an empty place-holder generated by link
     * code when it cannot find to actual library/ID. Much better to keep the local datablock as
     * is in the file in that case, until broken lib is fixed. */
    if (ID_MISSING(local->override_library->reference)) {
      return ret;
    }

    if (GS(local->name) == ID_OB) {
      /* Our beloved pose's bone cross-data pointers... Usually, depsgraph evaluation would ensure
       * this is valid, but in some situations (like hidden collections etc.) this won't be the
       * case, so we need to take care of this ourselves. */
      Object *ob_local = (Object *)local;
      if (ob_local->data != NULL && ob_local->type == OB_ARMATURE && ob_local->pose != NULL &&
          ob_local->pose->flag & POSE_RECALC) {
        BKE_pose_rebuild(bmain, ob_local, ob_local->data, true);
      }
    }

    PointerRNA rnaptr_local, rnaptr_reference;
    RNA_id_pointer_create(local, &rnaptr_local);
    RNA_id_pointer_create(local->override_library->reference, &rnaptr_reference);

    eRNAOverrideMatchResult report_flags = 0;
    RNA_struct_override_matches(bmain,
                                &rnaptr_local,
                                &rnaptr_reference,
                                NULL,
                                0,
                                local->override_library,
                                RNA_OVERRIDE_COMPARE_CREATE | RNA_OVERRIDE_COMPARE_RESTORE,
                                &report_flags);
    if (report_flags & RNA_OVERRIDE_MATCH_RESULT_CREATED) {
      ret = true;
    }
#ifndef NDEBUG
    if (report_flags & RNA_OVERRIDE_MATCH_RESULT_RESTORED) {
      printf("We did restore some properties of %s from its reference.\n", local->name);
    }
    if (ret) {
      printf("We did generate library override rules for %s\n", local->name);
    }
    else {
      printf("No new library override rules for %s\n", local->name);
    }
#endif
  }
  return ret;
}

static void lib_override_library_operations_create_cb(TaskPool *__restrict pool, void *taskdata)
{
  Main *bmain = BLI_task_pool_user_data(pool);
  ID *id = taskdata;

  BKE_lib_override_library_operations_create(bmain, id);
}

/** Check all overrides from given \a bmain and create/update overriding operations as needed. */
void BKE_lib_override_library_main_operations_create(Main *bmain, const bool force_auto)
{
  ID *id;

#ifdef DEBUG_OVERRIDE_TIMEIT
  TIMEIT_START_AVERAGED(BKE_lib_override_library_main_operations_create);
#endif

  /* When force-auto is set, we also remove all unused existing override properties & operations.
   */
  if (force_auto) {
    BKE_lib_override_library_main_tag(bmain, IDOVERRIDE_LIBRARY_TAG_UNUSED, true);
  }

  TaskPool *task_pool = BLI_task_pool_create(bmain, TASK_PRIORITY_HIGH);

  FOREACH_MAIN_ID_BEGIN (bmain, id) {
    if ((ID_IS_OVERRIDE_LIBRARY(id) && force_auto) ||
        (id->tag & LIB_TAG_OVERRIDE_LIBRARY_AUTOREFRESH)) {
      BLI_task_pool_push(task_pool, lib_override_library_operations_create_cb, id, false, NULL);
      id->tag &= ~LIB_TAG_OVERRIDE_LIBRARY_AUTOREFRESH;
    }
  }
  FOREACH_MAIN_ID_END;

  BLI_task_pool_work_and_wait(task_pool);

  BLI_task_pool_free(task_pool);

  if (force_auto) {
    BKE_lib_override_library_main_unused_cleanup(bmain);
  }

#ifdef DEBUG_OVERRIDE_TIMEIT
  TIMEIT_END_AVERAGED(BKE_lib_override_library_main_operations_create);
#endif
}

/** Set or clear given tag in all operations as unused in that override property data. */
void BKE_lib_override_library_operations_tag(struct IDOverrideLibraryProperty *override_property,
                                             const short tag,
                                             const bool do_set)
{
  if (override_property != NULL) {
    if (do_set) {
      override_property->tag |= tag;
    }
    else {
      override_property->tag &= ~tag;
    }

    LISTBASE_FOREACH (IDOverrideLibraryPropertyOperation *, opop, &override_property->operations) {
      if (do_set) {
        opop->tag |= tag;
      }
      else {
        opop->tag &= ~tag;
      }
    }
  }
}

/** Set or clear given tag in all properties and operations in that override data. */
void BKE_lib_override_library_properties_tag(struct IDOverrideLibrary *override,
                                             const short tag,
                                             const bool do_set)
{
  if (override != NULL) {
    LISTBASE_FOREACH (IDOverrideLibraryProperty *, op, &override->properties) {
      BKE_lib_override_library_operations_tag(op, tag, do_set);
    }
  }
}

/** Set or clear given tag in all properties and operations in that Main's ID override data. */
void BKE_lib_override_library_main_tag(struct Main *bmain, const short tag, const bool do_set)
{
  ID *id;

  FOREACH_MAIN_ID_BEGIN (bmain, id) {
    if (ID_IS_OVERRIDE_LIBRARY(id)) {
      BKE_lib_override_library_properties_tag(id->override_library, tag, do_set);
    }
  }
  FOREACH_MAIN_ID_END;
}

/** Remove all tagged-as-unused properties and operations from that ID override data. */
void BKE_lib_override_library_id_unused_cleanup(struct ID *local)
{
  if (local->override_library != NULL) {
    LISTBASE_FOREACH_MUTABLE (
        IDOverrideLibraryProperty *, op, &local->override_library->properties) {
      if (op->tag & IDOVERRIDE_LIBRARY_TAG_UNUSED) {
        BKE_lib_override_library_property_delete(local->override_library, op);
      }
      else {
        LISTBASE_FOREACH_MUTABLE (IDOverrideLibraryPropertyOperation *, opop, &op->operations) {
          if (opop->tag & IDOVERRIDE_LIBRARY_TAG_UNUSED) {
            BKE_lib_override_library_property_operation_delete(op, opop);
          }
        }
      }
    }
  }
}

/** Remove all tagged-as-unused properties and operations from that Main's ID override data. */
void BKE_lib_override_library_main_unused_cleanup(struct Main *bmain)
{
  ID *id;

  FOREACH_MAIN_ID_BEGIN (bmain, id) {
    if (ID_IS_OVERRIDE_LIBRARY(id)) {
      BKE_lib_override_library_id_unused_cleanup(id);
    }
  }
  FOREACH_MAIN_ID_END;
}

/** Update given override from its reference (re-applying overridden properties). */
void BKE_lib_override_library_update(Main *bmain, ID *local)
{
  if (local->override_library == NULL || local->override_library->reference == NULL) {
    return;
  }

  /* Do not attempt to apply overriding rules over an empty place-holder generated by link code
   * when it cannot find to actual library/ID. Much better to keep the local datablock as loaded
   * from the file in that case, until broken lib is fixed. */
  if (ID_MISSING(local->override_library->reference)) {
    return;
  }

  /* Recursively do 'ancestors' overrides first, if any. */
  if (local->override_library->reference->override_library &&
      (local->override_library->reference->tag & LIB_TAG_OVERRIDE_LIBRARY_REFOK) == 0) {
    BKE_lib_override_library_update(bmain, local->override_library->reference);
  }

  /* We want to avoid having to remap here, however creating up-to-date override is much simpler
   * if based on reference than on current override.
   * So we work on temp copy of reference, and 'swap' its content with local. */

  /* XXX We need a way to get off-Main copies of IDs (similar to localized mats/texts/ etc.)!
   *     However, this is whole bunch of code work in itself, so for now plain stupid ID copy will
   *     do, as inn-efficient as it is. :/
   *     Actually, maybe not! Since we are swapping with original ID's local content, we want to
   *     keep user-count in correct state when freeing tmp_id
   *     (and that user-counts of IDs used by 'new' local data also remain correct). */
  /* This would imply change in handling of user-count all over RNA
   * (and possibly all over Blender code).
   * Not impossible to do, but would rather see first if extra useless usual user handling
   * is actually a (performances) issue here. */

  ID *tmp_id;
  BKE_id_copy(bmain, local->override_library->reference, &tmp_id);

  if (tmp_id == NULL) {
    return;
  }

  /* This ID name is problematic, since it is an 'rna name property' it should not be editable or
   * different from reference linked ID. But local ID names need to be unique in a given type list
   * of Main, so we cannot always keep it identical, which is why we need this special manual
   * handling here. */
  BLI_strncpy(tmp_id->name, local->name, sizeof(tmp_id->name));

  PointerRNA rnaptr_src, rnaptr_dst, rnaptr_storage_stack, *rnaptr_storage = NULL;
  RNA_id_pointer_create(local, &rnaptr_src);
  RNA_id_pointer_create(tmp_id, &rnaptr_dst);
  if (local->override_library->storage) {
    rnaptr_storage = &rnaptr_storage_stack;
    RNA_id_pointer_create(local->override_library->storage, rnaptr_storage);
  }

  RNA_struct_override_apply(
      bmain, &rnaptr_dst, &rnaptr_src, rnaptr_storage, local->override_library);

  /* This also transfers all pointers (memory) owned by local to tmp_id, and vice-versa.
   * So when we'll free tmp_id, we'll actually free old, outdated data from local. */
  BKE_lib_id_swap(bmain, local, tmp_id);

  /* Again, horribly inn-efficient in our case, we need something off-Main
   * (aka more generic nolib copy/free stuff)! */
  /* XXX And crashing in complex cases (e.g. because depsgraph uses same data...). */
  BKE_id_free_ex(bmain, tmp_id, LIB_ID_FREE_NO_UI_USER, true);

  if (local->override_library->storage) {
    /* We know this datablock is not used anywhere besides local->override->storage. */
    /* XXX For until we get fully shadow copies, we still need to ensure storage releases
     *     its usage of any ID pointers it may have. */
    BKE_id_free_ex(bmain, local->override_library->storage, LIB_ID_FREE_NO_UI_USER, true);
    local->override_library->storage = NULL;
  }

  local->tag |= LIB_TAG_OVERRIDE_LIBRARY_REFOK;

  /* Full rebuild of Depsgraph! */

  /* XXX Is this actual valid replacement for old DAG_relations_tag_update(bmain) ? */
  DEG_on_visible_update(bmain, true);
}

/** Update all overrides from given \a bmain. */
void BKE_lib_override_library_main_update(Main *bmain)
{
  ID *id;

  FOREACH_MAIN_ID_BEGIN (bmain, id) {
    if (id->override_library != NULL && id->lib == NULL) {
      BKE_lib_override_library_update(bmain, id);
    }
  }
  FOREACH_MAIN_ID_END;
}

/**
 * Storage (how to store overriding data into `.blend` files).
 *
 * Basically:
 * 1) Only 'differential' storage needs special handling here. All others (replacing values or
 *    inserting/removing items from a collection) can be handled with simply storing current
 *    content of local data-block.
 * 2) We store the differential value into a second 'ghost' data-block,
 *    which is an empty ID of same type as local one,
 *    where we only define values that need differential data.
 *
 * This avoids us having to modify 'real' data-block at write time (and restoring it afterwards),
 * which is inefficient, and potentially dangerous (in case of concurrent access...), while not
 * using much extra memory in typical cases.  It also ensures stored data-block always contains
 * exact same data as "desired" ones (kind of "baked" data-blocks).
 */

/** Initialize an override storage. */
OverrideLibraryStorage *BKE_lib_override_library_operations_store_initialize(void)
{
  return BKE_main_new();
}

/**
 * Generate suitable 'write' data (this only affects differential override operations).
 *
 * Note that \a local ID is no more modified by this call,
 * all extra data are stored in its temp \a storage_id copy. */
ID *BKE_lib_override_library_operations_store_start(Main *bmain,
                                                    OverrideLibraryStorage *override_storage,
                                                    ID *local)
{
  BLI_assert(local->override_library != NULL);
  BLI_assert(override_storage != NULL);
  const bool is_template = (local->override_library->reference == NULL);

  if (is_template) {
    /* This is actually purely local data with an override template, nothing to do here! */
    return NULL;
  }

  /* Forcefully ensure we know about all needed override operations. */
  BKE_lib_override_library_operations_create(bmain, local);

  ID *storage_id;
#ifdef DEBUG_OVERRIDE_TIMEIT
  TIMEIT_START_AVERAGED(BKE_lib_override_library_operations_store_start);
#endif

  /* XXX TODO We may also want a specialized handling of things here too, to avoid copying heavy
   * never-overridable data (like Mesh geometry etc.)? And also maybe avoid lib reference-counting
   * completely (shallow copy...). */
  /* This would imply change in handling of user-count all over RNA
   * (and possibly all over Blender code).
   * Not impossible to do, but would rather see first is extra useless usual user handling is
   * actually a (performances) issue here, before doing it. */
  BKE_id_copy((Main *)override_storage, local, &storage_id);

  if (storage_id != NULL) {
    PointerRNA rnaptr_reference, rnaptr_final, rnaptr_storage;
    RNA_id_pointer_create(local->override_library->reference, &rnaptr_reference);
    RNA_id_pointer_create(local, &rnaptr_final);
    RNA_id_pointer_create(storage_id, &rnaptr_storage);

    if (!RNA_struct_override_store(
            bmain, &rnaptr_final, &rnaptr_reference, &rnaptr_storage, local->override_library)) {
      BKE_id_free_ex(override_storage, storage_id, LIB_ID_FREE_NO_UI_USER, true);
      storage_id = NULL;
    }
  }

  local->override_library->storage = storage_id;

#ifdef DEBUG_OVERRIDE_TIMEIT
  TIMEIT_END_AVERAGED(BKE_lib_override_library_operations_store_start);
#endif
  return storage_id;
}

/** Restore given ID modified by \a BKE_lib_override_library_operations_store_start, to its
 * original state. */
void BKE_lib_override_library_operations_store_end(
    OverrideLibraryStorage *UNUSED(override_storage), ID *local)
{
  BLI_assert(local->override_library != NULL);

  /* Nothing else to do here really, we need to keep all temp override storage data-blocks in
   * memory until whole file is written anyway (otherwise we'd get mem pointers overlap...). */
  local->override_library->storage = NULL;
}

void BKE_lib_override_library_operations_store_finalize(OverrideLibraryStorage *override_storage)
{
  /* We cannot just call BKE_main_free(override_storage), not until we have option to make 'ghost'
   * copies of IDs without increasing usercount of used data-blocks. */
  ID *id;

  FOREACH_MAIN_ID_BEGIN (override_storage, id) {
    BKE_id_free_ex(override_storage, id, LIB_ID_FREE_NO_UI_USER, true);
  }
  FOREACH_MAIN_ID_END;

  BKE_main_free(override_storage);
}
