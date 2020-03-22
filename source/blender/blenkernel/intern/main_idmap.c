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

#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "BLI_ghash.h"
#include "BLI_listbase.h"
#include "BLI_utildefines.h"

#include "DNA_ID.h"

#include "BKE_idtype.h"
#include "BKE_lib_id.h"
#include "BKE_main.h"
#include "BKE_main_idmap.h" /* own include */

/** \file
 * \ingroup bke
 *
 * Utility functions for faster ID lookups.
 */

/** \name BKE_main_idmap API
 *
 * Cache ID (name, library lookups).
 * This doesn't account for adding/removing data-blocks,
 * and should only be used when performing many lookups.
 *
 * \note GHash's are initialized on demand,
 * since its likely some types will never have lookups run on them,
 * so its a waste to create and never use.
 * \{ */

struct IDNameLib_Key {
  /** ``ID.name + 2``: without the ID type prefix, since each id type gets it's own 'map' */
  const char *name;
  /** ``ID.lib``: */
  const Library *lib;
};

struct IDNameLib_TypeMap {
  GHash *map;
  short id_type;
  /* only for storage of keys in the ghash, avoid many single allocs */
  struct IDNameLib_Key *keys;
};

/**
 * Opaque structure, external API users only see this.
 */
struct IDNameLib_Map {
  struct IDNameLib_TypeMap type_maps[MAX_LIBARRAY];
  struct GHash *uuid_map;
  struct Main *bmain;
  struct GSet *valid_id_pointers;
  int idmap_types;
};

static struct IDNameLib_TypeMap *main_idmap_from_idcode(struct IDNameLib_Map *id_map,
                                                        short id_type)
{
  if (id_map->idmap_types & MAIN_IDMAP_TYPE_NAME) {
    for (int i = 0; i < MAX_LIBARRAY; i++) {
      if (id_map->type_maps[i].id_type == id_type) {
        return &id_map->type_maps[i];
      }
    }
  }
  return NULL;
}

/**
 * Generate mapping from ID type/name to ID pointer for given \a bmain.
 *
 * \note When used during undo/redo, there is no guaranty that ID pointers from UI area
 *       are not pointing to freed memory (when some IDs have been deleted). To avoid crashes
 *       in those cases, one can provide the 'old' (aka current) Main database as reference.
 *       #BKE_main_idmap_lookup_id will then check that given ID does exist in \a old_bmain
 *       before trying to use it.
 *
 * \param create_valid_ids_set: If \a true, generate a reference to prevent freed memory accesses.
 * \param old_bmain: If not NULL, its IDs will be added the valid references set.
 */
struct IDNameLib_Map *BKE_main_idmap_create(struct Main *bmain,
                                            const bool create_valid_ids_set,
                                            struct Main *old_bmain,
                                            const int idmap_types)
{
  struct IDNameLib_Map *id_map = MEM_mallocN(sizeof(*id_map), __func__);
  id_map->bmain = bmain;
  id_map->idmap_types = idmap_types;

  int index = 0;
  while (index < MAX_LIBARRAY) {
    struct IDNameLib_TypeMap *type_map = &id_map->type_maps[index];
    type_map->map = NULL;
    type_map->id_type = BKE_idtype_idcode_iter_step(&index);
    BLI_assert(type_map->id_type != 0);
  }
  BLI_assert(index == MAX_LIBARRAY);

  if (idmap_types & MAIN_IDMAP_TYPE_UUID) {
    ID *id;
    id_map->uuid_map = BLI_ghash_int_new(__func__);
    FOREACH_MAIN_ID_BEGIN (bmain, id) {
      BLI_assert(id->session_uuid != MAIN_ID_SESSION_UUID_UNSET);
      void **id_ptr_v;
      const bool existing_key = BLI_ghash_ensure_p(
          id_map->uuid_map, POINTER_FROM_UINT(id->session_uuid), &id_ptr_v);
      BLI_assert(existing_key == false);
      UNUSED_VARS_NDEBUG(existing_key);

      *id_ptr_v = id;
    }
    FOREACH_MAIN_ID_END;
  }
  else {
    id_map->uuid_map = NULL;
  }

  if (create_valid_ids_set) {
    id_map->valid_id_pointers = BKE_main_gset_create(bmain, NULL);
    if (old_bmain != NULL) {
      id_map->valid_id_pointers = BKE_main_gset_create(old_bmain, id_map->valid_id_pointers);
    }
  }
  else {
    id_map->valid_id_pointers = NULL;
  }

  return id_map;
}

struct Main *BKE_main_idmap_main_get(struct IDNameLib_Map *id_map)
{
  return id_map->bmain;
}

static unsigned int idkey_hash(const void *ptr)
{
  const struct IDNameLib_Key *idkey = ptr;
  unsigned int key = BLI_ghashutil_strhash(idkey->name);
  if (idkey->lib) {
    key ^= BLI_ghashutil_ptrhash(idkey->lib);
  }
  return key;
}

static bool idkey_cmp(const void *a, const void *b)
{
  const struct IDNameLib_Key *idkey_a = a;
  const struct IDNameLib_Key *idkey_b = b;
  return strcmp(idkey_a->name, idkey_b->name) || (idkey_a->lib != idkey_b->lib);
}

ID *BKE_main_idmap_lookup_name(struct IDNameLib_Map *id_map,
                               short id_type,
                               const char *name,
                               const Library *lib)
{
  struct IDNameLib_TypeMap *type_map = main_idmap_from_idcode(id_map, id_type);

  if (UNLIKELY(type_map == NULL)) {
    return NULL;
  }

  /* lazy init */
  if (type_map->map == NULL) {
    ListBase *lb = which_libbase(id_map->bmain, id_type);
    const int lb_len = BLI_listbase_count(lb);
    if (lb_len == 0) {
      return NULL;
    }
    type_map->map = BLI_ghash_new_ex(idkey_hash, idkey_cmp, __func__, lb_len);
    type_map->keys = MEM_mallocN(sizeof(struct IDNameLib_Key) * lb_len, __func__);

    GHash *map = type_map->map;
    struct IDNameLib_Key *key = type_map->keys;

    for (ID *id = lb->first; id; id = id->next, key++) {
      key->name = id->name + 2;
      key->lib = id->lib;
      BLI_ghash_insert(map, key, id);
    }
  }

  const struct IDNameLib_Key key_lookup = {name, lib};
  return BLI_ghash_lookup(type_map->map, &key_lookup);
}

ID *BKE_main_idmap_lookup_id(struct IDNameLib_Map *id_map, const ID *id)
{
  /* When used during undo/redo, this function cannot assume that given id points to valid memory
   * (i.e. has not been freed),
   * so it has to check that it does exist in 'old' (aka current) Main database.
   * Otherwise, we cannot provide new ID pointer that way (would crash accessing freed memory
   * when trying to get ID name).
   */
  if (id_map->valid_id_pointers == NULL || BLI_gset_haskey(id_map->valid_id_pointers, id)) {
    return BKE_main_idmap_lookup_name(id_map, GS(id->name), id->name + 2, id->lib);
  }
  return NULL;
}

ID *BKE_main_idmap_lookup_uuid(struct IDNameLib_Map *id_map, const uint session_uuid)
{
  if (id_map->idmap_types & MAIN_IDMAP_TYPE_UUID) {
    return BLI_ghash_lookup(id_map->uuid_map, POINTER_FROM_UINT(session_uuid));
  }
  return NULL;
}

void BKE_main_idmap_destroy(struct IDNameLib_Map *id_map)
{
  if (id_map->idmap_types & MAIN_IDMAP_TYPE_NAME) {
    struct IDNameLib_TypeMap *type_map = id_map->type_maps;
    for (int i = 0; i < MAX_LIBARRAY; i++, type_map++) {
      if (type_map->map) {
        BLI_ghash_free(type_map->map, NULL, NULL);
        type_map->map = NULL;
        MEM_freeN(type_map->keys);
      }
    }
  }
  if (id_map->idmap_types & MAIN_IDMAP_TYPE_UUID) {
    BLI_ghash_free(id_map->uuid_map, NULL, NULL);
  }

  if (id_map->valid_id_pointers != NULL) {
    BLI_gset_free(id_map->valid_id_pointers, NULL);
  }

  MEM_freeN(id_map);
}

/** \} */
