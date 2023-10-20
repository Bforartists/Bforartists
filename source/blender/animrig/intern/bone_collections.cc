/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup animrig
 */

#include "BLI_linklist.h"
#include "BLI_listbase.h"
#include "BLI_map.hh"
#include "BLI_math_color.h"
#include "BLI_string.h"
#include "BLI_string_utf8.h"
#include "BLI_string_utils.hh"
#include "BLI_utildefines.h"

#include "BLT_translation.h"

#include "DNA_armature_types.h"

#include "BLI_math_bits.h"

#include "MEM_guardedalloc.h"

#include "BKE_animsys.h"
#include "BKE_idprop.h"
#include "BKE_lib_id.h"

#include "ANIM_armature_iter.hh"
#include "ANIM_bone_collections.hh"

#include <cstring>
#include <string>

using std::strcmp;

using namespace blender::animrig;

namespace {

/** Default flags for new bone collections. */
constexpr eBoneCollection_Flag default_flags = BONE_COLLECTION_VISIBLE |
                                               BONE_COLLECTION_SELECTABLE;
constexpr auto bonecoll_default_name = "Bones";
}  // namespace

BoneCollection *ANIM_bonecoll_new(const char *name)
{
  if (name == nullptr || name[0] == '\0') {
    /* Use a default name if no name was given. */
    name = DATA_(bonecoll_default_name);
  }

  /* Note: the collection name may change after the collection is added to an
   * armature, to ensure it is unique within the armature. */
  BoneCollection *bcoll = MEM_cnew<BoneCollection>(__func__);

  STRNCPY_UTF8(bcoll->name, name);
  bcoll->flags = default_flags;

  bcoll->prop = nullptr;

  return bcoll;
}

void ANIM_bonecoll_free(BoneCollection *bcoll)
{
  BLI_assert_msg(BLI_listbase_is_empty(&bcoll->bones),
                 "bone collection still has bones assigned to it, will cause dangling pointers in "
                 "bone runtime data");
  if (bcoll->prop) {
    IDP_FreeProperty(bcoll->prop);
  }
  MEM_delete(bcoll);
}

/**
 * Construct the mapping from the bones to this collection.
 *
 * This assumes that the bones do not have such a pointer yet, i.e. calling this
 * twice for the same bone collection will cause duplicate pointers. */
static void add_reverse_pointers(BoneCollection *bcoll)
{
  LISTBASE_FOREACH (BoneCollectionMember *, member, &bcoll->bones) {
    BoneCollectionReference *ref = MEM_cnew<BoneCollectionReference>(__func__);
    ref->bcoll = bcoll;
    BLI_addtail(&member->bone->runtime.collections, ref);
  }
}

void ANIM_armature_runtime_refresh(bArmature *armature)
{
  ANIM_armature_runtime_free(armature);

  BoneCollection *active = ANIM_armature_bonecoll_get_by_name(armature,
                                                              armature->active_collection_name);
  ANIM_armature_bonecoll_active_set(armature, active);

  /* Construct the bone-to-collections mapping. */
  LISTBASE_FOREACH (BoneCollection *, bcoll, &armature->collections) {
    add_reverse_pointers(bcoll);
  }
}

void ANIM_armature_runtime_free(bArmature *armature)
{
  /* Free the bone-to-its-collections mapping. */
  ANIM_armature_foreach_bone(&armature->bonebase,
                             [&](Bone *bone) { BLI_freelistN(&bone->runtime.collections); });
}

static void bonecoll_ensure_name_unique(bArmature *armature, BoneCollection *bcoll)
{
  BLI_uniquename(&armature->collections,
                 bcoll,
                 DATA_(bonecoll_default_name),
                 '.',
                 offsetof(BoneCollection, name),
                 sizeof(bcoll->name));
}

BoneCollection *ANIM_armature_bonecoll_new(bArmature *armature, const char *name)
{
  BoneCollection *bcoll = ANIM_bonecoll_new(name);

  if (!ID_IS_LINKED(&armature->id) && ID_IS_OVERRIDE_LIBRARY(&armature->id)) {
    /* Mark this bone collection as local override, so that certain operations can be allowed. */
    bcoll->flags |= BONE_COLLECTION_OVERRIDE_LIBRARY_LOCAL;
  }

  bonecoll_ensure_name_unique(armature, bcoll);
  BLI_addtail(&armature->collections, bcoll);
  return bcoll;
}

BoneCollection *ANIM_armature_bonecoll_insert_copy_after(bArmature *armature,
                                                         BoneCollection *anchor,
                                                         const BoneCollection *bcoll_to_copy)
{
  BoneCollection *bcoll = static_cast<BoneCollection *>(MEM_dupallocN(bcoll_to_copy));

  /* Remap the bone pointers to the given armature, as `bcoll_to_copy` will
   * likely be owned by another copy of the armature. */
  BLI_duplicatelist(&bcoll->bones, &bcoll->bones);
  BLI_assert_msg(armature->bonehash, "Expected armature bone hash to be there");
  LISTBASE_FOREACH (BoneCollectionMember *, member, &bcoll->bones) {
    member->bone = BKE_armature_find_bone_name(armature, member->bone->name);
  }

  if (bcoll_to_copy->prop) {
    bcoll->prop = IDP_CopyProperty_ex(bcoll_to_copy->prop,
                                      0 /*do_id_user ? 0 : LIB_ID_CREATE_NO_USER_REFCOUNT*/);
  }

  BLI_insertlinkafter(&armature->collections, anchor, bcoll);
  bonecoll_ensure_name_unique(armature, bcoll);
  add_reverse_pointers(bcoll);

  return bcoll;
}

static void armature_bonecoll_active_clear(bArmature *armature)
{
  armature->runtime.active_collection_index = -1;
  armature->runtime.active_collection = nullptr;
  armature->active_collection_name[0] = '\0';
}

void ANIM_armature_bonecoll_active_set(bArmature *armature, BoneCollection *bcoll)
{
  if (bcoll == nullptr) {
    armature_bonecoll_active_clear(armature);
    return;
  }

  const int index = BLI_findindex(&armature->collections, bcoll);
  if (index == -1) {
    /* TODO: print warning? Or just ignore this case? */
    armature_bonecoll_active_clear(armature);
    return;
  }

  STRNCPY(armature->active_collection_name, bcoll->name);
  armature->runtime.active_collection_index = index;
  armature->runtime.active_collection = bcoll;
}

void ANIM_armature_bonecoll_active_index_set(bArmature *armature, const int bone_collection_index)
{
  if (bone_collection_index < 0) {
    armature_bonecoll_active_clear(armature);
    return;
  }

  void *found_link = BLI_findlink(&armature->collections, bone_collection_index);
  BoneCollection *bcoll = static_cast<BoneCollection *>(found_link);
  if (bcoll == nullptr) {
    /* TODO: print warning? Or just ignore this case? */
    armature_bonecoll_active_clear(armature);
    return;
  }

  STRNCPY(armature->active_collection_name, bcoll->name);
  armature->runtime.active_collection_index = bone_collection_index;
  armature->runtime.active_collection = bcoll;
}

void ANIM_armature_bonecoll_active_name_set(bArmature *armature, const char *name)
{
  BoneCollection *bcoll = ANIM_armature_bonecoll_get_by_name(armature, name);
  ANIM_armature_bonecoll_active_set(armature, bcoll);
}

bool ANIM_armature_bonecoll_is_editable(const bArmature *armature, const BoneCollection *bcoll)
{
  const bool is_override = ID_IS_OVERRIDE_LIBRARY(armature);
  if (ID_IS_LINKED(armature) && !is_override) {
    return false;
  }
  if (is_override && (bcoll->flags & BONE_COLLECTION_OVERRIDE_LIBRARY_LOCAL) == 0) {
    return false;
  }
  return true;
}

bool ANIM_armature_bonecoll_move(bArmature *armature, BoneCollection *bcoll, const int step)
{
  if (bcoll == nullptr) {
    return false;
  }

  if (!BLI_listbase_link_move(&armature->collections, bcoll, step)) {
    return false;
  }

  if (bcoll == armature->runtime.active_collection) {
    armature->runtime.active_collection_index = BLI_findindex(&armature->collections, bcoll);
  }
  return true;
}

void ANIM_armature_bonecoll_name_set(bArmature *armature, BoneCollection *bcoll, const char *name)
{
  char old_name[sizeof(bcoll->name)];

  STRNCPY(old_name, bcoll->name);

  if (name[0] == '\0') {
    /* Refuse to have nameless collections. The name of the active collection is stored in DNA, and
     * an empty string means 'no active collection'. */
    STRNCPY(bcoll->name, DATA_(bonecoll_default_name));
  }
  else {
    STRNCPY_UTF8(bcoll->name, name);
  }

  bonecoll_ensure_name_unique(armature, bcoll);

  BKE_animdata_fix_paths_rename_all(&armature->id, "collections", old_name, bcoll->name);
}

void ANIM_armature_bonecoll_remove(bArmature *armature, BoneCollection *bcoll)
{
  LISTBASE_FOREACH_MUTABLE (BoneCollectionMember *, member, &bcoll->bones) {
    ANIM_armature_bonecoll_unassign(bcoll, member->bone);
  }
  if (armature->edbo) {
    LISTBASE_FOREACH (EditBone *, ebone, armature->edbo) {
      ANIM_armature_bonecoll_unassign_editbone(bcoll, ebone);
    }
  }

  BLI_remlink_safe(&armature->collections, bcoll);
  ANIM_bonecoll_free(bcoll);

  /* Make sure the active collection is correct. */
  const int num_collections = BLI_listbase_count(&armature->collections);
  const int active_index = min_ii(armature->runtime.active_collection_index, num_collections - 1);
  ANIM_armature_bonecoll_active_index_set(armature, active_index);
}

BoneCollection *ANIM_armature_bonecoll_get_by_name(bArmature *armature, const char *name)
{
  LISTBASE_FOREACH (BoneCollection *, bcoll, &armature->collections) {
    if (STREQ(bcoll->name, name)) {
      return bcoll;
    }
  }
  return nullptr;
}

void ANIM_bonecoll_show(BoneCollection *bcoll)
{
  bcoll->flags |= BONE_COLLECTION_VISIBLE;
}

void ANIM_bonecoll_hide(BoneCollection *bcoll)
{
  bcoll->flags &= ~BONE_COLLECTION_VISIBLE;
}

/* Store the bone's membership on the collection. */
static void add_membership(BoneCollection *bcoll, Bone *bone)
{
  BoneCollectionMember *member = MEM_cnew<BoneCollectionMember>(__func__);
  member->bone = bone;
  BLI_addtail(&bcoll->bones, member);
}
/* Store reverse membership on the bone. */
static void add_reference(Bone *bone, BoneCollection *bcoll)
{
  BoneCollectionReference *ref = MEM_cnew<BoneCollectionReference>(__func__);
  ref->bcoll = bcoll;
  BLI_addtail(&bone->runtime.collections, ref);
}

bool ANIM_armature_bonecoll_assign(BoneCollection *bcoll, Bone *bone)
{
  /* Precondition check: bail out if already a member. */
  LISTBASE_FOREACH (BoneCollectionMember *, member, &bcoll->bones) {
    if (member->bone == bone) {
      return false;
    }
  }

  add_membership(bcoll, bone);
  add_reference(bone, bcoll);

  return true;
}

bool ANIM_armature_bonecoll_assign_editbone(BoneCollection *bcoll, EditBone *ebone)
{
  /* Precondition check: bail out if already a member. */
  LISTBASE_FOREACH (BoneCollectionReference *, ref, &ebone->bone_collections) {
    if (ref->bcoll == bcoll) {
      return false;
    }
  }

  /* Store membership on the edit bone. Bones will be rebuilt when the armature
   * goes out of edit mode, and by then the newly created bones will be added to
   * the actual collection on the Armature. */
  BoneCollectionReference *ref = MEM_cnew<BoneCollectionReference>(__func__);
  ref->bcoll = bcoll;
  BLI_addtail(&ebone->bone_collections, ref);

  return true;
}

bool ANIM_armature_bonecoll_assign_and_move(BoneCollection *bcoll, Bone *bone)
{
  ANIM_armature_bonecoll_unassign_all(bone);
  return ANIM_armature_bonecoll_assign(bcoll, bone);
}

bool ANIM_armature_bonecoll_assign_and_move_editbone(BoneCollection *bcoll, EditBone *ebone)
{
  ANIM_armature_bonecoll_unassign_all_editbone(ebone);
  return ANIM_armature_bonecoll_assign_editbone(bcoll, ebone);
}

bool ANIM_armature_bonecoll_unassign(BoneCollection *bcoll, Bone *bone)
{
  bool was_found = false;

  /* Remove membership from collection. */
  LISTBASE_FOREACH_MUTABLE (BoneCollectionMember *, member, &bcoll->bones) {
    if (member->bone == bone) {
      BLI_freelinkN(&bcoll->bones, member);
      was_found = true;
      break;
    }
  }

  /* Remove reverse membership from the bone.
   * For data consistency sake, this is always done, regardless of whether the
   * above loop found the membership. */
  LISTBASE_FOREACH_MUTABLE (BoneCollectionReference *, ref, &bone->runtime.collections) {
    if (ref->bcoll == bcoll) {
      BLI_freelinkN(&bone->runtime.collections, ref);
      break;
    }
  }

  return was_found;
}

void ANIM_armature_bonecoll_unassign_all(Bone *bone)
{
  LISTBASE_FOREACH_MUTABLE (BoneCollectionReference *, ref, &bone->runtime.collections) {
    /* TODO: include Armature as parameter, and check that the bone collection to unassign from is
     * actually editable. */
    ANIM_armature_bonecoll_unassign(ref->bcoll, bone);
  }
}

void ANIM_armature_bonecoll_unassign_all_editbone(EditBone *ebone)
{
  LISTBASE_FOREACH_MUTABLE (BoneCollectionReference *, ref, &ebone->bone_collections) {
    ANIM_armature_bonecoll_unassign_editbone(ref->bcoll, ebone);
  }
}

bool ANIM_armature_bonecoll_unassign_editbone(BoneCollection *bcoll, EditBone *ebone)
{
  bool was_found = false;

  /* Edit bone membership is only stored on the edit bone itself. */
  LISTBASE_FOREACH_MUTABLE (BoneCollectionReference *, ref, &ebone->bone_collections) {
    if (ref->bcoll == bcoll) {
      BLI_freelinkN(&ebone->bone_collections, ref);
      was_found = true;
      break;
    }
  }
  return was_found;
}

void ANIM_armature_bonecoll_reconstruct(bArmature *armature)
{
  /* Remove all the old collection memberships. */
  LISTBASE_FOREACH (BoneCollection *, bcoll, &armature->collections) {
    BLI_freelistN(&bcoll->bones);
  }

  /* For all bones, restore their collection memberships. */
  ANIM_armature_foreach_bone(&armature->bonebase, [&](Bone *bone) {
    LISTBASE_FOREACH (BoneCollectionReference *, ref, &bone->runtime.collections) {
      add_membership(ref->bcoll, bone);
    }
  });
}

static bool any_bone_collection_visible(const ListBase /*BoneCollectionRef*/ *collection_refs)
{
  /* Special case: when a bone is not in any collection, it is visible. */
  if (BLI_listbase_is_empty(collection_refs)) {
    return true;
  }

  LISTBASE_FOREACH (const BoneCollectionReference *, bcoll_ref, collection_refs) {
    const BoneCollection *bcoll = bcoll_ref->bcoll;
    if (bcoll->flags & BONE_COLLECTION_VISIBLE) {
      return true;
    }
  }
  return false;
}

/* TODO: these two functions were originally implemented for armature layers, hence the armature
 * parameters. These should be removed at some point. */

bool ANIM_bonecoll_is_visible(const bArmature * /*armature*/, const Bone *bone)
{
  return any_bone_collection_visible(&bone->runtime.collections);
}
bool ANIM_bonecoll_is_visible_editbone(const bArmature * /*armature*/, const EditBone *ebone)
{
  return any_bone_collection_visible(&ebone->bone_collections);
}

void ANIM_armature_bonecoll_show_all(bArmature *armature)
{
  LISTBASE_FOREACH (BoneCollection *, bcoll, &armature->collections) {
    ANIM_bonecoll_show(bcoll);
  }
}

void ANIM_armature_bonecoll_hide_all(bArmature *armature)
{
  LISTBASE_FOREACH (BoneCollection *, bcoll, &armature->collections) {
    ANIM_bonecoll_hide(bcoll);
  }
}

/* ********************************* */
/* Armature Layers transitional API. */

void ANIM_armature_bonecoll_assign_active(const bArmature *armature, EditBone *ebone)
{
  if (armature->runtime.active_collection == nullptr) {
    /* No active collection, do not assign to any. */
    printf("ANIM_armature_bonecoll_assign_active(%s, %s): no active collection\n",
           ebone->name,
           armature->id.name);
    return;
  }

  ANIM_armature_bonecoll_assign_editbone(armature->runtime.active_collection, ebone);
}

void ANIM_armature_bonecoll_show_from_bone(bArmature *armature, const Bone *bone)
{
  if (ANIM_bonecoll_is_visible(armature, bone)) {
    return;
  }

  /* Making the first collection visible is enough to make the bone visible.
   *
   * Since bones without collection are considered visible,
   * bone->runtime.collections.first is certainly a valid pointer. */
  BoneCollectionReference *ref = static_cast<BoneCollectionReference *>(
      bone->runtime.collections.first);
  ref->bcoll->flags |= BONE_COLLECTION_VISIBLE;
}

void ANIM_armature_bonecoll_show_from_ebone(bArmature *armature, const EditBone *ebone)
{
  if (ANIM_bonecoll_is_visible_editbone(armature, ebone)) {
    return;
  }

  /* Making the first collection visible is enough to make the bone visible.
   *
   * Since bones without collection are considered visible,
   * ebone->bone_collections.first is certainly a valid pointer. */
  BoneCollectionReference *ref = static_cast<BoneCollectionReference *>(
      ebone->bone_collections.first);
  ref->bcoll->flags |= BONE_COLLECTION_VISIBLE;
}

void ANIM_armature_bonecoll_show_from_pchan(bArmature *armature, const bPoseChannel *pchan)
{
  ANIM_armature_bonecoll_show_from_bone(armature, pchan->bone);
}

/* ********* */
/* C++ only. */
namespace blender::animrig {

/* Utility functions for Armature edit-mode undo. */

blender::Map<BoneCollection *, BoneCollection *> ANIM_bonecoll_listbase_copy_no_membership(
    ListBase *bone_colls_dst, ListBase *bone_colls_src, const bool do_id_user)
{
  BLI_assert(BLI_listbase_is_empty(bone_colls_dst));

  blender::Map<BoneCollection *, BoneCollection *> bcoll_map{};
  LISTBASE_FOREACH (BoneCollection *, bcoll_src, bone_colls_src) {
    BoneCollection *bcoll_dst = static_cast<BoneCollection *>(MEM_dupallocN(bcoll_src));

    /* This will be rebuilt from the edit bones, so we don't need to copy it. */
    BLI_listbase_clear(&bcoll_dst->bones);

    if (bcoll_src->prop) {
      bcoll_dst->prop = IDP_CopyProperty_ex(bcoll_src->prop,
                                            do_id_user ? 0 : LIB_ID_CREATE_NO_USER_REFCOUNT);
    }
    BLI_addtail(bone_colls_dst, bcoll_dst);
    bcoll_map.add(bcoll_src, bcoll_dst);
  }

  return bcoll_map;
}

void ANIM_bonecoll_listbase_free(ListBase *bcolls, const bool do_id_user)
{
  LISTBASE_FOREACH_MUTABLE (BoneCollection *, bcoll, bcolls) {
    if (bcoll->prop) {
      IDP_FreeProperty_ex(bcoll->prop, do_id_user);
    }

    /* This will usually already be empty, because the passed BoneCollection
     * list is usually from ANIM_bonecoll_listbase_copy_no_membership().
     * However, during undo this is also used to free the BoneCollection
     * list on the Armature itself before copying over the undo BoneCollection
     * list, in which case this of Bone pointers may not be empty. */
    BLI_freelistN(&bcoll->bones);
  }
  BLI_freelistN(bcolls);
}

}  // namespace blender::animrig
