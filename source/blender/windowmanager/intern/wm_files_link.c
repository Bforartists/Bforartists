/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/windowmanager/intern/wm_files_link.c
 *  \ingroup wm
 *
 * Functions for dealing with append/link operators and helpers.
 */


#include <float.h>
#include <string.h>
#include <ctype.h>
#include <stdio.h>
#include <stddef.h>
#include <assert.h>
#include <errno.h>

#include "MEM_guardedalloc.h"

#include "DNA_ID.h"
#include "DNA_screen_types.h"
#include "DNA_scene_types.h"
#include "DNA_windowmanager_types.h"



#include "BLI_blenlib.h"
#include "BLI_bitmap.h"
#include "BLI_linklist.h"
#include "BLI_math.h"
#include "BLI_memarena.h"
#include "BLI_utildefines.h"
#include "BLI_ghash.h"

#include "BLO_readfile.h"

#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_library.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_report.h"
#include "BKE_scene.h"

#include "BKE_idcode.h"


#include "IMB_colormanagement.h"

#include "ED_screen.h"

#include "GPU_material.h"

#include "RNA_access.h"
#include "RNA_define.h"


#include "WM_api.h"
#include "WM_types.h"

#include "wm_files.h"

/* **************** link/append *************** */

static int wm_link_append_poll(bContext *C)
{
	if (WM_operator_winactive(C)) {
		/* linking changes active object which is pretty useful in general,
		 * but which totally confuses edit mode (i.e. it becoming not so obvious
		 * to leave from edit mode and invalid tools in toolbar might be displayed)
		 * so disable link/append when in edit mode (sergey) */
		if (CTX_data_edit_object(C))
			return 0;

		return 1;
	}

	return 0;
}

static int wm_link_append_invoke(bContext *C, wmOperator *op, const wmEvent *UNUSED(event))
{
	if (RNA_struct_property_is_set(op->ptr, "filepath")) {
		return WM_operator_call_notest(C, op);
	}
	else {
		/* XXX TODO solve where to get last linked library from */
		if (G.lib[0] != '\0') {
			RNA_string_set(op->ptr, "filepath", G.lib);
		}
		else if (G.relbase_valid) {
			char path[FILE_MAX];
			BLI_strncpy(path, G.main->name, sizeof(G.main->name));
			BLI_parent_dir(path);
			RNA_string_set(op->ptr, "filepath", path);
		}
		WM_event_add_fileselect(C, op);
		return OPERATOR_RUNNING_MODAL;
	}
}

static short wm_link_append_flag(wmOperator *op)
{
	PropertyRNA *prop;
	short flag = 0;

	if (RNA_boolean_get(op->ptr, "autoselect"))
		flag |= FILE_AUTOSELECT;
	if (RNA_boolean_get(op->ptr, "active_layer"))
		flag |= FILE_ACTIVELAY;
	if ((prop = RNA_struct_find_property(op->ptr, "relative_path")) && RNA_property_boolean_get(op->ptr, prop))
		flag |= FILE_RELPATH;
	if (RNA_boolean_get(op->ptr, "link"))
		flag |= FILE_LINK;
	if (RNA_boolean_get(op->ptr, "instance_groups"))
		flag |= FILE_GROUP_INSTANCE;

	return flag;
}

typedef struct WMLinkAppendDataItem {
	char *name;
	BLI_bitmap *libraries;  /* All libs (from WMLinkAppendData.libraries) to try to load this ID from. */
	short idcode;

	ID *new_id;
	void *customdata;
} WMLinkAppendDataItem;

typedef struct WMLinkAppendData {
	LinkNodePair libraries;
	LinkNodePair items;
	int num_libraries;
	int num_items;
	short flag;

	/* Internal 'private' data */
	MemArena *memarena;
} WMLinkAppendData;

static WMLinkAppendData *wm_link_append_data_new(const int flag)
{
	MemArena *ma = BLI_memarena_new(BLI_MEMARENA_STD_BUFSIZE, __func__);
	WMLinkAppendData *lapp_data = BLI_memarena_calloc(ma, sizeof(*lapp_data));

	lapp_data->flag = flag;
	lapp_data->memarena = ma;

	return lapp_data;
}

static void wm_link_append_data_free(WMLinkAppendData *lapp_data)
{
	BLI_memarena_free(lapp_data->memarena);
}

/* WARNING! *Never* call wm_link_append_data_library_add() after having added some items! */

static void wm_link_append_data_library_add(WMLinkAppendData *lapp_data, const char *libname)
{
	size_t len = strlen(libname) + 1;
	char *libpath = BLI_memarena_alloc(lapp_data->memarena, len);

	BLI_strncpy(libpath, libname, len);
	BLI_linklist_append_arena(&lapp_data->libraries, libpath, lapp_data->memarena);
	lapp_data->num_libraries++;
}

static WMLinkAppendDataItem *wm_link_append_data_item_add(
        WMLinkAppendData *lapp_data, const char *idname, const short idcode, void *customdata)
{
	WMLinkAppendDataItem *item = BLI_memarena_alloc(lapp_data->memarena, sizeof(*item));
	size_t len = strlen(idname) + 1;

	item->name = BLI_memarena_alloc(lapp_data->memarena, len);
	BLI_strncpy(item->name, idname, len);
	item->idcode = idcode;
	item->libraries = BLI_BITMAP_NEW_MEMARENA(lapp_data->memarena, lapp_data->num_libraries);

	item->new_id = NULL;
	item->customdata = customdata;

	BLI_linklist_append_arena(&lapp_data->items, item, lapp_data->memarena);
	lapp_data->num_items++;

	return item;
}

static void wm_link_do(
        WMLinkAppendData *lapp_data, ReportList *reports, Main *bmain, Scene *scene, View3D *v3d)
{
	Main *mainl;
	BlendHandle *bh;
	Library *lib;

	const int flag = lapp_data->flag;

	LinkNode *liblink, *itemlink;
	int lib_idx, item_idx;

	BLI_assert(lapp_data->num_items && lapp_data->num_libraries);

	for (lib_idx = 0, liblink = lapp_data->libraries.list; liblink; lib_idx++, liblink = liblink->next) {
		char *libname = liblink->link;

		bh = BLO_blendhandle_from_file(libname, reports);

		if (bh == NULL) {
			/* Unlikely since we just browsed it, but possible
			 * Error reports will have been made by BLO_blendhandle_from_file() */
			continue;
		}

		/* here appending/linking starts */
		mainl = BLO_library_link_begin(bmain, &bh, libname);
		lib = mainl->curlib;
		BLI_assert(lib);
		UNUSED_VARS_NDEBUG(lib);

		if (mainl->versionfile < 250) {
			BKE_reportf(reports, RPT_WARNING,
			            "Linking or appending from a very old .blend file format (%d.%d), no animation conversion will "
			            "be done! You may want to re-save your lib file with current Blender",
			            mainl->versionfile, mainl->subversionfile);
		}

		/* For each lib file, we try to link all items belonging to that lib,
		 * and tag those successful to not try to load them again with the other libs. */
		for (item_idx = 0, itemlink = lapp_data->items.list; itemlink; item_idx++, itemlink = itemlink->next) {
			WMLinkAppendDataItem *item = itemlink->link;
			ID *new_id;

			if (!BLI_BITMAP_TEST(item->libraries, lib_idx)) {
				continue;
			}

			new_id = BLO_library_link_named_part_ex(mainl, &bh, item->idcode, item->name, flag, scene, v3d);
			if (new_id) {
				/* If the link is sucessful, clear item's libs 'todo' flags.
				 * This avoids trying to link same item with other libraries to come. */
				BLI_BITMAP_SET_ALL(item->libraries, false, lapp_data->num_libraries);
				item->new_id = new_id;
			}
		}

		BLO_library_link_end(mainl, &bh, flag, scene, v3d);
		BLO_blendhandle_close(bh);
	}
}

static int wm_link_append_exec(bContext *C, wmOperator *op)
{
	Main *bmain = CTX_data_main(C);
	Scene *scene = CTX_data_scene(C);
	PropertyRNA *prop;
	WMLinkAppendData *lapp_data;
	char path[FILE_MAX_LIBEXTRA], root[FILE_MAXDIR], libname[FILE_MAX], relname[FILE_MAX];
	char *group, *name;
	int totfiles = 0;
	short flag;

	RNA_string_get(op->ptr, "filename", relname);
	RNA_string_get(op->ptr, "directory", root);

	BLI_join_dirfile(path, sizeof(path), root, relname);

	/* test if we have a valid data */
	if (!BLO_library_path_explode(path, libname, &group, &name)) {
		BKE_reportf(op->reports, RPT_ERROR, "'%s': not a library", path);
		return OPERATOR_CANCELLED;
	}
	else if (!group) {
		BKE_reportf(op->reports, RPT_ERROR, "'%s': nothing indicated", path);
		return OPERATOR_CANCELLED;
	}
	else if (BLI_path_cmp(bmain->name, libname) == 0) {
		BKE_reportf(op->reports, RPT_ERROR, "'%s': cannot use current file as library", path);
		return OPERATOR_CANCELLED;
	}

	/* check if something is indicated for append/link */
	prop = RNA_struct_find_property(op->ptr, "files");
	if (prop) {
		totfiles = RNA_property_collection_length(op->ptr, prop);
		if (totfiles == 0) {
			if (!name) {
				BKE_reportf(op->reports, RPT_ERROR, "'%s': nothing indicated", path);
				return OPERATOR_CANCELLED;
			}
		}
	}
	else if (!name) {
		BKE_reportf(op->reports, RPT_ERROR, "'%s': nothing indicated", path);
		return OPERATOR_CANCELLED;
	}

	flag = wm_link_append_flag(op);

	/* sanity checks for flag */
	if (scene && scene->id.lib) {
		BKE_reportf(op->reports, RPT_WARNING,
		            "Scene '%s' is linked, instantiation of objects & groups is disabled", scene->id.name + 2);
		flag &= ~FILE_GROUP_INSTANCE;
		scene = NULL;
	}

	/* from here down, no error returns */

	if (scene && RNA_boolean_get(op->ptr, "autoselect")) {
		BKE_scene_base_deselect_all(scene);
	}
	
	/* tag everything, all untagged data can be made local
	 * its also generally useful to know what is new
	 *
	 * take extra care BKE_main_id_flag_all(bmain, LIB_TAG_PRE_EXISTING, false) is called after! */
	BKE_main_id_tag_all(bmain, LIB_TAG_PRE_EXISTING, true);

	/* We define our working data...
	 * Note that here, each item 'uses' one library, and only one. */
	lapp_data = wm_link_append_data_new(flag);
	if (totfiles != 0) {
		GHash *libraries = BLI_ghash_new(BLI_ghashutil_strhash_p, BLI_ghashutil_strcmp, __func__);
		int lib_idx = 0;

		RNA_BEGIN (op->ptr, itemptr, "files")
		{
			RNA_string_get(&itemptr, "name", relname);

			BLI_join_dirfile(path, sizeof(path), root, relname);

			if (BLO_library_path_explode(path, libname, &group, &name)) {
				if (!group || !name) {
					continue;
				}

				if (!BLI_ghash_haskey(libraries, libname)) {
					BLI_ghash_insert(libraries, BLI_strdup(libname), SET_INT_IN_POINTER(lib_idx));
					lib_idx++;
					wm_link_append_data_library_add(lapp_data, libname);
				}
			}
		}
		RNA_END;

		RNA_BEGIN (op->ptr, itemptr, "files")
		{
			RNA_string_get(&itemptr, "name", relname);

			BLI_join_dirfile(path, sizeof(path), root, relname);

			if (BLO_library_path_explode(path, libname, &group, &name)) {
				WMLinkAppendDataItem *item;
				if (!group || !name) {
					printf("skipping %s\n", path);
					continue;
				}

				lib_idx = GET_INT_FROM_POINTER(BLI_ghash_lookup(libraries, libname));

				item = wm_link_append_data_item_add(lapp_data, name, BKE_idcode_from_name(group), NULL);
				BLI_BITMAP_ENABLE(item->libraries, lib_idx);
			}
		}
		RNA_END;

		BLI_ghash_free(libraries, MEM_freeN, NULL);
	}
	else {
		WMLinkAppendDataItem *item;

		wm_link_append_data_library_add(lapp_data, libname);
		item = wm_link_append_data_item_add(lapp_data, name, BKE_idcode_from_name(group), NULL);
		BLI_BITMAP_ENABLE(item->libraries, 0);
	}

	/* XXX We'd need re-entrant locking on Main for this to work... */
	/* BKE_main_lock(bmain); */

	wm_link_do(lapp_data, op->reports, bmain, scene, CTX_wm_view3d(C));

	/* BKE_main_unlock(bmain); */

	wm_link_append_data_free(lapp_data);

	/* mark all library linked objects to be updated */
	BKE_main_lib_objects_recalc_all(bmain);
	IMB_colormanagement_check_file_config(bmain);

	/* append, rather than linking */
	if ((flag & FILE_LINK) == 0) {
		bool set_fake = RNA_boolean_get(op->ptr, "set_fake");
		BKE_library_make_local(bmain, NULL, true, set_fake);
	}

	/* important we unset, otherwise these object wont
	 * link into other scenes from this blend file */
	BKE_main_id_tag_all(bmain, LIB_TAG_PRE_EXISTING, false);

	/* recreate dependency graph to include new objects */
	DAG_scene_relations_rebuild(bmain, scene);
	
	/* free gpu materials, some materials depend on existing objects, such as lamps so freeing correctly refreshes */
	GPU_materials_free();

	/* XXX TODO: align G.lib with other directory storage (like last opened image etc...) */
	BLI_strncpy(G.lib, root, FILE_MAX);

	WM_event_add_notifier(C, NC_WINDOW, NULL);

	return OPERATOR_FINISHED;
}

static void wm_link_append_properties_common(wmOperatorType *ot, bool is_link)
{
	PropertyRNA *prop;

	/* better not save _any_ settings for this operator */
	/* properties */
	prop = RNA_def_boolean(ot->srna, "link", is_link,
	                       "Link", "Link the objects or datablocks rather than appending");
	RNA_def_property_flag(prop, PROP_SKIP_SAVE | PROP_HIDDEN);
	prop = RNA_def_boolean(ot->srna, "autoselect", true,
	                       "Select", "Select new objects");
	RNA_def_property_flag(prop, PROP_SKIP_SAVE);
	prop = RNA_def_boolean(ot->srna, "active_layer", true,
	                       "Active Layer", "Put new objects on the active layer");
	RNA_def_property_flag(prop, PROP_SKIP_SAVE);
	prop = RNA_def_boolean(ot->srna, "instance_groups", is_link,
	                       "Instance Groups", "Create Dupli-Group instances for each group");
	RNA_def_property_flag(prop, PROP_SKIP_SAVE);
}

void WM_OT_link(wmOperatorType *ot)
{
	ot->name = "Link from Library";
	ot->idname = "WM_OT_link";
	ot->description = "Link from a Library .blend file";
	
	ot->invoke = wm_link_append_invoke;
	ot->exec = wm_link_append_exec;
	ot->poll = wm_link_append_poll;
	
	ot->flag |= OPTYPE_UNDO;

	WM_operator_properties_filesel(
	        ot, FILE_TYPE_FOLDER | FILE_TYPE_BLENDER | FILE_TYPE_BLENDERLIB, FILE_LOADLIB, FILE_OPENFILE,
	        WM_FILESEL_FILEPATH | WM_FILESEL_DIRECTORY | WM_FILESEL_FILENAME | WM_FILESEL_RELPATH | WM_FILESEL_FILES,
	        FILE_DEFAULTDISPLAY, FILE_SORT_ALPHA);
	
	wm_link_append_properties_common(ot, true);
}

void WM_OT_append(wmOperatorType *ot)
{
	ot->name = "Append from Library";
	ot->idname = "WM_OT_append";
	ot->description = "Append from a Library .blend file";

	ot->invoke = wm_link_append_invoke;
	ot->exec = wm_link_append_exec;
	ot->poll = wm_link_append_poll;

	ot->flag |= OPTYPE_UNDO;

	WM_operator_properties_filesel(
	        ot, FILE_TYPE_FOLDER | FILE_TYPE_BLENDER | FILE_TYPE_BLENDERLIB, FILE_LOADLIB, FILE_OPENFILE,
	        WM_FILESEL_FILEPATH | WM_FILESEL_DIRECTORY | WM_FILESEL_FILENAME | WM_FILESEL_FILES,
	        FILE_DEFAULTDISPLAY, FILE_SORT_ALPHA);

	wm_link_append_properties_common(ot, false);
	RNA_def_boolean(ot->srna, "set_fake", false, "Fake User", "Set Fake User for appended items (except Objects and Groups)");
}
