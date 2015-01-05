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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_file/filesel.c
 *  \ingroup spfile
 */


#include <string.h>
#include <stdio.h>
#include <math.h>

#include <sys/stat.h>
#include <sys/types.h>

/* path/file handeling stuff */
#ifdef WIN32
#  include <io.h>
#  include <direct.h>
#  include "BLI_winstuff.h"
#else
#  include <unistd.h>
#  include <sys/times.h>
#  include <dirent.h>
#endif

#include "DNA_space_types.h"
#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"
#include "BLI_fileops_types.h"
#include "BLI_fnmatch.h"

#include "BKE_appdir.h"
#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_main.h"

#include "BLF_api.h"


#include "ED_fileselect.h"

#include "WM_api.h"
#include "WM_types.h"


#include "RNA_access.h"

#include "UI_interface.h"
#include "UI_interface_icons.h"

#include "file_intern.h"
#include "filelist.h"

FileSelectParams *ED_fileselect_get_params(struct SpaceFile *sfile)
{
	if (!sfile->params) {
		ED_fileselect_set_params(sfile);
	}
	return sfile->params;
}

/**
 * \note RNA_struct_property_is_set_ex is used here because we want
 *       the previously used settings to be used here rather then overriding them */
short ED_fileselect_set_params(SpaceFile *sfile)
{
	FileSelectParams *params;
	wmOperator *op = sfile->op;

	/* create new parameters if necessary */
	if (!sfile->params) {
		sfile->params = MEM_callocN(sizeof(FileSelectParams), "fileselparams");
		/* set path to most recently opened .blend */
		BLI_split_dirfile(G.main->name, sfile->params->dir, sfile->params->file, sizeof(sfile->params->dir), sizeof(sfile->params->file));
		sfile->params->filter_glob[0] = '\0';
	}

	params = sfile->params;

	/* set the parameters from the operator, if it exists */
	if (op) {
		PropertyRNA *prop;
		const bool is_files = (RNA_struct_find_property(op->ptr, "files") != NULL);
		const bool is_filepath = (RNA_struct_find_property(op->ptr, "filepath") != NULL);
		const bool is_filename = (RNA_struct_find_property(op->ptr, "filename") != NULL);
		const bool is_directory = (RNA_struct_find_property(op->ptr, "directory") != NULL);
		const bool is_relative_path = (RNA_struct_find_property(op->ptr, "relative_path") != NULL);

		BLI_strncpy_utf8(params->title, RNA_struct_ui_name(op->type->srna), sizeof(params->title));

		if (RNA_struct_find_property(op->ptr, "filemode"))
			params->type = RNA_int_get(op->ptr, "filemode");
		else
			params->type = FILE_SPECIAL;

		if (is_filepath && RNA_struct_property_is_set_ex(op->ptr, "filepath", false)) {
			char name[FILE_MAX];
			RNA_string_get(op->ptr, "filepath", name);
			if (params->type == FILE_LOADLIB) {
				BLI_strncpy(params->dir, name, sizeof(params->dir));
				sfile->params->file[0] = '\0';
			}
			else {
				BLI_split_dirfile(name, sfile->params->dir, sfile->params->file, sizeof(sfile->params->dir), sizeof(sfile->params->file));
			}
		}
		else {
			if (is_directory && RNA_struct_property_is_set_ex(op->ptr, "directory", false)) {
				RNA_string_get(op->ptr, "directory", params->dir);
				sfile->params->file[0] = '\0';
			}

			if (is_filename && RNA_struct_property_is_set_ex(op->ptr, "filename", false)) {
				RNA_string_get(op->ptr, "filename", params->file);
			}
		}

		if (params->dir[0]) {
			BLI_cleanup_dir(G.main->name, params->dir);
			BLI_path_abs(params->dir, G.main->name);
		}

		if (is_directory == true && is_filename == false && is_filepath == false && is_files == false) {
			params->flag |= FILE_DIRSEL_ONLY;
		}
		else {
			params->flag &= ~FILE_DIRSEL_ONLY;
		}

		params->filter = 0;
		if ((prop = RNA_struct_find_property(op->ptr, "filter_blender")))
			params->filter |= RNA_property_boolean_get(op->ptr, prop) ? FILE_TYPE_BLENDER : 0;
		if ((prop = RNA_struct_find_property(op->ptr, "filter_backup")))
			params->filter |= RNA_property_boolean_get(op->ptr, prop) ? FILE_TYPE_BLENDER_BACKUP : 0;
		if ((prop = RNA_struct_find_property(op->ptr, "filter_image")))
			params->filter |= RNA_property_boolean_get(op->ptr, prop) ? FILE_TYPE_IMAGE : 0;
		if ((prop = RNA_struct_find_property(op->ptr, "filter_movie")))
			params->filter |= RNA_property_boolean_get(op->ptr, prop) ? FILE_TYPE_MOVIE : 0;
		if ((prop = RNA_struct_find_property(op->ptr, "filter_python")))
			params->filter |= RNA_property_boolean_get(op->ptr, prop) ? FILE_TYPE_PYSCRIPT : 0;
		if ((prop = RNA_struct_find_property(op->ptr, "filter_font")))
			params->filter |= RNA_property_boolean_get(op->ptr, prop) ? FILE_TYPE_FTFONT : 0;
		if ((prop = RNA_struct_find_property(op->ptr, "filter_sound")))
			params->filter |= RNA_property_boolean_get(op->ptr, prop) ? FILE_TYPE_SOUND : 0;
		if ((prop = RNA_struct_find_property(op->ptr, "filter_text")))
			params->filter |= RNA_property_boolean_get(op->ptr, prop) ? FILE_TYPE_TEXT : 0;
		if ((prop = RNA_struct_find_property(op->ptr, "filter_folder")))
			params->filter |= RNA_property_boolean_get(op->ptr, prop) ? FILE_TYPE_FOLDER : 0;
		if ((prop = RNA_struct_find_property(op->ptr, "filter_btx")))
			params->filter |= RNA_property_boolean_get(op->ptr, prop) ? FILE_TYPE_BTX : 0;
		if ((prop = RNA_struct_find_property(op->ptr, "filter_collada")))
			params->filter |= RNA_property_boolean_get(op->ptr, prop) ? FILE_TYPE_COLLADA : 0;
		if ((prop = RNA_struct_find_property(op->ptr, "filter_glob"))) {
			RNA_property_string_get(op->ptr, prop, params->filter_glob);
			params->filter |= (FILE_TYPE_OPERATOR | FILE_TYPE_FOLDER);
		}
		else {
			params->filter_glob[0] = '\0';
		}

		if (params->filter != 0) {
			if (U.uiflag & USER_FILTERFILEEXTS) {
				params->flag |= FILE_FILTER;
			}
			else {
				params->flag &= ~FILE_FILTER;
			}
		}

		if (U.uiflag & USER_HIDE_DOT) {
			params->flag |= FILE_HIDE_DOT;
		}
		else {
			params->flag &= ~FILE_HIDE_DOT;
		}
		

		if (params->type == FILE_LOADLIB) {
			params->flag |= RNA_boolean_get(op->ptr, "link") ? FILE_LINK : 0;
			params->flag |= RNA_boolean_get(op->ptr, "autoselect") ? FILE_AUTOSELECT : 0;
			params->flag |= RNA_boolean_get(op->ptr, "active_layer") ? FILE_ACTIVELAY : 0;
		}

		if (RNA_struct_find_property(op->ptr, "display_type"))
			params->display = RNA_enum_get(op->ptr, "display_type");

		if (params->display == FILE_DEFAULTDISPLAY) {
			if (U.uiflag & USER_SHOW_THUMBNAILS) {
				if (params->filter & (FILE_TYPE_IMAGE | FILE_TYPE_MOVIE))
					params->display = FILE_IMGDISPLAY;
				else
					params->display = FILE_SHORTDISPLAY;
			}
			else {
				params->display = FILE_SHORTDISPLAY;
			}
		}

		if (is_relative_path) {
			if (!RNA_struct_property_is_set_ex(op->ptr, "relative_path", false)) {
				RNA_boolean_set(op->ptr, "relative_path", U.flag & USER_RELPATHS);
			}
		}
	}
	else {
		/* default values, if no operator */
		params->type = FILE_UNIX;
		params->flag |= FILE_HIDE_DOT;
		params->flag &= ~FILE_DIRSEL_ONLY;
		params->display = FILE_SHORTDISPLAY;
		params->filter = 0;
		params->filter_glob[0] = '\0';
	}

	/* operator has no setting for this */
	params->sort = FILE_SORT_ALPHA;


	/* initialize the list with previous folders */
	if (!sfile->folders_prev)
		sfile->folders_prev = folderlist_new();

	if (!sfile->params->dir[0]) {
		if (G.main->name[0]) {
			BLI_split_dir_part(G.main->name, sfile->params->dir, sizeof(sfile->params->dir));
		}
		else {
			const char *doc_path = BKE_appdir_folder_default();
			if (doc_path) {
				BLI_strncpy(sfile->params->dir, doc_path, sizeof(sfile->params->dir));
			}
		}
	}

	folderlist_pushdir(sfile->folders_prev, sfile->params->dir);

	/* switching thumbnails needs to recalc layout [#28809] */
	if (sfile->layout) {
		sfile->layout->dirty = true;
	}

	return 1;
}

void ED_fileselect_reset_params(SpaceFile *sfile)
{
	sfile->params->type = FILE_UNIX;
	sfile->params->flag = 0;
	sfile->params->title[0] = '\0';
}

int ED_fileselect_layout_numfiles(FileLayout *layout, ARegion *ar)
{
	int numfiles;

	/* Values in pixels.
	 *
	 * - *_item: size of each (row|col), (including padding)
	 * - *_view: (x|y) size of the view.
	 * - *_over: extra pixels, to take into account, when the fit isnt exact
	 *   (needed since you may see the end of the previous column and the beginning of the next).
	 *
	 * Could be more clever and take scrolling into account,
	 * but for now don't bother.
	 */
	if (layout->flag & FILE_LAYOUT_HOR) {
		const int x_item = layout->tile_w + (2 * layout->tile_border_x);
		const int x_view = (int)(BLI_rctf_size_x(&ar->v2d.cur));
		const int x_over = x_item - (x_view % x_item);
		numfiles = (int)((float)(x_view + x_over) / (float)(x_item));
		return numfiles * layout->rows;
	}
	else {
		const int y_item = layout->tile_h + (2 * layout->tile_border_y);
		const int y_view = (int)(BLI_rctf_size_y(&ar->v2d.cur));
		const int y_over = y_item - (y_view % y_item);
		numfiles = (int)((float)(y_view + y_over) / (float)(y_item));
		return numfiles * layout->columns;
	}
}

static bool is_inside(int x, int y, int cols, int rows)
{
	return ((x >= 0) && (x < cols) && (y >= 0) && (y < rows));
}

FileSelection ED_fileselect_layout_offset_rect(FileLayout *layout, const rcti *rect)
{
	int colmin, colmax, rowmin, rowmax;
	FileSelection sel;
	sel.first = sel.last = -1;

	if (layout == NULL)
		return sel;
	
	colmin = (rect->xmin) / (layout->tile_w + 2 * layout->tile_border_x);
	rowmin = (rect->ymin) / (layout->tile_h + 2 * layout->tile_border_y);
	colmax = (rect->xmax) / (layout->tile_w + 2 * layout->tile_border_x);
	rowmax = (rect->ymax) / (layout->tile_h + 2 * layout->tile_border_y);
	
	if (is_inside(colmin, rowmin, layout->columns, layout->rows) ||
	    is_inside(colmax, rowmax, layout->columns, layout->rows) )
	{
		CLAMP(colmin, 0, layout->columns - 1);
		CLAMP(rowmin, 0, layout->rows - 1);
		CLAMP(colmax, 0, layout->columns - 1);
		CLAMP(rowmax, 0, layout->rows - 1);
	}
	
	if ((colmin > layout->columns - 1) || (rowmin > layout->rows - 1)) {
		sel.first = -1;
	}
	else {
		if (layout->flag & FILE_LAYOUT_HOR) 
			sel.first = layout->rows * colmin + rowmin;
		else
			sel.first = colmin + layout->columns * rowmin;
	}
	if ((colmax > layout->columns - 1) || (rowmax > layout->rows - 1)) {
		sel.last = -1;
	}
	else {
		if (layout->flag & FILE_LAYOUT_HOR) 
			sel.last = layout->rows * colmax + rowmax;
		else
			sel.last = colmax + layout->columns * rowmax;
	}

	return sel;
}

int ED_fileselect_layout_offset(FileLayout *layout, int x, int y)
{
	int offsetx, offsety;
	int active_file;

	if (layout == NULL)
		return -1;
	
	offsetx = (x) / (layout->tile_w + 2 * layout->tile_border_x);
	offsety = (y) / (layout->tile_h + 2 * layout->tile_border_y);
	
	if (offsetx > layout->columns - 1) return -1;
	if (offsety > layout->rows - 1) return -1;
	
	if (layout->flag & FILE_LAYOUT_HOR) 
		active_file = layout->rows * offsetx + offsety;
	else
		active_file = offsetx + layout->columns * offsety;
	return active_file;
}

void ED_fileselect_layout_tilepos(FileLayout *layout, int tile, int *x, int *y)
{
	if (layout->flag == FILE_LAYOUT_HOR) {
		*x = layout->tile_border_x + (tile / layout->rows) * (layout->tile_w + 2 * layout->tile_border_x);
		*y = layout->tile_border_y + (tile % layout->rows) * (layout->tile_h + 2 * layout->tile_border_y);
	}
	else {
		*x = layout->tile_border_x + ((tile) % layout->columns) * (layout->tile_w + 2 * layout->tile_border_x);
		*y = layout->tile_border_y + ((tile) / layout->columns) * (layout->tile_h + 2 * layout->tile_border_y);
	}
}

/* Shorten a string to a given width w. 
 * If front is set, shorten from the front,
 * otherwise shorten from the end. */
float file_shorten_string(char *string, float w, int front)
{	
	char temp[FILE_MAX];
	short shortened = 0;
	float sw = 0;
	float pad = 0;

	if (w <= 0) {
		*string = '\0';
		return 0.0;
	}

	sw = file_string_width(string);
	if (front == 1) {
		const char *s = string;
		BLI_strncpy(temp, "...", 4);
		pad = file_string_width(temp);
		while ((*s) && (sw + pad > w)) {
			s++;
			sw = file_string_width(s);
			shortened = 1;
		}
		if (shortened) {
			int slen = strlen(s);
			BLI_strncpy(temp + 3, s, slen + 1);
			temp[slen + 4] = '\0';
			BLI_strncpy(string, temp, slen + 4);
		}
	}
	else {
		const char *s = string;
		while (sw > w) {
			int slen = strlen(string);
			string[slen - 1] = '\0';
			sw = file_string_width(s);
			shortened = 1;
		}

		if (shortened) {
			int slen = strlen(string);
			if (slen > 3) {
				BLI_strncpy(string + slen - 3, "...", 4);
			}
		}
	}
	
	return sw;
}

float file_string_width(const char *str)
{
	uiStyle *style = UI_style_get();
	UI_fontstyle_set(&style->widget);
	return BLF_width(style->widget.uifont_id, str, BLF_DRAW_STR_DUMMY_MAX);
}

float file_font_pointsize(void)
{
#if 0
	float s;
	char tmp[2] = "X";
	uiStyle *style = UI_style_get();
	UI_fontstyle_set(&style->widget);
	s = BLF_height(style->widget.uifont_id, tmp);
	return style->widget.points;
#else
	uiStyle *style = UI_style_get();
	UI_fontstyle_set(&style->widget);
	return style->widget.points * UI_DPI_FAC;
#endif
}

static void column_widths(struct FileList *files, struct FileLayout *layout)
{
	int i;
	int numfiles = filelist_numfiles(files);

	for (i = 0; i < MAX_FILE_COLUMN; ++i) {
		layout->column_widths[i] = 0;
	}

	for (i = 0; (i < numfiles); ++i) {
		struct direntry *file = filelist_file(files, i);
		if (file) {
			float len;
			len = file_string_width(file->relname);
			if (len > layout->column_widths[COLUMN_NAME]) layout->column_widths[COLUMN_NAME] = len;
			len = file_string_width(file->date);
			if (len > layout->column_widths[COLUMN_DATE]) layout->column_widths[COLUMN_DATE] = len;
			len = file_string_width(file->time);
			if (len > layout->column_widths[COLUMN_TIME]) layout->column_widths[COLUMN_TIME] = len;
			len = file_string_width(file->size);
			if (len > layout->column_widths[COLUMN_SIZE]) layout->column_widths[COLUMN_SIZE] = len;
			len = file_string_width(file->mode1);
			if (len > layout->column_widths[COLUMN_MODE1]) layout->column_widths[COLUMN_MODE1] = len;
			len = file_string_width(file->mode2);
			if (len > layout->column_widths[COLUMN_MODE2]) layout->column_widths[COLUMN_MODE2] = len;
			len = file_string_width(file->mode3);
			if (len > layout->column_widths[COLUMN_MODE3]) layout->column_widths[COLUMN_MODE3] = len;
			len = file_string_width(file->owner);
			if (len > layout->column_widths[COLUMN_OWNER]) layout->column_widths[COLUMN_OWNER] = len;
		}
	}
}

void ED_fileselect_init_layout(struct SpaceFile *sfile, ARegion *ar)
{
	FileSelectParams *params = ED_fileselect_get_params(sfile);
	FileLayout *layout = NULL;
	View2D *v2d = &ar->v2d;
	int maxlen = 0;
	int numfiles;
	int textheight;

	if (sfile->layout == NULL) {
		sfile->layout = MEM_callocN(sizeof(struct FileLayout), "file_layout");
		sfile->layout->dirty = true;
	}
	else if (sfile->layout->dirty == false) {
		return;
	}

	numfiles = filelist_numfiles(sfile->files);
	textheight = (int)file_font_pointsize();
	layout = sfile->layout;
	layout->textheight = textheight;

	if (params->display == FILE_IMGDISPLAY) {
		layout->prv_w = 4.8f * UI_UNIT_X;
		layout->prv_h = 4.8f * UI_UNIT_Y;
		layout->tile_border_x = 0.3f * UI_UNIT_X;
		layout->tile_border_y = 0.3f * UI_UNIT_X;
		layout->prv_border_x = 0.3f * UI_UNIT_X;
		layout->prv_border_y = 0.3f * UI_UNIT_Y;
		layout->tile_w = layout->prv_w + 2 * layout->prv_border_x;
		layout->tile_h = layout->prv_h + 2 * layout->prv_border_y + textheight;
		layout->width = (int)(BLI_rctf_size_x(&v2d->cur) - 2 * layout->tile_border_x);
		layout->columns = layout->width / (layout->tile_w + 2 * layout->tile_border_x);
		if (layout->columns > 0)
			layout->rows = numfiles / layout->columns + 1;  // XXX dirty, modulo is zero
		else {
			layout->columns = 1;
			layout->rows = numfiles + 1; // XXX dirty, modulo is zero
		}
		layout->height = sfile->layout->rows * (layout->tile_h + 2 * layout->tile_border_y) + layout->tile_border_y * 2;
		layout->flag = FILE_LAYOUT_VER;
	}
	else {
		int column_space = 0.6f * UI_UNIT_X;
		int column_icon_space = 0.2f * UI_UNIT_X;

		layout->prv_w = 0;
		layout->prv_h = 0;
		layout->tile_border_x = 0.4f * UI_UNIT_X;
		layout->tile_border_y = 0.1f * UI_UNIT_Y;
		layout->prv_border_x = 0;
		layout->prv_border_y = 0;
		layout->tile_h = textheight * 3 / 2;
		layout->height = (int)(BLI_rctf_size_y(&v2d->cur) - 2 * layout->tile_border_y);
		layout->rows = layout->height / (layout->tile_h + 2 * layout->tile_border_y);

		column_widths(sfile->files, layout);

		if (params->display == FILE_SHORTDISPLAY) {
			maxlen = ICON_DEFAULT_WIDTH_SCALE + column_icon_space +
			         (int)layout->column_widths[COLUMN_NAME] + column_space +
			         (int)layout->column_widths[COLUMN_SIZE] + column_space;
		}
		else {
			maxlen = ICON_DEFAULT_WIDTH_SCALE + column_icon_space +
			         (int)layout->column_widths[COLUMN_NAME] + column_space +
#ifndef WIN32
			         (int)layout->column_widths[COLUMN_MODE1] + column_space +
			         (int)layout->column_widths[COLUMN_MODE2] + column_space +
			         (int)layout->column_widths[COLUMN_MODE3] + column_space +
			         (int)layout->column_widths[COLUMN_OWNER] + column_space +
#endif
			         (int)layout->column_widths[COLUMN_DATE] + column_space +
			         (int)layout->column_widths[COLUMN_TIME] + column_space +
			         (int)layout->column_widths[COLUMN_SIZE] + column_space;

		}
		layout->tile_w = maxlen;
		if (layout->rows > 0)
			layout->columns = numfiles / layout->rows + 1;  // XXX dirty, modulo is zero
		else {
			layout->rows = 1;
			layout->columns = numfiles + 1; // XXX dirty, modulo is zero
		}
		layout->width = sfile->layout->columns * (layout->tile_w + 2 * layout->tile_border_x) + layout->tile_border_x * 2;
		layout->flag = FILE_LAYOUT_HOR;
	}
	layout->dirty = false;
}

FileLayout *ED_fileselect_get_layout(struct SpaceFile *sfile, ARegion *ar)
{
	if (!sfile->layout) {
		ED_fileselect_init_layout(sfile, ar);
	}
	return sfile->layout;
}

void file_change_dir(bContext *C, int checkdir)
{
	wmWindowManager *wm = CTX_wm_manager(C);
	SpaceFile *sfile = CTX_wm_space_file(C);

	if (sfile->params) {
		ED_fileselect_clear(wm, sfile);

		/* Clear search string, it is very rare to want to keep that filter while changing dir,
		 * and usually very annoying to keep it actually! */
		sfile->params->filter_search[0] = '\0';

		if (checkdir && !BLI_is_dir(sfile->params->dir)) {
			BLI_strncpy(sfile->params->dir, filelist_dir(sfile->files), sizeof(sfile->params->dir));
			/* could return but just refresh the current dir */
		}
		filelist_setdir(sfile->files, sfile->params->dir);
		
		if (folderlist_clear_next(sfile))
			folderlist_free(sfile->folders_next);

		folderlist_pushdir(sfile->folders_prev, sfile->params->dir);

		file_draw_check_cb(C, NULL, NULL);
	}
}

int file_select_match(struct SpaceFile *sfile, const char *pattern, char *matched_file)
{
	int match = 0;
	
	int i;
	struct direntry *file;
	int n = filelist_numfiles(sfile->files);

	/* select any file that matches the pattern, this includes exact match 
	 * if the user selects a single file by entering the filename
	 */
	for (i = 0; i < n; i++) {
		file = filelist_file(sfile->files, i);
		if (fnmatch(pattern, file->relname, 0) == 0) {
			file->selflag |= FILE_SEL_SELECTED;
			if (!match) {
				BLI_strncpy(matched_file, file->relname, FILE_MAX);
			}
			match++;
		}
	}

	return match;
}

int autocomplete_directory(struct bContext *C, char *str, void *UNUSED(arg_v))
{
	SpaceFile *sfile = CTX_wm_space_file(C);
	int match = AUTOCOMPLETE_NO_MATCH;

	/* search if str matches the beginning of name */
	if (str[0] && sfile->files) {
		char dirname[FILE_MAX];

		DIR *dir;
		struct dirent *de;
		
		BLI_split_dir_part(str, dirname, sizeof(dirname));

		dir = opendir(dirname);

		if (dir) {
			AutoComplete *autocpl = UI_autocomplete_begin(str, FILE_MAX);

			while ((de = readdir(dir)) != NULL) {
				if (strcmp(".", de->d_name) == 0 || strcmp("..", de->d_name) == 0) {
					/* pass */
				}
				else {
					char path[FILE_MAX];
					BLI_stat_t status;
					
					BLI_join_dirfile(path, sizeof(path), dirname, de->d_name);

					if (BLI_stat(path, &status) == 0) {
						if (S_ISDIR(status.st_mode)) { /* is subdir */
							UI_autocomplete_update_name(autocpl, path);
						}
					}
				}
			}
			closedir(dir);

			match = UI_autocomplete_end(autocpl, str);
			if (match) {
				if (match == AUTOCOMPLETE_FULL_MATCH) {
					BLI_add_slash(str);
				}
				else {
					BLI_strncpy(sfile->params->dir, str, sizeof(sfile->params->dir));
				}
			}
		}
	}

	return match;
}

int autocomplete_file(struct bContext *C, char *str, void *UNUSED(arg_v))
{
	SpaceFile *sfile = CTX_wm_space_file(C);
	int match = AUTOCOMPLETE_NO_MATCH;

	/* search if str matches the beginning of name */
	if (str[0] && sfile->files) {
		AutoComplete *autocpl = UI_autocomplete_begin(str, FILE_MAX);
		int nentries = filelist_numfiles(sfile->files);
		int i;

		for (i = 0; i < nentries; ++i) {
			struct direntry *file = filelist_file(sfile->files, i);
			if (file && (S_ISREG(file->type) || S_ISDIR(file->type))) {
				UI_autocomplete_update_name(autocpl, file->relname);
			}
		}
		match = UI_autocomplete_end(autocpl, str);
	}

	return match;
}

void ED_fileselect_clear(struct wmWindowManager *wm, struct SpaceFile *sfile)
{
	/* only NULL in rare cases - [#29734] */
	if (sfile->files) {
		thumbnails_stop(wm, sfile->files);
		filelist_freelib(sfile->files);
		filelist_free(sfile->files);
	}

	sfile->params->active_file = -1;
	WM_main_add_notifier(NC_SPACE | ND_SPACE_FILE_LIST, NULL);
}

void ED_fileselect_exit(struct wmWindowManager *wm, struct SpaceFile *sfile)
{
	if (!sfile) return;
	if (sfile->op) {
		WM_event_fileselect_event(wm, sfile->op, EVT_FILESELECT_EXTERNAL_CANCEL);
		sfile->op = NULL;
	}

	folderlist_free(sfile->folders_prev);
	folderlist_free(sfile->folders_next);
	
	if (sfile->files) {
		ED_fileselect_clear(wm, sfile);
		MEM_freeN(sfile->files);
		sfile->files = NULL;
	}

}
