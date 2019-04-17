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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup spbuttons
 */

#ifndef __BUTTONS_INTERN_H__
#define __BUTTONS_INTERN_H__

#include "DNA_listBase.h"
#include "RNA_types.h"

struct ARegionType;
struct ID;
struct SpaceProperties;
struct Tex;
struct bContext;
struct bContextDataResult;
struct bNode;
struct bNodeTree;
struct uiLayout;
struct wmOperatorType;

/* Display the context path in the header instead of the main window */
#define USE_HEADER_CONTEXT_PATH

/* context data */

typedef struct ButsContextPath {
  PointerRNA ptr[8];
  int len;
  int flag;
  int collection_ctx;
} ButsContextPath;

typedef struct ButsTextureUser {
  struct ButsTextureUser *next, *prev;

  struct ID *id;

  PointerRNA ptr;
  PropertyRNA *prop;

  struct bNodeTree *ntree;
  struct bNode *node;

  const char *category;
  int icon;
  const char *name;

  int index;
} ButsTextureUser;

typedef struct ButsContextTexture {
  ListBase users;

  struct Tex *texture;

  struct ButsTextureUser *user;
  int index;
} ButsContextTexture;

/* internal exports only */

/* buttons_context.c */
void buttons_context_compute(const struct bContext *C, struct SpaceProperties *sbuts);
int buttons_context(const struct bContext *C,
                    const char *member,
                    struct bContextDataResult *result);
void buttons_context_draw(const struct bContext *C, struct uiLayout *layout);
void buttons_context_register(struct ARegionType *art);
struct ID *buttons_context_id_path(const struct bContext *C);

extern const char *buttons_context_dir[]; /* doc access */

/* buttons_texture.c */
void buttons_texture_context_compute(const struct bContext *C, struct SpaceProperties *sbuts);

/* buttons_ops.c */
void BUTTONS_OT_file_browse(struct wmOperatorType *ot);
void BUTTONS_OT_directory_browse(struct wmOperatorType *ot);
void BUTTONS_OT_context_menu(struct wmOperatorType *ot);

#endif /* __BUTTONS_INTERN_H__ */
