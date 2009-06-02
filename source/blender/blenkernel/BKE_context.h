/**
 * $Id$
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation (2008).
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef BKE_CONTEXT_H
#define BKE_CONTEXT_H

#ifdef __cplusplus
extern "C" {
#endif

#include "DNA_listBase.h"
#include "RNA_types.h"

struct ARegion;
struct bScreen;
struct EditMesh;
struct ListBase;
struct Main;
struct Object;
struct PointerRNA;
struct ReportList;
struct Scene;
struct ScrArea;
struct SpaceLink;
struct View3D;
struct RegionView3D;
struct StructRNA;
struct ToolSettings;
struct Image;
struct Text;
struct ImBuf;
struct EditBone;
struct bPoseChannel;
struct wmWindow;
struct wmWindowManager;
struct SpaceText;
struct SpaceImage;
struct ID;

/* Structs */

struct bContext;
typedef struct bContext bContext;

struct bContextDataResult;
typedef struct bContextDataResult bContextDataResult;

typedef int (*bContextDataCallback)(const bContext *C,
	const char *member, bContextDataResult *result);

typedef struct bContextStoreEntry {
	struct bContextStoreEntry *next, *prev;

	char name[128];
	PointerRNA ptr;
} bContextStoreEntry;

typedef struct bContextStore {
	struct bContextStore *next, *prev;

	ListBase entries;
	int used;
} bContextStore;

/* Context */

bContext *CTX_create(void);
void CTX_free(bContext *C);

bContext *CTX_copy(const bContext *C);

/* Stored Context */

bContextStore *CTX_store_add(ListBase *contexts, char *name, PointerRNA *ptr);
void CTX_store_set(bContext *C, bContextStore *store);
bContextStore *CTX_store_copy(bContextStore *store);
void CTX_store_free(bContextStore *store);
void CTX_store_free_list(ListBase *contexts);

/* Window Manager Context */

struct wmWindowManager *CTX_wm_manager(const bContext *C);
struct wmWindow *CTX_wm_window(const bContext *C);
struct bScreen *CTX_wm_screen(const bContext *C);
struct ScrArea *CTX_wm_area(const bContext *C);
struct SpaceLink *CTX_wm_space_data(const bContext *C);
struct ARegion *CTX_wm_region(const bContext *C);
void *CTX_wm_region_data(const bContext *C);
struct ARegion *CTX_wm_menu(const bContext *C);

struct View3D *CTX_wm_view3d(const bContext *C);
struct RegionView3D *CTX_wm_region_view3d(const bContext *C);
struct SpaceText *CTX_wm_space_text(const bContext *C);
struct SpaceImage *CTX_wm_space_image(const bContext *C);

void CTX_wm_manager_set(bContext *C, struct wmWindowManager *wm);
void CTX_wm_window_set(bContext *C, struct wmWindow *win);
void CTX_wm_screen_set(bContext *C, struct bScreen *screen); /* to be removed */
void CTX_wm_area_set(bContext *C, struct ScrArea *sa);
void CTX_wm_region_set(bContext *C, struct ARegion *region);
void CTX_wm_menu_set(bContext *C, struct ARegion *menu);

/* Data Context

   - note: listbases consist of LinkData items and must be
     freed with BLI_freelistN! */

PointerRNA CTX_data_pointer_get(bContext *C, const char *member);
ListBase CTX_data_collection_get(bContext *C, const char *member);
void CTX_data_get(bContext *C, const char *member, PointerRNA *r_ptr, ListBase *r_lb);

void CTX_data_id_pointer_set(bContextDataResult *result, struct ID *id);
void CTX_data_pointer_set(bContextDataResult *result, struct ID *id, StructRNA *type, void *data);

void CTX_data_id_list_add(bContextDataResult *result, struct ID *id);
void CTX_data_list_add(bContextDataResult *result, struct ID *id, StructRNA *type, void *data);

int CTX_data_equals(const char *member, const char *str);

/*void CTX_data_pointer_set(bContextDataResult *result, void *data);
void CTX_data_list_add(bContextDataResult *result, void *data);*/

#define CTX_DATA_BEGIN(C, Type, instance, member) \
	{ \
		ListBase ctx_data_list; \
		CollectionPointerLink *ctx_link; \
		CTX_data_##member(C, &ctx_data_list); \
		for(ctx_link=ctx_data_list.first; ctx_link; ctx_link=ctx_link->next) { \
			Type instance= ctx_link->ptr.data;

#define CTX_DATA_END \
		} \
		BLI_freelistN(&ctx_data_list); \
	}

int ctx_data_list_count(const bContext *C, int (*func)(const bContext*, ListBase*));

#define CTX_DATA_COUNT(C, member) \
	ctx_data_list_count(C, CTX_data_##member)

/* Data Context Members */

struct Main *CTX_data_main(const bContext *C);
struct Scene *CTX_data_scene(const bContext *C);
struct ToolSettings *CTX_data_tool_settings(const bContext *C);

void CTX_data_main_set(bContext *C, struct Main *bmain);
void CTX_data_scene_set(bContext *C, struct Scene *bmain);

int CTX_data_selected_editable_objects(const bContext *C, ListBase *list);
int CTX_data_selected_editable_bases(const bContext *C, ListBase *list);

int CTX_data_selected_objects(const bContext *C, ListBase *list);
int CTX_data_selected_bases(const bContext *C, ListBase *list);

int CTX_data_visible_objects(const bContext *C, ListBase *list);
int CTX_data_visible_bases(const bContext *C, ListBase *list);

struct Object *CTX_data_active_object(const bContext *C);
struct Base *CTX_data_active_base(const bContext *C);
struct Object *CTX_data_edit_object(const bContext *C);

struct Image *CTX_data_edit_image(const bContext *C);

struct Text *CTX_data_edit_text(const bContext *C);

int CTX_data_selected_nodes(const bContext *C, ListBase *list);

struct EditBone *CTX_data_active_bone(const bContext *C);
int CTX_data_selected_bones(const bContext *C, ListBase *list);
int CTX_data_selected_editable_bones(const bContext *C, ListBase *list);
int CTX_data_visible_bones(const bContext *C, ListBase *list);
int CTX_data_editable_bones(const bContext *C, ListBase *list);

struct bPoseChannel *CTX_data_active_pchan(const bContext *C);
int CTX_data_selected_pchans(const bContext *C, ListBase *list);
int CTX_data_visible_pchans(const bContext *C, ListBase *list);

#ifdef __cplusplus
}
#endif
	
#endif

