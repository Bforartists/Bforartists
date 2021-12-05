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
#pragma once

/** \file
 * \ingroup bke
 */

#ifdef __cplusplus
extern "C" {
#endif

struct BlendHandle;
struct ID;
struct Library;
struct LibraryLink_Params;
struct Main;
struct ReportList;
struct Scene;
struct ViewLayer;
struct View3D;

typedef struct BlendfileLinkAppendContext BlendfileLinkAppendContext;
typedef struct BlendfileLinkAppendContextItem BlendfileLinkAppendContextItem;

BlendfileLinkAppendContext *BKE_blendfile_link_append_context_new(
    struct LibraryLink_Params *params);
void BKE_blendfile_link_append_context_free(struct BlendfileLinkAppendContext *lapp_context);
void BKE_blendfile_link_append_context_flag_set(struct BlendfileLinkAppendContext *lapp_context,
                                                const int flag,
                                                const bool do_set);

void BKE_blendfile_link_append_context_embedded_blendfile_set(
    struct BlendfileLinkAppendContext *lapp_context,
    const void *blendfile_mem,
    int blendfile_memsize);
void BKE_blendfile_link_append_context_embedded_blendfile_clear(
    struct BlendfileLinkAppendContext *lapp_context);

void BKE_blendfile_link_append_context_library_add(struct BlendfileLinkAppendContext *lapp_context,
                                                   const char *libname,
                                                   struct BlendHandle *blo_handle);
struct BlendfileLinkAppendContextItem *BKE_blendfile_link_append_context_item_add(
    struct BlendfileLinkAppendContext *lapp_context,
    const char *idname,
    const short idcode,
    void *userdata);

#define BLENDFILE_LINK_APPEND_INVALID -1
int BKE_blendfile_link_append_context_item_idtypes_from_library_add(
    struct BlendfileLinkAppendContext *lapp_context,
    struct ReportList *reports,
    const uint64_t id_types_filter,
    const int library_index);

void BKE_blendfile_link_append_context_item_library_index_enable(
    struct BlendfileLinkAppendContext *lapp_context,
    struct BlendfileLinkAppendContextItem *item,
    const int library_index);
bool BKE_blendfile_link_append_context_is_empty(struct BlendfileLinkAppendContext *lapp_context);

void *BKE_blendfile_link_append_context_item_userdata_get(
    struct BlendfileLinkAppendContext *lapp_context, struct BlendfileLinkAppendContextItem *item);
struct ID *BKE_blendfile_link_append_context_item_newid_get(
    struct BlendfileLinkAppendContext *lapp_context, struct BlendfileLinkAppendContextItem *item);
short BKE_blendfile_link_append_context_item_idcode_get(
    struct BlendfileLinkAppendContext *lapp_context, struct BlendfileLinkAppendContextItem *item);

typedef enum eBlendfileLinkAppendForeachItemFlag {
  /** Loop over directly linked items (i.e. those explicitly defined by user code). */
  BKE_BLENDFILE_LINK_APPEND_FOREACH_ITEM_FLAG_DO_DIRECT = 1 << 0,
  /** Loop over indirectly linked items (i.e. those defined by internal code, as dependencies of
   * direct ones).
   *
   * IMPORTANT: Those 'indirect' items currently may not cover **all** indirectly linked data.
   * See comments in #foreach_libblock_link_append_callback. */
  BKE_BLENDFILE_LINK_APPEND_FOREACH_ITEM_FLAG_DO_INDIRECT = 1 << 0,
} eBlendfileLinkAppendForeachItemFlag;
/** Callback called by #BKE_blendfile_link_append_context_item_foreach over each (or a subset of
 * each) of the items in given #BlendfileLinkAppendContext.
 *
 * \param userdata: An opaque void pointer passed to the `callback_function`.
 *
 * \return `true` if iteration should continue, `false` otherwise. */
typedef bool (*BKE_BlendfileLinkAppendContexteItemFunction)(
    struct BlendfileLinkAppendContext *lapp_context,
    struct BlendfileLinkAppendContextItem *item,
    void *userdata);
void BKE_blendfile_link_append_context_item_foreach(
    struct BlendfileLinkAppendContext *lapp_context,
    BKE_BlendfileLinkAppendContexteItemFunction callback_function,
    const eBlendfileLinkAppendForeachItemFlag flag,
    void *userdata);

void BKE_blendfile_append(struct BlendfileLinkAppendContext *lapp_context,
                          struct ReportList *reports);
void BKE_blendfile_link(struct BlendfileLinkAppendContext *lapp_context,
                        struct ReportList *reports);

void BKE_blendfile_library_relocate(struct BlendfileLinkAppendContext *lapp_context,
                                    struct ReportList *reports,
                                    struct Library *library,
                                    const bool do_reload);

#ifdef __cplusplus
}
#endif
