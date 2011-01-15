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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Andrea Weikert (c) 2008 Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "BKE_context.h"
#include "BKE_screen.h"
#include "BKE_global.h"
#include "BKE_report.h"
#include "BKE_main.h"

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"
#include "BLI_storage_types.h"
#ifdef WIN32
#include "BLI_winstuff.h"
#endif

#include "ED_screen.h"
#include "ED_fileselect.h"

#include "MEM_guardedalloc.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "UI_view2d.h"

#include "WM_api.h"
#include "WM_types.h"

#include "file_intern.h"
#include "filelist.h"
#include "fsmenu.h"

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* for events */
#define NOTACTIVEFILE			0
#define ACTIVATE			1
#define INACTIVATE			2

/* ---------- FILE SELECTION ------------ */

static int find_file_mouse(SpaceFile *sfile, struct ARegion* ar, int clamp_bounds, int x, int y)
{
	float fx,fy;
	int active_file = -1;
	View2D* v2d = &ar->v2d;

	UI_view2d_region_to_view(v2d, x, y, &fx, &fy);

	active_file = ED_fileselect_layout_offset(sfile->layout, clamp_bounds, v2d->tot.xmin + fx, v2d->tot.ymax - fy);
	
	return active_file;
}


static void file_deselect_all(SpaceFile* sfile)
{
	int numfiles = filelist_numfiles(sfile->files);
	int i;

	for ( i=0; i < numfiles; ++i) {
		struct direntry* file = filelist_file(sfile->files, i);
		if (file && (file->flags & ACTIVEFILE)) {
			file->flags &= ~ACTIVEFILE;
		}
	}
}

typedef enum FileSelect { FILE_SELECT_DIR = 1, 
  FILE_SELECT_FILE = 2 } FileSelect;


static void clamp_to_filelist(int numfiles, int *first_file, int *last_file)
{
	/* border select before the first file */
	if ( (*first_file < 0) && (*last_file >=0 ) ) {
		*first_file = 0;
	}
	/* don't select if everything is outside filelist */
	if ( (*first_file >= numfiles) && ((*last_file < 0) || (*last_file >= numfiles)) ) {
		*first_file = -1;
		*last_file = -1;
	}
	
	/* fix if last file invalid */
	if ( (*first_file > 0) && (*last_file < 0) )
		*last_file = numfiles-1;

	/* clamp */
	if ( (*first_file >= numfiles) ) {
		*first_file = numfiles-1;
	}
	if ( (*last_file >= numfiles) ) {
		*last_file = numfiles-1;
	}
}

static FileSelect file_select(bContext* C, const rcti* rect, short selecting, short toggle_one, short fill)
{
	ARegion *ar= CTX_wm_region(C);
	SpaceFile *sfile= CTX_wm_space_file(C);
	int first_file = -1;
	int last_file = -1;
	int act_file;
	FileSelect retval = FILE_SELECT_FILE;

	FileSelectParams *params = ED_fileselect_get_params(sfile);
	// FileLayout *layout = ED_fileselect_get_layout(sfile, ar);

	int numfiles = filelist_numfiles(sfile->files);
	
	params->selstate = NOTACTIVEFILE;
	first_file = find_file_mouse(sfile, ar, 1, rect->xmin, rect->ymax);
	last_file = find_file_mouse(sfile, ar, 1, rect->xmax, rect->ymin);
	
	clamp_to_filelist(numfiles, &first_file, &last_file);

	if (fill && (last_file >= 0) && (last_file < numfiles) ) {
		int f= last_file;
		while (f >= 0) {
			struct direntry* file = filelist_file(sfile->files, f);
			if (file->flags & ACTIVEFILE)
				break;
			f--;
		}
		if (f >= 0) {
			first_file = f+1;
		}
	}

	/* select all valid files between first and last indicated */
	if ( (first_file >= 0) && (first_file < numfiles) && (last_file >= 0) && (last_file < numfiles) ) {
		for (act_file = first_file; act_file <= last_file; act_file++) {
			struct direntry* file = filelist_file(sfile->files, act_file);
			
			if (toggle_one) {
				if (file->flags & ACTIVEFILE) {
					file->flags &= ~ACTIVEFILE;
					selecting=0;
				} else
					file->flags |= ACTIVEFILE;
			} else if (selecting) 
				file->flags |= ACTIVEFILE;
			else
				file->flags &= ~ACTIVEFILE;
		}
	}

	/* Don't act on multiple selected files */
	if (first_file != last_file) selecting= 0;

	/* make the last file active */
	if (selecting && (last_file >= 0 && last_file < numfiles)) {
		struct direntry* file = filelist_file(sfile->files, last_file);
		params->active_file = last_file;

		if(file && S_ISDIR(file->type)) {
			/* the path is too long and we are not going up! */
			if (strcmp(file->relname, "..") && strlen(params->dir) + strlen(file->relname) >= FILE_MAX ) 
			{
				// XXX error("Path too long, cannot enter this directory");
			} else {
				if (strcmp(file->relname, "..")==0) { 	 
					/* avoids /../../ */ 	 
					BLI_parent_dir(params->dir); 	 
				} else {
					BLI_cleanup_dir(G.main->name, params->dir);
					strcat(params->dir, file->relname);
					BLI_add_slash(params->dir);
				}

				file_change_dir(C, 0);
				retval = FILE_SELECT_DIR;
			}
		}
		else if (file)
		{
			if (file->relname) {
				BLI_strncpy(params->file, file->relname, FILE_MAXFILE);
			}
			
		}	
	}
	
	/* update operator for name change event */
	file_draw_check_cb(C, NULL, NULL);
	
	return retval;
}



static int file_border_select_exec(bContext *C, wmOperator *op)
{
	ARegion *ar= CTX_wm_region(C);
	short selecting;
	rcti rect;
	
	selecting= (RNA_int_get(op->ptr, "gesture_mode")==GESTURE_MODAL_SELECT);
	rect.xmin= RNA_int_get(op->ptr, "xmin");
	rect.ymin= RNA_int_get(op->ptr, "ymin");
	rect.xmax= RNA_int_get(op->ptr, "xmax");
	rect.ymax= RNA_int_get(op->ptr, "ymax");

	BLI_isect_rcti(&(ar->v2d.mask), &rect, &rect);
	
	if (FILE_SELECT_DIR == file_select(C, &rect, selecting, 0, 0)) {
		WM_event_add_notifier(C, NC_SPACE|ND_SPACE_FILE_LIST, NULL);
	} else {
		WM_event_add_notifier(C, NC_SPACE|ND_SPACE_FILE_PARAMS, NULL);
	}
	return OPERATOR_FINISHED;
}

void FILE_OT_select_border(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Activate/Select File";
	ot->description= "Activate/select the file(s) contained in the border";
	ot->idname= "FILE_OT_select_border";
	
	/* api callbacks */
	ot->invoke= WM_border_select_invoke;
	ot->exec= file_border_select_exec;
	ot->modal= WM_border_select_modal;
	ot->poll= ED_operator_file_active;

	/* rna */
	WM_operator_properties_gesture_border(ot, 0);
}

static int file_select_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	ARegion *ar= CTX_wm_region(C);
	SpaceFile *sfile= CTX_wm_space_file(C);
	rcti rect;
	int extend = RNA_boolean_get(op->ptr, "extend");
	int fill = RNA_boolean_get(op->ptr, "fill");

	if(ar->regiontype != RGN_TYPE_WINDOW)
		return OPERATOR_CANCELLED;

	rect.xmin = rect.xmax = event->x - ar->winrct.xmin;
	rect.ymin = rect.ymax = event->y - ar->winrct.ymin;

	if(!BLI_in_rcti(&ar->v2d.mask, rect.xmin, rect.ymin))
		return OPERATOR_CANCELLED;

	/* single select, deselect all selected first */
	if (!extend) file_deselect_all(sfile);

	if (FILE_SELECT_DIR == file_select(C, &rect, 1, extend, fill ))
		WM_event_add_notifier(C, NC_SPACE|ND_SPACE_FILE_LIST, NULL);
	else
		WM_event_add_notifier(C, NC_SPACE|ND_SPACE_FILE_PARAMS, NULL);

	WM_event_add_mousemove(C); /* for directory changes */
	WM_event_add_notifier(C, NC_SPACE|ND_SPACE_FILE_PARAMS, NULL);

	return OPERATOR_FINISHED;
}

void FILE_OT_select(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Activate/Select File";
	ot->description= "Activate/select file";
	ot->idname= "FILE_OT_select";
	
	/* api callbacks */
	ot->invoke= file_select_invoke;
	ot->poll= ED_operator_file_active;

	/* rna */
	RNA_def_boolean(ot->srna, "extend", 0, "Extend", "Extend selection instead of deselecting everything first.");
	RNA_def_boolean(ot->srna, "fill", 0, "Fill", "Select everything beginning with the last selection.");
}

static int file_select_all_exec(bContext *C, wmOperator *UNUSED(op))
{
	ScrArea *sa= CTX_wm_area(C);
	SpaceFile *sfile= CTX_wm_space_file(C);
	int numfiles = filelist_numfiles(sfile->files);
	int i;
	int select = 1;

	/* if any file is selected, deselect all first */
	for ( i=0; i < numfiles; ++i) {
		struct direntry* file = filelist_file(sfile->files, i);
		if (file && (file->flags & ACTIVEFILE)) {
			file->flags &= ~ACTIVEFILE;
			select = 0;
			ED_area_tag_redraw(sa);
		}
	}
	/* select all only if previously no file was selected */
	if (select) {
		for ( i=0; i < numfiles; ++i) {
			struct direntry* file = filelist_file(sfile->files, i);
			if(file && !S_ISDIR(file->type)) {
				file->flags |= ACTIVEFILE;
				ED_area_tag_redraw(sa);
			}
		}
	}
	return OPERATOR_FINISHED;
}

void FILE_OT_select_all_toggle(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Select/Deselect All Files";
	ot->description= "Select/deselect all files";
	ot->idname= "FILE_OT_select_all_toggle";
	
	/* api callbacks */
	ot->exec= file_select_all_exec;

	/* rna */

	ot->poll= ED_operator_file_active;
}

/* ---------- BOOKMARKS ----------- */

static int bookmark_select_exec(bContext *C, wmOperator *op)
{
	SpaceFile *sfile= CTX_wm_space_file(C);

	if(RNA_struct_find_property(op->ptr, "dir")) {
		char entry[256];
		FileSelectParams* params = sfile->params;

		RNA_string_get(op->ptr, "dir", entry);
		BLI_strncpy(params->dir, entry, sizeof(params->dir));
		BLI_cleanup_dir(G.main->name, params->dir);
		file_change_dir(C, 1);

		WM_event_add_notifier(C, NC_SPACE|ND_SPACE_FILE_LIST, NULL);
	}
	
	return OPERATOR_FINISHED;
}

void FILE_OT_select_bookmark(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Select Directory";
	ot->description= "Select a bookmarked directory";
	ot->idname= "FILE_OT_select_bookmark";
	
	/* api callbacks */
	ot->exec= bookmark_select_exec;
	ot->poll= ED_operator_file_active;

	RNA_def_string(ot->srna, "dir", "", 256, "Dir", "");
}

static int bookmark_add_exec(bContext *C, wmOperator *UNUSED(op))
{
	ScrArea *sa= CTX_wm_area(C);
	SpaceFile *sfile= CTX_wm_space_file(C);
	struct FSMenu* fsmenu = fsmenu_get();
	struct FileSelectParams* params= ED_fileselect_get_params(sfile);

	if (params->dir[0] != '\0') {
		char name[FILE_MAX];
	
		fsmenu_insert_entry(fsmenu, FS_CATEGORY_BOOKMARKS, params->dir, 0, 1);
		BLI_make_file_string("/", name, BLI_get_folder_create(BLENDER_USER_CONFIG, NULL), BLENDER_BOOKMARK_FILE);
		fsmenu_write_file(fsmenu, name);
	}

	ED_area_tag_redraw(sa);
	return OPERATOR_FINISHED;
}

void FILE_OT_bookmark_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Bookmark";
	ot->description= "Add a bookmark for the selected/active directory";
	ot->idname= "FILE_OT_bookmark_add";
	
	/* api callbacks */
	ot->exec= bookmark_add_exec;
	ot->poll= ED_operator_file_active;
}

static int bookmark_delete_exec(bContext *C, wmOperator *op)
{
	ScrArea *sa= CTX_wm_area(C);
	struct FSMenu* fsmenu = fsmenu_get();
	int nentries = fsmenu_get_nentries(fsmenu, FS_CATEGORY_BOOKMARKS);
	
	if(RNA_struct_find_property(op->ptr, "index")) {
		int index = RNA_int_get(op->ptr, "index");
		if ( (index >-1) && (index < nentries)) {
			char name[FILE_MAX];
			
			fsmenu_remove_entry(fsmenu, FS_CATEGORY_BOOKMARKS, index);
			BLI_make_file_string("/", name, BLI_get_folder_create(BLENDER_USER_CONFIG, NULL), BLENDER_BOOKMARK_FILE);
			fsmenu_write_file(fsmenu, name);
			ED_area_tag_redraw(sa);
		}
	}

	return OPERATOR_FINISHED;
}

void FILE_OT_delete_bookmark(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Delete Bookmark";
	ot->description= "Delete selected bookmark";
	ot->idname= "FILE_OT_delete_bookmark";
	
	/* api callbacks */
	ot->exec= bookmark_delete_exec;
	ot->poll= ED_operator_file_active;

	RNA_def_int(ot->srna, "index", -1, -1, 20000, "Index", "", -1, 20000);
}

int file_hilight_set(SpaceFile *sfile, ARegion *ar, int mx, int my)
{
	FileSelectParams* params;
	int numfiles, actfile, origfile;
	
	if(sfile==NULL || sfile->files==NULL) return 0;

	numfiles = filelist_numfiles(sfile->files);
	params = ED_fileselect_get_params(sfile);

	origfile= params->active_file;

	mx -= ar->winrct.xmin;
	my -= ar->winrct.ymin;

	if(BLI_in_rcti(&ar->v2d.mask, mx, my)) {
		actfile = find_file_mouse(sfile, ar, 0, mx , my);

		if((actfile >= 0) && (actfile < numfiles))
			params->active_file=actfile;
		else
			params->active_file= -1;
	}
	else
		params->active_file= -1;

	return (params->active_file != origfile);
}

static int file_highlight_invoke(bContext *C, wmOperator *UNUSED(op), wmEvent *event)
{
	ARegion *ar= CTX_wm_region(C);
	SpaceFile *sfile= CTX_wm_space_file(C);

	if(!file_hilight_set(sfile, ar, event->x, event->y))
		return OPERATOR_CANCELLED;

	ED_area_tag_redraw(CTX_wm_area(C));
	
	return OPERATOR_FINISHED;
}

void FILE_OT_highlight(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Highlight File";
	ot->description= "Highlight selected file(s)";
	ot->idname= "FILE_OT_highlight";
	
	/* api callbacks */
	ot->invoke= file_highlight_invoke;
	ot->poll= ED_operator_file_active;
}

int file_cancel_exec(bContext *C, wmOperator *UNUSED(unused))
{
	SpaceFile *sfile= CTX_wm_space_file(C);
	wmOperator *op = sfile->op;
	
	sfile->op = NULL;

	WM_event_fileselect_event(C, op, EVT_FILESELECT_CANCEL);
	
	return OPERATOR_FINISHED;
}

int file_operator_poll(bContext *C)
{
	int poll = ED_operator_file_active(C);
	SpaceFile *sfile= CTX_wm_space_file(C);

	if (!sfile || !sfile->op) poll= 0;

	return poll;
}

void FILE_OT_cancel(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Cancel File Load";
	ot->description= "Cancel loading of selected file";
	ot->idname= "FILE_OT_cancel";
	
	/* api callbacks */
	ot->exec= file_cancel_exec;
	ot->poll= file_operator_poll;
}


void file_sfile_to_operator(wmOperator *op, SpaceFile *sfile, char *filepath)
{
	BLI_join_dirfile(filepath, sfile->params->dir, sfile->params->file);
	if(RNA_struct_find_property(op->ptr, "relative_path")) {
		if(RNA_boolean_get(op->ptr, "relative_path")) {
			BLI_path_rel(filepath, G.main->name);
		}
	}

	if(RNA_struct_find_property(op->ptr, "filename")) {
		RNA_string_set(op->ptr, "filename", sfile->params->file);
	}
	if(RNA_struct_find_property(op->ptr, "directory")) {
		RNA_string_set(op->ptr, "directory", sfile->params->dir);
	}
	if(RNA_struct_find_property(op->ptr, "filepath")) {
		RNA_string_set(op->ptr, "filepath", filepath);
	}
	
	/* some ops have multiple files to select */
	{
		PointerRNA itemptr;
		int i, numfiles = filelist_numfiles(sfile->files);
		struct direntry *file;
		if(RNA_struct_find_property(op->ptr, "files")) {
			for (i=0; i<numfiles; i++) {
				file = filelist_file(sfile->files, i);
				if(file->flags & ACTIVEFILE) {
					if ((file->type & S_IFDIR)==0) {
						RNA_collection_add(op->ptr, "files", &itemptr);
						RNA_string_set(&itemptr, "name", file->relname);
					}
				}
			}
		}
		
		if(RNA_struct_find_property(op->ptr, "dirs")) {
			for (i=0; i<numfiles; i++) {
				file = filelist_file(sfile->files, i);
				if(file->flags & ACTIVEFILE) {
					if ((file->type & S_IFDIR)) {
						RNA_collection_add(op->ptr, "dirs", &itemptr);
						RNA_string_set(&itemptr, "name", file->relname);
					}
				}
			}
		}
	}
}

void file_operator_to_sfile(SpaceFile *sfile, wmOperator *op)
{
	int change= FALSE;
	if(RNA_struct_find_property(op->ptr, "filename")) {
		RNA_string_get(op->ptr, "filename", sfile->params->file);
		change= TRUE;
	}
	if(RNA_struct_find_property(op->ptr, "directory")) {
		RNA_string_get(op->ptr, "directory", sfile->params->dir);
		change= TRUE;
	}
	
	/* If neither of the above are set, split the filepath back */
	if(RNA_struct_find_property(op->ptr, "filepath")) {
		if(change==FALSE) {
			char filepath[FILE_MAX];
			RNA_string_get(op->ptr, "filepath", filepath);
			BLI_split_dirfile(filepath, sfile->params->dir, sfile->params->file);
		}
	}
	
	/* XXX, files and dirs updates missing, not really so important though */
}

void file_draw_check_cb(bContext *C, void *UNUSED(arg1), void *UNUSED(arg2))
{
	SpaceFile *sfile= CTX_wm_space_file(C);
	wmOperator *op= sfile->op;
	if(op) { /* fail on reload */
		if(op->type->check) {
			char filepath[FILE_MAX];
			file_sfile_to_operator(op, sfile, filepath);
			
			/* redraw */
			if(op->type->check(C, op)) {
				file_operator_to_sfile(sfile, op);
	
				/* redraw, else the changed settings wont get updated */
				ED_area_tag_redraw(CTX_wm_area(C));
			}
		}
	}
}

int file_draw_check_exists(SpaceFile *sfile)
{
	if(sfile->op) { /* fails on reload */
		if(RNA_struct_find_property(sfile->op->ptr, "check_existing")) {
			if(RNA_boolean_get(sfile->op->ptr, "check_existing")) {
				char filepath[FILE_MAX];
				BLI_join_dirfile(filepath, sfile->params->dir, sfile->params->file);
				if(BLI_exists(filepath) && !BLI_is_dir(filepath)) {
					return TRUE;
				}
			}
		}
	}

	return FALSE;
}

/* sends events now, so things get handled on windowqueue level */
int file_exec(bContext *C, wmOperator *exec_op)
{
	SpaceFile *sfile= CTX_wm_space_file(C);
	char filepath[FILE_MAX];
	
	if(sfile->op) {
		wmOperator *op= sfile->op;
	
		/* when used as a macro, for doubleclick, 
		 to prevent closing when doubleclicking on .. item */
		if (RNA_boolean_get(exec_op->ptr, "need_active")) {
			int i, active=0;
			struct direntry *file;
			
			for (i=0; i<filelist_numfiles(sfile->files); i++) {
				file = filelist_file(sfile->files, i);
				if(file->flags & ACTIVEFILE) {
					active=1;
				}
			}
			if (active == 0)
				return OPERATOR_CANCELLED;
		}
		
		sfile->op = NULL;

		file_sfile_to_operator(op, sfile, filepath);

		fsmenu_insert_entry(fsmenu_get(), FS_CATEGORY_RECENT, sfile->params->dir,0, 1);
		BLI_make_file_string(G.main->name, filepath, BLI_get_folder_create(BLENDER_USER_CONFIG, NULL), BLENDER_BOOKMARK_FILE);
		fsmenu_write_file(fsmenu_get(), filepath);
		WM_event_fileselect_event(C, op, EVT_FILESELECT_EXEC);

	}
				
	return OPERATOR_FINISHED;
}

void FILE_OT_execute(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Execute File Window";
	ot->description= "Execute selected file";
	ot->idname= "FILE_OT_execute";
	
	/* api callbacks */
	ot->exec= file_exec;
	ot->poll= file_operator_poll; 
	
	RNA_def_boolean(ot->srna, "need_active", 0, "Need Active", "Only execute if there's an active selected file in the file list.");
}


int file_parent_exec(bContext *C, wmOperator *UNUSED(unused))
{
	SpaceFile *sfile= CTX_wm_space_file(C);
	
	if(sfile->params) {
		if (BLI_has_parent(sfile->params->dir)) {
			BLI_parent_dir(sfile->params->dir);
			BLI_cleanup_dir(G.main->name, sfile->params->dir);
			file_change_dir(C, 0);
			WM_event_add_notifier(C, NC_SPACE|ND_SPACE_FILE_LIST, NULL);
		}
	}		
	
	return OPERATOR_FINISHED;

}


void FILE_OT_parent(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Parent File";
	ot->description= "Move to parent directory";
	ot->idname= "FILE_OT_parent";
	
	/* api callbacks */
	ot->exec= file_parent_exec;
	ot->poll= ED_operator_file_active; /* <- important, handler is on window level */
}


int file_refresh_exec(bContext *C, wmOperator *UNUSED(unused))
{
	SpaceFile *sfile= CTX_wm_space_file(C);

	ED_fileselect_clear(C, sfile);

	WM_event_add_notifier(C, NC_SPACE|ND_SPACE_FILE_LIST, NULL);

	return OPERATOR_FINISHED;

}

void FILE_OT_previous(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Previous Folder";
	ot->description= "Move to previous folder";
	ot->idname= "FILE_OT_previous";
	
	/* api callbacks */
	ot->exec= file_previous_exec;
	ot->poll= ED_operator_file_active; /* <- important, handler is on window level */
}

int file_previous_exec(bContext *C, wmOperator *UNUSED(unused))
{
	SpaceFile *sfile= CTX_wm_space_file(C);

	if(sfile->params) {
		if (!sfile->folders_next)
			sfile->folders_next = folderlist_new();

		folderlist_pushdir(sfile->folders_next, sfile->params->dir);
		folderlist_popdir(sfile->folders_prev, sfile->params->dir);
		folderlist_pushdir(sfile->folders_next, sfile->params->dir);

		file_change_dir(C, 1);
	}
	WM_event_add_notifier(C, NC_SPACE|ND_SPACE_FILE_LIST, NULL);

	return OPERATOR_FINISHED;
}

void FILE_OT_next(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Next Folder";
	ot->description= "Move to next folder";
	ot->idname= "FILE_OT_next";
	
	/* api callbacks */
	ot->exec= file_next_exec;
	ot->poll= ED_operator_file_active; /* <- important, handler is on window level */
}

int file_next_exec(bContext *C, wmOperator *UNUSED(unused))
{
	SpaceFile *sfile= CTX_wm_space_file(C);
	if(sfile->params) {
		if (!sfile->folders_next)
			sfile->folders_next = folderlist_new();

		folderlist_pushdir(sfile->folders_prev, sfile->params->dir);
		folderlist_popdir(sfile->folders_next, sfile->params->dir);

		// update folder_prev so we can check for it in folderlist_clear_next()
		folderlist_pushdir(sfile->folders_prev, sfile->params->dir);

		file_change_dir(C, 1);
	}		
	WM_event_add_notifier(C, NC_SPACE|ND_SPACE_FILE_LIST, NULL);

	return OPERATOR_FINISHED;
}


/* only meant for timer usage */
static int file_smoothscroll_invoke(bContext *C, wmOperator *UNUSED(op), wmEvent *event)
{
	ScrArea *sa = CTX_wm_area(C);
	SpaceFile *sfile= CTX_wm_space_file(C);
	ARegion *ar, *oldar= CTX_wm_region(C);
	int numfiles, offset;
	int edit_idx = 0;
	int numfiles_layout;
	int i;

	/* escape if not our timer */
	if(sfile->smoothscroll_timer==NULL || sfile->smoothscroll_timer!=event->customdata)
		return OPERATOR_PASS_THROUGH;
	
	numfiles = filelist_numfiles(sfile->files);

	/* check if we are editing a name */
	for (i=0; i < numfiles; ++i)
	{
		struct direntry *file = filelist_file(sfile->files, i);	
		if (file->flags & EDITING) {
			edit_idx=i;
			break;
		}
	}

	/* if we are not editing, we are done */
	if (0==edit_idx) {
		WM_event_remove_timer(CTX_wm_manager(C), CTX_wm_window(C), sfile->smoothscroll_timer);
		sfile->smoothscroll_timer=NULL;
		return OPERATOR_PASS_THROUGH;
	}

	/* we need the correct area for scrolling */
	ar = BKE_area_find_region_type(sa, RGN_TYPE_WINDOW);
	if (!ar || ar->regiontype != RGN_TYPE_WINDOW) {
		WM_event_remove_timer(CTX_wm_manager(C), CTX_wm_window(C), sfile->smoothscroll_timer);
		sfile->smoothscroll_timer=NULL;
		return OPERATOR_PASS_THROUGH;
	}

	offset = ED_fileselect_layout_offset(sfile->layout, 0, ar->v2d.cur.xmin, -ar->v2d.cur.ymax);
	if (offset<0) offset=0;

	/* scroll offset is the first file in the row/column we are editing in */
	if (sfile->scroll_offset == 0) {
		if (sfile->layout->flag & FILE_LAYOUT_HOR) {
			sfile->scroll_offset = (edit_idx/sfile->layout->rows)*sfile->layout->rows;
			if (sfile->scroll_offset <= offset) sfile->scroll_offset -= sfile->layout->rows;
		} else {
			sfile->scroll_offset = (edit_idx/sfile->layout->columns)*sfile->layout->columns;
			if (sfile->scroll_offset <= offset) sfile->scroll_offset -= sfile->layout->columns;
		}
	}
	
	numfiles_layout = ED_fileselect_layout_numfiles(sfile->layout, ar);
	
	/* check if we have reached our final scroll position */
	if ( (sfile->scroll_offset >= offset) && (sfile->scroll_offset < offset + numfiles_layout) ) {
		WM_event_remove_timer(CTX_wm_manager(C), CTX_wm_window(C), sfile->smoothscroll_timer);
		sfile->smoothscroll_timer=NULL;
		return OPERATOR_FINISHED;
	}

	/* temporarily set context to the main window region, 
	 * so the scroll operators work */
	CTX_wm_region_set(C, ar);
	
	/* scroll one step in the desired direction */
	if (sfile->scroll_offset < offset) {
		if (sfile->layout->flag & FILE_LAYOUT_HOR) {
			WM_operator_name_call(C, "VIEW2D_OT_scroll_left", 0, NULL);
		} else {
			WM_operator_name_call(C, "VIEW2D_OT_scroll_up", 0, NULL);
		}
		
	} else {
		if (sfile->layout->flag & FILE_LAYOUT_HOR) {
			WM_operator_name_call(C, "VIEW2D_OT_scroll_right", 0, NULL);
		} else {
			WM_operator_name_call(C, "VIEW2D_OT_scroll_down", 0, NULL);
		}
	}
	
	ED_region_tag_redraw(CTX_wm_region(C));
	
	/* and restore context */
	CTX_wm_region_set(C, oldar);
	
	return OPERATOR_FINISHED;
}


void FILE_OT_smoothscroll(wmOperatorType *ot)
{
	
	/* identifiers */
	ot->name= "Smooth Scroll";
	ot->idname= "FILE_OT_smoothscroll";
	ot->description="Smooth scroll to make editable file visible.";
	
	/* api callbacks */
	ot->invoke= file_smoothscroll_invoke;
	
	ot->poll= ED_operator_file_active;
}


/* create a new, non-existing folder name, returns 1 if successful, 0 if name couldn't be created.
   The actual name is returned in 'name', 'folder' contains the complete path, including the new folder name.
*/
static int new_folder_path(const char* parent, char *folder, char *name)
{
	int i = 1;
	int len = 0;

	BLI_strncpy(name, "New Folder", FILE_MAXFILE);
	BLI_join_dirfile(folder, parent, name);
	/* check whether folder with the name already exists, in this case
	   add number to the name. Check length of generated name to avoid
	   crazy case of huge number of folders each named 'New Folder (x)' */
	while (BLI_exists(folder) && (len<FILE_MAXFILE)) {
		len = BLI_snprintf(name, FILE_MAXFILE, "New Folder(%d)", i);
		BLI_join_dirfile(folder, parent, name);
		i++;
	}

	return (len<FILE_MAXFILE);
}

int file_directory_new_exec(bContext *C, wmOperator *op)
{
	char name[FILE_MAXFILE];
	char path[FILE_MAX];
	int generate_name= 1;

	SpaceFile *sfile= CTX_wm_space_file(C);
	
	if(!sfile->params) {
		BKE_report(op->reports,RPT_WARNING, "No parent directory given.");
		return OPERATOR_CANCELLED;
	}
	
	path[0] = '\0';

	if(RNA_struct_find_property(op->ptr, "directory")) {
		RNA_string_get(op->ptr, "directory", path);
		if (path[0] != '\0') generate_name= 0;
	}

	if (generate_name) {
		/* create a new, non-existing folder name */
		if (!new_folder_path(sfile->params->dir, path, name)) {
			BKE_report(op->reports,RPT_ERROR, "Couldn't create new folder name.");
			return OPERATOR_CANCELLED;
		}
	}

	/* create the file */
	BLI_recurdir_fileops(path);

	if (!BLI_exists(path)) {
		BKE_report(op->reports,RPT_ERROR, "Couldn't create new folder.");
		return OPERATOR_CANCELLED;
	} 

	/* now remember file to jump into editing */
	BLI_strncpy(sfile->params->renamefile, name, FILE_MAXFILE);

	/* set timer to smoothly view newly generated file */
	sfile->smoothscroll_timer = WM_event_add_timer(CTX_wm_manager(C), CTX_wm_window(C), TIMER1, 1.0/1000.0);	/* max 30 frs/sec */
	sfile->scroll_offset=0;

	/* reload dir to make sure we're seeing what's in the directory */
	ED_fileselect_clear(C, sfile);
	WM_event_add_notifier(C, NC_SPACE|ND_SPACE_FILE_LIST, NULL);

	return OPERATOR_FINISHED;
}


void FILE_OT_directory_new(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Create New Directory";
	ot->description= "Create a new directory";
	ot->idname= "FILE_OT_directory_new";
	
	/* api callbacks */
	ot->invoke= WM_operator_confirm;
	ot->exec= file_directory_new_exec;
	ot->poll= ED_operator_file_active; /* <- important, handler is on window level */

	RNA_def_string_dir_path(ot->srna, "directory", "", FILE_MAX, "Directory", "Name of new directory");

}


static void file_expand_directory(bContext *C)
{
	SpaceFile *sfile= CTX_wm_space_file(C);
	
	if(sfile->params) {
		if ( sfile->params->dir[0] == '~' ) {
			char tmpstr[sizeof(sfile->params->dir)-1];
			strncpy(tmpstr, sfile->params->dir+1, sizeof(tmpstr));
			BLI_join_dirfile(sfile->params->dir, BLI_getDefaultDocumentFolder(), tmpstr);
		}

#ifdef WIN32
		if (sfile->params->dir[0] == '\0')
			get_default_root(sfile->params->dir);
#endif
	}
}

int file_directory_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	SpaceFile *sfile= CTX_wm_space_file(C);

	if(sfile->params) {
		file_expand_directory(C);
		
		if (!BLI_exists(sfile->params->dir)) {
			return WM_operator_confirm_message(C, op, "Create new directory?");
		} 

		return file_directory_exec(C, op);
	}

	return OPERATOR_CANCELLED;
}



int file_directory_exec(bContext *C, wmOperator *UNUSED(unused))
{
	SpaceFile *sfile= CTX_wm_space_file(C);
	
	if(sfile->params) {
		file_expand_directory(C);

		if (!BLI_exists(sfile->params->dir)) {
			BLI_recurdir_fileops(sfile->params->dir);
		}

		/* special case, user may have pasted a fulepath into the directory */
		if(BLI_exists(sfile->params->dir) && BLI_is_dir(sfile->params->dir) == 0) {
			char path[sizeof(sfile->params->dir)];
			BLI_strncpy(path, sfile->params->dir, sizeof(path));
			BLI_split_dirfile(path, sfile->params->dir, sfile->params->file);
		}

		BLI_cleanup_dir(G.main->name, sfile->params->dir);
		BLI_add_slash(sfile->params->dir);
		file_change_dir(C, 1);

		WM_event_add_notifier(C, NC_SPACE|ND_SPACE_FILE_LIST, NULL);
	}		
	

	return OPERATOR_FINISHED;
}

int file_filename_exec(bContext *C, wmOperator *UNUSED(unused))
{
	SpaceFile *sfile= CTX_wm_space_file(C);
	
	if(sfile->params) {
		if (file_select_match(sfile, sfile->params->file))
		{
			sfile->params->file[0] = '\0';
			WM_event_add_notifier(C, NC_SPACE|ND_SPACE_FILE_PARAMS, NULL);
		}
	}		

	return OPERATOR_FINISHED;
}

void FILE_OT_directory(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Enter Directory Name";
	ot->description= "Enter a directory name";
	ot->idname= "FILE_OT_directory";
	
	/* api callbacks */
	ot->invoke= file_directory_invoke;
	ot->exec= file_directory_exec;
	ot->poll= ED_operator_file_active; /* <- important, handler is on window level */
}

void FILE_OT_refresh(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Refresh Filelist";
	ot->description= "Refresh the file list";
	ot->idname= "FILE_OT_refresh";
	
	/* api callbacks */
	ot->exec= file_refresh_exec;
	ot->poll= ED_operator_file_active; /* <- important, handler is on window level */
}

int file_hidedot_exec(bContext *C, wmOperator *UNUSED(unused))
{
	SpaceFile *sfile= CTX_wm_space_file(C);
	
	if(sfile->params) {
		sfile->params->flag ^= FILE_HIDE_DOT;
		ED_fileselect_clear(C, sfile);
		WM_event_add_notifier(C, NC_SPACE|ND_SPACE_FILE_LIST, NULL);
	}
	
	return OPERATOR_FINISHED;
}


void FILE_OT_hidedot(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Toggle Hide Dot Files";
	ot->description= "Toggle hide hidden dot files";
	ot->idname= "FILE_OT_hidedot";
	
	/* api callbacks */
	ot->exec= file_hidedot_exec;
	ot->poll= ED_operator_file_active; /* <- important, handler is on window level */
}

struct ARegion *file_buttons_region(struct ScrArea *sa)
{
	ARegion *ar, *arnew;
	
	for(ar= sa->regionbase.first; ar; ar= ar->next)
		if(ar->regiontype==RGN_TYPE_CHANNELS)
			return ar;

	/* add subdiv level; after header */
	for(ar= sa->regionbase.first; ar; ar= ar->next)
		if(ar->regiontype==RGN_TYPE_HEADER)
			break;
	
	/* is error! */
	if(ar==NULL) return NULL;
	
	arnew= MEM_callocN(sizeof(ARegion), "buttons for file panels");
	
	BLI_insertlinkafter(&sa->regionbase, ar, arnew);
	arnew->regiontype= RGN_TYPE_CHANNELS;
	arnew->alignment= RGN_ALIGN_LEFT;
	
	arnew->flag = RGN_FLAG_HIDDEN;
	
	return arnew;
}

int file_bookmark_toggle_exec(bContext *C, wmOperator *UNUSED(unused))
{
	ScrArea *sa= CTX_wm_area(C);
	ARegion *ar= file_buttons_region(sa);
	
	if(ar)
		ED_region_toggle_hidden(C, ar);

	return OPERATOR_FINISHED;
}

void FILE_OT_bookmark_toggle(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Toggle Bookmarks";
	ot->description= "Toggle bookmarks display";
	ot->idname= "FILE_OT_bookmark_toggle";
	
	/* api callbacks */
	ot->exec= file_bookmark_toggle_exec;
	ot->poll= ED_operator_file_active; /* <- important, handler is on window level */
}


int file_filenum_exec(bContext *C, wmOperator *op)
{
	SpaceFile *sfile= CTX_wm_space_file(C);
	ScrArea *sa= CTX_wm_area(C);
	
	int inc = RNA_int_get(op->ptr, "increment");
	if(sfile->params && (inc != 0)) {
		BLI_newname(sfile->params->file, inc);
		ED_area_tag_redraw(sa);
		file_draw_check_cb(C, NULL, NULL);
		// WM_event_add_notifier(C, NC_WINDOW, NULL);
	}
	
	return OPERATOR_FINISHED;

}

void FILE_OT_filenum(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Increment Number in Filename";
	ot->description= "Increment number in filename";
	ot->idname= "FILE_OT_filenum";
	
	/* api callbacks */
	ot->exec= file_filenum_exec;
	ot->poll= ED_operator_file_active; /* <- important, handler is on window level */

	/* props */
	RNA_def_int(ot->srna, "increment", 1, 0, 100, "Increment", "", 0,100);
}

int file_rename_exec(bContext *C, wmOperator *UNUSED(op))
{
	ScrArea *sa= CTX_wm_area(C);
	SpaceFile *sfile= (SpaceFile*)CTX_wm_space_data(C);
	
	if(sfile->params) {
		int idx = sfile->params->active_file;
		int numfiles = filelist_numfiles(sfile->files);
		if ( (0<=idx) && (idx<numfiles) ) {
			struct direntry *file= filelist_file(sfile->files, idx);
			file->flags |= EDITING;
			BLI_strncpy(sfile->params->renameedit, file->relname, FILE_MAXFILE);
			sfile->params->renamefile[0]= '\0';
		}
		ED_area_tag_redraw(sa);
	}
	
	return OPERATOR_FINISHED;

}

int file_rename_poll(bContext *C)
{
	int poll = ED_operator_file_active(C);
	SpaceFile *sfile= CTX_wm_space_file(C);

	if (sfile && sfile->params) {
		if (sfile->params->active_file < 0) { 
			poll= 0;
		} else {
			char dir[FILE_MAX], group[FILE_MAX];	
			if (filelist_islibrary(sfile->files, dir, group)) poll= 0;
		}
	}
	else
		poll= 0;
	return poll;
}

void FILE_OT_rename(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Rename File or Directory";
	ot->description= "Rename file or file directory";
	ot->idname= "FILE_OT_rename";
	
	/* api callbacks */
	ot->exec= file_rename_exec;
	ot->poll= file_rename_poll; 

}

int file_delete_poll(bContext *C)
{
	int poll = ED_operator_file_active(C);
	SpaceFile *sfile= CTX_wm_space_file(C);
	struct direntry* file;

	if (sfile && sfile->params) {
		if (sfile->params->active_file < 0) { 
			poll= 0;
		} else {
			char dir[FILE_MAX], group[FILE_MAX];	
			if (filelist_islibrary(sfile->files, dir, group)) poll= 0;
			file = filelist_file(sfile->files, sfile->params->active_file);
			if (file && S_ISDIR(file->type)) poll= 0;
		}
	}
	else
		poll= 0;
		
	return poll;
}

int file_delete_exec(bContext *C, wmOperator *UNUSED(op))
{
	char str[FILE_MAX];
	SpaceFile *sfile= CTX_wm_space_file(C);
	struct direntry* file;
	
	
	file = filelist_file(sfile->files, sfile->params->active_file);
	BLI_make_file_string(G.main->name, str, sfile->params->dir, file->relname);
	BLI_delete(str, 0, 0);	
	ED_fileselect_clear(C, sfile);
	WM_event_add_notifier(C, NC_SPACE|ND_SPACE_FILE_LIST, NULL);
	
	return OPERATOR_FINISHED;

}

void FILE_OT_delete(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Delete File";
	ot->description= "Delete selected file";
	ot->idname= "FILE_OT_delete";
	
	/* api callbacks */
	ot->invoke= WM_operator_confirm;
	ot->exec= file_delete_exec;
	ot->poll= file_delete_poll; /* <- important, handler is on window level */
}


void ED_operatormacros_file(void)
{
	wmOperatorType *ot;
	wmOperatorTypeMacro *otmacro;
	
	ot= WM_operatortype_append_macro("FILE_OT_select_execute", "Select and Execute", OPTYPE_UNDO|OPTYPE_REGISTER);
	WM_operatortype_macro_define(ot, "FILE_OT_select");
	otmacro= WM_operatortype_macro_define(ot, "FILE_OT_execute");
	RNA_boolean_set(otmacro->ptr, "need_active", 1);

}
