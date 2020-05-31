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
 */

#ifndef __BKE_WORKSPACE_H__
#define __BKE_WORKSPACE_H__

#include "BLI_compiler_attrs.h"

#ifdef __cplusplus
extern "C" {
#endif

struct Main;
struct bScreen;
struct bToolRef;

/* -------------------------------------------------------------------- */
/* Create, delete, init */

struct WorkSpace *BKE_workspace_add(struct Main *bmain, const char *name);
void BKE_workspace_remove(struct Main *bmain, struct WorkSpace *workspace);

struct WorkSpaceInstanceHook *BKE_workspace_instance_hook_create(const struct Main *bmain);
void BKE_workspace_instance_hook_free(const struct Main *bmain,
                                      struct WorkSpaceInstanceHook *hook);

struct WorkSpaceLayout *BKE_workspace_layout_add(struct Main *bmain,
                                                 struct WorkSpace *workspace,
                                                 struct bScreen *screen,
                                                 const char *name) ATTR_NONNULL();
void BKE_workspace_layout_remove(struct Main *bmain,
                                 struct WorkSpace *workspace,
                                 struct WorkSpaceLayout *layout) ATTR_NONNULL();

void BKE_workspace_relations_free(ListBase *relation_list);

/* -------------------------------------------------------------------- */
/* General Utils */

struct WorkSpaceLayout *BKE_workspace_layout_find(const struct WorkSpace *workspace,
                                                  const struct bScreen *screen)
    ATTR_NONNULL() ATTR_WARN_UNUSED_RESULT;
struct WorkSpaceLayout *BKE_workspace_layout_find_global(const struct Main *bmain,
                                                         const struct bScreen *screen,
                                                         struct WorkSpace **r_workspace)
    ATTR_NONNULL(1, 2);

struct WorkSpaceLayout *BKE_workspace_layout_iter_circular(
    const struct WorkSpace *workspace,
    struct WorkSpaceLayout *start,
    bool (*callback)(const struct WorkSpaceLayout *layout, void *arg),
    void *arg,
    const bool iter_backward);

void BKE_workspace_tool_remove(struct WorkSpace *workspace, struct bToolRef *tref)
    ATTR_NONNULL(1, 2);

/* -------------------------------------------------------------------- */
/* Getters/Setters */

#define GETTER_ATTRS ATTR_NONNULL() ATTR_WARN_UNUSED_RESULT
#define SETTER_ATTRS ATTR_NONNULL(1)

struct WorkSpace *BKE_workspace_active_get(struct WorkSpaceInstanceHook *hook) GETTER_ATTRS;
void BKE_workspace_active_set(struct WorkSpaceInstanceHook *hook,
                              struct WorkSpace *workspace) SETTER_ATTRS;
struct WorkSpaceLayout *BKE_workspace_active_layout_get(const struct WorkSpaceInstanceHook *hook)
    GETTER_ATTRS;
void BKE_workspace_active_layout_set(struct WorkSpaceInstanceHook *hook,
                                     struct WorkSpace *workspace,
                                     struct WorkSpaceLayout *layout) SETTER_ATTRS;
struct bScreen *BKE_workspace_active_screen_get(const struct WorkSpaceInstanceHook *hook)
    GETTER_ATTRS;
void BKE_workspace_active_screen_set(struct WorkSpaceInstanceHook *hook,
                                     struct WorkSpace *workspace,
                                     struct bScreen *screen) SETTER_ATTRS;

const char *BKE_workspace_layout_name_get(const struct WorkSpaceLayout *layout) GETTER_ATTRS;
void BKE_workspace_layout_name_set(struct WorkSpace *workspace,
                                   struct WorkSpaceLayout *layout,
                                   const char *new_name) ATTR_NONNULL();
struct bScreen *BKE_workspace_layout_screen_get(const struct WorkSpaceLayout *layout) GETTER_ATTRS;

struct WorkSpaceLayout *BKE_workspace_active_layout_for_workspace_get(
    const struct WorkSpaceInstanceHook *hook, const struct WorkSpace *workspace) GETTER_ATTRS;

bool BKE_workspace_owner_id_check(const struct WorkSpace *workspace, const char *owner_id)
    ATTR_NONNULL();

void BKE_workspace_id_tag_all_visible(struct Main *bmain, int tag) ATTR_NONNULL();

#undef GETTER_ATTRS
#undef SETTER_ATTRS

#ifdef __cplusplus
}
#endif

#endif /* __BKE_WORKSPACE_H__ */
