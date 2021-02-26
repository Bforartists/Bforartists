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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 */

#pragma once

/** \file
 * \ingroup bke
 *
 * ID type structure, helping to factorize common operations and data for all data-block types.
 */

#include "BLI_sys_types.h"

#ifdef __cplusplus
extern "C" {
#endif

struct BlendDataReader;
struct BlendExpander;
struct BlendLibReader;
struct BlendWriter;
struct ID;
struct LibraryForeachIDData;
struct Main;

/** IDTypeInfo.flags. */
enum {
  /** Indicates that the given IDType does not support copying. */
  IDTYPE_FLAGS_NO_COPY = 1 << 0,
  /** Indicates that the given IDType does not support linking/appending from a library file. */
  IDTYPE_FLAGS_NO_LIBLINKING = 1 << 1,
  /** Indicates that the given IDType does not support making a library-linked ID local. */
  IDTYPE_FLAGS_NO_MAKELOCAL = 1 << 2,
  /** Indicates that the given IDType does not have animation data. */
  IDTYPE_FLAGS_NO_ANIMDATA = 1 << 3,
};

typedef struct IDCacheKey {
  /* The session UUID of the ID owning the cached data. */
  unsigned int id_session_uuid;
  /* Value uniquely identifying the cache within its ID.
   * Typically the offset of its member in the data-block struct, but can be anything. */
  size_t offset_in_ID;
  /* Actual address of the cached data to save and restore. */
  void *cache_v;
} IDCacheKey;

uint BKE_idtype_cache_key_hash(const void *key_v);
bool BKE_idtype_cache_key_cmp(const void *key_a_v, const void *key_b_v);

/* ********** Prototypes for #IDTypeInfo callbacks. ********** */

typedef void (*IDTypeInitDataFunction)(struct ID *id);

/** \param flag: Copying options (see BKE_lib_id.h's LIB_ID_COPY_... flags for more). */
typedef void (*IDTypeCopyDataFunction)(struct Main *bmain,
                                       struct ID *id_dst,
                                       const struct ID *id_src,
                                       const int flag);

typedef void (*IDTypeFreeDataFunction)(struct ID *id);

/** \param flag: See BKE_lib_id.h's LIB_ID_MAKELOCAL_... flags. */
typedef void (*IDTypeMakeLocalFunction)(struct Main *bmain, struct ID *id, const int flags);

typedef void (*IDTypeForeachIDFunction)(struct ID *id, struct LibraryForeachIDData *data);

typedef enum eIDTypeInfoCacheCallbackFlags {
  /** Indicates to the callback that that cache may be stored in the .blend file, so its pointer
   * should not be cleared at read-time. */
  IDTYPE_CACHE_CB_FLAGS_PERSISTENT = 1 << 0,
} eIDTypeInfoCacheCallbackFlags;
typedef void (*IDTypeForeachCacheFunctionCallback)(struct ID *id,
                                                   const struct IDCacheKey *cache_key,
                                                   void **cache_p,
                                                   uint flags,
                                                   void *user_data);
typedef void (*IDTypeForeachCacheFunction)(struct ID *id,
                                           IDTypeForeachCacheFunctionCallback function_callback,
                                           void *user_data);

typedef struct ID *(*IDTypeEmbeddedOwnerGetFunction)(struct Main *bmain, struct ID *id);

typedef void (*IDTypeBlendWriteFunction)(struct BlendWriter *writer,
                                         struct ID *id,
                                         const void *id_address);
typedef void (*IDTypeBlendReadDataFunction)(struct BlendDataReader *reader, struct ID *id);
typedef void (*IDTypeBlendReadLibFunction)(struct BlendLibReader *reader, struct ID *id);
typedef void (*IDTypeBlendReadExpandFunction)(struct BlendExpander *expander, struct ID *id);

typedef void (*IDTypeBlendReadUndoPreserve)(struct BlendLibReader *reader,
                                            struct ID *id_new,
                                            struct ID *id_old);

typedef void (*IDTypeLibOverrideApplyPost)(struct ID *id_dst, struct ID *id_src);

typedef struct IDTypeInfo {
  /* ********** General IDType data. ********** */

  /**
   * Unique identifier of this type, either as a short or an array of two chars, see DNA_ID.h's
   * ID_XX enums.
   */
  short id_code;
  /**
   * Bitflag matching id_code, used for filtering (e.g. in file browser), see DNA_ID.h's
   * FILTER_ID_XX enums.
   */
  uint64_t id_filter;

  /**
   * Define the position of this data-block type in the virtual list of all data in a Main that is
   * returned by `set_listbasepointers()`.
   * Very important, this has to be unique and below INDEX_ID_MAX, see DNA_ID.h.
   */
  int main_listbase_index;

  /** Memory size of a data-block of that type. */
  size_t struct_size;

  /** The user visible name for this data-block, also used as default name for a new data-block. */
  const char *name;
  /** Plural version of the user-visble name. */
  const char *name_plural;
  /** Translation context to use for UI messages related to that type of data-block. */
  const char *translation_context;

  /** Generic info flags about that data-block type. */
  uint32_t flags;

  /* ********** ID management callbacks ********** */

  /* TODO: Note about callbacks: Ideally we could also handle here `BKE_lib_query`'s behavior, as
   * well as read/write of files. However, this is a bit more involved than basic ID management
   * callbacks, so we'll check on this later. */

  /**
   * Initialize a new, empty calloc'ed data-block. May be NULL if there is nothing to do.
   */
  IDTypeInitDataFunction init_data;

  /**
   * Copy the given data-block's data from source to destination. May be NULL if mere memcopy of
   * the ID struct itself is enough.
   */
  IDTypeCopyDataFunction copy_data;

  /**
   * Free the data of the data-block (NOT the ID itself). May be NULL if there is nothing to do.
   */
  IDTypeFreeDataFunction free_data;

  /**
   * Make a linked data-block local. May be NULL if default behavior from
   * `BKE_lib_id_make_local_generic()` is enough.
   */
  IDTypeMakeLocalFunction make_local;

  /**
   * Called by `BKE_library_foreach_ID_link()` to apply a callback over all other ID usages (ID
   * pointers) of given data-block.
   */
  IDTypeForeachIDFunction foreach_id;

  /**
   * Iterator over all cache pointers of given ID.
   */
  IDTypeForeachCacheFunction foreach_cache;

  /**
   * For embedded IDs, return their owner ID.
   */
  IDTypeEmbeddedOwnerGetFunction owner_get;

  /* ********** Callbacks for reading and writing .blend files. ********** */

  /**
   * Write all structs that should be saved in a .blend file.
   */
  IDTypeBlendWriteFunction blend_write;

  /**
   * Update pointers for all structs directly owned by this data block.
   */
  IDTypeBlendReadDataFunction blend_read_data;

  /**
   * Update pointers to other id data blocks.
   */
  IDTypeBlendReadLibFunction blend_read_lib;

  /**
   * Specify which other id data blocks should be loaded when the current one is loaded.
   */
  IDTypeBlendReadExpandFunction blend_read_expand;

  /**
   * Allow an ID type to preserve some of its data across (memfile) undo steps.
   *
   * \note Called from #setup_app_data when undoing or redoing a memfile step.
   */
  IDTypeBlendReadUndoPreserve blend_read_undo_preserve;

  /**
   * Called after library override operations have been applied.
   *
   * \note Currently needed for some update operation on point caches.
   */
  IDTypeLibOverrideApplyPost lib_override_apply_post;
} IDTypeInfo;

/* ********** Declaration of each IDTypeInfo. ********** */

/* Those are defined in the respective BKE files. */
extern IDTypeInfo IDType_ID_SCE;
extern IDTypeInfo IDType_ID_LI;
extern IDTypeInfo IDType_ID_OB;
extern IDTypeInfo IDType_ID_ME;
extern IDTypeInfo IDType_ID_CU;
extern IDTypeInfo IDType_ID_MB;
extern IDTypeInfo IDType_ID_MA;
extern IDTypeInfo IDType_ID_TE;
extern IDTypeInfo IDType_ID_IM;
extern IDTypeInfo IDType_ID_LT;
extern IDTypeInfo IDType_ID_LA;
extern IDTypeInfo IDType_ID_CA;
extern IDTypeInfo IDType_ID_IP;
extern IDTypeInfo IDType_ID_KE;
extern IDTypeInfo IDType_ID_WO;
extern IDTypeInfo IDType_ID_SCR;
extern IDTypeInfo IDType_ID_VF;
extern IDTypeInfo IDType_ID_TXT;
extern IDTypeInfo IDType_ID_SPK;
extern IDTypeInfo IDType_ID_SO;
extern IDTypeInfo IDType_ID_GR;
extern IDTypeInfo IDType_ID_AR;
extern IDTypeInfo IDType_ID_AC;
extern IDTypeInfo IDType_ID_NT;
extern IDTypeInfo IDType_ID_BR;
extern IDTypeInfo IDType_ID_PA;
extern IDTypeInfo IDType_ID_GD;
extern IDTypeInfo IDType_ID_WM;
extern IDTypeInfo IDType_ID_MC;
extern IDTypeInfo IDType_ID_MSK;
extern IDTypeInfo IDType_ID_LS;
extern IDTypeInfo IDType_ID_PAL;
extern IDTypeInfo IDType_ID_PC;
extern IDTypeInfo IDType_ID_CF;
extern IDTypeInfo IDType_ID_WS;
extern IDTypeInfo IDType_ID_LP;
extern IDTypeInfo IDType_ID_HA;
extern IDTypeInfo IDType_ID_PT;
extern IDTypeInfo IDType_ID_VO;
extern IDTypeInfo IDType_ID_SIM;

extern IDTypeInfo IDType_ID_LINK_PLACEHOLDER;

/* ********** Helpers/Utils API. ********** */

/* Module initialization. */
void BKE_idtype_init(void);

/* General helpers. */
const struct IDTypeInfo *BKE_idtype_get_info_from_idcode(const short id_code);
const struct IDTypeInfo *BKE_idtype_get_info_from_id(const struct ID *id);

const char *BKE_idtype_idcode_to_name(const short idcode);
const char *BKE_idtype_idcode_to_name_plural(const short idcode);
const char *BKE_idtype_idcode_to_translation_context(const short idcode);
bool BKE_idtype_idcode_is_linkable(const short idcode);
bool BKE_idtype_idcode_is_valid(const short idcode);

short BKE_idtype_idcode_from_name(const char *idtype_name);

uint64_t BKE_idtype_idcode_to_idfilter(const short idcode);
short BKE_idtype_idcode_from_idfilter(const uint64_t idfilter);

int BKE_idtype_idcode_to_index(const short idcode);
short BKE_idtype_idcode_from_index(const int index);

short BKE_idtype_idcode_iter_step(int *index);

/* Some helpers/wrappers around callbacks defined in #IDTypeInfo, dealing e.g. with embedded IDs.
 * XXX Ideally those would rather belong to #BKE_lib_id, but using callback function pointers makes
 * this hard to do properly if we want to avoid headers includes in headers. */

void BKE_idtype_id_foreach_cache(struct ID *id,
                                 IDTypeForeachCacheFunctionCallback function_callback,
                                 void *user_data);

#ifdef __cplusplus
}
#endif
